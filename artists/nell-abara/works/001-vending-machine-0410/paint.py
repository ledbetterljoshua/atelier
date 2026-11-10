"""Nell Abara - Vending machine, link corridor waiting bay, 04:10

Standing in the link corridor where it opens into the waiting bay. The machine is against the bay's
back wall, facing me. A row of beam seats has its back to me. Somebody's coat. The corridor goes
on to the left, to the fire doors.
"""
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[3]))
sys.path.insert(0, str(HERE.parents[1]))

from engine import Board, Brush, ground, hexc, mix, paths, scale  # noqa: E402
from engine.studio import finish  # noqa: E402
from tools import Plane, RectLight, View, lay, line3, quad, tone, v3  # noqa: E402

W, H = 1800, 1200
rng0 = np.random.default_rng(410)
board = Board(W, H, hexc("#0b0a0a"), ground.hardboard_mesh(W, H, rng0), seed=1994)
rng = board.rng
view = View(W, H, 1500, 486, 504, (0, 1.45, 0))
P = view.P

# --- tubes -----------------------------------------------------------------------------------
black, ultra, umber = hexc("#0b0a0a"), hexc("#1b2a7a"), hexc("#4a2a16")
viridian, ochre, cadred = hexc("#0f6b55"), hexc("#c0902f"), hexc("#c6281c")
lemon, white = hexc("#efe36a"), hexc("#f6f3ea")
night = mix((ultra, 2), (umber, 1), (black, 2))

# --- what the surfaces are -------------------------------------------------------------------
A_WALL = mix((white, 5), (ochre, 1))
A_DADO = mix((white, 2), (viridian, 1), (umber, 0.6))
A_CEIL = mix((white, 3), (umber, 1), (ochre, 0.3))
A_FLOOR = mix((white, 2.2), (viridian, 0.45), (umber, 1), (black, 0.35))
A_DOOR = mix((umber, 2), (ochre, 1))
A_SEAT = mix((viridian, 1.5), (ultra, 1), (white, 2.5), (umber, 0.8))

# --- what is lit -----------------------------------------------------------------------------
tube = mix((white, 10), (viridian, 0.5), (lemon, 1.2))
tube = tube / tube.max()
R = 26.0
win = RectLight(Plane((2.36, 0.78, 5.7), (0.64, 0, 0), (0, 0.90, 0)), tube * R, facing=(0, 0, -1))
hdr = RectLight(Plane((2.34, 1.71, 5.7), (0.87, 0, 0), (0, 0.10, 0)), v3(1.0, 0.42, 0.10) * R * 0.8,
                nu=3, nv=1, facing=(0, 0, -1))
far = RectLight(Plane((-0.6, 1.15, 21.9), (1.2, 0, 0), (0, 0.6, 0)), v3(0.85, 1.0, 0.55) * 13,
                nu=2, nv=1, facing=(0, 0, -1))
sign = RectLight(Plane((-0.3, 2.2, 21.9), (0.6, 0, 0), (0, 0.2, 0)), v3(0.1, 1.0, 0.4) * 10,
                 nu=2, nv=1, facing=(0, 0, -1))
AMB = v3(0.0045, 0.0055, 0.012)

CHAIRS = [(1.45 + i * 0.56, 1.45 + i * 0.56 + 0.52) for i in range(4)]
ZB, ZF, SEAT_Y, BACK0, BACK1 = 3.9, 4.32, 0.45, 0.50, 0.84


def in_chair(x):
    return any(a <= x <= b for a, b in CHAIRS)


def blocked(S, Q):
    if Q[2] < ZB < S[2]:
        t = (ZB - Q[2]) / (S[2] - Q[2])
        h, x = Q[1] + t * (S[1] - Q[1]), Q[0] + t * (S[0] - Q[0])
        if BACK0 <= h <= BACK1 and in_chair(x):
            return True
    if Q[1] < SEAT_Y < S[1]:
        t = (SEAT_Y - Q[1]) / (S[1] - Q[1])
        z, x = Q[2] + t * (S[2] - Q[2]), Q[0] + t * (S[0] - Q[0])
        if ZB <= z <= ZF and in_chair(x):
            return True
    return False


def bounce(Q):
    """What the lit floor throws back up at the things standing near it."""
    g = np.exp(-((Q[0] - 2.8) / 2.2) ** 2) * np.exp(-Q[1] / 0.9) * np.exp(-max(0.0, Q[2] - 6.6) / 1.5)
    return tube * A_FLOOR * 0.55 * g


def light(Q, N, shadows=False):
    b = blocked if shadows else None
    return AMB + bounce(Q) + win.onto(Q, N, b) + hdr.onto(Q, N, b) + far.onto(Q, N) + sign.onto(Q, N)


def shader(albedo, N, shadows=False, gain=1.0, vary=0.10):
    N = v3(*N)

    def f(Q):
        a = albedo(Q) if callable(albedo) else albedo
        c = tone(a * light(Q, N, shadows) * gain)
        return c * np.exp(rng.normal(0, vary))
    return f


def lum(c):
    return 0.2 * c[0] + 0.7 * c[1] + 0.1 * c[2]


UP, DOWN, EAST, WEST, BACK = (0, 1, 0), (0, -1, 0), (1, 0, 0), (-1, 0, 0), (0, 0, -1)
wall_alb = lambda Q: A_DADO if Q[1] < 0.95 else A_WALL  # noqa: E731

ceil_cor = Plane((-1.2, 2.7, 3.4), (2.4, 0, 0), (0, 0, 18.6))
ceil_bay = Plane((1.2, 2.7, 3.4), (4.8, 0, 0), (0, 0, 3.1))
wall_l = Plane((-1.2, 0, 3.0), (0, 0, 4.5), (0, 2.7, 0))
wall_lf = Plane((-1.2, 0, 7.5), (0, 0, 14.5), (0, 2.7, 0))
wall_r = Plane((1.2, 0, 6.5), (0, 0, 15.5), (0, 2.7, 0))
wall_end = Plane((-1.2, 0, 22), (2.4, 0, 0), (0, 2.7, 0))
floor_cor = Plane((-1.2, 0, 6.5), (2.4, 0, 0), (0, 0, 15.5))
floor_near = Plane((-1.2, 0, 2.6), (7.2, 0, 0), (0, 0, 3.9))
wall_bay = Plane((1.2, 0, 6.5), (4.8, 0, 0), (0, 2.7, 0))

# =============================================================================================
# 1. Imprimatura: thin coloured darks over the black, so the black is never just black.
# =============================================================================================
wash = Brush(width=130, bristle=2.6, opacity=0.5, dryness=0.42, pickup=0.3, thickness=0.2, jitter=0.12, deplete=0.0008)
for i in range(110):
    x, y = rng.uniform(-100, W + 100), rng.uniform(-50, H + 50)
    a = rng.normal(-0.5, 0.35)
    L = rng.uniform(300, 700)
    c = mix((ultra, rng.uniform(1, 3)), (umber, rng.uniform(0.5, 2.5)), (black, 2.5))
    board.stroke([(x - np.cos(a) * L / 2, y - np.sin(a) * L / 2), (x + np.cos(a) * L / 2, y + np.sin(a) * L / 2)],
                 wash, c, wobble=10)
board.dry()
board.stage("coloured darks over black")

# =============================================================================================
# 2. Block-in, back to front. Thin, a bit dry, so the mesh stays in the darks.
# =============================================================================================
blk = Brush(width=24, opacity=0.92, pickup=0.4, dryness=0.22, thickness=0.45, jitter=0.06, deplete=0.001)
dk = 0.8
C = 3.4
CG, LG = 0.38, 0.55      # she holds the ceiling and the near wall down so the machine stays brightest
lay(board, view, wall_end, blk, shader(A_WALL, BACK, gain=dk), UP, length=40, zref=22, cover=C)
lay(board, view, ceil_cor, blk, shader(A_CEIL, DOWN, gain=dk * CG), EAST, length=110, cover=C, shrink=0.8)
lay(board, view, wall_lf, blk, shader(wall_alb, EAST, gain=dk), UP, length=70, cover=C, shrink=0.8)
lay(board, view, wall_l, blk, shader(wall_alb, EAST, gain=dk * LG), (0, 0, 1), length=120, cover=C, shrink=0.8)
lay(board, view, wall_r, blk, shader(wall_alb, WEST, gain=dk), UP, length=70, cover=C, shrink=0.8)
lay(board, view, floor_cor, blk, shader(A_FLOOR, UP, gain=dk), EAST, length=70, cover=C, shrink=0.8)
lay(board, view, ceil_bay, blk, shader(A_CEIL, DOWN, gain=dk * CG), EAST, length=130, cover=C)
lay(board, view, wall_bay, blk, shader(wall_alb, BACK, gain=dk), UP, length=110, zref=6.5, cover=2.2)
lay(board, view, wall_bay, blk, shader(wall_alb, BACK, gain=dk), (1, 0.25, 0), length=110, zref=6.5, cover=1.6)
lay(board, view, floor_near, blk, shader(A_FLOOR, UP, shadows=True, gain=dk), EAST, length=130, cover=C)
board.dry()
board.stage("the room blocked in")

# =============================================================================================
# 3. Scumbles: drier paint dragged over the mesh wherever the machine's light actually reaches.
# =============================================================================================
scm = Brush(width=26, opacity=0.8, pickup=0.0, dryness=0.52, thickness=0.9, jitter=0.05, deplete=0.0016)


def lit_only(albedo, N, thr, shadows=False):
    N = v3(*N)

    def w(Q):
        a = albedo(Q) if callable(albedo) else albedo
        return lum(tone(a * light(Q, N, shadows))) > thr
    return w


S = 2.6
lay(board, view, floor_near, scm, shader(A_FLOOR, UP, shadows=True, gain=1.2), EAST, length=140, cover=S,
    where=lit_only(A_FLOOR, UP, 0.02, True))
lay(board, view, wall_l, scm, shader(wall_alb, EAST, gain=1.2 * LG), UP, length=100, cover=S,
    where=lit_only(wall_alb, EAST, 0.012))
lay(board, view, wall_lf, scm.but(width=12), shader(wall_alb, EAST, gain=1.25), UP, length=46, cover=1.8, shrink=0.8,
    where=lambda Q: Q[2] > 13)
lay(board, view, wall_r, scm.but(width=12), shader(wall_alb, WEST, gain=1.25), UP, length=46, cover=1.8, shrink=0.8,
    where=lambda Q: Q[2] > 13)
lay(board, view, ceil_bay, scm, shader(A_CEIL, DOWN, gain=1.15 * CG), EAST, length=110, cover=S,
    where=lit_only(A_CEIL, DOWN, 0.012))
lay(board, view, ceil_cor, scm, shader(A_CEIL, DOWN, gain=1.15 * CG), EAST, length=100, cover=S, shrink=0.8,
    where=lit_only(A_CEIL, DOWN, 0.012))
lay(board, view, wall_bay, scm.but(dryness=0.62), shader(wall_alb, BACK, gain=1.25), EAST, length=120, zref=6.5,
    cover=1.8, where=lambda Q: Q[1] < 1.3)
lay(board, view, floor_cor, scm.but(width=12), shader(A_FLOOR, UP, gain=1.4), EAST, length=46, cover=2.0, shrink=0.8,
    where=lambda Q: abs(Q[0]) < 0.8)
# brightest floor, wetter
lay(board, view, floor_near, scm.but(dryness=0.3, opacity=0.75), shader(A_FLOOR, UP, shadows=True, gain=1.45), EAST,
    length=110, cover=2.0, where=lit_only(A_FLOOR, UP, 0.10, True))
board.dry()
board.stage("light scumbled over the mesh")

# =============================================================================================
# 4. Fixtures: the things a corridor has.
# =============================================================================================
fine = Brush(width=3, bristle=0.9, opacity=0.85, pickup=0.0, thickness=0.6, jitter=0.03, gap=0.0, taper=(0.03, 0.05))

# fire doors at the far end
ZE = 21.95
board.tape(quad(view, [(-0.9, 0, ZE), (0.9, 0, ZE), (0.9, 2.05, ZE), (-0.9, 2.05, ZE)]))
board.fill(quad(view, [(-0.9, 0, ZE), (0.9, 0, ZE), (0.9, 2.05, ZE), (-0.9, 2.05, ZE)]),
           Brush(width=9, opacity=0.9, thickness=0.5), tone(A_DOOR * 0.03), angle=np.pi / 2)
board.untape()
for sx in (-1, 1):
    q = quad(view, [(sx * 0.22, 1.12, ZE), (sx * 0.64, 1.12, ZE), (sx * 0.64, 1.78, ZE), (sx * 0.22, 1.78, ZE)])
    board.tape(q)
    board.fill(q, Brush(width=7, opacity=0.95, thickness=2.2, pickup=0), mix((white, 6), (lemon, 2), (viridian, 0.6)),
               angle=np.pi / 2, color_fn=lambda m: scale(mix((white, 6), (lemon, 2), (viridian, 0.6)), rng.uniform(0.75, 1.0)))
    board.untape()
line3(board, view, (0, 0.02, ZE), (0, 2.05, ZE), fine.but(width=2), black)
q = quad(view, [(-0.3, 2.2, ZE), (0.3, 2.2, ZE), (0.3, 2.42, ZE), (-0.3, 2.42, ZE)])
board.tape(q)
board.fill(q, Brush(width=6, opacity=0.95, thickness=2.0, pickup=0), hexc("#35d07a"), angle=0)
board.untape()

# doors off the corridor, shut
door_b = Brush(width=8, opacity=0.9, thickness=0.5, dryness=0.15)
for x, z0, z1 in [(-1.19, 8.6, 9.6), (-1.19, 13.5, 14.5), (1.19, 10.5, 11.5), (1.19, 16.0, 17.0)]:
    q = quad(view, [(x, 0.02, z0), (x, 0.02, z1), (x, 2.05, z1), (x, 2.05, z0)])
    N = v3(1 if x < 0 else -1, 0, 0)
    c = tone(A_DOOR * light(v3(x, 1.0, (z0 + z1) / 2), N) * 0.9)
    board.tape(q)
    board.fill(q, door_b.but(width=max(3, 40 / z0 * 2)), c, angle=np.pi / 2)
    board.untape()
    for zz in (z0, z1):
        line3(board, view, (x, 0.02, zz), (x, 2.08, zz), fine.but(width=1.6, opacity=0.6), scale(night, 0.5))

# noticeboard on the bay wall, between the corner and the machine
nb = [(1.5, 1.1), (2.12, 1.9)]
q = quad(view, [(nb[0][0], nb[0][1], 6.49), (nb[1][0], nb[0][1], 6.49), (nb[1][0], nb[1][1], 6.49), (nb[0][0], nb[1][1], 6.49)])
board.tape(q)
board.fill(q, Brush(width=11, opacity=0.9, thickness=0.5, dryness=0.2), tone(mix((umber, 2), (ochre, 1)) * (AMB * 2.5 + bounce(v3(1.8, 0.9, 6.5)))), angle=0.1)
board.untape()
for k in range(6):
    px0 = rng.uniform(nb[0][0] + 0.03, nb[1][0] - 0.18)
    py0 = rng.uniform(nb[0][1] + 0.04, nb[1][1] - 0.24)
    pw_, ph_ = rng.choice([0.105, 0.148]), rng.choice([0.148, 0.21])
    tilt = rng.normal(0, 0.012)
    q = quad(view, [(px0, py0, 6.48), (px0 + pw_, py0 + tilt, 6.48), (px0 + pw_, py0 + ph_ + tilt, 6.48), (px0, py0 + ph_, 6.48)])
    paper_c = tone(mix((white, 4), (lemon if k % 3 == 0 else white, 1)) * (AMB * 2.2 + bounce(v3(px0, py0, 6.5)) * 1.3))
    board.tape(q, feather=0.6)
    board.fill(q, Brush(width=6, opacity=0.85, thickness=0.7, dryness=0.25), paper_c, angle=0.0)
    board.untape()

# skirtings, dado line, handrail
dark_line = fine.but(width=4, opacity=0.7)
line3(board, view, (-1.2, 0.05, 3.6), (-1.2, 0.05, 22), dark_line, scale(night, 0.6))
line3(board, view, (1.2, 0.05, 6.5), (1.2, 0.05, 22), dark_line.but(width=3), scale(night, 0.6))
line3(board, view, (1.2, 0.05, 6.5), (6.0, 0.05, 6.5), dark_line.but(width=5), scale(night, 0.5))
line3(board, view, (-1.2, 0.95, 3.6), (-1.2, 0.95, 22), fine.but(width=2, opacity=0.5), scale(night, 0.8))
line3(board, view, (1.2, 0.95, 6.5), (6.0, 0.95, 6.5), fine.but(width=2, opacity=0.4), scale(night, 0.7))
# handrail: lit where the machine can see it, then lost
for z0, z1 in [(3.65, 4.4), (4.4, 5.1), (5.1, 5.8), (5.8, 8), (8, 22)]:
    zm = (z0 + z1) / 2
    c = tone(mix((ochre, 1), (umber, 1), (white, 1)) * light(v3(-1.12, 0.92, zm), v3(0.6, 0.8, 0)) * 1.6)
    line3(board, view, (-1.13, 0.92, z0), (-1.13, 0.92, z1), fine.but(width=max(2, 16 * 4 / zm), thickness=1.2), c)
    line3(board, view, (-1.13, 0.87, z0), (-1.13, 0.87, z1), fine.but(width=max(1.5, 8 * 4 / zm), opacity=0.7), scale(night, 0.5))
# corner where the corridor wall leaves the bay
line3(board, view, (1.2, 0.05, 6.5), (1.2, 2.7, 6.5), fine.but(width=3, opacity=0.5),
      tone(A_WALL * (AMB + bounce(v3(1.4, 0.6, 6.5))) * 2.2))
# ceiling grid, only where there is light to see it by
grid = fine.but(width=2.4, opacity=0.6)
for z in np.arange(3.9, 6.6, 0.6):
    line3(board, view, (-1.2, 2.7, z), (6.0, 2.7, z), grid, scale(night, 0.7), wobble=0.6)
for x in np.arange(-0.6, 6.0, 0.6):
    line3(board, view, (x, 2.7, 3.75), (x, 2.7, 6.5 if x > 1.2 else 22), grid, scale(night, 0.7), wobble=0.6)
# the ceiling light that is switched off
off = Plane((3.6, 2.69, 4.5), (1.2, 0, 0), (0, 0, 0.6))
lay(board, view, off, Brush(width=12, opacity=0.8, thickness=0.8, pickup=0), shader(mix((white, 4), (ultra, 0.5)), DOWN, gain=0.55),
    EAST, length=70, cover=2.2, feather=0.8)
# clock on the bay wall
cx, cy = P(v3(4.5, 2.02, 6.5))
cr = 0.155 * view.ppm(6.5)
face = tone(white * (AMB * 2.0 + bounce(v3(4.5, 0.75, 6.5)) * 1.5))
board.tape(paths.arc(cx, cy, cr, 0, 2 * np.pi, 40))
board.fill(paths.arc(cx, cy, cr, 0, 2 * np.pi, 40), Brush(width=9, opacity=0.92, thickness=0.8), face, angle=0.3)
board.untape()
board.stroke(paths.arc(cx, cy, cr, 0, 2.02 * np.pi, 48), fine.but(width=3.0, taper=(0, 0)), scale(night, 0.4), smooth=False)
hand = fine.but(taper=(0.0, 0.1), gap=0.0, jitter=0.0)
for ang, ln, wd in [(np.radians(125 - 90), 0.5, 2.6), (np.radians(60 - 90), 0.78, 1.8)]:
    board.stroke([(cx, cy), (cx + np.cos(ang) * cr * ln, cy + np.sin(ang) * cr * ln)], hand.but(width=wd), black)
board.dry()
board.stage("fixtures")

# =============================================================================================
# 5. The machine's cabinet. Dark, exact, taped: the one hard-edged thing in the room.
# =============================================================================================
ZM = 5.7
side = quad(view, [(2.3, 0.03, 6.5), (2.3, 0.03, ZM), (2.3, 1.83, ZM), (2.3, 1.83, 6.5)])
board.tape(side)
board.fill(side, Brush(width=14, opacity=0.95, thickness=0.6, dryness=0.15), mix((black, 3), (ultra, 1)), angle=np.pi / 2,
           color_fn=lambda m: scale(mix((black, 3), (ultra, 1)), rng.uniform(0.9, 1.6)))
board.untape()
front = quad(view, [(2.3, 0.03, ZM), (3.25, 0.03, ZM), (3.25, 1.83, ZM), (2.3, 1.83, ZM)])
board.tape(front)
board.fill(front, Brush(width=18, opacity=0.96, thickness=0.6, dryness=0.12), mix((black, 3), (ultra, 1.2)), angle=np.pi / 2,
           color_fn=lambda m: scale(mix((black, 3), (ultra, 1.2), (viridian, 0.3)), rng.uniform(0.9, 1.5)))
board.untape()
# its edges, found by its own light
edge = fine.but(width=1.8, opacity=0.5)
line3(board, view, (2.3, 0.05, ZM), (2.3, 1.83, ZM), edge, tone(tube * 0.09))
line3(board, view, (3.25, 0.05, ZM), (3.25, 1.83, ZM), edge, tone(tube * 0.07))
line3(board, view, (2.3, 1.83, ZM), (3.25, 1.83, ZM), edge.but(opacity=0.35), tone(v3(1.0, 0.42, 0.10) * 0.12))
# kick-space shadow under the cabinet
line3(board, view, (2.3, 0.015, ZM), (3.25, 0.015, ZM), fine.but(width=5), black)
# keypad column
kp = quad(view, [(3.03, 0.80, ZM), (3.21, 0.80, ZM), (3.21, 1.68, ZM), (3.03, 1.68, ZM)])
board.tape(kp)
board.fill(kp, Brush(width=8, opacity=0.9, thickness=0.5), scale(mix((black, 2), (ultra, 1), (white, 0.3)), 1.4), angle=np.pi / 2)
board.untape()
board.dry()

# header panel, lit from inside, orange
hq = quad(view, [(2.34, 1.705, ZM), (3.21, 1.705, ZM), (3.21, 1.805, ZM), (2.34, 1.805, ZM)])
board.tape(hq)
orange = mix((cadred, 1.2), (lemon, 1.5), (white, 0.6))
board.fill(hq, Brush(width=9, opacity=0.95, thickness=2.0, pickup=0.3), orange, angle=0,
           color_fn=lambda m: mix((orange, 3), (white, max(0.0, 1.6 - abs(m[0] - (hq[0][0] + hq[1][0]) / 2) / 45))))
board.untape()
board.stage("the cabinet, dark")

# =============================================================================================
# 6. Reflections in the lino, before the chairs go in front of them.
# =============================================================================================
x0m, x1m = P(v3(2.36, 0, ZM))[0], P(v3(3.0, 0, ZM))[0]
yb = P(v3(2.7, 0, ZM))[1]
glow = tone(tube * 0.55)
refl = Brush(width=12, opacity=0.2, pickup=0.0, dryness=0.34, thickness=0.4, jitter=0.1, deplete=0.003, taper=(0.3, 0.5))
xm_ = (x0m + x1m) / 2
for i in range(110):
    x = xm_ + rng.normal(0, (x1m - x0m) * 0.33)
    y0 = yb + rng.uniform(8, 170)
    L = rng.uniform(60, 220)
    k = np.exp(-((y0 + L / 2 - (yb + 150)) / 120) ** 2) * np.exp(-((x - xm_) / ((x1m - x0m) * 0.5)) ** 2)
    board.stroke([(x, y0), (x + rng.normal(0, 2), y0 + L)], refl.but(width=rng.uniform(6, 22), opacity=0.05 + 0.2 * k),
                 scale(glow, rng.uniform(0.45, 0.9)), wobble=1.0)
# far doors and the exit sign, a long way down the corridor floor
fy = P(v3(0, 0, 22))[1]
for i in range(46):
    sx = rng.choice([-1, 1]) * rng.uniform(0.2, 0.66)
    x = P(v3(sx, 0, 22))[0]
    board.stroke([(x, fy + 2), (x + rng.normal(0, 1.5), fy + rng.uniform(30, 120))], refl.but(width=rng.uniform(3, 6), opacity=0.26),
                 scale(mix((white, 4), (lemon, 2), (viridian, 0.8)), rng.uniform(0.25, 0.6)), wobble=0.6)
for i in range(10):
    x = P(v3(rng.uniform(-0.28, 0.28), 0, 22))[0]
    board.stroke([(x, fy + 30), (x, fy + rng.uniform(90, 200))], refl.but(width=3, opacity=0.3), hexc("#1f8a55"))
# drag across to break the streaks, as a mop would
for i in range(44):
    y = rng.uniform(yb + 20, H - 10)
    xa = rng.uniform(x0m - 120, x0m + 40)
    board.stroke([(xa, y), (xa + rng.uniform(160, 420), y + rng.normal(0, 3))],
                 Brush(width=rng.uniform(5, 14), opacity=0.22, pickup=0.9, dryness=0.3, thickness=0.2),
                 tone(A_FLOOR * light(v3(2.7, 0, 4.6), v3(0, 1, 0), True)), wobble=1.5)
# light pooling at the foot of the cabinet
for i in range(30):
    x = rng.uniform(x0m - 30, x1m + 60)
    board.stroke([(x, yb + rng.uniform(1, 9)), (x + rng.uniform(40, 120), yb + rng.uniform(1, 9))],
                 Brush(width=rng.uniform(4, 8), opacity=0.5, dryness=0.3, thickness=1.0, pickup=0), scale(glow, rng.uniform(0.7, 1.1)))
board.dry()
board.stage("the floor gives it back")

# =============================================================================================
# 7. Beam seating, backs to me. And the coat.
# =============================================================================================
def ppt(x, y, z):
    return P(v3(x, y, z))


def rounded(x0, x1, y0, y1, z, r=0.05, n=6):
    pts = []
    for (cx_, cy_, a0) in [(x1 - r, y1 - r, 0), (x0 + r, y1 - r, np.pi / 2), (x0 + r, y0 + r, np.pi), (x1 - r, y0 + r, 1.5 * np.pi)]:
        for a in np.linspace(a0, a0 + np.pi / 2, n):
            pts.append((cx_ + r * np.cos(a), cy_ + r * np.sin(a), z))
    return quad(view, pts)


LFOOT = v3(2.7, 0, ZM)
chair_dark = mix((black, 3), (viridian, 1), (ultra, 1))
rim = mix((white, 10), (viridian, 0.5), (lemon, 1))
beam_y, beam_z = 0.36, 4.1

# shadows the legs throw toward me, fanning away from the foot of the light
for lx in (1.62, 3.48):
    for fz in (3.82, 4.38):
        F = v3(lx, 0.0, fz)
        d = F - LFOOT
        d = d / np.linalg.norm(d)
        for k in range(3):
            line3(board, view, F, F + d * rng.uniform(0.9, 1.6) + v3(rng.normal(0, 0.03), 0, 0),
                  Brush(width=9, opacity=0.4, dryness=0.2, pickup=0.5, thickness=0.2, taper=(0.02, 0.6)), scale(night, 0.45), wobble=1)

# seats first (lit tops), then frame, then backs over them
for i, (xa, xb) in enumerate(CHAIRS):
    sq = quad(view, [(xa + 0.02, SEAT_Y, ZB), (xb - 0.02, SEAT_Y, ZB), (xb - 0.03, SEAT_Y + 0.02, ZF), (xa + 0.03, SEAT_Y + 0.02, ZF)])
    board.tape(sq, feather=0.8)
    board.fill(sq, Brush(width=7, opacity=0.95, thickness=1.6, pickup=0.2), white, angle=0.02,
               color_fn=lambda m, xa=xa, xb=xb: tone(A_SEAT * light(v3((xa + xb) / 2, SEAT_Y, 4.15), v3(0, 0.85, 0.5)) * rng.uniform(0.5, 0.75)))
    board.untape()
board.dry()

frame_b = Brush(width=13, opacity=0.97, thickness=1.0, pickup=0.0, gap=0.0, jitter=0.03, taper=(0.02, 0.02))
line3(board, view, (1.45, beam_y, beam_z), (3.75, beam_y, beam_z), frame_b.but(width=16), scale(chair_dark, 0.8))
line3(board, view, (1.45, beam_y + 0.03, beam_z), (3.75, beam_y + 0.03, beam_z), fine.but(width=2.2, opacity=0.8), scale(rim, 0.55), wobble=0.4)
for lx in (1.62, 3.48):
    line3(board, view, (lx, beam_y, beam_z), (lx, 0.03, beam_z), frame_b.but(width=14), scale(chair_dark, 0.7))
    line3(board, view, (lx, 0.03, 3.88), (lx, 0.03, 4.34), frame_b.but(width=11), scale(chair_dark, 0.7))
    line3(board, view, (lx + 0.022, beam_y - 0.02, beam_z), (lx + 0.022, 0.08, beam_z), fine.but(width=1.8, opacity=0.6), scale(rim, 0.35))
for i, (xa, xb) in enumerate(CHAIRS):
    xm = (xa + xb) / 2
    line3(board, view, (xm, beam_y, beam_z), (xm, SEAT_Y, beam_z), frame_b.but(width=12), scale(chair_dark, 0.7))
    for px_ in (xa + 0.12, xb - 0.12):
        line3(board, view, (px_, SEAT_Y - 0.02, ZB), (px_, BACK0 + 0.03, ZB), frame_b.but(width=7), scale(chair_dark, 0.7))

for i, (xa, xb) in enumerate(CHAIRS):
    bq = rounded(xa + 0.02, xb - 0.02, BACK0, BACK1, ZB)
    board.tape(bq, feather=0.7)
    y_top, y_bot = bq[:, 1].min(), bq[:, 1].max()
    board.fill(bq, Brush(width=16, opacity=0.97, thickness=0.9, pickup=0.25, dryness=0.1), chair_dark, angle=rng.normal(0, 0.06),
               color_fn=lambda m: scale(mix((chair_dark, 3), (A_SEAT, 0.5 + 1.2 * (m[1] - y_top) / (y_bot - y_top))), rng.uniform(0.7, 1.15)))
    board.untape()
    # rim along the top edge, where the light comes over
    top = [ppt(x, BACK1 - 0.004, ZB) for x in np.linspace(xa + 0.06, xb - 0.06, 6)]
    board.stroke(top, fine.but(width=2.6, thickness=1.8, opacity=0.92), scale(rim, rng.uniform(0.75, 1.0)), wobble=0.5)
    xm = (xa + xb) / 2
    if xm < 2.5:    # light is to the right of this chair: rim on its right edge
        board.stroke([ppt(xb - 0.022, y, ZB) for y in np.linspace(BACK1 - 0.05, BACK0 + 0.06, 5)], fine.but(width=2, opacity=0.6), scale(rim, 0.5))
    if xm > 3.0:
        board.stroke([ppt(xa + 0.022, y, ZB) for y in np.linspace(BACK1 - 0.05, BACK0 + 0.06, 5)], fine.but(width=2, opacity=0.6), scale(rim, 0.5))
board.dry()

# the coat over the third chair: an anorak hooked by its hood on one corner of the seat back,
# so everything hangs from that corner and one sleeve has slid along the top
xa, xb = CHAIRS[2]
cl, cr_ = ppt(xa, 0, ZB)[0], ppt(xb, 0, ZB)[0]
cm = (cl + cr_) / 2
ty = ppt(0, BACK1, ZB)[1]
peak = np.array([cl + 34.0, ty - 24.0])
coat = np.array([
    (cl - 8, ty + 6), (cl + 6, ty - 16), peak, (cl + 72, ty - 12), (cm + 12, ty + 16), (cm + 52, ty + 56),
    (cr_ - 28, ty + 86), (cr_ - 6, ty + 124), (cr_ - 20, ty + 150), (cm + 34, ty + 122), (cm + 4, ty + 150),
    (cm - 2, ty + 232), (cm - 28, ty + 250), (cl + 34, ty + 244), (cl + 10, ty + 264), (cl - 18, ty + 252),
    (cl - 26, ty + 150), (cl - 22, ty + 50)])
coat_poly = paths.chaikin(np.vstack([coat, coat[:1]]), 2)
coat_d = mix((cadred, 2.0), (umber, 2), (black, 4.0))
board.tape(coat_poly, feather=0.9)
cloth = Brush(width=16, opacity=0.97, thickness=1.2, pickup=0.5, jitter=0.07, deplete=0.0, gap=0.02, taper=(0.0, 0.0))
board.fill(coat_poly[:-1], cloth, coat_d, angle=np.pi / 2 - 0.12, spacing=6,
           color_fn=lambda m: scale(mix((coat_d, 3), (cadred, 0.1 + 1.5 * max(0.0, (m[1] - ty - 70) / 190))), rng.uniform(0.8, 1.2)))
for i in range(34):   # folds fall away from the corner it hangs by
    a = rng.uniform(0.25, 1.75)
    L = rng.uniform(90, 250)
    e = peak + np.array([np.cos(a), np.sin(a)]) * L
    m = peak + np.array([np.cos(a), np.sin(a)]) * L * 0.5 + np.array([rng.normal(0, 6), 8])
    s0 = peak + np.array([np.cos(a), np.sin(a)]) * rng.uniform(8, 50)
    board.stroke([s0, m, e], cloth.but(width=rng.uniform(3, 8), opacity=0.5, pickup=0.3, taper=(0.15, 0.4)),
                 scale(coat_d, rng.choice([0.4, 0.55, 1.6, 2.0])), wobble=1.5)
# the sleeve that slid along the top keeps its own edge
board.stroke([(cl + 70, ty + 10), (cm + 16, ty + 44), (cm + 50, ty + 84), (cr_ - 24, ty + 128)],
             cloth.but(width=3.5, opacity=0.85, taper=(0.1, 0.2)), scale(coat_d, 0.3), wobble=1)
board.untape()
# light comes over the corner it hangs from and runs a little way down the sleeve
edge_t = paths.chaikin(np.array([coat[0], coat[1], coat[2], coat[3], coat[4], coat[5], coat[6]]), 3)
board.stroke(edge_t[3:-10] + np.array([0.5, 1.8]), fine.but(width=2.8, thickness=1.8, opacity=0.92, taper=(0.15, 0.4)),
             mix((white, 5), (cadred, 1.4), (lemon, 1.6)), wobble=0.5)
board.stroke(edge_t[2:-3] + np.array([0, 5]), fine.but(width=5, opacity=0.45, dryness=0.45, taper=(0.2, 0.5)), mix((cadred, 3), (lemon, 1)), wobble=0.8)
board.dry()
board.stage("seats, and somebody's coat")

# =============================================================================================
# 8. Pull the room down around it: glazes in the corners and along the bottom.
# =============================================================================================
gz = Brush(width=150, bristle=2.6, opacity=0.2, glaze=True, jitter=0.02, gap=0.0, taper=(0.2, 0.2))
deep = mix((ultra, 2), (umber, 1.5))
for i in range(8):
    y = H - rng.uniform(0, 50)
    board.stroke([(rng.uniform(-100, 300), y), (W + 100, y + rng.normal(0, 12))], gz, deep, wobble=6)
for i in range(7):
    x = W - rng.uniform(0, 110)
    board.stroke([(x, 150), (x + rng.normal(0, 20), 820)], gz, deep, wobble=6)
for i in range(6):
    board.stroke([(820 + rng.uniform(0, 100), rng.uniform(240, 330)), (1040, rng.uniform(260, 700))], gz.but(opacity=0.14), deep, wobble=6)
board.dry()

# =============================================================================================
# 9. White last. The window, in one sitting.
# =============================================================================================
wq = quad(view, [(2.36, 0.78, ZM), (3.00, 0.78, ZM), (3.00, 1.68, ZM), (2.36, 1.68, ZM)])
wx0, wy1 = wq[0]
wx1, wy0 = wq[2]
lit_white = mix((white, 14), (viridian, 0.35), (lemon, 0.9))
board.tape(wq, feather=0.6)
board.fill(wq, Brush(width=16, opacity=0.97, thickness=2.4, pickup=0.15, jitter=0.03), lit_white, angle=0.0,
           color_fn=lambda m: scale(lit_white, rng.uniform(0.9, 1.0)))
rows = 5
rh = (wy1 - wy0) / rows
palettes = [
    [hexc("#c8281e"), hexc("#e0b21e"), hexc("#2a59b0"), hexc("#2f8a4a"), hexc("#d86a1c")],   # crisps
    [hexc("#5a2a14"), hexc("#7a1f6a"), hexc("#c8281e"), hexc("#e8dcc0"), hexc("#1d3f8a")],   # bars
    [hexc("#c8281e"), hexc("#111a2a"), hexc("#1f7a3c"), hexc("#e06a1a"), hexc("#d8d8d0")],   # cans
    [hexc("#c8281e"), hexc("#16357a"), hexc("#e8c81e"), hexc("#111a2a"), hexc("#2f8a4a")],   # cans
    [hexc("#3a6a98"), hexc("#5a8a3a"), hexc("#b84a18"), hexc("#3a6a98"), hexc("#8a5a1a")],   # bottles
]
widths = [19, 11, 13, 13, 12]
heights = [0.70, 0.52, 0.56, 0.56, 0.78]
item = Brush(opacity=0.95, thickness=1.8, pickup=0.12, jitter=0.05, gap=0.0, taper=(0.04, 0.04), deplete=0.0)
for r in range(rows):
    base = wy0 + (r + 1) * rh - 5
    x = wx0 + 7 + rng.uniform(0, 4)
    run_col, run_left = None, 0
    while x < wx1 - widths[r] * 0.6 - 4:
        if run_left <= 0:
            run_col = palettes[r][rng.integers(len(palettes[r]))]
            run_left = rng.integers(1, 4)
        run_left -= 1
        if rng.random() < 0.07:     # sold out
            x += widths[r] + 4
            continue
        hpx = rh * heights[r] * rng.uniform(0.92, 1.05)
        wpx = widths[r] * rng.uniform(0.9, 1.08)
        c = scale(run_col, rng.uniform(0.8, 1.1))
        board.stroke([(x + wpx / 2, base), (x + wpx / 2 + rng.normal(0, 0.5), base - hpx)], item.but(width=wpx), scale(c, 0.6), color2=c)
        if rng.random() < 0.7:      # a label, a band, a cap
            yy = base - hpx * rng.uniform(0.3, 0.7)
            board.stroke([(x + 1.5, yy), (x + wpx - 1.5, yy)], item.but(width=rng.uniform(2.5, 5), thickness=1.0),
                         mix((white, 3), (palettes[r][rng.integers(len(palettes[r]))], 1)))
        x += wpx + rng.uniform(3.5, 6)
    # shelf edge and its price tickets
    board.stroke([(wx0 + 2, base + 2.5), (wx1 - 2, base + 2.5)], item.but(width=3.2, thickness=0.8), scale(night, 1.5))
    for tx in np.arange(wx0 + 12, wx1 - 8, 21):
        board.stroke([(tx, base + 2.5), (tx + 6, base + 2.5)], item.but(width=2.2, thickness=1.2), white)
board.untape()
# frame of the window
for a, b in [((2.36, 0.78), (3.00, 0.78)), ((3.00, 0.78), (3.00, 1.68)), ((3.00, 1.68), (2.36, 1.68)), ((2.36, 1.68), (2.36, 0.78))]:
    line3(board, view, (a[0], a[1], ZM), (b[0], b[1], ZM), fine.but(width=2.4), black)

# keypad: the small lights
kx0, kx1 = P(v3(3.03, 0, ZM))[0], P(v3(3.21, 0, ZM))[0]
ky = lambda y: P(v3(3.1, y, ZM))[1]  # noqa: E731
kb = item.but(thickness=1.6)
board.stroke([(kx0 + 8, ky(1.50)), (kx1 - 8, ky(1.50))], kb.but(width=9), hexc("#2a0606"))
board.stroke([(kx0 + 12, ky(1.50)), (kx1 - 16, ky(1.50))], kb.but(width=3.4), hexc("#ff4a2a"))
for r in range(4):
    for c in range(3):
        board.dab(kx0 + 13 + c * 10.5, ky(1.34) + r * 10.5, kb.but(width=4.2), scale(mix((white, 2), (ultra, 1)), 0.34), angle=0, length=4)
board.stroke([(kx0 + 23, ky(1.06)), (kx0 + 23, ky(0.98))], kb.but(width=2.4), scale(rim, 0.5))
board.dab(kx0 + 14, ky(0.90), kb.but(width=4), hexc("#39e07a"), angle=0, length=4)

# last touches of the thickest white, top of each shelf where the tube sits
hot = item.but(thickness=3.2, pickup=0.0)
for r in range(rows):
    yy = wy0 + r * rh + 5.5
    xs = np.sort(rng.uniform(wx0 + 6, wx1 - 30, 4))
    for xs_ in xs:
        board.stroke([(xs_, yy), (xs_ + rng.uniform(14, 40), yy + rng.normal(0, 0.6))], hot.but(width=rng.uniform(4, 6.5)), white)

finish(board, HERE, title="Vending machine, link corridor waiting bay, 04:10", artist="nell-abara", year=2003,
       medium="Oil on hardboard, rough side", made="2026-11-09")
