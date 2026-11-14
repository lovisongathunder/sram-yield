import numpy as np
import matplotlib.pyplot as plt
from spicelib import RawRead

raw = RawRead("../netlists/inverter.raw")
vin  = np.array(raw.get_trace("v(in)").get_wave(0))
vout = np.array(raw.get_trace("v(out)").get_wave(0))

idx = np.argmin(np.abs(vout - vin))
print(f"Switching threshold ~ {vin[idx]:.3f} V")
print(f"Output high ~ {vout[0]:.3f} V, output low ~ {vout[-1]:.3f} V")

plt.plot(vin, vout, label="Vout")
plt.plot(vin, vin, "--", label="Vout = Vin")
plt.xlabel("Vin (V)"); plt.ylabel("Vout (V)")
plt.legend(); plt.grid(True)
plt.savefig("../results/inverter_vtc.png", dpi=150)
plt.show()