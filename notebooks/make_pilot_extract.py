"""Build a separate ANES Pilot extract (HDF) for Task 10.

Stacks local Pilots (2022, 2019, 2018, 2016) with book-aligned columns where
overlap exists. Does **not** merge into the CDF extract.

Invoke: ``make run_pilot_extract`` or ``python make_pilot_extract.py``.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
import pyreadstat

from utils import log_and_print

ROOT = Path(__file__).resolve().parent.parent
PILOT_ROOT = ROOT / "data/raw/midterm_pilots"
DEFAULT_OUTPUT = ROOT / "data/interim/anes_pilot_extract.hdf"
DEFAULT_COMPRESSION = 6
debug_log = None  # set in run_extract for utils.log_and_print

# Survey year for each Pilot study folder.
PILOT_SPECS = {
    2022: {
        "path": PILOT_ROOT / "2022/anes_pilot_2022_stata_20221214.dta",
        "kind": "stata",
        "birthyr": "birthyr_dropdown",
        "sex": "gender",
        "race": None,  # no simple race profile var in 2022 skim
        "weight": "weight",
        # output_col -> source column(s); list = coalesce first non-null
        "map": {
            "VCF0217": "fthisp",
            "VCF0227": "ftasian",
            "VCF0206": ["ftblack1", "ftblack2"],
            "VCF0207": ["ftwhite1", "ftwhite2"],
            "VCF0253": "ftfem",
            "VCF9270": "swhwork",
            "VCF9271": "sblwork",
            "VCF9272": "slawork",
            "VCF9273": "saswork",
        },
    },
    2019: {
        "path": PILOT_ROOT / "2019/anes_pilot_2019.dta",
        "kind": "stata",
        "birthyr": "birthyr",
        "sex": "gender",
        "race": "race",
        "weight": "weight",
        "map": {
            "VCF0217": "fthisp",
            "VCF0227": "ftasian",
            "VCF0206": "ftblack",
            "VCF0207": "ftwhite",
            "VCF0233": "ftillegal",
            "VCF9267": "ftmuslim",
            "immig_volume": "immignum",  # 7-cat; related to VCF0879 but not identical
            "ft_immigrants": "ftimmig1",
            "ft_legal_immigrants": "ftimmig2",
        },
    },
    2018: {
        "path": PILOT_ROOT / "2018/anes_pilot_2018.dta",
        "kind": "stata",
        "birthyr": "birthyr",
        "sex": "gender",
        "race": "race",
        "weight": "weight",
        "map": {
            "VCF0217": "fthisp",
            "VCF0227": "ftasian",
            "VCF0206": "ftblack",
            "VCF0207": "ftwhite",
            "VCF0232": "ftgay",
            "VCF9267": "ftmuslim",
            "immig_volume": "immignum",
            "ft_immigrants": "ftimmig",
        },
    },
    2016: {
        "path": PILOT_ROOT / "2016/anes_pilot_2016.sav",
        "kind": "sav",
        "birthyr": "birthyr",
        "sex": "gender",
        "race": "race",
        "weight": "weight",
        "map": {
            "VCF0217": "fthisp",
            "VCF0206": "ftblack",
            "VCF0207": "ftwhite",
            "VCF0232": "ftgay",
            "VCF0253": "ftfem",
            "VCF9267": "ftmuslim",
            "immig_volume": "immig_numb",
            "lazy_whites": "lazyw",  # 5-pt lazy (not CDF 7-pt hardworking–lazy)
            "lazy_blacks": "lazyb",
            "lazy_hispanics": "lazyh",
        },
    },
}

THERMOMETER_COLS = [
    "VCF0206",
    "VCF0207",
    "VCF0217",
    "VCF0227",
    "VCF0232",
    "VCF0233",
    "VCF0253",
    "VCF9267",
    "ft_immigrants",
    "ft_legal_immigrants",
]

SCALE_COLS = [
    "VCF9270",
    "VCF9271",
    "VCF9272",
    "VCF9273",
    "immig_volume",
    "lazy_whites",
    "lazy_blacks",
    "lazy_hispanics",
]


def read_pilot(path: Path, kind: str, columns: list[str]) -> pd.DataFrame:
    cols = [c for c in columns if c]
    if kind == "stata":
        with pd.io.stata.StataReader(path) as reader:
            available = set(reader.variable_labels())
        use = [c for c in cols if c in available]
        missing = sorted(set(cols) - set(use))
        if missing:
            log_and_print(f"  Warning: missing columns in {path.name}: {missing}")
        return pd.read_stata(path, columns=use, convert_categoricals=False)
    df, _meta = pyreadstat.read_sav(path)
    use = [c for c in cols if c in df.columns]
    missing = sorted(set(cols) - set(use))
    if missing:
        log_and_print(f"  Warning: missing columns in {path.name}: {missing}")
    return df[use].copy()


def coalesce(df: pd.DataFrame, sources) -> pd.Series:
    if isinstance(sources, str):
        sources = [sources]
    out = pd.Series(np.nan, index=df.index, dtype=float)
    for col in sources:
        if col in df.columns:
            out = out.fillna(df[col])
    return out


def clean_thermometer(series: pd.Series) -> pd.Series:
    """Drop ANES Pilot missing / skip codes; keep 0–100."""
    s = pd.to_numeric(series, errors="coerce")
    return s.mask((s < 0) | (s > 100))


def clean_scale(series: pd.Series) -> pd.Series:
    """Drop negative / skip codes on Likert-type Pilot items."""
    s = pd.to_numeric(series, errors="coerce")
    return s.mask(s < 0)


def extract_one_year(year: int, spec: dict) -> pd.DataFrame | None:
    path = spec["path"]
    if not path.exists():
        log_and_print(f"  Skip {year}: missing {path}")
        return None

    needed = []
    for src in spec["map"].values():
        if isinstance(src, list):
            needed.extend(src)
        else:
            needed.append(src)
    for key in ("birthyr", "sex", "race", "weight"):
        if spec.get(key):
            needed.append(spec[key])

    log_and_print(f"\nReading Pilot {year}: {path.relative_to(ROOT)}")
    raw = read_pilot(path, spec["kind"], needed)
    log_and_print(f"  Raw rows: {len(raw):,}")

    out = pd.DataFrame(index=raw.index)
    out["year"] = float(year)
    out["pilot"] = year
    out["source"] = f"anes_pilot_{year}"

    birthyr = spec.get("birthyr")
    if birthyr and birthyr in raw.columns:
        by = pd.to_numeric(raw[birthyr], errors="coerce")
        by = by.mask(by < 0)
        out["birth_year"] = by
        out["age"] = year - by
        out["cohort"] = year - out["age"]  # same as CDF: year − age ≈ birth year

    sex_col = spec.get("sex")
    if sex_col and sex_col in raw.columns:
        sex = pd.to_numeric(raw[sex_col], errors="coerce")
        out["sex"] = sex.mask(sex < 0)

    race_col = spec.get("race")
    if race_col and race_col in raw.columns:
        race = pd.to_numeric(raw[race_col], errors="coerce")
        out["race"] = race.mask(race < 0)

    weight_col = spec.get("weight")
    if weight_col and weight_col in raw.columns:
        w = pd.to_numeric(raw[weight_col], errors="coerce")
        out["weight"] = w.mask(w <= 0)

    for out_col, src in spec["map"].items():
        series = coalesce(raw, src)
        if out_col in THERMOMETER_COLS:
            out[out_col] = clean_thermometer(series)
        else:
            out[out_col] = clean_scale(series)

    return out


def run_extract(
    output_file: Path | str = DEFAULT_OUTPUT,
    years: list[int] | None = None,
    compression_level: int = DEFAULT_COMPRESSION,
):
    global debug_log  # utils.log_and_print looks up caller/module debug_log
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    log_path = ROOT / "notebooks/logs/extract_pilot.txt"
    log_path.parent.mkdir(parents=True, exist_ok=True)

    years = years or sorted(PILOT_SPECS.keys(), reverse=True)

    debug_log = open(log_path, "w")
    try:
        log_and_print("ANES Pilot Extract Log")
        log_and_print("=" * 80)
        log_and_print("Script: make_pilot_extract.py")
        log_and_print(f"Output: {output_path}")
        log_and_print(f"Years: {years}")
        log_and_print(f"Started: {pd.Timestamp.now()}")
        log_and_print("=" * 80)

        frames = []
        for year in years:
            if year not in PILOT_SPECS:
                log_and_print(f"  Unknown year {year}; skip")
                continue
            frame = extract_one_year(year, PILOT_SPECS[year])
            if frame is not None:
                frames.append(frame)
                therm_present = [c for c in THERMOMETER_COLS if c in frame.columns]
                n_therm = frame[therm_present].notna().any(axis=1).sum() if therm_present else 0
                log_and_print(
                    f"  Kept {len(frame):,} rows; any thermometer non-null: {n_therm:,}"
                )

        if not frames:
            raise SystemExit("No Pilot years loaded")

        anes = pd.concat(frames, ignore_index=True, sort=False)
        front = [
            "year",
            "pilot",
            "source",
            "weight",
            "age",
            "birth_year",
            "cohort",
            "sex",
            "race",
        ]
        rest = [c for c in anes.columns if c not in front]
        anes = anes[[c for c in front if c in anes.columns] + sorted(rest)]

        log_and_print("\nStacked extract:")
        log_and_print(f"  Shape: {anes.shape[0]} rows × {anes.shape[1]} columns")
        log_and_print(
            f"  Years: {sorted(int(y) for y in anes['year'].dropna().unique())}"
        )
        log_and_print(anes.groupby("year").size().to_string())

        if output_path.exists():
            output_path.unlink()
            log_and_print(f"\nRemoved existing {output_path}")

        log_and_print(f"\nWriting {output_path}...")
        anes.to_hdf(output_path, key="anes", complevel=compression_level)

        labels_path = output_path.with_name(output_path.stem + "_labels.csv")
        label_rows = []
        for year in sorted(int(y) for y in anes["year"].dropna().unique()):
            spec = PILOT_SPECS[year]
            for out_col, src in spec["map"].items():
                src_s = "; ".join(src) if isinstance(src, list) else src
                label_rows.append(
                    {
                        "year": year,
                        "extract_column": out_col,
                        "pilot_source": src_s,
                        "kind": (
                            "thermometer"
                            if out_col in THERMOMETER_COLS
                            else "scale"
                        ),
                    }
                )
        pd.DataFrame(label_rows).to_csv(labels_path, index=False)
        log_and_print(f"  Saved column map: {labels_path}")
        log_and_print(
            f"  File size: {output_path.stat().st_size / (1024 * 1024):.2f} MB"
        )
        log_and_print(f"\n✓ Pilot extract complete: {output_path}")
        log_and_print(f"Completed: {pd.Timestamp.now()}")
    finally:
        debug_log.close()
        debug_log = None

    print(f"Log file: {log_path}")
    return anes


def main():
    parser = argparse.ArgumentParser(description="Build ANES Pilot extract HDF.")
    parser.add_argument(
        "--output",
        default=str(DEFAULT_OUTPUT),
        help="Output HDF path",
    )
    parser.add_argument(
        "--years",
        nargs="*",
        type=int,
        default=None,
        help="Pilot years to include (default: all local)",
    )
    parser.add_argument(
        "--compression",
        type=int,
        default=DEFAULT_COMPRESSION,
    )
    args = parser.parse_args()
    run_extract(
        output_file=args.output,
        years=args.years,
        compression_level=args.compression,
    )


if __name__ == "__main__":
    main()
