import os, io, zipfile, time, numpy as np, pandas as pd
from scipy.io import loadmat
from scipy import stats
from nptdms import TdmsFile
B="/sessions/serene-adoring-cray/mnt/Downloads/Vibration, Acoustic, Temperature, and Motor Current Dataset of Rotating Machine Under Varying Load Conditions for Fault Diagnosis"
OUT="/sessions/serene-adoring-cray/mnt/Mestrado/kaist_distill/data"; os.makedirs(OUT,exist_ok=True)
PARQUET=OUT+"/kaist_features.parquet"; WINDOW,HOP,MAXW,BUDGET=4096,2048,50,38
CLASS={'Normal':0,'BPFI':1,'BPFO':2,'Misalign':3,'Unbal':4}
def classify(n):
    for t,l in CLASS.items():
        if t in n: return l,t
    return None,None
def tfeat(x):
    r=np.sqrt(np.mean(x**2))+1e-12; ax=np.abs(x)
    return {'mean':np.mean(x),'std':np.std(x),'rms':r,'p2p':np.ptp(x),'kurt':stats.kurtosis(x),
            'skew':stats.skew(x),'crest':np.max(ax)/r,'shape':r/(np.mean(ax)+1e-12),'impulse':np.max(ax)/(np.mean(ax)+1e-12)}
def ffeat(x,sr):
    n=len(x); fr=np.fft.rfftfreq(n,1/sr); mag=np.abs(np.fft.rfft(x))/(n+1e-12); p=mag**2; tot=p.sum()+1e-12
    pn=p/tot; f={'domfreq':fr[np.argmax(mag)],'centroid':np.sum(fr*p)/tot,'entropy':-np.sum(pn[pn>0]*np.log2(pn[pn>0]+1e-12))}
    for lo,hi in [(0,2000),(2000,6000),(6000,sr/2)]: f[f'e{int(lo)}_{int(hi)}']=p[(fr>=lo)&(fr<hi)].sum()
    return f
def read_vib(z,m): return loadmat(io.BytesIO(z.read(m)))['Signal'][0,0]['y_values'][0,0]['values']
def read_tdms(path):
    g=TdmsFile.read(path)['Log']; cur_u=None; tmp=[]
    for c in g.channels():
        arr=np.asarray(c[:],dtype=np.float64)
        if 'Mod2/ai0' in c.name: cur_u=arr           # U-phase current (present in ALL files)
        elif 'Mod1' in c.name: tmp.append(arr)       # 2 temperatures
    Lt=min(map(len,tmp)); tmp=np.stack([a[:Lt] for a in tmp],1)
    return cur_u.reshape(-1,1), tmp                  # (N,1) current(U), (N,2) temp
VIBCH=['xA','yA','xB','yB']; CURCH=['U']; TMPCH=['TA','TB']; SR=25600
z=zipfile.ZipFile(B+"/vibration.zip"); vmembers=sorted(n for n in z.namelist() if n.lower().endswith('.mat'))
rows=[]; done=set()
if False:  # force fresh re-extract (clean U-only schema)
    df0=pd.read_parquet(PARQUET); rows=df0.to_dict('records'); done=set(df0['recording_id'].unique())
t0=time.time(); new=0
for vm in vmembers:
    base=os.path.basename(vm)[:-4]
    if base in done: continue
    if time.time()-t0>BUDGET: print("[budget] stopping this run",flush=True); break
    lab,tag=classify(base)
    if lab is None: continue
    tdms=os.path.join(B,"current,temp",base.replace('Unbalalnce','Unbalance')+".tdms")
    try:
        V=read_vib(z,vm); C,T=read_tdms(tdms)
    except Exception as e: print("ERR",base,repr(e)[:80],flush=True); continue
    N=min(len(V),len(C),len(T)); nw=0
    for s in range(0,N-WINDOW,HOP):
        if nw>=MAXW: break
        row={'label':lab,'class':tag,'load':base.split('_')[0],'recording_id':base,'window_idx':nw}
        for j,ch in enumerate(VIBCH):
            x=V[s:s+WINDOW,j]
            for k,v in tfeat(x).items(): row[f'vib_{ch}__{k}']=v
            for k,v in ffeat(x,SR).items(): row[f'vib_{ch}__{k}']=v
        for j,ch in enumerate(CURCH):
            x=C[s:s+WINDOW,j]
            for k,v in tfeat(x).items(): row[f'cur_{ch}__{k}']=v
            for k,v in ffeat(x,SR).items(): row[f'cur_{ch}__{k}']=v
        for j,ch in enumerate(TMPCH):
            x=T[s:s+WINDOW,j]; row[f'tmp_{ch}__mean']=np.mean(x); row[f'tmp_{ch}__std']=np.std(x)
        rows.append(row); nw+=1
    done.add(base); new+=1; print(f"+{base}: {nw}w (done {len(done)}/{len(vmembers)})",flush=True)
pd.DataFrame(rows).to_parquet(PARQUET)
print(f"SAVED rows={len(rows)} recordings_done={len(done)}/{len(vmembers)} new_this_run={new}",flush=True)
if len(done)>=len(vmembers): print("ALL DONE",flush=True)
