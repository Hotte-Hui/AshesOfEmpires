"""env_c3p2_cine_fire -- art of LS_C3_Fire and LS_C3_Escape (owner: cinematics stream, round 8; C3P2_DESIGN §2.9).

The commission's registry in the souterrain of the palais' east wing (the former Kurhaus coal cellar, brick vaults,
oak card cabinets with brass label holders, the green-shaded lamp over the sorting table; §5.1).

LS_C3_Fire   f1 the sorting table under the green lamp, Konrad from behind (pose 0/1: he looks up)
             f2 the Magazin aisle in one-point perspective: the C-17 boxes catch, a figure in a long coat and a
                porter's cap slips out through the lit service door at the end (a silhouette, no face)
             f3 the iron-clad ramp door from inside: the cold gap light, a shadow passes, the bolt slides home
             f4 the same hall as f1, burning: fire along the cabinets, smoke under the vault, Alexei at the table
LS_C3_Escape e1 up the coal chute toward the square of snow light, the file pushed ahead
             e2 the yard: the 1909 hatch flips open, Konrad crawls out with the file, smoke after him
             e3 a: Alexei's hand out of the smoke, Konrad's hand takes it; b: both on their backs in the snow
             e4 the east wing from the lane: the souterrain windows burst orange one after another
Runtime: scenes/cinematics/ch3_fire/ch3_fire.gd, ch3_escape/ch3_escape.gd (anchors in layout.json fire/escape).
"""
from __future__ import annotations

import math

import numpy as np

import env_c3p2_cine_kit as Q
from env_c3p2_cine_kit import (C, K, VW, VH, NIGHT, SNOW, LAMP, IRON, OAK, GREEN, PAPER, FIRE, RED, BRASS,
                               SMOKE, K_COAT, A_COAT, A_FUR, K_HAT, grid, poly, ell, box, hexrgb)
import pg

LF = Q.LAYOUT.setdefault('fire', {})
LE = Q.LAYOUT.setdefault('escape', {})

BRICK = ['#0A0706', '#140D0A', '#1E140F', '#2A1C15', '#3A271C', '#4E3424', '#66442E']
SOOT = ['#050404', '#0B0908', '#13100E', '#1C1814', '#27211C', '#342C25']
EMBERGLOW = ['#1A0805', '#3A0F08', '#6E1E0C', '#A8381A', '#D8662A', '#F2A044', '#FCE0A0']


def _bricks(p, m, ramp, base, light=None, course=7, brick=16, seed=0, gain=2.4, mortar=-0.9):
    """Brickwork on mask m: running bond, value noise per brick, darker mortar joints."""
    yy, xx = p.yy, p.xx
    row = np.floor(yy / course)
    off = np.where(np.mod(row, 2) == 0, 0, brick / 2)
    col = np.floor((xx + off) / brick)
    hsh = np.mod(np.sin(row * 12.9898 + col * 78.233 + seed) * 43758.5453, 1.0)
    joint = (np.mod(yy, course) < 1) | (np.mod(xx + off, brick) < 1)
    lt = 0.0 if light is None else light
    t = base + (hsh - 0.5) * 0.9 + lt * gain
    p.put(m, ramp, t[m] if not np.isscalar(t) else t)
    j = m & joint
    p.put(j, ramp, (t + mortar)[j])


# =========================================================================================== LS_C3_Fire
LAMP_G = (300, 104)                   # the green shade (centre of its rim)
TABLE_TOP = (236, 268)                # far / near edge of the sorting table (f1 / f4)


def _hall(mode):
    """f1 (mode 'night') / f4 (mode 'fire'): the Karteisaal from the near side of the sorting table."""
    fire = mode == 'fire'
    R = C.ramps(B=BRICK, O=OAK, M=BRASS, G=GREEN, P=PAPER, N=NIGHT, S=SNOW, F=EMBERGLOW, I=IRON, R=RED,
                V=['#120E14', '#1E1820', '#2C2430', '#3E3444', '#54485A'], X=SMOKE)
    p = C.Paint(VW, VH, R, 'hall_' + mode)
    yy, xx = p.yy, p.xx
    nz = Q.noise(VW, VH, 12, 901)
    # light fields
    green = Q.lightfield(VW, VH, [(LAMP_G[0], 250, 210, 1.0, 1.6), (LAMP_G[0], 150, 110, 0.6, 1.3)])
    if fire:
        heat = Q.lightfield(VW, VH, [(420, 190, 360, 1.0, 1.1), (180, 200, 260, 0.7, 1.2), (560, 170, 220, 0.8, 1.2)])
        green *= 0.35
    else:
        heat = np.zeros((VH, VW), np.float32)
    cold = Q.lightfield(VW, VH, [(80, 64, 160, 0.8, 1.6)])
    # the vault (brick barrel) at the top, the back wall of cabinets, the floor
    vault = yy < 70 + 0.0006 * (xx - 320) ** 2
    _bricks(p, vault, 'B', 0.8, green * 0.4 + heat * (1.6 if fire else 0) + cold * 0.6, course=6, brick=14, seed=3)
    # high souterrain window at the top left: snow light through bars
    win = box(44, 52, 116, 84)
    p.put(win, 'S', 2.2 + (84 - yy[win]) / 16.0)
    p.put(win & (np.mod(xx, 12) < 2), 'I', 1.0)
    p.put(win & (yy >= 80), 'S', 6.0)                                           # snow on the sill
    p.put(win & (yy < 58) & (np.mod(xx, 7) < 3), 'S', 5.0)                     # snow crust on the outer pane
    # card cabinets: a wall of drawers (columns of 3 x 12 drawers) from y 72 to the table
    cab = (yy >= 70 + 0.0006 * (xx - 320) ** 2) & (yy < 240)
    lt = green * 2.4 + heat * (3.4 if fire else 0) + cold * 0.4
    p.put(cab, 'O', 0.3 + lt[cab] * 1.2 + nz[cab] * 0.4)
    dw, dh = 22, 12
    cx_ = np.mod(xx - 8, dw)
    cy_ = np.mod(yy - 74, dh)
    gaps = cab & ((cx_ < 1) | (cy_ < 1))
    p.put(gaps, 'O', 0.2 + lt[gaps] * 0.5)
    holder = cab & (np.abs(cx_ - dw / 2) < 3.5) & (np.abs(cy_ - 4) < 1.5)
    p.put(holder, 'M', 0.1 + lt[holder] * 1.5)
    lab = holder & (np.abs(cy_ - 4) < 0.6) & (np.abs(cx_ - dw / 2) < 2.5)
    p.put(lab, 'P', 0.2 + lt[lab] * 2.2)
    knob = cab & (np.abs(cx_ - dw / 2) < 1) & (np.abs(cy_ - 8.5) < 1)
    p.put(knob, 'M', 0.3 + lt[knob] * 2.2)
    # cabinet columns: darker dividers every 3 drawers
    div = cab & (np.mod(xx - 8, dw * 3) < 3)
    p.put(div, 'O', 0.4 + lt[div] * 0.6)
    # drawer C-17 half open at the right with Elena's wine-red scarf over the chair beside it (f1 only)
    if not fire:
        dr = box(510, 176, 540, 192)
        p.put(dr, 'O', 3.0 + lt[dr])
        p.put(box(512, 172, 538, 178), 'P', 2.4 + lt[box(512, 172, 538, 178)] * 1.4)
        tag = box(519, 181, 531, 186)
        p.put(tag, 'R', 3.0)
        scarf = poly([(560, 200), (574, 196), (580, 240), (570, 262), (562, 236)])
        p.put(scarf, 'R', 1.4 + lt[scarf] * 1.4)
    # floor beyond the table (barely visible)
    # the sorting table
    far, near = TABLE_TOP
    top = (yy >= far) & (yy < near) & (xx >= 40) & (xx < 600)
    tl = green * 3.6 + heat * (2.4 if fire else 0)
    p.put(top, 'O', 1.6 + tl[top] + (yy[top] - far) / 40.0)
    front = (yy >= near) & (yy < near + 12) & (xx >= 40) & (xx < 600)
    p.put(front, 'O', 1.0 + tl[front] * 0.6)
    p.put((yy >= near + 12) & (xx >= 40) & (xx < 600), 'O', 0.2)
    p.put((yy >= near + 12) & ((xx < 40) | (xx >= 600)), 'B', 0.4)
    p.put(top & (yy == far), 'O', 3.0 + tl[top & (yy == far)])
    # papers on the table: the two halves side by side (Russian bluish/violet, German cream/black)
    if not fire:
        for i, (x0, ru) in enumerate(((120, True), (158, True), (196, True), (236, False), (274, False), (312, False))):
            y0 = far + 6 + (i % 2) * 3
            sheet = poly([(x0, y0), (x0 + 32, y0 - 1), (x0 + 34, y0 + 20), (x0 + 2, y0 + 21)])
            p.put(sheet, 'S' if ru else 'P', (3.6 if ru else 3.0) + tl[sheet] * 0.6)
            for ly in range(y0 + 4, y0 + 18, 3):
                ln = sheet & (yy == ly) & (np.mod(xx * 3 + ly, 5) < 3) & (xx > x0 + 4) & (xx < x0 + 28)
                p.put(ln, 'V' if ru else 'N', 2.0 if ru else 1.0)
            st = sheet & ell(x0 + 24, y0 + 14, 4, 3)
            p.put(st, 'V' if ru else 'R', 3.0)
        # red thread linking pairs (the Gegenprobe)
        for (a, b) in ((136, 252), (174, 290), (212, 328)):
            p.put(p.line([(a, far + 16), ((a + b) / 2, far + 24), (b, far + 16)], r=0.5), 'R', 3.4)
        mag = ell(380, far + 16, 9, 5)
        p.put(mag, 'M', 2.0 + tl[mag])
        p.put(ell(380, far + 16, 6, 3), 'S', 4.0)
        p.put(p.line([(388, far + 18), (402, far + 24)], r=1.2), 'O', 2.0)
    else:
        # scattered papers, a fallen chair: the table as he left it
        for x0 in (130, 180, 240, 300):
            sheet = poly([(x0, far + 8), (x0 + 30, far + 6), (x0 + 33, far + 24), (x0 + 3, far + 26)])
            p.put(sheet, 'P', 2.2 + tl[sheet] * 0.6)
    # the lamp: cord, enamel shade (green outside, white inside), bulb
    p.put(box(LAMP_G[0], 0, LAMP_G[0] + 1, LAMP_G[1] - 22), 'I', 1.0)
    shade = poly([(LAMP_G[0] - 9, LAMP_G[1] - 22), (LAMP_G[0] + 10, LAMP_G[1] - 22), (LAMP_G[0] + 34, LAMP_G[1]),
                  (LAMP_G[0] - 33, LAMP_G[1])])
    p.put(shade, 'G', 2.6 + np.clip((xx[shade] - LAMP_G[0]) / 40.0, -1, 1) * -0.8)
    p.put(shade & (yy >= LAMP_G[1] - 2), 'G', 5.6)
    p.put(ell(LAMP_G[0], LAMP_G[1] + 1, 6, 2.5), 'P', 6.0)
    if fire:
        # smoke already hangs under the vault (the runtime rolls more toward the camera)
        sm = yy < 64 + 0.0006 * (xx - 320) ** 2 + 18 * Q.noise(VW, VH, 40, 931)
        p.put(sm, 'X', 1.0 + heat[sm] * 2.6 + nz[sm] * 0.8)
        # the far cabinets scorched: dark streaks above the fire line
        sc = cab & (yy < 96 + 0.0006 * (xx - 320) ** 2 + 10 * Q.noise(VW, VH, 30, 933))
        p.put(sc, 'X', 0.8 + heat[sc] * 2.0)
    p.resolve(band=2.0)
    return p.L.c


def f1_bg():
    return _hall('night')


def f4_bg():
    return _hall('fire')


def lamp_cone():
    """Additive green light of the lamp: the cone and the pool on the table (modulated at runtime)."""
    a = np.zeros((VH, VW, 3), np.float32)
    yy, xx = grid()
    lx, ly = LAMP_G
    u = np.clip((yy - ly) / (TABLE_TOP[1] - ly), 0, 1)
    half = 30 + u * 150
    cone = (yy > ly) & (np.abs(xx - lx) < half)
    g = np.clip(1 - np.abs(xx - lx) / np.maximum(half, 1), 0, 1) ** 1.2 * (1 - u * 0.5)
    a += (cone * g)[..., None] * np.array([10, 26, 16], np.float32)
    Q.add_glow(a, lx, TABLE_TOP[0] + 14, 190, 26, (26, 56, 34), 1.4)
    Q.add_glow(a, lx, ly + 2, 40, 10, (40, 70, 46), 1.2)
    return K.soft_quant(a, 6.0)


def fire_glow(cx, cy, rx, ry, k=1.0):
    return Q.glow_sprite(VW, VH, [(cx, cy, rx, ry, (110 * k, 52 * k, 16 * k), 1.3),
                                  (cx, cy, rx * 0.45, ry * 0.5, (90 * k, 40 * k, 10 * k), 1.2)], 6.0)


# ------------------------------------------------------------------------------------------- f2 aisle
F2 = {'vpx': 320.0, 'vpy': 150.0, 'f': 300.0, 'eye': 1.6, 'half': 1.2, 'far': 9.0, 'h': 2.6}


def _f2p(X, Y, Z):
    return (F2['vpx'] + F2['f'] * X / Z, F2['vpy'] - F2['f'] * (Y - F2['eye']) / Z)


def f2_bg():
    R = C.ramps(O=OAK, I=IRON, P=PAPER, R=RED, B=BRICK, N=NIGHT, F=EMBERGLOW,
                C=['#100C08', '#1C150E', '#2A2014', '#3A2C1C', '#4E3C26', '#665036', '#806848'])
    p = C.Paint(VW, VH, R, 'f2')
    yy, xx = p.yy, p.xx
    f, vx, vy, eye, half, far = F2['f'], F2['vpx'], F2['vpy'], F2['eye'], F2['half'], F2['far']
    heat = Q.lightfield(VW, VH, [(430, 175, 300, 1.0, 1.3), (vx, vy + 10, 150, 0.35, 1.2)])
    door_l = Q.lightfield(VW, VH, [(vx, vy + 20, 90, 0.8, 1.4)])
    # far wall with the service door
    fw = np.ones((VH, VW), bool)
    _bricks(p, fw, 'B', 0.8, heat * 0.6 + door_l * 0.8, course=4, brick=9, seed=11)
    # ceiling, floor (planes), side shelves
    dx = xx + 0.5 - vx
    dy = yy + 0.5 - vy
    # floor Y=0: Z = f*eye/dy
    Zf = np.where(dy > 0.5, f * eye / np.maximum(dy, 0.5), 1e9)
    Xf = dx * Zf / f
    floor = (dy > 0.5) & (Zf < far) & (np.abs(Xf) < half)
    p.put(floor, 'C', 1.0 + heat[floor] * 2.4 + np.clip(1 - Zf[floor] / far, 0, 1) * 0.6)
    p.put(floor & (np.mod(Zf, 1.2) < 0.05), 'C', 0.4)
    # ceiling Y=2.9
    Zc = np.where(dy < -0.5, f * (2.9 - eye) / np.maximum(-dy, 0.5), 1e9)
    Xc = dx * Zc / f
    ceil = (dy < -0.5) & (Zc < far) & (np.abs(Xc) < half + 0.3)
    _bricks(p, ceil, 'B', 0.5, heat * 0.5, course=5, brick=12, seed=13)
    # side shelving planes X = +-half
    for sgn in (-1, 1):
        side = (dx * sgn > 0.5)
        Zs = np.where(side, f * half / np.maximum(np.abs(dx), 0.5), 1e9)
        Ys = eye - dy * Zs / f
        sh = side & (Zs >= 1.0) & (Zs < far) & (Ys >= 0) & (Ys < F2['h'])
        lt = heat * (2.6 if sgn > 0 else 1.6)
        p.put(sh, 'O', 0.3 + lt[sh] * 1.2)
        boards = sh & (np.mod(Ys, 0.42) < 0.035)
        p.put(boards, 'O', 0.9 + lt[boards] * 1.6)
        # archive boxes: width 0.34 m along Z, height 0.3, a label on each
        bz = np.mod(Zs, 0.36)
        by = np.mod(Ys, 0.42)
        boxf = sh & (bz > 0.02) & (by > 0.04) & (by < 0.34)
        hsh = np.mod(np.sin(np.floor(Zs / 0.36) * 7.1 + np.floor(Ys / 0.42) * 3.3 + sgn) * 437.5, 1.0)
        p.put(boxf, 'C', 0.5 + hsh[boxf] * 0.8 + lt[boxf] * 2.0)
        lab = boxf & (np.abs(bz - 0.18) < 0.06) & (np.abs(by - 0.19) < 0.05)
        p.put(lab, 'P', 0.4 + lt[lab] * 2.6)
        if sgn > 0:
            c17 = lab & (Zs > 2.9) & (Zs < 4.7) & (Ys > 0.8) & (Ys < 1.7)
            p.put(c17, 'R', 2.6 + lt[c17] * 0.6)
        up = sh & (np.mod(Zs, 2.0) < 0.07)
        p.put(up, 'I', 1.4 + lt[up] * 1.4)
        top = side & (Zs >= 1.0) & (Zs < far) & (Ys >= F2['h']) & (Ys < 2.9)
        p.put(top, 'B', 0.6 + heat[top] * 1.0)
    # the service door at the end (closed state in the bg; open frames are a sprite)
    d0 = _f2p(-0.5, 2.1, far)
    d1 = _f2p(0.5, 0.0, far)
    door = box(d0[0], d0[1], d1[0], d1[1])
    p.put(door, 'I', 1.2 + door_l[door] * 0.4)
    p.put(door & (np.mod(xx, 5) < 1), 'I', 2.4)                                   # bars of the gate
    p.resolve(band=2.0)
    LF['f2_door'] = [int(d0[0]), int(d0[1]), int(d1[0]), int(d1[1])]
    # fire anchors on the C-17 shelf (bottom centres of the flame sprites), in order of catching
    anchors = []
    for (Z, Y) in ((3.4, 1.26), (3.9, 1.26), (3.1, 0.84), (4.3, 1.68), (2.9, 1.68), (4.5, 0.84)):
        x, y = _f2p(half - 0.02, Y, Z)
        anchors.append([round(x, 1), round(y, 1)])
    LF['f2_fire'] = anchors
    return p.L.c


def f2_door():
    """4 frames of the service door (sprite over the bg door): the figure in the lit doorway, half out, the
    empty lit doorway, closed.  Long coat, porter's cap, seen from behind - never a face."""
    x0, y0, x1, y1 = LF.get('f2_door', [304, 115, 336, 197])
    w, h = x1 - x0 + 8, y1 - y0 + 4
    R = C.ramps(L=LAMP, N=NIGHT, I=IRON)
    frames = []
    for i in range(4):
        p = C.Paint(w, h, R, 'f2door', ox=x0 - 4, oy=y0 - 2)
        yy, xx = p.yy, p.xx
        dm = (xx >= x0) & (xx < x1) & (yy >= y0) & (yy < y1)
        if i < 3:
            p.put(dm, 'L', 3.6 - (yy[dm] - y0) / (y1 - y0) * 1.2)           # the lit stairwell
            p.put(dm & (yy > y1 - 14) & (np.mod(yy, 4) < 1), 'L', 2.2)       # steps
            p.put(dm & (np.mod(xx, 5) < 1) & (i == 2), 'I', 1.6)
        else:
            p.put(dm, 'I', 1.2)
            p.put(dm & (np.mod(xx, 5) < 1), 'I', 2.4)
        if i < 2:
            cx = (x0 + x1) / 2 + (0 if i == 0 else 9)
            hgt = (y1 - y0) * 0.86
            top = y1 - hgt
            sil = p.poly([(cx - 5.5, top + 9), (cx + 5.5, top + 9), (cx + 8, y1), (cx - 8, y1)])
            sil |= p.ell(cx, top + 5.5, 3.6, 4.2)
            sil |= p.box(cx - 4.5, top + 1, cx + 4.5, top + 4)                  # porter's cap crown
            sil |= p.box(cx - 2, top + 3, cx + 6.5, top + 5)                    # its peak (he turns away)
            sil |= p.poly([(cx - 6, top + 10), (cx - 9, top + 26), (cx - 6, top + 27)])   # arm
            if i == 1:
                sil &= xx >= x0 + (x1 - x0) * 0.55                               # half through the door
            p.put(sil & dm, 'N', 0.6)
            p.put(sil & dm & C.rim(sil, 1, 0), 'L', 1.6)
        p.resolve(band=2.0)
        frames.append(p.L.c)
    LF['f2_door_at'] = [x0 - 4, y0 - 2]
    return Q.sheet(frames)


# ------------------------------------------------------------------------------------------- f3 ramp door
F3_GAP_X = 470                        # x of the vertical gap (door edge / frame)
F3_FLOOR = 292


def f3_bg():
    R = C.ramps(O=OAK, I=IRON, B=BRICK, N=NIGHT, S=SNOW, M=BRASS)
    p = C.Paint(VW, VH, R, 'f3')
    yy, xx = p.yy, p.xx
    nz = Q.noise(VW, VH, 10, 951)
    warm = Q.lightfield(VW, VH, [(260, 330, 420, 0.8, 1.2)])
    wall = np.ones((VH, VW), bool)
    _bricks(p, wall, 'B', 0.6, warm * 1.2, course=8, brick=20, seed=21)
    door = box(150, 0, F3_GAP_X, F3_FLOOR)
    planks = np.mod(xx - 150, 40) < 1
    p.put(door, 'O', 1.0 + warm[door] * 2.2 + nz[door] * 0.6)
    p.put(door & planks, 'O', 0.3)
    grain = door & (Q.noise(VW, VH, 3, 953) > 0.66)
    p.put(grain, 'O', 0.6 + warm[grain] * 1.6)
    for sy in (40, 150, 250):
        strap = door & (yy >= sy) & (yy < sy + 14)
        p.put(strap, 'I', 1.6 + warm[strap] * 2.2)
        p.put(strap & (yy == sy), 'I', 3.0 + warm[strap & (yy == sy)] * 2.0)
        for rx in range(160, F3_GAP_X - 6, 26):
            rv = ell(rx, sy + 7, 2.4, 2.4)
            p.put(rv, 'I', 3.2 + warm[rv] * 1.6)
    # the inner lock box and handle
    lb = box(398, 120, 440, 168)
    p.put(lb, 'I', 1.8 + warm[lb] * 2.0)
    p.put(ell(418, 150, 4, 4), 'I', 0.4)
    p.put(p.line([(408, 132), (446, 132)], r=2.2), 'I', 3.0)
    # frame (stone jamb) right of the gap, the threshold
    jamb = box(F3_GAP_X + 3, 0, F3_GAP_X + 46, F3_FLOOR)
    p.put(jamb, 'B', 1.6 + warm[jamb] * 1.6)
    p.put(box(F3_GAP_X, 0, F3_GAP_X + 3, F3_FLOOR), 'N', 0.0)                      # gap (light drawn at runtime)
    flr = yy >= F3_FLOOR
    p.put(flr, 'B', 0.8 + warm[flr] * 1.8)
    p.put(box(150, F3_FLOOR, F3_GAP_X + 3, F3_FLOOR + 3), 'N', 0.0)
    # snow already blown in under the door
    drift = flr & (yy < F3_FLOOR + 18) & (xx > 170) & (xx < 470) & (Q.noise(VW, VH, 6, 955) > 0.52 + (yy - F3_FLOOR) / 40.0)
    p.put(drift, 'S', 2.6 + nz[drift])
    p.resolve(band=2.0)
    LF['f3_gap'] = [F3_GAP_X, 0, F3_GAP_X + 3, F3_FLOOR]
    LF['f3_floor'] = [150, F3_FLOOR, F3_GAP_X + 3, F3_FLOOR + 3]
    return p.L.c


# ------------------------------------------------------------------------------------------- f4 Alexei
def f4_alexei():
    """Alexei from behind at the near side of the table, the burning cabinets beyond: almost black against the
    fire, an orange rim on the ushanka (crown, ear flaps, back flap), the fur collar, broad quilted shoulders and
    the satchel strap; 2 frames (breath / the head turned a little toward the fire's front)."""
    w, h = 190, 230
    x0, y0 = 54, 112
    R = C.ramps(A=['#020504', '#060B09', '#0B1410', '#122019'], U=['#060506', '#0E0C0C', '#181412', '#241E1A'],
                F=EMBERGLOW, T=['#0A0604', '#160E08', '#24160C'])
    frames = []
    for fr in range(2):
        p = C.Paint(w, h, R, 'f4_alexei', ox=x0, oy=y0)
        b = 0 if fr == 0 else -1
        t = 0 if fr == 0 else 3
        hx, hy = x0 + 96 + t, y0 + 52 + b
        crown = p.ell(hx, hy - 12, 27, 18)
        hat = crown | p.rr(hx - 30, hy - 14, hx + 30, hy + 24, 9)
        collar = p.ell(hx - t, hy + 28, 34, 12)
        coat = p.poly([(hx - 34 - t, hy + 22), (hx - 66 - t, hy + 44 + b), (hx - 80 - t, hy + 92), (hx - 86 - t, y0 + h),
                       (hx + 86 - t, y0 + h), (hx + 80 - t, hy + 92), (hx + 66 - t, hy + 44 + b), (hx + 34 - t, hy + 22)])
        sil = hat | collar | coat
        p.put(coat, 'A', 1.0)
        quilt = coat & (np.mod(p.yy + np.abs(p.xx - hx) * 0.12, 12) < 1.0)
        p.put(quilt, 'A', 0.2)
        p.put(collar, 'U', 1.2 + Q.noise(w, h, 3, 961)[collar] * 1.0)
        p.put(hat, 'U', 1.0 + Q.noise(w, h, 2.5, 962)[hat] * 1.2)
        flap = hat & (np.abs(p.xx - hx) > 16) & (p.yy > hy - 2)
        p.put(flap, 'U', 0.6)                                                       # the ear flaps, a shade darker
        strap = p.line([(hx - 44 - t, hy + 34), (hx + 58 - t, hy + 170)], r=3.2) & coat
        p.put(strap, 'T', 1.4)
        # fire ahead: a hot rim on the outer boundary only (top strongest, flanks weaker)
        outer = sil & ~C.shift(sil, 0, -1)
        for k in (2, 3):
            outer |= sil & ~C.shift(sil, 0, -k) & (Q.noise(w, h, 2, 964 + k) > 0.35)
        p.put(outer, 'F', 3.0 + (outer & hat)[outer] * 1.6)
        for sx in (-1, 1):
            side = sil & ~C.shift(sil, sx, 0) & ~outer
            p.put(side, 'F', 2.0)
            side2 = sil & ~C.shift(sil, sx * 2, 0) & ~outer & ~side & (p.yy < hy + 80)
            p.put(side2, 'F', 1.0)
        fuzz = hat & ~C.shift(hat, 0, -3) & (Q.noise(w, h, 1.5, 963) > 0.5)
        p.put(fuzz, 'F', 4.6)
        p.resolve(band=2.0)
        frames.append(p.L.c)
    LF['f4_alexei'] = [x0, y0]
    return Q.sheet(frames)


def f4_anchors():
    """Flames along the cabinets in the order the fire runs (right -> left): [x, y bottom, size 0 small/1 big/2 wide],
    irregular clusters (a deterministic jitter), more of them up where the old drawers burn best."""
    rng = np.random.default_rng(1051)
    pts = []
    x = 634.0
    while x > -30:
        k = rng.integers(0, 3)
        pts.append([round(x), round(164 + rng.uniform(-14, 10)), 2 if k == 0 else 1])
        if rng.random() < 0.7:
            pts.append([round(x - rng.uniform(8, 22)), round(236 + rng.uniform(-8, 4)), 0])
        if rng.random() < 0.35:
            pts.append([round(x - rng.uniform(4, 16)), round(198 + rng.uniform(-6, 6)), 1])
        x -= rng.uniform(26, 44)
    LF['f4_fire'] = pts
    return pts


def wide_flame_sheet(n=8, fw=64, fh=72, seed=13):
    """A broad fire mass: three overlapping licking flames of different heights in one sheet."""
    a = Q.flame_sheet(n, 36, 72, seed=seed)
    b = Q.flame_sheet(n, 30, 56, seed=seed + 1)
    c = Q.flame_sheet(n, 28, 44, seed=seed + 2)
    out = np.zeros((fh, fw * n, 4), np.uint8)
    for i in range(n):
        fr = np.zeros((fh, fw, 4), np.uint8)
        for sh_, ox, j in ((c, 2, (i + 3) % n), (b, 30, (i + 5) % n), (a, 14, i)):
            fw2 = sh_.shape[1] // n
            src = sh_[:, j * fw2:(j + 1) * fw2]
            Q.blit(fr, src, ox, fh - src.shape[0])
        out[:, i * fw:(i + 1) * fw] = fr
    return out


def fire_sheets():
    return Q.flame_sheet(8, 26, 44, seed=3), Q.flame_sheet(8, 18, 30, seed=7), Q.flame_sheet(8, 44, 84, seed=11)


# =========================================================================================== LS_C3_Escape
CH = {'vpx': 320.0, 'vpy': 110.0, 'f': 280.0, 'half': 0.42}
CH_TOP = 5.0                          # distance of the hatch (m)


def e1_bg():
    """Up the coal chute: four brick walls converging to the square of snow light (the hatch, ajar)."""
    R = C.ramps(B=BRICK, X=SOOT, I=IRON, S=SNOW, N=NIGHT)
    p = C.Paint(VW, VH, R, 'e1')
    yy, xx = p.yy, p.xx
    vx, vy, f, hlf = CH['vpx'], CH['vpy'], CH['f'], CH['half']
    dx = xx + 0.5 - vx
    dy = yy + 0.5 - vy
    lit = Q.lightfield(VW, VH, [(vx, vy, 260, 1.0, 1.6)])
    # which wall: the one whose plane is hit first (|dx| vs |dy| in normalised units)
    ax = np.abs(dx)
    ay = np.abs(dy)
    vert = ax >= ay
    Z = np.where(vert, f * hlf / np.maximum(ax, 0.5), f * hlf / np.maximum(ay, 0.5))
    U = np.where(vert, dy * Z / f, dx * Z / f)                    # coordinate along the wall (m)
    inside = Z < CH_TOP
    # brick courses in wall space
    row = np.floor(Z / 0.075)
    off = np.where(np.mod(row, 2) == 0, 0, 0.11)
    col = np.floor((U + 1.0 + off) / 0.22)
    hsh = np.mod(np.sin(row * 12.99 + col * 78.23 + vert * 3.0) * 43758.5, 1.0)
    joint = (np.mod(Z, 0.075) < 0.008 * (1 + Z * 0.2)) | (np.mod(U + 1.0 + off, 0.22) < 0.012 * (1 + Z * 0.2))
    t = 0.6 + (hsh - 0.5) * 0.8 + lit * 3.2
    floor = inside & ~vert & (dy > 0)
    p.put(inside & ~floor, 'B', t[inside & ~floor])
    p.put(inside & ~floor & joint, 'X', (t - 0.4)[inside & ~floor & joint])
    # the chute's floor: a scratched steel slide plate
    sl = np.mod(U * 9.0 + Z * 0.3, 1.0) < 0.12
    p.put(floor, 'I', 0.8 + lit[floor] * 3.4)
    p.put(floor & sl, 'I', 1.6 + lit[floor & sl] * 3.8)
    # coal dust and soot on the lower walls
    dust = inside & (Q.noise(VW, VH, 5, 971) > 0.70) & (dy > -20)
    p.put(dust, 'X', 0.6 + lit[dust] * 2.2)
    # the hatch square at the top: lid ajar -> a bright slit and a softer square
    s = f * hlf / CH_TOP
    sq = (np.abs(dx) < s) & (np.abs(dy) < s)
    p.put(sq, 'I', 1.0)
    slit = sq & (dy < -s + 5)
    p.put(slit, 'S', 8.0)
    p.put(sq & (dy >= -s + 5) & (dy < -s + 8), 'S', 5.0)
    p.resolve(band=2.0)
    LE['e1_hatch'] = [vx, vy, s]
    return p.L.c


def e1_light():
    a = np.zeros((VH, VW, 3), np.float32)
    vx, vy = CH['vpx'], CH['vpy']
    s = CH['f'] * CH['half'] / CH_TOP
    Q.add_glow(a, vx, vy - s + 3, 60, 22, (90, 100, 116), 1.4)
    Q.add_glow(a, vx, vy + 60, 120, 150, (26, 30, 38), 1.2)
    return K.soft_quant(a, 6.0)


def e1_file():
    """Konrad's sooty hands shoving the tied file up the slide (2 frames: grip, shove); 220 x 130, bottom-anchored."""
    w, h = 220, 130
    R = C.ramps(S=['#1E1414', '#3A2624', '#5A3C34', '#7A5446', '#9A6E58', '#B88A6C'], P=PAPER,
                C=['#1C140C', '#3A2A18', '#5E4426', '#806038', '#9E7C4C'], K=K_COAT, T=['#2A2418', '#5A4E36', '#8A7A58'],
                L=['#3A4859', '#687789', '#A1AAB7'])
    frames = []
    for fr in range(2):
        p = C.Paint(w, h, R, 'e1_file')
        yy, xx = p.yy, p.xx
        b = 0 if fr == 0 else -8
        folder = p.poly([(44, 46 + b), (176, 46 + b), (188, 88 + b), (32, 88 + b)])
        p.put(folder, 'C', 1.2 + (88 - yy[folder]) / 42.0 * 2.2)
        pages = p.poly([(50, 36 + b), (170, 36 + b), (176, 47 + b), (44, 47 + b)])
        p.put(pages, 'P', 3.0 + np.mod(yy[pages], 2) * 0.9)
        string = (p.line([(110, 36 + b), (112, 88 + b)], r=0.9) | p.line([(40, 66 + b), (184, 66 + b)], r=0.8)) & (folder | pages)
        p.put(string, 'T', 1.6)
        p.put((folder | pages) & C.rim(folder | pages, 0, -1, 2), 'L', 2.0)         # snow light from above
        for sx in (-1, 1):
            hx = 110 + sx * 62
            palm = p.ell(hx, 94 + b, 19, 14)
            fing = p.line([(hx - 12, 88 + b), (hx - 10 - 3 * sx, 72 + b)], r=4.2) | p.line([(hx - 3, 86 + b), (hx - sx, 70 + b)], r=4.2) |                 p.line([(hx + 6, 86 + b), (hx + 6 + 2 * sx, 72 + b)], r=4.0) | p.line([(hx + 14, 90 + b), (hx + 15 + 3 * sx, 78 + b)], r=3.6)
            hand = palm | fing
            p.put(hand, 'S', 1.4 + np.clip((96 - yy[hand]) / 20.0, 0, 1) * 2.4)
            p.put(hand & C.rim(hand, 0, -1), 'S', 4.4)
            sleeve = p.poly([(hx - 22, 104 + b), (hx + 22, 102 + b), (hx + 30 + sx * 8, h), (hx - 30 + sx * 8, h)])
            p.put(sleeve, 'K', 1.0)
            p.put(sleeve & C.rim(sleeve, 0, -1, 2), 'L', 1.0)
        p.resolve(band=2.0)
        frames.append(p.L.c)
    return Q.sheet(frames)


# ------------------------------------------------------------------------------------------- e2 yard
WALL_FOOT = 214
HATCH = dict(back=(250, 390, 218), front=(238, 402, 246), outer_back=(236, 404, 213), outer_front=(220, 420, 253))
YARD_LAMP = (486, 64)
YARD_R = dict(W=['#05070B', '#0A0D13', '#10151D', '#171E28', '#202935', '#2B3644', '#394656'], S=SNOW, L=LAMP, I=IRON,
              N=NIGHT, F=EMBERGLOW, X=SOOT)


def _yard_wall(p, lamp, glow, nz):
    """Rusticated stone of the east wing's base: big blocks, deep joints, a lit bevel on every course."""
    yy, xx = p.yy, p.xx
    wall = yy < WALL_FOOT
    row = np.floor(yy / 30)
    off = np.where(np.mod(row, 2) == 0, 0, 36)
    blk = np.mod(np.sin(row * 7.7 + np.floor((xx + off) / 72) * 3.1) * 917.3, 1.0)
    p.put(wall, 'W', 1.0 + blk[wall] * 0.6 + lamp[wall] * 3.0 + glow[wall] * 0.8 + nz[wall] * 0.4)
    joint = wall & ((np.mod(yy, 30) < 2) | (np.mod(xx + off, 72) < 2))
    p.put(joint, 'W', 0.2 + lamp[joint] * 1.2)
    bev = wall & (np.mod(yy, 30) == 2) & ~joint
    p.put(bev, 'W', 1.6 + lamp[bev] * 3.2)
    plinth = (yy >= WALL_FOOT - 14) & (yy < WALL_FOOT)
    p.put(plinth, 'W', 1.8 + lamp[plinth] * 2.6)
    p.put((yy >= WALL_FOOT - 15) & (yy < WALL_FOOT - 13), 'S', 5.4)
    return wall


def e2_bg():
    R = C.ramps(**YARD_R)
    p = C.Paint(VW, VH, R, 'e2')
    yy, xx = p.yy, p.xx
    nz = Q.noise(VW, VH, 14, 983)
    lamp = Q.lightfield(VW, VH, [(YARD_LAMP[0], YARD_LAMP[1] + 30, 300, 1.0, 1.5)])
    glow = Q.lightfield(VW, VH, [(320, 236, 150, 0.9, 1.3), (128, 178, 110, 0.7, 1.4)])
    _yard_wall(p, lamp, glow, nz)
    # one souterrain window left of the hatch: barred, deep orange inside, soot streaks above
    win = box(92, 148, 166, 196)
    p.put(win, 'F', 0.4 + Q.noise(VW, VH, 5, 985)[win] * 1.0 + (yy[win] - 148) / 48.0 * 1.0)
    p.put(win & (np.mod(xx, 12) < 2), 'I', 0.8)
    p.put(box(88, 196, 170, 200), 'W', 2.6)
    soot = (xx > 96) & (xx < 162) & (yy < 148) & (yy > 96)
    p.put(soot & (pg.bayer(VW, VH, 0, 0) < 0.55 - (148 - yy) / 110.0), 'X', 1.4)
    # bracket lamp
    lx, ly = YARD_LAMP
    p.put(p.line([(lx + 24, ly - 20), (lx + 24, ly - 6), (lx + 4, ly - 6)], r=1.4), 'I', 2.0)
    p.put(p.poly([(lx - 7, ly - 6), (lx + 7, ly - 6), (lx + 5, ly + 4), (lx - 5, ly + 4)]), 'I', 1.4)
    p.put(ell(lx, ly + 3, 4, 3), 'L', 6.4)
    # snow: lamp pool, drifts against the wall, the iron frame of the hatch in it
    g = yy >= WALL_FOOT
    u = (yy - WALL_FOOT) / (VH - WALL_FOOT)
    p.put(g, 'S', 3.0 + nz[g] * 1.0 + lamp[g] * 3.0 + u[g] * 1.4 + glow[g] * 0.6)
    drift = g & (yy < WALL_FOOT + 8) & (Q.noise(VW, VH, 9, 987) > 0.4)
    p.put(drift, 'S', 5.0 + lamp[drift] * 2.0)
    ob0, ob1, oby = HATCH['outer_back']
    of0, of1, ofy = HATCH['outer_front']
    frame = poly([(ob0, oby), (ob1, oby), (of1, ofy), (of0, ofy)])
    b0, b1, by_ = HATCH['back']
    f0, f1_, fy = HATCH['front']
    mouth = poly([(b0, by_), (b1, by_), (f1_, fy), (f0, fy)])
    p.put(frame & ~mouth, 'I', 1.4 + lamp[frame & ~mouth] * 2.6)
    p.put(frame & ~mouth & (yy >= ofy - 2), 'I', 3.2 + lamp[frame & ~mouth & (yy >= ofy - 2)] * 2.0)
    p.put(mouth, 'N', 0.2)
    deep = mouth & (yy > by_ + 8)
    p.put(deep, 'F', 0.6 + (yy[deep] - by_) / 40.0 * 1.4)
    p.resolve(band=2.0)
    LE['hatch'] = {k: list(v) for k, v in HATCH.items()}
    LE['yard_lamp'] = list(YARD_LAMP)
    return p.L.c


def e2_hatch():
    """3 frames of the iron lid (hinged at the wall): closed with snow on it, lifting (a hot slit), open (standing
    against the wall, the cast date)."""
    ox, oy, w, h = 214, 130, 212, 128
    R = C.ramps(I=IRON, S=SNOW, F=EMBERGLOW, N=NIGHT)
    b0, b1, by_ = HATCH['back']
    f0, f1_, fy = HATCH['front']
    frames = []
    for fr in range(3):
        p = C.Paint(w, h, R, 'hatch', ox=ox, oy=oy)
        yy, xx = p.yy, p.xx
        if fr == 0:
            lid = p.poly([(b0 - 2, by_ - 1), (b1 + 2, by_ - 1), (f1_ + 3, fy + 1), (f0 - 3, fy + 1)])
            p.put(lid, 'I', 1.8)
            p.put(lid & (np.mod(xx - b0, 24) < 2), 'I', 3.0)
            p.put(lid & (yy < fy - 6) & (Q.noise(w, h, 4, 988) > 0.42), 'S', 5.6)
            p.put(lid & (yy >= fy - 1), 'I', 3.6)
        elif fr == 1:
            lid = p.poly([(b0 - 2, by_), (b1 + 2, by_), (f1_ + 4, by_ - 22), (f0 - 4, by_ - 22)])
            slit = p.poly([(b0 + 2, by_ + 1), (b1 - 2, by_ + 1), (f1_ - 4, fy - 2), (f0 + 4, fy - 2)])
            p.put(slit, 'F', 2.2 + (yy[slit] - by_) / 20.0)
            p.put(lid, 'I', 1.6)
            p.put(lid & (yy < by_ - 18), 'I', 3.4)
            p.put(lid & (np.mod(xx - b0, 24) < 2), 'I', 2.6)
        else:
            lid = p.poly([(b0 - 2, by_ + 1), (b1 + 2, by_ + 1), (b1 + 4, by_ - 72), (b0 - 4, by_ - 72)])
            p.put(lid, 'I', 1.4)
            p.put(lid & (np.mod(xx - b0, 24) < 2), 'I', 2.4)
            p.put(lid & (yy < by_ - 69), 'I', 3.4)
            tm = np.repeat(np.repeat(K.vtext('1909', 'l', 1), 2, 0), 2, 1)
            sm = K.place(tm, w, h, (b0 + b1) // 2 - ox - tm.shape[1] // 2, by_ - 44 - oy)
            p.put(sm & lid, 'I', 4.4)
            p.put(lid & C.rim(lid, 1, 0, 2), 'I', 4.0)                             # the lamp catches its edge
        p.resolve(band=2.0)
        frames.append(p.L.c)
    LE['hatch_at'] = [ox, oy]
    return Q.sheet(frames)


KR = dict(K=K_COAT, A=['#020504', '#071009', '#0E1A14', '#16261D', '#20342A', '#2E4636'], U=A_FUR, H=K_HAT,
          Z=['#140C0C', '#2A1A18', '#46302A', '#6A4A3C', '#8A644E'], P=PAPER, F=EMBERGLOW, L=LAMP, S=SNOW)


def _shade_fig(p, sil, coat, parts, warm_dir=(0.8, -0.6), hot_dir=(-0.3, 1.0)):
    """Soot-dark figure: base tone, lamp rim (warm, from the upper right), fire rim from below (the mouth)."""
    p.put(sil, coat, 0.8)
    for nm, m in parts:
        if nm == 'hat':
            p.put(m, 'H' if coat == 'K' else 'U', 1.0)
        elif nm == 'skin':
            p.put(m, 'Z', 1.6)
        elif nm == 'file':
            p.put(m, 'P', 2.4)
            p.put(m & C.rim(m, 0, -1), 'P', 4.0)
    e = C.edge_light(sil, warm_dir, width=3.5, soft=1)
    sel = sil & (e > 0.3)
    p.put(sel, 'L', 1.2 + e[sel] * 2.6)
    e2 = C.edge_light(sil, hot_dir, width=2.5, soft=1)
    sel2 = sil & (e2 > 0.42) & ~sel
    p.put(sel2, 'F', 2.0 + e2[sel2] * 2.4)


def e2_konrad():
    """4 frames: hat, head and shoulders out of the mouth (the file thrust onto the snow), out to the waist with a
    knee on the rim, then on hands and knees in the snow beside the hatch (two steps).  Drawn at scale k about
    the mouth so he fills the opening (a man's shoulders ~ two thirds of the hatch width)."""
    x0, y0, w, h = 190, 70, 420, 220
    R = C.ramps(**KR)
    b0, b1, by_ = HATCH['back']
    f0, f1_, fy = HATCH['front']
    mx = (b0 + b1) / 2
    k = 1.55

    def P(pts, ax, ay):
        return [(ax + (x - ax) * k, ay + (y - ay) * k) for (x, y) in pts]

    frames = []
    for fr in range(4):
        p = C.Paint(w, h, R, 'e2k', ox=x0, oy=y0)
        parts = []
        if fr in (0, 1):
            up = 0 if fr == 0 else 16
            cx = mx - 4 + (6 if fr == 1 else 0)
            ax, ay = cx, fy
            parts.append(('body', p.poly(P([(cx - 26, fy - 2), (cx + 26, fy - 2), (cx + 24, fy - 22 - up), (cx + 10, fy - 30 - up),
                                             (cx - 12, fy - 30 - up), (cx - 24, fy - 20 - up)], ax, ay))))
            parts.append(('collar', p.poly(P([(cx - 12, fy - 28 - up), (cx + 12, fy - 28 - up), (cx + 8, fy - 36 - up),
                                               (cx - 8, fy - 36 - up)], ax, ay))))
            hx, hy = ax + 3 * k, ay - (40 + up) * k
            parts.append(('skin', p.ell(hx, hy, 7.5 * k, 8.5 * k)))
            parts.append(('hat', p.ell(hx, hy - 6 * k, 14 * k, 3.6 * k) | p.rr(hx - 9 * k, hy - 17 * k, hx + 9 * k, hy - 5 * k, 3 * k)))
            parts.append(('arm', p.line(P([(cx + 18, fy - 24 - up), (cx + 38, fy - 12 - up * 0.4), (cx + 54, fy + 2)], ax, ay), r=4.6 * k)))
            parts.append(('file', p.poly(P([(cx + 46, fy - 5), (cx + 76, fy - 8), (cx + 79, fy + 4), (cx + 48, fy + 6)], ax, ay))))
            if fr == 1:
                parts.append(('leg', p.line(P([(cx - 18, fy - 6), (cx - 30, fy + 2), (cx - 27, fy + 6)], ax, ay), r=5.6 * k)))
        else:
            s_ = 0 if fr == 2 else 5
            gx = b1 + 50 + (0 if fr == 2 else 14)
            gy = fy + 8
            ax, ay = gx, gy
            parts.append(('body', p.poly(P([(gx - 36, gy - 28), (gx + 20, gy - 36), (gx + 27, gy - 21), (gx - 33, gy - 13)], ax, ay))))
            parts.append(('skirt', p.poly(P([(gx - 38, gy - 26), (gx - 24, gy - 28), (gx - 20, gy - 8), (gx - 42, gy - 6)], ax, ay))))
            parts.append(('collar', p.ell(gx + 22 * k, gy - 33 * k, 9 * k, 6 * k)))
            hx, hy = gx + 33 * k, gy - 33 * k
            parts.append(('skin', p.ell(hx, hy, 7 * k, 7.5 * k)))
            parts.append(('hat', p.ell(hx + 1 * k, hy - 5.5 * k, 12 * k, 3.4 * k) | p.rr(hx - 7 * k, hy - 15 * k, hx + 9 * k, hy - 5 * k, 3 * k)))
            parts.append(('arm', p.line(P([(gx + 18, gy - 30), (gx + 24 + s_, gy - 14), (gx + 27 + s_, gy)], ax, ay), r=3.8 * k)))
            parts.append(('arm2', p.line(P([(gx + 7, gy - 28), (gx + 11 - s_, gy - 12), (gx + 10 - s_, gy)], ax, ay), r=3.4 * k)))
            parts.append(('leg', p.line(P([(gx - 30, gy - 16), (gx - 20 + s_, gy - 2), (gx - 44 + s_, gy)], ax, ay), r=5.4 * k)))
            parts.append(('leg2', p.line(P([(gx - 33, gy - 18), (gx - 28 - s_, gy - 1), (gx - 52 - s_, gy)], ax, ay), r=5.0 * k)))
            parts.append(('file', p.poly(P([(gx - 6, gy - 33), (gx + 18, gy - 38), (gx + 20, gy - 30), (gx - 4, gy - 25)], ax, ay))))
        sil = np.zeros((h, w), bool)
        for _, m in parts:
            sil |= m
        _shade_fig(p, sil, 'K', parts)
        p.resolve(band=2.0)
        frames.append(p.L.c)
    LE['e2_konrad'] = [x0, y0]
    return Q.sheet(frames)


def e3a_bg():
    """Looking down into the open hatch from its front rim: smoke-filled dark, the glow deep below, the iron
    rim with snow at the edges, the cast date on the frame."""
    R = C.ramps(I=IRON, S=SNOW, N=NIGHT, F=EMBERGLOW, X=SOOT)
    p = C.Paint(VW, VH, R, 'e3a')
    yy, xx = p.yy, p.xx
    nz = Q.noise(VW, VH, 12, 991)
    lamp = Q.lightfield(VW, VH, [(600, 0, 520, 1.0, 1.3)])
    p.put(np.ones((VH, VW), bool), 'S', 3.0 + nz * 1.4 + lamp * 2.4)
    rim_ = poly([(70, 360), (570, 360), (560, 40), (80, 40)])
    hole = poly([(118, 330), (522, 330), (512, 64), (128, 64)])
    p.put(rim_, 'I', 1.6 + lamp[rim_] * 2.6)
    p.put(rim_ & (np.mod(xx + yy * 0.2, 22) < 2), 'I', 0.8)
    p.put(rim_ & C.rim(rim_, 0, -1, 3), 'S', 6.0)
    deep = Q.lightfield(VW, VH, [(320, 330, 260, 1.0, 1.3)])
    p.put(hole, 'X', 0.4 + deep[hole] * 2.4)
    p.put(hole & C.rim(hole, 0, -1, 4), 'N', 0.2)
    tm = np.repeat(np.repeat(K.vtext('1909', 'l', 2), 2, 0), 2, 1)
    sm = K.place(tm, VW, VH, 320 - tm.shape[1] // 2, 46)
    p.put(sm & rim_, 'I', 4.6)
    p.resolve(band=2.0)
    return p.L.c


def _hand(p, x, y, ang, s=1.0, spread=0.0, curl=0.0):
    """A big stylised hand: palm + four fingers + thumb, pointing along `ang` (degrees, 0 = up)."""
    a = math.radians(ang)
    ux, uy = math.sin(a), -math.cos(a)                 # finger direction
    vx, vy = -uy, ux                                   # across the hand
    m = p.ell(x, y, 15 * s, 15 * s)
    for i, off in enumerate((-9.0, -3.0, 3.0, 9.0)):
        fan = (i - 1.5) * spread
        bx, by = x + vx * off * s + ux * 10 * s, y + vy * off * s + uy * 10 * s
        L = (16 + (2 if 0 < i < 3 else 0)) * s * (1 - curl * 0.45)
        dx, dy = ux + vx * fan * 0.06, uy + vy * fan * 0.06
        m |= p.line([(bx, by), (bx + dx * L, by + dy * L)], r=3.4 * s)
    tb = (x - vx * 14 * s, y - vy * 14 * s)
    m |= p.line([tb, (tb[0] + (ux - vx * 0.8) * 13 * s, tb[1] + (uy - vy * 0.8) * 13 * s)], r=3.6 * s)
    return m


def e3a_hands():
    """0 Alexei's hand rises out of the smoke, 1 it reaches (fingers open), 2 Konrad's hand from above takes it,
    3 both a little higher: he pulls."""
    x0, y0, w, h = 120, 0, 520, 360
    R = C.ramps(**KR)
    frames = []
    for fr in range(4):
        p = C.Paint(w, h, R, 'hands', ox=x0, oy=y0)
        up = (0, -10, -14, -58)[fr]
        ax, ay = 300, 188 + up
        sleeve = p.poly([(ax - 34, 360), (ax + 30, 360), (ax + 20, ay + 34), (ax - 22, ay + 36)])
        p.put(sleeve, 'A', 1.2)
        p.put(sleeve & (np.mod(p.yy + (p.xx - ax) * 0.15, 13) < 1.2), 'A', 0.4)
        p.put(sleeve & C.rim(sleeve, -1, 0, 2), 'L', 1.6)
        p.put(sleeve & C.rim(sleeve, 1, 0, 2), 'F', 2.6)
        cuff = p.rr(ax - 24, ay + 22, ax + 22, ay + 38, 4)
        p.put(cuff, 'A', 2.4)
        hand = _hand(p, ax, ay, -6, 1.15, spread=(2.0 if fr == 1 else 0.6), curl=(0.5 if fr >= 2 else 0.0))
        p.put(hand, 'Z', 1.8)
        p.put(hand & C.rim(hand, 1, -1, 2), 'Z', 3.6)
        p.put(hand & C.rim(hand, -1, 1), 'F', 3.0)
        if fr >= 2:
            kx, ky = ax + 10, ay - 2
            ksl = p.poly([(kx + 150, -10), (kx + 206, 14), (kx + 40, ky + 4), (kx + 16, ky - 22)])
            p.put(ksl, 'K', 1.4)
            folds = ksl & (np.mod((p.xx - kx) * 0.6 + (p.yy - ky), 26) < 2.5)
            p.put(folds, 'K', 0.6)
            p.put(ksl & C.rim(ksl, 0, -1, 3), 'L', 2.2)
            p.put(ksl & C.rim(ksl, -1, 1, 2), 'F', 2.0)
            kc = p.rr(kx + 14, ky - 26, kx + 40, ky - 4, 4)
            p.put(kc, 'P', 3.2)                                                       # his shirt cuff
            kh = _hand(p, kx, ky + 8, 200, 1.1, spread=0.3, curl=0.55)
            p.put(kh, 'Z', 2.2)
            p.put(kh & C.rim(kh, 1, -1, 2), 'Z', 4.0)
        p.resolve(band=2.0)
        frames.append(p.L.c)
    LE['e3_hands'] = [x0, y0]
    return Q.sheet(frames)


E3B_SNOW = 214


def e3b_bg():
    """Low at the snow beside the hatch: the wall foot with the hatch behind, the lamp, the snow field where they
    lie (the men are a sprite), the two dragged tracks from the hatch."""
    R = C.ramps(**YARD_R)
    p = C.Paint(VW, VH, R, 'e3b')
    yy, xx = p.yy, p.xx
    nz = Q.noise(VW, VH, 10, 995)
    lamp = Q.lightfield(VW, VH, [(560, 30, 380, 1.0, 1.4)])
    glow = Q.lightfield(VW, VH, [(250, 200, 120, 0.5, 1.4)])
    wall = yy < E3B_SNOW - 30
    row = np.floor(yy / 22)
    off = np.where(np.mod(row, 2) == 0, 0, 26)
    p.put(wall, 'W', 1.0 + lamp[wall] * 3.0 + glow[wall])
    jt = wall & ((np.mod(yy, 22) < 2) | (np.mod(xx + off, 52) < 2))
    p.put(jt, 'W', 0.3 + lamp[jt])
    pl = (yy >= E3B_SNOW - 30) & (yy < E3B_SNOW - 22)
    p.put(pl, 'W', 2.0 + lamp[pl] * 2.6)
    g = yy >= E3B_SNOW - 22
    u = (yy - (E3B_SNOW - 22)) / (VH - E3B_SNOW + 22)
    p.put(g, 'S', 2.6 + nz[g] * 1.2 + lamp[g] * 3.0 + u[g] * 1.8)
    fr = poly([(214, E3B_SNOW - 18), (334, E3B_SNOW - 18), (344, E3B_SNOW - 8), (204, E3B_SNOW - 8)])
    p.put(fr, 'I', 1.6 + lamp[fr] * 2.0)
    p.resolve(band=2.0)
    LE['e3b_hatch'] = [204, E3B_SNOW - 66]
    return p.L.c


def e3b_hatch():
    """2 frames: the lid open against the wall, the lid down (slammed)."""
    w, h = 144, 62
    R = C.ramps(I=IRON, S=SNOW, N=NIGHT)
    frames = []
    for fr in range(2):
        p = C.Paint(w, h, R, 'e3bh')
        if fr == 0:
            lid = p.poly([(18, 50), (126, 50), (124, 4), (20, 4)])
            p.put(p.poly([(12, 60), (132, 60), (126, 50), (18, 50)]), 'N', 0.3)
        else:
            lid = p.poly([(8, 61), (136, 61), (128, 49), (16, 49)])
        p.put(lid, 'I', 1.6)
        p.put(lid & C.rim(lid, 0, -1), 'I', 3.6)
        p.put(lid & (np.mod(p.xx, 22) < 2), 'I', 2.6)
        p.resolve(band=2.0)
        frames.append(p.L.c)
    return Q.sheet(frames)


def e3b_men():
    """Both on their backs in the snow, heads toward each other near the middle (Konrad left, Alexei right): soft
    silhouettes (a spine stroke with chest, hips, one knee up, an arm flung out), the lamp rim on top; 2 frames
    (chests heaving)."""
    x0, y0, w, h = 40, 220, 560, 96
    R = C.ramps(**KR)
    frames = []

    def man(p, side, b):
        sg = -1 if side == 'k' else 1                     # k lies to the left of his head, a to the right
        hx = 306 if side == 'k' else 346
        hy = 270
        X = lambda d: hx + sg * d                          # noqa: E731 - distance from the head along the body
        parts = []
        parts.append(('skin', p.ell(hx, hy, 8.5, 9.0)))
        if side == 'a':
            parts.append(('hat', p.ell(hx + 3, hy - 3, 12, 10)))
        torso = p.line([(X(12), hy + 4), (X(40), hy + 2 + b), (X(74), hy + 6), (X(104), hy + 10)], r=12.0)
        chest = p.ell(X(42), hy - 2 + b, 22, 10)
        leg1 = p.line([(X(104), hy + 12), (X(150), hy + 14), (X(196), hy + 14)], r=7.0)
        leg2 = p.line([(X(104), hy + 10), (X(140), hy - 14), (X(172), hy + 14)], r=6.6)
        arm = p.line([(X(30), hy - 4 + b), (X(14), hy - 26), (X(-6), hy - 34)], r=5.0) if side == 'a' else \
            p.line([(X(34), hy + 2 + b), (X(58), hy + 16), (X(84), hy + 20)], r=5.0)
        parts += [('body', torso | chest), ('legs', leg1 | leg2), ('arm', arm)]
        sil = np.zeros((p.h, p.w), bool)
        for _, m in parts:
            sil |= m
        return sil, parts

    for fr in range(2):
        p = C.Paint(w, h, R, 'e3bm', ox=x0, oy=y0)
        b = 0 if fr == 0 else -2
        sk, pk = man(p, 'k', b)
        sa, pa = man(p, 'a', b)
        _shade_fig(p, sk, 'K', pk, warm_dir=(0.5, -1.0), hot_dir=(0.0, 1.0))
        _shade_fig(p, sa, 'A', pa, warm_dir=(0.5, -1.0), hot_dir=(0.0, 1.0))
        # undo the fire rim from below: the hatch is shut, only the snow light remains
        for sil in (sk, sa):
            low = sil & ~C.shift(sil, 0, 1)
            p.put(low, 'K' if sil is sk else 'A', 0.6)
        hat_k = p.ell(326, 290, 13, 4.5) | p.rr(318, 280, 334, 290, 3)            # his hat, fallen in the snow
        p.put(hat_k, 'H', 1.4)
        p.put(hat_k & C.rim(hat_k, 1, -1), 'L', 2.2)
        fl = p.poly([(312, 296), (346, 293), (348, 302), (314, 304)])
        p.put(fl, 'P', 2.6)
        p.put(fl & C.rim(fl, 0, -1), 'P', 4.0)
        p.resolve(band=2.0)
        frames.append(p.L.c)
    LE['e3b_men'] = [x0, y0]
    LE['e3b_breath'] = [[306, 258], [346, 258]]
    return Q.sheet(frames)


def e4_bg():
    """The east wing from the lane: a three-storey neo-baroque front (rusticated base with six barred souterrain
    windows, pilasters, pedimented windows, the snowy cornice, mansard and chimneys), one lit window high up, the
    yard gate at the left, the snowy lane in front."""
    R = C.ramps(W=['#05070C', '#0A0E15', '#10161F', '#171F2A', '#202A36', '#2A3644', '#364454'], S=SNOW, N=NIGHT,
                I=IRON, L=LAMP, F=EMBERGLOW, X=SOOT)
    p = C.Paint(VW, VH, R, 'e4')
    yy, xx = p.yy, p.xx
    nz = Q.noise(VW, VH, 16, 999)
    sky = yy < 84
    p.put(sky, 'N', 1.6 + nz[sky] * 1.2 + np.clip((yy[sky] - 30) / 54.0, 0, 1) * 1.4)
    glow = Q.lightfield(VW, VH, [(320, 250, 420, 0.6, 1.2)])
    roof = (yy >= 58) & (yy < 84) & (np.abs(xx - 320) < 360)
    p.put(roof, 'W', 0.5 + (yy[roof] - 58) / 26.0 * 0.8)
    p.put((yy >= 56) & (yy < 60), 'S', 5.0)
    for cx in (96, 300, 520):
        p.put(box(cx, 34, cx + 16, 62), 'W', 1.2)
        p.put(box(cx - 2, 32, cx + 18, 35), 'S', 5.0)
    for dx in range(40, 640, 92):
        p.put(box(dx + 6, 64, dx + 26, 80), 'W', 1.6)
        p.put(box(dx + 10, 68, dx + 22, 78), 'N', 1.0)
    wall = (yy >= 84) & (yy < 262)
    p.put(wall, 'W', 1.4 + nz[wall] * 0.6 + glow[wall] * 1.6)
    cor = (yy >= 84) & (yy < 94)
    p.put(cor, 'W', 3.6 + glow[cor])
    p.put((yy >= 80) & (yy < 84), 'S', 6.2)
    for px_ in range(0, 640, 92):
        pil = (xx >= px_ - 5) & (xx < px_ + 5) & (yy >= 94) & (yy < 196)
        p.put(pil, 'W', 2.4 + glow[pil] * 1.4)
        p.put(pil & (xx >= px_ + 3), 'W', 1.4)
    for i, wx in enumerate(range(28, 640, 92)):
        for j, (wy0, wy1) in enumerate(((104, 142), (154, 188))):
            w_ = box(wx, wy0, wx + 36, wy1)
            lit = (i == 4 and j == 0)
            p.put(w_, 'L' if lit else 'N', (3.4 - (yy[w_] - wy0) / 30.0) if lit else 1.0 + nz[w_] * 0.8)
            p.put(w_ & (np.abs(xx - wx - 18) < 1), 'W', 1.6)
            p.put(box(wx - 3, wy0 - 4, wx + 39, wy0), 'W', 3.0)
            if j == 0:
                ped = poly([(wx - 4, wy0 - 4), (wx + 18, wy0 - 12), (wx + 40, wy0 - 4)])
                p.put(ped, 'W', 3.2)
                p.put(ped & C.rim(ped, 0, -1), 'S', 5.4)
            p.put(box(wx - 3, wy1, wx + 39, wy1 + 3), 'S', 5.2)
    base = (yy >= 196) & (yy < 262)
    jb = base & (np.mod(yy - 196, 13) < 1.2)
    p.put(jb, 'W', 0.6 + glow[jb])
    p.put((yy >= 194) & (yy < 198), 'W', 3.4)
    souts = []
    for wx in range(28, 640, 92):
        w_ = box(wx + 2, 224, wx + 34, 252)
        p.put(w_, 'N', 0.6)
        p.put(w_ & (np.mod(xx, 8) < 2), 'I', 1.4)
        p.put(box(wx, 252, wx + 36, 255), 'S', 5.0)
        souts.append([wx + 2, 224])
    gate = (xx < 26) & (yy >= 150) & (yy < 262)
    p.put(gate & (np.mod(xx, 6) < 2), 'I', 1.4)
    g = yy >= 262
    u = (yy - 262) / 98.0
    p.put(g, 'S', 2.6 + nz[g] * 1.2 + u[g] * 1.6 + glow[g] * 1.6)
    ruts = g & ((np.abs(yy - 282 - (xx - 320) * 0.02) < 1.5) | (np.abs(yy - 298 + (xx - 320) * 0.015) < 1.5))
    p.put(ruts, 'S', 1.8 + glow[ruts])
    p.resolve(band=2.0)
    LE['e4_windows'] = souts
    return p.L.c


def e4_window():
    """3 frames for one souterrain window: dark, the burst (a hot flash), burning."""
    w, h = 32, 28
    out = np.zeros((h, w * 3, 4), np.uint8)
    yy, xx = grid(h, w)
    for i in range(3):
        a = np.zeros((h, w, 3), np.float32)
        if i == 1:
            a[:] = np.array([246, 170, 80], np.float32) * (1 - yy / h * 0.35)[..., None]
        elif i == 2:
            nzv = Q.noise(w, h, 5, 1011)
            a[:] = (np.array([200, 92, 32], np.float32)[None, None] * (0.5 + 0.5 * nzv[..., None]) *
                    (0.55 + 0.45 * (yy / h))[..., None])
        if i > 0:
            a[np.mod(xx, 8) < 2] *= 0.22
        fr = Q.requant(a, ['#000000'] + EMBERGLOW, spread=16.0)
        fr[..., 3] = 255
        out[:, i * w:(i + 1) * w] = fr
    return out


def e4_glow():
    blobs = [(x + 16, 240, 60, 40, (64, 28, 8), 1.4) for (x, _) in LE.get('e4_windows', [])]
    return Q.glow_sprite(VW, VH, blobs, 6.0)


# =========================================================================================== build
def _preview_fire():
    LF['preview'] = [
        {'id': 'f1', 'layers': [['fire/f1_bg.png', [0, 0]], ['fire/lamp_cone.png', [0, 0], 'add'],
                                ['fire/f1_konrad.png', LF['f1_konrad'], 'over', 2, 1]]},
        {'id': 'f2', 'layers': [['fire/f2_bg.png', [0, 0]], ['fire/f2_glow.png', [0, 0], 'add'],
                                ['fire/f2_door.png', LF['f2_door_at'], 'over', 4, 0]] +
            [['fire/flame_s.png', [int(x) - 9, int(y) - 30], 'over', 8, i] for i, (x, y) in enumerate(LF['f2_fire'][:3])]},
        {'id': 'f3', 'layers': [['fire/f3_bg.png', [0, 0]], ['fire/f3_warm.png', [0, 0], 'add']]},
        {'id': 'f4', 'layers': [['fire/f4_bg.png', [0, 0]], ['fire/f4_glow.png', [0, 0], 'add']] +
            [[('fire/flame.png', 'fire/flame_big.png', 'fire/flame_wide.png')[b], [int(x) - (13, 22, 32)[b], int(y) - (44, 84, 72)[b]],
              'over', 8, (i * 3) % 8] for i, (x, y, b) in enumerate(LF['f4_fire'])] +
            [['fire/f4_alexei.png', LF['f4_alexei'], 'over', 2, 0]]},
    ]


def build_fire(w):
    w('fire/f1_bg.png', f1_bg())
    w('fire/lamp_cone.png', lamp_cone())
    import env_c3p2_cine_figs as F
    w('fire/f1_konrad.png', F.reg_konrad_sheet())
    LF['f1_konrad'] = list(F.REG_K_AT)
    w('fire/f2_bg.png', f2_bg())
    w('fire/f2_door.png', f2_door())
    w('fire/f2_glow.png', fire_glow(436, 176, 160, 110))
    w('fire/f3_bg.png', f3_bg())
    w('fire/f3_warm.png', Q.glow_sprite(VW, VH, [(300, 360, 360, 200, (70, 30, 10), 1.3)], 6.0))
    w('fire/f4_bg.png', f4_bg())
    w('fire/f4_glow.png', Q.glow_sprite(VW, VH, [(420, 190, 330, 150, (90, 40, 12), 1.3),
                                                 (160, 200, 200, 120, (60, 26, 8), 1.3)], 6.0))
    w('fire/f4_alexei.png', f4_alexei())
    f4_anchors()
    mid, small, big = fire_sheets()
    w('fire/flame.png', mid)
    w('fire/flame_s.png', small)
    w('fire/flame_big.png', big)
    w('fire/flame_wide.png', wide_flame_sheet())
    w('fire/smoke.png', Q.smoke_sheet(8, 64, 48, seed=1021))
    w('fire/ember.png', Q.ember_sheet())
    LF['lamp'] = list(LAMP_G)
    LF['f2_proj'] = dict(F2)
    _preview_fire()


def _preview_escape():
    LE['preview'] = [
        {'id': 'e1', 'layers': [['escape/e1_bg.png', [0, 0]], ['escape/e1_light.png', [0, 0], 'add'],
                                ['escape/e1_file.png', [210, 200], 'over', 2, 0]]},
        {'id': 'e2', 'layers': [['escape/e2_bg.png', [0, 0]], ['escape/e2_lamp.png', [0, 0], 'add'],
                                ['escape/e2_hatch.png', LE['hatch_at'], 'over', 3, 2],
                                ['escape/e2_konrad.png', LE['e2_konrad'], 'over', 4, 1]]},
        {'id': 'e2b', 'layers': [['escape/e2_bg.png', [0, 0]], ['escape/e2_lamp.png', [0, 0], 'add'],
                                 ['escape/e2_hatch.png', LE['hatch_at'], 'over', 3, 2],
                                 ['escape/e2_konrad.png', LE['e2_konrad'], 'over', 4, 3]]},
        {'id': 'e3a', 'layers': [['escape/e3a_bg.png', [0, 0]], ['escape/e3a_glow.png', [0, 0], 'add'],
                                 ['escape/e3a_hands.png', LE['e3_hands'], 'over', 4, 3]]},
        {'id': 'e3b', 'layers': [['escape/e3b_bg.png', [0, 0]], ['escape/e3b_hatch.png', LE['e3b_hatch'], 'over', 2, 1],
                                 ['escape/e3b_men.png', LE['e3b_men'], 'over', 2, 0]]},
        {'id': 'e4', 'layers': [['escape/e4_bg.png', [0, 0]], ['escape/e4_glow.png', [0, 0], 'add']] +
            [['escape/e4_window.png', xy, 'over', 3, 2 if i < 4 else 0] for i, xy in enumerate(LE['e4_windows'])]},
    ]


def build_escape(w):
    w('escape/e1_bg.png', e1_bg())
    w('escape/e1_light.png', e1_light())
    w('escape/e1_file.png', e1_file())
    w('escape/e2_bg.png', e2_bg())
    w('escape/e2_hatch.png', e2_hatch())
    w('escape/e2_konrad.png', e2_konrad())
    w('escape/e2_lamp.png', Q.glow_sprite(VW, VH, [(YARD_LAMP[0], YARD_LAMP[1] + 4, 80, 60, (60, 46, 26), 1.5)], 6.0))
    w('escape/e3a_bg.png', e3a_bg())
    w('escape/e3a_hands.png', e3a_hands())
    w('escape/e3a_glow.png', Q.glow_sprite(VW, VH, [(320, 340, 230, 150, (110, 46, 12), 1.4),
                                                    (320, 360, 120, 60, (90, 50, 20), 1.2)], 6.0))
    w('escape/e3b_bg.png', e3b_bg())
    w('escape/e3b_hatch.png', e3b_hatch())
    w('escape/e3b_men.png', e3b_men())
    w('escape/e4_bg.png', e4_bg())
    w('escape/e4_window.png', e4_window())
    w('escape/e4_glow.png', e4_glow())
    w('escape/smoke.png', Q.smoke_sheet(8, 64, 48, seed=1031, cols=['#2E2522', '#43352E', '#5C473B', '#78604E', '#957A62']))
    w('escape/breath.png', K.puff_sheet(6, 24, 18, ['#4F5E70', '#687789', '#A1AAB7'], 1041, grow=(0.2, 0.42), thin=0.7))
    _preview_escape()
