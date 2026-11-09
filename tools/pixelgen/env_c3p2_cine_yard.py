"""env_c3p2_cine_yard -- the places of LS_C3_Escape, round 10 (owner: c3p2 places stream).

Out through the 1909 coal chute into the yard behind the east wing (C3P2_DESIGN §2.9), painted as lit colour:
  e1_bg      up the chute: brick walls converging on the square of snow light, the scratched steel slide with coal
             lumps, soot, an old pipe; the fire's glow from below on the lower bricks, cold light from above
  e2_bg      the yard at night: the rusticated base of the east wing with a souterrain window glowing orange and
             soot over it, a drainpipe, the bracket lamp, the iron hatch frame in the snow; a coal heap under snow,
             barrels, a handcart, the yard gate with the lane's lamp beyond, the far yard wall, drifts and tracks
  e2_hatch   the cast-iron lid: closed under snow, lifting (snow sliding off, the hot slit), open against the wall
  e3a_bg     looking down into the open hatch: the iron rim with snow and the cast date, the chute's walls going
             down into smoke, the fire's glow deep below
  e3b_bg     low at the snow beside the hatch: the wall foot, the window glowing, the hatch, drag marks, coal, snow
  e4_bg      the east wing from the lane: neo-baroque front (rusticated base with the barred souterrain windows in
             their light wells, pilasters, pedimented windows, cornice, mansard, chimneys, the one lit window high
             up), the neighbouring houses at the edges, bare lime trees and a lamp post in the lane, a snowed-in car
  e4_window  one souterrain window: dark / bursting / burning (the runtime bursts them one after another)
The people (Konrad crawling out, the hands, the two men in the snow, onlookers and firemen in the lane) come from
the figures stream.
"""
from __future__ import annotations

import math

import numpy as np

import env_c3p2_cine_kit as Q
from env_c3p2_cine_kit import (C, K, VW, VH, NIGHT, SNOW, LAMP, IRON, OAK, PAPER, BRASS, SMOKE)
import env_c3p2_cine_life as LF
import pg

LE = Q.LAYOUT.setdefault('escape', {})
BRICKC = ['#0A0706', '#140D0A', '#1E140F', '#2A1C15', '#3A271C', '#4E3424', '#66442E']
EMBER = ['#1A0805', '#3A0F08', '#6E1E0C', '#A8381A', '#D8662A', '#F2A044', '#FCE0A0']
STONE = ['#05070B', '#0A0D13', '#10151D', '#171E28', '#202935', '#2B3644', '#394656', '#4A5868']
PAL_Y = LF.palette(NIGHT, SNOW, LAMP, IRON, BRICKC, EMBER, STONE, OAK[:6], SMOKE,
                   ['#3A2A22', '#5A3E2E', '#7A523A', '#4A3A36', '#6A5448', '#8A705C', '#26201E', '#2E3A48',
                    '#3A4A5C', '#566A80', '#1E2A3A', '#2A2622'])

CH = {'vpx': 320.0, 'vpy': 110.0, 'f': 280.0, 'half': 0.42}
CH_TOP = 5.0
WALL_FOOT = 214
HATCH = dict(back=(250, 390, 218), front=(238, 402, 246), outer_back=(236, 404, 213), outer_front=(220, 420, 253))
YARD_LAMP = (486, 64)
E3B_SNOW = 214


def _bricks(cv, m, U, V, seed, course, brick, base='#3A271C', mortar='#1E140F', k=1.0):
    row = np.floor(V / course)
    off = np.where(np.mod(row, 2) == 0, 0.0, brick / 2)
    col = np.floor((U + off) / brick)
    hv = LF.hsh(row, col, seed)
    cv.put(m, base, (0.72 + hv[m] * 0.3) * k)
    joint = m & ((np.mod(V, course) < course * 0.14) | (np.mod(U + off, brick) < brick * 0.07))
    cv.put(joint, mortar, 0.9 * k)


# ================================================================================================ e1 chute
def e1_bg():
    cv = LF.Cv(VW, VH, 0, 0, amb=(0.08, 0.08, 0.09))
    xx, yy = cv.xx, cv.yy
    vx, vy, f, hlf = CH['vpx'], CH['vpy'], CH['f'], CH['half']
    s = f * hlf / CH_TOP
    cv.light(vx, vy - s, 260, (0.85, 0.95, 1.15), 1.5)                 # snow light from the hatch
    cv.light(vx, 420, 330, (1.1, 0.5, 0.2), 1.4)                        # the fire's glow from below
    dx = xx + 0.5 - vx
    dy = yy + 0.5 - vy
    ax, ay = np.abs(dx), np.abs(dy)
    vert = ax >= ay
    Z = np.where(vert, f * hlf / np.maximum(ax, 0.5), f * hlf / np.maximum(ay, 0.5))
    U = np.where(vert, dy * Z / f, dx * Z / f)
    inside = Z < CH_TOP
    floor = inside & ~vert & (dy > 0)
    walls = inside & ~floor
    _bricks(cv, walls, U + 2.0, Z, 971, 0.075, 0.22)
    soot = walls & (LF.nz(VW, VH, 5, 973, 2) > 0.62)
    cv.mix(soot, '#0B0908', 0.7)
    drip = walls & (LF.vnoise(U * 9.0, Z * 0.6, 975) > 0.8)
    cv.mix(drip, '#13100E', 0.6)
    # the steel slide: scratched plate, rivet lines, coal lumps caught on it
    cv.put(floor, '#323840', 0.85 + np.clip(Z[floor] / CH_TOP, 0, 1) * 0.1)
    sl = floor & (np.mod(U * 9.0 + Z * 0.3, 1.0) < 0.12)
    cv.put(sl, '#5E666E', 0.9)
    rv = floor & (np.mod(Z, 0.5) < 0.03)
    cv.put(rv, '#15171C', 1.0)
    coal = floor & (LF.vnoise(U * 18.0, Z * 6.0, 977) > 0.82)
    cv.put(coal, '#0B0908', 1.0)
    cv.put(coal & C.rim(coal, 0, -1), '#464D55', 1.0)
    # an old pipe along the left wall
    p0 = (vx - f * hlf / 0.6, vy - 30.0 / 0.6)
    p1 = (vx - f * hlf / 4.5, vy - 30.0 / 4.5)
    pipe = cv.seg([p0, p1], 6.0, 0.8)
    cv.put(pipe, '#3A2A22', 0.9 + C.edge_light(pipe, (0.3, -1.0), width=3.0, soft=1)[pipe] * 0.6)
    # the hatch square at the top: lid ajar -> snow light, flakes on the rim
    sq = (np.abs(dx) < s) & (np.abs(dy) < s)
    cv.put(sq, '#15171C', 1.0)
    cv.emit(sq & (dy < -s + 5), '#DEE2E7', 1.0)
    cv.emit(sq & (dy >= -s + 5) & (dy < -s + 8), '#7D8796', 1.0)
    cv.put(cv.box(vx - s, vy + s - 2, vx + s, vy + s), '#A1AAB7', 1.0)
    out = cv.quant(PAL_Y, spread=10.0)
    out[..., 3] = 255
    LE['e1_hatch'] = [vx, vy, s]
    return out


def e1_light():
    a = np.zeros((VH, VW, 3), np.float32)
    vx, vy = CH['vpx'], CH['vpy']
    s = CH['f'] * CH['half'] / CH_TOP
    Q.add_glow(a, vx, vy - s + 3, 60, 22, (90, 100, 116), 1.4)
    Q.add_glow(a, vx, vy + 60, 120, 150, (26, 30, 38), 1.2)
    Q.add_glow(a, vx, 380, 260, 90, (46, 18, 6), 1.3)
    return K.soft_quant(a, 6.0)


# ================================================================================================ e2 yard
def _yard_light(cv):
    lamp = cv.light(YARD_LAMP[0], YARD_LAMP[1] + 30, 320, (1.15, 0.95, 0.65), 1.45)
    win = cv.light(128, 186, 150, (1.3, 0.58, 0.22), 1.35)
    hot = cv.light(320, 236, 120, (0.9, 0.4, 0.14), 1.4)
    gate = cv.light(612, 150, 110, (0.6, 0.5, 0.36), 1.5)
    return lamp, win, hot, gate


def e2_bg():
    cv = LF.Cv(VW, VH, 0, 0, amb=(0.22, 0.25, 0.34))
    xx, yy = cv.xx, cv.yy
    _yard_light(cv)
    n1 = cv.nz(14, 983)
    n2 = cv.nz(3, 985)
    # rusticated base of the east wing: big blocks, deep joints, a lit bevel on every course
    wall = yy < WALL_FOOT
    row = np.floor(yy / 30)
    off = np.where(np.mod(row, 2) == 0, 0, 36)
    blk = LF.hsh(row, np.floor((xx + off) / 72), 7.0)
    cv.put(wall, '#2B3644', 0.72 + blk[wall] * 0.15 + n1[wall] * 0.1)
    joint = wall & ((np.mod(yy, 30) < 2) | (np.mod(xx + off, 72) < 2))
    cv.put(joint, '#10151D', 1.0)
    bev = wall & (np.mod(yy, 30) == 2) & ~joint
    cv.put(bev, '#4A5868', 0.95)
    plinth = (yy >= WALL_FOOT - 14) & (yy < WALL_FOOT)
    cv.put(plinth, '#394656', 0.9)
    cv.put((yy >= WALL_FOOT - 15) & (yy < WALL_FOOT - 13), '#A1AAB7', 0.95)
    # the far yard wall and the gate at the right (the lane's lamp beyond the bars)
    yw = (xx >= 560) & (yy < WALL_FOOT + 4)
    cv.put(yw, '#202935', 0.8 + n1[yw] * 0.1)
    gate = cv.box(578, 96, 640, WALL_FOOT + 4)
    cv.emit(gate, '#2E3A48', 0.9)
    cv.emit(gate & (yy > 170), '#3A4A5C', 0.9)
    cv.emit(cv.ell(620, 112, 3, 4), '#FCE2B0')
    bars = gate & ((np.mod(xx, 7) < 2) | (np.abs(yy - 120) < 1) | (np.abs(yy - 190) < 1))
    cv.put(bars, '#05070B', 1.0)
    spikes = np.zeros_like(gate)
    for gx in range(578, 640, 7):
        spikes |= cv.poly([(gx - 0.5, 96), (gx + 2.5, 96), (gx + 1, 90)])
    cv.put(spikes, '#05070B', 1.0)
    cv.put(cv.box(570, 80, 578, WALL_FOOT + 4), '#2B3644', 0.9)
    cv.put(cv.box(568, 76, 580, 80), '#A1AAB7', 0.9)
    # the souterrain window left of the hatch: barred, glowing orange (the fire inside), soot above it
    win = cv.box(92, 148, 166, 196)
    cv.emit(win, '#A8381A', 0.75 + n2[win] * 0.4 + (yy[win] - 148) / 48.0 * 0.4)
    cv.emit(win & (LF.nz(VW, VH, 4, 987, 2) > 0.6), '#F2A044', 0.9)
    cv.put(win & (np.mod(xx, 12) < 2), '#05070B', 1.0)
    cv.put(cv.box(88, 196, 170, 200), '#4A5868', 0.95)
    soot = (xx > 96) & (xx < 162) & (yy < 148) & (yy > 92) & (pg.bayer(VW, VH, 0, 0) < 0.6 - (148 - yy) / 100.0)
    cv.put(soot, '#05070B', 1.0)
    # drainpipe with brackets, ice at its foot
    dp = cv.box(196, 46, 203, WALL_FOOT + 2)
    cv.put(dp, '#22262D', 0.95 + C.edge_light(dp, (1.0, 0.0), width=2.0, soft=1)[dp] * 0.6)
    for by in (70, 130, 190):
        cv.put(cv.box(194, by, 205, by + 3), '#15171C', 1.0)
    cv.put(cv.ell(199, WALL_FOOT + 2, 7, 2), '#C2C9D2', 0.95)
    # the bracket lamp
    lx, ly = YARD_LAMP
    cv.put(cv.seg([(lx + 24, ly - 20), (lx + 24, ly - 6), (lx + 4, ly - 6)], 1.4), '#15171C', 1.0)
    cv.put(cv.poly([(lx - 7, ly - 6), (lx + 7, ly - 6), (lx + 5, ly + 4), (lx - 5, ly + 4)]), '#15171C', 1.0)
    cv.emit(cv.ell(lx, ly + 3, 4, 3), '#FCE2B0')
    cv.put(cv.box(lx - 8, ly - 9, lx + 8, ly - 6), '#C2C9D2', 0.95)
    # snow: drifts against the wall, the lamp pool, the glow from the window and the hatch, tracks
    g = yy >= WALL_FOOT
    u = (yy - WALL_FOOT) / (VH - WALL_FOOT)
    cv.put(g, '#7D8796', 0.62 + n1[g] * 0.12 + u[g] * 0.18)
    drift = g & (yy < WALL_FOOT + 8 + LF.vnoise(xx * 0.05, 0.0, 989) * 6)
    cv.put(drift, '#A1AAB7', 0.9)
    trk = g & (np.abs(yy - (WALL_FOOT + 30 + (xx - 560) * 0.25)) < 3) & (xx > 470) & (LF.vnoise(xx * 0.5, yy, 991) > 0.45)
    cv.put(trk, '#4F5E70', 0.85)
    # a coal heap under snow at the left, barrels, a handcart against the wall
    heap = cv.ell(40, WALL_FOOT + 6, 52, 30) & (yy < WALL_FOOT + 6)
    cv.put(heap, '#14161A', 1.0)
    cv.put(heap & (LF.nz(VW, VH, 4, 993, 2) > 0.45) & ~C.shift(heap, 0, -3), '#C2C9D2', 0.9)
    cv.put(LF.edge_top(heap) | LF.edge_top(heap, 2), '#DEE2E7', 0.85)
    LF.barrel(cv, 452, WALL_FOOT + 8, 10, 24, col='#2B3038', snow='#C2C9D2', seed=995)
    LF.barrel(cv, 474, WALL_FOOT + 10, 10, 22, col='#3A2A22', snow='#C2C9D2', seed=996)
    cart = cv.box(520, WALL_FOOT - 18, 556, WALL_FOOT - 4)
    cv.put(cart, '#3D271A', 0.9)
    cv.put(cart & (np.mod(xx, 9) < 1), '#1C120C', 1.0)
    cv.put(cv.ring(528, WALL_FOOT - 2, 5, 7) | cv.ell(528, WALL_FOOT - 2, 1.5, 1.5), '#1C120C', 1.0)
    cv.put(cv.seg([(556, WALL_FOOT - 12), (574, WALL_FOOT + 10)], 1.0), '#3D271A', 1.0)
    LF.snowcap(cv, cart, 2, '#C2C9D2', 997)
    # the iron frame of the hatch in the snow, the dark mouth with the glow deep inside
    ob0, ob1, oby = HATCH['outer_back']
    of0, of1, ofy = HATCH['outer_front']
    frame = cv.poly([(ob0, oby), (ob1, oby), (of1, ofy), (of0, ofy)])
    b0, b1, by_ = HATCH['back']
    f0, f1_, fy = HATCH['front']
    mouth = cv.poly([(b0, by_), (b1, by_), (f1_, fy), (f0, fy)])
    cv.put(frame & ~mouth, '#323840', 0.9)
    cv.put(frame & ~mouth & (yy >= ofy - 2), '#5E666E', 0.95)
    cv.put(mouth, '#05070B', 1.0, lit=False)
    deep = mouth & (yy > by_ + 8)
    cv.emit(deep, '#6E1E0C', 0.5 + (yy[deep] - by_) / 40.0 * 0.6)
    out = cv.quant(PAL_Y, spread=10.0)
    out[..., 3] = 255
    LE['hatch'] = {k: list(v) for k, v in HATCH.items()}
    LE['yard_lamp'] = list(YARD_LAMP)
    LE['e2_window'] = [92, 148, 166, 196]
    return out


def _iron_plate(cv, m, U, V, ulen, vlen, face, lamp_dir=(0.55, -0.8)):
    """Paint a cast-iron plate over mask m with plate coordinates U (0..ulen across) and V (0..vlen along): a heavy
    raised rim, the face: 'tread' (the top: a raised lozenge tread pattern) or 'ribs' (the underside: a grid of
    deep reinforcing ribs), rust blooms, the lamp catching every raised edge.  Opaque everywhere, in the warm
    rust-black of old cast iron so it never melts into the blue-grey wall behind it."""
    xx, yy = cv.xx, cv.yy
    n1 = LF.nz(cv.w, cv.h, 5, 1101, 2)
    n2 = LF.nz(cv.w, cv.h, 11, 1103, 2)
    cv.put(m, '#2A2320', 0.85 + n2[m] * 0.15)
    rim = m & ((U < ulen * 0.06) | (U > ulen * 0.94) | (V < vlen * 0.07) | (V > vlen * 0.93))
    if face == 'tread':
        # raised lozenges in staggered rows
        gu, gv = ulen / 14.0, vlen / 9.0
        cu = np.mod(U, gu) - gu / 2
        rowi = np.floor(V / gv)
        cvv = np.mod(V + np.where(np.mod(rowi, 2) == 0, 0, gv / 2), gv) - gv / 2
        loz = m & ~rim & (np.abs(cu) / (gu * 0.42) + np.abs(cvv) / (gv * 0.18) < 1.0)
        cv.put(loz, '#463A32', 0.95)
        cv.put(loz & ~C.shift(loz, 0, -1), '#8A7A6A', 1.0)
        cv.put(loz & ~C.shift(loz, 0, 1), '#120E0C', 1.0)
    else:
        # the underside: deep ribs across and along, the bosses where they cross, the plate between them
        ribs = m & ~rim & ((np.abs(np.mod(U, ulen / 4.0) - ulen / 8.0) > ulen / 8.0 - ulen * 0.025) |
                           (np.abs(np.mod(V, vlen / 3.0) - vlen / 6.0) > vlen / 6.0 - vlen * 0.035))
        panel = m & ~rim & ~ribs
        cv.put(panel, '#30282A', 0.8 + n1[panel] * 0.25)
        cv.put(panel & C.shift(ribs, 0, 1) & ~ribs, '#120E0C', 1.0)          # the ribs' shadows on the plate
        cv.put(panel & C.shift(ribs, 1, 0) & ~ribs, '#1C1614', 1.0)
        cv.put(ribs, '#4A3E36', 0.95)
        cv.put(ribs & ~C.shift(ribs, -1, 0), '#7A6A5A', 1.0)
        cv.put(ribs & ~C.shift(ribs, 0, -1), '#A08C76', 0.95)
        cv.put(ribs & ~C.shift(ribs, 1, 0), '#120E0C', 1.0)
    cv.put(rim, '#3E342E', 1.0)
    cv.put(rim & ~C.shift(rim, 0, -1), '#A89886', 1.0)
    cv.put(rim & ~C.shift(rim, -1, 0), '#6E5E50', 1.0)
    rust = m & (n2 > 0.66) & (LF.hsh(xx, yy, 1105) > 0.4)
    cv.mix(rust, '#5A3020', 0.55)
    cv.mix(rust & (n1 > 0.7), '#7A4428', 0.5)
    # a dark outline where the plate meets the air, so its silhouette stays crisp against the wall
    edge = m & ~(C.shift(m, 1, 0) & C.shift(m, -1, 0) & C.shift(m, 0, 1) & C.shift(m, 0, -1))
    cv.put(edge & ~(rim & ~C.shift(rim, 0, -1)), '#0B0807', 1.0, lit=False)


def e2_hatch():
    """3 frames of the cast-iron lid (hinged at the wall), opaque and heavy: closed (the tread plate under a pillow
    of snow that has melted back from its warm rim, the cast '1909' showing), lifting (its thick front edge, the
    snow sliding off, the red slit under it), open against the wall (the ribbed, sooted underside with the cast
    date, the hinge knuckles, lit from below by the fire and from the side by the lamp)."""
    ox, oy, w, h = 214, 130, 212, 128
    b0, b1, by_ = HATCH['back']
    f0, f1_, fy = HATCH['front']
    frames = []
    tm = K.vtext('1909', 'l', 1)
    for fr in range(3):
        cv = LF.Cv(w, h, ox, oy, amb=(0.42, 0.44, 0.52))
        cv.light(YARD_LAMP[0], YARD_LAMP[1] + 30, 320, (1.0, 0.85, 0.6), 1.4)
        xx, yy = cv.xx, cv.yy
        if fr == 0:
            q = [(b0 - 3, by_ - 2), (b1 + 3, by_ - 2), (f1_ + 4, fy + 1), (f0 - 4, fy + 1)]
            lid = cv.poly(q)
            V = np.clip((yy - (by_ - 2)) / max(1.0, fy + 1 - (by_ - 2)), 0, 1)
            left = (b0 - 3) + ((f0 - 4) - (b0 - 3)) * V
            right = (b1 + 3) + ((f1_ + 4) - (b1 + 3)) * V
            U = (xx - left) / np.maximum(1.0, right - left)
            cv.light(320, 250, 90, (0.5, 0.24, 0.08), 1.5)          # warmth from below at the rim
            _iron_plate(cv, lid, U * 140, V * 30, 140, 30, 'tread')
            sm = K.place(np.repeat(tm, 1, 0), w, h, (b0 + b1) // 2 - ox - tm.shape[1] // 2, (by_ + fy) // 2 - oy - 3)
            cv.put(sm & lid, '#8A929A', 1.0)
            # snow: a soft pillow over the middle, melted back from the warm rim (wet dark iron there)
            cu, cvv = np.abs(U - 0.5) / 0.42, np.abs(V - 0.45) / 0.4
            pillow = lid & (cu ** 2.4 + cvv ** 2.4 + (LF.nz(w, h, 7, 988, 2) - 0.5) * 0.5 < 1.0) & ~(sm & (V > 0.3))
            cv.put(pillow, '#A1AAB7', 0.86 + (1 - V[pillow]) * 0.14)
            cv.put(LF.edge_top(pillow), '#DEE2E7', 1.0)
            cv.put(pillow & ~C.shift(pillow, 0, 1), '#687789', 1.0)
            wet = lid & ~pillow & (cu ** 2.4 + cvv ** 2.4 < 1.35)
            cv.mix(wet, '#0B0C0F', 0.35)
            cv.put(lid & (yy >= fy - 1), '#5E666E', 0.95)              # the front edge's thickness
            cv.put(lid & (yy >= fy), '#15171C', 1.0)
        elif fr == 1:
            top = by_ - 24
            q = [(b0 - 3, by_), (b1 + 3, by_), (f1_ + 5, top), (f0 - 5, top)]
            slit = cv.poly([(b0 + 2, by_ + 1), (b1 - 2, by_ + 1), (f1_ - 4, fy - 2), (f0 + 4, fy - 2)])
            cv.emit(slit, '#D8662A', 0.7 + (yy[slit] - by_) / 40.0)
            cv.emit(slit & (yy > fy - 8), '#F2A044', 0.9)
            lid = cv.poly(q)
            V = np.clip((by_ - yy) / 24.0, 0, 1)
            left = (b0 - 3) + ((f0 - 5) - (b0 - 3)) * V
            right = (b1 + 3) + ((f1_ + 5) - (b1 + 3)) * V
            U = (xx - left) / np.maximum(1.0, right - left)
            cv.light(320, by_ + 8, 160, (1.1, 0.5, 0.16), 1.3)       # the fire lights its rising edge
            _iron_plate(cv, lid, U * 140, (1 - V) * 30, 140, 30, 'tread')
            edge = cv.poly([(f0 - 5, top - 3), (f1_ + 5, top - 3), (f1_ + 5, top), (f0 - 5, top)])
            cv.put(edge, '#323840', 1.0)
            cv.put(edge & (yy == top - 3), '#8A929A', 1.0)
            # the snow sliding off the front edge in clumps
            slide = cv.poly([(b0 + 6, top - 4), (b1 - 6, top - 4), (b1 - 2, top - 9), (b0 + 2, top - 9)]) & \
                (LF.nz(w, h, 3, 989, 2) > 0.42)
            cv.put(slide, '#C2C9D2', 0.95)
            cv.put(LF.edge_top(slide), '#F2F3F5', 1.0)
            for cx_, cy_ in ((268, top - 14), (300, top - 18), (344, top - 12), (372, top - 16)):
                cv.put(cv.ell(cx_, cy_, 3, 2), '#C2C9D2', 0.95)
        else:
            top = by_ - 74
            q = [(b0 - 4, by_ + 1), (b1 + 4, by_ + 1), (b1 + 4, top), (b0 - 4, top)]
            lid = cv.poly(q)
            U = (xx - (b0 - 4)) / float(b1 - b0 + 8)
            V = (yy - top) / float(by_ + 1 - top)
            cv.light(320, by_ + 20, 110, (1.2, 0.52, 0.16), 1.25)    # the fire below lights the lid's foot
            _iron_plate(cv, lid, U * 150, V * 75, 150, 75, 'ribs')
            # the cast date on the centre panel, raised letters
            tm2 = np.repeat(np.repeat(tm, 2, 0), 2, 1)
            sm = K.place(tm2, w, h, (b0 + b1) // 2 - ox - tm2.shape[1] // 2, by_ - 46 - oy)
            cv.put(sm & lid, '#5E666E', 1.0)
            cv.put(sm & lid & ~C.shift(sm, 0, -1), '#A1AAB7', 1.0)
            cv.put(sm & lid & ~C.shift(sm, 0, 1), '#0B0C0F', 1.0)
            # the lid's thickness (its side), the hinge knuckles at the foot, soot streaks up from the mouth
            side = cv.box(b1 + 4, top + 2, b1 + 7, by_ + 1)
            cv.put(side, '#15171C', 1.0)
            cv.put(side & (xx == b1 + 6), '#464D55', 1.0)
            for hx in (b0 + 14, b1 - 20):
                kn = cv.box(hx, by_ - 4, hx + 8, by_ + 2)
                cv.put(kn, '#323840', 1.0)
                cv.put(LF.edge_top(kn), '#8A929A', 1.0)
            # soot: a smooth darkening toward the foot (the smoke has been pouring past it), no blotches
            foot = lid & (yy > by_ - 26)
            cv.mix(foot, '#0B0807', np.clip((yy - (by_ - 26)) / 26.0, 0, 1) * 0.55)
            cv.put(lid & (yy >= top) & (yy < top + 1), '#A1AAB7', 1.0)     # snow left on its top edge
        frames.append(cv.quant(PAL_Y, spread=6.0))
    LE['hatch_at'] = [ox, oy]
    return Q.sheet(frames)


# ================================================================================================ e3a into the hatch
def e3a_bg():
    """Looking down into the open hatch from its front rim: the iron rim with snow and the cast date, the chute's
    brick walls going down into the smoke, the steel slide, the fire's glow deep below."""
    cv = LF.Cv(VW, VH, 0, 0, amb=(0.32, 0.34, 0.42))
    xx, yy = cv.xx, cv.yy
    cv.light(600, 0, 520, (0.9, 0.82, 0.62), 1.3)
    cv.light(320, 330, 280, (1.4, 0.6, 0.22), 1.3)
    n1 = cv.nz(12, 991)
    cv.put(cv.full(), '#A1AAB7', 0.75 + n1 * 0.18)
    cell = LF.hsh(np.floor(xx / 14), np.floor(yy / 18), 993.0)
    prints = (cell > 0.9) & (np.hypot(np.mod(xx, 14) - 7, (np.mod(yy, 18) - 9) * 0.7) < 3.2)
    cv.put(prints, '#7D8796', 0.8)
    rim_ = cv.poly([(70, 360), (570, 360), (560, 40), (80, 40)])
    hole = cv.poly([(118, 330), (522, 330), (512, 64), (128, 64)])
    cv.put(rim_ & ~hole, '#323840', 0.9)
    cv.put(rim_ & ~hole & (np.mod(xx + yy * 0.2, 22) < 2), '#15171C', 1.0)
    cv.put(rim_ & C.rim(rim_, 0, -1, 3), '#C2C9D2', 0.95)
    # inside: the chute's four walls converging toward the glow below (vanishing point low in the frame)
    vx, vy = 320.0, 250.0
    dx = xx + 0.5 - vx
    dy = yy + 0.5 - vy
    left = hole & (dx < 0) & (np.abs(dx) * 0.66 > np.abs(dy))
    right = hole & (dx > 0) & (np.abs(dx) * 0.66 > np.abs(dy))
    top = hole & (dy < 0) & ~left & ~right
    bottom = hole & ~left & ~right & ~top
    rad = np.hypot(dx / 1.3, dy)
    depth = np.clip(1 - rad / 200.0, 0, 1)
    Zs = 40.0 / np.maximum(rad, 4.0)                                  # depth down the shaft (m-ish)
    for m_, uu in ((left, dy / np.maximum(np.abs(dx), 1) * 2.0), (right, dy / np.maximum(np.abs(dx), 1) * 2.0),
                   (top, dx / np.maximum(np.abs(dy), 1) * 2.0)):
        _bricks(cv, m_, uu, Zs, 999, 0.18, 0.5, base='#2A1C15', mortar='#0A0706', k=1.0)
    cv.put(bottom, '#323840', 0.75)
    cv.put(bottom & (np.mod(Zs, 0.5) < 0.05), '#5E666E', 0.8)
    cv.mix(hole, '#050404', np.clip(depth * 1.35, 0, 0.92))
    hot = np.clip(1 - np.hypot(dx / 60.0, dy / 44.0), 0, 1)
    cv.add(hole & (pg.bayer(VW, VH, 0, 0) < hot * 1.2), '#4A1408', 1.0)
    cv.put(hole & C.rim(hole, 0, -1, 4), '#05070B', 1.0, lit=False)
    tm = np.repeat(np.repeat(K.vtext('1909', 'l', 2), 2, 0), 2, 1)
    sm = K.place(tm, VW, VH, 320 - tm.shape[1] // 2, 46)
    cv.put(sm & rim_, '#7A828A', 1.0)
    out = cv.quant(PAL_Y, spread=10.0)
    out[..., 3] = 255
    return out


# ================================================================================================ e3b in the snow
def e3b_bg():
    cv = LF.Cv(VW, VH, 0, 0, amb=(0.24, 0.27, 0.36))
    xx, yy = cv.xx, cv.yy
    cv.light(560, 30, 400, (1.05, 0.9, 0.62), 1.4)
    cv.light(520, 168, 140, (1.2, 0.52, 0.2), 1.35)
    cv.light(270, 200, 110, (0.6, 0.3, 0.12), 1.4)
    n1 = cv.nz(10, 995)
    wall = yy < E3B_SNOW - 30
    row = np.floor(yy / 22)
    off = np.where(np.mod(row, 2) == 0, 0, 26)
    blk = LF.hsh(row, np.floor((xx + off) / 52), 9.0)
    cv.put(wall, '#2B3644', 0.75 + blk[wall] * 0.15 + n1[wall] * 0.08)
    jt = wall & ((np.mod(yy, 22) < 2) | (np.mod(xx + off, 52) < 2))
    cv.put(jt, '#10151D', 1.0)
    # the souterrain window at the right glowing, soot above it
    win = cv.box(486, 140, 556, E3B_SNOW - 32)
    cv.emit(win, '#A8381A', 0.8 + LF.nz(VW, VH, 4, 997, 2)[win] * 0.4)
    cv.put(win & (np.mod(xx, 11) < 2), '#05070B', 1.0)
    soot = (xx > 490) & (xx < 552) & (yy < 140) & (yy > 92) & (pg.bayer(VW, VH, 0, 0) < 0.6 - (140 - yy) / 90.0)
    cv.put(soot, '#05070B', 1.0)
    pl = (yy >= E3B_SNOW - 30) & (yy < E3B_SNOW - 22)
    cv.put(pl, '#394656', 0.9)
    cv.put((yy >= E3B_SNOW - 31) & (yy < E3B_SNOW - 29), '#A1AAB7', 0.95)
    g = yy >= E3B_SNOW - 22
    u = (yy - (E3B_SNOW - 22)) / (VH - E3B_SNOW + 22)
    cv.put(g, '#7D8796', 0.62 + n1[g] * 0.12 + u[g] * 0.2)
    drag = g & (np.abs(yy - (E3B_SNOW - 4) - (xx - 270) * 0.18) < 5) & (xx > 270) & (xx < 340) & \
        (LF.vnoise(xx * 0.4, yy * 0.4, 999) > 0.4)
    cv.put(drag, '#4F5E70', 0.85)
    coal = g & (LF.hsh(np.floor(xx / 5), np.floor(yy / 4), 13.0) > 0.996) & (np.abs(xx - 280) < 90)
    cv.put(coal, '#0A0D13', 1.0)
    fr = cv.poly([(214, E3B_SNOW - 18), (334, E3B_SNOW - 18), (344, E3B_SNOW - 8), (204, E3B_SNOW - 8)])
    cv.put(fr, '#323840', 0.95)
    cv.put(LF.edge_top(fr), '#7A828A', 0.95)
    out = cv.quant(PAL_Y, spread=10.0)
    out[..., 3] = 255
    LE['e3b_hatch'] = [204, E3B_SNOW - 66]
    return out


def e3b_hatch():
    w, h = 144, 62
    frames = []
    for fr in range(2):
        cv = LF.Cv(w, h, 0, 0, amb=(0.45, 0.46, 0.55))
        if fr == 0:
            lid = cv.poly([(18, 50), (126, 50), (124, 4), (20, 4)])
            cv.put(cv.poly([(12, 60), (132, 60), (126, 50), (18, 50)]), '#05070B', 1.0)
        else:
            lid = cv.poly([(8, 61), (136, 61), (128, 49), (16, 49)])
        cv.put(lid, '#323840', 0.9)
        cv.put(lid & C.rim(lid, 0, -1), '#7A828A', 0.95)
        cv.put(lid & (np.mod(cv.xx, 22) < 2), '#5E666E', 0.9)
        if fr == 0:
            tm = K.vtext('1909', 's', 1)
            cv.put(K.place(tm, w, h, 72 - tm.shape[1] // 2, 20) & lid, '#7A828A', 1.0)
        frames.append(cv.quant(PAL_Y, spread=6.0))
    return Q.sheet(frames)


# ================================================================================================ e4 the east wing
def e4_bg():
    cv = LF.Cv(VW, VH, 0, 0, amb=(0.20, 0.23, 0.32))
    xx, yy = cv.xx, cv.yy
    glow = cv.light(320, 250, 460, (0.7, 0.32, 0.12), 1.2)
    cv.light(560, 230, 120, (0.9, 0.75, 0.5), 1.5)                    # the lane's lamp
    n1 = cv.nz(16, 999)
    n2 = cv.nz(4, 1001)
    sky = yy < 84
    cv.put(sky, '#1A2431', 0.5 + n1[sky] * 0.3 + np.clip((yy[sky] - 30) / 54.0, 0, 1) * 0.4)
    # mansard, chimneys, dormers
    roof = (yy >= 58) & (yy < 84)
    cv.put(roof, '#1E2836', 0.8 + (yy[roof] - 58) / 26.0 * 0.3)
    cv.put((yy >= 56) & (yy < 60), '#A1AAB7', 0.95)
    for cx in (96, 300, 520):
        ch = cv.box(cx, 34, cx + 16, 62)
        cv.put(ch, '#202935', 0.9)
        cv.put(cv.box(cx - 2, 32, cx + 18, 35), '#A1AAB7', 0.95)
    for dx in range(40, 640, 92):
        cv.put(cv.box(dx + 6, 64, dx + 26, 80), '#2B3644', 0.9)
        cv.put(cv.box(dx + 10, 68, dx + 22, 78), '#0A0D13', 1.0)
        cv.put(cv.box(dx + 4, 62, dx + 28, 64), '#A1AAB7', 0.9)
    wall = (yy >= 84) & (yy < 262)
    cv.put(wall, '#2B3644', 0.75 + n1[wall] * 0.12 + n2[wall] * 0.04)
    cor = (yy >= 84) & (yy < 94)
    cv.put(cor, '#394656', 1.0)
    cv.put((yy >= 80) & (yy < 84), '#C2C9D2', 0.95)
    for px_ in range(0, 640, 92):
        pil = (xx >= px_ - 5) & (xx < px_ + 5) & (yy >= 94) & (yy < 196)
        cv.put(pil, '#394656', 0.95)
        cv.put(pil & (xx >= px_ + 3), '#202935', 1.0)
    for i, wx in enumerate(range(28, 640, 92)):
        for j, (wy0, wy1) in enumerate(((104, 142), (154, 188))):
            w_ = cv.box(wx, wy0, wx + 36, wy1)
            lit = (i == 4 and j == 0)
            if lit:
                cv.emit(w_, '#A8703A', 0.95 - (yy[w_] - wy0) / 60.0)
                cv.emit(w_ & (np.mod(xx, 4) < 1), '#7E5226', 0.9)
            else:
                cv.put(w_, '#0A0D13', 0.9 + n2[w_] * 0.3)
                cv.put(w_ & (yy < wy0 + 6), '#202935', 0.9)
            cv.put(w_ & (np.abs(xx - wx - 18) < 1), '#2B3644', 1.0)
            cv.put(cv.box(wx - 3, wy0 - 4, wx + 39, wy0), '#394656', 1.0)
            if j == 0:
                ped = cv.poly([(wx - 4, wy0 - 4), (wx + 18, wy0 - 12), (wx + 40, wy0 - 4)])
                cv.put(ped, '#394656', 1.0)
                cv.put(LF.edge_top(ped), '#C2C9D2', 0.95)
            cv.put(cv.box(wx - 3, wy1, wx + 39, wy1 + 3), '#C2C9D2', 0.92)
    base = (yy >= 196) & (yy < 262)
    cv.put(base & (np.mod(yy - 196, 13) < 1.2), '#10151D', 1.0)
    cv.put((yy >= 194) & (yy < 198), '#4A5868', 1.0)
    souts = []
    for wx in range(28, 640, 92):
        well = cv.box(wx - 4, 222, wx + 40, 262)
        cv.put(well, '#10151D', 1.0)
        w_ = cv.box(wx + 2, 224, wx + 34, 252)
        cv.put(w_, '#05070B', 1.0)
        cv.put(cv.box(wx, 252, wx + 36, 255), '#C2C9D2', 0.95)
        rail = cv.box(wx - 6, 248, wx + 42, 262) & ((np.mod(xx, 5) < 1) | (yy < 250))
        cv.put(rail, '#05070B', 1.0)
        souts.append([wx + 2, 224])
    # the neighbouring houses at the edges, set back, a few lit windows
    for (x0, x1) in ((-10, 18), (622, 650)):
        nb = cv.box(x0, 60, x1, 262)
        cv.put(nb, '#171E28', 0.9)
    # the lane: snow, ruts, the glow of the fire on it, a lamp post, bare lime trees, a snowed-in car
    g = yy >= 262
    u = (yy - 262) / 98.0
    cv.put(g, '#7D8796', 0.6 + n1[g] * 0.12 + u[g] * 0.25)
    ruts = g & ((np.abs(yy - 282 - (xx - 320) * 0.02) < 1.5) | (np.abs(yy - 298 + (xx - 320) * 0.015) < 1.5))
    cv.put(ruts, '#4F5E70', 0.9)
    LF.lamp_post(cv, 560, 300, 120, col='#05070B', style='lantern')
    for i, tx in enumerate((150, 430)):
        LF.tree(cv, tx, 304, 230, 1011 + i, col='#05070B', snow='#7D8796', spread=1.1, trunk_r=4.0)
        cv.put(cv.ell(tx, 305, 12, 3), '#A1AAB7', 0.9)
    LF.car(cv, 252, 312, s=2.1, facing=1, body='#26303A', snow='#C2C9D2', seed=1015)
    out = cv.quant(PAL_Y, spread=10.0)
    out[..., 3] = 255
    LE['e4_windows'] = souts
    return out


# ================================================================================================ e4 the brigade (round 11)
def e4_engine():
    """e4: the fire engine's nose nosing into the lane from the right (2 frames: the beacon's lamp facing us / away):
    red bonnet and wing lit orange by the fire from the left, the chrome grille and bumper, a headlamp, the brass
    bell, the cab with its dark windscreen, the ladder on the roof, the blue beacon on the cab; 128 x 64,
    bottom-left at the front wheel's foot."""
    w, h = 128, 64
    frames = []
    for fr in range(2):
        cv = LF.Cv(w, h, 0, 0, amb=(0.30, 0.32, 0.42))
        cv.light(-60, 20, 200, (1.4, 0.6, 0.2), 1.2)                   # the burning wing to the left
        cv.light(64, 40, 140, (0.3, 0.32, 0.4), 1.4)
        xx, yy = cv.xx, cv.yy
        body = cv.poly([(8, 30), (40, 26), (52, 18), (128, 18), (128, 54), (6, 54), (4, 44)])
        cv.put(body, '#7A2218', 0.9 + C.edge_light(body, (-0.9, -0.3), width=4.0, soft=1)[body] * 0.7)
        cv.put(body & (yy < 34) & (xx < 52), '#A8382E', 0.9)            # the bonnet's top catches the fire
        cab = cv.poly([(52, 18), (60, 6), (128, 6), (128, 18)])
        cv.put(cab, '#5A1A14', 0.95)
        ws = cv.poly([(56, 17), (62, 9), (84, 9), (84, 17)])
        cv.put(ws, '#0C111C', 1.0)
        cv.put(ws & (np.abs(xx - yy * 0.6 - 62) < 1.2), '#4F5E70', 1.0)
        cv.put(cv.box(60, 4, 128, 6), '#3A2A22', 1.0)
        lad = cv.box(70, 0, 128, 4) & ((yy == 0) | (yy == 3) | (np.mod(xx, 6) == 0))
        cv.put(lad, '#8E856C', 0.95)
        grille = cv.box(4, 30, 12, 50)
        cv.put(grille, '#5E666E', 0.9)
        cv.put(grille & (np.mod(yy, 2) == 0), '#2B3038', 1.0)
        cv.put(cv.box(0, 48, 30, 52), '#8E969E', 0.95)                   # the bumper
        cv.put(cv.box(0, 48, 30, 49), '#C8C4BA', 1.0)
        cv.emit(cv.ell(16, 38, 4, 4), '#FCE2B0')                        # the headlamp
        cv.put(cv.ring(16, 38, 4, 5.5), '#8E969E', 1.0)
        bell = cv.ell(30, 26, 4, 4) & (yy < 28)
        cv.put(bell, '#C49A48', 1.1)
        cv.put(cv.box(29, 27, 32, 30), '#9C7630', 1.0)
        for wx in (24, 104):
            cv.put(cv.ell(wx, 56, 9, 8), '#0B0D10', 1.0)
            cv.put(cv.ell(wx, 56, 4, 3.5), '#5E666E', 0.9)
        cv.put(cv.box(40, 40, 128, 42), '#C8C4BA', 0.8)                  # the white band along its side
        # the beacon on the cab: a blue glass dome, lit when it faces us
        cv.put(cv.box(72, 0, 80, 3), '#15171C', 1.0)
        dome = cv.ell(76, -1, 4, 4) & (yy < 1)
        if fr == 0:
            cv.emit(dome | cv.ell(76, 0, 3, 2), '#C8DAFF')
        else:
            cv.put(dome | cv.ell(76, 0, 3, 2), '#2A3E7A', 1.0, lit=False)
        frames.append(cv.quant(PAL_Y + ['#C8DAFF', '#2A3E7A', '#7A2218', '#A8382E', '#5A1A14'], spread=6.0))
    return Q.sheet(frames)


def e4_beacon_glow():
    """Additive blue glow of the beacon (64 x 64), drawn at the lamp, pulsing as it turns."""
    a = np.zeros((64, 64, 3), np.float32)
    Q.add_glow(a, 32, 32, 30, 30, (30, 46, 110), 1.6)
    Q.add_glow(a, 32, 32, 9, 9, (60, 80, 140), 1.2)
    return K.soft_quant(a, 2.0)


def e4_beacon_wash():
    """Additive blue wash the turning beacon throws over the snow and the facade (240 x 120, soft)."""
    a = np.zeros((120, 240, 3), np.float32)
    Q.add_glow(a, 120, 60, 118, 58, (16, 26, 64), 1.3)
    return K.soft_quant(a, 2.0)
