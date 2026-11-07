"""env_c4p2_cine_k14 -- Kolonnenstraße 14 in the films (owner: cine stream, round 11).

LS_C4P2_Express x4 (Berlin, 22.10): the street front of No. 14 and the gap site of No. 12, plus the far layer that
pans slower behind them (parallax), the glows and the street's life (a neighbour walking home, the builders' hut's
stove smoking, a window lighting up).  LS_C4P2_Clock k1 (23.40): the dressing of the courtyard behind the same house
(courtyard_dress, called by env_c4p2_cine_clock.k1_plate before its light pools).

The house is drawn to Konrad's scale (54 px = 1.8 m, so 30 px to the metre): a Gründerzeit tenement with a
rusticated ground floor, the string course with its dentils, window surrounds with ears, triangular and segmental
pediments, consoles under the sills and recessed parapet panels, plaster scarred by the war (a few chips and
pockmarks, soot under the sills), the gate passage receding to the lit courtyard, the coal merchant's shop with its
shutter half down, the corner pub's frosted window, the gas lamp with its lamplighter's bar, the Berlin pavement
(granite slabs between mosaic stones) under trodden snow.  The windows are rooms: lace and drapes, a woman holding the
curtain aside, a man reading under a standard lamp, a family at the table under the hanging lamp with the cat on the
sill, a radio's dial in a dark room, roller blinds, the street lamp mirrored in the dark panes.

Painted flat (env_c4p2_cine_flat), original, deterministic (fixed seeds), 1 texel = 1 px of the 640 x 360 world;
the letterbox shows world rows 46..314, so everything that matters sits between them.
"""
from __future__ import annotations

import math

import numpy as np

import env_c4p2_cine_flat as FL
import env_c4p2_cine_kit as K

SNOW = '#dfe6ee'
SNOW_SH = '#9eaabf'
PAVE = 296                                      # the pavement's back edge (the house wall's foot)
GF_TOP = 184                                    # No. 14: top of the ground floor (string course 178..184)
WIN_Y = (96, 160)                               # No. 14: the Beletage windows (top, bottom)
WIN_W = 38
AXES = (678, 752, 826, 900, 974, 1048)          # No. 14: window axes (the second one over the gate)
KINDS = ('dark', 'lit_watch', 'blind', 'lit_reader', 'lit_table', 'radio')
KINDS2 = ('lit_lace', 'dark', 'dark', 'lit_lace', 'blind', 'dark')
LAMP_X = 937                                    # the gas lamp's post (between two window axes)
LAMP_HEAD = (937, 80)
HUT = (372, 452, 206, 236)                      # the builders' hut on the gap site (x0, x1, roof, hoarding top)
SMOKE = (445, 186)                              # its stovepipe's mouth
WALKER = (1062, 958, 302, 10.6)                 # the neighbour: from x, to x, feet y, start time (walks left)
WIN_ON = (0, 11.8)                              # the Beletage window (axis index) that lights up, and when
PARALLAX = 0.6                                  # the far layer pans at this fraction of the street


def _xy(F):
    return F.xx.astype(np.int64), F.yy.astype(np.int64)


def _ledge(F, x0, y, x1, h=3, col='#57555e', dark='#1e1d24', snow=True, dent=False, seed=0):
    """A projecting ledge: snow on its top, the body, a hard shadow below (dentils hang under it when dent)."""
    xx, yy = _xy(F)
    F.fill(F.box(x0, y, x1, y + h), col)
    F.fill(F.box(x0, y + 1, x1, y + 2), '#6c6a72')
    if dent:
        F.fill(F.box(x0, y + h, x1, y + h + 3) & (np.mod(xx, 4) < 2), col)
        F.fill(F.box(x0, y + h, x1, y + h + 3) & (np.mod(xx, 4) >= 2), dark)
        F.fill(F.box(x0, y + h + 3, x1, y + h + 4), dark)
    else:
        F.fill(F.box(x0, y + h, x1, y + h + 1), dark)
    if snow:
        F.fill(F.box(x0, y - 1, x1, y + 1), SNOW)
        F.fill(F.box(x0, y - 2, x1, y - 1) & (K.hash2(np.floor_divide(xx, 3), yy, 7 + seed) > 0.45), SNOW)
        F.fill(F.box(x0, y + 1, x1, y + 2) & (K.hash2(xx, yy, 9 + seed) > 0.6), SNOW_SH)


def _drape(F, x0, y0, x1, y1, col, side):
    """A heavy curtain hanging at one side, gathered at two thirds of its height, folds every 3 px."""
    xx, yy = _xy(F)
    w = x1 - x0
    tie = y0 + (y1 - y0) * 0.62
    if side == 'l':
        m = F.poly([(x0, y0), (x0 + w * 0.32, y0), (x0 + w * 0.2, tie), (x0 + w * 0.3, y1), (x0, y1)])
    else:
        m = F.poly([(x1 - w * 0.32, y0), (x1, y0), (x1, y1), (x1 - w * 0.3, y1), (x1 - w * 0.2, tie)])
    F.fill(m, col)
    F.mul(m & (np.mod(xx, 3) == 0), 0.72)
    F.fill(m & F.box(x0, tie - 1, x1, tie + 1), '#c8a050')
    F.fill(F.box(x0, y0, x1, y0 + 2), '#5a3a1e')                     # the curtain rail's pelmet
    return m


def _lace(F, m, col='#fae6bc', k=0.55):
    xx, yy = _xy(F)
    pat = m & ((np.mod(xx + yy, 4) == 0) | (np.mod(xx - yy, 4) == 0))
    F.tint(pat, col, k)
    F.tint(m & ~pat, col, k * 0.35)


def _sil(F, m, col='#2a160c'):
    F.fill(m, col)


def _fg():
    import env_c4p2_cine_figs as FG             # the figure stream's people (window figures, passers-by)
    return FG


def window(F, x0, y0, w, h, kind, seed=0):
    """One window opening (x0, y0, w, h) as a room: see the module docstring for the kinds."""
    xx, yy = _xy(F)
    x1, y1 = x0 + w, y0 + h
    op = F.box(x0, y0, x1, y1)
    tr = y0 + max(6, h // 4)
    cx = x0 + w // 2
    lit = kind.startswith('lit')
    lower = op & (yy >= tr + 2)
    if lit:
        F.grad(op, y0, y1, '#f8d488', '#c06e30', steps=4)
        F.fill(op & (yy < tr), '#ffe0a0')
    else:
        F.grad(op, y0, y1, '#1e2638', '#090d16', steps=3)
    drape = ('#7e2a20', '#3e5a2e', '#6a4424', '#5a2a48')[seed % 4]
    if kind == 'lit_watch':                     # a woman holds the curtain aside and looks down at the street
        F.paste(_fg().window_figure('curtain', w=20, h=36, light='#f8d488', seed=seed, face=1), x0 + 4, y1 - 36, clip=op)
        _drape(F, x0, y0, x1, y1, drape, 'r')
    elif kind == 'lit_reader':                  # a man reads the paper under a standard lamp, seen through lace
        F.fill(F.poly([(x0 + 5, tr + 6), (x0 + 15, tr + 6), (x0 + 13, tr + 13), (x0 + 7, tr + 13)]) & op, '#fff4c8')
        F.fill(F.box(x0 + 9, tr + 13, x0 + 11, y1) & op, '#3a2010')
        F.paste(_fg().window_figure('sit', w=20, h=30, light='#f8d488', seed=seed, face=-1), x1 - 23, y1 - 30, clip=op)
        _lace(F, lower)
        _drape(F, x0, y0, x1, y1, drape, 'l')
        _drape(F, x0, y0, x1, y1, drape, 'r')
    elif kind == 'lit_table':                   # the family at the table under the hanging lamp, the cat on the sill
        F.fill(F.line([(cx, y0), (cx, tr + 3)], 0.5) & op, '#3a2010')
        F.fill(F.ell(cx, tr + 7, 7, 4) & (yy < tr + 7) & op, '#b0602a')
        F.fill(F.box(cx - 6, tr + 7, cx + 7, tr + 8) & op, '#fff8d8')
        F.paste(_fg().window_figure('pair', w=28, h=28, light='#f8d488', seed=seed, face=1), cx - 14, y0 + h * 0.76 - 20,
                clip=op)
        F.fill(F.box(x0, y0 + h * 0.76, x1, y0 + h * 0.76 + 2) & op, '#4a2a14')
        F.fill(F.box(x0, y0 + h * 0.76 + 2, x1, y1) & op, '#7a4420')
        cat = (F.ell(x1 - 9, y1 - 5, 4.5, 5) | F.ell(x1 - 9, y1 - 12, 3.2, 3)
               | F.poly([(x1 - 12, y1 - 13), (x1 - 11, y1 - 18), (x1 - 9.5, y1 - 14)])
               | F.poly([(x1 - 8.5, y1 - 14), (x1 - 7, y1 - 18), (x1 - 6, y1 - 13)])
               | F.line([(x1 - 5, y1 - 2), (x1 - 2, y1 - 4), (x1 - 2, y1 - 9)], 0.7))
        _sil(F, cat & op, '#120a06')
        for k in range(4):
            F.fill(F.ell(x0 + 5 + k * 3, y1 - 4 - (k % 2) * 2, 2.5, 3.5) & op, '#2e4a20')
        F.fill(F.box(x0 + 2, y1 - 3, x0 + 16, y1) & op, '#8a3a1e')
        _drape(F, x0, y0, x1, y1, drape, 'l')
    elif kind == 'lit_lace':
        _lace(F, op & (yy >= tr + 2))
        _drape(F, x0, y0, x1, y1, drape, 'l')
        _drape(F, x0, y0, x1, y1, drape, 'r')
    elif kind == 'radio':                       # a dark room: the radio's dial glows green-blue on the dresser
        F.fill(F.ell(cx, y1 - 9, 11, 7) & op, '#16262a')
        F.fill(F.ell(cx, y1 - 9, 7, 4) & op, '#22403e')
        F.fill(F.box(cx - 5, y1 - 11, cx + 5, y1 - 8) & op, '#8ad0b0')
        F.fill(F.box(cx - 1, y1 - 11, cx, y1 - 8) & op, '#2a4a40')
        F.fill(F.box(x0, y1 - 6, x1, y1) & op, '#0e1416')
    elif kind == 'blind':                       # the roller shutter let down to two thirds
        sh = op & (yy < y0 + h * 0.62)
        F.fill(sh, '#4e4e58')
        F.fill(sh & (np.mod(yy, 3) == 0), '#34343c')
        F.fill(sh & (np.mod(yy, 3) == 1), '#5e5e68')
        F.fill(F.box(x0, y0 + h * 0.62, x1, y0 + h * 0.62 + 1), '#24242a')
    if not lit and kind != 'blind':             # the street lamp and the sky mirrored in the panes
        refl = op & (np.abs((xx - x0) - (y1 - yy) * 0.55 - w * 0.25) < 2.2) & (yy < y1 - 4)
        F.tint(refl, '#4a5878', 0.55)
        F.tint(op & (yy < tr), '#2a3650', 0.5)
        if kind == 'dark':
            F.tint(lower & ((np.mod(xx + yy, 4) == 0) | (np.mod(xx - yy, 4) == 0)), '#3a4258', 0.45)
    fr = '#3a2414' if lit else '#8a8c94'
    F.fill(F.box(x0, tr, x1, tr + 2), fr)
    F.fill(F.box(cx - 1, tr + 2, cx + 1, y1), fr)
    F.fill(F.box(x0 + 1, y0 + h * 0.62, x1 - 1, y0 + h * 0.62 + 1) & ~F.box(cx - 1, 0, cx + 1, 9999), fr)
    F.outline(op, col=fr, k=1.0)
    rv = op & ((xx < x0 + 2) | (yy < y0 + 2))                     # the reveal's shadow on the left and the top
    F.tint(rv, '#05060a' if not lit else '#5a3010', 0.6)
    return op


def _surround(F, x0, y0, w, h, ped=None, seed=0, panel=True):
    """The window's stucco frame with ears, the pediment (tri / seg / cap / None), the sill on two consoles and the
    recessed parapet panel below."""
    x1, y1 = x0 + w, y0 + h
    band = F.box(x0 - 3, y0 - 3, x1 + 3, y1) & ~F.box(x0, y0, x1, y1)
    F.fill(band, '#5c5a63')
    F.fill(F.box(x0 - 3, y0 - 3, x1 + 3, y0 - 2) | F.box(x0 - 3, y0 - 3, x0 - 2, y1), '#706e76')
    F.fill(F.box(x0 - 1, y0 - 1, x1 + 1, y0) | F.box(x0 - 1, y0 - 1, x0, y1), '#2e2d34')
    F.fill(F.box(x0 - 5, y0 - 3, x0 - 3, y0 + 3) | F.box(x1 + 3, y0 - 3, x1 + 5, y0 + 3), '#5c5a63')   # the ears
    F.fill(F.box(x0 + w // 2 - 3, y0 - 5, x0 + w // 2 + 3, y0 + 1), '#6a6870')                  # the keystone
    F.fill(F.box(x0 + w // 2 - 3, y0 + 1, x0 + w // 2 + 3, y0 + 2), '#2e2d34')
    if ped == 'tri':
        m = F.poly([(x0 - 7, y0 - 6), (x1 + 7, y0 - 6), (x0 + w / 2, y0 - 17)])
        F.fill(m, '#55535c')
        F.fill(m & ~F.poly([(x0 - 2, y0 - 8), (x1 + 2, y0 - 8), (x0 + w / 2, y0 - 14)]), '#6a6870')
        F.fill(F.line([(x0 - 7, y0 - 6.5), (x0 + w / 2, y0 - 17.5), (x1 + 7, y0 - 6.5)], 0.9), SNOW)
        _ledge(F, x0 - 8, y0 - 7, x1 + 8, 2, snow=False, seed=seed)
    elif ped == 'seg':
        m = F.ell(x0 + w / 2, y0 - 4, w / 2 + 8, 11) & (F.yy < y0 - 5)
        F.fill(m, '#55535c')
        F.fill(m & ~F.ell(x0 + w / 2, y0 - 4, w / 2 + 3, 7), '#6a6870')
        F.fill(m & FL.edge(m, 't'), SNOW)
        _ledge(F, x0 - 8, y0 - 6, x1 + 8, 2, snow=False, seed=seed)
    elif ped == 'cap':
        _ledge(F, x0 - 6, y0 - 9, x1 + 6, 3, seed=seed)
        F.fill(F.box(x0 - 2, y0 - 6, x1 + 2, y0 - 3) & (np.mod(F.xx.astype(np.int64), 6) < 3), '#4e4c55')
    _ledge(F, x0 - 5, y1, x1 + 5, 3, seed=seed + 1)
    for cx in (x0 + 3, x1 - 5):
        F.fill(F.poly([(cx, y1 + 3), (cx + 3, y1 + 3), (cx + 2, y1 + 8), (cx + 1, y1 + 8)]), '#57555e')
        F.fill(F.box(cx + 1, y1 + 8, cx + 3, y1 + 9), '#1e1d24')
    if panel:
        p = F.box(x0 + 2, y1 + 6, x1 - 2, y1 + 16)
        F.fill(p, '#3e3d46')
        F.fill(p & FL.edge(p, 't') | p & FL.edge(p, 'l'), '#2a2930')
        F.fill(p & FL.edge(p, 'b') | p & FL.edge(p, 'r'), '#56545c')
        F.fill(F.poly([(x0 + w / 2, y1 + 8), (x0 + w / 2 + 3, y1 + 11), (x0 + w / 2, y1 + 14),
                       (x0 + w / 2 - 3, y1 + 11)]), '#5c5a63')
    # soot run down from the sill
    xx, yy = _xy(F)
    for k in range(5):
        sx = x0 + 2 + int(K.hash2(k, seed, 811) * (w - 4))
        ln = 6 + int(K.hash2(k, seed, 812) * 18)
        F.mul(F.box(sx, y1 + 3, sx + 1, y1 + 3 + ln) & ~F.box(x0 + 2, y1 + 6, x1 - 2, y1 + 16), 0.82)


# ================================================================================================== the far layer
def street_far(W=1100):
    """The night over Kreuzberg's roofs: the sky with the city's glow, roofs and chimneys, a church tower with its
    lit clock (22.10), the S-Bahn viaduct (brick, its arches, one bricked in as a workshop with a lit window, the
    deck with the railing the train runs behind), the gap site's snowy ground and rubble beyond the hoarding."""
    F = FL.Flat(W, 360, bg='#04060c')
    xx, yy = _xy(F)
    F.grad(F.box(0, 0, W, 240), 0, 236, '#03050b', '#2a2632', steps=7)
    for k in range(46):
        sx, sy = int(K.hash2(k, 1, 901) * W), 4 + int(K.hash2(k, 2, 901) * 92)
        F.fill(F.box(sx, sy, sx + 1, sy + 1), '#c8d0e0' if K.hash2(k, 3, 901) > 0.7 else '#56607a')
    # roofs beyond the viaduct
    x = 0
    k = 0
    while x < W:
        bw = 50 + int(K.hash2(k, 1, 902) * 70)
        top = 98 + int(K.hash2(k, 2, 902) * 20)
        F.fill(F.box(x, top, x + bw, 140), '#0d1018')
        F.fill(F.poly([(x, top), (x + 8, top - 6), (x + bw - 8, top - 6), (x + bw, top)]), '#121622')
        F.fill(F.box(x + 6, top - 7, x + bw - 6, top - 6), '#5a6478')                        # snow on the ridge
        for c in range(1 + int(K.hash2(k, 3, 902) * 3)):
            chx = x + 10 + int(K.hash2(k, 10 + c, 902) * (bw - 20))
            F.fill(F.box(chx, top - 16, chx + 5, top - 4), '#151a24')
            F.fill(F.box(chx - 1, top - 17, chx + 6, top - 15), '#6a7488')
            F.fill(F.box(chx + 1, top - 19, chx + 2, top - 17) | F.box(chx + 3, top - 19, chx + 4, top - 17), '#151a24')
        for wv in range(bw // 14):
            wx = x + 6 + wv * 14
            if K.hash2(k, 20 + wv, 902) > 0.72:
                F.fill(F.box(wx, top + 6, wx + 4, top + 11), '#d8a058')
        x += bw + 2
        k += 1
    # the church tower with its lit clock face at ten past ten
    tw = F.box(506, 66, 534, 140)
    F.fill(tw, '#10141e')
    F.fill(F.poly([(504, 66), (536, 66), (520, 26)]), '#121828')
    F.fill(F.line([(520, 26), (520, 18)], 0.5), '#2a3040')
    F.fill(F.poly([(504, 66), (520, 26), (521, 26), (507, 66)]), '#3a4458')
    F.fill(F.ell(520, 84, 6, 6), '#d8c890')
    F.fill(F.line([(520, 84), (515, 81)], 0.5) | F.line([(520, 84), (526, 80)], 0.5), '#3a3020')
    F.fill(F.box(516, 100, 524, 112), '#0a0c14')
    F.fill(F.ell(520, 100, 4, 4) & (F.yy < 100), '#0a0c14')
    # the viaduct: brick courses, the arches, the deck, the railing the S-Bahn passes behind
    via = F.box(0, 138, W, 228)
    F.fill(via, '#3a2624')
    F.fill(via & (np.mod(yy, 4) == 0), '#2c1c1c')
    F.fill(via & (np.mod(xx + (np.floor_divide(yy, 4) % 2) * 4, 8) == 0) & (np.mod(yy, 4) != 0), '#30201e')
    F.speckle(via, 0.05, None, seed=903, k=0.82)
    F.fill(F.box(0, 136, W, 142), '#2a2a32')
    F.fill(F.box(0, 135, W, 137), SNOW_SH)
    F.fill(F.box(0, 126, W, 127), '#3a3c48')
    for x_ in range(0, W, 12):
        F.fill(F.box(x_, 126, x_ + 1, 136), '#3a3c48')
    for ax in range(0, W, 64):
        cxa = ax + 32
        arch = (F.ell(cxa, 196, 24, 26) | F.box(cxa - 24, 196, cxa + 24, 228))
        F.fill(arch & F.box(0, 160, W, 228), '#06070c')
        F.fill(F.ell(cxa, 196, 27, 29) & ~F.ell(cxa, 196, 24, 26) & (yy < 196) & (np.mod(xx, 3) == 0), '#4a302c')
        F.fill(F.box(cxa - 2, 166, cxa + 2, 170), '#4e3430')
        if ax == 320:                                   # bricked in: a workshop, its window lit, the door
            wall = arch & F.box(0, 168, W, 228)
            F.fill(wall, '#2e1e1c')
            F.fill(wall & (np.mod(yy, 4) == 0), '#24181a')
            F.fill(F.box(cxa - 14, 194, cxa - 2, 206), '#e0a050')
            F.fill(F.box(cxa - 9, 194, cxa - 8, 206) | F.box(cxa - 14, 199, cxa - 2, 200), '#3a2010')
            F.fill(F.box(cxa + 4, 198, cxa + 14, 228), '#1a1210')
            F.pool(F.box(0, 206, W, 240), cxa - 8, 212, 30, 12, steps=((1.0, 1.25),), col='#ffb050')
    # the gap site's ground beyond the hoarding: snow, the rubble humps, a path
    gnd = F.box(0, 226, W, 360)
    F.fill(gnd, '#4e566c')
    for k in range(14):
        hx_ = int(K.hash2(k, 1, 904) * W)
        hw = 16 + int(K.hash2(k, 2, 904) * 30)
        hump = F.ell(hx_, 232, hw, 7 + k % 4) & (yy < 232)
        F.fill(hump, '#6a7488')
        F.fill(hump & FL.edge(hump, 't'), '#a8b4c6')
        F.speckle(hump, 0.08, '#3a2622', seed=905 + k)
    F.fill(F.box(0, 226, W, 227), '#7a869c')
    return F.opaque()


# ================================================================================================== the front plate
def _hoarding(F, W):
    xx, yy = _xy(F)
    hoard = F.box(0, 236, 560, PAVE)
    F.fill(hoard, '#3e3024')
    for x in range(0, 560, 12):
        F.fill(hoard & F.box(x, 236, x + 1, PAVE), '#1e160e')
        F.fill(hoard & F.box(x + 1, 236, x + 2, PAVE), '#5a4632')
        F.mul(hoard & F.box(x + 2, 236, x + 12, PAVE) & (K.hash2(np.floor_divide(xx, 12), yy // 9, 921) > 0.7), 0.88)
    F.speckle(hoard, 0.04, None, seed=922, k=0.8)
    posters = ((296, 244, 46, 40, '#c8b890', 'RADRENNEN', 'wheel'), (348, 242, 42, 44, '#9ab0b4', 'KINO', 'star'),
               (396, 246, 50, 38, '#d8c8a0', 'KONZERT', 'lines'), (452, 242, 48, 42, '#d0a888', 'ZIRKUS', 'tent'),
               (506, 246, 44, 38, '#c8c8b8', 'TANZ', 'lines'))
    for k, (px, py, pw, ph, col, txt, pic) in enumerate(posters):
        F.fill(F.box(px - 3, py + 4, px + pw - 6, py + ph + 3), '#8a7a62')                   # an older poster under it
        po = F.box(px, py, px + pw, py + ph)
        F.fill(po, col)
        F.speckle(po, 0.06, None, seed=930 + k, k=0.9)
        F.fill(F.text(txt, px + 3, py + 3, 's') & po, '#2a2018')
        cx, cy = px + pw // 2, py + ph // 2 + 6
        if pic == 'wheel':
            F.fill((F.ell(cx, cy, 10, 10) & ~F.ell(cx, cy, 8, 8)) | F.line([(cx - 8, cy), (cx + 8, cy)], 0.4)
                   | F.line([(cx, cy - 8), (cx, cy + 8)], 0.4), '#6a2a1e')
        elif pic == 'star':
            F.fill(F.box(px + 4, py + 12, px + pw - 4, py + ph - 4), '#2a3a44')
            F.fill(F.ell(cx, cy, 5, 6) | F.box(cx - 7, cy + 5, cx + 7, py + ph - 4), '#c8b890')
        elif pic == 'tent':
            F.fill(F.poly([(cx - 14, cy + 10), (cx + 14, cy + 10), (cx, cy - 8)]) & po, '#a83a24')
            F.fill(F.poly([(cx - 14, cy + 10), (cx + 14, cy + 10), (cx, cy - 8)]) & po & (np.mod(xx, 6) < 3), '#e8d8b8')
        else:
            for ly in range(py + 14, py + ph - 4, 4):
                F.fill(F.box(px + 3, ly, px + pw - 3 - (ly % 7), ly + 1) & po, '#6a5a48')
        F.fill(F.poly([(px + pw - 12, py + ph), (px + pw, py + ph - 15), (px + pw, py + ph)]), '#3e3024')
        F.fill(F.line([(px + pw - 12, py + ph), (px + pw, py + ph - 15)], 0.5), '#efe4cc')
        F.outline(po, col='#22180f', k=0.6)
    F.fill(F.box(0, 234, 560, 237), SNOW)
    F.fill(F.box(0, 233, 560, 234) & (K.hash2(np.floor_divide(xx, 4), 1, 923) > 0.5), SNOW)
    F.fill(F.box(0, 237, 560, 238), '#2a2018')


def _hut_and_rubble(F):
    xx, yy = _xy(F)
    x0, x1, top, base = HUT
    body = F.box(x0, top + 6, x1, base)
    F.fill(body, '#3a4a3a')
    F.fill(body & (np.mod(xx, 4) == 0), '#2e3c2e')
    roof = F.ell((x0 + x1) / 2, top + 8, (x1 - x0) / 2 + 2, 5) & (yy < top + 8) | F.box(x0 - 2, top + 6, x1 + 2, top + 8)
    F.fill(roof, '#22262a')
    F.fill(F.ell((x0 + x1) / 2, top + 7, (x1 - x0) / 2, 4) & (yy < top + 6), SNOW)
    F.fill(F.box(x0 + 12, top + 10, x0 + 26, top + 20), '#e8a850')
    F.fill(F.box(x0 + 18, top + 10, x0 + 19, top + 20) | F.box(x0 + 12, top + 14, x0 + 26, top + 15), '#3a2010')
    F.fill(F.box(x0 + 48, top + 9, x0 + 62, base), '#26302a')
    F.fill(F.box(x0 + 58, top + 20, x0 + 60, top + 22), '#8a8a7a')
    F.fill(F.box(SMOKE[0] - 1, SMOKE[1] + 2, SMOKE[0] + 2, top + 6), '#1a1c20')
    F.fill(F.box(SMOKE[0] - 3, SMOKE[1], SMOKE[0] + 4, SMOKE[1] + 2), '#2a2c30')
    F.outline(body, col='#141a14', k=0.6)
    rub = F.poly([(466, 236), (488, 224), (512, 216), (536, 220), (560, 214), (590, 222), (620, 232), (634, 236)])
    F.fill(rub, '#6a7488')
    F.fill(rub & FL.edge(rub, 't', 2), '#c8d2e0')
    for k in range(22):
        bx = 476 + int(K.hash2(k, 1, 941) * 150)
        by = 222 + int(K.hash2(k, 2, 941) * 12)
        F.fill(F.box(bx, by, bx + 4, by + 2) & rub, ('#5a3226', '#4a2a22', '#3a3a40')[k % 3])
    F.fill(F.line([(548, 216), (556, 196)], 0.7) | F.line([(552, 214), (566, 200)], 0.6), '#2a2420')  # iron rods


def _litfass(F, cx=330):
    """The advertising column on the pavement's edge: plinth, the pasted column, the ring and the dome with snow."""
    xx, yy = _xy(F)
    col = F.box(cx - 12, 228, cx + 12, 302)
    F.fill(col, '#b8b0a0')
    bands = ((228, 246, '#c8a060'), (246, 262, '#d8d0c0'), (262, 280, '#8a4a36'), (280, 302, '#c0c8b8'))
    for k, (y0, y1, c) in enumerate(bands):
        F.fill(col & F.box(0, y0, 9999, y1), c)
        F.fill(F.text(('OPER', 'LOTTO', 'KINO', 'HEUTE')[k], cx - 9, y0 + 4, 's') & col, '#2a2420')
    shade = col & (xx > cx + 3)
    F.mul(shade, 0.72)
    F.mul(col & (xx > cx + 8), 0.8)
    F.lit_edge(col, k=1.15, sides='l')
    F.fill(F.box(cx - 15, 224, cx + 15, 228), '#3a4a3a')
    dome = F.ell(cx, 224, 13, 9) & (yy < 224)
    F.fill(dome, '#2e3c30')
    F.fill(F.ell(cx, 222, 11, 7) & (yy < 220), SNOW)
    F.fill(F.box(cx - 1, 210, cx + 1, 216), '#2e3c30')
    F.fill(F.box(cx - 14, 302, cx + 14, 308), '#3a4a3a')
    F.fill(F.box(cx - 14, 302, cx + 14, 303), SNOW_SH)


def _gas_lamp(F):
    x, (hx_, hy_) = LAMP_X, LAMP_HEAD
    F.fill(F.box(x - 2, hy_ + 12, x + 3, 306), '#1c1e26')
    F.fill(F.box(x - 2, hy_ + 12, x - 1, 306), '#3a3e4a')
    for y in range(160, 300, 10):
        F.fill(F.box(x - 2, y, x + 3, y + 1), '#14161c')
    F.fill(F.box(x - 11, hy_ + 40, x + 12, hy_ + 42), '#1c1e26')                    # the lamplighter's bar
    F.fill(F.box(x - 6, 286, x + 7, 308), '#1c1e26')
    F.fill(F.box(x - 8, 300, x + 9, 308), '#22242c')
    F.fill(F.box(x - 6, 286, x + 7, 288) | F.box(x - 8, 299, x + 9, 300), '#4a4e5a')
    F.fill(F.poly([(x - 4, hy_ + 12), (x + 5, hy_ + 12), (x + 3, hy_ + 18), (x - 2, hy_ + 18)]), '#1c1e26')
    glass = F.poly([(hx_ - 11, hy_ - 10), (hx_ + 12, hy_ - 10), (hx_ + 7, hy_ + 12), (hx_ - 6, hy_ + 12)])
    F.fill(glass, '#ffd890')
    F.fill(F.ell(hx_, hy_ + 2, 5, 6), '#fff4d0')
    F.fill(F.line([(hx_ + 0.5, hy_ - 10), (hx_ + 0.5, hy_ + 12)], 0.5) | F.line([(hx_ - 11, hy_ - 10), (hx_ - 6, hy_ + 12)], 0.5)
           | F.line([(hx_ + 12, hy_ - 10), (hx_ + 7, hy_ + 12)], 0.5), '#2a2a2e')
    roof = F.poly([(hx_ - 14, hy_ - 10), (hx_ + 15, hy_ - 10), (hx_ + 0.5, hy_ - 20)])
    F.fill(roof, '#1c1e26')
    F.fill(F.line([(hx_ - 14, hy_ - 10.5), (hx_ + 0.5, hy_ - 20.5), (hx_ + 15, hy_ - 10.5)], 0.8), SNOW)
    F.fill(F.box(hx_, hy_ - 25, hx_ + 1, hy_ - 20), '#1c1e26')
    F.fill(F.box(hx_ - 6, hy_ + 12, hx_ + 7, hy_ + 13), '#1c1e26')


def _house14(F, W):
    xx, yy = _xy(F)
    h14 = F.box(640, 0, W, PAVE)
    F.fill(h14, '#45434c')
    F.speckle(h14, 0.07, None, seed=951, k=0.92)
    F.speckle(h14, 0.03, None, seed=952, k=1.08)
    for k in range(9):                              # plaster chipped off: the brick shows, war pockmarks
        px = 660 + int(K.hash2(k, 1, 953) * 420)
        py = 20 + int(K.hash2(k, 2, 953) * 150)
        if k < 4:
            pm = F.ell(px, py, 6 + k * 2, 4 + k) & F.box(640, 0, W, GF_TOP)
            F.fill(pm, '#4a2c26')
            F.fill(pm & (np.mod(yy, 3) == 0), '#2e1c1a')
            F.fill(pm & FL.edge(pm, 'tl'), '#24222a')
        else:
            for j in range(6):
                qx = px + int(K.hash2(k, j, 954) * 14) - 7
                qy = py + int(K.hash2(k, j + 9, 954) * 10) - 5
                F.fill(F.box(qx, qy, qx + 1, qy + 1), '#26252c')
    # the lisenes at both ends, the downpipe
    for (a, b) in ((640, 648), (W - 8, W)):
        ls = F.box(a, 0, b, PAVE)
        F.fill(ls, '#4e4c56')
        F.fill(ls & FL.edge(ls, 'l'), '#64626c')
        F.fill(ls & FL.edge(ls, 'r'), '#2a2930')
    dp = F.box(W - 14, 0, W - 10, PAVE)
    F.fill(dp, '#2a2c34')
    F.fill(dp & FL.edge(dp, 'l'), '#5a5e6a')
    for y in range(20, PAVE, 50):
        F.fill(F.box(W - 15, y, W - 9, y + 2), '#1a1a20')
    # the second floor's sills at the top of the picture, its cornice, the Beletage and the string course
    for k, ax in enumerate(AXES):
        x0 = ax - WIN_W // 2
        window(F, x0, -6, WIN_W, 64, KINDS2[k], seed=k + 7)
        _surround(F, x0, -6, WIN_W, 64, 'cap', seed=40 + k, panel=False)
    _ledge(F, 640, 72, W, 4, dent=True, seed=3)
    for k, ax in enumerate(AXES):
        x0 = ax - WIN_W // 2
        _surround(F, x0, WIN_Y[0], WIN_W, WIN_Y[1] - WIN_Y[0], ('tri', 'seg')[k % 2], seed=20 + k)
        window(F, x0, WIN_Y[0], WIN_W, WIN_Y[1] - WIN_Y[0], KINDS[k], seed=k)
    _ledge(F, 640, 178, W, 5, col='#5a5862', dent=True, seed=5)
    # the rusticated ground floor and its granite plinth
    gf = F.box(648, GF_TOP + 4, W - 8, PAVE - 12)
    F.fill(gf & (np.mod(yy - GF_TOP, 10) == 0), '#2a2930')
    F.fill(gf & (np.mod(yy - GF_TOP, 10) == 1), '#5e5c66')
    pl = F.box(640, PAVE - 12, W, PAVE)
    F.fill(pl, '#3a3c44')
    F.speckle(pl, 0.2, '#4a4c56', seed=955)
    F.fill(pl & FL.edge(pl, 't'), '#6a6e7a')
    for x in range(640, W, 30):
        F.fill(F.box(x, PAVE - 12, x + 1, PAVE), '#24252c')
    # the caretaker's window left of the gate: lace and geraniums
    window(F, 654, 212, 34, 56, 'lit_lace', seed=2)
    _surround(F, 654, 212, 34, 56, None, seed=60, panel=False)
    for k in range(5):
        F.fill(F.ell(658 + k * 6, 264, 3, 3.5), '#2e4a20')
        F.fill(F.ell(659 + k * 6, 262, 1.2, 1.2), '#c83a2a')
    F.fill(F.box(656, 266, 688, 270), '#6a3a1e')
    # the gate passage: rusticated arch, the folded gate leaves, the vault receding to the lit courtyard
    g0, g1 = 700, 800
    gc = (g0 + g1) / 2
    vous = F.ell(gc, 226, 58, 42) & (yy < 226) & ~F.ell(gc, 226, 50, 34)
    F.fill(vous, '#56545e')
    ang = np.arctan2(yy - 226.0, xx - gc)
    F.fill(vous & (np.mod(np.floor(ang / (math.pi / 11)), 2) == 0), '#4c4a54')
    F.fill(vous & FL.edge(vous, 't'), SNOW_SH)
    F.fill(F.box(gc - 5, 182, gc + 5, 194), '#6a6870')
    F.fill(F.box(gc - 5, 182, gc + 5, 183), SNOW)
    op = (F.ell(gc, 226, 50, 34) & (yy < 226)) | F.box(g0, 226, g1, PAVE)
    F.fill(op, '#0c0c12')
    far_ = F.box(gc - 13, 244, gc + 13, PAVE - 8)                   # the courtyard at the end of the vault
    F.fill(far_, '#252a3a')
    F.fill(F.box(gc - 13, 280, gc + 13, PAVE - 8), '#5a647c')
    F.fill(F.box(gc - 13, 279, gc + 13, 280), '#7a86a0')
    F.fill(F.box(gc - 9, 252, gc - 4, 260), '#c88a46')
    F.fill(F.box(gc + 4, 250, gc + 9, 258), '#141a28')
    vault = op & ~far_
    F.fill(vault & F.poly([(g0, 200), (gc - 13, 244), (gc - 13, PAVE - 8), (g0 + 10, PAVE)]), '#17161d')
    F.fill(vault & F.poly([(g1, 200), (gc + 13, 244), (gc + 13, PAVE - 8), (g1 - 10, PAVE)]), '#111017')
    F.fill(vault & F.poly([(g0 + 10, PAVE), (gc - 13, PAVE - 8), (gc + 13, PAVE - 8), (g1 - 10, PAVE)]), '#2a2c36')
    F.fill(vault & F.poly([(g0 + 10, PAVE), (gc - 13, PAVE - 8), (gc + 13, PAVE - 8), (g1 - 10, PAVE)])
           & (np.mod(yy, 2) == 0), '#22242e')
    F.fill(F.line([(gc, 200), (gc, 226)], 0.5), '#2a2a30')
    F.fill(F.ell(gc, 230, 4, 3), '#ffe2a0')
    F.fill(F.ell(gc, 227, 5, 2) & (yy < 228), '#2a2a30')
    for (a, b) in ((g0 + 1, g0 + 9), (g1 - 9, g1 - 1)):                         # the gate leaves folded back
        lf = F.box(a, 222, b, PAVE)
        F.fill(lf, '#3a2416')
        F.fill(lf & (np.mod(yy - 222, 18) < 1), '#22140c')
        F.fill(lf & FL.edge(lf, 'l'), '#5a3a22')
    F.pool(op & ~far_, gc, 236, 44, 50, steps=((1.0, 1.2), (0.55, 1.45)), col='#ffc070')
    num = F.box(804, 198, 818, 208)
    F.fill(num, '#2a4a8a')
    F.fill(F.text('14', 806, 200, 's') & num, '#f0f0f0')
    F.outline(num, col='#e0e0e0', k=1.0)
    bell = F.box(690, 240, 696, 256)
    F.fill(bell, '#8a7a50')
    for y in range(242, 256, 3):
        F.fill(F.box(691, y, 695, y + 1), '#e8e0c8')
    # the coal merchant: fascia, the door, the shop window with its shutter half down, sacks on the pavement
    fas = F.box(822, 190, 962, 204)
    F.fill(fas, '#1e2a3e')
    F.fill(F.text('KOHLEN · KOKS · BRIKETTS', 828, 194, 's') & fas, '#d8c890')
    F.outline(fas, col='#0a0a10', k=0.8)
    F.fill(F.box(822, 189, 962, 190), SNOW)
    door = F.box(828, 212, 848, PAVE)
    F.fill(door, '#2a1c14')
    F.fill(F.box(831, 216, 845, 244), '#0e1220')
    F.fill(F.box(838, 216, 839, 244), '#2a1c14')
    F.fill(F.box(844, 262, 846, 266), '#a89060')
    disp = F.box(854, 212, 958, 284)
    F.fill(disp, '#0c101a')
    shut = disp & (yy < 250)
    F.fill(shut, '#545660')
    F.fill(shut & (np.mod(yy, 3) == 0), '#3a3c44')
    F.fill(shut & (np.mod(yy, 3) == 1), '#62646e')
    for k in range(6):                                                   # briquettes stacked behind the glass
        for j in range(3):
            F.fill(F.box(862 + k * 15, 276 - j * 5, 874 + k * 15, 280 - j * 5), '#1a1a20')
            F.fill(F.box(862 + k * 15, 276 - j * 5, 874 + k * 15, 277 - j * 5), '#3a3a44')
    F.fill(F.box(866, 256, 892, 266), '#c8c0a0')
    F.fill(F.text('PREISE', 868, 258, 's') & F.box(866, 256, 892, 266), '#2a2a2a')
    F.tint(disp & ~shut & (np.abs((xx - 854) - (284 - yy) * 0.8 - 30) < 3), '#4a5878', 0.5)
    F.outline(disp, col='#6a6c78', k=1.0)
    _ledge(F, 850, 284, 962, 3, seed=11)
    for k, sx in enumerate((928, 942)):
        sk = F.ell(sx, PAVE - 4, 7, 9) | F.box(sx - 7, PAVE - 4, sx + 7, PAVE + 4)
        F.fill(sk, ('#4a3e30', '#3e342a')[k])
        F.fill(F.ell(sx, PAVE - 11, 5, 3), SNOW)
        F.fill(F.box(sx - 3, PAVE - 13, sx + 3, PAVE - 12), '#2a2018')
    # the corner pub: frosted window with the drinkers' shadows, its lettering, the door, the hanging sign
    pw = F.box(970, 210, 1032, 276)
    F.grad(pw, 210, 276, '#f0c47a', '#c27a38', steps=3)
    for k, (dx, dy) in enumerate(((14, 0), (30, 4), (46, -2))):
        sil = F.ell(970 + dx, 248 + dy, 5, 6) | F.ell(970 + dx, 262 + dy, 9, 8)
        F.tint(sil & pw, '#6a3a1a', 0.55)
    F.fill(F.box(970, 210, 1032, 222), '#e8b468')
    F.fill(F.text('SCHANKWIRTSCHAFT', 972, 213, 's') & pw, '#5a2e12')
    F.fill(F.box(1000, 222, 1002, 276) | F.box(970, 244, 1032, 245), '#3a2010')
    F.outline(pw, col='#2a1408', k=1.0)
    _surround(F, 970, 210, 62, 66, None, seed=70, panel=False)
    pd = F.box(1040, 212, 1062, PAVE)
    F.fill(pd, '#3a2416')
    F.fill(F.box(1044, 218, 1058, 246), '#d8a058')
    F.fill(F.box(1050, 218, 1051, 246), '#3a2416')
    F.fill(F.box(1064, 196, 1080, 198), '#1a1a20')
    sg = F.ell(1074, 206, 7, 7)
    F.fill(sg, '#b8241a')
    F.fill(F.text('BIER', 1067, 204, 's') & sg, '#f0e0c0')
    F.fill(F.ell(1074, 198, 7, 2) & (yy < 199), SNOW)


def _pavement(F, W):
    """Granite slabs between mosaic stones under trodden snow, a ridge along the wall, prints, the curb, the road."""
    xx, yy = _xy(F)
    pv = F.box(0, PAVE, W, 312)
    F.fill(pv, '#7c869c')
    mos = pv & ((yy < 299) | (yy >= 307)) & ((np.mod(xx + yy * 2, 3) == 0) | (np.mod(yy, 2) == 0))
    F.fill(mos & (K.hash2(np.floor_divide(xx, 6), yy // 3, 961) > 0.5), '#5a6276')
    slab = F.box(0, 299, W, 307)
    trod = slab & (K.hash2(np.floor_divide(xx, 22), 1, 962) > 0.35)
    F.fill(trod, '#5e6678')
    F.fill(trod & (np.mod(xx, 22) == 0), '#3e4454')
    F.fill(trod & (K.hash2(xx, yy, 963) > 0.86), '#8a94a8')
    F.fill(F.box(0, PAVE, W, PAVE + 2) & (K.hash2(np.floor_divide(xx, 5), 2, 964) > 0.3), SNOW)
    for k in range(70):
        px = int(K.hash2(k, 1, 965) * W)
        py = 300 + (k % 3) * 3
        F.fill(F.box(px, py, px + 3, py + 1), '#4e566a')
    curb = F.box(0, 312, W, 316)
    F.fill(curb, '#6a7080')
    F.fill(F.box(0, 311, W, 313) & (K.hash2(np.floor_divide(xx, 7), 3, 966) > 0.25), SNOW)
    road = F.box(0, 316, W, 360)
    F.fill(road, '#2a3040')
    row_ = np.floor_divide(yy - 316, 6)
    cob = road & ((np.mod(yy - 316, 6) == 0) | (np.mod(xx + (row_ % 2) * 5, 10) == 0))
    F.fill(cob, '#1a1e2a')
    F.fill(cob & (K.hash2(np.floor_divide(xx, 10), row_, 61) > 0.45), '#7a86a4')
    for ty in (328, 344):
        F.fill(F.box(0, ty, W, ty + 3) & road, '#22283a')


def street_front(W=1100, x4_lamp=(610, 226)):
    """No. 12's gap site and No. 14 with the pavement (RGBA; clear above the hoarding so the far layer shows)."""
    F = FL.Flat(W, 360, bg='#000000')
    xx, yy = _xy(F)
    _hoarding(F, W)
    _hut_and_rubble(F)
    bar = F.box(480, 264, 640, 278)                             # the barrier with its warning lamp (x4a's match)
    F.fill(bar, '#e8e0d4')
    F.fill(bar & (np.mod(xx - yy, 30) < 15), '#b8241a')
    F.outline(bar, col='#1a0e0a', k=0.5)
    F.fill(F.box(480, 262, 640, 264), SNOW)
    for lx in (492, 628):
        F.fill(F.line([(lx - 6, PAVE + 6), (lx, 278)], 0.9) | F.line([(lx + 6, PAVE + 6), (lx, 278)], 0.9), '#2a2018')
    F.fill(F.box(x4_lamp[0] - 2, x4_lamp[1] + 6, x4_lamp[0] + 2, 278), '#1a1c20')
    lamp = F.ell(x4_lamp[0], x4_lamp[1], 6, 6)
    F.fill(lamp, '#e83a24')
    F.fill(F.ell(x4_lamp[0] - 1, x4_lamp[1] - 1, 2, 2), '#ffb08a')
    F.outline(lamp, col='#3a0402', k=0.5)
    F.fill(F.ell(x4_lamp[0], x4_lamp[1] - 6, 5, 2) & (yy < x4_lamp[1] - 5), SNOW)
    _house14(F, W)
    _pavement(F, W)
    _litfass(F)
    _gas_lamp(F)
    # light: the gas lamp on the facade and the snow, the pub, the passage, the caretaker, the warning lamp
    wall = F.box(640, 0, W, PAVE)
    F.pool(wall, LAMP_HEAD[0], LAMP_HEAD[1] + 30, 130, 120, steps=((1.0, 1.06), (0.66, 1.14), (0.36, 1.22)),
           col='#ffd890')
    ground = F.box(0, PAVE, W, 316)
    F.pool(ground, LAMP_X, 304, 150, 16, steps=((1.0, 1.1), (0.6, 1.2), (0.3, 1.32)), col='#ffd890')
    F.pool(ground, 1001, 300, 50, 9, steps=((1.0, 1.12), (0.5, 1.26)), col='#ffb860')
    F.pool(ground, 750, 300, 56, 10, steps=((1.0, 1.1), (0.5, 1.2)), col='#ffc070')
    F.pool(ground, 671, 300, 30, 7, steps=((1.0, 1.12),), col='#ffb860')
    F.pool(ground | bar, x4_lamp[0], 298, 50, 12, steps=((1.0, 1.1),), col='#ff6a50')
    return F.rgba()


def street_glows(W=1100, x4_lamp=(610, 226)):
    blobs = [(x4_lamp[0], x4_lamp[1], 22, 18, (120, 26, 12), 1.5),
             (LAMP_HEAD[0], LAMP_HEAD[1], 46, 36, (110, 84, 46), 1.5),
             (750, 234, 26, 20, (90, 62, 26), 1.5),
             (1001, 244, 44, 34, (70, 46, 18), 1.4),
             (671, 240, 18, 22, (50, 32, 12), 1.4),
             (HUT[0] + 19, HUT[2] + 15, 10, 7, (70, 44, 14), 1.5)]
    return K.glow_sprite(W, K.VH, blobs, 8.0)


# ================================================================================================== the street's life
def lamp_backdrop():
    """LS_C4P2_Express x4a (round 11b): what stands behind the building site's warning lamp in the close shot, the
    first frame in Berlin -- across the gap site the far layer (the roofs, the church tower with its lit clock at ten
    past ten, the viaduct and the bricked-in arch's lit window) and, on the right, No. 14's corner nearer and larger
    than in the street shot: the quoins, the firewall's edge with the ghost of the bombed neighbour's floors, two
    floors of windows in their surrounds (the same rooms as in the street: the woman at the curtain, the dark
    Beletage window that lights up later, lace, a blind), ledges and sills under snow, the gas lamp's warmth from the
    right; all of it a step back in the night haze, since the lens is focused on the lamp.  Opaque 640 x 360; the
    hoarding and the barrier (express.lamp_macro) cover it from y 230 down."""
    F = FL.Flat(640, 360, bg='#04060c')
    xx, yy = _xy(F)
    F.paste(street_far(1100)[:, 300:940], 0, 0)
    c0 = 404                                                   # No. 14's corner
    fw = F.box(380, 0, c0, 252)                                # the firewall, seen edge-on past the corner
    F.fill(fw, '#2a2830')
    F.fill(fw & (np.mod(yy, 4) == 0) & (np.mod(xx + yy, 3) == 0), '#24222a')
    for (ya, yb, c) in ((58, 112, '#332e34'), (128, 196, '#2e3234')):     # the neighbour's rooms: old distemper
        F.fill(fw & (yy >= ya) & (yy < yb) & (xx > 384), c)
    for y in (54, 122, 200):                                   # its floors' scars
        F.fill(fw & (yy >= y) & (yy < y + 3), '#3c3a42')
        F.fill(fw & (yy == y + 3), '#18171c')
    F.fill(F.line([(386, 196), (400, 128)], 0.6), '#3a3840')   # the stair's trace
    F.fill(F.box(379, 0, 380, 252), '#16151a')
    fa = F.box(c0, 0, 640, 252)                                # the street front
    F.fill(fa, '#45434c')
    F.speckle(fa, 0.07, None, seed=961, k=0.92)
    F.speckle(fa, 0.03, None, seed=962, k=1.08)
    for k in range(5):                                         # war pockmarks
        px, py = 430 + int(K.hash2(k, 1, 963) * 200), 30 + int(K.hash2(k, 2, 963) * 180)
        for j in range(5):
            qx, qy = px + int(K.hash2(k, j, 964) * 12) - 6, py + int(K.hash2(k, j + 9, 964) * 8) - 4
            F.fill(F.box(qx, qy, qx + 1, qy + 1), '#26252c')
    q = F.box(c0, 0, c0 + 12, 252)                             # the quoins
    F.fill(q, '#4e4c56')
    for k, y in enumerate(range(-4, 252, 14)):
        F.fill(F.box(c0, y, c0 + (12 if k % 2 else 8), y + 13), '#55535c')
        F.fill(F.box(c0, y + 13, c0 + 12, y + 14), '#2a2930')
    F.fill(F.box(c0, 0, c0 + 1, 252), '#6c6a74')
    _ledge(F, c0, 120, 640, 5, col='#5a5862', dent=True, seed=11)          # the string course
    w, h = 44, 70
    for k, x0 in enumerate((440, 529, 618)):                   # the second floor: sills at the top of the picture
        window(F, x0, 24, w, 72, KINDS2[k], seed=k + 7)
        _surround(F, x0, 24, w, 72, 'cap', seed=40 + k)
    for k, x0 in enumerate((440, 529, 618)):                   # the Beletage: the same rooms as in the street
        _surround(F, x0, 150, w, h, ('tri', 'seg')[k % 2], seed=20 + k)
        window(F, x0, 150, w, h, KINDS[k], seed=k)
    # the gas lamp beyond the right edge warms the facade; the night haze over everything (the lens is on the lamp)
    F.pool(fa | fw, 700, 196, 300, 230, steps=((1.0, 1.03), (0.82, 1.06), (0.64, 1.09), (0.46, 1.12), (0.3, 1.15)),
           col='#f0c080')
    bg = F.box(0, 0, 640, 252)
    hot = bg & (F.rgb.max(axis=-1) > 0.62)
    F.tint(bg & ~hot, '#0c1222', 0.28)
    F.mul(bg & ~hot, 0.9)
    F.pool(bg & ~hot, 44, 200, 26, 18, steps=((1.0, 1.1), (0.6, 1.2)), col='#ffb050')       # the workshop's window
    return F.opaque()


def win_on_sprite():
    """The Beletage window at axis WIN_ON[0] lit (it is dark on the plate): (rgba, x, y)."""
    ax = AXES[WIN_ON[0]]
    x0 = ax - WIN_W // 2
    h = WIN_Y[1] - WIN_Y[0]
    F = FL.Flat(WIN_W, h, ox=x0, oy=WIN_Y[0], bg='#000000')
    window(F, x0, WIN_Y[0], WIN_W, h, 'lit_lace', seed=3)
    F.pool(F.box(x0, WIN_Y[0], x0 + WIN_W, WIN_Y[1]), LAMP_HEAD[0], LAMP_HEAD[1] + 30, 130, 120,
           steps=((1.0, 1.06), (0.66, 1.14), (0.36, 1.22)), col='#ffd890')
    return F.rgba(), x0, WIN_Y[0]


def smoke_sheet():
    return K.puff_sheet(8, 18, 24, ['#2a2c34', '#3a3c46', '#4e505a', '#62646e'], 971, grow=(0.25, 0.5), thin=0.6,
                        light=(0.6, -0.5), drift=0.2)


def walker_sheet():
    """The neighbour walking home from the pub (berlin_father on the rig, walking left, the gas lamp behind him)."""
    sh, n, w = _fg().passerby_sheet('berlin_father', flip=True, key='left', mul=(0.82, 0.86, 1.02), rim=(170, 150, 110))
    return sh, n, w


def layout():
    return dict(x4_parallax=PARALLAX, x4_walker=list(WALKER), x4_smoke=list(SMOKE), x4_win_on_t=WIN_ON[1])


# ================================================================================================== k1 the courtyard
def courtyard_dress(F, Y, hanna, base_win, gate):
    """Clock k1: the side wing's plaster (patched, sooty, the brick showing where it fell off), stucco frames round
    the first-floor windows, neighbours behind the curtains, a sled against the wall, prints
    from the door to the bins, the lit windows' light lying on the snow.  Never touches the cobbler's basement
    window (base_win)."""
    xx, yy = _xy(F)
    keep = F.box(base_win[0] - 2, base_win[1] - 2, base_win[2] + 2, base_win[3] + 2)
    wall = np.zeros(F.a.shape, bool)
    for c in ('#3a3e50', '#34384a', '#33364a'):
        wall |= np.all(np.abs(F.rgb - FL.hx(c)) < 0.004, axis=-1)
    wall &= ~keep & (yy < Y['plinth'])
    F.speckle(wall, 0.08, None, seed=981, k=0.9)
    F.speckle(wall, 0.03, None, seed=982, k=1.1)
    for k in range(6):
        px = 90 + int(K.hash2(k, 1, 983) * 500)
        py = 20 + int(K.hash2(k, 2, 983) * 280)
        pm = F.ell(px, py, 7 + k * 2, 4 + k) & wall
        F.fill(pm, '#4a2c26')
        F.fill(pm & (np.mod(yy, 3) == 0), '#2e1c1a')
    for x in range(80, 640, 23):                                        # soot run down from the eaves
        ln = 20 + int(K.hash2(x, 1, 984) * 60)
        F.mul(F.box(x, Y['eaves'], x + 2, Y['eaves'] + ln) & wall, 0.86)
    gfz = wall & (yy > Y['gf_top'] + 4) & (yy < Y['plinth'] - 2)             # the ground floor's rustication
    F.fill(gfz & (np.mod(yy - Y['gf_top'], 12) == 0), '#2a2e3c')
    F.fill(gfz & (np.mod(yy - Y['gf_top'], 12) == 1), '#4a4e60')
    # the workshop window: lettering on the glass, boots on the shelf, the back room's door ajar with its light
    sx0, sy0, sx1, sy1 = 290, Y['gf_top'] + 30, 490, Y['plinth'] - 14
    shop = F.box(sx0 + 1, sy0 + 1, sx1 - 1, sy1 - 1)
    F.fill(F.box(456, sy0 + 22, 476, sy1 - 2), '#2a1a10')
    F.fill(F.box(458, sy0 + 24, 462, sy1 - 2), '#c88a46')
    F.pool(shop, 460, sy1 - 30, 70, 60, steps=((1.0, 1.5), (0.5, 1.9)), col='#ffb050')
    for k in range(7):
        bx = 302 + k * 20
        boot = F.poly([(bx, sy1 - 46), (bx + 5, sy1 - 46), (bx + 5, sy1 - 36), (bx + 11, sy1 - 34), (bx + 11, sy1 - 30),
                       (bx, sy1 - 30)])
        F.fill(boot, ('#3a2416', '#2a1a10', '#4a2e1a')[k % 3])
        F.fill(boot & FL.edge(boot, 't'), '#6a4a2e')
    F.fill(F.box(sx0 + 4, sy1 - 30, sx1 - 4, sy1 - 28), '#3a3a44')
    F.fill(F.text('REPARATUREN  BESOHLUNGEN', sx0 + 12, sy0 + 8, 's') & shop, '#c8a860')
    for x in (355, 425):
        F.fill(F.box(x, sy0, x + 2, sy1), '#2a2c38')
    # the yard lamp by the house door
    F.fill(F.box(512, Y['gf_top'] + 30, 516, Y['gf_top'] + 32), '#1a1c24')
    F.fill(F.box(509, Y['gf_top'] + 32, 519, Y['gf_top'] + 44), '#ffe0a0')
    F.fill(F.poly([(507, Y['gf_top'] + 32), (521, Y['gf_top'] + 32), (514, Y['gf_top'] + 26)]), '#1a1c24')
    F.fill(F.box(507, Y['gf_top'] + 31, 521, Y['gf_top'] + 32), SNOW)
    F.pool(wall | gfz, 514, Y['gf_top'] + 40, 70, 60, steps=((1.0, 1.08), (0.55, 1.18), (0.3, 1.3)), col='#ffd890')
    # stucco frames and neighbours on the first floor
    hx0, hy0, hx1, hy1 = hanna
    w, h = hx1 - hx0, hy1 - hy0
    for k, x in enumerate((110, 230, 330, hx0, 530)):
        fr = F.box(x - 4, hy0 - 4, x + w + 4, hy1) & ~F.box(x - 1, hy0 - 1, x + w + 1, hy1 + 3)
        F.fill(fr, '#4e5264')
        F.fill(fr & FL.edge(fr, 't'), '#626678')
        F.fill(F.box(x + w // 2 - 3, hy0 - 7, x + w // 2 + 3, hy0 - 2), '#56596c')
        _ledge(F, x - 6, hy0 - 9, x + w + 6, 2, col='#4e5264', seed=990 + k)
    for x, side in ((230, 1), (330, -1)):                               # neighbours watch the car leave
        cx = x + w / 2 + side * 6
        if x == 330:                                                    # a dark room: only the face and the hand
            F.fill(F.ell(cx, hy0 + 20, 3.5, 4.2), '#4a3a36')
            F.fill(F.ell(cx + side * -5, hy0 + 26, 2, 1.6), '#4a3a36')
            F.fill(F.box(x + 2, hy0 + 2, x + 6, hy1 - 2), '#2a3044')
        else:
            F.paste(_fg().window_figure('lean', w=18, h=28, light='#f0b860', seed=5, face=1), x + w / 2 - 9, hy1 - 28,
                    clip=F.box(x, hy0, x + w, hy1))
    # the yard: a sled against the wall, prints in the snow, the windows' light on the snow
    yd0 = Y['yard']
    sled = F.poly([(612, Y['plinth'] + 6), (620, Y['plinth'] + 4), (626, yd0 - 2), (618, yd0)])
    F.fill(sled, '#6a4424')
    F.fill(F.line([(611, Y['plinth'] + 8), (617, yd0 + 2)], 0.7), '#2a2c34')
    for k in range(16):                                                 # prints: the door's steps to the bins
        u = k / 15.0
        px = 548 + u * 48 + (k % 2) * 3
        py = Y['plinth'] + 40 + u * 34
        if py > yd0 + 2:
            F.fill(F.box(px, py, px + 3, py + 1), '#3e4660')
    for (wx0, wx1) in ((200, 240), (hx0, hx1)):
        F.pool(F.box(0, yd0, 640, yd0 + 120), (wx0 + wx1) / 2, yd0 + 30, 40, 14, steps=((1.0, 1.08),), col='#ffb050')
