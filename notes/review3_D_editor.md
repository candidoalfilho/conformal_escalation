# Reviewer D (technical editor), round 3 — *Calibrate Where You Deploy*, draft 3 (`main_ifac.tex`, 6 pp.)

## 1. Round-2 items

| Item | Status |
|---|---|
| Old 4.6 numbers in a table | Done (Table 6; all eight values match) |
| Two/three-to-five contradiction | Done; consistent with Table 5 and the ρ grid |
| One name per concept | Three slips: abstract "confidence threshold", Discussion "score threshold" (→ "threshold gate"); 4.4 "KAIST load-shift columns" (→ "the KAIST shift column, where only torque changes") |
| LAC, LR, RF at first use | Done |
| 247-word sentence split | Done; (i)–(iv) are 51–54 words each (§5) |
| Unshrink tables | **Not done**: three tables still at 5–6 pt (§7) |
| Stale macros | **Not done**: 12 unused macros in `numbers_ifac.tex` (`gateLr*`, `gateRf*`, `fOneExpRf`, `lemTwoMj`, `computeMarg`); `tab_gate.tex`, `tab_weighted.tex` generated but not input |
| Code-and-data paragraph, α grid, features, AI declaration | Done |
| Red placeholders only where pending | Done (funding, co-authors, repository) |

## 2. Numbers in text vs tables

Every number cited from Tables 1–6 matches (2.3 ratios reproduce; 0.18 mJ = 0.33 × 0.53). Backed only by the repository: 2.2 q̂ values; 2.3 "1.9× in cycles", "26 µW"; 4.2 per-cascade range; 4.5 n_src = 500, 7 729 windows and nine weighted-conformal numbers (ρ = 0.03 is not even in `tab_weighted.tex`); 4.7 "0.11–0.35". The weighted paragraph (147 words) is the one long unbacked block; replace with (87 words): "Weighted conformal prediction (source weight ρ, target 1; grid in the repository) helps only when the target share of the normalised weight is large: on KAIST (n_src = 500) ρ = 0.3 at k = 5 gives −0.030 against −0.001 target-only; on Paderborn (n_src ≈ 7 729) ρ = 0.3 leaves the source in control (−0.271) and only ρ = 0.03 approaches target-only (−0.056 vs +0.008). At k = 1 a residual source weight beats both pooling and target-only, because one recording holds one class. Once three target recordings exist, calibrate on them."

**Factual mismatch.** 4.1 defines the cascades as "current → one accelerometer, time+FFT" and "one accelerometer, time → time+FFT". `make_tables_ifac.py` names the KAIST cascades `cur_full→vib_full` and `vib1_time→vib_full`: the expensive tier is *four* accelerometers + FFT on KAIST. Write "current-first (current → the full vibration tier: four accelerometers on KAIST, one on Paderborn, time+FFT)" and "same-sensor (time-domain → time+FFT on the same accelerometer(s))".

## 3. Cross-references

All `\ref`s resolve. 4.2 hard-codes "Sec.~2.2" (add a label). Table 6 is first cited in 4.3, before Table 5 (write "Table 6 below").

## 4. Internal contradictions

1. 4.3: "trained on three operating points (Table 6) the random forest keeps its escalation fraction" holds for the same-sensor cascade (6 % → 6 %) but not for current-first (33 % → 53 %, the over-escalation mode). Write "in the same-sensor cascade of Table 6".
2. Table 6 "exp." = 0.941 (RF) vs Table 2 = 0.959 for the same tier and protocol. Add to the caption: "trained on two thirds of the recordings (a third is held out for calibration), hence below Table 2".
3. 2.3 "an order of magnitude below" is 7.5× on the total basis (0.071 vs 0.53) → "well below".

## 5. Sentences > 45 words; jargon

28 sentences exceed 45 words (max 73). Splits of equal length:
- (i): full stop after "energy per window"; "With a dedicated transducer motor current is the expensive tier, so ... only when current is free; that cascade is the one most exposed to shift."
- 2.2 (65): full stop after "the right baseline"; "In the experiments, however, q̂ is large (...), so ...".
- Data (73/67): full stops after "25.6 kHz", "(five masses)", "64 kHz", "400 N".
- Conformal protocol (70): full stop after "pooled test predictions"; "Under shift the pooled calibration set therefore holds ...".
- 4.5 "commissioning" (60): full stop after "labelled recordings".

Jargon: "X3" (4.7) is an unexplained label (name the notebook or drop); "APS" is never expanded ("adaptive prediction sets").

## 6. IFAC compliance

Title 10 words (limit); abstract 96–98 words; 7 keywords; 6 pages, page 6 ≈ 85 % full (ten lines of slack: enough for the fixes above, not for a new table). One overfull hbox (3.7 pt, 4.1: "(671 744 operations)" → "(671 744)"); two underfull vboxes are benign. References: 21 cited, author-year, alphabetical, NeurIPS uniform. Remaining: Lessmeier 2016 lacks volume/pages (PHM Society European Conf. 3(1); add DOI 10.36001/phme.2016.v3i1.1577); Kaya 2026 is the only entry with a DOI (all or none); Lee 2023 may have a journal version; Panić "2027" must be verified as the assigned volume or marked in press; 19 uncited `.bib` entries do not print but should be pruned from the submission zip.

## 7. Table shrink factors (measured natural widths; 8 pt base)

| Table | Factor | Size | Fix |
|---|---|---|---|
| 1 energy | 0.70 | 5.6 pt | Shorten names ("IEPE accel., TIDA-010249 front end"; "ESP32-S3 compute, full accel. tier (marg./total)") → ≈ 0.87 |
| 2 frontier | 0.84 | 6.8 pt | Borderline; `\tabcolsep` 3 pt and "[0.33,0.45]" → ≈ 0.9 |
| 3 gap | 0.66 | 5.3 pt | Unreadable. Protocol → "in / bearing / shift" (as Table 4); cell "50.0 / 32.6", spreads to the caption → ≈ 0.94 |
| 4 factor | 1.03 | 8.2 pt | Fine |
| 5 recal | 0.93 | 7.5 pt | Fine |
| 6 shift | 0.65 | 5.2 pt | Unreadable. Drop the uncited "cheap"/"exp." columns → ≈ 0.93, or `table*` |

## 8. Scores

**Clarity 4/5.** Contributions, naming and Table 6 landed; what remains is mechanical: three tables at 5–6 pt, three naming slips, the KAIST cascade misstatement, long sentences in Secs. 2–3.

**Reproducibility 4/5.** Grids, features, splits, seeds and bootstrap are stated. For 5/5: repository URL and commit hash; one clause of classifier hyper-parameters (LR: standardised inputs, C = 1; RF: 300 trees, min leaf 2, per `cmlib.py`); the weighted-conformal numbers in a table or reduced as in §2; stale macros and unused table files removed so that `make_tables_ifac.py` regenerates exactly what is printed.

## 9. Round 3b verification

**Numbers vs tables.** All values cited from Tables 1–6 match the new tables (33–70 % = 32.6–70.3; 2.2 mJ ≈ 2.25, 4× = 2.25/0.53, 46 µW = 2.78 mJ/60 s, 7× = 0.53/0.071; bearing +0.002/−0.053; healthy 38 % = mean of 9/67). New repository-only numbers: 4.3 per-class coverage under factor change ("0.03–0.55", "0.00"), not in Table 4; acceptable if flagged as such.

**Blocking error (4.3).** "40.2–70.3 % on KAIST and 32.6–50.0 % on Paderborn (RF to LR on KAIST, LR to RF on Paderborn)" is swapped: Table 3 gives KAIST LR 40.2 / RF 70.3 and Paderborn LR 50.0 / RF 32.6. Write "(LR to RF on KAIST, RF to LR on Paderborn)".

**Minor.** 4.5: stray comma in "(−0.052, −0.037), (seed s.d. …)" → drop the comma. Four macros now unused (`covEightyK`, `memsAvgUw`, `lightMj`, `wOneK`). `kaya2026iot` is no longer cited (fine). Table 1's IEPE row changed to 100 mW / 16.0 mJ; nothing in the text depends on it.

**Cross-references.** All resolve; table order now matches citation order (shift = Table 5 cited in 4.3, recal = Table 6 in 4.5); Table 5 caption's note on "exp." vs Table 2 is present. No overfull box remains; the two underfull vboxes are page-break artefacts. Title 10 words, abstract 96, keywords 7, 6 pages.

**Resizebox factors (measured).** Table 1 0.75 (6.0 pt), Table 3 0.78 (6.2 pt), Table 5 0.74 (5.9 pt): readable on screen, at the floor in print. Cheap gains: Table 5 labels "1 accel. time → +FFT" / "2 phases → +FFT" and `\tabcolsep` 2.5 pt (→ ≈ 0.85); Table 3 header "80 % cov. LR/RF" (→ ≈ 0.85); Table 1 last row "ESP32-S3 compute, accel. time+FFT (marg./total)" (→ ≈ 0.82).

**Scores.** Clarity **4/5** (the swapped parenthesis and three borderline tables are what remain). Reproducibility **4/5**, becoming 5/5 once the repository URL and commit hash replace the placeholder; hyper-parameters, grids and the exp.-column note are now in.
