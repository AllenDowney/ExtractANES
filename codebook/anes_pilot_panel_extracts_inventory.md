# ANES Pilot & Panel extracts — inventory for CultureWar

**Source repo:** `~/ExtractANES`  
**Date:** 2026-08-15  
**Audience:** CultureWar — how to use the two *auxiliary* ANES extracts alongside the main Time Series CDF extract.

These files are **not** the CDF APC extract. Do **not** append their rows to CDF-based APC stacks without an explicit design decision (mode / panel dependence).

| Extract | Rebuild | HDF | Column map |
|---------|---------|-----|------------|
| Midterm Pilots (Task 10) | `make run_pilot_extract` | `data/interim/anes_pilot_extract.hdf` | `…/anes_pilot_extract_labels.csv` |
| 2016–2020–2024 Panel (Task 11) | `make run_panel_extract` | `data/interim/anes_panel_extract.hdf` | `…/anes_panel_extract_labels.csv` |

HDF key for both: `anes` (pandas `pd.read_hdf(path, "anes")`).

Suggested CultureWar landing paths (when syncing by hand):

```text
~/CultureWar/notebooks/anes_pilot_extract.hdf
~/CultureWar/notebooks/anes_pilot_extract_labels.csv
~/CultureWar/notebooks/anes_panel_extract.hdf
~/CultureWar/notebooks/anes_panel_extract_labels.csv
~/CultureWar/codebook/anes_pilot_panel_extracts_inventory.md   # this file
~/CultureWar/codebook/anes_pilot_panel_harmonization.md          # coding fixes for extract rebuilds
```

Related notes in ExtractANES: `codebook/extract_notes.md` (Task 10 / Task 11 sections), `codebook/anes_pilot_panel_harmonization.md`, `project_board.md`.

---

## Shared conventions

- **Book VCFs:** Where an item matches CultureWar `SELECTED_VALUES` / ANES book labels, the extract column uses the CDF name (e.g. `VCF0206` Blacks FT).
- **Non-book columns:** Short descriptive names (`ft_transgender`, `immig_volume`, …).
- **Thermometers:** Numeric 0–100; ANES missing/skip codes (`< 0` or `> 100`) → NaN.
- **Other scales:** Numeric; codes `< 0` → NaN. Response-option labels live in year codebooks / CDF catalog — not re-exported here.
- **Demography:** `age`, `birth_year`, `cohort` (`year − age`), `sex`, `race` when available; coding is **wave-/study-specific** (not necessarily identical to CDF `VCF0104` / `VCF0106`).
- **Weight:** Study weight; values `≤ 0` → NaN. **Different weight series per extract/wave** — see below.

---

## 1. Pilot extract (`anes_pilot_extract.hdf`)

### What it is

Stacked **ANES Pilot** studies (opt-in online panels), kept for midterm / mode comparison vs Time Series CDF.

| Pilot year | N | Midterm calendar year? |
|------------|---|------------------------|
| 2016 | 1,200 | No |
| 2018 | 2,500 | Yes |
| 2019 | 3,165 | No |
| 2022 | 1,585 | Yes |
| **Total** | **8,450** | |

**Shape:** 8,450 rows × 27 columns.  
**IDs:** `year`, `pilot` (same as year), `source` (`anes_pilot_<year>`). No person-level panel ID across Pilots.  
**Weight:** Pilot `weight` (non-null: 2016 all; 2018 all; 2019 3,000; 2022 1,500).  
**Mode caveat:** YouGov-style opt-in online — **not** interchangeable with CDF FTF/mixed Time Series.

**Raw:** `ExtractANES/data/raw/midterm_pilots/{2016,2018,2019,2022}/`  
**Builder:** `notebooks/make_pilot_extract.py`  
**Crosswalk EDA:** `data/processed/anes_pilot_cdf_crosswalk.csv`, `notebooks/eda_pilot_inventory.md`

### Columns

**Core:** `year`, `pilot`, `source`, `weight`, `age`, `birth_year`, `cohort`, `sex`, `race`

**Book-aligned outcomes** (present in some years only — NaN elsewhere):

| Column | Concept | Years with data |
|--------|---------|-----------------|
| `VCF0206` | Blacks FT | 2016, 2018, 2019, 2022 |
| `VCF0207` | Whites FT | 2016, 2018, 2019, 2022 |
| `VCF0217` | Hispanics FT | 2016, 2018, 2019, 2022 |
| `VCF0227` | Asian-Americans FT | 2018, 2019, 2022 |
| `VCF0232` | Gays and lesbians FT | 2016, 2018 |
| `VCF0233` | Illegal immigrants FT | 2019 |
| `VCF0253` | Feminists FT | 2016, 2022 |
| `VCF9267` | Muslims FT | 2016, 2018, 2019 |
| `VCF9270`–`VCF9273` | Hardworking↔lazy (7-pt) W/B/H/A | **2022 only** |

**Pilot-only / not forced onto CDF names:**

| Column | Concept | Years | Caution |
|--------|---------|-------|---------|
| `immig_volume` | Increase/decrease immigrants | 2016, 2018, 2019 | Pilot **7-cat**; **never** rename to CDF `VCF0879` (5/6-cat). Any CDF↔Pilot figure needs an explicit category collapse (H3). |
| `ft_immigrants` | Immigrants FT | 2018, 2019 | Not a book VCF |
| `ft_legal_immigrants` | Legal immigrants FT | 2019 | Not a book VCF |
| `lazy_whites` / `lazy_blacks` / `lazy_hispanics` | Lazy stereotype | **2016 only** | **5-pt** Pilot-only names — **never** map onto `VCF9270`–`72` (H4) |

### Notable gaps vs CultureWar book

Equal-role scale, women’s movement FT, Protestants/Catholics/Jews/fundamentalists FTs (except Muslims in some years), gay-rights **policy** items, foreign aid, immigration “takes jobs,” most years’ illegal-immigrant FT.

---

## 2. Panel extract (`anes_panel_extract.hdf`)

### What it is

Long form of the **ANES 2016–2020–2024 Panel Merged Study** (same respondents across Time Series waves).

| Wave | Rows | Weight non-null |
|------|------|-----------------|
| 2016 | 2,839 | 2,839 (`V160102` post full-sample) |
| 2020 | 2,839 | 2,670 (`V200011b` 2016–2020 panel post) |
| 2024 | 2,839 | 2,070 (`V240106b` 2016–2024 panel post) |
| **Total** | **8,517** | |

**Shape:** 8,517 rows × 43 columns.  
**IDs:** `panel_id` (stable across waves), `year`, `caseid` (wave-specific), `source` = `anes_panel_2016_2020_2024`.  
**Design caveat:** Within-person dependence — use for **panel / change** analyses; do not treat rows as independent CDF cross-sections.

**Study page:** https://electionstudies.org/data-center/2016-2020-2024-panel-merged-study/  
**Raw:** `ExtractANES/data/raw/panel_2016_2020_2024/`  
**Builder:** `notebooks/make_panel_extract.py`  
**Staff repeated-item list:** `REPEATED_VARIABLES_2016_20_24.csv` (in that folder)

### Columns — core

`panel_id`, `year`, `source`, `caseid`, `weight`, `age`, `birth_year`, `cohort`, `sex`, `race`

### Columns — book-aligned (CultureWar ANES keys)

| Column | Concept | Waves |
|--------|---------|-------|
| `VCF0206` / `VCF0207` / `VCF0217` / `VCF0227` | Blacks / Whites / Hispanics / Asian-Americans FT | 2016, 2020, 2024 |
| `VCF0232` | Gay men and lesbians FT | all three |
| `VCF0233` | Illegal immigrants FT | all three |
| `VCF0253` | Feminists FT | all three |
| `VCF0205` | Jews FT | all three |
| `VCF9267` | Muslims FT | all three |
| `VCF0234` | Christian fundamentalists FT | all three |
| `VCF0879` | Immigration levels | all three |
| `VCF9223` | Immigration takes jobs | all three |
| `VCF9270` / `VCF9271` / `VCF9273` | Hardworking↔lazy W/B/A | all three |
| `VCF9272` | Hardworking↔lazy Hispanics | **2020, 2024 only** |
| `VCF0876` / `VCF0876a` | Gay job-discrimination favor/oppose (+ strength) | all three |
| `VCF0878` | Gay/lesbian couples adopt | all three |

**Not in this extract (book gaps / replacements):** `VCF0834` equal role; `VCF0225` women’s movement FT; `VCF0203`/`VCF0204` Protestants/Catholics FT; `VCF0892` foreign aid; `VCF0877` gays in military (see transgender military below).

### Columns — panel extras (not CDF book VCFs)

| Column | Concept | Waves |
|--------|---------|-------|
| `gay_marriage` | Position on gay marriage | all three |
| `immig_unauthorized` | Unauthorized immigrants policy | all three |
| `border_security` | Tightening border security | **2020, 2024** |

### Columns — transgender battery (main reason to prefer panel for these topics)

| Column | Concept | Waves |
|--------|---------|-------|
| `ft_transgender` | Feeling thermometer: transgender people | all three (~2787 / 2626 / 2029 non-null) |
| **`trans_bathroom_restrict`** | **Harmonized binary (H1): 1 = restrictive, 0 = inclusive** | all three — **use this for CultureWar / cross-wave series** |
| `trans_bathroom` | Raw bathroom item (wave-specific coding) | all three — audit only |
| `trans_bathroom_str` | Strength | all three — wave-specific |
| `trans_bathroom_sum` | Summary | all three — **do not** use cross-wave (H2: polarity + levels change) |
| `trans_military` | Favor/oppose transgender people in US Armed Forces | **2020, 2024** |
| `trans_military_str` / `trans_military_sum` | Strength / summary | **2020, 2024** |
| `trans_discrim` | Discrimination against transgender people | all three |
| `trans_know_someone` | Know transgender family/friends/coworkers/etc. | **2020, 2024** |
| `trans_sports_ban` | Ban transgender girls from K–12 girls’ sports | **2024 only** |

**H1 map for `trans_bathroom_restrict`:** 2016/2020 raw `1→1`, `2→0`; 2024 raw `2→1`, `1→0`, `3→NaN`. Details: `anes_pilot_panel_harmonization.md`, labels CSV `notes` column.

Source Time Series variable names by wave are in `anes_panel_extract_labels.csv`.

---

## 3. How CultureWar should treat them

| Use case | Prefer |
|----------|--------|
| Long-run APC / book figures (1948–2024) | **CDF extract** (`anes_extract_anes_timeseries_cdf_*.hdf`) |
| Midterm years 2018/2022 sensitivity vs CDF | **Pilot** (mode caveat) |
| Within-person 2016→2020→2024 change; illegal FT; gay policy; religion FTs; **trans** items | **Panel** |
| Pooling Pilot or Panel into CDF APC stacks | **Not by default** |

Copy this inventory with the four HDF/label files when syncing. Rebuild in ExtractANES if labels or column sets change.
