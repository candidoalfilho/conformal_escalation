# Reviewer A (statistics / conformal prediction) — round 3, draft 3

Checked against `cmlib.py`, the two run scripts, `make_tables_ifac.py` and the result CSVs (all regenerated after the quantile fix; ρ = 1 / ρ = 0 now reproduce the pooled / target-only columns of Table 5 to within 0.0014, ties only).

## 1. Round-2 requests

| # | Request | Status |
|---|---|---|
| (i) | α-direction; Sec. 4.2 recast as empirical with the q̂ range | Done. `conformal_qhat` is now exactly the ⌈(n+1)(1−α)⌉-th smallest score. The q̂ claims are verified except one bound (below). |
| (ii) | Declare pooled-across-fold calibration | Done (Sec. 3), but with an unsupported clause (below). |
| (iii) | Recording-level clustering, hierarchical citation | Done (Dunn et al.; Lee et al.), including "small α cannot be certified from three calibration recordings". |
| (iv) | Weighted-quantile normalisation, normalised-weight share, Barber bound | Done; one notation issue (below). |
| (v) | Soften "three to five" | Done in abstract, Sec. 1, Sec. 4.5. The Conclusion's "Five recordings … restore the guarantee" should read "restore mean coverage" (seed s.d. is 0.04–0.07 at k = 5). |
| (vi) | Same statistic for point and interval (Table 2); intervals in the 80 % column (Table 3) | Not done; both tables now disclose the mismatch in the caption instead. Acceptable at the page limit, but see 2b–2c. |

## 2. Errors and inconsistencies in draft 3

**2a. Table 3, bearing-grouped row, pools three tiers.** The caption says "for the cheap tier of the current-first cascade", but `make_tables_ifac.py` builds the bearing-grouped row from `bearing_coverage.csv` without filtering `block`, so it averages `cur2_full`, `vib1_time` and `vib1_full`. For the current tier alone the row is: mean +0.002, worst −0.053, 81.0 ± 3.0 %, healthy/faulty 62 / 82. The conclusion ("holds under bearing-grouped validation as well") survives; the numbers in the table and in Sec. 4.3 ("+0.009 mean, worst −0.098") must change, or the caption must say the row pools the three tiers of Table 4.

**2b. Table 3, 80 % column, inconsistent aggregation.** The KAIST shift entry "55.3 ± 17.3 %" pools LR (40.2 ± 5.4 %) and RF (70.3 ± 6.4 %), so the ± is mostly the classifier difference, while the Paderborn shift entry is already split "50.0 ± 5.9 / 32.6 ± 2.6 %". Report both shift rows as LR / RF; the ± is then a seed s.d. (n = 3) and the caption's "spread over classifiers and seeds" becomes "s.d. over seeds". Consequence: abstract "nominal 80 % delivers 33–55 %" and Sec. 1 "55.3 % (KAIST)" become "33–70 %" and "40.2–70.3 % (KAIST)".

**2c. Table 2 caption.** "mean over three seeds" holds for the recording-grouped column only; `e1_pareto` runs the shift protocol with `seeds = [0]` (`f1_std = 0` in `pareto.csv`). A percentile interval is also not "centred on the bootstrap mean". Replace the parenthesis by "(mean over three seeds for the recording-grouped column, seed 0 otherwise)" and "centred on the bootstrap mean, which differs …" by "whose bootstrap mean differs …". The cheap fix for (vi) proper is to bootstrap the three-seed mean F1 (resample recordings once, evaluate all three seeds' predictions).

**2d. Sec. 2.2, q̂ bound.** "≥ 0.66 at α ≤ 0.40" is false by rounding: the minimum of `qhat` over classifiers, seeds and both protocols at α = 0.40 is 0.657 (LR, shift). Write "≥ 0.65". The rest is verified: q̂ ≥ 0.803 for all α ≤ 0.20 on KAIST; on Paderborn 1 − q̂ > 0.5 only for RF at α ≥ 0.20 (q̂ ≤ 0.481), never for LR (q̂ ≥ 0.502).

**2e. Sec. 3, "which if anything favours the gate".** Not supported, and the data show the pooling is immaterial: source-only calibration with one quantile per held-out point (Table 5 caption) gives −0.144 on KAIST against −0.148 pooled (Table 3). Replace the clause by "and gives the same gap as the per-point quantile of Sec. 4.5 (−0.144 against −0.148)".

**2f. Sec. 2.1, Barber bound notation.** "coverage at least 1−α−Σᵢ w̃ᵢ d_TV(Zᵢ, Z_test)" is not the theorem: the TV distance is between the joint law of the data sequence Z and that of Z⁽ⁱ⁾, the sequence with calibration point i and the test point swapped, not between two marginals. Replace by "1−α−Σᵢ w̃ᵢ d_TV(Z, Z⁽ⁱ⁾), with Z⁽ⁱ⁾ the data with point i and the test point swapped". Same length.

**2g. Sec. 4.2, undefined ±, unstated protocol.** "−0.0001 ± 0.0039 on KAIST and −0.0015 ± 0.0043 on Paderborn" is mean ± s.d. over 119 / 163 matched points, in-distribution folds only (`tab_gate_delta(protocol="grouped")`); no table in the paper backs it (`tab_gate.tex` is generated but not included). Insert "in distribution, mean ± s.d. over 119 and 163 matched points". The per-cascade range "between −0.003 and +0.001" is verified.

## 3. Verified without remark

Table 5 (all cells and the source-only caption values), every weighted-conformal number in Sec. 4.5, Table 4 and the ranges quoted from it in Sec. 4.3–4.4, Table 6 and Sec. 4.6, the damage-transfer range 0.11–0.35, the remaining rows of Table 3, the Σwᵢ + 1 normalisation, the singleton ⇔ threshold condition, and the corrected statement of what α bounds (wrong singletons over all windows, not among singletons).

## 4. Scores

**Soundness 4/5, clarity 4/5.** The conformal content is now correct and the text matches the code. What separates the paper from 5/5 is one table error (2a), one inconsistent aggregation that touches the abstract (2b), one wrong caption (2c), and four sentence-level fixes (2d–2g); none changes a conclusion, and all fit the page limit as replacements.

## Round 3b verification (draft 3b, 6 pages)

Items 2a–2g checked against the regenerated tables, `main_ifac.tex` and the CSVs.

- **2a** Table 3 bearing row now `cur2_full` only: +0.002 / −0.053 / 81.2 / 80.8 % / 62 / 82 — verified.
- **2b** LR / RF split in every Table 3 row (82.9 / 93.5, 40.2 / 70.3, 79.0 / 78.2, 50.0 / 32.6) — verified; abstract and conclusion read "33–70 %". **New error:** the Sec. 4.3 parenthesis "(RF to LR on KAIST, LR to RF on Paderborn)" is reversed. The ranges are written 40.2–70.3 % (LR = 40.2, RF = 70.3) and 32.6–50.0 % (RF = 32.6, LR = 50.0), so it must read "(LR to RF on KAIST, RF to LR on Paderborn)". Not blocking, but it would mislead a reader cross-checking Table 3.
- **2c** Table 2 caption: "three seeds for the grouped protocols; one run per held-out point under shift" and "percentile intervals … of the seed-0 predictions; the interval can sit off the point" — matches `e1_pareto` (shift uses seed 0 only). Verified.
- **2d** "≥ 0.65 at α ≤ 0.40" — verified (minimum 0.657).
- **2e** "the two give the same source-only gap to within 0.01 on KAIST" — true as stated (Table 3 −0.148 vs Table 5 −0.144), but the two means use different α grids; on the common grid {0.05, 0.10, 0.20, 0.30} the pooled gap is −0.158 against −0.144 (0.014), and on Paderborn −0.328 against −0.338. "to within 0.02" would be grid-independent and still supports the point. Minor.
- **2f** Barber bound now "d_TV^{(i)} the total-variation distance between the data sequence and the one with calibration point i and the test point swapped" — correct.
- **2g** Sec. 4.2 now "In distribution … (mean ± s.d. over matched points)" — verified; −0.003 / +0.001 per-cascade range re-verified.
- **New sentence, Sec. 4.3** (modality-specific direction of the silent failure): from `factor_coverage.csv` (LAC, α = 0.20, LR, mean over seeds): vibration tiers under speed change cover the healthy class at 1.00 (both tiers) and the fault classes at 0.41 / 0.03 / 0.08 (time+FFT) and 0.31 / 0.55 / 0.03 (time), i.e. 0.03–0.55 — verified; current tier under speed or torque covers the healthy class at 0.00 — verified (the LR current gate collapses onto one fault class: class 1 at 1.00 under speed, class 2 at 1.00 under torque, all others 0.00). The "missed detections" / "false alarms" reading is correct given 0.91–0.96 singletons.

**Updated scores: soundness 5/5, clarity 4/5.** Nothing blocks acceptance on statistical grounds. Clarity is held at 4 by the reversed parenthesis in Sec. 4.3 (a one-line fix) and the α-grid mismatch behind "to within 0.01"; the Table 2 point/interval mismatch remains disclosed rather than removed, which is acceptable at the page limit.
