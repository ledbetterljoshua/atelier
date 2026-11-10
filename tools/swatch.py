"""A sheet of test marks: run after touching the engine to see that paint still behaves."""
import sys, time
import numpy as np
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from engine import Board, Brush, ground, hexc, mix

W, H = 1400, 900
rng = np.random.default_rng(1)
b = Board(W, H, hexc("#141210"), ground.hardboard_mesh(W, H, rng), seed=2)
t0 = time.time()
red, blue, yel, white = hexc("#c8321e"), hexc("#1f3f9a"), hexc("#e8c23a"), hexc("#f4efe2")
flat = Brush(width=46)
# 1 loaded strokes running dry
for i, c in enumerate([red, blue, yel, white]):
    b.stroke([(60, 70 + i * 60), (640, 60 + i * 60)], flat.but(deplete=0.004), c, wobble=3)
# 2 wet into wet: blue dragged across yellow
for i in range(5):
    b.stroke([(720 + i * 50, 40), (730 + i * 50, 280)], flat, yel)
b.stroke([(700, 100), (1000, 110)], flat.but(pickup=0.5), blue)
b.stroke([(700, 200), (1000, 210)], flat.but(pickup=0.05), blue)
# 3 dry brush scumble over the mesh
b.dry()
for i in range(4):
    b.stroke([(60, 340 + i * 50), (640, 345 + i * 50)], flat.but(dryness=0.5 + 0.15 * i, opacity=0.8), white, wobble=2)
# 4 glaze over dry paint
for i in range(6):
    b.stroke([(720, 330 + i * 34), (1340, 330 + i * 34)], flat, mix((white, 3), (yel, 1)))
b.dry()
b.stroke([(800, 310), (820, 540)], Brush(width=90, glaze=True, opacity=0.6, bristle=2), red)
b.stroke([(1000, 310), (1020, 540)], Brush(width=90, glaze=True, opacity=0.6, bristle=2), blue)
# 5 double-loaded brush, knife, small round
b.stroke([(60, 620), (300, 580), (640, 640)], Brush(width=70, pickup=0.1), red, color2=yel)
b.stroke([(60, 760), (640, 770)], Brush(width=60, hard=True, jitter=0.02, gap=0.0, thickness=3, taper=(0.0, 0.02), deplete=0.003), white)
for i in range(40):
    b.dab(720 + rng.random() * 600, 600 + rng.random() * 250, Brush(width=14, thickness=2.5), [red, blue, yel, white][i % 4])
print("strokes", b.n_strokes, "sec", round(time.time() - t0, 2))
b.save(".scratch/swatch.png")
