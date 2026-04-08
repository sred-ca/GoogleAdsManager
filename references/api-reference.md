# Google Ads API Reference

API version: v23.x  
Python library: `google-ads` (v24+)  
Base endpoint: `https://googleads.googleapis.com/v23/`

## Authentication

### Required credentials
```yaml
# ~/.adloop/config.yaml
ads:
  developer_token: "..."     # From Tools → API Center in Google Ads
  customer_id: "..."         # 10-digit account ID (no dashes)
  login_customer_id: "..."   # MCC ID (same as customer_id if no MCC)
```

### OAuth2 scopes
```
https://www.googleapis.com/auth/adwords
```

## Key Services

### GoogleAdsService
Primary query interface. Used for all `run_gaql` calls.
- `Search` — paginated results, use for most queries
- `SearchStream` — streaming results, use for large datasets (>10k rows)

### CampaignService
Create and manage campaigns.
- `MutateCampaigns` — create, update, remove campaigns
- Status values: `ENABLED`, `PAUSED`, `REMOVED`

### CampaignBudgetService
Manage campaign budgets.
- `MutateCampaignBudgets` — create, update budgets
- Budget is in micros (×1,000,000): $10/day = `10000000`

### AdGroupService
Manage ad groups.
- `MutateAdGroups` — create, update, remove ad groups

### AdGroupAdService
Manage ads.
- `MutateAdGroupAds` — create, update, remove ads
- Ad types: `RESPONSIVE_SEARCH_AD` (primary), `EXPANDED_TEXT_AD` (legacy)

### AdGroupCriterionService
Manage keywords.
- `MutateAdGroupCriteria` — add, update, remove keywords
- Keyword match types: `EXACT`, `PHRASE`, `BROAD`

### CampaignCriterionService
Manage campaign-level targeting and negative keywords.
- `MutateCampaignCriteria` — add negative keywords, geo targeting

### KeywordPlanService + KeywordPlanIdeaService
Keyword research.
- `GenerateKeywordIdeas` — volume and CPC estimates for seed keywords

## Resource Name Formats
Google Ads API uses resource names (not just IDs) for references:
```
customers/{customer_id}
customers/{customer_id}/campaigns/{campaign_id}
customers/{customer_id}/adGroups/{ad_group_id}
customers/{customer_id}/adGroupAds/{ad_group_id}~{ad_id}
customers/{customer_id}/adGroupCriteria/{ad_group_id}~{criterion_id}
customers/{customer_id}/campaignBudgets/{budget_id}
```

## Mutate Operation Structure
```python
# All write operations follow this pattern:
operation = client.get_type("CampaignOperation")
campaign = operation.update
campaign.resource_name = campaign_service.campaign_path(customer_id, campaign_id)
campaign.status = client.enums.CampaignStatusEnum.PAUSED
client.copy_from(operation.update_mask, protobuf_helpers.field_mask(None, campaign))

response = campaign_service.mutate_campaigns(
    customer_id=customer_id,
    operations=[operation]
)
```

## API Limits

| Limit | Value |
|-------|-------|
| QPS per CID | Token bucket (varies) |
| Daily basic access | 15,000 operations |
| Daily standard access | Unlimited |
| Max objects per mutate | 10,000 |
| Max GAQL results | 10,000 (use SearchStream for more) |
| AudienceInsights requests/day | ~200 |

## Backoff Strategy
```python
import time

def call_with_backoff(api_func, max_retries=5):
    for attempt in range(max_retries):
        try:
            return api_func()
        except GoogleAdsException as ex:
            for error in ex.failure.errors:
                if error.error_code.quota_error == QuotaErrorEnum.RESOURCE_TEMPORARILY_EXHAUSTED:
                    wait = (2 ** attempt) + random.uniform(0, 1)
                    time.sleep(wait)
                    break
            else:
                raise
    raise Exception("Max retries exceeded")
```

## Version Lifecycle
- v23.x: Current (announced Jan 2026, ~12 month support window)
- v22.x: Previous (sunset ~Jan 2027)
- Upgrade script: `scripts/migrate-api-version.py`
- Release notes: https://developers.google.com/google-ads/api/docs/release-notes
