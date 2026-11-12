"""Zala Hrovat - Soča at Kobarid, 4 November 1983, 112 cm

The same place over the same parapet as 001, five months on. Two days of rain; the river is up
54 cm and carrying the mountain, so the bar is a ghost and the channel shows nothing. Low cloud,
no sun. Boils come up off the lip of the bar and spread; between them the surface is broken and
catches the sky. A hazel branch is coming down the seam with its heavy end under.
"""
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[3]))
sys.path.insert(0, str(HERE.parents[1]))

from engine import Board, Brush, ground, hexc, mix, scale  # noqa: E402
from engine.studio import finish  # noqa: E402
from tools import (Boils, foam_lace, glaze_through, leaf_outline, pack_stones, scatter,  # noqa: E402
                   smoothstep, stone_under_cloud, streamline)

W, H = 1350, 1800
PPM = 540.0
rng0 = np.random.default_rng(1104)
# no sun: the studio window is the only raking light, and it is a grey one
board = Board(W, H, hexc("#f4f1e8"), ground.smooth_panel(W, H, rng0), seed=1104, light=(-0.3, -0.42))
rng = board.rng

# --- tubes ---------------------------------------------------------------------------------------
white, ochre, umber, sienna = hexc("#f5f2ea"), hexc("#c49a45"), hexc("#6b5a44"), hexc("#8a4a26")
payne, phthalo, turq, ultra = hexc("#2e3640"), hexc("#0b5a4a"), hexc("#1f9a9a"), hexc("#23338c")
cadorange = hexc("#e8701a")

CLOUD = mix((white, 6), (payne, 1.0), (ochre, 0.15))     # the sky, what the surface gives back
RISE = 0.54                                              # 112 cm against 58 in June


# --- the reach: the same bed as in June, with half a metre more on top --------------------------
def edge(y):
    return W * (0.64 - 0.28 * y / H) + 28 * np.sin(y / 170 + 0.7) + 14 * np.sin(y / 61)


def depth(x, y):
    x = np.asarray(x, dtype=np.float64)
    y = np.asarray(y, dtype=np.float64)
    e = edge(y)
    s = smoothstep(-70, 160, x - e)
    bar = 0.09 + 0.16 * smoothstep(-400, 0, x - e) + 0.03 * np.sin(x / 90 + y / 140)
    deep = 0.9 + 0.9 * smoothstep(40, 640, x - e) ** 1.3 + 0.12 * np.sin(y / 230 + x / 300)
    return RISE + bar * (1 - s) + deep * s


def see(d):
    """How much of the bed still comes back through silty water at a depth."""
    return np.exp(-np.maximum(d, 0.0) / 0.42)


def base_vel(x, y):
    e = edge(y)
    s = smoothstep(-70, 160, x - e)
    vx = -0.21 + 0.10 * np.sin(y / 95 + x / 160)
    k = np.exp(-((x - e - 40) / 110) ** 2)               # the shear over the lip
    vx += 0.45 * k * np.sin(y / 85 + 0.5)
    vx += 0.30 * s * np.sin(y / 180 + x / 260 + 1.0)
    return vx, (0.9 + 0.5 * s)


# Boils come up just downstream of the lip, where the fast channel water tears over the step.
BOILS = Boils([
    (930, 330, 135, 1.5),
    (800, 900, 215, 1.8),
    (1215, 1240, 95, 0.9),
    (735, 1600, 165, 1.6),          # the one under me
])
# and on the shear, where the bar water and the channel water rub, slow whirls that turn the slick
VORT = [(edge(y) + 70 + rng0.normal(0, 25), y, rng0.uniform(50, 95), rng0.choice([-1, 1]) * rng0.uniform(0.9, 1.6))
        for y in (140, 560, 1120, 1380)]


def swirl_vel(x, y):
    vx, vy = base_vel(x, y)
    for cx, cy, r, w in VORT:
        dx, dy = x - cx, y - cy
        d2 = dx * dx + dy * dy
        k = w * np.exp(-d2 / (2 * r * r))
        vx, vy = vx - k * dy / r, vy + k * dx / r
    return vx, vy


vel = BOILS.flow(swirl_vel)

# the branch: a metre of hazel, the butt end heavy and under, the tip and its twigs riding
DRIFT = np.array([(560, 380), (604, 470), (640, 560), (668, 650), (690, 740), (700, 820)], dtype=float)
UNDER_FROM = 0.62                    # past this far along it is under water, getting deeper
TWIGS = [(0.14, -1, 60), (0.3, 1, 80), (0.48, -1, 42)]
LEAVES = [(0.05, 1, 1.05, 0.0), (0.3, 1, 1.15, 0.55), (0.42, -1, 0.9, 0.3)]


def along_branch(t):
    from scipy.interpolate import interp1d
    s_ = np.concatenate([[0], np.cumsum(np.hypot(*np.diff(DRIFT, axis=0).T))])
    f = interp1d(s_ / s_[-1], DRIFT, axis=0)
    return f(np.clip(t, 0, 1))

def roughness(X, Y):
    """How broken the surface is: chop everywhere, more on the shear, none on top of a boil."""
    e = edge(Y)
    n = 0.5 + 0.5 * np.sin(X / 70 + np.sin(Y / 55) * 1.7) * np.sin(Y / 90 - X / 210)
    shear = np.exp(-((X - e - 60) / 140) ** 2)
    bar = 1.0 - smoothstep(-60, 200, X - e)
    r = 0.48 + 0.25 * n + 0.35 * shear + 0.2 * bar
    # what came up in a boil stays smooth a while as it is carried off: slicks trailing downstream
    trail = np.zeros_like(X)
    for i, (cx, cy, rb, _) in enumerate(BOILS.b):
        along = (Y - cy) / rb
        wob = 0.25 * rb * np.sin((Y - cy) / 70 + i)
        side = np.abs(X - cx + 0.22 * (Y - cy) - wob) / (rb * (0.75 - 0.25 * smoothstep(0, 4, along)))
        trail = np.maximum(trail, smoothstep(0.0, 0.8, along) * (1 - smoothstep(1.5, 4.5, along))
                           * (1 - smoothstep(0.4, 1.0, side)))
    r = r * (1.0 - 0.8 * trail)
    r = r * (1.0 - BOILS.inside(X, Y))
    return np.clip(r, 0, 1)


# =================================================================================================
# 1. The bed, turned off, but only as much of it as will come through.
# =================================================================================================
silt = mix((umber, 2), (white, 2), (ochre, 0.6), (payne, 0.4))
scrub = Brush(width=80, bristle=2.6, opacity=0.9, pickup=0.15, jitter=0.07, deplete=0.0012)
whole = [(-60, -60), (W + 60, -60), (W + 60, H + 60), (-60, H + 60)]


def silt_col(m):
    d = float(depth(*m))
    return scale(mix((silt, 3), (white, 1.2 * see(d))), (0.8 + 0.25 * see(d)) * rng.uniform(0.88, 1.1))


board.fill(whole, scrub, silt, angle=np.radians(rng.uniform(70, 110)), color_fn=silt_col)

A_LIME = mix((white, 6), (ochre, 0.6), (umber, 0.4))
A_GREY = mix((white, 3), (payne, 1), (umber, 0.3))
A_RUST = mix((white, 2), (sienna, 1), (ochre, 0.8))
KINDS = [A_LIME, A_GREY, A_RUST]


def r_fn(x, y, g):
    return float(np.clip(g.lognormal(np.log(30), 0.4), 12, 70))


stones = pack_stones(rng, W, H, r_fn, 6000, overlap=0.8, where=lambda x, y: see(depth(x, y)) > 0.12)
pb = Brush(width=20, bristle=1.4, opacity=0.95, pickup=0.1, jitter=0.05, gap=0.02, thickness=0.5, wander=0.4)
for (x, y, r) in stones:
    A = scale(KINDS[rng.choice(3, p=[0.7, 0.22, 0.08])], rng.uniform(0.85, 1.05))
    stone_under_cloud(board, x, y, r, rng.uniform(0, np.pi), rng.uniform(1.0, 1.5), A,
                      scale(mix((A, 2), (silt, 1)), 0.72 - 0.9 * see(float(depth(x, y))) * (1 - y / H)), pb.but(bristle=max(1.0, r / 14)))
bark = mix((umber, 3), (payne, 1), (sienna, 0.6))
tt = np.linspace(UNDER_FROM, 1.0, 12)
board.stroke(along_branch(tt), Brush(width=24, bristle=1.4, opacity=0.95, pickup=0.1, taper=(0.0, 0.3), thickness=0.4),
             [scale(mix((bark, 1), (payne, 1)), 0.45 - 0.2 * u) for u in np.linspace(0, 1, 6)])
board.stage("the bed, as much of it as will come through; the sunk end of the branch")

# =================================================================================================
# 2. The river back in. The glazes cross the lip now instead of stopping at it.
# =================================================================================================
board.dry()
ABSORB = np.array([1.25, 0.55, 0.75])          # flood water: the silt takes the blue as well


def glaze_at(n):
    def c(x, y):
        d = float(depth(x, y))
        return np.clip(np.exp(-ABSORB * (0.55 * d + 0.5 * max(d - 1.0, 0.0) ** 1.2) / n) * rng.uniform(0.985, 1.015), 0.004, 1.0)
    return c


gb = Brush(width=80, bristle=3.2, opacity=0.6, glaze=True, jitter=0.02, gap=0.0, taper=(0.2, 0.25),
           pickup=0.0, wander=2.0)
NPASS = 7
for i in range(NPASS):
    seeds = scatter(rng, W, H, int(W * H * 1.6 / (190 * 80)))
    glaze_through(board, vel, seeds, gb, glaze_at(NPASS * 1.05), 190)
board.stage("the river back in, the glazes crossing the lip")

# =================================================================================================
# 3. The silt in it. Not glaze: the mountain in the water sends light back before it reaches
#    the bed, so it goes on as a thin scumble, heavier where there is more water to hold it.
# =================================================================================================
board.dry()
MILK = mix((white, 3), (ochre, 0.6), (payne, 0.75), (turq, 0.3), (umber, 0.25))
sb = Brush(width=90, bristle=2.6, opacity=0.2, pickup=0.0, jitter=0.03, gap=0.03, taper=(0.25, 0.3),
           thickness=0.05, wander=1.5)


def milk_at(x, y):
    d = float(depth(x, y))
    return scale(MILK, (0.8 - 0.3 * smoothstep(1.0, 2.4, d)) * rng.uniform(0.96, 1.04))


for i in range(7):
    seeds = scatter(rng, W, H, int(W * H * 1.0 / (200 * 90)))
    for x, y in seeds:
        pts = streamline(vel, x, y, 200 * rng.uniform(0.6, 1.3), step=12)
        if len(pts) < 4:
            continue
        op = 0.1 + 0.22 * (1 - see(float(depth(x, y)))) ** 2 + 0.06 * y / H
        board.stroke(pts, sb.but(opacity=op, width=sb.width * rng.uniform(0.7, 1.3)),
                     [milk_at(*p) for p in pts[::4]], wobble=1.0)
board.stage("the silt in it")

# =================================================================================================
# 4. The boils: smooth, levelled, a little milkier than the water round them, spreading.
# =================================================================================================
board.dry()
boil_top = Brush(width=26, bristle=2.0, opacity=0.2, pickup=0.0, jitter=0.02, gap=0.0, taper=(0.15, 0.5),
                 thickness=0.0, level=1.0, wander=1.0)
UP = scale(mix((MILK, 3), (phthalo, 0.6), (payne, 0.3)), 0.42)
crease = Brush(width=4, bristle=1.2, opacity=0.2, glaze=True, jitter=0.02, gap=0.05, taper=(0.4, 0.4), wander=0.5)
board.tape_where(lambda X, Y: BOILS.inside(X, Y, soft=0.02), feather=0.8)
for i, (cx, cy, r, push) in enumerate(BOILS.b):
    for k in range(int(r * 1.1)):
        rr_, aa_ = r * 1.05 * np.sqrt(rng.random()), rng.uniform(0, 2 * np.pi)
        c = np.array([cx, cy]) + rr_ * np.array([np.cos(aa_), np.sin(aa_)])
        a = rng.uniform(0, np.pi)
        L = rng.uniform(0.4, 0.9) * r
        d_ = np.array([np.cos(a), np.sin(a)]) * L / 2
        board.stroke([c - d_, c + d_], boil_top.but(width=rng.uniform(40, 70), opacity=0.08),
                     scale(UP, rng.uniform(0.98, 1.02)), wobble=2.0)
    # and a few faint wrinkles running out from where it comes up
    for k in range(int(r * 0.08)):
        a = rng.uniform(0, 2 * np.pi)
        e = BOILS.edge_at(i, np.array([a]))[0]
        c = np.array([cx, cy])
        board.stroke([c + (e - c) * rng.uniform(0.3, 0.6), e], boil_top.but(width=rng.uniform(4, 9), opacity=0.12),
                     scale(UP, 1.06), wobble=1.0)
# a dome: toward its edge the surface tips and gives back more of the cloud
for i, (cx, cy, r, push) in enumerate(BOILS.b):
    for j in range(int(r * 0.25)):
        a0 = rng.uniform(0, 2 * np.pi)
        t = np.linspace(a0, a0 + rng.uniform(0.6, 1.6), 16)
        ring = np.array([cx, cy]) + (BOILS.edge_at(i, t) - [cx, cy]) * rng.uniform(0.8, 0.97)
        board.stroke(ring, boil_top.but(width=r * rng.uniform(0.12, 0.3), opacity=0.1, taper=(0.4, 0.4)),
                     mix((UP, 2), (CLOUD, 1)), wobble=1.0)
    # rings going out across it, each one a crest that catches the cloud and a trough that does not
    for f in np.sort(rng.uniform(0.45, 0.93, int(rng.integers(2, 4)))):
        for _ in range(int(rng.integers(1, 4))):
            a0 = rng.uniform(0, 2 * np.pi)
            t = np.linspace(a0, a0 + rng.uniform(0.3, 1.0), 22)
            wig = (f + 0.035 * np.sin(t * rng.uniform(6, 11) + rng.uniform(0, 6)))[:, None]
            ring = np.array([cx, cy]) + (BOILS.edge_at(i, t) - [cx, cy]) * wig
            board.stroke(ring, boil_top.but(width=rng.uniform(2.0, 4.0), opacity=0.1 + 0.15 * f, taper=(0.45, 0.45)),
                         mix((UP, 1), (CLOUD, 1.4)), wobble=0.6)
            inner = np.array([cx, cy]) + (ring - [cx, cy]) * (1 - 5.0 / r)
            board.stroke(inner, crease.but(width=rng.uniform(3, 5), opacity=0.12), mix((payne, 1), (UP, 1)), wobble=0.6)
board.untape()
# what came up stays glassy a while as it is carried off
for i, (cx, cy, r, push) in enumerate(BOILS.b):
    for k in range(int(r * 0.35)):
        a = rng.uniform(0.15, np.pi - 0.15)
        p = BOILS.edge_at(i, np.array([a]))[0] * 0.92 + np.array([cx, cy]) * 0.08
        line = streamline(swirl_vel, p[0], p[1], r * rng.uniform(1.5, 4.0), step=6, both=False)
        if len(line) < 4:
            continue
        board.stroke(line, boil_top.but(width=rng.uniform(20, 46), opacity=0.13, taper=(0.05, 0.6)),
                     scale(UP, rng.uniform(1.0, 1.12)), pressure=lambda t: 1.0 - 0.8 * t, wobble=1.5)
board.stage("the boils come up")

# =================================================================================================
# 5. The sky on the broken water. The wavelets' faces that tip toward the cloud are lighter, their
#    backs, toward the dark under the bridge, darker; both lie across the current, in trains.
# =================================================================================================
board.dry()
XX, YY = np.meshgrid(np.arange(W) + 0.5, np.arange(H) + 0.5)
ROUGH = roughness(XX, YY)
CLUMP = ground.fbm(W, H, rng0, base=9, octaves=3)
CLUMP = smoothstep(0.35, 0.75, CLUMP)
TRAIN = 0.5 + 0.5 * np.sin((YY + 25 * np.sin(XX / 140) + 18 * CLUMP * 6) / 46 * 2 * np.pi - XX * 0.21 / 46 * 2 * np.pi)
LIVE = np.clip(ROUGH * (0.45 + 0.35 * CLUMP + 0.3 * TRAIN) + 0.2 * BOILS.rim(XX, YY, 0.09) * (BOILS.inside(XX, YY) < 0.5), 0, 1)
board.tape_where(ROUGH, feather=2.0)


def live(x, y):
    return LIVE[int(np.clip(y, 0, H - 1)), int(np.clip(x, 0, W - 1))]


def across(x, y):
    vx, vy = vel(x, y)
    return np.arctan2(vy, vx) + np.pi / 2


sheen = Brush(width=10, bristle=1.6, opacity=0.14, pickup=0.0, jitter=0.03, gap=0.1, taper=(0.35, 0.35),
              thickness=0.15, wander=0.8)
for x, y in scatter(rng, W, H, 2400, where=lambda x, y: rng.random() < live(x, y) ** 1.2, pad=0):
    lv = live(x, y)
    board.dab(x, y, sheen.but(width=rng.uniform(6, 16), opacity=0.06 + 0.14 * lv),
              scale(CLOUD, rng.uniform(0.85, 1.05)), angle=across(x, y) + rng.normal(0, 0.25),
              length=rng.uniform(30, 80), wobble=1.5)
backs = Brush(width=4, bristle=1.0, opacity=0.3, glaze=True, jitter=0.02, gap=0.1, taper=(0.35, 0.35), wander=0.4)
fleck = Brush(width=3, bristle=0.9, opacity=0.75, pickup=0.0, jitter=0.03, gap=0.0, taper=(0.4, 0.4),
              thickness=0.9, wander=0.3)
SHADE = mix((payne, 1.2), (MILK, 1))


def scale_mark(x, y, a, L, bow):
    """One wavelet seen from above: a little crescent bowed upstream."""
    ca, sa = np.cos(a), np.sin(a)
    nx_, ny_ = -sa, ca                        # points downstream
    return np.array([(x - ca * L / 2, y - sa * L / 2), (x - nx_ * bow, y - ny_ * bow),
                     (x + ca * L / 2, y + sa * L / 2)])


for x, y in scatter(rng, W, H, 30000, where=lambda x, y: rng.random() < live(x, y) ** 1.3, pad=0):
    lv = live(x, y)
    a = across(x, y) + rng.normal(0, 0.28)
    L = rng.uniform(4, 15) * (0.7 + 0.6 * lv)
    bow = L * rng.uniform(0.0, 0.14)
    nx_, ny_ = -np.sin(a), np.cos(a)
    board.stroke(scale_mark(x + nx_ * 2.5, y + ny_ * 2.5, a, L * 1.1, bow),
                 backs.but(width=rng.uniform(2.0, 4.0), opacity=0.06 + 0.2 * lv), SHADE)
    if rng.random() < 0.35 + 0.55 * lv:
        board.stroke(scale_mark(x, y, a, L, bow), fleck.but(width=rng.uniform(1.4, 3.2), opacity=0.15 + 0.55 * lv),
                     scale(CLOUD, rng.uniform(0.92, 1.12)))
board.untape()
board.stage("the sky on the broken water")

# =================================================================================================
# 6. Foam: rings on the boils' creases, drawn out downstream, and the seam over the lip.
# =================================================================================================
board.dry()
fb = Brush(width=4, bristle=1.0, opacity=0.9, pickup=0.0, jitter=0.02, gap=0.0, taper=(0.3, 0.3), thickness=1.8)
FOAM = mix((white, 8), (ochre, 0.35), (payne, 0.2))


def foam_col(x, y):
    return scale(FOAM, rng.uniform(0.72, 1.0))


# foam is carried in lines: it gathers where water goes down, on the upstream crease of each boil
# and along the shear, and is drawn out by the current round the boils and on downstream
starts = []
for i, (cx, cy, r, push) in enumerate(BOILS.b):
    # held on the crease along the upstream side, in clumps
    a0 = -np.pi / 2 + rng.normal(0, 0.3)
    for _ in range(int(rng.integers(2, 4))):
        a1 = a0 + rng.uniform(-1.6, 1.0)
        t = np.linspace(a1, a1 + rng.uniform(0.4, 1.1), 40)
        crest = np.array([cx, cy]) + (BOILS.edge_at(i, t) - [cx, cy]) * rng.uniform(1.0, 1.04)
        foam_lace(board, crest, fb, foam_col, rng, width=rng.uniform(2, 6), strands=int(rng.integers(2, 4)),
                  every=(1, 4), size=(1.3, 4.0))
    # and torn off the sides and carried down
    for a in (rng.normal(0.15, 0.25), rng.normal(np.pi - 0.15, 0.25)):
        starts.append(BOILS.edge_at(i, np.array([a]))[0] + rng.normal(0, 3, 2))
for y0 in np.linspace(-80, H - 500, 9):
    starts.append(np.array([edge(y0) + rng.normal(60, 40), y0 + rng.normal(0, 30)]))
starts.append(np.array([DRIFT[0][0] - 10, DRIFT[0][1] - 30]))
for p in starts:
    line = streamline(swirl_vel, p[0], p[1], rng.uniform(200, 900) * (1 - 0.6 * np.clip(p[1] / H, 0, 1)), step=4, both=False,
                      stop=lambda x, y: BOILS.inside(np.array(x), np.array(y)) > 0.5)
    # it comes and goes: break each line into runs
    k = 0
    while k < len(line):
        run = int(rng.integers(8, 60))
        if rng.random() < 0.7:
            seg = line[k:k + run]
            if len(seg) > 3:
                board.stroke(seg, Brush(width=rng.uniform(5, 14), bristle=1.4, opacity=0.2, pickup=0.0, gap=0.3,
                                        jitter=0.03, taper=(0.4, 0.4), thickness=0.3), FOAM, wobble=1.5)
            if rng.random() < 0.3 and len(seg) > 2:
                q = seg[len(seg) // 2]
                for _ in range(int(rng.integers(6, 20))):
                    z = q + rng.normal(0, 5, 2)
                    board.dab(z[0], z[1], fb.but(width=rng.uniform(2.5, 6.5)), foam_col(*z), length=rng.uniform(2, 6))
            foam_lace(board, line[k:k + run], fb, foam_col, rng, width=rng.uniform(3, 14),
                      strands=int(rng.integers(2, 6)), every=(1, 5), size=(1.3, 4.5))
        k += run + int(rng.integers(0, 25))
board.stage("foam on the creases and the seam")

# =================================================================================================
# 7. What floats, in body colour: the dry part of the branch, its twigs and the last leaves on it,
#    and the foam that has gathered on its upstream side.
# =================================================================================================
board.dry()
barkb = Brush(width=22, bristle=1.3, opacity=0.97, pickup=0.3, jitter=0.05, gap=0.0, taper=(0.15, 0.0),
              thickness=1.6, wander=0.4)
tt = np.linspace(0.0, UNDER_FROM + 0.02, 30)
pts = along_branch(tt)
board.stroke(pts, barkb, [scale(mix((bark, 3), (white, 0.2)), 0.9 + 0.1 * u) for u in np.linspace(0, 1, 8)],
             pressure=lambda t: 0.65 + 0.35 * t)
d = np.gradient(pts, axis=0)
nrm = np.column_stack([-d[:, 1], d[:, 0]]) / (np.hypot(d[:, 0], d[:, 1])[:, None] + 1e-9)
# under cloud the round top of the stick is lit all along its length, and wet
board.stroke(pts[1:-2] - nrm[1:-2] * 1.5, barkb.but(width=4, opacity=0.7, thickness=0.6, taper=(0.3, 0.3)),
             mix((bark, 1), (CLOUD, 1.6)))
board.stroke(pts[1:-1] + nrm[1:-1] * 5, barkb.but(width=3.5, opacity=0.6, thickness=0.3, taper=(0.3, 0.3)),
             mix((payne, 2), (umber, 1)))
twig = barkb.but(width=7, taper=(0.0, 0.7), thickness=1.0)
for t0, side, L in TWIGS:
    p0 = along_branch(t0)
    k = int(t0 / (UNDER_FROM + 0.02) * (len(pts) - 1))
    tang = d[k] / (np.hypot(*d[k]) + 1e-9)
    dirv = -tang * 0.55 + nrm[k] * side
    dirv /= np.linalg.norm(dirv)
    bend = np.array([-dirv[1], dirv[0]]) * rng.normal(0, 0.18) * L
    p1 = p0 + dirv * L * 0.5 + bend
    p2 = p0 + dirv * L + bend * 0.3 + rng.normal(0, 4, 2)
    board.stroke([p0, p1, p2], twig, mix((bark, 3), (sienna, 0.6)), wobble=1.0)
    board.stroke([p1, p1 + (p2 - p0) * 0.35 + bend * 0.8], twig.but(width=3.5), mix((bark, 3), (sienna, 0.6)))
DEAD = [mix((sienna, 2), (umber, 1), (ochre, 0.6)), mix((umber, 2), (sienna, 1)), mix((ochre, 1), (sienna, 1), (umber, 1))]
lb = Brush(width=7, bristle=1.0, opacity=0.95, pickup=0.4, jitter=0.06, gap=0.0, taper=(0.1, 0.2), thickness=1.4)
for t0, side, sz, up in LEAVES:
    p0 = along_branch(t0)
    k = int(t0 / (UNDER_FROM + 0.02) * (len(pts) - 1))
    tang = d[k] / (np.hypot(*d[k]) + 1e-9)
    v = nrm[k] * side * (1 - up) - tang * (0.6 + up)
    ang = np.arctan2(v[1], v[0]) + rng.normal(0, 0.3)
    Lf, Wf = 60 * sz, 36 * sz
    c = p0 + np.array([np.cos(ang), np.sin(ang)]) * Lf * 0.55
    lo = leaf_outline(*c, Lf, Wf, ang, rng)
    board.tape(lo, feather=0.7)
    col = DEAD[int(rng.integers(0, 3))]
    board.fill(lo, lb.but(width=6), col, angle=ang + 0.5, spacing=2.5,
               color_fn=lambda m, col=col: scale(col, rng.uniform(0.82, 1.08)))
    ca, sa = np.cos(ang), np.sin(ang)
    # dead leaves curl along the midrib: one half turns down and goes dark
    turn = rng.choice([-1, 1])
    board.tape_where(lambda X, Y: ((X - c[0]) * -sa + (Y - c[1]) * ca) * turn > 0, mode="and", feather=1.5)
    board.fill(lo, lb.but(glaze=True, opacity=0.25, width=14, jitter=0.01), mix((umber, 1), (payne, 1), (white, 0.6)), angle=ang, spacing=3)
    board.untape()
    board.stroke([c - np.array([ca, sa]) * Lf / 2, c + np.array([ca, sa]) * Lf / 2],
                 lb.but(width=1.6, opacity=0.6, taper=(0.0, 0.6)), mix((col, 1), (CLOUD, 1)))
# foam held against the upstream side, and piled where the stick goes under
for k in range(0, len(pts) - 2, 2):
    side = 1 if (nrm[k] @ np.array([0.0, -1.0])) > 0 else -1
    q = pts[k] + nrm[k] * side * rng.uniform(8, 14)
    for _ in range(int(rng.integers(1, 4))):
        z = q + rng.normal(0, 2.5, 2)
        board.dab(z[0], z[1], fb.but(width=rng.uniform(1.6, 4.0)), foam_col(*z), length=rng.uniform(1.5, 4))
wet = along_branch(UNDER_FROM)
for _ in range(30):
    z = wet + rng.normal(0, 9, 2)
    board.dab(z[0], z[1], fb.but(width=rng.uniform(1.5, 3.8)), foam_col(*z), length=rng.uniform(1.5, 4))
board.stage("what floats: the branch")

finish(board, HERE, title="Soča at Kobarid, 4 November 1983, 112 cm", artist="zala-hrovat", year=1983,
       medium="Oil on gessoed birch ply", made="2026-11-12")
