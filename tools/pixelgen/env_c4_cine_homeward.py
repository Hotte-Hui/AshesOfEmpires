"""env_c4_cine_homeward -- art of LS_C4_Homeward (owner: cine stream, round 9; C4_DESIGN §2.9).

Four days after the fire, each man goes home with his half of the file:
  w1  Veltrava station at first light, looking down the island platform under the iron shed: the westbound
      train to Berlin on the left, the eastbound to Karsk on the right; Konrad and Alexei walk up the platform
      (the game's own sheets, seen from behind, re-lit), part, and board on opposite sides
  w2  split windows: the Reich carriage (left) passing under the dome of the Great Hall, the Soviet carriage
      (right) crossing the snow plain toward the cooling towers of Karsk -- the landscapes run in opposite
      directions (scrolling strips)
  w3  Karsk freight yard before dawn (plate shared with LS_C4_Voices v3: env_c4_cine_places.karsk_yard):
      the repaired signal shows green, Alexei walks to the lit cellar window of the freight office
Runtime: scenes/cinematics/ch4_homeward/ch4_homeward.gd (anchors in layout.json "homeward").
"""
from __future__ import annotations

import math

import numpy as np

import env_c4_cine_kit as Q
from env_c4_cine_kit import (C, VW, VH, KNIGHT, AMBER, RUST, CREAM, CONCRETE, IRONK, DAWN, SNOWB, SNOWK, SODIUM,
                             NAVYB, OAKK, PAPERB, box, ell, poly, grid)
import pg

L = Q.LAYOUT.setdefault('homeward', {})

VP = (320, 148)                        # vanishing point of the platform (w1)
EDGE_NEAR = (186, 454)                 # platform edges at the bottom of the frame (y = 360)
DOOR_K = (248, 266)                    # the doors they board: Konrad left, Alexei right (feet x, y)
DOOR_A = (392, 266)
WIN_K = (36, 70, 300, 290)             # w2 windows (x0, y0, x1, y1)
WIN_A = (340, 70, 604, 290)
STRIP_W = 780


def _edge_x(y, side):
    """x of a platform edge at row y (perspective)."""
    x_near = EDGE_NEAR[0] if side == 'l' else EDGE_NEAR[1]
    return VP[0] + (x_near - VP[0]) * (y - VP[1]) / (VH - VP[1])


# ======================================================================================= w1
def w1_station():
    R = Q.ramps(D=DAWN, S=SNOWB, I=IRONK, N=SODIUM, U=NAVYB, G=['#06100C', '#0C1C14', '#14281E', '#1E3A2A',
                                                                    '#2C5038', '#406A4C'],
                C=CONCRETE, X=PAPERB, P=['#2A2230', '#4A3A48', '#6E5A64', '#9A7E84', '#C4A8A6', '#E6CEC2'])
    p = C.Paint(VW, VH, R, 'w1')
    yy, xx = p.yy, p.xx
    nz = Q.noise(VW, VH, 14, 8101)
    vx, vy = VP
    # the shed's far opening: the dawn sky and the line out of the city
    sky = (yy < vy + 4) & (np.abs(xx - vx) < 70 - (vy - yy) * 0.2)
    p.put(sky, 'P', 2.4 + (yy[sky] - 90) / 60.0 * 2.6 + nz[sky] * 0.4)
    # the glass roof: arched trusses converging, panes catching the first light
    roof = (yy < vy) & ~sky
    u = (vy - yy) / vy
    p.put(roof, 'D', 3.0 + u[roof] * 2.4 + nz[roof] * 0.5)
    ang = np.arctan2(yy - vy, xx - vx)
    ribs = roof & (np.mod(ang * 9.0, 1.0) < 0.08 + u * 0.05)
    p.put(ribs, 'I', 1.6 + u[ribs] * 1.6)
    d = np.hypot(xx - vx, (yy - vy) * 1.7)
    trusses = roof & (np.mod(np.log(d + 1.0) * 7.0, 1.0) < 0.10)
    p.put(trusses, 'I', 1.4 + u[trusses] * 1.4)
    # the two trains: carriage walls in perspective, lit windows, doors; dark under-frames
    for side, ramp, base in (('l', 'U', 2.6), ('r', 'G', 2.8)):
        if side == 'l':
            wall = (xx < _edge_x(yy, 'l') - 6) & (yy > vy - 24 - (vx - xx) * 0.55) & (xx < vx - 30)
        else:
            wall = (xx > _edge_x(yy, 'r') + 6) & (yy > vy - 24 - (xx - vx) * 0.55) & (xx > vx + 30)
        dist = np.abs(xx - vx) / 320.0
        p.put(wall, ramp, base + dist[wall] * 1.4 + nz[wall] * 0.5)
        # the window band: rows between 0.30 and 0.55 of the wall height at that x
        top = vy - 24 - np.abs(xx - vx) * 0.55
        bot = np.where(side == 'l', 0, 0) + vy + 6 + np.abs(xx - vx) * 0.62
        hgt = bot - top
        band = wall & (yy > top + hgt * 0.27) & (yy < top + hgt * 0.43)
        seg = np.mod(np.log(np.abs(xx - vx) + 8.0) * 11.0, 1.0)
        winm = band & (seg > 0.14) & (seg < 0.80)
        p.put(winm, 'N', 2.4 + nz[winm] * 1.0 - dist[winm] * 0.8)
        p.put(winm & (np.abs(yy - (top + hgt * 0.36)) < 0.8), ramp, base + 1.0)          # the sash bar
        under = wall & (yy > top + hgt * 0.86)
        p.put(under, 'I', 0.8 + dist[under] * 0.6)
        p.put(wall & (np.abs(yy - (top + hgt * 0.20)) < 1.0), ramp, base + 2.6)
    # destination boards, readable: BERLIN (left), КАРСК (right)
    for txt, x0, ramp in (('BERLIN', 54, 'U'), ('КАРСК', 520, 'G')):
        b = box(x0 - 4, 196, x0 + 66, 210)
        p.put(b, 'X', 6.4)
        p.put(Q.text_at(txt, VW, VH, x0 + 2, 199, 'l'), ramp, 0.8)
    # the doors they board (dark openings with a lit step)
    for (dx, dy) in (DOOR_K, DOOR_A):
        dr = box(dx - 7, dy - 50, dx + 7, dy - 2)
        p.put(dr, 'N', 1.4)
        p.put(box(dx - 8, dy - 2, dx + 8, dy + 1), 'I', 3.0)
    # the island platform: stone with snow, edge lines, a lamp row, the clock and the platform number
    plat = (yy > vy + 2) & (xx >= _edge_x(yy, 'l')) & (xx <= _edge_x(yy, 'r'))
    v = (yy - vy) / (VH - vy)
    p.put(plat, 'S', 3.0 + v[plat] * 2.4 + nz[plat] * 0.8)
    edge = plat & ((np.abs(xx - _edge_x(yy, 'l')) < 1 + v * 2) | (np.abs(xx - _edge_x(yy, 'r')) < 1 + v * 2))
    p.put(edge, 'X', 6.8)
    for k in range(6):
        ly = vy + 6 + (VH - vy) * (0.08 + 0.17 * k) ** 1.6
        hl = 6 + (ly - vy) * 0.55
        p.put(box(vx - 1, ly - hl, vx + 1 + int(v[int(min(VH - 1, ly)), vx] * 2), ly), 'I', 1.8)
        p.put(box(vx - 3 - k, ly - hl - 2, vx + 4 + k, ly - hl + 1), 'N', 6.0)
    p.put(ell(vx, 104, 9, 9), 'X', 6.0)
    p.put(ell(vx, 104, 7, 7), 'X', 7.4)
    p.put(p.line([(vx, 104), (vx, 99)], r=0.5) | p.line([(vx, 104), (vx + 4, 106)], r=0.5), 'I', 1.0)
    p.put(box(vx - 1, 46, vx + 1, 95), 'I', 2.0)
    p.put(box(vx - 14, 118, vx + 15, 132), 'X', 6.2)
    p.put(Q.text_at('5', VW, VH, vx - 2, 121, 'l'), 'I', 1.0)
    p.resolve(band=2.0)
    L['vp'] = list(VP)
    L['door_k'] = list(DOOR_K)
    L['door_a'] = list(DOOR_A)
    L['w1_steam'] = [[262, 150], [378, 150]]
    return p.L.c


def w1_glow():
    return Q.glow_sprite(VW, VH, [(VP[0], 120, 90, 60, (40, 34, 40), 1.3), (VP[0], 300, 160, 40, (30, 28, 34), 1.4),
                                  (110, 180, 130, 50, (60, 40, 16), 1.4), (530, 180, 130, 50, (60, 40, 16), 1.4)], 6.0)


# ======================================================================================= w2
def w2_frames():
    """The two carriage interiors around the windows: the Reich carriage (dark wood, brass) left, the Soviet
    carriage (green-painted panels, a lace curtain) right; the window holes are transparent."""
    R = Q.ramps(W=OAKK, B=['#2A1D0B', '#4A3415', '#73531F', '#9C7630', '#C49A48'], G=['#06100C', '#0C1C14',
                                                                                      '#14281E', '#1E3A2A',
                                                                                      '#2C5038', '#406A4C'],
                X=PAPERB, R=RUST, K=KNIGHT)
    p = C.Paint(VW, VH, R, 'w2')
    yy, xx = p.yy, p.xx
    nz = Q.noise(VW, VH, 10, 8201)
    left = xx < 320
    p.put(left, 'W', 1.6 + nz[left] * 0.6 + (np.mod(xx, 40) < 1)[left] * -0.8)
    p.put(~left, 'G', 2.2 + nz[~left] * 0.5)
    p.put(~left & (np.mod(yy, 46) == 0), 'G', 1.2)
    p.put(box(316, 0, 324, VH), 'K', 0.6)
    for (x0, y0, x1, y1), ramp in ((WIN_K, 'B'), (WIN_A, 'G')):
        fr = box(x0 - 8, y0 - 8, x1 + 8, y1 + 8) & ~box(x0, y0, x1, y1)
        p.put(fr, ramp, 2.6 + nz[fr] * 0.6)
        p.put(box(x0 - 8, y0 - 8, x1 + 8, y0 - 6), ramp, 4.4)
        p.put(box(x0 - 12, y1 + 8, x1 + 12, y1 + 16), ramp, 3.4)            # the sill / the little table
    # the lace curtain gathered at the right window's edge, a tea glass in its holder on the table
    cur = box(WIN_A[2] - 20, WIN_A[1] - 6, WIN_A[2] + 6, WIN_A[3] + 4)
    lace = cur & ((np.mod(xx + yy, 5) < 2) | (np.mod(xx - yy, 7) < 1))
    p.put(cur, 'X', 4.0 + nz[cur] * 0.8)
    p.put(lace, 'X', 6.0)
    p.put(box(560, 284, 572, 300), 'B', 3.0)
    p.put(box(561, 278, 571, 284), 'X', 5.4)
    # the leather blind strap in the Reich carriage
    p.put(box(WIN_K[0] + 120, WIN_K[1] - 8, WIN_K[0] + 128, WIN_K[1] + 26), 'R', 2.4)
    out = p.resolve(band=2.0).c.copy()
    for (x0, y0, x1, y1) in (WIN_K, WIN_A):
        out[y0:y1, x0:x1, 3] = 0
    out[WIN_A[1] - 6:WIN_A[3] + 4, WIN_A[2] - 20:WIN_A[2] + 6] = p.L.c[WIN_A[1] - 6:WIN_A[3] + 4,
                                                                       WIN_A[2] - 20:WIN_A[2] + 6]
    L['win_k'] = list(WIN_K)
    L['win_a'] = list(WIN_A)
    return out


def w2_sky(city):
    w, h = WIN_K[2] - WIN_K[0], WIN_K[3] - WIN_K[1]
    a = np.zeros((h, w, 3), np.float32)
    yy, xx = grid(h, w)
    if city == 'berlin':
        top, bot = Q.hexrgb('#1C2A46'), Q.hexrgb('#8A9EB6')
    else:
        top, bot = Q.hexrgb('#2A2432'), Q.hexrgb('#D8A88A')
    u = (yy / h)[..., None]
    a[:] = top * (1 - u) + bot * u
    pal = (['#1C2A46', '#26385A', '#32486E', '#425C84', '#58729A', '#7489AE', '#8A9EB6'] if city == 'berlin' else
           ['#2A2432', '#3E2E3C', '#5A3C44', '#7E5048', '#A86A52', '#C88A6A', '#D8A88A'])
    return Q.requant(a, pal, 10.0)


def w2_far(city):
    """Far layer (not tiled: it scrolls only ~40 px): Berlin -- the dome of the Great Hall looming over the blocks
    of the axis and two cranes; Karsk -- the snow plain, a birch line, the cooling towers with their plumes."""
    h = WIN_K[3] - WIN_K[1]
    w = STRIP_W
    if city == 'berlin':
        R = Q.ramps(D=DAWN, S=SNOWB)
        p = C.Paint(w, h, R, 'far_b')
        yy, xx = p.yy, p.xx
        hz = 150
        dome = Q.C.ellipse_mask(w, h, 330, hz + 10, 230, 150) & (yy < hz)
        cosv = np.sqrt(np.clip(1.0 - ((hz + 10 - yy) / 150.0) ** 2, 0, 1))
        p.put(dome, 'D', 3.2 + (yy[dome] - 10) / 140.0 * 0.8)
        ribs = np.zeros_like(dome)
        for sk in np.sin(np.linspace(-1.4, 1.4, 13)):
            ribs |= np.abs(xx - (330 + 230 * sk * cosv)) < 0.6
        p.put(ribs & dome, 'D', 2.6)
        p.put(dome & C.rim(dome, 1, -1, 2), 'D', 4.6)
        blocks = (yy >= hz - 40) & (yy < hz + 30) & (np.mod(np.floor(xx / 38) * 7.1, 6) > 1.4 + (hz - yy) / 20.0)
        p.put(blocks, 'D', 2.2)
        p.put(blocks & (np.mod(xx, 7) < 2) & (np.mod(yy, 9) < 3) & (Q.noise(w, h, 3, 8301) > 0.6), 'D', 5.0)
        for cx_ in (120, 640):
            p.put(Q.box(cx_, hz - 110, cx_ + 3, hz + 30, w, h), 'D', 2.0)
            p.put(p.line([(cx_ - 30, hz - 110), (cx_ + 80, hz - 108)], r=0.8), 'D', 2.0)
        gr = yy >= hz + 30
        p.put(gr, 'S', 3.0 + (yy[gr] - hz - 30) / 40.0)
        p.resolve(band=2.0)
    else:
        R = Q.ramps(P=['#2A2432', '#3E2E3C', '#5A3C44', '#7E5048', '#A86A52', '#C88A6A', '#D8A88A', '#EEC8A8'],
                    S=['#3A3444', '#564A58', '#7A6670', '#A08A8E', '#C6B0AE', '#E4D2CA'], K=KNIGHT)
        p = C.Paint(w, h, R, 'far_a')
        yy, xx = p.yy, p.xx
        hz = 140
        for (tx, tb) in ((470, hz + 2), (540, hz + 2)):
            u = np.clip((tb - yy) / 70.0, 0, 1)
            half = 26 - 10 * np.sin(u * math.pi * 0.85) + u * 4
            tw = (yy <= tb) & (yy >= tb - 70) & (np.abs(xx - tx) < half)
            p.put(tw, 'S', 2.0 + (1 - u[tw]) * 0.8)
            p.put(tw & (xx > tx + half - 4), 'P', 5.4)
        th = pg.bayer(w, h, 0, 0)
        for k in range(7):                                           # the plume: soft puffs leaning east
            cx_, cy_ = 506 + k * 13, hz - 74 - k * 15
            pr = Q.C.ellipse_mask(w, h, cx_, cy_, 12 + k * 4, 9 + k * 3)
            sel = pr & (th < 0.95 - k * 0.11) & (yy < hz - 60)
            p.put(sel, 'P', 3.6 - k * 0.12 + Q.noise(w, h, 6, 8305)[sel] * 0.8)
        birch = (yy >= hz - 18) & (yy < hz) & (Q.noise(w, h, 4, 8307) > 0.45 + (hz - yy) / 40.0)
        p.put(birch, 'S', 1.4)
        gr = yy >= hz
        p.put(gr, 'S', 3.4 + (yy[gr] - hz) / 80.0 * 1.2 + Q.noise(w, h, 10, 8309)[gr] * 0.9)
        drift = gr & (np.mod(yy - hz + np.floor(xx / 60) * 3, 9) == 0) & (Q.noise(w, h, 5, 8311) > 0.5)
        p.put(drift, 'S', 2.4)
        p.resolve(band=2.0)
    return p.L.c


def w2_near(city):
    """Near layer, tiled (period 260 px): Berlin -- catenary masts and a lamp; Karsk -- telegraph poles and
    their sagging wires, snow fence."""
    h = WIN_K[3] - WIN_K[1]
    w = 260
    R = Q.ramps(K=KNIGHT, D=DAWN, S=SNOWB, P=['#2A2432', '#5A3C44', '#A86A52'])
    p = C.Paint(w, h, R, 'near_' + city)
    yy, xx = p.yy, p.xx
    if city == 'berlin':
        p.put(Q.box(40, 0, 46, h, w, h), 'K', 1.6)
        p.put(Q.box(46, 20, 120, 23, w, h), 'K', 1.8)
        p.put(Q.box(0, 34, w, 35, w, h), 'K', 1.2)
        p.put(Q.box(160, 120, 163, h, w, h), 'K', 1.4)
        p.put(Q.box(156, 116, 168, 121, w, h), 'D', 6.0)
    else:
        p.put(Q.box(60, 0, 65, h, w, h), 'K', 1.8)
        for k in range(3):
            p.put(Q.box(48, 16 + k * 10, 78, 18 + k * 10, w, h), 'K', 2.0)
            sag = (yy - (18 + k * 10 + 10 * np.sin(np.clip((xx - 65) / 260.0, 0, 1) * math.pi)) )
            p.put((np.abs(sag) < 0.6) & (xx > 65), 'K', 2.2)
            sag2 = (yy - (18 + k * 10 + 10 * np.sin(np.clip((xx + 195) / 260.0, 0, 1) * math.pi)))
            p.put((np.abs(sag2) < 0.6) & (xx < 60), 'K', 2.2)
        fence = (yy > h - 46) & (yy < h - 20) & (np.mod(xx, 9) < 2)
        p.put(fence, 'K', 1.6)
        p.put((yy >= h - 22) & (yy < h - 18), 'S', 6.0)
    p.resolve(band=2.0)
    return p.L.c


def build(w):
    w('homeward/w1_station.png', w1_station())
    w('homeward/w1_glow.png', w1_glow())
    look = Q.LIGHT_STATION
    sk, ik = Q.fig_sheet('konrad', [('walk_back', None, False), ('walk_side', None, True)], look)
    sa, ia = Q.fig_sheet('alexei', [('walk_back', None, False), ('walk_side', None, False)], look)
    w('homeward/w1_konrad.png', sk)
    w('homeward/w1_alexei.png', sa)
    L['w1_konrad'] = ik
    L['w1_alexei'] = ia
    w('homeward/w2_frames.png', w2_frames())
    for city in ('berlin', 'karsk'):
        w('homeward/w2_sky_%s.png' % city, w2_sky(city))
        w('homeward/w2_far_%s.png' % city, w2_far(city))
        w('homeward/w2_near_%s.png' % city, w2_near(city))
    L['strip_w'] = STRIP_W
    sa3, ia3 = Q.fig_sheet('alexei', [('walk_side', None, False), ('idle_side', None, False),
                                      ('look_side', None, False)], Q.LIGHT_KARSK_NIGHT)
    w('homeward/w3_alexei.png', sa3)
    L['w3_alexei'] = ia3
    L['w3_walk'] = [230, 466]
