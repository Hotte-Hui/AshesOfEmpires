"""env_karsk_yard -- playfield-level art (parallax 1) for scene A1 'Verladebahnhof Karsk'.

Layout of the walkable band (world y, oblique Mode B, tracks run horizontally):
    250..262  back strip (cinder path along the back-line buildings: cabin door, freight office)
    262..276  track 2      rails y 264 / 272
    276..284  ballast between the tracks
    284..297  track 1      rails y 286 / 294   (the C-17 wagon stands here)
    297..300  platform edge stones (worn white stripe)
    300..360  platform (concrete slabs, slush, puddles reflecting lamps)
Back-line buildings stand with their base on y = 250 and are never walkable.
All drawing here uses world coordinates (layers are full 360 px tall, cropped on export).
"""
from __future__ import annotations

import os as _os
import sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))

import math

import numpy as np

import pg
import env_karsk_emblems as EMB
import env_karsk_life as LF
from env_karsk_lib import (Layer, NI, TE, SA, SK, ST, RU, CO, SN, WO, RED, bayer, value_noise, dmask,
                           ladder_shift, text, text_width, cyl_normal, flat_normal, figure, snow_top,
                           stains, bricks, crop_box)

W = 1920
GROUND_Y = 250
RAIL2 = (264, 272)
RAIL1 = (286, 294)
PLATFORM_EDGE = 297
UP = (0.0, 0.55, 0.83)     # oblique ground normal (faces up/toward the camera, OpenGL +Y up)
CLEAR = np.zeros(4, np.uint8)


# =========================================================================== small painters
def snowline(L, x, y, w, depth=2, seed=0, cols=None):
    cols = cols or [SN[1], SN[2], SN[3]]
    snow_top(L, x, y, w, cols, depth=depth, seed=seed)


def brick_wall(L, x, y, w, h, seed=0, rim=True, soot=True):
    bricks(L, x, y, w, h, RU[1], RU[0], alt=RU[2], seed=seed, alt_prob=0.10, hgt=0.5)
    rng = np.random.default_rng(seed)
    # scattered sooty bricks + lighter repaired bricks (reconstruction)
    for _ in range(int(w * h / 90)):
        bx = x + int(rng.integers(0, max(1, w - 3)))
        by = y + 2 * int(rng.integers(0, max(1, h // 2)))
        L.rect(bx, by, 3, 1, NI[3] if rng.random() < 0.6 else RU[2])
    if rim:
        for yy in range(y, y + h):
            L.px(x + w - 1, yy, RU[3] if yy % 2 else RU[4])
        L.vline(x, y, h, RU[0])


def planks_h(L, x, y, w, h, base, line, hi=None, step=3, seed=0, hgt=0.5):
    L.rect(x, y, w, h, base, hgt=hgt)
    rng = np.random.default_rng(seed)
    for yy in range(y + step - 1, y + h, step):
        L.hline(x, yy, w, line, hgt - 0.06)
        if hi is not None:
            for xx in range(x, x + w):
                if rng.random() < 0.08:
                    L.px(xx, yy - 1, hi)


def planks_v(L, x, y, w, h, base, line, hi=None, step=3, seed=0, hgt=0.5, ragged_top=0):
    rng = np.random.default_rng(seed)
    for xx in range(x, x + w):
        top = y + (int(rng.integers(0, ragged_top + 1)) if ragged_top and (xx - x) % step == 0 else 0)
        col = line if (xx - x) % step == step - 1 else base
        L.rect(xx, top, 1, h - (top - y), col, hgt=hgt if col is base else hgt - 0.06)
        if hi is not None and (xx - x) % step == 0 and rng.random() < 0.5:
            L.vline(xx, top, int(rng.integers(2, max(3, h // 3))), hi)


def window_dark(L, x, y, w, h, frame=SN[1], frame_sh=TE[1], glass=NI[1], refl=TE[3], mull=True, sill=True,
                curtain=None, seed=0):
    L.rect(x - 1, y - 1, w + 2, h + 2, frame, hgt=0.6)
    L.vline(x - 1, y - 1, h + 2, frame_sh)
    L.rect(x, y, w, h, glass, hgt=0.22)
    # cold sky reflection: diagonal soft band in the upper part
    for k in range(min(w, h) // 2 + 2):
        xx = x + w - 2 - k
        yy = y + 1 + k // 2
        if x <= xx < x + w and y <= yy < y + h:
            L.px(xx, yy, refl)
    L.px(x + w - 1, y, SK[1])
    if curtain is not None:
        L.rect(x, y, max(2, w // 3), h, curtain, hgt=0.25)
        L.vline(x + max(2, w // 3) - 1, y, h, frame_sh)
    if mull:
        L.vline(x + w // 2, y, h, frame, 0.55)
        L.hline(x, y + h // 3, w, frame, 0.55)
    if sill:
        L.hline(x - 2, y + h + 1, w + 4, SN[3], 0.75)
        L.hline(x - 2, y + h + 2, w + 4, ST[1], 0.7)


def window_lit(L, x, y, w, h, frame=SN[1], seed=0, figure_inside=True):
    """The ONE amber window: warm glass, emissive, with a hint of interior (lamp, kettle, chart)."""
    L.rect(x - 1, y - 1, w + 2, h + 2, frame, hgt=0.6)
    em_a = CO[3].copy()
    L.rect(x, y, w, h, CO[2], hgt=0.22, em=CO[2])
    # warmer core around the desk lamp only (amber), deep copper toward the edges
    L.rect(x + w - 12, y + 3, 9, h - 8, CO[3], em=CO[3])
    L.rect(x + w - 10, y + 6, 4, 3, CO[4], em=CO[4])
    L.rect(x + 2, y + h - 6, w - 4, 3, CO[1], em=CO[1])
    L.hline(x, y + h - 1, w, CO[1])
    L.vline(x, y, h, CO[1])
    L.vline(x + w - 1, y, h, CO[1])
    for k in (0, 1):
        L.px(x + k, y + h - 1, CO[1])
    L.em[y:y + h, x:x + w] = np.where(L.c[y:y + h, x:x + w, 3:4] > 0, L.c[y:y + h, x:x + w], 0)
    if figure_inside:
        # desk lamp (green shade) + kettle silhouette + wall chart, all as warm-shadow shapes
        lx = x + w - 8
        L.rect(lx, y + 5, 5, 2, TE[1])
        L.px(lx + 2, y + 7, CO[4])
        L.vline(lx + 1, y + 7, h - 10, RU[0])
        L.rect(lx - 2, y + h - 4, 7, 1, RU[0])
        L.rect(x + 3, y + h - 7, 5, 4, RU[1])          # kettle
        L.px(x + 8, y + h - 6, RU[1])
        L.px(x + 5, y + h - 8, RU[1])
        L.rect(x + 3, y + 3, 6, 5, CO[2])              # wall schedule sheet
        L.hline(x + 4, y + 4, 4, CO[1])
        L.hline(x + 4, y + 6, 3, CO[1])
        for yy in range(y, y + h):
            for xx in range(x, x + w):
                c = L.c[yy, xx]
                L.em[yy, xx] = c if c[3] else 0
    L.vline(x + w // 2, y, h, frame, 0.55)
    L.hline(x, y + h // 3, w, frame, 0.55)
    # warm spill on the frame's inner edges and the sill below
    L.hline(x - 2, y + h + 1, w + 4, CO[2], 0.75)
    L.hline(x - 2, y + h + 2, w + 4, ST[1], 0.7)
    L.px(x - 1, y + h, CO[1])
    L.px(x + w, y + h, CO[1])
    return (x, y, w, h)


def door(L, x, y, w, h, col=WO[2], sh=WO[1], frame=ST[2], hi=WO[3], window=True, handle=True):
    L.rect(x - 2, y - 2, w + 4, h + 2, frame, hgt=0.6)
    L.vline(x - 2, y - 2, h + 2, ST[1])
    L.rect(x, y, w, h, col, hgt=0.4)
    for xx in range(x + 2, x + w, 3):
        L.vline(xx, y + 1, h - 1, sh, 0.36)
    L.vline(x + w - 1, y, h, hi)
    L.hline(x, y + h // 2, w, sh, 0.38)
    L.line(x + 1, y + h // 2, x + w - 2, y + h - 2, sh)
    if window:
        L.rect(x + 3, y + 5, w - 6, 9, NI[1], hgt=0.25)
        L.px(x + w - 5, y + 6, TE[3])
        L.vline(x + w // 2, y + 5, 9, col)
    if handle:
        L.px(x + w - 3, y + h // 2 + 2, ST[4])
    L.rect(x - 3, y + h - 2, w + 6, 2, ST[2], hgt=0.62)  # concrete step
    L.hline(x - 3, y + h - 2, w + 6, SN[3])


def roof_hip(L, x, y_eave, w, rise, inset, col=NI[3], col2=TE[0], snow=True, seed=0):
    """Hipped roof seen from the front: trapezoid, slight shading, snow on the top and slopes."""
    for k in range(rise):
        t = k / max(1, rise - 1)
        xl = int(round(x + inset * t))
        xr = int(round(x + w - inset * t))
        yy = y_eave - k
        L.hline(xl, yy, xr - xl, col if k % 3 else col2, 0.6 + 0.1 * t)
        L.px(xr - 1, yy, TE[3])
        L.px(xl, yy, NI[1])
    L.hline(x - 1, y_eave, w + 2, NI[1], 0.55)
    L.hline(x - 1, y_eave + 1, w + 2, NI[2], 0.5)
    if snow:
        rng = np.random.default_rng(seed)
        top_y = y_eave - rise + 1
        xl = int(round(x + inset))
        xr = int(round(x + w - inset))
        snowline(L, xl, top_y, xr - xl, depth=3, seed=seed)
        rows = []
        for k in range(1, rise - 1):
            t = k / max(1, rise - 1)
            rows.append((y_eave - k, int(round(x + inset * t)) + 1, int(round(x + w - inset * t)) - 1, t))
        roof_snow(L, rows, seed=seed)
        snowline(L, x, y_eave - 1, w, depth=1, seed=seed + 1, cols=[SN[1], SN[2]])


def roof_snow(L, rows, seed=0, cover=0.55):
    """Snow lying on a pitched roof seen from the front.  rows: list of (y, xl, xr, t) with t = 0 at the
    eave .. 1 at the ridge.  Snow forms horizontal runs (on the courses) that merge toward the ridge;
    the lower courses are partly bare (slid / melted), giving clean clusters instead of dot grids."""
    for (y, xl, xr, t) in rows:
        n = value_noise(max(2, xr - xl), 1, 7, seed=seed * 31 + y, octaves=2)[0]
        thr = 1.0 - cover * (0.35 + 0.9 * t)
        for i, xx in enumerate(range(xl, xr)):
            v = n[i]
            if v > thr:
                edge = v < thr + 0.06
                L.px(xx, y, SN[1] if edge else (SN[3] if t > 0.8 else SN[2]), 0.72)
                L.nrm[y, xx] = (0.0, 0.8, 0.6)


def concrete_fence(L, x0, x1, y_top=218, seed=0, gaps=(), broken=()):
    """Soviet concrete panel fence with the diamond relief pattern.  Panels 38 px + 4 px posts."""
    yb = GROUND_Y
    x = x0
    i = 0
    rng = np.random.default_rng(seed)
    while x < x1:
        pw = min(38, x1 - x)
        # post
        L.rect(x, y_top - 4, 4, yb - y_top + 4, ST[2], hgt=0.65)
        L.vline(x + 3, y_top - 4, yb - y_top + 4, ST[4])
        L.vline(x, y_top - 4, yb - y_top + 4, ST[1])
        snowline(L, x, y_top - 4, 4, depth=2, seed=x)
        px0 = x + 4
        if i in gaps:
            x += 4 + pw
            i += 1
            continue
        top = y_top
        L.rect(px0, top, pw - 4, yb - top, ST[2], hgt=0.5)
        # diamond relief
        for yy in range(top + 2, yb - 2):
            for xx in range(px0 + 1, px0 + pw - 5):
                u = (xx - px0) % 8
                v = (yy - top - 2) % 6
                d = abs(u - 4) / 4.0 + abs(v - 3) / 3.0
                if 0.85 < d < 1.2:
                    L.px(xx, yy, ST[1] if (u < 4) == (v < 3) else ST[3], 0.46)
        L.hline(px0, top, pw - 4, ST[3], 0.6)
        L.hline(px0, yb - 3, pw - 4, ST[1], 0.45)
        snowline(L, px0, top, pw - 4, depth=2, seed=x + 3)
        if i in broken:  # broken panel: jagged top
            for xx in range(px0, px0 + pw - 4):
                cut = int(6 + 5 * math.sin(xx * 0.9) + rng.integers(0, 4))
                L.rect(xx, top, 1, cut, CLEAR)
                L.px(xx, top + cut, SN[2])
                L.px(xx, top + cut + 1, ST[1])
        # grime at the bottom
        for xx in range(px0, px0 + pw - 4):
            for yy in range(yb - 8, yb):
                if (xx + yy) % 3 == 0 and rng.random() < (yy - (yb - 8)) / 10:
                    L.px(xx, yy, ST[1])
        x += 4 + pw
        i += 1
    # snow drift along the foot
    for xx in range(x0, x1):
        dh = int(2 + 1.5 * math.sin(xx / 9.0) + rng.integers(0, 2))
        for k in range(dh):
            L.px(xx, yb - 1 - k, SN[1] if k == dh - 1 else SN[0], 0.55)


def sleepers_pile(L, x, w, h_layers=4, seed=0):
    rng = np.random.default_rng(seed)
    yb = GROUND_Y
    for k in range(h_layers):
        y = yb - (k + 1) * 4
        inset = k * 3 + int(rng.integers(0, 2))
        L.rect(x + inset, y, w - 2 * inset, 4, WO[1], hgt=0.55 + k * 0.05)
        L.hline(x + inset, y, w - 2 * inset, WO[3])
        for xx in range(x + inset, x + w - inset, 13):
            L.vline(xx, y, 4, WO[0])
        L.vline(x + w - inset - 1, y, 4, WO[4])
    snowline(L, x + h_layers * 3, yb - h_layers * 4, w - h_layers * 6, depth=2, seed=seed)


# =========================================================================== back-line buildings
def signal_box(L, E):
    """Dispatcher cabin / signal box: brick ground floor, timber operator room with the ONE amber
    window, external stair, station nameplate КАРСК, loudspeaker horn, stovepipe."""
    x0 = 470
    # ground floor
    brick_wall(L, 474, 190, 112, 60, seed=7)
    L.rect(474, 244, 112, 6, ST[1], hgt=0.62)               # plinth
    L.hline(474, 244, 112, ST[3])
    for yy in range(244, 250, 2):
        L.hline(474, yy + 1, 112, ST[0])
    door(L, 482, 198, 17, 52)
    L.rect(479, 194, 23, 2, NI[2], hgt=0.7)                 # door canopy
    snowline(L, 479, 193, 23, depth=1)
    for wx in (522, 556):
        window_dark(L, wx, 205, 14, 18, frame=ST[3], frame_sh=ST[1], refl=TE[2], mull=False, sill=True)
        for bx in range(wx + 2, wx + 14, 3):                  # bars
            L.vline(bx, 205, 18, NI[3])
    # stains under the ground-floor windows
    stains(L, 520, 226, 50, 18, [RU[0], RU[1], RU[2]], seed=4, density=0.4, length=(3, 10))
    # nameplate
    L.rect(506, 191, 29, 10, SN[1], hgt=0.7)
    L.rect(507, 192, 27, 8, TE[0], hgt=0.68)
    tw = text_width('КАРСК', 's')
    text(L, 507 + (27 - tw) // 2, 194, 'КАРСК', SN[3])
    # operator room (timber, painted teal-green)
    planks_h(L, 470, 150, 120, 40, TE[2], TE[1], hi=TE[3], seed=3)
    L.rect(470, 150, 3, 40, TE[1], hgt=0.62)
    L.rect(587, 150, 3, 40, TE[3], hgt=0.62)
    L.vline(589, 150, 40, TE[4])
    L.rect(468, 186, 124, 4, NI[2], hgt=0.66)                # floor beam
    L.hline(468, 186, 124, TE[1])
    # upper door + landing + stair (left)
    door(L, 476, 156, 12, 30, col=TE[1], sh=TE[0], frame=SN[1], hi=TE[3], window=True)
    L.rect(436, 188, 40, 3, WO[2], hgt=0.66)               # landing
    L.hline(436, 188, 40, WO[3])
    snowline(L, 436, 187, 40, depth=1)
    for k in range(0, 61):                                  # stair stringer 45 deg down-left
        sx = 440 - k
        sy = 190 + k
        if sy >= GROUND_Y:
            break
        L.px(sx, sy, WO[1])
        L.px(sx + 1, sy, WO[1])
        L.px(sx + 6, sy, WO[0])
        if k % 4 == 0:
            L.hline(sx, sy, 8, WO[2])
            L.px(sx + 2, sy - 1, SN[2])
            L.px(sx + 3, sy - 1, SN[2])
    for k in range(0, 61, 10):                              # railing posts + rail
        L.vline(438 - k, 178 + k, 12, WO[1])
    L.line(438, 178, 378, 238, WO[2])
    L.vline(436, 178, 10, WO[1])
    L.hline(436, 178, 40, WO[2])
    # windows of the operator room: [dark, AMBER, dark]
    window_dark(L, 494, 157, 22, 24, frame=SN[2], frame_sh=TE[1], refl=TE[3], seed=1)
    lit = window_lit(L, 522, 157, 24, 24, frame=SN[2])
    window_dark(L, 552, 157, 22, 24, frame=SN[2], frame_sh=TE[1], refl=TE[3], curtain=TE[0], seed=2)
    L.px(578, 165, SN[1])
    # roof
    roof_hip(L, 464, 149, 132, 16, 30, seed=5)
    # stovepipe (smoke anim at its top)
    L.rect(566, 116, 3, 22, NI[2], hgt=0.7)
    L.vline(568, 116, 22, TE[3])
    L.rect(565, 114, 5, 2, NI[1], hgt=0.75)
    # loudspeaker horn on a bracket (right corner)
    L.hline(590, 160, 6, NI[2])
    L.rect(595, 158, 3, 5, NI[2])
    L.rect(597, 157, 2, 7, ST[2])
    L.px(598, 157, ST[4])
    # lightning rod / antenna
    L.vline(530, 120, 14, NI[2])
    L.hline(527, 122, 7, NI[2])
    E['amber_window'] = lit
    E['stovepipe_top'] = (567, 113)


def tea_stall(L, E):
    """Tea kiosk ('ЧАЙ') with samovar and the vendor at the hatch, x 252-328."""
    x0, x1 = 256, 326
    y_top = 206
    planks_v(L, x0, y_top, x1 - x0, GROUND_Y - y_top, TE[3], TE[2], hi=TE[4], seed=9)
    # peeling paint: wood showing through
    rng = np.random.default_rng(91)
    for _ in range(26):
        px_ = int(rng.integers(x0, x1 - 2))
        py_ = int(rng.integers(y_top + 30, GROUND_Y - 2))
        L.rect(px_, py_, int(rng.integers(1, 3)), int(rng.integers(1, 4)), WO[2])
    L.vline(x1 - 1, y_top, GROUND_Y - y_top, SK[0])
    L.vline(x0, y_top, GROUND_Y - y_top, TE[1])
    # hatch with vendor
    hx0, hy0, hw, hh = 266, 216, 46, 18
    L.rect(hx0, hy0, hw, hh, NI[1], hgt=0.2)
    vend = figure(40, [TE[0], TE[1], TE[2]], hat='scarf', hat_col=SN[2], rim=TE[4], seed=8,
                  apron=SN[2], skin=RU[4])
    # paste only the upper body of the vendor into the hatch
    sub_h = hh
    for yy in range(sub_h):
        for xx in range(vend.w):
            c = vend.c[yy + 2, xx]
            if c[3]:
                L.px(hx0 + 26 + xx - vend.w // 2, hy0 + yy + 1, c, 0.3)
    # warm-ish interior glint (unlit, no emission: the ONE warm window rule)
    L.hline(hx0, hy0, hw, NI[3])
    L.rect(hx0 - 2, hy0 + hh, hw + 4, 3, WO[3], hgt=0.7)     # counter
    L.hline(hx0 - 2, hy0 + hh, hw + 4, WO[4])
    snowline(L, hx0 - 2, hy0 + hh - 1, 6, depth=1)
    # samovar on the counter
    sx = hx0 + 8
    L.rect(sx, hy0 + hh - 9, 7, 8, RU[3], hgt=0.75)
    L.vline(sx, hy0 + hh - 9, 8, RU[2])
    L.vline(sx + 5, hy0 + hh - 9, 8, RU[4])
    L.vline(sx + 6, hy0 + hh - 8, 6, RU[5])
    L.rect(sx + 2, hy0 + hh - 11, 3, 2, RU[3])
    L.px(sx + 3, hy0 + hh - 13, NI[2])
    L.rect(sx - 1, hy0 + hh - 1, 9, 1, RU[2])
    L.px(sx + 7, hy0 + hh - 5, RU[4])
    cyl_normal(L, sx, hy0 + hh - 11, 7, 10)
    # glasses in holders
    for gx in (hx0 + 30, hx0 + 34):
        L.rect(gx, hy0 + hh - 4, 2, 3, SK[2])
        L.px(gx, hy0 + hh - 4, SN[4])
    # hatch flap propped open above
    L.rect(hx0 - 3, hy0 - 6, hw + 6, 4, TE[3], hgt=0.75)
    L.hline(hx0 - 3, hy0 - 6, hw + 6, TE[4])
    L.hline(hx0 - 3, hy0 - 3, hw + 6, TE[1])
    snowline(L, hx0 - 3, hy0 - 7, hw + 6, depth=2)
    # roof + sign
    L.rect(x0 - 4, y_top - 4, x1 - x0 + 8, 4, NI[3], hgt=0.7)
    L.hline(x0 - 4, y_top - 1, x1 - x0 + 8, NI[1])
    snowline(L, x0 - 4, y_top - 6, x1 - x0 + 8, depth=3)
    L.rect(x0 + 14, y_top - 17, 42, 11, SN[2], hgt=0.7)
    L.rect(x0 + 15, y_top - 16, 40, 9, RU[2], hgt=0.68)
    tw = text_width('ЧАЙ', 'l')
    text(L, x0 + 15 + (40 - tw) // 2, y_top - 16, 'ЧАЙ', SN[3], font='l')
    L.vline(x0 + 54, y_top - 16, 9, RU[3])
    L.vline(x0 + 18, y_top - 6, 2, NI[2])
    L.vline(x0 + 52, y_top - 6, 2, NI[2])
    # stovepipe of the stall (steam/smoke anim) + crate + bucket
    L.rect(x1 - 4, y_top - 20, 3, 16, NI[2], hgt=0.7)
    L.vline(x1 - 2, y_top - 20, 16, TE[3])
    L.hline(x1 - 5, y_top - 21, 5, NI[1])
    E['stall_pipe'] = (x1 - 3, y_top - 22)
    E['samovar'] = (sx + 3, hy0 + hh - 14)
    L.rect(x1 + 2, GROUND_Y - 12, 14, 12, WO[2], hgt=0.6)
    L.hline(x1 + 2, GROUND_Y - 12, 14, WO[4])
    L.hline(x1 + 2, GROUND_Y - 6, 14, WO[1])
    L.vline(x1 + 15, GROUND_Y - 12, 12, WO[3])
    snowline(L, x1 + 2, GROUND_Y - 13, 14, depth=2)
    text(L, x1 + 4, GROUND_Y - 10, 'КВАС', WO[3], font='s')


def relay_hut(L):
    x, w, h = 604, 44, 24
    y = GROUND_Y - h
    L.rect(x, y, w, h, ST[2], hgt=0.5)
    for xx in range(x, x + w, 11):
        L.vline(xx, y, h, ST[1])
    L.vline(x + w - 1, y, h, ST[4])
    L.rect(x - 2, y - 3, w + 4, 3, ST[1], hgt=0.7)
    snowline(L, x - 2, y - 4, w + 4, depth=2)
    L.rect(x + 6, y + 6, 10, 18, NI[3], hgt=0.3)       # steel door
    L.vline(x + 15, y + 6, 18, TE[3])
    L.px(x + 13, y + 15, ST[4])
    for k in range(3):                                  # vent slots
        L.hline(x + 26, y + 7 + k * 3, 10, NI[2])
    # cable duct running along the ground
    L.rect(x + w, GROUND_Y - 3, 46, 3, ST[1], hgt=0.55)
    L.hline(x + w, GROUND_Y - 3, 46, ST[3])


def warehouse(L, E):
    """Open freight canopy (naves) x 744-1094 on timber posts over a concrete loading ramp: dark
    interior with stacked crates and sacks, corrugated roof with snow.  Low and open, so the brick
    depot of the near background stays readable above it."""
    x, w = 744, 350
    eave = 212
    yb = GROUND_Y
    # deep shadow interior: back wall planks barely visible
    planks_v(L, x + 2, eave + 2, w - 4, yb - eave - 10, NI[2], NI[1], step=5, seed=13, hgt=0.2)
    rng = np.random.default_rng(14)
    # goods under the roof (silhouettes with faint rim)
    gx = x + 8
    while gx < x + w - 30:
        kind = rng.integers(0, 3)
        if kind == 0:      # crate stack
            for k in range(int(rng.integers(1, 4))):
                cw = int(rng.integers(12, 20))
                ch = int(rng.integers(8, 12))
                cy = yb - 8 - ch * (k + 1)
                if cy < eave + 4:
                    break
                L.rect(gx, cy, cw, ch, WO[0], hgt=0.35)
                L.hline(gx, cy, cw, WO[1])
                L.vline(gx + cw - 1, cy, ch, WO[1])
                L.line(gx, cy, gx + cw - 1, cy + ch - 1, NI[3])
            gx += 22
        elif kind == 1:    # sacks
            for k in range(int(rng.integers(3, 6))):
                sx = gx + k * 6
                sy = yb - 14 - (k % 2) * 4
                L.ellipse(sx + 4, sy + 3, 4.5, 3, ST[0], hgt=0.35)
                L.px(sx + 6, sy + 1, ST[1])
            gx += 34
        else:              # gap / barrels
            L.rect(gx + 2, yb - 22, 9, 14, RU[0], hgt=0.35)
            L.hline(gx + 2, yb - 18, 9, NI[3])
            L.vline(gx + 10, yb - 22, 14, RU[1])
            gx += 26
    # loading ramp front (concrete) with worn timber edge
    L.rect(x, yb - 8, w, 8, ST[2], hgt=0.62)
    L.hline(x, yb - 8, w, WO[2])
    L.hline(x, yb - 7, w, ST[3])
    for xx in range(x, x + w, 22):
        L.vline(xx, yb - 7, 7, ST[1])
    snowline(L, x, yb - 9, w, depth=1, cols=[SN[0], SN[1]])
    # posts with knee braces
    for px_ in range(x + 2, x + w, 58):
        L.rect(px_, eave, 4, yb - 8 - eave, WO[1], hgt=0.62)
        L.vline(px_ + 3, eave, yb - 8 - eave, WO[3])
        L.line(px_ - 7, eave + 2, px_, eave + 9, WO[1])
        L.line(px_ + 4, eave + 9, px_ + 11, eave + 2, WO[1])
    # roof: corrugated sheet, slight slope toward us, eave board, snow load
    for k in range(9):
        y = eave - 1 - k
        L.hline(x - 6 + k, y, w + 12 - 2 * k, ST[1] if k % 2 else ST[2], 0.66)
    for xx in range(x - 6, x + w + 6, 3):
        L.vline(xx, eave - 8, 8, ST[1])
    L.hline(x - 6, eave, w + 12, WO[1], 0.7)
    L.hline(x - 6, eave + 1, w + 12, NI[2], 0.5)
    L.vline(x + w + 5, eave - 8, 9, ST[4])
    snowline(L, x - 4, eave - 10, w + 8, depth=3, seed=8)
    for xx in range(x - 4, x + w + 4):            # icicles / drips along the eave
        if (xx * 13) % 17 < 2:
            L.vline(xx, eave + 1, 1 + (xx % 3), SN[1])
    text(L, x + 150, eave + 4, 'СКЛАД 2', SN[0], font='s')


def hoarding(L, E, hist=False):
    """Timber construction hoarding x 1100-1462 with the civic banner ВОССТАНОВИМ ВМЕСТЕ and the
    reconstruction / housing notices (obs_poster)."""
    x0, x1 = 1100, 1462
    y_top = 204
    planks_v(L, x0, y_top, x1 - x0, GROUND_Y - y_top, WO[2], WO[1], hi=WO[3], step=4, seed=17, ragged_top=3)
    for xx in range(x0, x1, 4):
        if (xx // 4) % 5 == 0:
            L.vline(xx, y_top, GROUND_Y - y_top, WO[0])
    for yy in (y_top + 8, GROUND_Y - 12):                 # rails
        L.rect(x0, yy, x1 - x0, 3, WO[1], hgt=0.6)
        L.hline(x0, yy, x1 - x0, WO[3])
    for xx in range(x0, x1, 46):                            # posts
        L.rect(xx, y_top - 6, 4, GROUND_Y - y_top + 6, WO[1], hgt=0.66)
        L.vline(xx + 3, y_top - 6, GROUND_Y - y_top + 6, WO[4])
        snowline(L, xx, y_top - 6, 4, depth=2)
    snowline(L, x0, y_top, x1 - x0, depth=2, seed=4)
    # civic banner (cloth, nailed): fictional slogan 'we rebuild together', state emblem at both ends
    # (§12.4: neutral = fictional gear-and-wheat, hist = hammer & sickle; same 11x11 footprint)
    msg = 'ВОССТАНОВИМ ВМЕСТЕ'
    tw = text_width(msg, 'l')
    bx0, by0 = 1146, 213
    ek = EMB.kind_for('gw11', hist)
    ew, eh = EMB.size(ek)
    bw = tw + 2 * (ew + 9) + 4
    bh = 15
    L.rect(bx0, by0, bw, bh, RU[2], hgt=0.62)
    L.hline(bx0, by0, bw, RU[3])
    L.hline(bx0, by0 + bh - 1, bw, RU[1])
    for xx in range(bx0, bx0 + bw):                         # sagging cloth folds (not across the emblems)
        rel = xx - bx0
        if rel % 23 == 11 and ew + 6 < rel < bw - ew - 6:
            L.vline(xx, by0 + 1, bh - 2, RU[1])
    L.vline(bx0 + bw - 1, by0, bh, RU[4])
    text(L, bx0 + ew + 9 + 2, by0 + 4, msg, SN[3], font='l', shadow=RU[1])
    emb = []
    for ex in (bx0 + 4, bx0 + bw - 4 - ew):
        EMB.paint(L, ex, by0 + 2, ek, CO[3], shade=CO[1], hgt=0.64)
        emb.append(('banner_l' if ex < bx0 + bw // 2 else 'banner_r', ex, by0 + 2, ew, eh))
    for nx in (bx0 + 1, bx0 + bw - 2):
        L.px(nx, by0 + 1, ST[4])
        L.px(nx, by0 + bh - 2, ST[3])
    # water stains under the nails + frayed bottom edge
    for nx in (bx0 + 1, bx0 + bw - 2):
        L.px(nx, by0 + bh, RU[1])
    for xx in range(bx0 + 3, bx0 + bw - 3, 7):
        L.px(xx, by0 + bh, RU[1])
    E['banner'] = (bx0, by0, bw, bh)
    E.setdefault('emblems', []).extend(emb)
    # posters near the right end (obs_poster): reconstruction poster (state emblem in a red header band,
    # new housing block + crane) and the typed housing notice
    px0, py0 = 1380, 214
    L.rect(px0, py0, 20, 28, SN[2], hgt=0.6)                 # poster paper
    L.rect(px0 + 1, py0 + 1, 18, 26, CO[4], hgt=0.58)
    L.rect(px0 + 2, py0 + 2, 16, 9, RED[2], hgt=0.59)        # red header band with the emblem
    pk = EMB.kind_for('gw7', hist)
    EMB.paint(L, px0 + 3, py0 + 3, pk, CO[4])
    E['emblems'].append(('poster', px0 + 3, py0 + 3) + EMB.size(pk))
    for k, wy in enumerate((py0 + 4, py0 + 6, py0 + 8)):   # slogan lines in the header
        L.hline(px0 + 11, wy, 6 - k, CO[4])
    L.rect(px0 + 2, py0 + 11, 16, 7, RU[3])                  # printed image: new block + crane
    L.rect(px0 + 4, py0 + 12, 7, 6, SN[3])
    for wy in range(py0 + 13, py0 + 18, 2):
        L.hline(px0 + 5, wy, 5, RU[2])
    L.vline(px0 + 14, py0 + 11, 7, NI[2])
    L.hline(px0 + 11, py0 + 12, 6, NI[2])
    for wy in range(py0 + 19, py0 + 26, 2):                  # printed lines (scribble)
        L.hline(px0 + 3, wy, 13 - (wy % 3) * 2, RU[2])
    L.rect(px0 + 13, py0 + 21, 6, 7, CLEAR)                  # torn corner
    L.px(px0 + 13, py0 + 21, SN[2])
    L.rect(px0 + 24, py0 + 6, 14, 18, SN[3], hgt=0.6)        # housing notice
    for wy in range(py0 + 8, py0 + 22, 2):
        L.hline(px0 + 26, wy, 10 - (wy % 4), ST[2])
    L.rect(px0 + 26, py0 + 8, 6, 2, ST[1])
    L.px(px0 + 30, py0 + 6, NI[2])                            # pin
    L.px(px0 + 9, py0, NI[2])
    # older poster shreds
    L.rect(1328, 222, 12, 14, SN[1], hgt=0.6)
    L.rect(1330, 230, 10, 6, CLEAR)
    for wy in range(224, 230, 2):
        L.hline(1330, wy, 8, ST[2])
    E['poster'] = (px0, py0, 38, 28)


def freight_office(L, E, hist=False):
    """Freight office (Товарная контора) x 1478-1684 with the counter window where the ledger lies,
    warm enamel wall lamp above it, door, notice board, chimney."""
    x, w, h = 1478, 206, 62
    y = GROUND_Y - h
    brick_wall(L, x, y, w, h, seed=21)
    L.rect(x, GROUND_Y - 6, w, 6, ST[1], hgt=0.62)
    L.hline(x, GROUND_Y - 6, w, ST[3])
    door(L, 1494, 198, 18, 52, col=TE[1], sh=TE[0], hi=TE[3])
    L.rect(1490, 192, 26, 3, NI[2], hgt=0.7)
    snowline(L, 1490, 191, 26, depth=1)
    # counter window (open hatch) with shelf + ledger
    cx, cy, cw, ch = 1556, 212, 34, 22
    L.rect(cx - 3, cy - 3, cw + 6, ch + 6, WO[2], hgt=0.62)
    L.vline(cx - 3, cy - 3, ch + 6, WO[1])
    L.vline(cx + cw + 2, cy - 3, ch + 6, WO[4])
    L.rect(cx, cy, cw, ch, NI[1], hgt=0.2)
    # interior: shelves with files (dim), a clerk's lamp is OFF
    for sy in (cy + 4, cy + 11):
        L.hline(cx + 2, sy, cw - 4, WO[1])
        for k in range(cx + 3, cx + cw - 4, 3):
            L.rect(k, sy - 3, 2, 3, [ST[1], WO[1], TE[1]][(k // 3) % 3])
    L.rect(cx - 4, cy + ch, cw + 8, 3, WO[3], hgt=0.75)      # shelf
    L.hline(cx - 4, cy + ch, cw + 8, WO[4])
    L.hline(cx - 4, cy + ch + 2, cw + 8, WO[1])
    # the ledger: dark cover, pale page edge, a red ribbon (story accent, small)
    L.rect(cx + 10, cy + ch - 4, 12, 4, NI[2], hgt=0.8)
    L.hline(cx + 11, cy + ch - 4, 10, SN[3])
    L.hline(cx + 11, cy + ch - 3, 10, SN[2])
    L.vline(cx + 16, cy + ch - 4, 2, ST[2])
    L.px(cx + 19, cy + ch - 1, RED[2])
    L.px(cx + 19, cy + ch, RED[1])
    # sign above: enamel plate with the state emblem medallion at the left (§12.4) + КОНТОРА
    sx0, sw = cx - 6, cw + 12 + 10
    L.rect(sx0, cy - 14, sw, 11, SN[2], hgt=0.68)
    L.rect(sx0 + 1, cy - 13, sw - 2, 9, TE[0], hgt=0.66)
    L.rect(sx0 + 2, cy - 13, 9, 9, RED[1], hgt=0.67)         # red medallion field
    L.vline(sx0 + 10, cy - 13, 9, SN[1])
    mk = EMB.kind_for('gw7', hist)
    EMB.paint(L, sx0 + 3, cy - 12, mk, CO[3])
    E.setdefault('emblems', []).append(('kontora_sign', sx0 + 3, cy - 12) + EMB.size(mk))
    tw = text_width('КОНТОРА', 's')
    text(L, sx0 + 11 + (sw - 12 - tw) // 2, cy - 11, 'КОНТОРА', SN[3])
    L.px(sx0, cy - 4, RU[1])                                 # rust bleeding from the fixing screws
    L.px(sx0 + sw - 1, cy - 4, RU[1])
    # warm enamel wall lamp above the sign
    lx, ly = cx + cw // 2, cy - 22
    L.hline(lx - 6, ly - 3, 7, NI[2])
    L.vline(lx - 6, ly - 3, 4, NI[2])
    L.rect(lx - 3, ly - 1, 7, 2, TE[1], hgt=0.8)
    L.hline(lx - 4, ly + 1, 9, SN[2], 0.8)
    L.rect(lx - 1, ly + 2, 3, 2, CO[4], hgt=0.85, em=CO[4])
    L.px(lx, ly + 2, SN[4], em=SN[4])
    L.px(lx - 2, ly + 2, CO[3], em=CO[3])
    L.px(lx + 2, ly + 2, CO[3], em=CO[3])
    # warm spill on the brick below the lamp (baked, gentle) -> brick tops get copper accents
    for yy in range(ly + 4, cy - 13):
        for xx in range(lx - 10, lx + 11):
            if (L.c[yy, xx, :3] == RU[2][:3]).all() and abs(xx - lx) < 9:
                L.px(xx, yy, RU[4])
    E['office_lamp'] = (lx, ly + 3)
    # other windows (dark)
    for wx in (1530, 1650):
        window_dark(L, wx, 204, 16, 22, frame=SN[1], frame_sh=TE[1], refl=TE[3])
    LF.office_shelf_window(L, 1616, 204, 16, 22)            # exp_kontora_shelf: the bookshelf behind glass
    E['shelf_window'] = (1616, 204, 16, 22)
    # notice board next to the door
    L.rect(1518, 208, 10, 14, WO[2], hgt=0.62)
    L.rect(1519, 209, 8, 12, SN[2])
    for wy in range(210, 220, 2):
        L.hline(1520, wy, 6, ST[2])
    # roof (gable seen from the long side -> trapezoid) + chimney
    for k in range(18):
        L.hline(x - 4 + k, y - 1 - k, w + 8 - 2 * k, NI[3] if k % 4 else TE[0], 0.6 + k * 0.01)
        L.px(x + w + 3 - k, y - 1 - k, TE[3])
    L.hline(x - 5, y - 1, w + 10, NI[1])
    snowline(L, x + 14, y - 18, w - 28, depth=3, seed=6)
    roof_snow(L, [(y - 1 - k, x - 2 + k, x + w + 2 - k, k / 17.0) for k in range(1, 16)], seed=21, cover=0.6)
    L.rect(1652, y - 28, 8, 14, RU[1], hgt=0.7)
    L.vline(1659, y - 28, 14, RU[3])
    L.rect(1651, y - 30, 10, 2, ST[2])
    snowline(L, 1651, y - 31, 10, depth=1)
    E['office_chimney'] = (1656, y - 31)
    E['counter'] = (cx, cy, cw, ch)


def right_end(L, E):
    concrete_fence(L, 1690, 1920, y_top=216, seed=31, broken=(3,))
    sleepers_pile(L, 1760, 60, 4, seed=3)
    # buffer stop of a stub siding (scenery, behind the back strip)
    bx = 1872
    L.rect(bx, 232, 26, 14, NI[3], hgt=0.6)
    L.rect(bx + 2, 234, 22, 3, RED[1])
    for k in range(bx + 4, bx + 22, 6):
        L.rect(k, 234, 3, 3, SN[2])
    L.rect(bx + 4, 246, 4, 4, NI[2])
    L.rect(bx + 18, 246, 4, 4, NI[2])
    snowline(L, bx, 231, 26, depth=1)


PA_POLE_FOOT = (722, 255)        # loudspeaker pole prop (exp_loudspeaker); its cable runs to the cabin horn
PA_POLE_ANCHOR = (713, 153)      # world position of the pole's cable insulator (see LF.loudspeaker_pole)
PA_CABIN_ANCHOR = (597, 159)


def make_yard_back(E, hist=False):
    """Playfield back line.  hist=True paints the real Soviet emblems instead of the fictional gear-and-wheat
    (only the emblem pixels differ; used for the *_hist variant, TECHNICAL_ARCHITECTURE §12.4)."""
    L = Layer(W, 360, 'yard_back')
    E['emblems'] = []
    concrete_fence(L, -2, 252, y_top=218, seed=1, broken=(4,))
    tea_stall(L, E)
    concrete_fence(L, 330, 470, y_top=220, seed=2, gaps=(2,))
    sleepers_pile(L, 336, 58, 3, seed=5)
    signal_box(L, E)
    relay_hut(L)
    concrete_fence(L, 650, 744, y_top=220, seed=4)
    warehouse(L, E)
    hoarding(L, E, hist)
    concrete_fence(L, 1462, 1478, y_top=220, seed=5)
    freight_office(L, E, hist)
    right_end(L, E)
    yard_life(L, E)
    return L


def yard_life(L, E):
    """Round-2 detail pass over the back line: icicles on every eave, rust run-off, drifts against walls,
    the cabin's coal heap, the PA cable (crows' perch) and the cache under the stairs."""
    # icicles (eave underside rows)
    LF.icicles(L, 466, 595, 151, seed=1, density=0.34, maxlen=6)          # signal box roof
    LF.icicles(L, 470, 590, 190, seed=2, density=0.16, maxlen=3)          # operator-room floor beam
    LF.icicles(L, 480, 501, 196, seed=3, density=0.4, maxlen=3)           # cabin door canopy
    LF.icicles(L, 253, 329, 206, seed=4, density=0.3, maxlen=4)           # tea stall roof
    LF.icicles(L, 264, 314, 214, seed=5, density=0.36, maxlen=4)          # tea stall hatch flap
    LF.icicles(L, 603, 649, 226, seed=6, density=0.3, maxlen=4)           # relay hut
    LF.icicles(L, 1476, 1686, 188, seed=7, density=0.24, maxlen=5)        # freight office eave
    LF.icicles(L, 1491, 1515, 195, seed=8, density=0.4, maxlen=3)         # office door canopy
    # rust run-off
    LF.rust_streak(L, 596, 164, 9, seed=11, strong=True)                  # cabin horn bracket
    for k, vx in enumerate((631, 635, 639)):
        LF.rust_streak(L, vx, 235, 7 + k, seed=12 + k)                     # relay hut vents
    LF.rust_streak(L, 619, 242, 6, seed=15)                               # relay hut door hinge
    for px_ in range(746, 1094, 58):
        LF.rust_streak(L, px_ + 1, 222, 8, seed=px_)                       # canopy post bolts
    LF.rust_streak(L, 1655, 174, 10, seed=21, strong=True)                # office chimney flashing
    for k in range(1876, 1896, 6):
        LF.rust_streak(L, k, 237, 6, seed=k)                               # buffer stop
    # drifts against walls
    LF.drift_wedge(L, 238, 256, GROUND_Y, 7, rise_left=False, seed=1)     # tea stall, left wall
    LF.drift_wedge(L, 648, 662, GROUND_Y, 5, rise_left=True, seed=2)      # relay hut, right wall
    LF.drift_wedge(L, 1464, 1478, GROUND_Y, 6, rise_left=False, seed=3)   # office, left wall
    LF.drift_wedge(L, 1684, 1700, GROUND_Y, 7, rise_left=True, seed=4)    # office, right wall
    # coal for the cabin stove between the signal box and the relay hut
    LF.coal_heap(L, 587, 17, GROUND_Y, 8, seed=5)
    # PA cable: cabin horn -> loudspeaker pole (the hooded crows perch on it)
    E['pa_wire'] = LF.pa_wire(L, PA_CABIN_ANCHOR, PA_POLE_ANCHOR, 8)
    LF.stairs_cache(L, E)


# =========================================================================== ground band
def make_ground(E, lamp_xs, warm_sources):
    """Platform, tracks, ballast, back strip.  Calm value structure: wet dark concrete, designed snow
    (drifts at edges and corners, trampled walking line), clean rail rhythm, puddles that mirror the
    bright horizon at grazing angles (back) and the dark zenith up front, light streaks in wet areas."""
    L = Layer(W, 360, 'ground')
    Y0 = 246
    rng = np.random.default_rng(77)
    nz = value_noise(W, 360, 11, seed=2, octaves=3)
    nzf = value_noise(W, 360, 4, seed=8, octaves=2)
    TH = bayer(W, 360)

    def pick(y0, y1, levels, t):
        """levels: list of (threshold, colour) ascending; ordered dither only near thresholds."""
        T = t[y0:y1]
        out = np.empty((y1 - y0, W, 4), np.uint8)
        out[:] = levels[0][1]
        for thr, col in levels[1:]:
            d = (T - thr) / 0.05 + 0.5
            m = d > TH[y0:y1]
            out[m] = col
        L.c[y0:y1] = out

    # ---- under building bases
    L.rect(0, Y0, W, GROUND_Y - Y0, NI[3], hgt=0.1)
    # ---- back strip: dark cinder path with trampled snow at the margins
    rows = np.arange(360)[:, None]
    nzb = value_noise(W, 360, 22, seed=12, octaves=2)
    t = nzb * 0.85 + nzf * 0.15
    edge_bias = np.where(rows < 252, 0.32, 0.0) + np.where(rows == 252, 0.12, 0.0)
    pick(GROUND_Y, 262, [(0, NI[3]), (0.4, ST[0]), (0.66, SN[0]), (0.74, SN[1])], t + edge_bias)
    # ---- track bed: dark ballast; snow lies between the tracks and in the cribs
    t2 = nz * 0.75 + nzf * 0.25
    between = ((rows >= 276) & (rows < 284)).astype(np.float32) * 0.22
    pick(262, PLATFORM_EDGE - 1, [(0, NI[3]), (0.36, ST[0]), (0.55, SN[0]), (0.66, SN[1]), (0.78, SN[2])],
         t2 + between)
    for _ in range(1600):          # sparse ballast stones (2x1), only on dark ballast
        x = int(rng.integers(0, W - 2))
        y = int(rng.integers(262, PLATFORM_EDGE - 1))
        cur = L.c[y, x, :3]
        if (cur == ST[0][:3]).all() or (cur == NI[3][:3]).all():
            L.rect(x, y, 2, 1, ST[1] if rng.random() < 0.7 else ST[2], hgt=0.25)
    # ---- tracks
    for (ra, rb), seed in ((RAIL2, 1), (RAIL1, 2)):
        ys0, ys1 = ra - 2, rb + 3
        r = np.random.default_rng(seed)
        off = int(r.integers(0, 12))
        for sx in range(-off, W, 12):
            x0 = sx + int(r.integers(-1, 2))
            new = r.random() < 0.12
            top, body, dark = (WO[3], WO[2], WO[1]) if new else (WO[2], WO[1], WO[0])
            L.rect(x0, ys0, 5, ys1 - ys0, body, hgt=0.35)
            L.vline(x0 + 4, ys0, ys1 - ys0, dark, 0.3)
            L.hline(x0, ys0, 5, top, 0.4)
            L.hline(x0, ys1 - 1, 5, NI[2], 0.25)
            if r.random() < 0.6:                   # snow cap on the sleeper top face
                L.hline(x0, ys0 + int(r.integers(0, 2)), 4, SN[1], 0.42)
        for ry in (ra, rb):
            L.hline(0, ry - 1, W, ST[1], 0.55)     # rail head top edge
            L.hline(0, ry, W, ST[3], 0.6)          # matte wet head
            L.hline(0, ry + 1, W, NI[1], 0.3)      # web shadow
            for x in range(W):
                n = (x * 7 + ry * 13) % 23
                if n < 3:
                    L.px(x, ry, SK[0])            # cold sky sheen (matte, sparse)
                elif n == 11:
                    L.px(x, ry - 1, ST[2])
            for x in range(W):                     # tie plates where rails cross sleepers
                if (L.c[ry + 2, x, :3] == WO[1][:3]).all() and x % 3 == 0:
                    L.px(x, ry + 2, NI[2])
    # plank crossings (route to the back strip)
    rail_rows = set()
    for (ra, rb) in (RAIL2, RAIL1):
        rail_rows |= {ra - 1, ra, ra + 1, rb - 1, rb, rb + 1}
    for cx0 in (382, 1462):
        for y in range(262, PLATFORM_EDGE - 1):
            if y in rail_rows:
                continue
            for x in range(cx0, cx0 + 26):
                L.px(x, y, WO[2] if (y // 3) % 2 else WO[1], 0.45)
            if y % 3 == 0:
                L.hline(cx0, y, 26, WO[0])
        L.vline(cx0 + 25, 262, PLATFORM_EDGE - 263, WO[3])
        L.vline(cx0, 262, PLATFORM_EDGE - 263, WO[0])
        for x in range(cx0 + 1, cx0 + 25, 3):      # trampled slush on the planks
            L.px(x, 279, SN[0])
            L.px(x + 1, 268, SN[0])
    # ---- platform edge stones + worn stripe
    L.hline(0, PLATFORM_EDGE - 1, W, NI[2], 0.3)
    L.rect(0, PLATFORM_EDGE, W, 3, ST[3], hgt=0.7)
    L.hline(0, PLATFORM_EDGE, W, ST[4], 0.75)
    for x in range(0, W, 24):
        L.vline(x, PLATFORM_EDGE, 3, ST[1])
    for x in range(W):
        if (x // 4) % 6 != 5 and nzf[PLATFORM_EDGE + 1, x] > 0.36:
            L.px(x, PLATFORM_EDGE + 1, SN[1])
    # ---- platform: wet concrete slabs (flat tones per slab, clean joints)
    for row in range(5):
        y0 = 300 + row * 12
        shift = 0 if row % 2 == 0 else 21
        for k, x0 in enumerate(range(-shift, W, 42)):
            v = r_slab(row, k)
            L.rect(x0, y0, 42, 12, [ST[1], ST[1], ST[1], ST[2], ST[0]][v], hgt=0.3)
            L.vline(x0, y0, 12, ST[0], 0.26)
        L.hline(0, y0, W, ST[0], 0.26)
    # wet sheen zones: horizontal broken sky reflections (teal)
    wet = value_noise(W, 360, 26, seed=41, octaves=2)
    for y in range(302, 360, 2):
        x = 0
        while x < W:
            if wet[y, x] > 0.6:
                ln = 3 + (x * 7 + y) % 6
                for xx in range(x, min(W, x + ln)):
                    if (L.c[y, xx, :3] == ST[1][:3]).all() or (L.c[y, xx, :3] == ST[0][:3]).all():
                        L.px(xx, y, TE[2] if y < 330 else TE[1], 0.28)
                x += ln + 2 + (x * 3 + y) % 5
            else:
                x += 3
    # designed snow: drift along the back edge of the platform, drift at the front, slush streaks
    for x in range(W):
        d_back = int(2 + 3 * nz[300, x] + 2 * nzf[301, x])
        for k in range(d_back):
            L.px(x, 300 + k, SN[2] if k < d_back - 2 else (SN[1] if k < d_back - 1 else SN[0]), 0.4)
        d_front = int(4 + 6 * nz[355, x] + 3 * nzf[350, x])
        for k in range(d_front):
            L.px(x, 359 - k, SN[1] if k > 1 else SN[0], 0.4)
            if k == d_front - 1:
                L.px(x, 359 - k, SN[2])
    for _ in range(140):                            # slush streaks (short, horizontal)
        x = int(rng.integers(0, W - 8))
        y = int(rng.integers(308, 344))
        ln = int(rng.integers(3, 9))
        L.hline(x, y, ln, SN[0], 0.32)
        if ln > 5:
            L.hline(x + 2, y - 1, ln - 4, ST[2], 0.32)
    # repairs and wear: a few broken slabs (gravel showing), asphalt patches, drain grates, a manhole
    for (bx, by_, bw, bh) in ((96, 336, 18, 7), (612, 312, 22, 8), (1132, 340, 16, 6), (1508, 314, 20, 7),
                              (1846, 326, 18, 8)):
        L.rect(bx, by_, bw, bh, ST[0], hgt=0.2)
        for _ in range(bw * bh // 4):
            L.px(bx + int(rng.integers(0, bw)), by_ + int(rng.integers(0, bh)), ST[1] if rng.random() < 0.7 else ST[2])
        L.hline(bx, by_, bw, NI[3])
        L.hline(bx, by_ + bh, bw, ST[2])
    for (ax, ay, aw_, ah) in ((330, 300, 46, 12), (880, 324, 40, 12), (1622, 336, 50, 12)):
        L.rect(ax, ay, aw_, ah, NI[3], hgt=0.28)
        for _ in range(aw_ * ah // 6):
            L.px(ax + int(rng.integers(0, aw_)), ay + int(rng.integers(0, ah)), ST[0])
        L.hline(ax, ay, aw_, ST[0])
    for gx in (470, 1260, 1720):                    # cast-iron drain grates at the platform edge
        L.rect(gx, 301, 10, 4, NI[2], hgt=0.2)
        for k in range(gx + 1, gx + 10, 2):
            L.vline(k, 301, 4, ST[2])
    mx, my = 1040, 343                               # manhole cover
    m_, mx0, my0 = L.ellipse(mx, my, 9, 3.5, NI[3], hgt=0.3)
    L.ellipse(mx, my, 7, 2.5, ST[1])
    for k in range(-6, 7, 3):
        L.px(mx + k, my, NI[3])
    L.hline(mx - 6, my - 3, 12, ST[2])
    for k in range(0, W, 10):                       # trampled walking line: footprints
        fy = 318 + int(5 * math.sin(k / 83.0))
        L.rect(k, fy, 2, 1, ST[0])
        L.rect(k + 5, fy + 2, 2, 1, ST[0])
    for _ in range(28):                             # a few short cracks
        x = int(rng.integers(0, W))
        y = int(rng.integers(304, 352))
        for k in range(int(rng.integers(3, 9))):
            L.px(x, y, ST[0])
            x += 1
            y += int(rng.integers(-1, 2))
    # ---- puddles: mirror tone depends on depth (grazing angle at the back -> bright horizon sky)
    puddles = [(140, 326, 30, 4), (305, 342, 22, 3), (520, 324, 40, 5), (690, 336, 26, 4), (960, 330, 34, 5),
               (1180, 322, 28, 4), (1320, 344, 34, 4), (1560, 330, 30, 4), (1760, 338, 40, 5), (60, 350, 24, 3),
               (860, 348, 30, 3), (1440, 352, 26, 3), (530, 256, 30, 3), (1572, 256, 26, 3), (230, 256, 18, 2),
               (1010, 280, 22, 2), (640, 280, 16, 2), (1250, 280, 18, 2), (90, 279, 14, 2)]
    for (px_, py_, rx, ry) in puddles:
        m, mx, my = L.ellipse_mask(px_, py_, rx, ry)
        hh, ww = m.shape
        sy, sx = np.mgrid[0:hh, 0:ww]
        Y = sy + my
        X = sx + mx
        back = py_ < 300
        if back:   # far: mirrors the bright low sky
            ladder = [TE[3], SK[0], SK[1], SK[2]]
            tval = 1 - (sy / max(1, hh - 1))
        else:      # near: mirrors the dark upper sky, bright rim at the far edge
            ladder = [NI[2], TE[1], TE[2], SK[0]]
            tval = np.clip(1 - sy / max(1, hh - 1) * 1.6, 0, 1) * 0.8
        T = tval * (len(ladder) - 1)
        idx = np.floor(T).astype(int)
        idx = np.clip(idx + ((T - idx) > bayer(ww, hh, mx, my)), 0, len(ladder) - 1)
        cols = np.stack(ladder)[idx]
        streak = (Y % 2 == 0) & ((X * 3 + Y) % 9 < 2)
        cols[streak] = ladder[0] if not back else ladder[1]
        L._put(m, mx, my, cols, hgt=0.05)
        for x in range(mx, mx + ww):               # dark lip at the near edge
            col = m[:, x - mx]
            if col.any():
                yb = my + int(np.nonzero(col)[0].max())
                L.px(x, yb + 1, ST[0])
    # ---- light reflections: short broken horizontal dashes stacked below each source, wet pixels only
    wet_cols = [NI[2], TE[1], TE[2], TE[3], SK[0], SK[1], SK[2]]
    wet_keys = set(int(c[0]) << 16 | int(c[1]) << 8 | int(c[2]) for c in wet_cols)
    rr = np.random.default_rng(5)
    for (lx, ly_base, col_list, strength) in warm_sources:
        for k, y in enumerate(range(ly_base, min(360, ly_base + 22), 2)):
            t = k / 11.0
            if rr.random() > strength * (1 - t * 0.8):
                continue
            half = 1 + int(rr.integers(0, 2)) + int(2 * t)
            off = int(rr.integers(-1, 2))
            for x in range(int(lx) - half + off, int(lx) + half + off + 1):
                if not (0 <= x < W):
                    continue
                c = L.c[y, x]
                key = int(c[0]) << 16 | int(c[1]) << 8 | int(c[2])
                if key in wet_keys:
                    cc = col_list[0] if t < 0.4 else col_list[1]
                    L.px(x, y, cc, em=cc)
    flat_normal(L, 0, GROUND_Y, W, 360 - GROUND_Y, UP)
    for (ra, rb) in (RAIL2, RAIL1):
        for ry in (ra, rb):
            flat_normal(L, 0, ry - 1, W, 1, (0, 0.8, 0.6))
            flat_normal(L, 0, ry + 1, W, 1, (0, -0.4, 0.9))
    flat_normal(L, 0, PLATFORM_EDGE, W, 1, (0, 0.85, 0.5))
    return L


def r_slab(row, k):
    """Deterministic slab tone pick: mostly wet (0..2), some dry (3), few dark (4)."""
    h = (row * 7919 + k * 104729 + 17) % 23
    return 3 if h < 4 else (4 if h == 9 else (h % 3))


# =========================================================================== props (y-sorted)
def prop_layer(w, h, name):
    return Layer(w, h, name)


def lamp_post(variant=0, emissive=True):
    """Platform lamp: concrete post, curved steel arm, enamel reflector shade, cold mercury bulb."""
    P = Layer(30, 84, 'lamp_post')
    bx = 8                         # post x (base centre ~ bx+2)
    by = 83
    P.rect(bx - 2, by - 5, 9, 5, ST[2], hgt=0.6)          # foot
    P.hline(bx - 2, by - 5, 9, ST[4])
    P.vline(bx + 6, by - 5, 5, ST[3])
    P.rect(bx, 12, 5, by - 16, ST[2], hgt=0.6)            # concrete post (tapers)
    P.vline(bx, 12, by - 16, ST[1])
    P.vline(bx + 4, 12, by - 16, ST[4])
    P.vline(bx + 3, 12, by - 16, ST[3])
    for yy in range(20, by - 8, 9):
        P.px(bx + 1, yy, ST[1])
    cyl_normal(P, bx, 12, 5, by - 16)
    # arm
    pts = pg.bezier([(bx + 2, 14), (bx + 4, 4), (bx + 12, 2), (bx + 18, 6)], 24)
    P.polyline([(round(a), round(b)) for a, b in pts], NI[2])
    P.polyline([(round(a), round(b) - 1) for a, b in pts], TE[3])
    # shade + bulb
    sx, sy = bx + 18, 7
    P.rect(sx - 4, sy, 9, 2, TE[1], hgt=0.8)
    P.hline(sx - 3, sy - 1, 7, TE[3])
    P.hline(sx - 5, sy + 2, 11, SN[2], 0.8)
    # bulb (lamp 2 leaves it non-emissive: the KarskLamp actor draws its flickering glow)
    P.rect(sx - 1, sy + 3, 3, 2, SN[4], hgt=0.9, em=SN[4] if emissive else None)
    P.px(sx, sy + 5, SK[5], em=SK[5] if emissive else None)
    snowline(P, sx - 3, sy - 2, 7, depth=1, cols=[SN[2], SN[3]])
    # enamel number plate + notice on the post
    P.rect(bx, 40, 5, 4, SN[2])
    P.px(bx + 2, 41, NI[2])
    if variant == 1:  # timetable change notice glued on
        P.rect(bx - 1, 50, 6, 8, SN[3])
        P.hline(bx, 52, 4, ST[2])
        P.hline(bx, 54, 3, ST[2])
    snowline(P, bx - 2, by - 6, 9, depth=1)
    return P, (bx + 2, by), (sx, sy + 4)


def wagon_c17(hist=False):
    """Two-axle covered goods wagon (Soviet type, wartime-worn) with a sliding door and the damaged
    lead seal.  Body rust-brown planking, steel frame, arched snowy roof, spoked wheels."""
    Wd, Hd = 200, 100
    P = Layer(Wd, Hd, 'wagon_c17')
    by = Hd - 1                       # rail contact (wheel bottom) row
    x0, x1 = 12, 188                  # body
    body_bot = by - 22                # underframe level
    body_top = body_bot - 62
    # underframe (solebar) + buffers + coupling
    P.rect(x0 - 4, body_bot, x1 - x0 + 8, 6, NI[2], hgt=0.6)
    P.hline(x0 - 4, body_bot, x1 - x0 + 8, ST[2])
    for rx in range(x0, x1, 9):
        P.px(rx, body_bot + 2, ST[3])                    # rivets
    for bx in (x0 - 12, x1 + 4):
        P.rect(bx, body_bot + 1, 8, 4, NI[3], hgt=0.7)
        P.rect(bx + (0 if bx < x0 else 5), body_bot - 1, 3, 8, ST[2], hgt=0.75)  # buffer heads
        P.vline(bx + (2 if bx < x0 else 7), body_bot - 1, 8, ST[4])
    P.hline(x0 - 16, body_bot + 3, 6, ST[1])
    P.px(x0 - 17, body_bot + 4, ST[1])
    # wheels (2 axles), axle boxes, leaf springs, brake blocks
    for wc in (x0 + 34, x1 - 34):
        cy = by - 9
        m, mx, my = P.ellipse(wc, cy, 9.5, 9.5, NI[2], hgt=0.55)
        P.ellipse(wc, cy, 8, 8, NI[1], hgt=0.45)
        P.ellipse(wc, cy, 2.5, 2.5, ST[2], hgt=0.7)
        for a in range(0, 360, 40):                       # spokes
            ex = wc + math.cos(math.radians(a)) * 7
            ey = cy + math.sin(math.radians(a)) * 7
            P.line(wc, cy, ex, ey, NI[3])
        for a in range(-60, 61, 12):                      # rim highlight (right side, rim light)
            P.px(wc + int(round(math.cos(math.radians(a)) * 9)), cy + int(round(math.sin(math.radians(a)) * 9)),
                 ST[3])
        P.rect(wc - 5, body_bot + 5, 11, 5, NI[3], hgt=0.6)   # axle box
        P.hline(wc - 5, body_bot + 5, 11, ST[2])
        for k in range(4):                                # leaf spring
            P.hline(wc - 12 + k, body_bot + 6 + k, 24 - 2 * k, ST[1] if k % 2 else NI[2])
        P.rect(wc + 9, cy - 4, 2, 7, RU[1])                # brake block (rusty)
    # body planking (vertical boards), rust-brown paint, weathered
    for xx in range(x0, x1):
        col = RU[1] if (xx - x0) % 4 else RU[0]
        P.rect(xx, body_top, 1, body_bot - body_top, col, hgt=0.5 if col is RU[1] else 0.44)
    rng = np.random.default_rng(17)
    for _ in range(160):                                  # faded paint / bare wood flecks
        fx = int(rng.integers(x0, x1 - 1))
        fy = int(rng.integers(body_top + 2, body_bot - 2))
        P.rect(fx, fy, 1, int(rng.integers(1, 4)), [RU[2], WO[2], RU[0]][int(rng.integers(0, 3))])
    # steel frame: corner posts, diagonal braces, top/bottom chord
    P.rect(x0, body_top, x1 - x0, 3, NI[3], hgt=0.65)
    P.rect(x0, body_bot - 4, x1 - x0, 4, NI[3], hgt=0.65)
    P.hline(x0, body_bot - 4, x1 - x0, ST[1])
    for px_ in (x0, x0 + 44, x1 - 48, x1 - 4):
        P.rect(px_, body_top, 4, body_bot - body_top, NI[3], hgt=0.66)
        P.vline(px_ + 3, body_top, body_bot - body_top, ST[2])
    for (ax, bx2) in ((x0 + 4, x0 + 44), (x1 - 44, x1 - 4)):
        P.line(ax, body_bot - 5, bx2 - 1, body_top + 3, NI[3])
        P.line(ax + 1, body_bot - 5, bx2, body_top + 3, NI[3])
        P.line(ax + 2, body_bot - 5, bx2 + 1, body_top + 3, ST[1])
    # sliding door (centre) with rails, handle bar, hasp + damaged LEAD SEAL
    dx0, dx1 = 78, 124
    P.rect(dx0 - 2, body_top + 2, 2, body_bot - body_top - 6, NI[2])
    for xx in range(dx0, dx1):
        col = RU[2] if (xx - dx0) % 4 else RU[1]
        P.rect(xx, body_top + 4, 1, body_bot - body_top - 9, col, hgt=0.56)
    P.rect(dx0, body_top + 4, dx1 - dx0, 2, NI[3])
    P.rect(dx0, body_bot - 7, dx1 - dx0, 2, NI[3])
    P.line(dx0 + 2, body_bot - 8, dx1 - 3, body_top + 7, NI[3])
    P.vline(dx1 - 1, body_top + 4, body_bot - body_top - 9, RU[3])
    P.rect(dx0 - 4, body_top - 1, dx1 - dx0 + 10, 2, NI[2])          # top door rail
    P.rect(dx0 - 4, body_bot - 5, dx1 - dx0 + 10, 2, NI[2])          # bottom door rail
    hy = body_top + 40
    P.rect(dx1 - 6, hy - 6, 2, 14, ST[3], hgt=0.75)                   # handle bar
    P.vline(dx1 - 5, hy - 6, 14, ST[4])
    P.rect(dx1 - 3, hy - 1, 6, 3, NI[2], hgt=0.75)                    # hasp
    seal = (dx1 + 3, hy + 3)
    P.px(dx1 + 1, hy + 2, ST[3])                                      # seal wire
    P.px(dx1 + 2, hy + 3, ST[3])
    P.rect(dx1 + 2, hy + 4, 4, 3, ST[4], hgt=0.85)                    # lead seal (dented, scratched)
    P.px(dx1 + 2, hy + 4, SN[3])
    P.px(dx1 + 3, hy + 4, SN[2])
    P.px(dx1 + 5, hy + 6, ST[2])
    P.px(dx1 + 4, hy + 5, ST[3])
    P.px(dx1 + 6, hy + 5, ST[3])                                      # dangling wire end
    # replaced boards (lighter, fresh) + nail rows: the wagon has been patched more than once
    for bx in (x0 + 52, x0 + 56, x1 - 40, x1 - 14):
        P.rect(bx, body_top + 3, 3, body_bot - body_top - 7, RU[2], hgt=0.52)
        P.vline(bx + 3, body_top + 3, body_bot - body_top - 7, RU[0])
        for ny in (body_top + 8, body_bot - 10):
            P.px(bx + 1, ny, ST[3])
    # chalk marks + stencil number on the body (tiny, scribbled)
    text(P, x0 + 8, body_top + 15, '24-311', SN[1], font='s')
    for k in range(6):
        P.px(x0 + 9 + k * 2, body_top + 22, SN[0])
    P.line(x1 - 40, body_top + 10, x1 - 28, body_top + 18, SN[2])    # chalk tick
    P.line(x1 - 28, body_top + 18, x1 - 22, body_top + 8, SN[2])
    text(P, x1 - 42, body_top + 24, '20T', SN[1], font='s')
    # old state stencil on the sliding door (weathered paint; §12.4 neutral gear-and-wheat / hist hammer & sickle)
    sk = EMB.kind_for('gw11', hist)
    EMB.paint(P, dx0 + 6, body_top + 9, sk, SN[1], wear=0.2, seed=24311)
    P.hline(dx0 + 4, body_top + 22, 15, SN[0])                       # faded stencil line under it
    P.rect(dx0 + 5, body_top + 22, 2, 1, RU[2])
    stencil_xy = (dx0 + 6, body_top + 9)
    # chalk marks at the FAR (right) end (exp_wagon_chalk): tally groups, an arrow, a crossed-out mark
    cx_, cy_ = x1 - 19, body_top + 30
    for g in range(3):
        n = 5 if g < 2 else 3
        gx = cx_ + (g % 2) * 9
        gy = cy_ + (g // 2) * 8
        for k in range(min(n, 4)):                     # strokes 2 px apart (readable at 1:1)
            P.vline(gx + 2 * k, gy, 5, SN[2] if g == 0 else SN[1])
        if n == 5:
            P.line(gx - 1, gy + 4, gx + 7, gy, SN[2])   # the fifth stroke across
    P.vline(cx_ + 3, cy_ + 18, 7, SN[1])                              # arrow pointing down (to the floor)
    P.px(cx_ + 2, cy_ + 23, SN[1])
    P.px(cx_ + 4, cy_ + 23, SN[1])
    P.line(cx_ + 7, cy_ + 18, cx_ + 11, cy_ + 22, SN[0])              # crossed-out mark
    P.line(cx_ + 11, cy_ + 18, cx_ + 7, cy_ + 22, SN[0])
    chalk_xy = (cx_ + 4, cy_ + 8)
    # small vent hatches
    for vx in (x0 + 22, x1 - 30):
        P.rect(vx, body_top + 6, 10, 6, NI[2], hgt=0.4)
        P.hline(vx, body_top + 6, 10, ST[2])
        for k in range(vx + 1, vx + 10, 2):
            P.vline(k, body_top + 7, 4, NI[1])
    # roof: shallow arch, snow covered
    for k in range(6):
        inset = [3, 1, 0, 0, 0, 0][k]
        P.hline(x0 - 2 + inset, body_top - 1 - k, x1 - x0 + 4 - 2 * inset, NI[3] if k < 2 else SN[2], 0.7 + k * 0.03)
    P.hline(x0, body_top - 6, x1 - x0, SN[3], 0.8)
    P.hline(x0 + 2, body_top - 7, x1 - x0 - 4, SN[4], 0.8)
    for xx in range(x0, x1):                               # snow overhang drips
        if (xx * 7) % 13 < 3:
            P.px(xx, body_top - 1, SN[2])
            if (xx * 3) % 7 == 0:
                P.px(xx, body_top, SN[1])
    # rim light: right edges (sun back-right)
    for yy in range(body_top, body_bot):
        P.px(x1 - 1, yy, RU[4] if yy % 2 else RU[3])
    P.vline(x1, body_top - 6, 6, SN[4])
    # rust streaks downwards from the frame / rivets
    stains(P, x0, body_top + 3, x1 - x0, body_bot - body_top - 8, [RU[0], RU[1], RU[2]], seed=5,
           density=0.25, length=(4, 18))
    # grime at the bottom of the body
    for xx in range(x0, x1):
        for yy in range(body_bot - 10, body_bot - 4):
            if (xx + yy) % 3 == 0 and rng.random() < 0.5:
                P.px(xx, yy, RU[0])
    return P, seal, by, {'stencil': stencil_xy, 'stencil_kind': sk, 'chalk': chalk_xy}


def flatcar_panels():
    """Two-axle flatcar loaded with prefab concrete wall panels (reconstruction material)."""
    Wd, Hd = 196, 62
    P = Layer(Wd, Hd, 'flatcar_panels')
    by = Hd - 1
    x0, x1 = 12, 184
    deck = by - 20
    P.rect(x0, deck, x1 - x0, 5, NI[3], hgt=0.6)
    P.hline(x0, deck, x1 - x0, WO[3])
    P.hline(x0, deck + 1, x1 - x0, WO[2])
    for k in range(x0 + 6, x1, 16):                    # stakes
        P.rect(k, deck - 8, 2, 8, NI[2], hgt=0.66)
        P.px(k + 1, deck - 8, ST[3])
    for bx in (x0 - 9, x1 + 2):
        P.rect(bx, deck + 1, 7, 3, NI[3])
        P.rect(bx + (0 if bx < x0 else 4), deck - 1, 3, 6, ST[2])
    for wc in (x0 + 30, x1 - 30):
        cy = by - 9
        P.ellipse(wc, cy, 9.5, 9.5, NI[2], hgt=0.55)
        P.ellipse(wc, cy, 8, 8, NI[1], hgt=0.45)
        P.ellipse(wc, cy, 2.5, 2.5, ST[2])
        for a in range(0, 360, 40):
            P.line(wc, cy, wc + math.cos(math.radians(a)) * 7, cy + math.sin(math.radians(a)) * 7, NI[3])
        for a in range(-60, 61, 12):
            P.px(wc + int(round(math.cos(math.radians(a)) * 9)), cy + int(round(math.sin(math.radians(a)) * 9)), ST[3])
        P.rect(wc - 5, deck + 5, 11, 5, NI[3])
        for k in range(4):
            P.hline(wc - 12 + k, deck + 6 + k, 24 - 2 * k, ST[1] if k % 2 else NI[2])
    # stacked panels (3 panels with window openings), snow on top
    for i, (px0, pw, ph) in enumerate(((x0 + 6, 76, 24), (x0 + 88, 74, 26), (x0 + 30, 60, 8))):
        pyb = deck if i < 2 else deck - 26
        P.rect(px0, pyb - ph, pw, ph, ST[3], hgt=0.6)
        P.hline(px0, pyb - ph, pw, ST[4])
        P.vline(px0 + pw - 1, pyb - ph, ph, ST[5])
        P.vline(px0, pyb - ph, ph, ST[2])
        if ph > 12:
            for k in range(2):
                wx = px0 + 10 + k * (pw // 2)
                P.rect(wx, pyb - ph + 6, 14, 12, NI[2], hgt=0.25)
                P.hline(wx, pyb - ph + 6, 14, NI[3])
        snowline(P, px0, pyb - ph, pw, depth=2, seed=i)
        for yy in range(pyb - ph + 2, pyb, 4):
            P.px(px0 + 3, yy, ST[2])
    P.line(x0 + 4, deck - 1, x0 + 50, deck - 34, NI[2])   # tie-down wire
    P.line(x1 - 6, deck - 1, x1 - 60, deck - 34, NI[2])
    return P, by


def fire_barrel_workers():
    """Two workers warming their hands at a fire barrel (obs_stove).  The barrel holes and flame core
    are emissive; warm light catches the workers' facing edges."""
    P = Layer(64, 52, 'fire_barrel')
    by = 51
    bx, bw, bh = 25, 14, 18
    # barrel
    for xx in range(bx, bx + bw):
        u = (xx - bx + 0.5) / bw
        c = RU[1] if u < 0.25 else (RU[2] if u < 0.7 else RU[3])
        P.rect(xx, by - bh, 1, bh, c, hgt=0.5)
    P.vline(bx + bw - 1, by - bh, bh, RU[4])
    for ry in (by - bh + 4, by - 6):
        P.hline(bx, ry, bw, RU[0])
    cyl_normal(P, bx, by - bh, bw, bh)
    for (hx_, hy_) in ((bx + 4, by - 10), (bx + 9, by - 12), (bx + 6, by - 4), (bx + 11, by - 5)):
        P.rect(hx_, hy_, 2, 2, CO[3], em=CO[3])
        P.px(hx_, hy_ + 1, CO[2], em=CO[2])
    P.rect(bx - 1, by - bh - 1, bw + 2, 2, RU[0], hgt=0.6)
    # glowing embers just above the rim (the flame tongues are the animated fx strip 'barrel_flames')
    for k in range(bw - 2):
        c = CO[3] if k % 3 else CO[2]
        P.px(bx + 1 + k, by - bh - 2, c, 0.9, em=c)
    for k in range(2, bw - 3, 3):
        P.px(bx + k, by - bh - 3, CO[2], 0.9, em=CO[2])
    # two workers (padded jackets, ushankas), warm edge facing the barrel
    w1 = figure(45, [NI[3], TE[1], TE[2]], hat='shapka', hat_col=NI[2], rim=TE[3], warm=('r', CO[2]),
                arms='forward', seed=3, trousers=NI[2], boots=NI[0], skin=RU[3], scarf=ST[2])
    w2 = figure(44, [WO[0], WO[1], WO[2]], hat='shapka', hat_col=NI[3], rim=None, warm=('l', CO[2]),
                arms='forward', seed=4, trousers=NI[2], boots=NI[0], skin=RU[3], facing='front')
    P.blit(w1, bx - w1.w + 3, by - w1.h + 1)
    P.blit(w2, bx + bw - 3, by - w2.h + 1)
    # trampled, melted snow ring at the foot (wet, dark) -- the dynamic light warms it
    for k in range(-16, 17):
        P.px(bx + bw // 2 + k, by, NI[3] if abs(k) < 12 else ST[0])
    return P, (bx + bw // 2, by - bh - 4), by


def timetable_board():
    """Fahrplantafel on two posts with a small roof: worn board, three re-booked lines marked with
    tiny square / circle / triangle (world-scale hint; detail lives in the inspect document)."""
    P = Layer(44, 58, 'timetable_board')
    by = 57
    for px_ in (6, 36):
        P.rect(px_, 10, 3, by - 10, WO[1], hgt=0.6)
        P.vline(px_ + 2, 10, by - 10, WO[3])
    P.rect(2, 4, 40, 4, NI[3], hgt=0.8)                  # little roof
    P.hline(2, 4, 40, TE[1])
    snowline(P, 2, 2, 40, depth=2)
    P.rect(3, 9, 38, 28, WO[2], hgt=0.6)                 # frame
    P.vline(40, 9, 28, WO[4])
    P.rect(5, 11, 34, 24, TE[0], hgt=0.5)                # board face (dark enamel)
    text(P, 7, 12, 'ОТПР', SN[2])
    for i, yy in enumerate(range(19, 34, 3)):            # timetable rows (scribble)
        P.hline(7, yy, 18 - (i % 3) * 3, SN[1])
        P.hline(27, yy, 10, SN[0])
    # the three re-booked lines: pasted slips with symbols
    for i, (yy, sym) in enumerate(((22, 'sq'), (25, 'ci'), (28, 'tr'))):
        P.rect(27, yy - 1, 11, 3, SN[3])
        sx = 36
        if sym == 'sq':
            P.rect(sx - 1, yy - 1, 2, 2, NI[2])
        elif sym == 'ci':
            P.px(sx - 1, yy - 1, NI[2])
            P.px(sx, yy, NI[2])
            P.px(sx - 1, yy + 1, NI[2])
            P.px(sx - 2, yy, NI[2])
        else:
            P.px(sx - 1, yy - 1, NI[2])
            P.hline(sx - 2, yy + 1, 3, NI[2])
    P.rect(5, 11, 3, 3, SN[0])                           # peeled corner
    # a paper notice pinned below
    P.rect(14, 38, 12, 9, SN[2], hgt=0.55)
    P.hline(15, 40, 9, ST[2])
    P.hline(15, 42, 7, ST[2])
    P.hline(15, 44, 8, ST[2])
    P.vline(40, 9, 28, WO[4])
    snowline(P, 3, 36, 38, depth=1, cols=[SN[1], SN[2]])
    return P, by


def teaching_board():
    """'Übungskasten': disconnected, unpowered TEACHING board in an open steel cabinet on a post.
    Three empty card slots + a tiny fictional demonstration diagram; stencil УЧЕБНЫЙ (training),
    cut cable end hanging below (clearly not connected to anything)."""
    P = Layer(46, 64, 'teaching_board')
    by = 63
    P.rect(19, 30, 5, by - 30, ST[2], hgt=0.6)          # post
    P.vline(23, 30, by - 30, ST[4])
    P.vline(19, 30, by - 30, ST[1])
    P.rect(16, by - 4, 11, 4, ST[2])
    P.hline(16, by - 4, 11, ST[4])
    # cabinet body
    cx0, cy0, cw, ch = 6, 4, 30, 28
    P.rect(cx0, cy0, cw, ch, TE[1], hgt=0.6)
    P.vline(cx0 + cw - 1, cy0, ch, TE[4])
    P.hline(cx0, cy0, cw, TE[3])
    P.rect(cx0 + 2, cy0 + 2, cw - 4, ch - 4, ST[3], hgt=0.45)     # inner panel (pale grey)
    # demonstration diagram (fictional): three boxes joined by a line, arrow
    P.hline(cx0 + 4, cy0 + 6, 20, NI[3])
    for k, sx in enumerate((cx0 + 4, cx0 + 12, cx0 + 20)):
        P.rect(sx, cy0 + 4, 4, 4, SN[3])
        P.rect(sx + 1, cy0 + 5, 2, 2, NI[3])
    P.px(cx0 + 25, cy0 + 5, NI[3])
    P.px(cx0 + 25, cy0 + 7, NI[3])
    # three empty card slots
    for k in range(3):
        sx = cx0 + 4 + k * 8
        P.rect(sx, cy0 + 12, 6, 8, NI[2], hgt=0.25)
        P.hline(sx, cy0 + 12, 6, NI[1])
        P.hline(sx, cy0 + 20, 6, ST[4])
    # stencil plate
    P.rect(cx0 + 2, cy0 + ch - 6, cw - 4, 4, TE[0])
    for k in range(cx0 + 4, cx0 + cw - 4, 2):
        P.px(k, cy0 + ch - 4, SN[1])
    # open door swung to the left (seen almost edge-on)
    P.rect(0, cy0 + 1, 6, ch - 2, TE[2], hgt=0.62)
    P.vline(0, cy0 + 1, ch - 2, TE[1])
    P.vline(5, cy0 + 1, ch - 2, TE[3])
    P.px(2, cy0 + ch // 2, ST[4])
    # roof hood + snow
    P.rect(cx0 - 2, cy0 - 3, cw + 4, 3, NI[3], hgt=0.7)
    snowline(P, cx0 - 2, cy0 - 5, cw + 4, depth=2)
    # cut cable dangling (no power)
    P.vline(cx0 + 20, cy0 + ch, 9, NI[2])
    P.px(cx0 + 21, cy0 + ch + 9, NI[2])
    P.px(cx0 + 21, cy0 + ch + 10, RU[3])
    P.px(cx0 + 20, cy0 + ch + 10, ST[4])
    # paper label 'УЧЕБНЫЙ' on the post
    P.rect(15, 36, 13, 7, SN[3])
    for k in range(16, 27, 2):
        P.px(k, 39, ST[1])
    return P, by


def family_bundles():
    """Family waiting with bundles (obs_family): mother (43 px), child (30 px) holding her coat,
    grandfather seated on a wooden trunk, cloth bundles and a suitcase."""
    P = Layer(72, 50, 'family')
    by = 49
    # trunk + grandfather seated
    P.rect(4, by - 12, 22, 12, WO[2], hgt=0.6)
    P.hline(4, by - 12, 22, WO[4])
    P.rect(4, by - 7, 22, 2, WO[1])
    P.vline(25, by - 12, 12, WO[3])
    P.rect(13, by - 10, 3, 3, ST[3])
    g = figure(40, [ST[1], ST[2], ST[3]], hat='cap', hat_col=NI[3], rim=SK[1], seed=11, coat_len=0.66,
               trousers=NI[3], boots=NI[1], skin=RU[3], scarf=SN[1])
    # seated: take upper 60 % of the figure, place on the trunk
    cut = int(g.h * 0.58)
    for yy in range(cut):
        for xx in range(g.w):
            c = g.c[yy, xx]
            if c[3]:
                P.px(4 + xx - 1, by - 12 - cut + yy + 2, c, 0.6)
    P.rect(8, by - 12, 4, 10, NI[3])                     # knees / legs hanging
    P.rect(16, by - 12, 4, 10, NI[3])
    P.rect(7, by - 2, 5, 2, NI[1])
    P.rect(16, by - 2, 5, 2, NI[1])
    # mother
    m = figure(43, [TE[0], TE[1], TE[2]], hat='scarf', hat_col=SN[2], rim=SK[2], seed=12, coat_len=0.78,
               trousers=NI[2], boots=NI[1], skin=RU[4], arms='down')
    P.blit(m, 30, by - m.h + 1)
    # child holding mother's coat
    c = figure(29, [RU[0], RU[1], RU[2]], hat='shapka', hat_col=SN[1], rim=SK[2], seed=13, coat_len=0.66,
               trousers=NI[2], boots=NI[1], skin=RU[4], scarf=RED[1])
    P.blit(c, 48, by - c.h + 1)
    # bundles (uzly): knotted cloth, a suitcase
    for (bx, bw_, bh_, cols) in ((52, 12, 9, (SA[0], SA[1], SA[2])), (60, 10, 7, (RU[1], RU[2], RU[3]))):
        P.ellipse(bx + bw_ / 2, by - bh_ / 2, bw_ / 2, bh_ / 2, cols[1], hgt=0.55)
        P.ellipse(bx + bw_ / 2 + 1, by - bh_ / 2 - 1, bw_ / 2 - 2, bh_ / 2 - 2, cols[2])
        P.px(int(bx + bw_ / 2), int(by - bh_) - 1, cols[0])
        P.px(int(bx + bw_ / 2) + 1, int(by - bh_) - 2, cols[0])
    P.rect(26, by - 8, 12, 8, WO[1], hgt=0.6)          # suitcase
    P.hline(26, by - 8, 12, WO[3])
    P.vline(37, by - 8, 8, WO[3])
    P.rect(30, by - 10, 4, 2, NI[2])
    snowline(P, 26, by - 9, 12, depth=1, cols=[SN[1], SN[2]])
    return P, by


def crates_stack(seed=0):
    P = Layer(40, 34, 'crates')
    by = 33
    rng = np.random.default_rng(seed)
    boxes = [(2, by - 12, 16, 12), (18, by - 14, 18, 14), (8, by - 24, 16, 12)]
    for (x, y, w, h) in boxes:
        P.rect(x, y, w, h, WO[2], hgt=0.55)
        P.rect(x, y, w, 1, WO[4])
        P.vline(x + w - 1, y, h, WO[3])
        P.vline(x, y, h, WO[1])
        P.hline(x, y + h // 2, w, WO[1])
        P.line(x + 1, y + 1, x + w - 2, y + h - 2, WO[1])
        text(P, x + 3, y + 3, 'Г-' + str(int(rng.integers(1, 9))), WO[0], font='s')
        snowline(P, x, y - 1, w, depth=2, seed=x)
    return P, by


def bench():
    P = Layer(36, 16, 'bench')
    by = 15
    P.rect(1, 6, 34, 3, WO[2], hgt=0.6)
    P.hline(1, 6, 34, WO[4])
    P.rect(1, 1, 34, 2, WO[2], hgt=0.6)
    P.hline(1, 1, 34, WO[3])
    for lx in (3, 31):
        P.rect(lx, 9, 2, 6, NI[2])
        P.vline(lx, 1, 8, NI[2])
    snowline(P, 1, 5, 34, depth=1, cols=[SN[2], SN[3]])
    return P, by


# =========================================================================== foreground frame (1.3)
def make_fg():
    """Near-black framing silhouettes: wrecked 1940s truck at the left edge, low broken fence
    fragments with sagging barbed wire, dead grass, bare tree at the far right.
    Width >= 640 + 1.3 * 1280 = 2304.  Everything except the two edge framers stays below y ~322 so
    actors on the platform are only crossed by grass tips."""
    Wf = 2312
    L = Layer(Wf, 360, 'fg_frame')
    K0, K1, K2 = NI[0], NI[1], NI[2]
    rim = TE[1]
    snow = [TE[0], TE[1], TE[2]]
    rng = np.random.default_rng(5)
    tb = 360
    wrecked_truck(L, K0, K1, K2, TE[2], [TE[1], TE[2], TE[3]])
    # ---- low broken fence fragments (concrete posts, leaning; sagging barbed wire)
    frags = [(420, [0, 44, 90]), (1010, [0, 46]), (1530, [0, 42, 86, 128]), (2010, [0, 48])]
    for fx0, offs in frags:
        tops = []
        for j, o in enumerate(offs):
            px_ = fx0 + o
            h = 32 + ((px_ * 7) % 13)
            lean = [0, 1, -1, 2][(px_ // 7) % 4]
            for k in range(h):
                xx = px_ + (lean * k) // h
                L.rect(xx, tb - k, 5, 1, K0, hgt=0.6)
                L.px(xx + 4, tb - k, rim)
            if (px_ // 3) % 3 == 0:            # broken top
                L.rect(px_ + lean, tb - h, 2, 2, CLEAR)
            tops.append((px_ + 2 + lean, tb - h))
            snowline(L, px_ + lean, tb - h, 5, depth=1, cols=snow)
        for a, b in zip(tops[:-1], tops[1:]):
            for dy, sag in ((6, 9), (15, 6)):
                pts = pg.catenary(a[0], a[1] + dy, b[0], b[1] + dy, sag)
                for jj, (x, y) in enumerate(pts):
                    L.px(round(x), round(y), K1)
                    if jj % 9 == 0:
                        L.px(round(x) - 1, round(y) - 1, K1)
                        L.px(round(x) + 1, round(y) + 1, K1)
        # loose wire end hanging from the last post
        lx, ly = tops[-1]
        for k in range(14):
            L.px(lx + 3 + k, ly + 8 + int(k * k * 0.08), K1)
    # ---- dead grass: low base everywhere + tall tufts clustered at posts and the truck
    for x in range(-4, Wf):
        if rng.random() < 0.6:
            h = int(rng.integers(3, 12))
            lean = int(rng.choice([-1, 0, 1]))
            for k in range(h):
                L.px(x + lean * (k // 4), tb - 1 - k, K0 if k < h - 2 else K1, 0.3)
    clusters = [150, 420, 510, 1010, 1056, 1530, 1660, 2010, 2058, 2240]
    for cx in clusters:
        for _ in range(26):
            x = int(cx + rng.normal(0, 14))
            h = int(rng.integers(10, 26))
            lean = rng.uniform(-0.35, 0.35)
            for k in range(h):
                xx = int(round(x + lean * k * (k / h)))
                L.px(xx, tb - 1 - k, K0 if k < h * 0.7 else K1, 0.3)
            if rng.random() < 0.3:             # seed head
                L.px(int(round(x + lean * h)), tb - h - 1, K1)
    for x in range(0, Wf, 3):
        hh = int(5 + 3 * math.sin(x / 23.0) + 2 * math.sin(x / 7.0))
        L.rect(x, tb - max(1, hh), 3, max(1, hh), K0)
    # snow lumps on the ground strip (dim, in shadow)
    for x in range(0, Wf, 2):
        if math.sin(x / 31.0) + math.sin(x / 11.3) > 1.1:
            L.px(x, tb - int(4 + 2 * math.sin(x / 5.0)), TE[1])
    # ---- bare tree at the far right (frames the end of the yard; trunk at screen ~606 for cam 1280)
    bare_fg_tree(L, 2272, tb, 262, K0, rim, seed=9)
    return L


def wrecked_truck(L, K0, K1, K2, rim, snow, shift=-82):
    """1940s 1.5 t truck, abandoned at the left edge: side view facing right, no tyres, bent bed.
    Drawn on a scratch layer and blitted with x shift so only cab + hood frame the edge at cam 0 and the
    spawn (x 120) stays clear."""
    T = Layer(260, 360, 'truck')
    _truck_draw(T, K0, K1, K2, rim, snow, ox=60)
    L.blit(T, shift - 60, 0)


def _truck_draw(L0, K0, K1, K2, rim, snow, ox=0):
    L = _Shift(L0, ox)
    tb = 360
    # chassis rail + rear bed (planks, broken side board)
    L.rect(-40, 316, 190, 6, K1, hgt=0.5)
    L.hline(-40, 316, 190, K2)
    L.poly([(-40, 288), (58, 291), (60, 316), (-40, 316)], K0, hgt=0.55)
    for k in range(-36, 58, 7):
        L.vline(k, 292, 23, K1)
    L.hline(-40, 288, 98, K2)
    L.line(-40, 287, 58, 290, rim)
    L.poly([(30, 276), (56, 268), (58, 290), (34, 290)], K1)         # side board sprung loose
    L.line(30, 276, 56, 268, rim)
    # cab: boxy, slanted windscreen, empty window, collapsed door
    cab = [(60, 316), (60, 252), (64, 246), (90, 246), (100, 262), (103, 316)]
    L.poly(cab, K0, hgt=0.6)
    L.poly([(66, 254), (86, 254), (94, 270), (66, 270)], K2, hgt=0.3)  # window hole
    L.line(70, 256, 90, 268, K0)                                       # bent frame strut
    L.rect(64, 276, 30, 2, K1)
    L.line(60, 251, 64, 246, rim)
    L.line(64, 246, 90, 246, rim)
    L.line(90, 246, 100, 262, rim)
    L.vline(102, 262, 54, rim)
    # hood with louvres + radiator grille + bumper
    L.poly([(100, 262), (140, 266), (146, 274), (146, 316), (100, 316)], K0, hgt=0.6)
    for k in range(108, 136, 5):
        L.vline(k, 274, 12, K1)
    L.line(100, 262, 140, 266, rim)
    L.line(140, 266, 146, 274, rim)
    L.rect(146, 270, 6, 46, K1, hgt=0.65)
    for k in range(272, 314, 3):
        L.hline(147, k, 4, K0)
    L.vline(151, 270, 46, rim)
    L.rect(144, 314, 14, 4, K1)
    # front fender arch over the (missing) wheel, rims sunk in snow and grass
    L.poly([(96, 318), (104, 300), (118, 294), (134, 296), (148, 306), (152, 318)], K0, hgt=0.62)
    L.line(104, 300, 118, 294, rim)
    L.line(118, 294, 134, 296, rim)
    for (wx, wy) in ((124, 332), (14, 334)):      # bare rims (tyres long gone)
        L.ellipse(wx, wy, 17, 17, K0, hgt=0.6)
        L.ellipse(wx, wy, 12, 12, K1)
        L.ellipse(wx, wy, 10, 10, K0)
        L.ellipse(wx, wy, 3, 3, K2)
        for a in range(-80, 30, 10):
            L.px(wx + int(round(math.cos(math.radians(a)) * 12)), wy + int(round(math.sin(math.radians(a)) * 12)), rim)
    for (hx, hy, hw) in ((104, 268, 30), (66, 280, 26)):   # faint rust bloom on hood and door (dark)
        for k in range(hw):
            if (k * 7) % 5 < 3:
                L.px(hx + k, hy + (k % 3), RU[0])
    L.ellipse(147, 296, 3, 3, K1)                                      # dead headlamp
    L.px(148, 295, rim)
    L.rect(-40, 330, 200, 30, K0, hgt=0.3)                             # sunk in drift
    # dim snow on top surfaces (in shadow, so teal-dark, not white)
    snowline(L0, -40 + ox, 286, 98, depth=2, cols=snow)
    snowline(L0, 64 + ox, 244, 26, depth=2, cols=snow)
    snowline(L0, 104 + ox, 262, 36, depth=2, cols=snow)
    snowline(L0, 106 + ox, 292, 26, depth=1, cols=snow)
    for x in range(-40, 160):
        hh = int(8 + 3 * math.sin(x / 9.0) + 2 * math.sin(x / 3.1))
        L.rect(x, 330 - hh // 2, 1, 2, TE[0])


class _Shift:
    """Draw proxy that offsets x by dx (keeps the truck drawing code in its own coordinates)."""
    def __init__(self, L, dx):
        self.L, self.dx = L, dx

    def rect(self, x, y, w, h, col, hgt=None, em=None):
        self.L.rect(x + self.dx, y, w, h, col, hgt, em)

    def poly(self, pts, col, hgt=None, em=None):
        return self.L.poly([(a + self.dx, b) for a, b in pts], col, hgt, em)

    def line(self, x0, y0, x1, y1, col, hgt=None, em=None):
        self.L.line(x0 + self.dx, y0, x1 + self.dx, y1, col, hgt, em)

    def vline(self, x, y, h, col, hgt=None):
        self.L.vline(x + self.dx, y, h, col, hgt)

    def hline(self, x, y, w, col, hgt=None):
        self.L.hline(x + self.dx, y, w, col, hgt)

    def px(self, x, y, col, hgt=None, em=None):
        self.L.px(x + self.dx, y, col, hgt, em)

    def ellipse(self, cx, cy, rx, ry, col, hgt=None, em=None):
        return self.L.ellipse(cx + self.dx, cy, rx, ry, col, hgt, em)

    @property
    def nrm(self):
        return self.L.nrm

    @property
    def c(self):
        return self.L.c

    @property
    def w(self):
        return self.L.w

    @property
    def h(self):
        return self.L.h


def bare_fg_tree(L, x, base, h, col, rim, seed=0):
    """Near-black bare tree; crown leans up-left and out of frame, never below y 196 on the left."""
    rng = np.random.default_rng(seed)
    th = int(h * 0.62)
    for k in range(th):
        w = int(15 - k * 0.07)
        xx = x + int(math.sin(k / 36.0) * 5)
        L.rect(xx - w // 2, base - k, max(4, w), 1, col, hgt=0.6)
        L.px(xx + max(4, w) // 2 - 1, base - k, rim if k % 3 else NI[1])
    for k in range(10):                          # root flare
        L.hline(x - 10 - k, base - k // 3, 6, col)
        L.hline(x + 6 + k, base - k // 3, 6, col)

    def branch(x0, y0, ang, ln, w, depth):
        steps = max(2, int(ln / 5))
        cx, cy = x0, y0
        for i in range(steps):
            ang += rng.uniform(-0.16, 0.16)
            nx = cx + math.cos(ang) * ln / steps
            ny = cy - math.sin(ang) * ln / steps
            if ny > 196 and nx < x - 30:          # keep the crown off the playfield on the left
                ang = max(ang, math.pi * 0.55)
                ny = cy - abs(math.sin(ang)) * ln / steps
            for t in range(max(1, int(round(w)))):
                L.line(cx + t, cy, nx + t, ny, col, 0.5)
            cx, cy = nx, ny
            if depth > 0 and rng.random() < 0.42:
                branch(cx, cy, ang + rng.choice([-1, 1]) * rng.uniform(0.3, 0.8), ln * rng.uniform(0.3, 0.55),
                       max(1, w * 0.55), depth - 1)
        if depth > 0:
            branch(cx, cy, ang + rng.uniform(-0.3, 0.3), ln * 0.55, max(1, w * 0.65), depth - 1)

    ty = base - th
    branch(x, ty, math.pi * 0.58, h * 0.42, 6, 4)
    branch(x + 2, ty + 14, math.pi * 0.78, h * 0.4, 4, 4)
    branch(x + 4, ty + 4, math.pi * 0.36, h * 0.3, 4, 3)
    branch(x - 2, ty + 40, math.pi * 0.7, h * 0.22, 3, 3)
