"""Carmela Zammit - Grigal

The roof on a January afternoon with the gregale on it, cold and bright, the sky scoured. She has
her back to the wind and the sun in front of her, low, behind the line. The washing is at the top
of the board, most of it out of the picture; what is in the picture is the roof, and the shadows of
the washing lying on it, all going one way. The basket has gone over.
"""
import os
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw
from scipy.spatial import ConvexHull

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[3]))
sys.path.insert(0, str(HERE.parents[1]))

from engine import Board, Brush, hexc, mix, scale  # noqa: E402
from engine.studio import finish  # noqa: E402
from tools import Camera, Gust, Line, Sheet, cast, lay_cloth, lay_field, lay_screen, sheeting, tone, unit, v3  # noqa: E402

QUICK = float(os.environ.get("QUICK", "1.0"))     # less cover while she is still finding it

W, H = 1200, 1500
rng0 = np.random.default_rng(1989)
board = Board(W, H, hexc("#7a3021"), sheeting(W, H, rng0, darns=[(300, 1180, 34, 24)]), seed=1989,
              light=(0.55, -0.8))
rng = board.rng
cam = Camera(W, H, 1600, (0.0, 1.62, 0.0), pitch=-0.43)
E = cam.eye
P = cam.P

# --- tubes ---------------------------------------------------------------------------------------
white, ultra, prussian = hexc("#f7f4ec"), hexc("#20307f"), hexc("#14284a")
naples, ochre, rawsi, burnsi = hexc("#ecd398"), hexc("#c49236"), hexc("#a8692a"), hexc("#7d3418")
cadyel, cadorange, black, turq = hexc("#f2cc3a"), hexc("#e8782a"), hexc("#141210"), hexc("#2a9a9a")

# --- the roof and the line -----------------------------------------------------------------------
ZB, PAR_H = 14.0, 1.0
WIND = (-0.72, 0.69)                        # from behind her right shoulder: the gregale
line = Line((-3.6, 3.4), (5.5, 11.0), 2.05, 0.10)
G1 = Gust(line, 0.20, 2.10, 1.55, pegs=4, wind=WIND, throw=0.95, flap=0.45, band=0.08, seed=1)
G2 = Gust(line, 2.55, 0.70, 0.75, pegs=2, wind=WIND, throw=1.25, flap=0.5, seed=2)       # pillowcase
G3 = Gust(line, 3.50, 2.00, 1.45, pegs=4, wind=WIND, throw=0.9, flap=0.45, band=0.08, seed=3)
G4 = Gust(line, 5.75, 1.00, 1.30, pegs=3, wind=WIND, throw=0.75, flap=0.2, seed=4)        # towel
G5 = Gust(line, 7.00, 1.95, 1.45, pegs=4, wind=WIND, throw=0.95, flap=0.45, band=0.08, seed=5)
G6 = Gust(line, 9.25, 0.70, 0.75, pegs=2, wind=WIND, throw=1.2, flap=0.5, seed=6)
G7 = Gust(line, 10.1, 1.60, 1.40, pegs=4, wind=WIND, throw=0.9, flap=0.45, band=0.08, seed=7)
WASH = [G1, G2, G3, G4, G5, G6, G7]


# --- the basket, over, and the sheet the wind is taking out of it -------------------------------
WD = unit(v3(WIND[0], 0, WIND[1]))
SIDE = unit(np.cross(WD, v3(0, 1, 0)))
BC = v3(1.05, 0.0, 3.7)                      # where the basket lies
BRX, BRZ, BH = 0.33, 0.23, 0.27


class Basket:
    """The laundry basket on its side, mouth to the wind's way. u goes round it, v from the bottom to
    the mouth; with solid, v from the middle of the bottom instead, for its shadow."""
    band = 0.0
    axis = unit(SIDE + WD * 0.3)

    def __init__(self, solid=False):
        self.solid = solid

    def pos(self, u, v):
        u, v = np.broadcast_arrays(np.asarray(u, dtype=np.float64), np.asarray(v, dtype=np.float64))
        th = 2 * np.pi * u
        r = 0.86 + 0.14 * np.clip(v, 0, 1)
        if self.solid:
            v = 1.3 * v - 0.3
            r = np.where(v < 0, 0.86 * (1 + v / 0.3), 0.86 + 0.14 * v)
            v = np.maximum(v, 0)
        side = unit(np.cross(self.axis, v3(0, 1, 0)))
        c = BC + v3(0, BRZ * 0.93, 0) + self.axis * ((v - 0.5) * BH)[..., None]
        return c + side * (BRX * r * np.cos(th))[..., None] + v3(0, 1, 0) * (BRZ * r * np.sin(th))[..., None]


class Spill(Sheet):
    """A sheet half out of the basket, lying on the roof, dragged the way the wind goes: crumpled
    across, and the far end lifted and turning over. u runs along it from the basket, v across."""

    def __init__(self, start, length, width, seed=0):
        self.start, self.length, self.width, self.band = start, length, width, 0.0
        r = np.random.default_rng(seed)
        self.ph = r.uniform(0, 2 * np.pi, 6)

    def pos(self, u, v):
        u, v = np.broadcast_arrays(np.asarray(u, dtype=np.float64), np.asarray(v, dtype=np.float64))
        ph = self.ph
        gather = 0.25 + 0.75 * np.clip(u / 0.16, 0, 1) ** 0.6         # bunched where it comes out of the mouth
        edge = 0.06 * np.sin(2 * np.pi * (2.3 * u) + ph[4]) * np.clip(2 * v - 1, 0, 1) \
            - 0.03 * np.sin(2 * np.pi * (1.6 * u) + ph[5]) * np.clip(1 - 2 * v, 0, 1)
        bend = 0.1 * np.sin(np.pi * u + ph[0]) * u
        skew = 0.35 * (v - 0.5) * np.clip((u - 0.5) / 0.5, 0, 1)        # the far end does not lie square
        along = WD * (u * self.length + skew)[..., None] \
            + SIDE * (bend + edge + (v - 0.5) * self.width * gather * (0.85 + 0.3 * u))[..., None]
        # dragged cloth rucks up across the way it is pulled
        ruck = 0.06 * np.abs(np.sin(2 * np.pi * (1.3 * u + 0.25 * v) + ph[1])) ** 0.8 * np.clip(u / 0.2, 0, 1) \
            + 0.012 * np.sin(2 * np.pi * (2.0 * u - 1.2 * v) + ph[2])
        # one far corner the wind has got under, lifting and going back over
        cn = np.clip((u - 0.6) / 0.4, 0, 1) ** 2 * np.clip((v - 0.3) / 0.7, 0, 1) ** 1.2
        h = 0.015 + ruck + 0.13 * cn + 0.14 * np.clip(0.12 - u, 0, 1) / 0.12
        along = along - WD * (0.08 * cn)[..., None]
        return self.start + along + v3(0, 1, 0) * h[..., None]

    def outline(self, cam, n=40):
        return Sheet.outline(self, cam, n)




class Prop:
    """The wooden prop that holds the wire up in the middle, leaning in from her side. Thin as it is,
    it throws a shadow the whole way across the roof. u goes across it, v from the foot up."""
    band = 0.0

    def __init__(self, s, out=0.7, w=0.045):
        self.top = line.at(s)
        self.foot = self.top * v3(1, 0, 1) - v3(line.n[0], 0, line.n[1]) * out
        self.across = unit(np.cross(v3(L[0], 0, L[2]), v3(0, 1, 0))) * w

    def pos(self, u, v):
        u, v = np.broadcast_arrays(np.asarray(u, dtype=np.float64), np.asarray(v, dtype=np.float64))
        return self.foot + (self.top - self.foot) * v[..., None] + self.across * (u - 0.5)[..., None]

BASKET = Basket()
SPILL = Spill(BC + Basket.axis * BH * 0.5, 2.6, 1.1, seed=9)

# --- the light -----------------------------------------------------------------------------------
AZ, EL = 0.42, 0.25                           # the sun, low, ahead of her and to the right
L = unit(v3(np.sin(AZ) * np.cos(EL), np.sin(EL), np.cos(AZ) * np.cos(EL)))
SUN = v3(1.0, 0.88, 0.70) * 2.2
SKY = v3(0.13, 0.24, 0.62) * 0.36            # a scoured sky: blue, and a lot of it
THROUGH = v3(1.0, 0.90, 0.76)                # what cotton does to the sun coming through it
TAU, TAU2 = 0.2, 0.07
COTTON = mix((white, 10), (naples, 0.7))
LIME = scale(mix((white, 3), (naples, 1.4), (ochre, 0.1), (burnsi, 0.08)), 0.72)   # weathered screed

PROP = Prop(5.3)
ON_SPILL = cast(cam, W, H, WASH, L, tau=TAU, tau2=TAU2) * cast(cam, W, H, [Basket(solid=True)], L, tau=0.03) \
    * cast(cam, W, H, [PROP], L, tau=0.0, grid=(2, 40))
SUNLIT = ON_SPILL * cast(cam, W, H, [SPILL], L, tau=TAU)


def wall_shadow(Q):
    """1 where the back wall keeps the sun off the roof: it is between the roof and the sun."""
    t = (ZB - Q[..., 2]) / L[2]
    return (Q[..., 1] + L[1] * t < PAR_H).astype(float)


def sun_at(x, y):
    """How much sun reaches the roof seen at board point (x, y), and how warm what gets through is."""
    xi = np.clip(np.asarray(x).astype(int), 0, W - 1)
    yi = np.clip(np.asarray(y).astype(int), 0, H - 1)
    return SUNLIT[yi, xi]


def roof_colour(x, y, vary=0.03, open_sun=False):
    """The screed seen at (x, y). With open_sun, as if nothing were on the line."""
    x, y = np.atleast_1d(x).astype(float), np.atleast_1d(y).astype(float)
    Q = cam.on_ground(x, y)
    k = (1.0 if open_sun else sun_at(x, y)) * (1 - 0.7 * wall_shadow(Q))
    # through cotton the sun comes out warmer and it comes from the whole cloth, not one direction
    sun = np.where(k[:, None] > 0.98, SUN, SUN * THROUGH)
    c = LIME * (SKY * 1.0 + sun * L[1] * k[:, None])
    dist = np.hypot(Q[:, 0], Q[:, 2])
    c = c * (0.92 + 0.08 * np.clip((dist - 2) / 10, 0, 1))[:, None]
    c = tone(c, 1.9) * np.exp(rng.normal(0, vary, 3))
    return c if c.shape[0] > 1 else c[0]


def sky_colour(x, y):
    d = cam.ray(x, y)
    el = np.arcsin(np.clip(d[..., 1], -1, 1))
    t = np.clip(el / 0.3, 0, 1) ** 0.7
    low, high = v3(0.36, 0.47, 0.64), v3(0.06, 0.15, 0.46)
    c = np.exp(np.log(low) * (1 - t[..., None]) + np.log(high) * t[..., None])
    ang = np.arccos(np.clip(d @ L, -1, 1))
    c = c + v3(1.0, 0.85, 0.6) * 0.18 * np.exp(-ang / 0.25)
    return np.clip(c, 0.004, 0.97)


# =================================================================================================
# 1. The sky, the strip of it there is, wet, over the red.
# =================================================================================================
par_top_y = float(P(v3(0, PAR_H, ZB))[1])
par_bot_y = float(P(v3(0, 0, ZB))[1])
scrub = Brush(width=110, bristle=2.6, opacity=0.97, pickup=0.08, dryness=0.0, thickness=0.05, jitter=0.03, deplete=0.0005)
sky_b = Brush(width=40, bristle=2.0, opacity=0.65, pickup=0.4, dryness=0.0, thickness=0.05, jitter=0.025,
              deplete=0.0004, taper=(0.15, 0.2))
region = (-60, -40, W + 60, par_top_y + 20)
lay_screen(board, region, scrub, lambda x, y: scale(sky_colour(x, y), 0.88), angle=-0.05, length=500, cover=3.5 * QUICK, wobble=8)
lay_screen(board, region, sky_b, lambda x, y: sky_colour(x, y) * np.exp(rng.normal(0, 0.03, 3)), angle=-0.05,
           length=380, cover=7.0 * QUICK, wobble=6)
board.dry()
board.stage("a strip of scoured sky")

# =================================================================================================
# 2. The roof, all of it in the sun first, and the wall at the back with its face in shade.
# =================================================================================================
deck = Brush(width=36, bristle=1.8, opacity=0.85, pickup=0.5, dryness=0.0, thickness=0.12, jitter=0.04, deplete=0.0006)
lay_screen(board, (-150, par_bot_y - 10, W + 150, H + 40), scrub.but(width=100),
           lambda x, y: scale(roof_colour(x, y, open_sun=True), 0.9), angle=0.0, angle_jitter=0.04, length=480, cover=3.0 * QUICK, wobble=3)
# the brush gets smaller as the roof goes away
bands = np.linspace(par_bot_y - 14, H + 40, 7)
for y0, y1 in zip(bands[:-1], bands[1:]):
    zk = float(np.clip((((y0 + y1) / 2) - par_bot_y) / (H - par_bot_y), 0.15, 1.0))
    lay_screen(board, (-150, y0, W + 150, y1), deck.but(width=10 + 30 * zk), lambda x, y: roof_colour(x, y, 0.018, open_sun=True),
               angle=0.0, angle_jitter=0.03, length=90 + 300 * zk, cover=5.0 * QUICK, wobble=0.5 + 1.5 * zk)

back = np.array([P(v3(-9, PAR_H, ZB)), P(v3(10, PAR_H, ZB)), P(v3(10, 0, ZB)), P(v3(-9, 0, ZB))])
board.tape(back, feather=0.7)
wallc = lambda x, y: tone(LIME * SKY * 0.9 * (0.95 + 0.1 * (y - par_top_y) / (par_bot_y - par_top_y)), 2.2) * np.exp(rng.normal(0, 0.03, 3))  # noqa: E731
lay_screen(board, (-20, par_top_y - 4, W + 20, par_bot_y + 4), deck.but(width=12, thickness=0.1), wallc, angle=0.0,
           angle_jitter=0.02, length=160, cover=8.0 * QUICK, wobble=0.6)
board.untape()
# near her the big brush again, broken: warmer and cooler in turn, the way screed is in a low sun
near_y = float(P(v3(0, 0, 3.2))[1])
lay_screen(board, (-100, near_y, W + 100, H + 40), deck.but(width=34, opacity=0.7, thickness=0.3, pickup=0.35),
           lambda x, y: roof_colour(x, y, 0.0, open_sun=True) * np.exp(rng.normal(0, 0.05) + v3(0.03, 0, -0.03) * rng.normal(0, 1.2)),
           angle=lambda x, y: -0.06, angle_jitter=0.05, length=300, cover=1.6 * QUICK, wobble=2.0)
board.stroke([(-10, par_top_y + 1), (W + 10, par_top_y + 1)], Brush(width=4, opacity=0.9, gap=0, thickness=0.6, pickup=0.1),
             tone(LIME * (SKY + SUN * 0.25), 2.2), wobble=0.5)
board.dry()
board.stage("the roof, all in the sun")

# =================================================================================================
# 3. The shadows of the washing, laid on the roof the way they fall.
# =================================================================================================
# on the board the shadows run along the projection of the sun's direction
g0 = cam.on_ground(np.float64(W / 2), np.float64(H * 0.6))
sdir = P(g0 - v3(L[0], 0, L[2]) * 0.5) - P(g0)
SANG = float(np.arctan2(sdir[1], sdir[0]))
shade_b = Brush(width=22, bristle=1.6, opacity=0.9, pickup=0.35, dryness=0.0, thickness=0.1, jitter=0.03, deplete=0.0005,
                taper=(0.15, 0.2))
board.tape_where(np.clip((0.97 - SUNLIT) * 6, 0, 1), feather=1.2)
lay_field(board, (-60, par_bot_y, W + 60, H + 40), shade_b, lambda xs, ys: roof_colour(xs, ys, 0.02),
          angle=SANG, length=140, cover=7.0 * QUICK, wobble=0.8, angle_jitter=0.05)
board.untape()
board.dry()
board.stage("the shadows of the washing")

# the joints in the screed, every three metres, and what else stands up and throws a shadow: the prop
# and the wire
jnt = Brush(width=3, bristle=1.0, opacity=0.55, gap=0.1, pickup=0.3, thickness=0.05, taper=(0.1, 0.1))


def ground_line(a, b, n=300):
    """A line on the roof, only as far as it is on the board (a brush run off the edge comes back dry)."""
    p = np.linspace(a, b, n)
    p = P(p[p[:, 2] > 0.8])
    inside = (p[:, 0] > -30) & (p[:, 0] < W + 30) & (p[:, 1] > -30) & (p[:, 1] < H + 30)
    return p[inside]


def darker(k):
    return lambda xs, ys: roof_colour(xs, ys, 0.02) * k


for z in np.arange(2.9, ZB - 0.5, 3.0):
    pts = ground_line(v3(-9, 0, z), v3(10, 0, z))
    if len(pts) > 2:
        board.stroke(pts, jnt.but(width=max(1.6, 12.0 / z)), darker(0.5)(pts[:, 0], pts[:, 1]), wobble=0.5, smooth=False)
for x in np.arange(-7.6, 9.0, 3.0):
    pts = ground_line(v3(x, 0, 1.0), v3(x, 0, ZB))
    if len(pts) > 2:
        board.stroke(pts, jnt.but(width=3.0), darker(0.5)(pts[:, 0], pts[:, 1]), wobble=0.5, smooth=False,
                     pressure=lambda t: 0.5 + 0.5 * (1 - t))
# the prop's shadow, one long stroke from its foot to wherever the top of it lands
prop_sh = PROP.pos(np.full(120, 0.5), np.linspace(0, 1, 120))
prop_sh = prop_sh - L * (prop_sh[:, 1] / L[1])[:, None]
prop_sh = P(prop_sh[prop_sh[:, 2] > 1.0])
prop_sh = prop_sh[(prop_sh[:, 0] > -30) & (prop_sh[:, 1] < H + 30)]
board.stroke(prop_sh, Brush(width=7, bristle=1.1, opacity=0.9, gap=0.02, pickup=0.3, thickness=0.1, taper=(0.0, 0.05)),
             darker(0.42)(prop_sh[:, 0], prop_sh[:, 1]) * np.exp(rng.normal(0, 0.02, 3)))
wire_g = line.pts(n=120)
wire_g = wire_g - L * (wire_g[:, 1] / L[1])[:, None]
pts = P(wire_g[wire_g[:, 2] > 1.0])
keep = (pts[:, 0] > -50) & (pts[:, 0] < W + 50) & (pts[:, 1] > 0) & (pts[:, 1] < H + 50)
if keep.sum() > 2:
    pts = pts[keep]
    board.stroke(pts, Brush(width=4, bristle=0.9, opacity=0.85, gap=0.0, pickup=0.2, thickness=0.05, taper=(0.0, 0.0)),
                 darker(0.45)(pts[:, 0], pts[:, 1]), smooth=False)
board.dry()
board.stage("joints, and the shadows of the prop and the wire")

# =================================================================================================
# 4. The washing, what there is of it, with the sun coming through from behind.
# =================================================================================================
BOUNCE = LIME * SUN * L[1] * 0.35            # the sunlit roof gives some back, up under the cloth


def cloth(sheet, gain=1.0, vary=0.03):
    def f(u, v):
        u, v = np.atleast_1d(u).astype(float), np.atleast_1d(v).astype(float)
        n = sheet.normal(u, v, E)
        nl = n @ L
        layers = np.where((v < sheet.band) | (v > 0.96), TAU2 / TAU, 1.0)
        front = COTTON * SUN * np.clip(nl, 0, 1)[:, None] * 0.9
        back = THROUGH * SUN * TAU * (np.clip(-nl, 0, 1) ** 0.6 * layers)[:, None]
        amb = COTTON * (SKY * (0.5 + 0.5 * n[:, 1:2]) + BOUNCE * (0.5 - 0.5 * n[:, 1:2]))
        c = tone((np.where(nl[:, None] > 0, front, back) + amb) * gain, 2.0) * np.exp(rng.normal(0, vary, 3))
        return c if c.shape[0] > 1 else c[0]
    return f


blk = Brush(width=26, bristle=1.5, opacity=0.92, pickup=0.3, dryness=0.03, thickness=0.35, jitter=0.03, deplete=0.0006)
for s in WASH[::-1]:
    lay_cloth(board, cam, s, blk, cloth(s, gain=0.9, vary=0.02), along="v", length=220, cover=3.0 * QUICK, wobble=1.0, margin=0.06)
board.dry()
board.stage("the washing laid in, the side away from the sun")

fold_b = Brush(width=15, bristle=1.4, opacity=0.9, pickup=0.4, dryness=0.0, thickness=0.45, jitter=0.025, deplete=0.0005,
               taper=(0.2, 0.25))
for s in WASH[::-1]:
    lay_cloth(board, cam, s, fold_b, cloth(s, vary=0.015), along="v", length=240, cover=7.0 * QUICK, wobble=0.6, margin=0.05,
              run=True)
    lay_cloth(board, cam, s, fold_b.but(width=9, opacity=0.7), cloth(s, vary=0.015), along="u", length=110, cover=1.0 * QUICK,
              wobble=0.4, margin=0.04, where=lambda u, v: v > 0.88, run=True)
fine = Brush(width=3, bristle=0.9, opacity=0.9, pickup=0.0, thickness=0.8, jitter=0.02, gap=0.0, taper=(0.0, 0.0), deplete=0.0)
board.stroke(P(line.pts(n=80)), fine.but(width=3.2), tone(mix((black, 2), (ultra, 1)) * 0.6, 2.0), smooth=False)
board.dry()
wood = mix((burnsi, 2), (rawsi, 1), (black, 0.6))
pw = max(4.0, 0.05 * cam.f / (PROP.foot[2] - E[2]))
board.stroke([P(PROP.foot), P(PROP.top)], Brush(width=pw, opacity=0.95, gap=0.0, thickness=0.6, pickup=0.1, taper=(0.0, 0.0)),
             tone(wood * (SKY + BOUNCE * 0.8), 1.9), smooth=False)
board.stroke([P(PROP.foot) + (pw * 0.35, 0), P(PROP.top) + (pw * 0.35, 0)],
             Brush(width=pw * 0.3, opacity=0.8, gap=0.0, thickness=0.5, taper=(0.0, 0.0)), tone(wood * SUN * 0.35, 1.9), smooth=False)
board.stage("the sun through the washing")

# =================================================================================================
# 5. The basket, over on its side.
# =================================================================================================
PLASTIC = mix((turq, 2), (ultra, 0.3), (white, 1.6), (rawsi, 0.9), (burnsi, 0.2))


def basket_light(u, v, inside=False):
    u, v = np.atleast_1d(u).astype(float), np.atleast_1d(v).astype(float)
    e = 1e-3
    pu = BASKET.pos(u + e, v) - BASKET.pos(u - e, v)
    pv = BASKET.pos(u, v + e) - BASKET.pos(u, v - e)
    n = unit(np.cross(pu, pv))
    out = BASKET.pos(u, v) - (BC + v3(0, BRZ * 0.93, 0)) - Basket.axis * ((v - 0.5) * BH)[:, None]
    n = n * np.sign(np.sum(n * out, axis=-1, keepdims=True))      # outward
    if inside:
        n = -n
    x, y = P(BASKET.pos(u, v)).T
    k = np.clip(n @ L, 0, 1) * (sun_at(x, y) if not inside else 0.15)
    c = PLASTIC * (SUN * k[:, None] * 0.9 + SKY * (0.55 + 0.45 * n[:, 1:2]) + BOUNCE * 0.6 * (0.5 - 0.5 * n[:, 1:2]))
    c = tone(c, 1.9) * np.exp(rng.normal(0, 0.03, 3))
    return c if c.shape[0] > 1 else c[0]


uu, vv = np.meshgrid(np.linspace(0, 1, 60), np.linspace(0, 1, 12))
bpts = P(BASKET.pos(uu, vv)).reshape(-1, 2)
hull = bpts[ConvexHull(bpts).vertices]
_im = Image.new("L", (W, H), 0)
ImageDraw.Draw(_im).polygon([tuple(q) for q in SPILL.outline(cam)], fill=1)
SPILL_MASK = np.asarray(_im) > 0
ImageDraw.Draw(_im).polygon([tuple(q) for q in hull], fill=1)
TAKEN = np.asarray(_im) > 0
board.tape(hull, feather=0.7)
pl = Brush(width=10, bristle=1.2, opacity=0.95, pickup=0.25, thickness=0.5, jitter=0.03, taper=(0.05, 0.08), gap=0.02)
for u0 in rng.permutation(np.linspace(0, 1, 140, endpoint=False)):
    vs = np.linspace(-0.05, 1.05, 6)
    board.stroke(P(BASKET.pos(np.full(6, u0), vs)), pl, basket_light(np.full(6, u0), vs), wobble=0.3)
# the mouth, and the dark inside it
# the end toward her: the mouth, dark inside, or the bottom, which takes the sky like the sides
facing = float(Basket.axis @ (E - BC)) > 0
mouth = P(BASKET.pos(np.linspace(0, 1, 50), np.full(50, 1.0 if facing else 0.0)))
board.tape(mouth, feather=0.8, mode="and")
inner = tone(PLASTIC * SKY * (0.35 if facing else 0.75), 1.9)
lay_screen(board, tuple(np.r_[mouth.min(0) - 4, mouth.max(0) + 4]), pl.but(width=12, opacity=0.9),
           lambda x, y: inner * np.exp(rng.normal(0, 0.05, 3)), angle=1.2, length=40, cover=5, wobble=0.4)
# through the mouth, the inside of the far wall, lit by what sky gets in
cen = BC + v3(0, BRZ * 0.93, 0)
for u0 in rng.permutation(np.linspace(0, 1, 90, endpoint=False)):
    vs = np.linspace(0.0, 1.0, 6)
    pts3 = cen + (BASKET.pos(np.full(6, u0), vs) - cen) * 0.94
    radial = BASKET.pos(np.full(6, u0), vs) - cen - Basket.axis * ((vs - 0.5) * BH)[:, None]
    if float(radial[3] @ (E - pts3[3])) > 0:
        continue                                       # the near wall: its inside is turned from her
    up = -unit(radial)[:, 1]                           # the inside of the floor looks up
    c = [tone(PLASTIC * (SKY * (0.25 + 0.45 * max(w, 0)) + BOUNCE * 0.25), 1.9) for w in up]
    board.stroke(P(pts3), pl.but(width=8, opacity=0.85), c, wobble=0.3)
board.untape()
# two moulded ribs round the outside
for vv0 in (0.33, 0.66):
    us = np.linspace(0, 1, 80)
    pts3 = BASKET.pos(us, np.full(80, vv0))
    vis = np.sum((pts3 - cen - Basket.axis * ((vv0 - 0.5) * BH)) * (E - pts3), axis=1) > 0
    for seg in np.split(np.arange(80), np.where(np.diff(vis.astype(int)) != 0)[0] + 1):
        if vis[seg[0]] and len(seg) > 2:
            board.stroke(P(pts3[seg]), Brush(width=3, opacity=0.55, gap=0, thickness=0.3, taper=(0.1, 0.1)),
                         scale(basket_light(us[seg], np.full(len(seg), vv0)), 0.6), smooth=False)
# slots moulded in the side, two rows
SLOTS = [(u0 + 0.5 / 16 * row, vv0) for row, vv0 in enumerate((0.38, 0.68)) for u0 in np.linspace(0, 1, 16, endpoint=False)]
for u0, vv0 in SLOTS:
    q0, q1 = BASKET.pos(u0 - 0.012, vv0), BASKET.pos(u0 + 0.012, vv0)
    mid = (q0 + q1) / 2
    if float((mid - cen - Basket.axis * ((vv0 - 0.5) * BH)) @ (E - mid)) > 0:
        board.stroke([P(q0), P(q1)], Brush(width=5, opacity=0.85, gap=0, thickness=0.2, taper=(0.1, 0.1)),
                     tone(PLASTIC * SKY * 0.3, 1.9))
rim = P(BASKET.pos(np.linspace(0, 1, 60), np.full(60, 1.0)) + Basket.axis * 0.005)
board.stroke(rim, Brush(width=6, opacity=0.95, gap=0, thickness=0.9, pickup=0.1, taper=(0.0, 0.0)),
             scale(basket_light(np.linspace(0, 1, 60), np.full(60, 0.6)), 1.25), smooth=False)
board.dry()
board.stage("the basket, gone over")

# pegs, flung out of the basket and along the way the wind went
peg_c = mix((burnsi, 2), (black, 1.2), (ochre, 0.6))
for i in range(9):
    d = rng.uniform(0.2, 2.6)
    q = BC + Basket.axis * 0.3 + WD * d + SIDE * (rng.choice([-1, 1]) * rng.uniform(0.75, 1.2) + 0.2 * d)
    ang = rng.uniform(0, np.pi)
    e = v3(np.cos(ang), 0, np.sin(ang)) * 0.045
    a, b = P(q - e + v3(0, 0.012, 0)), P(q + e + v3(0, 0.012, 0))
    if TAKEN[int(np.clip((a[1] + b[1]) / 2, 0, H - 1)), int(np.clip((a[0] + b[0]) / 2, 0, W - 1))]:
        continue
    sa, sb = P(q - e - v3(L[0], 0, L[2]) * 0.03), P(q + e - v3(L[0], 0, L[2]) * 0.03)
    wpx = max(3.0, 0.02 * cam.f / (q[2] - E[2]))
    k = sun_at(*((a + b) / 2))
    if k > 0.9:
        board.stroke([sa, sb], Brush(width=wpx * 0.9, opacity=0.6, gap=0, thickness=0.05), roof_colour(*((sa + sb) / 2), 0.0) * 0.45)
    board.stroke([a, b], Brush(width=wpx, opacity=0.95, gap=0, thickness=0.9, taper=(0.05, 0.05)),
                 tone(peg_c * (SKY + SUN * 0.4 * k), 1.9))
for q in (v3(0.75, 0, 1.95), v3(0.45, 0, 2.35)):
    ang = rng.uniform(0, np.pi)
    e = v3(np.cos(ang), 0, np.sin(ang)) * 0.045
    a, b = P(q - e + v3(0, 0.012, 0)), P(q + e + v3(0, 0.012, 0))
    tip = v3(-L[0], 0, -L[2]) * (0.02 / L[1])
    wpx = 0.014 * cam.f / (q[2] - E[2])
    board.stroke([P(q - e + tip * 0.15), P(q + e + tip * 0.15)], Brush(width=wpx * 1.5, opacity=0.7, gap=0, thickness=0.05,
                 taper=(0.1, 0.1)), roof_colour(*P(q + tip * 0.15), 0.0) * 0.5)
    board.stroke([a, b], Brush(width=wpx, opacity=0.95, gap=0, thickness=1.0, taper=(0.05, 0.05)), tone(peg_c * (SKY + SUN * 0.3), 1.9))
    board.stroke([a + (0, -wpx * 0.3), b + (0, -wpx * 0.3)], Brush(width=wpx * 0.3, opacity=0.8, gap=0, thickness=0.6, taper=(0.1, 0.1)),
                 tone(peg_c * (SKY + SUN * 0.9), 1.9))
board.dry()
board.stage("pegs")

# =================================================================================================
# 6. The sheet the wind is taking. In the sun, the one thing on the roof that is: thick, in one go.
# =================================================================================================
def spill_light(u, v, gain=1.0):
    u, v = np.atleast_1d(u).astype(float), np.atleast_1d(v).astype(float)
    n = SPILL.normal(u, v, E)
    Q = SPILL.pos(u, v)
    x, y = P(Q).T
    k = np.clip(n @ L, 0, 1) * ON_SPILL[np.clip(y.astype(int), 0, H - 1), np.clip(x.astype(int), 0, W - 1)]
    c = COTTON * (SUN * k[:, None] * 1.5 + SKY * (0.6 + 0.4 * n[:, 1:2]) * 0.55 + BOUNCE * (1.4 - n[:, 1:2]))
    c = tone(c * gain, 2.0) * np.exp(rng.normal(0, 0.02, 3))
    return c if c.shape[0] > 1 else c[0]


lay_cloth(board, cam, SPILL, blk.but(width=20), lambda u, v: spill_light(u, v, 0.9), along="u", length=160,
          cover=4.0 * QUICK, wobble=0.8, margin=0.03, run=True)
hot = Brush(width=13, bristle=1.3, opacity=0.95, pickup=0.35, dryness=0.0, thickness=1.6, jitter=0.02, deplete=0.0004,
            taper=(0.2, 0.25), gap=0.01)


def facing_sun(u, v, k=0.42):
    return float(SPILL.normal(np.atleast_1d(u), np.atleast_1d(v), E)[0] @ L) > k


lay_cloth(board, cam, SPILL, hot.but(thickness=0.8), spill_light, along="u", length=130, cover=6.0 * QUICK, wobble=0.5,
          margin=0.02, run=True)
lay_cloth(board, cam, SPILL, hot, lambda u, v: spill_light(u, v, 1.15), along="u", length=90, cover=14.0 * QUICK,
          wobble=0.4, margin=0.0, run=True, where=facing_sun)
# the hem all round, a double thickness, a shade darker than the cloth beside it
for us, vs in [(np.linspace(0.1, 1, 30), np.zeros(30)), (np.linspace(0.1, 1, 30), np.ones(30)),
               (np.ones(20), np.linspace(0, 1, 20))]:
    pts = P(SPILL.pos(us, vs))
    board.stroke(pts, Brush(width=4, opacity=0.8, gap=0.05, pickup=0.3, thickness=0.6, taper=(0.1, 0.1)),
                 spill_light(us, vs, 0.75), smooth=False)
# where it lies on the screed its edge sits in a thin dark of its own
for vv0 in (0.0, 1.0):
    us = np.linspace(0.02, 0.97, 40)
    h = SPILL.pos(us, np.full(40, vv0))[:, 1]
    pts = P(SPILL.pos(us, np.full(40, vv0)) * v3(1, 0, 1))
    board.stroke(pts, Brush(width=4, opacity=0.7, gap=0.05, pickup=0.2, thickness=0.05, taper=(0.1, 0.1)),
                 roof_colour(pts[:, 0], pts[:, 1], 0.0) * 0.45, opacity=np.clip(1 - h / 0.08, 0, 1), smooth=False)
# and where the prop's shadow goes over the sheet, it goes over it in the cloth's own blue
over = np.array([SPILL_MASK[int(np.clip(y, 0, H - 1)), int(np.clip(x, 0, W - 1))] for x, y in prop_sh])
for seg in np.split(np.arange(len(prop_sh)), np.where(np.diff(over.astype(int)) != 0)[0] + 1):
    if over[seg[0]] and len(seg) > 1:
        q = prop_sh[seg[0] - (seg[0] > 0): seg[-1] + 2]
        board.stroke(q, Brush(width=6, bristle=1.0, opacity=0.95, gap=0.0, pickup=0.05, thickness=0.3, taper=(0.1, 0.1)),
                     tone(COTTON * (SKY * 0.55 + BOUNCE * 0.6), 2.0), smooth=False)
board.dry()
board.stage("the sheet the wind is taking")


finish(board, HERE, title="Grigal, the basket over", artist="carmela-zammit", year=1989,
       medium="Oil on cotton sheeting, red oxide ground", made="2026-11-12")
