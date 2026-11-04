"""env_karsk_skyline_lib -- shared helpers for the redesigned Karsk background skyline (scene A1).

Self-contained on purpose: depends only on tools/pixelgen/pg.py (the shared core, never modified), so the
skyline can be regenerated independently of the env_karsk_* railyard generator.  Everything is original
procedural pixel art (no reference image is sampled or traced).

World / plane model (see documentation/asset_manifest_parts/karsk_skyline.md):
    every plane is drawn in WORLD rows (y 0..359, camera y is always 0 in this level) and cropped to the layer
    rows at save time, x = layer x (= screen x at camera 0).  Depth scale: architecture px/m = 10.56 * parallax
    (near_bg 7.6, mid 4.75, far_industry 2.64, far_city 1.27), i.e. scale is proportional to parallax as for a
    pinhole camera; the background is compressed ~2.5x against the hero-scale playfield (person 47 px).
"""
from __future__ import annotations

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import numpy as np  # noqa: E402
from PIL import Image  # noqa: E402

import pg  # noqa: E402
from pg import Layer, hx, bayer, value_noise  # noqa: E402,F401

ROOT = 'C:/Spiele/AshesOfEmpires'
OUT_DIR = ROOT + '/assets/environments/karsk_skyline'
SRC_ENV = ROOT + '/assets/environments/karsk_railyard'
TEST_DIR = ROOT + '/tests/visual/skyline'
SCRATCH = os.environ.get('KARSK_SKYLINE_SCRATCH',
                         'C:/Users/quent/AppData/Local/Temp/claude/93385ca81d10c49a/'
                         'a2c7a323-0b5e-4c1a-ac96-5cf7edc43030/scratchpad/karsk-skyline')

KP = pg.PALETTES['karsk']


def _r(n):
    return [hx(c) for c in KP[n]]


NI, TE, SA, SK, ST, RU, CO, SN, WO = (_r(n) for n in
                                      ('night', 'teal', 'sage', 'sky', 'stone', 'rust', 'copper', 'snow', 'wood'))
RED = [hx(c) for c in pg.PALETTES['sepia']['red']]          # shared C-17 red accent ramp
ALL = pg.all_colors('karsk') + RED
CLEAR = np.zeros(4, np.uint8)

WORLD_W, VIEW_W, VIEW_H = 1920, 640, 360
SUN = (612, 190)                         # hazy sun on the sky layer (parallax 0), screen coordinates
PX_PER_M_PER_PARALLAX = 10.56            # depth scale: px/m = 10.56 * parallax

# plane geometry = the layers this module replaces (identical size / pos / parallax / z as karsk_railyard)
PLANES = {
    'far_city':     dict(p=0.12, W=802, H=112, top=118, z=-90, base=207),
    'far_industry': dict(p=0.25, W=968, H=147, top=83, z=-84, base=217),
    'mid':          dict(p=0.45, W=1224, H=185, top=49, z=-74, base=231),
    'near_bg':      dict(p=0.72, W=1570, H=113, top=137, z=-60, base=249),
}
for _k, _v in PLANES.items():
    _v['ppm'] = round(PX_PER_M_PER_PARALLAX * _v['p'], 2)


def ppm(plane: str) -> float:
    return PLANES[plane]['ppm']


def ckey(c):
    c = np.asarray(c, np.int64)
    return (c[..., 0] << 16) | (c[..., 1] << 8) | c[..., 2]


# --------------------------------------------------------------------------- world-row layer
def world_layer(plane: str) -> Layer:
    """Full-height (360 rows) layer of the plane's width; drawn in world rows, cropped at save time."""
    g = PLANES[plane]
    L = Layer(g['W'], VIEW_H, plane)
    L.plane = plane
    return L


def crop_rows(L: Layer, y0: int, y1: int) -> Layer:
    N = Layer(L.w, y1 - y0, L.name)
    N.c, N.hgt, N.nrm, N.em = L.c[y0:y1].copy(), L.hgt[y0:y1].copy(), L.nrm[y0:y1].copy(), L.em[y0:y1].copy()
    return N


# --------------------------------------------------------------------------- drawing helpers
def put(L: Layer, x, y, c, n=None, em=None):
    """Single pixel with optional explicit normal (nx, ny, nz; +Y up) and emission."""
    x, y = int(x), int(y)
    if 0 <= x < L.w and 0 <= y < L.h:
        L.c[y, x] = c
        if n is not None:
            L.nrm[y, x] = n
        if em is not None:
            L.em[y, x] = em


def rect(L: Layer, x, y, w, h, c, n=None, em=None):
    x0, y0 = max(0, int(x)), max(0, int(y))
    x1, y1 = min(L.w, int(x) + int(w)), min(L.h, int(y) + int(h))
    if x1 <= x0 or y1 <= y0:
        return
    L.c[y0:y1, x0:x1] = c
    if n is not None:
        L.nrm[y0:y1, x0:x1] = n
    if em is not None:
        L.em[y0:y1, x0:x1] = em


def hline(L, x, y, w, c, n=None, em=None):
    rect(L, x, y, w, 1, c, n, em)


def vline(L, x, y, h, c, n=None, em=None):
    rect(L, x, y, 1, h, c, n, em)


def line(L, x0, y0, x1, y1, c, n=None):
    x0, y0, x1, y1 = int(round(x0)), int(round(y0)), int(round(x1)), int(round(y1))
    dx, dy = abs(x1 - x0), -abs(y1 - y0)
    sx, sy = (1 if x0 < x1 else -1), (1 if y0 < y1 else -1)
    err = dx + dy
    while True:
        put(L, x0, y0, c, n)
        if x0 == x1 and y0 == y1:
            break
        e2 = 2 * err
        if e2 >= dy:
            err += dy
            x0 += sx
        if e2 <= dx:
            err += dx
            y0 += sy


def poly(L, pts, c, n=None):
    m, x0, y0 = L.poly_mask(pts)
    L._put(m, x0, y0, c)
    if n is not None:
        L.paint_normal(m, x0, y0, n)
    return m, x0, y0


def clear_rect(L, x, y, w, h):
    rect(L, x, y, w, h, CLEAR)
    x0, y0 = max(0, int(x)), max(0, int(y))
    x1, y1 = min(L.w, int(x) + int(w)), min(L.h, int(y) + int(h))
    if x1 > x0 and y1 > y0:
        L.nrm[y0:y1, x0:x1] = np.nan
        L.em[y0:y1, x0:x1] = 0


def opaque(L, x, y) -> bool:
    x, y = int(x), int(y)
    return 0 <= x < L.w and 0 <= y < L.h and L.c[y, x, 3] > 0


def dith(x, y, t) -> bool:
    """Ordered-dither decision (Bayer 4x4) at pixel (x, y) for coverage t in 0..1."""
    return pg.BAYER4[int(y) % 4, int(x) % 4] < t


# normals (OpenGL, +Y up)
N_FRONT = (0.0, 0.0, 1.0)
N_UP = (0.0, 0.8, 0.6)
N_RIGHT = (0.7, 0.0, 0.71)
N_LEFT = (-0.7, 0.0, 0.71)
N_DOWN = (0.0, -0.6, 0.8)


def cyl_normals(L, x, y, w, h, mask=None):
    xs = (np.arange(w, dtype=np.float32) + 0.5 - w / 2) / (w / 2)
    nx = np.clip(xs, -0.95, 0.95)
    nz = np.sqrt(1 - nx * nx)
    n = np.stack([nx, np.zeros_like(nx), nz], -1)
    X0, Y0, X1, Y1 = max(0, x), max(0, y), min(L.w, x + w), min(L.h, y + h)
    if X1 <= X0 or Y1 <= Y0:
        return
    blk = np.repeat(n[None, X0 - x:X1 - x], Y1 - Y0, axis=0)
    m = L.c[Y0:Y1, X0:X1, 3] > 0
    if mask is not None:
        m &= mask[Y0 - y:Y1 - y, X0 - x:X1 - x]
    L.nrm[Y0:Y1, X0:X1][m] = blk[m]


def sphere_normals(L, cx, cy, rx, ry, x0, y0, x1, y1):
    for yy in range(max(0, y0), min(L.h, y1)):
        for xx in range(max(0, x0), min(L.w, x1)):
            if L.c[yy, xx, 3] == 0:
                continue
            nx = np.clip((xx + 0.5 - cx) / max(0.5, rx), -0.95, 0.95)
            ny = np.clip(-(yy + 0.5 - cy) / max(0.5, ry), -0.95, 0.95)
            nz = math.sqrt(max(0.05, 1 - nx * nx - ny * ny))
            v = np.array([nx, ny, nz], np.float32)
            L.nrm[yy, xx] = v / np.linalg.norm(v)


# --------------------------------------------------------------------------- haze (atmospheric perspective)
class Haze:
    """Colour chains toward the air light: each colour maps to its next hazier colour.  shift() moves pixels
    `amount` steps along their chain with ordered dither (clean 2-colour transitions, no new colours)."""

    def __init__(self, chains):
        self.nxt = {}
        for ch in chains:
            for a, b in zip(ch[:-1], ch[1:]):
                ka = int(ckey(a))
                if ka not in self.nxt:
                    self.nxt[ka] = np.asarray(b, np.uint8)

    def shift(self, L: Layer, amount: np.ndarray, mask=None, size=4):
        """amount: (h, w) float steps (>= 0)."""
        a = np.clip(amount, 0, 12)
        k = np.floor(a)
        thr = bayer(L.w, L.h, 0, 0, size)
        k = (k + ((a - k) > thr)).astype(np.int32)
        sel = (L.c[..., 3] > 0) & (k > 0)
        if mask is not None:
            sel &= mask
        if not sel.any():
            return
        out = L.c.copy()
        ys, xs = np.nonzero(sel)
        for yy, xx, kk in zip(ys, xs, k[ys, xs]):
            c = L.c[yy, xx]
            for _ in range(int(kk)):
                n = self.nxt.get(int(ckey(c)))
                if n is None:
                    break
                c = n
            out[yy, xx] = c
        L.c = out


def vfog(L: Layer, y0: int, y1: int, steps: float, power: float = 1.5) -> np.ndarray:
    """(h, w) amount array: 0 above world row y0 rising to `steps` at y1 (ground haze)."""
    rows = np.arange(L.h, dtype=np.float32)
    t = np.clip((rows - y0) / max(1, y1 - y0), 0, 1) ** power * steps
    return np.repeat(t[:, None], L.w, axis=1)


# --------------------------------------------------------------------------- fonts (5x7 caps, original)
FONT_L = {
    'С': [".###.", "#...#", "#....", "#....", "#....", "#...#", ".###."],
    'Л': ["..###", ".#..#", ".#..#", ".#..#", ".#..#", ".#..#", "#...#"],
    'А': [".###.", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"],
    'В': ["####.", "#...#", "#...#", "####.", "#...#", "#...#", "####."],
    'Т': ["#####", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."],
    'Р': ["####.", "#...#", "#...#", "####.", "#....", "#....", "#...."],
    'У': ["#...#", "#...#", "#...#", ".####", "....#", "#...#", ".###."],
    'Д': [".###.", ".#.#.", ".#.#.", ".#.#.", ".#.#.", "#####", "#...#"],
    'Е': ["#####", "#....", "#....", "####.", "#....", "#....", "#####"],
    'П': ["#####", "#...#", "#...#", "#...#", "#...#", "#...#", "#...#"],
    'О': [".###.", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."],
    'К': ["#...#", "#..#.", "#.#..", "##...", "#.#..", "#..#.", "#...#"],
    'Э': [".###.", "#...#", "....#", ".####", "....#", "#...#", ".###."],
    'Ф': ["..#..", ".###.", "#.#.#", "#.#.#", ".###.", "..#..", "..#.."],
    'Ж': ["#.#.#", "#.#.#", ".###.", "..#..", ".###.", "#.#.#", "#.#.#"],
    '!':["##", "##", "##", "##", "##", "..", "##"],
    '1': [".#.", "##.", ".#.", ".#.", ".#.", ".#.", "###"],
    '9': [".###.", "#...#", "#...#", ".####", "....#", "....#", ".###."],
    '3': [".###.", "#...#", "....#", "..##.", "....#", "#...#", ".###."],
    '6': [".###.", "#....", "#....", "####.", "#...#", "#...#", ".###."],
}
FONT_S = {
    'С': ["###", "#..", "#..", "#..", "###"], 'Л': [".##", "#.#", "#.#", "#.#", "#.#"],
    'А': ["###", "#.#", "###", "#.#", "#.#"], 'В': ["##.", "#.#", "##.", "#.#", "##."],
    'Т': ["###", ".#.", ".#.", ".#.", ".#."], 'Р': ["###", "#.#", "###", "#..", "#.."],
    'У': ["#.#", "#.#", "###", "..#", "##."], 'Д': ["..##", ".#.#", ".#.#", "####", "#..#"],
    'Е': ["###", "#..", "##.", "#..", "###"], 'П': ["###", "#.#", "#.#", "#.#", "#.#"],
    'О': ["###", "#.#", "#.#", "#.#", "###"], 'К': ["#.#", "#.#", "##.", "#.#", "#.#"],
    'Г': ["###", "#..", "#..", "#..", "#.."], 'Э': ["##.", "..#", ".##", "..#", "##."],
    'Х': ["#.#", "#.#", ".#.", "#.#", "#.#"], 'Б': ["###", "#..", "###", "#.#", "###"],
    'Н': ["#.#", "#.#", "###", "#.#", "#.#"], 'Ч': ["#.#", "#.#", "###", "..#", "..#"],
    'И': ["#..#", "#.##", "##.#", "#..#", "#..#"], 'М': ["#...#", "##.##", "#.#.#", "#...#", "#...#"],
    'Я': ["###", "#.#", "###", ".##", "#.#"], 'Ш': ["#.#.#", "#.#.#", "#.#.#", "#.#.#", "#####"],
    '!': ["#", "#", "#", ".", "#"], '1': [".#", "##", ".#", ".#", ".#"], '9': ["###", "#.#", "###", "..#", "##."],
    '3': ["##.", "..#", ".#.", "..#", "##."], '5': ["###", "#..", "##.", "..#", "##."],
    '6': [".##", "#..", "###", "#.#", "###"], '0': ["###", "#.#", "#.#", "#.#", "###"],
    '-': ["...", "...", "##.", "...", "..."], '.': [".", ".", ".", ".", "#"],
}


# bold 7-row capitals with 2 px stems for rooftop sheet-metal letters (read at 1x from far away)
FONT_B = {
    'С': [".####.", "##..##", "##....", "##....", "##....", "##..##", ".####."],
    'Л': ["..####", ".##.##", ".##.##", ".##.##", ".##.##", ".##.##", "##..##"],
    'А': [".####.", "##..##", "##..##", "######", "##..##", "##..##", "##..##"],
    'В': ["#####.", "##..##", "##..##", "#####.", "##..##", "##..##", "#####."],
    'Т': ["######", "..##..", "..##..", "..##..", "..##..", "..##..", "..##.."],
    'Р': ["#####.", "##..##", "##..##", "#####.", "##....", "##....", "##...."],
    'У': ["##..##", "##..##", "##..##", ".#####", "....##", "##..##", ".####."],
    'Д': [".#####.", ".##.##.", ".##.##.", ".##.##.", ".##.##.", "#######", "##...##"],
    'Е': ["######", "##....", "##....", "#####.", "##....", "##....", "######"],
    'О': [".####.", "##..##", "##..##", "##..##", "##..##", "##..##", ".####."],
    'М': ["##...##", "###.###", "##.#.##", "##...##", "##...##", "##...##", "##...##"],
    'Н': ["##..##", "##..##", "##..##", "######", "##..##", "##..##", "##..##"],
    '!': ["##", "##", "##", "##", "##", "..", "##"],
}


def glyph_mask(ch: str, font: str = 'L', scale: int = 1):
    f = FONT_L if font == 'L' else (FONT_B if font == 'B' else FONT_S)
    g = f.get(ch)
    if not g:
        return None
    m = np.array([[c == '#' for c in row] for row in g], bool)
    if scale > 1:
        m = np.repeat(np.repeat(m, scale, 0), scale, 1)
    return m


def text_width(s: str, font='L', spacing=1, scale=1) -> int:
    w = 0
    for ch in s:
        if ch == ' ':
            w += (2 if font == 'S' else 3) * scale
        else:
            m = glyph_mask(ch, font, scale)
            w += (m.shape[1] if m is not None else 3) + spacing
    return max(0, w - spacing)


def text_masks(s: str, font='L', spacing=1, scale=1):
    """[(x offset, mask)] for every glyph."""
    out, cx = [], 0
    for ch in s:
        if ch == ' ':
            cx += (2 if font == 'S' else 3) * scale
            continue
        m = glyph_mask(ch, font, scale)
        if m is None:
            cx += 4
            continue
        out.append((cx, m))
        cx += m.shape[1] + spacing
    return out


def draw_text(L, x, y, s, col, font='S', spacing=1, n=N_FRONT, em=None):
    for ox, m in text_masks(s, font, spacing):
        ys, xs = np.nonzero(m)
        for yy, xx in zip(ys, xs):
            put(L, x + ox + xx, y + yy, col, n, em)


# --------------------------------------------------------------------------- state emblems (TECH ARCH 12.4)
# neutral (fictional gear-and-wheat) <-> historical (hammer & sickle) pairs of identical footprint; the masks
# are the project's emblem set of env_karsk_emblems (copied, so this generator stays independent).
EMBLEMS = {
    'gw11': """
....###....
.#.#####.#.
..##....##.
.##....####
###...####.
###..####.#
###.####.##
.##.#.#.##.
..#.#..##..
.#.#####.#.
....###....""",
    'hs11': """
.....###...
.##....##..
####....##.
.####....#.
..####...#.
...#.##.##.
......###..
....######.
..###...##.
.##......#.
##.........""",
    'gw9': """
...###...
.#######.
.##...##.
###..####
###.####.
###.#.###
.#.#..##.
.#######.
...###...""",
    'hs9': """
.....##..
.#.....#.
###....##
.###...##
..#.#.##.
....###..
..##.##..
.##...##.
##.....#.""",
    'star5': """
..#..
.###.
#####
.###.
.#.#.""",
    'star7': """
...#...
...#...
#######
.#####.
..###..
.##.##.
.#...#.""",
}


def emblem_mask(kind: str) -> np.ndarray:
    rows = EMBLEMS[kind].strip('\n').split('\n')
    w = max(len(r) for r in rows)
    m = np.zeros((len(rows), w), bool)
    for y, r in enumerate(rows):
        for x, ch in enumerate(r):
            m[y, x] = ch == '#'
    return m


def paint_mask(L, x, y, m, col, shade=None, n=N_FRONT, em=None):
    h, w = m.shape
    for yy in range(h):
        for xx in range(w):
            if not m[yy, xx]:
                continue
            c = col
            if shade is not None:
                below = yy + 1 >= h or not m[yy + 1, xx]
                left = xx == 0 or not m[yy, xx - 1]
                if below or left:
                    c = shade
            put(L, x + xx, y + yy, c, n, em)


# --------------------------------------------------------------------------- QA
def palette_report(arr: np.ndarray):
    pal = set(int(k) for k in ckey(np.stack(ALL)[:, :3]))
    a = arr[..., 3] > 0
    keys = np.unique(ckey(arr[..., :3])[a])
    return [('#%06X' % int(k)) for k in keys if int(k) not in pal]


def save_png(arr: np.ndarray, path: str):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    Image.fromarray(arr, 'RGBA').save(path)
