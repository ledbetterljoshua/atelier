"""Paths a hand might take. Everything is an (N, 2) array of x, y in pixels."""
import numpy as np


def chaikin(pts, rounds=2):
    pts = np.asarray(pts, dtype=np.float64)
    for _ in range(rounds):
        if len(pts) < 3:
            break
        q = 0.75 * pts[:-1] + 0.25 * pts[1:]
        r = 0.25 * pts[:-1] + 0.75 * pts[1:]
        mid = np.empty((2 * len(q), 2))
        mid[0::2], mid[1::2] = q, r
        pts = np.vstack([pts[:1], mid, pts[-1:]])
    return pts


def resample(pts, spacing):
    pts = np.asarray(pts, dtype=np.float64)
    seg = np.hypot(*np.diff(pts, axis=0).T)
    s = np.concatenate([[0.0], np.cumsum(seg)])
    total = s[-1]
    if total < 1e-6:
        return pts[:1].copy(), 0.0
    n = max(2, int(total / spacing) + 1)
    t = np.linspace(0.0, total, n)
    return np.stack([np.interp(t, s, pts[:, 0]), np.interp(t, s, pts[:, 1])], axis=1), total


def line(a, b):
    return np.array([a, b], dtype=np.float64)


def wobble(pts, rng, amp, wavelength=60.0):
    """Push a path off true with slow sideways drift, the way an unsupported arm does."""
    if amp <= 0:
        return np.asarray(pts, dtype=np.float64)
    p, total = resample(pts, max(2.0, wavelength / 6))
    if len(p) < 3:
        return p
    k = max(2, int(total / wavelength) + 2)
    ctrl = rng.normal(0, amp, k)
    off = np.interp(np.linspace(0, k - 1, len(p)), np.arange(k), ctrl)
    d = np.gradient(p, axis=0)
    n = np.stack([-d[:, 1], d[:, 0]], axis=1)
    n /= np.linalg.norm(n, axis=1, keepdims=True) + 1e-9
    return p + n * off[:, None]


def arc(cx, cy, r, a0, a1, n=24):
    a = np.linspace(a0, a1, n)
    return np.stack([cx + r * np.cos(a), cy + r * np.sin(a)], axis=1)


def hatch(poly, angle, spacing, rng=None, jitter=0.0, inset=0.0):
    """Parallel segments that fill a polygon. Returns a list of (a, b) endpoints."""
    poly = np.asarray(poly, dtype=np.float64)
    ca, sa = np.cos(-angle), np.sin(-angle)
    R = np.array([[ca, -sa], [sa, ca]])
    q = poly @ R.T
    y0, y1 = q[:, 1].min(), q[:, 1].max()
    out = []
    y = y0 + spacing * 0.5
    while y < y1:
        yy = y + (rng.normal(0, jitter * spacing) if rng is not None and jitter else 0.0)
        xs = []
        for i in range(len(q)):
            (xa, ya), (xb, yb) = q[i], q[(i + 1) % len(q)]
            if (ya <= yy < yb) or (yb <= yy < ya):
                xs.append(xa + (yy - ya) * (xb - xa) / (yb - ya))
        xs.sort()
        for j in range(0, len(xs) - 1, 2):
            xa, xb = xs[j] + inset, xs[j + 1] - inset
            if xb - xa > 1.0:
                seg = np.array([[xa, yy], [xb, yy]]) @ R
                out.append((seg[0], seg[1]))
        y += spacing
    return out
