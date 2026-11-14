"""Itzel Moroyoqui - Bulevar Solidaridad, 47°

A bus shelter on Bulevar Solidaridad roofed with green corrugated fibreglass, a quarter past two in
July. She knelt on the pavement under it with the board flat beside her and looked down, nearer
than before. The roof is all above the top of the board. What is on it is the concrete, her helmet
where she put it down at the edge of the shade, and what the roof does to the sun on its way
through: it lets the green by and keeps the rest.

Painted the way the roof works. Everything goes on first as the sun has it, the whole board, the
helmet pink all over. Then the roof goes on over that as a glaze, one corrugation to a brushload.
Then what stops the light altogether: the purlin, the leaves lying in the valleys of the lámina,
somebody's sandal.
"""
import os
import sys
from pathlib import Path

import numpy as np
from scipy.ndimage import gaussian_filter, gaussian_filter1d

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[3]))
sys.path.insert(0, str(HERE.parents[1]))

from engine import Board, Brush, hexc, mix, scale  # noqa: E402
from engine.studio import finish  # noqa: E402
from tools import (Canopy, Floor, View, blocked, fur, loads, march, normals, plywood,  # noqa: E402
                   sd_ellipsoid, shape_dab, smin, v3)

DEBUG = os.environ.get("ITZEL_DEBUG")
W, H = 1640, 1640
rng0 = np.random.default_rng(4703)
PRIMER = hexc("#f1efe8")
board = Board(W, H, PRIMER, plywood(W, H, rng0), seed=47, light=(0.6, -0.45))
board.dries_off_board = False
rng = board.rng
view = View(W, H, 1500, 0.95, 55)
floor = Floor(board, view)

# --- tubes -----------------------------------------------------------------------------------
white = hexc("#fbfaf5")
ultra, violet, turq = hexc("#26308f"), hexc("#4a2a86"), hexc("#0f8f95")
magenta, orange, cadyel = hexc("#c4206a"), hexc("#f2601c"), hexc("#f4c21c")
lemon, ochre = hexc("#eee65a"), hexc("#c99a3c")
m = mix

# --- the shelter -------------------------------------------------------------------------------
EL = np.radians(60)
SUN_H = np.array([0.80, -0.60])                    # the sun: high, to her right and a little behind
SUN = v3(SUN_H[0] * np.cos(EL), np.sin(EL), SUN_H[1] * np.cos(EL))
K = SUN[[0, 2]] / SUN[1]
RH = 2.35                                          # the roof
E0 = np.array([-0.30, 0.12])                       # a point of its shade's edge, on the pavement
EE = np.array([1.14, 1.38]) / np.hypot(1.14, 1.38)  # along the eave
NN = np.array([-EE[1], EE[0]])                     # in under the roof
KN = -float(K @ NN)                                # how far in a centimetre of height throws its edge
R0 = E0 + RH * K
LAM, DEPTH = 0.076, 0.011                          # the lámina's wave
SW, LAP, U0 = 11 * LAM, 0.095, -0.636              # a sheet, the lap onto the next, where the first starts
ENDS = np.array([0.0, 0.03, 0.0, -0.035, 0.012, 0.0, 0.0])   # nobody cut the sheets to one length
PURLINS, PURLIN_W = (0.50, 1.72), 0.027
HOLES = [(0.556, 0.395, 0.040), (0.612, 0.325, 0.021), (1.50, 0.33, 0.030)]   # where stones went through
BITE = (1.52, -0.035, 0.075)                       # a corner gone
# leaves lying in the valleys, mostly where the purlin's screws catch them: (which valley, from, how long)
DRIFTS = [(5, 0.53, 0.30), (6, 0.54, 0.13), (10, 0.53, 0.46), (14, 0.55, 0.22), (15, 0.53, 0.09), (3, 1.22, 0.34),
          (19, 0.54, 0.38), (9, 1.73, 0.3), (-1, 0.54, 0.24)]


def sheet_end(j):
    return ENDS[np.clip(np.asarray(j, int) + 1, 0, len(ENDS) - 1)]


def roof_layers(U, V):
    """How many sheets of fibreglass stand over each point of the roof's plane, and where nothing
    gets through at all."""
    hc = DEPTH * np.cos(2 * np.pi * U / LAM)
    sj = np.floor((U - U0) / SW)
    fr = U - U0 - sj * SW
    count = (V > sheet_end(sj) + KN * hc).astype(int) + ((fr > SW - LAP) & (V > sheet_end(sj + 1) + KN * hc))
    count[np.hypot(U - BITE[0], V - BITE[1]) < BITE[2]] = 0
    for hu, hv, hr in HOLES:
        th = np.arctan2(V - hv, U - hu)
        count[np.hypot(U - hu, V - hv) < hr * (1 + 0.28 * np.sin(3 * th + hu * 40) + 0.17 * np.sin(5 * th + 1))] = 0
    solid = np.zeros(U.shape, bool)
    for pv in PURLINS:
        solid |= np.abs(V - pv) < PURLIN_W
    for j, v0, ln in DRIFTS:                              # leaves, lying where the valleys hold them
        uc = (j + 0.5) * LAM
        t = np.clip((V - v0) / ln, 0, 1)
        solid |= (np.abs(U - uc) < 0.019 * np.sin(np.pi * t) ** 0.6 + 1e-9) & (V > v0) & (V < v0 + ln)
    return count, solid & (count > 0)


CELL, GX0, GZ0 = 0.004, -0.60, -1.20
gzz, gxx = np.mgrid[0:720, 0:850].astype(np.float64)
qx, qz = GX0 + gxx * CELL - R0[0], GZ0 + gzz * CELL - R0[1]
COUNT, SOLID = roof_layers(qx * EE[0] + qz * EE[1], qx * NN[0] + qz * NN[1])
through_open = Canopy((COUNT == 0).astype(float), GX0, GZ0, CELL, RH, SUN)
through_one = Canopy(((COUNT == 1) & ~SOLID).astype(float), GX0, GZ0, CELL, RH, SUN)
through_two = Canopy(((COUNT == 2) & ~SOLID).astype(float), GX0, GZ0, CELL, RH, SUN)


def G3(u, v, y=0.0):
    """A place given along the eave and in from it, as a point."""
    q = E0 + np.multiply.outer(u, EE) + np.multiply.outer(v, NN)
    return np.stack([q[..., 0], np.broadcast_to(y, q[..., 0].shape), q[..., 1]], -1)


def uv(p):
    q = np.asarray(p)[..., [0, 2]] - E0
    return q @ EE, q @ NN


# --- the helmet, where she put it down ---------------------------------------------------------
HEL = G3(0.60, -0.115) + v3(0, 0.086, 0)
HF = v3(0.447, 0, -0.894)                          # its face, turned to her and to the sun
HSD = v3(0.894, 0, 0.447)
HR = v3(0.160, 0.133, 0.122)


def hlocal(p):
    q = p - HEL
    return np.stack([q @ HF, q[..., 1], q @ HSD], -1)


CHIN_C, CHIN_R = v3(0.072, -0.052, 0.0), v3(0.108, 0.043, 0.104)     # the bar across the jaw, standing proud


def helmet_sdf(p):
    q = hlocal(p)
    return smin(sd_ellipsoid(q, 0.0, HR), sd_ellipsoid(q, CHIN_C, CHIN_R), 0.018)


# --- what she sees at every point of the board ---------------------------------------------------
rays = view.rays()
eye = view.eye
tg = -eye[1] / np.minimum(rays[..., 1], -1e-9)
G = eye + rays * tg[..., None]
T = tg.copy()
WHAT = np.zeros((H, W), np.int8)                   # 0 pavement, 1 shell, 2 visor, 3 the stripe
NRM = np.zeros((H, W, 3))
NRM[..., 1] = 1
c = view.P(np.array([HEL + v3(x, y, z) for x in (-0.2, 0.2) for y in (-0.086, 0.14) for z in (-0.2, 0.2)]))
x0, x1 = max(0, int(c[:, 0].min()) - 6), min(W, int(c[:, 0].max()) + 6)
y0, y1 = max(0, int(c[:, 1].min()) - 6), min(H, int(c[:, 1].max()) + 6)
t = march(eye, rays[y0:y1, x0:x1].reshape(-1, 3), helmet_sdf, 0.5, 2.6).reshape(y1 - y0, x1 - x0)
near = t < T[y0:y1, x0:x1]
T[y0:y1, x0:x1] = np.where(near, t, T[y0:y1, x0:x1])
WHAT[y0:y1, x0:x1][near] = 1
PT = eye + rays * T[..., None]
HELM = WHAT == 1
NRM[HELM] = normals(helmet_sdf, PT[HELM])
loc = hlocal(PT)
WHAT[HELM & (np.abs(np.abs(loc[..., 2]) - 0.017) < 0.007)] = 3
port = (loc[..., 0] > 0.030) & (loc[..., 1] > -0.022 + 0.10 * np.abs(loc[..., 2])) & \
       (loc[..., 1] < 0.074 - 0.16 * np.abs(loc[..., 2])) & \
       (sd_ellipsoid(loc, 0.0, HR) < sd_ellipsoid(loc, CHIN_C, CHIN_R) + 0.004)
WHAT[HELM & port] = 2
GROUND = WHAT == 0

# the sun at every point: let by, passed through one sheet, through two, or stopped
LO = np.clip(through_open.light(PT), 0, 1)
L1 = np.clip(through_one.light(PT), 0, 1)
L2 = np.clip(through_two.light(PT), 0, 1)
LB = np.clip(1 - LO - L1 - L2, 0, 1)
HB = np.zeros((H, W), bool)                        # where the helmet stands in the sun's way
nearh = np.hypot(PT[..., 0] - HEL[0], PT[..., 2] - HEL[2]) < 0.5
HB[nearh] = blocked(PT[nearh] + NRM[nearh] * 0.004, SUN, helmet_sdf, far=0.7)
ROOF = LO < 0.5                                    # under the roof's shade

if DEBUG:
    from PIL import Image
    Path(HERE / ".scratch").mkdir(exist_ok=True)
    dbg = np.stack([LO, L1 + L2, LB], -1) * np.where(HB, 0.5, 1.0)[..., None]
    dbg[HELM] = dbg[HELM] * 0.6 + 0.4 * (WHAT[HELM, None] / 3.0)
    Image.fromarray((dbg * 255).astype(np.uint8)).save(HERE / ".scratch/light.png")

# --- colours ---------------------------------------------------------------------------------------
SUN_BASE = m((white, 6), (ochre, 0.5), (cadyel, 0.25), (magenta, 0.10), (orange, 0.08))
SUNLIT = [m((SUN_BASE, 4), (lemon, 0.4)),
          m((SUN_BASE, 4), (magenta, 0.10), (white, 0.6)),
          m((SUN_BASE, 4), (orange, 0.12)),
          m((SUN_BASE, 4), (ochre, 0.25)),
          m((SUN_BASE, 4), (white, 1.5))]
# the roof, as glazes: turquoise and lemon, there being no green in the tin
GLZ = {"lemon": m((turq, 1.0), (lemon, 2.6), (white, 1.4)),
       "mid": m((turq, 1.0), (lemon, 1.9), (white, 1.3)),
       "blue": m((turq, 1.3), (lemon, 1.2), (ultra, 0.12), (white, 1.3)),
       "old": m((turq, 1.0), (lemon, 1.8), (ochre, 0.5), (white, 1.2))}
DARK = m((ultra, 1.5), (violet, 1.5), (magenta, 0.3))

two_inch = Brush(width=80, bristle=3.0, opacity=0.97, pickup=0.0, deplete=0.0010, jitter=0.03,
                 thickness=0.12, wander=1.2, gap=0.03)
one_inch = Brush(width=34, bristle=1.7, opacity=0.95, pickup=0.0, deplete=0.0008, jitter=0.03,
                 thickness=0.25, wander=0.8, gap=0.03)
letter = Brush(width=14, bristle=1.2, opacity=0.95, pickup=0.2, deplete=0.0001, jitter=0.03, thickness=0.15,
               taper=(0.05, 0.08), gap=0.0)

# =====================================================================================================
# 1. The light, all of it: the whole board as the sun would have it if the roof were not there.
ground_m = GROUND.astype(np.float32)
board.tape_where(ground_m, feather=0.7)
loads(board, view, G, ground_m, two_inch, lambda p, r: SUNLIT[r.integers(len(SUNLIT))], 360, 0.5,
      lambda x, z: 0.24 + 0.1 * np.sin(1.3 * x + z), rng, width_m=0.075, jitter=0.12, wobble=3)
board.dry()
loads(board, view, G, ground_m, two_inch.but(opacity=0.85, dryness=0.3), lambda p, r: SUNLIT[r.integers(len(SUNLIT))],
      130, 0.36, 0.9, rng, width_m=0.06, jitter=0.4, wobble=3)
board.dry()

# the concrete: a broom dragged across it the day it was poured, and the cuts made after
JA = 0.24                                          # the way the slabs lie, against the way I am kneeling
jd, jn = np.array([np.cos(JA), np.sin(JA)]), np.array([-np.sin(JA), np.cos(JA)])
for k in range(110):
    cpt = np.array([rng.uniform(-1.3, 1.3), rng.uniform(0.05, 2.0)])
    if not floor.on_board(cpt, 40):
        continue
    L = rng.uniform(0.25, 0.7)
    col = scale(m((SUN_BASE, 3), (ochre, rng.uniform(0.3, 0.9)), (violet, rng.uniform(0.0, 0.12))), rng.uniform(0.9, 1.0))
    floor.stroke([cpt - jd * L / 2, cpt, cpt + jd * L / 2], letter.but(pickup=0.0, opacity=rng.uniform(0.3, 0.6)),
                 col, width_m=rng.uniform(0.0025, 0.004), wobble=0.6)
JOINT = m((ochre, 1.2), (violet, 0.35), (white, 1.5))
for a, b in ((np.array([-0.15, 1.02]) - jd * 1.6, np.array([-0.15, 1.02]) + jd * 1.6),
             (np.array([-0.40, 0.6]) - jn * 0.7, np.array([-0.40, 0.6]) + jn * 1.6)):
    for s0 in np.arange(0, 1, 0.125):                  # reloaded as it goes, so it never runs dry
        p0, p1 = a + (b - a) * s0, a + (b - a) * (s0 + 0.13)
        if floor.on_board((p0 + p1) / 2, 60):
            floor.stroke([p0, (p0 + p1) / 2, p1], letter.but(pickup=0.0, taper=(0.02, 0.02)),
                         scale(JOINT, rng.uniform(0.85, 1.0)), width_m=0.007, wobble=0.4)

# what is lying on it: gum trodden flat, two bottle caps. Round things, laid round.
GUM = m((violet, 1.0), (ultra, 0.6), (ochre, 1.0), (white, 0.7))
for (gx_, gz_, gr) in ((-0.22, 0.42, 0.017), (-0.05, 1.33, 0.02), (0.52, 0.93, 0.015), (-0.62, 0.95, 0.019),
                       (0.36, 0.30, 0.014), (-0.30, 1.62, 0.022), (0.86, 1.52, 0.02), (0.05, 0.70, 0.012)):
    floor.dab((gx_, gz_), gr, one_inch.but(opacity=0.9, thickness=0.05), scale(GUM, rng.uniform(0.75, 0.95)),
              angle=rng.uniform(0, 3))
CAP = m((orange, 2.0), (magenta, 0.7), (white, 0.25))
CAPS = ((0.45, 0.45), (-0.10, 0.98))
for cx_, cz_ in CAPS:
    floor.dab((cx_ - SUN_H[0] * 0.005, cz_ - SUN_H[1] * 0.005), 0.0155, one_inch.but(thickness=0.05),
              scale(GUM, 0.8))
    floor.dab((cx_, cz_), 0.0145, one_inch.but(thickness=0.5), CAP, angle=0.3)
    floor.dab((cx_ + 0.003, cz_ - 0.002), 0.0065, one_inch.but(thickness=0.3), m((CAP, 1), (white, 1.4), (cadyel, 0.3)))
board.untape()
board.dry()

# the helmet, pink all over, as it is out on the road
D_HEL = np.zeros((H, W, 3))
D_HEL[...] = -HF
D_RING = np.cross(NRM, v3(0, 1, 0))


def shell_sun(y, x, r):
    d = float(NRM[y, x] @ SUN)
    if d > 0.8:
        cmix = m((magenta, 1.0), (white, 2.6), (orange, 0.22))
    elif d > 0.45:
        cmix = m((magenta, 1.0), (white, 1.25), (orange, 0.18))
    elif d > 0.08:
        cmix = m((magenta, 1.0), (white, 0.45))
    else:
        cmix = scale(m((magenta, 1.0), (violet, 0.55), (white, 0.2)), 0.8)
    return scale(cmix, r.uniform(0.94, 1.06))


def stripe_sun(y, x, r):
    d = float(NRM[y, x] @ SUN)
    cmix = m((cadyel, 1.0), (lemon, 1.0), (white, 1.6)) if d > 0.45 else \
        m((cadyel, 1.0), (white, 0.4)) if d > 0.08 else m((cadyel, 1.0), (orange, 0.3), (violet, 0.35))
    return scale(cmix, r.uniform(0.95, 1.05))


def visor_sun(y, x, r):
    up = float(NRM[y, x, 1])
    cmix = m((ultra, 1.2), (turq, 0.5), (white, 1.3)) if up > 0.42 else scale(DARK, 0.5 if up > 0.2 else 0.36)
    return scale(cmix, r.uniform(0.92, 1.06))


shell_m, stripe_m, visor_m = [(WHAT == k).astype(np.float32) for k in (1, 3, 2)]
helm_m = (WHAT > 0).astype(np.float32)
board.tape_where(helm_m, feather=0.6)
ys_, xs_ = np.nonzero(helm_m)
for yy in np.arange(ys_.min() - 10, ys_.max() + 20, 22):          # a coat under everything, so no primer shows
    board.stroke([(xs_.min() - 40, yy + 14), (xs_.max() + 40, yy - 14)], one_inch.but(width=40, opacity=0.99),
                 m((magenta, 1.0), (white, 1.25), (orange, 0.18)))
board.dry()
fur(board, view, PT, NRM, D_HEL, shell_m, one_inch, shell_sun, rng, 150, 0.11, wobble=0.5)
fur(board, view, PT, NRM, D_HEL, shell_m, one_inch.but(width=24, opacity=0.9), shell_sun, rng, 130, 0.07, wobble=0.5)
board.tape_where(stripe_m, feather=0.6)
fur(board, view, PT, NRM, D_HEL, stripe_m, one_inch.but(width=26), stripe_sun, rng, 40, 0.09, wobble=0.3)
board.tape_where(visor_m, feather=0.6)
fur(board, view, PT, NRM, D_RING, visor_m, one_inch.but(width=30, opacity=0.99), lambda y, x, r: scale(DARK, 0.42),
    rng, 60, 0.12, wobble=0.3)
fur(board, view, PT, NRM, D_RING, visor_m, one_inch.but(width=18), visor_sun, rng, 50, 0.08, wobble=0.3)
board.untape()
board.dry()
board.stage("the light, all of it, as if there were no roof")

# =====================================================================================================
# 2. The roof, put on over it. A glaze the colour of what the fibreglass lets through, one
#    corrugation to a brushload, laid from the eave inward. Where two sheets lap, two coats.
glaze2 = Brush(width=80, bristle=3.2, opacity=0.9, pickup=0.0, deplete=0.0009, jitter=0.015, loadvar=0.035,
               thickness=0.0, wander=0.3, gap=0.0, glaze=True, taper=(0.012, 0.02))
film = letter.but(glaze=True, pickup=0.0, thickness=0.0, loadvar=0.0, jitter=0.0, gap=0.0, bristle=2.0,
                  taper=(0.0, 0.0))


def roof_mix(u, v, r):
    w = {"lemon": 0.15 + 4.0 * max(0.0, 0.5 - v), "mid": 1.0, "blue": 0.1 + 2.2 * max(0.0, v - 0.45), "old": 0.3}
    keys = list(w)
    pr = np.array([w[k] for k in keys])
    a, b = r.choice(len(keys), 2, p=pr / pr.sum())
    far = float(np.clip((v - 0.5) / 1.3, 0, 1))        # further in under the roof, less of it gets there
    return m((GLZ[keys[a]], 1.0), (GLZ[keys[b]], r.uniform(0.0, 0.6)), (white, r.uniform(0.0, 0.3) * (1 - far)),
             (ultra, 0.10 * far), (turq, 0.25 * far))


def ribs(mask, us, width_m, brush, v_from=-0.10, mixer=roof_mix, skip=0.0):
    board.tape_where(mask, feather=1.1)
    for u in us:
        v = v_from + rng.uniform(-0.45, 0.0)
        while v < 2.1:
            L = rng.uniform(0.55, 0.95) * (1 + 0.45 * max(v, 0))
            mid = G3(u, v + L / 2)
            if floor.on_board(mid, 700) and rng.random() >= skip:
                iy, ix = np.clip(view.P(mid)[::-1].astype(int), 0, [H - 1, W - 1])
                du = rng.normal(0, 0.003)
                if True:
                    floor.stroke(G3(np.full(4, u) + du * np.array([0, 0.3, 0.7, 1]), np.linspace(v, v + L, 4)), brush,
                                 mixer(u, v + L / 2, rng), width_m=width_m, wobble=1.0)
            v += L * 0.99
    board.untape()


def across(mask, brush, mixer, angle, spacing, feather=1.0, reach=260):
    """Parallel strokes over a small shape on the board, each one mix, none laid twice."""
    ys, xs = np.nonzero(mask > 0.5)
    if not len(xs):
        return
    board.tape_where(mask, feather=feather)
    cc = np.array([xs.mean(), ys.mean()])
    d = np.array([np.cos(angle), np.sin(angle)])
    nr = np.array([-d[1], d[0]])
    off = (np.stack([xs, ys], 1) - cc) @ nr
    for o in np.arange(off.min() - spacing * 0.2, off.max() + spacing * 0.5, spacing):
        o += rng.normal(0, spacing * 0.06)
        sel = np.abs(off - o) < spacing
        if not sel.any():
            continue
        al = (np.stack([xs[sel], ys[sel]], 1) - cc) @ d
        a0, a1 = cc + nr * o + d * (al.min() - brush.width), cc + nr * o + d * (al.max() + brush.width)
        board.stroke([a0, (a0 + a1) / 2 + nr * rng.normal(0, 2), a1], brush, mixer(rng), wobble=0.6)
    board.untape()


shade_g = (ROOF & GROUND).astype(np.float32)
rib_us = (np.arange(-6, 34) + 0.5) * LAM
ribs(shade_g, rng.permutation(rib_us), LAM * 1.05, glaze2)
lap_g = ((L2 > 0.5) & GROUND).astype(np.float32)
ribs(lap_g, [U0 + k * SW - LAP / 2 for k in range(1, 5)], LAP * 1.2, glaze2.but(opacity=0.78))
# the sheets are not new: a second, thin, dirtier coat on some of the corrugations, the whole way in
board.tape_where(shade_g, feather=1.1)
for u in rng.permutation(rib_us)[:13]:
    floor.stroke(G3(np.full(5, u), np.linspace(-0.1, 2.2, 5)), glaze2.but(opacity=0.3, taper=(0.0, 0.0), deplete=0.0002),
                 m((GLZ["old"], 1.0), (GLZ["blue"], rng.uniform(0, 0.8))), width_m=LAM, wobble=0.6)
board.untape()

# and over the helmet, as far up it as the roof's shade comes
hq = view.P(np.array([HEL, HEL - HF * 0.1]))
hel_ang = float(np.arctan2(hq[1, 1] - hq[0, 1], hq[1, 0] - hq[0, 0]))
helm_sh = ((WHAT > 0) & ROOF).astype(np.float32)
across(helm_sh, glaze2.but(width=44, bristle=2.2, opacity=0.86), lambda r: roof_mix(0, r.uniform(0.3, 0.9), r), hel_ang, 40)
board.dry()
board.stage("the roof, put on over it as a glaze")

# =====================================================================================================
# 3. What stops the light altogether: the purlin, the leaves lying in the valleys, the helmet. The
#    old shade, ultramarine and violet, and it is a glaze as well, the same one everywhere. Over
#    the green it comes out the colour of the roof's underside; over the open concrete it is the
#    blue it always was.
STOP = {"mid": m((ultra, 1.5), (violet, 1.2), (white, 2.9)),
        "cool": m((ultra, 1.7), (turq, 0.5), (violet, 0.6), (white, 2.9)),
        "warm": m((violet, 1.7), (ultra, 0.7), (magenta, 0.4), (white, 2.9))}


def stop_mix(r, pink=0.0):
    if r.random() < pink:
        return m((STOP["warm"], 1.0), (magenta, 0.35), (white, 0.5))
    keys = list(STOP)
    a, b = r.choice(len(keys), 2)
    return m((STOP[keys[a]], 1.0), (STOP[keys[b]], r.uniform(0, 0.7)), (white, r.uniform(0.0, 0.25)))


board.tape_where(np.clip((LB - 0.12) / 0.6, 0, 1) * ground_m)
for pv in PURLINS:                                    # the purlin, in loads along its length
    u = -0.6
    while u < 2.7:
        L = rng.uniform(0.3, 0.5) * (1 + 0.3 * pv)
        if floor.on_board(G3(u + L / 2, pv), 200):
            floor.stroke(G3(np.linspace(u, u + L, 4), np.full(4, pv) + rng.normal(0, 0.002, 4)), glaze2.but(opacity=0.92),
                         stop_mix(rng), width_m=PURLIN_W * 3.0, wobble=0.5)
        u += L * 0.98
for jv, v0, ln in DRIFTS:                             # each drift of leaves, one touch along its valley
    uc = (jv + 0.5) * LAM
    if floor.on_board(G3(uc, v0 + ln / 2), 100):
        floor.stroke(G3(np.full(4, uc), np.linspace(v0 - 0.03, v0 + ln + 0.03, 4)), glaze2.but(opacity=0.9),
                     stop_mix(rng), width_m=0.06, wobble=0.5)
board.untape()

# the helmet's own shadow, pinker close in where the shell throws its colour down
hsh = (GROUND & HB).astype(np.float32)
nq = view.P(G3(np.array([0.6, 0.6]), np.array([0.0, 0.3])))
n_ang = float(np.arctan2(nq[1, 1] - nq[0, 1], nq[1, 0] - nq[0, 0]))
across(hsh, glaze2.but(width=46, bristle=2.2, opacity=0.9), lambda r: stop_mix(r, pink=0.45), n_ang, 42, feather=2.2)
# the side of it turned from the sun, the same
turned = ((WHAT > 0) & HB & ~ROOF).astype(np.float32)
across(turned, glaze2.but(width=40, bristle=2.0, opacity=0.6), lambda r: stop_mix(r, pink=0.6), hel_ang, 36, feather=3.0)
board.dry()

# where it sits on the concrete, and the trim round the visor
ring = np.array([HEL + HF * (0.124 * np.cos(a)) + HSD * (0.094 * np.sin(a)) - v3(0, 0.084, 0)
                 for a in np.linspace(0.3, 3.6, 14)])
board.tape_where(ground_m, feather=0.8)
board.stroke(view.P(ring), letter.but(width=9, pickup=0.0), scale(DARK, 0.42), wobble=0.0)
board.untape()
ys, xs = np.nonzero(visor_m > 0.5)
if len(xs):
    cols = np.arange(xs.min() + 2, xs.max() - 1, 6)
    cols = np.array([xx for xx in cols if (xs == xx).any()])
    top = np.array([ys[xs == xx].min() for xx in cols], float)
    bot = np.array([ys[xs == xx].max() for xx in cols], float)
    board.tape_where(helm_m, feather=0.6)
    for yy in (top, bot):
        fit = np.polyval(np.polyfit(cols, yy, 4), cols)
        board.stroke(np.stack([cols, fit], 1)[::4], letter.but(width=6, pickup=0.0), scale(DARK, 0.4), wobble=0.0)
    board.untape()
board.dry()
board.stage("what stops the light altogether")

# =====================================================================================================
# 4. The edge, cut once. Nearer, it has a width: the sun is not a point, and the line between its
#    light and the roof's is as wide as the lettering brush. One pass, from the shade side, half
#    strength, reloaded as it goes.
us_ = np.arange(-0.5, 2.6, 0.004)
hc_ = DEPTH * np.cos(2 * np.pi * us_ / LAM)
sj_ = np.floor((us_ - U0) / SW)
fr_ = us_ - U0 - sj_ * SW
ve = np.where(fr_ > SW - LAP, np.minimum(sheet_end(sj_), sheet_end(sj_ + 1)), sheet_end(sj_)) + KN * hc_
inb = np.abs(us_ - BITE[0]) < BITE[2]
ve[inb] = np.maximum(ve[inb], BITE[1] + np.sqrt(BITE[2] ** 2 - (us_[inb] - BITE[0]) ** 2))
ve = gaussian_filter1d(ve, 0.009 / 0.004)
EDGE_G = m((GLZ["lemon"], 1.0), (GLZ["mid"], 0.6))
board.tape_where(ground_m, feather=0.8)
step = 75
for i0 in range(0, len(us_) - step, step):
    seg = G3(us_[i0:i0 + step + 1:5], ve[i0:i0 + step + 1:5])
    if floor.on_board(seg[len(seg) // 2], 80):
        floor.stroke(seg, film.but(opacity=0.6), EDGE_G, width_m=0.027, wobble=0.0)
board.untape()
# and across the helmet, the same line
ys, xs = np.nonzero((WHAT > 0) & (np.abs(LO - 0.5) < 0.2))
if len(xs) > 30:
    xx = np.arange(xs.min() + 3, xs.max() - 2, 10)
    board.tape_where(helm_m, feather=0.6)
    board.stroke(np.stack([xx, np.polyval(np.polyfit(xs, ys, 3), xx)], 1), film.but(opacity=0.6, width=18),
                 EDGE_G, wobble=0.0)
    board.untape()
board.stage("the edge, cut once, as wide as the sun made it")

# =====================================================================================================
# 5. Sun handed on: off the visor. The only white on the board.
gl = np.nonzero((WHAT == 2) & (LO > 0.5) & ~HB)
if len(gl[0]):
    vv = eye - PT[gl]
    vv /= np.linalg.norm(vv, axis=-1, keepdims=True)
    hv = vv + SUN
    hv /= np.linalg.norm(hv, axis=-1, keepdims=True)
    sp = (hv * NRM[gl]).sum(-1)
    k = np.argsort(sp)[-max(8, len(sp) // 60):]
    cy_, cx_ = gl[0][k].mean(), gl[1][k].mean()
    board.tape_where(visor_m)
    glint = Brush(width=12, bristle=1.4, opacity=1.0, pickup=0.0, thickness=1.0, taper=(0.3, 0.3))
    board.dab(cx_, cy_, glint.but(width=16), white, angle=-0.25, length=58)
    board.dab(cx_ + 44, cy_ - 16, glint.but(width=8), white, angle=-0.25, length=14)
    board.untape()
board.stage("sun handed on")

finish(board, HERE, title="Bulevar Solidaridad, 47°", year=2025, medium="Acrylic and acrylic glaze on primed plywood")
