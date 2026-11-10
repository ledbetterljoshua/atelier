"""Nell Abara's working kit: a room she can stand in, and light that behaves.

Nothing here draws a picture and copies it. A View turns a point in the room into a point on the
board; a Plane is a wall, floor or ceiling she can lay strokes along; lights tell her how much of
the lit thing reaches a given spot, so every stroke is mixed for where it lands.
"""
import numpy as np

from engine import paths


def v3(*a):
    return np.array(a, dtype=np.float64)


class View:
    def __init__(self, W, H, f, vx, vy, eye):
        self.W, self.H, self.f, self.vx, self.vy = W, H, f, vx, vy
        self.eye = v3(*eye)

    def P(self, p):
        p = np.asarray(p, dtype=np.float64) - self.eye
        z = np.maximum(p[..., 2], 1e-3)
        return np.stack([self.vx + self.f * p[..., 0] / z, self.vy - self.f * p[..., 1] / z], axis=-1)

    def ppm(self, z):
        """Pixels per metre at depth z."""
        return self.f / max(z - self.eye[2], 1e-3)

    def ray(self, sx, sy):
        return np.stack([(sx - self.vx) / self.f, -(sy - self.vy) / self.f, np.ones_like(sx)], axis=-1)


class Plane:
    """A rectangle in the room: origin plus two edge vectors."""

    def __init__(self, O, U, V):
        self.O, self.U, self.V = v3(*O), v3(*U), v3(*V)
        n = np.cross(self.U, self.V)
        self.n = n / np.linalg.norm(n)
        self.uu, self.vv = self.U @ self.U, self.V @ self.V

    def at(self, u, v):
        return self.O + self.U * u + self.V * v

    def uv(self, P):
        d = P - self.O
        return d @ self.U / self.uu, d @ self.V / self.vv

    def facing(self, eye):
        """Normal turned toward the viewer."""
        c = self.O + 0.5 * self.U + 0.5 * self.V
        return self.n if (eye - c) @ self.n > 0 else -self.n

    def screen_poly(self, view, znear=0.6):
        pts = [self.at(0, 0), self.at(1, 0), self.at(1, 1), self.at(0, 1)]
        out = []
        for i in range(4):
            a, b = pts[i], pts[(i + 1) % 4]
            ain, bin_ = a[2] > znear, b[2] > znear
            if ain:
                out.append(a)
            if ain != bin_:
                t = (znear - a[2]) / (b[2] - a[2])
                out.append(a + t * (b - a))
        return view.P(np.array(out)) if len(out) >= 3 else None

    def sample(self, view, rng, n_target, margin=0.02):
        """Random points on the plane, even on the board rather than even in the room."""
        poly = self.screen_poly(view)
        if poly is None:
            return np.zeros((0, 3)), 0.0
        m = 50   # start strokes a little off the board too, or its edges come out thin
        x0, y0 = np.clip(poly.min(0), [-m, -m], [view.W + m, view.H + m])
        x1, y1 = np.clip(poly.max(0), [-m, -m], [view.W + m, view.H + m])
        if x1 - x0 < 2 or y1 - y0 < 2:
            return np.zeros((0, 3)), 0.0
        M = 4000
        sx, sy = rng.uniform(x0, x1, M), rng.uniform(y0, y1, M)
        d = view.ray(sx, sy)
        denom = d @ self.n
        denom = np.where(np.abs(denom) < 1e-9, 1e-9, denom)
        t = ((self.O - view.eye) @ self.n) / denom
        P = view.eye + d * t[:, None]
        rel = P - self.O
        u, v = rel @ self.U / self.uu, rel @ self.V / self.vv
        ok = (t > 0) & (u > margin) & (u < 1 - margin) & (v > margin) & (v < 1 - margin)
        area = (x1 - x0) * (y1 - y0) * ok.mean()
        P = P[ok]
        want = int(n_target(area)) if callable(n_target) else n_target
        while len(P) < want and ok.any():
            P = np.vstack([P, P + rng.normal(0, 1e-3, P.shape)])
        return P[:want], area


class RectLight:
    def __init__(self, plane, radiance, nu=3, nv=3, facing=None):
        self.plane = plane
        self.rad = v3(*radiance)
        self.n = v3(*facing) if facing is not None else plane.n
        us, vs = (np.arange(nu) + 0.5) / nu, (np.arange(nv) + 0.5) / nv
        self.S = np.array([plane.at(u, v) for u in us for v in vs])
        self.dA = np.linalg.norm(np.cross(plane.U, plane.V)) / len(self.S)

    def onto(self, P, N, blocked=None):
        """Light arriving at P on a surface facing N. blocked(S, P) -> True hides one sample."""
        out = np.zeros(3)
        for S in self.S:
            l = S - P
            d2 = l @ l
            d = np.sqrt(d2)
            l = l / d
            cp, cl = N @ l, -(self.n @ l)
            if cp <= 0 or cl <= 0:
                continue
            if blocked is not None and blocked(S, P):
                continue
            out += self.rad * (self.dA * cp * cl / (np.pi * d2))
        return out


def tone(c, k=2.2):
    """Radiance to paint. Soft shoulder so the lit thing can go near white without going flat."""
    return np.maximum(1.0 - np.exp(-k * np.asarray(c)), 0.004)


def lay(board, view, plane, brush, shade, direction, length=110.0, cover=2.0, wobble=1.5,
        zref=5.0, shrink=0.5, tape=True, where=None, color2=None, feather=1.2, max_m=6.0):
    """Lay strokes along a plane. direction is a vector in the room; shade(P) mixes the colour."""
    rng = board.rng
    dvec = v3(*direction)
    dvec /= np.linalg.norm(dvec)
    if tape:
        poly = plane.screen_poly(view)
        if poly is None:
            return 0
        board.tape(poly, feather=feather)
    pts, area = plane.sample(view, rng, lambda a: a * cover / (length * brush.width) + 1)
    n = 0
    for P in pts:
        if where is not None and not where(P):
            continue
        z = P[2] - view.eye[2]
        k = min(1.6, max(0.25, (zref / z) ** shrink))
        # choose a length in the room that comes out the wanted length on the board,
        # however steeply this plane runs away from the eye
        e = view.P(np.array([P - dvec * 0.05, P + dvec * 0.05]))
        px_per_m = max(np.hypot(*(e[1] - e[0])) / 0.1, 1e-3)
        Lm = min(length * k * rng.uniform(0.6, 1.25) / px_per_m, max_m)
        a, b = P - dvec * Lm / 2, P + dvec * Lm / 2
        for _ in range(6):
            ua, va = plane.uv(a)
            ub, vb = plane.uv(b)
            if min(ua, va, ub, vb) >= 0 and max(ua, va, ub, vb) <= 1 and min(a[2], b[2]) > 0.6:
                break
            a, b = P + (a - P) * 0.6, P + (b - P) * 0.6
        if rng.random() < 0.5:
            a, b = b, a
        c = shade(P)
        board.stroke(view.P(np.array([a, b])), brush.but(width=brush.width * k), c,
                     color2=None if color2 is None else color2(P), wobble=wobble * k)
        n += 1
    if tape:
        board.untape()
    return n


def line3(board, view, a, b, brush, color, wobble=0.0, **kw):
    board.stroke(view.P(np.array([a, b], dtype=np.float64)), brush, color, wobble=wobble, **kw)


def quad(view, pts):
    return view.P(np.array(pts, dtype=np.float64))
