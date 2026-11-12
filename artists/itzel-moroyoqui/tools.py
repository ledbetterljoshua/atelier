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


# --- under a tree ------------------------------------------------------------------------------------
SUN_DISC = 0.00465   # the sun's radius seen from here, radians


class Canopy:
    """Leaves at one height over the ground, as a grid of how open each bit of them is (1 a gap,
    0 a leaf), cell metres square, its first cell at (x0, z0). A gap smaller than the sun's disc
    puts down a picture of the sun, not of the gap, so the grid is spread by the disc on its way
    down: an ellipse, longer along the way the sun is coming from."""

    def __init__(self, openness, x0, z0, cell, height, sun):
        from scipy.signal import fftconvolve
        sun = np.asarray(sun, dtype=np.float64)
        sun = sun / np.linalg.norm(sun)
        self.h, self.x0, self.z0, self.cell = height, x0, z0, cell
        self.k = sun[[0, 2]] / sun[1]
        d = height / sun[1]
        ra = d * SUN_DISC / cell
        rl = ra / sun[1]
        az = sun[[0, 2]] / (np.hypot(sun[0], sun[2]) + 1e-12)
        n = int(np.ceil(rl)) + 1
        gz, gx = np.mgrid[-n:n + 1, -n:n + 1].astype(np.float64)
        along = gx * az[0] + gz * az[1]
        across = -gx * az[1] + gz * az[0]
        kern = ((along / rl) ** 2 + (across / ra) ** 2 <= 1.0).astype(np.float64)
        self.L = np.clip(fftconvolve(openness, kern / kern.sum(), mode="same"), 0, 1)

    def at(self, P):
        """Where on the canopy grid the sun's ray from P passes, in metres (x, z)."""
        P = np.asarray(P, dtype=np.float64)
        return P[..., [0, 2]] + (self.h - P[..., 1:2]) * self.k

    def light(self, P):
        """How much of the sun's disc each point sees through the leaves, 0..1."""
        from scipy.ndimage import map_coordinates
        q = self.at(P)
        gx = (q[..., 0] - self.x0) / self.cell
        gz = (q[..., 1] - self.z0) / self.cell
        return map_coordinates(self.L, [gz.ravel(), gx.ravel()], order=1, mode="nearest").reshape(gx.shape)


def to_ground(P, sun):
    """Where a point's shadow falls on the pavement, along the sun."""
    P = np.asarray(P, dtype=np.float64)
    return P[..., [0, 2]] - P[..., 1:2] * (np.asarray(sun)[[0, 2]] / sun[1])


# Shapes as distances, for anything round: an animal, a bowl. Negative inside.
def sd_ellipsoid(p, c, r):
    q = (p - c) / r
    k0 = np.linalg.norm(q, axis=-1)
    k1 = np.linalg.norm(q / r, axis=-1)
    return k0 * (k0 - 1.0) / (k1 + 1e-9)


def sd_capsule(p, a, b, r):
    pa, ba = p - a, b - a
    h = np.clip((pa @ ba) / (ba @ ba), 0, 1)
    return np.linalg.norm(pa - h[..., None] * ba, axis=-1) - r


def smin(a, b, k):
    h = np.clip(0.5 + 0.5 * (b - a) / k, 0, 1)
    return b * (1 - h) + a * h - k * h * (1 - h)


def march(eye, rays, sdf, t0, t1, steps=90, eps=4e-4):
    """Distance along each ray to the surface of sdf, inf where it misses. rays is (N, 3)."""
    eye = np.asarray(eye, dtype=np.float64)
    t = np.full(len(rays), float(t0))
    hit = np.zeros(len(rays), bool)
    live = np.ones(len(rays), bool)
    for _ in range(steps):
        idx = np.nonzero(live)[0]
        if len(idx) == 0:
            break
        d = sdf((eye[idx] if eye.ndim == 2 else eye) + rays[idx] * t[idx, None])
        h = d < eps
        hit[idx[h]] = True
        t[idx[~h]] += np.maximum(d[~h] * 0.85, eps * 0.5)
        live[idx] = ~h & (t[idx] < t1)
    return np.where(hit, t, np.inf)


def blocked(P, toward, sdf, start=0.006, far=1.0, steps=40, eps=5e-4):
    """Whether something in sdf stands between each point and the direction `toward`."""
    P = np.asarray(P, dtype=np.float64)
    toward = np.asarray(toward, dtype=np.float64)
    o = P + toward * start
    return np.isfinite(march(o, np.broadcast_to(toward, P.shape).copy(), sdf, 0.0, far, steps, eps))


def normals(sdf, P, e=1e-3):
    g = np.stack([sdf(P + np.array(v) * e) - sdf(P - np.array(v) * e)
                  for v in ((1, 0, 0), (0, 1, 0), (0, 0, 1))], -1)
    return g / (np.linalg.norm(g, axis=-1, keepdims=True) + 1e-12)


def loads(board, view, G, mask, brush, mix_at, n, length, angle, rng, width_m=None, jitter=0.15,
          wobble=1.5, **kw):
    """n brushloads laid on the ground: each stroke is placed and turned in metres and is one mix
    from start to finish, asked of mix_at(p, rng) once, where the stroke is centred. The centres
    are drawn from the mask's pixels (G holds the ground point under every pixel), so every load
    lands where it is wanted and the tape makes its ends."""
    ys, xs = np.nonzero(mask > 0.5)
    if len(xs) == 0:
        return 0
    for i in rng.integers(len(xs), size=n):
        c = G[ys[i], xs[i]].copy()
        c[1] = 0.0
        a = (angle(c[0], c[2]) if callable(angle) else angle) + rng.normal(0, jitter)
        L = length * rng.uniform(0.7, 1.3)
        d = np.array([np.cos(a), 0.0, np.sin(a)]) * L / 2
        pts = view.P(np.array([c - d, c - d * 0.33, c + d * 0.33, c + d]))
        b = brush if width_m is None else brush.but(width=max(3.0, width_m * view.scale_at(c)))
        board.stroke(pts, b, mix_at(c, rng), wobble=wobble, **kw)
    return n


def fur(board, view, P, N, D, mask, brush, mix_at, rng, n, length, curl=0.0, wobble=0.5, **kw):
    """Strokes the way the hair lies. P, N, D hold the surface point, its normal and the way the
    hair grows under every pixel. Each stroke starts at a pixel of the mask, runs `length` metres
    along the hair over the surface (curl bends it round toward the normal's far side), and is one
    mix, asked of mix_at(y, x, rng) where it starts."""
    ys, xs = np.nonzero(mask > 0.5)
    if len(xs) == 0:
        return 0
    for i in rng.integers(len(xs), size=n):
        y, x = ys[i], xs[i]
        p, nn, d = P[y, x], N[y, x], D[y, x]
        d = d - (d @ nn) * nn
        d /= np.linalg.norm(d) + 1e-9
        L = length * rng.uniform(0.7, 1.3)
        s = np.linspace(0, 1, 4)[:, None]
        pts3 = p + d * (s * L) - nn * (curl * (s * L) ** 2 / max(L, 1e-6))
        board.stroke(view.P(pts3), brush, mix_at(y, x, rng), wobble=wobble, **kw)
    return n
