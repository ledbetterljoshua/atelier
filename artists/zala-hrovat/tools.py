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


# --- a river with its surface on (added for 002) -----------------------------------------------

def colors_along(pts, fn, every=3):
    """The colour a stroke should have at each place it passes, for a stroke whose colour changes
    along its length. fn(x, y) -> colour. Sampled every few points; the engine spreads them evenly."""
    pts = np.asarray(pts)
    idx = list(range(0, len(pts), every))
    if idx[-1] != len(pts) - 1:
        idx.append(len(pts) - 1)
    return np.array([fn(*pts[i]) for i in idx])


def glaze_through(board, vel, seeds, brush, color_at, length, wobble=0.8, width_jit=(0.7, 1.25)):
    """Glazes that run with the current right across changes of depth, mixed for each place they
    cross instead of stopping where the bed comes up. color_at(x, y) -> glaze colour there."""
    rng = board.rng
    n = 0
    for x, y in seeds:
        pts = streamline(vel, x, y, length * rng.uniform(0.6, 1.3), step=max(2.0, brush.width * 0.25))
        if len(pts) < 4:
            continue
        board.stroke(pts, brush.but(width=brush.width * rng.uniform(*width_jit)), colors_along(pts, color_at),
                     wobble=wobble)
        n += 1
    return n


class Boils:
    """Water coming up from the bed in domes: each spreads out from its centre and is smooth on top,
    and where it meets the river round it there is a crease that gathers foam. (x, y, radius, push)."""

    def __init__(self, boils):
        self.b = [tuple(map(float, q)) for q in boils]

    def flow(self, vel):
        def v(x, y):
            vx, vy = vel(x, y)
            for cx, cy, r, push in self.b:
                dx, dy = x - cx, y - cy
                d = np.hypot(dx, dy) + 1e-6
                k = push * np.where(d < r, d / r, np.exp(-((d - r) / (0.45 * r)) ** 2))
                vx = vx + k * dx / d
                vy = vy + k * dy / d
            return vx, vy
        return v

    def reach(self, i, X, Y):
        """Distance from boil i's centre in units of its edge, which is never a true circle: it
        bulges where it has pushed further and is drawn out a little downstream."""
        cx, cy, r, _ = self.b[i]
        dx, dy = X - cx, Y - cy
        th = np.arctan2(dy, dx)
        edge = r * (1.0 + 0.10 * np.sin(3 * th + 1.7 * i) + 0.06 * np.sin(5 * th + 0.9 * i + 2.0)
                    + 0.12 * np.clip(np.sin(th), 0, 1) ** 2)
        return np.hypot(dx, dy) / edge

    def inside(self, X, Y, soft=0.08):
        """0..1, how far inside the smooth top of a boil."""
        m = np.zeros(np.shape(X))
        for i in range(len(self.b)):
            m = np.maximum(m, 1.0 - smoothstep(1.0 - soft * 2, 1.0, self.reach(i, X, Y)))
        return m

    def rim(self, X, Y, w=0.07):
        m = np.zeros(np.shape(X))
        for i in range(len(self.b)):
            m = np.maximum(m, np.exp(-((self.reach(i, X, Y) - 1.0) / w) ** 2))
        return m

    def edge_at(self, i, th):
        """Points on boil i's edge at angles th."""
        cx, cy, r, _ = self.b[i]
        e = r * (1.0 + 0.10 * np.sin(3 * th + 1.7 * i) + 0.06 * np.sin(5 * th + 0.9 * i + 2.0)
                 + 0.12 * np.clip(np.sin(th), 0, 1) ** 2)
        return np.column_stack([cx + e * np.cos(th), cy + e * np.sin(th)])


def stone_under_cloud(board, x, y, r, ang, elong, lit, dark, brush):
    """A stone with the light from the whole sky: lit on top, dark all round where it meets the bed."""
    L = 2 * r * elong
    board.dab(x, y, brush.but(width=2 * r * 1.08, taper=(0.28, 0.28)), dark, angle=ang, length=L * 1.04)
    board.dab(x, y, brush.but(width=1.5 * r, taper=(0.3, 0.32), opacity=0.85), lit, angle=ang, length=L * 0.74)


def foam_lace(board, pts, brush, color_fn, rng, width=6.0, strands=3, every=(2, 6), size=(1.3, 3.4)):
    """A foam line as it really lies on a fast river: a few strands of beads along the current that
    wander apart and come back together, wider and thinner by turns."""
    pts = np.asarray(pts)
    if len(pts) < 3:
        return 0
    d = np.gradient(pts, axis=0)
    nrm = np.column_stack([-d[:, 1], d[:, 0]])
    nrm /= np.linalg.norm(nrm, axis=1, keepdims=True) + 1e-9
    s = np.arange(len(pts))
    n = 0
    for j in range(strands):
        ph, f = rng.uniform(0, 6.3), rng.uniform(0.04, 0.12)
        w = width * (0.5 + 0.5 * np.sin(s * rng.uniform(0.02, 0.05) + rng.uniform(0, 6.3))) + 0.6
        off = np.sin(s * f + ph) * w * rng.uniform(0.4, 1.0)
        line = pts + nrm * off[:, None]
        k = int(rng.integers(0, 4))
        while k < len(line):
            if rng.random() < 0.85:
                q = line[k] + rng.normal(0, 0.8, 2)
                board.dab(q[0], q[1], brush.but(width=rng.uniform(*size)), color_fn(q[0], q[1]),
                          length=rng.uniform(1.5, 5.0))
                n += 1
            k += int(rng.integers(*every))
    return n


# --- clear water under a broken skin (added for 003) -------------------------------------------

class Skin:
    """The river's surface as a height field in metres, height(X, Y) over the pixel grid, and what
    its slopes do to the light: where the bed is seen to be, which facets send the sun up to me."""

    def __init__(self, height, W, H, ppm):
        Y, X = np.mgrid[0:H, 0:W].astype(np.float64) + 0.5
        self.h = height(X, Y)
        gy, gx = np.gradient(self.h)
        self.sx, self.sy = gx * ppm, gy * ppm          # rise per run, both on the board
        self.W, self.H, self.ppm = W, H, ppm

    def slope(self, x, y):
        ix = np.clip(np.asarray(x, dtype=np.float64).astype(int), 0, self.W - 1)
        iy = np.clip(np.asarray(y, dtype=np.float64).astype(int), 0, self.H - 1)
        return self.sx[iy, ix], self.sy[iy, ix]

    def seen(self, pts, depth, n=1.333):
        """Where things at `depth` metres (a number or fn(x, y)) appear from straight above: a facet
        tipped up toward one side bends the line of sight under it, so the bed slides that way."""
        pts = np.asarray(pts, dtype=np.float64)
        d = depth(pts[:, 0], pts[:, 1]) if callable(depth) else depth
        sx, sy = self.slope(pts[:, 0], pts[:, 1])
        k = (1.0 - 1.0 / n) * np.asarray(d) * self.ppm
        return pts + np.column_stack([sx * k, sy * k])

    def glints(self, rng, n_try, sun, sun_elev, tol, where=None):
        """Places where a facet is tipped just so, halfway between the sun and my eye. Returns x, y and
        how squarely (0..1) each one sends the sun up."""
        tgt = np.tan(np.radians(90.0 - sun_elev) / 2.0)
        x = rng.uniform(0, self.W, n_try)
        y = rng.uniform(0, self.H, n_try)
        sx, sy = self.slope(x, y)
        miss = np.hypot(sx + tgt * sun[0], sy + tgt * sun[1])
        keep = miss < tol
        if where is not None:
            keep &= where(x, y)
        return x[keep], y[keep], 1.0 - miss[keep] / tol


def net_cells(rng, W, H, cell_fn, n_try, stretch=1.0, angle=0.0, pad=80):
    """The sunlight net when its mesh changes across the reach: coarse under big chop, fine under
    small. cell_fn(x, y) -> px. Segments as (a, b)."""
    pts = pack_stones(rng, W, H, lambda x, y, g: 0.5 * cell_fn(x, y) * g.uniform(0.85, 1.15), n_try,
                      overlap=0.92, pad=pad)
    P = np.array([(x, y) for x, y, _ in pts])
    ca, sa = np.cos(angle), np.sin(angle)
    R = np.array([[ca, sa], [-sa, ca]])
    Q = P @ R.T
    Q[:, 1] *= 1.0 / stretch
    vor = Voronoi(Q)
    V = vor.vertices.copy()
    V[:, 1] *= stretch
    V = V @ R
    segs = []
    for (a, b) in vor.ridge_vertices:
        if a < 0 or b < 0:
            continue
        pa, pb = V[a], V[b]
        if np.hypot(*(pa - pb)) > 4 * cell_fn(*((pa + pb) / 2)):
            continue
        if not (-pad < pa[0] < W + pad and -pad < pa[1] < H + pad):
            continue
        segs.append((pa, pb))
    return segs


def _axis(x, y, ang, L, k=7):
    t = np.linspace(-0.5, 0.5, k)
    return np.column_stack([x + np.cos(ang) * L * t, y + np.sin(ang) * L * t])


def stone_seen(board, seen, x, y, r, ang, elong, lit, dark, sun, brush, shadow=None, shadow_len=0.5):
    """stone(), seen through a broken surface: seen(pts) moves every part of it to where it appears,
    so a stone under a wave is bent with it."""
    sx, sy = sun
    L = 2 * r * elong
    if -np.sin(ang) * sx + np.cos(ang) * sy < 0:
        ang += np.pi
    if shadow is not None:
        ox, oy = -sx * r * shadow_len, -sy * r * shadow_len
        board.stroke(seen(_axis(x + ox, y + oy, ang, L * 1.02)),
                     brush.but(width=2 * r * 1.05, glaze=True, opacity=0.55, taper=(0.3, 0.3)), shadow)
    board.stroke(seen(_axis(x, y, ang, L)), brush.but(width=2 * r, taper=(0.28, 0.28)), dark, color2=lit)
    board.stroke(seen(_axis(x + sx * r * 0.32, y + sy * r * 0.32, ang, L * 0.62)),
                 brush.but(width=1.25 * r, taper=(0.3, 0.35), opacity=0.8), lit)
    board.stroke(seen(_axis(x - sx * r * 0.62, y - sy * r * 0.62, np.arctan2(sx, -sy), r * 1.3, 5)),
                 brush.but(width=max(2.0, 0.35 * r), opacity=0.4, taper=(0.35, 0.35)), dark)


def trout_outline(cx, cy, length, ang, bend=0.0, n=40):
    """A trout from above, snout first along `ang`: the body to the tail fork, and the two pectoral
    fins splayed back off the shoulders. bend swings the tail to one side."""
    u = np.linspace(0.0, 1.0, n)
    hw = np.where(u < 0.26, (u / 0.26) ** 0.55, 1.0 - 0.8 * np.clip((u - 0.26) / 0.62, 0, 1) ** 1.25)
    hw = length * 0.095 * hw
    tail = u > 0.88
    hw[tail] = length * (0.015 + 0.075 * ((u[tail] - 0.88) / 0.12) ** 0.8)
    s = u * length
    lat = bend * length * 0.09 * (u ** 2)
    ca, sa = np.cos(ang), np.sin(ang)
    fwd, side = np.array([ca, sa]), np.array([-sa, ca])
    c0 = np.array([cx, cy]) + fwd * length / 2
    spine = c0 - np.outer(s, fwd) + np.outer(lat, side)
    right = spine + side * hw[:, None]
    left = spine - side * hw[:, None]
    fork = spine[-1] + fwd * length * 0.035
    body = np.vstack([right, [fork], left[::-1]])
    fins = []
    k = int(0.24 * (n - 1))
    for sg in (1, -1):
        root = spine[k] + sg * side * hw[k] * 0.8
        out = -fwd * 0.75 + sg * side * 0.65
        out /= np.linalg.norm(out)
        tip = root + out * length * 0.13
        back = spine[k + 3] + sg * side * hw[k + 3] * 0.8
        fins.append(np.array([root, tip + sg * side * length * 0.012, tip - fwd * length * 0.02, back]))
    return body, fins
