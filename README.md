# Conformal sensor escalation under operating-point shift

Code and analysis for *Calibrate Where You Deploy: Conformal Sensor Escalation Under Operating-Point Shift*
(target: IFAC SAFEPROCESS 2027). Two public datasets, one pipeline.

## Layout

| path | content |
|---|---|
| `cmlib.py` | shared library: cost model (operations, energy), classifiers with convergence check, recording-grouped validation protocols, split conformal prediction (LAC, APS, weighted), cluster bootstrap |
| `kaist_lib.py`, `paderborn_lib.py`, `paderborn_meta.py` | dataset adapters (sensing configurations, classes, operating points) |
| `extract_kaist.py`, `extract_paderborn.py`, `paderborn_colab.ipynb` | feature extraction (raw signals → `data/*.parquet`); the Colab notebook streams the Paderborn archives |
| `run_experiments.py --dataset {kaist,paderborn} [e1 … e6]` | E1 cost–accuracy frontier · E2 learning curve · E3 conformal coverage · E4 escalation gate vs threshold gate · E5 recalibration at the target operating point · E6 weighted conformal prediction |
| `run_paderborn_extra.py [x1 x2 x3]` | X1 bearing-grouped validation · X2 coverage by shifted factor and modality · X3 artificial ↔ real damage transfer |
| `energy_params.py` | datasheet-derived power figures (MEMS vs current transducer vs IEPE chain, ESP32-S3) |
| `report_lib.py`, `build_notebooks.py` | figures/tables from the CSVs; generator of the two analysis notebooks |
| `01_kaist_conformal_gate.ipynb`, `02_paderborn_replication.ipynb` | executed analysis notebooks (read `results*/`, write `figs_en/`) |
| `results/`, `results_paderborn/` | experiment outputs (CSV) |
| `figs_en/` | figures (PNG + PDF) |
| `paper/` | manuscript: `main_ifac.tex` (IFAC class), `refs_ifac.bib`, `make_tables_ifac.py` → `tables_ifac/` and `numbers_ifac.tex` |
| `notes/` | working notes and the prior-art review |
| `legacy/` | earlier (Portuguese) notebooks and notes, kept for provenance |

## Run the notebooks on Google Colab

Each notebook starts with a setup cell that clones this repository and installs the dependencies when it is not already running inside the repository, so it can be opened directly from GitHub in Colab (File → Open notebook → GitHub, or the badges below once the repository is public). Nothing is recomputed: the notebooks read the CSVs in `results*/` and regenerate every table and figure.

- `01_kaist_conformal_gate.ipynb` — KAIST: frontier, learning curve, coverage, gate, recalibration, weighted conformal prediction
- `02_paderborn_replication.ipynb` — Paderborn: replication, bearing-grouped validation, factor-by-modality attribution, artificial↔real transfer

## Reproduce

```bash
pip install -r requirements.txt
python run_experiments.py --dataset kaist          # ~3 min (2 CPUs)
python run_experiments.py --dataset paderborn      # ~25 min
python run_paderborn_extra.py                      # ~20 min (X1 dominates)
python build_notebooks.py && jupyter nbconvert --to notebook --execute --inplace 0*.ipynb
python paper/make_tables_ifac.py && (cd paper && pdflatex main_ifac && bibtex main_ifac && pdflatex main_ifac && pdflatex main_ifac)
```

All experiments are seeded (`SEEDS = [0, 1, 2]`, five seeds for recalibration) and run on CPU; a full rerun
takes under an hour on a free Colab instance. To check that a rerun reproduces the manuscript, regenerate the
tables and compare the headline macros: `python paper/make_tables_ifac.py && git diff --stat paper/numbers_ifac.tex paper/tables_ifac/`
(no diff means every number in the paper reproduced; differences in the third decimal can arise from
BLAS/threading nondeterminism in the random forest and do not change any conclusion).

Before publishing a fork, set `REPO_URL` in `build_notebooks.py` (first code cell of both notebooks) to the
repository's own URL and rebuild the notebooks.

`data/kaist_features.parquet` is derived from Jung et al. (Data in Brief 48:109049, 2023);
`data/paderborn_features.parquet` from the Paderborn KAt bearing data centre (Lessmeier et al., PHME 2016), quick pass (5 of 20 measurements per setting).
