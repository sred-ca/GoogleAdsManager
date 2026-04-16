#!/usr/bin/env python3
"""
SRED.ca Google Ads — Contractor Brief Generator

Generates branded 1-2 page PDF briefs for work that can't be done via API
(landing pages, conversion tracking, speed optimization).

Run with: python3 contractor_brief.py --spec <brief_spec_json> --output <pdf_path>
"""

import json
import sys
import argparse
from pathlib import Path

sys.path.insert(0, "/Users/judebrown/Documents/Claude/sales-coach/.claude/skills/sred-doc-creator/scripts")
from sred_doc import SREDDoc

from reportlab.lib.colors import HexColor

SRED_DARK_BLUE = HexColor("#2F2A4F")
SRED_EMERALD = HexColor("#35B586")
SRED_AMBER = HexColor("#E8A838")
BENCHMARK_RED = HexColor("#E05555")

PRIORITY_COLORS = {
    "CRITICAL": BENCHMARK_RED,
    "HIGH": SRED_AMBER,
    "MEDIUM": SRED_EMERALD,
}


def generate_brief(spec, output_path):
    doc = SREDDoc("Contractor Brief", output_path)

    doc.cover_page(
        "CONTRACTOR BRIEF",
        spec.get("title", "Task Brief"),
        f"Priority: {spec.get('priority', 'MEDIUM')} | Suggested deadline: {spec.get('deadline_suggestion', 'TBD')}",
    )

    doc.section_header("WHAT NEEDS TO CHANGE")
    doc.body(spec.get("what_needs_to_change", ""))

    doc.spacer(0.15)
    doc.section_header("WHY THIS MATTERS")
    doc.body(spec.get("why_it_matters", ""))

    doc.spacer(0.15)
    doc.section_header("SPECIFIC REQUIREMENTS")
    requirements = spec.get("specific_requirements", [])
    for i, req in enumerate(requirements, 1):
        doc.body(f"{i}. {req}")
        doc.spacer(0.05)

    doc.spacer(0.15)
    doc.section_header("CURRENT STATE")
    doc.body(spec.get("current_state", "No current state data available."))

    doc.spacer(0.15)
    doc.section_header("SUCCESS CRITERIA")
    doc.body(spec.get("success_criteria", "To be defined."))
    doc.body("The Google Ads Manager system will automatically track these metrics after the change is implemented.")

    doc.build()
    print(f"Brief saved: {output_path}")


def generate_from_proposals(proposals_path, output_dir):
    with open(proposals_path) as f:
        data = json.load(f)

    brief_specs = data.get("brief_specs", [])
    if not brief_specs:
        print("No contractor briefs to generate.")
        return []

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    generated = []

    for spec in brief_specs:
        brief_type = spec.get("brief_type", "task")
        date_str = data["meta"]["week_start"]
        filename = f"brief-{brief_type}-{date_str}.pdf"
        output_path = str(output_dir / filename)

        generate_brief(spec, output_path)
        generated.append(output_path)

    return generated


def main():
    parser = argparse.ArgumentParser(description="Generate contractor briefs from proposals")
    parser.add_argument("--proposals", help="Path to proposals JSON (generates all briefs)")
    parser.add_argument("--spec", help="Path to single brief spec JSON")
    parser.add_argument("--output", help="Output PDF path (for single brief)")
    parser.add_argument("--output-dir", default=str(Path(__file__).parent.parent / "outputs" / "contractor-briefs"))
    args = parser.parse_args()

    if args.proposals:
        generated = generate_from_proposals(args.proposals, args.output_dir)
        print(f"\nGenerated {len(generated)} contractor brief(s)")
        for g in generated:
            print(f"  - {g}")
    elif args.spec and args.output:
        with open(args.spec) as f:
            spec = json.load(f)
        generate_brief(spec, args.output)
    else:
        print("Provide --proposals or (--spec + --output)")
        sys.exit(1)


if __name__ == "__main__":
    main()
