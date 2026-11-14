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
designs = [180e-9, 270e-9]
avts = [1.5, 2.0, 3.0]                       # mV*um
vdds = [0.9, 0.8, 0.7, 0.6, 0.5, 0.4, 0.3]

def vmin_from(vdds, zs):
    order = np.argsort(vdds)
    vd = np.array(vdds)[order]
    zo = np.array(zs)[order]
    if zo.min() > z_req:
        return f"< {vd.min():.2f}", vd.min()
    if zo.max() < z_req:
        return f"> {vd.max():.2f}", vd.max()
    v = float(np.interp(z_req, zo, vd))
    return f"{v:.2f}", v

data, table = {}, {}
t0 = time.time()
for wpd in designs:
    for a in avts:
        zs = []
        for v in vdds:
            h, r = run_mc(v, N, avt=a * 1e-9, wpd=wpd, wax=WAX, wpu=WPU)
            x = r * 1000
            zs.append(x.mean() / x.std(ddof=1))
            data[f"read_wpd{wpd*1e9:.0f}_avt{a}_{v}"] = r
            print(f"Wpd {wpd*1e9:.0f} nm  A_VT {a} mV*um  VDD {v:.2f}  "
                  f"mean {x.mean():5.0f}  sd {x.std(ddof=1):4.1f}  z {zs[-1]:5.1f}  ({time.time()-t0:.0f} s)")
        table[(wpd, a)] = (vmin_from(vdds, zs), zs)
        np.savez(ROOT / "results" / "avt_data.npz", **data)

print(f"\nz needed: {z_req:.2f}")
print("Wpd (nm)   A_VT (mV*um)   Vmin (V)")
for (wpd, a), ((txt, _), _) in table.items():
    print(f"{wpd*1e9:6.0f}     {a:8.1f}       {txt}")

for wpd in designs:
    plt.plot(avts, [table[(wpd, a)][0][1] for a in avts], "o-", label=f"Wpd = {wpd*1e9:.0f} nm")
plt.xlabel("A_VT (mV*um)"); plt.ylabel("Minimum VDD for 99% yield (V)")
plt.grid(True); plt.legend()
plt.savefig(ROOT / "results" / "avt_sensitivity.png", dpi=150)
plt.show()