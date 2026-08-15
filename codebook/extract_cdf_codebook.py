#!/usr/bin/env python3
"""Extract ANES CDF variable metadata from the HTML codebook and Stata headers.

Reads the HTML codebook and Stata metadata once, then writes cached JSON/CSV
catalogs under codebook/extracted/. Run with the ExtractANES conda env active:

    conda activate ExtractANES
    python codebook/extract_cdf_codebook.py

Or: make extract_codebook
"""

from __future__ import annotations

import argparse
import csv
import html
import json
import re
from pathlib import Path

import pandas as pd

CODEBOOK_DIR = Path(__file__).parent
HTML_FILE = CODEBOOK_DIR / (
    "ANES TIME SERIES CUMULATIVE DATA FILE 1948-2024 VARIABLE CODEBOOK.html"
)
OUTPUT_DIR = CODEBOOK_DIR / "extracted"
DEFAULT_STATA = CODEBOOK_DIR.parent / "data/raw/anes_timeseries_cdf_stata_20260205.dta.gz"

VAR_HEADER_RE = re.compile(
    r"<table class=\"table table-condensed\s*\">"
    r"\s*<tbody><tr class=\"blocks header\">"
    r"\s*<td class=\"first\"[^>]*>\s*(VCF\d{4}[a-z]?)\s*</td>"
    r"\s*<td class=\"second\">\s*(.*?)\s*</td>",
    re.DOTALL | re.IGNORECASE,
)
SECTION_RE = re.compile(
    r"<div style=\"font-weight: bold; \">\s*(\w+)\s*</div>\s*"
    r"<div style=\"padding-left:70px[^\"]*\">(.*?)</div>",
    re.DOTALL | re.IGNORECASE,
)
MISSING_CODE_RE = re.compile(r"^\s*(\d+)\.", re.MULTILINE)
YEAR_IN_SOURCES_RE = re.compile(r"\b(19\d{2}|20\d{2}):\s")


def html_to_text(raw: str) -> str:
    text = re.sub(r"<br\s*/?>", "\n", raw, flags=re.IGNORECASE)
    text = re.sub(r"<[^>]+>", "", text)
    return html.unescape(text).strip()


def parse_missing_codes(text: str) -> list[int]:
    if not text:
        return []
    return sorted({int(m.group(1)) for m in MISSING_CODE_RE.finditer(text)})


def parse_valid_range(text: str) -> str:
    """Derive a compact valid-range string from the Valid section."""
    if not text:
        return ""
    numbers: list[int] = []
    for line in text.splitlines():
        m = re.match(r"^\s*(\d+)\.", line.strip())
        if m:
            numbers.append(int(m.group(1)))
        m_range = re.match(r"^\s*(\d+)\s*-\s*(\d+)\.", line.strip())
        if m_range:
            lo, hi = int(m_range.group(1)), int(m_range.group(2))
            numbers.extend([lo, hi])
    if not numbers:
        return ""
    lo, hi = min(numbers), max(numbers)
    if lo == hi:
        return str(lo)
    return f"{lo}-{hi}"


def parse_years_from_sources(text: str) -> str:
    if not text:
        return ""
    years = sorted({int(y) for y in YEAR_IN_SOURCES_RE.findall(text)})
    return ", ".join(str(y) for y in years)


def format_value_labels(value_labels: dict) -> str:
    if not value_labels:
        return ""
    parts = []
    for code in sorted(value_labels):
        parts.append(f"[{code}] {value_labels[code]}")
    return " / ".join(parts)


def parse_html_codebook(path: Path) -> dict[str, dict]:
    text = path.read_text(encoding="utf-8", errors="replace")
    entries: dict[str, dict] = {}

    for match in VAR_HEADER_RE.finditer(text):
        var_name = match.group(1).upper()
        label_html = html_to_text(match.group(2))
        table_end = text.find("</table>", match.end())
        if table_end == -1:
            continue
        table_html = text[match.start() : table_end]

        sections: dict[str, str] = {}
        for sec in SECTION_RE.finditer(table_html):
            key = sec.group(1).lower()
            sections[key] = html_to_text(sec.group(2))

        missing_text = sections.get("missing", "")
        valid_text = sections.get("valid", "")
        sources_text = sections.get("sources", "")

        entries[var_name] = {
            "variable": var_name,
            "label_html": label_html,
            "question": sections.get("question", ""),
            "valid_text": valid_text,
            "valid_range": parse_valid_range(valid_text),
            "missing_text": missing_text,
            "missing_codes": parse_missing_codes(missing_text),
            "notes": sections.get("notes", ""),
            "weight": sections.get("weight", ""),
            "sources": sources_text,
            "years_available": parse_years_from_sources(sources_text),
        }

    return entries


def read_stata_metadata(path: Path) -> tuple[dict[str, str], dict[str, dict]]:
    with pd.io.stata.StataReader(path) as reader:
        var_labels = reader.variable_labels()
        value_label_sets = reader.value_labels()
        varlist = reader._varlist
        lbllist = reader._lbllist

    per_var_labels: dict[str, dict] = {}
    for var, lbl_name in zip(varlist, lbllist):
        if lbl_name:
            per_var_labels[var] = value_label_sets.get(lbl_name, {})
        else:
            per_var_labels[var] = {}

    return var_labels, per_var_labels


def build_catalog(
    html_entries: dict[str, dict],
    var_labels: dict[str, str],
    stata_value_labels: dict[str, dict],
) -> tuple[dict, dict]:
    minimal: dict[str, dict] = {}
    full: dict[str, dict] = {}

    def html_for_var(var: str) -> dict:
        return html_entries.get(var.upper(), html_entries.get(var, {}))

    for var in var_labels:
        html_meta = html_for_var(var)
        vl = stata_value_labels.get(var, {})
        label = var_labels.get(var, "") or html_meta.get("label_html", "")

        entry_minimal = {
            "variable": var,
            "label": label,
            "question": html_meta.get("question", ""),
            "value_labels": format_value_labels(vl),
            "missing_codes": html_meta.get("missing_codes", []),
            "valid_range": html_meta.get("valid_range", ""),
            "years_available": html_meta.get("years_available", "") or None,
            "notes": html_meta.get("notes", ""),
        }
        minimal[var] = entry_minimal

        full[var] = {
            **entry_minimal,
            "label_html": html_meta.get("label_html", ""),
            "valid_text": html_meta.get("valid_text", ""),
            "missing_text": html_meta.get("missing_text", ""),
            "weight": html_meta.get("weight", ""),
            "sources": html_meta.get("sources", ""),
            "value_labels_dict": {str(k): v for k, v in sorted(vl.items())},
        }

    return minimal, full


def write_summary_csv(path: Path, minimal: dict[str, dict]) -> None:
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(
            [
                "variable",
                "label",
                "question",
                "valid_range",
                "missing_codes",
                "years_available",
                "has_notes",
                "n_value_labels",
            ]
        )
        for var in sorted(minimal):
            e = minimal[var]
            writer.writerow(
                [
                    var,
                    e.get("label", "")[:100],
                    e.get("question", "")[:120],
                    e.get("valid_range", ""),
                    ";".join(str(c) for c in e.get("missing_codes", [])),
                    e.get("years_available") or "",
                    "Yes" if e.get("notes") else "No",
                    len(e.get("value_labels", "").split(" / ")) if e.get("value_labels") else 0,
                ]
            )


def validate(minimal: dict, html_entries: dict, stata_vars: list[str]) -> None:
    n_stata = len(stata_vars)
    n_minimal = len(minimal)
    n_html = len(html_entries)
    html_only = sorted(
        v for v in html_entries if v.upper() not in {s.upper() for s in stata_vars}
    )
    stata_no_html = sorted(
        v for v in stata_vars if v.upper() not in html_entries
    )

    print("=" * 60)
    print("VALIDATION")
    print("=" * 60)
    print(f"Stata variables:     {n_stata}")
    print(f"HTML variables:      {n_html}")
    print(f"Catalog entries:     {n_minimal}")
    print(f"Stata without HTML:  {len(stata_no_html)}")
    print(f"HTML without Stata:  {len(html_only)}")

    if stata_no_html:
        print(f"  e.g. {stata_no_html[:5]}")
    if html_only:
        print(f"  e.g. {html_only[:5]}")

    with_question = sum(1 for e in minimal.values() if e.get("question"))
    with_missing = sum(1 for e in minimal.values() if e.get("missing_codes"))
    with_years = sum(1 for e in minimal.values() if e.get("years_available"))
    print(f"With question text:  {with_question}")
    print(f"With missing_codes:  {with_missing}")
    print(f"With years_available:{with_years}")

    # Spot-check known variables
    for var in ["VCF0101", "VCF0104", "VCF0206", "VCF0803"]:
        e = minimal.get(var, {})
        print(f"\n{var}: {e.get('label', '')[:50]}")
        print(f"  missing_codes: {e.get('missing_codes')}")
        print(f"  valid_range:   {e.get('valid_range')}")
        print(f"  value_labels:  {e.get('value_labels', '')[:80]}...")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--html", type=Path, default=HTML_FILE)
    parser.add_argument("--stata", type=Path, default=DEFAULT_STATA)
    parser.add_argument("--output-dir", type=Path, default=OUTPUT_DIR)
    args = parser.parse_args()

    if not args.html.exists():
        raise FileNotFoundError(f"HTML codebook not found: {args.html}")
    if not args.stata.exists():
        raise FileNotFoundError(f"Stata file not found: {args.stata}")

    args.output_dir.mkdir(parents=True, exist_ok=True)

    print(f"Parsing HTML:  {args.html}")
    html_entries = parse_html_codebook(args.html)
    print(f"  Found {len(html_entries)} variable sections")

    print(f"Reading Stata: {args.stata}")
    var_labels, stata_value_labels = read_stata_metadata(args.stata)
    print(f"  Found {len(var_labels)} variables")

    minimal, full = build_catalog(html_entries, var_labels, stata_value_labels)

    minimal_path = args.output_dir / "anes_cdf_minimal.json"
    dict_path = args.output_dir / "anes_cdf_dict.json"
    summary_path = args.output_dir / "anes_cdf_summary.csv"

    with minimal_path.open("w", encoding="utf-8") as f:
        json.dump(minimal, f, indent=2, ensure_ascii=False)
    print(f"Wrote {minimal_path} ({minimal_path.stat().st_size / 1e6:.1f} MB)")

    with dict_path.open("w", encoding="utf-8") as f:
        json.dump(full, f, indent=2, ensure_ascii=False)
    print(f"Wrote {dict_path} ({dict_path.stat().st_size / 1e6:.1f} MB)")

    write_summary_csv(summary_path, minimal)
    print(f"Wrote {summary_path}")

    validate(minimal, html_entries, list(var_labels.keys()))


if __name__ == "__main__":
    main()
