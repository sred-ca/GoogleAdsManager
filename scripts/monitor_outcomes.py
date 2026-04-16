#!/usr/bin/env python3
"""
SRED.ca Google Ads — Outcome Monitoring

Tracks hypothesis vs result for executed mutations.
Creates weekly checkpoints, renders verdicts, proposes reverts.

Run with: python3 monitor_outcomes.py --data <weekly_json> --outcomes <registry_json>
"""

import json
import argparse
from datetime import datetime, date
from pathlib import Path

PROJECT_DIR = Path(__file__).parent.parent

VERDICT_POSITIVE_THRESHOLD = 0.0
VERDICT_NEGATIVE_THRESHOLD = -0.15


def load_json(path):
    p = Path(path)
    if p.exists():
        with open(p) as f:
            return json.load(f)
    return None


def create_outcome_from_mutation(mutation, proposal, weekly_data):
    """Create an outcome record when a mutation is first executed."""
    campaign_id = proposal.get("api_params", {}).get("campaign_id", "")
    campaign = next((c for c in weekly_data["this_week"]["campaigns"] if c["id"] == str(campaign_id)), None)

    baseline = {}
    if campaign:
        baseline = {
            "spend": campaign["spend"],
            "clicks": campaign["clicks"],
            "impressions": campaign["impressions"],
            "conversions": campaign["conversions"],
            "cpa": campaign["cpa"],
            "ctr": campaign["ctr"],
            "impression_share": campaign.get("impression_share", 0),
        }

    return {
        "outcome_id": f"O-{mutation['mutation_id']}",
        "proposal_id": proposal["proposal_id"],
        "mutation_id": mutation["mutation_id"],
        "best_practice_ref": proposal.get("best_practice_ref", ""),
        "category": proposal["category"],
        "what": proposal["what"],
        "hypothesis": proposal.get("hypothesis", ""),
        "executed_at": mutation["executed_at"],
        "evaluation_window_weeks": proposal.get("evaluation_window_weeks", 2),
        "baseline_metrics": baseline,
        "weekly_checkpoints": [],
        "final_verdict": None,
        "concluded_at": None,
        "learnings": None,
    }


def get_entity_metrics(outcome, weekly_data):
    """Extract current metrics for the entity being tracked."""
    campaign_id = outcome.get("api_params", {}).get("campaign_id", "")
    if not campaign_id:
        parts = outcome.get("what", "").split()
        for camp in weekly_data["this_week"]["campaigns"]:
            if camp["name"] in outcome.get("what", ""):
                return {
                    "spend": camp["spend"],
                    "clicks": camp["clicks"],
                    "impressions": camp["impressions"],
                    "conversions": camp["conversions"],
                    "cpa": camp["cpa"],
                    "ctr": camp["ctr"],
                    "impression_share": camp.get("impression_share", 0),
                }
    else:
        for camp in weekly_data["this_week"]["campaigns"]:
            if camp["id"] == str(campaign_id):
                return {
                    "spend": camp["spend"],
                    "clicks": camp["clicks"],
                    "impressions": camp["impressions"],
                    "conversions": camp["conversions"],
                    "cpa": camp["cpa"],
                    "ctr": camp["ctr"],
                    "impression_share": camp.get("impression_share", 0),
                }
    return {}


def assess_trend(baseline, current, category):
    """Determine if the change is trending positive, negative, or inconclusive."""
    if not baseline or not current:
        return "inconclusive"

    if category == "budget":
        baseline_is = baseline.get("impression_share", 0)
        current_is = current.get("impression_share", 0)
        baseline_cpa = baseline.get("cpa", 0)
        current_cpa = current.get("cpa", 0)

        if current_is > baseline_is and (current_cpa <= baseline_cpa * 1.15 or current_cpa == 0):
            return "trending_positive"
        if current_cpa > baseline_cpa * 1.15 and baseline_cpa > 0:
            return "trending_negative"
        return "inconclusive"

    if category == "bids":
        baseline_cpa = baseline.get("cpa", 0)
        current_cpa = current.get("cpa", 0)
        if current_cpa < baseline_cpa * 0.9 and baseline_cpa > 0:
            return "trending_positive"
        if current_cpa > baseline_cpa * 1.15 and baseline_cpa > 0:
            return "trending_negative"
        return "inconclusive"

    if category == "schedule":
        baseline_cpa = baseline.get("cpa", 0)
        current_cpa = current.get("cpa", 0)
        if current_cpa < baseline_cpa * 0.95 and baseline_cpa > 0:
            return "trending_positive"
        if current_cpa > baseline_cpa * 1.1 and baseline_cpa > 0:
            return "trending_negative"
        return "inconclusive"

    return "inconclusive"


def render_verdict(outcome):
    """After evaluation window, determine final verdict."""
    checkpoints = outcome["weekly_checkpoints"]
    if not checkpoints:
        return "inconclusive"

    positive_count = sum(1 for c in checkpoints if c["trend"] == "trending_positive")
    negative_count = sum(1 for c in checkpoints if c["trend"] == "trending_negative")

    if positive_count > negative_count and positive_count >= len(checkpoints) / 2:
        return "positive"
    if negative_count > positive_count and negative_count >= len(checkpoints) / 2:
        return "negative"
    return "neutral"


def generate_revert_proposal(outcome):
    """Generate a revert proposal for a negative outcome."""
    return {
        "category": outcome["category"],
        "priority": "HIGH",
        "risk": "LOW",
        "status": "pending",
        "what": f"REVERT: {outcome['what']}",
        "why": f"Change executed on {outcome['executed_at'][:10]} produced negative results after "
               f"{len(outcome['weekly_checkpoints'])} weeks of monitoring. "
               f"Reverting to original values.",
        "best_practice_ref": f"REVERT-{outcome['best_practice_ref']}",
        "api_service": "Revert",
        "api_params": outcome.get("api_params", {}),
        "expected_impact": "Restore previous performance levels",
        "hypothesis": "Reverting the change will restore metrics to baseline levels",
        "evaluation_window_weeks": 2,
    }


def monitor(weekly_data, outcomes_path, proposals_path=None):
    outcomes = load_json(outcomes_path) or {"outcomes": []}
    week_date = weekly_data["meta"]["report_week_start"]
    revert_proposals = []

    active = [o for o in outcomes["outcomes"] if o["final_verdict"] is None]
    if not active:
        print("No active outcomes to monitor.")
        return outcomes, revert_proposals

    for outcome in active:
        current_metrics = get_entity_metrics(outcome, weekly_data)
        if not current_metrics:
            print(f"  [{outcome['outcome_id']}] Could not find entity metrics — skipping")
            continue

        trend = assess_trend(outcome["baseline_metrics"], current_metrics, outcome["category"])

        checkpoint = {
            "week": week_date,
            "metrics": current_metrics,
            "trend": trend,
            "weeks_since_execution": len(outcome["weekly_checkpoints"]) + 1,
        }
        outcome["weekly_checkpoints"].append(checkpoint)

        weeks_elapsed = len(outcome["weekly_checkpoints"])
        window = outcome.get("evaluation_window_weeks", 2)

        if weeks_elapsed >= window:
            verdict = render_verdict(outcome)
            outcome["final_verdict"] = verdict
            outcome["concluded_at"] = datetime.now().isoformat()

            if verdict == "positive":
                outcome["learnings"] = f"Change produced positive results after {weeks_elapsed} weeks. Keep."
                print(f"  [{outcome['outcome_id']}] VERDICT: POSITIVE — {outcome['what']}")
            elif verdict == "negative":
                outcome["learnings"] = f"Change produced negative results. Proposing revert."
                revert = generate_revert_proposal(outcome)
                revert_proposals.append(revert)
                print(f"  [{outcome['outcome_id']}] VERDICT: NEGATIVE — proposing revert for {outcome['what']}")
            else:
                outcome["learnings"] = f"Results inconclusive after {weeks_elapsed} weeks. No action."
                print(f"  [{outcome['outcome_id']}] VERDICT: NEUTRAL — {outcome['what']}")
        else:
            print(f"  [{outcome['outcome_id']}] Week {weeks_elapsed}/{window}: {trend} — {outcome['what']}")

    with open(outcomes_path, "w") as f:
        json.dump(outcomes, f, indent=2, default=str)

    return outcomes, revert_proposals


def main():
    parser = argparse.ArgumentParser(description="Monitor Google Ads experiment outcomes")
    parser.add_argument("--data", required=True, help="Path to this week's data JSON")
    parser.add_argument("--outcomes", default=str(PROJECT_DIR / "outputs" / "outcomes" / "outcomes-registry.json"))
    parser.add_argument("--proposals", help="Path to current week's proposals JSON (for adding revert proposals)")
    args = parser.parse_args()

    weekly_data = load_json(args.data)
    outcomes, reverts = monitor(weekly_data, args.outcomes, args.proposals)

    if reverts and args.proposals:
        proposals = load_json(args.proposals) or {"proposals": []}
        for r in reverts:
            r["proposal_id"] = f"P-REVERT-{datetime.now().strftime('%Y-%m-%d')}-{len(proposals['proposals'])+1:03d}"
            r["created_at"] = datetime.now().isoformat()
            proposals["proposals"].append(r)
        with open(args.proposals, "w") as f:
            json.dump(proposals, f, indent=2, default=str)
        print(f"\n{len(reverts)} revert proposal(s) added to {args.proposals}")

    active = sum(1 for o in outcomes.get("outcomes", []) if o["final_verdict"] is None)
    concluded = sum(1 for o in outcomes.get("outcomes", []) if o["final_verdict"] is not None)
    print(f"\nOutcomes: {active} active, {concluded} concluded")


if __name__ == "__main__":
    main()
