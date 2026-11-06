"""env_veltrava_cine -- Chapter 3 cinematic art (LS_C3_Trains, LS_C3_ToHall, LS_C3_Close).

Owner: cinematics stream (documentation/C3_DESIGN.md §7).  Every file written here is original, painted in
code, deterministic (fixed seeds, no time or global random state) and drawn at 1 texel = 1 px of the
640x360 world (close shots use bespoke larger figures, never scaled sprites).  Run:

    py -3 -P tools/pixelgen/env_veltrava_cine.py [--only trains,tohall,close]     (~2 min uncached, ~3 s cached)

Palette: the 'veltrava' / 'palais' ramps of data/chapters/c3.json are registered into pg.PALETTES at import
time (read-only use).  Konrad and Alexei (backs at the windows, faces in the glass) are sculpted with the
dialogue-portrait SDF pipeline in env_veltrava_cine_figs.py so they match their portraits and sprites.
Modules: this file (trains: night exterior, both compartments, flare, build/main), env_veltrava_cine_dawn.py
(t4), env_veltrava_cine_tohall.py, env_veltrava_cine_close.py, env_veltrava_cine_kit.py, env_veltrava_cine_figs.py.

Output (assets/cinematics/ch3/):
  trains/  ext_sky, ext_far_de|su, ext_mid, ext_near, pole, int_konrad, fig_konrad, refl_konrad, glow_lamp,
           patch_warm|cold, int_alexei, fig_alexei, refl_alexei, glow_tea, steam_tea, spoon, sweep, flare,
           roomflare_k|a, bridge_bg, bridge_fg, train_de, train_su, smoke, dawn_glow, fg_glow, walker
  tohall/  k1_bg, k1_clock, k1_glass, steam_puffs, k2_bg, k2_clock, k2_glass, pendulum, k2_konrad
  close/   n1_bg, n1_mid, n1_fg, board, steam, n2_bg, n2_win_konrad, n2_win_alexei, n2_lamp_glow
The runtime (scenes/cinematics/ch3_*) composes these layers and animates them; layout constants shared with
the runtime are listed in LAYOUT and written to assets/cinematics/ch3/layout.json.
"""
from __future__ import annotations

import json
import math
import os
import sys

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
import pg  # noqa: E402
import env_berlin_kit as kit  # noqa: E402

DATE = '2026-11-04'
VW, VH = 640, 360
SAFE = (46, 314)                 # visible rows inside the 2.39:1 letterbox (138 px bars at 1080p = 46 px)
OUT = os.path.join(ROOT, 'assets', 'cinematics', 'ch3')

# --------------------------------------------------------------------------- palettes
with open(os.path.join(ROOT, 'data', 'chapters', 'c3.json'), encoding='utf-8') as _f:
    _C3 = json.load(_f)
pg.PALETTES.setdefault('veltrava', _C3['palettes']['veltrava'])
pg.PALETTES.setdefault('palais', _C3['palettes']['palais'])
V = pg.PALETTES['veltrava']
P = pg.PALETTES['palais']
KR = pg.PALETTES['karsk']

# character ramps sampled from assets/characters/{konrad,alexei}/sheet.png + portrait.png
K_COAT = ['#05070E', '#0B0F1C', '#131A2C', '#1D2442', '#2C3B5E', '#3A4A6A', '#4E556C', '#7E848F']
K_HAT = ['#0E0D12', '#1F1A22', '#2D2D36', '#3D3639', '#4B4547', '#5E504C', '#7C6A5E']
K_SCARF = ['#3D3020', '#5E4A36', '#76583A', '#8E7656', '#AD9271', '#D0B074']
SKIN = ['#3E2C3A', '#6E4442', '#8A5550', '#A2664E', '#B67D66', '#D2925E', '#F2C47E']
A_COAT = ['#000B10', '#0B2825', '#193026', '#213D34', '#3B5443', '#5D6D57', '#718C7D']
A_FUR = ['#15181B', '#2A3034', '#383D3A', '#474845', '#57514A', '#73624E', '#816E56', '#977E62']
A_BAG = ['#2A1E16', '#544434', '#7A5639', '#957253', '#A68C6A']

# cold night super-ramp: night -> slate -> snow (monotonic luminance)
COLD = V['night'] + V['slate'] + V['snow']                     # 0..14
WARM = V['lamp']                                                # 0..4


def ramps(**kw) -> kit.Ramps:
    return kit.Ramps(kw)


# --------------------------------------------------------------------------- generic helpers
def grid(h, w, x0=0, y0=0):
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    return yy + y0, xx + x0


def dist_inside(mask: np.ndarray, maxd: int = 24) -> np.ndarray:
    """Chamfer-ish distance (in px) from every True pixel to the nearest False pixel (capped)."""
    d = np.zeros(mask.shape, np.float32)
    cur = mask.copy()
    for k in range(1, maxd + 1):
        if not cur.any():
            break
        d[cur] = k
        cur = kit.erode(cur, 1)
    return d


def rim(mask: np.ndarray, dx: int, dy: int, width: int = 1) -> np.ndarray:
    """Pixels of mask within `width` px of an edge that faces direction (dx, dy) (toward the light)."""
    out = np.zeros_like(mask)
    for k in range(1, width + 1):
        out |= mask & ~shift(mask, dx * k, dy * k)
    return out


def shift(m: np.ndarray, dx: int, dy: int, fill=False) -> np.ndarray:
    """out[y, x] = m[y + dy, x + dx] (pixels shifted by (-dx, -dy)); outside -> fill."""
    h, w = m.shape[:2]
    out = np.full_like(m, fill)
    ys0, ys1 = max(0, dy), min(h, h + dy)
    xs0, xs1 = max(0, dx), min(w, w + dx)
    yd0, xd0 = max(0, -dy), max(0, -dx)
    out[yd0:yd0 + (ys1 - ys0), xd0:xd0 + (xs1 - xs0)] = m[ys0:ys1, xs0:xs1]
    return out


def poly_mask(w, h, pts):
    lay = pg.Layer(w, h)
    m, x0, y0 = lay.poly_mask(pts)
    out = np.zeros((h, w), bool)
    X0, Y0 = max(0, x0), max(0, y0)
    X1, Y1 = min(w, x0 + m.shape[1]), min(h, y0 + m.shape[0])
    if X1 > X0 and Y1 > Y0:
        out[Y0:Y1, X0:X1] = m[Y0 - y0:Y1 - y0, X0 - x0:X1 - x0]
    return out


def ellipse_mask(w, h, cx, cy, rx, ry):
    yy, xx = grid(h, w)
    return ((xx + 0.5 - cx) / max(rx, 0.5)) ** 2 + ((yy + 0.5 - cy) / max(ry, 0.5)) ** 2 <= 1.0


def rrect_mask(w, h, x0, y0, x1, y1, r):
    """Rounded rectangle [x0, x1) x [y0, y1) with corner radius r."""
    yy, xx = grid(h, w)
    cx = np.clip(xx + 0.5, x0 + r, x1 - r)
    cy = np.clip(yy + 0.5, y0 + r, y1 - r)
    inside = (xx >= x0) & (xx < x1) & (yy >= y0) & (yy < y1)
    return inside & (((xx + 0.5 - cx) ** 2 + (yy + 0.5 - cy) ** 2) <= r * r + 0.25)


def blank(w, h, R, name):
    return kit.MLayer(w, h, R, name)


def save(lay_or_arr, rel, prev=None, opaque=False):
    arr = lay_or_arr.c.copy() if hasattr(lay_or_arr, 'c') else lay_or_arr.copy()
    if opaque:
        arr[..., 3] = 255
    path = os.path.join(OUT, rel)
    kit.save_rgba(arr, path)
    return path


def wrap_noise(w, h, cell, seed, octaves=3):
    """Horizontally periodic smooth noise in [0,1] (sum of periodic cosine-interpolated value grids)."""
    rng = np.random.default_rng(seed)
    out = np.zeros((h, w), np.float32)
    amp, tot = 1.0, 0.0
    c = float(cell)
    for _ in range(octaves):
        nx = max(1, int(round(w / c)))
        ny = int(math.ceil(h / c)) + 2
        g = rng.random((ny, nx)).astype(np.float32)
        xs = np.arange(w) / (w / nx)
        ys = np.arange(h) / c
        x0 = np.floor(xs).astype(int); fx = xs - x0
        y0 = np.floor(ys).astype(int); fy = ys - y0
        fx = fx * fx * (3 - 2 * fx); fy = fy * fy * (3 - 2 * fy)
        x1 = (x0 + 1) % nx; x0 = x0 % nx
        a = g[y0[:, None], x0[None, :]]; b = g[y0[:, None], x1[None, :]]
        c0 = g[y0[:, None] + 1, x0[None, :]]; d = g[y0[:, None] + 1, x1[None, :]]
        top = a + (b - a) * fx[None, :]; bot = c0 + (d - c0) * fx[None, :]
        out += amp * (top + (bot - top) * fy[:, None])
        tot += amp
        amp *= 0.5
        c = max(1.0, c / 2)
    return out / tot


def dither_alpha(mask: np.ndarray, density: np.ndarray, x0=0, y0=0) -> np.ndarray:
    """Ordered-dither a soft density (0..1) into a binary mask."""
    h, w = mask.shape
    return mask & (density > pg.bayer(w, h, x0, y0))


def text(s, font='35'):
    return kit.text_mask(s, font)


LAYOUT: dict = {}


# =========================================================================== TRAINS: shared window geometry
# glass opening (identical in both cars -> the match cut lands on the same frame), sash ring around it
GLASS = (172, 84, 468, 226)          # x0, y0, x1, y1 (exclusive)
GLASS_R = 12
SASH = (167, 79, 473, 231)
SASH_R = 16
EXT = (164, 76, 312, 158)            # exterior layer box: x, y, w, h (covers the glass + jolt margin)
STRIP_W = 640                        # tileable exterior strips
COLD = V['night'] + V['slate'] + V['snow'][1:]          # 0..13, monotonic luminance
LAYOUT['trains'] = {'glass': GLASS, 'glass_r': GLASS_R, 'sash': SASH, 'ext': EXT, 'strip_w': STRIP_W}


def glass_mask(w=VW, h=VH, ox=0, oy=0):
    x0, y0, x1, y1 = GLASS
    return rrect_mask(w, h, x0 - ox, y0 - oy, x1 - ox, y1 - oy, GLASS_R)


# =========================================================================== TRAINS: exterior (night plain)
def ext_sky():
    """Overcast night over the plain; the low cloud is lit from below by the floodlit Line."""
    R = ramps(C=COLD)
    x, y, w, h = EXT
    lay = blank(w, h, R, 'ext_sky')
    yy, xx = grid(h, w, x, y)
    t = 1.3 + 4.4 * np.clip((yy - 86) / 92, 0, 1) ** 1.8
    n = pg.value_noise(w, h, 26, 51, octaves=3)
    band = np.clip(1 - np.abs(yy - 118) / 40, 0, 1)
    t += (n - 0.5) * (0.8 + 0.8 * band)
    # flat stratus undersides catching the glow
    rng = np.random.default_rng(52)
    for _ in range(7):
        by = rng.uniform(118, 160); x0 = rng.uniform(-40, w); ln = rng.uniform(60, 180)
        thick = rng.uniform(1.5, 3.5)
        m = (np.abs(yy - by - 0.02 * (xx - x - x0)) < thick) & (xx - x > x0) & (xx - x < x0 + ln)
        t[m] += 0.55
    lay.put(np.ones((h, w), bool), 0, 0, 'C', t)
    lay.resolve(band=2.6)
    return lay


def ext_far(side='de'):
    """The Line: a double fence on the horizon, floodlight masts, towers, the lit strip.
    side 'de' = seen from the west (Konrad), 'su' = seen from the east (Alexei).  Tileable (STRIP_W)."""
    R = ramps(C=COLD)
    w, y0, h = STRIP_W, 136, 58               # abs rows 136..193
    lay = blank(w, h, R, 'ext_far_' + side)
    yy, xx = grid(h, w, 0, y0)
    rng = np.random.default_rng(61 if side == 'de' else 62)
    nz = wrap_noise(w, 4, 18, 63)[0]
    # land beyond the Line (dark treeline), its top ragged
    top = 169 + (nz * 4).astype(int) + (wrap_noise(w, 1, 4, 64)[0] * 2).astype(int)
    land = yy >= top[None, :]
    lay.put(land, 0, 0, 'C', 2.4 + (yy - 170) * 0.05)
    # floodlight masts on the near fence
    fence_y, far_fence_y = 180, 175
    masts = []
    x = 18.0
    while x < w - 8:
        masts.append(int(x))
        x += rng.uniform(70, 92)
    # lit strip between the fences + the snow in front of the near fence (cones from each lamp)
    lit = np.zeros((h, w), np.float32)
    for mx in masts:
        for dx in (-w, 0, w):
            d = np.abs(xx - (mx + dx))
            cone = np.clip(1 - d / (10 + (yy - 150) * 0.9), 0, 1) * (yy >= far_fence_y) * (yy <= 192)
            lit = np.maximum(lit, cone * np.clip(1 - (yy - 181) / 12, 0.25, 1))
    strip = (yy >= far_fence_y) & (yy <= 192)
    lay.put(strip, 0, 0, 'C', 5.2 + lit * 6.2 - np.clip(yy - 183, 0, 9) * 0.3)
    # fence lines + posts (tiny at this distance)
    lay.rect(0, far_fence_y - y0, w, 1, 'C', 3.0, flat=True)
    px_ = 0
    while px_ < w:
        lay.rect(px_, far_fence_y - 2 - y0, 1, 2, 'C', 2.6, flat=True)
        px_ += 5 + (px_ * 7 % 3)
    lay.rect(0, fence_y - 1 - y0, w, 1, 'C', 1.6, flat=True)
    lay.rect(0, fence_y - 4 - y0, w, 1, 'C', 2.4, flat=True)
    px_ = 2
    while px_ < w:
        lay.rect(px_, fence_y - 5 - y0, 1, 5, 'C', 1.4, flat=True)
        px_ += 6 + (px_ * 5 % 3)
    # halos first (dithered glow in the haze around every lamp head), then the masts on top
    heights = [int(rng.uniform(26, 31)) for _ in masts]
    for mx, ht in zip(masts, heights):
        ytop = fence_y - ht
        for dx in (-w, 0, w):
            d = np.hypot((xx - mx - dx) / 13.0, (yy - ytop - 2) / 8.0)
            g = np.clip(1 - d, 0, 1) ** 1.4
            sub = (g > 0.02) & ~land & (g * 1.15 > pg.bayer(w, h, 0, y0))
            val = 5.4 + g * 3.0
            empty = sub & (lay.rid < 0)
            lay.put(empty, 0, 0, 'C', val)
            full = sub & (lay.rid >= 0)
            lay.tone[full] = np.maximum(lay.tone[full], val[full])
    for i, mx in enumerate(masts):
        ht = heights[i]
        ytop = fence_y - ht
        lay.rect(mx, ytop - y0, 1, ht, 'C', 1.6, flat=True)
        if side == 'de':
            lay.rect(mx - 2, ytop - y0, 5, 2, 'C', 2.0, flat=True)        # box floodlights angled down
            lay.rect(mx - 2, ytop + 2 - y0, 2, 1, 'C', 13.0, flat=True)
            lay.rect(mx + 1, ytop + 2 - y0, 2, 1, 'C', 13.0, flat=True)
        else:
            lay.rect(mx - 1, ytop - 1 - y0, 3, 2, 'C', 2.0, flat=True)    # backs of the lamps (seen from behind)
            lay.px(mx - 2, ytop + 1 - y0, 'C', 11.0, flat=True)
            lay.px(mx + 2, ytop + 1 - y0, 'C', 11.0, flat=True)
        masts[i] = (mx, ytop)
    # watchtowers
    towers = []
    for k in range(2):
        tx = int(150 + k * 320 + rng.uniform(-20, 20))
        base = fence_y - 1
        lay.rect(tx - 2, base - 14 - y0, 1, 14, 'C', 1.4, flat=True)
        lay.rect(tx + 4, base - 14 - y0, 1, 14, 'C', 1.4, flat=True)
        lay.line(tx - 2, base - 1 - y0, tx + 4, base - 13 - y0, 'C', 1.4, flat=True)
        cab_y = base - 21
        lay.rect(tx - 4, cab_y - y0, 11, 7, 'C', 1.2, flat=True)
        if side == 'de':
            lay.rect(tx - 5, cab_y - 1 - y0, 13, 1, 'C', 1.8, flat=True)             # flat concrete roof
        else:
            lay.poly([(tx - 5, cab_y - y0), (tx + 1.5, cab_y - 5 - y0), (tx + 8, cab_y - y0)], 'C', 1.6)
        lay.rect(tx - 2, cab_y + 2 - y0, 2, 2, 'C', 9.0, flat=True)                  # lit slit
        lay.rect(tx + 2, cab_y + 2 - y0, 2, 2, 'C', 7.0, flat=True)
        towers.append([tx + 1, cab_y + 4 - y0])
    lay.resolve(band=3.0)
    LAYOUT['trains']['masts_' + side] = masts
    LAYOUT['trains']['towers_' + side] = towers
    return lay


def ext_mid():
    """The snow plain in front of the Line (tileable).  Bushes, birches, an old field fence, a cleared farm."""
    R = ramps(C=COLD)
    w, y0, h = STRIP_W, 186, 46               # abs rows 186..231
    lay = blank(w, h, R, 'ext_mid')
    yy, xx = grid(h, w, 0, y0)
    rng = np.random.default_rng(71)
    edge = 188 + (wrap_noise(w, 1, 30, 72)[0] * 2.5).astype(int)
    m = yy >= edge[None, :]
    depth = np.clip((yy - 188) / 38, 0, 1)                        # 0 far .. 1 near
    t = 5.7 - depth * 2.5 + depth ** 2 * 1.3
    drift = wrap_noise(w, h, 40, 73, octaves=3)
    crest = np.sin((yy - 188) * 0.55 + drift * 9.0)
    t += np.where(crest > 0.86, 0.75, 0.0) - np.where(crest < -0.9, 0.45, 0.0)
    t += (drift - 0.5) * 0.8
    lay.put(m, 0, 0, 'C', t)
    # old field fence (posts + one sagging wire)
    fy = 199
    for px_ in range(3, w, 11):
        hgt = 3 + (px_ * 7) % 2
        lay.rect(px_, fy - hgt - y0, 1, hgt, 'C', 1.8, flat=True)
    for px_ in range(w):
        sag = 0.6 * math.sin(math.pi * ((px_ - 3) % 11) / 11)
        lay.px(px_, int(round(fy - 3 + sag)) - y0, 'C', 2.6, flat=True)
    # bushes (bigger when nearer)
    for _ in range(46):
        bx = rng.uniform(0, w); by = rng.uniform(192, 228)
        s = 0.8 + (by - 192) / 36 * 3.4
        for dx in (-w, 0, w):
            for k in range(int(3 + s * 1.2)):
                cx = bx + dx + rng.uniform(-s * 1.4, s * 1.4)
                cy = by - rng.uniform(0, s * 0.9)
                bm = ellipse_mask(w, h, cx, cy - y0, s * rng.uniform(0.5, 0.9), s * rng.uniform(0.4, 0.7))
                lay.put(bm & m, 0, 0, 'C', 1.4 + rng.uniform(0, 0.8))
            # a lit snow cap on the bush top
            lay.px(int(bx + dx), int(by - s) - y0, 'C', 5.6, flat=True)
    # birches: pale trunks with dark bark marks, bare crowns
    for _ in range(9):
        bx = int(rng.uniform(0, w)); by = int(rng.uniform(196, 212))
        th = int(10 + (by - 196) * 0.9 + rng.uniform(0, 5))
        for dx in (-w, 0, w):
            X = bx + dx
            lay.rect(X, by - th - y0, 1, th, 'C', 7.0, flat=True)
            for k in range(2, th, 3):
                lay.px(X, by - k - y0, 'C', 2.0, flat=True)
            for k in range(5):
                a = rng.uniform(-2.4, -0.7)
                ln = rng.uniform(3, 7)
                sy = by - th + rng.uniform(0, th * 0.4)
                lay.line(X, sy - y0, X + math.cos(a) * ln, sy + math.sin(a) * ln - y0, 'C', 1.8, flat=True)
    # a cleared farmstead (no light): broken roof, dead tree
    fx = 412
    for dx in (-w, 0, w):
        X = fx + dx
        lay.rect(X, 189 - y0 + 4, 26, 8, 'C', 1.4, flat=True)
        lay.poly([(X - 2, 193 - y0), (X + 9, 186 - y0), (X + 14, 190 - y0), (X + 17, 187 - y0),
                  (X + 28, 193 - y0)], 'C', 1.0)
        lay.rect(X + 5, 196 - y0, 3, 3, 'C', 0.4, flat=True)
        lay.rect(X + 15, 196 - y0, 3, 3, 'C', 0.4, flat=True)
        lay.rect(X + 21, 182 - y0, 1, 11, 'C', 1.0, flat=True)
        for (a, ln) in ((-2.2, 6), (-1.0, 5), (-0.5, 4), (-2.7, 4)):
            lay.line(X + 21, 185 - y0, X + 21 + math.cos(a) * ln, 185 + math.sin(a) * ln - y0, 'C', 1.0, flat=True)
    lay.resolve(band=3.0)
    return lay


def ext_near():
    """Snow on the embankment right beside the track (fast parallax: horizontal streaks only)."""
    R = ramps(C=COLD)
    w, y0, h = STRIP_W, 212, 20               # abs rows 212..231
    lay = blank(w, h, R, 'ext_near')
    yy, xx = grid(h, w, 0, y0)
    top = 216 + (wrap_noise(w, 1, 16, 81)[0] * 5).astype(int)
    m = yy >= top[None, :]
    streak = wrap_noise(w, h, 64, 82, octaves=2)
    fine = wrap_noise(w, h, 9, 83, octaves=2)
    t = 5.4 - (yy - 216) * 0.12 + (streak - 0.5) * 1.4 + (fine - 0.5) * 0.5
    lay.put(m, 0, 0, 'C', t)
    # crest highlight on the mound tops, dark ballast flecks low down
    crest = m & ~shift(m, 0, -1) & (streak > 0.45)
    lay.put(crest, 0, 0, 'C', 6.8, flat=True)
    rng = np.random.default_rng(84)
    for _ in range(130):
        x = int(rng.integers(0, w)); y = int(rng.integers(224, 232)) - y0
        if m[y, x]:
            lay.rect(x, y, int(rng.integers(2, 6)), 1, 'C', 3.0, flat=True)
    lay.resolve(band=3.0)
    return lay


def pole():
    """Telegraph pole passing close to the window (dark wood, two crossarms with insulators)."""
    R = ramps(C=COLD, L=['#0C111C', '#22150F', '#331F16', '#4A2D1F', '#63402C'])
    w, h = 24, 160                             # abs rows 74..233, x centred on col 12
    lay = blank(w, h, R, 'pole')
    y0 = 74
    lay.rect(9, 0, 6, h, 'C', 0.4, flat=True)
    lay.rect(14, 0, 1, h, 'C', 1.6, flat=True)                      # cold edge from the Line glow
    lay.rect(9, 0, 1, h, 'C', 1.0, flat=True)
    for k in range(0, h, 9):                                        # wood checks
        lay.rect(11, k + (k * 7) % 5, 1, 3, 'C', 1.0, flat=True)
    yy = np.arange(h)[:, None] + y0
    warm = np.clip((yy - 168) / 62, 0, 1)[:, 0]
    for k in range(h):
        if warm[k] > 0.1:
            lay.rect(9, k, 3, 1, 'L', 0.4 + warm[k] * 2.0)          # train-window light on the low pole
    # crossarms (seen nearly end-on) with glass insulators
    for (cy, ln) in ((92, 22), (104, 16)):
        lay.rect(12 - ln // 2, cy - y0, ln, 3, 'C', 0.6, flat=True)
        lay.rect(12 - ln // 2, cy - y0, ln, 1, 'C', 2.2, flat=True)
        for ix in (12 - ln // 2 + 1, 12 + ln // 2 - 3):
            lay.rect(ix, cy - 4 - y0, 2, 4, 'C', 7.0, flat=True)
            lay.rect(ix, cy - 4 - y0, 1, 1, 'C', 10.0, flat=True)
        lay.line(12 - ln // 2 + 2, cy + 3 - y0, 10, cy + 9 - y0, 'C', 0.8, flat=True)    # brace
        lay.line(12 + ln // 2 - 3, cy + 3 - y0, 14, cy + 9 - y0, 'C', 0.8, flat=True)
    for k in range(5, h, 21):                                       # snow stuck on the windward side
        lay.rect(14, k, 1, 2, 'C', 6.0, flat=True)
    lay.resolve(band=2.0)
    LAYOUT['trains']['pole'] = {'w': w, 'h': h, 'y': y0, 'cx': 12,
                                'insulators': [[2, 14], [20, 14], [5, 26], [17, 26]]}
    return lay


# =========================================================================== painting helpers (figures, light)
def blur(a: np.ndarray, r: int) -> np.ndarray:
    """Separable box blur (edge clamped)."""
    if r <= 0:
        return a.astype(np.float32)
    a = a.astype(np.float32)
    for axis in (0, 1):
        p = np.pad(a, [(r, r) if i == axis else (0, 0) for i in range(2)], mode='edge')
        c = np.cumsum(p, axis=axis, dtype=np.float64)
        c = np.concatenate([np.zeros_like(np.take(c, [0], axis=axis)), c], axis=axis)
        n = a.shape[axis]
        hi = np.take(c, np.arange(2 * r + 1, 2 * r + 1 + n), axis=axis)
        lo = np.take(c, np.arange(0, n), axis=axis)
        a = ((hi - lo) / (2 * r + 1)).astype(np.float32)
    return a


def edge_light(mask: np.ndarray, light, width: float = 4.0, soft: int = 2) -> np.ndarray:
    """0..1 lighting of a flat silhouette's rounded edge facing `light` (2D direction, y down);
    fades inward over `width` px -> pixel-art 'form' rims instead of a hard outline."""
    d = dist_inside(mask, int(width) + 6)
    ds = blur(d, soft)
    gy, gx = np.gradient(ds)
    L = np.asarray(light, np.float32)
    L = L / (np.linalg.norm(L) + 1e-6)
    # distance grows inward -> outward normal = -grad
    nrm = np.sqrt(gx * gx + gy * gy) + 1e-6
    lam = np.clip((-gx * L[0] - gy * L[1]) / nrm, 0, 1)
    fall = np.clip(1 - (d - 1) / width, 0, 1)
    return (lam * fall * mask).astype(np.float32)


def point_light(h, w, lx, ly, radius, x0=0, y0=0, power=1.4):
    yy, xx = grid(h, w, x0, y0)
    return np.clip(1 - np.hypot(xx + 0.5 - lx, yy + 0.5 - ly) / radius, 0, 1) ** power


def stroke(w, h, pts, r, jitter=0.0, seed=0, ox=0, oy=0):
    return kit.stroke_mask(w, h, [[(x - ox, y - oy) for (x, y) in kit.smooth_poly(pts, 6)]], r, jitter=jitter,
                           seed=seed)


class Paint:
    """Small helper around an MLayer in absolute frame coordinates with a local origin."""

    def __init__(self, w, h, R, name, ox=0, oy=0):
        self.L = kit.MLayer(w, h, R, name)
        self.w, self.h, self.ox, self.oy = w, h, ox, oy
        self.yy, self.xx = grid(h, w, ox, oy)

    def poly(self, pts):
        return poly_mask(self.w, self.h, [(x - self.ox, y - self.oy) for (x, y) in pts])

    def ell(self, cx, cy, rx, ry):
        return ellipse_mask(self.w, self.h, cx - self.ox, cy - self.oy, rx, ry)

    def rr(self, x0, y0, x1, y1, r):
        return rrect_mask(self.w, self.h, x0 - self.ox, y0 - self.oy, x1 - self.ox, y1 - self.oy, r)

    def box(self, x0, y0, x1, y1):
        m = np.zeros((self.h, self.w), bool)
        X0, Y0 = max(0, int(x0 - self.ox)), max(0, int(y0 - self.oy))
        X1, Y1 = min(self.w, int(x1 - self.ox)), min(self.h, int(y1 - self.oy))
        if X1 > X0 and Y1 > Y0:
            m[Y0:Y1, X0:X1] = True
        return m

    def line(self, pts, r=0.5, jitter=0.0, seed=0):
        return stroke(self.w, self.h, pts, r, jitter, seed, self.ox, self.oy)

    def put(self, mask, ramp, tone, **kw):
        if not np.isscalar(tone):
            tone = np.asarray(tone, np.float32)
            if tone.ndim == 1:                       # values already selected by the mask
                full = np.zeros((self.h, self.w), np.float32)
                full[mask] = tone
                tone = full
            elif tone.shape != (self.h, self.w):
                tone = np.broadcast_to(tone, (self.h, self.w)).astype(np.float32)
        self.L.put(mask, 0, 0, ramp, tone, **kw)

    def add(self, mask, dt, only=None):
        m = mask & (self.L.rid >= 0)
        if only is not None:
            m &= np.isin(self.L.rid, [self.L.R[o] for o in only])
        self.L.tone[m] += dt[m] if not np.isscalar(dt) else dt

    def px(self, x, y, ramp, tone):
        self.L.px(int(x - self.ox), int(y - self.oy), ramp, tone, flat=True)

    def resolve(self, band=2.6):
        self.L.resolve(band=band)
        return self.L


# =========================================================================== TRAINS: the shared sash ring
def paint_sash(p: Paint, ramp='I'):
    """The iron window sash around the glass -- painted identically in both cars (the match-cut anchor)."""
    x0, y0, x1, y1 = SASH
    ring = p.rr(x0, y0, x1, y1, SASH_R) & ~p.rr(*GLASS, GLASS_R)
    yy = p.yy
    p.put(ring, ramp, 2.2 - np.clip((yy - 80) / 150, 0, 1) * 0.4, flat=True)
    inner = ring & kit.dilate(p.rr(*GLASS, GLASS_R), 1)
    outer = ring & ~kit.erode(p.rr(x0, y0, x1, y1, SASH_R), 1)
    p.put(outer, ramp, 0.9, flat=True)
    p.put(inner, ramp, 4.6, flat=True)
    # the exterior light catches the lower inner lip a little more (snow below)
    lip = inner & (yy > 200)
    p.put(lip, ramp, 5.6, flat=True)
    # rubber seal: a dark line just outside the inner lip
    seal = ring & kit.dilate(inner, 1) & ~inner
    p.put(seal, ramp, 1.0, flat=True)
    return ring


def punch_glass(p: Paint):
    g = p.rr(*GLASS, GLASS_R)
    p.L.rid[g] = -1
    return g


# =========================================================================== TRAINS: Konrad's saloon car
K_LAMP = (330, 209)


def ramps_k():
    return ramps(
        W=['#070A12', '#0C111C', '#22150F', '#331F16', '#4A2D1F', '#63402C', '#7E553B', '#A8643A', '#D08F55',
           '#EDB777'],
        B=['#0C111C', '#4A3415', '#73531F', '#9C7630', '#C49A48', '#E8C779', '#FCE2B0'],
        V=['#070A12', '#0A1016', '#10181F', '#172229', '#1E302E', '#2B4541', '#3D5E57', '#56796E'],
        I=['#070A12', '#15171C', '#22262D', '#323840', '#464D55', '#5E666E', '#8593A3', '#C2C9D2'],
        L=['#4A2D1F', '#6E3F22', '#A8643A', '#D08F55', '#EDB777', '#FCE2B0'],
        P=['#22150F', '#4A4236', '#645A49', '#80745E', '#9E9076', '#BBAD8F', '#D6CBAE', '#FCE2B0'],
        H=K_HAT, K=K_COAT, F=SKIN, Y=K_SCARF, C=COLD)


def lamp_field_k(p: Paint):
    """Warm light of the table lamp: strong below the shade, weak above it (the shade blocks it)."""
    f = point_light(p.h, p.w, K_LAMP[0], K_LAMP[1], 270, p.ox, p.oy, power=1.25)
    above = np.clip((K_LAMP[1] - 8 - p.yy) / 40, 0, 1)
    return f * (1 - 0.55 * above)


def wood_panels(p: Paint, rects, lamp, seed):
    """Framed mahogany panels with a light inlay line (Art-Deco saloon car)."""
    rng = np.random.default_rng(seed)
    for (x0, y0, x1, y1) in rects:
        box = p.box(x0, y0, x1, y1)
        grain = pg.value_noise(p.w, max(2, p.h // 7 + 2), 3, int(rng.integers(1 << 20)), octaves=2)
        grain = np.repeat(grain, 7, axis=0)[:p.h]
        p.put(box, 'W', 2.7 + lamp * 5.2 + (grain - 0.5) * 0.7)
        # moulding: top/left catch light, bottom/right in shadow
        p.add(box & ~shift(box, 0, -1), 1.3)
        p.add(box & ~shift(box, -1, 0), 0.9)
        p.add(box & ~shift(box, 0, 1), -1.2)
        p.add(box & ~shift(box, 1, 0), -0.9)
        inl = p.box(x0 + 6, y0 + 6, x1 - 6, y1 - 6)
        inl &= ~kit.erode(inl, 1)
        p.add(inl, 1.6)


def int_konrad():
    R = ramps_k()
    p = Paint(VW, VH, R, 'int_konrad')
    yy, xx = p.yy, p.xx
    lamp = lamp_field_k(p)
    allm = np.ones((VH, VW), bool)
    # ---- wall: dark mahogany with vertical grain, darker toward the ceiling
    g = np.repeat(pg.value_noise(VW, VH // 6 + 2, 2, 201, octaves=2), 6, axis=0)[:VH]
    p.put(allm, 'W', 2.3 + lamp * 5.0 + (g - 0.5) * 0.6 - np.clip((90 - yy) / 60, 0, 1) * 0.8)
    wood_panels(p, [(6, 70, 58, 234), (64, 70, 116, 234), (526, 70, 578, 234), (584, 70, 636, 234),
                    (6, 262, 116, 330), (526, 262, 636, 330)], lamp, 202)
    # ---- window moulding (outer frame) with a lit bevel toward the lamp
    frame = p.rr(152, 64, 488, 248, 28) & ~p.rr(*SASH, SASH_R)
    p.put(frame, 'W', 3.0 + lamp * 5.6)
    bevel = frame & kit.dilate(p.rr(*SASH, SASH_R), 3)
    cx, cy = 320, 155
    facing = np.clip(((yy - cy) / 90.0) * 0.9 + 0.1, -1, 1)       # bottom bevel faces the lamp/table
    p.add(bevel, (facing * 1.6 + 0.4) * (0.5 + lamp))
    groove = frame & kit.dilate(p.rr(*SASH, SASH_R), 4) & ~kit.dilate(p.rr(*SASH, SASH_R), 3)
    p.add(groove, -1.6)
    outer_edge = frame & ~kit.erode(p.rr(152, 64, 488, 248, 28), 1)
    p.add(outer_edge, -1.4)
    # brass corner rosettes on the moulding
    for (bx, by) in ((162, 74), (476, 74), (162, 236), (476, 236)):
        m = p.ell(bx + 0.5, by + 0.5, 3.2, 3.2)
        p.put(m, 'B', 2.2 + point_light(VH, VW, *K_LAMP, 260)[m] * 3.5)
        p.px(bx - 1, by - 1, 'B', 5.0)
    # ---- velvet curtains (dark teal), tied back; they never overlap the sash
    for side in (-1, 1):
        if side < 0:
            xa, xb, tie_x = 114, 166, 150
        else:
            xa, xb, tie_x = 474, 526, 490
        top, tie_y, bottom = 66, 196, 272
        pts = []
        for yv in range(top, bottom + 1, 2):
            if yv <= tie_y:
                u = (yv - top) / (tie_y - top)
                a = xa + (tie_x - 10 - xa) * u ** 2.2 if side < 0 else xa
                b = xb if side < 0 else xb - (xb - (tie_x + 10)) * u ** 2.2
            else:
                u = (yv - tie_y) / (bottom - tie_y)
                a = (tie_x - 10 - (tie_x - 10 - xa) * u ** 0.6) if side < 0 else xa
                b = xb if side < 0 else (tie_x + 10 + (xb - tie_x - 10) * u ** 0.6)
            pts.append((a, yv, b))
        left = [(a, yv) for (a, yv, b) in pts]
        right = [(b, yv) for (a, yv, b) in reversed(pts)]
        cm = p.poly(left + right)
        folds = np.sin((xx - xa) * 0.62 + np.sin(yy * 0.05) * 1.2)
        tone = 2.0 + lamp * 4.2 + folds * 0.9
        tone += np.clip((yy - tie_y) / 60, 0, 1) * 0.3
        p.put(cm, 'V', tone)
        sheen = cm & (folds > 0.82)
        p.add(sheen, 0.9)
        # gold cord tie-back: a sagging loop around the gathered velvet, a small tassel hanging from it
        cord = p.line([(tie_x - 12, tie_y - 3), (tie_x - 4, tie_y + 1), (tie_x + 4, tie_y + 1),
                       (tie_x + 12, tie_y - 3)], 0.7) & cm
        p.put(cord, 'B', 2.2 + lamp * 2.6)
        p.add(cm & shift(cord, 0, -1) & ~cord, -0.8)
        tx = tie_x + (7 if side < 0 else -7)
        p.put(p.line([(tx, tie_y), (tx, tie_y + 7)], 0.5), 'B', 2.0)
        p.put(p.poly([(tx - 1.5, tie_y + 7), (tx + 1.5, tie_y + 7), (tx + 2.5, tie_y + 13), (tx - 2.5, tie_y + 13)]),
              'B', 2.4 + lamp * 1.5)
    # curtain rod
    p.put(p.box(104, 63, 536, 65), 'B', 2.6)
    p.put(p.box(104, 63, 536, 64), 'B', 3.6)
    # ---- luggage rack: two brass rods, a net, brackets; the drafting tube and a suitcase on it
    for bx in (122, 516):
        p.put(p.box(bx - 2, 50, bx + 2, 80), 'B', 1.8)
        p.put(p.line([(bx, 62), (bx + (12 if bx < 300 else -12), 78)], 0.6), 'B', 2.6)
    net = p.box(118, 53, 522, 61) & (((xx.astype(int) + yy.astype(int)) % 4 == 0) |
                                    ((xx.astype(int) - yy.astype(int)) % 4 == 0))
    p.put(net, 'W', 1.4)
    p.put(p.box(116, 52, 524, 53), 'B', 2.2)
    # suitcase (only its lower part shows under the letterbox)
    case = p.rr(384, 36, 474, 60, 3)
    p.put(case, 'W', 3.6 + lamp * 3.0)
    p.add(case & (yy > 57), -1.0)
    for sx in (404, 452):
        p.put(p.box(sx, 36, sx + 4, 60) & case, 'W', 2.2)
        p.put(p.box(sx, 54, sx + 4, 57), 'B', 3.4)
    p.put(p.box(384, 58, 474, 60) & case, 'B', 2.0)
    # the drafting tube: a long cylinder in dark leather with brass caps, a strap with a buckle
    tube = p.rr(166, 48, 352, 61, 5)
    cyl = np.clip((yy - 48) / 13, 0, 1)
    shade = 0.8 + np.sin(cyl * math.pi) * 1.6 + cyl * 0.9
    p.put(tube, 'H', shade + lamp * 2.0)
    p.put(tube & (np.abs(yy - 59.5) < 0.6), 'C', 6.0)               # cold rim from the glass below
    for (c0, c1) in ((166, 173), (345, 352)):
        cap = tube & p.box(c0, 46, c1, 63)
        p.put(cap, 'B', 1.8 + np.sin(cyl * math.pi) * 2.2)
        p.put(cap & (np.abs(xx - (c0 + 2)) < 0.6), 'B', 4.6)
    strap = p.line([(206, 60), (226, 70), (258, 74), (290, 70), (306, 60)], 0.7)
    p.put(strap, 'W', 2.2)
    p.put(p.line([(206, 49), (206, 60)], 0.6) | p.line([(306, 49), (306, 60)], 0.6), 'W', 2.0)
    p.put(p.box(254, 72, 260, 76), 'B', 3.6)
    tag = p.poly([(232, 70), (240, 69), (241, 78), (233, 79)])
    p.put(tag, 'P', 4.6 + lamp[tag].mean() * 2)
    p.put(p.line([(236, 70), (238, 74)], 0.4), 'P', 2.0)
    # the front rail in front of everything on the rack
    p.put(p.box(114, 61, 526, 64), 'B', 2.4)
    p.put(p.box(114, 61, 526, 62), 'B', 4.2)
    # ---- table under the window: polished top, brass edge, apron, shadow
    top = p.box(168, 236, 472, 244)
    p.put(top, 'W', 3.8 + lamp * 6.2)
    refl = p.ell(330, 239.5, 26, 2.6)                                 # lamp reflected in the polish
    p.add(refl & top, 1.4)
    p.put(top & (yy < 237), 'C', 3.4 + np.clip(1 - np.abs(xx - 320) / 200, 0, 1) * 2.0)   # cold window sheen
    p.put(p.box(168, 244, 472, 246), 'B', 2.4 + lamp[244:246, :].mean() * 4 + 0.0)
    p.put(p.box(168, 244, 472, 245), 'B', 3.4 + lamp[244, :][None, :].repeat(1, 0) * 0 + 1.0)
    p.put(p.box(168, 246, 472, 254), 'W', 2.6 + lamp * 4.0)
    p.put(p.box(168, 254, 472, 262), 'W', 1.2)
    # ---- leather folder (mostly behind Konrad)
    fold = p.box(386, 236, 456, 242)
    p.put(fold, 'W', 2.4 + lamp * 3.0)
    p.put(p.box(386, 236, 456, 237), 'W', 4.0)
    p.put(p.box(418, 238, 421, 240), 'B', 4.2)
    # ---- heater grille under the table
    grille = p.box(176, 270, 464, 302)
    p.put(grille, 'W', 1.0)
    for gy in range(271, 302, 3):
        sl = p.box(178, gy, 462, gy + 1)
        p.put(sl, 'B', 1.8 + lamp * 3.0)
    p.put(p.box(176, 268, 464, 270), 'B', 2.8 + lamp * 2.0)
    # ---- the sash (identical in both cars) and the glass hole
    paint_sash(p)
    punch_glass(p)
    # the lamp stands in front of the glass -> painted after the punch
    # ---- the reading lamp: brass foot, stem, pleated silk shade glowing
    p.put(p.ell(330, 236.5, 8.5, 2.6), 'B', 3.2)
    p.put(p.ell(330, 235.8, 6, 1.4), 'B', 4.8)
    p.put(p.box(329, 214, 331, 236), 'B', 3.0)
    p.put(p.box(329, 214, 330, 236), 'B', 4.6)
    shade = p.poly([(322, 197), (338, 197), (346, 214), (314, 214)])
    pleat = 3.0 + (np.sin(xx * 1.4) > 0.3) * 0.7 + np.clip((yy - 197) / 17, 0, 1) * 0.9
    p.put(shade, 'L', pleat, emis=True)
    p.put(shade & (yy < 199), 'L', 2.2, emis=True)
    p.put(p.box(314, 213, 347, 215), 'L', 5.0, emis=True)
    p.put(p.box(323, 215, 338, 216), 'L', 5.0, emis=True)
    # ---- coffee cup on its saucer (the counterpart of Alexei's tea glass), in front of the glass
    cx_ = K_CUP[0]
    p.put(p.ell(cx_, 236.8, 11, 2.4), 'P', 4.2 + lamp[236, cx_] * 1.0)
    p.put(p.ell(cx_, 236.2, 9, 1.4), 'P', 5.6)
    cup = p.poly([(cx_ - 7, 226), (cx_ + 7, 226), (cx_ + 6, 233), (cx_ + 3, 236), (cx_ - 3, 236), (cx_ - 6, 233)])
    p.put(cup, 'P', 6.4 - np.clip((xx - (cx_ - 6)) / 13, 0, 1) * 3.0)
    p.put(p.box(cx_ - 7, 226, cx_ + 8, 227), 'B', 4.4)
    p.put(p.ell(cx_, 226.9, 6, 0.9), 'W', 2.2)
    p.put(p.line([(cx_ + 7, 228), (cx_ + 10, 229), (cx_ + 10, 232), (cx_ + 6, 233)], 0.5), 'P', 3.4)
    paint_reach_k(p, lamp)
    # overall falloff to the frame edges (night interior)
    p.L.amb_field(-np.clip(np.hypot((xx - 330) / 420, (yy - 200) / 260) - 0.35, 0, 1) * 2.4)
    p.resolve(band=2.6)
    return p.L


K_CUP = (352, 236)


def paint_reach_k(p: Paint, lamp):
    """Konrad's left forearm on the table: from behind his body (right) to the cup handle by the window.
    Coat sleeve, white shirt cuff, the back of the hand warm in the lamp light, fingers round the handle."""
    yy, xx = p.yy, p.xx
    hx = K_CUP[0] + 9                                   # the handle
    sleeve = p.poly([(hx + 10, 225), (hx + 22, 222), (hx + 42, 233), (hx + 44, 250), (hx + 30, 252), (hx + 12, 236)])
    p.put(sleeve, 'K', 1.0 + lamp * 1.6)
    top = sleeve & ~shift(sleeve, 0, -1)
    p.put(top, 'K', 3.2 + lamp * 1.2)
    p.put(sleeve & ~shift(sleeve, -1, 0) & (yy < 238), 'L', 1.4 + lamp * 1.2)      # lamp rim on the cuff side
    p.add(p.line([(hx + 20, 229), (hx + 36, 240)], 0.5) & sleeve, -0.6)              # fold along the forearm
    cuff = p.poly([(hx + 6, 227), (hx + 11, 225), (hx + 14, 235), (hx + 9, 237)])
    p.put(cuff, 'P', 4.6 + lamp * 0.8)
    p.put(cuff & ~shift(cuff, 1, 0), 'P', 2.8)
    hand = p.poly([(hx - 1, 228), (hx + 3, 226), (hx + 8, 227), (hx + 10, 234), (hx + 5, 236), (hx, 235)])
    p.put(hand, 'F', 2.4 + lamp * 1.4)
    p.put(hand & ~shift(hand, 0, -1), 'F', 4.6)                                    # knuckles catch the lamp
    p.put(hand & ~shift(hand, -1, 0), 'F', 4.0)
    for fy in (230, 232):
        p.px(hx + 1, fy, 'F', 1.2)                                                 # fingers round the handle
    p.px(hx - 1, 231, 'F', 3.2)


# ---------------------------------------------------------------- Konrad (seated, seen from behind-right)
FIG_K = (363, 88, 200, 232)          # frame box x, y, w, h (absolute), 4 frames side by side


def _breath(img):
    """The same frame with chest and shoulders 1 px higher (the bottom row repeats)."""
    out = np.empty_like(img)
    out[:-1] = img[1:]
    out[-1] = img[-1]
    return out


def _sheet4(f0, f1):
    """[turn0, turn0 + breath, turn1, turn1 + breath] side by side."""
    return np.concatenate([f0, _breath(f0), f1, _breath(f1)], axis=1)


def fig_konrad():
    import env_veltrava_cine_figs as F
    f0 = F.back_konrad(0)['rgba']
    f1 = F.back_konrad(1)['rgba']
    LAYOUT['trains']['fig_konrad'] = [FIG_K[0], FIG_K[1]]
    LAYOUT['trains']['fig_frames'] = 4
    return _sheet4(f0, f1)


def _glass_reflection(face_rgba, at, extra, fade_from, fade_len):
    """Full-frame additive reflection: the posterised face (top-left at `at`) fading out below `fade_from`,
    plus `extra` (h, w, 3) float light (lamp, tea glass), all clipped to the glass and dithered."""
    a = extra.astype(np.float32).copy()
    fh, fw = face_rgba.shape[:2]
    x0, y0 = at
    yy, xx = grid(VH, VW)
    face = np.zeros((VH, VW, 3), np.float32)
    X0, Y0, X1, Y1 = max(0, x0), max(0, y0), min(VW, x0 + fw), min(VH, y0 + fh)
    face[Y0:Y1, X0:X1] = face_rgba[Y0 - y0:Y1 - y0, X0 - x0:X1 - x0, :3]
    fall = np.clip(1 - (yy - fade_from) / fade_len, 0.15, 1.0)[..., None]
    a += face * fall
    a[~glass_mask()] = 0
    q = np.floor(a / 4.0 + pg.bayer(VW, VH)[..., None]) * 4.0
    out = np.zeros((VH, VW, 4), np.uint8)
    out[..., :3] = np.clip(q, 0, 255).astype(np.uint8)
    out[..., 3] = np.where(out[..., :3].max(-1) > 0, 255, 0)
    return out


def refl_konrad():
    """Additive reflection in the black glass: Konrad's lamp-lit face, the lamp, the table edge and cup."""
    import env_veltrava_cine_figs as F
    face = F.reflection(F.face_konrad(0), (54, 38, 26), gain=1.25, levels=5)
    yy, xx = grid(VH, VW)
    a = np.zeros((VH, VW, 3), np.float32)
    d = np.hypot((xx - 304) / 14, (yy - 203) / 9)
    for c, v in enumerate((70, 44, 20)):
        a[..., c] += np.clip(1 - d, 0, 1) ** 1.3 * v
    a[ellipse_mask(VW, VH, 304, 205, 5, 2.5)] += (40, 26, 12)
    a[(yy >= 220) & (yy < 225) & (xx > 290) & (xx < 380)] += (14, 9, 4)
    LAYOUT['trains']['refl_face_konrad'] = [358, 104]
    return _glass_reflection(face, (358, 104), a, 158, 26)


def additive_glow(cx, cy, rx, ry, rgb, power=1.5, levels=7, w=None, h=None, ox=0, oy=0):
    """Soft additive glow quantised to a few levels with ordered dither between them."""
    w = w or VW; h = h or VH
    yy, xx = grid(h, w, ox, oy)
    d = np.hypot((xx + 0.5 - cx) / rx, (yy + 0.5 - cy) / ry)
    g = np.clip(1 - d, 0, 1) ** power
    th = pg.bayer(w, h, ox, oy)
    q = np.floor(g * levels + th) / levels
    out = np.zeros((h, w, 4), np.uint8)
    for c in range(3):
        out[..., c] = np.clip(q * rgb[c], 0, 255).astype(np.uint8)
    out[..., 3] = np.where(out[..., :3].max(-1) > 0, 255, 0)
    return out


def glow_lamp():
    x0, y0, w, h = 250, 150, 160, 110
    g = additive_glow(330, 207, 64, 40, (70, 44, 20), power=1.8, w=w, h=h, ox=x0, oy=y0)
    LAYOUT['trains']['glow_lamp'] = [x0, y0]
    return g


def window_patches(rgb, seed):
    """Light falling from the carriage windows onto the snow right outside (additive, static)."""
    x, y, w, h = EXT
    yy, xx = grid(h, w, x, y)
    out = np.zeros((h, w, 3), np.float32)
    for (a, b) in ((150, 160), (196, 444), (480, 520)):
        # trapezoid: wider at the bottom (the light spreads onto the slope)
        t = np.clip((yy - 213) / 14, 0, 1)
        m = (yy >= 213) & (xx >= a - 10 * t) & (xx <= b + 10 * t)
        f = np.clip(1 - np.abs((xx - (a + b) / 2) / ((b - a) / 2 + 12)), 0, 1) ** 0.6 * (0.55 + 0.45 * t)
        for c in range(3):
            out[..., c] += m * f * rgb[c]
    q = np.floor(out / 8.0 + pg.bayer(w, h, x, y)[..., None]) * 8.0
    res = np.zeros((VH, VW, 4), np.uint8)
    res[y:y + h, x:x + w, :3] = np.clip(q, 0, 255).astype(np.uint8)
    res[..., 3] = np.where(res[..., :3].max(-1) > 0, 255, 0)
    return res


# =========================================================================== TRAINS: Alexei's Soviet compartment
A_LAMP = (507, 152)                   # wall reading lamp on the right wall
TEA = (331, 236)                      # foot of the tea glass holder (same spot as Konrad's lamp: the eye stays)


def ramps_a():
    return ramps(
        M=['#070A12', '#121A26', '#1E2836', '#2A3646', '#4A4236', '#645A49', '#80745E', '#9E9076', '#BBAD8F',
           '#D6CBAE'],
        P=['#070A12', '#10181F', '#1E302E', '#2B4541', '#3D5E57', '#56796E', '#739585'],
        I=['#070A12', '#15171C', '#22262D', '#323840', '#464D55', '#5E666E', '#8593A3', '#C2C9D2'],
        X=['#15171C', '#22262D', '#323840', '#464D55', '#5E666E', '#8593A3', '#C2C9D2', '#F2F3F5'],
        L=['#4A2D1F', '#6E3F22', '#A8643A', '#D08F55', '#EDB777', '#FCE2B0'],
        S=['#1A2431', '#2A3646', '#4F5E70', '#8593A3', '#A1AAB7', '#C2C9D2', '#DEE2E7'],
        R=['#2A3646'] + V['red'],
        A=A_COAT, U=A_FUR, F=SKIN, G=A_BAG, C=COLD, W=['#070A12', '#22150F', '#331F16', '#4A2D1F', '#63402C'])


def lamp_field_a(p: Paint):
    """The small wall lamp: a warm pool on the right wall and the table, falling off fast (a 40 W bulb)."""
    f = point_light(p.h, p.w, A_LAMP[0], A_LAMP[1], 250, p.ox, p.oy, power=1.6)
    return f


def night_light(p: Paint):
    """The blue night-light in the ceiling: a dim cold wash from above."""
    return np.clip(1 - (p.yy - 40) / 260, 0, 1) ** 1.5 * np.clip(1 - np.abs(p.xx - 320) / 520, 0, 1)


def int_alexei():
    R = ramps_a()
    p = Paint(VW, VH, R, 'int_alexei')
    yy, xx = p.yy, p.xx
    lamp = lamp_field_a(p)
    nl = night_light(p)
    allm = np.ones((VH, VW), bool)
    # ---- laminate walls (cream, here in night shadow) with aluminium joint strips; green dado below
    n = pg.value_noise(VW, VH, 30, 301, octaves=2)
    p.put(allm, 'M', 1.8 + lamp * 4.6 + nl * 1.2 + (n - 0.5) * 0.4)
    # laminate sheets: faint vertical seams and a wood-grain print, so the lit wall is not one flat blob
    grain = np.repeat(pg.value_noise(VW, VH // 5 + 2, 3, 302, octaves=2), 5, axis=0)[:VH]
    p.add(allm & (yy < 250), (grain - 0.5) * 0.5 * (0.3 + lamp))
    for jx in range(8, VW, 64):
        p.add(p.box(jx, 82, jx + 1, 250), -0.5)
    for jx in (40, 112, 528, 600):
        p.put(p.box(jx, 60, jx + 2, 250), 'I', 2.6 + lamp[150, jx] * 3.0)
        p.put(p.box(jx, 60, jx + 1, 250), 'I', 3.6 + lamp[150, jx] * 3.0)
    dado = p.box(0, 252, VW, VH)
    p.put(dado, 'P', 1.6 + lamp * 3.0)
    p.put(p.box(0, 250, VW, 253), 'I', 3.2)
    p.put(p.box(0, 250, VW, 251), 'I', 4.6)
    # heating pipe along the dado
    pipe = p.box(0, 290, VW, 297)
    p.put(pipe, 'I', 1.8 + np.clip((yy - 290) / 7, 0, 1) * -0.8 + lamp * 2.0)
    p.put(p.box(0, 291, VW, 292), 'I', 3.8)
    for bx in (60, 250, 430, 590):
        p.put(p.box(bx, 288, bx + 5, 299), 'I', 1.4)
    # ---- upper berths (folded down for the night) left and right, with guard rails and rolled mattresses
    for (x0b, x1b) in ((0, 150), (490, VW)):
        berth = p.box(x0b, 44, x1b, 72)
        p.put(berth, 'P', 1.4 + lamp * 2.4 + nl * 1.0)
        p.put(p.box(x0b, 70, x1b, 74), 'I', 2.2)
        p.put(p.box(x0b, 70, x1b, 71), 'I', 4.0)
        mat = p.rr(x0b + 6, 50, x1b - 6, 69, 8)
        stripes = ((xx.astype(int) // 5) % 3 == 0)
        p.put(mat, 'S', 2.0 + nl * 1.6 + lamp * 1.8)
        p.put(mat & stripes, 'P', 3.0 + lamp * 1.5)
        p.add(mat & (yy > 64), -0.8)
        rail = p.box(x0b, 76, x1b, 78)
        p.put(rail, 'X', 3.0 + lamp * 2.0)
        for sx in range(x0b + 18, x1b, 40):
            p.put(p.box(sx, 72, sx + 2, 78), 'X', 2.4)
    # ---- window frame: painted steel, the rolled-up blind with its pull tab
    frame = p.rr(156, 70, 484, 244, 24) & ~p.rr(*SASH, SASH_R)
    p.put(frame, 'P', 2.6 + lamp * 3.2 + nl * 0.8)
    p.add(frame & kit.dilate(p.rr(*SASH, SASH_R), 2), 0.9)
    p.add(frame & ~kit.erode(p.rr(156, 70, 484, 244, 24), 1), -1.2)
    blind = p.rr(172, 70, 468, 80, 3)
    p.put(blind, 'M', 4.0 + lamp * 2.0 + np.sin((yy - 70) / 10 * math.pi) * 1.2)
    p.put(p.box(176, 79, 464, 80), 'M', 2.6)
    p.put(p.box(316, 80, 324, 83), 'W', 2.6)                       # pull tab (over the sash top)
    p.put(p.box(319, 80, 321, 82), 'X', 5.0)
    # short cream curtains with a red stripe, gathered at both sides of the window
    for (xa, xb) in ((118, 166), (474, 522)):
        cm = p.box(xa, 82, xb, 236)
        folds = np.sin((xx - xa) * 0.9)
        p.put(cm, 'M', 3.4 + lamp * 4.2 + nl * 1.0 + folds * 0.7)
        stripe = cm & ((yy > 220) & (yy < 224) | (yy > 226) & (yy < 228))
        p.put(stripe, 'R', 1.6 + lamp * 2.0)
        p.put(p.box(xa, 82, xb, 84), 'M', 2.4)
        hem = cm & (yy > 232)
        p.add(hem, -0.8)
    p.put(p.box(110, 79, 530, 81), 'X', 3.4)                         # curtain rod
    # ---- radio speaker grille + the wall reading lamp on the right wall
    sp = p.ell(568, 118, 13, 13)
    p.put(sp, 'I', 2.0 + lamp * 2.4)
    p.put(sp & ((xx.astype(int) + yy.astype(int)) % 3 == 0), 'I', 1.0)
    p.put(sp & ~kit.erode(sp, 1), 'I', 3.6 + lamp * 2.0)
    p.put(p.box(562, 134, 574, 138), 'I', 2.8)
    p.put(p.box(500, 156, 514, 160), 'I', 3.0)                       # lamp bracket
    lshade = p.poly([(499, 140), (515, 140), (518, 154), (496, 154)])
    p.put(lshade, 'L', 3.2 + (yy - 140) / 14 * 1.4, emis=True)
    p.put(p.box(497, 153, 518, 155), 'L', 5.0, emis=True)
    p.put(p.box(503, 138, 511, 140), 'X', 4.0)
    # ---- table: grey laminate, aluminium edge, the napkin, newspaper, tea glass in its holder
    top = p.box(168, 236, 472, 244)
    p.put(top, 'M', 3.0 + lamp * 5.2 + nl * 0.8)
    p.put(top & (yy < 237), 'C', 4.0 + np.clip(1 - np.abs(xx - 320) / 220, 0, 1) * 2.2)
    p.put(p.box(168, 244, 472, 247), 'X', 3.6 + lamp * 2.5)
    p.put(p.box(168, 244, 472, 245), 'X', 5.4)
    p.put(p.box(168, 247, 472, 252), 'M', 1.6 + lamp * 2.0)
    napkin = p.poly([(298, 236), (360, 236), (366, 243), (292, 243)])
    p.put(napkin, 'S', 3.4 + lamp * 3.0)
    p.put(napkin & (np.abs(yy - 239.5) < 0.6), 'S', 2.4)
    paper = p.poly([(396, 236), (452, 235), (458, 243), (392, 243)])
    p.put(paper, 'M', 5.4 + lamp * 2.2)
    for k in range(3):
        p.put(p.box(400 + k * 17, 238, 414 + k * 17, 239), 'M', 3.6)
        p.put(p.box(400 + k * 17, 240, 410 + k * 17, 241), 'M', 3.8)
    for (sx, sy) in ((282, 240), (286, 241)):                       # wrapped sugar cubes
        p.put(p.box(sx, sy, sx + 4, sy + 2), 'S', 5.0)
    # ---- sash + glass hole, then everything that stands in front of the glass
    paint_sash(p)
    g = punch_glass(p)
    # tea glass in a nickel-silver holder (podstakannik): handle left (toward Alexei), spoon, amber tea
    tx, ty = TEA
    holder = p.poly([(tx - 7, ty - 14), (tx + 7, ty - 14), (tx + 6, ty - 2), (tx + 8, ty), (tx - 8, ty), (tx - 6, ty - 2)])
    hl = np.clip((xx - (tx - 7)) / 14, 0, 1)
    p.put(holder, 'X', 2.4 + hl * 3.4)
    p.put(holder & (((xx.astype(int) * 2 + yy.astype(int)) % 4) == 0) & (yy < ty - 3), 'X', 1.6 + hl * 2.0)
    p.put(holder & (np.abs(yy - (ty - 13.5)) < 0.6), 'X', 6.0)
    p.put(p.box(tx - 9, ty - 1, tx + 9, ty + 1), 'X', 4.0)
    handle = p.line([(tx - 7, ty - 12), (tx - 11, ty - 11), (tx - 11, ty - 5), (tx - 7, ty - 4)], 0.6)
    p.put(handle, 'X', 3.2)
    glass = p.box(tx - 6, ty - 21, tx + 7, ty - 14)
    p.put(glass, 'L', 3.4 + hl * 1.2, emis=True)                      # amber tea seen through the glass
    p.put(p.box(tx - 6, ty - 21, tx + 7, ty - 20), 'L', 5.0, emis=True)
    p.put(p.box(tx - 7, ty - 22, tx + 8, ty - 21), 'S', 5.4)          # glass rim
    p.put(p.box(tx + 5, ty - 21, tx + 6, ty - 15), 'S', 6.0)          # glint
    paint_reach_a(p, lamp)
    # frost on the cold glass corners (on the glass, in front of the night)
    rng = np.random.default_rng(311)
    gx0, gy0, gx1, gy1 = GLASS
    for (cx, cy, sx, sy) in ((gx0, gy1, 1, -1), (gx1, gy1, -1, -1), (gx0, gy0, 1, 1), (gx1, gy0, -1, 1)):
        reach = 26 if cy == gy1 else 14
        for _ in range(int(reach * 4)):
            a = rng.uniform(0, math.pi / 2)
            r = rng.uniform(0, reach) ** 1.0
            px_ = int(cx + sx * math.cos(a) * r * rng.uniform(0.6, 1.6))
            py_ = int(cy + sy * math.sin(a) * r * 0.7)
            ln = int(rng.integers(1, 4))
            for k in range(ln):
                X, Y = px_ + sx * k, py_ + sy * (k % 2)
                if 0 <= X < VW and 0 <= Y < VH and g[Y, X]:
                    p.L.put(np.ones((1, 1), bool), X, Y, 'S', float(rng.choice([2.0, 3.0, 4.0])), flat=True)
    p.L.amb_field(-np.clip(np.hypot((xx - 330) / 430, (yy - 190) / 260) - 0.35, 0, 1) * 2.2)
    p.resolve(band=2.6)
    return p.L


def paint_reach_a(p: Paint, lamp):
    """Alexei's right forearm on the table, the quilted sleeve, his hand at the handle of the glass holder."""
    yy, xx = p.yy, p.xx
    hx = TEA[0] - 11                                    # the holder's handle
    sleeve = p.poly([(hx - 10, 224), (hx - 24, 221), (hx - 46, 233), (hx - 48, 252), (hx - 32, 254), (hx - 12, 236)])
    p.put(sleeve, 'A', 1.2 + lamp * 1.8)
    p.put(sleeve & ~shift(sleeve, 0, -1), 'A', 3.4 + lamp * 1.2)
    p.put(sleeve & ~shift(sleeve, 1, 0) & (yy < 240), 'L', 1.4 + lamp * 1.4)       # the wall lamp on its side
    for k in range(3):                                                             # quilting across the sleeve
        q = p.line([(hx - 20 - k * 8, 223 + k * 3), (hx - 14 - k * 8, 236 + k * 4)], 0.5) & sleeve
        p.add(q, -0.8)
    hand = p.poly([(hx + 1, 228), (hx - 3, 226), (hx - 9, 227), (hx - 11, 234), (hx - 5, 236), (hx, 235)])
    p.put(hand, 'F', 2.4 + lamp * 1.6)
    p.put(hand & ~shift(hand, 0, -1), 'F', 4.6)
    p.put(hand & ~shift(hand, 1, 0), 'F', 4.0)
    for fy in (230, 232):
        p.px(hx - 1, fy, 'F', 1.2)
    p.px(hx + 1, 231, 'F', 3.2)


# ---------------------------------------------------------------- Alexei (seated, seen from behind-left)
FIG_A = (96, 86, 220, 232)


def fig_alexei():
    import env_veltrava_cine_figs as F
    f0 = F.back_alexei(0)['rgba']
    f1 = F.back_alexei(1)['rgba']
    LAYOUT['trains']['fig_alexei'] = [FIG_A[0], FIG_A[1]]
    return _sheet4(f0, f1)


def refl_alexei():
    """Additive reflections: Alexei's face lit from the wall lamp, the lamp itself and the glowing tea."""
    import env_veltrava_cine_figs as F
    face = F.reflection(F.face_alexei(0), (50, 38, 24), gain=1.25, levels=5)
    yy, xx = grid(VH, VW)
    a = np.zeros((VH, VW, 3), np.float32)
    d = np.hypot((xx - 452) / 12, (yy - 150) / 8)
    for c, v in enumerate((60, 40, 20)):
        a[..., c] += np.clip(1 - d, 0, 1) ** 1.4 * v
    d2 = np.hypot((xx - 352) / 9, (yy - 214) / 7)
    for c, v in enumerate((34, 20, 9)):
        a[..., c] += np.clip(1 - d2, 0, 1) ** 1.4 * v
    LAYOUT['trains']['refl_face_alexei'] = [236, 106]
    return _glass_reflection(face, (236, 106), a, 160, 26)


def spoon():
    """The tea spoon standing in Alexei's glass, 2 frames: at rest leaning right, and knocked upright by a
    rail joint (the runtime switches with every knock; the bed sound clinks on the same beat)."""
    fw, fh = 8, 14
    tx, ty = TEA
    x0, y0 = tx - 1, ty - 34
    R = ramps(X=['#15171C', '#22262D', '#323840', '#464D55', '#5E666E', '#8593A3', '#C2C9D2', '#F2F3F5'])
    sheet = np.zeros((fh, fw * 2, 4), np.uint8)
    for fr, top in enumerate(((6, 3), (4, 2))):
        p = Paint(fw, fh, R, 'spoon', x0, y0)
        bot = (tx + 2, ty - 21)
        tip = (x0 + top[0], y0 + top[1])
        p.put(p.line([bot, tip], 0.5), 'X', 5.4)
        p.px(tip[0], tip[1] - 1, 'X', 6.8)
        p.px(tip[0] - 1, tip[1], 'X', 4.0)
        p.resolve(band=2.0)
        sheet[:, fr * fw:(fr + 1) * fw] = p.L.c
    LAYOUT['trains']['spoon'] = [x0, y0]
    return sheet


def glow_tea():
    x0, y0, w, h = 280, 120, 270, 140
    g1 = additive_glow(TEA[0], TEA[1] - 18, 22, 16, (60, 36, 14), power=1.6, w=w, h=h, ox=x0, oy=y0)
    g2 = additive_glow(A_LAMP[0], A_LAMP[1], 46, 30, (64, 42, 20), power=1.8, w=w, h=h, ox=x0, oy=y0)
    g = np.clip(g1.astype(np.int32) + g2.astype(np.int32), 0, 255).astype(np.uint8)
    g[..., 3] = np.where(g[..., :3].max(-1) > 0, 255, 0)
    LAYOUT['trains']['glow_tea'] = [x0, y0]
    return g


def steam_tea():
    """Six frames of a thin steam wisp rising from the tea (16 x 30 each)."""
    fw, fh, n = 16, 30, 6
    sheet = np.zeros((fh, fw * n, 4), np.uint8)
    cols = [pg.hx('#8593A3'), pg.hx('#A1AAB7'), pg.hx('#C2C9D2')]
    for i in range(n):
        for k in range(26):
            yv = fh - 1 - k
            ph = i / n * math.tau
            xv = 8 + math.sin(k * 0.33 - ph) * (1.2 + k * 0.09) + math.sin(k * 0.11 + ph * 0.5) * 1.5
            if (k + i) % 7 in (5, 6) and k > 8:
                continue
            c = cols[2] if k < 6 else (cols[1] if k < 16 else cols[0])
            X = int(round(xv))
            if 0 <= X < fw:
                sheet[yv, i * fw + X] = c
    LAYOUT['trains']['steam_tea'] = [TEA[0] - 6, TEA[1] - 22 - fh + 2]
    return sheet


# =========================================================================== TRAINS: the passing light (t2)
def quant_add(a: np.ndarray, step=6.0, ox=0, oy=0):
    h, w = a.shape[:2]
    q = np.floor(a / step + pg.bayer(w, h, ox, oy)[..., None]) * step
    out = np.zeros((h, w, 4), np.uint8)
    out[..., :3] = np.clip(q, 0, 255).astype(np.uint8)
    out[..., 3] = np.where(out[..., :3].max(-1) > 0, 255, 0)
    return out


def flare():
    """Cold light flooding the glass while a floodlit level crossing passes (additive; runtime alpha)."""
    yy, xx = grid(VH, VW)
    g = glass_mask()
    f = 0.72 + 0.28 * np.clip(1 - np.hypot((xx - 320) / 200, (yy - 170) / 110), 0, 1)
    a = np.zeros((VH, VW, 3), np.float32)
    for c, v in enumerate((150, 158, 170)):
        a[..., c] = g * f * v
    return quant_add(a, 8.0)


def sweep():
    """A vertical band of light sliding across the glass (additive)."""
    w, h = 140, EXT[3]
    yy, xx = grid(h, w)
    prof = np.clip(np.cos((xx - w / 2) / (w / 2) * math.pi / 2), 0, 1) ** 1.6
    shafts = 0.8 + 0.2 * np.sin(xx * 0.45) * np.sin(yy * 0.05 + 1.0)
    a = np.zeros((h, w, 3), np.float32)
    for c, v in enumerate((120, 128, 140)):
        a[..., c] = prof * shafts * v
    LAYOUT['trains']['sweep'] = [0, EXT[1]]
    return quant_add(a, 8.0)


def roomflare(interior: np.ndarray, figure: np.ndarray, fig_xy, toward=(-1, -1)):
    """The flash lighting the room around the window and rimming the sitter's silhouette (additive)."""
    yy, xx = grid(VH, VW)
    x0, y0, x1, y1 = GLASS
    dx = np.maximum(np.maximum(x0 - xx, xx - (x1 - 1)), 0)
    dy = np.maximum(np.maximum(y0 - yy, yy - (y1 - 1)), 0)
    d = np.hypot(dx, dy)
    inter = interior[..., 3] > 127
    fm = np.zeros((VH, VW), bool)
    fh, fw = figure.shape[:2]
    fx, fy = fig_xy
    fm[fy:fy + fh, fx:fx + fw] = figure[..., 3] > 127
    lit = np.clip(1 - d / 80, 0, 1) ** 1.6 * (inter & ~fm)
    a = np.zeros((VH, VW, 3), np.float32)
    for c, v in enumerate((70, 76, 86)):
        a[..., c] = lit * v
    # rim on the silhouette edges that face the glass
    edge = fm & ~shift(fm, toward[0], 0) | fm & ~shift(fm, 0, toward[1])
    inside_glass = (xx >= x0 - 4) & (xx < x1 + 4) & (yy >= y0 - 4) & (yy < y1 + 6)
    rimm = edge & inside_glass
    for c, v in enumerate((120, 128, 140)):
        a[..., c] += rimm * v
    return quant_add(a, 8.0)


# =========================================================================== TRAINS: dawn on the river bridge (t4)
# painted in env_veltrava_cine_dawn.py (imported lazily: it imports this module)


# =========================================================================== build
def build_trains():
    out = {}

    def w(rel, img):
        arr = img.c if hasattr(img, 'c') else img
        save(arr, 'trains/' + rel)
        out[rel] = arr
        return arr

    w('ext_sky.png', ext_sky())
    w('ext_far_de.png', ext_far('de'))
    w('ext_far_su.png', ext_far('su'))
    w('ext_mid.png', ext_mid())
    w('ext_near.png', ext_near())
    w('pole.png', pole())
    ik = w('int_konrad.png', int_konrad())
    fk = w('fig_konrad.png', fig_konrad())
    w('refl_konrad.png', refl_konrad())
    w('glow_lamp.png', glow_lamp())
    w('patch_warm.png', window_patches((60, 40, 20), 1))
    w('patch_cold.png', window_patches((30, 34, 40), 2))
    ia = w('int_alexei.png', int_alexei())
    fa = w('fig_alexei.png', fig_alexei())
    w('refl_alexei.png', refl_alexei())
    w('glow_tea.png', glow_tea())
    w('steam_tea.png', steam_tea())
    w('spoon.png', spoon())
    w('sweep.png', sweep())
    w('flare.png', flare())
    fwk = FIG_K[2]
    fwa = FIG_A[2]
    w('roomflare_k.png', roomflare(ik, fk[:, :fwk], FIG_K[:2], toward=(-1, -1)))
    w('roomflare_a.png', roomflare(ia, fa[:, :fwa], FIG_A[:2], toward=(1, -1)))
    import env_veltrava_cine_dawn as D
    w('bridge_bg.png', D.bridge_bg())
    w('bridge_fg.png', D.bridge_fg())
    w('train_de.png', D.train_de())
    w('train_su.png', D.train_su())
    w('smoke.png', D.smoke())
    w('dawn_glow.png', D.dawn_glow())
    w('fg_glow.png', D.fg_glow())
    w('walker.png', D.walker())
    return out


def build_tohall():
    import env_veltrava_cine_tohall as T
    for rel, fn in (('k1_bg.png', T.k1_bg), ('k1_clock.png', T.k1_clock), ('k1_glass.png', T.k1_glass),
                    ('steam_puffs.png', T.steam_puffs), ('k2_bg.png', T.k2_bg), ('k2_clock.png', T.k2_clock),
                    ('k2_glass.png', T.k2_glass), ('pendulum.png', T.pendulum), ('k2_konrad.png', T.k2_konrad)):
        img = fn()
        save(img.c if hasattr(img, 'c') else img, 'tohall/' + rel)


def build_close():
    import env_veltrava_cine_close as N
    for rel, fn in (('n1_bg.png', N.n1_bg), ('n1_mid.png', N.n1_mid), ('n1_fg.png', N.n1_fg),
                    ('board.png', N.board), ('steam.png', N.steam), ('n2_bg.png', N.n2_bg),
                    ('n2_win_konrad.png', N.n2_win_konrad), ('n2_win_alexei.png', N.n2_win_alexei),
                    ('n2_lamp_glow.png', N.n2_lamp_glow)):
        img = fn()
        save(img.c if hasattr(img, 'c') else img, 'close/' + rel)


def write_layout():
    p = os.path.join(OUT, 'layout.json')
    os.makedirs(OUT, exist_ok=True)

    def norm(o):
        if isinstance(o, dict):
            return {str(k): norm(v) for k, v in o.items()}
        if isinstance(o, (list, tuple)):
            return [norm(v) for v in o]
        if isinstance(o, (np.integer,)):
            return int(o)
        if isinstance(o, (np.floating, float)):
            v = float(o)
            return int(v) if v.is_integer() and isinstance(o, np.floating) else round(v, 4)
        return o
    import re
    txt = json.dumps(norm(LAYOUT), indent=1, sort_keys=True, ensure_ascii=False)
    # short numeric lists on one line (readable diffs)
    txt = re.sub(r'\[\s*(-?[\d.]+(?:,\s*-?[\d.]+)*)\s*\]',
                 lambda m: '[' + ', '.join(v.strip() for v in m.group(1).split(',')) + ']', txt)
    with open(p, 'w', encoding='utf-8', newline='\n') as f:
        f.write(txt + '\n')


def main(argv=None):
    import argparse
    import time
    ap = argparse.ArgumentParser()
    ap.add_argument('--only', default='trains,tohall,close')
    args = ap.parse_args(argv)
    parts = [s.strip() for s in args.only.split(',') if s.strip()]
    t0 = time.time()
    # every part registers its LAYOUT entries; layout.json is always written from a complete build
    # (a partial --only run rebuilds the other parts' layout entries without writing their images)
    if 'trains' in parts:
        build_trains()
    else:
        _layout_only_trains()
    if 'tohall' in parts:
        build_tohall()
    else:
        _layout_only('tohall')
    if 'close' in parts:
        build_close()
    else:
        _layout_only('close')
    write_layout()
    print('env_veltrava_cine: %s in %.1f s -> %s' % (','.join(parts), time.time() - t0, OUT))


def _layout_only_trains():
    # cheap functions that register the trains LAYOUT keys (the figure renders are skipped)
    import env_veltrava_cine_dawn as D
    for fn in (pole, glow_lamp, glow_tea, steam_tea, spoon, sweep, D.bridge_bg, D.bridge_fg, D.train_de, D.train_su,
               D.smoke, D.walker):
        fn()
    ext_far('de')
    ext_far('su')
    LAYOUT['trains']['fig_konrad'] = [FIG_K[0], FIG_K[1]]
    LAYOUT['trains']['fig_alexei'] = [FIG_A[0], FIG_A[1]]


def _layout_only(part):
    if part == 'tohall':
        import env_veltrava_cine_tohall as T
        T.k1_clock()
        T.k2_clock()
        T.steam_puffs()
        T.pendulum()
        T.k2_konrad()
    else:
        import env_veltrava_cine_close as N
        N.n1_bg()
        N.board()
        N.steam()
        N.n2_bg()
        N.n2_win_konrad()
        N.n2_win_alexei()


if __name__ == '__main__':
    # run inside the importable module object: the sub-modules (tohall, close, figs) import
    # env_veltrava_cine and must share its LAYOUT dict with the writer
    sys.modules.pop('env_veltrava_cine', None)
    import env_veltrava_cine as _self  # noqa: E402
    _self.main()
