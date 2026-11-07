"""env_c4p2_cine_clock -- LS_C4P2_Clock (24 s): Berlin, Kordon-17, Karsk at 23.40 Korridorzeit.

  k1 establishing  Berlin, 23.40: the courtyard of Kolonnenstraße 14 seen from above, the side wing square on: the
                   ground floor with the cobbler's workshop (its sign), the house door with its lit fanlight, the
                   plinth and the basement windows -- in the cobbler's a candle on the sill, lasts on the shelf, Ilse
                   asleep on leather offcuts under the cobbler's coat; the cobbled yard with snow, the bins, a
                   bicycle, the light well's grating; Wendt's black car rolls out to the left into the gate passage;
                   the camera then tilts up to the first floor: Hanna's window stays lit, neighbours watch
  k2 establishing  Kordon-17 wide and from far: the snow plain in bands, the forest line, the Line's fence and its
                   ploughed strip, two watch towers, the floodlight masts and their pools, the long low building on
                   the Line (the German hall west, Tür Ost east), the guard hut, a lorry, wagon C-17/45 on its
                   siding.  publish_now: a flashbulb at the fence, a man with a notebook, the door stays shut, two
                   figures are led back into the German hall; protect_first: Tür Ost opens, two figures cross its
                   light into the wagon, the door closes.  No faces, no force, nobody inside a wagon.
  k3 side_on       Karsk, 1.40: Irina's dispatch office -- Irina (her dialogue bust) at the teleprinter, the tape
                   typing the news in telegraph Russian across the desk in front of her; Alexei (his bust) outside at
                   the window, frost round him; the yard at night beyond, Lev's lamp in the freight office; the wall
                   clock with the second hand on the tick, the train graph, the green lamp, the telephone, tea
  k4 macro_locked  Irina's desk from above under the green lamp: the German half of card 0417 beside a film
                   canister (protect_first) or beside Lev's empty folder (publish_now); the ledger, the tape's end,
                   the tea glass, a pencil, the blotter
  k5 title         black
Painted flat (env_c4p2_cine_flat); people from the dialogue busts (env_c4p2_cine_busts).
Outputs assets/cinematics/c4p2/clock/*.png; anchors in layout.json "clock".
"""
from __future__ import annotations

import math

import numpy as np

import env_c4p2_cine_busts as BU
import env_c4p2_cine_flat as FL
import env_c4p2_cine_k14 as Z14
import env_c4p2_cine_kit as K
import env_c4p2_cine_kordon as KD
import env_c4p2_cine_pal as PAL
from env_c4p2_cine_kit import GB, Lt

L = K.LAYOUT.setdefault('clock', {})
PAL_K = PAL.KARSK

# ------------------------------------------------------------------------------------------------ k1 the courtyard
K1_H = 520                                                 # the plate's height (the camera tilts up over it)
K1_TILT = (3.3, 5.0, 160, 40)                              # (t0, t1, offset at t0, offset at t1)
GATE_K = (0, 64, 300, 470)                                 # the gate passage's mouth at the left (x0, x1, top, bottom)
CAR_PATH = ((560, 476), (-150, 476))                       # the car's bottom-centre: from its place out to the left
CAR_T = (0.9, 3.4)                                         # the car rolls from its place into the passage
CAR_DOORS = (0.3, 0.55)                                    # two doors shut (c4p2cine_k14)
ENGINE_T = 0.75
CANDLE = (318, 372)                                        # the candle in the cobbler's basement window (plate)
BASE_WIN = (300, 352, 440, 396)                            # the cobbler's basement window (plate)
HANNA = (430, 76, 464, 124)                                # Hanna's window, first floor of the side wing (plate)
Y = dict(eaves=18, cornice=164, gf_top=170, plinth=330, yard=400)


def _window(F, x0, y0, x1, y1, lit, kind=0, frame='#d8d4c8'):
    """A tall Berlin window: casement frame and mullion, sill with snow, lit (curtain, a figure, plants) or
    dark (a reflection)."""
    w = F.box(x0, y0, x1, y1)
    if lit:
        F.fill(w, '#e0984a')
        F.fill(w & F.box(x0, y0, x1, y0 + 5), '#f8d080')
        if kind == 1:
            F.fill(w & F.ell((x0 + x1) / 2 + 3, y1 - 12, 6, 10), '#3a2014')
            F.fill(w & F.ell((x0 + x1) / 2 + 3, y1 - 26, 4, 5), '#3a2014')
        elif kind == 2:
            F.fill(w & F.box(x0, y1 - 10, x1, y1), '#4a6a32')
            F.fill(w & F.ell(x0 + 8, y1 - 12, 5, 6), '#2e4a22')
        elif kind == 3:
            F.fill(w & (np.mod(F.xx.astype(int), 3) == 0), '#f0d8a8')
            F.fill(w & F.box(x0, y0, x0 + 6, y1), '#b06a2a')
            F.fill(w & F.box(x1 - 6, y0, x1, y1), '#b06a2a')
    else:
        F.fill(w, '#0e1424')
        F.fill(w & F.line([(x0 + 3, y1 - 6), (x0 + 12, y0 + 4)], 0.8), '#2a3450')
    m = F.box((x0 + x1) / 2 - 1, y0, (x0 + x1) / 2 + 1, y1) | F.box(x0, y0 + (y1 - y0) * 0.35,
                                                                       x1, y0 + (y1 - y0) * 0.35 + 2)
    F.fill(m, '#2a2c38' if not lit else '#5a3a1e')
    F.outline(w, col=frame)
    sill = F.box(x0 - 3, y1, x1 + 3, y1 + 3)
    F.fill(sill, '#5a5c6c')
    F.fill(sill & FL.edge(sill, 't'), '#e2e8f2')
    return w


def k1_plate():
    """The courtyard of No. 14 (640 x K1_H): the side wing's facade square on (first floor at the top, the ground
    floor, the plinth with the basement windows), the gate passage's mouth at the left, the yard below."""
    F = FL.Flat(640, K1_H, bg='#05070e')
    xx, yy = F.xx.astype(np.int64), F.yy.astype(np.int64)
    fac = F.box(64, 0, 640, Y['yard'])
    F.fill(fac, '#3a3e50')
    F.fill(fac & (np.mod(yy, 14) == 0), '#34384a')
    F.fill(fac & (K.hash2(np.floor_divide(xx, 18), np.floor_divide(yy, 14), 3) > 0.9), '#33364a')
    # eaves with snow, the cornice, the drainpipe
    F.fill(F.box(64, 0, 640, Y['eaves']), '#22242e')
    F.fill(F.box(64, Y['eaves'] - 4, 640, Y['eaves']), '#dfe6ee')
    cor = F.box(64, Y['cornice'], 640, Y['cornice'] + 6)
    F.fill(cor, '#4a4e60')
    F.fill(cor & FL.edge(cor, 't', 2), '#e2e8f2')
    F.fill(cor & FL.edge(cor, 'b'), '#22242e')
    dp = F.box(600, 0, 606, Y['yard'])
    F.fill(dp, '#2a2e3a')
    F.fill(dp & FL.edge(dp, 'l'), '#5a6070')
    for y in range(30, Y['yard'], 60):
        F.fill(F.box(598, y, 608, y + 3), '#22242e')
    # first floor: four windows -- Hanna's lit (her silhouette, the hair knot), a radio's glow, dark ones
    for k, x in enumerate((110, 230, 330, HANNA[0], 530)):
        lit = x in (HANNA[0], 230)
        _window(F, x, HANNA[1], x + (HANNA[2] - HANNA[0]), HANNA[3], lit, 3 if x == 230 else 0)
    hx0, hy0, hx1, hy1 = HANNA
    hw = F.ell((hx0 + hx1) / 2 - 3, hy1 - 16, 7, 12) | F.ell((hx0 + hx1) / 2 - 3, hy1 - 32, 5, 6) | \
        F.ell((hx0 + hx1) / 2 - 2, hy1 - 39, 3, 3)
    F.fill(hw & F.box(hx0, hy0, hx1, hy1), '#2a1610')
    F.fill(F.box(hx0 + 2, hy1 - 2, hx0 + 6, hy1), '#8a3a20')
    # ground floor: the cobbler's workshop window and sign, the house door with its fanlight, a lit kitchen
    sign = F.box(280, Y['gf_top'] + 8, 500, Y['gf_top'] + 22)
    F.fill(sign, '#2a2018')
    F.fill(F.text('SCHUHMACHEREI PIETSCH', 290, Y['gf_top'] + 12, 's') & sign, '#d8c890')
    F.outline(sign, col='#120c08')
    shop = F.box(290, Y['gf_top'] + 30, 490, Y['plinth'] - 14)
    F.fill(shop, '#0c101c')
    for k in range(5):
        sx = 300 + k * 38
        F.fill(F.box(sx, Y['plinth'] - 30, sx + 16, Y['plinth'] - 22), '#2a2018')
        F.fill(F.box(sx + 2, Y['plinth'] - 34, sx + 12, Y['plinth'] - 30), '#3a2a1e')
    F.fill(F.box(290, Y['plinth'] - 40, 490, Y['plinth'] - 38), '#3a3a44')
    F.fill(shop & F.line([(300, Y['plinth'] - 50), (330, Y['gf_top'] + 34)], 1.0), '#26304a')
    for x in (355, 425):
        F.fill(F.box(x, Y['gf_top'] + 30, x + 2, Y['plinth'] - 14), '#2a2c38')
    F.outline(shop, col='#d8d4c8')
    _window(F, 130, Y['gf_top'] + 34, 170, Y['plinth'] - 30, False)
    _window(F, 200, Y['gf_top'] + 34, 240, Y['plinth'] - 30, True, 1)
    door = F.box(530, Y['gf_top'] + 46, 570, Y['plinth'] + 30)
    F.fill(door, '#3a2418')
    F.fill(door & (np.mod(xx, 10) == 0), '#2a180f')
    fan = F.ell(550, Y['gf_top'] + 46, 20, 14) & (F.yy < Y['gf_top'] + 46)
    F.fill(fan, '#f0b860')
    F.fill(fan & (np.mod(xx - 550, 6) == 0), '#5a3a1e')
    F.outline(door | fan, col='#d8d4c8')
    st = F.box(522, Y['plinth'] + 30, 578, Y['plinth'] + 36)
    F.fill(st, '#4a4c58')
    F.fill(st & FL.edge(st, 't', 2), '#dfe6ee')
    # the plinth with its basement windows; the cobbler's: candle, lasts, leather offcuts, Ilse under the coat
    pl = F.box(64, Y['plinth'], 640, Y['yard'])
    F.fill(pl, '#2a2c38')
    F.fill(pl & (np.mod(yy - Y['plinth'], 12) == 0), '#22242e')
    F.fill(pl & (np.mod(xx + (np.floor_divide(yy - Y['plinth'], 12) % 2) * 14, 28) == 0), '#22242e')
    F.fill(F.box(64, Y['plinth'], 640, Y['plinth'] + 2), '#dfe6ee')
    for (x0, x1) in ((150, 206), (500, 556)):
        bw = F.box(x0, 356, x1, 390)
        F.fill(bw, '#07080e')
        F.fill(bw & (np.mod(xx, 7) == 0), '#2a2c38')
        F.outline(bw, col='#4a4c58')
    bx0, by0, bx1, by1 = BASE_WIN
    bw = F.box(bx0, by0, bx1, by1)
    F.fill(bw, '#3a1e0e')
    F.fill(bw & F.box(bx0, by0, bx1, by0 + 14), '#4a2810')
    for k in range(6):
        lx = bx0 + 34 + k * 16
        last = F.ell(lx, by0 + 8, 6, 3)
        F.fill(last, '#8a5a30')
        F.fill(last & (F.yy < by0 + 7), '#b07a40')
    F.fill(F.box(bx0, by0 + 12, bx1, by0 + 13), '#2a140a')
    offc = F.poly([(bx0 + 40, by1), (bx0 + 50, by1 - 12), (bx1 - 10, by1 - 14), (bx1, by1)])
    F.fill(offc, '#6a3a1e')
    for k in range(8):
        ox = bx0 + 48 + k * 11
        F.fill(F.poly([(ox, by1 - 10), (ox + 9, by1 - 13), (ox + 7, by1 - 7)]) & offc, ['#8a4a24', '#5a2e14', '#a05a2a'][k % 3])
    # Ilse asleep under the cobbler's coat (round 11: a figure of env_c4p2_cine_figs -- curled on her side, the
    # head on a rolled apron, plaits, the eye shut, a hand under the cheek, the knees drawn up, stockinged feet)
    import env_c4p2_cine_figs as FG
    FG.paint_into(F, FG.ilse_asleep(), bx0 + 58, by1 - 27)
    cx_, cy_ = CANDLE
    F.fill(F.box(cx_ - 2, cy_ + 2, cx_ + 2, cy_ + 12), '#f0e8d0')
    F.fill(F.box(cx_ - 4, cy_ + 11, cx_ + 4, cy_ + 13), '#8a8070')
    F.fill(F.ell(cx_, cy_ - 1, 2, 3), '#ffd060')
    F.fill(F.ell(cx_, cy_, 1, 1.5), '#fff8e0')
    F.pool(bw, cx_, cy_, 90, 40, steps=((1.0, 1.05), (0.6, 1.2), (0.3, 1.45)), col='#ffb050')
    F.fill(bw & F.box(bx0, by0, bx1, by0 + 3), '#c8d0dc')
    F.fill(F.box((bx0 + bx1) / 2 - 1, by0, (bx0 + bx1) / 2 + 1, by1), '#2a1a10')
    F.outline(bw, col='#5a5c68')
    # the yard: cobbles under snow, the light well's grating, the bins, a bicycle, tyre tracks
    yd = F.box(0, Y['yard'], 640, K1_H)
    F.fill(yd, '#566078')
    row_ = np.floor_divide(yy - Y['yard'], 6)
    cob = yd & ((np.mod(yy - Y['yard'], 6) == 0) | (np.mod(xx + (row_ % 2) * 5, 10) == 0))
    F.fill(cob & (K.hash2(np.floor_divide(xx, 10), row_, 41) > 0.55), '#3e4660')
    F.fill(yd & (K.hash2(np.floor_divide(xx, 12), row_, 42) > 0.72) & ~cob, '#7a86a4')
    for ty in (452, 494):
        F.fill(F.box(0, ty, 640, ty + 5) & yd, '#3a4258')
        F.fill(F.box(0, ty + 5, 640, ty + 6) & yd, '#8a96b4')
    gr = F.box(bx0 - 6, Y['yard'], bx1 + 6, Y['yard'] + 18)
    F.fill(gr, '#1a1c24')
    F.fill(gr & (np.mod(xx, 4) == 0), '#4a4e5c')
    F.fill(gr & FL.edge(gr, 'b'), '#dfe6ee')
    F.pool(gr, cx_, Y['yard'] + 6, 60, 14, steps=((1.0, 1.4),), col='#ffb050')
    for k, bx in enumerate((588, 614)):
        bin_ = F.box(bx - 12, Y['yard'] - 30, bx + 12, Y['yard'] + 8)
        F.fill(bin_, '#5a6070')
        for y in range(Y['yard'] - 26, Y['yard'] + 8, 6):
            F.fill(F.box(bx - 12, y, bx + 12, y + 1), '#3a3e48')
        lid = F.ell(bx, Y['yard'] - 30, 14, 4)
        F.fill(lid, '#6a7080')
        F.fill(lid & FL.edge(lid, 't', 2), '#dfe6ee')
        F.outline(bin_, col='#1a1c22')
    bk = (250, Y['yard'] + 6)
    for wx_ in (bk[0] - 18, bk[0] + 18):
        whl = F.ell(wx_, bk[1] - 10, 11, 11) & ~F.ell(wx_, bk[1] - 10, 9, 9)
        F.fill(whl, '#14161c')
        F.fill(F.line([(wx_ - 8, bk[1] - 10), (wx_ + 8, bk[1] - 10)], 0.4) | F.line([(wx_, bk[1] - 18), (wx_, bk[1] - 2)], 0.4),
               '#3a3e48')
    F.fill(F.line([(bk[0] - 18, bk[1] - 10), (bk[0] - 2, bk[1] - 28), (bk[0] + 18, bk[1] - 10)], 0.8) |
           F.line([(bk[0] - 2, bk[1] - 28), (bk[0] + 12, bk[1] - 28), (bk[0] + 18, bk[1] - 10)], 0.8) |
           F.line([(bk[0] - 2, bk[1] - 28), (bk[0] - 4, bk[1] - 34)], 0.8), '#5a1e18')
    F.fill(F.box(bk[0] - 8, bk[1] - 36, bk[0], bk[1] - 34) | F.box(bk[0] + 10, bk[1] - 32, bk[0] + 16, bk[1] - 30),
           '#1a1a1e')
    # the gate passage's mouth at the left: the front house's corner, the arch, its lamp inside
    fh = F.box(0, 0, 64, Y['yard'] + 10)
    F.fill(fh, '#2e3242')
    F.fill(fh & FL.edge(fh, 'r', 2), '#4a4e60')
    gx0, gx1, gy0, gy1 = GATE_K
    arch = F.box(gx0, gy0, gx1 - 10, gy1)
    F.fill(arch, '#07080e')
    F.fill(F.box(gx0 + 6, gy0 + 10, gx0 + 14, gy0 + 16), '#ffe0a0')
    F.pool(arch, gx0 + 10, gy0 + 40, 60, 90, steps=((1.0, 1.3),), col='#5a3a1a')
    Z14.courtyard_dress(F, Y, HANNA, BASE_WIN, GATE_K)      # plaster, stucco, neighbours, the yard's things
    # light: the candle's spill on the plinth and the yard, the fanlight's on the steps, Hanna's on the sill
    F.pool(pl | yd, cx_ + 40, Y['yard'], 140, 50, steps=((1.0, 1.06), (0.5, 1.14)), col='#ffb050')
    F.pool(fac, 550, Y['plinth'] + 20, 70, 50, steps=((1.0, 1.08), (0.5, 1.16)), col='#ffc070')
    return F.opaque()


def k1_front():
    """Drawn over the car: the gate passage's left jamb so the car disappears into the arch."""
    F = FL.Flat(640, K1_H, bg='#000000')
    jamb = F.box(0, GATE_K[2] - 20, 8, K1_H)
    F.fill(jamb, '#2e3242')
    F.fill(jamb & FL.edge(jamb, 'r'), '#4a4e60')
    return F.rgba()


def car_frames():
    """Wendt's black saloon from the side and a little above (it drives left): the roof with a cap of snow, the
    windows, chrome strip and bumpers, the wheels (6 frames: the hubs turning), red tail lights at the right,
    the headlamps' glow ahead."""
    W, H = 200, 70
    out = []
    for i in range(6):
        F = FL.Flat(W, H, bg='#000000')
        x0, x1 = 14, 186
        body = F.poly([(x0, 46), (x0 + 6, 32), (x0 + 40, 28), (x0 + 60, 12), (x1 - 56, 10), (x1 - 34, 26),
                       (x1 - 4, 30), (x1, 46), (x1 - 4, 56), (x0 + 4, 56)])
        F.fill(body, '#0e1016')
        F.fill(body & F.box(0, 30, W, 36), '#1c2030')
        F.fill(body & F.box(0, 36, W, 37), '#8a96b4')
        roof = F.poly([(x0 + 62, 12), (x1 - 58, 10), (x1 - 62, 6), (x0 + 66, 8)])
        F.fill(roof, '#d8e0ec')
        F.fill(F.poly([(x0 + 64, 13), (x1 - 60, 11), (x1 - 40, 26), (x0 + 44, 28)]) & body, '#141a2a')
        F.fill(F.box(x0 + 98, 12, x0 + 101, 27) & body, '#0e1016')
        F.fill(F.line([(x0 + 70, 24), (x0 + 84, 14)], 0.6) & body, '#4a5878')
        F.fill(F.box(x0 + 4, 50, x1 - 4, 52), '#9aa4b8')
        F.fill(F.box(x0, 44, x0 + 8, 50), '#ffe8b0')
        F.fill(F.box(x1 - 6, 36, x1, 42), '#ff3020')
        F.outline(body, col='#050608')
        for wx in (x0 + 34, x1 - 36):
            wh = F.ell(wx, 54, 12, 12)
            F.fill(wh, '#0a0a0c')
            F.fill(F.ell(wx, 54, 6, 6), '#5a6070')
            a = i * math.pi / 3
            F.fill(F.line([(wx, 54), (wx + math.cos(a) * 5, 54 + math.sin(a) * 5)], 0.6), '#14161c')
            F.outline(wh, col='#050608')
        out.append(F.rgba())
    return K.hsheet(out), W, H


# ------------------------------------------------------------------------------------------------ k2 Kordon-17
K2_HORIZON = 178
HALL = (250, 470, 196, 226)              # the building on the Line (x0, x1, roof, ground)
DOOR_E = (452, 216, 462, 226)            # Tür Ost (east end, lit when open)
WAGON = (500, 560, 208, 226)
FENCE_Y = 238
FLASH_T = 7.35                           # publish_now: the flashbulb pops at the fence (c4p2cine_kordon_publish)
DOOR_OPEN = 6.2                          # protect_first: Tür Ost opens (c4p2cine_kordon_protect)
DOOR_SHUT = 9.7                          # ... and closes


def k2_plate():
    """Kordon-17 from far, painted in env_c4p2_cine_kordon (sky and its light dome, the forest in two bands, the
    compound under its masts and towers, the hall on the Line with Tür Ost, the siding with C-17/45, the sentry hut
    and boom, the fences, the road with its telegraph poles) on this film's anchors."""
    return KD.k2_plate(HALL, DOOR_E, WAGON, FENCE_Y, K2_HORIZON)


def tiny_walkers():
    """Far figures (10-12 px) for Kordon-17: a two-frame walk of a figure in a dark coat (the people), one in a
    greatcoat and cap (the escort, without weapons shown), and the man with the notebook at the fence
    (two frames: notebook down, notebook up)."""
    sheets = {}
    for name, coat, hat, h in (('person', '#4a4e5e', 'scarf', 12), ('escort', '#2e343c', 'cap', 13),
                               ('witness', '#5a5040', 'hat', 13)):
        frames = []
        for pose in (('walk1', 'walk2') if name != 'witness' else ('stand', 'arms_up')):
            g = GB(16, 18)
            K.tiny(g, 8, 16, h, coat=coat, hat=hat, face=-1 if name != 'witness' else 1, z=10, pose=pose,
                   seed=len(frames), hat_col='#14161c')
            frames.append(g.final([Lt(8, -20, -40, '#f2e8c8', I=1.8, r=100, wrap=0.5)], PAL.KORDON, spread=0.0,
                                  sky='#6a7a96', gnd='#4a5a76', amb=0.9))
        sheets[name] = K.hsheet(frames)
    return sheets


def door_light():
    """The light falling from Tür Ost onto the snow when it stands open (a trapezoid), additive, in steps."""
    dx0, dy0, dx1, dy1 = DOOR_E
    g = np.zeros((K.VH, K.VW, 3), np.float32)
    yy, xx = np.mgrid[0:K.VH, 0:K.VW].astype(np.float32)
    spread = (yy - dy1) * 1.6
    m = (yy >= dy0) & (yy < dy1 + 20) & (xx >= dx0 - np.maximum(0, spread)) & (xx <= dx1 + np.maximum(0, spread))
    f = np.where(yy < dy1, 1.0, np.clip(1 - (yy - dy1) / 20, 0, 1))
    g += (m * f)[..., None] * np.array([130, 118, 80], np.float32)
    return K.VK.soft_quant(g, 8.0, 0, 0)


def flash_frames():
    """The flashbulb: 3 frames (the burst, a halo, a fading glow) -- additive; reduced motion uses frame 2 only."""
    out = []
    for r, k in ((26, 1.0), (40, 0.6), (30, 0.25)):
        out.append(K.glow_sprite(100, 100, [(50, 50, r, r, (255 * k, 250 * k, 230 * k), 1.6),
                                            (50, 50, 4, 4, (255, 255, 255), 1.0)], 8.0))
    return K.hsheet(out)


# ------------------------------------------------------------------------------------------------ k3 dispatch office
K3_WIN = (96, 64, 300, 236)              # the window onto the yard (x0, y0, x1, y1)
K3_ALEXEI = (112, 112)                   # top-left of Alexei's bust (outside the glass)
K3_IRINA = (262, 150)                    # top-left of Irina's bust cell (112 x 160)
TTY = (430, 252)                         # the teleprinter's tape slot (the newest character is printed here)
CLOCK_C = (540, 96)
TEXT = {'publish_now': 'ПЕРЕДАЧА ПРИОСТАНОВЛЕНА ТЧК', 'protect_first': 'С-17/45 УБЫЛ КОРДОН-17 ТЧК'}
TYPE_T0 = 11.6                           # the teleprinter starts (c4p2cine_tty_*)
TYPE_CPS = 7.0                           # characters per second
LEV_LAMP = (262, 178)


def k3_plate():
    """The dispatch office at night: the wall (panelled below, distempered above), the train graph, the
    calendar, the clock (its second hand is drawn live), the window with frost and the yard beyond (snow, a lamp
    post, the freight office with Lev's lamp), the desk with the ledger, the telephone, tea, the green lamp,
    and the teleprinter at the right with its paper roll, type unit and keyboard."""
    F = FL.Flat(bg='#0a0806')
    xx, yy = F.xx.astype(np.int64), F.yy.astype(np.int64)
    wall = F.box(0, 0, 640, 300)
    F.fill(wall, '#5a5a48')
    F.fill(wall & (K.hash2(np.floor_divide(xx, 16), np.floor_divide(yy, 16), 5) > 0.85), '#545442')
    pan = F.box(0, 200, 640, 300)
    F.fill(pan, '#4a3222')
    for x in range(0, 640, 40):
        F.fill(F.box(x, 200, x + 1, 300), '#2e1e14')
        F.fill(F.box(x + 1, 200, x + 2, 300), '#6a4a32')
    F.fill(F.box(0, 198, 640, 202), '#6a4a32')
    # the train graph: stations on the left, the time grid, the trains as slanted lines (red / blue)
    gr = F.box(330, 50, 480, 150)
    F.fill(gr, '#e2dcc6')
    for k, y in enumerate(range(56, 148, 12)):
        F.fill(F.box(334, y, 476, y + 1), '#9a9682')
    for x in range(340, 476, 8):
        F.fill(F.box(x, 54, x + 1, 146), '#c8c2aa')
    for k in range(7):
        x0 = 340 + k * 20
        F.fill(F.line([(x0, 58), (x0 + 34, 142)], 0.5), '#b03020' if k % 2 else '#2a4a8a')
    F.fill(F.text('ГРАФИК', 340, 44, 's'), '#2a2a24')
    F.outline(gr, col='#3a3a30')
    cal = F.box(500, 140, 540, 186)
    F.fill(cal, '#e8e2d0')
    F.fill(F.box(500, 140, 540, 150), '#b03020')
    F.fill(F.text('17', 510, 158, 'm') & cal, '#2a2a24')
    F.outline(cal, col='#3a3a30')
    cx, cy = CLOCK_C
    ck = F.ell(cx, cy, 22, 22)
    F.fill(ck, '#2a2a28')
    F.fill(F.ell(cx, cy, 19, 19), '#ece6d4')
    for k in range(12):
        a = k * math.pi / 6
        F.fill(F.box(cx + math.cos(a) * 15 - 1, cy + math.sin(a) * 15 - 1, cx + math.cos(a) * 15 + 1,
                     cy + math.sin(a) * 15 + 1), '#2a2a28')
    F.fill(F.line([(cx, cy), (cx + 8, cy - 6)], 0.9) | F.line([(cx, cy), (cx - 2, cy - 12)], 0.7), '#1a1a18')
    F.outline(ck, col='#0a0a08')
    # the window: frame, the night yard, the freight office with Lev's lamp, the lamp post
    wx0, wy0, wx1, wy1 = K3_WIN
    yard = F.box(wx0, wy0, wx1, wy1)
    F.grad(yard, wy0, wy1, '#0a0e1c', '#2a3448', steps=4)
    F.fill(yard & (yy > 196), '#4a5670')
    fo = F.box(212, 150, 290, 196)
    F.fill(fo, '#2a1e18')
    F.fill(F.poly([(206, 150), (296, 150), (251, 132)]), '#1a1414')
    F.fill(F.poly([(206, 150), (296, 150), (251, 132)]) & FL.edge(F.poly([(206, 150), (296, 150), (251, 132)]), 't'), '#c8d0dc')
    lw = F.box(LEV_LAMP[0] - 7, LEV_LAMP[1] - 6, LEV_LAMP[0] + 7, LEV_LAMP[1] + 6)
    F.fill(lw, '#f0b050')
    F.fill(F.box(LEV_LAMP[0] - 1, LEV_LAMP[1] - 6, LEV_LAMP[0] + 1, LEV_LAMP[1] + 6), '#2a1e18')
    F.fill(F.box(wx0 + 20, 120, wx0 + 22, 200), '#14161c')
    F.fill(F.box(wx0 + 16, 118, wx0 + 26, 121), '#fff0c0')
    fr = F.box(wx0 - 8, wy0 - 8, wx1 + 8, wy1 + 8) & ~yard
    F.fill(fr, '#e0dccc')
    F.fill(fr & FL.edge(F.box(wx0 - 8, wy0 - 8, wx1 + 8, wy1 + 8), 'b', 3), '#8a8676')
    F.fill(F.box(wx0 - 12, wy1 + 6, wx1 + 12, wy1 + 12), '#d8d4c4')
    F.outline(F.box(wx0 - 8, wy0 - 8, wx1 + 8, wy1 + 8), col='#2a2a24')
    # the desk across the front (everything from here on is also the foreground layer over Irina)
    front0 = F.a.copy()
    desk = F.box(0, 286, 640, 360)
    F.fill(desk, '#5a3a24')
    F.fill(F.box(0, 286, 640, 289), '#8a5a38')
    F.fill(desk & (np.mod(yy - 286, 9) == 0), '#4a2e1c')
    led = F.poly([(40, 292), (150, 290), (152, 316), (42, 318)])
    F.fill(led, '#e2d8bc')
    for ly in range(296, 316, 3):
        F.fill(F.box(46, ly, 146, ly + 1) & led, '#8a8070')
    F.outline(led, col='#4a4030')
    ph = F.box(170, 270, 214, 292)
    F.fill(ph, '#141414')
    F.fill(F.box(166, 262, 218, 270), '#1e1e1e')
    F.fill(F.ell(192, 284, 9, 6), '#e8e0d0')
    F.fill(F.ell(192, 284, 3, 2), '#141414')
    F.outline(ph, col='#050505')
    tg = F.box(226, 262, 246, 290)
    F.fill(tg, '#8a9098')
    F.fill(F.box(228, 262, 244, 272), '#a0521a')
    F.fill(F.box(226, 262, 228, 290), '#c8ced4')
    F.outline(tg, col='#2a2e34')
    # the green lamp
    lb = F.box(392, 272, 412, 290)
    F.fill(lb, '#8a6a2a')
    F.fill(F.box(400, 236, 404, 272), '#8a6a2a')
    sh = F.poly([(376, 226), (430, 226), (420, 210), (386, 210)])
    F.fill(sh, '#1e5a3a')
    F.fill(sh & FL.edge(sh, 't'), '#4a8a6a')
    F.fill(F.box(380, 226, 426, 229), '#fff0c0')
    F.outline(sh, col='#0a2014')
    # the teleprinter: cabinet, keyboard, type unit under its hood, paper roll, the tape slot facing left
    tb = F.box(436, 196, 620, 296)
    F.fill(tb, '#3a4440')
    F.fill(tb & FL.edge(tb, 't', 3), '#5a6a64')
    hood = F.poly([(444, 196), (604, 196), (596, 168), (452, 168)])
    F.fill(hood, '#2a3430')
    F.fill(hood & F.box(452, 172, 596, 190), '#4a5a64')
    F.fill(hood & F.box(480, 178, 560, 186), '#8a9aa4')
    roll = F.ell(520, 160, 26, 10)
    F.fill(roll, '#e8e2cc')
    F.fill(roll & (F.yy < 157), '#f6f0de')
    F.outline(roll, col='#6a6450')
    kb = F.poly([(446, 262), (610, 262), (620, 292), (436, 292)])
    F.fill(kb, '#26302c')
    for r_ in range(4):
        for c in range(12):
            kx, ky = 452 + c * 13 + r_ * 3, 266 + r_ * 6
            F.fill(F.box(kx, ky, kx + 9, ky + 4), '#d8d4c4')
            F.fill(F.box(kx, ky + 3, kx + 9, ky + 4), '#8a867a')
    F.fill(F.box(TTY[0] - 4, TTY[1] - 6, TTY[0] + 8, TTY[1] + 6), '#1a201e')
    F.fill(F.box(TTY[0] - 2, TTY[1] - 1, TTY[0] + 6, TTY[1] + 1), '#0a0a0a')
    plate_ = F.box(500, 240, 556, 250)
    F.fill(plate_, '#c8b878')
    F.fill(F.text('ТА-68', 510, 242, 's') & plate_, '#2a2418')
    F.outline(tb | hood, col='#0a100e')
    # light: the green lamp's pool on the desk and the machine, the room dim beyond it
    F.pool(desk | tb | kb, 404, 262, 220, 70, steps=((1.0, 1.08), (0.6, 1.2), (0.3, 1.34)), col='#ffd890')
    F.mul(wall & ~F.ell(404, 230, 330, 200), 0.84)
    front = desk | led | ph | F.box(166, 262, 218, 270) | tg | lb | F.box(400, 236, 404, 272) | sh |         F.box(380, 226, 426, 229) | tb | hood | roll | kb
    return F.opaque(), F.rgba(front)


def k3_glass():
    """Frost on the window's glass over Alexei (drawn over his bust): ferns from the corners, a cold sheen."""
    F = FL.Flat(bg='#000000')
    wx0, wy0, wx1, wy1 = K3_WIN
    glass = F.box(wx0, wy0, wx1, wy1)
    xx, yy = F.xx, F.yy
    fern = glass & (((np.abs(np.sin((xx - wx0) * 0.6 + (yy - wy0) * 0.5)) > 0.8) &
                     (np.minimum(xx - wx0, yy - wy0) < 22 - 0.2 * np.maximum(xx - wx0, yy - wy0))) |
                    ((np.abs(np.sin((wx1 - xx) * 0.55 + (wy1 - yy) * 0.45)) > 0.82) &
                     (np.minimum(wx1 - xx, wy1 - yy) < 26 - 0.16 * np.maximum(wx1 - xx, wy1 - yy))))
    F.fill(fern, '#c8d8e8')
    mull = F.box((wx0 + wx1) / 2 + 30, wy0, (wx0 + wx1) / 2 + 34, wy1) | F.box(wx0, wy0 + 40, wx1, wy0 + 44)
    F.fill(mull, '#e0dccc')
    F.fill(mull & FL.edge(mull, 'b'), '#8a8676')
    outer = F.box(wx0 - 8, wy0 - 8, wx1 + 8, wy1 + 8)
    fr = outer & ~glass
    F.fill(fr, '#e0dccc')
    F.fill(fr & FL.edge(outer, 'b', 3), '#8a8676')
    sill = F.box(wx0 - 12, wy1 + 6, wx1 + 12, wy1 + 12)
    F.fill(sill, '#d8d4c4')
    F.fill(sill & FL.edge(sill, 't'), '#f0ece0')
    edge_ = FL.edge(outer, 'all')
    F.fill(edge_, '#2a2a24')
    F.fill(FL.edge(glass, 'all'), '#8a8676')
    return F.rgba(fern | mull | fr | sill | edge_)


def tape_strip(text):
    """The teleprinter tape with the message in capitals (cream paper, 11 px, the 'm' font)."""
    m = K.VK.vtext(text, 'm', 1)
    w = m.shape[1] + 8
    F = FL.Flat(w, 11, bg='#000000')
    F.fill(F.box(0, 0, w, 11), '#ece4cc')
    F.fill(F.box(0, 0, w, 1) | F.box(0, 10, w, 11), '#b8b098')
    tm = np.zeros((11, w), bool)
    tm[2:2 + min(9, m.shape[0]), 4:4 + m.shape[1]] = m[:min(9, m.shape[0])]
    F.fill(tm, '#1a1a20')
    out = F.rgba(np.ones((11, w), bool))
    xs = []
    import env_veltrava_lib as vlib
    cx = 1
    for ch in text:
        if ch == ' ':
            cx += 3
        else:
            gl_, acc = vlib._glyph(ch, 'm')
            cx += (len(gl_[0]) + 1) if gl_ is not None else 6
        xs.append(cx + 4)
    return out, xs


def k3_people():
    """Irina at the teleprinter (10 frames: reading the tape -- neutral, a blink, then concerned; 6..9 concerned
    breathing, a blink) and Alexei outside the frosted glass (8 frames, graded cold by the night with the room's
    warm light on his face) -- round 11: whole figures from env_c4p2_cine_figs (her shoulders, arms and hands
    on the desk; his shoulders under the ushanka, cut by the sill) instead of busts on painted torsos."""
    import env_c4p2_cine_figs as FG
    return FG.irina_k3_sheet(), FG.alexei_k3_sheet()


# ------------------------------------------------------------------------------------------------ k4 the desk
K4_CARD = (250, 170)
K4_THING = (390, 160)


def k4_plate():
    """Irina's desk from above: the green baize pad with its leather border, the ledger open, the blotter, a
    pencil, the tea glass in its holder, the tape's end curling in, the lamp's stepped pool (the card and the
    canister or folder are sprites)."""
    F = FL.Flat(bg='#140e0a')
    xx, yy = F.xx.astype(np.int64), F.yy.astype(np.int64)
    wood = F.box(0, 0, 640, 360)
    F.fill(wood, '#4a2e1c')
    F.fill(wood & (np.mod(yy + (np.floor_divide(xx, 120) * 7), 11) == 0), '#3a2414')
    pad = F.box(30, 50, 610, 300)
    F.fill(pad, '#7a4a2a')
    baize = F.box(40, 60, 600, 290)
    F.fill(baize, '#2a5a3a')
    F.fill(baize & (K.hash2(xx, yy, 3) > 0.92), '#2e6040')
    F.outline(pad, col='#2a180c')
    led = F.poly([(60, 76), (210, 68), (218, 250), (66, 260)])
    F.shadow(led, -5, 6, 0.7, under=baize)
    F.fill(led, '#e2d8bc')
    F.fill(F.line([(138, 72), (142, 256)], 0.6), '#a89a80')
    for ly in range(90, 250, 6):
        F.fill(F.line([(72, ly), (210, ly - 6)], 0.4) & led, '#8a8070')
        if ly % 12 == 0:
            F.fill(F.line([(78, ly - 2), (128, ly - 4)], 0.4) & led, '#2a3a6a')
    F.outline(led, col='#6a6050')
    pen = F.line([(72, 272), (200, 296)], 1.4)
    F.shadow(pen, -3, 4, 0.7)
    F.fill(pen, '#c8a040')
    F.fill(F.line([(196, 295), (202, 297)], 1.0), '#2a2a2a')
    hold = F.ell(560, 110, 26, 26)
    F.shadow(hold, -8, 10, 0.68)
    F.fill(hold, '#9aa0a8')
    F.fill(hold & ~F.ell(556, 106, 26, 26), '#c8ced6')
    F.fill(F.ell(560, 110, 20, 20), '#a0521a')
    F.fill(F.ell(560, 110, 20, 20) & ~F.ell(562, 112, 20, 20), '#6e3410')
    F.fill(F.ell(552, 104, 5, 4), '#e8a860')
    F.outline(hold, col='#2a2e34')
    tape = F.poly([(640, 214), (470, 226), (452, 240), (470, 250), (640, 240)])
    F.shadow(tape, -3, 5, 0.7, under=baize)
    F.fill(tape, '#ece4cc')
    for k in range(18):
        x = 480 + k * 9
        F.fill(F.box(x, 230 - k * 0.1, x + 5, 234 - k * 0.1), '#2a2a30')
    F.outline(tape, col='#8a8470')
    _k4_dress(F, pad, baize)
    F.pool(baize | led, 330, 170, 300, 180, steps=((1.0, 1.0), (0.6, 1.12), (0.3, 1.26)), col='#ffd890')
    F.mul(wood & ~pad, 0.7)
    return F.opaque()


def _k4_dress(F, pad, baize):
    """The rest of a night dispatcher's desk round the card: the baize's nap, wear and two ink blots, the leather
    border's tooled line, the schoty (abacus) with tonight's count pushed over, the inkwell and the dip pen, the
    stamp and its pad, a stack of telegram blanks, paper clips, the glass ashtray (all in the lamp's light later)."""
    import env_c4p2_cine_book as B
    xx, yy = F.xx.astype(np.int64), F.yy.astype(np.int64)
    F.speckle(baize, 0.10, None, seed=471, k=0.9)
    F.speckle(baize, 0.05, None, seed=472, k=1.1)
    F.mul(baize & F.ell(330, 286, 120, 26), 1.08)
    for (bx, by, r) in ((452, 120, 4), (338, 254, 3)):
        F.fill(F.ell(bx, by, r, r * 0.7) | F.ell(bx + r * 0.8, by + 1, r * 0.5, r * 0.4), '#1e2a3a')
    F.speckle(pad & ~baize, 0.12, None, seed=473, k=0.85)
    tool = (F.box(34, 54, 606, 296) & ~F.box(35, 55, 605, 295))
    F.fill(tool, '#a8783a')
    # the schoty: frame, eight wires, beads (the middle pair dark), a count pushed to the left
    fr = F.box(236, 64, 346, 120)
    F.shadow(fr, -5, 6, 0.7, under=baize)
    F.fill(fr, '#6a3a1e')
    F.fill(fr & FL.edge(fr, 't', 2), '#9a6030')
    inner = F.box(242, 70, 340, 114)
    F.fill(inner, '#2a1a10')
    for r in range(8):
        y = 73 + r * 5.2
        F.fill(F.box(242, y, 340, y + 1), '#b8b0a0')
        pushed = int(K.hash2(r, 1, 474) * 6)
        for b in range(10):
            bx = (244 + b * 7) if b < pushed else (340 - (10 - b) * 7)
            col = '#2a1a10' if b in (4, 5) else '#d8c098'
            F.fill(F.ell(bx + 3, y + 0.5, 3, 2.2), col)
            F.fill(F.box(bx + 1, y - 1, bx + 4, y), '#f0e0b8' if b not in (4, 5) else '#5a4030')
    F.outline(fr, col='#2a1408', k=0.6)
    # the inkwell and the dip pen
    ink = F.ell(228, 146, 9, 8)
    F.shadow(ink, -4, 5, 0.7, under=baize)
    F.fill(ink, '#8a9aa0')
    F.fill(F.ell(228, 146, 5, 4), '#141a2a')
    F.fill(F.ell(225, 142, 2, 1.5), '#e8f0f4')
    F.outline(ink, col='#2a3034', k=0.6)
    pen = F.line([(242, 160), (300, 138)], 1.0)
    F.shadow(pen, -3, 4, 0.7, under=baize)
    F.fill(pen, '#3a2418')
    F.fill(F.line([(296, 139.5), (304, 136.5)], 0.7), '#c8c0b0')
    # the stamp and its ink pad
    tin = F.box(222, 234, 260, 258)
    F.shadow(tin, -4, 5, 0.7, under=baize)
    F.fill(tin, '#7a7a82')
    F.fill(F.box(225, 237, 257, 255), '#3a2a5a')
    F.fill(F.box(225, 237, 257, 238), '#5a4a7a')
    st = F.box(268, 238, 292, 256)
    F.shadow(st, -4, 5, 0.7, under=baize)
    F.fill(st, '#5a3a20')
    F.fill(F.ell(280, 247, 6, 6), '#9a6a3a')
    F.fill(F.ell(278, 245, 2, 2), '#c89a60')
    F.outline(st | tin, col='#2a1a10', k=0.6)
    # telegram blanks, a few paper clips
    for k, (dx, dy, a) in enumerate(((0, 0, -3.0), (3, -2, 2.0), (1, 2, -1.0))):
        c, s_ = math.cos(math.radians(a)), math.sin(math.radians(a))
        pts = [(470 + dx + u * c - v * s_, 64 + dy + u * s_ + v * c) for (u, v) in ((0, 0), (58, 0), (58, 74), (0, 74))]
        sh = F.poly(pts)
        if k == 0:
            F.shadow(sh, -4, 5, 0.7, under=baize)
        F.fill(sh, ('#e4dcc4', '#ece6d2', '#f2ecdc')[k])
        F.outline(sh, col='#8a8470', k=0.7)
    top_ = F.poly([(471, 66), (529, 64), (531, 138), (473, 140)])
    F.fill(F.text('ТЕЛЕГРАММА', 476, 70, 's') & top_, '#5a3a3a')
    for ly in range(84, 134, 6):
        F.fill(F.box(476, ly, 524, ly + 1) & top_, '#b8b0a0')
    for (cx, cy) in ((440, 76), (452, 82), (214, 284)):
        clip = (F.ell(cx, cy, 4, 2) & ~F.ell(cx, cy, 3, 1)) | (F.ell(cx + 1, cy, 2.5, 1.2) & ~F.ell(cx + 1, cy, 1.5, 0.4))
        F.fill(clip, '#b8c0c8')
    B.ashtray(F, 566, 272, 14, glass=True, under=baize, butts=2, papirosa=True)


def k4_card():
    import env_c4p2_cine_book as B
    c = B.card_rgba(False, ('#ffcf8a', 1.0))
    return FL.shadow_rgba(c, -3, 4, (20, 12, 6, 110))


def k4_canister():
    """The film canister (protect_first): a squat aluminium tin with its lid's rim, a strip of tape, C-17 in
    pencil; its shadow on the baize."""
    F = FL.Flat(76, 76, bg='#000000')
    disc = F.ell(35, 35, 30, 30)
    F.fill(disc, '#8a9096')
    F.fill(disc & ~F.ell(39, 39, 30, 30), '#c0c8cc')
    F.fill(disc & ~F.ell(31, 31, 30, 30), '#5a6066')
    ring = disc & ~F.ell(35, 35, 25, 25)
    F.fill(ring & (F.yy < 35), '#d8e0e4')
    F.fill(ring & (F.yy >= 35), '#6a7076')
    F.fill(F.ell(35, 35, 6, 6), '#a8b0b4')
    tape = F.box(14, 30, 56, 40) & disc
    F.fill(tape, '#e8e0c4')
    F.fill(F.text('C-17', 22, 32, 's') & tape, '#3a3a40')
    F.outline(disc, col='#2a2e32')
    out = F.rgba()
    return FL.shadow_rgba(out, -5, 6, (20, 12, 6, 110))


def k4_folder():
    """Lev's empty folder (publish_now): grey card, open, nothing in it, the string ties loose, C-17/45 in ink."""
    F = FL.Flat(156, 116, bg='#000000')
    left = F.poly([(6, 10), (72, 6), (74, 102), (8, 106)])
    right = F.poly([(74, 6), (142, 10), (140, 104), (74, 102)])
    F.fill(left, '#9a9278')
    F.fill(right, '#a49c80')
    F.fill(left & FL.edge(left, 'l', 2), '#7a7258')
    F.fill(F.line([(74, 6), (74, 102)], 0.6), '#5a5440')
    F.fill(F.text('C-17/45', 92, 20, 's') & right, '#2a2a3a')
    F.fill(F.line([(140, 56), (148, 66), (144, 80)], 0.5) | F.line([(8, 56), (2, 70)], 0.5), '#6a5a3a')
    F.outline(left | right, col='#3a3626')
    return FL.shadow_rgba(F.rgba(), -5, 6, (20, 12, 6, 110))


def build(w):
    w('clock/k1_bg.png', k1_plate())
    w('clock/k1_front.png', k1_front())
    cs, cw, ch = car_frames()
    w('clock/car.png', cs)
    w('clock/k1_glow.png', K.glow_sprite(K.VW, K1_H, [(CANDLE[0], CANDLE[1], 26, 16, (110, 60, 16), 1.5)], 8.0))
    w('clock/passage_glow.png', K.glow_sprite(K.VW, K1_H, [(GATE_K[0] + 20, 430, 40, 30, (110, 80, 36), 1.5)],
                                              8.0))
    w('clock/k2_bg.png', k2_plate())
    for name, sh in tiny_walkers().items():
        w('clock/k2_%s.png' % name, sh)
    w('clock/k2_door.png', door_light())
    w('clock/k2_smoke.png', KD.smoke_sheet())
    ps, pcw, pch = KD.patrol_sheet()
    w('clock/k2_patrol.png', ps)
    L.update(KD.layout((pcw, pch)))
    w('clock/flash.png', flash_frames())
    beams = np.zeros((K.VH, K.VW, 4), np.uint8)
    for mx in (300, 520, 160):
        bm = K.beam_sprite(K.VW, K.VH, mx, 152, 0, 80, 34, (60, 54, 38), 8.0, 1.2, 0.3, seed=mx)
        m = bm[..., 3] > 0
        beams[m] = np.maximum(beams[m], bm[m])
    w('clock/k2_beams.png', beams)
    back, front = k3_plate()
    w('clock/k3_bg.png', back)
    w('clock/k3_front.png', front)
    w('clock/k3_glass.png', k3_glass())
    tapes = {}
    for key, txt in TEXT.items():
        strip, xs = tape_strip(txt)
        w('clock/tape_%s.png' % key, strip)
        tapes[key] = xs
    irina, alexei = k3_people()
    w('clock/k3_irina.png', irina)
    w('clock/k3_alexei.png', alexei)
    w('clock/k3_lev_glow.png', K.glow_sprite(K.VW, K.VH, [(LEV_LAMP[0], LEV_LAMP[1], 14, 10, (90, 56, 16), 1.5)], 8.0))
    w('clock/k3_lamp_glow.png', K.glow_sprite(K.VW, K.VH, [(404, 232, 70, 30, (80, 64, 30), 1.5)], 8.0))
    w('clock/k4_bg.png', k4_plate())
    w('clock/k4_card.png', k4_card())
    w('clock/k4_canister.png', k4_canister())
    w('clock/k4_folder.png', k4_folder())
    w('clock/k4_glow.png', K.glow_sprite(K.VW, K.VH, [(330, 170, 200, 110, (40, 30, 12), 1.4)], 8.0))
    w('clock/tea_steam.png', K.puff_sheet(8, 22, 30, PAL.K_STEAM[2:], 461, grow=(0.2, 0.5), thin=0.7,
                                          light=(0.5, -0.6), drift=0.15))
    L.update(car_path=[list(p) for p in CAR_PATH], car_t=list(CAR_T), car_cell=[cw, ch], car_doors=list(CAR_DOORS),
             engine_t=ENGINE_T, candle=list(CANDLE), gate=list(GATE_K), k1_h=K1_H, k1_tilt=list(K1_TILT),
             hall=list(HALL), door_e=list(DOOR_E), wagon=list(WAGON), fence_y=FENCE_Y, flash_t=FLASH_T,
             door_open=DOOR_OPEN, door_shut=DOOR_SHUT, k3_win=list(K3_WIN), alexei=list(K3_ALEXEI),
             irina=list(K3_IRINA), tty=list(TTY), clock_c=list(CLOCK_C), type_t0=TYPE_T0, type_cps=TYPE_CPS,
             tape_x=tapes, text=TEXT, lev_lamp=list(LEV_LAMP), k4_card=list(K4_CARD), k4_thing=list(K4_THING))
