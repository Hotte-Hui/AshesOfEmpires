"""env_karsk_lib -- shared helpers for the Karsk railyard environment (scene A1).

Area: env_karsk.  Builds on tools/pixelgen/pg.py (never modifies it).
Everything here is original procedural pixel art; no reference image is sampled.
"""
from __future__ import annotations

import math
import os
import sys

sys.path.insert(0, 'C:/Spiele/AshesOfEmpires/tools/pixelgen')
import numpy as np  # noqa: E402
from PIL import Image  # noqa: E402

import pg  # noqa: E402
from pg import Layer, hx, bayer, value_noise  # noqa: E402,F401

ROOT = 'C:/Spiele/AshesOfEmpires'
ENV_DIR = ROOT + '/assets/environments/karsk_railyard'
DOC_DIR = ROOT + '/assets/ui/documents'

KP = pg.PALETTES['karsk']


def _r(n):
    return [hx(c) for c in KP[n]]


NI, TE, SA, SK, ST, RU, CO, SN, WO = (_r(n) for n in
                                      ('night', 'teal', 'sage', 'sky', 'stone', 'rust', 'copper', 'snow', 'wood'))
# Story accent (C-17 stamp, signal lamp): the shared C-17 red ramp of the project's 'sepia' palette.
RED = [hx(c) for c in pg.PALETTES['sepia']['red']]
ALL = pg.all_colors('karsk') + RED
CLEAR = np.zeros(4, np.uint8)


def col_key(c):
    c = np.asarray(c, np.int64)
    return (c[..., 0] << 16) | (c[..., 1] << 8) | c[..., 2]


# --------------------------------------------------------------------------- pixel fonts
# 5x7 capitals for painted signs and the civic banner (fictional slogan, Cyrillic).
FONT_L = {
    'В': ["####.", "#...#", "#...#", "####.", "#...#", "#...#", "####."],
    'О': [".###.", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."],
    'С': [".###.", "#...#", "#....", "#....", "#....", "#...#", ".###."],
    'Т': ["#####", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."],
    'А': [".###.", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"],
    'Н': ["#...#", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"],
    'И': ["#...#", "#...#", "#..##", "#.#.#", "##..#", "#...#", "#...#"],
    'М': ["#...#", "##.##", "#.#.#", "#.#.#", "#...#", "#...#", "#...#"],
    'Е': ["#####", "#....", "#....", "####.", "#....", "#....", "#####"],
    'К': ["#...#", "#..#.", "#.#..", "##...", "#.#..", "#..#.", "#...#"],
    'Р': ["####.", "#...#", "#...#", "####.", "#....", "#....", "#...."],
    'Д': [".###.", ".#.#.", ".#.#.", ".#.#.", ".#.#.", "#####", "#...#"],
    'П': ["#####", "#...#", "#...#", "#...#", "#...#", "#...#", "#...#"],
    'Л': ["..###", ".#..#", ".#..#", ".#..#", ".#..#", ".#..#", "#...#"],
    'Ч': ["#...#", "#...#", "#...#", ".####", "....#", "....#", "....#"],
    'Й': [".#.#.", "#...#", "#..##", "#.#.#", "##..#", "#...#", "#...#"],
    'Г': ["#####", "#....", "#....", "#....", "#....", "#....", "#...."],
    'У': ["#...#", "#...#", "#...#", ".####", "....#", "#...#", ".###."],
    'Ы': ["#...#", "#...#", "#...#", "###.#", "#.#.#", "#.#.#", "###.#"],
    'Я': [".####", "#...#", "#...#", ".####", "..#.#", ".#..#", "#...#"],
    'Б': ["#####", "#....", "#....", "####.", "#...#", "#...#", "####."],
    'Ж': ["#.#.#", "#.#.#", ".###.", "..#..", ".###.", "#.#.#", "#.#.#"],
    'C': [".###.", "#...#", "#....", "#....", "#....", "#...#", ".###."],
    '-': ["....", "....", "....", "###.", "....", "....", "...."],
    '1': [".#.", "##.", ".#.", ".#.", ".#.", ".#.", "###"],
    '7': ["#####", "....#", "...#.", "..#..", ".#...", ".#...", ".#..."],
    '6': [".###.", "#....", "#....", "####.", "#...#", "#...#", ".###."],
    '4': ["...#.", "..##.", ".#.#.", "#..#.", "#####", "...#.", "...#."],
    '9': [".###.", "#...#", "#...#", ".####", "....#", "....#", ".###."],
    '0': [".###.", "#...#", "#..##", "#.#.#", "##..#", "#...#", ".###."],
    '2': [".###.", "#...#", "....#", "...#.", "..#..", ".#...", "#####"],
    '.': [".", ".", ".", ".", ".", ".", "#"],
}

# 5-row small capitals (variable width) for plates, stencils and stall signs.
FONT_S = {
    'А': ["###", "#.#", "###", "#.#", "#.#"], 'В': ["##.", "#.#", "##.", "#.#", "##."],
    'Г': ["###", "#..", "#..", "#..", "#.."], 'Д': ["..##", ".#.#", ".#.#", "####", "#..#"],
    'Е': ["###", "#..", "##.", "#..", "###"], 'Ж': ["#.#.#", ".###.", "..#..", ".###.", "#.#.#"],
    'З': ["##.", "..#", ".#.", "..#", "##."], 'И': ["#..#", "#.##", "##.#", "#..#", "#..#"],
    'К': ["#.#", "#.#", "##.", "#.#", "#.#"], 'Л': [".##", "#.#", "#.#", "#.#", "#.#"],
    'М': ["#...#", "##.##", "#.#.#", "#...#", "#...#"], 'Н': ["#.#", "#.#", "###", "#.#", "#.#"],
    'О': ["###", "#.#", "#.#", "#.#", "###"], 'П': ["###", "#.#", "#.#", "#.#", "#.#"],
    'Р': ["###", "#.#", "###", "#..", "#.."], 'С': ["###", "#..", "#..", "#..", "###"],
    'Т': ["###", ".#.", ".#.", ".#.", ".#."], 'У': ["#.#", "#.#", "###", "..#", "##."],
    'Ч': ["#.#", "#.#", "###", "..#", "..#"], 'Ы': ["#..#", "#..#", "##.#", "#.##", "##.#"],
    'Я': ["###", "#.#", "###", ".##", "#.#"], 'Й': ["#.#", "#.#", "#.#", "##.", "#.#"],
    'Ш': ["#.#.#", "#.#.#", "#.#.#", "#.#.#", "#####"], 'Б': ["###", "#..", "###", "#.#", "###"],
    'C': ["###", "#..", "#..", "#..", "###"],
    '0': ["###", "#.#", "#.#", "#.#", "###"], '1': [".#", "##", ".#", ".#", ".#"],
    '2': ["##.", "..#", ".#.", "#..", "###"], '3': ["##.", "..#", ".#.", "..#", "##."],
    '4': ["#.#", "#.#", "###", "..#", "..#"], '5': ["###", "#..", "##.", "..#", "##."],
    '6': [".##", "#..", "###", "#.#", "###"], '7': ["###", "..#", ".#.", ".#.", ".#."],
    '8': ["###", "#.#", "###", "#.#", "###"], '9': ["###", "#.#", "###", "..#", "##."],
    '-': ["...", "...", "##.", "...", "..."], '.': [".", ".", ".", ".", "#"],
    ':': [".", "#", ".", "#", "."], '/': ["..#", "..#", ".#.", "#..", "#.."],
    '·': [".", ".", "#", ".", "."],
}


def text_width(s: str, font: str = 's', spacing: int = 1) -> int:
    f = FONT_S if font == 's' else FONT_L
    w = 0
    for ch in s:
        if ch == ' ':
            w += 2 if font == 's' else 3
        else:
            w += len(f.get(ch, ['###'])[0]) + spacing
    return max(0, w - spacing)


def text(L: Layer, x: int, y: int, s: str, col, font: str = 's', spacing: int = 1, hgt=None, em=None,
         shadow=None):
    """Draw pixel text; returns width.  shadow: colour drawn 1 px down-left (painted letters)."""
    f = FONT_S if font == 's' else FONT_L
    cx = x
    for ch in s:
        if ch == ' ':
            cx += 2 if font == 's' else 3
            continue
        g = f.get(ch)
        if g is None:
            cx += 4
            continue
        for r, row in enumerate(g):
            for c, v in enumerate(row):
                if v == '#':
                    if shadow is not None:
                        L.px(cx + c - 1, y + r + 1, shadow)
        for r, row in enumerate(g):
            for c, v in enumerate(row):
                if v == '#':
                    L.px(cx + c, y + r, col, hgt, em)
        cx += len(g[0]) + spacing
    return cx - x - spacing


# --------------------------------------------------------------------------- dithering / ramps
def dmask(w: int, h: int, x0: int, y0: int, t, size: int = 4) -> np.ndarray:
    """Ordered-dither coverage mask: True where bayer threshold < t (t scalar or (h, w) array)."""
    return bayer(w, h, x0, y0, size) < t


def ladder_shift(L: Layer, ladder, amount, x0=0, y0=0, x1=None, y1=None, mask=None, size: int = 4):
    """Move every pixel whose colour is in `ladder` (ordered list) by `amount` steps (float or (h,w)
    array, may be negative) with ordered dither -> clean 2-colour transitions (fog, stains, grime)."""
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


def vfade(y0: int, y1: int, h: int, w: int, steps: float, power: float = 1.0, top0: int = 0) -> np.ndarray:
    """(h, w) array: 0 above y0, rising to `steps` at y1 (rows in layer coordinates offset top0)."""
    rows = np.arange(h, dtype=np.float32)[:, None] + top0
    t = np.clip((rows - y0) / max(1, (y1 - y0)), 0, 1) ** power
    return np.repeat(t * steps, w, axis=1)


def recolor(L: Layer, mapping: dict, mask=None):
    """Exact colour replace {np colour: np colour}."""
    keys = col_key(L.c[..., :3])
    out = L.c.copy()
    for a, b in mapping:
        m = (keys == col_key(np.asarray(a)[:3])) & (L.c[..., 3] > 0)
        if mask is not None:
            m &= mask
        out[m] = b
    L.c = out


# --------------------------------------------------------------------------- normals
def cyl_normal(L: Layer, x: int, y: int, w: int, h: int, mask=None, tilt_y: float = 0.0):
    """Explicit cylinder normals (vertical axis) for silos, barrels, poles, pipes."""
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
def rim_right(L: Layer, x, y, h, col, every=1, hgt=None):
    for k in range(h):
        if k % every == 0:
            L.px(x, y + k, col, hgt)


def stains(L: Layer, x, y, w, h, ladder, seed=0, strength=1.0, density=0.35, length=(4, 14), darker=True):
    """Vertical rain/rust streaks: shift colours of `ladder` 1 step darker in thin columns."""
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


def bricks(L: Layer, x, y, w, h, brick, mortar, alt=None, bw=4, bh=2, seed=0, alt_prob=0.12, hgt=0.5):
    """Running-bond bricks (near planes only): brick bw x bh incl. 1 px mortar."""
    rng = np.random.default_rng(seed)
    for yy in range(y, y + h):
        row = (yy - y) // bh
        in_mortar_row = (yy - y) % bh == bh - 1
        off = (bw // 2) * (row % 2)
        for xx in range(x, x + w):
            if in_mortar_row or ((xx - x + off) % bw == bw - 1):
                L.px(xx, yy, mortar, hgt - 0.08)
            else:
                L.px(xx, yy, brick, hgt)
    if alt is not None:
        rows = h // bh
        for r in range(rows):
            off = (bw // 2) * (r % 2)
            for bx in range(-off, w, bw):
                if rng.random() < alt_prob:
                    for yy in range(y + r * bh, y + r * bh + bh - 1):
                        for xx in range(x + max(0, bx), x + min(w, bx + bw - 1)):
                            L.px(xx, yy, alt, hgt + 0.03)


def window(L: Layer, x, y, w, h, frame, glass, refl=None, mullion=True, sill=None, recess=0.25, lit=None):
    L.rect(x - 1, y - 1, w + 2, h + 2, frame, hgt=0.55)
    if lit is not None:
        L.rect(x, y, w, h, lit, hgt=recess, em=lit)
    else:
        L.rect(x, y, w, h, glass, hgt=recess)
        if refl is not None:
            L.px(x, y, refl)
            if w > 3:
                L.px(x + 1, y, refl)
    if mullion and w >= 4 and h >= 5:
        mx = x + w // 2
        L.vline(mx, y, h, frame, 0.5)
        L.hline(x, y + max(1, h // 3), w, frame, 0.5)
    if sill is not None:
        L.hline(x - 1, y + h + 1, w + 2, sill, 0.7)


def snow_top(L: Layer, x, y, w, cols, depth=2, seed=0, ragged=True):
    """Snow along a horizontal top edge at row y (cols dark->light)."""
    rng = np.random.default_rng(abs(int(seed)))
    for xx in range(x, x + w):
        d = depth + (1 if (ragged and rng.random() < 0.25) else 0) - (1 if (ragged and rng.random() < 0.12) else 0)
        for k in range(max(1, d)):
            c = cols[-1] if k == 0 else cols[max(0, len(cols) - 1 - k)]
            L.px(xx, y + k, c, 0.75)
            L.nrm[min(L.h - 1, max(0, y + k)), min(L.w - 1, max(0, xx))] = (0.0, 0.8, 0.6)


# --------------------------------------------------------------------------- people
def figure(H: int, coat, skin=None, hat='shapka', facing='front', coat_len=0.72, rim=None, warm=None,
           arms='down', trousers=None, boots=None, scarf=None, hat_col=None, bundle=None, seed=0,
           outline=None, lean=0, width=1.0, apron=None) -> Layer:
    """Parametric human sprite (feet at bottom centre).  coat: ramp list dark->light (>=3).
    rim: colour for right-edge rim light (dawn sun); warm: (side, colour) warm light from 'l'/'r'.
    arms: 'down' | 'forward' (warming hands) | 'hold' (holding bundle) | 'hip'.
    Returns a Layer of size (W, H) with height field for normals."""
    rng = np.random.default_rng(seed)
    W = max(9, int(round(H * 0.42 * width)) + 4)
    S = Layer(W, H + 1, 'fig')
    cx = W // 2 + lean
    k = H / 46.0
    head_h = max(3, int(round(7 * k)))
    head_w = max(3, int(round(6 * k)))
    sh_y = head_h + max(1, int(round(1 * k)))
    sh_w = max(5, int(round(13 * k * width)))
    hip_w = max(4, int(round(12 * k * width)))
    hem_y = int(round(H * coat_len))
    hem_w = max(5, int(round(14 * k * width)))
    leg_w = max(1, int(round(3 * k)))
    gap = max(1, int(round(1.4 * k))) if H > 20 else 0
    trousers = trousers if trousers is not None else NI[2]
    boots = boots if boots is not None else NI[0]
    skin = skin if skin is not None else RU[4]
    hat_col = hat_col if hat_col is not None else coat[0]
    # ---- legs
    ly0 = hem_y - 1
    for side in (-1, 1):
        lx = cx + (side * (gap // 2 + (leg_w if side > 0 else 0))) - (0 if side > 0 else leg_w) - (gap % 2 if side < 0 else 0)
        if side > 0:
            lx = cx + (gap + 1) // 2
        else:
            lx = cx - gap // 2 - leg_w
        S.rect(lx, ly0, leg_w, H - ly0, trousers, hgt=0.5)
        bh = max(1, int(round(2.4 * k)))
        S.rect(lx - (1 if side < 0 and H > 24 else 0), H - bh, leg_w + (1 if H > 24 else 0), bh, boots, hgt=0.55)
    # ---- coat body (trapezoid shoulders -> hem)
    pts = [(cx - sh_w / 2, sh_y), (cx + sh_w / 2, sh_y), (cx + hem_w / 2, hem_y), (cx - hem_w / 2, hem_y)]
    m, x0, y0 = S.poly(pts, coat[1], hgt=0.6)
    # shading: left third darker, right edge rim
    hh, ww = m.shape
    yy, xx = np.mgrid[0:hh, 0:ww]
    rel = (xx + x0 - (cx - hem_w / 2)) / max(1, hem_w)
    dark = m & (rel < 0.34)
    S._put(dark, x0, y0, coat[0])
    light = m & (rel > 0.62) & (rel <= 0.86)
    if len(coat) > 2:
        S._put(light & dmask(ww, hh, x0, y0, 0.5), x0, y0, coat[2])
    # coat seams / belt
    if H >= 30:
        S.hline(cx - hip_w // 2, int(H * 0.47), hip_w, coat[0], 0.55)
        S.vline(cx, sh_y + 2, hem_y - sh_y - 2, coat[0], 0.55)
    if apron is not None and H >= 30:
        S.rect(cx - hip_w // 2 + 1, int(H * 0.36), hip_w - 2, hem_y - int(H * 0.36), apron, hgt=0.62)
    # ---- arms
    aw = max(1, int(round(3 * k)))
    if arms == 'down':
        for side in (-1, 1):
            ax = cx + side * (sh_w // 2) - (aw if side < 0 else 0) + (0 if side < 0 else 0)
            ax = int(cx - sh_w / 2) - (aw - 1) if side < 0 else int(cx + sh_w / 2) - 1
            S.rect(ax, sh_y + 1, aw, int(H * 0.38), coat[0] if side < 0 else coat[1], hgt=0.62)
            S.rect(ax, sh_y + 1 + int(H * 0.38), aw, max(1, int(2 * k)), NI[2] if H > 16 else coat[0], hgt=0.6)
            if H >= 30:   # sleeve seam separates arm from torso
                S.vline(ax + (aw if side < 0 else -1), sh_y + 3, int(H * 0.3), coat[0], 0.55)
    elif arms == 'forward':  # hands stretched toward a fire (front view: forearms toward centre-front)
        ay = sh_y + int(H * 0.22)
        S.rect(int(cx - sh_w / 2) - 1, sh_y + 1, aw, int(H * 0.2), coat[0], hgt=0.62)
        S.rect(int(cx + sh_w / 2) - 1, sh_y + 1, aw, int(H * 0.2), coat[1], hgt=0.62)
        S.rect(int(cx - sh_w / 2), ay, sh_w, aw, coat[1], hgt=0.7)
        S.rect(cx - 2, ay - 1, 4, max(2, int(2 * k)), skin, hgt=0.75)
    elif arms == 'hold':
        ay = sh_y + int(H * 0.2)
        S.rect(int(cx - sh_w / 2) - 1, sh_y + 1, aw, int(H * 0.18), coat[0], hgt=0.62)
        S.rect(int(cx + sh_w / 2) - 1, sh_y + 1, aw, int(H * 0.18), coat[1], hgt=0.62)
        S.rect(int(cx - sh_w / 2) + 1, ay, sh_w - 2, aw, coat[1], hgt=0.7)
    elif arms == 'hip':
        S.rect(int(cx - sh_w / 2) - 2, sh_y + 2, aw, int(H * 0.3), coat[0], hgt=0.62)
        S.rect(int(cx + sh_w / 2) - 1, sh_y + 1, aw, int(H * 0.38), coat[1], hgt=0.62)
    # ---- head (rounded); backlit faces: skin in shadow + 1 px lit edge on the sun side (right)
    hx0 = cx - head_w // 2
    skin_sh = RU[2] if skin is RU[4] or skin is RU[3] else skin
    if facing == 'back':
        S.rect(hx0, 1, head_w, head_h, hat_col, hgt=0.7)
    else:
        S.rect(hx0, 1, head_w, head_h, skin_sh, hgt=0.7)
        S.vline(hx0, 2, head_h - 2, RU[1], 0.7)                       # shadow side
        S.vline(hx0 + head_w - 1, 2, head_h - 3, RU[3], 0.72)         # lit cheek (sun side)
        if H >= 38:
            ey = 1 + int(head_h * 0.45)
            S.px(hx0 + 1, ey, NI[2])
            S.px(hx0 + head_w - 2, ey, NI[2])
            S.px(hx0 + head_w // 2, ey + 2, RU[1])                    # nose shadow
        for (px_, py_) in ((hx0, 1), (hx0 + head_w - 1, 1), (hx0, head_h), (hx0 + head_w - 1, head_h)):
            S.c[py_, px_] = 0
    # neck / scarf
    if scarf is not None:
        S.rect(cx - head_w // 2, head_h, head_w + (1 if H > 30 else 0), max(1, int(2 * k)), scarf, hgt=0.66)
    # headwear
    if hat == 'shapka':
        hh_ = max(2, int(round(3 * k)))
        S.rect(hx0 - 1, 0, head_w + 2, hh_, hat_col, hgt=0.8)
        if H >= 26:  # ear flaps
            S.rect(hx0 - 1, hh_, 1, max(1, int(3 * k)), hat_col, hgt=0.75)
            S.rect(hx0 + head_w, hh_, 1, max(1, int(3 * k)), hat_col, hgt=0.75)
    elif hat == 'scarf':  # headscarf (platok), knot under the chin
        S.rect(hx0 - 1, 0, head_w + 2, max(2, int(3 * k)), hat_col, hgt=0.8)
        S.rect(hx0 - 1, 0, 1, head_h + 1, hat_col, hgt=0.75)
        S.rect(hx0 + head_w, 0, 1, head_h + 1, hat_col, hgt=0.75)
        if H >= 26:
            S.px(cx, head_h + 1, hat_col)
    elif hat == 'cap':
        S.rect(hx0, 0, head_w + 1, max(1, int(2 * k)), hat_col, hgt=0.8)
        S.hline(hx0 + 1, max(1, int(2 * k)), head_w + 1, hat_col, 0.8)
    elif hat == 'bare':
        S.rect(hx0, 0, head_w, max(1, int(2 * k)), NI[1], hgt=0.8)
    # bundle carried / held
    if bundle is not None:
        bc = bundle
        bw_, bh_ = max(3, int(7 * k)), max(3, int(6 * k))
        bx = cx + sh_w // 2 - 1 if arms != 'hold' else cx - bw_ // 2
        by = int(H * 0.42) if arms != 'hold' else sh_y + int(H * 0.08)
        S.rect(bx, by, bw_, bh_, bc[1], hgt=0.7)
        S.rect(bx, by, bw_, 1, bc[2], hgt=0.75)
        S.rect(bx, by, 1, bh_, bc[0], hgt=0.65)
        S.px(bx + bw_ // 2, by - 1, bc[0])
    # rim light on the right silhouette edge (sun back-right) and optional warm side light
    a = S.alpha()
    p = np.pad(a, 1)
    right_edge = a & ~p[1:-1, 2:]
    left_edge = a & ~p[1:-1, :-2]
    if rim is not None:
        rows = np.arange(S.h)[:, None]
        sel = right_edge & (rows >= sh_y) & (rows < hem_y)
        S.c[sel] = rim
    if warm is not None:
        side, wc = warm
        e = left_edge if side == 'l' else right_edge
        S.c[e] = wc
        S.em[e] = (wc * np.array([1, 1, 1, 0]) + np.array([0, 0, 0, 170])).astype(np.uint8)
    if outline is not None:
        S.outline(outline, outer=False, only_where=left_edge)
    return S


def tiny_person(L: Layer, x: int, ybase: int, h: int, body, head=None, rim=None, pose='stand', seed=0):
    """Far-away person 5..16 px tall."""
    rng = np.random.default_rng(seed)
    head = head if head is not None else body
    hw = 1 if h < 9 else 2
    bw = 2 if h < 9 else 3
    L.rect(x, ybase - h, hw, max(1, h // 6), head)
    torso_h = int(h * 0.5)
    L.rect(x - (bw - hw) // 2 - (0 if h < 9 else 0), ybase - h + max(1, h // 6), bw, torso_h, body)
    ly = ybase - h + max(1, h // 6) + torso_h
    if pose == 'walk':
        L.px(x - 1, ybase - 1, body)
        L.px(x + bw - 1, ybase - 1, body)
        L.rect(x, ly, max(1, bw - 1), ybase - ly - 1, body)
    else:
        L.rect(x, ly, max(1, bw - 1), ybase - ly, body)
        if h >= 10:
            L.px(x + bw - 2, ybase - 1, body)
    if rim is not None:
        L.vline(x + bw - 1 - (bw - hw) // 2, ybase - h + max(1, h // 6), torso_h, rim)


# --------------------------------------------------------------------------- export helpers
def crop_v(L: Layer, pad: int = 0):
    """Vertical crop to content rows. Returns (Layer, y_offset)."""
    rows = np.nonzero(L.c[..., 3].any(1))[0]
    if len(rows) == 0:
        return L, 0
    y0 = max(0, rows[0] - pad)
    y1 = min(L.h, rows[-1] + 1 + pad)
    N = Layer(L.w, y1 - y0, L.name)
    N.c = L.c[y0:y1].copy()
    N.hgt = L.hgt[y0:y1].copy()
    N.nrm = L.nrm[y0:y1].copy()
    N.em = L.em[y0:y1].copy()
    return N, y0


def crop_box(L: Layer, pad: int = 1):
    a = L.c[..., 3] > 0
    rows = np.nonzero(a.any(1))[0]
    cols = np.nonzero(a.any(0))[0]
    y0, y1 = max(0, rows[0] - pad), min(L.h, rows[-1] + 1 + pad)
    x0, x1 = max(0, cols[0] - pad), min(L.w, cols[-1] + 1 + pad)
    N = Layer(x1 - x0, y1 - y0, L.name)
    N.c = L.c[y0:y1, x0:x1].copy()
    N.hgt = L.hgt[y0:y1, x0:x1].copy()
    N.nrm = L.nrm[y0:y1, x0:x1].copy()
    N.em = L.em[y0:y1, x0:x1].copy()
    return N, x0, y0


def palette_report(img_arr: np.ndarray, extra=()):
    """Return colours used that are NOT in the scene palette (+ accents)."""
    pal = set(int(k) for k in col_key(np.stack(ALL + list(extra))[:, :3]))
    a = img_arr[..., 3] > 0
    keys = np.unique(col_key(img_arr[..., :3])[a])
    return [('#%06X' % int(k)) for k in keys if int(k) not in pal]


def save_png(arr: np.ndarray, path: str):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    Image.fromarray(arr, 'RGBA').save(path)
