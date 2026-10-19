# Originality / prior-art review — "Calibrate Where You Deploy: Conformal Sensor Escalation Under Operating-Point Shift"

Target: IFAC SAFEPROCESS 2027. Review date: 2 Oct 2026. Window searched: 2019–Oct 2026, emphasis 2024–2026, arXiv included.
Method: ~45 web searches, ~35 abstract/full-text fetches. Every entry below was verified against the publisher/arXiv page unless marked **[unverified]**. Nothing is cited from memory alone without that flag.

Pages I could not read (rate-limited or bot-walled): arXiv HTML of 2607.08273 (used the Pith mirror instead — abstract verified there), ResearchGate page for "Confidence-Aware TinyML Orchestration for Vibration-Based PdM in Automotive Powertrains" (429), IEEE Xplore 10609509 (empty), PMC 13517235 (captcha), OpenReview for Yilmaz & Heckel (bot check; arXiv 2210.04166 abstract partially read).

---

## (a) Executive verdict

**C1 — conformal set-size gate on the *sensor* side, cost in joules: partially novel.** The gating mechanism itself (escalate iff the conformal set is not a singleton; α as the knob, deferral rate as a measured consequence) is already published three times over in 2025–2026: CADS (image model cascades, FLOPs), Conformal Cascade (LLM tiers; it even writes expected cost as an explicit function of α and the calibration acceptance rate), and Huang–Park–Paoletti–Simeone (edge→cloud escalation with conformal alignment). What is not published anywhere I could find: applying the gate to *acquisition* (waking a second sensor), modeling the cost in energy from datasheets, and the current→vibration inversion. That is the defensible novelty; claim only that.

**C2 — conformal gate ≈ softmax gate at matched escalation: novel as a stated negative result, but a reviewer will call it expected.** With a monotone score (1 − p̂), "non-singleton" is a reparametrized threshold on the top-two softmax margin, so equal accuracy at matched escalation is close to a tautology. Frame it as "conformal gives a principled way to *set* τ, not a better gate" — and note it contradicts the premise of Conformal Cascade (Dou et al.), which motivates CP by softmax miscalibration.

**C3 — coverage collapse under operating-point shift with source-only calibration, factor attribution: partially novel.** Collapse of CP coverage under shift is textbook (Tibshirani 2019; Barber 2023) and has been shown empirically in PHM regression (Yang/Wang/Wang 2026, conditional undercoverage 0.666), in time-series classification (Nanopoulos & Buza 2025), and in bearing diagnosis under recording-level splits (González-García et al. 2026, CP "fails on MFPT"). No one has measured it in fault *classification* with leave-one-operating-point-out on KAIST/Paderborn — that is new. **Risk:** the factor attribution (torque destroys coverage, radial force harmless) partially conflicts with Panić et al. (RESS 2027: on Paderborn "rotational speed causes substantial degradation (42.8% RPD), load and force have negligible impact") and Alam et al. (2025: the torque-only condition was the *easiest* transfer). Must be reconciled explicitly (plausibly: your cheap tier uses motor current, which is torque-dependent).

**C4 — recalibration cost in target recordings; pooling worse than discarding: novel in PHM, not in CP.** Han & Qu (2026) give the label complexity of restoring coverage under shift and show "only target labels restore it"; Lee (2026) shows retraining recovers only partially; the ETA paper (Öçal & Kilim 2026) shows few-shot recovery needs 5–10% target support. "Pooling is worse" is what the quantile of a source-dominated mixture must do; Barber et al. 2023 is the published fix (down-weight, don't discard) and you must either test it or name it as the untested alternative. The commissioning framing (k=3–5 recordings) is yours.

**No single paper does ≥2 of C1–C4 together.** The framing survives. The introduction must, however, cite CADS, Conformal Cascade, Huang et al., Yang et al., Mei et al., Han & Qu, Panić et al., and Barber et al., and drop the implicit claim that conformal gating of cascades is new.

---

## (b) Most relevant works

Legend — Relation: **O** overlaps, **D** differs, **S** supports/needed context. Must-cite: **Y** / **R** (recommended) / **N**.

| # | Citation | What it does | Relation to C1–C4 | Must cite |
|---|---|---|---|---|
| 1 | Turkoglu, Bary, Thielens, Dausort, Macq, "CADS: Conformal Adaptive Decision System for Cost-Efficient Image Classification", arXiv:2605.16401, May 2026. https://arxiv.org/abs/2605.16401 (author order from the HTML page; the project note lists Macq first — verify) | Model cascade Scout→Oracle; routing by conformal set size (singleton / binary / ≥3), cost in GFLOPs, PathMNIST + CIFAR-100. No shift, no recalibration. | **C1-O** (same gate, model side, FLOPs). C3/C4 absent. | **Y** |
| 2 | Dou, Lian, Li, "Conformal Cascade: Distribution-Free Accuracy Guarantees for Multi-Tier LLM Inference", arXiv:2607.25018, Jul 2026. https://arxiv.org/abs/2607.25018 | "accept when the calibrated set collapses to a single answer, defer otherwise"; "characterizes expected cascade cost as an explicit function of α and the calibration-set acceptance rate"; finite-sample accuracy guarantee. | **C1-O** (α as spec, deferral rate as consequence — this exact framing). **C2-D**: they argue softmax thresholds are miscalibrated and need per-pair tuning; your C2 says the two gates are accuracy-equivalent at matched escalation. | **Y** |
| 3 | Huang, Park, Paoletti, Simeone, "Reliable Inference in Edge-Cloud Model Cascades via Conformal Alignment", arXiv:2510.17543, Oct 2025. https://arxiv.org/abs/2510.17543 | Edge→cloud escalation cast as multiple hypothesis testing with conformal alignment; guarantees on fraction of edge decisions with cloud-level conditional coverage. No energy model; covariate shift listed as future work. | **C1-O** (edge/cloud two-tier conformal escalation). **C3-S** (they flag shift robustness as open). | **Y** |
| 4 | Fisch, Schuster, Jaakkola, Barzilay, "Efficient Conformal Prediction via Cascaded Inference with Expanded Admission", ICLR 2021. https://arxiv.org/abs/2007.03114 | Cascades *inside* CP to prune candidates cheaply before expensive scoring. Different sense of "cascade" but the canonical reference. | C1-S (terminology). | **R** |
| 5 | Wang, Yang, Wang, "Empirical Calibration and Conditional-Reliability Diagnostics for Bearing RUL Prediction under Operating-Regime Shift", arXiv:2607.08273, Jul 2026. https://arxiv.org/abs/2607.08273 (Pith mirror lists first author as Jun Wang; the project note says Yang, Wang & Wang — verify order) | PHME 10-bearing subset, load/speed regimes as held-out units; marginal 90% coverage 0.900 but "0.666 coverage in a low-load/high-speed cell"; regime-conditioned residuals raise it to 0.941 "only as motivation". | **C3-O** (closest PHM result; regression, pooled calibration, conditional not source-only). **C4-D** (post-hoc diagnostic, no sample-count). | **Y** |
| 6 | Mei, Li, Qian, Jia, "Calibrated Prediction Set in Fault Detection with Risk Guarantees via Significance Tests", arXiv:2508.01208, Aug 2025. https://arxiv.org/abs/2508.01208 | CP sets for bearing diagnosis, CWRU↔SEU; "the testing subset was further divided equally, dedicating one half for calibration" — i.e., **calibrated on the target domain**; reports coverage ≥ nominal even when accuracy is 24–36%. | **C3-O/D**: shows CP "works" cross-domain only because calibration is target-side; never measures source-only. Your gap is exactly the case they skip. | **Y** |
| 7 | Han, Qu, "The Label Complexity of Class Conditional Coverage under Distribution Shift", arXiv:2607.18088, Jul 2026. https://arxiv.org/abs/2607.18088 | Under shift marginal coverage holds (0.881) while per-class collapses (worst 0.699); "every label-free method we evaluate sits below the 0.90 validity band, and only the target-label" procedures restore it; minimax label complexity O(ε⁻² log K). | **C4-O** (theory for "how many target labels"; "only target labels restore"). C3-S. | **Y** |
| 8 | Barber, Candès, Ramdas, Tibshirani, "Conformal prediction beyond exchangeability", Ann. Statist. 51(2):816–845, 2023. https://doi.org/10.1214/23-AOS2276 | Weighted CP with coverage gap bounded by weighted TV distance. | **C4-D/S**: the principled alternative to "discard the stale source set" is to down-weight it. Must be tested or named. | **Y** |
| 9 | Tibshirani, Barber, Candès, Ramdas, "Conformal Prediction Under Covariate Shift", NeurIPS 2019. https://arxiv.org/abs/1904.06019 | Likelihood-ratio weighted CP. | C3-S, C4-S. | **Y** |
| 10 | Gibbs, Candès, "Adaptive Conformal Inference Under Distribution Shift", NeurIPS 2021. https://proceedings.neurips.cc/paper/2021/hash/0d441de75945e5acbc865406fc9a2559-Abstract.html | Online α adaptation. | C4-S (online alternative to batch recalibration). | **R** |
| 11 | Panić, Pašić, Nagode, Oman, "On simple baselines for domain shift in condition monitoring: A case study in bearing fault identification", Reliab. Eng. Syst. Saf. 277:113041, 2027 (online 2026). https://doi.org/10.1016/j.ress.2026.113041 | 600k evaluations on CWRU + Paderborn, Relative Performance Drop metric: "rotational speed causes substantial degradation (42.8% RPD), load and force have negligible impact". | **C3-O/conflict**: agrees on speed and radial force, **disagrees on torque**. Accuracy-based, no CP. | **Y** |
| 12 | Alam, Ahsan, Raman, "Multimodal Bearing Fault Classification Under Variable Conditions: A 1D CNN with Transfer Learning", arXiv:2502.17524, Feb 2025; and "Physics-Informed Multimodal Bearing Fault Classification under Variable Operating Conditions using Transfer Learning", arXiv:2508.07536, Sep 2025 (also validated on KAIST). | Paderborn vibration + current, baseline N15_M07_F10 → the three single-factor conditions; the torque-only condition (N15_M01_F10) was the *easiest* (0.96), speed 0.92, radial force 0.89. | **C3-conflict** on torque and radial force ordering. Same single-factor design as yours — ideal foil. | **Y** |
| 13 | Kaya, Jobani, "IoT-Driven Robust Bearing Fault Diagnosis for Induction Motors Under Operating-Condition Shift", Sensors 26(12):3829, 2026. https://doi.org/10.3390/s26123829 | Paderborn vibration + phase current, 1D-CNN early fusion, measurement-wise vs operating-condition holdout (F1 0.925 → 0.863, worst 0.716), bearing-disjoint 0.55. No UQ, no energy. | C3-S (condition-holdout degradation on Paderborn with current+vibration). C1-S (same modalities, no cascade). | **R** |
| 14 | Cekic, Akan, "Motor-Current-Based Bearing Fault Detection Under Unseen Operating Conditions", Energies 19(16):3884, 2026. https://doi.org/10.3390/en19163884 | Paderborn, current-only, leave-one-operating-condition-out, bearing-level grouping; specificity collapses (0.09–0.56). | C1-S/C3-S: motor current as the cheap tier is fragile across conditions — supports your "under-escalation" story. | **R** |
| 15 | Vieira, Bauler, Rosa, Silva, "Towards a more realistic evaluation of machine learning models for bearing fault diagnosis", arXiv:2509.22267, Sep 2025. | Leakage taxonomy (segment-, condition-, repetition-wise splits) on CWRU/PU/UORED; PU near-100% under repetition-wise splits. | C3-S (justifies recording-grouped CV as the honest baseline). | **R** |
| 16 | González-García, Usero, Sicilia, García-Barriocanal, "Shapelet-Based Bearing Fault Diagnosis Under Interpretability Constraints: A Recording-Level Evaluation", Electronics 15(14):3035, 2026. https://doi.org/10.3390/electronics15143035 | Recording-level CV on CWRU/MFPT; secondary analysis: "split conformal prediction yields valid coverage on CWRU but fails on MFPT due to class-proportion mismatch across recording-level splits". | **C3-O** (CP coverage failure in bearing diagnosis under grouped splits, though via label shift, not operating point). | **Y** |
| 17 | Nanopoulos, Buza, "Conformal prediction for out-of-distribution time-series classification", Applied Intelligence, 2025. https://doi.org/10.1007/s10489-025-06708-7 | CP coverage under OOD distortions on FordA/FordB (engine noise), PdM-motivated; fixes via label smoothing / hybrid classifiers, no target recalibration. | C3-O (CP coverage under OOD in a PdM-flavoured TSC task). C4-D. | **R** |
| 18 | Lee, "Diagnosing Conformal Prediction Failures Under Distribution Shift: A COVID-19 Case Study", arXiv:2601.00908, 2026. | Coverage drops 0.1–77.1 pp under identical temporal shift; retraining recovers only partially; ACI restores marginal coverage at inflated set size. | C3-S, C4-S (recalibration partial recovery; shift detectors don't predict coverage loss). | **R** |
| 19 | Javanmardi, Hüllermeier, "Conformal Prediction Intervals for Remaining Useful Lifetime Estimation", Int. J. Progn. Health Manag. 14(2), 2023. | CP for RUL on C-MAPSS; handles the 6 operating modes by per-mode normalization. | C3-S (CP adoption in PHM; operating modes acknowledged, not stress-tested). | **R** |
| 20 | Wang, Vidal, Pozo, "Uncertainty-Aware Bearing Remaining Useful Life Prediction Based on Conformal Prediction", PHM Society European Conf. (PHME), 2026. | Physics-informed Transformer + conformal calibration on XJTU-SY; PICP 0.48 → 0.94 after calibration. | C3-S (context). | **R** |
| 21 | de la Fuente, Radrigan, Morales, "Enhancing Predictive Maintenance in Mining Mobile Machinery through a TinyML-enabled Hierarchical Inference Network", IEEE Access, 2024 (arXiv:2411.07168). | Device/gateway/cloud tiers; escalation by anomaly-count heuristics and battery level, **not** uncertainty; energy measured with PPK-II (≈2.0 J vs 3.6 J per cycle). | **C1-D**: hierarchical inference *location*, same sensor; no conformal; energy measured. Closest TinyML-PdM cascade. | **Y** |
| 22 | Jia, Kwon, Ma, Pham, Qendro, Vu, Mascolo, "A cascade framework for on-device uncertainty-aware event detection on microcontrollers", Pervasive Mob. Comput. 119:102208, 2026. | Evidential DL uncertainty gates early exits (shallow/medium/deep) on MCU; up to 8.57× lower energy. No sensor cascade, no CP. | C1-D (uncertainty-gated model cascade on MCU). | **R** |
| 23 | Lamaakal, Yahyati, Maleh, El Makkaoui, Ouahbi, "Efficient uncertainty aware human activity recognition on microcontrollers using hyperdimensional computing and conformal prediction", Sci. Rep., 2026. https://doi.org/10.1038/s41598-026-57375-8 | Label-conditional CP on Cortex-M4 (3–5 ms, 6–9 KB RAM); sets "expand gracefully under shift". No escalation. | C1-S (CP is MCU-feasible). | **R** |
| 24 | Singh, Srikantha, Lakhanpal, "Cost-Sensitive Conformal Prediction and Human-in-the-Loop Abstention for Imbalanced High-Stakes Decision Support", arXiv:2607.27143, Jul 2026. | Defers when \|Ĉ(X)\| ≠ 1; break-even deferral thresholds vs human review budget. Tabular, no shift. | C1-O (non-singleton as deferral rule, cost break-even). | **R** |
| 25 | Wang, Sun, Dobriban, "Singleton-Optimized Conformal Prediction", arXiv:2509.24095, Sep 2025. | Score that maximizes singleton frequency; "a set of size two or more may require additional human intervention … brings an outsized cost". | C1-S/C2-S (if the gate is set-size, SOCOP would lower escalation at fixed α — an obvious ablation reviewers may ask for). | **R** |
| 26 | Doula, "Conformal Calibration Transfer", arXiv:2609.10737, Sep 2026 (ICML 2026 poster per icml.cc). | Transport source calibration to a target *sensor/modality* space via unlabeled pairs; label-free mismatch correction. | C4-D (label-free alternative to your labeled-target recalibration; explicitly about "sensor changes"). | **R** |
| 27 | Siahkali, Verma, Gupta, "Coverage Guarantees for Pseudo-Calibrated Conformal Prediction under Distribution Shift", arXiv:2602.14913, 2026. | Pseudo-labeled target calibration with Wasserstein-based slack. | C4-D. | N/R |
| 28 | Yilmaz, Heckel, "Test-time Recalibration of Conformal Predictors Under Distribution Shift Based on Unlabeled Examples", arXiv:2210.04166, 2022 **[authors from memory — verify]**. | Unlabeled-target recalibration. | C4-D. | **R** |
| 29 | Öçal, Kilim, "ETA Prediction in Last-Mile Logistics Under Domain Shift: From Zero-Shot Failure to Few-Shot Recovery", Applied Sciences 16(17):8861, 2026. | 1/5/10/20% target support; "markedly more stable at 5–10% support"; target-only control; "conformal recalibration improved coverage but did not correct … bias". | C4-O (quantifies target samples for recovery; pooled vs target-only control), other domain. | N/R |
| 30 | Yuan, Li, Wang, Zhang, "Conformal machine learning for reliable anomaly detection in industrial cyber-physical systems", Reliab. Eng. Syst. Saf. 274:112417, 2026. | Sliding calibration set + temporal quantile adjustment for FAR guarantees. | C4-S (rolling recalibration in industrial CP). | **R** |
| 31 | Diallo, Homri, Dantan, "Reducing false alarms in fault detection: … conformal prediction … PCA and autoencoders", J. Process Control 152:103495, 2025. | CP thresholds for TEP fault detection. | S (CP in SAFEPROCESS-adjacent literature). | **R** |
| 32 | Goodarzi, Schütze, Schneider, "Domain shifts in industrial condition monitoring: a comparative analysis of automated machine learning models", J. Sens. Sens. Syst. 14:119, 2025. | LOGO by operating condition on Paderborn among 7 datasets; FESC beats DL under shift in 4/7. | C3-S. | N/R |
| 33 | Jung, Kim, Yun, Bae, Park, "Vibration, acoustic, temperature, and motor current dataset of rotating machine under varying operating conditions for fault diagnosis", **Data in Brief 48:109049, 2023** (not Sci. Data). https://doi.org/10.1016/j.dib.2023.109049 | KAIST testbed; loads 0/2/4 Nm; 3 CT phase-current sensors + 4 accelerometers. | Dataset. **Fix the venue in the manuscript.** | **Y** |
| 34 | Lessmeier, Kimotho, Zimmer, Sextro, "Condition Monitoring of Bearing Damage in Electromechanical Drive Systems by Using Motor Current Signals of Electric Motors: A Benchmark Data Set for Data-Driven Classification", PHME 2016 **[standard citation, not re-verified this session]**. | Paderborn KAt dataset. | Dataset. | **Y** |

Not found (negative results of the search, useful for the "to our knowledge" sentences):
- No paper that gates **sensor acquisition** (as opposed to model tier or inference location) with a conformal prediction set.
- No academic comparison of **current-transducer vs MEMS-accelerometer energy** for PdM nodes; the only sources are datasheets and vendor notes (ADI, ST). Datasheet check: LEM CKSR 15-NP v14 lists I_C = 15 mA typ (20 max) at 5 V → **75 mW typ / 105 mW max**, not 82 mW — state the exact assumption (voltage, I_P term) or correct the number. IIS3DWB 1.1 mA at 3 V ≈ 3.3 mW is consistent.
- No PHM paper comparing **pooled vs replaced** calibration sets under operating-point shift.

---

## (c) Threats — works that touch ≥2 of the four claims

1. **Conformal Cascade (Dou, Lian, Li, arXiv:2607.25018) — touches C1 and the premise of C2.** Abstract: "Production cascades govern this deferral through a confidence threshold, but LLM confidence scores are miscalibrated, the threshold must be tuned per model pair and per domain, and no setting yields a formal bound on cascade accuracy. We introduce Conformal Cascade (CC) … that uses conformal prediction set size as the deferral rule: accept when the calibrated set collapses to a single answer, defer otherwise." and it "characterizes expected cascade cost as an explicit function of α and the calibration-set acceptance rate." This is your C1 sentence ("α is the specification; escalation rate is a measured consequence") in another domain. Your C2 (no accuracy difference vs softmax at matched escalation) is a direct empirical counterpoint to their motivation — say so; it strengthens the paper.

2. **CADS (arXiv:2605.16401) — C1.** "CADS leverages conformal prediction to quantify image uncertainty at runtime … dynamically routes samples through a model cascade, ranging from lightweight 'Scout' models to high-capacity 'Oracle' architectures … at a computational cost that can be up to 12 times lower." Set-size routing (singleton/binary/≥3) and a cost budget. Only the cost currency (FLOPs vs joules) and the cascaded object (models vs sensors) differ.

3. **Huang, Park, Paoletti, Simeone (arXiv:2510.17543) — C1 and an explicit pointer to C3.** "We study edge-cloud cascades that must preserve conditional coverage: whenever the edge returns a prediction set, it should contain the true label with a user-specified probability." They name "robustness of CAb schemes under covariate shift" as future work — your C3 answers the question they pose, so cite them as motivation.

4. **Wang/Yang/Wang (arXiv:2607.08273) — C3 and a gesture at C4.** "conditional diagnostics expose non-uniform reliability, including 0.666 coverage in a low-load/high-speed cell, and a post-hoc pooled regime-conditioned residual diagnostic raises that cell to 0.941 only as motivation for future pre-specified conditional calibration." Regression, PHME bearings, pooled calibration. You differ by (i) classification, (ii) source-only calibration, (iii) quantified fix. Do not claim to be first to observe regime-conditional undercoverage in PHM.

5. **Han & Qu (arXiv:2607.18088) — C3 and C4.** "Under that shift the certificate stays reassuring while per class coverage fails silently … only the target-label [procedures restore it]"; label complexity O(ε⁻² log K). This is the theory behind your "3–5 recordings restore coverage" — cite it and, if possible, check whether your k is consistent with their bound at your ε and K.

6. **Mei et al. (arXiv:2508.01208) — C3 (by omission).** Reports coverage ≥ 1−α cross-domain *because* calibration uses half the target test set. A reviewer who knows this paper will ask why your result differs; the answer (source-only calibration) must be in the first paragraph where you cite them.

7. **Panić et al. (RESS 2027) + Alam et al. (2025) — C3 factor attribution.** "rotational speed causes substantial degradation (42.8% RPD), load and force have negligible impact" vs your "torque (0.7→0.1 Nm) destroys coverage (0.01–0.33)". Not a novelty threat but a *credibility* threat: explain the discrepancy (coverage of a source-calibrated quantile vs accuracy; which features/modality; whether the cheap tier is motor current, whose amplitude scales with torque).

8. **de la Fuente et al. (IEEE Access 2024) — C1 adjacent.** Tiered PdM inference with measured energy and battery-aware escalation on real machinery. Not conformal, same sensor throughout, but it is the paper a PHM reviewer will have in mind when reading "hierarchical" + "energy".

No paper combines sensor-side escalation **and** coverage-under-shift **and** recalibration cost. The combination is yours.

---

## (d) Suggested positioning paragraph and contribution statements

**Positioning (related work / intro, ~150 words):**

Conformal prediction has recently been used to govern cascades: CADS routes images between light and heavy models by prediction-set size [Turkoglu et al. 2026], Conformal Cascade defers LLM queries whenever the set is not a singleton and writes expected cost as a function of α [Dou et al. 2026], and conformal alignment certifies edge-to-cloud escalation [Huang et al. 2025]. All three cascade *models* and price cost in compute. We move the gate to the *acquisition* side, where the dominant cost of a battery-powered condition-monitoring node is sensing energy, and show that in joules the familiar "cheap current, expensive vibration" ordering inverts. In PHM, conformal intervals have been adopted for RUL [Javanmardi & Hüllermeier 2023; Wang et al. 2026], and regime-conditional undercoverage has been reported for RUL regression [Wang et al. 2026]; cross-domain prediction sets for bearing diagnosis have been calibrated on target data [Mei et al. 2025]. We study the case practitioners actually face—source-only calibration under a new operating point—and quantify what it costs to fix, consistent with the label-complexity results of Han & Qu [2026].

**Contribution statements (one line each, as they survive review):**

- **C1.** First conformal set-size gate applied to *sensor wake-up* rather than model selection, with cost accounted in datasheet-derived energy per window; the same gate used in CADS/Conformal Cascade/CAb, relocated to acquisition, reverses the cheap/expensive ordering of current and vibration.
- **C2.** At matched escalation fraction, the conformal gate and a tuned softmax-margin gate are statistically indistinguishable in accuracy — the value of the conformal gate is that α fixes the operating point without tuning τ, not higher accuracy (a counterpoint to the motivation in Dou et al.).
- **C3.** With source-only calibration, nominal 80 % coverage falls to 55 % (KAIST, leave-one-load-out) and 33–50 % (Paderborn, leave-one-operating-point-out), and the gate fails by *under*-escalating; on Paderborn, speed and torque shifts drive the collapse while radial force does not — an ordering we reconcile with accuracy-based studies [Panić et al.; Alam et al.] by [state the reason].
- **C4.** Three to five labeled recordings from the new operating point restore nominal coverage; pooling them with the stale source calibration set is worse than discarding it, because the source quantile dominates by volume — a commissioning rule that complements, and should be benchmarked against, weighted non-exchangeable conformal prediction [Barber et al. 2023].

---

## (e) BibTeX — must-cite works (best effort; TODO = unverified field)

```bibtex
@article{turkoglu2026cads,
  title   = {{CADS}: Conformal Adaptive Decision System for Cost-Efficient Image Classification},
  author  = {Turkoglu, Mikael and Bary, Tim and Thielens, Vincent and Dausort, Manon and Macq, Beno{\^i}t},
  journal = {arXiv preprint arXiv:2605.16401},
  year    = {2026},
  note    = {TODO: verify author order (project note lists Macq first)}
}

@article{dou2026conformalcascade,
  title   = {Conformal Cascade: Distribution-Free Accuracy Guarantees for Multi-Tier {LLM} Inference},
  author  = {Dou, Yifan and Lian, Shikan and Li, Shibo},
  journal = {arXiv preprint arXiv:2607.25018},
  year    = {2026}
}

@article{huang2025cab,
  title   = {Reliable Inference in Edge-Cloud Model Cascades via Conformal Alignment},
  author  = {Huang, Jiayi and Park, Sangwoo and Paoletti, Nicola and Simeone, Osvaldo},
  journal = {arXiv preprint arXiv:2510.17543},
  year    = {2025}
}

@inproceedings{fisch2021cascades,
  title     = {Efficient Conformal Prediction via Cascaded Inference with Expanded Admission},
  author    = {Fisch, Adam and Schuster, Tal and Jaakkola, Tommi and Barzilay, Regina},
  booktitle = {International Conference on Learning Representations (ICLR)},
  year      = {2021}
}

@article{wang2026rulregime,
  title   = {Empirical Calibration and Conditional-Reliability Diagnostics for Bearing {RUL} Prediction under Operating-Regime Shift},
  author  = {Wang, Jun and Yang, Shaoliang and Wang, Yunsheng},
  journal = {arXiv preprint arXiv:2607.08273},
  year    = {2026},
  note    = {TODO: verify author order (project note lists Yang first)}
}

@article{mei2025calibratedset,
  title   = {Calibrated Prediction Set in Fault Detection with Risk Guarantees via Significance Tests},
  author  = {Mei, Mingchen and Li, Yi and Qian, Yiyao and Jia, Zijun},
  journal = {arXiv preprint arXiv:2508.01208},
  year    = {2025}
}

@article{han2026labelcomplexity,
  title   = {The Label Complexity of Class Conditional Coverage under Distribution Shift},
  author  = {Han, Weijia and Qu, Lisha},
  journal = {arXiv preprint arXiv:2607.18088},
  year    = {2026}
}

@article{barber2023beyond,
  title   = {Conformal prediction beyond exchangeability},
  author  = {Barber, Rina Foygel and Cand{\`e}s, Emmanuel J. and Ramdas, Aaditya and Tibshirani, Ryan J.},
  journal = {The Annals of Statistics},
  volume  = {51},
  number  = {2},
  pages   = {816--845},
  year    = {2023},
  doi     = {10.1214/23-AOS2276}
}

@inproceedings{tibshirani2019covariate,
  title     = {Conformal Prediction Under Covariate Shift},
  author    = {Tibshirani, Ryan J. and Barber, Rina Foygel and Cand{\`e}s, Emmanuel J. and Ramdas, Aaditya},
  booktitle = {Advances in Neural Information Processing Systems 32 (NeurIPS)},
  year      = {2019}
}

@inproceedings{gibbs2021adaptive,
  title     = {Adaptive Conformal Inference Under Distribution Shift},
  author    = {Gibbs, Isaac and Cand{\`e}s, Emmanuel J.},
  booktitle = {Advances in Neural Information Processing Systems 34 (NeurIPS)},
  year      = {2021}
}

@article{panic2027baselines,
  title   = {On simple baselines for domain shift in condition monitoring: A case study in bearing fault identification},
  author  = {Pani{\'c}, Branislav and Pa{\v{s}}i{\'c}, Mirza and Nagode, Marko and Oman, Simon},
  journal = {Reliability Engineering \& System Safety},
  volume  = {277},
  pages   = {113041},
  year    = {2027},
  doi     = {10.1016/j.ress.2026.113041}
}

@article{alam2025multimodal,
  title   = {Multimodal Bearing Fault Classification Under Variable Conditions: A {1D} {CNN} with Transfer Learning},
  author  = {Alam, Tasfiq E. and Ahsan, Md Manjurul and Raman, Shivakumar},
  journal = {arXiv preprint arXiv:2502.17524},
  year    = {2025}
}

@article{alam2025physics,
  title   = {Physics-Informed Multimodal Bearing Fault Classification under Variable Operating Conditions using Transfer Learning},
  author  = {Alam, Tasfiq E. and Ahsan, Md Manjurul and Raman, Shivakumar},
  journal = {arXiv preprint arXiv:2508.07536},
  year    = {2025}
}

@article{gonzalezgarcia2026shapelet,
  title   = {Shapelet-Based Bearing Fault Diagnosis Under Interpretability Constraints: A Recording-Level Evaluation},
  author  = {Gonz{\'a}lez-Garc{\'i}a, Lino and Usero, Luis and Sicilia, Miguel-Angel and Garc{\'i}a-Barriocanal, Elena},
  journal = {Electronics},
  volume  = {15},
  number  = {14},
  pages   = {3035},
  year    = {2026},
  doi     = {10.3390/electronics15143035}
}

@article{delafuente2024esnpdm,
  title   = {Enhancing Predictive Maintenance in Mining Mobile Machinery through a {TinyML}-enabled Hierarchical Inference Network},
  author  = {de la Fuente, Ra{\'u}l and Radrigan, Luciano and Morales, An{\'i}bal S.},
  journal = {IEEE Access},
  year    = {2024},
  note    = {arXiv:2411.07168. TODO: volume/pages/DOI (page lists DOI 10.1109/ACCESS.2024.0429000 as placeholder)}
}

@article{jung2023kaist,
  title   = {Vibration, acoustic, temperature, and motor current dataset of rotating machine under varying operating conditions for fault diagnosis},
  author  = {Jung, Wonho and Kim, Seong-Hu and Yun, Sung-Hyun and Bae, Jaewoong and Park, Yong-Hwa},
  journal = {Data in Brief},
  volume  = {48},
  pages   = {109049},
  year    = {2023},
  doi     = {10.1016/j.dib.2023.109049}
}

@inproceedings{lessmeier2016paderborn,
  title     = {Condition Monitoring of Bearing Damage in Electromechanical Drive Systems by Using Motor Current Signals of Electric Motors: A Benchmark Data Set for Data-Driven Classification},
  author    = {Lessmeier, Christian and Kimotho, James Kuria and Zimmer, Detmar and Sextro, Walter},
  booktitle = {Proceedings of the European Conference of the PHM Society (PHME)},
  year      = {2016},
  note      = {TODO: re-verify pages; standard citation, not re-checked this session}
}
```

Recommended (R) entries — add if space allows:

```bibtex
@article{kaya2026iot,
  title={{IoT}-Driven Robust Bearing Fault Diagnosis for Induction Motors Under Operating-Condition Shift},
  author={Kaya, {\c{S}}{\"u}kr{\"u} Mustafa and Esmaeili Jobani, Alireza},
  journal={Sensors}, volume={26}, number={12}, pages={3829}, year={2026}, doi={10.3390/s26123829}}

@article{cekic2026motorcurrent,
  title={Motor-Current-Based Bearing Fault Detection Under Unseen Operating Conditions},
  author={Cekic, Yalcin and Akan, Aydin},
  journal={Energies}, volume={19}, number={16}, pages={3884}, year={2026}, doi={10.3390/en19163884}}

@article{vieira2025realistic,
  title={Towards a more realistic evaluation of machine learning models for bearing fault diagnosis},
  author={Vieira, Jo{\~a}o Paulo and Bauler, Victor and Rosa, Rodrigo Kobashikawa and Silva, Danilo},
  journal={arXiv preprint arXiv:2509.22267}, year={2025}}

@article{nanopoulos2025ood,
  title={Conformal prediction for out-of-distribution time-series classification},
  author={Nanopoulos, Alexandros and Buza, Krisztian},
  journal={Applied Intelligence}, year={2025}, doi={10.1007/s10489-025-06708-7}, note={TODO: volume/pages}}

@article{lee2026diagnosing,
  title={Diagnosing Conformal Prediction Failures Under Distribution Shift: A {COVID-19} Case Study},
  author={Lee, Chorok},
  journal={arXiv preprint arXiv:2601.00908}, year={2026}}

@article{javanmardi2023cprul,
  title={Conformal Prediction Intervals for Remaining Useful Lifetime Estimation},
  author={Javanmardi, Alireza and H{\"u}llermeier, Eyke},
  journal={International Journal of Prognostics and Health Management}, volume={14}, number={2}, year={2023}}

@inproceedings{wang2026phme,
  title={Uncertainty-Aware Bearing Remaining Useful Life Prediction Based on Conformal Prediction},
  author={Wang, Shun and Vidal, Yolanda and Pozo, Francesc},
  booktitle={Proceedings of the European Conference of the PHM Society (PHME)}, year={2026}, note={TODO: pages}}

@article{jia2026cascade,
  title={A cascade framework for on-device uncertainty-aware event detection on microcontrollers},
  author={Jia, Hong and Kwon, Young D. and Ma, Dong and Pham, Nhat and Qendro, Lorena and Vu, Tam and Mascolo, Cecilia},
  journal={Pervasive and Mobile Computing}, volume={119}, pages={102208}, year={2026}}

@article{lamaakal2026hduq,
  title={Efficient uncertainty aware human activity recognition on microcontrollers using hyperdimensional computing and conformal prediction},
  author={Lamaakal, Ismail and Yahyati, Chaymae and Maleh, Yassine and El Makkaoui, Khalid and Ouahbi, Ibrahim},
  journal={Scientific Reports}, year={2026}, doi={10.1038/s41598-026-57375-8}}

@article{singh2026costsensitive,
  title={Cost-Sensitive Conformal Prediction and Human-in-the-Loop Abstention for Imbalanced High-Stakes Decision Support: A Multi-Domain Benchmark},
  author={Singh, Manpreet and Srikantha, Akshatha and Lakhanpal, Shyamal},
  journal={arXiv preprint arXiv:2607.27143}, year={2026}}

@article{wang2025socop,
  title={Singleton-Optimized Conformal Prediction},
  author={Wang, Tao and Sun, Yan and Dobriban, Edgar},
  journal={arXiv preprint arXiv:2509.24095}, year={2025}}

@article{doula2026tcc,
  title={Conformal Calibration Transfer},
  author={Doula, Achref},
  journal={arXiv preprint arXiv:2609.10737}, year={2026}, note={ICML 2026 poster per icml.cc listing}}

@article{yilmaz2022testtime,
  title={Test-time Recalibration of Conformal Predictors Under Distribution Shift Based on Unlabeled Examples},
  author={Yilmaz, Fatih Furkan and Heckel, Reinhard},
  journal={arXiv preprint arXiv:2210.04166}, year={2022}, note={TODO: verify authors}}

@article{yuan2026icps,
  title={Conformal machine learning for reliable anomaly detection in industrial cyber-physical systems},
  author={Yuan, Shuaiqi and Li, Jipu and Wang, Chunjin and Zhang, Xiaoge},
  journal={Reliability Engineering \& System Safety}, volume={274}, pages={112417}, year={2026}}

@article{diallo2025falsealarms,
  title={Reducing false alarms in fault detection: A comparative analysis between conformal prediction and classical methods applied to {PCA} and autoencoders},
  author={Diallo, Abdoul Rahime and Homri, Lazhar and Dantan, Jean-Yves},
  journal={Journal of Process Control}, volume={152}, pages={103495}, year={2025}}
```

---

## Action items for the manuscript (short)

1. Rewrite the C1 claim: "we apply the conformal set-size gate of [CADS; Conformal Cascade; CAb] to sensor wake-up" — do not claim the gate.
2. Add a sentence reconciling the torque result with Panić et al. and Alam et al. (both find torque shift benign on Paderborn).
3. Fix KAIST citation venue (Data in Brief 48:109049, 2023) and the CKSR 15-NP power figure (datasheet: 75 mW typ at 5 V, 105 mW max) or state the assumption behind 82 mW.
4. Either run weighted non-exchangeable CP [Barber 2023] as a third recalibration strategy (source-weighted vs pooled vs replace) or explicitly list it as untested.
5. Cite Han & Qu for the label complexity of restoring coverage; check your k=3–5 against their O(ε⁻² log K).
6. Cite Mei et al. precisely: their coverage holds because calibration is target-side.
