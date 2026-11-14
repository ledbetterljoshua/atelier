"""Carmela Zammit - Tramuntana, taking in the pegs

The morning after the laundry stopped sending linen up. Eleven wires and nothing on them but the
pegs. There is no sheet to put between her and the sun, so for once it is at her back, low, and
everything that stands on the roof is laid out on the screed in front of her: the wires, hardly;
the pegs, as ticks hanging off them; and herself, one arm up to the line, with the north wind in
her skirt. No cloth on the board except what the shadow is wearing, and none under the paint: this
one is on the plywood lid of a linen hamper.
"""
import json
import os
import sys
import time
from pathlib import Path

import numpy as np
from PIL import Image

T0 = time.time()
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[3]))
sys.path.insert(0, str(HERE.parents[1]))

from engine import Board, Brush, hexc, mix, scale  # noqa: E402
from engine import ground as eground  # noqa: E402
from engine.paths import chaikin  # noqa: E402
from tools import Camera, SunFloor, band, crate_lid, cut, lay_field, lay_screen, tone, unit, v3  # noqa: E402

QUICK = float(os.environ.get("QUICK", "1.0"))
DIAG = os.environ.get("DIAG")

W, H = 1600, 1250
rng0 = np.random.default_rng(2005)
RED = hexc("#7a3021")
board = Board(W, H, RED, crate_lid(W, H, rng0), seed=2005, light=(-0.5, -0.8))
board.dries_off_board = False
board.relief_soft = 1.6
rng = board.rng
cam = Camera(W, H, 900, (0.0, 1.5, 0.0), pitch=-0.27, cy=360)
E, P = cam.eye, cam.P
UP = v3(0, 1, 0)

# --- tubes ---------------------------------------------------------------------------------------
white, ultra, prussian = hexc("#f7f4ec"), hexc("#20307f"), hexc("#14284a")
naples, ochre, rawsi, burnsi = hexc("#ecd398"), hexc("#c49236"), hexc("#a8692a"), hexc("#7d3418")
cadyel, cadorange, black, turq = hexc("#f2cc3a"), hexc("#e8782a"), hexc("#141210"), hexc("#2a9a9a")

# --- the roof, squared to the wires, not to her --------------------------------------------------
WDIR = unit(np.array([-0.60, 0.80]))            # the way the wires run, away from her and to the left
EU = v3(WDIR[0], 0, WDIR[1])                    # along the wires
ER = v3(WDIR[1], 0, -WDIR[0])                   # across them, to the right
UF, RR, PH, CW = 13.0, 4.6, 0.95, 0.24          # the end wall, the side wall, their height, the coping
U_NEAR, U_FAR, WIRE_Y, SAG = -4.5, 11.5, 1.95, 0.06


def roof(u, r, y=0.0):
    u, r, y = np.broadcast_arrays(np.asarray(u, float), np.asarray(r, float), np.asarray(y, float))
    return EU * u[..., None] + ER * r[..., None] + UP * y[..., None]


# --- the sun, behind her ---------------------------------------------------------------------------
EL = np.radians(23.0)
S2 = unit(np.array([0.35, 0.94]))               # the way the shadows go
L = v3(S2[0] * np.cos(EL), -np.sin(EL), S2[1] * np.cos(EL))    # the way the light travels
SUN = v3(1.0, 0.90, 0.74) * 2.3
SKY = v3(0.115, 0.225, 0.62) * 0.44               # a sky the north wind has scoured
T2 = np.array([S2[1], -S2[0]])                  # across the sun, to her right

# --- herself, as the sun sees her from behind: (sideways, height) --------------------------------
HAND = (0.30, 1.905)


def closed(p, rounds=2):
    p = np.asarray(p, float)
    return chaikin(np.vstack([p, p[:1]]), rounds)


def limb(pts, w):
    p = chaikin(np.asarray(pts, float), 2)
    return band(p, np.linspace(w[0], w[1], len(p)))


th = np.linspace(0, 2 * np.pi, 28, endpoint=False)
# the wind has the skirt: flat against the leg on the side it comes from, and the hem kicked out on the other
SKIRT = closed([(0.165, 1.0), (-0.165, 1.0), (-0.215, 0.88), (-0.25, 0.76), (-0.33, 0.65), (-0.44, 0.58), (-0.54, 0.56),
                (-0.46, 0.51), (-0.34, 0.53), (-0.23, 0.49), (-0.11, 0.52), (0.01, 0.49), (0.11, 0.52), (0.18, 0.50),
                (0.185, 0.66), (0.215, 0.88)], 2)
TORSO = closed([(-0.165, 0.99), (-0.175, 1.08), (-0.205, 1.20), (-0.235, 1.30), (-0.17, 1.365), (-0.06, 1.39), (0.06, 1.39),
                (0.17, 1.365), (0.235, 1.30), (0.205, 1.20), (0.175, 1.08), (0.165, 0.99)], 2)
HEAD = np.stack([0.112 * np.cos(th), 1.478 + 0.105 * np.sin(th)], 1)
SCARF = closed([(-0.08, 1.42), (-0.20, 1.45), (-0.30, 1.42), (-0.23, 1.395), (-0.31, 1.34), (-0.19, 1.36), (-0.07, 1.37)], 1)
ARM_UP = limb([(0.20, 1.31), (0.35, 1.44), (0.41, 1.60), (0.34, 1.78), HAND], (0.105, 0.065))
FIST = np.stack([HAND[0] + 0.045 * np.cos(th), HAND[1] - 0.02 + 0.05 * np.sin(th)], 1)
PEG_IN_HAND = np.array([(HAND[0] - 0.045, HAND[1] + 0.0), (HAND[0] - 0.03, HAND[1] + 0.0), (HAND[0] - 0.05, HAND[1] - 0.085),
                        (HAND[0] - 0.065, HAND[1] - 0.085)])
ARM_HIP = limb([(-0.21, 1.31), (-0.33, 1.20), (-0.42, 1.09), (-0.33, 1.00), (-0.20, 0.95)], (0.10, 0.07))
LEGS = [np.array([(-0.15, 0.0), (-0.07, 0.0), (-0.045, 0.30), (-0.05, 0.56), (-0.15, 0.56), (-0.155, 0.30)]),
        np.array([(0.05, 0.0), (0.13, 0.0), (0.135, 0.30), (0.13, 0.56), (0.03, 0.56), (0.025, 0.30)])]
HER = [SKIRT, TORSO, HEAD, SCARF, ARM_UP, FIST, PEG_IN_HAND, ARM_HIP] + LEGS
FOOT = np.array([0.0, 0.0])

# --- the wires, and the pegs she has not got to yet ------------------------------------------------
hand_xz = FOOT + HAND[0] * T2
R_HAND, U_HAND = float(hand_xz @ ER[[0, 2]]), float(hand_xz @ EU[[0, 2]])
N_WIRE, J_HERS = 11, 6
WIRE_R = R_HAND + (np.arange(N_WIRE) - J_HERS) * 0.5


def wire(j, u):
    u = np.asarray(u, float)
    mid, half = (U_NEAR + U_FAR) / 2, (U_FAR - U_NEAR) / 2
    return roof(u, WIRE_R[j], WIRE_Y - SAG * (1 - ((u - mid) / half) ** 2))


WINDX = -ER                                     # the tramuntana comes over the side wall, from her right
prng = np.random.default_rng(71)
PEGS = []                                       # (top, tip)
for j in range(N_WIRE):
    u = (U_HAND + 0.5 if j == J_HERS else U_NEAR + 0.3)   # her own line is bare behind her hand + prng.uniform(0.0, 0.5)
    while u < U_FAR - 0.25:
        twins = 1 if prng.random() > 0.3 else 2
        for k in range(twins):
            top = wire(j, u + 0.045 * k)
            lean = np.clip(prng.normal(0.75, 0.3), 0.05, 2.2)       # how far the wind has swung it round the wire
            PEGS.append((top, top + 0.078 * (WINDX * np.sin(lean) - UP * np.cos(lean))))
        u += prng.uniform(0.38, 1.0) if prng.random() > 0.15 else prng.uniform(1.2, 2.0)
POST_R = [WIRE_R[0] - 0.22, WIRE_R[5] + 0.25, WIRE_R[-1] + 0.22]
POST_W, RAIL_W = 0.06, 0.05


class Tub:
    """The basket, on the roof a step ahead of her: u round it, v up the side."""

    def __init__(self, c, r0, r1, h):
        self.c, self.r0, self.r1, self.h = v3(*c), r0, r1, h

    def pos(self, u, v):
        u, v = np.broadcast_arrays(np.asarray(u, float), np.asarray(v, float))
        r = self.r0 + (self.r1 - self.r0) * v
        a = 2 * np.pi * u
        return self.c + np.stack([r * np.cos(a), v * self.h, r * np.sin(a)], -1)

    def out(self, u):
        a = 2 * np.pi * np.asarray(u, float)
        return unit(np.stack([np.cos(a), np.full_like(a, -0.15), np.sin(a)], -1))


TUB = Tub((-0.95, 0.0, 2.25), 0.24, 0.30, 0.30)

# --- everything laid on the roof, once ---------------------------------------------------------------
# the prop, not wanted, lying along the way the wires run
PROP_A, PROP_B = cam.on_ground(np.float64(60.0), np.float64(985.0)), cam.on_ground(np.float64(640.0), np.float64(1120.0))
PROP_W = 0.045
PROP_SIDE = unit(np.cross(UP, PROP_B - PROP_A)) * PROP_W / 2
us = np.linspace(U_NEAR, U_FAR, 17)
uu = np.linspace(0, 1, 40, endpoint=False)


def lay_out(wires=True, pegs=True, things=True):
    m = SunFloor(L, a=(-9.0, 13.0), b=(-1.0, 22.0))
    if wires:
        # she gives the wires more than they have: a wire that high throws a tenth of a shadow
        m.threads([(wire(j, a), wire(j, b)) for j in range(N_WIRE) for a, b in zip(us[:-1], us[1:])], 0.003, gain=WIRE_GAIN)
    if pegs:
        m.threads(PEGS, 0.013, gain=PEG_GAIN)
    if not things:
        return m.settle()
    for u_rail in (U_NEAR, U_FAR):
        a, b = roof(u_rail, POST_R[0], WIRE_Y + 0.02), roof(u_rail, POST_R[-1], WIRE_Y + 0.02)
        m.solid([a - EU * RAIL_W / 2, a + EU * RAIL_W / 2, b + EU * RAIL_W / 2, b - EU * RAIL_W / 2], y=WIRE_Y)
        for r in POST_R:
            m.standing(roof(u_rail, r)[[0, 2]], [[(-POST_W / 2, 0), (POST_W / 2, 0), (POST_W / 2, WIRE_Y), (-POST_W / 2, WIRE_Y)]])
    m.standing(FOOT, HER)
    m.solid(np.concatenate([TUB.pos(uu, 0.0), TUB.pos(uu, 1.0)]), y=0.25)
    return m.settle()


WIRE_GAIN, PEG_GAIN = 7.5, 1.5
sun, bodies, wires_only, hung = lay_out(), lay_out(wires=False, pegs=False), lay_out(pegs=False, things=False), lay_out(things=False)

# --- what is behind each point of the board ---------------------------------------------------------
Yp, Xp = np.mgrid[0:H, 0:W].astype(np.float64) + 0.5
D = cam.ray(Xp, Yp)


def in_roof(v):
    return np.stack([v @ EU, v @ ER, v[..., 1]], -1)


Dr, Er = in_roof(D), in_roof(E)
TBEST = np.full((H, W), np.inf)
KIND = np.zeros((H, W), dtype=np.int8)          # 0 sky, 1 screed, 2 side wall, 3 end wall, 4 coping


def strike(axis, val, ok, kind):
    global TBEST, KIND
    t = (val - Er[axis]) / np.where(np.abs(Dr[..., axis]) < 1e-9, 1e-9, Dr[..., axis])
    q = Er + Dr * t[..., None]
    hit = (t > 0.05) & (t < TBEST) & ok(q)
    TBEST = np.where(hit, t, TBEST)
    KIND = np.where(hit, kind, KIND).astype(np.int8)


strike(2, 0.0, lambda q: (q[..., 0] < UF) & (q[..., 1] < RR), 1)
strike(1, RR, lambda q: (q[..., 2] >= 0) & (q[..., 2] <= PH) & (q[..., 0] <= UF), 2)
strike(0, UF, lambda q: (q[..., 2] >= 0) & (q[..., 2] <= PH) & (q[..., 1] <= RR + CW), 3)
strike(2, PH, lambda q: (q[..., 1] >= RR) & (q[..., 1] <= RR + CW) & (q[..., 0] <= UF + CW), 4)
strike(2, PH, lambda q: (q[..., 0] >= UF) & (q[..., 0] <= UF + CW) & (q[..., 1] <= RR + CW), 4)
Q = E + D * np.where(np.isfinite(TBEST), TBEST, 1.0)[..., None]
SUNF = np.where(KIND > 0, sun.at(Q), 1.0).astype(np.float32)
LINEF = np.where(KIND > 0, wires_only.at(Q), 1.0).astype(np.float32)
HUNGF = np.where(KIND > 0, hung.at(Q), 1.0).astype(np.float32)
BODY = np.where(KIND > 0, 1.0 - bodies.at(Q), 0.0).astype(np.float32)       # 1 inside the shadow of something with body
COS = np.array([0.0, np.sin(EL), float(L @ ER), float(L @ EU), np.sin(EL)])[KIND]     # how square the sun lands
DIST = np.where(KIND > 0, TBEST, 30.0)
QU, QR = Q @ EU, Q @ ER

if DIAG:
    g = (SUNF * (0.35 + 0.65 * COS / COS.max()) * (KIND > 0) + 0.15 * (KIND == 0)) ** 0.5
    Image.fromarray((np.clip(g, 0, 1) * 255).astype(np.uint8)).save(DIAG)
    print("diag", round(time.time() - T0, 1))
    sys.exit()

# --- the stuff of the roof ------------------------------------------------------------------------
DEFFUN = scale(mix((white, 3), (naples, 1.3), (burnsi, 0.21), (ochre, 0.1)), 0.76)   # lime and crushed pot: it is pink
WASH = scale(mix((white, 4), (naples, 1.0), (ochre, 0.06)), 0.62)                    # limewash on the walls
RUSTC = mix((RED, 2), (ochre, 1), (white, 0.6))
from scipy.ndimage import map_coordinates  # noqa: E402

_n = np.random.default_rng(5)
_f1, _f2 = eground.fbm(512, 512, _n, base=7, octaves=5), eground.fbm(512, 512, _n, base=4, octaves=4)


def _world(f, scale_m=26.0):
    return map_coordinates(f, [(QU + 8) / scale_m * 511 % 511, (QR + 10) / scale_m * 511 % 511], order=1).astype(np.float32)


NV, NW = _world(_f1) - 0.5, _world(_f2) - 0.5            # lighter and darker; warmer and cooler
_bay = np.random.default_rng(9).normal(0, 1, (16, 16))
BAY = _bay[np.clip((QU + 9) // 3.0, 0, 15).astype(int), np.clip((QR + 12) // 3.2, 0, 15).astype(int)].astype(np.float32)
# where the iron posts weep down the fall of the roof, and the foot of the walls, where the wet sits
RUST = np.zeros((H, W), dtype=np.float32)
for u_rail in (U_FAR,):
    for r in POST_R:
        du, dr = QU - u_rail, QR - r
        RUST += np.exp(-(dr / (0.07 + 0.05 * np.clip(-du, 0, 3))) ** 2) * np.exp(-np.clip(-du, 0, 9) / 1.2) * (du < 0.08) \
            + np.exp(-(du ** 2 + dr ** 2) / 0.02)
RUST = np.clip(RUST, 0, 1) * (KIND == 1)
FOOTW = np.where(KIND == 1, np.exp(-np.minimum(RR - QR, UF - QU) / 0.12), 0.0) \
    + np.where((KIND == 2) | (KIND == 3), np.exp(-Q[..., 1] / 0.10), 0.0)
BOUNCE = DEFFUN * SUN * np.sin(EL) * 0.22
HORIZON_Y = float(P(E + v3(0, 0, 500.0))[1])


def lookup(x, y):
    xi = np.clip(np.asarray(x).astype(int), 0, W - 1)
    yi = np.clip(np.asarray(y).astype(int), 0, H - 1)
    return yi, xi


def sky_colour(x, y):
    d = cam.ray(np.asarray(x, float), np.asarray(y, float))
    el = np.arcsin(np.clip(d[..., 1], -1, 1))
    t = np.clip((el + 0.02) / 0.32, 0, 1) ** 0.75
    low, high = v3(0.21, 0.35, 0.62), v3(0.028, 0.085, 0.37)       # away from the sun, and washed
    return np.clip(np.exp(np.log(low) * (1 - t[..., None]) + np.log(high) * t[..., None]), 0.004, 0.97)


def ground_colour(x, y, vary=0.02, open_sun=False, k=1.0, fld=None):
    """The screed or the wall behind board point (x, y). With open_sun, as if nothing stood on the roof."""
    x, y = np.atleast_1d(x), np.atleast_1d(y)
    i = lookup(x, y)
    kind = KIND[i]
    sf = np.where(kind > 0, 1.0 if open_sun else (SUNF if fld is None else fld)[i], 0.0)
    wall = (kind == 2) | (kind == 3)
    alb = np.where(wall[:, None], WASH, DEFFUN) * np.exp(0.22 * NV[i] + 0.05 * BAY[i] * (kind == 1))[:, None]
    alb = alb * np.exp(v3(0.10, 0.0, -0.12) * NW[i][:, None])
    alb = alb * (1 - 0.22 * np.clip(FOOTW[i], 0, 1))[:, None] * np.where((kind == 3)[:, None], v3(0.80, 0.81, 0.86), 1.0)
    rr = RUST[i][:, None]
    alb = alb * (1 - rr) + RUSTC * rr
    amb = np.where(wall[:, None], SKY * 0.62 + BOUNCE, SKY)
    c = alb * (amb + SUN * (COS[i] * sf)[:, None]) * k
    c = np.where((kind == 0)[:, None], sky_colour(x, y), tone(c, 1.9))
    c = c * np.exp(rng.normal(0, vary, 3))
    return c if c.shape[0] > 1 else c[0]


def on_board(direction):
    """fn(x, y) -> the angle on the board of a level direction (x, z) lying on the roof at that point."""
    d3 = v3(direction[0], 0, direction[1])

    def f(x, y):
        q = cam.on_ground(np.float64(x), np.float64(min(max(y, HORIZON_Y + 8), H + 200)))
        a, b = P(q), P(q + d3 * 0.05)
        return float(np.arctan2(b[1] - a[1], b[0] - a[0]))
    return f


def seen(pts3, margin=30):
    """A run of points in the world as a run on the board, only where it is in front of her and on it."""
    pts3 = np.atleast_2d(pts3)
    d = pts3 - E
    zc = d[:, 1] * cam.sp + d[:, 2] * cam.cp
    p = P(pts3)
    ok = (zc > 0.4) & (p[:, 0] > -margin) & (p[:, 0] < W + margin) & (p[:, 1] > -margin) & (p[:, 1] < H + margin)
    return p[ok], zc[ok]


def land(q):
    """Where the shadow of a point lands: on the screed, or on the side wall or the end wall if they are in the way."""
    q = np.atleast_2d(np.asarray(q, float))
    t = q[:, 1] / -L[1]
    lr, lu = float(L @ ER), float(L @ EU)
    t = np.minimum(t, np.where(lr > 0, (RR - q @ ER) / lr, np.inf))
    t = np.minimum(t, np.where(lu > 0, (UF - q @ EU) / lu, np.inf))
    return q + L * np.maximum(t, 0)[:, None] - L * 0.004


IS_FLOOR, IS_SIDE, IS_END, IS_COPE = (KIND == 1), (KIND == 2), (KIND == 3), (KIND == 4)
wall_top = np.where((KIND > 0).any(axis=0), (KIND > 0).argmax(axis=0), H)          # first row that is not sky, per column

# =================================================================================================
# 1. The sky, the strip of it, wet, from the top down, over the red.
# =================================================================================================
scrub = Brush(width=110, bristle=2.6, opacity=0.97, pickup=0.08, dryness=0.0, thickness=0.05, jitter=0.03, deplete=0.0005)
sky_b = Brush(width=38, bristle=2.0, opacity=0.7, pickup=0.4, dryness=0.0, thickness=0.06, jitter=0.025,
              deplete=0.0004, taper=(0.15, 0.2))
sky_bot = float(wall_top.max()) + 12
region = (-60, -40, W + 60, sky_bot)
lay_screen(board, region, scrub, lambda x, y: scale(sky_colour(x, y), 0.9), angle=0.06, length=520, cover=3.5 * QUICK, wobble=8)
lay_screen(board, region, sky_b, lambda x, y: sky_colour(x, y) * np.exp(rng.normal(0, 0.03, 3)), angle=0.06,
           length=360, cover=6.5 * QUICK, wobble=6)
# the wind combs it: a few long dry drags that let the red back through, thin
comb = Brush(width=60, bristle=1.6, opacity=0.5, pickup=0.5, dryness=0.75, thickness=0.05, jitter=0.03, deplete=0.001, gap=0.2)
for _ in range(int(9 * QUICK) + 1):
    y0 = rng.uniform(5, sky_bot * 0.75)
    x0 = rng.uniform(-100, W - 300)
    xs = np.linspace(x0, x0 + rng.uniform(400, 800), 6)
    board.stroke(np.stack([xs, y0 + 0.06 * (xs - x0) + rng.normal(0, 4, 6)], 1), comb, sky_colour(xs.mean(), y0) * 1.12, wobble=3)

# Qormi, standing up over the end wall. In this air it is near, and hard, and the sun is full on it.
dx = 265.0
dy = float(wall_top[int(dx)])
stone_lit = tone(WASH * v3(1.0, 0.93, 0.80) * (SKY * 0.5 + SUN * 0.62), 1.9)
stone_shd = tone(WASH * v3(1.0, 0.93, 0.80) * (SKY * 0.8 + SUN * 0.16), 1.9)
dome_b = Brush(width=7, bristle=1.1, opacity=0.92, pickup=0.25, thickness=0.25, jitter=0.02, gap=0.02, taper=(0.05, 0.1))
RX, RY, DRUM = 34.0, 30.0, 13.0
half = mix(stone_lit, stone_shd)
board.tape([(dx - RX - 6, dy + 2), (dx + RX + 6, dy + 2), (dx + RX + 6, dy - 90), (dx - RX - 6, dy - 90)])
for x0, x1, c in ((dx - RX - 3, dx + 6, stone_lit), (dx + 2, dx + RX + 3, half)):                         # the drum
    for yy in (dy - 4, dy - DRUM + 4):
        board.stroke([(x0, yy), (x1, yy)], dome_b.but(width=10, taper=(0.0, 0.0), pickup=0.0), c)
for a in np.linspace(0.0, 1.0, 22):                           # the shell, rib by rib from the sun's side round
    x_edge = dx + RX * np.cos(np.pi * (1 - a))
    tt = np.linspace(0, 1, 6)
    xs = x_edge + (dx - x_edge) * tt ** 1.5
    ys = dy - DRUM - RY * np.sqrt(np.clip(1 - ((xs - dx) / RX) ** 2 * (1 - tt) ** 0.0, 0, 1)) * (0.25 + 0.75 * tt ** 0.6) - 1
    c = mix((stone_lit, 1.02 - a ** 1.6), (stone_shd, 0.02 + a ** 1.6))
    board.stroke(np.stack([xs, ys], 1), dome_b.but(width=8, pickup=0.1), c, wobble=0.2)
board.untape()
top_y = dy - DRUM - RY
board.stroke([(dx, top_y + 3), (dx, top_y - 14)], dome_b.but(width=8, taper=(0, 0)), stone_lit)           # the lantern
board.stroke([(dx + 3, top_y + 3), (dx + 3, top_y - 13)], dome_b.but(width=2.5, taper=(0, 0)), stone_shd)
board.stroke([(dx, top_y - 13), (dx, top_y - 23)], dome_b.but(width=2, taper=(0, 0)), stone_shd)
board.dry()
board.stage("the sky, combed")

# =================================================================================================
# 2. The roof and its two walls, as if nothing at all stood on it.
# =================================================================================================
deck = Brush(width=36, bristle=1.8, opacity=0.86, pickup=0.5, dryness=0.0, thickness=0.14, jitter=0.04, deplete=0.0006)
across, along_w, throw = on_board(ER[[0, 2]]), on_board(EU[[0, 2]]), on_board(S2)
floor_top = float(np.where(IS_FLOOR.any(axis=1))[0].min())
bare = lambda x, y: ground_colour(x, y, 0.02, open_sun=True)  # noqa: E731
board.tape_where((KIND > 0).astype(np.float32), feather=0.6)
lay_screen(board, (-150, floor_top - 80, W + 150, H + 40), scrub.but(width=100), lambda x, y: scale(bare(x, y), 0.9),
           angle=0.0, angle_jitter=0.05, length=460, cover=2.5 * QUICK, wobble=3)
cut(board, IS_FLOOR, feather=0.7)
bands = np.linspace(floor_top - 6, H + 40, 8)
for y0, y1 in zip(bands[:-1], bands[1:]):
    zk = float(np.clip((((y0 + y1) / 2) - floor_top) / (H - floor_top), 0.1, 1.0))
    lay_screen(board, (-150, y0, W + 150, y1), deck.but(width=9 + 34 * zk), bare, angle=across, angle_jitter=0.05,
               length=80 + 330 * zk, cover=5.5 * QUICK, wobble=0.5 + 1.8 * zk)
board.dry()
for y0, y1 in zip(bands[:-1], bands[1:]):
    zk = float(np.clip((((y0 + y1) / 2) - floor_top) / (H - floor_top), 0.1, 1.0))
    lay_screen(board, (-150, y0, W + 150, y1), deck.but(width=8 + 26 * zk, opacity=0.93, pickup=0.3), bare, angle=across,
               angle_jitter=0.05, length=70 + 280 * zk, cover=4.0 * QUICK, wobble=0.5 + 1.5 * zk)
# near her the big brush again, broken, warmer and cooler in turn, the way the floats left it
lay_screen(board, (-100, H * 0.45, W + 100, H + 40), deck.but(width=40, opacity=0.5, thickness=0.3, pickup=0.5),
           lambda x, y: bare(x, y) * np.exp(rng.normal(0, 0.02) + v3(0.02, 0, -0.03) * rng.normal(0, 1.0)),
           angle=along_w, angle_jitter=0.07, length=280, cover=1.3 * QUICK, wobble=2.5)
for msk, ang, wd in ((IS_SIDE, along_w, 15), (IS_END, across, 9)):
    cut(board, msk, feather=0.7)
    ys_, xs_ = np.where(msk)
    lay_screen(board, (xs_.min() - 30, ys_.min() - 6, xs_.max() + 30, ys_.max() + 6), deck.but(width=wd, thickness=0.22),
               bare, angle=ang, angle_jitter=0.03, length=150, cover=9.0 * QUICK, wobble=0.6, where=lambda x, y: msk[lookup(x, y)])
cut(board, IS_COPE, feather=0.5)
ys_, xs_ = np.where(IS_COPE)
lay_screen(board, (xs_.min() - 30, ys_.min() - 4, xs_.max() + 30, ys_.max() + 4), deck.but(width=7, thickness=0.3),
           lambda x, y: bare(x, y) * 0.93, angle=lambda x, y: along_w(x, y) if x > 520 else across(x, y), angle_jitter=0.02,
           length=120, cover=9.0 * QUICK, wobble=0.4, where=lambda x, y: IS_COPE[lookup(x, y)])
board.untape()
board.dry()
# one dry drag over the near roof, lighter, so the lid's own grain comes up through the screed
cut(board, IS_FLOOR, feather=0.7)
lay_screen(board, (-100, H * 0.35, W + 100, H + 40), deck.but(width=46, opacity=0.5, thickness=0.2, pickup=0.0, dryness=0.72, gap=0.15),
           lambda x, y: bare(x, y) * 1.07, angle=across, angle_jitter=0.05, length=330, cover=1.1 * QUICK, wobble=2.0)
board.untape()
board.dry()
# where wall meets screed, and the lip of the coping
edge = Brush(width=3, bristle=0.9, opacity=0.8, gap=0.0, pickup=0.2, thickness=0.05, taper=(0.02, 0.02))
for a, b in ((roof(-3.0, RR), roof(UF, RR)), (roof(UF, RR), roof(UF, -14.0))):
    for h, kk, wd in ((0.012, 0.45, 3.6), (PH - 0.045, 0.7, 2.2)):
        q, zc = seen(np.linspace(a, b, 200) + UP * h - (ER if a is not None and abs((b - a) @ EU) > 1 else EU) * 0.004)
        if len(q) > 2:
            board.stroke(q, edge.but(width=max(1.3, wd * 4.0 / zc.mean() ** 0.7)), ground_colour(q[:, 0], q[:, 1] + 2, 0.01, open_sun=True, k=kk),
                         smooth=False, wobble=0.3)
board.dry()
board.stage("the roof and the walls, all in the sun")

# the joints between the bays, and the line where wall meets screed
jnt = Brush(width=3, bristle=1.0, opacity=0.5, gap=0.1, pickup=0.3, thickness=0.05, taper=(0.1, 0.1))


def roof_line(a, b, brush, k=0.6, n=240, open_sun=True, wobble=0.5):
    p, zc = seen(np.linspace(a, b, n) + UP * 0.002)
    if len(p) > 2:
        board.stroke(p, brush.but(width=max(1.4, brush.width * 3.0 / zc.mean() ** 0.8)),
                     ground_colour(p[:, 0], p[:, 1], 0.02, open_sun=open_sun, k=k), wobble=wobble, smooth=False)


cut(board, IS_FLOOR, feather=0.5)
for u in np.arange(-9 + 3.0, UF, 3.0):
    roof_line(roof(u, -8), roof(u, RR), jnt)
board.untape()
board.dry()

# =================================================================================================
# 3. What stands on it, laid on it: the wires hardly, the pegs, and herself.
# =================================================================================================
shade_b = Brush(width=22, bristle=1.6, opacity=0.93, pickup=0.0, dryness=0.0, thickness=0.015, jitter=0.03, deplete=0.0005,
                taper=(0.15, 0.2))
DARK = (1.0 - SUNF) * (KIND > 0)
# first the wires: one long faint pull each, the width of what a wire two metres up can throw
lines_b = Brush(width=6, bristle=1.1, opacity=0.88, pickup=0.0, dryness=0.0, thickness=0.01, jitter=0.02, gap=0.03,
                taper=(0.02, 0.05), deplete=0.0001)
board.tape_where((KIND > 0).astype(np.float32), feather=0.5)
for j in range(N_WIRE):
    p, zc = seen(land(wire(j, np.linspace(U_NEAR, U_FAR, 400))), margin=10)
    if len(p) < 3:
        continue
    # break the pull where the run on the board jumps (floor to wall)
    brk = np.where(np.hypot(*np.diff(p, axis=0).T) > 40)[0]
    for seg, zs in zip(np.split(p, brk + 1), np.split(zc, brk + 1)):
        if len(seg) < 3:
            continue
        for _ in range(2):
            wpx = float(np.clip(0.06 * cam.f / zs.mean(), 2.2, 22))
            on_wall = KIND[lookup(*seg[len(seg) // 2])] > 1          # on the wall she leans on them a little: it is nearly white
            board.stroke(seg + rng.normal(0, 0.6, 2), lines_b.but(width=wpx),
                         ground_colour(seg[:, 0], seg[:, 1], 0.01, fld=LINEF, k=0.9 if on_wall else 1.0),
                         wobble=0.4, smooth=False)
board.dry()
board.stage("the wires, what there is of them")

# then the pegs: a touch each, pulled the way the sun throws it
tick = Brush(width=5, bristle=1.2, opacity=0.8, pickup=0.0, thickness=0.01, jitter=0.02, gap=0.0, loadvar=0.05, taper=(0.25, 0.3))
for top, tip in PEGS:
    ends = land(np.array([tip, top]))
    p, zc = seen(ends + (ends[1] - ends[0]) * np.array([[-0.12], [0.08]]), margin=0)
    if len(p) < 2:
        continue
    along = p[0] + (p[1] - p[0]) * np.linspace(0.15, 0.85, 7)[:, None]
    mid = along[np.argmin(HUNGF[lookup(along[:, 0], along[:, 1])])]
    wpx = float(np.clip(0.03 * cam.f / zc.mean(), 1.8, 16))
    board.stroke(p, tick.but(width=wpx), ground_colour(mid[0], mid[1], 0.02, fld=HUNGF), wobble=0.0)
board.dry()
board.stage("the pegs, as ticks")

# then everything that has body: the posts, the basket's, hers. Cut where the light cuts, brushed the way it is thrown.
cut(board, BODY * IS_FLOOR, at=0.04, soft=0.06, feather=0.8)
bands = np.linspace(floor_top - 6, H + 40, 6)
for y0, y1 in zip(bands[:-1], bands[1:]):
    zk = float(np.clip((((y0 + y1) / 2) - floor_top) / (H - floor_top), 0.1, 1.0))
    lay_field(board, (-60, y0, W + 60, y1), shade_b.but(width=4 + 20 * zk ** 1.4), lambda xs, ys: ground_colour(xs, ys, 0.02),
              angle=throw, length=30 + 140 * zk, cover=10.0 * QUICK, wobble=0.6, angle_jitter=0.05,
              where=lambda x, y: BODY[lookup(x, y)] > 0.02)
cut(board, BODY * (IS_SIDE | IS_END), at=0.04, soft=0.06, feather=0.6)
lay_field(board, (-60, 0, W + 60, floor_top + 320), shade_b.but(width=6), lambda xs, ys: ground_colour(xs, ys, 0.02),
          angle=-np.pi / 2, length=40, cover=7.0 * QUICK, wobble=0.3, angle_jitter=0.05,
          where=lambda x, y: (BODY * (IS_SIDE | IS_END))[lookup(x, y)] > 0.02)
board.untape()
board.dry()
board.stage("the shadows with body: herself")

# the prop, weathered grey, lying where it was put down; its shadow is one pull laid beside it
reach = PROP_W * 0.5 * np.cos(EL) / np.sin(EL)          # she keeps it narrower than it was: it is a pole, not a plank
sh, zc = seen(np.linspace(PROP_A, PROP_B, 30) + v3(S2[0], 0, S2[1]) * (PROP_W * 0.5 + reach * 0.5))
for _ in range(2):
    board.stroke(sh, Brush(width=float(reach * cam.f / zc.mean()), bristle=1.3, opacity=0.97, gap=0.0, pickup=0.0, thickness=0.01,
                           taper=(0.02, 0.02), jitter=0.02, loadvar=0.05),
                 ground_colour(sh[:, 0], sh[:, 1], 0.01, fld=np.zeros((H, W), np.float32)), smooth=False, wobble=0.4)
prop_c = mix((white, 2), (rawsi, 1), (black, 0.5), (ultra, 0.2))
pp, zc = seen(np.linspace(PROP_A, PROP_B, 30) + UP * PROP_W * 0.6)
pwid = PROP_W * cam.f / zc
for off, kk, wd in ((0.0, 0.62, 1.0), (-0.22, 0.95, 0.45), (0.34, 0.25, 0.3)):
    nrm = np.gradient(pp, axis=0)
    nrm = np.stack([-nrm[:, 1], nrm[:, 0]], 1) / (np.linalg.norm(nrm, axis=1, keepdims=True) + 1e-9)
    if nrm[len(nrm) // 2, 1] > 0:
        nrm = -nrm                                          # off < 0 is the top of it, toward the sky
    board.stroke(pp - nrm * (off * pwid)[:, None], Brush(width=float(pwid.mean() * wd), bristle=1.0, opacity=0.95, gap=0.02, pickup=0.1,
                 thickness=0.5, taper=(0.0, 0.0), jitter=0.04), tone(prop_c * (SKY + SUN * kk * 0.6), 1.9), smooth=False, wobble=0.3)
# the notch at its head, where the wire sat
for sgn in (-1, 1):
    board.stroke([P(PROP_B + UP * PROP_W * 0.5), P(PROP_B + unit(PROP_B - PROP_A) * 0.10 + PROP_SIDE * sgn * 1.8 + UP * PROP_W * 0.5)],
                 Brush(width=float(pwid[-1] * 0.5), opacity=0.95, gap=0, thickness=0.5, taper=(0.0, 0.1)), tone(prop_c * (SKY + SUN * 0.4), 1.9))
board.dry()

# =================================================================================================
# 4. What stands up: the rail and its posts at the far end, in Toni's red; the wires; the pegs.
# =================================================================================================
fine = Brush(width=3, bristle=0.9, opacity=0.93, pickup=0.0, thickness=0.7, jitter=0.02, gap=0.0, taper=(0.0, 0.0), deplete=0.0)
oxide_lit = tone(RED * 1.25 * (SKY * 0.7 + SUN * 0.55), 1.9)
oxide_shd = tone(RED * 1.25 * (SKY * 0.9 + SUN * 0.06), 1.9)
for r in POST_R:
    foot, top = roof(U_FAR, r, 0.0), roof(U_FAR, r, WIRE_Y + 0.03)
    p, zc = seen(np.linspace(foot, top, 12))
    if len(p) > 2:
        wpx = max(3.0, POST_W * cam.f / zc.mean())
        board.stroke(p, fine.but(width=wpx), oxide_lit, smooth=False)
        board.stroke(p + (wpx * 0.3, 0), fine.but(width=max(1.2, wpx * 0.35)), oxide_shd, smooth=False)
p, zc = seen(np.linspace(roof(U_FAR, POST_R[0] - 0.1, WIRE_Y + 0.02), roof(U_FAR, POST_R[-1] + 0.1, WIRE_Y + 0.02), 40))
if len(p) > 2:
    board.stroke(p, fine.but(width=max(2.5, RAIL_W * cam.f / zc.mean())), oxide_lit, smooth=False)
board.dry()

zinc = tone(mix((white, 3), (ultra, 0.25), (black, 0.25)) * (SKY * 0.8 + SUN * 0.5), 1.9)
zinc_shd = tone(mix((white, 3), (ultra, 0.25), (black, 0.25)) * (SKY * 0.9), 1.9)
for j in range(N_WIRE):
    p, zc = seen(wire(j, np.linspace(U_NEAR, U_FAR, 300)), margin=60)
    if len(p) < 3:
        continue
    wn, wf = float(np.clip(0.0045 * cam.f / zc.min(), 1.3, 4.0)), float(np.clip(0.0045 * cam.f / zc.max(), 1.2, 4.0))
    board.stroke(p + (0, 0.8), fine.but(width=(wn + wf) / 2, opacity=0.7, thickness=0.2), zinc_shd, smooth=False)
    board.stroke(p, fine.but(width=(wn + wf) / 2 * 0.8, thickness=0.5), zinc, smooth=False)
board.dry()
board.stage("the rail in Toni's red, and the wires")

# the pegs, far ones first: the only thick paint in it
wood_lit = tone(mix((naples, 3), (ochre, 1.0), (white, 1.5), (rawsi, 0.3)) * (SKY * 0.6 + SUN * 0.62), 1.9)
wood_shd = tone(mix((naples, 2), (rawsi, 1.5), (burnsi, 0.5)) * (SKY * 1.0 + SUN * 0.08), 1.9)
order = np.argsort([-(t[0] - E) @ v3(0, cam.sp, cam.cp) for t in PEGS])
n_pegs = 0
for i in order:
    top, tip = PEGS[i]
    p, zc = seen(np.array([top + (top - tip) * 0.3, tip]), margin=0)
    if len(p) < 2:
        continue
    wpx = float(np.clip(0.02 * cam.f / zc.mean(), 1.8, 9.0))
    k = np.exp(rng.normal(0, 0.08))
    board.stroke(p, fine.but(width=wpx, thickness=1.6, opacity=0.97), wood_lit * k * np.exp(rng.normal(0, 0.03, 3)))
    if wpx > 2.6:
        board.stroke(p + (wpx * 0.34, 0.4), fine.but(width=wpx * 0.3, thickness=0.4), wood_shd)
    n_pegs += 1
board.dry()
board.stage("the pegs")

# =================================================================================================
# 5. The basket, a step ahead of her, with what she has taken in so far.
# =================================================================================================
from scipy.spatial import ConvexHull  # noqa: E402

PLASTIC = mix((turq, 2.4), (ultra, 0.25), (white, 2.4), (rawsi, 0.5), (burnsi, 0.25))
TO_SUN = -L


def tub_light(u, v, inside=False):
    u, v = np.atleast_1d(u).astype(float), np.atleast_1d(v).astype(float)
    n = TUB.out(u) * (-1 if inside else 1)
    cosn = np.clip(n @ TO_SUN, 0, 1)
    if inside:
        # the near rim keeps the sun off the inside wall below where its shadow falls
        q = TUB.pos(u, v)
        back = q + TO_SUN * ((TUB.h - q[:, 1]) / TO_SUN[1])[:, None]
        cosn = cosn * (np.hypot(*(back - TUB.c)[:, [0, 2]].T) < TUB.r1)
    c = PLASTIC * (SKY * (np.full_like(v, 0.9) if inside else 0.75 + 0.25 * v)[:, None] + BOUNCE * 0.6 * (1 - v)[:, None] + SUN * (cosn * 0.8)[:, None])
    c = tone(c, 1.9) * np.exp(rng.normal(0, 0.025, 3))
    return c if c.shape[0] > 1 else c[0]


uu, vv = np.meshgrid(np.linspace(0, 1, 60), np.linspace(0, 1, 6))
tp = P(TUB.pos(uu, vv)).reshape(-1, 2)
hull = tp[ConvexHull(tp).vertices]
board.tape(hull, feather=0.7)
pl = Brush(width=8, bristle=1.1, opacity=0.95, pickup=0.25, thickness=0.4, jitter=0.03, taper=(0.05, 0.08), gap=0.02)
to_eye = lambda u: float(TUB.out(u)[[0, 2]] @ (E - TUB.pos(u, 0.5))[[0, 2]]) > 0  # noqa: E731
mouth = P(TUB.pos(np.linspace(0, 1, 60), np.ones(60)))
board.stroke(mouth, pl.but(width=60), tone(PLASTIC * SKY * 0.7, 1.9))
for u0 in rng.permutation(np.linspace(0, 1, 150, endpoint=False)):
    if to_eye(u0):
        continue
    vs = np.linspace(0.0, 1.0, 5)
    q = TUB.c + (TUB.pos(np.full(5, u0), vs) - TUB.c) * v3(0.96, 1, 0.96)
    board.stroke(P(q), pl.but(width=7), tub_light(np.full(5, u0), vs, inside=True), wobble=0.2)
# the pegs in it: not many yet
floor_in = P(TUB.c + v3(0, 0.04, 0) + np.stack([0.2 * np.cos(2 * np.pi * uu[0]), 0 * uu[0], 0.2 * np.sin(2 * np.pi * uu[0])], 1))
board.tape(mouth, feather=0.6)
for _ in range(46):
    a, rad = rng.uniform(0, 2 * np.pi), 0.19 * np.sqrt(rng.random())
    c0 = TUB.c + v3(rad * np.cos(a), 0.05 + 0.03 * rng.random(), rad * np.sin(a))
    d = unit(v3(rng.normal(), 0.2 * rng.normal(), rng.normal())) * 0.038
    in_sun = np.hypot(*((c0 + TO_SUN * ((TUB.h - c0[1]) / TO_SUN[1])) - TUB.c)[[0, 2]]) < TUB.r1
    board.stroke([P(c0 - d), P(c0 + d)], fine.but(width=5.5, thickness=0.9, taper=(0.05, 0.05)),
                 (wood_lit if in_sun else wood_shd * 0.8) * np.exp(rng.normal(0, 0.1)))
board.tape(hull, feather=0.7)
board.tape(mouth, feather=0.6, mode="cut")
for u0 in rng.permutation(np.linspace(0, 1, 190, endpoint=False)):
    if not to_eye(u0):
        continue
    vs = np.linspace(-0.05, 1.05, 5)
    board.stroke(P(TUB.pos(np.full(5, u0), vs)), pl, tub_light(np.full(5, u0), vs), wobble=0.2)
board.untape()
for vv0 in (0.42, 0.72):
    for u0 in np.linspace(0, 1, 24, endpoint=False):
        if to_eye(u0):
            a, b = P(TUB.pos(u0 - 0.011, vv0)), P(TUB.pos(u0 + 0.011, vv0))
            board.stroke([a, b], Brush(width=4, opacity=0.85, gap=0, thickness=0.2, taper=(0.1, 0.1)),
                         tone(PLASTIC * SKY * 0.55, 1.9))
board.stroke(mouth, Brush(width=4.5, opacity=0.95, gap=0, thickness=0.8, pickup=0.1, taper=(0.0, 0.0)),
             tub_light(np.linspace(0, 1, 60), np.full(60, 1.0)) * 1.15, smooth=False)
base = P(TUB.pos(np.linspace(0.52, 0.98, 30), np.zeros(30)) + UP * 0.004)
board.stroke(base + (0, 2.0), Brush(width=4, opacity=0.8, gap=0, thickness=0.02, taper=(0.3, 0.3)),
             ground_colour(base[:, 0], base[:, 1] + 6, 0.0, open_sun=True, k=0.42), smooth=False)
board.dry()
board.stage("the basket")

# --- hand it over ------------------------------------------------------------------------------------
(HERE / "stages").mkdir(exist_ok=True)
for old in (HERE / "stages").glob("*.jpg"):
    old.unlink()
board.stage("finished")
Image.fromarray(board.stages[-1][2]).save(HERE / "final.png")
stages = []
for i, (name, n, img) in enumerate(board.stages):
    im = Image.fromarray(img)
    im.thumbnail((1400, 1400))
    im.save(HERE / "stages" / f"{i:02d}.jpg", quality=86)
    stages.append({"name": name, "strokes": n, "file": f"stages/{i:02d}.jpg"})
meta = dict(title="Tramuntana, taking in the pegs", artist="carmela-zammit", year=2005,
            medium="Oil on the plywood lid of a linen hamper, red oxide ground", made="2026-11-14", program="paint.py",
            strokes=board.n_strokes, size=[W, H], stages=stages, seconds=round(time.time() - T0, 1))
(HERE / "work.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False))
print(f"{meta['title']}: {board.n_strokes} strokes, {n_pegs} pegs seen, {meta['seconds']}s")
