"""env_veltrava_lib -- shared palette + pixel kit for the Free City of Veltrava (Chapter 3).

Area: env_veltrava (station art stream).  Builds on tools/pixelgen/pg.py (imported, never modified).
Importing this module registers the scene palette 'veltrava' in pg.PALETTES (ramps identical to
data/chapters/c3.json "palettes.veltrava"; dark -> light inside every ramp, 46 colours).

Contents: palette ramps, trilingual pixel fonts (Latin incl. German/French accents, Cyrillic, digits),
ordered-dither ramp painters, explicit normal helpers, snow edges, parametric people, export helpers.
Everything is original procedural pixel art with fixed seeds; no reference image is ever sampled.
"""
from __future__ import annotations

import math
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

import numpy as np  # noqa: E402
from PIL import Image  # noqa: E402

import pg  # noqa: E402
from pg import Layer, hx, bayer, value_noise  # noqa: E402,F401

ROOT = os.path.normpath(os.path.join(_HERE, '..', '..'))
ENV_DIR = os.path.join(ROOT, 'assets', 'environments', 'veltrava_station')
DOC_DIR = os.path.join(ROOT, 'assets', 'ui', 'documents')

# --------------------------------------------------------------------------- palette (binding: c3.json)
VELTRAVA = {
    # cold dawn of a neutral city: slate-blue shadows, cream sandstone, copper-green patina roofs,
    # cast iron, one warm lamp ramp (the café / lit windows) and the shared story red.
    'night':  ['#070A12', '#0C111C', '#121A26', '#1A2431'],
    'slate':  ['#1E2836', '#2A3646', '#3A4859', '#4F5E70', '#687789', '#8593A3'],
    'iron':   ['#15171C', '#22262D', '#323840', '#464D55', '#5E666E'],
    'cream':  ['#4A4236', '#645A49', '#80745E', '#9E9076', '#BBAD8F', '#D6CBAE'],
    'patina': ['#1E302E', '#2B4541', '#3D5E57', '#56796E', '#739585'],
    'lamp':   ['#6E3F22', '#A8643A', '#D08F55', '#EDB777', '#FCE2B0'],
    'sky':    ['#5C6B82', '#7684A0', '#95A0B8', '#B6B9C9', '#D3CDD3', '#E8DCD6'],
    'snow':   ['#7D8796', '#A1AAB7', '#C2C9D2', '#DEE2E7', '#F2F3F5'],
    'red':    ['#4A1712', '#7A2218', '#A8382E', '#C8503C'],
}
pg.PALETTES['veltrava'] = VELTRAVA          # registered at import time (pg.pal('veltrava', ramp) works)


def _r(n):
    return [hx(c) for c in VELTRAVA[n]]


NI, SL, IR, CR, PA, LA, SK, SN, RD = (_r(n) for n in
                                      ('night', 'slate', 'iron', 'cream', 'patina', 'lamp', 'sky', 'snow', 'red'))
ALL = pg.all_colors('veltrava')
CLEAR = np.zeros(4, np.uint8)
UP = (0.0, 0.55, 0.83)        # oblique ground normal (faces up / toward the camera, OpenGL +Y up)

WORLD_W, WORLD_H, VIEW_W = 1920, 360, 640


def layer_w(p: float, margin: int = 8) -> int:
    """TECHNICAL_ARCHITECTURE 3.1: required width = 640 + parallax * (world_w - 640) (+ margin)."""
    return int(math.ceil(VIEW_W + p * (WORLD_W - VIEW_W))) + margin


def hexc(c) -> str:
    return '#%02X%02X%02X' % (int(c[0]), int(c[1]), int(c[2]))


def col_key(c):
    c = np.asarray(c, np.int64)
    return (c[..., 0] << 16) | (c[..., 1] << 8) | c[..., 2]


# --------------------------------------------------------------------------- pixel fonts
# FONT_S: 5-row capitals (variable width) for plates, stencils, timetable rows, small signs.
FONT_S = {
    'A': ["###", "#.#", "###", "#.#", "#.#"], 'B': ["##.", "#.#", "##.", "#.#", "##."],
    'C': ["###", "#..", "#..", "#..", "###"], 'D': ["##.", "#.#", "#.#", "#.#", "##."],
    'E': ["###", "#..", "##.", "#..", "###"], 'F': ["###", "#..", "##.", "#..", "#.."],
    'G': ["###", "#..", "#.#", "#.#", "###"], 'H': ["#.#", "#.#", "###", "#.#", "#.#"],
    'I': ["###", ".#.", ".#.", ".#.", "###"], 'J': ["..#", "..#", "..#", "#.#", "###"],
    'K': ["#.#", "#.#", "##.", "#.#", "#.#"], 'L': ["#..", "#..", "#..", "#..", "###"],
    'M': ["#...#", "##.##", "#.#.#", "#...#", "#...#"], 'N': ["#..#", "##.#", "#.##", "#..#", "#..#"],
    'O': ["###", "#.#", "#.#", "#.#", "###"], 'P': ["###", "#.#", "###", "#..", "#.."],
    'Q': ["###", "#.#", "#.#", "###", "..#"], 'R': ["###", "#.#", "##.", "#.#", "#.#"],
    'S': ["###", "#..", "###", "..#", "###"], 'T': ["###", ".#.", ".#.", ".#.", ".#."],
    'U': ["#.#", "#.#", "#.#", "#.#", "###"], 'V': ["#.#", "#.#", "#.#", "#.#", ".#."],
    'W': ["#...#", "#...#", "#.#.#", "##.##", "#...#"], 'X': ["#.#", "#.#", ".#.", "#.#", "#.#"],
    'Y': ["#.#", "#.#", ".#.", ".#.", ".#."], 'Z': ["###", "..#", ".#.", "#..", "###"],
    # Cyrillic (shapes identical to Latin reuse the Latin rows)
    'Б': ["###", "#..", "###", "#.#", "###"], 'Г': ["###", "#..", "#..", "#..", "#.."],
    'Д': [".##.", ".#.#", ".#.#", "####", "#..#"], 'Ж': ["#.#.#", ".###.", "..#..", ".###.", "#.#.#"],
    'З': ["##.", "..#", ".#.", "..#", "##."], 'И': ["#..#", "#..#", "#.##", "##.#", "#..#"],
    'Л': [".##", "#.#", "#.#", "#.#", "#.#"], 'П': ["###", "#.#", "#.#", "#.#", "#.#"],
    'У': ["#.#", "#.#", "###", "..#", "##."], 'Ф': [".#.", "###", "#.#", "###", ".#."],
    'Ц': ["#.#.", "#.#.", "#.#.", "####", "...#"], 'Ч': ["#.#", "#.#", "###", "..#", "..#"],
    'Ш': ["#.#.#", "#.#.#", "#.#.#", "#.#.#", "#####"], 'Щ': ["#.#.#.", "#.#.#.", "#.#.#.", "######", ".....#"],
    'Ъ': ["##..", ".#..", ".##.", ".#.#", ".##."], 'Ы': ["#...#", "#...#", "##..#", "#.#.#", "##..#"],
    'Ь': ["#..", "#..", "##.", "#.#", "##."], 'Э': ["##.", "..#", ".##", "..#", "##."],
    'Ю': ["#.###", "#.#.#", "###.#", "#.#.#", "#.###"], 'Я': ["###", "#.#", "###", ".##", "#.#"],
    # digits (0 rounded so it never reads as O)
    '0': [".#.", "#.#", "#.#", "#.#", ".#."], '1': [".#", "##", ".#", ".#", ".#"],
    '2': ["##.", "..#", ".#.", "#..", "###"], '3': ["##.", "..#", ".#.", "..#", "##."],
    '4': ["#.#", "#.#", "###", "..#", "..#"], '5': ["###", "#..", "##.", "..#", "##."],
    '6': [".##", "#..", "###", "#.#", "###"], '7': ["###", "..#", ".#.", ".#.", ".#."],
    '8': ["###", "#.#", "###", "#.#", "###"], '9': ["###", "#.#", "###", "..#", "##."],
    '-': ["...", "...", "###", "...", "..."], '–': ["...", "...", "###", "...", "..."],
    '.': [".", ".", ".", ".", "#"], ',': ["..", "..", "..", ".#", "#."], ':': [".", "#", ".", "#", "."],
    '/': ["..#", "..#", ".#.", "#..", "#.."], '·': [".", ".", "#", ".", "."], "'": ["#", "#", ".", ".", "."],
    '(': [".#", "#.", "#.", "#.", ".#"], ')': ["#.", ".#", ".#", ".#", "#."], '+': ["...", ".#.", "###", ".#.", "..."],
    '=': ["...", "###", "...", "###", "..."], '%': ["#.#", "..#", ".#.", "#..", "#.#"], '!': ["#", "#", "#", ".", "#"],
    '„': ["..", "..", "..", "..", "##"], '“': ["##", "..", "..", "..", ".."], '"': ["#.#", "#.#", "...", "...", "..."],
    '№': ["#..#.", "##.#.", "#.##.", "#..#.", "#..##"], '?': ["##.", "..#", ".#.", "...", ".#."],
    'k': ["#..", "#.#", "##.", "#.#", "#.#"], 'g': ["###", "#.#", "###", "..#", "##."],
}
for _lat, _cyr in (('A', 'А'), ('B', 'В'), ('C', 'С'), ('E', 'Е'), ('H', 'Н'), ('K', 'К'), ('M', 'М'),
                   ('O', 'О'), ('P', 'Р'), ('T', 'Т'), ('X', 'Х')):
    FONT_S[_cyr] = FONT_S[_lat]

# accented capitals: base glyph + accent row drawn above (cedilla below)
ACCENTS = {'Ä': ('A', 'uml'), 'Ö': ('O', 'uml'), 'Ü': ('U', 'uml'), 'É': ('E', 'acute'), 'È': ('E', 'grave'),
           'Ê': ('E', 'circ'), 'À': ('A', 'grave'), 'Ô': ('O', 'circ'), 'Ç': ('C', 'ced'), 'Й': ('И', 'breve'),
           'Ё': ('Е', 'uml')}

# FONT_L: 7-row capitals for station signs, the clock plates, document headlines and key numbers.
FONT_L = {
    'A': [".###.", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"],
    'B': ["####.", "#...#", "#...#", "####.", "#...#", "#...#", "####."],
    'C': [".###.", "#...#", "#....", "#....", "#....", "#...#", ".###."],
    'D': ["####.", "#...#", "#...#", "#...#", "#...#", "#...#", "####."],
    'E': ["#####", "#....", "#....", "####.", "#....", "#....", "#####"],
    'F': ["#####", "#....", "#....", "####.", "#....", "#....", "#...."],
    'G': [".###.", "#...#", "#....", "#.###", "#...#", "#...#", ".###."],
    'H': ["#...#", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"],
    'I': ["###", ".#.", ".#.", ".#.", ".#.", ".#.", "###"],
    'J': ["..###", "...#.", "...#.", "...#.", "#..#.", "#..#.", ".##.."],
    'K': ["#...#", "#..#.", "#.#..", "##...", "#.#..", "#..#.", "#...#"],
    'L': ["#....", "#....", "#....", "#....", "#....", "#....", "#####"],
    'M': ["#...#", "##.##", "#.#.#", "#.#.#", "#...#", "#...#", "#...#"],
    'N': ["#...#", "##..#", "#.#.#", "#..##", "#...#", "#...#", "#...#"],
    'O': [".###.", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."],
    'P': ["####.", "#...#", "#...#", "####.", "#....", "#....", "#...."],
    'Q': [".###.", "#...#", "#...#", "#...#", "#.#.#", "#..#.", ".##.#"],
    'R': ["####.", "#...#", "#...#", "####.", "#.#..", "#..#.", "#...#"],
    'S': [".####", "#....", "#....", ".###.", "....#", "....#", "####."],
    'T': ["#####", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."],
    'U': ["#...#", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."],
    'V': ["#...#", "#...#", "#...#", "#...#", "#...#", ".#.#.", "..#.."],
    'W': ["#...#", "#...#", "#...#", "#.#.#", "#.#.#", "##.##", "#...#"],
    'X': ["#...#", "#...#", ".#.#.", "..#..", ".#.#.", "#...#", "#...#"],
    'Y': ["#...#", "#...#", ".#.#.", "..#..", "..#..", "..#..", "..#.."],
    'Z': ["#####", "....#", "...#.", "..#..", ".#...", "#....", "#####"],
    'Б': ["#####", "#....", "#....", "####.", "#...#", "#...#", "####."],
    'Г': ["#####", "#....", "#....", "#....", "#....", "#....", "#...."],
    'Д': ["..##.", ".#.#.", ".#.#.", ".#.#.", ".#.#.", "#####", "#...#"],
    'Ж': ["#.#.#", "#.#.#", ".###.", "..#..", ".###.", "#.#.#", "#.#.#"],
    'З': [".###.", "#...#", "....#", "..##.", "....#", "#...#", ".###."],
    'И': ["#...#", "#...#", "#..##", "#.#.#", "##..#", "#...#", "#...#"],
    'Л': ["..###", ".#..#", ".#..#", ".#..#", ".#..#", ".#..#", "#...#"],
    'П': ["#####", "#...#", "#...#", "#...#", "#...#", "#...#", "#...#"],
    'У': ["#...#", "#...#", "#...#", ".####", "....#", "#...#", ".###."],
    'Ф': ["..#..", ".###.", "#.#.#", "#.#.#", ".###.", "..#..", "..#.."],
    'Ц': ["#..#.", "#..#.", "#..#.", "#..#.", "#..#.", "#####", "....#"],
    'Ч': ["#...#", "#...#", "#...#", ".####", "....#", "....#", "....#"],
    'Ш': ["#.#.#", "#.#.#", "#.#.#", "#.#.#", "#.#.#", "#.#.#", "#####"],
    'Щ': ["#.#.#.", "#.#.#.", "#.#.#.", "#.#.#.", "#.#.#.", "######", ".....#"],
    'Ы': ["#...#", "#...#", "#...#", "###.#", "#.#.#", "#.#.#", "###.#"],
    'Ь': ["#....", "#....", "#....", "####.", "#...#", "#...#", "####."],
    'Э': [".###.", "#...#", "....#", ".####", "....#", "#...#", ".###."],
    'Ю': ["#..#.", "#.#.#", "#.#.#", "###.#", "#.#.#", "#.#.#", "#..#."],
    'Я': [".####", "#...#", "#...#", ".####", "..#.#", ".#..#", "#...#"],
    '0': [".###.", "#...#", "#..##", "#.#.#", "##..#", "#...#", ".###."],
    '1': ["..#", ".##", "..#", "..#", "..#", "..#", ".###"],
    '2': [".###.", "#...#", "....#", "...#.", "..#..", ".#...", "#####"],
    '3': ["####.", "....#", "....#", ".###.", "....#", "....#", "####."],
    '4': ["...#.", "..##.", ".#.#.", "#..#.", "#####", "...#.", "...#."],
    '5': ["#####", "#....", "####.", "....#", "....#", "#...#", ".###."],
    '6': [".###.", "#....", "#....", "####.", "#...#", "#...#", ".###."],
    '7': ["#####", "....#", "...#.", "..#..", ".#...", ".#...", ".#..."],
    '8': [".###.", "#...#", "#...#", ".###.", "#...#", "#...#", ".###."],
    '9': [".###.", "#...#", "#...#", ".####", "....#", "....#", ".###."],
    '-': ["....", "....", "....", "####", "....", "....", "...."],
    '–': ["....", "....", "....", "####", "....", "....", "...."],
    '/': ["....#", "...#.", "...#.", "..#..", ".#...", ".#...", "#...."],
    ':': [".", ".", "#", ".", "#", ".", "."], '.': [".", ".", ".", ".", ".", ".", "#"],
    '·': [".", ".", ".", "#", ".", ".", "."], ',': ["..", "..", "..", "..", "..", ".#", "#."],
    'k': ["#....", "#....", "#..#.", "#.#..", "##...", "#.#..", "#..#."],
    'g': [".....", ".....", ".####", "#...#", ".####", "....#", ".###."],
    '"': ["#.#", "#.#", "...", "...", "...", "...", "..."], '№': ["#..#..", "##.#..", "#.##.#", "#..#.#", "#..#..",
                                                                 "#..#..", "#..#.."],
}
for _lat, _cyr in (('A', 'А'), ('B', 'В'), ('C', 'С'), ('E', 'Е'), ('H', 'Н'), ('K', 'К'), ('M', 'М'),
                   ('O', 'О'), ('P', 'Р'), ('T', 'Т'), ('X', 'Х')):
    FONT_L[_cyr] = FONT_L[_lat]

_ACC_ROWS = {'uml': lambda w: '#' + '.' * max(0, w - 2) + '#' if w >= 3 else '##',
             'acute': lambda w: '.' * (w - 1) + '#', 'grave': lambda w: '#' + '.' * (w - 1),
             'circ': lambda w: '.' * (w // 2) + '#' + '.' * (w - w // 2 - 1),
             'breve': lambda w: '#' + '.' * max(0, w - 2) + '#' if w >= 3 else '##',
             'ced': lambda w: '.' * (w // 2) + '#' + '.' * (w - w // 2 - 1)}


def _glyph(ch, font):
    f = FONT_S if font == 's' else FONT_L
    if ch in f:
        return f[ch], None
    if ch in ACCENTS:
        base, acc = ACCENTS[ch]
        g = f.get(base)
        if g is None:
            return None, None
        return g, (acc, _ACC_ROWS[acc](len(g[0])))
    up = ch.upper()
    if up != ch and up in f:
        return f[up], None
    return None, None


def text_width(s: str, font: str = 's', spacing: int = 1) -> int:
    w = 0
    for ch in s:
        if ch == ' ':
            w += 2 if font == 's' else 3
            continue
        g, _ = _glyph(ch, font)
        w += (len(g[0]) if g else 3) + spacing
    return max(0, w - spacing)


def text(L: Layer, x: int, y: int, s: str, col, font: str = 's', spacing: int = 1, hgt=None, em=None,
         shadow=None, scale: int = 1, rng=None, wear: float = 0.0):
    """Draw pixel text; returns width.  shadow: colour drawn 1 px down-left (painted letters).
    scale: integer block scale (stamped numbers on documents).  wear: random missing pixels."""
    cx = x
    for ch in s:
        if ch == ' ':
            cx += (2 if font == 's' else 3) * scale
            continue
        g, acc = _glyph(ch, font)
        if g is None:
            cx += 4 * scale
            continue
        pts = [(c, r) for r, row in enumerate(g) for c, v in enumerate(row) if v == '#']
        if acc is not None:
            kind, row = acc
            ay = len(g) if kind == 'ced' else -2
            pts += [(c, ay) for c, v in enumerate(row) if v == '#']
        for (c, r) in pts:
            if rng is not None and wear > 0 and rng.random() < wear:
                continue
            for dy in range(scale):
                for dx in range(scale):
                    if shadow is not None:
                        L.px(cx + c * scale + dx - 1, y + r * scale + dy + 1, shadow)
        for (c, r) in pts:
            if rng is not None and wear > 0 and rng.random() < wear * 0.5:
                continue
            for dy in range(scale):
                for dx in range(scale):
                    L.px(cx + c * scale + dx, y + r * scale + dy, col, hgt, em)
        cx += (len(g[0]) + spacing) * scale
    return cx - x - spacing * scale


def text_center(L, cx, y, s, col, font='s', **kw):
    w = text_width(s, font, kw.get('spacing', 1)) * kw.get('scale', 1)
    return text(L, int(round(cx - w / 2)), y, s, col, font=font, **kw)


# --------------------------------------------------------------------------- dithering / ramps
def dmask(w: int, h: int, x0: int, y0: int, t, size: int = 4) -> np.ndarray:
    """Ordered-dither coverage mask: True where bayer threshold < t (t scalar or (h, w) array)."""
    return bayer(w, h, x0, y0, size) < t


def ladder_paint(L: Layer, mask, x0, y0, T, ladder, steep=2.6, hgt=None):
    """Fill mask (placed at x0, y0) with ladder colours chosen by float index T (same shape).  steep > 1
    keeps most pixels on pure ramp colours and confines the ordered dither to narrow transition bands."""
    h, w = mask.shape
    T = np.clip(T, 0, len(ladder) - 1)
    idx = np.floor(T).astype(int)
    fr = np.clip((T - idx - 0.5) * steep + 0.5, 0, 1)
    idx = np.clip(idx + (fr > bayer(w, h, x0, y0)), 0, len(ladder) - 1)
    L._put(mask, x0, y0, np.stack(ladder)[idx], hgt)


def ladder_shift(L: Layer, ladder, amount, x0=0, y0=0, x1=None, y1=None, mask=None, size: int = 4):
    """Move every pixel whose colour is in `ladder` by `amount` steps (float or (h, w) array, may be
    negative) with ordered dither -> clean 2-colour transitions (haze, stains, grime, light spill)."""
    x1 = L.w if x1 is None else min(L.w, x1)
    y1 = L.h if y1 is None else min(L.h, y1)
    x0, y0 = max(0, x0), max(0, y0)
    if x1 <= x0 or y1 <= y0:
        return
    sub = L.c[y0:y1, x0:x1]
    keys = col_key(sub[..., :3])
    lk = col_key(np.stack(ladder)[:, :3])
    idx = np.full(keys.shape, -1, np.int32)
    for i, k in enumerate(lk):
        idx[keys == k] = i
    ok = (idx >= 0) & (sub[..., 3] > 0)
    if mask is not None:
        ok &= mask[y0:y1, x0:x1] if mask.shape == L.c.shape[:2] else mask
    amt = np.broadcast_to(np.asarray(amount, np.float32), keys.shape)
    s = np.sign(amt)
    a = np.abs(amt)
    k = np.floor(a)
    thr = bayer(x1 - x0, y1 - y0, x0, y0, size)
    k = k + ((a - k) > thr)
    new = np.clip(idx + (s * k).astype(np.int32), 0, len(ladder) - 1)
    carr = np.stack(ladder)
    res = sub.copy()
    res[ok] = carr[new[ok]]
    L.c[y0:y1, x0:x1] = res


def recolor(L: Layer, pairs, mask=None):
    """Exact colour replace [(from, to), ...]."""
    keys = col_key(L.c[..., :3])
    out = L.c.copy()
    for a, b in pairs:
        m = (keys == col_key(np.asarray(a)[:3])) & (L.c[..., 3] > 0)
        if mask is not None:
            m &= mask
        out[m] = b
    L.c = out


def haze(L: Layer, fog_ladder, amount, power=1.0):
    """Atmospheric perspective inside a layer: every opaque pixel moves toward the fog ladder by
    `amount` (0..1, scalar or (h, w)), snapping onto the ladder with ordered dither."""
    a = L.alpha()
    lad = np.stack(fog_ladder).astype(np.float32)[:, :3]
    c = L.c[..., :3].astype(np.float32)
    lum = c @ np.array([0.3, 0.59, 0.11], np.float32)
    llum = lad @ np.array([0.3, 0.59, 0.11], np.float32)
    # position of each pixel's luminance on the fog ladder, then pushed toward the top
    T = np.interp(lum, llum, np.arange(len(lad), dtype=np.float32))
    amt = np.broadcast_to(np.asarray(amount, np.float32), lum.shape) ** power
    T = T + (len(lad) - 1 - T) * amt
    m = np.zeros((L.h, L.w), bool)
    m[:] = a
    ladder_paint(L, m, 0, 0, T, fog_ladder, steep=2.2)


# --------------------------------------------------------------------------- normals
def cyl_normal(L: Layer, x: int, y: int, w: int, h: int, mask=None, tilt_y: float = 0.0):
    """Explicit cylinder normals (vertical axis) for columns, pipes, domes, tanks."""
    xs = (np.arange(w, dtype=np.float32) + 0.5 - w / 2) / (w / 2)
    nx = np.clip(xs, -0.95, 0.95)
    nz = np.sqrt(1 - nx * nx)
    n = np.stack([nx, np.full_like(nx, tilt_y), nz], -1)
    n /= np.linalg.norm(n, axis=-1, keepdims=True)
    X0, Y0, X1, Y1 = max(0, x), max(0, y), min(L.w, x + w), min(L.h, y + h)
    if X1 <= X0 or Y1 <= Y0:
        return
    blk = np.repeat(n[None, X0 - x:X1 - x], Y1 - Y0, axis=0)
    m = L.c[Y0:Y1, X0:X1, 3] > 0
    if mask is not None:
        m &= mask[Y0 - y:Y1 - y, X0 - x:X1 - x]
    L.nrm[Y0:Y1, X0:X1][m] = blk[m]


def flat_normal(L: Layer, x, y, w, h, n, mask=None):
    v = np.asarray(n, np.float32)
    v = v / (np.linalg.norm(v) + 1e-6)
    X0, Y0, X1, Y1 = max(0, int(x)), max(0, int(y)), min(L.w, int(x + w)), min(L.h, int(y + h))
    if X1 <= X0 or Y1 <= Y0:
        return
    m = L.c[Y0:Y1, X0:X1, 3] > 0
    if mask is not None:
        m &= mask[Y0:Y1, X0:X1]
    L.nrm[Y0:Y1, X0:X1][m] = v


# --------------------------------------------------------------------------- building blocks
def snow_top(L: Layer, x, y, w, cols, depth=2, seed=0, ragged=True, hgt=0.75):
    """Snow along a horizontal top edge at row y (cols dark -> light, last = top highlight)."""
    rng = np.random.default_rng(abs(int(seed)) + 7)
    for xx in range(int(x), int(x + w)):
        d = depth + (1 if (ragged and rng.random() < 0.25) else 0) - (1 if (ragged and rng.random() < 0.15) else 0)
        for k in range(max(1, d)):
            c = cols[-1] if k == 0 else cols[max(0, len(cols) - 1 - k)]
            L.px(xx, y + k, c, hgt)
            if 0 <= y + k < L.h and 0 <= xx < L.w:
                L.nrm[y + k, xx] = (0.0, 0.8, 0.6)


def snow_lip(L: Layer, x, y, w, cols, seed=0, icicles=0.0, ice_col=None):
    """Overhanging snow cornice along an edge seen from slightly below: 1-2 px lip + optional icicles."""
    rng = np.random.default_rng(abs(int(seed)) + 3)
    for xx in range(int(x), int(x + w)):
        L.px(xx, y, cols[-1], 0.7)
        if rng.random() < 0.55:
            L.px(xx, y + 1, cols[-2], 0.65)
        if icicles and rng.random() < icicles:
            ln = int(rng.integers(1, 5))
            for k in range(ln):
                L.px(xx, y + 2 + k, ice_col if ice_col is not None else cols[0], 0.6)


def stains(L: Layer, x, y, w, h, ladder, seed=0, strength=1.0, density=0.35, length=(4, 14), darker=True):
    """Vertical streaks: shift colours of `ladder` one step darker in thin columns."""
    rng = np.random.default_rng(seed)
    for _ in range(int(w * density)):
        sx = int(x + rng.integers(0, max(1, w)))
        sy = int(y + rng.integers(0, max(1, h // 2)))
        ln = int(rng.integers(length[0], length[1] + 1))
        y1 = min(y + h, sy + ln, L.h)
        if y1 <= sy or not (0 <= sx < L.w) or sy < 0:
            continue
        prof = np.linspace(strength, 0.2 * strength, y1 - sy).astype(np.float32)[:, None]
        ladder_shift(L, ladder, -prof if darker else prof, sx, sy, sx + 1, y1)


def rustication(L: Layer, x, y, w, h, body, joint, hi=None, course=6, block=(14, 22), seed=0, hgt=0.5):
    """Rusticated stone base (neo-renaissance): courses with recessed joints and offset blocks."""
    rng = np.random.default_rng(seed)
    L.rect(x, y, w, h, body, hgt=hgt)
    yy = y
    row = 0
    while yy < y + h:
        L.hline(x, yy + course - 1, w, joint, hgt - 0.12)
        if hi is not None:
            L.hline(x, yy, w, hi, hgt + 0.04)
        xx = x - (block[0] // 2 if row % 2 else 0)
        while xx < x + w:
            bw = int(rng.integers(block[0], block[1] + 1))
            if x <= xx < x + w:
                L.vline(xx, yy, course - 1, joint, hgt - 0.12)
            xx += bw
        yy += course
        row += 1


def arch_mask(w: int, h: int, spring: int) -> np.ndarray:
    """Round-headed arch opening: (h, w) bool, semicircle on top of a rectangle starting at row `spring`."""
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    r = w / 2.0
    cy = spring
    m = yy >= cy
    m |= ((xx + 0.5 - r) ** 2 + (yy + 0.5 - cy) ** 2) <= r * r
    return m


def put_mask(L: Layer, m: np.ndarray, x0: int, y0: int, col, hgt=None, em=None):
    L._put(m, int(x0), int(y0), col, hgt, em)


def edge_of(m: np.ndarray) -> np.ndarray:
    p = np.pad(m, 1)
    inner = p[:-2, 1:-1] & p[2:, 1:-1] & p[1:-1, :-2] & p[1:-1, 2:]
    return m & ~inner


# --------------------------------------------------------------------------- people
def figure(H: int, coat, skin=None, hat='cap', facing='front', coat_len=0.74, rim=None, warm=None,
           arms='down', trousers=None, boots=None, scarf=None, hat_col=None, bag=None, seed=0,
           width=1.0, outline=None, hair=None) -> Layer:
    """Parametric person (feet at the bottom centre).  coat: ramp list dark -> light (>= 3).
    facing: 'front' | 'back' (back view: no face, collar + hair) | 'side'.
    hat: 'cap' | 'peaked' | 'fedora' | 'homburg' | 'scarf' | 'shapka' | 'bare' | 'beret'.
    rim: right-edge rim colour (dawn key light from the back-right); warm: (side, colour)."""
    W = max(9, int(round(H * 0.42 * width)) + 4)
    S = Layer(W, H + 2, 'fig')
    cx = W // 2
    k = H / 46.0
    top = 2
    head_h = max(3, int(round(7 * k)))
    head_w = max(3, int(round(6 * k)))
    sh_y = top + head_h + max(1, int(round(1 * k)))
    sh_w = max(5, int(round(13 * k * width)))
    hem_y = top + int(round((H - 1) * coat_len))
    hem_w = max(5, int(round(14 * k * width)))
    leg_w = max(1, int(round(3 * k)))
    gap = max(1, int(round(1.4 * k))) if H > 20 else 0
    base = top + H - 1
    trousers = trousers if trousers is not None else NI[2]
    boots = boots if boots is not None else NI[0]
    skin = skin if skin is not None else CR[3]
    hat_col = hat_col if hat_col is not None else coat[0]
    hair = hair if hair is not None else NI[2]
    for side in (-1, 1):
        lx = cx + (gap + 1) // 2 if side > 0 else cx - gap // 2 - leg_w
        S.rect(lx, hem_y - 1, leg_w, base + 1 - (hem_y - 1), trousers, hgt=0.5)
        bh = max(1, int(round(2.4 * k)))
        S.rect(lx - (1 if side < 0 and H > 24 else 0), base + 1 - bh, leg_w + (1 if H > 24 else 0), bh, boots,
               hgt=0.55)
    pts = [(cx - sh_w / 2, sh_y), (cx + sh_w / 2, sh_y), (cx + hem_w / 2, hem_y), (cx - hem_w / 2, hem_y)]
    m, x0, y0 = S.poly(pts, coat[1], hgt=0.6)
    hh, ww = m.shape
    yy, xx = np.mgrid[0:hh, 0:ww]
    rel = (xx + x0 - (cx - hem_w / 2)) / max(1, hem_w)
    S._put(m & (rel < 0.32), x0, y0, coat[0])
    if len(coat) > 2:
        S._put(m & (rel > 0.64) & (rel <= 0.86) & dmask(ww, hh, x0, y0, 0.5), x0, y0, coat[2])
    if H >= 30:
        if facing != 'back':
            S.vline(cx, sh_y + 2, hem_y - sh_y - 2, coat[0], 0.55)
        S.hline(cx - hem_w // 2 + 1, top + int(H * 0.47), hem_w - 2, coat[0], 0.55)
    aw = max(1, int(round(3 * k)))
    if arms == 'down':
        for side in (-1, 1):
            ax = int(cx - sh_w / 2) - (aw - 1) if side < 0 else int(cx + sh_w / 2) - 1
            S.rect(ax, sh_y + 1, aw, int(H * 0.38), coat[0] if side < 0 else coat[1], hgt=0.62)
            if facing != 'back':
                S.rect(ax, sh_y + 1 + int(H * 0.38), aw, max(1, int(2 * k)), skin if H > 30 else coat[0], hgt=0.6)
    elif arms == 'hold':          # holding papers / a case in front
        ay = sh_y + int(H * 0.2)
        S.rect(int(cx - sh_w / 2) - 1, sh_y + 1, aw, int(H * 0.18), coat[0], hgt=0.62)
        S.rect(int(cx + sh_w / 2) - 1, sh_y + 1, aw, int(H * 0.18), coat[1], hgt=0.62)
        S.rect(int(cx - sh_w / 2) + 1, ay, sh_w - 2, aw, coat[1], hgt=0.7)
    elif arms == 'push':          # porter pushing a cart (both arms forward-right)
        ay = sh_y + int(H * 0.22)
        S.rect(int(cx + sh_w / 2) - 2, ay, max(3, int(6 * k)), aw, coat[1], hgt=0.7)
        S.rect(int(cx - sh_w / 2) - 1, sh_y + 1, aw, int(H * 0.25), coat[0], hgt=0.62)
    hx0 = cx - head_w // 2
    if facing == 'back':
        S.rect(hx0, top, head_w, head_h, hair, hgt=0.7)
        S.vline(hx0 + head_w - 1, top + 1, head_h - 2, skin, 0.7)       # ear / neck edge in the rim light
        S.rect(hx0, top + head_h - 1, head_w, 1, skin if H > 30 else hair, hgt=0.7)
    else:
        S.rect(hx0, top, head_w, head_h, CR[2] if skin is CR[3] else skin, hgt=0.7)
        S.vline(hx0, top + 1, head_h - 2, CR[1], 0.7)
        S.vline(hx0 + head_w - 1, top + 1, head_h - 3, CR[4], 0.72)
        if H >= 38 and facing == 'front':
            ey = top + int(head_h * 0.45)
            S.px(hx0 + 1, ey, NI[2])
            S.px(hx0 + head_w - 2, ey, NI[2])
        for (px_, py_) in ((hx0, top), (hx0 + head_w - 1, top), (hx0, top + head_h - 1),
                           (hx0 + head_w - 1, top + head_h - 1)):
            S.c[py_, px_] = 0
    if scarf is not None:
        S.rect(cx - head_w // 2, top + head_h, head_w + (1 if H > 30 else 0), max(1, int(2 * k)), scarf, hgt=0.66)
    hk = max(1, int(round(2 * k)))
    if hat in ('fedora', 'homburg'):
        S.rect(hx0 - 1, top + hk - 1, head_w + 2, 1, hat_col, hgt=0.82)          # brim
        S.rect(hx0, top - 1, head_w, hk, hat_col, hgt=0.8)                        # crown
        if hat == 'homburg':
            S.hline(hx0, top + hk - 2, head_w, coat[0] if coat[0] is not hat_col else NI[1], 0.8)
    elif hat == 'peaked':
        S.rect(hx0, top - 1, head_w + 1, hk + 1, hat_col, hgt=0.8)
        S.hline(hx0 + (2 if facing != 'back' else -1), top + hk, head_w, hat_col, 0.8)
    elif hat == 'cap':
        S.rect(hx0, top - 1, head_w + 1, hk, hat_col, hgt=0.8)
        S.hline(hx0 + 1, top - 1 + hk, head_w + 1, hat_col, 0.8)
    elif hat == 'shapka':
        S.rect(hx0 - 1, top - 1, head_w + 2, hk + 1, hat_col, hgt=0.8)
        if H >= 26:
            S.rect(hx0 - 1, top + hk, 1, hk + 1, hat_col, hgt=0.75)
            S.rect(hx0 + head_w, top + hk, 1, hk + 1, hat_col, hgt=0.75)
    elif hat == 'scarf':
        S.rect(hx0 - 1, top - 1, head_w + 2, hk + 1, hat_col, hgt=0.8)
        S.rect(hx0 - 1, top - 1, 1, head_h + 1, hat_col, hgt=0.75)
        S.rect(hx0 + head_w, top - 1, 1, head_h + 1, hat_col, hgt=0.75)
    elif hat == 'beret':
        S.rect(hx0 - 1, top - 1, head_w + 1, hk, hat_col, hgt=0.8)
    if bag is not None:           # (colours, side) suitcase / briefcase held at the side
        bc, side = bag
        bw_, bh_ = max(3, int(7 * k)), max(3, int(6 * k))
        bx = (cx + sh_w // 2 + 1) if side > 0 else (cx - sh_w // 2 - bw_ - 1)
        by = top + int(H * 0.5)
        S.rect(bx, by, bw_, bh_, bc[1], hgt=0.7)
        S.hline(bx, by, bw_, bc[2], 0.75)
        S.vline(bx, by, bh_, bc[0], 0.65)
        S.px(bx + bw_ // 2, by - 1, bc[0])
    a = S.alpha()
    p = np.pad(a, 1)
    right_edge = a & ~p[1:-1, 2:]
    left_edge = a & ~p[1:-1, :-2]
    if rim is not None:
        rows = np.arange(S.h)[:, None]
        S.c[right_edge & (rows >= sh_y) & (rows < hem_y)] = rim
    if warm is not None:
        side, wc = warm
        e = left_edge if side == 'l' else right_edge
        S.c[e] = wc
    if outline is not None:
        S.outline(outline, outer=False, only_where=left_edge)
    return S


def tiny_person(L: Layer, x: int, ybase: int, h: int, body, head=None, rim=None, pose='stand', hat=None):
    """Far-away person 6..20 px tall (feet at ybase)."""
    head = head if head is not None else body
    hw = 1 if h < 9 else 2
    bw = 2 if h < 9 else 3
    hh = max(1, h // 6)
    L.rect(x, ybase - h, hw, hh, head)
    if hat is not None:
        L.rect(x - (1 if h >= 12 else 0), ybase - h - 1, hw + (2 if h >= 12 else 0), 1, hat)
    torso_h = int(h * 0.5)
    L.rect(x - (bw - hw) // 2, ybase - h + hh, bw, torso_h, body)
    ly = ybase - h + hh + torso_h
    if pose == 'walk':
        L.px(x - 1, ybase - 1, body)
        L.px(x + bw - 1, ybase - 1, body)
        L.rect(x, ly, max(1, bw - 1), ybase - ly - 1, body)
    else:
        L.rect(x, ly, max(1, bw - 1), ybase - ly, body)
        if h >= 10:
            L.px(x + bw - 2, ybase - 1, body)
    if rim is not None:
        L.vline(x + bw - 1 - (bw - hw) // 2, ybase - h + hh, torso_h, rim)


# --------------------------------------------------------------------------- export helpers
def crop_v(L: Layer, pad: int = 0):
    """Vertical crop to content rows. Returns (Layer, y_offset)."""
    rows = np.nonzero(L.c[..., 3].any(1))[0]
    if len(rows) == 0:
        return L, 0
    y0 = max(0, rows[0] - pad)
    y1 = min(L.h, rows[-1] + 1 + pad)
    return sub_layer(L, 0, y0, L.w, y1 - y0), y0


def crop_box(L: Layer, pad: int = 0):
    a = L.c[..., 3] > 0
    rows = np.nonzero(a.any(1))[0]
    cols = np.nonzero(a.any(0))[0]
    y0, y1 = max(0, rows[0] - pad), min(L.h, rows[-1] + 1 + pad)
    x0, x1 = max(0, cols[0] - pad), min(L.w, cols[-1] + 1 + pad)
    return sub_layer(L, x0, y0, x1 - x0, y1 - y0), x0, y0


def sub_layer(L: Layer, x0, y0, w, h) -> Layer:
    N = Layer(w, h, L.name)
    N.c = L.c[y0:y0 + h, x0:x0 + w].copy()
    N.hgt = L.hgt[y0:y0 + h, x0:x0 + w].copy()
    N.nrm = L.nrm[y0:y0 + h, x0:x0 + w].copy()
    N.em = L.em[y0:y0 + h, x0:x0 + w].copy()
    return N


def palette_report(img_arr: np.ndarray, extra=()):
    """Return colours used that are NOT in the scene palette."""
    pal = set(int(k) for k in col_key(np.stack(ALL + list(extra))[:, :3]))
    a = img_arr[..., 3] > 0
    keys = np.unique(col_key(img_arr[..., :3])[a])
    return [('#%06X' % int(k)) for k in keys if int(k) not in pal]


def save_png(arr: np.ndarray, path: str):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    Image.fromarray(arr, 'RGBA').save(path)
