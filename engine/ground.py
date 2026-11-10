"""Supports. Each returns a tooth map in 0..1: high spots catch a dry brush first."""
import numpy as np
from PIL import Image


def fbm(w, h, rng, base=6, octaves=5, falloff=0.55):
    out = np.zeros((h, w), dtype=np.float32)
    amp, total = 1.0, 0.0
    for o in range(octaves):
        n = base * 2 ** o
        gh, gw = max(2, int(n * h / w) + 1), n + 1
        g = (rng.random((gh, gw)) * 255).astype(np.uint8)
        layer = np.asarray(Image.fromarray(g).resize((w, h), Image.BICUBIC), dtype=np.float32) / 255.0
        out += layer * amp
        total += amp
        amp *= falloff
    out /= total
    return (out - out.min()) / (out.max() - out.min() + 1e-9)


def linen(w, h, rng, pitch=4.2):
    """Woven canvas: two thread directions with slubs."""
    y, x = np.mgrid[0:h, 0:w].astype(np.float32)
    wob = fbm(w, h, rng, base=5, octaves=3) * 6.0
    warp = 0.5 + 0.5 * np.sin(2 * np.pi * (x + wob) / pitch)
    wob2 = fbm(w, h, rng, base=5, octaves=3) * 6.0
    weft = 0.5 + 0.5 * np.sin(2 * np.pi * (y + wob2) / pitch)
    t = 0.45 * warp * weft + 0.25 * np.maximum(warp, weft) + 0.30 * fbm(w, h, rng, base=90, octaves=3)
    return ((t - t.min()) / (t.max() - t.min())).astype(np.float32)


def hardboard_mesh(w, h, rng, pitch=5.5):
    """The rough back of hardboard: a pressed diamond mesh, a little crushed in places."""
    y, x = np.mgrid[0:h, 0:w].astype(np.float32)
    x, y = x * 0.982 - y * 0.191, x * 0.191 + y * 0.982   # boards are never cut square to the mesh
    a = np.sin(2 * np.pi * (x + y) / (pitch * 1.414))
    b = np.sin(2 * np.pi * (x - y) / (pitch * 1.414))
    mesh = 0.5 + 0.5 * a * b
    crush = fbm(w, h, rng, base=7, octaves=4)
    grit = fbm(w, h, rng, base=160, octaves=2)
    mid = fbm(w, h, rng, base=40, octaves=3)
    t = mesh * (0.35 + 0.65 * crush) * 0.42 + grit * 0.33 + mid * 0.25
    return ((t - t.min()) / (t.max() - t.min())).astype(np.float32)


def paper(w, h, rng, grain=120):
    t = 0.6 * fbm(w, h, rng, base=grain, octaves=3) + 0.4 * fbm(w, h, rng, base=14, octaves=4)
    return ((t - t.min()) / (t.max() - t.min())).astype(np.float32)


def smooth_panel(w, h, rng):
    return (0.5 + 0.1 * (fbm(w, h, rng, base=200, octaves=2) - 0.5)).astype(np.float32)
