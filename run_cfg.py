"""run_cfg.py - shared configuration, segment selection and mixture builder.
Edit VAL_RECORDS / TEST_RECORDS here."""
import os, sys
import numpy as np
import ecg_draft as E

_HERE = os.path.dirname(os.path.abspath(__file__))
# data folder: ./data inside the repository (default), or ../data (original project layout)
DATA = next((p for p in (os.path.join(_HERE, "data"), os.path.join(_HERE, "..", "data"))
             if os.path.exists(os.path.join(p, "em.hea"))), os.path.join(_HERE, "data"))
# (record, start_s, end_s).  With only record 100: minutes 0-10 validation, 15-30 test.
VAL_RECORDS = [("100", 0, 600)]
TEST_RECORDS = [("100", 900, 1806)]
# With more records downloaded into data/, use separate records instead, e.g.:
# VAL_RECORDS  = [("100", 0, 1806), ("101", 0, 1806)]
# TEST_RECORDS = [("103", 0, 1806), ("112", 0, 1806), ("115", 0, 1806), ("117", 0, 1806)]
SNRS, F0S = [0, 6, 12], [50, 60]
LS = [8, 16, 32, 64]
MU = {"lms": [0.001, 0.005, 0.01, 0.02, 0.05],
      "nlms": [0.05, 0.1, 0.25, 0.5, 1.0]}
PLI_MOTION_DB = 0.0
QS = [20, 30, 40]
SEED = 2026
QUICK = "--quick" in sys.argv
MAX_SEG = 6 if QUICK else None

EM = E.load_em(DATA)
_REC = {}


def rec(rid):
    if rid not in _REC:
        _REC[rid] = E.load_record(rid, DATA)
    return _REC[rid]


def collect(spec):
    segs = []
    for rid, t0, t1 in spec:
        x, fs, rp, asamp, asym = rec(rid)
        assert fs == E.FS, f"record {rid}: fs = {fs}, expected 360 Hz"
        for st in E.segment_starts(len(x), asamp, asym, t0, t1):
            ri = rp[(rp >= st) & (rp < st + E.SEG)] - st
            segs.append((rid, st, x[st:st + E.SEG], ri))
    return segs[:MAX_SEG] if MAX_SEG else segs


VAL, TEST = collect(VAL_RECORDS), collect(TEST_RECORDS)


def build(segs, snr, f0, ratio=PLI_MOTION_DB, df=0.0, use_em=True, use_pli=True):
    """Identical noisy realisation for every method: the seed depends only on
    (record, segment start, SNR, f0)."""
    D, S, R, RI, META = [], [], [], [], []
    for rid, st, x, ri in segs:
        rng = np.random.default_rng([SEED, int(rid), st, int(10 * snr), f0])
        em = EM[st % (len(EM) - E.SEG):][:E.SEG]          # aligned by sample index
        m = E.make_mixture(x, em, snr, f0, rng, pli_motion_db=ratio, df=df, use_em=use_em, use_pli=use_pli)
        D.append(m["d"]); S.append(m["s"]); R.append(m["ref_m"]); RI.append(ri)
        META.append(dict(record=rid, start=int(st), phase=float(m["phase"]),
                         snr_check=float(10 * np.log10(np.sum(m["s"] ** 2) / np.sum(m["v"] ** 2)))))
    return np.array(D), np.array(S), np.array(R), RI, META


def test_batch(snr, f0, n=None):
    D, S, R, _, _ = build(TEST[:n] if n else TEST, snr, f0)
    return D, S, R


def example_segment():
    """Held-out segment used for the time-domain and PSD figures: the one whose
    em excerpt has the largest peak-to-RMS ratio, so motion transients are visible."""
    best, bp = TEST[0], -1
    for seg in TEST:
        st = seg[1]
        em = EM[st % (len(EM) - E.SEG):][:E.SEG]
        p = np.max(np.abs(em - em.mean())) / np.std(em)
        if p > bp:
            best, bp = seg, p
    return best
