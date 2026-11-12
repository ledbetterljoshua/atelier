"""Gavino Cossu - Miserere, first verse, Lunissanti 1997

The first verse of the Miserere as the cuncordu sang it on Holy Monday 1997, from first light to
the last station after dark, every time they sang it laid over the last. Time runs left to right,
pitch up the board. One stroke for each breath a singer took. The quintina, the fifth voice that
nobody sings, is the gesso he never painted.
"""
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[3]))
sys.path.insert(0, str(HERE.parents[1]))

from engine import Board, Brush, hexc  # noqa: E402
from engine.studio import finish  # noqa: E402
from tools import Verse, along, breath_path, cork_board, deplete_for, smooth01, vowel_run  # noqa: E402

W, H = 1800, 1050
rng0 = np.random.default_rng(1997)
GESSO = hexc("#ece4d2")
board = Board(W, H, GESSO, cork_board(W, H, rng0), seed=1997)
rng = board.rng

# --- the verse ----------------------------------------------------------------------------------
I0, V, I, IV, VI, II = (0, 7, 12, 16), (-2, 5, 10, 14), (0, 7, 12, 17), (0, 5, 9, 14), (-3, 4, 9, 12), (2, 9, 14, 17)
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
VOICES = ["bassu", "contra", "contraltu", "boghe"]
verse = Verse(SYL, VOICES)

X0, X1 = 120.0, 1500.0
BX = (X1 - X0) / verse.total
Y_ROOT, PX_SEMI = 800.0, 14.0


def x_of(beat):
    return X0 + np.asarray(beat) * BX


def y_of(semi):
    return Y_ROOT - np.asarray(semi) * PX_SEMI


# where each voice breathes: after these syllables
BREATHS = {0: [7, 12, 18], 1: [5, 10, 16], 2: [7, 13, 18], 3: [3, 7, 12, 18]}
ENTER = {0: 1, 1: 1, 2: 1, 3: 0}            # the boghe sets the note alone; the others come in under it

# vowels: his colours for them, the same since he was a boy
PAL = {
    "i": hexc("#94a08c"),
    "e": hexc("#b88c3c"),
    "a": hexc("#a4472b"),
    "o": hexc("#3e4e8a"),
    "u": hexc("#4a3650"),
}
SHADE = [0.2, 0.36, 0.62, 1.0]             # a low "a" is a darker "a"

# --- the quintina: worked out before anything goes on ------------------------------------------
Q_Y = float(y_of(30))
fin0 = verse.start[-1]
QX0, QX1 = float(x_of(fin0 + 0.4)), float(x_of(verse.total + 7.5))
GX0, GX1 = float(x_of(verse.start[7] + 0.7)), float(x_of(verse.start[7] + 3.1))


def q_shape(X, Y, x0, x1, y, thick, peak=0.45):
    """Where the quintina was heard: it comes in thin when the four lock, swells, and hangs on in the
    church after they stop, thinning as it goes."""
    u = np.clip((X - x0) / (x1 - x0), 0, 1)
    p, q = 2.0 * peak, 2.0 * (1 - peak)
    env = (u ** p * (1 - u) ** q) / (peak ** p * (1 - peak) ** q)
    yy = y + 4 * np.sin(X / 23.0) * env
    return env * np.exp(-((Y - yy) / np.maximum(thick * env ** 0.7, 1.5)) ** 2)


def quintina(X, Y):
    core = q_shape(X, Y, QX0, QX1, Q_Y, 15, peak=0.3)
    ghost = 0.8 * q_shape(X, Y, GX0, GX1, float(y_of(29)), 15)
    return np.maximum(core, ghost)


def near_quintina(X, Y):
    """How far the dark thins out round it."""
    a = q_shape(X, Y, QX0 - 140, QX1 + 160, Q_Y, 62, peak=0.3)
    b = 0.9 * q_shape(X, Y, GX0 - 90, GX1 + 140, float(y_of(29)), 60)
    return np.maximum(a, b) ** 0.8


board.stage("gesso on cork")

# --- the silence: laid with time, left to right, before anyone sings -----------------------------
board.tape_where(lambda X, Y: quintina(X, Y) > 0.6, outside=True, feather=9)
ink = [hexc("#15120f"), hexc("#141317"), hexc("#171311"), hexc("#131115")]
sil = Brush(width=120, bristle=2.2, opacity=0.99, dryness=0.08, thickness=0.35, jitter=0.05, gap=0.06,
            deplete=0.0003, pickup=0.0, wander=1.4, taper=(0.02, 0.04))
for layer in range(5):
    y = -50.0 + rng.uniform(0, 30)
    while y < H + 60:
        x = -80.0 + rng.uniform(-300, 0)
        while x < W + 40:
            L = rng.uniform(600, 1300)
            pts = np.array([(x, y), (x + L * 0.5, y + rng.normal(0, 6)), (x + L, y + rng.normal(0, 10))])
            reach = 0.45 + 0.35 * layer      # each coat stops further out from it
            thin = along(pts, lambda X, Y, r=reach: np.clip(1.0 - near_quintina(X, Y) * r * 1.6, 0, 1) ** 2)
            board.stroke(pts, sil.but(dryness=0.08 + 0.06 * layer), ink[rng.integers(4)],
                         pressure=lambda t, f=thin: f(t), wobble=3)
            x += L * rng.uniform(0.55, 0.85)
        y += rng.uniform(34, 50)
board.dry(0.9)
board.stage("the silence")

# --- the singing ---------------------------------------------------------------------------------
def voice_brush(width, bristle):
    return Brush(width=width, bristle=bristle, opacity=0.45, thickness=0.8, dryness=0.1, jitter=0.15,
                 gap=0.14, pickup=0.4, taper=(0.015, 0.16), wander=1.2)


BRUSH = [voice_brush(84, 1.9), voice_brush(58, 1.7), voice_brush(50, 1.6), voice_brush(44, 1.5)]
VIB = [1.0, 1.5, 2.0, 2.6]
LAG = [1.0, 0.5, 0.25, 0.0]                # the others follow the boghe, the bassu last


def breath_pressure(t):
    """Hard on the attack, a long sustain that swells a little, and away to nothing."""
    t = np.clip(t, 0, 1)
    attack = 0.35 * np.exp(-t / 0.035)
    return 0.85 + attack + 0.2 * np.sin(np.pi * t) ** 0.6 - 0.25 * t ** 3


def dyn(beat):
    """How loud: the boghe sets it quietly, it opens at "magnam", and the last "am" is full."""
    b = np.asarray(beat) / verse.total
    return 0.55 + 0.25 * smooth01(b / 0.45) + 0.25 * smooth01((b - 0.55) / 0.3)


def sing(take, load=1.0, x_jit=0.0, w_k=1.0, **kw):
    for v in range(4):
        cuts = [take.end[k] for k in BREATHS[v]] + [verse.total + 0.9]
        b0 = take.start[ENTER[v]] + abs(rng.normal(0, 0.08))
        lag = LAG[v] + rng.normal(0, 0.08)
        for c in cuts:
            b1 = c - (0.4 if c < verse.total else 0.0) + rng.normal(0, 0.06)
            pts = breath_path(take, v, b0, b1, lambda b: x_of(b) + x_jit, y_of, vib=VIB[v], vib_beats=2.6 + 0.4 * v, lag=lag,
                              phase=rng.uniform(0, 6.28))
            br = BRUSH[v].but(width=BRUSH[v].width * w_k * np.exp(rng.normal(0, 0.08)), load=load, **kw)
            length = float(np.hypot(*np.diff(pts, axis=0).T).sum())
            br = br.but(deplete=deplete_for(length, br, end_load=rng.uniform(0.06, 0.16)))
            col = vowel_run(take, (b0, b1), PAL, SHADE[v] * np.exp(rng.normal(0, 0.06)), lag=lag,
                            gain=lambda bt: dyn(bt) ** 1.3)
            pr = lambda t, a=b0, z=b1: breath_pressure(t) * dyn(a + (z - a) * np.asarray(t))
            board.stroke(pts, br, col, pressure=pr, wobble=2.0)
            b0 = c + 0.05 + abs(rng.normal(0, 0.05))


board.untape()
board.tape_where(lambda X, Y: quintina(X, Y) > 0.3, outside=True, feather=6)

DAY = [("morning, the first stations", 4, 0.8, 0.35, 1.15),
       ("midday", 4, 0.85, 0.15, 1.05),
       ("afternoon, tired and a little flat", 4, 0.9, -0.45, 1.0),
       ("evening, the torches", 3, 1.0, 0.0, 0.95)]
for name, n, load, drift, wk in DAY:
    for _ in range(n):
        take = verse.sung(rng, rubato=0.06, drift=drift + rng.normal(0, 0.3))
        sing(take, load=load, x_jit=rng.normal(0, 10), w_k=wk)
    board.dry(0.5)
    board.stage(name)

# the nave keeps every chord a moment after it is let go: what is left on the brush, drawn on past
# the end of each syllable into the next, and on past the last one into the dark
echo = Brush(width=70, bristle=2.0, opacity=0.2, dryness=0.0, thickness=0.1, jitter=0.1, gap=0.2,
             pickup=0.0, taper=(0.2, 0.5), wander=1.6)
ref = verse.sung(rng, rubato=0.0)
for v in range(4):
    for k in range(len(SYL)):
        last = k == len(SYL) - 1
        b0 = ref.end[k] - 0.5 * ref.beats[k] + LAG[v]
        b1 = ref.end[k] + (7.5 if last else 1.4) + LAG[v]
        pts = breath_path(ref, v, b0, min(b1, verse.total), x_of, y_of, lag=LAG[v])
        if b1 > verse.total:
            pts = np.vstack([pts, pts[-1] + (BX * (b1 - verse.total), rng.normal(0, 6))])
        col = vowel_run(ref, (b0, b0 + 0.01), PAL, SHADE[v] * 0.8, lag=LAG[v])
        board.stroke(pts, echo.but(width=BRUSH[v].width * rng.uniform(1.0, 1.4)), col, wobble=3,
                     pressure=lambda t: 1.0 - 0.7 * t)
board.dry(1.0)
board.stage("the church keeping it")

# the last time, at the church door, after dark: the one he still hears
take = verse.sung(rng, rubato=0.03, drift=0.0)
sing(take, load=1.2, x_jit=0.0, w_k=0.62, opacity=0.92, thickness=2.2, dryness=0.16, jitter=0.1, gap=0.1)
board.stage("the last time, at the door")

finish(board, HERE, title="Miserere, first verse, Lunissanti 1997", year=2011,
       medium="Oil on agglomerated cork, gessoed", artist="gavino-cossu")
