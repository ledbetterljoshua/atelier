"""Carmela Zammit - Majjistral, last sun

The roof of the laundry in Marsa, looking west at the end of the afternoon. Two lines running away
from her to the right. The sun is low behind the third piece on the near line. The roof is already in
shade; only the washing still has the sun.
"""
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[3]))
sys.path.insert(0, str(HERE.parents[1]))

from engine import Board, Brush, hexc, mix, scale  # noqa: E402
from engine.studio import finish  # noqa: E402
from tools import Camera, Line, Sheet, lay_cloth, lay_screen, sheeting, tone, unit, v3  # noqa: E402

W, H = 1800, 1200
rng0 = np.random.default_rng(1983)
board = Board(W, H, hexc("#7a3021"), sheeting(W, H, rng0, darns=[(1480, 210, 46, 30)]), seed=1983)
rng = board.rng
cam = Camera(W, H, 1450, (0.0, 1.1, 0.0), pitch=0.15, cy=600)
E = cam.eye
P = cam.P

# --- tubes ---------------------------------------------------------------------------------------
oxide = hexc("#7a3021")
white, ultra, prussian = hexc("#f7f4ec"), hexc("#20307f"), hexc("#14284a")
naples, ochre, rawsi, burnsi = hexc("#ecd398"), hexc("#c49236"), hexc("#a8692a"), hexc("#7d3418")
cadyel, cadorange, black = hexc("#f2cc3a"), hexc("#e8782a"), hexc("#141210")
turq = hexc("#2a9a9a")

# --- the washing -----------------------------------------------------------------------------------
near = Line((-2.7, 2.3), (5.6, 9.6), 2.18, 0.10)
off = np.array([-near.n[0], -near.n[1]]) * 1.9
far = Line(near.a + off, near.b + off, 2.20, 0.12)

S1 = Sheet(near, 0.10, 2.10, 1.45, pegs=4, belly=0.50, lift=0.26, flare=0.16, side=-0.06, ripple=0.05, fold=0.06, band=0.09, seed=11)
PC1 = Sheet(near, 2.32, 0.52, 0.74, pegs=2, belly=0.15, lift=0.10, flare=0.05, ripple=0.012, sag=0.02, seed=12)
PC2 = Sheet(near, 2.95, 0.52, 0.72, pegs=2, belly=0.17, lift=0.12, flare=0.06, ripple=0.012, sag=0.02, seed=13)
S3 = Sheet(near, 3.62, 2.00, 1.38, pegs=4, belly=0.44, lift=0.22, flare=0.12, side=-0.04, ripple=0.045, fold=0.05, band=0.09, seed=14)
TW = Sheet(near, 5.80, 0.95, 1.30, pegs=3, belly=0.20, lift=0.10, flare=0.05, ripple=0.02, seed=15)
S5 = Sheet(near, 6.95, 1.90, 1.36, pegs=4, belly=0.36, lift=0.16, flare=0.05, ripple=0.045, fold=0.05, band=0.09, seed=16)
PC3 = Sheet(near, 9.00, 0.52, 0.72, pegs=2, belly=0.16, lift=0.10, flare=0.05, ripple=0.012, sag=0.02, seed=17)
NEAR = [S1, PC1, PC2, S3, TW, S5, PC3]

F1 = Sheet(far, 3.55, 0.95, 1.20, pegs=3, belly=0.22, lift=0.1, flare=0.05, ripple=0.02, seed=21)  # a bath towel
TC = Sheet(far, 6.65, 1.7, 1.20, pegs=4, belly=0.34, lift=0.16, flare=0.08, ripple=0.025, seed=22)  # tablecloth
F3 = Sheet(far, 9.3, 1.6, 1.30, pegs=4, belly=0.40, lift=0.2, flare=0.1, ripple=0.03, band=0.09, seed=23)
F4 = Sheet(far, 0.2, 1.9, 1.25, pegs=3, belly=0.36, lift=0.18, flare=0.1, ripple=0.03, seed=24)
FAR = [F1, TC, F3, F4]
ALL = FAR + NEAR

# --- the light ------------------------------------------------------------------------------------
# the sun is wherever it was behind the third piece; she always stands so that it is
L = unit(S3.pos(0.30, 0.34) - E)
SUN = v3(1.0, 0.80, 0.52) * 1.15
SKY = v3(0.24, 0.32, 0.52) * 0.40       # skylight from behind her, the east, already going blue
BOUNCE = v3(0.36, 0.27, 0.18) * 0.12      # off the roof in shade
COTTON = mix((white, 10), (naples, 1))
THROUGH = v3(1.0, 0.85, 0.62)             # what cotton does to the sun coming through it
TAU, TAU2 = 0.45, 0.36
ZP, PAR_H = 11.0, 0.95


def stripe(sheet, u):
    """The tablecloth's woven border: denser, lets less through."""
    if sheet is not TC:
        return 1.0
    return 0.6 if (0.04 < u < 0.11) or (0.89 < u < 0.96) else 1.0


def through(sheet, u, v, Q):
    """How much of the sun gets to the back of this cloth at Q."""
    k = 1.0
    if v < sheet.band or v > 0.965:
        k *= TAU2                        # folded over the wire, or the hem: two layers
    if sheet in NEAR:
        for o in FAR:
            h = o.hits(Q, L)
            if h is not None:
                k *= TAU * 0.75 * stripe(o, h[0])
                break
    t = (ZP - Q[2]) / L[2]
    if Q[1] + L[1] * t < PAR_H:
        k = 0.0
    return k


def cloth_light(sheet, u, v, parts=("sky", "sun")):
    Q = sheet.pos(u, v)
    n = sheet.normal(u, v, E)
    V = unit(E - Q)
    nl, nv = n @ L, abs(n @ V)
    out = np.zeros(3)
    if "sky" in parts:
        out += COTTON * (SKY * (0.5 + 0.5 * n[1]) + BOUNCE * (0.5 - 0.5 * n[1])) * (0.6 + 0.4 * nv)
    if "sun" in parts:
        k = through(sheet, u, v, Q) * stripe(sheet, u)
        if nl > 0:
            out += COTTON * SUN * nl * 0.9 * k
        else:
            cos_t = (-V) @ L
            glow = 6.0 * np.exp((cos_t - 1) / 0.0022) + 0.7 * np.exp((cos_t - 1) / 0.007)
            out += THROUGH * SUN * k * (TAU * (-nl) ** 0.7 * nv ** 0.6 + glow * (-nl) ** 0.3)
    return out


def sky_colour(x, y):
    d = cam.ray(x, y)
    el = np.arcsin(np.clip(d[1], -1, 1))
    t = np.clip(el / 0.46, 0, 1)
    high, mid, low = v3(0.022, 0.085, 0.29), v3(0.24, 0.40, 0.55), v3(0.80, 0.58, 0.30)
    a = np.clip(t / 0.35, 0, 1) ** 0.8
    b = np.clip((t - 0.35) / 0.65, 0, 1) ** 0.7
    c = np.exp(np.log(low) * (1 - a) + np.log(mid) * a)
    c = np.exp(np.log(c) * (1 - b) + np.log(high) * b)
    ang = np.arccos(np.clip(d @ L, -1, 1))
    c = c + v3(1.0, 0.66, 0.32) * (0.55 * np.exp(-ang / 0.09) + 0.16 * np.exp(-ang / 0.3))
    return np.clip(c, 0.004, 0.97) * np.exp(rng.normal(0, 0.035, 3))


# =================================================================================================
# 1. The sky, wet, from the top down, over the red.
# =================================================================================================
horizon_y = P(v3(0, E[1], 1e4))[1]
scrub = Brush(width=130, bristle=2.8, opacity=0.95, pickup=0.05, dryness=0.0, thickness=0.05, jitter=0.03, deplete=0.0003)
region = (-80, -60, W + 80, P(v3(0, PAR_H, ZP))[1] + 30)
lay_screen(board, region, scrub, lambda x, y: scale(sky_colour(x, y), 0.85), angle=-0.12, length=560, cover=3.0, wobble=10)
sky_b = Brush(width=60, bristle=2.0, opacity=0.6, pickup=0.35, dryness=0.0, thickness=0.05, jitter=0.025,
              deplete=0.0003, taper=(0.25, 0.3))
lay_screen(board, region, sky_b, sky_colour, angle=-0.12, length=520, cover=7.0, wobble=8)
board.dry()

# Qormi, two miles off: the dome and its belfries, the only thing that stands up past the parapet
haze = scale(mix((sky_colour(1700, 800), 3), (ultra, 0.8), (burnsi, 0.2)), 0.78)
dx, dz, gy = 560.0, 1000.0, -8.0
def town(x, y):
    return P(v3(dx + x, gy + y, dz))
drum = [town(-11, 22), town(11, 22), town(11, 34), town(-11, 34)]
dome = [town(11 * np.cos(t), 34 + 13 * np.sin(t) ** 0.8) for t in np.linspace(0, np.pi, 18)]
lantern = [town(-2.2, 45), town(2.2, 45), town(2.2, 51), town(0, 53.5), town(-2.2, 51)]
belfry = lambda c: [town(c - 4, 0), town(c + 4, 0), town(c + 4, 33), town(c + 2.5, 35), town(c, 38.5), town(c - 2.5, 35), town(c - 4, 33)]  # noqa: E731
body = [town(-26, 0), town(26, 0), town(26, 24), town(-26, 24)]
board.tape(body, drum, dome, lantern, belfry(-22), belfry(22), feather=0.7)
lay_screen(board, (P(v3(dx - 40, 0, dz))[0], P(v3(0, gy + 55, dz))[1], P(v3(dx + 40, 0, dz))[0], horizon_y + 60),
           Brush(width=7, bristle=1.0, opacity=0.9, pickup=0.2, thickness=0.3), lambda x, y: haze * np.exp(rng.normal(0, 0.03)),
           angle=np.pi / 2, angle_jitter=0.1, length=24, cover=5, wobble=0.3)
board.untape()
board.dry()
board.stage("the sky, wet, from the top down")

# =================================================================================================
# 2. The roof, already in shade.
# =================================================================================================
LIME = mix((naples, 2), (white, 2), (burnsi, 0.12))
yp_top, yp_bot = P(v3(0, PAR_H, ZP))[1], P(v3(0, 0, ZP))[1]


def roof_shade(x, y):
    Q = cam.on_ground(x, y)
    warm = np.exp(-((Q[2] - 7.5) / 2.0) ** 2) * 0.05        # the washing gives a little warm light back
    c = LIME * (SKY * 0.62 + v3(1.0, 0.75, 0.5) * warm)
    near_dark = 0.42 + 0.58 * np.clip((Q[2] - 4.5) / 4.0, 0, 1)   # she holds the near roof down
    return tone(c * near_dark, 1.8) * np.exp(rng.normal(0, 0.04))


deck_b = Brush(width=30, bristle=1.8, opacity=0.92, pickup=0.25, dryness=0.0, thickness=0.15, jitter=0.04, deplete=0.0006)
lay_screen(board, (-260, yp_bot - 6, W + 260, H + 40), scrub.but(width=90), lambda x, y: scale(roof_shade(x, y), 0.9),
           angle=0.0, angle_jitter=0.03, length=500, cover=3.5, wobble=3)
lay_screen(board, (-260, yp_bot - 16, W + 260, H + 40), deck_b, roof_shade, angle=0.0, angle_jitter=0.03, length=320,
           cover=6.0, wobble=2)
# the parapet: a wall of soft stone facing the east, so it has more sky on it than the roof does
board.tape(np.array([(-10, yp_top), (W + 10, yp_top), (W + 10, yp_bot), (-10, yp_bot)]), feather=0.8)
par = lambda x, y: tone(LIME * SKY * (1.05 + 0.15 * (y - yp_top) / (yp_bot - yp_top)), 1.8) * np.exp(rng.normal(0, 0.035))  # noqa: E731
lay_screen(board, (-40, yp_top - 5, W + 40, yp_bot + 5), deck_b.but(width=14), par, angle=0.0, angle_jitter=0.02,
           length=200, cover=8.0, wobble=0.6)
joint = Brush(width=2.2, bristle=0.8, opacity=0.5, pickup=0.3, thickness=0.2, gap=0.0, taper=(0.05, 0.05))
jc = tone(LIME * SKY * 0.55, 1.8)
for y in np.arange(0.27, PAR_H, 0.27):                       # courses
    yy = P(v3(0, y, ZP))[1]
    board.stroke([(-10, yy), (W + 10, yy + rng.normal(0, 1))], joint, jc, wobble=0.6)
for i, y in enumerate(np.arange(0.0, PAR_H - 0.2, 0.27)):    # perpends, staggered
    for x in np.arange(-8 + 0.3 * (i % 2), 8, 0.6):
        a, b = P(v3(x, y + 0.02, ZP)), P(v3(x, y + 0.25, ZP))
        board.stroke([a, b], joint.but(width=1.8), jc)
board.untape()
board.stroke([(-10, yp_top + 2), (W + 10, yp_top + 2)], Brush(width=5, opacity=0.85, gap=0, thickness=0.8, pickup=0.1),
             tone(LIME * SKY * 1.55, 1.8), wobble=0.5)
board.stroke([(-10, yp_top + 6), (W + 10, yp_top + 6)], Brush(width=3, opacity=0.6, gap=0, thickness=0.3), jc, wobble=0.5)
# where the wall meets the roof
board.stroke([(-10, yp_bot), (W + 10, yp_bot)], Brush(width=6, opacity=0.6, gap=0, thickness=0.2), scale(jc, 0.8), wobble=1)
board.dry()
board.stage("the roof, already in shade")


# =================================================================================================
# 3. Far line.
# =================================================================================================
def shade_of(sheet, parts=("sky", "sun"), gain=1.0, vary=0.035):
    def f(u, v):
        return tone(cloth_light(sheet, u, v, parts) * gain) * np.exp(rng.normal(0, vary))
    return f


blk = Brush(width=22, bristle=1.5, opacity=0.95, pickup=0.25, dryness=0.04, thickness=0.4, jitter=0.03, deplete=0.0006)
for s in FAR:
    lay_cloth(board, cam, s, blk.but(width=16), shade_of(s), along="v", length=90, cover=6.0, wobble=0.6)
board.dry()
board.stage("the far line")

# =================================================================================================
# 4. Near line: the side facing me first, all in its own shadow.
# =================================================================================================
for s in NEAR[::-1]:
    lay_cloth(board, cam, s, blk.but(width=26), shade_of(s, ("sky",), gain=1.3), along="v", length=180, cover=3.5,
              wobble=1.0, margin=0.1)
board.dry()
board.stage("near line, the shadow side first")

# =================================================================================================
# 5. The sun coming through.
# =================================================================================================
lt = Brush(width=18, bristle=1.4, opacity=0.9, pickup=0.4, dryness=0.0, thickness=0.45, jitter=0.03, deplete=0.0005,
           taper=(0.22, 0.25))
for s in NEAR[::-1]:
    lay_cloth(board, cam, s, lt, shade_of(s, vary=0.02), along="v", length=200, cover=7.0, wobble=0.8, margin=0.1)
    # the hem and the fold over the wire run across, and seal the ends of the hanging strokes
    lay_cloth(board, cam, s, lt.but(width=12, pickup=0.4), shade_of(s, vary=0.015), along="u", length=110, cover=1.2,
              wobble=0.5, margin=0.06, where=lambda u, v: v > 0.86)
    if s.band:
        lay_cloth(board, cam, s, lt.but(width=10, pickup=0.4), shade_of(s, vary=0.015), along="u", length=120,
                  cover=0.5, wobble=0.4, margin=0.03, where=lambda u, v, b=s.band: v < b + 0.01)
board.dry()
board.stage("the sun coming through")

# =================================================================================================
# 6. The sun behind the third sheet. Thick, in one go.
# =================================================================================================
hot = Brush(width=16, bristle=1.4, opacity=0.95, pickup=0.25, dryness=0.0, thickness=2.4, jitter=0.02, deplete=0.0004,
            gap=0.01)
sx, sy = P(E + L * 100)


def near_sun(u, v, r=0.075):
    d = unit(S3.pos(u, v) - E) @ L
    return d > np.cos(r)


for r, wd, ln, th, cv in [(0.13, 18, 170, 0.8, 4.0), (0.085, 14, 130, 1.1, 5.0), (0.05, 12, 90, 1.5, 6.0), (0.025, 10, 60, 2.0, 7.0)]:
    lay_cloth(board, cam, S3, hot.but(width=wd, thickness=th, pickup=0.55), shade_of(S3, vary=0.01), along="v",
              length=ln, cover=cv, wobble=0.5, where=lambda u, v, r=r: near_sun(u, v, r))
# the core, where it is nearly too much to look at
core = mix((white, 12), (naples, 1), (cadyel, 0.3))
for i in range(26):
    a = rng.normal(0, 1, 2) * np.array([10, 16])
    board.stroke([(sx + a[0], sy + a[1] - 14), (sx + a[0] + rng.normal(0, 2), sy + a[1] + 14)],
                 hot.but(width=rng.uniform(6, 10), thickness=3.0, pickup=0.2, taper=(0.3, 0.3)), core)
board.dry()
board.stage("the sun behind the third sheet")

# =================================================================================================
# 7. Wire and pegs.
# =================================================================================================
fine = Brush(width=3, bristle=0.9, opacity=0.9, pickup=0.0, thickness=0.8, jitter=0.02, gap=0.0, taper=(0.0, 0.0),
             deplete=0.0)
wire = scale(mix((black, 2), (ultra, 1)), 3.0)
board.tape(*[o.outline(cam) for o in NEAR], outside=True, feather=0.6)
board.stroke(P(far.pts(n=80)), fine.but(width=2.0), wire, smooth=False)
board.untape()
board.stroke(P(near.pts(n=80)), fine.but(width=2.8), wire, smooth=False)
peg_c = mix((burnsi, 2), (black, 1.5), (ochre, 0.5))
rim_c = mix((cadorange, 1), (naples, 2), (white, 1))
for sh in NEAR:
    for k in range(sh.pegs):
        u = k / (sh.pegs - 1) + rng.normal(0, 0.01)
        top = sh.line.at(sh.s0 + u * sh.width)
        a, b = P(top + v3(0, 0.025, 0)), P(top - v3(0, 0.055, 0))
        wpx = max(3.0, 0.016 * cam.f / (top[2] - E[2]))
        board.stroke([a, b + rng.normal(0, 0.5, 2)], fine.but(width=wpx, thickness=1.4), scale(peg_c, rng.uniform(0.8, 1.3)))
        board.stroke([a + (0.4 * wpx, 0), b + (0.4 * wpx, -2)], fine.but(width=1.0, opacity=0.7), rim_c)
board.stage("wire and pegs")

# =================================================================================================
# 8. The basket, with what is already in.
# =================================================================================================
bx, bz, rx, rz, bh = -1.3, 5.5, 0.33, 0.23, 0.27


def ring(y, k=1.0, t0=0.0, t1=2 * np.pi, n=40):
    t = np.linspace(t0, t1, n)
    return P(np.stack([bx + rx * k * np.cos(t), np.full(n, y), bz + rz * k * np.sin(t)], 1))


PLASTIC = turq
def basket_light(N, gain=1.0):
    N = unit(np.asarray(N, dtype=np.float64))
    return SKY * (0.55 + 0.45 * N[1]) * (0.7 + 0.3 * max(0.0, -N[2])) * gain


# a soft dark where it sits, and two pegs that went on the floor
sit = tone(LIME * SKY * 0.22, 1.8)
for k in (1.18, 1.05, 0.95):
    board.stroke(ring(0.0, k, 0, 2 * np.pi, 50), Brush(width=14, opacity=0.45, pickup=0.5, thickness=0.1, taper=(0, 0)),
                 sit, smooth=False)
for px_, pz_, ang in [(-0.62, 5.15, 0.4), (-0.48, 5.3, 2.1)]:
    a = P(v3(px_, 0.01, pz_))
    d = np.array([np.cos(ang), np.sin(ang) * 0.35]) * 9
    board.stroke([a - d, a + d], Brush(width=4, opacity=0.95, gap=0, thickness=1.0, taper=(0.05, 0.05)), scale(peg_c, 1.6))
    board.stroke([a - d + (1, 3), a + d + (1, 3)], Brush(width=3, opacity=0.4, gap=0, thickness=0.1), sit)
front = np.vstack([ring(bh, 1.0, 0, np.pi), ring(0.0, 0.86, np.pi, 0)])     # sin<0 is the near side
front = np.vstack([ring(bh, 1.0, np.pi, 2 * np.pi), ring(0.0, 0.86, 2 * np.pi, np.pi)])
board.tape(front, feather=0.7)
for t in np.linspace(np.pi - 0.1, 2 * np.pi + 0.1, 70):
    N = v3(np.cos(t), 0.05, np.sin(t) * rx / rz)
    c = tone(PLASTIC * basket_light(N, 1.6), 2.0) * np.exp(rng.normal(0, 0.04))
    a = P(v3(bx + rx * np.cos(t), bh, bz + rz * np.sin(t)))
    b = P(v3(bx + 0.86 * rx * np.cos(t), 0.0, bz + 0.86 * rz * np.sin(t)))
    board.stroke([a, b], Brush(width=9, opacity=0.95, pickup=0.3, thickness=0.6, taper=(0.02, 0.05)), c)
# slots moulded in the side, three rows
for row, y in enumerate((0.07, 0.13, 0.19)):
    k = 0.86 + 0.14 * y / bh
    for t in np.linspace(np.pi + 0.25, 2 * np.pi - 0.25, 13) + 0.12 * (row % 2):
        p0 = v3(bx + rx * k * np.cos(t), y, bz + rz * k * np.sin(t))
        a, b = P(p0 - v3(-np.sin(t), 0, np.cos(t)) * 0.025), P(p0 + v3(-np.sin(t), 0, np.cos(t)) * 0.025)
        board.stroke([a, b], Brush(width=3.5, opacity=0.85, gap=0, thickness=0.2, taper=(0, 0)), tone(PLASTIC * SKY * 0.25, 2.0))
board.untape()
# inside: the back wall in its own shadow, then what's folded in it
inner = ring(bh, 0.95, 0, 2 * np.pi, 50)
board.tape(inner, feather=0.6)
lay_screen(board, tuple(np.r_[inner.min(0) - 6, inner.max(0) + 6]), Brush(width=10, opacity=0.95, pickup=0.3, thickness=0.3),
           lambda x, y: tone(PLASTIC * SKY * 0.5, 2.0) * np.exp(rng.normal(0, 0.04)), angle=np.pi / 2, length=40, cover=4)
fold = np.vstack([ring(bh - 0.05, 0.86, np.pi * 0.08, np.pi * 0.92, 20)[::-1], ring(bh - 0.04, 0.9, np.pi * 1.0, np.pi * 2.0, 30)])
board.tape(fold, feather=0.6)
for i in range(70):
    q = fold[rng.integers(len(fold))] * 0.4 + fold.mean(0) * 0.6 + rng.normal(0, 6, 2)
    c = tone(COTTON * SKY * rng.choice([1.25, 1.45, 1.0]), 2.0) * np.exp(rng.normal(0, 0.03))
    board.dab(q[0], q[1], Brush(width=12, opacity=0.9, pickup=0.3, thickness=1.0), c, angle=rng.normal(0.05, 0.08),
              length=rng.uniform(30, 70))
# folds in the stack: the edges of each sheet as it was laid in
for yy in (bh - 0.045, bh - 0.06):
    board.stroke(ring(yy, 0.8, np.pi * 1.15, np.pi * 1.85, 16), Brush(width=2.2, opacity=0.6, gap=0, thickness=0.3),
                 tone(COTTON * SKY * 0.6, 2.0))
board.untape()
board.untape()
# the rim catches the sky
board.stroke(ring(bh, 1.0, np.pi * 0.98, np.pi * 2.02, 40), Brush(width=5, opacity=0.95, gap=0, thickness=1.6, pickup=0.1,
             taper=(0.05, 0.05)), tone(PLASTIC * SKY * 2.4 + 0.02, 2.0))
board.stroke(ring(bh, 0.97, 0.0, np.pi, 30), Brush(width=3, opacity=0.8, gap=0, thickness=0.8, taper=(0.05, 0.05)),
             tone(PLASTIC * SKY * 1.6, 2.0))
board.dry()
board.stage("the basket, with what is already in")

finish(board, HERE, title="Majjistral, last sun", artist="carmela-zammit", year=1986,
       medium="Oil on cotton sheeting, red oxide ground", made="2026-11-09")
