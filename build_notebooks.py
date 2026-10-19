#!/usr/bin/env python3
"""Generate the two analysis notebooks from the result CSVs.

    python build_notebooks.py            # writes 01_kaist_conformal_gate.ipynb, 02_paderborn_replication.ipynb
    jupyter nbconvert --to notebook --execute --inplace 0*.ipynb   # embed outputs

The notebooks do not recompute any experiment; they read ``results/`` and
``results_paderborn/`` (written by ``run_experiments.py``, ``run_paderborn.py`` and
``run_paderborn_extra.py``) and produce the tables and figures used in the paper.
Figures are written to ``figs_en/``.
"""
import nbformat as nbf

def build(cells, path):
    nb = nbf.v4.new_notebook()
    nb.cells = cells
    nb.metadata["kernelspec"] = {"display_name": "Python 3", "language": "python", "name": "python3"}
    nb.metadata["language_info"] = {"name": "python"}
    nbf.write(nb, path)
    print("wrote", path, len(cells), "cells")

def md(s):   return nbf.v4.new_markdown_cell(s.strip())
def code(s): return nbf.v4.new_code_cell(s.strip())


ENV = """
# Environment setup: runs unchanged locally (repository root as working directory) and on Google Colab.
import os, sys, subprocess
REPO_URL = "https://github.com/candidoalfilho/conformal_escalation"   # update if the repository moves
IN_COLAB = "google.colab" in sys.modules
if not os.path.exists("cmlib.py"):                       # not inside the repository: fetch it
    subprocess.run(["git", "clone", "--depth", "1", REPO_URL, "conformal_escalation"], check=True)
    os.chdir("conformal_escalation")
if IN_COLAB:
    subprocess.run([sys.executable, "-m", "pip", "install", "-q", "pyarrow", "scikit-learn", "matplotlib", "pandas", "scipy"], check=False)
print("working directory:", os.getcwd())
"""
SETUP = """
import numpy as np, pandas as pd, matplotlib.pyplot as plt
from IPython.display import display
import report_lib as R
pd.set_option("display.width", 160); pd.set_option("display.max_columns", 30); pd.set_option("display.precision", 3)
"""

METHODS_COMMON = r"""
## Shared methodology

**Windowing and features.** Signals are segmented into windows of 4096 samples with a hop of 2048 (160 ms at 25.6 kHz), at most 50 windows per recording. For every channel, nine time-domain statistics are computed (mean, standard deviation, RMS, peak-to-peak, kurtosis, skewness, crest factor, shape factor, impulse factor) and, when the configuration includes the FFT, six spectral descriptors (dominant frequency, spectral centroid, spectral entropy, and band energies in 0–2 kHz, 2–6 kHz and 6–12.8 kHz). The temperature channel, which is quasi-constant within a window, contributes its mean and standard deviation. The same two functions (`tfeat`, `ffeat` in `extract_kaist.py` / `extract_paderborn.py`) are used for both datasets, so that feature vectors and costs are directly comparable.

**Sensing configurations.** A configuration is a set of channels and the choice of including the FFT. Its *cost in operations per window* is computed analytically (`kaist_lib.cost_ops`): 9 accumulations per sample for the time-domain statistics, $2.5\,N\log_2 N$ operations for a real radix-2 FFT of length $N$, plus magnitude and band accumulation per bin. The operation count isolates the arithmetic burden of each configuration on a microcontroller; it does not include acquisition energy, which is modelled separately (Section *Energy model*).

**Classifiers.** Three families are used so that any ordering of configurations is not an artefact of one learner: $\ell_2$-regularised logistic regression, a random forest (300 trees, minimum leaf size 2) and a multilayer perceptron (64–32 hidden units, tol $10^{-5}$, up to 3000 iterations). Convergence is checked for every fit and reported (`converged = 1.00` throughout).

**Validation protocols.** Windows from the same recording are strongly dependent (same mounting, thermal state, residual unbalance). All splits are therefore grouped by recording. Two protocols are used: *recording-grouped stratified 3-fold cross-validation*, repeated over three seeds, which estimates in-distribution performance; and *leave-one-operating-point-out* (LOLO), which trains on all but one operating point and tests on the held-out one, which estimates performance under operating-point shift. Confidence intervals are 95 % percentile intervals from a cluster bootstrap that resamples *recordings* (600 replicates); a window-level bootstrap would understate uncertainty by roughly an order of magnitude.

**Split conformal prediction.** From the training recordings of each fold, a stratified third is carved out as a calibration set (never used for fitting). With non-conformity score $s_i = 1 - \hat p(y_i \mid x_i)$ (LAC) or the cumulative sorted probability up to the true class (APS), the conformal quantile $\hat q$ is the $\lceil (n+1)(1-\alpha)\rceil$-th smallest calibration score (`cmlib.conformal_qhat`; $\hat q = 1$ when that rank exceeds $n$) and the prediction set is $C(x) = \{y : s(x, y) \le \hat q\}$. Under exchangeability of calibration and test data, $\mathbb P\,(Y \in C(X)) \ge 1 - \alpha$ for any classifier. Two qualifications apply. First, windows of one recording are dependent, so exchangeability holds at recording level and the finite-sample statement is approximate, with an effective calibration size equal to the number of calibration recordings (hierarchical conformal prediction; Dunn, Wasserman & Ramdas, *JASA* 2023; Lee, Barber & Willett, 2023). Second, in the coverage and gate experiments (E3, E4, X1) the calibration scores of the three folds are pooled and a single $\hat q$ is applied to the pooled test predictions; the recalibration experiments (E5, E6, X3) use one quantile per held-out operating point. Coverage is reported as the empirical fraction of test windows whose true label lies in $C(x)$; the *gap* is coverage minus the nominal $1-\alpha$. In weighted conformal prediction (E6) calibration score $i$ carries a weight $w_i$, the test point weight 1, and $\hat q$ is the $(1-\alpha)$-quantile of the weighted empirical distribution normalised by $\sum_i w_i + 1$ (`cmlib.weighted_conformal_qhat`); with $w_i \equiv 1$ it reduces to the unweighted quantile, and for fixed weights the applicable guarantee is the total-variation bound of Barber et al. (2023).

**The escalation gate.** The cheap configuration is always on. A window is *escalated* to the expensive configuration if and only if its conformal set is not a singleton. The risk level $\alpha$ is the only parameter; the escalation fraction is measured, not tuned. The baseline *threshold gate* escalates when the top-class score $\max_y \hat p(y \mid x)$ falls below a swept threshold $\tau$. With the LAC score, $C(x)$ is a singleton iff the top-class probability is at least $1-\hat q$ and the second-highest is below it; when $1-\hat q > 0.5$ this coincides with a threshold on the top-class score, but at the quantiles observed here ($\hat q$ mostly above 0.5) the two gates are different selection rules, and the comparison is empirical. They are compared *at matched escalation fraction*: for every conformal operating point the threshold-gate curve is linearly interpolated at the same escalation fraction and the difference in macro-F1 is reported.

**Recalibration under shift.** For each held-out operating point, the model is trained on the remaining points and three calibration sets are compared: the *source* calibration recordings only; the source set *pooled* with $k$ labelled recordings from the target point; and the $k$ target recordings *only*. Test recordings are always disjoint from calibration recordings. Results are averaged over five seeds (random choice of the $k$ recordings).
"""

ENERGY_MD = r"""
## Energy model

Operation counts are the wrong currency for a battery-powered node: acquisition dominates. The table lists datasheet power figures for the components of a deployable node (ESP32-S3 with a digital MEMS accelerometer and an isolated current transducer) and, for comparison, the laboratory chain used by the benchmark testbeds. Energy per 160 ms window is power × window duration for the sensing chain. The current transducer figure includes the secondary-side term $I_C + I_P/N_S$ at 5 V for the Paderborn motor (2.3 A, $N_S = 1731$); ignoring that term gives 75 mW typical / 105 mW maximum.

Two consequences follow. First, **one current phase costs ≈25× the energy of a three-axis MEMS accelerometer per window, and two phases ≈50×**: the cascade "cheap current, expensive vibration" is inverted when the currency is joules. Second, the arithmetic is negligible by comparison: a 4096-point FFT on the ESP32-S3 costs about 19 µJ (34 400 cycles extrapolated from the ESP-DSP benchmark table, which stops at 1024 complex points, × 543 pJ per cycle in single-core SIMD mode) against 0.5 mJ to keep the MEMS accelerometer powered during the window. The extrapolated cycle count is the one quantity in this model that is derived rather than measured and is marked as such.

Three caveats apply. The figures model a *dedicated, active* transducer; a passive split-core transformer or Rogowski coil draws no supply power and would make current the cheap tier again. A drive inverter that already samples phase current for control delivers that signal at near-zero marginal energy; in that scenario current is free, but the signal is sampled at the control-loop rate with lower resolution than the laboratory signal, so the current-tier models would have to be trained on inverter-sampled data. Finally, the MCU is not idle during acquisition: the IIS3DWB FIFO holds about an eighth of a 4096-sample three-axis window, so the ESP32-S3 sleeps between eight FIFO drains over SPI (about 20 ms of bus time at the idle floor), ≈2.2 mJ per window or four times the sensor itself (`energy_params.mcu_acquisition_mj`); the current ADC has no FIFO, so on a dedicated current tier the MCU idles in WAITI for the whole window (≈17 mJ). The computation figure is also given on a total-power basis (≈0.07 mJ) that includes the idle floor a duty-cycled node pays. At one window per minute the MEMS tier with its MCU service averages about 46 µW against a 26 µW deep-sleep floor, so the acquisition energy of the cascade matters for near-continuous monitoring.
"""

# =============================================================================
# Notebook 01 — KAIST
# =============================================================================
k = []
k.append(md(r"""
# Conformal sensor escalation under operating-point shift — KAIST dataset

**Scope.** This notebook contains the complete analysis on the KAIST rotating-machine dataset for the study *Calibrate Where You Deploy: Conformal Sensor Escalation Under Operating-Point Shift*. It covers the cost–accuracy frontier of sensing configurations, the learning curve in windows per recording, the empirical coverage of split conformal prediction under two validation protocols, the comparison of a conformal escalation gate with a threshold gate on the top-class score at matched escalation fraction, and the recalibration experiment that quantifies how many recordings from a new operating point restore nominal coverage. The companion notebook `02_paderborn_replication.ipynb` repeats the analysis on the Paderborn KAt bearing dataset and adds the factor-wise attribution of the coverage collapse.

**Data.** KAIST testbed (Jung et al., *Data in Brief* 48:109049, 2023): 45 recordings, five condition classes (normal, inner-race fault, outer-race fault, shaft misalignment, rotor unbalance), three torque loads (0, 2 and 4 N·m), four ICP accelerometers, three current-transformer phases (only the U phase is present in every file and is the one used) and two housing temperatures; vibration and current are both sampled at 25.6 kHz (Jung et al., 2023). Severities (three bearing-fault sizes, three misalignment offsets, five unbalance masses) are pooled per class, which gives 15 recordings per load and a single healthy recording per load. After windowing: 2 250 windows. The effective sample size for any inferential statement is 45 (recordings), not 2 250.

**Reproduction.** `python run_experiments.py --dataset kaist` writes `results/*.csv` (about 10 min on a laptop); this notebook only reads those files. Figures are saved to `figs_en/`. The shared library is `cmlib.py` (cost model, classifiers, validation protocols, conformal prediction, bootstrap); `kaist_lib.py` is the dataset adapter that defines the sensing configurations.
"""))
k.append(code(ENV))
k.append(code(SETUP + """
P  = pd.read_csv("results/pareto.csv")
LC = pd.read_csv("results/learning_curve.csv")
CC = pd.read_csv("results/conformal_coverage.csv")
G  = pd.read_csv("results/gate.csv")
RC = pd.read_csv("results/recalibration.csv")
df = pd.read_parquet("data/kaist_features.parquet")
print(f"{len(df):,} windows · {df.recording_id.nunique()} recordings · {df['class'].nunique()} classes · loads {sorted(df.load.unique())}")
display(df.groupby(["class", "load"]).recording_id.nunique().unstack().fillna(0).astype(int).rename_axis(columns="recordings per load"))
"""))
k.append(md(METHODS_COMMON))
k.append(md(r"""
### Sensing configurations and their cost

Nine configurations are evaluated. Two of them have identical operation counts but require different hardware (one accelerometer with FFT versus one current phase with FFT), which is why the energy model below is needed in addition to the operation count.
"""))
k.append(code("""
import kaist_lib as K
blocks = K.feature_blocks(df)
tab = pd.DataFrame([(R.KAIST_BLOCKS[b][0], R.KAIST_SHORT[b], len(cols), int(K.cost_ops(spec))) for b, (cols, spec) in blocks.items()],
                   columns=["configuration", "abbrev.", "n_features", "ops_per_window"]).set_index("configuration")
display(tab)
"""))
k.append(md(ENERGY_MD))
k.append(code("""
import energy_params as E
et = R.energy_table(E); display(et)
w = 4096/25600
mems, lem = E.IIS3DWB["p_mw"], E.LEM_CKSR_15NP["p_mw"]
print(f"current/MEMS energy ratio per window: {lem/mems:.1f}x per phase, {2*lem/mems:.1f}x for two phases")
print(f"FFT 4096 on ESP32-S3 (extrapolated cycles): {E.fft_energy_uj():.1f} uJ  vs  MEMS sensing per window: {mems*w*1e3:.0f} uJ")
"""))

k.append(md(r"""
## 1. Cost–accuracy frontier (E1)

Macro-F1 of every configuration and classifier under the two protocols. Colour encodes the sensing family, marker shape the classifier; error bars are 95 % cluster-bootstrap intervals over recordings. The grey line joins the Pareto-efficient configurations (best classifier per configuration). The temperature-only configuration (4 operations per window) is omitted from the plot and reported in the table: it is a confounder rather than a candidate configuration, as the shift protocol shows.
"""))
k.append(code("""
R.fig_pareto(P, R.KAIST_BLOCKS, R.KAIST_SHORT, name="kaist_fig1_pareto");
display(R.tab_pareto(P, R.KAIST_BLOCKS))
"""))
k.append(md(r"""
**Observations.** (i) A single accelerometer with nine time-domain features (36 864 operations per window) reaches a macro-F1 of 0.69 under recording-grouped validation and 0.69 under load shift, against 0.73 / 0.75 for four accelerometers with FFT (671 744 operations): an 18-fold reduction in arithmetic and the elimination of three ICP conditioning chains for a loss of about 0.04. (ii) The FFT is dispensable in this dataset: four accelerometers without FFT lose 0.002–0.010 relative to the full configuration, within the confidence interval. (iii) Motor current alone does not sustain the diagnosis: 0.42 under grouped validation and 0.21 under load shift; it is the only configuration whose performance *collapses* rather than degrades. (iv) Temperature behaves as a recording identifier rather than a feature: 0.52 under grouped validation falls to 0.18 under load shift. Grouped validation does not protect against this confounder; the shift protocol exposes it. (v) Adding current to the four accelerometers does not improve on vibration alone.
"""))

k.append(md(r"""
## 2. Learning curve in windows per recording (E2)

Feature extraction stopped at 50 windows per recording. If performance had not saturated, the natural objection "too few windows" would call for re-extraction. The curve below uses 10 to 50 windows per recording with the same grouped protocol.
"""))
k.append(code("""
R.fig_learning_curve(LC, R.KAIST_BLOCKS, name="kaist_fig2_learning_curve");
display(LC.pivot_table(index="n_windows", columns=["block", "model"], values="f1_mean").round(3))
"""))
k.append(md(r"""
The curve is flat (variation below 0.03 across all configurations, within seed-to-seed noise). Additional windows from the same recordings add no information; the binding constraint is the number of recordings, which motivates the second dataset.
"""))

k.append(md(r"""
## 3. Empirical coverage of split conformal prediction (E3)

The cheap tier of the cascade (current, time+FFT) is calibrated on recordings held out from training and evaluated on unseen recordings, under both protocols, for both scores and eight values of α. Panel (a) plots empirical against nominal coverage; panel (b) breaks the shift protocol down by held-out torque load at nominal 80 %.
"""))
k.append(code("""
R.fig_coverage(CC, per_group_label=lambda c: c.replace("cov_", "").replace("Nm", " N·m"), name="kaist_fig3_coverage");
display(R.tab_coverage_gap(CC))
print("coverage per class at nominal 80 % (LAC), mean over classifiers and seeds; class 0 = normal")
sel = CC[(CC.score=="lac") & np.isclose(CC.alpha, 0.20)]
display(sel.groupby("protocol")[[c for c in CC.columns if c.startswith("covclass_")]].mean().round(3))
"""))
k.append(md(r"""
**Under exchangeability the guarantee holds.** With recording-grouped validation the mean gap is +0.045 (LAC) and +0.085 (APS): conservative, as the finite-sample correction and the grouping predict.

**Marginal coverage is not class-conditional coverage.** Even in distribution, the normal class (one recording per load, three in total) is covered far below nominal while the fault classes are covered above it; the marginal guarantee averages over classes, so a false-alarm bound on the healthy class needs class-conditional (Mondrian) calibration, which the healthy-class recordings alone would support.

**Under load shift it fails.** With leave-one-load-out validation the mean LAC gap is −0.148 and the worst case −0.453. At nominal 80 % the gate delivers 55.3 % coverage, and the failure is uneven across operating points (0.41 at 0 N·m, 0.73 at 2 N·m, 0.52 at 4 N·m). APS is less affected on average (−0.013) at the price of much larger sets. This is not a defect of the implementation: the exchangeability assumption between calibration and test recordings is violated by construction, and the measurement quantifies how much of the guarantee is lost.
"""))

k.append(md(r"""
## 4. Conformal gate versus threshold gate (E4)

Two cascades are evaluated: *current (time+FFT) → four accelerometers (time+FFT)* and *one accelerometer (time) → four accelerometers (time+FFT)*. For each, the threshold τ on the top-class score is swept and the conformal gate is run for the eight values of α with both scores. The comparison is made at matched escalation fraction; a positive difference favours the conformal gate.
"""))
k.append(code("""
CASC = {"cur_full->vib_full": "current (time+FFT) → 4 accelerometers (time+FFT)",
        "vib1_time->vib_full": "1 accelerometer (time) → 4 accelerometers (time+FFT)"}
R.fig_gate(G, CASC, model="rf", name="kaist_fig4_gate");
display(R.tab_gate_delta(G, protocol="grouped"))
display(G[G.protocol=="grouped"].groupby("cascade")[["cheap_ops","exp_ops","f1_cheap","f1_exp"]].mean().round(3))
"""))
k.append(md(r"""
**The conformal gate does not buy accuracy.** The mean difference in macro-F1 at matched escalation fraction is −0.000 ± 0.004 over all cascades, scores and seeds; the two gates lie on the same accuracy–escalation curve although, at the quantiles observed, they are different selection rules (see *Shared methodology*). What the conformal gate changes is the *specification*: τ is a dimensionless knob tuned on a validation set, whereas α is a stated risk level from which the escalation fraction, and therefore the energy budget, follows as a measured consequence.

**Which cascade.** The current-first cascade has a 4× ratio in operations and a large accuracy gap between tiers (0.35 → 0.68), but the cheap tier is so weak that the gate escalates 87–100 % of windows at any α ≤ 0.20 and saves nothing. The accelerometer-first cascade has an 18× ratio and a small gap (0.63 → 0.68); at α = 0.20 it escalates 12.3 % of windows for a macro-F1 of 0.655 at a mean cost of 120 k operations against 672 k for the always-on expensive tier. In energy terms, however, the accelerometer-first cascade keeps one accelerometer powered at all times; the two cascades optimise different currencies, which is why the operation count alone cannot decide between them.
"""))

k.append(md(r"""
## 5. Recalibration at the target operating point (E5)

The engineering question that follows from Section 3 is how much labelled data from the new operating point is needed to recover the guarantee. For each held-out load, $k \in \{0, 1, 2, 3, 5, 8\}$ target recordings enter the calibration set either pooled with the source calibration set or replacing it; test recordings are disjoint from calibration recordings (variant `rec`). A second variant (`win`) calibrates on the first $m$ windows of *each* target recording and tests on the remaining windows of the same recordings; it corresponds to "run the machine briefly and label", but calibration and test share recordings, so its coverage is optimistic. The contrast between the two variants is itself informative.
"""))
k.append(code("""
R.fig_recal(RC, group_label=lambda s: f"target {s.replace('Nm',' N·m')}", name="kaist_fig5_recalibration");
print("variant 'rec' (disjoint recordings) — gap by k and calibration mix, mean over both classifiers and α ∈ {0.05, 0.10, 0.20, 0.30}")
display(R.tab_recal(RC))
print("same, per classifier at α = 0.20")
display(pd.concat({m: R.tab_recal(RC, model=m, alpha=0.20) for m in ["logreg", "rf"]}, axis=1))
print("variant 'win' (first m windows of each target recording in calibration; test on the remaining windows of the same recordings)")
d = RC[RC.variant=="win"].assign(gap=lambda d: d.coverage-d.nominal)
display(d.groupby(["k", "model"])["gap"].mean().unstack().assign(both=lambda x: x.mean(axis=1)).round(3).rename_axis(index="m (windows per recording)"))
"""))
k.append(md(r"""
**Five recordings from the new operating point restore nominal coverage.** Averaged over both classifiers and the four risk levels, the gap moves from −0.144 with source calibration only to −0.001 with $k=5$ and +0.010 with $k=8$. This is a commissioning quantity: five short runs at the new operating point, labelled, and the guarantee holds again. The per-classifier view shows that the random forest is far less affected by the shift at α = 0.20 (source gap −0.05) than the logistic regression (−0.41), so the number of recordings needed depends on how over-confident the classifier is off-distribution; the aggregate is the conservative figure to plan with.

**Discarding the source calibration set is better than pooling it.** At $k=3$, calibrating on the three target recordings alone gives a gap of −0.052, while pooling them with the source set gives −0.100, twice as bad. Stale non-conformity scores contaminate the quantile; what matters for the guarantee is exchangeability, not volume. The principled alternative, down-weighting rather than discarding the source scores (Barber et al., 2023), is evaluated in Section 6.

**Calibrating on the first windows of each run recovers less than calibrating on whole runs.** Variant `win` with $m = 5, 10, 20$ windows per recording reaches gaps of −0.078, −0.071 and −0.056, against −0.001 for five whole recordings, even though calibration and test then share recordings. The early windows of a run are evidently not exchangeable with its later windows (start-up transient, thermal drift), which argues for calibration recordings that span the run rather than its first seconds.
"""))

k.append(md(r"""
## 6. Weighted conformal prediction as the alternative to discarding the source set (E6)

Section 5 replaced the source calibration set by the target recordings. The principled alternative is to keep the source scores with a reduced weight (weighted conformal prediction; Tibshirani et al., 2019; Barber et al., 2023). Here the source scores receive a fixed weight $\rho$ and the target scores weight 1, so that $\rho = 1$ is ordinary pooling and $\rho = 0$ is target-only calibration; intermediate values are the fixed-weight schemes a practitioner could set without estimating likelihood ratios. Same five seeds, recordings and α grid as Section 5, so that ρ = 1 reproduces the pooled column and ρ = 0 the target-only column of that section (to within 0.01).
"""))
k.append(code("""
W = pd.read_csv("results/weighted_recalibration.csv")
R.fig_weighted(W, name="kaist_fig6_weighted");
g, s = R.tab_weighted(W); print("coverage gap"); display(g); print("mean set size"); display(s)
"""))
k.append(md(r"""
Down-weighting interpolates between the two extremes and confirms the ordering of Section 5: pooling ($\rho = 1$) is the worst option at every $k \ge 2$, and any $\rho \le 0.3$ recovers most of the coverage of target-only calibration. At $k = 1$ a small residual weight on the source scores ($\rho \approx 0.1$–$0.3$) is better than both extremes, because a single target recording gives a very noisy quantile and the source scores stabilise it. The practical rule is therefore not "discard" but "down-weight heavily": $\rho \le 0.1$ once two or more target recordings are available.
"""))

k.append(md(r"""
## 7. Summary of findings on KAIST

1. One accelerometer with time-domain features is within 0.04 macro-F1 of four accelerometers with FFT at 1/18 of the arithmetic; the FFT is dispensable; current alone collapses under load shift; temperature is a recording-level confounder revealed only by the shift protocol.
2. Performance is saturated in windows per recording; the limiting quantity is the number of recordings.
3. Split conformal coverage holds under recording-grouped validation (+0.045) and collapses under load shift (−0.148 mean, −0.453 worst; 80 % nominal → 55 %); marginal coverage hides a healthy-class coverage of 38 % even in distribution.
4. The conformal gate and a tuned threshold gate are indistinguishable in accuracy at matched escalation fraction (Δ = −0.000 ± 0.004); the conformal gate's contribution is a stated risk level in place of a tuned threshold.
5. Five target-point recordings restore coverage; pooling them with the stale source calibration set is worse than replacing it, and weighted conformal prediction with a small source weight (ρ ≤ 0.1) matches target-only calibration while stabilising the quantile when only one target recording is available.

**Limitations specific to this dataset.** 45 recordings and three loads leave about ten recordings in each calibration set under the shift protocol, so coverage estimates are noisy and the recalibration curve rests on small $k$. The three loads vary torque only, so the collapse cannot be attributed to a specific physical factor. Both limitations are addressed with the Paderborn dataset in the companion notebook.
"""))
build(k, "01_kaist_conformal_gate.ipynb")

# =============================================================================
# Notebook 02 — Paderborn
# =============================================================================
p = []
p.append(md(r"""
# Conformal sensor escalation under operating-point shift — Paderborn replication and factor attribution

**Scope.** This notebook repeats, on the Paderborn KAt bearing dataset, every experiment of `01_kaist_conformal_gate.ipynb` with the same code (`run_experiments.py --dataset paderborn`; only the dataset adapter changes), and adds three analyses that the KAIST data cannot support: validation grouped by physical bearing rather than by recording (X1); attribution of the coverage collapse to a single operating factor, per sensing modality (X2); and transfer from artificially damaged to naturally damaged bearings (X3), produced by `run_paderborn_extra.py`.

**Data.** Paderborn KAt bearing data centre (Lessmeier et al., PHM Society European Conference, 2016): 32 bearings — 6 healthy, 12 with machined (artificial) damage and 14 with damage from accelerated-lifetime tests (real) — recorded at four operating points that differ from the baseline N15_M07_F10 (1500 rpm, 0.7 N·m, 1000 N) in exactly one factor: N09_M07_F10 (speed 900 rpm), N15_M01_F10 (torque 0.1 N·m) and N15_M07_F04 (radial force 400 N). One vibration channel and two motor-current phases are sampled at 64 kHz, plus a bearing-module temperature. Classes are healthy, outer-race damage, inner-race damage and combined damage (the last with only three bearings).

**Harmonisation with KAIST.** Vibration and current are resampled from 64 kHz to 25.6 kHz with an exact 2/5 polyphase filter; windows of 4096 samples with hop 2048 and the same `tfeat`/`ffeat` functions are used, so operation counts are identical across datasets (e.g. one accelerometer with time-domain features costs 36 864 operations in both). This analysis uses the *quick pass*: 5 of the 20 measurements per (bearing, operating point), i.e. 639 recordings and 31 266 windows (one recording failed to parse). The learning-curve result in Section 2 indicates that the remaining measurements would not change the ordering of configurations.

**Reproduction.** `python run_experiments.py --dataset paderborn` (E1–E6, about 45 min) and `python run_paderborn_extra.py` (X1–X3, about 1 h) write `results_paderborn/*.csv`; this notebook only reads them. `paderborn_lib.py` is the dataset adapter over the shared `cmlib.py`.
"""))
p.append(code(ENV))
p.append(code(SETUP + """
import os
P  = pd.read_csv("results_paderborn/pareto.csv")
LC = pd.read_csv("results_paderborn/learning_curve.csv")
CC = pd.read_csv("results_paderborn/conformal_coverage.csv")
G  = pd.read_csv("results_paderborn/gate.csv")
RC = pd.read_csv("results_paderborn/recalibration.csv")
FC = pd.read_csv("results_paderborn/factor_coverage.csv")
DT = pd.read_csv("results_paderborn/damage_transfer.csv")
BP = pd.read_csv("results_paderborn/bearing_pareto.csv") if os.path.exists("results_paderborn/bearing_pareto.csv") else None
BC = pd.read_csv("results_paderborn/bearing_coverage.csv") if os.path.exists("results_paderborn/bearing_coverage.csv") else None
df = pd.read_parquet("data/paderborn_features.parquet")
OPS = {"N15_M07_F10": "baseline (1500 rpm, 0.7 N·m, 1000 N)", "N09_M07_F10": "speed 900 rpm", "N15_M01_F10": "torque 0.1 N·m", "N15_M07_F04": "radial force 400 N"}
print(f"{len(df):,} windows · {df.recording_id.nunique()} recordings · {df.bearing.nunique()} bearings · {df['class'].nunique()} classes")
display(df.groupby(["class", "damage_origin"]).bearing.nunique().rename("bearings").to_frame().T)
display(df.groupby(["class", "load"]).recording_id.nunique().unstack().rename(columns=OPS).rename_axis(columns="recordings per operating point"))
"""))
p.append(md(METHODS_COMMON.replace("leave-one-operating-point-out* (LOLO), which trains on all but one operating point and tests on the held-out one",
                                   "leave-one-operating-point-out* (LOLO), which trains on three operating points and tests on the fourth")))
p.append(md(r"""
**Dataset-specific protocol note.** In the Paderborn data the same physical bearing is recorded at all four operating points and five times per point. Grouping by *recording* therefore allows a bearing to appear in both training and test folds (at different operating points or measurements), which is optimistic for in-distribution accuracy. Section 7 repeats the main experiments with folds grouped by *bearing* to bound that optimism. The shift protocol (LOLO) is unaffected: each test operating point is entirely unseen.
"""))
p.append(code("""
import paderborn_lib as K
blocks = K.feature_blocks(df)
display(pd.DataFrame([(R.PB_BLOCKS[b][0], R.PB_SHORT[b], len(cols), int(K.cost_ops(spec))) for b, (cols, spec) in blocks.items()],
                     columns=["configuration", "abbrev.", "n_features", "ops_per_window"]).set_index("configuration"))
"""))

p.append(md(r"""
## 1. Cost–accuracy frontier (E1)

Same encoding as in the KAIST notebook; the temperature-only configuration is omitted from the plot and reported in the table.
"""))
p.append(code("""
R.fig_pareto(P, R.PB_BLOCKS, R.PB_SHORT, name="pb_fig1_pareto");
display(R.tab_pareto(P, R.PB_BLOCKS))
"""))
p.append(md(r"""
**The KAIST ordering replicates.** Vibration degrades under operating-point shift (one accelerometer with FFT: 0.959 → 0.762); current collapses (two phases with FFT: 0.908 → 0.612 with the random forest, 0.477 with the MLP); fusing accelerometer and current reaches 0.991 in distribution but 0.768 / 0.560 under shift, i.e. additional sensors do not help where it matters; temperature is again a confounder (0.374 → 0.288).

**What differs from KAIST, and matters.** With two current phases sampled at 64 kHz the current-only configuration reaches 0.908 in distribution — nearly on par with vibration — whereas on KAIST it never exceeded 0.42. Motor current therefore *does* carry the diagnosis as long as the operating point is the one it was trained and calibrated on; the question of when it can be trusted is exactly the one the conformal gate is meant to answer, and Section 3 shows that this is where the guarantee fails. Two caveats apply to the in-distribution figures. First, recording-grouped folds let the same physical bearing appear in training and test; Section 7 shows that bearing-grouped validation lowers every in-distribution macro-F1 to 0.4–0.55, so the recording-grouped numbers measure recognition of known bearings at known operating points, not generalisation to new bearings. The shift-protocol numbers, which carry the central claim, are not affected in their interpretation: because the same bearings appear on both sides of the leave-one-operating-point-out split, the degradation they show is attributable to the operating point alone. Second, the two-phase current configuration costs 335 872 operations per window, twice the single-accelerometer configuration with FFT (167 936): current is not the cheap tier even in operations, and in energy the ratio is reversed by a further order of magnitude (energy model in the companion notebook). The only cascade with a cheap tier worth the name is therefore *one accelerometer, time-domain → one accelerometer, time+FFT* (4.6× in operations).
"""))

p.append(md(r"""
## 2. Learning curve in windows per recording (E2)
"""))
p.append(code("""
R.fig_learning_curve(LC, R.PB_BLOCKS, name="pb_fig2_learning_curve");
display(LC.pivot_table(index="n_windows", columns=["block", "model"], values="f1_mean").round(3))
"""))
p.append(md(r"""
Saturated, as on KAIST (one accelerometer with FFT, random forest: 0.950 at 10 windows per recording, 0.959 at 50). The quick pass with 5 of 20 measurements per setting is therefore sufficient for the ordering of configurations; the full pass would narrow intervals, not change conclusions.
"""))

p.append(md(r"""
## 3. Empirical coverage of split conformal prediction (E3)

The cheap tier is now the two-phase current configuration (the direct analogue of the KAIST cascade). Each held-out operating point in panel (b) differs from the baseline in one factor, which is what allows the attribution in Section 8.
"""))
p.append(code("""
R.fig_coverage(CC, per_group_label=lambda c: OPS[c.replace("cov_", "")].replace("baseline ", "baseline\\n"), name="pb_fig3_coverage");
display(R.tab_coverage_gap(CC))
sel = CC[(CC.protocol=="lolo") & (CC.score=="lac") & np.isclose(CC.alpha, 0.20)]
display(sel.groupby("model")[[c for c in CC.columns if c.startswith("cov_")] + ["coverage", "avg_size", "empty_frac"]].mean().rename(columns=lambda c: OPS.get(c.replace("cov_",""), c)).round(3).T)
print("coverage per class at nominal 80 % (LAC), mean over classifiers and seeds; classes: 0 healthy, 1 outer race, 2 inner race, 3 combined")
sel = CC[(CC.score=="lac") & np.isclose(CC.alpha, 0.20)]
display(sel.groupby("protocol")[[c for c in CC.columns if c.startswith("covclass_")]].mean().round(3))
"""))
p.append(md(r"""
**The collapse replicates and is stronger.** Under recording-grouped validation the LAC gap is −0.009 on average (worst −0.039); under leave-one-operating-point-out it is **−0.296 on average and −0.501 in the worst case**, against −0.148 / −0.453 on KAIST. At nominal 80 % the gate delivers 50.0 % (logistic regression) and 32.6 % (random forest). APS stays at or above nominal by producing very large sets (99.8 % coverage with the random forest under shift, mean set size 3.5 of 4 classes), which hides rather than solves the problem. Per class, shift lowers the coverage of every fault class to 0.34–0.41 while the healthy class keeps 0.57: the gate's failure is concentrated on the missed-detection side.

**Per held-out operating point** (LAC, α = 0.20): changing the rotational speed gives 0.33 / 0.01 coverage (logistic regression / random forest) and changing the torque 0.31 / 0.11, while changing the radial force gives 0.69 / 0.65. For the current-based cheap tier, speed and torque destroy exchangeability and radial force barely affects it. Section 8 shows that this attribution is specific to the modality.

**A note on the random forest.** Under shift 62 % of its LAC sets are *empty*: the calibrated quantile is small because in-distribution probabilities are confident, and under shift no class clears it. An empty set is not a singleton, so the gate does escalate; but the phenomenon is a symptom of over-confidence that the logistic regression does not show, and it is reported rather than hidden.
"""))

p.append(md(r"""
## 4. Conformal gate versus threshold gate (E4)
"""))
p.append(code("""
CASC = {"cur2_full->vib1_full": "2 current phases (time+FFT) → 1 accelerometer (time+FFT)",
        "vib1_time->vib1_full": "1 accelerometer (time) → 1 accelerometer (time+FFT)"}
R.fig_gate(G, CASC, model="rf", name="pb_fig4_gate");
display(R.tab_gate_delta(G, protocol="grouped"))
d = G[(G.model=="rf") & (G.gate=="conformal_lac") & (G.cascade=="vib1_time->vib1_full")]
display(d.groupby(["protocol", "knob"])[["esc_frac", "f1", "avg_cost_ops"]].mean().round(3))
"""))
p.append(md(r"""
**Same curve, again.** At matched escalation fraction the conformal gate and the threshold gate are indistinguishable (table above). For the accelerometer-first cascade with the random forest in distribution, α = 0.05 escalates 21.9 % of windows and reaches a macro-F1 of 0.925 at a mean cost of 73.7 k operations, against 0.941 at 167.9 k for the always-on expensive tier (fitted on the same calibration split; the full-training figure in Section 1 is 0.959). Empty sets count as escalation, as the gate definition requires.

**Under shift the gate under-escalates.** With leave-one-operating-point-out validation and α = 0.10, the LAC gate with the random forest escalates only 6 % of windows (against 6 % in distribution) and delivers a macro-F1 of 0.719 instead of 0.890 (the always-on expensive tier gives 0.753 under the same shift): the sets are singletons *and wrong*. A gate whose guarantee has silently expired does not ask for the expensive sensor precisely when it should. On the current tier the same classifier fails the other way, with 62 % empty sets and therefore over-escalation (Section 3); which mode a deployment gets depends on how the cheap model behaves off-distribution and is not observable by the node. This is the safety-relevant reading of the coverage collapse, and the reason recalibration at the deployment point (Section 5) is a requirement rather than a refinement.
"""))

p.append(md(r"""
## 5. Recalibration at the target operating point (E5)
"""))
p.append(code("""
R.fig_recal(RC, group_label=lambda s: OPS[s], name="pb_fig5_recalibration");
print("gap by k and calibration mix, mean over both classifiers and α ∈ {0.05, 0.10, 0.20, 0.30}"); display(R.tab_recal(RC))
print("per classifier at α = 0.20"); display(pd.concat({m: R.tab_recal(RC, model=m, alpha=0.20) for m in ["logreg", "rf"]}, axis=1))
"""))
p.append(md(r"""
**Three to five target recordings restore nominal coverage.** Averaged over both classifiers and the four risk levels, the gap moves from −0.337 with source calibration only to −0.037 at $k=3$ and +0.008 at $k=5$. At α = 0.20 the random forest goes from −0.458 to −0.018 ($k=3$) and +0.006 ($k=5$), the logistic regression from −0.299 to −0.017 and +0.064.

**Pooling with the source calibration set is nearly useless here.** The source set contains about 31 000 windows; $k$ target recordings add a few hundred. The pooled quantile barely moves (−0.337 → −0.311 at $k=8$ in the aggregate; −0.458 → −0.435 for the random forest at α = 0.20). On KAIST pooling was worse than replacing; on Paderborn it is close to doing nothing, because the stale scores dominate by volume. The conclusion is the same and sharper: the calibration set must be *exchangeable* with the deployment data, and volume does not compensate. Per held-out operating point (target-only calibration), the speed and torque shifts are repaired with $k = 2$–$3$ (gaps +0.01 and −0.09 at $k = 2$, +0.08 and +0.06 at $k = 3$), the radial-force shift needs $k = 5$ (−0.24 at $k = 3$, −0.01 at $k = 5$).
"""))

p.append(md(r"""
## 5b. Weighted conformal prediction (E6)

As in the KAIST notebook: source scores keep a fixed weight $\rho$ in the pooled calibration set ($\rho = 1$ pooled, $\rho = 0$ target only). With about 31 000 source windows against a few hundred target windows, the question is whether any fixed weight short of zero can neutralise the stale set.
"""))
p.append(code("""
W = pd.read_csv("results_paderborn/weighted_recalibration.csv") if os.path.exists("results_paderborn/weighted_recalibration.csv") else None
if W is not None:
    R.fig_weighted(W, name="pb_fig5b_weighted");
    g, s = R.tab_weighted(W); print("coverage gap"); display(g); print("mean set size"); display(s)
else:
    print("weighted_recalibration.csv not found — run `python run_experiments.py --dataset paderborn e6`")
"""))
p.append(md(r"""
With a source set two orders of magnitude larger than the target set, a weight of $\rho = 0.3$ still leaves the source scores in control of the quantile; only $\rho \le 0.03$ approaches target-only calibration. What governs the outcome is the target share of the normalised weight, $n_{\mathrm{tgt}} / (n_{\mathrm{tgt}} + \rho\, n_{\mathrm{src}})$: with $n_{\mathrm{src}} \approx 7\,700$ windows and a few hundred target windows, $\rho = 0.3$ leaves that share below 0.1. Likelihood-ratio weights (Tibshirani et al., 2019) are density ratios, not functions of the set sizes, and were not evaluated. For a commissioning rule the simple statement stands: once three target recordings exist, calibrate on them.
"""))

p.append(md(r"""
## 6. Summary of the replication

| quantity | KAIST | Paderborn |
|---|---|---|
| mean LAC gap, recording-grouped | +0.045 | −0.009 |
| mean LAC gap, bearing-grouped | — | +0.002 to +0.014 |
| mean LAC gap, operating-point shift | −0.148 | −0.296 |
| worst LAC gap, shift | −0.453 | −0.501 |
| coverage delivered at nominal 80 %, shift | 55.3 % | 50.0 % (LR) / 32.6 % (RF) |
| Δ macro-F1 conformal − threshold gate, matched escalation | −0.000 ± 0.004 | −0.002 ± 0.004 |
| target recordings to restore coverage (mean over classifiers and α) | 5 | 3–5 |
| pooled vs replaced calibration at $k=3$ (same aggregation) | −0.100 vs −0.052 | −0.327 vs −0.037 |

Two independent benchmarks, different machines (a motor-driven shaft with four accelerometers; a bearing test rig with two current phases), different classes, the same pipeline and the same conclusions.
"""))

p.append(md(r"""
## 7. Validation grouped by bearing (X1)

Folds are grouped by physical bearing (stratified 3-fold, three seeds; the combined-damage class has only three bearings, which caps the number of folds). Calibration recordings for the coverage experiment are also carved by bearing.
"""))
p.append(code("""
if BP is not None:
    R.fig_protocol_compare(P, BP, R.PB_BLOCKS, R.PB_SHORT, name="pb_fig6_bearing_grouped");
    t = R.tab_pareto(P, R.PB_BLOCKS)[["grouped_F1", "lolo_F1"]].join(
        R.tab_pareto(BP, R.PB_BLOCKS, protocols=("bearing",))[["bearing_F1", "bearing_CI95"]])
    display(t)
    bc = BC.copy(); bc["gap"] = bc.coverage - bc.nominal
    print("coverage gap with bearing-grouped folds and bearing-carved calibration (cheap tiers)")
    display(bc.groupby(["block", "score"])["gap"].agg(mean="mean", worst="min").round(3))
else:
    print("bearing_pareto.csv not found — run `python run_paderborn_extra.py x1`")
"""))
p.append(md(r"""
**Recording-grouped validation overstates in-distribution accuracy by a wide margin on this dataset.** With folds grouped by bearing, the single-accelerometer configuration with FFT falls from 0.959 to 0.553 (random forest, 95 % CI [0.40, 0.67]), the two-phase current configuration from 0.908 to 0.458, and the fusion configuration from 0.991 to 0.504. Hand-crafted statistics with shallow classifiers recognise *bearings* far better than they recognise *damage classes* on unseen bearings — a leakage mode documented for this benchmark (Vieira et al., 2025; Kaya & Jobani, 2026). The bearing-grouped figures are the honest in-distribution reference for the Paderborn data and are the ones to compare with the literature.

**The conformal guarantee is unaffected by the weakness of the classifier.** With bearing-grouped folds and bearing-carved calibration, the LAC coverage gap is +0.002 (current) and +0.012–0.014 (vibration): coverage holds whenever calibration and test are exchangeable, whatever the accuracy, which is the property the gate relies on. The guarantee fails under operating-point shift (Section 3), not under bearing novelty.

**What this changes in the reading of the shift results.** The leave-one-operating-point-out split shares bearings between training and test, so the coverage collapse it exposes is attributable to the operating point alone and not confounded with unseen bearings; the same holds for the factor attribution of Section 8. The in-distribution comparison between current and vibration (Section 1), on the other hand, must be read as bearing-level recognition; on unseen bearings the two modalities are closer (0.46–0.53 vs 0.55) and both are modest.
"""))

p.append(md(r"""
## 8. Which factor breaks exchangeability, per sensing modality (X2)

Models are fitted and calibrated on recordings of the baseline operating point only (fit / calibration / in-domain test split by recording) and evaluated on each neighbouring operating point. Because each neighbour changes one factor, the loss of coverage can be attributed to that factor. The experiment is run for the current-only tier, the single-accelerometer time-domain tier and the full vibration tier.
"""))
p.append(code("""
R.fig_factor_modality(FC, R.PB_BLOCKS, alpha=0.20, score="lac", name="pb_fig7_factor_modality");
s = FC[(FC.score=="lac") & np.isclose(FC.alpha, 0.20)]
print("empirical coverage at nominal 80 % (LAC)"); display(s.pivot_table(index=["block","model"], columns="factor", values="coverage")[R.FACTOR_ORDER].rename(columns=R.FACTOR_LABEL).round(3))
print("macro-F1 of the same models on the same targets"); display(s.pivot_table(index=["block","model"], columns="factor", values="f1")[R.FACTOR_ORDER].rename(columns=R.FACTOR_LABEL).round(3))
"""))
p.append(md(r"""
**The attribution is modality-specific.** For the vibration tiers, a change of **rotational speed** destroys coverage (0.07–0.50 at nominal 80 %) while a change of **torque leaves it essentially intact** (0.67–0.82, with the logistic regression at nominal) and a change of radial force degrades it moderately (0.27–0.73). For the current tier, both speed and torque destroy coverage (0.01–0.38). Macro-F1 on the same targets tells the same story (vibration under torque shift: 0.64–0.90; under speed shift: 0.22–0.31).

This reconciles the result with accuracy-based studies of domain shift on Paderborn, which report that rotational speed drives the degradation while load and radial force have small effects (Panić et al., *Reliability Engineering & System Safety*, 2027; Alam et al., 2025): those studies use vibration. The torque sensitivity observed in Section 3 belongs to the *current-based* cheap tier, as the KAIST load-shift results (vibration 0.69 → 0.69, current 0.42 → 0.21) independently confirm. The physics is consistent with the attribution. Speed scales the impact rate and the vibration amplitude, so every time-domain statistic moves (which is why the time-domain-only vibration tier collapses as well), and on an inverter-fed motor it moves the current fundamental and every fault sideband. A torque change from 0.7 to 0.1 N·m is a roughly seven-fold change in q-axis current: every amplitude statistic of the current channel rescales while the fault sidebands stay small relative to the fundamental, the classical load dependence of motor-current signature analysis, which the gate inherits; the vibration signature is mainly unaffected. Radial force changes the load zone and hence the amplitude of outer-race impulses. Whether speed-normalised (order-tracked) features would remove the speed sensitivity is an untested control.

The consequence for cascade design is direct. A current-first cascade must be recalibrated whenever speed *or* torque changes; an accelerometer-first cascade when speed changes and, to a lesser degree, when radial force changes. Which operating factors a plant varies is therefore part of the sensor-selection decision, together with energy.
"""))

p.append(md(r"""
## 9. Transfer from artificial to real damage (X3)

Models are trained on bearings with machined damage (plus three healthy bearings) and evaluated on bearings with damage from accelerated-lifetime tests (plus the other three healthy bearings), and vice versa. The machined-damage set has no combined-damage class, so the artificial→real direction tests a three-class model on four classes and its macro-F1 is bounded by 0.75 by construction. Calibration is carved by bearing from the training side; recalibration uses $k$ recordings of the test side, as in Section 5.
"""))
p.append(code("""
s = DT[(DT.score=="lac") & np.isclose(DT.alpha, 0.20)]
print("macro-F1 of source-trained models on the target damage origin (chance level for 4 classes ≈ 0.25)")
display(s.groupby(["train","test","block","model"]).f1_target.mean().unstack().round(3))
R.fig_damage_transfer(DT, {b: R.PB_BLOCKS[b] for b in ["cur2_full","vib1_time","vib1_full"]}, model="rf", name="pb_fig8_damage_transfer");
t = s[s.model=="rf"].assign(gap=lambda d: d.coverage-d.nominal)
display(t.pivot_table(index=["train","block","k"], columns="mix", values=["gap","avg_size"]).round(3))
"""))
p.append(md(r"""
**Hand-crafted features do not transfer between damage origins.** Macro-F1 on the unseen damage origin is 0.19–0.29 for every tier and classifier, i.e. chance level for four classes, in both directions. This is a failure of the classifier, not only of its calibration, and it is consistent with the known difficulty of the artificial-to-real split on this benchmark.

**Recalibration cannot rescue an uninformative classifier.** With source calibration the gap is −0.37 (current) and −0.13 to −0.17 (vibration); target-only recalibration moves coverage towards nominal, but erratically across $k$ and only by inflating the sets (see `avg_size`): when the classifier is at chance, the only set with 80 % coverage is close to the full label set, and a gate built on it would escalate every window. Operating-point shift (Sections 3–5 and 8) is a *calibration* problem that a few labelled recordings fix; damage-origin shift is a *representation* problem that they do not. The distinction bounds the claim of this work: recalibration at the deployment point restores the guarantee when the model remains informative there.
"""))

p.append(md(r"""
## 10. Limitations and open items

* The quick pass uses 5 of 20 measurements per setting; intervals would narrow with the full pass but the learning curve indicates no change in ordering.
* The combined-damage class has three bearings; macro-F1 is sensitive to it.
* Recording-grouped in-distribution numbers are strongly optimistic for this dataset (bearing identity leaks); bearing-grouped numbers (Section 7) are the honest reference and should be the ones reported for accuracy.
* Energy figures are datasheet-derived; the FFT cycle count on the ESP32-S3 is extrapolated and remains to be measured on hardware.
* Weighted conformal prediction was evaluated only with fixed source weights (Section 5b); likelihood-ratio weighting and online (adaptive) conformal inference remain to be compared.
* The 3–5 recordings of the commissioning rule must be *labelled by class*; on a production machine only healthy recordings exist at a new operating point, which recalibrate the healthy-class quantile alone (class-conditional / Mondrian calibration).
* No deep baseline on raw signals is included; the phenomena reported concern the calibration of a given classifier, but the magnitude of the transfer failures in Section 9 may differ for learned representations.
"""))
build(p, "02_paderborn_replication.ipynb")
