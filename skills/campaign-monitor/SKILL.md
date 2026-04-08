# Campaign Monitor Skill

## Purpose
Pull performance data, generate reports, and surface anomalies before they become expensive problems. This skill is the primary read-only interface to campaign data — run it on-demand or on a schedule to stay on top of what's happening.

## When To Use This Skill
- User asks for a performance summary ("how are my campaigns doing?", "what did we spend this week?")
- User wants to check for problems ("anything weird going on?", "any campaigns burning budget?")
- Scheduled daily/weekly monitoring run
- Before making optimization decisions — always start with a monitoring pass

## Tools Used (AdLoop)
- `get_campaign_performance` — primary tool for spend, clicks, conversions, CPA, ROAS
- `get_ad_performance` — ad copy CTR and engagement
- `get_keyword_performance` — keyword-level metrics and Quality Scores
- `get_search_terms` — actual queries triggering ads (feeds into Keyword Manager)
- `get_pmax_performance` — Performance Max specific metrics
- `get_recommendations` — Google's auto-generated suggestions (informational only — don't apply without review)
- `health_check` — run first if anything looks broken

## Standard Monitoring Workflow

### 1. Daily Check (5 min)
```
1. get_campaign_performance (date_range: YESTERDAY)
2. Compare spend vs. daily budget target
3. Flag any campaign with spend >120% of its daily budget share
4. Flag any campaign with 0 conversions if it spent >$20
5. Report: spend total, top campaign, any flags
```

### 2. Weekly Summary (10 min)
```
1. get_campaign_performance (date_range: LAST_7_DAYS)
2. get_campaign_performance (date_range: LAST_14_DAYS) — for comparison
3. Calculate WoW change: spend, clicks, conversions, CPA, ROAS
4. get_keyword_performance (date_range: LAST_7_DAYS)
5. get_search_terms (date_range: LAST_7_DAYS)
6. Identify top 3 performers and bottom 3 performers by ROAS
7. Flag keywords with Quality Score < 5
8. Report: full weekly summary with WoW comparison
```

### 3. Anomaly Check
Run when something feels off, or as part of any monitoring pass:
```
Spend spike: campaign spend >150% of 7-day daily average
Conversion drop: conversions down >30% WoW with similar spend
CTR drop: CTR down >25% WoW (possible ad disapproval or ranking issue)
Zero conversions: any campaign spending >$50 with 0 conversions in 7 days
Quality Score: any keyword at QS 1-3 (immediate review needed)
```

## Report Format

### Daily Report
```
SRED.ca Google Ads — Daily Report [DATE]

Total spend: $XX.XX (budget: $XX.XX/day — X% paced)

Campaigns:
  [Name]  $XX.XX  XX clicks  XX conv  $XX CPA
  [Name]  $XX.XX  XX clicks  XX conv  $XX CPA

⚠ Flags: [list any anomalies, or "None"]
```

### Weekly Report
```
SRED.ca Google Ads — Weekly Report [DATE RANGE]

                  This Week    Last Week    Change
Spend             $XX.XX       $XX.XX       +X%
Clicks            XXX          XXX          +X%
Conversions       XX           XX           +X%
CPA               $XX.XX       $XX.XX       -X%
ROAS              X.Xx         X.Xx         +X%

Top performers (by ROAS): [list]
Needs attention: [list]

Keyword flags: [QS issues, high spend / no conversion]
Search terms to review: [unusual queries worth adding as negatives]
```

## Key Metrics — What They Mean for SRED.ca

| Metric | What It Means | Target (adjust based on actuals) |
|--------|--------------|----------------------------------|
| CPA (Cost Per Acquisition) | Cost per lead/form fill | Depends on lead value — track over time |
| ROAS | Return on ad spend | >3x is healthy for most B2B |
| CTR | Click-through rate | >3% for Search is strong |
| Quality Score | Google's 1-10 rating for keyword relevance | Target 7+ |
| Impression Share | % of eligible impressions you're showing for | >50% for branded terms |

## Anomaly Thresholds (Defaults — Adjust Over Time)
```yaml
spend_spike_pct: 150        # Alert if daily spend > 150% of 7-day avg
conversion_drop_pct: 30     # Alert if conversions down >30% WoW
ctr_drop_pct: 25            # Alert if CTR down >25% WoW
zero_conversion_spend: 50   # Alert if $50+ spent with 0 conversions
low_quality_score: 5        # Alert if QS < 5
```

## Notes
- Always use `dry_run=true` (default) — this skill is read-only, no mutations
- Date ranges: prefer `LAST_7_DAYS`, `LAST_14_DAYS`, `LAST_30_DAYS` for consistency
- For SRED.ca, the key conversion is likely form submission / lead — confirm which conversion action is tracked before interpreting CPA/ROAS
- Search term reports are gold for negative keyword discovery — always review weekly
