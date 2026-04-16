#!/usr/bin/env python3
"""
SRED.ca Google Ads — Weekly Data Pull Component

Pulls all account data via GAQL queries and saves to a single JSON file.
Run with: /Users/judebrown/.local/share/uv/tools/google-ads-mcp/bin/python3.12 pull_weekly_data.py

Outputs: outputs/weekly-data/week-of-YYYY-MM-DD.json
"""

import json
import os
import sys
import time
import random
from datetime import datetime, timedelta
from pathlib import Path
import zoneinfo

PROJECT_DIR = Path(__file__).parent.parent
ENV_PATH = PROJECT_DIR / ".env"
CID = "5552474733"
MANAGER_ID = "5122627517"

def load_env():
    for line in ENV_PATH.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, val = line.split("=", 1)
            os.environ.setdefault(key.strip(), val.strip())

def get_client():
    from google.ads.googleads.client import GoogleAdsClient
    from google.auth import default
    credentials, _ = default(scopes=["https://www.googleapis.com/auth/adwords"])
    return GoogleAdsClient(
        credentials=credentials,
        developer_token=os.environ["GOOGLE_ADS_DEVELOPER_TOKEN"],
    )

def query_with_retry(ga_service, cid, query, max_retries=3):
    for attempt in range(max_retries):
        try:
            return list(ga_service.search(customer_id=cid, query=query))
        except Exception as e:
            if "RESOURCE_TEMPORARILY_EXHAUSTED" in str(e) and attempt < max_retries - 1:
                wait = (2 ** attempt) + random.uniform(0, 1)
                print(f"  Rate limited, retrying in {wait:.1f}s...", file=sys.stderr)
                time.sleep(wait)
            else:
                raise

def micros_to_cad(micros):
    return round(micros / 1_000_000, 2) if micros else 0.0

def compute_dates():
    tz = zoneinfo.ZoneInfo("America/Vancouver")
    now = datetime.now(tz)
    days_since_sunday = (now.weekday() + 1) % 7
    if days_since_sunday == 0:
        days_since_sunday = 7
    sunday = (now - timedelta(days=days_since_sunday)).date()
    monday = sunday - timedelta(days=6)
    prior_sunday = monday - timedelta(days=1)
    prior_monday = prior_sunday - timedelta(days=6)
    return monday, sunday, prior_monday, prior_sunday

def pull_campaign_performance(ga, monday, sunday):
    print("  [1/11] Campaign performance (this week)...")
    q = f"""
        SELECT
            campaign.id, campaign.name, campaign.status,
            campaign.bidding_strategy_type,
            campaign_budget.amount_micros,
            metrics.impressions, metrics.clicks, metrics.cost_micros,
            metrics.conversions, metrics.all_conversions,
            metrics.ctr, metrics.average_cpc, metrics.cost_per_conversion,
            metrics.search_impression_share,
            metrics.search_budget_lost_impression_share,
            metrics.search_rank_lost_impression_share,
            segments.date
        FROM campaign
        WHERE segments.date BETWEEN '{monday}' AND '{sunday}'
            AND campaign.status != 'REMOVED'
        ORDER BY segments.date ASC
    """
    rows = query_with_retry(ga, CID, q)
    campaigns = {}
    for r in rows:
        cid = str(r.campaign.id)
        if cid not in campaigns:
            campaigns[cid] = {
                "id": cid,
                "name": r.campaign.name,
                "status": str(r.campaign.status),
                "bidding_strategy": str(r.campaign.bidding_strategy_type),
                "daily_budget_cad": micros_to_cad(r.campaign_budget.amount_micros),
                "spend": 0, "clicks": 0, "impressions": 0,
                "conversions": 0, "all_conversions": 0,
                "daily_breakdown": [],
            }
        c = campaigns[cid]
        day_spend = micros_to_cad(r.metrics.cost_micros)
        c["spend"] += day_spend
        c["clicks"] += r.metrics.clicks
        c["impressions"] += r.metrics.impressions
        c["conversions"] += r.metrics.conversions
        c["all_conversions"] += r.metrics.all_conversions
        c["daily_breakdown"].append({
            "date": r.segments.date,
            "spend": day_spend,
            "clicks": r.metrics.clicks,
            "impressions": r.metrics.impressions,
            "conversions": r.metrics.conversions,
        })
    for c in campaigns.values():
        c["spend"] = round(c["spend"], 2)
        c["conversions"] = round(c["conversions"], 1)
        c["all_conversions"] = round(c["all_conversions"], 1)
        if c["clicks"] > 0:
            c["ctr"] = round(c["clicks"] / c["impressions"], 4) if c["impressions"] else 0
            c["avg_cpc"] = round(c["spend"] / c["clicks"], 2)
        else:
            c["ctr"] = 0
            c["avg_cpc"] = 0
        c["cpa"] = round(c["spend"] / c["conversions"], 2) if c["conversions"] > 0 else 0
    # Get impression share from weekly aggregate (not daily)
    q_agg = f"""
        SELECT
            campaign.id,
            metrics.search_impression_share,
            metrics.search_budget_lost_impression_share,
            metrics.search_rank_lost_impression_share
        FROM campaign
        WHERE segments.date BETWEEN '{monday}' AND '{sunday}'
            AND campaign.status != 'REMOVED'
    """
    for r in query_with_retry(ga, CID, q_agg):
        cid = str(r.campaign.id)
        if cid in campaigns:
            campaigns[cid]["impression_share"] = round(r.metrics.search_impression_share, 4) if r.metrics.search_impression_share else 0
            campaigns[cid]["budget_lost_is"] = round(r.metrics.search_budget_lost_impression_share, 4) if r.metrics.search_budget_lost_impression_share else 0
            campaigns[cid]["rank_lost_is"] = round(r.metrics.search_rank_lost_impression_share, 4) if r.metrics.search_rank_lost_impression_share else 0
    return list(campaigns.values())

def pull_prior_week_totals(ga, prior_monday, prior_sunday):
    print("  [2/11] Campaign performance (prior week)...")
    q = f"""
        SELECT
            campaign.id, campaign.name,
            metrics.impressions, metrics.clicks, metrics.cost_micros,
            metrics.conversions, metrics.all_conversions,
            metrics.ctr, metrics.average_cpc, metrics.cost_per_conversion,
            metrics.search_impression_share
        FROM campaign
        WHERE segments.date BETWEEN '{prior_monday}' AND '{prior_sunday}'
            AND campaign.status != 'REMOVED'
    """
    rows = query_with_retry(ga, CID, q)
    campaigns = {}
    for r in rows:
        cid = str(r.campaign.id)
        campaigns[cid] = {
            "id": cid, "name": r.campaign.name,
            "spend": micros_to_cad(r.metrics.cost_micros),
            "clicks": r.metrics.clicks,
            "impressions": r.metrics.impressions,
            "conversions": round(r.metrics.conversions, 1),
            "all_conversions": round(r.metrics.all_conversions, 1),
            "ctr": round(r.metrics.ctr, 4),
            "avg_cpc": micros_to_cad(r.metrics.average_cpc),
            "cpa": micros_to_cad(r.metrics.cost_per_conversion),
            "impression_share": round(r.metrics.search_impression_share, 4) if r.metrics.search_impression_share else 0,
        }
    return list(campaigns.values())

def pull_keywords(ga, monday, sunday):
    print("  [3/11] Keyword performance + Quality Scores...")
    q = f"""
        SELECT
            ad_group.id, ad_group.name,
            ad_group_criterion.criterion_id,
            ad_group_criterion.keyword.text,
            ad_group_criterion.keyword.match_type,
            ad_group_criterion.quality_info.quality_score,
            ad_group_criterion.quality_info.creative_quality_score,
            ad_group_criterion.quality_info.post_click_quality_score,
            ad_group_criterion.quality_info.search_predicted_ctr,
            ad_group_criterion.status,
            campaign.name,
            metrics.impressions, metrics.clicks, metrics.cost_micros,
            metrics.conversions, metrics.ctr, metrics.average_cpc,
            metrics.cost_per_conversion
        FROM keyword_view
        WHERE segments.date BETWEEN '{monday}' AND '{sunday}'
            AND ad_group_criterion.status != 'REMOVED'
        ORDER BY metrics.cost_micros DESC
        LIMIT 200
    """
    rows = query_with_retry(ga, CID, q)
    keywords = []
    for r in rows:
        qi = r.ad_group_criterion.quality_info
        keywords.append({
            "keyword": r.ad_group_criterion.keyword.text,
            "match_type": str(r.ad_group_criterion.keyword.match_type),
            "status": str(r.ad_group_criterion.status),
            "campaign": r.campaign.name,
            "ad_group": r.ad_group.name,
            "quality_score": qi.quality_score if qi.quality_score else None,
            "ad_relevance": str(qi.creative_quality_score) if qi.creative_quality_score else None,
            "landing_page_score": str(qi.post_click_quality_score) if qi.post_click_quality_score else None,
            "expected_ctr": str(qi.search_predicted_ctr) if qi.search_predicted_ctr else None,
            "impressions": r.metrics.impressions,
            "clicks": r.metrics.clicks,
            "spend": micros_to_cad(r.metrics.cost_micros),
            "conversions": round(r.metrics.conversions, 1),
            "ctr": round(r.metrics.ctr, 4),
            "avg_cpc": micros_to_cad(r.metrics.average_cpc),
            "cpa": micros_to_cad(r.metrics.cost_per_conversion),
        })
    return keywords

def pull_search_terms(ga, monday, sunday):
    print("  [4/11] Search terms...")
    q = f"""
        SELECT
            search_term_view.search_term,
            search_term_view.status,
            campaign.id, campaign.name,
            ad_group.id, ad_group.name,
            metrics.impressions, metrics.clicks, metrics.cost_micros,
            metrics.conversions, metrics.all_conversions, metrics.ctr
        FROM search_term_view
        WHERE segments.date BETWEEN '{monday}' AND '{sunday}'
        ORDER BY metrics.cost_micros DESC
        LIMIT 500
    """
    rows = query_with_retry(ga, CID, q)
    terms = []
    for r in rows:
        terms.append({
            "term": r.search_term_view.search_term,
            "status": str(r.search_term_view.status),
            "campaign_id": str(r.campaign.id),
            "campaign": r.campaign.name,
            "ad_group_id": str(r.ad_group.id),
            "ad_group": r.ad_group.name,
            "impressions": r.metrics.impressions,
            "clicks": r.metrics.clicks,
            "spend": micros_to_cad(r.metrics.cost_micros),
            "conversions": round(r.metrics.conversions, 1),
            "all_conversions": round(r.metrics.all_conversions, 1),
            "ctr": round(r.metrics.ctr, 4),
        })
    return terms

def pull_ads(ga, monday, sunday):
    print("  [5/11] Ad performance (RSAs)...")
    q = f"""
        SELECT
            ad_group_ad.ad.id, ad_group_ad.ad.type,
            ad_group_ad.ad.responsive_search_ad.headlines,
            ad_group_ad.ad.responsive_search_ad.descriptions,
            ad_group_ad.ad.final_urls,
            ad_group_ad.status,
            campaign.name, ad_group.name,
            metrics.impressions, metrics.clicks, metrics.ctr,
            metrics.conversions, metrics.cost_micros, metrics.cost_per_conversion
        FROM ad_group_ad
        WHERE segments.date BETWEEN '{monday}' AND '{sunday}'
            AND ad_group_ad.status != 'REMOVED'
        ORDER BY metrics.impressions DESC
        LIMIT 50
    """
    rows = query_with_retry(ga, CID, q)
    ads = []
    for r in rows:
        headlines = []
        descriptions = []
        if r.ad_group_ad.ad.responsive_search_ad.headlines:
            headlines = [h.text for h in r.ad_group_ad.ad.responsive_search_ad.headlines]
        if r.ad_group_ad.ad.responsive_search_ad.descriptions:
            descriptions = [d.text for d in r.ad_group_ad.ad.responsive_search_ad.descriptions]
        ads.append({
            "ad_id": str(r.ad_group_ad.ad.id),
            "type": str(r.ad_group_ad.ad.type_),
            "status": str(r.ad_group_ad.status),
            "campaign": r.campaign.name,
            "ad_group": r.ad_group.name,
            "headlines": headlines,
            "descriptions": descriptions,
            "final_urls": list(r.ad_group_ad.ad.final_urls),
            "impressions": r.metrics.impressions,
            "clicks": r.metrics.clicks,
            "ctr": round(r.metrics.ctr, 4),
            "conversions": round(r.metrics.conversions, 1),
            "spend": micros_to_cad(r.metrics.cost_micros),
            "cpa": micros_to_cad(r.metrics.cost_per_conversion),
        })
    return ads

def pull_hourly(ga, monday, sunday):
    print("  [6/11] Hour-of-day performance...")
    q = f"""
        SELECT
            segments.hour,
            metrics.impressions, metrics.clicks, metrics.cost_micros,
            metrics.conversions
        FROM campaign
        WHERE segments.date BETWEEN '{monday}' AND '{sunday}'
            AND campaign.status = 'ENABLED'
    """
    rows = query_with_retry(ga, CID, q)
    hours = {}
    for r in rows:
        h = r.segments.hour
        if h not in hours:
            hours[h] = {"hour": h, "spend": 0, "clicks": 0, "impressions": 0, "conversions": 0}
        hours[h]["spend"] += micros_to_cad(r.metrics.cost_micros)
        hours[h]["clicks"] += r.metrics.clicks
        hours[h]["impressions"] += r.metrics.impressions
        hours[h]["conversions"] += r.metrics.conversions
    result = []
    for h in sorted(hours.keys()):
        d = hours[h]
        d["spend"] = round(d["spend"], 2)
        d["conversions"] = round(d["conversions"], 1)
        d["cpa"] = round(d["spend"] / d["conversions"], 2) if d["conversions"] > 0 else 0
        result.append(d)
    return result

def pull_daily(ga, monday, sunday):
    print("  [7/11] Day-of-week performance...")
    q = f"""
        SELECT
            segments.day_of_week,
            metrics.impressions, metrics.clicks, metrics.cost_micros,
            metrics.conversions
        FROM campaign
        WHERE segments.date BETWEEN '{monday}' AND '{sunday}'
            AND campaign.status = 'ENABLED'
    """
    rows = query_with_retry(ga, CID, q)
    days = {}
    for r in rows:
        d = str(r.segments.day_of_week)
        if d not in days:
            days[d] = {"day": d, "spend": 0, "clicks": 0, "impressions": 0, "conversions": 0}
        days[d]["spend"] += micros_to_cad(r.metrics.cost_micros)
        days[d]["clicks"] += r.metrics.clicks
        days[d]["impressions"] += r.metrics.impressions
        days[d]["conversions"] += r.metrics.conversions
    result = []
    for d in sorted(days.keys()):
        v = days[d]
        v["spend"] = round(v["spend"], 2)
        v["conversions"] = round(v["conversions"], 1)
        v["cpa"] = round(v["spend"] / v["conversions"], 2) if v["conversions"] > 0 else 0
        result.append(v)
    return result

def pull_device(ga, monday, sunday):
    print("  [8/11] Device performance...")
    q = f"""
        SELECT
            segments.device,
            metrics.impressions, metrics.clicks, metrics.cost_micros,
            metrics.conversions, metrics.average_cpc
        FROM campaign
        WHERE segments.date BETWEEN '{monday}' AND '{sunday}'
            AND campaign.status = 'ENABLED'
    """
    rows = query_with_retry(ga, CID, q)
    devices = {}
    for r in rows:
        d = str(r.segments.device)
        if d not in devices:
            devices[d] = {"device": d, "spend": 0, "clicks": 0, "impressions": 0, "conversions": 0}
        devices[d]["spend"] += micros_to_cad(r.metrics.cost_micros)
        devices[d]["clicks"] += r.metrics.clicks
        devices[d]["impressions"] += r.metrics.impressions
        devices[d]["conversions"] += r.metrics.conversions
    result = []
    for d, v in devices.items():
        v["spend"] = round(v["spend"], 2)
        v["conversions"] = round(v["conversions"], 1)
        v["cpa"] = round(v["spend"] / v["conversions"], 2) if v["conversions"] > 0 else 0
        result.append(v)
    return result

def pull_geo(ga, monday, sunday):
    print("  [9/11] Geographic performance...")
    q = f"""
        SELECT
            geographic_view.country_criterion_id,
            geographic_view.location_type,
            metrics.impressions, metrics.clicks, metrics.cost_micros,
            metrics.conversions
        FROM geographic_view
        WHERE segments.date BETWEEN '{monday}' AND '{sunday}'
        ORDER BY metrics.cost_micros DESC
        LIMIT 50
    """
    try:
        rows = query_with_retry(ga, CID, q)
        geo = []
        for r in rows:
            geo.append({
                "location_id": str(r.geographic_view.country_criterion_id),
                "location_type": str(r.geographic_view.location_type),
                "impressions": r.metrics.impressions,
                "clicks": r.metrics.clicks,
                "spend": micros_to_cad(r.metrics.cost_micros),
                "conversions": round(r.metrics.conversions, 1),
            })
        return geo
    except Exception as e:
        print(f"  WARNING: Geo query failed: {str(e)[:100]}", file=sys.stderr)
        return []

def pull_negatives(ga):
    print("  [10/11] Existing negative keywords...")
    q = """
        SELECT
            campaign_criterion.keyword.text,
            campaign_criterion.keyword.match_type,
            campaign.name, campaign.id
        FROM campaign_criterion
        WHERE campaign_criterion.negative = TRUE
            AND campaign_criterion.type = KEYWORD
    """
    rows = query_with_retry(ga, CID, q)
    negatives = []
    for r in rows:
        negatives.append({
            "keyword": r.campaign_criterion.keyword.text,
            "match_type": str(r.campaign_criterion.keyword.match_type),
            "campaign": r.campaign.name,
            "campaign_id": str(r.campaign.id),
        })
    return negatives

def pull_conversion_actions(ga, monday, sunday):
    print("  [11/11] Conversion action breakdown...")
    q = f"""
        SELECT
            segments.conversion_action_name,
            metrics.conversions, metrics.all_conversions,
            metrics.conversions_value
        FROM campaign
        WHERE segments.date BETWEEN '{monday}' AND '{sunday}'
            AND campaign.status = 'ENABLED'
    """
    rows = query_with_retry(ga, CID, q)
    actions = {}
    for r in rows:
        name = r.segments.conversion_action_name
        if name not in actions:
            actions[name] = {"name": name, "conversions": 0, "all_conversions": 0, "value": 0}
        actions[name]["conversions"] += r.metrics.conversions
        actions[name]["all_conversions"] += r.metrics.all_conversions
        actions[name]["value"] += r.metrics.conversions_value
    result = []
    for a in actions.values():
        a["conversions"] = round(a["conversions"], 1)
        a["all_conversions"] = round(a["all_conversions"], 1)
        a["value"] = round(a["value"], 2)
        result.append(a)
    return sorted(result, key=lambda x: -x["conversions"])

def main():
    load_env()
    client = get_client()
    ga = client.get_service("GoogleAdsService")

    monday, sunday, prior_monday, prior_sunday = compute_dates()
    print(f"Pulling data for week: {monday} to {sunday}")
    print(f"Prior week: {prior_monday} to {prior_sunday}")

    data = {
        "meta": {
            "account_id": CID,
            "account_name": "Bloom Technical",
            "currency": "CAD",
            "timezone": "America/Vancouver",
            "report_week_start": str(monday),
            "report_week_end": str(sunday),
            "prior_week_start": str(prior_monday),
            "prior_week_end": str(prior_sunday),
            "pulled_at": datetime.now(zoneinfo.ZoneInfo("America/Vancouver")).isoformat(),
        },
        "this_week": {"campaigns": pull_campaign_performance(ga, monday, sunday)},
        "prior_week": {"campaigns": pull_prior_week_totals(ga, prior_monday, prior_sunday)},
        "keywords": pull_keywords(ga, monday, sunday),
        "search_terms": pull_search_terms(ga, monday, sunday),
        "ads": pull_ads(ga, monday, sunday),
        "hourly_performance": pull_hourly(ga, monday, sunday),
        "daily_performance": pull_daily(ga, monday, sunday),
        "device_performance": pull_device(ga, monday, sunday),
        "geo_performance": pull_geo(ga, monday, sunday),
        "negative_keywords": pull_negatives(ga),
        "conversion_actions": pull_conversion_actions(ga, monday, sunday),
    }

    # Compute totals
    for period in ["this_week", "prior_week"]:
        camps = data[period]["campaigns"]
        totals = {
            "spend": round(sum(c["spend"] for c in camps), 2),
            "clicks": sum(c["clicks"] for c in camps),
            "impressions": sum(c["impressions"] for c in camps),
            "conversions": round(sum(c["conversions"] for c in camps), 1),
        }
        if totals["impressions"] > 0:
            totals["ctr"] = round(totals["clicks"] / totals["impressions"], 4)
        else:
            totals["ctr"] = 0
        if totals["clicks"] > 0:
            totals["avg_cpc"] = round(totals["spend"] / totals["clicks"], 2)
        else:
            totals["avg_cpc"] = 0
        if totals["conversions"] > 0:
            totals["cpa"] = round(totals["spend"] / totals["conversions"], 2)
        else:
            totals["cpa"] = 0
        data[period]["totals"] = totals

    output_dir = PROJECT_DIR / "outputs" / "weekly-data"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"week-of-{monday}.json"

    with open(output_path, "w") as f:
        json.dump(data, f, indent=2, default=str)

    size_kb = output_path.stat().st_size / 1024
    print(f"\nSaved: {output_path} ({size_kb:.1f} KB)")
    print(f"  This week: ${data['this_week']['totals']['spend']:.2f} spend, "
          f"{data['this_week']['totals']['clicks']} clicks, "
          f"{data['this_week']['totals']['conversions']:.1f} conversions")
    print(f"  Prior week: ${data['prior_week']['totals']['spend']:.2f} spend, "
          f"{data['prior_week']['totals']['clicks']} clicks, "
          f"{data['prior_week']['totals']['conversions']:.1f} conversions")

    return str(output_path)

if __name__ == "__main__":
    result = main()
    print(f"\n✅ Data pull complete: {result}")
