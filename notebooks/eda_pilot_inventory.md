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

# EDA: ANES Pilot inventory vs book CDF variables

Allen Downey

[MIT License](https://en.wikipedia.org/wiki/MIT_License)

Task 10: map local Pilot studies (2022, 2019, 2018, 2016) to CultureWar book VCFs (`SELECTED_VALUES` in `~/CultureWar/notebooks/utils.py`). Decide whether a separate Pilot extract is worth building before downloading older Pilots.

```python
import os
from pathlib import Path

import pandas as pd

from build_pilot_crosswalk import BOOK_VCFS, build_crosswalk, main as write_crosswalk
from utils import log_and_print
```

```python
os.makedirs("logs", exist_ok=True)
debug_log = open("logs/eda_pilot_inventory.txt", "w")

log_and_print("ANES Pilot ↔ book CDF inventory (Task 10)")
log_and_print(f"Book VCFs tracked: {len(BOOK_VCFS)}")
```

## Build / load crosswalk

```python
write_crosswalk()
meta_df, cross_df = build_crosswalk()
meta_df
```

```python
log_and_print("\nPilot study sizes:")
log_and_print(meta_df.to_string(index=False))
```

## Coverage summary

```python
status_order = ["match", "match_split", "related", "miss"]
summary = (
    cross_df.assign(
        match_status=pd.Categorical(cross_df["match_status"], status_order, ordered=True)
    )
    .groupby(["pilot_year", "match_status"], observed=False)
    .size()
    .unstack(fill_value=0)
)
log_and_print("\nMatch status counts:")
log_and_print(summary.to_string())
summary
```

```python
useful = (
    cross_df.loc[cross_df["match_status"] != "miss"]
    .groupby("pilot_year")
    .size()
    .rename("n_useful")
    .to_frame()
)
useful["n_book"] = len(BOOK_VCFS)
useful["pct_useful"] = (100 * useful["n_useful"] / useful["n_book"]).round(1)
log_and_print("\nShare of book VCFs with Pilot analogue:")
log_and_print(useful.to_string())
useful
```

## Detail by Pilot year

```python
status_rank = {"match": 0, "match_split": 1, "related": 2, "miss": 3}

for year in sorted(cross_df["pilot_year"].unique(), reverse=True):
    print("=" * 80)
    print(f"Pilot {year}")
    sub = cross_df.loc[cross_df["pilot_year"] == year].copy()
    sub["_rank"] = sub["match_status"].map(status_rank)
    sub = sub.sort_values(["_rank", "book_vcf"]).drop(columns="_rank")
    display(sub[["book_vcf", "book_label", "match_status", "pilot_vars", "notes"]])
```

## Verdict (for extract decision)

```python
verdict = """
Local Pilots are useful enough to build a small separate extract — especially for
group feeling thermometers — without fetching older Pilots yet.

Strong overlaps
- Race/ethnicity FTs: Hispanics, Blacks, Whites, Asians (2022/2019/2018; 2016 lacks Asian FT)
- Feminists FT: 2022, 2016
- Muslims FT: 2019, 2018, 2016 (not 2022)
- Gays/lesbians FT: 2018, 2016 (not 2022)
- Illegal immigrants FT: 2019 ftillegal (best); 2022 only related salience/emotions
- Immigration volume: immignum (2019/2018), immig_numb (2016); 2022 has emotions only
- Hardworking–lazy 7-pt battery: 2022 swhwork/sblwork/slawork/saswork; 2016 has lazy* only

Clear misses (across local Pilots)
- Women's equal-role scale (VCF0834), women's movement FT (VCF0225)
- Religion FTs Protestants/Catholics/Jews/Christian fundamentalists
- Gay-rights policy battery (VCF0876–VCF0878)
- Foreign aid spending (VCF0892), immigration takes jobs (VCF9223)

Recommendation
1. Proceed with make_pilot_extract.py starting at 2022 (+ 2018/2019 thermometer/volume items).
2. Keep Pilot HDF separate from CDF; use for parallel / mode-sensitivity plots.
3. Defer 2006 and older Pilots until after that extract is in use.
"""
log_and_print(verdict)
print(verdict)
```

```python
debug_log.close()
print("Log: logs/eda_pilot_inventory.txt")
print("Crosswalk: ../data/processed/anes_pilot_cdf_crosswalk.csv")
print("Meta: ../data/processed/anes_pilot_study_meta.csv")
```
