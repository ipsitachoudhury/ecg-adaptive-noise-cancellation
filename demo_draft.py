"""demo_draft.py - live demonstration on ONE held-out segment.

    python3 demo_draft.py              # 6 dB, 50 Hz (default)
    python3 demo_draft.py 0 60         # input SNR 0 dB, 60 Hz mains
    python3 demo_draft.py 6 50 8       # 6 dB, 50 Hz, motion filter length L = 8 (selected configuration)

Prints the metrics of every method (screenshot this for report Fig. 4) and opens
the clean / noisy / filtered plot. Uses the locked parameters from
results/results.json if run_draft.py has been run, otherwise L = 16 defaults."""
import json, os, sys, time
import numpy as np
import matplotlib.pyplot as plt
import ecg_draft as E
import run_cfg

snr = float(sys.argv[1]) if len(sys.argv) > 1 else 6.0
f0 = int(sys.argv[2]) if len(sys.argv) > 2 else 50
L = int(sys.argv[3]) if len(sys.argv) > 3 else 16      # e.g. python3 demo_draft.py 6 50 8
mu = {"lms": 0.005, "nlms": 0.1}; mu_p = {"lms": 0.005, "nlms": 0.05}
if os.path.exists("results/results.json"):
    R = json.load(open("results/results.json"))
    mu = {a: R["validation"]["motion_selected"][f"{a}|{L}"]["mu"] or mu[a] for a in ("lms", "nlms")}
    for a in ("lms", "nlms"):
        if R["validation"]["motion_selected"][f"{a}|{L}"]["mu"] is None:
            print(f"NOTE: no stable {a.upper()} step size at L = {L} in validation; showing mu = {mu[a]} for illustration only")
    mu_p = {a: R["validation"]["pli_selected"][a] or {"lms": 0.005, "nlms": 0.05}[a] for a in ("lms", "nlms")}

os.makedirs("figs", exist_ok=True)
rid, st, x, ri = run_cfg.example_segment()
rng = np.random.default_rng([run_cfg.SEED, int(rid), st, int(10 * snr), f0])
em = run_cfg.EM[st % (len(run_cfg.EM) - E.SEG):][:E.SEG]
m = E.make_mixture(x, em, snr, f0, rng)
d, s, ref = m["d"], m["s"], m["ref_m"]

print(f"\nRecord {rid}, held-out segment at {st / E.FS:.0f} s, input SNR {snr:g} dB, PLI {f0} Hz")
print(f"Locked parameters: L = {L}, LMS mu = {mu['lms']}, NLMS mu = {mu['nlms']}, PLI mu = {mu_p}\n")
print(f"{'Method':<26}{'dSNR (dB)':>10}{'RMSE (mV)':>11}{'r':>8}{'R-time (ms)':>12}{'PLI att (dB)':>13}{'MACs':>6}{'time (ms)':>10}")
outs = {}
cases = [("A: BP 0.5-40 Hz", lambda: E.baseline_A(d), E.macs("A")),
         ("B: BP 0.5-100 + notch", lambda: E.baseline_B(d, f0), E.macs("B"))]
for alg in ("lms", "nlms"):
    cases += [(f"C: PLI-only {alg.upper()}", lambda a=alg: E.anc(d, None, f0=f0, mu_p=mu_p[a], alg=a)[0][0], E.macs("C", L, alg)),
              (f"D: motion-only {alg.upper()}", lambda a=alg: E.anc(d, ref, L=L, mu_m=mu[a], alg=a)[0][0], E.macs("D", L, alg)),
              (f"E: combined {alg.upper()}", lambda a=alg: E.anc(d, ref, L=L, mu_m=mu[a], f0=f0, mu_p=mu_p[a], alg=a)[0][0], E.macs("E", L, alg))]
for name, fn, mc in cases:
    t = time.perf_counter(); y = fn(); dt = (time.perf_counter() - t) * 1000
    q = E.metrics(s, y, d, ri, f0)
    outs[name] = (y, q["lag"])
    print(f"{name:<26}{q['dsnr']:>10.2f}{q['rmse']:>11.4f}{q['r']:>8.3f}{q.get('rt_err', float('nan')):>12.2f}"
          f"{q['pli_att']:>13.1f}{mc:>6}{dt:>10.1f}")

t = np.arange(E.SEG) / E.FS
i0, i1 = E.TRANS, E.TRANS + int(4 * E.FS)
show = ["A: BP 0.5-40 Hz", "B: BP 0.5-100 + notch", "E: combined NLMS"]
fig, axs = plt.subplots(len(show) + 1, 1, figsize=(10, 7), sharex=True)
axs[0].plot(t[i0:i1], d[i0:i1], c="0.6", lw=0.7, label="noisy"); axs[0].plot(t[i0:i1], s[i0:i1], "k", lw=0.8, label="clean")
for ax, k in zip(axs[1:], show):
    y, lag = outs[k]
    ax.plot(t[i0:i1], s[i0:i1], "k", lw=0.7, label="clean"); ax.plot(t[i0:i1], y[i0 + lag:i1 + lag], lw=0.8, label=k)
for ax in axs:
    ax.legend(loc="upper right", fontsize=8); ax.set_ylabel("mV")
axs[-1].set_xlabel("Time (s)")
fig.suptitle(f"Demo – record {rid}, {snr:g} dB input, {f0} Hz PLI")
plt.tight_layout(); plt.savefig("figs/demo_output.png", dpi=150)
if os.environ.get("MPLBACKEND", "").lower() != "agg":
    plt.show()
