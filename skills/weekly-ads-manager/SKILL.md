---
name: weekly-ads-manager
description: >
  Weekly Google Ads management plugin for SRED.ca. Pulls all account data,
  compares against B2B industry benchmarks and historical performance,
  auto-executes safe optimizations (negative keywords, ad schedule),
  generates recommendations needing approval (bids, copy, budget),
  and produces a branded PDF report delivered via Gmail.
  
  Triggers: "run the ads review", "weekly ads report", "Google Ads check",
  "how are the ads doing", "ads report", "run google ads manager",
  or when the Sunday 10pm PT scheduled task fires.
---

# Weekly Google Ads Manager

One plugin, three components: **Data Pull** -> **Analysis + Actions** -> **Report + Delivery**.

## Account Details

- **Account:** Bloom Technical Advisors (CID: `5552474733`)
- **Manager:** SRED.ca (`5122627517`)
- **Currency:** CAD | **Timezone:** America/Vancouver
- **Python (data pull):** `/Users/judebrown/.local/share/uv/tools/google-ads-mcp/bin/python3.12`
- **Python (PDF):** `/usr/bin/python3`
- **Project root:** `/Users/judebrown/Documents/Claude/google-ads-manager`

## Step 1: Read Context

Read these files before doing anything:

- `google-ads-manager/references/google-ads-strategy.md` — current strategy, known issues, account structure
- `google-ads-manager/references/industry-benchmarks.md` — B2B benchmarks and interpretation guide
- `google-ads-manager/action-log.md` — last 10 entries (what was done recently)
- Most recent `google-ads-manager/outputs/weekly-data/week-of-*.json` — prior week for comparison

## Step 2: Pull Data (Component 1)

Run the data pull script:

```bash
/Users/judebrown/.local/share/uv/tools/google-ads-mcp/bin/python3.12 \
  /Users/judebrown/Documents/Claude/google-ads-manager/scripts/pull_weekly_data.py
```

This executes 11 GAQL queries and outputs a JSON file to `outputs/weekly-data/week-of-YYYY-MM-DD.json`.

**Queries included:**
1. Campaign performance (this week, daily breakdown)
2. Campaign performance (prior week)
3. Keyword performance with Quality Scores
4. Search terms (top 500 by spend)
5. RSA ad performance
6. Hour-of-day breakdown
7. Day-of-week breakdown
8. Device breakdown
9. Geographic breakdown
10. Existing negative keywords
11. Conversion action breakdown

**Date logic:** Always pulls the prior full calendar week (Monday 00:00 to Sunday 23:59 PT). Not a rolling 7-day window.

**If the script fails:** Check that OAuth credentials are valid. If token expired, re-run:
```bash
python3 /tmp/setup_adc.py
```
using the setup script pattern from the initial auth setup.

## Step 3: Analyze Performance

Load the JSON from Step 2. Compare against:

1. **Prior week JSON** (week-over-week changes)
2. **4-week rolling average** (if 4+ weekly JSONs exist in `outputs/weekly-data/`)
3. **Industry benchmarks** from `references/industry-benchmarks.md`:
   - CTR: 5.65% B2B avg, 8.0% SRED.ca target
   - CPC: $7.60 CAD B2B avg, $10.00 target
   - CPA: $141 CAD B2B avg, $45 target
   - Conversion Rate: 5.14% B2B avg
   - Impression Share: 50% target
   - Quality Score: 5.5 avg, 7+ target
4. **Conversion quality** — calculate "True CPA" excluding `au_visited_2_pages`

Produce a structured analysis covering:
- What improved vs last week (wins)
- What got worse (concerns)
- Where we stand vs benchmarks (above/below/on target)
- Budget pacing (spend vs daily budget x 7)
- Quality Score changes
- Search term waste (zero-conversion terms with spend)

## Step 4: Auto-Execute Safe Actions

These actions are safe and execute without confirmation.

### 4A: Negative Keywords

Decision tree for each search term this week:

```
IF clicks >= 1 AND conversions == 0 AND spend > $20:
  -> Check if already in negative keywords list
  -> If NOT already negative: ADD as EXACT match negative to that campaign
  -> Log to action-log.md

IF term contains clearly irrelevant words ("free", "diy", "jobs", "careers",
   "salary", "template", "download", "government grant", "what is", "define",
   "meaning", "wiki", "reddit"):
  -> ADD as PHRASE match negative to that campaign
  -> Log to action-log.md
```

**To add a negative keyword via the Google Ads API:**

```python
from google.ads.googleads.client import GoogleAdsClient
from google.auth import default

credentials, _ = default(scopes=["https://www.googleapis.com/auth/adwords"])
client = GoogleAdsClient(credentials=credentials, developer_token="K-utWwcjTvDjswCXX_VfPA")

campaign_criterion_service = client.get_service("CampaignCriterionService")
operation = client.get_type("CampaignCriterionOperation")
criterion = operation.create
criterion.campaign = f"customers/5552474733/campaigns/{campaign_id}"
criterion.negative = True
criterion.keyword.text = "the search term"
criterion.keyword.match_type = client.enums.KeywordMatchTypeEnum.EXACT  # or PHRASE

response = campaign_criterion_service.mutate_campaign_criteria(
    customer_id="5552474733",
    operations=[operation]
)
```

**Safety rules:**
- Only add to the specific campaign where the waste was detected
- EXACT match for high-spend zero-conversion terms
- PHRASE match only for clearly irrelevant qualifiers
- NEVER add BROAD match negatives
- Always check existing negatives first (from Query 10 in the JSON) to prevent duplicates

### 4B: Ad Schedule Adjustments

Only adjust if the pattern held for 2+ consecutive weeks (compare to prior week JSON):

```
IF overnight (11pm-6am PT) CPA > 2x daytime average for 2+ weeks:
  -> Set bid modifier -80% for hours 23, 0, 1, 2, 3, 4, 5

IF weekend CPA > 1.5x weekday average for 3+ weeks:
  -> Set bid modifier -30% for Saturday and Sunday

IF best hours (10am-1pm, 3-5pm PT) consistently outperform for 3+ weeks:
  -> Set bid modifier +15%
```

## Step 5: Monitor Previous Outcomes (Closed-Loop)

Check if any previously executed changes are being tracked:

```bash
python3 /Users/judebrown/Documents/Claude/google-ads-manager/scripts/monitor_outcomes.py \
  --data <this_week_json> \
  --outcomes /Users/judebrown/Documents/Claude/google-ads-manager/outputs/outcomes/outcomes-registry.json \
  --proposals <this_week_proposals_json>
```

For each active outcome:
- Compares current metrics to baseline (snapshot from when the change was made)
- Appends a weekly checkpoint with trend assessment (trending_positive/negative/inconclusive)
- If evaluation window has passed, renders final verdict (positive/neutral/negative)
- If verdict is **negative**, auto-generates a revert proposal in this week's proposals

## Step 6: Run Optimization Engine (Closed-Loop)

Evaluates best-practices rules against this week's data and generates proposals:

```bash
/Users/judebrown/.local/share/uv/tools/google-ads-mcp/bin/python3.12 \
  /Users/judebrown/Documents/Claude/google-ads-manager/scripts/optimization_engine.py \
  --data <this_week_json> \
  --output /Users/judebrown/Documents/Claude/google-ads-manager/outputs/proposals/proposals-YYYY-MM-DD.json
```

Generates max 5 proposals per week, ranked by priority. Categories:
- **budget** — increase/decrease daily budgets
- **bids** — raise/lower keyword or ad group bids
- **keywords** — add converting search terms as keywords
- **schedule** — overnight/weekend bid modifiers
- **ad_copy** — new RSA variants for underperformers
- **contractor_brief** — landing page, conversion tracking, speed work

Also generates contractor brief specs for non-API work. Run:

```bash
python3 /Users/judebrown/Documents/Claude/google-ads-manager/scripts/contractor_brief.py \
  --proposals <proposals_json>
```

## Step 7: Process Pending Approvals (Closed-Loop)

Check prior week's proposals for approved items and execute:

```bash
/Users/judebrown/.local/share/uv/tools/google-ads-mcp/bin/python3.12 \
  /Users/judebrown/Documents/Claude/google-ads-manager/scripts/execute_mutations.py \
  --proposals <prior_week_proposals_json> --execute
```

**Approval methods (check in order):**
1. Email reply from Jude — parse "Approve 1, 3" or "Approve all" from Gmail
2. Chat command — "approve proposal P-2026-04-13-001"
3. Direct JSON edit — status changed to "approved" in proposals file

**Safety:** Dry-run by default. Budget cap $150/day. Max 10 mutations per run. All before/after values logged to `outputs/mutation-log.json`. Outcome records created for every mutation.

Proposals pending 2+ weeks without action are auto-expired.

## Step 8: Lead Quality Audit

Before generating the report, verify that conversion events represent real leads — not spam form submissions from people trying to sell SRED.ca something.

**How to run:**

1. Search Gmail for HubSpot form notifications from the week:
   ```
   query: "subject:\"You've got a new submission on the HubSpot Form\" after:YYYY/MM/DD before:YYYY/MM/DD"
   ```
2. Use `get_thread` to retrieve the full body of each notification.
3. Classify each submission:

**SPAM signals (disqualify):**
- Message reads as a sales pitch (offering a service TO SRED.ca rather than asking for SR&ED help)
- Signed off with a sales title ("Sales Executive", "Business Development", "Account Manager")
- Includes "Reply STOP to opt out" or similar unsubscribe language
- Domain is a generic services company with no R&D relevance
- Message is about SEO, Wikipedia, social media, web design, recruiting, insurance, software sales, etc.

**REAL LEAD signals (count):**
- Mentions SR&ED, R&D, tax credits, CRA, eligibility, claims, funding
- Asks about fees, process, or how SRED.ca works
- Mentions their company's technical work or product development
- Has a Canadian company with a plausible R&D context

**Output a lead quality table:**

```
| Name | Company | Source | Verdict | Reason |
|------|---------|--------|---------|--------|
| ... | ...     | ...    | REAL / SPAM | one-line reason |
```

**Corrected metrics to use in the report:**
- `real_leads_total` = total form submissions minus spam
- `real_leads_paid` = real leads attributed to Google Ads (HubSpot source = PAID_SEARCH with campaign matching "bloom rsa 1" or "competitor")
- `real_leads_organic` = real leads from organic/direct sources
- `spam_count` = number of spam submissions (report separately so Jude knows the form is getting hit)
- `true_cpa_paid` = this week's total spend ÷ `real_leads_paid` (report alongside Google's reported CPA)

Note: A lead flagged as SPAM still fired `thankyou_page_view` — so Google Ads may count it as a conversion. Note the discrepancy in the report if a spam submission is attributed to PAID_SEARCH. Do NOT adjust Google's reported conversion numbers — just annotate them.

## Step 10: Update Strategy Document

Edit `references/google-ads-strategy.md`:

1. Update the **Current Performance Snapshot** YAML block with this week's numbers
2. Append new observations to **Patterns and Insights** section (only genuinely new patterns)
3. Move any completed recommendations to **Completed Actions** table

## Step 10b: Refresh Annual Data

Refresh the fiscal year performance data (monthly totals for May–Apr). Run once per week — takes ~10 seconds:

```bash
/Users/judebrown/.local/share/uv/tools/google-ads-mcp/bin/python3.12 \
  /Users/judebrown/Documents/Claude/google-ads-manager/scripts/pull_annual_data.py --fy 2026
```

Outputs to `outputs/annual-data-FY2026.json`. When the fiscal year turns over (May 1), change `--fy` to `2027`.

## Step 11: Generate PDF Report (Component 2)

Run the report generator:

```bash
python3 /Users/judebrown/Documents/Claude/google-ads-manager/scripts/generate_ads_report.py \
  --data /Users/judebrown/Documents/Claude/google-ads-manager/outputs/weekly-data/week-of-YYYY-MM-DD.json \
  --prior /Users/judebrown/Documents/Claude/google-ads-manager/outputs/weekly-data/week-of-PRIOR-DATE.json \
  --output /Users/judebrown/Documents/Claude/google-ads-manager/outputs/reports/google-ads-report-YYYY-MM-DD.pdf \
  --leads /Users/judebrown/Documents/Claude/google-ads-manager/outputs/leads-pipeline.json \
  --annual /Users/judebrown/Documents/Claude/google-ads-manager/outputs/annual-data-FY2026.json
```

The report includes:
1. **Cover** — branded SRED.ca cover
2. **Performance vs Benchmarks** — bar charts with legend, stat explanations, benchmark table
3. **Week-over-Week Summary** — KPI cards + comparison table
4. **Campaign Performance** — per-campaign breakdown with pacing alerts
5. **Keyword and Search Term Analysis** — top keywords, QS flags, wasted spend
6. **Ad Copy Performance** — RSA comparison table
7. **Time and Device Analysis** — hourly, daily, device tables
8. **Conversion Quality Audit** — action breakdown, True CPA calculation
9. **Actions and Recommendations** — automated actions taken + pending recommendations

## Step 12: Deliver via Gmail

Create a Gmail draft and send to Jude:

**To:** jude@sred.ca
**Subject:** Google Ads Weekly Report - Week of [Monday date]
**Body:**

```
Hey Jude,

Here's your Google Ads weekly report.

Quick summary:
- Spend: $[X] ([+/-X%] vs last week)
- Clicks: [X] | Google reported conversions: [X] | Reported CPA: $[X]
- vs B2B benchmark: CTR [above/below], CPA [above/below], Imp Share [X%]

Lead quality (verified via HubSpot form submissions):
- Real leads this week: [X] ([X] from paid ads, [X] organic/direct)
- Spam submissions: [X] [list names/companies if any]
- True CPA (paid leads only): $[X]

Actions taken this week:
[list any auto-executed negatives or schedule changes, or "None"]

Recommendations needing your approval:
[numbered list of HIGH/MEDIUM priority items, or "None"]

Full report attached.

— Google Ads Manager
```

**Attachment:** the PDF from Step 7

**Delivery method:** Create Gmail draft using `create_draft` tool, then use Chrome automation to open and send.

## Step 13: Log and Confirm

### Update action-log.md

Prepend a new entry at the top:

```markdown
## YYYY-MM-DD — Weekly Review (Week of [Monday]-[Sunday])

**Type:** Weekly Review
**Data file:** outputs/weekly-data/week-of-YYYY-MM-DD.json
**Report:** outputs/reports/google-ads-report-YYYY-MM-DD.pdf

**Key Metrics:** $[spend] spend | [clicks] clicks | [conversions] conv | $[CPA] CPA | [IS]% imp share
**Lead Quality:** [X] real leads ([X] paid, [X] organic/direct) | [X] spam | True CPA (paid): $[X]
**vs Prior Week:** spend [+/-X%] | clicks [+/-X%] | CPA [+/-X%]
**vs Benchmark:** CTR [above/below] | CPA [above/below] | Imp Share [above/below]

**Automated Actions:**
- [list negatives added, schedule changes, or "None"]

**Recommendations Generated:**
- [numbered list with priority]

**Errors:** [any query failures or issues, or "None"]
```

### Output completion summary

```
Google Ads Weekly Review Complete — Week of [Monday] to [Sunday]

Data: outputs/weekly-data/week-of-YYYY-MM-DD.json ([size] KB)
Report: outputs/reports/google-ads-report-YYYY-MM-DD.pdf
Email: Sent to jude@sred.ca

Key metrics:
  Spend: $X (X% vs last week)
  Clicks: X | Conv: X | CPA: $X
  Impression Share: X% (target: 50%)
  True CPA (excl. page visits): $X
  Real leads: X total (X paid, X organic) | Spam: X

Actions taken: [count] negative keywords added, [schedule changes or "no schedule changes"]
Recommendations: [count] pending your approval (see report)
Strategy doc: Updated
```

## Cadence and Scheduling

| Action | Frequency | When |
|--------|-----------|------|
| Full weekly review (this skill) | Weekly | Sunday 10pm PT |
| Negative keyword additions | Auto (within weekly review) | Sunday |
| Ad schedule adjustments | Auto (if 2+ week pattern) | Sunday |
| Budget/bid recommendations | Weekly report | Sunday |
| Ad copy recommendations | When data warrants | Sunday |
| Strategy doc update | Weekly | Sunday |
| Quarterly deep review | Quarterly | Feb 1, May 1, Aug 1, Nov 1 |

## Reference Files

- `google-ads-manager/CLAUDE.md` — project overview and architecture
- `google-ads-manager/references/google-ads-strategy.md` — living strategy doc
- `google-ads-manager/references/industry-benchmarks.md` — B2B benchmarks (WordStream 2025)
- `google-ads-manager/references/gaql-cheatsheet.md` — GAQL query reference
- `google-ads-manager/references/api-reference.md` — Google Ads API patterns
- `google-ads-manager/references/error-codes.md` — common errors and fixes
- `google-ads-manager/action-log.md` — append-only change log
- `google-ads-manager/outputs/weekly-data/` — weekly JSON snapshots
- `google-ads-manager/outputs/reports/` — weekly PDF reports
