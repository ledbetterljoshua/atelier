"""Itzel Moroyoqui - Calle Sahuaripa, 43°

A mesquite on a lot at the corner of Calle Sahuaripa, twenty to four in August. She sat on the bike
under it with her back to the trunk's lean and looked down. The tree is all above the top of the
board: what is on it is the packed earth in its shade, and a hundred little pictures of the sun
coming down through the leaves. The dog that is always under that tree lies in the hollow it has
scraped for itself. Somebody keeps a clay bowl of water for it, and one of the suns has landed in
the bowl.
"""
import os
import sys
from pathlib import Path

import numpy as np
from scipy.ndimage import gaussian_filter, maximum_filter

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[3]))
sys.path.insert(0, str(HERE.parents[1]))

from engine import Board, Brush, ground, hexc, mix, scale  # noqa: E402
from engine.studio import finish  # noqa: E402
from tools import (Canopy, View, blocked, fur, loads, march, normals, plywood, sd_capsule,  # noqa: E402
                   sd_ellipsoid, smin, to_ground, v3)

DEBUG = os.environ.get("ITZEL_DEBUG")
W, H = 1680, 1400
rng0 = np.random.default_rng(4303)
PRIMER = hexc("#f1efe8")
board = Board(W, H, PRIMER, plywood(W, H, rng0), seed=43, light=(0.6, -0.45))
board.dries_off_board = False
rng = board.rng
view = View(W, H, 1250, 1.15, 46)

# --- tubes -----------------------------------------------------------------------------------
white = hexc("#fbfaf5")
ultra, violet, turq = hexc("#26308f"), hexc("#4a2a86"), hexc("#0f8f95")
magenta, orange, cadyel = hexc("#c4206a"), hexc("#f2601c"), hexc("#f4c21c")
lemon, ochre = hexc("#eee65a"), hexc("#c99a3c")
m = mix

# --- the lot -----------------------------------------------------------------------------------
EL, AZ = np.radians(57), np.radians(24)        # the sun: high, ahead of her and a little right
SUN = v3(np.sin(AZ) * np.cos(EL), np.sin(EL), np.cos(AZ) * np.cos(EL))
CH = 5.0                                         # the leaves overhead
CROWN_C, CROWN_R = np.array([0.3, 4.75]), 3.05  # the crown, on the canopy's own plane

# the openness of the leaves, on a 5 mm grid over the part of the canopy that matters
CELL, CX0, CZ0 = 0.005, -3.0, 0.8
cw, chh = 1900, 1500
crng = np.random.default_rng(57)
gz, gx = np.mgrid[0:chh, 0:cw].astype(np.float64)
qx, qz = CX0 + gx * CELL, CZ0 + gz * CELL
th = np.arctan2(qz - CROWN_C[1], qx - CROWN_C[0])
rr = np.hypot(qx - CROWN_C[0], qz - CROWN_C[1])
rim = CROWN_R * (1 + 0.07 * np.sin(3 * th + 1.0) + 0.05 * np.sin(7 * th + 2.0) + 0.03 * np.sin(13 * th + 0.3))
inside = rr / rim
# inside the crown the leaves are shut, with holes: most of them smaller than the sun, a few big
patchy = ground.fbm(cw, chh, crng, base=8, octaves=3)
O = np.zeros((chh, cw))
holes = []
for _ in range(2600):
    hx, hz = crng.uniform(-2.0, 5.5), crng.uniform(2.4, 7.4)
    ix, iz = int((hx - CX0) / CELL), int((hz - CZ0) / CELL)
    near = hz < 3.7                                           # what lands in the foreground: fewer, smaller
    if not (0 <= ix < cw and 0 <= iz < chh) or crng.random() > patchy[iz, ix] ** 2.2 * (0.45 if near else 1.0):
        continue
    big = crng.random() < (0.015 if near else 0.05)
    r = crng.uniform(0.05, 0.10) if big else np.exp(crng.normal(np.log(0.019), 0.38))
    holes.append((hx, hz, r))
for hx, hz, r in holes:
    ang, el = crng.uniform(0, np.pi), crng.uniform(1.0, 2.2)      # a gap between twigs is longer than wide
    n = int(r * el / CELL) + 2
    ix, iz = int((hx - CX0) / CELL), int((hz - CZ0) / CELL)
    a0, a1, b0, b1 = max(0, iz - n), min(chh, iz + n), max(0, ix - n), min(cw, ix + n)
    dx, dz = qx[a0:a1, b0:b1] - hx, qz[a0:a1, b0:b1] - hz
    u, w = dx * np.cos(ang) + dz * np.sin(ang), -dx * np.sin(ang) + dz * np.cos(ang)
    O[a0:a1, b0:b1] = np.maximum(O[a0:a1, b0:b1], (np.hypot(u / el, w) < r).astype(float))
thin = np.clip((inside - 0.9) / 0.1, 0, 1)                     # thinner toward the crown's edge
O = np.where(inside > 1.0, 1.0, np.maximum(O, thin * (ground.fbm(cw, chh, crng, base=60, octaves=3) > 0.55)))

BOWL = v3(0.36, 0.0, 0.74)
# one gap, right over the bowl from where she sits
bq = BOWL[[0, 2]] + CH * SUN[[0, 2]] / SUN[1]
O = np.maximum(O, np.clip(1 - np.hypot(qx - bq[0], (qz - bq[1]) * 1.1) / 0.15, 0, 1) * 1.6).clip(0, 1)
canopy = Canopy(O, CX0, CZ0, CELL, CH, SUN)

# the trunk and the two big limbs, which only show where they cut a sun out
LIMBS = [(v3(0.95, 0.0, 4.25), v3(1.15, 1.7, 4.2), 0.17, 0.15),
         (v3(1.15, 1.7, 4.2), v3(2.3, 3.6, 4.4), 0.12, 0.06),
         (v3(1.15, 1.7, 4.2), v3(0.1, 3.4, 4.0), 0.12, 0.07)]

# --- the dog, lying on its side in its hollow, head toward the bowl ----------------------------
DOG_C, YAW = v3(-0.22, 0.0, 1.32), -0.12
EX = v3(np.cos(YAW), 0, np.sin(YAW))
EZ = v3(-np.sin(YAW), 0, np.cos(YAW))
EY = v3(0, 1, 0)


def L3(x, y, z):
    return DOG_C + x * EX + y * EY + z * EZ


# (kind, a, b/radii, r, the way the hair lies, which part)
PARTS = [
    ("e", L3(0.08, 0.125, 0.03), v3(0.23, 0.125, 0.16), None, -EX, "chest"),
    ("e", L3(-0.20, 0.115, 0.01), v3(0.20, 0.115, 0.135), None, -EX, "hip"),
    ("c", L3(0.24, 0.12, 0.06), L3(0.37, 0.105, 0.07), 0.075, -EX, "neck"),
    ("e", L3(0.46, 0.10, 0.06), v3(0.12, 0.095, 0.105), None, -EX, "head"),
    ("c", L3(0.52, 0.08, 0.025), L3(0.635, 0.065, -0.005), 0.05, -EX, "muzzle"),
    ("e", L3(0.38, 0.172, 0.085), v3(0.10, 0.016, 0.07), None, -EX - 0.5 * EZ, "ear"),
    ("c", L3(0.17, 0.14, -0.08), L3(0.29, 0.13, -0.29), 0.04, -EZ, "fore"),
    ("c", L3(0.29, 0.13, -0.29), L3(0.41, 0.10, -0.38), 0.03, -EZ + EX, "forepaw"),
    ("c", L3(0.12, 0.04, -0.10), L3(0.22, 0.035, -0.33), 0.034, -EZ, "fore"),
    ("c", L3(0.22, 0.035, -0.33), L3(0.32, 0.03, -0.42), 0.028, -EZ + EX, "forepaw"),
    ("c", L3(-0.24, 0.15, -0.04), L3(-0.20, 0.14, -0.20), 0.065, -EZ, "thigh"),
    ("c", L3(-0.20, 0.14, -0.20), L3(-0.33, 0.11, -0.37), 0.032, -EZ - EX, "hind"),
    ("c", L3(-0.33, 0.11, -0.37), L3(-0.30, 0.09, -0.46), 0.026, -EZ, "hindpaw"),
    ("c", L3(-0.27, 0.04, -0.07), L3(-0.25, 0.035, -0.30), 0.04, -EZ, "hind"),
    ("c", L3(-0.25, 0.035, -0.30), L3(-0.38, 0.03, -0.41), 0.028, -EZ - EX, "hindpaw"),
    ("c", L3(-0.38, 0.09, 0.02), L3(-0.53, 0.06, -0.04), 0.03, -EX, "tail"),
    ("c", L3(-0.53, 0.06, -0.04), L3(-0.60, 0.035, -0.17), 0.024, -EZ, "tail"),
]


def part_d(p, k):
    kind, a, b, r, _, _ = PARTS[k]
    return sd_ellipsoid(p, a, b) if kind == "e" else sd_capsule(p, a, b, r)


def dog_sdf(p):
    d = part_d(p, 0)
    for k in range(1, len(PARTS)):
        d = smin(d, part_d(p, k), 0.045 if k < 5 else 0.022)
    return d


BR0, BR1, BH, BWALL, BWATER = 0.09, 0.118, 0.07, 0.012, 0.05


def bowl_sdf(p):
    q = p - BOWL
    rho = np.hypot(q[..., 0], q[..., 2])
    y = q[..., 1]
    rad = BR0 + (BR1 - BR0) * np.clip(y / BH, 0, 1)
    outer = np.maximum.reduce([(rho - rad) * 0.97, -y, y - BH])
    cav = np.maximum((rho - (rad - BWALL)) * 0.97, BWALL - y)
    return np.maximum(outer, -cav) - 0.002


def scene_sdf(p):
    return np.minimum(dog_sdf(p), bowl_sdf(p))


# --- what she sees at every point of the board ---------------------------------------------------
rays = view.rays()
eye = view.eye
tg = -eye[1] / np.minimum(rays[..., 1], -1e-9)
G = eye + rays * tg[..., None]

T = tg.copy()
WHAT = np.zeros((H, W), np.int8)          # 0 earth, 1 dog, 2 bowl clay, 3 water
NRM = np.zeros((H, W, 3))
NRM[..., 1] = 1
for sdf, corners, tag in ((dog_sdf, [L3(x, y, z) for x in (-0.68, 0.7) for y in (0, 0.3) for z in (-0.52, 0.22)], 1),
                          (bowl_sdf, [BOWL + v3(x, y, z) for x in (-0.13, 0.13) for y in (0, BH) for z in (-0.13, 0.13)], 2)):
    c = view.P(np.array(corners))
    x0, x1 = max(0, int(c[:, 0].min()) - 6), min(W, int(c[:, 0].max()) + 6)
    y0, y1 = max(0, int(c[:, 1].min()) - 6), min(H, int(c[:, 1].max()) + 6)
    sub = rays[y0:y1, x0:x1].reshape(-1, 3)
    t = march(eye, sub, sdf, 0.6, 3.5).reshape(y1 - y0, x1 - x0)
    near = t < T[y0:y1, x0:x1]
    T[y0:y1, x0:x1] = np.where(near, t, T[y0:y1, x0:x1])
    WHAT[y0:y1, x0:x1][near] = tag
    if tag == 2:
        tw = (BWATER - eye[1]) / rays[y0:y1, x0:x1, 1]
        pw = eye + rays[y0:y1, x0:x1] * tw[..., None]
        rho = np.hypot(pw[..., 0] - BOWL[0], pw[..., 2] - BOWL[2])
        water = (rho < BR0 + (BR1 - BR0) * BWATER / BH - BWALL) & (tw < T[y0:y1, x0:x1])
        T[y0:y1, x0:x1] = np.where(water, tw, T[y0:y1, x0:x1])
        WHAT[y0:y1, x0:x1][water] = 3
PT = eye + rays * T[..., None]
OBJ = (WHAT == 1) | (WHAT == 2)
NRM[OBJ] = normals(scene_sdf, PT[OBJ])

# the sun at every point: through the leaves, past the limbs, and past the dog and the bowl
LIGHT = canopy.light(PT)
EARTH = WHAT == 0
for a, b, r0, r1 in LIMBS:
    ga, gb = to_ground(a, SUN), to_ground(b, SUN)
    d = PT[..., [0, 2]] - ga
    ab = gb - ga
    h = np.clip((d @ ab) / (ab @ ab), 0, 1)
    dist = np.linalg.norm(d - h[..., None] * ab, axis=-1)
    LIGHT = np.where(EARTH & (dist < r0 + (r1 - r0) * h), 0.0, LIGHT)
check = (LIGHT > 0.04) & (EARTH | OBJ)
near_obj = np.zeros((H, W), bool)
for sdf_c, rad in ((DOG_C, 0.95), (BOWL, 0.3)):
    near_obj |= np.hypot(PT[..., 0] - sdf_c[0], PT[..., 2] - sdf_c[2]) < rad
idx = check & near_obj
P0 = PT[idx] + NRM[idx] * 0.004
LIGHT[idx] = np.where(blocked(P0, SUN, scene_sdf, far=0.8), 0.0, LIGHT[idx])

FLECK = LIGHT > 0.3
HALF = (LIGHT > 0.1) & (maximum_filter(LIGHT, 71) < 0.3)
OPEN = (EARTH & (LIGHT > 0.97) & (gaussian_filter(LIGHT, 18) > 0.93))   # past the crown: plain sun

if DEBUG:
    from PIL import Image
    Path(".scratch").mkdir(exist_ok=True)
    Image.fromarray((np.clip(LIGHT, 0, 1) * 255).astype(np.uint8)).save(".scratch/itzel2_light.png")
    Image.fromarray((WHAT * 60).astype(np.uint8)).save(".scratch/itzel2_what.png")

# --- colours ---------------------------------------------------------------------------------------
SUN_BASE = m((white, 6), (ochre, 0.8), (cadyel, 0.3), (magenta, 0.10), (orange, 0.12))
SUNLIT = [m((SUN_BASE, 4), (lemon, 0.4)),
          m((SUN_BASE, 4), (magenta, 0.10), (white, 0.6)),
          m((SUN_BASE, 4), (orange, 0.14)),
          m((SUN_BASE, 4), (ochre, 0.3)),
          m((SUN_BASE, 4), (white, 1.5))]
SH = {"mid": m((ultra, 2.0), (violet, 1.4), (white, 2.0), (ochre, 0.25)),
      "warm": m((violet, 1.6), (magenta, 0.7), (white, 2.0), (ochre, 0.4)),
      "cool": m((ultra, 1.6), (turq, 0.9), (white, 2.3)),
      "deep": m((ultra, 2.0), (violet, 1.8), (white, 0.9)),
      "bounce": m((violet, 1.0), (magenta, 1.0), (orange, 0.4), (white, 2.0))}
FUR = m((orange, 1.0), (ochre, 2.0), (white, 1.3))
FUR_PALE = m((ochre, 0.7), (white, 3.0), (orange, 0.25))
FUR_DARK = m((orange, 1.0), (magenta, 0.5), (violet, 0.5), (ochre, 0.9))
TERRA = m((orange, 2.0), (magenta, 0.5), (ochre, 0.8), (white, 0.5))

DENS = gaussian_filter(np.clip(LIGHT, 0, 1).astype(np.float32), 40)   # how many suns are about
NEAR_OPEN = gaussian_filter(OPEN.astype(np.float32), 90)
HOLLOW_C, HOLLOW_R = DOG_C + 0.03 * EZ - 0.04 * EX, (0.78, 0.40)


def hollow(p):
    """0 outside the dog's scrape, 1 at its floor."""
    q = p - HOLLOW_C
    u, w = q @ EX, q @ EZ
    return float(np.clip(1.3 - np.hypot(u / HOLLOW_R[0], w / HOLLOW_R[1]) * 1.3, 0, 1)) if np.ndim(u) == 0 else \
        np.clip(1.3 - np.hypot(u / HOLLOW_R[0], w / HOLLOW_R[1]) * 1.3, 0, 1)


def pix(p):
    q = view.P(p)
    return int(np.clip(q[1], 0, H - 1)), int(np.clip(q[0], 0, W - 1))


def shade_load(p, r):
    """One brushload for the shade, mixed for where it is going."""
    iy, ix = pix(p)
    dn, op, hl = float(DENS[iy, ix]), float(NEAR_OPEN[iy, ix]), float(hollow(p))
    w = {"mid": 1.0, "warm": 0.3 + 2.5 * dn, "cool": 0.15 + 4.0 * op, "deep": 0.05 + 2.5 * hl,
         "bounce": 0.05 + 3.0 * max(0.0, dn - 0.12)}
    keys = list(w)
    pr = np.array([w[k] for k in keys])
    a, b = r.choice(len(keys), 2, p=pr / pr.sum())
    c = m((SH[keys[a]], 1.0), (SH[keys[b]], r.uniform(0.0, 0.6)))
    return scale(c, r.uniform(0.86, 1.06) * (0.8 + 0.25 * (1 - hl)))


# =====================================================================================================
# 1. The light, all of it, over the whole board: earth, dog and bowl as they would be in the sun.
#    Separate hot strokes, no pickup, nothing running into anything.
two_inch = Brush(width=80, bristle=3.0, opacity=0.97, pickup=0.0, deplete=0.0010, jitter=0.03,
                 thickness=0.12, wander=1.2, gap=0.03)
one_inch = Brush(width=30, bristle=1.6, opacity=0.95, pickup=0.0, deplete=0.0008, jitter=0.03,
                 thickness=0.25, wander=0.8, gap=0.03)
letter = Brush(width=14, bristle=1.2, opacity=0.95, pickup=0.2, deplete=0.0001, jitter=0.03, thickness=0.15,
               taper=(0.05, 0.08), gap=0.0)

earth_m = EARTH.astype(np.float32)
board.tape_where(earth_m, feather=0.7)
loads(board, view, G, earth_m, two_inch, lambda p, r: SUNLIT[r.integers(len(SUNLIT))], 700, 0.75,
      lambda x, z: 0.15 * np.sin(1.3 * x + z), rng, width_m=0.10, jitter=0.12, wobble=3)
board.dry()
loads(board, view, G, earth_m, two_inch.but(opacity=0.85, dryness=0.3), lambda p, r: SUNLIT[r.integers(len(SUNLIT))],
      200, 0.5, 0.6, rng, width_m=0.08, jitter=0.4, wobble=3)
board.dry()

dog_m = (WHAT == 1).astype(np.float32)
DOGPART = np.full((H, W), -1, np.int16)
HAIR = np.zeros((H, W, 3))
di = np.nonzero(WHAT == 1)
dd = np.stack([part_d(PT[di], k) for k in range(len(PARTS))], 0)
DOGPART[di] = dd.argmin(0)
HAIR[di] = np.array([PARTS[k][4] for k in range(len(PARTS))])[DOGPART[di]]
PALE_PARTS = {"muzzle", "forepaw", "hindpaw"}


def fur_base(y, x):
    k = PARTS[DOGPART[y, x]][5]
    p = PT[y, x]
    belly = float(np.clip(((DOG_C - p) @ EZ - 0.02) / 0.08, 0, 1))      # toward the legs: the pale belly
    back = float(np.clip(((p - DOG_C) @ EZ - 0.04) / 0.08, 0, 1))
    if k in PALE_PARTS:
        return FUR_PALE
    if k == "ear":
        return scale(FUR_DARK, 0.55)
    if k in ("chest", "hip", "neck"):
        return m((FUR, 1.0), (FUR_PALE, 1.6 * belly), (FUR_DARK, 0.9 * back))
    if k in ("fore", "hind", "thigh"):
        return m((FUR, 1.0), (FUR_PALE, 0.8))
    return FUR


def fur_sun(y, x, r):
    return scale(m((fur_base(y, x), 1.0), (cadyel, 0.25), (white, 0.5)), r.uniform(0.95, 1.08))


board.tape_where(dog_m, feather=0.6)
fur(board, view, PT, NRM, HAIR, dog_m, one_inch, fur_sun, rng, 380, 0.09, wobble=0.6)
bowl_m = ((WHAT == 2) | (WHAT == 3)).astype(np.float32)
board.tape_where(bowl_m, feather=0.5)
for k in range(30):
    c = BOWL + v3(rng.uniform(-0.12, 0.12), 0.03, rng.uniform(-0.12, 0.12))
    a = rng.uniform(0, np.pi)
    d = v3(np.cos(a), 0, np.sin(a)) * 0.05
    board.stroke(view.P(np.array([c - d, c + d])), one_inch, m((TERRA, 1), (white, 0.8), (cadyel, 0.3)), wobble=0.5)
board.untape()
board.dry()
board.stage("the light, all of it")

# =====================================================================================================
# 2. The shade on the earth, over the light, around every sun. In here the paint runs together.
wet_two = two_inch.but(pickup=0.35, deplete=0.0006, opacity=0.96)
SHADE = EARTH & ~FLECK & ~OPEN
shade_m = SHADE.astype(np.float32)
board.tape_where(shade_m, feather=0.7)
loads(board, view, G, shade_m, wet_two.but(pickup=0.06), shade_load, 520, 1.1,
      lambda x, z: 0.08 * np.sin(0.9 * x - 0.5 * z), rng, width_m=0.13, jitter=0.1, wobble=2.5)
loads(board, view, G, shade_m, wet_two.but(opacity=0.8), shade_load, 380, 0.9, 0.55, rng, width_m=0.11,
      jitter=0.25, wobble=2.5)
loads(board, view, G, shade_m, wet_two.but(opacity=0.75), shade_load, 260, 0.8, -0.6, rng, width_m=0.10,
      jitter=0.25, wobble=2.5)
# the last of each load dragged back over it, so the board's grain catches it
loads(board, view, G, shade_m, two_inch.but(dryness=0.6, opacity=0.7, pickup=0.0, load=0.8),
      lambda p, r: scale(shade_load(p, r), 1.04), 70, 0.9, 0.0, rng, width_m=0.12, jitter=0.4, wobble=2.0)
board.stage("the shade, round a hundred suns")

# the dog's hollow: scraped down to the cool earth, darker, with the loose stuff pushed up round it
hol = np.zeros((H, W), np.float32)
hol[EARTH] = hollow(PT[EARTH])
hol_m = ((hol > 0.05) & SHADE).astype(np.float32)
board.tape_where(hol_m, feather=0.8)
board.tape_where(np.clip(hol * 3, 0, 1) * shade_m, feather=6.0, mode="and")
loads(board, view, G, hol_m, wet_two.but(width=60, opacity=0.8, pickup=0.45),
      lambda p, r: scale(m((SH["deep"], 1.0), (SH[["mid", "warm", "cool"][r.integers(3)]], r.uniform(0.3, 1.0))),
                         r.uniform(0.62, 0.78)), 160, 0.55, lambda x, z: YAW + 0.2 * np.sin(4 * x), rng,
      width_m=0.07, jitter=0.2, wobble=2)
board.untape()

# the half-suns, where a gap is smaller than the sun: dimmer, pinker pictures of it
half_m = (HALF & EARTH).astype(np.float32)
board.tape_where(half_m, feather=0.8)
ys, xs = np.nonzero(half_m > 0)
for i in rng.integers(len(ys), size=min(900, len(ys))):
    lv = float(LIGHT[ys[i], xs[i]])
    c = m((SH["mid"], 1.0), (SH["bounce"], 0.5), (SUN_BASE, 0.2 + 2.0 * (lv - 0.1)))
    board.dab(xs[i], ys[i], letter.but(width=16, pickup=0.3), scale(c, rng.uniform(0.92, 1.05)), angle=0.1,
              length=14)
board.untape()
board.dry()

# =====================================================================================================
# 3. The dog, in the shade with me. One mix to a brushload: where it is turned to the leaves it is
#    blue, where it faces the earth it takes the earth's warm, and where a sun lands on it, it burns.
SKY = v3(-0.35, 0.85, 0.4)
SKY /= np.linalg.norm(SKY)


def fur_shade(y, x, r):
    n = NRM_S[y, x]
    base = fur_base(y, x)
    up = float(n @ SKY)
    if up > 0.5:
        c = m((base, 1.0), (ultra, 0.45), (violet, 0.25), (ochre, 0.2), (white, 0.5))
        k = 1.0
    elif up > 0.05:
        c = m((base, 1.0), (violet, 0.5), (magenta, 0.15), (white, 0.2))
        k = 0.82
    else:
        c = m((base, 1.0), (violet, 0.7), (magenta, 0.25), (orange, 0.25))
        k = 0.6
    return scale(c, k * r.uniform(0.9, 1.08))


# the planes as she sees them, not every bump: the normals smoothed over a brush's width
NRM_S = np.stack([gaussian_filter(np.where(WHAT == 1, NRM[..., i], 0.0), 14) for i in range(3)], -1)
NRM_S /= np.linalg.norm(NRM_S, axis=-1, keepdims=True) + 1e-9
dshade = ((WHAT == 1) & ~FLECK).astype(np.float32)
board.tape_where(dshade, feather=0.6)
fur(board, view, PT, NRM, HAIR, dshade, one_inch.but(pickup=0.05), fur_shade, rng, 520, 0.10, wobble=0.6)
fur(board, view, PT, NRM, HAIR, dshade, one_inch.but(pickup=0.4, opacity=0.85), fur_shade, rng, 420, 0.07, wobble=0.6)
board.untape()

# the hair itself, flicked on with the lettering brush into the wet
fur(board, view, PT, NRM, HAIR, dshade, letter.but(width=9, pickup=0.35, opacity=0.9, taper=(0.1, 0.4)),
    lambda y, x, r: scale(fur_shade(y, x, r), r.choice([0.8, 1.15])), rng, 320, 0.05, wobble=0.3)
board.untape()

# the creases: where a leg folds against the body, and the ground under it
DOGD = np.full((H, W), 9.0)
DOGD[EARTH] = dog_sdf(PT[EARTH])
under = EARTH & (DOGD < 0.03) & ~FLECK & (np.abs((PT - DOG_C) @ EZ) < 0.22)
board.tape_where(under.astype(np.float32), feather=1.5)
loads(board, view, G, under.astype(np.float32), one_inch.but(pickup=0.4, opacity=0.85),
      lambda p, r: scale(m((SH["deep"], 1.0), (magenta, r.uniform(0, 0.2))), r.uniform(0.42, 0.55)), 140, 0.14,
      YAW, rng, jitter=0.15, wobble=1.0)
board.untape()


# the face: the closed eye, the nose, the mouth line, and the ear's edge
def face_line(pts_local, brush, col):
    q = view.P(np.array([L3(*p) for p in pts_local]))
    board.stroke(q, brush, col, wobble=0.3)


DARK = m((ultra, 1.5), (violet, 1.5), (magenta, 0.3))
face_line([(0.47, 0.168, 0.075), (0.50, 0.168, 0.06), (0.53, 0.158, 0.045)], letter.but(width=6, pickup=0.0), scale(DARK, 0.5))
nose = view.P(L3(0.645, 0.075, -0.005))
board.dab(nose[0], nose[1], letter.but(width=20, pickup=0.0, taper=(0.45, 0.45)), scale(DARK, 0.42), angle=1.3, length=22)
face_line([(0.55, 0.05, -0.04), (0.60, 0.05, -0.035), (0.63, 0.06, -0.03)], letter.but(width=4, pickup=0.3, opacity=0.6),
          scale(m((DARK, 1), (magenta, 0.8)), 0.6))
face_line([(0.36, 0.18, 0.06), (0.41, 0.19, 0.10), (0.47, 0.18, 0.12)], letter.but(width=6, pickup=0.2),
          scale(m((FUR_DARK, 1), (violet, 1.0)), 0.5))
board.stage("the dog")

# =====================================================================================================
# 4. The bowl: clay, and the water in it. The sun through the gap lands on most of it.
def bowl_col(y, x, r):
    p, n = PT[y, x], NRM[y, x]
    lit = LIGHT[y, x] > 0.3
    inner = np.hypot(p[0] - BOWL[0], p[2] - BOWL[2]) < BR0 + (BR1 - BR0) * p[1] / BH - BWALL * 0.5
    if lit:
        c = m((TERRA, 1.0), (white, 0.6 + 0.6 * max(0, float(n @ SUN))), (cadyel, 0.25))
    else:
        c = scale(m((TERRA, 1.0), (violet, 0.8), (magenta, 0.2)), 0.6 if inner else 0.7)
    return scale(c, r.uniform(0.93, 1.06))


clay = (WHAT == 2).astype(np.float32)
board.tape_where(clay, feather=0.5)
ys, xs = np.nonzero(clay)
for i in rng.integers(len(ys), size=150):
    p = PT[ys[i], xs[i]]
    a = np.arctan2(p[2] - BOWL[2], p[0] - BOWL[0]) + np.pi / 2
    d = v3(np.cos(a), 0, np.sin(a)) * 0.035
    board.stroke(view.P(np.array([p - d, p, p + d])), letter.but(width=14, pickup=0.25), bowl_col(ys[i], xs[i], rng),
                 wobble=0.3)
water = (WHAT == 3).astype(np.float32)
board.tape_where(water, feather=0.5)
WATER_D = m((ultra, 1.4), (turq, 1.2), (violet, 0.4), (white, 0.6))
WATER_L = m((turq, 1.0), (ultra, 0.4), (white, 2.4))
# the water gives back the leaves overhead: dark, and a little lighter on the far side
wq = view.P(np.array([BOWL + v3(0, BWATER, z) for z in (-0.1, 0.1)]))
for k, yy in enumerate(np.linspace(wq[1, 1] - 6, wq[0, 1] + 6, 9)):
    f = k / 8
    c = scale(m((WATER_D, 1.0), (violet, 0.3), (WATER_L, 0.25 + 0.6 * f)), rng.uniform(0.62, 0.72) + 0.15 * f)
    xc = wq[0, 0] + rng.normal(0, 6)
    board.stroke([(xc - 150, yy + rng.normal(0, 3)), (xc, yy + rng.normal(0, 2)), (xc + 150, yy + rng.normal(0, 3))],
                 one_inch.but(width=26, pickup=0.03, opacity=0.98, level=0.8), c, wobble=1.0)
board.untape()
board.stage("the bowl")

# =====================================================================================================
# 5. Where the crown stops and the plain sun begins: cut once, from the shade side, along its length.
th = np.linspace(-np.pi, np.pi, 1400)
rim_r = CROWN_R * (1 + 0.07 * np.sin(3 * th + 1.0) + 0.05 * np.sin(7 * th + 2.0) + 0.03 * np.sin(13 * th + 0.3)) * 0.965
crown_ground = np.stack([CROWN_C[0] + rim_r * np.cos(th), np.zeros_like(th), CROWN_C[1] + rim_r * np.sin(th)], 1)
crown_ground[:, [0, 2]] -= CH * SUN[[0, 2]] / SUN[1]
cq = view.P(crown_ground)
ok = (cq[:, 0] > -30) & (cq[:, 0] < W + 30) & (cq[:, 1] > -30) & (cq[:, 1] < H + 30) & (crown_ground[:, 2] > 0.2)
EDGE = scale(m((violet, 1.5), (ultra, 1.0), (magenta, 0.6), (white, 0.5)), 0.6)
board.tape_where(SHADE.astype(np.float32), feather=0.6)
if ok.sum() > 2:
    seg = cq[ok][::6]
    board.stroke(seg, letter.but(width=16), EDGE, wobble=0.0, smooth=True)
board.untape()

# what the tree drops: leaflets by the thousand, and pods
# pebbles, each with the bit of shadow that sits it down
board.tape_where(earth_m)
PEB = [m((ochre, 0.6), (white, 2.0), (magenta, 0.1)), m((ochre, 0.4), (white, 1.4), (ultra, 0.2)),
       m((orange, 0.3), (ochre, 0.5), (white, 1.6))]
for k in range(14):
    p = v3(rng.uniform(-1.6, 1.8), 0.0, rng.uniform(0.3, 2.2))
    if np.hypot(*((p - DOG_C)[[0, 2]] * [0.8, 1.6])) < 0.7 or np.hypot(*(p - BOWL)[[0, 2]]) < 0.2:
        continue
    q = view.P(p)
    if not (0 <= q[0] < W and 0 <= q[1] < H):
        continue
    s_ = view.scale_at(p)
    lit = canopy.light(p + v3(0, 0.01, 0)) > 0.3
    rad = rng.uniform(0.012, 0.022) * s_
    peb = letter.but(pickup=0.0, taper=(0.45, 0.45), thickness=0.5)
    c = PEB[rng.integers(3)]
    sh = view.P(p - v3(SUN[0], 0, SUN[2]) * 0.012)
    board.dab(sh[0] - rad * 0.3, sh[1] + rad * 0.35, peb.but(width=rad * 1.3), scale(SH["deep"], 0.5 if lit else 0.6),
              angle=0.15, length=rad * 3.0)
    board.dab(q[0], q[1], peb.but(width=rad * 1.4),
              scale(c, 1.0 if lit else 0.55) if lit else scale(m((c, 1.0), (violet, 0.6)), 0.6), angle=rng.uniform(-0.3, 0.3), length=rad * 2.4)
POD = m((ochre, 1.4), (magenta, 0.4), (orange, 0.3), (white, 0.5))
for (px0, pz0, ang, bend) in ((-1.05, 2.3, 0.4, 0.03), (0.75, 1.75, -0.6, -0.035), (1.1, 0.95, 1.2, 0.025),
                              (-0.9, 0.55, 2.6, 0.03), (0.15, 2.55, 0.2, -0.02), (-0.45, 0.62, -0.3, 0.025)):
    t = np.linspace(-1, 1, 7)
    Lp = 0.17
    pts3 = np.array([v3(px0 + np.cos(ang) * Lp / 2 * u - np.sin(ang) * bend * (1 - u * u), 0.004,
                        pz0 + np.sin(ang) * Lp / 2 * u + np.cos(ang) * bend * (1 - u * u)) for u in t])
    q = view.P(pts3)
    lit = canopy.light(pts3[3]) > 0.5
    sc = view.scale_at(pts3[3])
    base = m((POD, 1), (white, 0.6), (cadyel, 0.2)) if lit else scale(m((POD, 1), (violet, 0.8)), 0.65)
    board.stroke(q, letter.but(width=0.022 * sc, pickup=0.1, thickness=0.3, taper=(0.25, 0.3)),
                 [scale(base, 0.85), base, scale(base, 0.8)], wobble=0.0)
board.untape()
board.stage("the edge, and what the tree drops")

# =====================================================================================================
# 6. Sun handed on: the one the bowl's water throws back at me. The only white on the board.
gl = np.nonzero(WHAT == 3)
pw = PT[gl]
v = eye - pw
v /= np.linalg.norm(v, axis=-1, keepdims=True)
hv = v + SUN
hv /= np.linalg.norm(hv, axis=-1, keepdims=True)
spec = (hv[:, 1] > 0.9985) & (LIGHT[gl] > 0.5)
if spec.any():
    cy_, cx_ = gl[0][spec].mean(), gl[1][spec].mean()
    board.tape_where(water)
    glint = Brush(width=12, bristle=1.4, opacity=1.0, pickup=0.0, thickness=1.0, taper=(0.3, 0.3))
    board.dab(cx_, cy_, glint.but(width=20), white, angle=0.04, length=64)
    board.dab(cx_ + 52, cy_ - 7, glint.but(width=9), white, angle=0.04, length=16)
    board.untape()
board.stage("sun handed on")

finish(board, HERE, title="Calle Sahuaripa, 43°", year=2024, medium="Acrylic on primed plywood")
