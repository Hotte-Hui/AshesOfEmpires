"""env_karsk_skyline_arch -- landmark architecture for the Karsk skyline: Orthodox church turned warehouse,
Stalinist railway administration with spire, tower crane, Russian log houses (izby), garages.
Builds on env_karsk_skyline_kit (shapes, windows, styles).  Original procedural pixel art.
"""
from __future__ import annotations

import math

import numpy as np

from env_karsk_skyline_lib import (NI, TE, SA, SK, ST, RU, CO, SN, WO, CLEAR, put, rect, hline, vline, line, opaque,
                                   cyl_normals, sphere_normals, N_UP, N_RIGHT, emblem_mask, paint_mask, draw_text,
                                   text_width)
from env_karsk_skyline_kit import (M, facade, snow_line, window, arched_window, birch)


# =========================================================================== ORTHODOX CHURCH (now a warehouse)
def onion_dome(L, cx, y_base, w, h, C, seed=0, rust=None, holes=0, spike=3, snow_col=None, neck=None):
    """Onion dome sitting on row y_base (its neck), max width w, bulb height h, pointed top + bare spike (the
    cross was removed).  Shaded for the back-right sun; optional rust patches / missing sheets (ribs show)."""
    rng = np.random.default_rng(seed)
    neck = neck if neck is not None else max(2, int(round(w * 0.62)))
    rows = []
    for k in range(h):
        t = k / max(1, h - 1)                     # 0 bottom (neck) .. 1 top (point)
        if t < 0.38:                               # neck -> belly
            u = t / 0.38
            half = neck / 2.0 + (w / 2.0 - neck / 2.0) * math.sin(u * math.pi / 2)
        else:                                      # belly -> point (ogee)
            u = (t - 0.38) / 0.62
            half = (w / 2.0) * (math.cos(u * math.pi / 2) ** 1.35)
        rows.append(max(0.5, half))
    top_y = y_base - h
    for k, half in enumerate(rows):
        yy = y_base - 1 - k
        xa, xb = int(round(cx - half)), int(round(cx + half))
        if xb <= xa:
            xb = xa + 1
        for xx in range(xa, xb):
            u = (xx + 0.5 - cx) / max(0.6, half)
            if xx == xb - 1:
                c = C[4]
            elif u > 0.45:
                c = C[3]
            elif u < -0.55:
                c = C[0]
            elif u < -0.1:
                c = C[1]
            else:
                c = C[2]
            put(L, xx, yy, c)
    for k in range(int(h * 0.15), int(h * 0.8)):  # sheet seams on the belly
        yy = y_base - 1 - k
        half = rows[k]
        for f in (-0.35, 0.25):
            xx = int(round(cx + f * half))
            if opaque(L, xx, yy) and half > 2.5:
                cur = L.c[yy, xx]
                put(L, xx, yy, C[1] if not (cur[:3] == C[0][:3]).all() else C[0])
    if rust:
        for _ in range(max(1, w // 6)):
            k = int(rng.integers(int(h * 0.15), max(int(h * 0.15) + 1, int(h * 0.7))))
            yy = y_base - 1 - k
            xx = int(round(cx + rng.uniform(-0.6, 0.5) * rows[k]))
            for (a, b) in ((0, 0), (1, 0), (0, 1)):
                if opaque(L, xx + a, yy + b):
                    put(L, xx + a, yy + b, rust[int(rng.integers(0, len(rust)))])
    for _ in range(holes):                         # missing sheets: dark void with a rib line
        k = int(rng.integers(int(h * 0.3), int(h * 0.65)))
        yy = y_base - 1 - k
        xx = int(round(cx + rng.uniform(-0.3, 0.4) * rows[k]))
        rect(L, xx, yy, 2, 3, NI[3])
        put(L, xx + 1, yy + 1, C[2])
    if snow_col is not None:                      # snow caught on the upper shoulders
        k = int(h * 0.62)
        yy = y_base - 1 - k
        half = rows[k]
        for xx in range(int(round(cx - half * 0.7)), int(round(cx + half * 0.2))):
            if opaque(L, xx, yy - 1):
                put(L, xx, yy - 1, snow_col, N_UP)
    vline(L, int(round(cx)), top_y - spike, spike, C[0])           # bare spike, no cross
    sphere_normals(L, cx, y_base - h * 0.4, w / 2.0, h / 2.0, int(cx - w), top_y, int(cx + w), y_base)
    return top_y - spike


def drum(L, cx, y_base, w, h, Cw, S, windows=2, win_kind='dark'):
    x0 = int(round(cx - w / 2.0))
    facade(L, x0, y_base - h, w, h, Cw)
    cyl_normals(L, x0, y_base - h, w, h)
    if windows and w >= 6 and h >= 6:
        ww = 1 if w < 10 else 2
        for i in range(windows):
            wx = x0 + int((i + 1) * w / (windows + 1)) - ww // 2
            rect(L, wx, y_base - h + 2, ww, max(2, h - 5), S['glass'] if win_kind != 'boarded' else WO[2])
    hline(L, x0 - 1, y_base - h, w + 2, Cw[3], N_UP)
    return y_base - h


def kokoshniki(L, x, y_top, w, n, Cw, S):
    """Row of semicircular gables (kokoshniki) crowning the church cube."""
    r = w / (2.0 * n)
    for i in range(n):
        cx = x + r * (2 * i + 1)
        for yy in range(int(y_top - r), y_top + 1):
            for xx in range(int(cx - r), int(cx + r) + 1):
                dx = xx + 0.5 - cx
                dy = y_top - yy
                if dx * dx + dy * dy <= r * r:
                    put(L, xx, yy, Cw[2] if dx < r * 0.5 else Cw[3])
        for a in range(0, 181, 6):
            ax = cx + math.cos(math.radians(a)) * (r - 0.5)
            ay = y_top - math.sin(math.radians(a)) * (r - 0.5)
            put(L, int(round(ax)), int(round(ay)), Cw[1])
        for a in range(30, 151, 10):
            ax = cx + math.cos(math.radians(a)) * (r + 0.4)
            ay = y_top - math.sin(math.radians(a)) * (r + 0.4)
            put(L, int(round(ax)), int(round(ay)), S['snow'][-1], N_UP)


def church(L, x, base, S, seed=0):
    """Five-domed parish church seen from the south, west end (bell tower) on the left, now a state goods
    warehouse: crosses removed (bare spikes), sheets missing on the main dome, rust, boarded windows, scaffolding
    on the belfry, a birch sapling on the refectory roof, painted СКЛАД sign.  ~20 m (94 px at mid scale)."""
    Cw = S['white']
    Cd = S['dome']
    Cm = S['metal']
    # ---- bell tower (left)
    bt_x, bt_w = x, 18
    facade(L, bt_x, base - 50, bt_w, 50, Cw)
    vline(L, bt_x + 2, base - 50, 50, Cw[1])
    vline(L, bt_x + bt_w - 3, base - 50, 50, Cw[3])
    arched_window(L, bt_x + 7, base - 40, 4, 9, S, 'boarded', sill=True)
    hline(L, bt_x - 1, base - 50, bt_w + 2, Cw[3], N_UP)
    snow_line(L, bt_x - 1, base - 51, bt_w + 2, S, 1, seed)
    bf_x, bf_w = bt_x + 2, bt_w - 4                                  # belfry: open arches, bells gone
    facade(L, bf_x, base - 66, bf_w, 16, Cw)
    for ax in (bf_x + 2, bf_x + 8):
        arched_window(L, ax, base - 63, 4, 10, S, 'void', sill=False)
    hline(L, bf_x - 1, base - 66, bf_w + 2, Cw[3], N_UP)
    snow_line(L, bf_x - 1, base - 67, bf_w + 2, S, 1, seed + 1)
    oc_x, oc_w = bt_x + 4, bt_w - 8                                  # upper octagon
    facade(L, oc_x, base - 74, oc_w, 8, Cw)
    rect(L, oc_x + 4, base - 72, 2, 4, S['glass'])
    tr_h = 15                                                         # tent roof (shatyor)
    cx = oc_x + oc_w / 2.0
    for k in range(tr_h):
        t = k / max(1, tr_h - 1)
        half = (oc_w / 2.0 + 0.5) * (1 - t) + 0.5
        yy = base - 74 - 1 - k
        for xx in range(int(round(cx - half)), int(round(cx + half))):
            c = Cd[1] if xx < cx - 0.5 else Cd[2]
            if (k % 4 == 1) and xx < cx:
                c = S['snow'][-1]
            put(L, xx, yy, c)
        put(L, int(round(cx + half)) - 1, yy, Cd[4])
    otop = onion_dome(L, cx, base - 74 - tr_h, 5, 5, Cd, seed=seed + 2, spike=3)
    sc_x = bt_x + bt_w - 6                                           # scaffolding on the belfry (right half)
    for px_ in (sc_x, bt_x + bt_w + 1):
        vline(L, px_, base - 70, 70, ST[3])
        put(L, px_, base - 71, ST[2])
    for yy in range(base - 68, base - 20, 12):
        hline(L, sc_x - 1, yy, bt_x + bt_w + 3 - sc_x, ST[4])
        hline(L, sc_x - 1, yy + 1, bt_x + bt_w + 3 - sc_x, ST[2])
    line(L, sc_x, base - 56, bt_x + bt_w + 1, base - 44, ST[3])
    # ---- refectory (trapeznaya)
    rf_x, rf_w, rf_h = bt_x + bt_w, 26, 30
    facade(L, rf_x, base - rf_h, rf_w, rf_h, Cw, left=False)
    for wx in (rf_x + 5, rf_x + 15):
        arched_window(L, wx, base - rf_h + 7, 5, 10, S, 'boarded' if wx == rf_x + 5 else 'dark')
    for k in range(6):
        hline(L, rf_x - 1 + k, base - rf_h - 1 - k, rf_w + 2 - 2 * k, Cm[2] if k % 2 else Cm[3])
    snow_line(L, rf_x + 2, base - rf_h - 6, rf_w - 4, S, 1, seed + 3)
    birch(L, rf_x + rf_w - 7, base - rf_h - 3, 9, S, seed=seed + 4, twig_density=0.6)
    # ---- main cube (chetverik) with pilasters and 3 kokoshniki
    cb_x, cb_w, cb_h = rf_x + rf_w, 52, 48
    facade(L, cb_x, base - cb_h, cb_w, cb_h, Cw)
    for px_ in (cb_x + 1, cb_x + 17, cb_x + 34, cb_x + cb_w - 3):
        rect(L, px_, base - cb_h + 1, 2, cb_h - 1, Cw[3])
        vline(L, px_, base - cb_h + 1, cb_h - 1, Cw[1])
    hline(L, cb_x - 1, base - cb_h, cb_w + 2, Cw[3], N_UP)
    hline(L, cb_x - 1, base - cb_h + 1, cb_w + 2, Cw[1])
    for i, wx in enumerate((cb_x + 7, cb_x + 23, cb_x + 40)):
        arched_window(L, wx, base - cb_h + 9, 5, 12, S, 'boarded' if i != 1 else 'dark')
    kokoshniki(L, cb_x + 1, base - cb_h - 1, cb_w - 2, 3, Cw, S)
    sg_w = text_width('СКЛАД', 'S', 1) + 2                            # painted warehouse sign
    sgx = cb_x + (cb_w - sg_w) // 2
    rect(L, sgx, base - cb_h + 24, sg_w, 7, ST[1])
    draw_text(L, sgx + 1, base - cb_h + 25, 'СКЛАД', SA[4], font='S', spacing=1)
    cx_main = cb_x + cb_w / 2.0
    for cxd in (cb_x + 6, cb_x + cb_w - 6):
        dtop = drum(L, cxd, base - cb_h - 6, 6, 7, Cw, S, windows=0)
        onion_dome(L, cxd, dtop, 8, 9, Cd, seed=seed + int(cxd), rust=S['rust'], spike=2, snow_col=S['snow'][-1])
    dtop = drum(L, cx_main, base - cb_h - 8, 18, 14, Cw, S, windows=3)
    main_top = onion_dome(L, cx_main, dtop, 22, 16, Cd, seed=seed + 7, rust=S['rust'], holes=2, spike=4,
                          snow_col=S['snow'][-1])
    # ---- apse (right): half-round, lower, half-dome roof
    ap_x, ap_w, ap_h = cb_x + cb_w, 20, 34
    facade(L, ap_x, base - ap_h, ap_w, ap_h, Cw, left=False)
    cyl_normals(L, ap_x, base - ap_h, ap_w, ap_h)
    arched_window(L, ap_x + 8, base - ap_h + 8, 4, 10, S, 'boarded')
    for k in range(7):
        half = ap_w / 2.0 * math.cos(k / 7.0 * math.pi / 2)
        cxa = ap_x + ap_w / 2.0 - 1
        hline(L, int(cxa - half), base - ap_h - 1 - k, int(2 * half) + 1, Cm[2] if k < 5 else Cm[3])
    snow_line(L, ap_x + 3, base - ap_h - 7, ap_w - 6, S, 1, seed + 9)
    return {'x0': x, 'x1': ap_x + ap_w, 'top': min(main_top, otop)}


# =========================================================================== STALINIST ADMINISTRATION BUILDING
def stalinka(L, x, base, S, seed=0, lit=4, year='1953'):
    """Railway administration in Stalinist classicism: symmetric wings (rusticated ground floor, window
    surrounds, balustrade), central block with a giant portico of four columns and an attic with the year,
    two-tier tower with clock, colonnaded belvedere, gilt spire and a red star.  ~150 x 156 px at mid scale."""
    rng = np.random.default_rng(seed)
    St = S['stucco']
    Wh = S['white']
    wing_w, cen_w = 48, 54
    gf, fl = 16, 15
    W = 2 * wing_w + cen_w
    wing_top = base - (gf + 3 * fl)
    cen_top = base - (gf + 4 * fl)
    lit_windows = []

    def storey_windows(x0, w, floors, n):
        sp = w / float(n)
        for f in range(floors):
            fy = base - gf - (f + 1) * fl
            for i in range(n):
                wx = int(round(x0 + sp * i + (sp - 6) / 2))
                window(L, wx, fy + 3, 6, 9, S, 'curtain' if rng.random() < 0.18 else 'dark', sill=True)
                lit_windows.append((wx, fy + 3))
                if f == 0:                                  # sandrik over the piano nobile
                    hline(L, wx - 1, fy + 1, 8, Wh[3], N_UP)
                    hline(L, wx - 1, fy + 2, 8, Wh[1])
                elif f == floors - 1:
                    hline(L, wx - 1, fy + 2, 8, Wh[2])
        for i in range(n):
            wx = int(round(x0 + sp * i + (sp - 6) / 2))
            arched_window(L, wx, base - gf + 3, 6, 10, S, 'dark', sill=False)

    for side, wx0 in (('L', x), ('R', x + wing_w + cen_w)):
        facade(L, wx0, wing_top, wing_w, base - wing_top, St, left=(side == 'L'), rim=(side == 'R'))
        for yy in range(base - gf + 1, base, 3):                 # rustication
            hline(L, wx0, yy, wing_w, St[1])
        hline(L, wx0, base - gf, wing_w, Wh[2], N_UP)
        storey_windows(wx0 + 3, wing_w - 6, 3, 4)
        for px_ in (wx0 + (1 if side == 'L' else 0), wx0 + wing_w - 3):
            rect(L, px_, wing_top + 3, 2, base - gf - wing_top - 3, Wh[2])
        hline(L, wx0 - 1, wing_top + 2, wing_w + 2, Wh[1])
        hline(L, wx0 - 1, wing_top + 1, wing_w + 2, Wh[3], N_UP)
        hline(L, wx0 - 1, wing_top, wing_w + 2, Wh[2])
        for xx in range(wx0, wx0 + wing_w):                      # balustrade
            if xx % 2 == 0:
                put(L, xx, wing_top - 1, Wh[2])
                put(L, xx, wing_top - 2, Wh[2])
        hline(L, wx0 - 1, wing_top - 3, wing_w + 2, Wh[3], N_UP)
        snow_line(L, wx0 - 1, wing_top - 4, wing_w + 2, S, 1, seed + wx0)
        for k in range(3):
            hline(L, wx0 + 3 + k * 2, wing_top - 5 - k, wing_w - 6 - k * 4, S['snow'][-1] if k else S['snow'][-2],
                  N_UP)
        put(L, wx0 + 3, wing_top - 5, S['metal'][2])
    # ---- central block
    cx0 = x + wing_w
    facade(L, cx0, cen_top, cen_w, base - cen_top, St, left=False, rim=False)
    vline(L, cx0, cen_top, base - cen_top, St[1])
    vline(L, cx0 + cen_w - 1, cen_top, base - cen_top, St[3])
    for yy in range(base - gf + 1, base, 3):
        hline(L, cx0, yy, cen_w, St[1])
    hline(L, cx0, base - gf, cen_w, Wh[2], N_UP)
    lg_top = base - gf - 3 * fl - 2                                   # loggia behind the portico
    rect(L, cx0 + 4, lg_top, cen_w - 8, base - gf - lg_top, St[1])
    for f in range(3):
        fy = base - gf - (f + 1) * fl
        for i in range(3):
            wx = cx0 + 9 + i * 14
            window(L, wx, fy + 4, 6, 8, S, 'dark', sill=False)
            lit_windows.append((wx, fy + 4))
    for i in range(4):
        colx = cx0 + 5 + i * 14
        rect(L, colx, lg_top, 4, base - gf - lg_top, Wh[2])
        vline(L, colx, lg_top, base - gf - lg_top, Wh[1])
        vline(L, colx + 3, lg_top, base - gf - lg_top, Wh[4], N_RIGHT)
        rect(L, colx - 1, lg_top, 6, 2, Wh[3])
        rect(L, colx - 1, base - gf - 2, 6, 2, Wh[1])
    hline(L, cx0 + 2, lg_top - 1, cen_w - 4, Wh[1])
    rect(L, cx0 + 2, lg_top - 4, cen_w - 4, 3, Wh[2])
    hline(L, cx0 + 1, lg_top - 5, cen_w - 2, Wh[3], N_UP)
    fy = base - gf - 4 * fl
    for i in range(4):
        wx = cx0 + 6 + i * 12
        window(L, wx, fy + 3, 6, 7, S, 'dark', sill=True)
        lit_windows.append((wx, fy + 3))
    rect(L, cx0 + cen_w // 2 - 5, base - gf + 2, 10, gf - 2, NI[3])
    rect(L, cx0 + cen_w // 2 - 7, base - gf - 1, 14, 2, Wh[3])
    hline(L, cx0 - 1, cen_top + 1, cen_w + 2, Wh[3], N_UP)
    hline(L, cx0 - 1, cen_top + 2, cen_w + 2, Wh[1])
    at_h = 7
    facade(L, cx0 + 2, cen_top - at_h, cen_w - 4, at_h, St)
    hline(L, cx0 + 1, cen_top - at_h - 1, cen_w - 2, Wh[3], N_UP)
    snow_line(L, cx0 + 1, cen_top - at_h - 2, cen_w - 2, S, 1, seed + 3)
    if year:
        tw_ = text_width(year, 'S', 1)
        draw_text(L, cx0 + (cen_w - tw_) // 2, cen_top - at_h + 1, year, Wh[3], font='S', spacing=1)
    # ---- tower
    t_w = 26
    t_x = cx0 + (cen_w - t_w) // 2
    t_top = cen_top - at_h - 20
    facade(L, t_x, t_top, t_w, 20, St)
    for px_ in (t_x + 1, t_x + t_w - 3):
        rect(L, px_, t_top + 1, 2, 19, Wh[2])
    ccx, ccy = t_x + t_w / 2.0, t_top + 9
    for yy in range(t_top + 4, t_top + 15):
        for xx in range(t_x + 6, t_x + t_w - 6):
            d = math.hypot(xx + 0.5 - ccx, yy + 0.5 - ccy)
            if d <= 4.6:
                put(L, xx, yy, Wh[3] if d < 3.6 else Wh[1])
    line(L, ccx - 0.5, ccy - 0.5, ccx - 0.5, ccy - 3, NI[3])
    line(L, ccx - 0.5, ccy - 0.5, ccx + 1.5, ccy + 1, NI[3])
    hline(L, t_x - 1, t_top, t_w + 2, Wh[3], N_UP)
    snow_line(L, t_x - 1, t_top - 1, t_w + 2, S, 1, seed + 4)
    b_w, b_h = 18, 14
    b_x = t_x + (t_w - b_w) // 2
    b_top = t_top - b_h
    rect(L, b_x, b_top, b_w, b_h, St[0])
    for i in range(5):
        colx = b_x + i * 4
        rect(L, colx, b_top + 1, 2, b_h - 2, Wh[2])
        put(L, colx + 1, b_top + 1, Wh[4])
    hline(L, b_x - 1, b_top + b_h - 1, b_w + 2, Wh[1])
    hline(L, b_x - 1, b_top, b_w + 2, Wh[3], N_UP)
    snow_line(L, b_x - 1, b_top - 1, b_w + 2, S, 1, seed + 5)
    l_w, l_h = 10, 6
    l_x = t_x + (t_w - l_w) // 2
    l_top = b_top - l_h
    facade(L, l_x, l_top, l_w, l_h, St)
    rect(L, l_x + 4, l_top + 2, 2, 3, S['glass'])
    hline(L, l_x - 1, l_top, l_w + 2, Wh[3], N_UP)
    sp_h = 28                                                        # gilt spire, sunlit right edge
    scx = t_x + t_w / 2.0
    for k in range(sp_h):
        t = k / max(1, sp_h - 1)
        half = 3.6 * (1 - t) ** 1.3 + 0.5
        yy = l_top - 1 - k
        xa, xb = int(round(scx - half)), int(round(scx + half))
        if xb <= xa:
            xb = xa + 1
        for xx in range(xa, xb):
            put(L, xx, yy, S['metal'][2] if xx < scx - 0.5 else S['metal'][3])
        put(L, xb - 1, yy, CO[2] if k % 3 else CO[3])
    sp_top = l_top - sp_h
    star = emblem_mask('star5')
    paint_mask(L, int(round(scx)) - 2, sp_top - 5, star, S['red'][2], shade=S['red'][1])
    put(L, int(round(scx)) + 1, sp_top - 3, S['red'][3])
    for (wx, wy) in rng.permutation(np.array(lit_windows))[:lit]:
        rect(L, int(wx), int(wy), 6, 3, S['warm'], em=S['warm'])
        rect(L, int(wx), int(wy) + 3, 6, 2, S['warm2'], em=S['warm2'])
    return {'x0': x, 'x1': x + W, 'top': sp_top - 5, 'tower_x': int(round(scx))}


# =========================================================================== TOWER CRANE
def tower_crane(L, mast_x, base, mast_h, jib_l, jib_r, C, lamp=None, hook_x=None, hook_y=None, load=None,
                load_cols=None):
    """BKSM-style tower crane: lattice mast, cab, horizontal jib to the left, counter-jib with ballast to the
    right, tie bars from the apex, trolley + hook with a wall panel.  Returns (x, y) of the jib-end lamp."""
    col, rim = C[0], C[2]
    top = base - mast_h
    for yy in range(top, base):
        put(L, mast_x, yy, col)
        put(L, mast_x + 3, yy, rim)
        k = yy - top
        if k % 4 == 0:
            hline(L, mast_x, yy, 4, col)
        put(L, mast_x + 1 + (1 if k % 4 < 2 else 0), yy, col)
    jy = top - 1
    for xx in range(mast_x - jib_l, mast_x + 4 + jib_r):
        put(L, xx, jy, col)
        put(L, xx, jy + 2, col)
        if (xx - mast_x) % 3 == 0:
            put(L, xx, jy + 1, col)
    hline(L, mast_x - jib_l, jy - 1, jib_l, rim)
    ax, ay = mast_x + 1, jy - 9
    vline(L, ax, ay, 9, col)
    vline(L, ax + 1, ay, 9, rim)
    line(L, ax, ay, mast_x - jib_l + 2, jy - 1, col)
    line(L, ax + 1, ay, mast_x + 3 + jib_r - 2, jy - 1, col)
    rect(L, mast_x + 4, jy + 3, 5, 4, C[1])
    put(L, mast_x + 7, jy + 4, C[2])
    rect(L, mast_x + jib_r - 6, jy + 2, 7, 5, C[1])
    hline(L, mast_x + jib_r - 6, jy + 2, 7, C[2])
    lamp_xy = (mast_x - jib_l, jy - 1)
    if lamp is not None:
        put(L, lamp_xy[0], lamp_xy[1], lamp, em=lamp)
        put(L, mast_x + 2, ay - 1, lamp, em=lamp)
    if hook_x is not None:
        rect(L, hook_x - 1, jy + 3, 3, 2, col)
        vline(L, hook_x, jy + 5, hook_y - (jy + 5), col)
        if load is not None:
            lw, lh = load
            line(L, hook_x, hook_y - 3, hook_x - lw // 2, hook_y, col)
            line(L, hook_x, hook_y - 3, hook_x + lw // 2 - 1, hook_y, col)
            rect(L, hook_x - lw // 2, hook_y, lw, lh, load_cols[0])
            hline(L, hook_x - lw // 2, hook_y, lw, load_cols[1], N_UP)
    return lamp_xy


# =========================================================================== WOODEN HOUSES
def izba(L, x, base, S, ppm, w_m=7.5, wall_m=3.0, roof_m=4.2, seed=0, windows=3, carved=True, chimney_side=0.3,
         fence=True, mat='logs', lit=False, attic_window=True):
    """Russian log house (izba), gable end to the street: log walls, windows with white carved frames
    (nalichniki), steep snowy roof with bargeboards, brick chimney.  Returns the chimney top (x, y)."""
    C = S[mat]
    w = M(w_m, ppm)
    wh = M(wall_m, ppm)
    rh = M(roof_m, ppm)
    top = base - wh
    facade(L, x, top, w, wh, C)
    for yy in range(top + 1, base, max(2, int(round(ppm * 0.28)) + 1)):
        hline(L, x, yy, w, C[1])
    for k in range(0, wh, 2):
        put(L, x, top + k, C[3])
        put(L, x + w - 1, top + k, C[4])
    if windows:
        ww = max(2, M(0.7, ppm))
        whh = max(2, M(1.0, ppm))
        sp = w / float(windows)
        for i in range(windows):
            wx = int(round(x + sp * i + (sp - ww) / 2))
            wy = top + max(1, (wh - whh) // 2)
            if carved:
                cc = S.get('carve', [SA[3], SA[4]])
                rect(L, wx - 1, wy - 1, ww + 2, whh + 2, cc[0])
                hline(L, wx - 1, wy - 2, ww + 2, cc[1])
                if ww >= 3:
                    put(L, wx + ww // 2, wy - 3, cc[1])
                hline(L, wx - 1, wy + whh + 1, ww + 2, cc[0])
            if lit and i == 1:
                rect(L, wx, wy, ww, whh, S['warm'], em=S['warm'])
            else:
                rect(L, wx, wy, ww, whh, S['glass'])
                if whh >= 3 and ww >= 2:
                    vline(L, wx + ww // 2, wy, whh, C[1])
    cx = x + w / 2.0
    for k in range(rh):                                              # gable boards
        t = k / max(1, rh - 1)
        half = (w / 2.0 + 1) * (1 - t)
        yy = top - 1 - k
        for xx in range(int(round(cx - half)), int(round(cx + half))):
            put(L, xx, yy, C[1] if (xx % 3 == 0) else C[2])
    if attic_window and rh >= 6:
        aw = max(1, M(0.5, ppm))
        rect(L, int(cx - aw / 2), top - rh // 2 - 1, aw, max(1, aw + 1), S['glass'])
    sn = S['snow']
    for k in range(rh + 2):                                          # snow-laden roof slopes
        t = k / max(1, rh + 1)
        half = (w / 2.0 + 2) * (1 - t)
        yy = top - k
        xl = int(round(cx - half)) - 1
        xr = int(round(cx + half))
        for d in range(2):
            put(L, xl + d, yy - 1, sn[-1] if d == 0 else sn[-2], N_UP)
            put(L, xr - d, yy - 1, sn[-1] if d == 0 else sn[-2], N_UP)
        put(L, xl + 2, yy, C[0])
        put(L, xr - 2, yy, C[0])
    put(L, int(round(cx)), top - rh - 3, sn[-1], N_UP)
    chx = int(round(cx + w * chimney_side))
    chy = top - int(rh * (1 - chimney_side * 2)) - 3
    rect(L, chx, chy, 2, 4, RU[2])
    put(L, chx + 1, chy, RU[3])
    hline(L, chx, chy - 1, 2, sn[-1], N_UP)
    if fence:
        fh = max(2, M(1.4, ppm))
        for fx in range(x - 6, x + w + 6, 2):
            vline(L, fx, base - fh, fh, WO[2] if fx % 4 else WO[3])
            put(L, fx, base - fh - 1, sn[-1])
    return (chx, chy - 1)


def garages(L, x, base, n, S, ppm, seed=0, mat='conc_d'):
    """Row of small lock-up garages (brick / sheet metal) with single-pitch snowy roofs."""
    rng = np.random.default_rng(seed)
    C = S[mat]
    gw = M(3.2, ppm)
    gh = M(2.6, ppm)
    for i in range(n):
        gx = x + i * gw
        h = gh + int(rng.integers(0, 2))
        facade(L, gx, base - h, gw, h, C, left=(i == 0), rim=(i == n - 1))
        vline(L, gx, base - h, h, C[1])
        rect(L, gx + 2, base - h + 3, gw - 4, h - 3, S['metal'][1] if 'metal' in S else C[0])
        hline(L, gx - 1, base - h - 1, gw + 1, S['snow'][-1], N_UP)
        hline(L, gx - 1, base - h, gw + 1, C[3])
