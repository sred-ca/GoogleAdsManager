# Campaign Optimizer Skill

## Purpose
Create campaigns, adjust bids, manage ads, and optimize performance. This is the write skill — it makes changes to live campaigns. All actions use AdLoop's draft → preview → confirm workflow. **Never apply changes without showing the user a preview first.**

## When To Use This Skill
- User wants to create a new campaign ("set up a campaign targeting X")
- User wants to adjust bids ("increase bids on our best keywords")
- User wants to pause or enable campaigns/ads
- User wants to test new ad copy
- After a monitoring pass surfaces optimization opportunities

## Tools Used (AdLoop)
- `draft_campaign` — creates campaign structure (launches PAUSED)
- `update_campaign` — modifies bidding strategy, budget, targeting
- `draft_ad_group` — creates ad groups within a campaign
- `update_ad_group` — updates ad group name or CPC bid
- `draft_responsive_search_ad` — creates RSA with headlines/descriptions
- `draft_keywords` — proposes keywords with match types
- `pause_entity` — pauses campaigns, ad groups, ads, or keywords
- `enable_entity` — re-enables paused entities
- `confirm_and_apply` — executes previewed changes (requires dry_run=false)
- `get_campaign_performance` — always read first before optimizing
- `get_keyword_performance` — for bid adjustment decisions

## Safety Rules
1. **Always run a monitoring pass first** — read data before making changes
2. **Always show preview** — use draft tools, present output to user, wait for confirmation
3. **Always launch campaigns PAUSED** — user enables manually after review
4. **Never change more than one major setting per confirm** — one campaign's bids, not all campaigns at once
5. **Document every change** — AdLoop logs to `~/.adloop/audit.log` automatically

## Campaign Creation Workflow

### From a Brief
When user provides: audience, budget, goal, geography, and landing page URL.

```
1. Clarify: What's the conversion goal? (form fill, phone call, purchase?)
2. Clarify: What's the monthly budget?
3. draft_campaign — name, budget, bidding strategy, targeting
4. draft_ad_group — themed around primary keyword cluster
5. draft_responsive_search_ad — 5+ headlines, 3+ descriptions
6. draft_keywords — exact and phrase match for core terms
7. Present full preview to user
8. User confirms → confirm_and_apply (dry_run=false)
9. Remind user to enable campaign when ready
```

### Campaign Structure Best Practices (for SRED.ca)
```
Campaign: [Service] — [Match Type] — [Geography]
  Ad Group: [Keyword Theme]
    Keywords: 5-15 tightly themed keywords
    Ads: 1-2 RSAs per ad group
```

Example for SRED.ca:
```
Campaign: SR&ED Consulting — Exact — Canada
  Ad Group: SR&ED Tax Credit
    Keywords: [sred tax credit], [sr&ed credit], [sr ed consulting]
  Ad Group: SR&ED Eligibility
    Keywords: [am i eligible for sred], [sred eligibility], [sred application]
```

## Bid Adjustment Workflow

### Increase bids on top performers
```
1. get_keyword_performance (last 30 days)
2. Identify keywords: high conversions, ROAS > target, QS >= 7
3. Recommend bid increase: +10-20% for strong performers
4. update_ad_group (with new CPC bid) — draft first
5. Present preview, get confirmation
6. confirm_and_apply
```

### Decrease bids on poor performers
```
1. get_keyword_performance (last 30 days)
2. Identify keywords: spend > $30, 0 conversions, CPA > 3x target
3. Recommend: bid decrease or pause
4. Present options to user
5. Apply after confirmation
```

## Ad Copy A/B Testing Workflow
```
1. Check existing ad performance: get_ad_performance
2. Identify lowest-CTR ads
3. Draft variant: draft_responsive_search_ad with new headlines/descriptions
4. Note: Google automatically rotates RSA headline combinations
5. After 2 weeks: compare performance, pause underperformer
```

### RSA Headline Principles (for SRED.ca)
- Pin headline 1: brand/service ("SR&ED Consulting | SRED.ca")
- Headlines 2-5: value props ("Maximize Your R&D Tax Credit", "Expert SR&ED Claims", "Fast Approval Process")
- Headlines 6-10: proof/urgency ("15+ Years Experience", "Free Assessment", "Canadian-Owned")
- Descriptions: lead with benefit, end with CTA ("Get your SR&ED claim maximized. Free consultation — apply today.")

## Pausing / Enabling Entities
```
User: "pause the [campaign name]"
1. Confirm which campaign (show current status first)
2. pause_entity — draft
3. Show preview: "This will pause [name], currently spending $X/day"
4. Confirm → apply
```

## Notes
- `draft_campaign` always creates in PAUSED status — this is intentional and safe
- Bid changes take 24-48 hours to show measurable impact — don't re-adjust the same day
- For SRED.ca: Smart Bidding (Target CPA or Maximize Conversions) is better than manual CPC once you have 30+ conversions/month. Check conversion volume before recommending.
- AdLoop blocks Broad Match + Manual CPC combinations — this is correct behavior, don't work around it
