import inspect
import json
import re
from pathlib import Path

import numpy as np

CATALOG_PATH = Path(__file__).resolve().parent.parent / "codebook/extracted/anes_cdf_minimal.json"

_DK_NA_LABEL_RE = re.compile(r"\b(DK|RF|INAP)\b|(?:^|[.;,\s])NA(?:;|,|$|\s)", re.IGNORECASE)

# Map renamed extract columns to CDF variable names (see make_cdf_extract.py).
CORE_VCF_COLUMNS = {
    "age": "VCF0101",
    "sex": "VCF0104",
    "race": "VCF0106",
    "race_eth": "VCF0105a",
    "hispanic": "VCF0108",
    "hispanic_type": "VCF0107",
    "polviews": "VCF0803",
    "weight": "VCF0009z",
}


def log_and_print(message, log_file=None):
    """Write message to debug log and print to notebook."""
    if log_file is None:
        frame = inspect.currentframe()
        try:
            caller_globals = frame.f_back.f_globals
            log_file = caller_globals.get("debug_log", None)
        finally:
            del frame

    if log_file:
        log_file.write(message + "\n")
        log_file.flush()

    print(message)


def load_cdf_catalog(path=None):
    """Load cached ANES CDF metadata (see codebook/extract_cdf_codebook.py)."""
    path = CATALOG_PATH if path is None else Path(path)
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def catalog_entry(vcf_var, catalog):
    """Return catalog entry for a VCF variable (case-insensitive fallback)."""
    return catalog.get(vcf_var) or catalog.get(vcf_var.upper(), {})


def dk_codes_from_value_labels(entry):
    """Numeric codes whose Stata value label indicates DK/NA/RF/INAP.

    Handles negative missing codes (e.g. ``[-8]``, ``[-9]``). Skips labels that
    begin with a substantive Yes/No (avoids false positives like
    ``Yes, Hispanic but DK/NA type``).
    """
    value_labels = entry.get("value_labels", "")
    if not value_labels:
        return []
    codes = []
    for part in value_labels.split(" / "):
        match = re.match(r"\[(-?\d+)\]\s*(.*)", part.strip())
        if not match:
            continue
        label = match.group(2)
        if re.match(r"(?i)^\d*\.?\s*(Yes|No)\b", label):
            continue
        if _DK_NA_LABEL_RE.search(label):
            codes.append(int(match.group(1)))
    return codes


def missing_codes_for_var(vcf_var, catalog=None, include_dk_labels=True):
    """Missing-data codes for a CDF variable from the catalog."""
    catalog = catalog or load_cdf_catalog()
    entry = catalog_entry(vcf_var, catalog)
    codes = list(entry.get("missing_codes", []))
    if include_dk_labels:
        for code in dk_codes_from_value_labels(entry):
            if code not in codes:
                codes.append(code)
    return sorted(codes)


def recode_values_to_nan(series, codes, drop_negatives=False):
    """Replace listed codes with NaN; return count recoded.

    If *drop_negatives* is True, also set values ``< 0`` to NaN (ANES modern
    RF/DK/INAP convention, e.g. ``-8``, ``-9``).
    """
    mask = series.isin(codes)
    if drop_negatives:
        mask = mask | (series.notna() & (series < 0))
    n = int(mask.sum())
    if n:
        series = series.mask(mask)
    return series, n


def recode_thermometer(series, vcf_var=None, catalog=None):
    """Recode ANES feeling-thermometer missing values to NaN.

    Uses catalog missing_codes when *vcf_var* is given; always drops
    negative values and codes above 100 (harmonized candidate-slot codes).
    """
    catalog = catalog or load_cdf_catalog()
    codes = missing_codes_for_var(vcf_var, catalog) if vcf_var else [98, 99]
    mask = series.notna() & ((series < 0) | series.isin(codes) | (series > 100))
    n = int(mask.sum())
    if n:
        series = series.mask(mask)
    return series, n


def recode_core_variables(df, column_to_vcf=None, catalog=None):
    """Apply codebook missing codes to renamed core columns."""
    column_to_vcf = column_to_vcf or CORE_VCF_COLUMNS
    catalog = catalog or load_cdf_catalog()
    counts = {}
    for col, vcf_var in column_to_vcf.items():
        if col not in df.columns:
            continue
        codes = missing_codes_for_var(vcf_var, catalog)
        if col == "weight" and not codes:
            # Continuous weight; zero is non-substantive (not in HTML Missing section).
            mask = df[col].notna() & (df[col] <= 0)
            n = int(mask.sum())
            if n:
                df[col] = df[col].mask(mask)
            counts[col] = n
            continue
        # Always drop negatives (modern ANES RF/DK codes may be absent from labels).
        df[col], counts[col] = recode_values_to_nan(
            df[col], codes, drop_negatives=True
        )
    return counts


def recode_thermometer_columns(df, columns, catalog=None):
    """Apply thermometer missing-code rules to VCF thermometer columns."""
    counts = {}
    for col in columns:
        if col in df.columns:
            df[col], counts[col] = recode_thermometer(df[col], vcf_var=col, catalog=catalog)
    return counts


def recode_vcf_columns(df, vcf_columns, catalog=None):
    """Apply catalog missing codes to CDF columns kept under VCF names.

    Also drops negative values (ANES ``-8``/``-9``/``-1`` RF/DK/INAP convention).
    """
    catalog = catalog or load_cdf_catalog()
    counts = {}
    for col in vcf_columns:
        if col not in df.columns:
            continue
        codes = missing_codes_for_var(col, catalog)
        df[col], counts[col] = recode_values_to_nan(
            df[col], codes, drop_negatives=True
        )
    return counts


def harmonize_vcf0878_adopt(df):
    """Harmonize VCF0878 oppose code: 5=no (1992–2020) → 2=no (2024 native coding).

    ANES switched from code 5 to code 2 for *no* in 2024 only; earlier waves keep 5.
    Returns count of values recoded 5→2.
    """
    col = "VCF0878"
    if col not in df.columns:
        return 0
    mask = df[col] == 5
    n = int(mask.sum())
    if n:
        df.loc[mask, col] = 2
    return n
