"""Plotting and tabulation helpers shared by the analysis notebooks.

All functions take the CSV outputs written by ``run_experiments.py`` /
``run_paderborn.py`` / ``run_paderborn_extra.py`` and return matplotlib figures
or pandas tables.  Nothing here recomputes a result; the CSVs are the source of
truth.  Figures are saved to ``figs_en/<name>.{png,pdf}`` when ``save`` is given.
"""
import os
import numpy as np, pandas as pd
import matplotlib
import matplotlib.pyplot as plt

plt.rcParams.update({
    "font.size": 9, "axes.grid": True, "grid.alpha": 0.25, "grid.linewidth": 0.6,
    "axes.spines.top": False, "axes.spines.right": False,
    "figure.dpi": 120, "savefig.dpi": 200, "savefig.bbox": "tight",
    "legend.frameon": False, "legend.fontsize": 8, "axes.titlesize": 9.5,
})

# Categorical colours (validated palette, slots 1-3) plus neutrals.
BLUE, ORANGE, AQUA, GRAY, INK = "#2a78d6", "#eb6834", "#1baf7a", "#8a8a85", "#0b0b0b"
PROTOCOL_COLOR = {"grouped": BLUE, "bearing": AQUA, "lolo": ORANGE}
PROTOCOL_LABEL = {"grouped": "recording-grouped CV", "bearing": "bearing-grouped CV",
                  "lolo": "leave-one-operating-point-out"}
MODEL_LABEL = {"logreg": "logistic regression", "rf": "random forest", "mlp": "MLP"}
MARKER = {"logreg": "o", "rf": "s", "mlp": "^"}
SCORE_LABEL = {"lac": "LAC", "aps": "APS"}

# Sensing-configuration labels (English) and the sensing family used for colour.
KAIST_BLOCKS = {
    "tmp":          ("temperature only",                 "other"),
    "cur_time":     ("current, time-domain",             "current"),
    "cur_full":     ("current, time+FFT",                "current"),
    "cur_full_tmp": ("current, time+FFT, + temperature", "current"),
    "vib1_time":    ("1 accelerometer, time-domain",     "vibration"),
    "vib1_full":    ("1 accelerometer, time+FFT",        "vibration"),
    "vib_time":     ("4 accelerometers, time-domain",    "vibration"),
    "vib_full":     ("4 accelerometers, time+FFT",       "vibration"),
    "vib_cur":      ("4 accelerometers + current",       "fusion"),
}
KAIST_SHORT = {"tmp": "T", "cur_time": "I", "cur_full": "I+F", "cur_full_tmp": "I+F+T",
               "vib1_time": "1A", "vib1_full": "1A+F", "vib_time": "4A", "vib_full": "4A+F",
               "vib_cur": "4A+F+I"}
PB_BLOCKS = {
    "tmp":       ("temperature only",                      "other"),
    "cur1_time": ("1 current phase, time-domain",          "current"),
    "cur1_full": ("1 current phase, time+FFT",             "current"),
    "cur2_time": ("2 current phases, time-domain",         "current"),
    "cur2_full": ("2 current phases, time+FFT",            "current"),
    "vib1_time": ("1 accelerometer, time-domain",          "vibration"),
    "vib1_full": ("1 accelerometer, time+FFT",             "vibration"),
    "vib_cur":   ("1 accelerometer + 2 current phases",    "fusion"),
}
PB_SHORT = {"tmp": "T", "cur1_time": "I1", "cur1_full": "I1+F", "cur2_time": "I2", "cur2_full": "I2+F",
            "vib1_time": "1A", "vib1_full": "1A+F", "vib_cur": "1A+F+I2"}
FAMILY_COLOR = {"vibration": BLUE, "current": ORANGE, "fusion": AQUA, "other": GRAY}
FACTOR_LABEL = {"none (in-domain)": "none (in-domain)", "speed_rpm": "speed 1500→900 rpm",
                "torque_nm": "torque 0.7→0.1 N·m", "force_n": "radial force 1000→400 N"}
FACTOR_ORDER = ["none (in-domain)", "speed_rpm", "torque_nm", "force_n"]


def save(fig, name, outdir="figs_en"):
    os.makedirs(outdir, exist_ok=True)
    fig.savefig(f"{outdir}/{name}.png"); fig.savefig(f"{outdir}/{name}.pdf")
    return fig


# --------------------------------------------------------------------------- tables
def tab_pareto(p, blocks, protocols=("grouped", "lolo")):
    """Best classifier per configuration and protocol, with cost."""
    rows = []
    for b, (lab, fam) in blocks.items():
        d = p[p.block == b]
        if d.empty:
            continue
        r = dict(configuration=lab, ops_per_window=int(d.cost_ops.iloc[0]))
        for prot in protocols:
            dd = d[d.protocol == prot]
            if dd.empty:
                continue
            best = dd.loc[dd.f1_mean.idxmax()]
            r[f"{prot}_F1"] = round(best.f1_mean, 3)
            r[f"{prot}_CI95"] = f"[{best.boot_lo:.3f}, {best.boot_hi:.3f}]"
            r[f"{prot}_model"] = best.model
        rows.append(r)
    return pd.DataFrame(rows).set_index("configuration")


def tab_coverage_gap(cc):
    cc = cc.copy(); cc["gap"] = cc.coverage - cc.nominal
    t = cc.groupby(["protocol", "score"])["gap"].agg(mean="mean", worst="min").round(3)
    at80 = cc[np.isclose(cc.alpha, 0.20)].groupby(["protocol", "score"])["coverage"].mean().round(3)
    t["coverage_at_nominal_80"] = at80
    return t


def tab_gate_delta(g, protocol="grouped", lo=0.02, hi=0.98):
    """Macro-F1 difference conformal − softmax at matched escalation fraction,
    obtained by linear interpolation of the softmax curve."""
    rows = []
    for (casc, model, seed), d in g[g.protocol == protocol].groupby(["cascade", "model", "seed"]):
        s = d[d.gate == "softmax"].sort_values("esc_frac")
        if len(s) < 2:
            continue
        for gate in ("conformal_lac", "conformal_aps"):
            c = d[(d.gate == gate) & (d.esc_frac > lo) & (d.esc_frac < hi)]
            for _, r in c.iterrows():
                f_soft = np.interp(r.esc_frac, s.esc_frac.values, s.f1.values)
                rows.append(dict(cascade=casc, model=model, seed=seed, gate=SCORE_LABEL[gate[-3:]],
                                 esc_frac=r.esc_frac, delta_f1=r.f1 - f_soft))
    d = pd.DataFrame(rows)
    out = d.groupby(["cascade", "gate"])["delta_f1"].agg(["mean", "std", "count"]).round(4)
    out.loc[("all", "all"), :] = [round(float(d.delta_f1.mean()), 4), round(float(d.delta_f1.std()), 4), len(d)]
    return out


def tab_recal(r, model=None, alpha=None, variant="rec"):
    """Gap by k and calibration mix.  model=None / alpha=None average over all
    classifiers / all risk levels (the aggregation used for the headline numbers)."""
    d = r[r.variant == variant].copy()
    if model is not None:
        d = d[d.model == model]
    if alpha is not None:
        d = d[np.isclose(d.alpha, alpha)]
    d["gap"] = d.coverage - d.nominal
    t = d.groupby(["k", "mix"])["gap"].mean().unstack().round(3)
    return t[[c for c in ["source", "source+target", "target"] if c in t]]


# --------------------------------------------------------------------------- figures
def fig_pareto(p, blocks, short, protocols=("grouped", "lolo"), titles=None, name=None):
    titles = titles or [PROTOCOL_LABEL[x] for x in protocols]
    fig, axes = plt.subplots(1, len(protocols), figsize=(4.6 * len(protocols), 3.6), sharey=True)
    axes = np.atleast_1d(axes)
    jit = {"logreg": 0.85, "rf": 1.0, "mlp": 1.18}
    p = p[p.block != "tmp"]   # temperature is a confounder, not a candidate configuration (see tables)
    for ax, prot, title in zip(axes, protocols, titles):
        d = p[p.protocol == prot]
        for _, r in d.iterrows():
            fam = blocks[r.block][1]
            ax.errorbar(r.cost_ops * jit.get(r.model, 1), r.f1_mean,
                        yerr=[[max(0, r.f1_mean - r.boot_lo)], [max(0, r.boot_hi - r.f1_mean)]],
                        fmt=MARKER[r.model], ms=5, lw=0.8, capsize=1.5, color=FAMILY_COLOR[fam],
                        mec="white", mew=0.4, alpha=0.95)
        best = d.groupby("block").agg(cost=("cost_ops", "first"), f1=("f1_mean", "max"))
        best = best.sort_values(["cost", "f1"], ascending=[True, False]).drop_duplicates("cost")
        front, top = [], -1
        for b, r in best.iterrows():
            if r.f1 > top:
                front.append((b, r.cost, r.f1)); top = r.f1
        ax.plot([f[1] for f in front], [f[2] for f in front], "-", color=GRAY, lw=1.0, zorder=0)
        for i, (b, x, yv) in enumerate(front):
            ax.annotate(short[b], (x, yv), fontsize=7.5, fontweight="bold", ha="center",
                        xytext=(0, 11 if i % 2 == 0 else -15), textcoords="offset points", color=INK)
        ax.set_xscale("log"); ax.set_title(title); ax.set_xlabel("operations per window")
    axes[0].set_ylabel("macro-F1 (95% cluster-bootstrap CI)")
    from matplotlib.lines import Line2D
    h = [Line2D([], [], color=FAMILY_COLOR[f], marker="o", ls="", label=f) for f in ("vibration", "current", "fusion")]
    h += [Line2D([], [], color=INK, marker=MARKER[m], ls="", mfc="none", label=MODEL_LABEL[m]) for m in ("logreg", "rf", "mlp")]
    fig.legend(handles=h, loc="lower center", ncol=7, bbox_to_anchor=(0.5, -0.04))
    fig.tight_layout()
    return save(fig, name) if name else fig


def fig_learning_curve(lc, blocks, name=None):
    fig, ax = plt.subplots(figsize=(5.6, 3.4))
    ls = {"logreg": "--", "rf": "-"}
    for (b, m), d in lc.groupby(["block", "model"]):
        d = d.sort_values("n_windows")
        ax.errorbar(d.n_windows, d.f1_mean, yerr=d.f1_std, ls=ls.get(m, "-"), marker=MARKER[m], ms=4,
                    lw=1.4, capsize=2, color=FAMILY_COLOR[blocks[b][1]],
                    label=f"{blocks[b][0]} · {MODEL_LABEL[m]}")
    ax.set_xlabel("windows per recording used"); ax.set_ylabel("macro-F1 (recording-grouped CV)")
    ax.set_ylim(0, 1); ax.legend(fontsize=7, ncol=2, loc="upper center", bbox_to_anchor=(0.5, -0.22))
    fig.tight_layout()
    return save(fig, name) if name else fig


def fig_coverage(cc, per_group_label, name=None, protocols=("grouped", "lolo")):
    """(a) empirical vs nominal coverage per protocol and score; (b) coverage per held-out
    group at nominal 80 % (LAC) under the shift protocol."""
    fig, axes = plt.subplots(1, 2, figsize=(9.2, 3.5))
    ax = axes[0]
    ax.plot([0.5, 1], [0.5, 1], color=GRAY, lw=1, ls=":", label="nominal")
    for prot in protocols:
        for score, ls in (("lac", "-"), ("aps", "--")):
            d = cc[(cc.protocol == prot) & (cc.score == score)].groupby("nominal")["coverage"].agg(["mean", "min", "max"]).reset_index()
            ax.plot(d.nominal, d["mean"], ls=ls, marker="o", ms=3.5, lw=1.6, color=PROTOCOL_COLOR[prot],
                    label=f"{PROTOCOL_LABEL[prot]} · {SCORE_LABEL[score]}")
            ax.fill_between(d.nominal, d["min"], d["max"], color=PROTOCOL_COLOR[prot], alpha=0.12, lw=0)
    ax.set_xlabel("nominal coverage 1−α"); ax.set_ylabel("empirical coverage")
    ax.set_title("(a) coverage vs nominal (band: min–max over classifiers and seeds)")
    ax.legend(fontsize=7, loc="upper left")
    ax = axes[1]
    cols = [c for c in cc.columns if c.startswith("cov_")]
    d = cc[(cc.protocol == protocols[-1]) & (cc.score == "lac") & np.isclose(cc.alpha, 0.20)]
    t = d.groupby("model")[cols].mean()
    x = np.arange(len(cols)); w = 0.8 / max(len(t), 1)
    for i, (m, row) in enumerate(t.iterrows()):
        ax.bar(x + i * w - 0.4 + w / 2, row.values, width=w * 0.92, color=PROTOCOL_COLOR[protocols[-1]],
               alpha=0.55 + 0.45 * i / max(len(t) - 1, 1), label=MODEL_LABEL[m], edgecolor="white")
    ax.axhline(0.8, color=GRAY, ls=":", lw=1, label="nominal 80 %")
    import textwrap
    ax.set_xticks(x); ax.set_xticklabels(["\n".join(textwrap.wrap(per_group_label(c).replace("\n", " "), 16)) for c in cols], fontsize=7.5)
    ax.set_ylim(0, 1); ax.set_ylabel("empirical coverage (LAC, α = 0.20)")
    ax.set_title(f"(b) per held-out operating point, {PROTOCOL_LABEL[protocols[-1]]}")
    ax.legend(fontsize=7, loc="upper left")
    fig.tight_layout()
    return save(fig, name) if name else fig


def fig_gate(g, cascade_labels, model="rf", name=None):
    """Macro-F1 vs escalation fraction: conformal gates vs softmax threshold, grouped and shift."""
    cascades = list(cascade_labels)
    fig, axes = plt.subplots(1, len(cascades), figsize=(4.6 * len(cascades), 3.4), sharey=True)
    axes = np.atleast_1d(axes)
    for ax, casc in zip(axes, cascades):
        for prot in ("grouped", "lolo"):
            d = g[(g.cascade == casc) & (g.model == model) & (g.protocol == prot)]
            if d.empty:
                continue
            s = d[d.gate == "softmax"].groupby("knob")[["esc_frac", "f1"]].mean().sort_values("esc_frac")
            ax.plot(s.esc_frac, s.f1, "-", color=PROTOCOL_COLOR[prot], lw=1.4, alpha=0.8,
                    label=f"softmax threshold τ · {PROTOCOL_LABEL[prot]}")
            for gate, mk in (("conformal_lac", "o"), ("conformal_aps", "^")):
                c = d[d.gate == gate].groupby("knob")[["esc_frac", "f1"]].mean()
                ax.plot(c.esc_frac, c.f1, mk, ms=5, color=PROTOCOL_COLOR[prot], mec="white", mew=0.5,
                        label=f"conformal {SCORE_LABEL[gate[-3:]]} (α sweep) · {PROTOCOL_LABEL[prot]}")
        ax.set_title(cascade_labels[casc]); ax.set_xlabel("fraction of windows escalated")
    axes[0].set_ylabel(f"macro-F1 ({MODEL_LABEL[model]})")
    axes[-1].legend(fontsize=6.5, loc="lower right")
    fig.tight_layout()
    return save(fig, name) if name else fig


def fig_recal(r, model=None, alpha=None, group_label=lambda s: s, name=None):
    """(a) gap vs k for the three calibration mixes; (b) target-only gap per held-out operating
    point.  model=None / alpha=None average over classifiers / risk levels."""
    d = r[r.variant == "rec"].copy()
    if model is not None:
        d = d[d.model == model]
    if alpha is not None:
        d = d[np.isclose(d.alpha, alpha)]
    d["gap"] = d.coverage - d.nominal
    fig, axes = plt.subplots(1, 2, figsize=(9.2, 3.4), sharey=True)
    ax = axes[0]
    style = {"source": (GRAY, ":", "source calibration only"),
             "source+target": (ORANGE, "--", "source + k target recordings (pooled)"),
             "target": (BLUE, "-", "k target recordings only")}
    for mix, (col, ls, lab) in style.items():
        per_seed = d[d.mix == mix].groupby(["k", "seed"])["gap"].mean().reset_index()
        t = per_seed.groupby("k")["gap"].agg(["mean", "std"]).reset_index()
        ax.plot(t.k, t["mean"], ls=ls, marker="o", ms=4, lw=1.6, color=col, label=lab)
        ax.fill_between(t.k, t["mean"] - t["std"], t["mean"] + t["std"], color=col, alpha=0.15, lw=0)
    ax.axhline(0, color=INK, lw=0.8); ax.set_xlabel("k = recordings from the target operating point in calibration")
    agg = f"α = {alpha:.2f}" if alpha is not None else "mean over α ∈ {0.05, 0.10, 0.20, 0.30}"
    agg += "" if model is not None else " and classifiers"
    ax.set_ylabel("coverage − nominal (LAC)"); ax.set_title(f"(a) calibration-set composition; {agg}\n(band: ±1 s.d. over seeds)", fontsize=8.5); ax.legend(fontsize=7)
    ax = axes[1]
    t = d[d.mix == "target"].groupby(["load", "k"])["gap"].mean().unstack(0)
    mks = ["o", "s", "^", "D"]
    for i, c in enumerate(t.columns):
        ax.plot(t.index, t[c], ls="-", marker=mks[i % 4], ms=4, lw=1.3, color=BLUE, mec="white", mew=0.4,
                alpha=0.4 + 0.6 * i / max(len(t.columns) - 1, 1), label=group_label(c))
    ax.axhline(0, color=INK, lw=0.8); ax.set_xlabel("k (target recordings only)"); ax.set_title("(b) per target operating point"); ax.legend(fontsize=7)
    fig.tight_layout()
    return save(fig, name) if name else fig


def fig_factor_modality(fc, blocks, alpha=0.20, score="lac", name=None):
    """Coverage by shifted factor (columns) and sensing tier (rows), one panel per classifier."""
    d = fc[(fc.score == score) & np.isclose(fc.alpha, alpha)]
    models = [m for m in ("logreg", "rf") if m in d.model.unique()]
    fig, axes = plt.subplots(1, len(models), figsize=(4.8 * len(models), 2.9), sharey=True)
    axes = np.atleast_1d(axes)
    cmap = matplotlib.colors.LinearSegmentedColormap.from_list("blues", ["#f4f7fb", BLUE])
    for ax, m in zip(axes, models):
        t = d[d.model == m].pivot_table(index="block", columns="factor", values="coverage")
        t = t.reindex(index=[b for b in blocks if b in t.index], columns=[f for f in FACTOR_ORDER if f in t.columns])
        im = ax.imshow(t.values, cmap=cmap, vmin=0, vmax=1, aspect="auto")
        for i in range(t.shape[0]):
            for j in range(t.shape[1]):
                v = t.values[i, j]
                ax.text(j, i, f"{v:.2f}", ha="center", va="center", fontsize=8.5, color="white" if v > 0.6 else INK)
        ax.set_xticks(range(t.shape[1])); ax.set_xticklabels([FACTOR_LABEL[c] for c in t.columns], rotation=20, ha="right", fontsize=7.5)
        ax.set_yticks(range(t.shape[0])); ax.set_yticklabels([blocks[b][0] for b in t.index], fontsize=8)
        ax.set_title(MODEL_LABEL[m])
        ax.grid(False)
    fig.suptitle(f"Empirical coverage at nominal {1-alpha:.0%} ({SCORE_LABEL[score]}), calibrated at the baseline operating point", y=1.02, fontsize=9.5)
    fig.colorbar(im, ax=axes, fraction=0.025, pad=0.02, label="coverage")
    return save(fig, name) if name else fig


def fig_damage_transfer(dt, blocks, alpha=0.20, score="lac", model="rf", name=None):
    """Coverage gap vs k, one panel per (direction, sensing tier), three calibration mixes each."""
    d = dt[(dt.score == score) & np.isclose(dt.alpha, alpha) & (dt.model == model)].copy()
    d["gap"] = d.coverage - d.nominal
    dirs = [("artificial", "real"), ("real", "artificial")]
    tiers = list(blocks)
    fig, axes = plt.subplots(len(dirs), len(tiers), figsize=(3.2 * len(tiers), 2.6 * len(dirs)), sharex=True, sharey=True)
    style = {"source": (GRAY, ":", "source calibration only"), "source+target": (ORANGE, "--", "source + k target (pooled)"),
             "target": (BLUE, "-", "k target recordings only")}
    for i, (tr, te) in enumerate(dirs):
        for j, b in enumerate(tiers):
            ax = axes[i, j]
            dd = d[(d.train == tr) & (d.test == te) & (d.block == b)]
            for mix, (col, ls, lab) in style.items():
                t = dd[dd.mix == mix].groupby("k")["gap"].mean()
                if mix == "source":
                    t = pd.Series(t.values, index=t.index)
                ax.plot(t.index, t.values, ls=ls, marker="o", ms=3.5, lw=1.3, color=col, label=lab)
            ax.axhline(0, color=INK, lw=0.8)
            if i == 0:
                ax.set_title(blocks[b][0], fontsize=8.5)
            if j == 0:
                ax.set_ylabel(f"train {tr} → test {te}\ncoverage − nominal", fontsize=8)
            if i == len(dirs) - 1:
                ax.set_xlabel("k = target recordings in calibration")
    axes[0, 0].legend(fontsize=6.5, loc="lower right")
    fig.suptitle(f"{SCORE_LABEL[score]}, α = {alpha:.2f}, {MODEL_LABEL[model]}", fontsize=9, y=1.0)
    fig.tight_layout()
    return save(fig, name) if name else fig


def fig_protocol_compare(p_rec, p_bear, blocks, short, name=None):
    """Recording-grouped vs bearing-grouped macro-F1 per configuration (best classifier)."""
    a = p_rec[p_rec.protocol == "grouped"].groupby("block").f1_mean.max()
    b = p_bear.groupby("block").f1_mean.max()
    l = p_rec[p_rec.protocol == "lolo"].groupby("block").f1_mean.max()
    order = [k for k in blocks if k in a.index]
    x = np.arange(len(order)); w = 0.27
    fig, ax = plt.subplots(figsize=(7.6, 3.2))
    for i, (ser, lab, col) in enumerate([(a, PROTOCOL_LABEL["grouped"], BLUE), (b, PROTOCOL_LABEL["bearing"], AQUA), (l, PROTOCOL_LABEL["lolo"], ORANGE)]):
        ax.bar(x + (i - 1) * w, [ser.get(k, np.nan) for k in order], width=w * 0.9, color=col, label=lab, edgecolor="white")
    ax.set_xticks(x); ax.set_xticklabels([short[k] for k in order]); ax.set_ylim(0, 1)
    ax.set_ylabel("macro-F1 (best classifier)"); ax.legend(fontsize=7, loc="lower right")
    fig.tight_layout()
    return save(fig, name) if name else fig


def energy_table(E):
    """Datasheet-derived power of the sensing chains and energy per 160 ms window."""
    w = 4096 / 25600.0
    rows = [
        ("MEMS accelerometer IIS3DWB (3 axes, integrated ADC)", E.IIS3DWB["p_mw"], E.IIS3DWB["cond"]),
        ("Current transducer LEM CKSR 15-NP, per phase (I_C + I_P/N_S at 5 V)", E.LEM_CKSR_15NP["p_mw"], E.LEM_CKSR_15NP["cond"]),
        ("ADC for current channel, ADS7042 at 25.6 kSPS", E.ADS7042["p_mw_at"](25_600), E.ADS7042["cond"]),
        ("Hall current sensor TMCS1100 (low-cost alternative)", E.TMCS1100["p_mw"], E.TMCS1100["cond"]),
        ("IEPE accelerometer PCB 352C33 (sensor only, 4 mA / 24 V)", E.PCB_352C33["p_mw"], E.PCB_352C33["cond"]),
        ("IEPE front-end TI TIDA-010249, per channel", E.TIDA_010249["p_mw"], E.TIDA_010249["cond"]),
        ("ESP32-S3 active, dual core 240 MHz (Modem-sleep, Typ2)", E.ESP32S3["p_active_mw_typ2"], E.ESP32S3["cond"]),
        ("ESP32-S3 idle (WAITI) at 240 MHz: current tier during acquisition (no FIFO)", E.ESP32S3["p_waiti_mw"], E.ESP32S3["cond"]),
    ]
    t = pd.DataFrame(rows, columns=["component", "power_mW", "datasheet condition"])
    t["energy_per_window_mJ"] = (t.power_mW * w).round(3)
    t["power_mW"] = t.power_mW.round(2)
    if hasattr(E, "mcu_acquisition_mj"):
        t.loc[len(t)] = ["ESP32-S3 during a MEMS window: light sleep + 8 FIFO drains over SPI at 10 MHz", np.nan,
                         "light-sleep and WAITI rows of Table 5-9; FIFO 3 kB vs 24 576-byte window", round(E.mcu_acquisition_mj(), 3)]
    return t.set_index("component")


def tab_weighted(w):
    w = w.copy(); w["gap"] = w.coverage - w.nominal
    g = w.groupby(["k", "rho"])["gap"].mean().unstack().round(3)
    s = w.groupby(["k", "rho"])["avg_size"].mean().unstack().round(2)
    return g, s


def fig_weighted(w, name=None):
    """Coverage gap vs k for fixed source weights rho (1 = pooled, 0 = target-only)."""
    w = w.copy(); w["gap"] = w.coverage - w.nominal
    rhos = sorted(w.rho.unique(), reverse=True)
    fig, axes = plt.subplots(1, 2, figsize=(9.2, 3.3))
    cmap = matplotlib.colors.LinearSegmentedColormap.from_list("b", ["#b9d0ee", BLUE])
    for ax, col, lab in ((axes[0], "gap", "coverage − nominal (LAC)"), (axes[1], "avg_size", "mean prediction-set size")):
        for i, rho in enumerate(rhos):
            per_seed = w[w.rho == rho].groupby(["k", "seed"])[col].mean().reset_index()
            t = per_seed.groupby("k")[col].agg(["mean", "std"]).reset_index()
            c = ORANGE if rho == 1.0 else (GRAY if rho == 0.0 else cmap(i / max(len(rhos) - 1, 1)))
            ls = "--" if rho == 1.0 else (":" if rho == 0.0 else "-")
            name_r = {1.0: "ρ = 1 (pooled)", 0.0: "ρ = 0 (target only)"}.get(rho, f"ρ = {rho:g}")
            ax.plot(t.k, t["mean"], ls=ls, marker="o", ms=4, lw=1.5, color=c, label=name_r)
        ax.set_xlabel("k = target recordings in calibration"); ax.set_ylabel(lab)
    axes[0].axhline(0, color=INK, lw=0.8); axes[0].set_title("(a) coverage gap, mean over classifiers and α"); axes[1].set_title("(b) set size")
    axes[0].legend(fontsize=7)
    fig.tight_layout()
    return save(fig, name) if name else fig
