import numpy as np
from spicelib import RawRead

def snm(vin, outa, outb):
    def to_pq(x, y):
        p = (x + y) / np.sqrt(2)      # along the diagonal
        q = (y - x) / np.sqrt(2)      # across the diagonal
        order = np.argsort(q)
        return p[order], q[order]

    pA, qA = to_pq(vin, outa)
    pB, qB = to_pq(outb, vin)

    q = np.linspace(max(qA.min(), qB.min()), min(qA.max(), qB.max()), 4000)
    d = np.interp(q, qA, pA) - np.interp(q, qB, pB)

    eye1 = max(d.max(), 0) / np.sqrt(2)
    eye2 = max((-d).max(), 0) / np.sqrt(2)
    return min(eye1, eye2), eye1, eye2

raw = RawRead("../netlists/sram_butterfly.raw")
steps = list(raw.get_steps())

for s, name in zip(steps, ["Hold", "Read"]):
    vin  = np.array(raw.get_trace("v(in)").get_wave(s))
    outa = np.array(raw.get_trace("v(outa)").get_wave(s))
    outb = np.array(raw.get_trace("v(outb)").get_wave(s))
    m, e1, e2 = snm(vin, outa, outb)
    print(f"{name}: SNM = {m*1000:.0f} mV  (eye 1: {e1*1000:.0f} mV, eye 2: {e2*1000:.0f} mV)")