#!/usr/bin/env python3
"""
SRED.ca Google Ads — Mutation Execution Engine

Reads proposals JSON, executes approved mutations via Google Ads API.
Dry-run by default. Use --execute for real mutations.

Run with: /Users/judebrown/.local/share/uv/tools/google-ads-mcp/bin/python3.12 \
  execute_mutations.py --proposals <json> [--execute]
"""

import json
import os
import sys
import argparse
from datetime import datetime
from pathlib import Path

PROJECT_DIR = Path(__file__).parent.parent
CID = "5552474733"
MAX_MUTATIONS_PER_RUN = 10
MAX_DAILY_BUDGET_MICROS = 150_000_000
MAX_BID_DECREASE_PCT = 0.25


def load_env():
    env_path = PROJECT_DIR / ".env"
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, val = line.split("=", 1)
            os.environ.setdefault(key.strip(), val.strip())


def get_client():
    from google.ads.googleads.client import GoogleAdsClient
    from google.auth import default
    credentials, _ = default(scopes=["https://www.googleapis.com/auth/adwords"])
    return GoogleAdsClient(credentials=credentials, developer_token=os.environ["GOOGLE_ADS_DEVELOPER_TOKEN"])


def execute_budget_change(client, proposal, dry_run=True):
    params = proposal["api_params"]
    proposed = params["proposed_value"]
    if proposed > MAX_DAILY_BUDGET_MICROS:
        return {"success": False, "error": f"Proposed budget ${proposed/1e6:.2f} exceeds cap ${MAX_DAILY_BUDGET_MICROS/1e6:.2f}"}

    if dry_run:
        return {"success": True, "dry_run": True,
                "message": f"Would change budget from ${params['current_value']/1e6:.2f} to ${proposed/1e6:.2f}/day"}

    ga = client.get_service("GoogleAdsService")
    budget_query = f"""
        SELECT campaign.id, campaign_budget.resource_name, campaign_budget.amount_micros
        FROM campaign
        WHERE campaign.id = {params['campaign_id']}
    """
    rows = list(ga.search(customer_id=CID, query=budget_query))
    if not rows:
        return {"success": False, "error": "Budget resource not found for campaign"}

    budget_resource = rows[0].campaign_budget.resource_name
    budget_service = client.get_service("CampaignBudgetService")
    operation = client.get_type("CampaignBudgetOperation")
    budget = operation.update
    budget.resource_name = budget_resource
    budget.amount_micros = proposed
    from google.protobuf import field_mask_pb2
    client.copy_from(operation.update_mask, field_mask_pb2.FieldMask(paths=["amount_micros"]))

    response = budget_service.mutate_campaign_budgets(customer_id=CID, operations=[operation])
    return {"success": True, "resource": response.results[0].resource_name,
            "before": params["current_value"], "after": proposed}


def execute_negative_keyword(client, proposal, dry_run=True):
    params = proposal["api_params"]
    if dry_run:
        return {"success": True, "dry_run": True,
                "message": f"Would add negative \"{params['term']}\" [{params['match_type']}] to campaign {params['campaign']}"}

    service = client.get_service("CampaignCriterionService")
    operation = client.get_type("CampaignCriterionOperation")
    criterion = operation.create
    criterion.campaign = f"customers/{CID}/campaigns/{params['campaign_id']}"
    criterion.negative = True
    criterion.keyword.text = params["term"]
    match_type = params.get("match_type", "EXACT")
    mt_enum = client.enums.KeywordMatchTypeEnum
    mt_map = {"EXACT": mt_enum.EXACT, "PHRASE": mt_enum.PHRASE, "BROAD": mt_enum.BROAD}
    criterion.keyword.match_type = mt_map.get(match_type, mt_enum.EXACT)

    response = service.mutate_campaign_criteria(customer_id=CID, operations=[operation])
    return {"success": True, "resource": response.results[0].resource_name}


def execute_add_keyword(client, proposal, dry_run=True):
    params = proposal["api_params"]
    if dry_run:
        return {"success": True, "dry_run": True,
                "message": f"Would add keyword \"{params['term']}\" [{params['match_type']}] to {params['campaign']} > {params['ad_group']}"}

    service = client.get_service("AdGroupCriterionService")
    operation = client.get_type("AdGroupCriterionOperation")
    criterion = operation.create
    criterion.ad_group = f"customers/{CID}/adGroups/{params['ad_group_id']}"
    criterion.keyword.text = params["term"]
    mt_enum = client.enums.KeywordMatchTypeEnum
    mt_map = {"EXACT": mt_enum.EXACT, "PHRASE": mt_enum.PHRASE, "BROAD": mt_enum.BROAD}
    criterion.keyword.match_type = mt_map.get(params.get("match_type", "PHRASE"), mt_enum.PHRASE)

    response = service.mutate_ad_group_criteria(customer_id=CID, operations=[operation])
    return {"success": True, "resource": response.results[0].resource_name}


DISPATCH = {
    "budget": execute_budget_change,
    "negatives_auto": execute_negative_keyword,
    "keywords": execute_add_keyword,
}


def process_proposals(proposals_path, dry_run=True):
    with open(proposals_path) as f:
        data = json.load(f)

    approved = [p for p in data["proposals"] if p["status"] in ("approved", "auto")]
    if not approved:
        print("No approved proposals to execute.")
        return []

    if len(approved) > MAX_MUTATIONS_PER_RUN:
        print(f"WARNING: {len(approved)} approved proposals exceeds max {MAX_MUTATIONS_PER_RUN}. Processing first {MAX_MUTATIONS_PER_RUN}.")
        approved = approved[:MAX_MUTATIONS_PER_RUN]

    load_env()
    client = get_client() if not dry_run else None
    if dry_run:
        load_env()
        client = get_client()

    results = []
    mutation_log_path = PROJECT_DIR / "outputs" / "mutation-log.json"
    mutation_log = json.loads(mutation_log_path.read_text()) if mutation_log_path.exists() else {"mutations": []}

    for p in approved:
        category = p["category"]
        executor = DISPATCH.get(category)
        if not executor:
            print(f"  SKIP [{p['proposal_id']}] No executor for category '{category}'")
            results.append({"proposal_id": p["proposal_id"], "success": False, "error": f"No executor for {category}"})
            continue

        print(f"  {'DRY RUN' if dry_run else 'EXECUTING'} [{p['proposal_id']}] {p['what']}")
        try:
            result = executor(client, p, dry_run=dry_run)
            result["proposal_id"] = p["proposal_id"]
            results.append(result)

            if result["success"] and not dry_run:
                p["status"] = "executed"
                mutation_entry = {
                    "mutation_id": f"M-{datetime.now().strftime('%Y-%m-%d')}-{len(mutation_log['mutations'])+1:03d}",
                    "proposal_id": p["proposal_id"],
                    "executed_at": datetime.now().isoformat(),
                    "category": category,
                    "what": p["what"],
                    "api_params": p.get("api_params", {}),
                    "result": result,
                    "success": True,
                }
                mutation_log["mutations"].append(mutation_entry)

            if result["success"]:
                msg = result.get("message", result.get("resource", "OK"))
                print(f"    -> {msg}")
            else:
                print(f"    -> FAILED: {result.get('error', 'Unknown error')}")
                break

        except Exception as e:
            print(f"    -> ERROR: {str(e)[:200]}")
            results.append({"proposal_id": p["proposal_id"], "success": False, "error": str(e)[:200]})
            break

    if not dry_run:
        with open(proposals_path, "w") as f:
            json.dump(data, f, indent=2, default=str)
        with open(mutation_log_path, "w") as f:
            json.dump(mutation_log, f, indent=2, default=str)

    return results


def main():
    parser = argparse.ArgumentParser(description="Execute approved Google Ads mutations")
    parser.add_argument("--proposals", required=True, help="Path to proposals JSON")
    parser.add_argument("--execute", action="store_true", help="Actually execute mutations (default: dry-run)")
    args = parser.parse_args()

    mode = "LIVE EXECUTION" if args.execute else "DRY RUN"
    print(f"=== Mutation Engine ({mode}) ===")

    results = process_proposals(args.proposals, dry_run=not args.execute)

    success = sum(1 for r in results if r["success"])
    failed = sum(1 for r in results if not r["success"])
    print(f"\nResults: {success} succeeded, {failed} failed")

    return results


if __name__ == "__main__":
    main()
