"""env_c3p2_cine_rooms -- the two hotel rooms of LS_C3_Radio r2/r3, round 10 (owner: c3p2 places stream).

One window/table geometry for both rooms (the match cut on the dial: env_c3p2_cine_radio WIN, MULLION, RADIO_AT,
DIAL, TABLE_Y), lit as float colour and snapped to a room palette:
  room_alexei  Hotel Nord, room 214: painted plaster with a stencilled border and a dado, a white double casement
               with frost flowers in the corners, cotton curtains, the radiator's warmth, the oak table with the
               doily, the tea glass in its holder, sugar, a folded newspaper,
               the quilted coat and the ushanka on the hook, a cheap landscape print; across the square the
               Europa's mansard and windows, Konrad's lit window, the lamp globes and the tram wires below
  room_konrad  Hotel Europa, room 317: damask above a panelled wainscot, a picture rail, velvet curtains with
               tasselled tie-backs over a net curtain, a wall sconce, the desk with its leather inlay, blotter,
               notepad, inkstand, the conference folder, a coffee cup, the hat, the brass
               desk lamp (its reflection in the glass); the coat stand with the coat and scarf; across the square
               the Nord's flat front, its roof letters, Alexei's lit window
  chair_alexei / chair_konrad   the chair backs in front of the men (drawn over the figures at runtime)
The men themselves come from the figures stream (env_c3p2_cine_figs.room_alexei / room_konrad).
"""
from __future__ import annotations

import math

import numpy as np

import env_c3p2_cine_kit as Q
from env_c3p2_cine_kit import (C, K, VW, VH, NIGHT, SNOW, LAMP, OAK, PAPER, BRASS, BAKE, RED)
import env_c3p2_cine_life as LF
import env_c3p2_cine_radio as RD

L = Q.LAYOUT.setdefault('radio', {})
WIN = RD.WIN
MUL = RD.MULLION
TY = RD.TABLE_Y
DIAL = RD.DIAL

PAL_A = LF.palette(NIGHT, SNOW, LAMP, OAK, PAPER, BRASS, BAKE[:6],
                   ['#0A0E0E', '#111818', '#192222', '#222E2D', '#2D3A39', '#3B4A48', '#4E605C', '#66786E',
                    '#1E2A24', '#2A3A30', '#3A4C3E', '#536452', '#0E1A14', '#16261D', '#20342A', '#2E4636',
                    '#3A3226', '#4E4234', '#6A5A46', '#8A7860', '#2A3646', '#3A4859', '#4F5E70', '#1A2431',
                    '#7A3A2C', '#A8382E', '#5A2A22', '#C2B8A0', '#E0D6BC', '#9A9078'])
PAL_K = LF.palette(NIGHT, SNOW, LAMP, OAK, PAPER, BRASS, BAKE[:6],
                   ['#100A0A', '#1A0F10', '#261616', '#331D1C', '#432826', '#563532', '#6E443C', '#8A5A48',
                    '#14080A', '#22100F', '#341815', '#4A221C', '#622E22', '#7A3A2A', '#0C1A14', '#163024',
                    '#22442F', '#2E5640', '#05070E', '#0B0F1C', '#131A2C', '#1D2442', '#2C3B5E', '#3A4A6A',
                    '#2A3646', '#3A4859', '#4F5E70', '#1A2431', '#C2B8A0', '#E0D6BC', '#9A9078', '#B8AE96'])


# ================================================================================================ the view
def _view(cv, kind, lit_xy):
    """The hotel across the square through the window: night sky with lit snow clouds, the facade frontally
    (~5 px per metre), one lit window with the other man at his radio, the square below with the lamp globes
    and the tram wires; frost flowers in the pane corners."""
    x0, y0, x1, y1 = WIN
    xx, yy = cv.xx, cv.yy
    inside = (xx >= x0) & (xx < x1) & (yy >= y0) & (yy < y1)
    n1 = cv.nz(9, 503)
    n2 = cv.nz(26, 505)
    europa = kind == 'europa'
    roof_y = 84 if europa else 80
    sky = inside & (yy < roof_y)
    cv.put(sky, '#1A2431', 0.55 + n2[sky] * 0.35 + (yy[sky] - y0) / 90.0, lit=False)
    fac = inside & (yy >= roof_y) & (yy < 190)
    cv.put(fac, '#2A3646' if europa else '#323E4C', 0.62 + n1[fac] * 0.18, lit=False)
    if europa:
        mans = inside & (yy >= 66) & (yy < 84)
        slope = np.abs(np.mod(xx - x0, 27) - 13.5)
        cv.put(mans & (yy >= 70 + np.clip(slope - 9, 0, 9) * 0.0), '#1E2836', 0.8, lit=False)
        for dx_ in range(x0 + 6, x1, 27):
            d = inside & (xx >= dx_) & (xx < dx_ + 9) & (yy >= 70) & (yy < 82)
            cv.put(d, '#2A3646', 0.8, lit=False)
            g = inside & (xx >= dx_ + 2) & (xx < dx_ + 7) & (yy >= 73) & (yy < 80)
            if LF.hsh(dx_, 1.0, 2.0) < 0.25:
                cv.emit(g, '#7E5226', 0.9)
            else:
                cv.put(g, '#0A0E16', 1.0, lit=False)
            cv.put(inside & (xx >= dx_ - 1) & (xx < dx_ + 10) & (yy >= 68) & (yy < 70), '#A1AAB7', 0.9, lit=False)
        cv.put(inside & (yy >= 84) & (yy < 88), '#3E4C5E', 0.9, lit=False)                # cornice
        cv.put(inside & (yy >= 83) & (yy < 85), '#A1AAB7', 0.85, lit=False)
        cols, rows, ww, wh = 20, ((96, 114), (124, 142), (152, 170)), 7, 15
    else:
        cv.put(inside & (yy >= 76) & (yy < 80), '#3E4C5E', 0.9, lit=False)                # parapet
        cv.put(inside & (yy >= 75) & (yy < 77), '#A1AAB7', 0.85, lit=False)
        tm = K.vtext('HOTEL NORD', 's', 1)
        tm = np.repeat(np.repeat(tm, 2, 0), 2, 1)
        lx0 = x0 + 170
        frame = inside & (yy >= 72) & (yy < 76) & (xx >= lx0 - 2) & (xx < lx0 + tm.shape[1] + 2)
        cv.put(frame & (np.mod(xx, 5) < 1), '#0A0E16', 1.0, lit=False)
        sm = K.place(tm, cv.w, cv.h, lx0 - cv.ox, 58 - cv.oy) & inside
        cv.emit(sm, '#E8DCC0')
        cols, rows, ww, wh = 17, ((92, 104), (112, 124), (132, 144), (152, 164)), 8, 11
    for cxw in range(x0 + 8, x1, cols):
        for j, (ry0, ry1) in enumerate(rows):
            win = inside & (xx >= cxw) & (xx < cxw + ww) & (yy >= ry0) & (yy < ry1)
            hv = LF.hsh(cxw, ry0, 11.0 if europa else 13.0)
            if hv < 0.1:
                cv.emit(win, '#7E5226', 0.8 + hv * 2)
                cv.emit(win & (np.mod(xx, 3) == 0), '#5A3A1C', 1.0)
            else:
                cv.put(win, '#0A0E16', 0.9 + n1[win] * 0.3, lit=False)
            cv.put(inside & (xx >= cxw - 1) & (xx < cxw + ww + 1) & (yy == ry1), '#A1AAB7', 0.85, lit=False)
            if europa and j == 0:
                ped = inside & (yy >= ry0 - 4) & (yy < ry0) & (np.abs(xx - cxw - ww / 2) < 5 - (ry0 - yy) * 0.9)
                cv.put(ped, '#3E4C5E', 0.9, lit=False)
                cv.put(LF.edge_top(ped), '#A1AAB7', 0.85, lit=False)
            if europa and j == 2 and (cxw - x0) // cols % 2 == 0:
                bal = inside & (xx >= cxw - 2) & (xx < cxw + ww + 2) & (yy >= ry1 + 1) & (yy < ry1 + 4)
                cv.put(bal & ((np.mod(xx, 2) == 0) | (yy == ry1 + 1)), '#0A0E16', 1.0, lit=False)
    # the other man's lit window: warm light, a mullion, his head and shoulders at his own radio
    lx, ly = lit_xy
    lwin = inside & (xx >= lx) & (xx < lx + ww) & (yy >= ly) & (yy < ly + wh)
    cv.emit(lwin, '#D09A58', 1.08 - (yy - ly) / wh * 0.3)
    cv.emit(lwin & (np.abs(xx - (lx + ww // 2)) < 0.6), '#5A3A1C')
    hx = lx + ww * (0.32 if europa else 0.68)
    head = cv.ell(hx, ly + wh - 5.0, 1.5, 1.8) | cv.poly([(hx - 3, ly + wh), (hx - 2.2, ly + wh - 3.2),
                                                         (hx + 2.2, ly + wh - 3.2), (hx + 3, ly + wh)])
    cv.put(head & lwin, '#1A0F0A', 1.0, lit=False)
    # the square below: snow with the lamp light, the globes, the tram wires
    ground = inside & (yy >= 190)
    cv.put(ground, '#4F5E70', 0.75 + n1[ground] * 0.25 + (yy[ground] - 190) / 40.0, lit=False)
    for gx in (x0 + 40, x0 + 170, x0 + 300):
        glow_ = inside & cv.ell(gx, 205, 26, 9) & (yy >= 190)
        cv.add(glow_, '#3A2410', 0.8)
        cv.emit(cv.ell(gx, 197, 2.2, 2.4) & inside, '#FCE2B0')
        cv.put(cv.box(gx - 0.5, 199, gx + 0.5, 214) & inside, '#0A0E16', 1.0, lit=False)
    for k_ in (-1, 1):
        cv.put(cv.seg([(x0, 188 + k_ * 3), (x1, 182 + k_ * 3)], 0.45) & inside, '#0A0E16', 1.0, lit=False)
    return inside


def _frost(cv, inside, seed):
    """Frost flowers growing from the corners of the panes (fern-like, pale)."""
    x0, y0, x1, y1 = WIN
    xx, yy = cv.xx, cv.yy
    frost = np.zeros_like(inside)
    for (px0, px1) in ((x0 + 4, MUL - 3), (MUL + 3, x1 - 4)):
        for (cx, cy, sx, sy) in ((px0, y1 - 6, 1, -1), (px1, y1 - 6, -1, -1), (px0, y0 + 26, 1, 1)):
            d = np.hypot((xx - cx) * 1.0, (yy - cy) * 1.4)
            r = 34 if cy > 100 else 18
            fern = (np.mod((xx - cx) * sx * 0.7 + (yy - cy) * sy * 0.7 + LF.nz(cv.w, cv.h, 3, seed, 2) * 6, 5.0) < 1.2)
            frost |= inside & (d < r * (0.6 + 0.5 * LF.nz(cv.w, cv.h, 6, seed + 1, 2))) & fern
    cv.mix(frost, '#C2C9D2', 0.55)
    return frost


# ================================================================================================ rooms
def _alexei(cv):
    xx, yy = cv.xx, cv.yy
    x0, y0, x1, y1 = WIN
    n1 = cv.nz(14, 611)
    n2 = cv.nz(3, 613)
    # light: the radio's dial (warm, centre), the window (cold), the street glow from below outside
    cv.light(DIAL[0], DIAL[1], 270, (1.25, 0.82, 0.42), 1.5)
    cv.light(DIAL[0], TY - 2, 210, (0.9, 0.58, 0.28), 1.8, sy=0.35)
    cv.light((x0 + x1) / 2, 140, 300, (0.30, 0.38, 0.55), 1.3)
    cv.light(600, 170, 150, (0.42, 0.50, 0.66), 1.2)
    cv.light(60, 230, 170, (0.26, 0.30, 0.42), 1.3)
    wall = cv.full()
    cv.put(wall, '#4E605C', 0.62 + n1 * 0.12 + n2 * 0.03)
    # stencilled border under the ceiling, the dado below the window line, a picture hook, the switch
    border = (yy >= 46) & (yy < 52)
    cv.put(border, '#3A4C3E', 0.9)
    cv.put(border & (np.mod(xx + (yy - 46) * 2, 8) < 2), '#66786E', 0.9)
    dado = yy >= 202
    cv.put(dado, '#2A3A30', 0.8 + n1[dado] * 0.12)
    cv.put((yy >= 200) & (yy < 202), '#536452', 0.9)
    stain = (np.hypot(xx - 560, (yy - 110) * 1.3) < 30) & (LF.nz(cv.w, cv.h, 7, 619, 2) > 0.55)
    cv.put(stain & ~dado, '#4E605C', 0.52)
    cv.put(cv.box(552, 168, 558, 178), '#C2B8A0', 0.7)
    cv.put(cv.box(554, 171, 556, 175), '#4E4234', 0.8)
    # a cheap landscape print in a thin frame on the right wall (birches, a river)
    fx0, fy0, fx1, fy1 = 524, 76, 572, 112
    fr = cv.box(fx0, fy0, fx1, fy1)
    cv.put(fr, '#3A3226', 1.0)
    pic = cv.box(fx0 + 3, fy0 + 3, fx1 - 3, fy1 - 3)
    cv.put(pic, '#8A7860', 0.75)
    cv.put(pic & (yy > fy0 + 18), '#536452', 0.8)
    cv.put(pic & (np.abs(yy - (fy0 + 24 - (xx - fx0) * 0.08)) < 1.5), '#9A9078', 0.9)
    for bx in (fx0 + 9, fx0 + 14, fx0 + 33):
        cv.put(pic & (np.abs(xx - bx) < 0.8) & (yy > fy0 + 6), '#E0D6BC', 0.9)
    cv.put(cv.seg([(548, fy0), (548, 66)], 0.4), '#3A3226', 0.9)
    # window: reveal, the view, frame (painted white, double casement + transom), sill
    reveal = (xx >= x0 - 10) & (xx < x1 + 10) & (yy >= y0 - 8) & (yy < y1 + 6)
    cv.put(reveal, '#66786E', 0.62 + n1[reveal] * 0.1)
    inside = _view(cv, 'europa', (230, 112))
    _frost(cv, inside, 621)
    frame = inside & ((np.abs(xx - MUL) < 3) | (xx < x0 + 4) | (xx >= x1 - 4) | (yy < y0 + 4) |
                      (np.abs(yy - 92) < 2) | (yy >= y1 - 5))
    cv.put(frame, '#C2B8A0', 0.62)
    cv.put(frame & (np.abs(xx - MUL) < 1), '#9A9078', 0.6)
    cv.put(cv.box(MUL - 6, 140, MUL - 3, 150) | cv.box(MUL + 3, 140, MUL + 6, 150), '#C2B8A0', 0.9)   # latches
    cv.put(inside & (yy >= y1 - 6) & (yy < y1 - 4), '#A1AAB7', 0.9, lit=False)                    # outer sill snow
    cv.put(cv.box(x0 - 14, y1 + 2, x1 + 14, y1 + 8), '#C2B8A0', 0.66)                              # inner sill
    # curtains: cotton with a small check, gathered at the sides on a rod
    cv.put(cv.box(x0 - 34, y0 - 16, x1 + 34, y0 - 13), '#3A3226', 1.0)
    for side in (-1, 1):
        cxa = x0 - 30 if side < 0 else x1 - 18
        cur = (xx >= cxa) & (xx < cxa + 48) & (yy >= y0 - 13) & (yy < 228)
        cur &= (xx < x0 + 18) if side < 0 else (xx >= x1 - 18)
        bulge = np.sin((yy - y0) / 170.0 * np.pi) * 6
        cur &= (xx < x0 + 12 - bulge) if side < 0 else (xx >= x1 - 12 + bulge)
        fold = np.sin((xx - cxa) * 0.7) * 0.18
        chk = ((np.mod(xx, 6) < 1) | (np.mod(yy, 6) < 1))
        cv.put(cur, '#8A7860', 0.72 + fold + (cv.L[..., 2] - 0.4) * 0.0)
        cv.put(cur & chk, '#6A5A46', 0.72 + fold)
    # radiator under the sill (behind the table, the top shows)
    rad = cv.box(x0 + 30, y1 + 8, x1 - 30, TY - 12)
    cv.put(rad, '#9A9078', 0.5)
    cv.put(rad & (np.mod(xx, 6) < 2), '#6A5A46', 0.5)
    # the table: oak top, front apron with a drawer, legs
    top = (yy >= TY - 12) & (yy < TY) & (xx >= 112) & (xx < 568)
    cv.put(top, '#6E4A33', 0.85 + (yy - (TY - 12)) / 30.0 + n2 * 0.05)
    cv.put(top & (yy == TY - 12), '#8A6040', 1.0)
    cv.put(top & (np.mod(xx * 0.3 + yy * 2.0 + LF.nz(cv.w, cv.h, 5, 631, 2) * 4, 6.0) < 0.6), '#553826', 0.9)
    edge = (yy >= TY) & (yy < TY + 6) & (xx >= 112) & (xx < 568)
    cv.put(edge, '#553826', 0.9)
    under = (yy >= TY + 6) & (xx >= 112) & (xx < 568)
    cv.put(under, '#2B1B12', 0.65 + np.clip((yy - TY) / 80.0, 0, 1) * -0.3)
    drawer = cv.box(300, TY + 10, 420, TY + 30)
    cv.put(drawer, '#3D271A', 0.9)
    cv.put(LF.edge_top(drawer) | LF.edge_dir(drawer, -1, 0), '#553826', 0.9)
    cv.put(cv.box(354, TY + 18, 366, TY + 21), '#9C7630', 0.9)
    for lx in (120, 552):
        leg = (xx >= lx) & (xx < lx + 9) & (yy >= TY + 6)
        cv.put(leg, '#3D271A', 0.9)
    # the crocheted doily under the radio, the tea glass in its holder, sugar on a saucer
    doily = cv.ell(328, TY - 5, 112, 8)
    cv.put(doily & ((xx.astype(int) + yy.astype(int)) % 3 != 0), '#E0D6BC', 0.75)
    gx = 476
    glass = (np.abs(xx + 0.5 - gx) < 9 - (TY - yy) * 0.03) & (yy >= TY - 34) & (yy < TY - 3)
    cv.put(glass, '#A8703A', 0.9)
    tea = glass & (yy >= TY - 28)
    cv.put(tea, '#7E5226', 1.05)
    cv.put(glass & (np.abs(xx + 0.5 - (gx - 6)) < 1), '#E0D6BC', 1.2)
    holder = (np.abs(xx + 0.5 - gx) < 10) & (yy >= TY - 18) & (yy < TY - 2)
    cv.put(holder, '#73531F', 1.0)
    cv.put(holder & (np.mod(xx + yy, 4) < 2), '#C49A48', 1.0)
    handle = (np.abs(np.hypot(xx + 0.5 - (gx + 11), yy + 0.5 - (TY - 12)) - 5) < 1.2) & (xx > gx + 10)
    cv.put(handle, '#9C7630', 1.0)
    cv.put((np.abs(xx + 0.5 - (gx + 2)) < 0.6) & (yy >= TY - 42) & (yy < TY - 28), '#C49A48', 1.2)
    sau = cv.ell(gx + 32, TY - 3, 12, 3)
    cv.put(sau, '#E0D6BC', 0.85)
    cv.put(cv.box(gx + 27, TY - 8, gx + 31, TY - 4) | cv.box(gx + 32, TY - 7, gx + 36, TY - 3), '#F2F3F5', 0.9)
    # a folded newspaper at the left end and the room key on its brass fob "214"
    np_ = cv.poly([(516, TY - 9), (560, TY - 11), (564, TY - 2), (520, TY - 1)])
    cv.put(np_, '#C2B8A0', 0.78)
    for ly in range(TY - 8, TY - 2, 2):
        cv.put(np_ & (yy == ly) & (np.mod(xx, 4) < 3) & (xx > 522) & (xx < 558), '#4E4234', 0.9)
    cv.put(np_ & (xx > 520) & (xx < 540) & (yy < TY - 7), '#2A1A14', 0.9)
    # his coat on the hook at the right wall: quilted green with the fur collar, the ushanka above it
    hook = cv.box(606, 96, 610, 110)
    cv.put(hook, '#9C7630', 0.9)
    coat = cv.poly([(594, 116), (603, 108), (614, 108), (626, 118), (636, 150), (640, 262), (586, 262), (582, 200),
                    (586, 144)])
    cv.put(coat, '#26392D', 0.85)
    quilt = coat & (np.mod(yy + np.abs(xx - 610) * 0.25, 9) < 1.2)
    cv.put(quilt, '#12201A', 0.9)
    cv.put(coat & (xx < 590), '#3B5443', 0.85)
    collar = cv.ell(610, 114, 15, 7)
    cv.put(collar, '#57514A', 0.85 + n2[collar] * 0.3)
    hat_crown = cv.ell(608, 88, 12, 9)
    flaps = cv.poly([(595, 88), (590, 106), (598, 108), (601, 92)]) | cv.poly([(621, 88), (626, 106), (618, 108), (615, 92)])
    hat = hat_crown | flaps
    cv.put(hat, '#57514A', 0.75 + n2[hat] * 0.35)
    cv.put(hat_crown & (yy < 84), '#73624E', 0.85)
    cv.put(cv.box(600, 82, 616, 86) & hat_crown, '#474845', 0.8)
    # the iron bedstead at the left (its foot rail and knobs), the grey blanket over the end
    bed = cv.box(0, 232, 106, 330)
    fold_ = np.sin((cv.xx - 4) * 0.09 + (cv.yy - 232) * 0.05) * 0.12
    cv.put(bed, '#4F5E70', 0.55 + LF.nz(cv.w, cv.h, 5, 641, 2) * 0.2 + fold_)
    cv.put(bed & (np.abs(cv.yy - 246 - np.sin(cv.xx * 0.11) * 2) < 1.2), '#2A3646', 0.8)
    cv.put(bed & (np.abs(cv.yy - 262) < 1) & (np.mod(cv.xx, 6) < 3), '#A8382E', 0.7)
    rail = cv.seg([(0, 226), (100, 226)], 1.6) | cv.seg([(100, 226), (100, 320)], 1.8) | cv.seg([(0, 250), (100, 250)], 1.0)
    for bx in range(10, 100, 12):
        rail |= cv.seg([(bx, 226), (bx, 250)], 0.7)
    cv.put(rail, '#3A4859', 0.9 + C.edge_light(rail, (0.6, -0.8), width=2.0, soft=1) * 0.8)
    cv.put(cv.ell(100, 222, 3.2, 3.2), '#9C7630', 1.0)
    pillow = cv.ell(30, 228, 30, 7) & (cv.yy < 232)
    cv.put(pillow, '#C2B8A0', 0.62)
    return cv


def _konrad(cv):
    xx, yy = cv.xx, cv.yy
    x0, y0, x1, y1 = WIN
    n1 = cv.nz(14, 612)
    n2 = cv.nz(3, 614)
    lamp = (206.0, 150.0)
    # light: the desk lamp (strong, warm, left), the dial (warm, centre), the window (cold)
    cv.light(lamp[0], lamp[1] + 10, 380, (1.35, 0.95, 0.52), 1.35)
    cv.light(lamp[0], TY - 4, 260, (1.1, 0.78, 0.4), 1.6, sy=0.4)
    cv.light(DIAL[0], DIAL[1], 220, (0.6, 0.38, 0.18), 1.6)
    cv.light((x0 + x1) / 2, 140, 300, (0.24, 0.30, 0.45), 1.3)
    wall = cv.full()
    cv.put(wall, '#563532', 0.6 + n1 * 0.08)
    # damask: a stylised lily in a diamond lattice, darker than the ground
    u = np.mod(xx + np.floor(yy / 24) * 12, 24) - 12
    v = np.mod(yy, 24) - 12
    lat = (np.abs(u) + np.abs(v) * 0.9) < 9.5
    lily = (np.hypot(u * 1.4, v + 2) < 4.5) | ((np.abs(u) < 1.0) & (np.abs(v) < 8)) | (np.hypot(np.abs(u) - 4, v - 3) < 2.2)
    dm = lat & lily & (yy < 212)
    cv.put(dm, '#432826', 0.62 + n1[dm] * 0.08)
    cv.put((lat & ~C.shift(lat, 1, 0) & (yy < 212)), '#6E443C', 0.5)
    rail = (yy >= 58) & (yy < 61)
    cv.put(rail, '#3D271A', 0.95)
    cv.put((yy >= 58) & (yy < 59), '#8A6040', 0.9)
    wain = yy >= 214
    cv.put(wain, '#43291B', 0.9 + n1[wain] * 0.1)
    for px0 in range(8, 640, 92):
        pan = cv.box(px0, 222, px0 + 80, 330)
        cv.put(pan & ~C.shift(pan, 0, -1), '#5A3824', 1.0)
        cv.put(pan & ~C.shift(pan, 0, 1), '#231710', 1.0)
    cv.put((yy >= 212) & (yy < 216), '#5A3824', 1.0)
    # a wall sconce (off: brass arm, pleated cream shade) between the stand and the window
    cv.put(cv.seg([(118, 104), (124, 98), (124, 92)], 1.0), '#9C7630', 1.0)
    cv.put(cv.box(115, 100, 121, 108), '#73531F', 1.0)
    shade = cv.poly([(117, 80), (131, 80), (135, 92), (113, 92)])
    cv.put(shade, '#B3A98D', 0.8)
    cv.put(shade & (np.mod(xx, 3) == 0), '#8E856C', 0.8)
    # window: reveal, the view, frame (dark oak casement, brass espagnolette), sill
    reveal = (xx >= x0 - 10) & (xx < x1 + 10) & (yy >= y0 - 8) & (yy < y1 + 6)
    cv.put(reveal, '#6E443C', 0.6 + n1[reveal] * 0.08)
    inside = _view(cv, 'nord', (420, 124))
    # the net curtain (lace) over the lower panes: a fine dither veil with a scalloped edge
    net = inside & (yy >= 150) & (np.mod(xx + yy, 3) == 0)
    cv.mix(net, '#C2B8A0', 0.4)
    scal = inside & (np.abs(yy - (150 - np.abs(np.sin((xx - x0) / 8.0 * np.pi)) * 3)) < 0.8)
    cv.mix(scal, '#C2B8A0', 0.5)
    _frost(cv, inside, 622)
    # the lamp's reflection in the glass (a warm smudge beside the lamp)
    refl = inside & cv.ell(238, 118, 6, 8)
    cv.add(refl & (np.mod(xx + yy, 2) == 0), '#2A1A0C', 1.0)
    cv.add(inside & cv.box(232, 114, 245, 116), '#3A2410', 1.0)
    frame = inside & ((np.abs(xx - MUL) < 3) | (xx < x0 + 4) | (xx >= x1 - 4) | (yy < y0 + 4) |
                      (np.abs(yy - 92) < 2) | (yy >= y1 - 5))
    cv.put(frame, '#43291B', 0.95)
    cv.put(frame & (np.abs(xx - MUL) < 1), '#2B1B12', 1.0)
    cv.put(cv.box(MUL - 2, 120, MUL + 2, 176), '#C49A48', 0.9)                            # espagnolette
    cv.put(cv.box(MUL - 5, 144, MUL + 5, 150), '#E8C779', 0.9)
    cv.put(inside & (yy >= y1 - 6) & (yy < y1 - 4), '#A1AAB7', 0.9, lit=False)
    cv.put(cv.box(x0 - 14, y1 + 2, x1 + 14, y1 + 8), '#553826', 1.0)
    # velvet curtains: deep folds, a tasselled tie-back each side, the pelmet on top
    pel = cv.box(x0 - 40, y0 - 22, x1 + 40, y0 - 8)
    cv.put(pel, '#4A221C', 0.95)
    cv.put(pel & (yy >= y0 - 11), '#622E22', 0.9)
    cv.put(pel & (np.mod(xx, 14) < 1), '#22100F', 1.0)
    for side in (-1, 1):
        cxa = x0 - 38 if side < 0 else x1 - 22
        cur = (xx >= cxa) & (xx < cxa + 60) & (yy >= y0 - 8) & (yy < 300)
        waist = 168.0
        pinch = np.clip(1 - np.abs(yy - waist) / 46.0, 0, 1) * 20
        cur &= (xx < x0 + 22 - pinch) if side < 0 else (xx >= x1 - 22 + pinch)
        fold = np.sin((xx - cxa) * 0.55 + np.clip(yy - waist, 0, 99) * 0.02) * 0.32
        cv.put(cur, '#622E22', 0.62 + fold)
        cv.put(cur & (fold > 0.22), '#7A3A2A', 0.7)
        tie = cur & (np.abs(yy - waist - np.sin((xx - cxa) * 0.4) * 1.2) < 1.2)
        cv.put(tie, '#C49A48', 0.9)
        tx = (x0 + 6) if side < 0 else (x1 - 6)
        cv.put(cv.seg([(tx, waist + 2), (tx, waist + 16)], 1.4, 2.6), '#9C7630', 0.9)
    # the desk: leather inlay, blotter, the notepad (the pencil hand writes at runtime), inkstand, folder
    top = (yy >= TY - 12) & (yy < TY) & (xx >= 112) & (xx < 568)
    cv.put(top, '#553826', 0.9 + (yy - (TY - 12)) / 30.0)
    inlay = top & (xx >= 150) & (xx < 530) & (yy >= TY - 10) & (yy < TY - 2)
    cv.put(inlay, '#22442F', 0.95 + n2[inlay] * 0.08)
    cv.put(inlay & (LF.edge_top(inlay) | LF.edge_dir(inlay, 0, 1)), '#9C7630', 0.8)
    cv.put(top & (yy == TY - 12), '#8A6040', 1.0)
    edge = (yy >= TY) & (yy < TY + 6) & (xx >= 112) & (xx < 568)
    cv.put(edge, '#43291B', 1.0)
    under = (yy >= TY + 6) & (xx >= 112) & (xx < 568)
    cv.put(under, '#311F15', 0.85)
    for dx0 in (130, 440):
        dr = cv.box(dx0, TY + 12, dx0 + 96, TY + 30)
        cv.put(dr, '#43291B', 0.9)
        cv.put(LF.edge_top(dr), '#5A3824', 1.0)
        cv.put(cv.box(dx0 + 44, TY + 19, dx0 + 52, TY + 22), '#C49A48', 1.0)
    blot = cv.poly([(380, TY - 10), (560, TY - 10), (562, TY - 2), (378, TY - 2)])
    cv.put(blot, '#3D271A', 0.9)
    pad = cv.poly([(424, TY - 9), (500, TY - 9), (506, TY - 2), (418, TY - 2)])
    cv.put(pad, '#E0D6BC', 0.85)
    for ly in (TY - 7, TY - 5, TY - 3):
        cv.put(pad & (yy == ly) & (np.mod(xx, 7) < 5) & (xx < 470), '#6B6350', 0.9)
    folder = cv.poly([(222, TY - 9), (268, TY - 10), (270, TY - 3), (220, TY - 2)])
    cv.put(folder, '#8E856C', 0.8)
    cv.put(folder & (np.abs(xx - 245) < 1), '#7A2218', 0.9)
    cv.put(folder & (yy < TY - 8), '#B3A98D', 0.9)
    ink = cv.box(512, TY - 18, 526, TY - 9)
    cv.put(ink, '#14161A', 1.0)
    cv.put(LF.edge_top(ink), '#C49A48', 1.0)
    cv.put(cv.seg([(519, TY - 18), (526, TY - 34)], 0.7), '#2B2E33', 1.0)
    # the coffee cup on its saucer (steam at runtime) and the hat at the left end
    cupx = 258
    cv.put(cv.ell(cupx, TY - 3, 11, 3), '#E0D6BC', 0.85)
    cup = cv.box(cupx - 6, TY - 15, cupx + 6, TY - 4) | cv.ell(cupx, TY - 4, 6, 2)
    cv.put(cup, '#E0D6BC', 0.9)
    cv.put(cv.ell(cupx, TY - 15, 6, 1.6), '#2A170E', 1.0)
    cv.put((np.abs(np.hypot(xx + 0.5 - (cupx + 8), yy + 0.5 - (TY - 10)) - 3) < 1.0) & (xx > cupx + 6), '#E0D6BC', 0.85)
    L['steam_cup'] = [cupx - 9, TY - 15 - 32]
    crown = cv.poly([(158, TY - 12), (162, TY - 24), (176, TY - 27), (190, TY - 24), (194, TY - 12)])
    brim = cv.ell(176, TY - 8, 28, 5)
    cv.put(brim, '#2D2D36', 0.95)
    cv.put(crown, '#3D3639', 0.9)
    cv.put(crown & (yy >= TY - 15) & (yy < TY - 12), '#14161A', 1.0)                       # ribbon
    cv.put(LF.edge_top(crown) & (np.abs(xx - 176) < 6), '#2D2D36', 0.8)                     # the pinch
    # lamp: brass foot, stem, cream shade (its light pool is the runtime glow)
    cv.put(cv.ell(206, TY - 4, 12, 3), '#C49A48', 0.95)
    cv.put(cv.box(204, 150, 208, TY - 4), '#9C7630', 0.95)
    sh = cv.poly([(186, 132), (226, 132), (236, 156), (176, 156)])
    cv.emit(sh, '#E8D8B0', 0.95)
    cv.emit(sh & (yy >= 152), '#FCE2B0', 1.0)
    cv.put(sh & (yy < 135), '#B3A98D', 0.9)
    # his coat and scarf on the stand at the far left
    cv.put(cv.box(46, 66, 50, 314), '#43291B', 1.0)
    cv.put(cv.seg([(36, 72), (60, 72)], 1.2) | cv.seg([(48, 66), (48, 60)], 1.6), '#43291B', 1.0)
    coat = cv.poly([(30, 92), (40, 84), (56, 84), (66, 92), (74, 140), (80, 268), (20, 270), (24, 140)])
    cv.put(coat, '#1D2442', 0.95)
    cv.put(coat & (xx > 58), '#2C3B5E', 0.9)
    lap = cv.poly([(40, 88), (48, 120), (56, 88)])
    cv.put(lap, '#131A2C', 1.0)
    cv.put(coat & (np.abs(xx - 48) < 0.6) & (yy > 120), '#0B0F1C', 1.0)
    for by in (140, 172, 204):
        cv.put(cv.ell(52, by, 1.4, 1.4), '#3A4A6A', 1.0)
    sc = cv.poly([(38, 90), (58, 88), (55, 176), (44, 178)])
    cv.put(sc, '#B3A98D', 0.82)
    cv.put(sc & (np.mod(yy, 5) < 1), '#8E856C', 0.8)
    cv.put(cv.box(42, 172, 58, 180) & (np.mod(xx, 2) == 0), '#B3A98D', 0.82)              # fringe
    return cv


def room(kind):
    cv = LF.Cv(VW, VH, 0, 0, amb=(0.16, 0.17, 0.22))
    if kind == 'alexei':
        _alexei(cv)
        pal = PAL_A
    else:
        _konrad(cv)
        pal = PAL_K
    out = cv.quant(pal, spread=10.0)
    out[..., 3] = 255
    L['lit_view_' + kind] = [int(v) for v in ((420, 124) if kind == 'alexei' else (230, 112))]
    return out


# ================================================================================================ chairs
def chair(kind):
    """The chair back in front of the man (over the figure): Alexei a bentwood chair (the hoop and the bow of
    the back), Konrad an upholstered desk chair (buttoned leather back in a carved frame).  Returns the sprite
    and records its top-left in layout.json (chair_alexei / chair_konrad)."""
    if kind == 'alexei':
        x0, y0, w, h = 112, 250, 120, 70
        cv = LF.Cv(w, h, x0, y0, amb=(0.22, 0.22, 0.28))
        cv.light(DIAL[0], DIAL[1], 300, (1.1, 0.72, 0.38), 1.5)
        cx = 172.0
        hoop = cv.ring(cx, 300, 46, 52, sy=0.92) & (cv.yy < 300)
        bow = cv.ring(cx, 312, 30, 35, sy=1.1) & (cv.yy < 312)
        legs = cv.seg([(cx - 49, 300), (cx - 47, 320)], 2.6) | cv.seg([(cx + 49, 300), (cx + 47, 320)], 2.6)
        wood = hoop | bow | legs
        lit = C.edge_light(wood, (0.8, -0.6), width=3.0, soft=1)
        cv.put(wood, '#3D271A', 0.75 + lit * 0.9)
        cv.put(wood & ~C.shift(wood, 0, 1), '#1C120C', 0.8)
        pal = PAL_A
    else:
        x0, y0, w, h = 484, 240, 140, 80
        cv = LF.Cv(w, h, x0, y0, amb=(0.2, 0.18, 0.2))
        cv.light(206, 150, 520, (1.2, 0.85, 0.48), 1.3)
        cx = 552.0
        frame = cv.poly([(cx - 58, 320), (cx - 60, 268), (cx - 50, 252), (cx - 20, 246), (cx + 20, 246),
                         (cx + 50, 252), (cx + 60, 268), (cx + 58, 320)])
        back = cv.poly([(cx - 50, 320), (cx - 52, 270), (cx - 44, 258), (cx - 18, 253), (cx + 18, 253),
                        (cx + 44, 258), (cx + 52, 270), (cx + 50, 320)])
        cv.put(frame, '#43291B', 0.9 + C.edge_light(frame, (-0.8, -0.6), width=3.0, soft=1) * 0.9)
        cv.put(LF.edge_top(frame), '#8A6040', 0.9)
        shade = 0.7 + np.clip((cx - cv.xx) / 120.0, -0.25, 0.35) + np.clip((290 - cv.yy) / 80.0, 0, 0.3)
        cv.put(back, '#4A221C', shade)
        for by in (270, 292):
            for bx in np.arange(cx - 36, cx + 37, 18):
                b = cv.ell(bx + (9 if by == 292 else 0), by, 1.6, 1.6) & back
                cv.put(b, '#22100F', 1.0)
                cv.put(cv.seg([(bx + (9 if by == 292 else 0) - 7, by - 6), (bx + (9 if by == 292 else 0), by)], 0.5) & back,
                       '#341815', 1.0)
        pal = PAL_K
    out = cv.quant(pal, spread=8.0)
    L['chair_' + kind] = [x0, y0]
    return out
