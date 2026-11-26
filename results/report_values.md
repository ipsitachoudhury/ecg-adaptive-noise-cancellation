# Values for the report placeholders

## Sec. 8.3 - environment
- Python 3.10.12, NumPy 2.2.6, SciPy 1.15.3, Matplotlib 3.10.9, WFDB 4.3.1
- OS: Linux-6.8.0-149-generic-aarch64-with-glibc2.35
- Processor: aarch64 (aarch64)
- Results file produced with: Python 3.10.12, NumPy 2.2.6, SciPy 1.15.3; full run time 43 s

## Sec. 6.2 / Table III / App. B - dataset log
- Validation: record 100, channel 0 (MLII), fs = 360 Hz; window 0-600 s; 60 segments of 10 s used (0 excluded by annotation check); first start 0 samples (0 s), last start 212400 samples (590 s), step 3600 samples; 760 annotated beats
- Held-out test: record 100, channel 0 (MLII), fs = 360 Hz; window 900-1806 s; 90 segments of 10 s used (0 excluded by annotation check); first start 324000 samples (900 s), last start 644400 samples (1790 s), step 3600 samples; 1124 annotated beats
- Segment starts are every 3600 samples; segment k covers samples [start, start + 3600).
- Random seed per mixture: numpy default_rng([2026, record, start_sample, round(10*SNR_dB), f0]) - the same noisy realisation is given to every method.
- Transient exclusion: first 360 samples (1 s) of every output; delay alignment searched over 0-40 samples.

## App. B - noise settings
- PLI-to-motion power ratio 0 dB (equal power): g_m = 0.7071, g_p = 0.7071 in eq. (1)
- PLI: unit-RMS sinusoid sqrt(2)*sin(2*pi*f0*n/Fs + phi), phi ~ Uniform[0, 2*pi) drawn per mixture; no harmonics, no amplitude modulation; f0 = 50 Hz (primary) and 60 Hz; T2 also uses a +0.2 Hz offset
- em: NSTDB record 'em', channel 0, excerpt starts at the same sample index as the ECG segment (index mod 646400); mean removed and scaled to unit RMS; the same unit-RMS excerpt is the motion reference
- 0 dB: measured SNR_in over the full segment = 0.000000 dB (max |error| 1.9e-15 dB) over 90 held-out segments
- 6 dB: measured SNR_in over the full segment = 6.000000 dB (max |error| 2.7e-15 dB) over 90 held-out segments
- 12 dB: measured SNR_in over the full segment = 12.000000 dB (max |error| 3.6e-15 dB) over 90 held-out segments

## App. B - full parameter sweep (validation, 50 Hz, mean ΔSNR over 0/6/12 dB)
| Branch | Algorithm | L | μ | Stable (rule) | Validation ΔSNR (dB) | Selected |
|---|---|---|---|---|---|---|
| PLI (C) | LMS | 2 weights | 0.001 | yes | 0.14 |  |
| PLI (C) | LMS | 2 weights | 0.005 | yes | 0.36 | yes |
| PLI (C) | LMS | 2 weights | 0.01 | yes | 0.33 |  |
| PLI (C) | LMS | 2 weights | 0.02 | yes | 0.26 |  |
| PLI (C) | LMS | 2 weights | 0.05 | yes | 0.02 |  |
| PLI (C) | NLMS | 2 weights | 0.05 | yes | 0.23 | yes |
| PLI (C) | NLMS | 2 weights | 0.1 | yes | 0.02 |  |
| PLI (C) | NLMS | 2 weights | 0.25 | yes | -0.88 |  |
| PLI (C) | NLMS | 2 weights | 0.5 | yes | -2.25 |  |
| PLI (C) | NLMS | 2 weights | 1.0 | no | -6.13 |  |
| Motion (E) | LMS | 8 | 0.001 | yes | 1.78 | yes |
| Motion (E) | LMS | 8 | 0.005 | yes | 0.92 |  |
| Motion (E) | LMS | 8 | 0.01 | yes | 0.10 |  |
| Motion (E) | LMS | 8 | 0.02 | yes | -0.83 |  |
| Motion (E) | LMS | 8 | 0.05 | no | – (rejected) |  |
| Motion (E) | LMS | 16 | 0.001 | yes | 1.48 | yes |
| Motion (E) | LMS | 16 | 0.005 | yes | 0.05 |  |
| Motion (E) | LMS | 16 | 0.01 | yes | -0.87 |  |
| Motion (E) | LMS | 16 | 0.02 | no | – (rejected) |  |
| Motion (E) | LMS | 16 | 0.05 | no | – (rejected) |  |
| Motion (E) | LMS | 32 | 0.001 | yes | 0.94 | yes |
| Motion (E) | LMS | 32 | 0.005 | yes | -0.94 |  |
| Motion (E) | LMS | 32 | 0.01 | no | – (rejected) |  |
| Motion (E) | LMS | 32 | 0.02 | no | – (rejected) |  |
| Motion (E) | LMS | 32 | 0.05 | no | – (rejected) |  |
| Motion (E) | LMS | 64 | 0.001 | yes | 0.21 | yes |
| Motion (E) | LMS | 64 | 0.005 | yes | -1.98 |  |
| Motion (E) | LMS | 64 | 0.01 | no | – (rejected) |  |
| Motion (E) | LMS | 64 | 0.02 | no | – (rejected) |  |
| Motion (E) | LMS | 64 | 0.05 | no | – (rejected) |  |
| Motion (E) | NLMS | 8 | 0.05 | no | – (rejected) |  |
| Motion (E) | NLMS | 8 | 0.1 | no | – (rejected) |  |
| Motion (E) | NLMS | 8 | 0.25 | no | – (rejected) |  |
| Motion (E) | NLMS | 8 | 0.5 | no | – (rejected) |  |
| Motion (E) | NLMS | 8 | 1.0 | no | – (rejected) |  |
| Motion (E) | NLMS | 16 | 0.05 | no | – (rejected) |  |
| Motion (E) | NLMS | 16 | 0.1 | no | – (rejected) |  |
| Motion (E) | NLMS | 16 | 0.25 | no | – (rejected) |  |
| Motion (E) | NLMS | 16 | 0.5 | no | – (rejected) |  |
| Motion (E) | NLMS | 16 | 1.0 | no | – (rejected) |  |
| Motion (E) | NLMS | 32 | 0.05 | no | – (rejected) |  |
| Motion (E) | NLMS | 32 | 0.1 | no | – (rejected) |  |
| Motion (E) | NLMS | 32 | 0.25 | no | – (rejected) |  |
| Motion (E) | NLMS | 32 | 0.5 | no | – (rejected) |  |
| Motion (E) | NLMS | 32 | 1.0 | no | – (rejected) |  |
| Motion (E) | NLMS | 64 | 0.05 | no | – (rejected) |  |
| Motion (E) | NLMS | 64 | 0.1 | no | – (rejected) |  |
| Motion (E) | NLMS | 64 | 0.25 | no | – (rejected) |  |
| Motion (E) | NLMS | 64 | 0.5 | no | – (rejected) |  |
| Motion (E) | NLMS | 64 | 1.0 | yes | -5.94 | yes |

## App. B - filter specifications and SOS coefficients (each row: b0 b1 b2 a0 a1 a2)
- Baseline A: Butterworth band-pass 0.5-40 Hz, 4th-order prototype (8th-order band-pass):
    +6.6048756713e-03  +1.3209751343e-02  +6.6048756713e-03  +1.0000000000e+00  -9.7894906924e-01  +2.6401065276e-01
    +1.0000000000e+00  +2.0000000000e+00  +1.0000000000e+00  +1.0000000000e+00  -1.2374771035e+00  +6.1247881993e-01
    +1.0000000000e+00  -2.0000000000e+00  +1.0000000000e+00  +1.0000000000e+00  -1.9836536735e+00  +9.8373240690e-01
    +1.0000000000e+00  -2.0000000000e+00  +1.0000000000e+00  +1.0000000000e+00  -1.9933805831e+00  +9.9345700282e-01
- Baseline B / adaptive front end: Butterworth band-pass 0.5-100 Hz, 4th-order prototype:
    +1.2889853689e-01  +2.5779707379e-01  +1.2889853689e-01  +1.0000000000e+00  +1.7546645815e-01  +4.7217141609e-02
    +1.0000000000e+00  +2.0000000000e+00  +1.0000000000e+00  +1.0000000000e+00  +2.5115959426e-01  +4.5498702988e-01
    +1.0000000000e+00  -2.0000000000e+00  +1.0000000000e+00  +1.0000000000e+00  -1.9838454806e+00  +9.8392197641e-01
    +1.0000000000e+00  -2.0000000000e+00  +1.0000000000e+00  +1.0000000000e+00  -1.9933016441e+00  +9.9337770695e-01
- IIR notch f0 = 50 Hz, Q = 20 (scipy.signal.iirnotch):
    +9.7864587113e-01  -1.2581228805e+00  +9.7864587113e-01  +1.0000000000e+00  -1.2581228805e+00  +9.5729174225e-01
- IIR notch f0 = 50 Hz, Q = 30 (scipy.signal.iirnotch):
    +9.8566310036e-01  -1.2671440565e+00  +9.8566310036e-01  +1.0000000000e+00  -1.2671440565e+00  +9.7132620073e-01
- IIR notch f0 = 50 Hz, Q = 40 (scipy.signal.iirnotch):
    +9.8920897597e-01  -1.2717025463e+00  +9.8920897597e-01  +1.0000000000e+00  -1.2717025463e+00  +9.7841795194e-01
- IIR notch f0 = 60 Hz, Q = 20 (scipy.signal.iirnotch):
    +9.7448228336e-01  -9.7448228336e-01  +9.7448228336e-01  +1.0000000000e+00  -9.7448228336e-01  +9.4896456671e-01
- IIR notch f0 = 60 Hz, Q = 30 (scipy.signal.iirnotch):
    +9.8284438740e-01  -9.8284438740e-01  +9.8284438740e-01  +1.0000000000e+00  -9.8284438740e-01  +9.6568877481e-01
- IIR notch f0 = 60 Hz, Q = 40 (scipy.signal.iirnotch):
    +9.8707843546e-01  -9.8707843546e-01  +9.8707843546e-01  +1.0000000000e+00  -9.8707843546e-01  +9.7415687092e-01

## App. B - timing statistics
- Batch of 4 held-out segments (4 x 3600 samples), 6 dB, 50 Hz; one warm-up run then 5 timed runs; median and standard deviation of time per output sample
| Method | L | Median (µs/sample) | s.d. (µs/sample) | MACs LMS | MACs NLMS |
|---|---|---|---|---|---|
| A | – | 0.019 | 0.000 | 20 | 20 |
| B | – | 0.046 | 0.000 | 25 | 25 |
| C | – | 2.558 | 0.006 | 25 | 26 |
| D | 8 | 2.859 | 0.016 | 57 | 59 |
| D | 16 | 2.928 | 0.009 | 73 | 75 |
| D | 32 | 2.917 | 0.015 | 105 | 107 |
| D | 64 | 3.025 | 0.013 | 169 | 171 |
| E | 8 | 5.099 | 0.002 | 62 | 65 |
| E | 16 | 5.430 | 0.746 | 78 | 81 |
| E | 32 | 5.232 | 0.022 | 110 | 113 |
| E | 64 | 5.354 | 0.146 | 174 | 177 |

## Extra metrics used in Secs. 10-12 and 15 (held-out means)
| Condition | Method | ΔSNR (dB) | RMSE (mV) | r | R-time err (ms) | QRS amp. err (%) | PLI att. (dB) |
|---|---|---|---|---|---|---|---|
| 0 dB, 50 Hz | noisy | 0.00 | 0.2008 | 0.705 | 2.10 | 13.3 | 0.0 |
| 0 dB, 50 Hz | A | 3.01 | 0.1437 | 0.777 | 1.61 | 3.7 | 9.3 |
| 0 dB, 50 Hz | B | 3.84 | 0.1312 | 0.810 | 0.42 | 2.5 | 44.2 |
| 0 dB, 50 Hz | C|lms | 3.81 | 0.1318 | 0.810 | 0.46 | 2.6 | 36.3 |
| 0 dB, 50 Hz | C|nlms | 3.67 | 0.1339 | 0.809 | 0.36 | 3.3 | 48.4 |
| 0 dB, 50 Hz | D|lms|8 | 1.63 | 0.1666 | 0.730 | 2.20 | 12.0 | -0.0 |
| 0 dB, 50 Hz | D|lms|16 | 1.51 | 0.1690 | 0.720 | 2.25 | 12.4 | -0.0 |
| 0 dB, 50 Hz | E|lms|8 | 7.36 | 0.0868 | 0.903 | 0.55 | 2.3 | 36.3 |
| 0 dB, 50 Hz | E|lms|16 | 6.96 | 0.0908 | 0.894 | 0.70 | 2.8 | 36.3 |
| 0 dB, 50 Hz | E|lms|32 | 6.42 | 0.0967 | 0.878 | 0.93 | 3.5 | 36.3 |
| 0 dB, 50 Hz | E|lms|64 | 5.67 | 0.1055 | 0.853 | 1.43 | 4.5 | 36.3 |
| 0 dB, 50 Hz | E|nlms|64 | -0.15 | 0.2055 | 0.239 | 12.65 | 56.1 | 44.0 |
| 0 dB, 60 Hz | noisy | 0.00 | 0.2008 | 0.705 | 2.26 | 14.1 | 0.0 |
| 0 dB, 60 Hz | A | 3.46 | 0.1368 | 0.792 | 1.58 | 3.5 | 16.4 |
| 0 dB, 60 Hz | B | 3.84 | 0.1313 | 0.810 | 0.40 | 2.5 | 51.1 |
| 0 dB, 60 Hz | C|lms | 3.80 | 0.1319 | 0.810 | 0.50 | 2.6 | 39.0 |
| 0 dB, 60 Hz | C|nlms | 3.67 | 0.1339 | 0.810 | 0.36 | 3.6 | 54.0 |
| 0 dB, 60 Hz | D|lms|8 | 1.65 | 0.1664 | 0.730 | 2.41 | 13.2 | -0.0 |
| 0 dB, 60 Hz | D|lms|16 | 1.53 | 0.1687 | 0.721 | 2.48 | 13.7 | -0.0 |
| 0 dB, 60 Hz | E|lms|8 | 7.34 | 0.0870 | 0.903 | 0.54 | 2.4 | 39.1 |
| 0 dB, 60 Hz | E|lms|16 | 6.95 | 0.0910 | 0.893 | 0.69 | 2.9 | 39.1 |
| 0 dB, 60 Hz | E|lms|32 | 6.41 | 0.0969 | 0.878 | 0.94 | 3.6 | 39.1 |
| 0 dB, 60 Hz | E|lms|64 | 5.66 | 0.1056 | 0.853 | 1.50 | 4.6 | 39.2 |
| 0 dB, 60 Hz | E|nlms|64 | -0.11 | 0.2045 | 0.238 | 12.70 | 56.2 | 48.9 |
| 6 dB, 50 Hz | noisy | 0.00 | 0.1006 | 0.893 | 1.04 | 6.1 | 0.0 |
| 6 dB, 50 Hz | A | -0.16 | 0.1034 | 0.867 | 1.53 | 2.7 | 9.3 |
| 6 dB, 50 Hz | B | 0.57 | 0.0954 | 0.887 | 0.39 | 1.9 | 38.4 |
| 6 dB, 50 Hz | C|lms | 0.55 | 0.0956 | 0.887 | 0.45 | 1.9 | 31.4 |
| 6 dB, 50 Hz | C|nlms | 0.43 | 0.0969 | 0.886 | 0.35 | 2.7 | 42.6 |
| 6 dB, 50 Hz | D|lms|8 | -0.78 | 0.1106 | 0.852 | 1.28 | 4.6 | -0.0 |
| 6 dB, 50 Hz | D|lms|16 | -1.02 | 0.1137 | 0.843 | 1.36 | 5.0 | -0.0 |
| 6 dB, 50 Hz | E|lms|8 | 1.59 | 0.0846 | 0.908 | 0.56 | 2.2 | 31.5 |
| 6 dB, 50 Hz | E|lms|16 | 1.20 | 0.0884 | 0.899 | 0.71 | 2.7 | 31.4 |
| 6 dB, 50 Hz | E|lms|32 | 0.63 | 0.0945 | 0.883 | 0.94 | 3.4 | 31.4 |
| 6 dB, 50 Hz | E|lms|64 | -0.16 | 0.1034 | 0.858 | 1.45 | 4.4 | 31.4 |
| 6 dB, 50 Hz | E|nlms|64 | -6.08 | 0.2035 | 0.243 | 12.57 | 56.5 | 39.6 |
| 6 dB, 60 Hz | noisy | 0.00 | 0.1007 | 0.893 | 1.26 | 5.6 | 0.0 |
| 6 dB, 60 Hz | A | 0.04 | 0.1011 | 0.872 | 1.54 | 2.7 | 16.4 |
| 6 dB, 60 Hz | B | 0.56 | 0.0954 | 0.886 | 0.37 | 1.8 | 45.5 |
| 6 dB, 60 Hz | C|lms | 0.54 | 0.0957 | 0.886 | 0.48 | 2.0 | 35.9 |
| 6 dB, 60 Hz | C|nlms | 0.43 | 0.0969 | 0.886 | 0.33 | 3.1 | 48.3 |
| 6 dB, 60 Hz | D|lms|8 | -0.78 | 0.1105 | 0.852 | 1.46 | 4.8 | -0.0 |
| 6 dB, 60 Hz | D|lms|16 | -1.02 | 0.1136 | 0.843 | 1.50 | 5.3 | -0.0 |
| 6 dB, 60 Hz | E|lms|8 | 1.57 | 0.0847 | 0.908 | 0.57 | 2.2 | 36.0 |
| 6 dB, 60 Hz | E|lms|16 | 1.18 | 0.0886 | 0.898 | 0.68 | 2.8 | 35.9 |
| 6 dB, 60 Hz | E|lms|32 | 0.61 | 0.0947 | 0.883 | 0.94 | 3.5 | 35.9 |
| 6 dB, 60 Hz | E|lms|64 | -0.17 | 0.1035 | 0.858 | 1.47 | 4.5 | 36.0 |
| 6 dB, 60 Hz | E|nlms|64 | -6.08 | 0.2037 | 0.242 | 12.77 | 56.5 | 45.1 |
| 12 dB, 50 Hz | noisy | 0.00 | 0.0504 | 0.970 | 0.53 | 3.0 | 0.0 |
| 12 dB, 50 Hz | A | -4.99 | 0.0903 | 0.895 | 1.53 | 2.5 | 9.3 |
| 12 dB, 50 Hz | B | -4.29 | 0.0836 | 0.910 | 0.39 | 1.7 | 32.5 |
| 12 dB, 50 Hz | C|lms | -4.30 | 0.0837 | 0.911 | 0.46 | 1.7 | 26.0 |
| 12 dB, 50 Hz | C|nlms | -4.41 | 0.0847 | 0.910 | 0.32 | 2.5 | 36.6 |
| 12 dB, 50 Hz | D|lms|8 | -5.08 | 0.0912 | 0.894 | 0.77 | 2.6 | -0.0 |
| 12 dB, 50 Hz | D|lms|16 | -5.42 | 0.0948 | 0.885 | 0.89 | 3.1 | -0.0 |
| 12 dB, 50 Hz | E|lms|8 | -4.35 | 0.0840 | 0.909 | 0.58 | 2.1 | 25.9 |
| 12 dB, 50 Hz | E|lms|16 | -4.74 | 0.0878 | 0.900 | 0.71 | 2.6 | 25.9 |
| 12 dB, 50 Hz | E|lms|32 | -5.32 | 0.0939 | 0.885 | 0.94 | 3.4 | 25.9 |
| 12 dB, 50 Hz | E|lms|64 | -6.12 | 0.1029 | 0.859 | 1.44 | 4.4 | 25.9 |
| 12 dB, 50 Hz | E|nlms|64 | -12.05 | 0.2028 | 0.245 | 12.64 | 56.6 | 34.0 |
| 12 dB, 60 Hz | noisy | 0.00 | 0.0504 | 0.970 | 0.60 | 3.0 | 0.0 |
| 12 dB, 60 Hz | A | -4.92 | 0.0897 | 0.897 | 1.53 | 2.4 | 16.4 |
| 12 dB, 60 Hz | B | -4.30 | 0.0837 | 0.910 | 0.38 | 1.7 | 39.5 |
| 12 dB, 60 Hz | C|lms | -4.32 | 0.0839 | 0.910 | 0.47 | 1.8 | 31.1 |
| 12 dB, 60 Hz | C|nlms | -4.40 | 0.0847 | 0.910 | 0.33 | 3.0 | 42.3 |
| 12 dB, 60 Hz | D|lms|8 | -5.08 | 0.0912 | 0.894 | 0.87 | 2.6 | -0.0 |
| 12 dB, 60 Hz | D|lms|16 | -5.42 | 0.0947 | 0.885 | 0.95 | 3.1 | -0.0 |
| 12 dB, 60 Hz | E|lms|8 | -4.37 | 0.0842 | 0.909 | 0.57 | 2.2 | 31.1 |
| 12 dB, 60 Hz | E|lms|16 | -4.76 | 0.0880 | 0.900 | 0.68 | 2.7 | 31.1 |
| 12 dB, 60 Hz | E|lms|32 | -5.34 | 0.0941 | 0.884 | 0.94 | 3.5 | 31.1 |
| 12 dB, 60 Hz | E|lms|64 | -6.12 | 0.1030 | 0.859 | 1.47 | 4.5 | 31.1 |
| 12 dB, 60 Hz | E|nlms|64 | -12.06 | 0.2033 | 0.243 | 12.77 | 56.6 | 40.0 |

## Validation vs held-out ranking of E-LMS by L (6 dB, 50 Hz held-out)
- L = 8: validation ΔSNR 1.78 dB; held-out ΔSNR 1.59 dB
- L = 16: validation ΔSNR 1.48 dB; held-out ΔSNR 1.20 dB
- L = 32: validation ΔSNR 0.94 dB; held-out ΔSNR 0.63 dB
- L = 64: validation ΔSNR 0.21 dB; held-out ΔSNR -0.16 dB