#!/usr/bin/env python3
"""
SRED.ca Google Ads — Weekly Report Generator Component (v3)

Reads weekly JSON data and generates a branded PDF report.
New in v3:
  - Week-over-week change column is colour-coded (green=good, red=bad)
  - New Lead Pipeline page with WoW, source breakdown, quarterly summary,
    conversion funnel. Requires --leads outputs/leads-pipeline.json
"""

import json
import sys
import argparse
from pathlib import Path
from datetime import date as Date
from collections import defaultdict

sys.path.insert(0, "/Users/judebrown/Documents/Claude/sales-coach/.claude/skills/sred-doc-creator/scripts")
from sred_doc import SREDDoc

from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from reportlab.graphics.shapes import Drawing, Rect, String, Line
from reportlab.graphics import renderPDF
from reportlab.platypus import Paragraph

# ── Brand colours ──────────────────────────────────────────────────────────────
SRED_DARK_BLUE  = HexColor("#2F2A4F")
SRED_GREEN      = HexColor("#B7DB41")
SRED_LIGHT_BLUE = HexColor("#40BAEB")
SRED_EMERALD    = HexColor("#35B586")
SRED_GRAY       = HexColor("#4A4A4A")
SRED_LIGHT_GRAY = HexColor("#E4E4E4")
SRED_AMBER      = HexColor("#E8A838")
BENCHMARK_RED   = HexColor("#E05555")
BENCHMARK_BG    = HexColor("#F2F2F2")
DELTA_GREEN     = "#35B586"
DELTA_RED       = "#E05555"
DELTA_GRAY      = "#888888"

# ── Benchmarks & targets ───────────────────────────────────────────────────────
BENCHMARKS = {
    "ctr":              {"industry": 0.0565, "label": "B2B Avg",  "format": "pct", "good": "higher"},
    "avg_cpc":          {"industry": 7.60,   "label": "B2B Avg",  "format": "cad", "good": "lower"},
    "cpa":              {"industry": 141.00, "label": "B2B Avg",  "format": "cad", "good": "lower"},
    "conversion_rate":  {"industry": 0.0514, "label": "B2B Avg",  "format": "pct", "good": "higher"},
    "quality_score":    {"industry": 5.5,    "label": "Avg",      "format": "num", "good": "higher"},
    "impression_share": {"industry": 0.50,   "label": "B2B Target","format": "pct", "good": "higher"},
}
TARGETS = {
    "ctr":              {"value": 0.08,  "label": "Our Target"},
    "avg_cpc":          {"value": 10.00, "label": "Our Target"},
    "cpa":              {"value": 45.00, "label": "Our Target"},
    "impression_share": {"value": 0.50,  "label": "Our Target"},
    "quality_score":    {"value": 7.0,   "label": "Our Target"},
}

# good direction for WoW colour coding (higher=green, lower=green)
METRIC_GOOD = {
    "spend": "lower", "clicks": "higher", "impressions": "higher",
    "conversions": "higher", "ctr": "higher", "avg_cpc": "lower", "cpa": "lower",
    "impression_share": "higher",
}

DEVICE_LABELS = {"2": "Mobile", "3": "Tablet", "4": "Desktop", "5": "Connected TV"}
DAY_LABELS    = {"2": "Mon", "3": "Tue", "4": "Wed", "5": "Thu",
                 "6": "Fri", "7": "Sat", "8": "Sun"}

CHANNEL_DISPLAY = {
    "paid_ads":      "Paid Ads (Google)",
    "organic_search":"Organic / Content",
    "direct":        "Direct / Referral",
    "email_outreach":"Email Outreach",
    "import":        "List Import",
    "crm_manual":    "CRM / Manual",
    "other":         "Other",
}


# ── Formatting helpers ─────────────────────────────────────────────────────────
def pct(v):        return f"{v:.1%}" if v else "0.0%"
def cad(v):        return f"${v:,.2f}" if v else "$0.00"
def num(v):        return f"{v:,.0f}"
def fmt_metric(v, fmt_type):
    if fmt_type == "pct": return pct(v)
    if fmt_type == "cad": return cad(v)
    return f"{v:.1f}"

def delta_str(curr, prev):
    """Plain string delta (used internally)."""
    if not prev or prev == 0:
        return "N/A"
    change = (curr - prev) / prev
    arrow = "+" if change >= 0 else ""
    return f"{arrow}{change:.1%}"

def load_data(path):
    with open(path) as f:
        return json.load(f)

def tbl(doc, all_rows, col_widths=None):
    doc.branded_table(all_rows[0], all_rows[1:], col_widths=col_widths)


# ── Coloured delta cell ────────────────────────────────────────────────────────
def _delta_para(text, color_hex, align=TA_CENTER):
    """Paragraph with coloured bold text for WoW change cells."""
    style = ParagraphStyle(
        name="delta_cell",
        fontName="Lato-Bold",
        fontSize=9,
        textColor=HexColor(color_hex),
        alignment=align,
        spaceAfter=0,
        spaceBefore=0,
        leftIndent=2,
        rightIndent=2,
    )
    return Paragraph(text, style)

def colored_delta(curr, prev, good="higher"):
    """Return a colour-coded Paragraph for a WoW change cell.
    Green  = the change is in the good direction.
    Red    = the change is in the bad direction.
    Gray   = no prior data or no change.
    """
    if prev is None or prev == 0:
        return _delta_para("N/A", DELTA_GRAY)
    change = (curr - prev) / prev
    if abs(change) < 0.001:
        return _delta_para("— 0.0%", DELTA_GRAY)
    arrow = "▲" if change > 0 else "▼"
    text  = f"{arrow} {abs(change):.1%}"
    is_good = (good == "higher" and change > 0) or (good == "lower" and change < 0)
    return _delta_para(text, DELTA_GREEN if is_good else DELTA_RED)


# ── Lead pipeline helpers ──────────────────────────────────────────────────────
def fiscal_quarter(date_str):
    """Return (fy, q_num, q_label) for a YYYY-MM-DD date.
    FY runs May 1 – Apr 30.  Q1=May–Jul, Q2=Aug–Oct, Q3=Nov–Jan, Q4=Feb–Apr.
    """
    d = Date.fromisoformat(date_str[:10])
    m, y = d.month, d.year
    if m >= 5:
        fy = y + 1
        q  = 1 if m <= 7 else (2 if m <= 10 else 3)
    else:
        fy = y
        q  = 3 if m == 1 else 4
    labels = {1: "Q1 May–Jul", 2: "Q2 Aug–Oct", 3: "Q3 Nov–Jan", 4: "Q4 Feb–Apr"}
    return fy, q, labels[q]


def aggregate_pipeline(weeks):
    """Aggregate lead pipeline weeks into per-quarter dicts.
    Returns a dict: {(fy, q): {...metrics...}}

    For months with a pre-computed qualified_count / clients_count in summary
    (historical data where real_leads array is sparse), those values are used
    directly.  For fully-tracked weeks the real_leads array is walked instead.
    """
    quarters = defaultdict(lambda: {
        "submissions": 0, "real_leads": 0, "paid": 0, "organic": 0,
        "direct": 0, "spam": 0, "opportunities": 0, "clients": 0,
    })
    for week in weeks:
        fy, q, _ = fiscal_quarter(week["week_start"])
        key = (fy, q)
        s = week.get("summary", {})
        quarters[key]["submissions"] += s.get("total_submissions", 0)
        quarters[key]["real_leads"]  += s.get("real_leads", 0)
        quarters[key]["paid"]        += s.get("paid_leads", 0)
        quarters[key]["organic"]     += s.get("organic_leads", 0)
        quarters[key]["direct"]      += s.get("direct_leads", 0)
        quarters[key]["spam"]        += s.get("spam_count", 0)

        # Use pre-computed qualified/client counts when present (historical months)
        if "qualified_count" in s or "clients_count" in s:
            quarters[key]["opportunities"] += s.get("qualified_count", 0)
            quarters[key]["clients"]       += s.get("clients_count", 0)
        else:
            # Fully-tracked week: derive from real_leads array
            for lead in week.get("real_leads", []):
                stage = lead.get("hubspot_stage", "")
                if lead.get("converted_to_client"):
                    quarters[key]["clients"] += 1
                elif stage in ("salesqualifiedlead", "opportunity"):
                    quarters[key]["opportunities"] += 1
    return quarters


def channel_breakdown(weeks, target_week_start):
    """Return channel → count dict for a specific week."""
    counts = defaultdict(int)
    for week in weeks:
        if week["week_start"] == target_week_start:
            for lead in week.get("real_leads", []):
                counts[lead.get("channel", "other")] += 1
            break
    return counts


# ── Benchmark bar chart ────────────────────────────────────────────────────────
def draw_benchmark_bar(metric_name, your_value, benchmark_value, target_value,
                       fmt_type, good_direction, width=460, height=50):
    d = Drawing(width, height)
    bar_x = 120; bar_w = width - bar_x - 10; bar_y = 18; bar_h = 18

    d.add(String(2, bar_y + 4, metric_name,
                 fontName="Lato-Bold", fontSize=9, fillColor=SRED_DARK_BLUE))
    d.add(Rect(bar_x, bar_y, bar_w, bar_h, fillColor=BENCHMARK_BG, strokeColor=None))

    if good_direction == "lower":
        max_val  = max(your_value, benchmark_value, target_value or 0) * 1.3 or 1
        your_w   = (your_value / max_val) * bar_w
        bench_x  = bar_x + (benchmark_value / max_val) * bar_w
        target_x = bar_x + ((target_value or 0) / max_val) * bar_w
        color = SRED_EMERALD if your_value <= (target_value or benchmark_value) \
                else SRED_AMBER if your_value <= benchmark_value else BENCHMARK_RED
    else:
        max_val  = max(your_value, benchmark_value, target_value or 0) * 1.2 or 1
        your_w   = (your_value / max_val) * bar_w
        bench_x  = bar_x + (benchmark_value / max_val) * bar_w
        target_x = bar_x + ((target_value or 0) / max_val) * bar_w
        color = SRED_EMERALD if your_value >= (target_value or benchmark_value) \
                else SRED_AMBER if your_value >= benchmark_value else BENCHMARK_RED

    d.add(Rect(bar_x, bar_y, min(your_w, bar_w), bar_h, fillColor=color, strokeColor=None))
    d.add(String(bar_x + min(your_w, bar_w) + 4, bar_y + 4,
                 fmt_metric(your_value, fmt_type),
                 fontName="Lato-Bold", fontSize=9, fillColor=SRED_DARK_BLUE))
    d.add(Line(bench_x, bar_y - 2, bench_x, bar_y + bar_h + 2,
               strokeColor=SRED_DARK_BLUE, strokeWidth=2, strokeDashArray=[3, 2]))
    d.add(String(bench_x - 2, bar_y + bar_h + 4,
                 f"B2B: {fmt_metric(benchmark_value, fmt_type)}",
                 fontName="Lato", fontSize=7, fillColor=SRED_GRAY))
    if target_value and target_value != benchmark_value:
        d.add(Line(target_x, bar_y - 2, target_x, bar_y + bar_h + 2,
                   strokeColor=SRED_LIGHT_BLUE, strokeWidth=2))
        d.add(String(target_x - 2, bar_y - 10,
                     f"Target: {fmt_metric(target_value, fmt_type)}",
                     fontName="Lato", fontSize=7, fillColor=SRED_LIGHT_BLUE))
    return d


# ── Lead Pipeline page ─────────────────────────────────────────────────────────
def build_lead_pipeline_page(doc, leads_data, this_week_start):
    doc.page_break()
    doc.section_header("LEAD PIPELINE")
    doc.body(
        "All form submissions verified against HubSpot and Gmail — spam filtered out. "
        "Paid = Google Ads attribution. Organic/Content = unpaid search. "
        "Direct/Referral = direct URL, email without UTM, or referral link."
    )
    doc.spacer(0.1)

    weeks = leads_data.get("weeks", [])
    if not weeks:
        doc.body("No lead pipeline data available yet.")
        return

    # Find this week and last week
    this_w = next((w for w in weeks if w["week_start"] == this_week_start), None)
    sorted_weeks = sorted(weeks, key=lambda w: w["week_start"])
    idx = next((i for i, w in enumerate(sorted_weeks) if w["week_start"] == this_week_start), None)
    last_w = sorted_weeks[idx - 1] if (idx is not None and idx > 0) else None

    # ── Section 1: This Week KPI cards ───────────────────────────────────────
    if this_w:
        s = this_w.get("summary", {})
        paid       = s.get("paid_leads", 0)
        organic    = s.get("organic_leads", 0)
        direct     = s.get("direct_leads", 0)
        email_out  = s.get("email_leads", 0)
        other      = s.get("other_leads", 0)
        non_paid   = organic + direct + email_out + other
        doc.kpi_row([
            ("Submissions", str(s.get("total_submissions", 0))),
            ("Real Leads", str(s.get("real_leads", 0))),
            ("Paid (Google)", str(paid)),
            ("Organic / Other", str(non_paid)),
        ])
        if s.get("spam_count", 0):
            doc.spacer(0.05)
            doc.caution(
                f"{s['spam_count']} spam submission(s) filtered this week — "
                "someone used the contact form to pitch a service."
            )
    doc.spacer(0.12)

    # ── Section 2: Week over Week ─────────────────────────────────────────────
    doc.sub_header("Week over Week")

    def _w_val(w, key, default=0):
        return w.get("summary", {}).get(key, default) if w else default

    wow_metrics = [
        ("Total Submissions",    "total_submissions",  "higher"),
        ("Real Leads",           "real_leads",         "higher"),
        ("Paid Leads (Google)",  "paid_leads",         "higher"),
        ("Organic / Content",    "organic_leads",      "higher"),
        ("Direct / Referral",    "direct_leads",       "higher"),
        ("Email Outreach",       "email_leads",        "higher"),
        ("Spam Submissions",     "spam_count",         "lower"),
    ]
    wow_rows = [["Metric", "This Week", "Last Week", "Change"]]
    for label, key, good in wow_metrics:
        tw_v = _w_val(this_w, key)
        pw_v = _w_val(last_w, key) if last_w else None
        pw_s = str(pw_v) if pw_v is not None else "—"
        wow_rows.append([label, str(tw_v), pw_s,
                         colored_delta(tw_v, pw_v, good) if pw_v is not None else _delta_para("—", DELTA_GRAY)])
    tbl(doc, wow_rows, col_widths=[2.2, 1.2, 1.2, 1.2])
    doc.spacer(0.15)

    # ── Section 3: Source breakdown (this week) ───────────────────────────────
    doc.sub_header("Lead Sources — This Week")
    if this_w:
        ch = channel_breakdown(weeks, this_week_start)
        real_total = this_w.get("summary", {}).get("real_leads", 0) or 1
        src_rows = [["Channel", "Leads", "% of Real Leads", "Example Leads"]]
        for channel_key, display in CHANNEL_DISPLAY.items():
            count = ch.get(channel_key, 0)
            if count == 0:
                continue
            # Pull names for this channel
            names = [
                f"{l['name']} ({l['company'] or l['email'][:20]})"
                for l in this_w.get("real_leads", [])
                if l.get("channel") == channel_key
            ][:2]
            example = ", ".join(names) if names else "—"
            src_rows.append([display, str(count),
                             pct(count / real_total), example[:45]])
        tbl(doc, src_rows, col_widths=[1.6, 0.7, 1.3, 2.7])
        doc.spacer(0.08)
        doc.body(
            "Paid Ads = Google Ads click confirmed by HubSpot PAID_SEARCH attribution. "
            "Organic/Content = found SRED.ca via unpaid search (SEO/content working). "
            "Direct/Referral = typed URL, email without UTM, or referred by someone."
        )
    doc.spacer(0.15)

    # ── Section 4: Quarterly Summary ─────────────────────────────────────────
    doc.sub_header("Quarterly Summary (FY2026)")
    quarters_data = aggregate_pipeline(weeks)

    # Determine current FY from this_week_start
    cur_fy, _, _ = fiscal_quarter(this_week_start)
    # Build columns for all 4 quarters of current FY
    q_keys   = [(cur_fy, 1), (cur_fy, 2), (cur_fy, 3), (cur_fy, 4)]
    q_labels = ["Q1 May–Jul", "Q2 Aug–Oct", "Q3 Nov–Jan", "Q4 Feb–Apr"]

    def _qv(qkey, field):
        return quarters_data.get(qkey, {}).get(field, 0)

    def _q_or_dash(qkey, field):
        v = _qv(qkey, field)
        # Show "—" for quarters with no data at all
        if _qv(qkey, "submissions") == 0 and field != "submissions":
            return "—"
        return str(v) if v > 0 else ("—" if _qv(qkey, "submissions") == 0 else "0")

    ytd_labels = {
        "submissions":  sum(_qv(k, "submissions")  for k in q_keys),
        "real_leads":   sum(_qv(k, "real_leads")   for k in q_keys),
        "paid":         sum(_qv(k, "paid")          for k in q_keys),
        "organic":      sum(_qv(k, "organic")       for k in q_keys),
        "direct":       sum(_qv(k, "direct")        for k in q_keys),
        "spam":         sum(_qv(k, "spam")          for k in q_keys),
        "opportunities":sum(_qv(k, "opportunities") for k in q_keys),
        "clients":      sum(_qv(k, "clients")       for k in q_keys),
    }

    q_rows = [["Metric"] + q_labels + ["FY Total"]]
    q_metrics = [
        ("Submissions",    "submissions"),
        ("Real Leads",     "real_leads"),
        ("Paid (Google)",  "paid"),
        ("Organic/Content","organic"),
        ("Direct/Referral","direct"),
        ("Spam",           "spam"),
        ("Clients Won",    "clients"),
    ]
    for label, field in q_metrics:
        row = [label]
        for qk in q_keys:
            row.append(_q_or_dash(qk, field))
        row.append(str(ytd_labels[field]) if ytd_labels[field] > 0 else "0")
        q_rows.append(row)

    # Lead-to-client rate row
    rate_row = ["Lead→Client Rate"]
    for qk in q_keys:
        rl = _qv(qk, "real_leads")
        cl = _qv(qk, "clients")
        rate_row.append(pct(cl / rl) if rl > 0 else "—")
    rl_ytd = ytd_labels["real_leads"]
    cl_ytd = ytd_labels["clients"]
    rate_row.append(pct(cl_ytd / rl_ytd) if rl_ytd > 0 else "—")
    q_rows.append(rate_row)

    tbl(doc, q_rows, col_widths=[1.4, 0.9, 0.9, 0.9, 0.9, 0.9])

    doc.spacer(0.05)
    doc.small(
        "Inbound digital leads only (Paid Search, Organic Search, Direct/Referral). "
        "Existing clients imported from prior relationships (HubSpot OFFLINE source) are excluded. "
        "Email sequence attribution: 0 inbound leads traced to an email campaign this FY — "
        "outbound email is driving meetings but not yet driving form submissions."
    )
    doc.spacer(0.15)

    # ── Section 5: Conversion Funnel (YTD) ───────────────────────────────────
    doc.sub_header("Conversion Funnel — YTD")

    total_submissions = ytd_labels["submissions"]
    total_real        = ytd_labels["real_leads"]
    total_opps        = ytd_labels["opportunities"]
    total_clients     = ytd_labels["clients"]

    funnel_rows = [
        ["Stage", "Count", "Rate from Prior Stage", "Interpretation"],
        ["Form Submissions", str(total_submissions),
         "—",
         "Everyone who filled out the contact form"],
        ["Real Leads (non-spam)", str(total_real),
         pct(total_real / total_submissions) if total_submissions else "—",
         "Genuine inquiries after removing spam"],
        ["Qualified (Opp/SQL)", str(total_opps),
         pct(total_opps / total_real) if total_real else "—",
         "Moved to Opportunity or SQL in HubSpot"],
        ["Clients Won", str(total_clients),
         pct(total_clients / total_opps) if total_opps else "—",
         "Signed and paying (inbound digital only)"],
    ]
    tbl(doc, funnel_rows, col_widths=[1.6, 0.7, 1.5, 2.5])

    doc.spacer(0.08)
    if total_clients > 0:
        still_open = total_opps - total_clients
        doc.body(
            f"{still_open} qualified leads are still open in the pipeline — "
            f"close rate will grow as these convert. "
            f"Current close rate ({pct(total_clients / total_opps if total_opps else 0)}) "
            "is a floor, not a ceiling."
        )


# ── Annual Performance page ────────────────────────────────────────────────────
def build_annual_performance_page(doc, annual_data):
    doc.page_break()
    doc.section_header("ANNUAL PERFORMANCE — FY2026")

    meta_a = annual_data.get("meta", {})
    totals = annual_data.get("fy_totals", {})
    monthly = annual_data.get("monthly_totals", [])

    doc.body(
        f"Full fiscal year summary: {meta_a.get('fy_label', 'FY2026')}. "
        "Note: conversions prior to April 16, 2026 include au_visited_2_pages "
        "(page-visit events counted as conversions). Spend figures are accurate; "
        "CPA reflects the inflated baseline for those months."
    )
    doc.spacer(0.12)

    # ── FY Totals KPI cards ────────────────────────────────────────────────────
    doc.kpi_row([
        ("Total Spend",   cad(totals.get("spend", 0))),
        ("Total Clicks",  f"{totals.get('clicks', 0):,}"),
        ("Avg CTR",       pct(totals.get("ctr", 0))),
        ("Avg CPA",       cad(totals.get("cpa", 0))),
    ])
    doc.spacer(0.08)
    doc.kpi_row([
        ("Impressions",   f"{totals.get('impressions', 0):,}"),
        ("Avg CPC",       cad(totals.get("avg_cpc", 0))),
        ("Conversions",   f"{totals.get('conversions', 0):.0f}"),
        ("Months Active", str(len(monthly))),
    ])
    doc.spacer(0.18)

    # ── Monthly performance table ─────────────────────────────────────────────
    doc.sub_header("Monthly Performance Breakdown")

    MONTH_NAMES = {
        "01": "Jan", "02": "Feb", "03": "Mar", "04": "Apr",
        "05": "May", "06": "Jun", "07": "Jul", "08": "Aug",
        "09": "Sep", "10": "Oct", "11": "Nov", "12": "Dec",
    }

    mo_rows = [["Month", "Spend", "Clicks", "Impr.", "CTR", "Avg CPC", "CPA"]]
    for m in monthly:
        yr, mo_num = m["month"].split("-")
        mo_label = f"{MONTH_NAMES[mo_num]} {yr}"
        mo_rows.append([
            mo_label,
            cad(m["spend"]),
            f"{m['clicks']:,}",
            f"{m['impressions']:,}",
            pct(m["ctr"]),
            cad(m["avg_cpc"]),
            cad(m["cpa"]),
        ])

    # FY Total row
    mo_rows.append([
        "FY2026 Total",
        cad(totals.get("spend", 0)),
        f"{totals.get('clicks', 0):,}",
        f"{totals.get('impressions', 0):,}",
        pct(totals.get("ctr", 0)),
        cad(totals.get("avg_cpc", 0)),
        cad(totals.get("cpa", 0)),
    ])

    tbl(doc, mo_rows, col_widths=[1.0, 1.0, 0.7, 0.7, 0.7, 0.9, 0.9])
    doc.spacer(0.08)

    # Find best and worst months
    if len(monthly) >= 2:
        best_spend  = max(monthly, key=lambda m: m["spend"])
        worst_cpa   = max(monthly, key=lambda m: m["cpa"])
        best_ctr    = max(monthly, key=lambda m: m["ctr"])
        yr_b, mo_b  = best_spend["month"].split("-")
        yr_c, mo_c  = worst_cpa["month"].split("-")
        yr_t, mo_t  = best_ctr["month"].split("-")
        doc.small(
            f"Peak spend: {MONTH_NAMES[mo_b]} {yr_b} ({cad(best_spend['spend'])}). "
            f"Highest CPA: {MONTH_NAMES[mo_c]} {yr_c} ({cad(worst_cpa['cpa'])}). "
            f"Best CTR: {MONTH_NAMES[mo_t]} {yr_t} ({pct(best_ctr['ctr'])})."
        )
    doc.spacer(0.18)

    # ── Campaign annual breakdown ──────────────────────────────────────────────
    doc.sub_header("Campaign Breakdown — FY2026 Totals")
    by_camp = annual_data.get("by_campaign", [])
    if by_camp:
        camp_rows = [["Campaign", "Spend", "Clicks", "Conversions", "Avg CTR", "Avg CPA"]]
        for camp in by_camp:
            months_data = camp.get("months", {}).values()
            c_spend = round(sum(m["spend"] for m in months_data), 2)
            months_data = camp.get("months", {}).values()
            c_clicks = sum(m["clicks"] for m in months_data)
            months_data = camp.get("months", {}).values()
            c_conv  = round(sum(m["conversions"] for m in months_data), 1)
            months_data = camp.get("months", {}).values()
            c_impr  = sum(m["impressions"] for m in months_data)
            c_ctr   = round(c_clicks / c_impr, 4) if c_impr else 0
            c_cpa   = round(c_spend / c_conv, 2) if c_conv else 0
            camp_rows.append([
                camp["name"][:28],
                cad(c_spend),
                f"{c_clicks:,}",
                f"{c_conv:.0f}",
                pct(c_ctr),
                cad(c_cpa),
            ])
        tbl(doc, camp_rows, col_widths=[1.8, 1.0, 0.8, 1.0, 0.8, 0.8])

    doc.spacer(0.1)
    doc.body(
        "Competitor campaign (targeting Infinity SRED) delivers consistently lower CPA "
        "but runs on only $5/day. Bloom RSA 1 drives the majority of volume."
    )


# ── Main report builder ────────────────────────────────────────────────────────
def build_report(data, prior_data, output_path, leads_data=None, annual_data=None):
    meta  = data["meta"]
    tw    = data["this_week"]
    pw    = data.get("prior_week", prior_data.get("this_week", {})) if prior_data else data["prior_week"]
    tw_t  = tw["totals"]
    pw_t  = pw.get("totals", {})

    doc = SREDDoc("Google Ads Weekly Report", output_path)

    # ── Cover ──────────────────────────────────────────────────────────────────
    doc.cover_page(
        "GOOGLE ADS WEEKLY REPORT",
        f"Week of {meta['report_week_start']} to {meta['report_week_end']}",
        "SRED.ca  -  Bloom Technical Advisors",
    )

    # ================================================================
    # PAGE 2: PERFORMANCE vs BENCHMARKS
    # ================================================================
    doc.section_header("PERFORMANCE vs INDUSTRY BENCHMARKS")
    doc.body("How SRED.ca compares to B2B Professional Services averages. "
             "Benchmarks sourced from WordStream/LOCALiQ 2025 (16,446 campaigns).")
    doc.spacer(0.1)

    legend = Drawing(460, 30)
    legend.add(Rect(10, 15, 20, 10, fillColor=SRED_EMERALD, strokeColor=None))
    legend.add(String(34, 16, "Exceeds Target", fontName="Lato", fontSize=8, fillColor=SRED_GRAY))
    legend.add(Rect(130, 15, 20, 10, fillColor=SRED_AMBER, strokeColor=None))
    legend.add(String(154, 16, "Above Industry Avg", fontName="Lato", fontSize=8, fillColor=SRED_GRAY))
    legend.add(Rect(270, 15, 20, 10, fillColor=BENCHMARK_RED, strokeColor=None))
    legend.add(String(294, 16, "Below Industry Avg", fontName="Lato", fontSize=8, fillColor=SRED_GRAY))
    legend.add(Line(10, 5, 30, 5, strokeColor=SRED_DARK_BLUE, strokeWidth=2, strokeDashArray=[3, 2]))
    legend.add(String(34, 2, "Industry Average", fontName="Lato", fontSize=8, fillColor=SRED_GRAY))
    legend.add(Line(130, 5, 150, 5, strokeColor=SRED_LIGHT_BLUE, strokeWidth=2))
    legend.add(String(154, 2, "SRED.ca Target", fontName="Lato", fontSize=8, fillColor=SRED_GRAY))
    doc.raw(legend)
    doc.spacer(0.1)

    conv_rate  = tw_t["conversions"] / tw_t["clicks"] if tw_t["clicks"] else 0
    imp_share  = tw["campaigns"][0].get("impression_share", 0) if tw["campaigns"] else 0

    benchmarks_to_draw = [
        ("Click-Through Rate (CTR)",  tw_t.get("ctr", 0),      BENCHMARKS["ctr"]["industry"],             TARGETS["ctr"]["value"],             "pct", "higher"),
        ("Cost Per Click (CPC)",      tw_t.get("avg_cpc", 0),  BENCHMARKS["avg_cpc"]["industry"],         TARGETS["avg_cpc"]["value"],         "cad", "lower"),
        ("Cost Per Lead (CPA)",       tw_t.get("cpa", 0),      BENCHMARKS["cpa"]["industry"],             TARGETS["cpa"]["value"],             "cad", "lower"),
        ("Conversion Rate",           conv_rate,               BENCHMARKS["conversion_rate"]["industry"], None,                                "pct", "higher"),
        ("Impression Share",          imp_share,               BENCHMARKS["impression_share"]["industry"],TARGETS["impression_share"]["value"], "pct", "higher"),
    ]
    for name, yours, bench, target, fmt, direction in benchmarks_to_draw:
        chart = draw_benchmark_bar(name, yours, bench, target, fmt, direction)
        doc.raw(chart)
        doc.spacer(0.05)

    doc.spacer(0.15)
    doc.sub_header("What These Metrics Mean")
    doc.body("CTR (Click-Through Rate): The percentage of people who see your ad and click it. "
             "Higher is better — it means your ad copy resonates with searchers. B2B average is 5.65%. SRED.ca targets 8%+.")
    doc.spacer(0.08)
    doc.body("CPC (Cost Per Click): What you pay each time someone clicks your ad. "
             "Lower is better. Influenced by your Quality Score and competition. B2B average is $7.60 CAD.")
    doc.spacer(0.08)
    doc.body("CPA (Cost Per Lead): What you pay for each conversion. "
             "Lower is better. B2B average is $141 CAD. SRED.ca targets under $45 CAD. "
             "NOTE: This number is only meaningful if conversions represent real leads — see Conversion Quality section.")
    doc.spacer(0.08)
    doc.body("Conversion Rate: The percentage of clicks that turn into a conversion. "
             "Higher is better. Depends on landing page quality and keyword intent. B2B average is 5.14%.")
    doc.spacer(0.08)
    doc.body("Impression Share: The percentage of times your ad showed vs. how many times it could have. "
             "50% means you're missing half of all eligible searches. Limited by budget and Quality Score.")
    doc.spacer(0.15)

    doc.sub_header("Benchmark Comparison")
    bench_rows = [
        ["Metric", "SRED.ca", "B2B Avg", "Target", "Status"],
        ["CTR", pct(tw_t.get("ctr", 0)), "5.65%", "8.0%",
         "Exceeds" if tw_t.get("ctr", 0) >= 0.08 else "Above Avg" if tw_t.get("ctr", 0) >= 0.0565 else "Below Avg"],
        ["CPC", cad(tw_t.get("avg_cpc", 0)), "$7.60", "$10.00",
         "On Target" if tw_t.get("avg_cpc", 0) <= 10 else "Above Target"],
        ["CPA", cad(tw_t.get("cpa", 0)), "$141", "$45",
         "On Target" if tw_t.get("cpa", 0) <= 45 else "Above Target" if tw_t.get("cpa", 0) <= 141 else "Expensive"],
        ["Conv Rate", pct(conv_rate), "5.14%", "—",
         "Strong" if conv_rate >= 0.0514 else "Below Avg"],
        ["Imp Share", pct(imp_share), "50%", "50%",
         "On Target" if imp_share >= 0.50 else "Below Target"],
    ]
    tbl(doc, bench_rows, col_widths=[1.2, 1.3, 1.2, 1.3, 1.0])

    conv_actions = data.get("conversion_actions", [])
    two_page = next((a for a in conv_actions if "2_pages" in a.get("name", "")), None)
    if two_page and tw_t.get("conversions", 0) > 0:
        two_page_pct = two_page["conversions"] / tw_t["conversions"]
        if two_page_pct > 0.3:
            true_conv = tw_t["conversions"] - two_page["conversions"]
            true_cpa  = tw_t["spend"] / true_conv if true_conv > 0 else 0
            doc.spacer(0.1)
            doc.caution(
                f"Conversion quality alert: {two_page_pct:.0%} of conversions "
                f"({two_page['conversions']:.0f}/{tw_t['conversions']:.0f}) are '2+ page visits' only. "
                f"True leads (form/call/email): {true_conv:.0f}. "
                f"True CPA: {cad(true_cpa) if true_conv > 0 else 'No leads this week'}."
            )

    # ================================================================
    # PAGE 3: WEEK-OVER-WEEK SUMMARY  (with colour-coded change column)
    # ================================================================
    doc.page_break()
    doc.section_header("WEEK-OVER-WEEK SUMMARY")

    doc.kpi_row([
        ("Spend",       cad(tw_t.get("spend", 0))),
        ("Clicks",      str(tw_t.get("clicks", 0))),
        ("Conversions", f"{tw_t.get('conversions', 0):.1f}"),
        ("CPA",         cad(tw_t.get("cpa", 0))),
    ])
    doc.spacer(0.08)
    doc.kpi_row([
        ("CTR",       pct(tw_t.get("ctr", 0))),
        ("Avg CPC",   cad(tw_t.get("avg_cpc", 0))),
        ("Imp Share", pct(imp_share)),
        ("WoW Spend", delta_str(tw_t.get("spend", 0), pw_t.get("spend", 0))),
    ])
    doc.spacer(0.12)

    doc.body("Change column: green = improving, red = worsening, direction based on what's good for the account.")
    doc.spacer(0.08)

    wow_rows = [["Metric", "This Week", "Prior Week", "Change"]]
    wow_metrics_list = [
        ("Spend",       "spend",       cad,                             "lower"),
        ("Clicks",      "clicks",      str,                             "higher"),
        ("Impressions", "impressions", lambda v: f"{int(v):,}",         "higher"),
        ("Conversions", "conversions", lambda v: f"{v:.1f}",            "higher"),
        ("CTR",         "ctr",         pct,                             "higher"),
        ("Avg CPC",     "avg_cpc",     cad,                             "lower"),
        ("CPA",         "cpa",         cad,                             "lower"),
    ]
    for label, key, fmt, good in wow_metrics_list:
        tw_v = tw_t.get(key, 0)
        pw_v = pw_t.get(key, 0)
        wow_rows.append([label, fmt(tw_v), fmt(pw_v), colored_delta(tw_v, pw_v, good)])
    tbl(doc, wow_rows, col_widths=[1.5, 1.7, 1.7, 1.4])

    # ================================================================
    # PAGE 4: CAMPAIGN PERFORMANCE  (with colour-coded change column)
    # ================================================================
    doc.page_break()
    doc.section_header("CAMPAIGN PERFORMANCE")

    camp_metric_dirs = {
        "spend": "lower", "clicks": "higher", "impressions": "higher",
        "conversions": "higher", "ctr": "higher", "cpa": "lower",
        "impression_share": "higher",
    }

    for camp in tw["campaigns"]:
        prior_camp = next((c for c in pw.get("campaigns", []) if c["id"] == camp["id"]), {})
        doc.sub_header(camp["name"])

        camp_rows = [["Metric", "This Week", "Prior Week", "Change"]]
        for label, key, fmt in [
            ("Spend",       "spend",       cad),
            ("Clicks",      "clicks",      str),
            ("Impressions", "impressions", lambda v: f"{int(v):,}"),
            ("Conversions", "conversions", lambda v: f"{v:.1f}"),
            ("CTR",         "ctr",         pct),
            ("CPA",         "cpa",         cad),
        ]:
            tw_v  = camp.get(key, 0)
            pw_v  = prior_camp.get(key, 0)
            good  = camp_metric_dirs.get(key, "higher")
            camp_rows.append([label, fmt(tw_v), fmt(pw_v), colored_delta(tw_v, pw_v, good)])

        if camp.get("impression_share"):
            tw_is = camp.get("impression_share", 0)
            pw_is = prior_camp.get("impression_share", 0)
            camp_rows.append(["Imp Share", pct(tw_is), pct(pw_is),
                              colored_delta(tw_is, pw_is, "higher")])
        tbl(doc, camp_rows, col_widths=[1.5, 1.7, 1.7, 1.4])

        budget = camp.get("daily_budget_cad", 0)
        if budget > 0:
            pacing = camp["spend"] / (budget * 7) if budget > 0 else 0
            if pacing > 1.1:
                doc.caution(f"Overpacing: {cad(camp['spend'])} against {cad(budget * 7)} weekly budget ({pacing:.0%}).")
            elif pacing < 0.7:
                doc.caution(f"Underpacing: only {pacing:.0%} of weekly budget used. "
                            f"Budget lost impression share: {pct(camp.get('budget_lost_is', 0))}.")
        doc.spacer(0.15)

    # ================================================================
    # PAGE 5: KEYWORDS + SEARCH TERMS
    # ================================================================
    doc.page_break()
    doc.section_header("KEYWORD AND SEARCH TERM ANALYSIS")

    doc.sub_header("Top Keywords by Spend")
    kw_rows = [["Keyword", "QS", "Spend", "Clicks", "Conv", "CPA"]]
    for kw in data["keywords"][:10]:
        qs = str(kw["quality_score"]) if kw["quality_score"] else "—"
        kw_rows.append([kw["keyword"][:30], qs, cad(kw["spend"]),
                        str(kw["clicks"]), f"{kw['conversions']:.1f}", cad(kw["cpa"])])
    tbl(doc, kw_rows, col_widths=[2.0, 0.4, 1.0, 0.7, 0.7, 1.0])

    low_qs = [kw for kw in data["keywords"] if kw["quality_score"] and kw["quality_score"] < 5 and kw["spend"] > 5]
    if low_qs:
        doc.spacer(0.1)
        doc.caution(f"Quality Score alert: {len(low_qs)} keyword(s) with QS below 5 (industry avg 5.5, target 7+):")
        for kw in low_qs[:5]:
            doc.body(f"  - \"{kw['keyword']}\" (QS: {kw['quality_score']}, Spend: {cad(kw['spend'])})")

    doc.spacer(0.15)
    doc.sub_header("Wasted Spend (Zero-Conversion Search Terms)")
    waste = [t for t in data["search_terms"] if t["conversions"] == 0 and t["spend"] > 5]
    if waste:
        w_rows = [["Search Term", "Spend", "Clicks", "Campaign"]]
        total_waste = 0
        for t in sorted(waste, key=lambda x: -x["spend"])[:8]:
            w_rows.append([t["term"][:35], cad(t["spend"]), str(t["clicks"]), t["campaign"][:18]])
            total_waste += t["spend"]
        tbl(doc, w_rows, col_widths=[2.5, 1.0, 0.7, 1.5])
        doc.caution(f"Total waste: {cad(total_waste)} on {len(waste)} terms with zero conversions.")
    else:
        doc.win("No significant wasted spend on zero-conversion search terms this week.")

    # ================================================================
    # PAGE 6: AD COPY
    # ================================================================
    doc.page_break()
    doc.section_header("AD COPY PERFORMANCE")

    ad_rows = [["Ad (Headlines)", "Impr", "Clicks", "CTR", "Conv", "CPA"]]
    for ad in data["ads"][:8]:
        if not ad.get("headlines"):
            continue
        headline_preview = " | ".join(ad["headlines"][:3])
        if len(headline_preview) > 50:
            headline_preview = headline_preview[:47] + "..."
        ad_rows.append([headline_preview, f"{ad['impressions']:,}", str(ad["clicks"]),
                        pct(ad["ctr"]), f"{ad['conversions']:.1f}", cad(ad["cpa"])])
    if len(ad_rows) > 1:
        tbl(doc, ad_rows, col_widths=[2.5, 0.7, 0.7, 0.7, 0.7, 0.9])

    # ================================================================
    # PAGE 7: TIME AND DEVICE
    # ================================================================
    doc.page_break()
    doc.section_header("TIME AND DEVICE ANALYSIS")

    doc.sub_header("Top Hours by Spend (PT)")
    hourly = data.get("hourly_performance", [])
    if hourly:
        relevant = sorted([h for h in hourly if h["clicks"] > 0], key=lambda x: -x["spend"])[:10]
        h_rows = [["Hour", "Spend", "Clicks", "Conv", "CPA"]]
        for h in relevant:
            h_rows.append([f"{h['hour']:02d}:00", cad(h["spend"]), str(h["clicks"]),
                           f"{h['conversions']:.1f}", cad(h["cpa"])])
        tbl(doc, h_rows, col_widths=[1.0, 1.3, 1.0, 1.0, 1.3])
        overnight = [h for h in hourly if h["hour"] < 6 or h["hour"] >= 23]
        night_spend = sum(h["spend"] for h in overnight)
        night_conv  = sum(h["conversions"] for h in overnight)
        if night_spend > 5 and night_conv == 0:
            doc.caution(f"Overnight (11pm–6am): {cad(night_spend)} spent, 0 conversions.")

    doc.spacer(0.15)
    doc.sub_header("Day of Week")
    daily = data.get("daily_performance", [])
    if daily:
        d_rows = [["Day", "Spend", "Clicks", "Conv", "CPA"]]
        for d in daily:
            d_rows.append([DAY_LABELS.get(d["day"], d["day"]), cad(d["spend"]),
                           str(d["clicks"]), f"{d['conversions']:.1f}", cad(d["cpa"])])
        tbl(doc, d_rows, col_widths=[1.0, 1.3, 1.0, 1.0, 1.3])

    doc.spacer(0.15)
    doc.sub_header("Device")
    devices = data.get("device_performance", [])
    if devices:
        dev_rows = [["Device", "Spend", "Clicks", "Conv", "CPA"]]
        for d in devices:
            dev_rows.append([DEVICE_LABELS.get(d["device"], d["device"]), cad(d["spend"]),
                             str(d["clicks"]), f"{d['conversions']:.1f}", cad(d["cpa"])])
        tbl(doc, dev_rows, col_widths=[1.2, 1.3, 1.0, 1.0, 1.3])

    # ================================================================
    # PAGE 8: CONVERSION QUALITY
    # ================================================================
    doc.page_break()
    doc.section_header("CONVERSION QUALITY AUDIT")

    conv_actions = data.get("conversion_actions", [])
    if conv_actions:
        total_conv = sum(a["conversions"] for a in conv_actions)
        ca_rows = [["Conversion Action", "Count", "% of Total", "Quality Tier"]]
        for a in conv_actions:
            pct_total = a["conversions"] / total_conv if total_conv > 0 else 0
            tier = ("LOW — page engagement only" if "2_pages" in a["name"]
                    else "HIGH — form submission (real lead)" if "thankyou" in a["name"]
                    else "MEDIUM — intent signal")
            ca_rows.append([a["name"][:35], f"{a['conversions']:.1f}", pct(pct_total), tier])
        tbl(doc, ca_rows, col_widths=[2.5, 0.8, 0.8, 2.1])

        two_page = next((a for a in conv_actions if "2_pages" in a.get("name", "")), None)
        if two_page:
            doc.spacer(0.15)
            doc.sub_header("True CPA Analysis")
            true_conv = total_conv - two_page["conversions"]
            true_cpa  = tw_t["spend"] / true_conv if true_conv > 0 else 0
            doc.body(f"Reported conversions:    {total_conv:.1f}  (Reported CPA: {cad(tw_t.get('cpa', 0))})")
            doc.body(f"Minus '2+ page visits':  -{two_page['conversions']:.1f}")
            doc.body(f"True lead conversions:   {true_conv:.1f}")
            doc.body(f"True CPA:                {cad(true_cpa) if true_conv > 0 else 'N/A — no leads this week'}")
            if true_conv == 0:
                doc.caution("ZERO real leads this week. All conversions are just 2+ page visits.")
    else:
        doc.body("No conversion action data available.")

    # ================================================================
    # PAGE 9: ANNUAL PERFORMANCE  (only if --annual provided)
    # ================================================================
    if annual_data:
        build_annual_performance_page(doc, annual_data)

    # ================================================================
    # PAGE 10: LEAD PIPELINE  (only if --leads provided)
    # ================================================================
    if leads_data:
        build_lead_pipeline_page(doc, leads_data, meta["report_week_start"])

    # ================================================================
    # PAGE 11: ACTIONS AND RECOMMENDATIONS  (always last)
    # ================================================================
    doc.page_break()
    doc.section_header("ACTIONS AND RECOMMENDATIONS")

    doc.sub_header("Automated Actions This Week")
    neg_added = data.get("negatives_added", [])
    if neg_added:
        for n in neg_added:
            doc.body(f"  - Added negative: \"{n['keyword']}\" [{n['match_type']}] — {n['reason']}")
    else:
        doc.body("No automated actions taken this week.")

    doc.spacer(0.15)
    doc.sub_header("Recommendations (Approval Needed)")
    recs = generate_recommendations(data, pw)
    if recs:
        for i, rec in enumerate(recs, 1):
            doc.body(f"{i}. [{rec['priority']}] {rec['title']}")
            doc.small(f"   {rec['detail']}")
            doc.spacer(0.05)
    else:
        doc.body("No recommendations this week.")

    doc.spacer(0.15)
    doc.sub_header("Strategic Notes")
    for camp in tw["campaigns"]:
        if camp.get("budget_lost_is", 0) > 0.1:
            est_lost = camp["clicks"] * (camp["budget_lost_is"] / max(1 - camp["budget_lost_is"], 0.01))
            doc.body(f"- {camp['name']}: {pct(camp['budget_lost_is'])} impressions lost to budget "
                     f"(~{est_lost:.0f} potential clicks).")
    low_lp = [kw for kw in data["keywords"] if kw.get("landing_page_score") in ["2", "BELOW_AVERAGE"]]
    if low_lp:
        doc.body(f"- Landing page quality 'Below Average' on {len(low_lp)} keywords. "
                 "Dedicated landing pages would improve QS and reduce CPC by ~32%.")

    doc.build()
    print(f"Report saved: {output_path}")


# ── Recommendations engine ─────────────────────────────────────────────────────
def generate_recommendations(data, pw):
    recs  = []
    tw_t  = data["this_week"]["totals"]
    pw_t  = pw.get("totals", {})

    for camp in data["this_week"]["campaigns"]:
        if camp.get("impression_share", 1) < 0.4 and camp.get("cpa", 999) < 50:
            recs.append({
                "priority": "HIGH",
                "title": f"Increase {camp['name']} daily budget",
                "detail": (f"Imp share {pct(camp.get('impression_share', 0))}, "
                           f"CPA {cad(camp.get('cpa', 0))}. "
                           f"Missing {pct(camp.get('budget_lost_is', 0))} to budget. "
                           f"Recommend {cad(camp.get('daily_budget_cad', 0))}/day "
                           f"-> {cad(camp.get('daily_budget_cad', 0) * 1.2)}/day."),
            })

    hourly      = data.get("hourly_performance", [])
    overnight   = [h for h in hourly if h["hour"] < 6 or h["hour"] >= 23]
    night_spend = sum(h["spend"] for h in overnight)
    night_conv  = sum(h["conversions"] for h in overnight)
    if night_spend > 10 and night_conv == 0:
        recs.append({"priority": "MEDIUM", "title": "Add ad schedule — reduce overnight bids",
                     "detail": f"Overnight spent {cad(night_spend)} with 0 conversions. Recommend -80% bid modifier 11pm–6am."})

    existing_kws = {kw["keyword"].lower() for kw in data["keywords"]}
    for t in data["search_terms"]:
        if t["conversions"] >= 2 and t["term"].lower() not in existing_kws:
            recs.append({"priority": "MEDIUM", "title": f"Add keyword: \"{t['term']}\"",
                         "detail": f"{t['conversions']:.0f} conversions, {cad(t['spend'])}. Not in keyword list."})

    if pw_t.get("cpa", 0) > 0 and tw_t.get("cpa", 0) > pw_t["cpa"] * 1.3:
        recs.append({"priority": "HIGH", "title": "CPA increased significantly WoW",
                     "detail": f"CPA: {cad(pw_t['cpa'])} -> {cad(tw_t['cpa'])} ({delta_str(tw_t['cpa'], pw_t['cpa'])}). Review search terms."})

    return sorted(recs, key=lambda r: {"HIGH": 0, "MEDIUM": 1, "LOW": 2}.get(r["priority"], 3))


# ── Entry point ────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data",   required=True,  help="This week's JSON data file")
    parser.add_argument("--prior",                  help="Prior week's JSON data file")
    parser.add_argument("--output", required=True,  help="Output PDF path")
    parser.add_argument("--leads",                  help="Lead pipeline JSON (outputs/leads-pipeline.json)")
    parser.add_argument("--annual",                 help="Annual data JSON (outputs/annual-data-FYXXXX.json)")
    args = parser.parse_args()

    data         = load_data(args.data)
    prior_data   = load_data(args.prior)  if args.prior  else None
    leads_data   = load_data(args.leads)  if args.leads  else None
    annual_data  = load_data(args.annual) if args.annual else None
    build_report(data, prior_data, args.output, leads_data, annual_data)

if __name__ == "__main__":
    main()
