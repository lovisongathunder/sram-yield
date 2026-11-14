import numpy as np
import matplotlib.pyplot as plt
from sram import measure_mc, run_mc, sigma_vth, ROOT

print("Vth sigma (A_VT = 2.0 mV*um):")
print(f"  pull-down, W=180n: {sigma_vth(180e-9, 45e-9)*1000:.1f} mV")
print(f"  pull-up / access, W=90n: {sigma_vth(90e-9, 45e-9)*1000:.1f} mV")

h, r = measure_mc(1.1, np.zeros((2, 6)))
print(f"Zero-variation check at 1.1 V: hold {h[0]*1000:.0f} mV, read {r[0]*1000:.0f} mV (expect 457 / 268)")

fig, axes = plt.subplots(1, 2, figsize=(10, 4))
for vdd, ax in zip((1.1, 0.6), axes):
    h, r = run_mc(vdd, 100)
    h, r = h * 1000, r * 1000
    print(f"VDD = {vdd} V: hold mean {h.mean():.0f} sd {h.std():.0f} mV | "
          f"read mean {r.mean():.0f} sd {r.std():.0f} min {r.min():.0f} mV | "
          f"read fails (SNM < 1 mV): {(r < 1).sum()} of {len(r)}")
    ax.hist(r, bins=20)
    ax.set_title(f"Read SNM, VDD = {vdd} V (100 cells)")
    ax.set_xlabel("Read SNM (mV)"); ax.set_ylabel("Number of cells")
plt.tight_layout()
plt.savefig(ROOT / "results" / "snm_histograms.png", dpi=150)
plt.show()