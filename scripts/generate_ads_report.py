#!/usr/bin/env python3
"""
SRED.ca Google Ads — Weekly Report Generator Component (v2)

Reads weekly JSON data and generates a branded PDF report with
industry benchmark comparisons and visual performance graphics.
"""

import json
import sys
import argparse
from pathlib import Path

sys.path.insert(0, "/Users/judebrown/Documents/Claude/sales-coach/.claude/skills/sred-doc-creator/scripts")
from sred_doc import SREDDoc

from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor
from reportlab.graphics.shapes import Drawing, Rect, String, Line
from reportlab.graphics import renderPDF
from reportlab.platypus import Paragraph

SRED_DARK_BLUE = HexColor("#2F2A4F")
SRED_GREEN = HexColor("#B7DB41")
SRED_LIGHT_BLUE = HexColor("#40BAEB")
SRED_EMERALD = HexColor("#35B586")
SRED_GRAY = HexColor("#4A4A4A")
SRED_LIGHT_GRAY = HexColor("#E4E4E4")
SRED_AMBER = HexColor("#E8A838")
BENCHMARK_RED = HexColor("#E05555")
BENCHMARK_BG = HexColor("#F2F2F2")

BENCHMARKS = {
    "ctr": {"industry": 0.0565, "label": "B2B Avg", "format": "pct", "good": "higher"},
    "avg_cpc": {"industry": 7.60, "label": "B2B Avg", "format": "cad", "good": "lower"},
    "cpa": {"industry": 141.00, "label": "B2B Avg", "format": "cad", "good": "lower"},
    "conversion_rate": {"industry": 0.0514, "label": "B2B Avg", "format": "pct", "good": "higher"},
    "quality_score": {"industry": 5.5, "label": "Avg", "target": 7.0, "format": "num", "good": "higher"},
    "impression_share": {"industry": 0.50, "label": "B2B Target", "format": "pct", "good": "higher"},
}

TARGETS = {
    "ctr": {"value": 0.08, "label": "Our Target"},
    "avg_cpc": {"value": 10.00, "label": "Our Target"},
    "cpa": {"value": 45.00, "label": "Our Target"},
    "impression_share": {"value": 0.50, "label": "Our Target"},
    "quality_score": {"value": 7.0, "label": "Our Target"},
}

DEVICE_LABELS = {"2": "Mobile", "3": "Tablet", "4": "Desktop", "5": "Connected TV"}
DAY_LABELS = {"2": "Mon", "3": "Tue", "4": "Wed", "5": "Thu", "6": "Fri", "7": "Sat", "8": "Sun"}

def pct(v): return f"{v:.1%}" if v else "0.0%"
def cad(v): return f"${v:,.2f}" if v else "$0.00"
def fmt_metric(v, fmt_type):
    if fmt_type == "pct": return pct(v)
    if fmt_type == "cad": return cad(v)
    return f"{v:.1f}"

def delta(curr, prev):
    if not prev or prev == 0: return "N/A"
    change = (curr - prev) / prev
    arrow = "+" if change >= 0 else ""
    return f"{arrow}{change:.1%}"

def load_data(path):
    with open(path) as f:
        return json.load(f)

def tbl(doc, all_rows, col_widths=None):
    doc.branded_table(all_rows[0], all_rows[1:], col_widths=col_widths)


def draw_benchmark_bar(metric_name, your_value, benchmark_value, target_value,
                       fmt_type, good_direction, width=460, height=50):
    d = Drawing(width, height)

    bar_x = 120
    bar_w = width - bar_x - 10
    bar_y = 18
    bar_h = 18

    d.add(String(2, bar_y + 4, metric_name, fontName="Lato-Bold", fontSize=9, fillColor=SRED_DARK_BLUE))

    d.add(Rect(bar_x, bar_y, bar_w, bar_h, fillColor=BENCHMARK_BG, strokeColor=None))

    if good_direction == "lower":
        max_val = max(your_value, benchmark_value, target_value or 0) * 1.3
        if max_val == 0: max_val = 1
        your_w = (your_value / max_val) * bar_w
        bench_x = bar_x + (benchmark_value / max_val) * bar_w
        target_x = bar_x + ((target_value or 0) / max_val) * bar_w

        color = SRED_EMERALD if your_value <= (target_value or benchmark_value) else SRED_AMBER if your_value <= benchmark_value else BENCHMARK_RED
    else:
        max_val = max(your_value, benchmark_value, target_value or 0) * 1.2
        if max_val == 0: max_val = 1
        your_w = (your_value / max_val) * bar_w
        bench_x = bar_x + (benchmark_value / max_val) * bar_w
        target_x = bar_x + ((target_value or 0) / max_val) * bar_w

        color = SRED_EMERALD if your_value >= (target_value or benchmark_value) else SRED_AMBER if your_value >= benchmark_value else BENCHMARK_RED

    d.add(Rect(bar_x, bar_y, min(your_w, bar_w), bar_h, fillColor=color, strokeColor=None))
    d.add(String(bar_x + min(your_w, bar_w) + 4, bar_y + 4, fmt_metric(your_value, fmt_type),
                 fontName="Lato-Bold", fontSize=9, fillColor=SRED_DARK_BLUE))

    d.add(Line(bench_x, bar_y - 2, bench_x, bar_y + bar_h + 2,
               strokeColor=SRED_DARK_BLUE, strokeWidth=2, strokeDashArray=[3, 2]))
    d.add(String(bench_x - 2, bar_y + bar_h + 4, f"B2B: {fmt_metric(benchmark_value, fmt_type)}",
                 fontName="Lato", fontSize=7, fillColor=SRED_GRAY))

    if target_value and target_value != benchmark_value:
        d.add(Line(target_x, bar_y - 2, target_x, bar_y + bar_h + 2,
                   strokeColor=SRED_LIGHT_BLUE, strokeWidth=2))
        d.add(String(target_x - 2, bar_y - 10, f"Target: {fmt_metric(target_value, fmt_type)}",
                     fontName="Lato", fontSize=7, fillColor=SRED_LIGHT_BLUE))

    return d


def build_report(data, prior_data, output_path):
    meta = data["meta"]
    tw = data["this_week"]
    pw = data.get("prior_week", prior_data.get("this_week", {})) if prior_data else data["prior_week"]
    tw_t = tw["totals"]
    pw_t = pw.get("totals", {})

    doc = SREDDoc("Google Ads Weekly Report", output_path)

    # -- Cover --
    doc.cover_page(
        "GOOGLE ADS WEEKLY REPORT",
        f"Week of {meta['report_week_start']} to {meta['report_week_end']}",
        "SRED.ca  -  Bloom Technical Advisors",
    )

    # ================================================================
    # PAGE 2: PERFORMANCE vs BENCHMARKS (the key page)
    # ================================================================
    doc.section_header("PERFORMANCE vs INDUSTRY BENCHMARKS")
    doc.body("How SRED.ca compares to B2B Professional Services averages. "
             "Benchmarks sourced from WordStream/LOCALiQ 2025 (16,446 campaigns).")
    doc.spacer(0.1)

    # --- LEGEND ---
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

    conv_rate = tw_t["conversions"] / tw_t["clicks"] if tw_t["clicks"] else 0
    imp_share = tw["campaigns"][0].get("impression_share", 0) if tw["campaigns"] else 0

    benchmarks_to_draw = [
        ("Click-Through Rate (CTR)", tw_t.get("ctr", 0), BENCHMARKS["ctr"]["industry"], TARGETS["ctr"]["value"], "pct", "higher"),
        ("Cost Per Click (CPC)", tw_t.get("avg_cpc", 0), BENCHMARKS["avg_cpc"]["industry"], TARGETS["avg_cpc"]["value"], "cad", "lower"),
        ("Cost Per Lead (CPA)", tw_t.get("cpa", 0), BENCHMARKS["cpa"]["industry"], TARGETS["cpa"]["value"], "cad", "lower"),
        ("Conversion Rate", conv_rate, BENCHMARKS["conversion_rate"]["industry"], None, "pct", "higher"),
        ("Impression Share", imp_share, BENCHMARKS["impression_share"]["industry"], TARGETS["impression_share"]["value"], "pct", "higher"),
    ]

    for name, yours, bench, target, fmt, direction in benchmarks_to_draw:
        chart = draw_benchmark_bar(name, yours, bench, target, fmt, direction)
        doc.raw(chart)
        doc.spacer(0.05)

    doc.spacer(0.15)

    # --- WHAT THESE STATS MEAN ---
    doc.sub_header("What These Metrics Mean")
    doc.body("CTR (Click-Through Rate): The percentage of people who see your ad and click it. "
             "Higher is better - it means your ad copy resonates with searchers. "
             "B2B average is 5.65%. SRED.ca targets 8%+.")
    doc.spacer(0.08)
    doc.body("CPC (Cost Per Click): What you pay each time someone clicks your ad. "
             "Lower is better. Influenced by your Quality Score and competition. "
             "B2B average is $7.60 CAD.")
    doc.spacer(0.08)
    doc.body("CPA (Cost Per Lead): What you pay for each conversion (form fill, call, or email). "
             "Lower is better. B2B average is $141 CAD. SRED.ca targets under $45 CAD. "
             "NOTE: This number is only meaningful if conversions represent real leads - "
             "see Conversion Quality section.")
    doc.spacer(0.08)
    doc.body("Conversion Rate: The percentage of clicks that turn into a conversion. "
             "Higher is better. Depends on landing page quality and keyword intent. "
             "B2B average is 5.14%.")
    doc.spacer(0.08)
    doc.body("Impression Share: The percentage of times your ad showed vs. how many times "
             "it could have shown. Higher means more visibility. "
             "50% means you're missing half of all eligible searches. "
             "Limited by budget and Quality Score.")
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
        ["Conv Rate", pct(conv_rate), "5.14%", "-",
         "Strong" if conv_rate >= 0.0514 else "Below Avg"],
        ["Imp Share", pct(imp_share), "50%", "50%",
         "On Target" if imp_share >= 0.50 else "Below Target"],
    ]
    tbl(doc, bench_rows, col_widths=[1.2, 1.3, 1.2, 1.3, 1.0])

    # Conversion quality warning
    conv_actions = data.get("conversion_actions", [])
    two_page = next((a for a in conv_actions if "2_pages" in a.get("name", "")), None)
    if two_page and tw_t.get("conversions", 0) > 0:
        two_page_pct = two_page["conversions"] / tw_t["conversions"]
        if two_page_pct > 0.3:
            true_conv = tw_t["conversions"] - two_page["conversions"]
            true_cpa = tw_t["spend"] / true_conv if true_conv > 0 else 0
            doc.spacer(0.1)
            doc.caution(
                f"Conversion quality alert: {two_page_pct:.0%} of conversions "
                f"({two_page['conversions']:.0f}/{tw_t['conversions']:.0f}) are '2+ page visits' only. "
                f"True leads (form/call/email): {true_conv:.0f}. "
                f"True CPA: {cad(true_cpa) if true_conv > 0 else 'No leads this week'}."
            )

    # ================================================================
    # PAGE 3: WEEK-OVER-WEEK SUMMARY
    # ================================================================
    doc.page_break()
    doc.section_header("WEEK-OVER-WEEK SUMMARY")

    doc.kpi_row([
        ("Spend", cad(tw_t.get("spend", 0))),
        ("Clicks", str(tw_t.get("clicks", 0))),
        ("Conversions", f"{tw_t.get('conversions', 0):.1f}"),
        ("CPA", cad(tw_t.get("cpa", 0))),
    ])
    doc.spacer(0.08)
    doc.kpi_row([
        ("CTR", pct(tw_t.get("ctr", 0))),
        ("Avg CPC", cad(tw_t.get("avg_cpc", 0))),
        ("Imp Share", pct(imp_share)),
        ("WoW Spend", delta(tw_t.get("spend", 0), pw_t.get("spend", 0))),
    ])
    doc.spacer(0.15)

    wow_rows = [["Metric", "This Week", "Prior Week", "Change"]]
    for label, key, fmt in [
        ("Spend", "spend", cad), ("Clicks", "clicks", str),
        ("Impressions", "impressions", lambda v: f"{v:,}"),
        ("Conversions", "conversions", lambda v: f"{v:.1f}"),
        ("CTR", "ctr", pct), ("Avg CPC", "avg_cpc", cad), ("CPA", "cpa", cad),
    ]:
        tw_v = tw_t.get(key, 0)
        pw_v = pw_t.get(key, 0)
        wow_rows.append([label, fmt(tw_v), fmt(pw_v), delta(tw_v, pw_v)])
    tbl(doc, wow_rows, col_widths=[1.5, 1.8, 1.8, 1.2])

    # ================================================================
    # PAGE 4: CAMPAIGN PERFORMANCE
    # ================================================================
    doc.page_break()
    doc.section_header("CAMPAIGN PERFORMANCE")

    for camp in tw["campaigns"]:
        prior_camp = next((c for c in pw.get("campaigns", []) if c["id"] == camp["id"]), {})
        doc.sub_header(camp["name"])

        camp_rows = [["Metric", "This Week", "Prior Week", "Change"]]
        for label, key, fmt in [
            ("Spend", "spend", cad), ("Clicks", "clicks", str),
            ("Impressions", "impressions", lambda v: f"{v:,}"),
            ("Conversions", "conversions", lambda v: f"{v:.1f}"),
            ("CTR", "ctr", pct), ("CPA", "cpa", cad),
        ]:
            tw_v = camp.get(key, 0)
            pw_v = prior_camp.get(key, 0)
            camp_rows.append([label, fmt(tw_v), fmt(pw_v), delta(tw_v, pw_v)])

        if camp.get("impression_share"):
            camp_rows.append(["Imp Share", pct(camp["impression_share"]),
                              pct(prior_camp.get("impression_share", 0)),
                              delta(camp.get("impression_share", 0), prior_camp.get("impression_share", 0))])
        tbl(doc, camp_rows, col_widths=[1.5, 1.8, 1.8, 1.2])

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
        qs = str(kw["quality_score"]) if kw["quality_score"] else "-"
        kw_rows.append([kw["keyword"][:30], qs, cad(kw["spend"]),
                        str(kw["clicks"]), f"{kw['conversions']:.1f}", cad(kw["cpa"])])
    tbl(doc, kw_rows, col_widths=[2.0, 0.4, 1.0, 0.7, 0.7, 1.0])

    low_qs = [kw for kw in data["keywords"] if kw["quality_score"] and kw["quality_score"] < 5 and kw["spend"] > 5]
    if low_qs:
        doc.spacer(0.1)
        doc.caution(f"Quality Score alert: {len(low_qs)} keyword(s) with QS below 5 (industry avg is 5.5, target is 7+):")
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
        night_conv = sum(h["conversions"] for h in overnight)
        if night_spend > 5 and night_conv == 0:
            doc.caution(f"Overnight (11pm-6am): {cad(night_spend)} spent, 0 conversions.")

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
            tier = "LOW (engagement)" if "2_pages" in a["name"] else "HIGH (lead)" if "thankyou" in a["name"] else "MEDIUM (intent)"
            ca_rows.append([a["name"][:35], f"{a['conversions']:.1f}", pct(pct_total), tier])
        tbl(doc, ca_rows, col_widths=[2.5, 0.8, 0.8, 1.5])

        two_page = next((a for a in conv_actions if "2_pages" in a.get("name", "")), None)
        if two_page:
            doc.spacer(0.15)
            doc.sub_header("True CPA Analysis")
            true_conv = total_conv - two_page["conversions"]
            true_cpa = tw_t["spend"] / true_conv if true_conv > 0 else 0
            doc.body(f"Reported conversions: {total_conv:.1f} (Reported CPA: {cad(tw_t.get('cpa', 0))})")
            doc.body(f"Minus '2+ page visits': -{two_page['conversions']:.1f}")
            doc.body(f"True lead conversions: {true_conv:.1f}")
            doc.body(f"True CPA: {cad(true_cpa) if true_conv > 0 else 'N/A (no leads this week)'}")
            if true_conv == 0:
                doc.caution("ZERO real leads this week. All conversions are just 2+ page visits. "
                            "Recommendation: remove 'au_visited_2_pages' from Conversions column in Google Ads.")
    else:
        doc.body("No conversion action data available.")

    # ================================================================
    # PAGE 9: ACTIONS AND RECOMMENDATIONS
    # ================================================================
    doc.page_break()
    doc.section_header("ACTIONS AND RECOMMENDATIONS")

    doc.sub_header("Automated Actions This Week")
    neg_added = data.get("negatives_added", [])
    if neg_added:
        for n in neg_added:
            doc.body(f"  - Added negative: \"{n['keyword']}\" [{n['match_type']}] - {n['reason']}")
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


def generate_recommendations(data, pw):
    recs = []
    tw_t = data["this_week"]["totals"]
    pw_t = pw.get("totals", {})

    for camp in data["this_week"]["campaigns"]:
        if camp.get("impression_share", 1) < 0.4 and camp.get("cpa", 999) < 50:
            recs.append({
                "priority": "HIGH",
                "title": f"Increase {camp['name']} daily budget",
                "detail": f"Imp share {pct(camp.get('impression_share', 0))}, CPA {cad(camp.get('cpa', 0))}. "
                          f"Missing {pct(camp.get('budget_lost_is', 0))} to budget. "
                          f"Recommend {cad(camp.get('daily_budget_cad', 0))}/day -> {cad(camp.get('daily_budget_cad', 0) * 1.2)}/day.",
            })

    hourly = data.get("hourly_performance", [])
    overnight = [h for h in hourly if h["hour"] < 6 or h["hour"] >= 23]
    night_spend = sum(h["spend"] for h in overnight)
    night_conv = sum(h["conversions"] for h in overnight)
    if night_spend > 10 and night_conv == 0:
        recs.append({"priority": "MEDIUM", "title": "Add ad schedule - reduce overnight bids",
                     "detail": f"Overnight spent {cad(night_spend)} with 0 conversions. Recommend -80% bid modifier 11pm-6am."})

    existing_kws = {kw["keyword"].lower() for kw in data["keywords"]}
    for t in data["search_terms"]:
        if t["conversions"] >= 2 and t["term"].lower() not in existing_kws:
            recs.append({"priority": "MEDIUM", "title": f"Add keyword: \"{t['term']}\"",
                         "detail": f"{t['conversions']:.0f} conversions, {cad(t['spend'])}. Not in keyword list."})

    if pw_t.get("cpa", 0) > 0 and tw_t.get("cpa", 0) > pw_t["cpa"] * 1.3:
        recs.append({"priority": "HIGH", "title": "CPA increased significantly WoW",
                     "detail": f"CPA: {cad(pw_t['cpa'])} -> {cad(tw_t['cpa'])} ({delta(tw_t['cpa'], pw_t['cpa'])}). Review search terms."})

    return sorted(recs, key=lambda r: {"HIGH": 0, "MEDIUM": 1, "LOW": 2}.get(r["priority"], 3))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", required=True)
    parser.add_argument("--prior")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    data = load_data(args.data)
    prior_data = load_data(args.prior) if args.prior else None
    build_report(data, prior_data, args.output)

if __name__ == "__main__":
    main()
