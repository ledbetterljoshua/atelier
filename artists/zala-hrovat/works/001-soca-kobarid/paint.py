"""Zala Hrovat - Soča at Kobarid, 9 June 1983, 58 cm

Straight down over the upstream parapet of the Kobarid bridge, mid-morning, sun behind me and to
the right. A gravel bar on the left, white limestone; the bar drops off into the channel, which
runs diagonally under me toward the bridge. A beech leaf going over the edge of the drop.
The bridge's shadow lies across the bottom, with the railing posts in it.
"""
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[3]))
sys.path.insert(0, str(HERE.parents[1]))

from engine import Board, Brush, ground, hexc, mix, scale  # noqa: E402
from engine.studio import finish  # noqa: E402
from tools import (Water, glaze_by_depth, leaf_outline, offset_through_water, pack_stones, poly_mask,  # noqa: E402
                   scatter, smoothstep, stone, streamline, sun_net, tape_where, with_the_current)

W, H = 1350, 1800
PPM = 540.0                      # the frame is two and a half metres of river
rng0 = np.random.default_rng(1983)
board = Board(W, H, hexc("#f4f1e8"), ground.smooth_panel(W, H, rng0), seed=609)
rng = board.rng

# --- tubes ---------------------------------------------------------------------------------------
white, ochre, umber, sienna = hexc("#f5f2ea"), hexc("#c49a45"), hexc("#6b5a44"), hexc("#8a4a26")
payne, phthalo, turq, ultra = hexc("#2e3640"), hexc("#0b5a4a"), hexc("#1f9a9a"), hexc("#23338c")
cadyel, cadorange = hexc("#f2b01e"), hexc("#e8701a")

# --- where the sun is ----------------------------------------------------------------------------
SUN = np.array([0.95, 0.31]); SUN /= np.linalg.norm(SUN)      # toward the light, on the board
SUN_ELEV = 67.0                                                 # 46 N, early June, near noon
SKY = mix((white, 3), (ultra, 1), (payne, 0.4))                 # what fills the shadows


# --- the reach -----------------------------------------------------------------------------------
def edge(y):
    """x of the lip of the drop-off."""
    return W * (0.64 - 0.28 * y / H) + 28 * np.sin(y / 170 + 0.7) + 14 * np.sin(y / 61)


def depth(x, y):
    x = np.asarray(x, dtype=np.float64)
    y = np.asarray(y, dtype=np.float64)
    e = edge(y)
    s = smoothstep(-70, 160, x - e)
    bar = 0.09 + 0.16 * smoothstep(-400, 0, x - e) + 0.03 * np.sin(x / 90 + y / 140)
    deep = 0.9 + 0.9 * smoothstep(40, 640, x - e) ** 1.3 + 0.12 * np.sin(y / 230 + x / 300)
    return bar * (1 - s) + deep * s


def vel(x, y):
    e = edge(y)
    s = smoothstep(-70, 160, x - e)
    vx = -0.21 + 0.10 * np.sin(y / 95 + x / 160) * (1 - 0.6 * s)
    vy = 1.0
    # the seam: water off the bar curls into the channel along the lip
    k = np.exp(-((x - e - 40) / 90) ** 2)
    vx += 0.35 * k * np.sin(y / 120)
    # slow lanes in the channel that lean one way and then the other
    vx += 0.22 * s * np.sin(y / 240 + x / 420 + 1.0)
    return vx, vy * (0.6 + 0.6 * s)


# --- the bridge's shadow -------------------------------------------------------------------------
# The bottom edge of the board is the bridge's face. Deck edge 4 m above the water, an iron railing
# 1 m above that with a top rail and square balusters every 25 cm. The sun is off to the right and a
# little behind, so the shadow comes out from the bridge only a short way and the balusters lie long.
_reach = 1.0 / np.tan(np.radians(SUN_ELEV))                    # horizontal shadow per metre of height
DECK_U = 4.0 * _reach * SUN[1] * PPM                           # px up from the bottom edge
RAIL_U = 5.0 * _reach * SUN[1] * PPM
RAIL_TH, POST_EVERY, POST_W = 9.0, 0.25 * PPM, 0.02 * PPM / SUN[1]   # a 2 cm bar lies wide
SLANT = SUN[0] / SUN[1]                                         # px across per px up


PEN = np.radians(0.53) * PPM * _reach                           # penumbra per metre of height, px


def shade_surface(x, y):
    """1 in sun, 0 in the bridge's shadow, at the water surface. The sun is not a point: the railing,
    five metres up, throws a soft shadow, and a 2 cm baluster hardly a shadow at all."""
    u = (H - y) + 0.02 * (x - W / 2)
    pd, pr = 4.0 * PEN * SUN[1], 5.0 * PEN * SUN[1]
    deck = smoothstep(DECK_U + pd, DECK_U - pd, u)
    rail = smoothstep(RAIL_U - RAIL_TH - pr, RAIL_U - RAIL_TH + pr, u) * smoothstep(RAIL_U + pr, RAIL_U - pr, u) * 0.75
    ph = np.mod(x + SLANT * (u - DECK_U) + 30, POST_EVERY)
    pp = 4.6 * PEN / SUN[1] * 0.5
    post = (smoothstep(DECK_U - 4, DECK_U, u) * smoothstep(RAIL_U, RAIL_U - 4, u)
            * smoothstep(POST_W + pp, POST_W - pp, ph) * smoothstep(-pp, pp, ph) * 0.8)
    return 1.0 - np.clip(deck + rail + post, 0, 1)


def shade_bed(x, y):
    """The bridge's shadow on the bed: the deeper the bed, the further off it lands."""
    d = depth(x, y)
    ox, oy = offset_through_water(d, PPM, SUN_ELEV, SUN)
    # the surface point the sunlight came in through, with a little wander from the ripples
    wx = 3.0 * np.sin(y / 23 + x / 41) * (0.3 + d)
    return shade_surface(x - ox + wx, y - oy + wx * 0.6)


water = Water(absorb=(1.7, 0.42, 0.62), body=mix((turq, 2), (phthalo, 2), (ultra, 0.5), (white, 0.3)))

# coarse look at the reach, to size each pass
gy, gx = np.mgrid[0:H:12, 0:W:12].astype(np.float64)
DG = depth(gx, gy)


def frac(m):
    return float(np.mean(m))


# =================================================================================================
# 1. The river turned off: the bed in its own colour, scrubbed in.
# =================================================================================================
silt = mix((umber, 2), (white, 2), (ochre, 0.6), (payne, 0.4))
scrub = Brush(width=70, bristle=2.4, opacity=0.9, dryness=0.0, pickup=0.15, jitter=0.07, deplete=0.0012)


def silt_col(m):
    x, y = m
    d = float(depth(x, y))
    k = 1.0 - 0.35 * smoothstep(0.2, 1.4, d)
    return scale(mix((silt, 3), (white, 1.0 * (1 - smoothstep(0.1, 0.6, d)))), k * rng.uniform(0.85, 1.12))


whole = [(-60, -60), (W + 60, -60), (W + 60, H + 60), (-60, H + 60)]
board.fill(whole, scrub, silt, angle=np.radians(rng.uniform(70, 110)), color_fn=silt_col)
board.fill(whole, scrub.but(width=50, opacity=0.6), silt, angle=np.radians(20), color_fn=silt_col)
board.stage("the river turned off: the bed scrubbed in")

# =================================================================================================
# 2. Stones. Biggest first. Limestone mostly, some grey, a few rust and black.
# =================================================================================================
A_LIME = mix((white, 6), (ochre, 0.5), (umber, 0.35))
A_GREY = mix((white, 3), (payne, 1), (umber, 0.3))
A_RUST = mix((white, 2), (sienna, 1), (ochre, 0.8))
A_DARK = mix((payne, 2), (umber, 1), (white, 0.8))
A_BLUE = mix((white, 4), (ultra, 0.5), (payne, 0.8))
KINDS = [(A_LIME, 0.62), (A_GREY, 0.18), (A_BLUE, 0.11), (A_RUST, 0.06), (A_DARK, 0.03)]
SILT = mix((umber, 2), (phthalo, 0.3), (white, 1.2))


def patchy(x, y):
    """Where the river sorted its stones: slow patches of one kind or another."""
    return 0.5 + 0.5 * np.sin(x / 210 + 1.3 * np.sin(y / 260)) * np.cos(y / 170 - x / 400)


def r_fn(x, y, g):
    d = float(depth(x, y))
    if d < 0.5:
        return float(np.clip(g.lognormal(np.log(12 + 10 * d / 0.5), 0.42), 4, 46))
    return float(np.clip(g.lognormal(np.log(38), 0.5), 12, 110))


stones = pack_stones(rng, W, H, r_fn, 26000, overlap=0.72,
                     where=lambda x, y: depth(x, y) < 0.5 or rng.random() < 0.5)
order = sorted(stones, key=lambda s: s[2], reverse=True)
probs = np.array([p for _, p in KINDS]); probs /= probs.sum()
pb = Brush(width=20, bristle=1.2, opacity=0.95, pickup=0.08, jitter=0.05, gap=0.02, deplete=0.001,
           thickness=0.7, wander=0.4)
cast = mix((payne, 1), (umber, 0.5), (white, 1.4))
for (x, y, r) in order:
    pz = patchy(x, y)
    p = probs * np.array([1.0, 0.6 + 0.8 * pz, 0.6 + 0.8 * pz, 0.3 + 1.6 * pz ** 3, 0.5 + pz])
    A = KINDS[rng.choice(len(KINDS), p=p / p.sum())][0]
    A = scale(A, rng.uniform(0.85, 1.08))
    d = float(depth(x, y))
    film = smoothstep(0.5, 1.5, d)     # deeper stones carry a skin of silt and algae
    A = mix((A, 1 - 0.75 * film), (SILT, 0.75 * film + 1e-3))
    lit = A
    dark = scale(mix((A, 2), (SKY, 1)), 0.5 + 0.25 * film)
    stone(board, x, y, r, rng.uniform(0, np.pi), rng.uniform(1.0, 1.55), lit, dark, SUN,
          pb.but(bristle=max(1.0, r / 14)), shadow=mix((cast, 1 - 0.7 * film), (white, 0.7 * film + 1e-3)), shadow_len=0.45)
board.stage("stones, biggest first")

# =================================================================================================
# 3. Sun on the bed: the net of light, the leaf's shadow, the bridge's shadow.
# =================================================================================================
board.dry()
LEAF = (790.0, 735.0)
LEAF_LEN, LEAF_WID, LEAF_ANG = 136.0, 76.0, np.radians(112)
d_leaf = float(depth(*LEAF))
lox, loy = offset_through_water(d_leaf, PPM, SUN_ELEV, SUN)
LSH = (LEAF[0] + lox, LEAF[1] + loy)
sh = leaf_outline(*LSH, LEAF_LEN * 1.02, LEAF_WID * 1.04, LEAF_ANG, rng)
rim = leaf_outline(*LSH, LEAF_LEN * 1.25, LEAF_WID * 1.4, LEAF_ANG, rng)
LEAF_SH = poly_mask(W, H, sh)

tape_where(board, lambda X, Y: shade_bed(X, Y) * (1.0 - LEAF_SH), feather=1.0)
netb = Brush(width=4, bristle=1.0, opacity=0.6, pickup=0.0, jitter=0.03, gap=0.05, taper=(0.2, 0.2),
             thickness=0.0, dryness=0.12)
hot = mix((white, 6), (cadyel, 1.3), (ochre, 0.5))      # warm: the water will cool it on the way back up
segs = sun_net(rng, -40, -40, W + 40, H + 40, cell=74, stretch=1.5, angle=np.arctan2(-0.21, 1.0) + np.pi / 2)


def riffle(x, y):
    """How broken the surface is above a spot: the net is sharp under the riffle, faint under glides."""
    wave = 0.5 + 0.5 * np.sin(x / 150 - y / 330 + 2.0) * np.sin(y / 190 + 0.4)
    lip = np.exp(-((x - edge(y) + 140) / 300) ** 2)          # the water quickens as it goes over the lip
    return 0.3 + 0.7 * np.clip(0.55 * wave + 0.6 * lip, 0, 1)


def junction_heavy(t):
    return 0.4 + 0.85 * np.abs(2 * t - 1) ** 1.5


for a, b in segs:
    m = (a + b) / 2
    d = float(depth(*m))
    if d > 1.5:
        continue
    focus = np.exp(-d / 0.7) * riffle(*m)      # deeper, the net goes out of focus and dims
    if rng.random() > 0.2 + 0.7 * focus:
        continue
    nrm = np.array([-(b - a)[1], (b - a)[0]]) / (np.hypot(*(b - a)) + 1e-9)
    bend = rng.normal(0, 8.0)
    mid = [a + (b - a) * 0.33 + nrm * bend, a + (b - a) * 0.66 + nrm * (bend * 0.4 + rng.normal(0, 4))]
    w = 3.0 + 5.0 * (1 - focus) + rng.uniform(0.0, 3.0) * focus
    path = [a, *mid, b]
    # a wide faint glow, then the line itself in one soft round hair
    board.stroke(path, netb.but(width=w * 3.2, bristle=w * 0.9, opacity=0.10 + 0.12 * focus, gap=0.0),
                 scale(hot, 0.95), pressure=junction_heavy)
    board.stroke(path, netb.but(width=w, bristle=max(1.2, w * 0.45), opacity=0.35 + 0.6 * focus, gap=0.0, jitter=0.01),
                 scale(hot, 1.0 + 0.2 * focus), pressure=junction_heavy)
board.untape()
board.stage("the sun's net on the gravel")

# the leaf's shadow: dark where the leaf is, a bright rim where its dimple in the surface focuses the sun
board.tape(rim)
for i in range(2):
    board.stroke(np.vstack([rim, rim[:2]]), netb.but(width=9 - 3 * i, opacity=0.22), scale(hot, 1.05), smooth=True)
board.untape()
board.tape(sh, feather=0.7)
board.fill(sh, Brush(width=22, bristle=3.0, glaze=True, opacity=0.6, taper=(0.02, 0.02), jitter=0.01, gap=0.0),
           mix((SKY, 2), (payne, 0.9)), angle=LEAF_ANG, spacing=9)
board.untape()

# the bridge's shadow: a glaze of skylight-blue grey over everything it covers
tape_where(board, lambda X, Y: 1.0 - shade_bed(X, Y), feather=1.0)
shb = Brush(width=90, bristle=7.0, glaze=True, opacity=0.5, jitter=0.01, gap=0.0, pickup=0.0, taper=(0.02, 0.02), wander=0.3)
for da in (-0.12, 0.1):
    board.fill(whole, shb, mix((SKY, 2), (payne, 0.9)), angle=np.arctan2(SUN[1], SUN[0]) + da, spacing=34)
board.untape()
board.stage("shadows: the leaf's, and the bridge's")

# =================================================================================================
# 4. The river goes back in. One glaze per depth, with the current.
# =================================================================================================
board.dry()
levels = [0.0, 0.3, 0.45, 0.6, 0.75, 0.9, 1.05, 1.2, 1.35, 1.5, 1.65, 1.8]
gbrush = Brush(width=54, bristle=3.4, opacity=0.8, glaze=True, jitter=0.02, gap=0.0, taper=(0.18, 0.22),
               pickup=0.0, wander=2.0)
GL = 210.0


def glaze_col(i, d, x, y):
    T = water.through(0.14) ** 0.5 if i == 0 else water.through(0.17) ** 0.4
    return np.clip(T * rng.uniform(0.97, 1.03), 0.004, 1.0)


def glaze_brush(i, d):
    # the first glaze goes everywhere, wide and even; the rest are the river's own strokes
    return gbrush.but(width=110, bristle=3.2, opacity=0.6, gap=0.0, jitter=0.02) if i == 0 else gbrush


def per_level(i, d):
    a = frac(DG >= d) * W * H
    return int(a * (2.6 if i == 0 else 2.4) / (GL * glaze_brush(i, d).width)) + 4


glaze_by_depth(board, vel, lambda x, y: float(depth(x, y)), levels, gbrush, glaze_col, per_level, GL, W, H,
               brush_for=glaze_brush)
board.stage("the river back in, a glaze for each depth")

# =================================================================================================
# 5. The water's own colour, where it is deep enough to have one. Weak in the bridge's shadow.
# =================================================================================================
board.dry()
veilb = Brush(width=44, bristle=2.2, opacity=0.2, pickup=0.0, jitter=0.05, gap=0.05, taper=(0.25, 0.3),
              thickness=0.1, wander=1.0)


def veil_col(x, y):
    d = float(depth(x, y))
    s = float(shade_bed(x, y))
    near_lip = float(np.exp(-max(0.0, d - 0.5) / 0.35))   # light bouncing up off the white slope
    c = mix((water.body, 3), (turq, 1.5 * near_lip), (white, 0.6 * near_lip))
    return scale(c, (0.35 + 0.65 * s) * rng.uniform(0.85, 1.15) * (1.0 - 0.55 * smoothstep(1.1, 1.85, d)))


def veil_op(x, y):
    d = float(depth(x, y))
    s = float(shade_bed(x, y))
    return (0.02 + 0.12 * water.veil(d - 0.25)) * s ** 2


seeds = scatter(rng, W, H, int(frac(DG > 0.3) * W * H * 2.2 / (180 * 44)), where=lambda x, y: depth(x, y) > 0.3)
with_the_current(board, vel, seeds, veilb, veil_col, 180, opacity_fn=veil_op,
                 stop=lambda x, y: depth(x, y) < 0.22)
board.stage("the water's own colour")

# =================================================================================================
# 6. The surface: sky caught on the ripples, the seam, foam.
# =================================================================================================
board.dry()
skyhi = mix((white, 5), (ultra, 0.6), (payne, 0.3))
# foam coming off the lip, in little rafts
foam = Brush(width=5, bristle=1.0, opacity=0.9, pickup=0.0, jitter=0.02, gap=0.0, taper=(0.3, 0.3), thickness=2.0)
for i in range(16):
    y0 = rng.uniform(60, H - RAIL_U - 80)
    x0 = edge(y0) + rng.normal(40, 30)
    line = streamline(vel, x0, y0, rng.uniform(80, 260), step=5)
    k = 0
    while k < len(line):
        p = line[k]
        for _ in range(int(rng.integers(1, 6))):
            q = p + rng.normal(0, 3.5, 2)
            board.dab(q[0], q[1], foam.but(width=rng.uniform(1.8, 4.5)), scale(white, rng.uniform(0.7, 1.0)),
                      length=rng.uniform(1.5, 4))
        k += int(rng.integers(4, 14))
board.stage("the surface")

# =================================================================================================
# 7. The leaf, last, thick, in one go.
# =================================================================================================
lo = leaf_outline(*LEAF, LEAF_LEN, LEAF_WID, LEAF_ANG, rng)
board.tape(lo, feather=0.8)
ca, sa = np.cos(LEAF_ANG), np.sin(LEAF_ANG)
tip = np.array(LEAF) + np.array([ca, sa]) * LEAF_LEN / 2
base = np.array(LEAF) - np.array([ca, sa]) * LEAF_LEN / 2
nrm = np.array([-sa, ca])
lb = Brush(width=13, bristle=1.1, opacity=0.97, pickup=0.35, jitter=0.05, gap=0.0, taper=(0.1, 0.2), thickness=2.4)
leafy = mix((cadyel, 3), (cadorange, 1), (white, 0.3))
C = np.array(LEAF)


def leaf_col(m):
    # across the blade: warm at the rim, the sun's side paler, a rusty bruise near the tip
    off = float((m - C) @ nrm) / (LEAF_WID / 2)
    along = float((m - C) @ np.array([ca, sa])) / (LEAF_LEN / 2)
    c = mix((leafy, 3), (cadorange, 1.6 * abs(off) ** 1.5), (sienna, 1.2 * max(0.0, along - 0.4) * (rng.random() < 0.6)))
    if off * (nrm @ SUN) > 0:
        c = mix((c, 3), (white, 0.5 * abs(off)))
    return scale(c, rng.uniform(0.94, 1.04))


board.fill(lo, lb, leafy, angle=LEAF_ANG, spacing=5.5, color_fn=leaf_col, wobble=0.4)
board.fill(lo, lb.but(opacity=0.35, pickup=0.9, width=18, jitter=0.01), leafy, angle=LEAF_ANG + 0.25, spacing=9,
           color_fn=leaf_col)                                  # worked together wet, so it reads as one skin
vein = lb.but(width=1.7, opacity=0.5, thickness=1.0, taper=(0.1, 0.6), pickup=0.0)
for k in range(10):                                          # beech veins run straight and parallel
    t = (k + 0.8) / 11.0
    p0 = base + (tip - base) * t
    for side in (-1, 1):
        dirv = (tip - base) / LEAF_LEN * 0.75 + nrm * side
        dirv /= np.linalg.norm(dirv)
        reach = LEAF_WID * 0.5 * np.sin(np.pi * min(1.0, t * 1.04)) ** 0.8
        board.stroke([p0, p0 + dirv * reach], vein, mix((leafy, 2), (sienna, 0.9)), smooth=False)
board.stroke([base, tip], lb.but(width=3.0, opacity=0.85, taper=(0.0, 0.5)), mix((cadyel, 2), (white, 2)))
board.untape()
board.stroke([base, base - np.array([ca, sa]) * 22 + nrm * 4], lb.but(width=3.5, taper=(0.0, 0.5)), mix((sienna, 2), (umber, 1)))
# the meniscus catching sky on the side away from the sun
board.stroke(np.vstack([lo[25:60], lo[60:62]]), Brush(width=3, bristle=1.0, opacity=0.6, taper=(0.3, 0.3)), skyhi)

finish(board, HERE, title="Soča at Kobarid, 9 June 1983, 58 cm", artist="zala-hrovat", year=1983,
       medium="Oil on gessoed birch ply", made="2026-11-09")
