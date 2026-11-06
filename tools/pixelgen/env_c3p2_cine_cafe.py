"""env_c3p2_cine_cafe -- LS_C3_Radio r4 (the doors, the note) and r5 (Café „Korridor"), round 10 (owner: c3p2
places stream).

  doors        split screen at floor level, inside the two rooms: left room 214 (Hotel Nord: plaster, an oxblood
               door with a simple lever, the chain, the framed house rules, linoleum with a rag rug), right room
               317 (Hotel Europa: damask and wainscot, the cream panelled door with mouldings and the brass kick
               plate, a brass lever, carpet with a border); the corridor light in both gaps rakes over the floor
  keyfob       the key left in each lock with its fob („214" / „317"), 3 frames (still, swung left / right): it
               swings when the note pushes under the door (runtime)
  note_fold    the folded note (46 x 14) that slides in under the door (runtime)
  note_close   the note unfolded on the boards in the gap light: two folds, pencil block letters, Russian above
               German (the words of data/locale/de_c3p2_cinematics.json), the door's foot and its bright gap above
  cafe         the café after closing (648 x 360 at (-4, 0)): the front window with the reversed gold lettering,
               the station across the square with its lit clock (hands at runtime), the name on its roof, a lamp
               post, the tram stop, snow; marble tables with the bentwood chairs upside down, pendant lamps off,
               the bar with the espresso machine, glasses and a night light, newspaper holders, a coat stand
               with a forgotten umbrella, the closed sign on the door, tiles that mirror the window
  cafe_fg      Elena's table in front (her chair pulled out, the untouched glass of tea with lemon on its saucer)
  cat          the café's cat asleep on the bar (2 frames: breathing / the tail tip)
"""
from __future__ import annotations

import math

import numpy as np

import env_c3p2_cine_kit as Q
from env_c3p2_cine_kit import (C, K, VW, VH, NIGHT, SNOW, LAMP, OAK, PAPER, BRASS, RED)
import env_c3p2_cine_life as LF
import env_c3p2_cine_radio as RD

L = Q.LAYOUT.setdefault('radio', {})
DOOR_FLOOR = RD.DOOR_FLOOR
CLOCK = RD.CLOCK
CLOCK_R = RD.CLOCK_R

PAL_D = LF.palette(NIGHT, SNOW, LAMP, OAK, PAPER, BRASS,
                   ['#0F0807', '#1A0E0B', '#29150F', '#3A1D14', '#4E271A', '#663322', '#14141A', '#25252C',
                    '#3A3A42', '#55545A', '#727076', '#918E90', '#B4B0A8', '#0A0806', '#141009', '#21190F',
                    '#2E2416', '#3E311E', '#120709', '#1E0C0F', '#2C1216', '#3E1A1D', '#552426', '#6E3030',
                    '#0A0E0E', '#111818', '#192222', '#222E2D', '#2D3A39', '#100A0A', '#261616', '#432826',
                    '#1E2A24', '#3A4C3E'])
PAL_C = LF.palette(NIGHT, SNOW, LAMP, OAK, PAPER, BRASS, RED,
                   ['#0B0D10', '#14171B', '#1F2328', '#2C3137', '#3C424A', '#555C64', '#727A82', '#8E969E',
                    '#1A1A1C', '#3A3A3C', '#7C7A76', '#C8C4BA', '#EEEAE0', '#1C2A26', '#2A3E36', '#3E5A4C',
                    '#3A2C20', '#5A4430', '#2A3646', '#36475A', '#9AB0C8', '#B8C4D0'])


# ================================================================================================ r4 doors
def doors():
    """Split screen: left Alexei's door (room 214), right Konrad's (room 317), seen from the floor."""
    cv = LF.Cv(VW, VH, 0, 0, amb=(0.25, 0.25, 0.3))
    xx, yy = cv.xx, cv.yy
    n1 = cv.nz(12, 801)
    n2 = cv.nz(3, 803)
    left = xx < 319
    right = xx >= 321
    for side, m in ((0, left), (1, right)):
        cx = 160 if side == 0 else 480
        dx0, dx1 = cx - 96, cx + 96
        # the corridor light in the gap rakes over the floor and catches the door's foot
        g = cv.light(cx, DOOR_FLOOR + 2, 220, (1.5, 1.05, 0.55), 1.6, sy=0.42, mask=m & (yy >= DOOR_FLOOR))
        cv.light(cx, DOOR_FLOOR - 2, 130, (0.34, 0.24, 0.13), 1.4, sy=0.3, mask=m & (yy < DOOR_FLOOR))
        cv.light(cx, 150, 260, (0.10, 0.11, 0.14), 1.2, mask=m)
        wall = m & (yy < DOOR_FLOOR)
        if side == 0:
            cv.put(wall, '#2D3A39', 0.7 + n1[wall] * 0.15)
            cv.put(wall & (yy >= 200), '#1E2A24', 0.85)
            cv.put(wall & (yy >= 198) & (yy < 200), '#3A4C3E', 0.9)
        else:
            u = np.mod(xx + np.floor(yy / 24) * 12, 24) - 12
            v = np.mod(yy, 24) - 12
            lat = (np.abs(u) + np.abs(v) * 0.9) < 9.5
            cv.put(wall, '#432826', 0.7 + n1[wall] * 0.1)
            cv.put(wall & lat & (np.hypot(u * 1.4, v + 2) < 4.5), '#261616', 0.8)
            cv.put(wall & (yy >= 204), '#3E311E', 0.9)
            cv.put(wall & (yy >= 202) & (yy < 205), '#663322', 0.8)
        # architrave
        arch = m & (((xx >= dx0 - 12) & (xx < dx0)) | ((xx >= dx1) & (xx < dx1 + 12))) & (yy < DOOR_FLOOR)
        cv.put(arch, '#B4B0A8' if side == 1 else '#3A1D14', 0.85)
        cv.put(arch & ((xx == dx0 - 12) | (xx == dx1 + 11)), '#14141A', 1.0)
        door = m & (xx >= dx0) & (xx < dx1) & (yy < DOOR_FLOOR - 4)
        if side == 0:
            brush = (np.mod(yy * 0.9 + n2 * 4, 3.0) < 0.6)
            cv.put(door, '#663322', 0.82 + n1[door] * 0.18)
            cv.put(door & brush, '#3A1D14', 0.85)
            scuff = door & (yy > DOOR_FLOOR - 20) & (LF.nz(cv.w, cv.h, 4, 805, 2) > 0.7)
            cv.put(scuff, '#3A1D14', 0.7)
            # simple lever, escutcheon, the chain on its slide, the framed house rules
            cv.put(cv.box(cx + 62, 132, cx + 76, 160), '#727076', 0.75)
            cv.put(cv.seg([(cx + 69, 138), (cx + 46, 140)], 2.2), '#918E90', 0.8)
            cv.put(cv.ell(cx + 69, 152, 2, 3), '#0A0806', 1.0)
            cv.put(cv.box(cx + 80, 96, cx + 92, 101), '#727076', 0.8)
            chain = np.zeros_like(door)
            for i in range(9):
                t_ = i / 8.0
                px_ = cx + 86 - t_ * 28
                py_ = 99 + math.sin(t_ * math.pi) * 14
                chain |= cv.ell(px_, py_, 1.3, 1.0)
            cv.put(chain, '#918E90', 0.85)
            card = cv.box(cx - 34, 70, cx + 2, 112)
            cv.put(card, '#3A3A42', 0.9)
            cv.put(cv.box(cx - 32, 72, cx, 110), '#B4B0A8', 0.7)
            for ly in range(76, 108, 4):
                cv.put(cv.box(cx - 29, ly, cx - 3 - (ly % 7) * 2, ly + 1), '#3A3A42', 0.9)
            L['key_214'] = [cx + 69, 154]
        else:
            cv.put(door, '#918E90', 0.85 + n1[door] * 0.1)
            for (px0, px1, py0, py1) in ((dx0 + 18, cx - 8, 54, 150), (cx + 8, dx1 - 18, 54, 150),
                                         (dx0 + 18, cx - 8, 164, 222), (cx + 8, dx1 - 18, 164, 222)):
                pan = cv.box(px0, py0, px1, py1)
                cv.put(pan & door, '#B4B0A8', 0.72)
                cv.put(door & (LF.edge_top(pan) | LF.edge_dir(pan, -1, 0)), '#3A3A42', 0.9)
                cv.put(door & (LF.edge_dir(pan, 0, 1) | LF.edge_dir(pan, 1, 0)), '#B4B0A8', 0.9)
                inner = cv.box(px0 + 5, py0 + 5, px1 - 5, py1 - 5)
                cv.put(door & (LF.edge_top(inner) | LF.edge_dir(inner, -1, 0)), '#B4B0A8', 0.8)
            kick = door & (yy >= DOOR_FLOOR - 30)
            cv.put(kick, '#9C7630', 0.9 + np.clip((yy - (DOOR_FLOOR - 30)) / 30.0, 0, 1) * 0.6)
            cv.put(kick & (yy == DOOR_FLOOR - 30), '#E8C779', 0.9)
            cv.put(kick & (np.mod(xx - dx0, 32) < 1), '#73531F', 0.9)
            cv.put(cv.box(cx + 60, 128, cx + 78, 166), '#9C7630', 0.9)
            cv.put(cv.box(cx + 62, 130, cx + 76, 164) & ~cv.box(cx + 64, 132, cx + 74, 162), '#E8C779', 0.8)
            cv.put(cv.seg([(cx + 69, 140), (cx + 44, 142), (cx + 40, 146)], 2.4), '#C49A48', 0.95)
            cv.put(cv.ell(cx + 69, 154, 2, 3), '#0A0806', 1.0)
            card = cv.box(cx - 30, 168, cx + 30, 182)
            cv.put(card, '#9C7630', 0.9)
            cv.put(cv.box(cx - 28, 170, cx + 28, 180), '#B4B0A8', 0.7)
            tm = K.vtext('HAUSORDNUNG', 's', 1)
            cv.put(K.place(tm, cv.w, cv.h, cx - tm.shape[1] // 2, 170) & card, '#3A3A42', 0.9)
            L['key_317'] = [cx + 69, 154]
        # threshold gap: the corridor light (bright), the door's lower edge catching it
        gap = m & (yy >= DOOR_FLOOR - 4) & (yy < DOOR_FLOOR) & (xx >= dx0) & (xx < dx1)
        cv.emit(gap, '#FCE2B0', 1.0 - (DOOR_FLOOR - 1 - yy[gap]) * 0.06)
        cv.put(m & (yy >= DOOR_FLOOR - 4) & (yy < DOOR_FLOOR) & ~((xx >= dx0) & (xx < dx1)), '#0A0806', 1.0)
        cv.add(door & (yy >= DOOR_FLOOR - 7), '#3A2410', 0.8)
        # floor in perspective
        fl = m & (yy >= DOOR_FLOOR)
        u = (yy - DOOR_FLOOR) / (VH - DOOR_FLOOR)
        if side == 0:
            cv.put(fl, '#2E2416', 0.85 + n1[fl] * 0.2)
            seams = fl & (np.mod((xx - cx) / (0.6 + u * 3.0), 30) < 0.8)
            cv.put(seams, '#141009', 0.9)
            worn = fl & (np.abs(xx - cx) < 50 + u * 60) & (LF.nz(cv.w, cv.h, 6, 807, 2) > 0.55)
            cv.put(worn, '#3E311E', 0.9)
            rug = fl & (yy >= DOOR_FLOOR + 10) & (yy < DOOR_FLOOR + 30) & (np.abs(xx - cx) < 70 + u * 70)
            stripe = np.mod(np.floor((yy - DOOR_FLOOR) / 3.0), 4)
            cols = ('#552426', '#3A4C3E', '#B4B0A8', '#3E311E')
            for i_, cc in enumerate(cols):
                cv.put(rug & (stripe == i_), cc, 0.75)
            cv.put(rug & (np.mod(xx, 2) == 0) & (LF.edge_top(rug) | LF.edge_dir(rug, 0, 1)), '#B4B0A8', 0.6)
        else:
            cv.put(fl, '#3E1A1D', 0.85 + n2[fl] * 0.1)
            fu = (xx - cx) / (1.0 + u * 2.6)
            fv = (yy - DOOR_FLOOR) / (0.35 + u * 0.9)
            dia = (np.abs(np.mod(fu, 28) - 14) + np.abs(np.mod(fv, 28) - 14)) < 6
            cv.put(fl & dia, '#552426', 0.9)
            cv.put(fl & dia & ((np.abs(np.mod(fu, 28) - 14) + np.abs(np.mod(fv, 28) - 14)) < 2.5), '#9C7630', 0.6)
            border = fl & (np.abs(np.abs(xx - cx) - (110 + u * 160)) < 4 + u * 4)
            cv.put(border, '#2C1216', 1.0)
            cv.put(border & (np.mod(xx + yy, 4) < 2), '#9C7630', 0.7)
    cv.put((xx >= 319) & (xx < 321), '#05070C', 1.0, lit=False)
    out = cv.quant(PAL_D, spread=10.0)
    out[..., 3] = 255
    L['door_floor'] = DOOR_FLOOR
    L['door_cx'] = [160, 480]
    return out


def keyfob():
    """The key in the lock with its fob: 2 rows (214 / 317) x 3 frames (still, swung left, swung right),
    each 18 x 30, the key's bow at the top centre (anchor = layout key_214 / key_317)."""
    fw, fh = 18, 30
    rows = []
    for num, wood in (('214', '#3A1D14'), ('317', '#9C7630')):
        frames = []
        for fr, ang in enumerate((0.0, -0.32, 0.32)):
            cv = LF.Cv(fw, fh, 0, 0, amb=(0.75, 0.62, 0.45))
            ax, ay = 9.0, 2.0
            bow = cv.ring(ax, ay + 1.5, 1.2, 2.6)
            cv.put(bow, '#C49A48', 1.0)
            ex, ey = ax + math.sin(ang) * 9, ay + 3 + math.cos(ang) * 9
            ring = cv.ring(ex, ey, 1.4, 2.4)
            cv.put(ring, '#9C7630', 1.0)
            cv.put(cv.seg([(ax, ay + 3), (ex, ey - 2)], 0.6), '#9C7630', 1.0)
            fx, fy = ax + math.sin(ang) * 18, ay + 3 + math.cos(ang) * 18
            fob = cv.ell(fx, fy, 5.0, 7.5)
            cv.put(fob, wood, 1.0)
            cv.put(LF.edge_dir(fob, -1, -1), '#E8C779' if num == '317' else '#663322', 1.0)
            tm = K.vtext(num, 's', 1)
            cv.put(K.place(tm, fw, fh, int(fx - tm.shape[1] / 2), int(fy - 4)) & fob, '#14141A', 1.0)
            frames.append(cv.quant(PAL_D, spread=4.0))
        rows.append(np.concatenate(frames, axis=1))
    return np.concatenate(rows, axis=0)


def note_fold():
    """The folded note on the floor (seen flat from low: 46 x 14) - emerges from under the door: a sheet folded once,
    the upper flap a little lifted along the crease (lit edge, its shadow on the lower half), a few pencil strokes
    showing through, the corner dog-eared."""
    w, h = 46, 14
    cv = LF.Cv(w, h, 0, 0, amb=(1.0, 0.92, 0.78))
    xx, yy = cv.xx, cv.yy
    sh = cv.poly([(3, 0), (43, 0), (46, 13), (0, 13)])
    lower = sh & (yy >= 7)
    upper = sh & (yy < 7)
    cv.put(lower, '#B3A98D', 0.92 + (yy / h) * 0.1)
    cv.put(upper, '#D8CFB2', 0.95 + (yy / h) * 0.08)
    cv.put(upper & (yy == 0), '#EFE8D2', 1.0)
    cv.put(sh & (yy == 7), '#6B6350', 1.0)                      # the crease's shadow under the lifted flap
    cv.put(sh & (yy == 6), '#F2E8D2', 1.0)                      # the crease catching the light
    # a few pencil strokes showing through the paper (irregular, like handwriting seen from the back)
    for (x0, x1, y_) in ((9, 15, 3), (17, 21, 3), (23, 31, 3), (10, 18, 10), (20, 24, 10), (27, 35, 10)):
        stroke = sh & (yy == y_) & (xx >= x0) & (xx < x1) & (LF.hsh(xx, y_, 731) > 0.25)
        cv.put(stroke, '#8E856C', 1.0)
    # the dog-eared corner at the right
    cv.put(cv.poly([(39, 0), (43, 0), (44, 5)]), '#EFE8D2', 1.0)
    cv.put(cv.poly([(39, 0), (44, 5), (41, 5)]) & sh, '#8E856C', 1.0)
    cv.put(sh & (xx >= 0) & (yy == 13), '#6B6350', 1.0)
    return cv.quant(PAPER + ['#F2E8D2'], spread=4.0)


def note_close():
    """Close-up: the note unfolded on the boards, the door's foot and its gap at the top, the light raking
    across; two folds, pencil block letters, Russian above German."""
    cv = LF.Cv(VW, VH, 0, 0, amb=(0.30, 0.28, 0.27))
    xx, yy = cv.xx, cv.yy
    nz_ = cv.nz(22, 707)
    gap_y = 56
    # the light fans out from the gap at the top toward the camera
    spread = np.clip(1 - np.abs(xx - 320) / (240 + (yy - gap_y) * 1.3), 0, 1)
    rake = np.clip(1 - (yy - gap_y) / 330.0, 0, 1) ** 1.2 * spread
    cv.light_field(rake, (1.05, 0.9, 0.66))
    boards = yy >= gap_y + 4
    plank = np.floor((xx - 320) / (30 + (yy - gap_y) * 0.22))
    cv.put(boards, '#3E311E', 0.75 + nz_[boards] * 0.3 + LF.hsh(plank, 3.0)[boards] * 0.2)
    seam = boards & (np.mod((xx - 320) / (30 + (yy - gap_y) * 0.22), 1.0) < 0.04)
    cv.put(seam, '#0A0806', 1.0)
    grain = boards & (np.mod(yy * 0.35 + LF.nz(cv.w, cv.h, 8, 709, 2) * 5 + plank * 1.7, 2.0) < 0.25)
    cv.put(grain, '#2E2416', 0.9)
    # the door's foot and the bright gap
    door = yy < gap_y - 2
    cv.put(door, '#3A1D14', 0.5)
    cv.emit((yy >= gap_y - 2) & (yy < gap_y + 3), '#FCE2B0', 1.0)
    cv.add((yy >= gap_y - 8) & (yy < gap_y - 2), '#3A2410', 0.8)
    # the paper: soft shadow, the sheet, two folds (a cross), the light across it
    pts = [(132, 84), (504, 74), (516, 270), (122, 282)]
    shadow = cv.poly([(p[0] + 5, p[1] + 6) for p in pts])
    cv.mix(shadow & boards, '#0A0806', 0.6)
    paper = cv.poly(pts)
    pn = LF.nz(cv.w, cv.h, 5, 711, 3)
    cv.put(paper, '#D8CFB2', 0.72 + nz_[paper] * 0.12 + pn[paper] * 0.08)
    hcrease = paper & (np.abs(yy - (178 - (xx - 132) * 0.025)) < 1.0)
    cv.put(hcrease, '#8E856C', 0.8)
    cv.put(paper & (yy > 178 - (xx - 132) * 0.025) & (yy < 184 - (xx - 132) * 0.025), '#B3A98D', 0.8)
    vx = lambda y: 318 + (y - 84) * -0.026
    vcrease = paper & (np.abs(xx - vx(yy)) < 0.9)
    cv.put(vcrease, '#8E856C', 0.85)
    cv.put(paper & (xx > vx(yy)) & (xx < vx(yy) + 5), '#B3A98D', 0.82)
    cv.put(paper & ~C.shift(paper, 0, 2), '#6B6350', 0.8)
    cv.put(paper & (LF.nz(cv.w, cv.h, 2, 713, 2) > 0.8), '#B3A98D', 0.8)
    lines = [(Q.locale('cin.c3p2.radio.note_ru'), 0), (Q.locale('cin.c3p2.radio.note'), 1)]
    ty = 102
    for txt, k in lines:
        parts = RD._split_note(txt)
        for j, ln in enumerate(parts):
            tm = Q.hand_text(ln.upper(), scale=2, slant=0.18, seed=17 + k * 5 + j)
            x = 156 + (6 if j else 0)
            sm = K.place(tm, VW, VH, x, ty) & paper
            cv.put(sm, '#36363C', 0.95)
            smudge = C.shift(sm, -1, 0) & paper & ~sm & (LF.nz(cv.w, cv.h, 3, 715 + j, 2) > 0.55)
            cv.put(smudge, '#8E856C', 0.85)
            ty += 22
        ty += 14
    pal = LF.palette(PAPER, LAMP, ['#07060A', '#0E0B0D', '#171214', '#211A18', '#2C221C', '#3A2D22', '#141418',
                                   '#24242A', '#36363C', '#4A4A50', '#3A1D14', '#4E271A', '#2E2416', '#3E311E',
                                   '#0A0806', '#F2E8D2', '#5A4430'])
    out = cv.quant(pal, spread=8.0)
    out[..., 3] = 255
    return out


# ================================================================================================ r5 the café
CMX = 4                               # margin of the café bg (the runtime drifts the camera)


def _station_outside(cv, win):
    """Through the window: the station across the square (arches, the roof edge with its name, the big lit
    clock), a lamp post, the tram stop sign, snow on the ground and the sills."""
    xx, yy = cv.xx, cv.yy
    n1 = cv.nz(9, 813)
    sky = win & (yy < 74)
    cv.put(sky, '#1A2431', 0.6 + n1[sky] * 0.3, lit=False)
    stn = win & (yy >= 74) & (yy < 196) & (xx >= 340) & (xx < 580)
    cv.put(win & (yy >= 74) & (yy < 196), '#2A3646', 0.55 + n1[win & (yy >= 74) & (yy < 196)] * 0.15, lit=False)
    cv.put(stn, '#3A4859', 0.7 + n1[stn] * 0.15, lit=False)
    for ax in range(352, 572, 30):
        arc = stn & (np.abs(xx - ax - 11) < 9) & (yy > 148) & ((yy > 157) | (np.hypot(xx - ax - 11, yy - 157) < 9))
        cv.emit(arc & (LF.hsh(ax, 2.0, 1.0) < 0.5), '#5A3A1C', 0.9)
        cv.put(arc & (LF.hsh(ax, 2.0, 1.0) >= 0.5), '#0A0E16', 1.0, lit=False)
    cv.put(stn & (yy >= 74) & (yy < 78), '#A1AAB7', 0.9, lit=False)
    tm = K.vtext('VELTRAVA', 'l', 2)
    sm = K.place(tm, cv.w, cv.h, 456 - tm.shape[1] // 2 - cv.ox, 80 - cv.oy) & stn
    cv.emit(sm, '#D09A58', 0.9)
    clock = cv.ell(CLOCK[0], CLOCK[1], CLOCK_R + 3, CLOCK_R + 3) & win
    cv.put(clock, '#2A1D0B', 1.0, lit=False)
    face = cv.ell(CLOCK[0], CLOCK[1], CLOCK_R, CLOCK_R) & win
    cv.emit(face, '#EEEAE0', 0.95 - np.hypot(xx - CLOCK[0], yy - CLOCK[1])[face] / CLOCK_R * 0.15)
    hours, mins = K.clock_indices(yy, xx, CLOCK[0], CLOCK[1], CLOCK_R - 1.5, 5.0, 2.5)
    cv.emit(hours & face, '#1A1A1C')
    cv.emit(mins & face, '#7C7A76')
    ground = win & (yy >= 196)
    cv.put(ground, '#4F5E70', 0.8 + n1[ground] * 0.25 + (yy[ground] - 196) / 40.0, lit=False)
    for rx in (250, 262):
        cv.put(win & (yy >= 196) & (np.abs(xx - rx - (yy - 196) * 0.6) < 0.6), '#1A2431', 1.0, lit=False)
    # lamp post with its globe, the tram-stop sign on its pole
    cv.put(win & (np.abs(xx - 300) < 1.2) & (yy >= 116) & (yy < 200), '#0A0E16', 1.0, lit=False)
    cv.emit(win & cv.ell(300, 112, 4, 5), '#FCE2B0')
    cv.add(win & cv.ell(300, 200, 30, 6), '#3A2410', 0.9)
    cv.put(win & (np.abs(xx - 120) < 0.8) & (yy >= 140) & (yy < 200), '#0A0E16', 1.0, lit=False)
    sign = win & cv.box(112, 132, 128, 144)
    cv.emit(sign, '#C8C4BA', 0.7)
    cv.emit(sign & cv.box(115, 135, 125, 141), '#7A2218', 0.8)


def _chair_up(cv, cx, ty, s, k=1.0, side=1):
    """A bentwood chair upside down on a table top: the round seat lying on the marble (its rim and thickness),
    four turned legs splaying up -- the two front legs light-edged, the two back ones darker behind them -- the
    leg ring a third of the way up, the back's hoop hanging down past the table's edge."""
    r = max(0.9, 1.15 * s)
    seat = cv.ell(cx, ty - 2.5 * s, 9.5 * s, 2.4 * s)
    rim = cv.ell(cx, ty - 1.2 * s, 9.5 * s, 2.0 * s) & ~seat
    back_legs = cv.seg([(cx - 3.5 * s, ty - 4 * s), (cx - 4.8 * s, ty - 24 * s)], r * 0.9) | \
        cv.seg([(cx + 3.5 * s, ty - 4 * s), (cx + 4.8 * s, ty - 24 * s)], r * 0.9)
    front_legs = cv.seg([(cx - 8.0 * s, ty - 3 * s), (cx - 10.5 * s, ty - 27 * s)], r) | \
        cv.seg([(cx + 8.0 * s, ty - 3 * s), (cx + 10.5 * s, ty - 27 * s)], r)
    ring = cv.ring(cx, ty - 12 * s, 8.2 * s, 8.2 * s + max(1.0, 1.1 * s), sy=0.3)
    hx = cx + side * 10.5 * s
    back = cv.seg([(hx, ty - 2 * s), (hx + side * 2.5 * s, ty + 7 * s), (hx + side * 2 * s, ty + 17 * s)], r)
    hoop = cv.ring(hx + side * 1.0 * s, ty + 11 * s, 3.6 * s, 3.6 * s + max(1.0, 1.0 * s), sy=2.0)
    cv.put(back_legs, '#140D0A', 0.9 * k)
    m = seat | rim | front_legs | ring | back | hoop
    cv.put(m, '#2B1B12', 0.95 * k)
    cv.put(seat, '#3D271A', 1.0 * k)
    cv.put(rim, '#1C120C', 1.0 * k)
    cv.put(front_legs & C.rim(front_legs, -side, 0), '#6E4A33', 0.9 * k)
    cv.put((ring | hoop) & C.rim(ring | hoop, 0, -1), '#553826', 0.9 * k)
    return m | back_legs


def _table(cv, cx, ty, s, up=True, k=1.0):
    top = cv.ell(cx, ty, 30 * s, 6 * s)
    cv.put(top, '#727A82', 0.9 * k)
    cv.put(top & (cv.yy < ty - 2 * s), '#8E969E', 0.95 * k)
    cv.put(LF.edge_dir(top, 0, 1, 2), '#3C424A', 0.9 * k)
    cv.put(top & (LF.nz(cv.w, cv.h, 3, 821, 2) > 0.66), '#555C64', 0.9 * k)
    cv.put(cv.seg([(cx, ty + 5 * s), (cx, ty + 50 * s)], 2.2 * s, 1.6 * s), '#0B0D10', 1.0)
    cv.put(cv.ell(cx, ty + 52 * s, 13 * s, 3 * s), '#1A1A1C', 1.0)
    if up:
        _chair_up(cv, cx - 13 * s, ty - 1 * s, s, k, side=-1)
        _chair_up(cv, cx + 13 * s, ty - 1 * s, s * 0.95, k, side=1)
    return top


def cafe():
    """r5 background (648 x 360 at (-4, 0)): see the module docstring."""
    cv = LF.Cv(VW + 2 * CMX, VH, -CMX, 0, amb=(0.20, 0.22, 0.28))
    xx, yy = cv.xx, cv.yy
    n1 = cv.nz(16, 811)
    wx0, wy0, wx1, wy1 = 40, 58, 600, 228
    win = (xx >= wx0) & (xx < wx1) & (yy >= wy0) & (yy < wy1)
    # light: the cold snow light through the window, the night light behind the bar, the clock's glow
    cv.light(320, 150, 420, (0.55, 0.62, 0.8), 1.2)
    cv.light(612, 130, 230, (1.2, 0.8, 0.4), 1.5)
    cv.light(CLOCK[0], CLOCK[1] + 60, 140, (0.25, 0.25, 0.22), 1.4)
    cv.put(cv.full(), '#2C3137', 0.6 + n1 * 0.1)
    # ceiling and two pendant lamps (off) hanging into the frame
    ceil = yy < 52
    cv.put(ceil, '#14171B', 0.8)
    for px_ in (150, 470):
        cv.put(cv.seg([(px_, 40), (px_, 60)], 0.5), '#0B0D10', 1.0)
        sh = cv.poly([(px_ - 12, 72), (px_ + 12, 72), (px_ + 5, 60), (px_ - 5, 60)])
        cv.put(sh, '#1C2A26', 0.9 + C.edge_light(sh, (0.0, 1.0), width=2.0, soft=1) * 0.8)
        cv.put(cv.ell(px_, 72, 4, 1.5), '#3C424A', 0.9)
    # the window: the outside, the reversed lettering, the closed sign on the door, condensation
    cv.put(win, '#1A2431', 1.0)
    _station_outside(cv, win)
    tm = K.vtext('KORRIDOR', 'l', 2)[:, ::-1]
    tm = np.repeat(np.repeat(tm, 2, 0), 2, 1)
    sm = K.place(tm, cv.w, cv.h, 320 - tm.shape[1] // 2 + CMX, 66) & win
    cv.emit(sm, '#C49A48', 0.85)
    cv.emit(sm & ~C.shift(sm, 0, -1), '#E8C779', 0.9)
    tc = K.vtext('CAFÉ', 's', 1)[:, ::-1]
    tc = np.repeat(np.repeat(tc, 2, 0), 2, 1)
    cv.emit(K.place(tc, cv.w, cv.h, 320 - tc.shape[1] // 2 + CMX, 90) & win, '#9C7630', 0.85)
    mist = win & (yy > wy1 - 22) & (np.mod(xx + yy * 3, 4) == 0)
    cv.mix(mist, '#727A82', np.clip((yy - (wy1 - 22)) / 22.0, 0, 1) * 0.6)
    # the door in the right pane: its frame, the closed sign hanging on a cord (reversed from inside)
    dfr = (xx >= 520) & (xx < 596) & (yy >= wy0) & (yy < wy1) & ((xx < 523) | (xx >= 593) | (yy < wy0 + 3))
    cv.put(dfr, '#2B1B12', 1.0)
    cv.put(cv.box(526, 150, 532, 154), '#C49A48', 0.9)
    cv.put(cv.seg([(548, 120), (558, 112), (568, 120)], 0.4), '#C8C4BA', 0.7)
    sign = cv.box(540, 120, 576, 136)
    cv.put(sign, '#C8C4BA', 0.75)
    ts = K.vtext('GESCHLOSSEN', 's', 1)[:, ::-1]
    cv.put(K.place(ts, cv.w, cv.h, 558 - ts.shape[1] // 2 + CMX, 125) & sign, '#7A2218', 0.9)
    # mullions + the sill, the radiator under the window
    frame = win & ((np.abs(xx - 226) < 3) | (np.abs(xx - 414) < 3) | (xx < wx0 + 3) | (xx >= wx1 - 3) |
                   (yy < wy0 + 3) | (yy >= wy1 - 4))
    cv.put(frame, '#3D271A', 1.0)
    cv.put((xx >= wx0 - 6) & (xx < wx1 + 6) & (yy >= wy1) & (yy < wy1 + 6), '#553826', 1.0)
    rad = cv.box(wx0 + 40, wy1 + 8, wx0 + 170, wy1 + 30)
    cv.put(rad, '#3C424A', 0.8)
    cv.put(rad & (np.mod(xx, 5) < 2), '#1F2328', 0.8)
    # wainscot below, newspaper holders on the left wall, the coat stand with a forgotten umbrella
    wain = (yy >= 228) & (yy < 262)
    cv.put(wain, '#2B1B12', 0.85 + n1[wain] * 0.1)
    for px_ in range(0, 660, 46):
        cv.put(cv.box(px_ - CMX, 232, px_ - CMX + 1, 260), '#1C120C', 1.0)
    for i, ny in enumerate((96, 126, 156)):
        stick = cv.seg([(4, ny), (34, ny + 4)], 1.0)
        cv.put(stick, '#553826', 0.9)
        paper_ = cv.poly([(8, ny + 2), (30, ny + 5), (28, ny + 24), (6, ny + 20)])
        cv.put(paper_, '#C8C4BA', 0.6 - i * 0.05)
        cv.put(paper_ & (np.mod(yy, 3) == 0) & (np.mod(xx, 5) < 4), '#3A3A3C', 0.8)
    cv.put(cv.box(-4, 60, 0, 262), '#1C120C', 1.0)
    # floor: worn black and white tiles in perspective (low contrast in the night light), the snow light falling
    # through the window onto them -- three skewed panes with the mullions' shadows -- and the polish mirroring the
    # lamp and the clock outside as soft vertical smears
    fl = yy >= 262
    u = (yy - 262) / 98.0
    chk = (np.floor((xx - 320) / (14 + u * 40)) + np.floor((yy - 262) / (4 + u * 10))) % 2 == 0
    cv.put(fl, '#1F2328', 0.85 + n1[fl] * 0.12)
    cv.put(fl & chk, '#5E666E', 0.55 + n1[fl & chk] * 0.12)
    grout = fl & ((np.mod((xx - 320) / (14 + u * 40), 1.0) < 0.05) | (np.mod((yy - 262) / (4 + u * 10), 1.0) < 0.08))
    cv.put(grout, '#14171B', 0.9)
    # the window's light on the floor (cold, from the snow and the square's lamps), skewed toward the camera
    for (a0, a1) in ((wx0 + 3, 223), (229, 411), (417, wx1 - 3)):
        pane = cv.poly([(a0 + 4, 262), (a1 - 4, 262), (a1 + (a1 - 320) * 0.55 + 10, 352), (a0 + (a0 - 320) * 0.55 + 18, 352)])
        fade = np.clip(1 - (yy - 262) / 110.0, 0, 1)
        cv.add(pane & fl, '#232C38', 0.55 * fade)
        cv.add(pane & fl & chk, '#2E3846', 0.45 * fade)
    for (mx_, col) in ((300, '#3A2410'), (CLOCK[0], '#2A2A26')):
        smear = fl & (np.abs(xx - mx_ - (yy - 262) * 0.1) < 4 - u * 2) & (yy < 330)
        cv.add(smear & (LF.hsh(xx, yy, 823) > 0.3), col, np.clip(1 - (yy - 262) / 70.0, 0, 1))
    # the polished floor mirrors the bright window (snow outside): soft vertical sheen under each pane, broken by
    # the mullions, fading toward the camera
    for (a0, a1) in ((wx0 + 3, 223), (229, 411), (417, wx1 - 3)):
        sheen = fl & (xx >= a0 + 2) & (xx < a1 - 2) & (yy < 312)
        k_ = np.clip(1 - (yy - 262) / 50.0, 0, 1) ** 1.5 * (0.7 + 0.3 * LF.vnoise(xx * 0.08, yy * 0.4, 829))
        cv.add(sheen, '#26303C', k_)
    # a coir mat at the door, a chair standing on the floor in the right foreground, the near corner darker
    mat = cv.poly([(522, 264), (598, 264), (610, 284), (512, 284)])
    cv.put(mat, '#3A2618', 0.7 + n1[mat] * 0.2)
    cv.put(mat & (np.mod(xx + yy, 3) == 0), '#2A1C12', 0.8)
    cv.put(LF.edge_top(mat), '#553826', 0.8)
    vig = fl & (yy > 320)
    cv.mix(vig, '#0B0D10', np.clip((yy - 320) / 60.0, 0, 1) * 0.45)
    # marble tables with the bentwood chairs upside down on them (back to front), a second row nearer
    _table(cv, 372, 240, 0.78)
    _table(cv, 250, 238, 0.7)
    _table(cv, 520, 246, 0.9)
    _table(cv, 96, 250, 0.95)
    _table(cv, 452, 282, 1.15)
    _table(cv, -2, 290, 1.25)
    # a zinc mop bucket and the mop leaning on the near table: the floor was washed after closing, still damp
    bk = cv.poly([(380, 312), (406, 312), (402, 340), (384, 340)])
    cv.put(bk, '#727A82', 0.75 + C.edge_light(bk, (-0.8, -0.4), width=3.0, soft=1)[bk] * 0.6)
    cv.put(cv.ell(393, 312, 13, 3), '#3C424A', 0.9)
    cv.put(cv.ell(393, 312, 11, 2) , '#14171B', 1.0)
    cv.put(cv.seg([(381, 316), (380, 306), (393, 300), (406, 306), (405, 316)], 0.5), '#8E969E', 0.8)
    cv.put(cv.seg([(396, 312), (430, 226)], 1.2), '#553826', 0.95)
    cv.put(cv.seg([(396, 312), (391, 324)], 2.4, 1.6), '#8E856C', 0.7)
    cv.add(fl & cv.ell(393, 346, 30, 5), '#141C26', 0.8)
    # a dropped napkin and a cigarette end by Elena's table
    cv.put(cv.poly([(330, 318), (342, 315), (346, 322), (334, 325)]), '#C8C4BA', 0.65)
    cv.put(cv.box(318, 330, 322, 331), '#C8C4BA', 0.7)
    # the bar at the right: counter, espresso machine, glasses, the night light, the cake dome
    bar = (xx >= 596) & (yy >= 150)
    cv.put(bar, '#3D271A', 0.95 + n1[bar] * 0.1)
    cv.put(bar & (yy < 156), '#C8C4BA', 0.8)
    cv.put(bar & (yy >= 156) & (np.mod(xx, 12) < 1), '#1C120C', 1.0)
    shelf = (xx >= 600) & (yy >= 96) & (yy < 99)
    cv.put(shelf, '#553826', 1.0)
    for gx in range(604, 644, 6):
        g = cv.box(gx, 86, gx + 4, 96)
        cv.put(g, '#8E969E', 0.7)
        cv.put(g & (xx == gx), '#EEEAE0', 0.9)
    # the lever espresso machine: chrome boiler under its domed cap with the brass eagle, a pressure gauge, two
    # groups with their levers raised, the portafilters' black handles, the steam wand, the drip tray
    boiler = cv.box(604, 118, 632, 142)
    cv.put(boiler, '#3C424A', 0.85 + C.edge_light(boiler, (-0.9, -0.2), width=4.0, soft=1)[boiler] * 0.9)
    cv.put(boiler & (np.abs(xx - 609) < 1), '#C8C4BA', 0.9)
    cv.put(cv.box(604, 126, 632, 128), '#9C7630', 0.9)
    cap = cv.ell(618, 118, 14, 5) & (yy < 119)
    cv.put(cap, '#555C64', 0.9 + C.edge_light(cap, (-0.6, -0.8), width=2.0, soft=1)[cap] * 0.8)
    cv.put(cv.box(616, 108, 621, 113) | cv.box(613, 110, 624, 112), '#9C7630', 0.95)
    gauge = cv.ell(625, 133, 3, 3)
    cv.put(gauge, '#1A1A1C', 1.0)
    cv.put(cv.ell(625, 133, 2, 2), '#C8C4BA', 0.8)
    for gx_ in (609, 625):
        cv.put(cv.box(gx_ - 2, 142, gx_ + 3, 146), '#555C64', 0.9)
        cv.put(cv.seg([(gx_, 142), (gx_ - 3, 124)], 0.7), '#3C424A', 0.95)
        cv.put(cv.ell(gx_ - 3, 123, 1.5, 1.5), '#1A1A1C', 1.0)
        cv.put(cv.box(gx_ - 1, 146, gx_ + 9, 148), '#0B0D10', 1.0)
    cv.put(cv.seg([(603, 132), (599, 146)], 0.6), '#8E969E', 0.9)
    cv.put(cv.box(602, 148, 634, 150), '#3C424A', 0.9)
    cv.emit(cv.ell(636, 112, 3, 3), '#FCE2B0')
    dome = cv.ell(600, 146, 9, 10) & (yy < 150)
    cv.put(dome & ~cv.ell(600, 147, 7.5, 8.5), '#B8C4D0', 0.8)
    # the coat stand by the door with a forgotten umbrella
    cv.put(cv.seg([(586, 120), (586, 262)], 1.2), '#1C120C', 1.0)
    cv.put(cv.seg([(578, 124), (594, 118)], 0.9), '#1C120C', 1.0)
    umb = cv.poly([(580, 150), (586, 150), (590, 214), (582, 216)])
    cv.put(umb, '#14171B', 0.9)
    cv.put(cv.seg([(584, 150), (580, 142), (575, 144)], 0.7), '#553826', 0.9)
    # a bentwood chair left standing on the floor in the right foreground, in front of the bar
    fx_, fy_ = 566, 304
    fch = (cv.seg([(fx_ - 14, fy_ - 2), (fx_ - 16, 360)], 1.8) | cv.seg([(fx_ + 16, fy_ - 2), (fx_ + 18, 360)], 1.8) |
           cv.ell(fx_, fy_ - 2, 22, 6) |
           cv.seg([(fx_ + 16, fy_ - 4), (fx_ + 20, fy_ - 60), (fx_ + 12, fy_ - 92), (fx_ - 4, fy_ - 96)], 2.0) |
           cv.ring(fx_ + 14, fy_ - 58, 7, 9, sy=2.2))
    cv.put(fch, '#1C120C', 0.85)
    cv.put(fch & C.rim(fch, -1, -1), '#553826', 0.8)
    cv.put(cv.ell(fx_, fy_ - 3, 20, 4.5), '#2B1B12', 0.9)
    out = cv.quant(PAL_C, spread=10.0)
    out[..., 3] = 255
    L['clock'] = list(CLOCK)
    L['clock_r'] = CLOCK_R
    L['cafe_win'] = [wx0 + 3, wy0 + 3, wx1 - 3, 196]
    L['cafe_at'] = [-CMX, 0]
    return out


def cafe_fg():
    """Elena's table in the foreground: marble, her chair pulled out (not up like the others), the untouched
    glass of tea with lemon on its saucer, the spoon, two sugar cubes; transparent elsewhere."""
    cv = LF.Cv(240, 140, 90, 214, amb=(0.24, 0.26, 0.32))
    cv.light(300, 120, 300, (0.6, 0.66, 0.84), 1.2)
    cv.light(640, 130, 420, (0.5, 0.33, 0.16), 1.4)
    cx, ty, s = 196, 268, 1.45
    ch = (cv.seg([(cx + 38 * s, ty - 30 * s), (cx + 40 * s, ty + 8 * s)], 1.5 * s) |
          cv.ell(cx + 30 * s, ty + 8 * s, 12 * s, 3 * s) |
          cv.seg([(cx + 22 * s, ty + 10 * s), (cx + 20 * s, ty + 50 * s)], 1.1 * s) |
          cv.seg([(cx + 38 * s, ty + 10 * s), (cx + 40 * s, ty + 50 * s)], 1.1 * s) |
          cv.ring(cx + 39 * s, ty - 18 * s, 5 * s, 6.2 * s, sy=1.8))
    cv.put(ch, '#3D271A', 0.8 + C.edge_light(ch, (0.6, -0.8), width=2.0, soft=1) * 0.8)
    _table(cv, cx, ty, s, up=False)
    gx, gy = cx - 10 * s, ty - 2 * s
    gw, gh = 4.4 * s, 17 * s
    cv.put(cv.ell(gx, gy, 9 * s, 2.0 * s), '#EEEAE0', 0.8)
    glass = (np.abs(cv.xx + 0.5 - gx) < gw - (gy - cv.yy) * 0.04) & (cv.yy >= gy - gh) & (cv.yy < gy)
    cv.put(glass, '#B8C4D0', 0.75)
    tea = glass & (cv.yy >= gy - gh * 0.7)
    cv.put(tea, '#A8643A', 0.95)
    cv.put(glass & (np.abs(cv.xx + 0.5 - (gx - gw * 0.55)) < 0.7), '#EEEAE0', 1.2)
    cv.put(glass & (cv.yy < gy - gh + 1.5), '#C8C4BA', 1.1)
    lemon = cv.ell(gx + 1, gy - gh * 0.7, 3.2 * s, 1.0 * s) & glass
    cv.put(lemon, '#E8C779', 1.0)
    cv.put(cv.seg([(gx + 6 * s, gy - 1), (gx + 14 * s, gy + 1)], 0.6), '#C49A48', 1.1)
    for sx_ in (12, 17):
        cv.put(cv.box(gx + sx_ * s, gy - 4, gx + sx_ * s + 4, gy), '#F2F3F5', 0.9)
    out = cv.quant(PAL_C, spread=8.0)
    L['cafe_fg_at'] = [90, 214]
    return out


def cafe_glow():
    return Q.glow_sprite(VW, VH, [(CLOCK[0], CLOCK[1], 46, 40, (34, 34, 30), 1.4), (614, 120, 80, 64, (54, 36, 14), 1.6),
                                  (300, 112, 26, 26, (40, 28, 12), 1.5)], 6.0)


def cat():
    L['cat_at'] = [602, 141]
    return LF.cat_sheet()
