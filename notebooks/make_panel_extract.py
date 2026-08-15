"""Build a separate ANES 2016–2020–2024 panel extract (HDF) for Task 11.

Reshapes the wide merged panel file to long (one row per respondent × wave).
Does **not** merge into the CDF or Pilot extracts.

Invoke: ``make run_panel_extract`` or ``python make_panel_extract.py``.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
import pyreadstat

from utils import log_and_print

ROOT = Path(__file__).resolve().parent.parent
PANEL_ROOT = ROOT / "data/raw/panel_2016_2020_2024"
DEFAULT_SAV = PANEL_ROOT / "anes_mergedfile_2016-2020-2024panel_20260519.sav"
DEFAULT_OUTPUT = ROOT / "data/interim/anes_panel_extract.hdf"
DEFAULT_COMPRESSION = 6
debug_log = None

# Per-wave source columns. Outcome keys are extract names (book VCF where matched).
# None = not asked that wave.
WAVE_SPECS = {
    2016: {
        "caseid": "V160001",
        "weight": "V160102",  # post full-sample (no 2016-only panel weight)
        "age": "V161267",
        "birth_year": "V161267c",
        "sex": "V161342",
        "race": "V161310x",
        "map": {
            # Feeling thermometers (book VCFs)
            "VCF0206": "V162312",  # Blacks
            "VCF0207": "V162314",  # Whites
            "VCF0217": "V162311",  # Hispanics
            "VCF0227": "V162310",  # Asian-Americans
            "VCF0232": "V162103",  # Gay men and lesbians
            "VCF0233": "V162313",  # Illegal immigrants
            "VCF0253": "V162096",  # Feminists
            "VCF0205": "V162108",  # Jews
            "VCF9267": "V162106",  # Muslims
            "VCF0234": "V162095",  # Christian fundamentalists
            # Immigration / stereotypes / gay policy
            "VCF0879": "V162157",  # immigration levels
            "VCF9223": "V162158",  # takes jobs
            "VCF9270": "V162345",  # hardworking–lazy Whites
            "VCF9271": "V162346",  # Blacks
            "VCF9273": "V162348",  # Asian-Americans
            "VCF0876": "V161229",  # gay job discrimination
            "VCF0876a": "V161229a",
            "VCF0878": "V161230",  # gay/lesbian adopt
            "gay_marriage": "V161231",
            "immig_unauthorized": "V161192",
            # Transgender (panel-era; not CDF book VCFs)
            "ft_transgender": "V162111",
            "trans_bathroom": "V161228",
            "trans_bathroom_str": "V161228a",
            "trans_bathroom_sum": "V161228x",
            "trans_discrim": "V162366",
            "VCF9272": None,  # Hispanics HW: 2020+
            "trans_military": None,
            "trans_military_str": None,
            "trans_military_sum": None,
            "trans_sports_ban": None,
            "trans_know_someone": None,
            "border_security": None,
        },
    },
    2020: {
        "caseid": "V200001",
        "weight": "V200011b",  # 2016–2020 panel post weight
        "age": "V201507x",
        "birth_year": "V201506",
        "sex": "V201600",
        "race": "V201549x",
        "map": {
            "VCF0206": "V202480",
            "VCF0207": "V202482",
            "VCF0217": "V202479",
            "VCF0227": "V202477",
            "VCF0232": "V202166",
            "VCF0233": "V202481",
            "VCF0253": "V202160",
            "VCF0205": "V202170",
            "VCF9267": "V202168",
            "VCF0234": "V202159",
            "VCF0879": "V202232",
            "VCF9223": "V202233",
            "VCF9270": "V202515",
            "VCF9271": "V202516",
            "VCF9272": "V202518",
            "VCF9273": "V202519",
            "VCF0876": "V201412",
            "VCF0876a": "V201413",
            "VCF0878": "V201415",
            "gay_marriage": "V201416",
            "immig_unauthorized": "V201417",
            "border_security": "V201306",
            "ft_transgender": "V202172",
            "trans_bathroom": "V201409",
            "trans_bathroom_str": "V201410",
            "trans_bathroom_sum": "V201411x",
            "trans_military": "V202388",
            "trans_military_str": "V202389",
            "trans_military_sum": "V202390x",
            "trans_discrim": "V202536",
            "trans_know_someone": "V202473",
            "trans_sports_ban": None,
        },
    },
    2024: {
        "caseid": "V240001",
        "weight": "V240106b",  # 2016–2024 panel post weight
        "age": "V241458x",
        "birth_year": "V241455",
        "sex": "V241551",
        "race": "V241501x",
        "map": {
            "VCF0206": "V242516",
            "VCF0207": "V242518",
            "VCF0217": "V242515",
            "VCF0227": "V242514",
            "VCF0232": "V242144",
            "VCF0233": "V242517",
            "VCF0253": "V242138",
            "VCF0205": "V242149",
            "VCF9267": "V242146",
            "VCF0234": "V242137",
            "VCF0879": "V242227",
            "VCF9223": "V242228",
            "VCF9270": "V242541",
            "VCF9271": "V242542",
            "VCF9272": "V242543",
            "VCF9273": "V242544",
            "VCF0876": "V241376",
            "VCF0876a": "V241377",
            "VCF0878": "V241379",
            "gay_marriage": "V241382",
            "immig_unauthorized": "V241386",
            "border_security": "V241267",
            "ft_transgender": "V242151",
            "trans_bathroom": "V241370",
            "trans_bathroom_str": "V241371",
            "trans_bathroom_sum": "V241372x",
            "trans_military": "V242362",
            "trans_military_str": "V242363",
            "trans_military_sum": "V242364x",
            "trans_discrim": "V242558",
            "trans_know_someone": "V242510",
            "trans_sports_ban": "V241373",  # 2024+ (not in ANES repeated list)
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
    "VCF0205",
    "VCF9267",
    "VCF0234",
    "ft_transgender",
]


def clean_thermometer(series: pd.Series) -> pd.Series:
    s = pd.to_numeric(series, errors="coerce")
    return s.mask((s < 0) | (s > 100))


def clean_scale(series: pd.Series) -> pd.Series:
    s = pd.to_numeric(series, errors="coerce")
    return s.mask(s < 0)


def harmonize_trans_bathroom_restrict(raw: pd.Series, year: int) -> pd.Series:
    """Fixed-meaning binary: 1 = restrictive, 0 = inclusive, NaN = neither/missing.

    2016/2020 forced choice: 1 = birth-gender bathroom, 2 = identity bathroom.
    2024 favor/oppose allow identity bathrooms: 1 = favor, 2 = oppose, 3 = neither.
    See codebook/anes_pilot_panel_harmonization.md (H1).
    """
    s = pd.to_numeric(raw, errors="coerce")
    s = s.mask(s < 0)
    out = pd.Series(np.nan, index=s.index, dtype=float)
    if year in (2016, 2020):
        out = out.mask(s == 1, 1.0)
        out = out.mask(s == 2, 0.0)
    elif year == 2024:
        out = out.mask(s == 2, 1.0)  # oppose allowing → restrictive
        out = out.mask(s == 1, 0.0)  # favor allowing → inclusive
        # code 3 (neither) stays NaN
    else:
        raise ValueError(f"No bathroom harmonization for year {year}")
    return out


def all_source_columns() -> list[str]:
    cols = set()
    for spec in WAVE_SPECS.values():
        for key in ("caseid", "weight", "age", "birth_year", "sex", "race"):
            cols.add(spec[key])
        for src in spec["map"].values():
            if src:
                cols.add(src)
    return sorted(cols)


def extract_wave(raw: pd.DataFrame, year: int, panel_id: pd.Series) -> pd.DataFrame:
    spec = WAVE_SPECS[year]
    out = pd.DataFrame({"panel_id": panel_id.values})
    out["year"] = float(year)
    out["source"] = "anes_panel_2016_2020_2024"
    out["caseid"] = pd.to_numeric(raw[spec["caseid"]], errors="coerce")

    w = pd.to_numeric(raw[spec["weight"]], errors="coerce")
    out["weight"] = w.mask(w <= 0)

    age = pd.to_numeric(raw[spec["age"]], errors="coerce")
    out["age"] = age.mask(age < 0)

    by = pd.to_numeric(raw[spec["birth_year"]], errors="coerce")
    by = by.mask(by < 0)
    # Prefer reported birth year; else year − age
    out["birth_year"] = by.fillna(year - out["age"])
    out["cohort"] = year - out["age"]

    sex = pd.to_numeric(raw[spec["sex"]], errors="coerce")
    out["sex"] = sex.mask(sex < 0)

    race = pd.to_numeric(raw[spec["race"]], errors="coerce")
    out["race"] = race.mask(race < 0)

    for out_col, src in spec["map"].items():
        if not src or src not in raw.columns:
            out[out_col] = np.nan
            continue
        series = raw[src]
        if out_col in THERMOMETER_COLS:
            out[out_col] = clean_thermometer(series)
        else:
            out[out_col] = clean_scale(series)

    # H1: cross-wave fixed polarity (keep raw trans_bathroom*)
    out["trans_bathroom_restrict"] = harmonize_trans_bathroom_restrict(
        out["trans_bathroom"], year
    )

    return out


def run_extract(
    sav_path: Path | str = DEFAULT_SAV,
    output_file: Path | str = DEFAULT_OUTPUT,
    compression_level: int = DEFAULT_COMPRESSION,
):
    global debug_log
    sav_path = Path(sav_path)
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    log_path = ROOT / "notebooks/logs/extract_panel.txt"
    log_path.parent.mkdir(parents=True, exist_ok=True)

    debug_log = open(log_path, "w")
    try:
        log_and_print("ANES 2016–2020–2024 Panel Extract Log")
        log_and_print("=" * 80)
        log_and_print("Script: make_panel_extract.py")
        log_and_print(f"Input: {sav_path}")
        log_and_print(f"Output: {output_path}")
        log_and_print(f"Started: {pd.Timestamp.now()}")
        log_and_print("=" * 80)

        if not sav_path.exists():
            raise SystemExit(f"Missing panel file: {sav_path}")

        usecols = all_source_columns()
        log_and_print(f"\nReading {len(usecols)} columns from SAV...")
        raw, meta = pyreadstat.read_sav(str(sav_path), usecols=usecols)
        log_and_print(f"  Wide rows: {len(raw):,}  (meta n={meta.number_rows})")

        panel_id = pd.Series(np.arange(len(raw)), name="panel_id")
        frames = [extract_wave(raw, year, panel_id) for year in sorted(WAVE_SPECS)]
        anes = pd.concat(frames, ignore_index=True)

        front = [
            "panel_id",
            "year",
            "source",
            "caseid",
            "weight",
            "age",
            "birth_year",
            "cohort",
            "sex",
            "race",
        ]
        rest = sorted(c for c in anes.columns if c not in front)
        anes = anes[front + rest]

        log_and_print("\nLong extract:")
        log_and_print(f"  Shape: {anes.shape[0]} rows × {anes.shape[1]} columns")
        log_and_print(anes.groupby("year").size().to_string())
        log_and_print("\n  Weight non-null by year:")
        log_and_print(anes.groupby("year")["weight"].apply(lambda s: s.notna().sum()).to_string())
        if "ft_transgender" in anes.columns:
            log_and_print("\n  ft_transgender non-null by year:")
            log_and_print(
                anes.groupby("year")["ft_transgender"]
                .apply(lambda s: s.notna().sum())
                .to_string()
            )
        if "trans_bathroom_restrict" in anes.columns:
            log_and_print("\n  trans_bathroom_restrict (1=restrictive) by year:")
            for y, g in anes.groupby("year"):
                vc = g["trans_bathroom_restrict"].value_counts(dropna=False).sort_index()
                log_and_print(f"    {int(y)}: {vc.to_dict()}")

        if output_path.exists():
            output_path.unlink()
            log_and_print(f"\nRemoved existing {output_path}")

        log_and_print(f"\nWriting {output_path}...")
        anes.to_hdf(output_path, key="anes", complevel=compression_level)

        # Column map for documentation
        label_rows = []
        for year, spec in WAVE_SPECS.items():
            for out_col, src in spec["map"].items():
                kind = "thermometer" if out_col in THERMOMETER_COLS else "scale"
                note = ""
                if out_col == "trans_bathroom_sum":
                    note = (
                        "Audit only across waves (H2): polarity/levels change; "
                        "use trans_bathroom_restrict for book series"
                    )
                label_rows.append(
                    {
                        "year": year,
                        "extract_column": out_col,
                        "panel_source": src or "",
                        "kind": kind,
                        "notes": note,
                    }
                )
            # H1 derived
            src = spec["map"].get("trans_bathroom") or ""
            if year in (2016, 2020):
                mapping = "raw 1→1 restrictive, 2→0 inclusive"
            else:
                mapping = "raw 2→1 restrictive, 1→0 inclusive, 3→NaN"
            label_rows.append(
                {
                    "year": year,
                    "extract_column": "trans_bathroom_restrict",
                    "panel_source": f"derived from {src}" if src else "derived",
                    "kind": "derived_binary",
                    "notes": (
                        f"H1 fixed meaning: 1=restrictive, 0=inclusive; {mapping}"
                    ),
                }
            )
        labels_path = output_path.with_name(output_path.stem + "_labels.csv")
        pd.DataFrame(label_rows).to_csv(labels_path, index=False)
        log_and_print(f"  Saved column map: {labels_path}")
        log_and_print(
            f"  File size: {output_path.stat().st_size / (1024 * 1024):.2f} MB"
        )
        log_and_print(f"\n✓ Panel extract complete: {output_path}")
        log_and_print(f"Completed: {pd.Timestamp.now()}")
    finally:
        debug_log.close()
        debug_log = None

    print(f"Log file: {log_path}")
    return anes


def main():
    parser = argparse.ArgumentParser(
        description="Build ANES 2016–2020–2024 panel extract HDF."
    )
    parser.add_argument("--sav", default=str(DEFAULT_SAV))
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT))
    parser.add_argument("--compression", type=int, default=DEFAULT_COMPRESSION)
    args = parser.parse_args()
    run_extract(
        sav_path=args.sav,
        output_file=args.output,
        compression_level=args.compression,
    )


if __name__ == "__main__":
    main()
