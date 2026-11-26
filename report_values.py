"""report_values.py - prints every remaining value the report placeholders need.

Run AFTER run_draft.py (it reads results/results.json):
    python3 report_values.py            -> results/report_values.md
Covers: environment (Sec. 8.3), dataset log and seeds (Sec. 6.2, Table III, App. B),
noise settings (App. B), full parameter sweep (App. B), SOS coefficients (App. B),
timing statistics (App. B), and extra metrics used in Secs. 10-12 and 15.
"""
import json, platform, subprocess, sys
import numpy as np
import scipy, matplotlib, wfdb
from scipy import signal
import ecg_draft as E
import run_cfg as C

R = json.load(open("results/results.json"))
out = []
P = out.append


def cpu_name():
    for cmd in (["sysctl", "-n", "machdep.cpu.brand_string"], ["lscpu"]):
        try:
            t = subprocess.run(cmd, capture_output=True, text=True, timeout=5).stdout
            if cmd[0] == "lscpu":
                for line in t.splitlines():
                    if line.startswith("Model name"):
                        return line.split(":", 1)[1].strip()
            elif t.strip():
                return t.strip()
        except Exception:
            pass
    return platform.processor() or platform.machine()


P("# Values for the report placeholders\n")
# ------------------------------------------------------------------ environment
P("## Sec. 8.3 - environment")
P(f"- Python {platform.python_version()}, NumPy {np.__version__}, SciPy {scipy.__version__}, "
  f"Matplotlib {matplotlib.__version__}, WFDB {wfdb.__version__}")
P(f"- OS: {platform.platform()}")
P(f"- Processor: {cpu_name()} ({platform.machine()})")
P(f"- Results file produced with: Python {R['meta']['python']}, NumPy {R['meta']['numpy']}, SciPy {R['meta']['scipy']}; "
  f"full run time {R['meta']['runtime_s']:.0f} s\n")

# ------------------------------------------------------------------ dataset log
P("## Sec. 6.2 / Table III / App. B - dataset log")
for name, spec, segs in [("Validation", C.VAL_RECORDS, C.VAL), ("Held-out test", C.TEST_RECORDS, C.TEST)]:
    for rid, t0, t1 in spec:
        hdr = wfdb.rdheader(f"{C.DATA}/{rid}")
        possible = len(range(int(t0 * E.FS), int(t1 * E.FS) - E.SEG + 1, E.SEG))
        mine = [s for s in segs if s[0] == rid]
        starts = [s[1] for s in mine]
        beats = sum(len(s[3]) for s in mine)
        P(f"- {name}: record {rid}, channel 0 ({hdr.sig_name[0]}), fs = {hdr.fs:g} Hz; window {t0}-{t1} s; "
          f"{len(mine)} segments of 10 s used ({possible - len(mine)} excluded by annotation check); "
          f"first start {starts[0]} samples ({starts[0]/E.FS:.0f} s), last start {starts[-1]} samples "
          f"({starts[-1]/E.FS:.0f} s), step {E.SEG} samples; {beats} annotated beats")
P(f"- Segment starts are every 3600 samples; segment k covers samples [start, start + 3600).")
P(f"- Random seed per mixture: numpy default_rng([{C.SEED}, record, start_sample, round(10*SNR_dB), f0]) "
  "- the same noisy realisation is given to every method.")
P(f"- Transient exclusion: first {E.TRANS} samples (1 s) of every output; delay alignment searched over 0-{E.MAXLAG} samples.\n")

# ------------------------------------------------------------------ noise settings
P("## App. B - noise settings")
ratio = C.PLI_MOTION_DB
gm, gp = np.sqrt(1 / (1 + 10 ** (ratio / 10))), np.sqrt(10 ** (ratio / 10) / (1 + 10 ** (ratio / 10)))
P(f"- PLI-to-motion power ratio {ratio:g} dB (equal power): g_m = {gm:.4f}, g_p = {gp:.4f} in eq. (1)")
P("- PLI: unit-RMS sinusoid sqrt(2)*sin(2*pi*f0*n/Fs + phi), phi ~ Uniform[0, 2*pi) drawn per mixture; no harmonics, "
  "no amplitude modulation; f0 = 50 Hz (primary) and 60 Hz; T2 also uses a +0.2 Hz offset")
P(f"- em: NSTDB record 'em', channel 0, excerpt starts at the same sample index as the ECG segment "
  f"(index mod {len(C.EM) - E.SEG}); mean removed and scaled to unit RMS; the same unit-RMS excerpt is the motion reference")
for snr in C.SNRS:
    D, S, Rm, RI, META = C.build(C.TEST, snr, 50)
    chk = [m["snr_check"] for m in META]
    P(f"- {snr} dB: measured SNR_in over the full segment = {np.mean(chk):.6f} dB "
      f"(max |error| {np.max(np.abs(np.array(chk) - snr)):.1e} dB) over {len(chk)} held-out segments")
P("")

# ------------------------------------------------------------------ sweep
P("## App. B - full parameter sweep (validation, 50 Hz, mean ΔSNR over 0/6/12 dB)")
P("| Branch | Algorithm | L | μ | Stable (rule) | Validation ΔSNR (dB) | Selected |")
P("|---|---|---|---|---|---|---|")
V = R["validation"]
for k, v in V["pli_sweep"].items():
    alg, mu = k.split("|")
    sel = "yes" if V["pli_selected"][alg] is not None and float(mu) == V["pli_selected"][alg] else ""
    P(f"| PLI (C) | {alg.upper()} | 2 weights | {mu} | {'yes' if v['stable'] else 'no'} | {v['dsnr']:.2f} | {sel} |")
for k, v in V["motion_sweep"].items():
    alg, L, mu = k.split("|")
    s = V["motion_selected"][f"{alg}|{L}"]["mu"]
    sel = "yes" if s is not None and float(mu) == s else ""
    d = f"{v['dsnr']:.2f}" if v["dsnr"] is not None else "– (rejected)"
    P(f"| Motion (E) | {alg.upper()} | {L} | {mu} | {'yes' if v['stable'] else 'no'} | {d} | {sel} |")
P("")

# ------------------------------------------------------------------ SOS
P("## App. B - filter specifications and SOS coefficients (each row: b0 b1 b2 a0 a1 a2)")
filt = [("Baseline A: Butterworth band-pass 0.5-40 Hz, 4th-order prototype (8th-order band-pass)", E.SOS_A),
        ("Baseline B / adaptive front end: Butterworth band-pass 0.5-100 Hz, 4th-order prototype", E.SOS_W)]
for f0 in (50, 60):
    for Q in (20, 30, 40):
        filt.append((f"IIR notch f0 = {f0} Hz, Q = {Q} (scipy.signal.iirnotch)", E.notch(f0, Q)))
for name, sos in filt:
    P(f"- {name}:")
    for row in sos:
        P("    " + "  ".join(f"{c:+.10e}" for c in row))
P("")

# ------------------------------------------------------------------ timing
P("## App. B - timing statistics")
P("- Batch of 4 held-out segments (4 x 3600 samples), 6 dB, 50 Hz; one warm-up run then 5 timed runs; "
  "median and standard deviation of time per output sample")
P("| Method | L | Median (µs/sample) | s.d. (µs/sample) | MACs LMS | MACs NLMS |")
P("|---|---|---|---|---|---|")
for k, v in R["cost"].items():
    m, L = (k.split("|") + ["–"])[:2]
    P(f"| {m} | {L} | {v['us'][0]:.3f} | {v['us'][1]:.3f} | {v['macs_lms']} | {v['macs_nlms']} |")
P("")

# ------------------------------------------------------------------ extra metrics for discussion
P("## Extra metrics used in Secs. 10-12 and 15 (held-out means)")
P("| Condition | Method | ΔSNR (dB) | RMSE (mV) | r | R-time err (ms) | QRS amp. err (%) | PLI att. (dB) |")
P("|---|---|---|---|---|---|---|---|")
for cond, T in R["test"].items():
    for k in ["noisy", "A", "B", "C|lms", "C|nlms", "D|lms|8", "D|lms|16", "E|lms|8", "E|lms|16", "E|lms|32", "E|lms|64", "E|nlms|64"]:
        if k not in T:
            continue
        v = T[k]
        g = lambda key, d=2: f"{v[key][0]:.{d}f}" if key in v and np.isfinite(v[key][0]) else "–"
        P(f"| {cond.replace('|', ' dB, ')} Hz | {k} | {g('dsnr')} | {g('rmse', 4)} | {g('r', 3)} | {g('rt_err')} | "
          f"{g('qrs_amp_err', 1)} | {g('pli_att', 1)} |")
P("")
P("## Validation vs held-out ranking of E-LMS by L (6 dB, 50 Hz held-out)")
for L in C.LS:
    P(f"- L = {L}: validation ΔSNR {V['motion_selected'][f'lms|{L}']['val_dsnr']:.2f} dB; "
      f"held-out ΔSNR {R['test']['6|50'][f'E|lms|{L}']['dsnr'][0]:.2f} dB")
open("results/report_values.md", "w").write("\n".join(out))
print("\n".join(out))
