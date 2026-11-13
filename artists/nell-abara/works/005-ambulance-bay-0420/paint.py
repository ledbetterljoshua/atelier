"""Nell Abara - Ambulance bay, A&E entrance, 04:20

Standing in the doors, under the canopy, looking out. It has stopped raining. The bay is lit by
one low-pressure sodium lamp on a column at the far side, and under it there is no colour at all,
only how much of that one orange a thing sends back. The road beyond the canopy is wet and pulls
the lamp at me. Somebody has left a wheelchair out in the bay.
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
from tools import (Patches, Plane, View, cast, drag, floor_at, gloss, line3, mirrored, one_line, quad, room,  # noqa: E402
                   scrub, v3)

W, H = 1000, 990
rng0 = np.random.default_rng(420)
board = Board(W, H, hexc("#0b0a0a"), ground.hardboard_mesh(W, H, rng0, pitch=5.4), seed=2010, light=(0.05, -0.95))
board.dries_off_board = False
board.relief_soft = 2.2
rng = board.rng
EYE = (0.0, 1.6, 0.0)
view = View(W, H, 1150, 470, 380, EYE)
P = view.P

# --- tubes -----------------------------------------------------------------------------------
black, ultra, umber = hexc("#0b0a0a"), hexc("#1b2a7a"), hexc("#4a2a16")
viridian, ochre, cadred = hexc("#0f6b55"), hexc("#c0902f"), hexc("#c6281c")
lemon, white = hexc("#efe36a"), hexc("#f6f3ea")
night = mix((ultra, 2), (umber, 1), (black, 2))

# the lamp's one colour, mixed: cadmium red into lemon, a little ochre to stop it going acid
SOD = mix((cadred, 1.0), (lemon, 1.6), (ochre, 0.5))
SOD = SOD / SOD.max()

# --- what the surfaces are -------------------------------------------------------------------
A_TARMAC = mix((white, 0.5), (umber, 0.7), (ultra, 0.4), (black, 1.0))
A_YELLOW = mix((lemon, 3), (ochre, 1), (white, 1))           # the hatching; under this lamp, white
A_HEDGE = mix((viridian, 1), (umber, 1), (black, 1))
A_STEEL = mix((white, 2), (ultra, 0.2), (umber, 0.3))         # the chair's frame, chromed and dull

UP, BACK = v3(0, 1, 0), v3(0, 0, -1)

# --- the place --------------------------------------------------------------------------------
ZC, YC = 4.4, 3.3                 # the canopy over the doors: its edge, and its soffit
ZK, YK = 2.6, 0.12                # the kerb, and the pavement I stand on
LX, LY, LZ = 3.2, 5.5, 22.0       # the lantern's bowl
PX = 3.85                         # its column
ZH = 40.0                         # the hedge at the back of the car park

# a wheelchair left out in the bay, side on, facing left
CX, CZ, YAW = 1.28, 9.0, np.radians(4)
cu, cw = v3(np.cos(YAW), 0, np.sin(YAW)), v3(-np.sin(YAW), 0, np.cos(YAW))   # along it, across it


def chair(x, y, z):
    """A point on the chair from chair coordinates: x forward (left on the board), z across."""
    return v3(CX, 0, CZ) + cu * (-x) + v3(0, y, 0) + cw * z


# --- the lamp -----------------------------------------------------------------------------------
lens = Plane((LX - 0.35, LY, LZ - 0.12), (0.7, 0, 0), (0, 0, 0.24))
RL = 60.0
def throw(S, Q):
    """A cut-off lantern: it puts its light down, and gives little of it sideways."""
    d = S - Q
    return np.clip(d[:, 1] / np.linalg.norm(d, axis=1), 0, 1) ** 1.0


lamp = Patches.on(lens, v3(1, 1, 1) * RL, 6, 2, facing=v3(0, -1, 0), rng=np.random.default_rng(5), occlude=throw)
LC = v3(LX, LY, LZ)


def amb(N):
    """The department behind me, through two sets of doors, and the sky: next to nothing, and cold."""
    return v3(0.00010, 0.00013, 0.00022) * (1.0 + 0.4 * max(0.0, N[2] * -1))


def irr(Q, N):
    return lamp.onto(Q, N)[0]


def light(Q, N, albedo):
    return one_line(albedo) * irr(Q, N) * SOD + amb(N) * albedo


# keyed once, on the wet road a couple of metres this side of the lamp's foot
_probe = v3(LX - 0.6, 0.0, LZ - 2.5)
_c = light(_probe, UP, A_TARMAC)
lo, hi = 1e-3, 1e6
for _ in range(80):
    mid = np.sqrt(lo * hi)
    v = room(_c * mid)
    if 0.2 * v[0] + 0.7 * v[1] + 0.1 * v[2] < 0.07:
        lo = mid
    else:
        hi = mid
EXPO = np.sqrt(lo * hi)


def shade_at(Q, N, albedo, vary=0.0):
    c = room(light(Q, N, albedo) * EXPO)
    return c * (np.exp(rng.normal(0, vary)) if vary else 1.0)


def lum(c):
    return 0.2 * c[0] + 0.7 * c[1] + 0.1 * c[2]


GG = 0.28
MX, MZ = 0.02, 0.25

# --- the wet ------------------------------------------------------------------------------------
PUDDLES = [(-1.4, 7.5, 1.1, 0.5), (3.1, 14.0, 1.6, 0.9), (1.4, 10.5, 0.7, 0.45)]


def puddle(x, z):
    k = 0.0
    for px, pz, rx, rz in PUDDLES:
        d = ((x - px) / rx) ** 2 + ((z - pz) / rz) ** 2 + 0.25 * np.sin(3 * x + 2 * z)
        k = max(k, np.clip((1.0 - d) * 4, 0, 1))
    return k


def ripple(x, z):
    """Wet tarmac is not flat: ruts, a camber, the aggregate. Bands across the line of sight."""
    k = (np.sin(7.1 * z + 1.3 * np.sin(9.3 * x)) + 0.7 * np.sin(13.7 * z + 0.4 + 2.0 * np.sin(17.0 * x))
         + 0.5 * np.sin(3.1 * z + 23.0 * x)) / 2.2
    return 0.5 + 0.5 * k


def wet(x, z):
    """Dry under the canopy, wet past its drip line (blown in a little, unevenly), water in the dips."""
    edge = ZC - 0.2 - 0.25 * (0.5 + 0.5 * np.sin(1.7 * x + 0.4)) * (0.5 + 0.5 * np.sin(4.3 * x))
    if z < edge:
        return 0.0
    return min(1.0, np.clip((z - edge) / 1.1, 0, 1) ** 1.5 * 0.8 + puddle(x, z))


def road_col(x, z, albedo=A_TARMAC):
    """The road at (x, z) as paint: what lands on it, and the lamp it gives back if it is wet."""
    F = v3(x, 0.0, z)
    base = light(F, UP, albedo)
    w = wet(x, z)
    if w > 0:
        base = base * (1.0 - 0.45 * w)          # wet tarmac goes darker
        dry = 1.0 - puddle(x, z)
        m = (0.006 + MX * dry, 0.006 + MZ * dry)
        g = GG * w * gloss(F, view.eye, lamp.S, RL, lamp.dA[0], lamp.n, m) * (0.35 + 0.9 * ripple(x, z) * dry + (1 - dry))
        base = base + g * SOD
    return room(base * EXPO)


def road_at(sx, sy):
    F = floor_at(view, np.float64(sx), np.float64(sy))
    if F[2] < 0.5:
        return scale(night, 0.05)
    return road_col(F[0], F[2])


if os.environ.get("CHECK"):
    print("EXPO", EXPO)
    for nm, p in [("lamp", LC), ("lamp foot", v3(LX, 0, LZ)), ("canopy edge", v3(0, YC, ZC)), ("kerb", v3(0, YK, ZK)),
                  ("hedge top", v3(0, 1.8, ZH)), ("chair base", chair(0, 0, 0)), ("chair top", chair(0, 1.0, 0)),
                  ("bottom z", v3(0, 0, 2.0))]:
        print(f"{nm:12s}", np.round(P(p), 1))
    for z in (4.6, 5.3, 6, 8, 10, 14, 18, 21, 22, 24, 30):
        x = LX * z / LZ
        print("road", z, np.round(road_col(x, z), 3), np.round(road_col(x - 1.5, z), 3), np.round(road_col(x + 2, z), 3))
    print("hedge", np.round(shade_at(v3(1.5, 1.0, ZH), BACK, A_HEDGE), 3))
    sys.exit()

# --- the board's geography ------------------------------------------------------------------------
y_canopy = P(v3(0, YC, ZC))[1]
y_hedge_top = P(v3(0, 1.9, ZH))[1]
y_horizon = view.vy
y_kerb = P(v3(0, YK, ZK))[1]
road_poly = np.array([(-80, P(v3(0, 0, 200))[1]), (W + 80, P(v3(0, 0, 200))[1]), (W + 80, y_kerb), (-80, y_kerb)])
sky_poly = np.array([(-80, y_canopy), (W + 80, y_canopy), (W + 80, y_hedge_top + 4), (-80, y_hedge_top + 4)])

# --- the chair, as tubes and slings, for painting and for what it does to the light -----------
R0 = 0.30
tubes = []
for zs in (-0.27, 0.27):
    tubes.append([chair(0.24, 0.50, zs), chair(-0.20, 0.50, zs)])                 # seat rail
    tubes.append([chair(-0.20, 0.50, zs), chair(-0.24, 0.95, zs), chair(-0.36, 0.97, zs)])   # back post, handle
    tubes.append([chair(0.20, 0.72, zs), chair(-0.18, 0.72, zs)])                 # armrest
    tubes.append([chair(0.24, 0.50, zs), chair(0.26, 0.16, zs)])                  # front post to caster
    tubes.append([chair(0.24, 0.42, zs), chair(0.40, 0.10, zs * 0.6)])            # footrest hanger
cross = [[chair(-0.05, 0.36, -0.27), chair(0.10, 0.50, 0.27)], [chair(-0.05, 0.36, 0.27), chair(0.10, 0.50, -0.27)]]


def ring(cx, cy, z, r, n=40):
    return [chair(cx + r * np.cos(a), cy + r * np.sin(a), z) for a in np.linspace(0, 2 * np.pi, n)]


pts = []
for t in tubes + cross:
    for a, b in zip(t[:-1], t[1:]):
        pts += [a + (b - a) * s for s in np.linspace(0, 1, 30)]
for zs in (-0.30, 0.30):
    pts += ring(-0.10, R0, zs, R0, 120)
    pts += ring(0.27, 0.08, zs * 0.85, 0.08, 40)
for s in np.linspace(0, 1, 12):
    for u in np.linspace(0, 1, 12):
        pts.append(chair(-0.20 + 0.44 * s, 0.50, -0.25 + 0.5 * u))
        pts.append(chair(-0.21 - 0.02 * u, 0.55 + 0.38 * s, -0.25 + 0.5 * u))
pts = np.array(pts)

# =============================================================================================
# 1. Imprimatura: thin darks over the black, cold where the doors are behind me, warm out there.
# =============================================================================================
wash = Brush(width=130, bristle=2.6, opacity=0.4, dryness=0.55, pickup=0.3, thickness=0.2, jitter=0.12, deplete=0.0008)
for i in range(60):
    x, y = rng.uniform(-100, W + 100), rng.uniform(-50, H + 50)
    a = rng.uniform(0, np.pi)
    L = rng.uniform(300, 800)
    warm = np.exp(-((x - 700) / 360) ** 2 - ((y - 640) / 260) ** 2)
    c = mix((ultra, rng.uniform(0.8, 1.8) * (1 - 0.7 * warm)), (umber, rng.uniform(0.4, 1.4) + 2.5 * warm), (black, 4))
    board.stroke([(x - np.cos(a) * L / 2, y - np.sin(a) * L / 2), (x + np.cos(a) * L / 2, y + np.sin(a) * L / 2)],
                 wash, c, wobble=10)
board.dry()
board.stage("coloured darks over black")

# =============================================================================================
# 2. The dark is the board: the soffit, the sky, the pavement, a few dry strokes and no more.
# =============================================================================================
dark = Brush(width=90, bristle=2.4, opacity=0.5, pickup=0.5, dryness=0.7, thickness=0.3, jitter=0.04, deplete=0.0005,
             taper=(0.12, 0.18))


def sky_shade(x, y):
    """Sodium in the cloud over the town: brown, brightest low down."""
    k = np.clip((y - y_canopy) / (y_hedge_top - y_canopy), 0, 1)
    return mix((umber, 1.0), (cadred, 0.25), (ochre, 0.3), (black, 3.0 - 1.5 * k)) * (0.15 + 0.45 * k)


scrub(board, sky_poly, dark.but(opacity=0.4, dryness=0.8, width=120), sky_shade, 8, length=(400, 900),
      angle=(-1.3, 1.3), along=7)
soffit = np.array([(-80, -80), (W + 80, -80), (W + 80, y_canopy), (-80, y_canopy)])
scrub(board, soffit, dark.but(opacity=0.4, dryness=0.75), lambda x, y: scale(night, 0.25), 5, length=(700, 1300),
      angle=(-0.08, 0.08), along=4)
pave = np.array([(-80, y_kerb), (W + 80, y_kerb), (W + 80, H + 80), (-80, H + 80)])
scrub(board, pave, dark.but(opacity=0.4, dryness=0.74), lambda x, y: scale(night, 0.35), 7, length=(600, 1200),
      angle=(-0.3, 0.3), along=4)
board.dry()
board.stage("the dark, left as the board")

# =============================================================================================
# 3. The road: rows across it, each mixed along its length, and only as far as the lamp reaches.
# =============================================================================================
SHADOW = cast(view, W, H, LC, pts, radius=2.5, blur=4.0)
MIRROR = mirrored(view, W, H, pts, radius=2.0, blur=(10.0, 3.0)) * 0.55
row = Brush(width=10, opacity=0.85, pickup=0.45, dryness=0.42, thickness=0.5, jitter=0.03, deplete=0.0005,
            taper=(0.25, 0.25))
board.tape(road_poly, feather=1.0)
board.tape_where(SHADOW, mode="cut")
board.tape_where(MIRROR, mode="cut")
y_far = P(v3(0, 0, 60))[1]
NR = 46
for i in range(NR):
    sy = y_far + (y_kerb - y_far) * ((i + 0.5 + rng.uniform(-0.3, 0.3)) / NR) ** 1.6
    z = floor_at(view, 0.0, sy)[2]
    xs = np.linspace(-16, 18, 60)
    cs = [road_col(x, z) for x in xs]
    ls = np.array([lum(c) for c in cs])
    on = np.where(ls > 0.006)[0]
    if len(on) < 2:
        continue
    i0, i1 = max(on[0] - 2, 0), min(on[-1] + 2, len(xs) - 1)
    a_, b_ = P(v3(xs[i0], 0, z)), P(v3(xs[i1], 0, z))
    gap = (y_kerb - y_far) / NR * 1.6 * ((i + 1) / NR) ** 0.6
    board.stroke(np.array([a_, b_]) + [0, rng.normal(0, 1.0)], row.but(width=float(np.clip(gap * 2.2, 3, 40))),
                 cs[i0:i1 + 1], wobble=0.0, opacity=list(np.clip(ls[i0:i1 + 1] / 0.035, 0, 1) ** 0.8))
board.untape()
board.dry()
board.stage("the road, where the lamp reaches it")

# =============================================================================================
# 4. The hedge at the back of the car park, and the lamp's column against it.
# =============================================================================================
hedge_q = np.array([P(v3(-30, 0, ZH)), P(v3(30, 0, ZH)), P(v3(30, 1.9, ZH)), P(v3(-30, 1.9, ZH))])
board.tape(hedge_q, feather=2.0)
hb = Brush(width=16, opacity=0.8, pickup=0.5, dryness=0.5, thickness=0.5, jitter=0.05, deplete=0.0006)
for i in range(160):
    x = rng.uniform(-14, 18)
    y = rng.uniform(0.2, 1.9)
    Q = v3(x, y, ZH)
    c = shade_at(Q, BACK, A_HEDGE, 0.15)
    p = P(Q)
    board.dab(p[0], p[1], hb.but(width=rng.uniform(8, 18)), c, angle=rng.uniform(-0.6, 0.6), length=rng.uniform(10, 26))
board.untape()

colb = Brush(width=5, opacity=0.95, pickup=0.2, dryness=0.1, thickness=0.6, jitter=0.02, gap=0.0)
line3(board, view, v3(PX, 0, LZ), v3(PX, LY + 0.25, LZ), colb.but(width=0.14 * view.ppm(LZ)), scale(night, 0.25))
line3(board, view, v3(PX, LY + 0.2, LZ), v3(LX + 0.3, LY + 0.12, LZ), colb.but(width=0.08 * view.ppm(LZ)), scale(night, 0.25))
board.dry()
board.stage("the hedge, and the lamp's column")

# =============================================================================================
# 4b. The hatched box in front of the doors, keep clear: yellow, and under this lamp no colour at all.
# =============================================================================================
BX0, BX1, BZ0, BZ1, LW_ = -3.0, 2.6, 5.0, 16.0, 0.1
board.tape(road_poly, feather=1.0)
board.tape_where(SHADOW, mode="cut")
mark = Brush(width=4, opacity=0.85, pickup=0.3, dryness=0.55, thickness=0.7, jitter=0.03, gap=0.04, taper=(0.05, 0.05))


def paint_line(a, b):
    qs = [a + (b - a) * t for t in np.linspace(0, 1, 16)]
    cs = [road_col(q[0], q[2], A_YELLOW) for q in qs]
    op = [float(np.clip(lum(c) / 0.12, 0, 1)) for c in cs]
    if max(op) < 0.08:
        return
    zm = (a[2] + b[2]) / 2
    board.stroke(P(np.array([a, b])), mark.but(width=max(1.5, LW_ * view.ppm(zm))), cs, opacity=op)


for a, b in ((v3(BX0, 0, BZ0), v3(BX1, 0, BZ0)), (v3(BX0, 0, BZ1), v3(BX1, 0, BZ1)),
             (v3(BX0, 0, BZ0), v3(BX0, 0, BZ1)), (v3(BX1, 0, BZ0), v3(BX1, 0, BZ1))):
    paint_line(a, b)
for c in np.arange(BX0 - BZ1 + 0.6, BX1 - BZ0, 1.6):
    # the line x - z = c, clipped to the box
    z0, z1 = max(BZ0, BX0 - c), min(BZ1, BX1 - c)
    if z1 - z0 > 0.2:
        paint_line(v3(c + z0, 0, z0), v3(c + z1, 0, z1))
# no waiting, along both edges of the road out to the lamp
for xe in (-4.3, -4.12, 6.6, 6.78):
    for z0 in np.arange(4.0, 44.0, 4.0):
        paint_line(v3(xe, 0, z0), v3(xe, 0, z0 + 4.0))
board.untape()
board.dry()
board.stage("keep clear, and no waiting")

# =============================================================================================
# 5. The wet: the lamp pulled down the road at me, a dry brush so the tarmac's grain stays in it.
#    Not where the chair stands between the lamp and the road, nor where the chair is in the wet.
# =============================================================================================
xL = P(LC)[0]
y_top = P(v3(LX, 0, LZ + 3))[1]
y_drip = P(v3(0, 0, ZC))[1]
board.tape(road_poly, feather=1.0)
board.tape_where(SHADOW, mode="cut")
board.tape_where(MIRROR, mode="cut")
streak = Brush(width=5, opacity=0.9, pickup=0.25, dryness=0.48, thickness=0.4, jitter=0.03, gap=0.05, deplete=0.0004,
               taper=(0.15, 0.15))
drag(board, xL - 60, xL + 60, y_top, y_drip + 14, 30, streak, road_at, along=30, floor=0.02, fade=0.08)
for i in range(9):
    ya = rng.uniform(y_top, y_drip - 60)
    yb = min(ya + rng.uniform(60, 220), y_drip + 14)
    drag(board, xL - 45, xL + 45, ya, yb, 12, streak.but(dryness=0.5, width=4), road_at, along=14, floor=0.03, fade=0.1)
# where the crests of the ripples catch it: short touches across, only where the light is
crest = Brush(width=3, bristle=1.0, opacity=0.8, pickup=0.3, dryness=0.45, thickness=0.2, jitter=0.02, gap=0.0, taper=(0.3, 0.3))
for i in range(260):
    sx, sy = xL + rng.normal(0, 22), rng.uniform(y_top, y_drip)
    F = floor_at(view, np.float64(sx), np.float64(sy))
    if ripple(F[0], F[2]) < 0.6 or board.mask[int(sy), int(np.clip(sx, 0, W - 1))] < 0.5:
        continue
    c = road_at(sx, sy)
    if lum(c) < 0.08:
        continue
    L = rng.uniform(8, 26)
    board.stroke([(sx - L / 2, sy), (sx + L / 2, sy + rng.normal(0, 0.6))], crest.but(width=rng.uniform(1.5, 3.0)),
                 np.minimum(c * 1.15, 0.62))
board.untape()
board.dry()
board.stage("the wet road, pulling the lamp at me")

# =============================================================================================
# 6. The chair, after the wet it stands in: dark tubes against the light, lit only along their tops.
# =============================================================================================
ink = Brush(width=4, bristle=1.5, opacity=1.0, pickup=0.1, dryness=0.0, thickness=0.6, jitter=0.02, gap=0.0, taper=(0.04, 0.04))
k = view.ppm(CZ)
cdark = scale(night, 0.12)
# the far wheel first, then the frame, then the near wheel over it
for zs in (0.30, -0.30):
    rr = ring(-0.10, R0, zs, R0, 60)
    board.stroke(P(np.array(rr)), ink.but(width=0.045 * k), cdark, smooth=False)
    board.stroke(P(np.array(ring(-0.10, R0, zs - 0.03 * np.sign(zs), 0.26, 50))), ink.but(width=0.012 * k), cdark, smooth=False)
    if zs > 0:
        for t in tubes + cross:
            board.stroke(P(np.array(t)), ink.but(width=0.025 * k), cdark, smooth=False)
        # the seat and back slings, blue vinyl, which this lamp leaves black
        seat = quad(view, [chair(-0.20, 0.50, -0.25), chair(0.22, 0.50, -0.25), chair(0.22, 0.50, 0.25), chair(-0.20, 0.50, 0.25)])
        board.tape(seat, feather=0.6)
        board.fill(seat, ink.but(width=6), scale(night, 0.15), angle=0.0)
        board.untape()
        back = quad(view, [chair(-0.21, 0.55, -0.25), chair(-0.23, 0.93, -0.25), chair(-0.23, 0.93, 0.25), chair(-0.21, 0.55, 0.25)])
        board.tape(back, feather=0.6)
        board.fill(back, ink.but(width=6), scale(night, 0.1), angle=1.4)
        board.untape()
    board.stroke(P(np.array(ring(0.27, 0.08, zs * 0.85, 0.08, 24))), ink.but(width=0.03 * k), cdark, smooth=False)
# where the lamp catches the tops of things, from behind
glint = Brush(width=2, bristle=0.8, opacity=0.9, pickup=0.0, thickness=0.8, jitter=0.02, gap=0.0, taper=(0.3, 0.3))
for a0, a1, zs in ((1.35, 1.75, -0.30),):
    arc = [chair(-0.10 + R0 * np.cos(a), R0 + R0 * np.sin(a), zs) for a in np.linspace(a0, a1, 10)]
    c = shade_at(arc[5], v3(0, 0.6, 0.8), mix((black, 2), (white, 1)))
    board.stroke(P(np.array(arc)) - [0, 0.02 * k], glint.but(width=0.012 * k), c)
for t in [tubes[2], tubes[7]] + [tubes[1][1:], tubes[6][1:]]:
    c = shade_at(t[0], v3(0, 0.7, 0.7), A_STEEL)
    board.stroke(P(np.array(t)) - [0, 0.012 * k], glint.but(width=0.012 * k), c, smooth=False)
board.dry()
board.stage("what was left in the bay")


# =============================================================================================
# 7. White last: the lamp. The brightest thing, and the only thing that is the lamp's own colour.
# =============================================================================================
hot = Brush(width=6, opacity=0.97, pickup=0.05, thickness=2.0, jitter=0.02, gap=0.0, deplete=0.0, taper=(0.05, 0.05))
lampc = np.minimum(1.0 - np.exp(-3.0 * SOD * 1.6), 0.97)
body_q = quad(view, [v3(LX - 0.42, LY + 0.02, LZ), v3(LX + 0.42, LY + 0.02, LZ), v3(LX + 0.38, LY + 0.2, LZ), v3(LX - 0.36, LY + 0.17, LZ)])
board.fill(body_q, Brush(width=4, opacity=0.95, pickup=0.1, thickness=0.6, gap=0.0), scale(night, 0.2), angle=0.0)
line3(board, view, v3(LX - 0.33, LY, LZ), v3(LX + 0.33, LY, LZ), hot.but(width=0.11 * view.ppm(LZ)), lampc, smooth=False)
board.dry()
board.stage("white last: the lamp")

finish(board, HERE, title="Ambulance bay, A&E entrance, 04:20", artist="nell-abara", year=2010,
       medium="Oil on hardboard, rough side", made="2026-11-12")
