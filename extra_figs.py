"""extra_figs.py - Appendix B extra plots (run after run_draft.py):
    python3 extra_figs.py   -> figs/figB2_time_conditions.png, figs/figB3_psd_conditions.png
Same held-out segment as Figs. 6-7, shown for 0 dB/50 Hz, 12 dB/50 Hz and 6 dB/60 Hz,
with the best locked adaptive configuration. (No baseline-wander (bw) test was run.)"""
import json
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy import signal
import ecg_draft as E
import run_cfg as C

plt.rcParams.update({"font.family": "serif", "font.size": 8, "axes.grid": True, "grid.alpha": 0.3,
                     "figure.dpi": 300, "savefig.bbox": "tight"})
R = json.load(open("results/results.json"))
SM, SP = R["validation"]["motion_selected"], R["validation"]["pli_selected"]
best = max((k for k, v in SM.items() if v["mu"] is not None), key=lambda k: SM[k]["val_dsnr"])
alg, L = best.split("|")[0], int(best.split("|")[1])
rid, st, x, ri = C.example_segment()
em = C.EM[st % (len(C.EM) - E.SEG):][:E.SEG]
conds = [(0, 50), (12, 50), (6, 60)]
t = np.arange(E.SEG) / E.FS
i0, i1 = E.TRANS + int(1 * E.FS), E.TRANS + int(4 * E.FS)
fig1, ax1 = plt.subplots(len(conds), 1, figsize=(7.2, 6.0), sharex=True)
fig2, ax2 = plt.subplots(len(conds), 1, figsize=(7.2, 6.0), sharex=True)
for j, (snr, f0) in enumerate(conds):
    rng = np.random.default_rng([C.SEED, int(rid), st, int(10 * snr), f0])
    m = E.make_mixture(x, em, snr, f0, rng)
    d, s, ref = m["d"], m["s"], m["ref_m"]
    outs = {"A": E.baseline_A(d), "B": E.baseline_B(d, f0),
            f"E ({alg.upper()}, L={L})": E.anc(d, ref, L=L, mu_m=SM[best]["mu"], f0=f0, mu_p=SP[alg], alg=alg)[0][0]}
    ax1[j].plot(t[i0:i1], d[i0:i1], c="0.7", lw=0.6, label="noisy")
    ax1[j].plot(t[i0:i1], s[i0:i1], "k", lw=0.8, label="clean")
    for (k, y), c in zip(outs.items(), ["#1f4e79", "#2e8b57", "#c0504d"]):
        lag = E.best_lag(s, y)
        ax1[j].plot(t[i0:i1], y[i0 + lag:i1 + lag], c=c, lw=0.7, label=k)
    ax1[j].set_title(f"{snr} dB input, {f0} Hz PLI", fontsize=8); ax1[j].set_ylabel("mV")
    for y, k, c in [(s, "clean", "k"), (d, "noisy", "0.6")] + [(y, k, c) for (k, y), c in zip(outs.items(), ["#1f4e79", "#2e8b57", "#c0504d"])]:
        f, Pxx = signal.welch(y[E.TRANS:], E.FS, nperseg=1024)
        ax2[j].semilogy(f, Pxx, c=c, lw=0.7, label=k)
    for fz in (f0, 2 * f0, 3 * f0):
        if fz < E.FS / 2:
            ax2[j].axvline(fz, ls=":", c="k", lw=0.5)
    ax2[j].set_title(f"{snr} dB input, {f0} Hz PLI", fontsize=8); ax2[j].set_ylabel("PSD (mV²/Hz)")
ax1[0].legend(fontsize=6, ncol=5, loc="upper right"); ax1[-1].set_xlabel(f"Time (s), record {rid}, held-out segment at {st / E.FS:.0f} s")
ax2[0].legend(fontsize=6, ncol=5, loc="upper right"); ax2[-1].set_xlabel("Frequency (Hz)"); ax2[-1].set_xlim(0, 180)
fig1.tight_layout(); fig1.savefig("figs/figB2_time_conditions.png")
fig2.tight_layout(); fig2.savefig("figs/figB3_psd_conditions.png")
print("written figs/figB2_time_conditions.png and figs/figB3_psd_conditions.png")
