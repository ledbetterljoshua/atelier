"""Nell Abara - Back stairs, east wing, half-landing, 04:50

Standing on the half-landing at the foot of a flight, a couple of metres back. Eleven risers go up
to the landing outside Ward 9, and the fire door into the ward has a bulkhead over it that is
never switched off. That light falls down the stairs toward me: it catches the front of every
step, stops at every riser, and is nearly gone by the time it reaches the floor I am standing on.
Someone has left a cup on a step.
"""
import os
import sys
from pathlib import Path

import numpy as np
from scipy.spatial import ConvexHull

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[3]))
sys.path.insert(0, str(HERE.parents[1]))

from engine import Board, Brush, ground, hexc, mix, scale  # noqa: E402
from engine.studio import finish  # noqa: E402
from tools import Flight, Patches, Plane, View, in_the_way, keyed, lay, line3, quad, room, sweep, v3  # noqa: E402

W, H = 1050, 1500
rng0 = np.random.default_rng(450)
board = Board(W, H, hexc("#0b0a0a"), ground.hardboard_mesh(W, H, rng0, pitch=5.2), seed=2008, light=(-0.12, -0.95))
rng = board.rng
view = View(W, H, 955, 560, 592, (0.2, 1.55, 0))
P = view.P

# --- tubes -----------------------------------------------------------------------------------
black, ultra, umber = hexc("#0b0a0a"), hexc("#1b2a7a"), hexc("#4a2a16")
viridian, ochre, cadred = hexc("#0f6b55"), hexc("#c0902f"), hexc("#c6281c")
lemon, white = hexc("#efe36a"), hexc("#f6f3ea")
night = mix((ultra, 2), (umber, 1), (black, 2))

# --- what the surfaces are -------------------------------------------------------------------
A_WALL = mix((white, 5), (viridian, 0.22), (ultra, 0.08), (ochre, 0.25))   # pale hospital green over blockwork
A_DADO = mix((white, 1.4), (viridian, 0.35), (ultra, 0.25), (umber, 0.6))    # darker gloss, to the rail
A_CEIL = mix((white, 4), (umber, 0.6))
A_VINYL = mix((white, 2.2), (ultra, 0.3), (umber, 0.6), (black, 0.35))  # grey stair vinyl, flecked
A_STRIP = mix((lemon, 3), (ochre, 1.2))                            # the contrasting nosing insert
A_ALU = mix((white, 5), (ultra, 0.15), (umber, 0.2))
A_DOOR = mix((white, 3), (ochre, 1.1), (umber, 0.6), (cadred, 0.08))   # beech veneer fire door
A_FRAME = mix((white, 2), (umber, 0.6), (ultra, 0.3), (black, 0.25))     # frame, painted grey
A_RAIL = mix((white, 1.2), (ultra, 0.3), (umber, 0.4))

UP, DOWN, EAST, WEST, BACK, FRONT = v3(0, 1, 0), v3(0, -1, 0), v3(1, 0, 0), v3(-1, 0, 0), v3(0, 0, -1), v3(0, 0, 1)

# --- the stair ---------------------------------------------------------------------------------
XL, XR = -0.65, 0.65
fl = Flight(XL, XR, z0=2.4, rise=0.17, going=0.26, n=11, z_end=6.4)
ZB = fl.z_end                              # the back wall, with the fire door in it
YL = fl.y0 + fl.n * fl.r                   # the landing
YC_LO, Z_SLAB = 2.75, 2.2                  # the half-landing's ceiling, and where the slab stops
YC_HI = YL + 2.70

# the rail on the left wall, 900 above the nosings, running on 300 past the top one
RX, RR = XL + 0.07, 0.024


def rail_y(z):
    return np.where(z < fl.z_head, fl.pitch_y(np.minimum(z, fl.z_head)) + 0.9, YL + 0.9)


# the fire door and the light over it
DX0, DX1, DY1 = -0.55, 0.37, YL + 2.05
LX, LY, LW, LH, LD = (DX0 + DX1) / 2, DY1 + 0.26, 0.42, 0.16, 0.09

# a paper cup on the sixth step, by the right-hand wall
CUP_K = 6
CX, CZ, CRAD, CH = 0.43, fl.z0 + (CUP_K - 1) * fl.g + 0.09, 0.037, 0.095
CY = fl.y0 + CUP_K * fl.r


def solid(X, Y, Z):
    s = fl.solid(X, Y, Z)
    s |= ((X - CX) ** 2 + (Z - CZ) ** 2 < CRAD ** 2) & (Y > CY) & (Y < CY + CH)
    return s


def occlude(S, Q):
    """The steps in the way, the cup, and the rail (thin, so worked out where the ray crosses it)."""
    out = in_the_way(S, Q, solid)
    if Q[0] < RX:
        t = (RX - Q[0]) / (S[:, 0] - Q[0])
        y = Q[1] + t * (S[:, 1] - Q[1])
        z = Q[2] + t * (S[:, 2] - Q[2])
        hit = (t > 0) & (t < 1) & (z > fl.z0 - 0.3) & (z < fl.z_head + 0.3) & (np.abs(y - rail_y(z)) < RR)
        out = np.where(hit, 0.0, out)
    return out


# --- what is lit: an opal diffuser, its face and its underside ---------------------------------
tube = mix((white, 10), (viridian, 0.45), (lemon, 1.1))
tube = tube / tube.max()
R = 30.0
lrng = np.random.default_rng(9)
face = Plane((LX - LW / 2, LY - LH / 2, ZB - LD), (LW, 0, 0), (0, LH, 0))
under = Plane((LX - LW / 2, LY - LH / 2, ZB - LD), (LW, 0, 0), (0, 0, LD))
lamp = (Patches.on(face, tube * R, 6, 3, facing=BACK, rng=lrng, occlude=occlude)
        + Patches.on(under, tube * R * 0.8, 6, 2, facing=DOWN, rng=lrng))


def amb(N):
    """The stairwell below, through the gaps: next to nothing."""
    return v3(0.0016, 0.0019, 0.0026) * (1.0 + 0.5 * max(0.0, N[1]))


# what the lit surfaces throw back
wall_l = Plane((XL, 0, 0.5), (0, 0, ZB - 0.5), (0, YC_HI, 0))
wall_r = Plane((XR, 0, 0.5), (0, 0, ZB - 0.5), (0, YC_HI, 0))
wall_b = Plane((XL, YL, ZB), (XR - XL, 0, 0), (0, YC_HI - YL, 0))
land = fl.tread(fl.n)


def wall_alb(Q):
    return A_DADO if Q[1] < fl.pitch_y(min(Q[2], fl.z_head)) + 0.9 and Q[1] < (YL + 0.9 if Q[2] > fl.z_head else 9) else A_WALL


bounce = Patches.on(land, lambda S: lamp.onto(S, UP) * A_VINYL, 6, 5, facing=UP)
bounce = bounce + Patches.on(wall_b, lambda S: lamp.onto(S, BACK) * A_WALL, 6, 6, facing=BACK)
for k in range(5, fl.n):
    bounce = bounce + Patches.on(fl.tread(k), lambda S: lamp.onto(S, UP) * A_VINYL, 4, 1, facing=UP)
bounce = bounce + Patches.on(Plane((XL, 1.0, 3.0), (0, 0, ZB - 3.0), (0, YC_HI - 1.0, 0)),
                             lambda S: lamp.onto(S, EAST) * wall_alb(S), 8, 4, facing=EAST)
bounce = bounce + Patches.on(Plane((XR, 1.0, 3.0), (0, 0, ZB - 3.0), (0, YC_HI - 1.0, 0)),
                             lambda S: lamp.onto(S, WEST) * wall_alb(S), 8, 4, facing=WEST)
KB = 0.6


def light(Q, N):
    return amb(N) + lamp.onto(Q, N) + KB * bounce.onto(Q, N)


# the room is keyed once, on the front of the seventh step; the lamp alone gets white
EXPO = keyed(light, (v3(0.0, 7 * fl.r, fl.z0 + 6 * fl.g + 0.03), UP, A_VINYL), target=0.045)


def shade_at(Q, N, albedo, vary=0.0):
    a = albedo(Q) if callable(albedo) else albedo
    return room(a * light(Q, N) * EXPO) * (np.exp(rng.normal(0, vary)) if vary else 1.0)


def shader(albedo, N, vary=0.05):
    N = v3(*N)
    return lambda Q: shade_at(Q, N, albedo, vary)


def lum(c):
    return 0.2 * c[0] + 0.7 * c[1] + 0.1 * c[2]


if os.environ.get("CHECK"):
    print("EXPO", EXPO)
    for name, Q, N, a in [("door top", v3(LX, DY1 - 0.15, ZB), BACK, A_DOOR), ("door foot", v3(LX, YL + 0.3, ZB), BACK, A_DOOR),
                          ("wall by door", v3(DX1 + 0.12, DY1, ZB), BACK, A_WALL), ("landing", v3(0, YL, 5.6), UP, A_VINYL),
                          ("tread 10 front", v3(0, 1.7, fl.z0 + 9 * fl.g + 0.03), UP, A_VINYL),
                          ("tread 10 back", v3(0, 1.7, fl.z0 + 9 * fl.g + 0.22), UP, A_VINYL),
                          ("tread 3 front", v3(0, 0.51, fl.z0 + 2 * fl.g + 0.03), UP, A_VINYL),
                          ("tread 3 back", v3(0, 0.51, fl.z0 + 2 * fl.g + 0.22), UP, A_VINYL),
                          ("tread 1", v3(0, 0.17, fl.z0 + 0.05), UP, A_VINYL),
                          ("riser 8", v3(0, 1.45, fl.z0 + 8 * fl.g), BACK, A_VINYL),
                          ("half-landing", v3(0, 0, 2.0), UP, A_VINYL), ("left wall top", v3(XL, 3.0, 5.8), EAST, A_WALL),
                          ("left wall mid", v3(XL, 2.0, 3.6), EAST, A_WALL), ("left wall low", v3(XL, 1.0, 2.2), EAST, A_DADO),
                          ("right wall mid", v3(XR, 2.0, 3.6), WEST, A_WALL), ("ceiling hi", v3(0, YC_HI, 5.6), DOWN, A_CEIL),
                          ("ceiling lo", v3(0, YC_LO, 2.0), DOWN, A_CEIL)]:
        print(f"{name:16s}", np.round(room(a * light(Q, N) * EXPO), 3))
    for nm, p in [("lamp", v3(LX, LY, ZB - LD)), ("door top", v3(DX0, DY1, ZB)), ("door foot", v3(DX1, YL, ZB)),
                  ("landing edge L", v3(XL, YL, fl.z_head)), ("foot of flight L", v3(XL, 0, fl.z0)),
                  ("foot of flight R", v3(XR, 0, fl.z0)), ("slab edge", v3(0, YC_LO, Z_SLAB)), ("cup", v3(CX, CY, CZ))]:
        print(nm, np.round(P(p), 1))
    sys.exit()

# --- the room's planes ------------------------------------------------------------------------
ceil_hi = Plane((XL, YC_HI, Z_SLAB), (XR - XL, 0, 0), (0, 0, ZB - Z_SLAB))
ceil_lo = Plane((XL, YC_LO, 0.6), (XR - XL, 0, 0), (0, 0, Z_SLAB - 0.6))
half = Plane((XL, 0, 0.6), (XR - XL, 0, 0), (0, 0, fl.z0 - 0.6))
PITCH = v3(0, fl.r, fl.g)
PITCH = PITCH / np.linalg.norm(PITCH)
EYE_Y = view.eye[1]


# =============================================================================================
# 1. Imprimatura. Thin coloured darks over the black; warmer up where the light will be.
# =============================================================================================
wash = Brush(width=120, bristle=2.6, opacity=0.5, dryness=0.42, pickup=0.3, thickness=0.2, jitter=0.12, deplete=0.0008)
for i in range(90):
    x, y = rng.uniform(-100, W + 100), rng.uniform(-50, H + 50)
    a = rng.normal(np.pi / 2, 0.5)
    L = rng.uniform(300, 700)
    warm = np.exp(-((x - 520) / 300) ** 2 - ((y - 330) / 300) ** 2)
    c = mix((ultra, rng.uniform(1, 3) * (1 - 0.6 * warm)), (umber, rng.uniform(0.5, 2.0) + 2 * warm), (black, 2.5))
    board.stroke([(x - np.cos(a) * L / 2, y - np.sin(a) * L / 2), (x + np.cos(a) * L / 2, y + np.sin(a) * L / 2)],
                 wash, c, wobble=10)
board.dry()
board.stage("coloured darks over black")

# =============================================================================================
# 2. The dark, one broad dry brush, long. Walls run with the stair; the strokes carry the light
#    down them as they go instead of being cut up into values.
# =============================================================================================
dark = Brush(width=54, bristle=2.0, opacity=0.6, pickup=0.6, dryness=0.4, thickness=0.3, jitter=0.05, deplete=0.0006,
             taper=(0.1, 0.15))


def even(z0, z1):
    """Depth at t, spaced so the strokes come out evenly across the board."""
    return lambda t: 1.0 / (1.0 / z0 + t * (1.0 / z1 - 1.0 / z0))


def wall_top(z):
    return YC_LO if z < Z_SLAB else YC_HI


# the ceiling over me and the floor I stand on: rows right across, wall to wall
zt = even(1.0, Z_SLAB)
board.tape(ceil_lo.screen_poly(view), feather=1.0)
sweep(board, view, lambda t: v3(XL - 0.1, YC_LO, zt(t)), lambda t: v3(XR + 0.1, YC_LO, zt(t)), 6, dark,
      shader(A_CEIL, DOWN, 0.03), along=4, wobble=3)
zf_ = even(1.2, fl.z0 + 0.1)
board.tape(half.screen_poly(view), feather=1.0)
sweep(board, view, lambda t: v3(XL - 0.1, 0, zf_(t)), lambda t: v3(XR + 0.1, 0, zf_(t)), 13, dark.but(dryness=0.5),
      shader(A_VINYL, UP, 0.03), along=5, wobble=3)
# the walls: upright, floor to ceiling, each stroke carrying the light down it as it goes
zw = even(0.62, ZB)
wallb = dark.but(bristle=2.6, jitter=0.02, dryness=0.45)
for X, N, wall in ((XL, EAST, wall_l), (XR, WEST, wall_r)):
    board.tape(wall.screen_poly(view), feather=1.0)
    sweep(board, view, lambda t: v3(X, -0.2, zw(t)), lambda t: v3(X, wall_top(zw(t)) + 0.1, zw(t)), 70, wallb,
          shader(wall_alb, N, 0.01), along=7, wobble=0.5, max_w=120)
    # then across it, dry, with the pitch of the stair: it only finds the high spots of the mesh
    lay(board, view, wall, wallb.but(dryness=0.62, opacity=0.45, width=40), shader(wall_alb, N, 0.01), PITCH, length=360,
        cover=1.4, zref=3.0, shrink=0.5, wobble=2, along=4, tape=False)
zc = even(4.6, ZB)
board.tape(ceil_hi.screen_poly(view), feather=1.0)
sweep(board, view, lambda t: v3(XL - 0.1, YC_HI, zc(t)), lambda t: v3(XR + 0.1, YC_HI, zc(t)), 10, dark.but(dryness=0.25),
      shader(A_CEIL, DOWN, 0.02), along=5, wobble=1)
board.tape(wall_b.screen_poly(view), feather=1.0)
sweep(board, view, lambda t: v3(XL - 0.05 + t * (XR - XL + 0.1), YL - 0.1, ZB), lambda t: v3(XL - 0.05 + t * (XR - XL + 0.1), YC_HI + 0.1, ZB),
      24, dark.but(width=20), shader(A_WALL, BACK, 0.02), along=7, wobble=1)
board.untape()
board.dry()
board.stage("the dark, one brush")

# =============================================================================================
# 3. The walls where the light comes down them: a smaller brush, wetter, over the top half.
# =============================================================================================
fine = Brush(width=3, bristle=0.9, opacity=0.85, pickup=0.0, thickness=0.6, jitter=0.03, gap=0.0, taper=(0.03, 0.05))
blk = Brush(width=18, opacity=0.8, pickup=0.65, dryness=0.3, thickness=0.5, jitter=0.03, deplete=0.0009)
for X, N, wall in ((XL, EAST, wall_l), (XR, WEST, wall_r)):
    board.tape(wall.screen_poly(view), feather=1.0)
    sweep(board, view, lambda t: v3(X, float(fl.pitch_y(min(zw(t), fl.z_head))) - 0.2, zw(t)),
          lambda t: v3(X, wall_top(zw(t)) + 0.1, zw(t)), 110, blk, shader(wall_alb, N, 0.02), along=7, wobble=0.4,
          max_w=60, where=lambda t: lum(shade_at(v3(X, 3.0, zw(t)), N, A_WALL)) > 0.05)
board.tape(ceil_hi.screen_poly(view), feather=1.0)
sweep(board, view, lambda t: v3(XL - 0.1, YC_HI, zc(t)), lambda t: v3(XR + 0.1, YC_HI, zc(t)), 16, blk,
      shader(A_CEIL, DOWN, 0.02), along=7)
board.untape()
board.dry()
scm = Brush(width=16, opacity=0.8, pickup=0.1, dryness=0.55, thickness=0.9, jitter=0.04, deplete=0.0015)
# drier and thicker where most light lands, so the mesh shows through the paint and not round it
for X, N, wall in ((XL, EAST, wall_l), (XR, WEST, wall_r)):
    board.tape(wall.screen_poly(view), feather=1.0)
    sweep(board, view, lambda t: v3(X, float(fl.pitch_y(min(zw(t), fl.z_head))) + 0.3, zw(t)),
          lambda t: v3(X, wall_top(zw(t)) + 0.1, zw(t)), 80, scm.but(jitter=0.02), shader(wall_alb, N, 0.02), along=7,
          max_w=40, where=lambda t: lum(shade_at(v3(X, 3.2, zw(t)), N, A_WALL)) > 0.12)
    # block courses, only where the light is low enough across the wall to find them
    for yc in np.arange(0.225, YC_HI, 0.225):
        zs = [z for z in np.linspace(2.6, ZB - 0.02, 40) if yc > fl.pitch_y(min(z, fl.z_head)) + 0.05]
        zs = [z for z in zs if lum(shade_at(v3(X, yc, z), N, A_WALL)) > 0.07]
        if len(zs) < 3:
            continue
        pts = np.array([v3(X, yc, z) for z in zs])
        board.stroke(P(pts), fine.but(width=1.2, opacity=0.35, pickup=0.3),
                     [scale(shade_at(q, N, wall_alb), 0.75) for q in pts[:: max(1, len(pts) // 5)]], smooth=False)
board.untape()
# the dado line: where the gloss stops, level with the rail
for x, N in ((XL + 0.002, EAST), (XR - 0.002, WEST)):
    zs = np.linspace(0.9, ZB, 40)
    pts = np.array([v3(x, float(rail_y(z)) - 0.003, z) for z in zs])
    board.stroke(P(pts), fine.but(width=2.4, opacity=0.6), [scale(shade_at(q, N, A_DADO), 0.7) for q in pts[::5]], smooth=False)
board.dry()
board.stage("the walls, with the stair")

# =============================================================================================
# 4. The landing: the back wall round the door, then the door, its glass and its furniture.
# =============================================================================================
FR = 0.05
door_q = [v3(DX0 - FR, YL, ZB), v3(DX1 + FR, YL, ZB), v3(DX1 + FR, DY1 + FR, ZB), v3(DX0 - FR, DY1 + FR, ZB)]
board.tape(wall_b.screen_poly(view), feather=0.8)
board.tape(quad(view, door_q), mode="cut", feather=0.5)
sweep(board, view, lambda t: v3(XL - 0.05 + t * (XR - XL + 0.1), YL - 0.1, ZB), lambda t: v3(XL - 0.05 + t * (XR - XL + 0.1), YC_HI + 0.1, ZB),
      44, blk.but(width=8), shader(A_WALL, BACK, 0.02), along=9, wobble=0.5)
board.untape()
# the frame
board.tape(quad(view, door_q), feather=0.5)
board.tape(quad(view, [v3(DX0, YL, ZB), v3(DX1, YL, ZB), v3(DX1, DY1, ZB), v3(DX0, DY1, ZB)]), mode="cut", feather=0.4)
body = Brush(width=6, opacity=0.95, pickup=0.35, dryness=0.12, thickness=0.6, jitter=0.04, deplete=0.0005)
for x in np.linspace(DX0 - FR, DX1 + FR, 26):
    pts = [v3(x, YL, ZB - 0.01), v3(x, DY1 + FR, ZB - 0.01)]
    board.stroke(P(np.array(pts)), body, [shade_at(v3(x, y, ZB - 0.01), BACK, A_FRAME) for y in np.linspace(YL, DY1 + FR, 5)])
for y in np.linspace(DY1, DY1 + FR, 3):
    pts = [v3(DX0 - FR, y, ZB - 0.01), v3(DX1 + FR, y, ZB - 0.01)]
    board.stroke(P(np.array(pts)), body, shade_at(v3(LX, y, ZB - 0.01), BACK, A_FRAME))
board.untape()
# the leaf: veneer, upright, each stroke running from the light at the head down into the dark
door = Plane((DX0, YL, ZB - 0.012), (DX1 - DX0, 0, 0), (0, DY1 - YL, 0))
board.tape(door.screen_poly(view), feather=0.4)
# one long wet pass the height of the leaf, then a few drier ones that leave the grain
sweep(board, view, lambda t: v3(DX0 - 0.02 + t * (DX1 - DX0 + 0.04), DY1 + 0.03, ZB - 0.012),
      lambda t: v3(DX0 - 0.02 + t * (DX1 - DX0 + 0.04), YL - 0.05, ZB - 0.012), 16,
      body.but(opacity=0.9, pickup=0.7, dryness=0.05, jitter=0.012, gap=0.0), shader(A_DOOR, BACK, 0.01), along=8, overlap=1.8)
veneer = body.but(width=3.0, opacity=0.5, pickup=0.5, dryness=0.35, jitter=0.015, gap=0.02)
for i in range(26):
    x = rng.uniform(DX0, DX1)
    y0 = DY1 + 0.02 if rng.random() < 0.6 else rng.uniform(YL + 0.6, DY1)
    ys = np.linspace(y0, max(YL - 0.05, y0 - rng.uniform(0.6, 2.2)), 6)
    pts = np.array([v3(x + rng.normal(0, 0.002), y, ZB - 0.012) for y in ys])
    board.stroke(P(pts), veneer, [shade_at(q, BACK, A_DOOR, 0.02) for q in pts], wobble=0.2)
board.untape()
# the vision panel: wired glass, the ward corridor dark behind it, laid flat
GX0, GX1, GY0, GY1 = 0.05, 0.23, YL + 1.0, YL + 1.68
gq = quad(view, [v3(GX0, GY0, ZB - 0.013), v3(GX1, GY0, ZB - 0.013), v3(GX1, GY1, ZB - 0.013), v3(GX0, GY1, ZB - 0.013)])
board.tape(gq, feather=0.4)
glass = Brush(width=6, opacity=0.95, pickup=0.4, dryness=0.0, thickness=0.1, jitter=0.02, gap=0.0, level=1.0, taper=(0.05, 0.05))
for x in np.linspace(GX0, GX1, 5):
    # dark corridor behind; the glass gives back a little of the lit wall above, more toward its head
    ys = np.linspace(GY1 + 0.02, GY0 - 0.02, 5)
    board.stroke(P(np.array([v3(x, ys[0], ZB), v3(x, ys[-1], ZB)])), glass.but(width=0.06 * view.ppm(ZB)),
                 [mix((night, 3), (ultra, 0.3)) * (0.35 + 0.5 * ((y - GY0) / (GY1 - GY0)) ** 2) for y in ys])
# the wire, catching what little the glass gets from above
for i in range(-6, 8):
    for sgn in (1, -1):
        x0 = GX0 + i * 0.04
        a, b = v3(x0, GY0, ZB - 0.014), v3(x0 + sgn * (GY1 - GY0), GY1, ZB - 0.014)
        board.stroke(P(np.array([a, b])), fine.but(width=0.8, opacity=0.14), scale(shade_at(v3(LX, GY1, ZB), BACK, A_ALU), 0.35),
                     smooth=False)
board.untape()
line3(board, view, v3(GX0, GY1 + 0.008, ZB - 0.014), v3(GX1, GY1 + 0.008, ZB - 0.014), fine.but(width=2.4),
      shade_at(v3(LX, GY1 + 0.01, ZB - 0.02), BACK, A_FRAME) * 1.3)
# push plate, and the blue FIRE DOOR KEEP SHUT disc
pq = quad(view, [v3(0.26, YL + 0.95, ZB - 0.015), v3(0.335, YL + 0.95, ZB - 0.015), v3(0.335, YL + 1.30, ZB - 0.015),
                 v3(0.26, YL + 1.30, ZB - 0.015)])
board.tape(pq, feather=0.3)
for x in np.linspace(0.26, 0.335, 5):
    pts = np.array([v3(x, YL + 1.31, ZB - 0.015), v3(x, YL + 0.94, ZB - 0.015)])
    board.stroke(P(pts), fine.but(width=3), [shade_at(q, BACK, A_ALU) * 1.4 for q in pts])
board.untape()
sc = P(v3(-0.30, YL + 1.52, ZB - 0.015))
rr = 0.055 * view.ppm(ZB)
blue = mix((ultra, 3), (white, 0.5))
for k in range(5):
    board.dab(sc[0] + rng.normal(0, 0.6), sc[1] + rng.normal(0, 0.6), Brush(width=rr * 1.6, opacity=0.9, thickness=0.7, gap=0),
              shade_at(v3(-0.3, YL + 1.52, ZB - 0.015), BACK, blue), angle=np.pi / 2 + rng.normal(0, 0.3), length=rr * 0.5)
for yy in (-0.3, 0.0, 0.3):
    board.stroke([sc + (-rr * 0.55, rr * yy), sc + (rr * 0.55, rr * yy)], fine.but(width=1.1, opacity=0.6),
                 shade_at(v3(-0.3, YL + 1.52, ZB - 0.015), BACK, white))
# the closer arm at the head of the door
ca, cb = v3(DX1 - 0.08, DY1 - 0.06, ZB - 0.06), v3(DX0 + 0.35, DY1 - 0.03, ZB - 0.08)
line3(board, view, ca, cb, fine.but(width=5), scale(night, 0.5))
line3(board, view, ca + v3(0, 0.012, 0), cb + v3(0, 0.012, 0), fine.but(width=1.6), shade_at(ca, UP, A_ALU))
cq = quad(view, [v3(DX1 - 0.32, DY1 - 0.09, ZB - 0.05), v3(DX1 - 0.05, DY1 - 0.09, ZB - 0.05), v3(DX1 - 0.05, DY1 - 0.03, ZB - 0.05),
                 v3(DX1 - 0.32, DY1 - 0.03, ZB - 0.05)])
board.tape(cq, feather=0.3)
for y in np.linspace(DY1 - 0.09, DY1 - 0.03, 4):
    board.stroke(P(np.array([v3(DX1 - 0.33, y, ZB - 0.05), v3(DX1 - 0.04, y, ZB - 0.05)])), fine.but(width=3),
                 shade_at(v3(DX1 - 0.2, y, ZB - 0.05), BACK, A_ALU))
board.untape()
board.dry()
board.stage("the landing and the fire door")

# =============================================================================================
# 5. The flight, from the top down. Each riser one dry stroke or two across; each tread laid in
#    rows across, mixed along the row, so the light at the front of a step and the riser's shadow
#    at the back of it come out of the stair and not out of me.
# =============================================================================================
stepb = Brush(width=10, opacity=0.9, pickup=0.45, dryness=0.3, thickness=0.5, jitter=0.05, deplete=0.0006, taper=(0.04, 0.06))
xs_along = np.linspace(XL, XR, 6)
for k in range(fl.n - 1, -1, -1):
    # riser k
    rz = fl.z0 + k * fl.g
    ry0, ry1 = fl.y0 + k * fl.r, fl.y0 + (k + 1) * fl.r
    rq = quad(view, [v3(XL, ry0, rz), v3(XR, ry0, rz), v3(XR, ry1, rz), v3(XL, ry1, rz)])
    hpx = abs(rq[2][1] - rq[1][1])
    board.tape(rq, feather=0.4)
    nrow = max(1, int(hpx / 9))
    for y in np.linspace(ry0, ry1, nrow + 2)[1:-1]:
        pts = np.array([v3(XL - 0.05, y, rz - 0.001), v3(XR + 0.05, y, rz - 0.001)])
        board.stroke(P(pts), stepb.but(width=hpx / nrow * 1.7, dryness=0.42), [shade_at(v3(x, y, rz - 0.002), BACK, A_VINYL, 0.04)
                                                                              for x in xs_along], wobble=0.5)
    board.untape()
    # tread k (only the ones below my eye show their tops)
    tk = k
    if 1 <= tk < fl.n and fl.y0 + tk * fl.r < EYE_Y - 0.01:
        ty = fl.y0 + tk * fl.r
        zf, zb = fl.z0 + (tk - 1) * fl.g, fl.z0 + tk * fl.g
        tq = quad(view, [v3(XL, ty, zf), v3(XR, ty, zf), v3(XR, ty, zb), v3(XL, ty, zb)])
        hpx = abs(tq[0][1] - tq[3][1])
        board.tape(tq, feather=0.4)
        nrow = max(2, int(hpx / 5))
        for v in np.linspace(0, 1, nrow + 2)[1:-1]:
            z = zf + 0.03 + (zb - zf - 0.03) * v
            pts = np.array([v3(XL - 0.05, ty, z), v3(XR + 0.05, ty, z)])
            xs = np.linspace(XL, XR, 12)
            board.stroke(P(pts), stepb.but(width=max(3.0, hpx / nrow * 1.8)), [shade_at(v3(x, ty, z), UP, A_VINYL, 0.03) for x in xs],
                         wobble=0.4)
        board.untape()
board.dry()
board.stage("the flight, step by step")

# =============================================================================================
# 6. Where the light catches: the nosing on every step, the rail, and the rail's shadow.
# =============================================================================================
NOSE_D = 0.045                       # how far back the yellow insert runs on the tread
UPFRONT = v3(0, 0.6, -0.8)           # the rounded lip, facing me and a little up
for k in range(fl.n, 0, -1):
    ty, zf = fl.nosing(k)
    xs = np.linspace(XL + 0.03, XR - 0.03, 18)
    if ty < EYE_Y - 0.01:
        # the insert, seen from above, mixed all along the step so the cup's shadow can cross it
        a, b = v3(XL + 0.02, ty + 0.002, zf + NOSE_D / 2), v3(XR - 0.02, ty + 0.002, zf + NOSE_D / 2)
        sw = abs(P(v3(0, ty, zf))[1] - P(v3(0, ty, zf + NOSE_D))[1])
        board.stroke(P(np.array([a, b])), fine.but(width=max(1.6, sw * 1.1), opacity=0.92, thickness=1.0, pickup=0.1),
                     [shade_at(v3(x, ty, zf + 0.02), UP, A_STRIP, 0.03) for x in xs], wobble=0.2)
    # the aluminium lip, front on
    a, b = v3(XL + 0.01, ty - 0.008, zf - 0.004), v3(XR - 0.01, ty - 0.008, zf - 0.004)
    lw = max(1.2, 0.018 * view.ppm(zf))
    board.stroke(P(np.array([a, b])), fine.but(width=lw, opacity=0.85, thickness=0.8),
                 [shade_at(v3(x, ty - 0.008, zf - 0.004), UPFRONT, A_ALU) * 1.3 for x in xs], wobble=0.15)
board.dry()
# the rail: a dark tube, lit along its top where it faces up the stairs, and its brackets
zs = np.concatenate([np.linspace(1.2, fl.z_head, 40), np.linspace(fl.z_head + 0.03, fl.z_head + 0.3, 4)])
rail = np.array([v3(RX, float(rail_y(z)), z) for z in zs])
for z in (1.7, 2.9, 4.1, fl.z_head + 0.26):
    q = v3(RX, float(rail_y(z)) - RR, z)
    line3(board, view, q + v3(-0.07, -0.04, 0), q, fine.but(width=max(1.5, 0.016 * view.ppm(z)), opacity=0.9), scale(night, 0.5))
for j0 in range(0, len(zs) - 1, 4):
    seg = rail[j0:j0 + 5]
    w = max(2.0, 2 * RR * view.ppm(seg[len(seg) // 2][2]))
    board.stroke(P(seg), fine.but(width=w, opacity=0.95, taper=(0, 0)), shade_at(seg[0], v3(0.3, -0.6, -0.5), A_RAIL), smooth=False)
for j0 in range(0, len(zs) - 1, 4):
    seg = rail[j0:j0 + 5]
    w = max(2.0, 2 * RR * view.ppm(seg[len(seg) // 2][2]))
    scr = P(seg)
    d = scr[-1] - scr[0]
    nrm = np.array([d[1], -d[0]]) / (np.hypot(*d) + 1e-9)
    nrm = nrm if nrm[1] < 0 else -nrm                    # toward the top of the board
    board.stroke(scr + nrm * w * 0.28, fine.but(width=max(1.0, w * 0.3), opacity=0.9, thickness=1.2, taper=(0, 0)),
                 [shade_at(q, v3(0.3, 0.75, 0.6), A_RAIL) * 1.5 for q in seg[::2]], smooth=False)
# its shadow on the wall: where the lamp, through the rail, lands on the wall. Glazed, soft-edged,
# as dark as the light it takes away.
Lc = v3(LX, LY - LH / 2, ZB - LD)
sh = []
for z in np.linspace(1.0, fl.z_head + 0.3, 50):
    Rq = v3(RX, float(rail_y(z)), z)
    t = (XL + 0.001 - Lc[0]) / (Rq[0] - Lc[0])
    sh.append(Lc + t * (Rq - Lc))
sh = np.array([q for q in sh if 0.9 < q[2] < ZB - 0.05])
sgz = Brush(width=8, bristle=1.6, opacity=0.6, glaze=True, jitter=0.02, gap=0.0, taper=(0.1, 0.1))
for j in range(0, len(sh) - 3, 3):
    q = sh[j:j + 4]
    lit = lum(shade_at(q[1], EAST, A_WALL))
    board.stroke(P(q), sgz.but(width=max(3.0, 0.045 * view.ppm(q[1][2])), opacity=min(0.7, 2.0 * lit)),
                 mix((ultra, 1.2), (umber, 2), (black, 1)), smooth=False)
board.dry()
board.stage("where the light catches")

# =============================================================================================
# 7. What was left: a cup on the sixth step. Lit from behind; its shadow comes down at me.
# =============================================================================================
deep_shadow = mix((ultra, 1.5), (umber, 2), (black, 1))
for i in range(90):
    Q = v3(CX + rng.uniform(-0.12, 0.12), CY + 0.001, rng.uniform(fl.nosing(CUP_K)[1], CZ))
    if (Q[0] - CX) ** 2 + (Q[2] - CZ) ** 2 < CRAD ** 2:
        continue
    full = lum(room(A_VINYL * lamp.onto(Q + v3(0, 0.2, 0), UP) * EXPO))
    k = 1 - lum(shade_at(Q, UP, A_VINYL)) / max(full, 1e-6)
    if k < 0.3:
        continue
    d = Q - v3(CX, CY, CZ)
    d = d / (np.linalg.norm(d) + 1e-9)
    line3(board, view, Q - d * 0.01, Q + d * 0.02, sgz.but(width=2.5, opacity=0.5 * k), deep_shadow)
cprof = [(0.0, 0.026), (CH, CRAD)]
ppm = view.ppm(CZ)
left = [P(v3(CX - r, CY + y, CZ)) for y, r in cprof]
right = [P(v3(CX + r, CY + y, CZ)) for y, r in cprof]
board.tape(np.array(left + right[::-1]), feather=0.4)
A_CUP = mix((white, 6), (ochre, 0.3))
for a in np.linspace(np.pi, 2 * np.pi, 10):
    N = v3(np.cos(a), 0, np.sin(a))
    pts = np.array([v3(CX + r * np.cos(a), CY + y, CZ + r * np.sin(a)) for y, r in cprof])
    board.stroke(P(pts), Brush(width=0.25 * CRAD * ppm, opacity=0.95, thickness=0.7, pickup=0.3, gap=0, taper=(0.02, 0.02)),
                 [shade_at(q, N, A_CUP) for q in pts])
board.untape()
# the rim, seen from just above: the far half of it catches the lamp, the coffee is dark
rim = np.array([v3(CX + CRAD * np.cos(a), CY + CH, CZ + CRAD * np.sin(a)) for a in np.linspace(0, 2 * np.pi, 40)])
board.tape(P(rim), feather=0.3)
board.fill(P(rim), fine.but(width=2.2), mix((umber, 2), (black, 2)), angle=0.0)
board.untape()
far = rim[(rim[:, 2] > CZ - 0.005)]
board.stroke(P(far[np.argsort(far[:, 0])]), fine.but(width=1.6, opacity=0.95, thickness=1.2), shade_at(v3(CX, CY + CH, CZ - CRAD), v3(0, 0.6, -0.8), A_CUP) * 1.2)
near = rim[(rim[:, 2] <= CZ - 0.005)]
board.stroke(P(near[np.argsort(near[:, 0])]), fine.but(width=1.4, opacity=0.9, thickness=1.0), shade_at(v3(CX, CY + CH, CZ + CRAD), v3(0, 0.9, 0.4), A_CUP))
board.dry()
board.stage("what was left: a cup")

# pull the room down round the edges, hardest at the floor I am standing on
gz = Brush(width=150, bristle=2.6, opacity=0.2, glaze=True, jitter=0.02, gap=0.0, taper=(0.2, 0.2))
deep = mix((ultra, 2), (umber, 1.5))
for i in range(6):
    y = H - rng.uniform(0, 140)
    board.stroke([(-100, y), (W + 100, y + rng.normal(0, 12))], gz, deep)
board.dry()

# =============================================================================================
# 8. White last. The bulkhead over the door, in one sitting.
# =============================================================================================
# the housing, grey plastic, a little bigger than the diffuser
hous = [v3(LX - LW / 2 - 0.025, LY - LH / 2 - 0.02, ZB - 0.002), v3(LX + LW / 2 + 0.025, LY - LH / 2 - 0.02, ZB - 0.002),
        v3(LX + LW / 2 + 0.025, LY + LH / 2 + 0.02, ZB - 0.002), v3(LX - LW / 2 - 0.025, LY + LH / 2 + 0.02, ZB - 0.002)]
box = [v3(LX - LW / 2 - 0.02, LY - LH / 2 - 0.015, ZB - LD - 0.004), v3(LX + LW / 2 + 0.02, LY - LH / 2 - 0.015, ZB - LD - 0.004),
       v3(LX + LW / 2 + 0.02, LY - LH / 2 - 0.015, ZB - 0.002), v3(LX - LW / 2 - 0.02, LY - LH / 2 - 0.015, ZB - 0.002)]
hq = np.vstack([quad(view, hous), quad(view, box)])
hull = hq[ConvexHull(hq).vertices]
board.tape(hull, feather=0.4)
board.fill(hull, body.but(width=4), mix((white, 2), (umber, 0.5), (ultra, 0.2)) * 0.35, angle=0.0)
board.untape()
hot = Brush(width=4, opacity=0.97, pickup=0.1, thickness=2.6, jitter=0.03, gap=0.0, deplete=0.0, taper=(0.02, 0.02))
lampc = mix((white, 12), (viridian, 0.35), (lemon, 0.9))
lampc = lampc / lampc.max() * 0.97
# its underside, which I see from below, then its face
uq = quad(view, [v3(LX - LW / 2, LY - LH / 2, ZB - LD), v3(LX + LW / 2, LY - LH / 2, ZB - LD),
                 v3(LX + LW / 2, LY - LH / 2, ZB - 0.01), v3(LX - LW / 2, LY - LH / 2, ZB - 0.01)])
fq = quad(view, [v3(LX - LW / 2, LY - LH / 2, ZB - LD), v3(LX + LW / 2, LY - LH / 2, ZB - LD),
                 v3(LX + LW / 2, LY + LH / 2, ZB - LD), v3(LX - LW / 2, LY + LH / 2, ZB - LD)])
board.tape(np.vstack([uq, fq])[ConvexHull(np.vstack([uq, fq])).vertices], feather=0.3)
for y in np.linspace(LY - LH / 2, LY + LH / 2, 7):
    board.stroke(P(np.array([v3(LX - LW / 2 - 0.02, y, ZB - LD), v3(LX + LW / 2 + 0.02, y, ZB - LD)])), hot, lampc)
for zz in np.linspace(ZB - LD, ZB - 0.01, 3):
    board.stroke(P(np.array([v3(LX - LW / 2 - 0.02, LY - LH / 2, zz), v3(LX + LW / 2 + 0.02, LY - LH / 2, zz)])), hot,
                 scale(lampc, 0.9))
board.untape()
board.dry()
board.stage("white last: the light over the door")

finish(board, HERE, title="Back stairs, east wing, half-landing, 04:50", artist="nell-abara", year=2008,
       medium="Oil on hardboard, rough side", made="2026-11-12")
