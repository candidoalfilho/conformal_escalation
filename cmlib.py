"""
cmlib — shared library for the conformal sensor-escalation study.

Dataset-agnostic components: acquisition cost model (operations and energy),
classifier families with convergence checking, validation protocols grouped by
recording, split conformal prediction (LAC and APS scores, weighted variant),
cluster bootstrap confidence intervals and metrics.  Dataset-specific feature
blocks live in the adapters ``kaist_lib.py`` and ``paderborn_lib.py``, which
re-export everything here.
"""

from __future__ import annotations

import warnings
import numpy as np
import pandas as pd

from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import f1_score, accuracy_score
from sklearn.model_selection import StratifiedGroupKFold
from sklearn.neural_network import MLPClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.exceptions import ConvergenceWarning

RNG_GLOBAL = 0
N_WINDOW = 4096            # samples per window (set in the feature extractors)
META_COLS = ["label", "class", "load", "recording_id", "window_idx"]
TIME_FEATS = ["mean", "std", "rms", "p2p", "kurt", "skew", "crest", "shape", "impulse"]
FFT_FEATS = ["domfreq", "centroid", "entropy", "e0_2000", "e2000_6000", "e6000_12800"]


def load_features(path: str) -> pd.DataFrame:
    """Load the feature parquet and validate the expected schema."""
    df = pd.read_parquet(path)
    missing = [c for c in META_COLS if c not in df.columns]
    if missing:
        raise ValueError(f"colunas de metadados ausentes: {missing}")
    if df.isna().any().any():
        raise ValueError("parquet contém NaN — investigar antes de treinar")
    return df


def _cols(df, prefixes, feats):
    out = []
    for c in df.columns:
        if "__" not in c:
            continue
        head, feat = c.split("__", 1)
        if head in prefixes and feat in feats:
            out.append(c)
    return out



# ---------------------------------------------------------------------------
# 2. Modelo de custo de aquisição
# ---------------------------------------------------------------------------
# Duas moedas distintas, propositalmente separadas:
#   (a) OPS  — trabalho aritmético por janela no MCU. Totalmente calculável.
#   (b) ENERGIA — dominada pela cadeia analógica (acelerômetro IPEPE/ICP +
#       condicionamento + ADC de alta taxa) e não pela aritmética. Os números
#       abaixo são PARÂMETROS a preencher com datasheet; ficam explícitos para o
#       revisor poder trocar.

OPS_PER_SAMPLE_TIME = 9      # 9 acumuladores nas 9 estatísticas temporais (limite superior)
OPS_MAG = 3                  # |X| por bin: 2 mult + 1 soma (a raiz é 1 op amortizada)
OPS_BANDS = 1                # 1 acumulação por bin para as 3 bandas de energia


def cost_ops(spec: dict, n: int = N_WINDOW, sr_vib: float = 25600.0,
             sr_cur: float = 25600.0) -> float:
    """Operations per window needed to extract the features of a configuration.

    `sr_cur` é parâmetro porque a taxa real da corrente no KAIST ainda precisa
    ser confirmada no data descriptor. Se a corrente for amostrada mais devagar
    que 25,6 kHz, o ramo barato fica AINDA mais barato — ou seja, manter
    sr_cur = sr_vib é a hipótese conservadora contra a nossa própria tese.
    """
    n_cur_eff = max(1, int(round(n * sr_cur / sr_vib)))  # janela equivalente na corrente
    total = 0.0
    for n_ch, nn in ((spec["n_vib"], n), (spec["n_cur"], n_cur_eff)):
        if n_ch == 0:
            continue
        per_ch = OPS_PER_SAMPLE_TIME * nn
        if spec["fft"]:
            # rFFT radix-2: ~5·N·log2(N)/2 flops reais, + magnitude + bandas
            per_ch += 2.5 * nn * np.log2(nn) + (OPS_MAG + OPS_BANDS) * nn / 2
        total += n_ch * per_ch
    # temperatura: média e desvio sobre uma janela lenta — custo desprezível,
    # modelado como 2 ops por canal por janela.
    total += spec["n_tmp"] * 2
    return float(total)


# PARÂMETROS DE ENERGIA — PREENCHER COM DATASHEET ANTES DE PUBLICAR.
# Valores abaixo são placeholders de ordem de grandeza para a estrutura do modelo.
ENERGY_PARAMS = dict(
    p_accel_mw=None,      # potência por acelerômetro ICP + condicionador [mW]
    p_adc_hi_mw=None,     # ADC 25,6 kHz por canal [mW]
    p_ct_mw=None,         # transformador de corrente + condicionamento [mW]
    p_adc_lo_mw=None,     # ADC da corrente [mW]
    p_mcu_active_mw=None, # MCU ativo [mW]
    e_per_op_nj=None,     # energia por operação no MCU [nJ]
)


def cost_energy(spec: dict, params: dict = ENERGY_PARAMS, window_s: float = N_WINDOW / 25600.0):
    """Energy per window [mJ]; None if the parameter dictionary is incomplete."""
    if any(v is None for v in params.values()):
        return None
    p = (spec["n_vib"] * (params["p_accel_mw"] + params["p_adc_hi_mw"])
         + spec["n_cur"] * (params["p_ct_mw"] + params["p_adc_lo_mw"])
         + params["p_mcu_active_mw"])
    e_analog = p * window_s                       # mW·s = mJ
    e_compute = cost_ops(spec) * params["e_per_op_nj"] * 1e-6   # nJ -> mJ
    return e_analog + e_compute


# ---------------------------------------------------------------------------
# 3. Modelos
# ---------------------------------------------------------------------------

def make_model(name: str, seed: int = 0):
    """Three independent classifier families; if they agree on the ORDER of the
    configurations, the conclusion is not an artefact of one learner."""
    if name == "logreg":
        return Pipeline([
            ("sc", StandardScaler()),
            ("clf", LogisticRegression(max_iter=5000, C=1.0, random_state=seed)),
        ])
    if name == "rf":
        return Pipeline([
            ("clf", RandomForestClassifier(n_estimators=300, min_samples_leaf=2,
                                           n_jobs=-1, random_state=seed)),
        ])
    if name == "mlp":
        # max_iter alto + tol apertado: queremos convergência de verdade, e
        # verificamos depois com `check_convergence`.
        return Pipeline([
            ("sc", StandardScaler()),
            ("clf", MLPClassifier(hidden_layer_sizes=(64, 32), alpha=1e-3,
                                  max_iter=3000, tol=1e-5, n_iter_no_change=30,
                                  learning_rate_init=3e-3, random_state=seed)),
        ])
    raise ValueError(name)


MODELS = ["logreg", "rf", "mlp"]


def fit_quiet(model, X, y):
    """Fit while recording convergence warnings instead of ignoring them."""
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always", ConvergenceWarning)
        model.fit(X, y)
        converged = not any(issubclass(wi.category, ConvergenceWarning) for wi in w)
    return model, converged


def predict_proba_full(model, X, n_classes: int) -> np.ndarray:
    """predict_proba re-aligned to the full class space 0..n_classes-1
    (a class may be absent from a training split)."""
    p = model.predict_proba(X)
    classes = model.classes_ if hasattr(model, "classes_") else model[-1].classes_
    out = np.zeros((X.shape[0], n_classes))
    for j, c in enumerate(classes):
        out[:, int(c)] = p[:, j]
    return out


# ---------------------------------------------------------------------------
# 4. Protocolos de validação (sempre agrupados por gravação)
# ---------------------------------------------------------------------------

def splits_grouped(df: pd.DataFrame, n_splits: int = 3, seed: int = 0):
    """Stratified K-fold grouped by recording.

    n_splits=3 é o máximo possível: a classe Normal só tem 3 gravações
    (uma por carga). Repetimos com várias sementes em vez de aumentar K.
    """
    y = df["label"].values
    g = df["recording_id"].values
    sgkf = StratifiedGroupKFold(n_splits=n_splits, shuffle=True, random_state=seed)
    for tr, te in sgkf.split(np.zeros(len(y)), y, g):
        assert not (set(g[tr]) & set(g[te])), "vazamento de gravação entre treino e teste"
        yield tr, te


def splits_lolo(df: pd.DataFrame):
    """Leave-one-operating-point-out: train on all but one load/operating point, test on it.

    É o teste de deslocamento de domínio que um revisor de diagnóstico de falhas
    vai pedir. Também é onde a hipótese de permutabilidade da predição conforme
    é violada de propósito — e queremos MEDIR o quanto a cobertura cai.
    """
    loads = sorted(df["load"].unique())
    idx = np.arange(len(df))
    for L in loads:
        te = idx[df["load"].values == L]
        tr = idx[df["load"].values != L]
        yield tr, te, L


def carve_calibration(df: pd.DataFrame, tr_idx: np.ndarray, frac: float = 0.33,
                      seed: int = 0):
    """Hold out RECORDINGS from the training indices for conformal calibration.

    Estratificado por classe: sorteia uma fração das gravações de cada classe,
    garantindo pelo menos 1 gravação por classe na calibração (Normal só tem
    2 gravações disponíveis no treino — é apertado, e isso é reportado).
    """
    rng = np.random.RandomState(seed)
    sub = df.iloc[tr_idx]
    rec_class = sub.groupby("recording_id")["label"].first()
    cal_recs = []
    for c in sorted(rec_class.unique()):
        recs = rec_class[rec_class == c].index.to_numpy()
        rng.shuffle(recs)
        k = max(1, int(round(frac * len(recs))))
        k = min(k, len(recs) - 1) if len(recs) > 1 else 1   # nunca zera o treino
        cal_recs += list(recs[:k])
    cal_mask = sub["recording_id"].isin(cal_recs).values
    return tr_idx[~cal_mask], tr_idx[cal_mask]


# ---------------------------------------------------------------------------
# 5. Predição conforme split (LAC e APS)
# ---------------------------------------------------------------------------

def conformal_qhat(probs_cal: np.ndarray, y_cal: np.ndarray, alpha: float,
                   score: str = "lac") -> float:
    """Conformal quantile from the calibration set.

    score='lac' (least-ambiguous / THR): s = 1 - p[y_true]. Conjuntos menores.
    score='aps': soma cumulativa das probabilidades ordenadas até a classe
                 verdadeira. Cobertura condicional melhor, conjuntos maiores.

    Usa o quantil de ordem ceil((n+1)(1-alpha))/n — a correção de amostra finita
    que dá a garantia P(y in C(x)) >= 1 - alpha.
    """
    n = len(y_cal)
    if score == "lac":
        s = 1.0 - probs_cal[np.arange(n), y_cal]
    elif score == "aps":
        order = np.argsort(-probs_cal, axis=1)
        sorted_p = np.take_along_axis(probs_cal, order, axis=1)
        cum = np.cumsum(sorted_p, axis=1)
        rank = np.argmax(order == y_cal[:, None], axis=1)
        s = cum[np.arange(n), rank]
    else:
        raise ValueError(score)
    k = int(np.ceil((n + 1) * (1 - alpha)))
    if k > n:
        return 1.0   # n too small for this alpha: the set is the full label space
    return float(np.sort(s)[k - 1])   # the k-th smallest score (1-based), exactly ceil((n+1)(1-alpha))


def conformal_sets(probs: np.ndarray, qhat: float, score: str = "lac") -> np.ndarray:
    """Boolean mask (n_samples, n_classes) with the prediction sets."""
    if score == "lac":
        return (1.0 - probs) <= qhat
    if score == "aps":
        order = np.argsort(-probs, axis=1)
        sorted_p = np.take_along_axis(probs, order, axis=1)
        cum = np.cumsum(sorted_p, axis=1)
        keep_sorted = cum - sorted_p < qhat        # inclui a classe que cruza o limiar
        keep = np.zeros_like(keep_sorted)
        np.put_along_axis(keep, order, keep_sorted, axis=1)
        keep[np.arange(len(probs)), np.argmax(probs, axis=1)] = True  # nunca vazio
        return keep
    raise ValueError(score)


def conformal_metrics(sets: np.ndarray, y: np.ndarray) -> dict:
    cov = sets[np.arange(len(y)), y]
    size = sets.sum(axis=1)
    return dict(coverage=float(cov.mean()),
                avg_size=float(size.mean()),
                singleton_frac=float((size == 1).mean()),
                empty_frac=float((size == 0).mean()))


# ---------------------------------------------------------------------------
# 6. Incerteza: bootstrap de cluster (reamostra GRAVAÇÕES)
# ---------------------------------------------------------------------------

def cluster_bootstrap_ci(y, pred, groups, B: int = 1000, seed: int = 0,
                         stat=lambda a, b: f1_score(a, b, average="macro", zero_division=0)):
    """95 % CI by resampling recordings with replacement (cluster bootstrap).

    A unidade de independência é a GRAVAÇÃO, não a janela: janelas da mesma
    gravação são fortemente correlacionadas e um bootstrap por janela produz
    intervalos artificialmente estreitos (erro comum na literatura de PHM).
    """
    y, pred, groups = np.asarray(y), np.asarray(pred), np.asarray(groups)
    uniq = np.unique(groups)
    idx_by_g = {g: np.where(groups == g)[0] for g in uniq}
    rng = np.random.RandomState(seed)
    stats = []
    for _ in range(B):
        pick = rng.choice(uniq, size=len(uniq), replace=True)
        idx = np.concatenate([idx_by_g[g] for g in pick])
        if len(np.unique(y[idx])) < 2:
            continue
        stats.append(stat(y[idx], pred[idx]))
    lo, hi = np.percentile(stats, [2.5, 97.5])
    return float(np.mean(stats)), float(lo), float(hi)


def macro_f1(y, pred):
    return float(f1_score(y, pred, average="macro", zero_division=0))


def acc(y, pred):
    return float(accuracy_score(y, pred))


def weighted_conformal_qhat(scores: np.ndarray, weights: np.ndarray, alpha: float) -> float:
    """Weighted conformal quantile (Tibshirani et al. 2019; Barber et al. 2023).

    Each calibration score carries a non-negative weight; the quantile is the
    smallest s such that the normalised weight of {scores <= s} plus the weight of
    a hypothetical test point (taken as 1) reaches 1 - alpha.  With all weights
    equal to 1 this reduces to the standard split-conformal quantile.
    """
    scores, weights = np.asarray(scores, float), np.asarray(weights, float)
    order = np.argsort(scores)
    s, w = scores[order], weights[order]
    total = w.sum() + 1.0
    cum = np.cumsum(w) / total
    idx = np.searchsorted(cum, 1 - alpha, side="left")
    return 1.0 if idx >= len(s) else float(s[idx])


def lac_scores(probs: np.ndarray, y: np.ndarray) -> np.ndarray:
    return 1.0 - probs[np.arange(len(y)), y]
