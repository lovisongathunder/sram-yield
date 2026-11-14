import matplotlib.pyplot as plt
from sram import measure, ROOT

vdds = [1.1, 1.0, 0.9, 0.8, 0.7, 0.6, 0.5, 0.4, 0.3]
hold, read = [], []
for v in vdds:
    h, r = measure(v)
    hold.append(h * 1000); read.append(r * 1000)
    print(f"VDD = {v:.2f} V   hold SNM = {h*1000:.0f} mV   read SNM = {r*1000:.0f} mV")

plt.plot(vdds, hold, "o-", label="Hold SNM")
plt.plot(vdds, read, "s-", label="Read SNM")
plt.xlabel("VDD (V)"); plt.ylabel("SNM (mV)")
plt.gca().invert_xaxis(); plt.grid(True); plt.legend()
plt.savefig(ROOT / "results" / "snm_vs_vdd.png", dpi=150)
plt.show()