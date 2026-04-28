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
as_of: 2026-04-20
data_window: week of 2026-04-13 to 2026-04-19
weekly_spend_cad: 467.46
weekly_clicks: 48
weekly_impressions: 577
weekly_conversions: 8.0
weekly_true_conversions: 3
weekly_true_conversion_action: thankyou_page_view
weekly_ctr: 0.0832
weekly_avg_cpc_cad: 9.74
weekly_cpa_cad: 58.43
weekly_true_cpa: 155.82
impression_share: 0.261
budget_lost_is: 0.426
rank_lost_is: 0.313
wow_spend_change: -0.105
wow_cpa_change: +0.342
wow_conversions_change: -0.333
wow_true_conversions_change: +inf
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

**[2026-04-16] Week of Apr 6-12 Review:**
Zero real leads this week — all 12 "conversions" are just 2-page visits (au_visited_2_pages). CPA spiked 41% WoW ($30.81 -> $43.55). Impression share dropped to 23.4% (72.4% lost to budget). CTR remains strong at 8.2% (above 8% target). "sred credits" identified as waste term ($25.55, 0 conv) and added as exact match negative. Biggest concern: conversion tracking is fundamentally broken — Google is optimizing toward page visits, not actual leads. Budget increased to $90/day. Jude demoted au_visited_2_pages to Secondary conversion action.

**[2026-04-20] Week of Apr 13-19 Review:**
BREAKTHROUGH: 3 real leads (thankyou_page_view form submissions) — first week of real lead data after conversion tracking fix. Reported CPA $58.43 (8 conversions including 5 page visits still counting); True CPA $155.82 (3 actual leads/$467.46). Budget increase impact visible: budget lost IS dropped 72.4% → 42.6% — major improvement. However, rank lost IS jumped 4.3% → 31.3% — Quality Score drag is now the primary constraint. CTR maintained at 8.3% (above 8% target). Two waste terms identified and negated: "sr&ed tax credits" ($29.68, 0 conv) and "sr&ed specialist" ($32.68, 0 conv). Note: Apr 16 shows $0 spend (paused for conversion tracking change). Weekend CPA 2.4x weekday — schedule optimization warranted but needs 2-week pattern confirmation.

## Completed Actions

| Date | Action | Rationale | Result |
|------|--------|-----------|--------|
| 2026-04-16 | Added "sred credits" as exact negative to Bloom RSA 1 | $25.55 spent, 0 conversions, informational query | Reduced to $5.97 week after (residual) — working |
| 2026-04-16 | Demoted au_visited_2_pages to Secondary conversion action | 100% of prior week conversions were page visits, not leads | 3 real leads (thankyou_page_view) visible the following week |
| 2026-04-16 | Increased Bloom RSA 1 budget $75 → $90/day | Budget lost IS was 72.4%; CPA below $45 target | Budget lost IS dropped 72.4% → 42.6% the following week |
| 2026-04-20 | Added "sr&ed tax credits" as EXACT negative to Bloom RSA 1 | $29.68 spent, 0 conversions, informational query | Pending — will measure next week |
| 2026-04-20 | Added "sr&ed specialist" as EXACT negative to Bloom RSA 1 | $32.68 spent, 0 conversions, high CPC waste | Pending — will measure next week |

## Quarterly Strategy Review Notes

Next review: Q1 FY2027 (Aug 2026)
