"""ecg_draft.py - DSP library for the ECE F434 mini project (draft-protocol version).

Implements the method exactly as described in the report:
  * clean ECG: MIT-BIH Arrhythmia DB, non-overlapping 10 s segments (3600 samples),
    mean (DC) offset removed only, no peak normalisation
  * disturbance: NSTDB electrode-motion record (em) aligned by sample index
    + synthetic 50/60 Hz PLI with random phase; PLI:motion power ratio set first,
    then ONE common gain gives the exact input SNR  (report eq. (3))
  * Baseline A: causal Butterworth band-pass 0.5-40 Hz (4th-order prototype, SOS)
  * Baseline B: causal Butterworth band-pass 0.5-100 Hz + IIR notch (Q = 30)
  * adaptive branches on the 0.5-100 Hz band:
        C = PLI only (sin/cos reference, 2 weights)
        D = motion only (L-tap filter on the em proxy reference)
        E = C and D in parallel with a shared error
    each with LMS  w <- w + mu e x               (report eq. (5))
          or NLMS  w <- w + mu e x / (eps + x'x)  (report eq. (6)), eps = 1e-6
  * references normalised to unit RMS before adaptation
  * weights start at zero for every segment; equal 1 s transient exclusion for
    every method
All filters are causal (sample-by-sample realisable); filtfilt is never used.
"""
import numpy as np
from scipy import signal

FS = 360.0
SEG = int(10 * FS)          # 10 s segments = 3600 samples
TRANS = int(1.0 * FS)       # transient exclusion applied to EVERY method
MAXLAG = 40                 # max integer delay searched when aligning outputs
EPS = 1e-6                  # NLMS regulariser (report Table II)
# annotation symbols that mark unsuitable intervals (signal-quality / noise marks)
BAD_SYMS = set("~|Q!x")
BEAT_SYMS = set("NLRBAaJSVrFejnE/f")


# --------------------------------------------------------------------------- data
def load_record(rec, path="data", channel=0):
    """Return (signal_mV, fs, r_peak_indices, annotation_samples, annotation_symbols)."""
    import wfdb
    r = wfdb.rdrecord(f"{path}/{rec}", channels=[channel])
    a = wfdb.rdann(f"{path}/{rec}", "atr")
    sym = np.array(a.symbol)
    rp = np.array([s for s, c in zip(a.sample, sym) if c in BEAT_SYMS])
    return r.p_signal[:, 0].astype(float), float(r.fs), rp, np.array(a.sample), sym


def load_em(path="data", channel=0):
    import wfdb
    r = wfdb.rdrecord(f"{path}/em", channels=[channel])
    return r.p_signal[:, 0].astype(float)


def segment_starts(n_total, ann_samp, ann_sym, t0_s, t1_s):
    """Non-overlapping 10 s segment starts in [t0, t1) that contain no
    signal-quality / noise annotations (report Sec. 6.2)."""
    starts = []
    for st in range(int(t0_s * FS), int(t1_s * FS) - SEG + 1, SEG):
        if st + SEG > n_total:
            break
        inside = ann_sym[(ann_samp >= st) & (ann_samp < st + SEG)]
        if not any(c in BAD_SYMS for c in inside):
            starts.append(st)
    return starts


# --------------------------------------------------------------------------- mixtures
def rms(x, axis=None):
    return np.sqrt(np.mean(np.square(x), axis=axis))


def pli_wave(n, f0, phase, df=0.0):
    """Unit-RMS mains sinusoid at f0 + df Hz."""
    t = np.arange(n) / FS
    return np.sqrt(2.0) * np.sin(2 * np.pi * (f0 + df) * t + phase)


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


# --------------------------------------------------------------------------- fixed filters
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


# --------------------------------------------------------------------------- adaptive canceller
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


# --------------------------------------------------------------------------- metrics
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


# --------------------------------------------------------------------------- operation counts
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
