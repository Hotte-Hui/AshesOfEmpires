"""cine_a1m1_lib -- shared helpers for the A1 -> M1 transition cinematic (owner: trans-a1m1).

Original pixel art, generated deterministically (seeds from crc32 of names, never hash()).
Builds on pg.py (read-only shared core): palette ramps, Bayer dithering, Layer with height field ->
OpenGL normal map (+Y up) and emission masks.

Contents
--------
* ramps per scene (karsk / berlin / archive / sepia) as lists of RGBA uint8 arrays (dark -> light)
* tone fills with ordered dither, cylinder / dome shading, selective outlines
* a tiny 3x5 pixel font (Latin caps, digits, a few Cyrillic caps) and a 5x7 carved font
* regime insignia as clean hand-designed pixel templates (TECHNICAL_ARCHITECTURE section 12.4):
  red star, hammer & sickle, tilted swastika (historical variants) and the fictional neutral emblems
  (gear-and-wheat for Karsk, the "Reichssiegel" pillar disc for Berlin)
* frame-strip / layer savers that also write *_n.png normals and *_e.png emission masks
"""
from __future__ import annotations

import json
import math
import os
import sys
import zlib

import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pg  # noqa: E402
from pg import Layer, hx, bayer, value_noise, white_noise  # noqa: E402,F401

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
OUT = os.path.join(ROOT, 'assets', 'cinematics', 'a1m1')
CLEAR = np.zeros(4, np.uint8)


def seed_of(name: str) -> int:
    """Deterministic seed from a name (crc32, never Python's salted hash())."""
    return zlib.crc32(name.encode('utf-8')) & 0x7FFFFFFF


def ramps(scene: str) -> dict:
    return {k: [hx(c) for c in v] for k, v in pg.PALETTES[scene].items()}


KR = ramps('karsk')
BR = ramps('berlin')
AR = ramps('archive')
SR_ = ramps('sepia')


# --------------------------------------------------------------------------- tone helpers
def tone_put(L: Layer, mask: np.ndarray, x0: int, y0: int, ramp, tone, hgt=None, em=None, dither=True):
    """Fill `mask` (placed at x0,y0) with colours of `ramp` chosen by `tone` (float index into the ramp,
    scalar or array shaped like mask) using 4x4 Bayer ordered dither between neighbouring entries."""
    mh, mw = mask.shape
    T = np.broadcast_to(np.asarray(tone, np.float32), (mh, mw)).copy()
    n = len(ramp) - 1
    T = np.clip(T, 0, n)
    idx = np.floor(T).astype(int)
    if dither:
        thr = bayer(mw, mh, x0, y0)
        idx = idx + ((T - idx) > thr)
    idx = np.clip(idx, 0, n)
    carr = np.stack([np.asarray(c, np.uint8) for c in ramp])
    cols = carr[idx]
    L._put(mask, x0, y0, cols, hgt)
    if em is True:                      # emission = the painted colours themselves
        X0, Y0 = max(0, x0), max(0, y0)
        X1, Y1 = min(L.w, x0 + mw), min(L.h, y0 + mh)
        if X1 > X0 and Y1 > Y0:
            m = mask[Y0 - y0:Y1 - y0, X0 - x0:X1 - x0]
            L.em[Y0:Y1, X0:X1][m] = cols[Y0 - y0:Y1 - y0, X0 - x0:X1 - x0][m]
    elif em is not None and em is not False:
        L._put(mask, x0, y0, None, None, em)


def rect_tone(L: Layer, x, y, w, h, ramp, tone, hgt=None, em=None):
    x, y, w, h = int(x), int(y), int(w), int(h)
    if w <= 0 or h <= 0:
        return
    tone_put(L, np.ones((h, w), bool), x, y, ramp, tone, hgt=hgt, em=em)


def grad_v(h: int, w: int, t0: float, t1: float, power: float = 1.0) -> np.ndarray:
    t = (np.arange(h, dtype=np.float32) / max(1, h - 1)) ** power
    return np.repeat((t0 + (t1 - t0) * t)[:, None], w, axis=1)


def grad_h(h: int, w: int, t0: float, t1: float, power: float = 1.0) -> np.ndarray:
    t = (np.arange(w, dtype=np.float32) / max(1, w - 1)) ** power
    return np.repeat((t0 + (t1 - t0) * t)[None, :], h, axis=0)


def cyl_tone(h: int, w: int, lo: float, hi: float, light_y: float = 0.28) -> np.ndarray:
    """Horizontal cylinder (boiler) shading across rows: brightest at `light_y` (0 = top)."""
    y = (np.arange(h, dtype=np.float32) + 0.5) / h
    nrm = np.sqrt(np.clip(1 - (2 * y - 1) ** 2, 0, 1))      # facing camera
    lit = np.clip(1 - np.abs(y - light_y) * 1.6, 0, 1) ** 1.3
    t = lo + (hi - lo) * (0.55 * lit + 0.45 * nrm * (1 - y * 0.5))
    return np.repeat(t[:, None], w, axis=1)


def cyl_height(h: int, w: int) -> np.ndarray:
    y = (np.arange(h, dtype=np.float32) + 0.5) / h
    z = np.sqrt(np.clip(1 - (2 * y - 1) ** 2, 0, 1))
    return np.repeat(z[:, None], w, axis=1)


def outline_sel(L: Layer, col, where=None, sides=('l', 'r', 't', 'b')):
    """Selective 1 px outer outline on given sides only."""
    a = L.alpha()
    p = np.pad(a, 1)
    m = np.zeros_like(a)
    if 'l' in sides:
        m |= p[1:-1, 2:] & ~a      # pixel left of an opaque one
    if 'r' in sides:
        m |= p[1:-1, :-2] & ~a
    if 't' in sides:
        m |= p[2:, 1:-1] & ~a
    if 'b' in sides:
        m |= p[:-2, 1:-1] & ~a
    if where is not None:
        m &= where
    L.c[m] = col
    return m


def erode(m: np.ndarray, r: int = 1) -> np.ndarray:
    out = m.copy()
    for _ in range(r):
        p = np.pad(out, 1)
        out = out & p[:-2, 1:-1] & p[2:, 1:-1] & p[1:-1, :-2] & p[1:-1, 2:]
    return out


def dilate(m: np.ndarray, r: int = 1) -> np.ndarray:
    out = m.copy()
    for _ in range(r):
        p = np.pad(out, 1)
        out = out | p[:-2, 1:-1] | p[2:, 1:-1] | p[1:-1, :-2] | p[1:-1, 2:]
    return out


def edge_of(m: np.ndarray) -> np.ndarray:
    return m & ~erode(m, 1)


def disc_mask(d: int) -> np.ndarray:
    r = d / 2.0
    yy, xx = np.mgrid[0:d, 0:d]
    return ((xx + 0.5 - r) ** 2 + (yy + 0.5 - r) ** 2) <= r * r + 0.2


def poly_raster(w: int, h: int, polys, ss: int = 6) -> np.ndarray:
    """Supersampled polygon fill -> bool mask (coverage >= 0.5)."""
    img = Image.new('L', (w * ss, h * ss), 0)
    from PIL import ImageDraw
    d = ImageDraw.Draw(img)
    for poly in polys:
        d.polygon([(x * ss, y * ss) for x, y in poly], fill=255)
    a = np.asarray(img, np.float32).reshape(h, ss, w, ss).mean(axis=(1, 3)) / 255.0
    return a >= 0.5


def stroke_raster(w: int, h: int, polylines, width: float, ss: int = 6, thresh: float = 0.5) -> np.ndarray:
    img = Image.new('L', (w * ss, h * ss), 0)
    from PIL import ImageDraw
    d = ImageDraw.Draw(img)
    for pl in polylines:
        pts = [(x * ss, y * ss) for x, y in pl]
        d.line(pts, fill=255, width=max(1, int(round(width * ss))), joint='curve')
        r = width * ss / 2
        for (x, y) in pts:
            d.ellipse([x - r, y - r, x + r, y + r], fill=255)
    a = np.asarray(img, np.float32).reshape(h, ss, w, ss).mean(axis=(1, 3)) / 255.0
    return a >= thresh


def clean_mask(m: np.ndarray) -> np.ndarray:
    """Remove orphan pixels (no 4-neighbour) and fill single-pixel holes."""
    p = np.pad(m, 1)
    nb = p[:-2, 1:-1].astype(int) + p[2:, 1:-1] + p[1:-1, :-2] + p[1:-1, 2:]
    out = m & (nb >= 1)
    out |= (~m) & (nb >= 4)
    return out


# --------------------------------------------------------------------------- tiny fonts
# 3x5 font, rows top->bottom, '1' = ink. Latin caps, digits, punctuation, Cyrillic (Л, П, Д, Ж, Я, Ф, Ч, Ш, Ц, Б, Г, И, У)
F35 = {
    'A': ['010', '101', '111', '101', '101'], 'B': ['110', '101', '110', '101', '110'],
    'C': ['011', '100', '100', '100', '011'], 'D': ['110', '101', '101', '101', '110'],
    'E': ['111', '100', '110', '100', '111'], 'F': ['111', '100', '110', '100', '100'],
    'G': ['011', '100', '101', '101', '011'], 'H': ['101', '101', '111', '101', '101'],
    'I': ['111', '010', '010', '010', '111'], 'J': ['001', '001', '001', '101', '010'],
    'K': ['101', '101', '110', '101', '101'], 'L': ['100', '100', '100', '100', '111'],
    'M': ['101', '111', '111', '101', '101'], 'N': ['101', '111', '111', '111', '101'],
    'O': ['010', '101', '101', '101', '010'], 'P': ['110', '101', '110', '100', '100'],
    'Q': ['010', '101', '101', '111', '011'], 'R': ['110', '101', '110', '101', '101'],
    'S': ['011', '100', '010', '001', '110'], 'T': ['111', '010', '010', '010', '010'],
    'U': ['101', '101', '101', '101', '111'], 'V': ['101', '101', '101', '101', '010'],
    'W': ['101', '101', '111', '111', '101'], 'X': ['101', '101', '010', '101', '101'],
    'Y': ['101', '101', '010', '010', '010'], 'Z': ['111', '001', '010', '100', '111'],
    '0': ['111', '101', '101', '101', '111'], '1': ['010', '110', '010', '010', '111'],
    '2': ['110', '001', '010', '100', '111'], '3': ['110', '001', '010', '001', '110'],
    '4': ['101', '101', '111', '001', '001'], '5': ['111', '100', '110', '001', '110'],
    '6': ['011', '100', '111', '101', '111'], '7': ['111', '001', '010', '010', '010'],
    '8': ['111', '101', '111', '101', '111'], '9': ['111', '101', '111', '001', '110'],
    '-': ['000', '000', '111', '000', '000'], '.': ['000', '000', '000', '000', '010'],
    ' ': ['000', '000', '000', '000', '000'], '/': ['001', '001', '010', '100', '100'],
    ':': ['000', '010', '000', '010', '000'], '·': ['000', '000', '010', '000', '000'],
    'Л': ['011', '101', '101', '101', '101'], 'П': ['111', '101', '101', '101', '101'],
    'Д': ['011', '101', '101', '111', '101'], 'Я': ['011', '101', '011', '101', '101'],
    'Ж': ['101', '111', '010', '111', '101'], 'Ч': ['101', '101', '011', '001', '001'],
    'Ш': ['101', '101', '101', '101', '111'], 'Б': ['111', '100', '110', '101', '110'],
    'Г': ['111', '100', '100', '100', '100'], 'И': ['101', '101', '111', '111', '101'],
    'У': ['101', '101', '011', '001', '110'], 'Ф': ['010', '111', '111', '010', '010'],
    'Ц': ['101', '101', '101', '111', '001'], 'Ы': ['101', '101', '111', '111', '111'],
}


def text_w(s: str, spacing: int = 1) -> int:
    return max(0, len(s) * (3 + spacing) - spacing)


def text_mask(s: str, spacing: int = 1) -> np.ndarray:
    w = text_w(s, spacing)
    m = np.zeros((5, max(1, w)), bool)
    x = 0
    for ch in s:
        g = F35.get(ch.upper(), F35[' '])
        for yy, row in enumerate(g):
            for xx, v in enumerate(row):
                if v == '1':
                    m[yy, x + xx] = True
        x += 3 + spacing
    return m


def text(L: Layer, x: int, y: int, s: str, col, spacing: int = 1, hgt=None, em=None):
    m = text_mask(s, spacing)
    L._put(m, int(x), int(y), col, hgt, em)
    return m


# Carved 4x7 capitals for monumental lettering (BAUARCHIV etc.)
F47 = {
    'A': ['0110', '1001', '1001', '1111', '1001', '1001', '1001'],
    'B': ['1110', '1001', '1001', '1110', '1001', '1001', '1110'],
    'C': ['0111', '1000', '1000', '1000', '1000', '1000', '0111'],
    'H': ['1001', '1001', '1001', '1111', '1001', '1001', '1001'],
    'I': ['111', '010', '010', '010', '010', '010', '111'],
    'R': ['1110', '1001', '1001', '1110', '1010', '1001', '1001'],
    'U': ['1001', '1001', '1001', '1001', '1001', '1001', '0110'],
    'V': ['10001', '10001', '10001', '01010', '01010', '00100', '00100'],
    'E': ['1111', '1000', '1000', '1110', '1000', '1000', '1111'],
    'S': ['0111', '1000', '1000', '0110', '0001', '0001', '1110'],
    'T': ['11111', '00100', '00100', '00100', '00100', '00100', '00100'],
    'N': ['1001', '1101', '1101', '1011', '1011', '1001', '1001'],
    'L': ['1000', '1000', '1000', '1000', '1000', '1000', '1111'],
    'G': ['0111', '1000', '1000', '1011', '1001', '1001', '0111'],
    'O': ['0110', '1001', '1001', '1001', '1001', '1001', '0110'],
    'D': ['1110', '1001', '1001', '1001', '1001', '1001', '1110'],
    ' ': ['00', '00', '00', '00', '00', '00', '00'],
    '·': ['0', '0', '0', '1', '0', '0', '0'],
}


def carved_mask(s: str, spacing: int = 2) -> np.ndarray:
    widths = [len(F47.get(ch, F47[' '])[0]) for ch in s]
    w = sum(widths) + spacing * (len(s) - 1)
    m = np.zeros((7, max(1, w)), bool)
    x = 0
    for ch, gw in zip(s, widths):
        g = F47.get(ch, F47[' '])
        for yy, row in enumerate(g):
            for xx, v in enumerate(row):
                if v == '1':
                    m[yy, x + xx] = True
        x += gw + spacing
    return m


# --------------------------------------------------------------------------- insignia templates
def _grid(rows) -> np.ndarray:
    return np.array([[c == 'X' for c in r] for r in rows], bool)


STAR_7 = _grid([
    '...X...',
    '...X...',
    'XXXXXXX',
    '.XXXXX.',
    '..XXX..',
    '.XX.XX.',
    '.X...X.',
])
STAR_9 = _grid([
    '....X....',
    '...XXX...',
    '...XXX...',
    'XXXXXXXXX',
    '.XXXXXXX.',
    '..XXXXX..',
    '..XXXXX..',
    '.XXX.XXX.',
    '.XX...XX.',
])
STAR_13 = _grid([
    '......X......',
    '.....XXX.....',
    '.....XXX.....',
    '....XXXXX....',
    'XXXXXXXXXXXXX',
    '.XXXXXXXXXXX.',
    '..XXXXXXXXX..',
    '...XXXXXXX...',
    '...XXXXXXX...',
    '..XXXXXXXXX..',
    '..XXXX.XXXX..',
    '.XXX.....XXX.',
    '.XX.......XX.',
])

# Hammer and sickle, 11x11 (sickle blade arcs from lower left over the top to the right; hammer crosses
# from lower right to upper left with its head top-left). Hand-placed pixels, no orphans.
HAMMER_SICKLE_11 = _grid([
    '.....XXX...',
    'XX.....XX..',
    'XXX.....XX.',
    '.XXX.....X.',
    '...XX....X.',
    '....XX..XX.',
    '.....XXXX..',
    '..X...XX...',
    '.XXX...XX..',
    'XX......XX.',
    'X........X.',
])

# Swastika tilted 45 degrees (as on the historical NSDAP flag), 11x11, 2 px arms drawn as diagonal
# staircases. Hand-placed so every arm is a clean 2-px band.
SWASTIKA_11 = _grid([
    '....X......',
    '...XXX.....',
    '....XXX..X.',
    '.....XXXXX.',
    '.X..XXXXX..',
    'XXXXX.XXXXX',
    '..XXXXX..X.',
    '.XXXXX.....',
    '.X..XXX....',
    '.....XXX...',
    '......X....',
])

SWASTIKA_9 = _grid([
    '...X.....',
    '..XXX..X.',
    '...XXXXX.',
    '.X.XXX...',
    'XXXX.XXXX',
    '...XXX.X.',
    '.XXXXX...',
    '.X..XXX..',
    '.....X...',
])

HS_13 = _grid([               # hammer & sickle, 13 px (pixel primitives, verified at 8x)
    '.............',
    '....XXXXXX...',
    '...XXX...XX..',
    '..XXX.....X..',
    '..XXX.....XX.',
    '.XX.XX....XX.',
    '.X...XX...XX.',
    '......XX..X..',
    '.......XXXX..',
    '.....XXXXX...',
    '....XX...XX..',
    '...XX.....XX.',
    '..XX.........',
])
HS_15 = _grid([
    '...............',
    '.....XXXXXX....',
    '...XX.XX.XXX...',
    '...X.XX....XX..',
    '....XX.....XX..',
    '...XXX......XX.',
    '..XX.XX.....XX.',
    '..X...XX....X..',
    '.......XX..XX..',
    '........XXXXX..',
    '......XXXXXX...',
    '.....XXXXXXX...',
    '....XX.....XX..',
    '...XX.......XX.',
    '...............',
])


def swastika(n: int = 3, m: int = 3, thick: int = 2) -> np.ndarray:
    """Historical swastika rotated 45 degrees (as on the NSDAP flag), arms bent clockwise, drawn as clean
    2-px diagonal staircases: arm length n, hook length m. n=3,m=3 -> 13x14 px; n=3,m=2 -> 11x12 px."""
    pts = set()
    for d in ((1, -1), (1, 1), (-1, 1), (-1, -1)):
        dp = (-d[1], d[0])                       # clockwise turn (screen coordinates, y down)
        for k in range(n + 1):
            pts.add((k * d[0], k * d[1]))
        ex, ey = n * d[0], n * d[1]
        for k in range(m + 1):
            pts.add((ex + k * dp[0], ey + k * dp[1]))
    P = set(pts)
    if thick >= 2:
        P |= {(x + 1, y) for (x, y) in pts}
    if thick >= 3:
        P |= {(x, y + 1) for (x, y) in pts}
    xs = [p[0] for p in P]
    ys = [p[1] for p in P]
    g = np.zeros((max(ys) - min(ys) + 1, max(xs) - min(xs) + 1), bool)
    for (x, y) in P:
        g[y - min(ys), x - min(xs)] = True
    return g


# Fictional neutral emblems (section 12.4)
GEAR_WHEAT_13 = _grid([        # cog ring with a wheat ear (Karsk neutral emblem)
    '....X...X....',
    '...XXXXXXX...',
    '..XXX...XXX..',
    'XXX..X.X..XXX',
    '.X..X.X.X..X.',
    '.X...XXX...X.',
    'XX..X.X.X..XX',
    '.X...XXX...X.',
    '.X..X.X.X..X.',
    'XXX...X...XXX',
    '..XXX.X.XXX..',
    '...XXXXXXX...',
    '....X...X....',
])

REICHSSIEGEL_11 = _grid([      # white pillar / obelisk (the fictional state seal), drawn inside a disc
    '.....X.....',
    '....XXX....',
    '....XXX....',
    '....XXX....',
    '....XXX....',
    '....XXX....',
    '....XXX....',
    '....XXX....',
    '...XXXXX...',
    '..XXXXXXX..',
    '...........',
])


def put_grid(L: Layer, grid: np.ndarray, x: int, y: int, col, hgt=None, em=None):
    L._put(grid, int(x), int(y), col, hgt, em)


def emblem_disc(d: int, inner: np.ndarray, ring_col, field_col, inner_col, ring: bool = True) -> Layer:
    """A round emblem: disc of `field_col` with an optional 1 px ring and `inner` centred on it."""
    E = Layer(d, d, 'emblem')
    m = disc_mask(d)
    E._put(m, 0, 0, field_col, hgt=0.6)
    if ring:
        E._put(edge_of(m), 0, 0, ring_col, hgt=0.7)
    ih, iw = inner.shape
    E._put(inner, (d - iw) // 2, (d - ih) // 2, inner_col, hgt=0.8)
    return E


# --------------------------------------------------------------------------- output helpers
def ensure_dir(p: str):
    os.makedirs(p, exist_ok=True)


def save(L: Layer, rel: str, normal: bool = True, emission=None, strength: float = 3.0) -> dict:
    base = os.path.join(OUT, rel)
    ensure_dir(os.path.dirname(base))
    info = L.save(base, normal=normal, emission=emission, strength=strength)
    info['path'] = rel + '.png'
    return info


def strip(frames, rel: str, normal: bool = True, emission=None, strength: float = 3.0) -> dict:
    """Saves frames (same size) side by side as one horizontal strip (Sprite2D hframes)."""
    fw, fh = frames[0].w, frames[0].h
    S = Layer(fw * len(frames), fh, rel)
    for i, F in enumerate(frames):
        S.c[:, i * fw:(i + 1) * fw] = F.c
        S.hgt[:, i * fw:(i + 1) * fw] = F.hgt
        S.nrm[:, i * fw:(i + 1) * fw] = F.nrm
        S.em[:, i * fw:(i + 1) * fw] = F.em
    info = save(S, rel, normal=normal, emission=emission, strength=strength)
    info.update({'frames': len(frames), 'frame_w': fw, 'frame_h': fh})
    return info


def preview(img: Image.Image, name: str, k: int = 3, folder: str = '_preview'):
    p = os.path.join(OUT, folder)
    ensure_dir(p)
    img.resize((img.width * k, img.height * k), Image.NEAREST).save(os.path.join(p, name))


def write_json(rel: str, data: dict):
    p = os.path.join(OUT, rel)
    ensure_dir(os.path.dirname(p))
    with open(p, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=1, ensure_ascii=False)


def flip_layer(L: Layer) -> Layer:
    """Mirror horizontally (normals: x component negated)."""
    F = Layer(L.w, L.h, L.name + '_flip')
    F.c = L.c[:, ::-1].copy()
    F.hgt = L.hgt[:, ::-1].copy()
    F.nrm = L.nrm[:, ::-1].copy()
    F.nrm[..., 0] = -F.nrm[..., 0]
    F.em = L.em[:, ::-1].copy()
    return F


def crop_alpha(L: Layer, pad: int = 0):
    """Tight crop to opaque pixels -> (Layer, x_off, y_off)."""
    a = L.alpha() | (L.em[..., 3] > 0)
    ys, xs = np.nonzero(a)
    if len(xs) == 0:
        return L, 0, 0
    x0 = max(0, xs.min() - pad); x1 = min(L.w, xs.max() + 1 + pad)
    y0 = max(0, ys.min() - pad); y1 = min(L.h, ys.max() + 1 + pad)
    C = Layer(x1 - x0, y1 - y0, L.name)
    C.c = L.c[y0:y1, x0:x1].copy()
    C.hgt = L.hgt[y0:y1, x0:x1].copy()
    C.nrm = L.nrm[y0:y1, x0:x1].copy()
    C.em = L.em[y0:y1, x0:x1].copy()
    return C, x0, y0


def composite(items, w: int, h: int, bg=(0, 0, 0, 255)) -> np.ndarray:
    """Quick preview compositing: [(rgba array, x, y, alpha_mult)] back to front (alpha-over)."""
    out = np.zeros((h, w, 3), np.float32)
    out[:] = np.asarray(bg[:3], np.float32)
    for arr, x, y, am in items:
        ah, aw = arr.shape[:2]
        X0, Y0 = max(0, x), max(0, y)
        X1, Y1 = min(w, x + aw), min(h, y + ah)
        if X1 <= X0 or Y1 <= Y0:
            continue
        sub = arr[Y0 - y:Y1 - y, X0 - x:X1 - x].astype(np.float32)
        a = (sub[..., 3:4] / 255.0) * am
        out[Y0:Y1, X0:X1] = out[Y0:Y1, X0:X1] * (1 - a) + sub[..., :3] * a
    return np.clip(out, 0, 255).astype(np.uint8)
