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

# Explore ANES CDF Extract

Allen Downey

[MIT License](https://en.wikipedia.org/wiki/MIT_License)

Read the HDF extract and summarize all variables: missingness, distributions, and time trends.

```python
import os
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from empiricaldist import Cdf
from utils import log_and_print
```

```python tags=["parameters"]
INPUT_FILE = "../data/interim/anes_extract_anes_timeseries_cdf_stata_20260205.hdf"
LABELS_FILE = "../data/interim/anes_extract_anes_timeseries_cdf_stata_20260205_labels.csv"
RAW_FILE = "../data/raw/anes_timeseries_cdf_stata_20260205.dta.gz"
```

```python
os.makedirs("logs", exist_ok=True)
input_stem = Path(INPUT_FILE).stem
log_path = f"logs/eda_{input_stem}.txt"
debug_log = open(log_path, "w")

log_and_print("ANES CDF EDA")
log_and_print(f"Input: {INPUT_FILE}")
log_and_print(f"Labels: {LABELS_FILE}")
```

## Load Data

```python
anes = pd.read_hdf(INPUT_FILE, key="anes")
labels = pd.read_csv(LABELS_FILE)

log_and_print(f"Shape: {anes.shape[0]} rows × {anes.shape[1]} columns")
log_and_print(f"Years: {anes['year'].min():.0f}–{anes['year'].max():.0f}")
log_and_print(f"Thermometer variables in labels file: {len(labels)}")

id_cols = ["VCF0006", "VCF0006a"]
therm_cols = sorted(
    labels.loc[labels["label"].str.contains("Thermometer", na=False), "variable"].tolist(),
    key=lambda v: labels.loc[labels["variable"] == v, "label"].iloc[0],
)
therm_cols = [c for c in therm_cols if c in anes.columns]
vcf_other_cols = [
    c for c in anes.columns
    if c.startswith("VCF") and c not in therm_cols and c not in id_cols
]
log_and_print(f"Thermometer columns in extract: {len(therm_cols)}")
log_and_print(f"Other VCF columns (attitudes, VCF0103, …): {vcf_other_cols}")

anes.head()
```

## Variable Inventory

Summary for every column: dtype, count non-null, percent missing, and unique values (for categoricals).

```python
core_cols = ["year", "age", "cohort", "sex", "VCF0103", "race", "race_eth", "hispanic", "hispanic_type", "polviews", "weight"]
inventory = []
for col in anes.columns:
    series = anes[col]
    n_valid = series.notna().sum()
    n_missing = series.isna().sum()
    pct_missing = 100 * n_missing / len(series)
    row = {
        "variable": col,
        "dtype": str(series.dtype),
        "n_valid": n_valid,
        "n_missing": n_missing,
        "pct_missing": round(pct_missing, 1),
        "n_unique": series.nunique(dropna=True),
    }
    if col in therm_cols or col in vcf_other_cols:
        label_row = labels.loc[labels["variable"] == col, "label"]
        row["label"] = label_row.iloc[0] if len(label_row) else ""
    inventory.append(row)

inventory_df = pd.DataFrame(inventory)
inventory_df["group"] = np.select(
    [
        inventory_df["variable"].isin(core_cols),
        inventory_df["variable"].isin(id_cols),
        inventory_df["variable"].isin(therm_cols),
        inventory_df["variable"].isin(vcf_other_cols),
    ],
    ["core", "id", "thermometer", "attitude"],
    default="other",
)
log_and_print("\nMissingness by group:")
log_and_print(inventory_df.groupby("group")["pct_missing"].describe().round(1).to_string())
inventory_df.sort_values("pct_missing").head(20)
```

```python
inventory_df.sort_values("pct_missing", ascending=False).head(20)
```

## Core Variables

```python
log_and_print("\nCore variable summaries:")
for col in core_cols:
    if col not in anes.columns:
        continue
    log_and_print(f"\n{col}:")
    log_and_print(anes[col].describe().to_string())
    if anes[col].nunique(dropna=True) <= 15:
        log_and_print(anes[col].value_counts(dropna=False).sort_index().to_string())
```

```python
fig, axes = plt.subplots(2, 2, figsize=(10, 8))
axes = axes.ravel()

for ax, col in zip(axes, ["age", "polviews", "race", "race_eth"]):
    subset = anes[[col, "year"]].dropna()
    by_year = subset.groupby("year")[col].mean()
    ax.plot(by_year.index, by_year.values, marker="o", ms=3)
    ax.set_title(f"Mean {col} by year")
    ax.set_xlabel("year")

plt.tight_layout()
plt.show()
```

```python
counts_by_year = anes.groupby("year").size()
log_and_print("\nRespondents by year:")
log_and_print(counts_by_year.to_string())
counts_by_year.plot(figsize=(10, 4), title="Respondents by year")
plt.xlabel("year")
plt.ylabel("count")
plt.tight_layout()
plt.show()
```

## Thermometer Missing Codes

The codebook says group thermometers are coded 00–96 (individual degrees) and 97 (= 97–100), with 98 = DK and 99 = NA. In the raw CDF, **candidate/challenger/incumbent slot variables** also contain harmonized missing codes **990, 996, 997, 998, and 999** — these do not appear in standard group thermometers like `VCF0206`.

```python
with pd.io.stata.StataReader(RAW_FILE) as reader:
    raw_labels = reader.variable_labels()

raw_therms = sorted(n for n, lab in raw_labels.items() if "Thermometer" in lab)
raw = pd.read_stata(RAW_FILE, columns=raw_therms, convert_categoricals=False)

special_rows = []
for col in raw_therms:
    s = raw[col].dropna()
    if s.empty:
        continue
    gt100 = s[s > 100]
    special_rows.append(
        {
            "variable": col,
            "label": raw_labels[col],
            "max": s.max(),
            "n_gt100": len(gt100),
            "gt100_codes": ", ".join(
                f"{v:.0f}({c})" for v, c in gt100.value_counts().head(5).items()
            ),
        }
    )

special_df = pd.DataFrame(special_rows).sort_values("n_gt100", ascending=False)
has_999 = special_df[special_df["gt100_codes"].str.contains("999", na=False)]
log_and_print(f"\nRaw thermometer variables with any value > 100: {(special_df.n_gt100 > 0).sum()}")
log_and_print(f"  of which contain 999: {len(has_999)}")
log_and_print("\nStandard group thermometer VCF0206 (Blacks), values >= 90:")
log_and_print(raw["VCF0206"].value_counts().sort_index().loc[lambda s: s.index >= 90].to_string())
log_and_print("\nCandidate-slot example VCF9056 (Senate Dem Candidate), values >= 90:")
log_and_print(raw["VCF9056"].value_counts().sort_index().loc[lambda s: s.index >= 90].to_string())
has_999.head(10)
```

The extract drops candidate/challenger/incumbent thermometers and recodes 98, 99, negatives, and any value > 100 to NaN on the remaining variables.

### What thermometers are included?

Selection logic lives in `make_cdf_extract.py` (`keep_thermometer`). **Excluded:** derived Average/Index variables, **named candidates** (e.g. Nixon, Clinton), **candidate/challenger/incumbent office slots**, Senator/Jesse Jackson thermometers, and any thermometer asked in **fewer than 6** survey years.

**Included:** mostly **social groups and institutions** (race, religion, class, gender/sexuality, ideology labels) — but **not** a pure “groups only” set. The filter removes *person-specific* politician thermometers, yet still keeps **parties** (Democrats, Republicans, Democratic/Republican Party, Political Parties), **elected offices** (U.S. President, Vice-president), and **government bodies** (Congress, Federal Government, Supreme Court).

```python
POLITICAL_THERM_PATTERNS = (
    "Democrat",
    "Republican",
    "Political Part",
    "President",
    "Vice-president",
    "Congress",
    "Federal Government",
    "Supreme Court",
)


def thermometer_category(label):
    """Rough group vs. political-institution classification for kept thermometers."""
    if any(p in label for p in POLITICAL_THERM_PATTERNS):
        return "political institution / party"
    return "social group / organization"


therm_selection = []
for col in therm_cols:
    label = labels.loc[labels["variable"] == col, "label"].iloc[0]
    therm_selection.append(
        {
            "variable": col,
            "label": label,
            "category": thermometer_category(label),
        }
    )

therm_selection_df = pd.DataFrame(therm_selection).sort_values(["category", "label"])
log_and_print("\nThermometer selection in extract (by category):")
for cat, grp in therm_selection_df.groupby("category"):
    log_and_print(f"\n  {cat} ({len(grp)}):")
    for _, row in grp.iterrows():
        log_and_print(f"    {row['variable']}: {row['label'].replace('Thermometer - ', '').replace('Thermometer for: ', '')}")

log_and_print(
    f"\nSummary: {len(therm_selection_df)} thermometers — "
    f"{(therm_selection_df['category'] == 'social group / organization').sum()} social/group, "
    f"{(therm_selection_df['category'] == 'political institution / party').sum()} political/party"
)
therm_selection_df
```

## Thermometer Variables

Feeling thermometers are coded 0–100 in most years; the HDF extract has missing codes recoded to NaN.

```python
therm_summary = []
for col in therm_cols:
    series = anes[col].dropna()
    therm_summary.append(
        {
            "variable": col,
            "label": labels.loc[labels["variable"] == col, "label"].iloc[0],
            "n_valid": len(series),
            "pct_valid": round(100 * len(series) / len(anes), 1),
            "mean": series.mean() if len(series) else np.nan,
            "std": series.std() if len(series) else np.nan,
            "min": series.min() if len(series) else np.nan,
            "max": series.max() if len(series) else np.nan,
        }
    )

therm_summary_df = pd.DataFrame(therm_summary).sort_values("pct_valid", ascending=False)
log_and_print(f"\nThermometer variables in extract: {len(therm_summary_df)}")
log_and_print(f"Max value across all cleaned thermometers: {therm_summary_df['max'].max():.0f}")
log_and_print(f"Most complete:")
log_and_print(therm_summary_df.head(10)[["variable", "label", "pct_valid", "mean"]].to_string(index=False))
therm_summary_df.head(15)
```

```python
log_and_print("\nLeast complete thermometers:")
therm_summary_df.sort_values("pct_valid").head(10)[
    ["variable", "label", "pct_valid", "mean"]
]
```

```python
# Mean thermometer rating by year for every thermometer variable
label_lookup = dict(zip(labels["variable"], labels["label"]))

def short_label(col):
    text = label_lookup.get(col, col)
    return text.replace("Thermometer - ", "").replace("Thermometer for: ", "")

def mean_therm_by_year(data, col):
    """Mean thermometer rating by year (missing codes already recoded in extract)."""
    mask = data[col].notna()
    if not mask.any():
        return pd.Series(dtype=float)
    return data.loc[mask].groupby("year")[col].mean()

# Shared x-axis: earliest and latest year with any thermometer data
therm_cols = sorted(therm_cols, key=short_label)
year_mins, year_maxs = [], []
for col in therm_cols:
    valid_years = anes.loc[anes[col].notna(), "year"]
    if len(valid_years):
        year_mins.append(valid_years.min())
        year_maxs.append(valid_years.max())

xmin = min(year_mins)
xmax = max(year_maxs)
log_and_print(f"\nThermometer year range across all variables: {xmin:.0f}–{xmax:.0f}")

n_cols = 4
n_rows = int(np.ceil(len(therm_cols) / n_cols))
fig, axes = plt.subplots(n_rows, n_cols, figsize=(16, 2.2 * n_rows), sharex=True)
axes = np.atleast_1d(axes).ravel()

for ax, col in zip(axes, therm_cols):
    by_year = mean_therm_by_year(anes, col)
    ax.plot(by_year.index, by_year.values, marker="o", ms=2, lw=1)
    ax.set_title(short_label(col), fontsize=8)
    ax.set_xlim(xmin, xmax)
    ax.tick_params(labelsize=7)

for ax in axes[len(therm_cols):]:
    ax.set_visible(False)

fig.supxlabel("year")
fig.suptitle(
    f"Mean thermometer rating by year (all {len(therm_cols)} variables, x-axis {xmin:.0f}–{xmax:.0f})",
    y=1.002,
)
plt.tight_layout()
plt.show()
```

```python
# Empirical CDF of each thermometer variable (cleaned extract)
therm_cols = sorted(therm_cols, key=short_label)

n_cols = 4
n_rows = int(np.ceil(len(therm_cols) / n_cols))
fig, axes = plt.subplots(n_rows, n_cols, figsize=(16, 2.2 * n_rows), sharex=True)
axes = np.atleast_1d(axes).ravel()

for ax, col in zip(axes, therm_cols):
    values = anes[col].dropna()
    if len(values):
        cdf = Cdf.from_seq(values)
        cdf.plot(ax=ax, drawstyle="steps-post", lw=1)
    ax.set_title(short_label(col), fontsize=8)
    ax.set_xlim(0, 100)
    ax.tick_params(labelsize=7)

for ax in axes[len(therm_cols):]:
    ax.set_visible(False)

fig.supxlabel("thermometer rating")
fig.suptitle(f"Empirical CDF of each thermometer variable (n={len(therm_cols)})", y=1.002)
plt.tight_layout()
plt.show()
```

```python
# Pooled distribution of all cleaned thermometer values
valid_temps = anes[therm_cols].stack().dropna()
log_and_print(f"\nPooled cleaned thermometer values: n={len(valid_temps):,}")
log_and_print(valid_temps.describe().to_string())

cdf = Cdf.from_seq(valid_temps)
plt.figure(figsize=(8, 4))
cdf.plot(drawstyle="steps-post")
plt.xlabel("thermometer rating")
plt.ylabel("CDF")
plt.title("Empirical CDF of all feeling-thermometer responses (pooled)")
plt.tight_layout()
plt.show()
```

## Thermometer Response Patterns

Summarize where responses pile up: modal rating (is 50 the neutral midpoint?), share at 50, and mean rating by target group. Compare means across thermometers (warmest vs. coldest target).

```python
label_lookup = dict(zip(labels["variable"], labels["label"]))


def short_label(col):
    text = label_lookup.get(col, col)
    return text.replace("Thermometer - ", "").replace("Thermometer for: ", "")


pattern_rows = []
for col in therm_cols:
    series = anes[col].dropna()
    if series.empty:
        continue
    counts = series.value_counts()
    mode_val = counts.index[0]
    pattern_rows.append(
        {
            "variable": col,
            "label": short_label(col),
            "category": thermometer_category(
                labels.loc[labels["variable"] == col, "label"].iloc[0]
            ),
            "n_valid": len(series),
            "mean": series.mean(),
            "median": series.median(),
            "mode": mode_val,
            "pct_at_mode": round(100 * counts.iloc[0] / len(series), 1),
            "pct_at_50": round(100 * (series == 50).mean(), 1),
        }
    )

therm_pattern_df = pd.DataFrame(pattern_rows).sort_values("mean")
therm_pattern_df["rank_mean"] = therm_pattern_df["mean"].rank().astype(int)

log_and_print("\n" + "=" * 80)
log_and_print("THERMOMETER RESPONSE PATTERNS")
log_and_print("=" * 80)

n_mode_50 = int((therm_pattern_df["mode"] == 50).sum())
log_and_print(
    f"\nModal rating is 50 (neutral midpoint) for {n_mode_50} of {len(therm_pattern_df)} thermometers"
)
log_and_print(
    f"Share of responses at exactly 50 — median across thermometers: "
    f"{therm_pattern_df['pct_at_50'].median():.1f}% "
    f"(range {therm_pattern_df['pct_at_50'].min():.1f}%–{therm_pattern_df['pct_at_50'].max():.1f}%)"
)

pooled_temps = anes[therm_cols].stack().dropna()
pooled_counts = pooled_temps.value_counts()
pooled_mode = pooled_counts.index[0]
log_and_print(f"\nPooled across all thermometers (n={len(pooled_temps):,}):")
log_and_print(f"  Most common single rating: {pooled_mode:.0f} ({100 * pooled_counts.iloc[0] / len(pooled_temps):.1f}%)")
log_and_print(f"  Share at 50: {100 * (pooled_temps == 50).mean():.1f}%")
log_and_print("  Top 5 ratings:")
for val, cnt in pooled_counts.head(5).items():
    log_and_print(f"    {val:.0f}: {100 * cnt / len(pooled_temps):.1f}%")

mean_of_means = therm_pattern_df["mean"].mean()
min_row = therm_pattern_df.iloc[0]
max_row = therm_pattern_df.iloc[-1]
mean_spread = max_row["mean"] - min_row["mean"]

log_and_print(f"\nMean rating across thermometers (each variable's mean, then summarized):")
log_and_print(f"  Mean of per-thermometer means: {mean_of_means:.1f}")
log_and_print(f"  Lowest mean: {min_row['mean']:.1f} — {min_row['label']} ({min_row['variable']})")
log_and_print(f"  Highest mean: {max_row['mean']:.1f} — {max_row['label']} ({max_row['variable']})")
log_and_print(f"  Spread (highest − lowest mean): {mean_spread:.1f}")

log_and_print("\nPer-thermometer detail (sorted by mean, coldest → warmest):")
log_and_print(
    therm_pattern_df[
        ["variable", "label", "category", "n_valid", "mean", "mode", "pct_at_mode", "pct_at_50"]
    ].to_string(index=False)
)

therm_pattern_df
```

```python
fig, axes = plt.subplots(1, 2, figsize=(12, 5))

axes[0].barh(therm_pattern_df["label"], therm_pattern_df["mean"], color="steelblue", alpha=0.85)
axes[0].axvline(50, color="gray", ls="--", lw=1, label="neutral (50)")
axes[0].axvline(mean_of_means, color="darkorange", ls=":", lw=1.5, label=f"mean of means ({mean_of_means:.0f})")
axes[0].set_xlabel("mean rating")
axes[0].set_title("Mean thermometer rating by target")
axes[0].legend(fontsize=8)
axes[0].invert_yaxis()

axes[1].hist(therm_pattern_df["pct_at_50"], bins=12, color="steelblue", alpha=0.85, edgecolor="white")
axes[1].set_xlabel("% of responses at exactly 50")
axes[1].set_ylabel("number of thermometer variables")
axes[1].set_title("How often is 50 the most common answer?")

plt.tight_layout()
plt.show()
```

## Save Summary Tables

```python
inventory_path = "../data/processed/anes_cdf_inventory.csv"
therm_path = "../data/processed/anes_cdf_thermometer_summary.csv"
pattern_path = "../data/processed/anes_cdf_thermometer_patterns.csv"
os.makedirs("../data/processed", exist_ok=True)

inventory_df.to_csv(inventory_path, index=False)
therm_summary_df.to_csv(therm_path, index=False)
therm_pattern_df.to_csv(pattern_path, index=False)
log_and_print(f"\nSaved inventory: {inventory_path}")
log_and_print(f"Saved thermometer summary: {therm_path}")
log_and_print(f"Saved thermometer patterns: {pattern_path}")

debug_log.close()
print(f"Log file closed: {log_path}")
```
