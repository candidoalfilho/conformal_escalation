# Paderborn — resultados (passada rápida: 5 medidas/ponto)

Rodado em 29/set (E1) e 02/out/2026 (E2–E5) com `run_paderborn.py` sobre
`data/paderborn_features.parquet`: **31.266 janelas, 639 gravações, 32 rolamentos,
4 pontos de operação, 4 classes** (Healthy/OR/IR/Both). Mesmo `run_experiments.py`
do KAIST; só os nomes de bloco mudam (`cur2_full`, `vib1_full`, `vib1_time`).
LOLO aqui = leave-one-operating-point-out (4 folds). Comparar com `RESULTS_v2.md`.

## 1. A ordem do KAIST replica — e a corrente ganha um papel novo

Melhor classificador por configuração (macro-F1, agrupado / LOLO):

| configuração | ops/janela | agrupado | LOLO |
|---|---:|---:|---:|
| só temperatura | 4 | 0.374 | 0.288 |
| 1 fase corrente (tempo+FFT) | 167.936 | 0.767 | 0.480 |
| **2 fases corrente (tempo+FFT)** | 335.872 | **0.908** | 0.612 |
| 1 acelerômetro (só tempo) | 36.864 | 0.888 | 0.714 |
| **1 acelerômetro (tempo+FFT)** | 167.936 | **0.959** | **0.762** |
| acel. + 2 fases | 503.808 | 0.991 | 0.768 (rf) / 0.560 (mlp) |

Vibração degrada sob shift (0.959 → 0.762); corrente **colapsa** (0.908 → 0.612 rf,
0.477 mlp); fusão não ajuda sob shift (0.991 → 0.768/0.560). Temperatura é
confundidor de novo (0.374 → 0.288). Tudo igual ao KAIST.

**Diferença que importa**: com 2 fases a 64 kHz a corrente chega a 0.908 agrupado,
quase vibração. No KAIST ela nunca passou de 0.42. Ou seja: a corrente *serve*
enquanto o ponto de operação é o da calibração, e é exatamente aí que a garantia
de "quando confiar nela" tem que valer — e não vale (§3).

**Mas a corrente não é o tier barato nem em ops**: `cur2_full` custa 335.872 ops,
o dobro de `vib1_full` (167.936). Em joules a inversão é maior ainda
(`energy_params.py`: CKSR 15-NP ≈ 82 mW/fase vs IIS3DWB 3,3 mW). A única cascata
que faz sentido no Paderborn é `vib1_time → vib1_full` (4,6× em ops).

## 2. Curva de janelas: plana (E2)

`vib1_full` rf: 0.950 (10 janelas/gravação) → 0.959 (50). Saturado. A objeção
"poucos dados" morre, como no KAIST. O gargalo é o número de pontos de operação,
não de janelas.

## 3. A cobertura conforme colapsa sob mudança de operação — mais forte que no KAIST (E3)

Gap médio (cobertura − nominal), LAC:

| protocolo | KAIST | Paderborn |
|---|---:|---:|
| agrupado | +0.046 | −0.009 (pior −0.038) |
| **LOLO** | **−0.146** (pior −0.453) | **−0.295** (pior −0.501) |

Em α = 0,20 (nominal 80%), LOLO entrega **50,0%** (logreg) e **32,6%** (rf).
KAIST entregava 55,3%. APS fica superconservador (98–99% agrupado; rf LOLO 99,8%
com conjuntos enormes) — não resolve, só esconde.

### ★ Qual fator quebra (o que o KAIST não podia dizer)

Cobertura LAC, α = 0,20, por ponto de operação deixado de fora (cada um muda UM
fator em relação ao baseline N15_M07_F10):

| fator alterado | op testado | logreg | rf |
|---|---|---:|---:|
| **rotação** 1500 → 900 rpm | N09_M07_F10 | **0.329** | **0.013** |
| **torque** 0,7 → 0,1 N·m | N15_M01_F10 | **0.305** | **0.107** |
| força radial 1000 → 400 N | N15_M07_F04 | 0.690 | 0.652 |
| (baseline, treinado nos 3 outros) | N15_M07_F10 | 0.674 | 0.528 |

**Rotação e torque destroem a trocabilidade; força radial quase não.** Faz sentido
físico: rotação desloca as frequências características de falha (features de FFT
mudam de bin), torque muda a assinatura da corrente; força radial muda sobretudo
amplitude. É a frase mais forte do paper.

Detalhe do rf: 62% dos conjuntos sob LOLO ficam **vazios** (`empty_frac` 0.622) —
o quantil LAC calibrado em probabilidades superconfiantes fica minúsculo e, sob
shift, nenhuma classe passa. Conjunto vazio ≠ singleton, então o portão escala;
mas é um sintoma a reportar, não esconder.

## 4. O portão conforme não ganha acurácia (E4) — e sob shift ele *subescala*

Na mesma fração de escalonamento, `vib1_time → vib1_full` (rf, agrupado):
LAC α=0,05 escala 21,9% → F1 0.925 a 73,7 k ops (vs 0.943 a 167,9 k com tudo);
softmax em ~22% → F1 0.926. **Mesma curva**, como no KAIST. O que o conforme
entrega continua sendo a especificação (α), não acurácia.

Sob LOLO o portão **para de escalar quando mais precisava**: LAC α=0,10 escala só
5,3% das janelas e entrega F1 0.717 (vs 0.943 nominal). Conjuntos singleton e
errados: confiante e enganado. É a falha de segurança do mecanismo, dita em uma
linha — e o gancho com o tema "AI for Safety".

## 5. Cinco gravações do alvo restauram; somar à calibração antiga é (quase) inútil (E5)

Gap LAC α=0,20, média sobre os 4 pontos de operação:

| k (gravações do alvo) | só antiga | antiga + nova | **só a nova** |
|---:|---:|---:|---:|
| 0 | −0.458 | — | — |
| 1 | −0.459 | −0.455 | −0.205 |
| 2 | −0.459 | −0.453 | −0.076 |
| 3 | −0.459 | −0.449 | **−0.016** |
| 5 | −0.459 | −0.442 | **+0.011** |
| 8 | −0.459 | −0.435 | +0.008 |

(rf; logreg dá o mesmo desenho: −0.298 → −0.016 em k=3, +0.069 em k=5.)

Replica o KAIST e endurece a conclusão: aqui a calibração antiga tem ~31 mil
janelas e k gravações novas são uma gota — **somar não só é pior do que trocar, é
praticamente não fazer nada** (−0.455 → −0.435 com k=8). Escores obsoletos
dominam o quantil por volume. Por fator: rotação e torque consertam com k = 2–3;
força radial precisa de k = 5 (−0.448 em k=1 → +0.013 em k=5).

## Ressalvas a escrever
1. **Agrupamento por gravação vaza identidade de rolamento**: o mesmo rolamento
   aparece em treino e teste (medidas diferentes). Protocolo mais duro = agrupar
   por rolamento. Afeta os números "agrupado", não os LOLO. Rodar antes do paper
   se der tempo; senão, declarar.
2. Passada rápida (5/20 medidas). Passada completa (`MEAS=20`) só se sobrar tempo;
   a curva de janelas sugere que não muda a ordem.
3. Classe `Both` tem só 3 rolamentos (KB23/24/27); pesa no macro-F1.
4. `splits_shift_by_factor` e `splits_by_damage_origin` (artificial → real) ainda
   não rodaram — o §3 já responde "qual fator" via LOLO; o de dano real é o
   próximo experimento.

## Arquivos
`results_paderborn/{pareto,learning_curve,conformal_coverage,gate,recalibration}.csv`

---

## Adendo 02/out (noite) — experimentos extras (`run_paderborn_extra.py`)

### X2 ★ Qual fator quebra, POR MODALIDADE (cobertura LAC, α=0,20, calibrado só no baseline)

| tier | in-domain | rotação 1500→900 | torque 0,7→0,1 | força radial 1000→400 |
|---|---:|---:|---:|---:|
| 2 fases corrente (logreg / rf) | 0.77 / 0.78 | **0.38 / 0.01** | **0.35 / 0.16** | 0.66 / 0.46 |
| 1 acel. tempo (logreg / rf) | 0.82 / 0.79 | **0.50 / 0.08** | 0.82 / 0.71 | 0.73 / 0.40 |
| 1 acel. tempo+FFT (logreg / rf) | 0.83 / 0.86 | **0.36 / 0.07** | 0.80 / 0.67 | 0.64 / 0.27 |

**A atribuição é específica da modalidade.** Rotação destrói a cobertura em todas as
modalidades. **Torque destrói a corrente e NÃO afeta a vibração** (logreg fica no nominal).
Força radial degrada moderadamente. Isso reconcilia com Panić et al. (RESS 2027) e Alam et
al. (2025), que usam vibração e acham torque inofensivo — o "torque quebra" da §3 era o tier
de corrente, cuja amplitude escala com o torque. Consequência de projeto: cascata
corrente-first recalibra quando rotação OU torque mudam; acelerômetro-first só com rotação.

### X3 Dano artificial → real: o classificador vai pro acaso

Macro-F1 no dano de origem não vista = **0,19–0,29** (acaso p/ 4 classes ≈ 0,25), nas duas
direções, todos os tiers. Não é problema de calibração, é de representação: features manuais
+ modelo raso não transferem entre dano usinado e dano real. Recalibrar com k gravações do
alvo move a cobertura pro nominal só inflando os conjuntos (avg_size → quase todas as
classes), i.e. o portão escalaria tudo. **Delimita a tese**: recalibração no ponto de
implantação restaura a garantia quando o modelo continua informativo lá (shift de operação);
não quando o modelo não serve (shift de origem do dano).

### X1 Agrupado por rolamento — rodando (ver `bearing_pareto.csv` / `bearing_coverage.csv`)

### Correções vindas da revisão de originalidade (`originality_review.md`)
- KAIST (Jung et al. 2023) é **Data in Brief 48:109049**, não Scientific Data.
- LEM CKSR 15-NP: 81,6 mW inclui o termo I_P/N_S a 5 V; sem ele, 75 typ / 105 max — dizer qual.
- Δ conforme − softmax recomputado por interpolação: **+0,000 ± 0,004** (106 pontos) no KAIST.
- Números-manchete de recalibração são **média sobre os 2 classificadores e α ∈ {0,05; 0,1; 0,2; 0,3}**.
- Variante `win` (primeiras m janelas de cada gravação) recupera MENOS que 5 gravações inteiras
  (−0,073 vs +0,002): as primeiras janelas de uma corrida não são permutáveis com o resto.

### X1 (pronto) — agrupado por ROLAMENTO derruba o "agrupado por gravação"
1 acel.+FFT: 0,959 → **0,553** (IC [0,40; 0,67]); 2 fases corrente: 0,908 → 0,458; fusão: 0,991 → 0,504.
Features manuais + modelo raso reconhecem *rolamento*, não *classe de dano* em rolamento novo (Vieira 2025; Kaya & Jobani 2026).
A cobertura conforme NÃO depende disso: com folds e calibração por rolamento, gap LAC +0,002 (corrente) / +0,01 (vibração). A garantia quebra sob shift de operação, não sob rolamento novo. E como o LOLO compartilha rolamentos, o colapso do E3/X2 é atribuível só ao ponto de operação.
→ No paper: números in-distribution = agrupado por rolamento. "Corrente ≈ vibração in-domain" vira "ambas modestas em rolamento novo (0,46–0,53 vs 0,55)".

### E6 (pronto) — conformal ponderado (Barber 2023) como alternativa a descartar
Peso ρ nos escores da fonte (ρ=1 somar, ρ=0 só alvo). KAIST: qualquer ρ ≤ 0,3 recupera quase tudo; em k=1, ρ≈0,1–0,3 é melhor que os dois extremos (estabiliza o quantil). Paderborn: com 31k escores de fonte, ρ=0,3 ainda deixa a fonte mandar; só ρ ≤ 0,03 chega perto do só-alvo → o peso tem que escalar com a razão de tamanhos (o que os pesos por razão de verossimilhança fazem implicitamente). Regra prática: "ponderar pesado" (ρ ≤ 0,1 com k ≥ 2), não "descartar".
