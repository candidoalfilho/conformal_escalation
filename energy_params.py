"""Energy model — datasheet-derived parameters, all traceable.

Every figure here carries a part number, the datasheet column it comes from
(typical / maximum), the test condition and a URL.  Nothing is estimated; what
has no datasheet figure is declared as a range (``SWEEP``), not as a point.

Usage::

    import energy_params as E
    import cmlib as C
    C.ENERGY_PARAMS = E.deploy_mems()   # deployable node: ESP32-S3 + digital MEMS + isolated current transducer
    C.ENERGY_PARAMS = E.lab_iepe()      # laboratory chain: IEPE accelerometer + mains-powered conditioner

Headline: a dedicated isolated current transducer draws roughly 25x the power
of a three-axis MEMS accelerometer per phase (~50x for two phases), so the
"cheap current -> expensive vibration" cascade is inverted when the currency is
energy rather than operations.  This holds for a dedicated transducer; a drive
inverter that already samples phase current for control delivers that signal at
near-zero marginal energy, and the two scenarios must not be confused.
"""
import numpy as np

# --- vibration sensors --------------------------------------------------------
IIS3DWB = dict(          # ST, digital MEMS, ODR 26.667 kHz, 3 axes
    p_mw=1.1 * 3.0,      # 1.1 mA typ @ Vdd = 3.0 V, T = 25 C, ODR = 26.667 kHz
    note="integrated ADC; no external converter needed",
    cond="typ; Table 4, Vdd = 3.0 V, T = 25 C ('typical specifications are not guaranteed')",
    url="https://www.st.com/resource/en/datasheet/iis3dwb.pdf")
# 26.7 kHz is the output data rate, NOT the bandwidth: the analogue bandwidth is
# dc-6 kHz (+-3 dB).  At 25.6 kHz sampling the device is ~4x oversampled relative
# to its own passband, so no external anti-aliasing filter is required.

ADXL1002 = dict(         # ADI, analogue MEMS, 11 kHz bandwidth (-3 dB)
    p_mw=1.0 * 5.0,      # 1.0 mA typ @ VDD = 5.0 V, TA = 25 C, 0 g
    note="analogue output; requires external ADC and buffer (add ADS8860)",
    cond="typ; header 'TA = 25 C, VDD = 5.0 V, acceleration = 0 g'",
    url="https://www.analog.com/media/en/technical-documentation/data-sheets/adxl1001-1002.pdf")

PCB_352C33 = dict(       # ICP/IEPE piezoelectric accelerometer, sensor only
    p_mw=4.0 * 24.0,     # typical operating point 4 mA / 24 V within the 2-20 mA / 18-30 V excitation range
    cond="excitation range from spec sheet Rev H; 4 mA / 24 V is the chosen operating point",
    url="https://www.pcb.com/contentstore/docs/pcb_corporate/vibration/products/specsheets/352c33_h.pdf")

KISTLER_5015A = dict(    # bench conditioner, one channel, mains powered
    p_mw=20_000.0,       # ~20 VA
    note="used by the Paderborn testbed (charge amplifier, not IEPE)",
    cond="'Consumption ~20 VA', 115/230 V~",
    url="https://intertechnology.com/Kistler/pdfs/ACC_5015A_Charge_Meter.pdf")

TIDA_010249 = dict(      # modern integrated IEPE front end; the fair comparison for a field node
    p_mw=100.0,          # ~100 mW per channel including boost-converter losses (3.5 mA @ 23-24 V at the sensor alone = 84 mW)
    note="cited alongside the Kistler conditioner so that the laboratory chain is not a straw man",
    cond="Table 1-1 Key System Specs; ~100 mW per channel including boost losses",
    url="https://www.ti.com/lit/ug/tiduf13/tiduf13.pdf")

# --- ADCs ----------------------------------------------------------------------
# The ESP32-S3 internal ADC has no published power figure in any datasheet
# revision (it is absorbed in the Typ2 column of Table 5-9), and with DNL +-4 LSB,
# INL +-8 LSB and a 100 kSPS ceiling it is not vibration grade.  The model uses an
# external converter and says so.
ADS8860 = dict(          # TI, 16 bit, 1 MSPS -- vibration channel
    p_mw_at=lambda sps: 5.5 * (sps / 1e6),   # linear in sample rate, as stated by TI
    cond="typ @ AVDD = 3 V; 1 MSPS = 5.5 mW, 100 kSPS = 0.55 mW, 10 kSPS = 55 uW (exactly linear)",
    url="https://www.ti.com/lit/ds/symlink/ads8860.pdf")
ADS7042 = dict(          # TI, 12 bit, ultra-low-power -- slow channel
    p_mw_at=lambda sps: 0.690 * (sps / 1e6),
    cond="MAX @ AVDD = 3 V (TI's 3 V bullets are maxima, the 1.8 V bullets are typicals)",
    url="https://www.ti.com/lit/ds/symlink/ads7042.pdf")

# --- current sensing ------------------------------------------------------------
LEM_CKSR_15NP = dict(    # used by the Paderborn testbed, per phase
    p_mw=(15.0 + 2300.0 / 1731.0) * 5.0,   # I_C = 15 mA + I_P/N_S at 5 V; 425 W PMSM, I_P = 2.3 A, N_S = 1731
    cond="typ; header 'TA = 25 C, VC = +5 V, NP = 1 turn, RL = 10 k, internal reference'; "
         "without the I_P/N_S term: 75 mW typ / 105 mW max",
    url="https://www.lem.com/en/product-list/cksr-15np")
TMCS1100 = dict(         # TI Hall sensor, low-cost alternative
    p_mw=4.5 * 5.0,      # 4.5 mA typ @ VS = 5 V, TA = 25 C
    cond="typ; section 6.9 'at TA = 25 C, VS = 5 V, VREF = 2.5 V'",
    url="https://www.ti.com/lit/ds/symlink/tmcs1100.pdf")
ACS712 = dict(
    p_mw=10.0 * 5.0,     # 10 mA typ @ VCC = 5 V (more than the TMCS1100)
    cond="typ; 'over full range of TA, CF = 1 nF, VCC = 5 V'",
    url="https://www.allegromicro.com/-/media/files/datasheets/acs712-datasheet.ashx")

# --- MCU -------------------------------------------------------------------------
# ESP32-S3 datasheet Table 5-9, MODEM-SLEEP (radio clock-gated).  Tables 5-7/5-8
# (283-340 mA) are RF transmit peaks and are irrelevant here.  Measured at 3.3 V,
# 25 C.  Typ1 = peripheral clocks off; Typ2 = peripheral clocks on.  The node
# drives SPI, so Typ2 is the honest choice for the compute phase.
ESP32S3 = dict(
    p_active_mw_typ1=66.2 * 3.3,    # dual core, 32-bit, peripheral clocks off
    p_active_mw_typ2=81.3 * 3.3,    # dual core, 32-bit, peripheral clocks on  <- used
    p_simd_mw_typ1=91.7 * 3.3,      # dual core, 128-bit SIMD
    p_waiti_mw=32.9 * 3.3,          # idle floor (WAITI)
    p_lightsleep_mw=0.240 * 3.3,
    p_deepsleep_mw=0.008 * 3.3,
    p_flash_mw=10.0 * 3.3,          # add only if code executes from flash rather than IRAM
    coremark=1329.92, coremark_per_mhz=5.54, f_mhz=240,
    cond="Table 5-9, Modem-sleep, 240 MHz, 3.3 V, 25 C",
    url="https://documentation.espressif.com/esp32-s3_datasheet_en.pdf")

# --- MCU during acquisition ------------------------------------------------------------
# The IIS3DWB FIFO holds 3 kB, about 1/8 of a 4096-sample three-axis 16-bit window
# (24 576 bytes), so the MCU wakes about eight times per window to drain it over SPI
# (10 MHz max for this device).  The current ADC (ADS7042) has no FIFO at all, so the
# MCU idles (WAITI) for the whole window on that tier.
IIS3DWB_FIFO_BYTES = 3_072
WINDOW_BYTES_3AXIS = 4096 * 3 * 2
SPI_MHZ = 10.0
FIFO_DRAIN_S = WINDOW_BYTES_3AXIS * 8 / (SPI_MHZ * 1e6)      # ~19.7 ms of bus time per window
FIFO_WAKEUPS = int(np.ceil(WINDOW_BYTES_3AXIS / IIS3DWB_FIFO_BYTES))   # 8


def mcu_acquisition_mj(window_s=4096 / 25600):
    """ESP32-S3 energy during one MEMS window: light sleep plus FIFO drains at the WAITI floor."""
    sleep = ESP32S3["p_lightsleep_mw"] * (window_s - FIFO_DRAIN_S)
    drain = ESP32S3["p_waiti_mw"] * FIFO_DRAIN_S
    return sleep + drain


# --- energy per CYCLE (not per operation) -----------------------------------------
# No vendor publishes nJ per operation (Espressif, Arm and EEMBC included; ULPMark
# is iterations per millijoule, and an iteration is not an operation).  What is
# traceable is pJ per cycle from the datasheet times the cycle counts Espressif
# publishes for its DSP kernels.
#
# pJ per core-cycle, MARGINAL over the WAITI floor (isolates switching from static):
PJ_PER_CORE_CYCLE = dict(
    single_32bit=252.0, dual_32bit=229.0,
    single_simd128=543.0, dual_simd128=404.0,
)
# On a TOTAL-power basis (what a duty-cycled node actually pays):
PJ_PER_CORE_CYCLE_TOTAL = dict(single_32bit=704.0, dual_32bit=455.0)

# Cycle counts measured by Espressif (ESP-DSP, optimised assembly, -O2, ESP32-S3):
ESP_DSP_CYCLES = {
    "fft2r_sc16_1024": 15_623,     # 16-bit fixed-point FFT, 1024 complex points
    "fft2r_sc16_512":   7_294,
    "fft4r_fc32_1024": 64_482,     # float radix-4
    "fft2r_fc32_1024": 97_847,     # float radix-2
    "dotprod_f32_256":     432,
}
ESP_DSP_URL = "https://docs.espressif.com/projects/esp-dsp/en/latest/esp32/esp-dsp-benchmarks.html"
# Espressif's table stops at 1024 complex points.  A 4096-sample real window is
# 2048 complex points; N log N extrapolation gives ~34 400 cycles.  This is the
# one derived quantity in the model: a CCOUNT reading on the board replaces it.
FFT_4096_CYCLES_EXTRAPOLATED = 34_400   # to be measured, not cited


def fft_energy_uj(cycles=FFT_4096_CYCLES_EXTRAPOLATED, mode="single_simd128"):
    """Marginal energy of one FFT, in microjoules (cycles x pJ per cycle)."""
    return cycles * PJ_PER_CORE_CYCLE[mode] * 1e-6


# --- the two scenarios --------------------------------------------------------------
def deploy_mems(current_sensor=LEM_CKSR_15NP):
    """Deployable node: ESP32-S3 + digital MEMS accelerometer + isolated current transducer."""
    return dict(
        p_accel_mw=IIS3DWB["p_mw"],
        p_adc_hi_mw=0.0,                       # the IIS3DWB converts internally
        p_ct_mw=current_sensor["p_mw"],
        p_adc_lo_mw=ADS7042["p_mw_at"](25_600),
        p_mcu_active_mw=ESP32S3["p_active_mw_typ2"],
        e_per_op_nj=None,                      # see above: report pJ per cycle instead
    )


def lab_iepe():
    """Laboratory chain as in the KAIST / Paderborn testbeds: IEPE sensor + mains-powered conditioner."""
    return dict(
        p_accel_mw=PCB_352C33["p_mw"] + KISTLER_5015A["p_mw"],
        p_adc_hi_mw=ADS8860["p_mw_at"](25_600),
        p_ct_mw=LEM_CKSR_15NP["p_mw"],
        p_adc_lo_mw=ADS7042["p_mw_at"](25_600),
        p_mcu_active_mw=ESP32S3["p_active_mw_typ2"],
        e_per_op_nj=None,
    )


# --- declared range instead of a point ----------------------------------------------
SWEEP = dict(
    pj_per_core_cycle=(229.0, 404.0),   # Typ1 <-> Typ2 band (peripheral clocks)
    note="the band is itself a result: the peripheral configuration weighs as much as the arithmetic",
)

if __name__ == "__main__":
    for name, params in [("deployable node (MEMS)", deploy_mems()), ("laboratory chain (IEPE)", lab_iepe())]:
        print(f"\n{name}:")
        for k, v in params.items():
            print(f"  {k:20} {v if v is None else f'{v:10.3f} mW'}")
    d = deploy_mems()
    r = d["p_ct_mw"] / d["p_accel_mw"]
    print(f"\ncurrent / accelerometer power ratio: {r:.0f}x per phase, {2*r:.0f}x for the two Paderborn phases")
    print(f"laboratory / deployable vibration chain: {lab_iepe()['p_accel_mw']/d['p_accel_mw']:.0f}x")
    print(f"FFT 4096 (extrapolated cycles, SIMD): {fft_energy_uj():.1f} uJ")
