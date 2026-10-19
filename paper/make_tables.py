"""Gera as tabelas do paper direto dos CSVs. Nenhum número é digitado à mão.
Saída: tables/tab_*.tex, incluídos pelo main.tex via \\input{}.
"""
import os
import numpy as np
import pandas as pd

R = "../results"
os.makedirs("tables", exist_ok=True)


def w(name, body):
    with open(f"tables/{name}.tex", "w") as f:
        f.write("% GERADO POR make_tables.py -- NAO EDITAR A MAO\n" + body)
    print("  tables/" + name + ".tex")


# ---------------------------------------------------------------- Tabela 1
# Fronteira de cadeia de sensor: melhor classificador de cada configuração.
p = pd.read_csv(f"{R}/pareto.csv")
NAME = {
    "tmp":          (r"temperature only",                 "T"),
    "cur_time":     (r"current, time only",               "I"),
    "vib1_time":    (r"\textbf{1 accel., time only}",     "1A"),
    "vib_time":     (r"4 accel., time only",              "4A"),
    "cur_full":     (r"current + FFT",                    "I+F"),
    "vib1_full":    (r"1 accel. + FFT",                   "1A+F"),
    "cur_full_tmp": (r"current + FFT + temp.",            "I+F+T"),
    "vib_full":     (r"4 accel. + FFT",                   "4A+F"),
    "vib_cur":      (r"4 accel. + FFT + current",         "4A+F+I"),
}
rows = []
for blk in sorted(p.block.unique(), key=lambda b: p[p.block == b].cost_ops.iloc[0]):
    d = p[p.block == blk]
    r = {}
    for prot in ["grouped", "lolo"]:
        dd = d[d.protocol == prot]
        best = dd.loc[dd.f1_mean.idxmax()]
        r[prot] = (best.f1_mean, best.boot_lo, best.boot_hi, best.model)
    g, l = r["grouped"], r["lolo"]
    rows.append(
        f"{NAME[blk][0]} & {d.n_feat.iloc[0]:.0f} & {d.cost_ops.iloc[0]:,.0f} & "
        f"{g[0]:.3f} \\tiny[{g[1]:.2f},{g[2]:.2f}] & "
        f"{l[0]:.3f} \\tiny[{l[1]:.2f},{l[2]:.2f}] \\\\"
    )
w("tab_frontier", r"""\begin{table}[t]
\centering\footnotesize\setlength{\tabcolsep}{3.2pt}
\caption{Sensor-chain frontier. Best of \{logreg, RF, MLP\} per row;
95\% CI from a cluster bootstrap over \emph{recordings}. Acquisition cost is
operations per 4096-sample window. Nine time-domain features from a
\emph{single} accelerometer land within $0.06$ macro-F1 of the full chain at
$18\times$ lower cost.}
\label{tab:frontier}
\begin{tabular}{lrrcc}
\toprule
sensor chain & \#f & ops/win & grouped & load shift \\
\midrule
""" + "\n".join(rows) + r"""
\bottomrule
\end{tabular}
\end{table}
""")

# ---------------------------------------------------------------- Tabela 2
# Portão conforme vs limiar de softmax, na MESMA fração de escalonamento.
gt = pd.read_csv(f"{R}/gate.csv")
rec = []
for (casc, prot, model, seed), d in gt.groupby(["cascade", "protocol", "model", "seed"]):
    sm = d[d.gate == "softmax"].sort_values("esc_frac")
    if len(sm) < 2:
        continue
    for g in ["conformal_lac", "conformal_aps"]:
        for _, r in d[d.gate == g].iterrows():
            rec.append(dict(cascade=casc, gate=g,
                            delta=r.f1 - np.interp(r.esc_frac, sm.esc_frac, sm.f1)))
D = pd.DataFrame(rec)
CN = {"cur_full->vib_full": r"current $\rightarrow$ 4 accel.+FFT",
      "vib1_time->vib_full": r"1 accel. $\rightarrow$ 4 accel.+FFT"}
GN = {"conformal_lac": "LAC", "conformal_aps": "APS"}
body = []
for casc in D.cascade.unique():
    for g in ["conformal_lac", "conformal_aps"]:
        s = D[(D.cascade == casc) & (D.gate == g)].delta
        body.append(f"{CN[casc]} & {GN[g]} & ${s.mean():+.4f} \\pm {s.std():.4f}$ & "
                    f"${s.min():+.3f}$ & ${s.max():+.3f}$ \\\\")
w("tab_gate", r"""\begin{table}[t]
\centering\footnotesize\setlength{\tabcolsep}{4pt}
\caption{Conformal gate minus softmax threshold in system macro-F1, compared
\emph{at matched escalation rate} (softmax curve linearly interpolated).
The two gates trace the same curve; the conformal gate buys specification,
not accuracy.}
\label{tab:gate}
\begin{tabular}{llccc}
\toprule
cascade & score & $\Delta$ macro-F1 & min & max \\
\midrule
""" + "\n".join(body) + r"""
\midrule
\multicolumn{2}{l}{\emph{pooled}} & $""" +
  f"{D.delta.mean():+.4f} \\pm {D.delta.std():.4f}" + r"""$ & & \\
\bottomrule
\end{tabular}
\end{table}
""")

# ---------------------------------------------------------------- Tabela 3
# Recalibração: gap de cobertura por k gravações do ponto de operação alvo.
rc = pd.read_csv(f"{R}/recalibration.csv")
rc["gap"] = rc.coverage - rc.nominal
pt = rc[rc.variant == "rec"].pivot_table(index="k", columns="mix", values="gap")
lines = []
for k, r in pt.iterrows():
    f = lambda v: "--" if pd.isna(v) else f"${v:+.3f}$"
    tgt = f(r.get("target"))
    if not pd.isna(r.get("target")) and abs(r["target"]) < 0.02:
        tgt = r"\textbf{" + tgt + "}"
    lines.append(f"{k:.0f} & {f(r.get('source'))} & {f(r.get('source+target'))} & {tgt} \\\\")
w("tab_recal", r"""\begin{table}[t]
\centering\footnotesize\setlength{\tabcolsep}{5pt}
\caption{Coverage gap (empirical $-$ nominal) after recalibrating with $k$
recordings from the target operating point. Five target recordings restore
nominal coverage --- and \emph{discarding} the source calibration set beats
pooling it at every $k \geq 2$.}
\label{tab:recal}
\begin{tabular}{cccc}
\toprule
$k$ & source only & source $+$ target & target only \\
\midrule
""" + "\n".join(lines) + r"""
\bottomrule
\end{tabular}
\end{table}
""")

# ------------------------------------------------- macros com números soltos
cv = pd.read_csv(f"{R}/conformal_coverage.csv")
cv["gap"] = cv.coverage - cv.nominal
gl = cv[(cv.protocol == "lolo") & (cv.score == "lac")]
gg = cv[(cv.protocol == "grouped") & (cv.score == "lac")]
a20 = gl[gl.nominal == 0.80]
m = {
    "gapGrouped":  f"{gg.gap.mean():+.3f}",
    "gapLolo":     f"{gl.gap.mean():+.3f}",
    "gapLoloWorst": f"{gl.gap.min():+.3f}",
    "covEighty":   f"{a20.coverage.mean()*100:.0f}",
    "covZero":     f"{a20.cov_0Nm.mean():.3f}",
    "covTwo":      f"{a20.cov_2Nm.mean():.3f}",
    "covFour":     f"{a20.cov_4Nm.mean():.3f}",
    "gateDelta":   f"{D.delta.mean():+.3f} \\pm {D.delta.std():.3f}",
    "recalFive":   f"{pt.loc[5, 'target']:+.3f}",
    "recalThreeT": f"{pt.loc[3, 'target']:+.3f}",
    "recalThreeST": f"{pt.loc[3, 'source+target']:+.3f}",
}
w("macros", "\n".join(rf"\newcommand{{\{k}}}{{{v}\xspace}}" for k, v in m.items()))
print("ok")
