"""Nell Abara - Photocopier, Medical Records, lower ground, 03:40

Standing over it, close enough to touch. The copier in medical records jammed on someone's last
job of the evening and nobody cleared it: the lid is up, the original is still face down on the
glass, and the lamp stopped partway along its run and stayed on. So the light is under the glass
and comes up, through the sheet and past it, onto the underside of the lid. The case notes the
sheet came out of are on the machine beside it.
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
from tools import Over, Patches, Plane, keyed, line3, quad, radiate, room, scrub, sweep, v3  # noqa: E402

W, H = 1400, 900
rng0 = np.random.default_rng(340)
board = Board(W, H, hexc("#0b0a0a"), ground.hardboard_mesh(W, H, rng0, pitch=5.4), seed=2009, light=(0.1, 0.95))
rng = board.rng
view = Over(W, H, 1080, 700, 520, (-0.03, 1.63, -0.14), np.radians(43))
view.vy = 545
P = view.P

# --- tubes -----------------------------------------------------------------------------------
black, ultra, umber = hexc("#0b0a0a"), hexc("#1b2a7a"), hexc("#4a2a16")
viridian, ochre, cadred = hexc("#0f6b55"), hexc("#c0902f"), hexc("#c6281c")
lemon, white = hexc("#efe36a"), hexc("#f6f3ea")
night = mix((ultra, 2), (umber, 1), (black, 2))

# --- what the surfaces are -------------------------------------------------------------------
A_BODY = mix((white, 3), (umber, 0.35), (ochre, 0.12), (ultra, 0.18))     # putty-grey plastic
A_PAD = mix((white, 7), (umber, 0.25), (ultra, 0.12))                   # the white pad under the lid
A_LID = mix((white, 0.8), (umber, 0.6), (ultra, 0.4), (black, 0.3))                   # the lid's grey shell
A_FOLDER = mix((white, 1.4), (ochre, 1.8), (umber, 0.45), (lemon, 0.2))                 # buff case-notes folder
A_PAPER = mix((white, 8), (ochre, 0.1))
A_WALL = mix((white, 3), (ochre, 0.5), (umber, 0.3))                    # magnolia, as everywhere
A_CARPET = mix((ultra, 1), (umber, 1.4), (white, 0.6))

UP, DOWN, EAST, WEST, BACK, FRONT = v3(0, 1, 0), v3(0, -1, 0), v3(1, 0, 0), v3(-1, 0, 0), v3(0, 0, -1), v3(0, 0, 1)

# --- the machine -------------------------------------------------------------------------------
X0, X1, Z0, Z1, YT = -0.46, 0.52, 0.32, 0.98, 0.92     # its top
ZW = 1.10                                             # the wall behind it
GX0, GX1, GZ0, GZ1 = -0.36, 0.08, 0.47, 0.78          # the glass
YG = YT - 0.006
# the lid, hinged along the back of the glass and opened a little past upright
HZ, LD, LX0, LX1 = 0.86, 0.42, -0.40, 0.12
TH = np.radians(110)
lid_v = v3(0, np.sin(TH), -np.cos(TH)) * LD
lid = Plane((LX0, YT + 0.012, HZ), (LX1 - LX0, 0, 0), lid_v)
N_PAD = v3(0, -np.cos(TH), -np.sin(TH))
N_PAD = N_PAD / np.linalg.norm(N_PAD)
# the lamp stopped here, partway along its run, and stayed on
XB = -0.13

# the original, face down, dropped against the back of the glass a little skew
SA = np.radians(-3.0)
su, sv = v3(np.cos(SA), 0, np.sin(SA)), v3(-np.sin(SA), 0, np.cos(SA))
S0 = v3(GX0 + 0.004, YG + 0.001, GZ1 - 0.215)
SHEET = [S0, S0 + su * 0.297, S0 + su * 0.297 + sv * 0.21, S0 + sv * 0.21]


def on_sheet(x, z):
    d = v3(x, 0, z) - S0
    u, v = d @ su, d @ sv
    return (0 <= u <= 0.297) and (0 <= v <= 0.21)


# the case notes the sheet came out of, a fat folder dropped half over the right end of the glass
FA = np.radians(5)
fu, fv = v3(np.cos(FA), 0, np.sin(FA)), v3(-np.sin(FA), 0, np.cos(FA))
F0, FT = v3(0.035, YT, 0.45), 0.055
FOLD = [F0, F0 + fu * 0.24, F0 + fu * 0.24 + fv * 0.32, F0 + fv * 0.32]


def under_notes(x, z):
    d = v3(x, 0, z) - F0
    u, v = d @ fu, d @ fv
    return (0 <= u <= 0.24) and (0 <= v <= 0.32)


# --- what is lit: the tube under the glass, and what gets through the sheet -------------------
tube = mix((white, 10), (viridian, 0.45), (lemon, 1.1))
tube = tube / tube.max()
R = 26.0


def under_glass(S):
    """Radiance coming up out of the glass at S."""
    dx = S[0] - XB
    if under_notes(S[0], S[2]):
        return np.zeros(3)
    if on_sheet(S[0], S[2]):
        k = 0.9 * np.exp(-(dx / 0.028) ** 2) + 0.16 * np.exp(-(dx / 0.09) ** 2) + 0.03
    else:
        k = np.exp(-(dx / 0.007) ** 2) + 0.07 * np.exp(-(dx / 0.05) ** 2) + 0.004
    return tube * R * k


glass = Plane((GX0, YG, GZ0), (GX1 - GX0, 0, 0), (0, 0, GZ1 - GZ0))
lrng = np.random.default_rng(4)
src = Patches.on(glass, under_glass, 70, 10, facing=UP, rng=lrng, blockers=[(lid, 0.0)])
free = Patches(src.S, src.n, src.rad, src.dA)        # the same light, for points on the lid itself


def amb(N):
    """The corridor, through the open door behind me. Next to nothing."""
    return v3(0.0036, 0.0040, 0.0052) * (1.0 + 0.6 * max(0.0, -N[2]))


bounce = Patches.on(lid, lambda S: free.onto(S, N_PAD) * A_PAD, 8, 6, facing=N_PAD)
KB = 1.0


def light(Q, N):
    on_lid = abs((Q - lid.O) @ lid.n) < 2e-3
    return amb(N) + (free if on_lid else src).onto(Q, N) + KB * bounce.onto(Q, N)


# keyed once, on the edges of the notes where the lamp catches them across the glass
PROBE = lid.at((XB - LX0 + 0.04) / (LX1 - LX0), 0.3)
EXPO = keyed(light, (F0 + fv * 0.16 + v3(0, FT / 2, 0), -fu, A_PAPER), target=0.22)


def shade_at(Q, N, albedo, vary=0.0):
    a = albedo(Q) if callable(albedo) else albedo
    return room(a * light(Q, N) * EXPO) * (np.exp(rng.normal(0, vary)) if vary else 1.0)


def shader(albedo, N, vary=0.03):
    N = v3(*N)
    return lambda Q: shade_at(Q, N, albedo, vary)


def lum(c):
    return 0.2 * c[0] + 0.7 * c[1] + 0.1 * c[2]



if os.environ.get("CHECK"):
    print("EXPO", EXPO)
    for name, Q, N, a in [("pad low", lid.at(0.5, 0.1), N_PAD, A_PAD), ("pad probe", PROBE, N_PAD, A_PAD),
                          ("pad top", lid.at(0.5, 0.9), N_PAD, A_PAD), ("pad far R", lid.at(0.95, 0.4), N_PAD, A_PAD),
                          ("top front", v3(-0.1, YT, 0.38), UP, A_BODY), ("top R", v3(0.3, YT, 0.45), UP, A_BODY),
                          ("top L", v3(-0.42, YT, 0.6), UP, A_BODY), ("folder", F0 + fu * 0.12 + fv * 0.16 + v3(0, FT, 0), UP, A_FOLDER), ("folder side", F0 + fv * 0.16 + v3(0, FT / 2, 0), -fu, A_PAPER),
                          ("sheet top", v3(-0.2, YG, 0.7), UP, A_PAPER), ("front face", v3(0, 0.8, Z0), BACK, A_BODY),
                          ("wall above lid", v3(-0.13, 1.45, ZW), BACK, A_WALL), ("wall side", v3(0.4, 1.2, ZW), BACK, A_WALL),
                          ("wall low R", v3(0.6, 1.0, ZW), BACK, A_WALL)]:
        print(f"{name:16s}", np.round(shade_at(Q, N, a), 3))
    for nm, p in [("lid top L", lid.at(0, 1)), ("lid top R", lid.at(1, 1)), ("glass FL", v3(GX0, YG, GZ0)), ("glass FR", v3(GX1, YG, GZ0)),
                  ("top FL", v3(X0, YT, Z0)), ("top FR", v3(X1, YT, Z0)), ("top BL", v3(X0, YT, Z1)), ("bar front", v3(XB, YG, GZ0)),
                  ("floor front", v3(0, 0, Z0)), ("wall top", v3(0, 2.0, ZW))]:
        print(nm, np.round(P(p), 1))
    sys.exit()

# --- the planes I can see ------------------------------------------------------------------------
top_q = quad(view, [v3(X0, YT, Z0), v3(X1, YT, Z0), v3(X1, YT, Z1), v3(X0, YT, Z1)])
glass_q = quad(view, [v3(GX0, YG, GZ0), v3(GX1, YG, GZ0), v3(GX1, YG, GZ1), v3(GX0, YG, GZ1)])
face_q = quad(view, [v3(X0, YT - 0.02, Z0), v3(X1, YT - 0.02, Z0), v3(X1, 0.0, Z0), v3(X0, 0.0, Z0)])
LT = 0.03                                                             # the lid's thickness
lid_q = quad(view, [lid.at(0, 0), lid.at(1, 0), lid.at(1, 1), lid.at(0, 1)])
sheet_q = quad(view, SHEET)


def on_plane_z(sx, sy, z):
    d = view.ray(np.asarray(sx, dtype=np.float64), np.asarray(sy, dtype=np.float64))
    t = (z - view.eye[2]) / d[..., 2]
    return view.eye + d * t[..., None]


def wall_shade(sx, sy):
    Q = on_plane_z(sx, sy, ZW)
    return shade_at(Q, BACK, A_WALL, 0.02)


def face_shade(sx, sy):
    Q = on_plane_z(sx, sy, Z0)
    return shade_at(Q, BACK, A_BODY, 0.02)


def glow(Q):
    """The light itself, coming up out of the glass at Q, as paint. The lamp alone goes to white."""
    k = under_glass(Q) / R
    return np.minimum(1.0 - np.exp(-2.5 * k * tube), 0.95)


def sheet_col(Q):
    """The sheet: what it gets back from the lid, and what comes through it from the lamp."""
    a = shade_at(Q, UP, A_PAPER)
    g = glow(Q) * mix((white, 6), (ochre, 0.2)) / white
    return 1.0 - (1.0 - a) * (1.0 - g)


def glass_col(Q):
    """Bare glass: the dark of the machine under it, the lamp's spill, and a little of the lid in it."""
    d = Q - view.eye
    d = d / np.linalg.norm(d)
    r = d * v3(1, -1, 1)
    t = ((lid.O - Q) @ lid.n) / (r @ lid.n)
    refl = np.zeros(3)
    if t > 0:
        X = Q + r * t
        u, v = lid.uv(X)
        if 0 <= u <= 1 and 0 <= v <= 1:
            refl = shade_at(X, N_PAD, A_PAD) * 0.035
    inside = scale(night, 0.06)
    return inside + glow(Q) + refl


# =============================================================================================
# 1. Imprimatura. Thin coloured darks, scrubbed dry over the black; warmer where the light is.
# =============================================================================================
wash = Brush(width=130, bristle=2.6, opacity=0.4, dryness=0.55, pickup=0.3, thickness=0.2, jitter=0.12, deplete=0.0008)
for i in range(70):
    x, y = rng.uniform(-100, W + 100), rng.uniform(-50, H + 50)
    a = rng.uniform(0, np.pi)
    L = rng.uniform(300, 800)
    warm = np.exp(-((x - 480) / 330) ** 2 - ((y - 420) / 300) ** 2)
    c = mix((ultra, rng.uniform(0.6, 1.6) * (1 - 0.6 * warm)), (umber, rng.uniform(0.5, 2.0) + 2 * warm), (black, 4))
    board.stroke([(x - np.cos(a) * L / 2, y - np.sin(a) * L / 2), (x + np.cos(a) * L / 2, y + np.sin(a) * L / 2)],
                 wash, c, wobble=10)
board.dry()
board.stage("coloured darks over black")

# =============================================================================================
# 2. The dark is the board. The wall and the front of the machine get a few long strokes, dry,
#    dragged across at whatever angle the arm falls, and the rest is left as it is.
# =============================================================================================
dark = Brush(width=90, bristle=2.4, opacity=0.5, pickup=0.5, dryness=0.7, thickness=0.3, jitter=0.04, deplete=0.0005,
             taper=(0.12, 0.18))
wall_poly = np.array([(-60, -60), (W + 60, -60), (W + 60, top_q[2][1]), (-60, top_q[3][1])])
board.tape(wall_poly, feather=1.5)
board.tape(lid_q, mode="cut", feather=1.0)
scrub(board, None, dark.but(opacity=0.4, dryness=0.78, width=120), lambda x, y: scale(wall_shade(x, y), 0.5), 8, length=(700, 1300), angle=(-0.12, 0.12), along=9)
# what gets past the lid climbs the wall: dry strokes up from where it comes from, only the mesh catching
wall = Plane((-1.2, YT, ZW), (2.4, 0, 0), (0, 1.4, 0))
radiate(board, view, wall, ((XB + 1.2) / 2.4, 0.0), dark.but(width=60, opacity=0.5, dryness=0.74, taper=(0.4, 0.4)),
        shader(A_WALL, BACK, 0.02), 40, reach=1.4, along=9, spread=(0.2, np.pi - 0.2), r0=(0.1, 0.4))
board.untape()
scrub(board, face_q, dark.but(dryness=0.62), face_shade, 12, length=(500, 1100), angle=(-0.15, 0.15), along=7)
board.dry()
board.stage("the dark, left as the board")

# =============================================================================================
# 3. The top of the machine: rows across it, mixed along the row, the glass taped out.
# =============================================================================================
blk = Brush(width=18, opacity=0.85, pickup=0.55, dryness=0.32, thickness=0.5, jitter=0.03, deplete=0.0008)
board.tape(top_q, feather=0.8)
board.tape(glass_q, mode="cut", feather=0.6)
zt = lambda t: Z0 + t * (Z1 - Z0)  # noqa: E731
sweep(board, view, lambda t: v3(X0 - 0.05, YT, zt(t)), lambda t: v3(X1 + 0.05, YT, zt(t)), 14, blk.but(width=40, dryness=0.45, pickup=0.7),
      shader(A_BODY, UP, 0.02), along=14, wobble=2.0, max_w=90, overlap=2.2)
board.untape()
# the rounded front lip, just catching the lid
lip = [v3(X0, YT - 0.008, Z0 - 0.004), v3(X1, YT - 0.008, Z0 - 0.004)]
fine = Brush(width=3, bristle=0.9, opacity=0.85, pickup=0.0, thickness=0.6, jitter=0.03, gap=0.0, taper=(0.03, 0.05))
board.stroke(P(np.array(lip)), fine.but(width=4, opacity=0.7),
             [shade_at(v3(x, YT, Z0), v3(0, 0.7, -0.7), A_BODY) for x in np.linspace(X0, X1, 10)])
# the recess the glass sits in, a dark line round it
for a, b in ((v3(GX0, YG, GZ0), v3(GX1, YG, GZ0)), (v3(GX1, YG, GZ0), v3(GX1, YG, GZ1)), (v3(GX0, YG, GZ0), v3(GX0, YG, GZ1))):
    line3(board, view, a, b, fine.but(width=3, opacity=0.8), scale(night, 0.3))
board.dry()
board.stage("the top of the machine")

# =============================================================================================
# 4. The lid. Its grey edge, then the pad, each stroke running up from the glass into the dark.
# =============================================================================================
# the edge of the shell I see along the top and down the right side
shell = Brush(width=8, opacity=0.9, pickup=0.4, dryness=0.2, thickness=0.6, jitter=0.03, deplete=0.0006)
back = v3(0, np.cos(TH), np.sin(TH)) * LT                       # from the pad out to the lid's back
rim_q = quad(view, [lid.at(0, 1), lid.at(1, 1), lid.at(1, 1) + back, lid.at(0, 1) + back])
board.tape(rim_q, feather=0.4)
for s in np.linspace(0, 1, 4):
    line3(board, view, lid.at(-0.02, 1) + back * s, lid.at(1.02, 1) + back * s, shell.but(width=5),
          [shade_at(lid.at(u, 1) + back * s, v3(0, 1, 0), A_LID) for u in np.linspace(0, 1, 6)])
board.untape()
side_q = quad(view, [lid.at(1, 0), lid.at(1, 1), lid.at(1, 1) + back, lid.at(1, 0) + back])
board.tape(side_q, feather=0.4)
for s in np.linspace(0, 1, 3):
    line3(board, view, lid.at(1, -0.02) + back * s, lid.at(1, 1.02) + back * s, shell.but(width=4),
          [shade_at(lid.at(1, v) + back * s, EAST, A_LID) for v in np.linspace(0, 1, 6)])
board.untape()
# a plastic frame round the pad
FRM = 0.022
pad = Plane(lid.at(FRM / (LX1 - LX0), FRM / LD), lid.U * (1 - 2 * FRM / (LX1 - LX0)), lid.V * (1 - 2 * FRM / LD))
board.tape(lid_q, feather=0.5)
board.tape(quad(view, [pad.at(0, 0), pad.at(1, 0), pad.at(1, 1), pad.at(0, 1)]), mode="cut", feather=0.4)
sweep(board, view, lambda t: lid.at(t, -0.05), lambda t: lid.at(t, 1.05), 30, shell.but(width=6), shader(A_LID, N_PAD, 0.02), along=8)
board.untape()
pad_q = quad(view, [pad.at(0, 0), pad.at(1, 0), pad.at(1, 1), pad.at(0, 1)])
board.tape(pad_q, feather=0.5)
padb = Brush(width=26, opacity=0.85, pickup=0.75, dryness=0.1, thickness=0.6, jitter=0.012, gap=0.02, deplete=0.0004,
             taper=(0.15, 0.2))
sweep(board, view, lambda t: pad.at(t, -0.06), lambda t: pad.at(t, 1.06), 26, padb.but(pickup=0.05, jitter=0.008, gap=0.0), shader(A_PAD, N_PAD, 0.0),
      along=10, overlap=3.0, wobble=1.5)
# foam has no grain to follow, so the strokes over it follow the light: out from where the lamp is,
# below the hinge, each mixed along its length as the light falls away up the lid
ORG = ((XB - pad.O[0]) / pad.U[0], -0.25)
radiate(board, view, pad, ORG, padb.but(width=30, pickup=0.3, opacity=0.6, dryness=0.45, thickness=0.7, taper=(0.5, 0.3)),
        shader(A_PAD, N_PAD, 0.0), 110, reach=1.9, along=10, wobble=1.0, spread=(0.15, np.pi - 0.15), r0=(0.25, 0.7))
# years of toner on it: grey where the edges of the originals sat, worst along the hinge
smut = Brush(width=10, bristle=1.4, opacity=0.25, glaze=True, jitter=0.03, gap=0.1, taper=(0.3, 0.3))
for i in range(14):
    v = abs(rng.normal(0, 0.06))
    u0 = rng.uniform(0.0, 0.7)
    line3(board, view, pad.at(u0, v), pad.at(min(1, u0 + rng.uniform(0.1, 0.4)), v + rng.normal(0, 0.01)),
          smut.but(width=rng.uniform(4, 14)), mix((umber, 1), (black, 1), (white, 1)), wobble=2)
for u, v in ((0.02, 0.5), (0.02, 0.98), (0.75, 0.02)):
    line3(board, view, pad.at(u, 0.02), pad.at(u + (0.0 if u < 0.5 else 0.0), v), smut.but(width=5, opacity=0.18),
          mix((umber, 1), (black, 1), (white, 1)), wobble=1)
board.untape()
board.dry()
board.stage("the lid, lit from under")

# =============================================================================================
# 5. The case notes on the machine, and the panel.
# =============================================================================================
body = Brush(width=6, opacity=0.95, pickup=0.35, dryness=0.12, thickness=0.6, jitter=0.04, deplete=0.0005)
TOPF = [p + v3(0, FT, 0) for p in FOLD]
# the edges of the notes inside, toward me, then the cover
edge_q = quad(view, [FOLD[0], FOLD[1], TOPF[1], TOPF[0]])
board.tape(edge_q, feather=0.3)
for s in np.linspace(0.05, 0.95, 9):
    a, b = FOLD[0] + v3(0, FT * s, 0) - fu * 0.01, FOLD[1] + v3(0, FT * s, 0) + fu * 0.01
    c = shade_at(a + fu * 0.12, v3(0, 0.3, -0.95), A_PAPER if 0.15 < s < 0.85 else A_FOLDER, 0.08)
    board.stroke(P(np.array([a, b])), fine.but(width=2.2, opacity=0.9), c)
board.untape()
# its left side, the edges of every sheet in it, faces the lamp across the glass and is lit by it
side = quad(view, [FOLD[0], FOLD[3], TOPF[3], TOPF[0]])
board.tape(side, feather=0.3)
NF = -fu
for s in np.linspace(0.03, 0.97, 14):
    a, b = FOLD[0] + v3(0, FT * s, 0) - fv * 0.01, FOLD[3] + v3(0, FT * s, 0) + fv * 0.01
    alb = A_FOLDER if (s < 0.1 or s > 0.9) else scale(A_PAPER, rng.uniform(0.7, 1.0))
    board.stroke(P(np.array([a, b])), fine.but(width=2.0, opacity=0.9, pickup=0.2),
                 [shade_at(a + (b - a) * t, NF, alb, 0.04) for t in np.linspace(0, 1, 8)])
board.untape()
board.tape(quad(view, TOPF), feather=0.4)
sweep(board, view, lambda t: TOPF[0] + fv * 0.32 * t - fu * 0.02, lambda t: TOPF[1] + fv * 0.32 * t + fu * 0.02, 22,
      body.but(width=8, pickup=0.3, jitter=0.015, gap=0.0, dryness=0.25), shader(A_FOLDER, UP, 0.01), along=8, wobble=0.3, overlap=2.2)
board.untape()
# the cover stands a little proud of the notes: its edge, and the dark under it
line3(board, view, TOPF[0] - fu * 0.003, TOPF[1] + fu * 0.003, fine.but(width=2.5, opacity=0.9), scale(night, 0.35))
line3(board, view, TOPF[0] + v3(0, 0.002, 0), TOPF[1] + v3(0, 0.002, 0), fine.but(width=1.4, opacity=0.8),
      shade_at(TOPF[0] + fu * 0.1, v3(0, 0.6, -0.8), A_FOLDER) * 1.4)
# the coloured tab, and the patient label
tab = [TOPF[3] + fu * 0.16, TOPF[3] + fu * 0.22, TOPF[3] + fu * 0.22 + fv * 0.025, TOPF[3] + fu * 0.16 + fv * 0.025]
board.tape(quad(view, tab), feather=0.3)
board.fill(quad(view, tab), body.but(width=4), shade_at(tab[0], UP, mix((cadred, 2), (white, 0.6))), angle=0.1)
board.untape()
# the panel, front right, a shade darker
PZ0, PZ1, PX0, PX1 = 0.335, 0.43, 0.30, 0.50
pq = quad(view, [v3(PX0, YT + 0.002, PZ0), v3(PX1, YT + 0.002, PZ0), v3(PX1, YT + 0.002, PZ1), v3(PX0, YT + 0.002, PZ1)])
board.tape(pq, feather=0.4)
sweep(board, view, lambda t: v3(PX0 - 0.02, YT, PZ0 + t * (PZ1 - PZ0)), lambda t: v3(PX1 + 0.02, YT, PZ0 + t * (PZ1 - PZ0)), 8,
      body.but(width=6), shader(scale(A_BODY, 0.55), UP, 0.02), along=6)
board.untape()
for i, x in enumerate(np.linspace(PX0 + 0.09, PX1 - 0.03, 3)):
    for z in (PZ0 + 0.03, PZ0 + 0.07):
        c = P(v3(x, YT + 0.004, z))
        board.dab(c[0], c[1], Brush(width=7, opacity=0.9, thickness=0.8, gap=0, pickup=0.2), shade_at(v3(x, YT, z), UP, A_BODY) * 1.2,
                  angle=0.0, length=10)
board.dry()
board.stage("the case notes, and the panel")

# =============================================================================================
# 6. The glass, levelled; then the sheet on it, each row mixed along with what comes through.
# =============================================================================================
board.tape(glass_q, feather=0.4)
board.tape(sheet_q, mode="cut", feather=0.3)
fp = quad(view, FOLD + TOPF)
board.tape(fp[ConvexHull(fp).vertices], mode="cut", feather=0.3)
glassb = Brush(width=8, opacity=0.95, pickup=0.3, dryness=0.0, thickness=0.1, jitter=0.015, gap=0.0, level=1.0,
               taper=(0.04, 0.04))
gz = lambda t: GZ0 + t * (GZ1 - GZ0)  # noqa: E731
sweep(board, view, lambda t: v3(GX0 - 0.02, YG, gz(t)), lambda t: v3(GX1 + 0.02, YG, gz(t)), 44, glassb.but(jitter=0.006), glass_col, along=40, overlap=2.2)
board.untape()
board.tape(sheet_q, feather=0.35)
paperb = Brush(width=6, opacity=0.95, pickup=0.05, dryness=0.0, thickness=0.15, jitter=0.005, gap=0.0, deplete=0.0002)
sweep(board, view, lambda t: S0 + sv * 0.21 * t - su * 0.02, lambda t: S0 + sv * 0.21 * t + su * 0.317, 40, paperb, sheet_col,
      along=40, overlap=1.8)
board.dry()
# what is typed on the other side of it, showing through only where the lamp is behind it
ink = Brush(width=2.2, bristle=0.8, opacity=0.5, glaze=True, jitter=0.02, gap=0.05, taper=(0.05, 0.05))
inkc = mix((umber, 2), (ultra, 1), (black, 1))
for row in range(17):
    v = 0.025 + row * 0.0098
    if row in (3, 9):
        continue
    u = 0.03 + (0.05 if row in (0, 1) else 0.0)
    end = 0.27 - rng.uniform(0, 0.08 if row % 5 else 0.18)
    while u < end:
        w = rng.uniform(0.008, 0.03)
        a = S0 + su * (0.297 - u) + sv * v                        # face down: it reads backwards
        b = S0 + su * (0.297 - min(u + w, end)) + sv * v
        k = lum(glow((a + b) / 2))
        if k > 0.03:
            line3(board, view, a, b, ink.but(opacity=min(0.55, 1.2 * k)), inkc)
        u += w + rng.uniform(0.004, 0.009)
board.untape()
board.dry()
board.stage("the glass, and what was left on it")

# pull the room down at the edges, hardest along the front of the machine
gzb = Brush(width=160, bristle=2.6, opacity=0.22, glaze=True, jitter=0.02, gap=0.0, taper=(0.2, 0.2))
deep = mix((ultra, 2), (umber, 1.5))
for i in range(5):
    y = H - rng.uniform(0, 120)
    board.stroke([(-100, y), (W + 100, y + rng.normal(0, 10))], gzb, deep)
for x in (-40, W + 40):
    board.stroke([(x, -100), (x + rng.normal(0, 10), H + 100)], gzb.but(width=200), deep)
board.dry()

# =============================================================================================
# 7. White last. The lamp where nothing is over it, and the hot line through the sheet.
# =============================================================================================
hot = Brush(width=4, opacity=0.97, pickup=0.05, thickness=2.6, jitter=0.02, gap=0.0, deplete=0.0, taper=(0.02, 0.02))
lampc = mix((white, 12), (viridian, 0.35), (lemon, 0.9))
lampc = lampc / lampc.max() * 0.97
z_sheet_front = (S0 + su * ((XB - S0[0]) / su[0]))[2]
bw = 0.012 * view.ppm(v3(XB, YG, GZ0))
line3(board, view, v3(XB, YG, GZ0 + 0.002), v3(XB, YG, z_sheet_front - 0.001), hot.but(width=bw), lampc, smooth=False)
# the readout: one copy, and the jam light
lc = P(v3(PX0 + 0.04, YT + 0.004, PZ0 + 0.06))
board.dab(lc[0], lc[1], Brush(width=9, opacity=0.95, thickness=1.0, gap=0), mix((viridian, 2), (lemon, 2), (white, 2)), angle=0.0, length=22)
jc = P(v3(PX0 + 0.04, YT + 0.004, PZ0 + 0.025))
board.dab(jc[0], jc[1], Brush(width=5, opacity=0.95, thickness=1.2, gap=0), mix((cadred, 1), (ochre, 2), (white, 1)), angle=0.0, length=5)
board.dry()
board.stage("white last: the lamp under the glass")

finish(board, HERE, title="Photocopier, Medical Records, lower ground, 03:40", artist="nell-abara", year=2009,
       medium="Oil on hardboard, rough side", made="2026-11-12")
