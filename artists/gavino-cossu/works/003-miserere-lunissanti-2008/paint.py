"""Gavino Cossu - Miserere, first verse, Lunissanti 2008

The same verse as his first panel, eleven years on: the last Holy Monday he sang contra, when the
mill had taken enough of his right ear that he could no longer tune to the other three. Painted
from his own place in the four, so the chord fills the board and the silence is only what is left
between the voices. They sang it loud from the first station. His own line goes flat and is pulled
back, again and again; the quintina sounded only where he happened to be on the note.
"""
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[3]))
sys.path.insert(0, str(HERE.parents[1]))

from engine import Board, Brush, hexc  # noqa: E402
from engine.studio import finish  # noqa: E402
from tools import (OffTrue, Verse, breath_dry, breath_path, cork_board, deplete_for, field, in_tune,  # noqa: E402
                   sag, slide_thin, smooth01, vowel_run)

W, H = 1800, 1050
rng0 = np.random.default_rng(2008)
GESSO = hexc("#ece4d2")
board = Board(W, H, GESSO, cork_board(W, H, rng0), seed=2008)
board.dries_off_board = False
board.relief_soft = 2.0
rng = board.rng
Y, X = np.mgrid[0:H, 0:W].astype(np.float64) + 0.5

# --- the verse, as in 1997 -----------------------------------------------------------------------
# the bassu and his own contra hold; from inside, the floor of it does not move and the tune goes on
# above. Under every slide of the boghe he is meant to stay exactly where he is.
I0, V, I, IV, VI, II = (0, 7, 12, 16), (0, 7, 10, 14), (0, 7, 12, 17), (0, 5, 9, 14), (0, 7, 9, 12), (0, 7, 14, 17)
SYL = [
    ("Mi", "i", 1.0, I0), ("se", "e", 1.0, I0), ("re", "e", 1.5, V), ("re", "e", 2.5, (0, 7, 12, 17)),
    ("me", "e", 1.0, I), ("i", "i", 2.5, I0),
    ("De", "e", 1.5, V), ("us", "u", 3.0, I0),
    ("se", "e", 1.0, IV), ("cun", "u", 1.0, V), ("dum", "u", 2.0, I0),
    ("ma", "a", 1.5, I), ("gnam", "a", 2.5, II),
    ("mi", "i", 1.0, I0), ("se", "e", 1.0, IV), ("ri", "i", 1.0, V), ("cor", "o", 2.0, VI),
    ("di", "i", 1.0, V), ("am", "a", 2.0, I0),
    ("tu", "u", 1.5, V), ("am", "a", 5.5, I0),
]
verse = Verse(SYL, ["bassu", "contra", "contraltu", "boghe"])
CONTRA = 1

# from inside the four: the chord is as tall as the board
X0, X1 = 60.0, 1580.0
BX = (X1 - X0) / verse.total
Y_ROOT, PX_SEMI = 880.0, 38.0
Q_SEMI = 21.4


def x_of(beat):
    return X0 + np.asarray(beat) * BX


def y_of(semi):
    return Y_ROOT - np.asarray(semi) * PX_SEMI


BREATHS = {0: [7, 12, 18], 1: [5, 10, 16], 2: [7, 13, 18], 3: [3, 7, 12, 18]}
ENTER = {0: 0, 1: 0, 2: 0, 3: 0}          # loud from the first syllable: all four come in together
LAG = [0.5, 0.25, 0.12, 0.0]
GLIDE = 0.7
PAL = {
    "i": hexc("#94a08c"),
    "e": hexc("#b88c3c"),
    "a": hexc("#a4472b"),
    "o": hexc("#3e4e8a"),
    "u": hexc("#4a3650"),
}
SHADE = [0.17, 0.4, 0.66, 1.0]
WID = [150, 66, 88, 80]

# --- the day, worked out before anything goes on -------------------------------------------------
# morning to dark: his line goes flat faster as the day goes on and he catches it less often
# he pulls back up to the bassu each time he breathes, and in a long breath when he feels it
DAY = [("morning, the first stations", 3, 0.09, 6.0, 0.3),
       ("afternoon", 3, 0.13, 5.5, 0.0),
       ("evening, the torches", 3, 0.17, 5.0, -0.2)]
TAKES = []
for name, n, rate, every, drift in DAY:
    for _ in range(n):
        t = verse.sung(rng, rubato=0.035, drift=drift + rng.normal(0, 0.15))
        at = [t.start[0] + 0.1] + [t.end[k] + 0.15 for k in BREATHS[CONTRA]]
        fn, _ = sag(verse.total, rng, rate * rng.uniform(0.8, 1.2), every, at=at)
        TAKES.append((name, OffTrue(t, {CONTRA: fn})))


def held(take):
    """The quintina only comes on a held chord, never on a passing syllable or a slide."""
    def keep(b):
        k = take.syl_at(b)
        return take.v.beats[k] >= 2.0 and b - take.start[k] > 0.5
    return keep


SPANS = []
for name, take in TAKES:
    for a, b in in_tune(take, CONTRA, tol=0.12, min_beats=0.9, keep=held(take)):
        SPANS.append((a, b))


def q_shape(x0, x1, y, thick, peak=0.35):
    u = np.clip((X - x0) / max(x1 - x0, 1.0), 0, 1)
    p, q = 2.0 * peak, 2.0 * (1 - peak)
    env = (u ** p * (1 - u) ** q) / (peak ** p * (1 - peak) ** q)
    yy = y + 2 * np.sin(X / 31.0) * env
    return env * np.exp(-((Y - yy) / np.maximum(thick * env ** 0.7, 1.5)) ** 2)


QY = float(y_of(Q_SEMI))
QUIN = np.zeros((H, W))
NEAR = np.zeros((H, W))
LAST = verse.start[-1]
for a, b in SPANS:
    # on the last "am" the church keeps it and it runs on off the board; anywhere else it was gone
    # almost as soon as he heard it
    last = a >= LAST
    x0, x1 = float(x_of(a)), float(x_of(b + (14.0 if last else 1.6)))
    s_ = 1.0 if last else 0.8
    QUIN = np.maximum(QUIN, s_ * q_shape(x0, x1, QY, 15 if last else 6, peak=0.3 if last else 0.4))
    NEAR = np.maximum(NEAR, s_ * q_shape(x0 - 70, x1 + 110, QY, 40, peak=0.25 if last else 0.4) ** 0.8)
print(f"quintina: {len(SPANS)} spans", [(round(a, 1), round(b, 1)) for a, b in SPANS])

board.stage("gesso on cork")

# --- the silence ---------------------------------------------------------------------------------
board.tape_where(QUIN > 0.5, outside=True, feather=5)
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
board.dry(0.95)
board.stage("the silence")

# --- the singing ---------------------------------------------------------------------------------
def dyn(beat):
    """Loud from the first syllable; louder still at "magnam" and on the last "am"."""
    b = np.asarray(beat) / verse.total
    return 0.85 + 0.1 * smooth01((b - 0.45) / 0.15) + 0.1 * smooth01((b - 0.8) / 0.15)


def breath_pressure(t):
    t = np.clip(t, 0, 1)
    return 0.85 + 0.3 * np.exp(-t / 0.03) + 0.15 * np.sin(np.pi * t) ** 0.6 - 0.25 * t ** 3


def voice_brush(v, **kw):
    b = Brush(width=WID[v], bristle=2.0, opacity=0.75, thickness=1.2, dryness=0.15, jitter=0.12,
              gap=0.1, pickup=0.25, taper=(0.02, 0.14), wander=1.2, angle=0.0)
    return b.but(**kw)


def sing(take, load=1.0, x_jit=0.0, w_k=1.0, gain=1.0, base_dry=0.15, **kw):
    for v in range(4):
        cuts = [take.end[k] for k in BREATHS[v]] + [verse.total + 0.6]
        b0 = take.start[ENTER[v]] + abs(rng.normal(0, 0.08))
        lag = LAG[v] + rng.normal(0, 0.05)
        for c in cuts:
            b1 = c - (0.4 if c < verse.total else 0.0) + rng.normal(0, 0.05)
            pts = breath_path(take, v, b0, b1, lambda b: x_of(b) + x_jit, y_of, lag=lag, glide=GLIDE)
            br = voice_brush(v, width=WID[v] * w_k * np.exp(rng.normal(0, 0.06)), load=load, **kw)
            length = float(np.hypot(*np.diff(pts, axis=0).T).sum())
            br = br.but(deplete=deplete_for(length, br, end_load=rng.uniform(0.15, 0.3)))
            col = vowel_run(take, (b0, b1), PAL, SHADE[v] * gain * np.exp(rng.normal(0, 0.05)), lag=lag,
                            blend=1.2 if v == 0 else 0.5)
            pr = lambda t, a=b0, z=b1: breath_pressure(t) * dyn(a + (z - a) * np.asarray(t))
            sl = slide_thin(pts, steep=0.6, floor=0.0)
            # the bassu is the rough one, felt in the back more than heard: drier even when loud
            dr = breath_dry(base_dry + (0.3 if v == 0 else 0.0))
            board.stroke(pts, br, col, pressure=pr, opacity=sl, dryness=lambda t: max(dr(t), 0.95 * (1 - sl(t))),
                         wobble=1.0)
            b0 = c + 0.05 + abs(rng.normal(0, 0.05))


board.untape()
board.tape_where(QUIN > 0.3, outside=True, feather=4)

for i, (name, take) in enumerate(TAKES[:-1]):
    sing(take, load=0.9, x_jit=rng.normal(0, 3), w_k=1.0, gain=0.85)
    if i + 1 == len(TAKES) - 1 or TAKES[i + 1][0] != name:
        board.dry(0.6)
        board.stage(name)

# what the nave keeps of a loud verse: the end of each line held on into the dark, and the last
# chord dragged off the edge of the board
echo = Brush(width=60, bristle=2.0, opacity=0.3, dryness=0.7, thickness=0.2, jitter=0.1, gap=0.2,
             pickup=0.0, taper=(0.15, 0.5), wander=1.4, angle=0.0)
ref = verse.sung(rng, rubato=0.0)
for v in range(4):
    for k in (7, 12, 20):
        last = k == len(SYL) - 1
        b0 = ref.end[k] - 0.4 * ref.beats[k] + LAG[v]
        b1 = ref.end[k] + (9.0 if last else 1.8) + LAG[v]
        pts = breath_path(ref, v, b0, min(b1, verse.total), x_of, y_of, lag=LAG[v], glide=GLIDE)
        if b1 > verse.total:
            pts = np.vstack([pts, pts[-1] + (BX * (b1 - verse.total), rng.normal(0, 4))])
        col = vowel_run(ref, (b0, b0 + 0.01), PAL, SHADE[v] * 0.8, lag=LAG[v])
        for _ in range(2 if last else 1):
            board.stroke(pts + (0, rng.normal(0, 6)), echo.but(width=WID[v] * rng.uniform(0.9, 1.2)), col,
                         wobble=2, pressure=lambda t: 1.0 - 0.75 * t, dryness=lambda t: 0.55 + 0.4 * t)
board.dry(1.0)
board.stage("the church keeping it")

# the last time, at the church door: the one he remembers best goes on top
name, take = TAKES[-1]
sing(take, load=1.1, w_k=0.85, opacity=0.9, thickness=1.8, base_dry=0.08)
board.stage("the last time, at the door")

finish(board, HERE, title="Miserere, first verse, Lunissanti 2008", year=2013,
       medium="Oil on agglomerated cork, gessoed", artist="gavino-cossu")
