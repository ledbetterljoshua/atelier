"""Nell Abara - A&E doors, from the ambulance bay, 04:35

Turned round. Fifteen minutes after the last board I am out in the bay with the sodium lamp behind
me, looking back at the doors I stood in. The reception is lit behind the glass, cold, by tubes I
did not choose; the lamp I did not choose either is on the outside of it, on the brick and the kerb
and once, small, in the glass itself. I brought the wheelchair in before I started. With my back to
a lamp for the first time, my own shadow lies in front of me, and the only light in it is the doors'.
"""
import os
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[3]))
sys.path.insert(0, str(HERE.parents[1]))

from engine import Board, Brush, ground, hexc, mix, scale  # noqa: E402
from engine.studio import finish  # noqa: E402
from tools import (Field, Patches, Plane, View, body, crosses, floor_at, lay, line3, one_line, quad, room,  # noqa: E402
                   sheen, standing, sweep, v3)

W, H = 1000, 900
rng0 = np.random.default_rng(435)
board = Board(W, H, hexc("#0b0a0a"), ground.hardboard_mesh(W, H, rng0, pitch=5.4), seed=2010, light=(0.05, -0.95))
board.dries_off_board = False
board.relief_soft = 2.2
rng = board.rng
EYE = (0.0, 1.6, 0.0)
view = View(W, H, 900, 500, 290, EYE)
P = view.P

# --- tubes -----------------------------------------------------------------------------------
black, ultra, umber = hexc("#0b0a0a"), hexc("#1b2a7a"), hexc("#4a2a16")
viridian, ochre, cadred = hexc("#0f6b55"), hexc("#c0902f"), hexc("#c6281c")
lemon, white = hexc("#efe36a"), hexc("#f6f3ea")
night = mix((ultra, 2), (umber, 1), (black, 2))

# the lamp's one colour, as mixed for the last board
SOD = mix((cadred, 1.0), (lemon, 1.6), (ochre, 0.5))
SOD = SOD / SOD.max()
# the tubes behind their diffusers: white with a breath of viridian and lemon
COLD = mix((white, 8), (viridian, 0.5), (lemon, 0.5))
COLD = COLD / COLD.max()

# --- what the surfaces are -------------------------------------------------------------------
A_TARMAC = mix((white, 1.1), (umber, 0.7), (ultra, 0.4), (black, 0.8))          # dry, under the canopy; worn grey
A_YELLOW = mix((lemon, 3), (ochre, 1), (white, 1))
A_PAVE = mix((white, 2.0), (umber, 0.5), (black, 0.7))          # concrete flags, and the kerb
A_BRICK = mix((cadred, 1.2), (umber, 1.5), (ochre, 1.0), (white, 0.8))
A_ALU = mix((white, 1), (umber, 1), (black, 1.0))               # the door frames, bronze anodised
A_SOFFIT = mix((white, 2), (black, 1))
A_WALL = mix((white, 6), (ochre, 0.6))                          # magnolia
A_LINO = mix((white, 3), (viridian, 0.4), (umber, 0.5), (black, 0.5))
A_CEIL = scale(white, 0.9)
A_BEECH = mix((ochre, 1.4), (umber, 1.6), (white, 2.2), (cadred, 0.2))
A_BLUE = mix((ultra, 3), (white, 1))                            # the wheelchair's vinyl
A_SEAT = mix((cadred, 1), (umber, 2), (black, 1))
A_CORK = mix((umber, 3), (ochre, 1.3), (white, 1))
A_STEEL = mix((white, 2), (ultra, 0.2), (umber, 0.3))

UP, DOWN, BACK = v3(0, 1, 0), v3(0, -1, 0), v3(0, 0, -1)

# --- the place, turned round: x is now to my right, z runs from my feet to the doors ------------
XD = -1.0                         # the middle of the doors; I am a metre right of their line
G = 8.0                           # the glass
YP = 0.12                         # the pavement, and the floor inside, above the road
ZK = 5.1                          # the kerb
ZC, YC = 3.3, 3.3                 # the canopy's edge over me, and its soffit
XL, LY, LZ = XD - 3.2, 5.5, -14.3  # the sodium lantern, behind my left shoulder
ZB, XW, YCL = 15.0, 4.2, YP + 2.6  # reception: its back wall, half its width, its ceiling
GX0, GX1, GY1 = XD - 2.7, XD + 2.7, 2.9   # the glazed screen
YT = 2.27                         # its transom


def sstep(x, a, b):
    t = np.clip((np.asarray(x, dtype=np.float64) - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)


def gh(x, z):
    """Height of the ground. The kerb drops flush in front of the doors and ramps up to them."""
    out = sstep(np.abs(np.asarray(x) - XD), 1.1, 1.5)
    return YP * (out * (np.asarray(z) >= ZK) + (1 - out) * np.clip((np.asarray(z) - ZK) / 0.8, 0, 1))


def lum(c):
    c = np.asarray(c)
    return 0.2 * c[..., 0] + 0.7 * c[..., 1] + 0.1 * c[..., 2]


# --- the lamp behind me ---------------------------------------------------------------------------
LENS = np.array([[XL + dx, LY, LZ] for dx in np.linspace(-0.29, 0.29, 6)])
RLS, DA_L = 1.0, 0.7 * 0.24


def sod(Q, N, me=True):
    """How much of the lamp lands at Q on a surface facing N: a cut-off lantern, stopped by the
    canopy over the doors and by me, standing at the origin with my back to it."""
    Q = np.asarray(Q, dtype=np.float64)
    d = LENS - Q[..., None, :]
    d2 = (d * d).sum(-1)
    dist = np.sqrt(d2)
    cl = (d[..., 1] / dist) ** 2
    cp = np.clip((d @ N) / dist, 0, None)
    run = np.maximum(-d[..., 2], 1e-6)
    qy, qz = Q[..., None, 1], Q[..., None, 2]
    yc = qy + d[..., 1] * (qz - ZC) / run
    vis = np.where((qz > ZC) & (yc > YC), 0.0, 1.0)
    if me:
        t = qz / run
        vis = np.where((qz > 0.05) & standing(Q[..., None, 0] + d[..., 0] * t, qy + d[..., 1] * t), 0.0, vis)
    return RLS * DA_L * (cp * cl * vis / (np.pi * d2)).mean(-1)


# --- the tubes inside -----------------------------------------------------------------------------
FIT_X, FIT_Z = (XD - 2.4, XD, XD + 2.4), (10.0, 12.2, 14.2)
_r = np.random.default_rng(6)
fS = np.array([(fx + u, YCL - 0.01, fz + _r.uniform(-0.25, 0.25)) for fx in FIT_X for fz in FIT_Z
               for u in np.linspace(-0.5, 0.5, 6)])
RF = 1.0
fit = Patches(fS, np.tile(DOWN, (len(fS), 1)), np.tile(COLD * RF, (len(fS), 1)), 1.2 * 0.6 / 6)
AMB_IN = 0.22 * fit.onto(v3(XD, YP, 11.0), UP)

GLAZ = Plane((GX0, YP, G), (GX1 - GX0, 0, 0), (0, GY1 - YP, 0))
backwall = Plane((XD - XW, YP, ZB), (2 * XW, 0, 0), (0, YCL - YP, 0))
wallp = Patches.on(backwall, lambda s: A_WALL * (fit.onto(s, BACK) + AMB_IN) / np.pi, 12, 3, facing=BACK)
cold_out = fit + wallp
cold_out.aperture = GLAZ                   # what of the reception gets out through the glass
floor_in = Patches.on(Plane((XD - 4, YP, 8.2), (8, 0, 0), (0, 0, 5)), lambda s: A_LINO * fit.onto(s, UP) / np.pi,
                      8, 4, facing=UP, aperture=GLAZ)

coldF = Field(-7.5, 7.5, 76, 2.2, 7.98, 44, lambda x, z: cold_out.onto(v3(x, float(gh(x, z)), z), UP), smooth=0.8)

# The two lights against each other: the lamp puts as much on the brick as the doors put on their
# own step. Then one exposure for the board, keyed on that step, where both of them land.
PROBE = v3(XD + 0.3, YP, 6.9)
_brick = one_line(A_BRICK) * sod(v3(XD + 3.6, 1.5, G), BACK)
RLS = 0.75 * lum(A_PAVE * coldF.at(PROBE[0], PROBE[2])) / _brick
SKY = v3(0.6, 0.7, 1.0) * 0.04 * float(sod(v3(0, 0, 4.0), UP, me=False))


def wet(x, z):
    """Dry under the canopy; wet out here, past its drip line, the same ragged line as last time."""
    xo = -1.0 - np.asarray(x, dtype=np.float64)
    edge = ZC + 0.2 + 0.25 * (0.5 + 0.5 * np.sin(1.7 * xo + 0.4)) * (0.5 + 0.5 * np.sin(4.3 * xo))
    edge = edge + 0.07 * np.sin(13.0 * xo + 1.0) * np.sin(5.1 * xo) + 0.04 * np.sin(31.0 * xo)   # and blown about, close to
    return np.clip((edge - np.asarray(z)) / 0.16, 0, 1) * 0.85


def ripple(x, z):
    k = (np.sin(7.1 * z + 1.3 * np.sin(9.3 * x)) + 0.7 * np.sin(13.7 * z + 0.4 + 2.0 * np.sin(17.0 * x))
         + 0.5 * np.sin(3.1 * z + 23.0 * x)) / 2.2
    return 0.5 + 0.5 * k


def ground_raw(xs, z, albedo=None):
    """What both lights put on the ground along a line across it at depth z, before exposure."""
    xs = np.atleast_1d(np.asarray(xs, dtype=np.float64))
    Q = np.stack([xs, gh(xs, z), np.full_like(xs, z)], -1)
    alb = (A_PAVE if z >= ZK else A_TARMAC) if albedo is None else albedo
    c = one_line(alb) * sod(Q, UP)[:, None] * SOD + alb * coldF.at(xs, z) + alb * SKY
    return c * (1.0 - 0.75 * wet(xs, z))[:, None]


EXPO = 1.0
_c = ground_raw(PROBE[0], PROBE[2])[0]
lo, hi = 1e-3, 1e7
for _ in range(80):
    mid = np.sqrt(lo * hi)
    if lum(room(_c * mid)) < 0.17:
        lo = mid
    else:
        hi = mid
EXPO = np.sqrt(lo * hi)

# the lit paving, and the lino inside, as lights in their own right: what reaches the soffit, the
# lintel and the foot of the brick comes off them
_px, _pz = np.meshgrid(XD + np.linspace(-3.2, 3.2, 8), np.linspace(5.4, 7.8, 5))
_pS = np.stack([_px.ravel(), np.full(_px.size, YP), _pz.ravel()], -1)
pool = Patches(_pS, np.tile(UP, (len(_pS), 1)),
               np.array([ground_raw(s[0], s[2])[0] / np.pi for s in _pS]), (6.4 / 8) * (2.4 / 5))


def ground_col(xs, z, albedo=None):
    return room(ground_raw(xs, z, albedo) * EXPO)


def outside(Q, N, albedo, me=False):
    """A surface out here: the lamp's one colour, and what comes back off the lit paving."""
    c = one_line(albedo) * sod(Q, N, me=me) * SOD + albedo * (pool.onto(Q, N) + SKY)
    return room(c * EXPO)


GLASS = v3(0.90, 0.93, 0.90)          # what the glass takes out on the way through


def inside(Q, N, albedo, k=1.0):
    return room(albedo * (fit.onto(Q, N) + AMB_IN) * EXPO * k) * GLASS


if os.environ.get("CHECK"):
    print("EXPO", EXPO, "RLS", RLS, "SOD", np.round(SOD, 3), "COLD", np.round(COLD, 3))
    for nm, p in [("glass foot", v3(XD, YP, G)), ("glass head", v3(XD, GY1, G)), ("soffit", v3(XD, YC, G)),
                  ("kerb", v3(0, 0, ZK)), ("drip", v3(0, 0, ZC + 0.3)), ("back floor", v3(XD, YP, ZB)),
                  ("back ceil", v3(XD, YCL, ZB)), ("lamp refl", v3(XL, LY, 2 * G - LZ))]:
        print(f"{nm:12s}", np.round(P(p), 1))
    for z in (2.5, 3.0, 3.6, 4.5, 5.0, 5.3, 6.0, 7.0, 7.8):
        print("ground", z, np.round(ground_col([XD, 0.0, 1.5, 3.0], z), 3).tolist())
    print("brick", np.round(outside(v3(XD + 3.6, 1.5, G), BACK, A_BRICK), 3), np.round(outside(v3(XD + 3.6, 3.0, G), BACK, A_BRICK), 3))
    print("soffit", [np.round(room(A_SOFFIT * (pool.onto(v3(XD, YC, z), DOWN) + floor_in.onto(v3(XD, YC, z), DOWN)
                                              + cold_out.onto(v3(XD, YC, z), DOWN)) * EXPO), 3).tolist() for z in (7.8, 7, 6, 5, 4)])
    print("in wall", np.round(inside(v3(XD, 1.5, ZB), BACK, A_WALL), 3), "floor", np.round(inside(v3(XD, YP, 11), UP, A_LINO), 3),
          "ceil", np.round(inside(v3(XD, YCL, 11), DOWN, A_CEIL), 3))
    sys.exit()

# --- the board's geography ------------------------------------------------------------------------
y_foot = P(v3(0, YP, G))[1]                       # where the wall meets the paving
y_head = P(v3(0, GY1, G))[1]
y_soffit = P(v3(0, YC, G))[1]
x_g0, x_g1 = P(v3(GX0, 0, G))[0], P(v3(GX1, 0, G))[0]
GLAZ_Q = quad(view, [(GX0, YP, G), (GX1, YP, G), (GX1, GY1, G), (GX0, GY1, G)])
ground_poly = np.array([(-80, y_foot), (W + 80, y_foot), (W + 80, H + 80), (-80, H + 80)])

# =============================================================================================
# 1. Imprimatura: thin darks over the black, cold where the doors will be, warm round them.
# =============================================================================================
wash = Brush(width=130, bristle=2.6, opacity=0.4, dryness=0.55, pickup=0.3, thickness=0.2, jitter=0.12, deplete=0.0008)
for i in range(60):
    x, y = rng.uniform(-100, W + 100), rng.uniform(-50, H + 50)
    a = rng.uniform(0, np.pi)
    L = rng.uniform(300, 800)
    cool = np.exp(-((x - 390) / 300) ** 2 - ((y - 340) / 230) ** 2)
    c = mix((ultra, rng.uniform(0.5, 1.2) + 1.2 * cool), (viridian, 0.8 * cool + 0.01),
            (umber, rng.uniform(0.8, 1.8) * (1 - 0.8 * cool) + 0.2), (black, 4))
    board.stroke([(x - np.cos(a) * L / 2, y - np.sin(a) * L / 2), (x + np.cos(a) * L / 2, y + np.sin(a) * L / 2)],
                 wash, c, wobble=10)
board.dry()
board.stage("coloured darks over black")

# =============================================================================================
# 2. The soffit over the doors: the board, and dry strokes along its planks, cold, from what the
#    lino and the lit paving send up.
# =============================================================================================
dark = Brush(width=80, bristle=2.4, opacity=0.5, pickup=0.5, dryness=0.72, thickness=0.3, jitter=0.04, deplete=0.0005,
             taper=(0.1, 0.25))
sof = Plane((XD - 7, YC, G), (14, 0, 0), (0, 0, -(G - 2.6)))


def soffit_shade(Q):
    return room(A_SOFFIT * (pool.onto(Q, DOWN) + floor_in.onto(Q, DOWN) + cold_out.onto(Q, DOWN) + SKY) * EXPO)


# the soffit is planked, and the planks run along the building: strokes along them, each mixed along
# its length, and only where enough comes up off the floor to find them
lay(board, view, sof, dark.but(width=30, dryness=0.7, opacity=0.5), soffit_shade, (1, 0, 0), length=520, cover=1.5, wobble=0.0,
    zref=5.0, shrink=1.0, max_m=9.0, along=9, where=lambda Q: lum(soffit_shade(Q)) > 0.0045, feather=1.5)

board.dry()
board.stage("the soffit, by what the floor sends up")

# =============================================================================================
# 3. The ground: rows across it, each mixed along its length for both lights at once. The road
#    first, then the flags course by course with the joints left as the board.
# =============================================================================================
row = Brush(width=10, opacity=0.85, pickup=0.45, dryness=0.42, thickness=0.5, jitter=0.03, deplete=0.0003,
            taper=(0.02, 0.02))
board.tape(ground_poly, feather=1.0)
PXS = np.linspace(-50, W + 50, 150)


def ground_row(z, width, dy=0.0, brush=row, albedo=None):
    xs = (PXS - view.vx) * z / view.f
    cs = ground_col(xs, z, albedo)
    ls = lum(cs)
    if ls.max() < 0.006:
        return
    pts = P(np.stack([xs, gh(xs, z), np.full_like(xs, z)], -1)) + [0, dy]
    board.stroke(pts, brush.but(width=width), list(cs), smooth=False, opacity=list(np.clip(ls / 0.03, 0, 1) ** 0.8))


y_kerb = P(v3(0, 0, ZK))[1]
NR = 50
for i in range(NR):
    sy = y_kerb + (H + 20 - y_kerb) * ((i + 0.5 + rng.uniform(-0.3, 0.3)) / NR) ** 1.25
    z = float(floor_at(view, 0.0, sy)[2])
    gap = (H + 20 - y_kerb) / NR * 1.25 * ((i + 1) / NR) ** 0.25
    ground_row(z, float(np.clip(gap * 2.1, 5, 34)), rng.normal(0, 1.0))
# the flags: their joints taped out first and left as the board, then each course laid across
courses = [G - 0.02, 7.4, 6.8, 6.2, 5.6, ZK + 0.02]
joints = []
fx = (np.linspace(-60, W + 60, 60) - view.vx)
for zj in courses[1:-1]:
    xs = fx * zj / view.f
    a_ = P(np.stack([xs, gh(xs, zj), np.full_like(xs, zj)], -1))
    joints.append(np.vstack([a_ - [0, 0.6], a_[::-1] + [0, 0.6]]))
for i, (za, zb) in enumerate(zip(courses[:-1], courses[1:])):
    for xj in np.arange(-9.0 + 0.45 * (i % 2), 9.0, 0.9):
        a_, b_ = P(v3(xj, float(gh(xj, za)), za)), P(v3(xj, float(gh(xj, zb)), zb))
        joints.append(np.array([a_ - [0.5, 0], a_ + [0.5, 0], b_ + [0.6, 0], b_ - [0.6, 0]]))
board.tape(*joints, mode="cut", feather=0.9)
for za, zb in zip(courses[:-1], courses[1:]):
    hpx = P(v3(XD + 3, YP, zb))[1] - P(v3(XD + 3, YP, za))[1]
    for s in (0.18, 0.5, 0.82):
        ground_row(za + (zb - za) * s, hpx * 0.6, brush=row.but(dryness=0.34))
board.untape()
board.dry()

# keep clear: the near edge of the hatched box and two of its diagonals. Yellow, which is to say orange.
def marking(corners):
    board.tape(P(np.array([v3(x, 0, z) for x, z in corners])), feather=0.8)
    zs = [z for _, z in corners]
    ya, yb = P(v3(0, 0, max(zs)))[1], min(P(v3(0, 0, min(zs)))[1], H + 10)
    for sy in np.arange(ya + 2, yb, 5.0):
        ground_row(float(floor_at(view, 0.0, sy)[2]), 8.0, brush=row.but(dryness=0.5, pickup=0.0, opacity=0.8), albedo=A_YELLOW)
    board.untape()


marking([(-3.6, 2.65), (2.0, 2.65), (2.0, 2.75), (-3.6, 2.75)])
for k in (1.5, 3.1):
    marking([(1.9 - k - 0.07, 1.9), (1.9 - k + 0.07, 1.9), (2.65 - k + 0.07, 2.65), (2.65 - k - 0.07, 2.65)])

# the kerb's face: it looks straight at the lamp, and is the brightest orange thing on the ground
kx = (PXS - view.vx) * ZK / view.f
ktop = P(np.stack([kx, gh(kx, ZK + 1e-6) + 0.004, np.full_like(kx, ZK)], -1))
kbot = P(np.stack([kx, np.zeros_like(kx), np.full_like(kx, ZK)], -1))
board.tape(np.vstack([ktop, kbot[::-1]]), feather=0.6)
kc = room((one_line(A_PAVE) * sod(np.stack([kx, np.full_like(kx, 0.06), np.full_like(kx, ZK)], -1), BACK)[:, None] * SOD
           + A_PAVE * SKY) * EXPO)
for dy in (-6, 2):
    board.stroke((ktop + kbot) / 2 + [0, dy], row.but(width=14, dryness=0.3, opacity=0.9, pickup=0.0), list(kc), smooth=False)
board.untape()
board.dry()
board.stage("the ground, under both of them")

# =============================================================================================
# 4. The brick either side of the doors: runs of a course at a time, dry, only where the lamp
#    gets in under the canopy. Above that line it is the board.
# =============================================================================================
brick = Brush(width=7.5, opacity=0.8, pickup=0.35, dryness=0.52, thickness=0.4, jitter=0.05, gap=0.08, deplete=0.0012,
              taper=(0.05, 0.08))


def brick_shade(Q):
    return outside(Q, BACK, A_BRICK) * np.exp(rng.normal(0, 0.10))


for x0, x1 in ((GX0 - 6.0, GX0), (GX1, GX1 + 6.0)):
    board.tape(quad(view, [(x0, YP, G), (x1, YP, G), (x1, YC, G), (x0, YC, G)]), feather=0.8)
    wall = Plane((x0 - 0.8, YP - 0.1, G), (x1 - x0 + 1.6, 0, 0), (0, YC - YP + 0.2, 0))
    lay(board, view, wall, brick.but(width=30, dryness=0.5, opacity=0.6, gap=0.0), lambda Q: outside(Q, BACK, A_BRICK) * 0.7,
        (1, 0, 0), length=150, cover=1.5, wobble=0.0, zref=G, where=lambda Q: lum(outside(Q, BACK, A_BRICK)) > 0.012, along=4,
        tape=False)
    lay(board, view, wall, brick, brick_shade, (1, 0, 0), length=52, cover=3.0, wobble=0.5, zref=G,
        where=lambda Q: lum(outside(Q, BACK, A_BRICK)) > 0.012, tape=False)
    board.untape()
lintel = Plane((GX0, GY1, G), (GX1 - GX0, 0, 0), (0, YC - GY1, 0))
lay(board, view, lintel, brick.but(dryness=0.62), brick_shade, (1, 0, 0), length=64, cover=1.2, wobble=0.6, zref=G,
    where=lambda Q: lum(outside(Q, BACK, A_BRICK)) > 0.006)

# the sign on the wall is blue, and under this lamp blue is black; its lettering comes back orange
SX0, SX1, SY0, SY1 = GX1 + 0.75, GX1 + 1.45, 1.55, 2.0
flat = Brush(width=5, opacity=0.97, pickup=0.1, dryness=0.05, thickness=0.25, jitter=0.02, gap=0.0, taper=(0.04, 0.04))
sq = quad(view, [(SX0, SY0, G), (SX1, SY0, G), (SX1, SY1, G), (SX0, SY1, G)])
board.tape(sq, feather=0.5)
board.fill(sq, flat, scale(night, 0.14), angle=0.0)
board.untape()
letter = outside(v3((SX0 + SX1) / 2, 1.8, G), BACK, white) * 0.8
for yy, x_end in ((1.87, SX1 - 0.1), (1.74, SX1 - 0.22), (1.66, SX1 - 0.3)):
    line3(board, view, v3(SX0 + 0.08, yy, G), v3(x_end, yy, G), body(flat.but(width=2.2, dryness=0.3)), letter)
board.dry()
board.stage("the brick, where the lamp gets under the canopy")

# =============================================================================================
# 5. The reception, through the glass: laid flat and level, with no tooth in it, because it is
#    behind a pane. Everything in here has its own colour.
# =============================================================================================
pane = Brush(width=12, opacity=0.97, pickup=0.2, dryness=0.0, thickness=0.2, jitter=0.006, gap=0.0, loadvar=0.0, wander=0.2,
             level=0.9, taper=(0.03, 0.03))
def lino(q):
    """Polished lino gives the back wall back, more the further off it is."""
    t = (q[2] - G) / (ZB - G)
    return np.minimum(inside(q, UP, A_LINO) + 0.10 * t ** 2 * inside(v3(q[0], 1.0, ZB), BACK, A_WALL), 0.62)


def surface(corners, e0, e1, n, shade, along):
    board.tape(GLAZ_Q, feather=0.6)
    board.tape(quad(view, corners), feather=0.5, mode="and")
    sweep(board, view, e0, e1, n, pane, shade, along=along, overlap=2.3, jitter=0.2)
    board.untape()


x_a, x_b = XD - XW, XD + XW
surface([(x_a, YCL, G), (x_b, YCL, G), (x_b, YCL, ZB), (x_a, YCL, ZB)],
        lambda t: v3(x_a - 1, YCL, G + t * (ZB - G)), lambda t: v3(x_b + 1, YCL, G + t * (ZB - G)), 12,
        lambda q: inside(q, DOWN, A_CEIL), 5)
surface([(x_a, YP, ZB), (x_b, YP, ZB), (x_b, YCL, ZB), (x_a, YCL, ZB)],
        lambda t: v3(x_a - 1, YCL - t * (YCL - YP), ZB), lambda t: v3(x_b + 1, YCL - t * (YCL - YP), ZB), 22,
        lambda q: inside(q, BACK, A_WALL), 20)
surface([(x_a, YP, G), (x_b, YP, G), (x_b, YP, ZB), (x_a, YP, ZB)],
        lambda t: v3(x_a - 1, YP, ZB - t * (ZB - G)), lambda t: v3(x_b + 1, YP, ZB - t * (ZB - G)), 16, lino, 20)
for sx, n_ in ((x_a, v3(1, 0, 0)), (x_b, v3(-1, 0, 0))):
    surface([(sx, YP, G), (sx, YP, ZB), (sx, YCL, ZB), (sx, YCL, G)],
            lambda t: v3(sx, YCL - t * (YCL - YP), G - 1), lambda t: v3(sx, YCL - t * (YCL - YP), ZB + 0.5), 12,
            lambda q: inside(v3(q[0], q[1], np.clip(q[2], G, ZB)), n_, A_WALL), 12)
board.dry()
board.stage("the reception, behind the glass")

ZW = ZB - 0.02
small = Brush(width=4, opacity=0.97, pickup=0.1, dryness=0.0, thickness=0.15, jitter=0.02, gap=0.0, level=0.8,
              taper=(0.03, 0.03))


def panel(x0, x1, y0, y1, col, z=ZW, angle=0.0, w=4.0, feather=0.5):
    q = quad(view, [(x0, y0, z), (x1, y0, z), (x1, y1, z), (x0, y1, z)])
    board.tape(GLAZ_Q)
    board.tape(q, feather=feather, mode="and")
    board.fill(q, small.but(width=w), col, angle=angle)
    board.untape()


def at_wall(x, y, alb, k=1.0):
    return inside(v3(x, y, ZW), BACK, alb, k)


# the doors through to the department: beech, vision panels, steel kick plates
DX0, DX1, DY1 = XD - 3.5, XD - 1.9, YP + 2.05
panel(DX0 - 0.06, DX1 + 0.06, YP, DY1 + 0.06, at_wall(DX0, 1.2, A_BEECH, 0.55))
for a, b in ((DX0, (DX0 + DX1) / 2 - 0.01), ((DX0 + DX1) / 2 + 0.01, DX1)):
    for y0, y1 in ((YP + 0.28, YP + 1.0), (YP + 1.0, YP + 1.6), (YP + 1.6, DY1)):
        panel(a, b, y0, y1, at_wall((a + b) / 2, (y0 + y1) / 2, A_BEECH), angle=np.pi / 2, w=3.5)
    panel(a, b, YP, YP + 0.27, at_wall((a + b) / 2, YP + 0.15, A_STEEL, 0.8))
    m = (a + b) / 2 + (0.22 if a == DX0 else -0.22)
    panel(m - 0.08, m + 0.08, YP + 1.15, YP + 1.8, at_wall(m, 1.5, mix((viridian, 1), (white, 1), (black, 1.5)), 0.5), w=2.5)
# the clock over them
ck = P(v3(XD - 0.55, YP + 2.3, ZW))
rr = 0.14 * view.ppm(ZW)
board.tape(GLAZ_Q)
for r_, c_ in ((rr, scale(night, 0.5)), (rr * 0.8, at_wall(DX0, 2.3, white))):
    ring_ = [(ck[0] + r_ * 0.5 * np.cos(a), ck[1] + r_ * 0.5 * np.sin(a)) for a in np.linspace(0, 2 * np.pi, 14)]
    board.stroke(ring_, small.but(width=r_ * 1.05, taper=(0, 0)), c_, smooth=False)
for ang, ln in ((np.radians(4.58 * 30), 0.5), (np.radians(210), 0.72)):      # 04:35
    board.stroke([ck, ck + rr * ln * np.array([np.sin(ang), -np.cos(ang)])], small.but(width=1.6, level=0.0), scale(night, 0.3))
board.untape()
# the notice board, and the seats under it
NX0, NX1 = XD - 1.45, XD + 0.35
panel(NX0, NX1, YP + 1.15, YP + 1.95, at_wall(XD - 0.5, 1.6, A_CORK))
for i in range(9):
    nx, ny = rng.uniform(NX0 + 0.1, NX1 - 0.25), rng.uniform(YP + 1.22, YP + 1.7)
    panel(nx, nx + rng.uniform(0.12, 0.2), ny, ny + rng.uniform(0.12, 0.2),
          at_wall(nx, ny, mix((white, 5), (rng.choice([lemon, cadred, viridian, white]), 0.5))), w=2.0, feather=0.3)
for i in range(4):
    cx = NX0 + 0.22 + i * 0.45
    panel(cx - 0.21, cx + 0.21, YP, YP + 0.05, inside(v3(cx, YP, ZW - 0.2), UP, A_LINO, 0.35), z=ZW - 0.3, w=2.0)  # its shadow
    panel(cx - 0.19, cx + 0.19, YP + 0.48, YP + 0.9, at_wall(cx, 0.7, A_SEAT), z=ZW - 0.08, w=3.0)                    # back
    sq_ = quad(view, [(cx - 0.2, YP + 0.43, ZW - 0.5), (cx + 0.2, YP + 0.43, ZW - 0.5), (cx + 0.2, YP + 0.45, ZW - 0.08),
                      (cx - 0.2, YP + 0.45, ZW - 0.08)])
    board.tape(GLAZ_Q)
    board.tape(sq_, feather=0.4, mode="and")
    board.fill(sq_, small.but(width=2.5), inside(v3(cx, YP + 0.44, ZW - 0.3), UP, A_SEAT), angle=0.0)
    board.untape()
board.tape(GLAZ_Q)
for lx in (NX0 + 0.04, NX0 + 0.92, NX0 + 1.76):
    line3(board, view, v3(lx, YP, ZW - 0.3), v3(lx, YP + 0.43, ZW - 0.3), small.but(width=1.6, level=0.0), scale(night, 0.6))
line3(board, view, v3(NX0 + 0.02, YP + 0.41, ZW - 0.3), v3(NX0 + 1.78, YP + 0.41, ZW - 0.3), small.but(width=1.8, level=0.0), scale(night, 0.6))
board.untape()
# the extinguisher by the doors, which is red in here
panel(DX1 + 0.22, DX1 + 0.36, YP + 0.55, YP + 1.1, at_wall(DX1 + 0.3, 0.8, cadred), w=2.5)
# the hatch: nobody at it, the office behind it dark, the counter and the front of the desk
HX0, HX1 = XD + 0.9, XD + 3.7
panel(HX0, HX1, YP, YP + 1.02, at_wall(XD + 2.2, 0.6, A_BEECH, 0.8), angle=np.pi / 2)
panel(HX0, HX1, YP + 1.1, YP + 2.0, scale(mix((viridian, 1), (ultra, 1), (black, 3)), 0.5))
panel(HX0 + 1.1, HX0 + 1.55, YP + 1.1, YP + 1.52, scale(mix((ultra, 1), (white, 1), (black, 2)), 0.4), w=3)       # a chair back
panel(HX0 + 0.25, HX0 + 0.7, YP + 1.1, YP + 1.45, scale(mix((white, 2), (black, 2)), 0.35), w=3)                  # the back of a screen
panel(HX0 - 0.05, HX1 + 0.05, YP + 1.02, YP + 1.1, inside(v3(XD + 2.2, YP + 1.05, ZW - 0.2), UP, A_WALL), z=ZW - 0.25, w=2.5)
board.dry()

# the wheelchair, brought in and left facing the doors. Its seat and back are blue.
CX, CZ, YAW = XD - 1.95, 9.15, np.radians(28)
cf, cs_ = v3(np.sin(YAW), 0, -np.cos(YAW)), v3(np.cos(YAW), 0, np.sin(YAW))    # the way it faces, and across it


def chair(x, y, z):
    return v3(CX, YP, CZ) + cf * x + v3(0, y, 0) + cs_ * z


R0 = 0.30
tubes = []
for zs in (-0.27, 0.27):
    tubes.append([chair(0.24, 0.50, zs), chair(-0.20, 0.50, zs)])
    tubes.append([chair(-0.20, 0.50, zs), chair(-0.24, 0.95, zs), chair(-0.36, 0.97, zs)])
    tubes.append([chair(0.20, 0.72, zs), chair(-0.18, 0.72, zs)])
    tubes.append([chair(0.24, 0.50, zs), chair(0.26, 0.16, zs)])
    tubes.append([chair(0.24, 0.42, zs), chair(0.40, 0.10, zs * 0.6)])
    tubes.append([chair(0.20, 0.72, zs), chair(0.22, 0.50, zs)])


def ring(cx, cy, z, r, n=40):
    return [chair(cx + r * np.cos(a), cy + r * np.sin(a), z) for a in np.linspace(0, 2 * np.pi, n)]


kc_ = view.ppm(CZ)
board.tape(GLAZ_Q)
# its shadow on the lino first: the tubes are nearly overhead, so it sits under it
under = quad(view, [chair(-0.45, 0, -0.36), chair(0.45, 0, -0.36), chair(0.45, 0, 0.36), chair(-0.45, 0, 0.36)])
board.tape(under, feather=5.0, mode="and")
board.fill(under, small.but(width=7, glaze=True, opacity=0.5), mix((white, 1), (ultra, 1), (black, 1)), angle=0.0)
board.untape()
board.tape(GLAZ_Q)
ink = Brush(width=4, bristle=1.2, opacity=1.0, pickup=0.05, dryness=0.0, thickness=0.1, jitter=0.02, gap=0.0,
            taper=(0.03, 0.03), level=0.6)
tyre = inside(chair(0, 0.3, 0), cf, mix((black, 3), (white, 1)), 0.5)
steel = inside(chair(0, 0.7, 0), cf, A_STEEL, 0.55)
steel_top = inside(chair(0, 0.72, 0), UP, A_STEEL)
blue_back = inside(chair(-0.2, 0.75, 0), cf, A_BLUE, 1.6)
blue_seat = inside(chair(0, 0.5, 0), UP, A_BLUE, 1.0)
for zs in (-0.31, 0.31):
    board.stroke(P(np.array(ring(-0.10, R0, zs, R0, 60))), ink.but(width=max(2.0, 0.04 * kc_)), tyre, smooth=False)
    board.stroke(P(np.array(ring(-0.10, R0, zs * 1.08, 0.25, 50))), ink.but(width=1.3), steel, smooth=False)
    board.stroke(P(np.array(ring(0.27, 0.08, zs * 0.85, 0.07, 24))), ink.but(width=2.4), tyre, smooth=False)
back_q = quad(view, [chair(-0.21, 0.55, -0.25), chair(-0.23, 0.93, -0.25), chair(-0.23, 0.93, 0.25), chair(-0.21, 0.55, 0.25)])
board.tape(back_q, feather=0.5, mode="and")
board.fill(back_q, ink.but(width=4), blue_back, angle=0.0)
board.tape(GLAZ_Q)
seat_q = quad(view, [chair(-0.20, 0.50, -0.25), chair(0.22, 0.50, -0.25), chair(0.22, 0.50, 0.25), chair(-0.20, 0.50, 0.25)])
board.tape(seat_q, feather=0.5, mode="and")
board.fill(seat_q, ink.but(width=3), blue_seat, angle=0.0)
board.tape(GLAZ_Q)
for t in tubes:
    board.stroke(P(np.array(t)), ink.but(width=max(1.6, 0.025 * kc_)), steel, smooth=False)
for t in (tubes[2], tubes[8]):
    board.stroke(P(np.array(t)) - [0, 1.0], ink.but(width=1.4), steel_top, smooth=False)
board.untape()
board.dry()
board.stage("what is in it, and the chair I brought in")

# =============================================================================================
# 6. The frames, which are outside: aluminium, lit by the lamp up to where the canopy stops it.
# =============================================================================================
frame = Brush(width=7, opacity=1.0, pickup=0.0, dryness=0.0, thickness=0.3, jitter=0.015, gap=0.0, loadvar=0.04, wander=0.15,
              hard=True, taper=(0.01, 0.01))
ppm_g = view.ppm(G)


def member(a, b, wm, alb=A_ALU, k=1.0):
    a, b = v3(*a), v3(*b)
    cs = [outside(a + (b - a) * t, BACK, alb) * k for t in np.linspace(0, 1, 14)]
    board.stroke(P(np.array([a, b])), frame.but(width=max(2.0, wm * ppm_g)), cs, smooth=False)


member((GX0, GY1 - 0.04, G), (GX1, GY1 - 0.04, G), 0.09)                         # head
member((GX0, YT, G), (XD - 1.0, YT, G), 0.07)                                    # transoms over the side-lights
member((XD + 1.0, YT, G), (GX1, YT, G), 0.07)
member((XD - 1.0, YT + 0.04, G), (XD + 1.0, YT + 0.04, G), 0.22)                 # the box the door gear lives in
member((GX0, YP + 0.05, G), (GX1, YP + 0.05, G), 0.11)                           # bottom rails and threshold
for x, wm, top in ((GX0 + 0.04, 0.09, GY1), (GX1 - 0.04, 0.09, GY1), (XD - 1.0, 0.11, GY1), (XD + 1.0, 0.11, GY1),
                   (XD, 0.10, YT)):
    member((x, YP, G), (x, top, G), wm)
# the dots across the glass at chest height, so nobody walks into it: frosted, and the one place
# on the pane where the lamp and the tubes are in the same paint
dot = Brush(width=3.6, bristle=1.0, opacity=0.75, pickup=0.0, dryness=0.0, thickness=0.05, jitter=0.02, gap=0.0, taper=(0.2, 0.2))
board.tape(GLAZ_Q)
for x in np.arange(GX0 + 0.18, GX1 - 0.1, 0.125):
    if min(abs(x - XD), abs(abs(x - XD) - 1.0)) < 0.1:
        continue
    for yy in (YP + 1.5, YP + 0.85):
        Q = v3(x, yy, G)
        c = room((0.5 * sod(Q, BACK, me=False) * SOD + 0.045 * fit.onto(v3(x, yy, G + 2), BACK) + 0.1 * AMB_IN) * EXPO)
        p = P(Q)
        board.stroke([p - [1.6, 0], p + [1.6, 0]], dot, c)
board.untape()
board.dry()
board.stage("the frames, and the dots on the glass")

# =============================================================================================
# 7. The wet, here at my feet: it gives back the doors and the top of the lit brick, pulled at me,
#    and starts where the canopy stopped the rain.
# =============================================================================================
bx_, by_ = np.meshgrid(np.concatenate([np.linspace(GX0 - 5.5, GX0 - 0.2, 6), np.linspace(GX1 + 0.2, GX1 + 5.5, 6)]),
                       np.linspace(0.4, 2.6, 5))
bS = np.stack([bx_.ravel(), by_.ravel(), np.full(bx_.size, G)], -1)
bR = np.array([one_line(A_BRICK) * sod(s, BACK, me=False) * SOD / np.pi for s in bS])
srcS = np.vstack([cold_out.S, bS])
srcN = np.vstack([cold_out.n, np.tile(BACK, (len(bS), 1))])
srcR = np.vstack([cold_out.rad, bR])
srcA = np.concatenate([cold_out.dA, np.full(len(bS), (10.6 / 12) * (2.2 / 5))])
n_in = len(cold_out.S)
GG, MX, MZ = 0.55, 0.014, 0.60
y_drip = P(v3(0, 0, ZC + 0.45))[1]


def wet_raw(sx, sy):
    """(the road as it is, what it gives back) at a spot on the board."""
    F = floor_at(view, np.float64(sx), np.float64(sy))
    w = float(wet(F[0], F[2]))
    base = ground_raw(F[0], F[2])[0]
    if w <= 0.01:
        return np.concatenate([base, np.zeros(3)])
    ok = np.concatenate([crosses(GLAZ, srcS[:n_in], F), np.ones(len(bS))])
    g = sheen(F, view.eye, srcS, srcN, srcR, srcA, (MX, MZ), ok=ok)
    return np.concatenate([base, GG * w * g * (0.3 + 1.0 * ripple(F[0], F[2]))])


wetF = Field(-10, W + 10, 128, y_drip - 30, H + 8, 64, wet_raw)


def wet_at(sx, sy):
    v = wetF.at(sx, sy)
    return room((v[..., :3] + v[..., 3:]) * EXPO)


def back_at(sx, sy):
    return lum(room(wetF.at(sx, sy)[..., 3:] * EXPO))


board.tape(ground_poly, feather=1.0)
streak = Brush(width=4.5, opacity=0.9, pickup=0.25, dryness=0.46, thickness=0.4, jitter=0.03, gap=0.05, deplete=0.0004,
               taper=(0.2, 0.25))
ys_ = np.linspace(y_drip - 26, H + 6, 90)
n_col = 170
for i in range(n_col):
    # side by side down the board, each only where the wet gives something back, the paint leaving the
    # brush by how much: so the ripples break it and it gives out where the light does
    sx = (i + 0.5 + rng.uniform(-0.4, 0.4)) / n_col * (W + 20) - 10
    bk = back_at(np.full_like(ys_, sx), ys_)
    on = np.where(bk > 0.01 * rng.uniform(0.8, 1.3))[0]
    if len(on) < 3:
        continue
    j0, j1 = max(on[0] - 1, 0), on[-1]
    cs = wet_at(np.full(j1 - j0 + 1, sx), ys_[j0:j1 + 1])
    board.stroke([(sx, ys_[j0]), (sx + rng.normal(0, 0.8), ys_[j1])], streak.but(width=rng.uniform(3.0, 6.0), dryness=rng.uniform(0.4, 0.55)), list(cs),
                 opacity=list(np.clip(bk[j0:j1 + 1] / 0.07, 0, 1)))
crest = body(Brush(width=2.4, bristle=1.0, opacity=0.8, pickup=0.3, dryness=0.45, thickness=0.3, jitter=0.02, gap=0.0,
                   taper=(0.3, 0.3)))
for i in range(700):
    sx, sy = rng.uniform(0, W), rng.uniform(y_drip - 20, H)
    if back_at(sx, sy) < 0.07:
        continue
    L = rng.uniform(6, 16)
    board.stroke([(sx - L / 2, sy), (sx + L / 2, sy + rng.normal(0, 0.6))], crest, np.minimum(wet_at(sx, sy) * 1.15, 0.62))
board.untape()
board.dry()
board.stage("the wet at my feet")

# =============================================================================================
# 8. The lamp, at second hand: once, small, in the glass over the doors. Doubled, because the
#    pane is two panes.
# =============================================================================================
lp = P(v3(XL, LY, 2 * G - LZ))
lw = 0.7 * view.f / (2 * G - LZ)
lampc = np.minimum(1.0 - np.exp(-3.0 * SOD * 1.25), 0.95)
refl = Brush(width=3.6, bristle=1.0, opacity=0.96, pickup=0.0, dryness=0.0, thickness=0.1, jitter=0.01, gap=0.0, deplete=0.0,
             taper=(0.1, 0.1), level=0.8)
board.tape(GLAZ_Q)
board.stroke([lp + [-lw / 2 + 2.5, 2.2], lp + [lw / 2 + 2.5, 2.2]], refl.but(opacity=0.5, width=3.0), lampc * 0.55)
board.stroke([lp - [lw / 2, 0], lp + [lw / 2, 0]], refl, lampc)
board.untape()
board.stage("the lamp, in the glass")

# =============================================================================================
# 9. White last: the tubes.
# =============================================================================================
hot = Brush(width=6, opacity=0.98, pickup=0.03, thickness=1.6, jitter=0.01, gap=0.0, deplete=0.0, taper=(0.04, 0.04))
tube = np.minimum(mix((white, 14), (viridian, 0.25), (lemon, 0.25)) * 1.08, 0.985)
board.tape(GLAZ_Q)
for q_ in ([(GX0, YT + 0.035, G), (XD - 1.06, YT + 0.035, G), (XD - 1.06, GY1 - 0.085, G), (GX0, GY1 - 0.085, G)],
           [(XD - 0.94, YT + 0.15, G), (XD + 0.94, YT + 0.15, G), (XD + 0.94, GY1 - 0.085, G), (XD - 0.94, GY1 - 0.085, G)],
           [(XD + 1.06, YT + 0.035, G), (GX1, YT + 0.035, G), (GX1, GY1 - 0.085, G), (XD + 1.06, GY1 - 0.085, G)]):
    board.tape(quad(view, q_), mode="replace")
    for fx in FIT_X:
        for fz in FIT_Z:
            a, b = P(v3(fx - 0.6, YCL, fz)), P(v3(fx + 0.6, YCL, fz))
            hgt = P(v3(fx, YCL, fz + 0.3))[1] - P(v3(fx, YCL, fz - 0.3))[1]
            board.stroke([a, b], body(hot.but(width=max(2.6, hgt + 0.8)), ref=5.0), tube, smooth=False)
board.untape()
board.dry()
board.stage("white last: the tubes")

finish(board, HERE, title="A&E doors, from the ambulance bay, 04:35", artist="nell-abara", year=2010,
       medium="Oil on hardboard, rough side", made="2026-11-14")
