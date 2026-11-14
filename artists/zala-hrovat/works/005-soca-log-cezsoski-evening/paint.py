"""Zala Hrovat - Soča at Log Čezsoški, 2 September 1984, 36 cm

The evening reading, the same day as the boulder. The sun has been behind the hill for an hour and
there is high cloud with the light still on it. From the rail the river is not there any more: it
is the sky, lying flat, with the cloud bent a little by the swell. Except where the bridge stands
in it. The bridge's reflection is dark, and a dark reflection is a window: inside it the water is
clear to the bottom, and the rock is where it was this morning. On the edge of the bridge is my
own head and shoulders, small, and inside that the stone too.
"""
import sys
from pathlib import Path

import numpy as np
from scipy.ndimage import gaussian_filter, map_coordinates

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[3]))
sys.path.insert(0, str(HERE.parents[1]))

from engine import Board, Brush, ground, hexc, mix, paths, scale  # noqa: E402
from engine.studio import finish  # noqa: E402
from tools import (Skin, SmallTape, colors_along, current_grain, faceted_stone, film_glaze, mirror,  # noqa: E402
                   pack_stones, rock_outline, scatter, smoothstep, streamline, veil)

W, H = 1350, 1800
PPM = 540.0
rng0 = np.random.default_rng(1902)
board = Board(W, H, hexc("#f4f1e8"), ground.smooth_panel(W, H, rng0), seed=1902, light=(0.55, 0.4))
board.dries_off_board = False
board.relief_soft = 1.6
rng = board.rng

# --- tubes ---------------------------------------------------------------------------------------
white, ochre, umber, sienna = hexc("#f5f2ea"), hexc("#c49a45"), hexc("#6b5a44"), hexc("#8a4a26")
payne, phthalo, turq, ultra = hexc("#2e3640"), hexc("#0b5a4a"), hexc("#1f9a9a"), hexc("#23338c")
whole = [(-60, -60), (W + 60, -60), (W + 60, H + 60), (-60, H + 60)]

# No sun. The light is the sky, and most of the sky is up the valley, away from the bridge.
L3 = np.array([0.0, -0.38, 1.0]); L3 /= np.linalg.norm(L3)
DUSK = np.array([0.42, 0.49, 0.58])        # what this light makes of a white card. A confession.


def eve(c, k=1.0):
    return np.clip(np.asarray(c) * DUSK * k, 0.004, 1.0)


# --- where I am ----------------------------------------------------------------------------------
EYE = np.array([1005.0, 840.0])            # the point on the water straight under my eyes
EYE_H = 4.45                               # metres: deck 3.0, rail 1.1, and me on my elbows
DECK_H, RAIL_H = 3.0, 4.1
RAIL_Y = 0.28                              # the rail is this far back from my eyes, toward the bridge

# --- the reach: the rock of this morning ---------------------------------------------------------
BX, BY = 540.0, 930.0
B_OUT, B_REACH = rock_outline(BX, BY, 330, 440, np.radians(-8), np.random.default_rng(31), facets=8, round_=0.6)
TOP = 0.21


def bed_depth(x, y):
    x = np.asarray(x, dtype=np.float64)
    y = np.asarray(y, dtype=np.float64)
    d = 1.0 + 0.3 * smoothstep(0, 1800, y) + 0.25 * smoothstep(450, 1250, x) + 0.45 * smoothstep(1150, 1800, y)
    d = d + 0.04 * np.sin(x / 130 + y / 190) + 0.03 * np.sin(y / 77 - x / 105)
    r = B_REACH(x, y)
    d = d + 0.06 * np.exp(-((r - 1.12) / 0.22) ** 2) * (0.5 + 0.5 * smoothstep(1300, 400, y))
    return d


def rock_height(x, y):
    """0 off the rock, 1 on its back. This morning I had it a table with straight sides. It is not:
    the head, where the river hits it, is steep, and the tail goes down toward the bridge in the
    ledges the limestone splits along."""
    x = np.asarray(x, dtype=np.float64)
    y = np.asarray(y, dtype=np.float64)
    r = B_REACH(x, y)
    down = (y - BY) / (np.hypot((x - BX) * 1.33, y - BY) + 1e-6)       # -1 at the head, 1 at the tail
    side = (x - BX) / (np.hypot(x - BX, (y - BY) * 0.75) + 1e-6)
    pe = 0.80 - 0.42 * smoothstep(-0.1, 0.9, down) - 0.12 * smoothstep(0.2, 1.0, side)
    u = np.clip((r - pe) / (1.0 - pe), 0.0, 1.0)
    g = 1.0 - u ** 1.15
    wob = 0.10 * np.sin(x / 97.0 + 1.3 * np.sin(y / 140.0)) + 0.05 * np.sin(x / 41.0 - y / 67.0)
    q = (g + wob) * 2.2 + 0.35
    step = np.clip((np.floor(q) + smoothstep(0.72, 1.0, q - np.floor(q)) - 0.35) / 2.2, 0, 1)
    led = smoothstep(-0.2, 0.6, down)
    f = np.clip((1 - 0.85 * led) * g + 0.85 * led * step, 0.0, 1.0)
    f = np.where(r < pe, 1.0, f) * (1 - smoothstep(0.96, 1.0, r))
    lump = 1 - 0.05 * (0.5 + 0.5 * np.sin(x / 47 + np.sin(y / 61) * 2) * np.sin(y / 53 - x / 90))
    return f * lump


def depth(x, y):
    bd = bed_depth(x, y)
    return bd - (bd - TOP) * rock_height(x, y)


def vel(x, y):
    dx, dy = x - BX, y - BY
    r = np.hypot(dx / 330, dy / 440) + 1e-6
    vx = -0.06 + 0.05 * np.sin(y / 140 + x / 210)
    k = 0.8 * np.exp(-((r - 1.0) / 0.45) ** 2) * smoothstep(250, -150, dy)
    vx = vx + k * np.sign(dx) * np.minimum(1.0, abs(dx) / 120)
    k2 = 0.5 * np.exp(-((r - 1.0) / 0.6) ** 2) * smoothstep(-100, 300, dy)
    vx = vx - k2 * np.sign(dx) * np.minimum(1.0, abs(dx) / 160)
    return vx, 1.0 + 0.2 * smoothstep(300, 1500, y)


XX, YY = np.meshgrid(np.arange(W) + 0.5, np.arange(H) + 0.5)
RH = gaussian_filter(rock_height(XX, YY), 1.6)
BED = bed_depth(XX, YY)
DEP = BED - (BED - TOP) * RH


def at(F, x, y):
    return F[int(np.clip(y, 0, H - 1)), int(np.clip(x, 0, W - 1))]


# --- the surface: evening, glassy, a long slow swell and the cushion on the rock's head -----------
SWELL = [(rng0.uniform(380, 800), rng0.normal(np.pi / 2, 0.8), rng0.uniform(0, 6.3)) for _ in range(6)]
RIPPLE = [(rng0.uniform(210, 330), rng0.normal(np.pi / 2, 0.6), rng0.uniform(0, 6.3)) for _ in range(5)]
S_SWELL, S_RIPPLE = 0.0068, 0.0018         # the slope each one is allowed


def height(X, Y):
    h = np.zeros_like(X)
    for lam, a, ph in SWELL:
        kx, ky = np.cos(a) * 2 * np.pi / lam, np.sin(a) * 2 * np.pi / lam
        h += S_SWELL * lam / (2 * np.pi * PPM) * np.sin(kx * X + ky * Y + ph + 0.7 * np.sin(X / 330 + Y / 500))
    for lam, a, ph in RIPPLE:
        kx, ky = np.cos(a) * 2 * np.pi / lam, np.sin(a) * 2 * np.pi / lam
        h += S_RIPPLE * lam / (2 * np.pi * PPM) * np.sin(kx * X + ky * Y + ph + 0.6 * np.sin(X / 140))
    h += 0.012 * np.exp(-(((X - BX + 10) / 300) ** 2 + ((Y - BY + 330) / 150) ** 2))
    h += 0.005 * np.exp(-(((X - BX) / 280) ** 2 + ((Y - BY + 40) / 360) ** 2))
    return h


skin = Skin(height, W, H, PPM)


def seen_bed(pts):
    return skin.seen(pts, depth)


# =================================================================================================
# 1. The river turned off, in the light there is. Nothing throws a shadow; a stone is lighter on top
#    and darker where it leans away from the open sky, and the bed under the bridge end gets less.
# =================================================================================================
UNDER = 1.0 - 0.30 * smoothstep(1050, 1900, YY)             # the bridge takes some of the sky
silt = mix((umber, 2), (white, 1.0), (ochre, 0.5), (payne, 1.1))
scrub = Brush(width=70, bristle=3.0, opacity=0.9, pickup=0.0, jitter=0.05, deplete=0.0001, thickness=0.0, loadvar=0.08)


def silt_col(m):
    d = float(bed_depth(*m))
    return eve(silt, (1.15 - 0.2 * smoothstep(0.8, 1.4, d)) * at(UNDER, *m) * rng.uniform(0.9, 1.06))


for a in (rng.uniform(-20, 20), rng.uniform(50, 80), rng.uniform(110, 140)):
    board.fill(whole, scrub, eve(silt), angle=np.radians(a), color_fn=silt_col, wobble=2.0)

A_LIME = mix((white, 6), (ochre, 0.45), (umber, 0.3))
A_GREY = mix((white, 3), (payne, 1), (umber, 0.3))
A_BLUE = mix((white, 4), (payne, 1.3))
A_PINK = mix((white, 4), (sienna, 0.6), (ochre, 0.3))
A_DARK = mix((payne, 2), (umber, 1), (white, 0.9))
KINDS = [A_LIME, A_GREY, A_BLUE, A_PINK, A_DARK]
probs = np.array([0.6, 0.18, 0.08, 0.1, 0.04])
FILM = mix((umber, 2), (phthalo, 0.5), (ochre, 0.7), (white, 0.8))


def r_fn(x, y, g):
    med = 17 + 14 * smoothstep(0.8, 1.3, float(bed_depth(x, y)))
    return float(np.clip(g.lognormal(np.log(med), 0.66), 5, 90))


cobbles = pack_stones(rng, W, H, r_fn, 30000, overlap=0.86, where=lambda x, y: B_REACH(x, y) > 0.99)
facet = Brush(width=20, bristle=2.0, opacity=0.95, pickup=0.2, jitter=0.03, gap=0.0, thickness=0.2, wander=0.6,
              taper=(0.0, 0.0), loadvar=0.08)
stape = SmallTape(board)
for (x, y, r) in cobbles:
    A = scale(KINDS[rng.choice(5, p=probs)], rng.uniform(0.86, 1.05))
    film = smoothstep(0.7, 1.2, float(bed_depth(x, y)))
    A = mix((A, 1 - 0.45 * film), (FILM, 0.45 * film + 1e-3))
    out, _ = rock_outline(x, y, r, r * rng.uniform(0.6, 0.95), rng.uniform(0, np.pi), rng,
                          facets=int(rng.integers(5, 9)), n=28, round_=rng.uniform(0.5, 0.85))
    faceted_stone(board, stape, out, (x, y), r, eve(A, 0.72 * at(UNDER, x, y)), L3, rng, facet, seen=seen_bed,
                  cuts=1 + int(rng.random() < 0.3), tilt=0.75, edge=0.9)
board.stage("the river turned off, in the light there is: no sun, so no shadows")

# =================================================================================================
# 2. The rock. Each stroke is mixed for how much of the sky that bit of it can see.
# =================================================================================================
board.dry()
board.tape(seen_bed(B_OUT), feather=1.2)
BOUL = mix((white, 6), (payne, 0.45), (ochre, 0.5), (umber, 0.25))
gyh, gxh = np.gradient(-gaussian_filter(DEP, 3.5) * PPM)


def boul_col(x, y):
    ix, iy = int(np.clip(x, 0, W - 1)), int(np.clip(y, 0, H - 1))
    n = np.array([-gxh[iy, ix], -gyh[iy, ix], 1.0])
    n /= np.linalg.norm(n)
    lam = max(0.0, float(n @ L3))
    rh = float(RH[iy, ix])
    open_ = 0.78 + 0.22 * rh                                   # low on the flank the bed shuts the sky out
    c = mix((BOUL, 3), (FILM, 0.9 * (1 - rh) ** 1.5 + 0.2))
    return eve(c, (0.42 + 0.80 * lam ** 1.3) * open_ * UNDER[iy, ix])


bb = Brush(width=15, bristle=1.5, opacity=0.95, pickup=0.35, dryness=0.08, jitter=0.04, gap=0.02, thickness=0.4, wander=0.5,
           taper=(0.1, 0.15))
BED_ANG = np.radians(-30)
for ang, wid, op in ((BED_ANG, 16, 0.95), (BED_ANG + 1.3, 13, 0.7), (BED_ANG + 0.15, 10, 0.6)):
    for a, b in paths.hatch(B_OUT * 1.04 - np.array([BX, BY]) * 0.04, ang, wid * 0.55, rng, jitter=0.3):
        L = np.hypot(*(b - a))
        k = max(1, int(L / rng.uniform(50, 100)))
        cuts = np.sort(np.concatenate([[0, 1], rng.uniform(0, 1, k - 1)]))
        for t0, t1 in zip(cuts[:-1], cuts[1:]):
            seg = a + np.outer(np.linspace(t0, t1, 8), b - a)
            board.stroke(seen_bed(seg), bb.but(width=wid * rng.uniform(0.8, 1.2), opacity=op),
                         colors_along(seg, boul_col, every=1), wobble=0.8)
# along the ledges, at one height, the way the stone splits
level_dir = lambda x, y: (-at(gyh, x, y), at(gxh, x, y))
for x, y in scatter(rng, W, H, 700, where=lambda x, y: 0.35 < B_REACH(x, y) < 1.0 and 0.03 < at(RH, x, y) < 0.9)[:320]:
    pts = streamline(level_dir, x, y, rng.uniform(40, 110), step=3.0)
    if len(pts) < 4:
        continue
    board.stroke(seen_bed(pts), bb.but(width=rng.uniform(5, 9), opacity=0.5, pickup=0.1), colors_along(pts, boul_col), wobble=0.3)
for _ in range(140):
    x, y = BX + rng.normal(0, 170), BY + rng.normal(0, 230)
    if B_REACH(x, y) > 0.85:
        continue
    board.dab(*seen_bed(np.array([[x, y]]))[0], bb.but(width=rng.uniform(2, 5), opacity=0.7), scale(boul_col(x, y), 0.6),
              length=rng.uniform(2, 6))
crack = np.array([[BX - 260, BY - 120], [BX - 120, BY - 60], [BX - 40, BY - 85], [BX + 60, BY + 10], [BX + 150, BY + 30],
                  [BX + 230, BY + 110]])
cp, _ = paths.resample(crack, 9.0)
cp = cp + rng.normal(0, 1.1, cp.shape)
cuts = np.sort(rng.choice(np.arange(6, len(cp) - 6), 3, replace=False))
for seg in np.split(cp, cuts):
    seg = seg[: max(3, len(seg) - int(rng.integers(0, 4)))]
    board.stroke(seen_bed(seg), Brush(width=6, bristle=1.2, opacity=0.7, pickup=0.0, taper=(0.3, 0.4)),
                 eve(mix((payne, 2), (umber, 1))), smooth=False)
board.untape()
board.stage("the rock: steep at the head, going down in ledges toward the bridge")

# =================================================================================================
# 3. The river back in, as films. One depth at a time, each only where the water is that deep, each
#    drawn with the current. No bristles: I lay it and badger it out, and the streaks are the grain.
# =================================================================================================
board.dry()
ABSORB = np.array([1.65, 0.38, 0.72])
GRAINS = [current_grain(vel, W, H, np.random.default_rng(50 + i), length=220, fine=f) for i, f in enumerate((1.0, 1.6, 2.6))]
levels = np.linspace(0.0, 2.0, 16)
for i, (lo, hi) in enumerate(zip(levels[:-1], levels[1:])):
    thick = np.clip(DEP - lo, 0.0, hi - lo)
    film_glaze(board, np.exp(-ABSORB[None, None, :] * thick[..., None]), grain=GRAINS[i % 3], streak=0.035)
    if i == 3:
        board.stage("the river back in: four films, the water over the rock's back")
BODY = eve(mix((turq, 3), (phthalo, 1.4), (ultra, 0.35), (white, 1.0)), 0.5)
veil(board, BODY, 0.30 * smoothstep(0.6, 2.0, DEP), grain=GRAINS[1], drag=0.08, tooth=0.0, thickness=0.0)
film_glaze(board, np.ones(3), level=1.0)                     # stand oil over all of it
board.stage("fifteen films, and stand oil: the river as it is under the bridge")

# =================================================================================================
# 4. The sky lying on the water. Worked out, not drawn: from my eye down to each bit of the surface,
#    off the facet it meets there, and back up. If that line meets the bridge or me, the water there
#    is a window. If it gets past, it is sky, and goes on as a scumble: pale paint dragged thin with
#    the current, which lightens what is under it without covering it.
# =================================================================================================
board.dry()
_, _, TX, TY = mirror(skin, EYE, EYE_H, 1.0)


def up(z):
    """Where each line of sight is, in metres from my eye, when it is z metres above the water."""
    return (XX - EYE[0]) / PPM + TX * z, (YY - EYE[1]) / PPM + TY * z


def capsule(qx, qy, a, b, r):
    a, b = np.asarray(a, dtype=np.float64), np.asarray(b, dtype=np.float64)
    ab = b - a
    t = np.clip(((qx - a[0]) * ab[0] + (qy - a[1]) * ab[1]) / (ab @ ab), 0, 1)
    return np.hypot(qx - a[0] - t * ab[0], qy - a[1] - t * ab[1]) < r


blocked = np.zeros((H, W), dtype=bool)
qx, qy = up(DECK_H)
blocked |= qy > RAIL_Y + 0.02                                          # the deck
qx, qy = up(RAIL_H)
blocked |= np.abs(qy - (RAIL_Y + 0.005)) < 0.04                        # the top rail
for z in np.linspace(DECK_H, RAIL_H, 9):                               # the posts that carry it
    qx, qy = up(z)
    px_ = (qx + 0.55) % 1.5
    blocked |= (np.minimum(px_, 1.5 - px_) < 0.035) & (np.abs(qy - (RAIL_Y + 0.005)) < 0.04)
    bx_ = (qx + 0.03) % 0.12                                           # the balusters between them
    blocked |= (np.minimum(bx_, 0.12 - bx_) < 0.011) & (np.abs(qy - (RAIL_Y + 0.005)) < 0.02)
    blocked |= (np.abs(qx) < 0.21) & (qy > RAIL_Y) & (qy < RAIL_Y + 0.4)                # and me, standing behind them
qx, qy = up(EYE_H + 0.02)
blocked |= np.hypot(qx / 0.112, (qy - 0.015) / 0.122) < 1.0            # my head, and my hair
qx, qy = up(EYE_H - 0.16)
blocked |= np.hypot(qx / 0.085, (qy - 0.08) / 0.09) < 1.0              # neck
qx, qy = up(EYE_H - 0.27)
blocked |= np.hypot(qx / 0.235, (qy - 0.18) / 0.125) < 1.0             # shoulders, leaning
qx, qy = up(RAIL_H + 0.08)
for sg in (-1, 1):
    blocked |= capsule(qx, qy, (sg * 0.19, 0.19), (sg * 0.36, RAIL_Y), 0.07)       # upper arms, out to the elbows
    blocked |= capsule(qx, qy, (sg * 0.36, RAIL_Y), (sg * 0.03, 0.13), 0.06)        # forearms, hands together
SKYTAPE = gaussian_filter(1.0 - blocked.astype(np.float64), 1.1)

# the sky itself: zenith going grey-blue, lighter up the valley where the sun went; cirrus in long
# streaks with the light still on it
T = 768
n1 = gaussian_filter(rng0.normal(0, 1, (T, T)), (4, 95)); n1 /= n1.std()
n2 = gaussian_filter(rng0.normal(0, 1, (T, T)), (28, 110)); n2 /= n2.std()
CIR = n1 + 0.9 * n2
ca, sa = np.cos(np.radians(24)), np.sin(np.radians(24))
u, v = TX * ca + TY * sa, -TX * sa + TY * ca
CLOUD = smoothstep(-0.4, 2.2, map_coordinates(CIR, [v * T / 1.7 + T / 2, u * T / 1.7 + T / 2], order=1, mode="reflect"))
GLOW = smoothstep(0.05, -0.5, TY)                                       # up the valley
SKYC = mix((white, 5), (payne, 1.25))
SKYLT = mix((white, 9), (payne, 0.7), (ochre, 0.25))
CLOUDC = mix((white, 9), (ochre, 0.6), (sienna, 0.7))
SG = [current_grain(vel, W, H, np.random.default_rng(80 + i), length=70, fine=f) for i, f in enumerate((2.2, 3.2))]

board.tape_where(SKYTAPE)
sky_field = SKYC[None, None, :] * (1 - GLOW[..., None]) + SKYLT[None, None, :] * GLOW[..., None]
veil(board, sky_field, 0.42 + 0.08 * GLOW, grain=SG[0], drag=0.035, tooth=0.15, thickness=0.05)
board.stage("the sky goes on, everywhere the bridge and I are not in its way")
veil(board, sky_field, 0.38 + 0.08 * GLOW, grain=SG[1], drag=0.035, tooth=0.15, thickness=0.05)
veil(board, CLOUDC, 0.38 * CLOUD, grain=SG[0], drag=0.05, tooth=0.25, thickness=0.12)
# ultramarine only ever as a glaze: a thin one over the sky between the clouds, once the scumble is dry
board.dry()
film_glaze(board, np.exp(np.log(ultra)[None, None, :] * (0.085 * (1 - 0.8 * CLOUD) * (1 - 0.5 * GLOW))[..., None]))
board.untape()
board.stage("the cloud with the light still on it, bent by the swell")

print(f"{len(cobbles)} cobbles; sky on {SKYTAPE.mean():.0%} of the panel")
finish(board, HERE, title="Soča at Log Čezsoški, 2 September 1984, 36 cm", artist="zala-hrovat", year=1984,
       medium="Oil on gessoed birch ply: body colour, glazes laid as films, a scumble for the sky",
       made="2026-11-14")
