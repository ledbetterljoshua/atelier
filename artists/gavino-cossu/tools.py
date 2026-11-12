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


def breath_path(take, voice, b0, b1, x_of, y_of, vib=0.0, vib_beats=0.35, phase=0.0, step=0.04, lag=0.0,
                glide=1.0):
    """Points along one breath: across the board with time, up and down with pitch, with a vibrato
    that is a few px either way. A slower chant leans into its notes over a longer `glide`."""
    bt = np.arange(b0, b1 + 1e-9, step)
    if len(bt) < 2:
        bt = np.array([b0, b1])
    semi = take.pitch(voice, bt - lag, glide=glide)
    # a breath starts on its note: no sliding up into it from the one before the breath
    k0 = take.syl_at(b0 - lag)
    first = bt - lag < take.end[k0]
    semi[first] = take.v.sylls[k0][3][voice] + take.drift
    if hasattr(take, "off"):
        semi[first] += take.off(voice, bt[first] - lag)
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


def quiet(dyn, b0, b1, floor=0.15, power=1.3):
    """Opacity along a breath from b0 to b1: soft singing is less paint on the brush, not only darker
    paint, so on a dry brush it catches only the tops of the cork."""
    def fn(t):
        return floor + (1.0 - floor) * float(dyn(b0 + (b1 - b0) * t)) ** power
    return fn


def field(w, h, fn):
    """fn(X, Y) at every pixel centre, as an (h, w) array: a pressure the engine reads where a stroke
    passes."""
    Y, X = np.mgrid[0:h, 0:w].astype(np.float64) + 0.5
    return np.broadcast_to(np.asarray(fn(X, Y), dtype=np.float64), (h, w)).copy()


class OffTrue(Take):
    """A take in which one voice wanders off the note on its own: `off[voice](beat)` in semitones,
    added to where that voice should be. The others stay where the take has them."""

    def __init__(self, take, off):
        super().__init__(take.v, take.beats, take.drift)
        self._off = off

    def off(self, voice, beat):
        f = self._off.get(voice)
        beat = np.atleast_1d(np.asarray(beat, dtype=float))
        return np.zeros_like(beat) if f is None else np.asarray(f(beat), dtype=float)

    def pitch(self, voice, beat, glide=1.0):
        return super().pitch(voice, beat, glide) + self.off(voice, beat)


def sag(total, rng, rate, catch_every, catch_beats=0.5, at=()):
    """A voice that cannot hear itself: it goes flat steadily, `rate` semitones a beat, until it
    hears the bassu in its back and pulls up over `catch_beats`. It always catches at the beats in
    `at` (a breath, say), and in a long stretch without one, about every `catch_every` beats.
    Returns (fn(beat), catch beats)."""
    fixed = sorted(list(at) + [total + 8.0])
    catches, b = [], 0.0
    for f in fixed:
        while f - b > catch_every * 1.3:
            b += catch_every * rng.uniform(0.8, 1.2)
            catches.append(b)
        if f <= total:
            catches.append(f)
        b = f
    c = np.array(catches if catches else [total + 8.0])

    def fn(beat):
        beat = np.atleast_1d(np.asarray(beat, dtype=float))
        k = np.searchsorted(c, beat, side="right")
        last = np.where(k > 0, c[np.maximum(k - 1, 0)], 0.0)
        down = -rate * (beat - last)                       # flat since the last catch
        prev = np.where(k > 1, c[np.maximum(k - 2, 0)], 0.0)
        before = np.where(k > 0, -rate * (last - prev), 0.0)  # how flat it was when he caught it
        u = smooth01((beat - last) / catch_beats)
        return np.where(k > 0, before * (1 - u) + down * u, down)
    return fn, c


def in_tune(take, voice, tol=0.12, min_beats=1.0, step=0.05, keep=None):
    """Spans of beats where a wandering voice is within `tol` of its note for at least `min_beats`:
    the only places the four could lock. keep(beat) -> bool rules out spans that do not count."""
    bt = np.arange(0.0, take.v.total, step)
    ok = np.abs(take.off(voice, bt)) < tol
    if keep is not None:
        ok &= np.array([bool(keep(b)) for b in bt])
    spans, a = [], None
    for b, o in zip(bt, ok):
        if o and a is None:
            a = b
        elif not o and a is not None:
            if b - a >= min_beats:
                spans.append((a, b))
            a = None
    if a is not None and bt[-1] - a >= min_beats:
        spans.append((a, bt[-1]))
    return spans


def breath_dry(base, attack=0.85, tail=0.65, a=0.05, z=0.18):
    """Dryness along one breath: the brush lands scratchy on the attack, fills in as the voice
    opens, and goes dry again as the breath and the paint run out together."""
    def fn(t):
        t = float(t)
        d = base + (attack - base) * np.exp(-t / max(a, 1e-3))
        return max(d, base + (tail - base) * smooth01((t - (1 - z)) / z))
    return fn


def slide_thin(pts, steep=1.2, floor=0.12):
    """fn(t) -> 0..1 along a breath path: full on a held note, little paint where the voice slides
    between notes. A level flat moved up the board would otherwise sweep a block as tall as itself;
    the voice is thin there, so the brush barely touches."""
    pts = np.asarray(pts, dtype=float)
    d = np.gradient(pts, axis=0)
    slope = np.abs(d[:, 1]) / (np.abs(d[:, 0]) + 1e-6)
    k = floor + (1 - floor) / (1.0 + (slope / steep) ** 2)
    k = gaussian_filter(k, 1.0)
    s = np.linspace(0, 1, len(k))

    def fn(t):
        return float(np.interp(t, s, k))
    return fn
