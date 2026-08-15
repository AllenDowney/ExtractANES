# ANES CDF Codebook Documentation Plan

## Overview

Variable metadata for the ANES Time Series Cumulative Data File is extracted once from the HTML codebook and Stata file headers, then cached under `codebook/extracted/` for use in notebooks.

## Sources

| Source | Path | Provides |
|--------|------|----------|
| HTML codebook | `codebook/ANES TIME SERIES CUMULATIVE DATA FILE 1948-2024 VARIABLE CODEBOOK.html` | Question text, valid/missing codes, notes, sources (years) |
| Stata CDF | `data/raw/anes_timeseries_cdf_stata_20260205.dta.gz` | Authoritative variable list, short labels, value labels |

## Extraction

```bash
conda activate ExtractANES
make extract_codebook
# or: python codebook/extract_cdf_codebook.py
```

## Extracted outputs

| File | Role |
|------|------|
| **`anes_cdf_minimal.json`** | Primary lookup — GSS-compatible schema (variable, label, question, value_labels, missing_codes, valid_range, years_available, notes) |
| `anes_cdf_dict.json` | Full metadata including raw HTML sections and structured value_labels_dict |
| `anes_cdf_summary.csv` | Quick index for grep/spreadsheet review |

## Schema (minimal entry)

```json
{
  "VCF0101": {
    "variable": "VCF0101",
    "label": "Respondent - Age",
    "question": "1964-1976: What is your date of birth? ...",
    "value_labels": "[0] NA; DK; RF; no Pre IW / [1] ...",
    "missing_codes": [0],
    "valid_range": "17-99",
    "years_available": "1952, 1956, 1958, ...",
    "notes": "GENERAL NOTE: Prior to 1964 ..."
  }
}
```

Designed to mirror `~/CultureWar/codebook/extracted/gssrdoc_minimal.json` for cross-project compatibility.

## Integration

- `notebooks/utils.py`: `load_cdf_catalog()`, `missing_codes_for_var()` — used by `recode_core_variables`, `recode_thermometer_columns`, and `recode_vcf_columns`
- `notebooks/make_cdf_extract.md`: loads catalog at recode time; maps core columns via `CORE_VCF_COLUMNS`
- **`codebook/extract_notes.md`**: project harmonization decisions and analysis caveats (complements catalog `notes`)
