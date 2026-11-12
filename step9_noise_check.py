import numpy as np
from scipy.stats import norm
from sram import run_mc, ROOT

CELLS = 2**20
z_req = norm.isf(-np.log(0.99) / CELLS)
vdds = [0.9, 0.8, 0.7, 0.6, 0.5, 0.4, 0.3]

def vmin(zs):
    order = np.argsort(vdds)
    vd = np.array(vdds)[order]; zo = np.array(zs)[order]
    return float(np.interp(z_req, zo, vd))

d = np.load(ROOT / "results" / "avt_data.npz")
reads = {v: d[f"read_wpd180_avt2.0_{v}"] * 1000 for v in vdds}
rng = np.random.default_rng(1)
vm = []
for _ in range(2000):
    zs = []
    for v in vdds:
        x = rng.choice(reads[v], size=len(reads[v]), replace=True)
        zs.append(x.mean() / x.std(ddof=1))
    vm.append(vmin(zs))
lo, hi = np.percentile(vm, [2.5, 97.5])
print(f"Bootstrap Vmin (baseline, A_VT 2.0): median {np.median(vm):.3f} V, 95% CI [{lo:.3f}, {hi:.3f}] V")

for seed in (1, 2):
    zs = []
    for v in vdds:
        h, r = run_mc(v, 300, seed=seed)
        x = r * 1000
        zs.append(x.mean() / x.std(ddof=1))
    print(f"Seed {seed}: Vmin = {vmin(zs):.3f} V")