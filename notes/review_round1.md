# Review: "Calibrate Where You Deploy: Conformal Sensor Escalation Under Operating-Point Shift" (IFAC SAFEPROCESS 2027)

## 1. Summary

The paper considers a two-tier condition-monitoring node where a cheap sensor runs continuously and an expensive one is woken on demand. It proposes replacing the softmax wake-up threshold by a split-conformal rule: escalate whenever the cheap tier's prediction set is not a singleton, so the user specifies a risk level α and the escalation rate (hence energy) becomes an observed consequence. On KAIST and Paderborn with hand-crafted features and shallow classifiers it reports that (a) in energy terms a dedicated current transducer, not a MEMS accelerometer, is the expensive sensor; (b) the conformal gate and a tuned softmax threshold give the same accuracy at matched escalation fraction; (c) coverage holds under recording- and bearing-grouped validation but collapses under operating-point shift (80 % nominal → 33–55 %), with speed breaking all modalities and torque breaking only current; and (d) three to five labelled recordings from the new operating point restore coverage, whereas pooling them with the stale source calibration set does not. The summary is recoverable from the text alone.

## 2. Scores

| Criterion | Score |
|---|---|
| Novelty | 3 |
| Technical soundness | 2 |
| Clarity | 3 |
| Reproducibility | 2 |
| Significance for SAFEPROCESS | 4 |

**Recommendation: major revision.** The question (does the conformal guarantee survive an operating-point change, and what does recommissioning cost?) is exactly right for this audience and the recalibration result is useful, but several headline claims are contradicted by the paper's own tables, two tables disagree on the same quantity, promised confidence intervals never appear, and the sensor-energy premise is undermined by the frontier result.

## 3. Major issues

1. **Headline "radial force neither" is contradicted by Table 5.** Introduction (p. 1–2): "rotational speed breaks every tier, torque breaks only the current tier, radial force neither." Table 5 gives vibration-tier coverage under radial force of 0.40 and 0.27 for the random forest (nominal 0.80). Sec. 4.4 softens this to "degrades it moderately", and the Discussion's "a plant whose load varies but whose speed does not can run an accelerometer-first cascade without recalibration" is unsupported. Also "torque leaves it essentially at nominal (0.67–0.82)": 0.67 is a 13-point gap.

2. **Tables 6 and 7 report the same quantity with different numbers.** By definition ρ=1 is "pooled" and ρ=0 is "target only" (Table 7 caption), yet KAIST k=5: pooled −0.072 (Table 6) vs −0.046 (Table 7); target +0.002 vs +0.047. Paderborn k=5: +0.010 vs +0.023. If the α grids or seeds differ, say so and use one grid; otherwise one table is wrong.

3. **"Fails by under-escalating" is not what the evidence shows for every classifier.** Sec. 4.3: "for the random forest, 62 % of the sets under shift are empty." By Eq. (2) an empty set escalates, so the RF fails by over-escalating (wasteful but safe). The "silent" wrong-singleton failure (5 % escalation, 0.717) is for an unnamed classifier. Contribution (iii) and the Discussion's "confident silence" must be scoped to the classifier/tier where it occurs, and the split empty/wrong-singleton should be tabulated.

4. **Table 4 does not say which tier(s) it aggregates.** Fig. 1 is the current tier only; Table 5 shows vibration LR under torque at 0.82. If the headline 33–55 % pools the current tier with the vibration tiers, it is dominated by the modality the paper itself calls fragile. "50.0 / 32.6 %" has no legend (LR/RF?). Likewise "it holds equally under bearing-grouped validation" (+0.009) ignores a worst gap of −0.098 vs −0.038 recording-grouped.

5. **The sensor-escalation premise is undercut by Sec. 4.1.** The paper concludes "the only cascade with a cheap tier worth the name is one accelerometer time-domain → one accelerometer time+FFT (same sensor)". That cascade saves no acquisition energy; its currency is operations, which Sec. 2.3 calls "the wrong currency". It then differs from CADS/Conformal Cascade only in domain. Either show a cascade that actually saves acquisition energy, or reframe the contribution as "conformal compute escalation, plus a negative result on sensor cascades". Relatedly, no table reports energy per window vs α for any cascade, although the abstract promises energy as "a measured consequence".

6. **Energy model is internally inconsistent.** Table 1 lists the ESP32-S3 active at 42.9 mJ/window, 80× the MEMS sensor, yet the first sentence claims the node is "dominated, energetically, by its analogue front end". This only holds if the MCU sleeps during acquisition (IIS3DWB FIFO); state the duty model. The 25× ratio uses the LEM CKSR (81.7 mW); with the TMCS1100 in the same table it is 6.8×, and the IEPE accelerometer (180 mW) is costlier than either current sensor. Choosing the worst current transducer and the best accelerometer is not a fair ordering.

7. **No confidence intervals anywhere.** Sec. 3 promises 95 % cluster-bootstrap intervals (600 replicates); no table or figure shows one. "The FFT is dispensable" (0.690 vs 0.706) and "indistinguishable" (Table 3) need them. Table 3 gives an s.d. over matched points, not an interval.

8. **Class coverage of tiny target calibration sets.** KAIST has 5 classes and 3 recordings per (class, load); k=1 target-only calibration contains one class, k=3 at most three. Is sampling stratified by class? If not, the "3–5 recordings" rule coincides with the class count and the k=1 collapse (−0.231, worse than source-only) is an artefact. Same for Paderborn (one bearing = one class).

9. **Missing baseline: unlabelled recalibration.** The costly resource is labelled target recordings. Test-time recalibration on unlabelled target data (Yilmaz & Heckel, in the .bib but uncited), conformal calibration transfer (Doula 2026, uncited) and ACI (Gibbs & Candès) are the natural competitors. At least one should be run; otherwise "only target labels can restore coverage" rests on a citation.

10. **Gate equivalence claim is imprecise.** "'non-singleton' is a reparametrised threshold on the top softmax probability": with LAC, |C|=1 iff p̂(1) ≥ 1−q̂ and p̂(2) < 1−q̂, i.e. a condition on the top two scores. Equivalent only when 1−q̂ ≥ 0.5. State this; it also explains why Table 3 can be non-zero.

## 4. Minor issues

- Abstract is 103 words (limit 100). Title is 10 words only if "Operating-Point" counts as one. Keywords: 8, fine.
- Red `\TODO` placeholders (funding, co-authors) remain in the PDF.
- Sec. 4.1 "two current phases at 64 kHz": signals are resampled to 25.6 kHz (Sec. 3), and the op count assumes N=4096 at that rate.
- "source set holds some 31 000 windows": 31 266 is the whole dataset; with one operating point held out the source cannot exceed ~23 000, and with a one-third calibration split ~7 800. Also clarify whether the model is trained and calibrated on the same source recordings in the recalibration protocol (would violate split conformal).
- Table 6 "source" column varies with k (−0.131 to −0.142); explain (test set shrinks?).
- "Softmax" is used for RF vote fractions; say "top-class score".
- Tables 1–2 are shrunk by `\resizebox` to ~6 pt; Fig. 1a legend covers the LOLO band; "nominal 80 %" line in Fig. 1b is barely visible.
- Sec. 4.6 "chance level (0.11–0.35)": chance macro-F1 for 4 classes is ~0.25; 0.35 is above it.
- Declaration of generative AI: "figure generation" and "drafting of the manuscript text" go beyond Elsevier/IFAC policy, which permits AI only to improve readability/language and forbids AI-created figures. Reword to "code for data processing and plotting; language editing", if accurate.
- References: 9 of 20 are arXiv preprints, including three 2026 preprints carrying key claims; Lessmeier 2016 lacks pages; Panić et al. is dated 2027 with a 2026 DOI; 18 .bib entries are uncited (harmless, but several have `TODO` notes).
- Fig. 1 is the only figure and shows one tier of one dataset; KAIST has no figure.

## 5. Three suggestions (within 6 pages; page 6 is half empty)

1. **Add one table splitting shift failures into empty / wrong-singleton / correct-singleton per classifier and tier, with bootstrap CIs**, and cut the Sec. 4.2 prose (the equivalence is expected; four lines suffice). This fixes issues 3, 4, 7 at once.
2. **Replace Table 7 with a figure of coverage vs effective source weight ρ·n_src/n_tgt** (both datasets on one axis), which makes the "weight must scale with the size ratio" claim quantitative and removes the Table 6/7 discrepancy. Add one unlabelled-recalibration baseline curve to it.
3. **Reframe contribution (i) honestly**: present the accelerometer time → time+FFT cascade with its energy (MCU duty included), state that no sensor-level cascade on these benchmarks saves acquisition energy, and move the LEM/TMCS/IEPE comparison into one sentence. Fix "radial force neither" everywhere (abstract, intro, 4.4, discussion, conclusion).

## 6. Numeric claims not verifiable against any table or macro

- "0.477 with the MLP" (Paderborn current under shift), Sec. 4.1
- "The ordering is the same ... in all three classifier families", Sec. 4.1 (only best classifier shown; KAIST fusion 0.675 < 1-accel 0.687 under shift already breaks the ordering)
- "99.8 % coverage with the random forest under shift" (APS), Sec. 4.3
- "62 % of the sets under shift are empty", Sec. 4.3
- "escalates 5–22 % of windows", "0.925 vs. 0.943 at 22 % escalation, 74 k vs. 168 k operations", "escalates 5 % ... delivers 0.717", Sec. 4.3 (0.943 also disagrees with Table 2's 0.959 for the same tier)
- "vibration under torque shift 0.64–0.91, under speed shift 0.22–0.31" (macro-F1), Sec. 4.4
- "at k=1 a small residual weight is better than both extremes", Sec. 4.5 (Table 7 has no k=1 row)
- "source set holds some 31 000 windows", Sec. 4.5
- "macro-F1 at chance level ... (0.11–0.35)" for damage-origin shift, Sec. 4.6
- "combined-damage class has three bearings", Limitations
- "picojoules per cycle times published cycle counts" (no numbers given), Sec. 2.3; "19 μJ" FFT appears only in a caption, with no cycle count
- 95 % bootstrap intervals (promised in Sec. 3, never shown)
