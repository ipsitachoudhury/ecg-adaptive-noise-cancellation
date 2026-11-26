# Real-Time Adaptive Cancellation of Power-Line Interference and Motion Artifact in Wearable ECG

ECE F434 Digital Signal Processing – Mini Project, BITS Pilani Dubai Campus, First Semester 2026-27.

This repository contains all code, results and figures for the mini-project report. It compares two
causal fixed filters with low-complexity, reference-assisted **LMS / NLMS adaptive noise cancellers** for
removing 50/60 Hz power-line interference (PLI) and electrode-motion artifact from ECG, and reports signal
quality together with computational cost (MACs per sample).

* **Clean ECG:** MIT-BIH Arrhythmia Database, record 100 (lead MLII, 360 Hz), cut into 10 s segments.
* **Disturbance:** NSTDB electrode-motion record `em` + synthetic 50/60 Hz PLI, scaled to an exact input SNR of 0, 6 or 12 dB.
* **Methods:** A = 0.5–40 Hz band-pass; B = 0.5–100 Hz band-pass + IIR notch (Q = 30); C = adaptive PLI canceller
  (sin/cos reference, 2 weights); D = adaptive motion canceller (L-tap, em proxy reference); E = C + D in parallel.
  Every adaptive branch is run with LMS and NLMS.
* **Protocol:** step sizes tuned on 60 validation segments (0–600 s), then locked and tested once on 90 held-out
  segments (900–1806 s).

## Key results (held-out, 50 Hz)

| Method | ΔSNR 0 dB | ΔSNR 6 dB | ΔSNR 12 dB | MACs/sample |
|---|---|---|---|---|
| A: band-pass 0.5–40 Hz | 3.01 | -0.16 | -4.99 | 20 |
| B: band-pass 0.5–100 Hz + notch | 3.84 | 0.57 | -4.29 | 25 |
| E: combined LMS, L = 8 (selected) | 7.36 | 1.59 | -4.35 | 62 |

* The adaptive canceller helps under heavy noise (0 and 6 dB) but not at 12 dB, where the causal 0.5 Hz
  high-pass limits every method: the clean ECG alone through the 0.5–100 Hz front end has an output SNR of only
  8.18 dB.
* With the protocol settings (ε = 10⁻⁶, μ ∈ {0.05 … 1.0}) NLMS was unstable for L = 8–32 and harmful at L = 64.
* Full tables: [`results/tables.md`](results/tables.md). Appendices: [Appendix A – Source Code](docs/APPENDIX_A.md),
  [Appendix B – Supplementary Results / Dataset Details](docs/APPENDIX_B.md).

## Repository structure

```
.
├── ecg_draft.py          signal model, fixed filters, LMS/NLMS canceller, instability rule, metrics, MAC counts
├── run_cfg.py            records, validation/test split, step-size grids, seeds, mixture builder
├── run_draft.py          full experiment: validation sweep -> locked held-out tests T1–T6, cost, checks
├── make_figs_draft.py    report figures (Figs. 1–3, 5–11, 12)
├── extra_figs.py         Appendix B plots (Figs. 13–14)
├── report_values.py      values for the report placeholders / Appendix B
├── demo_draft.py         live demonstration on one held-out segment (Fig. 4)
├── download_data.py      downloads the PhysioNet records into data/
├── requirements.txt
├── data/                 PhysioNet files (downloaded, not committed)
├── results/              results.json, tables.md, report_values.md, run.log, demo output
├── figs/                 all figures as PNG
└── docs/                 APPENDIX_A.md, APPENDIX_B.md
```

## How to run

```bash
pip3 install -r requirements.txt
python3 download_data.py          # MIT-BIH record 100 + NSTDB em into data/
python3 run_draft.py              # ~1 min -> results/results.json, results/tables.md
python3 report_values.py          # -> results/report_values.md
python3 make_figs_draft.py        # -> figs/fig01 ... fig11, figB1
python3 extra_figs.py             # -> figs/figB2, figB3
python3 demo_draft.py 6 50 8      # demo: 6 dB input, 50 Hz PLI, L = 8
```

`python3 run_draft.py --quick` runs on 6 segments only, as a fast check. All random seeds are fixed, so a re-run
reproduces the committed quality values; runtimes depend on the computer.

## Figures (report numbering)

| Report | File | Report | File |
|---|---|---|---|
| Fig. 1 | `figs/fig01_methodology_flow.png` | Fig. 8 | `figs/fig08_dsnr_vs_L.png` |
| Fig. 2 | `figs/fig02_block_diagram.png` | Fig. 9 | `figs/fig09_learning_curves.png` |
| Fig. 3 | `figs/fig03_algorithm_flowchart.png` | Fig. 10 | `figs/fig10_pareto.png` |
| Fig. 4 | `figs/demo_output_L8.png` (+ terminal output) | Fig. 11 | `figs/fig11_reference_stress.png` |
| Fig. 5 | `figs/fig05_filter_responses.png` | Fig. 12 | `figs/figB1_validation_sweep.png` |
| Fig. 6 | `figs/fig06_time_domain.png` | Fig. 13 | `figs/figB2_time_conditions.png` |
| Fig. 7 | `figs/fig07_psd.png` | Fig. 14 | `figs/figB3_psd_conditions.png` |

## Limitations

Simulation only: one MIT-BIH record, additive noise, and the em record used as a *proxy* motion reference (it
is not an accelerometer signal). No clinical, accelerometer or embedded-hardware validation is claimed. Runtimes
are Python timings; MAC counts are algorithmic estimates.

## Data and citation

The data are not redistributed here; `download_data.py` fetches them from PhysioNet (Open Data Commons
Attribution License v1.0). If you use them, cite:

* G. B. Moody and R. G. Mark, "The impact of the MIT-BIH Arrhythmia Database," *IEEE Eng. Med. Biol. Mag.*, vol. 20, no. 3, pp. 45–50, 2001.
* G. B. Moody, W. K. Muldrow and R. G. Mark, "A noise stress test for arrhythmia detectors," *Computers in Cardiology*, vol. 11, pp. 381–384, 1984.
* A. L. Goldberger et al., "PhysioBank, PhysioToolkit, and PhysioNet," *Circulation*, vol. 101, no. 23, pp. e215–e220, 2000.

## Authors

Ipsita Choudhury – BITS Pilani Dubai Campus.
