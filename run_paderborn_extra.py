#!/usr/bin/env python3
"""Additional Paderborn experiments that the shared KAIST pipeline does not cover.

Three questions, each answering a reviewer objection that the main run
(`run_experiments.py --dataset paderborn`) leaves open:

X1  Bearing-grouped validation.  In the Paderborn data the same physical bearing
    is recorded at four operating points and several times per point.  Grouping by
    *recording* (the KAIST protocol) therefore lets a bearing appear in both train
    and test.  X1 repeats the Pareto and coverage experiments with folds grouped by
    *bearing*, so that every test bearing is unseen.  Reported next to the
    recording-grouped numbers, this bounds the optimism of the latter.

X2  Which factor breaks exchangeability, per sensing modality.  Models are fitted
    and calibrated on the baseline operating point (N15_M07_F10) and evaluated on
    each neighbouring point, which differs in exactly one factor: rotational
    speed, load torque, or radial force.  Coverage is measured for the current-only
    tier, the single-accelerometer time-domain tier and the full vibration tier,
    so that the attribution is modality-specific rather than aggregate.

X3  Artificial-to-real damage transfer.  Models are trained on bearings with
    machined (artificial) damage and evaluated on bearings with damage from
    accelerated-lifetime tests (real), and vice versa.  Healthy bearings are split
    between the two sides so that every class is present on both.  Coverage is
    measured with source-only calibration and after recalibration with k target
    recordings, mirroring the operating-point recalibration experiment.

Outputs (results_paderborn/):
    bearing_pareto.csv, bearing_coverage.csv, factor_coverage.csv, damage_transfer.csv

Usage:
    python run_paderborn_extra.py            # all
    python run_paderborn_extra.py x2 x3      # subset
"""
import sys, time
import numpy as np, pandas as pd
from sklearn.model_selection import StratifiedGroupKFold

import paderborn_lib as K
from paderborn_meta import OPERATING, BASELINE_OP, HEALTHY

PARQUET = "data/paderborn_features.parquet"
OUT = "results_paderborn"
ALPHAS = [0.01, 0.02, 0.05, 0.10, 0.15, 0.20, 0.30, 0.40]
SCORES = ["lac", "aps"]
MODELS = ["logreg", "rf"]
BLOCKS_X = ["cur2_full", "vib1_time", "vib1_full"]

df = K.load_features(PARQUET)
BLOCKS = K.feature_blocks(df)
Y = df["label"].values.astype(int)
G = df["recording_id"].values
BEARING = df["bearing"].values
OP = df["load"].values
NC = len(np.unique(Y))
print(f"data: {len(df):,} windows, {df.recording_id.nunique()} recordings, "
      f"{df.bearing.nunique()} bearings, {NC} classes", flush=True)


# --------------------------------------------------------------------------- helpers
def carve_by_group(idx, groups, frac=0.33, seed=0):
    """Hold out a stratified fraction of *groups* (recordings or bearings) from
    idx for conformal calibration.  At least one group per class is held out and
    at least one group per class is kept for fitting."""
    rng = np.random.RandomState(seed)
    sub_g, sub_y = groups[idx], Y[idx]
    g_class = pd.Series(sub_y).groupby(sub_g).first()
    cal = []
    for c in sorted(g_class.unique()):
        gs = g_class[g_class == c].index.to_numpy()
        rng.shuffle(gs)
        k = max(1, int(round(frac * len(gs))))
        k = min(k, len(gs) - 1) if len(gs) > 1 else 1
        cal += list(gs[:k])
    m = np.isin(sub_g, cal)
    return idx[~m], idx[m]


def fit_predict(cols, model, seed, fit_idx, *eval_idx):
    X = df[cols].values
    m, ok = K.fit_quiet(K.make_model(model, seed), X[fit_idx], Y[fit_idx])
    return [K.predict_proba_full(m, X[i], NC) for i in eval_idx], ok


def coverage_rows(p_cal, y_cal, p_te, y_te, **meta):
    rows = []
    for score in SCORES:
        for a in ALPHAS:
            q = K.conformal_qhat(p_cal, y_cal, a, score)
            S = K.conformal_sets(p_te, q, score)
            percls = {f"covclass_{int(c)}": float(S[y_te == c][np.arange((y_te == c).sum()), y_te[y_te == c]].mean())
                      for c in np.unique(y_te)}
            rows.append(dict(**meta, score=score, alpha=a, nominal=1 - a,
                             n_cal=len(y_cal), qhat=q, **K.conformal_metrics(S, y_te), **percls))
    return rows


def splits_by_bearing(n_splits=3, seed=0):
    sgkf = StratifiedGroupKFold(n_splits=n_splits, shuffle=True, random_state=seed)
    for tr, te in sgkf.split(np.zeros(len(Y)), Y, BEARING):
        assert not (set(BEARING[tr]) & set(BEARING[te]))
        yield tr, te


# --------------------------------------------------------------------------- X1
def x1_bearing_grouped(seeds=(0, 1, 2)):
    t0 = time.time()
    par, cov = [], []
    for bname, (cols, spec) in BLOCKS.items():
        for mname in MODELS:
            f1s, convs, pred0 = [], [], None
            for s in seeds:
                pred = np.full(len(Y), -1)
                for tr, te in splits_by_bearing(3, s):
                    (p,), ok = fit_predict(cols, mname, s, tr, te)
                    pred[te] = p.argmax(1); convs.append(ok)
                f1s.append(K.macro_f1(Y, pred))
                if pred0 is None:
                    pred0 = pred
            bm, lo, hi = K.cluster_bootstrap_ci(Y, pred0, BEARING, B=600, seed=0)
            par.append(dict(block=bname, label=spec["label"], model=mname, protocol="bearing",
                            n_feat=len(cols), cost_ops=K.cost_ops(spec),
                            f1_mean=np.mean(f1s), f1_std=np.std(f1s),
                            boot_f1=bm, boot_lo=lo, boot_hi=hi, converged=np.mean(convs)))
            print(f"  [x1] {bname:10s} {mname:7s} F1={np.mean(f1s):.3f}±{np.std(f1s):.3f} "
                  f"IC[{lo:.3f},{hi:.3f}]", flush=True)
    # coverage with calibration carved by bearing (cheap tier of each cascade)
    for bname in BLOCKS_X:
        cols = BLOCKS[bname][0]
        for mname in MODELS:
            for s in seeds:
                pc_cal, y_cal, pc_te, y_te = [], [], [], []
                for tr, te in splits_by_bearing(3, s):
                    fit_idx, cal_idx = carve_by_group(tr, BEARING, 0.33, s)
                    (pcal, pte), _ = fit_predict(cols, mname, s, fit_idx, cal_idx, te)
                    pc_cal.append(pcal); y_cal.append(Y[cal_idx]); pc_te.append(pte); y_te.append(Y[te])
                cov += coverage_rows(np.vstack(pc_cal), np.concatenate(y_cal),
                                     np.vstack(pc_te), np.concatenate(y_te),
                                     protocol="bearing", block=bname, model=mname, seed=s)
                print(f"  [x1-cov] {bname:10s} {mname:7s} seed={s} ok", flush=True)
    pd.DataFrame(par).to_csv(f"{OUT}/bearing_pareto.csv", index=False)
    pd.DataFrame(cov).to_csv(f"{OUT}/bearing_coverage.csv", index=False)
    print(f"[x1] {time.time()-t0:.0f}s -> {OUT}/bearing_pareto.csv, bearing_coverage.csv", flush=True)


# --------------------------------------------------------------------------- X2
def x2_factor_coverage(seeds=(0, 1, 2)):
    t0 = time.time()
    rows = []
    idx = np.arange(len(df))
    base_idx = idx[OP == BASELINE_OP]
    base = OPERATING[BASELINE_OP]
    for bname in BLOCKS_X:
        cols = BLOCKS[bname][0]
        for mname in MODELS:
            for s in seeds:
                # within-baseline: fit / calibration / in-domain test, all by recording
                rest, te_in = carve_by_group(base_idx, G, 0.25, s)
                fit_idx, cal_idx = carve_by_group(rest, G, 0.33, s)
                (p_cal, p_in), ok = fit_predict(cols, mname, s, fit_idx, cal_idx, te_in)
                targets = [("none (in-domain)", te_in, p_in, {})]
                for op, params in OPERATING.items():
                    if op == BASELINE_OP:
                        continue
                    changed = [k for k in ("speed_rpm", "torque_nm", "force_n") if params[k] != base[k]]
                    te = idx[OP == op]
                    X = df[cols].values
                    m, _ = K.fit_quiet(K.make_model(mname, s), X[fit_idx], Y[fit_idx])
                    targets.append(("+".join(changed), te, K.predict_proba_full(m, X[te], NC),
                                    {k: params[k] for k in changed}))
                for factor, te, p_te, extra in targets:
                    f1 = K.macro_f1(Y[te], p_te.argmax(1))
                    rows += coverage_rows(p_cal, Y[cal_idx], p_te, Y[te],
                                          block=bname, model=mname, seed=s, factor=factor,
                                          target_op=str(np.unique(OP[te])[0]), f1=f1,
                                          converged=ok, **{f"to_{k}": v for k, v in extra.items()})
                print(f"  [x2] {bname:10s} {mname:7s} seed={s} ok", flush=True)
    pd.DataFrame(rows).to_csv(f"{OUT}/factor_coverage.csv", index=False)
    print(f"[x2] {time.time()-t0:.0f}s -> {OUT}/factor_coverage.csv", flush=True)


# --------------------------------------------------------------------------- X3
def x3_damage_transfer(seeds=(0, 1, 2), ks=(0, 1, 2, 3, 5, 8)):
    t0 = time.time()
    rows = []
    idx = np.arange(len(df))
    org = df["damage_origin"].values
    healthy_a, healthy_b = HEALTHY[:3], HEALTHY[3:]
    sides = {
        "artificial": idx[(org == "artificial") | np.isin(BEARING, healthy_a)],
        "real":       idx[(org == "real")       | np.isin(BEARING, healthy_b)],
    }
    for train_side, test_side in [("artificial", "real"), ("real", "artificial")]:
        src, tgt = sides[train_side], sides[test_side]
        tgt_recs = np.array(sorted(np.unique(G[tgt])))
        for bname in BLOCKS_X:
            cols = BLOCKS[bname][0]
            X = df[cols].values
            for mname in MODELS:
                for s in seeds:
                    fit_idx, cal_idx = carve_by_group(src, BEARING, 0.33, s)
                    m, ok = K.fit_quiet(K.make_model(mname, s), X[fit_idx], Y[fit_idx])
                    p_srccal = K.predict_proba_full(m, X[cal_idx], NC)
                    p_tgt = K.predict_proba_full(m, X[tgt], NC)
                    f1 = K.macro_f1(Y[tgt], p_tgt.argmax(1))
                    rng = np.random.RandomState(s)
                    perm = tgt_recs.copy(); rng.shuffle(perm)
                    for k in ks:
                        cal_recs = set(perm[:k])
                        te_mask = ~np.isin(G[tgt], list(cal_recs))
                        te = tgt[te_mask]; p_te = p_tgt[te_mask]
                        mixes = {"source": (p_srccal, Y[cal_idx])}
                        if k > 0:
                            tm = np.isin(G[tgt], list(cal_recs))
                            mixes["target"] = (p_tgt[tm], Y[tgt][tm])
                            mixes["source+target"] = (np.vstack([p_srccal, p_tgt[tm]]),
                                                      np.concatenate([Y[cal_idx], Y[tgt][tm]]))
                        for mix, (pc, yc) in mixes.items():
                            rows += coverage_rows(pc, yc, p_te, Y[te], train=train_side, test=test_side,
                                                  block=bname, model=mname, seed=s, k=k, mix=mix,
                                                  f1_target=f1, converged=ok)
                    print(f"  [x3] {train_side}->{test_side} {bname:10s} {mname:7s} seed={s} F1={f1:.3f}",
                          flush=True)
    pd.DataFrame(rows).to_csv(f"{OUT}/damage_transfer.csv", index=False)
    print(f"[x3] {time.time()-t0:.0f}s -> {OUT}/damage_transfer.csv", flush=True)


if __name__ == "__main__":
    which = sys.argv[1:] or ["x2", "x3", "x1"]
    if "x2" in which: print("\n=== X2 coverage by shifted factor and modality ==="); x2_factor_coverage()
    if "x3" in which: print("\n=== X3 artificial <-> real damage transfer ==="); x3_damage_transfer()
    if "x1" in which: print("\n=== X1 bearing-grouped validation ==="); x1_bearing_grouped()
