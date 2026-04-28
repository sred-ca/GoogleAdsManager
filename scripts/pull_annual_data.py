#!/usr/bin/env python3
"""
SRED.ca Google Ads — Annual / Fiscal Year Data Pull

Pulls monthly campaign performance for the full fiscal year (May 1 – Apr 30)
and outputs to outputs/annual-data-FYXXXX.json.

Run with:
  /Users/judebrown/.local/share/uv/tools/google-ads-mcp/bin/python3.12 pull_annual_data.py [--fy 2026]
"""

import json
import os
import sys
import time
import random
import argparse
from datetime import date, timedelta
from pathlib import Path

PROJECT_DIR = Path(__file__).parent.parent
ENV_PATH    = PROJECT_DIR / ".env"
CID         = "5552474733"


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


def fy_dates(fy: int):
    """Return (start_date, end_date) for fiscal year FY{fy}.
    FY2026 = May 1 2025 – Apr 30 2026.
    """
    start = date(fy - 1, 5, 1)
    end   = date(fy, 4, 30)
    # Don't request future dates
    today = date.today()
    if end > today:
        end = today
    return start, end


def pull_monthly_totals(ga, start: date, end: date):
    """Pull campaign performance grouped by calendar month."""
    print(f"  Pulling monthly totals {start} to {end}...")
    q = f"""
        SELECT
            segments.month,
            metrics.impressions,
            metrics.clicks,
            metrics.cost_micros,
            metrics.conversions,
            metrics.all_conversions
        FROM campaign
        WHERE segments.date BETWEEN '{start}' AND '{end}'
            AND campaign.status != 'REMOVED'
        ORDER BY segments.month ASC
    """
    rows = query_with_retry(ga, CID, q)
    months = {}
    for r in rows:
        mo = r.segments.month  # "YYYY-MM-DD" (first of month)
        if mo not in months:
            months[mo] = {
                "month":       mo[:7],  # "YYYY-MM"
                "impressions": 0,
                "clicks":      0,
                "spend":       0.0,
                "conversions": 0.0,
                "all_conversions": 0.0,
            }
        months[mo]["impressions"]     += r.metrics.impressions
        months[mo]["clicks"]          += r.metrics.clicks
        months[mo]["spend"]           += micros_to_cad(r.metrics.cost_micros)
        months[mo]["conversions"]     += r.metrics.conversions
        months[mo]["all_conversions"] += r.metrics.all_conversions

    result = []
    for mo_key in sorted(months.keys()):
        m = months[mo_key]
        m["spend"]           = round(m["spend"], 2)
        m["conversions"]     = round(m["conversions"], 1)
        m["all_conversions"] = round(m["all_conversions"], 1)
        if m["impressions"] > 0:
            m["ctr"] = round(m["clicks"] / m["impressions"], 4)
        else:
            m["ctr"] = 0.0
        if m["clicks"] > 0:
            m["avg_cpc"] = round(m["spend"] / m["clicks"], 2)
        else:
            m["avg_cpc"] = 0.0
        if m["conversions"] > 0:
            m["cpa"] = round(m["spend"] / m["conversions"], 2)
        else:
            m["cpa"] = 0.0
        result.append(m)
    return result


def pull_monthly_by_campaign(ga, start: date, end: date):
    """Pull per-campaign monthly breakdown."""
    print("  Pulling per-campaign monthly breakdown...")
    q = f"""
        SELECT
            campaign.id,
            campaign.name,
            segments.month,
            metrics.impressions,
            metrics.clicks,
            metrics.cost_micros,
            metrics.conversions
        FROM campaign
        WHERE segments.date BETWEEN '{start}' AND '{end}'
            AND campaign.status != 'REMOVED'
        ORDER BY campaign.name ASC, segments.month ASC
    """
    rows = query_with_retry(ga, CID, q)
    campaigns = {}
    for r in rows:
        name = r.campaign.name
        mo   = r.segments.month[:7]
        if name not in campaigns:
            campaigns[name] = {"name": name, "months": {}}
        if mo not in campaigns[name]["months"]:
            campaigns[name]["months"][mo] = {
                "impressions": 0, "clicks": 0, "spend": 0.0, "conversions": 0.0
            }
        m = campaigns[name]["months"][mo]
        m["impressions"]  += r.metrics.impressions
        m["clicks"]       += r.metrics.clicks
        m["spend"]        += micros_to_cad(r.metrics.cost_micros)
        m["conversions"]  += r.metrics.conversions

    # Compute derived metrics per month per campaign
    for camp in campaigns.values():
        for mo_data in camp["months"].values():
            mo_data["spend"]       = round(mo_data["spend"], 2)
            mo_data["conversions"] = round(mo_data["conversions"], 1)
            mo_data["ctr"]    = round(mo_data["clicks"] / mo_data["impressions"], 4) if mo_data["impressions"] else 0
            mo_data["avg_cpc"] = round(mo_data["spend"] / mo_data["clicks"], 2)      if mo_data["clicks"]      else 0
            mo_data["cpa"]    = round(mo_data["spend"] / mo_data["conversions"], 2)  if mo_data["conversions"] else 0

    return list(campaigns.values())


def pull_fy_totals(monthly_rows):
    """Sum up fiscal year totals from monthly rows."""
    totals = {
        "impressions":     sum(m["impressions"]     for m in monthly_rows),
        "clicks":          sum(m["clicks"]          for m in monthly_rows),
        "spend":           round(sum(m["spend"]     for m in monthly_rows), 2),
        "conversions":     round(sum(m["conversions"] for m in monthly_rows), 1),
        "all_conversions": round(sum(m["all_conversions"] for m in monthly_rows), 1),
    }
    totals["ctr"]     = round(totals["clicks"] / totals["impressions"], 4) if totals["impressions"] else 0
    totals["avg_cpc"] = round(totals["spend"] / totals["clicks"], 2)       if totals["clicks"]      else 0
    totals["cpa"]     = round(totals["spend"] / totals["conversions"], 2)  if totals["conversions"] else 0
    return totals


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--fy", type=int, default=2026, help="Fiscal year (e.g. 2026 = May 2025–Apr 2026)")
    args = parser.parse_args()

    load_env()
    client = get_client()
    ga = client.get_service("GoogleAdsService")

    start, end = fy_dates(args.fy)
    print(f"Pulling FY{args.fy} data: {start} to {end}")

    monthly   = pull_monthly_totals(ga, start, end)
    by_camp   = pull_monthly_by_campaign(ga, start, end)
    fy_totals = pull_fy_totals(monthly)

    data = {
        "meta": {
            "fiscal_year": args.fy,
            "fy_label":    f"FY{args.fy} (May {args.fy - 1} – Apr {args.fy})",
            "start_date":  str(start),
            "end_date":    str(end),
            "account_id":  CID,
            "pulled_at":   str(date.today()),
        },
        "monthly_totals":    monthly,
        "by_campaign":       by_camp,
        "fy_totals":         fy_totals,
    }

    out_dir = PROJECT_DIR / "outputs"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"annual-data-FY{args.fy}.json"

    with open(out_path, "w") as f:
        json.dump(data, f, indent=2)

    size_kb = out_path.stat().st_size / 1024
    print(f"\nSaved: {out_path} ({size_kb:.1f} KB)")
    print(f"  FY{args.fy} totals: ${fy_totals['spend']:,.2f} spend | "
          f"{fy_totals['clicks']:,} clicks | "
          f"{fy_totals['conversions']:.0f} conversions | "
          f"CTR {fy_totals['ctr']:.1%} | CPA ${fy_totals['cpa']:,.2f}")
    print(f"  Monthly rows: {len(monthly)}")

    return str(out_path)


if __name__ == "__main__":
    result = main()
    print(f"\nAnnual data pull complete: {result}")
