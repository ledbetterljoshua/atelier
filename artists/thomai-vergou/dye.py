"""Dye on paper, and the light that spends it.

A sheet holds six dyes as six densities. Nothing is opaque: every wash multiplies what is under
it, and the only white is the paper. Each dye has a colour and a life, and the two cannot be
bought separately. Light takes each dye away at its own rate and leaves a little tea behind.

    sheet = Sheet(1600, 2000)
    sheet.wash(blob(points), {"walnut": 0.5}, wet=2.0)
    sheet.render(days=9)        # the sheet after nine days of the room's light
"""
import numpy as np
from PIL import Image, ImageDraw
from scipy.ndimage import gaussian_filter, map_coordinates

# name: (what it takes out of red, green, blue; days of household light to fall to 1/e)
DYES = {
    "kermes":  ((0.04, 0.85, 0.42), 1.5),    # rose. Gone inside the week.
    "logwood": ((0.62, 0.72, 0.50), 3.2),    # violet grey, the cheap black.
    "madder":  ((0.07, 0.58, 0.72), 4.5),    # brick.
    "weld":    ((0.02, 0.09, 0.80), 7.5),    # yellow.
    "indigo":  ((0.86, 0.56, 0.17), 11.0),   # blue.
    "walnut":  ((0.42, 0.64, 0.96), 15.0),   # the furriers' brown. Nothing lawful is slower.
}
ORDER = list(DYES)
TEA = ((0.05, 0.11, 0.27), 60.0)             # what a dye leaves when it goes, and how long that stays
TEA_YIELD = {"kermes": 0.14, "logwood": 0.10, "madder": 0.11, "weld": 0.05, "indigo": 0.04, "walnut": 0.07}
PAPER = np.array([0.958, 0.944, 0.905], np.float32)


def noise(shape, sigma, rng, aniso=None):
    """Smooth noise in 0..1."""
    n = rng.standard_normal(shape).astype(np.float32)
    n = gaussian_filter(n, sigma if aniso is None else aniso, mode="wrap")
    return np.clip(0.5 + 0.17 * (n - n.mean()) / max(n.std(), 1e-9), 0, 1)


def blob(pts, n=14):
    """A closed curve through the points (Catmull-Rom)."""
    p = np.asarray(pts, np.float32)
    out = []
    m = len(p)
    for i in range(m):
        p0, p1, p2, p3 = p[(i - 1) % m], p[i], p[(i + 1) % m], p[(i + 2) % m]
        for t in np.linspace(0, 1, n, endpoint=False):
            out.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t
                              + (-p0 + 3 * p1 - 3 * p2 + p3) * t ** 3))
    return np.array(out)


def poly(pts):
    return np.asarray(pts, np.float32)


def band(pts, width):
    """A brush dragged along the points: (path, width). Width may be a list, one per point."""
    return ("band", np.asarray(pts, np.float32), width)


class Sheet:
    def __init__(self, w, h, unit, seed=7):
        self.w, self.h, self.u = w, h, unit
        self.rng = np.random.default_rng(seed)
        self.d = {k: np.zeros((h, w), np.float32) for k in DYES}
        r = self.rng
        # the paper: a cold-pressed tooth, and the slow unevenness of the sizing
        self.tooth = 0.6 * noise((h, w), 1.3, r) + 0.4 * noise((h, w), 3.5, r)
        self.tooth = (self.tooth - self.tooth.mean()) / self.tooth.std()
        self.size = noise((h, w), 60, r)
        self.pool = noise((h, w), 22, r)
        self.broad = 0.7 * noise((h, w), 110, r) + 0.3 * noise((h, w), 1, r, aniso=(9, 140))
        self.streak_h = noise((h, w), 1, r, aniso=(1.6, 26))
        self.streak_v = noise((h, w), 1, r, aniso=(26, 1.6))
        self.wx = noise((h, w), 14, r) - 0.5
        self.wy = noise((h, w), 14, r) - 0.5
        self.count = 0

    # ---- shapes -------------------------------------------------------------------------
    def mask(self, shape, wobble=1.0):
        """A shape in sheet units -> coverage 0..1 at sheet size, its edge shaken by the hand."""
        ss = 2
        im = Image.new("L", (self.w * ss, self.h * ss), 0)
        dr = ImageDraw.Draw(im)
        k = self.u * ss
        if isinstance(shape, tuple) and shape[0] == "band":
            _, pts, width = shape
            ws = np.broadcast_to(np.asarray(width, np.float32), (len(pts),))
            for i in range(len(pts) - 1):
                a, b = pts[i] * k, pts[i + 1] * k
                steps = max(2, int(np.hypot(*(b - a)) / 3))
                for t in np.linspace(0, 1, steps):
                    c = a + (b - a) * t
                    rad = (ws[i] + (ws[i + 1] - ws[i]) * t) * k / 2
                    dr.ellipse([c[0] - rad, c[1] - rad, c[0] + rad, c[1] + rad], fill=255)
        else:
            dr.polygon([tuple(q) for q in (np.asarray(shape) * k)], fill=255)
        m = np.asarray(im.resize((self.w, self.h), Image.BOX), np.float32) / 255
        if wobble:
            ys, xs = np.nonzero(gaussian_filter(m, 4) > 0.002)
            if len(ys) == 0:
                return m
            y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
            yy, xx = np.mgrid[y0:y1, x0:x1].astype(np.float32)
            amp = wobble * self.u * 0.9
            sub = map_coordinates(m, [yy + amp * self.wy[y0:y1, x0:x1], xx + amp * self.wx[y0:y1, x0:x1]],
                                  order=1, mode="nearest")
            m = np.zeros_like(m)
            m[y0:y1, x0:x1] = sub
        return m

    # ---- a wash -------------------------------------------------------------------------
    def wash(self, shape, mix, wet=1.5, rim=0.5, var=0.25, tooth=0.06, wobble=1.0, streak=None,
             dry=0.0, ramp=None, keep=None, mask=None, grain="pool"):
        """Lay one wash.

        mix     {dye: amount}
        wet     how far the edge runs, in pixels
        rim     how much dye is carried to the drying edge
        var     how unevenly it pools
        streak  "h" or "v": the hairs of the brush show
        dry     0..1: a brush running out, catching only the top of the tooth
        ramp    (x0, y0, a0, x1, y1, a1) in sheet units: the wash thins from a0 to a1
        keep    a coverage array: paper kept clear of this wash (it is painted round)
        """
        m = self.mask(shape, wobble) if mask is None else mask
        ys, xs = np.nonzero(m > 0.003)
        if len(ys) == 0:
            return m
        pad = int(wet * 4 + 24)
        y0, y1 = max(ys.min() - pad, 0), min(ys.max() + pad + 1, self.h)
        x0, x1 = max(xs.min() - pad, 0), min(xs.max() + pad + 1, self.w)
        sl = (slice(y0, y1), slice(x0, x1))
        s = gaussian_filter(m[sl], wet)
        if keep is not None:
            s = s * (1 - keep[sl])
        body = s * (1 + var * 2 * (getattr(self, grain)[sl] - 0.5)) * (1 + 0.5 * var * (self.size[sl] - 0.5))
        edge = s * (1 - gaussian_filter(s, max(wet * 2.2, 3.0)))
        dens = body * (1 - 0.35 * rim) + rim * 2.6 * edge
        if streak:
            st = self.streak_h if streak == "h" else self.streak_v
            dens = dens * (0.72 + 0.56 * st[sl])
        if dry > 0:
            t = self.tooth[sl] * 0.5 + (self.streak_h if streak != "v" else self.streak_v)[sl] * 2.2 - 1.1
            dens = dens * np.clip((t + (1 - dry) * 2.4 - 0.6) * 1.6, 0, 1)
        dens = dens * (1 - tooth * self.tooth[sl])
        if ramp is not None:
            ax, ay, a0, bx, by, a1 = ramp
            yy, xx = np.mgrid[y0:y1, x0:x1].astype(np.float32) / self.u
            dx, dy = bx - ax, by - ay
            t = np.clip(((xx - ax) * dx + (yy - ay) * dy) / (dx * dx + dy * dy), 0, 1)
            dens = dens * (a0 + (a1 - a0) * t)
        dens = np.clip(dens, 0, None)
        for k, a in mix.items():
            self.d[k][sl] += a * dens
        self.count += 1
        return m

    def snapshot(self):
        return {k: v.copy() for k, v in self.d.items()}

    # ---- light --------------------------------------------------------------------------
    def render(self, days=0.0, light=None, d=None):
        """The sheet after `days` of the room's light. `light` is how much of it each part gets."""
        d = self.d if d is None else d
        e = days * (np.ones((self.h, self.w), np.float32) if light is None else light)
        od = np.zeros((self.h, self.w, 3), np.float32)
        tea = np.zeros((self.h, self.w), np.float32)
        for k, (ab, tau) in DYES.items():
            f = np.exp(-e / tau)
            od += (d[k] * f)[..., None] * np.array(ab, np.float32)
            tea += TEA_YIELD[k] * d[k] * (1 - f)
        tea *= np.exp(-e / TEA[1])
        od += tea[..., None] * np.array(TEA[0], np.float32)
        # the paper itself, lit a little from the upper left so the tooth shows
        gy, gx = np.gradient(self.tooth)
        relief = 1 + 0.026 * np.clip(gx + gy, -2, 2) * 2.2
        paper = PAPER * (1 - 0.018 * (self.size[..., None] - 0.5)) * relief[..., None]
        rgb = paper * np.power(10.0, -od)
        return np.clip(rgb, 0, 1)

    def image(self, **kw):
        return Image.fromarray((self.render(**kw) * 255 + 0.5).astype(np.uint8))
