"""Build ANES Pilot ↔ book CDF crosswalk for Task 10.

Reads local Pilot microdata labels and CultureWar book VCF list; writes
``data/processed/anes_pilot_cdf_crosswalk.csv`` and study meta CSV.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pyreadstat

ROOT = Path(__file__).resolve().parent.parent
PILOT_ROOT = ROOT / "data/raw/midterm_pilots"
OUT_DIR = ROOT / "data/processed"

# Book VCFs from CultureWar notebooks/utils.py SELECTED_VALUES (ANES keys).
BOOK_VCFS = {
    "VCF0834": "Women equal role scale",
    "VCF0225": "Women's Libbers / women's movement FT",
    "VCF0253": "Feminists FT",
    "VCF0206": "Blacks FT",
    "VCF0207": "Whites FT",
    "VCF0227": "Asian-Americans FT",
    "VCF0232": "Gays and Lesbians FT",
    "VCF0233": "Illegal aliens / illegal immigrants FT",
    "VCF0217": "Hispanics FT",
    "VCF0203": "Protestants FT",
    "VCF0204": "Catholics FT",
    "VCF0205": "Jews FT",
    "VCF0234": "Christian Fundamentalists FT",
    "VCF9267": "Muslims FT",
    "VCF0879": "Increase/decrease immigrants (6-cat)",
    "VCF0879a": "Increase/decrease immigrants (4-cat)",
    "VCF9223": "Immigration levels take jobs",
    "VCF9270": "Hardworking–lazy: whites",
    "VCF9271": "Hardworking–lazy: blacks",
    "VCF9272": "Hardworking–lazy: Hispanics",
    "VCF9273": "Hardworking–lazy: Asians",
    "VCF0892": "Federal spending: foreign aid",
    "VCF0876": "Gay job-discrimination protection",
    "VCF0876a": "Gay job-discrimination strength",
    "VCF0877": "Gays in the military",
    "VCF0877a": "Gays in the military strength",
    "VCF0878": "Gay/lesbian couples adopt",
}

# Curated mappings: pilot_year -> book_vcf -> (pilot_vars, status, notes)
# status: match | match_split | related | miss
CURATED = {
    2022: {
        "VCF0217": ("fthisp", "match", "Hispanics FT"),
        "VCF0227": ("ftasian", "match", "Asians FT"),
        "VCF0206": ("ftblack1; ftblack2", "match_split", "Wording variants; random split"),
        "VCF0207": ("ftwhite1; ftwhite2", "match_split", "Wording variants; random split"),
        "VCF0253": ("ftfem", "match", "Feminists FT"),
        "VCF9270": ("swhwork", "match", "Hardworking–lazy whites"),
        "VCF9271": ("sblwork", "match", "Hardworking–lazy blacks"),
        "VCF9272": ("slawork", "match", "Hardworking–lazy Hispanics"),
        "VCF9273": ("saswork", "match", "Hardworking–lazy Asians"),
        "VCF0233": (
            "impstem_illegal_immigration; ownstem_illegal_immigration; imhope/imangry/…",
            "related",
            "No illegal-immigrant FT; salience/ownership + immigrant emotions",
        ),
        "VCF0879": ("imhope; imangry; imafraid; …", "related", "Emotion battery, not volume"),
        "VCF0879a": ("imhope; imangry; …", "related", "Emotion battery, not volume"),
    },
    2019: {
        "VCF0217": ("fthisp", "match", ""),
        "VCF0227": ("ftasian", "match", ""),
        "VCF0206": ("ftblack", "match", ""),
        "VCF0207": ("ftwhite", "match", ""),
        "VCF0233": ("ftillegal", "match", "Illegal immigrants FT (stronger than 2022)"),
        "VCF9267": ("ftmuslim", "match", ""),
        "VCF0879": ("immignum", "match", "Immigration volume (increase/decrease)"),
        "VCF0879a": ("immignum", "match", "Same item; collapse in analysis if needed"),
        # Related extras not in book list but useful:
        # ftimmig1 / ftimmig2 = immigrants / legal immigrants FTs
    },
    2018: {
        "VCF0217": ("fthisp", "match", ""),
        "VCF0227": ("ftasian", "match", ""),
        "VCF0206": ("ftblack", "match", ""),
        "VCF0207": ("ftwhite", "match", ""),
        "VCF0232": ("ftgay", "match", "Gays and lesbians FT (absent in 2022)"),
        "VCF9267": ("ftmuslim", "match", ""),
        "VCF0879": ("immignum", "match", "Immigration volume"),
        "VCF0879a": ("immignum", "match", ""),
        "VCF0233": (
            "ftimmig; illimcrime; illimecon; illimschool",
            "related",
            "Immigrants FT + illegal-immigration consequence items; no illegal FT",
        ),
    },
    2016: {
        "VCF0217": ("fthisp", "match", ""),
        "VCF0206": ("ftblack", "match", ""),
        "VCF0207": ("ftwhite", "match", ""),
        "VCF0232": ("ftgay", "match", ""),
        "VCF0253": ("ftfem", "match", ""),
        "VCF9267": ("ftmuslim", "match", ""),
        "VCF0879": ("immig_numb", "match", "Legal immigration volume wording"),
        "VCF0879a": ("immig_numb", "match", ""),
        "VCF9270": ("lazyw", "related", "Lazy stereotype (not full hardworking–lazy 7-pt)"),
        "VCF9271": ("lazyb", "related", "Lazy — Blacks"),
        "VCF9272": ("lazyh", "related", "Lazy — Hispanics"),
        "VCF0227": ("", "miss", "No Asian FT in 2016 Pilot skim"),
    },
}

PILOT_FILES = {
    2022: (PILOT_ROOT / "2022/anes_pilot_2022_stata_20221214.dta", "stata"),
    2019: (PILOT_ROOT / "2019/anes_pilot_2019.dta", "stata"),
    2018: (PILOT_ROOT / "2018/anes_pilot_2018.dta", "stata"),
    2016: (PILOT_ROOT / "2016/anes_pilot_2016.sav", "sav"),
}


def study_meta(path: Path, kind: str) -> dict:
    if kind == "stata":
        with pd.io.stata.StataReader(path) as reader:
            labels = reader.variable_labels()
        n = int(pd.read_stata(path, columns=[next(iter(labels))], convert_categoricals=False).shape[0])
        return {"n_rows": n, "n_vars": len(labels), "format": "stata"}
    _df, meta = pyreadstat.read_sav(path, metadataonly=True)
    return {
        "n_rows": int(meta.number_rows),
        "n_vars": len(meta.column_names),
        "format": "sav",
    }


def build_crosswalk() -> tuple[pd.DataFrame, pd.DataFrame]:
    meta_rows = []
    cross_rows = []
    for year, (path, kind) in sorted(PILOT_FILES.items(), reverse=True):
        if not path.exists():
            continue
        meta = study_meta(path, kind)
        meta_rows.append(
            {
                "pilot_year": year,
                "n_rows": meta["n_rows"],
                "n_vars": meta["n_vars"],
                "format": meta["format"],
                "path": str(path.relative_to(ROOT)),
                "midterm_calendar_year": year in (2018, 2022),
            }
        )
        curated = CURATED.get(year, {})
        for vcf, book_label in BOOK_VCFS.items():
            if vcf in curated:
                pilot_vars, status, notes = curated[vcf]
            else:
                pilot_vars, status, notes = "", "miss", ""
            cross_rows.append(
                {
                    "book_vcf": vcf,
                    "book_label": book_label,
                    "pilot_year": year,
                    "match_status": status,
                    "pilot_vars": pilot_vars,
                    "notes": notes,
                }
            )
    return pd.DataFrame(meta_rows), pd.DataFrame(cross_rows)


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    meta_df, cross_df = build_crosswalk()
    meta_path = OUT_DIR / "anes_pilot_study_meta.csv"
    cross_path = OUT_DIR / "anes_pilot_cdf_crosswalk.csv"
    meta_df.to_csv(meta_path, index=False)
    cross_df.to_csv(cross_path, index=False)
    print(f"Wrote {meta_path}")
    print(meta_df.to_string(index=False))
    print(f"\nWrote {cross_path}")
    print(cross_df.groupby(["pilot_year", "match_status"]).size().unstack(fill_value=0))
    print("\nUseful (non-miss) counts by year:")
    for y, g in cross_df.groupby("pilot_year"):
        n = (g["match_status"] != "miss").sum()
        print(f"  {y}: {n}/{len(g)} book VCFs have match/related Pilot item")


if __name__ == "__main__":
    main()
