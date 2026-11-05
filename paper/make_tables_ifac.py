#!/usr/bin/env python3
"""Generate the LaTeX tables of the IFAC manuscript from the result CSVs.

    python paper/make_tables_ifac.py        # run from the repository root
Writes paper/tables_ifac/*.tex and paper/numbers_ifac.tex (macros with the headline numbers).
"""
import os, sys
import numpy as np, pandas as pd
sys.path.insert(0, os.getcwd())
import report_lib as R
import energy_params as E

OUT = "paper/tables_ifac"; os.makedirs(OUT, exist_ok=True)
K = {n: pd.read_csv(f"results/{n}.csv") for n in ["pareto", "conformal_coverage", "gate", "recalibration", "weighted_recalibration"]}
P = {n: pd.read_csv(f"results_paderborn/{n}.csv") for n in ["pareto", "conformal_coverage", "gate", "recalibration", "weighted_recalibration", "factor_coverage", "bearing_pareto", "bearing_coverage", "damage_transfer"]}

def f3(x): return f"{x:.3f}"
def w(name, s, colsep="3.5pt"):
    if "table*" in s:   # full-width tables fit at 8 pt; never enlarge them
        s = s.replace("\\begin{tabular}", "\\setlength{\\tabcolsep}{" + colsep + "}\\begin{tabular}")
    else:
        s = s.replace("\\begin{tabular}", "\\setlength{\\tabcolsep}{" + colsep + "}\\resizebox{\\columnwidth}{!}{\\begin{tabular}").replace("\\end{tabular}", "\\end{tabular}}")
    open(f"{OUT}/{name}.tex", "w").write(s); print("wrote", name)

# ---------------------------------------------------------------- frontier (with 95 % cluster-bootstrap CIs)
SHALLOW = ["logreg", "rf"]          # the two classifiers used in every conformal experiment
def best(p, block, prot):
    d = p[(p.block == block) & (p.protocol == prot) & p.model.isin(SHALLOW)]
    if d.empty: return np.nan, "--"
    r = d.loc[d.f1_mean.idxmax()]
    return r.f1_mean, f"[{r.boot_lo:.2f}, {r.boot_hi:.2f}]"
rows = []
for b, lab in [("cur_full", "current, time+FFT"), ("vib1_time", "1 accel., time"), ("vib_full", "4 accel., time+FFT")]:
    g, gci = best(K["pareto"], b, "grouped"); l, lci = best(K["pareto"], b, "lolo")
    rows.append(("KAIST", lab, int(K["pareto"][K["pareto"].block == b].cost_ops.iloc[0]), g, gci, np.nan, "--", l, lci))
for b, lab in [("cur2_full", "2 current phases, time+FFT"), ("vib1_time", "1 accel., time"), ("vib1_full", "1 accel., time+FFT"), ("vib_cur", "1 accel. + 2 phases")]:
    g, gci = best(P["pareto"], b, "grouped"); l, lci = best(P["pareto"], b, "lolo")
    bp = P["bearing_pareto"][(P["bearing_pareto"].block == b) & P["bearing_pareto"].model.isin(SHALLOW)]; br = bp.loc[bp.f1_mean.idxmax()]
    rows.append(("Paderborn", lab, int(P["pareto"][P["pareto"].block == b].cost_ops.iloc[0]), g, gci, br.f1_mean, f"[{br.boot_lo:.2f}, {br.boot_hi:.2f}]", l, lci))
def mlp_deficit():
    out = []
    for p, blocks in [(K["pareto"], ["cur_full", "vib1_time", "vib1_full", "vib_full", "vib_cur"]), (P["pareto"], ["cur2_full", "vib1_time", "vib1_full", "vib_cur"]), (P["bearing_pareto"], ["cur2_full", "vib1_time", "vib1_full", "vib_cur"])]:
        for (b, pr), d in p[p.block.isin(blocks)].groupby(["block", "protocol"]):
            out.append(d.f1_mean.max() - d[d.model.isin(SHALLOW)].f1_mean.max())
    return max(out)
MLP_DEFICIT = mlp_deficit()
s_ = ["\\begin{table*}[tb]\\centering\\footnotesize",
     "\\caption{Cost--accuracy frontier: macro-F1 of the better of LR and RF per tier (mean over three seeds for the grouped protocols; one run per held-out point under shift) with 95\\,\\% percentile intervals of a cluster bootstrap over recordings (bearings for the bearing-grouped column) of the seed-0 predictions. Operations per 160\\,ms window.}",
     "\\label{tab:frontier}",
     "\\begin{tabular}{llrlll}\\hline",
     " & tier & ops / window & recording-grouped & bearing-grouped & operating-point shift \\\\ \\hline"]
last = None
for ds, lab, ops, g, gci, bg, bci, l, lci in rows:
    opsf = f"{ops:,}".replace(",", "\\,")
    bcol = "--" if np.isnan(bg) else f"{bg:.3f} {bci}"
    s_.append(f"{ds if ds != last else ''} & {lab} & {opsf} & {g:.3f} {gci} & {bcol} & {l:.3f} {lci} \\\\")
    last = ds
s_ += ["\\hline\\end{tabular}\\end{table*}"]
w("tab_frontier", "\n".join(s_))

# ---------------------------------------------------------------- coverage gaps
def classcov(d20):
    """coverage at alpha = 0.20 for the healthy class (index 0) and mean over the fault classes."""
    cols = [c for c in d20.columns if c.startswith("covclass_")]
    if not cols: return np.nan, np.nan
    faulty = [c for c in cols if c != "covclass_0"]
    return d20["covclass_0"].mean(), d20[faulty].mean(axis=1).mean()
def gaps(cc):
    cc = cc.copy(); cc["gap"] = cc.coverage - cc.nominal
    out = {}
    for prot in ["grouped", "lolo"]:
        d = cc[(cc.protocol == prot) & (cc.score == "lac")]
        d20 = d[np.isclose(d.alpha, 0.2)]
        out[prot] = (d.gap.mean(), d.gap.min(), d20.coverage.mean(), d20.coverage.std(), *classcov(d20))
    return out
gk, gp = gaps(K["conformal_coverage"]), gaps(P["conformal_coverage"])
bc = P["bearing_coverage"].copy(); bc = bc[bc.block == "cur2_full"]; bc["gap"] = bc.coverage - bc.nominal
bcl = bc[bc.score == "lac"]; bcl20 = bcl[np.isclose(bcl.alpha, 0.2)]
def cov80_by_model(cc, prot):
    d = cc[(cc.protocol == prot) & (cc.score == "lac") & np.isclose(cc.alpha, 0.2)]
    return {m: (d[d.model == m].coverage.mean(), d[d.model == m].coverage.std()) for m in ["logreg", "rf"]}
cov80 = {m: v[0] for m, v in cov80_by_model(P["conformal_coverage"], "lolo").items()}
cov80sd = {m: v[1] for m, v in cov80_by_model(P["conformal_coverage"], "lolo").items()}
cov80k = cov80_by_model(K["conformal_coverage"], "lolo")
def pm(m, sd): return f"{100*m:.1f} $\\pm$ {100*sd:.1f}"
def lrrf(cc, prot):
    v = cov80_by_model(cc, prot); return f"{100*v['logreg'][0]:.1f}$\\pm${100*v['logreg'][1]:.1f} / {100*v['rf'][0]:.1f}$\\pm${100*v['rf'][1]:.1f}"
def perpoint_worst(cc):
    """worst per-held-out-point gap of the pooled shift protocol (cov_<point> columns of E3)."""
    d = cc[(cc.protocol == "lolo") & (cc.score == "lac")]
    cols = [c for c in d.columns if c.startswith("cov_")]
    return float(d[cols].sub(d.nominal, axis=0).min().min())
ppwK, ppwP = perpoint_worst(K["conformal_coverage"]), perpoint_worst(P["conformal_coverage"])
def fullset_cells(cc):
    d = cc[(cc.protocol == "grouped") & (cc.score == "lac") & (cc.model == "rf") & (cc.alpha <= 0.2001)]
    return int((d.qhat >= 0.9999).sum()), len(d)
def hf(h, f): return "--" if h != h else f"{100*h:.0f} / {100*f:.0f}"
bh, bf = classcov(bcl20)
s = ["\\begin{table}[tb]\\centering\\footnotesize",
     "\\caption{Coverage gap (empirical $-$ nominal) of LAC sets for the current tier (current, time+FFT on KAIST; two phases on Paderborn): mean and worst cell over the $\\alpha$ grid, classifiers and seeds (48 cells per row); coverage at nominal 80\\,\\% by LR / RF, mean $\\pm$ s.d.\\ over seeds, and the same averaged over classifiers for the healthy and the fault classes. in = recording-grouped, bearing = bearing-grouped, shift = operating-point shift.}",
     "\\label{tab:gap}",
     "\\begin{tabular}{@{}llcccc@{}}\\hline",
     "dataset & protocol & mean & worst & LR / RF at 80\\,\\% & healthy / faulty \\\\ \\hline",
     f"KAIST & in & ${gk['grouped'][0]:+.3f}$ & ${gk['grouped'][1]:+.3f}$ & {lrrf(K['conformal_coverage'], 'grouped')}& {hf(gk['grouped'][4], gk['grouped'][5])} \\\\",
     f"KAIST & shift & ${gk['lolo'][0]:+.3f}$ & ${gk['lolo'][1]:+.3f}$ & {lrrf(K['conformal_coverage'], 'lolo')}& {hf(gk['lolo'][4], gk['lolo'][5])} \\\\",
     f"Paderborn & in & ${gp['grouped'][0]:+.3f}$ & ${gp['grouped'][1]:+.3f}$ & {lrrf(P['conformal_coverage'], 'grouped')}& {hf(gp['grouped'][4], gp['grouped'][5])} \\\\",
     f"Paderborn & bearing & ${bcl.gap.mean():+.3f}$ & ${bcl.gap.min():+.3f}$ & {100*bcl20[bcl20.model=='logreg'].coverage.mean():.1f}$\\pm${100*bcl20[bcl20.model=='logreg'].coverage.std():.1f} / {100*bcl20[bcl20.model=='rf'].coverage.mean():.1f}$\\pm${100*bcl20[bcl20.model=='rf'].coverage.std():.1f} & {hf(bh, bf)} \\\\",
     f"Paderborn & shift & ${gp['lolo'][0]:+.3f}$ & ${gp['lolo'][1]:+.3f}$ & {lrrf(P['conformal_coverage'], 'lolo')}& {hf(gp['lolo'][4], gp['lolo'][5])} \\\\",
     "\\hline\\end{tabular}\\end{table}"]
w("tab_gap", "\n".join(s), colsep="2pt")

# ---------------------------------------------------------------- gate delta
LAC = ("conformal_lac",)          # the manuscript reports the LAC gate only
dk = R.tab_gate_delta(K["gate"], gates=LAC); dp = R.tab_gate_delta(P["gate"], gates=LAC)
dkl = R.tab_gate_delta(K["gate"], protocol="lolo", gates=LAC); dpl = R.tab_gate_delta(P["gate"], protocol="lolo", gates=LAC)
s = ["\\begin{table}[tb]\\centering\\footnotesize",
     "\\caption{Macro-F1 difference, conformal gate $-$ threshold on the top-class score, at matched escalation fraction (threshold curve interpolated), in-distribution folds; mean $\\pm$ s.d.\\ over matched points, scores, classifiers and seeds.}",
     "\\label{tab:gate}",
     "\\begin{tabular}{llc}\\hline",
     "dataset & cascade (cheap $\\to$ expensive) & $\\Delta$ macro-F1 \\\\ \\hline"]
names = {"cur_full->vib_full": "current $\\to$ 4 accel.+FFT", "vib1_time->vib_full": "1 accel.\\ time $\\to$ 4 accel.+FFT",
         "cur2_full->vib1_full": "2 phases $\\to$ 1 accel.+FFT", "vib1_time->vib1_full": "1 accel.\\ time $\\to$ 1 accel.+FFT"}
for ds, d in [("KAIST", dk), ("Paderborn", dp)]:
    for casc in [c for c in d.index.get_level_values(0).unique() if c != "all"]:
        sub = d.loc[casc]
        m = (sub["mean"] * sub["count"]).sum() / sub["count"].sum()
        s.append(f"{ds} & {names[casc]} & ${m:+.4f}$ \\\\")
    s.append(f"{ds} & all & ${d.loc[('all','all'),'mean']:+.4f} \\pm {d.loc[('all','all'),'std']:.4f}$ \\\\")
s += ["\\hline\\end{tabular}\\end{table}"]
# gate-delta table replaced by a sentence in the manuscript (numbers via the gateDelta macros)

# ---------------------------------------------------------------- recalibration (mean over classifiers and alpha; s.d. over seeds)
def recal_stats(r):
    d = r[r.variant == "rec"].copy(); d["gap"] = d.coverage - d.nominal
    per_seed = d.groupby(["k", "mix", "seed"])["gap"].mean().reset_index()
    return per_seed.groupby(["k", "mix"])["gap"].agg(["mean", "std"])
rk, rp = recal_stats(K["recalibration"]), recal_stats(P["recalibration"])
tk = R.tab_recal(K["recalibration"]); tp = R.tab_recal(P["recalibration"])
s = ["\\begin{table}[tb]\\centering\\footnotesize",
     "\\caption{Recalibration at the target operating point: coverage gap (LAC) by number $k$ of target recordings in the calibration set and by composition (source recordings pooled with the $k$ target recordings; the $k$ target recordings only), mean over classifiers, $\\alpha\\in\\{0.05,0.10,0.20,0.30\\}$ and held-out points, $\\pm$ s.d.\\ over five seeds (random draw of the $k$ recordings, not stratified by class). Source-only calibration gives " + f"${rk.loc[(0,'source'),'mean']:+.3f}\\pm{rk.loc[(0,'source'),'std']:.3f}$ (KAIST) and ${rp.loc[(0,'source'),'mean']:+.3f}\\pm{rp.loc[(0,'source'),'std']:.3f}$ (Paderborn)" + ".}",
     "\\label{tab:recal}",
     "\\begin{tabular}{c cc c cc}\\hline",
     " & \\multicolumn{2}{c}{KAIST} & & \\multicolumn{2}{c}{Paderborn} \\\\",
     "$k$ & pooled & target & & pooled & target \\\\ \\hline"]
def cell(st, k, mix):
    if (k, mix) not in st.index: return "--"
    m, sd = st.loc[(k, mix), "mean"], st.loc[(k, mix), "std"]
    return f"${m:+.3f}\\pm{sd:.3f}$" if sd == sd else f"${m:+.3f}$"
for k in [1, 2, 3, 5, 8]:
    s.append(f"{k} & {cell(rk,k,'source+target')} & {cell(rk,k,'target')} & & {cell(rp,k,'source+target')} & {cell(rp,k,'target')} \\\\")
s += ["\\hline\\end{tabular}\\end{table}"]
w("tab_recal", "\n".join(s))

# ---------------------------------------------------------------- weighted (compact: k=2,5 rows x rho)
gkw, _ = R.tab_weighted(K["weighted_recalibration"]); gpw, _ = R.tab_weighted(P["weighted_recalibration"])
rhos = [1.0, 0.3, 0.1, 0.0]
s = ["\\begin{table}[tb]\\centering\\footnotesize",
     "\\caption{Weighted conformal prediction: coverage gap with source scores weighted $\\rho$ and target scores weighted 1, same seeds, $\\alpha$ grid and recordings as Table~\\ref{tab:recal} ($\\rho=1$ matches its pooled column and $\\rho=0$ its target-only column to within 0.01).}",
     "\\label{tab:weighted}",
     "\\begin{tabular}{lc" + "c" * len(rhos) + "}\\hline",
     "dataset & $k$ & " + " & ".join(f"$\\rho={r:g}$" for r in rhos) + " \\\\ \\hline"]
for ds, g in [("KAIST", gkw), ("Paderborn", gpw)]:
    for k in [1, 2, 3, 5]:
        s.append(f"{ds} & {k} & " + " & ".join(f"{g.loc[k, r]:+.3f}" for r in rhos) + " \\\\")
s += ["\\hline\\end{tabular}\\end{table}"]
# weighted-conformal table replaced by a paragraph in the manuscript (numbers via the w* macros)

# ---------------------------------------------------------------- factor x modality + failure modes (X2, alpha = 0.20, LAC)
fc = P["factor_coverage"]; fc = fc[(fc.score == "lac") & np.isclose(fc.alpha, 0.2)]
piv = fc.pivot_table(index=["block", "model"], columns="factor", values="coverage")
pivf = fc.pivot_table(index=["block", "model"], columns="factor", values="f1")
ind = fc[fc.factor == "none (in-domain)"].groupby(["block", "model"])[["coverage", "singleton_frac", "empty_frac", "f1"]].mean()
sh = fc[fc.factor != "none (in-domain)"].groupby(["block", "model"])[["coverage", "singleton_frac", "empty_frac", "f1"]].mean()
tiers = {"cur2_full": "2 current phases, time+FFT", "vib1_time": "1 accel., time", "vib1_full": "1 accel., time+FFT"}
s = ["\\begin{table*}[tb]\\centering\\footnotesize",
     "\\caption{Paderborn, LAC at nominal 80\\,\\%, classifiers fitted and calibrated at the baseline operating point: coverage (macro-F1) on held-out baseline recordings (in; recording-grouped, so the macro-F1 reference is optimistic) and on each point that changes one factor; coverage, singleton and empty-set fractions over the three shifted points; seed s.d.\\ $\\le0.12$.}",
     "\\label{tab:factor}",
     "\\begin{tabular}{llcccc ccc}\\hline",
     " & & \\multicolumn{4}{c}{coverage (macro-F1) by factor changed} & \\multicolumn{3}{c}{shift, pooled} \\\\",
     "tier & classifier & in & speed & torque & radial force & coverage & singletons & empty \\\\ \\hline"]
for b_, lab in tiers.items():
    for m, ml in [("logreg", "LR"), ("rf", "RF")]:
        r = piv.loc[(b_, m)]; q = pivf.loc[(b_, m)]; h = sh.loc[(b_, m)]
        c = lambda f: f"{r[f]:.2f} ({q[f]:.2f})"
        s.append(f"{lab if m=='logreg' else ''} & {ml} & {c('none (in-domain)')} & {c('speed_rpm')} & {c('torque_nm')} & {c('force_n')} & {h.coverage:.2f} & {h.singleton_frac:.2f} & {h.empty_frac:.2f} \\\\")
s += ["\\hline\\end{tabular}\\end{table*}"]
w("tab_factor", "\n".join(s))

# ---------------------------------------------------------------- energy
wdur = 4096 / 25600
rows = [("IIS3DWB MEMS accel., 3 axes, on-chip ADC", E.IIS3DWB["p_mw"], None),
        ("LEM CKSR 15-NP transducer + ADC, per phase", E.LEM_CKSR_15NP["p_mw"] + E.ADS7042["p_mw_at"](25_600), None),
        ("TMCS1100 Hall sensor + ADC, per phase", E.TMCS1100["p_mw"] + E.ADS7042["p_mw_at"](25_600), None),
        ("MCU, MEMS window: light sleep + 10 FIFO drains", None, E.mcu_acquisition_mj()),
        ("MCU, current window (no FIFO): idle", E.ESP32S3["p_waiti_mw"], None)]
compute_uj = (9 * 4096 + E.FFT_4096_CYCLES_EXTRAPOLATED) * E.PJ_PER_CORE_CYCLE["single_simd128"] * 1e-6
compute_total_uj = (9 * 4096 + E.FFT_4096_CYCLES_EXTRAPOLATED) * (E.PJ_PER_CORE_CYCLE["single_simd128"] + E.ESP32S3["p_waiti_mw"] / 240.0 * 1e3) * 1e-6
s = ["\\begin{table}[tb]\\centering\\footnotesize",
     "\\caption{Datasheet typical power of the sensing chains and of the MCU (ESP32-S3, 240\\,MHz, peripheral clocks off; other settings move the MCU rows by up to about 3$\\times$), and energy per 160\\,ms window. Last row: computation of the accelerometer time+FFT tier (" + f"{9*4096 + E.FFT_4096_CYCLES_EXTRAPOLATED:,}".replace(",", "\\,") + " cycles, 16-bit ESP-DSP FFT, extrapolated), on a marginal (" + f"{E.PJ_PER_CORE_CYCLE['single_simd128']:.0f}" + "\\,pJ per cycle) / total-power basis.}",
     "\\label{tab:energy}",
     "\\begin{tabular}{lrr}\\hline",
     "component & mW & mJ / window \\\\ \\hline"]
for lab, p, mj in rows:
    s.append(f"{lab} & {p:.2f} & {p*wdur:.2f} \\\\" if mj is None else f"{lab} & -- & {mj:.2f} \\\\")
s.append(f"MCU compute, accel.\\ time+FFT (marg.\\ / total) & -- & {compute_uj/1000:.3f} / {compute_total_uj/1000:.3f} \\\\")
s += ["\\hline\\end{tabular}\\end{table}"]
w("tab_energy", "\n".join(s))


# ---------------------------------------------------------------- gate under shift (Paderborn, LAC)
gp_ = P["gate"]
def gsel(casc, model, knob, prot):
    d = gp_[(gp_.gate == "conformal_lac") & (gp_.cascade == casc) & (gp_.model == model) & (gp_.protocol == prot) & np.isclose(gp_.knob, knob)]
    return d.esc_frac.mean(), d.f1.mean(), d.f1_exp.mean(), d.f1_cheap.mean()
s = ["\\begin{table}[tb]\\centering\\footnotesize",
     "\\caption{Paderborn: the LAC gate at a fixed $\\alpha$ in distribution (recording-grouped) and under operating-point shift, mean over seeds. esc = fraction of windows escalated; F1 = macro-F1 of the cascade; exp.\\ = macro-F1 of the expensive tier always on, fitted without the calibration recordings (hence below Table~\\ref{tab:frontier}).}",
     "\\label{tab:shift}",
     "\\begin{tabular}{llc ccc ccc}\\hline",
     " & & & \\multicolumn{3}{c}{in distribution} & \\multicolumn{3}{c}{operating-point shift} \\\\",
     "cascade & classifier & $\\alpha$ & esc & F1 & exp. & esc & F1 & exp. \\\\ \\hline"]
for casc, lab in [("vib1_time->vib1_full", "1 accel.\\ time $\\to$ 1 accel.+FFT"), ("cur2_full->vib1_full", "2 phases $\\to$ 1 accel.+FFT")]:
    for model, ml in [("logreg", "LR"), ("rf", "RF")]:
        for knob in ([0.10] if casc.startswith("vib") else [0.05]):
            g = gsel(casc, model, knob, "grouped"); l = gsel(casc, model, knob, "lolo")
            s.append(f"{lab if model=='logreg' else ''} & {ml} & {knob:.2f} & {100*g[0]:.0f}\\,\\% & {g[1]:.3f} & {g[2]:.3f} & {100*l[0]:.0f}\\,\\% & {l[1]:.3f} & {l[2]:.3f} \\\\")
s += ["\\hline\\end{tabular}\\end{table}"]
w("tab_shift", "\n".join(s))


# ---------------------------------------------------------------- Fig. 1: coverage vs nominal (a) and recalibration vs k (b)
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
os.makedirs("paper/figs", exist_ok=True)
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 7, "axes.labelsize": 7, "legend.fontsize": 6.5, "xtick.labelsize": 6.5, "ytick.labelsize": 6.5,
                     "axes.linewidth": 0.6, "lines.linewidth": 1.1, "lines.markersize": 3.2, "pdf.fonttype": 42})
DSC = {"KAIST": "#1f5fa8", "Paderborn": "#d1742b"}
fig, (axa, axb) = plt.subplots(1, 2, figsize=(3.45, 1.5), gridspec_kw={"wspace": 0.42})
axa.plot([0.55, 1], [0.55, 1], color="0.45", lw=0.8, ls=":", zorder=1)
for ds, cc in (("KAIST", K["conformal_coverage"]), ("Paderborn", P["conformal_coverage"])):
    for prot, mfc in (("grouped", DSC[ds]), ("lolo", "white")):
        for model, mk in (("logreg", "o"), ("rf", "s")):
            d = cc[(cc.protocol == prot) & (cc.score == "lac") & (cc.model == model)].groupby("nominal")["coverage"].mean().reset_index()
            d = d[d.nominal >= 0.58]
            axa.plot(d.nominal, d.coverage, marker=mk, color=DSC[ds], mfc=mfc, mew=0.7, lw=0.9,
                     ls="-" if prot == "grouped" else "--", zorder=3)
axa.axvline(0.8, color="0.75", lw=0.6, zorder=0)
lo80 = min(cov80k["logreg"][0], cov80k["rf"][0], cov80["logreg"], cov80["rf"]); hi80 = max(cov80k["logreg"][0], cov80k["rf"][0], cov80["logreg"], cov80["rf"])
axa.annotate("", xy=(0.8, lo80), xytext=(0.8, hi80), arrowprops=dict(arrowstyle="|-|", lw=0.8, color="0.2", shrinkA=0, shrinkB=0, mutation_scale=3))
axa.text(0.812, lo80 - 0.03, f"{100*lo80:.0f}\u2013{100*hi80:.0f} %", ha="left", va="top", fontsize=6, color="0.2")
axa.set_xlabel("nominal coverage $1-\\alpha$"); axa.set_ylabel("empirical coverage")
axa.set_xlim(0.58, 1.0); axa.set_ylim(0.0, 1.02); axa.set_xticks([0.6, 0.7, 0.8, 0.9, 1.0]); axa.set_title("(a) current tier", fontsize=7, pad=3)
from matplotlib.lines import Line2D
h = [Line2D([], [], color=DSC["KAIST"], lw=1, label="KAIST"), Line2D([], [], color=DSC["Paderborn"], lw=1, label="Paderborn"),
     Line2D([], [], color="0.2", marker="o", lw=0, label="LR"), Line2D([], [], color="0.2", marker="s", lw=0, label="RF"),
     Line2D([], [], color="0.2", marker="o", mfc="0.2", lw=1, label="in distribution"), Line2D([], [], color="0.2", marker="o", mfc="white", lw=1, ls="--", label="op.-point shift")]

# (b) recalibration
ks = [1, 2, 3, 5, 8]
axb.axhline(0, color="0.45", lw=0.8, ls=":", zorder=1); axb.axhspan(-0.05, 0.05, color="0.92", lw=0, zorder=0)
for ds, st in (("KAIST", rk), ("Paderborn", rp)):
    for mix, ls, mk, lab in (("target", "-", "o", "target only"), ("source+target", "--", "x", "pooled with source")):
        m = [st.loc[(k, mix), "mean"] for k in ks]; sd = [st.loc[(k, mix), "std"] for k in ks]
        axb.errorbar(ks, m, yerr=sd, color=DSC[ds], ls=ls, marker=mk, mew=0.9, lw=0.9, capsize=1.5, elinewidth=0.6, zorder=3)
    axb.axhline(st.loc[(0, "source"), "mean"], color=DSC[ds], lw=0.7, ls="-.", zorder=2)
axb.text(8.4, rk.loc[(0, "source"), "mean"] - 0.012, "source only", ha="right", va="top", fontsize=6.2, color=DSC["KAIST"])
axb.text(8.4, rp.loc[(0, "source"), "mean"] - 0.012, "source only", ha="right", va="top", fontsize=6.2, color=DSC["Paderborn"])
axb.set_xlabel("target recordings $k$ in calibration"); axb.set_ylabel("coverage gap")
axb.set_xticks(ks); axb.set_xlim(0.5, 8.6); axb.set_ylim(-0.44, 0.08); axb.set_title("(b) recalibration", fontsize=7, pad=3)
hb = [Line2D([], [], color="0.2", marker="o", mfc="0.2", lw=1, label="(b) target only"), Line2D([], [], color="0.2", marker="x", lw=1, ls="--", label="(b) pooled with source")]
h[2] = Line2D([], [], color="0.2", marker="o", lw=0, label="LR; filled: in distr.")
h[3] = Line2D([], [], color="0.2", marker="s", lw=0, label="RF; open: op.-point shift")
fig.legend(handles=h[:4] + hb, loc="lower center", ncol=3, frameon=False, handlelength=1.8, columnspacing=1.2, labelspacing=0.2, bbox_to_anchor=(0.5, -0.34))
for ax in (axa, axb):
    ax.spines[["top", "right"]].set_visible(False); ax.tick_params(length=2, width=0.5, pad=1.5)
fig.savefig("paper/figs/fig_coverage.pdf", bbox_inches="tight", pad_inches=0.01); plt.close(fig); print("wrote paper/figs/fig_coverage.pdf")

# ---------------------------------------------------------------- headline macros
dt = P["damage_transfer"]; dt = dt[(dt.score == "lac") & np.isclose(dt.alpha, 0.2)]
macros = {
    "covEightyPlr": f"{100*cov80['logreg']:.1f}", "covEightyPrf": f"{100*cov80['rf']:.1f}",
    "gapGroupedK": f"{gk['grouped'][0]:+.3f}", "gapLoloK": f"{gk['lolo'][0]:+.3f}", "gapLoloWorstK": f"{gk['lolo'][1]:+.3f}",
    "gapGroupedP": f"{gp['grouped'][0]:+.3f}", "gapLoloP": f"{gp['lolo'][0]:+.3f}", "gapLoloWorstP": f"{gp['lolo'][1]:+.3f}",
    "gapBearingP": f"{bcl.gap.mean():+.3f}",
    "gateDeltaK": f"{dk.loc[('all','all'),'mean']:+.4f} \\pm {dk.loc[('all','all'),'std']:.4f}",
    "gateDeltaP": f"{dp.loc[('all','all'),'mean']:+.4f} \\pm {dp.loc[('all','all'),'std']:.4f}",
    "gateDeltaKshift": f"{dkl.loc[('all','all'),'mean']:+.4f} \\pm {dkl.loc[('all','all'),'std']:.4f}",
    "gateDeltaPshift": f"{dpl.loc[('all','all'),'mean']:+.4f} \\pm {dpl.loc[('all','all'),'std']:.4f}",
    "recalSrcK": f"{tk.loc[0,'source']:+.3f}", "recalFiveK": f"{tk.loc[5,'target']:+.3f}", "recalThreeTK": f"{tk.loc[3,'target']:+.3f}", "recalThreeSTK": f"{tk.loc[3,'source+target']:+.3f}",
    "recalSrcP": f"{tp.loc[0,'source']:+.3f}", "recalFiveP": f"{tp.loc[5,'target']:+.3f}", "recalThreeTP": f"{tp.loc[3,'target']:+.3f}", "recalThreeSTP": f"{tp.loc[3,'source+target']:+.3f}", "recalEightSTP": f"{tp.loc[8,'source+target']:+.3f}",
    "energyRatio": f"{E.LEM_CKSR_15NP['p_mw']/E.IIS3DWB['p_mw']:.0f}",
    "damageFone": f"{dt.f1_target.min():.2f}--{dt.f1_target.max():.2f}",
}
cc = P["conformal_coverage"]; cs = cc[(cc.protocol == "lolo") & (cc.score == "lac") & np.isclose(cc.alpha, 0.2)]
fm = cs.groupby("model")[["coverage", "singleton_frac", "empty_frac"]].mean()
vt = gp_[(gp_.gate == "conformal_lac") & (gp_.cascade == "vib1_time->vib1_full")]
def gate_at(model, prot, knob):
    d = vt[(vt.model == model) & (vt.protocol == prot) & np.isclose(vt.knob, knob)]
    return d.esc_frac.mean(), d.f1.mean(), d.avg_cost_ops.mean()
cf = gp_[(gp_.gate == "conformal_lac") & (gp_.cascade == "cur2_full->vib1_full") & (gp_.model == "rf")]
cfl = gp_[(gp_.gate == "conformal_lac") & (gp_.cascade == "cur2_full->vib1_full") & (gp_.model == "logreg")]
def cf_at(prot, knob):
    d = cf[(cf.protocol == prot) & np.isclose(cf.knob, knob)]; return d.esc_frac.mean(), d.f1.mean()
def cfl_at(prot, knob):
    d = cfl[(cfl.protocol == prot) & np.isclose(cfl.knob, knob)]; return d.esc_frac.mean(), d.f1.mean()
mems_mj = E.IIS3DWB["p_mw"] * 4096 / 25600; lem2_mj = 2 * (E.LEM_CKSR_15NP["p_mw"] + E.ADS7042["p_mw_at"](25_600)) * 4096 / 25600
e_g = cf_at("grouped", 0.05); e_l = cf_at("lolo", 0.05)
f1_exp_rf = gp_[(gp_.model == "rf") & (gp_.protocol == "grouped")].f1_exp.mean()
macros.update({
    
    
    
    
    "wOneKthree": f"{gkw.loc[1, 0.3]:+.3f}",
    "escCurG": f"{100*e_g[0]:.0f}", "fCurG": f"{e_g[1]:.3f}", "escCurL": f"{100*e_l[0]:.0f}", "fCurL": f"{e_l[1]:.3f}",
    "memsMj": f"{mems_mj:.2f}", "energyCurGFree": f"{e_g[0]*mems_mj:.2f}", "mcuMemsMj": f"{E.mcu_acquisition_mj():.1f}",
    "mcuRatio": f"{E.mcu_acquisition_mj()/mems_mj:.0f}", "memsAvgUwTot": f"{(mems_mj + E.mcu_acquisition_mj())/60*1e3:.0f}",
    "covEightyKlr": f"{100*cov80k['logreg'][0]:.1f}", "covEightyKrf": f"{100*cov80k['rf'][0]:.1f}",
    "computeRatio": f"{mems_mj/(compute_total_uj/1000):.0f}",
    "srcCalP": f"{int(P['recalibration'][(P['recalibration'].mix=='source')&(P['recalibration'].k==0)].n_cal.median()):,}".replace(",", "\\,"),
    "ratioTmcs": f"{(E.TMCS1100['p_mw'])/E.IIS3DWB['p_mw']:.0f}",
    "computeTot": f"{compute_total_uj/1000:.3f}",
    "cycleRatio": f"{(9*4096 + E.FFT_4096_CYCLES_EXTRAPOLATED)/(9*4096):.1f}",
    "deepSleepUw": f"{E.ESP32S3['p_deepsleep_mw']*1e3:.0f}",
    "waitiMj": f"{E.ESP32S3['p_waiti_mw']*wdur:.1f}", 
    "wOneKpool": f"{gkw.loc[1, 1.0]:+.3f}", "wOneKtgt": f"{gkw.loc[1, 0.0]:+.3f}",
    "wFivePthree": f"{gpw.loc[5, 0.3]:+.3f}", "wFivePlow": f"{gpw.loc[5, 0.03]:+.3f}", "wFivePtgt": f"{gpw.loc[5, 0.0]:+.3f}",
    "wFiveKthree": f"{gkw.loc[5, 0.3]:+.3f}", "wFiveKtgt": f"{gkw.loc[5, 0.0]:+.3f}",
})
# ---- round-4 macros: price of recalibration, per-deployment spread, wrong-singleton rate, accuracy vs validity
def esc_after(R, C, model, alpha):
    r = R[(R.variant == "rec") & (R.model == model) & np.isclose(R.alpha, alpha)]
    ind = C[(C.protocol == "grouped") & (C.score == "lac") & (C.model == model) & np.isclose(C.alpha, alpha)]
    return 1 - ind.singleton_frac.mean(), r[(r.k == 5) & (r.mix == "target")].esc_frac.mean(), ind.avg_size.mean(), r[(r.k == 5) & (r.mix == "target")].avg_size.mean()
def esc_mean(R, k, mix):
    r = R[(R.variant == "rec") & (R.k == k) & (R.mix == mix) & R.alpha.isin([0.05, 0.10, 0.20, 0.30])]; return r.esc_frac.mean()
def spread(R, k):
    r = R[(R.variant == "rec") & (R.k == k) & (R.mix == "target") & R.alpha.isin([0.05, 0.10, 0.20, 0.30])]; g = r.coverage - r.nominal
    return g.std(), (g < -0.05).mean()
pr10, pl10 = esc_after(P["recalibration"], P["conformal_coverage"], "rf", 0.10), esc_after(P["recalibration"], P["conformal_coverage"], "logreg", 0.10)
spK, spP = spread(K["recalibration"], 5), spread(P["recalibration"], 5)
def wrong_single(G, casc, prot, model, alpha):
    g = G[(G.gate == "conformal_lac") & (G.cascade == casc) & (G.protocol == prot) & (G.model == model) & np.isclose(G.knob, alpha)]
    return ((1 - g.esc_frac) * (1 - g.sel_acc_no_esc.fillna(1))).mean()
wsK = {m: wrong_single(K["gate"], "cur_full->vib_full", "lolo", m, 0.2) for m in ["logreg", "rf"]}
wsP = {m: wrong_single(P["gate"], "cur2_full->vib1_full", "lolo", m, 0.2) for m in ["logreg", "rf"]}
e_l_seeds = cf[(cf.protocol == "lolo") & np.isclose(cf.knob, 0.05)].groupby("seed").esc_frac.mean()
fB = best(P["pareto"], "cur2_full", "grouped")[0]; fBb = P["bearing_pareto"][(P["bearing_pareto"].block == "cur2_full") & P["bearing_pareto"].model.isin(SHALLOW)].f1_mean.max(); fBs = best(P["pareto"], "cur2_full", "lolo")[0]
vg = gate_at("rf", "grouped", 0.10); vl = gate_at("rf", "lolo", 0.10)
macros.update({
    "escInPrf": f"{100*pr10[0]:.0f}", "escTgtPrf": f"{100*pr10[1]:.0f}", "escInPlr": f"{100*pl10[0]:.0f}", "escTgtPlr": f"{100*pl10[1]:.0f}",
    "sizeInPrf": f"{pr10[2]:.1f}", "sizeTgtPrf": f"{pr10[3]:.1f}",
    "escSrcMeanK": f"{100*esc_mean(K['recalibration'], 0, 'source'):.0f}", "escTgtMeanK": f"{100*esc_mean(K['recalibration'], 5, 'target'):.0f}",
    "escSrcMeanP": f"{100*esc_mean(P['recalibration'], 0, 'source'):.0f}", "escTgtMeanP": f"{100*esc_mean(P['recalibration'], 5, 'target'):.0f}",
    "spreadK": f"{spK[0]:.2f}", "spreadP": f"{spP[0]:.2f}", "belowK": f"{100*spK[1]:.0f}", "belowP": f"{100*spP[1]:.0f}",
    "wrongLrK": f"{wsK['logreg']:.2f}", "wrongLrP": f"{wsP['logreg']:.2f}", "wrongRfK": f"{wsK['rf']:.2f}", "wrongRfP": f"{wsP['rf']:.2f}",
    "escCurLlo": f"{100*e_l_seeds.min():.0f}", "escCurLhi": f"{100*e_l_seeds.max():.0f}",
    "ppWorstK": f"{ppwK:+.3f}", "ppWorstP": f"{ppwP:+.3f}", "mlpDeficit": f"{MLP_DEFICIT:.3f}",
    "fCurGrpP": f"{fB:.2f}", "fCurBearP": f"{fBb:.2f}", "fCurShiftP": f"{fBs:.2f}",
    "escVibG": f"{100*vg[0]:.0f}", "fVibG": f"{vg[1]:.3f}", "escVibL": f"{100*vl[0]:.0f}", "fVibL": f"{vl[1]:.3f}",
    "escVibLrG": f"{100*gate_at('logreg', 'grouped', 0.10)[0]:.0f}", "escVibLrL": f"{100*gate_at('logreg', 'lolo', 0.10)[0]:.0f}",
    "escCurLrG": f"{100*cfl_at('grouped', 0.05)[0]:.0f}", "escCurLrL": f"{100*cfl_at('lolo', 0.05)[0]:.0f}",
    "wrongVibRfPten": f"{wrong_single(P['gate'], 'vib1_time->vib1_full', 'lolo', 'rf', 0.10):.2f}",
    "wrongCurRfPten": f"{wrong_single(P['gate'], 'cur2_full->vib1_full', 'lolo', 'rf', 0.10):.2f}",
    "fullsetK": "{}/{}".format(*fullset_cells(K["conformal_coverage"])),
    "memsTotMj": f"{mems_mj + E.mcu_acquisition_mj():.1f}", "energyCurGFreeTot": f"{e_g[0]*(mems_mj + E.mcu_acquisition_mj()):.1f}",
    "breakEvenS": f"{(mems_mj + E.mcu_acquisition_mj())/E.ESP32S3['p_lightsleep_mw']:.0f}",
})
for dead in ["wOneKthree", "wOneKpool", "wOneKtgt", "memsAvgUwTot", "deepSleepUw"]: macros.pop(dead, None)
open("paper/numbers_ifac.tex", "w").write("\n".join(f"\\newcommand{{\\{k}}}{{{v}}}" for k, v in macros.items()) + "\n")
print("wrote paper/numbers_ifac.tex"); print(macros)
