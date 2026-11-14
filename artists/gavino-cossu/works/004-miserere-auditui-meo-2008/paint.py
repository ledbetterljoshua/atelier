"""Gavino Cossu - Miserere, Auditui meo, Lunissanti 2008

The verse he stopped in. "Auditui meo dabis gaudium et laetitiam, et exsultabunt ossa humiliata":
to my hearing you will give joy and gladness, and the bones that were humbled will rejoice. All
that day his contra was under the note and never once on it, and from the afternoon on he left the
last line to the other three. The quintina did not sound. So no gesso is left showing anywhere:
the silence covers the whole board, and where the fifth voice would have been the dark goes on
fullest, enough to fill the seams of the cork, so that it is the one place the lamp finds nothing.

Painted in his own copy of the paint (../../cork.py): oil-rich black that takes the lamp on the
granules, and breaths that land scratchy on a full brush.
"""
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[3]))
sys.path.insert(0, str(HERE.parents[1]))

from engine import hexc  # noqa: E402
from engine.studio import finish  # noqa: E402
from cork import Board, Brush  # noqa: E402
from tools import (OffTrue, Verse, breath_dry, breath_path, cork_board, deplete_for, in_tune,  # noqa: E402
                   sag, slide_thin, smooth01, vowel_run)

W, H = 1800, 1050
rng0 = np.random.default_rng(20080317)
GESSO = hexc("#ece4d2")
board = Board(W, H, GESSO, cork_board(W, H, rng0), seed=20080317)
board.dries_off_board = False
board.relief_soft = 2.0
board.bury = (1.1, 3.0)
board.light = (-0.3, -0.95)      # the strip light over the bench in the garage
rng = board.rng
Y, X = np.mgrid[0:H, 0:W].astype(np.float64) + 0.5

# --- the verse -----------------------------------------------------------------------------------
# bassu and contra hold, as in the first verse; the upper two keep a note across several syllables
# so the vowels change along a level line
I0, V, I, IV, VI, II = (0, 7, 12, 16), (0, 7, 10, 14), (0, 7, 12, 17), (0, 5, 9, 14), (0, 7, 9, 12), (0, 7, 14, 17)
SYL = [
    ("Au", "a", 1.5, I0), ("di", "i", 1.0, I0), ("tu", "u", 1.0, I), ("i", "i", 2.5, I),
    ("me", "e", 1.5, V), ("o", "o", 3.0, I0),
    ("da", "a", 1.0, I0), ("bis", "i", 1.5, II),
    ("gau", "a", 1.5, II), ("di", "i", 1.0, I), ("um", "u", 2.5, I0),
    ("et", "e", 1.0, VI), ("lae", "e", 1.5, VI), ("ti", "i", 1.0, V), ("ti", "i", 1.0, V), ("am", "a", 3.0, I0),
    ("et", "e", 1.0, I0), ("ex", "e", 1.0, I), ("sul", "u", 1.5, I), ("ta", "a", 1.5, II), ("bunt", "u", 2.5, I),
    ("os", "o", 2.0, VI), ("sa", "a", 2.0, V),
    ("hu", "u", 1.0, I0), ("mi", "i", 1.0, I), ("li", "i", 1.0, I), ("a", "a", 1.5, II), ("ta", "a", 5.0, I0),
]
verse = Verse(SYL, ["bassu", "contra", "contraltu", "boghe"])
CONTRA = 1
BUNT, SA, END = 20, 22, len(SYL) - 1

# from the same place as the 2008 first verse: the chord is as tall as the board
X0, X1 = 60.0, 1590.0
BX = (X1 - X0) / verse.total
Y_ROOT, PX_SEMI = 880.0, 38.0
Q_SEMI = 21.4


def x_of(beat):
    return X0 + np.asarray(beat) * BX


def y_of(semi):
    return Y_ROOT - np.asarray(semi) * PX_SEMI


BREATHS = {0: [5, 10, 15, 22], 1: [3, 7, 10, 15, 20, 22], 2: [5, 10, 15, 20], 3: [3, 7, 10, 15, 20, 22]}
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
# (name, the last syllable the contra sang, how fast he went flat, how far under he started)
DAY = [("morning", END, 0.10, 0.22),
       ("morning", SA, 0.12, 0.26),
       ("afternoon", SA, 0.14, 0.30),
       ("afternoon", BUNT, 0.15, 0.34),
       ("evening, the torches", BUNT, 0.17, 0.38),
       ("evening, the torches", BUNT, 0.18, 0.42),
       ("the last time, at the door", BUNT, 0.19, 0.45)]
TAKES = []
for name, stop, rate, under in DAY:
    t = verse.sung(rng, rubato=0.035, drift=rng.normal(0, 0.12))
    at = [t.start[0] + 0.1] + [t.end[k] + 0.15 for k in BREATHS[CONTRA]]
    fn, _ = sag(verse.total, rng, rate * rng.uniform(0.9, 1.1), 5.0, at=at)
    # he pulls up when he feels the bassu, but no longer all the way
    TAKES.append((name, stop, OffTrue(t, {CONTRA: lambda b, fn=fn, u=under: fn(b) - u})))

locked = sum(len(in_tune(tk, CONTRA, tol=0.12, min_beats=0.9)) for _, _, tk in TAKES)
print(f"quintina: {locked} spans in {len(TAKES)} takes")
assert locked == 0

# where it would have sounded had he been on the note: the long home chords, and the last one, which
# the church used to keep. The contra was not singing by then at all.
WOULD = [(k, verse.start[k] + 0.6, verse.start[k] + s[2]) for k, s in enumerate(SYL) if s[3] == I0 and s[2] >= 2.5]
QY = float(y_of(Q_SEMI))

board.stage("gesso on cork")

# --- the silence, over all of it -----------------------------------------------------------------
ink = [hexc("#1d150e"), hexc("#16130f"), hexc("#141317"), hexc("#121219")]
sil = Brush(width=110, bristle=2.2, opacity=0.99, dryness=0.1, thickness=0.08, jitter=0.05, gap=0.05,
            deplete=0.0003, pickup=0.0, wander=1.4, taper=(0.02, 0.04), angle=0.0, gloss=1.0)
for layer in range(4):
    y = -40.0 + rng.uniform(0, 30)
    while y < H + 50:
        x = -60.0 + rng.uniform(-30, 0)
        while x < W + 40:
            L = W + 140.0
            pts = np.array([(x, y), (x + L * 0.5, y + rng.normal(0, 4)), (x + L, y + rng.normal(0, 7))])
            # the first two coats cover. The last two are loaded once at the left edge and carried
            # the whole way, so the dark is fat before the first syllable and lean by the last
            run = sil.but(dryness=(0.1, 0.15, 0.25, 0.45)[layer], gloss=(0.5, 0.7, 0.85, 1.0)[layer])
            if layer >= 2:
                run = run.but(thickness=0.2, load=1.2, deplete=deplete_for(L, sil, end_load=0.4))
            board.stroke(pts, run, ink[layer], wobble=2)
            if layer >= 2:
                break
            x += L * rng.uniform(0.7, 0.95)
        y += rng.uniform(36, 50)
board.dry(0.95)
board.stage("the silence, and no gesso left")

# --- where it would have been, closed ------------------------------------------------------------
# one loaded stroke of black for each, oil-rich enough to settle: it fills the seams and lies flat
shut = Brush(width=30, bristle=2.0, opacity=0.995, dryness=0.0, thickness=0.0, jitter=0.02, gap=0.0,
             loadvar=0.05, deplete=0.0, pickup=0.0, wander=0.8, taper=(0.1, 0.3), angle=0.0, gloss=1.0,
             level=1.0)
BLACK = hexc("#0c0b0b")
for k, a, b in WOULD:
    last = k == END
    x0, x1 = float(x_of(a)), float(x_of(b)) + (520.0 if last else 20.0)
    pts = np.array([(x0, QY), ((x0 + x1) / 2, QY + rng.normal(0, 1.5)), (x1, QY + rng.normal(0, 2))])
    for _ in range(2):
        board.stroke(pts, shut.but(width=34 if last else 11), BLACK, wobble=1.0,
                     pressure=lambda t: 0.55 + 0.45 * np.sin(np.pi * np.clip(t, 0, 1) ** 0.6))
board.dry(1.0)
board.stage("where it would have been, closed")


# --- the singing ---------------------------------------------------------------------------------
def dyn(beat):
    """Loud all through; a little more at "laetitiam", and the three push the last line."""
    b = np.asarray(beat) / verse.total
    return 0.85 + 0.1 * smooth01((b - 0.42) / 0.12) + 0.1 * smooth01((b - 0.72) / 0.1)


def breath_pressure(t):
    t = np.clip(t, 0, 1)
    return 0.85 + 0.3 * np.exp(-t / 0.03) + 0.15 * np.sin(np.pi * t) ** 0.6 - 0.25 * t ** 3


def voice_brush(v, **kw):
    b = Brush(width=WID[v], bristle=2.0, opacity=0.75, thickness=1.2, dryness=0.15, jitter=0.12,
              gap=0.1, pickup=0.25, taper=(0.02, 0.14), wander=1.2, angle=0.0, gloss=0.0)
    return b.but(**kw)


def landing(v, length_px, faint=False):
    """The scratchy landing of a breath, on a full brush: for the first few centimetres only the
    tops of the granules take paint. The bassu never gets below them at all."""
    px = 70.0 if v else 110.0
    a = px / max(length_px, px)
    floor = 0.34 if v == 0 else 0.0
    if faint:
        floor = 0.58
    return lambda t: max(floor, 0.66 * np.exp(-float(t) / a))


def sing(take, stop, load=1.0, x_jit=0.0, w_k=1.0, gain=1.0, base_dry=0.15, **kw):
    for v in range(4):
        cuts = [take.end[k] for k in BREATHS[v]] + [verse.total + 0.6]
        if v == CONTRA:
            cuts = [take.end[k] for k in BREATHS[v] if k <= stop] + ([verse.total + 0.3] if stop == END else [])
        b0 = take.start[0] + abs(rng.normal(0, 0.08))
        lag = LAG[v] + rng.normal(0, 0.05)
        for j, c in enumerate(cuts):
            b1 = c - (0.4 if c < verse.total else 0.0) + rng.normal(0, 0.05)
            gone = v == CONTRA and j == len(cuts) - 1      # the breath after which he did not come in
            # the last line, the times he still sang it: hardly any voice, the tops of the granules
            faint = v == CONTRA and b0 > take.end[BUNT] - 0.2
            pts = breath_path(take, v, b0, b1, lambda b: x_of(b) + x_jit, y_of, lag=lag, glide=GLIDE)
            br = voice_brush(v, width=WID[v] * w_k * np.exp(rng.normal(0, 0.06)), load=load, **kw)
            length = float(np.hypot(*np.diff(pts, axis=0).T).sum())
            br = br.but(deplete=deplete_for(length, br, end_load=0.06 if gone else rng.uniform(0.15, 0.3)))
            if gone:
                br = br.but(taper=(0.02, 0.45))
            col = vowel_run(take, (b0, b1), PAL, SHADE[v] * gain * np.exp(rng.normal(0, 0.05)), lag=lag,
                            blend=1.2 if v == 0 else 0.5)
            pr = lambda t, a=b0, z=b1: breath_pressure(t) * dyn(a + (z - a) * np.asarray(t))
            sl = slide_thin(pts, steep=0.6, floor=0.0)
            dr = breath_dry(base_dry + (0.3 if v == 0 else 0.0))
            board.stroke(pts, br, col, pressure=pr, opacity=sl, dryness=lambda t: max(dr(t), 0.95 * (1 - sl(t))),
                         scratch=landing(v, length, faint), wobble=1.0)
            b0 = c + 0.05 + abs(rng.normal(0, 0.05))


for i, (name, stop, take) in enumerate(TAKES[:-1]):
    sing(take, stop, load=0.9, x_jit=rng.normal(0, 3), w_k=1.0, gain=0.85)
    if TAKES[i + 1][0] != name:
        board.dry(0.6)
        board.stage(name)

# what the nave keeps: the end of each line held on into the dark. At the end it keeps three.
echo = Brush(width=60, bristle=2.0, opacity=0.3, dryness=0.7, thickness=0.2, jitter=0.1, gap=0.2,
             pickup=0.0, taper=(0.15, 0.5), wander=1.4, angle=0.0, gloss=0.0)
ref = verse.sung(rng, rubato=0.0)
for v in range(4):
    for k in (10, 15, END):
        last = k == END
        if last and v == CONTRA:
            continue
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

name, stop, take = TAKES[-1]
sing(take, stop, load=1.1, w_k=0.85, opacity=0.9, thickness=1.8, base_dry=0.08)
board.stage(name)

finish(board, HERE, title="Miserere, Auditui meo, Lunissanti 2008", year=2014,
       medium="Oil on agglomerated cork, gessoed, the whole board covered", artist="gavino-cossu",
       made="2026-11-14")
