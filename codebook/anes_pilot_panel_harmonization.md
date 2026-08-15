# ANES Pilot & Panel extracts — harmonization plan

**Status:** Living checklist (add issues as we find them)  
**Date opened:** 2026-08-15  
**Owners:** ExtractANES builders (`make run_pilot_extract` / `make run_panel_extract`); CultureWar consumes the result  
**Related:** [`anes_pilot_panel_extracts_inventory.md`](anes_pilot_panel_extracts_inventory.md), ExtractANES `codebook/extract_notes.md`, ExtractANES **Task 12** (`project_board.md`), CultureWar **Task 99**

## Principle

Harmonize **in the extract** when the same CultureWar column name would otherwise mean different things across waves or vs the CDF. Keep raw study columns for audit; add derived columns with **fixed** meanings. CultureWar should only choose which side is `y=1` in `SELECTED_VALUES`, not undo polarity flips.

Do **not** silently pool Pilot/Panel rows into CDF APC stacks (mode / panel dependence) — that is a design decision, not a coding fix.

---

## Open issues

_(none)_

---

## Watchlist (not coding flips, but extract caveats)

These are not polarity bugs, but they affect how CultureWar should treat columns. Promote to numbered **H** issues if we decide to change the extract.

| ID | Topic | Note |
|----|--------|------|
| W1 | Demography (`sex`, `race`) | Wave-/study-specific; not necessarily CDF `VCF0104` / `VCF0106`. Subgroup fits need a documented map before comparing to CDF. |
| W2 | Weights | Different series per Pilot year and per Panel wave; never one global weight. |
| W3 | Panel `trans_sports_ban` | 2024-only — fine in extract; not a multi-year APC series. |
| W4 | Panel military / discrim / know someone | Coding looks **consistent** across waves that field them; CultureWar chooses `y=1` (e.g. oppose allow military = restrictive). No extract harmonization known yet. |
| W5 | `ft_transgender` | Thermometer 0–100; missing already cleaned. No cross-wave polarity issue found. |

---

## Workflow when adding a new issue

1. Confirm with year codebooks (raw ANES names in `anes_*_extract_labels.csv`).
2. Add an **H** section here: risk, proposed derived column, keep-raw vs replace.
3. Implement in ExtractANES (`make_panel_extract.py` / `make_pilot_extract.py`), rebuild HDF + labels, sync to CultureWar.
4. Point CultureWar `SELECTED_VALUES` at the **derived** column; mark status Done.

---

## Done

### H1. Panel `trans_bathroom` — polarity flip (2024 vs 2016/2020) — Done 2026-08-15

| | 2016 / 2020 (`V161228` / `V201409`) | 2024 (`V241370`) |
|--|--------------------------------------|------------------|
| Question form | Forced choice: birth-gender bathroom vs identity bathroom | Favor / oppose / neither *allowing* identity bathrooms |
| Code `1` | Restrictive (birth-gender bathrooms) | **Favor** allowing identity bathrooms |
| Code `2` | Inclusive (identity bathrooms) | **Oppose** allowing |
| Code `3` | — | Neither |

**Implemented:** Keep raw `trans_bathroom` (+ `_str` / `_sum`). Derived **`trans_bathroom_restrict`** in `make_panel_extract.py`:

- 1 = restrictive, 0 = inclusive, NaN = neither / missing  
- 2016/2020: `1→1`, `2→0`  
- 2024: `2→1`, `1→0`, `3→NaN`

CultureWar should model `trans_bathroom_restrict`, not raw `trans_bathroom`. Mapping also in `anes_panel_extract_labels.csv` (`kind=derived_binary`).

### H2. Panel `trans_bathroom_sum` — scale and polarity change — Done 2026-08-15

Leave `_sum` as wave-specific **audit only**. Labels CSV notes warn not to use as cross-wave APC outcome. Book series → **H1** binary.

### H3. Pilot `immig_volume` vs CDF `VCF0879` — Done 2026-08-15 (confirm naming)

Pilot volume stays `immig_volume` (7-cat). Not renamed to `VCF0879`. Inventory states any future CDF↔Pilot figure needs an explicit category collapse.

### H4. Pilot 2016 lazy stereotypes vs `VCF9270`–`72` — Done 2026-08-15 (confirm naming)

2016 `lazy_*` remain Pilot-only (5-pt). Not mapped onto book/CDF 7-pt columns. Inventory reiterates the rule.
