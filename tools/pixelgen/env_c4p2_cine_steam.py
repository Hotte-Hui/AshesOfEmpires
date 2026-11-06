"""env_c4p2_cine_steam -- LS_C4P2_Steam (12.5 s): Karsk -> Berlin, Monday.  The steam jet is ONE shape and ONE
sound across the cut.

  m1 side_on          the coal stage before the sun: the timber trestle with its bunker and the steel chute, the
                      special-run engine (Л-2238) and its tender under it -- coal rattling down -- in the amber of the
                      floodlight mast; at the right three men stretch a tarpaulin on poles "for tomorrow" in front of
                      the heap where Kolonne 4 shovels; Alexei, dark against the light, watches from the foreground
  m2 macro_locked     the engine's twin pop valves on the boiler's crown blow off: the white jet at JET_BASE; behind,
                      the trestle and the mast's lamps against the dawn
  m3 macro_to_medium  Berlin, Ostbahnhof 20.30: the same jet at the same place from the express engine's valve under
                      the iron and glass of the roof (m3a), hard cut on the jet (CUT_M3) to the hall: the express at
                      platform K, the split-flap board flipping to D 303 KARSK 21.10 (m3b)
  m4 establishing     platform K in three depths: travellers boarding at the carriages, people on the platform, a
                      clear lane in front where Konrad comes in from the left and stops; the buffet with Marta in her
                      driver's coat under its lamp, the kiosk with the man and his newspaper
Painted flat (env_c4p2_cine_flat), the engines by env_c4p2_cine_loco, people on the game's rig.
Outputs assets/cinematics/c4p2/steam/*.png; anchors in layout.json "steam".
"""
from __future__ import annotations

import math

import numpy as np

import env_c4p2_cine_flat as FL
import env_c4p2_cine_kit as K
import env_c4p2_cine_loco as LO
import env_c4p2_cine_pal as PAL
import env_c4p2_cine_people as PP
import env_c4p2_cine_places as PL
import env_c4p2_cine_rig as R
from env_c4p2_cine_kit import GB

L = K.LAYOUT.setdefault('steam', {})
PAL_B = PAL.BERLIN_ST
JET_BASE = (320, 168)                    # the valve mouth in m2 AND m3a (the match cut)
JET_SIZE = (120, 240)
RAIL = 300

# ------------------------------------------------------------------------------------------------ m1
M1_LOCO_X = 30                          # smokebox end (the engine faces left)
M1_CHUTE = (452, 126, 424, 190)         # chute: top (x0, y0) -> mouth (x1, y1): coal falls from (x1, y1)
M1_POLES = (508, 552, 596, 640)
M1_WORKERS = (('worker_b', 530, {'coat': '#3a3e46'}), ('porter', 574, {'coat': '#4a3a2c'}),
              ('worker_a', 618, {'coat': '#2e3a2c'}))
TARP_T = (0.4, 3.5)                     # the last section rises over this span
TARP_SNAPS = (1.55, 3.05)               # the canvas cracks taut in the wind (c4p2cine_coal)
COAL_RUN = (0.25, 3.7)                  # coal rattles down the chute (c4p2cine_coal)
MAST = (560, 52)
AMBER = (1.1, 0.95, 0.78)
RIM_A = (255, 196, 120)


def m1_plate():
    """The coal stage at dawn in the floodlight: sky, town and cooling tower, the mast, the trestle and its bunker,
    the chute, the coal heap behind the tarpaulin line, the engine and tender, the yard's snow on cinders."""
    F = FL.Flat(bg='#05070c')
    sky = F.box(0, 0, 640, 220)
    F.grad(sky, 0, 220, '#0a0e1c', '#3a3450', steps=7)
    F.pool(sky, 120, 220, 300, 70, steps=((1.0, 1.25), (0.55, 1.5)), col='#8a5a4a')
    for (x0, x1, top) in ((0, 80, 196), (70, 150, 186), (150, 220, 200), (380, 460, 192), (600, 640, 188)):
        b = F.box(x0, top, x1, 222)
        F.fill(b, '#141826')
        for wy in range(top + 4, 218, 6):
            for wx in range(x0 + 3, x1 - 2, 6):
                if K.hash2(wx, wy, 13) > 0.72:
                    F.fill(F.box(wx, wy, wx + 2, wy + 2), '#d89848')
    cx, w = 236, 26
    pts = []
    for k in range(13):
        t = k / 12.0
        hw = w * (1.0 - 0.36 * math.sin(math.pi * min(1.0, t * 1.2)))
        pts.append((cx - hw, 222 - t * 100))
    tw = F.poly(pts + [(2 * cx - x, y) for (x, y) in reversed(pts)])
    F.fill(tw, '#1a1e2c')
    F.fill(tw & (F.xx > cx + 4), '#22283a')
    F.outline(tw, col='#0c0e16', sides='lr')
    for (px, py, r) in ((cx - 2, 116, 15), (cx + 10, 100, 18), (cx + 2, 82, 20), (cx + 22, 64, 22), (cx + 44, 50, 20),
                        (cx + 66, 42, 16)):
        pf = F.ell(px, py, r, r * 0.78)
        F.fill(pf, '#4a4656')
        F.fill(pf & ~F.ell(px - 3, py + 3, r, r * 0.78), '#6a5e66')
        F.fill(pf & (F.yy > py + r * 0.35), '#3a3646')
    # the yard: cinders and snow, tracks
    gnd = F.box(0, 220, 640, 360)
    F.fill(gnd, '#3c4252')
    xx, yy = F.xx.astype(np.int64), F.yy.astype(np.int64)
    F.fill(gnd & (yy > 236), '#465064')
    for k, y in enumerate((228, 240, 256, 276)):
        F.fill(F.box(0, y, 640, y + 1), '#2e3442')
        F.fill(F.box(0, y + 1, 640, y + 2), '#56607a')
    F.fill(gnd & (yy > RAIL + 6), '#566078')
    for k in range(10):
        x0_ = 10 + k * 66 + (k * 23) % 31
        dr = F.ell(x0_, 322 + (k % 3) * 10, 30 + (k * 11) % 18, 5)
        F.fill(dr & gnd & (yy > RAIL + 6), '#7a86a0')
        F.fill(dr & FL.edge(dr, 't') & (yy > RAIL + 6), '#b4bfcc')
    for x in range(0, 640, 11):
        F.fill(F.box(x, RAIL + 1, x + 7, RAIL + 5), '#2a221c')
    F.fill(F.box(0, RAIL - 1, 640, RAIL + 1), '#8a929c')
    F.fill(F.box(0, RAIL - 1, 640, RAIL), '#d0b088')
    # the floodlight mast (lattice) and its lamp cluster
    mx, my = MAST
    mast = F.box(mx - 3, my, mx + 3, RAIL)
    F.fill(mast, '#1a1e26')
    for y in range(my + 2, RAIL, 8):
        F.fill(F.line([(mx - 3, y), (mx + 3, y + 8)], 0.5) | F.line([(mx + 3, y), (mx - 3, y + 8)], 0.5), '#2c323e')
    head = F.box(mx - 12, my - 8, mx + 12, my + 2)
    F.fill(head, '#20242c')
    for k in range(4):
        F.fill(F.box(mx - 10 + k * 6, my - 6, mx - 6 + k * 6, my - 1), '#fff4d0')
    F.outline(head, col='#0a0c10')
    # the coal heap at the right (Kolonne 4's) and the trestle with its bunker
    heap = F.poly([(470, 300), (520, 236), (560, 214), (610, 220), (640, 232), (640, 300)])
    F.fill(heap, '#121216')
    F.fill(heap & (K.hash2(np.floor_divide(xx, 3), np.floor_divide(yy, 2), 51) > 0.55), '#1e1e26')
    F.fill(heap & (K.hash2(xx, yy, 52) > 0.97), '#c89a5a')
    F.fill(heap & FL.edge(heap, 't', 2), '#dfe6ee')
    for x0 in (360, 420, 480):
        leg = F.box(x0, 116, x0 + 8, RAIL)
        F.fill(leg, '#4a3626')
        F.fill(leg & FL.edge(leg, 'l', 2), '#6a5038')
        F.outline(leg, col='#1a120a')
    for (a, b) in ((360, 420), (420, 480)):
        for y in (150, 210, 262):
            F.fill(F.line([(a + 8, y), (b, y + 46)], 1.2) | F.line([(b, y), (a + 8, y + 46)], 1.2), '#3a2a1c')
        F.fill(F.box(a, 146, b + 8, 151), '#5a4430')
    deck = F.box(350, 108, 500, 118)
    F.fill(deck, '#5a4430')
    F.fill(deck & FL.edge(deck, 't'), '#dfe6ee')
    F.outline(deck, col='#1a120a')
    bunk = F.poly([(358, 64), (494, 64), (494, 108), (358, 108)])
    F.fill(bunk, '#4a3626')
    for k, x in enumerate(range(358, 494, 9)):
        F.fill(bunk & F.box(x, 64, x + 1, 108), '#2e2016')
        F.fill(bunk & F.box(x + 1, 64, x + 2, 108), '#6a5038')
    for y in (78, 94):
        F.fill(F.box(356, y, 496, y + 3), '#2a2a30')
    coal_top = F.poly([(358, 64), (380, 52), (420, 46), (470, 50), (494, 64)])
    F.fill(coal_top, '#121216')
    F.fill(coal_top & (K.hash2(np.floor_divide(xx, 3), np.floor_divide(yy, 2), 53) > 0.55), '#22222a')
    F.fill(coal_top & FL.edge(coal_top, 't', 2), '#dfe6ee')
    F.outline(bunk, col='#1a120a')
    lad = F.box(500, 64, 506, RAIL)
    F.fill(lad & (np.mod(yy, 8) < 2), '#5a4430')
    F.fill(F.box(500, 64, 501, RAIL) | F.box(505, 64, 506, RAIL), '#5a4430')
    # the chute: a steel trough from the bunker down to the tender, its gate lever
    c0x, c0y, c1x, c1y = M1_CHUTE
    ch = F.poly([(c0x - 10, c0y - 18), (c0x + 10, c0y - 14), (c1x + 9, c1y + 3), (c1x - 9, c1y - 2)])
    F.fill(ch, '#3a3e46')
    F.fill(ch & FL.edge(ch, 't', 2), '#8a929c')
    F.fill(F.line([(c0x - 6, c0y - 14), (c1x - 4, c1y)], 0.8), '#121216')
    F.outline(ch, col='#0a0c10')
    F.fill(F.line([(c0x + 12, c0y - 12), (c0x + 30, c0y - 34)], 1.0), '#2a2e34')
    F.fill(F.ell(c0x + 30, c0y - 34, 3, 3), '#8e1e16')
    # the engine and tender (the tender under the chute)
    lo = LO.SideLoco(F, M1_LOCO_X, RAIL, m=26.0, facing=-1, kind='soviet', number='Л-2238', crank=0.9, snow=True,
                     lit=1).paint().tender(coal=True, number='Л-2238').finish()
    # light: the floodlight's stepped pools on the ground, the trestle, the tender; the far left in the dawn blue
    lit_all = F.a.copy()
    F.pool(gnd, mx - 60, RAIL + 10, 300, 52, steps=((1.0, 1.08), (0.6, 1.22), (0.3, 1.38)), col='#ffc070')
    F.pool(F.box(330, 0, 640, 300), mx - 40, 160, 220, 200, steps=((1.0, 1.05), (0.6, 1.14)), col='#ffc070')
    F.tint(F.box(0, 0, 220, 360) & ~sky, '#5a6a9a', 0.12)
    return F.opaque(), lo


def tarp_frames():
    """The last tarpaulin section rising between the right poles: 6 frames from slack to taut; canvas in flat
    panels with seams, lit by the floodlight, snow sliding off its top."""
    out = []
    a, b = M1_POLES[2] + 3, M1_POLES[3]
    for i in range(6):
        u = i / 5
        F = FL.Flat(bg='#000000')
        top = 290 - (290 - 200) * u
        belly = (1 - u) * 26 + 4
        m = F.poly([(a, top), (b, top), (b, 290), (a, 290)]) & \
            (F.yy > top + belly * np.sin((F.xx - a) / (b - a) * math.pi) - 2)
        if u < 0.15:
            m = F.ell((a + b) / 2, 292, (b - a) / 2, 6)
        F.fill(m, '#5a5c48')
        for k, x in enumerate(range(a, b, 10)):
            F.fill(m & F.box(x, 0, x + 4, 360), '#4a4c3a' if k % 2 else '#6a6c54')
        F.fill(m & FL.edge(m, 't', 2), '#dfe6ee' if u > 0.5 else '#8a8c74')
        F.outline(m, col='#22241a', sides='lrb')
        F.pool(m, 560, 200, 120, 110, steps=((1.0, 1.08), (0.5, 1.2)), col='#ffc070')
        out.append(F.rgba())
    return out


def m1_workers():
    out = []
    for i, (cid, x, cols) in enumerate(M1_WORKERS):
        sh, n, w = PP.sheet(cid, R.tarp_poses(), R.tarp_setup, 48, i == 1, key='right', mul=AMBER, rim=RIM_A,
                            recolor=cols, standin='worker_b')
        x0, y0 = PP.cell_xy(x, RAIL + 2, 48)
        out.append((sh, x0, y0))
    return out


# ------------------------------------------------------------------------------------------------ m2 / m3a
def macro_plate(city):
    """The valve macro: the boiler's crown across the bottom (black steel in stepped bands, a riveted band, the
    handrail, snow in Karsk), the twin pop valves (karsk) or the brass safety valve and whistle (berlin) whose
    mouth is JET_BASE; behind them, crisp and dark: the trestle and the mast's lamps against the dawn (karsk), the
    roof's iron trusses, its glass and the pendant lamps (berlin)."""
    F = FL.Flat(bg='#05070c')
    jx, jy = JET_BASE
    if city == 'karsk':
        F.grad(F.box(0, 0, 640, 360), 0, 300, '#0a0e1c', '#4a3c52', steps=7)
        F.pool(F.box(0, 0, 640, 360), 470, 300, 420, 140, steps=((1.0, 1.15), (0.55, 1.35)), col='#9a6a50')
        for x0 in (60, 150):
            leg = F.box(x0, 40, x0 + 14, 300)
            F.fill(leg, '#1a1410')
            F.fill(leg & FL.edge(leg, 'r', 2), '#3a2a1c')
        F.fill(F.line([(74, 80), (150, 180)], 2.0) | F.line([(150, 80), (74, 180)], 2.0), '#1a1410')
        F.fill(F.box(30, 30, 200, 44), '#22180f')
        F.fill(F.box(30, 30, 200, 32), '#cfd8e0')
        mx = 540
        F.fill(F.box(mx - 4, 0, mx + 4, 300), '#14161c')
        for y in range(0, 300, 12):
            F.fill(F.line([(mx - 4, y), (mx + 4, y + 12)], 0.7), '#22262e')
        head = F.box(mx - 22, 40, mx + 22, 58)
        F.fill(head, '#1a1c22')
        for k in range(4):
            F.fill(F.box(mx - 19 + k * 10, 44, mx - 12 + k * 10, 54), '#fff4d0')
        F.pool(F.box(0, 0, 640, 300), mx, 50, 36, 22, steps=((1.0, 1.4), (0.5, 1.9)), col='#ffd8a0')
        body = ['#07080a', '#101215', '#1a1d22', '#262a31', '#383d46', '#565c66']
        hl = '#d0a868'
        snowy = True
    else:
        F.fill(F.box(0, 0, 640, 360), '#0a0c12')
        for x in range(-200, 900, 80):
            F.fill(F.line([(x, 0), (x + 160, 260)], 1.2), '#1c1e24')
        for y in (60, 130, 200):
            F.fill(F.box(0, y, 640, y + 3), '#1c1e24')
        for x in range(0, 640, 26):
            F.fill(F.box(x, 0, x + 1, 230), '#16181e')
        pane = F.box(0, 0, 640, 230) & ~((np.mod(F.xx.astype(int), 26) == 0))
        F.fill(pane & (K.hash2(np.floor_divide(F.xx.astype(np.int64), 26), np.floor_divide(F.yy.astype(np.int64), 70), 3)
                       > 0.8), '#121826')
        for (lx, ly) in ((110, 96), (470, 80), (600, 140)):
            F.fill(F.box(lx, 0, lx + 1, ly - 8), '#14141a')
            sh = F.poly([(lx - 14, ly), (lx + 15, ly), (lx + 8, ly - 9), (lx - 7, ly - 9)])
            F.fill(sh, '#1e2a24')
            F.fill(F.box(lx - 9, ly, lx + 10, ly + 3), '#ffd890')
            F.pool(F.box(0, 0, 640, 300), lx, ly + 4, 30, 18, steps=((1.0, 1.6), (0.5, 2.4)), col='#ffc070')
        F.fill(F.box(0, 230, 640, 300), '#140e0a')
        body = ['#07080a', '#101215', '#1a1d22', '#262a31', '#383d46', '#565c66']
        hl = '#e8b870'
        snowy = False
    # the boiler's crown: a big arc across the bottom
    cy = 640.0
    r = 430.0
    crown = F.ell(320, cy, 900, r)
    v = (F.yy - (cy - r)) / 140.0
    idx = np.clip((v * 4).astype(int), 0, 3)
    cols = [body[4], body[3], body[2], body[1]]
    for k in range(4):
        F.fill(crown & (idx == k), cols[k])
    sheen = crown & (v > 0.06) & (v < 0.16)
    F.fill(sheen, body[4])
    F.fill(sheen & (((F.xx.astype(np.int32) + F.yy.astype(np.int32)) & 1) == 0) & (v > 0.13), body[3])
    F.fill(crown & (v > 0.09) & (v < 0.11) & (np.abs(F.xx - 300) < 220), hl)
    for sx_ in (60, 250, 470, 610):
        F.fill(crown & (np.abs(F.xx - sx_) < 1), body[1])
        F.fill(crown & (np.abs(F.xx - sx_ - 1) < 1), body[4])
    F.fill(crown & FL.edge(crown, 't', 2), hl)
    F.fill(crown & FL.edge(crown, 't', 4) & ~FL.edge(crown, 't', 2), body[5])
    for bx_ in (120, 560):
        band = crown & (np.abs(F.xx - bx_) < 6)
        F.fill(band, body[2])
        F.fill(band & (np.abs(F.xx - bx_ + 4) < 1), body[5])
        F.fill(band & (np.abs(F.xx - bx_ - 5) < 1), body[0])
    seam = crown & (np.abs(F.xx - 430) < 1)
    F.fill(seam, body[1])
    for y_ in range(int(cy - r) + 10, 360, 6):
        F.fill(F.box(433, y_, 435, y_ + 2) & crown, body[5])
    sp = F.line([(200, 360), (210, 250), (236, 236)], 2.0) & crown
    F.fill(sp, body[3])
    F.fill(F.line([(201, 360), (211, 250)], 0.5) & crown, body[5])
    for k in range(18):
        rx_ = 40 + k * 34
        ry_ = cy - r * math.sqrt(max(0.0, 1 - ((rx_ - 320) / 900.0) ** 2)) + 14
        F.fill(F.box(rx_, ry_, rx_ + 2, ry_ + 2), body[5])
        F.fill(F.box(rx_ + 1, ry_ + 1, rx_ + 3, ry_ + 3), body[0])
    hr = F.line([(0, 266), (640, 262)], 1.2)
    F.fill(hr, '#8a929c')
    F.fill(hr & FL.edge(hr, 't'), '#d8dde4')
    for x in (90, 300, 520):
        F.fill(F.box(x, 262, x + 3, 284), '#3a4048')
    if snowy:
        sn = crown & FL.edge(crown, 't', 5) & (K.hash2(F.xx.astype(np.int64), 0, 7) > 0.2)
        F.fill(sn, '#dfe6ee')
        F.fill(sn & FL.edge(sn, 't'), '#f6f8fa')
    # the valves: twin pop valves (karsk) / a brass safety valve and whistle (berlin): the jet's mouth at JET_BASE
    metal = ['#2a1a08', '#5a3a14', '#8a6020', '#b88a34', '#e0b860', '#fff0b0']
    if city == 'karsk':
        for (vx, main) in ((jx, True), (jx + 44, False)):
            base = F.box(vx - 20, jy + 34, vx + 20, jy + 60)
            F.fill(base, body[2])
            F.fill(base & FL.edge(base, 'l', 3), body[4])
            F.outline(base, col='#050506')
            col = F.box(vx - 13, jy + 6, vx + 13, jy + 34)
            F.fill(col, metal[3])
            F.fill(col & (F.xx < vx - 6), metal[4])
            F.fill(col & (F.xx < vx - 9), metal[5])
            F.fill(col & (F.xx > vx + 6), metal[2])
            for y in range(jy + 10, jy + 34, 5):
                F.fill(col & F.box(0, y, 640, y + 1), metal[1])
            cap = F.box(vx - 16, jy, vx + 16, jy + 7)
            F.fill(cap, metal[3])
            F.fill(cap & FL.edge(cap, 't'), metal[5])
            F.outline(col | cap, col='#1a1004')
            if not main:
                F.fill(F.box(vx - 6, jy - 2, vx + 6, jy), '#2a1a08')
        F.fill(F.box(jx - 5, jy - 2, jx + 5, jy + 1), '#0a0604')
    else:
        base = F.box(jx - 26, jy + 34, jx + 26, jy + 62)
        F.fill(base, body[2])
        F.fill(base & FL.edge(base, 'l', 3), body[4])
        F.outline(base, col='#050506')
        bd = F.ell(jx, jy + 34, 24, 20) & (F.yy < jy + 36)
        F.fill(bd, metal[3])
        F.fill(bd & (F.xx < jx - 8), metal[4])
        F.fill(bd & (F.xx < jx - 14), metal[5])
        F.fill(bd & (F.xx > jx + 10), metal[2])
        col = F.box(jx - 8, jy + 2, jx + 8, jy + 18)
        F.fill(col, metal[3])
        F.fill(col & (F.xx < jx - 3), metal[5])
        F.outline(bd | col, col='#1a1004')
        F.fill(F.box(jx - 6, jy - 1, jx + 6, jy + 3), metal[2])
        wx = jx + 70
        wh = F.box(wx - 3, jy - 10, wx + 3, jy + 40)
        F.fill(wh, metal[3])
        F.fill(wh & (F.xx < wx - 1), metal[5])
        bell = F.box(wx - 8, jy - 30, wx + 8, jy - 8)
        F.fill(bell, metal[3])
        F.fill(bell & (F.xx < wx - 3), metal[4])
        F.fill(F.box(wx - 9, jy - 32, wx + 9, jy - 29), metal[5])
        F.outline(wh | bell, col='#1a1004')
    return F.opaque()


# ------------------------------------------------------------------------------------------------ the hall
HALL_W = 1200
M4_OX = 560                             # m4 shows the hall from this x
HALL_BOARD = (448, 104, 624, 176)        # the split-flap board (x0, y0, x1, y1) hanging from the girder
BOARD_ROW = 2                            # the row that flips to D 303
FLAP_T = (6.85, 7.95)                    # the row's flaps run (film time; c4p2cine_hall)
BUFFET = (996, 1120)
KIOSK = (818, 884)
HALL_LIGHTS = []
HALL_AMB = dict(sky='#3a3442', gnd='#2a2220', amb=0.42)
LAMPS = [70 + k * 140 for k in range(9)]
PLAT = 296                              # the platform's back edge (the train side)


def hall_plate():
    """The Ostbahnhof's hall at night: the iron roof trusses and glass, the far track with a dark train, the
    express D 303 at platform K -- its engine (01 1064, smoke deflectors, red wheels) and green carriages
    with lit windows and route boards --, the stone platform in slabs with the lamps' pools, the kiosk ZEITUNGEN
    with its papers, the buffet ERFRISCHUNGEN with its counter, urns and lamp, a luggage cart, a bench."""
    W = HALL_W
    F = FL.Flat(W, 360, bg='#07080c')
    xx, yy = F.xx.astype(np.int64), F.yy.astype(np.int64)
    roof = F.box(0, 0, W, 150)
    F.fill(roof, '#0c0f16')
    F.fill(roof & (K.hash2(np.floor_divide(xx, 30), np.floor_divide(yy, 34), 5) > 0.82), '#141a26')
    for x in range(0, W, 30):
        F.fill(F.box(x, 0, x + 1, 150), '#1a1c22')
    for y in (34, 68, 102):
        F.fill(F.box(0, y, W, y + 2), '#1a1c22')
    for x in range(-150, W + 150, 150):
        F.fill(F.line([(x, 120), (x + 75, 30)], 1.4) | F.line([(x + 75, 30), (x + 150, 120)], 1.4), '#22242c')
    tr = F.box(0, 118, W, 130)
    F.fill(tr, '#1e2028')
    F.fill(tr & FL.edge(tr, 'b', 2), '#34363e')
    for x in range(0, W, 12):
        F.fill(F.line([(x, 120), (x + 6, 128)], 0.5) | F.line([(x + 6, 120), (x, 128)], 0.5), '#2a2c34')
    # the far side: brick wall with arched windows, a dark train on the far track
    wall = F.box(0, 130, W, 236)
    F.fill(wall, '#2a1c18')
    for k, y in enumerate(range(130, 236, 4)):
        F.fill(F.box(0, y, W, y + 1), '#22160f')
    for x in range(40, W, 120):
        a = F.ell(x + 22, 158, 22, 18) & (F.yy < 158) | F.box(x, 158, x + 44, 196)
        F.fill(a, '#141c2c')
        F.fill(a & (np.mod(xx - x, 11) == 0), '#2a1c18')
        F.outline(a, col='#4a3428')
    far = F.box(0, 196, W, 238)
    F.fill(far, '#14181e')
    for x in range(10, W, 90):
        fw = F.box(x, 204, x + 60, 216)
        F.fill(fw, '#2a2416')
        F.fill(fw & (np.mod(xx - x, 14) < 2), '#14181e')
    F.fill(F.box(0, 236, W, 240), '#0a0a0c')
    # platform K: slabs, the edge, lamp pools
    plat = F.box(0, PLAT, W, 360)
    F.fill(plat, '#3a3530')
    ys = [PLAT]
    while ys[-1] < 360:
        ys.append(ys[-1] + max(5, int((ys[-1] - PLAT) * 0.28) + 5))
    for k, y in enumerate(ys):
        F.fill(F.box(0, y, W, y + 1) & plat, '#2a2622')
        if k + 1 < len(ys):
            for x in range(-600, W + 600, 64):
                xa = 600 + (x - 600) * (1 + (y - PLAT) * 0.01)
                xb = 600 + (x - 600) * (1 + (ys[k + 1] - PLAT) * 0.01)
                F.fill(F.line([(xa, y + 1), (xb, ys[k + 1])], 0.45) & plat, '#2e2a26')
    F.fill(F.box(0, PLAT, W, PLAT + 3), '#8a8274')
    F.fill(F.box(0, PLAT + 3, W, PLAT + 4), '#e8e0c8')
    # the express: engine at the left, carriages along the platform
    lo = LO.SideLoco(F, 34, PLAT - 2, m=24.0, facing=-1, kind='german', number='01 1064', crank=0.3, snow=False,
                     lit=1).paint().tender(coal=True, number='DR')
    lo.finish()
    x = lo.anchors['tender'][1] + 6
    rail_y = PLAT - 2
    while x < W:
        cw_ = 300
        body = F.box(x, rail_y - 96, x + cw_ - 6, rail_y - 18)
        F.fill(body, '#1e3a2a')
        F.fill(body & F.box(0, rail_y - 96, W, rail_y - 92), '#2a4a36')
        F.fill(F.box(x, rail_y - 102, x + cw_ - 6, rail_y - 96), '#2a2c30')
        F.fill(F.box(x + 4, rail_y - 50, x + cw_ - 10, rail_y - 47), '#c8b070')
        for k in range(8):
            wx = x + 18 + k * 34
            w_ = F.box(wx, rail_y - 86, wx + 22, rail_y - 60)
            F.fill(w_, '#e8b060')
            F.fill(w_ & F.box(0, rail_y - 86, W, rail_y - 82), '#f8d888')
            if K.hash2(wx, 1, 71) > 0.55:
                F.fill(w_ & F.ell(wx + 11, rail_y - 66, 5, 7), '#3a2414')
                F.fill(w_ & F.ell(wx + 11, rail_y - 76, 3, 3), '#3a2414')
            F.outline(w_, col='#0e1a12')
        board = F.box(x + 90, rail_y - 44, x + 210, rail_y - 36)
        F.fill(board, '#e8e4d8')
        F.fill(F.text('BERLIN - KARSK D 303', x + 94, rail_y - 43, 's') & board, '#1a1a1a')
        F.fill(F.box(x, rail_y - 18, x + cw_ - 6, rail_y - 8), '#0c0e10')
        for wx in (x + 40, x + 70, x + cw_ - 76, x + cw_ - 46):
            w_ = F.ell(wx, rail_y - 9, 9, 9)
            F.fill(w_, '#202428')
            F.outline(w_, col='#050506')
        F.outline(body, col='#0a140e')
        x += cw_
    # the departure board: frame and the rows (the flipping row is a sprite)
    bx0, by0, bx1, by1 = HALL_BOARD
    bd = F.box(bx0, by0, bx1, by1)
    F.fill(bd, '#141618')
    F.fill(bd & FL.edge(bd, 't', 2), '#3a3e44')
    F.fill(F.text('ABFAHRT', bx0 + 6, by0 + 4, 's'), '#d8c890')
    F.fill(F.text('ОТПРАВЛЕНИЕ', bx0 + 60, by0 + 4, 's'), '#a89a70')
    rows = ['E 412  WARSCHAU     20.44 3', 'P 1307 STRALSUND     20.58 5', '', 'P 1188 FRANKFURT(O)  21.20 2']
    for k, txt in enumerate(rows):
        ry = by0 + 16 + k * 14
        for c in range(27):
            cx_ = bx0 + 5 + c * 6
            F.fill(F.box(cx_, ry, cx_ + 5, ry + 9), '#0c0d0e')
            F.fill(F.box(cx_, ry + 4, cx_ + 5, ry + 5), '#1e2022')
            if txt and c < len(txt) and txt[c] != ' ':
                F.fill(F.text(txt[c], cx_, ry + 1, 's'), '#e8dcbc')
    for hx_ in (bx0 + 20, bx1 - 20):
        F.fill(F.box(hx_, 118, hx_ + 1, by0), '#3a3e44')
    F.outline(bd, col='#050506')
    clock = F.ell(780, 160, 12, 12)
    F.fill(clock, '#e8e4d0')
    F.fill(F.line([(780, 160), (780, 152)], 0.6) | F.line([(780, 160), (786, 162)], 0.6), '#1a1a1a')
    F.outline(clock, col='#1a1a1a')
    F.fill(F.box(779, 130, 781, 148), '#2a2c32')
    # the kiosk and the buffet on the platform
    k0, k1 = KIOSK
    ks = F.box(k0, 226, k1, PLAT + 2)
    F.fill(ks, '#1e3a2a')
    F.fill(F.box(k0 - 4, 220, k1 + 4, 228), '#14281c')
    F.fill(F.box(k0 + 4, 230, k1 - 4, 240), '#e8e4d8')
    F.fill(F.text('ZEITUNGEN', k0 + 7, 232, 's'), '#1e3a2a')
    shelf = F.box(k0 + 4, 244, k1 - 4, 284)
    F.fill(shelf, '#d8b070')
    for j in range(5):
        for i in range(4):
            px_, py_ = k0 + 6 + i * 14, 246 + j * 8
            F.fill(F.box(px_, py_, px_ + 12, py_ + 6), ['#e8e4d8', '#c8c0a8', '#d8a890', '#b8c8d0'][(i + j) % 4])
            F.fill(F.box(px_ + 1, py_ + 1, px_ + 8, py_ + 2), '#3a3a3a')
    F.outline(ks, col='#0a140e')
    b0, b1 = BUFFET
    bu = F.box(b0, 214, b1, PLAT + 2)
    F.fill(bu, '#4a3020')
    for k, x_ in enumerate(range(b0, b1, 8)):
        F.fill(F.box(x_, 254, x_ + 1, PLAT + 2), '#3a2416')
    F.fill(F.box(b0 - 6, 206, b1 + 6, 216), '#2a1a10')
    F.fill(F.box(b0 + 10, 218, b1 - 10, 230), '#e8dcc0')
    F.fill(F.text('ERFRISCHUNGEN', b0 + 16, 221, 's'), '#5a1a10')
    win = F.box(b0 + 6, 232, b1 - 6, 252)
    F.fill(win, '#f0c070')
    for x_ in (b0 + 20, b0 + 34, b0 + 48):
        F.fill(F.box(x_, 236, x_ + 8, 252), '#b0b4bc')
        F.fill(F.box(x_ + 2, 234, x_ + 6, 236), '#6a6e76')
    for x_ in (b0 + 70, b0 + 80, b0 + 90, b0 + 100):
        F.fill(F.box(x_, 244, x_ + 4, 252), '#e8e4dc')
    counter = F.box(b0, 252, b1, 258)
    F.fill(counter, '#8a6040')
    F.fill(counter & FL.edge(counter, 't'), '#c08a5a')
    F.outline(bu, col='#1a0e06')
    # a luggage cart and a bench
    cart = F.box(700, 280, 760, 288)
    F.fill(cart, '#3a2a1c')
    for x_, w_, h_, c_ in ((704, 18, 14, '#6a3a22'), (724, 24, 10, '#2a3a4a'), (742, 14, 18, '#5a4a32')):
        s_ = F.box(x_, 280 - h_, x_ + w_, 280)
        F.fill(s_, c_)
        F.outline(s_, col='#0a0806')
    F.fill(F.ell(708, 292, 4, 4) | F.ell(752, 292, 4, 4), '#1a1a1a')
    bench = F.box(940, 282, 990, 286)
    F.fill(bench, '#5a3a22')
    F.fill(F.box(944, 286, 947, 296) | F.box(983, 286, 986, 296), '#2a1a10')
    # light: the pendant lamps' pools on the platform, the buffet's window spill
    for lx in LAMPS:
        F.pool(plat, lx, PLAT + 16, 80, 20, steps=((1.0, 1.15), (0.55, 1.3), (0.25, 1.45)), col='#ffc070')
    F.pool(plat, (b0 + b1) / 2, PLAT + 10, 90, 18, steps=((1.0, 1.2), (0.5, 1.4)), col='#ffc070')
    return F.opaque(), lo


def hall_glows():
    blobs = []
    for x in LAMPS:
        blobs += [(x, 150, 26, 18, (110, 66, 22), 1.4)]
    blobs += [((BUFFET[0] + BUFFET[1]) / 2, 242, 50, 24, (90, 60, 24), 1.5)]
    return K.glow_sprite(HALL_W, K.VH, blobs, 8.0)


def hall_lamps():
    """The pendant lamps (drawn over the glows: their rods, enamel shades and the lit bowls)."""
    F = FL.Flat(HALL_W, 360, bg='#000000')
    for x in LAMPS:
        F.fill(F.box(x, 130, x + 1, 142), '#141414')
        sh = F.poly([(x - 8, 148), (x + 9, 148), (x + 5, 142), (x - 4, 142)])
        F.fill(sh, '#1e2a24')
        F.fill(sh & FL.edge(sh, 't'), '#3a5a48')
        F.fill(F.box(x - 5, 148, x + 6, 151), '#ffd890')
    return F.rgba()


FLAP_W = 6


def flaps(g, bx0, ry, txt, moving=()):
    """One row of split-flap cells, one character per cell (the hinge line across the middle; a moving flap
    shows its falling half)."""
    for c in range(min(27, len(txt) if txt else 27)):
        cx_ = bx0 + 5 + c * FLAP_W
        g.put(g.box(cx_, ry, cx_ + FLAP_W - 1, ry + 9), '#0c0d0e', z=148)
        ch = txt[c] if c < len(txt) else ' '
        if ch != ' ':
            m = g.text(ch, cx_, ry + 1, 's')
            g.put(m, '#e8dcbc', z=146)
        g.put(g.box(cx_, ry + 4, cx_ + FLAP_W - 1, ry + 5), '#1e2022', z=145)
        if c in moving:
            g.put(g.box(cx_, ry + 5, cx_ + FLAP_W - 1, ry + 8), '#2e3034', z=144)


def board_frames():
    """The flipping row: 10 frames -- the old row, flaps running (random glyphs settling left to right), then
    D 303  KARSK  21.10  K."""
    bx0, by0, bx1, by1 = HALL_BOARD
    ry = by0 + 16 + BOARD_ROW * 14
    final = 'D 303  KARSK        21.10 K'
    old = 'P 1265 FÜRSTENWALDE 20.31 4'
    glyphs = 'ABCDEFGHIKLMNOPRSTUVWZ0123456789'
    out = []
    w, h = bx1 - bx0, 14
    for f in range(10):
        g = GB(w, h, bx0, ry - 2)
        s = []
        for c in range(len(final)):
            settle = 1 + c * 0.22
            if f == 0:
                s.append(old[c] if c < len(old) else ' ')
            elif f >= settle + 1.5:
                s.append(final[c])
            else:
                s.append(glyphs[int(K.hash2(c, f, 7) * len(glyphs))] if final[c] != ' ' or f < 3 else ' ')
        txt = ''.join(s)
        flaps(g, bx0, ry, txt, moving=[c for c in range(len(txt)) if 0 < f < 9 and txt[c] != final[c] and
                                        K.hash2(c, f, 11) > 0.5])
        out.append(g.final(HALL_LIGHTS, PAL_B, spread=0.0, **HALL_AMB))
    return out, (bx0, ry - 2)


# ------------------------------------------------------------------------------------------------ m4 people
# (rig id, stand-in, anim, x (hall), sole y, facing, recolours, fps): three depths -- boarding at the doors
# (y 286), on the platform (y 294), the front only at the sides (y 306) so Konrad's lane stays clear
M4_PEOPLE = [
    ('conductor', 'conductor', 'idle_side', 616, 286, 1, {}, 3.0),
    ('typist', 'typist', 'talk_side', 690, 286, 1, {'coat': '#5a2a2a'}, 5.0),
    ('kessler', 'kessler', 'idle_side', 712, 286, -1, {'coat': '#2a2e3a'}, 3.0),
    ('librarian', 'librarian', 'idle_side', 930, 286, 1, {'coat': '#3a4a5a'}, 3.0),
    ('porter', 'porter', 'idle_side', 770, 294, -1, {}, 3.0),
    ('stapo_civil', 'clerk', 'idle_side', 866, 296, -1, {}, 3.0),
    ('berlin_mother', 'berlin_mother', 'talk_side', 950, 294, 1, {'coat': '#4a3a4a'}, 5.0),
    ('berlin_child', 'berlin_child', 'idle_side', 966, 296, -1, {}, 3.0),
    ('marta', 'marta', 'idle_side', 1012, 296, 1, {}, 3.0),
    ('berlin_father', 'berlin_father', 'idle_side', 1150, 300, -1, {'coat': '#3a3a2e'}, 3.0),
    ('clerk', 'clerk', 'idle_side', 1100, 306, -1, {'coat': '#3a3428'}, 3.0),
    ('worker_a', 'worker_a', 'idle_side', 1184, 312, -1, {'coat': '#2e3442'}, 3.0),
]
M4_KONRAD = (580, 690)                   # Konrad's feet x (hall) from 9.5 s at the in-game speed, then he stops
M4_FEET = 306


def m4_people():
    CH, CB, A, CC = K.rig()
    out = []
    for i, (cid, stand, anim, x, base, face, cols, fps) in enumerate(M4_PEOPLE):
        spec, used = K.spec_of(cid, stand)
        fn = {'idle_side': A.idle_side, 'talk_side': A.talk_side}[anim]
        poses = fn(spec.style)
        sh, n, w = PP.sheet(cid, poses, None, 32, face < 0, key='left' if face < 0 else 'right',
                            mul=(1.08, 0.98, 0.84), rim=(255, 210, 140), recolor=cols, standin=stand)
        x0, y0 = PP.cell_xy(x, base, 32)
        out.append((sh, x0, y0, fps, n, base, x))
    spec, used = K.spec_of('konrad')
    walk = A.walk_side(spec.style)
    idle = A.idle_side(spec.style)
    kw, n1, w1 = PP.sheet('konrad', walk, None, 32, False, key='left', mul=(1.0, 0.98, 0.92), rim=(255, 220, 160))
    ki, n2, w2 = PP.sheet('konrad', idle, None, 32, False, key='left', mul=(1.0, 0.98, 0.92), rim=(255, 220, 160))
    return out, K.hsheet([kw, ki])


def build(w):
    plate, lo1 = m1_plate()
    w('steam/m1_bg.png', plate)
    tx0, ty0, tx1, ty1 = M1_POLES[2] - 2, 180, M1_POLES[3], 300
    w('steam/tarp.png', K.hsheet([fr[ty0:ty1, tx0:tx1] for fr in tarp_frames()]))
    workers = m1_workers()
    for i, (sh, x0, y0) in enumerate(workers):
        w('steam/m1_worker_%d.png' % i, sh)
    import env_c4p2_cine_express as EX
    w('steam/m1_alexei.png', EX.alexei_silhouette())
    w('steam/dust.png', K.puff_sheet(6, 28, 22, PAL.K_CONC[3:], 61, grow=(0.25, 0.5), thin=0.7, light=(0.3, -0.7),
                                     drift=0.2))
    w('steam/m2_bg.png', macro_plate('karsk'))
    w('steam/m3a_bg.png', macro_plate('berlin'))
    w('steam/jet.png', PL.jet_sheet(12, JET_SIZE[0], JET_SIZE[1], seed=501))
    w('steam/jet_far.png', K.puff_sheet(8, 26, 30, PAL.B_STEAM[1:], 63, grow=(0.2, 0.55), thin=0.5,
                                        light=(0.2, -0.8), drift=0.1))
    hp, lo3 = hall_plate()
    w('steam/hall.png', hp)
    w('steam/hall_glow.png', hall_glows())
    w('steam/hall_lamps.png', hall_lamps())
    frames, (fx_, fy_) = board_frames()
    w('steam/board_row.png', K.hsheet(frames))
    people, kon = m4_people()
    for i, row in enumerate(people):
        w('steam/m4_p%02d.png' % i, row[0])
    w('steam/m4_konrad.png', kon)
    w('steam/hall_steam.png', K.puff_sheet(8, 60, 44, PAL.B_STEAM[:6], 65, grow=(0.25, 0.55), thin=0.6,
                                           light=(0.1, 0.8), drift=0.25))
    tender = lo1.anchors['tender']
    valve = lo1.anchors['valve']
    v3 = lo3.anchors['valve']
    L.update(tarp_at=[tx0, ty0], tarp_w=tx1 - tx0, jet_base=list(JET_BASE), jet_size=list(JET_SIZE), rail=RAIL,
             m1_chute=list(M1_CHUTE), m1_valve=[int(valve[0]) - 13, int(valve[1]) - 28],
             m1_tender=[int(tender[0]), int(tender[1]), int(tender[2]) - 6],
             m1_poles=list(M1_POLES), tarp_t=list(TARP_T), tarp_snaps=list(TARP_SNAPS), coal_run=list(COAL_RUN),
             m1_workers=[[x0, y0] for (sh, x0, y0) in workers], m1_alexei=[0, 146], m1_alexei_cell=240,
             m3_valve=[int(v3[0]) - 13, int(v3[1]) - 28], hall_w=HALL_W, m4_ox=M4_OX,
             board=list(HALL_BOARD), board_row_at=[fx_, fy_], flap_t=list(FLAP_T),
             m4_people=[[x0, y0, fps, n] for (sh, x0, y0, fps, n, base, x) in people], m4_konrad=list(M4_KONRAD),
             m4_feet=M4_FEET, konrad_walk_frames=8)
