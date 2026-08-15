# ANES CDF Extract Notes

Project decisions for variables added to `notebooks/make_cdf_extract.py`. ANES codebook harmonization text lives in `codebook/extracted/anes_cdf_minimal.json` (`notes` field); this file records **what we keep in the extract** and **analysis caveats**.

See also: `codebook/codebook_plan.md`, Task-specific EDA notebooks under `notebooks/`.

---

## Core demographics: age, cohort, VCF0103

The CDF has no native birth-year variable. The extract keeps harmonized **age**, derives **cohort** as an approximate birth year, and retains the CDF’s **VCF0103** birth-era bins under the original variable name.

| Extract column | Source | Type | Description |
|----------------|--------|------|-------------|
| `year` | `VCF0004` | CDF | Survey year (1948–2024) |
| `age` | `VCF0101` | CDF | Respondent age; missing code `0` → NaN |
| `cohort` | derived | `year - age` | Approximate birth year; NaN when `year` or `age` is missing |
| `VCF0103` | `VCF0103` | CDF | ANES birth-era bins (1–8); missing code `0` → NaN; **not** birth year |

**Derivation:** After catalog missing recode on `age`, `cohort = year - age`. No rounding or censoring.

**Caveats (from ANES harmonization, not extra extract logic):**

- Age reference date varies by study year (interview date, Nov 1, election day, etc.); pre-1964 often uses reported age rather than computed birthdate. See `VCF0101` `notes` in `anes_cdf_minimal.json`.
- Top-coded ages **97–99** (“97+”, etc.) are kept as numeric and subtracted literally, so `cohort` can be off by a few years for very old respondents.
- **`cohort` and `VCF0103` measure different things.** `cohort` is a point estimate of birth year; `VCF0103` is ANES’s fixed birth-era categories (e.g. code 4 = 1943–1958). They will not always agree.
- **`VCF0103` in 1948 and 1954** was estimated from age groups; see codebook notes.

### Paste into CultureWar

Copy the block below into CultureWar project docs (e.g. `PROJECT_BOARD.md` or a codebook note):

```markdown
## ANES extract: age and cohort columns

Source: ExtractANES `make_cdf_extract.py` → HDF synced to `notebooks/anes_extract_*.hdf`.

| Column | Source | Meaning |
|--------|--------|---------|
| `year` | `VCF0004` | ANES Time Series survey year |
| `age` | `VCF0101` | Respondent age (harmonized CDF) |
| `cohort` | **derived** | Approximate **birth year** = `year - age` |
| `VCF0103` | `VCF0103` | ANES birth-era **bins** (1–8), unchanged from CDF |

**Use `cohort` for birth-year / APC-style work.** It is not the same as `VCF0103`.

- `cohort` is computed after recoding age missing codes to NaN; missing when either input is missing.
- `VCF0103` labels are fixed birth-year ranges (e.g. 4 = 1943–1958), not survey-relative bins.
- Age harmonization rules differ by year; top codes 97–99 are treated as numeric ages.
- There is **no** `birth_year` column in the extract; `cohort` holds that role.

Catalog detail: `codebook/extracted/anes_cdf_minimal.json` (`VCF0101`, `VCF0103`).
```

---

**Source (Task 4):** CDF appendix PDF `data/raw/anes_timeseries_cdf_codebook_app_20260205.pdf`, section **WEIGHTS** (p. 1–2). Variable-level `notes` in `anes_cdf_minimal.json` point here but do not include the text.

---

## Task 4: Sample weights

**Extract uses:** `VCF0009z` (type 0, full sample).

### Weight grid (suffix × 1970 type)

| | **Type 0** (`VCF0009*`) | **Type 1** (`VCF0010*`) | **Type 2** (`VCF0011*`) |
|--|-------------------------|-------------------------|-------------------------|
| **Full sample** | `VCF0009z` | `VCF0010z` | `VCF0011z` |
| **FTF only** | `VCF0009x` | `VCF0010x` | `VCF0011x` |
| **Web only** | `VCF0009y` | `VCF0010y` | `VCF0011y` |

**Suffix (x / y / z):** Choose sample for 2012+ mode-mixed years.

- **`z`** — combined full sample (FTF + web/internet, etc.)
- **`x`** — face-to-face (in-person) subsample only
- **`y`** — web/internet subsample only

2012 and 2016 included both FTF and web; 2020 web/phone/video; 2024 web/FTF/video/phone (see variable codebook intro table footnote).

**1970 type (0009 / 0010 / 0011):** In the 1970 study, weights applied at the **variable** level. Three schemes — Type 0, Type 1, Type 2 — are indicated in codebook **sources** for each variable’s 1970 row, e.g. `V700390(type 0)`. Match weight number to that tag for 1970 rows.

- **`VCF0009*`** — 1970 Type 0 *(default for most CDF variables)*
- **`VCF0010*`** — 1970 Type 1
- **`VCF0011*`** — 1970 Type 2

The appendix does **not** define substantively what Type 0/1/2 meant in the 1970 design — only which weight column to use. For that, see 1970 ANES study documentation online.

### When the nine weights agree

From the appendix (paraphrased):

1. **Neither 1970 nor 2012+ mode splits in use** → all nine weights are **identical**; any one suffices.
2. **2012+ included, 1970 excluded** → 0009 vs 0010 vs 0011 **does not matter**; pick the correct **suffix** (`x`/`y`/`z`).
3. **1970 included, 2012+ mode splits excluded** → suffix **does not matter**; pick the correct **type** (0009/0010/0011) for each variable’s 1970 tag.
4. **Both 1970 and 2012+** → match **both** suffix and 1970 type.

**Catalog note:** Most variables with 1970 data use Type 0.

### 1970 Type 1 and Type 2 variables (complete list from appendix)

**Type 1:** `VCF0522`, `VCF0601`, `VCF0602`, `VCF0603`, `VCF0622`, `VCF0623`, `VCF0624`, `VCF0625`, `VCF0649`, `VCF0825`, `VCF0880`, `VCF0881`

**Type 2:** `VCF0813`, `VCF0814`, `VCF0815`, `VCF0816`, `VCF0818`, `VCF0819`, `VCF0820`, `VCF0821`, `VCF0860`, `VCF0861`, `VCF0862`, `VCF0863`, `VCF0864`, `VCF0865`, `VCF0866`

All other variables with 1970 data are Type 0.

### Other weight notes (codebook intro)

- **1992+:** Weights are post-stratified and centered to mean 1.
- **`VCF9999`** (post-election weight, full sample): catalog says *“Additional documentation will be forthcoming.”* Use for post-election-only variables; see ANES website for details not in the CDF appendix.

### Recommended weight for this extract

**Pooled time-series descriptive/APC work:** **`VCF0009z`** (Type 0, full sample) — **used in `make_cdf_extract.py`** as column `weight`.

Rationale:

- Nearly all extract variables are Type 0 if they include 1970; Task 6 attitude items start in 1972+ (`VCF0834` catalog `weight` field lists `VCF0009x/y/z`).
- For years **other than 1970 and 2012+ mode-mixed years**, all nine weights are identical.
- Type 1/2 variables in the extract are none today; if added later, use variable-specific weights for 1970 rows or standardize on Type 0 variables.

**Mode-specific analysis (2012+):** Use `x` or `y` instead of `z` when restricting to FTF or web subsamples.

### Appendix text (verbatim)

<details>
<summary>WEIGHTS section — `anes_timeseries_cdf_codebook_app_20260205.pdf` p. 1</summary>

To accommodate the addition of ANES 2012 and later Time Series Study, weights in the file have been replaced.

Selection among the new CDF weights depends upon how CDF data from 2012 and later years are used. The ANES 2012 and 2016 Time Series Study included both face-to-face (in-person) interviews and Web interviews. Data from both of the modes are present in the CDF.

It must first be decided whether CDF data should be used from the full (combined) sample, from the FTF-only sample, or from the internet-only sample.

When using the combined sample, one of the following three CDF weight variables can apply: VCF0009z, VCF0010z, VCF0011z

When using the FTF-only sample, one of the following three CDF weight variables can apply: VCF0009x, VCF0010x, VCF0011x

When using the Web-only sample, one of the following three CDF weight variables can apply: VCF0009y, VCF0010y, VCF0011y

Once the desired sample from has been identifed, and the choice of weight has been narrowed down to one of the three "z" variables, or one of the three "x" variables, or one of the three "y" variables), selection of a specific weight variable numbered 0009, 0010, or 0011 (from among the set of three weights with the same letter suffix, "x" or "y" or "z") now depends upon the type of 1970 data being used.

In the 1970 Time Series study, weights were applicable at variable level for 3 types of 1970 variables, Type "0", Type "1" and Type "2".

In CDF codebook documentation, indication is provided for every CDF variable whether 1970 data are from Type 0, Type 1, or Type 2 variables. For 1970, the three "0009" weight variables (VCF0009x,VCF0009y,VCF0009z) are for 1970 type 0; the three "0010" weight variables (VCF0010x,VCF0010y,VCF0010z) are for 1970 type 1, and the three "0011" weight variables (VCF0011x,VCF0011y,VCF0011z) are for 1970 Type 2.

If, for example, you have chosen to work with the FTF-only sample from 2012, an "x" variable should be chosen; VCF0009x should be selected if the CDF variable being used has documentation in the codebook indicating 1970 data were Type 0, VCF0010x should be selected if the CDF variable being used has documentation in the codebook indicating 1970 data were Type 1, and VCF0011x should be selected if the CDF variable being used has documentation in the codebook indicating 1970 data were Type 2

If use of the CDF includes 2012 data but excludes 1970 data, it does not matter whether the 0009, 0010, or 0011 variable is used as long as the "x" or "y" or "z" suffix is appropriate. Values are identical across variables having the same suffix (x or y or z) for all years except 1970.

If use of the CDF includes 1970 data but excludes 2012 data, the "x" or "y" or "z" suffix does not matter as long as the number (0009 or 0010 or 0011) is appropriate to the type of 1970 data.

If neither 1970 nor 2012 data from the CDF are being used, than any of the 9 variables can be used: all 9 weights are identical for years other than 1970 and 2012.

NOTE: most variables in the ANES Timeseries Cumulative Data File that include 1970 data use "Type 0" data from 1970.

</details>

---

## Task 6: Women's role, feminism, equal-rights backlash

**EDA:** `notebooks/eda_womens_role.md`  
**Added to extract:** `VCF0834`, `VCF9014`, `VCF9017` (VCF names retained, like thermometers)

### `VCF0834` — Women equal role scale

**Question (summary):** 7-point scale from “women and men should have an equal role” (1) to “women’s place is in the home” (7).

**Extract decision:** Keep as harmonized in the CDF. Higher values = more traditional / home-centered.

**Missing codes (recoded to NaN):** `0` (NA — includes 2008 version NEW and 2000 telephone); `9` (DK / haven’t thought much). From catalog + value labels.

**Harmonization caveats:**

| Issue | Detail |
|-------|--------|
| **2000 telephone** | `VCF0834` includes face-to-face 7-point scale only. Telephone respondents received a branching series not represented here → coded `0`. |
| **2008 OLD/NEW** | Question administered to random half (OLD). Remaining half (NEW) not asked → coded `0`. |
| **2000 wording** | Random half got “or haven’t you thought much about this?” in question text; both face-to-face versions included. |
| **Year span** | 16 survey years (1972–2008); not asked 2012+. |

### `VCF9014` — We have gone too far pushing equal rights

**Question:** “We have gone too far in pushing equal rights in this country.”

**Extract decision:** Keep 5-point agree–disagree as coded (1 = agree strongly … 5 = disagree strongly). Higher = *less* backlash (more support for equal-rights push).

**Missing codes:** `8` (DK), `9` (NA / no Post IW). Catalog `missing_codes` is `[9]`; value labels add `8`.

**Harmonization caveats:**

- Part of egalitarianism battery (`VCF9013`–`VCF9018`); item order varied by study.
- 12 survey years (1984–2012; gaps in 2016, 2020, 2024).

### `VCF9017` — Country would be better off worrying less about equality

**Question:** “The country would be better off if we worried less about how equal people are.”

**Extract decision:** Same 5-point scale as `VCF9014`. Higher = *less* agreement with the anti-egalitarian statement.

**Missing codes:** `8` (DK), `9` (NA).

**Harmonization caveats:**

- Same battery as `VCF9014`.
- 14 survey years (1984–2024; gaps in 1998, 2016).

### Thermometers (already in extract)

`VCF0225` (Women’s Libbers / women’s movement) and `VCF0253` (Feminists) use standard group-thermometer recode rules in `utils.recode_thermometer_columns`. See Task 2 thermometer filter in `project_board.md`.

---

## Task 8: LGBT rights and anti-discrimination attitudes

**EDA:** `notebooks/eda_lgbt_rights.md`  
**Added to extract:** `VCF0876`, `VCF0876a`, `VCF0877`, `VCF0877a`, `VCF0878` (VCF names retained)

**Cross-reference:** `VCF0232` (Gays and Lesbians thermometer) already in extract; see Task 2.

### `VCF0876` — Job-discrimination protection (favor / oppose)

**Question (summary):** Favor or oppose laws to protect homosexuals / gays and lesbians against job discrimination.

**Extract decision:** Keep harmonized CDF codes. **1 = favor**, **5 = oppose**. Lower = more supportive.

**Missing codes (recoded to NaN):** `8` (DK; 1988 “depends”), `9` (NA / no Post IW). Catalog `missing_codes` is `[9]`; value labels add `8`.

**Harmonization caveats:**

| Issue | Detail |
|-------|--------|
| **2012** | Random ½ sample only (other half got alternate wording/version). |
| **Wording** | *Homosexuals* vs. *gays and lesbians* across years (see catalog `question`). |
| **Year span** | 10 waves: 1988, 1992, 1996, 2000, 2004, 2008, 2012, 2016, 2020, 2024. |

### `VCF0876a` — Strength of position on job-discrimination law

**Question:** Follow-up strength for respondents who favor or oppose on `VCF0876`.

**Extract decision:** Keep as coded. **1–2 = favor** (strongly / not strongly), **4–5 = oppose** (not strongly / strongly). Code **7** = DK on strength or on main item (1988 depends).

**Missing codes:** `7`, `9` (from catalog + value labels).

**Harmonization caveats:** Same waves and 2012 ½-sample note as `VCF0876`. See catalog notes VCF0876.

### `VCF0877` — Gays in the military (allow / not allow)

**Question:** Should homosexuals be allowed to serve in the U.S. Armed Forces?

**Extract decision:** **1 = yes, allow**, **5 = don't allow**. Lower = more supportive.

**Missing codes:** `8` (DK), `9` (NA).

**Harmonization caveats:**

| Issue | Detail |
|-------|--------|
| **2012** | Random ½ sample. |
| **Year span** | 6 waves: 1992, 1996, 2000, 2004, 2008, 2012. Not asked 2016+. |

### `VCF0877a` — Strength of position on military service

**Extract decision:** Parallel to `VCF0876a`: **1–2 = allow**, **4–5 = don't allow**; **7** = DK.

**Missing codes:** `7`, `9`.

**Harmonization caveats:** Same 6 waves as `VCF0877`.

### `VCF0878` — Gay/lesbian couples permitted to adopt

**Question:** Should gay or lesbian (homosexual) couples be legally permitted to adopt children?

**Extract decision:** **1 = yes**, **2 = no** (oppose). Lower = more supportive.

**Harmonization:** ANES used **5 = no** through 2020 and **2 = no** in 2024 only. The extract recodes legacy **5 → 2** on pre-2024 waves (`harmonize_vcf0878_adopt` in `notebooks/utils.py`).

**Missing codes:** `8` (DK), `9` (NA).

**Harmonization caveats:**

| Issue | Detail |
|-------|--------|
| **Year span** | 8 waves: 1992, 2000, 2004, 2008, 2012, 2016, 2020, 2024. Gap: 1996. *(Catalog `years_available` omits 2016; EDA confirms 2016 data.)* |
| **Wording** | *Gay or lesbian couples* / *homosexual couples* (see catalog). |
| **Oppose code** | After extract harmonization, **2 = no** in all waves; CultureWar APC uses `SELECTED_VALUES` `[2]`. |

---

## Task 9: Immigration, immigrant threat, and group stereotypes

**EDA:** `notebooks/eda_immigration.md`  
**Added to extract:** `VCF0879`, `VCF0879a`, `VCF9223`, `VCF9270`–`VCF9273`, `VCF0892` (VCF names retained); `hispanic` ← `VCF0108`, `hispanic_type` ← `VCF0107`

**Cross-reference thermometers (already in extract):** `VCF0217` (Hispanics), `VCF0227` (Asian-Americans), `VCF0233` (illegal aliens / illegal immigrants).

**Missing-code helper updates (this task):** `utils.dk_codes_from_value_labels` now parses negative codes (`-8`, `-9`) and skips false positives like “Yes, Hispanic but DK/NA type.” `recode_vcf_columns` / core recode also drop any remaining negative values (e.g. unlabeled `-1` on `VCF9223`).

### `VCF0879` — Increase/decrease immigrants (6-category)

**Question:** Number of immigrants from foreign countries who are permitted to come to the U.S. should be increased a lot / a little / left the same / decreased a little / decreased a lot.

**Extract decision:** Keep both 6-cat and 4-cat. Prefer **`VCF0879`** for APC when present (finer grain). Higher = prefer fewer immigrants.

| Code | Label |
|------|-------|
| 1 | Increased a lot |
| 2 | Increased a little |
| 3 | Same as now |
| 4 | Decreased a little |
| 5 | Decreased a lot |

**Missing codes:** `8` (DK), `9` (NA).

**Year span:** 1992, 1994, 1996, 1998, 2004, 2008, 2012, 2016, 2020, 2024 (gap **2000** — use `VCF0879a` for that year).

### `VCF0879a` — Increase/decrease immigrants (4-category)

**Extract decision:** Keep for coding checks and **2000** coverage. Collapse: 1 = increased, 3 = same, 5 = decreased.

**Missing codes:** `8`, `9`.

**Year span:** Same as `VCF0879` plus **2000**.

### `VCF9223` — Immigration levels take jobs

**Question:** How likely recent immigration levels will take jobs away from people already here.

**Extract decision:** Keep as coded. **1 = extremely likely** … **4 = not at all likely**. Higher = less economic-threat perception.

**Missing codes:** `-9`, `-8` (and any other negatives, e.g. unlabeled `-1`).

**Year span:** 2004, 2008, 2012, 2016, 2020, 2024.

### `VCF9270`–`VCF9273` — Hardworking↔lazy (7-pt) by group

| Variable | Group |
|----------|-------|
| `VCF9270` | Whites |
| `VCF9271` | Blacks |
| `VCF9272` | Hispanic-Americans |
| `VCF9273` | Asian-Americans |

**Extract decision:** Keep full battery (not Hispanic/Asian only). **1 = hardworking** … **7 = lazy**. Higher = more negative stereotype. Administered whites first, then other groups in random order; 2008 ACASI.

**Missing codes:** `-9`, `-8` (and other negatives).

**Year span:** 1992–2024 even years with gaps (`VCF9273` skips 1996). No intelligent–unintelligent companion scales in the CDF.

### `VCF0892` — Federal spending: foreign aid

**Extract decision:** Keep (thin series). **1 = increased**, **2 = same**, **3 = decreased or cut out**.

**Missing codes:** `8`, `9`.

**Year span:** 1990, 1996, 2000, 2002, 2004, 2008 (ends 2008).

### `hispanic` (`VCF0108`) / `hispanic_type` (`VCF0107`)

**Extract decision:** Renamed core demographics for subgroup splits.

| Output | Source | Codes (after missing recode) |
|--------|--------|------------------------------|
| `hispanic` | `VCF0108` | 1 = Hispanic, 2 = not Hispanic |
| `hispanic_type` | `VCF0107` | 1 Mexican-American/Chicano, 2 Puerto Rican, 3 other Hispanic, **4 Hispanic but DK/NA type** (kept — substantive), 7 not Hispanic |

**Missing codes:** `0`, `8`, `9`, plus negatives. Code **4** is *not* treated as missing (Hispanic of unknown type).

**Caveats:** Pre-1988 Hispanic origin often from interviewer observation; sparseness / confidentiality for fine types in early years.

---

## Task 10: Midterm Pilot inventory (separate extract)

**EDA / crosswalk:** `notebooks/eda_pilot_inventory.md`, `notebooks/build_pilot_crosswalk.py`  
**Crosswalk outputs:** `data/processed/anes_pilot_cdf_crosswalk.csv`, `anes_pilot_study_meta.csv`  
**Extract:** `make run_pilot_extract` → `data/interim/anes_pilot_extract.hdf` (+ `_labels.csv`); log `notebooks/logs/extract_pilot.txt`  
**Raw:** `data/raw/midterm_pilots/{2022,2019,2018,2016}/`

### Decision so far

Local Pilots are **useful enough** for a small **separate** extract (thermometers / immigration volume / stereotypes), especially midterm years **2022** and **2018**. Do **not** merge into the CDF HDF. Defer **2006** and older Pilots until mode diagnostics on this extract.

| Pilot | N | Book-VCF useful | Highlights |
|-------|---|-----------------|------------|
| 2022 | 1,585 | 12/27 | Race FTs + feminists FT + hardworking–lazy 7-pt; no gays FT; no illegal FT |
| 2019 | 3,165 | 8/27 | `ftillegal`, `immignum`, Muslims FT; not a midterm year |
| 2018 | 2,500 | 9/27 | `ftgay`, `immignum`, Muslims FT; midterm year |
| 2016 | 1,200 | 11/27 | `ftgay`, `ftfem`, `immig_numb`, `lazy*`; SPSS `.sav` |

**Mode:** All local Pilots are opt-in online panels — parallel / sensitivity only vs Time Series CDF.

### Extract conventions (`make_pilot_extract.py`)

- Stack years in one HDF (`key=anes`); keep `year`, `pilot`, `source`, `weight`, demogs (`birth_year`, `age`, `cohort=year−age`, `sex`, `race` when present).
- Book VCF column names where matched (e.g. `VCF0206` Blacks FT). 2022 Blacks/Whites: coalesce `ftblack1`/`ftblack2`, `ftwhite1`/`ftwhite2`.
- Thermometers: keep 0–100; negatives / skips → missing.
- Immigration volume stays as `immig_volume` (Pilot 7-cat `immignum` / `immig_numb`) — **not** forced onto CDF `VCF0879` (5/6-cat).
- 2016 `lazy_*` kept separate from CDF 7-pt hardworking–lazy (`VCF9270`–`VCF9273` from 2022 only).
- Extra Pilot-only FTs: `ft_immigrants`, `ft_legal_immigrants` (not book VCFs).
- Weight: Pilot `weight`; values ≤0 → missing.

---

## Task 11: 2016–2020–2024 Panel Merged Study (separate extract)

**Raw:** `data/raw/panel_2016_2020_2024/` (SPSS merged file + `REPEATED_VARIABLES_2016_20_24.csv` + year TS codebooks)  
**Extract:** `make run_panel_extract` → `data/interim/anes_panel_extract.hdf` (+ `_labels.csv`); log `notebooks/logs/extract_panel.txt`  
**Study page:** https://electionstudies.org/data-center/2016-2020-2024-panel-merged-study/

### Decision

Build a **long** panel extract (2,839 × 3 waves) kept separate from CDF and Pilot HDFs. Strong book overlap plus transgender battery. Do **not** pool with CDF APC stacks by default.

### Extract conventions (`make_panel_extract.py`)

- Reshape wide V16*/V20*/V24* file → rows keyed by `panel_id` + `year`.
- Book VCF names where matched (thermometers, `VCF0879`, `VCF9223`, `VCF9270`–`VCF9273`, `VCF0876`/`a`, `VCF0878`).
- Panel-only columns: `ft_transgender`, `trans_bathroom` (+ str/sum), **`trans_bathroom_restrict`** (H1 derived), `trans_military` (+ str/sum; 2020+), `trans_discrim`, `trans_know_someone` (2020+), `trans_sports_ban` (2024-only), `gay_marriage`, `immig_unauthorized`, `border_security` (2020+).
- Thermometers 0–100; other scales drop `< 0`.
- Weights: 2016 `V160102` (post full-sample); 2020 `V200011b` (2016–2020 panel post); 2024 `V240106b` (2016–2024 panel post). Non-positive → missing. Wave Ns with weight: ~2839 / 2670 / 2070.
- `cohort = year − age`; birth year from restricted year vars when usable, else `year − age`.

### Transgender notes

Bathroom policy and transgender FT repeat 2016–2024. **Raw `trans_bathroom` polarity flips in 2024** — CultureWar should model **`trans_bathroom_restrict`** (1 = restrictive, 0 = inclusive): 2016/2020 `1→1`, `2→0`; 2024 `2→1`, `1→0`, `3→NaN`. Do not use `trans_bathroom_sum` as a cross-wave series (H2). Military service favor/oppose starts 2020 (legacy “gays in military” not in this panel stream). K–12 girls’ sports ban is **2024-only** (`V241373`) and is **not** on the ANES repeated-variables list — still kept in the extract.

### Task 12 (harmonization)

See `codebook/anes_pilot_panel_harmonization.md`. Done for H1–H4: derived bathroom binary; `_sum` audit-only; Pilot `immig_volume` / `lazy_*` stay non-CDF names.

