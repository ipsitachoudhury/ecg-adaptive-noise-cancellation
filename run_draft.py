"""run_draft.py - complete experiment for the report (draft protocol).

    python3 run_draft.py            # full run  -> results/results.json, results/tables.md
    python3 run_draft.py --quick    # fewer segments, for a fast check

Records and the validation/test split are set in CONFIG below. With only record 100
available, minutes 0-10 are used for validation and minutes 15-30 for testing.
If you download more MIT-BIH records into data/, list them in TEST_RECORDS
(and optionally VAL_RECORDS) so validation and test use different records.
"""
import json, os, sys, time, itertools
import numpy as np
from scipy import signal
import ecg_draft as E

from run_cfg import (VAL, TEST, VAL_RECORDS, TEST_RECORDS, SNRS, F0S, LS, MU, PLI_MOTION_DB, QS,
                     SEED, QUICK, build)

os.makedirs("results", exist_ok=True)
T0 = time.time()
print(f"validation segments: {len(VAL)}, test segments: {len(TEST)}")


def score(S, D, Y, RI, f0=None):
    rows = [E.metrics(S[i], Y[i], D[i], RI[i], f0) for i in range(len(S))]
    rows = [r for r in rows if r is not None]
    if not rows:                                   # every segment diverged
        nan = [float("nan"), float("nan")]
        return dict(dsnr=nan, rmse=nan, r=nan, snr_in=nan, snr_out=nan)
    keys = [k for k in rows[0] if k != "lag"]
    return {k: [float(np.mean([r[k] for r in rows if k in r])),
                float(np.std([r[k] for r in rows if k in r]))] for k in keys}


def run(method, D, R, f0, alg="lms", L=16, mu_m=0.01, mu_p=0.01, Q=30.0):
    """Returns (output, unstable_flag)."""
    if method == "A":
        return E.baseline_A(D), False
    if method == "B":
        return E.baseline_B(D, f0, Q), False
    if method == "C":
        y, w = E.anc(D, None, f0=f0, mu_p=mu_p, alg=alg)
    elif method == "D":
        y, w = E.anc(D, R, L=L, mu_m=mu_m, alg=alg)
    elif method == "E":
        y, w = E.anc(D, R, L=L, mu_m=mu_m, f0=f0, mu_p=mu_p, alg=alg)
    bad = E.unstable(y, E.causal(E.SOS_W, D), w)
    return y, bool(bad.any())


OUT = dict(config=dict(val=VAL_RECORDS, test=TEST_RECORDS, n_val=len(VAL), n_test=len(TEST),
                       seg_s=10, transient_s=1.0, mu=MU, Ls=LS, snrs=SNRS, f0s=F0S,
                       pli_motion_db=PLI_MOTION_DB, eps=E.EPS, seed=SEED, quick=QUICK))

# ============================================================== Stage 1: validation (50 Hz)
VM = {s: build(VAL, s, 50) for s in SNRS}
sweep_p, sweep_m, sel_p, sel_m = {}, {}, {}, {}
for alg in ["lms", "nlms"]:
    best = None
    for mu in MU[alg]:
        vals, bad = [], False
        for s in SNRS:
            D, S, R, RI, _ = VM[s]
            y, u = run("C", D, R, 50, alg=alg, mu_p=mu)
            bad |= u
            vals.append(score(S, D, y, RI)["dsnr"][0])
        sweep_p[f"{alg}|{mu}"] = dict(dsnr=float(np.mean(vals)), stable=not bad)
        if not bad and (best is None or np.mean(vals) > best[1]):
            best = (mu, np.mean(vals))
    sel_p[alg] = best[0] if best else None
print("PLI step size selected:", sel_p, f"{time.time()-T0:.0f}s")

for alg, L in itertools.product(["lms", "nlms"], LS):
    best = None
    for mu in MU[alg] if sel_p[alg] is not None else []:
        vals, bad = [], False
        for s in SNRS:
            D, S, R, RI, _ = VM[s]
            y, u = run("E", D, R, 50, alg=alg, L=L, mu_m=mu, mu_p=sel_p[alg])
            bad |= u
            if not u:
                vals.append(score(S, D, y, RI)["dsnr"][0])
        sweep_m[f"{alg}|{L}|{mu}"] = dict(dsnr=float(np.mean(vals)) if not bad else None, stable=not bad)
        if not bad and (best is None or np.mean(vals) > best[1]):
            best = (mu, np.mean(vals))
    sel_m[f"{alg}|{L}"] = dict(mu=best[0] if best else None, val_dsnr=float(best[1]) if best else None,
                               rejected=[m for m in MU[alg] if f"{alg}|{L}|{m}" in sweep_m and not sweep_m[f"{alg}|{L}|{m}"]["stable"]])
    print(f"  {alg} L={L}: mu={sel_m[f'{alg}|{L}']['mu']}  rejected={sel_m[f'{alg}|{L}']['rejected']}  {time.time()-T0:.0f}s")
OUT["validation"] = dict(pli_sweep=sweep_p, pli_selected=sel_p, motion_sweep=sweep_m, motion_selected=sel_m)

# ============================================================== Stage 2: locked held-out test (T3-T5)
test, snr_checks = {}, []
for s, f0 in itertools.product(SNRS, F0S):
    D, S, R, RI, META = build(TEST, s, f0)
    snr_checks += [m["snr_check"] - s for m in META]
    key = f"{s}|{f0}"
    T = {"noisy": score(S, D, D, RI, f0)}
    for m in ["A", "B"]:
        y, _ = run(m, D, R, f0)
        T[m] = score(S, D, y, RI, f0)
    # diagnostic: perfect noise removal but the same causal front end (fidelity ceiling)
    T["ceiling_A"] = score(S, D, E.baseline_A(S), RI)
    T["ceiling_B"] = score(S, D, E.causal(E.SOS_W, S), RI)
    for alg in ["lms", "nlms"]:
        if sel_p[alg] is None:
            continue
        y, u = run("C", D, R, f0, alg=alg, mu_p=sel_p[alg])
        T[f"C|{alg}"] = dict(score(S, D, y, RI, f0), unstable=u)
        for L in LS:
            mu = sel_m[f"{alg}|{L}"]["mu"]
            if mu is None:
                continue
            for m in ["D", "E"]:
                y, u = run(m, D, R, f0, alg=alg, L=L, mu_m=mu, mu_p=sel_p[alg])
                T[f"{m}|{alg}|{L}"] = dict(score(S, D, y, RI, f0), unstable=u)
    test[key] = T
    print("test", key, f"{time.time()-T0:.0f}s")
OUT["test"] = test

# ============================================================== T1: em only, Baseline A
t1 = {}
for s in SNRS:
    D, S, R, RI, _ = build(TEST, s, 50, use_pli=False)
    t1[str(s)] = score(S, D, E.baseline_A(D), RI)
OUT["T1_em_only_A"] = t1

# ============================================================== T2: PLI only, Baseline B, Q and offset
t2 = {}
for f0, df, Q in itertools.product(F0S, [0.0, 0.2], QS):
    D, S, R, RI, _ = build(TEST, 6, f0, use_em=False, df=df)
    t2[f"{f0}|{df}|{Q}"] = score(S, D, E.baseline_B(D, f0, Q), RI, f0)
OUT["T2_pli_only_B"] = t2

# ============================================================== T6: reference stress (motion only, D, L=16, 6 dB)
t6 = {"gain": {}, "corr": {}, "L_used": {}}
D, S, R, RI, _ = build(TEST, 6, 50, use_pli=False)


def t6_setting(alg):
    """L = 16 if it has a stable locked mu, otherwise the shortest L that does."""
    for L in [16] + [l for l in LS if l != 16]:
        if sel_m[f"{alg}|{L}"]["mu"] is not None:
            return L, sel_m[f"{alg}|{L}"]["mu"]
    return None, None


for alg in ["lms", "nlms"]:
    t6["L_used"][alg] = t6_setting(alg)[0]
for g in [0.1, 0.316, 1.0, 3.16, 10.0]:
    for alg in ["lms", "nlms"]:
        L6, mu6 = t6_setting(alg)
        if L6 is None:
            t6["gain"][f"{g}|{alg}"] = dict(dsnr=[float("nan")] * 2, unstable=True); continue
        y, u = run("D", D, R * g, 50, alg=alg, L=L6, mu_m=mu6)
        t6["gain"][f"{g}|{alg}"] = dict(score(S, D, y, RI), unstable=u)
rng = np.random.default_rng(SEED)
W = rng.standard_normal(R.shape)
for rho in [1.0, 0.9, 0.7, 0.5, 0.3]:
    Rc = rho * R + np.sqrt(1 - rho ** 2) * W          # unit RMS, correlation rho with em
    for alg in ["lms", "nlms"]:
        L6, mu6 = t6_setting(alg)
        if L6 is None:
            t6["corr"][f"{rho}|{alg}"] = dict(dsnr=[float("nan")] * 2, unstable=True); continue
        y, u = run("D", D, Rc, 50, alg=alg, L=L6, mu_m=mu6)
        t6["corr"][f"{rho}|{alg}"] = dict(score(S, D, y, RI), unstable=u)
OUT["T6_reference_stress"] = t6
print("stress tests done", f"{time.time()-T0:.0f}s")

# ============================================================== EXTRA: NLMS regulariser sensitivity
# Not part of the draft protocol (which fixes eps = 1e-6). Repeats the NLMS
# validation sweep for E (L = 16) with larger eps, and evaluates the best stable
# setting on the held-out 6 dB / 50 Hz mixtures. Report it as an additional
# diagnostic, e.g. under "implementation challenges".
extra_eps = {}
if sel_p["nlms"] is not None:
    Dt, St, Rt, RIt, _ = build(TEST, 6, 50)
    for eps in [1e-6, 0.01 * 16, 0.1 * 16]:
        best, rej = None, []
        for mu in MU["nlms"]:
            vals, bad = [], False
            for s_ in SNRS:
                D, S, R, RI, _ = VM[s_]
                y, w = E.anc(D, R, L=16, mu_m=mu, f0=50, mu_p=sel_p["nlms"], alg="nlms", eps=eps)
                bad |= bool(E.unstable(y, E.causal(E.SOS_W, D), w).any())
                if not bad:
                    vals.append(score(S, D, y, RI)["dsnr"][0])
            if bad:
                rej.append(mu)
            elif best is None or np.mean(vals) > best[1]:
                best = (mu, float(np.mean(vals)))
        row = dict(rejected=rej, mu=best[0] if best else None, val_dsnr=best[1] if best else None)
        if best:
            y, w = E.anc(Dt, Rt, L=16, mu_m=best[0], f0=50, mu_p=sel_p["nlms"], alg="nlms", eps=eps)
            row["test_6dB_50Hz"] = score(St, Dt, y, RIt, 50)
        extra_eps[f"{eps:g}"] = row
OUT["extra_nlms_eps"] = extra_eps
print("extra eps test done", f"{time.time()-T0:.0f}s")

# ============================================================== cost
D, S, R, RI, _ = build(TEST[:4], 6, 50)
ns = D.size


def timed(fn, reps=5):
    fn()                                               # warm-up
    t = []
    for _ in range(reps):
        a = time.perf_counter(); fn(); t.append(time.perf_counter() - a)
    return float(np.median(t) / ns * 1e6), float(np.std(t) / ns * 1e6)


cost = {}
for m in ["A", "B", "C"]:
    alg = "lms"
    rt = timed(lambda: run(m, D, R, 50, alg=alg, mu_p=0.005))
    cost[m] = dict(us=rt, macs_lms=E.macs(m, 16, "lms"), macs_nlms=E.macs(m, 16, "nlms"))
for m, L in itertools.product(["D", "E"], LS):
    rt = timed(lambda: run(m, D, R, 50, alg="lms", L=L, mu_m=0.001, mu_p=0.005))
    cost[f"{m}|{L}"] = dict(us=rt, macs_lms=E.macs(m, L, "lms"), macs_nlms=E.macs(m, L, "nlms"))
OUT["cost"] = cost

# ============================================================== validation checks (report Table X)
chk = {}
for f0 in F0S:
    w, h = signal.sosfreqz(E.notch(f0, 30), 2 ** 18, fs=E.FS)
    mag = 20 * np.log10(np.abs(h) + 1e-15)
    band = w[mag < -3.0103]
    chk[f"notch_{f0}"] = dict(null_hz=float(w[np.argmin(mag)]), bw3_hz=float(band.max() - band.min()),
                              expected_bw=f0 / 30)
for name, sos, lo, hi in [("A", E.SOS_A, 0.5, 40), ("W", E.SOS_W, 0.5, 100)]:
    w, h = signal.sosfreqz(sos, 2 ** 18, fs=E.FS)
    mag = 20 * np.log10(np.abs(h) + 1e-15)
    pas = w[mag > -3.0103]
    chk[f"bandpass_{name}"] = dict(lo3_hz=float(pas.min()), hi3_hz=float(pas.max()), design=[lo, hi])
chk["snr_scaling_max_abs_err_db"] = float(np.max(np.abs(snr_checks)))
chk["nlms_stable_mu"] = sorted({float(k.split("|")[2]) for k, v in sweep_m.items() if k.startswith("nlms") and v["stable"]})
chk["lms_stable_mu"] = {L: sorted(float(k.split("|")[2]) for k, v in sweep_m.items() if k.startswith(f"lms|{L}|") and v["stable"]) for L in LS}
OUT["checks"] = chk
OUT["meta"] = dict(runtime_s=time.time() - T0, python=sys.version.split()[0], numpy=np.__version__,
                   scipy=__import__("scipy").__version__)
json.dump(OUT, open("results/results.json", "w"), indent=1)

# ============================================================== tables for the report
def f(v, d=2):
    return "–" if v is None else f"{v[0]:.{d}f} ± {v[1]:.{d}f}" if isinstance(v, list) else f"{v:.{d}f}"


L_REP = 16
lines = [f"# Results tables (validation segments: {len(VAL)}, held-out test segments: {len(TEST)})", ""]
lines += ["## Table V – Locked parameters", "", "| Algorithm | L | Selected μ | Validation ΔSNR (dB) | Rejected μ |", "|---|---|---|---|---|"]
for alg, L in itertools.product(["lms", "nlms"], LS):
    v = sel_m[f"{alg}|{L}"]
    lines.append(f"| {alg.upper()} | {L} | {v['mu']} | {f(v['val_dsnr'])} | {', '.join(map(str, v['rejected'])) or 'none'} |")
for alg in ["lms", "nlms"]:
    vd = sweep_p[f"{alg}|{sel_p[alg]}"]["dsnr"] if sel_p[alg] is not None else float("nan")
    lines.append(f"| PLI branch {alg.upper()} | 2 weights | {sel_p[alg]} | {vd:.2f} | "
                 f"{', '.join(k.split('|')[1] for k, v in sweep_p.items() if k.startswith(alg) and not v['stable']) or 'none'} |")
T6d = test["6|50"]
lines += ["", f"## Table VI – Held-out results at 6 dB, 50 Hz (D and E use L = {L_REP})", "",
          "| Method | ΔSNR (dB) | RMSE (mV) | r | R-peak timing err (ms) | PLI atten. (dB) | Runtime (µs/sample) | MACs/sample |",
          "|---|---|---|---|---|---|---|---|"]
rowspec = [("Noisy input", "noisy", None), ("A: 0.5–40 Hz band-pass", "A", "A"), ("B: 0.5–100 Hz + notch", "B", "B"),
           ("C: PLI-only LMS", "C|lms", "C"), ("C: PLI-only NLMS", "C|nlms", "C"),
           ("D: motion-only LMS", f"D|lms|{L_REP}", f"D|{L_REP}"), ("D: motion-only NLMS", f"D|nlms|{L_REP}", f"D|{L_REP}"),
           ("E: combined LMS", f"E|lms|{L_REP}", f"E|{L_REP}"), ("E: combined NLMS", f"E|nlms|{L_REP}", f"E|{L_REP}")]
for lab, k, ck in rowspec:
    v = T6d.get(k)
    if v is None:
        continue
    alg = "nlms" if "nlms" in k else "lms"
    c = cost.get(ck) if ck else None
    lines.append(f"| {lab} | {f(v['dsnr'])} | {f(v['rmse'], 4)} | {f(v['r'], 3)} | {f(v.get('rt_err'))} | "
                 f"{f(v.get('pli_att'), 1)} | {f(c['us'][0]) if c else '–'} | {c['macs_' + alg] if c else '–'} |")
lines += ["", "## Extra – front-end fidelity ceiling (clean ECG alone through the filter, 6 dB / 50 Hz reference)", "",
          "| Front end | Output SNR vs clean (dB) | r |", "|---|---|---|",
          f"| A: 0.5–40 Hz | {T6d['ceiling_A']['snr_out'][0]:.2f} | {T6d['ceiling_A']['r'][0]:.3f} |",
          f"| 0.5–100 Hz (B, C, D, E) | {T6d['ceiling_B']['snr_out'][0]:.2f} | {T6d['ceiling_B']['r'][0]:.3f} |"]
lines += ["", "## Table VII – ΔSNR (dB) across input SNR and mains frequency", "",
          "| Method | " + " | ".join(f"{s} dB, {f0} Hz" for s in SNRS for f0 in F0S) + " |", "|---" * 7 + "|"]


def bestkey(prefix, T):
    c = [k for k in T if k.startswith(prefix) and np.isfinite(T[k]["dsnr"][0])]
    return max(c, key=lambda k: T[k]["dsnr"][0]) if c else None


for lab, pick in [("A", lambda T: "A"), ("B", lambda T: "B"), ("C (best)", lambda T: bestkey("C|", T)),
                  ("D (best)", lambda T: bestkey("D|", T)), ("E – LMS (best L)", lambda T: bestkey("E|lms", T)),
                  ("E – NLMS (best L)", lambda T: bestkey("E|nlms", T))]:
    cells = []
    for s in SNRS:
        for f0 in F0S:
            T = test[f"{s}|{f0}"]; k = pick(T)
            if k is None:
                cells.append("–"); continue
            cells.append(f"{T[k]['dsnr'][0]:.2f} ({k})" if k and k not in ("A", "B") else f"{T[k]['dsnr'][0]:.2f}")
    lines.append(f"| {lab} | " + " | ".join(cells) + " |")
lines += ["", "## Table VIII – Computational cost", "", "| Method | L | MACs (LMS) | MACs (NLMS) | Runtime µs/sample (median) |", "|---|---|---|---|---|"]
for k, v in cost.items():
    m, L = (k.split("|") + ["–"])[:2]
    lines.append(f"| {m} | {L} | {v['macs_lms']} | {v['macs_nlms']} | {v['us'][0]:.2f} |")
lines += ["", "## Table X – Validation checks", ""]
for f0 in F0S:
    c = chk[f"notch_{f0}"]
    lines.append(f"- Notch {f0} Hz: null at {c['null_hz']:.2f} Hz, −3 dB width {c['bw3_hz']:.2f} Hz (expected ≈ {c['expected_bw']:.2f} Hz)")
for n in ["A", "W"]:
    c = chk[f"bandpass_{n}"]
    lines.append(f"- Band-pass {'A' if n == 'A' else 'B'}: −3 dB at {c['lo3_hz']:.3f} Hz and {c['hi3_hz']:.2f} Hz (design {c['design']})")
lines.append(f"- SNR scaling: max |SNR_in − target| = {chk['snr_scaling_max_abs_err_db']:.2e} dB")
lines.append(f"- NLMS μ values stable for every L: {chk['nlms_stable_mu']}")
lines.append(f"- LMS stable μ per L: {chk['lms_stable_mu']}")
lines += ["", "## T1 – em only, Baseline A", "", "| Input SNR | ΔSNR | RMSE | r |", "|---|---|---|---|"]
for s, v in t1.items():
    lines.append(f"| {s} dB | {f(v['dsnr'])} | {f(v['rmse'], 4)} | {f(v['r'], 3)} |")
lines += ["", "## T2 – PLI only, Baseline B (6 dB)", "", "| f0 | offset (Hz) | Q | PLI atten. (dB) | ΔSNR | RMSE |", "|---|---|---|---|---|---|"]
for k, v in t2.items():
    f0, df, Q = k.split("|")
    lines.append(f"| {f0} | {df} | {Q} | {f(v['pli_att'], 1)} | {f(v['dsnr'])} | {f(v['rmse'], 4)} |")
lines += ["", f"## T6 – Reference stress (motion only, D, 6 dB; L used: LMS {t6['L_used']['lms']}, NLMS {t6['L_used']['nlms']})", "", "| Condition | LMS ΔSNR | NLMS ΔSNR |", "|---|---|---|"]
for kind, vals in [("gain", [0.1, 0.316, 1.0, 3.16, 10.0]), ("corr", [1.0, 0.9, 0.7, 0.5, 0.3])]:
    for v in vals:
        a, b = t6[kind][f"{v}|lms"], t6[kind][f"{v}|nlms"]
        fa = "unstable" if a["unstable"] else f(a.get("dsnr"))
        fb = "unstable" if b["unstable"] else f(b.get("dsnr"))
        lines.append(f"| reference {'gain ×' if kind == 'gain' else 'correlation ρ = '}{v} | {fa} | {fb} |")
lines += ["", "## Extra – NLMS regulariser sensitivity (E, L = 16; NOT part of the draft protocol, eps = 1e-6 there)", "",
          "| ε | Rejected μ | Selected μ | Validation ΔSNR | Held-out ΔSNR (6 dB, 50 Hz) | r |", "|---|---|---|---|---|---|"]
for k, v in extra_eps.items():
    t = v.get("test_6dB_50Hz")
    lines.append(f"| {k} | {', '.join(map(str, v['rejected'])) or 'none'} | {v['mu']} | {f(v['val_dsnr'])} | "
                 f"{f(t['dsnr']) if t else '–'} | {f(t['r'], 3) if t else '–'} |")
lines += ["", f"Instability rule: non-finite output, ||w|| > {E.W_LIMIT:g}, or output power > {E.P_LIMIT:g}x input power over the final 2 s, in any segment."]
lines += ["", f"Environment: Python {OUT['meta']['python']}, NumPy {OUT['meta']['numpy']}, SciPy {OUT['meta']['scipy']}; "
          f"run time {OUT['meta']['runtime_s']/60:.1f} min"]
open("results/tables.md", "w").write("\n".join(lines))
print("ALL DONE", f"{time.time()-T0:.0f}s")
