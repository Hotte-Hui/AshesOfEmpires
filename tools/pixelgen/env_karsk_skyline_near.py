"""env_karsk_skyline_near -- near background plane (parallax 0.72, 7.6 px/m, base y 249) of the Karsk skyline.

Seen mostly above the yard fences (y ~214) and the playfield buildings:
    4-160     two-storey timber residential barrack (exp_barrack): plank siding, carved window frames, stovepipes
              through two windows, laundry line to a pole at x 200 (KarskLaundry actor hangs the washing), a woman
    206-460   two log houses (izby, x 208 and 412) with steep snowy roofs, carved frames, smoking chimneys,
              birches, picket fences -> roofs above the fence beside the tea stall and the signal box (cam 0);
              300-410 stays low so the far goods train on the mid embankment is seen from exp_distant_train
    460-690   woodsheds and log piles (hidden behind the signal box / low under the sun at cam 0)
    690-1000  brick locomotive shed (DEPO): arched gates, roof with a row of smoke jacks (steam fx), lower than
              before so the Stalinist tower of the mid plane rises above it at cam 640
    1000-1120 low timber goods shed (sun at cam 640)
    1120-1330 half-stone merchant house (brick ground floor, log upper floor) -- hidden behind the office at 1280
    1330-1570 garages, fences, birches only: cooling towers, distant train and sun stay visible at cam 1280.
"""
from __future__ import annotations

import math

import numpy as np

import env_karsk_skyline_lib as SL
from env_karsk_skyline_lib import (NI, TE, SA, SK, ST, RU, CO, SN, WO, RED, PLANES, put, rect, hline, vline, line,
                                   Haze, vfog, dith, N_UP, N_RIGHT, draw_text, text_width)
import env_karsk_skyline_kit as K
import env_karsk_skyline_arch as A


def snow_roof_band(L, x, y_eave, w, rise, S, C, seed=0, inset=1):
    """Pitched roof seen from the long side: a band that narrows to the ridge (hipped ends), under thick snow;
    dark eave line, a few darker gaps where the snow slid."""
    rng = np.random.default_rng(seed)
    sn = S['snow']
    for k in range(rise):
        yy = y_eave - 1 - k
        xa = x - 2 + k * inset
        xb = x + w + 2 - k * inset
        for xx in range(xa, xb):
            t = k / max(1, rise - 1)
            r = rng.random()
            c = sn[-1] if r < 0.25 + 0.5 * t else (sn[-2] if r < 0.85 else C[2])
            if xx in (xa, xb - 1):
                c = C[1] if xx == xa else C[3]
            put(L, xx, yy, c, N_UP)
    hline(L, x - 2, y_eave, w + 4, C[0])
    hline(L, x - 1, y_eave + 1, w + 2, C[1])
    return y_eave - rise


def plank_wall(L, x, y, w, h, C, step=3):
    K.facade(L, x, y, w, h, C)
    for yy in range(y + 1, y + h, step):
        hline(L, x + 1, yy, w - 2, C[1])
    vline(L, x, y, h, C[0])


def carved_window(L, x, y, w, h, S, C, kind='dark', em=False, shutters=False):
    """Window with a white carved frame (nalichnik): side boards, pointed crown, skirt; optional lit pane."""
    cc = S['carve']
    rect(L, x - 1, y - 1, w + 2, h + 2, cc[0])
    hline(L, x - 2, y - 2, w + 4, cc[1])
    hline(L, x - 1, y - 3, w + 2, cc[1])
    put(L, x + w // 2, y - 4, cc[1])
    hline(L, x - 2, y + h + 1, w + 4, cc[1])
    put(L, x - 1, y + h + 2, cc[0])
    put(L, x + w, y + h + 2, cc[0])
    if kind == 'lit':
        rect(L, x, y, w, h, S['warm'], em=S['warm'])
        rect(L, x, y + h - 2, w, 2, S['warm2'], em=S['warm2'])
    else:
        rect(L, x, y, w, h, S['glass'])
        put(L, x + w - 1, y, S['glass_hi'])
    vline(L, x + w // 2, y, h, cc[0])
    hline(L, x, y + h // 3, w, cc[0])
    if shutters:
        rect(L, x - 4, y, 3, h, C[2])
        rect(L, x + w + 1, y, 3, h, C[2])


def stovepipe_through_window(L, wx, wy, ww, wh, S, up=14):
    """Tin stovepipe leaving a window pane sideways and turning up along the wall (housing shortage)."""
    py = wy + wh // 2
    hline(L, wx + ww - 2, py, 6, NI[2])
    hline(L, wx + ww - 2, py + 1, 6, NI[1])
    vline(L, wx + ww + 3, py - up, up + 2, NI[2])
    vline(L, wx + ww + 4, py - up, up + 2, TE[3])
    hline(L, wx + ww + 2, py - up - 1, 4, NI[1])
    return (wx + ww + 3, py - up - 1)


def tiny_woman(L, x, base, S):
    """13 px woman (headscarf, padded coat, felt boots) hanging washing, arms raised to the line."""
    coat = [TE[1], TE[2], TE[3]]
    rect(L, x - 1, base - 13, 3, 3, SN[2])                 # headscarf
    put(L, x, base - 11, RU[3])                            # face (back-lit)
    rect(L, x - 2, base - 10, 5, 6, coat[1])               # coat
    vline(L, x - 2, base - 10, 6, coat[0])
    vline(L, x + 2, base - 10, 6, coat[2])
    rect(L, x - 2, base - 4, 5, 2, coat[1])
    rect(L, x - 1, base - 2, 1, 2, NI[1])                  # boots
    rect(L, x + 1, base - 2, 1, 2, NI[1])
    line(L, x + 2, base - 10, x + 4, base - 14, coat[2])   # raised arm to the line
    put(L, x + 4, base - 15, RU[3])


def woodpile(L, x, base, w, h, S, seed=0):
    rng = np.random.default_rng(seed)
    for yy in range(base - h, base):
        for xx in range(x, x + w):
            c = WO[2] if (xx + yy * 2) % 3 else WO[3]
            if rng.random() < 0.15:
                c = WO[4]
            put(L, xx, yy, c)
    hline(L, x, base - h - 1, w, S['snow'][-1], N_UP)
    hline(L, x, base - h, w, S['snow'][-2], N_UP)


def make_near_bg():
    S = K.STYLES['near_bg']
    g = PLANES['near_bg']
    B = g['base']
    ppm = SL.ppm('near_bg')
    L = SL.world_layer('near_bg')
    Cp = S['plank']
    Cl = S['logs']
    Cb = S['brick']
    meta = {'smoke': [], 'steam': [], 'pegs': []}
    rng = np.random.default_rng(17)
    # ---------------------------------------------------------------- barrack (4-160), laundry pole at 200
    bx0, bw = 4, 156
    wall_top = B - 50
    plank_wall(L, bx0, wall_top, bw, 50, Cp)
    rect(L, bx0, B - 4, bw, 4, TE[0])                                  # plinth
    vline(L, bx0 + bw - 1, wall_top, 50, Cp[4], N_RIGHT)
    for k in range(bx0 + 52, bx0 + bw, 52):                           # corner posts / section joints
        vline(L, k, wall_top, 46, Cp[3])
    win = []
    for i in range(7):
        wx = bx0 + 9 + i * 21
        for wy in (wall_top + 6, wall_top + 29):
            kind = 'dark'
            if (i, wy) == (2, wall_top + 29):
                kind = 'lit'
            carved_window(L, wx, wy, 7, 10, S, Cp, kind=kind)
            win.append((wx, wy))
    for (i, wy, up) in ((1, wall_top + 6, 12), (5, wall_top + 29, 8)):  # stovepipes through two windows
        wx = bx0 + 9 + i * 21
        top_xy = stovepipe_through_window(L, wx, wy, 7, 10, S, up=up)
        if i == 1:                                     # the lower pipe ends behind the yard fence: no fx
            meta['smoke'].append(('barrack_%d' % i, top_xy))
    ridge = snow_roof_band(L, bx0, wall_top - 1, bw, 11, S, TE, seed=3, inset=1)
    for (cx, ch) in ((bx0 + 40, 6), (bx0 + 116, 6)):                  # brick chimneys on the ridge
        rect(L, cx, ridge - ch + 2, 4, ch, Cb[2])
        vline(L, cx + 3, ridge - ch + 2, ch, Cb[3])
        hline(L, cx - 1, ridge - ch + 1, 6, S['snow'][-1], N_UP)
    pole_x = bx0 + bw + 40
    vline(L, pole_x, B - 56, 56, WO[2])
    vline(L, pole_x + 1, B - 56, 56, TE[4])
    pts = []
    x0, y0, x1, y1 = bx0 + bw - 1, wall_top + 10, pole_x, B - 54
    for i in range(41):
        t = i / 40.0
        pts.append((x0 + (x1 - x0) * t, y0 + (y1 - y0) * t + 6 * 4 * t * (1 - t)))
    for a, b in zip(pts[:-1], pts[1:]):
        line(L, a[0], a[1], b[0], b[1], NI[3])
    for t in (0.12, 0.26, 0.4, 0.55, 0.7, 0.84):
        lx, ly = pts[int(t * (len(pts) - 1))]
        meta['pegs'].append([int(round(lx)), int(round(ly))])
    meta['barrack'] = (bx0, bw, wall_top)
    # ---------------------------------------------------------------- izby between barrack, tea stall and box
    S2 = dict(S, logs=[NI[3], WO[1], WO[2], WO[3], TE[4]])
    # (near_bg 300-410 stays low: from exp_distant_train (cam ~150) the far train is seen over it)
    for (ix, wm, seed, lit) in ((208, 5.6, 1, False), (412, 6.0, 3, False)):   # no warm light next to the box
        chim = A.izba(L, ix, B, S2, ppm, w_m=wm, wall_m=3.2, roof_m=4.2, seed=seed, mat='logs', lit=lit,
                      chimney_side=0.22, fence=True)
        meta['smoke'].append(('izba_%d' % ix, chim))
    for (tx, th, sd) in ((262, 52, 1), (404, 46, 2), (460, 60, 3), (590, 48, 4), (676, 54, 5)):
        K.birch(L, tx, B, th, S, seed=sd)
    # ---------------------------------------------------------------- woodsheds, log piles (behind the box)
    for (wx, ww, wh) in ((466, 40, 22), (520, 30, 18), (560, 44, 24), (630, 36, 16)):
        plank_wall(L, wx, B - wh, ww, wh, Cp)
        snow_roof_band(L, wx, B - wh - 1, ww, 4, S, TE, seed=wx, inset=1)
    woodpile(L, 508, B, 12, 10, S, seed=2)
    woodpile(L, 604, B, 20, 8, S, seed=3)
    # ---------------------------------------------------------------- locomotive shed (DEPO)
    dx, dw = 690, 310
    d_top = B - 64
    rect(L, dx, d_top, dw, 64, Cb[2])
    for yy in range(d_top + 1, B, 3):                                  # dithered brick coursing
        for xx in range(dx, dx + dw):
            if (xx + (yy // 3) * 2) % 4 != 0:
                put(L, xx, yy, Cb[1])
    vline(L, dx, d_top, 64, NI[3])
    vline(L, dx + dw - 1, d_top, 64, Cb[4], N_RIGHT)
    for k in range(dx, dx + dw, 62):                                   # pilasters
        rect(L, k, d_top, 4, 64, Cb[3])
        vline(L, k + 3, d_top, 64, TE[3])
    hline(L, dx - 1, d_top, dw + 2, Cb[3], N_UP)                        # brick cornice
    for k in range(5):                                                  # arched gates + windows
        gx = dx + 12 + k * 62
        gw, gh = 38, 44
        gy = B - gh
        for yy in range(gy, B):
            rel = yy - gy
            half = int(math.sqrt(max(0, 19 ** 2 - (12 - rel) ** 2 * 3))) if rel < 12 else 19
            hline(L, gx + 19 - half, yy, 2 * half, TE[0] if k != 2 else NI[1])
        for a in range(0, 181, 12):
            ax = gx + 19 + int(math.cos(math.radians(a)) * 20)
            ay = gy + 12 - int(math.sin(math.radians(a)) * 12)
            put(L, ax, ay, Cb[3])
        if k != 2:
            for xx in range(gx + 1, gx + 38, 3):
                vline(L, xx, gy + 6, gh - 6, TE[1])
        for j in range(3):
            K.arched_window(L, gx + 4 + j * 12, d_top + 5, 7, 9, dict(S, snow=S['snow']), 'dark', sill=True)
    ridge = snow_roof_band(L, dx, d_top - 1, dw, 9, S, TE, seed=7, inset=1)
    for k in range(6):                                                  # smoke jacks on the roof
        jx = dx + 30 + k * 50
        rect(L, jx, ridge - 5, 5, 7, NI[2])
        vline(L, jx + 4, ridge - 5, 7, TE[3])
        hline(L, jx - 1, ridge - 6, 7, NI[1])
        hline(L, jx - 1, ridge - 7, 7, S['snow'][-1], N_UP)
        if k == 5:
            meta['steam'].append(('depot_jack', (jx + 2, ridge - 7)))
    sg = 'ДЕПО'
    sw = text_width(sg, 'S', 1)
    rect(L, dx + dw // 2 - sw // 2 - 2, d_top + 1, sw + 4, 7, TE[1])
    draw_text(L, dx + dw // 2 - sw // 2, d_top + 2, sg, SN[2], font='S', spacing=1)
    # ---------------------------------------------------------------- low goods shed (sun gap at cam 640)
    plank_wall(L, 1006, B - 30, 96, 30, Cp)
    for k in range(1012, 1100, 22):
        rect(L, k, B - 24, 14, 20, TE[0])
        vline(L, k + 7, B - 24, 20, TE[1])
    snow_roof_band(L, 1006, B - 31, 96, 5, S, TE, seed=11, inset=2)
    # ---------------------------------------------------------------- half-stone merchant house (behind office)
    mx, mw = 1150, 120
    rect(L, mx, B - 26, mw, 26, Cb[2])
    for yy in range(B - 25, B, 3):
        for xx in range(mx, mx + mw):
            if (xx + (yy // 3) * 2) % 4 != 0:
                put(L, xx, yy, Cb[1])
    log_top = B - 26 - 24
    K.facade(L, mx - 2, log_top, mw + 4, 24, Cl)
    for yy in range(log_top + 1, B - 26, 3):
        hline(L, mx - 2, yy, mw + 4, Cl[1])
    for i in range(6):
        wx = mx + 8 + i * 19
        carved_window(L, wx, log_top + 7, 7, 10, S, Cl, kind='lit' if i == 4 else 'dark')
        K.arched_window(L, wx, B - 20, 7, 11, S, 'dark', sill=True)
    ridge = snow_roof_band(L, mx - 2, log_top - 1, mw + 4, 12, S, TE, seed=13, inset=2)
    rect(L, mx + 30, ridge - 4, 4, 7, Cb[2])
    hline(L, mx + 29, ridge - 5, 6, S['snow'][-1], N_UP)
    meta['smoke'].append(('merchant', (mx + 31, ridge - 5)))
    # ---------------------------------------------------------------- east end: garages, fences, birches
    A.garages(L, 1336, B, 6, dict(S, conc_d=S['conc']), ppm, seed=5, mat='conc_d')
    for (fx0, fx1) in ((1290, 1336), (1520, 1570)):
        for fx in range(fx0, fx1, 3):
            vline(L, fx, B - 12, 12, WO[2] if fx % 2 else WO[1])
            put(L, fx, B - 13, S['snow'][-1])
    for (tx, th, sd) in ((1110, 58, 6), (1300, 50, 7), (1488, 62, 8), (1548, 44, 9)):
        K.birch(L, tx, B, th, S, seed=sd)
    # ---------------------------------------------------------------- base fill + haze toward the yard fog
    for xx in range(L.w):
        hh = 3 + int(1.5 * math.sin(xx / 7.0) + math.sin(xx / 2.3))
        for yy in range(B - hh, B + 1):
            if L.c[yy, xx, 3] == 0:
                put(L, xx, yy, TE[1] if dith(xx, yy, 0.5) else TE[2])
    hz = Haze([[NI[1], NI[2], NI[3], TE[0], TE[1], TE[2], TE[3], TE[4], SA[2], SA[3]],
               [WO[1], WO[2], WO[3], WO[4], ST[4], SA[3]], [RU[0], RU[1], RU[2], RU[3], ST[4]],
               [SN[0], SN[1], SN[2], SN[3]]])
    hz.shift(L, vfog(L, 214, B + 1, 2.4, 1.6))
    return L, meta
