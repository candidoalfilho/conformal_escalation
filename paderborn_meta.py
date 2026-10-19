"""Metadados do Paderborn KAt bearing dataset (tabelas 6-8 do data descriptor).

Fonte: Lessmeier et al., "Condition Monitoring of Bearing Damage in
Electromechanical Drive Systems by Using Motor Current Signals of Electric
Motors: A Benchmark Data Set for Data-Driven Classification", PHM Europe 2016.
"""

# --- 4 pontos de operação (Tabela 6) -------------------------------------
# Cada um varia UM fator em relação ao baseline N15_M07_F10. Isso é o que
# permite atribuir a quebra de cobertura a um fator específico, em vez de a
# um "load shift" agregado como no KAIST.
OPERATING = {
    "N15_M07_F10": dict(speed_rpm=1500, torque_nm=0.7, force_n=1000),  # baseline
    "N09_M07_F10": dict(speed_rpm= 900, torque_nm=0.7, force_n=1000),  # -rotação
    "N15_M01_F10": dict(speed_rpm=1500, torque_nm=0.1, force_n=1000),  # -torque
    "N15_M07_F04": dict(speed_rpm=1500, torque_nm=0.7, force_n= 400),  # -força radial
}
BASELINE_OP = "N15_M07_F10"

# --- 32 rolamentos (Tabelas 7-9) -----------------------------------------
HEALTHY       = ["K001", "K002", "K003", "K004", "K005", "K006"]
ARTIFICIAL_OR = ["KA01", "KA03", "KA05", "KA06", "KA07", "KA08", "KA09"]
ARTIFICIAL_IR = ["KI01", "KI03", "KI05", "KI07", "KI08"]
REAL_OR       = ["KA04", "KA15", "KA16", "KA22", "KA30"]
REAL_IR       = ["KI04", "KI14", "KI16", "KI17", "KI18", "KI21"]
REAL_BOTH     = ["KB23", "KB24", "KB27"]

CLASSES = ["Healthy", "OR", "IR", "Both"]      # OR = pista externa, IR = interna
CLASS_ID = {c: i for i, c in enumerate(CLASSES)}

def _build():
    m = {}
    for b in HEALTHY:                     m[b] = ("Healthy", "healthy")
    for b in ARTIFICIAL_OR:               m[b] = ("OR",      "artificial")
    for b in ARTIFICIAL_IR:               m[b] = ("IR",      "artificial")
    for b in REAL_OR:                     m[b] = ("OR",      "real")
    for b in REAL_IR:                     m[b] = ("IR",      "real")
    for b in REAL_BOTH:                   m[b] = ("Both",    "real")
    return m

BEARINGS = _build()                       # code -> (classe, origem do dano)
ALL_CODES = sorted(BEARINGS)

# --- aquisição ------------------------------------------------------------
SR_RAW = 64000.0          # vibração e corrente, síncronas
SR_TARGET = 25600.0       # reamostrado p/ bater com o KAIST (64k * 2/5 = 25.6k)
RESAMPLE_UP, RESAMPLE_DOWN = 2, 5

# nomes dos canais dentro do struct Y do .mat -> prefixo no parquet
CHANNEL_MAP = {
    "vibration_1":           ("vib", "A"),
    "phase_current_1":       ("cur", "U"),
    "phase_current_2":       ("cur", "V"),
    "temp_2_bearing_module": ("tmp", "TB"),
}

if __name__ == "__main__":
    from collections import Counter
    assert len(ALL_CODES) == 32, len(ALL_CODES)
    print(f"{len(ALL_CODES)} rolamentos | classes: {Counter(c for c, _ in BEARINGS.values())}")
    print(f"origem: {Counter(o for _, o in BEARINGS.values())}")
    print(f"gravações totais: 32 x {len(OPERATING)} ops x 20 medidas = {32*len(OPERATING)*20}")
