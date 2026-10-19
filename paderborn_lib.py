"""paderborn_lib — dataset adapter for the Paderborn KAt bearing dataset
(Lessmeier et al., PHM Society European Conference, 2016).

Re-exports the shared library (``cmlib``) and defines what is dataset-specific:
classes, available channels, sensing configurations and the shift splits that
the KAIST data cannot support.  Usage: ``import paderborn_lib as K``.
"""
import numpy as np
import pandas as pd
from cmlib import *                # noqa: F401,F403 -- shared library
import cmlib as _K

from paderborn_meta import CLASSES as PB_CLASSES, OPERATING, BASELINE_OP

# --- o que muda em relação ao KAIST ---------------------------------------
CLASSES = PB_CLASSES                      # Healthy / OR / IR / Both
VIB_CHANNELS = ["A"]                      # 1 acelerômetro (KAIST tinha 4)
CUR_CHANNELS = ["U", "V"]                 # 2 fases (KAIST tinha 1 utilizável)
META_COLS = _K.META_COLS + ["bearing", "damage_origin", "meas_idx",
                            "speed_rpm", "torque_nm", "force_n"]

TIME_FEATS, FFT_FEATS = _K.TIME_FEATS, _K.FFT_FEATS


def load_features(path: str) -> pd.DataFrame:
    df = pd.read_parquet(path)
    missing = [c for c in _K.META_COLS if c not in df.columns]
    if missing:
        raise ValueError(f"colunas de metadados ausentes: {missing}")
    bad = df.columns[df.isna().any()].tolist()
    if bad:
        raise ValueError(f"colunas com NaN: {bad[:8]} — rode o extrator com --strict")
    return df


def feature_blocks(df: pd.DataFrame) -> dict:
    """Mesma lógica do KAIST, adaptada aos canais do Paderborn.

    A pergunta central muda de "quantos acelerômetros?" para "corrente basta?",
    que é exatamente onde o KAIST foi inconclusivo (0.417 -> 0.213 sob LOLO).
    Aqui a corrente tem 2 fases a 64 kHz e 2560 gravações para se defender.
    """
    cur_1 = ["cur_U"]
    cur_2 = ["cur_U", "cur_V"]
    vib_1 = ["vib_A"]
    tmp_cols = [c for c in df.columns if c.startswith("tmp_")]

    B = {}
    if tmp_cols:
        B["tmp"] = (tmp_cols,
                    dict(n_vib=0, n_cur=0, n_tmp=1, fft=False, label="temperature only"))
    B["cur1_time"] = (_cols(df, cur_1, TIME_FEATS),
                      dict(n_vib=0, n_cur=1, n_tmp=0, fft=False, label="1 current phase, time-domain"))
    B["cur1_full"] = (_cols(df, cur_1, TIME_FEATS + FFT_FEATS),
                      dict(n_vib=0, n_cur=1, n_tmp=0, fft=True, label="1 current phase, time+FFT"))
    B["cur2_time"] = (_cols(df, cur_2, TIME_FEATS),
                      dict(n_vib=0, n_cur=2, n_tmp=0, fft=False, label="2 current phases, time-domain"))
    B["cur2_full"] = (_cols(df, cur_2, TIME_FEATS + FFT_FEATS),
                      dict(n_vib=0, n_cur=2, n_tmp=0, fft=True, label="2 current phases, time+FFT"))
    B["vib1_time"] = (_cols(df, vib_1, TIME_FEATS),
                      dict(n_vib=1, n_cur=0, n_tmp=0, fft=False, label="1 accelerometer, time-domain"))
    B["vib1_full"] = (_cols(df, vib_1, TIME_FEATS + FFT_FEATS),
                      dict(n_vib=1, n_cur=0, n_tmp=0, fft=True, label="1 accelerometer, time+FFT"))
    B["vib_cur"] = (_cols(df, vib_1 + cur_2, TIME_FEATS + FFT_FEATS),
                    dict(n_vib=1, n_cur=2, n_tmp=0, fft=True, label="1 accelerometer + 2 current phases"))
    for k, (cols, _) in B.items():
        if not cols:
            raise ValueError(f"bloco {k} ficou vazio — nomes de coluna mudaram?")
    return B


# --- o ganho científico sobre o KAIST -------------------------------------
def splits_shift_by_factor(df: pd.DataFrame):
    """Treina no ponto de operação BASELINE e testa em cada um dos outros três.

    Cada alvo difere do baseline em UM fator (rotação, torque ou força radial).
    É isto que o KAIST não permitia: lá as três cargas variavam junto e a quebra
    de cobertura só podia ser atribuída a "mudança de operação" em bloco.
    Aqui o paper passa a dizer QUAL fator quebra a trocabilidade.
    """
    idx = np.arange(len(df))
    op = df["load"].values
    tr = idx[op == BASELINE_OP]
    if not len(tr):
        raise ValueError(f"baseline {BASELINE_OP} ausente do parquet")
    base = OPERATING[BASELINE_OP]
    for target, params in OPERATING.items():
        if target == BASELINE_OP:
            continue
        changed = [k for k in ("speed_rpm", "torque_nm", "force_n")
                   if params[k] != base[k]]
        te = idx[op == target]
        if len(te):
            yield tr, te, {"target_op": target, "factor": "+".join(changed),
                           **{k: params[k] for k in changed}}


def splits_by_damage_origin(df: pd.DataFrame):
    """Treina em dano artificial, testa em dano real (e vice-versa).

    Segundo eixo de trocabilidade que o KAIST não tem: 12 rolamentos com dano
    usinado vs 14 com dano de ensaio de vida acelerado. Se a cobertura conforme
    quebrar aqui, é o achado mais transferível do paper — todo mundo treina em
    dano artificial e implanta em dano real.
    """
    idx = np.arange(len(df))
    org = df["damage_origin"].values
    art = idx[np.isin(org, ["artificial", "healthy"])]
    real = idx[np.isin(org, ["real", "healthy"])]
    if len(art) and len(real):
        yield art, idx[org == "real"], {"train": "artificial", "test": "real"}
        yield real, idx[org == "artificial"], {"train": "real", "test": "artificial"}


_cols = _K._cols
