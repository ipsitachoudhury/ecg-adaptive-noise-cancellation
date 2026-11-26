# Appendix A – Source Code

All code is written in Python and is contained in this repository (8 files, 1186 lines). Every
filter is causal (sample-by-sample realisable); zero-phase `filtfilt` is never used in the compared methods.

## A.1 Files

| File | Purpose |
|---|---|
| [`ecg_draft.py`](../ecg_draft.py) | Core DSP library: mixture model (eqs. 1, 3), Baselines A and B, LMS/NLMS canceller (eqs. 4–6), instability rule, metrics, MAC counts |
| [`run_cfg.py`](../run_cfg.py) | Configuration: records, validation/test split, μ grids, PLI-to-motion ratio, seeds; segment selection and mixture builder |
| [`run_draft.py`](../run_draft.py) | Experiment: validation sweep → locked parameters → held-out tests T1–T6, extra NLMS ε diagnostic, timing, validation checks; writes results/ |
| [`make_figs_draft.py`](../make_figs_draft.py) | Draws Figs. 1–3, 5–11 and the validation-sweep figure (Fig. 12) |
| [`extra_figs.py`](../extra_figs.py) | Draws Appendix B Figs. 13–14 (0 dB/50 Hz, 12 dB/50 Hz, 6 dB/60 Hz) |
| [`report_values.py`](../report_values.py) | Prints environment, dataset log, sweep, SOS coefficients and timing values (results/report_values.md) |
| [`demo_draft.py`](../demo_draft.py) | Demonstration on one held-out segment: prints metrics of every method and plots the traces (Fig. 4) |
| [`download_data.py`](../download_data.py) | Downloads MIT-BIH record 100 and NSTDB em from PhysioNet into data/ |

## A.2 Requirements

Python 3 with `numpy`, `scipy`, `matplotlib` and `wfdb` (see [`requirements.txt`](../requirements.txt)).
Results in this repository were produced with Python 3.10.12, NumPy 2.2.6, SciPy 1.15.3, Matplotlib 3.10.9, WFDB 4.3.1.

## A.3 How to reproduce

```bash
pip3 install -r requirements.txt
python3 download_data.py          # data/100.hea .dat .atr and data/em.hea .dat from PhysioNet
python3 run_draft.py              # results/results.json, results/tables.md  (about 1 minute)
python3 report_values.py          # results/report_values.md
python3 make_figs_draft.py        # figs/fig01 ... fig11, figB1
python3 extra_figs.py             # figs/figB2, figB3
python3 demo_draft.py 6 50 8      # demonstration: input SNR 6 dB, 50 Hz PLI, L = 8
```

Expected console output of `run_draft.py` (first and last lines):

```
validation segments: 60, test segments: 90
PLI step size selected: {'lms': 0.005, 'nlms': 0.05}
...
ALL DONE
```

## A.4 Configuration used for the reported results

| Setting | Value |
|---|---|
| Records / split | MIT-BIH 100, channel 0 (MLII); validation 0–600 s (60 segments), test 900–1806 s (90 segments) |
| Segment length / transient exclusion | 10 s (3600 samples) / first 1 s of every output |
| Input SNR / PLI frequency | 0, 6, 12 dB / 50 Hz (primary), 60 Hz |
| PLI-to-motion power ratio | 0 dB (equal power) |
| Motion filter length L | 8, 16, 32, 64 |
| LMS μ grid | 0.001, 0.005, 0.01, 0.02, 0.05 |
| NLMS μ grid, ε | 0.05, 0.1, 0.25, 0.5, 1.0; ε = 10⁻⁶ |
| Notch | IIR, Q = 30 (20 and 40 in T2) |
| Instability rule | any segment: non-finite output, ‖w‖ > 100, or output power > 2× input power over the final 2 s |
| Random seed | default_rng([2026, record, start sample, round(10·SNR), f0]) |

## A.5 Core listings

### A.5.1 Mixture generation (report eqs. (1) and (3)) – `ecg_draft.py`

```python
def make_mixture(s, em_seg, snr_db, f0, rng, pli_motion_db=0.0, df=0.0,
                 use_em=True, use_pli=True):
    """Report eqs. (1) and (3).

    s       : clean ECG segment (mV); its mean is removed here
    em_seg  : em noise excerpt aligned by sample index (same length)
    Returns d (noisy primary), s (clean, mean removed), ref_m (unit-RMS em
    proxy reference), v (scaled total disturbance), phase, a (common gain)."""
    s = s - s.mean()
    n = len(s)
    vm = em_seg - em_seg.mean()
    vm = vm / rms(vm)
    phase = rng.uniform(0, 2 * np.pi)
    vp = pli_wave(n, f0, phase, df)
    if use_em and use_pli:
        ratio = 10 ** (pli_motion_db / 10)          # P_PLI / P_motion
        gm, gp = np.sqrt(1 / (1 + ratio)), np.sqrt(ratio / (1 + ratio))
    else:
        gm, gp = float(use_em), float(use_pli)
    v = gm * vm + gp * vp                           # composite first ...
    a = rms(s) / (rms(v) * 10 ** (snr_db / 20))     # ... then one common gain
    d = s + a * v
    return dict(d=d, s=s, ref_m=vm.copy(), v=a * v, phase=phase, a=a)
```

### A.5.2 Fixed baselines A and B – `ecg_draft.py`

```python
def bandpass(lo, hi, order=4):
    return signal.butter(order, [lo, hi], btype="band", fs=FS, output="sos")


def notch(f0, Q=30.0):
    b, a = signal.iirnotch(f0, Q, fs=FS)
    return signal.tf2sos(b, a)


SOS_A = bandpass(0.5, 40.0)
SOS_W = bandpass(0.5, 100.0)      # wide band used by Baseline B and C/D/E


def causal(sos, x):
    return signal.sosfilt(sos, x, axis=-1)


def baseline_A(d):
    return causal(SOS_A, d)


def baseline_B(d, f0, Q=30.0):
    return causal(notch(f0, Q), causal(SOS_W, d))
```

### A.5.3 LMS / NLMS adaptive canceller (report eqs. (4)–(6)) – `ecg_draft.py`

```python
def anc(d, ref_m=None, L=16, mu_m=0.01, f0=None, mu_p=0.01, alg="lms", eps=EPS,
        front_end=True):
    """Adaptive cancellation for a batch of segments (rows), causal per sample.

    d      : (B, N) noisy primary
    ref_m  : (B, N) unit-RMS motion reference, or None (no motion branch)
    f0     : nominal PLI frequency for the sin/cos reference, or None (no PLI branch)
    The primary AND the motion reference pass through the same causal
    0.5-100 Hz band-pass, so the relation between them is preserved.
    Returns e (cleaned output), wmax (largest weight norm seen, per segment)."""
    d = np.atleast_2d(d)
    if front_end:
        d = causal(SOS_W, d)
    B, N = d.shape
    use_m, use_p = ref_m is not None, f0 is not None
    if use_m:
        r = np.atleast_2d(ref_m)
        if front_end:
            r = causal(SOS_W, r)
        wm = np.zeros((B, L)); xm = np.zeros((B, L)); pw = np.zeros(B)
    if use_p:
        k = np.arange(N)
        sp = np.sqrt(2) * np.sin(2 * np.pi * f0 * k / FS)   # unit-RMS references
        cp = np.sqrt(2) * np.cos(2 * np.pi * f0 * k / FS)
        wp = np.zeros((B, 2))
    e = np.empty_like(d)
    wmax = np.zeros(B)
    with np.errstate(over="ignore", invalid="ignore"):
        for n in range(N):
            y = np.zeros(B)
            if use_m:
                old = xm[:, -1].copy()
                xm[:, 1:] = xm[:, :-1]; xm[:, 0] = r[:, n]
                pw += xm[:, 0] ** 2 - old ** 2               # recursive ||x||^2
                y += np.einsum("bl,bl->b", wm, xm)
            if use_p:
                y += wp[:, 0] * sp[n] + wp[:, 1] * cp[n]
            en = d[:, n] - y
            e[:, n] = en
            if use_m:
                g = mu_m * en
                if alg == "nlms":
                    g = g / (eps + np.maximum(pw, 0.0))
                wm += g[:, None] * xm
                wmax = np.maximum(wmax, np.linalg.norm(wm, axis=1))
            if use_p:
                g = mu_p * en
                if alg == "nlms":
                    g = g / (eps + sp[n] ** 2 + cp[n] ** 2)  # = eps + 2
                wp[:, 0] += g * sp[n]; wp[:, 1] += g * cp[n]
                wmax = np.maximum(wmax, np.linalg.norm(wp, axis=1))
    return e, wmax
```

### A.5.4 Instability rule – `ecg_draft.py`

```python
W_LIMIT = 100.0     # coefficient-norm runaway threshold (references are unit RMS)
P_LIMIT = 2.0       # "sustained" = output power > 2x (+3 dB) input power over the final 2 s


def unstable(e, d, wmax, wlimit=W_LIMIT, plimit=P_LIMIT):
    """Predeclared instability rule (report Sec. 6.5), evaluated per segment:
    (i) non-finite output, (ii) coefficient-norm runaway (||w|| > wlimit), or
    (iii) sustained error power above input power: mean e^2 over the final 2 s
    more than plimit times the mean (band-passed) input power over the same 2 s.
    A setting is rejected if ANY segment meets one of these conditions."""
    tail = slice(-int(2 * FS), None)
    bad = ~np.all(np.isfinite(e), axis=1)
    bad |= ~np.isfinite(wmax) | (wmax > wlimit)
    with np.errstate(invalid="ignore", over="ignore"):
        pe = np.nan_to_num(np.mean(e[:, tail] ** 2, 1), nan=np.inf)
        bad |= pe > plimit * np.mean(np.atleast_2d(d)[:, tail] ** 2, 1)
    return bad
```

### A.5.5 Quality metrics – `ecg_draft.py`

```python
def best_lag(s, y):
    """Integer delay (0..MAXLAG) that best aligns causal output y with s."""
    a = s[TRANS:len(s) - MAXLAG]
    c = [np.dot(a, y[TRANS + k:len(y) - MAXLAG + k]) for k in range(MAXLAG + 1)]
    return int(np.argmax(c))


def metrics(s, y, d, r_idx=None, f0=None, lag=None):
    """Report Sec. 6.6. All metrics after the common transient exclusion and
    integer-delay alignment."""
    if not np.all(np.isfinite(y)):
        return None
    if lag is None:
        lag = best_lag(s, y)
    N = len(s) - MAXLAG
    ss, yy, dd = s[TRANS:N], y[TRANS + lag:N + lag], d[TRANS:N]
    snr_in = 10 * np.log10(np.sum(ss ** 2) / np.sum((dd - ss) ** 2))
    snr_out = 10 * np.log10(np.sum(ss ** 2) / np.sum((yy - ss) ** 2))
    out = dict(snr_in=snr_in, snr_out=snr_out, dsnr=snr_out - snr_in,
               rmse=float(rms(yy - ss)), r=float(np.corrcoef(ss, yy)[0, 1]), lag=lag)
    if f0 is not None:
        f, Pd = signal.welch(d[TRANS:], FS, nperseg=1024, nfft=4096)
        _, Py = signal.welch(y[TRANS:], FS, nperseg=1024, nfft=4096)
        k = np.argmin(abs(f - f0))
        out["pli_att"] = float(10 * np.log10(Pd[k - 2:k + 3].sum() / Py[k - 2:k + 3].sum()))
    if r_idx is not None:
        w = int(0.05 * FS)
        te, ae = [], []
        for rp in r_idx:
            i = rp - TRANS
            if i - w < 0 or i + w >= len(ss):
                continue
            cs, cy = ss[i - w:i + w], yy[i - w:i + w]
            te.append(abs(np.argmax(np.abs(cy)) - np.argmax(np.abs(cs))) / FS * 1000)
            ae.append(abs(np.ptp(cy) - np.ptp(cs)) / np.ptp(cs) * 100)
        if te:
            out["rt_err"] = float(np.mean(te)); out["qrs_amp_err"] = float(np.mean(ae))
    return out
```

### A.5.6 Operation counts – `ecg_draft.py`

```python
BIQUAD = 5                       # multiplies per DF-II-transposed biquad
SOS_COST = {"A": len(SOS_A) * BIQUAD, "W": len(SOS_W) * BIQUAD, "notch": BIQUAD}


def macs(method, L=16, alg="lms"):
    """Estimated MAC-like operations per output sample (report eq. / Sec. 7)."""
    motion = 2 * L + (3 if alg == "nlms" else 1)     # filter + update (+ recursive norm)
    pli = 2 + 2 + 1 + (1 if alg == "nlms" else 0)    # filter + update + error scaling
    return {"A": SOS_COST["A"],
            "B": SOS_COST["W"] + SOS_COST["notch"],
            "C": SOS_COST["W"] + pli,
            "D": 2 * SOS_COST["W"] + motion,          # reference also band-passed
            "E": 2 * SOS_COST["W"] + motion + pli}[method]
```

The complete files are in the repository root; `run_draft.py` and `make_figs_draft.py` are not reproduced here
because of their length.
