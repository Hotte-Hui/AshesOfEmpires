"""env_c4p2_cine_express -- LS_C4P2_Express (13 s): Karsk -> Berlin, Tuesday.  The decision is shown, never
explained.

  x1 side_on         platform 1, 20.10: close at the green sleeping car -- the route board, the riveted panels,
                     the cream band, the bogie; Ekdahl at his compartment window (his own dialogue bust, behind the
                     lace half-curtain, the drapes, the lamp on the window table, the frost on the glass) holds a
                     film canister up to the glass (publish_now) or shows his empty hand and nods (protect_first);
                     the next window glows through drawn curtains with a reader's shadow; the car pulls away left
  x2 fixed           the emptying platform at eye level, looking west: Alexei and Lev in the foreground (their
                     dialogue busts), between them the express's last car receding to the vanishing point with its
                     two red tail lamps; the platform lamps in perspective, the signal box, the band packing its
                     cases in the middle distance.  protect_first: Lev's carbons -- a white bundle in his hands --
                     go back under his coat; publish_now: Lev shows his empty hands
  x3 macro_locked    the tail lamp: the last car's end -- the gangway bellows, the end door, the buffers, the hook --
                     and the red lamp with its Fresnel rings, snow crossing it
  x4 tracking        Berlin, Kolonnenstraße 22.10: the red globe lamp of the building site of No. 12 (the same red
                     circle at the same place); Konrad's coat sweeps past the camera; the street -- the hoarding with
                     its posters, the scaffold, No. 14 with its lit windows, the coal merchant's shutter and the arched
                     gate passage; the camera follows Konrad into the passage; an S-Bahn crosses the viaduct behind
Painted flat (env_c4p2_cine_flat), busts from the dialogue portraits (env_c4p2_cine_busts), hands from the sprite
shader (env_c4p2_cine_hands), people on the game's rig.  Outputs assets/cinematics/c4p2/express/*.png; anchors in
layout.json "express".
"""
from __future__ import annotations

import math

import numpy as np

import env_c4p2_cine_busts as BU
import env_c4p2_cine_flat as FL
import env_c4p2_cine_hands as HD
import env_c4p2_cine_k14 as Z14
import env_c4p2_cine_kit as K
import env_c4p2_cine_people as PP
import env_c4p2_cine_rig as R

L = K.LAYOUT.setdefault('express', {})
LAMP_C = (320, 188)                      # the red lamp's centre in x3 AND x4a (the match cut)
LAMP_R = 46
CAR_W = 1180                             # the sleeping car's strip (scrolls left as the train starts)
WIN1 = (230, 92, 410, 214)               # Ekdahl's window in the strip (x0, y0, x1, y1)
WIN_STEP = 290
GLASS1 = (WIN1[0] + 6, WIN1[1] + 6, WIN1[2] - 6, WIN1[3] - 6)
TRAIN_T0 = 0.95                          # the brakes are off: the car starts to roll
TRAIN_A = 26.0                           # px/s^2
GESTURE_T = 0.6                          # Ekdahl lifts the canister / the empty hand
NOD_T = (1.55, 2.25)
VP = (262, 206)                          # x2: the vanishing point down the line (west), the horizon at eye level
TRACK_B = (-200, 90)                     # x2: the express's rails reach the frame's bottom (y 360) at these x
TRAIL_T = (4.0, 8.0)
TRAIL_N = 14
TRAIL_K = (0.3, 0.03)                    # the last car's end: perspective scale at the start / end of x2
CARBONS_T = (4.6, 6.4)                   # Lev's carbons go back under his coat (protect_first)
EMPTY_T = (4.5, 6.9)                     # publish_now: Lev shows his empty hands
X2_ALEXEI = (0, 146)                     # top-left of Alexei's silhouette cell (240 x 214), left foreground
X2_LEV = (330, 152)                      # top-left of Lev's cell (160 x 184): bust, coat, hands
STREET_W = 1100
X4_LAMP = (610, 226)                     # the warning lamp on its post at the barrier (wide shot)
GATE = (700, 800)                        # the gate passage of No. 14 (x0, x1)
X4_KONRAD = (586, 730)                   # Konrad's feet x from the wipe on (the in-game speed): into the passage
X4_FEET = 300
SBAHN_T = (10.9, 12.6)
GREEN = ['#0a1410', '#102018', '#183022', '#22422e', '#2e563a', '#3e6e4a']
CREAM = ['#5a5038', '#8a7c5a', '#b4a47a', '#d2c296', '#e6d8ae', '#f6ecc8']


def _register_lev():
    """Lev's dialogue portrait spec (characters_c4.PORTRAITS_C4) into the portrait cast, read-only."""
    import characters_c4 as C4
    if 'lev' not in BU.PR.C.CAST:
        BU.PR.C.CAST['lev'] = C4.PORTRAITS_C4['lev']


# ================================================================================================= x1
def _rivet_row(F, x0, x1, y, step, hi, lo):
    for x in range(int(x0), int(x1), step):
        F.fill(F.box(x, y, x + 1, y + 1), hi)
        F.fill(F.box(x + 1, y + 1, x + 2, y + 2), lo)


def car_strip():
    """The sleeping car's side, CAR_W wide (transparent above the roof): roof with snow, the route board, the
    panels, three compartment windows (the first is Ekdahl's: its contents are his sprite), the cream band with
    the car's name, the skirt, the bogie behind the platform's edge."""
    W = CAR_W
    F = FL.Flat(W, 360, bg='#000000')
    body = F.box(20, 50, W, 300)
    F.fill(body, GREEN[3])
    # roof and gutter
    roof = F.box(20, 30, W, 52)
    F.fill(roof, '#2a2e34')
    F.fill(F.box(20, 30, W, 34), '#dfe6ee')
    F.fill(F.box(20, 34, W, 36), '#9aa6b4')
    F.fill(F.box(20, 50, W, 53), '#1a1e22')
    F.fill(F.box(20, 53, W, 54), GREEN[5])
    # upper panel band with the route board on brackets
    F.fill(F.box(20, 54, W, 92), GREEN[2])
    for bx in (300, 880):
        board = F.box(bx, 60, bx + 190, 78)
        F.fill(board, '#e8e4d8')
        F.fill(board & FL.edge(board, 't'), '#ffffff')
        F.outline(board, col='#2a2a2a')
        txt = 'КАРСК - БЕРЛИН'
        tw = K.VK.vtext(txt, 'm').shape[1]
        F.fill(F.text(txt, bx + 95 - tw // 2, 65, 'm') & board, '#1a1a1a')
        for k in (12, 178):
            F.fill(F.box(bx + k - 2, 58, bx + k + 2, 80), '#3a3e44')
    # panel joints and rivets
    for x in range(40, W, 145):
        F.fill(F.box(x, 54, x + 1, 262), GREEN[1])
        F.fill(F.box(x + 1, 54, x + 2, 262), GREEN[4])
    _rivet_row(F, 24, W, 57, 7, GREEN[5], GREEN[0])
    _rivet_row(F, 24, W, 258, 7, GREEN[5], GREEN[0])
    # windows: 1 Ekdahl (glass left transparent for his sprite), 2 drawn curtains with a reader's shadow, 3 dark
    for k in range(3):
        x0 = WIN1[0] + k * WIN_STEP
        fr = F.box(x0 - 2, WIN1[1] - 2, x0 + 182, WIN1[3] + 4)
        F.fill(fr, '#8a8e94')
        F.fill(fr & FL.edge(fr, 't', 2), '#c8ccd2')
        F.fill(fr & FL.edge(fr, 'b', 2), '#4a4e54')
        gl = F.box(x0 + 6, WIN1[1] + 6, x0 + 174, WIN1[3] - 6)
        if k == 0:
            F.fill(gl, '#000000')
            F.a[gl] = False
        elif k == 1:
            F.fill(gl, '#7a2418')
            for j, x in enumerate(range(x0 + 6, x0 + 174, 6)):
                F.fill(gl & F.box(x, 0, x + 3, 360), '#5e1810' if j % 2 else '#922e1e')
            glow = gl & F.ell(x0 + 90, WIN1[1] + 62, 70, 50)
            F.mul(glow, 1.35)
            F.fill(gl & F.box(x0 + 84, WIN1[1] + 6, x0 + 96, WIN1[3] - 6), '#f0b860')
            # the reader's shadow on the curtain: head, shoulder, the newspaper held up
            sh = F.ell(x0 + 128, WIN1[1] + 54, 11, 13) | F.poly([(x0 + 104, WIN1[3] - 6), (x0 + 112, WIN1[1] + 70),
                                                                 (x0 + 146, WIN1[1] + 68), (x0 + 156, WIN1[3] - 6)])
            news = F.poly([(x0 + 132, WIN1[1] + 46), (x0 + 166, WIN1[1] + 40), (x0 + 170, WIN1[1] + 84),
                           (x0 + 136, WIN1[1] + 90)])
            F.mul((sh | news) & gl, 0.55)
        else:
            F.fill(gl, '#0c1014')
            F.fill(gl & F.box(0, WIN1[1] + 70, W, WIN1[3] - 6), '#141a20')
            F.fill(gl & F.line([(x0 + 20, WIN1[1] + 20), (x0 + 60, WIN1[1] + 6)], 1.0), '#3a4450')
            for j in range(3):
                lx = x0 + 30 + j * 50
                F.fill(gl & F.box(lx, WIN1[1] + 30 + j * 7, lx + 3, WIN1[1] + 32 + j * 7), '#d8a860')
        F.outline(fr, col='#1a1e22')
        # the window's little vent pane at the top
        F.fill(F.box(x0 + 6, WIN1[1] + 6, x0 + 174, WIN1[1] + 8) & ~F.box(-1, -1, 0, 0), '#8a8e94') if k else None
    # cream band with the car's name and number
    band = F.box(20, 222, W, 240)
    F.fill(band, CREAM[3])
    F.fill(band & FL.edge(band, 't'), CREAM[5])
    F.fill(band & FL.edge(band, 'b'), CREAM[1])
    for (txt, x) in (('СПАЛЬНЫЙ ВАГОН', 120), ('ПРЯМОГО СООБЩЕНИЯ', 520), ('07', 960)):
        F.fill(F.text(txt, x, 227, 'm') & band, '#2a2a20')
    # the end: vestibule door with its window and handrails, the step
    door = F.box(1080, 70, 1150, 262)
    F.fill(door, GREEN[2])
    F.outline(door, col=GREEN[0])
    dw = F.box(1094, 90, 1136, 150)
    F.fill(dw, '#0c1014')
    F.fill(dw & F.box(1094, 90, 1136, 96), '#2a3440')
    F.outline(dw, col='#8a8e94')
    for hx in (1072, 1156):
        F.fill(F.box(hx, 100, hx + 3, 250), '#a8acb2')
        F.fill(F.box(hx, 100, hx + 1, 250), '#e0e4ea')
    # skirt, battery box, the bogie behind the platform's edge
    F.fill(F.box(20, 262, W, 276), GREEN[1])
    F.fill(F.box(20, 262, W, 263), GREEN[4])
    F.fill(F.box(20, 276, W, 300), '#0c0e10')
    bb = F.box(520, 270, 640, 294)
    F.fill(bb, '#1a1c20')
    F.outline(bb, col='#050506')
    for bx in (110, 860):
        for wx in (0, 120):
            cx = bx + wx
            w_ = F.ell(cx, 292, 16, 16)
            F.fill(w_, '#202428')
            F.fill(w_ & ~F.ell(cx, 292, 13, 13), '#3a4048')
            F.fill(F.ell(cx, 292, 5, 5), '#4a525a')
            F.outline(w_, col='#050506')
        fr_ = F.box(bx - 20, 276, bx + 140, 286)
        F.fill(fr_, '#16191c')
        for k in range(4):
            F.fill(F.box(bx + 40, 278 + k * 2, bx + 80, 279 + k * 2), '#3a4048')
    # light: the platform lamps from above-left (stepped), the car's lower side in shadow
    F.pool(body, 300, 40, 900, 210, steps=((1.0, 1.0), (0.6, 1.1), (0.3, 1.2)), col='#ffd8a0')
    F.mul(F.box(20, 240, W, 300) & F.a, 0.82)
    F.outline(F.a.copy(), col='#050608', sides='lr')
    return F.rgba()


def ekdahl_frames():
    """Ekdahl's window contents (GLASS1, 168 x 110): the compartment behind him (panelling, the folded upper
    berth, his hat on the hook, the net with his suitcase, the lamp on the window table) and his bust; f 0 hands
    down, 1 the film canister held up to the glass, 2 the open empty hand, 3 the empty hand and a nod."""
    w, h = GLASS1[2] - GLASS1[0], GLASS1[3] - GLASS1[1]
    bg = FL.Flat(w, h, bg='#3a2416')
    F = bg
    F.fill(F.box(0, 0, w, h), '#4a2e1c')
    for x in range(0, w, 14):
        F.fill(F.box(x, 0, x + 1, h), '#341e12')
        F.fill(F.box(x + 1, 0, x + 2, h), '#5e3c26')
    F.fill(F.box(0, 22, w, 30), '#2a1a10')
    F.fill(F.box(0, 22, w, 23), '#7a5038')
    net = F.box(6, 4, 70, 18)
    F.fill(net & (((F.xx + F.yy).astype(int) % 4) == 0), '#8a6a4a')
    case = F.box(14, 6, 52, 18)
    F.fill(case, '#5a3a22')
    F.fill(case & FL.edge(case, 't'), '#8a5a34')
    F.fill(F.box(30, 6, 36, 8), '#c8a050')
    F.outline(case, col='#1a0c06')
    hook = F.box(150, 34, 154, 38)
    F.fill(hook, '#c8a050')
    hat = F.ell(152, 46, 13, 5) | F.poly([(144, 46), (146, 36), (158, 36), (160, 46)])
    F.fill(hat, '#5a5650')
    F.fill(hat & F.box(0, 42, w, 44), '#2a2826')
    F.outline(hat, col='#1a1816')
    lamp_s = F.poly([(130, 76), (146, 76), (150, 90), (126, 90)])
    F.fill(F.box(136, 90, 140, 104), '#a87828')
    F.fill(lamp_s, '#f6d8a0')
    F.fill(lamp_s & F.box(0, 86, w, 90), '#fff4d0')
    F.outline(lamp_s, col='#8a6430')
    F.pool(F.box(0, 0, w, h), 138, 86, 90, 70, steps=((1.0, 1.15), (0.5, 1.35)), col='#ffc070')
    base = F.opaque()
    # round 11: Ekdahl as a whole figure (env_c4p2_cine_figs): his shoulders, his left arm up from below the
    # sill, the film can in his fist / the open hand at the glass, the nod
    import env_c4p2_cine_figs as FG
    return FG.ekdahl_cells(base)


def win_overlay():
    """Ekdahl's window over his sprite: the frame, the drapes, the lace half-curtain on its rod, frost creeping
    in from the corners, a reflection of the platform lamps on the glass."""
    F = FL.Flat(CAR_W, 360, bg='#000000')
    x0, y0, x1, y1 = WIN1
    gx0, gy0, gx1, gy1 = GLASS1
    glass = F.box(gx0, gy0, gx1, gy1)
    a = np.zeros((360, CAR_W), bool)
    for side in (0, 1):
        dx0 = gx0 if side == 0 else gx1 - 18
        dr = F.poly([(dx0, gy0), (dx0 + 18, gy0), (dx0 + (12 if side == 0 else 6), gy0 + 60),
                     (dx0 + 18, gy1), (dx0, gy1)]) & glass
        F.fill(dr, '#6a1a16')
        for k, x in enumerate(range(int(dx0), int(dx0) + 18, 4)):
            F.fill(dr & F.box(x, 0, x + 2, 360), '#8e2a20' if k % 2 else '#4a0e0c')
        F.outline(dr, col='#2a0806', sides='lr')
        a |= dr
    rod = F.box(gx0, gy0 + 76, gx1, gy0 + 78)
    F.fill(rod, '#c8a050')
    a |= rod
    lace = glass & F.box(gx0 + 16, gy0 + 78, gx1 - 16, gy1)
    xx, yy = F.xx.astype(np.int64), F.yy.astype(np.int64)
    pat = ((np.mod(xx + yy, 4) == 0) & (np.mod(xx - yy, 8) < 4)) | ((np.mod(yy - gy0, 10) == 0) & (np.mod(xx, 2) == 0))
    scal = (yy > gy1 - 8) & (np.mod(xx, 8) < 5)
    lm = lace & (pat | scal | (yy < gy0 + 82))
    F.fill(lm, '#d8ccb0')
    F.fill(lm & (np.mod(xx, 12) < 6) & (yy > gy0 + 82), '#c4b494')
    F.fill(lm & (yy < gy0 + 82), '#ece2c8')
    a |= lm
    fern = glass & (((np.abs(np.sin((xx - gx0) * 0.7 + (yy - gy0) * 0.4)) > 0.82) &
                     (np.minimum(xx - gx0, yy - gy0) < 16 - 0.2 * np.maximum(xx - gx0, yy - gy0))) |
                    ((np.abs(np.sin((gx1 - xx) * 0.6 + (gy1 - yy) * 0.5)) > 0.84) &
                     (np.minimum(gx1 - xx, gy1 - yy) < 14 - 0.18 * np.maximum(gx1 - xx, gy1 - yy))))
    F.fill(fern & ~lm, '#d8e4ee')
    a |= fern
    refl = glass & F.line([(gx0 + 40, gy0 + 2), (gx0 + 26, gy0 + 40)], 1.2) & ~lm
    F.fill(refl, '#e8eef4')
    a |= refl
    return F.rgba(a)


def x1_platform():
    """Static foreground: the platform's edge stones with the white line and snow, a cast-iron lamp column at the
    right, a carnation someone dropped in the snow."""
    F = FL.Flat(bg='#000000')
    plat = F.box(0, 300, 640, 360)
    F.fill(plat, '#5a6070')
    F.fill(F.box(0, 300, 640, 304), '#9aa2b0')
    F.fill(F.box(0, 300, 640, 301), '#d0d6e0')
    F.fill(F.box(0, 306, 640, 308), '#e8e8e0')
    xx, yy = F.xx.astype(np.int64), F.yy.astype(np.int64)
    F.fill(plat & (yy > 308), '#4e5464')
    for k in range(9):
        x0_ = 20 + k * 74 + (k * 37) % 29
        dr = F.ell(x0_, 330 + (k % 3) * 8, 26 + (k * 13) % 20, 5)
        F.fill(dr & plat & (yy > 309), '#8a94a8')
        F.fill(dr & plat & FL.edge(dr, 't'), '#c8d0dc')
    for k in range(16):
        fx = 30 + (k * 41) % 600
        fy = 316 + (k * 17) % 30
        F.fill(F.box(fx, fy, fx + 4, fy + 2), '#3a3e4a')
    for x in range(0, 640, 40):
        F.fill(F.box(x, 301, x + 1, 306), '#6a7280')
    fl = F.ell(170, 314, 3, 2)
    F.fill(F.line([(160, 316), (170, 313)], 0.6), '#3a5a2a')
    F.fill(fl, '#c02a2a')
    F.fill(F.box(169, 312, 171, 313), '#e85a4a')
    col = F.box(586, 0, 596, 300)
    F.fill(col, '#1a1e24')
    F.fill(col & FL.edge(col, 'l', 2), '#4a525e')
    F.fill(col & FL.edge(col, 'r'), '#0a0c10')
    for y in (60, 140, 220):
        F.fill(F.box(582, y, 600, y + 4), '#2a3038')
    base_ = F.box(578, 280, 604, 300)
    F.fill(base_, '#22262c')
    F.fill(base_ & FL.edge(base_, 't'), '#dfe6ee')
    F.outline(base_ | col, col='#050608')
    F.pool(plat, 300, 300, 420, 60, steps=((1.0, 1.0), (0.6, 1.12), (0.3, 1.22)), col='#ffd8a0')
    return F.rgba()


# ================================================================================================= x2
def car_end(F, cx, base, s, lamps_only=False):
    """The last car's end at s px per metre, its bottom centre at (cx, base): body, gangway bellows, end door,
    buffers, the two red tail lamps; returns the mask."""
    def B(x0, y0, x1, y1):
        return F.box(cx + x0 * s, base - y1 * s, cx + x1 * s, base - y0 * s)
    body = B(-1.5, 0.55, 1.5, 4.1)
    roof = F.ell(cx, base - 4.05 * s, 1.5 * s, 0.35 * s) & (F.yy < base - 4.0 * s)
    m = body | roof
    if s >= 1.2:
        F.fill(m, GREEN[2])
        F.fill(roof, '#2a2e34')
        F.fill(roof & FL.edge(roof, 't'), '#dfe6ee')
        if s >= 4:
            bel = B(-0.55, 0.9, 0.55, 3.0)
            F.fill(bel, '#0c0c0e')
            for k in range(int(6)):
                F.fill(bel & B(-0.55 + k * 0.2, 0.9, -0.5 + k * 0.2, 3.0), '#24242a')
            dw = B(-0.25, 2.1, 0.25, 2.7)
            F.fill(dw, '#e0b060')
        F.fill(B(-1.5, 0.55, 1.5, 0.8), '#14161a')
        for sx_ in (-1.15, 1.15):
            bf = F.ell(cx + sx_ * s, base - 0.75 * s, max(1.0, 0.2 * s), max(1.0, 0.2 * s))
            F.fill(bf, '#6a7078')
        F.outline(m, col='#050608')
    else:
        F.fill(m, GREEN[1])
    for sx_ in (-1.05, 1.05):
        lm = F.ell(cx + sx_ * s, base - 1.25 * s, max(0.8, 0.14 * s), max(0.8, 0.14 * s))
        F.fill(lm, '#ff3a24')
        if s >= 3:
            F.fill(F.ell(cx + sx_ * s, base - 1.25 * s, max(0.6, 0.06 * s), max(0.6, 0.06 * s)), '#ffd0b0')
    return m


def x2_plate():
    """The platform at eye level looking west: the night sky with the town's glow, telegraph poles and the
    signal box along the line, the tracks converging, our platform at the right with its lamps in perspective;
    the band's cases on the platform (the bandsmen are sprites)."""
    F = FL.Flat(bg='#05070c')
    hz = VP[1]
    sky = F.box(0, 0, 640, hz)
    F.grad(sky, 0, hz, '#04060b', '#1c2438', steps=6)
    F.pool(sky, 316, hz, 260, 60, steps=((1.0, 1.25), (0.5, 1.5)), col='#5a4038')
    for (x0, x1, top) in ((0, 60, hz - 18), (52, 130, hz - 26), (140, 200, hz - 12), (430, 520, hz - 20),
                          (510, 600, hz - 30), (590, 640, hz - 14)):
        b = F.box(x0, top, x1, hz)
        F.fill(b, '#0c111c')
        for wy in range(top + 4, hz - 2, 6):
            for wx in range(x0 + 3, x1 - 2, 6):
                if K.hash2(wx, wy, 11) > 0.66:
                    F.fill(F.box(wx, wy, wx + 2, wy + 2), '#d89848')
    gnd = F.box(0, hz, 640, 360)
    F.fill(gnd, '#3a4250')
    xx, yy = F.xx, F.yy
    vx, vy = VP
    # ballast and the rails converging (the express's track and the next one)
    for (xl, xr) in ((TRACK_B[0], TRACK_B[1]), (-420, -140)):
        bed = F.poly([(vx - 2, vy), (vx + 2, vy), (xr + 30, 360), (xl - 30, 360)])
        F.fill(bed, '#2a2a30')
        for k in range(30):
            t = (k / 30.0) ** 2.2
            y = vy + (360 - vy) * t
            xa = vx + (xl - vx) * t
            xb = vx + (xr - vx) * t
            F.fill(F.box(xa - 2, y, xb + 2, y + max(1, int(3 * t))), '#4a3a2c')
        for xe in (xl, xr):
            F.fill(F.line([(vx, vy), (xe, 360)], 0.7), '#a8b0ba')
        F.fill(F.line([(vx, vy), (xr + 1, 360)], 0.4), '#e0e6ee')
    # our platform at the right: its surface, the edge, the lamps in perspective, the snow along the edge
    pl = F.poly([(vx + 6, vy), (640, vy - 2), (640, 360), (TRACK_B[1] + 40, 360)])
    F.fill(pl, '#4a5262')
    edge_ = F.line([(vx + 6, vy), (TRACK_B[1] + 40, 360)], 1.4)
    F.fill(edge_, '#e8e8e0')
    for k in range(14):
        t = (k / 14.0) ** 2
        y = vy + (360 - vy) * t
        x = vx + 6 + (TRACK_B[1] + 40 - vx - 6) * t
        F.fill(F.line([(x, y), (640, y + (360 - y) * 0.02)], 0.4) & pl, '#3a4252')
    ang_ = np.arctan2(yy - vy, xx - vx)
    streak = pl & (K.hash2(np.floor(ang_ * 90).astype(np.int64), np.floor_divide(yy.astype(np.int64), 7), 21) > 0.8)
    F.fill(streak, '#56607a')
    drift_ = pl & (np.abs((xx - vx) * (360 - vy) - (TRACK_B[1] + 40 - vx) * (yy - vy)) < 14 * (yy - vy + 4))
    F.fill(drift_, '#7a86a0')
    F.fill(drift_ & (K.hash2(xx.astype(np.int64), yy.astype(np.int64), 22) > 0.8), '#aab4c8')
    for k, t in enumerate((0.06, 0.14, 0.28, 0.5, 0.86)):
        x = vx + 30 + (640 - vx) * t * 1.3
        yb = vy + (360 - vy) * t * 0.9
        hpost = (40 + 260 * t)
        if x > 660:
            continue
        F.fill(F.box(x, yb - hpost, x + max(1, int(4 * t + 1)), yb), '#1a1e26')
        F.fill(F.box(x - 3 * t - 2, yb - hpost - 3, x + 4 * t + 3, yb - hpost + 1), '#2a2e36')
        F.fill(F.box(x - 2 * t - 1, yb - hpost + 1, x + 3 * t + 2, yb - hpost + 2 + 2 * t), '#fff0c0')
        F.pool(pl, x, yb, 30 + 120 * t, 6 + 26 * t, steps=((1.0, 1.15), (0.5, 1.3)), col='#ffd8a0')
    # the left side: the signal box with its lit window, telegraph poles
    sb = F.box(60, vy - 38, 104, vy + 6)
    F.fill(sb, '#3a2a22')
    F.fill(F.box(56, vy - 46, 108, vy - 38), '#1a1e24')
    F.fill(F.box(66, vy - 30, 98, vy - 16), '#e8a050')
    F.fill(F.box(81, vy - 30, 83, vy - 16), '#3a2a22')
    F.outline(sb, col='#0a0806')
    for k, t in enumerate((0.1, 0.22, 0.42, 0.72)):
        x = vx - 20 - (vx + 80) * t
        yb = vy + (360 - vy) * t * 0.6
        hpole = 30 + 220 * t
        F.fill(F.box(x, yb - hpole, x + 1 + int(3 * t), yb), '#14181e')
        F.fill(F.box(x - 6 - 10 * t, yb - hpole + 3, x + 7 + 10 * t, yb - hpole + 4 + int(2 * t)), '#14181e')
    for k in range(3):
        F.fill(F.line([(vx - 20, vy - 28 - k * 2), (-80, 60 + k * 8)], 0.4), '#2a3040')
    # the band's cases on the platform (middle distance, right)
    for (x, y, w_, h_, col) in ((508, 238, 16, 7, '#3a2a1c'), (556, 240, 10, 9, '#2a2a30'), (600, 236, 22, 6, '#4a3020')):
        c = F.box(x, y - h_, x + w_, y)
        F.fill(c, col)
        F.fill(c & FL.edge(c, 't'), '#8a7a5a')
        F.outline(c, col='#0a0806')
        F.mul(F.box(x - 2, y, x + w_ + 3, y + 2), 0.6)
    # round 11: the water tower by the line beyond the platform's end, the station's name board at the right,
    # footprints in the platform's snow walking in towards Lev
    wt = F.box(294, hz - 22, 310, hz)
    F.fill(wt, '#2a1c18')
    F.fill(wt & (np.mod(yy.astype(np.int64), 3) == 0), '#22161a')
    tank = F.box(291, hz - 36, 313, hz - 22)
    F.fill(tank, '#1a1e26')
    F.fill(tank & (np.mod(xx.astype(np.int64), 4) == 0), '#141820')
    F.fill(F.poly([(289, hz - 36), (315, hz - 36), (302, hz - 44)]), '#14181e')
    F.fill(F.line([(289, hz - 36.5), (302, hz - 44.5), (315, hz - 36.5)], 0.6), '#9aa6ba')
    F.fill(F.box(300, hz - 14, 304, hz - 8), '#d89848')
    for px_ in (606, 636):
        F.fill(F.box(px_, 188, px_ + 2, 300), '#1a1e26')
    nb = F.box(600, 176, 640, 192)
    F.fill(nb, '#1e3a5a')
    F.fill(F.text('КАРСК', 606, 181, 's') & nb, '#e8ecf0')
    F.fill(F.box(600, 175, 640, 177), '#dfe6ee')
    F.outline(nb, col='#0a1a2a', k=0.6)
    for k in range(12):
        u = k / 11.0
        fx_ = 628 - u * 150 + (k % 2) * (4 - 3 * u)
        fy_ = 330 - u * 96
        sz = 3.2 - 2.2 * u
        F.fill(F.ell(fx_, fy_, sz, sz * 0.45) & pl, '#3e4658')
    return F.opaque()


def trail_k(i):
    a, b = TRAIL_K
    return a * (b / a) ** (i / (TRAIL_N - 1))


def trail_frames():
    """The last car's end receding along the track to the vanishing point: TRAIL_N frames, each the end painted
    at its perspective scale (its bottom centre at the cell's bottom middle)."""
    cw, ch = 220, 260
    out = []
    for i in range(TRAIL_N):
        k = trail_k(i)
        s = 26.0 * 3.0 * k
        F = FL.Flat(cw, ch, bg='#000000')
        car_end(F, cw / 2.0, ch - 1, s)
        out.append(F.rgba())
    return K.hsheet(out), cw, ch


def alexei_silhouette():
    """Alexei from behind in the left foreground, against the platform lamps (round 11: a whole figure from
    env_c4p2_cine_figs instead of the flat silhouette) -- the ushanka, flaps tied up on the crown, the quilted jacket's
    raised collar, its channels across the back and round the arms, the lamps' amber on the rims.  8 frames:
    breathing (the shoulders rise a pixel)."""
    import env_c4p2_cine_figs as FG
    return FG.alexei_back_sheet()


def x2_people():
    """Alexei from behind (8 frames) and Lev (14 frames, facing the camera from the platform's edge -- round 11:
    a whole figure with arms and hands from env_c4p2_cine_figs) -- 0..7 publish_now: his empty hands rise,
    palms to us, and sink again; 8..13 protect_first: the white bundle of carbons in his hands is folded,
    pushed under his coat, the coat buttoned."""
    import env_c4p2_cine_figs as FG
    return alexei_silhouette(), FG.lev_sheet(), FG.LEV_CELL


def band_packing():
    """Two bandsmen in the middle distance packing up: one idles with his helicon over the shoulder, one with
    the drum; drawn on the rig (idle frames, 32 px cells)."""
    out = []
    for (cid, x, base, flip) in (('conductor', 540, 236, True), ('porter', 582, 238, True)):
        sh, n, w = PP.idle(cid, flip, key='left', mul=(0.96, 0.92, 0.86), rim=(255, 206, 140))
        x0, y0 = PP.cell_xy(x, base, 32)
        out.append((sh, x0, y0, n))
    return out


# ================================================================================================= x3 / x4a
def lamp_macro(kind):
    """The red lamp close, its lens centred on LAMP_C with radius LAMP_R (the shared circle of the match cut).
    tail: the last car's end -- the gangway bellows, the end door, a handrail, the buffers and the hook, snow on
    every ledge; barrier: the building site of No. 12 -- the red globe lamp in its wire cage on the striped
    barrier, the hoarding with a torn poster, the dark street behind."""
    F = FL.Flat(bg='#000000')
    cx, cy = LAMP_C
    r = LAMP_R
    xx, yy = F.xx.astype(np.int64), F.yy.astype(np.int64)
    if kind == 'tail':
        wall = F.box(0, 0, 640, 360)
        F.fill(wall, GREEN[2])
        for x in range(0, 640, 6):
            F.fill(F.box(x, 0, x + 1, 360), GREEN[1])
            F.fill(F.box(x + 1, 0, x + 2, 360), GREEN[3])
        bel = F.box(0, 0, 150, 360)
        F.fill(bel, '#121214')
        for k, x in enumerate(range(0, 150, 12)):
            F.fill(F.box(x, 0, x + 6, 360), '#222228')
            F.fill(F.box(x + 5, 0, x + 6, 360), '#3a3a44')
        F.outline(bel, col='#050506', sides='r')
        door = F.box(170, 0, 250, 360)
        F.fill(door, GREEN[1])
        F.outline(door, col=GREEN[0])
        dw = F.box(184, 40, 236, 120)
        F.fill(dw, '#0c1014')
        F.outline(dw, col='#8a8e94')
        F.fill(F.box(262, 0, 266, 360), '#a8acb2')
        F.fill(F.box(262, 0, 263, 360), '#e0e4ea')
        beam = F.box(0, 296, 640, 330)
        F.fill(beam, '#1a1c20')
        F.fill(beam & FL.edge(beam, 't', 3), '#dfe6ee')
        for bx in (120, 520):
            bf = F.ell(bx, 318, 34, 34)
            F.fill(bf, '#4a5058')
            F.fill(bf & ~F.ell(bx + 3, 321, 34, 34), '#8a929c')
            F.fill(F.ell(bx, 318, 12, 12), '#2a2e34')
            F.outline(bf, col='#050506')
            F.fill(bf & FL.edge(bf, 't', 2), '#dfe6ee')
        hook = F.box(306, 312, 334, 344)
        F.fill(hook, '#2a2e34')
        F.outline(hook, col='#050506')
        for k in range(14):
            ix = 20 + k * 44 + (k * 13) % 17
            ln = 6 + (k * 7) % 12
            F.fill(F.poly([(ix, 330), (ix + 4, 330), (ix + 2, 330 + ln)]), '#cfe0ee')
        snow_ = F.box(0, 0, 640, 360) & (K.hash2(xx, yy, 31) > 0.9975)
        F.fill(snow_, '#9aa8b8')
        # the lamp: hood, black housing ring with screws, the red lens with Fresnel rings and a hot centre
        hood = F.poly([(cx - r - 14, cy - r - 10), (cx + r + 14, cy - r - 10), (cx + r + 4, cy - r + 8),
                       (cx - r - 4, cy - r + 8)])
        F.fill(hood, '#16181c')
        F.fill(hood & FL.edge(hood, 't', 3), '#dfe6ee')
        F.outline(hood, col='#050506')
        house = F.ell(cx, cy, r + 12, r + 12)
        F.fill(house, '#1a1c20')
        F.fill(house & ~F.ell(cx + 2, cy + 2, r + 12, r + 12), '#4a5058')
        for k in range(6):
            a = k * math.pi / 3 + 0.3
            sx, sy = cx + math.cos(a) * (r + 7), cy + math.sin(a) * (r + 7)
            F.fill(F.ell(sx, sy, 2, 2), '#8a929c')
        F.outline(house, col='#050506')
    else:
        F.paste(Z14.lamp_backdrop(), 0, 0)               # round 11b: No. 14's corner and the far layer, in the haze
        hoard = F.box(0, 230, 640, 360)
        F.fill(hoard, '#3a2e24')
        pl = np.floor_divide(xx, 22)
        F.mul(hoard & (K.hash2(pl, 1, 771) > 0.6), 0.86)                # each plank its own weathering
        F.mul(hoard & (K.hash2(pl, 2, 771) > 0.82), 1.12)
        F.mul(hoard & (np.mod(xx * 3 + np.floor_divide(yy, 7) + pl * 5, 11) == 0), 0.88)        # the grain
        for k in range(9):                                                # knots
            kx, ky = 8 + int(K.hash2(k, 1, 772) * 620), 280 + int(K.hash2(k, 2, 772) * 70)
            F.fill(F.ell(kx, ky, 2.5, 1.6) & hoard, '#22180f')
        for k, x in enumerate(range(0, 640, 22)):
            F.fill(hoard & F.box(x, 230, x + 1, 360), '#22180f')
            F.fill(hoard & F.box(x + 1, 230, x + 2, 360), '#5a4632')
            F.fill(F.box(x + 6, 278, x + 7, 279) | F.box(x + 15, 278, x + 16, 279), '#8a8e94')   # nails in the rail
        F.fill(F.box(0, 276, 640, 277), '#22180f')                        # the rail behind the boards
        F.fill(F.box(0, 227, 640, 230) & (yy >= 227 + np.floor(K.hash2(np.floor_divide(xx, 4), 1, 773) * 3)), '#dfe6ee')
        F.fill(F.box(0, 230, 640, 231), '#9eaabf')                        # snow on the hoarding's top
        po = F.poly([(424, 282), (494, 280), (496, 326), (474, 334), (462, 322), (424, 330)])   # a torn notice
        F.fill(F.poly([(420, 286), (440, 284), (442, 318), (420, 320)]), '#4a5a6a')            # an older one under it
        F.fill(po, '#bfb69c')
        F.speckle(po, 0.08, None, seed=774, k=0.9)
        F.fill(po & F.box(424, 280, 500, 292), '#8a2a1e')
        F.fill(F.text('BEKANNTMACHUNG', 430, 284, 's') & po, '#e8e0cc')
        for k in range(6):
            F.fill(F.box(430, 298 + k * 4, 488 - (k * 9) % 17, 299 + k * 4) & po, '#4a4236')
        F.fill(F.poly([(474, 334), (462, 322), (480, 318)]), '#d8d0bc')     # the torn corner's flap
        F.outline(po, col='#6a604e', k=0.7)
        post = F.box(84, 240, 230, 340)
        F.fill(post, '#d8d0bc')
        F.fill(F.poly([(84, 240), (230, 240), (230, 270), (190, 300), (84, 262)]), '#c8b890')
        txt = 'BAUSTELLE'
        F.fill(F.text(txt, 100, 276, 'm') & post, '#2a2420')
        F.fill(F.text('BETRETEN VERBOTEN', 96, 292, 's') & post, '#7a1410')
        F.fill(F.poly([(196, 300), (230, 280), (230, 340), (204, 340)]), '#3a2e24')
        F.outline(post, col='#2a2018')
        bar = F.box(0, 252, 640, 272)
        F.fill(bar, '#e8e0d4')
        F.fill(bar & (np.mod(xx - yy, 40) < 20), '#b8241a')
        F.fill(bar & FL.edge(bar, 't', 2), '#dfe6ee')
        F.outline(bar, col='#1a0e0a')
        brk = F.box(cx - 5, cy + r, cx + 5, 252)
        F.fill(brk, '#1a1c20')
        F.fill(brk & FL.edge(brk, 'l'), '#4a5058')
        house = F.ell(cx, cy, r + 6, r + 6) & (F.yy > cy + r - 4)
        F.fill(house, '#1a1c20')
    # the lens (both kinds): red glass, Fresnel rings, the hot centre; a wire cage on the barrier lamp
    lens = F.ell(cx, cy, r, r)
    F.fill(lens, '#b8180e')
    dd = np.hypot(F.xx - cx, F.yy - cy)
    F.fill(lens & (np.mod(dd, 7.0) < 1.6), '#8a0e08')
    F.fill(lens & (np.mod(dd, 7.0) > 5.6), '#e8402a')
    F.fill(F.ell(cx - 4, cy - 4, r * 0.42, r * 0.42), '#ff5a3a')
    F.fill(F.ell(cx - 6, cy - 6, r * 0.2, r * 0.2), '#ffb08a')
    F.fill(F.ell(cx - 7, cy - 8, r * 0.08, r * 0.06), '#fff0e0')
    F.outline(lens, col='#3a0402')
    if kind == 'barrier':
        cage = lens & ((np.abs(F.xx - cx) < 1.0) | (np.abs(F.yy - cy) < 1.0) | (np.abs(dd - r * 0.62) < 0.8))
        F.fill(cage, '#14161a')
        F.fill(lens & FL.edge(lens, 't', 2) & (F.yy < cy - r * 0.8), '#dfe6ee')
    return F.opaque()


def lamp_glow(col=(150, 30, 16)):
    cx, cy = LAMP_C
    return K.glow_sprite(K.VW, K.VH, [(cx, cy, LAMP_R * 2.0, LAMP_R * 1.9, col, 1.7),
                                      (cx, cy, LAMP_R * 1.25, LAMP_R * 1.2, (90, 30, 18), 1.3)], 8.0)


def coat_wipe():
    """Konrad's coat passing close in front of the camera (left -> right): dark wool with a fold's lit ridge, the
    curved leading edge, a button and his scarf's fringe; 900 px wide so it covers the frame at mid-sweep."""
    w, h = 900, 360
    F = FL.Flat(w, h, bg='#000000')
    lead = 640 + 40 * np.sin(F.yy / 360 * math.pi)
    m = F.xx < lead
    F.fill(m, '#141828')
    for k, x0 in enumerate((180, 340, 470, 560)):
        ridge = m & (np.abs(F.xx - x0 - 30 * np.sin(F.yy / 90.0 + k)) < 6)
        F.fill(ridge, '#222840')
        F.fill(ridge & (np.abs(F.xx - x0 - 30 * np.sin(F.yy / 90.0 + k) + 4) < 1.5), '#3a4260')
    edge_ = m & (F.xx > lead - 10)
    F.fill(edge_, '#2a3048')
    F.fill(m & (F.xx > lead - 2), '#5a3a2a')
    bt = F.ell(lead.max() - 60, 210, 7, 7)
    F.fill(bt, '#2a2a30')
    F.fill(F.ell(lead.max() - 62, 208, 2, 2), '#6a6a72')
    fr = (F.xx > lead - 52) & (F.xx < lead - 30) & (F.yy > 40) & (F.yy < 150) & (np.mod(F.xx.astype(int), 3) == 0)
    F.fill(fr, '#7a3a2a')
    return F.rgba(m | fr)


# ================================================================================================= x4 street
def street_plate():
    """(far, front): Kolonnenstraße 14 by night, painted in env_c4p2_cine_k14 -- far = the sky, the roofs and the
    church clock, the S-Bahn viaduct (the train is a sprite on this layer; the layer pans at Z14.PARALLAX of the
    street), the gap site's snow beyond the hoarding; front = No. 12's gap site (hoarding with posters, the
    builders' hut, rubble, the barrier with its warning lamp at X4_LAMP, the Litfaßsäule) and No. 14 to scale
    (stucco relief, windows as rooms, the gate passage at GATE receding to the courtyard, the coal merchant, the
    corner pub), the gas lamp and the pavement under snow."""
    return Z14.street_far(STREET_W), Z14.street_front(STREET_W, X4_LAMP)


def street_glows():
    return Z14.street_glows(STREET_W, X4_LAMP)


def sbahn():
    """An S-Bahn train crossing the viaduct far behind: a dark strip of cars with lit windows (it slides)."""
    w, h = 220, 12
    F = FL.Flat(w, h, bg='#000000')
    car = F.box(0, 2, w, 11)
    F.fill(car, '#1a1c24')
    F.fill(F.box(0, 2, w, 3), '#3a3c48')
    for k in range(0, w - 6, 9):
        F.fill(F.box(k + 2, 4, k + 7, 8), '#ffd080')
    for k in range(0, w, 55):
        F.fill(F.box(k, 2, k + 1, 11), '#0a0a10')
    return F.rgba()


def konrad_walk():
    sh, n, w = PP.sheet('konrad', None, None, 32, False, key='right', mul=(0.86, 0.9, 1.06), rim=(150, 170, 220))
    return sh


def _konrad_poses():
    CH, CB, A, CC = K.rig()
    spec, used = K.spec_of('konrad')
    return A.walk_side(spec.style)


# ================================================================================================= build
def build(w):
    w('express/x1_car.png', car_strip())
    w('express/x1_frames.png', win_overlay())
    w('express/x1_ekdahl.png', K.hsheet(ekdahl_frames()))
    w('express/x1_platform.png', x1_platform())
    w('express/x2_bg.png', x2_plate())
    tr, tw, th = trail_frames()
    w('express/x2_trail.png', tr)
    al, lv, (lcw, lch) = x2_people()
    w('express/x2_alexei.png', al)
    w('express/x2_lev.png', lv)
    bp = band_packing()
    for k, (sh, x0, y0, n) in enumerate(bp):
        w('express/x2_band_%d.png' % k, sh)
    w('express/x3_lamp.png', lamp_macro('tail'))
    w('express/x4_lamp.png', lamp_macro('barrier'))
    w('express/lamp_glow.png', lamp_glow())
    w('express/coat.png', coat_wipe())
    far, front = street_plate()
    w('express/x4_far.png', far)
    w('express/x4_street.png', front)
    w('express/x4_glow.png', street_glows())
    w('express/x4_sbahn.png', sbahn())
    sh, n, cw = PP.sheet('konrad', _konrad_poses(), None, 32, False, key='right', mul=(0.86, 0.9, 1.06),
                         rim=(150, 170, 220))
    w('express/x4_konrad.png', sh)
    wk, wn, ww = Z14.walker_sheet()                       # the street's life (env_c4p2_cine_k14)
    w('express/x4_walker.png', wk)
    w('express/x4_smoke.png', Z14.smoke_sheet())
    won, wox, woy = Z14.win_on_sprite()
    w('express/x4_win_on.png', won)
    L.update(Z14.layout(), x4_win_on=[wox, woy], x4_walker_cell=[ww, wn])
    L.update(lamp_c=list(LAMP_C), lamp_r=LAMP_R, car_w=CAR_W, win1=list(WIN1), win_step=WIN_STEP,
             ekdahl_at=[GLASS1[0], GLASS1[1]], ekdahl_cell=[GLASS1[2] - GLASS1[0], GLASS1[3] - GLASS1[1]],
             train_t0=TRAIN_T0, train_a=TRAIN_A, gesture_t=GESTURE_T, nod_t=list(NOD_T),
             vp=list(VP), trail_t=list(TRAIL_T), trail_n=TRAIL_N, trail_cell=[tw, th], track_b=list(TRACK_B),
             trail_k=[round(trail_k(i), 4) for i in range(TRAIL_N)], x2_alexei=list(X2_ALEXEI), x2_alexei_cell=240,
             x2_lev=list(X2_LEV),
             x2_lev_cell=[lcw, lch], x2_band=[[x0, y0, n] for (sh, x0, y0, n) in bp],
             carbons_t=list(CARBONS_T), empty_t=list(EMPTY_T), street_w=STREET_W, x4_lamp=list(X4_LAMP),
             gate=list(GATE), x4_konrad=list(X4_KONRAD), x4_feet=X4_FEET, sbahn_t=list(SBAHN_T))
