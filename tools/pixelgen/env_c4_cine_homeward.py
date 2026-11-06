"""env_c4_cine_homeward -- art of LS_C4_Homeward (owner: cine stream; C4_DESIGN §2.9; polish pass 2026-11-06).

Four days after the fire, each man goes home with his half of the file:
  w1  Veltrava station at first light, down platform 5 under the iron shed (env_c4_cine_station: a ray-cast plate in
      which the game's own 56 px figures stand at their true size): the westbound train to Berlin on the left, the
      eastbound to Karsk on the right, lit compartments, destination boards, globes, the clock, benches, a trolley;
      Konrad and Alexei walk up the platform (the game's sheets, from behind, re-lit), part, board on opposite sides;
      the conductors, a porter, a mother and her boy, an old woman (game sheets) around them; the doors as sprites
  w2  split windows: the Reich compartment (walnut, brass, a reading lamp, a suitcase on the rack) passing under the
      dome of the Great Hall, the Soviet one (green panels, a lace curtain, tea in its holder) crossing the snow plain
      toward the cooling towers of Karsk -- three depths of landscape per window (far / mid / near strips) running
      in opposite directions, snow streaks on the glass
  w3  Karsk freight yard before dawn (the layered yard of env_c4_cine_yard, shared with LS_C4_Voices v3): the
      repaired signal shows green, Alexei walks to the lit cellar window of the freight office, the camera tracking
The round-9 painters w1_station / w2_far / w2_near stay below for reference (no longer built).
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


# ======================================================================================= w2 (polish pass)
WIN_W, WIN_H = WIN_K[2] - WIN_K[0], WIN_K[3] - WIN_K[1]
MID_W = 520                            # tiled mid strip (houses / birches)


def w2_interiors():
    """The two compartments around the windows (window holes transparent): the Reich carriage (left): polished
    walnut with brass, a leather blind strap, the brass luggage rack with a suitcase, the table with a reading
    lamp, the white antimacassar on the seat; the Soviet carriage (right): green panels, a cream frame, the lace
    curtain gathered, a tea glass in its holder, the rack with a bundle tied in string."""
    R = Q.ramps(W=OAKK, B=['#2A1D0B', '#4A3415', '#73531F', '#9C7630', '#C49A48', '#E8C779'],
                G=['#06100C', '#0C1C14', '#14281E', '#1E3A2A', '#2C5038', '#406A4C', '#5A8462'],
                X=PAPERB, R=['#1A0A08', '#2E120E', '#4A1C14', '#6A2A1A', '#8A3C22'], K=KNIGHT,
                Y=['#3A3428', '#6A6050', '#A09684', '#D2CABA', '#F0EAE0'], A=AMBER)
    p = C.Paint(VW, VH, R, 'w2i')
    yy, xx = p.yy, p.xx
    nz = Q.noise(VW, VH, 10, 8201)
    grain = Q.noise(VW, VH, 3, 8203)
    lampk = Q.lightfield(VW, VH, [(70, 300, 200, 1.0, 1.3)])
    tea = Q.lightfield(VW, VH, [(560, 300, 160, 0.7, 1.4)])
    left = xx < 320
    # walnut panels with inlay lines, brightening toward the reading lamp
    p.put(left, 'W', 1.4 + nz[left] * 0.5 + grain[left] * 0.5 + lampk[left] * 2.0)
    p.put(left & ((np.mod(xx, 44) == 0) | (np.mod(yy, 64) == 0)), 'W', 0.8)
    p.put(left & ((np.mod(xx, 44) == 2) | (np.mod(yy, 64) == 2)), 'B', 2.0 + lampk[left & ((np.mod(xx, 44) == 2) |
                                                                                              (np.mod(yy, 64) == 2))])
    # green-painted panels (right), the seams, a little worn at the edges
    p.put(~left, 'G', 2.0 + nz[~left] * 0.5 + tea[~left] * 1.2)
    p.put(~left & (np.mod(yy, 46) == 0), 'G', 1.0)
    p.put(~left & (np.mod(yy, 46) == 1), 'G', 3.2)
    p.put(box(316, 0, 324, VH), 'K', 0.6)
    # window frames: brass (left), cream paint (right); the sills / small tables
    for (x0, y0, x1, y1), fr_ramp, ft in ((WIN_K, 'B', 2.4), (WIN_A, 'Y', 2.2)):
        fr = box(x0 - 10, y0 - 10, x1 + 10, y1 + 10) & ~box(x0, y0, x1, y1)
        p.put(fr, fr_ramp, ft + nz[fr] * 0.5 + (lampk[fr] if fr_ramp == 'B' else tea[fr]) * 1.2)
        p.put(box(x0 - 10, y0 - 10, x1 + 10, y0 - 8), fr_ramp, ft + 2.0)
        p.put(box(x0 - 2, y0 - 2, x1 + 2, y0) | box(x0 - 2, y0, x0, y1), fr_ramp, ft - 1.0)       # inner shadow
        p.put(box(x0 - 16, y1 + 10, x1 + 16, y1 + 18), fr_ramp if fr_ramp == 'B' else 'G', ft + 1.4)
        p.put(box(x0 - 16, y1 + 10, x1 + 16, y1 + 11), fr_ramp, ft + 2.6)
        # the luggage rack above the window: two rails and the net
        p.put(box(x0 - 6, y0 - 34, x1 + 6, y0 - 32) | box(x0 - 6, y0 - 22, x1 + 6, y0 - 20), 'B', 3.4)
        net = box(x0 - 6, y0 - 32, x1 + 6, y0 - 22) & ((np.mod(xx + yy, 4) == 0) | (np.mod(xx - yy, 4) == 0))
        p.put(net, 'K', 2.0)
    # left: the suitcase on the rack (strap, brass corners), the blind strap, the reading lamp, antimacassar
    x0, y0, x1, y1 = WIN_K
    sc = box(x0 + 30, y0 - 54, x0 + 118, y0 - 34)
    p.put(sc, 'R', 2.4 + nz[sc] * 0.8)
    p.put(box(x0 + 30, y0 - 54, x0 + 118, y0 - 52), 'R', 3.6)
    p.put(box(x0 + 70, y0 - 54, x0 + 74, y0 - 34), 'W', 1.2)
    p.put(box(x0 + 30, y0 - 54, x0 + 34, y0 - 50) | box(x0 + 114, y0 - 54, x0 + 118, y0 - 50), 'B', 4.4)
    p.put(box(x0 + 128, y0 - 10, x0 + 136, y0 + 34), 'R', 2.2)
    p.put(box(x0 + 129, y0 + 30, x0 + 135, y0 + 34), 'B', 4.4)
    lamp_ = box(x0 - 26, y1 - 14, x0 - 18, y1 + 10) | ell(x0 - 22, y1 - 20, 9, 7)
    p.put(lamp_, 'B', 3.4)
    p.put(ell(x0 - 22, y1 - 18, 7, 4) & (yy > y1 - 20), 'A', 6.6)
    am = box(0, y0 + 40, 14, y0 + 120)
    p.put(am, 'Y', 3.6 + nz[am] * 0.4)
    p.put(am & ((np.mod(xx + yy, 6) == 0) | (np.mod(xx - yy, 6) == 0)), 'Y', 2.4)
    # right: the lace curtain gathered at the window's right edge, the tea glass, the bundle on the rack
    x0, y0, x1, y1 = WIN_A
    cur = box(x1 - 22, y0 - 8, x1 + 8, y1 + 6)
    lace = cur & ((np.mod(xx + yy, 5) < 2) | (np.mod(xx - yy, 7) < 1))
    folds = cur & (np.mod(xx - (x1 - 22), 6) < 1)
    p.put(cur, 'Y', 3.0 + nz[cur] * 0.6 + tea[cur] * 0.8)
    p.put(lace, 'Y', 4.0 + tea[lace] * 0.6)
    p.put(folds, 'Y', 2.0)
    p.put(box(x1 - 24, y0 - 10, x1 + 10, y0 - 6), 'B', 3.0)                          # curtain rod
    gx = 548
    # the tea glass in its podstakannik, standing on the sill in front of the glass (drawn again after the window
    # hole is cut, so it stays whole); the spoon is a runtime sprite that rattles in it
    holder = box(gx, y1 - 8, gx + 14, y1 + 10)
    p.put(holder, 'B', 2.6 + np.clip((gx + 10 - xx[holder]) / 10.0, 0, 1) * 1.6)        # podstakannik, lit left
    p.put(box(gx + 2, y1 - 6, gx + 12, y1 + 8) & (np.mod(xx - gx, 3) == 0), 'B', 1.6)    # its filigree
    p.put(box(gx, y1 - 8, gx + 14, y1 - 7) | box(gx, y1 + 2, gx + 14, y1 + 3), 'B', 4.6)  # the rims of the bands
    p.put(box(gx + 14, y1 - 4, gx + 18, y1 + 6) & ~box(gx + 14, y1 - 2, gx + 16, y1 + 4), 'B', 3.0)  # handle
    glass = box(gx + 1, y1 - 16, gx + 13, y1 - 8)
    p.put(glass, 'A', 2.4 + (yy[glass] - (y1 - 16)) / 8.0 * -0.8 + np.clip((gx + 6 - xx[glass]) / 6.0, 0, 1) * 1.0)
    p.put(box(gx + 2, y1 - 16, gx + 3, y1 - 9), 'Y', 3.6)                               # the glass's highlight
    p.put(box(gx + 1, y1 - 17, gx + 13, y1 - 16), 'Y', 4.4)                             # the rim
    tea_m = (holder | glass | box(gx + 1, y1 - 17, gx + 13, y1 - 16) |
             (box(gx + 14, y1 - 4, gx + 18, y1 + 6) & ~box(gx + 14, y1 - 2, gx + 16, y1 + 4)))
    bd = ell(x0 + 90, y0 - 44, 40, 12) & (yy < y0 - 34)
    p.put(bd, 'Y', 1.8 + nz[bd] * 0.8)
    p.put(bd & (np.abs(xx - (x0 + 90)) < 1), 'R', 2.0)
    out = p.resolve(band=2.0).c.copy()
    for (a0, b0, a1, b1) in (WIN_K, WIN_A):
        out[b0:b1, a0:a1, 3] = 0
    keep = box(WIN_A[2] - 22, WIN_A[1] - 8, WIN_A[2] + 8, WIN_A[3] + 6)              # the curtain over the glass
    out[keep] = p.L.c[keep]
    out[tea_m] = p.L.c[tea_m]                                                        # the tea glass, whole
    L['win_k'] = list(WIN_K)
    L['win_a'] = list(WIN_A)
    L['tea_spoon'] = [gx + 9, WIN_A[3] - 30]
    return out


def w2_far2(city):
    """Far (non-tiled, scrolls ~40 px): Berlin -- the dome of the Great Hall looming over the axis, its lantern,
    the blocks in the haze, cranes with their lamps; Karsk -- the town on the horizon, the cooling towers and
    their plumes lit by the sunrise, the snow plain."""
    h, w = WIN_H, STRIP_W
    if city == 'berlin':
        R = Q.ramps(D=DAWN, S=SNOWB, N=SODIUM)
        p = C.Paint(w, h, R, 'far2_b')
        yy, xx = p.yy, p.xx
        nz = Q.noise(w, h, 14, 8321)
        hz = 158
        dome = Q.C.ellipse_mask(w, h, 330, hz + 8, 250, 150) & (yy < hz)
        cosv = np.sqrt(np.clip(1.0 - ((hz + 8 - yy) / 150.0) ** 2, 0, 1))
        p.put(dome, 'D', 3.4 + (yy[dome] - 10) / 150.0 * 1.0 + nz[dome] * 0.3)
        ribs = np.zeros_like(dome)
        for sk in np.sin(np.linspace(-1.4, 1.4, 15)):
            ribs |= np.abs(xx - (330 + 250 * sk * cosv)) < 0.6
        p.put(ribs & dome, 'D', 2.6)
        for k in range(1, 4):
            p.put(dome & (np.abs(yy - (hz - k * 34)) < 0.6), 'D', 2.8)
        p.put(dome & C.rim(dome, 1, -1, 2), 'D', 5.2)
        p.put(box(316, 0, 344, 18, w, h), 'D', 3.0)
        p.put(box(322, 0, 338, 6, w, h), 'D', 3.6)
        # the axis blocks in the haze (windows lit at random), cranes with red lamps
        blocks = (yy >= hz - 46) & (yy < hz + 24) & (np.mod(np.floor(xx / 40) * 7.1, 6) > 1.2 + (hz - yy) / 22.0)
        p.put(blocks, 'D', 2.4 + nz[blocks] * 0.4)
        lit = blocks & (np.mod(xx, 7) < 2) & (np.mod(yy, 9) < 3) & (Q.noise(w, h, 3, 8323) > 0.62)
        p.put(lit, 'N', 5.0)
        for cx_ in (110, 560, 700):
            p.put(box(cx_, hz - 120, cx_ + 3, hz + 24, w, h), 'D', 2.0)
            p.put(p.line([(cx_ - 34, hz - 120), (cx_ + 84, hz - 117)], r=0.8), 'D', 2.0)
            p.put(box(cx_ + 80, hz - 117, cx_ + 81, hz - 90, w, h), 'D', 2.6)
            p.put(box(cx_, hz - 124, cx_ + 3, hz - 121, w, h), 'N', 6.4)
        gr = yy >= hz + 24
        p.put(gr, 'S', 3.0 + (yy[gr] - hz - 24) / 40.0 + nz[gr] * 0.5)
        p.resolve(band=2.0)
    else:
        R = Q.ramps(P=['#2A2432', '#3E2E3C', '#5A3C44', '#7E5048', '#A86A52', '#C88A6A', '#D8A88A', '#EEC8A8'],
                    S=['#3A3444', '#564A58', '#7A6670', '#A08A8E', '#C6B0AE', '#E4D2CA'], K=KNIGHT, A=AMBER)
        p = C.Paint(w, h, R, 'far2_a')
        yy, xx = p.yy, p.xx
        nz = Q.noise(w, h, 12, 8331)
        hz = 150
        th = pg.bayer(w, h, 0, 0)
        for (tx, tb, ht) in ((470, hz + 2, 62), (536, hz + 2, 54), (600, hz + 2, 46)):
            u = np.clip((tb - yy) / ht, 0, 1)
            half = 22 - 9 * np.sin(np.clip(u / 0.72, 0, 1) * math.pi * 0.5) + np.clip(u - 0.72, 0, 1) * 12
            tw = (yy <= tb) & (yy >= tb - ht) & (np.abs(xx - tx) < half)
            p.put(tw, 'S', 1.8 + (1 - u[tw]) * 0.6)
            p.put(tw & (xx < tx - half + 4), 'P', 5.6)                    # the sunrise on their east flanks
            for k in range(8):
                cx_, cy_ = tx - k * 8 - k * k, tb - ht - 10 - k * 12
                pr = Q.C.ellipse_mask(w, h, cx_, cy_, 11 + k * 3.5, 7 + k * 2.6)
                sel = pr & (th < 0.78 - k * 0.085) & (yy < tb - ht)
                p.put(sel, 'S', 4.4 - k * 0.12 + nz[sel] * 0.5)
                p.put(sel & (xx < cx_ - (11 + k * 3.5) * 0.4), 'P', 6.2)       # the sunrise on the plume's east side
        town = (yy >= hz - 12) & (yy < hz) & (np.mod(np.floor(xx / 9) * 5.3, 7) > 2 + (hz - yy) / 3.0) & (xx < 420)
        p.put(town, 'S', 1.4)
        p.put(town & (np.mod(xx, 5) == 0) & (Q.noise(w, h, 2, 8333) > 0.6), 'A', 5.0)
        gr = yy >= hz
        p.put(gr, 'S', 3.6 + (yy[gr] - hz) / 70.0 * 1.2 + nz[gr] * 0.8)
        p.put(gr & (np.mod(yy - hz + np.floor(xx / 60) * 3, 11) == 0) & (Q.noise(w, h, 5, 8335) > 0.5), 'S', 2.6)
        p.resolve(band=2.0)
    out = p.L.c.copy()
    out[p.L.rid < 0] = 0
    return out


def w2_mid(city):
    """Mid strip, tiled (MID_W): Berlin -- a row of tenements and sheds passing, lit windows, chimneys; Karsk -- a
    birch wood, a village of log houses with one lit window and smoke, a fence."""
    h, w = WIN_H, MID_W
    if city == 'berlin':
        R = Q.ramps(D=DAWN, S=SNOWB, N=SODIUM, K=KNIGHT)
        p = C.Paint(w, h, R, 'mid_b')
        yy, xx = p.yy, p.xx
        nz = Q.noise(w, h, 8, 8341)
        base = 196
        for (bx0, bw, top) in ((0, 70, 120), (78, 56, 140), (150, 90, 108), (256, 40, 150), (312, 84, 126),
                               (410, 70, 136), (488, 32, 160)):
            b = box(bx0, top, bx0 + bw, base, w, h)
            p.put(b, 'D', 1.6 + nz[b] * 0.4)
            p.put(box(bx0, top, bx0 + bw, top + 2, w, h), 'S', 5.4)
            win = b & (np.mod(xx - bx0, 10) < 4) & (np.mod(yy - top, 14) < 6) & (yy > top + 6) & (xx > bx0 + 3) & \
                (xx < bx0 + bw - 3)
            lit = win & (Q.noise(w, h, 4, 8343 + bx0) > 0.58)
            p.put(win & ~lit, 'D', 0.8)
            p.put(lit, 'N', 4.6 + nz[lit])
            p.put(box(bx0 + bw // 3, top - 10, bx0 + bw // 3 + 4, top, w, h), 'D', 1.4)
        p.put(box(0, base, w, h, w, h), 'S', 3.4)
        p.put(box(0, base, w, base + 2, w, h), 'S', 5.6)
        p.resolve(band=2.0)
    else:
        R = Q.ramps(S=['#3A3444', '#564A58', '#7A6670', '#A08A8E', '#C6B0AE', '#E4D2CA'], K=KNIGHT, A=AMBER,
                    W=['#2A2026', '#3E2E30', '#5A4038', '#7A5A44'],
                    B=['#6A6268', '#9A8E8E', '#C8BAB4', '#ECE0D8'])
        p = C.Paint(w, h, R, 'mid_a')
        yy, xx = p.yy, p.xx
        nz = Q.noise(w, h, 6, 8351)
        base = 186
        # the birch wood: a soft violet haze of bare crowns, white trunks with their dark marks
        crown = (yy > 112 + nz * 26) & (yy < base) & ((xx < 226) | (xx > 334))
        p.put(crown, 'S', 1.6 + nz[crown] * 0.5 + (yy[crown] - 112) / 80.0 * 0.6)
        twig = crown & (Q.noise(w, h, 4, 8353) > 0.62)
        p.put(twig, 'S', 1.0)
        for k in range(18):
            tx_ = (k * 29 + (k * k * 13) % 17) % w
            if 222 < tx_ < 338:
                continue
            top = 120 + (k * 17) % 30
            tr = box(tx_, top, tx_ + 1 + (k % 3 == 0), base, w, h)
            p.put(tr, 'B', 2.2 + (k % 3) * 0.4)
            p.put(tr & (np.mod(yy + k * 5, 11) < 2), 'K', 2.4)
        # the village: two log houses, snow on the roofs, one window lit, a fence
        for (hx, hw) in ((240, 40), (290, 34)):
            house = box(hx, base - 26, hx + hw, base, w, h)
            p.put(house, 'W', 1.4 + nz[house] * 0.5)
            p.put(house & (np.mod(yy, 4) == 0), 'W', 0.8)
            roof = poly([(hx - 4, base - 26), (hx + hw + 4, base - 26), (hx + hw // 2, base - 44)], w, h)
            p.put(roof, 'S', 4.8)
            p.put(box(hx + hw // 2 - 4, base - 18, hx + hw // 2 + 4, base - 10, w, h), 'A', 6.0 if hx == 240 else 1.4)
            p.put(box(hx + hw - 10, base - 50, hx + hw - 6, base - 36, w, h), 'W', 1.2)
        fence = (yy > base - 10) & (yy < base) & (np.mod(xx, 6) < 1) & (xx > 220) & (xx < 340)
        p.put(fence, 'W', 1.6)
        p.put(box(0, base, w, h, w, h), 'S', 3.6)
        p.put(box(0, base, w, base + 2, w, h), 'S', 4.6)
        p.resolve(band=2.0)
    out = p.L.c.copy()
    out[p.L.rid < 0] = 0
    L['w2_chimneys_' + city] = [[278, 76], [300, 60]] if city == 'karsk' else [[150 + 30, 98]]
    return out


def w2_near2(city):
    """Near, tiled (260 px): Berlin -- a catenary mast with its cantilever, the contact wire, a lamp; Karsk -- a
    telegraph pole with three crossarms, the sagging wires, a snow fence and a drift."""
    h, w = WIN_H, 260
    R = Q.ramps(K=KNIGHT, D=DAWN, S=SNOWB, P=['#2A2432', '#5A3C44', '#A86A52'], N=SODIUM)
    p = C.Paint(w, h, R, 'near2_' + city)
    yy, xx = p.yy, p.xx
    if city == 'berlin':
        p.put(box(40, 0, 47, h, w, h), 'K', 1.4)
        p.put(box(41, 0, 42, h, w, h), 'K', 2.6)
        for y_ in range(10, h, 16):
            p.put(p.line([(40, y_), (47, y_ + 8)], r=0.4), 'K', 2.0)
        p.put(box(47, 22, 132, 25, w, h), 'K', 1.8)
        p.put(p.line([(47, 40), (120, 25)], r=0.6), 'K', 1.8)
        p.put(box(0, 36, w, 37, w, h), 'K', 1.2)
        p.put(box(0, 44, w, 45, w, h), 'K', 1.0)
        p.put(box(170, 118, 173, h, w, h), 'K', 1.4)
        p.put(box(166, 114, 178, 119, w, h), 'D', 6.0)
        p.put(box(168, 119, 176, 121, w, h), 'N', 6.6)
        p.put((yy >= h - 18), 'S', 2.4)
    else:
        p.put(box(60, 0, 66, h, w, h), 'K', 1.8)
        p.put(box(60, 0, 61, h, w, h), 'K', 3.0)
        for k in range(3):
            y_ = 14 + k * 11
            p.put(box(44, y_, 82, y_ + 3, w, h), 'K', 2.0)
            for ix in (46, 54, 72, 80):
                p.put(box(ix, y_ - 3, ix + 2, y_, w, h), 'S', 6.0)
            u = np.mod(xx - 66, 260) / 260.0
            sag = yy - (y_ + 2 + 14 * np.sin(u * math.pi))
            p.put((np.abs(sag) < 0.6) & ((xx < 60) | (xx > 66)), 'K', 2.0)
        fence = (yy > h - 52) & (yy < h - 22) & (np.mod(xx, 8) < 2)
        p.put(fence, 'K', 1.4)
        p.put(box(0, h - 46, w, h - 44, w, h) | box(0, h - 34, w, h - 32, w, h), 'K', 1.6)
        drift = (yy >= h - 26 - 6 * np.sin(xx / 41.0)) & (yy < h)
        p.put(drift, 'S', 6.0 - (yy[drift] - (h - 26)) / 20.0)
    p.resolve(band=2.0)
    out = p.L.c.copy()
    out[p.L.rid < 0] = 0
    return out


def w2_streaks():
    """Snow streaks on the glass (6 frames of a short diagonal smear), for the runtime to scatter."""
    out = []
    for i in range(6):
        a = np.zeros((10, 16, 4), np.uint8)
        L_ = 6 + i * 1.6
        for t in np.linspace(0, 1, 24):
            x, y = 2 + t * L_, 1 + t * L_ * 0.45
            if x < 16 and y < 10:
                v = int(150 + 90 * t)
                a[int(y), int(x)] = (v, v + 4, v + 10, 255)
        out.append(a)
    return Q.sheet(out)


# ======================================================================================= build
def build(w):
    import env_c4_cine_station as ST
    img, hh = ST.station()
    w('homeward/w1_station.png', img)
    w('homeward/w1_glow.png', ST.glow(hh))
    for key, (sheet_, at) in ST.door_sprites().items():
        w('homeward/w1_door_%s.png' % key, sheet_)
        L['w1_door_%s_at' % key] = at
    L.update(ST.anchors())
    look = Q.LIGHT_STATION
    sk, ik = Q.fig_sheet('konrad', [('walk_back', None, False), ('walk_side', None, True)], look)
    sa, ia = Q.fig_sheet('alexei', [('walk_back', None, False), ('walk_side', None, False)], look)
    w('homeward/w1_konrad.png', sk)
    w('homeward/w1_alexei.png', sa)
    L['w1_konrad'] = ik
    L['w1_alexei'] = ia
    # the platform's people (the game's own sheets): the two conductors at their doors, a porter, a mother and
    # child for the Berlin train, an old woman with her bundles for the Karsk train
    npcs = {'conductor_k': ('conductor', [('idle_side', None, False), ('gesture_side', None, False)]),
            'conductor_a': ('porter', [('idle_side', None, True), ('gesture_side', None, True)]),
            'porter': ('worker_a', [('walk_side', None, True), ('idle_side', None, True)]),
            'mother': ('berlin_mother', [('walk_side', None, True), ('idle_side', None, True)]),
            'child': ('berlin_child', [('walk_side', None, True), ('idle_side', None, True)]),
            'babushka': ('babushka', [('walk_side', None, False), ('idle_side', None, False)])}
    idx = {}
    for key, (cid, rows) in npcs.items():
        sh_, ix_ = Q.fig_sheet(cid, rows, look)
        w('homeward/w1_%s.png' % key, sh_)
        idx[key] = ix_
    L['w1_npc_anims'] = idx
    w('homeward/w2_frames.png', w2_interiors())
    import env_c4_cine_figs as G
    for city in ('berlin', 'karsk'):                  # the men's faces mirrored in their windows (figures stream)
        from env_c4_cine_places import figs_disk as FD
        w('homeward/w2_refl_%s.png' % city, FD('homeward/w2_refl_%s.png' % city, lambda c=city: G.w2_reflection(c)))
    for city in ('berlin', 'karsk'):
        w('homeward/w2_sky_%s.png' % city, w2_sky(city))
        w('homeward/w2_far_%s.png' % city, w2_far2(city))
        w('homeward/w2_mid_%s.png' % city, w2_mid(city))
        w('homeward/w2_near_%s.png' % city, w2_near2(city))
    w('homeward/w2_streaks.png', w2_streaks())
    L['strip_w'] = STRIP_W
    L['mid_w'] = MID_W
    sa3, ia3 = Q.fig_sheet('alexei', [('walk_side', None, False), ('idle_side', None, False),
                                      ('look_side', None, False)], Q.LIGHT_KARSK_NIGHT)
    w('homeward/w3_alexei.png', sa3)
    L['w3_alexei'] = ia3
    L['w3_walk'] = [230, 466]
    L['w3_cam'] = [0, 64]
