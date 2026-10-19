"""Figuras do paper, em INGLÊS e no tamanho de coluna do IEEE.
Coluna simples = 3.4in; largura total = 7.0in. Fontes em 7-8pt para que
o texto da figura fique do tamanho do texto do corpo depois da redução.
"""
import numpy as np, pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

R = "../results"
plt.rcParams.update({
    "font.size": 7.4, "axes.grid": True, "grid.alpha": 0.22,
    "axes.spines.top": False, "axes.spines.right": False,
    "figure.dpi": 200, "savefig.bbox": "tight", "savefig.pad_inches": 0.02,
    "legend.frameon": False, "axes.labelsize": 7.4, "axes.titlesize": 7.8,
    "xtick.labelsize": 6.8, "ytick.labelsize": 6.8, "legend.fontsize": 6.6,
    "font.family": "serif", "mathtext.fontset": "dejavuserif",
})
BLUE, RED, GREY, GREEN, AMBER = "#2563eb", "#dc2626", "#64748b", "#059669", "#d97706"


def save(fig, name):
    fig.savefig(f"figs/{name}.pdf")
    fig.savefig(f"figs/{name}.png", dpi=200)
    plt.close(fig)
    print("  figs/" + name)


# === Fig 1 (largura total): cobertura — o achado central ====================
cv = pd.read_csv(f"{R}/conformal_coverage.csv")
fig, axes = plt.subplots(1, 2, figsize=(7.0, 2.35))

ax = axes[0]
ax.plot([0.55, 1], [0.55, 1], "--", color=GREY, lw=0.9, label="nominal")
for prot, col, lab in [("grouped", BLUE, "grouped by recording"),
                       ("lolo", RED, "leave-one-load-out")]:
    d = cv[(cv.protocol == prot) & (cv.score == "lac")].groupby("nominal")["coverage"]
    ax.errorbar(d.mean().index, d.mean().values, yerr=d.std().values,
                fmt="o-", ms=3.2, lw=1.2, capsize=1.8, color=col, label=lab)
ax.set_xlabel(r"nominal coverage $1-\alpha$")
ax.set_ylabel("empirical coverage")
ax.legend(loc="upper left")
ax.set_title("(a) the guarantee holds until the load changes", loc="left")

ax = axes[1]
sub = cv[(cv.protocol == "lolo") & (cv.score == "lac")]
g = sub.groupby("nominal")[["cov_0Nm", "cov_2Nm", "cov_4Nm"]].mean()
for c, lab, col in zip(g.columns, ["0 N$\\cdot$m", "2 N$\\cdot$m", "4 N$\\cdot$m"],
                       [BLUE, AMBER, GREEN]):
    ax.plot(g.index, g[c], "o-", ms=3.2, lw=1.2, color=col, label=f"held-out {lab}")
ax.plot([0.55, 1], [0.55, 1], "--", color=GREY, lw=0.9)
ax.set_xlabel(r"nominal coverage $1-\alpha$")
ax.set_ylabel("empirical coverage")
ax.legend(loc="upper left")
ax.set_title("(b) breakage is uneven across operating points", loc="left")
save(fig, "f_coverage")

# === Fig 2 (coluna simples): recalibração — o conserto =====================
rc = pd.read_csv(f"{R}/recalibration.csv")
rc["gap"] = rc.coverage - rc.nominal
fig, ax = plt.subplots(figsize=(3.4, 2.25))
for mix, col, lab, mk in [("source", RED, "source calib. only", "o"),
                          ("source+target", AMBER, "source $+$ target", "s"),
                          ("target", GREEN, "target only", "D")]:
    d = rc[(rc.variant == "rec") & (rc.mix == mix)].groupby("k")["gap"].mean()
    ax.plot(d.index, d.values, mk + "-", ms=3.4, lw=1.2, color=col, label=lab)
ax.axhline(0, color="k", lw=0.8, ls="--")
ax.annotate("nominal", (0.15, 0.012), fontsize=6.2, color="k", ha="left")
ax.set_xlabel("target-load recordings used for calibration ($k$)")
ax.set_ylabel("coverage $-$ nominal")
ax.legend(loc="lower right")
save(fig, "f_recal")

# === Fig 3 (opcional, largura total): portão vs softmax ====================
gt = pd.read_csv(f"{R}/gate.csv")
fig, axes = plt.subplots(1, 2, figsize=(7.0, 2.3))
for ax, casc, title in zip(
        axes, ["cur_full->vib_full", "vib1_time->vib_full"],
        [r"(a) current $\rightarrow$ 4 accel.+FFT",
         r"(b) 1 accel. (time) $\rightarrow$ 4 accel.+FFT"]):
    d = gt[(gt.cascade == casc) & (gt.protocol == "grouped")]
    sm = d[d.gate == "softmax"].groupby("knob")[["esc_frac", "f1"]].mean().sort_values("esc_frac")
    ax.plot(sm.esc_frac, sm.f1, "-", color=GREY, lw=1.5, label="softmax threshold $\\tau$")
    cf = d[d.gate == "conformal_lac"].groupby("knob")[["esc_frac", "f1"]].mean()
    ax.plot(cf.esc_frac, cf.f1, "o", ms=4.2, color=BLUE, mec="white", mew=0.5,
            label="conformal gate (LAC)")
    for i, (a, r) in enumerate([(a, r) for a, r in cf.iterrows()
                                if a in (0.05, 0.10, 0.20, 0.30)]):
        ax.annotate(rf"$\alpha$={a:g}", (r.esc_frac, r.f1), fontsize=6.0, color=BLUE,
                    xytext=(4, [-9, 6, -9, 6][i]), textcoords="offset points")
    ax.set_xlabel("fraction of windows that wake the accelerometer")
    ax.set_title(title, loc="left")
axes[0].set_ylabel("system macro-F1")
axes[0].legend(loc="lower right")
save(fig, "f_gate")
print("ok")
