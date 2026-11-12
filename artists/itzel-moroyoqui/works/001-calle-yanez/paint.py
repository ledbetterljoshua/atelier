"""Itzel Moroyoqui - Calle Yáñez, 46°

A tienda on Calle Yáñez with a lámina awning two metres deep over the pavement, ten to two in
August. She pulled the bike in under it to wait for the next order. Standing, looking down: the foot
of the shop wall, turquoise with a magenta skirting, the open door with the shop dark inside, the
awning's shade on the pavement with the corrugations along its edge, and the sun beyond it. Her
cooler box is half in and half out. The shopkeeper's garrafón of water is out in the sun, and it
hands some of it on.
"""
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[3]))
sys.path.insert(0, str(HERE.parents[1]))

from engine import Board, Brush, hexc, mix, scale  # noqa: E402
from engine.studio import finish  # noqa: E402
from tools import View, lay_ground, plywood, ray_box, sweep, sweep_ground, v3  # noqa: E402

W, H = 1440, 1800
rng0 = np.random.default_rng(1346)
PRIMER = hexc("#f1efe8")
board = Board(W, H, PRIMER, plywood(W, H, rng0), seed=46, light=(0.7, 0.25))
rng = board.rng
view = View(W, H, 1320, 1.6, 53)

# --- tubes -----------------------------------------------------------------------------------
white = hexc("#fbfaf5")
ultra, violet, turq = hexc("#26308f"), hexc("#4a2a86"), hexc("#0f8f95")
magenta, orange, cadyel = hexc("#c4206a"), hexc("#f2601c"), hexc("#f4c21c")
lemon, ochre = hexc("#eee65a"), hexc("#c99a3c")
m = mix

# --- the street --------------------------------------------------------------------------------
ZW = 2.2                 # the shop wall
AW_Y = 2.6               # the awning
SKIRT = 0.26             # the magenta skirting on the wall
DOOR = (-1.30, -0.42)    # the shop door, open
SUN = v3(0.95, 1.0, -0.15)
SUN /= np.linalg.norm(SUN)
KX, KZ = SUN[0] / SUN[1], SUN[2] / SUN[1]


def awning_edge(x):
    """Where the lámina stops, out over the pavement: not square to the wall, sagging a little
    between the posts, and each corrugation ending in a scallop."""
    return 0.12 + 0.15 * x + 0.03 * np.sin(x * 2.1 + 0.4) + 0.016 * np.abs(np.sin(np.pi * x / 0.076))


def under_awning(p):
    """True where the awning stands between a point and the sun."""
    k = (AW_Y - p[..., 1])
    return p[..., 2] + KZ * k > awning_edge(p[..., 0] + KX * k)


def shade_edge_z(x):
    """On the pavement, how far out toward her the awning's shade reaches at x."""
    return awning_edge(x + KX * AW_Y) - KZ * AW_Y


BOX = (v3(0.24, 0.0, 0.56), v3(0.66, 0.38, 0.88))     # her cooler box
JUG = v3(-0.12, 0.0, 0.46)                            # the garrafón
JR, JH, JS, JN = 0.135, 0.34, 0.44, 0.49              # radius, body, shoulder, neck top
LEVEL = 0.29                                           # the water in it, a few litres down
NECK = 0.034


def jug_r(h):
    r = np.where(h < JH, JR, JR * np.sqrt(np.clip(1 - ((h - JH) / (JS - JH)) ** 2, 0, 1)))
    r = np.where(h > JS - 0.03, np.maximum(r, NECK), r)
    return np.where((h < 0) | (h > JN), 0.0, r)


def toward_sun(p):
    """For points on the pavement: whether the box or the jug is in the sun's way, and how close to
    the jug's axis the sun's ray passes through its water."""
    lo, hi = BOX
    hits_box = np.zeros(p.shape[:-1], bool)
    through = np.zeros(p.shape[:-1], bool)
    best = np.full(p.shape[:-1], 9.0)
    for h in np.linspace(0.0, JN, 44):
        qx, qz = p[..., 0] + KX * h, p[..., 2] + KZ * h
        if h <= hi[1]:
            hits_box |= (qx >= lo[0]) & (qx <= hi[0]) & (qz >= lo[2]) & (qz <= hi[2])
        d = np.hypot(qx - JUG[0], qz - JUG[2])
        through |= d < jug_r(h)
        if 0.05 < h < JH - 0.03:
            best = np.minimum(best, d / JR)
    return hits_box, through, best


# --- what she sees at every point of the board ---------------------------------------------------
rays = view.rays()
eye = view.eye
tg = -eye[1] / np.minimum(rays[..., 1], -1e-9)
tw = (ZW - eye[2]) / np.maximum(rays[..., 2], 1e-9)
tb, bface = ray_box(eye, rays, *BOX)
tj = np.full((H, W), np.inf)
jb = view.P(np.array([[JUG[0] + sx * JR, h, JUG[2] + sz * JR] for sx in (-1, 1) for sz in (-1, 1) for h in (0, JN)]))
jx0, jx1 = int(jb[:, 0].min()) - 4, int(jb[:, 0].max()) + 4
jy0, jy1 = int(jb[:, 1].min()) - 4, int(jb[:, 1].max()) + 4
sub = rays[jy0:jy1, jx0:jx1]
blk = tj[jy0:jy1, jx0:jx1]
for t in np.linspace(1.1, 2.4, 600):
    q = eye + sub * t
    inside = np.hypot(q[..., 0] - JUG[0], q[..., 2] - JUG[2]) < jug_r(q[..., 1])
    blk[inside & np.isinf(blk)] = t

seewall = tw < tg
T = np.minimum.reduce([np.where(seewall, tw, np.inf), tg, tb, tj])
PT = eye + rays * T[..., None]
in_door = seewall & (PT[..., 0] > DOOR[0]) & (PT[..., 0] < DOOR[1])
WHAT = np.select([T == tj, T == tb, in_door, seewall],
                 [5, 2 + np.where(bface == 1, 0, np.where(bface == 2, 1, 2)), 6, 1], 0)
# 0 pavement, 1 wall, 2 box lid, 3 box front, 4 box side, 5 jug, 6 the doorway

GROUND = WHAT == 0
AWN = under_awning(PT)
BOXS, JUGS, JBEST = toward_sun(np.where(GROUND[..., None], PT, v3(9, 0, 9)))
SHADE = AWN | (GROUND & (BOXS | JUGS))
JUG_SH = GROUND & JUGS & ~AWN & ~BOXS
CAUSTIC = np.where(JUG_SH, np.exp(-(np.clip(JBEST, 0, 9) / 0.30) ** 2), 0.0)


def px(sx, sy):
    return int(np.clip(sy, 0, H - 1)), int(np.clip(sx, 0, W - 1))


def at(sx, sy):
    return PT[px(sx, sy)]


# --- colours ---------------------------------------------------------------------------------------
SUN_BASE = m((white, 7), (cadyel, 0.5), (magenta, 0.06), (orange, 0.08))
SUNLIT = [m((SUN_BASE, 4), (lemon, 0.35)),
          m((SUN_BASE, 4), (magenta, 0.07), (white, 0.6)),
          m((SUN_BASE, 4), (orange, 0.08)),
          m((SUN_BASE, 4), (ochre, 0.15), (white, 0.4)),
          m((SUN_BASE, 4), (white, 1.2))]
SH_MID = m((ultra, 2.0), (violet, 1.2), (white, 1.9))
SH_WARM = m((violet, 1.0), (magenta, 1.1), (white, 2.0), (orange, 0.2))
SH_WALLB = m((turq, 1.0), (ultra, 1.0), (white, 1.8))
WALL_T = m((turq, 3), (ultra, 0.9), (violet, 0.2))
WALL_F = m((turq, 3), (white, 1.4), (ultra, 0.2))
SKIRT_T = m((magenta, 3), (violet, 1.4), (ultra, 0.4))
SKIRT_F = m((magenta, 3), (white, 0.7), (violet, 0.3))
INSIDE = m((ultra, 2), (violet, 1.5), (magenta, 0.3), (turq, 0.3))


def near_edge(p):
    """0 at the wall, 1 at the edge of the shade: how much of the lit pavement this place can see."""
    ez = shade_edge_z(p[0])
    return float(np.clip((ZW - p[2]) / (ZW - ez), 0, 1)) ** 1.6


def ground_shade(sx, sy):
    p = at(sx, sy)
    e = near_edge(p)
    c = m((SH_MID, 1.5), (SH_WARM, 0.25 + 1.1 * e ** 10), (SH_WALLB, 0.1 + 0.9 * (1 - e) ** 4))
    lo, hi = BOX                                    # the lit box throws orange into the shade beside it
    dbx = max(lo[0] - p[0], 0, p[0] - hi[0]) + max(lo[2] - p[2], 0, p[2] - hi[2])
    c = m((c, 1.0), (m((orange, 2), (magenta, 0.6), (white, 1.0)), 0.35 * np.exp(-dbx / 0.08)))
    if DOOR[0] - 0.1 < p[0] < DOOR[1] + 0.1 and p[2] > ZW - 0.5:   # in front of the door, the dark spills out
        k = (1 - abs(p[0] - (DOOR[0] + DOOR[1]) / 2) / 0.55) * (p[2] - (ZW - 0.5)) / 0.5
        c = m((c, 1.0), (INSIDE, max(0.0, 0.5 * k)))
    return scale(c, 0.82 + 0.25 * e ** 6)


def wall_col(sx, sy):
    p = at(sx, sy)
    up = float(np.clip(p[1] / 0.6, 0, 1))         # lit from the pavement: lightest at its foot
    if p[1] < SKIRT:
        u = float(np.clip(p[1] / SKIRT, 0, 1))
        return m((SKIRT_F, 1.2 - u), (SKIRT_T, u + 0.4))
    return m((WALL_F, 1 - up + 0.1), (WALL_T, up + 0.3))


def sun_col(sx, sy):
    return SUNLIT[rng.integers(len(SUNLIT))]


# =====================================================================================================
# 1. The light, all of it: separate hot strokes over the whole pavement, past where the shade will
#    go. Acrylic in the sun: no pickup, and nothing runs into anything.
two_inch = Brush(width=80, bristle=3.0, opacity=0.97, pickup=0.0, deplete=0.0010, jitter=0.03,
                 thickness=0.12, wander=1.2, gap=0.03)
pav = (GROUND | (WHAT == 5) | (WHAT >= 2) & (WHAT <= 4)).astype(np.float32)


def on(mask):
    def where(x, z):
        q = view.P(v3(x, 0, z))
        return 0 <= q[0] < W and 0 <= q[1] < H and mask[int(q[1]), int(q[0])] > 0.5
    return where


board.tape_where(pav)
lay_ground(board, view, on(pav), two_inch, lambda p: sun_col(0, 0), 1100, 0.9, 0.0, rng, width_m=0.10,
           jitter=0.12, wobble=3, area=(-2.0, 2.0, -0.15, 2.3))
board.dry()
lay_ground(board, view, on(pav), two_inch.but(opacity=0.8, dryness=0.3), lambda p: sun_col(0, 0), 260,
           0.6, 0.5, rng, width_m=0.08, jitter=0.3, wobble=3, area=(-2.0, 2.0, -0.15, 2.3))
board.dry()
# the kerb, painted yellow for no parking, and the street beyond it, both in full sun
CURB_Z = lambda x: 0.13 + 0.08 * x
ASPH = GROUND & (PT[..., 2] < CURB_Z(PT[..., 0]))
CURB = GROUND & ~ASPH & (PT[..., 2] < CURB_Z(PT[..., 0]) + 0.10)
for reg, col, k in ((ASPH, m((ultra, 1.2), (orange, 0.8), (violet, 0.4), (white, 1.4)), 0.62),
                    (CURB, m((cadyel, 2.0), (lemon, 0.4), (white, 2.2), (orange, 0.1)), 1.0)):
    r = reg.astype(np.float32)
    board.tape_where(r, feather=0.7)
    for zs in (np.arange(-0.2, 0.6, 0.025), np.arange(-0.19, 0.6, 0.04)):
        sweep_ground(board, view, r, two_inch.but(width=50, pickup=0.0, opacity=0.98),
                     lambda p, col=col, k=k: scale(col, k * rng.uniform(0.94, 1.06)), rng, zs=zs, samples=12,
                     wobble=1.5)
board.untape()
board.dry()
board.stage("the light, all of it")

# the joints in the pavement and the broom marks across it, while she is in the light
one_inch = Brush(width=30, bristle=1.3, opacity=0.9, pickup=0.0, deplete=0.00015, jitter=0.03, thickness=0.3)
joint = m((white, 1.2), (ochre, 1.8), (violet, 0.5), (orange, 0.3))
broom = m((white, 3), (ochre, 1.2), (orange, 0.3), (magenta, 0.1))
paving = (GROUND & ~ASPH & ~CURB).astype(np.float32)
board.tape_where(paving)
BROOM = Brush(width=4, bristle=0.8, opacity=0.45, pickup=0.0, dryness=0.35, deplete=0.0008, gap=0.35,
              thickness=0.15, taper=(0.15, 0.15))
lay_ground(board, view, on(paving), BROOM, lambda p: broom, 2400, 0.5, 0.0, rng, width_m=0.007, jitter=0.03,
           wobble=0.4)
JOINTS_Z, JOINTS_X = (0.38, 1.38), (-0.70, 1.10)


def joint_lines():
    """The saw-cuts in the pavement, clipped to the board so the brush is not spent off the edge."""
    out = []
    lines = [[v3(x, 0, zj) for x in np.linspace(-2.4, 2.4, 60)] for zj in JOINTS_Z]
    lines += [[v3(xj, 0, z) for z in np.linspace(0.0, ZW, 60)] for xj in JOINTS_X]
    for ln in lines:
        q = view.P(np.array(ln))
        ok = (q[:, 0] > -20) & (q[:, 0] < W + 20) & (q[:, 1] > -20) & (q[:, 1] < H + 20)
        if ok.sum() > 1:
            qq = q[ok]
            out.append(np.vstack([qq[::4], qq[-1:]]) if len(qq) > 8 else qq)
    return out


for ln in joint_lines():
    board.stroke(ln, one_inch.but(width=6, opacity=0.95), joint, wobble=0.6)
board.dry()
board.untape()

# =====================================================================================================
# 2. The shade, over the light, as one shape. In here the paint stays open and runs together.
wet_two = Brush(width=84, bristle=3.0, opacity=0.97, pickup=0.45, deplete=0.0006, jitter=0.03,
                thickness=0.12, wander=1.2, gap=0.02)
gshade = (SHADE & GROUND).astype(np.float32)
board.tape_where(gshade, feather=0.8)
shade_run = lambda p: ground_shade(*view.P(p))
TINTS = [violet, ultra, magenta, turq, white]


def vary(r):
    tint, w, k = TINTS[r.integers(len(TINTS))], r.uniform(0.08, 0.3), r.uniform(0.92, 1.08)
    return lambda c: scale(m((c, 1.0), (tint, w)), k)


sweep_ground(board, view, gshade, wet_two.but(width=74, pickup=0.08), shade_run, rng,
             zs=np.arange(0.3, 2.3, 0.05), samples=14, wobble=2.5, vary=vary)
for a0, op in ((0.5, 0.7), (-0.45, 0.6)):
    for z0 in rng.permutation(np.arange(-3.0, 3.0, 0.085)):
        P3 = np.array([v3(x, 0, z0 + np.tan(a0) * x) for x in np.linspace(-2.6, 2.6, 14)])
        pts = view.P(P3)
        ok = [(0 <= q[0] < W and 0 <= q[1] < H and gshade[int(q[1]), int(q[0])] > 0.5) for q in pts]
        if sum(ok) < 1:
            continue
        idx = np.nonzero(ok)[0]
        i0, i1 = max(0, idx[0] - 1), min(len(pts) - 1, idx[-1] + 1)
        f = vary(rng)
        cols = [f(shade_run(P3[min(max(i, idx[0]), idx[-1])])) for i in range(i0, i1 + 1)]
        board.stroke(pts[i0:i1 + 1], wet_two.but(width=66, opacity=op), cols, wobble=2.0)

# the shopkeeper threw a bucket of water out front to lay the dust; in the shade it has not dried
yy, xx = np.mgrid[0:H, 0:W]
splash_c = view.P(v3(-0.55, 0, 1.75))
noise = __import__("engine").ground.fbm(W, H, np.random.default_rng(7), base=9, octaves=4)
dist = np.hypot((xx - splash_c[0]) / 420.0, (yy - splash_c[1]) / 170.0)
WET = (gshade > 0.5) & (dist + 0.55 * (noise - 0.5) < 0.62)
wet_m = WET.astype(np.float32)
board.tape_where(wet_m, feather=2.5)
WETC = m((ultra, 1.8), (violet, 1.0), (turq, 0.6), (white, 0.5))
sweep(board, wet_m, wet_two.but(width=60, opacity=0.85, pickup=0.5, level=0.8),
      lambda x, y: scale(m((WETC, 2.0), (ground_shade(x, y), 1.0)), 0.75), angle=0.05, spacing=26, rng=rng,
      every=60, wobble=2.0, vary=vary)
board.tape_where(gshade, feather=0.8)
lay_ground(board, view, on(gshade), BROOM.but(opacity=0.35, pickup=0.2), lambda p: scale(m((SH_MID, 1), (ultra, 0.7)), 0.75),
           1500, 0.5, 0.0, rng, width_m=0.007, jitter=0.03, wobble=0.4)
lay_ground(board, view, on(gshade), BROOM.but(opacity=0.3, pickup=0.2), lambda p: m((SH_MID, 1), (white, 0.5)),
           900, 0.5, 0.0, rng, width_m=0.006, jitter=0.03, wobble=0.4)
# the joints again, where the shade went over them: darker, bluer, and wet into it
for ln in joint_lines():
    board.stroke(ln, one_inch.but(width=8, opacity=0.95, pickup=0.2), scale(m((SH_MID, 1), (ultra, 1.0), (violet, 0.8)), 0.45),
                 wobble=0.6)

# what the wind left in there with her: mesquite pods, a bottle cap
POD = scale(m((ochre, 1.6), (violet, 0.8), (magenta, 0.6), (orange, 0.3)), 0.8)
for (px0, pz0, ang, bend) in ((-0.95, 1.55, 0.3, 0.025), (0.05, 1.92, -0.5, -0.03), (1.0, 1.42, 1.1, 0.02),
                              (-0.35, 1.18, 2.4, 0.02)):
    t = np.linspace(-1, 1, 7)
    L = 0.16
    pts3 = np.array([v3(px0 + np.cos(ang) * L / 2 * u - np.sin(ang) * bend * (1 - u * u),
                        0.004, pz0 + np.sin(ang) * L / 2 * u + np.cos(ang) * bend * (1 - u * u)) for u in t])
    q = view.P(pts3)
    sc = view.scale_at(pts3[3])
    board.stroke(q, Brush(width=0.024 * sc, bristle=1.2, opacity=0.95, pickup=0.1, thickness=0.3, taper=(0.25, 0.3),
                 gap=0.0), [scale(POD, 0.8), POD, scale(POD, 0.75)], wobble=0.0)
    board.stroke(q + np.array([0.004 * sc, -0.003 * sc]), Brush(width=0.004 * sc, bristle=0.8, opacity=0.6, pickup=0.0,
                 thickness=0.1, taper=(0.3, 0.3)), m((POD, 1), (white, 1.2)), wobble=0.0)
cap_c = v3(-0.62, 0.006, 1.30)
q = view.P(np.array([cap_c + v3(0.017 * np.cos(a), 0, 0.017 * np.sin(a)) for a in np.linspace(0, 2 * np.pi, 20)]))
board.tape(q, mode="and")
cq = q.mean(0)
for k in range(3):
    board.dab(cq[0], cq[1] + (k - 1) * 4, Brush(width=16, bristle=1.0, opacity=0.95, pickup=0.0, thickness=0.3),
              m((magenta, 1.5), (orange, 0.6), (violet, 0.6)), angle=0.0, length=22)
board.tape_where(gshade, feather=0.8)
board.dab(cq[0] + 3, cq[1] - 2, Brush(width=5, bristle=0.8, opacity=0.8, pickup=0.0), m((magenta, 1), (white, 1.5)), angle=0.0, length=8)
board.untape()
board.stage("the pavement in the shade")

WALLY = PT[..., 1]
for part in ((WHAT == 1) & (WALLY >= SKIRT), (WHAT == 1) & (WALLY < SKIRT)):
    reg = part.astype(np.float32)
    board.tape_where(reg, feather=0.6)
    sweep(board, reg, wet_two.but(width=60, opacity=0.98, pickup=0.03), wall_col, angle=np.pi / 2 + 0.03,
          spacing=22, rng=rng, every=30, wobble=1.0)
    sweep(board, reg, wet_two.but(width=70, opacity=0.9, pickup=0.03, jitter=0.015), wall_col, angle=np.pi / 2 - 0.03,
          spacing=30, rng=rng, every=30, wobble=1.0, vary=lambda r: (lambda c, k=r.uniform(0.95, 1.05): scale(c, k)))
    sweep(board, reg, wet_two.but(width=60, opacity=0.6, pickup=0.4), wall_col, angle=np.pi / 2, spacing=36,
          rng=rng, every=30, wobble=1.0)
    board.untape()

# the shop, dark inside
door = (WHAT == 6).astype(np.float32)
board.tape_where(door, feather=0.6)
for k in range(2):
    sweep(board, door, wet_two.but(width=60, opacity=0.98, pickup=0.03), lambda x, y: scale(INSIDE, 0.26 + 0.3 * (y / 440) ** 2),
          angle=np.pi / 2 + 0.02 - 0.04 * k, spacing=24, rng=rng, every=40, wobble=1.0)
board.untape()

# inside: two shelves low down, the packets on them just catching what comes in at the door
board.tape_where(door, feather=0.6)
for sy_, hgt in ((0.12, 0.10), (0.40, 0.12)):
    for xx in np.arange(DOOR[0] + 0.05, DOOR[1] - 0.04, 0.055):
        c = [magenta, orange, cadyel, turq, white][rng.integers(5)]
        p0 = view.P(v3(xx, sy_, ZW + 0.35))
        p1 = view.P(v3(xx, sy_ + hgt * rng.uniform(0.6, 1.0), ZW + 0.35))
        board.stroke([p0, p1], Brush(width=0.04 * view.scale_at(v3(xx, sy_, ZW + 0.35)), bristle=1.6, opacity=0.6,
                     pickup=0.3, thickness=0.1), scale(m((c, 1), (INSIDE, 2.5)), 0.5), wobble=0.5)
board.untape()
fr = view.P(np.array([v3(DOOR[1] + 0.02, y, ZW) for y in np.linspace(0, 1.2, 6)]))
board.stroke(fr, one_inch.but(width=12, opacity=0.9, pickup=0.2), m((violet, 1), (ultra, 1), (white, 1.2)), wobble=0.4)

# where the wall stands on the pavement
foot = view.P(np.array([v3(x, 0.0, ZW - 0.004) for x in np.linspace(-2.6, 2.6, 12)]))
board.stroke(foot, one_inch.but(width=10, opacity=0.9, pickup=0.4), m((ultra, 2), (violet, 1.5), (white, 0.5)),
             wobble=0.8)
board.stage("the wall and the door")

# =====================================================================================================
# 3. The box: hers, orange, its back edge just under the awning.
NORM = {2: v3(0, 1, 0), 3: v3(0, 0, -1), 4: v3(-1, 0, 0)}
BOX_SUN = m((orange, 3), (cadyel, 0.5), (white, 0.3))
BOX_HOT = m((orange, 1), (cadyel, 1.0), (white, 2.0))
BOX_SH = m((orange, 1.2), (magenta, 1.0), (violet, 0.7))


def box_col(sx, sy):
    iy, ix = px(sx, sy)
    f = int(WHAT[iy, ix])
    f = f if f in NORM else 3
    p = PT[iy, ix]
    I = max(0.0, float(NORM[f] @ SUN))
    if I > 0.05 and not under_awning(p):
        if f == 2:
            return m((BOX_SUN, 1.0), (BOX_HOT, 2.4 * I))
        return scale(m((BOX_SUN, 1.0), (magenta, 0.25)), 0.5 + 0.5 * I)
    return scale(BOX_SH, 0.62 if f == 4 else 0.85)


box_brush = Brush(width=36, bristle=2.4, opacity=0.97, pickup=0.3, deplete=0.0008, jitter=0.03,
                  thickness=0.15, wander=0.8, gap=0.02)
for f, ang in ((4, np.pi / 2), (3, np.pi / 2 + 0.02), (2, 0.02)):
    for part in (AWN, ~AWN):                     # the awning's edge crosses the lid: two shapes, not a blur
        reg = ((WHAT == f) & part).astype(np.float32)
        if reg.sum() < 20:
            continue
        board.tape_where(reg, feather=0.6)
        for k in range(2):
            sweep(board, reg, box_brush.but(pickup=0.05 if k == 0 else 0.3), box_col, angle=ang + 0.04 * k,
                  spacing=16, rng=rng, every=12, wobble=0.6, over=30)
        board.untape()
# the lid's lip, a little proud all round, and the strap
lo, hi = BOX
lip = [v3(lo[0], hi[1] - 0.035, lo[2]), v3(hi[0], hi[1] - 0.035, lo[2])]
board.stroke(view.P(np.array(lip)), box_brush.but(width=7, pickup=0.0), m((orange, 1), (magenta, 0.5), (violet, 0.4)),
             wobble=0.4)
side = [v3(lo[0], hi[1] - 0.035, lo[2]), v3(lo[0], hi[1] - 0.035, hi[2])]
board.stroke(view.P(np.array(side)), box_brush.but(width=6, pickup=0.0), m((magenta, 1), (violet, 1.0)), wobble=0.4)
board.stage("the box")

# =====================================================================================================
# 4. The garrafón, out in the sun: twenty litres of water with the light going through it.
WATER = m((turq, 1.0), (ultra, 0.5), (white, 9.0))
WATER_D = m((ultra, 1.3), (turq, 1.4), (white, 2.2))
CAP = m((ultra, 2.0), (turq, 0.4), (white, 1.6))
SH_JUG = m((ultra, 1.0), (turq, 0.9), (violet, 0.3), (white, 3.4))


def jug_col(sx, sy):
    p = at(sx, sy)
    hd = np.hypot(p[0] - JUG[0], p[2] - JUG[2])
    if p[1] > JS - 0.03 and hd < NECK + 0.004:
        return CAP
    n = np.array([p[0] - JUG[0], 0.0, p[2] - JUG[2]])
    if p[1] > JH:                                   # the shoulder turns up toward the sky
        n[1] = (p[1] - JH) / (JS - JH) * JR
    n /= np.linalg.norm(n) + 1e-9
    I = max(0.0, float(n @ SUN))
    v = view.eye - p
    v /= np.linalg.norm(v)
    rim = 1.0 - abs(float(n @ v))
    if p[1] > LEVEL:                               # above the water: only the plastic, pale
        c = m((WATER, 1.0 + 1.6 * I), (turq, 0.12), (WATER_D, 0.3 + 1.5 * rim ** 3))
        return scale(c, 0.86 + 0.12 * I)
    c = m((WATER, 0.4 + 1.2 * I), (WATER_D, 0.5 + 3.0 * rim ** 3), (turq, 0.15), (SUN_BASE, 1.0 * (1 - rim)))
    return scale(c, 0.78 + 0.3 * I)


jreg = (WHAT == 5).astype(np.float32)
board.tape_where(jreg, feather=0.5)
for k in range(2):
    sweep(board, jreg, box_brush.but(width=30, pickup=0.05 if k == 0 else 0.4), jug_col,
          angle=np.pi / 2 + 0.06 * (k - 0.5), spacing=16, rng=rng, every=14, wobble=0.6, over=20,
          vary=lambda r: (lambda c, k=r.uniform(0.9, 1.1): scale(c, k)))
# the rings moulded round it, seen on the side toward her
for hr, w, c in ((0.07, 6, WATER_D), (0.15, 6, WATER_D), (0.23, 6, WATER_D), (LEVEL, 9, m((ultra, 1), (turq, 1.2), (white, 0.8)))):
    th = np.linspace(np.pi * 1.02, np.pi * 1.98, 14)
    ring = view.P(np.array([v3(JUG[0] + JR * 1.01 * np.cos(t), hr, JUG[2] + JR * 1.01 * np.sin(t)) for t in th]))
    board.stroke(ring, box_brush.but(width=w, pickup=0.2, opacity=0.8, deplete=0.0002), c, wobble=0.3)
board.untape()

# the cap, on its short neck
capP = view.P(np.array([v3(JUG[0] + NECK * 1.1 * np.cos(a), JN, JUG[2] + NECK * 1.1 * np.sin(a)) for a in np.linspace(0, 2 * np.pi, 24)]))
board.tape(capP)
cc = capP.mean(0)
for k in range(4):
    board.dab(cc[0], cc[1] + (k - 1.5) * 7, Brush(width=34, bristle=1.4, opacity=0.95, pickup=0.1, thickness=0.3),
              m((ultra, 1.4), (turq, 0.7), (white, 1.2)), angle=0.03, length=60)
board.dab(cc[0] + 7, cc[1] - 4, Brush(width=9, bristle=1.6, opacity=0.9, pickup=0.3, thickness=0.4, taper=(0.4, 0.4)), white, angle=0.6, length=9)
board.untape()

# where it stands: a dark line round the foot of it, on the side toward her
base = view.P(np.array([v3(JUG[0] + JR * np.cos(t), 0.004, JUG[2] + JR * np.sin(t)) for t in np.linspace(np.pi * 0.95, np.pi * 2.0, 16)]))
board.tape_where((WHAT != 5).astype(np.float32))
board.stroke(base + np.array([0, 2]), Brush(width=9, bristle=1.0, opacity=0.8, pickup=0.0, thickness=0.1, taper=(0.3, 0.3)),
             m((ultra, 1.5), (violet, 1.0), (white, 0.6)), wobble=0.3)
lo, hi = BOX
bb = view.P(np.array([v3(lo[0], 0.004, lo[2]), v3(hi[0], 0.004, lo[2])]))
board.stroke(np.vstack([bb[:1], bb.mean(0, keepdims=True), bb[1:]]) + np.array([0, 2]),
             Brush(width=9, bristle=1.0, opacity=0.8, pickup=0.0, thickness=0.1, taper=(0.1, 0.1)),
             m((violet, 1.5), (magenta, 0.6), (white, 0.6)), wobble=0.3)
board.untape()

# its shadow on the lit pavement, lighter and bluer than the awning's: the water lets most of it through
jsh = JUG_SH.astype(np.float32)
board.tape_where(jsh, feather=0.8)
sweep(board, jsh, box_brush.but(width=30, pickup=0.35), lambda x, y: SH_JUG, angle=0.25, spacing=14, rng=rng,
      every=20, wobble=0.6, over=30)
board.untape()
board.stage("the garrafón")

# =====================================================================================================
# 5. The edge, cut once with the lettering brush along its whole length, from the shade side.
#    Where shade meets sun the shade looks its deepest and most violet.
edge_pts, run = [], []
for sx in range(0, W, 3):
    col = AWN[:, sx] & GROUND[:, sx]
    ys = np.nonzero(col)[0]
    if len(ys) == 0:
        if len(run) > 1:
            edge_pts.append(run)
        run = []
        continue
    y = ys.max()
    if y >= H - 2 or not GROUND[min(H - 1, y + 3), sx] or (run and abs(y - run[-1][1]) > 14):
        if len(run) > 1:
            edge_pts.append(run)
        run = [] if y >= H - 2 or not GROUND[min(H - 1, y + 3), sx] else [(sx, y)]
        continue
    run.append((sx, y))
if len(run) > 1:
    edge_pts.append(run)
EDGE = scale(m((violet, 1.5), (ultra, 1.0), (magenta, 0.8), (white, 0.4)), 0.62)
letter = Brush(width=14, bristle=1.2, opacity=0.95, pickup=0.25, deplete=0.0001, jitter=0.03, thickness=0.15,
               taper=(0.01, 0.01), gap=0.0)
board.tape_where(gshade, feather=0.6)
for seg in edge_pts:
    seg = np.array(seg, dtype=float)
    seg[:, 1] -= 4
    board.stroke(seg, letter, EDGE, wobble=0.0, smooth=False)
board.untape()
board.stage("the edge")

# =====================================================================================================
# 6. Sun handed on twice: what the jug's water gathers and puts down in its own shadow, and what its
#    side throws back. The only white in the picture.
cz = (CAUSTIC > 0.06).astype(np.float32)
board.tape_where(np.clip(CAUSTIC * 3.5, 0, 1).astype(np.float32), feather=5.0)
CYAN = m((turq, 1.0), (white, 3.0), (lemon, 0.2))
ys, xs = np.nonzero(CAUSTIC > 0.06)
cx0, cy0 = xs.mean(), ys.mean()
sd0 = np.array([-1.0, 0.18]) / np.hypot(1, 0.18)
cx0, cy0 = cx0 + sd0[0] * 75, cy0 + sd0[1] * 75
sd = np.array([-1.0, 0.18]) / np.hypot(1, 0.18)     # along the shadow, away from the jug
L = (xs.max() - xs.min()) * 0.9
for k in range(9):
    o = rng.normal(0, 10)
    c0 = np.array([cx0, cy0]) + np.array([-sd[1], sd[0]]) * o
    board.stroke([c0 - sd * L / 2, c0, c0 + sd * L / 2], Brush(width=34, bristle=2.2, opacity=0.9, pickup=0.4,
                 thickness=0.2, taper=(0.3, 0.3)), [CYAN, m((CYAN, 1), (white, 1.5)), CYAN], wobble=1.0)
hot = np.clip((CAUSTIC - 0.3) * 3, 0, 1).astype(np.float32)
board.tape_where(hot, feather=2.0)
for k in range(3):
    c0 = np.array([cx0, cy0]) + rng.normal(0, 4, 2)
    board.stroke([c0 - sd * L * 0.35, c0, c0 + sd * L * 0.35], Brush(width=22, bristle=2.0, opacity=1.0, pickup=0.0,
                 thickness=1.0, taper=(0.3, 0.3)), white, wobble=0.5)
board.untape()

# a glint down the jug's lit side, where it looks back at the sun past her shoulder
jx = view.P(np.array([v3(JUG[0] + JR * 0.55, h, JUG[2] - JR * 0.83) for h in np.linspace(0.05, JH - 0.02, 6)]))
board.tape_where(jreg)
board.stroke(jx, Brush(width=10, bristle=1.4, opacity=1.0, pickup=0.0, thickness=1.0, taper=(0.2, 0.3)), white, wobble=0.5)
board.untape()
board.stage("sun handed on twice")

finish(board, HERE, title="Calle Yáñez, 46°", year=2024, medium="Acrylic on primed plywood")
