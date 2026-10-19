#!/usr/bin/env python3
"""Extrai features do Paderborn KAt no MESMO esquema do kaist_features.parquet.

Decisão de projeto: reamostra 64 kHz -> 25,6 kHz (polifásico 2/5, exato) e usa
WINDOW=4096 / HOP=2048, idênticos ao KAIST. Assim `cost_ops` do kaist_lib vale
para os dois datasets sem nenhuma conversão, e as duas tabelas de Pareto ficam
lado a lado no paper.

Uso:
    python extract_paderborn.py --raw ~/Downloads/paderborn --out data/
    python extract_paderborn.py --raw ... --meas-per-setting 20   # passada completa
"""
import argparse, os, re, sys, time
import numpy as np, pandas as pd
from scipy.io import loadmat
from scipy import stats, signal

from paderborn_meta import (OPERATING, BEARINGS, CLASS_ID, CHANNEL_MAP,
                            SR_RAW, SR_TARGET, RESAMPLE_UP, RESAMPLE_DOWN)

WINDOW, HOP, MAXW = 4096, 2048, 50          # iguais ao extract_kaist.py
FNAME_RE = re.compile(r"^(N\d{2}_M\d{2}_F\d{2})_(K[AIB]?\d{2,3})_(\d+)$")

# ---------------------------------------------------------------- features
# Cópia fiel de extract_kaist.py -- qualquer divergência aqui invalida a
# comparação entre datasets, então NÃO "melhore" estas duas funções.
def tfeat(x):
    r = np.sqrt(np.mean(x**2)) + 1e-12; ax = np.abs(x)
    return {'mean': np.mean(x), 'std': np.std(x), 'rms': r, 'p2p': np.ptp(x),
            'kurt': stats.kurtosis(x), 'skew': stats.skew(x),
            'crest': np.max(ax)/r, 'shape': r/(np.mean(ax)+1e-12),
            'impulse': np.max(ax)/(np.mean(ax)+1e-12)}

def ffeat(x, sr):
    n = len(x); fr = np.fft.rfftfreq(n, 1/sr)
    mag = np.abs(np.fft.rfft(x))/(n+1e-12); p = mag**2; tot = p.sum()+1e-12
    pn = p/tot
    f = {'domfreq': fr[np.argmax(mag)], 'centroid': np.sum(fr*p)/tot,
         'entropy': -np.sum(pn[pn > 0]*np.log2(pn[pn > 0]+1e-12))}
    for lo, hi in [(0, 2000), (2000, 6000), (6000, sr/2)]:
        f[f'e{int(lo)}_{int(hi)}'] = p[(fr >= lo) & (fr < hi)].sum()
    return f

# ---------------------------------------------------------------- leitura
def _as_str(v):
    v = _unwrap(v)
    a = np.asarray(v).flat
    return str(a[0]).strip() if a.base is not None or np.asarray(v).size else ""

def _as_1d(v):
    if v is None:
        return None
    v = _unwrap(v)
    a = np.asarray(v).squeeze()
    if a.dtype == object:
        return None
    return a.astype(np.float64) if a.ndim == 1 and a.size > 1 else None

def _unwrap(o):
    """Desembrulha os ndarray(dtype=object) de tamanho 1 que o loadmat cria
    em volta de cada mat_struct."""
    while isinstance(o, np.ndarray) and o.dtype == object and o.size == 1:
        o = o.flat[0]
    return o

def read_mat(path):
    """Devolve {nome_do_canal: array 1-D}. Introspecta o struct em vez de
    assumir a ordem dos campos -- o layout varia entre lotes do dataset."""
    mat = loadmat(path, squeeze_me=False, struct_as_record=False)
    root = [v for k, v in mat.items() if not k.startswith("__")]
    if not root:
        raise ValueError("nenhuma variavel no .mat")
    obj = _unwrap(root[0])
    Y = getattr(obj, "Y", None)
    if Y is None:
        raise ValueError("struct sem campo Y")
    out = {}
    for raw_entry in np.asarray(Y, dtype=object).flat:
        entry = _unwrap(raw_entry)
        name = getattr(entry, "Name", None)
        if name is None:
            continue
        name = _as_str(name)
        if not name:
            continue
        arr = None
        for field in ("Data", "Raw", "Values", "y_values"):
            cand = getattr(entry, field, None)
            if cand is not None:
                arr = _as_1d(cand)
                if arr is not None:
                    break
        if arr is None:                      # fallback: maior vetor do struct
            best = None
            for field in getattr(entry, "_fieldnames", []):
                cand = _as_1d(getattr(entry, field, None))
                if cand is not None and (best is None or cand.size > best.size):
                    best = cand
            arr = best
        if arr is not None:
            out[name] = arr
    return out

def to_target_sr(x):
    """64 kHz -> 25,6 kHz, exato (2/5). Canais lentos (temperatura) passam
    direto: são constantes na escala de uma janela de 160 ms."""
    if x.size < 100:
        return x
    return signal.resample_poly(x, RESAMPLE_UP, RESAMPLE_DOWN).astype(np.float64)

# ---------------------------------------------------------------- extração
def process_file(path, stem, meta_extra):
    op, bearing, meas = FNAME_RE.match(stem).groups()
    cls, origin = BEARINGS[bearing]
    raw = read_mat(path)

    chans = {}
    for src, (kind, ch) in CHANNEL_MAP.items():
        if src not in raw:
            continue
        x = raw[src]
        chans[(kind, ch)] = to_target_sr(x) if kind in ("vib", "cur") else x

    if not any(k == "vib" for k, _ in chans):
        raise ValueError(f"{stem}: sem canal de vibração")

    n_fast = min(v.size for (k, _), v in chans.items() if k in ("vib", "cur"))
    rows, nw = [], 0
    for s in range(0, n_fast - WINDOW, HOP):
        if nw >= MAXW:
            break
        row = {'label': CLASS_ID[cls], 'class': cls, 'load': op,
               'recording_id': stem, 'window_idx': nw,
               'bearing': bearing, 'damage_origin': origin,
               'meas_idx': int(meas), **meta_extra}
        for (kind, ch), x in chans.items():
            if kind == 'tmp':
                seg = x if x.size < 100 else x[s:s+WINDOW]
                row[f'tmp_{ch}__mean'] = float(np.mean(seg))
                row[f'tmp_{ch}__std'] = float(np.std(seg))
                continue
            seg = x[s:s+WINDOW]
            for k, v in tfeat(seg).items():
                row[f'{kind}_{ch}__{k}'] = v
            for k, v in ffeat(seg, SR_TARGET).items():
                row[f'{kind}_{ch}__{k}'] = v
        rows.append(row); nw += 1
    return rows, nw

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", required=True, help="pasta com os .mat (recursivo)")
    ap.add_argument("--out", default="data", help="pasta de saída")
    ap.add_argument("--meas-per-setting", type=int, default=5,
                    help="medidas por (rolamento, op). 5 = passada rápida, 20 = tudo")
    ap.add_argument("--resume", action="store_true")
    a = ap.parse_args()

    os.makedirs(a.out, exist_ok=True)
    parquet = os.path.join(a.out, "paderborn_features.parquet")

    files = []
    for dirpath, _, names in os.walk(a.raw):
        for n in names:
            if not n.lower().endswith(".mat"):
                continue
            stem = n[:-4]
            m = FNAME_RE.match(stem)
            if not m:
                continue
            op, bearing, meas = m.groups()
            if op not in OPERATING or bearing not in BEARINGS:
                continue
            if int(meas) > a.meas_per_setting:
                continue
            files.append((os.path.join(dirpath, n), stem))
    files.sort(key=lambda t: t[1])
    if not files:
        sys.exit(f"nenhum .mat reconhecido em {a.raw} -- confira se o unrar rodou")

    rows, done = [], set()
    if a.resume and os.path.exists(parquet):
        df0 = pd.read_parquet(parquet)
        rows = df0.to_dict("records"); done = set(df0["recording_id"].unique())
        print(f"[resume] {len(done)} gravações já extraídas")

    t0 = time.time(); errs = 0
    for i, (path, stem) in enumerate(files, 1):
        if stem in done:
            continue
        op = FNAME_RE.match(stem).group(1)
        try:
            r, nw = process_file(path, stem, OPERATING[op])
        except Exception as e:
            errs += 1; print(f"ERR {stem}: {repr(e)[:90]}", flush=True); continue
        rows += r; done.add(stem)
        if i % 25 == 0 or i == len(files):
            el = time.time()-t0
            print(f"{i}/{len(files)} · {len(rows)} janelas · {el:5.0f}s "
                  f"· eta {el/max(i,1)*(len(files)-i):5.0f}s", flush=True)

    df = pd.DataFrame(rows)

    # Nem todo lote do Paderborn traz os mesmos canais. Colunas ausentes viram
    # NaN e o kaist_lib recusa NaN de propósito -- então resolvemos aqui, de
    # forma explícita e auditável, em vez de deixar o treino escolher sozinho.
    nan_cols = df.columns[df.isna().any()].tolist()
    if nan_cols:
        bad_rec = df.loc[df[nan_cols].isna().any(axis=1), "recording_id"].nunique()
        frac = bad_rec / max(df.recording_id.nunique(), 1)
        if frac < 0.05:
            print(f"[strict] {bad_rec} gravações incompletas ({frac:.1%}) -> descartadas")
            df = df.dropna(axis=0)
        else:
            print(f"[strict] {len(nan_cols)} colunas ausentes em {frac:.1%} das "
                  f"gravações -> coluna descartada: {nan_cols[:6]}")
            df = df.drop(columns=nan_cols)
        df = df.reset_index(drop=True)

    df.to_parquet(parquet)
    print(f"\nSALVO {parquet}")
    print(f"  {len(df)} janelas · {df.recording_id.nunique()} gravações · {errs} erros")
    print(f"  classes: {df['class'].value_counts().to_dict()}")
    print(f"  ops:     {df['load'].value_counts().to_dict()}")
    print(f"  origem:  {df['damage_origin'].value_counts().to_dict()}")

if __name__ == "__main__":
    main()
