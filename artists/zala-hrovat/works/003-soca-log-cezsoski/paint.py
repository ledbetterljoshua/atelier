"""Zala Hrovat - Soča at Log Čezsoški, 17 August 1984, 41 cm

Upstream of Kobarid, where the river is still clear. Summer low water, near midday, the sun high
behind me and to the right. A riffle: shallow and fast over coarse cobbles at the top, a boulder
standing up into it with the water glassy over its back and a train of standing waves behind,
deepening into a glide toward the bridge. A marble trout holds in the slack behind the boulder.
Everything on the bed is seen through the broken surface, and the sun comes down through it as a
net.
"""
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[3]))
sys.path.insert(0, str(HERE.parents[1]))

from engine import Board, Brush, ground, hexc, mix, scale  # noqa: E402
from engine.studio import finish  # noqa: E402
from tools import (Skin, glaze_through, net_cells, offset_through_water, pack_stones, poly_mask,  # noqa: E402
                   scatter, smoothstep, stone_seen, streamline, trout_outline)

W, H = 1350, 1800
PPM = 540.0
rng0 = np.random.default_rng(1708)
board = Board(W, H, hexc("#f4f1e8"), ground.smooth_panel(W, H, rng0), seed=1708, light=(0.5, 0.42))
rng = board.rng

# --- tubes ---------------------------------------------------------------------------------------
white, ochre, umber, sienna = hexc("#f5f2ea"), hexc("#c49a45"), hexc("#6b5a44"), hexc("#8a4a26")
payne, phthalo, turq, ultra = hexc("#2e3640"), hexc("#0b5a4a"), hexc("#1f9a9a"), hexc("#23338c")
cadyel = hexc("#f2b01e")

SUN = np.array([0.6, 0.8]); SUN /= np.linalg.norm(SUN)        # toward the light, on the board
SUN_ELEV = 56.0                                                 # 46 N, mid August, a little after noon
SKY = mix((white, 3), (ultra, 1), (payne, 0.4))


# --- the reach -----------------------------------------------------------------------------------
BX, BY, BR = 640.0, 690.0, 112.0          # the boulder, 40 cm across, its back 12 cm under
FISH = (790.0, 1110.0)
FISH_LEN, FISH_D = 0.44 * PPM, 0.30       # a 44 cm trout, 30 cm down


def slot_x(y):
    return 990 - 0.24 * y + 30 * np.sin(y / 210)


def depth(x, y):
    x = np.asarray(x, dtype=np.float64)
    y = np.asarray(y, dtype=np.float64)
    t = smoothstep(350, 1750, y)
    d = 0.15 + 0.85 * t ** 1.3
    d = d + 0.22 * np.exp(-((x - slot_x(y)) / 260) ** 2) * (0.4 + 0.6 * smoothstep(0, 900, y))
    d = d - 0.07 * (1 - smoothstep(0, 420, x))
    d = d + 0.03 * np.sin(x / 110 + y / 170) + 0.02 * np.sin(y / 63 - x / 90)
    d = d + 0.24 * np.exp(-(((x - 690) / 170) ** 2 + ((y - 1000) / 240) ** 2))     # scoured out behind it
    rr = np.hypot(x - BX, (y - BY) / 1.12) / BR
    dome = 0.12 + (d - 0.12) * np.clip(rr, 0, 1) ** 2
    d = np.where(rr < 1, np.minimum(d, dome), d)
    return np.maximum(d, 0.06)


def vel(x, y):
    vx = -0.17 + 0.08 * np.sin(y / 120 + x / 170)
    dx, dy = x - BX, y - BY
    r = np.hypot(dx, dy) + 1e-6
    k = 0.9 * np.exp(-((r - BR * 1.05) / 60) ** 2) * (dy < 40)       # parted round the boulder's head
    vx = vx + k * dx / r
    return vx, 1.0 + 0.3 * smoothstep(300, 1500, y)


# --- the surface ---------------------------------------------------------------------------------
def train_env(X, Y):
    """Where the standing waves stand: behind the boulder, spreading and dying downstream."""
    xc = BX - 0.15 * (Y - BY)
    hw = 90 + 0.32 * np.clip(Y - 780, 0, None)
    on = smoothstep(780, 860, Y) * np.exp(-np.clip(Y - 860, 0, None) / 520)
    return on * np.exp(-((X - xc) / hw) ** 2), xc, hw


def pillow(X, Y):
    return np.exp(-(((X - BX) / (1.05 * BR)) ** 2 + ((Y - BY + 15) / (1.15 * BR)) ** 2) * 1.6)


CHOP_C = [(rng0.uniform(55, 95), rng0.normal(np.pi / 2, 0.45), rng0.uniform(0, 6.3)) for _ in range(6)]
CHOP_F = [(rng0.uniform(20, 36), rng0.normal(np.pi / 2, 0.55), rng0.uniform(0, 6.3)) for _ in range(7)]


def roughness(X, Y):
    clump = 0.5 + 0.5 * np.sin(X / 130 + np.sin(Y / 160) * 1.5) * np.sin(Y / 105 - X / 260)
    r = (0.95 - 0.78 * smoothstep(700, 1650, Y)) * (0.6 + 0.4 * clump)
    r = r + 0.25 * (1 - smoothstep(0, 380, X))                          # quick over the shallow margin
    env, _, _ = train_env(X, Y)
    r = r * (1 - 0.95 * smoothstep(0.25, 0.75, pillow(X, Y))) * (1 - 0.5 * env)
    return np.clip(r, 0, 1)


def chop_scale(Y):
    """0 coarse (the riffle head) .. 1 fine (the tail)."""
    return smoothstep(450, 1500, Y)


def height(X, Y):
    R = roughness(X, Y)
    f = chop_scale(Y)
    hc = np.zeros_like(X)
    hf = np.zeros_like(X)
    for lam, a, ph in CHOP_C:
        kx, ky = np.cos(a) * 2 * np.pi / lam, np.sin(a) * 2 * np.pi / lam
        hc += 0.17 * lam / (2 * np.pi * PPM) * np.sin(kx * X + ky * Y + ph + 0.6 * np.sin(X / 97))
    for lam, a, ph in CHOP_F:
        kx, ky = np.cos(a) * 2 * np.pi / lam, np.sin(a) * 2 * np.pi / lam
        hf += 0.13 * lam / (2 * np.pi * PPM) * np.sin(kx * X + ky * Y + ph + 0.5 * np.sin(X / 61))
    h = R * ((1 - f) * hc + f * hf)
    env, xc, hw = train_env(X, Y)
    lam = 150.0
    h += 0.019 * env * np.cos(2 * np.pi * (Y - 860) / lam - 1.1 * ((X - xc) / hw) ** 2)
    h += 0.035 * pillow(X, Y)
    # the glide: long slow swells and nothing else
    h += 0.004 * smoothstep(1100, 1700, Y) * np.sin(Y / 70 + 0.8 * np.sin(X / 210))
    return h


skin = Skin(height, W, H, PPM)
XX, YY = np.meshgrid(np.arange(W) + 0.5, np.arange(H) + 0.5)
ROUGH = roughness(XX, YY)
ENV, _, _ = train_env(XX, YY)


def seen_bed(pts):
    return skin.seen(pts, depth)


def seen_at(d):
    return lambda pts: skin.seen(pts, d)


# where the trout's shadow lands on the bed: down through its 30 cm and the half metre below it
d_bed = float(depth(*FISH))
ox, oy = offset_through_water(d_bed - FISH_D, PPM, SUN_ELEV, SUN)
FISH_ANG = np.arctan2(-1.0, 0.16)          # nose into the current
body, fins = trout_outline(*FISH, FISH_LEN, FISH_ANG, bend=0.5)
SH_BODY = [skin.seen(p + [ox, oy], d_bed) for p in [body] + fins]
FISH_SHADOW = np.maximum.reduce([poly_mask(W, H, p) for p in SH_BODY])

# =================================================================================================
# 1. The river turned off: the bed, coarse at the head of the riffle and finer toward the glide.
# =================================================================================================
silt = mix((umber, 2), (white, 1.6), (ochre, 0.5), (payne, 0.6))
scrub = Brush(width=70, bristle=2.4, opacity=0.9, pickup=0.15, jitter=0.07, deplete=0.0012, thickness=0.2)
whole = [(-60, -60), (W + 60, -60), (W + 60, H + 60), (-60, H + 60)]


def silt_col(m):
    d = float(depth(*m))
    return scale(silt, (1.0 - 0.3 * smoothstep(0.3, 1.0, d)) * rng.uniform(0.86, 1.1))


board.fill(whole, scrub, silt, angle=np.radians(rng.uniform(70, 110)), color_fn=silt_col)

A_LIME = mix((white, 6), (ochre, 0.45), (umber, 0.3))
A_GREY = mix((white, 3), (payne, 1), (umber, 0.3))
A_BLUE = mix((white, 4), (ultra, 0.45), (payne, 0.8))
A_PINK = mix((white, 4), (sienna, 0.6), (ochre, 0.3))
A_DARK = mix((payne, 2), (umber, 1), (white, 0.9))
KINDS = [(A_LIME, 0.68), (A_GREY, 0.13), (A_BLUE, 0.07), (A_PINK, 0.09), (A_DARK, 0.03)]
probs = np.array([p for _, p in KINDS]); probs /= probs.sum()
FILM = mix((umber, 2), (phthalo, 0.5), (ochre, 0.6), (white, 1.0))
cast = mix((payne, 1.2), (umber, 0.6), (white, 0.7))


def r_fn(x, y, g):
    med = 26 - 16 * smoothstep(200, 1650, y)
    return float(np.clip(g.lognormal(np.log(med), 0.42), 4, 80))


def off_boulder(x, y):
    return np.hypot(x - BX, (y - BY) / 1.12) > BR * 0.92


stones = pack_stones(rng, W, H, r_fn, 60000, overlap=0.93, where=off_boulder)
pb = Brush(width=20, bristle=1.2, opacity=0.95, pickup=0.08, jitter=0.05, gap=0.02, deplete=0.001,
           thickness=0.25, wander=0.4, hard=True)
for (x, y, r) in stones:
    A = scale(KINDS[rng.choice(len(KINDS), p=probs)][0], rng.uniform(0.86, 1.06))
    d = float(depth(x, y))
    film = smoothstep(0.35, 1.0, d)
    A = mix((A, 1 - 0.6 * film), (FILM, 0.6 * film + 1e-3))
    dark = scale(mix((A, 3), (SKY, 1), (umber, 0.3)), 0.42 + 0.15 * film)
    stone_seen(board, seen_bed, x, y, r, rng.uniform(0, np.pi), rng.uniform(1.0, 1.5), scale(A, 1.08), dark, SUN,
               pb.but(bristle=max(1.0, r / 11)), shadow=cast, shadow_len=0.42)

# the boulder: a grey limestone block, rounded, a skin of brown algae low on its flanks. Modelled as
# a dome in the sun, every stroke mixed for which way that bit of it faces.
BOUL = mix((white, 6), (payne, 0.45), (ochre, 0.3))
bb = Brush(width=16, bristle=1.6, opacity=0.95, pickup=0.3, jitter=0.04, gap=0.02, thickness=0.6, wander=0.5)
th = np.linspace(0, 2 * np.pi, 80, endpoint=False)
rim_r = BR * (1 + 0.06 * np.sin(3 * th + 1.0) + 0.04 * np.sin(5 * th + 2.2))
outline = np.column_stack([BX + rim_r * np.cos(th), BY + 1.12 * rim_r * np.sin(th)])
L3 = np.array([SUN[0] * np.cos(np.radians(SUN_ELEV)), SUN[1] * np.cos(np.radians(SUN_ELEV)), np.sin(np.radians(SUN_ELEV))])
# its shadow on the bed, the height of it (22 cm) carried off by the refracted sun
board.tape(seen_bed(outline - SUN * BR * 0.5), feather=2.0)
board.tape(seen_bed(outline), mode="cut")
board.fill(whole, Brush(width=50, bristle=5.0, glaze=True, opacity=0.6, jitter=0.01, gap=0.0, pickup=0.0, taper=(0.02, 0.02)),
           cast, angle=0.4, spacing=14)
board.tape(seen_bed(outline), feather=1.2)


def boul_col(m):
    m = np.asarray(m)
    nx, ny = (m[0] - BX) / BR, (m[1] - BY) / (1.12 * BR)
    rr = min(np.hypot(nx, ny), 0.99)
    nz = np.sqrt(1 - rr * rr)
    lam = max(0.0, (nx * L3[0] + ny * L3[1] + nz * L3[2]) / np.linalg.norm([nx, ny, nz]))
    c = mix((BOUL, 3), (FILM, 2.2 * rr ** 4 + 1e-3), (SKY, 0.8 * (1 - lam)))
    pit = 0.82 if np.sin(m[0] / 9 + np.sin(m[1] / 13) * 2) * np.sin(m[1] / 11 - m[0] / 23) > 0.55 else 1.0
    return scale(c, (0.3 + 0.82 * lam ** 1.4) * pit * rng.uniform(0.94, 1.05))


for ang in (np.radians(20), np.radians(-55), np.radians(70)):
    board.fill(seen_bed(outline), bb.but(width=rng.uniform(12, 18)), BOUL, angle=ang, spacing=7,
               color_fn=lambda m: boul_col(m), wobble=0.5)
board.untape()
board.stage("the river turned off: cobbles at the head, gravel in the tail, the boulder")

# =================================================================================================
# 2. The sun on the bed, through the chop: a net, coarse where the chop is coarse, bars of light
#    under the standing waves, and none in the trout's shadow or on the boulder's glassy back.
# =================================================================================================
board.dry()
hot = mix((white, 7), (cadyel, 0.9), (ochre, 0.25))
board.tape_where(lambda X, Y: (1 - FISH_SHADOW) * np.clip(0.25 + ROUGH, 0, 1) * (1 - 0.7 * ENV)
                 * (1 - smoothstep(0.3, 0.6, pillow(X, Y))), feather=1.0)
netb = Brush(width=4, bristle=1.0, opacity=0.6, pickup=0.0, jitter=0.03, gap=0.0, taper=(0.2, 0.2),
             thickness=0.0, dryness=0.12)


def cell_fn(x, y):
    return 60 - 28 * float(chop_scale(y)) + 30 * float(smoothstep(0.6, 1.2, depth(x, y)))


segs = net_cells(rng, W, H, cell_fn, 16000, stretch=1.45, angle=np.radians(-9))


def junction_heavy(t):
    return 0.4 + 0.85 * np.abs(2 * t - 1) ** 1.5


for a, b in segs:
    m = (a + b) / 2
    d = float(depth(*m))
    rgh = float(ROUGH[int(np.clip(m[1], 0, H - 1)), int(np.clip(m[0], 0, W - 1))])
    focus = np.exp(-d / 0.75) * (0.35 + 0.65 * rgh)
    if rng.random() > 0.1 + 0.85 * focus:
        continue
    nrm = np.array([-(b - a)[1], (b - a)[0]]) / (np.hypot(*(b - a)) + 1e-9)
    bend = rng.normal(0, 0.12) * np.hypot(*(b - a))
    path = seen_bed(np.array([a, a + (b - a) * 0.35 + nrm * bend, a + (b - a) * 0.7 + nrm * bend * 0.4, b]))
    if rng.random() < 0.18:
        continue
    w = (2.5 + 6.0 * (1 - focus)) * rng.uniform(0.6, 1.6)
    board.stroke(path, netb.but(width=w * 5.0, bristle=w * 1.4, opacity=0.1 + 0.2 * focus),
                 scale(hot, 0.95), pressure=junction_heavy)
    board.stroke(path, netb.but(width=w, bristle=max(1.2, w * 0.45), opacity=0.35 + 0.65 * focus, jitter=0.01),
                 scale(hot, 1.0 + 0.25 * focus), pressure=junction_heavy)

# bars of light under the standing waves: each crest is a lens laid across the river
board.tape_where(lambda X, Y: 1 - FISH_SHADOW, feather=1.0)
for k in range(5):
    yc = 860 + k * 150 + 34
    env_k = float(np.exp(-k * 150 / 420))
    xc = BX - 0.15 * (yc - BY)
    hw = 90 + 0.32 * (yc - 780)
    for j in range(int(5 + 3 * env_k)):
        u0 = rng.uniform(-1.3, 1.0)
        u = np.linspace(u0, u0 + rng.uniform(0.25, 0.7), 9)
        xs = xc + u * hw
        ys = yc + 1.1 * u ** 2 * 150 / (2 * np.pi) + rng.normal(0, 4) + 6 * np.sin(xs / 37 + j)
        pts = seen_bed(np.column_stack([xs, ys]))
        board.stroke(pts, netb.but(width=16, bristle=4.0, opacity=0.25 * env_k + 0.06), scale(hot, 0.95))
        board.stroke(pts, netb.but(width=5, bristle=2.0, opacity=0.6 * env_k + 0.25, jitter=0.01),
                     scale(hot, 1.15), pressure=lambda t: 0.5 + 0.6 * np.sin(np.pi * t))
board.untape()
for _ in range(5):
    a0 = rng.uniform(-0.3, 1.9)
    th = np.linspace(a0, a0 + rng.uniform(0.5, 1.4), 14)
    k = rng.uniform(0.95, 1.12)
    ring = np.column_stack([BX + np.cos(th) * BR * k, BY + 1.12 * np.sin(th) * BR * k])
    ring = seen_bed(ring + rng.normal(0, 3, ring.shape))
    board.stroke(ring, netb.but(width=18, bristle=4.0, opacity=0.18), scale(hot, 0.95))
    board.stroke(ring, netb.but(width=4, bristle=2.0, opacity=0.35, jitter=0.01), scale(hot, 1.1),
                 pressure=lambda t: 0.4 + 0.7 * np.sin(np.pi * t))
board.stage("the sun's net, coarse under the riffle, fine in the tail; bars under the waves")

# the trout's shadow: where its half metre of water to the bed lands it, sharper than the fish
board.tape_where(FISH_SHADOW, feather=1.6)
board.fill(whole, Brush(width=40, bristle=4.0, glaze=True, opacity=0.7, taper=(0.02, 0.02), jitter=0.01, gap=0.0,
                        pickup=0.0), mix((SKY, 0.8), (payne, 1.6)), angle=FISH_ANG, spacing=10)
board.fill(whole, Brush(width=40, bristle=4.0, glaze=True, opacity=0.5, taper=(0.02, 0.02), jitter=0.01, gap=0.0,
                        pickup=0.0), mix((SKY, 0.5), (payne, 2.0)), angle=FISH_ANG + 0.5, spacing=12)
board.untape()
board.stage("the trout's shadow on the bed")

# =================================================================================================
# 3. The river back in. First the water below the trout, then the trout, then the water over it.
# =================================================================================================
board.dry()
ABSORB = np.array([1.7, 0.42, 0.62])
gb = Brush(width=90, bristle=12.0, opacity=0.6, glaze=True, jitter=0.0, gap=0.0, taper=(0.2, 0.25),
           pickup=0.0, wander=2.0)
NPASS = 6


def glaze_below(n):
    def c(x, y):
        d = max(float(depth(x, y)) - FISH_D, 0.0)
        return np.clip(np.exp(-ABSORB * 1.0 * d / n) * rng.uniform(0.985, 1.015), 0.004, 1.0)
    return c


def glaze_above(n):
    def c(x, y):
        d = min(float(depth(x, y)), FISH_D)
        return np.clip(np.exp(-ABSORB * 1.0 * d / n) * rng.uniform(0.985, 1.015), 0.004, 1.0)
    return c


for i in range(NPASS):
    seeds = scatter(rng, W, H, int(W * H * 1.5 / (200 * 90)), where=lambda x, y: depth(x, y) > FISH_D)
    glaze_through(board, vel, seeds, gb, glaze_below(NPASS * 1.05), 200)
# the water's own colour, where it is deep enough to have one
veilb = Brush(width=50, bristle=2.2, opacity=0.2, pickup=0.0, jitter=0.05, gap=0.05, taper=(0.25, 0.3),
              thickness=0.05, wander=1.0)
BODY = mix((turq, 3), (phthalo, 1.2), (ultra, 0.3), (white, 1.2))
for x, y in scatter(rng, W, H, 1300, where=lambda x, y: depth(x, y) > 0.5):
    d = float(depth(x, y))
    pts = streamline(vel, x, y, 200 * rng.uniform(0.6, 1.3), step=12)
    if len(pts) < 4:
        continue
    board.stroke(pts, veilb.but(opacity=0.02 + 0.13 * smoothstep(0.55, 1.2, d), width=veilb.width * rng.uniform(0.7, 1.3)),
                 scale(BODY, rng.uniform(0.85, 1.1)), wobble=1.0)
board.stage("the water below the trout")

# the trout, in body colour, where the surface shows it at thirty centimetres
board.dry()
seen_f = seen_at(FISH_D)
fbody = seen_f(body)
board.tape(fbody, feather=0.9)
for f in fins:
    board.tape(seen_f(f), feather=0.9, mode="or")
BACK = mix((payne, 1.0), (phthalo, 0.6), (umber, 1.0), (white, 0.45))
FLANK = mix((white, 1.5), (ochre, 0.6), (umber, 0.8), (payne, 0.4))
ca, sa = np.cos(FISH_ANG), np.sin(FISH_ANG)
fwd, side = np.array([ca, sa]), np.array([-sa, ca])
F = np.array(FISH)
tb = Brush(width=8, bristle=1.1, opacity=0.9, pickup=0.35, jitter=0.05, gap=0.0, taper=(0.15, 0.2), thickness=0.8)


def trout_col(m):
    s = float((m - F) @ side) / (FISH_LEN * 0.095)
    return scale(mix((BACK, 2.0), (FLANK, 2.5 * abs(s) ** 1.3)), rng.uniform(0.85, 1.08))


board.fill(fbody, tb, BACK, angle=FISH_ANG, spacing=3.5, color_fn=trout_col, wobble=0.4)
for f in fins:
    board.fill(seen_f(f), tb.but(width=4, opacity=0.6), mix((FLANK, 2), (white, 0.6)), angle=FISH_ANG + 0.6, spacing=2.5)
# the marbling: worm-tracks of dark over the olive, the mark of the Soča trout
for _ in range(60):
    u = rng.uniform(-0.45, 0.4)
    s = rng.uniform(-0.9, 0.9)
    p0 = F + fwd * u * FISH_LEN + side * s * FISH_LEN * 0.06
    pts = [p0]
    a = rng.uniform(0, 2 * np.pi)
    for _ in range(4):
        a += rng.normal(0, 0.9)
        pts.append(pts[-1] + np.array([np.cos(a), np.sin(a)]) * rng.uniform(3, 7))
    board.stroke(seen_f(np.array(pts)), tb.but(width=rng.uniform(1.6, 3.0), opacity=0.7, pickup=0.0),
                 mix((payne, 2), (umber, 1)))
board.untape()
board.stage("the trout, thirty centimetres down")

board.dry()
for i in range(NPASS):
    seeds = scatter(rng, W, H, int(W * H * 1.5 / (200 * 90)))
    glaze_through(board, vel, seeds, gb, glaze_above(NPASS * 1.05), 200)

board.stage("the river back in over it")

# =================================================================================================
# 4. The skin. Faces tipped toward the bright side of the sky take a little of it; backs tipped
#    away take a little dark. Each mark lies along the crest it is on and is as long as that chop.
# =================================================================================================
board.dry()
SKYHI = mix((white, 5), (ultra, 0.5), (payne, 0.25))
face = Brush(width=4, bristle=1.0, opacity=0.3, pickup=0.0, jitter=0.03, gap=0.05, taper=(0.4, 0.4),
             thickness=0.3, wander=0.3)
backb = Brush(width=4, bristle=1.0, opacity=0.25, glaze=True, jitter=0.02, gap=0.05, taper=(0.4, 0.4), wander=0.3)
DARKW = mix((payne, 1.2), (phthalo, 0.6), (white, 0.4))
xs = rng.uniform(0, W, 90000)
ys = rng.uniform(0, H, 90000)
sx, sy = skin.slope(xs, ys)
toward = -(sx * SUN[0] + sy * SUN[1])
n_face = n_back = 0
for x, y, gx, gy, tw in zip(xs, ys, sx, sy, toward):
    rg = float(ROUGH[int(y), int(x)])
    s = np.hypot(gx, gy)
    if s < 0.05:
        continue
    crest = np.arctan2(gy, gx) + np.pi / 2
    lam = 80 - 52 * float(chop_scale(y))
    if tw > 0.08 and rng.random() < 0.45 * min(1.0, tw / 0.3) * rg ** 1.5:
        L = lam * rng.uniform(0.3, 0.7)
        board.dab(x, y, face.but(width=rng.uniform(3.0, 8.0), bristle=1.6, opacity=0.04 + 0.12 * min(1.0, tw / 0.35)),
                  scale(SKYHI, rng.uniform(0.9, 1.05)), angle=crest + rng.normal(0, 0.12), length=L)
        n_face += 1
    elif tw < -0.1 and rng.random() < 0.2 * min(1.0, -tw / 0.3) * rg ** 1.5:
        L = lam * rng.uniform(0.25, 0.5)
        board.dab(x, y, backb.but(width=rng.uniform(2.0, 4.5), opacity=0.06 + 0.12 * min(1.0, -tw / 0.35)),
                  DARKW, angle=crest + rng.normal(0, 0.12), length=L)
        n_back += 1

# the glassy water over the boulder and the glide lie flat: a clear stand-oil glaze that levels
CLEAR = np.array([1.0, 1.0, 1.0])
board.tape_where(np.clip(pillow(XX, YY) * 1.4, 0, 1) + smoothstep(1250, 1700, YY) * 0.8, feather=6.0)
board.fill(whole, Brush(width=120, bristle=14.0, glaze=True, opacity=0.6, level=1.0, taper=(0.02, 0.02), jitter=0.0,
                        gap=0.0, pickup=0.0), CLEAR, angle=np.radians(90), spacing=18)
board.untape()
# where the water comes off the boulder's back and drops into the hole, it breaks white
fb = Brush(width=4, bristle=1.0, opacity=0.85, pickup=0.0, jitter=0.02, gap=0.0, taper=(0.3, 0.3), thickness=1.6)
FOAM = mix((white, 8), (ochre, 0.2), (ultra, 0.1))
for _ in range(70):
    u = rng.uniform(-1.0, 1.0)
    yc = 860 + 0.15 * 150 + 1.1 * u ** 2 * 150 / (2 * np.pi)
    z = np.array([BX - 0.15 * (yc - BY) + u * (90 + 0.32 * (yc - 780)), yc]) + rng.normal(0, [6, 9])
    if rng.random() < 1 - abs(u) * 0.7:
        board.dab(z[0], z[1], fb.but(width=rng.uniform(1.3, 3.0), opacity=rng.uniform(0.4, 0.8)),
                  scale(FOAM, rng.uniform(0.8, 1.0)), length=rng.uniform(1.5, 3.5))
# the standing waves: each crest's downstream face is tipped toward the sun and the bright sky
# behind me, and carries a band of it, broken where the chop crosses
for k in range(5):
    yc = 860 + k * 150
    env_k = float(np.exp(-k * 150 / 420))
    xc = BX - 0.15 * (yc - BY)
    hw = 90 + 0.32 * (yc - 780)
    for j in range(int(4 + 6 * env_k)):
        u0 = rng.uniform(-1.4, 1.1)
        u = np.linspace(u0, u0 + rng.uniform(0.2, 0.55), 8)
        xs = xc + u * hw
        ys = yc + 1.1 * u ** 2 * 150 / (2 * np.pi) + 22 + rng.normal(0, 3) + 4 * np.sin(xs / 29 + j)
        fall = float(np.exp(-np.mean(u) ** 2 * 1.3))
        board.stroke(np.column_stack([xs, ys]), face.but(width=rng.uniform(8, 18), bristle=2.4,
                     opacity=(0.1 + 0.14 * env_k) * fall), scale(SKYHI, rng.uniform(0.95, 1.05)), wobble=1.0)
        board.stroke(np.column_stack([xs, ys - 30]), backb.but(width=rng.uniform(8, 16), bristle=2.4,
                     opacity=(0.04 + 0.06 * env_k) * fall), DARKW, wobble=1.0)
board.stage("the skin: sky on the faces, dark on the backs, glass over the boulder")

# =================================================================================================
# 5. The sun itself, last, wherever a facet is tipped just so. The brightest paint on the panel.
# =================================================================================================
board.dry()
GLINT = mix((white, 10), (cadyel, 0.35))
gl = Brush(width=4, bristle=1.0, opacity=0.95, pickup=0.0, jitter=0.01, gap=0.0, taper=(0.3, 0.3), thickness=2.2)
# strung along the crests of the standing waves, where the faces are steepest
for k in range(5):
    yc = 860 + k * 150
    env_k = float(np.exp(-k * 150 / 420))
    xc = BX - 0.15 * (yc - BY)
    hw = 90 + 0.32 * (yc - 780)
    for _ in range(int(60 * env_k ** 1.5)):
        u = rng.normal(0, 0.55)
        x = xc + u * hw
        y = yc + 1.1 * u ** 2 * 150 / (2 * np.pi) + 14 + rng.normal(0, 6)
        q = rng.uniform(0.3, 1.0) * np.exp(-u * u)
        board.dab(x, y, gl.but(width=1.2 + 2.4 * q, opacity=0.5 + 0.5 * q), GLINT,
                  angle=rng.normal(0, 0.25), length=1.5 + 7 * q * rng.uniform(0.5, 1.3))
gx_, gy_, gq = skin.glints(rng, 900_000, SUN, SUN_ELEV, 0.035)
for x, y, q in zip(gx_, gy_, gq):
    gx, gy = skin.slope(x, y)
    crest = np.arctan2(gy, gx) + np.pi / 2
    board.dab(x, y, gl.but(width=1.2 + 2.2 * q * rng.uniform(0.6, 1.2), opacity=0.55 + 0.45 * q),
              GLINT, angle=crest + rng.normal(0, 0.2), length=1.5 + 5 * q * rng.uniform(0.5, 1.3))
board.stage("the sun on the facets")

print(f"surface: {n_face} faces, {n_back} backs, {len(gx_)} glints, {len(stones)} stones")
finish(board, HERE, title="Soča at Log Čezsoški, 17 August 1984, 41 cm", artist="zala-hrovat", year=1984,
       medium="Oil on gessoed birch ply", made="2026-11-12")
