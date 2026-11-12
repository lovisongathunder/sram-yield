import time
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import norm
from sram import run_mc, ROOT

N = 300
CELLS = 2**20
TARGET_YIELD = 0.99
z_req = norm.isf(-np.log(TARGET_YIELD) / CELLS)

WAX = WPU = 90e-9
designs = [135e-9, 180e-9, 270e-9, 360e-9]          
vdds = [0.7, 0.6, 0.55, 0.5, 0.45, 0.4, 0.35, 0.3]

def area_proxy(wpd):
    return 2 * (wpd + WAX + WPU)
base_area = area_proxy(180e-9)

data, summary, z_curves = {}, [], {}
t0 = time.time()
for wpd in designs:
    label = f"Wpd = {wpd*1e9:.0f} nm"
    zs = []
    for v in vdds:
        h, r = run_mc(v, N, wpd=wpd, wax=WAX, wpu=WPU)
        x = r * 1000
        z = x.mean() / x.std(ddof=1)
        zs.append(z)
        data[f"read_wpd{wpd*1e9:.0f}_{v}"] = r
        print(f"{label:14s} VDD {v:.2f}  mean {x.mean():5.0f}  sd {x.std(ddof=1):4.1f}  "
              f"z {z:5.1f}   ({time.time()-t0:.0f} s)")
    np.savez(ROOT / "results" / "sizing_data.npz", **data)

    zs = np.array(zs)
    order = np.argsort(vdds)
    vd = np.array(vdds)[order]
    zo = zs[order]
    if zo.min() > z_req:
        vmin_txt, vmin = f"< {vd.min():.2f}", vd.min()
    elif zo.max() < z_req:
        vmin_txt, vmin = f"> {vd.max():.2f}", vd.max()
    else:
        vmin = float(np.interp(z_req, zo, vd))
        vmin_txt = f"{vmin:.2f}"
    summary.append((label, vmin_txt, vmin, area_proxy(wpd) / base_area))
    z_curves[label] = zs

print(f"\nz needed for {TARGET_YIELD:.0%} yield on 1 Mb: {z_req:.2f}")
print("Design           Vmin (V)   Relative width-area")
for label, vtxt, _, a in summary:
    print(f"{label:16s} {vtxt:>8s}   {a:.2f}x")

fig, axes = plt.subplots(1, 2, figsize=(11, 4.5))
for label, zs in z_curves.items():
    axes[0].plot(vdds, zs, "o-", label=label)
axes[0].axhline(z_req, color="r", ls="--", label="z needed")
axes[0].set_xlabel("VDD (V)"); axes[0].set_ylabel("z = mean / sd")
axes[0].invert_xaxis(); axes[0].grid(True); axes[0].legend()
axes[1].plot([s[3] for s in summary], [s[2] for s in summary], "o-")
axes[1].set_xlabel("Relative cell width-area (baseline = 1)")
axes[1].set_ylabel("Minimum VDD for 99% yield (V)")
axes[1].grid(True)
plt.tight_layout()
plt.savefig(ROOT / "results" / "sizing_study.png", dpi=150)
plt.show()