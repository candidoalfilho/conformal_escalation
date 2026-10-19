"""
kaist_lib — dataset adapter for the KAIST rotating-machine dataset
(Jung et al., Data in Brief 48:109049, 2023).

Re-exports the shared library (``cmlib``) and defines the KAIST sensing
configurations.  Usage: ``import kaist_lib as K``.
"""
from cmlib import *            # noqa: F401,F403
from cmlib import _cols        # noqa: F401

CLASSES = ["Normal", "BPFI", "BPFO", "Misalign", "Unbal"]
VIB_CHANNELS = ["xA", "yA", "xB", "yB"]


def feature_blocks(df: pd.DataFrame) -> dict:
    """Sensing configurations that compete on the cost-accuracy frontier (KAIST).

    Cada entrada: (lista_de_colunas, dict de descrição de custo).
    O dict de custo diz quantos canais de cada tipo precisam estar ligados e se
    a FFT é necessária — é dele que sai o custo de aquisição.
    """
    vib_all = [f"vib_{ch}" for ch in VIB_CHANNELS]
    vib_1 = ["vib_xA"]

    B = {}
    B["tmp"] = (
        [c for c in df.columns if c.startswith("tmp_")],
        dict(n_vib=0, n_cur=0, n_tmp=2, fft=False, label="temperature only"),
    )
    B["cur_time"] = (
        _cols(df, ["cur_U"], TIME_FEATS),
        dict(n_vib=0, n_cur=1, n_tmp=0, fft=False, label="current, time-domain"),
    )
    B["cur_full"] = (
        _cols(df, ["cur_U"], TIME_FEATS + FFT_FEATS),
        dict(n_vib=0, n_cur=1, n_tmp=0, fft=True, label="current, time+FFT"),
    )
    B["cur_full_tmp"] = (
        _cols(df, ["cur_U"], TIME_FEATS + FFT_FEATS) + [c for c in df.columns if c.startswith("tmp_")],
        dict(n_vib=0, n_cur=1, n_tmp=2, fft=True, label="current, time+FFT, + temperature"),
    )
    B["vib1_time"] = (
        _cols(df, vib_1, TIME_FEATS),
        dict(n_vib=1, n_cur=0, n_tmp=0, fft=False, label="1 accelerometer, time-domain"),
    )
    B["vib1_full"] = (
        _cols(df, vib_1, TIME_FEATS + FFT_FEATS),
        dict(n_vib=1, n_cur=0, n_tmp=0, fft=True, label="1 accelerometer, time+FFT"),
    )
    B["vib_time"] = (
        _cols(df, vib_all, TIME_FEATS),
        dict(n_vib=4, n_cur=0, n_tmp=0, fft=False, label="4 accelerometers, time-domain"),
    )
    B["vib_full"] = (
        _cols(df, vib_all, TIME_FEATS + FFT_FEATS),
        dict(n_vib=4, n_cur=0, n_tmp=0, fft=True, label="4 accelerometers, time+FFT"),
    )
    B["vib_cur"] = (
        _cols(df, vib_all + ["cur_U"], TIME_FEATS + FFT_FEATS),
        dict(n_vib=4, n_cur=1, n_tmp=0, fft=True, label="4 accelerometers + current"),
    )
    for k, (cols, _) in B.items():
        if not cols:
            raise ValueError(f"bloco {k} ficou vazio — nomes de coluna mudaram?")
    return B


