import numpy as np
import sram
from sram import run_mc

for pts in (200, 400):
    sram.DC_POINTS = pts
    h, r = run_mc(0.5, 100, seed=0)
    x = r * 1000
    print(f"DC points {pts}: read SNM mean {x.mean():.2f} mV, sd {x.std(ddof=1):.2f} mV")