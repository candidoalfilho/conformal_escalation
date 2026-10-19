# Review round 3 (draft 3, October 2026)

Four reviewer passes on `paper/main_ifac.pdf` (A statistics, B PHM, C embedded, D editor), followed by a verification pass on draft 3b. Full reviews: `review3_A_stats.md`, `review3_B_phm.md`, `review3_C_embedded.md`, `review3_D_editor.md` (this folder).

## Scores

| reviewer | criterion | round 2 | round 3 | round 3b |
|---|---|---|---|---|
| A (statistics) | soundness / clarity | 3 / 4 | 4 / 4 | **5 / 4** |
| B (PHM) | significance / clarity | 4 / 3.5 | 4.5 / 4 | — |
| C (embedded) | soundness / usefulness | 3 / 3 | 4 / 4 | — |
| D (editor) | clarity / reproducibility | 3 / 2 | 4 / 4 | 4 / 4 (5 once the repository URL replaces the placeholder) |

Novelty is not scored above 3–4 by any reviewer and cannot be raised by editing: CADS, Conformal Cascade and conformal alignment already gate *model* cascades with prediction-set size; the contribution here is the sensor-cascade framing, the shift measurement and the commissioning number.

## What changed between draft 2 and draft 3

Code
- `cmlib.conformal_qhat`: exact ⌈(n+1)(1−α)⌉-th smallest score (was one rank above). All E3–E6 and X1–X3 results regenerated.
- E3 and `run_paderborn_extra.coverage_rows` write per-class coverage (`covclass_<k>`).
- `energy_params.py`: TIDA-010249 at 100 mW (boost losses), `mcu_acquisition_mj()` (light sleep + eight FIFO drains over SPI at 10 MHz ≈ 2.2 mJ per MEMS window), FIFO/SPI constants.
- `make_tables_ifac.py`: frontier as `table*`; gap table with LR/RF split, healthy/faulty column and current-tier-only bearing row; factor table merged with failure modes as `table*` (coverage + macro-F1 per factor, singleton/empty fractions under shift); new gate-under-shift table; recalibration table without the constant source column; energy table with MCU-during-acquisition rows; stale macros removed.
- `build_notebooks.py`: exact-quantile statement, recording-level exchangeability caveat, pooled-across-fold declaration, weighted-quantile normalisation, "threshold gate" terminology, per-class coverage cells, physics paragraph, labelling caveat, FIFO-drain energy text, all narrative numbers re-synced to the regenerated CSVs.

Manuscript (6 pages, IFAC class)
- Sec. 2.1: hierarchical-conformal caveat (Dunn et al. 2023; Lee et al. 2023), Barber et al. TV bound with normalised weights.
- Sec. 2.2: singleton ⇔ threshold only when 1−q̂ > 0.5; observed q̂ ranges; comparison declared empirical; Mondrian / scheduling-variable sentence for the FDI audience.
- Sec. 2.3: active-sensing restriction, total-basis compute, 1.9× cycles beside 4.6× ops, in-drive free current with training-data caveat, MCU state during acquisition (FIFO drains), duty-cycle average power.
- Sec. 3: KAIST channels and rates (25.6 kHz, three CTs, U phase), severities pooled per class, "three of four" operating points, 639 of 640, combined class with three bearings, resampling discards the envelope band, feature list, α grid, hyper-parameters, pooled-across-fold calibration declared.
- Sec. 4: contributions split into four sentences; gate-delta table replaced by a sentence; healthy/faulty reading of marginal coverage (KAIST healthy class 38 % in distribution); modality-specific direction of the silent failure; physics paragraph rewritten; "five restore to within 0.01, three to within about 0.05"; labelling caveat and healthy-only case; weighted CP explained by the target share of the normalised weight; damage-origin transfer as a 3-class model on 4 classes.
- Discussion: overclaims softened (per-speed calibration / speed normalisation untested; commercial wake-on-threshold cascade *expected* to share the sensitivity).
- Terminology unified: threshold gate; operating-point shift; recording-grouped / bearing-grouped ("in" / "bearing" / "shift" in tables); tier; LR / RF / LAC / APS defined at first use.
- Figure removed for space (coverage curves and per-point coverage are in the notebooks); "Code and data" paragraph; AI declaration in the template wording; abstract 96 words; "33–70 %" (LR/RF range) replaces "33–55 %".

## Still open (not fixable by editing)

- Repository URL and commit hash (red placeholder), co-authors, funding.
- Reviewer C: the FIFO-drain figure assumes SPI at 10 MHz and the WAITI floor during drains; a measurement on the board would replace it, as would a CCOUNT reading for the FFT.
- Reviewer B: speed-normalised (order-tracked) features and healthy-only (Mondrian) recalibration are untested controls; both are stated as such.
- Reviewer D: tables sit at resizebox ≈ 0.75 (≈ 6 pt), readable but borderline in print.
