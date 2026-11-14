import time
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import norm, skew
from sram import run_mc, ROOT

N = 300                     
CELLS = 2**20                
TARGET_YIELD = 0.99
vdds = [1.1, 0.9, 0.8, 0.7, 0.6, 0.5, 0.4]

z_req = norm.isf(-np.log(TARGET_YIELD) / CELLS)
print(f"z needed for {TARGET_YIELD:.0%} yield on 1 Mb: {z_req:.2f}")
print("VDD    mean   sd    min   z     skew   P_cell_fail   yield_1Mb")

data, mu_l, sd_l, z_l = {}, [], [], []
t0 = time.time()
for v in vdds:
    h, r = run_mc(v, N)
    data[f"hold_{v}"] = h
    data[f"read_{v}"] = r
    x = r * 1000
    mu, sd = x.mean(), x.std(ddof=1)
    z = mu / sd
    p = norm.sf(z)
    y = np.exp(-CELLS * p)
    mu_l.append(mu); sd_l.append(sd); z_l.append(z)
    print(f"{v:.2f}  {mu:5.0f}  {sd:4.1f}  {x.min():4.0f}  {z:4.1f}  {skew(x):+.2f}  "
          f"{p:.2e}   {y:.4f}    ({time.time()-t0:.0f} s elapsed)")

np.savez(ROOT / "results" / "mc_data.npz", **data)

vd, z_a = np.array(vdds), np.array(z_l)
order = np.argsort(vd)
vmin = np.interp(z_req, z_a[order], vd[order])
print(f"\nEstimated minimum VDD for {TARGET_YIELD:.0%} yield on 1 Mb: ~{vmin:.2f} V")

fig, axes = plt.subplots(1, 2, figsize=(11, 4.5))
axes[0].errorbar(vdds, mu_l, yerr=3 * np.array(sd_l), fmt="o-", capsize=4)
axes[0].axhline(0, color="k", lw=1)
axes[0].set_xlabel("VDD (V)"); axes[0].set_ylabel("Read SNM (mV), mean ± 3 sd")
axes[1].plot(vdds, z_l, "o-")
axes[1].axhline(z_req, color="r", ls="--", label=f"z = {z_req:.1f} (99% yield, 1 Mb)")
axes[1].set_xlabel("VDD (V)"); axes[1].set_ylabel("z = mean / sd"); axes[1].legend()
for ax in axes:
    ax.invert_xaxis(); ax.grid(True)
plt.tight_layout()
plt.savefig(ROOT / "results" / "yield_vs_vdd.png", dpi=150)
plt.show()