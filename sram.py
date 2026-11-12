import re
import subprocess, time
from pathlib import Path
import numpy as np
from spicelib import RawRead

ROOT = Path(__file__).resolve().parent.parent
MODEL = ROOT / "models" / "45nm_LP.pm"
RUNS = ROOT / "runs"
RUNS.mkdir(exist_ok=True)
DC_POINTS = 200

CANDIDATES = [
    r"E:\LTspice\LTspice.exe",
    r"C:\Program Files\ADI\LTspice\LTspice.exe",
    str(Path.home() / r"AppData\Local\Programs\ADI\LTspice\LTspice.exe"),
    r"C:\Program Files\LTC\LTspiceXVII\XVIIx64.exe",
]

def find_ltspice():
    for p in CANDIDATES:
        if Path(p).exists():
            return p
    raise FileNotFoundError("LTspice.exe not found. Add its full path to CANDIDATES in sram.py")

def snm(vin, outa, outb):
    def to_pq(x, y):
        p = (x + y) / np.sqrt(2)
        q = (y - x) / np.sqrt(2)
        order = np.argsort(q)
        return p[order], q[order]
    pA, qA = to_pq(vin, outa)
    pB, qB = to_pq(outb, vin)
    q = np.linspace(max(qA.min(), qB.min()), min(qA.max(), qB.max()), 4000)
    d = np.interp(q, qA, pA) - np.interp(q, qB, pB)
    eye1 = max(d.max(), 0) / np.sqrt(2)
    eye2 = max((-d).max(), 0) / np.sqrt(2)
    return min(eye1, eye2)

def build_netlist(vdd, wpd=180e-9, wax=90e-9, wpu=90e-9, L=45e-9):
    step = vdd / 200
    return f"""* auto-generated 6T SRAM butterfly
.include "{MODEL}"
.param wlv=0
Vdd vdd 0 {vdd}
Vwl wl 0 {{wlv}}
Vs in 0 0
Mpd_a outa in 0 0 nmos W={wpd} L={L}
Mpu_a outa in vdd vdd pmos W={wpu} L={L}
Max_a vdd wl outa 0 nmos W={wax} L={L}
Mpd_b outb in 0 0 nmos W={wpd} L={L}
Mpu_b outb in vdd vdd pmos W={wpu} L={L}
Max_b vdd wl outb 0 nmos W={wax} L={L}
.step param wlv list 0 {vdd}
.dc Vs 0 {vdd} {step}
.end
"""

def run_ltspice(cir):
    raw = cir.with_suffix(".raw")
    if raw.exists():
        raw.unlink()
    subprocess.run([find_ltspice(), "-b", str(cir)], timeout=300)
    t0 = time.time()
    while not raw.exists() and time.time() - t0 < 30:
        time.sleep(0.2)
    time.sleep(0.3)
    if not raw.exists():
        raise RuntimeError(f"No raw file produced. Check {cir.with_suffix('.log')}")
    return raw

def measure(vdd, **sizes):
    cir = RUNS / "run.cir"
    cir.write_text(build_netlist(vdd, **sizes))
    raw = RawRead(str(run_ltspice(cir)))
    results = []
    for s in list(raw.get_steps()):
        vin  = np.array(raw.get_trace("v(in)").get_wave(s))
        outa = np.array(raw.get_trace("v(outa)").get_wave(s))
        outb = np.array(raw.get_trace("v(outb)").get_wave(s))
        results.append(snm(vin, outa, outb))
    del raw
    return results[0], results[1]   # hold SNM, read SNM (volts)

def _load_cards():
    parts = re.split(r"(?m)^(?=\.model)", MODEL.read_text())
    cards = {}
    for p in parts:
        m = re.match(r"\.model\s+(\w+)\s+(\w+)", p)
        if m:
            cards[m.group(2).lower()] = p
    return cards["nmos"], cards["pmos"]

NMOS_CARD, PMOS_CARD = _load_cards()
AVT = 2.0e-9   # V*m  (= 2.0 mV*um), assumed value

def sigma_vth(w, l, avt=AVT):
    return avt / np.sqrt(w * l)

def _card(kind, name, dvth):
    base = NMOS_CARD if kind == "nmos" else PMOS_CARD
    c = re.sub(r"^\.model\s+\w+\s+(\w+)", rf".model {name} \1", base, count=1)
    return re.sub(r"vth0\s*=\s*([-+\d.eE]+)",
                  lambda m: f"vth0 = {float(m.group(1)) + dvth:.6f}", c, count=1)

def build_mc_netlist(vdd, dvth, wpd=180e-9, wax=90e-9, wpu=90e-9, L=45e-9):
    lines = ["* Monte Carlo 6T SRAM", ".param wlv=0",
             f"Vdd vdd 0 {vdd}", "Vwl wl 0 {wlv}", "Vs in 0 0"]
    for k, d in enumerate(dvth):
        devs = [
            ("pda", "nmos", wpd, f"outa{k} in 0 0"),
            ("pua", "pmos", wpu, f"outa{k} in vdd vdd"),
            ("axa", "nmos", wax, f"vdd wl outa{k} 0"),
            ("pdb", "nmos", wpd, f"outb{k} in 0 0"),
            ("pub", "pmos", wpu, f"outb{k} in vdd vdd"),
            ("axb", "nmos", wax, f"vdd wl outb{k} 0"),
        ]
        for (tag, kind, w, nodes), dv in zip(devs, d):
            name = f"{tag}_{k}"
            lines.append(f"M{name} {nodes} {name} W={w} L={L}")
            lines.append(_card(kind, name, dv))
    lines += [f".step param wlv list 0 {vdd}", f".dc Vs 0 {vdd} {vdd/DC_POINTS}", ".end"]
    return "\n".join(lines) + "\n"

def measure_mc(vdd, dvth, **sizes):
    cir = RUNS / "mc.cir"
    cir.write_text(build_mc_netlist(vdd, dvth, **sizes))
    raw = RawRead(str(run_ltspice(cir)))
    steps = list(raw.get_steps())
    hold, read = [], []
    for k in range(len(dvth)):
        row = []
        for s in steps:
            vin  = np.array(raw.get_trace("v(in)").get_wave(s))
            outa = np.array(raw.get_trace(f"v(outa{k})").get_wave(s))
            outb = np.array(raw.get_trace(f"v(outb{k})").get_wave(s))
            row.append(snm(vin, outa, outb))
        hold.append(row[0]); read.append(row[1])
    del raw
    return np.array(hold), np.array(read)

def sample_dvth(n, rng, wpd=180e-9, wax=90e-9, wpu=90e-9, L=45e-9, avt=AVT):
    widths = (wpd, wpu, wax, wpd, wpu, wax)      # pda pua axa pdb pub axb
    sig = np.array([sigma_vth(w, L, avt) for w in widths])
    return rng.normal(0, 1, (n, 6)) * sig

def run_mc(vdd, n, batch=20, seed=0, avt=AVT, **sizes):
    rng = np.random.default_rng(seed)
    hold, read = [], []
    for i in range(0, n, batch):
        dv = sample_dvth(min(batch, n - i), rng, avt=avt, **sizes)
        h, r = measure_mc(vdd, dv, **sizes)
        hold.append(h); read.append(r)
    return np.concatenate(hold), np.concatenate(read)