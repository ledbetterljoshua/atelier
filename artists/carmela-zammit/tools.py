"""Carmela Zammit's working kit: a roof she can stand on, cloth the wind has hold of, and a low sun
behind it.

A Camera turns a point on the roof into a point on the board. A Sheet is one piece of washing as the
wind holds it: a surface she can ask for any point and the way it faces, so strokes can run down the
cloth from the pegs or round the belly. Light on cloth is worked out at the point a stroke lands:
skylight on the side facing her, and sun coming through from behind, less where something else stands
between that point and the sun.
"""
import numpy as np
from scipy.ndimage import gaussian_filter

from engine import ground


def v3(*a):
    return np.array(a, dtype=np.float64)


def unit(a):
    a = np.asarray(a, dtype=np.float64)
    return a / (np.linalg.norm(a, axis=-1, keepdims=True) + 1e-12)


# --- the support ---------------------------------------------------------------------------------

def sheeting(w, h, rng, darns=()):
    """Condemned hotel cotton, sized and stretched. Fine even weave, and the laundry's own darns,
    which stand up off the cloth and catch a dry brush first."""
    t = ground.linen(w, h, rng, pitch=3.1) * 0.8 + 0.2 * ground.fbm(w, h, rng, base=30, octaves=3)
    y, x = np.mgrid[0:h, 0:w].astype(np.float32)
    for cx, cy, rw, rh in darns:
        inside = (np.abs(x - cx) < rw) & (np.abs(y - cy) < rh)
        edge = np.clip(1 - np.maximum(np.abs(x - cx) / rw, np.abs(y - cy) / rh), 0, 0.15) / 0.15
        cross = 0.5 + 0.5 * np.sin(2 * np.pi * (x - cx) / 5.0) * np.sin(2 * np.pi * (y - cy) / 5.0)
        t = np.where(inside, t * 0.4 + 0.45 + 0.3 * cross * edge, t)
    t = gaussian_filter(t, 0.5)
    return ((t - t.min()) / (t.max() - t.min())).astype(np.float32)


# --- where she stands ------------------------------------------------------------------------------

class Camera:
    """A pinhole at eye height, tipped up or down by pitch (radians, up is positive)."""

    def __init__(self, W, H, f, eye, pitch=0.0, cx=None, cy=None):
        self.W, self.H, self.f = W, H, f
        self.eye = v3(*eye)
        self.cx = W / 2 if cx is None else cx
        self.cy = H / 2 if cy is None else cy
        self.cp, self.sp = np.cos(pitch), np.sin(pitch)

    def P(self, p):
        d = np.asarray(p, dtype=np.float64) - self.eye
        y = d[..., 1] * self.cp - d[..., 2] * self.sp
        z = np.maximum(d[..., 1] * self.sp + d[..., 2] * self.cp, 1e-3)
        return np.stack([self.cx + self.f * d[..., 0] / z, self.cy - self.f * y / z], axis=-1)

    def ray(self, sx, sy):
        """World direction through a point on the board."""
        sx, sy = np.asarray(sx, dtype=np.float64), np.asarray(sy, dtype=np.float64)
        x = (sx - self.cx) / self.f
        y = -(sy - self.cy) / self.f
        z = np.ones_like(x)
        wy = y * self.cp + z * self.sp
        wz = -y * self.sp + z * self.cp
        return unit(np.stack([x, wy, wz], axis=-1))

    def on_ground(self, sx, sy, h=0.0):
        """The point on a level surface at height h seen through a point on the board."""
        d = self.ray(sx, sy)
        t = (h - self.eye[1]) / np.minimum(d[..., 1], -1e-6)
        return self.eye + d * t[..., None]


# --- washing ----------------------------------------------------------------------------------------

class Line:
    """A wire between two posts, seen from above as a straight run from a to b (x, z), at height y0
    at the posts and lower by sag in the middle."""

    def __init__(self, a, b, y0, sag):
        self.a, self.b = np.asarray(a, dtype=np.float64), np.asarray(b, dtype=np.float64)
        d = self.b - self.a
        self.span = np.linalg.norm(d)
        self.d = d / self.span
        self.y0, self.sag = y0, sag
        n = np.array([-self.d[1], self.d[0]])     # horizontal normal in (x, z)
        self.n = n if n[1] < 0 else -n             # the side facing the near end of the roof

    def at(self, s):
        s = np.asarray(s, dtype=np.float64)
        xz = self.a + self.d * s[..., None]
        y = self.y0 - self.sag * (1 - ((s - self.span / 2) / (self.span / 2)) ** 2)
        return np.stack([xz[..., 0], y, xz[..., 1]], axis=-1)

    def pts(self, s0=0.0, s1=None, n=60):
        s1 = self.span if s1 is None else s1
        return self.at(np.linspace(s0, s1, n))


class Sheet:
    """A piece of washing pegged along a Line from s0 metres for width metres.

    u runs along the wire (0..1 across the width), v runs down from the pegs (0..1 to the hem).
    The wind comes from beyond the line, so the cloth bellies toward her, the hem lifts and flares.
    """

    def __init__(self, line, s0, width, length, pegs=3, belly=0.35, lift=0.18, flare=0.10,
                 side=0.0, ripple=0.035, fold=0.0, sag=0.035, band=0.0, seed=0):
        self.line, self.s0, self.width, self.length = line, s0, width, length
        self.pegs = pegs
        self.belly, self.lift, self.flare, self.side = belly, lift, flare, side
        self.ripple, self.fold, self.sag, self.band = ripple, fold, sag, band
        r = np.random.default_rng(seed)
        self.ph = r.uniform(0, 2 * np.pi, 6)
        self.fr = r.uniform(3.0, 5.5) * max(width, 0.6) / 1.8

    def pos(self, u, v):
        u = np.asarray(u, dtype=np.float64)
        v = np.asarray(v, dtype=np.float64)
        u, v = np.broadcast_arrays(u, v)
        ph, Ln = self.ph, self.length
        w = np.clip(v, 0.0, 1.1)
        k = (u * (self.pegs - 1)) % 1.0 if self.pegs > 1 else u
        # along the wire
        a = self.s0 + u * self.width
        a = a + self.flare * w ** 2 * (u - 0.5) * 2 + self.side * w ** 2
        a = a + 0.03 * Ln * w ** 2 * np.sin(2 * np.pi * (1.6 * v + 0.7 * u) + ph[3])
        base = self.line.at(np.clip(a, -2, self.line.span + 2))
        # down
        drop = self.sag * np.sin(np.pi * k) * (1 - w) + v * Ln
        drop = drop - self.lift * w ** 2.2 - 0.04 * Ln * w ** 3 * np.sin(2 * np.pi * (2.2 * u) + ph[2])
        # out toward her
        shape = np.sin(np.pi * np.clip(u, 0, 1)) ** 0.55
        bel = self.belly * w ** 1.2 * shape * (1 + 0.28 * np.sin(2 * np.pi * (1.1 * u - 0.45 * v) + ph[0]))
        rip = self.ripple * np.sin(2 * np.pi * (self.fr * u + 0.35 * v) + ph[1]) * (0.25 + w)
        pk = np.abs(((u * (self.pegs - 1)) + 0.5) % 1.0 - 0.5) / max(self.pegs - 1, 1)
        peg = -0.05 * np.exp(-(pk / 0.035) ** 2) * (1 - w) ** 2
        fold = self.fold * np.sin(2 * np.pi * (2.0 * u + 1.2 * v) + ph[4]) * w
        out = bel + rip + peg + fold
        n = self.line.n
        return np.stack([base[..., 0] + n[0] * out, base[..., 1] - drop, base[..., 2] + n[1] * out], axis=-1)

    def normal(self, u, v, eye):
        e = 1e-3
        pu = self.pos(u + e, v) - self.pos(u - e, v)
        pv = self.pos(u, v + e) - self.pos(u, v - e)
        n = unit(np.cross(pu, pv))
        to_eye = eye - self.pos(u, v)
        s = np.sign(np.sum(n * to_eye, axis=-1, keepdims=True))
        return n * np.where(s == 0, 1, s)

    def outline(self, cam, n=40):
        t = np.linspace(0, 1, n)
        z, o = np.zeros(n), np.ones(n)
        uv = np.concatenate([np.stack([t, z], 1), np.stack([o, t], 1), np.stack([t[::-1], o], 1),
                             np.stack([z, t[::-1]], 1)])
        return cam.P(self.pos(uv[:, 0], uv[:, 1]))

    def hits(self, P, L):
        """Where the ray from P toward the sun L crosses this cloth, as (u, v), or None.
        The cloth is taken at its mean belly for the crossing, then its outline is checked there."""
        n = np.array([self.line.n[0], 0.0, self.line.n[1]])
        o = self.line.at(self.s0 + self.width / 2) + n * self.belly * 0.5
        den = L @ n
        if abs(den) < 1e-6:
            return None
        t = ((o - P) @ n) / den
        if t < 0.05:
            return None
        Q = P + t * L
        a = (Q[[0, 2]] - self.line.a) @ self.line.d
        u = (a - self.s0) / self.width
        top = self.line.at(a)[1]
        v = (top - Q[1]) / max(self.length - self.lift * 0.6, 1e-3)
        if -0.02 < u < 1.02 and 0 < v < 1:
            return u, v
        return None


class Hang(Sheet):
    """Washing with no wind in it, heavy with damp: it drops straight from the pegs, swags between
    them at the top, and the swags run down into folds that hang to the hem.

    folds is how deep the folds stand (metres), give is how far the wind still moves it."""

    def __init__(self, line, s0, width, length, pegs=3, folds=0.05, give=0.02, sag=0.05, droop=0.03,
                 band=0.0, seed=0):
        super().__init__(line, s0, width, length, pegs=pegs, belly=give, lift=0.0, flare=0.0,
                         ripple=0.0, sag=sag, band=band, seed=seed)
        r = np.random.default_rng(seed + 1000)
        span = max(pegs - 1, 1)
        # a fold per swag, and finer ones between, at frequencies tied to where the pegs are
        self.fk = np.array([span, 2 * span + r.uniform(-0.4, 0.4), 3.3 * span + r.uniform(-0.6, 0.6),
                            r.uniform(3.5, 5.0) * width])
        self.fa = folds * np.array([1.0, 0.5, 0.22, 0.07]) * r.uniform(0.8, 1.2, 4)   # wet cloth: few, deep
        self.fp = r.uniform(0, 2 * np.pi, 4)
        self.fp[0] = np.pi                       # the deepest fold hangs from the middle of each swag
        self.fd = r.normal(0, 0.06, 4)           # folds drift a little sideways as they go down
        self.droop = droop

    def crease(self, u, v):
        """How far the cloth stands out of its own mean surface here: + toward her, - into a fold."""
        u, v = np.broadcast_arrays(np.asarray(u, dtype=np.float64), np.asarray(v, dtype=np.float64))
        w = np.clip(v, 0.0, 1.1)
        env = 0.35 + 0.65 * np.clip(w / 0.35, 0, 1) ** 0.7
        f = np.zeros_like(u)
        for k, a, p, d in zip(self.fk, self.fa, self.fp, self.fd):
            f += a * np.cos(2 * np.pi * k * (u + d * w) + p)
        return f * env * (1 - (1 - np.sin(np.pi * np.clip(u, 0, 1))) ** 4)   # eases off at the sides

    def pos(self, u, v):
        u = np.asarray(u, dtype=np.float64)
        v = np.asarray(v, dtype=np.float64)
        u, v = np.broadcast_arrays(u, v)
        Ln, ph = self.length, self.ph
        w = np.clip(v, 0.0, 1.1)
        k = (u * (self.pegs - 1)) % 1.0 if self.pegs > 1 else u
        f = self.crease(u, v)
        # the sides come in a little as it hangs
        a = self.s0 + u * self.width - 0.012 * w * (u - 0.5) + 0.01 * np.sin(2 * np.pi * 1.3 * u + ph[3]) * w ** 2
        base = self.line.at(np.clip(a, -2, self.line.span + 2))
        swag = self.sag * np.sin(np.pi * k) * np.clip(1 - w, 0, 1) ** 1.6
        drop = swag + v * Ln + self.droop * w ** 3 * np.sin(2 * np.pi * (1.4 * u) + ph[2])
        out = self.belly * w * np.sin(np.pi * np.clip(u, 0, 1)) ** 0.8 + f
        n = self.line.n
        return np.stack([base[..., 0] + n[0] * out, base[..., 1] - drop, base[..., 2] + n[1] * out], axis=-1)


# --- paint for where it lands ---------------------------------------------------------------------

def tone(c, k=2.0):
    """Light to paint, with a shoulder, so the brightest cloth goes near white without going flat."""
    return np.maximum(1.0 - np.exp(-k * np.asarray(c, dtype=np.float64)), 0.004)


def lay_cloth(board, cam, sheet, brush, shade, along="v", length=90.0, cover=2.0, wobble=1.0,
              where=None, tape=True, feather=1.0, margin=0.02, color2=None, width_fn=None, run=False):
    """Strokes that follow the cloth: down from the pegs (along v) or round the belly (along u).
    shade(u, v) mixes the colour for where each stroke lands. With run, shade gets the stroke's
    points as arrays and returns a colour for each, so one stroke goes from fold into light."""
    rng = board.rng
    poly = sheet.outline(cam)
    if tape:
        board.tape(poly, feather=feather)
    x0, y0 = poly.min(0)
    x1, y1 = poly.max(0)
    area = max((x1 - x0) * (y1 - y0) * 0.8, 1.0)
    n = int(area * cover / (length * brush.width)) + 1
    us = rng.uniform(-margin, 1 + margin, n)
    vs = rng.uniform(-margin, 1 + margin, n)
    count = 0
    for u0, v0 in zip(us, vs):
        if where is not None and not where(u0, v0):
            continue
        e = 0.01
        if along == "v":
            a, b = cam.P(sheet.pos(u0, v0 - e)), cam.P(sheet.pos(u0, v0 + e))
        else:
            a, b = cam.P(sheet.pos(u0 - e, v0)), cam.P(sheet.pos(u0 + e, v0))
        per = max(np.hypot(*(b - a)) / (2 * e), 1e-3)
        half = length * rng.uniform(0.6, 1.2) / per / 2
        s = np.linspace(-half, half, 7)
        if along == "v":
            uu = u0 + s * rng.normal(0, 0.05)
            vv = v0 + s
        else:
            uu = u0 + s
            vv = v0 + s * rng.normal(0, 0.05)
        pts = cam.P(sheet.pos(uu, vv))
        if rng.random() < 0.5:
            pts = pts[::-1]
            if run:
                uu, vv = uu[::-1], vv[::-1]
        c = shade(uu, vv) if run else shade(u0, v0)
        br = brush if width_fn is None else brush.but(width=width_fn(u0, v0))
        board.stroke(pts, br, c, color2=None if color2 is None else color2(u0, v0), wobble=wobble)
        count += 1
    if tape:
        board.untape()
    return count


def lay_screen(board, region, brush, shade, angle=0.0, length=120.0, cover=2.0, wobble=2.0,
               angle_jitter=0.15, where=None, color2=None):
    """Strokes laid in a board region (x0, y0, x1, y1), each mixed for where it lands."""
    rng = board.rng
    x0, y0, x1, y1 = region
    n = int((x1 - x0) * (y1 - y0) * cover / (length * brush.width)) + 1
    count = 0
    for _ in range(n):
        x, y = rng.uniform(x0, x1), rng.uniform(y0, y1)
        if where is not None and not where(x, y):
            continue
        a = (angle(x, y) if callable(angle) else angle) + rng.normal(0, angle_jitter)
        L = length * rng.uniform(0.6, 1.25)
        dx, dy = np.cos(a) * L / 2, np.sin(a) * L / 2
        c = shade(x, y)
        board.stroke([(x - dx, y - dy), (x + dx, y + dy)], brush, c,
                     color2=None if color2 is None else color2(x, y), wobble=wobble)
        count += 1
    return count


# --- a hard wind, and what the washing does to the sun on the roof -------------------------------

class Gust(Sheet):
    """Washing in a hard wind that blows across the roof in direction wind (x, z). Pegged along the
    top, the rest swings out the way the wind goes, more the further from the pegs, and waves run
    down it. throw is how far it swings out at the hem (radians from hanging), flap how much the
    waves turn it, curl how far the free corners at the hem go over."""

    def __init__(self, line, s0, width, length, pegs=3, wind=(-1.0, 0.0), throw=0.9, flap=0.25,
                 curl=0.3, sag=0.04, band=0.0, seed=0):
        super().__init__(line, s0, width, length, pegs=pegs, belly=0.0, lift=0.0, flare=0.0,
                         ripple=0.0, sag=sag, band=band, seed=seed)
        w = np.asarray(wind, dtype=np.float64)
        w = w / np.linalg.norm(w)
        self.wind = np.array([w[0], 0.0, w[1]])
        self.throw, self.flap, self.curl = throw, flap, curl
        r = np.random.default_rng(seed + 2000)
        self.wk = r.uniform(1.2, 2.2), r.uniform(0.9, 1.6)      # how many waves across and down
        self.wp = r.uniform(0, 2 * np.pi, 3)

    def pos(self, u, v):
        u = np.asarray(u, dtype=np.float64)
        v = np.asarray(v, dtype=np.float64)
        u, v = np.broadcast_arrays(u, v)
        K = 8
        s = v[..., None] * (np.arange(K) + 0.5) / K                  # points down the cloth to here
        uu = u[..., None]
        ku, kv = self.wk
        phi = self.throw * (0.3 + 0.7 * np.clip(s, 0, 1.1) ** 0.8)
        phi = phi + self.flap * np.sin(2 * np.pi * (ku * uu - kv * s) + self.wp[0]) * np.clip(s, 0, 1) ** 0.7
        edge = np.clip(1 - 2 * np.minimum(uu, 1 - uu), 0, 1) ** 2   # the free corners
        phi = phi + self.curl * edge * np.clip(s, 0, 1) ** 2
        n3 = np.array([self.line.n[0], 0.0, self.line.n[1]])
        tw = 0.18 * np.sin(2 * np.pi * (0.8 * uu + 0.6 * s) + self.wp[1]) * np.clip(s, 0, 1)
        d = (-np.cos(phi))[..., None] * np.array([0.0, 1.0, 0.0]) + np.sin(phi)[..., None] * self.wind \
            + tw[..., None] * n3
        down = d.mean(axis=-2) * (v * self.length)[..., None]
        k = (u * (self.pegs - 1)) % 1.0 if self.pegs > 1 else u
        a = self.s0 + u * self.width
        base = self.line.at(np.clip(a, -2, self.line.span + 2))
        swag = self.sag * np.sin(np.pi * k) * np.clip(1 - np.clip(v, 0, 1), 0, 1) ** 1.6
        return base + down - np.stack([np.zeros_like(swag), swag, np.zeros_like(swag)], axis=-1)


def cast(cam, W, H, sheets, L, tau=0.35, tau2=0.13, grid=(48, 36), ground_h=0.0):
    """How much of the sun reaches the roof at each point of the board, after the washing: 1 in the
    open, tau behind one thickness of cotton, tau2 behind the hem or the fold over the wire, and the
    product where two pieces stand in the way. Worked out by laying each piece's shadow down on the
    roof along the sun's direction L, a little quad of cloth at a time."""
    from PIL import Image, ImageDraw
    out = np.ones((H, W), dtype=np.float32)
    L = unit(L)
    nu, nv = grid
    U, V = np.meshgrid(np.linspace(0, 1, nu + 1), np.linspace(0, 1, nv + 1))
    for sh in sheets:
        Q = sh.pos(U, V)
        g = Q - L * ((Q[..., 1] - ground_h) / L[1])[..., None]
        p = cam.P(g)
        im = Image.new("L", (W, H), 255)
        d = ImageDraw.Draw(im)
        dbl = (V[:-1, :-1] < sh.band) | (V[:-1, :-1] > 0.96)
        for pass_dbl in (False, True):
            val = int(255 * (tau2 if pass_dbl else tau))
            for j in range(nv):
                for i in range(nu):
                    if pass_dbl and not dbl[j, i]:
                        continue
                    q = [tuple(p[j, i]), tuple(p[j, i + 1]), tuple(p[j + 1, i + 1]), tuple(p[j + 1, i])]
                    d.polygon(q, fill=val)
        out *= np.asarray(im, dtype=np.float32) / 255.0
    return out


def lay_field(board, region, brush, shade, angle=0.0, length=120.0, cover=2.0, wobble=1.0,
              angle_jitter=0.1, where=None, n_pts=6):
    """Like lay_screen, but shade(xs, ys) gets every point of the stroke and returns a colour for
    each, so one stroke can run from sun into shadow and out again."""
    rng = board.rng
    x0, y0, x1, y1 = region
    n = int((x1 - x0) * (y1 - y0) * cover / (length * brush.width)) + 1
    count = 0
    for _ in range(n):
        x, y = rng.uniform(x0, x1), rng.uniform(y0, y1)
        if where is not None and not where(x, y):
            continue
        a = (angle(x, y) if callable(angle) else angle) + rng.normal(0, angle_jitter)
        Ls = length(x, y) if callable(length) else length
        Ls = Ls * rng.uniform(0.6, 1.25)
        t = np.linspace(-0.5, 0.5, n_pts)
        xs, ys = x + np.cos(a) * Ls * t, y + np.sin(a) * Ls * t
        board.stroke(np.stack([xs, ys], 1), brush, shade(xs, ys), wobble=wobble)
        count += 1
    return count
