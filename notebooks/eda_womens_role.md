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

# EDA: Women's Role, Feminism, and Equal-Rights Attitudes

Allen Downey

[MIT License](https://en.wikipedia.org/wiki/MIT_License)

Task 6 exploratory analysis: year coverage, raw code distributions, missing codes, and time trends for selected CDF variables. Question text comes from `codebook/extracted/anes_cdf_minimal.json`.

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

# Task 6 selected variables (see project_board.md)
ATTITUDE_VARS = ["VCF0834", "VCF9014", "VCF9017"]
THERMOMETER_VARS = ["VCF0225", "VCF0253"]
SELECTED_VARS = ATTITUDE_VARS + THERMOMETER_VARS
YEAR_VAR = "VCF0004"
```

```python
os.makedirs("logs", exist_ok=True)
input_stem = Path(RAW_FILE).name.replace(".dta.gz", "")
log_path = f"logs/eda_womens_role_{input_stem}.txt"
debug_log = open(log_path, "w")

log_and_print("ANES women's role / feminism EDA")
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
        match = re.match(r"\[(\d+)\]\s*(.*)", part.strip())
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
            "question": entry.get("question", ""),
            "value_labels": entry.get("value_labels", ""),
            "notes": entry.get("notes", ""),
        }
    )

catalog_df = pd.DataFrame(catalog_rows)
catalog_df
```

### Question text

```python
for _, row in catalog_df.iterrows():
    print("=" * 80)
    print(f"{row['variable']} — {row['label']}")
    print(f"Years (catalog): {row['years_catalog']}")
    print(f"Valid range: {row['valid_range']}")
    print(f"Missing codes (catalog): {row['missing_codes']}")
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
fig, axes = plt.subplots(len(SELECTED_VARS), 1, figsize=(10, 1.8 * len(SELECTED_VARS)), sharex=True)
if len(SELECTED_VARS) == 1:
    axes = [axes]

for ax, var in zip(axes, SELECTED_VARS):
    counts = anes.groupby("year")[var].apply(lambda s: s.notna().sum())
    ax.bar(counts.index, counts.values, width=1.5, color="steelblue", alpha=0.85)
    label = catalog_entry(var, catalog).get("label", var)
    ax.set_ylabel("n valid")
    ax.set_title(f"{var} — {label}")

axes[-1].set_xlabel("year")
fig.suptitle("Valid responses by survey year", y=1.01)
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
    n_missing_codes = int(series.isin(inferred_missing).sum())
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
for var in SELECTED_VARS:
    s = summaries[var]
    print("=" * 80)
    print(f"{var} — {s['label']}")
    print(f"Inferred missing codes: {s['inferred_missing_codes']}")
    print(f"Substantive responses (after recode): {s['n_substantive_after_recode']:,}")
    print()
    display(s["raw_value_counts"])
```

## Attitude Scales: Distribution by Year

7-point equal-role scale (`VCF0834`) and 5-point agree–disagree items (`VCF9014`, `VCF9017`). Higher values on `VCF0834` = more traditional (“women's place is in the home”). For backlash items, code 1 = agree strongly with the conservative statement.

```python
def recode_attitude(series, var, catalog):
    """Drop catalog missing/DK codes; return cleaned copy."""
    codes = missing_codes_for_var(var, catalog)
    cleaned = series.copy()
    if codes:
        cleaned = cleaned.mask(cleaned.isin(codes))
    return cleaned


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


fig, axes = plt.subplots(len(ATTITUDE_VARS), 1, figsize=(10, 3 * len(ATTITUDE_VARS)), sharex=True)
if len(ATTITUDE_VARS) == 1:
    axes = [axes]

for ax, var in zip(axes, ATTITUDE_VARS):
    by_year = mean_attitude_by_year(anes, var, catalog)
    ax.plot(by_year.index, by_year.values, marker="o", ms=4)
    label = catalog_entry(var, catalog).get("label", var)
    ax.set_ylabel("mean code")
    ax.set_title(f"{var} — {label}")

axes[-1].set_xlabel("year")
fig.suptitle("Mean response code by year (missing/DK recoded to NaN)", y=1.01)
plt.tight_layout()
plt.show()
```

```python
# Stacked area: response mix over time (attitude scales)
n = len(ATTITUDE_VARS)
fig, axes = plt.subplots(1, n, figsize=(5 * n, 4), sharey=True)
if n == 1:
    axes = [axes]

for ax, var in zip(axes, ATTITUDE_VARS):
    cleaned = recode_attitude(anes[var], var, catalog)
    tmp = anes.assign(_val=cleaned)
    tmp = tmp.loc[tmp["_val"].notna(), ["year", "_val"]]
    if tmp.empty:
        ax.set_title(f"{var}\n(no data)")
        continue
    ct = pd.crosstab(tmp["year"], tmp["_val"], normalize="index")
    ct = ct.sort_index(axis=1)
    ax.stackplot(
        ct.index,
        [ct[col] for col in ct.columns],
        labels=[str(c) for c in ct.columns],
        alpha=0.85,
    )
    ax.set_xlabel("year")
    ax.set_ylabel("proportion")
    ax.set_title(catalog_entry(var, catalog).get("label", var), fontsize=9)
    ax.legend(loc="upper left", fontsize=7, ncol=2, title="code")

fig.suptitle("Response distribution by year (attitude scales)", y=1.02)
plt.tight_layout()
plt.show()
```

## Feeling Thermometers

Group thermometers (`VCF0225`, `VCF0253`): 0–97 degrees, 97 = 97–100 bucket; 98/99 missing.

```python
for var in THERMOMETER_VARS:
    entry = catalog_entry(var, catalog)
    print("=" * 80)
    print(f"{var} — {entry.get('label', '')}")
    print(format_question(entry.get("question", "")))
    print()
    cleaned, _ = recode_thermometer(anes[var].copy(), vcf_var=var, catalog=catalog)
    tmp = anes.assign(_val=cleaned)
    by_year = tmp.loc[tmp["_val"].notna()].groupby("year")["_val"].agg(["mean", "median", "count"])
    by_year.columns = ["mean", "median", "n"]
    display(by_year.round(2))
```

```python
fig, axes = plt.subplots(1, len(THERMOMETER_VARS), figsize=(6 * len(THERMOMETER_VARS), 4))
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
    ax.set_title(catalog_entry(var, catalog).get("label", var))

fig.suptitle("Mean feeling-thermometer rating by year", y=1.02)
plt.tight_layout()
plt.show()
```

## Harmonization Notes (for extract)

```python
notes = []
for var in SELECTED_VARS:
    entry = catalog_entry(var, catalog)
    if entry.get("notes"):
        notes.append({"variable": var, "notes": entry["notes"]})

if notes:
    harmonization_df = pd.DataFrame(notes)
    for _, row in harmonization_df.iterrows():
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

coverage_path = out_dir / "eda_womens_role_coverage.csv"
summary_path = out_dir / "eda_womens_role_missing_summary.csv"

coverage_df.to_csv(coverage_path, index=False)
summary_table.to_csv(summary_path, index=False)

log_and_print(f"\nSaved coverage: {coverage_path}")
log_and_print(f"Saved missing summary: {summary_path}")

debug_log.close()
print(f"Log file closed: {log_path}")
```
