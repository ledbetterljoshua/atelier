"""Itzel Moroyoqui's kit. A pavement she can look down at, a sun that throws shade, and plywood."""
import numpy as np
from scipy.ndimage import gaussian_filter

from engine import ground


def plywood(w, h, rng, grain=0.9):
    """9 mm ply primed with one coat of exterior vinyl. The face veneer's grain runs across the
    board and comes up through the primer as long low ridges, with the odd open pore."""
    y, x = np.mgrid[0:h, 0:w].astype(np.float32)
    warp = ground.fbm(w, h, rng, base=3, octaves=3) * 60.0
    rings = 0.5 + 0.5 * np.sin(2 * np.pi * (y + warp) / (9.0 + 5.0 * ground.fbm(w, h, rng, base=4, octaves=2)))
    streak = ground.fbm(max(8, w // 40), h, rng, base=60, octaves=3)
    streak = np.asarray(np.repeat(streak, int(np.ceil(w / streak.shape[1])), axis=1)[:, :w])
    t = grain * (0.45 * rings + 0.35 * gaussian_filter(streak, (0.6, 30))) + 0.35 * ground.fbm(w, h, rng, base=150, octaves=2)
    return ((t - t.min()) / (t.max() - t.min())).astype(np.float32)


def v3(*a):
    return np.array(a, dtype=np.float64)


class View:
    """Standing on the pavement and looking down at it. x right, y up, z away from her, metres.
    Eye at (0, eye_h, 0), tipped down by pitch."""

    def __init__(self, W, H, f, eye_h, pitch_deg, cy=None):
        self.W, self.H, self.f = W, H, f
        self.eye = v3(0, eye_h, 0)
        p = np.radians(pitch_deg)
        self.F = v3(0, -np.sin(p), np.cos(p))
        self.U = v3(0, np.cos(p), np.sin(p))
        self.R = v3(1, 0, 0)
        self.cx, self.cy = W / 2, (H / 2 if cy is None else cy)

    def P(self, p):
        p = np.asarray(p, dtype=np.float64)
        d = p - self.eye
        xc, yc, zc = d @ self.R, d @ self.U, d @ self.F
        return np.stack([self.cx + self.f * xc / zc, self.cy - self.f * yc / zc], -1)

    def rays(self):
        """Unit ray through every pixel centre, (H, W, 3)."""
        Y, X = np.mgrid[0:self.H, 0:self.W].astype(np.float64) + 0.5
        a = (X - self.cx) / self.f
        b = -(Y - self.cy) / self.f
        d = a[..., None] * self.R + b[..., None] * self.U + self.F
        return d / np.linalg.norm(d, axis=-1, keepdims=True)

    def scale_at(self, p):
        """Pixels per metre at a point."""
        d = np.asarray(p) - self.eye
        return self.f / (d @ self.F)


def ray_box(eye, rays, lo, hi):
    """Distance along each ray to an upright box, and which face it enters by (0 x, 1 y, 2 z; the
    face is the low side unless the ray comes from above, where y is the top). inf where it misses."""
    with np.errstate(divide="ignore", invalid="ignore"):
        t1 = (lo - eye) / rays
        t2 = (hi - eye) / rays
    tmin = np.minimum(t1, t2)
    tmax = np.maximum(t1, t2)
    tn = tmin.max(-1)
    tf = tmax.min(-1)
    face = tmin.argmax(-1)
    hit = (tn <= tf) & (tf > 0)
    return np.where(hit, tn, np.inf), face


def sweep(board, mask, brush, color_at, angle, spacing, rng, over=60, every=90, jitter=0.03,
          wobble=2.0, vary=None, **kw):
    """Long strokes laid right across a region, edge to edge, so no stroke ends inside it; tape cuts
    them. Each is mixed at points along its length as it crosses the region."""
    h, w = mask.shape
    ys, xs = np.nonzero(mask > 0.5)
    if len(xs) == 0:
        return
    cx, cy = (xs.min() + xs.max()) / 2, (ys.min() + ys.max()) / 2
    R = np.hypot(xs.max() - xs.min(), ys.max() - ys.min()) / 2 + over
    d = np.array([np.cos(angle), np.sin(angle)])
    nrm = np.array([-d[1], d[0]])
    offs = np.arange(-R, R, spacing)
    rng.shuffle(offs)
    for o in offs:
        o = o + rng.normal(0, spacing * 0.2)
        a = angle + rng.normal(0, jitter)
        dd = np.array([np.cos(a), np.sin(a)])
        c = np.array([cx, cy]) + nrm * o
        n = max(3, int(2 * R / every))
        s = np.linspace(-R, R, n)
        pts = c + s[:, None] * dd
        inside = [(0 <= p[0] < w and 0 <= p[1] < h and mask[int(p[1]), int(p[0])] > 0.5) for p in pts]
        if not any(inside):
            continue
        idx = np.nonzero(inside)[0]
        i0, i1 = max(0, idx[0] - 1), min(n - 1, idx[-1] + 1)
        pts = pts[i0:i1 + 1]
        if len(pts) < 3:
            pts = np.vstack([pts[:1], pts[:1] * 0.5 + pts[-1:] * 0.5, pts[-1:]])
        cols = [color_at(float(np.clip(p[0], 0, w - 1)), float(np.clip(p[1], 0, h - 1)))
                for p in pts[1:-1]]
        cols = [cols[0]] + cols + [cols[-1]]          # past the tape it is the same colour as inside
        if vary is not None:
            f = vary(rng)
            cols = [f(c) for c in cols]
        board.stroke(pts, brush, cols, wobble=wobble, **kw)


def lay_ground(board, view, where, brush, color_at, n, length, angle, rng, width_m=None, jitter=0.15,
               wobble=1.5, area=(-2.5, 2.5, 0.0, 2.3), **kw):
    """Strokes laid on the pavement itself: placed and turned in metres, then seen. A stroke further
    off comes out shorter and narrower, so the marks themselves lie down. where(x, z) says whether a
    place gets one; color_at(p) mixes it for the point p it starts from (or returns a run)."""
    x0, x1, z0, z1 = area
    done = 0
    for _ in range(n):
        x, z = rng.uniform(x0, x1), rng.uniform(z0, z1)
        if not where(x, z):
            continue
        a = angle(x, z) if callable(angle) else angle
        a += rng.normal(0, jitter)
        L = length * rng.uniform(0.7, 1.3)
        d = np.array([np.cos(a), 0.0, np.sin(a)]) * L / 2
        c = np.array([x, 0.0, z])
        pts = view.P(np.array([c - d, c - d * 0.33, c + d * 0.33, c + d]))
        b = brush if width_m is None else brush.but(width=max(3.0, width_m * view.scale_at(c)))
        board.stroke(pts, b, color_at(c), wobble=wobble, **kw)
        done += 1
    return done


def sweep_ground(board, view, mask, brush, color_at, rng, xs=None, zs=None, z_span=(0.0, 2.3),
                 x_span=(-2.6, 2.6), samples=12, wobble=1.5, vary=None, **kw):
    """Long strokes across the pavement edge to edge, along lines on the ground: at each x in xs a
    stroke runs away from her, at each z in zs one runs across. Seen, the first kind converge and the
    second kind close up with distance. The tape cuts them; color_at(p) mixes along each."""
    lines = []
    for x in (xs if xs is not None else []):
        z = np.linspace(*z_span, samples)
        lines.append(np.stack([np.full_like(z, x), np.zeros_like(z), z], 1))
    for z in (zs if zs is not None else []):
        x = np.linspace(*x_span, samples)
        lines.append(np.stack([x, np.zeros_like(x), np.full_like(x, z)], 1))
    rng.shuffle(lines)
    h, w = mask.shape
    for P3 in lines:
        pts = view.P(P3)
        ok = [(0 <= p[0] < w and 0 <= p[1] < h and mask[int(p[1]), int(p[0])] > 0.5) for p in pts]
        if not any(ok):
            continue
        idx = np.nonzero(ok)[0]
        i0, i1 = max(0, idx[0] - 1), min(len(pts) - 1, idx[-1] + 1)
        if i1 - i0 < 1:
            continue
        inner = [i for i in range(i0, i1 + 1) if ok[i]]
        cols = [color_at(P3[min(max(i, inner[0]), inner[-1])]) for i in range(i0, i1 + 1)]
        if vary is not None:
            f = vary(rng)
            cols = [f(c) for c in cols]
        board.stroke(pts[i0:i1 + 1], brush, cols, wobble=wobble, **kw)
