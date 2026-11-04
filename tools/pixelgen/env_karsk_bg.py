"""env_karsk_bg -- sky and parallax background layers for scene A1 'Verladebahnhof Karsk'.

Each make_* returns (Layer, pos_y).  Layer x = 0 is the layer's left edge (pos.x = 0).
Screen x of a layer pixel = x - cam_x * parallax.  Skyline plan (what is visible at cam 0/640/1280)
is documented next to every element.  Value plan (dark -> light = near -> far): near_bg teal,
mid sage, far industry / far city sky ramp.  Key light: low dawn sun behind haze, back-right ->
1 px rim on right edges, lit cloud undersides, cold ambient.
"""
from __future__ import annotations

import os as _os
import sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))

import math

import numpy as np

import pg
from env_karsk_lib import (Layer, NI, TE, SA, SK, ST, RU, CO, SN, WO, RED, bayer, value_noise, dmask,
                           ladder_shift, text, cyl_normal, flat_normal, tiny_person, figure, snow_top)

W_WORLD = 1920
VIEW_W = 640
SUN = (612, 190)          # screen position of the hazy sun (sky layer, parallax 0)
SKY_LADDER = [NI[3], TE[2], TE[3], TE[4], SK[0], SK[1], SK[2], SK[3], SK[4], SK[5], CO[4], SN[4]]
SKY_STOPS = [(0, 1.7), (34, 2.0), (70, 3.0), (104, 4.0), (134, 5.0), (160, 6.0), (182, 7.0), (198, 8.0),
             (214, 9.0), (360, 9.0)]


def layer_w(p: float, margin: int = 8) -> int:
    return int(math.ceil(VIEW_W + p * (W_WORLD - VIEW_W))) + margin


def sky_index(y):
    return np.interp(y, [s[0] for s in SKY_STOPS], [s[1] for s in SKY_STOPS])


def ladder_paint(L, mask, x0, y0, T, ladder, steep=2.6):
    """Fill mask (placed at x0,y0) with ladder colours chosen by float index T (same shape).
    steep > 1 keeps most pixels on pure ramp colours and confines the ordered dither to narrow
    transition bands (hand-dithered look instead of a noisy 50 % checker everywhere)."""
    h, w = mask.shape
    T = np.clip(T, 0, len(ladder) - 1)
    idx = np.floor(T).astype(int)
    fr = np.clip((T - idx - 0.5) * steep + 0.5, 0, 1)
    idx = np.clip(idx + (fr > bayer(w, h, x0, y0)), 0, len(ladder) - 1)
    L._put(mask, x0, y0, np.stack(ladder)[idx])


# =========================================================================== SKY (parallax 0)
def make_sky():
    W, H = layer_w(0.0), 360
    L = Layer(W, H, 'sky')
    ys = np.arange(H, dtype=np.float32)
    T = np.repeat(sky_index(ys)[:, None], W, axis=1).astype(np.float32)
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    # very faint stratified banding in the upper sky (keeps big flat areas alive)
    nz = value_noise(W, H // 5 + 2, 40, seed=5, octaves=2)
    band = np.repeat(nz, 5, axis=0)[:H]
    T += (band - 0.5) * 0.3 * np.clip((yy - 20) / 90, 0, 1) * (yy < 175)
    # dawn glow around the low sun (behind haze, right); capped so the disc itself stays distinct
    d = np.sqrt(((xx - SUN[0]) / 230.0) ** 2 + ((yy - SUN[1]) / 96.0) ** 2)
    T += np.clip(1 - d, 0, 1) ** 1.7 * 2.0
    d2 = np.sqrt(((xx - SUN[0]) / 64.0) ** 2 + ((yy - SUN[1]) / 26.0) ** 2)
    T += np.clip(1 - d2, 0, 1) ** 1.3 * 0.9
    hb = np.clip(1 - np.abs(yy - 204) / 18.0, 0, 1) * np.clip(1 - np.abs(xx - SUN[0]) / 360.0, 0, 1)
    T += hb * 0.7
    T = np.minimum(T, 9.85)
    dd = np.sqrt((xx - SUN[0]) ** 2 + ((yy - SUN[1]) * 1.08) ** 2)
    T[dd < 9.4] = np.maximum(T[dd < 9.4], 10.0)
    T[dd < 7.2] = 11.0
    # thin haze bars crossing the sun disc
    for (ly, x0, x1, amt) in [(186, 520, 648, -1.4), (189, 548, 640, -0.9), (194, 470, 648, -1.2),
                              (180, 430, 560, -0.6), (172, 560, 648, -0.5), (199, 520, 620, -0.7)]:
        wob = value_noise(W, 1, 16, seed=ly, octaves=2)[0]
        seg = (yy == ly) & (xx >= x0) & (xx < x1) & (wob[None, :] > 0.4)
        T[seg] += amt
    full = np.ones((H, W), bool)
    ladder_paint(L, full, 0, 0, T, SKY_LADDER)
    L.hgt[:] = 0
    return L, 0


# =========================================================================== CLOUDS (parallax 0.03)
def band_cloud(L, circles, sun_boost=0.0, flat_bottom=None, light=(1, 1), seed=0, wisp=0.0):
    """Clean pixel-art cloud: silhouette from circles, tone bands by offsetting the silhouette
    toward the light (lit crescent at bottom-right = low sun behind-right), colours taken from
    the sky ladder relative to the local sky so clouds sit in the gradient."""
    xs0 = int(min(c[0] - c[2] for c in circles)) - 2
    ys0 = int(min(c[1] - c[2] for c in circles)) - 2
    xs1 = int(max(c[0] + c[2] for c in circles)) + 3
    ys1 = int(max(c[1] + c[2] for c in circles)) + 3
    w, h = xs1 - xs0, ys1 - ys0
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    X, Y = xx + xs0, yy + ys0
    M = np.zeros((h, w), bool)
    for cx, cy, r in circles:
        M |= ((X + 0.5 - cx) ** 2 + (Y + 0.5 - cy) ** 2) <= r * r
    if flat_bottom is not None:
        M &= Y <= flat_bottom
    if wisp > 0:
        nz = value_noise(w, h, 4, seed, octaves=2)
        edge = M & ~(np.roll(M, 3, 0) & np.roll(M, -3, 0) & np.roll(M, 3, 1) & np.roll(M, -3, 1))
        M &= ~(edge & (nz < wisp))

    def inside(dx, dy):
        S = np.zeros_like(M)
        sy0, sy1 = max(0, -dy), min(h, h - dy)
        sx0, sx1 = max(0, -dx), min(w, w - dx)
        S[sy0:sy1, sx0:sx1] = M[sy0 + dy:sy1 + dy, sx0 + dx:sx1 + dx]
        return S & M

    lx, ly = light
    b1 = inside(lx * 2, ly * 2)
    b1b = inside(lx * 3, ly * 4)
    b2 = inside(lx * 5, ly * 7)
    b3 = inside(lx * 9, ly * 12)
    tone = np.full((h, w), 2.0, np.float32)      # lit crescent (bottom-right, facing the low sun)
    tone[b1b & ~b1] = 1.25
    tone[b1] = 0.85
    tone[b2] = 0.3
    tone[b3] = -0.25                               # shaded core
    cy_m = float(np.mean([c[1] for c in circles]))
    base = sky_index(cy_m) * 0.75 + sky_index(Y) * 0.25 - 0.25
    d = np.sqrt(((X - SUN[0]) / 280.0) ** 2 + ((Y - SUN[1]) / 130.0) ** 2)
    boost = np.clip(1 - d, 0, 1) ** 1.1 * (1.6 + sun_boost)
    T = base + tone + boost * np.clip(tone, 0, 2.1) * 0.75
    ladder_paint(L, M, xs0, ys0, T, SKY_LADDER)
    hg = np.zeros((h, w), np.float32)
    hg[M] = 0.3
    hg[b2] = 0.6
    L._put(M, xs0, ys0, None, hgt=hg)
    return M


def cloud_circles(rng, x, yb, w, h, lobes=None, rmin=0.35, rmax=0.9):
    """Bank silhouette: lobes along a flat base, taller in the middle."""
    n = lobes or max(4, int(w / (h * 0.7)))
    out = []
    for i in range(n):
        t = (i + rng.uniform(0.1, 0.9)) / n
        env = math.sin(math.pi * t) ** 0.6
        r = h * (rmin + (rmax - rmin) * env) * rng.uniform(0.75, 1.05)
        out.append((x + t * w, yb - r * rng.uniform(0.45, 0.75), r))
        if rng.random() < 0.45:
            out.append((x + t * w + rng.uniform(-r, r) * 0.6, yb - r * 1.1, r * rng.uniform(0.4, 0.6)))
    return out


def make_clouds():
    W, H = layer_w(0.03, 30), 206
    L = Layer(W, H, 'clouds')
    rng = np.random.default_rng(12)
    # high thin altocumulus streets (small, flat, sparse)
    for i, (x, yb, w) in enumerate([(10, 34, 70), (230, 40, 90), (520, 44, 80), (330, 56, 40)]):
        circ = cloud_circles(rng, x, yb, w, 7, rmin=0.6, rmax=1.0)
        band_cloud(L, circ, flat_bottom=yb, seed=100 + i, wisp=0.35)
    # big stratocumulus banks (mid sky) -- left mass, centre bank, right bank near the sun
    specs = [(-40, 116, 250, 36), (170, 92, 130, 24), (262, 134, 210, 34), (450, 104, 140, 26),
             (540, 146, 180, 24), (60, 156, 140, 16), (660, 122, 90, 22), (330, 70, 120, 16)]
    for i, (x, yb, w, h) in enumerate(specs):
        circ = cloud_circles(rng, x, yb, w, h)
        band_cloud(L, circ, flat_bottom=yb + 1, seed=200 + i, wisp=0.18)
    # low stratus streaks catching the sun near the horizon
    for i, (x0, y, ln) in enumerate([(380, 166, 150), (520, 176, 170), (200, 178, 110), (600, 160, 90)]):
        circ = [(x0 + k, y + math.sin(k / 17.0) * 1.5, 2.2 + 1.4 * math.sin(math.pi * k / ln))
                for k in range(0, ln, 3)]
        band_cloud(L, circ, seed=300 + i, sun_boost=0.6)
    L.hgt *= 0.6
    return L, 0


# =========================================================================== shared painters
def tone_box(L, x, y, w, h, C, hgt=0.5, rim=True, left=True, top=None):
    L.rect(x, y, w, h, C['body'], hgt=hgt)
    if left:
        L.rect(x, y, 1, h, C['sh'], hgt=hgt - 0.05)
    if rim:
        L.rect(x + w - 1, y, 1, h, C['rim'], hgt=hgt + 0.05)
    if top is not None:
        L.hline(x, y, w, top, hgt + 0.1)


def chimney(L, cx, base, h, wb, wt, C, bands=2, lip=True):
    for k in range(h):
        t = k / max(1, h - 1)
        w = wt + (wb - wt) * t
        x0 = int(round(cx - w / 2))
        x1 = int(round(cx + w / 2))
        y = base - h + k
        for x in range(x0, x1):
            u = (x - x0) / max(1, x1 - x0 - 1)
            c = C['sh'] if u < 0.3 else (C['rim'] if x == x1 - 1 else C['body'])
            L.px(x, y, c, 0.55)
    for b in range(bands):
        by = base - h + 3 + b * 5
        w = wt + (wb - wt) * (3 + b * 5) / h
        L.hline(int(round(cx - w / 2)), by, int(round(w)), C['band'], 0.6)
    if lip:
        L.hline(int(round(cx - wt / 2)) - 1, base - h, int(round(wt)) + 2, C['sh'], 0.65)
    cyl_normal(L, int(round(cx - wb / 2)) - 1, base - h - 1, int(round(wb)) + 2, h + 1)


def hyperboloid(L, cx, base, h, wb, ww, wt, C, tw=0.68):
    for k in range(h):
        t = k / max(1, h - 1)
        if t < tw:
            hw = ww / 2 + (wt / 2 - ww / 2) * ((tw - t) / tw) ** 2
        else:
            hw = ww / 2 + (wb / 2 - ww / 2) * ((t - tw) / (1 - tw)) ** 1.7
        x0 = int(round(cx - hw))
        x1 = int(round(cx + hw))
        y = base - h + k
        for x in range(x0, x1 + 1):
            u = (x - cx) / max(1.0, hw)
            if x == x1:
                c = C['rim']
            elif u > 0.5:
                c = C['lit'] if ((x + y) % 2 == 0 or u > 0.72) else C['body']
            elif u < -0.4:
                c = C['sh']
            else:
                c = C['body']
            L.px(x, y, c, 0.5)
    L.hline(int(round(cx - wt / 2)), base - h, int(round(wt)) + 1, C['sh'], 0.6)
    cyl_normal(L, int(cx - wb / 2) - 1, base - h, int(wb) + 3, h)


def cylinder(L, x, y, w, h, C, rings=0):
    for xx in range(x, x + w):
        u = (xx - x + 0.5) / w
        if xx == x + w - 1:
            c = C['rim']
        elif u > 0.8:
            c = C['lit']
        elif u > 0.64:
            c = C['lit'] if (xx + y) % 2 == 0 else C['body']
        elif u < 0.12:
            c = C['deep']
        elif u < 0.3:
            c = C['sh']
        else:
            c = C['body']
        L.rect(xx, y, 1, h, c, hgt=0.5)
    if rings:
        for ry in range(y + rings, y + h, rings):
            for xx in range(x + 2, x + w - 2):
                if 0 <= ry < L.h and 0 <= xx < L.w and (L.c[ry, xx, :3] == C['body'][:3]).all() and (xx + ry) % 3:
                    L.px(xx, ry, C['sh'])
    cyl_normal(L, x, y, w, h)


def sawtooth(L, x, base_roof, w, tooth, th, C):
    for xx in range(x, x + w):
        k = (xx - x) % tooth
        hh = int(round(th * (k + 1) / tooth))
        for yy in range(base_roof - hh, base_roof):
            L.px(xx, yy, C['body'], 0.55)
        L.px(xx, base_roof - hh, C['top'], 0.7)
        if k == tooth - 1:
            L.rect(xx, base_roof - th, 1, th, C['glass'], hgt=0.4)
            L.px(xx, base_roof - th, C['rim'], 0.7)


def fog_base(L, ladder, y0, y1, steps, power=1.4):
    rows = np.arange(L.h, dtype=np.float32)
    t = np.clip((rows - y0) / max(1, y1 - y0), 0, 1) ** power * steps
    ladder_shift(L, ladder, np.repeat(t[:, None], L.w, axis=1))


def base_fill(L, B, cols, seed=0, amp=(6, 3), period=(11.0, 4.3)):
    """Continuous low roofline / ground haze strip at the layer base so no gaps show."""
    for xx in range(0, L.w):
        hh = amp[0] + int(amp[1] * math.sin(xx / period[0] + seed) + 2 * math.sin(xx / period[1] + seed * 3))
        for yy in range(B - max(1, hh), B):
            if L.c[yy, xx, 3] == 0:
                L.px(xx, yy, cols[0] if (xx // 13 + seed) % 3 else cols[1], 0.4)
        L.rect(xx, B, 1, L.h - B, cols[2], hgt=0.2)


def bare_tree(L, x, base, h, col, seed=0, twig=None, droop=0.0, trunk_w=2, rim=None):
    rng = np.random.default_rng(seed)
    twig = col if twig is None else twig

    def branch(x0, y0, ang, ln, depth, w):
        x1 = x0 + math.cos(ang) * ln
        y1 = y0 - math.sin(ang) * ln
        c = col if depth > 1 else twig
        L.line(x0, y0, x1, y1, c, 0.4)
        if w > 1:
            L.line(x0 + 1, y0, x1 + 1, y1, c, 0.4)
        if depth > 0:
            nb = 2 if depth > 2 else 3
            for _ in range(nb):
                na = ang + rng.uniform(-0.75, 0.75) - droop * (1 if math.cos(ang) > 0 else -1) * 0.3
                branch(x1, y1, na, ln * rng.uniform(0.55, 0.78), depth - 1, max(1, w - 1))
        elif droop > 0:
            for _ in range(2):
                L.line(x1, y1, x1 + rng.uniform(-2, 2), y1 + rng.uniform(3, 7), twig)

    th = int(h * 0.45)
    for k in range(trunk_w):
        L.vline(x + k, base - th, th, col, 0.5)
    if rim is not None:
        L.vline(x + trunk_w - 1, base - th, th, rim)
    for a in (1.15, 1.55, 1.95):
        branch(x + trunk_w // 2, base - th + 2, a + rng.uniform(-0.15, 0.15), h * 0.3, 3, trunk_w)


# =========================================================================== FAR CITY (0.12)
def make_far_city():
    """Silhouette band at horizon (base y 206). Cooling towers at x 560-650 stand in front of the
    sun at cam 0 and drift left with the pan. Slab districts left and right, a broken block."""
    p = 0.12
    W, H, TOP = layer_w(p), 134, 96
    L = Layer(W, H, 'far_city')
    B = 207 - TOP
    C = dict(deep=SK[0], sh=SK[1], body=SK[2], lit=SK[3], rim=SK[4], top=SK[4], win=SK[1], band=SK[3],
             glass=SK[1])
    rng = np.random.default_rng(21)

    def block(x, w, h, seed, crane=False, ruin=False, lit=0, Cb=C):
        y = B - h
        tone_box(L, x, y, w, h, Cb, top=Cb['top'])
        r = np.random.default_rng(seed)
        for wy in range(y + 3, B - 2, 4):
            for wx in range(x + 2, x + w - 2, 3):
                if r.random() < 0.85:
                    L.px(wx, wy, Cb['win'], 0.3)
        for _ in range(lit):
            wy = y + 3 + 4 * int(r.integers(0, max(1, (h - 6) // 4)))
            wx = x + 2 + 3 * int(r.integers(0, max(1, (w - 4) // 3)))
            L.px(wx, wy, CO[2], 0.3, em=CO[2])
        if ruin:
            for xx in range(x, x + w):
                cut = int(r.integers(0, 6)) if (xx - x) % 5 else int(r.integers(4, 9))
                L.rect(xx, y, 1, cut, np.zeros(4, np.uint8))
        if crane:
            mx = x + w - 5
            for yy in range(y - 26, y):
                L.px(mx, yy, Cb['sh'])
                if yy % 3 == 0:
                    L.px(mx + 1, yy, Cb['sh'])
            L.hline(mx - 16, y - 26, 26, Cb['sh'])
            L.rect(mx - 16, y - 25, 3, 2, Cb['sh'])
            L.vline(mx + 6, y - 25, 8, Cb['sh'])

    x = -4
    for (w, h, s, cr, ru, lit) in [(44, 22, 0, False, False, 1), (28, 40, 1, False, False, 1),
                                   (54, 18, 2, False, False, 0), (34, 34, 3, True, False, 1),
                                   (40, 20, 4, False, True, 0), (24, 46, 5, False, False, 1),
                                   (60, 22, 6, False, False, 1), (32, 30, 7, False, False, 0),
                                   (46, 16, 8, False, False, 0)]:
        block(x, w, h, 300 + s, crane=cr, ruin=ru, lit=lit)
        x += w + int(rng.integers(4, 14))
    # radio mast (thin lattice) with a dim red obstruction light
    mx = 300
    for yy in range(B - 88, B):
        L.px(mx, yy, C['sh'])
        if yy % 4 == 0:
            L.px(mx - 1, yy, C['sh'])
            L.px(mx + 1, yy, C['sh'])
    L.px(mx, B - 89, RED[2], em=RED[2])
    # old quarter: pitched roofs + a church drum without dome (damaged)
    for (xx, w, h) in [(330, 22, 10), (350, 16, 14), (368, 26, 9), (396, 18, 12), (418, 24, 10)]:
        tone_box(L, xx, B - h, w, h, C, top=C['top'])
        for k in range(w // 2):
            L.hline(xx + k, B - h - k // 2 - 1, w - 2 * k, C['body'])
        L.vline(xx + w - 1, B - h, h, C['rim'])
    tone_box(L, 446, B - 26, 12, 26, C, top=C['top'])
    L.rect(448, B - 33, 8, 7, C['body'])
    L.vline(455, B - 33, 7, C['rim'])
    L.px(450, B - 34, C['body'])
    # power station: cooling towers in front of the sun glow + chimneys
    CT = dict(C, sh=SK[0], body=SK[1], lit=SK[2], rim=SK[4])
    hyperboloid(L, 546, B, 58, 44, 27, 31, CT)
    hyperboloid(L, 662, B, 50, 38, 23, 27, CT)
    CC = dict(C, sh=SK[0], body=SK[1], rim=SK[3], band=SK[3])
    chimney(L, 688, B, 84, 5, 4, CC, bands=2)
    chimney(L, 700, B, 70, 5, 3, CC, bands=1)
    tone_box(L, 676, B - 20, 40, 20, dict(C, body=SK[1], sh=SK[0], rim=SK[3]), top=SK[3])
    x = 722
    for (w, h, s, cr, ru, lit) in [(36, 26, 8, False, False, 1), (26, 40, 9, True, False, 0),
                                   (40, 18, 10, False, False, 1)]:
        block(x, w, h, 400 + s, crane=cr, ruin=ru, lit=lit)
        x += w + int(rng.integers(3, 8))
    base_fill(L, B, (C['body'], C['sh'], C['lit']), seed=1, amp=(5, 2))
    fog_base(L, [SK[0], SK[1], SK[2], SK[3], SK[4]], B - 26, B + 1, 1.6)
    return L, TOP


# =========================================================================== FAR INDUSTRY (0.25)
def make_far_industry():
    """Base y 216.  Stack clusters at x 100-140 (cam0), 560-600 (cam640), 800-880 (cam1280)."""
    p = 0.25
    W, H, TOP = layer_w(p), 160, 70
    L = Layer(W, H, 'far_industry')
    B = 217 - TOP
    C = dict(deep=TE[4], sh=SK[0], body=SK[1], lit=SK[2], rim=SK[3], top=SK[3], glass=SK[2], win=SK[0],
             band=SK[2])

    def hall(x, w, h, tooth=12, th=8):
        y = B - h
        tone_box(L, x, y, w, h, C)
        sawtooth(L, x, y, w, tooth, th, C)
        for wx in range(x + 3, x + w - 3, 4):
            L.rect(wx, y + 4, 2, 5, C['win'], hgt=0.3)
        L.vline(x + w - 1, y, h, C['rim'])

    def boxb(x, w, h, top=True):
        tone_box(L, x, B - h, w, h, C, top=C['top'] if top else None)

    hall(-6, 160, 26)
    chimney(L, 112, B, 118, 8, 6, C, bands=2)
    chimney(L, 130, B, 98, 7, 5, C, bands=2)
    chimney(L, 96, B, 84, 6, 4, C, bands=1)
    gx, gw, gh = 176, 46, 40
    cylinder(L, gx, B - gh, gw, gh, dict(C, deep=SK[0], sh=SK[0], body=SK[1], lit=SK[2], rim=SK[3]))
    for k in range(gx, gx + gw + 1, 7):
        L.vline(k, B - gh - 4, gh + 4, C['sh'])
    for yy in range(B - gh - 4, B, 11):
        L.hline(gx, yy, gw + 1, C['sh'])
    L.hline(gx + 1, B - gh, gw - 2, C['rim'])
    boxb(236, 30, 48)
    boxb(244, 12, 64)
    pg.truss(L, 266, B - 44, 300, B - 22, 3, C['sh'], step=5)
    hall(280, 124, 24, tooth=14, th=8)
    L.hline(270, B - 32, 30, C['sh'])
    L.hline(270, B - 30, 30, C['sh'])
    # power plant (left of the sun at cam 0, centre-left at cam 640): boiler house + 2 stacks
    boxb(410, 64, 56)
    for wy in range(B - 50, B - 8, 9):
        for wx in range(416, 470, 6):
            L.rect(wx, wy, 3, 5, C['win'])
    chimney(L, 432, B - 56, 66, 8, 6, C, bands=2)
    chimney(L, 458, B - 56, 78, 8, 6, C, bands=2)
    boxb(476, 40, 32)
    # low hall under the sun (x 520-720 stays below y 199 so the sun disc shows at cam 0)
    hall(518, 180, 17, tooth=10, th=6)
    boxb(700, 24, 22)
    # water tank on lattice
    L.rect(770, B - 62, 22, 13, C['body'], hgt=0.5)
    L.vline(791, B - 62, 13, C['rim'])
    L.hline(770, B - 62, 22, C['top'])
    for lx in (772, 788):
        L.vline(lx, B - 49, 49, C['sh'])
    for yy in range(B - 49, B, 8):
        L.line(772, yy, 788, yy + 8, C['sh'])
        L.line(788, yy, 772, yy + 8, C['sh'])
    hall(800, 112, 26, tooth=12, th=8)
    chimney(L, 846, B - 26, 92, 8, 6, C, bands=2)
    chimney(L, 868, B - 26, 70, 7, 5, C, bands=1)
    boxb(914, W - 914, 18)
    base_fill(L, B, (C['body'], C['sh'], C['lit']), seed=2, amp=(6, 3))
    fog_base(L, [TE[4], SK[0], SK[1], SK[2], SK[3]], B - 30, B + 1, 1.7)
    return L, TOP


# =========================================================================== MID (0.45)
def make_mid():
    """Base y 230.  Elevator x 84-300 (cam0 left), water tower x 352 (cam0), tower crane x 650 +
    new block x 664-756 (right of the sun at cam0, centre of cam640), low sheds x 760-920 and a thin
    chimney x 884 (sun gap at cam640), damaged factory facade x 930-1166 (cam1280 centre),
    low shed x 1170-1230 (sun gap at cam1280)."""
    p = 0.45
    W, H, TOP = layer_w(p), 200, 34
    L = Layer(W, H, 'mid')
    B = 231 - TOP
    C = dict(deep=TE[2], sh=TE[3], body=SA[1], lit=SA[2], rim=SA[3], top=SA[4], snow=SA[5], glass=TE[2],
             win=TE[2], band=SA[2])

    def boxb(x, y, w, h, top=True, hgt=0.5):
        tone_box(L, x, y, w, h, C, hgt=hgt)
        if top:
            L.hline(x, y, w, C['snow'], hgt + 0.2)
            L.hline(x, y + 1, w, C['top'], hgt + 0.1)

    # ---- grain elevator
    sx0 = 128
    for i in range(5):
        x = sx0 + i * 24
        cylinder(L, x, B - 112, 25, 112, C, rings=8)
        L.hline(x + 1, B - 113, 23, C['snow'])
        L.hline(x + 3, B - 114, 19, C['top'])
    L.ellipse(sx0 + 24 + 12, B - 80, 4, 6, TE[2], hgt=0.2)          # shell hole
    L.ellipse(sx0 + 24 + 12, B - 81, 2, 4, NI[3], hgt=0.1)
    L.rect(sx0 + 72 + 6, B - 58, 11, 9, C['lit'], hgt=0.55)          # repaired patch
    L.hline(sx0 + 72 + 6, B - 58, 11, C['top'])
    hx = sx0 + 42
    boxb(hx, B - 168, 38, 56)
    boxb(hx + 6, B - 182, 24, 14)
    for wy in range(B - 162, B - 120, 9):
        for wx in (hx + 6, hx + 16, hx + 26):
            L.rect(wx, wy, 5, 5, C['win'], hgt=0.3)
            L.px(wx + 4, wy, C['lit'])
    L.rect(hx + 9, B - 178, 14, 6, C['win'], hgt=0.3)
    pg.truss(L, hx + 38, B - 146, hx + 132, B - 98, 4, C['sh'], step=6)
    L.line(hx + 38, B - 147, hx + 132, B - 99, C['rim'])
    boxb(hx + 124, B - 102, 30, 102)
    for wy in range(B - 94, B - 10, 12):
        L.rect(hx + 130, wy, 4, 6, C['win'])
        L.rect(hx + 141, wy, 4, 6, C['win'])
    boxb(sx0 - 44, B - 40, 44, 40)
    for wx in range(sx0 - 40, sx0 - 4, 8):
        L.rect(wx, B - 32, 4, 7, C['win'])
    # ---- left edge: warehouse + chimney
    boxb(-4, B - 50, 78, 50)
    for wx in range(4, 68, 10):
        L.rect(wx, B - 42, 5, 8, C['win'])
        L.rect(wx, B - 24, 5, 8, C['win'])
    chimney(L, 58, B - 50, 64, 8, 6, C, bands=2)
    # ---- railway water tower
    wx0 = 352
    boxb(wx0 + 6, B - 70, 24, 70)
    for wy in range(B - 60, B - 10, 14):
        L.rect(wx0 + 15, wy, 5, 7, C['win'])
    L.rect(wx0, B - 96, 36, 26, C['body'], hgt=0.55)
    for k in range(wx0 + 2, wx0 + 34, 3):
        L.vline(k, B - 96, 26, C['sh'])
    L.vline(wx0, B - 96, 26, C['deep'])
    L.vline(wx0 + 35, B - 96, 26, C['rim'])
    L.vline(wx0 + 34, B - 96, 26, C['lit'])
    L.hline(wx0 - 1, B - 70, 38, C['deep'])
    for k in range(10):
        L.hline(wx0 + k * 2 - 1, B - 97 - k, 38 - k * 4 + 2, C['lit'] if k < 2 else C['body'])
        L.px(wx0 + 36 - k * 2, B - 97 - k, C['rim'])
    L.hline(wx0, B - 97, 36, C['snow'])
    cyl_normal(L, wx0, B - 96, 36, 26)
    # ---- construction site: new block in progress + tower crane
    bx = 664
    boxb(bx, B - 66, 92, 66)
    for fl in range(5):
        y = B - 62 + fl * 12
        for k in range(8):
            L.rect(bx + 5 + k * 11, y, 6, 7, C['win'])
            L.px(bx + 10 + k * 11, y, C['lit'])
    for k in range(6):
        L.rect(bx + 4 + k * 16, B - 88, 3, 22, C['sh'])
        L.px(bx + 6 + k * 16, B - 88, C['rim'])
    L.hline(bx, B - 77, 92, C['sh'])
    L.hline(bx + 40, B - 89, 52, C['sh'])
    cx = bx - 14
    pg.truss(L, cx, B, cx, B - 160, 5, C['deep'], step=6)
    L.vline(cx + 5, B - 160, 160, C['rim'])
    pg.truss(L, cx - 34, B - 160, cx + 94, B - 160, 4, C['deep'], step=6)
    L.hline(cx - 34, B - 161, 128, C['rim'])
    L.rect(cx - 34, B - 156, 10, 9, NI[3])
    L.rect(cx + 2, B - 168, 8, 8, C['body'])
    L.vline(cx + 9, B - 168, 8, C['rim'])
    L.vline(cx + 6, B - 176, 8, C['deep'])
    L.line(cx + 6, B - 176, cx + 90, B - 161, C['deep'])
    L.line(cx + 6, B - 176, cx - 30, B - 161, C['deep'])
    L.vline(cx + 62, B - 156, 64, C['deep'])
    L.rect(cx + 56, B - 92, 22, 3, C['lit'])                     # panel on the hook
    L.hline(cx + 56, B - 92, 22, C['top'])
    L.line(cx + 62, B - 95, cx + 66, B - 92, C['deep'])
    L.px(cx + 94, B - 162, RED[3], em=RED[3])
    for (px_, py_) in [(bx + 22, B - 77), (bx + 70, B - 89), (bx + 49, B - 77)]:
        tiny_person(L, px_, py_, 9, NI[3], rim=C['rim'], seed=px_)
    # ---- damaged factory facade with window grid (+ scaffolding, banner cloth)
    fx, fw, fh = 930, 236, 104
    boxb(fx, B - fh, fw, fh, top=False)
    for yy in range(B - fh + 2, B, 3):
        for xx in range(fx + 1, fx + fw - 1):
            if (xx + yy) % 4 == 0:
                L.px(xx, yy, C['sh'])
    for k in range(fx, fx + fw, 39):
        L.rect(k, B - fh, 4, fh, C['lit'], hgt=0.6)
        L.vline(k + 3, B - fh, fh, C['rim'])
    r = np.random.default_rng(43)
    for col in range(6):
        for row in range(2):
            x = fx + 8 + col * 39
            y = B - fh + 12 + row * 44
            L.rect(x, y, 27, 32, C['deep'], hgt=0.25)
            for yy in range(y, y + 32, 4):
                L.hline(x, yy, 27, C['sh'])
            for xx in range(x, x + 27, 5):
                L.vline(xx, y, 32, C['sh'])
            for _ in range(5):
                L.rect(x + 1 + 5 * int(r.integers(0, 5)), y + 1 + 4 * int(r.integers(0, 7)), 4, 3, C['lit'])
            roll = r.random()
            if roll < 0.28:
                for _ in range(4):
                    L.rect(x + 1 + 5 * int(r.integers(0, 5)), y + 1 + 4 * int(r.integers(0, 7)), 4, 3, NI[2])
            elif roll < 0.45:
                L.rect(x, y + 9, 27, 13, WO[2], hgt=0.55)
                for yy in range(y + 9, y + 22, 3):
                    L.hline(x, yy, 27, WO[1])
            L.hline(x - 1, y + 33, 29, C['top'])
    for xx in range(fx + 120, fx + fw):   # collapsed roof on the right section
        if xx < fx + 200:
            cut = int(12 + 9 * math.sin(xx / 7.0) + 5 * math.sin(xx / 2.3))
        else:
            cut = int(3 + 2 * math.sin(xx))
        cut = max(0, cut)
        L.rect(xx, B - fh, 1, cut, np.zeros(4, np.uint8))
        L.px(xx, B - fh + cut, C['snow'])
    L.rect(fx - 2, B - fh - 4, 124, 4, C['lit'], hgt=0.7)
    L.hline(fx - 2, B - fh - 5, 124, C['snow'])
    L.rect(fx + 20, B - fh - 18, 60, 14, C['body'])
    L.hline(fx + 20, B - fh - 18, 60, C['snow'])
    L.vline(fx + 79, B - fh - 18, 14, C['rim'])
    sx = fx + 128
    for k in range(6):
        L.vline(sx + k * 18, B - fh - 12, fh + 12, WO[3])
    for yy in range(B - fh - 6, B, 16):
        L.hline(sx - 2, yy, 96, WO[4])
        L.hline(sx - 2, yy + 1, 96, WO[2])
        for k in range(5):
            L.line(sx + k * 18, yy, sx + k * 18 + 18, min(B - 1, yy + 16), WO[2])
    for (px_, py_) in [(sx + 30, B - fh + 26), (sx + 64, B - fh + 42), (sx + 12, B - fh + 74)]:
        tiny_person(L, px_, py_, 10, NI[3], rim=C['rim'], seed=px_)
    L.rect(sx + 6, B - fh + 2, 60, 9, RU[2], hgt=0.6)
    L.hline(sx + 6, B - fh + 2, 60, RU[3])
    L.vline(sx + 65, B - fh + 2, 9, RU[4])
    for k in range(sx + 9, sx + 63, 4):
        L.px(k, B - fh + 6, SA[4])
    # ---- fillers: low sheds between the crane site and the facade (sun gap at cam 640),
    #      thin chimney in front of the sun at cam 640, low sheds right (sun gap at cam 1280)
    boxb(760, B - 30, 60, 30)
    for wx in range(766, 814, 9):
        L.rect(wx, B - 22, 4, 7, C['win'])
    boxb(824, B - 22, 96, 22)
    chimney(L, 884, B, 126, 8, 5, C, bands=2)
    boxb(1170, B - 24, 60, 24)
    for k in range(1172, 1226, 12):
        L.rect(k + 3, B - 18, 6, 8, C['win'])
    for tx in (306, 806, 860):
        bare_tree(L, tx, B, 42, TE[3], seed=tx, trunk_w=1)
    base_fill(L, B, (C['body'], C['sh'], C['lit']), seed=3, amp=(8, 3), period=(17.0, 5.0))
    fog_base(L, [TE[2], TE[3], SA[1], SA[2], SA[3], SA[4]], B - 44, B + 1, 2.4)
    return L, TOP


def hazy_brick(L, x, y, w, h, BR):
    """Near-bg brick: body + dithered coursing (no individual bricks at this depth)."""
    L.rect(x, y, w, h, BR['body'], hgt=0.5)
    for yy in range(y + 1, y + h, 3):
        for xx in range(x, x + w):
            if (xx + (yy // 3) * 2) % 4 != 0:
                L.px(xx, yy, BR['sh'], 0.46)


# =========================================================================== NEAR BG (0.72)
def make_near_bg():
    """Base y 248, visible mostly above the yard fences (y < 214).  Barrack + laundry x 0-200 (cam0),
    low sheds under the sun x 230-680 (cam0), depot hall x 690-1000 (cam640 centre), low warehouse
    x 1004-1074 (sun gap at cam640), house under repair x 1082-1248, slab block x 1256-1452 and
    low houses x 1458-1564 (sun gap at cam1280)."""
    p = 0.72
    W, H, TOP = layer_w(p), 150, 100
    L = Layer(W, H, 'near_bg')
    B = 249 - TOP
    C = dict(deep=TE[0], sh=TE[1], body=TE[2], lit=TE[3], rim=TE[4], top=SN[1], snow=SN[2], glass=NI[3],
             win=NI[3], band=TE[3])
    BR = dict(deep=NI[3], sh=TE[0], body=WO[1], lit=WO[2], rim=TE[4])

    def roof_snow(x, y, w):
        snow_top(L, x, y, w, [SN[0], SN[1], SN[2]], depth=2, seed=x)

    def gable(x, y, w, k_h, col_top=None):
        for k in range(k_h):
            L.hline(x - 3 + k * 2, y - 1 - k, w + 6 - k * 4, C['sh'] if k > 0 else C['lit'], 0.6)
            L.px(x + w + 2 - k * 2, y - 1 - k, C['rim'])
        roof_snow(x - 2, y - k_h, w + 4)

    # ---- residential barrack (2 storeys) with stovepipes through windows + laundry line
    x0, w0, h0 = 4, 156, 66
    y0 = B - h0
    L.rect(x0, y0, w0, h0, C['body'], hgt=0.5)
    for yy in range(y0 + 2, y0 + 32, 3):
        L.hline(x0, yy, w0, C['sh'], 0.45)
    hazy_brick(L, x0, y0 + 33, w0, h0 - 33, BR)
    L.vline(x0, y0, h0, C['deep'])
    L.vline(x0 + w0 - 1, y0, h0, C['rim'])
    gable(x0, y0, w0, 12)
    for i in range(7):
        wx = x0 + 8 + i * 21
        for wy in (y0 + 8, y0 + 40):
            L.rect(wx - 1, wy - 1, 9, 13, C['lit'], hgt=0.55)
            L.rect(wx, wy, 7, 11, C['win'], hgt=0.25)
            L.vline(wx + 3, wy, 11, C['lit'])
            L.hline(wx, wy + 4, 7, C['lit'])
            L.px(wx + 6, wy, C['rim'])
            L.hline(wx - 1, wy + 12, 9, SN[1])
    for (sx, sy) in [(x0 + 32, y0 + 12), (x0 + 116, y0 + 44)]:
        L.hline(sx, sy, 10, NI[2])
        L.vline(sx + 9, sy - 16, 17, NI[2])
        L.vline(sx + 10, sy - 16, 17, C['rim'])
        L.hline(sx + 8, sy - 17, 4, NI[1])
    pole_x = x0 + w0 + 40
    L.vline(pole_x, B - 56, 56, WO[2])
    L.vline(pole_x + 1, B - 56, 56, C['rim'])
    pts = pg.catenary(x0 + w0 - 1, y0 + 26, pole_x, B - 54, 6)
    L.polyline([(round(a), round(b)) for a, b in pts], NI[3])
    for i, t in enumerate([0.12, 0.26, 0.4, 0.55, 0.7, 0.84]):
        lx, ly = pts[int(t * (len(pts) - 1))]
        cols = [SN[2], TE[3], RU[2], SN[1], SA[2], SN[2]]
        L.rect(int(lx), int(ly) + 1, 5 + (i % 2) * 2, 7 - (i % 3), cols[i], hgt=0.6)
        L.vline(int(lx) + 4 + (i % 2) * 2, int(ly) + 1, 7 - (i % 3), C['rim'])
    fig = figure(31, [TE[1], TE[2], TE[3]], hat='scarf', hat_col=SN[1], rim=C['rim'], seed=5,
                 trousers=TE[1], boots=NI[2], skin=RU[3])
    L.blit(fig, x0 + w0 + 18 - fig.w // 2, B - fig.h + 1)
    # ---- low sheds/garages (stay under the sun glow at cam0)
    for (sx, sw, sh_) in [(232, 70, 30), (310, 50, 24), (370, 90, 34), (470, 80, 26), (560, 60, 30),
                          (626, 50, 22)]:
        L.rect(sx, B - sh_, sw, sh_, C['body'], hgt=0.5)
        for xx in range(sx, sx + sw, 3):
            L.vline(xx, B - sh_, sh_, C['sh'])
        L.vline(sx + sw - 1, B - sh_, sh_, C['rim'])
        L.hline(sx - 1, B - sh_ - 1, sw + 2, C['lit'])
        roof_snow(sx - 1, B - sh_ - 2, sw + 2)
        L.rect(sx + 6, B - sh_ + 6, 8, 6, C['win'])
    # stovepipe smoke source on a shed (anim fx placed in scene.json)
    L.vline(420, B - 46, 12, NI[2])
    L.vline(421, B - 46, 12, C['rim'])
    # ---- depot hall with arched gates
    dx, dw, dh = 690, 310, 78
    dy = B - dh
    hazy_brick(L, dx, dy, dw, dh, BR)
    L.vline(dx, dy, dh, BR['deep'])
    L.vline(dx + dw - 1, dy, dh, BR['rim'])
    for k in range(dx, dx + dw, 62):
        L.rect(k, dy, 5, dh, BR['lit'], hgt=0.6)
        L.vline(k + 4, dy, dh, TE[3])
    for k in range(5):
        gx = dx + 12 + k * 62
        if gx + 40 > dx + dw:
            continue
        gw, gh = 38, 50
        gy = B - gh
        for yy in range(gy, B):
            rel = yy - gy
            half = int(math.sqrt(max(0, 19 ** 2 - (12 - rel) ** 2 * 3))) if rel < 12 else 19
            L.hline(gx + 19 - half, yy, 2 * half, C['deep'] if k != 2 else NI[1], 0.2)
        for a in range(0, 181, 12):
            ax = gx + 19 + int(math.cos(math.radians(a)) * 20)
            ay = gy + 12 - int(math.sin(math.radians(a)) * 12)
            L.px(ax, ay, BR['lit'])
        if k == 2:  # open gate, steam loco smokebox inside (cold, unlit)
            lx = gx + 19
            L.ellipse(lx, B - 24, 11, 11, NI[2])
            L.ellipse(lx, B - 24, 8, 8, NI[3])
            L.ellipse(lx, B - 25, 1.6, 1.6, SN[0])
            L.rect(lx - 13, B - 13, 26, 3, NI[2])
            L.rect(lx - 9, B - 8, 18, 8, NI[1])
        else:
            for xx in range(gx + 1, gx + 38, 3):
                L.vline(xx, gy + 6, gh - 6, C['sh'])
            L.vline(gx + 19, gy + 2, gh - 2, C['deep'])
        for j in range(3):
            L.rect(gx + 2 + j * 12, dy + 8, 8, 12, C['win'], hgt=0.25)
            L.px(gx + 9 + j * 12, dy + 8, C['lit'])
    for k in range(8):
        L.hline(dx - 4 + k * 2, dy - 1 - k, dw + 8 - k * 4, C['sh'] if k > 0 else C['lit'], 0.6)
    roof_snow(dx - 2, dy - 8, dw + 4)
    L.rect(dx + 110, dy - 20, 90, 12, C['body'], hgt=0.6)
    for k in range(dx + 114, dx + 196, 6):
        L.rect(k, dy - 17, 3, 7, C['win'])
    L.vline(dx + 199, dy - 20, 12, C['rim'])
    roof_snow(dx + 110, dy - 21, 90)
    text(L, dx + 142, dy + 1, 'ДЕПО', SN[0], font='s')
    # ---- warehouses
    for (wx, ww, wh) in [(1004, 70, 38)]:
        L.rect(wx, B - wh, ww, wh, C['body'], hgt=0.5)
        for xx in range(wx, wx + ww, 4):
            L.vline(xx, B - wh, wh, C['sh'])
        L.vline(wx, B - wh, wh, C['deep'])
        L.vline(wx + ww - 1, B - wh, wh, C['rim'])
        for k in range(7):
            L.hline(wx - 3 + k, B - wh - 1 - k, ww + 6 - 2 * k, C['lit'] if k == 0 else C['sh'], 0.6)
        roof_snow(wx - 2, B - wh - 7, ww + 4)
    # ---- house under repair (behind the hoarding at cam ~1000-1300)
    rx, rw, rh = 1082, 166, 96
    ry = B - rh
    hazy_brick(L, rx, ry, rw, rh, BR)
    L.vline(rx, ry, rh, BR['deep'])
    L.vline(rx + rw - 1, ry, rh, BR['rim'])
    for fl in range(3):
        for i in range(6):
            wx = rx + 10 + i * 26
            wy = ry + 10 + fl * 29
            L.rect(wx - 1, wy - 1, 12, 17, BR['lit'], hgt=0.55)
            L.rect(wx, wy, 10, 15, C['win'] if (fl + i) % 4 else NI[1], hgt=0.25)
            L.vline(wx + 5, wy, 15, BR['lit'])
            L.px(wx + 9, wy, C['lit'])
    for xx in range(rx + 110, rx + rw):
        cut = int(min(34, (xx - rx - 110) * 0.7 + 5 * math.sin(xx / 3.0)))
        L.rect(xx, ry, 1, max(0, cut), np.zeros(4, np.uint8))
        if 0 < cut < rh:
            L.px(xx, ry + cut, SN[1])
    L.rect(rx + 20, ry + 46, 50, 16, BR['lit'], hgt=0.55)
    for yy in range(ry + 47, ry + 62, 2):
        L.hline(rx + 20, yy, 50, BR['body'])
    for k in range(7):
        L.vline(rx + 96 + k * 12, ry + 4, rh - 4, WO[3])
    for yy in range(ry + 8, B, 18):
        L.hline(rx + 92, yy, 82, WO[4])
        L.hline(rx + 92, yy + 1, 82, WO[1])
    L.hline(rx - 2, ry, 112, SN[2])
    tiny_person(L, rx + 120, ry + 26, 14, NI[2], rim=C['rim'], seed=3)
    tiny_person(L, rx + 152, ry + 62, 14, NI[2], rim=C['rim'], seed=4)
    # ---- 5-storey prefab slab block
    ax, aw, ah = 1256, 196, 112
    ay = B - ah
    L.rect(ax, ay, aw, ah, C['body'], hgt=0.5)
    for yy in range(ay, B, 21):
        L.hline(ax, yy, aw, C['sh'], 0.45)
    for xx in range(ax, ax + aw, 24):
        L.vline(xx, ay, ah, C['sh'], 0.45)
    L.vline(ax, ay, ah, C['deep'])
    L.vline(ax + aw - 1, ay, ah, C['rim'])
    L.hline(ax, ay, aw, SN[2])
    L.hline(ax, ay + 1, aw, SN[1])
    r = np.random.default_rng(57)
    for fl in range(5):
        for i in range(8):
            wx = ax + 7 + i * 24
            wy = ay + 6 + fl * 21
            L.rect(wx, wy, 9, 11, C['win'], hgt=0.25)
            L.vline(wx + 4, wy, 11, C['sh'])
            L.px(wx + 8, wy, C['lit'])
            L.hline(wx - 1, wy + 11, 11, SN[0])
            if r.random() < 0.1:
                L.rect(wx - 2, wy + 7, 13, 5, C['lit'], hgt=0.6)
                L.hline(wx - 2, wy + 7, 13, SN[1])
    for (hx_, hw_, hh_) in [(1458, 44, 26), (1508, 56, 30)]:
        L.rect(hx_, B - hh_, hw_, hh_, C['body'], hgt=0.5)
        for yy in range(B - hh_ + 2, B, 3):
            L.hline(hx_, yy, hw_, C['sh'])
        L.vline(hx_ + hw_ - 1, B - hh_, hh_, C['rim'])
        for k in range(hw_ // 2 + 2):
            L.hline(hx_ - 2 + k, B - hh_ - 1 - k // 2, hw_ + 4 - 2 * k, C['sh'] if k else C['lit'])
        roof_snow(hx_ - 1, B - hh_ - hw_ // 4 - 2, hw_ + 2)
        L.rect(hx_ + 7, B - hh_ + 7, 6, 8, C['win'])
        L.vline(hx_ + hw_ // 2, B - hh_ - hw_ // 4 - 9, 9, NI[2])
    base_fill(L, B, (C['sh'], C['deep'], C['sh']), seed=4, amp=(5, 2), period=(9.0, 3.1))
    fog_base(L, [NI[3], TE[1], TE[2], TE[3], TE[4], SA[2]], B - 28, B + 1, 2.0)
    return L, TOP


def birch(L, x, base, h, seed=0, trunk=(SN[1], SN[2]), mark=NI[2], twig=TE[2], twig2=TE[3]):
    """Bare winter birch: slim pale trunk, upward main limbs, fine drooping twig network."""
    rng = np.random.default_rng(seed)
    th = int(h * 0.8)
    pts = []
    for k in range(th):
        xx = x + int(round(math.sin(k / 17.0 + seed) * 1.3))
        L.px(xx, base - k, trunk[0], 0.5)
        if k < th * 0.55:
            L.px(xx + 1, base - k, trunk[1], 0.5)
        if (k * 7 + seed) % 9 == 0 or (k * 5) % 13 == 0:
            L.px(xx + (k % 2), base - k, mark)
        pts.append((xx, base - k))

    def limb(x0, y0, ang, ln, depth):
        segs = max(2, int(ln / 3))
        cx, cy = x0, y0
        for i in range(segs):
            ang2 = ang + rng.uniform(-0.25, 0.25)
            nx = cx + math.cos(ang2) * ln / segs
            ny = cy - math.sin(ang2) * ln / segs
            L.line(cx, cy, nx, ny, twig if depth > 1 else twig2, 0.4)
            cx, cy = nx, ny
            if depth > 0 and rng.random() < 0.55:
                side = rng.choice([-1, 1])
                limb(cx, cy, ang + side * rng.uniform(0.4, 0.9), ln * rng.uniform(0.35, 0.6), depth - 1)
        if depth <= 1:  # drooping hair twigs
            for _ in range(int(rng.integers(1, 3))):
                L.line(cx, cy, cx + rng.uniform(-2, 2), cy + rng.uniform(3, 7), twig2)

    for i in range(7):
        k = int(th * rng.uniform(0.35, 0.95))
        sx, sy = pts[min(k, len(pts) - 1)]
        side = -1 if i % 2 else 1
        ang = math.pi / 2 + side * rng.uniform(0.25, 0.75)
        limb(sx, sy, ang, h * rng.uniform(0.18, 0.32), 2)
    limb(pts[-1][0], pts[-1][1], math.pi / 2 + rng.uniform(-0.2, 0.2), h * 0.18, 2)


# =========================================================================== POLES (0.86)
def make_poles():
    """Telegraph poles every 172 px with sagging wires and crows, three bare birches and the distant
    home-signal mast with the red lamp at x 1662 (screen ~560 at cam 1280)."""
    p = 0.86
    W, H, TOP = layer_w(p), 172, 82
    L = Layer(W, H, 'poles')
    B = 252 - TOP
    col, rim = NI[2], TE[3]
    tops = []
    xs = list(range(52, W, 172))
    for i, x in enumerate(xs):
        h = 130 + (i % 3) * 5
        y = B - h
        L.rect(x, y, 3, h, col, hgt=0.5)
        L.vline(x + 2, y, h, rim)
        cyl_normal(L, x, y, 3, h)
        for k, (aw, dy) in enumerate([(22, 6), (16, 14)]):
            L.rect(x - aw // 2 + 1, y + dy, aw, 2, NI[1], hgt=0.6)
            L.hline(x - aw // 2 + 1, y + dy, aw, TE[2])
            for ix in range(x - aw // 2 + 2, x + aw // 2 + 1, 5):
                L.px(ix, y + dy - 1, SN[1])
                tops.append((ix, y + dy - 1, k))
        L.line(x + 2, y + 34, x + 13, B, col)
    by_k = {}
    for (ix, iy, k) in tops:
        by_k.setdefault(k, []).append((ix, iy))
    for k, pts in by_k.items():
        pts.sort()
        for i in range(len(pts) - 1):
            a, b = pts[i], pts[i + 1]
            if 140 < b[0] - a[0] < 200:
                pg.wire(L, a[0], a[1] + 1, b[0], b[1] + 1, 9 + k * 3, NI[3])
    for cx in (xs[2] + 58, xs[2] + 69, xs[6] + 92):
        ys = np.nonzero(L.c[:, cx, 3] > 0)[0]
        ys = [y for y in ys if y > 20]
        if ys:
            wy = ys[0]
            L.rect(cx - 1, wy - 3, 3, 3, NI[0])
            L.px(cx + 1, wy - 4, NI[0])
            L.px(cx - 2, wy - 2, NI[0])
            L.px(cx + 2, wy - 4, NI[1])
    # bare birches: pale trunks with dark marks, fine twig crowns
    for bx in (150, 640, 1214):
        birch(L, bx, B, 94, seed=bx)
    # distant home signal mast with the red lamp (scenery only, no real signalling)
    sx = 1662
    L.rect(sx, B - 108, 3, 108, col, hgt=0.5)
    L.vline(sx + 2, B - 108, 108, rim)
    L.rect(sx - 4, B - 118, 11, 12, NI[1], hgt=0.6)
    L.ellipse(sx + 1.5, B - 114, 2.6, 2.6, RED[2], em=RED[2])
    L.px(sx + 1, B - 115, RED[3], em=RED[3])
    L.px(sx + 2, B - 115, RED[3], em=RED[3])
    L.rect(sx - 2, B - 104, 7, 6, NI[1])
    L.px(sx + 1, B - 102, NI[3])
    for k in range(0, 104, 6):
        L.px(sx - 1, B - 104 + k, NI[3])
    L.hline(sx - 5, B - 119, 13, SN[1])
    return L, TOP
