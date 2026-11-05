"""env_veltrava_station_props -- playfield art (parallax 1) for L_C3_Station: our platform canopy (roof
underside band, hanging lamps, the triple station clock, hanging signs), the rear cast-iron columns, y-sorted
props, the passport control of the commission with its flags, the concourse façade (Café „Korridor“ = the
warm focal light, waiting room with the tiled stove, notice case, exchange office, exit arch), the square
seen through the exit arch, and the foreground frame (parallax 1.3).

Coordinates are world pixels.  Props are drawn on small local layers; `foot` = local pixel that lands on the
world position given by the orchestrator.  Trilingual signage DE / RU / FR as small pixel lettering.
"""
from __future__ import annotations

import math

import numpy as np

import pg
from env_veltrava_lib import (Layer, NI, SL, IR, CR, PA, LA, SK, SN, RD, CLEAR, UP, bayer, value_noise, dmask,
                              ladder_paint, ladder_shift, text, text_width, text_center, cyl_normal, flat_normal,
                              snow_top, snow_lip, stains, figure, tiny_person, layer_w, arch_mask, put_mask,
                              rustication)
from env_veltrava_station_bg import dilate, dome

W = 1920
BAND_Y = 20                 # rear eaves girder bottom of our canopy (screen y)
COLUMN_XS = (30, 290, 545, 900, 1095, 1352)
LAMP_XS = (150, 410, 700, 990, 1290, 1520, 1860)
CLOCK_X = 936               # the exp_clock hotspot (960) stands just right of it, looking up


# =========================================================================== small painters
def sign_board(L, x, y, lines, fg=SN[4], bg=SL[1], frame=SN[2], pad=2, font='s', gap=2, center=True, hgt=0.7,
               em=None):
    """Enamel sign with several lines of pixel text; returns (x, y, w, h)."""
    ws = [text_width(t, font) for t in lines]
    lh = 5 if font == 's' else 7
    w = max(ws) + 2 * pad + 2
    h = len(lines) * lh + (len(lines) - 1) * gap + 2 * pad + 2
    L.rect(x, y, w, h, frame, hgt=hgt)
    L.rect(x + 1, y + 1, w - 2, h - 2, bg, hgt=hgt - 0.02)
    for i, t in enumerate(lines):
        tx = x + 1 + pad + ((w - 2 - 2 * pad - ws[i]) // 2 if center else 0)
        text(L, tx, y + 1 + pad + i * (lh + gap), t, fg, font=font, em=em)
    return (x, y, w, h)


def clock_face(L, cx, cy, r, hh, mm, face=CR[5], rim=IR[2], hand=NI[1], em=SN[2]):
    L.ellipse(cx, cy, r + 1.4, r + 1.4, rim, hgt=0.8)
    L.ellipse(cx, cy, r, r, face, hgt=0.82, em=em)
    for a in range(0, 360, 30):
        rr = r - 1.3
        L.px(int(round(cx + math.cos(math.radians(a)) * rr)), int(round(cy + math.sin(math.radians(a)) * rr)),
             SL[3], em=SN[0])
    for ang, ln in ((math.radians(-90 + (hh % 12 + mm / 60.0) * 30), r * 0.5), (math.radians(-90 + mm * 6), r * 0.8)):
        for k in range(1, max(2, int(round(ln))) + 1):
            L.px(int(round(cx + math.cos(ang) * k)), int(round(cy + math.sin(ang) * k)), hand, em=SN[0])
    L.px(int(cx), int(cy), hand, em=SN[0])


def cast_column(L, cx, y_top, y_base, w=5, capital=True, brackets=True, col=None):
    """Fluted cast-iron column with base, capital and curved spandrel brackets (lit from the right)."""
    col = col if col is not None else [NI[2], IR[1], IR[2], IR[3], IR[4]]
    x0 = cx - w // 2
    L.rect(x0, y_top, w, y_base - y_top, col[1], hgt=0.6)
    L.vline(x0, y_top, y_base - y_top, col[0])
    L.vline(x0 + w - 1, y_top, y_base - y_top, col[3])
    if w >= 5:
        L.vline(x0 + w - 2, y_top, y_base - y_top, col[2])
        for yy in range(y_top + 6, y_base - 14, 2):           # flutes
            L.px(x0 + 2, yy, col[0])
    cyl_normal(L, x0, y_top, w, y_base - y_top)
    # base (plinth + torus)
    L.rect(x0 - 3, y_base - 12, w + 6, 12, col[1], hgt=0.62)
    L.rect(x0 - 2, y_base - 15, w + 4, 3, col[2], hgt=0.64)
    L.hline(x0 - 3, y_base - 12, w + 6, col[3])
    L.vline(x0 + w + 2, y_base - 12, 12, col[3])
    L.vline(x0 - 3, y_base - 12, 12, col[0])
    if capital:
        L.rect(x0 - 3, y_top, w + 6, 4, col[2], hgt=0.66)
        L.hline(x0 - 3, y_top, w + 6, col[4])
        L.rect(x0 - 2, y_top + 4, w + 4, 2, col[1])
        L.px(x0 - 3, y_top + 4, col[3])
        L.px(x0 + w + 2, y_top + 4, col[3])
    if brackets:
        for side in (-1, 1):
            r = 16
            for a in range(0, 91, 4):
                bx = cx + side * int(round(r - math.cos(math.radians(a)) * r))
                by = y_top - r + int(round(math.sin(math.radians(a)) * r))
                L.px(bx, by, col[2], 0.6)
                L.px(bx, by - 1, col[1], 0.6)
            for k in (5, 10):                                   # pierced spandrel rings
                L.px(cx + side * k, y_top - k // 2 - 2, col[3])


# =========================================================================== CANOPY BAND (layer, parallax 1)
def make_canopy(E):
    """Underside of our platform canopy at the top of the screen: dark roof boarding receding to the rear eaves
    girder (lattice, riveted), slate-blue dagger-board valance, snow lip + few icicles at the open rear edge,
    hanging cold lamps, the TRIPLE CLOCK (Berlin 7:55 / Veltrava 8:55 / Moskau 9:55) at x 960 and the
    trilingual hanging signs.  Pigeons roost on the girder above the pigeon corner."""
    L = Layer(W, 360, 'canopy')
    for y in range(0, BAND_Y):
        L.hline(0, y, W, NI[1] if y % 5 else NI[0], 0.6)
    for y in (4, 9, 13, 16, 18):                                # purlins (closer together toward the rear)
        L.hline(0, y, W, NI[2], 0.62)
    for cx in COLUMN_XS + (1500, 1700, 1900):                   # transverse girders above the columns
        L.rect(cx - 3, 0, 7, BAND_Y, NI[2], hgt=0.64)
        L.vline(cx + 3, 0, BAND_Y, IR[1])
        for yy in range(1, BAND_Y, 3):
            L.px(cx, yy, IR[2])
    L.rect(0, BAND_Y, W, 7, NI[2], hgt=0.7)                    # rear eaves girder (lattice)
    L.hline(0, BAND_Y, W, IR[2])
    L.hline(0, BAND_Y + 6, W, IR[1])
    for x in range(0, W, 8):
        L.line(x, BAND_Y + 1, x + 4, BAND_Y + 5, IR[1])
        L.line(x + 4, BAND_Y + 5, x + 8, BAND_Y + 1, IR[1])
        L.px(x, BAND_Y + 3, IR[3])
    for x in range(0, W, 4):                                    # dagger-board valance
        for k in range(5):
            L.px(x + 1, BAND_Y + 7 + k, SL[1] if k < 4 else SL[2], 0.66)
            if k < 3:
                L.px(x + 2, BAND_Y + 7 + k, SL[2] if k < 2 else SL[1], 0.66)
        L.px(x, BAND_Y + 7, SL[0])
    L.hline(0, BAND_Y + 7, W, SL[2])
    rng = np.random.default_rng(3)
    for x in range(W):                                          # snow lip from the roof above, few icicles
        if rng.random() < 0.6:
            L.px(x, BAND_Y + 12, SN[2] if rng.random() < 0.7 else SN[1], 0.7)
        if rng.random() < 0.035:
            for k in range(int(rng.integers(2, 6))):
                L.px(x, BAND_Y + 13 + k, SN[1] if k < 2 else SL[4], 0.6)
    flat_normal(L, 0, 0, W, BAND_Y, (0, -0.6, 0.8))             # underside faces down
    for x in range(468, 530, 9):                                # pigeons on the girder
        L.rect(x, BAND_Y - 3, 4, 3, SL[3])
        L.px(x + 4, BAND_Y - 3, SL[4])
        L.px(x - 1, BAND_Y - 2, SL[2])
    E['lamps'] = []
    for lx in LAMP_XS:                                          # hanging enamel lamps (cold mercury)
        L.vline(lx, BAND_Y + 7, 9, IR[1])
        L.rect(lx - 4, BAND_Y + 16, 9, 3, SL[2], hgt=0.85)
        L.hline(lx - 3, BAND_Y + 15, 7, SL[3])
        L.hline(lx - 5, BAND_Y + 19, 11, SN[3], 0.85)
        L.rect(lx - 1, BAND_Y + 20, 3, 2, SN[4], hgt=0.9, em=SN[4])
        L.px(lx, BAND_Y + 22, SN[3], em=SN[3])
        E['lamps'].append((lx, BAND_Y + 21))
    # the triple clock on a bracket: Berlin / Veltrava / Moskau (each city keeps its own time)
    cx = CLOCK_X
    hw = 50                                                     # housing half-width (three dials + plates)
    L.rect(cx - 1, BAND_Y + 7, 3, 7, IR[1])
    L.rect(cx - hw, BAND_Y + 13, 2 * hw + 1, 3, IR[1], hgt=0.8)
    L.hline(cx - hw, BAND_Y + 13, 2 * hw + 1, IR[3])
    for k in (-44, 44):
        L.vline(cx + k, BAND_Y + 16, 4, IR[1])
    L.rect(cx - hw, BAND_Y + 20, 2 * hw + 1, 30, NI[2], hgt=0.75)      # housing
    L.rect(cx - hw + 1, BAND_Y + 21, 2 * hw - 1, 28, IR[1])
    L.hline(cx - hw + 1, BAND_Y + 21, 2 * hw - 1, IR[3])
    L.vline(cx + hw, BAND_Y + 20, 30, IR[3])
    clock_face(L, cx, BAND_Y + 33, 9, 8, 55)
    clock_face(L, cx - 34, BAND_Y + 33, 7, 7, 55)
    clock_face(L, cx + 34, BAND_Y + 33, 7, 9, 55)
    for (lx, label) in ((cx - 34, 'BERLIN'), (cx, 'VELTRAVA'), (cx + 34, 'МОСКВА')):
        tw = text_width(label, 's')
        L.rect(lx - tw // 2 - 1, BAND_Y + 51, tw + 2, 7, SN[3], hgt=0.75)
        text(L, lx - tw // 2, BAND_Y + 52, label, NI[2])
    E['clock'] = (cx, BAND_Y + 33)
    # trilingual hanging signs: track 5 and the passport control
    for sx in (178, 808):
        L.vline(sx + 3, BAND_Y + 7, 7, IR[1])
        L.vline(sx + 34, BAND_Y + 7, 7, IR[1])
        sign_board(L, sx, BAND_Y + 14, ['GLEIS 5', 'ПУТЬ 5 · VOIE 5'], fg=SN[4], bg=SL[1], frame=SN[2])
    L.vline(1200, BAND_Y + 7, 8, IR[1])
    L.vline(1280, BAND_Y + 7, 8, IR[1])
    sign_board(L, 1192, BAND_Y + 15, ['PASSKONTROLLE', 'ПАСПОРТНЫЙ КОНТРОЛЬ', 'CONTRÔLE DES PASSEPORTS'],
               fg=SN[4], bg=SL[2], frame=SN[3])
    L.vline(1444, BAND_Y + 7, 6, IR[1])
    L.vline(1480, BAND_Y + 7, 6, IR[1])
    sign_board(L, 1436, BAND_Y + 13, ['AUSGANG · STADT', 'ВЫХОД · SORTIE'], fg=SN[4], bg=SL[1], frame=SN[2])
    return L


# =========================================================================== REAR COLUMNS (props)
def column_prop(kind=None):
    """One rear cast-iron column of our canopy (platform back edge, y 266) from the eaves girder down.
    kind: 'departures' (the departures board, exp/story 'departures'), 'poster' (commission poster),
    'track' (track-5 enamel plate + fire bucket), None."""
    Hc = 266 - BAND_Y + 2
    P = Layer(80, Hc + 2, 'column')
    cx = 40
    cast_column(P, cx, 6, Hc)
    info = {}
    if kind == 'departures':
        # mechanical departures board (white letters on black enamel) bolted to the column at eye level
        bx, by, bw, bh = cx - 33, 172, 68, 40
        P.rect(bx - 1, by - 9, bw + 2, 9, IR[1], hgt=0.8)
        P.rect(bx, by - 8, bw, 7, NI[2])
        text(P, bx + 3, by - 7, 'ABFAHRT', SN[4])
        text(P, bx + 38, by - 7, 'ОТПР.', SN[3])
        P.rect(bx - 1, by - 1, bw + 2, bh + 2, IR[2], hgt=0.8)
        P.rect(bx, by, bw, bh, NI[0], hgt=0.75)
        P.hline(bx, by, bw, IR[1])
        rows = [('6:12', 'BERLIN', '4'), ('9:20', 'WIEN', '2'), ('14:05', 'KORDON', '1'), ('19:48', 'MOSKVA', '3'),
                ('23:40', 'KORDON-17', '5')]
        for i, (t, d, g) in enumerate(rows):
            ry = by + 2 + i * 7
            key = i == len(rows) - 1
            col = SN[4] if key else SN[2]
            text(P, bx + 2, ry, t, col)
            text(P, bx + 24, ry, d, col)
            text(P, bx + bw - 6, ry, g, col)
            if key:                                           # freshly inserted slip (brighter edge)
                P.hline(bx + 1, ry - 1, bw - 2, IR[2])
        P.rect(bx + 2, by + bh - 4, bw - 4, 1, IR[1])
        P.px(bx + bw - 3, by + 2, SK[2])                       # glass glint
        info['board'] = (bx + bw // 2, by + bh // 2)
        P.rect(cx - 6, by + bh + 1, 12, 3, IR[1])              # bracket
    elif kind == 'poster':
        bx, by, pw = cx - 25, 184, 50
        P.rect(bx - 1, by - 1, pw + 2, 40, IR[2], hgt=0.8)
        P.rect(bx, by, pw, 38, CR[4], hgt=0.75)
        P.rect(bx + 1, by + 1, pw - 2, 15, SL[3])              # printed image: the bridge arms, three arches
        P.hline(bx + 7, by + 6, pw - 14, SN[4])
        for k in (13, 25, 37):
            P.px(bx + k - 1, by + 7, SN[4]); P.px(bx + k + 1, by + 7, SN[4])
            P.vline(bx + k - 2, by + 7, 4, SN[4]); P.vline(bx + k + 2, by + 7, 4, SN[4])
        for k in range(bx + 6, bx + pw - 6, 2):
            P.px(k, by + 12 + (k // 2) % 2, SN[3])
        text_center(P, bx + pw // 2, by + 18, 'WILLKOMMEN', SL[0])
        text_center(P, bx + pw // 2, by + 24, 'ДОБРО ПОЖ.', SL[1])
        text_center(P, bx + pw // 2, by + 30, 'BIENVENUE', SL[1])
        P.px(bx + pw // 2, by - 1, NI[2])
        P.px(bx + 3, by + 36, SL[1]); P.px(bx + pw - 4, by + 36, SL[1])   # drawing pins
        info['poster'] = (bx + pw // 2, by + 18)
    elif kind == 'track':
        P.rect(cx - 6, 160, 12, 14, SN[3], hgt=0.8)
        P.rect(cx - 5, 161, 10, 12, SL[1])
        text(P, cx - 2, 163, '5', SN[4], font='l')
        P.rect(cx - 5, 222, 10, 9, RD[2], hgt=0.8)             # fire bucket on a hook
        P.hline(cx - 5, 222, 10, RD[3])
        P.vline(cx + 4, 222, 9, RD[3])
        P.hline(cx - 4, 220, 8, IR[3])
        text(P, cx - 4, 225, 'FEU', SN[4])
    return P, (cx, Hc), info


# =========================================================================== PLATFORM PROPS
def luggage_cart():
    """Porter's four-wheel platform cart with suitcases, a trunk with travel labels and a hat box (exp_luggage)."""
    P = Layer(62, 40, 'luggage_cart')
    by = 39
    P.rect(4, by - 10, 50, 3, CR[1], hgt=0.6)
    P.hline(4, by - 10, 50, CR[2])
    P.hline(4, by - 8, 50, NI[3])
    for wx in (9, 48):
        P.ellipse(wx, by - 3, 3.5, 3.5, NI[2], hgt=0.55)
        P.ellipse(wx, by - 3, 1.5, 1.5, IR[3])
    P.line(54, by - 10, 61, by - 24, IR[2])                      # handle
    P.hline(58, by - 25, 4, IR[3])
    items = [(5, 14, 11, (LA[0], LA[1], LA[2])), (20, 18, 8, (IR[1], IR[2], IR[3])), (39, 13, 9, (PA[0], PA[1], PA[2])),
             (8, 12, 6, (CR[1], CR[2], CR[3])), (24, 10, 7, (RD[0], RD[1], RD[2]))]
    for i, (x, w, h, c) in enumerate(items):
        yb = by - 10 if i < 3 else by - 10 - (11 if i == 3 else 8)
        P.rect(x, yb - h, w, h, c[1], hgt=0.65)
        P.hline(x, yb - h, w, c[2])
        P.vline(x + w - 1, yb - h, h, c[2])
        P.vline(x, yb - h, h, c[0])
        P.hline(x, yb - h // 2, w, c[0])
        if i == 0:                                              # travel labels on the trunk
            P.rect(x + 2, yb - h + 3, 3, 2, CR[4])
            P.rect(x + 7, yb - h + 5, 3, 3, SN[3])
        P.px(x + w // 2, yb - h - 1, c[0])
    P.ellipse(48, by - 26, 4, 2.5, CR[3], hgt=0.7)              # hat box
    P.ellipse(48, by - 27, 3, 1.5, CR[4])
    return P, (31, by)


def bench(mitten=False, seated=False):
    """Station bench (cast-iron ends, wooden slats) facing the tracks: we see its back.  mitten: a lost
    child's mitten (red, knitted) lies on the seat (exp_mitten).  seated: two waiting travellers seen from
    behind (baked; far from every NPC anchor)."""
    o = 16 if seated else 0
    P = Layer(52, 24 + o, 'bench')
    by = 23 + o
    if seated:
        a = figure(30, [SL[0], SL[1], SL[2]], hat='scarf', hat_col=RD[1], facing='back', coat_len=0.7, seed=61,
                   rim=SL[3], hair=NI[1])
        b = figure(31, [IR[0], IR[1], IR[2]], hat='cap', hat_col=NI[1], facing='back', coat_len=0.72, seed=62,
                   rim=SL[3], hair=CR[1])
        P.blit(a, 11, o + 16 - 22)
        P.blit(b, 27, o + 16 - 23)
    for lx in (3, 45):
        P.rect(lx, o + 6, 3, 17, NI[2], hgt=0.6)
        P.px(lx + 2, o + 6, IR[2])
        P.line(lx, by, lx + 3, by - 6, NI[2])
    for k, yy in enumerate((4, 8, 12)):                        # back slats
        P.rect(1, o + yy, 50, 3, CR[1] if k % 2 else CR[2], hgt=0.62)
        P.hline(1, o + yy, 50, CR[3])
        P.hline(1, o + yy + 2, 50, CR[0])
    P.rect(1, o + 16, 50, 2, CR[0], hgt=0.6)                   # seat edge
    if mitten:
        P.rect(30, 1, 6, 4, RD[2], hgt=0.75)
        P.px(36, 2, RD[2]); P.px(35, 0, RD[2])
        P.hline(30, 4, 6, SN[3])
        P.px(31, 2, RD[3]); P.px(33, 2, RD[3])
    return P, (26, by)


def litter_basket():
    P = Layer(12, 18, 'basket')
    by = 17
    P.rect(2, 4, 8, 12, IR[1], hgt=0.6)
    for x in range(2, 10, 2):
        P.vline(x, 4, 12, NI[2])
    P.hline(1, 4, 10, IR[3])
    P.rect(4, 2, 4, 2, CR[3])                                   # newspaper sticking out
    P.rect(4, by - 1, 4, 1, NI[2])
    return P, (6, by)


def kiosk():
    """Newspaper kiosk (exp_kiosk): cast-iron frame, glazed sales window with the vendor, papers clipped on
    the front, trilingual header ZEITUNGEN · ГАЗЕТЫ · JOURNAUX."""
    P = Layer(64, 64, 'kiosk')
    by = 63
    P.rect(4, 14, 56, by - 14, PA[1], hgt=0.55)
    P.vline(4, 14, by - 14, PA[0])
    P.vline(59, 14, by - 14, PA[3])
    for x in range(8, 58, 6):
        P.vline(x, 40, by - 42, PA[0])
    P.rect(2, 8, 60, 6, PA[0], hgt=0.75)                       # roof cornice
    P.hline(2, 8, 60, PA[3])
    P.rect(6, 2, 52, 6, PA[1], hgt=0.75)
    for k in range(5):
        P.hline(6 + k * 2, 2 - k // 2, 52 - k * 4, PA[2])
    sign_board(P, 7, 15, ['ZEITUNGEN', 'ГАЗЕТЫ JOURNAUX'], fg=CR[5], bg=PA[0], frame=CR[3], pad=1, gap=1)
    wx, wy, ww, wh = 10, 30, 44, 12                             # sales window with the vendor
    P.rect(wx, wy, ww, wh, NI[3], hgt=0.3)
    vend = figure(40, [SL[0], SL[1], SL[2]], hat='beret', hat_col=NI[2], seed=91, skin=CR[3])
    for yy in range(wh - 1):
        for xx in range(vend.w):
            c = vend.c[yy + 1, xx]
            if c[3]:
                P.px(wx + 30 + xx - vend.w // 2, wy + yy + 1, c, 0.3)
    P.hline(wx, wy, ww, SL[3])
    P.px(wx + ww - 2, wy + 1, SK[1])
    P.rect(wx - 2, wy + wh, ww + 4, 3, CR[2], hgt=0.7)          # counter with papers
    for k in range(5):
        P.rect(wx + 2 + k * 8, wy + wh - 2, 6, 2, [SN[3], CR[4], SN[2], CR[5], SN[3]][k])
    for k, (px_, col) in enumerate(((8, SN[3]), (20, CR[4]), (32, SN[3]), (44, CR[5]))):   # papers on clips
        P.rect(px_, 46, 10, 13, col, hgt=0.6)
        P.hline(px_ + 1, 48, 8, NI[2])
        for yy in range(50, 58, 2):
            P.hline(px_ + 1, yy, 6 + (yy % 4) // 2, SL[3])
        P.px(px_ + 4, 46, IR[3])
        if k == 1:
            P.rect(px_ + 5, 52, 4, 4, SL[2])                    # a photo on the front page
    P.rect(2, by - 2, 60, 2, PA[0])
    return P, (32, by)


def booth():
    """Temporary booth of the commission's passport control (painted slate blue): counter 2 'Sowjetische
    Delegation' (left, x 1180-1246 when placed at 1180) with the warm desk lamp, counter 1 'Reichsdelegation'
    (right).  Trilingual counter signs, stamp, papers, a stovepipe."""
    P = Layer(160, 94, 'booth')
    by = 93
    x0, x1 = 2, 156
    top = 24
    P.rect(x0, top, x1 - x0, by - top, SL[2], hgt=0.55)
    for x in range(x0 + 3, x1, 5):                              # vertical boarding
        P.vline(x, top + 2, by - top - 4, SL[1])
    P.vline(x0, top, by - top, SL[0])
    P.vline(x1 - 1, top, by - top, SL[4])
    P.rect(x0 - 3, top - 6, x1 - x0 + 6, 6, SL[1], hgt=0.75)   # flat roof with a lip
    P.hline(x0 - 3, top - 6, x1 - x0 + 6, SL[3])
    P.hline(x0 - 3, top - 1, x1 - x0 + 6, NI[3])
    P.rect(x1 - 18, 4, 3, 14, NI[2])                            # stovepipe
    P.vline(x1 - 16, 4, 14, IR[3])
    P.hline(x1 - 19, 3, 5, NI[1])
    info = {}
    for k, (cxw, lines, num) in enumerate(((x0 + 38, ['SOWJ. DELEGATION', 'СОВ. ДЕЛЕГАЦИЯ', 'DÉL. SOVIÉTIQUE'], '2'),
                                           (x0 + 116, ['REICHSDELEGATION', 'ДЕЛЕГАЦИЯ РЕЙХА', 'DÉL. DU REICH'], '1'))):
        # trilingual counter sign, then the „Schalter n“ plate, then the counter window with its shelf
        sign_board(P, cxw - 35, top + 2, lines, fg=SN[4], bg=SL[0], frame=SN[2], pad=1, gap=1)
        plate = 'SCHALTER ' + num
        pw = text_width(plate, 's') + 6
        P.rect(cxw - pw // 2, top + 25, pw, 9, CR[4], hgt=0.75)
        P.rect(cxw - pw // 2 + 1, top + 26, pw - 2, 7, SL[1])
        text(P, cxw - pw // 2 + 3, top + 27, plate, SN[4])
        wx, wy, ww, wh = cxw - 26, top + 37, 52, 18              # counter window
        P.rect(wx - 2, wy - 2, ww + 4, wh + 4, CR[3], hgt=0.7)
        P.rect(wx, wy, ww, wh, NI[3], hgt=0.3)
        P.hline(wx, wy, ww, SL[0])
        P.px(wx + ww - 2, wy + 1, SK[2])
        P.rect(wx - 3, wy + wh, ww + 6, 3, CR[2], hgt=0.75)     # counter shelf
        P.hline(wx - 3, wy + wh, ww + 6, CR[4])
        P.rect(cxw + 16, wy + 4, 7, 7, SN[3], hgt=0.75)         # counter number disc
        P.rect(cxw + 17, wy + 5, 5, 5, SL[1])
        text(P, cxw + 18, wy + 5, num, SN[4])
        info['counter%s' % num] = (cxw, wy + wh)
        if num == '2':
            lx, ly = x0 + 18, wy + 4                           # the warm desk lamp (green shade), stamp, papers
            P.rect(lx - 3, ly, 7, 3, PA[2])
            P.px(lx, ly + 3, LA[4], em=LA[4])
            P.rect(lx - 2, ly + 3, 5, 3, LA[3], em=LA[3])
            P.rect(lx - 6, ly + 6, 16, 6, LA[1], em=LA[1])
            P.vline(lx, ly + 3, 9, LA[0])
            P.rect(cxw + 2, wy + 14, 10, 3, CR[5])
            P.rect(cxw - 10, wy + 13, 4, 4, NI[2])              # rubber stamp
            info['lamp'] = (lx, ly + 5)
        else:
            P.rect(cxw - 12, wy + 14, 14, 3, CR[4])             # the officer's ledger
            P.rect(cxw - 2, wy + 10, 3, 6, SL[3])               # ink stand
    P.rect(x0, by - 4, x1 - x0, 4, SL[1], hgt=0.6)              # skirting
    return P, (77, by), info


def flag(kind, hist=False):
    """Small delegation / commission flag on a short staff (prop).  kind: 'commission' (fictional city arms:
    white bridge with three arches over a wavy line on slate blue), 'ussr' (neutral: red with a fictional
    gear-and-wheat emblem; hist: hammer, sickle and star), 'reich' (neutral: Reichssiegel = white pillar in a
    black disc on grey-black; hist: the historical swastika flag).  Shown only as in-world iconography."""
    if kind == 'commission':
        P = Layer(26, 92, 'flag_commission')
        by = 91
        P.rect(3, by - 5, 6, 5, IR[1])
        P.vline(5, 4, by - 5, IR[3])
        P.vline(6, 4, by - 5, IR[1])
        P.ellipse(5.5, 3.5, 1.6, 1.6, LA[3])
        fx, fy, fw, fh = 7, 6, 18, 13
    else:
        P = Layer(22, 24, 'flag_' + kind)
        by = 23
        P.line(1, by, 7, 6, IR[3])                               # angled wall staff
        P.line(2, by, 8, 6, IR[1])
        fx, fy, fw, fh = 8, 5, 13, 9
    # cloth with two soft folds (hangs slightly)
    if kind == 'commission':
        base, dark, light = SL[3], SL[2], SL[4]
    elif kind == 'ussr':
        base, dark, light = RD[2], RD[1], RD[3]
    else:
        base, dark, light = (RD[2], RD[1], RD[3]) if hist else (IR[2], IR[1], IR[3])
    for x in range(fw):
        sag = int(round(1.2 * math.sin(math.pi * x / max(1, fw - 1))))
        for y in range(fh):
            c = base
            if x in (fw // 3, (2 * fw) // 3):
                c = dark
            elif x in (fw // 3 + 1,):
                c = light
            P.px(fx + x, fy + y + sag, c, 0.62)
    cx, cy = fx + fw // 2, fy + fh // 2
    if kind == 'commission':                                     # bridge with three arches over a wavy line
        P.hline(cx - 6, cy - 2, 13, SN[4])
        for k in (-4, 0, 4):
            P.px(cx + k - 1, cy - 1, SN[4]); P.px(cx + k + 1, cy - 1, SN[4])
            P.px(cx + k - 2, cy, SN[4]); P.px(cx + k + 2, cy, SN[4])
        P.px(cx - 6, cy - 1, SN[4]); P.px(cx + 6, cy - 1, SN[4])
        for k in range(-6, 7):
            P.px(cx + k, cy + 3 + ((k + 7) // 2) % 2, SN[3])
    elif kind == 'ussr':
        hx, hy = fx + 3, fy + 2
        if hist:                                                 # star above hammer and sickle (hoist corner)
            P.px(hx + 1, hy - 1, LA[3])
            for (dx, dy) in ((0, 1), (1, 1), (2, 1), (1, 2), (0, 3), (2, 3), (3, 3), (-1, 3)):
                pass
            P.px(hx, hy + 1, LA[3]); P.px(hx + 1, hy + 2, LA[3]); P.px(hx + 2, hy + 3, LA[3])   # sickle arc
            P.px(hx, hy + 3, LA[3]); P.px(hx - 1, hy + 2, LA[3])
            P.px(hx + 2, hy + 1, LA[3]); P.px(hx + 1, hy + 3, LA[3])                              # hammer
        else:                                                    # fictional gear ring with two wheat ears
            for (dx, dy) in ((1, 0), (2, 0), (0, 1), (3, 1), (0, 2), (3, 2), (1, 3), (2, 3)):
                P.px(hx + dx, hy + dy + 1, LA[3])
            P.px(hx - 1, hy + 2, LA[2]); P.px(hx + 4, hy + 2, LA[2])
            P.px(hx + 1, hy + 2, RD[1]); P.px(hx + 2, hy + 2, RD[1])
    else:
        if hist:                                                 # white disc + black hooked cross (tiny, tilted)
            P.ellipse(cx + 0.5, cy + 1.0, 3.2, 3.2, SN[4])
            for (dx, dy) in ((0, 0), (0, -1), (0, 1), (-1, 0), (1, 0), (1, -2), (-2, -1), (-1, 2), (2, 1)):
                P.px(cx + dx, cy + 1 + dy, NI[0])
        else:                                                    # black disc with the white pillar (Reichssiegel)
            P.ellipse(cx + 0.5, cy + 1.0, 3.2, 3.2, NI[0])
            P.vline(cx, cy - 1, 5, SN[4])
            P.px(cx + 1, cy - 1, SN[4])
    return P, ((5, by) if kind == 'commission' else (2, by))


def barrier():
    """Temporary barrier of the control: striped pole (slate blue / white) on two trestles + trilingual sign."""
    P = Layer(60, 40, 'barrier')
    by = 39
    for tx in (6, 50):
        P.line(tx - 4, by, tx, by - 18, CR[1])
        P.line(tx + 4, by, tx, by - 18, CR[1])
        P.hline(tx - 3, by - 8, 7, CR[0])
    for x in range(2, 58):
        P.vline(x, by - 21, 3, SN[3] if (x // 6) % 2 else SL[3], 0.7)
    P.hline(2, by - 21, 56, SN[4])
    sign_board(P, 14, by - 36, ['KONTROLLE', 'КОНТРОЛЬ', 'CONTRÔLE'], fg=NI[1], bg=SN[3], frame=SL[2], pad=1, gap=1)
    P.vline(29, by - 18 - 0, 0, NI[2])
    return P, (30, by)


def queue_reich():
    """Two members of the German delegation queueing at counter 1, seen from behind (baked, away from the
    Konrad anchor), with a suitcase."""
    P = Layer(48, 52, 'queue_reich')
    by = 51
    a = figure(45, [IR[0], IR[1], IR[2]], hat='homburg', hat_col=NI[1], facing='back', coat_len=0.84, seed=71,
               rim=SL[3], hair=NI[2], skin=CR[2])
    b = figure(44, [NI[3], IR[1], IR[2]], hat='fedora', hat_col=IR[1], facing='back', coat_len=0.8, seed=72,
               rim=SL[3], hair=CR[1], skin=CR[2], bag=([NI[2], IR[2], IR[3]], 1))
    P.blit(a, 2, by - a.h + 1)
    P.blit(b, 22, by - b.h + 1)
    P.rect(16, by - 8, 9, 8, LA[0], hgt=0.6)
    P.hline(16, by - 8, 9, LA[1])
    P.px(20, by - 9, NI[2])
    return P, (24, by)


def menu_stand():
    """Chalk-board menu of the café on an easel, a small storm lantern on top (warm accent at the door)."""
    P = Layer(22, 32, 'menu_stand')
    by = 31
    P.line(3, by, 8, 7, CR[0])
    P.line(19, by, 14, 7, CR[0])
    P.rect(6, 7, 11, 18, NI[2], hgt=0.6)
    P.hline(6, 7, 11, CR[1])
    P.vline(16, 7, 18, CR[1])
    P.rect(7, 8, 9, 3, PA[0])
    for yy in range(13, 24, 2):
        P.hline(8, yy, 4 + (yy % 4) // 2, SN[2])
    P.px(9, 9, LA[3]); P.px(11, 9, LA[3]); P.px(13, 9, LA[3])
    P.rect(10, 1, 4, 5, IR[2], hgt=0.7)                         # storm lantern
    P.rect(11, 2, 2, 3, LA[3], em=LA[3])
    P.px(11, 0, IR[3])
    return P, (11, by)


# =========================================================================== CONCOURSE FAÇADE (layer)
def make_concourse(E):
    """Concourse front of the station (x 1352-1920, y 20-262), seen under our canopy: rusticated ground floor
    with arched bays — notice case 'Büro für Rückführung' (x ~1440), waiting-room door with the tiled stove
    (x ~1520), Café „Korridor“ (x 1570-1730, THE warm light), exchange office (x ~1770), exit arch to the
    square (x 1836-1912, transparent: the square layer shows through) — tall hall windows above."""
    L = Layer(W, 360, 'concourse')
    x0, x1 = 1352, W
    S = dict(deep=SL[0], sh=SL[1], body=SL[2], lit=SL[3], rim=SL[4], hi=CR[3], joint=SL[1])
    # upper wall: ashlar with tall round-headed hall windows between pilasters (mid value, like the station
    # across the tracks; the glass mirrors the dawn sky so the upper band stays the lighter value group)
    L.rect(x0, BAND_Y + 6, x1 - x0, 150 - BAND_Y - 6, S['body'], hgt=0.5)
    for yy in range(BAND_Y + 8, 150, 6):
        L.hline(x0, yy, x1 - x0, S['joint'])
        off = 0 if (yy // 6) % 2 else 11
        for xx in range(x0 + off, x1, 22):
            L.vline(xx, yy - 5, 5, S['joint'])
    for k, wx in enumerate(range(x0 + 30, x1 - 20, 64)):
        m = arch_mask(30, 88, 15)
        put_mask(L, dilate(m, 2), wx - 2, 48, S['lit'], hgt=0.6)
        gy, gx = np.mgrid[0:88, 0:30].astype(np.float32)
        refl = np.clip(gx / 30.0 * 0.8 + (1 - gy / 88.0) * 1.0 - 0.45, 0, 1) * 2.4
        ladder_paint(L, m, wx, 50, refl, [SL[1], SL[2], SL[3], SK[0]], steep=2.4, hgt=0.25)
        for kk in range(1, 3):
            L.vline(wx + kk * 10, 64, 74, SL[0])
        for yy in range(72, 138, 16):
            L.hline(wx, yy, 30, SL[0])
        L.px(wx + 24, 56, SK[1])
        L.px(wx + 25, 57, SK[1])
        if k % 2 == 0:
            for kk in range(4):                                # hall lamps inside, dim
                L.px(wx + 6 + kk * 6, 90 + (kk % 2) * 4, LA[1])
        L.rect(wx + 32, 40, 4, 110, S['lit'], hgt=0.6)        # pilaster
        L.vline(wx + 35, 40, 110, S['rim'])
        L.hline(wx + 31, 40, 6, CR[2])                         # capital catches the lamp light
    L.rect(x0, 146, x1 - x0, 8, S['lit'], hgt=0.7)            # string course / cornice of the ground floor
    L.hline(x0, 146, x1 - x0, CR[2])
    L.hline(x0, 153, x1 - x0, S['deep'])
    text(L, 1590, 148, 'BAHNHOF · ВОКЗАЛ · GARE', CR[3])
    # ground floor: rusticated, arched bays
    rustication(L, x0, 154, x1 - x0, 262 - 154, S['body'], S['joint'], hi=S['lit'], course=7, block=(16, 26), seed=31)
    L.rect(x0, 154, 22, 108, S['lit'], hgt=0.6)                # corner quoins
    for yy in range(154, 262, 7):
        L.hline(x0, yy, 22 if (yy // 7) % 2 else 16, S['rim'])
    L.vline(x0, BAND_Y + 6, 262 - BAND_Y - 6, S['deep'])
    L.rect(x0, 254, x1 - x0, 8, SL[1], hgt=0.6)               # plinth
    L.hline(x0, 254, x1 - x0, SL[3])
    # --- notice case (exp_return_notice): glazed board with the trilingual official notice
    nx, ny = 1404, 196
    L.rect(nx - 2, ny - 2, 60, 46, CR[1], hgt=0.75)
    L.rect(nx, ny, 56, 42, CR[0], hgt=0.7)
    L.rect(nx + 2, ny + 2, 34, 38, SN[3], hgt=0.68)            # the notice
    L.rect(nx + 2, ny + 2, 34, 5, SL[2])
    text(L, nx + 4, ny + 3, 'BÜRO FÜR', SN[4])
    text(L, nx + 4, ny + 9, 'RÜCKFÜHRUNG', NI[2])
    text(L, nx + 4, ny + 15, 'БЮРО ВОЗВР.', SL[1])
    text(L, nx + 4, ny + 21, 'RETOURS', SL[1])
    for yy in range(ny + 28, ny + 38, 2):
        L.hline(nx + 4, yy, 28 - (yy % 4) * 2, SL[4])
    L.rect(nx + 26, ny + 32, 6, 6, RD[1])                       # official stamp
    L.rect(nx + 38, ny + 3, 15, 18, CR[4], hgt=0.68)            # two smaller notices
    for yy in range(ny + 6, ny + 20, 2):
        L.hline(nx + 40, yy, 10, SL[3])
    L.rect(nx + 38, ny + 24, 15, 15, SN[2], hgt=0.68)
    text(L, nx + 39, ny + 26, '23:40', SL[1])
    for yy in range(ny + 33, ny + 38, 2):
        L.hline(nx + 40, yy, 10, SL[3])
    L.px(nx + 54, ny + 2, SK[2])
    E['notice'] = (nx + 28, ny + 20)
    # --- waiting-room door with glass panes; the tiled stove glows inside (exp_stove)
    dx, dy, dw, dh = 1500, 188, 42, 66
    m = arch_mask(dw, dh, dw // 2)
    put_mask(L, dilate(m, 2), dx - 2, dy - 2, S['lit'], hgt=0.62)
    put_mask(L, m, dx, dy, NI[2], hgt=0.3)
    for (px0, pw) in ((dx + 3, 16), (dx + 23, 16)):              # door leaves with glazing
        L.rect(px0, dy + 22, pw, 42, CR[0], hgt=0.45)
        L.rect(px0 + 2, dy + 24, pw - 4, 22, NI[3], hgt=0.3)
        L.vline(px0 + pw // 2, dy + 24, 22, CR[0])
    sx0 = dx + 7                                                # the stove behind the left pane (green tiles)
    L.rect(sx0, dy + 26, 10, 20, PA[1], hgt=0.35)
    for yy in range(dy + 27, dy + 46, 3):
        L.hline(sx0, yy, 10, PA[0])
    for xx in range(sx0, sx0 + 10, 3):
        L.vline(xx, dy + 26, 20, PA[0])
    L.vline(sx0 + 9, dy + 26, 20, PA[3])
    L.rect(sx0 + 3, dy + 38, 4, 4, LA[2], em=LA[2])             # fire door glow
    L.px(sx0 + 4, dy + 39, LA[4], em=LA[4])
    L.rect(dx + 26, dy + 30, 10, 14, CR[1])                      # bench + travellers inside (right pane)
    tiny_person(L, dx + 28, dy + 44, 14, SL[0], head=CR[1])
    for kk in range(10):                                         # fan light above the door
        L.px(dx + dw // 2 + int(math.cos(math.radians(180 + kk * 18)) * 14), dy + 20 + int(math.sin(math.radians(180 + kk * 18)) * 14), CR[1])
    sign_board(L, dx - 12, dy - 22, ['WARTESAAL', 'ЗАЛ ОЖИДАНИЯ', "SALLE D'ATTENTE"], fg=SN[4], bg=SL[0],
               frame=CR[2], pad=1, gap=1)
    E['stove'] = (sx0 + 5, dy + 40)
    # --- Café „Korridor“: two arched shop windows (warm, emissive) and the glazed door between
    cafe = []
    for (wx, ww) in ((1566, 58), (1676, 58)):
        m = arch_mask(ww, 70, ww // 2)
        put_mask(L, dilate(m, 3), wx - 3, 181, CR[2], hgt=0.65)
        put_mask(L, dilate(m, 1), wx - 1, 183, LA[0], hgt=0.6)
        yy, xx = np.mgrid[0:70, 0:ww].astype(np.float32)
        glow = 1 - np.clip(np.sqrt(((xx - ww / 2) / (ww * 0.75)) ** 2 + ((yy - 46) / 52.0) ** 2), 0, 1)
        ladder_paint(L, m, wx, 184, 1.0 + glow * 2.9, [LA[0], LA[1], LA[2], LA[3], LA[4]], steep=2.2, hgt=0.3)
        for kk in range(3):                                      # pendant lamps
            lx = wx + 10 + kk * 19
            L.vline(lx, 184 + ww // 2 - 18, 8, LA[0])
            L.rect(lx - 3, 184 + ww // 2 - 10, 7, 3, LA[1])
            L.px(lx, 184 + ww // 2 - 7, SN[4])
        for kk in range(3):                                      # tables with patrons (warm silhouettes)
            tx = wx + 8 + kk * 18
            L.rect(tx, 234, 10, 2, LA[0])
            L.vline(tx + 5, 236, 6, LA[0])
            if (kk + wx) % 2:
                L.rect(tx - 3, 224, 4, 12, LA[0])
                L.rect(tx - 2, 220, 3, 4, LA[0])
        L.rect(wx + ww - 16, 214, 12, 20, LA[1])                 # counter with the brass coffee machine
        L.rect(wx + ww - 13, 207, 6, 7, LA[3])
        L.px(wx + ww - 11, 206, LA[4])
        L.hline(wx, 238, ww, LA[3])                              # half curtain rod; condensation below
        for yy in range(240, 254, 2):
            for xx in range(wx, wx + ww, 2):
                if (xx + yy // 2) % 3 == 0:
                    L.px(xx, yy, LA[2])
        for kk in range(1, 3):
            L.vline(wx + kk * ww // 3, 184 + ww // 2, 70 - ww // 2, LA[0])
        L.hline(wx, 184 + ww // 2, ww, LA[0])
        sub = L.c[184:254, wx:wx + ww]
        L.em[184:254, wx:wx + ww][m] = sub[m]
        cafe.append((wx, 184, ww, 70))
    ddx = 1630                                                   # café door
    L.rect(ddx - 2, 190, 44, 64, CR[2], hgt=0.62)
    L.rect(ddx, 192, 40, 62, LA[0], hgt=0.4)
    for (px0, pw) in ((ddx + 2, 17), (ddx + 21, 17)):
        L.rect(px0, 196, pw, 52, LA[2], hgt=0.3, em=LA[2])
        L.rect(px0 + 2, 198, pw - 4, 48, LA[3], hgt=0.3, em=LA[3])
        L.vline(px0 + pw - 2, 220, 8, LA[1])
    L.rect(ddx, 248, 40, 6, CR[1])
    # sign: gilded letters on a dark green fascia board
    L.rect(1562, 166, 176, 14, CR[2], hgt=0.75)
    L.rect(1563, 167, 174, 12, PA[0], hgt=0.72)
    text_center(L, 1650, 169, 'CAFÉ KORRIDOR', LA[3], font='l', em=LA[1])
    text(L, 1566, 158, 'КАФЕ', CR[3])
    text(L, 1720, 158, 'CAFÉ', CR[3])
    for k in range(1566, 1736, 2):                               # warm spill on the stone around the windows
        for yy in range(181, 184):
            if (L.c[yy, k, :3] == S['body'][:3]).all():
                L.px(k, yy, CR[1])
    E['cafe'] = cafe
    E['cafe_door'] = (ddx + 20, 254)
    # --- exchange office: barred hatch, rate board, trilingual sign
    ex = 1748
    L.rect(ex, 196, 44, 58, CR[0], hgt=0.6)
    L.rect(ex + 4, 206, 36, 22, NI[3], hgt=0.3)
    for xx in range(ex + 6, ex + 40, 4):
        L.vline(xx, 206, 22, IR[3])
    L.rect(ex + 2, 228, 40, 3, CR[3], hgt=0.75)
    L.rect(ex + 6, 234, 32, 16, SL[0], hgt=0.68)                 # rate board
    for i, (c, v) in enumerate((('DM', '1.00'), ('RBL', '0.40'), ('CHF', '0.93'))):
        text(L, ex + 8, 236 + i * 5 - (1 if i else 0), c, SN[3])
        text(L, ex + 22, 236 + i * 5 - (1 if i else 0), v, SN[4])
    sign_board(L, ex - 7, 170, ['WECHSELSTUBE', 'ОБМЕН ВАЛЮТЫ', 'CHANGE'], fg=SN[4], bg=SL[1], frame=CR[2],
               pad=1, gap=1)
    L.rect(ex + 14, 216, 6, 6, CR[3])                            # clerk behind the bars
    L.rect(ex + 13, 212, 8, 4, CR[1])
    E['exchange'] = (ex + 22, 230)
    # --- exit arch to the square: a transparent opening (the square layer shows through)
    ax, ay, aw, ah = 1836, 160, 76, 102
    m = arch_mask(aw, ah, aw // 2)
    put_mask(L, dilate(m, 4), ax - 4, ay - 4, S['lit'], hgt=0.65)
    put_mask(L, dilate(m, 2), ax - 2, ay - 2, S['rim'], hgt=0.62)
    for kk in range(15):                                         # voussoirs
        a = math.radians(180 + kk * 12)
        L.line(ax + aw / 2 + math.cos(a) * (aw / 2 + 1), ay + aw / 2 + math.sin(a) * (aw / 2 + 1),
               ax + aw / 2 + math.cos(a) * (aw / 2 + 4), ay + aw / 2 + math.sin(a) * (aw / 2 + 4), S['joint'])
    L.rect(ax + aw // 2 - 3, ay - 5, 7, 6, S['rim'])             # keystone
    L.hline(ax + aw // 2 - 3, ay - 5, 7, CR[3])
    sign_board(L, ax + 4, ay - 30, ['AUSGANG', 'ВЫХОД · SORTIE'], fg=SN[4], bg=SL[0], frame=CR[2], pad=1, gap=1)
    put_mask(L, m, ax, ay, CLEAR)
    L.c[ay:ay + ah, ax:ax + aw][m] = 0
    L.hgt[ay:ay + ah, ax:ax + aw][m] = 0
    E['arch'] = (ax, ay, aw, ah)
    # cold daylight from the arch on the jambs
    for yy in range(ay + aw // 2, ay + ah):
        L.px(ax - 1, yy, SN[1])
        L.px(ax + aw, yy, SL[3])
    flat_normal(L, x0, BAND_Y, x1 - x0, 262 - BAND_Y, (0, 0, 1))
    return L


def make_square():
    """The station square seen through the exit arch (parallax 0.85): pale sky, the 'Hotel Europa' and a
    tenement opposite (lit windows), a cream-and-red tram with lit windows, snow, a lamp post, tiny people.
    Drawn for layer x 1640..1770 (the arch is on screen only for cam >= ~1200)."""
    p = 0.85
    L = Layer(layer_w(p, 16), 262, 'square')
    x0, x1 = 1630, 1780
    L.vgrad(x0, 120, x1 - x0, 80, [SK[2], SK[3], SK[4], SK[5]])
    for (bx, bw, top, cols) in ((1630, 52, 150, (CR[2], CR[3])), (1682, 46, 138, (SL[3], SL[4])),
                                (1728, 52, 146, (CR[2], CR[3]))):
        L.rect(bx, top, bw, 220 - top, cols[0], hgt=0.5)
        L.vline(bx + bw - 1, top, 220 - top, cols[1])
        L.hline(bx, top, bw, SN[3])
        for wy in range(top + 6, 214, 9):
            for wx in range(bx + 4, bx + bw - 4, 7):
                lit = (wx * 3 + wy) % 11 == 0
                L.rect(wx, wy, 3, 5, LA[3] if lit else SL[1], em=LA[3] if lit else None)
        for k in range(6):
            L.hline(bx + k, top - 1 - k, bw - 2 * k, SL[2])
        L.hline(bx + 3, top - 7, bw - 6, SN[3])
    text(L, 1686, 142, 'HOTEL', CR[4])
    L.rect(x0, 220, x1 - x0, 42, SN[2], hgt=0.3)                 # snowy square
    for y in range(222, 262, 3):
        for x in range(x0, x1, 5):
            if (x * 7 + y) % 13 < 4:
                L.px(x, y, SN[1])
    for y in (236, 241):                                          # tram rails in the snow
        L.hline(x0, y, x1 - x0, SL[3])
    tx = 1668                                                     # tram (cream / red), lit windows
    L.rect(tx, 206, 70, 28, CR[4], hgt=0.55)
    L.rect(tx, 222, 70, 12, RD[2], hgt=0.55)
    L.hline(tx, 222, 70, RD[3])
    L.rect(tx + 4, 200, 62, 6, CR[3], hgt=0.6)
    L.hline(tx + 4, 199, 62, SN[4])
    for k in range(7):
        L.rect(tx + 4 + k * 9, 209, 7, 9, LA[3], em=LA[3])
        if k % 3 == 1:
            L.rect(tx + 6 + k * 9, 212, 2, 6, LA[1])
    L.rect(tx + 32, 188, 1, 12, IR[2])                            # pantograph pole + wire
    L.hline(x0, 186, x1 - x0, IR[2])
    text(L, tx + 2, 225, '7', SN[4])
    L.rect(tx + 6, 234, 6, 3, NI[2])
    L.rect(tx + 56, 234, 6, 3, NI[2])
    L.vline(1756, 190, 50, IR[1])                                 # lamp post
    L.rect(1754, 188, 5, 3, SN[4], em=SN[3])
    for (px_, h) in ((1648, 13), (1745, 12), (1762, 11)):
        tiny_person(L, px_, 248, h, SL[1], head=CR[2], hat=NI[2])
    return L


# =========================================================================== FOREGROUND (parallax 1.3)
def make_fg():
    """Near-black framing (parallax 1.3, width 2312): the front beam of our canopy along the top edge, two
    front cast-iron columns as edge framers (left at cam 0, right at cam 1280), the snowy front edge of the
    platform along the bottom and a bench back that drifts past around cam 640."""
    Wf = layer_w(1.3, 8)
    L = Layer(Wf, 360, 'fg_frame')
    K0, K1, K2 = NI[0], NI[1], NI[2]
    rim = SL[1]
    L.rect(0, 0, Wf, 7, K0, hgt=0.6)                              # canopy front beam
    L.hline(0, 6, Wf, K1)
    for x in range(0, Wf, 9):
        L.px(x, 3, K2)
    for (cx, w) in ((8, 16), (Wf - 30, 18)):                     # front columns (edge framers)
        L.rect(cx - w // 2, 0, w, 360, K0, hgt=0.6)
        L.vline(cx + w // 2 - 1, 0, 360, rim)
        L.vline(cx + w // 2 - 2, 0, 360, K1)
        L.rect(cx - w // 2 - 4, 8, w + 8, 6, K1)
        L.rect(cx - w // 2 - 3, 330, w + 6, 30, K1)
        for side in (-1, 1):
            for a in range(0, 91, 3):
                r = 26
                bx = cx + side * (w // 2 + int(round(r - math.cos(math.radians(a)) * r)))
                by = 6 + int(round(math.sin(math.radians(a)) * r)) - 0
                L.px(bx, max(6, 32 - by + 6), K0)
    tb = 360
    for x in range(Wf):                                           # snowy front edge of the platform
        hh = int(7 + 2 * math.sin(x / 19.0) + 1.5 * math.sin(x / 6.3))
        L.rect(x, tb - hh, 1, hh, K0, hgt=0.4)
        if (x * 7) % 5 < 3:
            L.px(x, tb - hh, SL[0])
        sn = int(2 + 1.5 * math.sin(x / 11.0 + 1) + math.sin(x / 3.7))
        for k in range(max(0, sn)):
            L.px(x, tb - hh - 1 - k, SL[1] if k == sn - 1 else SL[0])
    for x in range(0, Wf, 3):
        if math.sin(x / 31.0) + math.sin(x / 11.3) > 1.2:
            L.px(x, tb - 12 - int(2 * math.sin(x / 5.0)), SL[1])
    bx = 1000                                                     # bench back drifting through (cam ~400-1000)
    for (lx, lh) in ((bx + 4, 30), (bx + 84, 30)):
        L.rect(lx, tb - lh, 4, lh, K0)
    for k, yy in enumerate((tb - 30, tb - 24, tb - 18)):
        L.rect(bx, yy, 92, 4, K1 if k % 2 else K0, hgt=0.6)
        L.hline(bx, yy, 92, SL[0])
    return L
