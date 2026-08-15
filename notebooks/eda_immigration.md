---
jupyter:
  jupytext:
    text_representation:
      extension: .md
      format_name: markdown
      format_version: '1.3'
      jupytext_version: 1.19.1
  kernelspec:
    display_name: Python 3
    language: python
    name: python3
---

# EDA: Immigration, Immigrant Threat, and Group Stereotypes

Allen Downey

[MIT License](https://en.wikipedia.org/wiki/MIT_License)

Task 9 exploratory analysis: year coverage, raw code distributions, missing codes, and time trends for selected CDF variables. Question text comes from `codebook/extracted/anes_cdf_minimal.json`.

```python
import os
import re
import textwrap
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from utils import (
    catalog_entry,
    load_cdf_catalog,
    log_and_print,
    missing_codes_for_var,
    recode_thermometer,
)
```

```python tags=["parameters"]
RAW_FILE = "../data/raw/anes_timeseries_cdf_stata_20260205.dta.gz"

# Task 9 selected variables (see project_board.md)
VOLUME_VARS = ["VCF0879", "VCF0879a"]
THREAT_VARS = ["VCF9223"]
STEREOTYPE_VARS = ["VCF9270", "VCF9271", "VCF9272", "VCF9273"]
SPENDING_VARS = ["VCF0892"]
DEMOG_VARS = ["VCF0108", "VCF0107"]
ATTITUDE_VARS = VOLUME_VARS + THREAT_VARS + STEREOTYPE_VARS + SPENDING_VARS
THERMOMETER_VARS = ["VCF0217", "VCF0227", "VCF0233"]  # already in extract
SELECTED_VARS = ATTITUDE_VARS + DEMOG_VARS + THERMOMETER_VARS
YEAR_VAR = "VCF0004"
```

```python
os.makedirs("logs", exist_ok=True)
input_stem = Path(RAW_FILE).name.replace(".dta.gz", "")
log_path = f"logs/eda_immigration_{input_stem}.txt"
debug_log = open(log_path, "w")

log_and_print("ANES immigration / stereotype EDA")
log_and_print(f"Raw file: {RAW_FILE}")
log_and_print(f"Variables: {', '.join(SELECTED_VARS)}")
```

## Catalog: Questions and Value Labels

```python
catalog = load_cdf_catalog()


def parse_value_labels(value_labels):
    """Parse GSS-style value_labels string into {code: label}."""
    if not value_labels:
        return {}
    out = {}
    for part in value_labels.split(" / "):
        match = re.match(r"\[(-?\d+)\]\s*(.*)", part.strip())
        if match:
            out[int(match.group(1))] = match.group(2)
    return out


def format_question(text, width=88):
    """Normalize codebook newlines for display."""
    if not text:
        return ""
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    return "\n".join(textwrap.fill(ln, width=width) for ln in lines)


catalog_rows = []
for var in SELECTED_VARS:
    entry = catalog_entry(var, catalog)
    catalog_rows.append(
        {
            "variable": var,
            "label": entry.get("label", ""),
            "years_catalog": entry.get("years_available", ""),
            "valid_range": entry.get("valid_range", ""),
            "missing_codes": entry.get("missing_codes", []),
            "inferred_missing": missing_codes_for_var(var, catalog),
            "question": entry.get("question", ""),
            "value_labels": entry.get("value_labels", ""),
            "notes": entry.get("notes", ""),
        }
    )

catalog_df = pd.DataFrame(catalog_rows)
catalog_df[["variable", "label", "years_catalog", "valid_range", "missing_codes", "inferred_missing"]]
```

### Question text

```python
for _, row in catalog_df.iterrows():
    print("=" * 80)
    print(f"{row['variable']} — {row['label']}")
    print(f"Years (catalog): {row['years_catalog']}")
    print(f"Valid range: {row['valid_range']}")
    print(f"Catalog missing: {row['missing_codes']}")
    print(f"Inferred missing: {row['inferred_missing']}")
    print()
    print("QUESTION:")
    print(format_question(row["question"]))
    print()
    print("VALUE LABELS:")
    for code, label in sorted(parse_value_labels(row["value_labels"]).items()):
        print(f"  [{code}] {label}")
    if row["notes"]:
        print()
        print("NOTES:")
        print(format_question(row["notes"]))
    print()
```

## Load Raw CDF Columns

```python
read_cols = [YEAR_VAR] + SELECTED_VARS
anes = pd.read_stata(RAW_FILE, columns=read_cols, convert_categoricals=False)
anes = anes.rename(columns={YEAR_VAR: "year"})

log_and_print(f"Loaded {anes.shape[0]:,} rows × {anes.shape[1]} columns")
log_and_print(f"Survey years in file: {anes['year'].min():.0f}–{anes['year'].max():.0f}")
anes.head()
```

## Year Coverage

```python
coverage_rows = []
for var in SELECTED_VARS:
    asked = anes.loc[anes[var].notna(), "year"]
    n_years = asked.nunique()
    years_list = sorted(int(y) for y in asked.unique())
    coverage_rows.append(
        {
            "variable": var,
            "label": catalog_entry(var, catalog).get("label", ""),
            "n_years_with_data": n_years,
            "years_with_data": ", ".join(str(y) for y in years_list),
            "n_valid": int(anes[var].notna().sum()),
            "pct_valid": round(100 * anes[var].notna().mean(), 1),
        }
    )

coverage_df = pd.DataFrame(coverage_rows)
log_and_print("\nYear coverage:")
log_and_print(coverage_df.to_string(index=False))
coverage_df
```

```python
plot_vars = ATTITUDE_VARS
fig, axes = plt.subplots(len(plot_vars), 1, figsize=(10, 1.6 * len(plot_vars)), sharex=True)
if len(plot_vars) == 1:
    axes = [axes]

for ax, var in zip(axes, plot_vars):
    counts = anes.groupby("year")[var].apply(lambda s: s.notna().sum())
    ax.bar(counts.index, counts.values, width=1.5, color="steelblue", alpha=0.85)
    label = catalog_entry(var, catalog).get("label", var)
    ax.set_ylabel("n valid")
    ax.set_title(f"{var} — {label}", fontsize=9)

axes[-1].set_xlabel("year")
fig.suptitle("Valid responses by survey year (Task 9 attitude items)", y=1.01)
plt.tight_layout()
plt.show()
```

## Missing Codes and Raw Distributions

```python
def value_counts_with_labels(series, value_label_map):
    """Value counts with codebook labels appended."""
    counts = series.value_counts(dropna=False).sort_index()
    rows = []
    for code, n in counts.items():
        if pd.isna(code):
            label = "(pandas NaN)"
        else:
            code_int = int(code)
            label = value_label_map.get(code_int, "")
        rows.append({"code": code, "label": label, "count": int(n)})
    return pd.DataFrame(rows)


def summarize_variable(df, var, catalog):
    entry = catalog_entry(var, catalog)
    value_label_map = parse_value_labels(entry.get("value_labels", ""))
    inferred_missing = missing_codes_for_var(var, catalog)
    series = df[var]

    raw_counts = value_counts_with_labels(series, value_label_map)
    # Include negatives as missing for modern ANES codes (see utils.recode_vcf_columns).
    miss_mask = series.isin(inferred_missing) | (series.notna() & (series < 0))
    n_missing_codes = int(miss_mask.sum())
    n_valid_after_recode = int(series.notna().sum() - n_missing_codes)

    return {
        "variable": var,
        "label": entry.get("label", ""),
        "inferred_missing_codes": inferred_missing,
        "n_raw_nonnull": int(series.notna().sum()),
        "n_missing_code_rows": n_missing_codes,
        "n_substantive_after_recode": n_valid_after_recode,
        "raw_value_counts": raw_counts,
    }


summaries = {var: summarize_variable(anes, var, catalog) for var in SELECTED_VARS}

summary_table = pd.DataFrame(
    [
        {
            "variable": s["variable"],
            "label": s["label"],
            "missing_codes": s["inferred_missing_codes"],
            "n_raw_nonnull": s["n_raw_nonnull"],
            "n_missing_code_rows": s["n_missing_code_rows"],
            "n_substantive": s["n_substantive_after_recode"],
        }
        for s in summaries.values()
    ]
)
log_and_print("\nMissing-code summary:")
log_and_print(summary_table.to_string(index=False))
summary_table
```

```python
for var in ATTITUDE_VARS + DEMOG_VARS:
    s = summaries[var]
    print("=" * 80)
    print(f"{var} — {s['label']}")
    print(f"Inferred missing codes: {s['inferred_missing_codes']}")
    print(f"Substantive responses (after recode): {s['n_substantive_after_recode']:,}")
    print()
    display(s["raw_value_counts"])
```

## Attitude Scales: Distribution by Year

- **Volume** (`VCF0879` / `VCF0879a`): higher = prefer fewer immigrants (1 increase … 5 decrease).
- **Jobs threat** (`VCF9223`): 1 = extremely likely take jobs … 4 = not at all likely (higher = less threat).
- **Stereotypes** (`VCF9270`–`VCF9273`): 1 = hardworking … 7 = lazy (higher = more negative stereotype).
- **Foreign aid** (`VCF0892`): 1 = increase, 2 = same, 3 = decrease.

```python
def recode_attitude(series, var, catalog):
    """Drop catalog missing/DK codes and negatives; return cleaned copy."""
    codes = missing_codes_for_var(var, catalog)
    cleaned = series.copy()
    miss = cleaned.isin(codes) | (cleaned.notna() & (cleaned < 0))
    return cleaned.mask(miss)


def pct_by_code_by_year(df, var, catalog, normalize="index"):
    """Cross-tab of response code by year (row percentages)."""
    cleaned = recode_attitude(df[var], var, catalog)
    tmp = df.assign(_val=cleaned)
    tmp = tmp.loc[tmp["_val"].notna(), ["year", "_val"]]
    if tmp.empty:
        return pd.DataFrame()
    ct = pd.crosstab(tmp["year"], tmp["_val"], normalize=normalize) * 100
    ct.columns = [f"{c:.0f}" for c in ct.columns]
    return ct.round(1)


for var in ATTITUDE_VARS:
    entry = catalog_entry(var, catalog)
    print("=" * 80)
    print(f"{var} — {entry.get('label', '')}")
    print(format_question(entry.get("question", "")))
    print()
    pct = pct_by_code_by_year(anes, var, catalog)
    if pct.empty:
        print("(no substantive responses)")
    else:
        display(pct)
```

```python
def mean_attitude_by_year(df, var, catalog):
    cleaned = recode_attitude(df[var], var, catalog)
    tmp = df.assign(_val=cleaned)
    return tmp.loc[tmp["_val"].notna()].groupby("year")["_val"].mean()


# Volume + threat means
plot_main = VOLUME_VARS + THREAT_VARS + SPENDING_VARS
fig, axes = plt.subplots(len(plot_main), 1, figsize=(10, 2.8 * len(plot_main)), sharex=True)
if len(plot_main) == 1:
    axes = [axes]

for ax, var in zip(axes, plot_main):
    by_year = mean_attitude_by_year(anes, var, catalog)
    ax.plot(by_year.index, by_year.values, marker="o", ms=4)
    label = catalog_entry(var, catalog).get("label", var)
    ax.set_ylabel("mean code")
    ax.set_title(f"{var} — {label}", fontsize=9)

axes[-1].set_xlabel("year")
fig.suptitle("Mean response by year (volume / threat / foreign aid)", y=1.01)
plt.tight_layout()
plt.show()
```

```python
# Stereotype battery means (higher = more lazy)
fig, ax = plt.subplots(figsize=(10, 4))
for var in STEREOTYPE_VARS:
    by_year = mean_attitude_by_year(anes, var, catalog)
    ax.plot(by_year.index, by_year.values, marker="o", ms=4, label=var)

ax.set_xlabel("year")
ax.set_ylabel("mean (1=hardworking … 7=lazy)")
ax.set_ylim(1, 7)
ax.legend(fontsize=8)
ax.set_title("Hardworking–lazy stereotype means by group and year")
plt.tight_layout()
plt.show()
```

## VCF0879 vs VCF0879a (coding check)

Keep both in the extract for APC coding checks. Prefer **`VCF0879`** (6-category) when available; **`VCF0879a`** adds **2000** and collapses increase/decrease into single categories.

```python
both = anes.loc[anes["VCF0879"].notna() & anes["VCF0879a"].notna(), ["year", "VCF0879", "VCF0879a"]]
log_and_print(f"\nRows with both VCF0879 and VCF0879a: {len(both):,}")
if len(both):
    ct = pd.crosstab(both["VCF0879"], both["VCF0879a"])
    log_and_print("Crosstab VCF0879 (rows) × VCF0879a (cols):")
    log_and_print(ct.to_string())
    display(ct)

only_a = anes.loc[anes["VCF0879"].isna() & anes["VCF0879a"].notna(), "year"]
log_and_print(f"\nYears with VCF0879a but not VCF0879: {sorted(int(y) for y in only_a.unique())}")
log_and_print(f"  n rows: {len(only_a):,}")
```

## Feeling Thermometers (cross-reference)

`VCF0217` (Hispanics), `VCF0227` (Asian-Americans), `VCF0233` (illegal aliens / illegal immigrants) are already in the extract.

```python
fig, axes = plt.subplots(1, len(THERMOMETER_VARS), figsize=(5 * len(THERMOMETER_VARS), 4), sharey=True)
if len(THERMOMETER_VARS) == 1:
    axes = [axes]

for ax, var in zip(axes, THERMOMETER_VARS):
    cleaned, _ = recode_thermometer(anes[var].copy(), vcf_var=var, catalog=catalog)
    tmp = anes.assign(_val=cleaned)
    by_year = tmp.loc[tmp["_val"].notna()].groupby("year")["_val"].mean()
    ax.plot(by_year.index, by_year.values, marker="o", ms=4)
    ax.set_xlabel("year")
    ax.set_ylabel("mean thermometer")
    ax.set_ylim(0, 100)
    ax.set_title(catalog_entry(var, catalog).get("label", var), fontsize=9)

fig.suptitle("Related group thermometers (already in extract)", y=1.02)
plt.tight_layout()
plt.show()
```

## Harmonization Notes (for extract)

```python
notes = []
for var in ATTITUDE_VARS + DEMOG_VARS:
    entry = catalog_entry(var, catalog)
    if entry.get("notes"):
        notes.append({"variable": var, "notes": entry["notes"]})

if notes:
    for _, row in pd.DataFrame(notes).iterrows():
        print("=" * 80)
        print(row["variable"])
        print(format_question(row["notes"]))
else:
    print("No harmonization notes in catalog.")
```

## Save Summary

```python
out_dir = Path("../data/processed")
out_dir.mkdir(parents=True, exist_ok=True)

coverage_path = out_dir / "eda_immigration_coverage.csv"
summary_path = out_dir / "eda_immigration_missing_summary.csv"

coverage_df.to_csv(coverage_path, index=False)
summary_table.to_csv(summary_path, index=False)

log_and_print(f"\nSaved coverage: {coverage_path}")
log_and_print(f"Saved missing summary: {summary_path}")

debug_log.close()
print(f"Log file closed: {log_path}")
```
