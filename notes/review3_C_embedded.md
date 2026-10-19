# Reviewer C (embedded / TinyML) — round 3, draft 3

## 1. Arithmetic check (Table 1, Sec. 2.3, Sec. 4.6, Table 6)

Every number reproduces from `energy_params.py` with a 0.16 s window: IIS3DWB 3.30 mW → 0.528 mJ; LEM CKSR 15-NP + ADS7042 81.66 mW → 13.07 mJ; TMCS1100 + ADS7042 22.52 mW → 3.60 mJ; TIDA-010249 84.0 mW → 13.44 mJ (double count gone); light sleep 0.792 mW → 0.127 mJ; WAITI 108.57 mW → 17.37 mJ. Ratios 24.7× and 6.8× support "7–25×". Cycles 9×4096 + 34 400 = 71 264; × 543 pJ = 0.0387 mJ; total basis 543 + 108.57 mW/240 MHz = 995 pJ → 0.0709 mJ. Cycle ratio 1.93 and ops ratio 4.56 give "4.6×; 1.9× in cycles". 8.8 µW at one window per minute against 26.4 µW deep sleep is right. Sec. 4.6: 0.33 × 0.528 = 0.174, printed 0.18 from the unrounded escalation fraction (0.331–0.335), consistent with Table 6 (RF, α = 0.05: 33 % / 0.939 in distribution, 53 % / 0.722 under shift; same-sensor RF, α = 0.10: 6 % / 0.890 vs 0.941 always on). The FFT extrapolation reproduces (34 371 cycles).

All round-2 requests are in: MCU acquisition rows, IEPE fixed, total-basis compute, cycles beside ops, in-drive free current with the training caveat, duty-cycle sentence, active-sensing restriction, wake-on-threshold accelerometer named, shared window in Limitations.

## 2. What a node designer would still call wrong

**The light-sleep row prices the sleep, not the wake-ups.** 0.13 mJ is 0.79 mW × 160 ms, i.e. the MCU asleep for the whole window. It is not: the IIS3DWB FIFO (3 kB) must be drained eight times, over SPI whose ceiling on that part is 10 MHz. 4096 × 6 bytes at 10 Mbit/s is about 20 ms per window, 12 % of it, during which the ESP32-S3 is at least at the WAITI floor with SPI DMA running (light sleep gates the peripheral clocks), so the drains alone cost 20 ms × 108.6 mW ≈ 2.1 mJ, plus eight wake-up latencies. The honest "light sleep with FIFO wake-ups" figure is therefore about 2.3 mJ, not 0.13 mJ: four times the sensor row. Three sentences in the paper change as a result. (i) "The front end dominates only once that state is engineered" becomes "even then the MCU state is roughly four times the MEMS sensor; the front end dominates only for the IEPE and current chains." (ii) The free-current cascade saves vibration-acquisition energy (sensor plus MCU state, ≈ 2.8 mJ) times (1 − escalation fraction), which strengthens the cascade claim; Sec. 4.6 should then say "≈ 0.9 mJ of vibration-acquisition energy instead of ≈ 2.8" or at least qualify 0.18/0.53 as the sensor alone. (iii) At one window per minute the MEMS tier averages about 47 µW including the drains, above the 26 µW deep-sleep floor, so the cascade's joules already matter at that rate; the sentence currently says the opposite. One sentence with the 20 ms / ≈ 2 mJ figure fixes all three; the row should carry the corrected value or say "drains excluded". This is the only substantive finding.

**Smaller points.**
- 543 pJ/cycle is the peripheral-clocks-off (Typ1) column of Table 5-9, while `energy_params.py` itself declares Typ2 the honest choice because the node drives SPI. With the ≈ 15 mA Typ1→Typ2 delta the marginal figure is ≈ 750 pJ and the total row ≈ 0.086 mJ. No conclusion moves; say which column.
- "An order of magnitude below" for 0.071 vs 0.53 mJ is 7.4×; write "seven times".
- The TIDA-010249 row uses 3.5 mA × 24 V at the output; the design guide's ≈ 100 mW per channel includes the boost-converter losses the node pays. 100 mW, not 84.
- The WAITI row is at 240 MHz; a node draining a FIFO would run at 80 MHz, where the datasheet floor is markedly lower. Quote that row so the WAITI alternative is not a straw man.
- The dedicated current tier has no FIFO, so its MCU state is the WAITI row (17.4 mJ) on top of the LEM/Hall row; the text states the premise but not the consequence (one clause).
- The 36 864 statistics "cycles" assume one cycle per operation (float divides in kurtosis and the spectral descriptors); priced at the SIMD rate this is harmless.
- Settling is declared excluded; the IIS3DWB turn-on time in a parenthesis would close it.

## 3. Scores

Technical soundness of the embedded/energy content: **4/5**. Usefulness to a node designer: **4/5**.

Separating the paper from 5/5: one thing, the FIFO-drain cost, which turns the 0.13 mJ row into ≈ 2 mJ and reverses the "front end dominates" and "one window per minute" sentences for the MEMS tier; propagate it to Sec. 4.6. The rest is labelling (Typ1 column, 100 mW TIDA, 80 MHz floor) and fits in existing parentheses. The model is otherwise traceable to the part number, which is rare at this venue.
