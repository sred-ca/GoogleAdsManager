# Budget Manager Skill

## Purpose
Track spend against budget targets, alert on overspend risk, and optimize budget allocation across campaigns. The goal is to never blow the monthly budget and never leave money on the table at end of month.

## When To Use This Skill
- User asks about budget ("how much have we spent?", "are we on track?")
- Anomaly detection flags a spend spike
- End of month approaching and pacing is off
- User wants to reallocate budget between campaigns
- Before any bid increases (check if budget headroom exists)

## Tools Used (AdLoop)
- `get_campaign_performance` — spend data by campaign and date range
- `estimate_budget` — forecast clicks/conversions at different spend levels
- `update_campaign` — adjust daily budgets (after confirmation)
- `pause_entity` — emergency spend stop
- `confirm_and_apply` — execute budget changes

## Key Concepts

### Daily Budget vs. Monthly Spend
Google Ads daily budgets are averages — Google can spend up to 2x the daily budget on any given day, but won't exceed 30.4x the daily budget in a month. This means:
- Monthly budget ÷ 30.4 = daily budget to set
- Actual spend can vary day-to-day, even if on track monthly

### Pacing
Pacing = how your actual spend compares to where it should be given the date.

```
Expected spend by today = (monthly budget / days in month) × days elapsed
Pacing % = actual spend / expected spend × 100

< 80%: Underpacing — you'll miss budget, may be leaving impressions on the table
80-110%: On track
110-130%: Slightly ahead — monitor
> 130%: Overpacing — risk of hitting monthly cap early, consider reducing daily budgets
```

## Budget Monitoring Workflow

### Daily Pacing Check
```
1. get_campaign_performance (date_range: THIS_MONTH)
2. Calculate: days elapsed, expected spend, actual spend
3. Calculate pacing % per campaign and total
4. Flag any campaign pacing >130% or <70%
5. Report summary
```

### Pacing Report Format
```
SRED.ca Budget Report — [DATE]
Month: [Month] (Day X of XX)

                Budget    Spent     Remaining   Pacing
Total           $X,XXX    $XXX      $XXX        XX%
[Campaign 1]    $XXX      $XX       $XXX        XX%
[Campaign 2]    $XXX      $XX       $XXX        XX%

Status: [On track / Overpacing — action needed / Underpacing]
Projected month-end spend: $XXX
```

## Overspend Response Workflow

### If pacing >130%
```
1. Identify which campaigns are overpacing
2. Calculate new daily budget needed to finish month on target:
   remaining_budget = monthly_budget - spent_to_date
   days_remaining = days_in_month - today
   new_daily = remaining_budget / days_remaining
3. update_campaign — draft daily budget reduction
4. Show user: "Reducing [campaign] daily budget from $X to $X to stay within monthly target"
5. Confirm → apply
```

### Emergency Pause (extreme overspend)
```
If a campaign is spending 3x normal in a single day:
1. Immediately flag to user with current spend rate
2. Offer: pause campaign or reduce daily budget by 50%
3. Never auto-pause without user confirmation
```

## Budget Reallocation Workflow

When some campaigns are underpacing and others are overpacing:
```
1. get_campaign_performance (last 30 days) — get ROAS per campaign
2. Rank campaigns by ROAS
3. Recommend: shift budget from low-ROAS underspenders to high-ROAS underspenders
4. Keep total budget constant
5. Draft changes, show table of before/after budgets and rationale
6. Confirm → apply
```

### Reallocation Principles
- Never cut a campaign to $0 — minimum $5/day keeps it learning
- Don't reallocate based on <7 days of data — too noisy
- Prioritize campaigns with strong ROAS and impression share <80% (they can absorb more budget)
- Brand campaigns (if any) should be protected — don't reduce

## Month-End Workflow (Last 5 Days of Month)
```
1. get_campaign_performance (THIS_MONTH)
2. Calculate remaining budget
3. If remaining > 5 days × daily budgets: suggest increasing daily budgets for final push
4. If remaining < 5 days × daily budgets: suggest reducing to coast to end of month
5. Always: review what worked this month for next month's budget planning
```

## Budget Forecasting
```
Use estimate_budget to answer:
- "What would happen if we increased budget by 20%?"
- "How many more leads would $500 more/month get us?"
- "Is it worth putting more budget into [campaign]?"
```

## SRED.ca Specific Notes
- SR&ED is a seasonal/intent-driven category — Q1 and Q3 (around tax deadlines) typically see higher competition and CPCs. Budget may need to flex.
- B2B leads have high value — a $200 CPA is still profitable if the lead converts to a client worth $5K+. Don't optimize purely on CPA without factoring lead quality.
- Track monthly spend in alignment with the weekly-bookkeeping skill — ad spend should reconcile with what appears in Ramp/QuickBooks.
