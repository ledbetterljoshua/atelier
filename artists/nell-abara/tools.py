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


# --- added for 002: a door that is not shut, a floor that is still wet ------------------------

def crosses(plane, S, Q):
    """Which of the segments S[i] -> Q pass through this rectangle."""
    d = Q[None, :] - S
    den = d @ plane.n
    den = np.where(np.abs(den) < 1e-12, 1e-12, den)
    t = ((plane.O - S) @ plane.n) / den
    X = S + d * t[:, None]
    rel = X - plane.O
    u, v = rel @ plane.U / plane.uu, rel @ plane.V / plane.vv
    return (t > 0) & (t < 1) & (u >= 0) & (u <= 1) & (v >= 0) & (v <= 1)


class Patches:
    """Many small lit squares at once: S positions, n facing, rad radiance, dA area.

    aperture: the light only counts if it gets out through this rectangle (a door gap).
    blockers: [(plane, transmit)] things standing in the way; transmit 0 is solid, 0.3 a tea towel.
    """

    def __init__(self, S, n, rad, dA, aperture=None, blockers=()):
        self.S = np.asarray(S, dtype=np.float64)
        self.n = np.asarray(n, dtype=np.float64)
        self.rad = np.asarray(rad, dtype=np.float64)
        self.dA = np.broadcast_to(np.asarray(dA, dtype=np.float64), (len(self.S),)).copy()
        self.aperture, self.blockers = aperture, list(blockers)

    @classmethod
    def on(cls, plane, radiance, nu, nv, facing=None, rng=None, **kw):
        """Grid a rectangle into patches. radiance may be a function of the patch centre.

        With rng, each sample moves somewhere inside its cell, so a narrow gap seen through does not
        pick out the rows of the grid as stripes of light.
        """
        uu, vv = np.meshgrid(np.arange(nu) + 0.5, np.arange(nv) + 0.5, indexing="ij")
        uu, vv = uu.ravel(), vv.ravel()
        if rng is not None:
            uu, vv = uu + rng.uniform(-0.5, 0.5, uu.shape), vv + rng.uniform(-0.5, 0.5, vv.shape)
        S = np.array([plane.at(u / nu, v / nv) for u, v in zip(uu, vv)])
        n = np.tile(v3(*facing) if facing is not None else plane.n, (len(S), 1))
        rad = np.array([radiance(s) if callable(radiance) else radiance for s in S], dtype=np.float64)
        dA = np.linalg.norm(np.cross(plane.U, plane.V)) / len(S)
        return cls(S, n, rad, dA, **kw)

    def __add__(self, other):
        out = Patches(np.vstack([self.S, other.S]), np.vstack([self.n, other.n]),
                      np.vstack([self.rad, other.rad]), np.concatenate([self.dA, other.dA]),
                      self.aperture, self.blockers)
        return out

    def onto(self, P, N, near=0.03):
        P, N = np.asarray(P, dtype=np.float64), np.asarray(N, dtype=np.float64)
        l = self.S - P
        d2 = np.maximum((l * l).sum(1), near)
        l = l / np.sqrt(d2)[:, None]
        cp = l @ N
        cl = -(l * self.n).sum(1)
        w = np.where((cp > 0) & (cl > 0), self.dA * cp * cl / (np.pi * d2), 0.0)
        if self.aperture is not None:
            w = w * crosses(self.aperture, self.S, P)
        for plane, tr in self.blockers:
            w = np.where(crosses(plane, self.S, P), w * tr, w)
        return (self.rad * w[:, None]).sum(0)


def lay_flow(board, view, plane, brush, shade, field, length=110.0, cover=2.0, wobble=1.0, zref=5.0,
             shrink=0.5, tape=True, where=None, feather=1.2, steps=5, pressure=1.0):
    """Like lay(), but each stroke follows field(P) across the plane, so it can bend (a mop arc)."""
    rng = board.rng
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
        d0 = field(P)
        e = view.P(np.array([P - d0 * 0.05, P + d0 * 0.05]))
        px_per_m = max(np.hypot(*(e[1] - e[0])) / 0.1, 1e-3)
        Lm = length * k * rng.uniform(0.6, 1.25) / px_per_m
        h = Lm / (2 * steps)
        path = [P]
        for sgn in (1, -1):
            q = P.copy()
            side = []
            for _ in range(steps):
                d = field(q)
                q2 = q + sgn * d * h
                u, v = plane.uv(q2)
                if not (0 <= u <= 1 and 0 <= v <= 1) or q2[2] < 0.6:
                    break
                q = q2
                side.append(q)
            path = (path + side) if sgn > 0 else (side[::-1] + path)
        if len(path) < 2:
            continue
        path = np.array(path)
        if rng.random() < 0.5:
            path = path[::-1]
        board.stroke(view.P(path), brush.but(width=brush.width * k), shade(P), wobble=wobble * k,
                     pressure=pressure)
        n += 1
    if tape:
        board.untape()
    return n


def floor_at(view, sx, sy, y=0.0):
    """The point on the floor (height y) that a spot on the board is looking at."""
    d = view.ray(np.asarray(sx, dtype=np.float64), np.asarray(sy, dtype=np.float64))
    t = (y - view.eye[1]) / np.minimum(d[..., 1], -1e-6)
    return view.eye + d * t[..., None]


def wet_mirror(board, view, sources, wet, brush, smear=(18.0, 0.35), floor_ok=None, fresnel=(0.02, 5.0),
               spread=0.004, blur=0.03, gain=1.0, k=2.2, rough=None, threads=3, thread=(0.25, 0.35)):
    """What a wet floor gives back. sources: [(P, radiance)] lit points standing above the floor.

    Each source is mirrored through the floor and painted where its mirror image lands. How bright
    it comes back (Fresnel for water, times how wet the floor is there) goes into the colour, not
    the opacity, so a hundred overlapping touches settle on the right value instead of piling up
    to white. The higher the source stands above the floor the wider its image spreads, and each
    touch is smeared toward the eye until the floor under it stops being wet, so a drying floor
    breaks the image into pieces and a dry one gives nothing back. rough(F) scales the spread: a
    standing puddle is a mirror, a mopped floor is not. The spread is laid as a few thin threads
    side by side rather than one fat touch, because lino streaks along the line of sight.
    """
    rng = board.rng
    n = 0
    for P, rad in sources:
        M = v3(P[0] + rng.normal(0, spread), -P[1], P[2] + rng.normal(0, spread))
        sx, sy = view.P(M)
        F = floor_at(view, sx, sy)
        if F[2] <= 0.6 or (floor_ok is not None and not floor_ok(F)):
            continue
        w = wet(F)
        if w <= 0.03:
            continue
        cos_i = view.eye[1] / np.linalg.norm(F - view.eye)
        R = fresnel[0] + (1 - fresnel[0]) * (1 - cos_i) ** fresnel[1]
        col = tone(np.asarray(rad) * R * w * gain, k)
        if col.max() < 0.012:
            continue
        L = smear[0] * (1 + smear[1] * (sy - view.vy) / 100.0) * rng.uniform(0.6, 1.4)
        y1 = sy + L
        for yy in np.linspace(sy, sy + L, 7)[1:]:
            if wet(floor_at(view, sx, yy)) < 0.35 * w:
                y1 = yy
                break
        y0 = sy - L * 0.2
        for yy in np.linspace(sy, sy - L * 0.2, 3)[1:]:
            if wet(floor_at(view, sx, yy)) < 0.35 * w:
                y0 = yy
                break
        if y1 - y0 < 3:
            continue
        bl = blur * P[1] * view.ppm(F[2]) * (rough(F) if rough is not None else 1.0)
        for _ in range(threads):
            x = sx + rng.normal(0, thread[1] * bl)
            board.stroke([(x, y0), (x + rng.normal(0, 0.8), y1)], brush.but(width=brush.width + thread[0] * bl), col,
                         smooth=False)
            n += 1
    return n


class Hang:
    """A cloth hanging from a straight edge: u runs along the edge, v falls from it (0 top, 1 hem).

    top_a, top_b: the edge it hangs from. drop: length in metres. out: which way the face looks.
    sag(u): extra drop of the hem; folds: [(u, depth, width)] where the cloth swings toward or away
    from you as it falls.
    """

    def __init__(self, top_a, top_b, drop, out, sag=None, folds=(), lean=0.0):
        self.a, self.b, self.drop = v3(*top_a), v3(*top_b), drop
        self.out = v3(*out) / np.linalg.norm(out)
        self.sag = sag or (lambda u: 0.0)
        self.folds, self.lean = list(folds), lean

    def at(self, u, v):
        top = self.a + (self.b - self.a) * u
        L = self.drop + self.sag(u)
        off = 0.0
        for fu, depth, w in self.folds:
            off += depth * np.exp(-((u - fu) / w) ** 2) * min(1.0, v * 3)
        return top + v3(0, -L * v, 0) + self.out * (off + self.lean * v * v)

    def normal(self, u, v, e=1e-3):
        du = self.at(min(u + e, 1), v) - self.at(max(u - e, 0), v)
        dv = self.at(u, min(v + e, 1)) - self.at(u, max(v - e, 0))
        n = np.cross(dv, du)
        n /= np.linalg.norm(n) + 1e-12
        return n if n @ self.out >= 0 else -n

    def outline(self, view, n=24):
        us = np.linspace(0, 1, n)
        top = [self.at(u, 0) for u in us]
        right = [self.at(1, v) for v in np.linspace(0, 1, n)]
        hem = [self.at(u, 1) for u in us[::-1]]
        left = [self.at(0, v) for v in np.linspace(1, 0, n)]
        return view.P(np.array(top + right + hem + left))
