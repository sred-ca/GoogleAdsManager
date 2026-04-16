# SRED.ca Google Ads Strategy

Living document updated weekly by the Google Ads Manager plugin.

## Account Overview

- **Account:** Bloom Technical Advisors (CID: 5552474733)
- **Manager:** SRED.ca (5122627517)
- **Currency:** CAD
- **Timezone:** America/Vancouver
- **Consultant:** alden@plusroi.com (PlusROI) — under review

## Current Performance Snapshot

```yaml
as_of: 2026-04-15
data_window: lifetime (Apr 2022 - Apr 2026)
total_spend_cad: 93104.67
total_clicks: 7572
total_impressions: 141282
total_conversions: 2349.3
avg_ctr: 0.0536
avg_cpc_cad: 12.30
avg_cpa_cad: 39.63
active_months: 48
recent_monthly_spend: 3500-4100
recent_ctr: 0.081-0.088
recent_cpa: 33-40
recent_impression_share: 0.33-0.36
```

## Campaign Architecture

| Campaign | Status | Daily Budget | Bid Strategy | Ad Groups |
|----------|--------|-------------|--------------|-----------|
| Bloom RSA 1 | Enabled | $75/day | Maximize Conversions | Consultant/Company, Eligibility/Credit |
| Competitor | Enabled | $5/day | Max Conv (tCPA $65) | Ad group 1 (infinity sred) |
| DSA | Paused | $15/day | Maximize Conversions | All Webpages |
| Bloom RSA 1 #3 | Removed | — | — | — |

## Conversion Actions (Active)

| Action | Type | Counts In Conversions | Quality Tier |
|--------|------|----------------------|-------------|
| thankyou_page_view | GA4 event | Yes | Tier 1 (lead) |
| call_click | GA4 event | Yes | Tier 2 (intent) |
| email_click | GA4 event | Yes | Tier 3 (intent) |
| au_visited_2_pages | GA4 event | Yes | Tier 4 (EXCLUDE — inflates CPA) |

**Known issue:** `au_visited_2_pages` is counted as a conversion, inflating conversion numbers by ~30-40%. "True CPA" excluding this action is likely $50-65 vs reported $33-40.

## ICP Alignment

SRED.ca targets Canadian tech companies (5-100 employees) with active R&D. Google Ads should:
- Target Canada only (confirmed: geo shows only Canadian traffic)
- Focus on SR&ED-specific keywords (not generic R&D tax credits)
- Prioritize high-intent buyer terms ("consultant", "company", "services") over informational ("eligibility", "what is", "calculator")
- Ad copy should reflect flat-fee positioning vs contingency competitors

## Known Issues (from forensic audit, 2026-04-15)

1. **Quality Score 5** on core keywords — landing page score 2 (Below Average). Needs dedicated landing pages.
2. **Impression share 33-36%** — budget-constrained + QS drag. Missing 2/3 of eligible searches.
3. **19 unique negative keywords** in 4 years — critically underthin. Wasting ~$1,100/year on informational queries.
4. **No ad schedule** — ads run 24/7 but overnight (11pm-6am) has near-zero conversions.
5. **Weekend CPA 15-25% higher** than weekdays — no bid adjustments.
6. **97% of traffic to homepage** — no dedicated landing pages for eligibility or pricing queries.
7. **Competitor campaign underinvested** — best CPA ($18.52) and CTR (15.95%) but only $5/day budget.

## Patterns & Insights

**[2026-04-15] Initial Baseline:**
Account has been running since April 2022. Significant spend ramp in Sep-Oct 2025 ($7.7K and $12.2K — investigate). CTR doubled from ~5% (2024) to ~8.5% (2026) — ad copy improvements working. Provocative headlines ("Buying Your Consultant a Boat?", "Stop Overpaying") outperform generic copy on both CTR and CPA. "sr&ed consultant" is the money keyword: $21.5K lifetime, 587 conversions, best CPA. Competitor targeting (infinity sred) is the most efficient strategy but barely funded.

## Completed Actions

| Date | Action | Rationale | Result |
|------|--------|-----------|--------|
| (none yet) | | | |

## Quarterly Strategy Review Notes

Next review: Q1 FY2027 (Aug 2026)
