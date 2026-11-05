"""explore_karsk -- pixel-art close-ups for the Karsk exploration finds (area: karsk-explore).

Writes assets/explore/karsk/<find>.png (256x160, shown x3 by the DiscoveryView, TECHNICAL_ARCHITECTURE 12.1).
Finds that show real Soviet state insignia exist twice (12.4): <name>.png carries the fictional
gear-and-wheat emblem, <name>_hist.png the hammer and sickle; loaders pick via Symbols.pick().

Original procedural pixel art: every image is built from code (shapes, ramps, ordered dither) in the `karsk`
palette of tools/pixelgen/pg.py plus the shared C-17 red ramp (pg.PALETTES['sepia']['red']). Nothing is
sampled, traced or downloaded. Deterministic: all randomness is seeded from crc32 of the image name.

Run:  py -3 -P tools/pixelgen/explore_karsk.py [--preview]   (--preview also writes x3 review sheets
into the scratch folder given by EXPLORE_KARSK_PREVIEW, never into the project)
"""
from __future__ import annotations

import math
import os
import sys
import zlib

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import numpy as np  # noqa: E402
from PIL import Image  # noqa: E402

import pg  # noqa: E402  (read-only use)
from pg import Layer, hx, bayer, value_noise  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
OUT = os.path.join(ROOT, 'assets', 'explore', 'karsk')
W, H = 256, 160

KP = pg.PALETTES['karsk']


def _r(n):
    return [hx(c) for c in KP[n]]


NI, TE, SA, SK, ST, RU, CO, SN, WO = (_r(n) for n in
                                      ('night', 'teal', 'sage', 'sky', 'stone', 'rust', 'copper', 'snow', 'wood'))
RED = [hx(c) for c in pg.PALETTES['sepia']['red']]
RAMPS = [NI, TE, SA, SK, ST, RU, CO, SN, WO, RED]
PALETTE = [c for r in RAMPS for c in r]
CLEAR = np.zeros(4, np.uint8)


def seed_of(name: str) -> int:
    return zlib.crc32(name.encode('utf-8')) & 0x7FFFFFFF


def rng_of(name: str) -> np.random.Generator:
    return np.random.default_rng(seed_of(name))


# --------------------------------------------------------------------------- colour maps
def _key(c) -> int:
    c = np.asarray(c, np.int64)
    return int((c[0] << 16) | (c[1] << 8) | c[2])


def _arr_key(a: np.ndarray) -> np.ndarray:
    a = a.astype(np.int64)
    return (a[..., 0] << 16) | (a[..., 1] << 8) | a[..., 2]


_DARK, _LIGHT = {}, {}
for _ramp in RAMPS:
    for _i, _c in enumerate(_ramp):
        _DARK.setdefault(_key(_c), _ramp[max(0, _i - 1)])
        _LIGHT.setdefault(_key(_c), _ramp[min(len(_ramp) - 1, _i + 1)])


def shift(L: Layer, mask: np.ndarray, steps: int):
    """Move every pixel under mask `steps` along its own ramp (negative = darker). Keeps the palette."""
    table = _DARK if steps < 0 else _LIGHT
    for _ in range(abs(steps)):
        keys = _arr_key(L.c)
        m = mask & (L.c[..., 3] > 0)
        if not m.any():
            return
        out = L.c.copy()
        for k in np.unique(keys[m]):
            sel = m & (keys == k)
            col = table.get(int(k))
            if col is not None:
                out[sel] = col
        L.c = out


def dither_mask(amount: np.ndarray, x0: int = 0, y0: int = 0, size: int = 4) -> np.ndarray:
    """Ordered-dither threshold of an amount field in [0,1] (same shape) -> bool mask."""
    h, w = amount.shape
    return amount > bayer(w, h, x0, y0, size)


def radial(w, h, cx, cy, rx, ry=None) -> np.ndarray:
    ry = rx if ry is None else ry
    yy, xx = np.mgrid[0:h, 0:w]
    return np.sqrt(((xx + 0.5 - cx) / rx) ** 2 + ((yy + 0.5 - cy) / ry) ** 2)


def light_pool(L: Layer, cx, cy, rx, ry, steps=1, power=1.0, where=None):
    """Brighten (steps > 0) or darken (< 0) a soft elliptical pool with ordered dither falloff."""
    d = radial(L.w, L.h, cx, cy, rx, ry)
    for s in range(1, abs(steps) + 1):
        amt = np.clip(1.0 - d * (0.55 + 0.45 * s / abs(steps)), 0, 1) ** power
        m = dither_mask(amt)
        if where is not None:
            m &= where
        shift(L, m, 1 if steps > 0 else -1)


def vignette(L: Layer, strength=0.9, inner=0.62):
    d = radial(L.w, L.h, L.w / 2, L.h / 2, L.w / 2, L.h / 2)
    amt = np.clip((d - inner) / (1.25 - inner), 0, 1) * strength
    shift(L, dither_mask(amt), -1)
    amt2 = np.clip((d - inner - 0.22) / (1.3 - inner), 0, 1) * strength
    shift(L, dither_mask(amt2), -1)


def frame(L: Layer):
    """1 px near-black rim + 1 px inner dark line (consistent card edge)."""
    L.rect(0, 0, L.w, 1, NI[0]); L.rect(0, L.h - 1, L.w, 1, NI[0])
    L.rect(0, 0, 1, L.h, NI[0]); L.rect(L.w - 1, 0, 1, L.h, NI[0])


# --------------------------------------------------------------------------- tones & shapes
def tone(L: Layer, mask: np.ndarray, x0: int, y0: int, t, ramp, dither=True):
    t = np.broadcast_to(np.asarray(t, np.float32), mask.shape)
    L.tone_fill(mask, x0, y0, np.clip(t, 0, 1), ramp, dither)


def full(h, w):
    return np.ones((h, w), bool)


def sphere_t(w, h, cx, cy, rx, ry, light=(-0.55, -0.6, 0.58), base=0.0, amp=1.0, rim=0.0):
    """Lambert-ish tone of an ellipsoid; returns (mask, t)."""
    yy, xx = np.mgrid[0:h, 0:w]
    dx = (xx + 0.5 - cx) / rx
    dy = (yy + 0.5 - cy) / ry
    r2 = dx * dx + dy * dy
    m = r2 <= 1.0
    nz = np.sqrt(np.clip(1 - r2, 0, 1))
    lx, ly, lz = light
    ln = math.sqrt(lx * lx + ly * ly + lz * lz)
    lam = (dx * lx + dy * ly + nz * lz) / ln
    t = base + amp * np.clip(lam, -1, 1) * 0.5 + 0.5 * amp
    if rim:
        t = t + rim * np.clip(dx, 0, 1) ** 4 * (r2 > 0.55)
    return m, t


def poly_mask(pts, w=W, h=H):
    L = Layer(w, h)
    m, x0, y0 = L.poly_mask(pts)
    out = np.zeros((h, w), bool)
    X0, Y0 = max(0, x0), max(0, y0)
    X1, Y1 = min(w, x0 + m.shape[1]), min(h, y0 + m.shape[0])
    if X1 > X0 and Y1 > Y0:
        out[Y0:Y1, X0:X1] = m[Y0 - y0:Y1 - y0, X0 - x0:X1 - x0]
    return out


def ellipse_full(cx, cy, rx, ry, w=W, h=H):
    yy, xx = np.mgrid[0:h, 0:w]
    return ((xx + 0.5 - cx) / rx) ** 2 + ((yy + 0.5 - cy) / ry) ** 2 <= 1.0


def put(L: Layer, mask: np.ndarray, col):
    L.c[mask] = col


def thick_line(L: Layer, x0, y0, x1, y1, col, t=2):
    n = int(max(abs(x1 - x0), abs(y1 - y0)) * 2) + 1
    for i in range(n + 1):
        f = i / n
        x = x0 + (x1 - x0) * f
        y = y0 + (y1 - y0) * f
        L.rect(int(round(x - (t - 1) / 2)), int(round(y - (t - 1) / 2)), t, t, col)


def outline_mask(mask: np.ndarray, diagonal=False) -> np.ndarray:
    p = np.pad(mask, 1)
    nb = p[:-2, 1:-1] | p[2:, 1:-1] | p[1:-1, :-2] | p[1:-1, 2:]
    if diagonal:
        nb |= p[:-2, :-2] | p[:-2, 2:] | p[2:, :-2] | p[2:, 2:]
    return nb & ~mask


def edge_mask(mask: np.ndarray, side: str) -> np.ndarray:
    """Pixels of mask whose neighbour on `side` (l/r/t/b) is outside the mask."""
    p = np.pad(mask, 1)
    nb = {'l': p[1:-1, :-2], 'r': p[1:-1, 2:], 't': p[:-2, 1:-1], 'b': p[2:, 1:-1]}[side]
    return mask & ~nb


def snow_on_top(L: Layer, mask: np.ndarray, depth=2, seed=0, cols=None, coverage=0.92):
    """Snow lying on every upward-facing edge of mask (drawn above it, 1..depth px, bumpy)."""
    cols = cols or [SN[1], SN[3], SN[4]]
    rng = np.random.default_rng(seed)
    top = edge_mask(mask, 't')
    ys, xs = np.nonzero(top)
    for x, y in zip(xs, ys):
        if rng.random() > coverage:
            continue
        d = int(rng.integers(1, depth + 1))
        for k in range(d):
            yy = y - 1 - k
            if 0 <= yy < L.h:
                L.c[yy, x] = cols[2] if k == d - 1 else cols[1]
        if 0 <= y < L.h:
            L.c[y, x] = cols[0] if d > 1 else L.c[y, x]


def flakes(L: Layer, n, seed, region=None, big=0.25):
    rng = np.random.default_rng(seed)
    x0, y0, x1, y1 = region or (1, 1, L.w - 1, L.h - 1)
    for _ in range(n):
        x = int(rng.integers(x0, x1)); y = int(rng.integers(y0, y1))
        c = SN[4] if rng.random() < 0.5 else SN[3]
        L.px(x, y, c)
        if rng.random() < big:
            L.px(x + 1, y, SN[2]); L.px(x, y + 1, SN[2])


# --------------------------------------------------------------------------- pixel fonts (Cyrillic subset)
# 5x7 capitals for painted signs / mastheads; drawn 1 px or as bold 2 px strokes.
F57 = {
    'А': [".###.", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"],
    'Б': ["#####", "#....", "#....", "####.", "#...#", "#...#", "####."],
    'В': ["####.", "#...#", "#...#", "####.", "#...#", "#...#", "####."],
    'Г': ["#####", "#....", "#....", "#....", "#....", "#....", "#...."],
    'Д': [".###.", ".#.#.", ".#.#.", ".#.#.", ".#.#.", "#####", "#...#"],
    'Е': ["#####", "#....", "#....", "####.", "#....", "#....", "#####"],
    'З': [".###.", "#...#", "....#", "..##.", "....#", "#...#", ".###."],
    'И': ["#...#", "#...#", "#..##", "#.#.#", "##..#", "#...#", "#...#"],
    'К': ["#...#", "#..#.", "#.#..", "##...", "#.#..", "#..#.", "#...#"],
    'Л': ["..###", ".#..#", ".#..#", ".#..#", ".#..#", ".#..#", "#...#"],
    'М': ["#...#", "##.##", "#.#.#", "#.#.#", "#...#", "#...#", "#...#"],
    'Н': ["#...#", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"],
    'О': [".###.", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."],
    'П': ["#####", "#...#", "#...#", "#...#", "#...#", "#...#", "#...#"],
    'Р': ["####.", "#...#", "#...#", "####.", "#....", "#....", "#...."],
    'С': [".###.", "#...#", "#....", "#....", "#....", "#...#", ".###."],
    'Т': ["#####", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."],
    'У': ["#...#", "#...#", "#...#", ".####", "....#", "#...#", ".###."],
    'Ч': ["#...#", "#...#", "#...#", ".####", "....#", "....#", "....#"],
    'Ы': ["#...#", "#...#", "#...#", "###.#", "#.#.#", "#.#.#", "###.#"],
    'Я': [".####", "#...#", "#...#", ".####", "..#.#", ".#..#", "#...#"],
    'Й': [".#.#.", "#...#", "#..##", "#.#.#", "##..#", "#...#", "#...#"],
    'Ш': ["#.#.#", "#.#.#", "#.#.#", "#.#.#", "#.#.#", "#.#.#", "#####"],
    'Ж': ["#.#.#", "#.#.#", ".###.", "..#..", ".###.", "#.#.#", "#.#.#"],
    'Л2': ["..##.", ".#..#", ".#..#", ".#..#", ".#..#", "#...#", "#...#"],
    '0': [".###.", "#...#", "#..##", "#.#.#", "##..#", "#...#", ".###."],
    '1': ["..#..", ".##..", "..#..", "..#..", "..#..", "..#..", ".###."],
    '2': [".###.", "#...#", "....#", "...#.", "..#..", ".#...", "#####"],
    '3': ["####.", "....#", "....#", ".###.", "....#", "....#", "####."],
    '4': ["...#.", "..##.", ".#.#.", "#..#.", "#####", "...#.", "...#."],
    '6': [".###.", "#....", "#....", "####.", "#...#", "#...#", ".###."],
    '7': ["#####", "....#", "...#.", "..#..", ".#...", ".#...", ".#..."],
    '8': [".###.", "#...#", "#...#", ".###.", "#...#", "#...#", ".###."],
    '9': [".###.", "#...#", "#...#", ".####", "....#", "....#", ".###."],
    '-': [".....", ".....", ".....", "####.", ".....", ".....", "....."],
    '.': [".", ".", ".", ".", ".", ".", "#"],
    '№': ["#..#.", "##.#.", "#.##.", "#..#.", "#..#.", "....#", "...##"],
}
# 3x5 small capitals / digits for labels, stencils and print.
F35 = {
    'А': ["###", "#.#", "###", "#.#", "#.#"], 'В': ["##.", "#.#", "##.", "#.#", "##."],
    'Г': ["###", "#..", "#..", "#..", "#.."], 'Д': [".##", ".##", "#.#", "###", "#.#"],
    'Е': ["###", "#..", "##.", "#..", "###"], 'И': ["#.#", "#.#", "###", "###", "#.#"],
    'К': ["#.#", "#.#", "##.", "#.#", "#.#"], 'Л': [".##", "#.#", "#.#", "#.#", "#.#"],
    'М': ["#.#", "###", "###", "#.#", "#.#"], 'Н': ["#.#", "#.#", "###", "#.#", "#.#"],
    'О': ["###", "#.#", "#.#", "#.#", "###"], 'П': ["###", "#.#", "#.#", "#.#", "#.#"],
    'Р': ["###", "#.#", "###", "#..", "#.."], 'С': ["###", "#..", "#..", "#..", "###"],
    'Т': ["###", ".#.", ".#.", ".#.", ".#."], 'У': ["#.#", "#.#", "###", "..#", "##."],
    'Ч': ["#.#", "#.#", "###", "..#", "..#"], 'Э': ["##.", "..#", ".##", "..#", "##."],
    'Ш': ["#.#", "#.#", "###", "###", "###"], 'Я': ["###", "#.#", "###", ".##", "#.#"],
    'З': ["##.", "..#", ".#.", "..#", "##."], 'Б': ["###", "#..", "###", "#.#", "###"],
    '0': ["###", "#.#", "#.#", "#.#", "###"], '1': [".#", "##", ".#", ".#", ".#"],
    '2': ["##.", "..#", ".#.", "#..", "###"], '3': ["##.", "..#", ".#.", "..#", "##."],
    '4': ["#.#", "#.#", "###", "..#", "..#"], '5': ["###", "#..", "##.", "..#", "##."],
    '6': [".##", "#..", "###", "#.#", "###"], '7': ["###", "..#", ".#.", ".#.", ".#."],
    '8': ["###", "#.#", "###", "#.#", "###"], '9': ["###", "#.#", "###", "..#", "##."],
    '-': ["...", "...", "##.", "...", "..."], '.': [".", ".", ".", ".", "#"],
    ':': [".", "#", ".", "#", "."], '/': ["..#", "..#", ".#.", "#..", "#.."], '№': ["#..#", "##.#", "#.##", "#..#", "#..#"],
}


def glyph(font, ch):
    return font.get(ch)


def text_w(s, font=F57, spacing=1, scale=1):
    w = 0
    for ch in s:
        if ch == ' ':
            w += (3 if font is F57 else 2) * scale
            continue
        g = font.get(ch, font.get('-'))
        w += (len(g[0]) + spacing) * scale
    return max(0, w - spacing * scale)


def draw_text(L: Layer, x, y, s, col, font=F57, spacing=1, scale=1, wear=0.0, rng=None, shadow=None,
              bold=False):
    """Pixel text. scale>1 draws each glyph pixel as a scale x scale block (painted letters);
    bold widens strokes by one pixel to the right. wear drops pixels (chipped paint / chalk)."""
    cx = x
    for ch in s:
        if ch == ' ':
            cx += (3 if font is F57 else 2) * scale
            continue
        g = font.get(ch)
        if g is None:
            cx += 4 * scale
            continue
        for r, row in enumerate(g):
            for c, v in enumerate(row):
                if v != '#':
                    continue
                for by in range(scale):
                    for bx in range(scale + (1 if bold else 0)):
                        if wear and rng is not None and rng.random() < wear:
                            continue
                        px, py = cx + c * scale + bx, y + r * scale + by
                        if shadow is not None:
                            L.px(px + 1, py + 1, shadow)
                        L.px(px, py, col)
        cx += (len(g[0]) + spacing) * scale
    return cx - x


def pseudo_print(L: Layer, x, y, w, col, rng, gap_every=(2, 6), wear=0.0, h=3):
    """Illegible printed text line: blocky 2-3 px glyph runs with word gaps (reads as print at 1:1)."""
    cx = x
    end = x + w
    while cx < end - 2:
        n = int(rng.integers(gap_every[0], gap_every[1] + 1))
        for _ in range(n):
            gw = int(rng.integers(2, 4))
            if cx + gw > end:
                break
            for gx in range(gw):
                for gy in range(h):
                    if rng.random() < 0.72 - wear:
                        L.px(cx + gx, y + gy, col)
            cx += gw + 1
        cx += 2


def pseudo_hand(L: Layer, x, y, w, col, rng, slant=1):
    """Handwritten scribble line (connected humps, ascenders)."""
    cx = x
    base = y + 4
    prev = (cx, base)
    while cx < x + w - 3:
        k = rng.random()
        step = int(rng.integers(2, 4))
        if k < 0.2:
            pt = (cx + 1 + slant, base - 4)
        elif k < 0.6:
            pt = (cx + 1, base - 2)
        else:
            pt = (cx + step, base)
        L.line(prev[0], prev[1], pt[0], pt[1], col)
        prev = pt
        cx += step
        if rng.random() < 0.18:
            cx += 3
            prev = (cx, base)


# --------------------------------------------------------------------------- emblems (12.4)
# Hand-placed grids at final size (1 px = 1 game px). Layout of the real emblem (as in the other Karsk
# generators): sickle tip at the top, crescent blade round the right side, handle down-left; hammer head
# at the upper left, shaft down-right across the blade.
HS19 = """
...................
..........###......
....##......###....
...###.......###...
..###.........###..
.#####........###..
.##..##.......####.
......##......####.
.......##.....####.
........##....####.
.........##...####.
..........##.#####.
...........######..
...........######..
...#############...
..##############...
.###..#######..##..
###.............##.
##................."""
HS13 = """
.............
...#....##...
..##.....##..
.####.....##.
.#.###....##.
....###...##.
.....###..##.
......###.##.
.......#####.
..###..####..
.###########.
###..####.###
##..........."""
# Fictional neutral emblem: cogwheel with a wheat ear across it (same footprints as the HS grids).
GW19 = """
................E..
........###....EE..
....#...###...EE...
...###.#####.EEE...
....########EEE....
.....######EEE.....
....###...EEE##....
..#####..EEE#####..
..#####.EEE.#####..
..#####.E...#####..
....###E....###....
.....#E#######.....
....#E#########....
...#E#.#####.###...
...E#...###...#....
........###........
...................
...................
..................."""
GW13 = """
..........E..
.....##..EE..
..#.####EE...
.#####.EE....
..##..EE##...
.###.EE.###..
.###EE..###..
..#E#..##....
..E.#####....
.E.##.#.#....
E....##......
.............
............."""


def _grid(s: str, mark='#'):
    rows = [r for r in s.strip().splitlines()]
    return np.array([[ch in mark for ch in r] for r in rows], bool)


def hammer_sickle_mask(size=19):
    return _grid(HS19 if size >= 17 else HS13)


def gear_wheat_masks(size=19):
    """(cog mask, ear mask): the ear is drawn lighter and separated from the cog by a dark gap."""
    s = GW19 if size >= 17 else GW13
    return _grid(s, '#E'), _grid(s, 'E')


def hammer_sickle_big(n=31) -> np.ndarray:
    """Large hammer and sickle (crescent blade, hammer head band, round handle ends), n x n."""
    k = n / 31.0
    yy, xx = np.mgrid[0:n, 0:n]
    x = xx + 0.5
    y = yy + 0.5
    co, ro, ci, ri = (15.8 * k, 14.6 * k), 13.6 * k, (13.4 * k, 12.4 * k), 10.6 * k
    ang = np.degrees(np.arctan2(y - co[1], x - co[0]))
    blade = ((np.hypot(x - co[0], y - co[1]) <= ro) & ~(np.hypot(x - ci[0], y - ci[1]) <= ri)
             & (ang >= -97) & (ang <= 134))

    def seg(p, q, w):
        l2 = (q[0] - p[0]) ** 2 + (q[1] - p[1]) ** 2
        t = np.clip(((x - p[0]) * (q[0] - p[0]) + (y - p[1]) * (q[1] - p[1])) / l2, 0, 1)
        return np.hypot(x - (p[0] + t * (q[0] - p[0])), y - (p[1] + t * (q[1] - p[1]))) <= w / 2

    a = math.radians(129)
    h0 = (co[0] + (ro - 1.2 * k) * math.cos(a), co[1] + (ro - 1.2 * k) * math.sin(a))
    m = blade | seg(h0, (1.6 * k, 29.6 * k), 3.2 * k)
    hc = (5.6 * k, 6.8 * k)
    s = (x + y) - (hc[0] + hc[1])
    d = (x - y) - (hc[0] - hc[1])
    m |= (np.abs(s) <= 3.0 * k) & (np.abs(d) <= 7.2 * k)
    m |= seg(hc, (27.8 * k, 28.2 * k), 3.3 * k)
    return m


def gear_wheat_big(n=31):
    """Fictional neutral emblem (12.4): cogwheel inside a wreath of two wheat ears.
    Returns (cog mask, stem mask, [grain masks]) for an n x n box."""
    k = n / 31.0
    c = (n / 2 - 0.5, n * 0.40)
    yy, xx = np.mgrid[0:n, 0:n]
    x = xx + 0.5
    y = yy + 0.5
    r = np.hypot(xx - c[0], yy - c[1])
    cog = (r <= 7.2 * k) & (r >= 3.4 * k)
    for t in range(8):
        a = math.radians(t * 45 + 22.5)
        ux, uy = math.cos(a), math.sin(a)
        al = (xx - c[0]) * ux + (yy - c[1]) * uy
        ac = -(xx - c[0]) * uy + (yy - c[1]) * ux
        cog |= (al >= 6.6 * k) & (al <= 9.8 * k) & (np.abs(ac) <= 1.75 * k)
    grains, stem = [], np.zeros((n, n), bool)
    for side in (-1, 1):
        p0 = (c[0] + side * 2.0 * k, n - 1.5)
        p1 = (c[0] + side * 13.5 * k, n - 6.0 * k)
        p2 = (c[0] + side * 12.5 * k, c[1] - 9.0 * k)

        def bez(t, p0=p0, p1=p1, p2=p2):
            return ((1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * p1[0] + t * t * p2[0],
                    (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * p1[1] + t * t * p2[1])
        for i in range(300):
            px, py = bez(i / 299)
            if 0 <= int(px) < n and 0 <= int(py) < n:
                stem[int(py), int(px)] = True
        for g in range(7):
            t = 0.36 + 0.62 * g / 6
            px, py = bez(t)
            qx, qy = bez(min(1.0, t + 0.01))
            tl = math.hypot(qx - px, qy - py)
            tx, ty = (qx - px) / tl, (qy - py) / tl
            nx, ny = -ty, tx
            out = 1 if g % 2 == 0 else -1
            gx, gy = px + nx * out * 1.5 * k, py + ny * out * 1.5 * k
            rot = 0.6 * out * side
            ux = tx * math.cos(rot) - ty * math.sin(rot)
            uy = tx * math.sin(rot) + ty * math.cos(rot)
            ga = (x - gx) * ux + (y - gy) * uy
            gc = -(x - gx) * uy + (y - gy) * ux
            grains.append((ga * ga / (2.0 * k) ** 2 + gc * gc / (1.05 * k) ** 2) <= 1)
        px, py = bez(1.0)
        grains.append(np.hypot(x - px, (y - py) * 0.7) <= 1.2 * k)
    return cog, stem, grains


def draw_gear_wheat(L: Layer, x, y, n, outline_col, cols=None):
    cols = cols or (CO[3], CO[4], CO[1])
    cog, stem, grains = gear_wheat_big(n)
    draw_emblem(L, x, y, cog, cols)
    for yy, xx in zip(*np.nonzero(stem & ~cog)):
        L.px(x + xx, y + yy, cols[2])
    allg = np.zeros_like(cog)
    for g in grains:
        allg |= g
    for g in grains:
        ring = outline_mask(g) & ~cog
        for yy, xx in zip(*np.nonzero(ring)):
            L.px(x + xx, y + yy, outline_col)
    for g in grains:
        draw_emblem(L, x, y, g, cols)


def draw_emblem(L: Layer, x, y, mask, cols, shade_dir=(1, 1)):
    """Stamp an emblem mask in a metal/gold ramp: base, lit top-left edge, shadow bottom-right."""
    h, w = mask.shape
    base, lit, dark = cols
    for yy in range(h):
        for xx in range(w):
            if mask[yy, xx]:
                L.px(x + xx, y + yy, base)
    up = edge_mask(mask, 't') | edge_mask(mask, 'l')
    dn = edge_mask(mask, 'b') | edge_mask(mask, 'r')
    ys, xs = np.nonzero(up)
    for yy, xx in zip(ys, xs):
        L.px(x + xx, y + yy, lit)
    ys, xs = np.nonzero(dn & ~up)
    for yy, xx in zip(ys, xs):
        L.px(x + xx, y + yy, dark)


# --------------------------------------------------------------------------- QA
def palette_violations(img: np.ndarray) -> int:
    keys = _arr_key(img[..., :3])
    ok = np.zeros(keys.shape, bool)
    for c in PALETTE:
        ok |= keys == _key(c)
    return int(((img[..., 3] > 0) & ~ok).sum())


def save(L: Layer, name: str, out_dir=OUT):
    os.makedirs(out_dir, exist_ok=True)
    L.c[..., 3] = 255
    bad = palette_violations(L.c)
    if bad:
        raise SystemExit('%s: %d off-palette pixels' % (name, bad))
    path = os.path.join(out_dir, name + '.png')
    Image.fromarray(L.c, 'RGBA').save(path)
    return path


# =========================================================================== shared materials
def wood_planks_v(L: Layer, x, y, w, h, ramp, plank=7, seed=0, base=0.45, var=0.18, grain=True):
    """Vertical boards: per-board tone, 1 px dark seams, fine vertical grain, knots."""
    rng = np.random.default_rng(seed)
    cx = x
    while cx < x + w:
        pw = int(plank + rng.integers(-1, 2))
        pw = min(pw, x + w - cx)
        bt = base + rng.uniform(-var, var)
        yy, xx = np.mgrid[0:h, 0:pw]
        n = value_noise(pw, h, 6, seed=int(rng.integers(0, 1 << 30)), octaves=2)
        t = bt + (n - 0.5) * 0.22
        if grain:
            t += np.where((xx * 7 + (yy // 9)) % 5 == 0, -0.08, 0.0)
        tone(L, full(h, pw), cx, y, t, ramp)
        L.rect(cx + pw - 1, y, 1, h, ramp[0])
        if pw > 3:
            L.rect(cx, y, 1, h, ramp[min(len(ramp) - 1, 2)] if bt > 0.5 else ramp[1])
        if rng.random() < 0.35 and h > 12:
            ky = y + int(rng.integers(3, h - 3))
            L.px(cx + pw // 2, ky, ramp[0]); L.px(cx + pw // 2 + 1, ky, ramp[1])
        cx += pw


def wood_planks_h(L: Layer, x, y, w, h, ramp, plank=6, seed=0, base=0.45, var=0.15):
    rng = np.random.default_rng(seed)
    cy = y
    while cy < y + h:
        ph = int(plank + rng.integers(-1, 2))
        ph = min(ph, y + h - cy)
        bt = base + rng.uniform(-var, var)
        n = value_noise(w, ph, 9, seed=int(rng.integers(0, 1 << 30)), octaves=2)
        yy, xx = np.mgrid[0:ph, 0:w]
        t = bt + (n - 0.5) * 0.2 + np.where(((xx // 11) + yy * 3) % 7 == 0, -0.07, 0.0)
        tone(L, full(ph, w), x, cy, t, ramp)
        L.rect(x, cy + ph - 1, w, 1, ramp[0])
        L.rect(x, cy, w, 1, ramp[min(len(ramp) - 1, 3)] if bt > 0.45 else ramp[2])
        cy += ph


def nail(L: Layer, x, y):
    L.px(x, y, ST[4]); L.px(x + 1, y, ST[2]); L.px(x, y + 1, RU[1])


def band(t, levels, soft=0.24):
    """Posterise t (0..1) to `levels` steps with narrow transitions -> mostly solid ramp colours, ordered
    dither only along the band edges (clean pixel-art shading instead of noise)."""
    s = np.clip(t, 0, 1) * (levels - 1)
    i = np.floor(s)
    f = s - i
    f2 = np.clip((f - (0.5 - soft / 2)) / soft, 0, 1)
    return np.clip((i + f2) / (levels - 1), 0, 1)


# =========================================================================== 1. banner (+ _hist)
def img_banner(hist: bool) -> Layer:
    name = 'banner'
    rng = rng_of(name)
    L = Layer(W, H)
    # hoarding behind: weathered vertical boards, sky slit at the very top
    L.vgrad(0, 0, W, 9, [SK[2], SK[3], SK[4]])
    wood_planks_v(L, 0, 8, W, H - 8, [WO[0], WO[1], WO[2], WO[3], ST[3]], plank=11,
                  seed=seed_of('banner.boards'), base=0.40, var=0.12)
    L.rect(0, 8, W, 1, WO[0])
    for x in range(0, W):
        if (x * 7) % 11 < 8:
            L.px(x, 7, SN[3])
        if (x * 5) % 13 < 4:
            L.px(x, 6, SN[4])
    # cloth: x 8..247, top edge sags between four nails
    bx0, bx1, by0, by1 = 8, 248, 24, 134
    nails_x = [bx0 + 2, 88, 168, bx1 - 3]
    sag = np.zeros(W)
    for a, b in zip(nails_x[:-1], nails_x[1:]):
        for x in range(a, b + 1):
            sag[x] = 3.4 * math.sin(math.pi * (x - a) / max(1, b - a))
    yy, xx = np.mgrid[0:H, 0:W]
    sg = sag[np.clip(xx, 0, W - 1)]
    cloth = (xx >= bx0) & (xx < bx1) & (yy >= by0 + sg.astype(int)) & (yy < by1 + (sg * 0.4).astype(int))
    # broad folds hanging from the nails + slight belly between them; light from the upper right
    fold = np.zeros((H, W))
    for a, b in zip(nails_x[:-1], nails_x[1:]):
        mid = (a + b) / 2
        w = (b - a) / 2
        d = (xx - mid) / w
        inside = (xx >= a) & (xx <= b)
        fold += inside * (0.16 * np.cos(d * math.pi * 1.5) * np.clip(1 - (yy - by0) / 120.0, 0.35, 1))
    fold += 0.07 * np.sin(xx * 0.075 + 1.3)
    t = 0.55 + fold + (xx / W) * 0.16 - ((yy - by0) / (by1 - by0)) * 0.10
    tone(L, cloth, 0, 0, band(t, 4, 0.30), RED)
    # old slogan ghost: painted over, shows through as a faint lighter tone between the new letters
    ghost = Layer(W, H)
    gl1 = 'СЛАВА ТОВ.'
    gx, gy = 36, 103
    draw_text(ghost, gx, gy, gl1, RED[3], F57, spacing=2, scale=2)
    name_x0 = gx + text_w(gl1 + ' ', F57, 2, 2)
    draw_text(ghost, name_x0, gy, 'ВОРОНОВУ', RED[3], F57, spacing=2, scale=2)
    gm = (ghost.c[..., 3] > 0) & cloth
    # the old paint has cracked: keep it only in a lacy pattern so it reads as a faint ghost
    lace = dither_mask(np.full((H, W), 0.62)) & (value_noise(W, H, 4, seed=seed_of('banner.lace'), octaves=2) > 0.30)
    was_light = L.c[..., 0] == RED[3][0]
    put(L, gm & lace & ~was_light, RED[3])
    put(L, gm & lace & was_light, RED[2])
    # the name was painted out: streaky darker brushwork with ragged ends
    nw = text_w('ВОРОНОВУ', F57, 2, 2)
    patch = np.zeros((H, W), bool)
    for row in range(gy - 3, gy + 17):
        j0 = int(3 * math.sin(row * 1.31) + 2 * math.sin(row * 0.47))
        j1 = int(3 * math.cos(row * 0.93))
        patch[row, name_x0 - 5 + j0:name_x0 + nw + 5 + j1] = True
    patch &= cloth
    streak = 0.30 + 0.10 * (value_noise(W, H, 3, seed=seed_of('banner.brush'), octaves=1) > 0.62) + fold * 0.6
    tone(L, patch, 0, 0, band(streak, 3, 0.2), RED[:3])
    # fresh slogan in cream sign paint (two lines), shaded by the same folds
    paint = Layer(W, H)
    l1, l2 = 'ВОССТАНОВИМ', 'ВМЕСТЕ'
    w1 = text_w(l1, F57, 2, 2)
    x_text = (W - w1) // 2
    draw_text(paint, x_text, 36, l1, SN[4], F57, spacing=2, scale=2)
    draw_text(paint, x_text + (w1 - text_w(l2, F57, 2, 2)) // 2, 66, l2, SN[4], F57, spacing=2, scale=2)
    pm = (paint.c[..., 3] > 0) & cloth
    pt = 0.50 + fold * 2.0 + (xx / W) * 0.30
    tone(L, pm, 0, 0, band(pt, 4, 0.3), [SN[1], SN[2], SN[3], SN[4]])
    # brush ends: occasional short drips
    ys, xs = np.nonzero(edge_mask(pm, 'b'))
    for yv, xv in zip(ys, xs):
        if rng.random() < 0.045 and yv + 2 < H and cloth[yv + 2, xv]:
            L.px(xv, yv + 1, SN[1])
    # emblem (gold paint) at the left, vertically centred on the slogan
    for ex, ey, flip in ((10, 40, False), (W - 10 - 37, 40, True)):
        if hist:
            m = hammer_sickle_big(37)
            draw_emblem(L, ex, ey, m, (CO[3], CO[4], CO[1]))
        else:
            draw_gear_wheat(L, ex, ey, 37, RED[1])
    # hems, nails and rope ties, snow on the top hem
    put(L, edge_mask(cloth, 't'), RED[1])
    put(L, edge_mask(cloth, 'b'), RED[0])
    put(L, edge_mask(cloth, 'l') | edge_mask(cloth, 'r'), RED[0])
    for nx in nails_x:
        ny = by0 + int(sag[nx])
        L.rect(nx - 1, ny - 2, 3, 3, ST[1])
        L.px(nx, ny - 2, ST[4]); L.px(nx - 1, ny - 1, ST[3])
        L.px(nx + 1, ny + 1, WO[2]); L.px(nx + 1, ny + 2, WO[1])
    snow_on_top(L, cloth & (yy < by0 + 6), depth=2, seed=11, coverage=0.8)
    # shadow of the cloth on the boards below the hem
    below = np.roll(cloth, 2, axis=0) & ~cloth & (yy > by0 + 20)
    shift(L, below, -1)
    light_pool(L, -20, H + 30, 190, 110, steps=-1, power=1.2)
    flakes(L, 22, seed_of('banner.flakes'))
    vignette(L, 0.75)
    frame(L)
    return L


# =========================================================================== 2. newspaper (+ _hist)
def halftone_photo(L: Layer, x, y, w, h, seed):
    """Grainy newspaper photo: winter forest clearing, a row of men in coats and hats (a 'commission')."""
    rng = np.random.default_rng(seed)
    yy, xx = np.mgrid[0:h, 0:w]
    t = 0.62 - (yy / h) * 0.18 + (value_noise(w, h, 9, seed=seed, octaves=2) - 0.5) * 0.25
    # tree trunks
    for k in range(13):
        tx = int(rng.integers(0, w))
        tw = int(rng.integers(1, 4))
        t = np.where((xx >= tx) & (xx < tx + tw) & (yy < h * 0.78), t - 0.38 - 0.1 * rng.random(), t)
    # ground: snow, lighter
    t = np.where(yy > h * 0.74, t + 0.22, t)
    # figures: dark coats, pale faces, hats
    n = 6
    for i in range(n):
        fx = int(w * (0.12 + 0.76 * i / (n - 1)) + rng.integers(-2, 3))
        fh = int(h * 0.46 + rng.integers(-2, 3))
        fy = int(h * 0.80) - fh
        body = (np.abs(xx - fx) <= 3 + (yy - fy) // 9) & (yy >= fy + 5) & (yy < fy + fh)
        head = ((xx - fx) ** 2 + (yy - (fy + 3)) ** 2) <= 4
        hat = (np.abs(xx - fx) <= 3) & (yy >= fy - 1) & (yy <= fy + 1)
        t = np.where(body | hat, 0.10, t)
        t = np.where(head & ~hat, 0.72, t)
    m = full(h, w)
    tone(L, m, x, y, np.clip(t, 0, 1), [NI[1], ST[1], ST[3], SN[1], SN[2]], dither=True)
    L.rect(x - 1, y - 1, w + 2, 1, NI[1]); L.rect(x - 1, y + h, w + 2, 1, NI[1])
    L.rect(x - 1, y, 1, h, NI[1]); L.rect(x + w, y, 1, h, NI[1])


def img_newspaper(hist: bool) -> Layer:
    name = 'newspaper'
    rng = rng_of(name)
    L = Layer(W, H)
    # bench slats (painted teal timber) under the paper, snow in the gaps
    wood_planks_h(L, 0, 0, W, H, [TE[0], TE[1], TE[2], TE[3], TE[4]], plank=19, seed=seed_of('np.bench'),
                  base=0.5, var=0.12)
    for gy in range(18, H, 19):
        L.rect(0, gy, W, 2, NI[1])
    # the paper: slightly rotated look via a stepped top edge, folded corner bottom-right
    px0, py0, px1, py1 = 18, 8, 238, 154
    yy, xx = np.mgrid[0:H, 0:W]
    paper = (xx >= px0) & (xx < px1) & (yy >= py0 + (xx - px0) // 70) & (yy < py1 - (px1 - xx) // 90)
    fold = (xx + yy > px1 + py1 - 26)
    paper_main = paper & ~fold
    pt = 0.72 + (value_noise(W, H, 14, seed=seed_of('np.paper'), octaves=2) - 0.5) * 0.12 - (xx / W) * 0.08
    tone(L, paper_main, 0, 0, band(pt, 3, 0.4), [SN[1], SK[4], SN[2], SK[5]])
    # the folded corner (paper back, darker) + its shadow
    corner = paper & fold & (xx + yy <= px1 + py1 - 4)
    tone(L, corner, 0, 0, 0.45, [SN[0], SK[2], SN[1]])
    put(L, edge_mask(corner, 'l') | edge_mask(corner, 't'), SN[3])
    # wet margin (snow melted into the paper): darker, crinkled band along the right/bottom edge
    wet = paper_main & ((xx > px1 - 18 + (np.sin(yy * 0.35) * 3).astype(int)) | (yy > py1 - 12 + (np.sin(xx * 0.3) * 2).astype(int)))
    shift(L, wet, -1)
    shift(L, wet & dither_mask(np.full((H, W), 0.4)), -1)
    ink, red = NI[1], RED[2]
    # running head of page 3: emblem, title, number, date
    hx = px0 + 8
    if hist:
        m = hammer_sickle_mask(13)
        for yv, xv in zip(*np.nonzero(m)):
            L.px(hx + xv, py0 + 6 + yv, red)
    else:
        cog, ear = gear_wheat_masks(13)
        for yv, xv in zip(*np.nonzero(cog & ~ear)):
            L.px(hx + xv, py0 + 6 + yv, red)
        for yv, xv in zip(*np.nonzero(outline_mask(ear) & cog)):
            L.px(hx + xv, py0 + 6 + yv, SK[5])
        for yv, xv in zip(*np.nonzero(ear)):
            L.px(hx + xv, py0 + 6 + yv, red)
    tx = hx + 19
    draw_text(L, tx, py0 + 8, 'КАРСКАЯ', ink, F57, spacing=2)
    draw_text(L, tx + text_w('КАРСКАЯ', F57, 2) + 7, py0 + 8, 'ПРАВДА', ink, F57, spacing=2)
    L.rect(tx, py0 + 15, text_w('КАРСКАЯ ПРАВДА', F57, 2) + 4, 1, SN[1])
    draw_text(L, px1 - 22, py0 + 5, '3', ink, F57, spacing=1, scale=2)
    draw_text(L, tx, py0 + 18, '№ 18', ink, F35)
    pseudo_print(L, tx + 18, py0 + 18, 62, ink, rng, wear=0.1)
    draw_text(L, tx + 86, py0 + 18, '1964', ink, F35)
    L.rect(px0 + 6, py0 + 25, px1 - px0 - 14, 1, ink)
    L.rect(px0 + 6, py0 + 27, px1 - px0 - 14, 1, ink)
    # headline (bold pseudo letters, 2 lines) across the page
    for i, (lx, lw) in enumerate(((px0 + 10, 186), (px0 + 30, 140))):
        cx = lx
        while cx < lx + lw:
            gw = int(rng.integers(3, 6))
            L.rect(cx, py0 + 32 + i * 9, gw, 6, ink)
            L.px(cx + int(rng.integers(0, gw)), py0 + 32 + i * 9 + int(rng.integers(1, 5)), SK[5])
            cx += gw + (5 if rng.random() < 0.2 else 2)
    # the photo (same every year) + caption
    halftone_photo(L, px0 + 10, py0 + 54, 92, 58, seed_of('np.photo'))
    for r in range(3):
        pseudo_print(L, px0 + 10, py0 + 116 + r * 5, 92 - r * 20, ink, rng, wear=0.05)
    # text columns
    for col_x, col_w, y_a in ((px0 + 110, 50, py0 + 54), (px0 + 166, 46, py0 + 54)):
        for r in range(17):
            yv = y_a + r * 5
            if yv > py1 - 16:
                break
            ln = col_w - (int(rng.integers(4, 18)) if r % 6 == 5 else 0)
            pseudo_print(L, col_x, yv, ln, ink, rng, wear=0.12)
    L.rect(px0 + 106, py0 + 52, 1, 90, SN[1])
    L.rect(px0 + 162, py0 + 52, 1, 90, SN[1])
    # round stamp of the depot library (blue-green ink, slightly faint), over the column top
    scx, scy = px0 + 190, py0 + 62
    d = np.hypot(xx + 0.5 - scx, yy + 0.5 - scy)
    ring = ((d >= 10.0) & (d < 11.2)) | ((d >= 7.6) & (d < 8.4))
    stamp_ink = TE[2]
    put(L, ring & dither_mask(np.full((H, W), 0.8)), stamp_ink)
    for k in range(18):
        a = k / 18 * 2 * math.pi
        if k % 3:
            L.px(int(scx + math.cos(a) * 9.2), int(scy + math.sin(a) * 9.2), stamp_ink)
    draw_text(L, int(scx) - 7, int(scy) - 2, 'ДЕПО', stamp_ink, F35, spacing=0)
    # snow: flakes resting on the paper + a little drift at the top-left
    for _ in range(40):
        fx = int(rng.integers(px0, px1)); fy = int(rng.integers(py0, py1))
        if paper[fy, fx]:
            L.px(fx, fy, SN[4])
            if rng.random() < 0.3:
                L.px(fx + 1, fy, SN[3])
    light_pool(L, W * 0.2, -40, 220, 140, steps=1, power=1.4, where=paper_main)
    light_pool(L, W, H + 30, 160, 90, steps=-1, power=1.2)
    flakes(L, 14, seed_of('np.flakes'))
    vignette(L, 0.8)
    frame(L)
    return L


# =========================================================================== 3. cat (easter egg)
def corrugated_v(L: Layer, x, y, w, h, ramp, period=4, base=0.45, seed=0):
    """Corrugated sheet metal: vertical ridges (lit left flank, dark right flank)."""
    yy, xx = np.mgrid[0:h, 0:w]
    ph = (xx % period) / period
    t = base + np.where(ph < 0.5, 0.18, -0.12) + (value_noise(w, h, 8, seed=seed, octaves=2) - 0.5) * 0.15
    tone(L, full(h, w), x, y, band(t, len(ramp), 0.2), ramp)


def podstakannik(L: Layer, x, y):
    """Tea glass in a metal holder (podstakannik), ~21x33, top-left at (x, y). Tea amber, holder pewter."""
    for r in range(8):
        L.rect(x + 2, y + r, 14, 1, SK[3] if r > 1 else SK[4])
    L.rect(x + 3, y + 2, 12, 6, CO[1])
    L.rect(x + 3, y + 2, 12, 1, CO[2])
    L.rect(x + 4, y + 3, 2, 4, CO[2])
    L.px(x + 13, y + 3, CO[3])
    L.rect(x + 2, y, 1, 9, SN[3])
    L.rect(x + 15, y, 1, 9, SK[1])
    L.rect(x + 1, y + 8, 16, 18, ST[2])
    L.rect(x + 1, y + 8, 16, 1, ST[4])
    L.rect(x + 2, y + 9, 2, 16, ST[4])
    L.rect(x + 14, y + 9, 2, 16, ST[1])
    for k in range(3):
        L.px(x + 6 + k * 3, y + 15, ST[4])
        L.px(x + 7 + k * 3, y + 16, ST[1])
    L.rect(x + 4, y + 18, 10, 1, ST[1])
    L.rect(x + 4, y + 11, 10, 1, ST[3])
    L.rect(x, y + 25, 18, 2, ST[1])
    L.rect(x, y + 25, 18, 1, ST[3])
    L.rect(x + 17, y + 11, 3, 2, ST[3])
    L.rect(x + 19, y + 12, 2, 9, ST[2])
    L.rect(x + 17, y + 20, 3, 2, ST[1])
    L.rect(x + 11, y - 6, 1, 9, ST[4])
    L.px(x + 12, y - 6, ST[2])


def _metal_px(nx, band_row=False):
    """Brass/copper cylinder shading for a normalised x across the body (-1 left .. 1 right)."""
    if abs(nx) > 0.86:
        return CO[0]
    spec = math.exp(-((nx + 0.42) / 0.13) ** 2)
    lam = 0.38 - 0.28 * nx + 0.9 * spec
    if band_row:
        lam -= 0.3
    idx = 0 if lam < 0.18 else 1 if lam < 0.5 else 2 if lam < 0.78 else 3 if lam < 1.05 else 4
    return CO[idx]


def samovar(L: Layer, x, y):
    """Brass samovar ~46x70: porcelain teapot on the crown, banded vase body, wooden handles, spigot, tray."""
    cx = x + 22
    top = y + 22
    # body profile (half widths per row)
    for r in range(42):
        f = r / 41
        hw = 12 + 7 * math.sin(math.pi * min(1.0, 0.15 + f * 0.95)) - 3.5 * f * f
        band_row = r in (6, 7, 30, 31)
        for dx in range(-int(hw), int(hw) + 1):
            L.px(cx + dx, top + r, _metal_px(dx / hw, band_row))
        L.px(cx - int(hw) - 1, top + r, NI[1])
        L.px(cx + int(hw) + 1, top + r, NI[1])
    # shoulder ring + crown (konforka) + porcelain teapot with a small red flower
    L.rect(cx - 10, top - 3, 21, 3, CO[1]); L.rect(cx - 10, top - 3, 21, 1, CO[3]); L.rect(cx - 10, top - 1, 21, 1, CO[0])
    L.rect(cx - 6, top - 7, 13, 4, CO[0]); L.rect(cx - 5, top - 7, 4, 4, CO[2])
    for r in range(11):
        hw = 8 - abs(r - 6) * 0.75
        for dx in range(-int(hw), int(hw) + 1):
            nx = dx / max(1, hw)
            L.px(cx + dx, top - 18 + r, SN[4] if nx < -0.3 else SN[3] if nx < 0.4 else SN[1])
    L.rect(cx - 7, top - 18, 15, 1, SN[2])
    L.rect(cx - 2, top - 21, 5, 3, SN[2]); L.px(cx - 1, top - 21, SN[4])
    L.px(cx + 1, top - 13, RED[2]); L.px(cx, top - 12, RED[3]); L.px(cx + 2, top - 12, RED[2]); L.px(cx + 1, top - 11, SA[2])
    L.rect(cx + 8, top - 14, 4, 2, SN[2]); L.px(cx + 12, top - 15, SN[2])
    L.rect(cx - 11, top - 15, 3, 5, SN[1])
    # wooden handles at the shoulders
    for side in (-1, 1):
        hx_ = cx + side * 20
        L.rect(min(hx_, hx_ + side * 2), top + 3, 3, 2, CO[0])
        L.rect(hx_ + side * 2, top + 4, 2, 10, WO[1]); L.px(hx_ + side * 2, top + 4, WO[3])
        L.rect(min(hx_, hx_ + side * 2), top + 13, 3, 2, CO[0])
    # spigot with dark wooden key
    L.rect(cx - 3, top + 33, 7, 3, CO[2]); L.rect(cx - 3, top + 33, 7, 1, CO[4])
    L.rect(cx - 1, top + 36, 3, 4, CO[1]); L.px(cx, top + 40, CO[0])
    L.rect(cx - 5, top + 30, 3, 3, WO[1]); L.px(cx - 5, top + 30, WO[3])
    # base and tray
    L.rect(cx - 9, top + 42, 19, 3, CO[1]); L.rect(cx - 9, top + 42, 19, 1, CO[3])
    L.rect(cx - 14, top + 45, 29, 3, CO[0]); L.rect(cx - 14, top + 45, 29, 1, CO[2])


def cat_shape(L: Layer, x, y, seed, ramp=None, awake=False, warm_side='left'):
    """A round tabby curled up (loaf), ~74x50; ginger or grey ramp; awake = head raised, eyes half open.
    Lit warm from `warm_side` (fire / samovar), cold sky rim on the other side."""
    ramp = ramp or [NI[2], ST[1], ST[2], ST[3], ST[4], ST[5]]
    w, h = 74, 50
    C = Layer(w, h)
    hy = 15 if awake else 20
    lx = -0.75 if warm_side == 'left' else 0.75
    mb, tb = sphere_t(w, h, 38, 32, 30, 17, light=(lx, -0.55, 0.45))
    mh, th = sphere_t(w, h, 20, hy, 15, 13, light=(lx, -0.55, 0.5))
    ear_l = poly_mask([(8, hy - 8), (11, hy - 19), (18, hy - 11)], w, h)
    ear_r = poly_mask([(22, hy - 12), (29, hy - 20), (32, hy - 8)], w, h)
    m = mb | mh | ear_l | ear_r
    t = np.where(mh, th, tb)
    t = np.where(ear_l | ear_r, 0.55, t)
    yy, xx = np.mgrid[0:h, 0:w]
    stripes = (np.sin((xx * 0.42 + np.sin(yy * 0.25) * 2.2)) > 0.55) & mb & ~mh
    stripes |= (np.sin(xx * 0.9 + yy * 0.15) > 0.7) & mh & (yy < hy - 2)
    t = np.where(stripes, t - 0.22, t)
    tone(C, m, 0, 0, band(t, len(ramp), 0.35), ramp)
    mz, _ = sphere_t(w, h, 17, hy + 5, 6, 4)
    put(C, mz, SN[2])
    chest = (ellipse_full(28, 36, 5, 7, w, h) | ellipse_full(31, 41, 6, 4, w, h)) & mb & ~mh
    tone(C, chest, 0, 0, band(np.clip(0.75 - (yy - 22) / 20.0, 0, 1), 3, 0.4), [SN[1], SN[2], SN[3]])
    C.px(16, hy + 3, RU[4]); C.px(17, hy + 3, RU[4]); C.px(16, hy + 4, RU[3])
    for ex_ in (11, 21):
        if awake:      # half-open eyes: amber slit with dark pupil and a lid line
            C.px(ex_, hy - 2, NI[1]); C.px(ex_ + 1, hy - 2, NI[1]); C.px(ex_ + 2, hy - 2, NI[1]); C.px(ex_ + 3, hy - 2, NI[1])
            C.px(ex_, hy - 1, CO[2]); C.px(ex_ + 1, hy - 1, NI[0]); C.px(ex_ + 2, hy - 1, CO[3]); C.px(ex_ + 3, hy - 1, CO[2])
        else:
            C.px(ex_, hy - 2, NI[1]); C.px(ex_ + 1, hy - 1, NI[1]); C.px(ex_ + 2, hy - 1, NI[1]); C.px(ex_ + 3, hy - 2, NI[1])
    C.line(15, hy + 6, 7, hy + 5, SN[3])
    C.line(15, hy + 7, 7, hy + 8, SN[3])
    C.line(19, hy + 6, 27, hy + 5, SN[3])
    for (ax, ay) in ((11, hy - 13), (12, hy - 14), (27, hy - 14), (28, hy - 15)):
        C.px(ax, ay, RU[4])
    for px_ in (14, 24):
        C.rect(px_, 44, 7, 3, ramp[4]); C.rect(px_, 44, 7, 1, ramp[5])
        C.px(px_ + 2, 46, ramp[2]); C.px(px_ + 4, 46, ramp[2])
    for i in range(30):
        tx_ = 40 + i
        ty_ = 46 - int(4 * math.sin(i / 29 * math.pi))
        C.rect(tx_, ty_, 1, 3, ramp[3] if (i // 4) % 2 == 0 else ramp[1])
    alpha = C.c[..., 3] > 0
    for yv, xv in zip(*np.nonzero(outline_mask(alpha))):
        C.px(xv, yv, NI[1])
    warm = edge_mask(alpha, 'l' if warm_side == 'left' else 'r')
    cold = edge_mask(alpha, 'r' if warm_side == 'left' else 'l') | (edge_mask(alpha, 't') & (xx > 40))
    for yv, xv in zip(*np.nonzero(warm)):
        C.px(xv, yv, CO[3] if yv < 40 else CO[2])
    for yv, xv in zip(*np.nonzero(cold & ~warm)):
        C.px(xv, yv, SK[3])
    L.blit(C, x, y)


def img_cat() -> Layer:
    """Ginger cat curled beside the fire barrel (exp_cat): warm firelight left, cold snow light right."""
    L = Layer(W, H)
    yy, xx = np.mgrid[0:H, 0:W]
    # dark yard behind: the wagon's planks in shadow and the canopy edge
    wood_planks_v(L, 0, 0, W, 96, [NI[1], NI[3], RU[0], RU[1]], plank=14, seed=seed_of('cat.wagon'), base=0.3, var=0.08)
    L.rect(0, 60, W, 5, NI[1]); L.rect(0, 60, W, 1, ST[2])
    # snowy platform with slush, trampled near the barrel
    t = 0.55 + (value_noise(W, H, 12, seed=seed_of('cat.snow'), octaves=2) - 0.5) * 0.25 - (yy - 96) / 160.0
    tone(L, yy >= 96, 0, 0, band(t, 4, 0.35), [ST[2], SN[0], SN[1], SN[2]])
    L.rect(0, 96, W, 1, SN[2])
    # the workers' felt boots and coat hems at the edges of the frame (they stand at the barrel)
    for (bx, coat) in ((60, TE[1]), (214, WO[1])):
        L.rect(bx, 0, 30, 58, coat); L.rect(bx, 57, 30, 2, NI[1])
        L.rect(bx + 4, 59, 9, 34, NI[2]); L.rect(bx + 17, 59, 9, 34, NI[2])
        L.rect(bx + 2, 88, 13, 8, ST[1]); L.rect(bx + 15, 88, 13, 8, ST[1])
        L.rect(bx + 2, 88, 13, 1, ST[3]); L.rect(bx + 15, 88, 13, 1, ST[3])
        L.rect(bx + 4, 59, 1, 29, ST[2] if bx < 128 else WO[3])
    fire_barrel_closeup(L, 118, 44, 58, 84)
    # a scrap of sacking on the snow as the cat's bed
    bed = ellipse_full(196, 140, 44, 10)
    tone(L, bed, 0, 0, 0.5 + ((xx % 3) == 0) * 0.1, [WO[1], WO[2], WO[3]])
    cat_shape(L, 160, 96, seed_of('cat.cat'), ramp=[RU[0], RU[1], RU[2], RU[3], RU[4], CO[2]], awake=True,
              warm_side='left')
    # firelight: warm pool around the barrel, snow lit orange
    light_pool(L, 147, 100, 120, 70, steps=1, power=0.7)
    light_pool(L, 147, 120, 70, 40, steps=1, power=0.8)
    light_pool(L, W + 10, 20, 90, 120, steps=-1, power=1.1)
    flakes(L, 22, seed_of('cat.flakes'))
    vignette(L, 0.85)
    frame(L)
    return L


# =========================================================================== shared outdoor backdrop
def dawn_sky(L: Layer, y0=0, y1=110, seed=0):
    """Karsk dawn sky: dark teal at the top to pale sage at the horizon, banded with soft dither."""
    h = y1 - y0
    yy, xx = np.mgrid[0:h, 0:L.w]
    t = (yy / max(1, h - 1)) ** 0.9 + (value_noise(L.w, h, 22, seed=seed, octaves=2) - 0.5) * 0.12
    tone(L, full(h, L.w), 0, y0, band(t, 6, 0.5), [TE[3], TE[4], SK[0], SK[1], SK[2], SK[3]])


def silhouette_yard(L: Layer, base_y, seed, cols=(SK[0], TE[4])):
    """Far yard silhouettes (blocks, chimneys, a crane) in haze colours."""
    rng = np.random.default_rng(seed)
    x = -5
    while x < L.w:
        bw = int(rng.integers(14, 40))
        bh = int(rng.integers(10, 34))
        L.rect(x, base_y - bh, bw, bh, cols[0])
        if rng.random() < 0.5:
            for wy in range(base_y - bh + 3, base_y - 2, 5):
                for wx in range(x + 2, x + bw - 2, 5):
                    if rng.random() < 0.6:
                        L.px(wx, wy, cols[1])
        if rng.random() < 0.25:
            cx = x + bw // 2
            L.rect(cx, base_y - bh - 18, 3, 18, cols[0])
        x += bw + int(rng.integers(0, 8))


# =========================================================================== 4. snowman (easter egg)
def img_snowman() -> Layer:
    """Kids' snowman with a tin-can ushanka, a sled beside it, small footprints (exp_snowman)."""
    L = Layer(W, H)
    dawn_sky(L, 0, 104, seed=seed_of('sm.sky'))
    silhouette_yard(L, 98, seed_of('sm.yard'), (SK[1], SK[2]))
    L.rect(0, 94, W, 10, SK[2])
    L.rect(206, 24, 3, 82, TE[1]); L.rect(200, 24, 14, 3, TE[1]); L.rect(201, 27, 12, 2, SN[3])
    for i in range(W):
        L.px(i, 16 + int(6 * math.sin(i / W * math.pi)), NI[3])
    yy, xx = np.mgrid[0:H, 0:W]
    g = yy >= 102
    t = 0.62 - (yy - 102) / 60.0 * 0.35 + (value_noise(W, H, 18, seed=seed_of('sm.snow'), octaves=2) - 0.5) * 0.18
    tone(L, g, 0, 0, band(t, 4, 0.3), [ST[3], SN[0], SN[1], SN[2]])
    L.rect(0, 102, W, 1, SN[2])
    # child footprints circling the snowman
    for k in range(9):
        a = k / 9 * 2 * math.pi
        fx, fy = int(122 + math.cos(a) * 62), int(140 + math.sin(a) * 12)
        L.rect(fx, fy, 4, 2, ST[3]); L.px(fx + 1, fy + 1, ST[2])
    # two balls, lit from the back right (dawn) and the sky above
    balls = [(122, 118, 30, 24), (122, 74, 21, 19)]
    body = np.zeros((H, W), bool)
    tsum = np.zeros((H, W))
    for (cx, cy, rx, ry) in balls:
        m, tb = sphere_t(W, H, cx, cy, rx, ry, light=(0.45, -0.75, 0.45), rim=0.25)
        tsum = np.where(m & ~body, tb, tsum)
        body |= m
    tone(L, body, 0, 0, band(tsum * 0.9 + 0.08, 5, 0.35), [SN[0], SN[1], SN[2], SN[3], SN[4]])
    put(L, outline_mask(body) & (yy < 140), SN[0])
    put(L, edge_mask(body, 'r'), CO[4])
    sh = ellipse_full(126, 142, 38, 5) & ~body
    shift(L, sh & dither_mask(np.full((H, W), 0.7)), -1)
    # tin-can ushanka: a label-wrapped can, tilted, with bent tin ear flaps
    can = poly_mask([(106, 52), (138, 46), (134, 26), (104, 32)])
    ct = 0.5 + (xx - 104) / 70.0
    tone(L, can, 0, 0, band(ct, 4, 0.3), [ST[1], ST[2], ST[3], ST[4]])
    lab = can & (yy - (52 - (xx - 106) * 6 // 32) <= -6) & (yy - (52 - (xx - 106) * 6 // 32) >= -15)
    tone(L, lab, 0, 0, 0.5 + (xx - 104) / 80.0, [RU[1], RU[2], RU[3]])
    for k in range(3):
        L.px(112 + k * 7, 41 - k, SN[3]); L.px(113 + k * 7, 41 - k, SN[3])
    put(L, edge_mask(can, 't'), ST[5]); put(L, edge_mask(can, 'b'), ST[0])
    for (ex0, ey0, sgn) in ((102, 52, -1), (138, 46, 1)):
        for j in range(9):
            L.px(ex0 + sgn * (j // 4), ey0 + j, ST[3] if j % 3 else ST[4])
            L.px(ex0 + sgn * (j // 4) + sgn, ey0 + j, ST[1])
    # coal eyes, bolt nose, gravel smile
    for ex_ in (114, 127):
        L.rect(ex_, 66, 2, 2, NI[0]); L.px(ex_, 66, ST[3])
    L.rect(120, 70, 4, 5, ST[3]); L.rect(120, 70, 4, 1, ST[5]); L.rect(120, 74, 4, 1, ST[1])
    for k in range(7):
        L.px(124 + k, 72, ST[4] if k % 2 == 0 else ST[2])
        L.px(124 + k, 73, ST[2] if k % 2 == 0 else ST[1])
    for (mx, my) in ((113, 79), (116, 81), (120, 82), (124, 82), (128, 81), (131, 79)):
        L.px(mx, my, NI[1])
    for by in (106, 116, 126):
        L.rect(120, by, 4, 3, ST[2]); L.px(121, by + 1, NI[1]); L.px(120, by, ST[4])
    # stick arms: one saluting up to the can, one out to the side
    pts = [(103, 96), (90, 84), (96, 64), (104, 52)]
    for a, b in zip(pts[:-1], pts[1:]):
        thick_line(L, a[0], a[1], b[0], b[1], WO[1], 2)
    L.line(91, 83, 86, 79, WO[2]); L.line(97, 65, 93, 61, WO[2])
    for a, b in zip([(141, 96), (158, 102)], [(158, 102), (172, 112)]):
        thick_line(L, a[0], a[1], b[0], b[1], WO[1], 2)
    L.line(162, 104, 167, 101, WO[2]); L.line(172, 112, 176, 111, WO[2])
    # the sled: wooden slats on curved runners, a rope
    for k in range(4):
        L.rect(26, 120 + k * 4, 46, 3, WO[3] if k % 2 else WO[4]); L.rect(26, 122 + k * 4, 46, 1, WO[1])
    for rx_ in (30, 64):
        L.rect(rx_, 120, 3, 18, TE[2])
    for i in range(52):
        L.px(22 + i, 138, TE[3]); L.px(22 + i, 139, TE[1])
    L.px(21, 137, TE[3]); L.px(20, 136, TE[3]); L.px(74, 137, TE[3])
    for i in range(16):
        L.px(22 - i // 2, 136 - i, RU[3] if i % 2 else RU[2])
    snow_on_top(L, (xx >= 26) & (xx < 72) & (yy >= 120) & (yy < 123), depth=1, seed=8)
    flakes(L, 40, seed_of('sm.flakes'), (1, 1, W - 1, 104))
    vignette(L, 0.75)
    frame(L)
    return L


# =========================================================================== 5. stash: music on ribs (secret)
def img_stash() -> Layer:
    L = Layer(W, H)
    yy, xx = np.mgrid[0:H, 0:W]
    # cinder ground with snow patches, the lifted concrete slab at the top
    t = 0.32 + (value_noise(W, H, 6, seed=seed_of('st.ground'), octaves=3) - 0.5) * 0.35
    tone(L, full(H, W), 0, 0, band(t, 5, 0.3), [NI[1], NI[3], ST[0], ST[1], ST[2]])
    sn = value_noise(W, H, 14, seed=seed_of('st.snow'), octaves=3)
    snow = sn > 0.64
    tone(L, snow, 0, 0, band(np.clip((sn - 0.64) * 6, 0, 1), 3, 0.4), [ST[2], SN[0], SN[1]])
    slab = poly_mask([(0, 0), (150, 0), (138, 22), (0, 30)])
    tone(L, slab, 0, 0, 0.55 + (value_noise(W, H, 5, seed=3, octaves=2) - 0.5) * 0.3, [ST[1], ST[2], ST[3], ST[4]])
    put(L, edge_mask(slab, 'b'), ST[0]); put(L, outline_mask(slab) & (yy > 15), NI[0])
    snow_on_top(L, slab & (yy < 6), depth=1, seed=5)
    # the open tin box (rusty) and its lid leaning at the right
    tin = (xx >= 36) & (xx < 170) & (yy >= 40) & (yy < 150)
    tone(L, tin, 0, 0, 0.42 + (value_noise(W, H, 7, seed=7, octaves=2) - 0.5) * 0.4, [RU[0], RU[1], RU[2], RU[3]])
    inner = (xx >= 40) & (xx < 166) & (yy >= 44) & (yy < 146)
    tone(L, inner, 0, 0, 0.3 + (yy - 44) / 400.0, [NI[1], NI[2], RU[0]])
    put(L, edge_mask(tin, 't') | edge_mask(tin, 'l'), RU[4])
    put(L, edge_mask(tin, 'b') | edge_mask(tin, 'r'), RU[0])
    lid = poly_mask([(178, 36), (246, 46), (240, 152), (172, 142)])
    tone(L, lid, 0, 0, 0.35 + (value_noise(W, H, 6, seed=9, octaves=2) - 0.5) * 0.45 + (yy - 40) / 400.0,
         [RU[0], RU[1], RU[2], RU[3], RU[4]])
    put(L, outline_mask(lid), NI[0]); put(L, edge_mask(lid, 't') | edge_mask(lid, 'l'), CO[1])
    lab = poly_mask([(190, 80), (232, 86), (230, 108), (188, 102)])
    tone(L, lab, 0, 0, 0.5, [SK[2], SK[3], SN[1]])
    pseudo_print(L, 193, 89, 34, RU[1], np.random.default_rng(4), wear=0.3)
    pseudo_print(L, 193, 95, 28, RU[1], np.random.default_rng(5), wear=0.3)
    # the X-ray record: dark film disc with a ghost ribcage, grooves and a burnt centre hole
    cx, cy, R = 103, 95, 46
    d = np.hypot(xx + 0.5 - cx, yy + 0.5 - cy)
    disc = d <= R
    ft = 0.30 + 0.10 * ((np.floor(d) % 2) == 0) - 0.04 * ((np.floor(d) % 6) == 0)
    # ribcage: spine + curved ribs + clavicles (lighter = bone on the film)
    bone = np.zeros((H, W), bool)
    bone |= (np.abs(xx - cx) <= 2) & (yy > cy - 38) & (yy < cy + 38)
    for k in range(8):
        ry = cy - 30 + k * 8
        for side in (-1, 1):
            for s in range(36):
                px = cx + side * (4 + s)
                py = ry + int((s / 36.0) ** 1.6 * 14) - int(math.sin(s / 36.0 * math.pi) * 5)
                if 0 <= py < H:
                    bone[py, px] = True
                    if s < 28 and py + 1 < H:
                        bone[py + 1, px] = True
    for side in (-1, 1):
        for s in range(24):
            px = cx + side * (3 + s)
            py = cy - 36 + int(s * 0.25)
            bone[py, px] = True
    lungs = (ellipse_full(cx - 17, cy + 2, 14, 26) | ellipse_full(cx + 17, cy + 2, 14, 26))
    ft = np.where(lungs, ft - 0.08, ft)
    ft = np.where(bone, ft + 0.32, ft)
    # cold sheen: a curved highlight band across the grooves
    sheen = (np.abs(d - R * 0.70) < 3.0) & (xx < cx - 6) & (yy < cy + 4)
    ft = np.where(sheen, ft + 0.30, ft)
    sheen2 = (np.abs(d - R * 0.45) < 1.5) & (xx > cx + 8) & (yy > cy + 6)
    ft = np.where(sheen2, ft + 0.2, ft)
    tone(L, disc, 0, 0, np.clip(ft, 0, 1), [NI[0], NI[2], TE[0], TE[1], TE[2], SK[0], SK[1]])
    put(L, outline_mask(disc), NI[0]); put(L, edge_mask(disc, 't') & (xx < cx), TE[3])
    hole = d <= 3
    put(L, hole, NI[0]); put(L, (d > 3) & (d <= 4.5), RU[0])
    pseudo_hand(L, cx - 20, cy + 10, 34, SN[3], np.random.default_rng(11))
    # the paper sleeve under the disc (top-right corner peeking out)
    sleeve = poly_mask([(140, 46), (166, 46), (166, 92), (150, 70)]) & ~disc
    tone(L, sleeve, 0, 0, 0.55, [SK[2], SK[3], SK[4]])
    light_pool(L, 60, 60, 150, 110, steps=1, power=1.3)
    vignette(L, 0.95)
    frame(L)
    return L


# =========================================================================== 6. loudspeaker
def img_loudspeaker() -> Layer:
    """The PA mast (exp_loudspeaker): timber pole, crossarm, two flared horn loudspeakers, snow and ice."""
    L = Layer(W, H)
    dawn_sky(L, 0, H, seed=seed_of('ls.sky'))
    yy, xx = np.mgrid[0:H, 0:W]
    silhouette_yard(L, H - 6, seed_of('ls.yard'), (SK[0], SK[1]))
    # timber pole with metal bands, junction box, crossarm
    px0 = 122
    pole = (xx >= px0) & (xx < px0 + 12)
    tone(L, pole, 0, 0, 0.5 - (xx - px0) / 24.0 + (value_noise(W, H, 4, seed=2, octaves=2) - 0.5) * 0.2,
         [WO[0], WO[1], WO[2], WO[3]])
    put(L, edge_mask(pole, 'l'), WO[4]); put(L, edge_mask(pole, 'r'), NI[2])
    for by in (60, 104):
        L.rect(px0 - 1, by, 14, 3, ST[1]); L.rect(px0 - 1, by, 14, 1, ST[3])
    L.rect(px0 - 6, 72, 24, 22, TE[1]); L.rect(px0 - 6, 72, 24, 1, TE[3]); L.rect(px0 + 17, 72, 1, 22, NI[1])
    L.rect(px0 - 2, 80, 4, 4, NI[1]); L.px(px0 - 1, 81, ST[3])
    L.rect(70, 34, 116, 5, ST[1]); L.rect(70, 34, 116, 1, ST[3]); L.rect(70, 38, 116, 1, NI[1])
    snow_on_top(L, (xx >= 70) & (xx < 186) & (yy == 34), depth=2, seed=4)
    # two horns: one towards the platform (left, down), one towards the yard (right, down)
    hl = horn(L, 112, 42, 6.0, 40, 70, 20.0, flare=3.2)
    hr = horn(L, 146, 42, 6.0, 214, 66, 19.0, flare=3.2)
    for (mcx, mcy, rx, ry) in ((40, 70, 6, 20), (214, 66, 6, 19)):
        mouth = ellipse_full(mcx, mcy, rx, ry)
        put(L, mouth, NI[1])
        inner = ellipse_full(mcx + (2 if mcx < 128 else -2), mcy, rx - 3, ry - 4)
        tone(L, inner, 0, 0, 0.2 + (yy - mcy + ry) / 300.0, [NI[0], NI[1], NI[2]])
        rim_side = 'l' if mcx < 128 else 'r'
        put(L, edge_mask(mouth, rim_side), ST[4])
        put(L, edge_mask(mouth, 't'), SN[3])
        for k, ix in enumerate(range(mcx - 4, mcx + 6, 3)):
            for j in range(3 + (k * 5) % 6):
                L.px(ix, mcy + ry + 1 + j, SN[3] if j < 2 else SN[1])
    for m in (hl, hr):
        for yv, xv in zip(*np.nonzero(edge_mask(m, 't'))):
            L.px(xv, yv - 1, SN[3]); L.px(xv, yv, SN[4] if xv % 5 else SN[2])
        for yv, xv in zip(*np.nonzero(edge_mask(m, 'b'))):
            if (xv * 37 + yv * 11) % 23 == 0:
                for j in range(2 + (xv % 3)):
                    L.px(xv, yv + j, RU[2] if j % 2 else RU[1])
    # drivers at the pole + cables
    for dx_ in (108, 146):
        d = ellipse_full(dx_ + 2, 42, 6, 7)
        tone(L, d, 0, 0, 0.45 - (yy - 42) / 20.0, [NI[2], TE[1], ST[2]])
        put(L, outline_mask(d), NI[0])
    for i in range(70):
        L.px(px0 + 14 + i // 12, 44 + i, NI[1])
    flakes(L, 36, seed_of('ls.flakes'))
    vignette(L, 0.7)
    frame(L)
    return L


# =========================================================================== 7. mitten
def img_mitten() -> Layer:
    L = Layer(W, H)
    dawn_sky(L, 0, 96, seed=seed_of('mi.sky'))
    silhouette_yard(L, 92, seed_of('mi.yard'), (SK[1], SK[2]))
    yy, xx = np.mgrid[0:H, 0:W]
    ground = yy >= 92
    tone(L, ground, 0, 0, band(0.7 - (yy - 92) / 140.0, 4, 0.4), [SN[0], SN[1], SN[2], SN[3]])
    # chain-link fence behind the post: diamond mesh of thin wire
    mesh = (((xx + yy) % 9 == 0) | ((xx - yy) % 9 == 0)) & (yy > 30) & (yy < 140)
    put(L, mesh, TE[2])
    L.rect(0, 30, W, 2, TE[1])
    for fx in (24, 232):
        L.rect(fx, 26, 6, 120, ST[2]); L.rect(fx, 26, 2, 120, ST[3])
    # the concrete post in front (centre), chipped, rust streak from the old wire hooks
    px0, px1 = 104, 148
    post = (xx >= px0) & (xx < px1) & (yy >= 72)
    pt = 0.55 + (value_noise(W, H, 5, seed=seed_of('mi.post'), octaves=2) - 0.5) * 0.3 - (xx - px0) / 60.0
    tone(L, post, 0, 0, band(pt, 5, 0.35), [ST[1], ST[2], ST[3], ST[4], ST[5]])
    put(L, edge_mask(post, 'l'), ST[5]); put(L, edge_mask(post, 'r'), ST[0])
    for hy in (96, 124):
        L.rect(px1 - 6, hy, 6, 2, RU[1])
        for j in range(10):
            L.px(px1 - 4, hy + 2 + j, RU[2] if j % 3 else RU[3])
    # the red knitted mitten over the post top, thumb to the right, snow cap
    mit = (ellipse_full(126, 62, 27, 30) & (yy < 86)) | ((xx >= px0 - 2) & (xx < px1 + 2) & (yy >= 62) & (yy < 92))
    yy2, xx2 = np.mgrid[0:H, 0:W]
    ta = math.radians(-35)
    u = (xx2 + 0.5 - 154) * math.cos(ta) + (yy2 + 0.5 - 66) * math.sin(ta)
    v = -(xx2 + 0.5 - 154) * math.sin(ta) + (yy2 + 0.5 - 66) * math.cos(ta)
    thumb = (u / 11.0) ** 2 + (v / 6.5) ** 2 <= 1
    m = mit | thumb
    mt = 0.62 - (xx - 126) / 70.0 - (yy - 60) / 200.0
    tone(L, m, 0, 0, band(mt, 4, 0.3), RED)
    # knit texture: rows of small V stitches, a pale snowflake band, ribbed cuff
    knit = m & (((xx + (yy // 2)) % 3 == 0)) & (yy % 2 == 0)
    shift(L, knit, -1)
    band_y = (yy >= 70) & (yy < 76) & mit
    put(L, band_y, RED[1])
    for k in range(px0 + 2, px1, 6):
        L.px(k, 72, SN[3]); L.px(k + 1, 71, SN[3]); L.px(k + 1, 73, SN[3]); L.px(k + 2, 72, SN[3]); L.px(k + 1, 72, SN[4])
    cuff = (yy >= 84) & (yy < 92) & mit
    put(L, cuff & (xx % 2 == 0), RED[1]); put(L, cuff & (xx % 2 == 1), RED[2])
    put(L, outline_mask(m) & (yy > 40), RED[0])
    seam = outline_mask(thumb) & mit
    put(L, seam, RED[0])
    snow_cap = ellipse_full(124, 38, 22, 8) & ~ellipse_full(124, 46, 30, 8)
    tone(L, snow_cap | (ellipse_full(124, 38, 24, 7) & (yy < 40)), 0, 0, 0.8, [SN[2], SN[3], SN[4]])
    put(L, edge_mask(ellipse_full(124, 38, 24, 7), 'b') & (yy > 38), SN[1])
    flakes(L, 38, seed_of('mi.flakes'))
    vignette(L, 0.8)
    frame(L)
    return L


# =========================================================================== 8. kontora shelf (secret)
def binder(L: Layer, x, y, w, h, ramp, year, rng, label=True):
    """Upright lever-arch binder seen from the spine: worn cloth, label holder with a year, finger hole."""
    t = 0.5 + (value_noise(w, h, 4, seed=int(rng.integers(0, 1 << 30)), octaves=2) - 0.5) * 0.25
    tone(L, full(h, w), x, y, band(t, len(ramp), 0.3), ramp)
    L.rect(x, y, 1, h, ramp[-1])
    L.rect(x + w - 1, y, 1, h, ramp[0])
    L.rect(x, y, w, 1, ramp[-1])
    if label:
        lx, ly, lw = x + 2, y + 6, w - 4
        L.rect(lx, ly, lw, 11, SN[1]); L.rect(lx, ly, lw, 1, SN[3]); L.rect(lx, ly + 10, lw, 1, SK[1])
        tw = text_w(year, F35)
        draw_text(L, lx + (lw - tw) // 2, ly + 3, year, NI[1], F35)
    hx, hy = x + w // 2, y + h - 12
    L.rect(hx - 2, hy - 2, 5, 5, ramp[0]); L.rect(hx - 1, hy - 1, 3, 3, NI[1]); L.px(hx - 2, hy - 2, ramp[1])


def img_kontora_shelf() -> Layer:
    L = Layer(W, H)
    rng = rng_of('kontora_shelf')
    yy, xx = np.mgrid[0:H, 0:W]
    # plaster wall, lamp-lit from the upper left
    t = 0.45 + (value_noise(W, H, 12, seed=seed_of('ks.wall'), octaves=2) - 0.5) * 0.2
    tone(L, full(H, W), 0, 0, band(t, 4, 0.4), [TE[0], TE[1], TE[2], TE[3]])
    # shelf frame (two uprights) and three boards
    for sx in (4, 248):
        L.rect(sx, 0, 6, H, WO[1]); L.rect(sx, 0, 1, H, WO[3])
    boards = (44, 100, 154)
    for by in boards:
        L.rect(4, by, 250, 5, WO[2]); L.rect(4, by, 250, 1, WO[4]); L.rect(4, by + 4, 250, 1, WO[0])
        L.rect(4, by + 5, 250, 2, NI[1])
    # top tier: boxes and a ledger stack
    for i, (bx, bw, bh, ramp) in enumerate(((12, 40, 22, ST[1:5]), (56, 30, 30, WO[1:5]), (92, 52, 18, SA[0:4]),
                                            (150, 34, 26, ST[1:5]), (190, 54, 20, TE[1:5]))):
        tone(L, full(bh, bw), bx, 44 - bh, band(0.5 + (value_noise(bw, bh, 5, seed=i, octaves=1) - 0.5) * 0.3, 4, 0.3), ramp)
        L.rect(bx, 44 - bh, bw, 1, ramp[-1]); L.rect(bx + bw - 1, 44 - bh, 1, bh, ramp[0])
        if i % 2 == 0:
            L.rect(bx + 4, 44 - bh + 4, bw - 8, 6, SN[1]); pseudo_print(L, bx + 6, 44 - bh + 5, bw - 12, NI[2], rng, h=3)
    # middle tier: binders by year; 1939 missing (dust outline + label on the shelf edge)
    years = ['1934', '1935', '1936', '1937', '1938', None, '1940', '1941', '1946', '1947', '1948']
    ramps = [SA[0:4], WO[1:5], TE[1:5], ST[1:5], SA[1:5], None, WO[0:4], RU[1:5], ST[0:4], TE[0:4], SA[0:4]]
    x = 12
    gap = None
    for yr, rp in zip(years, ramps):
        bw = 20
        if yr is None:
            gap = (x, bw)
            x += bw + 1
            continue
        binder(L, x, 50, bw, 50, rp, yr, rng)
        x += bw + 1
    # dust on the shelf board, clean rectangle where the 1939 binder stood
    gx, gw = gap
    dust = (yy >= 100) & (yy < 102) & (xx >= 10) & (xx < 244)
    put(L, dust & dither_mask(np.full((H, W), 0.5)), ST[5])
    clean = (yy >= 100) & (yy < 102) & (xx >= gx) & (xx < gx + gw)
    put(L, clean, WO[2])
    shadow = (yy >= 50) & (yy < 100) & (xx >= gx) & (xx < gx + gw)
    tone(L, shadow, 0, 0, 0.25 + (yy - 50) / 300.0, [NI[1], NI[3], TE[0]])
    # dust line on the wall where the binder's top edge was
    L.rect(gx + 1, 50, gw - 2, 1, TE[3])
    # the label still glued to the shelf edge under the gap
    L.rect(gx - 2, 102, gw + 4, 9, SN[2]); L.rect(gx - 2, 102, gw + 4, 1, SN[4]); L.rect(gx - 2, 110, gw + 4, 1, SK[1])
    draw_text(L, gx + 3, 104, '1939', NI[1], F35)
    pseudo_hand(L, gx - 1, 109, gw + 2, RU[1], np.random.default_rng(3))
    # bottom tier: stamp + ink pad + more binders
    x = 12
    for i, rp in enumerate((ST[1:5], WO[1:5], SA[0:4], TE[1:5], ST[0:4], WO[0:4])):
        binder(L, x, 108 if i % 2 else 112, 18, 46 if i % 2 else 42, rp, str(1950 + i), rng, label=i % 2 == 0)
        x += 19
    L.rect(150, 144, 30, 10, NI[2]); L.rect(151, 145, 28, 7, TE[0]); L.rect(150, 144, 30, 1, ST[2])
    L.rect(192, 136, 8, 18, WO[3]); L.rect(192, 136, 8, 1, WO[4]); L.rect(189, 150, 14, 4, WO[1])
    L.rect(208, 128, 34, 26, ST[2]); L.rect(208, 128, 34, 1, ST[4]); pseudo_print(L, 212, 136, 26, NI[2], rng)
    # warm enamel lamp from the upper left, darkness to the right
    light_pool(L, 30, 10, 170, 120, steps=1, power=0.9)
    light_pool(L, W + 40, H, 170, 120, steps=-1, power=1.0)
    vignette(L, 0.85)
    frame(L)
    return L


# =========================================================================== 9. grain in the snow
def sparrow(L: Layer, x, y, facing=1, pecking=False):
    """Sparrow ~11x8 (brown streaked back, grey belly, dark cap and bib, tail up)."""
    f = facing
    rows = (["...##......", "..####.....", ".######..##", "#######.##.", ".#######...", "..#####....", "...#..#....", "...#..#...."]
            if not pecking else
            ["...........", "....##.....", "..#####..##", ".#######.#.", "###########", ".###.####..", "...#..#....", "...#..#...."])
    for r, row in enumerate(rows):
        for c, ch in enumerate(row):
            if ch != '#':
                continue
            px_ = x + (c if f > 0 else 10 - c)
            col = WO[3] if r < 3 else ST[3] if r < 6 else NI[2]
            if r < 3 and c in (3, 6):
                col = WO[1]
            L.px(px_, y + r, col)
    head_c = 1 if not pecking else 0
    hx = x + (1 if f > 0 else 9)
    L.px(hx, y + 1 + (3 if pecking else 0), NI[1])
    L.px(x + (0 if f > 0 else 10), y + 3 + (1 if pecking else 0), CO[2])
    return
    f = facing
    body = [(0, 2), (1, 1), (2, 1), (3, 1), (4, 2), (1, 2), (2, 2), (3, 2), (2, 3), (3, 3), (1, 3)]
    for (bx, by) in body:
        L.px(x + bx * f, y + by, WO[3])
    for (bx, by) in ((2, 3), (3, 3), (1, 3)):
        L.px(x + bx * f, y + by, ST[3])
    hx, hy = (5, 2) if pecking else (5, 0)
    L.px(x + hx * f, y + hy, WO[2]); L.px(x + (hx - 1) * f, y + hy, NI[2]); L.px(x + hx * f, y + hy + 1, WO[3])
    L.px(x + (hx + 1) * f, y + hy + (1 if pecking else 0), CO[2])
    L.px(x - 1 * f, y + 1, WO[1]); L.px(x - 2 * f, y, WO[1])
    L.px(x + 2 * f, y + 4, NI[2]); L.px(x + 3 * f, y + 4, NI[2])


def img_grain() -> Layer:
    """The grain elevator (exp_grain): five silos, a patched shell hole, a hopper wagon being loaded
    with Corridor grain; spilled grain and sparrows on the track bed."""
    L = Layer(W, H)
    rng = rng_of('grain')
    yy, xx = np.mgrid[0:H, 0:W]
    dawn_sky(L, 0, H, seed=seed_of('gr.sky'))
    # five silos (concrete cylinders with vertical shading bands), head house on top
    sx0 = 26
    for i in range(5):
        x0 = sx0 + i * 34
        nx = (xx - (x0 + 16)) / 16.0
        cyl = (np.abs(nx) <= 1) & (yy >= 30) & (yy < 118)
        t = 0.62 - 0.32 * nx - 0.1 * (nx > 0.6) + (value_noise(W, H, 6, seed=i, octaves=2) - 0.5) * 0.14
        t = t - ((yy - 30) / 300.0)
        tone(L, cyl, 0, 0, band(t, 5, 0.35), [ST[1], ST[2], ST[3], ST[4], ST[5]])
        for ry in range(40, 118, 12):
            L.rect(x0 + 1, ry, 31, 1, ST[1])
        put(L, edge_mask(cyl, 'r'), ST[0])
        top = ellipse_full(x0 + 16, 30, 16, 3)
        put(L, top & (yy <= 30), SN[3])
    # shell hole with a concrete patch (lighter, square-ish, with a rust stain) on silo 3
    hx, hy = sx0 + 2 * 34 + 7, 64
    patch = (xx >= hx) & (xx < hx + 16) & (yy >= hy) & (yy < hy + 14)
    tone(L, patch, 0, 0, 0.55 + (value_noise(W, H, 3, seed=9, octaves=1) - 0.5) * 0.3, [ST[3], ST[4], SK[1]])
    put(L, outline_mask(patch), ST[0])
    for k in range(10):
        a = k / 10 * 2 * math.pi
        L.px(int(hx + 8 + math.cos(a) * 11), int(hy + 7 + math.sin(a) * 9), ST[1])
    for j in range(14):
        L.px(hx + 4, hy + 14 + j, RU[2] if j % 3 else RU[1]); L.px(hx + 11, hy + 14 + j // 2, RU[2])
    # head house + conveyor gallery to the right
    L.rect(sx0 + 20, 8, 120, 22, ST[2]); L.rect(sx0 + 20, 8, 120, 1, ST[4]); L.rect(sx0 + 20, 29, 120, 1, ST[0])
    for wx in range(sx0 + 26, sx0 + 136, 10):
        L.rect(wx, 14, 5, 6, NI[2]); L.px(wx, 14, TE[2])
    snow_on_top(L, (xx >= sx0 + 20) & (xx < sx0 + 140) & (yy == 8), depth=2, seed=3)
    gal = poly_mask([(196, 22), (250, 40), (250, 46), (196, 28)])
    put(L, gal, ST[2]); put(L, edge_mask(gal, 't'), ST[4])
    # loading chute down to a hopper wagon stencilled КОРИДОР
    thick_line(L, 212, 34, 212, 96, ST[1], 3)
    L.rect(204, 96, 18, 6, ST[2])
    for i in range(20):
        L.px(212 + int(rng.integers(-2, 3)), 102 + i // 2, CO[2] if i % 2 else CO[3])
    wag = (xx >= 160) & (xx < 254) & (yy >= 106) & (yy < 140)
    tone(L, wag, 0, 0, 0.5 + (xx - 160) / 300.0, [RU[0], RU[1], RU[2], RU[3]])
    L.rect(160, 106, 94, 2, RU[4])
    for rx in range(166, 254, 14):
        L.rect(rx, 108, 1, 32, RU[0])
    draw_text(L, 172, 116, 'КОРИДОР', SN[3], F57, spacing=1, wear=0.06, rng=rng)
    draw_text(L, 216, 116, '3', SN[3], F57)
    for wx in (176, 230):
        L.rect(wx - 6, 140, 12, 6, NI[1]); L.rect(wx - 2, 142, 4, 2, ST[3])
    # track bed with snow; spilled grain and sparrows
    ground = yy >= 140
    tone(L, ground, 0, 0, band(0.5 + (value_noise(W, H, 10, seed=4, octaves=2) - 0.5) * 0.3, 4, 0.3),
         [NI[2], ST[1], SN[0], SN[1]])
    L.rect(0, 146, W, 2, ST[3]); L.rect(0, 146, W, 1, ST[5])
    grain_cols = [CO[1], CO[2], CO[3], WO[4]]
    for i in range(260):
        gx = int(212 + rng.normal(0, 22)); gy = int(150 + abs(rng.normal(0, 4)))
        if 0 < gx < W - 1 and 140 < gy < H - 1:
            L.px(gx, gy, grain_cols[int(rng.integers(0, 4))])
    sparrow(L, 150, 144, 1, pecking=True)
    sparrow(L, 236, 146, -1, pecking=True)
    sparrow(L, 120, 148, 1)
    # a queue of tiny figures in the far left foreground haze? no -- keep the silos as the subject
    light_pool(L, W, 0, 160, 120, steps=1, power=1.3)
    flakes(L, 30, seed_of('gr.flakes'))
    vignette(L, 0.8)
    frame(L)
    return L


# =========================================================================== 10. barrack
def img_barrack() -> Layer:
    L = Layer(W, H)
    rng = rng_of('barrack')
    yy, xx = np.mgrid[0:H, 0:W]
    # weathered clapboard wall
    wood_planks_h(L, 0, 0, W, H, [WO[0], WO[1], WO[2], WO[3], ST[3]], plank=8, seed=seed_of('ba.wall'), base=0.38,
                  var=0.1)
    # greyed weathering towards the bottom
    shift(L, (yy > 120) & dither_mask(np.clip((yy - 120) / 60.0, 0, 1) * np.ones((H, W))), -1)
    # door frame on the left, door boards (dark, patched)
    L.rect(14, 30, 70, H - 30, WO[0])
    wood_planks_v(L, 22, 40, 54, H - 40, [NI[2], WO[0], WO[1], WO[2]], plank=9, seed=seed_of('ba.door'), base=0.4)
    L.rect(14, 30, 8, H - 30, WO[2]); L.rect(76, 30, 8, H - 30, WO[2]); L.rect(14, 30, 70, 10, WO[2])
    L.rect(14, 30, 70, 1, WO[4]); L.rect(14, 30, 1, H - 30, WO[3])
    L.rect(66, 96, 6, 3, ST[3]); L.rect(66, 96, 6, 1, ST[5])
    # where the sign hung: a paler, unweathered rectangle with four screw holes + rust tears
    sx, sy, sw, sh = 22, 6, 54, 18
    sign = (xx >= sx) & (xx < sx + sw) & (yy >= sy) & (yy < sy + sh)
    shift(L, sign, 1)
    shift(L, sign & dither_mask(np.full((H, W), 0.5)), 1)
    put(L, edge_mask(sign, 'b'), WO[1])
    for (hx_, hy_) in ((sx + 3, sy + 3), (sx + sw - 4, sy + 3), (sx + 3, sy + sh - 4), (sx + sw - 4, sy + sh - 4)):
        L.px(hx_, hy_, NI[0]); L.px(hx_ + 1, hy_, NI[2]); L.px(hx_, hy_ + 1, RU[1])
        for j in range(2, 9 + (hx_ % 4)):
            L.px(hx_, hy_ + j, RU[2] if j % 3 else RU[1])
    # window on the right with a tin plate and a crooked stovepipe through it, frost on the glass
    wx, wy, ww, wh = 132, 34, 70, 64
    L.rect(wx - 4, wy - 4, ww + 8, wh + 8, WO[3]); L.rect(wx - 4, wy - 4, ww + 8, 1, WO[4])
    glass = (xx >= wx) & (xx < wx + ww) & (yy >= wy) & (yy < wy + wh)
    gt = 0.3 + (yy - wy) / 200.0 + (value_noise(W, H, 6, seed=5, octaves=2) - 0.5) * 0.15
    tone(L, glass, 0, 0, band(gt, 4, 0.3), [NI[2], TE[0], TE[1], TE[2]])
    edge_d = np.minimum.reduce([xx - wx, wx + ww - 1 - xx, yy - wy, wy + wh - 1 - yy]).astype(float)
    fn = value_noise(W, H, 3, seed=6, octaves=2)
    frost = glass & (edge_d + fn * 6 < 5)
    put(L, frost, SK[3])
    put(L, glass & (edge_d + fn * 6 >= 5) & (edge_d + fn * 6 < 6.5), SK[1])
    L.rect(wx + ww // 2 - 1, wy, 3, wh, WO[2]); L.rect(wx, wy + wh // 2 - 1, ww, 3, WO[2])
    tin = (xx >= wx + ww // 2 + 2) & (xx < wx + ww) & (yy >= wy) & (yy < wy + wh // 2 - 1)
    tone(L, tin, 0, 0, 0.45 + (xx - wx) / 300.0, [ST[1], ST[2], ST[3]])
    pipe_x, pipe_y = wx + ww * 3 // 4, wy + wh // 4
    L.rect(pipe_x - 5, pipe_y - 5, 11, 11, ST[1]); L.rect(pipe_x - 5, pipe_y - 5, 11, 1, ST[3])
    L.rect(pipe_x, pipe_y - 3, 34, 7, ST[2]); L.rect(pipe_x, pipe_y - 3, 34, 1, ST[4]); L.rect(pipe_x, pipe_y + 3, 34, 1, ST[0])
    for sx_ in (pipe_x + 12, pipe_x + 24):
        L.rect(sx_, pipe_y - 3, 1, 7, ST[0])
    L.rect(pipe_x + 30, pipe_y - 40, 7, 44, ST[2]); L.rect(pipe_x + 30, pipe_y - 40, 2, 44, ST[4])
    L.rect(pipe_x + 36, pipe_y - 40, 1, 44, ST[0])
    for j in range(0, 44, 4):
        if (j * 7) % 3 == 0:
            L.px(pipe_x + 33, pipe_y - 40 + j, RU[2])
    L.rect(pipe_x + 28, pipe_y - 43, 11, 3, ST[1]); L.rect(pipe_x + 28, pipe_y - 43, 11, 1, SN[3])
    for i in range(30):
        sx_ = pipe_x + 33 + int(3 * math.sin(i * 0.45)) + i // 4
        L.px(sx_, pipe_y - 45 - i, SK[3] if i % 3 else SK[4])
        if i % 2:
            L.px(sx_ + 1, pipe_y - 45 - i, SK[2])
    # sill with snow, icicles, frozen laundry line at the top right
    L.rect(wx - 6, wy + wh + 4, ww + 12, 4, WO[3]); L.rect(wx - 6, wy + wh + 4, ww + 12, 1, WO[4])
    for x in range(wx - 6, wx + ww + 6):
        d = 1 + ((x * 7) % 5 == 0)
        L.rect(x, wy + wh + 4 - d, 1, d, SN[4] if d == 1 else SN[3])
    for k, ix in enumerate(range(wx - 2, wx + ww + 2, 9)):
        for j in range(2 + (k * 3) % 5):
            L.px(ix, wy + wh + 8 + j, SN[3])
    light_pool(L, W, -30, 200, 120, steps=1, power=1.3)
    vignette(L, 0.85)
    flakes(L, 20, seed_of('ba.flakes'))
    frame(L)
    return L


# =========================================================================== 11. chalk on wagon 24-311
def chalk_line(L: Layer, pts, col, rng, wear=0.15):
    for a, b in zip(pts[:-1], pts[1:]):
        n = int(max(abs(b[0] - a[0]), abs(b[1] - a[1]))) + 1
        for i in range(n + 1):
            f = i / max(1, n)
            if rng.random() > wear:
                L.px(int(round(a[0] + (b[0] - a[0]) * f)), int(round(a[1] + (b[1] - a[1]) * f)), col)


def img_wagon_chalk() -> Layer:
    L = Layer(W, H)
    rng = rng_of('wagon_chalk')
    yy, xx = np.mgrid[0:H, 0:W]
    wood_planks_v(L, 0, 0, W, H, [RU[0], RU[1], RU[2], RU[3]], plank=15, seed=seed_of('wc.boards'), base=0.5,
                  var=0.12)
    # paint wear: lighter scuffs and bare grey wood
    scuff = (value_noise(W, H, 7, seed=seed_of('wc.scuff'), octaves=3) > 0.66)
    put(L, scuff & dither_mask(np.full((H, W), 0.6)), WO[3])
    # steel straps with rivets
    for sy_ in (18, 128):
        L.rect(0, sy_, W, 7, NI[3]); L.rect(0, sy_, W, 1, ST[3]); L.rect(0, sy_ + 6, W, 1, NI[1])
        for rx in range(6, W, 22):
            L.px(rx, sy_ + 3, ST[4]); L.px(rx + 1, sy_ + 3, ST[2]); L.px(rx, sy_ + 4, NI[1])
        for k in range(0, W, 3):
            if rng.random() < 0.3:
                for j in range(int(rng.integers(2, 7))):
                    L.px(k, sy_ + 7 + j, RU[2])
    # stencil 24-311 (white paint, chipped)
    draw_text(L, 18, 34, '24-311', SN[3], F57, spacing=2, scale=2, wear=0.12, rng=rng)
    draw_text(L, 20, 52, '20', SN[2], F35, wear=0.1, rng=rng)
    draw_text(L, 30, 52, 'Т', SN[2], F35, wear=0.1, rng=rng)
    # chalk layers, oldest (faint, washed) first, newest (bright) last
    old = SK[2]
    for k in range(5):
        chalk_line(L, [(150 + k * 5, 40), (150 + k * 5, 56)], old, rng, 0.45)
    chalk_line(L, [(146, 50), (178, 44)], old, rng, 0.45)
    draw_text(L, 110, 96, '7', old, F57, scale=2, wear=0.5, rng=rng)
    chalk_line(L, [(100, 70), (134, 70), (128, 66)], old, rng, 0.4)
    chalk_line(L, [(134, 70), (128, 74)], old, rng, 0.4)
    # the faint line at the very bottom, almost washed away: "40 ЧЕЛ."
    faint = Layer(W, H)
    draw_text(faint, 22, 140, '40 ЧЕЛ.', SK[3], F57, spacing=2)
    fm = (faint.c[..., 3] > 0) & dither_mask(np.full((H, W), 0.55))
    put(L, fm, SK[2])
    # newer chalk: circled number, ticks, a date, a scrawled route code
    nc = SN[3]
    draw_text(L, 196, 46, '20', nc, F57, scale=2, wear=0.08, rng=rng)
    pts = [(196 + int(16 * math.cos(a)) + 11, 52 + int(13 * math.sin(a)) + 2) for a in np.linspace(0, 2 * math.pi, 40)]
    chalk_line(L, pts, nc, rng, 0.12)
    for k, (cx_, cy_) in enumerate(((104, 40), (118, 44), (132, 40))):
        chalk_line(L, [(cx_, cy_), (cx_ + 3, cy_ + 4), (cx_ + 9, cy_ - 5)], SN[4] if k == 2 else nc, rng, 0.08)
    draw_text(L, 168, 96, '12.1', nc, F35, wear=0.1, rng=rng)
    pseudo_hand(L, 160, 108, 70, nc, rng)
    chalk_line(L, [(70, 104), (96, 98), (90, 95)], nc, rng, 0.1)
    chalk_line(L, [(96, 98), (91, 102)], nc, rng, 0.1)
    # a cross-out over an older number
    draw_text(L, 60, 76, '17', old, F57, scale=2, wear=0.4, rng=rng)
    chalk_line(L, [(56, 92), (90, 74)], nc, rng, 0.1)
    light_pool(L, W, -20, 200, 140, steps=1, power=1.4)
    light_pool(L, 0, H, 160, 90, steps=-1, power=1.3)
    vignette(L, 0.8)
    frame(L)
    return L


# =========================================================================== 12. chess under the stair (easter egg)
_PIECES = {
    'p': ["..#..", ".###.", "..#..", ".###."],
    'r': ["#.#.#", "#####", ".###.", ".###.", "#####"],
    'n': [".##..", "####.", ".###.", "..##.", ".###.", "#####"],
    'b': ["..#..", ".###.", ".#.#.", ".###.", "..#..", "#####"],
    'q': ["#.#.#", ".###.", "..#..", ".###.", ".###.", "#####"],
    'k': ["..#..", ".###.", "..#..", ".###.", ".###.", "#####"],
}


def chess_piece(L: Layer, x, y, kind, white):
    g = _PIECES[kind]
    h = len(g)
    for r, row in enumerate(g):
        for c, ch in enumerate(row):
            if ch == '#':
                if white:
                    col = SN[4] if c < 2 else SN[3] if c < 4 else SN[1]
                else:
                    col = ST[2] if c < 2 else NI[3] if c < 4 else NI[1]
                L.px(x + c, y - h + 1 + r, col)


def img_stairs_under() -> Layer:
    """Cache under the signal-box stair (exp_stairs_under): loose bricks pulled out of the foundation,
    an oilcloth bundle with a red rag, inside a pegged travel chess set mid-game."""
    L = Layer(W, H)
    rng = rng_of('stairs_under')
    yy, xx = np.mgrid[0:H, 0:W]
    t = 0.35 + (value_noise(W, H, 6, seed=1, octaves=2) - 0.5) * 0.2
    tone(L, full(H, W), 0, 0, band(t, 3, 0.3), [RU[0], RU[1], RU[2]])
    for by in range(0, 112, 5):
        L.rect(0, by, W, 1, NI[2])
        off = 0 if (by // 5) % 2 == 0 else 6
        for bx in range(off, W, 12):
            L.rect(bx, by, 1, 5, NI[2])
    # the gap where three bricks were pulled out (dark cavity), bricks lying below
    cav = (xx >= 22) & (xx < 58) & (yy >= 88) & (yy < 100)
    tone(L, cav, 0, 0, 0.2 + (xx - 30) / 200.0, [NI[0], NI[1], NI[2]])
    put(L, edge_mask(cav, 't'), RU[0])
    for (bx, by) in ((26, 104), (40, 108), (14, 110)):
        L.rect(bx, by, 11, 5, RU[2]); L.rect(bx, by, 11, 1, RU[4]); L.rect(bx + 10, by, 1, 5, RU[0])
    ground = yy >= 112
    gn = value_noise(W, H, 7, seed=2, octaves=3)
    tone(L, ground, 0, 0, band(0.35 + (gn - 0.5) * 0.7 - (yy - 112) / 200.0, 4, 0.3), [NI[1], NI[2], ST[0], ST[1]])
    drift = ground & (yy < 116 + (np.sin(xx * 0.21) * 2 + np.sin(xx * 0.07) * 2).astype(int))
    tone(L, drift, 0, 0, 0.55 + (xx / W) * 0.3, [SN[0], SN[1], SN[2]])
    specks = ground & (value_noise(W, H, 3, seed=12, octaves=1) > 0.95) & ~drift
    put(L, specks, SN[0])
    # the stair above, seen from below: a riveted steel stringer climbing to the upper right, treads on
    # top of it as dark slabs with lit front edges, warm light (signal-box window) through the gaps
    def sy(x):
        return int(78 - x * 0.30)
    for i in range(10):
        tx_ = -14 + i * 28
        top = sy(tx_ + 12) - 14
        slab = poly_mask([(tx_, top + 2), (tx_ + 24, top - 5), (tx_ + 24, top + 1), (tx_, top + 8)])
        put(L, slab, NI[1]); put(L, edge_mask(slab, 't'), RU[2])
        gap = poly_mask([(tx_ + 24, top - 5), (tx_ + 28, top - 6), (tx_ + 60, 112), (tx_ + 44, 112)])
        shift(L, gap & dither_mask(np.full((H, W), 0.42)), 1)
        for s in range(4):
            L.px(tx_ + 25 + s % 2, top - 4 + s * 2, SN[3] if s % 2 else SN[2])
    for x in range(-4, W + 4):
        y0 = sy(x)
        for k in range(8):
            yv = y0 + k
            if 0 <= x < W and 0 <= yv < H:
                L.c[yv, x] = (RU[2] if k == 1 else RU[1] if k < 3 else NI[2] if k < 7 else NI[0])
        if x % 14 == 0 and 0 <= x < W:
            L.px(x, y0 + 4, ST[3]); L.px(x + 1, y0 + 4, ST[1])
    # the opened oilcloth bundle (dark green waxed cloth, glossy folds) with a red rag corner
    cloth = poly_mask([(70, 96), (100, 80), (196, 82), (230, 98), (214, 132), (96, 136), (64, 124)])
    ctone = 0.35 + 0.18 * np.sin(xx * 0.09 + yy * 0.05) + (value_noise(W, H, 8, seed=5, octaves=2) - 0.5) * 0.2
    tone(L, cloth, 0, 0, band(ctone, 4, 0.3), [NI[1], TE[0], TE[1], SA[1]])
    put(L, outline_mask(cloth), NI[0])
    gloss = cloth & (np.abs(np.sin(xx * 0.09 + yy * 0.05) - 0.9) < 0.04)
    put(L, gloss, SA[3])
    rag = poly_mask([(196, 84), (232, 96), (240, 120), (222, 116), (206, 100)])
    tone(L, rag, 0, 0, 0.5 + (xx - 200) / 120.0, RED)
    put(L, outline_mask(rag), RED[0])
    # the travel chess set: hinged wooden board with peg holes, pieces mid-game
    bx0, by0, sw, sh = 104, 90, 11, 4
    L.rect(bx0 - 4, by0 - 4, sw * 8 + 8, sh * 8 + 8, WO[1]); L.rect(bx0 - 4, by0 - 4, sw * 8 + 8, 1, WO[3])
    for r in range(8):
        for c in range(8):
            light = (r + c) % 2 == 0
            L.rect(bx0 + c * sw, by0 + r * sh, sw, sh, CO[2] if light else WO[1])
            L.px(bx0 + c * sw + sw // 2, by0 + r * sh + 1, WO[0] if light else NI[2])
    L.rect(bx0 + 4 * sw - 1, by0 - 4, 2, sh * 8 + 8, WO[0])
    L.rect(bx0 - 4, by0 + sh * 8 + 4, sw * 8 + 8, 2, WO[0])
    layout = [('k', 6, 7, True), ('r', 5, 7, True), ('p', 5, 6, True), ('p', 6, 6, True), ('p', 7, 5, True),
              ('q', 3, 4, True), ('n', 4, 5, True), ('p', 2, 4, True),
              ('k', 1, 0, False), ('r', 3, 0, False), ('p', 0, 1, False), ('p', 1, 2, False), ('b', 4, 2, False),
              ('p', 6, 3, False)]
    for kind, c, r, white in sorted(layout, key=lambda p: p[2]):
        chess_piece(L, bx0 + c * sw + 3, by0 + r * sh + 2, kind, white)
    for i, (kind, white) in enumerate((('n', False), ('p', False), ('p', False), ('b', False))):
        chess_piece(L, 82 + i * 6, 122, kind, white)
    chess_piece(L, 196, 128, 'p', True)
    # a score sheet tucked into the cloth
    sheet = poly_mask([(74, 100), (98, 96), (100, 114), (76, 118)])
    tone(L, sheet, 0, 0, 0.6, [SK[3], SK[4], SN[2]])
    for k in range(3):
        pseudo_hand(L, 78, 99 + k * 5, 18, NI[2], rng)
    light_pool(L, 150, 40, 120, 80, steps=1, power=0.8)
    light_pool(L, W / 2, H + 40, 220, 80, steps=-1, power=1.2)
    flakes(L, 16, seed_of('su.flakes'), (1, 1, W - 1, 80), big=0.1)
    vignette(L, 0.9)
    frame(L)
    return L


def fire_barrel_closeup(L: Layer, x, y, w=58, h=84):
    """Rusty oil drum with punched holes glowing, flames on top (close-up scale)."""
    yy, xx = np.mgrid[0:h, 0:w]
    nx = (xx - w / 2) / (w / 2)
    t = 0.42 + 0.35 * (nx < -0.2) * (1 - np.abs(nx + 0.6)) - 0.25 * (nx > 0.5) + (value_noise(w, h, 5, seed=3, octaves=2) - 0.5) * 0.3
    tone(L, full(h, w), x, y, band(t, 5, 0.3), [RU[0], RU[1], RU[2], RU[3], RU[4]])
    for ry in (12, 44, 76):
        L.rect(x, y + ry, w, 2, RU[0]); L.rect(x, y + ry, w, 1, RU[3])
    for (hx_, hy_) in ((10, 24), (24, 30), (40, 22), (16, 56), (32, 60), (46, 54)):
        L.rect(x + hx_, y + hy_, 4, 4, CO[3]); L.rect(x + hx_ + 1, y + hy_ + 1, 2, 2, CO[4]); L.px(x + hx_, y + hy_, CO[2])
    L.rect(x - 1, y, w + 2, 3, NI[2]); L.rect(x - 1, y, w + 2, 1, RU[3])
    # flames: layered tongues
    rng = np.random.default_rng(5)
    for k in range(9):
        fx = x + 4 + k * 6
        fh = int(10 + rng.integers(0, 16))
        for j in range(fh):
            wv = max(1, int((fh - j) / fh * 4))
            ox = int(2 * math.sin(j * 0.5 + k))
            col = CO[4] if j < fh * 0.3 else CO[3] if j < fh * 0.6 else CO[2] if j < fh * 0.85 else RED[3]
            L.rect(fx + ox - wv // 2, y - 1 - j, wv, 1, col)
    for k in range(10):
        L.px(x + int(rng.integers(0, w)), y - int(rng.integers(20, 40)), CO[4])


def horn(L: Layer, x0, y0, r0, x1, y1, r1, flare=2.6):
    """Flared horn loudspeaker from the driver (x0,y0) to the mouth (x1,y1); returns the horn mask."""
    m = np.zeros((H, W), bool)
    ht = np.zeros((H, W))
    n = int(max(abs(x1 - x0), abs(y1 - y0)) * 3) + 1
    dx, dy = x1 - x0, y1 - y0
    ln = math.hypot(dx, dy)
    ux, uy = dx / ln, dy / ln
    px, py = -uy, ux
    for i in range(n + 1):
        f = i / n
        cx = x0 + dx * f
        cy = y0 + dy * f
        r = r0 + (r1 - r0) * f ** flare
        for s in np.linspace(-r, r, int(2 * r * 2) + 2):
            X = int(round(cx + px * s))
            Y = int(round(cy + py * s))
            if 0 <= X < W and 0 <= Y < H:
                v = s / r
                m[Y, X] = True
                ht[Y, X] = 0.62 - v * 0.42 + 0.25 * math.exp(-((v + 0.55) / 0.2) ** 2)
    tone(L, m, 0, 0, band(ht, 5, 0.3), [NI[2], TE[1], TE[2], ST[3], ST[4]])
    return m


def hooded_crow(L: Layer, x, y, facing=1, pose='perch', k=1.0):
    """Hooded crow perched on a wire, feet at (x, y); size scale k (1.0 ~ 22x20 px). Grey mantle and belly,
    black hood, bib, wings and tail; pose 'perch' | 'look' (head to the viewer) | 'preen' (head to the wing)."""
    f = facing
    cw, ch = int(34 * k), int(30 * k)
    C = Layer(cw, ch)
    ox, oy = int(13 * k), int(25 * k)
    body, tb = sphere_t(cw, ch, ox + 1 * k, oy - 9 * k, 9.0 * k, 7.0 * k, light=(0.45, -0.8, 0.45))
    tone(C, body, 0, 0, band(tb, 4, 0.3), [ST[1], ST[2], ST[3], ST[4]])
    wing = poly_mask([(ox - 6 * k, oy - 13 * k), (ox + 6 * k, oy - 14 * k), (ox + 10 * k, oy - 8 * k),
                      (ox + 2 * k, oy - 4 * k), (ox - 7 * k, oy - 8 * k)], cw, ch)
    tw = band(0.4 + (np.mgrid[0:ch, 0:cw][1] - ox) / (24 * k), 3, 0.3)
    tone(C, wing, 0, 0, tw, [NI[1], NI[2], TE[0]])
    for j in range(3):
        yy_ = int(oy - (11 - j * 2) * k)
        C.line(int(ox - 4 * k), yy_, int(ox + 6 * k), yy_ - 1, NI[1])
    tail = poly_mask([(ox - 7 * k, oy - 9 * k), (ox - 15 * k, oy - 4 * k), (ox - 14 * k, oy - 1.5 * k),
                      (ox - 6 * k, oy - 5 * k)], cw, ch)
    put(C, tail, NI[1])
    if pose == 'preen':
        hx, hy = ox + 2 * k, oy - 14 * k
    else:
        hx, hy = ox + 8.5 * k, oy - 16 * k
    head = ellipse_full(hx, hy, 4.4 * k, 4.0 * k, cw, ch)
    tone(C, head, 0, 0, 0.3 + (np.mgrid[0:ch, 0:cw][0] < hy - 1.5 * k) * 0.4, [NI[0], NI[1], NI[3]])
    bib = ellipse_full(hx - 1 * k, hy + 4.5 * k, 3.2 * k, 3.2 * k, cw, ch) & ~head
    put(C, bib, NI[2])
    hx, hy = int(round(hx)), int(round(hy))
    if pose == 'look':
        for dx in (-int(1.4 * k), int(1.4 * k)):
            C.px(hx + dx, hy - 1, SK[4]); C.px(hx + dx, hy, NI[0])
        for j in range(int(3 * k)):
            C.px(hx, hy + 1 + j, ST[1] if j == 0 else NI[0])
    elif pose == 'preen':
        for j in range(int(3 * k)):
            C.px(hx - 2 - j, hy + 1 + j, NI[0])
    else:
        C.px(hx + 1, hy - 1, SK[4]); C.px(hx + 1, hy, NI[0])
        for j in range(int(4 * k)):
            C.px(hx + 3 + j, hy + j // 3, NI[0] if j < 3 * k else ST[1])
            if j < 3 * k - 1:
                C.px(hx + 3 + j, hy + 1 + j // 3, NI[1])
    for fx in (int(ox - 1 * k), int(ox + 2 * k)):
        for j in range(int(3 * k)):
            C.px(fx, oy - 3 * k + j, NI[1])
        C.px(fx - 1, oy, NI[2]); C.px(fx + 1, oy, NI[2])
    alpha = C.c[..., 3] > 0
    for yv, xv in zip(*np.nonzero(edge_mask(alpha, 'r') & alpha)):
        if int(C.c[yv, xv][0]) > 60:
            C.px(xv, yv, SK[3])
    for yv, xv in zip(*np.nonzero(edge_mask(alpha, 't') & alpha & body)):
        C.px(xv, yv, ST[5])
    if f < 0:
        C.c = C.c[:, ::-1].copy()
        C.hgt = C.hgt[:, ::-1].copy()
        C.em = C.em[:, ::-1].copy()
        ox = cw - 1 - ox
    L.blit(C, x - ox, y - oy)


def img_crows() -> Layer:
    """Hooded crows on the PA cable (exp_crows): grey mantles, black hoods, snow on the wire."""
    L = Layer(W, H)
    dawn_sky(L, 0, H, seed=seed_of('cr.sky'))
    silhouette_yard(L, H - 4, seed_of('cr.yard'), (SK[0], SK[1]))
    for i in range(W):
        L.px(i, 34 + int(10 * math.sin(i / W * math.pi)), TE[2])

    def cable_y(x):
        return int(104 + 18 * math.sin((x + 40) / (W + 80) * math.pi))
    # the PA mast at the left edge: timber pole, crossarm, insulator, the cable leaving it
    L.rect(8, 0, 9, H, WO[1]); L.rect(8, 0, 2, H, WO[3]); L.rect(16, 0, 1, H, NI[2])
    L.rect(0, 70, 40, 4, ST[1]); L.rect(0, 70, 40, 1, ST[3]); snow_on_top(L, np.pad(full(1, 40), ((70, H - 71), (0, W - 40))), depth=2, seed=2)
    L.rect(30, 74, 5, 8, SN[1]); L.rect(30, 74, 5, 1, SN[3])
    for i in range(32, W):
        cy = cable_y(i)
        L.px(i, cy, NI[1]); L.px(i, cy + 1, NI[2])
        if (i * 7) % 5 < 3:
            L.px(i, cy - 1, SN[3])
    for (cx, pose, f) in ((84, 'perch', 1), (146, 'look', 1), (206, 'preen', -1)):
        hooded_crow(L, cx, cable_y(cx), f, pose, k=1.75)
    L.px(168, 140, NI[2]); L.px(169, 141, NI[2]); L.px(169, 140, ST[2])
    flakes(L, 40, seed_of('cr.flakes'))
    vignette(L, 0.7)
    frame(L)
    return L


def img_cooling_towers() -> Layer:
    """Two cooling towers on the horizon, steaming (exp_cooling_towers): haze planes, power line, fence."""
    L = Layer(W, H)
    dawn_sky(L, 0, H, seed=seed_of('ct.sky'))
    yy, xx = np.mgrid[0:H, 0:W]
    # far forest line and plant buildings in haze
    for x in range(W):
        h = 6 + int(3 * math.sin(x * 0.21) + 2 * math.sin(x * 0.07))
        L.rect(x, 112 - h, 1, h, SK[1])
    L.rect(0, 112, W, 48, SK[1])
    # two hyperboloid towers with vertical shading, the right one partly behind the left
    for (cx, base, top, rb, rt, sh) in ((92, 112, 40, 30, 17, 0.0), (170, 112, 52, 26, 15, 0.12)):
        for y in range(top, base):
            f = (y - top) / (base - top)
            waist = 0.35
            r = rt + (rb - rt) * (f ** 1.6) - 4 * math.exp(-((f - waist) / 0.25) ** 2)
            for x in range(int(cx - r), int(cx + r) + 1):
                nx = (x - cx) / max(r, 1)
                t = 0.62 - 0.35 * nx - sh + (0.06 if (x // 3) % 2 else 0)
                idx = int(np.clip(round(t * 4), 0, 4))
                L.px(x, y, [SK[0], SK[1], SK[2], SK[3], SK[4]][idx])
        L.rect(int(cx - rt), top, int(2 * rt) + 1, 1, SK[4])
    # steam plumes: billowing dithered columns drifting right
    for (cx, top, seed) in ((92, 40, 3), (170, 52, 4)):
        for k in range(46):
            ry = top - k
            rr = 10 + k * 0.45
            sx = cx + k * 0.9 + 3 * math.sin(k * 0.3 + seed)
            m = ellipse_full(sx, ry, rr, 4.5)
            amt = np.clip(0.9 - k / 52.0, 0, 1)
            sel = m & dither_mask(np.full((H, W), amt))
            put(L, sel, SN[2] if k % 3 else SN[3])
    # a chimney, a power line and a foreground fence with snow
    L.rect(214, 66, 6, 46, SK[1]); L.rect(214, 66, 6, 1, SK[3])
    for i in range(W):
        L.px(i, 22 + int(8 * math.sin(i / W * math.pi)), NI[3])
    ground = yy >= 128
    tone(L, ground, 0, 0, band(0.6 + (value_noise(W, H, 12, seed=7, octaves=2) - 0.5) * 0.25, 3, 0.3), [SN[0], SN[1], SN[2]])
    for px_ in range(4, W, 26):
        L.rect(px_, 112, 3, 34, ST[1]); L.rect(px_, 112, 1, 34, ST[3]); L.px(px_ + 1, 111, SN[3])
    for k in range(3):
        for i in range(W):
            L.px(i, 116 + k * 9 + int(2 * math.sin(i * 0.12 + k)), ST[0] if i % 6 else ST[2])
    flakes(L, 30, seed_of('ct.flakes'))
    vignette(L, 0.75)
    frame(L)
    return L


# =========================================================================== build
# (file name, builder, has a _hist variant)
IMAGES = [
    ('barrack', img_barrack, False),
    ('cat', img_cat, False),
    ('stairs_under', img_stairs_under, False),
    ('loudspeaker', img_loudspeaker, False),
    ('newspaper', img_newspaper, True),
    ('wagon_chalk', img_wagon_chalk, False),
    ('grain', img_grain, False),
    ('snowman', img_snowman, False),
    ('banner', img_banner, True),
    ('stash', img_stash, False),
    ('kontora_shelf', img_kontora_shelf, False),
    ('mitten', img_mitten, False),
    ('crows', img_crows, False),
    ('cooling_towers', img_cooling_towers, False),
]


def build_all(out_dir=OUT, preview_dir=None):
    written = []
    for name, fn, has_hist in IMAGES:
        variants = [(name, False), (name + '_hist', True)] if has_hist else [(name, None)]
        for fname, hist in variants:
            L = fn(hist) if hist is not None else fn()
            if L.w > 320 or L.h > 200:
                raise SystemExit('%s: %dx%d exceeds the 320x200 close-up limit' % (fname, L.w, L.h))
            written.append(save(L, fname, out_dir))
            if preview_dir:
                os.makedirs(preview_dir, exist_ok=True)
                im = Image.fromarray(L.c, 'RGBA').convert('RGB')
                im.resize((L.w * 3, L.h * 3), Image.NEAREST).save(os.path.join(preview_dir, fname + '_x3.png'))
    return written


if __name__ == '__main__':
    prev = os.environ.get('EXPLORE_KARSK_PREVIEW') if '--preview' in sys.argv else None
    files = build_all(OUT, prev)
    for f in files:
        print('wrote', os.path.relpath(f, ROOT).replace(os.sep, '/'))
    print('%d close-ups, palette check OK' % len(files))
