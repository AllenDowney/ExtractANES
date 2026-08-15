# ExtractANES Project Board

Numbered tasks for tracking work. Each task has a permanent number; add new tasks at the end. Update status as work progresses.

---

## Task 1: Bootstrap repo from GssExtract template

**Status:** In progress

Adapt the project scaffolding from [GssExtract](~/GssExtract) for ANES data processing. GssExtract follows the [cookiecutter data science](https://drivendata.github.io/cookiecutter-data-science/) layout; this repo reuses the same configuration pattern with ANES-specific naming. This is a notebook-based project, not an installable Python package.

### Configuration files to copy and modify

| Source (GssExtract) | Target (ExtractANES) | Modifications |
|---------------------|----------------------|---------------|
| `Makefile` | `Makefile` | `PROJECT_NAME` → `ExtractANES`; lint/format paths → `notebooks/` |
| `pyproject.toml` | `pyproject.toml` | Copy as-is (black config) |
| `setup.cfg` | `setup.cfg` | Copy as-is (flake8 config) |
| `requirements.txt` | `requirements.txt` | Add `pyreadstat` for Stata/SPSS ANES files |
| `requirements-dev.txt` | `requirements-dev.txt` | Copy as-is |
| `.gitignore` | `.gitignore` | Ensure `/data/` excluded (keep GitHub template entries) |
| `README.md` | `README.md` | Update title and one-line description |

**Deferred for later tasks** (copy when needed):

| Source (GssExtract) | Notes |
|---------------------|-------|
| `docs/` (Sphinx) | Adapt `conf.py` project name when documentation is needed |

### Setup steps

- [x] Copy and adapt configuration files listed above
- [ ] Create conda environment: `make create_environment` then `conda activate ExtractANES`
- [ ] Install dependencies: `make requirements` (or `pip install -r requirements-dev.txt` for dev tools)
- [ ] Create data directories: `data/raw/`, `data/interim/`, `data/processed/`
- [ ] Verify tooling: `make lint`, `make help`

**Quick start commands:**
```bash
cd ~/ExtractANES
make create_environment
conda activate ExtractANES; make requirements
pip install -r requirements-dev.txt
make help
```

---

## Task 2: Fetch and inventory ANES source data

**Status:** In progress

Download ANES source files, document what we have, and build the first CDF extract.

- [x] Download ANES source data into `data/raw/`
- [x] Create `data/raw/INVENTORY.md` (adapt template from `GssExtract/data/raw/INVENTORY.md`)
- [x] Write first extract notebook (`notebooks/make_cdf_extract.md`)
- [x] Run extract notebook and verify output HDF
- [x] EDA notebook (`notebooks/explore_cdf_extract.md`)

### Extract variable plan

The CDF has no explicit birth-year field. We keep **age**, derive **`cohort = year - age`** (approximate birth year), and retain **`VCF0103`** unchanged (ANES birth-era bins 1–8).

| Output name | CDF variable | Description |
|-------------|--------------|-------------|
| `year` | `VCF0004` | Year of study (1948–2024) |
| `age` | `VCF0101` | Respondent age |
| `cohort` | *(derived)* | `year - age` (approximate birth year) |
| `VCF0103` | `VCF0103` | ANES birth-era cohort bins (1–8); kept under CDF name |
| `sex` | `VCF0104` | Respondent gender (1=Male, 2=Female, 3=Other) |
| `race` | `VCF0106` | Race summary, 3 categories |
| `race_eth` | `VCF0105a` | Race-ethnicity summary, 7 categories |
| `hispanic` | `VCF0108` | Hispanic origin yes/no (Task 9) |
| `hispanic_type` | `VCF0107` | Hispanic origin type (Task 9) |
| `polviews` | `VCF0803` | Liberal–conservative scale (7-point; GSS `polviews` analog) |
| `weight` | `VCF0009z` | Full-sample weight, 1970 type 0 (see Task 4) |
| `VCF0006` | `VCF0006` | Year-level case ID |
| `VCF0006a` | `VCF0006a` | Cross-year respondent ID |
| *(37 columns)* | see below | Feeling thermometers (filtered; see Task 2 log) |

**Planned individual characteristics (Task 3):**

| Output name | CDF variable | Description |
|-------------|--------------|-------------|
| `attend` | `VCF0130` | Church attendance (1970–; see also `VCF0130a` for 1990–) |

**Thermometer filter (2026-06-18):** Drop derived Average/Index variables, named-candidate thermometers, candidate/challenger/incumbent slots, Senator variables, Jesse Jackson, and any thermometer asked in fewer than 6 survey years. **92 → 37** kept.

**Group thermometers available in the CDF** (whether kept or dropped):

| Category | Variable | Label | Years asked | Kept? |
|----------|----------|-------|-------------|-------|
| **Race/ethnicity** | VCF0206 | Blacks | 25 | ✓ |
| | VCF0207 | Whites | 23 | ✓ |
| | VCF0217 | Chicanos/Hispanics | 15 | ✓ |
| | VCF0227 | Asian-Americans | 9 | ✓ |
| | VCF0233 | Illegal Aliens | 9 | ✓ |
| | VCF9267 | Muslims | 6 | ✓ |
| | VCF9007 | Jesse Jackson | 9 | ✗ |
| **Religion** | VCF0203 | Protestants | 7 | ✓ |
| | VCF0204 | Catholics | 13 | ✓ |
| | VCF0205 | Jews | 14 | ✓ |
| | VCF0234 | Christian Fundamentalists | 12 | ✓ |
| | VCF9003 | Evangelical Groups | 4 | ✗ |
| | VCF9269 | Christians | 5 | ✗ |
| **Gender/sexuality** | VCF0232 | Gays and Lesbians | 14 | ✓ |
| | VCF0253 | Feminists | 10 | ✓ |
| | VCF0225 | Women's Libbers | 12 | ✓ |
| | VCF9006 | Women | 5 | ✗ |
| | — | Men | — | **Not in CDF** |
| | — | Transgender people | — | **Not in CDF** |
| **Class/income** | VCF0223 | Poor People | 18 | ✓ |
| | VCF0220 | People on Welfare | 14 | ✓ |
| | VCF0219 | Middle Class People | 8 | ✓ |
| | VCF9268 | rich people | 5 | ✗ |
| | VCF0209 | Big Business | 20 | ✓ |

**Read test:** `pd.read_stata("anes_timeseries_cdf_stata_20260205.dta.gz")` → 73,745 × 1,030 in ~7 s.

---

## Task 3: Explore spending, race-opportunity, and religion variables

**Status:** Pending

Extend the extract with additional individual characteristics and policy-attitude variables after EDA on coverage, coding, and missing values.

### Individual characteristics to add

- [ ] `VCF0130` — Church attendance (1970–)
- [ ] Review `VCF0130a` — Church attendance (1990–); decide whether to harmonize with `VCF0130` or keep separate

### Race and opportunity (requested)

| Variable | Label |
|----------|-------|
| `VCF9037` | Government should ensure fair jobs for blacks |
| `VCF9038` | Guaranteed equal opportunity is not government job |
| `VCF9039` | Conditions make it difficult for blacks to succeed |
| `VCF9040` | Blacks should not have special favors to succeed |
| `VCF9041` | Blacks must try harder to succeed |
| `VCF9042` | Blacks gotten less than they deserve over the past few years |

### Social issues (requested)

Deferred to **Task 8** (LGBT rights / anti-discrimination battery: `VCF0876`–`VCF0878` and strength items).

### Federal spending (requested + related CDF variables)

**Primary list:**

| Variable | Label |
|----------|-------|
| `VCF0886` | Federal spending — poor/poor people |
| `VCF0887` | Federal spending — child care |
| `VCF0888` | Federal spending — dealing with crime |
| `VCF0889` | Federal spending — AIDS research/fight AIDS |
| `VCF0890` | Federal spending — public schools |
| `VCF0891` | Federal spending — financial aid for college students |
| `VCF0892` | Federal spending — foreign aid *(also Task 9)* |
| `VCF0893` | Federal spending — the homeless |
| `VCF0894` | Federal spending — welfare programs |
| `VCF9046` | Federal spending — food stamps |
| `VCF9047` | Federal spending — improve and protect the environment |
| `VCF9048` | Federal spending — space/science/technology |
| `VCF9049` | Federal spending — social security |
| `VCF9050` | Federal spending — assistance to blacks |

**Older harmonized spending scales (explore for time series):**

- `VCF0839` — Government services–spending scale
- `VCF0843` — Defense spending scale
- `VCF0828` — Should government cut military spending
- Party/candidate spending ratings: `VCF0541`, `VCF0542`, `VCF0549`, `VCF0550`, etc.

### Work plan

- [ ] EDA notebook: year coverage, value distributions, and missing codes for each variable (use `codebook/` HTML)
- [ ] Document harmonization notes where question wording or scale changed across years
- [ ] Add selected variables to `make_cdf_extract.py` with missing-code recoding in `utils.py`
- [ ] Update `explore_cdf_extract.md` with time-series plots for new variables

---

## Task 4: Investigate sample weights

**Status:** Pending

The extract uses `VCF0009z` (full-sample weight, 1970 type 0). See `codebook/extract_notes.md` (Task 4) for x/y/z and type selection.

### Weight variables to review

| Variable | Description |
|----------|-------------|
| `VCF0009x` / `y` / `z` | Weight type 0 — FTF, Web, full sample *(currently used: `VCF0009z`)* |
| `VCF0010x` / `y` / `z` | Weight type 1 — FTF, Web, full sample |
| `VCF0011x` / `y` / `z` | Weight type 2 — FTF, Web, full sample |
| `VCF9999` | Post-election weight, full sample |

### Questions to answer

- [x] What is the difference between weight types 0, 1, and 2? → `codebook/extract_notes.md` (Task 4); 1970 variable-level schemes; substantive 1970 design needs external docs
- [x] When should we use FTF (`x`), Web (`y`), or pooled full-sample (`z`) weights? → `codebook/extract_notes.md` (Task 4)
- [x] Is `VCF0009z` appropriate for pooled time-series analysis 1948–2024? → Yes for Type 0 variables and years outside 1970/2012+ splits; see `codebook/extract_notes.md`
- [ ] How do weights interact with variables that are post-election only (`VCF9999`)? *(Catalog: docs forthcoming; check ANES website)*
- [x] Document recommended weight column(s) for extract and analysis notebooks → `VCF0009z` in extract; see `codebook/extract_notes.md`

---

## Task 5: Build CDF variable metadata catalog

**Status:** Done

Read the codebook and/or Stata file **once** and produce a cached metadata file so notebooks don't re-parse the CDF or HTML on every run.

- [x] Write `codebook/extract_cdf_codebook.py` — parse HTML + Stata headers
- [x] Emit `codebook/extracted/anes_cdf_minimal.json` (+ dict + summary CSV)
- [x] Document in `codebook/codebook_plan.md`
- [x] Use catalog in `utils.py` to replace hard-coded `CORE_MISSING_CODES`

### GSS reference (CultureWar)

Closest match: **`~/CultureWar/codebook/extracted/gssrdoc_minimal.json`**

| File | Size | Role |
|------|------|------|
| **`gssrdoc_minimal.json`** | 6.8 MB | **Primary lookup** — flat dict, one entry per variable |
| `gssrdoc_simple.json` / `gssrdoc_dict.json` | ~10 MB | Richer metadata (description, modules, subjects, ballot info) |
| `variables.json` | 693 KB | PDF extraction — structured value/reserve codes, frequencies (2024 only) |
| `variables_summary.csv` | 33 KB | Quick index |

CultureWar uses `gssrdoc_minimal.json` in `notebooks/utils.py` for question text, value labels, and missing-code inference. ANES should follow the same **minimal-dict** pattern for cross-project compatibility.

**GSS minimal entry (actual format):**
```json
{
  "wrkstat": {
    "variable": "wrkstat",
    "question": "Last week were you working full time, part time, ...",
    "value_labels": "[1] working full time / [2] working part time / ... / [NA(n)] no answer",
    "years_available": "1972, 1973, 1974, ..."
  }
}
```

Note: GSS `value_labels` is a **slash-separated string**, not a JSON object. Missing codes appear inline as `[NA(n)]`, `[NA(i)]`, etc.

### ANES schema (GSS-compatible + ANES extensions)

**Primary output:** `codebook/extracted/anes_cdf_minimal.json` (mirror GSS naming with `anes_` prefix)

**Optional outputs:**
- `codebook/extracted/anes_cdf_dict.json` — full HTML fields (notes, valid_range, question variants)
- `codebook/extracted/anes_cdf_summary.csv` — one row per variable for quick grep
- `data/processed/anes_cdf_variable_stats.json` — empirical stats (years with data, min/max); separate one-pass scan

**Per-variable schema:**

```json
{
  "VCF0101": {
    "variable": "VCF0101",
    "label": "Respondent - Age",
    "question": "How old are you?",
    "value_labels": "[0] NA; DK; RF / [1] ... / [98] 98 years old / [99] 99 years old",
    "missing_codes": [0, 98, 99],
    "valid_range": "0-99",
    "years_available": "1948, 1952, 1954, ...",
    "notes": "Built from VCF0101. 1948 NOTE: ..."
  }
}
```

**Field mapping (GSS ↔ ANES):**

| Field | GSS (`gssrdoc_minimal`) | ANES (`anes_cdf_minimal`) | Source |
|-------|-------------------------|----------------------|--------|
| `variable` | ✓ | ✓ | Stata var name |
| `question` | ✓ | ✓ | HTML codebook question text |
| `label` | — (in `description` in simple dict) | ✓ short name | Stata `variable_labels()` |
| `value_labels` | ✓ string | ✓ string (same format) | Stata value labels → GSS-style string |
| `years_available` | ✓ | ✓ | HTML and/or one-pass data scan |
| `missing_codes` | — (embedded in value_labels) | ✓ explicit list | HTML “Missing-data codes” + Stata labels |
| `valid_range` | — | ✓ | HTML codebook |
| `notes` | — | ✓ | HTML harmonization / year notes |

Use **`question`** (not `question_text`) to match GSS. Keep `value_labels` as a string for compatibility; add a helper to parse it into `{code: label}` when needed.

**Example entries:**

```json
{
  "VCF0104": {
    "variable": "VCF0104",
    "label": "Respondent - Gender",
    "question": "...",
    "value_labels": "[1] Male / [2] Female / [3] Other (2016) / [0] NA; no Pre IW",
    "missing_codes": [0],
    "valid_range": "1-3",
    "years_available": "1948, 1952, ...",
    "notes": ""
  },
  "VCF0206": {
    "variable": "VCF0206",
    "label": "Thermometer - Blacks",
    "question": "...",
    "value_labels": "[97] 97-100 Degrees / [98] DK / [99] NA",
    "missing_codes": [98, 99],
    "valid_range": "0-97",
    "years_available": "1958, 1960, ...",
    "notes": "Group thermometer; 97 = 97-100 bucket. No 999 in raw group thermometers."
  }
}
```

### Sources (use both)

| Source | Provides |
|--------|----------|
| **HTML codebook** (`codebook/`) | `question`, `missing_codes`, `valid_range`, `notes`, harmonization |
| **Stata file** (`StataReader`, metadata only) | Authoritative variable list, `label`, value labels — no row data needed |

### Work plan

- [x] Write `codebook/extract_cdf_codebook.py` (or `notebooks/build_cdf_catalog.md`) — parse HTML + Stata headers
- [x] Emit `codebook/extracted/anes_cdf_minimal.json` matching GSS minimal schema
- [x] Validate against all 1,030 CDF variables
- [x] Use catalog in `utils.py` to replace hard-coded `CORE_MISSING_CODES` and thermometer rules
- [x] Document in `codebook/codebook_plan.md` (mirror `~/CultureWar/codebook/codebook_plan.md`)

---

## Task 6: Explore sexism, feminism, and women's role variables

**Status:** Pending

Extend the extract with attitude items on gender roles, feminism, and women's rights. Variable list below was compiled from `codebook/extracted/anes_cdf_minimal.json` (Task 5 catalog). Cross-reference GSS gender-role battery in `~/CultureWar` (`GENDER_ROLES_VARIABLES`) for analysis patterns; ANES has no direct workplace-discrimination items (`discaffm`, `discaffw`, `wksexism`) or working-mother item (`fechld`).

### GSS ↔ ANES concept map

| GSS (CultureWar) | ANES CDF analog | Notes |
|------------------|-----------------|-------|
| `fepol` | `VCF0834` | Equal-role scale (1972–2008); no long-run “stay out of politics” item |
| `fechld` | — | No working-mother / children-hurt item in CDF |
| `fefam` | `VCF0834` | Same 7-pt equal role vs. “women's place is in the home” scale |
| `fepres` | — | No husband achiever / wife homemaker item |
| `fework` | `VCF0834` | Equal role in business, industry, government |
| `fehire` | — | No hire/promote women item; `VCF0867` is race-based affirmative action |
| `discaffm` / `discaffw` / `wksexism` | — | No sex-discrimination-at-work items |
| *(backlash)* | `VCF9014`, `VCF9017` | “Gone too far pushing equal rights”; “worry less about how equal people are” |

### Already in extract (group thermometers)

| Variable | Label | Years | Notes |
|----------|-------|-------|-------|
| `VCF0225` | Women's Libbers / women's movement | 12 | Wording shifts 1970–1996 |
| `VCF0253` | Feminists | 10 | 1988–2024 |


### Primary attitude items (requested)

| Variable | Label | Years |
|----------|-------|-------|
| `VCF0834` | Women equal role scale (equal role vs. women's place is in the home) | 16 |

### Deferred (sparse years or separate topic)

| Variable | Label | Years | Reason |
|----------|-------|-------|--------|
| `VCF0833` | Favor or oppose Equal Rights Amendment | 3 | Too few years |
| `VCF0836` | Women should stay out of politics | 2 | Too few years |
| `VCF0837` | When should abortion be allowed | 4 | Abortion — later task |
| `VCF0838` | By law, when should abortion be allowed | 17 | Abortion — later task |

### Equal-rights backlash (catalog: egalitarianism series)

| Variable | Label | Years |
|----------|-------|-------|
| `VCF9014` | We have gone too far pushing equal rights | 11 |
| `VCF9017` | Country would be better off if we worried less about how equal people are | 13 |

*(Related egalitarianism items in same battery — explore only: `VCF9013`, `VCF9015`, `VCF9016`, `VCF9018`.)*

### Work plan

- [x] EDA notebook: year coverage, value distributions, and missing codes via `anes_cdf_minimal.json` lookup (`notebooks/eda_womens_role.md`)
- [x] Document harmonization notes in `codebook/extract_notes.md` (Task 6 section)
- [x] Add `VCF0834` + `VCF9014`/`VCF9017` to `make_cdf_extract.py` with missing-code recoding in `utils.recode_vcf_columns`

---

## Task 7: Explore moral foundations and traditional-values variables

**Status:** Pending

Extend the extract with attitude items for **Part 2 (Shifting moral foundations)** in `~/CultureWar/alternate_outline.md` — Authority/Sanctity decline, Care/Fairness rise, Liberty vs. tradition. Variable list compiled from `codebook/extracted/anes_cdf_minimal.json` (Task 5 catalog). ANES coverage is thinner than GSS for sex (`premarsx`, `teensex`, …) and abortion batteries; this task focuses on the **traditional-values / moral-change** items and related religion scales.

**Related tasks:** Task 3 (church attendance `VCF0130`, social issues).

**Weights:** See `codebook/extract_notes.md` (Task 4) for x/y/z and 1970 type selection.

### MFT ↔ ANES concept map

| MFT foundation | CultureWar chapters | ANES CDF items |
|----------------|---------------------|----------------|
| **Authority / Sanctity** | Ch. 4 (sex norms), Ch. 6 (religion in public life) | `VCF0851`–`VCF0854`, `VCF0845`/`VCF0850`, `VCF9043`/`VCF9051` |
| **Liberty / oppression** | Ch. 5 (autonomy), Ch. 6 (speech) | `VCF0852`, `VCF0854` *(personal moral standards)* |
| **Care / harm** | Ch. 4–5 | *(sparse in CDF; abortion `VCF0837`/`VCF0838` deferred; see Task 3 social issues)* |

### Traditional-values battery (catalog: `VCF0851`–`VCF0854`)

Administered as a block from 1986; question order varied by study.

| Variable | Label | Years | MFT |
|----------|-------|-------|-----|
| `VCF0853` | More emphasis on traditional family ties | 14 | Authority / Sanctity |
| `VCF0851` | Newer lifestyles contribute to society breakdown | 12 | Authority / Sanctity |
| `VCF0852` | Adjust view of moral behavior to changes | 14 | Liberty *(pro-change)* |
| `VCF0854` | Tolerance of different moral standards | 12 | Liberty *(tolerance)* |

### Religion and public morality (catalog)

| Variable | Label | Years | MFT |
|----------|-------|-------|-----|
| `VCF0845` | Authority of the Bible (1964–1990 wording) | 7 | Authority / Sanctity |
| `VCF0850` | Authority of the Bible (1984– wording) | 12 | Authority / Sanctity |
| `VCF0846` | Is religion important to respondent | 17 | Authority / Sanctity |
| `VCF0847` | How much guidance from religion | 15 | Authority / Sanctity |
| `VCF9043` | School prayer allowed (4-category) | 7 | Authority / Sanctity |
| `VCF9051` | School prayer allowed (2-category) | 5 | Authority / Sanctity |

*(Church attendance `VCF0130` / `VCF0130a` — behavior, not attitude — is under Task 3. Explore harmonization: `VCF9043` vs. `VCF9051`; `VCF0845` vs. `VCF0850`.)*

### Work plan

- [ ] EDA notebook: year coverage, value distributions, and missing codes via `anes_cdf_minimal.json` lookup
- [ ] Document harmonization notes (`VCF0851`–`VCF0854` block order; `VCF0845`/`VCF0850`; `VCF9043`/`VCF9051`)
- [ ] Add traditional-values battery + selected religion items to `make_cdf_extract.py` with missing-code recoding in `utils.py`
- [ ] Update `explore_cdf_extract.md` with time-series plots; compare to GSS Part 2 items where concepts overlap (`divlaw`, `pornlaw`, `prayer`, etc.)

---

## Task 8: Explore LGBT rights and anti-discrimination attitudes

**Status:** Done

Extend the extract with attitude items on job-discrimination protection, military service, and adoption rights for gay/lesbian couples. Variable list compiled from `codebook/extracted/anes_cdf_minimal.json` (Task 5 catalog). Cross-reference group thermometer **`VCF0232`** (Gays and Lesbians, already in extract) and CultureWar Part 1 sexuality/gender chapters where relevant.

**Related tasks:** Task 3 (social issues — deferred here); Task 6 (women's role / equal rights).

### Already in extract (group thermometer)

| Variable | Label | Years | Notes |
|----------|-------|-------|-------|
| `VCF0232` | Gays and Lesbians | 14 | Feeling thermometer; see Task 2 |

### Primary attitude items (requested)

| Variable | Label | Years |
|----------|-------|-------|
| `VCF0876` | Law to protect homosexuals against job discrimination (favor / oppose) | 10 (1988–2024, even years) |
| `VCF0876a` | Strength of position on job-discrimination law | 10 (same waves) |
| `VCF0877` | Gays in the military — allow / not allow | 6 (1992–2012, even years) |
| `VCF0877a` | Strength of position on military service | 6 (same waves) |
| `VCF0878` | Gay/lesbian couples permitted to adopt | 8 (1992, 2000, 2004, 2008, 2012, 2016, 2020, 2024) |

**Catalog harmonization notes (for EDA):**

- **`VCF0876` / `VCF0876a`:** 1 = favor, 5 = oppose (main item); strength item 1–2 favor, 4–5 oppose. Code 8 = DK (1988 “depends” on main item). 2012: asked of random ½ sample.
- **`VCF0877` / `VCF0877a`:** 1 = allow service, 5 = don't allow; strength item parallels `VCF0876a`. 2012: random ½ sample.
- **`VCF0878`:** 1 = yes (permit adoption), 5 = no. Gap in 1996 (not 2016 — catalog `years_available` omits 2016 but data are present).
- Wording shifts (*homosexuals* vs. *gays and lesbians*); see catalog `question` text.

### Work plan

- [x] EDA notebook: year coverage, value distributions, and missing codes via `anes_cdf_minimal.json` lookup (`notebooks/eda_lgbt_rights.md`)
- [x] Document harmonization notes in `codebook/extract_notes.md` (Task 8 section)
- [x] Add `VCF0876`, `VCF0876a`, `VCF0877`, `VCF0877a`, `VCF0878` to `make_cdf_extract.py` with missing-code recoding in `utils.recode_vcf_columns`
- [x] Rebuild extract (`make run_extract`) and sync to CultureWar if needed

---

## Task 9: Explore immigration, immigrant-threat, and group-stereotype variables

**Status:** Done

Extend the extract with immigration volume / economic-threat attitudes, optional Hispanic-origin demographics, and hardworking–lazy stereotype scales. Variable list compiled from CultureWar candidate notes and checked against `codebook/extracted/anes_cdf_minimal.json` (Task 5 catalog). Cross-reference thermometers already in the extract: **`VCF0217`** (Chicanos/Hispanics), **`VCF0227`** (Asian-Americans), **`VCF0233`** (illegal aliens / illegal immigrants).

**Related tasks:** Task 3 (federal spending — `VCF0892` also listed there); Task 8 (social-issue battery pattern).

**CDF coverage notes (not in extract; not available for long-run use):**

- No durable **“legal immigrants”** or generic-immigrants thermometer besides **`VCF0233`** (illegal aliens / illegal immigrants).
- No long-run English-only / official-English *attitude* item (interview language `VCF0018a`/`b` is administration metadata, not opinion).
- Stereotype battery in the CDF is **hardworking↔lazy only** (`VCF9270`–`VCF9273`). No intelligent–unintelligent companion scales for these groups turned up in the catalog.

### Already in extract (related thermometers)

| Variable | Label | Years | Notes |
|----------|-------|-------|-------|
| `VCF0217` | Chicanos/Hispanics | 15 | Group thermometer |
| `VCF0227` | Asian-Americans | 9 | Group thermometer |
| `VCF0233` | Illegal Aliens / illegal immigrants | 9 | Closest immigrant thermometer in CDF |

### High priority (immigration volume / threat)

| Variable | Label | Waves (catalog) | Notes |
|----------|-------|-----------------|-------|
| `VCF0879` | Increase/decrease number of immigrants (6-category) | 1992–1998, 2004–2024 (10) | Main ANES volume series; GSS `letin*` crosswalk |
| `VCF0879a` | Same item, 4-category collapse | 1992–2000, 2004–2024 (11) | Prefer one of `VCF0879` / `VCF0879a` for APC; keep both for coding checks |
| `VCF9223` | Immigration levels take jobs from people already here | 2004–2024 (6) | Economic threat; pairs with GSS `immjobs` / `immameco` |

### Medium priority (stereotype trait scales)

| Variable | Label | Waves (catalog) | Notes |
|----------|-------|-----------------|-------|
| `VCF9270` | Whites hardworking↔lazy (7-pt) | 1992–2024 (gappy) | Full battery kept |
| `VCF9271` | Blacks hardworking↔lazy (7-pt) | 1992–2024 (gappy) | Full battery kept |
| `VCF9272` | Hispanic-Americans hardworking↔lazy (7-pt) | 1992–2024 (gappy; 9) | Companion to Hispanic thermometer |
| `VCF9273` | Asian-Americans hardworking↔lazy (7-pt) | 1992–2024 (gappy; 8) | Same battery for Asians |

### Low priority

| Variable | Label | Waves (catalog) | Notes |
|----------|-------|-----------------|-------|
| `VCF0892` | Federal spending: foreign aid | 1990–2008 (6) | Cosmopolitanism / overseas moral circle — thin; ends 2008. Also listed under Task 3 spending. |

### Optional demographics (subgroup splits)

| Variable | Output name | Waves (catalog) | Notes |
|----------|-------------|-----------------|-------|
| `VCF0108` | `hispanic` | 1978–2024 | Subgroup splits of thermometers / stereotypes |
| `VCF0107` | `hispanic_type` | 1978–2024 | Finer Hispanic subgroup; code 4 (Hispanic DK type) kept as substantive |

### Work plan

- [x] EDA notebook: year coverage, value distributions, and missing codes via `anes_cdf_minimal.json` (`notebooks/eda_immigration.md`)
- [x] Decide primary immigration-volume coding (`VCF0879` vs `VCF0879a`) and whether to keep both; document in `codebook/extract_notes.md`
- [x] Confirm whether to add full hardworking–lazy battery (`VCF9270`–`VCF9273`) or Hispanic/Asian only → **full battery**
- [x] Add selected variables to `make_cdf_extract.py` with missing-code recoding in `utils.recode_vcf_columns` (and core rename map if Hispanic demogs are kept under short names)
- [x] Rebuild extract (`make run_extract`) and sync to CultureWar if needed

---

## Task 10: Midterm Pilot studies — inventory and separate extract

**Status:** Extract built (watchlist / no-pool decision remain)  

Post-2002 midterms are **not** in the Time Series CDF. CultureWar Task 98 documented that **1974–2002 midterms are already in the CDF extract**. This task built a **separate** Pilot extract for mode/design comparison before any combine decision.

**Related:** CultureWar Task 98 midterm matrix; book VCFs in `~/CultureWar/notebooks/utils.py`; CDF Tasks 2, 6, 8, 9. CultureWar handoff: `codebook/anes_pilot_panel_extracts_inventory.md`.

**Done:** Local Pilots 2016/2018/2019/2022 under `data/raw/midterm_pilots/`; crosswalk + `eda_pilot_inventory.md`; `make run_pilot_extract` → `data/interim/anes_pilot_extract.hdf` (8,450 × 27); notes in `extract_notes.md`.


### Full ANES Pilot inventory (Data Center)

Many Pilots exist beyond midterm years. **Start with the local set (2022, 2019, 2018, 2016)** to see whether book-variable overlap is useful before downloading older studies.

| Pilot study | Midterm calendar year? | Local status (2026-08-15) |
|-------------|------------------------|---------------------------|
| 2024 Pilot | No | Not yet acquired (may exist under `~/WorldviewANES`) |
| 2022 Pilot | **Yes** | In `data/raw/midterm_pilots/2022/` |
| 2019 Pilot | No | In `…/2019/` |
| 2018 Pilot | **Yes** | In `…/2018/` |
| 2016 Pilot | No | In `…/2016/` (SPSS `.sav` only so far) |
| 2006 Pilot | **Yes** | Not yet acquired |
| 2000, 1998, 1997, 1995, 1993, 1991, 1989, 1987, 1985, 1983, 1979 | Mixed / early | Deferred until modern Pilots prove useful |
| *(no 2014 or 2010 Pilot on this list)* | Midterms 2014, 2010 | No Pilot parallel — gap remains |

**Strategy:** Inventory + small extract from **2022 → 2018 → 2019/2016** first. Only then pull **2006** and earlier Pilots if overlap warrants it. Site blocks `wget` (Cloudflare 403) — hand download via browser.

### Background (do not rebuild CDF for historical midterms)

| Year | In CDF extract? | Notes |
|------|-----------------|-------|
| 1974, 1978, 1982, 1986, 1990, 1994, 1998, 2002 | **Yes** | Already in `anes_extract_*.hdf`; use year matrix for chapter notes |
| 2006, 2018, 2022 | Midterms with Pilots | Use Pilot files (separate extract) |
| 2010, 2014 | Midterms **without** Pilots on Data Center list | No Pilot parallel |
| 2026 Pilot | Not yet | Watchlist until questionnaire/data exist |

**Mode caveat:** Recent Pilots (e.g. 2022) are opt-in online (YouGov), not Time Series FTF/mixed. Treat as **parallel / sensitivity**, not pooled with CDF APC stacks by default.

### Preferred microdata format

| Format | Preference | Why |
|--------|------------|-----|
| **Stata `.dta`** | **Preferred** | Matches CDF pipeline (`pd.read_stata`); value labels via `StataReader` |
| **SPSS `.sav`** | Acceptable | `pyreadstat` already in `requirements.txt`; use when no `.dta` (2016) |
| **CSV** | Last resort | Easy to read but **drops value labels** / type metadata — keep as backup only |

For **2016**: prefer Stata if ANES offers it; otherwise use **`.sav`** (already local). No need for CSV if `.sav` works.

### Scope

1. **Start local:** inventory book-overlap for 2022, 2018, 2019, 2016 before fetching more Pilots.
2. **Inventory** Pilot items that map to book-tracked CDF variables (thermometers, stereotypes, immigration, gay rights, women’s role, religion FTs, etc.).
3. **Build a second extract** (HDF + labels) kept separate from the CDF extract — same conceptual columns where possible, Pilot source names documented in a crosswalk.
4. **Defer combining** CDF + Pilot until after mode-effect diagnostics.
5. **Later (if useful):** 2006 Pilot and older series from the full list above.

### Suggested raw-data layout

Keep CDF and Pilots side by side under `data/raw/` (already gitignored). One folder per study; copy/symlink 2022 from `~/WorldviewANES` first.

```text
data/raw/
  INVENTORY.md                          # update with Pilot rows
  anes_timeseries_cdf_stata_20260205.*  # existing CDF
  midterm_pilots/
    README.md                           # download provenance, ANES study IDs, access notes
    2022/
      anes_pilot_2022_stata_*.dta       # from ~/WorldviewANES (or official zip)
      anes_pilot_2022_csv_*.csv
      anes_pilot_2022_*questionnaire*.pdf
      anes_pilot_2022_*codebook*.pdf    # or userguide
      NOTES.md                          # download date, version stamp, 403/manual notes
    2018/
      …                                 # same pattern when acquired
    2014/
    2010/
    2006/
```

**2022 local source (preferred):**  
`~/WorldviewANES/anes_pilot_2022_stata_20221214.dta` (+ csv, questionnaire, userguide/codebook PDFs). Site wget returned 403 in Task 98 notes — hand download is expected for other years.

**Processed / interim (separate from CDF):**

```text
data/interim/anes_pilot_extract.hdf               # stacked 2022+2019+2018+2016
data/interim/anes_pilot_extract_labels.csv
data/processed/anes_pilot_cdf_crosswalk.csv       # book VCF ↔ Pilot var name(s)
notebooks/make_pilot_extract.py                   # parallel to make_cdf_extract.py
notebooks/eda_pilot_inventory.md                  # coverage vs SELECTED_VALUES
```

Do **not** overwrite or merge into `anes_extract_anes_timeseries_cdf_*.hdf`.

### Inventory target (book VCFs)

Crosswalk against CultureWar `SELECTED_VALUES` / ANES book labels, including at least:

| CDF (book) | 2022 Pilot analogue (Task 98 skim) | Priority |
|------------|--------------------------------------|----------|
| `VCF0217` | `fthisp` | High |
| `VCF0227` | `ftasian` | High |
| `VCF0206` / `VCF0207` | `ftblack1/2`, `ftwhite1/2` | High |
| `VCF0253` | `ftfem` | High |
| `VCF9270`–`VCF9273` | `swhwork`, `sblwork`, `slawork`, `saswork` (+ intelligent scales in Pilot only) | High |
| `VCF0233` | — (salience/ownership only) | Note gap |
| `VCF0232`, religion FTs, `VCF0879`/`a`, `VCF9223`, `VCF0892`, gay-rights VCFs | — or weak analogues | Document misses |

Full list: grep `VCF` keys in `~/CultureWar/notebooks/utils.py` (`SELECTED_VALUES`, `VARIABLE_LABELS` / ANES sections).

### Work plan

- [x] Create `data/raw/midterm_pilots/` layout + README; copy/link 2022 files from `~/WorldviewANES`
  - [x] Layout + README; **2022** from WorldviewANES; **2018**, **2019**, **2016** from `~/Downloads`
  - [x] Record full Pilot list on board; **defer** older downloads until modern set proves useful
  - [ ] Optional later: **2006** Pilot (midterm); then 2000→1979 only if needed
  - [x] 2014 / 2010: no Pilot on Data Center list — documented as gaps
- [x] Update `data/raw/INVENTORY.md` with Pilot studies (year, N, mode, file versions)
- [x] EDA / inventory notebook: map Pilot items → book VCFs (`notebooks/eda_pilot_inventory.md`); write `data/processed/anes_pilot_cdf_crosswalk.csv`
- [x] Implement `notebooks/make_pilot_extract.py`; stacked HDF for 2022/2019/2018/2016 (`make run_pilot_extract`)
- [x] Document mode/design caveats + extract decisions in `codebook/extract_notes.md` (Task 10 section)
- [ ] Watchlist: 2024 Pilot, 2026 Pilot when released
- [ ] **Do not** append Pilot rows to CDF APC stacks until CultureWar decides after parallel diagnostics

---

## Task 11: 2016–2020–2024 Panel Merged Study — separate extract

**Status:** Extract built (EDA optional; sync when ready)  
**Study:** [ANES 2016-2020-2024 Panel Merged Study](https://electionstudies.org/data-center/2016-2020-2024-panel-merged-study/)  
**Related:** Task 10 (Pilots); Task 12 (harmonization); CultureWar book VCFs; CDF Tasks 2/6/8/9.

**Done:** Raw under `data/raw/panel_2016_2020_2024/`; `make run_panel_extract` → long HDF (8,517 × 43) with book VCFs + transgender battery; inventory + harmonization docs for CultureWar.


### Why this extract

Same respondents interviewed in **2016, 2020, and 2024** Time Series waves (merged wide file). Stronger book-variable overlap than midterm Pilots (illegal-immigrant FT, gays FT, religion FTs, immigration levels, takes-jobs, gay policy). Also carries **transgender** items that the CDF book stack mostly lacks. Keep **separate** from CDF and Pilot HDFs — within-person panel ≠ independent cross-sections for APC pooling.

### Local files (2026-08-15)

```text
data/raw/panel_2016_2020_2024/
  README.md
  anes_mergedfile_2016-2020-2024panel_20260519.sav   # from ~/Downloads zip
  REPEATED_VARIABLES_2016_20_24.csv                  # staff repeated-item list
  anes_timeseries_{2016,2020,2024}_*codebook*.pdf    # year TS userguides
```

**N (wide):** 2,839 cases × ~5,379 columns (V16* / V20* / V24*). SPSS `.sav` only in this download (acceptable; `pyreadstat`).

### Inventory verdict (from REPEATED_VARIABLES + codebooks)

| Book / topic | In repeated panel vars? | Notes |
|--------------|-------------------------|-------|
| Feminists, Blacks, Whites, Hispanics, Asian, Gays, **Illegal immigrants**, Jews, Muslims, Christian fundamentalists FTs | Yes (all three waves) | Maps to book `VCF02xx` / `VCF9267` |
| Immigration levels (`VCF0879`), takes jobs (`VCF9223`) | Yes | All three |
| Hardworking–lazy Whites/Blacks/Asians | Yes | Hispanics HW: **2020+2024 only** |
| Gay job discrimination + adopt (`VCF0876`/`0878`) | Yes | All three |
| Gay marriage | Yes (panel column `gay_marriage`) | Not a CDF book VCF |
| Gays in military (`VCF0877`) | No | Replaced by **transgender military** (2020+2024) |
| Equal role, women’s movement FT, Protestants/Catholics FTs, foreign aid | Missing / not in recent TS | Same gaps as modern TS |

### Transgender items (priority for this extract)

Include even when not in CultureWar `SELECTED_VALUES` yet — panel is the natural place to track them.

| Extract column | Concept | 2016 | 2020 | 2024 | In ANES repeated list? |
|----------------|---------|------|------|------|------------------------|
| `ft_transgender` | Feeling thermometer: transgender people | `V162111` | `V202172` | `V242151` | Yes (all three) |
| `trans_bathroom` | Bathroom / gender-identity policy | `V161228` | `V201409` | `V241370` | Yes |
| `trans_bathroom_str` / `_sum` | Strength / summary | `V161228a`/`x` | `V201410`/`411x` | `V241371`/`372x` | Yes |
| `trans_military` (+ str/sum) | Serve in US Armed Forces | — | `V202388`… | `V242362`… | Yes (2020;2024) |
| `trans_discrim` | Discrimination against transgender people | `V162366` | `V202536` | `V242558` | Yes |
| `trans_know_someone` | Know transgender family/friends/etc. | — | `V202473` | `V242510` | Yes (2020;2024) |
| `trans_sports_ban` | Ban transgender girls from K–12 girls’ sports | — | — | `V241373` | **2024-only** (not in repeated CSV) |

Optional later (not required for v1 extract): SPS thermometer `V241719`; paper/sports summary `V242458x`; R is transgender `V241552`.

### Extract design

1. **Input:** wide SPSS merged file.  
2. **Reshape to long:** one row per `panel_id` × `year` ∈ {2016, 2020, 2024}.  
3. **IDs / weights:** keep wave `caseid`; weights = post-election panel weights where available (`V160102` full-sample post in 2016; `V200011b` 2016–2020 panel post; `V240106b` 2016–2024 panel post). Document weight caveats in `extract_notes.md`.  
4. **Demogs:** age, birth year (or year−age), sex/gender, race summary per wave; `cohort = year − age`.  
5. **Outcomes:** book VCF names where matched; panel-only names for trans / gay marriage / unauthorized-immig / border security.  
6. **Cleaning:** thermometers keep 0–100 (negatives → NA); other scales drop codes `< 0`.  
7. **Outputs:** `data/interim/anes_panel_extract.hdf` + `_labels.csv`; log `notebooks/logs/extract_panel.txt`.  
8. **Do not** merge into CDF HDF or append to CultureWar APC stacks by default.

### Work plan

- [x] Acquire merged `.sav` + repeated-variables list + year codebooks → `data/raw/panel_2016_2020_2024/`
- [x] Inventory book overlap + transgender battery (this task write-up)
- [x] Implement `notebooks/make_panel_extract.py` + `make run_panel_extract`
- [x] Document conventions / trans codebook notes in `codebook/extract_notes.md` (Task 11)
- [x] Update `data/raw/INVENTORY.md`
- [ ] Optional EDA: within-person change on `ft_transgender`, bathroom, military, sports ban
- [ ] **Do not** pool panel rows with CDF/Pilot APC stacks until CultureWar decides

---

## Task 12: Harmonize Pilot/Panel extract coding (from plan)

**Status:** Done (H1–H4; sync to CultureWar when ready)  
**Plan doc:** [`codebook/anes_pilot_panel_harmonization.md`](codebook/anes_pilot_panel_harmonization.md)  
**Related:** Tasks 10–11; inventory [`codebook/anes_pilot_panel_extracts_inventory.md`](codebook/anes_pilot_panel_extracts_inventory.md); CultureWar Task 99

### Principle

Harmonize **in the extract builders** when one CultureWar column name would mean different things across waves. Keep raw columns for audit; add derived columns with **fixed** meaning. CultureWar only chooses which side is `y=1` in `SELECTED_VALUES`.

### Completed

| ID | Result |
|----|--------|
| **H1** | `trans_bathroom_restrict` in panel extract (1 = restrictive, 0 = inclusive); raw bathroom cols kept |
| **H2** | `trans_bathroom_sum` documented as audit-only; use H1 for book series |
| **H3** | Pilot `immig_volume` stays non-`VCF0879` (confirmed in inventory) |
| **H4** | Pilot 2016 `lazy_*` stay off `VCF9270`–`72` (confirmed in inventory) |

### Work plan

- [x] Implement **H1** in `notebooks/make_panel_extract.py`; rebuild (`make run_panel_extract`)
- [x] Record **H1** mapping in `anes_panel_extract_labels.csv` and inventory; CultureWar uses `trans_bathroom_restrict`
- [x] Close **H2** as “use H1; `_sum` audit-only” in harmonization plan + inventory
- [x] Confirm **H3** / **H4** in inventory + Done in harmonization plan
- [x] Note in `codebook/extract_notes.md` (Task 12 / panel bathroom)
- [ ] Sync rebuilt panel HDF + labels (+ inventory / harmonization) to CultureWar when ready

### Out of scope (watchlist only)

Demog coding vs CDF (**W1**), weight series (**W2**), 2024-only sports ban (**W3**), military/discrim/`ft_transgender` consistency (**W4**–**W5**). Promote to **H** items only if we find a polarity bug.

---
