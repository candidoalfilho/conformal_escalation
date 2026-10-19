# Re-review (v2): "Calibrate Where You Deploy" (IFAC SAFEPROCESS 2027)

Checked against `main_ifac.tex`, `tables_ifac/*.tex`, `numbers_ifac.tex`, the 6-page PDF and, where no table backs a claim, the result CSVs.

## 1. Status of the first-round issues

| # | Issue | Status | Justification |
|---|---|---|---|
| 1 | "Radial force neither" | Addressed | Now "radial force degrades the vibration tiers moderately (0.64–0.73 LR, 0.27–0.40 RF)" everywhere; the "load varies but speed does not" claim is gone. 4.4 still omits radial force on the current tier (0.66/0.46). |
| 2 | Tables 6 vs 7 disagree | Addressed | Regenerated on the same seeds/grid; ρ=1 vs pooled and ρ=0 vs target agree to ≤0.009 in all six rows. |
| 3 | Failure mode mis-scoped | Addressed | 4.3 scopes LR/current (80 % singletons, 50 % coverage), RF/current (62 % empty), RF/vibration (silent, 4.7); contribution (iii) rewritten. Still no table and no α stated. |
| 4 | Table 4 tier ambiguity | Addressed | Caption names the tier per dataset and "50.0 / 32.6 % (LR / RF)"; bearing-grouped worst gap −0.098 now in the text. |
| 5 | Sensor-escalation premise | Addressed | Reframed honestly: current-first saves acquisition energy only with free inverter current; 4.7 gives 0.18 vs 0.53 mJ/window at 34 % escalation. |
| 6 | Energy model | Addressed | 42.9 mJ MCU row replaced by 0.039 mJ with the sleep-during-acquisition duty model; ratio stated as 7–25×. Arithmetic checks. |
| 7 | No CIs | Partially | Table 2 has 95 % cluster-bootstrap CIs; Tables 4–7 none; Fig. 2 shows ±1 s.d. |
| 8 | Class coverage at small k | Partially | Admitted ("k=1 results are partly an artefact") but not re-run stratified, and 4.5 still argues from k=1. |
| 9 | Unlabelled baseline | Not addressed | Cited in Limitations as "remain to be compared"; "only target labels restore coverage" still rests on Han & Qu. |
| 10 | Gate equivalence | Addressed | 2.2 gives the top-two condition and the 1−q̂ ≥ 0.5 reduction; 4.2 still repeats the unqualified version. |

Minor: abstract (99 words), 64/25.6 kHz, Table 6 source drift, KAIST figure: addressed. "Softmax" for RF, chance level ("around 0.25" but range reaches 0.35), AI declaration ("drafting" and "literature search" remain): partially. `\resizebox` 6-pt tables, Fig. 1a legend over the band, references (10/22 arXiv, Panić 2027 with 2026 DOI, Lessmeier without pages), `\TODO` placeholders: not addressed.

## 2. New problems introduced by the revision

- **A. "about 250 per target recording" (4.5) is wrong by 5×.** Sec. 3 caps recordings at 50 windows; `results_paderborn/recalibration.csv` gives n_cal = 49 at k=1 and 392 at k=8 (250 belongs to the unused `win` variant). The argument survives; the number does not.
- **B. Table 1 caption is broken in the PDF**: `71\\,264` renders as "71" / line break / ",264 cycles".
- **C. 4.7 compares escalation at different α**: "at α=0.10 it escalates 6 % against 22 % in distribution", but the 22 % is at α=0.05, so part of the drop is α, not shift.
- **D. 4.5 cherry-picks ρ**: "a residual weight of 0.1 (−0.110) is better than both extremes", yet Table 7 gives ρ=0.3 as −0.103.
- **E. Bib note leaked** into the reference list: Doula (2026) "ICML 2026 poster per icml.cc listing".
- **F. Contradiction in 4.3**: "neither the classifier nor the tier predicts the mode" follows three sentences assigning a mode to each pair; say "not predictable a priori".

## 3. Numeric claims still not verifiable against a table or macro

- Ordering holds "for each classifier family", 4.1 (Table 2 shows the best only).
- "Learning curve ... flat", Sec. 3.
- Macro-F1 "torque 0.64–0.91, speed 0.22–0.31", 4.4.
- APS "near nominal only by inflating sets", 4.3 (the 99.8 % was removed, nothing replaced it).
- The α behind 80 % / 50 % / 62 % in 4.3.
- "Combined-damage class has three bearings".
- "About 250 per target recording" (contradicted, see A).
- All of 4.7 and the 4.3 failure-mode figures exist only as macros.

Everything else (Tables 2–7, energy figures, 4.6×, 74 k ops, 0.18 mJ, 7 729, every recalibration and ρ value quoted) checks out.

## 4. IFAC compliance

Abstract 99 words (ok). Title 10 words only if "Operating-Point" is one token. Keywords 8 (ok). 6 pages, page 6 now full (ok). Two red `\TODO` placeholders remain (funding, co-authors). AI declaration still claims "drafting", which the policy does not permit.

## 5. Updated scores

Novelty 3 · Soundness 3 · Clarity 4 · Reproducibility 3 · Significance 4.

**Recommendation: minor revision.** The claims now agree with the tables and the energy story is told straight; what is left is one factual error (A), one broken caption (B), intervals missing from the coverage tables, and an unrun label-free baseline the paper now openly defers.

## 6. Three most valuable remaining improvements (within 6 pages)

1. **Fix A–F, add 95 % bootstrap intervals to Tables 4 and 6** (± in the cell), and delete Table 7's k=1 row with its sentence in 4.5, since the paper itself calls k=1 an artefact. Zero net page cost.
2. **Replace the number-dense prose of 4.3 and 4.7 with one table**: rows (tier, classifier), columns escalation %, coverage, singleton %, empty %, macro-F1, in-distribution vs shift, at one stated α. This resolves C and F and makes the failure-mode claim auditable.
3. **Run one label-free baseline** (Yilmaz & Heckel test-time recalibration on the k target recordings with labels stripped) as a fourth column of Table 6. It needs no new data and is the one experiment that turns "only target labels restore coverage" from a citation into a result.
