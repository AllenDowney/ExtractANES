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

# Extract ANES Time Series CDF

Allen Downey

[MIT License](https://en.wikipedia.org/wiki/MIT_License)

This notebook runs the extract script (`make_cdf_extract.py`). **Source of truth:** `notebooks/make_cdf_extract.py` (also invoked by `make run_extract`).

```python tags=["parameters"]
INPUT_FILE = "../data/raw/anes_timeseries_cdf_stata_20260205.dta.gz"
COMPRESSION_LEVEL = 6
GIT_COMMIT = False

input_stem = __import__("pathlib").Path(INPUT_FILE).name.replace(".dta.gz", "")
OUTPUT_FILE = f"../data/interim/anes_extract_{input_stem}.hdf"
```

```python
from make_cdf_extract import run_extract

anes = run_extract(
    input_file=INPUT_FILE,
    output_file=OUTPUT_FILE,
    compression_level=COMPRESSION_LEVEL,
    git_commit=GIT_COMMIT,
)
anes[["year", "age", "cohort", "sex", "VCF0103", "race", "polviews"]].head()
```
