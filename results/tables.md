# Results tables (validation segments: 60, held-out test segments: 90)

## Table V – Locked parameters

| Algorithm | L | Selected μ | Validation ΔSNR (dB) | Rejected μ |
|---|---|---|---|---|
| LMS | 8 | 0.001 | 1.78 | 0.05 |
| LMS | 16 | 0.001 | 1.48 | 0.02, 0.05 |
| LMS | 32 | 0.001 | 0.94 | 0.01, 0.02, 0.05 |
| LMS | 64 | 0.001 | 0.21 | 0.01, 0.02, 0.05 |
| NLMS | 8 | None | – | 0.05, 0.1, 0.25, 0.5, 1.0 |
| NLMS | 16 | None | – | 0.05, 0.1, 0.25, 0.5, 1.0 |
| NLMS | 32 | None | – | 0.05, 0.1, 0.25, 0.5, 1.0 |
| NLMS | 64 | 1.0 | -5.94 | 0.05, 0.1, 0.25, 0.5 |
| PLI branch LMS | 2 weights | 0.005 | 0.36 | none |
| PLI branch NLMS | 2 weights | 0.05 | 0.23 | 1.0 |

## Table VI – Held-out results at 6 dB, 50 Hz (D and E use L = 16)

| Method | ΔSNR (dB) | RMSE (mV) | r | R-peak timing err (ms) | PLI atten. (dB) | Runtime (µs/sample) | MACs/sample |
|---|---|---|---|---|---|---|---|
| Noisy input | 0.00 ± 0.00 | 0.1006 ± 0.0061 | 0.893 ± 0.007 | 1.04 ± 0.42 | 0.0 ± 0.0 | – | – |
| A: 0.5–40 Hz band-pass | -0.16 ± 0.87 | 0.1034 ± 0.0169 | 0.867 ± 0.035 | 1.53 ± 0.46 | 9.3 ± 0.0 | 0.02 | 20 |
| B: 0.5–100 Hz + notch | 0.57 ± 1.02 | 0.0954 ± 0.0176 | 0.887 ± 0.035 | 0.39 ± 0.30 | 38.4 ± 1.4 | 0.05 | 25 |
| C: PLI-only LMS | 0.55 ± 1.03 | 0.0956 ± 0.0177 | 0.887 ± 0.035 | 0.45 ± 0.33 | 31.4 ± 1.4 | 2.56 | 25 |
| C: PLI-only NLMS | 0.43 ± 1.02 | 0.0969 ± 0.0178 | 0.886 ± 0.035 | 0.35 ± 0.30 | 42.6 ± 1.3 | 2.56 | 26 |
| D: motion-only LMS | -1.02 ± 0.57 | 0.1137 ± 0.0129 | 0.843 ± 0.030 | 1.36 ± 0.51 | -0.0 ± 0.0 | 2.93 | 73 |
| E: combined LMS | 1.20 ± 0.91 | 0.0884 ± 0.0137 | 0.899 ± 0.028 | 0.71 ± 0.40 | 31.4 ± 1.4 | 5.43 | 78 |

## Extra – front-end fidelity ceiling (clean ECG alone through the filter, 6 dB / 50 Hz reference)

| Front end | Output SNR vs clean (dB) | r |
|---|---|---|
| A: 0.5–40 Hz | 7.49 | 0.906 |
| 0.5–100 Hz (B, C, D, E) | 8.18 | 0.920 |

## Table VII – ΔSNR (dB) across input SNR and mains frequency

| Method | 0 dB, 50 Hz | 0 dB, 60 Hz | 6 dB, 50 Hz | 6 dB, 60 Hz | 12 dB, 50 Hz | 12 dB, 60 Hz |
|---|---|---|---|---|---|---|
| A | 3.01 | 3.46 | -0.16 | 0.04 | -4.99 | -4.92 |
| B | 3.84 | 3.84 | 0.57 | 0.56 | -4.29 | -4.30 |
| C (best) | 3.81 (C|lms) | 3.80 (C|lms) | 0.55 (C|lms) | 0.54 (C|lms) | -4.30 (C|lms) | -4.32 (C|lms) |
| D (best) | 1.63 (D|lms|8) | 1.65 (D|lms|8) | -0.78 (D|lms|8) | -0.78 (D|lms|8) | -5.08 (D|lms|8) | -5.08 (D|lms|8) |
| E – LMS (best L) | 7.36 (E|lms|8) | 7.34 (E|lms|8) | 1.59 (E|lms|8) | 1.57 (E|lms|8) | -4.35 (E|lms|8) | -4.37 (E|lms|8) |
| E – NLMS (best L) | -0.15 (E|nlms|64) | -0.11 (E|nlms|64) | -6.08 (E|nlms|64) | -6.08 (E|nlms|64) | -12.05 (E|nlms|64) | -12.06 (E|nlms|64) |

## Table VIII – Computational cost

| Method | L | MACs (LMS) | MACs (NLMS) | Runtime µs/sample (median) |
|---|---|---|---|---|
| A | – | 20 | 20 | 0.02 |
| B | – | 25 | 25 | 0.05 |
| C | – | 25 | 26 | 2.56 |
| D | 8 | 57 | 59 | 2.86 |
| D | 16 | 73 | 75 | 2.93 |
| D | 32 | 105 | 107 | 2.92 |
| D | 64 | 169 | 171 | 3.03 |
| E | 8 | 62 | 65 | 5.10 |
| E | 16 | 78 | 81 | 5.43 |
| E | 32 | 110 | 113 | 5.23 |
| E | 64 | 174 | 177 | 5.35 |

## Table X – Validation checks

- Notch 50 Hz: null at 50.00 Hz, −3 dB width 1.67 Hz (expected ≈ 1.67 Hz)
- Notch 60 Hz: null at 60.00 Hz, −3 dB width 2.00 Hz (expected ≈ 2.00 Hz)
- Band-pass A: −3 dB at 0.501 Hz and 40.00 Hz (design [0.5, 40])
- Band-pass B: −3 dB at 0.501 Hz and 100.00 Hz (design [0.5, 100])
- SNR scaling: max |SNR_in − target| = 3.55e-15 dB
- NLMS μ values stable for every L: [1.0]
- LMS stable μ per L: {8: [0.001, 0.005, 0.01, 0.02], 16: [0.001, 0.005, 0.01], 32: [0.001, 0.005], 64: [0.001, 0.005]}

## T1 – em only, Baseline A

| Input SNR | ΔSNR | RMSE | r |
|---|---|---|---|
| 0 dB | 1.62 ± 1.61 | 0.1701 ± 0.0358 | 0.722 ± 0.073 |
| 6 dB | -0.93 ± 1.06 | 0.1134 ± 0.0201 | 0.844 ± 0.042 |
| 12 dB | -5.27 ± 0.89 | 0.0934 ± 0.0156 | 0.889 ± 0.031 |

## T2 – PLI only, Baseline B (6 dB)

| f0 | offset (Hz) | Q | PLI atten. (dB) | ΔSNR | RMSE |
|---|---|---|---|---|---|
| 50 | 0.0 | 20 | 44.6 ± 1.3 | 2.18 ± 1.08 | 0.0792 ± 0.0148 |
| 50 | 0.0 | 30 | 41.5 ± 1.4 | 2.19 ± 1.08 | 0.0791 ± 0.0148 |
| 50 | 0.0 | 40 | 39.5 ± 1.4 | 2.20 ± 1.08 | 0.0790 ± 0.0149 |
| 50 | 0.2 | 20 | 16.0 ± 0.1 | 2.00 ± 1.04 | 0.0808 ± 0.0147 |
| 50 | 0.2 | 30 | 12.6 ± 0.1 | 1.81 ± 1.00 | 0.0825 ± 0.0146 |
| 50 | 0.2 | 40 | 10.3 ± 0.1 | 1.56 ± 0.96 | 0.0848 ± 0.0145 |
| 60 | 0.0 | 20 | 51.8 ± 1.8 | 2.18 ± 1.08 | 0.0791 ± 0.0148 |
| 60 | 0.0 | 30 | 48.6 ± 1.8 | 2.18 ± 1.08 | 0.0792 ± 0.0148 |
| 60 | 0.0 | 40 | 46.5 ± 1.8 | 2.18 ± 1.08 | 0.0792 ± 0.0148 |
| 60 | 0.2 | 20 | 17.6 ± 0.1 | 2.06 ± 1.05 | 0.0803 ± 0.0147 |
| 60 | 0.2 | 30 | 14.2 ± 0.1 | 1.91 ± 1.02 | 0.0816 ± 0.0147 |
| 60 | 0.2 | 40 | 11.8 ± 0.1 | 1.72 ± 0.98 | 0.0833 ± 0.0146 |

## T6 – Reference stress (motion only, D, 6 dB; L used: LMS 16, NLMS 64)

| Condition | LMS ΔSNR | NLMS ΔSNR |
|---|---|---|
| reference gain ×0.1 | -0.08 ± 1.00 | -6.00 ± 0.79 |
| reference gain ×0.316 | 1.24 ± 0.89 | -6.01 ± 0.80 |
| reference gain ×1.0 | 1.14 ± 0.91 | -6.01 ± 0.80 |
| reference gain ×3.16 | -1.21 ± 0.96 | -6.01 ± 0.80 |
| reference gain ×10.0 | unstable | -6.01 ± 0.80 |
| reference correlation ρ = 1.0 | 1.14 ± 0.91 | -6.01 ± 0.80 |
| reference correlation ρ = 0.9 | 1.08 ± 0.90 | -5.92 ± 0.45 |
| reference correlation ρ = 0.7 | 0.94 ± 0.87 | -6.07 ± 0.60 |
| reference correlation ρ = 0.5 | 0.66 ± 0.86 | -6.30 ± 0.43 |
| reference correlation ρ = 0.3 | 0.14 ± 0.91 | unstable |

## Extra – NLMS regulariser sensitivity (E, L = 16; NOT part of the draft protocol, eps = 1e-6 there)

| ε | Rejected μ | Selected μ | Validation ΔSNR | Held-out ΔSNR (6 dB, 50 Hz) | r |
|---|---|---|---|---|---|
| 1e-06 | 0.05, 0.1, 0.25, 0.5, 1.0 | None | – | – | – |
| 0.16 | none | 0.05 | -2.11 | -2.38 ± 0.89 | 0.782 ± 0.044 |
| 1.6 | none | 0.05 | -0.47 | -0.78 ± 0.77 | 0.842 ± 0.034 |

Instability rule: non-finite output, ||w|| > 100, or output power > 2x input power over the final 2 s, in any segment.

Environment: Python 3.10.12, NumPy 2.2.6, SciPy 1.15.3; run time 0.7 min