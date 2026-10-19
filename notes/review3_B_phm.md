# Reviewer B (PHM / fault diagnosis) — round 3, draft 3

Manuscript: *Calibrate Where You Deploy: Conformal Sensor Escalation Under Operating-Point Shift* (IFAC SAFEPROCESS 2027, 6 pp.)

## 1. Round-2 requests

| Item | Status |
|---|---|
| (a) physics paragraph | Rewritten (Sec. 4.4); two corrections in 3 |
| (b) healthy/faulty coverage | Added to Table 3; one inconsistency in 2 |
| (c) labelling caveat, healthy-only case | Added (Sec. 4.5); healthy-only claim is untested, see 4 |
| (d) Mondrian / scheduling-variable sentence | Added (Sec. 2.2, Discussion); correct |
| (e) dataset nits | "three of which", 639/640 (KA08), resonance band, U-phase, pooled severities, missing combined class, one combined bearing per fold: all fixed. KAIST rate: see 4 |

## 2. Numbers checked against the result files

Table 3 reproduces exactly from `conformal_coverage.csv` (LAC, α = 0.20, pooled over classifiers and seeds): 88.2 ± 9.3 / 38 / 92; 55.3 ± 17.3 / 33 / 56; 78.6 ± 1.1 / 69 / 82; 80.4 ± 6.9 / 75 / 71; 50.0 / 32.6 and 57 / 37. Table 4 and every range in Sec. 4.4 reproduce from `factor_coverage.csv`; Sec. 4.5 matches Table 5. Two presentation problems:

- The bearing-grouped row of Table 3 pools three tiers (`block` = cur2_full, vib1_time, vib1_full), while the caption says the table is the current tier. Current tier alone: mean gap +0.002, worst −0.053, 81.0 ± 3.0 %, healthy/faulty 62 / 82. Regenerate from `block == "cur2_full"` or label the row "(three tiers)". The pooled 71 % is dragged down by the combined class (40 %, one bearing per fold).
- "which on the KAIST current tier is covered at 38 % in distribution ... while the fault classes are covered at 92 %" (Sec. 4.3). The 38 % averages LR 9 % and RF 67 %. Replace: "which on the KAIST current tier is covered at 9 % (LR) to 67 % (RF) in distribution, 38 % on average (one healthy recording per load), while the fault classes are covered at 92 %".

## 3. Physics (Sec. 4.4)

The attribution is now physically right: amplitude and impact-rate scaling with speed; fundamental and sidebands moving with speed on the inverter-fed motor; the ~7× q-axis change as the classical MCSA load dependence; load zone for radial force; order tracking named as the missing control. Two corrections:

- "Speed scales impact rate and vibration amplitude, so every time-domain statistic moves". Kurtosis, skewness, crest, shape and impulse factors are scale-free; they move through impacts per window, not amplitude. Replace: "Speed scales vibration amplitude, so the dimensional statistics rescale, and impact rate, so the dimensionless impulsiveness factors change with the impacts per window".
- The per-class columns of `factor_coverage.csv` hold the fact a diagnosis audience will cite: the *direction* of the silent failure is modality-specific. Under a speed change the LR vibration gates cover healthy at 1.00 and the fault classes at 0.03–0.55 with 0.79–0.99 singletons: they emit {healthy} for damaged bearings (missed detection). The LR current gate under speed or torque covers healthy at 0.00 and one fault class at 1.00 (one wrong singleton for every window: false alarm and misdiagnosis). Add after "The physics is consistent.": "Per class, the silent failure of the LR vibration gates under speed change is a missed detection (healthy covered at 1.00, faults at 0.03–0.55); that of the current gate is a false alarm (healthy at 0.00)."

## 4. Engineering message and Discussion

- "a variable-speed drive cannot run either cascade without recalibration". Overclaim: the drive publishes speed, so per-speed (Mondrian) calibration or order-tracked features are the obvious design, both untested. Replace: "a variable-speed drive cannot run either cascade on a single calibration; it needs per-speed calibration or speed-normalised features, neither tested here".
- "the vibration cascade of commercial nodes ... shares the speed sensitivity". Those nodes wake on a raw amplitude threshold, not a classifier; write "is expected to share".
- "only healthy recordings exist at the new point, which recalibrate the healthy-class quantile alone (the false-alarm side of Table 3)". No experiment does this, and 1 − healthy coverage counts escalations as well as wrong singletons. Replace: "only healthy recordings exist at the new point; these can recalibrate a Mondrian healthy-class quantile, which bounds the silent false-alarm rate but was not tested here".
- "vibration and current both at 25.6 kHz" (Sec. 3). `extract_kaist.py` windows current and temperature with the same sample indices as vibration and no resampling, so the current tier and its 0–2 / 2–6 / 6–12.8 kHz band energies rest on this rate. Cite it from the specifications table of Jung et al. (2023) and state that windows are time-aligned across channels.

## 5. Scores

- Significance to SAFEPROCESS: **4.5/5**. Factor-by-modality attribution with a physical reading, the healthy/faulty split and the scheduling-variable framing make the result usable by a model-based FDI reader; the recalibration number is the practical contribution.
- Clarity: **4/5**. Sec. 4.4 is now readable; Table 3's bearing-grouped row and the pooled 38 % hide tier and classifier dependence.

What separates it from 5/5: the missed-detection vs false-alarm sentence is the result the FDI audience will cite and is absent; the three Discussion overclaims; and the untested status of speed normalisation and healthy-only recalibration should be stated where the claims are made, not only in Limitations. All fit within the page limit as equal-length replacements.
