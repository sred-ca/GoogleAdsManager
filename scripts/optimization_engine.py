#!/usr/bin/env python3
"""
SRED.ca Google Ads — Optimization Engine

Evaluates best-practices.yaml rules against weekly data,
generates proposals (API changes) and contractor brief specs.

Run with: /Users/judebrown/.local/share/uv/tools/google-ads-mcp/bin/python3.12 \
  optimization_engine.py --data <json> --output <proposals_json>
"""

import json
import os
import sys
import argparse
from datetime import datetime
from pathlib import Path
import yaml

PROJECT_DIR = Path(__file__).parent.parent
CID = "5552474733"


def load_yaml(path):
    with open(path) as f:
        return yaml.safe_load(f)


def load_json(path):
    with open(path) as f:
        return json.load(f)


def load_outcomes(path):
    if path.exists():
        with open(path) as f:
            return json.load(f)
    return {"outcomes": []}


def get_target(targets, ref):
    if ref.startswith("targets."):
        return targets[ref.split(".", 1)[1]]
    return ref


def evaluate_campaign_rules(rule, data, targets):
    proposals = []
    for camp in data["this_week"]["campaigns"]:
        match = True
        for f in rule["condition"]["filters"]:
            val = camp.get(f["field"], 0)
            threshold = f.get("value", 0)
            if "value_ref" in f:
                threshold = get_target(targets, f["value_ref"])
                if "multiplier" in f:
                    threshold *= f["multiplier"]
            if not compare(val, f["operator"], threshold):
                match = False
                break
        if match:
            proposals.append(build_campaign_proposal(rule, camp, targets, data))
    return proposals


def evaluate_keyword_rules(rule, data, targets):
    proposals = []
    seen = set()
    for kw in data["keywords"]:
        if kw["keyword"] in seen:
            continue
        match = True
        for f in rule["condition"]["filters"]:
            val = kw.get(f["field"], 0)
            if val is None:
                val = 0
            threshold = f.get("value", 0)
            if "value_ref" in f:
                threshold = get_target(targets, f["value_ref"])
                if "multiplier" in f:
                    threshold *= f["multiplier"]
            if not compare(val, f["operator"], threshold):
                match = False
                break
        if match:
            seen.add(kw["keyword"])
            proposals.append(build_keyword_proposal(rule, kw, targets))
    return proposals


def evaluate_search_term_rules(rule, data, targets):
    proposals = []
    existing_kws = {kw["keyword"].lower() for kw in data["keywords"]}
    existing_negs = {n["keyword"].lower() for n in data["negative_keywords"]}

    for term in data["search_terms"]:
        match = True
        for f in rule["condition"]["filters"]:
            if f["field"] == "not_in_keywords":
                if term["term"].lower() in existing_kws:
                    match = False
                    break
                continue
            if f["field"] == "not_in_negatives":
                if term["term"].lower() in existing_negs:
                    match = False
                    break
                continue
            val = term.get(f["field"], 0)
            if not compare(val, f["operator"], f.get("value", 0)):
                match = False
                break
        if match:
            proposals.append(build_search_term_proposal(rule, term))
    return proposals


def evaluate_ad_rules(rule, data, targets):
    proposals = []
    for ad in data["ads"]:
        if not ad.get("headlines"):
            continue
        match = True
        for f in rule["condition"]["filters"]:
            val = ad.get(f["field"], 0)
            if not compare(val, f["operator"], f.get("value", 0)):
                match = False
                break
        if match:
            proposals.append(build_ad_proposal(rule, ad))
    return proposals


def evaluate_hourly_rules(rule, data, targets):
    hourly = data.get("hourly_performance", [])
    if not hourly:
        return []
    daytime = [h for h in hourly if 8 <= h["hour"] <= 17]
    overnight = [h for h in hourly if h["hour"] < 6 or h["hour"] >= 23]
    if not daytime or not overnight:
        return []

    day_spend = sum(h["spend"] for h in daytime)
    day_conv = sum(h["conversions"] for h in daytime)
    night_spend = sum(h["spend"] for h in overnight)
    night_conv = sum(h["conversions"] for h in overnight)

    day_cpa = day_spend / day_conv if day_conv > 0 else 0
    night_cpa = night_spend / night_conv if night_conv > 0 else float("inf")

    ratio = night_cpa / day_cpa if day_cpa > 0 else 0
    if night_conv == 0 and night_spend > 0:
        ratio = float("inf")

    for f in rule["condition"]["filters"]:
        if f["field"] == "overnight_cpa_ratio":
            if ratio <= f["value"]:
                return []
        if f["field"] == "overnight_spend":
            if night_spend <= f["value"]:
                return []

    return [{
        "category": "schedule",
        "priority": "MEDIUM",
        "risk": rule["risk"],
        "what": f"Reduce overnight bids (11pm-6am) by 80%",
        "why": f"Overnight spent ${night_spend:.2f} with {night_conv:.0f} conversions. "
               f"Daytime CPA: ${day_cpa:.2f}. Overnight CPA: {'infinite' if night_conv == 0 else f'${night_cpa:.2f}'}.",
        "best_practice_ref": rule["id"],
        "api_service": "CampaignCriterionService",
        "api_params": {
            "type": "ad_schedule",
            "hours": rule["params"]["hours"],
            "bid_modifier": rule["params"]["bid_modifier"],
        },
        "expected_impact": f"Save ~${night_spend:.2f}/week in wasted overnight spend",
        "hypothesis": f"Reducing overnight bids 80% will save ${night_spend:.2f}/week without losing conversions",
        "evaluation_window_weeks": 2,
    }]


def evaluate_daily_rules(rule, data, targets):
    daily = data.get("daily_performance", [])
    if not daily:
        return []
    weekday = [d for d in daily if d["day"] in ["2", "3", "4", "5", "6"]]
    weekend = [d for d in daily if d["day"] in ["7", "8"]]
    if not weekday or not weekend:
        return []

    wd_spend = sum(d["spend"] for d in weekday)
    wd_conv = sum(d["conversions"] for d in weekday)
    we_spend = sum(d["spend"] for d in weekend)
    we_conv = sum(d["conversions"] for d in weekend)

    wd_cpa = wd_spend / wd_conv if wd_conv > 0 else 0
    we_cpa = we_spend / we_conv if we_conv > 0 else float("inf")

    ratio = we_cpa / wd_cpa if wd_cpa > 0 else 0

    for f in rule["condition"]["filters"]:
        if f["field"] == "weekend_cpa_ratio" and ratio <= f["value"]:
            return []
        if f["field"] == "weekend_spend" and we_spend <= f["value"]:
            return []

    return [{
        "category": "schedule",
        "priority": "LOW",
        "risk": rule["risk"],
        "what": f"Reduce weekend bids by 30%",
        "why": f"Weekend CPA ${we_cpa:.2f} vs weekday ${wd_cpa:.2f} (ratio: {ratio:.1f}x). "
               f"Weekend spend: ${we_spend:.2f}.",
        "best_practice_ref": rule["id"],
        "api_service": "CampaignCriterionService",
        "api_params": {
            "type": "ad_schedule",
            "days": rule["params"]["days"],
            "bid_modifier": rule["params"]["bid_modifier"],
        },
        "expected_impact": f"Reduce weekend CPA by ~30%, save ~${we_spend * 0.3:.2f}/week",
        "hypothesis": f"Reducing weekend bids 30% will lower weekend CPA below ${wd_cpa * 1.2:.2f} within 3 weeks",
        "evaluation_window_weeks": 3,
    }]


def evaluate_conversion_rules(rule, data, targets):
    conv_actions = data.get("conversion_actions", [])
    total = sum(a["conversions"] for a in conv_actions)
    if total == 0:
        return []
    low_quality = sum(a["conversions"] for a in conv_actions if "2_pages" in a.get("name", ""))
    pct = low_quality / total

    for f in rule["condition"]["filters"]:
        if f["field"] == "low_quality_pct" and pct <= f["value"]:
            return []

    return [{
        "category": "contractor_brief",
        "priority": "HIGH",
        "risk": "LOW",
        "what": "Fix conversion tracking — remove au_visited_2_pages from Conversions",
        "why": f"{pct:.0%} of conversions ({low_quality:.0f}/{total:.0f}) are low-quality '2+ page visits'. "
               "Google is optimizing bids toward page engagement, not real leads.",
        "best_practice_ref": rule["id"],
        "brief_spec": {
            "brief_type": rule["params"]["brief_type"],
            "title": rule["params"]["title"],
            "priority": "CRITICAL",
            "deadline_suggestion": "This week",
            "what_needs_to_change": "Remove 'au_visited_2_pages' from the Conversions column in Google Ads. "
                                   "Keep it as an 'All Conversions' action for reference, but exclude from bid optimization.",
            "why_it_matters": f"Currently {pct:.0%} of reported conversions are just 2-page visits. "
                              "This means Google's Smart Bidding is optimizing for page views, not form submissions or calls. "
                              "Real CPA is likely 2-3x higher than reported.",
            "specific_requirements": [
                "Go to Google Ads > Goals > Conversions > Summary",
                "Click on 'au_visited_2_pages' conversion action",
                "Change 'Include in Conversions' from Yes to No",
                "Verify 'thankyou_page_view', 'call_click', and 'email_click' remain set to Yes",
                "Allow 2 weeks for Smart Bidding to recalibrate",
            ],
            "current_state": f"12 conversion actions configured. {low_quality:.0f}/{total:.0f} conversions this week are page visits.",
            "success_criteria": "Reported conversions should decrease ~30-50% but represent real leads. CPA will increase initially but reflect true cost per lead.",
        },
        "expected_impact": "Reported CPA will rise but will reflect true cost per lead. Smart Bidding will optimize for real conversions.",
        "hypothesis": "Removing low-quality conversion action will cause Smart Bidding to target real leads within 2-3 weeks",
        "evaluation_window_weeks": 3,
    }]


def compare(val, operator, threshold):
    if operator == "lt": return val < threshold
    if operator == "lte": return val <= threshold
    if operator == "gt": return val > threshold
    if operator == "gte": return val >= threshold
    if operator == "eq": return val == threshold
    if operator == "neq": return val != threshold
    return False


def build_campaign_proposal(rule, camp, targets, data):
    if rule["action"] == "propose_budget_increase":
        current = camp.get("daily_budget_cad", 75)
        increase = rule["params"]["increase_pct"]
        max_budget = get_target(targets, rule["params"]["max_daily_cad_ref"])
        proposed = min(round(current * (1 + increase), 2), max_budget)
        return {
            "category": "budget",
            "priority": "HIGH",
            "risk": rule["risk"],
            "what": f"Increase {camp['name']} daily budget from ${current:.2f} to ${proposed:.2f}",
            "why": f"Impression share {camp.get('impression_share', 0):.1%}, losing {camp.get('budget_lost_is', 0):.1%} to budget. "
                   f"CPA ${camp.get('cpa', 0):.2f} is below ${targets['cpa_target_cad']:.2f} target.",
            "best_practice_ref": rule["id"],
            "api_service": "CampaignBudgetService",
            "api_params": {
                "campaign_id": camp["id"],
                "campaign_name": camp["name"],
                "field": "amount_micros",
                "current_value": int(current * 1_000_000),
                "proposed_value": int(proposed * 1_000_000),
            },
            "expected_impact": f"~{increase:.0%} more impressions, estimated {int(camp['clicks'] * increase)} additional clicks/week",
            "hypothesis": f"Increasing budget to ${proposed:.2f}/day will raise impression share above {camp.get('impression_share', 0) + 0.05:.0%} within 2 weeks while keeping CPA below ${targets['cpa_target_cad']:.2f}",
            "evaluation_window_weeks": 2,
        }
    return None


def build_keyword_proposal(rule, kw, targets):
    if rule["action"] == "propose_bid_increase":
        return {
            "category": "bids",
            "priority": "MEDIUM",
            "risk": rule["risk"],
            "what": f"Increase bid on \"{kw['keyword']}\" by {rule['params']['increase_pct']:.0%}",
            "why": f"CPA ${kw['cpa']:.2f} (below ${targets['cpa_target_cad']:.2f} target), "
                   f"{kw['conversions']:.0f} conversions, ${kw['spend']:.2f} spend.",
            "best_practice_ref": rule["id"],
            "api_service": "AdGroupCriterionService",
            "api_params": {
                "keyword": kw["keyword"],
                "match_type": kw["match_type"],
                "campaign": kw["campaign"],
                "ad_group": kw["ad_group"],
                "action": "bid_increase",
                "increase_pct": rule["params"]["increase_pct"],
            },
            "expected_impact": f"More impressions for a proven converting keyword",
            "hypothesis": f"Increasing bid on \"{kw['keyword']}\" will increase clicks by ~{rule['params']['increase_pct']:.0%} while maintaining CPA below target",
            "evaluation_window_weeks": 2,
        }
    if rule["action"] == "propose_bid_decrease":
        return {
            "category": "bids",
            "priority": "MEDIUM",
            "risk": rule["risk"],
            "what": f"Decrease bid on \"{kw['keyword']}\" by {rule['params']['decrease_pct']:.0%}",
            "why": f"CPA ${kw['cpa']:.2f} exceeds target ${targets['cpa_target_cad']:.2f} by {((kw['cpa']/targets['cpa_target_cad'])-1)*100:.0f}%.",
            "best_practice_ref": rule["id"],
            "api_service": "AdGroupCriterionService",
            "api_params": {
                "keyword": kw["keyword"],
                "match_type": kw["match_type"],
                "campaign": kw["campaign"],
                "ad_group": kw["ad_group"],
                "action": "bid_decrease",
                "decrease_pct": rule["params"]["decrease_pct"],
            },
            "expected_impact": f"Lower CPA on this keyword toward ${targets['cpa_target_cad']:.2f} target",
            "hypothesis": f"Reducing bid will lower CPA on \"{kw['keyword']}\" below ${targets['cpa_target_cad'] * 1.3:.2f} within 2 weeks",
            "evaluation_window_weeks": 2,
        }
    if rule["action"] == "generate_contractor_brief":
        return {
            "category": "contractor_brief",
            "priority": "MEDIUM",
            "risk": "LOW",
            "what": f"Landing page optimization needed for \"{kw['keyword']}\" (QS: {kw.get('quality_score', 'N/A')})",
            "why": f"Quality Score {kw.get('quality_score', 'N/A')}, landing page score {kw.get('landing_page_score', 'N/A')}. "
                   f"Spending ${kw['spend']:.2f}/week on this keyword.",
            "best_practice_ref": rule["id"],
            "brief_spec": {
                "brief_type": "landing_page",
                "title": f"Landing Page for \"{kw['keyword']}\"",
                "priority": "HIGH",
                "deadline_suggestion": "2 weeks",
                "what_needs_to_change": f"Create or optimize a landing page that directly addresses the search intent for \"{kw['keyword']}\".",
                "why_it_matters": f"Quality Score is {kw.get('quality_score', 'N/A')} (target: 7+). Each QS point below 7 increases CPC by ~16%. "
                                  f"Current spend: ${kw['spend']:.2f}/week.",
                "specific_requirements": [
                    f"Page headline should include \"{kw['keyword']}\" or close variant",
                    "Clear call-to-action above the fold (free consultation form)",
                    "Page load time under 3 seconds on mobile",
                    "Content should directly answer the searcher's question",
                    f"URL structure: sred.ca/{kw['keyword'].replace(' ', '-').replace('&', 'and')}/",
                ],
                "current_state": f"QS: {kw.get('quality_score', 'N/A')}, Landing: {kw.get('landing_page_score', 'N/A')}, "
                                 f"All traffic goes to sred.ca homepage",
                "success_criteria": f"Quality Score for \"{kw['keyword']}\" improves to 6+ within 4 weeks of launch",
            },
            "expected_impact": f"QS improvement from {kw.get('quality_score', 5)} to 7 would reduce CPC ~32%",
            "hypothesis": "N/A — contractor brief, not API change",
            "evaluation_window_weeks": 4,
        }
    return None


def build_search_term_proposal(rule, term):
    if rule["action"] == "propose_add_keyword":
        return {
            "category": "keywords",
            "priority": "MEDIUM",
            "risk": "LOW",
            "what": f"Add \"{term['term']}\" as PHRASE match keyword",
            "why": f"{term['conversions']:.0f} conversions, ${term['spend']:.2f} spend. "
                   f"Currently matching via broad/phrase but not a dedicated keyword.",
            "best_practice_ref": rule["id"],
            "api_service": "AdGroupCriterionService",
            "api_params": {
                "term": term["term"],
                "match_type": "PHRASE",
                "campaign_id": term.get("campaign_id", ""),
                "campaign": term["campaign"],
                "ad_group_id": term.get("ad_group_id", ""),
                "ad_group": term["ad_group"],
            },
            "expected_impact": "Better bid control on a proven converting term",
            "hypothesis": f"Adding \"{term['term']}\" as a keyword will maintain or improve conversion rate while giving better bid control",
            "evaluation_window_weeks": 2,
        }
    if rule["action"] == "auto_add_negative":
        return {
            "category": "negatives_auto",
            "priority": "LOW",
            "risk": "LOW",
            "what": f"Add \"{term['term']}\" as EXACT negative (auto)",
            "why": f"{term['clicks']} clicks, ${term['spend']:.2f} spend, 0 conversions.",
            "best_practice_ref": rule["id"],
            "api_params": {
                "term": term["term"],
                "match_type": "EXACT",
                "campaign_id": term.get("campaign_id", ""),
                "campaign": term["campaign"],
            },
            "expected_impact": f"Save ~${term['spend']:.2f}/week",
            "hypothesis": "N/A — auto-executed negative",
            "evaluation_window_weeks": 0,
        }
    return None


def build_ad_proposal(rule, ad):
    headlines = " | ".join(ad.get("headlines", [])[:3])
    return {
        "category": "ad_copy",
        "priority": "MEDIUM",
        "risk": "MEDIUM",
        "what": f"Replace underperforming RSA in {ad['campaign']} > {ad['ad_group']}",
        "why": f"CTR {ad['ctr']:.1%} (below 4% threshold), {ad['impressions']:,} impressions. "
               f"Headlines: {headlines}",
        "best_practice_ref": rule["id"],
        "api_service": "AdGroupAdService",
        "api_params": {
            "ad_id": ad["ad_id"],
            "campaign": ad["campaign"],
            "ad_group": ad["ad_group"],
            "action": "pause_and_create_new",
            "current_headlines": ad.get("headlines", []),
        },
        "expected_impact": "Higher CTR and conversion rate from refreshed ad copy",
        "hypothesis": "New RSA variant will achieve CTR above 4% within 4 weeks",
        "evaluation_window_weeks": 4,
    }


def run_engine(data, rules_config, outcomes):
    targets = rules_config["targets"]
    rules = rules_config["rules"]
    all_proposals = []
    brief_specs = []

    active_outcome_refs = {o.get("best_practice_ref") for o in outcomes.get("outcomes", [])
                          if o.get("final_verdict") is None}

    # Detect Smart Bidding — bid strategy type 10 = MAXIMIZE_CONVERSIONS, 11 = MAXIMIZE_CONVERSION_VALUE, 9 = TARGET_CPA
    smart_bidding_types = {"9", "10", "11"}
    uses_smart_bidding = any(
        str(c.get("bidding_strategy", "")) in smart_bidding_types
        for c in data.get("this_week", {}).get("campaigns", [])
    )

    for rule in rules:
        if rule["id"] in active_outcome_refs:
            continue

        if rule["condition"].get("requires_manual_bidding") and uses_smart_bidding:
            continue

        scope = rule["condition"]["scope"]
        proposals = []

        if scope == "campaign":
            proposals = evaluate_campaign_rules(rule, data, targets)
        elif scope == "keyword":
            proposals = evaluate_keyword_rules(rule, data, targets)
        elif scope == "search_term":
            proposals = evaluate_search_term_rules(rule, data, targets)
        elif scope == "ad":
            proposals = evaluate_ad_rules(rule, data, targets)
        elif scope == "hourly":
            proposals = evaluate_hourly_rules(rule, data, targets)
        elif scope == "daily":
            proposals = evaluate_daily_rules(rule, data, targets)
        elif scope == "conversion_actions":
            proposals = evaluate_conversion_rules(rule, data, targets)

        for p in proposals:
            if p is None:
                continue
            if p.get("brief_spec"):
                brief_specs.append(p.pop("brief_spec"))
            all_proposals.append(p)

    all_proposals.sort(key=lambda p: {"HIGH": 0, "MEDIUM": 1, "LOW": 2}.get(p.get("priority", "LOW"), 3))

    max_proposals = targets.get("max_proposals_per_week", 5)
    auto = [p for p in all_proposals if p["category"] == "negatives_auto"]
    non_auto = [p for p in all_proposals if p["category"] != "negatives_auto"][:max_proposals]

    return auto + non_auto, brief_specs


def main():
    parser = argparse.ArgumentParser(description="SRED.ca Google Ads Optimization Engine")
    parser.add_argument("--data", required=True, help="Path to weekly data JSON")
    parser.add_argument("--output", required=True, help="Output proposals JSON path")
    parser.add_argument("--rules", default=str(PROJECT_DIR / "references" / "best-practices.yaml"))
    parser.add_argument("--outcomes", default=str(PROJECT_DIR / "outputs" / "outcomes" / "outcomes-registry.json"))
    args = parser.parse_args()

    data = load_json(args.data)
    rules_config = load_yaml(args.rules)
    outcomes = load_outcomes(Path(args.outcomes))

    proposals, brief_specs = run_engine(data, rules_config, outcomes)

    week_start = data["meta"]["report_week_start"]
    for i, p in enumerate(proposals):
        p["proposal_id"] = f"P-{week_start}-{i+1:03d}"
        p["status"] = "auto" if p["category"] == "negatives_auto" else "pending"
        p["created_at"] = datetime.now().isoformat()

    output = {
        "meta": {
            "week_start": week_start,
            "generated_at": datetime.now().isoformat(),
            "total_proposals": len(proposals),
            "pending": len([p for p in proposals if p["status"] == "pending"]),
            "auto": len([p for p in proposals if p["status"] == "auto"]),
        },
        "proposals": proposals,
        "brief_specs": brief_specs,
    }

    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "w") as f:
        json.dump(output, f, indent=2, default=str)

    print(f"Proposals saved: {args.output}")
    print(f"  Total: {len(proposals)} ({output['meta']['pending']} pending, {output['meta']['auto']} auto)")
    for p in proposals:
        status = "AUTO" if p["status"] == "auto" else p["priority"]
        print(f"  [{status}] {p['what']}")
    if brief_specs:
        print(f"  Contractor briefs: {len(brief_specs)}")
        for b in brief_specs:
            print(f"    - {b['title']}")

    return output


if __name__ == "__main__":
    main()
