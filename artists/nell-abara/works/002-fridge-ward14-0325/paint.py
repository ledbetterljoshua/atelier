"""Nell Abara - Fridge, Ward 14 day kitchen, 03:25

Standing in the kitchen doorway. The fridge is in the far left corner, facing me, and its door has
not shut: somebody threw the tea towel over the top of it and the towel caught in the seal. So the
only light in the room is the fridge's own bulb, getting out through a gap a few centimetres wide
on the handle side. The cleaner has been and gone; the floor is still wet and the sign is out.
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
from tools import Hang, Patches, Plane, View, lay, lay_flow, line3, quad, tone, v3, wet_mirror  # noqa: E402

W, H = 1100, 1400
rng0 = np.random.default_rng(325)
board = Board(W, H, hexc("#0b0a0a"), ground.hardboard_mesh(W, H, rng0, pitch=5.0), seed=2004)
rng = board.rng
view = View(W, H, 850, 575, 395, (0.15, 1.55, 0))
P = view.P

# --- tubes -----------------------------------------------------------------------------------
black, ultra, umber = hexc("#0b0a0a"), hexc("#1b2a7a"), hexc("#4a2a16")
viridian, ochre, cadred = hexc("#0f6b55"), hexc("#c0902f"), hexc("#c6281c")
lemon, white = hexc("#efe36a"), hexc("#f6f3ea")
night = mix((ultra, 2), (umber, 1), (black, 2))

# --- what the surfaces are -------------------------------------------------------------------
A_WALL = mix((white, 5), (ochre, 1))
A_CEIL = mix((white, 4), (umber, 0.6))
A_FLOOR = mix((white, 2.0), (ultra, 0.35), (umber, 0.7), (black, 0.25))     # blue-grey safety lino
A_CUPB = mix((white, 3), (ochre, 1.1), (umber, 0.6), (cadred, 0.08))      # beech-effect laminate
A_TOP = mix((white, 2), (umber, 0.6), (ultra, 0.3))
A_TILE = mix((white, 6), (viridian, 0.2))
A_FRIDGE = mix((white, 8), (ultra, 0.1), (umber, 0.15))
A_SIGN = mix((lemon, 4), (cadred, 0.35), (ochre, 0.3))

UP, DOWN, EAST, WEST, BACK = v3(0, 1, 0), v3(0, -1, 0), v3(1, 0, 0), v3(-1, 0, 0), v3(0, 0, -1)

# --- the fridge, and its door not shut ---------------------------------------------------------
FX0, FX1, ZF, ZBK, FH = -0.95, -0.35, 2.75, 3.40, 1.75
TH = np.radians(8.0)
DW, DT = 0.60, 0.06
dvec = v3(np.cos(TH), 0, -np.sin(TH))          # along the door, hinge to handle
nd = v3(-np.sin(TH), 0, -np.cos(TH))           # the door's outside faces this way
Hin = v3(FX0, 0, ZF)
Ein = Hin + dvec * DW
Hout, Eout = Hin + nd * DT, Ein + nd * DT
Cc = v3(FX1, 0, ZF)                            # the cabinet's front corner on the handle side
TOWEL_Y = 1.36                                 # the towel's hem; above it, the gap is full of cloth

door_in = Plane((Hin[0], 0.03, Hin[2]), dvec * DW, (0, 1.71, 0))
slit = Plane((Ein[0], 0.05, Ein[2]), Cc - Ein, (0, 1.66, 0))
towel_in = Plane((Ein[0], TOWEL_Y, Ein[2]), Cc - Ein, (0, FH - TOWEL_Y, 0))

# --- the wet floor sign --------------------------------------------------------------------
SC, PHI = v3(0.45, 0, 1.62), np.radians(8)
fwd = v3(np.sin(PHI), 0, -np.cos(PHI))
rgt = v3(np.cos(PHI), 0, np.sin(PHI))
SW, SH, SD = 0.30, 0.57, 0.12
sign_front = Plane(SC + fwd * SD - rgt * SW / 2, rgt * SW, -fwd * SD + v3(0, SH, 0))
sign_back = Plane(SC - fwd * SD - rgt * SW / 2, rgt * SW, fwd * SD + v3(0, SH, 0))

# --- what is lit: the inside of the fridge, seen through the gap ------------------------------
bulb_col = mix((white, 10), (lemon, 1.3), (ochre, 0.9))
bulb_col = bulb_col / bulb_col.max()
BULB = v3(-0.48, 1.62, 3.05)
R = 42.0


def inside(S):
    k = 0.38 + 0.62 * np.exp(-((S - BULB) @ (S - BULB)) / 0.5)
    c = bulb_col if S[1] > 0.36 else mix((bulb_col, 3), (viridian, 0.12))   # crisper drawers
    return c * R * k


lrng = np.random.default_rng(7)
blockers = [(door_in, 0.0), (towel_in, 0.22), (sign_front, 0.0), (sign_back, 0.0)]
gap = (Patches.on(Plane((-0.91, 0.12, 3.30), (0.52, 0, 0), (0, 1.56, 0)), inside, 44, 18, facing=BACK, rng=lrng,
                  aperture=slit, blockers=blockers)
       + Patches.on(Plane((-0.91, 0.12, 2.76), (0, 0, 0.54), (0, 1.56, 0)), inside, 30, 18, facing=EAST, rng=lrng))

# --- the floor: where the mop has been and how wet it still is ---------------------------------
PIV = [(0.10 + 0.13 * np.sin(k * 1.7), 3.62 - 0.31 * k) for k in range(8)]
RM, HW = 1.02, 0.115


def damp(x, z):
    """It dries unevenly."""
    s = np.sin(3.1 * x + 1.3) * np.sin(2.3 * z + 0.4) + 0.6 * np.sin(5.3 * x - 4.1 * z + 2.0)
    return 0.6 + 0.3 * s


def band(F):
    x, z = F[0], F[2]
    for k in range(len(PIV) - 1, -1, -1):
        px, pz = PIV[k]
        r = np.hypot(x - px, z - pz)
        if abs(r - RM) < HW and z < pz + 0.25:
            return k, r
    return None, None


def puddle(F):
    """Where the fridge has been dripping since the door was left: standing water at its foot."""
    dx, dz = (F[0] + 0.24) / 0.22, (F[2] - 2.33) / 0.37
    th = np.arctan2(dz, dx)
    r = np.hypot(dx, dz) / (1 + 0.15 * np.sin(3 * th + 1.0) + 0.08 * np.sin(5 * th + 2.0))
    return float(np.clip((1.0 - r) / 0.08, 0, 1))


def wet(F):
    x, z = F[0], F[2]
    if x > 0.99 or x < -0.99 or (x < FX1 + 0.01 and z > ZF - 0.02):
        return 0.0
    pd = puddle(F)
    if pd > 0:
        return pd + (1 - pd) * 0.3
    k, r = band(F)
    if k is None:
        return 0.05 * damp(x, z)
    edge = max(0.0, (r - RM) / HW)
    patchy = np.clip(1.7 * damp(x, z) - 0.45, 0.0, 1.0)
    return float(np.clip((0.3 + 0.7 * k / 7) * (0.75 + 0.4 * edge ** 4) * patchy, 0, 1))


def mop(F):
    """Which way the mop went through here."""
    k, _ = band(F)
    if k is None:
        k = int(np.argmin([abs(np.hypot(F[0] - px, F[2] - pz) - RM) for px, pz in PIV]))
    px, pz = PIV[k]
    t = v3(-(F[2] - pz), 0, F[0] - px)
    t /= np.linalg.norm(t) + 1e-9
    return t if t[0] >= 0 else -t


# --- everything else is lit by what the lit floor and cupboards throw back --------------------
def amb(N):
    """Corridor light from behind me, through the doorway. Barely anything."""
    return v3(0.0027, 0.0031, 0.0037) * (1.0 + 0.8 * max(0.0, -N[2]))


floor_pl = Plane((-0.97, 0, 0.9), (1.95, 0, 0), (0, 0, 1.85))
cupb_pl = Plane((1.0, 0.1, 0.9), (0, 0, 2.5), (0, 0.77, 0))
bounce = (Patches.on(floor_pl, lambda S: gap.onto(S, UP) * A_FLOOR * (1 - 0.3 * wet(S)), 18, 16, facing=UP)
          + Patches.on(cupb_pl, lambda S: gap.onto(S, WEST) * A_CUPB, 16, 4, facing=WEST))


KB = 0.6


def light(Q, N):
    return amb(N) + gap.onto(Q, N) + KB * bounce.onto(Q, N)


def shader(albedo, N, gain=1.0, vary=0.06):
    N = v3(*N)

    def f(Q):
        a = albedo(Q) if callable(albedo) else albedo
        return tone(a * light(Q, N) * gain) * np.exp(rng.normal(0, vary))
    return f


def lum(c):
    return 0.2 * c[0] + 0.7 * c[1] + 0.1 * c[2]


def lit_only(albedo, N, thr):
    N = v3(*N)

    def w(Q):
        a = albedo(Q) if callable(albedo) else albedo
        return lum(tone(a * light(Q, N))) > thr
    return w


floor_alb = lambda Q: A_FLOOR * (1 - 0.38 * wet(Q)) * (1 - 0.55 * puddle(Q))  # noqa: E731  wet lino is darker

if os.environ.get("CHECK"):
    for name, Q, N, a in [("floor at the foot", v3(-0.25, 0, 2.55), UP, A_FLOOR), ("floor mid", v3(0.1, 0, 2.1), UP, A_FLOOR),
                          ("floor near", v3(0.3, 0, 1.5), UP, A_FLOOR), ("floor left", v3(-0.6, 0, 1.8), UP, A_FLOOR),
                          ("cupboard back", v3(1.0, 0.5, 2.5), WEST, A_CUPB), ("cupboard mid", v3(1.0, 0.5, 2.0), WEST, A_CUPB),
                          ("cupboard near", v3(1.0, 0.5, 1.5), WEST, A_CUPB), ("worktop", v3(1.2, 0.91, 2.0), UP, A_TOP),
                          ("ceiling", v3(0.0, 2.5, 2.3), DOWN, A_CEIL), ("back wall", v3(0.3, 1.0, 3.39), BACK, A_WALL),
                          ("left wall", v3(-0.99, 1.0, 2.0), EAST, A_WALL), ("door front", v3(-0.5, 0.6, 2.6), nd, A_FRIDGE),
                          ("splashback", v3(1.59, 1.2, 2.0), WEST, A_TILE)]:
        print(f"{name:16s}", np.round(tone(a * light(Q, N)), 3), "wet", round(wet(Q), 2))
    for nm, p in [("Ein", Ein), ("Eout", Eout), ("C", Cc), ("Hout", Hout)]:
        print(nm, np.round(P(p + v3(0, 0.05, 0)), 1), np.round(P(p + v3(0, 1.7, 0)), 1))
    sys.exit()

# --- the room's planes ------------------------------------------------------------------------
ceil = Plane((-1.0, 2.5, 0.9), (2.6, 0, 0), (0, 0, 2.5))
wall_back = Plane((-1.0, 0, 3.4), (2.6, 0, 0), (0, 2.5, 0))
wall_l = Plane((-1.0, 0, 0.9), (0, 0, 2.5), (0, 2.5, 0))
splash = Plane((1.6, 0.91, 0.9), (0, 0, 2.5), (0, 1.59, 0))
worktop = Plane((0.98, 0.91, 0.9), (0.62, 0, 0), (0, 0, 2.5))
cupb = Plane((1.0, 0.1, 0.9), (0, 0, 2.5), (0, 0.765, 0))
plinth = Plane((1.05, 0.0, 0.9), (0, 0, 2.5), (0, 0.1, 0))
floor = Plane((-1.0, 0, 0.9), (2.05, 0, 0), (0, 0, 2.5))
fr_side = Plane((FX1, 0.0, ZF), (0, 0, ZBK - ZF), (0, FH, 0))
door_out = Plane((Hout[0], 0.06, Hout[2]), dvec * DW, (0, 1.685, 0))

# =============================================================================================
# 1. Imprimatura. Thin coloured darks over the black; a little warmer where the light will be.
# =============================================================================================
wash = Brush(width=120, bristle=2.6, opacity=0.5, dryness=0.42, pickup=0.3, thickness=0.2, jitter=0.12, deplete=0.0008)
for i in range(80):
    x, y = rng.uniform(-100, W + 100), rng.uniform(-50, H + 50)
    a = rng.normal(np.pi / 2, 0.5)
    L = rng.uniform(300, 700)
    warm = np.exp(-((x - 650) / 350) ** 2 - ((y - 1050) / 350) ** 2)
    c = mix((ultra, rng.uniform(1, 3) * (1 - 0.6 * warm)), (umber, rng.uniform(0.5, 2.5) + 2 * warm), (black, 2.5))
    board.stroke([(x - np.cos(a) * L / 2, y - np.sin(a) * L / 2), (x + np.cos(a) * L / 2, y + np.sin(a) * L / 2)],
                 wash, c, wobble=10)
board.dry()
board.stage("coloured darks over black")

# =============================================================================================
# 2. Block-in. Long strokes that follow the surfaces, wet enough to pull into each other.
# =============================================================================================
# where nothing reaches, one broad dry brush, long, so the mesh shows through and nothing is a dab
dark = Brush(width=54, bristle=2.0, opacity=0.6, pickup=0.6, dryness=0.4, thickness=0.3, jitter=0.05, deplete=0.0006,
             taper=(0.1, 0.15))
lay(board, view, ceil, dark, shader(A_CEIL, DOWN, gain=0.4, vary=0.03), EAST, length=380, cover=2.4, zref=2.5, shrink=0.4, wobble=4)
lay(board, view, wall_back, dark, shader(A_WALL, BACK, gain=0.7, vary=0.015), (1, 0.08, 0), length=330, cover=2.4, zref=3.4, wobble=4)
lay(board, view, wall_l, dark, shader(A_WALL, EAST, vary=0.03), (0, -0.05, 1), length=420, cover=2.4, zref=2.5, shrink=0.4, wobble=4)
# where the gap's light reaches, a smaller brush that follows the surface
CB, SB = 0.45, 0.18     # she holds the cupboards and the tiles down: the gap has to stay the brightest thing
blk = Brush(width=20, opacity=0.9, pickup=0.55, dryness=0.2, thickness=0.45, jitter=0.05, deplete=0.0009)
C = 3.4
lay(board, view, splash, dark.but(width=30, dryness=0.3), shader(A_TILE, WEST, gain=SB, vary=0.03), UP, length=380, cover=2.6,
    zref=2.0, shrink=0.4, wobble=3)
lay(board, view, worktop, blk, shader(A_TOP, UP), (0, 0, 1), length=200, cover=C)
# strokes run past the doors' top and bottom and the tape cuts them, so the edges are clean
board.tape(cupb.screen_poly(view), feather=0.6)
lay(board, view, Plane((1.0, -0.05, 0.9), (0, 0, 2.5), (0, 1.0, 0)), blk.but(width=10, pickup=0.65),
    shader(A_CUPB, WEST, gain=CB, vary=0.03), UP, length=320, cover=6, zref=1.6, shrink=0.8, wobble=0.6, tape=False)
board.untape()
lay(board, view, plinth, blk.but(width=10), shader(scale(A_CUPB, 0.3), WEST), (0, 0, 1), length=120, cover=C)
lay(board, view, floor, blk.but(width=26), shader(floor_alb, UP), EAST, length=220, cover=C)
board.dry()
board.stage("the kitchen blocked in")

# =============================================================================================
# 3. The floor again, the way the mop went: arcs, backing out toward the door.
# =============================================================================================
mopb = Brush(width=16, opacity=0.85, pickup=0.7, dryness=0.18, thickness=0.4, jitter=0.04, deplete=0.0008, taper=(0.15, 0.2))
lay_flow(board, view, floor, mopb, shader(floor_alb, UP, vary=0.05), mop, length=170, cover=2.6, steps=6)
# the edge of each pass leaves a line of water
tide = Brush(width=5, opacity=0.6, pickup=0.4, dryness=0.1, thickness=0.3, jitter=0.03, gap=0.02, taper=(0.3, 0.3))
for k, (px, pz) in enumerate(PIV):
    for a0 in np.linspace(-1.25, 1.25, 7):
        a = np.linspace(a0, a0 + rng.uniform(0.25, 0.45), 10)
        r = RM + HW * rng.uniform(0.75, 0.98)
        pts = np.stack([px + r * np.sin(a), np.zeros_like(a), pz - r * np.cos(a)], axis=1)
        pts = pts[(pts[:, 2] > 0.95) & (np.abs(pts[:, 0]) < 0.97) & ~((pts[:, 0] < FX1) & (pts[:, 2] > ZF - 0.03))]
        if len(pts) < 3:
            continue
        mid = pts[len(pts) // 2]
        c = tone(A_FLOOR * 0.55 * light(mid, UP)) + scale(night, 0.1)
        board.stroke(P(pts), tide.but(width=max(2.0, 6 * 1.8 / mid[2])), c, wobble=0.5)
board.dry()
board.stage("mopped")

# =============================================================================================
# 4. Scumbles: drier paint dragged over the mesh only where the gap's light reaches.
# =============================================================================================
scm = Brush(width=18, opacity=0.8, pickup=0.1, dryness=0.5, thickness=0.9, jitter=0.04, deplete=0.0015)


def door_shadow_edge(z):
    """Where, across the floor at depth z, the door stops hiding the gap: found by looking, not drawn."""
    xs = np.arange(-0.95, 0.6, 0.01)
    v = np.array([gap.onto(v3(x, 0, z), UP)[1] for x in xs])
    return xs[np.argmax(v > 0.35 * v.max())]


EDGE = [v3(door_shadow_edge(z), 0, z) for z in np.linspace(0.95, ZF - 0.04, 14)]
lit_floor = P(np.array(EDGE + [v3(1.0, 0, ZF - 0.04), v3(1.0, 0, 0.95)]))
dry_floor = lambda Q: puddle(Q) < 0.2  # noqa: E731
board.tape(lit_floor, feather=0.8)
lay_flow(board, view, floor, scm, shader(floor_alb, UP, gain=1.15), mop, length=150, cover=2.2, tape=False,
         where=lambda Q: dry_floor(Q) and lit_only(floor_alb, UP, 0.012)(Q))
board.untape()
lay(board, view, splash, scm.but(width=20, dryness=0.62, thickness=0.5), shader(A_TILE, WEST, gain=1.1 * SB), UP, length=260, shrink=0.4,
    cover=1.4, where=lit_only(A_TILE, WEST, 0.02))
lay(board, view, worktop, scm.but(width=12), shader(A_TOP, UP, gain=1.2), (0, 0, 1), length=120, cover=1.8,
    where=lit_only(A_TOP, UP, 0.008))
# nearest the gap, wetter and thicker
board.tape(lit_floor, feather=0.8)
lay_flow(board, view, floor, scm.but(dryness=0.28, opacity=0.8, thickness=1.2), shader(floor_alb, UP, gain=1.2), mop,
         length=110, cover=2.0, tape=False, where=lambda Q: dry_floor(Q) and lit_only(floor_alb, UP, 0.07)(Q))
board.untape()
board.dry()
board.stage("light scumbled where the gap reaches")

# =============================================================================================
# 5. The fridge, dark, and the counter's furniture.
# =============================================================================================
fine = Brush(width=3, bristle=0.9, opacity=0.85, pickup=0.0, thickness=0.6, jitter=0.03, gap=0.0, taper=(0.03, 0.05))
body = Brush(width=12, opacity=0.95, pickup=0.35, dryness=0.12, thickness=0.6, jitter=0.04, deplete=0.0005)
lay(board, view, fr_side, body.but(width=8), shader(A_FRIDGE, EAST, vary=0.04), UP, length=90, cover=3.2, feather=0.6)
lay(board, view, door_out, body, shader(A_FRIDGE, nd, vary=0.04), UP, length=110, cover=3.4, feather=0.6)
# the thickness of the door at its free edge
eq = quad(view, [Eout + v3(0, 0.06, 0), Ein + v3(0, 0.06, 0), Ein + v3(0, 1.745, 0), Eout + v3(0, 1.745, 0)])
board.tape(eq, feather=0.5)
c_edge = tone(A_FRIDGE * light(Eout + v3(0, 0.5, 0), dvec))
board.fill(eq, body.but(width=4), c_edge, angle=np.pi / 2, color_fn=lambda m: scale(c_edge, rng.uniform(0.9, 1.15)))
board.untape()
# kick grille under the door
kq = quad(view, [Hout + v3(0, 0.0, 0), Cc + v3(0, 0, -0.05), Cc + v3(0, 0.06, -0.05), Hout + v3(0, 0.06, 0)])
board.tape(kq, feather=0.5)
board.fill(kq, body.but(width=5), scale(night, 0.45), angle=0.0)
board.untape()
for u in np.linspace(0.05, 0.95, 16):
    a = Hout + dvec * DW * u
    line3(board, view, a + v3(0, 0.012, 0), a + v3(0, 0.05, 0), fine.but(width=1.6, opacity=0.5), scale(night, 0.25))
# the notice on the door: PATIENTS' FOOD ONLY, LABEL AND DATE
def on_door(u, y, eps=0.004):
    return Hout + dvec * DW * u + v3(0, y, 0) + nd * eps


nq = quad(view, [on_door(0.20, 1.06), on_door(0.50, 1.07), on_door(0.50, 1.40), on_door(0.20, 1.39)])
board.tape(nq, feather=0.5)
c_paper = tone(mix((white, 5), (ochre, 0.4)) * light(on_door(0.35, 1.2), nd) * 1.2)
board.fill(nq, Brush(width=5, opacity=0.9, thickness=0.7, pickup=0.1), c_paper, angle=0.02,
           color_fn=lambda m: scale(c_paper, rng.uniform(0.92, 1.08)))
board.stroke(quad(view, [on_door(0.215, 1.355), on_door(0.485, 1.36)]), fine.but(width=4, opacity=0.8),
             tone(mix((cadred, 2), (white, 1)) * light(on_door(0.35, 1.3), nd) * 1.2))
for k, yy in enumerate(np.linspace(1.30, 1.11, 6)):
    u1 = rng.uniform(0.36, 0.48) if k % 3 else 0.46
    board.stroke(quad(view, [on_door(0.23, yy), on_door(u1, yy)]), fine.but(width=1.4, opacity=0.55), scale(c_paper, 0.45))
board.untape()
# recessed grip down the handle side
g0, g1 = on_door(0.93, 0.80), on_door(0.93, 1.30)
line3(board, view, g0, g1, fine.but(width=5, opacity=0.9), scale(night, 0.3))
line3(board, view, g0 + dvec * 0.012, g1 + dvec * 0.012, fine.but(width=1.6, opacity=0.6), scale(c_edge, 1.4))
# where the door meets the cabinet top, and its foot
line3(board, view, Hout + v3(0, 1.745, 0), Eout + v3(0, 1.745, 0), fine.but(width=2, opacity=0.6), scale(night, 0.3))
line3(board, view, Hout + v3(0, 0.06, 0), Eout + v3(0, 0.06, 0), fine.but(width=2.5, opacity=0.7), scale(night, 0.3))

# cupboard doors, their gaps and handles
for z in np.arange(1.4, 3.4, 0.5):
    line3(board, view, (0.999, 0.11, z), (0.999, 0.86, z), fine.but(width=max(1.5, 4.5 * 1.6 / z), opacity=0.8), scale(night, 0.35))
line3(board, view, (0.999, 0.10, 0.9), (0.999, 0.10, 3.4), fine.but(width=3, opacity=0.8), scale(night, 0.3))
for z in np.arange(1.4, 3.3, 0.5):
    for zh, side in ((z + 0.06, 1), (z - 0.06, -1)):
        if not 1.0 < zh < 3.35:
            continue
        a, b = v3(0.985, 0.80, zh), v3(0.985, 0.80, zh + 0.09 * side)
        c_h = tone(mix((white, 2), (ultra, 0.3)) * light(a, v3(-0.7, 0.7, 0)) * 1.6 * CB)
        line3(board, view, a, b, fine.but(width=max(2.0, 7 / zh), opacity=0.95, thickness=1.2), c_h)
        line3(board, view, a + v3(0.012, -0.022, 0), b + v3(0.012, -0.022, 0), fine.but(width=max(1.5, 5 / zh), opacity=0.5),
              scale(night, 0.4))
# worktop nosing catches the light end on
for z0 in np.arange(1.0, 3.3, 0.18):
    zm = z0 + 0.09
    c = tone(A_TOP * light(v3(0.975, 0.89, zm), WEST) * 1.5)
    line3(board, view, (0.975, 0.89, z0), (0.975, 0.89, z0 + 0.2), fine.but(width=max(1.6, 6 / zm), thickness=1.0), c)


def vessel(cx, cz, prof, albedo, base=0.91, n=18, gloss=0.0, gain=1.0):
    """Something round standing on the worktop. prof: [(height, radius)] from the bottom up.

    Taped to its own outline, then laid in with upright strokes around the half that faces me,
    each one mixed for the way that strip of it faces the gap.
    """
    ys = np.array([p[0] for p in prof])
    rs = np.array([p[1] for p in prof])
    left = [P(v3(cx - r, base + y, cz)) for y, r in prof]
    right = [P(v3(cx + r, base + y, cz)) for y, r in prof]
    board.tape(np.array(left + right[::-1]), feather=0.5)
    ppm = view.ppm(cz)
    wd = np.pi * rs.max() / n * ppm * 2.2
    for a in np.linspace(np.pi, 2 * np.pi, n):
        N = v3(np.cos(a), 0, np.sin(a))
        pts = np.array([v3(cx + r * np.cos(a), base + y, cz + r * np.sin(a)) for y, r in zip(ys, rs)])
        mid = pts[len(pts) // 2]
        c = tone(albedo * light(mid, N) * gain)
        board.stroke(P(pts), Brush(width=wd, opacity=0.95, thickness=0.9, pickup=0.3, gap=0.0, taper=(0.02, 0.02)), c)
    if gloss > 0:   # the gap seen in it: a thin upright glint on the side that faces the fridge
        a = np.pi + 0.45
        pts = np.array([v3(cx + r * np.cos(a), base + y, cz + r * np.sin(a)) for y, r in zip(ys, rs)])[1:-1]
        board.stroke(P(pts), fine.but(width=2.2, thickness=1.4, opacity=0.9), scale(slot_glint, gloss))
    board.untape()
    return ppm


slot_glint = mix((white, 10), (lemon, 1.4), (ochre, 0.7))
# kettle: a jug, its lid, its handle
KX, KZ = 1.27, 2.10
kprof = [(0.0, 0.082), (0.02, 0.088), (0.12, 0.086), (0.20, 0.074), (0.235, 0.066), (0.25, 0.05), (0.258, 0.02)]
vessel(KX, KZ, kprof, mix((white, 6), (ultra, 0.25)), gloss=0.45, gain=CB)
board.stroke(P(np.array([(KX + 0.07, 1.13, KZ), (KX + 0.135, 1.125, KZ), (KX + 0.145, 1.03, KZ), (KX + 0.085, 0.96, KZ)])),
             fine.but(width=6, opacity=0.95), scale(night, 0.45))
board.stroke(P(np.array([(KX - 0.07, 1.10, KZ - 0.03), (KX - 0.095, 1.125, KZ - 0.04), (KX - 0.105, 1.13, KZ - 0.04)])),
             fine.but(width=6, opacity=0.95, taper=(0.0, 0.5)), tone(mix((white, 6), (ultra, 0.25)) * light(v3(KX - 0.1, 1.14, KZ), WEST)))
board.stroke(P(np.array([(KX - 0.03, 0.97, KZ - 0.09), (KX + 0.03, 0.97, KZ - 0.09)])), fine.but(width=3, opacity=0.8),
             scale(night, 0.4))
line3(board, view, (KX - 0.085, 0.912, KZ - 0.02), (KX + 0.09, 0.912, KZ - 0.02), fine.but(width=3, opacity=0.8), scale(night, 0.25))
# a mug left by the kettle, handle out
MX, MZ = 1.13, 1.78
mprof = [(0.0, 0.038), (0.01, 0.042), (0.095, 0.043), (0.098, 0.041)]
vessel(MX, MZ, mprof, mix((white, 3), (ultra, 1.2), (viridian, 0.3)), n=12, gloss=0.3, gain=CB)
board.stroke(P(np.array([(MX + 0.035, 0.995, MZ - 0.012), (MX + 0.075, 0.99, MZ - 0.012), (MX + 0.078, 0.95, MZ - 0.012),
                         (MX + 0.038, 0.935, MZ - 0.012)])), fine.but(width=3.4, opacity=0.95), scale(night, 0.6))
ms = P(v3(MX, 1.008, MZ))
board.stroke([ms + (-0.04 * view.ppm(MZ), 0), ms + (0.04 * view.ppm(MZ), 0)], fine.but(width=3, opacity=0.9), scale(night, 0.2))
line3(board, view, (MX - 0.04, 0.912, MZ - 0.01), (MX + 0.045, 0.912, MZ - 0.01), fine.but(width=2.5, opacity=0.8), scale(night, 0.25))

# the water boiler on the back wall, and its neon
bq = quad(view, [(1.08, 1.30, 3.38), (1.44, 1.30, 3.38), (1.44, 1.84, 3.38), (1.08, 1.84, 3.38)])
board.tape(bq, feather=0.5)
c_box = tone(mix((white, 4), (ultra, 0.4)) * light(v3(1.26, 1.5, 3.38), BACK) * 1.1)
board.fill(bq, body.but(width=7), c_box, angle=np.pi / 2, color_fn=lambda m: scale(c_box, rng.uniform(0.85, 1.15)))
board.untape()
line3(board, view, (1.08, 1.30, 3.37), (1.44, 1.30, 3.37), fine.but(width=2, opacity=0.6), scale(night, 0.3))
line3(board, view, (1.18, 1.30, 3.36), (1.18, 1.18, 3.36), fine.but(width=3.2, opacity=0.9), scale(night, 0.4))
neon = P(v3(1.38, 1.36, 3.37))
board.dab(neon[0], neon[1], Brush(width=4, opacity=0.95, thickness=1.8, pickup=0, gap=0, jitter=0), mix((cadred, 2), (lemon, 1.4), (white, 0.6)), angle=0, length=3)
board.dry()
board.stage("the fridge, dark, and the counter")

deep_shadow = mix((ultra, 1.5), (umber, 2), (black, 1))
# =============================================================================================
# 6. What was left: the sign, and the tea towel that stopped the door.
# =============================================================================================
# its shadow first. Where the sign stands between a bit of floor and the gap, glaze that floor down
# by as much light as the sign takes away, in strokes that run away from the gap.
gap.blockers = blockers[:2]
open_lit = lambda Q: gap.onto(Q, UP)[1]  # noqa: E731
gap.blockers = blockers
sgz = Brush(width=14, bristle=2.0, opacity=0.5, glaze=True, jitter=0.02, gap=0.0, taper=(0.15, 0.35))
src = (Ein + Cc) / 2
for i in range(260):
    Q = SC + v3(rng.uniform(-0.25, 0.75), 0, rng.uniform(-0.9, 0.25))
    if Q[2] < 1.2 or Q[0] > 0.9:
        continue
    full = open_lit(Q)
    if full < 1e-4:
        continue
    k = 1 - gap.onto(Q, UP)[1] / full
    if k < 0.12:
        continue
    d = Q - src
    d = d / np.linalg.norm(d)
    line3(board, view, Q - d * 0.06, Q + d * 0.12, sgz.but(width=max(6, 16 * 1.6 / Q[2]), opacity=0.55 * k), deep_shadow)
for pl, us in ((sign_front, (0.04, 0.96)), (sign_back, (0.04, 0.96))):
    for u in us:
        f0 = pl.at(u, 0.0)
        line3(board, view, f0 + v3(-0.03, 0, 0), f0 + v3(0.05, 0, -0.03), fine.but(width=7, opacity=0.6, taper=(0.3, 0.3)),
              scale(night, 0.3))
nf = sign_front.n if sign_front.n @ (view.eye - SC) > 0 else -sign_front.n
nb = sign_back.n if sign_back.n @ (SC - view.eye) > 0 else -sign_back.n      # its outside, away from me
c_inner = tone(A_SIGN * light(sign_back.at(0.5, 0.4), -nb) * 0.9)
bk = sign_back.screen_poly(view)
board.tape(bk, feather=0.5)
board.fill(bk, body.but(width=6), c_inner, angle=np.pi / 2 + 0.2, color_fn=lambda m: scale(c_inner, rng.uniform(0.8, 1.2)))
board.untape()
fr = sign_front.screen_poly(view)
board.tape(fr, feather=0.5)
signb = Brush(width=12, opacity=0.95, pickup=0.3, dryness=0.12, thickness=0.8, jitter=0.04, deplete=0.0004)
for v in np.linspace(0.0, 1.0, 64):
    a, b = sign_front.at(-0.05, v), sign_front.at(1.05, v)
    c = tone(A_SIGN * light(sign_front.at(0.5, v), nf) * 1.3) * np.exp(rng.normal(0, 0.05))
    board.stroke(P(np.array([a, b])), signb, c, wobble=0.4)
# the warning triangle and the words, in black
tri = [sign_front.at(0.5, 0.80), sign_front.at(0.78, 0.48), sign_front.at(0.22, 0.48), sign_front.at(0.5, 0.80)]
board.stroke(P(np.array(tri)), fine.but(width=3.2, opacity=0.85, taper=(0, 0)), scale(night, 0.3), smooth=False)
fig = [sign_front.at(0.46, 0.68), sign_front.at(0.53, 0.60), sign_front.at(0.44, 0.53)]
board.stroke(P(np.array(fig)), fine.but(width=2.4, opacity=0.8), scale(night, 0.3))
for v, u0, u1 in [(0.36, 0.18, 0.82), (0.28, 0.24, 0.76), (0.20, 0.15, 0.85)]:
    board.stroke(P(np.array([sign_front.at(u0, v), sign_front.at(u1, v)])), fine.but(width=3.4 if v > 0.3 else 2.6, opacity=0.6),
                 scale(night, 0.35))
# the grip cut through the top
gp = [sign_front.at(0.36, 0.93), sign_front.at(0.64, 0.93)]
board.stroke(P(np.array(gp)), fine.but(width=6, opacity=0.95, taper=(0.2, 0.2)), scale(night, 0.25))
board.untape()
# rims: the back panel's edge and the top, where the gap's light comes over
for u in (0.0,):
    pts = np.array([sign_back.at(u, v) for v in np.linspace(0.02, 0.98, 8)])
    c = tone(A_SIGN * light(sign_back.at(0.1, 0.5), nb) * 1.4)
    board.stroke(P(pts), fine.but(width=2.4, opacity=0.9, thickness=1.6, taper=(0.3, 0.1)), c, wobble=0.3)
top = np.array([sign_front.at(u, 1.0) + v3(0, 0.004, 0) for u in np.linspace(0.02, 0.98, 6)])
board.stroke(P(top), fine.but(width=2.6, opacity=0.85, thickness=1.6), tone(A_SIGN * light(SC + v3(0, SH, 0), v3(-0.5, 0.8, 0.3)) * 1.3))
for pl, us in ((sign_front, (0.03, 0.97)), (sign_back, (0.03,))):
    for u in us:
        f0 = pl.at(u, 0.0)
        line3(board, view, f0, f0 + v3(0, 0.03, 0), fine.but(width=5), scale(night, 0.2))

# the tea towel: over the top of the door, caught in the seal, hanging down the front
TOW_A = Hout + dvec * DW * 0.40 + v3(0, 1.745, 0) + nd * 0.006
TOW_B = Eout + dvec * 0.035 + v3(0, 1.745, 0) + nd * 0.006
towel = Hang(TOW_A, TOW_B, 0.35, nd, sag=lambda u: 0.07 * (1 - u) ** 1.6 + 0.02 * np.sin(np.pi * u) + 0.012 * np.sin(9 * u),
             folds=[(0.2, 0.03, 0.07), (0.45, -0.02, 0.06), (0.7, 0.035, 0.06), (0.93, 0.03, 0.04)], lean=0.012)
U_EDGE = (DW - DW * 0.40) / (DW + 0.035 - DW * 0.40)
cotton = mix((white, 6), (ochre, 0.7), (umber, 0.15))
red = mix((cadred, 3), (umber, 0.5))


def stripe(v):
    return red if (0.60 < v < 0.69 or 0.75 < v < 0.785) else cotton


board.tape(towel.outline(view), feather=0.6)
clothb = Brush(width=6, opacity=0.95, pickup=0.25, dryness=0.08, thickness=0.9, jitter=0.03, gap=0.02, deplete=0.0, taper=(0.05, 0.05))
for v in np.linspace(-0.02, 1.02, 44):
    us = np.linspace(-0.03, 1.03, 10)
    pts = np.array([towel.at(np.clip(u, 0, 1), np.clip(v, 0, 1)) for u in us])
    cs = []
    for u in (0.2, 0.5, 0.8):
        Q = towel.at(u, np.clip(v, 0, 1))
        cs.append(tone(stripe(v) * light(Q, towel.normal(u, np.clip(v, 0, 1))) * 1.3))
    board.stroke(P(pts), clothb, cs[0], color2=cs[2], wobble=0.3)
# folds: the cloth turns toward or away as it falls
for fu, depth, w in towel.folds:
    for du, k in ((-0.025, 0.55), (0.02, 1.45)):
        pts = np.array([towel.at(np.clip(fu + du, 0, 1), v) for v in np.linspace(0.1, 0.98, 6)])
        board.stroke(P(pts), clothb.but(width=3, opacity=0.45, taper=(0.4, 0.2)), scale(tone(cotton * light(pts[3], nd) * 1.3), k))
# where it hangs past the door's edge it is in front of the gap, and the light comes through it
for v in np.linspace(0.0, 1.0, 22):
    us = np.linspace(U_EDGE + 0.01, 1.03, 4)
    pts = np.array([towel.at(np.clip(u, 0, 1), v) for u in us])
    glow = mix((bulb_col, 4), (stripe(v), 2.5 if stripe(v) is red else 1.0), (cadred, 0.25))
    board.stroke(P(pts), clothb.but(width=4, opacity=0.9, thickness=1.2), scale(glow, 0.32 + 0.25 * v),
                 color2=scale(glow, 0.55 + 0.25 * v))
board.untape()
hem = np.array([towel.at(u, 1.0) for u in np.linspace(0.0, 1.0, 12)])
board.stroke(P(hem) + [0, 4], fine.but(width=6, opacity=0.5, taper=(0.2, 0.2)), scale(night, 0.25))
board.stroke(P(hem) + [0, 1.0], fine.but(width=2.0, opacity=0.6), scale(tone(cotton * light(hem[6], nd) * 1.3), 0.7))
for u in np.linspace(0.02, U_EDGE, 34):     # the fringe
    q = towel.at(u, 1.0)
    line3(board, view, q, q + v3(0, -0.012, 0), fine.but(width=1.2, opacity=0.6), scale(tone(cotton * light(q, nd) * 1.3), 0.8))
board.dry()
board.stage("what was left: the sign, the towel")

# =============================================================================================
# 7. The wet floor gives it back. Only where it is still wet, and broken where it is drying.
# =============================================================================================
def floor_ok(F):
    return -0.99 < F[0] < 0.99 and 0.9 < F[2] < 3.39 and not (F[0] < FX1 + 0.01 and F[2] > ZF - 0.08)


refl = Brush(width=4, opacity=0.75, pickup=0.35, dryness=0.2, thickness=0.5, jitter=0.06, gap=0.05, taper=(0.25, 0.45))


def slot_col(y):
    k = 0.55 + 0.45 * np.exp(-((y - 1.45) / 0.6) ** 2)
    c = mix((white, 10), (lemon, 1.4), (ochre, 0.7)) if y > 0.36 else mix((white, 8), (lemon, 1.2), (viridian, 0.22))
    return scale(c, k)


# the puddle first: flat water, no tooth showing through it, darker than the lino round it because
# what it gives back here is the dark front of the fridge
pts = []
for th in np.linspace(-np.pi, np.pi, 90):
    rr = 1 + 0.15 * np.sin(3 * th + 1.0) + 0.08 * np.sin(5 * th + 2.0)
    pts.append(v3(-0.24 + 0.22 * rr * np.cos(th), 0, 2.33 + 0.37 * rr * np.sin(th)))
pts = np.array([q for q in pts if q[2] < ZF - 0.05 and not (q[0] < FX1 and q[2] > ZF - 0.1)])
board.tape(P(pts), feather=0.7)
glass = Brush(width=10, opacity=0.9, pickup=0.5, dryness=0.0, thickness=0.15, jitter=0.02, gap=0.0, taper=(0.1, 0.1))
for z in np.arange(1.9, 2.75, 0.012):
    xa, xb = -0.62, 0.12
    Q = v3(-0.26, 0, z)
    c = tone(A_FLOOR * 0.55 * light(v3(-0.55, 0, z), UP)) * 0.75 + tone(A_FRIDGE * light(v3(-0.3, 0.6, 2.62), nd)) * 0.1
    cl = tone(A_FLOOR * 0.55 * light(v3(0.0, 0, z), UP)) * 0.75
    board.stroke(P(np.array([v3(xa, 0, z), v3(xb, 0, z)])), glass.but(width=max(4, 10 * 1.8 / z)), c, color2=cl)
board.untape()
srcs = []
for y in np.linspace(0.14, TOWEL_Y, 140):
    S = Ein + (Cc - Ein) * rng.uniform(0.15, 0.95) + v3(0, y, 0)
    srcs.append((S, inside(v3(-0.5, y, 3.2)) * 0.8))
# in the puddle, a mirror; on the mopped floor, a faint broken smear
wet_mirror(board, view, srcs, puddle, refl.but(width=3), smear=(14, 0.2), floor_ok=floor_ok, spread=0.002, blur=0.006,
           threads=2)
wet_mirror(board, view, srcs, lambda F: wet(F) * (1 - puddle(F)), refl.but(width=1.4, opacity=0.4), smear=(34, 0.5),
           floor_ok=floor_ok, spread=0.004, blur=0.03, gain=0.15, threads=9, thread=(0.05, 0.45))
srcs = []
for i in range(360):
    Q = v3(0.995, rng.uniform(0.12, 0.86), rng.uniform(1.3, 3.0))
    srcs.append((Q, A_CUPB * light(Q, WEST) * CB))
wet_mirror(board, view, srcs, wet, refl.but(width=8, opacity=0.6), smear=(20, 0.3), floor_ok=floor_ok, spread=0.01, gain=3.0)
board.dry()
board.stage("the wet floor gives it back")

# pull the room down round the edges
gz = Brush(width=150, bristle=2.6, opacity=0.2, glaze=True, jitter=0.02, gap=0.0, taper=(0.2, 0.2))
deep = mix((ultra, 2), (umber, 1.5))
for i in range(7):
    y = rng.uniform(-40, 60)
    board.stroke([(-100, y), (W + 100, y + rng.normal(0, 12))], gz, deep, wobble=6)
for i in range(6):
    x = rng.uniform(-40, 70)
    board.stroke([(x, -50), (x + rng.normal(0, 20), H + 50)], gz, deep, wobble=6)
for i in range(5):
    y = H - rng.uniform(0, 60)
    board.stroke([(-100, y), (W * 0.55, y + rng.normal(0, 12))], gz.but(opacity=0.16), deep, wobble=6)
board.dry()

# =============================================================================================
# 8. White last. The gap, in one sitting.
# =============================================================================================
sq = quad(view, [Ein + v3(0, 0.13, 0), Cc + v3(0, 0.13, 0), Cc + v3(0, TOWEL_Y, 0), Ein + v3(0, TOWEL_Y, 0)])
board.tape(sq, feather=0.4)
hot = Brush(width=5, opacity=0.97, pickup=0.1, thickness=2.6, jitter=0.03, gap=0.0, deplete=0.0, taper=(0.02, 0.02))
for y0 in np.arange(0.13, TOWEL_Y, 0.07):
    y1 = min(TOWEL_Y + 0.02, y0 + rng.uniform(0.12, 0.3))
    for t in (0.3, 0.7):
        a = Ein + (Cc - Ein) * t + v3(0, y0, 0)
        b = Ein + (Cc - Ein) * t + v3(0, y1, 0)
        board.stroke(P(np.array([a, b])), hot, slot_col((y0 + y1) / 2))
# the shelves inside, end on: glass edges, a little green
for y in (0.36, 0.64, 0.93, 1.19):
    a, b = Ein + v3(0, y, 0), Cc + v3(0, y, 0)
    board.stroke(P(np.array([a, b])), hot.but(width=2.2, thickness=1.6), mix((white, 3), (viridian, 1.2), (lemon, 0.6)))
board.untape()
# the door seal down the near side of the gap
line3(board, view, Ein + v3(0, 0.14, 0) - dvec * 0.004, Ein + v3(0, TOWEL_Y, 0) - dvec * 0.004, fine.but(width=1.8, opacity=0.7),
      scale(night, 0.6))
# the floor at its foot, and the head of the reflection
# the floor at its foot takes the most light in the room: thick, following the mop
board.tape(lit_floor, feather=0.6)
lay_flow(board, view, floor, scm.but(width=12, dryness=0.22, thickness=1.8, opacity=0.85), shader(floor_alb, UP, gain=1.05),
         mop, length=50, tape=False, cover=2.0, where=lambda Q: np.hypot(Q[0] - Cc[0], Q[2] - Cc[2]) < 0.6 and puddle(Q) < 0.3
         and lum(tone(floor_alb(Q) * light(Q, UP))) > 0.12)
board.untape()
board.dry()
board.stage("white last: the gap")

finish(board, HERE, title="Fridge, Ward 14 day kitchen, 03:25", artist="nell-abara", year=2004,
       medium="Oil on hardboard, rough side", made="2026-11-09")
