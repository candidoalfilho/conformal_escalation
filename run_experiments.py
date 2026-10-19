"""
Experiment driver.  Writes the result CSVs for one dataset.

    python run_experiments.py --dataset kaist     [e1 e2 e3 e4 e5 e6]
    python run_experiments.py --dataset paderborn [e1 e2 e3 e4 e5 e6]

The experiments are dataset-agnostic; the dataset adapter (``kaist_lib`` or
``paderborn_lib``) supplies the feature blocks and the names of the cheap and
expensive tiers used by the cascade experiments.
"""
import sys, time, json, argparse
import numpy as np
import pandas as pd

_ap = argparse.ArgumentParser()
_ap.add_argument("--dataset", choices=["kaist", "paderborn"], default="kaist")
_ap.add_argument("which", nargs="*")
_args = _ap.parse_args()

DATASETS = {
    # adapter, parquet, output dir, cheap tier, expensive tier, cheap tier of the 2nd cascade, learning-curve blocks
    "kaist":     dict(lib="kaist_lib",     parquet="data/kaist_features.parquet",     out="results",
                      cheap="cur_full",  expensive="vib_full",  cheap2="vib1_time", lc=["cur_full", "vib_full", "vib_time"]),
    "paderborn": dict(lib="paderborn_lib", parquet="data/paderborn_features.parquet", out="results_paderborn",
                      cheap="cur2_full", expensive="vib1_full", cheap2="vib1_time", lc=["cur2_full", "vib1_full", "vib1_time"]),
}
CFG = DATASETS[_args.dataset]
K = __import__(CFG["lib"])

PARQUET = CFG["parquet"]
OUT = CFG["out"]
import os; os.makedirs(OUT, exist_ok=True)
SEEDS = [0, 1, 2]
ALPHAS = [0.01, 0.02, 0.05, 0.10, 0.15, 0.20, 0.30, 0.40]
CHEAP, EXPENSIVE, CHEAP2 = CFG["cheap"], CFG["expensive"], CFG["cheap2"]

df = K.load_features(PARQUET)
BLOCKS = K.feature_blocks(df)
Y = df["label"].values.astype(int)
G = df["recording_id"].values
NC = len(np.unique(Y))
print(f"[{_args.dataset}] {df.shape[0]} windows, {len(np.unique(G))} recordings, {NC} classes")


def oof_predictions(cols, model_name, protocol, seed=0):
    """Predições fora-da-amostra para todas as janelas, sob um protocolo."""
    X = df[cols].values
    pred = np.full(len(Y), -1)
    proba = np.zeros((len(Y), NC))
    conv = []
    if protocol == "grouped":
        it = [(tr, te, None) for tr, te in K.splits_grouped(df, 3, seed)]
    elif protocol == "lolo":
        it = list(K.splits_lolo(df))
    else:
        raise ValueError(protocol)
    for tr, te, _ in it:
        m, ok = K.fit_quiet(K.make_model(model_name, seed), X[tr], Y[tr])
        conv.append(ok)
        proba[te] = K.predict_proba_full(m, X[te], NC)
        pred[te] = proba[te].argmax(1)
    return pred, proba, float(np.mean(conv))


# ---------------------------------------------------------------------------
def e1_pareto():
    rows = []
    t0 = time.time()
    for bname, (cols, spec) in BLOCKS.items():
        ops = K.cost_ops(spec)
        for mname in K.MODELS:
            for protocol in ["grouped", "lolo"]:
                seeds = SEEDS if protocol == "grouped" else [0]
                f1s, accs, convs = [], [], []
                pred0 = None
                for s in seeds:
                    pred, _, cf = oof_predictions(cols, mname, protocol, s)
                    f1s.append(K.macro_f1(Y, pred)); accs.append(K.acc(Y, pred))
                    convs.append(cf)
                    if pred0 is None:
                        pred0 = pred
                bm, blo, bhi = K.cluster_bootstrap_ci(Y, pred0, G, B=600, seed=0)
                rows.append(dict(block=bname, label=spec["label"], model=mname,
                                 protocol=protocol, n_feat=len(cols), cost_ops=ops,
                                 f1_mean=np.mean(f1s), f1_std=np.std(f1s),
                                 acc=np.mean(accs), boot_f1=bm, boot_lo=blo, boot_hi=bhi,
                                 converged=np.mean(convs)))
                print(f"  {bname:14s} {mname:7s} {protocol:8s} "
                      f"F1={np.mean(f1s):.3f}±{np.std(f1s):.3f} "
                      f"IC[{blo:.3f},{bhi:.3f}] conv={np.mean(convs):.2f}", flush=True)
    pd.DataFrame(rows).to_csv(f"{OUT}/pareto.csv", index=False)
    print(f"[e1] {time.time()-t0:.0f}s -> {OUT}/pareto.csv")


# ---------------------------------------------------------------------------
def e2_learning_curve():
    """A extração parou em 50 janelas/gravação. A curva já saturou?
    Se saturou, a objeção 'poucas janelas' morre sem re-extrair nada."""
    rows = []
    t0 = time.time()
    for nw in [10, 20, 30, 40, 50]:
        keep = df["window_idx"].values < nw
        sub = df[keep].reset_index(drop=True)
        ysub = sub["label"].values.astype(int)
        gsub = sub["recording_id"].values
        for bname in CFG["lc"]:
            cols = BLOCKS[bname][0]
            X = sub[cols].values
            for mname in ["logreg", "rf"]:
                f1s = []
                for s in SEEDS:
                    pred = np.full(len(ysub), -1)
                    for tr, te in K.splits_grouped(sub, 3, s):
                        m, _ = K.fit_quiet(K.make_model(mname, s), X[tr], ysub[tr])
                        pred[te] = K.predict_proba_full(m, X[te], NC).argmax(1)
                    f1s.append(K.macro_f1(ysub, pred))
                rows.append(dict(n_windows=nw, block=bname, model=mname,
                                 f1_mean=np.mean(f1s), f1_std=np.std(f1s)))
                print(f"  nw={nw:3d} {bname:10s} {mname:7s} F1={np.mean(f1s):.3f}", flush=True)
    pd.DataFrame(rows).to_csv(f"{OUT}/learning_curve.csv", index=False)
    print(f"[e2] {time.time()-t0:.0f}s -> {OUT}/learning_curve.csv")


# ---------------------------------------------------------------------------
def _conformal_run(cheap_block, expensive_block, model_name, protocol, seed):
    """Uma passada: treina barato e caro no MESMO conjunto de ajuste, calibra o
    conforme em gravações separadas, avalia em gravações nunca vistas."""
    cheap_cols = BLOCKS[cheap_block][0]
    exp_cols = BLOCKS[expensive_block][0]
    Xc, Xe = df[cheap_cols].values, df[exp_cols].values
    if protocol == "grouped":
        it = [(tr, te) for tr, te in K.splits_grouped(df, 3, seed)]
    else:
        it = [(tr, te) for tr, te, _ in K.splits_lolo(df)]

    pool = dict(pc_cal=[], y_cal=[], pc_te=[], pe_te=[], y_te=[], g_te=[], load_te=[])
    for tr, te in it:
        fit_idx, cal_idx = K.carve_calibration(df, tr, frac=0.33, seed=seed)
        mc, _ = K.fit_quiet(K.make_model(model_name, seed), Xc[fit_idx], Y[fit_idx])
        me, _ = K.fit_quiet(K.make_model(model_name, seed), Xe[fit_idx], Y[fit_idx])
        pool["pc_cal"].append(K.predict_proba_full(mc, Xc[cal_idx], NC))
        pool["y_cal"].append(Y[cal_idx])
        pool["pc_te"].append(K.predict_proba_full(mc, Xc[te], NC))
        pool["pe_te"].append(K.predict_proba_full(me, Xe[te], NC))
        pool["y_te"].append(Y[te]); pool["g_te"].append(G[te])
        pool["load_te"].append(df["load"].values[te])
    return {k: (np.concatenate(v) if v[0].ndim == 1 else np.vstack(v))
            for k, v in pool.items()}


# cascatas testadas: (barato, caro). A segunda saiu do E1: 1 acelerômetro sem
# FFT já chega perto dos 4 com FFT, então a cascata realista talvez seja essa.
CASCADES = [(CHEAP, EXPENSIVE), (CHEAP2, EXPENSIVE)]


def e3_conformal_coverage():
    """A cobertura empírica bate com o nominal 1-alfa? E sob deslocamento de carga?"""
    rows = []
    t0 = time.time()
    for protocol in ["grouped", "lolo"]:
        for mname in ["logreg", "rf"]:
            for seed in SEEDS:
                P = _conformal_run(CHEAP, EXPENSIVE, mname, protocol, seed)
                for score in ["lac", "aps"]:
                    for a in ALPHAS:
                        q = K.conformal_qhat(P["pc_cal"], P["y_cal"], a, score)
                        S = K.conformal_sets(P["pc_te"], q, score)
                        m = K.conformal_metrics(S, P["y_te"])
                        # coverage per held-out operating point and per class
                        percov = {}
                        for L in np.unique(P["load_te"]):
                            sel = P["load_te"] == L
                            percov[f"cov_{L}"] = float(S[sel][np.arange(sel.sum()), P["y_te"][sel]].mean())
                        for c in np.unique(P["y_te"]):
                            sel = P["y_te"] == c
                            percov[f"covclass_{int(c)}"] = float(S[sel][np.arange(sel.sum()), P["y_te"][sel]].mean())
                        rows.append(dict(protocol=protocol, model=mname, seed=seed,
                                         score=score, alpha=a, nominal=1 - a,
                                         n_cal=len(P["y_cal"]), qhat=q, **m, **percov))
                print(f"  {protocol:8s} {mname:7s} seed={seed} ok", flush=True)
    pd.DataFrame(rows).to_csv(f"{OUT}/conformal_coverage.csv", index=False)
    print(f"[e3] {time.time()-t0:.0f}s -> {OUT}/conformal_coverage.csv")


# ---------------------------------------------------------------------------
def e4_gate():
    """O experimento principal.

    Portão conforme: acorda o acelerômetro sse o conjunto conforme do modelo de
    corrente NÃO for unitário. O nível alfa é o botão — e ele carrega garantia.
    Baseline: limiar de softmax (o que RESULTS_kaist.md fazia).
    Comparação justa: mesma fração de escalonamento nos dois.
    """
    rows = []
    t0 = time.time()
    combos = [(c, e, p, m, s) for (c, e) in CASCADES
              for p in ["grouped", "lolo"] for m in ["logreg", "rf"] for s in SEEDS]
    for cheap_b, exp_b, protocol, mname, seed in combos:
        casc = f"{cheap_b}->{exp_b}"
        cheap_ops = K.cost_ops(BLOCKS[cheap_b][1])
        exp_ops = K.cost_ops(BLOCKS[exp_b][1])
        P = _conformal_run(cheap_b, exp_b, mname, protocol, seed)
        y = P["y_te"]
        cheap_pred = P["pc_te"].argmax(1)
        exp_pred = P["pe_te"].argmax(1)
        base_cheap = K.macro_f1(y, cheap_pred)
        base_exp = K.macro_f1(y, exp_pred)
        common = dict(cascade=casc, protocol=protocol, model=mname, seed=seed,
                      cheap_ops=cheap_ops, exp_ops=exp_ops,
                      f1_cheap=base_cheap, f1_exp=base_exp)

        def emit(gate, knob, esc, pred, S=None):
            frac = float(esc.mean())
            keep = ~esc
            sel_acc = float((pred[keep] == y[keep]).mean()) if keep.any() else np.nan
            sel_cov = np.nan
            if S is not None and keep.any():
                sel_cov = float(S[keep][np.arange(keep.sum()), y[keep]].mean())
            rows.append(dict(gate=gate, knob=float(knob), esc_frac=frac,
                             avg_cost_ops=cheap_ops + frac * exp_ops,
                             f1=K.macro_f1(y, pred), acc=K.acc(y, pred),
                             sel_acc_no_esc=sel_acc, sel_cov_no_esc=sel_cov, **common))

        for score in ["lac", "aps"]:
            for a in ALPHAS:
                q = K.conformal_qhat(P["pc_cal"], P["y_cal"], a, score)
                S = K.conformal_sets(P["pc_te"], q, score)
                # Eq. (2): escalate iff the set is NOT a singleton (empty sets escalate too).
                esc = S.sum(1) != 1
                # where the gate does not escalate the set is a singleton: use that label
                pred = np.where(esc, exp_pred, S.argmax(1))
                emit(f"conformal_{score}", a, esc, pred, S)

        # baseline: limiar de softmax (o que RESULTS_kaist.md fazia)
        conf = P["pc_te"].max(1)
        for tau in np.linspace(0, 1, 41):
            esc = conf < tau
            emit("softmax", tau, esc, np.where(esc, exp_pred, cheap_pred))

        print(f"  {casc:22s} {protocol:8s} {mname:7s} s={seed} "
              f"barato={base_cheap:.3f} caro={base_exp:.3f}", flush=True)
    pd.DataFrame(rows).to_csv(f"{OUT}/gate.csv", index=False)
    print(f"[e4] {time.time()-t0:.0f}s -> {OUT}/gate.csv")


# ---------------------------------------------------------------------------
def e5_recalibration():
    """A correção: recalibrar no ponto de operação alvo.

    O E3 mostrou que a cobertura conforme desaba quando a carga muda. A pergunta
    de engenharia é: quanto dado do NOVO ponto de operação é preciso para
    recuperar a garantia? Duas variantes, ambas realistas em comissionamento:

      'rec' — k gravações inteiras da carga alvo entram na calibração.
              Estatisticamente limpo (calibração e teste são gravações distintas).
      'win' — os primeiros m janelas de CADA gravação alvo entram na calibração.
              É o que se faz na prática ("rode a máquina um instante e rotule"),
              mas calibração e teste dividem gravação: a cobertura sai otimista.
              O contraste entre as duas curvas é o próprio recado.
    """
    import itertools
    rows = []
    t0 = time.time()
    cheap_cols = BLOCKS[CHEAP][0]
    Xc = df[cheap_cols].values
    loads = sorted(df["load"].unique())
    alphas = [0.05, 0.10, 0.20, 0.30]
    SEEDS5 = [0, 1, 2, 3, 4]

    for mname in ["logreg", "rf"]:
        for L in loads:
            src = np.where(df["load"].values != L)[0]
            tgt = np.where(df["load"].values == L)[0]
            tgt_recs = np.array(sorted(df.iloc[tgt]["recording_id"].unique()))
            for seed in SEEDS5:
                fit_idx, src_cal = K.carve_calibration(df, src, frac=0.33, seed=seed)
                m, _ = K.fit_quiet(K.make_model(mname, seed), Xc[fit_idx], Y[fit_idx])
                p_srccal = K.predict_proba_full(m, Xc[src_cal], NC)
                rng = np.random.RandomState(seed)

                # --- variante 'rec'
                perm = tgt_recs.copy(); rng.shuffle(perm)
                for k in [0, 1, 2, 3, 5, 8]:
                    cal_recs = set(perm[:k])
                    te_idx = np.array([i for i in tgt
                                       if df["recording_id"].values[i] not in cal_recs])
                    tc_idx = np.array([i for i in tgt
                                       if df["recording_id"].values[i] in cal_recs], dtype=int)
                    if len(te_idx) == 0:
                        continue
                    p_te = K.predict_proba_full(m, Xc[te_idx], NC)
                    for mix in (["source", "source+target", "target"] if k > 0 else ["source"]):
                        if mix == "source":
                            pc, yc = p_srccal, Y[src_cal]
                        elif mix == "target":
                            pc = K.predict_proba_full(m, Xc[tc_idx], NC); yc = Y[tc_idx]
                        else:
                            pc = np.vstack([p_srccal, K.predict_proba_full(m, Xc[tc_idx], NC)])
                            yc = np.concatenate([Y[src_cal], Y[tc_idx]])
                        for a in alphas:
                            q = K.conformal_qhat(pc, yc, a, "lac")
                            S = K.conformal_sets(p_te, q, "lac")
                            mm = K.conformal_metrics(S, Y[te_idx])
                            rows.append(dict(variant="rec", model=mname, load=L, seed=seed,
                                             k=k, n_cal=len(yc), mix=mix, alpha=a,
                                             nominal=1 - a, esc_frac=float((S.sum(1) != 1).mean()),
                                             **mm))
                # --- variante 'win'
                for mw in [0, 5, 10, 20]:
                    wi = df["window_idx"].values
                    tc_idx = tgt[wi[tgt] < mw]
                    te_idx = tgt[wi[tgt] >= mw]
                    if len(te_idx) == 0:
                        continue
                    p_te = K.predict_proba_full(m, Xc[te_idx], NC)
                    for mix in (["source", "source+target", "target"] if mw > 0 else ["source"]):
                        if mix == "source":
                            pc, yc = p_srccal, Y[src_cal]
                        elif mix == "target":
                            pc = K.predict_proba_full(m, Xc[tc_idx], NC); yc = Y[tc_idx]
                        else:
                            pc = np.vstack([p_srccal, K.predict_proba_full(m, Xc[tc_idx], NC)])
                            yc = np.concatenate([Y[src_cal], Y[tc_idx]])
                        for a in alphas:
                            q = K.conformal_qhat(pc, yc, a, "lac")
                            S = K.conformal_sets(p_te, q, "lac")
                            mm = K.conformal_metrics(S, Y[te_idx])
                            rows.append(dict(variant="win", model=mname, load=L, seed=seed,
                                             k=mw, n_cal=len(yc), mix=mix, alpha=a,
                                             nominal=1 - a, esc_frac=float((S.sum(1) != 1).mean()),
                                             **mm))
            print(f"  {mname:7s} carga alvo {L} ok", flush=True)
    pd.DataFrame(rows).to_csv(f"{OUT}/recalibration.csv", index=False)
    print(f"[e5] {time.time()-t0:.0f}s -> {OUT}/recalibration.csv")


# ---------------------------------------------------------------------------
def e6_weighted_recalibration():
    """Weighted (non-exchangeable) conformal prediction as the alternative to
    discarding the source calibration set (Tibshirani et al. 2019; Barber et al. 2023).

    For each held-out operating point and k target recordings, the calibration
    set pools source and target scores but the source scores receive weight rho
    (target scores weight 1).  rho = 1 is ordinary pooling, rho -> 0 is
    target-only; intermediate values are the fixed-weight schemes a practitioner
    could set without estimating likelihood ratios.
    """
    rows = []
    t0 = time.time()
    cheap_cols = BLOCKS[CHEAP][0]
    Xc = df[cheap_cols].values
    loads = sorted(df["load"].unique())
    alphas = [0.05, 0.10, 0.20, 0.30]
    rhos = [1.0, 0.3, 0.1, 0.03, 0.0]
    SEEDS6 = [0, 1, 2, 3, 4]        # same seeds as E5, so that rho = 0 reproduces "target only" and rho = 1 "pooled"
    for mname in ["logreg", "rf"]:
        for L in loads:
            src = np.where(df["load"].values != L)[0]
            tgt = np.where(df["load"].values == L)[0]
            tgt_recs = np.array(sorted(df.iloc[tgt]["recording_id"].unique()))
            for seed in SEEDS6:
                fit_idx, src_cal = K.carve_calibration(df, src, frac=0.33, seed=seed)
                m, _ = K.fit_quiet(K.make_model(mname, seed), Xc[fit_idx], Y[fit_idx])
                s_src = K.lac_scores(K.predict_proba_full(m, Xc[src_cal], NC), Y[src_cal])
                rng = np.random.RandomState(seed)
                perm = tgt_recs.copy(); rng.shuffle(perm)
                for k in [1, 2, 3, 5, 8]:
                    cal_recs = set(perm[:k])
                    rec = df["recording_id"].values
                    te_idx = np.array([i for i in tgt if rec[i] not in cal_recs])
                    tc_idx = np.array([i for i in tgt if rec[i] in cal_recs], dtype=int)
                    if len(te_idx) == 0 or len(tc_idx) == 0:
                        continue
                    p_te = K.predict_proba_full(m, Xc[te_idx], NC)
                    s_tgt = K.lac_scores(K.predict_proba_full(m, Xc[tc_idx], NC), Y[tc_idx])
                    for rho in rhos:
                        sc = np.concatenate([s_src, s_tgt])
                        w = np.concatenate([np.full(len(s_src), rho), np.ones(len(s_tgt))])
                        for a in alphas:
                            q = K.weighted_conformal_qhat(sc, w, a)
                            S = K.conformal_sets(p_te, q, "lac")
                            mm = K.conformal_metrics(S, Y[te_idx])
                            rows.append(dict(model=mname, load=L, seed=seed, k=k, rho=rho,
                                             n_src=len(s_src), n_tgt=len(s_tgt), alpha=a, nominal=1 - a,
                                             esc_frac=float((S.sum(1) != 1).mean()), **mm))
            print(f"  [e6] {mname:7s} target {L} ok", flush=True)
    pd.DataFrame(rows).to_csv(f"{OUT}/weighted_recalibration.csv", index=False)
    print(f"[e6] {time.time()-t0:.0f}s -> {OUT}/weighted_recalibration.csv")


if __name__ == "__main__":
    which = _args.which or ["e1", "e2", "e3", "e4", "e5", "e6"]
    if "e1" in which: print("\n=== E1 cost-accuracy frontier ===");      e1_pareto()
    if "e2" in which: print("\n=== E2 learning curve ===");              e2_learning_curve()
    if "e3" in which: print("\n=== E3 conformal coverage ===");          e3_conformal_coverage()
    if "e4" in which: print("\n=== E4 escalation gate ===");             e4_gate()
    if "e5" in which: print("\n=== E5 recalibration ===");               e5_recalibration()
    if "e6" in which: print("\n=== E6 weighted recalibration ===");      e6_weighted_recalibration()
