"""Build the ANES Time Series CDF extract (HDF + variable labels).

Source of truth for extract logic; invoked by ``make run_extract``.
"""

from __future__ import annotations

import argparse
import os
import re
import warnings
from pathlib import Path

import pandas as pd

from utils import (
    load_cdf_catalog,
    log_and_print,
    harmonize_vcf0878_adopt,
    recode_core_variables,
    recode_thermometer_columns,
    recode_vcf_columns,
)

MIN_THERMOMETER_YEARS = 6

DEFAULT_INPUT = "../data/raw/anes_timeseries_cdf_stata_20260205.dta.gz"
DEFAULT_COMPRESSION_LEVEL = 6

ID_COLUMNS = [
    "VCF0006",  # Study respondent number (year-level case ID)
    "VCF0006a",  # Cross-year respondent ID
]

# Renamed on output (VCF0103 kept under its CDF name; see VCF_PASSTHROUGH_COLUMNS).
CORE_COLUMNS = {
    "VCF0004": "year",
    "VCF0101": "age",
    "VCF0104": "sex",
    "VCF0106": "race",
    "VCF0105a": "race_eth",
    "VCF0108": "hispanic",  # Task 9: Hispanic origin yes/no
    "VCF0107": "hispanic_type",  # Task 9: Hispanic origin type
    "VCF0803": "polviews",
}

WEIGHT_COLUMN = "VCF0009z"

# CDF columns kept under VCF names (missing codes from catalog).
VCF_PASSTHROUGH_COLUMNS = [
    "VCF0103",  # ANES birth-era bins (1–8); not used as extract cohort
]

ATTITUDE_COLUMNS = [
    # Task 6: women's role / equal-rights attitudes
    "VCF0834",  # Women equal role scale
    "VCF9014",  # Gone too far pushing equal rights
    "VCF9017",  # Better off worrying less about equality
    # Task 8: LGBT rights / anti-discrimination
    "VCF0876",  # Job-discrimination protection (favor/oppose)
    "VCF0876a",  # Strength of position on job-discrimination law
    "VCF0877",  # Gays in the military (allow / not allow)
    "VCF0877a",  # Strength of position on military service
    "VCF0878",  # Gay/lesbian couples permitted to adopt
    # Task 9: immigration volume / threat / stereotypes / foreign aid
    "VCF0879",  # Increase/decrease immigrants (6-category)
    "VCF0879a",  # Increase/decrease immigrants (4-category)
    "VCF9223",  # Immigration levels take jobs
    "VCF9270",  # Hardworking–lazy: whites
    "VCF9271",  # Hardworking–lazy: blacks
    "VCF9272",  # Hardworking–lazy: Hispanic-Americans
    "VCF9273",  # Hardworking–lazy: Asian-Americans
    "VCF0892",  # Federal spending: foreign aid
]


def keep_thermometer(name, label, preview):
    """Drop derived indices, named candidates, office slots, and rare thermometers."""
    if "Average" in label or "Index" in label:
        return False, "derived index/average"
    if re.match(r"VCF04(3[2-9]|4[0-9]|7[1-3])", name):
        return False, "named candidate"
    if re.search(r"Challenger|Candidate|Incumbent", label, re.IGNORECASE):
        return False, "candidate/challenger/incumbent slot"
    if re.search(r"Senator|Jesse Jackson", label, re.IGNORECASE):
        return False, "senator or Jesse Jackson"
    n_years = preview.loc[preview[name].notna(), "year"].nunique()
    if n_years < MIN_THERMOMETER_YEARS:
        return False, f"asked in {n_years} years"
    return True, f"asked in {n_years} years"


def select_thermometer_columns(input_file):
    """Return kept thermometer VCF names, exclusion log, and Stata variable labels."""
    with pd.io.stata.StataReader(input_file) as reader:
        variable_labels = reader.variable_labels()

    all_thermometer_columns = sorted(
        name for name, label in variable_labels.items() if "Thermometer" in label
    )

    preview_columns = ["VCF0004"] + all_thermometer_columns
    preview = pd.read_stata(input_file, columns=preview_columns, convert_categoricals=False)
    preview = preview.rename(columns={"VCF0004": "year"})

    thermometer_columns = []
    excluded_thermometers = []
    for name in all_thermometer_columns:
        keep, reason = keep_thermometer(name, variable_labels[name], preview)
        if keep:
            thermometer_columns.append(name)
        else:
            excluded_thermometers.append((name, variable_labels[name], reason))

    return sorted(thermometer_columns), excluded_thermometers, variable_labels


def run_extract(
    input_file=DEFAULT_INPUT,
    output_file=None,
    compression_level=DEFAULT_COMPRESSION_LEVEL,
    git_commit=False,
    log_path=None,
):
    """Read CDF Stata file, build extract, write HDF and labels CSV."""
    input_path = Path(input_file)
    input_stem = input_path.name.replace(".dta.gz", "")
    if output_file is None:
        output_file = f"../data/interim/anes_extract_{input_stem}.hdf"
    output_path = Path(output_file)

    os.makedirs("logs", exist_ok=True)
    os.makedirs(output_path.parent, exist_ok=True)

    if log_path is None:
        log_path = f"logs/extract_{input_stem}.txt"

    with open(log_path, "w") as debug_log:

        def log(msg):
            log_and_print(msg, log_file=debug_log)

        log("ANES CDF Extract Log")
        log("=" * 80)
        log("Script: make_cdf_extract.py")
        log(f"Input: {input_file}")
        log(f"Output: {output_file}")
        log(f"Started: {pd.Timestamp.now()}")
        log("=" * 80 + "\n")

        log("Configuration:")
        log(f"  Input file: {input_file}")
        log(f"  Output file: {output_file}")

        thermometer_columns, excluded_thermometers, variable_labels = select_thermometer_columns(
            input_file
        )

        desired_columns = (
            ID_COLUMNS
            + list(CORE_COLUMNS.keys())
            + [WEIGHT_COLUMN]
            + VCF_PASSTHROUGH_COLUMNS
            + ATTITUDE_COLUMNS
            + thermometer_columns
        )

        log("\nColumn selection:")
        log(f"  ID columns: {len(ID_COLUMNS)}")
        log(f"  Core columns: {len(CORE_COLUMNS)}")
        log(f"  VCF passthrough: {len(VCF_PASSTHROUGH_COLUMNS)}")
        log(f"  Weight column: 1")
        log(f"  Attitude columns: {len(ATTITUDE_COLUMNS)}")
        log(f"  Thermometer columns kept: {len(thermometer_columns)}")
        log(f"  Thermometer columns excluded: {len(excluded_thermometers)}")
        log(f"  Total desired: {len(desired_columns)}")
        log("\nExcluded thermometers:")
        for name, label, reason in excluded_thermometers:
            log(f"  {name} ({reason}): {label}")

        log(f"\nReading data from {input_file}...")
        anes = pd.read_stata(input_file, convert_categoricals=False)

        available_columns = [col for col in desired_columns if col in anes.columns]
        missing_columns = [col for col in desired_columns if col not in anes.columns]

        if missing_columns:
            warnings.warn(f"Missing columns: {missing_columns}")
            log(f"  Warning: Missing {len(missing_columns)} columns: {missing_columns}")

        log(f"  Read {len(anes)} rows, {len(anes.columns)} total columns in file")
        log(f"  Selected {len(available_columns)} columns from desired set")

        anes = anes[available_columns].copy()
        anes.rename(columns=CORE_COLUMNS, inplace=True)
        anes.rename(columns={WEIGHT_COLUMN: "weight"}, inplace=True)

        catalog = load_cdf_catalog()
        log(f"\nRecoding missing values to NaN (catalog: {len(catalog)} variables)...")
        core_counts = recode_core_variables(anes, catalog=catalog)
        for col, n in core_counts.items():
            log(f"  {col}: recoded {n:,} values")

        vcf_passthrough = [c for c in VCF_PASSTHROUGH_COLUMNS if c in anes.columns]
        vcf_counts = recode_vcf_columns(anes, vcf_passthrough, catalog=catalog)
        for col, n in vcf_counts.items():
            log(f"  {col}: recoded {n:,} values")

        therm_counts = recode_thermometer_columns(anes, thermometer_columns, catalog=catalog)
        therm_recoded = sum(therm_counts.values())
        log(
            f"  thermometers: recoded {therm_recoded:,} values "
            f"across {len(therm_counts)} columns"
        )
        top_therm = sorted(therm_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        for col, n in top_therm:
            if n:
                log(f"    {col}: {n:,}")

        attitude_counts = recode_vcf_columns(anes, ATTITUDE_COLUMNS, catalog=catalog)
        for col, n in attitude_counts.items():
            log(f"  {col}: recoded {n:,} values")

        n_0878 = harmonize_vcf0878_adopt(anes)
        if n_0878:
            log(f"  VCF0878: harmonized {n_0878:,} values (5=no → 2=no on pre-2024 waves)")

        if "year" in anes.columns and "age" in anes.columns:
            anes["cohort"] = anes["year"] - anes["age"]
            log("\nDerived cohort = year - age (approximate birth year)")
            log(
                f"  cohort range: {anes['cohort'].min():.0f} to {anes['cohort'].max():.0f}"
            )
        else:
            warnings.warn("Could not derive cohort: missing year or age")

        log("\nData summary:")
        log(f"  Shape: {anes.shape[0]} rows × {anes.shape[1]} columns")
        log(f"  Years: {anes['year'].min():.0f} to {anes['year'].max():.0f}")
        log(f"  Thermometer columns retained: {len(thermometer_columns)}")

        if output_path.exists():
            output_path.unlink()
            log(f"\nRemoved existing output file: {output_file}")

        log(f"\nWriting output to {output_file}...")
        anes.to_hdf(output_path, key="anes", complevel=compression_level)

        labels_path = output_path.with_name(output_path.stem + "_labels.csv")
        vcf_label_columns = (
            VCF_PASSTHROUGH_COLUMNS + ATTITUDE_COLUMNS + thermometer_columns
        )
        variable_label_rows = pd.DataFrame(
            {
                "variable": vcf_label_columns,
                "label": [variable_labels[c] for c in vcf_label_columns],
            }
        )
        variable_label_rows.to_csv(labels_path, index=False)
        log(f"  Saved variable labels: {labels_path}")

        file_size = output_path.stat().st_size / (1024 * 1024)
        log(f"  Output file size: {file_size:.2f} MB")
        log(f"  Final dataset: {anes.shape[0]} rows × {anes.shape[1]} columns")

        if git_commit:
            log("\nGit operations (git_commit=True)...")
            os.system(f"git add -f {output_file}")
            os.system(f'git commit -m "Updating ANES extract: {output_file}"')
            os.system("git push")
            log("  Git commit and push complete")
        else:
            log("\nGit operations disabled (git_commit=False)")

        log(f"\n✓ Extract complete: {output_file}")
        log(f"\nCompleted: {pd.Timestamp.now()}")

    print(f"Log file: {log_path}")
    return anes


def main():
    parser = argparse.ArgumentParser(description="Build ANES CDF extract HDF.")
    parser.add_argument(
        "--input",
        default=DEFAULT_INPUT,
        help=f"Path to CDF Stata file (default: {DEFAULT_INPUT})",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Output HDF path (default: ../data/interim/anes_extract_<stem>.hdf)",
    )
    parser.add_argument(
        "--compression",
        type=int,
        default=DEFAULT_COMPRESSION_LEVEL,
        help=f"HDF compression level (default: {DEFAULT_COMPRESSION_LEVEL})",
    )
    parser.add_argument(
        "--git-commit",
        action="store_true",
        help="Commit and push output HDF after writing",
    )
    parser.add_argument(
        "--log",
        default=None,
        help="Log file path (default: logs/extract_<stem>.txt)",
    )
    args = parser.parse_args()

    run_extract(
        input_file=args.input,
        output_file=args.output,
        compression_level=args.compression,
        git_commit=args.git_commit,
        log_path=args.log,
    )


if __name__ == "__main__":
    main()
