# Common Error Codes & Fixes

## Authentication Errors

| Error | Cause | Fix |
|-------|-------|-----|
| `OAUTH_TOKEN_EXPIRED` | OAuth token has expired | Run `adloop init` to re-authenticate |
| `OAUTH_TOKEN_INVALID` | Token is malformed or revoked | Delete `~/.adloop/token.json`, re-run `adloop init` |
| `DEVELOPER_TOKEN_PROHIBITED` | Developer token not approved for this account | Check token status in Google Ads → Tools → API Center |
| `DEVELOPER_TOKEN_NOT_APPROVED` | Token is test-level, hitting non-test account | Apply for Basic access (see setup guide) |
| `AUTHORIZATION_ERROR` | Account access denied | Ensure logged-in Google account has access to the Ads account |
| `CUSTOMER_NOT_FOUND` | Customer ID is wrong | Verify 10-digit customer ID in Google Ads account settings |

## Quota Errors

| Error | Cause | Fix |
|-------|-------|-----|
| `RESOURCE_TEMPORARILY_EXHAUSTED` | QPS limit hit | Implement exponential backoff (see api-reference.md) |
| `QUOTA_ERROR` | Daily operation limit hit (Basic: 15k/day) | Reduce query frequency; apply for Standard access |

## Request Errors

| Error | Cause | Fix |
|-------|-------|-----|
| `INVALID_ARGUMENT` | Malformed request field | Check field types and formats (especially micros for money) |
| `FIELD_NOT_FOUND` | GAQL query has unknown field | Verify field name in Google Ads API docs |
| `UNPARSEABLE_REQUEST` | GAQL syntax error | Check GAQL syntax — missing quotes, wrong operators |
| `TOO_MANY_RESULTS` | Query returned >10,000 rows | Add `LIMIT` clause or use `SearchStream` |

## Campaign / Ad Group Errors

| Error | Cause | Fix |
|-------|-------|-----|
| `CAMPAIGN_NOT_FOUND` | Campaign ID doesn't exist or wrong account | Verify campaign ID from `list_accounts` output |
| `BUDGET_ERROR` | Budget amount too low | Minimum budget varies by currency; try $1+/day |
| `INVALID_BUDGET_AMOUNT` | Budget in wrong format | Budget must be in micros ($10 = 10000000) |
| `AD_GROUP_AD_ERROR` | Ad creation failed | Check headlines (3-15 required) and descriptions (2-4 required) for RSAs |
| `POLICY_VIOLATION` | Ad copy violates Google policy | Review ad text for prohibited content (all-caps, excessive punctuation, claims) |
| `DUPLICATE_CAMPAIGN_NAME` | Campaign name already exists | Use a unique name |

## Keyword Errors

| Error | Cause | Fix |
|-------|-------|-----|
| `KEYWORD_TOO_LONG` | Keyword exceeds 80 characters | Shorten keyword |
| `KEYWORD_HAS_INVALID_CHARS` | Special characters in keyword | Remove `!`, `@`, `%`, `^`, `*`, `(`, `)`, `=`, `{`, `}`, `<`, `>`, `;`, `:`, `\` |
| `CRITERION_ERROR` | Keyword already exists in ad group | Check existing keywords before adding |

## AdLoop-Specific

| Error | Cause | Fix |
|-------|-------|-----|
| `Config not found` | `~/.adloop/config.yaml` missing | Run `adloop init` |
| `Token file not found` | `~/.adloop/token.json` missing | Run `adloop init` |
| `dry_run=true` (expected) | Write blocked by safety setting | This is correct — review preview, then call `confirm_and_apply` with `dry_run=false` |
| `Budget cap exceeded` | Campaign budget exceeds `max_daily_budget` setting | Increase `safety.max_daily_budget` in config.yaml, or it's a real overspend alert |
| `Blocked operation` | Operation is in `safety.blocked_operations` list | Review and update safety config if intentional |

## Debugging Checklist
```
1. Check ~/.adloop/audit.log — last operation details
2. Run health_check tool — validates OAuth, API, and GA4 connectivity  
3. Verify customer_id in config (10 digits, no dashes)
4. Confirm developer token status: Google Ads → Tools → API Center
5. For auth errors: delete token.json and re-run adloop init
6. For quota errors: check daily operation count in API Center dashboard
```
