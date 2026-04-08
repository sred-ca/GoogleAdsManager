# Keyword Manager Skill

## Purpose
Research keywords, clean up search terms, manage negative keywords, and keep the account targeting tightly relevant. Bad keyword management is the #1 source of wasted spend in Google Ads — this skill fixes that.

## When To Use This Skill
- Weekly search term review (always, without exception)
- User wants to add new keywords
- User asks "why are we showing for [irrelevant query]?"
- Launching a new ad group or campaign
- Quality Scores are low (often a relevance/keyword match problem)

## Tools Used (AdLoop)
- `get_search_terms` — actual queries that triggered your ads
- `get_keyword_performance` — performance by keyword
- `get_negative_keywords` — existing negative keyword lists
- `add_negative_keywords` — add new negatives
- `draft_keywords` — propose new keywords to add
- `estimate_budget` — keyword volume and CPC estimates
- `confirm_and_apply` — execute keyword changes

## Core Concepts

### Match Types
| Type | Example keyword | Matches | Use when |
|------|----------------|---------|----------|
| Exact | [sred consulting] | "sred consulting" only | High-intent, proven terms |
| Phrase | "sred consulting" | "best sred consulting firm" | Moderate control |
| Broad | sred consulting | Anything Google deems related | Exploration only, watch carefully |

**Default recommendation:** Start with Exact and Phrase. Use Broad only in dedicated campaigns with tight negative keyword lists.

### Negative Keywords
Prevent your ads from showing for irrelevant queries. Categories:
- **Competitor protection**: If you don't want to compete on competitor names
- **Informational**: "what is sred", "sred definition", "sred wiki" (research intent, not buyer intent)
- **DIY intent**: "sred template", "sred form download", "diy sred claim"
- **Job seekers**: "sred jobs", "sred careers", "sred analyst salary"
- **Wrong geography**: queries from provinces/regions you don't serve

## Weekly Search Term Review Workflow

This is the most important recurring task. Run every week.

```
1. get_search_terms (date_range: LAST_7_DAYS)
2. Review each unique query:
   - Is this what we want to show for? (intent check)
   - Did it convert? (value check)
   - Is it already a keyword? (coverage check)
3. Sort into three buckets:
   KEEP    — relevant, shows intent, leave it
   ADD     — worth adding as an exact/phrase keyword
   BLOCK   — irrelevant, add as negative
4. add_negative_keywords — draft negatives
5. draft_keywords — draft new keywords to add
6. Present both lists to user, confirm
7. apply
```

### Search Term Review Format
```
Search Term Review — [DATE RANGE]

New negatives to add (X terms):
  "irrelevant query 1" — reason
  "irrelevant query 2" — reason

New keywords to add (X terms):
  [new exact match term] — X clicks, X conv last 7 days
  "new phrase term" — X clicks, 0 conv (test)

High-performing terms (already converting):
  [existing keyword] — X conv, $XX CPA ✓
```

## Keyword Research Workflow

When launching a new campaign or expanding targeting:

```
1. Start with seed terms from the brief / ICP
2. estimate_budget — get volume and CPC estimates for seed terms
3. Think in themes: group related terms into ad group clusters
4. For each theme:
   - 1-3 exact match core terms
   - 2-4 phrase match variants
   - Avoid broad unless explicitly exploring
5. draft_keywords — propose with match types
6. Cross-check against existing negatives — don't add terms you've already blocked
7. Present to user with estimated volume and CPC
8. Confirm → apply
```

### SRED.ca Keyword Themes (Starting Points)

**Core Service:**
- [sred consulting], [sr&ed consulting], [sred consultant]
- "sred tax credit consultant", "sr&ed tax credit help"

**Problem-Aware:**
- [sred claim help], [sred application help], [sred eligible]
- "how to file sred claim", "sred claim process"

**High-Intent Buyer:**
- [hire sred consultant], [sred consulting firm], [sred services canada]
- "best sred consultants", "sred consulting toronto" (+ other cities)

**Negative Keywords (Start With):**
- "jobs", "careers", "salary", "hire" (job seekers)
- "what is", "definition", "meaning", "wiki" (informational)
- "template", "form", "download", "diy", "how to do it yourself"
- "free", "government grant" (wrong expectation)
- Competitors (decide per case)

## Quality Score Improvement Workflow

QS < 5 on a keyword = Google is saying the ad or landing page isn't relevant enough.

```
1. get_keyword_performance — find all keywords with QS < 6
2. For each low-QS keyword:
   a. Check: is the keyword in the ad headline? (if not, add it)
   b. Check: is the keyword in the landing page copy? (if not, it's a landing page issue)
   c. Check: is the keyword too broad for its ad group? (consider moving to its own ad group)
3. If headline fix: draft_responsive_search_ad with keyword in pin-1 headline
4. If landing page fix: flag to Jude — can't fix via API
5. If ad group too broad: draft new ad group for that keyword cluster
```

## Notes
- Negative keywords are free — add aggressively. You lose nothing by blocking irrelevant terms.
- Exact match in Google Ads is "close variant" — Google will show for plurals, misspellings. You can't turn this off.
- Search term reports are delayed ~24 hours — yesterday's terms won't show until today
- For SRED.ca: most valuable queries will have "consulting", "help", "services", or "hire" — these signal buyer intent vs. researcher intent
- Broad match + Smart Bidding can work well for mature accounts (100+ conversions/month) — but review search terms weekly to keep it clean
