"""Gavino Cossu - Stabat Mater, first verse, Venerdì Santo 2003

The first verse of the Stabat Mater as the second cuncordu sang it on Good Friday 2003, the year
their contra was ill and he stood in. Quieter and slower than his own choir's Miserere: four
threads laid across the dark, dry where the singing was soft, so the cork comes through. Time runs
left to right, pitch up. One stroke per breath. The quintina is the gesso he never painted.
"""
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[3]))
sys.path.insert(0, str(HERE.parents[1]))

from engine import Board, Brush, hexc  # noqa: E402
from engine.studio import finish  # noqa: E402
from tools import Verse, breath_path, cork_board, deplete_for, field, quiet, smooth01, vowel_run  # noqa: E402

W, H = 1800, 1050
rng0 = np.random.default_rng(2003)
GESSO = hexc("#ece4d2")
board = Board(W, H, GESSO, cork_board(W, H, rng0), seed=2003)
rng = board.rng
Y, X = np.mgrid[0:H, 0:W].astype(np.float64) + 0.5

# --- the verse ----------------------------------------------------------------------------------
# what each voice holds, low to high. The bassu sits on one note a line, the contra nearly as still;
# the boghe has the tune and the contraltu answers it.
SYL = [
    ("Sta", "a", 2.0, (0, 7, 12, 15)), ("bat", "a", 1.5, (0, 7, 12, 15)), ("Ma", "a", 2.0, (0, 7, 12, 15)),
    ("ter", "e", 2.5, (0, 7, 10, 14)), ("do", "o", 1.5, (0, 7, 12, 17)), ("lo", "o", 1.5, (0, 7, 12, 17)),
    ("ro", "o", 2.0, (0, 7, 10, 14)), ("sa", "a", 4.0, (0, 7, 12, 15)),
    ("iux", "u", 2.0, (-2, 5, 10, 14)), ("ta", "a", 1.5, (-2, 5, 10, 14)), ("cru", "u", 2.0, (-2, 5, 10, 17)),
    ("cem", "e", 2.5, (-2, 5, 10, 17)), ("la", "a", 1.5, (-2, 5, 12, 15)), ("cri", "i", 1.5, (-2, 5, 8, 12)),
    ("mo", "o", 2.0, (-2, 5, 7, 11)), ("sa", "a", 4.0, (0, 7, 12, 15)),
    ("dum", "u", 2.0, (-4, 3, 8, 12)), ("pen", "e", 1.5, (-4, 3, 8, 12)), ("de", "e", 1.5, (-4, 5, 10, 14)),
    ("bat", "a", 2.5, (-4, 5, 10, 14)), ("Fi", "i", 2.0, (-5, 3, 8, 12)), ("li", "i", 2.0, (-5, 2, 7, 11)),
    ("us", "u", 6.0, (0, 7, 12, 15)),
]
verse = Verse(SYL, ["bassu", "contra", "contraltu", "boghe"])

X0, X1 = 90.0, 1560.0
BX = (X1 - X0) / verse.total
Y_ROOT, PX_SEMI = 770.0, 17.0


def x_of(beat):
    return X0 + np.asarray(beat) * BX


def y_of(semi):
    return Y_ROOT - np.asarray(semi) * PX_SEMI


BREATHS = {0: [7, 15], 1: [3, 11, 19], 2: [7, 15], 3: [3, 7, 11, 15, 19]}
ENTER = {0: 1, 1: 1, 2: 1, 3: 0}
LAG = [1.6, 0.9, 0.4, 0.0]
GLIDE = 1.6

PAL = {
    "i": hexc("#94a08c"),
    "e": hexc("#b88c3c"),
    "a": hexc("#a4472b"),
    "o": hexc("#3e4e8a"),
    "u": hexc("#4a3650"),
}
SHADE = [0.3, 0.45, 0.68, 1.0]

# --- the quintina, worked out first --------------------------------------------------------------
def q_shape(x0, x1, y, thick, peak=0.4):
    u = np.clip((X - x0) / (x1 - x0), 0, 1)
    p, q = 2.0 * peak, 2.0 * (1 - peak)
    env = (u ** p * (1 - u) ** q) / (peak ** p * (1 - peak) ** q)
    yy = y + 3 * np.sin(X / 29.0) * env
    return env * np.exp(-((Y - yy) / np.maximum(thick * env ** 0.7, 1.5)) ** 2)


QS = [  # (start beat, end beat, semitone, thickness, strength)
    (verse.start[15] + 1.4, verse.start[15] + 5.5, 27, 5.5, 0.8),
    (verse.start[22] + 0.8, verse.total + 11.0, 27, 10, 1.0),
]
QUIN = np.max([s * q_shape(x_of(a), x_of(b), y_of(m), t, peak=0.3) for a, b, m, t, s in QS], axis=0)
NEAR = np.max([s * q_shape(x_of(a) - 110, x_of(b) + 140, y_of(m), t * 6, peak=0.3) for a, b, m, t, s in QS],
              axis=0) ** 0.8

board.stage("gesso on cork")

# --- the silence ---------------------------------------------------------------------------------
board.tape_where(QUIN > 0.5, outside=True, feather=7)
ink = [hexc("#1d150e"), hexc("#16130f"), hexc("#141317"), hexc("#121219")]
sil = Brush(width=110, bristle=2.2, opacity=0.99, dryness=0.1, thickness=0.08, jitter=0.05, gap=0.05,
            deplete=0.0003, pickup=0.0, wander=1.4, taper=(0.02, 0.04), angle=0.0)
for layer in range(4):
    thin = np.clip(1.0 - NEAR * (0.5 + 0.35 * layer) * 1.6, 0, 1) ** 2
    y = -40.0 + rng.uniform(0, 30)
    while y < H + 50:
        x = -60.0 + rng.uniform(-30, 0)
        while x < W + 40:
            L = W + 140.0
            pts = np.array([(x, y), (x + L * 0.5, y + rng.normal(0, 4)), (x + L, y + rng.normal(0, 7))])
            board.stroke(pts, sil.but(dryness=(0.1, 0.15, 0.25, 0.55)[layer]), ink[layer], pressure=thin, wobble=2)
            x += L * rng.uniform(0.7, 0.95)
        y += rng.uniform(36, 50)
# a last dry coat of umber, dragged so it only takes on the granules: heaviest in the empty church
# before the first note, wearing off as the singing goes on
board.dry(0.95)
scum = field(W, H, lambda X, Y: (0.5 - 0.36 * smooth01((X - 150) / 1300)) * np.clip(1 - NEAR * 2.2, 0, 1))
for _ in range(1):
    y = -30.0 + rng.uniform(0, 40)
    while y < H + 50:
        pts = np.array([(-80, y), (W / 2, y + rng.normal(0, 5)), (W + 80, y + rng.normal(0, 8))])
        board.stroke(pts, sil.but(dryness=0.92, opacity=0.5, width=130), hexc("#251b14"), pressure=scum, wobble=2)
        y += rng.uniform(60, 90)
board.dry(0.95)
board.stage("the silence")

# --- the singing ---------------------------------------------------------------------------------
def dyn(beat):
    """Quiet throughout; it opens a little at "lacrimosa" and holds there."""
    b = np.asarray(beat) / verse.total
    return 0.32 + 0.35 * smooth01((b - 0.1) / 0.55) + 0.2 * smooth01((b - 0.72) / 0.25)


def breath_pressure(t):
    t = np.clip(t, 0, 1)
    return 0.8 + 0.25 * np.exp(-t / 0.04) + 0.15 * np.sin(np.pi * t) ** 0.6 - 0.3 * t ** 3


WID = [46, 34, 30, 28]


def voice_brush(v, **kw):
    b = Brush(width=WID[v], bristle=1.5, opacity=0.7, thickness=0.7, dryness=0.5, jitter=0.12,
              gap=0.12, pickup=0.12, taper=(0.02, 0.18), wander=1.0, angle=0.0)
    return b.but(**kw)


def sing(take, load=1.0, x_jit=0.0, w_k=1.0, gain=1.0, **kw):
    for v in range(4):
        cuts = [take.end[k] for k in BREATHS[v]] + [verse.total + 0.8]
        b0 = take.start[ENTER[v]] + abs(rng.normal(0, 0.1))
        lag = LAG[v] + rng.normal(0, 0.08)
        for c in cuts:
            b1 = c - (0.45 if c < verse.total else 0.0) + rng.normal(0, 0.06)
            pts = breath_path(take, v, b0, b1, lambda b: x_of(b) + x_jit, y_of, lag=lag, glide=GLIDE)
            br = voice_brush(v, width=WID[v] * w_k * np.exp(rng.normal(0, 0.08)), load=load, **kw)
            length = float(np.hypot(*np.diff(pts, axis=0).T).sum())
            br = br.but(deplete=deplete_for(length, br, end_load=rng.uniform(0.08, 0.18)))
            col = vowel_run(take, (b0, b1), PAL, SHADE[v] * gain * np.exp(rng.normal(0, 0.06)), lag=lag,
                            blend=0.8, gain=lambda bt: 0.45 + 0.6 * dyn(bt))
            # quiet singing is less paint, not only darker paint: the brush barely touches
            op = quiet(dyn, b0, b1)
            pr = lambda t, a=b0, z=b1: breath_pressure(t) * dyn(a + (z - a) * np.asarray(t)) * 1.3
            board.stroke(pts, br, col, pressure=pr, opacity=op, wobble=1.2)
            b0 = c + 0.05 + abs(rng.normal(0, 0.05))


board.untape()
board.tape_where(QUIN > 0.3, outside=True, feather=6)

DAY = [("the morning stations, thin", 3, 0.7, 0.3, 0.9, 0.75),
       ("afternoon, flat", 3, 0.8, -0.4, 0.95, 0.8)]
for name, n, load, drift, wk, g in DAY:
    for _ in range(n):
        take = verse.sung(rng, rubato=0.05, drift=drift + rng.normal(0, 0.25))
        sing(take, load=load, x_jit=rng.normal(0, 6), w_k=wk, gain=g, dryness=0.85)
    board.dry(0.6)
    board.stage(name)

# what the nave keeps: the chord held at the end of each line, drawn on into the dark
echo = Brush(width=50, bristle=2.0, opacity=0.14, dryness=0.75, thickness=0.1, jitter=0.1, gap=0.2,
             pickup=0.0, taper=(0.2, 0.5), wander=1.4, angle=0.0)
ref = verse.sung(rng, rubato=0.0)
for v in range(4):
    for k in (7, 15, 22):
        last = k == len(SYL) - 1
        b0 = ref.end[k] - 0.25 * ref.beats[k] + LAG[v]
        b1 = ref.end[k] + (7.0 if last else 2.2) + LAG[v]
        pts = breath_path(ref, v, b0, min(b1, verse.total), x_of, y_of, lag=LAG[v], glide=GLIDE)
        if b1 > verse.total:
            pts = np.vstack([pts, pts[-1] + (BX * (b1 - verse.total), rng.normal(0, 4))])
        col = vowel_run(ref, (b0, b0 + 0.01), PAL, SHADE[v] * 0.8, lag=LAG[v])
        board.stroke(pts, echo.but(width=WID[v] * rng.uniform(1.0, 1.5)), col, wobble=2,
                     pressure=lambda t: 1.0 - 0.7 * t)
board.dry(1.0)
board.stage("the church keeping it")

take = verse.sung(rng, rubato=0.03, drift=0.0)
sing(take, load=1.1, w_k=0.8, opacity=0.9, thickness=1.6, dryness=0.55, pickup=0.08)
board.stage("the last time, at the Calvary")

finish(board, HERE, title="Stabat Mater, first verse, Venerdì Santo 2003", year=2012,
       medium="Oil on agglomerated cork, gessoed", artist="gavino-cossu")
