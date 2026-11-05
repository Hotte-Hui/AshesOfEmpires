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
    # ---- coffee cup on its saucer (the counterpart of Alexei's tea glass)
    p.put(p.ell(372, 236.8, 11, 2.4), 'P', 4.2)
    p.put(p.ell(372, 236.2, 9, 1.4), 'P', 5.6)
    cup = p.poly([(365, 226), (379, 226), (378, 233), (375, 236), (369, 236), (366, 233)])
    p.put(cup, 'P', 6.4 - np.clip((xx - 366) / 13, 0, 1) * 3.2)
    p.put(p.box(365, 226, 380, 227), 'B', 4.4)
    p.put(p.ell(372, 226.9, 6, 0.9), 'W', 2.2)
    handle = p.line([(379, 228), (382, 229), (382, 232), (378, 233)], 0.5)
    p.put(handle, 'P', 3.4)
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
    # overall falloff to the frame edges (night interior)
    p.L.amb_field(-np.clip(np.hypot((xx - 330) / 420, (yy - 200) / 260) - 0.35, 0, 1) * 2.4)
    p.resolve(band=2.6)
    return p.L


# ---------------------------------------------------------------- Konrad (seated, seen from behind-right)
FIG_K = (366, 96, 190, 218)          # frame box x, y, w, h (absolute), 4 frames side by side


def fig_konrad_frame(turn: int, breath: int):
    x0, y0, w, h = FIG_K
    R = ramps_k()
    p = Paint(w, h, R, 'fig_konrad', x0, y0)
    yy, xx = p.yy, p.xx
    lampdir = (-1.0, 0.2)
    lamp = point_light(h, w, K_LAMP[0], K_LAMP[1], 260, x0, y0, power=1.1)
    b = breath
    # ---------- torso in the overcoat: far shoulder low on the left, near shoulder + arm on the right
    torso = p.poly([(420, 161), (436, 165 - b), (458, 162 - b), (482, 166 - b), (504, 172 - b), (519, 183 - b),
                    (525, 200), (523, 236), (521, 276), (526, 314), (390, 314), (388, 282), (386, 248), (387, 214),
                    (390, 190 - b), (398, 176 - b), (410, 166 - b)])
    arm = p.poly([(505, 176 - b), (520, 182 - b), (530, 196), (536, 222), (541, 250), (544, 268), (540, 280),
                  (528, 284), (518, 270), (512, 240), (508, 208)])
    coat = torso | arm
    p.put(coat, 'K', 1.15 - np.clip((yy - 170) / 140, 0, 1) * 0.6, flat=True)
    # light on the wool: cold from the window (top/left edges), warm lamp rim on the left above the table
    p.add(coat, edge_light(coat, (-0.35, -1.0), 4.0) * 2.8)
    p.add(coat, edge_light(coat, lampdir, 7.0) * np.clip(lamp * 1.9, 0, 1) * (yy < 244) * 2.2)
    # the near arm separates from the back: a shadow crease and a soft sheen on the sleeve
    crease = p.line([(506, 178), (510, 206), (514, 240), (518, 268)], 0.6) & coat
    p.put(crease, 'K', 0.15)
    p.add(arm & ~crease, edge_light(arm, (1.0, -0.4), 3.0) * 0.8)
    # seams, shoulder blades, the vent, folds at the elbow
    for pts, dt in (([(456, 170), (460, 214), (464, 262), (468, 314)], -0.35),
                    ([(468, 165), (492, 170), (512, 180)], 0.55),
                    ([(424, 190), (430, 214)], 0.35), ([(486, 192), (494, 216)], 0.35),
                    ([(462, 286), (466, 314)], -0.5),
                    ([(520, 250), (530, 262)], 0.6), ([(512, 232), (522, 244)], 0.5)):
        p.add(p.line(pts, 0.5) & coat, dt)
    rimw = coat & rim(coat, -1, 0, 1) & (yy < 244) & (yy > 164)
    p.put(rimw, 'L', 0.8 + np.clip(lamp * 1.8, 0, 1.6))
    # ---------- collar (turned up) and the scarf
    collar = p.poly([(419, 152), (427, 148), (440, 149), (452, 149), (460, 153), (463, 161), (455, 166 - b),
                     (436, 167 - b), (421, 163)])
    p.put(collar, 'K', 1.6)
    p.add(collar, edge_light(collar, lampdir, 4) * 1.8 + edge_light(collar, (0, -1), 2) * 1.5)
    p.add(collar & p.line([(424, 160), (452, 160)], 0.5), -0.6)
    scarf = p.poly([(412, 155), (421, 150), (428, 152), (431, 160), (426, 167), (414, 167), (410, 161)])
    p.put(scarf, 'Y', 1.4 + edge_light(scarf, lampdir, 5) * 3.4)
    p.add(scarf & p.line([(415, 160), (427, 157)], 0.5), -0.9)
    # ---------- head: hair at the back, lit cheek plane in lost profile, ear, nose tip
    skull = p.ell(438, 139, 14.0, 14.0) & (yy >= 128)
    neck = p.box(431, 148, 447, 160)
    if turn == 0:
        face_pts = [(423, 129), (418, 133), (416, 140), (417, 147), (420, 153), (425, 158), (431, 159), (434, 154),
                    (431, 146), (429, 137)]
    else:
        face_pts = [(426, 129), (421, 133), (419, 140), (420, 147), (422, 153), (426, 158), (431, 159), (433, 154),
                    (431, 146), (430, 137)]
    face = p.poly(face_pts)
    head = skull | face | neck
    p.put(head, 'F', 1.2)
    p.put(neck, 'F', 0.7)
    hair = skull & ~face & (xx >= 429) & (yy < 151)
    p.put(hair, 'H', 0.45, flat=True)
    p.put(hair & rim(hair, 1, 0, 1), 'H', 1.4)
    p.put(hair & (np.abs(yy - 150.5) < 0.6), 'H', 1.3)           # clean neckline
    fl = edge_light(face, lampdir, 7.0, soft=2)
    p.put(face, 'F', 1.9 + fl * 3.9 + np.clip((434 - xx) / 18, 0, 1) * 0.7)
    p.add(face & (yy > 154), -0.8)
    p.add(face & p.line([(419, 141), (426, 143)], 0.5), 0.6)
    if turn == 0:
        nose = p.poly([(418, 138), (413, 143), (415, 146), (419, 146)])
        p.put(nose, 'F', 4.4)
        p.px(414, 143, 'F', 6.0)
        p.px(420, 137, 'F', 1.0)
        p.px(419, 151, 'F', 2.4)
    ear = p.ell(445.5, 140, 1.8, 3.6)
    p.put(ear, 'F', 1.1)
    p.put(ear & rim(ear, -1, 0, 1), 'F', 2.2)
    p.put(p.box(442, 131, 445, 137) & skull, 'H', 1.0)
    # ---------- hat
    if turn == 0:
        brim_pts = [(403, 132), (407, 128), (416, 125), (428, 124), (444, 124), (458, 123), (467, 121), (470, 123),
                    (465, 127), (455, 129), (440, 131), (424, 132), (412, 134), (405, 135)]
    else:
        brim_pts = [(406, 132), (409, 128), (417, 125), (428, 124), (444, 124), (458, 123), (467, 121), (470, 123),
                    (465, 127), (455, 129), (440, 131), (425, 132), (413, 134), (407, 134)]
    brim = p.poly(brim_pts)
    crown = p.poly([(421, 126), (420, 116), (423, 108), (429, 104), (436, 103), (440, 106), (445, 103), (450, 104),
                    (455, 109), (457, 117), (456, 126)])
    p.put(crown, 'H', 1.3 + edge_light(crown, (-0.5, -1), 3) * 2.3 + edge_light(crown, lampdir, 4) * 1.2)
    band = crown & (yy >= 120)
    p.put(band, 'H', 0.4)
    p.put(p.box(452, 120, 456, 125) & crown, 'H', 1.5)
    p.add(crown & p.line([(440, 106), (441, 115)], 0.5), -0.8)
    p.add(crown & p.line([(426, 109), (425, 118)], 0.5), -0.6)
    p.put(brim, 'H', 1.2)
    p.add(brim & (yy >= 128), edge_light(brim, lampdir, 5) * 3.0 * (xx < 450))
    p.put(brim & rim(brim, 0, -1, 1) & (xx > 412), 'H', 2.6)
    p.put(brim & rim(brim, -1, 0, 1), 'H', 4.2)
    p.add(head & shift(brim, 0, -1) & ~brim, -0.9)
    sil = coat | collar | scarf | head | brim | crown
    out = kit.dilate(sil, 1) & ~sil
    p.put(out & (xx < 470) & (yy < 236), 'K', 0.2)
    p.resolve(band=3.2)
    return p.L


def fig_konrad():
    frames = [fig_konrad_frame(turn, breath) for turn in (0, 1) for breath in (0, 1)]
    x0, y0, w, h = FIG_K
    sheet = np.zeros((h, w * 4, 4), np.uint8)
    for i, L in enumerate(frames):
        sheet[:, i * w:(i + 1) * w] = L.c
    LAYOUT['trains']['fig_konrad'] = [x0, y0]
    return sheet


def refl_konrad():
    """Additive reflection on the glass: Konrad's lamp-lit face (seen from the front) and the lamp."""
    a = np.zeros((VH, VW, 3), np.float32)
    yy, xx = grid(VH, VW)
    g = glass_mask()
    # face oval, lit from the lower left (the lamp), mirrored: he looks back toward his own head
    face = ellipse_mask(VW, VH, 377, 145, 10.5, 14.5)
    lit = np.clip((388 - xx) / 20, 0, 1) * 0.65 + 0.35
    soft = np.clip(1 - np.hypot((xx - 377) / 11.5, (yy - 145) / 15.5), 0, 1) ** 0.5
    for c, v in enumerate((19, 12, 8)):
        a[..., c] += face * v * lit * (0.45 + 0.55 * soft)
    for (ex, ey) in ((373, 141), (381, 141)):                     # eye sockets (no light)
        a[ellipse_mask(VW, VH, ex, ey, 2.4, 1.4)] *= 0.25
    nose = poly_mask(VW, VH, [(377, 141), (375, 150), (379, 151)])
    a[nose] += (7, 4, 3)
    a[(np.abs(yy - 154.5) < 0.6) & (np.abs(xx - 377) < 3)] *= 0.3
    # hat: dark (adds nothing) but the brim underside picks up a little lamp light
    brim = poly_mask(VW, VH, [(356, 131), (398, 130), (396, 134), (358, 135)])
    a[brim] = (10, 6, 4)
    crown = poly_mask(VW, VH, [(366, 131), (366, 114), (377, 110), (388, 114), (388, 131)])
    a[crown] = 0
    scarf = poly_mask(VW, VH, [(368, 158), (388, 158), (392, 168), (364, 168)])
    a[scarf] += (12, 9, 4)
    collar = poly_mask(VW, VH, [(358, 162), (366, 158), (366, 178), (354, 180)]) | \
        poly_mask(VW, VH, [(390, 158), (398, 162), (402, 180), (390, 178)])
    a[collar] += (6, 6, 10)
    # the lamp and its warm halo reflected near the real lamp
    d = np.hypot((xx - 306) / 14, (yy - 203) / 9)
    for c, v in enumerate((70, 44, 20)):
        a[..., c] += np.clip(1 - d, 0, 1) ** 1.3 * v
    core = ellipse_mask(VW, VH, 306, 205, 5, 2.5)
    a[core] += (40, 26, 12)
    # the table edge and cup glinting along the bottom of the glass
    a[(yy >= 220) & (yy < 226) & (xx > 300) & (xx < 400)] += (16, 10, 5)
    a[~g] = 0
    # posterise into a few levels + Bayer dither between them (pixel-art glass, not a smooth blend)
    q = np.floor(a / 4.0 + pg.bayer(VW, VH)[..., None]) * 4.0
    out = np.zeros((VH, VW, 4), np.uint8)
    out[..., :3] = np.clip(q, 0, 255).astype(np.uint8)
    out[..., 3] = np.where(out[..., :3].max(-1) > 0, 255, 0)
    return out


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
    f = point_light(p.h, p.w, A_LAMP[0], A_LAMP[1], 330, p.ox, p.oy, power=1.3)
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
    p.put(allm, 'M', 2.0 + lamp * 5.6 + nl * 1.2 + (n - 0.5) * 0.4)
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
    spoon = p.line([(tx + 2, ty - 21), (tx + 5, ty - 30)], 0.5)
    p.put(spoon, 'X', 5.4)
    p.px(tx + 5, ty - 31, 'X', 6.6)
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


# ---------------------------------------------------------------- Alexei (seated, seen from behind-left)
FIG_A = (112, 94, 228, 220)


def fig_alexei_frame(turn: int, breath: int):
    x0, y0, w, h = FIG_A
    R = ramps_a()
    p = Paint(w, h, R, 'fig_alexei', x0, y0)
    yy, xx = p.yy, p.xx
    lamp = point_light(h, w, A_LAMP[0], A_LAMP[1], 380, x0, y0, power=1.1)
    lampdir = (1.0, 0.15)
    b = breath
    # ---------- torso in the padded coat (mirror of Konrad: near shoulder + arm on the left)
    torso = p.poly([(219, 161), (204, 165 - b), (182, 162 - b), (158, 166 - b), (136, 172 - b), (121, 183 - b),
                    (115, 200), (117, 236), (119, 276), (114, 314), (250, 314), (252, 282), (254, 248), (253, 214),
                    (250, 190 - b), (242, 176 - b), (230, 166 - b)])
    arm = p.poly([(135, 176 - b), (120, 182 - b), (110, 196), (104, 222), (99, 250), (96, 268), (100, 280),
                  (112, 284), (122, 270), (128, 240), (132, 208)])
    coat = torso | arm
    p.put(coat, 'A', 1.2 - np.clip((yy - 170) / 140, 0, 1) * 0.6, flat=True)
    p.add(coat, edge_light(coat, (0.3, -1.0), 4.0) * 2.4)                       # window light (cold-ish)
    p.add(coat, edge_light(coat, lampdir, 7.0) * np.clip(lamp * 2.2, 0, 1) * 2.4)
    # quilted padding: curved horizontal seams across the back and the sleeve
    for k in range(12):
        yq = 178 + k * 11
        pts = [(112, yq + 6), (150, yq + 1), (190, yq), (230, yq + 2), (256, yq + 6)]
        seam = p.line(pts, 0.5) & torso
        p.add(seam, -0.4)
        p.add(shift(seam, 0, 2) & torso & ~seam, 0.22)
    for xq in (150, 196, 238):                                              # vertical stitching
        p.add(p.line([(xq, 172), (xq + 2, 314)], 0.5) & torso, -0.25)
    for k in range(7):
        yq = 196 + k * 12
        seam = p.line([(96, yq + 2), (134, yq - 2)], 0.5) & arm
        p.add(seam, -0.5)
    crease = p.line([(134, 178), (130, 206), (126, 240), (122, 268)], 0.6) & coat
    p.put(crease, 'A', 0.2)
    rimw = coat & rim(coat, 1, 0, 1) & (yy < 244) & (yy > 164)
    p.put(rimw, 'L', 0.9 + np.clip(lamp * 2.0, 0, 1.8))
    # satchel strap across the back (his satchel hangs at the other hip)
    strap = p.line([(132, 182), (170, 220), (210, 262), (240, 300)], 1.9) & torso
    p.put(strap, 'G', 1.0 + edge_light(strap, (0.3, -1), 2) * 1.4)
    p.put(strap & rim(strap, 0, 1, 1), 'G', 0.4)
    p.put(p.box(176, 224, 183, 231) & strap, 'X', 4.6)                          # buckle
    # ---------- collar of the padded coat
    collar = p.poly([(221, 152), (213, 148), (200, 149), (188, 149), (180, 153), (177, 161), (185, 166 - b),
                     (204, 167 - b), (219, 163)])
    p.put(collar, 'A', 1.9)
    p.add(collar, edge_light(collar, lampdir, 4) * 1.8 + edge_light(collar, (0, -1), 2) * 1.6)
    # ---------- head: lost profile to the right (cheek beyond the near ear flap), lit by the wall lamp
    skull = p.ell(203, 141, 14.0, 14.0) & (yy >= 130)
    neck = p.box(197, 150, 210, 158)
    if turn == 0:
        face_pts = [(216, 133), (222, 136), (225, 142), (225, 149), (222, 155), (217, 159), (211, 160), (212, 150)]
    else:
        face_pts = [(215, 133), (220, 136), (223, 142), (223, 149), (220, 155), (216, 159), (211, 160), (212, 150)]
    face = p.poly(face_pts)
    head = skull | face | neck
    p.put(head, 'F', 1.0)
    p.put(neck, 'F', 0.3)
    hair = skull & ~face & (yy < 153)
    p.put(hair, 'U', 0.7, flat=True)
    fl = edge_light(face, lampdir, 6.0, soft=1)
    p.put(face, 'F', 1.6 + fl * 3.4)
    p.add(face & (yy > 155), -0.7)
    if turn == 0:
        nose = p.poly([(224, 140), (229, 144), (227, 147), (224, 147)])
        p.put(nose, 'F', 3.8)
        p.px(228, 144, 'F', 5.4)
    p.px(222, 152, 'F', 2.0)
    # ---------- shapka: fur crown, turned-up fur band, ear flaps hanging at the sides
    crown = p.poly([(184, 128), (183, 116), (187, 107), (195, 101), (205, 99), (215, 101), (222, 107), (225, 116),
                    (224, 128)])
    band = p.poly([(180, 132), (181, 122), (186, 119), (204, 118), (222, 119), (228, 122), (229, 132), (224, 135),
                   (204, 136), (184, 135)])
    flap_far = p.poly([(181, 130), (190, 131), (191, 146), (188, 153), (182, 151), (179, 140)])
    flap_near = p.poly([(212, 132), (220, 132), (221, 144), (218, 153), (213, 152), (211, 141)])
    hat = crown | band | flap_far | flap_near
    fur = pg.value_noise(w, h, 2, 321 + turn, octaves=2)
    tuft = pg.white_noise(w, h, 322)
    p.put(crown, 'U', 2.0 + (fur - 0.5) * 2.2 + edge_light(crown, (0.4, -1), 3) * 1.8)
    p.put(band, 'U', 2.6 + (fur - 0.5) * 2.4 + edge_light(band, lampdir, 4) * 2.4)
    p.put(flap_far, 'U', 1.5 + (fur - 0.5) * 1.6)
    p.put(flap_near, 'U', 1.8 + (fur - 0.5) * 1.8 + edge_light(flap_near, lampdir, 3) * 2.2)
    p.add(band & (yy > 133), -0.9)
    p.add(crown & (yy > 126), -0.8)
    p.add(hat & (tuft > 0.82), 0.9)
    p.add(hat & (tuft < 0.12), -0.9)
    top_edge = hat & rim(hat, 0, -1, 1)
    p.put(top_edge, 'U', 3.6 + (tuft > 0.5) * 1.0)
    edge_out = kit.dilate(hat, 1) & ~hat & (tuft > 0.7) & (yy < 132)     # ragged fur silhouette
    p.put(edge_out, 'U', 2.6)
    p.add(head & shift(band, 0, -1) & ~band, -0.8)
    sil = coat | collar | head | hat
    out = kit.dilate(sil, 1) & ~sil
    p.put(out & (xx > 170) & (yy < 236), 'A', 0.1)
    p.resolve(band=3.2)
    return p.L


def fig_alexei():
    frames = [fig_alexei_frame(turn, breath) for turn in (0, 1) for breath in (0, 1)]
    x0, y0, w, h = FIG_A
    sheet = np.zeros((h, w * 4, 4), np.uint8)
    for i, L in enumerate(frames):
        sheet[:, i * w:(i + 1) * w] = L.c
    LAYOUT['trains']['fig_alexei'] = [x0, y0]
    return sheet


def refl_alexei():
    """Additive reflections: the wall lamp and the glowing tea glass on the cold glass; no face (cold car)."""
    a = np.zeros((VH, VW, 3), np.float32)
    yy, xx = grid(VH, VW)
    g = glass_mask()
    d = np.hypot((xx - 452) / 12, (yy - 150) / 8)
    for c, v in enumerate((60, 40, 20)):
        a[..., c] += np.clip(1 - d, 0, 1) ** 1.4 * v
    d2 = np.hypot((xx - 352) / 9, (yy - 214) / 7)
    for c, v in enumerate((34, 20, 9)):
        a[..., c] += np.clip(1 - d2, 0, 1) ** 1.4 * v
    a[~g] = 0
    q = np.floor(a / 4.0 + pg.bayer(VW, VH)[..., None]) * 4.0
    out = np.zeros((VH, VW, 4), np.uint8)
    out[..., :3] = np.clip(q, 0, 255).astype(np.uint8)
    out[..., 3] = np.where(out[..., :3].max(-1) > 0, 255, 0)
    return out


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
# Veltrava from the near bank: the three-arch railway bridge (the commission's arms) carries both trains into the
# city.  The old town and the palais dome stand against the slate-blue dawn (brightening in the east = right),
# the river half frozen below.  Trains run on the deck between the far railing (bg) and the near parapet (fg).
DAWN_SKY = V['night'][1:] + V['slate'][:4] + V['sky']        # 0..12, monotonic luminance
PARAPET_Y = 184                                               # top of the near parapet (bridge_fg)
TRAIN_H = 28
TRAIN_DE_Y, TRAIN_SU_Y = 160, 164                             # sprite tops; rail level = top + TRAIN_H
ARCHES = [(48, 222), (236, 404), (418, 592)]                  # x spans of the three arch openings
ARCH_CY, ARCH_RY = 236, 34                                    # arch intrados: ellipse centre row / rise
WATER_Y = 240
QUAY_LAMPS = [34, 118, 206, 294, 378, 466, 550, 626]
PARAPET_LAMPS = [36, 128, 220, 312, 404, 496, 588]


def ramps_dawn():
    return ramps(
        S=DAWN_SKY,
        N=V['night'] + V['slate'][:3],                                      # silhouettes 0..6
        W=V['snow'],
        L=V['lamp'],
        P=V['patina'],
        I=V['iron'] + [V['slate'][4], V['slate'][5]],                       # iron / stone 0..6
        C=V['cream'],
        R=V['red'],
        K=[V['night'][1], V['night'][3], V['slate'][1], V['slate'][3], V['sky'][0], V['sky'][2], V['sky'][4]],
        G=V['patina'][:3] + [V['slate'][2]],                                # frozen reeds, dark bank growth
    )


def _arch_mask(p: Paint, x0, x1, cy=ARCH_CY, ry=ARCH_RY):
    cx = (x0 + x1) / 2
    return p.ell(cx, cy, (x1 - x0) / 2, ry) & (p.yy < cy)


def _roof_run(p: Paint, xs, base, tone, seed, hz=None):
    """A run of gabled / hipped roofs between the x breakpoints xs at base row `base` (silhouette layer)."""
    rng = np.random.default_rng(seed)
    for a, b in zip(xs[:-1], xs[1:]):
        h = rng.uniform(10, 24)
        kind = rng.integers(0, 3)
        if kind == 0:                                           # gable
            pts = [(a, base), (a, base - h * 0.55), ((a + b) / 2, base - h), (b, base - h * 0.55), (b, base)]
        elif kind == 1:                                         # mansard
            pts = [(a, base), (a, base - h * 0.5), (a + 4, base - h), (b - 4, base - h), (b, base - h * 0.5), (b, base)]
        else:                                                   # flat with a chimney
            pts = [(a, base), (a, base - h * 0.7), (b, base - h * 0.7), (b, base)]
        m = p.poly(pts)
        t = tone if hz is None else tone + hz
        p.put(m, 'N', t)
        if kind == 2:
            cx = rng.uniform(a + 3, b - 3)
            p.put(p.box(cx, base - h * 0.7 - 5, cx + 2, base - h * 0.7), 'N', t)
        # a few lit windows
        for _ in range(int(rng.integers(0, 3))):
            wx = rng.uniform(a + 2, b - 4); wy = base - rng.uniform(3, max(4, h * 0.5))
            p.put(p.box(wx, wy, wx + 2, wy + 2), 'L', float(rng.choice([2.0, 3.0, 3.5])), emis=True)


def bridge_bg():
    R = ramps_dawn()
    p = Paint(VW, VH, R, 'bridge_bg')
    yy, xx = p.yy, p.xx
    allm = np.ones((VH, VW), bool)
    east = np.clip((xx - 100) / 540, 0, 1)
    # ---- sky: slate above, the dawn low in the east; stratus bands with lit undersides
    down = np.clip((yy - 40) / 118, 0, 1)
    sky = 4.4 + down ** 1.25 * (5.4 + 3.2 * east) + east * 0.6
    sky += (pg.value_noise(VW, VH, 56, 401, octaves=3) - 0.5) * 0.8
    p.put(allm, 'S', sky)
    rng = np.random.default_rng(402)
    for _ in range(11):
        by = rng.uniform(50, 122); x0 = rng.uniform(-80, 560); ln = rng.uniform(100, 300); th = rng.uniform(1.2, 3.6)
        band = (np.abs(yy - by - 0.012 * (xx - x0)) < th) & (xx > x0) & (xx < x0 + ln)
        p.add(band, -1.0)
        p.add(shift(band, 0, -1) & ~band, 0.8)
    # ---- castle hill (far left, deep in haze)
    hill = p.poly([(-5, 160), (-5, 138), (40, 124), (84, 112), (112, 108), (150, 120), (196, 136), (230, 152), (240, 160)])
    p.put(hill, 'N', 5.2 + np.clip((yy - 110) / 50, 0, 1) * 0.6)
    castle = p.box(70, 98, 126, 114) | p.box(76, 88, 84, 100) | p.box(110, 92, 118, 100) | p.box(96, 84, 102, 100)
    p.put(castle, 'N', 4.9)
    for bx in range(70, 126, 4):
        p.put(p.box(bx, 96, bx + 2, 98), 'N', 4.9)
    p.put(p.poly([(96, 84), (99, 78), (102, 84)]), 'N', 4.7)
    p.put(p.box(98, 94, 100, 96), 'L', 2.5, emis=True)
    # ---- old town, second rank (hazy)
    _roof_run(p, [-4, 30, 58, 96, 130, 168, 204, 238, 262, 286, 308, 332, 356, 380, 404, 430, 454, 478, 506, 534,
                  560, 584, 612, 644], 150, 3.8, 403)
    # Gothic cathedral: nave + two spires (one taller), far left-centre
    nave = p.poly([(150, 150), (150, 118), (160, 112), (200, 112), (210, 118), (210, 150)])
    p.put(nave, 'N', 3.4)
    for (sx, top, w) in ((154, 66, 12), (198, 80, 10)):
        tower = p.box(sx, 112, sx + w, 150)
        spire = p.poly([(sx - 1, 112), (sx + w / 2, top), (sx + w + 1, 112)])
        p.put(tower | spire, 'N', 3.2)
        p.put(p.box(sx + w / 2 - 1, 100, sx + w / 2 + 1, 106), 'N', 2.4)           # belfry opening
        p.put(p.line([(sx + w / 2, top), (sx + w / 2, top - 5)], 0.4), 'N', 2.6)   # cross
    for k in range(5):                                                               # buttress pinnacles
        p.put(p.poly([(163 + k * 8, 112), (165 + k * 8, 104), (167 + k * 8, 112)]), 'N', 3.3)
    # baroque church with an onion dome, right of centre
    body = p.box(466, 120, 500, 150)
    p.put(body, 'N', 3.3)
    onion = p.ell(483, 112, 10, 9) | p.poly([(475, 112), (483, 96), (491, 112)])
    p.put(onion, 'P', 1.6 + np.clip((xx - 476) / 14, 0, 1) * 1.3)
    p.put(p.box(482, 90, 484, 97), 'N', 2.4)
    p.put(p.ell(483, 89, 2, 2), 'P', 2.5)
    # town hall tower (right)
    th = p.box(560, 104, 576, 150) | p.poly([(557, 104), (568, 86), (579, 104)])
    p.put(th, 'N', 3.0)
    p.put(p.ell(568, 112, 4, 4), 'C', 3.2, emis=True)                               # lit clock face
    p.put(p.ell(568, 112, 2.5, 2.5), 'C', 4.6, emis=True)
    # ---- the palais of the commission: long classical front, central dome with a lantern and flagpoles
    front = p.box(246, 124, 416, 150)
    p.put(front, 'N', 2.6 + east * 0.3)
    for k in range(13):                                                              # pilaster rhythm
        p.put(p.box(252 + k * 13, 128, 253 + k * 13, 146), 'N', 3.4)
    for k in range(12):
        lit = k in (1, 2, 4, 7, 9, 10)
        p.put(p.box(256 + k * 13, 134, 260 + k * 13, 140), 'L' if lit else 'N', 2.6 if lit else 1.8, emis=lit)
    p.put(p.box(242, 122, 420, 124), 'N', 3.6)                                       # cornice
    p.put(p.box(242, 121, 420, 122), 'W', 1.4)                                       # snow on the cornice
    drum = p.box(302, 106, 360, 124)
    p.put(drum, 'N', 2.7)
    for k in range(8):
        p.put(p.box(306 + k * 7, 109, 307 + k * 7, 122), 'N', 3.5)
    dome = p.ell(331, 108, 31, 26) & (yy < 108)
    dl = np.clip((xx - 310) / 44, 0, 1)                                              # dawn on the east flank
    p.put(dome, 'P', 1.3 + dl * 2.2 + np.clip((yy - 84) / 24, 0, 1) * 0.6)
    for k in range(-3, 4):                                                           # ribs
        rx = 331 + k * 8
        p.put(p.line([(rx, 108), (331 + k * 4.5, 86)], 0.4) & dome, 'P', 0.9 + dl[108, int(rx)] * 1.4)
    p.put(dome & rim(dome, 0, -1, 1), 'P', 3.6 + dl * 1.0)                           # snow-lit crown
    lantern = p.box(326, 72, 336, 83) | p.poly([(324, 72), (331, 64), (338, 72)])
    p.put(lantern, 'N', 2.8)
    p.put(p.box(329, 75, 333, 80), 'L', 2.4, emis=True)
    for fx_ in (264, 298, 364, 398):                                                 # flagpoles with limp flags
        p.put(p.box(fx_, 100, fx_ + 1, 123), 'N', 3.0)
        p.put(p.box(fx_ + 1, 101, fx_ + 3, 108), 'N', 2.4)
    # ---- the riverside: warehouses and the quay street (nearest rank), the quay wall
    _roof_run(p, [-4, 26, 54, 88, 116, 146, 176, 202, 230, 258, 290, 320, 348, 378, 410, 440, 468, 496, 526, 556,
                  586, 616, 644], 158, 1.7, 405)
    p.put(p.box(0, 150, VW, 158), 'N', 1.6)
    for k in range(0, VW, 9):                                                        # street-level windows / arcades
        if (k // 9) % 3 != 1:
            p.put(p.box(k + 2, 152, k + 5, 156), 'L' if (k // 9) % 4 == 0 else 'N', 2.2 if (k // 9) % 4 == 0 else 1.0,
                  emis=(k // 9) % 4 == 0)
    quay = p.box(0, 158, VW, 164)
    p.put(quay, 'I', 1.6 + (pg.value_noise(VW, VH, 5, 406, octaves=1) - 0.5) * 0.8)
    p.put(p.box(0, 158, VW, 159), 'W', 1.6)
    for lx in QUAY_LAMPS:                                                            # quay lamps on the far bank
        p.put(p.box(lx, 148, lx + 1, 158), 'N', 0.8)
        p.put(p.box(lx - 1, 146, lx + 2, 149), 'L', 3.6, emis=True)
        p.put(p.box(lx, 145, lx + 1, 146), 'L', 4.2, emis=True)
    # ---- the bridge: far railing, deck, near spandrel wall, piers, arches with the river through them
    rail = p.box(0, 157, VW, 158) | (p.box(0, 157, VW, 163) & ((xx.astype(int) % 7) == 3))
    p.put(rail, 'I', 0.6)
    p.put(p.box(0, 156, VW, 157), 'I', 4.4)                                          # top rail catches the dawn
    deck = p.box(0, 163, VW, PARAPET_Y)
    dn = pg.value_noise(VW, VH, 9, 407, octaves=2)
    p.put(deck, 'W', 1.1 + (dn - 0.5) * 1.2 - np.clip((yy - 170) / 14, 0, 1) * 0.5)
    sleepers = deck & (yy >= 176) & ((xx.astype(int) % 6) < 2)
    p.add(sleepers, -0.55)
    p.put(p.box(0, 181, VW, 182), 'I', 3.0)                                          # the far rail of the near track
    p.put(p.box(0, 168, VW, 169), 'I', 2.4)                                          # the far track's rail
    # cornice under the near parapet, then the spandrel wall down to the water
    p.put(p.box(0, 194, VW, 196), 'I', 4.0)
    p.put(p.box(0, 193, VW, 194), 'W', 2.0)
    wall = p.box(0, 196, VW, WATER_Y + 8)
    stone = pg.value_noise(VW, VH, 7, 408, octaves=2)
    p.put(wall, 'I', 1.4 + (stone - 0.5) * 0.9 - np.clip((yy - 196) / 50, 0, 1) * 0.5)
    courses = wall & ((yy.astype(int) % 5) == 0)
    p.add(courses, -0.4)
    for (a, b) in ARCHES:
        op = _arch_mask(p, a, b)
        # the river beyond the bridge, lit by the dawn (brighter toward the east), seen through the opening
        p.put(op, 'K', 1.9 + east * 1.9 + np.clip((yy - 204) / 34, 0, 1) * 0.5 +
              (pg.value_noise(VW, VH, 24, 409, octaves=2) - 0.5) * 0.6)
        far_ice = op & (yy > 224) & ((pg.value_noise(VW, VH, 13, 410, octaves=2) + (1 - east) * 0.3) > 0.78)
        p.put(far_ice, 'W', 0.4 + east * 0.6)
        for lx in QUAY_LAMPS:                                                        # quay lamps mirrored
            st = op & (np.abs(xx - lx) < 1.0) & ((yy.astype(int) + lx) % 3 != 0)
            p.put(st, 'L', 0.9 + np.clip(1 - (yy - 200) / 36, 0, 1) * 1.4)
        ring = kit.dilate(op, 2) & ~op
        p.put(ring, 'I', 0.5)                                                        # voussoirs in shadow
        p.put(ring & (yy < 212) & (xx > (a + b) / 2), 'I', 2.6)                      # east side of the arch lit
        key = p.box((a + b) / 2 - 2, 200, (a + b) / 2 + 2, 206) & ~op
        p.put(key, 'I', 3.4)
    for (a, b) in ((222, 236), (404, 418)):                                          # piers with cutwaters
        pier = p.box(a, 200, b, WATER_Y + 10)
        p.put(pier, 'I', 1.0 + np.clip((xx - a) / (b - a), 0, 1) * 1.4)
        p.put(p.poly([(a - 4, WATER_Y + 10), (a - 4, 226), ((a + b) / 2, 214), (b + 4, 226), (b + 4, WATER_Y + 10)]),
              'I', 1.2 + np.clip((xx - a + 4) / (b - a + 8), 0, 1) * 1.2)
        p.put(p.box(a - 4, WATER_Y - 2, b + 4, WATER_Y + 1), 'W', 1.2)               # ice piled at the pier
    # ---- the river in front: dark open water, the dawn mirrored in the eastern channel, ice along the banks
    water = p.box(0, WATER_Y, VW, VH)
    wn = pg.value_noise(VW, VH, 22, 411, octaves=3)
    chan = np.clip(1 - np.abs(xx - 450) / 240, 0, 1)
    wt = 0.9 + chan * 1.7 + east * 1.0 + (wn - 0.5) * 0.9 - np.clip((yy - WATER_Y) / 60, 0, 1) * 0.5
    p.put(water, 'K', wt)
    # the lit arch openings mirrored right below the bridge (horizontal ripple lines)
    for (a, b) in ARCHES:
        mir = water & (xx > a + 16) & (xx < b - 16) & (yy < WATER_Y + 26)
        p.add(mir & ((yy.astype(int) + xx.astype(int) // 5) % 3 == 0), 1.1 * np.clip(1 - (yy - WATER_Y) / 26, 0, 1))
    # faint continuation of the quay-lamp streaks
    for lx in QUAY_LAMPS:
        st = water & (np.abs(xx - lx) < 1.0) & ((yy.astype(int) * 2 + lx) % 5 == 0) & (yy < WATER_Y + 24)
        p.put(st, 'L', 0.6 + np.clip(1 - (yy - WATER_Y) / 24, 0, 1) * 1.0)
    # ice sheets from both banks, thin floes drifting in the channel
    sheet = pg.value_noise(VW, VH, 30, 412, octaves=2)
    edge_w = np.clip(1 - xx / 150, 0, 1) + np.clip((xx - 560) / 80, 0, 1)
    ice = water & ((sheet * 0.6 + edge_w * 0.9 + np.clip((yy - 262) / 40, 0, 1) * 0.5) > 0.95)
    floes = water & (pg.value_noise(VW, VH, 9, 414, octaves=1) > 0.84) & (yy > WATER_Y + 6) & (yy < 280)
    ice |= floes
    p.put(ice, 'W', 0.5 + east * 0.5 + np.clip((yy - 250) / 60, 0, 1) * 0.5 + (wn - 0.5) * 0.5)
    p.put(ice & ~shift(ice, 0, 1), 'W', 1.6)                                         # lit floe edges
    p.put(ice & ~shift(ice, 0, -1) & ~kit.erode(ice, 1), 'K', 0.8)
    p.resolve(band=2.6)
    glints = []
    rng = np.random.default_rng(413)
    for _ in range(40):
        gx = int(rng.uniform(280, 600)); gy = int(rng.uniform(WATER_Y + 4, 282))
        if not ice[gy, gx]:
            glints.append([gx, gy, int(rng.integers(1, 4))])
    LAYOUT['trains']['glints'] = glints
    return p.L


def bridge_fg():
    """Near parapet with its lamp posts (in front of the trains) and the near bank at the bottom."""
    R = ramps_dawn()
    p = Paint(VW, VH, R, 'bridge_fg')
    yy, xx = p.yy, p.xx
    par = p.box(0, PARAPET_Y, VW, 194)
    st = pg.value_noise(VW, VH, 6, 421, octaves=2)
    p.put(par, 'I', 1.6 + (st - 0.5) * 0.8 + np.clip((xx - 100) / 540, 0, 1) * 0.4)
    p.put(par & ((xx.astype(int) % 11) == 0), 'I', 0.9)                              # balustrade joints
    p.put(p.box(0, PARAPET_Y, VW, PARAPET_Y + 1), 'W', 1.5)                          # snow on the coping
    p.put(p.box(0, PARAPET_Y + 1, VW, PARAPET_Y + 2), 'I', 3.6)
    for lx in PARAPET_LAMPS:
        p.put(p.box(lx - 2, PARAPET_Y - 2, lx + 3, PARAPET_Y + 1), 'I', 0.8)        # plinth
        p.put(p.box(lx, PARAPET_Y - 22, lx + 1, PARAPET_Y - 1), 'I', 0.9)           # post
        p.put(p.box(lx - 1, PARAPET_Y - 24, lx + 2, PARAPET_Y - 22), 'I', 1.2)
        p.put(p.box(lx - 2, PARAPET_Y - 30, lx + 3, PARAPET_Y - 24), 'L', 3.3, emis=True)    # lantern
        p.put(p.box(lx - 1, PARAPET_Y - 28, lx + 2, PARAPET_Y - 25), 'L', 4.4, emis=True)
        p.put(p.box(lx - 2, PARAPET_Y - 31, lx + 3, PARAPET_Y - 30), 'I', 2.6)      # cap
        p.put(p.box(lx - 1, PARAPET_Y - 32, lx + 2, PARAPET_Y - 31), 'W', 1.2)
    # ---- near bank: a snow slope falling into its own blue shadow, reed clumps, a bare tree at the right
    bank_top = 283 + (wrap_noise(VW, 1, 70, 422)[0] * 7).astype(int) - np.clip((xx[0] - 520) / 120, 0, 1).astype(int) * 2
    bank = yy >= bank_top[None, :]
    sn = pg.value_noise(VW, VH, 14, 423, octaves=2)
    p.put(bank, 'W', 1.6 + (sn - 0.5) * 0.8 - np.clip((yy - 290) / 24, 0, 1) * 1.2)
    p.put(bank & ~shift(bank, 0, 1), 'W', 3.0)
    p.put(bank & (yy > 304), 'S', 5.6 + (sn - 0.5) * 0.8)                            # the slope in shadow
    p.put(bank & (yy > 302) & (yy <= 304), 'S', 7.0)
    rng = np.random.default_rng(424)
    for _ in range(14):                                                              # frozen reed clumps
        rx = int(rng.uniform(20, 560)); base = int(bank_top[rx])
        for k in range(int(rng.integers(3, 7))):
            h = int(rng.uniform(4, 11)); dx = rng.uniform(-3, 3)
            p.put(p.line([(rx + dx, base + 2), (rx + dx + rng.uniform(-1.5, 1.5), base - h)], 0.4), 'G',
                  float(rng.uniform(0.4, 2.2)))
    # bare tree (trunk at the right edge, branches over the water, snow on their upper sides)
    trunk = p.poly([(606, 320), (610, 268), (612, 240), (616, 240), (620, 268), (626, 320)])
    p.put(trunk, 'N', 0.6 + np.clip((xx - 606) / 20, 0, 1) * 0.8)
    for pts in (((613, 244), (590, 226), (566, 214)), ((613, 242), (618, 222), (610, 204)), ((615, 246), (636, 230),
                (650, 220)), ((590, 226), (582, 212)), ((596, 229), (600, 214)), ((618, 222), (630, 212)),
                ((613, 258), (596, 250), (584, 248))):
        br = p.line(list(pts), 0.9)
        p.put(br, 'N', 0.7)
        p.put(br & ~shift(br, 0, 1), 'W', 1.4)
    p.put(trunk & ~shift(trunk, 1, 0), 'W', 0.8)                                     # snow on the trunk's east side
    p.resolve(band=2.6)
    return p.L


def _paint_coach(p: Paint, x0, w, body_ramp, body_tone, roof_tone, lit, frame, pennant=False, boxcar=False):
    """One passenger coach / boxcar from x0 to x0+w on a TRAIN_H-row sprite, rail level at row 28."""
    yy, xx = p.yy, p.xx
    body = p.rr(x0 + 1, 8, x0 + w - 1, 24, 2)
    p.put(body, body_ramp, body_tone + np.clip((xx - x0) / w, 0, 1) * 0.6)
    p.put(body & (yy >= 22), body_ramp, body_tone - 0.5)
    roof = p.rr(x0 + 1, 5, x0 + w - 1, 9, 3)
    p.put(roof, 'I', roof_tone)
    p.put(roof & (yy < 7), 'W', 1.6)                                                 # snow-dusted roof
    p.put(p.box(x0 + 3, 8, x0 + w - 3, 9), 'I', 1.0)                                 # roof shadow line
    if boxcar:
        door = p.box(x0 + w // 2 - 7, 10, x0 + w // 2 + 7, 23)
        p.put(door & ~kit.erode(door, 1), body_ramp, body_tone - 0.7)
        p.put(p.box(x0 + w // 2 - 7, 15, x0 + w // 2 + 7, 16), body_ramp, body_tone - 0.6)
        tm = text('4', '35')
        p.put(np.pad(tm, ((12, TRAIN_H - 17), (x0 + 6, p.w - x0 - 9)))[:p.h, :p.w], 'W', 2.0)
        # lead seal plate catching the lamp light
        p.put(p.box(x0 + w // 2 + 9, 17, x0 + w // 2 + 12, 19), 'L', 1.6)
    else:
        k = 0
        for wx in range(x0 + 7, x0 + w - 8, 7):
            win = p.box(wx, 11, wx + 4, 17)
            on = lit[k % len(lit)]
            p.put(win, 'L' if on else 'N', 2.4 + (k % 3) * 0.4 if on else 0.5, emis=on)
            if on:
                p.put(p.box(wx, 11, wx + 4, 12), 'L', 3.6, emis=True)
            k += 1
        for dx in (x0 + 2, x0 + w - 5):                                              # end doors
            p.put(p.box(dx, 10, dx + 3, 23), body_ramp, body_tone - 0.6)
            p.put(p.box(dx + 1, 12, dx + 2, 15), 'N', 1.2)
    p.put(p.box(x0 + 1, 24, x0 + w - 1, 25), 'N', 0.6)                               # underframe
    for bx in (x0 + 9, x0 + w - 13):                                                 # bogies
        p.put(p.box(bx - 2, 24, bx + 6, 26), 'N', 0.3)
        for wx in (bx - 1, bx + 5):
            wh = p.ell(wx, 26.5, 2.4, 2.4)
            p.put(wh, 'N', 0.2)
            p.put(wh & rim(wh, 1 if frame == 0 else -1, 0, 1), 'I', 2.4)
    p.put(p.box(x0 - 1, 19, x0 + 1, 21), 'I', 1.0)                                   # coupling
    if pennant:
        p.put(p.box(x0 + w - 3, 1, x0 + w - 2, 6), 'I', 2.6)
        fl = [(x0 + w - 2, 1), (x0 + w + 2 + frame, 2), (x0 + w - 2, 4)]
        p.put(p.poly(fl), 'W', 2.6 if frame == 0 else 2.0)
        p.put(p.poly(fl) & (yy >= 3), 'N', 0.4)


def _paint_loco(p: Paint, x0, side, frame):
    """Steam locomotive (62 px) with its tender (26 px).  side 'de': front at the right; 'su': front at the left."""
    yy, xx = p.yy, p.xx
    if side == 'de':
        f = lambda dx: x0 + dx                                                       # noqa: E731 (dx from the tender end)
    else:
        f = lambda dx: x0 + 88 - dx                                                  # noqa: E731
    lo = lambda a, b: (min(a, b), max(a, b))                                         # noqa: E731
    # tender
    a, b = lo(f(0), f(26))
    p.put(p.box(a + 1, 10, b - 1, 24), 'I', 1.3)
    p.put(p.box(a + 2, 8, b - 2, 11), 'N', 0.4)                                      # coal
    p.put(p.box(a + 1, 10, b - 1, 11), 'I', 2.6)
    for wx in (a + 6, a + 13, a + 20):
        wh = p.ell(wx, 26.5, 2.4, 2.4)
        p.put(wh, 'N', 0.2)
        p.put(wh & rim(wh, 1 if frame == 0 else -1, 0, 1), 'I', 2.2)
    # cab
    a, b = lo(f(26), f(40))
    p.put(p.box(a, 7, b, 24), 'I', 1.5)
    p.put(p.box(a - 1, 6, b + 1, 8), 'I', 2.6)
    p.put(p.box(a + 1, 5, b - 1, 7), 'W', 1.4)
    p.put(p.box(a + 4, 10, a + 8, 15), 'L', 2.6, emis=True)                          # lit cab window
    # boiler
    a, b = lo(f(40), f(84))
    boil = p.rr(a, 9, b, 21, 3)
    p.put(boil, 'I', 1.6 + np.clip((yy - 9) / 12, 0, 1) * -0.9)
    p.put(boil & (yy < 11), 'I', 3.4)
    p.put(boil & (yy < 10), 'W', 0.6)                                                # snow on top
    p.put(p.box(a, 21, b, 24), 'N', 0.5)                                             # running gear shadow
    dome_x = f(58)
    p.put(p.ell(dome_x, 9, 3.5, 2.5) & (yy < 9), 'I', 2.6)
    chim = f(76)
    p.put(p.box(chim - 2, 2, chim + 2, 9), 'I', 1.4)
    p.put(p.box(chim - 3, 2, chim + 3, 3), 'I', 2.6)
    # smoke deflectors + smokebox front + headlights
    front = f(88)
    fa, fb = lo(f(84), front)
    p.put(p.box(fa, 8, fb, 21), 'I', 1.1)
    hl_x = f(86)
    p.put(p.box(hl_x - 1, 10, hl_x + 1, 12), 'L', 4.2, emis=True)
    p.put(p.box(hl_x - 1, 17, hl_x + 1, 19), 'L', 3.4, emis=True)
    da, db = lo(f(80), f(81))
    p.put(p.box(da, 5, db + 1, 19), 'I', 2.8)
    # drivers with rods (two frames: the rod moves)
    for k, wx in enumerate((f(48), f(58), f(68))):
        wh = p.ell(wx, 25, 3.6, 3.6)
        p.put(wh, 'N', 0.25)
        p.put(wh & ~kit.erode(wh, 1), 'I', 1.6)
        p.put(p.box(wx, 25, wx + 1, 26), 'I', 2.8)
    rod_y = 26 if frame == 0 else 24
    a, b = lo(f(46), f(70))
    p.put(p.box(a, rod_y, b, rod_y + 1), 'I', 2.4)
    for wx in (f(78), f(85)):                                                        # leading truck
        wh = p.ell(wx, 26.5, 2.2, 2.2)
        p.put(wh, 'N', 0.25)
    LAYOUT['trains']['train_' + side]['chimney'] = [int(chim), 2]


def train_sheet(side):
    W = 368
    sheet = np.zeros((TRAIN_H * 2, W, 4), np.uint8)
    LAYOUT['trains']['train_' + side] = {'front': W if side == 'de' else 0, 'y': TRAIN_DE_Y if side == 'de' else TRAIN_SU_Y,
                                         'w': W}
    for fr in range(2):
        R = ramps_dawn()
        p = Paint(W, TRAIN_H, R, 'train_' + side)
        if side == 'de':
            for i in range(4):
                _paint_coach(p, i * 70, 70, 'I', 1.3, 2.6, [1, 1, 0, 1, 0, 1, 1, 0], fr, pennant=True)
            _paint_loco(p, 280, 'de', fr)
        else:
            _paint_loco(p, 0, 'su', fr)
            for i in range(3):
                _paint_coach(p, 88 + i * 70, 70, 'P', 1.6, 2.3, [0, 1, 1, 0, 1, 0, 0, 1], fr)
            _paint_coach(p, 298, 70, 'P', 1.5, 2.3, [], fr, boxcar=True)
        p.resolve(band=2.6)
        sheet[fr * TRAIN_H:(fr + 1) * TRAIN_H] = p.L.c
    return sheet


def train_de():
    return train_sheet('de')


def train_su():
    return train_sheet('su')


def smoke():
    """Six frames of a steam puff growing and thinning (26 x 26 each); lit from the east."""
    n, fw, fh = 6, 26, 26
    sheet = np.zeros((fh, fw * n, 4), np.uint8)
    for i in range(n):
        u = i / (n - 1)
        r = 3.5 + 8.5 * u
        yy, xx = grid(fh, fw)
        d = np.hypot((xx + 0.5 - fw / 2) / r, (yy + 0.5 - fh / 2 - u * 1.5) / (r * 0.85))
        nz = pg.value_noise(fw, fh, 4, 501 + i, octaves=2)
        core = np.clip(1 - d, 0, 1) ** 0.7 + (nz - 0.5) * 0.5
        dens = np.clip(core, 0, 1) * (1.0 - 0.58 * u)
        m = (dens > pg.bayer(fw, fh, i * 5, i * 3) * 0.7) & (dens > 0.08)
        lit = np.clip((xx - fw / 2) / r * 0.5 + (fh / 2 - yy) / r * 0.5 + 0.5, 0, 1)
        cols = [pg.hx(c) for c in (V['sky'][1], V['sky'][2], V['snow'][1], V['snow'][2], V['snow'][3])]
        idx = np.clip((lit * 2.4 + core * 1.0 - u * 1.0 + 0.3).round().astype(int), 0, 4)
        for ci in range(5):
            sel = m & (idx == ci)
            sheet[:, i * fw:(i + 1) * fw][sel] = cols[ci]
    LAYOUT['trains']['smoke'] = {'frames': n}
    return sheet


def dawn_glow():
    """Additive warmth of the dawn: a band behind the city and the lit water channel (runtime fades it in)."""
    yy, xx = grid(VH, VW)
    a = np.zeros((VH, VW, 3), np.float32)
    east = np.clip((xx - 160) / 480, 0, 1)
    band = np.clip(1 - np.abs(yy - 128) / 70, 0, 1) ** 1.6 * (0.25 + 0.75 * east)
    for c, v in enumerate((84, 50, 20)):
        a[..., c] += band * v
    water = (yy > WATER_Y - 2) & (yy < 300)
    ref = np.clip(1 - np.abs(xx - 460) / 150, 0, 1) ** 1.3 * np.clip(1 - (yy - WATER_Y) / 58, 0, 1) * water
    for c, v in enumerate((44, 28, 12)):
        a[..., c] += ref * v
    return quant_add(a, 8.0)


def fg_glow():
    """Halos of the parapet lanterns (additive, drawn over the trains and the parapet)."""
    yy, xx = grid(VH, VW)
    a = np.zeros((VH, VW, 3), np.float32)
    for lx in PARAPET_LAMPS:
        d = np.hypot((xx + 0.5 - lx - 0.5) / 15.0, (yy + 0.5 - (PARAPET_Y - 27)) / 11.0)
        g = np.clip(1 - d, 0, 1) ** 1.5
        for c, v in enumerate((66, 42, 18)):
            a[..., c] += g * v
    return quant_add(a, 8.0)
