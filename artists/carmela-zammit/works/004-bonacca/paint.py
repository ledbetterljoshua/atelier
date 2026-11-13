"""Carmela Zammit - Bonaċċa

A calm night in August. The washing was left out; nobody went up for it. The only light on the roof
is the bulb on the stairs, coming up through the door of the stair-head, off the board on the left,
low. It lights the washing from in front and from below, the near sheets most, and throws the whole
line, three times the size, up the blank wall of the house behind.
"""
import os
import sys
from pathlib import Path

import numpy as np
from scipy.spatial import ConvexHull

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[3]))
sys.path.insert(0, str(HERE.parents[1]))

from engine import Board, Brush, hexc, mix, scale  # noqa: E402
from engine.studio import finish  # noqa: E402
from tools import (Bulb, Camera, Hang, Line, cast_point, lay_cloth, lay_field, lay_screen, on_plane,  # noqa: E402
                   sheeting, thrown, tone, unit, v3)

QUICK = float(os.environ.get("QUICK", "1.0"))

W, H = 1650, 1100
rng0 = np.random.default_rng(1993)
board = Board(W, H, hexc("#7a3021"), sheeting(W, H, rng0, darns=[(1180, 300, 36, 22)]), seed=1993,
              light=(-0.6, 0.75))      # she paints at the kitchen table; the board is lit from below-left too
board.dries_off_board = False
board.relief_soft = 2.0
rng = board.rng
cam = Camera(W, H, 1350, (0.0, 1.25, 0.0), pitch=0.0, cy=600)   # sitting on the low wall
E = cam.eye
P = cam.P

# --- tubes ---------------------------------------------------------------------------------------
white, ultra, prussian = hexc("#f7f4ec"), hexc("#20307f"), hexc("#14284a")
naples, ochre, rawsi, burnsi = hexc("#ecd398"), hexc("#c49236"), hexc("#a8692a"), hexc("#7d3418")
cadyel, cadorange, black = hexc("#f2cc3a"), hexc("#e8782a"), hexc("#141210")

# --- the roof, the wall behind, the line ---------------------------------------------------------
ZB, WALL_H = 11.0, 5.0                    # the blank side of the house behind, higher than ours
FLOOR = (v3(0, 0, 0), v3(0, 1, 0))
WALL = (v3(0, 0, ZB), v3(0, 0, -1))
line = Line((-3.4, 4.6), (5.4, 10.97), 2.0, 0.11)    # to a hook in the house wall
S1 = Hang(line, 0.25, 2.15, 1.58, pegs=4, folds=0.12, give=0.03, sag=0.07, droop=0.03, band=0.08, seed=51)
S2 = Hang(line, 2.55, 0.70, 0.95, pegs=2, folds=0.03, give=0.01, sag=0.05, droop=0.02, seed=52)   # pillowcase
S3 = Hang(line, 3.40, 2.05, 1.52, pegs=4, folds=0.11, give=0.025, sag=0.06, band=0.08, seed=53)
S4 = Hang(line, 5.60, 0.95, 1.25, pegs=3, folds=0.04, give=0.015, sag=0.04, seed=54)              # towel
S5 = Hang(line, 6.70, 1.40, 1.45, pegs=3, folds=0.09, give=0.02, sag=0.06, band=0.08, seed=55)   # tablecloth
WASH = [S1, S2, S3, S4, S5]

# --- the light -----------------------------------------------------------------------------------
BULB = Bulb((-2.7, 0.85, 2.0), door=(-2.35, 2.75), facing=(0.4, 0.92), width=0.95, height=2.05, power=10.0,
            soft=0.02)
TUNG = v3(1.0, 0.62, 0.30)                 # a sixty-watt bulb, to an eye that has been in the dark
NIGHT = v3(0.010, 0.016, 0.040)            # what the sky gives, which is almost nothing
THROUGH = v3(1.0, 0.85, 0.66)              # what cotton does to the bulb's light coming through it
TAU, TAU2 = 0.2, 0.07
GEXP, GEXP_W = 0.5, 1.4                    # stone beside lit cotton: she keeps the roof down
COTTON = mix((white, 10), (naples, 0.7))
LIME = scale(mix((white, 3), (naples, 1.4), (ochre, 0.12), (burnsi, 0.08)), 0.7)       # screed
STONE = scale(mix((white, 2), (naples, 1.2), (ochre, 0.6), (burnsi, 0.15)), 0.75)       # franka, the wall

base_y = float(P(v3(0, 0, ZB))[1])
top_y = float(P(v3(0, WALL_H, ZB))[1])



class Tub:
    """The basket, empty, standing where she would have put it down: u round it, v up the side."""
    band = 0.0

    def __init__(self, c, r0, r1, h):
        self.c, self.r0, self.r1, self.h = v3(*c), r0, r1, h

    def pos(self, u, v):
        u, v = np.broadcast_arrays(np.asarray(u, dtype=np.float64), np.asarray(v, dtype=np.float64))
        r = self.r0 + (self.r1 - self.r0) * v
        th = 2 * np.pi * u
        return self.c + np.stack([r * np.cos(th), v * self.h, r * np.sin(th) * 0.8], axis=-1)

    def out(self, u):
        th = 2 * np.pi * np.asarray(u, dtype=np.float64)
        return unit(np.stack([np.cos(th) / 1.0, np.full_like(th, 0.12), np.sin(th) / 0.8], axis=-1))


TUB = Tub((-1.0, 0.0, 4.3), 0.25, 0.3, 0.29)
LIT_FLOOR = cast_point(cam, W, H, WASH, BULB.pos, FLOOR, tau=TAU, tau2=TAU2, blur=0.8) \
    * cast_point(cam, W, H, [TUB], BULB.pos, FLOOR, tau=0.03, tau2=0.03, grid=(60, 6), blur=0.8)
LIT_WALL = cast_point(cam, W, H, WASH, BULB.pos, WALL, tau=TAU, tau2=TAU2, blur=1.2)


def surface(x, y):
    """The world point at board (x, y) on the roof or the wall, its normal, and its albedo."""
    x, y = np.atleast_1d(x).astype(float), np.atleast_1d(y).astype(float)
    wall = y < base_y
    Q = np.where(wall[:, None], on_plane(cam, x, y, *WALL), on_plane(cam, x, y, *FLOOR))
    n = np.where(wall[:, None], WALL[1], FLOOR[1])
    alb = np.where(wall[:, None], STONE, LIME)
    return Q, n, alb, wall


def lit(x, y):
    x, y = np.atleast_1d(x), np.atleast_1d(y)
    xi = np.clip(np.asarray(x).astype(int), 0, W - 1)
    yi = np.clip(np.asarray(y).astype(int), 0, H - 1)
    return np.where(np.asarray(y) < base_y, LIT_WALL[yi, xi], LIT_FLOOR[yi, xi])


def ground_colour(x, y, vary=0.03, open_light=False, door=True):
    """The roof or wall at (x, y). With open_light, as if nothing hung on the line."""
    Q, n, alb, wall = surface(x, y)
    k = BULB.reach(Q, n) if door else BULB.power * np.clip(np.sum(n * unit(BULB.pos - Q), -1), 0, 1) / np.sum((BULB.pos - Q) ** 2, -1)
    s = np.ones_like(k) if open_light else lit(x, y)
    light = np.where(s[:, None] > 0.98, TUNG, TUNG * THROUGH)
    amb = NIGHT * np.where(wall, 0.8, 1.0)[:, None]
    c = alb * (amb + light * (k * s * np.where(wall, GEXP_W, GEXP))[:, None])
    c = tone(c, 1.6) * np.exp(rng.normal(0, vary, 3))
    return c if c.shape[0] > 1 else c[0]


def sky_colour(x, y):
    d = cam.ray(x, y)
    el = np.arcsin(np.clip(d[..., 1], -1, 1))
    t = np.clip(el / 0.35, 0, 1) ** 0.6
    low, high = v3(0.050, 0.040, 0.040), v3(0.008, 0.012, 0.035)    # the town's glow, low, and the night
    c = np.exp(np.log(low) * (1 - t[..., None]) + np.log(high) * t[..., None])
    return np.clip(c, 0.004, 0.97)


# =================================================================================================
# 1. The night, thin, over the red.
# =================================================================================================
scrub = Brush(width=110, bristle=2.6, opacity=0.95, pickup=0.08, dryness=0.0, thickness=0.05, jitter=0.03, deplete=0.0005)
sky_b = Brush(width=44, bristle=2.0, opacity=0.6, pickup=0.4, dryness=0.0, thickness=0.05, jitter=0.03,
              deplete=0.0004, taper=(0.15, 0.2))
region = (-60, -40, W + 60, top_y + 20)
lay_screen(board, region, scrub, lambda x, y: sky_colour(x, y) * 0.9, angle=0.03, length=520, cover=4.0 * QUICK, wobble=8)
lay_screen(board, region, sky_b, lambda x, y: sky_colour(x, y) * np.exp(rng.normal(0, 0.05, 3)), angle=0.03,
           length=380, cover=5.0 * QUICK, wobble=6)
board.dry()

# the aerial on the roof of the house behind, the only thing standing up against the sky
ax, az = 2.7, ZB + 0.8
blackc = tone(mix((black, 3), (ultra, 1)) * 0.02, 1.6)
rod = Brush(width=4, bristle=0.9, opacity=0.95, gap=0.0, pickup=0.05, thickness=0.3, taper=(0.0, 0.0))
board.stroke([P(v3(ax, WALL_H - 0.2, az)), P(v3(ax, 8.0, az))], rod, blackc, smooth=False)
for hy, half in ((5.95, 0.55), (6.45, 0.45)):
    board.stroke([P(v3(ax - half, hy, az + 0.3)), P(v3(ax + half, hy, az - 0.3))], rod.but(width=3), blackc, smooth=False)
    for t in np.linspace(-1, 1, 6):
        c0 = v3(ax + half * t, hy, az - 0.3 * t)
        board.stroke([P(c0 - v3(0.0, 0.0, 0.18)), P(c0 + v3(0.0, 0.0, 0.18))], rod.but(width=2.4), blackc, smooth=False)
cable = np.stack([np.linspace(ax, ax + 0.9, 30), WALL_H + 1.3 - 1.2 * np.sin(np.linspace(0, np.pi / 2, 30)) ** 1.5,
                  np.linspace(az, ZB + 0.02, 30)], 1)
board.stroke(P(cable), rod.but(width=1.8, opacity=0.8), blackc, smooth=False)
board.dry()
board.stage("the night, thin, over the red")

# =================================================================================================
# 2. The wall and the roof, as if the bulb reached all of it and nothing hung on the line.
# =================================================================================================
deck = Brush(width=30, bristle=1.8, opacity=0.85, pickup=0.45, dryness=0.0, thickness=0.12, jitter=0.04, deplete=0.0006)
board.tape([(-10, top_y), (W + 10, top_y), (W + 10, H + 10), (-10, H + 10)], feather=0.6)
lay_screen(board, (-150, top_y - 10, W + 150, H + 40), scrub.but(width=90),
           lambda x, y: scale(ground_colour(x, y, open_light=True, door=False), 0.9), angle=0.0, angle_jitter=0.04,
           length=420, cover=2.5 * QUICK, wobble=3)
board.tape([(-10, top_y), (W + 10, top_y), (W + 10, base_y + 1), (-10, base_y + 1)], feather=0.7)
lay_screen(board, (-60, top_y - 4, W + 60, base_y + 4), deck.but(width=16), lambda x, y: ground_colour(x, y, 0.02, True, False),
           angle=0.0, angle_jitter=0.03, length=170, cover=9.0 * QUICK, wobble=0.6)
board.dry()
board.tape([(-10, base_y - 1), (W + 10, base_y - 1), (W + 10, H + 10), (-10, H + 10)], feather=0.6)
bands = np.linspace(base_y - 2, H + 40, 6)
for y0, y1 in zip(bands[:-1], bands[1:]):
    zk = float(np.clip((((y0 + y1) / 2) - base_y) / (H - base_y), 0.15, 1.0))
    lay_screen(board, (-150, y0, W + 150, y1), deck.but(width=10 + 26 * zk),
               lambda x, y: ground_colour(x, y, 0.02, True, False), angle=0.0, angle_jitter=0.03,
               length=90 + 260 * zk, cover=6.5 * QUICK, wobble=0.5 + 1.5 * zk)
board.untape()
board.dry()
board.stage("the wall and the roof, all in the light")

# =================================================================================================
# 3. The shadows: the jamb's, and the washing's, laid the way the bulb throws them.
# =================================================================================================
shade_b = Brush(width=20, bristle=1.6, opacity=0.92, pickup=0.35, dryness=0.0, thickness=0.1, jitter=0.03, deplete=0.0005,
                taper=(0.15, 0.2))
Y, X = np.mgrid[0:H, 0:W].astype(np.float64) + 0.5
Qf = on_plane(cam, X, Y, *FLOOR)
Qw = on_plane(cam, X, Y, *WALL)
DOOR_F = BULB.through(Qf)
DOOR_W = BULB.through(Qw)
dark_f = np.clip((0.97 - LIT_FLOOR * DOOR_F) * 6, 0, 1) * (Y > base_y)
jamb_w = np.clip((0.97 - DOOR_W) * 6, 0, 1) * (Y <= base_y) * (Y >= top_y)
dark_w = np.clip((0.97 - LIT_WALL) * 6, 0, 1) * (Y <= base_y) * (Y >= top_y) * (1 - jamb_w)
ang_f = thrown(cam, BULB.pos, FLOOR)
board.tape_where(dark_f, feather=1.0)
lay_field(board, (-60, base_y, W + 60, H + 40), shade_b, lambda xs, ys: ground_colour(xs, ys, 0.02),
          angle=ang_f, length=130, cover=7.0 * QUICK, wobble=0.6, angle_jitter=0.04)
# where the jamb keeps the bulb off the wall, the wall is only the night: long strokes along the courses,
# begun off the board so they arrive loaded, and stopped by the tape at the jamb's edge
board.tape_where(jamb_w, feather=1.0)
jx = float(np.max(np.where(jamb_w[int((top_y + base_y) / 2)] > 0.5)[0], initial=0))
jb = shade_b.but(width=26, taper=(0.0, 0.0), deplete=0.0002, gap=0.0, loadvar=0.06, opacity=0.97)
for yy in np.arange(top_y - 6, base_y + 10, 9.0):
    yj = yy + rng.normal(0, 2)
    xs = np.linspace(-120, jx + 120 + rng.uniform(0, 60), 8)
    ys = yj + np.linspace(0, rng.normal(0, 3), 8)
    board.stroke(np.stack([xs, ys], 1), jb, ground_colour(xs, ys, 0.02), wobble=0.8)
board.tape_where(dark_w, feather=1.0)
lay_field(board, (-60, top_y, W + 60, base_y), shade_b.but(width=16), lambda xs, ys: ground_colour(xs, ys, 0.02),
          angle=-np.pi / 2, length=110, cover=7.0 * QUICK, wobble=0.6, angle_jitter=0.04)
board.untape()
board.dry()
board.stage("the shadows, the way the bulb throws them")

# the courses of the wall, franka blocks a hand high and two long, and the joints in the screed
jnt = Brush(width=2.5, bristle=0.9, opacity=0.5, gap=0.1, pickup=0.3, thickness=0.05, taper=(0.1, 0.1))


def darker(k):
    return lambda xs, ys: ground_colour(xs, ys, 0.02) * k


for yc in np.arange(0.27, WALL_H - 0.05, 0.27):
    pts = P(np.stack([np.linspace(-9, 9, 60), np.full(60, yc), np.full(60, ZB)], 1))
    board.stroke(pts, jnt, darker(0.6)(pts[:, 0], pts[:, 1]), wobble=0.4, smooth=False)
    for xc in np.arange(-9.0 + 0.27 * (round(yc / 0.27) % 2), 9.0, 0.55):
        a, b = P(v3(xc, yc - 0.27, ZB)), P(v3(xc, yc, ZB))
        board.stroke([a, b], jnt.but(width=2.0, opacity=0.4), darker(0.65)(np.array([a[0], b[0]]), np.array([a[1], b[1]])))
for z in np.arange(4.0, ZB, 2.0):
    pts = P(np.stack([np.linspace(-9, 9, 80), np.zeros(80), np.full(80, z)], 1))
    pts = pts[(pts[:, 0] > -40) & (pts[:, 0] < W + 40)]
    board.stroke(pts, jnt.but(width=max(1.5, 8.0 / z)), darker(0.55)(pts[:, 0], pts[:, 1]), wobble=0.4, smooth=False)
board.dry()

# the wire's shadow and the pegs', where they cross light; and the post at the far end, standing up
def on_wall(p):
    p = np.atleast_2d(p)
    t = (ZB - BULB.pos[2]) / (p[:, 2] - BULB.pos[2])
    return BULB.pos + (p - BULB.pos) * t[:, None]


wire_w = on_wall(line.pts(n=160))
keep = (wire_w[:, 1] < WALL_H) & (BULB.through(wire_w) > 0.5)
pts = P(wire_w[keep])
board.stroke(pts, Brush(width=2.6, bristle=0.9, opacity=0.85, gap=0.0, pickup=0.2, thickness=0.05, taper=(0.0, 0.0)),
             ground_colour(pts[:, 0], pts[:, 1], 0.0) * 0.3, smooth=False)
for sh in WASH:
    for k in range(sh.pegs):
        top = sh.line.at(sh.s0 + k / (sh.pegs - 1) * sh.width)
        if BULB.through(on_wall(top))[0] < 0.5:
            continue
        a, b = P(on_wall(top + v3(0, 0.025, 0))[0]), P(on_wall(top - v3(0, 0.07, 0))[0])
        board.stroke([a, b], Brush(width=5, opacity=0.8, gap=0, thickness=0.05, taper=(0.1, 0.1)),
                     ground_colour(*((a + b) / 2), 0.0) * 0.35)
board.dry()

# the drainpipe down the house wall, standing off it on brackets, and its shadow beside it
PIPE_X, PIPE_R = 6.0, 0.05
pz = ZB - 0.07
pipe_sh = on_wall(np.array([[PIPE_X, 0.0, pz], [PIPE_X, WALL_H, pz]]))
a, b = P(pipe_sh[0]), P(pipe_sh[1])
board.stroke([b, a], Brush(width=0.12 * cam.f / ZB, opacity=0.85, gap=0.0, pickup=0.2, thickness=0.05, taper=(0.0, 0.0)),
             ground_colour(*((a + b) / 2), 0.0) * 0.35, smooth=False)
pipe_c = mix((white, 1), (naples, 1), (rawsi, 0.5), (black, 0.4))
pw = 2 * PIPE_R * cam.f / pz
side = unit(v3(*(BULB.pos - v3(PIPE_X, 1.0, pz))) * v3(1, 0, 1))
kpipe = float(BULB.reach(v3(PIPE_X, 1.2, pz), side))
for off, k in ((-0.3, 1.0), (0.0, 0.55), (0.3, 0.15)):
    board.stroke([P(v3(PIPE_X, WALL_H + 0.02, pz)) + (off * pw, 0), P(v3(PIPE_X, 0.0, pz)) + (off * pw, 0)],
                 Brush(width=pw * 0.45, opacity=0.95, gap=0.0, pickup=0.1, thickness=0.4, taper=(0.0, 0.0)),
                 tone(pipe_c * (NIGHT + TUNG * kpipe * k * GEXP_W), 1.6), smooth=False)
for yb in np.arange(0.6, WALL_H, 1.1):
    board.stroke([P(v3(PIPE_X, yb, pz)) - (pw * 0.7, 0), P(v3(PIPE_X, yb, pz)) + (pw * 0.7, 0)],
                 Brush(width=4, opacity=0.9, gap=0.0, thickness=0.5, taper=(0.0, 0.0)), tone(pipe_c * NIGHT * 2, 1.6))
board.dry()
board.stage("courses and joints")

# =================================================================================================
# 4. The washing laid in, all of it, as the night has it.
# =================================================================================================
BOUNCE = LIME * TUNG * 0.25               # the lit screed gives a little back, up under the hems


def cloth(sheet, gain=1.0, vary=0.03, night_only=False, relief=0.85, inter=0.1):
    flat = v3(sheet.line.n[0], 0, sheet.line.n[1])

    def f(u, v):
        u, v = np.atleast_1d(u).astype(float), np.atleast_1d(v).astype(float)
        Q = sheet.pos(u, v)
        n = unit(sheet.normal(u, v, E) * relief + flat * (1 - relief))
        lv = unit(BULB.pos - Q)
        nl = np.sum(n * lv, -1)
        r2 = np.sum((BULB.pos - Q) ** 2, -1)
        k = BULB.power / r2 * BULB.through(Q)
        layers = np.where((v < sheet.band) | (v > 0.96), TAU2 / TAU, 1.0)
        front = COTTON * TUNG * (np.clip(nl, 0, 1) * k)[:, None]
        back = COTTON * TUNG * THROUGH * TAU * (np.clip(-nl, 0, 1) ** 0.6 * k * layers)[:, None]
        amb = COTTON * (NIGHT * (0.5 + 0.5 * n[:, 1:2]) + BOUNCE * 0.08 * (0.5 - 0.5 * n[:, 1:2]))
        # what one fold throws into the next: light comes out of a fold from both its walls
        inside = COTTON * TUNG * (inter * k * np.clip(np.sum(flat * lv, -1), 0, 1))[:, None]
        c = amb + 0.25 * inside if night_only else np.where(nl[:, None] > 0, front, back) + inside + amb
        c = tone(c * gain, 1.6) * np.exp(rng.normal(0, vary, 3))
        return c if c.shape[0] > 1 else c[0]
    return f


blk = Brush(width=26, bristle=1.5, opacity=0.92, pickup=0.3, dryness=0.03, thickness=0.3, jitter=0.03, deplete=0.0006)
for s in WASH[::-1]:
    lay_cloth(board, cam, s, blk, cloth(s, night_only=True, gain=2.2, vary=0.04), along="v", length=200,
              cover=5.0 * QUICK, wobble=1.0, margin=0.05)
board.dry()
board.stage("the washing, as the night has it")

# =================================================================================================
# 5. The light on the cloth, from the pegs down, out of the folds into the light.
# =================================================================================================
fold_b = Brush(width=15, bristle=1.4, opacity=0.9, pickup=0.4, dryness=0.0, thickness=0.4, jitter=0.025, deplete=0.0005,
               taper=(0.2, 0.25))
for s in WASH[::-1]:
    nk = float(np.clip(5.0 / (s.pos(0.5, 0.5)[2] - E[2]), 0.6, 1.2))
    lay_cloth(board, cam, s, fold_b.but(width=15 * nk), cloth(s, vary=0.015), along="v", length=240 * nk, cover=10.0 / nk * QUICK,
              wobble=0.6, margin=0.05, run=True)
    lay_cloth(board, cam, s, fold_b.but(width=8 * nk, opacity=0.5), cloth(s, vary=0.015), along="u", length=100 * nk,
              cover=0.6 * QUICK, wobble=0.4, margin=0.04, where=lambda u, v: v > 0.9, run=True)
# where the light lands hardest on cloth, thick, in one go: the near sheet, low, facing the door
hot = Brush(width=22, bristle=1.4, opacity=0.8, pickup=0.6, dryness=0.0, thickness=0.8, jitter=0.02, deplete=0.0003,
            taper=(0.12, 0.15), gap=0.01)


def hardest(u, v, k=0.55):
    Q = S1.pos(u, v)
    n = S1.normal(np.atleast_1d(u), np.atleast_1d(v), E)[0]
    return float(n @ unit(BULB.pos - Q)) > k and 0.35 < v < 0.95


lay_cloth(board, cam, S1, hot, cloth(S1, gain=1.1, vary=0.015), along="v", length=260, cover=2.5 * QUICK, wobble=0.4,
          margin=0.0, run=True, where=hardest)
board.dry()
board.stage("the bulb on the cloth")


# =================================================================================================
# 6. Wire and pegs.
# =================================================================================================
fine = Brush(width=3, bristle=0.9, opacity=0.9, pickup=0.0, thickness=0.8, jitter=0.02, gap=0.0, taper=(0.0, 0.0), deplete=0.0)
board.stroke([P(line.at(line.span)) + (-3, 0), P(line.at(line.span)) + (4, 3)], fine.but(width=4), tone(mix((black, 2), (ultra, 1)) * 0.3, 2.0))
board.stroke(P(line.pts(n=80)), fine.but(width=2.6), tone(mix((black, 2), (ultra, 1)) * 0.3, 2.0), smooth=False)
peg_c = mix((burnsi, 2), (black, 1.2), (ochre, 0.6))
for sh in WASH:
    for k in range(sh.pegs):
        u = k / (sh.pegs - 1) + rng.normal(0, 0.01)
        top = sh.line.at(sh.s0 + u * sh.width)
        a, b = P(top + v3(0, 0.025, 0)), P(top - v3(0, 0.06, 0))
        wpx = max(2.5, 0.016 * cam.f / max(top[2] - E[2], 0.5))
        kk = float(BULB.reach(top, unit(BULB.pos - top)))
        board.stroke([a, b + rng.normal(0, 0.5, 2)], fine.but(width=wpx, thickness=1.2), tone(peg_c * (NIGHT + TUNG * kk), 2.0))
board.dry()
board.stage("wire and pegs")

# =================================================================================================
# 7. The basket, empty, where she left it by the door.
# =================================================================================================
turq = hexc("#2a9a9a")
PLASTIC = mix((turq, 2), (ultra, 0.3), (white, 2.2), (rawsi, 0.8), (burnsi, 0.45))


def tub_light(u, v, inside=False):
    u, v = np.atleast_1d(u).astype(float), np.atleast_1d(v).astype(float)
    Q = TUB.pos(u, v)
    n = TUB.out(u) * (-1 if inside else 1)
    k = BULB.reach(Q, n)
    if inside:
        # the near rim keeps the bulb off the bottom of the inside wall
        lv = BULB.pos - Q
        hz = np.hypot(lv[:, 0], lv[:, 2])
        rr = np.hypot(*(Q - TUB.c)[:, [0, 2]].T) + 1e-6
        chord = np.clip(-2 * np.sum((Q - TUB.c)[:, [0, 2]] * lv[:, [0, 2]], -1) / hz, 0, 2 * rr)
        k = k * ((Q[:, 1] + chord * lv[:, 1] / hz) > TUB.h)
    c = PLASTIC * (NIGHT * 1.5 + TUNG * (k * GEXP * 1.4)[:, None])
    c = tone(c, 1.6) * np.exp(rng.normal(0, 0.03, 3))
    return c if c.shape[0] > 1 else c[0]


uu, vv = np.meshgrid(np.linspace(0, 1, 60), np.linspace(0, 1, 6))
tp = P(TUB.pos(uu, vv)).reshape(-1, 2)
hull = tp[ConvexHull(tp).vertices]
board.tape(hull, feather=0.7)
pl = Brush(width=7, bristle=1.1, opacity=0.95, pickup=0.25, thickness=0.4, jitter=0.03, taper=(0.05, 0.08), gap=0.02)
to_eye = lambda u: float(np.sum(TUB.out(u)[[0, 2]] * (E - TUB.pos(u, 0.5))[[0, 2]])) > 0  # noqa: E731
for u0 in rng.permutation(np.linspace(0, 1, 160, endpoint=False)):
    if not to_eye(u0):
        continue
    vs = np.linspace(-0.05, 1.05, 5)
    board.stroke(P(TUB.pos(np.full(5, u0), vs)), pl, tub_light(np.full(5, u0), vs), wobble=0.2)
mouth = P(TUB.pos(np.linspace(0, 1, 60), np.ones(60)))
board.tape(mouth, feather=0.7, mode="and")
board.stroke(mouth, pl.but(width=40), tone(PLASTIC * NIGHT * 0.6, 1.6))
for u0 in rng.permutation(np.linspace(0, 1, 120, endpoint=False)):
    if to_eye(u0):
        continue
    vs = np.linspace(0.0, 1.0, 5)
    q = TUB.c + (TUB.pos(np.full(5, u0), vs) - TUB.c) * v3(0.95, 1, 0.95)
    board.stroke(P(q), pl.but(width=6), tub_light(np.full(5, u0), vs, inside=True), wobble=0.2)
board.untape()
for vv0 in (0.4, 0.7):
    for u0 in np.linspace(0, 1, 22, endpoint=False):
        if to_eye(u0):
            a, b = P(TUB.pos(u0 - 0.01, vv0)), P(TUB.pos(u0 + 0.01, vv0))
            board.stroke([a, b], Brush(width=3.5, opacity=0.85, gap=0, thickness=0.2, taper=(0.1, 0.1)),
                         tone(PLASTIC * NIGHT * 0.5, 1.6))
board.stroke(mouth, Brush(width=4, opacity=0.95, gap=0, thickness=0.8, pickup=0.1, taper=(0.0, 0.0)),
             tub_light(np.linspace(0, 1, 60), np.full(60, 1.0)) * 1.2, smooth=False)
board.dry()
board.stage("the basket, empty, by the door")

finish(board, HERE, title="Bonaċċa, left out", artist="carmela-zammit", year=1993,
       medium="Oil on cotton sheeting, red oxide ground", made="2026-11-12")
