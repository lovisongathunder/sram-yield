import numpy as np
import matplotlib.pyplot as plt
from spicelib import RawRead

raw = RawRead("../netlists/sram_butterfly.raw")
steps = raw.get_steps()
print("steps:", steps)          # expect [0, 1]

titles = ["Hold (WL = 0)", "Read (WL = VDD)"]
fig, axes = plt.subplots(1, 2, figsize=(10, 5))
for s, ax, title in zip(steps, axes, titles):
    vin  = np.array(raw.get_trace("v(in)").get_wave(s))
    outa = np.array(raw.get_trace("v(outa)").get_wave(s))
    outb = np.array(raw.get_trace("v(outb)").get_wave(s))
    ax.plot(vin, outa, label="QB vs Q")
    ax.plot(outb, vin, label="Q vs QB")
    ax.set_title(title)
    ax.set_xlabel("Q (V)"); ax.set_ylabel("QB (V)")
    ax.set_aspect("equal"); ax.grid(True); ax.legend()
plt.tight_layout()
plt.savefig("../results/butterfly.png", dpi=150)
plt.show()