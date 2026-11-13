"""Zala Hrovat - Soča at Log Čezsoški, 2 September 1984, 37 cm

The same bridge as 003, two weeks on and four centimetres lower, a little after nine. I went back
for the boulder. A grey limestone block a metre and a half long, its back twenty-two centimetres
under, and the water goes over it glassy: no chop, only a slow swell, and the swell is a lens that
lays bands of sun across the stone. The bed falls away round it into deeper water. A trout lies
over its right shoulder, eight centimetres down, and its shadow lies beside it on the stone.
"""
import sys
from pathlib import Path

import numpy as np
from scipy.ndimage import binary_closing, gaussian_filter

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[3]))
sys.path.insert(0, str(HERE.parents[1]))

from engine import Board, Brush, ground, hexc, mix, paths, scale  # noqa: E402
from engine.studio import finish  # noqa: E402
from tools import (Skin, cast_down, caustics, colors_along, glaze_through, pack_stones, SmallTape, faceted_stone,  # noqa: E402
                   poly_mask, rock_outline, scatter, smoothstep, streamline, trout_outline, under)

W, H = 1350, 1800
PPM = 540.0
rng0 = np.random.default_rng(902)
board = Board(W, H, hexc("#f4f1e8"), ground.smooth_panel(W, H, rng0), seed=902, light=(0.55, 0.4))
board.dries_off_board = False
board.relief_soft = 1.6
rng = board.rng

# --- tubes ---------------------------------------------------------------------------------------
white, ochre, umber, sienna = hexc("#f5f2ea"), hexc("#c49a45"), hexc("#6b5a44"), hexc("#8a4a26")
payne, phthalo, turq, ultra = hexc("#2e3640"), hexc("#0b5a4a"), hexc("#1f9a9a"), hexc("#23338c")
cadyel = hexc("#f2b01e")

SUN = np.array([0.82, 0.57]); SUN /= np.linalg.norm(SUN)      # toward the light, on the board
SUN_ELEV = 38.0                                                 # 46 N, early September, a little after nine
L3 = np.array([SUN[0] * np.cos(np.radians(SUN_ELEV)), SUN[1] * np.cos(np.radians(SUN_ELEV)),
               np.sin(np.radians(SUN_ELEV))])
SKY = mix((white, 3), (ultra, 1), (payne, 0.4))
whole = [(-60, -60), (W + 60, -60), (W + 60, H + 60), (-60, H + 60)]

# --- the reach -----------------------------------------------------------------------------------
BX, BY = 540.0, 930.0                      # the boulder: 1.2 m by 1.6 m, its back 14 cm under
B_OUT, B_REACH = rock_outline(BX, BY, 330, 440, np.radians(-8), np.random.default_rng(31), facets=8, round_=0.6)
TOP = 0.22
FISH = (790.0, 965.0)
FISH_LEN, FISH_D = 0.40 * PPM, 0.08
FISH_ANG = np.arctan2(-1.0, -0.12)         # nose into the current


def bed_depth(x, y):
    x = np.asarray(x, dtype=np.float64)
    y = np.asarray(y, dtype=np.float64)
    d = 1.0 + 0.3 * smoothstep(0, 1800, y) + 0.25 * smoothstep(450, 1250, x)
    d = d + 0.04 * np.sin(x / 130 + y / 190) + 0.03 * np.sin(y / 77 - x / 105)
    r = B_REACH(x, y)
    d = d + 0.06 * np.exp(-((r - 1.12) / 0.22) ** 2) * (0.5 + 0.5 * smoothstep(1300, 400, y))   # the scour
    return d


def rock_height(x, y):
    """0 off the rock, 1 on its flat back. Rounded at the shoulders, a little lumpy on top."""
    r = B_REACH(x, y)
    f = np.clip(1 - np.clip(r, 0, 1) ** 6.0, 0, 1) ** 0.4
    lump = 1 - 0.05 * (0.5 + 0.5 * np.sin(x / 47 + np.sin(y / 61) * 2) * np.sin(y / 53 - x / 90))
    return f * lump


def depth(x, y):
    bd = bed_depth(x, y)
    return bd - (bd - TOP) * rock_height(x, y)


def vel(x, y):
    dx, dy = x - BX, y - BY
    r = np.hypot(dx / 330, dy / 440) + 1e-6
    vx = -0.06 + 0.05 * np.sin(y / 140 + x / 210)
    k = 0.8 * np.exp(-((r - 1.0) / 0.45) ** 2) * smoothstep(250, -150, dy)      # parted at its head
    vx = vx + k * np.sign(dx) * np.minimum(1.0, abs(dx) / 120)
    k2 = 0.5 * np.exp(-((r - 1.0) / 0.6) ** 2) * smoothstep(-100, 300, dy)       # and closing behind
    vx = vx - k2 * np.sign(dx) * np.minimum(1.0, abs(dx) / 160)
    return vx, 1.0 + 0.2 * smoothstep(300, 1500, y)


XX, YY = np.meshgrid(np.arange(W) + 0.5, np.arange(H) + 0.5)
DEP = depth(XX, YY)
RH = rock_height(XX, YY)
ON_ROCK = smoothstep(0.02, 0.12, RH)


# --- the surface: glassy, a slow swell, a cushion on the rock's head, a riffle coming in at the top
SWELL = [(rng0.uniform(110, 240), rng0.normal(np.pi / 2, 0.9), rng0.uniform(0, 6.3)) for _ in range(7)]
LENS = [(rng0.uniform(75, 120), rng0.normal(np.pi / 2, 0.3), rng0.uniform(0, 6.3)) for _ in range(4)]
CHOP = [(rng0.uniform(30, 55), rng0.normal(np.pi / 2, 0.5), rng0.uniform(0, 6.3)) for _ in range(6)]


def height(X, Y):
    h = np.zeros_like(X)
    for lam, a, ph in SWELL:
        kx, ky = np.cos(a) * 2 * np.pi / lam, np.sin(a) * 2 * np.pi / lam
        h += 0.0019 * np.sin(kx * X + ky * Y + ph + 0.7 * np.sin(X / 230 + Y / 400))
    rough = (1 - smoothstep(60, 300, Y)) * (0.4 + 0.6 * smoothstep(300, 1100, X) + 0.4 * (1 - smoothstep(0, 300, X)))
    for lam, a, ph in CHOP:
        kx, ky = np.cos(a) * 2 * np.pi / lam, np.sin(a) * 2 * np.pi / lam
        h += 0.0019 * rough * np.sin(kx * X + ky * Y + ph + 0.5 * np.sin(X / 61))
    # the swell steepens as it runs up over the rock's back, and that is where it is a lens
    over = np.exp(-(((X - BX - 170) / 300) ** 2 + ((Y - BY) / 360) ** 2) * 1.5)
    for lam, a, ph in LENS:
        kx, ky = np.cos(a) * 2 * np.pi / lam, np.sin(a) * 2 * np.pi / lam
        h += 0.0024 * over * np.sin(kx * X + ky * Y + ph + 0.8 * np.sin(Y / 150))
    # the cushion: water heaped against the rock's head and slid over its back
    h += 0.022 * np.exp(-(((X - BX + 10) / 300) ** 2 + ((Y - BY + 330) / 150) ** 2))
    h += 0.010 * np.exp(-(((X - BX) / 280) ** 2 + ((Y - BY + 40) / 360) ** 2))
    return h


skin = Skin(height, W, H, PPM)


def seen_bed(pts):
    return skin.seen(pts, depth)


def seen_at(d):
    return lambda pts: skin.seen(pts, d)


# =================================================================================================
# 1. The river turned off: the bed round the rock. Cobbles that are not pills: each a few facets.
# =================================================================================================
silt = mix((umber, 2), (white, 1.0), (ochre, 0.5), (payne, 0.9))
scrub = Brush(width=70, bristle=3.0, opacity=0.9, pickup=0.3, jitter=0.05, deplete=0.0012, thickness=0.0, loadvar=0.08)


def silt_col(m):
    d = float(depth(*m))
    return scale(silt, (1.0 - 0.25 * smoothstep(0.8, 1.4, d)) * rng.uniform(0.9, 1.06))


for a in (rng.uniform(-20, 20), rng.uniform(50, 80), rng.uniform(110, 140)):
    board.fill(whole, scrub, silt, angle=np.radians(a), color_fn=silt_col, wobble=2.0)

A_LIME = mix((white, 6), (ochre, 0.45), (umber, 0.3))
A_GREY = mix((white, 3), (payne, 1), (umber, 0.3))
A_BLUE = mix((white, 4), (ultra, 0.45), (payne, 0.8))
A_PINK = mix((white, 4), (sienna, 0.6), (ochre, 0.3))
A_DARK = mix((payne, 2), (umber, 1), (white, 0.9))
KINDS = [A_LIME, A_GREY, A_BLUE, A_PINK, A_DARK]
probs = np.array([0.6, 0.18, 0.08, 0.1, 0.04])
FILM = mix((umber, 2), (phthalo, 0.5), (ochre, 0.7), (white, 0.8))
cast = mix((payne, 1.2), (umber, 0.6), (white, 0.6))

# stones: sizes sorted by where the current drops them, biggest in the scour
def r_fn(x, y, g):
    med = 22 + 16 * smoothstep(0.8, 1.3, float(bed_depth(x, y)))
    return float(np.clip(g.lognormal(np.log(med), 0.5), 5, 80))


cobbles = pack_stones(rng, W, H, r_fn, 30000, overlap=0.86, where=lambda x, y: B_REACH(x, y) > 0.97)
facet = Brush(width=20, bristle=2.0, opacity=0.95, pickup=0.2, jitter=0.03, gap=0.0, thickness=0.2, wander=0.6,
              taper=(0.0, 0.0), loadvar=0.08)
stape = SmallTape(board)
for (x, y, r) in cobbles:
    A = scale(KINDS[rng.choice(5, p=probs)], rng.uniform(0.86, 1.05))
    film = smoothstep(0.7, 1.2, float(bed_depth(x, y)))
    A = mix((A, 1 - 0.65 * film), (FILM, 0.65 * film + 1e-3))
    out, _ = rock_outline(x, y, r, r * rng.uniform(0.6, 0.95), rng.uniform(0, np.pi), rng,
                          facets=int(rng.integers(5, 9)), n=28, round_=rng.uniform(0.5, 0.85))
    faceted_stone(board, stape, out, (x, y), r, A, L3, rng, facet, seen=seen_bed, cuts=1 + int(rng.random() < 0.3),
                  shadow=cast, sun=SUN, tilt=0.6, edge=0.9)
board.stage("the river turned off: the bed round the rock, falling into the scour")

# =================================================================================================
# 2. The boulder in body colour. Strokes go round it at one height, and each is mixed for which way
#    that bit of it faces the sun: clean grey on the scoured back, a brown film down its flanks.
# =================================================================================================
board.tape(seen_bed(B_OUT), feather=1.2)
BOUL = mix((white, 4), (payne, 0.6), (ochre, 0.5), (umber, 0.35))
gyh, gxh = np.gradient(-DEP * PPM)                         # rise of the rock per px


def boul_col(x, y):
    ix, iy = int(np.clip(x, 0, W - 1)), int(np.clip(y, 0, H - 1))
    n = np.array([-gxh[iy, ix], -gyh[iy, ix], 1.0])
    n /= np.linalg.norm(n)
    lam = max(0.0, float(n @ L3))
    rh = float(RH[iy, ix])
    c = mix((BOUL, 3), (FILM, 2.4 * (1 - rh) ** 1.5 + 0.25), (SKY, 0.6 * (1 - lam)))
    return scale(c, 0.38 + 0.75 * lam ** 1.2)


bb = Brush(width=15, bristle=1.5, opacity=0.95, pickup=0.35, dryness=0.08, jitter=0.04, gap=0.02, thickness=0.4, wander=0.5,
           taper=(0.1, 0.15))
# laid in along its bedding, the way the limestone splits, then across it; short strokes, each
# mixed along its length for the light on that bit of the form
BED_ANG = np.radians(-30)
for ang, wid, op in ((BED_ANG, 16, 0.95), (BED_ANG + 1.3, 13, 0.7), (BED_ANG + 0.15, 10, 0.6)):
    for a, b in paths.hatch(B_OUT * 1.04 - np.array([BX, BY]) * 0.04, ang, wid * 0.55, rng, jitter=0.3):
        L = np.hypot(*(b - a))
        k = max(1, int(L / rng.uniform(70, 140)))
        cuts = np.sort(np.concatenate([[0, 1], rng.uniform(0, 1, k - 1)]))
        for t0, t1 in zip(cuts[:-1], cuts[1:]):
            seg = a + np.outer(np.linspace(t0, t1, 6), b - a)
            board.stroke(seen_bed(seg), bb.but(width=wid * rng.uniform(0.8, 1.2), opacity=op),
                         colors_along(seg, boul_col, every=1), wobble=0.8)
# the brown film of diatoms, in patches, heavier low on the flanks where the light is less
MOT = gaussian_filter(rng0.normal(0, 1, (H // 8, W // 8)), 3.0)
MOT = np.kron(MOT / MOT.std(), np.ones((8, 8)))[:H, :W]
filmb = Brush(width=70, bristle=8.0, opacity=0.35, glaze=True, pickup=0.0, jitter=0.03, gap=0.0, loadvar=0.1,
              taper=(0.3, 0.3))
FILMG = mix((umber, 1.2), (ochre, 1.0), (phthalo, 0.3), (white, 1.4))
for x, y in scatter(rng, W, H, 260, where=lambda x, y: B_REACH(x, y) < 1.0):
    ix, iy = int(np.clip(x, 0, W - 1)), int(np.clip(y, 0, H - 1))
    w = float(smoothstep(-0.3, 1.2, MOT[iy, ix])) * (0.5 + 0.8 * (1 - RH[iy, ix]))
    if rng.random() > w:
        continue
    board.dab(*seen_bed(np.array([[x, y]]))[0], filmb.but(opacity=0.03 + 0.07 * min(w, 1)), FILMG,
              angle=BED_ANG + rng.normal(0, 0.4), length=rng.uniform(60, 140))
# down the fall line on the flanks, the way the water has worn it
fall = lambda x, y: (gxh[int(np.clip(y, 0, H - 1)), int(np.clip(x, 0, W - 1))],
                     gyh[int(np.clip(y, 0, H - 1)), int(np.clip(x, 0, W - 1))])
for x, y in scatter(rng, W, H, 500, where=lambda x, y: 0.6 < B_REACH(x, y) < 1.0):
    pts = streamline(fall, x, y, rng.uniform(30, 70), step=3.0)
    if len(pts) < 4:
        continue
    board.stroke(seen_bed(pts), bb.but(width=rng.uniform(5, 9), opacity=0.6), colors_along(pts, boul_col), wobble=0.3)
# pits and a crack: the marks of a limestone that has been in a river ten thousand years
for _ in range(140):
    x, y = BX + rng.normal(0, 170), BY + rng.normal(0, 230)
    if B_REACH(x, y) > 0.85:
        continue
    c = scale(boul_col(x, y), 0.6)
    board.dab(*seen_bed(np.array([[x, y]]))[0], bb.but(width=rng.uniform(2, 5), opacity=0.7), c, length=rng.uniform(2, 6))
# a crack, the long way across its back: jagged, and lost in places where it closes up
crack = np.array([[BX - 260, BY - 120], [BX - 120, BY - 60], [BX - 40, BY - 85], [BX + 60, BY + 10], [BX + 150, BY + 30],
                  [BX + 230, BY + 110]])
cp, _ = paths.resample(crack, 9.0)
cp = cp + rng.normal(0, 1.1, cp.shape)
cuts = np.sort(rng.choice(np.arange(6, len(cp) - 6), 3, replace=False))
for seg in np.split(cp, cuts):
    seg = seg[: max(3, len(seg) - int(rng.integers(0, 4)))]
    board.stroke(seen_bed(seg), Brush(width=6, bristle=1.2, opacity=0.7, pickup=0.0, taper=(0.3, 0.4)),
                 mix((payne, 2), (umber, 1)), smooth=False)
    board.stroke(seen_bed(seg + SUN * 5), Brush(width=3, bristle=1.0, opacity=0.25, pickup=0.0, taper=(0.3, 0.4)),
                 scale(BOUL, 1.15), smooth=False)
# the bedding: the faint lines along which the block will one day split
dvec = np.array([np.cos(BED_ANG), np.sin(BED_ANG)])
nvec = np.array([-dvec[1], dvec[0]])
for off in np.cumsum(rng.uniform(35, 90, 14)) - 420:
    t0 = rng.uniform(-300, -50)
    seg = np.array([BX, BY]) + nvec * off + np.outer(np.linspace(t0, t0 + rng.uniform(120, 380), 8), dvec)
    seg += rng.normal(0, 2.5, seg.shape)
    keep = B_REACH(seg[:, 0], seg[:, 1]) < 0.92
    if keep.sum() < 3:
        continue
    seg = seg[keep]
    board.stroke(seen_bed(seg), Brush(width=3, bristle=1.0, opacity=0.35, pickup=0.0, taper=(0.4, 0.4)),
                 colors_along(seg, lambda x, y: scale(boul_col(x, y), 0.62), every=1))
board.untape()
board.stage("the boulder in body colour, turned to the sun")

# =================================================================================================
# 3. Shadows are measurements. The rock's on the bed, thrown up-left by its height; the trout's,
#    thrown down through the water until it meets something, which here is the rock.
# =================================================================================================
board.dry()
K = under(SUN_ELEV) * PPM
# the rock's shadow: every bit of it carried off by its height above the bed
ys, xs = np.nonzero(RH[::3, ::3] > 0.02)
src = np.column_stack([xs * 3 + 1.5, ys * 3 + 1.5])
drop = bed_depth(src[:, 0], src[:, 1]) - depth(src[:, 0], src[:, 1])
land = src - np.outer(drop * K, SUN)

sh = np.zeros((H, W), dtype=bool)
li = np.clip(land.astype(int), 0, [W - 1, H - 1])
sh[li[:, 1], li[:, 0]] = True
sh = binary_closing(sh, iterations=4)
ROCK_SH = np.clip(gaussian_filter(sh.astype(np.float64), 5.0) * 2.0, 0, 1) * (1 - ON_ROCK)
AWAY = smoothstep(-0.3, 0.6, -((XX - BX) * SUN[0] + (YY - BY) * SUN[1]) / 400)
FOOT = np.exp(-((B_REACH(XX, YY) - 1.02) / 0.045) ** 2) * (0.35 + 0.65 * AWAY)
board.tape_where(np.maximum(ROCK_SH, FOOT * 0.85), feather=2.0)
board.fill(whole, Brush(width=60, bristle=6.0, glaze=True, opacity=0.2, loadvar=0.0, jitter=0.0, gap=0.0, pickup=0.0,
                        taper=(0.02, 0.02)), mix((payne, 0.8), (SKY, 1.0), (phthalo, 0.3), (white, 0.6)), angle=0.6, spacing=16)

# the trout's shadow, draped over the rock's flank
body, fins = trout_outline(*FISH, FISH_LEN, FISH_ANG, bend=-0.6, n=60)
SH_PARTS = []
for p in [body] + fins:
    q = cast_down(p, FISH_D, depth, PPM, SUN_ELEV, SUN)
    SH_PARTS.append(skin.seen(q, depth))
FISH_SH = np.maximum.reduce([poly_mask(W, H, p) for p in SH_PARTS])
board.tape_where(FISH_SH, feather=2.0)
for a, op in ((FISH_ANG, 0.55), (FISH_ANG + 0.5, 0.25)):
    board.fill(whole, Brush(width=40, bristle=4.0, glaze=True, opacity=op, loadvar=0.0, taper=(0.02, 0.02), jitter=0.0,
                            gap=0.0, pickup=0.0), mix((SKY, 0.6), (payne, 1.8), (umber, 0.3)), angle=a, spacing=10)
board.untape()
board.stage("shadows: the rock's on the bed, the trout's beside it on the rock")

# =================================================================================================
# 4. The sun through the swell. Glassy water is a lens: over the rock's back, where it is shallow,
#    it lays soft bands; over the deep bed the same swell folds them into a thin net.
# =================================================================================================
board.dry()
CA = caustics(skin, lambda X, Y: depth(X, Y), blur=1.5)
CAs = gaussian_filter(CA, 1.5)
lightable = (1 - np.clip(ROCK_SH * 1.3, 0, 1)) * (1 - FISH_SH)
board.tape_where(gaussian_filter(lightable, 1.0), feather=0.0)
hot = mix((white, 7), (cadyel, 0.35), (sienna, 1.0))
# the light is laid through tape cut to where it falls: brighter where more of it piles up, and
# fainter with depth, where it has further to come back
FADE = np.exp(-np.maximum(DEP - 0.1, 0) / 0.6)
RIM = np.exp(-((B_REACH(XX, YY) - 0.97) / 0.07) ** 2)
LIGHT = np.clip((CAs - 1.0) / 0.55, 0, 1) * FADE * lightable * (1 - RIM)
board.tape_where(LIGHT, feather=1.0)
lightb = Brush(width=90, bristle=10.0, opacity=0.55, pickup=0.0, jitter=0.0, gap=0.0, loadvar=0.0, taper=(0.02, 0.02),
               thickness=0.0, wander=1.0)
board.fill(whole, lightb, hot, angle=np.radians(90), spacing=30)
board.tape_where(np.clip(LIGHT * 1.6 - 0.5, 0, 1), feather=0.8)
board.fill(whole, lightb.but(opacity=0.5), scale(hot, 1.15), angle=np.radians(80), spacing=30)
board.untape()
n_band = int((LIGHT > 0.3).sum())
board.stage("the sun through the swell: bands on the rock's back, a net in the deep")

# =================================================================================================
# 5. The river back in. The water below the trout, the trout, the water above it.
# =================================================================================================
board.dry()
ABSORB = np.array([1.65, 0.38, 0.72])
gb = Brush(width=150, bristle=18.0, opacity=0.6, glaze=True, jitter=0.0, gap=0.0, loadvar=0.0, taper=(0.2, 0.25),
           pickup=0.0, wander=2.0)
NPASS = 8
THIN = 2.5                 # many thin films rather than a few: the overlaps stop showing as rain


def glaze_band(lo, hi, n):
    def c(x, y):
        d = float(np.clip(depth(x, y), lo, hi)) - lo
        return np.clip(np.exp(-ABSORB * d / n), 0.004, 1.0)
    return c


for i in range(NPASS):
    seeds = scatter(rng, W, H, int(W * H * 1.3 * THIN / (200 * 110)), where=lambda x, y: depth(x, y) > FISH_D)
    glaze_through(board, vel, seeds, gb, glaze_band(FISH_D, 9.0, NPASS * 1.05 * THIN), 220, wobble=0.6)
veilb = Brush(width=70, bristle=6.0, opacity=0.2, pickup=0.0, jitter=0.02, gap=0.0, loadvar=0.05, taper=(0.25, 0.3),
              thickness=0.0, wander=1.0)
BODY = mix((turq, 3), (phthalo, 1.4), (ultra, 0.35), (white, 1.0))
for x, y in scatter(rng, W, H, 900, where=lambda x, y: depth(x, y) > 0.6):
    d = float(depth(x, y))
    pts = streamline(vel, x, y, 220 * rng.uniform(0.6, 1.3), step=12)
    if len(pts) < 4:
        continue
    board.stroke(pts, veilb.but(opacity=0.03 + 0.14 * smoothstep(0.6, 1.3, d)), scale(BODY, rng.uniform(0.9, 1.05)),
                 wobble=0.8)
board.stage("the water below the trout")

board.dry()
seen_f = seen_at(FISH_D)
fbody = seen_f(body)
board.tape(fbody, feather=0.9)
for f in fins:
    board.tape(seen_f(f), feather=0.9, mode="or")
BACK = mix((payne, 0.8), (phthalo, 0.6), (umber, 1.3), (ochre, 0.3), (white, 0.35))
FLANK = mix((white, 0.7), (ochre, 1.1), (umber, 0.9), (phthalo, 0.3))
ca, sa = np.cos(FISH_ANG), np.sin(FISH_ANG)
fwd, side = np.array([ca, sa]), np.array([-sa, ca])
F = np.array(FISH)
tb = Brush(width=10, bristle=1.6, opacity=0.92, pickup=0.12, jitter=0.03, gap=0.0, taper=(0.1, 0.15), thickness=0.15,
           loadvar=0.08)


def trout_col(m):
    s = float((m - F) @ side) / (FISH_LEN * 0.095)
    return scale(mix((BACK, 2.0), (FLANK, 2.2 * abs(s) ** 1.3)), rng.uniform(0.88, 1.06))


board.fill(fbody, tb, BACK, angle=FISH_ANG, spacing=3.0, color_fn=trout_col, wobble=0.4)
for f in fins:
    board.fill(seen_f(f), tb.but(width=4, opacity=0.4), mix((FLANK, 2), (white, 0.3)), angle=FISH_ANG + 0.6, spacing=2.5)
for _ in range(35):
    u = rng.uniform(-0.45, 0.4)
    s = rng.uniform(-0.9, 0.9)
    p0 = F + fwd * u * FISH_LEN + side * s * FISH_LEN * 0.06
    pts = [p0]
    a = rng.uniform(0, 2 * np.pi)
    for _ in range(4):
        a += rng.normal(0, 0.9)
        pts.append(pts[-1] + np.array([np.cos(a), np.sin(a)]) * rng.uniform(3, 6))
    board.stroke(seen_f(np.array(pts)), tb.but(width=rng.uniform(1.8, 3.0), bristle=1.0, opacity=0.4, pickup=0.0),
                 mix((payne, 2), (umber, 1)))
board.untape()
board.stage("the trout, eight centimetres down, over the rock's shoulder")

board.dry()
for i in range(NPASS):
    seeds = scatter(rng, W, H, int(W * H * 1.3 * THIN / (200 * 110)))
    glaze_through(board, vel, seeds, gb, glaze_band(0.0, FISH_D, NPASS * 1.05 * THIN), 220, wobble=0.6)
board.stage("the river back in over it")

# =================================================================================================
# 6. The skin. Glassy, so almost nothing: a stand-oil film that levels it all, a little sky on the
#    swell faces, the riffle coming in at the top, and the sun where a facet sends it up.
# =================================================================================================
board.dry()
CLEAR = np.array([1.0, 1.0, 1.0])
board.tape_where(smoothstep(250, 500, YY), feather=8.0)
board.fill(whole, Brush(width=130, bristle=16.0, glaze=True, opacity=0.6, level=1.0, loadvar=0.0, taper=(0.02, 0.02),
                        jitter=0.0, gap=0.0, pickup=0.0), CLEAR, angle=np.radians(90), spacing=40)
board.untape()
SKYHI = mix((white, 5), (ultra, 0.5), (payne, 0.25))
face = Brush(width=4, bristle=1.0, opacity=0.2, pickup=0.0, jitter=0.03, gap=0.05, taper=(0.4, 0.4), thickness=0.3,
             wander=0.3)
backb = Brush(width=4, bristle=1.0, opacity=0.25, glaze=True, jitter=0.02, gap=0.05, taper=(0.4, 0.4), wander=0.3)
DARKW = mix((payne, 1.2), (phthalo, 0.6), (white, 0.4))
xs = rng.uniform(0, W, 40000)
ys = rng.uniform(0, 520, 40000)
sx, sy = skin.slope(xs, ys)
toward = -(sx * SUN[0] + sy * SUN[1])
for x, y, gx, gy, tw in zip(xs, ys, sx, sy, toward):
    rough = float(1 - smoothstep(60, 300, y))
    if np.hypot(gx, gy) < 0.04:
        continue
    crest = np.arctan2(gy, gx) + np.pi / 2
    if tw > 0.06 and rng.random() < 0.4 * rough:
        board.dab(x, y, face.but(width=rng.uniform(3.0, 7.0), bristle=1.5, opacity=0.015 + 0.03 * min(1.0, tw / 0.3)),
                  scale(SKYHI, rng.uniform(0.9, 1.05)), angle=crest + rng.normal(0, 0.12), length=rng.uniform(10, 26))
    elif tw < -0.08 and rng.random() < 0.2 * rough:
        board.dab(x, y, backb.but(width=rng.uniform(2.0, 4.0), opacity=0.03 + 0.05 * min(1.0, -tw / 0.3)),
                  DARKW, angle=crest + rng.normal(0, 0.12), length=rng.uniform(8, 18))
board.stage("the skin: glassy, the riffle coming in at the top")

print(f"{len(cobbles)} cobbles, {n_band} px of focused sun")
finish(board, HERE, title="Soča at Log Čezsoški, 2 September 1984, 37 cm", artist="zala-hrovat", year=1984,
       medium="Oil on gessoed birch ply", made="2026-11-12")
