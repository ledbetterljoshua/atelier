"""Forty for Zisis Vergos, dyer. Ninth day.

Dye on paper, hung by two pegs beside a west window for forty days.
The slow things are painted whole and first: the chair, the coat, the table, the cup.
The quick things are painted round him: the wall, the floor.
He goes on last, in the dyes that leave soonest.

    uv run python artists/thomai-vergou/works/001-forty-for-zisis-vergos/paint.py
"""
import base64
import io
import json
import sys
import time
from pathlib import Path

import numpy as np
from PIL import Image
from scipy.ndimage import gaussian_filter

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1]))
from dye import DYES, ORDER, PAPER, TEA, TEA_YIELD, Sheet, band, blob, poly  # noqa: E402

t0 = time.time()
U = 16
W, H = 100 * U, 125 * U
sh = Sheet(W, H, U, seed=1958)

# ------------------------------------------------------------------ the light in the room
# The window is to the left of where it hangs. Two pegs hold it to the string.
xx = np.linspace(0, 1, W, dtype=np.float32)[None, :]
light = (1.13 - 0.28 * xx) * (0.97 + 0.06 * sh.size)
pegs = np.zeros((H, W), np.float32)
for px in (19.0, 77.6):
    pegs[0:int(5.2 * U), int(px * U):int((px + 3.4) * U)] = 1
pegs = gaussian_filter(pegs, 1.6)
light = light * (1 - 0.985 * pegs)

# ------------------------------------------------------------------ him: shapes first, so the
# wall can be painted round them
head = blob([(53.6, 23.2), (57.2, 21.6), (61.4, 21.8), (64.6, 24.2), (65.8, 28.2), (65.2, 32.2),
             (63.8, 35.2), (62.6, 36.6), (59.2, 37.2), (56.0, 38.2), (53.8, 38.3), (52.3, 37.4),
             (52.25, 36.1), (51.6, 35.4), (51.95, 34.75), (51.35, 34.1), (51.9, 33.1), (50.2, 32.5),
             (49.9, 31.6), (51.3, 29.4), (51.9, 28.0), (51.6, 26.9), (52.2, 25.0)], n=6)
neck = poly([(56.8, 37.4), (63.6, 36.0), (64.2, 40.4), (57.4, 41.6)])
vest = blob([(57.8, 42.4), (55.2, 47.5), (53.7, 56), (53.8, 66), (54.4, 71.8), (63, 73.2), (71.5, 73.8),
             (72.2, 66), (72.4, 57), (71.4, 49.5), (68.8, 44.2), (65.0, 41.4)], n=8)
collar = blob([(56.6, 40.0), (60.5, 39.0), (64.6, 38.4), (65.4, 41.4), (61.0, 42.0), (59.0, 46.4), (57.4, 43.2)], n=6)
sleeve = band([(65.4, 46.6), (61.6, 55), (57.8, 63.4)], [7.8, 7.0, 6.4])
forearm = band([(57.2, 64.2), (48, 62.2), (41.2, 60.4)], [5.3, 4.4, 3.0])
hand = blob([(41.0, 58.9), (38.6, 58.2), (35.6, 57.5), (33.6, 58.0), (31.0, 59.2), (28.6, 60.2), (28.0, 60.8), (28.7, 61.3),
             (32, 61.2), (36, 61.5), (41.0, 62.0)], n=8)
thigh = blob([(71.4, 73.0), (72.2, 79.6), (70.8, 80.6), (50, 80.3), (36, 80.8), (31.2, 80.4), (29.8, 76.6),
              (31.6, 72.7), (40, 71.7), (54.4, 71.3)], n=8)
shin = band([(34.2, 78), (35.4, 92), (36.6, 105.4)], [7.0, 6.0, 5.0])
shin2 = band([(30.2, 79), (27.0, 91), (23.4, 103.0)], [5.6, 5.0, 4.4])
shoe = blob([(26.6, 111.8), (27.0, 109.6), (29.8, 107.0), (34.4, 105.4), (39.6, 105.6), (40.4, 109.4),
             (40.2, 112.0), (33, 112.0)], n=8)
shoe2 = blob([(12.4, 109.6), (12.8, 107.6), (15.6, 105.2), (20.4, 103.2), (25.6, 103.2), (26.6, 106.8),
              (26.4, 109.8), (19, 109.8)], n=8)

M = {k: sh.mask(v, wobble=w) for k, (v, w) in {
    "head": (head, 0.12), "neck": (neck, 0.2), "vest": (vest, 0.5), "collar": (collar, 0.2),
    "sleeve": (sleeve, 0.5), "forearm": (forearm, 0.3), "hand": (hand, 0.2), "thigh": (thigh, 0.5),
    "shin": (shin, 0.5), "shin2": (shin2, 0.5), "shoe": (shoe, 0.3), "shoe2": (shoe2, 0.3)}.items()}
him = np.clip(sum(M.values()), 0, 1)

# the cup and the glass are white too, and the wall goes round them
cup = poly([(21.6, 55.4), (26.4, 55.4), (25.7, 59.9), (22.3, 59.9)])
saucer = blob([(19.4, 60.3), (24, 59.6), (28.6, 60.3), (24, 61.1)], n=10)
glass = poly([(12.5, 51.0), (16.7, 51.0), (16.2, 60.2), (13.0, 60.2)])
white_things = np.clip(sh.mask(cup, 0.1) + sh.mask(saucer, 0.1) + 0.8 * sh.mask(glass, 0.1), 0, 1)

# the window on the wall: four panes of sun
panes = np.zeros((H, W), np.float32)
for (a, b, c, d) in [((3.0, 13.2), (15.2, 15.8), (15.2, 31.8), (3.0, 30.4)),
                     ((17.4, 16.3), (30.2, 19.0), (30.2, 33.6), (17.4, 32.1)),
                     ((3.0, 32.6), (15.2, 34.0), (15.2, 51.4), (3.0, 51.0)),
                     ((17.4, 34.3), (30.2, 35.8), (30.2, 52.0), (17.4, 51.5))]:
    panes += sh.mask(poly([a, b, c, d]), 0.25)
panes = gaussian_filter(np.clip(panes, 0, 1), 5.0)

stages = []


def stage(name, days=0.0, d=None):
    i = len(stages)
    im = sh.image(days=days, light=light, d=d)
    (HERE / "stages").mkdir(exist_ok=True)
    im.convert("RGB").resize((W // 2, H // 2), Image.LANCZOS).save(HERE / "stages" / f"{i:02d}.jpg", quality=90)
    stages.append({"name": name, "file": f"stages/{i:02d}.jpg", "strokes": sh.count})
    return im


# ================================================================== 1. the chair, empty
WAL = {"walnut": 0.55, "indigo": 0.07}
far = {"walnut": 0.34, "indigo": 0.05}
# far legs and post first, paler
sh.wash(band([(70.6, 109.6), (70.6, 81), (71.6, 68), (72.8, 55)], [1.8, 1.8, 1.7, 1.5]), far, wet=1.2, streak="v", wobble=0.3)
sh.wash(band([(45.2, 109.6), (45.4, 81)], 1.7), far, wet=1.2, streak="v", wobble=0.3)
sh.wash(band([(45.3, 97.4), (48.4, 99.2)], 0.9), far, wet=1.0)
sh.wash(band([(70.7, 97.4), (73.9, 99.2)], 0.9), far, wet=1.0)
# the slats of the back
sh.wash(poly([(72.7, 56.2), (76.4, 55.2), (76.1, 60.8), (72.4, 61.8)]), {"walnut": 0.4, "indigo": 0.04}, wet=1.2, streak="h", wobble=0.3)
sh.wash(poly([(71.8, 67.8), (75.5, 67.0), (75.3, 71.8), (71.6, 72.6)]), {"walnut": 0.4, "indigo": 0.04}, wet=1.2, streak="h", wobble=0.3)
# rush seat: the top, pale, and the edge wound over the rail
sh.wash(poly([(44.2, 78.3), (71.4, 78.3), (75.2, 80.3), (47.2, 80.3)]), {"walnut": 0.13, "indigo": 0.02}, wet=1.2, streak="h", var=0.4, wobble=0.3)
sh.wash(poly([(47.2, 80.3), (75.2, 80.3), (75.2, 83.2), (47.2, 83.2)]), {"walnut": 0.36, "indigo": 0.04}, wet=1.3, streak="v", var=0.4, wobble=0.3)
for x in np.arange(48.2, 75, 1.35):
    sh.wash(band([(x, 80.5), (x + 0.1, 83.0)], 0.28), {"walnut": 0.3}, wet=0.8, rim=0, wobble=0.3)
sh.wash(band([(47.4, 83.3), (75.0, 83.3)], 0.5), {"walnut": 0.4, "indigo": 0.1}, wet=1.0)
# near legs and post
sh.wash(band([(48.4, 112), (48.5, 96), (48.6, 81.5)], [2.0, 2.3, 2.3]), WAL, wet=1.3, streak="v", wobble=0.3)
sh.wash(band([(74.0, 112), (74.0, 81.5), (75.0, 68), (76.4, 54)], [2.1, 2.4, 2.2, 1.9]), WAL, wet=1.3, streak="v", wobble=0.3)
sh.wash(band([(48.6, 99.4), (74, 99.4)], 1.25), {"walnut": 0.46, "indigo": 0.05}, wet=1.1, streak="h", wobble=0.3)
sh.wash(band([(48.6, 91.0), (74, 91.0)], 1.0), {"walnut": 0.3, "indigo": 0.04}, wet=1.1, streak="h", wobble=0.3)
# the turned rings on the near legs: darker where the lathe cut
for (x, y) in [(48.5, 86), (48.5, 104.5), (74, 86), (74, 104.5), (75.3, 64.5)]:
    sh.wash(band([(x - 1.1, y), (x + 1.1, y)], 0.45), {"walnut": 0.4, "indigo": 0.08}, wet=0.9, wobble=0.2)
# shade down the right of each near leg (the window is on the left)
sh.wash(band([(49.0, 112), (49.2, 82)], 0.8), {"walnut": 0.2, "indigo": 0.12}, wet=1.6, rim=0)
sh.wash(band([(74.7, 112), (74.7, 82), (75.7, 68), (77.0, 55)], 0.8), {"walnut": 0.2, "indigo": 0.12}, wet=1.6, rim=0)
stage("the chair, painted empty, in walnut")

# ================================================================== 2. his coat on the back of it;
# the table, the cup, the glass of water
COAT = {"indigo": 0.5, "walnut": 0.4}
coat = blob([(72.2, 54.8), (75.2, 52.6), (79.6, 52.8), (83.2, 56.5), (85.6, 68), (87.0, 84), (87.4, 96.5),
             (83.6, 98.6), (79, 99.6), (72.6, 97.6), (71.9, 84), (71.8, 68)], n=10)
# seams are kept: a hair of paper down the front of the sleeve, along the lapel, round the pocket flap
seams = np.zeros((H, W), np.float32)
for pts, wd in [([(78.4, 54.6), (79.6, 66), (80.4, 80), (80.2, 93)], 0.3), ([(73.6, 57.6), (76.4, 64.5), (76.6, 71), (75.4, 77)], 0.28),
                ([(73.4, 84.2), (77.6, 84.6)], 0.25), ([(80.4, 93.2), (86.6, 92.2)], 0.25)]:
    seams += sh.mask(band(pts, wd), 0.3)
seams = np.clip(gaussian_filter(seams, 0.8) * 1.3, 0, 0.9)
sh.wash(coat, COAT, wet=1.8, rim=0.6, var=0.45, streak="v", wobble=0.5, keep=seams)
sh.wash(coat, {"indigo": 0.2, "walnut": 0.18}, wet=5, rim=0, var=0.7, ramp=(72, 60, 0.2, 87, 92, 1.3), wobble=0.5, keep=seams * 0.6)
# the sleeve, nearer than the body and darker; the folds
sh.wash(blob([(79.2, 54.4), (83.2, 57), (85.6, 68), (87.0, 84), (87.3, 93.0), (80.6, 93.6), (80.6, 80), (79.8, 66)], n=8),
        {"indigo": 0.22, "walnut": 0.2}, wet=1.6, rim=0.5, var=0.5, streak="v", wobble=0.3, keep=seams)
for pts, wd in [([(74.4, 78), (74.8, 88), (74.4, 96.5)], 0.9), ([(77.6, 72), (78.4, 86), (78.2, 97.5)], 1.2),
                ([(82.2, 60), (83.6, 74), (84.2, 91)], 1.3), ([(73.0, 60), (73.0, 74)], 0.8)]:
    sh.wash(band(pts, wd), {"indigo": 0.3, "walnut": 0.26}, wet=2.6, rim=0, wobble=0.4)
# the collar over the top slat, the lapel's shadow, two buttons, the cuff
sh.wash(blob([(72.0, 54.8), (75.4, 52.3), (79.6, 52.7), (79.4, 55.4), (76, 56.0), (72.6, 57.6)], n=8), {"indigo": 0.36, "walnut": 0.28}, wet=1.3, rim=0.8, wobble=0.3)
sh.wash(band([(74.2, 58), (77.0, 64.6), (77.2, 71), (76.0, 77)], 0.7), {"indigo": 0.24, "walnut": 0.2}, wet=1.8, rim=0, wobble=0.3)
for by in (80.4, 87.6):
    sh.wash(band([(74.9, by), (75.0, by + 0.1)], 0.85), {"indigo": 0.5, "walnut": 0.5}, wet=0.8, rim=0.6, wobble=0.1)
for bx in (81.6, 83.0, 84.4):
    sh.wash(band([(bx, 91.0), (bx + 0.05, 91.05)], 0.5), {"indigo": 0.4, "walnut": 0.4}, wet=0.7, wobble=0.1)
# the lining showing at the hem: the one warm thing that stays a while
sh.wash(poly([(72.8, 96.4), (79.5, 97.4), (79.3, 99.6), (72.9, 98.6)]), {"madder": 0.5, "walnut": 0.12}, wet=1.4, streak="h", wobble=0.3)

# table: top, edge, apron, legs
sh.wash(poly([(-2, 58.8), (44, 58.8), (47.6, 61.4), (-2, 61.4)]), {"walnut": 0.06, "indigo": 0.01}, wet=1.4, streak="h", var=0.5, wobble=0.3)
sh.wash(poly([(-2, 61.4), (47.6, 61.4), (47.6, 63.8), (-2, 63.8)]), {"walnut": 0.44, "indigo": 0.05}, wet=1.3, streak="h", var=0.4, wobble=0.3)
sh.wash(poly([(-2, 63.8), (45.2, 63.8), (45.2, 68.8), (-2, 68.8)]), {"walnut": 0.25, "indigo": 0.07}, wet=1.5, streak="h", var=0.4, wobble=0.3)
sh.wash(band([(-2, 64.4), (45.2, 64.4)], 0.9), {"walnut": 0.2, "indigo": 0.14}, wet=2.2, rim=0)
sh.wash(band([(40.0, 68.8), (40.2, 109.6)], [1.9, 1.6]), {"walnut": 0.3, "indigo": 0.06}, wet=1.2, streak="v", wobble=0.3)
sh.wash(band([(43.3, 68.8), (43.5, 90), (43.7, 112)], [2.7, 2.4, 2.0]), WAL, wet=1.3, streak="v", wobble=0.3)
sh.wash(band([(44.2, 69), (44.5, 112)], 0.8), {"walnut": 0.2, "indigo": 0.12}, wet=1.6, rim=0)
sh.wash(band([(4.6, 68.8), (4.5, 112)], [2.7, 2.0]), WAL, wet=1.3, streak="v", wobble=0.3)
sh.wash(band([(1.2, 68.8), (1.2, 109.6)], [1.9, 1.6]), {"walnut": 0.3, "indigo": 0.06}, wet=1.2, streak="v", wobble=0.3)

# cup: only its shaded side and what it throws. The cup itself is paper.
sh.wash(poly([(24.5, 55.5), (26.4, 55.5), (25.7, 59.8), (24.3, 59.8)]), {"indigo": 0.13, "walnut": 0.07}, wet=1.8, rim=0.2, wobble=0.1)
sh.wash(band([(21.7, 55.4), (26.3, 55.4)], 0.28), {"indigo": 0.22, "walnut": 0.12}, wet=0.7, wobble=0.1)
sh.wash(band([(21.7, 55.6), (22.4, 59.8)], 0.22), {"indigo": 0.12, "walnut": 0.06}, wet=0.7, wobble=0.1)
sh.wash(band([(26.4, 56.4), (28.0, 57.1), (27.6, 58.4), (26.1, 58.9)], 0.5), {"indigo": 0.2, "walnut": 0.12}, wet=0.7, wobble=0.1)
sh.wash(blob([(19.6, 60.5), (24, 60.9), (28.6, 60.5), (24, 61.25)], n=10), {"indigo": 0.2, "walnut": 0.1}, wet=0.9, wobble=0.1)
sh.wash(band([(27.5, 60.6), (36, 60.9)], [1.0, 0.3]), {"indigo": 0.14, "walnut": 0.1}, wet=2.0, rim=0)
# glass of water
for pts in ([(12.6, 51.0), (13.1, 60.2)], [(16.6, 51.0), (16.1, 60.2)], [(13.1, 60.1), (16.1, 60.1)]):
    sh.wash(band(pts, 0.3), {"indigo": 0.2, "walnut": 0.06}, wet=0.7, wobble=0.1)
sh.wash(band([(12.8, 53.3), (16.4, 53.3)], 0.25), {"indigo": 0.18}, wet=0.7, wobble=0.1)
sh.wash(poly([(12.9, 53.4), (16.4, 53.4), (16.1, 60.0), (13.2, 60.0)]), {"indigo": 0.06}, wet=1.2, ramp=(13, 56, 0.4, 16.4, 56, 1.4), wobble=0.1)
sh.wash(band([(16.6, 60.5), (23, 60.8)], [0.9, 0.3]), {"indigo": 0.09, "walnut": 0.05}, wet=2.0, rim=0)
stage("his coat on the back of it; the table, the cup, the water")
slow = sh.snapshot()

# ================================================================== 3. the wall and the floor,
# painted round him and round the window
keep_fig = np.clip(gaussian_filter(him, 1.3) * 1.7 - 0.5, 0, 1)
keep_wall = np.clip(keep_fig + panes + white_things, 0, 1)
wall = poly([(-3, -3), (103, -3), (103, 100.2), (-3, 100.2)])
sh.wash(wall, {"weld": 0.115, "madder": 0.034, "logwood": 0.016}, wet=3, rim=0.2, var=0.5, keep=keep_wall,
        ramp=(0, 70, 0.72, 100, 15, 1.3), wobble=0.3, grain="broad")
# then the big flat brush, left to right, each sweep over the edge of the last
yb = -3.0
rs = np.random.default_rng(4)
while yb < 100:
    hgt = rs.uniform(11, 17)
    tilt = rs.uniform(-4, 4)
    sh.wash(poly([(-3, yb), (103, yb + tilt), (103, min(yb + tilt + hgt + 1.6, 100.2)), (-3, min(yb + hgt + 1.6, 100.2))]),
            {"weld": 0.05 * rs.uniform(0.7, 1.3), "madder": 0.017, "logwood": 0.006}, wet=7, rim=0.1, var=0.6, keep=keep_wall,
            wobble=2.0, grain="broad")
    yb += hgt
# the room is darker away from the window, and under the table
sh.wash(wall, {"logwood": 0.08, "weld": 0.06, "madder": 0.035}, wet=3, rim=0, var=0.5, keep=keep_wall, grain="broad",
        ramp=(40, 70, 0.0, 104, 0, 1.0), wobble=0.3)
sh.wash(poly([(-3, 68.8), (45, 68.8), (47, 100.2), (-3, 100.2)]), {"logwood": 0.09, "madder": 0.04}, wet=5, rim=0, var=0.5, keep=keep_fig)
# the bars of the window
sh.wash(band([(16.3, 14), (16.3, 53)], 1.1), {"weld": 0.04, "logwood": 0.02}, wet=4, rim=0)
# skirting
sh.wash(band([(-3, 100.2), (103, 100.2)], 0.7), {"logwood": 0.16, "madder": 0.06}, wet=1.4, keep=keep_fig)
# floor
floor = poly([(-3, 100.6), (103, 100.6), (103, 128), (-3, 128)])
sh.wash(floor, {"madder": 0.12, "logwood": 0.10, "weld": 0.06}, wet=2.5, var=0.6, streak="h", keep=keep_fig,
        ramp=(0, 101, 0.75, 0, 126, 1.25))
# what the chair, the coat and the table throw, to the right
sh.wash(blob([(47, 111.2), (76, 110.6), (97, 112.4), (99, 115.4), (74, 116.6), (50, 114.2)], n=10), {"logwood": 0.24, "indigo": 0.05}, wet=7, rim=0, keep=keep_fig)
sh.wash(blob([(2, 111.4), (44, 111.0), (58, 113.6), (40, 116.4), (4, 115.4)], n=10), {"logwood": 0.2, "indigo": 0.04}, wet=7, rim=0, keep=keep_fig)
stage("the wall and the floor, painted round him")

# ================================================================== 4. him, in the quick dyes
FLESH = {"kermes": 0.10, "weld": 0.13, "madder": 0.05}
LOG = "logwood"

# trousers, shins, shoes
TR = {"logwood": 0.85, "indigo": 0.06}
sh.wash(None, {"logwood": 0.6, "indigo": 0.05}, mask=M["shin2"], wet=1.6, rim=0.5, var=0.4, streak="v")
sh.wash(None, {"logwood": 0.3}, mask=M["shin2"], wet=3, rim=0)
sh.wash(None, {"logwood": 0.9, "madder": 0.3}, mask=M["shoe2"], wet=1.3, rim=0.5)
sh.wash(None, TR, mask=M["thigh"], wet=1.8, rim=0.5, var=0.45, streak="h")
sh.wash(None, {"logwood": 0.55, "indigo": 0.05}, mask=M["shin"], wet=1.8, rim=0.5, var=0.45, streak="v")
sh.wash(band([(36.2, 80.5), (36.6, 104)], 1.6), {"logwood": 0.3}, wet=3, rim=0)        # shade down the calf
sh.wash(band([(34, 79.6), (60, 79.6), (70, 79.8)], 1.6), {"logwood": 0.3}, wet=3.5, rim=0)   # under the thigh
sh.wash(None, {"logwood": 0.95, "madder": 0.32}, mask=M["shoe"], wet=1.3, rim=0.6)
sh.wash(band([(26.0, 111.7), (38.6, 111.7)], 0.6), {"logwood": 0.5}, wet=1.0)

# waistcoat, knitted, brick: his arm and collar kept out of it
keep_v = np.clip(M["sleeve"] + M["collar"] + M["forearm"], 0, 1)
VEST = {"madder": 0.46, "logwood": 0.22, "weld": 0.10}
sh.wash(None, VEST, mask=M["vest"], wet=1.8, rim=0.5, var=0.5, streak="v", keep=keep_v)
sh.wash(blob([(62, 41), (68, 43.6), (71, 50), (72.4, 60), (72.2, 74.4), (63, 74), (64.4, 60), (63.6, 50)], n=8),
        {"logwood": 0.26, "madder": 0.1}, wet=6, rim=0, keep=np.clip(keep_v + (1 - M["vest"]), 0, 1))
sh.wash(band([(54.6, 70.9), (71.4, 72.9)], 0.9), {"logwood": 0.3, "madder": 0.15}, wet=1.2, keep=keep_v)   # the welt
for x in np.arange(55.0, 71, 1.5):
    sh.wash(band([(x, 44 + abs(x - 62) * 0.5), (x - 0.4, 70.5 + (x - 55) * 0.12)], 0.22), {"logwood": 0.12, "madder": 0.1},
            wet=1.0, rim=0, keep=np.clip(keep_v + (1 - M["vest"]), 0, 1), wobble=0.4)

# shirt: paper. Only its shadows.
sh.wash(band([(66.9, 49.5), (63.2, 57.5), (59.8, 64.6)], [2.6, 2.4, 2.2]), {"logwood": 0.13, "indigo": 0.02}, wet=4, rim=0, keep=1 - M["sleeve"])
for pts in ([(63.2, 50.6), (61.6, 53.4), (62.8, 55.4)], [(60.0, 56.6), (61.6, 59.2), (59.6, 61.2)], [(58.4, 60.4), (56.6, 63.6)]):
    sh.wash(band(pts, 0.35), {"logwood": 0.2}, wet=1.3, rim=0, keep=1 - M["sleeve"])
sh.wash(band([(54.9, 61.4), (57.6, 64.2), (60.2, 66.2)], 1.4), {"logwood": 0.07}, wet=1.2, rim=0.9)        # the roll at the elbow
sh.wash(band([(56.8, 40.1), (60.6, 39.1), (64.4, 38.5)], 0.28), {"logwood": 0.18}, wet=0.8)                  # collar
sh.wash(band([(61.2, 41.6), (63.4, 41.2), (65.2, 40.2)], 1.6), {"logwood": 0.12}, wet=1.6, rim=0, keep=1 - M["collar"])
sh.wash(band([(58.2, 43.0), (59.0, 45.8)], 0.26), {"logwood": 0.2}, wet=0.8)

# forearm and hand: his colour, and the walnut that never came out of them
sh.wash(None, FLESH, mask=M["forearm"], wet=1.4, rim=0.4, var=0.3)
sh.wash(None, {"walnut": 0.09, "indigo": 0.04, "madder": 0.03}, mask=M["forearm"], wet=2.5, rim=0.2, ramp=(56, 63, 0.1, 40, 60, 1.0))
sh.wash(band([(56.6, 66.2), (48, 64.4), (41, 62.4)], 1.3), {"logwood": 0.16, "madder": 0.08}, wet=2.5, rim=0)   # under the arm
sh.wash(None, FLESH, mask=M["hand"], wet=1.2, rim=0.4, var=0.3)
sh.wash(None, {"walnut": 0.2, "indigo": 0.09, "madder": 0.04}, mask=M["hand"], wet=1.2, rim=0.7, var=0.4)
sh.wash(band([(38.4, 59.4), (36.4, 60.6), (33.6, 60.9)], [1.1, 0.9, 0.6]), {"walnut": 0.12, "indigo": 0.06}, wet=1.0, rim=0.6, wobble=0.2)   # the thumb, behind
for pts in ([(34.4, 58.2), (32.2, 59.2), (29.4, 60.4)], [(35.2, 59.3), (32.4, 60.2), (29.6, 60.9)], [(37.6, 58.5), (36.6, 59.6)]):
    sh.wash(band(pts, 0.24), {"walnut": 0.16, "madder": 0.08, "logwood": 0.1}, wet=0.8, rim=0, wobble=0.2)
sh.wash(band([(28.8, 61.3), (41, 62.4)], 0.45), {"walnut": 0.1, "logwood": 0.2}, wet=1.4, rim=0)

# neck, head
sh.wash(None, FLESH, mask=M["neck"], wet=1.2, rim=0.2)
sh.wash(None, {"kermes": 0.05, "logwood": 0.08, "madder": 0.03}, mask=M["neck"], wet=1.5, rim=0, ramp=(57, 40, 0.5, 64.5, 40, 1.3))
sh.wash(None, FLESH, mask=M["head"], wet=1.0, rim=0.35, var=0.25)
inside = 1 - M["head"]
# the back of the head, away from the window. Everything in the face is kermes, with as little
# logwood as will make it a dark: nothing here is to see out the week
sh.wash(blob([(58.6, 21), (66.6, 23.6), (66.8, 33), (64, 38), (59.6, 37.6), (58.2, 30)], n=8), {"kermes": 0.04, "logwood": 0.08, "madder": 0.02},
        wet=7, rim=0, keep=inside)
sh.wash(blob([(54.8, 30.4), (58.6, 30.6), (59.2, 35.4), (55.2, 36.6)], n=8), {"kermes": 0.045, "madder": 0.03, "logwood": 0.02}, wet=5, rim=0, keep=inside)
sh.wash(band([(54.2, 37.7), (57.6, 37.3), (61.4, 36.4)], 1.0), {"kermes": 0.08, "logwood": 0.13}, wet=1.8, rim=0, keep=inside)
sh.wash(blob([(52.6, 27.9), (54.8, 27.7), (55.2, 29.4), (53.2, 29.7)], n=8), {"kermes": 0.07, "logwood": 0.08}, wet=1.6, rim=0, keep=inside)
sh.wash(band([(53.3, 28.8), (53.9, 28.75)], 0.52), {"kermes": 0.4, "logwood": 0.4}, wet=0.7, rim=0, wobble=0.1)        # eye
sh.wash(band([(52.8, 28.3), (54.0, 28.1), (54.9, 28.5)], 0.2), {"kermes": 0.2, "logwood": 0.2}, wet=0.6, rim=0, wobble=0.1)
sh.wash(band([(52.1, 27.5), (53.6, 27.0), (55.3, 27.3)], [0.45, 0.6, 0.3]), {"kermes": 0.25, "logwood": 0.28}, wet=0.8, dry=0.3, wobble=0.1)   # brow
sh.wash(band([(51.2, 32.6), (52.0, 33.0)], 0.3), {"kermes": 0.2, "logwood": 0.14}, wet=0.7, wobble=0.1)  # nostril
sh.wash(blob([(51.3, 33.5), (53.9, 33.0), (55.0, 34.7), (52.0, 35.1)], n=8), {"kermes": 0.2, "logwood": 0.26}, wet=0.9, rim=0.3, dry=0.25, streak="v", wobble=0.1, keep=inside)   # moustache
sh.wash(band([(52.0, 35.0), (53.0, 35.0)], 0.22), {"kermes": 0.3, "logwood": 0.12}, wet=0.6, wobble=0.1)  # mouth
# ear
sh.wash(blob([(59.6, 28.6), (60.9, 28.4), (61.4, 30.4), (60.6, 32.4), (59.6, 31.6)], n=8), {"madder": 0.12, "kermes": 0.08}, wet=0.9, rim=0.9, wobble=0.1)
sh.wash(band([(60.2, 29.4), (60.5, 30.8)], 0.3), {"kermes": 0.2, "logwood": 0.14}, wet=0.7, wobble=0.1)
# hair: grey, thin on top
hair = blob([(57.6, 21.5), (61.6, 21.4), (65.0, 24.0), (66.2, 28.3), (65.5, 32.6), (64.0, 35.6), (62.2, 35.2),
             (61.7, 32.4), (62.2, 28.2), (60.4, 25.2), (57.2, 23.6)], n=8)
sh.wash(hair, {"logwood": 0.3, "indigo": 0.03}, wet=1.2, rim=0.3, var=0.5, streak="v", dry=0.3, wobble=0.2, keep=inside)
sh.wash(blob([(62.4, 28), (65.8, 27), (65.6, 33), (63.8, 35.6), (62.2, 34.8)], n=8), {"logwood": 0.22}, wet=2, rim=0, keep=inside)
hung = sh.snapshot()
stage("him, last, in the quick dyes: hung")

# ================================================================== the forty days
going = HERE / "going"
going.mkdir(exist_ok=True)
for day in (0, 1, 3, 6, 9, 15, 25, 40):
    sh.image(days=day, light=light).resize((W // 2, H // 2), Image.LANCZOS).save(going / f"day-{day:02d}.jpg", quality=90)
stage("the third day", days=3)
final = stage("the ninth day", days=9)
final.save(HERE / "final.png")

# a sheet of all of them, for looking at
days = (0, 1, 3, 6, 9, 15, 25, 40)
tw, th = W // 4, H // 4
contact = Image.new("RGB", (tw * 4 + 50, th * 2 + 30), (60, 58, 55))
for i, day in enumerate(days):
    im = Image.open(going / f"day-{day:02d}.jpg").resize((tw, th), Image.LANCZOS)
    contact.paste(im, (10 + (i % 4) * (tw + 10), 10 + (i // 4) * (th + 10)))
contact.save(going / "contact.jpg", quality=88)

# ================================================================== the piece itself: the same
# sheet, handed to the page, to be spent by whoever looks at it
LW, LH = 720, 900


def small(a):
    return np.asarray(Image.fromarray(a.astype(np.float32), mode="F").resize((LW, LH), Image.BOX))


def png64(rgb):
    buf = io.BytesIO()
    Image.fromarray(rgb).save(buf, "PNG", optimize=True)
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()


dmax = {}
chans = []
for k in ORDER:
    a = small(sh.d[k])
    dmax[k] = float(max(a.max(), 1e-6))
    chans.append(np.sqrt(np.clip(a / dmax[k], 0, 1)))
gy, gx = np.gradient(sh.tooth)
relief = (1 - 0.018 * (sh.size - 0.5)) * (1 + 0.026 * np.clip(gx + gy, -2, 2) * 2.2)
LMAX = 1.3
extra = [np.clip(small(light) / LMAX, 0, 1), np.clip((small(relief) - 0.8) / 0.4, 0, 1), np.zeros((LH, LW), np.float32)]
q = lambda trio: (np.dstack(trio) * 255 + 0.5).astype(np.uint8)
data = {
    "w": LW, "h": LH, "order": ORDER,
    "absorb": [DYES[k][0] for k in ORDER], "tau": [DYES[k][1] for k in ORDER], "dmax": [dmax[k] for k in ORDER],
    "teaYield": [TEA_YIELD[k] for k in ORDER], "tea": TEA[0], "teaTau": TEA[1],
    "paper": [float(v) for v in PAPER], "lightMax": LMAX,
    "a": png64(q(chans[0:3])), "b": png64(q(chans[3:6])), "c": png64(q(extra)),
}
(HERE / "live").mkdir(exist_ok=True)
(HERE / "live" / "sheet.js").write_text("window.SHEET = " + json.dumps(data) + ";\n")

(HERE / "work.json").write_text(json.dumps({
    "title": "Forty for Zisis Vergos, dyer. Ninth day",
    "artist": "thomai-vergou",
    "year": 2004,
    "medium": "Six lawful dyes on paper, hung from two pegs beside a west window. Shown at the ninth day of forty",
    "made": "2026-11-14",
    "program": "paint.py",
    "strokes": sh.count,
    "marks": "washes",
    "size": [W, H],
    "live": "live/index.html",
    "stages": stages,
    "seconds": round(time.time() - t0, 1),
}, indent=2, ensure_ascii=False) + "\n")
print(f"{sh.count} washes, {time.time() - t0:.1f}s")
