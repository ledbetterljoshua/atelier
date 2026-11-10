"""Zala Hrovat's kit: a river seen from straight above.

The river is described, not pictured: how deep it is at a point, which way and how fast it runs
there, and where the sun is. Strokes follow the current; glazes are chosen by depth; stones are
lit from the sun's side; floating things throw their shadows down through the water.
"""
import numpy as np
from scipy.spatial import Voronoi


def smoothstep(a, b, x):
    t = np.clip((x - a) / (b - a), 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


# --- the current --------------------------------------------------------------------------------

def streamline(vel, x, y, length, step=3.0, both=True, stop=None):
    """Follow the current from (x, y) for `length` px (half each way if `both`).
    vel(x, y) -> (vx, vy). stop(x, y) -> True ends the line there."""
    def run(sign, L):
        pts = [(x, y)]
        px, py, s = x, y, 0.0
        while s < L:
            vx, vy = vel(px, py)
            n = np.hypot(vx, vy) + 1e-9
            mx, my = px + sign * vx / n * step * 0.5, py + sign * vy / n * step * 0.5
            vx, vy = vel(mx, my)
            n = np.hypot(vx, vy) + 1e-9
            px, py = px + sign * vx / n * step, py + sign * vy / n * step
            if stop is not None and stop(px, py):
                break
            pts.append((px, py))
            s += step
        return pts
    if both:
        back = run(-1, length / 2)[::-1]
        fwd = run(1, length / 2)
        return np.array(back[:-1] + fwd)
    return np.array(run(1, length))


def with_the_current(board, vel, seeds, brush, color_fn, length, stop=None, wobble=0.6,
                     width_fn=None, opacity_fn=None, min_len=12.0):
    """One stroke per seed, along the streamline through it. color_fn(x, y) mixes for where it lands."""
    rng = board.rng
    n = 0
    for x, y in seeds:
        L = length * rng.uniform(0.6, 1.3)
        pts = streamline(vel, x, y, L, step=max(2.0, brush.width * 0.25), stop=stop)
        if len(pts) < 3:
            continue
        if np.hypot(*(pts[-1] - pts[0])) < min_len:
            continue
        m = pts[len(pts) // 2]
        b = brush
        if width_fn is not None:
            b = b.but(width=width_fn(*m))
        if opacity_fn is not None:
            b = b.but(opacity=opacity_fn(*m))
        board.stroke(pts, b, color_fn(*m), wobble=wobble)
        n += 1
    return n


def scatter(rng, W, H, n, where=None, pad=40):
    """n points over the board, kept only where(x, y) says so."""
    out = []
    tries = 0
    while len(out) < n and tries < n * 30:
        k = max(64, (n - len(out)) * 3)
        xs = rng.uniform(-pad, W + pad, k)
        ys = rng.uniform(-pad, H + pad, k)
        for x, y in zip(xs, ys):
            if where is None or where(x, y):
                out.append((x, y))
                if len(out) >= n:
                    break
        tries += k
    return out


# --- water -------------------------------------------------------------------------------------

class Water:
    """What a depth of water does to light that goes down to the bed and comes back up."""

    def __init__(self, absorb, body):
        self.absorb = np.asarray(absorb, dtype=np.float64)   # per metre, linear r g b
        self.body = np.asarray(body, dtype=np.float64)       # what deep water itself looks like

    def through(self, depth):
        return np.exp(-self.absorb * 2.0 * max(depth, 0.0))

    def veil(self, depth):
        """How much of the water's own colour comes back from a depth (0 at the surface, ->1 deep)."""
        return 1.0 - np.exp(-1.1 * max(depth, 0.0))


def glaze_by_depth(board, vel, depth, levels, brush, color_for, per_level, length, W, H,
                   wobble=0.8, jitter=0.06, brush_for=None):
    """Glaze the river back in, one level at a time. A level only goes where the water is at least
    that deep, so deep water collects many layers and the shallows few. Strokes run with the
    current and stop where the bed rises above their level."""
    rng = board.rng
    n = 0
    for i, d in enumerate(levels):
        def deep_enough(x, y, d=d):
            return depth(x, y) >= d
        cnt = per_level(i, d)
        bi = brush if brush_for is None else brush_for(i, d)
        seeds = scatter(rng, W, H, cnt, where=deep_enough)
        for x, y in seeds:
            dd = d + rng.normal(0, jitter)
            pts = streamline(vel, x, y, length * rng.uniform(0.6, 1.3), step=max(2.0, bi.width * 0.25),
                             stop=lambda px, py, dd=dd: depth(px, py) < dd)
            if len(pts) < 4:
                continue
            board.stroke(pts, bi.but(width=bi.width * rng.uniform(0.7, 1.25)), color_for(i, d, x, y),
                         wobble=wobble)
            n += 1
    return n


def tape_where(board, fn, feather=1.5):
    """Masking tape cut to a region she has worked out rather than drawn: fn(X, Y) -> 0..1 over the
    pixel grid (vectorised). The engine's tape() only takes polygons."""
    from scipy.ndimage import gaussian_filter
    Y, X = np.mgrid[0:board.h, 0:board.w].astype(np.float64) + 0.5
    m = np.clip(fn(X, Y), 0.0, 1.0).astype(np.float32)
    if feather > 0:
        m = gaussian_filter(m, feather)
    board.mask = np.ascontiguousarray(m, dtype=np.float32)
    board.use_mask = True


# --- the bed -----------------------------------------------------------------------------------

def pack_stones(rng, W, H, r_fn, n_try, overlap=0.75, where=None, pad=30):
    """Stones for a gravel bed: biggest first, dart-thrown so they nestle rather than stack.
    r_fn(x, y, rng) -> radius in px at that spot. Returns (x, y, r) rows."""
    cand = np.column_stack([rng.uniform(-pad, W + pad, n_try), rng.uniform(-pad, H + pad, n_try)])
    rr = np.array([r_fn(x, y, rng) for x, y in cand])
    order = np.argsort(-rr)
    cell = max(8.0, rr.max())
    grid = {}
    out = []
    for i in order:
        x, y = cand[i]
        r = rr[i]
        if r < 2 or (where is not None and not where(x, y)):
            continue
        gx, gy = int(x // cell), int(y // cell)
        ok = True
        for ax in range(gx - 2, gx + 3):
            for ay in range(gy - 2, gy + 3):
                for (qx, qy, qr) in grid.get((ax, ay), ()):
                    if (qx - x) ** 2 + (qy - y) ** 2 < (overlap * (qr + r)) ** 2:
                        ok = False
                        break
                if not ok:
                    break
            if not ok:
                break
        if ok:
            grid.setdefault((gx, gy), []).append((x, y, r))
            out.append((x, y, r))
    return out


def stone(board, x, y, r, ang, elong, lit, dark, sun, brush, shadow=None, shadow_len=0.5):
    """One stone seen from above: its cast shadow, its body, the cap the sun is on, the dark under-edge.
    sun is a unit vector on the board pointing toward the light."""
    sx, sy = sun
    L = 2 * r * elong
    if -np.sin(ang) * sx + np.cos(ang) * sy < 0:   # the second colour rides the +normal side
        ang += np.pi
    if shadow is not None:
        ox, oy = -sx * r * shadow_len, -sy * r * shadow_len
        board.dab(x + ox, y + oy, brush.but(width=2 * r * 1.05, glaze=True, opacity=0.55, taper=(0.3, 0.3)),
                  shadow, angle=ang, length=L * 1.02)
    body = brush.but(width=2 * r, taper=(0.28, 0.28))
    board.dab(x, y, body, dark, angle=ang, length=L, color2=lit)
    cap = brush.but(width=1.25 * r, taper=(0.3, 0.35), opacity=0.8)
    board.dab(x + sx * r * 0.32, y + sy * r * 0.32, cap, lit, angle=ang, length=L * 0.62)
    edge = brush.but(width=max(2.0, 0.35 * r), opacity=0.4, taper=(0.35, 0.35))
    board.dab(x - sx * r * 0.62, y - sy * r * 0.62, edge, dark, angle=np.arctan2(sx, -sy), length=r * 1.3)


def sun_net(rng, x0, y0, x1, y1, cell, stretch=1.0, angle=0.0):
    """The sunlight net on a riverbed: where a riffled surface focuses the sun, the bright lines
    lie roughly on the edges of cells. Returns segments as (a, b, junction_weight)."""
    w, h = x1 - x0, y1 - y0
    nx, ny = int(w / cell) + 3, int(h / cell * stretch) + 3
    gx, gy = np.meshgrid(np.arange(nx), np.arange(ny))
    pts = np.column_stack([gx.ravel() + rng.uniform(-0.45, 0.45, gx.size),
                           gy.ravel() + rng.uniform(-0.45, 0.45, gy.size)]).astype(np.float64)
    pts[:, 0] *= cell
    pts[:, 1] *= cell / stretch
    vor = Voronoi(pts)
    ca, sa = np.cos(angle), np.sin(angle)
    cx, cy = w / 2, h / 2
    segs = []
    for (a, b) in vor.ridge_vertices:
        if a < 0 or b < 0:
            continue
        pa, pb = vor.vertices[a].copy(), vor.vertices[b].copy()
        for p in (pa, pb):
            p[0] -= cell
            p[1] -= cell / stretch
            dx, dy = p[0] - cx, p[1] - cy
            p[0], p[1] = cx + dx * ca - dy * sa + x0, cy + dx * sa + dy * ca + y0
        if not (-cell < pa[0] < w + x0 + cell and -cell < pa[1] < h + y0 + cell):
            continue
        segs.append((pa, pb))
    return segs


# --- what floats -------------------------------------------------------------------------------

def leaf_outline(cx, cy, length, width, ang, rng, teeth=9):
    """A beech leaf: ovate, a drawn-out tip, a shallow wave of teeth at each vein end."""
    t = np.linspace(0, np.pi, 48)
    u = -np.cos(t)                     # -1 stalk .. 1 tip
    widest = np.sqrt(np.clip(1 - u * u, 0, 1)) * (0.88 - 0.12 * u)
    drawn = 1 - 0.62 * smoothstep(0.25, 1.0, u)          # the tip is drawn out, not rounded
    half = width / 2 * widest * drawn / 0.95
    half *= 1 + 0.04 * np.abs(np.sin(t * teeth))
    xs = u * length / 2
    right = np.column_stack([xs, half * (1 + rng.normal(0, 0.015, len(t)))])
    left = np.column_stack([xs[::-1], -half[::-1] * (1 + rng.normal(0, 0.015, len(t)))])
    poly = np.vstack([right, left])
    ca, sa = np.cos(ang), np.sin(ang)
    R = np.array([[ca, -sa], [sa, ca]])
    return poly @ R.T + [cx, cy]


def offset_through_water(depth_m, ppm, sun_elev_deg, sun_dir):
    """How far, on the board, a floating thing's shadow lands from it."""
    zen = np.radians(90 - sun_elev_deg)
    under = np.arcsin(np.sin(zen) / 1.333)
    d = depth_m * np.tan(under) * ppm
    return -sun_dir[0] * d, -sun_dir[1] * d


def poly_mask(W, H, poly):
    """0..1 array, 1 inside the polygon: for combining with a worked-out region before taping."""
    from PIL import Image, ImageDraw
    im = Image.new("L", (W, H), 0)
    ImageDraw.Draw(im).polygon([tuple(map(float, q)) for q in poly], fill=255)
    return np.asarray(im, dtype=np.float64) / 255.0
