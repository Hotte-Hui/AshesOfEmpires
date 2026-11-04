"""env_veltrava_cine -- Chapter 3 cinematic art (LS_C3_Trains, LS_C3_ToHall, LS_C3_Close).

Owner: cinematics stream (documentation/C3_DESIGN.md §7).  Every file written here is original, painted in
code, deterministic (fixed seeds, no time or global random state) and drawn at 1 texel = 1 px of the
640x360 world (close shots use bespoke larger figures, never scaled sprites).  Run:

    python3 -P tools/pixelgen/env_veltrava_cine.py [--preview DIR] [--only trains,tohall,close]

Palette: the 'veltrava' / 'palais' ramps of data/chapters/c3.json are registered into pg.PALETTES at import
time (read-only use); a few character ramps are sampled from the existing protagonist sprites so the
bespoke figures match assets/characters/{konrad,alexei}.

Output (assets/cinematics/ch3/):
  trains/  ext_sky, ext_far_de|su, ext_mid, ext_near, pole, int_konrad, fig_konrad, refl_konrad, glow_lamp,
           patch_warm|cold, int_alexei, fig_alexei, refl_alexei, glow_tea, steam_tea, sweep, flare,
           bridge_bg, bridge_fg, train_de, train_su, smoke, dawn_glow
  tohall/  k1_bg, k1_clock, steam_puffs, k2_bg, k2_clock, pendulum, k2_konrad
  close/   n1_bg, n1_fg, board_*, n2_bg, n2_win_konrad, n2_win_alexei
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
K_COAT = ['#05070E', '#0F112A', '#1D2442', '#2C3B5E', '#3A4A6A', '#4E556C', '#7E848F']
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
    lay.put(strip, 0, 0, 'C', 6.0 + lit * 5.6 - np.clip(yy - 184, 0, 8) * 0.25)
    # fence lines + posts (tiny at this distance)
    lay.rect(0, far_fence_y - y0, w, 1, 'C', 4.0, flat=True)
    for px_ in range(0, w, 5):
        lay.rect(px_, far_fence_y - 2 - y0, 1, 2, 'C', 3.6, flat=True)
    lay.rect(0, fence_y - 1 - y0, w, 1, 'C', 2.2, flat=True)
    lay.rect(0, fence_y - 3 - y0, w, 1, 'C', 3.0, flat=True)
    for px_ in range(2, w, 4):
        lay.rect(px_, fence_y - 4 - y0, 1, 4, 'C', 2.0, flat=True)
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
    lay.resolve(band=3.0)
    LAYOUT['trains']['masts_' + side] = masts
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
    t = 7.4 - depth * 2.6 + depth ** 2 * 1.2
    drift = wrap_noise(w, h, 40, 73, octaves=3)
    crest = np.sin((yy - 188) * 0.55 + drift * 9.0)
    t += np.where(crest > 0.86, 0.9, 0.0) - np.where(crest < -0.9, 0.5, 0.0)
    t += (drift - 0.5) * 0.8
    lay.put(m, 0, 0, 'C', t)
    # old field fence (posts + one sagging wire)
    fy = 199
    for px_ in range(3, w, 11):
        hgt = 3 + (px_ * 7) % 2
        lay.rect(px_, fy - hgt - y0, 1, hgt, 'C', 2.4, flat=True)
    for px_ in range(w):
        sag = 0.6 * math.sin(math.pi * ((px_ - 3) % 11) / 11)
        lay.px(px_, int(round(fy - 3 + sag)) - y0, 'C', 3.4, flat=True)
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
            lay.px(int(bx + dx), int(by - s) - y0, 'C', 7.0, flat=True)
    # birches: pale trunks with dark bark marks, bare crowns
    for _ in range(9):
        bx = int(rng.uniform(0, w)); by = int(rng.uniform(196, 212))
        th = int(10 + (by - 196) * 0.9 + rng.uniform(0, 5))
        for dx in (-w, 0, w):
            X = bx + dx
            lay.rect(X, by - th - y0, 1, th, 'C', 8.6, flat=True)
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
    t = 7.8 - (yy - 216) * 0.16 + (streak - 0.5) * 1.6 + (fine - 0.5) * 0.6
    lay.put(m, 0, 0, 'C', t)
    # crest highlight on the mound tops, dark ballast flecks low down
    crest = m & ~shift(m, 0, -1)
    lay.put(crest, 0, 0, 'C', 9.6, flat=True)
    rng = np.random.default_rng(84)
    for _ in range(130):
        x = int(rng.integers(0, w)); y = int(rng.integers(224, 232)) - y0
        if m[y, x]:
            lay.rect(x, y, int(rng.integers(2, 6)), 1, 'C', 3.0, flat=True)
    lay.resolve(band=3.0)
    return lay


def pole():
    """Telegraph pole passing close to the window (dark, a crossarm with insulators)."""
    R = ramps(C=COLD, L=['#0C111C', '#22150F', '#331F16', '#4A2D1F', '#63402C'])
    w, h = 16, 160                             # abs rows 74..233, x centred on col 8
    lay = blank(w, h, R, 'pole')
    y0 = 74
    lay.rect(6, 0, 4, h, 'C', 0.6, flat=True)
    lay.rect(9, 0, 1, h, 'C', 1.4, flat=True)                       # cold edge from the Line glow
    yy = np.arange(h)[:, None] + y0
    warm = np.clip((yy - 170) / 60, 0, 1)[:, 0]
    for k in range(h):
        if warm[k] > 0.1:
            lay.rect(6, k, 2, 1, 'L', 0.6 + warm[k] * 2.2)          # train-window light on the low pole
    # crossarms
    for (cy, ln) in ((96, 16), (108, 12)):
        lay.rect(8 - ln // 2, cy - y0, ln, 2, 'C', 0.8, flat=True)
        for ix in (8 - ln // 2 + 1, 8 + ln // 2 - 2):
            lay.rect(ix, cy - 3 - y0, 1, 3, 'C', 9.0, flat=True)
            lay.px(ix, cy - 3 - y0, 'C', 11.0, flat=True)
    # bands of snow stuck on the windward side
    for k in range(0, h, 23):
        lay.px(9, k + 7, 'C', 6.0, flat=True)
    lay.resolve(band=2.0)
    LAYOUT['trains']['pole'] = {'w': w, 'h': h, 'y': y0, 'insulators': [[1, 93], [6, 93], [3, 105], [10, 105]],
                                'cx': 8}
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
