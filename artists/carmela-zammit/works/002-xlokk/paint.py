"""Carmela Zammit - Xlokk

The same roof, a sirocco afternoon. The sky is one flat dishwater colour with the dust in it, no sun
anywhere to put behind a sheet, and the washing has hung all day without drying. Nothing moves. The
lines run away to the left now; she is standing under the near one.
"""
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[3]))
sys.path.insert(0, str(HERE.parents[1]))

from engine import Board, Brush, hexc, mix, scale  # noqa: E402
from engine.studio import finish  # noqa: E402
from tools import Camera, Hang, Line, lay_cloth, lay_screen, sheeting, tone, unit, v3  # noqa: E402

W, H = 1800, 1200
rng0 = np.random.default_rng(1987)
board = Board(W, H, hexc("#7a3021"), sheeting(W, H, rng0, darns=[(1310, 760, 40, 26)]), seed=1987,
              light=(-0.35, -0.9))
rng = board.rng
cam = Camera(W, H, 1750, (0.0, 1.55, 0.0), pitch=-0.02, cy=520)
E = cam.eye
P = cam.P

# --- tubes ---------------------------------------------------------------------------------------
white, ultra, prussian = hexc("#f7f4ec"), hexc("#20307f"), hexc("#14284a")
naples, ochre, rawsi, burnsi = hexc("#ecd398"), hexc("#c49236"), hexc("#a8692a"), hexc("#7d3418")
black, turq = hexc("#141210"), hexc("#2a9a9a")

# --- the roof ------------------------------------------------------------------------------------
ZB, XL = 15.0, -5.0           # the back wall, and the side wall on the left
PAR_H = 1.0

# --- the washing -----------------------------------------------------------------------------------
near = Line((2.7, 2.7), (-4.3, 12.4), 2.02, 0.12)
off = -near.n * 2.3
far = Line(near.a + off + near.d * 1.2, near.b + off, 2.05, 0.12)

N1 = Hang(near, 0.00, 2.30, 1.62, pegs=4, folds=0.075, give=0.03, sag=0.07, droop=0.03, band=0.08, seed=31)
N2 = Hang(near, 2.45, 0.70, 0.98, pegs=2, folds=0.03, give=0.01, sag=0.05, droop=0.02, seed=32)  # pillowcase
N3 = Hang(near, 3.30, 2.10, 1.55, pegs=4, folds=0.065, give=0.025, sag=0.06, band=0.08, seed=33)
N4 = Hang(near, 5.55, 1.00, 1.30, pegs=3, folds=0.04, give=0.015, sag=0.04, seed=34)            # towel
N5 = Hang(near, 6.70, 2.00, 1.50, pegs=4, folds=0.06, give=0.02, sag=0.06, band=0.08, seed=35)
N6 = Hang(near, 8.85, 0.68, 0.95, pegs=2, folds=0.03, give=0.01, sag=0.05, seed=36)
N7 = Hang(near, 9.70, 2.00, 1.50, pegs=4, folds=0.06, give=0.02, sag=0.06, band=0.08, seed=37)
NEAR = [N1, N2, N3, N4, N5, N6, N7]
F1 = Hang(far, 0.3, 2.0, 1.45, pegs=4, folds=0.055, sag=0.06, band=0.08, seed=41)
F2 = Hang(far, 2.5, 1.0, 1.25, pegs=3, folds=0.04, sag=0.04, seed=42)
F3 = Hang(far, 3.7, 2.0, 1.45, pegs=4, folds=0.055, sag=0.06, band=0.08, seed=43)
F4 = Hang(far, 5.9, 2.0, 1.45, pegs=4, folds=0.055, sag=0.06, band=0.08, seed=44)
F5 = Hang(far, 8.1, 0.7, 0.95, pegs=2, folds=0.03, sag=0.05, seed=45)
FAR = [F1, F2, F3, F4, F5]

# --- the light -----------------------------------------------------------------------------------
# No sun. The whole sky is the lamp, brighter low down where the dust is thickest, and brightest of
# all low in the south-east, behind her right shoulder and off the board.
GLOW = unit(v3(0.3, 0.5, -0.8))
SKY_TOP = v3(0.21, 0.19, 0.14)
SKY_LOW = v3(0.43, 0.38, 0.27)
ROOF_BACK = v3(0.30, 0.25, 0.19) * 0.45
LAMP = v3(0.62, 0.56, 0.44)               # the sky as the cloth feels it, all of it at once
COTTON = mix((white, 10), (naples, 0.6))
DAMP = 0.10                                   # how much of the sky behind comes through wet cotton


def sky_colour(x, y):
    d = cam.ray(x, y)
    el = np.arcsin(np.clip(d[..., 1], -1, 1))
    t = np.clip(el / 0.42, 0, 1) ** 0.75
    c = np.exp(np.log(SKY_LOW) * (1 - t[..., None]) + np.log(SKY_TOP) * t[..., None])
    c = c * (1 + 0.10 * np.exp(-((x - 1350) / 500.0) ** 2 - ((y - 120) / 400.0) ** 2))
    return c


def irradiance(n):
    """Light arriving at a surface facing n, from the sky and back up off the roof."""
    up = (0.5 + 0.5 * n[..., 1])[..., None]
    g = np.clip(n @ GLOW, 0, 1)[..., None]
    return LAMP * 0.7 * up + ROOF_BACK * (1 - up) + LAMP * 0.72 * g


def behind(Q):
    """What she would see through the cloth at Q: sky above the back parapet, wall and roof below it."""
    d = Q - E
    t = (ZB - E[2]) / np.maximum(d[..., 2], 1e-3)
    y = E[1] + d[..., 1] * t
    sky = (y > PAR_H + 0.05).astype(float)
    return sky[..., None] * LAMP * 0.8 + (1 - sky[..., None]) * v3(0.30, 0.26, 0.20) * 0.6


def cloth(sheet, gain=1.0, damp=DAMP, vary=0.03, relief=1.0):
    """Mixes the colour for points of cloth: the side facing her takes the sky on its folds, and
    the damp lets a little of whatever is behind come through."""
    def f(u, v):
        u, v = np.atleast_1d(u).astype(float), np.atleast_1d(v).astype(float)
        Q = sheet.pos(u, v)
        n = sheet.normal(u, v, E)
        n = unit(n * relief + v3(sheet.line.n[0], 0, sheet.line.n[1]) * (1 - relief))   # far off, the folds go soft
        fd = relief * sheet.crease(u, v) / (np.abs(sheet.fa).sum() + 1e-6)
        ao = 0.62 + 0.38 * np.clip(0.5 + 0.9 * fd, 0, 1)           # the back of a fold sees less sky
        layers = np.where((v < sheet.band) | (v > 0.97), 0.35, 1.0)
        wet = np.clip((v - 0.45) / 0.55, 0, 1) ** 1.4                # the water has gone to the hem
        cool = 1 + (1 - ao)[:, None] * v3(-0.25, -0.05, 0.2)        # the inside of a fold is the colder grey
        c = COTTON * cool * irradiance(n) * (ao * (1 - 0.4 * wet))[:, None] \
            + damp * ((1 + 0.8 * wet) * layers)[:, None] * behind(Q) * COTTON
        c = tone(c * gain, 1.7) * np.exp(rng.normal(0, vary, 3))
        return c if c.shape[0] > 1 else c[0]
    return f


# =================================================================================================
# 1. The sky, thin, over the red. The dust is already in the ground.
# =================================================================================================
horizon_y = P(v3(0, E[1], 1e4))[1]
par_top_y = P(v3(0, PAR_H, ZB))[1]
scrub = Brush(width=140, bristle=2.8, opacity=0.97, pickup=0.08, dryness=0.0, thickness=0.05, jitter=0.03, deplete=0.0005)
region = (-80, -60, W + 80, par_top_y + 40)
lay_screen(board, region, scrub, lambda x, y: scale(sky_colour(x, y), 0.9), angle=0.05, length=700, cover=4.5, wobble=12)
sky_b = Brush(width=60, bristle=2.2, opacity=0.6, pickup=0.45, dryness=0.0, thickness=0.05, jitter=0.02,
              deplete=0.0004, taper=(0.12, 0.15))
lay_screen(board, region, sky_b, lambda x, y: sky_colour(x, y) * np.exp(rng.normal(0, 0.03, 3)), angle=0.05,
           length=700, cover=8.0, wobble=10)
board.stage("the sky, thin, over the red")

# Qormi in the dust, put in while the sky is still wet so it goes into it
haze = mix((sky_colour(np.float64(230), np.float64(par_top_y - 30)), 3), (burnsi, 0.3), (ultra, 0.35))
dx, dz, gy = -470.0, 1200.0, -46.0


def town(x, y):
    return P(v3(dx + x, gy + y, dz))


drum = [town(-11, 22), town(11, 22), town(11, 34), town(-11, 34)]
dome = [town(11 * np.cos(t), 34 + 13 * np.sin(t) ** 0.8) for t in np.linspace(0, np.pi, 18)]
lantern = [town(-2.2, 45), town(2.2, 45), town(2.2, 51), town(0, 53.5), town(-2.2, 51)]
belfry = lambda c: [town(c - 4, 0), town(c + 4, 0), town(c + 4, 33), town(c + 2.5, 35), town(c, 38.5), town(c - 2.5, 35), town(c - 4, 33)]  # noqa: E731
body = [town(-26, 0), town(26, 0), town(26, 24), town(-26, 24)]
board.tape(body, drum, dome, lantern, belfry(-22), belfry(22), feather=1.6)
x0, x1 = town(-40, 0)[0], town(40, 0)[0]
lay_screen(board, (x0, town(0, 56)[1], x1, par_top_y + 10),
           Brush(width=9, bristle=1.2, opacity=0.45, pickup=0.6, thickness=0.05, taper=(0.3, 0.3)),
           lambda x, y: haze * np.exp(rng.normal(0, 0.02)), angle=np.pi / 2, angle_jitter=0.12, length=30, cover=6, wobble=0.5)
board.untape()
board.dry()
board.stage("Qormi, into the wet sky")

# =================================================================================================
# 2. The roof and its walls.
# =================================================================================================
LIME = mix((naples, 2), (white, 2), (burnsi, 0.15), (ochre, 0.1))
DUST = mix((burnsi, 1), (ochre, 1), (white, 1))


def roof_colour(x, y):
    Q = cam.on_ground(x, y)
    dist = np.hypot(Q[0], Q[2])
    c = mix((LIME, 4), (DUST, 0.7), (ultra, 0.45), (white, 0.5)) * LAMP * 0.55
    c = c * (0.7 + 0.3 * np.clip((Q[2] - 3) / 9, 0, 1))
    # the dust settles where the wall keeps the wind off
    d = np.exp(-(ZB - Q[2]) / 2.0) + np.exp(-(Q[0] - XL) / 1.5)
    c = mix((c, 1), (c * DUST / LIME, min(0.6, 0.35 * d)))
    hz = np.clip((dist - 4) / 30, 0, 0.35)
    c = c * (1 - hz) + SKY_LOW * hz
    return tone(c, 1.7) * np.exp(rng.normal(0, 0.025, 3))


roof_top = P(v3(0, 0, ZB))[1]
deck = Brush(width=34, bristle=1.8, opacity=0.9, pickup=0.3, dryness=0.0, thickness=0.12, jitter=0.04, deplete=0.0006)
lay_screen(board, (-200, roof_top - 10, W + 200, H + 40), scrub.but(width=100), lambda x, y: scale(roof_colour(x, y), 0.92),
           angle=0.0, angle_jitter=0.04, length=520, cover=3.0, wobble=3)
lay_screen(board, (-200, roof_top - 14, W + 200, H + 40), deck, roof_colour, angle=lambda x, y: 0.02 * (y - 900) / 300,
           angle_jitter=0.03, length=420, cover=5.5, wobble=2)


# Under the line the screed has not dried all day. Where it is still wet it is darker, and the
# washing shows in it, upside down and dragged toward her by the roughness of the screed.
def seen_in_floor(Q, r):
    """What the reflected ray r from floor point Q meets: washing, the wall, or sky."""
    for line, sheets in ((near, NEAR), (far, FAR)):
        n3 = v3(line.n[0], 0, line.n[1])
        den = r @ n3
        if abs(den) < 1e-6:
            continue
        t = ((v3(line.a[0], 0, line.a[1]) - Q) @ n3) / den
        if t <= 0:
            continue
        Hh = Q + t * r
        sa = (Hh[[0, 2]] - line.a) @ line.d
        for sh in sheets:
            u = (sa - sh.s0) / sh.width
            v = (line.at(sa)[1] - Hh[1]) / sh.length
            if 0 <= u <= 1 and 0 <= v <= 1:
                return cloth(sh, vary=0.0)(u, v)
    t = (ZB - Q[2]) / max(r[2], 1e-6)
    if Q[1] + t * r[1] < PAR_H:
        return tone(mix((LIME, 3), (white, 1)) * LAMP * 0.85 * 0.68, 1.7)
    el = np.arcsin(np.clip(r[1], -1, 1))
    k = np.clip(el / 0.42, 0, 1) ** 0.75
    return np.exp(np.log(SKY_LOW) * (1 - k) + np.log(SKY_TOP) * k)


def wetness(Q):
    w = 0.0
    for sh in NEAR:
        line = sh.line
        rel = Q[[0, 2]] - line.a
        sa, dn = rel @ line.d, -(rel @ line.n)
        u = (sa - sh.s0) / sh.width
        inside = np.clip(min(u, 1 - u) / 0.12 + 0.5, 0, 1)
        w = max(w, inside * np.exp(-((dn + 0.15) / 0.45) ** 2))
    return w


def damp_floor(x, y):
    Q = cam.on_ground(x, y)
    w = wetness(Q)
    d = unit(Q - E)
    F = (0.15 + 0.5 * (1 - abs(d[1])) ** 3) * w
    base = roof_colour(x, y) * (1 - 0.3 * w)
    return base * (1 - F) + seen_in_floor(Q, d * v3(1, -1, 1)) * F


sheen = Brush(width=16, bristle=1.6, opacity=0.85, pickup=0.45, dryness=0.0, thickness=0.05, jitter=0.02, deplete=0.0005,
              taper=(0.3, 0.3), level=0.6)
y_line = P(v3(near.b[0], 0, near.b[1]))[1] - 20     # the floor under the far end of the line
n_sheen = int(W * (H - y_line) * 10.0 / (80 * 16))
for i in range(n_sheen):
    x, y = rng.uniform(-30, W + 30), rng.uniform(y_line, H + 20)
    if wetness(cam.on_ground(x, y)) < 0.06:
        continue
    k = 0.4 + 0.6 * (y - roof_top) / (H - roof_top)
    L = rng.uniform(70, 130) * k
    ys = np.linspace(y - L / 2, y + L / 2, 5)
    xs = x + rng.normal(0, 1.0) * np.linspace(-1, 1, 5)
    board.stroke(np.stack([xs, ys], 1), sheen.but(width=16 * k), [damp_floor(a, b) for a, b in zip(xs, ys)], wobble=0.3)

# the joints in the screed, every three metres each way, filled with tar and the dust in them
jnt = Brush(width=3, bristle=1.0, opacity=0.6, gap=0.1, pickup=0.3, thickness=0.05, taper=(0.1, 0.1))
jc = tone(mix((LIME, 2), (DUST, 2), (black, 0.5)) * LAMP * 0.14, 1.7)
for z in np.arange(3.2, ZB, 3.0):
    a, b = P(v3(XL, 0, z)), P(v3(9.0, 0, z))
    board.stroke(np.linspace(a, b, 8), jnt.but(width=max(1.4, 14.0 / z)), jc * np.exp(rng.normal(0, 0.05, 3)), wobble=0.6)
for x in np.arange(XL + 2.6, 9.0, 3.0):
    zs = np.linspace(2.0, ZB, 24)
    pts = P(np.stack([np.full_like(zs, x), np.zeros_like(zs), zs], 1))
    board.stroke(pts, jnt.but(width=3.0), jc * np.exp(rng.normal(0, 0.05, 3)), wobble=0.6,
                 pressure=lambda t: 0.6 + 0.4 * (1 - t))

# the back wall and the side wall, meeting in the corner on the left
def wall_poly(a, b, h0=0.0, h1=PAR_H):
    return np.array([P(v3(a[0], h1, a[1])), P(v3(b[0], h1, b[1])), P(v3(b[0], h0, b[1])), P(v3(a[0], h0, a[1]))])


back = wall_poly((XL, ZB), (9.0, ZB))
side = wall_poly((XL, 2.0), (XL, ZB))
# a stretch of the back wall was built up higher at some point and never rendered to match
raise_a, raise_b = -4.2, -1.0
raised = wall_poly((raise_a, ZB), (raise_b, ZB), PAR_H, PAR_H + 0.38)


def wall_colour(face):
    def f(x, y):
        k = {"back": 1.0, "side": 0.55, "raised": 0.92}[face]
        Q = cam.on_ground(x, y, 0.5)
        c = mix((LIME, 3), (white, 1)) * LAMP * 0.85 * k
        if face == "raised":
            c = mix((c, 3), (scale(burnsi, 0.4), 0.5))
        c = c * (0.94 + 0.06 * np.sin(Q[0] * 1.7 + 0.3))
        hz = 0.32 if face != "side" else 0.2
        c = c * (1 - hz) + SKY_LOW * hz
        return tone(c, 1.7) * np.exp(rng.normal(0, 0.035, 3))
    return f


for poly, face in [(back, "back"), (raised, "raised"), (side, "side")]:
    board.tape(poly, feather=0.7)
    x0, y0 = poly.min(0)
    x1, y1 = poly.max(0)
    ang = 0.0 if face != "side" else np.arctan2(*(P(v3(XL, PAR_H, ZB)) - P(v3(XL, PAR_H, 6.0)))[::-1])
    lay_screen(board, (x0 - 10, y0 - 4, x1 + 10, y1 + 4), deck.but(width=12, thickness=0.1), wall_colour(face),
               angle=ang, angle_jitter=0.03, length=150, cover=8.0, wobble=0.6)
    board.untape()
# the copings catch the sky; the foot of the walls is where the dust has drifted
cop = Brush(width=5, opacity=0.8, gap=0.02, thickness=0.5, pickup=0.15, taper=(0.03, 0.03))
copc = tone(LIME * SKY_LOW * 1.25, 1.7)
for a, b, hh in [((XL, ZB), (raise_a, ZB), PAR_H), ((raise_b, ZB), (9.0, ZB), PAR_H), ((raise_a, ZB), (raise_b, ZB), PAR_H + 0.38),
                 ((XL, 2.0), (XL, ZB), PAR_H)]:
    board.stroke(P(np.linspace(v3(a[0], hh, a[1]), v3(b[0], hh, b[1]), 12)), cop, copc, wobble=0.8)
foot = Brush(width=10, opacity=0.4, gap=0.05, thickness=0.05, pickup=0.4, taper=(0.2, 0.2))
for a, b in [((XL, ZB), (9.0, ZB)), ((XL, 2.0), (XL, ZB))]:
    for k in range(3):
        board.stroke(P(np.linspace(v3(a[0], 0.04, a[1]), v3(b[0], 0.04, b[1]), 12)) + rng.normal(0, 1.5, 2), foot,
                     tone(DUST * SKY_LOW * 0.55, 1.7), wobble=1.5)
# the corner, darker where the two walls meet
board.stroke([P(v3(XL, PAR_H, ZB)), P(v3(XL, 0, ZB))], Brush(width=3, opacity=0.5, gap=0, thickness=0.1),
             tone(LIME * SKY_LOW * 0.55, 1.7))
board.dry()
board.stage("the roof and its walls")

# =================================================================================================
# 3. Posts, and the far line.
# =================================================================================================
iron = mix((black, 1), (white, 1.4), (ultra, 0.2))


def post(xz, h, k=1.0):
    top, bot = v3(xz[0], h, xz[1]), v3(xz[0], 0, xz[1])
    wpx = max(2.5, 0.05 * cam.f / (xz[1] - E[2]))
    board.stroke([P(top), P(bot)], Brush(width=wpx, opacity=0.95, gap=0.0, thickness=0.6, taper=(0.0, 0.02), pickup=0.1),
                 tone(iron * SKY_LOW * 0.55 * k, 1.7))
    board.stroke([P(top) + (wpx * 0.3, 0), P(bot) + (wpx * 0.3, 0)], Brush(width=wpx * 0.35, opacity=0.6, gap=0, thickness=0.3),
                 tone(iron * SKY_LOW * 0.95 * k, 1.7))
    # the cross bar the wires hang from
    board.stroke([P(top + v3(-0.25 * near.n[0], 0, -0.25 * near.n[1])), P(top + v3(2.3 * -near.n[0] + 0.25 * -near.n[0], 0,
                 -2.55 * near.n[1]))], Brush(width=wpx * 0.8, opacity=0.9, gap=0, thickness=0.5), tone(iron * SKY_LOW * 0.6 * k, 1.7))


far_end = near.at(near.span)
post((far_end[0], far_end[2]), near.y0 + 0.05, 0.95)

blk = Brush(width=18, bristle=1.5, opacity=0.95, pickup=0.3, dryness=0.03, thickness=0.35, jitter=0.03, deplete=0.0006)
for s in FAR[::-1]:
    lay_cloth(board, cam, s, blk.but(width=14), cloth(s, gain=0.95), along="v", length=70, cover=6.0, wobble=0.5, run=True)
board.dry()
board.stage("the post at the end, and the far line")

# =================================================================================================
# 4. Near line, laid in flat, one colour a stroke: where the cloth is.
# =================================================================================================
lay = blk.but(width=30, opacity=0.9)
for s in NEAR[::-1]:
    flat = cloth(s, gain=0.92, vary=0.02)
    lay_cloth(board, cam, s, lay, flat, along="v", length=200, cover=3.0,
              wobble=1.0, margin=0.08)
board.dry()
board.stage("near line, laid in where the cloth is")

# =================================================================================================
# 5. The folds, from the pegs down: each stroke runs out of the fold into the sky's light.
# =================================================================================================
fold_b = Brush(width=16, bristle=1.4, opacity=0.9, pickup=0.35, dryness=0.0, thickness=0.4, jitter=0.025, deplete=0.0005,
               taper=(0.2, 0.25))
for s in NEAR[::-1]:
    near_k = float(np.clip(4.5 / (s.pos(0.5, 0.5)[2] - E[2]), 0.65, 1.3))     # a smaller brush for the far pieces
    rel = float(np.clip(near_k, 0.5, 1.0))
    lay_cloth(board, cam, s, fold_b, cloth(s, vary=0.015, relief=rel), along="v", length=260 * near_k, cover=8.0, wobble=0.6, margin=0.06,
              run=True, width_fn=lambda u, v, k=near_k: 16 * k)
    lay_cloth(board, cam, s, fold_b.but(width=10 * near_k), cloth(s, vary=0.012, relief=rel), along="v", length=160 * near_k, cover=2.5, wobble=0.4,
              margin=0.03, run=True)
board.dry()
board.stage("the folds, from the pegs down")

# =================================================================================================
# 6. Hems and the fold over the wire, across; then the wire and the pegs.
# =================================================================================================
hem_b = fold_b.but(width=8, pickup=0.5, opacity=0.6)
for s in NEAR[::-1]:
    lay_cloth(board, cam, s, hem_b, cloth(s, vary=0.015), along="u", length=90, cover=1.2, wobble=0.4, margin=0.04,
              where=lambda u, v: v > 0.9, run=True)
    if s.band:
        lay_cloth(board, cam, s, hem_b, cloth(s, vary=0.015), along="u", length=110, cover=0.6, wobble=0.3, margin=0.02,
                  where=lambda u, v, b=s.band: v < b + 0.01, run=True)
fine = Brush(width=3, bristle=0.9, opacity=0.9, pickup=0.0, thickness=0.8, jitter=0.02, gap=0.0, taper=(0.0, 0.0), deplete=0.0)
wire = tone(iron * SKY_LOW * 0.3, 1.7)
board.tape(*[o.outline(cam) for o in NEAR], outside=True, feather=0.6)
board.stroke(P(far.pts(n=80)), fine.but(width=1.8), wire, smooth=False)
board.untape()
board.stroke(P(near.pts(n=80)), fine.but(width=2.6), wire, smooth=False)
peg_c = mix((burnsi, 2), (black, 1.5), (ochre, 0.5))
for group in (FAR, NEAR):
    if group is FAR:
        board.tape(*[o.outline(cam) for o in NEAR], outside=True, feather=0.6)
    for sh in group:
        for k in range(sh.pegs):
            u = k / (sh.pegs - 1) + rng.normal(0, 0.01)
            top = sh.line.at(sh.s0 + u * sh.width)
            a, b = P(top + v3(0, 0.025, 0)), P(top - v3(0, 0.06, 0))
            wpx = max(2.5, 0.016 * cam.f / max(top[2] - E[2], 0.5))
            board.stroke([a, b + rng.normal(0, 0.5, 2)], fine.but(width=wpx, thickness=1.2),
                         scale(peg_c, rng.uniform(0.8, 1.2) * (0.8 if group is FAR else 1)))
    board.untape()
board.dry()
board.stage("hems, wire and pegs")

# =================================================================================================
# 7. The basket, with what she has already taken in, still wet.
# =================================================================================================
bx, bz, rx, rz, bh = -1.55, 4.3, 0.33, 0.23, 0.27


def ring(y, k=1.0, t0=0.0, t1=2 * np.pi, n=40):
    t = np.linspace(t0, t1, n)
    return P(np.stack([bx + rx * k * np.cos(t), np.full(n, y), bz + rz * k * np.sin(t)], 1))


def lamp_on(N):
    N = unit(np.asarray(N, dtype=np.float64))
    return irradiance(N)


PLASTIC = mix((turq, 2), (white, 1.0), (rawsi, 0.9))
sit = tone(mix((LIME, 3), (DUST, 1)) * LAMP * 0.16, 1.7)
foot = ring(0.0, 1.3, 0, 2 * np.pi, 50)
board.tape(foot, feather=6.0)
lay_screen(board, tuple(np.r_[foot.min(0) - 4, foot.max(0) + 4]), Brush(width=14, opacity=0.35, pickup=0.5, thickness=0.05),
           lambda x, y: sit, angle=0.0, length=60, cover=4, wobble=0.5)
board.untape()
front = np.vstack([ring(bh, 1.0, np.pi, 2 * np.pi), ring(0.0, 0.86, 2 * np.pi, np.pi)])
board.tape(front, feather=0.7)
for t in np.linspace(np.pi - 0.1, 2 * np.pi + 0.1, 80):
    N = v3(np.cos(t), 0.05, np.sin(t) * rx / rz)
    c = tone(PLASTIC * lamp_on(N) * 0.75, 1.7) * np.exp(rng.normal(0, 0.04))
    a = P(v3(bx + rx * np.cos(t), bh, bz + rz * np.sin(t)))
    b = P(v3(bx + 0.86 * rx * np.cos(t), 0.0, bz + 0.86 * rz * np.sin(t)))
    board.stroke([a, b], Brush(width=9, opacity=0.95, pickup=0.3, thickness=0.6, taper=(0.02, 0.05)), c)
for row, y in enumerate((0.07, 0.13, 0.19)):
    k = 0.86 + 0.14 * y / bh
    for t in np.linspace(np.pi + 0.25, 2 * np.pi - 0.25, 13) + 0.12 * (row % 2):
        p0 = v3(bx + rx * k * np.cos(t), y, bz + rz * k * np.sin(t))
        a, b = P(p0 - v3(-np.sin(t), 0, np.cos(t)) * 0.025), P(p0 + v3(-np.sin(t), 0, np.cos(t)) * 0.025)
        board.stroke([a, b], Brush(width=3.5, opacity=0.85, gap=0, thickness=0.2, taper=(0, 0)), tone(PLASTIC * LAMP * 0.16, 1.7))
board.untape()
# inside, heaped: sheets folded wet and laid in, standing up over the rim
# the top of the heap is not level: a sheet slumped over the near side, another folded on top
tt = np.linspace(0, np.pi, 30)
bump = bh + 0.035 + 0.035 * np.sin(2.3 * tt + 0.5) ** 2 + 0.02 * np.sin(5.1 * tt)
top = np.stack([P(v3(bx + rx * 0.8 * np.cos(t), y, bz + rz * 0.8 * np.sin(t))) for t, y in zip(tt, bump)])
heap_poly = np.vstack([ring(bh, 0.97, np.pi, 2 * np.pi, 30), top])
board.tape(heap_poly, feather=0.8)
hx0, hy0 = heap_poly.min(0)
hx1, hy1 = heap_poly.max(0)
lay_screen(board, (hx0 - 4, hy0 - 4, hx1 + 4, hy1 + 4), Brush(width=8, opacity=0.9, pickup=0.4, thickness=0.5, taper=(0.15, 0.15)),
           lambda x, y: tone(COTTON * LAMP * (0.36 + 0.2 * (1 - (y - hy0) / (hy1 - hy0 + 1e-6))), 1.7) * np.exp(rng.normal(0, 0.03, 3)),
           angle=0.0, angle_jitter=0.08, length=40, cover=5, wobble=0.6)
for k, yy in enumerate((bh + 0.075, bh + 0.045, bh + 0.02)):   # the folded edges, one sheet on another
    t0 = np.pi * (1.1 + rng.uniform(-0.05, 0.08))
    edge = ring(yy, 0.86 - 0.03 * k, t0, t0 + np.pi * rng.uniform(0.6, 0.78), 14) + rng.normal(0, 0.8, (14, 2))
    board.stroke(edge, Brush(width=2.4, opacity=0.55, gap=0, thickness=0.3), tone(COTTON * LAMP * 0.2, 1.7), wobble=0.4)
board.untape()
board.stroke(ring(bh, 1.0, np.pi * 0.98, np.pi * 2.02, 40), Brush(width=5, opacity=0.95, gap=0, thickness=1.2, pickup=0.1,
             taper=(0.05, 0.05)), tone(PLASTIC * LAMP * 0.95, 1.7))
# two pegs that went on the floor and stayed there
for px_, pz_, ang in [(-0.65, 4.7, 0.5), (-0.45, 4.9, 2.3), (-2.4, 4.5, 1.2)]:
    a = P(v3(px_, 0.01, pz_))
    d = np.array([np.cos(ang), np.sin(ang) * 0.35]) * 11
    board.stroke([a - d + (1, 4), a + d + (1, 4)], Brush(width=4, opacity=0.3, gap=0, thickness=0.05), sit)
    board.stroke([a - d, a + d], Brush(width=5, opacity=0.95, gap=0, thickness=1.0, taper=(0.05, 0.05)),
                 scale(mix((burnsi, 2), (black, 1.5), (ochre, 0.5)), 1.5))
board.dry()
board.stage("the basket, what is already in")

finish(board, HERE, title="Xlokk, nothing dries", artist="carmela-zammit", year=1987,
       medium="Oil on cotton sheeting, red oxide ground", made="2026-11-12")
