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
        zref=5.0, shrink=0.5, tape=True, where=None, color2=None, feather=1.2, max_m=6.0, along=0,
        tape_mode="replace"):
    """Lay strokes along a plane. direction is a vector in the room; shade(P) mixes the colour.

    along=n mixes the colour afresh at n points down each stroke, so one long stroke can run from
    the light into the dark instead of being cut into pieces that each carry one value."""
    rng = board.rng
    dvec = v3(*direction)
    dvec /= np.linalg.norm(dvec)
    if tape:
        poly = plane.screen_poly(view)
        if poly is None:
            return 0
        board.tape(poly, feather=feather, mode=tape_mode)
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
        c = shade(P) if along < 2 else [shade(a + (b - a) * t) for t in np.linspace(0, 1, along)]
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

    def __init__(self, S, n, rad, dA, aperture=None, blockers=(), occlude=None):
        self.S = np.asarray(S, dtype=np.float64)
        self.n = np.asarray(n, dtype=np.float64)
        self.rad = np.asarray(rad, dtype=np.float64)
        self.dA = np.broadcast_to(np.asarray(dA, dtype=np.float64), (len(self.S),)).copy()
        self.aperture, self.blockers = aperture, list(blockers)
        self.occlude = occlude     # occlude(S, P) -> how much of each sample's light gets to P, 0..1

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
                      self.aperture, self.blockers, self.occlude)
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
        if self.occlude is not None:
            live = w > 0
            if live.any():
                w = w.copy()
                w[live] *= self.occlude(self.S[live], P)
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


# --- added for 003: a flight of stairs, and a room keyed to the one light in it ----------------

def in_the_way(S, P, solid, n=56, eps=0.004):
    """For each light sample S, 1 if nothing solid stands between it and P, else 0.

    solid(X, Y, Z) -> bool. The samples crowd toward P, where a step's own riser does its shading."""
    S = np.asarray(S, dtype=np.float64)
    d = S - P
    L = np.linalg.norm(d, axis=1, keepdims=True)
    t = eps / L + (1 - eps / L) * np.linspace(0.0, 1.0, n)[None, :] ** 2   # (M, n)
    Q = P[None, None, :] + d[:, None, :] * t[..., None]
    hit = solid(Q[..., 0], Q[..., 1], Q[..., 2]).any(axis=1)
    return np.where(hit, 0.0, 1.0)


class Flight:
    """A straight flight between two walls, climbing away from me (toward +z).

    Riser k (0..n-1) stands at z0 + k*going. Tread k (1..n-1) lies on top of riser k-1 at
    y0 + k*rise. The landing at the head is tread n, and runs back to z_end.
    """

    def __init__(self, x0, x1, z0, rise, going, n, z_end, y0=0.0):
        self.x0, self.x1, self.z0, self.r, self.g, self.n = x0, x1, z0, rise, going, n
        self.z_end, self.y0 = z_end, y0
        self.z_head = z0 + (n - 1) * going

    def top(self, Z):
        """Height of whatever you would stand on at depth Z."""
        Z = np.asarray(Z, dtype=np.float64)
        k = np.clip(np.floor((Z - self.z0) / self.g) + 1, 0, self.n)
        return np.where(Z < self.z0, self.y0, self.y0 + k * self.r)

    def solid(self, X, Y, Z):
        inside = (X > self.x0) & (X < self.x1) & (Z >= self.z0) & (Z <= self.z_end)
        return inside & (Y < self.top(Z) - 1e-6)

    def nosing(self, k):
        """(y, z) of the front edge of tread k; k = n is the edge of the landing."""
        return self.y0 + k * self.r, self.z0 + (k - 1) * self.g

    def pitch_y(self, z):
        """The line through the nosings."""
        return self.y0 + self.r + (np.asarray(z) - self.z0) * self.r / self.g

    def tread(self, k):
        from_z = self.z0 + (k - 1) * self.g
        to_z = self.z_end if k >= self.n else from_z + self.g
        y = self.y0 + k * self.r
        return Plane((self.x0, y, from_z), (self.x1 - self.x0, 0, 0), (0, 0, to_z - from_z))

    def riser(self, k):
        z = self.z0 + k * self.g
        return Plane((self.x0, self.y0 + k * self.r, z), (self.x1 - self.x0, 0, 0), (0, self.r, 0))


def room(c, cap=0.62):
    """Radiance to paint for anything the light falls on. However much light lands on a surface it
    can only crowd up under cap (white knocked back), and does so slowly, so a wall a hand from the
    lamp still steps down to the one beside it. Pure white is kept for the light itself."""
    c = np.maximum(np.asarray(c, dtype=np.float64), 0.0)
    return np.maximum(cap * c / (c + cap), 0.004)


def keyed(light, probe, target, curve=room):
    """One exposure for the whole board, found once: the probe (Q, N, albedo) comes out at target.

    She keys on the thing the picture is about, not on whatever is brightest, and lets curve()
    look after the surfaces near the lamp. Every value keeps its order against every other."""
    Q, N, a = probe
    c = np.asarray(a) * light(Q, N)
    lo, hi = 1e-3, 1e5
    for _ in range(80):
        mid = np.sqrt(lo * hi)
        v = curve(c * mid)
        if 0.2 * v[0] + 0.7 * v[1] + 0.1 * v[2] < target:
            lo = mid
        else:
            hi = mid
    return np.sqrt(lo * hi)


def sweep(board, view, edge0, edge1, n, brush, shade, along=6, overlap=1.7, wobble=0.0, jitter=0.35, min_w=2.0,
          max_w=90.0, where=None):
    """Strokes that go the whole way across a surface, edge to edge, each mixed along its length.

    edge0(t), edge1(t): the two ends of the stroke at t in 0..1, as points in the room. Strokes sit
    at n steps of t; each is as wide on the board as the gap to its neighbour, times overlap, so
    nothing between them shows black. Ends are run past the surface and the tape stops them, so no
    stroke ends in a rounded tip in the middle of a wall. where(t) may skip a stroke.
    """
    rng = board.rng
    out = 0
    for i in range(n):
        t = (i + 0.5 + rng.uniform(-jitter, jitter)) / n
        if where is not None and not where(t):
            continue
        a, b = edge0(t), edge1(t)
        m = (a + b) / 2
        dt = 1.0 / n
        sp = np.hypot(*(view.P((edge0(min(t + dt, 1)) + edge1(min(t + dt, 1))) / 2) - view.P(m)))
        w = float(np.clip(sp * overlap, min_w, max_w))
        qs = [a + (b - a) * s for s in np.linspace(0, 1, along)]
        ends = view.P(np.array([a, b]))
        board.stroke(ends, brush.but(width=w), [shade(q) for q in qs], wobble=wobble)
        out += 1
    return out


# --- added for 004: standing over a machine and looking down into it ----------------------------

class Over(View):
    """A view tipped down by pitch (radians): standing over something, looking down at it.

    Same as View with pitch 0, except depth is measured along the line of sight, so ppm() takes a
    point in the room rather than a depth."""

    def __init__(self, W, H, f, vx, vy, eye, pitch):
        super().__init__(W, H, f, vx, vy, eye)
        c, s = np.cos(pitch), np.sin(pitch)
        self.fw, self.up, self.rt = v3(0, -s, c), v3(0, c, s), v3(1, 0, 0)

    def depth(self, p):
        return (np.asarray(p, dtype=np.float64) - self.eye) @ self.fw

    def P(self, p):
        d = np.asarray(p, dtype=np.float64) - self.eye
        z = np.maximum(d @ self.fw, 1e-3)
        return np.stack([self.vx + self.f * (d @ self.rt) / z, self.vy - self.f * (d @ self.up) / z], axis=-1)

    def ppm(self, p):
        return self.f / max(float(self.depth(p)), 1e-3)

    def ray(self, sx, sy):
        a = (np.asarray(sx, dtype=np.float64) - self.vx) / self.f
        b = -(np.asarray(sy, dtype=np.float64) - self.vy) / self.f
        return a[..., None] * self.rt + b[..., None] * self.up + np.ones_like(a)[..., None] * self.fw


def scrub(board, region, brush, shade, n, length=(260, 600), angle=(0.0, np.pi), along=5, feather=2.0, wobble=0.0):
    """The dark, left as the board. A few long strokes dragged dry across a region at whatever angle
    the arm falls, each mixed along its length from shade(x, y) on the board, so they cross each
    other instead of lining up into cloth. region is a polygon on the board or None for all of it."""
    rng = board.rng
    if region is not None:
        board.tape(region, feather=feather)
        x0, y0 = np.min(region, 0)
        x1, y1 = np.max(region, 0)
    else:
        x0, y0, x1, y1 = 0, 0, board.w, board.h
    for _ in range(n):
        cx, cy = rng.uniform(x0, x1), rng.uniform(y0, y1)
        a = rng.uniform(*angle)
        L = rng.uniform(*length)
        d = np.array([np.cos(a), np.sin(a)]) * L / 2
        pts = np.array([(cx, cy) - d, (cx, cy) + d])
        cols = [shade(*(pts[0] + (pts[1] - pts[0]) * t)) for t in np.linspace(0, 1, along)]
        board.stroke(pts, brush, cols, wobble=wobble)
    if region is not None:
        board.untape()


def radiate(board, view, plane, origin, brush, shade, n, reach=1.6, along=8, wobble=0.0, spread=(0.0, np.pi), r0=(0.0, 0.5)):
    """Strokes that run away from where the light comes from: each starts at a random distance from
    origin (u, v on the plane) and runs out past the plane's edge, where the tape stops it, mixed
    along its length. On a surface with no grain of its own the light is the only thing to follow.
    spread: the range of directions in the plane's (u, v), in radians."""
    rng = board.rng
    ou, ov = origin
    k = np.sqrt(plane.uu / plane.vv)            # so a direction in (u, v) is a direction in the room
    for _ in range(n):
        a = rng.uniform(*spread)
        r = rng.uniform(*r0)
        du, dv = np.cos(a), np.sin(a) * k
        m = np.hypot(du * np.sqrt(plane.uu), dv * np.sqrt(plane.vv)) / np.sqrt(plane.uu)
        du, dv = du / m, dv / m
        qs = [plane.at(ou + du * s, ov + dv * s) for s in np.linspace(r, reach, along)]
        board.stroke(view.P(np.array([qs[0], qs[-1]])), brush, [shade(q) for q in qs], wobble=wobble)
    return n


# --- added for 005: outside, under a lamp of one colour, on a wet road ---------------------------

def one_line(albedo, weight=(0.62, 0.38, 0.0)):
    """How much of a lamp that gives only one colour a surface sends back. Low-pressure sodium is a
    single yellow line: a red, a yellow and a white come back as the same thing at different
    strengths, and a blue comes back as nothing. Returns one number; the lamp gives the colour."""
    a = np.asarray(albedo, dtype=np.float64)
    return float(a @ np.asarray(weight))


def gloss(F, eye, S, rad, dA, n_S, m, fresnel=(0.02, 5.0), N=None):
    """What a wet surface at F gives back to the eye from light samples S (radiance rad, area dA,
    facing n_S): a Beckmann lobe of roughness m. Rough wet tarmac stretches a lamp into a streak
    running at the eye; m near zero is standing water and gives the lamp back whole. m may be a pair
    (across, along): the roughness across the line of sight and along it, since a road's ripples
    and ruts run with the traffic and pull a lamp out further than they spread it."""
    N = v3(0, 1, 0) if N is None else N
    mx, mz = (m, m) if np.ndim(m) == 0 else m
    V = eye - F
    V = V / np.linalg.norm(V)
    co = max(V @ N, 1e-3)
    B = V - N * (V @ N)
    B = B / (np.linalg.norm(B) + 1e-12)
    T = np.cross(N, B)
    L = S - F
    d2 = (L * L).sum(1)
    L = L / np.sqrt(d2)[:, None]
    ci = L @ N
    cl = -(L * n_S).sum(1)
    Hh = L + V
    Hh = Hh / np.linalg.norm(Hh, axis=1, keepdims=True)
    ch = np.clip(Hh @ N, 1e-3, 1.0)
    D = np.exp(-((Hh @ T / ch) ** 2 / (mx * mx) + (Hh @ B / ch) ** 2 / (mz * mz))) / (np.pi * mx * mz * ch ** 4)
    cd = np.clip(Hh @ V, 0, 1)
    Fr = fresnel[0] + (1 - fresnel[0]) * (1 - cd) ** fresnel[1]
    w = np.where((ci > 0) & (cl > 0), rad * dA * cl / d2 * Fr * D / (4 * co), 0.0)
    return float(w.sum())


def cast(view, W, H, L, pts, ground_y=0.0, radius=2.0, blur=1.2):
    """Where solid things stop a small lamp at L reaching the ground: each point of them pushed down
    the ray from L to the ground and found on the board. Returns an (H, W) 0..1 array for tape."""
    from scipy.ndimage import gaussian_filter, maximum_filter
    pts = np.asarray(pts, dtype=np.float64)
    pts = pts[pts[:, 1] < L[1] - 1e-3]
    s = (L[1] - ground_y) / (L[1] - pts[:, 1])
    G = L + (pts - L) * s[:, None]
    return _splat(view, W, H, G, radius, blur)


def mirrored(view, W, H, pts, ground_y=0.0, radius=2.0, blur=(10.0, 1.5)):
    """Where things standing on a wet floor show in it: each point flipped through the floor and
    found on the board, then smeared along the line of sight. An (H, W) 0..1 array for tape."""
    pts = np.asarray(pts, dtype=np.float64).copy()
    pts[:, 1] = 2 * ground_y - pts[:, 1]
    return _splat(view, W, H, pts, radius, blur)


def _splat(view, W, H, pts, radius, blur):
    from scipy.ndimage import gaussian_filter, maximum_filter
    q = view.P(pts)
    ok = (q[:, 0] >= 0) & (q[:, 0] < W) & (q[:, 1] >= 0) & (q[:, 1] < H)
    m = np.zeros((H, W), dtype=np.float32)
    m[q[ok, 1].astype(int), q[ok, 0].astype(int)] = 1.0
    r = max(1, int(round(radius)))
    m = maximum_filter(m, size=2 * r + 1)
    return np.clip(gaussian_filter(m, blur) * 1.6, 0, 1)


def drag(board, x0, x1, y0, y1, n, brush, shade, along=10, lean=0.0, wobble=0.0, where=None, floor=None, probe=60,
         fade=None):
    """Strokes pulled straight down the board, side by side between x0 and x1, from y0 to y1, each
    mixed along its length from shade(x, y). What a wet road does to a light is pull it at you; a
    dry brush pulled the same way leaves the tarmac's grain in it. where(x) may skip a stroke.
    floor: each stroke only runs where shade comes out brighter than this, so the light decides
    where it starts and stops and the dark either side of it is left alone. fade: paint leaves the
    brush in proportion to how bright it is mixed, up to this, so a stroke thins out into the dark."""
    rng = board.rng
    out = 0
    for i in range(n):
        x = x0 + (x1 - x0) * (i + 0.5 + rng.uniform(-0.4, 0.4)) / n
        if where is not None and not where(x):
            continue
        ya, yb = y0 + rng.uniform(-0.04, 0.04) * (y1 - y0), y1 + rng.uniform(-0.04, 0.04) * (y1 - y0)
        if floor is not None:
            ys = np.linspace(ya, yb, probe)
            v = np.array([0.2 * c[0] + 0.7 * c[1] + 0.1 * c[2] for c in (shade(x + lean * (y - ya), y) for y in ys)])
            on = np.where(v > floor * rng.uniform(0.8, 1.25))[0]
            if len(on) < 2:
                continue
            ya, yb = ys[max(on[0] - 1, 0)], ys[min(on[-1] + 1, probe - 1)]
        xs = np.linspace(x, x + lean * (yb - ya), along)
        ys = np.linspace(ya, yb, along)
        cs = [shade(a, b) for a, b in zip(xs, ys)]
        op = None
        if fade is not None:
            op = [float(np.clip((0.2 * c[0] + 0.7 * c[1] + 0.1 * c[2]) / fade, 0, 1)) for c in cs]
        board.stroke(np.array([(xs[0], ya), (xs[-1], yb)]), brush, cs, wobble=wobble, opacity=op)
        out += 1
    return out
