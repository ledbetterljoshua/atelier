"""Colour as linear reflectance. Paint mixes like pigment (geometric mean), not like light."""
import numpy as np

FLOOR = 0.004  # nothing is perfectly black


def srgb_to_linear(c):
    c = np.asarray(c, dtype=np.float64)
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def linear_to_srgb(c):
    c = np.clip(c, 0.0, 1.0)
    return np.where(c <= 0.0031308, c * 12.92, 1.055 * c ** (1 / 2.4) - 0.055)


def hexc(s):
    """'#rrggbb' -> linear reflectance."""
    s = s.lstrip("#")
    rgb = np.array([int(s[i:i + 2], 16) for i in (0, 2, 4)]) / 255.0
    return np.maximum(srgb_to_linear(rgb), FLOOR)


def mix(*parts):
    """Pigment mix. mix(a, b) is half and half; mix((a, 3), (b, 1)) is three parts to one."""
    cols, ws = [], []
    for p in parts:
        if isinstance(p, tuple) and len(p) == 2 and np.ndim(p[0]) == 1:
            cols.append(p[0]); ws.append(float(p[1]))
        else:
            cols.append(p); ws.append(1.0)
    ws = np.array(ws) / np.sum(ws)
    logs = np.log(np.maximum(np.array(cols, dtype=np.float64), FLOOR))
    return np.exp((logs * ws[:, None]).sum(axis=0))


def scale(c, k):
    """Brighten or darken without changing hue (a stand-in for more or less light on it)."""
    return np.clip(np.asarray(c) * k, FLOOR, 1.0)
