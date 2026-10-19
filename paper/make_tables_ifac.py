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
def w(name, s):
    width = "0.9\\textwidth" if "table*" in s else "\\columnwidth"
    s = s.replace("\\begin{tabular}", "\\setlength{\\tabcolsep}{3.5pt}\\resizebox{" + width + "}{!}{\\begin{tabular}").replace("\\end{tabular}", "\\end{tabular}}")
    open(f"{OUT}/{name}.tex", "w").write(s); print("wrote", name)

# ---------------------------------------------------------------- frontier (with 95 % cluster-bootstrap CIs)
def best(p, block, prot):
    d = p[(p.block == block) & (p.protocol == prot)]
    if d.empty: return np.nan, "--"
    r = d.loc[d.f1_mean.idxmax()]
    return r.f1_mean, f"[{r.boot_lo:.2f}, {r.boot_hi:.2f}]"
rows = []
for b, lab in [("cur_full", "current, time+FFT"), ("vib1_time", "1 accel., time"), ("vib1_full", "1 accel., time+FFT"),
               ("vib_full", "4 accel., time+FFT"), ("vib_cur", "4 accel. + current")]:
    g, gci = best(K["pareto"], b, "grouped"); l, lci = best(K["pareto"], b, "lolo")
    rows.append(("KAIST", lab, int(K["pareto"][K["pareto"].block == b].cost_ops.iloc[0]), g, gci, np.nan, "--", l, lci))
for b, lab in [("cur2_full", "2 current phases, time+FFT"), ("vib1_time", "1 accel., time"), ("vib1_full", "1 accel., time+FFT"), ("vib_cur", "1 accel. + 2 phases")]:
    g, gci = best(P["pareto"], b, "grouped"); l, lci = best(P["pareto"], b, "lolo")
    bp = P["bearing_pareto"][P["bearing_pareto"].block == b]; br = bp.loc[bp.f1_mean.idxmax()]
    rows.append(("Paderborn", lab, int(P["pareto"][P["pareto"].block == b].cost_ops.iloc[0]), g, gci, br.f1_mean, f"[{br.boot_lo:.2f}, {br.boot_hi:.2f}]", l, lci))
s_ = ["\\begin{table*}[tb]\\centering\\footnotesize",
     "\\caption{Cost--accuracy frontier: macro-F1 of the best classifier per tier (mean over three seeds for the grouped protocols; one run per held-out point under shift) with 95\\,\\% percentile intervals of a cluster bootstrap over recordings (bearings for the bearing-grouped column) of the seed-0 predictions; the interval can sit off the point where a class has few recordings (three per class on KAIST). Operations per 160\\,ms window.}",
     "\\label{tab:frontier}",
     "\\begin{tabular}{llrlll}\\hline",
     " & tier & ops / window & recording-grouped [95\\,\\% CI] & bearing-grouped [95\\,\\% CI] & operating-point shift [95\\,\\% CI] \\\\ \\hline"]
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
    v = cov80_by_model(cc, prot); return f"{100*v['logreg'][0]:.1f} / {100*v['rf'][0]:.1f}"
def hf(h, f): return "--" if h != h else f"{100*h:.0f} / {100*f:.0f}"
bh, bf = classcov(bcl20)
s = ["\\begin{table}[tb]\\centering\\footnotesize",
     "\\caption{Coverage gap (empirical $-$ nominal) of LAC conformal sets for the cheap tier of the current-first cascade (current, time+FFT on KAIST; two current phases, time+FFT on Paderborn): mean and worst case over the $\\alpha$ grid, classifiers and seeds; coverage delivered at nominal 80\\,\\% by LR / RF (mean over seeds); and the same coverage, averaged over classifiers, for the healthy class and for the fault classes. Protocols: in = recording-grouped, bearing = bearing-grouped, shift = operating-point shift.}",
     "\\label{tab:gap}",
     "\\begin{tabular}{llcccc}\\hline",
     "dataset & protocol & mean gap & worst gap & cov.\\ at 80\\,\\% LR / RF & healthy / faulty \\\\ \\hline",
     f"KAIST & in & ${gk['grouped'][0]:+.3f}$ & ${gk['grouped'][1]:+.3f}$ & {lrrf(K['conformal_coverage'], 'grouped')}\\,\\% & {hf(gk['grouped'][4], gk['grouped'][5])} \\\\",
     f"KAIST & shift & ${gk['lolo'][0]:+.3f}$ & ${gk['lolo'][1]:+.3f}$ & {lrrf(K['conformal_coverage'], 'lolo')}\\,\\% & {hf(gk['lolo'][4], gk['lolo'][5])} \\\\",
     f"Paderborn & in & ${gp['grouped'][0]:+.3f}$ & ${gp['grouped'][1]:+.3f}$ & {lrrf(P['conformal_coverage'], 'grouped')}\\,\\% & {hf(gp['grouped'][4], gp['grouped'][5])} \\\\",
     f"Paderborn & bearing & ${bcl.gap.mean():+.3f}$ & ${bcl.gap.min():+.3f}$ & {100*bcl20[bcl20.model=='logreg'].coverage.mean():.1f} / {100*bcl20[bcl20.model=='rf'].coverage.mean():.1f}\\,\\% & {hf(bh, bf)} \\\\",
     f"Paderborn & shift & ${gp['lolo'][0]:+.3f}$ & ${gp['lolo'][1]:+.3f}$ & {lrrf(P['conformal_coverage'], 'lolo')}\\,\\% & {hf(gp['lolo'][4], gp['lolo'][5])} \\\\",
     "\\hline\\end{tabular}\\end{table}"]
w("tab_gap", "\n".join(s))

# ---------------------------------------------------------------- gate delta
dk = R.tab_gate_delta(K["gate"]); dp = R.tab_gate_delta(P["gate"])
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
w("tab_gate", "\n".join(s))

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
w("tab_weighted", "\n".join(s))

# ---------------------------------------------------------------- factor x modality + failure modes (X2, alpha = 0.20, LAC)
fc = P["factor_coverage"]; fc = fc[(fc.score == "lac") & np.isclose(fc.alpha, 0.2)]
piv = fc.pivot_table(index=["block", "model"], columns="factor", values="coverage")
pivf = fc.pivot_table(index=["block", "model"], columns="factor", values="f1")
ind = fc[fc.factor == "none (in-domain)"].groupby(["block", "model"])[["coverage", "singleton_frac", "empty_frac", "f1"]].mean()
sh = fc[fc.factor != "none (in-domain)"].groupby(["block", "model"])[["coverage", "singleton_frac", "empty_frac", "f1"]].mean()
tiers = {"cur2_full": "2 current phases, time+FFT", "vib1_time": "1 accel., time", "vib1_full": "1 accel., time+FFT"}
s = ["\\begin{table*}[tb]\\centering\\footnotesize",
     "\\caption{Paderborn, LAC at nominal 80\\,\\%, classifiers fitted and calibrated at the baseline operating point: coverage (macro-F1 in parentheses) on held-out baseline recordings (in) and on each operating point that changes one factor; coverage, singleton and empty-set fractions with the three shifted points pooled. A wrong singleton is silent under-escalation; an empty set escalates by (\\ref{eq:gate}).}",
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
rows = [("MEMS accel.\\ IIS3DWB, 3 axes, ADC on chip", E.IIS3DWB["p_mw"], None),
        ("Current transducer LEM CKSR 15-NP + ADC, per phase", E.LEM_CKSR_15NP["p_mw"] + E.ADS7042["p_mw_at"](25_600), None),
        ("Hall current sensor TMCS1100 + ADC, per phase", E.TMCS1100["p_mw"] + E.ADS7042["p_mw_at"](25_600), None),
        ("IEPE accel.\\ on TI TIDA-010249 front end", E.TIDA_010249["p_mw"], None),
        ("ESP32-S3, MEMS window: light sleep + 8 FIFO drains", None, E.mcu_acquisition_mj()),
        ("ESP32-S3, current window (no FIFO): idle, 240\\,MHz", E.ESP32S3["p_waiti_mw"], None)]
compute_uj = (9 * 4096 + E.FFT_4096_CYCLES_EXTRAPOLATED) * E.PJ_PER_CORE_CYCLE["single_simd128"] * 1e-6
compute_total_uj = (9 * 4096 + E.FFT_4096_CYCLES_EXTRAPOLATED) * (E.PJ_PER_CORE_CYCLE["single_simd128"] + E.ESP32S3["p_waiti_mw"] / 240.0 * 1e3) * 1e-6
s = ["\\begin{table}[tb]\\centering\\footnotesize",
     "\\caption{Datasheet power of the sensing chains and of the MCU, and energy per 160\\,ms window. The MEMS FIFO holds an eighth of a window, so the MCU drains it eight times over SPI (about 20\\,ms at the idle floor); the current ADC has no FIFO. Last row: ESP32-S3 computation for one window of the accelerometer time+FFT tier (" + f"{9*4096 + E.FFT_4096_CYCLES_EXTRAPOLATED:,}".replace(",", "\\,") + " cycles, FFT count extrapolated from the ESP-DSP benchmarks), marginal at " + f"{E.PJ_PER_CORE_CYCLE['single_simd128']:.0f}" + "\\,pJ per cycle and on a total-power basis.}",
     "\\label{tab:energy}",
     "\\begin{tabular}{lrr}\\hline",
     "component & mW & mJ / window \\\\ \\hline"]
for lab, p, mj in rows:
    s.append(f"{lab} & {p:.2f} & {p*wdur:.2f} \\\\" if mj is None else f"{lab} & -- & {mj:.2f} \\\\")
s.append(f"ESP32-S3 computation, accel.\\ time+FFT tier (marginal / total) & -- & {compute_uj/1000:.3f} / {compute_total_uj/1000:.3f} \\\\")
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


# ---------------------------------------------------------------- single-panel coverage figure for the paper
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
os.makedirs("paper/figs", exist_ok=True)
cc_ = P["conformal_coverage"]
fig, ax = plt.subplots(figsize=(3.4, 2.5))
ax.plot([0.5, 1], [0.5, 1], color=R.GRAY, lw=1, ls=":", label="nominal")
for prot, lab in (("grouped", "recording-grouped"), ("lolo", "operating-point shift")):
    for score, ls in (("lac", "-"), ("aps", "--")):
        d = cc_[(cc_.protocol == prot) & (cc_.score == score)].groupby("nominal")["coverage"].agg(["mean", "min", "max"]).reset_index()
        ax.plot(d.nominal, d["mean"], ls=ls, marker="o", ms=3, lw=1.4, color=R.PROTOCOL_COLOR[prot], label=f"{lab}, {score.upper()}")
        ax.fill_between(d.nominal, d["min"], d["max"], color=R.PROTOCOL_COLOR[prot], alpha=0.12, lw=0)
ax.set_xlabel("nominal coverage $1-\\alpha$"); ax.set_ylabel("empirical coverage")
ax.set_xlim(0.58, 1.0); ax.set_ylim(0.0, 1.02); ax.legend(fontsize=6.5, loc="upper left")
fig.tight_layout(); fig.savefig("paper/figs/pb_coverage_a.pdf"); plt.close(fig); print("wrote paper/figs/pb_coverage_a.pdf")

# ---------------------------------------------------------------- headline macros
dt = P["damage_transfer"]; dt = dt[(dt.score == "lac") & np.isclose(dt.alpha, 0.2)]
macros = {
    "covEightyPlr": f"{100*cov80['logreg']:.1f}", "covEightyPrf": f"{100*cov80['rf']:.1f}",
    "gapGroupedK": f"{gk['grouped'][0]:+.3f}", "gapLoloK": f"{gk['lolo'][0]:+.3f}", "gapLoloWorstK": f"{gk['lolo'][1]:+.3f}",
    "gapGroupedP": f"{gp['grouped'][0]:+.3f}", "gapLoloP": f"{gp['lolo'][0]:+.3f}", "gapLoloWorstP": f"{gp['lolo'][1]:+.3f}",
    "gapBearingP": f"{bcl.gap.mean():+.3f}",
    "gateDeltaK": f"{dk.loc[('all','all'),'mean']:+.4f} \\pm {dk.loc[('all','all'),'std']:.4f}",
    "gateDeltaP": f"{dp.loc[('all','all'),'mean']:+.4f} \\pm {dp.loc[('all','all'),'std']:.4f}",
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
def cf_at(prot, knob):
    d = cf[(cf.protocol == prot) & np.isclose(cf.knob, knob)]; return d.esc_frac.mean(), d.f1.mean()
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
open("paper/numbers_ifac.tex", "w").write("\n".join(f"\\newcommand{{\\{k}}}{{{v}}}" for k, v in macros.items()) + "\n")
print("wrote paper/numbers_ifac.tex"); print(macros)
