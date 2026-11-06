"""env_c3p2_archive_kit -- palette, super-ramps, light hue tables and small painters for L_C3_Registry.

Owned by the registry art stream (Chapter 3 part 2).  Builds on tools/pixelgen/pg.py and the tone-space
painting model of env_veltrava_hall_kit.py (TLayer, Ramps, baked light fields -- imported, never modified):
every pixel is painted as (ramp, tone); baked light adds tone and, where it is strong, moves a pixel onto the
light's counterpart ramp at equal luminance (lamp -> paper/oak, snow light -> slate/snow, fire -> the fire
ramp).  Output is palette-pure in the 'registry' palette of data/chapters/c3.json (checked at build time).
"""
from __future__ import annotations

import json
import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import pg  # noqa: E402
import env_veltrava_hall_kit as hk  # noqa: E402  (TLayer, Ramps, light fields, fonts -- read-only use)

DATE = '2026-11-06'
ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))

# 'registry' = data/chapters/c3.json palettes.registry (binding, compared at build time)
REG = {
    'night': ['#06080D', '#0B1017', '#121A23', '#1A2530'],
    'slate': ['#1E2836', '#2A3646', '#3A4859', '#4F5E70', '#687789'],
    'oak': ['#1C120C', '#2B1B12', '#3D271A', '#553826', '#6E4A33'],
    'lamp_green': ['#14261C', '#1F3A2A', '#2E5640', '#4A7A5C', '#7FAE8C'],
    'paper': ['#4A4436', '#6B6350', '#8E856C', '#B3A98D', '#D8CFB2'],
    'brass': ['#4A3415', '#73531F', '#9C7630', '#C49A48', '#E8C779'],
    'snow': ['#7D8796', '#A1AAB7', '#C2C9D2', '#DEE2E7', '#F2F3F5'],
    'fire': ['#3A0F08', '#6E1E0C', '#A8381A', '#D8662A', '#F2A044', '#FCE0A0'],
    'red': ['#4A1712', '#7A2218', '#A8382E', '#C8503C'],
    'skin': ['#885551', '#B47B65', '#D5A081'],
}
pg.PALETTES['registry'] = REG


def reg_hex() -> set:
    return {h.upper() for r in REG.values() for h in r}


def check_c3_palette() -> list[str]:
    p = os.path.join(ROOT, 'data', 'chapters', 'c3.json')
    try:
        with open(p, encoding='utf-8') as f:
            ref = json.load(f).get('palettes', {}).get('registry', {})
    except (OSError, ValueError):
        return ['c3.json not readable']
    notes = []
    for ramp, cols in REG.items():
        if [c.upper() for c in cols] != [c.upper() for c in ref.get(ramp, [])]:
            notes.append('registry.%s differs from c3.json' % ramp)
    return notes


def _lum(h: str) -> float:
    return hk.lum(pg.hx(h))


def by_lum(cols: list) -> list:
    return sorted(cols, key=_lum)


N, SL, OK, GR, PA, BR, SN, FI, RD, SK = (REG[k] for k in ('night', 'slate', 'oak', 'lamp_green', 'paper', 'brass',
                                                         'snow', 'fire', 'red', 'skin'))

RAMPS = {
    'N': [N[0], N[1], N[2], N[3]],                                                   # poche / night (0..3)
    'W': [N[1], N[2], N[3], SL[0], SL[1], SL[2], SL[3], SL[4], SN[0], SN[1]],          # limewash (0..9)
    'S': [N[0], N[1], SL[0], SL[1], SL[2], SL[3], SL[4], SN[0]],                     # painted steel (0..7)
    'D': [N[0], OK[0], OK[1], OK[2], OK[3], OK[4], BR[2], BR[3]],                   # oak (0..7)
    'P': [N[2], OK[2], PA[0], PA[1], PA[2], PA[3], PA[4]],                          # paper / cream (0..6)
    'B': [OK[1], BR[0], BR[1], BR[2], BR[3], BR[4], FI[5]],                         # brass (0..6)
    'G': [N[0], GR[0], GR[1], GR[2], GR[3], GR[4]],                                 # oil green (0..5)
    'R': [N[0], RD[0], RD[1], RD[2], RD[3], FI[4]],                                 # red (0..5)
    'F': [N[0], FI[0], FI[1], FI[2], FI[3], FI[4], FI[5]],                          # fire (0..6)
    'C': [N[1], N[3], SL[1], SL[2], SL[3], SL[4], SN[0], SN[1], SN[2], SN[3]],        # cold light (0..9)
    'SN': [SL[2], SL[3], SL[4], SN[0], SN[1], SN[2], SN[3], SN[4]],                  # snow (0..7)
    'I': [N[0], N[1], N[2], SL[0]],                                                  # ink / black iron (0..3)
    'K': by_lum([N[0], OK[0], OK[1], RD[0], OK[2], RD[1], OK[3], RD[2]]),            # brick (0..7)
    'Y': [SK[0], SK[1], SK[2]],                                                     # skin (0..2)
}
R = hk.Ramps(RAMPS)

# hue counterparts (src ramp -> ramp a pixel moves onto when the light is strong)
WARM_OF = {'W': 'P', 'S': 'D', 'C': 'P', 'SN': 'P', 'N': 'D', 'I': 'D', 'K': 'D'}
COLD_OF = {'D': 'S', 'P': 'SN', 'B': 'P', 'W': 'C', 'N': 'C', 'I': 'S', 'K': 'S', 'G': 'C', 'Y': 'Y'}
FIRE_OF = {'W': 'F', 'S': 'R', 'C': 'F', 'SN': 'F', 'P': 'F', 'D': 'F', 'G': 'D', 'N': 'R', 'I': 'R', 'B': 'F',
           'K': 'R', 'R': 'F'}
GAINS = {
    'W': (2.4, 2.6, 2.4), 'S': (2.2, 2.4, 2.4), 'D': (2.6, 1.4, 2.0), 'P': (2.2, 2.2, 2.4), 'B': (2.4, 1.6, 2.0),
    'G': (1.8, 1.6, 1.8), 'R': (1.6, 0.8, 1.2), 'F': (1.4, 0.6, 1.0), 'C': (1.6, 2.4, 2.0), 'SN': (1.6, 2.2, 2.0),
    'N': (1.4, 1.6, 1.4), 'I': (0.7, 0.7, 0.7), 'K': (2.0, 1.4, 1.8), 'Y': (1.0, 0.6, 1.0),
}


def tlayer(w: int, h: int, name: str = 'layer') -> 'hk.TLayer':
    return hk.TLayer(w, h, R, name, warm_of=dict(WARM_OF), cold_of=dict(COLD_OF), gains=GAINS)


def resolve_state(lay, fields: dict, fire: bool, seed: int = 0, exposure: float = 0.76):
    """Resolve a TLayer with the hue table of the state (lamps: WARM_OF, fire: FIRE_OF). `exposure` scales the
    painted (unlit) tones of every lit pixel first: the night keeps its darks, the baked lights make the pools."""
    keep = lay.warm_of
    t0 = lay.tone.copy()
    m = ~lay.emis & ~lay.unlit
    lay.tone[m] = lay.tone[m] * exposure
    lay.warm_of = FIRE_OF if fire else WARM_OF
    lay.resolve(fields, seed=seed)
    lay.warm_of = keep
    lay.tone = t0
    return lay


def add_pools(F: dict, lights: list, floor_y: int, h: int, w: int):
    """Light pools on the floor under lamps ('pool': strength) -- a dithered ellipse that widens toward the
    viewer (the baked counterpart of the Godot light, like the palais bake)."""
    for lt in lights:
        k = float(lt.get('pool', 0.0))
        if k <= 0:
            continue
        x = float(lt['pos'][0]) + float(lt.get('pool_dx', 0.0))
        depth = int(lt.get('pool_depth', 44))
        for yy in range(floor_y + 1, min(h, floor_y + depth)):
            f = (1 - (yy - floor_y) / depth) ** 1.4
            hw = float(lt.get('pool_w', 8)) + (yy - floor_y) * float(lt.get('pool_spread', 0.5))
            xs = np.arange(max(0, int(x - hw - 2)), min(w, int(x + hw + 3)))
            fall = np.clip(1 - np.abs(xs - x) / max(1.0, hw), 0, 1) ** 0.8
            F[lt.get('kind', 'warm')][yy, xs] += k * f * fall * float(lt.get('energy', 1.0))
    return F


# --------------------------------------------------------------------------- helpers
light_fields = hk.light_fields
sub_fields = hk.sub_fields
dilate, erode, edge_of, box_blur, arch_mask = hk.dilate, hk.erode, hk.edge_of, hk.box_blur, hk.arch_mask
text_mask, text_width, bres, stroke_mask = hk.text_mask, hk.text_width, hk.bres, hk.stroke_mask


def noise(w, h, cell, seed, octaves=3):
    return pg.value_noise(w, h, cell, seed, octaves=octaves) - 0.5


def bevel(lay, x, y, w, h, ramp, face, hi=None, lo=None, hgt=0.5):
    lay.rect(x, y, w, h, ramp, face, hgt=hgt)
    if hi is not None:
        lay.rect(x, y, w, 1, ramp, hi, hgt=hgt * 0.8)
        lay.rect(x, y, 1, h, ramp, hi, hgt=hgt * 0.8)
    if lo is not None:
        lay.rect(x, y + h - 1, w, 1, ramp, lo, hgt=hgt * 0.6)
        lay.rect(x + w - 1, y, 1, h, ramp, lo, hgt=hgt * 0.6)


def recess(lay, x, y, w, h, ramp, face, shadow=None, light=None, hgt=-0.3):
    lay.rect(x, y, w, h, ramp, face, hgt=hgt)
    if shadow is not None:
        lay.rect(x, y, w, 1, ramp, shadow, hgt=hgt)
        lay.rect(x, y, 1, h, ramp, shadow, hgt=hgt)
    if light is not None:
        lay.rect(x, y + h - 1, w, 1, ramp, light, hgt=hgt)
        lay.rect(x + w - 1, y + 1, 1, h - 1, ramp, light, hgt=hgt)


def frame(lay, x, y, w, h, ramp='D', face=2.6, hi=4.0, lo=1.4, hgt=0.6, shadow=('W', 1.6)):
    """Picture frame (2 px moulding) with a drop shadow on the wall."""
    lay.rect(x - 2, y - 2, w + 4, h + 4, ramp, face, hgt=hgt)
    lay.rect(x - 2, y - 2, w + 4, 1, ramp, hi, hgt=hgt + 0.05)
    lay.rect(x - 2, y - 2, 1, h + 4, ramp, hi - 0.6, hgt=hgt)
    lay.rect(x - 2, y + h + 1, w + 4, 1, ramp, lo, hgt=hgt - 0.1)
    lay.rect(x + w + 1, y - 2, 1, h + 4, ramp, lo, hgt=hgt - 0.1)
    if shadow:
        lay.rect(x + w + 2, y, 1, h + 3, shadow[0], shadow[1])
        lay.rect(x, y + h + 2, w + 2, 1, shadow[0], shadow[1])


def pseudo_text(lay, x, y, w, rows, ramp, tone, seed=0, gap=2, rag=0.35, crisp=True):
    rng = np.random.default_rng(seed)
    for r in range(rows):
        xx = x
        end = x + w - int(rng.random() * w * rag)
        while xx < end:
            wl = int(rng.integers(2, 6))
            lay.rect(xx, y + r * gap, min(wl, end - xx), 1, ramp, tone, crisp=crisp)
            xx += wl + 1


def text(lay, s, x, y, ramp, tone, font='35', spacing=1, center=False, **kw):
    m = text_mask(s, font, spacing)
    if center:
        x = int(round(x - m.shape[1] / 2))
    kw.setdefault('flat', True)
    kw.setdefault('crisp', True)
    lay.put(m, x, y, ramp, tone, **kw)
    return m.shape[1]


def rivets(lay, x0, x1, y, step, ramp='S', tone=4.4, shadow=1.6, hgt=0.6):
    for x in range(int(x0), int(x1), step):
        lay.px(x, y, ramp, tone, hgt=hgt)
        lay.px(x + 1, y + 1, ramp, shadow, hgt=hgt * 0.4)


def bricks(lay, x, y, w, h, ramp, base, seed=0, course=4, length=9, joint=-0.55, var=0.35, hgt=0.12,
           mask=None):
    """Brick masonry in stretcher bond (painted over / limewashed: low relief, joints a little darker)."""
    rng = np.random.default_rng(seed)
    t = np.full((h, w), base, np.float32)
    hg = np.full((h, w), hgt, np.float32)
    for row in range(0, h, course):
        off = (row // course) % 2 * (length // 2)
        for bx in range(-length, w + length, length):
            x0 = bx + off
            dv = rng.normal(0, var)
            a, b = max(0, x0), min(w, x0 + length - 1)
            if b > a:
                t[row:row + course - 1, a:b] += dv
        t[min(h - 1, row + course - 1), :] += joint
        hg[min(h - 1, row + course - 1), :] = 0.0
        for bx in range(-length, w + length, length):
            xj = bx + off + length - 1
            if 0 <= xj < w:
                t[row:row + course - 1, xj] += joint
                hg[row:row + course - 1, xj] = 0.0
    m = np.ones((h, w), bool) if mask is None else mask
    lay.put(m, x, y, ramp, t, hgt=hg, flat=False)
    return t


def grain(lay, x, y, w, h, ramp, base, seed=0, amp=0.45, cell=(1.5, 14), hgt=0.4, vertical=True):
    """Wood grain: stretched noise (vertical boards by default)."""
    cx, cy = cell if vertical else cell[::-1]
    n1 = pg.value_noise(w, h, 1, seed, octaves=1)
    nn = noise(max(2, int(w * 6 / max(1, cx))), max(2, int(h * 6 / max(1, cy))), 3, seed + 1, octaves=2)
    from PIL import Image
    img = Image.fromarray(((nn + 0.5) * 255).astype(np.uint8)).resize((w, h), Image.BILINEAR)
    g = np.asarray(img, np.float32) / 255.0 - 0.5
    t = base + g * amp * 2 + (n1 - 0.5) * 0.12
    lay.put(np.ones((h, w), bool), x, y, ramp, t, hgt=hgt, flat=False)


def soft_box(w, h, r):
    """Mask of a box with rounded corners (radius r)."""
    m = np.ones((h, w), bool)
    for yy in range(h):
        for xx in range(w):
            dx = max(0, r - xx - 0.5, xx + 0.5 - (w - r))
            dy = max(0, r - yy - 0.5, yy + 0.5 - (h - r))
            if dx * dx + dy * dy > r * r:
                m[yy, xx] = False
    return m


def disc(d):
    yy, xx = np.mgrid[0:d, 0:d]
    c = (d - 1) / 2.0
    return (xx - c) ** 2 + (yy - c) ** 2 <= (d / 2.0) ** 2


# --------------------------------------------------------------------------- periodic noise (seamless loops)
def periodic_noise(w, h, cell_x, cell_y, seed, octaves=3, per_x=None, per_y=None):
    """Value noise (h, w) in [0, 1] that tiles with period per_x / per_y (defaults: w / h)."""
    rng = np.random.default_rng(seed)
    per_x = per_x or w
    per_y = per_y or h
    out = np.zeros((h, w), np.float32)
    amp, tot = 1.0, 0.0
    cx, cy = float(cell_x), float(cell_y)
    for _ in range(octaves):
        nx = max(1, int(round(per_x / cx)))
        ny = max(1, int(round(per_y / cy)))
        grid = rng.random((ny, nx)).astype(np.float32)
        xs = np.arange(w) * nx / per_x
        ys = np.arange(h) * ny / per_y
        x0 = np.floor(xs).astype(int); y0 = np.floor(ys).astype(int)
        fx = xs - x0; fy = ys - y0
        fx = fx * fx * (3 - 2 * fx); fy = fy * fy * (3 - 2 * fy)
        a = grid[(y0 % ny)[:, None], (x0 % nx)[None, :]]
        b = grid[(y0 % ny)[:, None], ((x0 + 1) % nx)[None, :]]
        c = grid[((y0 + 1) % ny)[:, None], (x0 % nx)[None, :]]
        d = grid[((y0 + 1) % ny)[:, None], ((x0 + 1) % nx)[None, :]]
        top = a + (b - a) * fx[None, :]
        bot = c + (d - c) * fx[None, :]
        out += amp * (top + (bot - top) * fy[:, None])
        tot += amp
        amp *= 0.5
        cx, cy = max(1.0, cx / 2), max(1.0, cy / 2)
    return out / tot


# --------------------------------------------------------------------------- palette helpers
_PAL = None


def pal_array():
    global _PAL
    if _PAL is None:
        _PAL = np.array([pg.hx(h)[:3] for h in sorted(reg_hex())], np.int32)
    return _PAL


def snap(rgb: np.ndarray) -> np.ndarray:
    """Nearest registry palette colour for an (..., 3) array."""
    pal = pal_array()
    flat = rgb.reshape(-1, 3).astype(np.int32)
    d = ((flat[:, None, :] - pal[None, :, :]) ** 2).sum(-1)
    return pal[np.argmin(d, axis=1)].reshape(rgb.shape).astype(np.uint8)


def ramp_rgba(ramp: str, t: np.ndarray, alpha: np.ndarray, seed=0, x0=0, y0=0) -> np.ndarray:
    """Dithered palette colours of `ramp` at float tones t (h, w) with alpha (h, w) uint8."""
    cols = R.table[R[ramp], :R.n(ramp)]
    h, w = t.shape
    thr = pg.bayer(w, h, x0 + seed, y0 + seed, 4)
    fl = np.floor(t)
    idx = np.clip(fl + ((t - fl) > thr), 0, R.n(ramp) - 1).astype(np.int32)
    out = cols[idx].copy()
    out[..., 3] = alpha
    out[alpha == 0] = 0
    return out


def palette_report(arr: np.ndarray) -> tuple[int, list]:
    a = arr[..., 3] > 0
    cols = {'#%02X%02X%02X' % tuple(int(v) for v in c[:3]) for c in arr[a].reshape(-1, 4)}
    allowed = reg_hex()
    return len(cols), sorted(c for c in cols if c not in allowed)
