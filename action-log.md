# Google Ads Manager — Action Log

Append-only log of all changes made by the AI Google Ads Manager.
Most recent entries at the top.

---

## 2026-04-20 — Weekly Review (Week of Apr 13-19, 2026)

**Type:** Weekly Review
**Data file:** outputs/weekly-data/week-of-2026-04-13.json
**Report:** outputs/reports/google-ads-report-2026-04-13.pdf

**Key Metrics:** $467.46 spend | 48 clicks | 8 conv (3 true leads) | $58.43 CPA ($155.82 true CPA) | 26.1% imp share
**vs Prior Week:** spend -10.5% | clicks -14.3% | CPA +34.2%
**vs Benchmark:** CTR 8.3% (exceeds 5.65% avg) | CPA $58.43 (below $141 avg) | Imp Share 26.1% (below 50% target)
**True Conversions:** 3 thankyou_page_view (first real leads after conversion tracking fix); 5 au_visited_2_pages (still counting, recalibration in progress)

**Automated Actions:**
- Added negative keyword: "sr&ed tax credits" [EXACT] to Bloom RSA 1 ($29.68 waste, 0 conv) — resource: campaignCriteria/16796057952~509519582394
- Added negative keyword: "sr&ed specialist" [EXACT] to Bloom RSA 1 ($32.68 waste, 0 conv) — resource: campaignCriteria/16796057952~461167937234

**Recommendations Generated:**
1. [MEDIUM] P-2026-04-13-005: Reduce overnight bids (11pm-6am) -80% — $12.85 overnight spend, 0 conversions
2. [MEDIUM] P-2026-04-13-003: Landing page for "sr&ed eligible expenditures" (QS:2, $69.37/week)
3. [MEDIUM] P-2026-04-13-004: Landing page for "sr&ed tax credit eligibility" (QS:4, $47.70/week)
4. [LOW] P-2026-04-13-006: Reduce weekend bids -30% (weekend CPA 2.4x weekday)

**Prior Week Outcomes:**
- "sred credits" negative working — reduced from $25.55 to $5.97 (residual only, status EXCLUDED)
- Budget increase $75→$90 confirmed: budget lost IS dropped 72.4% → 42.6%
- Conversion tracking fix confirmed: 3 real leads visible this week (vs 0 last week)

**Errors:** None. Gmail draft created (ID: r7372601908104388372); PDF must be attached manually (domain restriction).

---

## 2026-04-16 — Weekly Review (Week of Apr 6-12, 2026)

**Type:** Weekly Review
**Data file:** outputs/weekly-data/week-of-2026-04-06.json
**Report:** outputs/reports/google-ads-report-2026-04-06.pdf

**Key Metrics:** $522.60 spend | 56 clicks | 12.0 conv | $43.55 CPA | 23.4% imp share
**vs Prior Week:** spend -5.8% | clicks -15.2% | CPA +41.4%
**vs Benchmark:** CTR 8.2% (exceeds 5.65% avg) | CPA $43.55 (below $141 avg) | Imp Share 23.4% (below 50% target)
**True Conversions:** 0 (all 12 were 2+ page visits)

**Automated Actions:**
- Added negative keyword: "sred credits" [EXACT] to Bloom RSA 1 (was $25.55 waste, 0 conv)

**Recommendations Generated:**
1. [HIGH] Increase Bloom RSA 1 daily budget $75 -> $90/day
2. [HIGH] CPA spiked 41% WoW — investigate search term quality
3. [CRITICAL] Remove "au_visited_2_pages" from Conversions column in Google Ads

**Errors:** None. Gmail draft created but PDF attachment requires manual step (Gmail domain restricted for automation).

---

## 2026-04-15 — Initial Setup

**Type:** Setup
**Actions:**
- Google Ads MCP server installed (google-ads-mcp via uv)
- OAuth2 credentials configured (SREDHERO project, desktop app)
- Connection tested: CID 5552474733 (Bloom Technical) confirmed
- Full baseline data pulled and saved to `outputs/baseline-data-2026-04-15.md`
- Forensic audit completed: identified 7 key issues (QS, impression share, negatives, schedule, landing pages, conversion tracking, competitor underinvestment)
