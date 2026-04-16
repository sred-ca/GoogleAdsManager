# Google Ads Manager — Action Log

Append-only log of all changes made by the AI Google Ads Manager.
Most recent entries at the top.

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
