# GAQL Cheatsheet — Google Ads Query Language

GAQL is SQL-like. Structure: `SELECT fields FROM resource WHERE conditions ORDER BY field LIMIT n`

## Core Resources

| Resource | What it contains |
|----------|----------------|
| `campaign` | Campaign settings, status, budget |
| `ad_group` | Ad group settings, bids, status |
| `ad_group_ad` | Individual ads and their performance |
| `ad_group_criterion` | Keywords (criteria within ad groups) |
| `search_term_view` | Actual search queries that triggered ads |
| `campaign_budget` | Budget settings |
| `customer` | Account-level info |

## Common Queries

### Campaign Performance (last 7 days)
```sql
SELECT
  campaign.id,
  campaign.name,
  campaign.status,
  metrics.impressions,
  metrics.clicks,
  metrics.cost_micros,
  metrics.conversions,
  metrics.ctr,
  metrics.average_cpc
FROM campaign
WHERE segments.date DURING LAST_7_DAYS
  AND campaign.status = 'ENABLED'
ORDER BY metrics.cost_micros DESC
```

### Keyword Performance with Quality Score
```sql
SELECT
  ad_group_criterion.keyword.text,
  ad_group_criterion.keyword.match_type,
  ad_group_criterion.quality_info.quality_score,
  ad_group_criterion.quality_info.creative_quality_score,
  ad_group_criterion.quality_info.post_click_quality_score,
  metrics.impressions,
  metrics.clicks,
  metrics.cost_micros,
  metrics.conversions,
  metrics.average_cpc
FROM ad_group_criterion
WHERE segments.date DURING LAST_30_DAYS
  AND ad_group_criterion.type = 'KEYWORD'
  AND ad_group_criterion.status != 'REMOVED'
ORDER BY metrics.cost_micros DESC
LIMIT 100
```

### Search Terms Report
```sql
SELECT
  search_term_view.search_term,
  search_term_view.status,
  campaign.name,
  ad_group.name,
  metrics.impressions,
  metrics.clicks,
  metrics.cost_micros,
  metrics.conversions
FROM search_term_view
WHERE segments.date DURING LAST_7_DAYS
ORDER BY metrics.cost_micros DESC
LIMIT 200
```

### Budget Pacing (Month-to-Date)
```sql
SELECT
  campaign.name,
  campaign_budget.amount_micros,
  metrics.cost_micros,
  metrics.impressions,
  metrics.clicks
FROM campaign
WHERE segments.date DURING THIS_MONTH
  AND campaign.status = 'ENABLED'
ORDER BY metrics.cost_micros DESC
```

### Ad Performance (RSA effectiveness)
```sql
SELECT
  ad_group_ad.ad.id,
  ad_group_ad.ad.responsive_search_ad.headlines,
  ad_group_ad.status,
  campaign.name,
  ad_group.name,
  metrics.impressions,
  metrics.clicks,
  metrics.ctr,
  metrics.conversions,
  metrics.cost_micros
FROM ad_group_ad
WHERE segments.date DURING LAST_14_DAYS
  AND ad_group_ad.status != 'REMOVED'
ORDER BY metrics.cost_micros DESC
LIMIT 50
```

### Negative Keywords
```sql
SELECT
  campaign_criterion.keyword.text,
  campaign_criterion.keyword.match_type,
  campaign_criterion.negative,
  campaign.name
FROM campaign_criterion
WHERE campaign_criterion.negative = TRUE
  AND campaign_criterion.type = 'KEYWORD'
ORDER BY campaign.name
```

## Useful Segments (date ranges)
```
TODAY
YESTERDAY
THIS_WEEK_SUN_TODAY
LAST_7_DAYS
THIS_MONTH
LAST_30_DAYS
LAST_14_DAYS
LAST_MONTH
```

## Metrics Reference
```
metrics.cost_micros          # Spend in micros (divide by 1,000,000 for $)
metrics.impressions          # Times ad was shown
metrics.clicks               # Times ad was clicked
metrics.conversions          # Conversion count
metrics.ctr                  # Click-through rate (0.05 = 5%)
metrics.average_cpc          # Average cost per click (in micros)
metrics.conversion_rate      # Conversions / clicks
metrics.cost_per_conversion  # CPA (in micros)
metrics.value_per_conversion # Conversion value / conversions
metrics.search_impression_share  # % of eligible impressions captured
```

## Key Notes
- `cost_micros` = actual cost × 1,000,000. Always divide by 1,000,000 to get dollars.
- `average_cpc` is also in micros.
- GAQL doesn't support `JOIN` — each query is against one resource with auto-joined fields via dot notation.
- `LIMIT` is required for large result sets — always use it.
- Omit `WHERE segments.date` only if you want all-time data (rarely useful).
