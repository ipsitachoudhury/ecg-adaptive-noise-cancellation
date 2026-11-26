"""make_figs_draft.py - draws every report figure from results/results.json.
Run after run_draft.py:   python3 make_figs_draft.py
File names match the report's figure numbers (figs/fig01_... to figs/fig11_...).
Fig. 4 (demo screenshot) is a screenshot of demo_draft.py, not a generated plot."""
import json, os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker
from matplotlib.patches import FancyBboxPatch
from scipy import signal
import ecg_draft as E
import run_cfg

os.makedirs("figs", exist_ok=True)
plt.rcParams.update({"font.family": "serif", "font.size": 9, "axes.grid": True, "grid.alpha": 0.3,
                     "figure.dpi": 200, "savefig.bbox": "tight"})
R = json.load(open("results/results.json"))
C1, C2, C3, C4, C5 = "#1f4e79", "#2e8b57", "#c0504d", "#e69f00", "#7f7f7f"
LS = R["config"]["Ls"]
SEL_M, SEL_P = R["validation"]["motion_selected"], R["validation"]["pli_selected"]


def box(ax, x, y, w, h, t, fc, fs=7):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02", fc=fc, ec="#333", lw=0.8))
    ax.text(x + w / 2, y + h / 2, t, ha="center", va="center", fontsize=fs)


def arrow(ax, a, b):
    ax.annotate("", b, a, arrowprops=dict(arrowstyle="->", lw=0.8))


# ---------------------------------------------------------------- Fig 1 methodology flow
fig, ax = plt.subplots(figsize=(7.2, 2.4)); ax.axis("off"); ax.set_xlim(0, 12); ax.set_ylim(0, 3.4)
rows = [["Problem\ncontext", "Literature\nreview", "Research\ngap", "Research\nquestion"],
        ["MIT-BIH ECG +\nNSTDB em + PLI", "Pre-processing,\nexact SNR scaling", "Fixed baselines\nA, B", "Adaptive branches\nC, D, E (LMS/NLMS)"],
        ["Validation sweep\n(L, μ)", "Locked held-out\nevaluation", "Quality, QRS,\ncost metrics", "Comparison &\nconclusions"]]
for r, (row, fc) in enumerate(zip(rows, ["#dbe8f5", "#dff0e3", "#fbe5d6"])):
    y = 2.4 - r * 1.1
    for c, t in enumerate(row):
        box(ax, 0.15 + c * 3.0, y, 2.5, 0.8, t, fc)
        if c < 3:
            arrow(ax, (2.65 + c * 3.0, y + 0.4), (3.15 + c * 3.0, y + 0.4))
    if r < 2:
        arrow(ax, (10.4, y), (1.4, y - 0.3))
plt.savefig("figs/fig01_methodology_flow.png"); plt.close()

# ---------------------------------------------------------------- Fig 2 block diagram
fig, ax = plt.subplots(figsize=(7.2, 3.4)); ax.axis("off"); ax.set_xlim(0, 16); ax.set_ylim(0, 6.4)
W, H = 2.5, 0.9
_b = box
box = lambda ax, x, y, w, h, t, fc: _b(ax, x, y, w, h, t, fc, fs=6.3)
box(ax, 0.1, 4.8, W, H, "Clean ECG s[n]\n(MIT-BIH)", "#dbe8f5")
box(ax, 0.1, 3.3, W, H, "em noise\n(NSTDB)", "#dff0e3")
box(ax, 0.1, 1.8, W, H, "Synthetic PLI\n50/60 Hz", "#fbe5d6")
box(ax, 3.3, 3.3, W, H, "Sum + one gain\n(exact SNR)", "#fff")
box(ax, 6.5, 4.8, W, H, "A: band-pass\n0.5–40 Hz", "#dbe8f5")
box(ax, 6.5, 3.3, W, H, "B: 0.5–100 Hz\n+ notch", "#dbe8f5")
box(ax, 6.5, 1.8, W, H, "Band-pass\n0.5–100 Hz", "#dbe8f5")
box(ax, 6.5, 0.3, W, H, "Band-pass\n(reference)", "#dff0e3")
box(ax, 9.7, 3.3, W, H, "C: PLI canceller\nsin/cos ref.", "#fbe5d6")
box(ax, 9.7, 1.8, W, H, "e = d − y_p − y_m", "#fff")
box(ax, 9.7, 0.3, W, H, "D: motion\ncanceller, L taps", "#dff0e3")
box(ax, 12.9, 2.3, 3.0, 2.0, "Align, drop 1 s,\nscore vs s[n]:\nΔSNR, RMSE, r,\nQRS, MACs", "#f2f2f2")
for a_, b_ in [((2.6, 5.25), (3.3, 4.1)), ((2.6, 3.75), (3.3, 3.75)), ((2.6, 2.25), (3.3, 3.4)),
               ((5.8, 3.75), (6.5, 5.25)), ((5.8, 3.75), (6.5, 3.75)), ((5.8, 3.75), (6.5, 2.25)),
               ((1.35, 3.3), (6.5, 0.75)), ((9.0, 2.25), (9.7, 2.25)), ((9.0, 0.75), (9.7, 0.75)),
               ((10.95, 1.2), (10.95, 1.8)), ((10.95, 3.3), (10.95, 2.7)), ((12.2, 2.25), (12.9, 2.9)),
               ((9.0, 5.25), (12.9, 3.9)), ((9.0, 3.75), (12.9, 3.5))]:
    arrow(ax, a_, b_)
ax.text(3.3, 6.0, "Every branch receives the same noisy d[n]; motion reference x_m[n] = em proxy", fontsize=7, style="italic")
ax.text(11.05, 2.95, "y_p", fontsize=6.5); ax.text(11.05, 1.35, "y_m", fontsize=6.5)
plt.savefig("figs/fig02_block_diagram.png"); plt.close()
box = _b

# ---------------------------------------------------------------- Fig 3 algorithm flowchart
fig, ax = plt.subplots(figsize=(4.6, 6.4)); ax.axis("off"); ax.set_xlim(0, 6); ax.set_ylim(0, 12)
steps = ["Load ECG record, annotations, em; check Fs = 360 Hz",
         "Select clean 10 s segment (3600 samples)",
         "Build references: sin/cos at f0; em proxy",
         "Set PLI:motion ratio, scale to SNR (eq. 3)",
         "Run A, B (causal SOS) and C, D, E (LMS/NLMS)",
         "Per sample: y = wᵀx, e = d − y, update w",
         "Instability rule: non-finite / ‖w‖ runaway /\noutput power > input power",
         "Align delay, exclude 1 s, compute metrics",
         "Validation: pick μ per (alg, L) → lock",
         "Held-out test once with locked parameters"]
for i, t in enumerate(steps):
    y = 11.0 - i * 1.15
    box(ax, 0.3, y, 5.4, 0.8, t, "#fbe5d6" if i == 6 else ("#dff0e3" if i >= 8 else "#dbe8f5"), fs=6.8)
    if i < len(steps) - 1:
        arrow(ax, (3.0, y), (3.0, y - 0.35))
plt.savefig("figs/fig03_algorithm_flowchart.png"); plt.close()

# ---------------------------------------------------------------- Fig 5 filter responses
fig, axs = plt.subplots(1, 2, figsize=(7.2, 2.4))
for sos, lab, c in [(E.SOS_A, "A: BP 0.5–40 Hz", C1), (E.SOS_W, "B: BP 0.5–100 Hz", C2)]:
    w, h = signal.sosfreqz(sos, 2 ** 15, fs=E.FS)
    axs[0].semilogx(w[1:], 20 * np.log10(abs(h[1:]) + 1e-12), c=c, label=lab)
for f0 in (50, 60):
    axs[0].axvline(f0, ls=":", c="k", lw=0.7)
axs[0].set(ylim=(-60, 3), xlabel="Frequency (Hz)", ylabel="|H| (dB)", title="(a) Band-pass filters"); axs[0].legend(fontsize=6)
for Q, c in [(20, C1), (30, C2), (40, C3)]:
    w, h = signal.sosfreqz(E.notch(50, Q), 2 ** 16, fs=E.FS)
    axs[1].plot(w, 20 * np.log10(abs(h) + 1e-12), c=c, label=f"Q = {Q}")
axs[1].set(xlim=(44, 56), ylim=(-40, 2), xlabel="Frequency (Hz)", title="(b) 50 Hz IIR notch"); axs[1].legend(fontsize=6)
plt.tight_layout(); plt.savefig("figs/fig05_filter_responses.png"); plt.close()

# ---------------------------------------------------------------- example segment (Figs 6, 7)
seg = run_cfg.example_segment()
rid, st, x, ri = seg
rng = np.random.default_rng([run_cfg.SEED, int(rid), st, 60, 50])
em = run_cfg.EM[st % (len(run_cfg.EM) - E.SEG):][:E.SEG]
m = E.make_mixture(x, em, 6, 50, rng)
d, s, ref = m["d"], m["s"], m["ref_m"]
yA, yB = E.baseline_A(d), E.baseline_B(d, 50)
# best locked adaptive configuration (highest validation ΔSNR among stable settings)
_best = max((k for k, v in SEL_M.items() if v["mu"] is not None), key=lambda k: SEL_M[k]["val_dsnr"])
alg, LE = _best.split("|")[0], int(_best.split("|")[1])
yE = E.anc(d, ref, L=LE, mu_m=SEL_M[f"{alg}|{LE}"]["mu"], f0=50, mu_p=SEL_P[alg], alg=alg)[0][0]
lag = {k: E.best_lag(s, y) for k, y in [("A", yA), ("B", yB), ("E", yE)]}
t = np.arange(E.SEG) / E.FS
i0 = int(E.TRANS + 1.0 * E.FS); i1 = i0 + int(4 * E.FS)
fig, axs = plt.subplots(4, 1, figsize=(7.2, 5.0), sharex=True)
axs[0].plot(t[i0:i1], d[i0:i1], c="#999", lw=0.6, label="noisy d[n] (6 dB)")
axs[0].plot(t[i0:i1], s[i0:i1], c="k", lw=0.8, label="clean s[n]")
for ax, y, k, lab, c in [(axs[1], yA, "A", "A: BP 0.5–40 Hz", C1), (axs[2], yB, "B", "B: BP 0.5–100 Hz + notch", C2),
                         (axs[3], yE, "E", f"E: {alg.upper()}, L = {LE}", C3)]:
    ax.plot(t[i0:i1], s[i0:i1], c="k", lw=0.7, label="clean")
    ax.plot(t[i0:i1], y[i0 + lag[k]:i1 + lag[k]], c=c, lw=0.8, label=lab)
for ax in axs:
    ax.legend(fontsize=6.5, loc="upper right", ncol=2); ax.set_ylabel("mV")
beat = [r for r in ri if i0 + 30 < r < i1 - 60]
if beat:
    b0, w_ = beat[0], int(0.15 * E.FS)
    ins = axs[3].inset_axes([0.02, 0.5, 0.2, 0.46]); tt = np.arange(-w_, w_) / E.FS * 1000
    ins.plot(tt, s[b0 - w_:b0 + w_], "k", lw=0.8)
    ins.plot(tt, yE[b0 - w_ + lag["E"]:b0 + w_ + lag["E"]], c=C3, lw=0.8)
    ins.plot(tt, yA[b0 - w_ + lag["A"]:b0 + w_ + lag["A"]], c=C1, lw=0.6, ls="--")
    ins.tick_params(labelsize=5); ins.set_title("QRS ±150 ms", fontsize=5.5)
axs[-1].set_xlabel(f"Time (s) – record {rid}, segment starting at {st / E.FS:.0f} s (held-out), delay-aligned")
plt.tight_layout(); plt.savefig("figs/fig06_time_domain.png"); plt.close()

fig, ax = plt.subplots(figsize=(7.2, 2.5))
for y, lab, c in [(s, "clean", "k"), (d, "noisy", "#999"), (yA, "A", C1), (yB, "B", C2), (yE, f"E ({alg.upper()}, L={LE})", C3)]:
    f, P = signal.welch(y[E.TRANS:], E.FS, nperseg=1024)
    ax.semilogy(f, P, c=c, lw=0.8, label=lab)
for fz in (50, 100, 150):
    ax.axvline(fz, ls=":", c="k", lw=0.6)
ax.set(xlim=(0, 180), xlabel="Frequency (Hz)", ylabel="PSD (mV²/Hz)"); ax.legend(fontsize=7, ncol=5)
plt.savefig("figs/fig07_psd.png"); plt.close()

# ---------------------------------------------------------------- Fig 8 ΔSNR vs L
fig, ax = plt.subplots(figsize=(7.2, 2.5))
for snr, ls in [(0, "-"), (6, "--"), (12, ":")]:
    for alg, c in [("lms", C1), ("nlms", C3)]:
        T = R["test"][f"{snr}|50"]
        v = [T[f"E|{alg}|{L}"]["dsnr"][0] if f"E|{alg}|{L}" in T else np.nan for L in LS]
        ax.plot(LS, v, ls=ls, marker="o", ms=3, c=c, label=f"{alg.upper()}, {snr} dB")
ax.set(xscale="log", xlabel="Motion filter length L (taps)", ylabel="ΔSNR (dB)")
ax.set_xticks(LS); ax.set_xticklabels([str(L) for L in LS]); ax.xaxis.set_minor_formatter(matplotlib.ticker.NullFormatter())
ax.legend(fontsize=6.5, ncol=3)
plt.savefig("figs/fig08_dsnr_vs_L.png"); plt.close()

# ---------------------------------------------------------------- Fig 9 learning curves
D, S, Rm = run_cfg.test_batch(6, 50, n=min(20, len(run_cfg.TEST)))
Sf = E.causal(E.SOS_W, S)
win = np.ones(int(0.25 * E.FS)) / int(0.25 * E.FS)
fig, ax = plt.subplots(figsize=(7.2, 2.4))
base = np.mean([np.convolve((E.causal(E.SOS_W, D[i]) - Sf[i]) ** 2, win, "same") for i in range(len(D))], 0)
ax.plot(t, 10 * np.log10(base), c="#999", lw=0.8, label="no cancellation (band-passed input)")
for alg, c in [("lms", C1), ("nlms", C3)]:
    mu = SEL_M[f"{alg}|16"]["mu"]
    if mu is None:
        continue
    Y = E.anc(D, Rm, L=16, mu_m=mu, f0=50, mu_p=SEL_P[alg], alg=alg)[0]
    mse = np.mean([np.convolve((Y[i] - Sf[i]) ** 2, win, "same") for i in range(len(Y))], 0)
    ax.plot(t, 10 * np.log10(mse), c=c, lw=0.9, label=f"E {alg.upper()}, L = 16, μ = {mu}")
ax.axvspan(0, E.TRANS / E.FS, color="k", alpha=0.08); ax.text(0.05, ax.get_ylim()[1] - 2, "excluded", fontsize=7)
ax.set(xlabel="Time (s)", ylabel="Squared error (dB, mV²)", xlim=(0, 10)); ax.legend(fontsize=7, loc="upper right")
plt.savefig("figs/fig09_learning_curves.png"); plt.close()

# ---------------------------------------------------------------- Fig 10 Pareto
T = R["test"]["6|50"]; cost = R["cost"]
pts = [("A", "A", cost["A"]["macs_lms"], C1), ("B", "B", cost["B"]["macs_lms"], C2),
       ("C LMS", "C|lms", cost["C"]["macs_lms"], C5), ("C NLMS", "C|nlms", cost["C"]["macs_nlms"], C5)]
for L in LS:
    for alg, c in [("lms", C1), ("nlms", C3)]:
        pts.append((f"E {alg.upper()} {L}", f"E|{alg}|{L}", cost[f"E|{L}"][f"macs_{alg}"], c))
fig, ax = plt.subplots(figsize=(7.2, 2.8))
for lab, k, mc, c in pts:
    if k in T:
        ax.errorbar(mc, T[k]["dsnr"][0], yerr=T[k]["dsnr"][1], fmt="o", c=c, ms=4, capsize=2)
        off = {"B": (-10, 6), "C LMS": (5, -9), "C NLMS": (5, 3)}.get(lab, (4, 3))
        ax.annotate(lab, (mc, T[k]["dsnr"][0]), textcoords="offset points", xytext=off, fontsize=6)
ax.set(xscale="log", xlabel="Estimated MACs per sample (log)", ylabel="ΔSNR (dB)",
       title="Held-out, 6 dB input, 50 Hz (mean ± s.d.)")
plt.savefig("figs/fig10_pareto.png"); plt.close()

# ---------------------------------------------------------------- Fig 11 reference stress
t6 = R["T6_reference_stress"]
fig, axs = plt.subplots(1, 2, figsize=(7.2, 2.5))
gs, rhos = [0.1, 0.316, 1.0, 3.16, 10.0], [1.0, 0.9, 0.7, 0.5, 0.3]
for alg, c in [("lms", C1), ("nlms", C3)]:
    for ax, kind, xs, xv in [(axs[0], "gain", gs, 20 * np.log10(gs)), (axs[1], "corr", rhos, rhos)]:
        v = [np.nan if t6[kind][f"{x}|{alg}"]["unstable"] else t6[kind][f"{x}|{alg}"]["dsnr"][0] for x in xs]
        ax.plot(xv, v, "o-", ms=3, c=c, label=alg.upper())
        for xx, vv in zip(xv, v):
            if np.isnan(vv):
                ax.plot(xx, 0, "x", c=c, ms=7)
axs[0].set(xlabel="Reference gain change (dB)", ylabel="ΔSNR (dB)", title="(a) Reference amplitude")
axs[1].set(xlabel="Correlation ρ between reference and em", title="(b) Reference correlation"); axs[1].invert_xaxis()
for ax in axs:
    ax.legend(fontsize=7)
fig.text(0.5, -0.02, "× = setting rejected by the instability rule", ha="center", fontsize=7)
plt.tight_layout(); plt.savefig("figs/fig11_reference_stress.png"); plt.close()

# ---------------------------------------------------------------- Appendix: validation sweep
fig, axs = plt.subplots(1, 2, figsize=(7.2, 2.4), sharey=True)
sw = R["validation"]["motion_sweep"]
for ax, alg in zip(axs, ["lms", "nlms"]):
    for L, c in zip(LS, [C1, C2, C4, C3]):
        ks = sorted((k for k in sw if k.startswith(f"{alg}|{L}|")), key=lambda k: float(k.split("|")[2]))
        mus = [float(k.split("|")[2]) for k in ks]
        v = [sw[k]["dsnr"] if sw[k]["dsnr"] is not None else np.nan for k in ks]
        ax.semilogx(mus, v, "o-", ms=3, c=c, label=f"L = {L}")
    ax.set(xlabel="Step size μ", title=f"{alg.upper()} (validation, mean of 0/6/12 dB)"); ax.legend(fontsize=6)
axs[0].set_ylabel("ΔSNR (dB)")
plt.tight_layout(); plt.savefig("figs/figB1_validation_sweep.png"); plt.close()
print("figures written to figs/")
