# Industry Benchmarks — Google Ads

Reference data for evaluating SRED.ca (Bloom Technical) Google Ads performance.

## B2B Professional Services (General)

Source: WordStream / LOCALiQ 2024-2025 benchmarks

| Metric | B2B Average | Top 25% |
|--------|------------|---------|
| CTR (Search) | 2.41% | 4.5%+ |
| CPA | $116.13 USD (~$158 CAD) | <$75 USD |
| Conversion Rate | 3.04% | 6%+ |
| CPC | $3.33 USD (~$4.50 CAD) | — |
| Impression Share | 50-70% (competitive) | 80%+ |
| Quality Score | 5-6 (average) | 7-8 |

## Legal / Tax / Consulting (Closer Vertical)

| Metric | Vertical Average |
|--------|-----------------|
| CTR | 2.93% |
| CPA | $86.02 USD (~$117 CAD) |
| Conversion Rate | 6.98% |
| CPC | $6.75 USD (~$9.20 CAD) |

## Niche B2B — SR&ED Consulting (Estimated)

Based on SRED.ca historical data + vertical analysis. Small market (Canada-only, niche tax credit).

| Metric | Estimated Range | SRED.ca Actual (Q1 2026) |
|--------|----------------|--------------------------|
| CTR | 3-6% | 8.1-8.8% (exceeds) |
| CPA | $40-80 CAD | $33-40 CAD (strong) |
| CPC | $8-18 CAD | $8-11 CAD (improving) |
| Conversion Rate | 15-25% | ~20% (healthy) |
| Impression Share | 40-60% | 33-36% (below target) |
| Quality Score | 5-7 | 5 (needs improvement) |

## Interpretation Guide

### When SRED.ca Exceeds Benchmarks
- **CTR 8%+ vs 2.4% benchmark** — Ad copy resonates strongly. The provocative messaging ("Buying Your Consultant a Boat?") works in this niche.
- **CPA $35 vs $116 benchmark** — Partially real efficiency, partially inflated by `au_visited_2_pages` conversion action. "True CPA" (excluding 2-page visits) is likely $50-65.

### Where SRED.ca Underperforms
- **Impression Share 35% vs 50-70% benchmark** — Missing 2/3 of eligible searches. Primary constraint: daily budget ($75) and Quality Score (5).
- **Quality Score 5 vs 7 target** — Landing page score of 2 (Below Average) is the main drag. Needs dedicated landing pages matching search intent.

### What the Numbers Mean for Strategy
- **High CTR + Low Impression Share** = budget-constrained, not relevance-constrained. Increasing budget should yield proportional returns.
- **QS 5 with landing page 2** = Every QS point gained saves ~16% on CPC. Going from 5→7 would save ~32% ($15K+/year at current spend).
- **CPA below benchmark** = Room to be more aggressive on bids/budget while staying profitable.

## Seasonal Patterns (SR&ED Specific)

| Period | Expected Impact | Why |
|--------|----------------|-----|
| Jan-Mar | Higher competition, higher CPC | Tax year-end prep, SR&ED filing season |
| Apr-Jun | Moderate | Post-filing, new fiscal years starting |
| Jul-Sep | Lower competition, lower CPC | Summer slowdown in professional services |
| Oct-Dec | Higher competition | Pre-year-end planning, Q4 budget pushes |

## Conversion Quality Tiers

For SRED.ca, not all conversions are equal:

| Tier | Action | Value | Weight in "True CPA" |
|------|--------|-------|---------------------|
| 1 (High) | thankyou_page_view (form submission) | Direct lead | 1.0x |
| 2 (Medium) | call_click (phone tap) | Strong intent | 0.8x |
| 3 (Medium) | email_click | Intent signal | 0.6x |
| 4 (Low) | au_visited_2_pages | Engagement only | 0.0x (exclude) |
