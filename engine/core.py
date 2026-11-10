"""The board and the brush.

Three things paint can do here, kept separate because they are separate on a real surface:
  cover  - opaque paint hides what is under it (area coverage, linear blend)
  mix    - a loaded bristle dragging through wet paint picks it up (pigment mix, geometric)
  glaze  - a transparent film filters what is under it (multiply)

A stroke is a path walked by a row of bristles. Each bristle carries its own colour and its own
load, runs dry at its own rate, and on a rough board only reaches the high spots once it thins.
"""
from dataclasses import dataclass, replace
from math import ceil, exp, floor, log, sin, sqrt

import numpy as np
from numba import njit
from PIL import Image, ImageDraw
from scipy.ndimage import gaussian_filter

from . import paths
from .color import FLOOR, linear_to_srgb

PAINT, GLAZE = 0, 1


@njit(cache=True, fastmath=True)
def _walk(col, hgt, wet, tooth, mask, use_mask, px, py, pw, pp, boff, bph, bfr, wander, blog, bload,
          brad, mode, a0, pickup, deplete, dryness, soft, thickness, hard):
    H, W = hgt.shape
    n = px.shape[0]
    B = boff.shape[0]
    r2 = brad * brad
    for i in range(n):
        i0 = i - 1 if i > 0 else 0
        i1 = i + 1 if i < n - 1 else n - 1
        tx = px[i1] - px[i0]
        ty = py[i1] - py[i0]
        L = sqrt(tx * tx + ty * ty) + 1e-6
        nx = -ty / L
        ny = tx / L
        hw = pw[i] * 0.5
        pr = pp[i]
        if pr <= 0.0:
            continue
        for b in range(B):
            ld = bload[b]
            if ld <= 0.004:
                continue
            o = boff[b] * hw + wander * sin(bph[b] + i * bfr[b])
            cx = px[i] + nx * o
            cy = py[i] + ny * o
            ix = int(cx)
            iy = int(cy)
            if ix < 0 or iy < 0 or ix >= W or iy >= H:
                bload[b] = ld * (1.0 - deplete)
                continue
            if pickup > 0.0 and mode == 0:
                # feel for wet paint just ahead of the bristle, where this stroke has not been yet
                ax = int(cx + tx / L * (brad + 2.0))
                ay = int(cy + ty / L * (brad + 2.0))
                if ax >= 0 and ay >= 0 and ax < W and ay < H:
                    wv = wet[ay, ax]
                    if wv > 0.01:
                        k = pickup * wv * pr * 0.25
                        for c in range(3):
                            blog[b, c] = (1.0 - k) * blog[b, c] + k * log(col[ay, ax, c] + 1e-4)
            c0 = exp(blog[b, 0])
            c1 = exp(blog[b, 1])
            c2 = exp(blog[b, 2])
            x0 = int(floor(cx - brad))
            x1 = int(ceil(cx + brad))
            y0 = int(floor(cy - brad))
            y1 = int(ceil(cy + brad))
            if x0 < 0:
                x0 = 0
            if y0 < 0:
                y0 = 0
            if x1 > W - 1:
                x1 = W - 1
            if y1 > H - 1:
                y1 = H - 1
            thr = dryness * (1.0 - 0.7 * ld * pr)
            for y in range(y0, y1 + 1):
                dy = y + 0.5 - cy
                for x in range(x0, x1 + 1):
                    dx = x + 0.5 - cx
                    d2 = dx * dx + dy * dy
                    if d2 > r2:
                        continue
                    kern = 1.0 if hard else 1.0 - d2 / r2
                    a = a0 * pr * ld * kern
                    if a > 1.0:
                        a = 1.0
                    if dryness > 0.0:
                        s = (tooth[y, x] - thr) / soft + 0.5
                        if s <= 0.0:
                            continue
                        if s < 1.0:
                            a *= s
                    if use_mask:
                        a *= mask[y, x]
                    if a <= 0.0005:
                        continue
                    if mode == 0:
                        col[y, x, 0] += (c0 - col[y, x, 0]) * a
                        col[y, x, 1] += (c1 - col[y, x, 1]) * a
                        col[y, x, 2] += (c2 - col[y, x, 2]) * a
                        hgt[y, x] += a * thickness * ld
                        if a > wet[y, x]:
                            wet[y, x] = a
                    else:
                        col[y, x, 0] *= 1.0 - a + a * c0
                        col[y, x, 1] *= 1.0 - a + a * c1
                        col[y, x, 2] *= 1.0 - a + a * c2
            bload[b] = ld * (1.0 - deplete)


@dataclass
class Brush:
    width: float = 24.0        # px across the ferrule
    bristle: float = 1.3       # px radius of one bristle's mark
    opacity: float = 0.9       # how much a full pass covers
    load: float = 1.0          # paint on the brush at the start
    deplete: float = 0.0015    # fraction lost per step; higher runs dry sooner
    pickup: float = 0.25       # how readily bristles take up wet paint underneath
    dryness: float = 0.0       # 0 floods the tooth; 1 only kisses the high spots
    soft: float = 0.18         # width of the tooth threshold
    thickness: float = 1.0     # body left on the surface (reads as relief under raking light)
    jitter: float = 0.05       # colour variation between bristles (log units)
    gap: float = 0.08          # chance a bristle is splayed out or starved
    taper: tuple = (0.06, 0.12)  # fraction of the stroke spent landing and lifting
    glaze: bool = False
    hard: bool = False         # knife edge rather than hair
    wander: float = 0.6        # px each bristle strays from its place in the row

    def but(self, **kw):
        return replace(self, **kw)


class Board:
    def __init__(self, w, h, ground, tooth, seed=0):
        self.w, self.h = w, h
        self.rng = np.random.default_rng(seed)
        self.col = np.empty((h, w, 3), dtype=np.float32)
        self.col[:] = np.asarray(ground, dtype=np.float32)
        self.hgt = np.zeros((h, w), dtype=np.float32)
        self.wet = np.zeros((h, w), dtype=np.float32)
        self.tooth = np.ascontiguousarray(tooth, dtype=np.float32)
        self.mask = np.ones((h, w), dtype=np.float32)
        self.use_mask = False
        self.n_strokes = 0
        self.stages = []

    # --- masking tape -------------------------------------------------------
    def tape(self, *polys, outside=False, feather=0.0):
        """Only let paint land inside these polygons (or outside them)."""
        im = Image.new("L", (self.w, self.h), 0)
        d = ImageDraw.Draw(im)
        for p in polys:
            d.polygon([tuple(map(float, q)) for q in p], fill=255)
        m = np.asarray(im, dtype=np.float32) / 255.0
        if outside:
            m = 1.0 - m
        if feather > 0:
            m = gaussian_filter(m, feather)
        self.mask = np.ascontiguousarray(m, dtype=np.float32)
        self.use_mask = True

    def untape(self):
        self.use_mask = False

    def dry(self, amount=1.0):
        """Leave it overnight."""
        self.wet *= (1.0 - amount)

    # --- the stroke ---------------------------------------------------------
    def stroke(self, pts, brush, color, color2=None, pressure=1.0, wobble=0.0, smooth=True):
        pts = np.asarray(pts, dtype=np.float64)
        if smooth and len(pts) > 2:
            pts = paths.chaikin(pts, 4)
        if wobble > 0:
            pts = paths.chaikin(paths.wobble(pts, self.rng, wobble), 3)
        spacing = max(0.5, brush.bristle * 0.5)
        p, total = paths.resample(pts, spacing)
        n = len(p)
        if n < 2:
            return
        t = np.linspace(0.0, 1.0, n)
        tin, tout = brush.taper
        env = np.ones(n)
        if tin > 0:
            env *= np.clip(t / tin, 0, 1) ** 0.6
        if tout > 0:
            env *= np.clip((1 - t) / tout, 0, 1) ** 0.6
        if callable(pressure):
            pres = np.asarray(pressure(t), dtype=np.float64)
        else:
            pres = np.full(n, float(pressure))
        pp = np.clip(pres * (0.35 + 0.65 * env), 0, 1.5)
        pw = brush.width * (0.45 + 0.55 * env) * (0.8 + 0.2 * np.clip(pres, 0, 1.2))

        B = max(2, int(brush.width / (brush.bristle * 0.7)))
        rng = self.rng
        boff = np.linspace(-1, 1, B) + rng.normal(0, 0.35 / B, B)
        streak = np.cumsum(rng.normal(0, 1, B))
        streak = (streak - streak.mean()) / (streak.std() + 1e-6)
        c1 = np.log(np.maximum(np.asarray(color, dtype=np.float64), FLOOR))
        if color2 is not None:
            c2 = np.log(np.maximum(np.asarray(color2, dtype=np.float64), FLOOR))
            u = np.clip((boff + 1) / 2 + rng.normal(0, 0.08, B), 0, 1)[:, None]
            blog = c1 * (1 - u) + c2 * u
        else:
            blog = np.tile(c1, (B, 1))
        blog = blog + (streak * brush.jitter)[:, None] + rng.normal(0, brush.jitter * 0.4, (B, 3))
        blog = np.minimum(blog, 0.0)
        bload = brush.load * np.exp(rng.normal(0, 0.18, B))
        starved = rng.random(B) < brush.gap
        bload[starved] *= rng.random(starved.sum()) * 0.35
        hits = 5.0
        a0 = 1.0 - (1.0 - min(brush.opacity, 0.995)) ** (1.0 / hits)
        _walk(self.col, self.hgt, self.wet, self.tooth, self.mask, self.use_mask,
              np.ascontiguousarray(p[:, 0]), np.ascontiguousarray(p[:, 1]),
              np.ascontiguousarray(pw), np.ascontiguousarray(pp),
              np.ascontiguousarray(boff), rng.uniform(0, 6.283, B), rng.uniform(0.01, 0.05, B) * spacing,
              float(brush.wander), np.ascontiguousarray(blog), np.ascontiguousarray(bload),
              float(brush.bristle), GLAZE if brush.glaze else PAINT, a0, float(brush.pickup),
              float(brush.deplete), float(brush.dryness), float(brush.soft),
              float(brush.thickness), bool(brush.hard))
        self.n_strokes += 1

    def dab(self, x, y, brush, color, angle=None, length=None, **kw):
        """A short touch."""
        angle = self.rng.uniform(0, np.pi) if angle is None else angle
        length = brush.width * 0.8 if length is None else length
        dx, dy = np.cos(angle) * length / 2, np.sin(angle) * length / 2
        self.stroke([(x - dx, y - dy), (x + dx, y + dy)], brush, color, **kw)

    def fill(self, poly, brush, color, angle=0.0, spacing=None, wobble=0.0, color_fn=None, **kw):
        """Lay a polygon in with parallel strokes. color_fn(mid_xy) may vary the colour."""
        spacing = brush.width * 0.55 if spacing is None else spacing
        segs = paths.hatch(poly, angle, spacing, self.rng, jitter=0.25)
        self.rng.shuffle(segs)
        for a, b in segs:
            c = color if color_fn is None else color_fn((a + b) / 2)
            self.stroke([a, b], brush, c, wobble=wobble, **kw)

    # --- looking at it ------------------------------------------------------
    def render(self, relief=1.0, raking=(-0.55, -0.75), tooth_relief=0.25):
        h = gaussian_filter(self.hgt, 0.7)
        h = np.log1p(h) * 1.6 * relief + self.tooth * tooth_relief / (1.0 + self.hgt)
        gy, gx = np.gradient(h)
        lx, ly = raking
        shade = 1.0 + np.clip(-(gx * lx + gy * ly) * 0.55, -0.3, 0.45)
        img = self.col * shade[..., None]
        return (linear_to_srgb(img) * 255.0 + 0.5).astype(np.uint8)

    def stage(self, name):
        """Keep a look at the board as it stands, for the record of how it was made."""
        self.stages.append((name, self.n_strokes, self.render()))

    def save(self, path, **kw):
        Image.fromarray(self.render(**kw)).save(path)
