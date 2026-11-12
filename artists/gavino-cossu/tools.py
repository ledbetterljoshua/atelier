"""Gavino Cossu's kit. A verse of chant laid out as time across and pitch up, and the board it goes on."""
import numpy as np
from scipy.ndimage import gaussian_filter
from scipy.spatial import cKDTree

from engine import ground, paths


def cork_board(w, h, rng, coarse=5.5, fine=2.4):
    """Agglomerated cork from the granulating line, sealed with two coats of gesso.

    Granules pressed together: each is a little dome, the seams between them are low, and the gesso
    has half filled the seams. A dry brush catches the domes and skips the seams."""
    Y, X = np.mgrid[0:h, 0:w].astype(np.float32)
    pix = np.stack([X.ravel(), Y.ravel()], 1)
    out = np.zeros(h * w, dtype=np.float32)
    for size, weight in ((coarse, 0.65), (fine, 0.35)):
        n = int(w * h / (size * size * 1.6))
        pts = rng.random((n, 2)) * [w, h]
        rad = size * np.exp(rng.normal(0, 0.28, n))
        tree = cKDTree(pts)
        d, i = tree.query(pix, k=1, workers=-1)
        dome = np.clip(1.0 - (d / rad[i]) ** 2, 0, 1)
        dome *= 0.75 + 0.25 * rng.random(n)[i]          # some granules stand prouder than others
        out += dome.astype(np.float32) * weight
    t = out.reshape(h, w)
    t = 0.55 * t + 0.45 * gaussian_filter(t, 1.6)        # the gesso
    t = 0.85 * t + 0.15 * ground.fbm(w, h, rng, base=8, octaves=3)
    return ((t - t.min()) / (t.max() - t.min())).astype(np.float32)


def smooth01(u):
    u = np.clip(u, 0, 1)
    return u * u * (3 - 2 * u)


class Verse:
    """Syllables in order, each with its vowel, length in beats and a chord: the semitones above the
    root that each voice holds. Voices are listed low to high."""

    def __init__(self, sylls, voices):
        self.sylls = sylls                     # [(text, vowel, beats, (s0, s1, s2, s3)), ...]
        self.voices = voices
        self.beats = np.array([s[2] for s in sylls], dtype=float)
        self.start = np.concatenate([[0.0], np.cumsum(self.beats)[:-1]])
        self.total = float(self.beats.sum())

    def sung(self, rng, rubato=0.06, drift=0.0):
        """One time through: each syllable stretched or hurried a little, the whole lot a little
        sharp or flat. Returns a Take."""
        b = self.beats * np.exp(rng.normal(0, rubato, len(self.beats)))
        b *= self.total / b.sum()
        return Take(self, b, drift)


class Take:
    def __init__(self, verse, beats, drift):
        self.v = verse
        self.beats = beats
        self.start = np.concatenate([[0.0], np.cumsum(beats)[:-1]])
        self.end = self.start + beats
        self.drift = drift

    def syl_at(self, beat):
        return int(np.clip(np.searchsorted(self.end, beat, side="right"), 0, len(self.beats) - 1))

    def pitch(self, voice, beat, glide=1.0):
        """Semitones above the root, sliding into each new note over `glide` beats."""
        beat = np.atleast_1d(beat)
        out = np.empty_like(beat, dtype=float)
        for j, bt in enumerate(beat):
            k = self.syl_at(bt)
            now = self.v.sylls[k][3][voice]
            if k > 0:
                prev = self.v.sylls[k - 1][3][voice]
                u = smooth01((bt - self.start[k]) / glide)
                now = prev + (now - prev) * u
            out[j] = now + self.drift
        return out

    def vowel(self, beat):
        return self.v.sylls[self.syl_at(beat)][1]


def vowel_run(take, beats, palette, voice_shade, blend=0.35, lag=0.0, gain=None):
    """fn(t) for a stroke covering `beats`: the colour of whatever vowel is being sung at that
    moment, eased across each change of syllable. A voice `lag` beats behind the boghe changes
    vowel that much later; gain(beat) darkens what is sung quietly."""
    b0, b1 = beats
    names = sorted(palette)
    logs = {k: np.log(np.maximum(palette[k], 1e-4)) for k in names}

    def fn(t):
        bt = b0 + (b1 - b0) * t - lag
        g = 1.0 if gain is None else float(gain(bt))
        k = take.syl_at(bt)
        c = logs[take.v.sylls[k][1]]
        if k > 0 and bt - take.start[k] < blend:
            u = smooth01((bt - take.start[k]) / blend)
            c = logs[take.v.sylls[k - 1][1]] * (1 - u) + c * u
        return np.exp(c) * voice_shade * g
    return fn


def breath_path(take, voice, b0, b1, x_of, y_of, vib=0.0, vib_beats=0.35, phase=0.0, step=0.04, lag=0.0):
    """Points along one breath: across the board with time, up and down with pitch, with a vibrato
    that is a few px either way."""
    bt = np.arange(b0, b1 + 1e-9, step)
    if len(bt) < 2:
        bt = np.array([b0, b1])
    semi = take.pitch(voice, bt - lag)
    # a breath starts on its note: no sliding up into it from the one before the breath
    k0 = take.syl_at(b0 - lag)
    first = bt - lag < take.end[k0]
    semi[first] = take.v.sylls[k0][3][voice] + take.drift
    y = y_of(semi)
    if vib > 0:
        y = y + vib * np.sin(2 * np.pi * bt / vib_beats + phase) * smooth01((bt - b0) / 1.2)
    return np.stack([x_of(bt), y], 1)


def deplete_for(length_px, brush, end_load=0.2):
    """The brush is loaded once per breath and has to run out where the breath does."""
    n = max(2.0, length_px / max(0.5, brush.bristle * 0.5))
    return float(1.0 - end_load ** (1.0 / n))


def along(pts, field):
    """fn(t) sampling a field fn(x, y) along a path, for pressure that changes as it goes."""
    pts, _ = paths.resample(pts, 6.0)
    s = np.concatenate([[0], np.cumsum(np.hypot(*np.diff(pts, axis=0).T))])
    s /= max(s[-1], 1e-6)
    vals = field(pts[:, 0], pts[:, 1])

    def fn(t):
        return np.interp(t, s, vals)
    return fn
