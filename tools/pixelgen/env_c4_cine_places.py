"""env_c4_cine_places -- places seen in more than one Chapter-4 cinematic (owner: cine stream, round 9).

  karsk_yard()        the freight yard of Karsk before dawn, side view: the repaired signal (green), wagons in the
                      dark, yard lamps, the cooling towers far off; the freight office at the right with its lit
                      cellar window and the outside stair down to the archive cellar -- LS_C4_Homeward w3
                      (Alexei walks to the window) and LS_C4_Voices v3 (Alexei and Lev climb out of the stair)
  yard_parapet()      the stair's parapet in front of the figures (v3: they rise behind it)
  berlin_loop(light)  the tram loop Süd 8 in Berlin, 1000 px (level x 0-1000 of L_C4_Annex area B): house No. 9
                      boarded and sealed, the wallpaper of the demolished neighbour, house No. 11 with Marta's
                      window, the shelter with the lit timetable case, the loop, the advertising column S 2, the
                      freight hatch with the C-17/45 crates; the dome of the Great Hall far off in the haze --
                      'dawn' for LS_C4_Number n4, 'morning' for LS_C4_Voices v1 / v2
  tram(face, ilse)    the two-axle motor car of line 74 (Marta in the cab, Ilse at the last window)
  siding(lit)         the vaulted siding hall under the freight yard: wagon 24 318 / C-17/45 on track 1 under a
                      single work lamp, the paint stand, the conversion kit, the shut portal -- LS_C4_Voices v4
Runtime anchors in layout.json "places".
"""
from __future__ import annotations

import math

import numpy as np

import env_c4_cine_kit as Q
from env_c4_cine_kit import (C, VW, VH, KNIGHT, AMBER, RUST, CREAM, CONCRETE, BRICK, IRONK, SIGNAL, SNOWK, DAWN,
                             SNOWB, SODIUM, PINE, STEEL, TRAM, NAVYB, PAPERB, INKRED, box, ell, poly, grid)
import pg

L = Q.LAYOUT.setdefault('places', {})
FEET = 300

# ======================================================================================= Karsk yard
YARD_SIGNAL = (152, 158)               # the green lamp of the repaired signal
YARD_WINDOW = (520, 280, 560, 297)     # the cellar window (x0, y0, x1, y1), light well below the wall
YARD_STAIR = (414, 500)                # the outside stair down to the cellar (x range of the stairwell)
YARD_LAMPS = ((262, 104), (612, 96))
YARD_TOWERS = ((88, 196), (172, 196))  # cooling towers (centre x, base y)


def karsk_yard():
    R = Q.ramps(K=KNIGHT, S=SNOWK, B=BRICK, C=CONCRETE, I=IRONK, A=AMBER, G=SIGNAL, R=RUST)
    p = C.Paint(VW, VH, R, 'yard')
    yy, xx = p.yy, p.xx
    nz = Q.noise(VW, VH, 14, 5101)
    lamps = Q.lightfield(VW, VH, [(x, y + 40, 120, 1.0, 1.3) for (x, y) in YARD_LAMPS])
    sig = Q.lightfield(VW, VH, [(YARD_SIGNAL[0], YARD_SIGNAL[1], 90, 1.0, 1.4)])
    win = Q.lightfield(VW, VH, [((YARD_WINDOW[0] + YARD_WINDOW[2]) / 2, 300, 110, 1.0, 1.4),
                                ((YARD_STAIR[0] + YARD_STAIR[1]) / 2, 304, 90, 0.8, 1.4)])
    hz = 212
    sky = yy < hz
    glow = Q.lightfield(VW, VH, [(120, hz + 20, 260, 1.0, 1.2)])
    p.put(sky, 'K', 0.8 + (yy[sky] - 40) / (hz - 40) * 2.2 + nz[sky] * 0.5 + glow[sky] * 1.6)
    # the cooling towers of the power plant, lit from below by the plant, far off
    for (tx, tb) in YARD_TOWERS:
        u = np.clip((tb - yy) / 80.0, 0, 1)
        half = 30 - 12 * np.sin(np.clip(u, 0, 1) * math.pi * 0.85) + u * 4
        tw = (yy <= tb) & (yy >= tb - 80) & (np.abs(xx - tx) < half)
        p.put(tw, 'K', 2.4 + (1 - u[tw]) * 1.2 + nz[tw] * 0.4)
        p.put(tw & (np.abs(xx - tx) > half - 2) & (xx > tx), 'K', 3.6)
    p.put(box(232, 120, 238, hz), 'K', 2.0)                       # the plant's chimney
    p.put(box(233, 122, 237, 125), 'R', 7.0)                      # its red lamp
    # far wagons on the sidings, the water tower
    for k_, wx0 in enumerate(range(-30, 392, 74)):
        wx1 = wx0 + 66
        wb = box(wx0, 240, wx1, 268)
        rf = box(wx0 + 2, 236, wx1 - 2, 240)
        p.put(wb | rf, 'K', 1.8 + nz[wb | rf] * 0.6 + lamps[wb | rf] * 1.6 + sig[wb | rf] * 0.9)
        p.put(box(wx0 + 2, 235, wx1 - 2, 237), 'S', 4.6 + lamps[236, max(0, wx0 + 30)] * 2.0)
        p.put(wb & (np.mod(xx - wx0, 11) == 0), 'K', 1.0)
        p.put(box(wx0 + 26, 244, wx0 + 40, 266), 'K', 1.0)                       # door
        for ax in (wx0 + 12, wx1 - 12):
            p.put(ell(ax, 272, 5, 5), 'K', 1.0 + lamps[272, max(0, min(639, ax))] * 1.2)
    p.put(box(0, 276, 400, 278), 'I', 1.8)
    wt = ell(330, 186, 22, 14) | box(312, 186, 348, 196) | box(318, 196, 322, 232) | box(338, 196, 342, 232)
    p.put(wt, 'K', 2.0 + lamps[wt] * 1.2)
    # yard lamps: tall poles, lamp heads
    for (lx, ly) in YARD_LAMPS:
        p.put(box(lx - 1, ly, lx + 2, FEET), 'I', 2.0 + lamps[ly:FEET, lx - 1:lx + 2].mean())
        p.put(box(lx - 6, ly - 2, lx + 7, ly + 3), 'I', 3.0)
        p.put(box(lx - 4, ly + 3, lx + 5, ly + 5), 'A', 7.0)
    # the repaired signal: lattice mast, ladder, the lamp case with the green lens lit
    sx, sy = YARD_SIGNAL
    mast = box(sx - 3, sy, sx + 3, FEET)
    p.put(mast, 'I', 2.4 + sig[mast] * 2.0)
    lat = mast & (np.mod(yy + xx, 8) < 1)
    p.put(lat, 'I', 1.2)
    p.put(box(sx + 4, sy + 30, sx + 5, FEET), 'I', 3.0)
    for ry in range(sy + 32, FEET, 7):
        p.put(box(sx + 3, ry, sx + 8, ry + 1), 'I', 3.0)
    p.put(box(sx - 9, sy - 9, sx + 10, sy + 12), 'I', 1.6)
    p.put(ell(sx + 0.5, sy, 4, 4), 'G', 6.6)
    p.put(ell(sx + 0.5, sy + 1, 2, 2), 'G', 7.0)
    p.put(box(sx - 11, sy - 11, sx + 12, sy - 9), 'S', 6.0)       # snow on the hood
    # the freight office: brick, snow on the roof edge, dark windows, one dimly lit upstairs, sign
    bx0 = 392
    wall = (xx >= bx0) & (yy >= 116) & (yy < FEET)
    course = np.mod(yy, 6) == 0
    bond = np.mod(xx + (np.floor(yy / 6) % 2) * 6, 12) == 0
    p.put(wall, 'B', 2.0 + nz[wall] * 0.7 + lamps[wall] * 1.6 + win[wall] * 1.2)
    p.put(wall & (course | bond), 'B', 1.0 + lamps[wall & (course | bond)] * 0.8)
    p.put((xx >= bx0) & (yy >= 116) & (yy < 118), 'C', 4.0)
    roof = poly([(bx0 - 8, 118), (640, 118), (640, 88), (bx0 + 30, 92)])
    p.put(roof, 'K', 1.4 + nz[roof] * 0.4)
    p.put(poly([(bx0 - 8, 118), (640, 118), (640, 112), (bx0 - 2, 112)]), 'S', 6.2)
    for i, wx in enumerate((420, 476, 590)):
        ww = box(wx, 150, wx + 22, 190)
        p.put(ww, 'A' if i == 2 else 'K', 2.6 if i == 2 else 0.8 + lamps[ww] * 0.8)
        p.put(box(wx - 2, 190, wx + 24, 193), 'S', 6.0)
        p.put(box(wx + 10, 150, wx + 12, 190), 'B', 1.4)
    p.put(box(470, 204, 584, 216), 'C', 1.4)
    p.put(Q.text_at('ГРУЗОВАЯ КОНТОРА', VW, VH, 476, 207, 's'), 'C', 5.0)
    # the outside stair down to the cellar: a gap in the snow behind the parapet, warm light rising
    x0, x1 = YARD_STAIR
    well = box(x0, 276, x1, FEET + 2)
    p.put(well, 'A', 1.6 + win[well] * 3.0 - (FEET - yy[well]) / 30.0)
    p.put(box(x1, 240, x1 + 14, FEET), 'C', 2.2 + win[240:FEET, x1:x1 + 14].mean() * 1.0)    # stair-head wall
    p.put(box(x1, 236, x1 + 14, 240), 'S', 6.0)
    door = box(x1 - 26, 262, x1 - 6, FEET)
    p.put(door, 'A', 3.4 + win[door] * 2.0)
    # the cellar window in its light well: bars, frost flowers, warm lamp light
    wx0, wy0, wx1, wy1 = YARD_WINDOW
    cw = box(wx0, wy0, wx1, wy1)
    p.put(cw, 'A', 4.6 + Q.noise(VW, VH, 3, 5103)[cw] * 1.6)
    p.put(cw & (np.mod(xx - wx0, 9) < 2), 'I', 1.4)
    p.put(box(wx0 - 3, wy0 - 3, wx1 + 3, wy0), 'C', 3.0)
    frost = cw & (Q.noise(VW, VH, 2, 5105) > 0.7) & ((yy > wy1 - 4) | (xx < wx0 + 4))
    p.put(frost, 'A', 7.4)
    # snow ground, the trodden path to the office, foot prints
    gr = yy >= FEET - 10
    p.put(gr & ~well & ~cw, 'S', 3.6 + nz[gr & ~well & ~cw] * 1.0 + lamps[gr & ~well & ~cw] * 2.0 +
          win[gr & ~well & ~cw] * 1.8 + sig[gr & ~well & ~cw] * 0.6)
    path = gr & (yy > FEET - 4) & (yy < FEET + 5) & ~well & ~cw
    p.put(path, 'S', 2.8 + lamps[path] * 1.6 + win[path] * 1.6)
    p.put((yy >= FEET + 8) & (yy < FEET + 10), 'I', 2.0)                       # a rail half buried
    p.resolve(band=2.0)
    L['yard_signal'] = list(YARD_SIGNAL)
    L['yard_window'] = list(YARD_WINDOW)
    L['yard_stair'] = list(YARD_STAIR)
    L['yard_lamps'] = [list(v) for v in YARD_LAMPS]
    L['yard_towers'] = [list(v) for v in YARD_TOWERS]
    L['feet'] = FEET
    return p.L.c


def yard_parapet():
    """The concrete parapet along the outside stair (drawn over the figures climbing out)."""
    R = Q.ramps(C=CONCRETE, S=SNOWK, I=IRONK, A=AMBER)
    p = C.Paint(VW, VH, R, 'parapet')
    yy, xx = p.yy, p.xx
    x0, x1 = YARD_STAIR
    nz = Q.noise(VW, VH, 6, 5107)
    par = box(x0 - 6, 282, x1, FEET + 12)
    p.put(par, 'C', 2.4 + nz[par] * 0.8 + (xx[par] - x0) / (x1 - x0) * 1.0)
    p.put(box(x0 - 6, 279, x1, 283), 'S', 6.0)
    for px in range(x0, x1, 22):
        p.put(box(px, 262, px + 2, 282), 'I', 3.0)
    p.put(box(x0 - 4, 262, x1, 264), 'I', 3.6)
    p.resolve(band=2.0)
    return p.L.c


def yard_glows():
    """Additive: the signal's green, the yard lamps, the cellar window and the stair's warm light."""
    sx, sy = YARD_SIGNAL
    wx0, wy0, wx1, wy1 = YARD_WINDOW
    x0, x1 = YARD_STAIR
    green = Q.glow_sprite(VW, VH, [(sx, sy, 40, 36, (30, 110, 50), 1.4), (sx, sy, 10, 8, (60, 160, 80), 1.6),
                                   (sx, FEET, 60, 10, (10, 40, 20), 1.5)], 6.0)
    warm = Q.glow_sprite(VW, VH, [((wx0 + wx1) / 2, wy0 + 6, 70, 40, (96, 56, 18), 1.4),
                                  ((x0 + x1) / 2, FEET - 6, 70, 36, (80, 46, 14), 1.4)] +
                         [(x, y + 6, 46, 40, (60, 40, 16), 1.4) for (x, y) in YARD_LAMPS] +
                         [(x, FEET, 50, 10, (40, 26, 10), 1.5) for (x, y) in YARD_LAMPS], 6.0)
    return green, warm


# ======================================================================================= Berlin loop
LOOP_W = 1000
LOOP_SHELTER = (250, 330)
LOOP_CASE = (292, 238, 312, 262)
LOOP_COLUMN = (622, 670)               # the advertising column S 2
LOOP_DOOR = (632, 236, 658, FEET)      # its service door (tall enough for a man)
LOOP_HATCH = (712, 796)
LOOP_LAMP = (344, 128)
MARTA_WIN = (222, 158, 236, 174)
DOME = (560, 200, 150, 104)            # centre x, base y, rx, ry


def berlin_loop(light='dawn'):
    morning = light == 'morning'
    R = Q.ramps(D=DAWN, S=SNOWB, T=STEEL, B=['#0E0D12', '#18161E', '#24212A', '#302C36', '#3E3944', '#4E4854',
                                             '#625A66'],
                W=['#3A2E2A', '#56443A', '#6E5A48', '#8A7258'], V=['#2A2A3A', '#3C3C52', '#545470', '#6E6E8C'],
                N=SODIUM, P=PINE, X=PAPERB, R=INKRED, K=IRONK, G=['#1A2A22', '#26402F', '#3A5C44', '#56805E'])
    W = LOOP_W
    p = C.Paint(W, VH, R, 'loop_' + light)
    yy, xx = p.yy, p.xx
    nz = Q.noise(W, VH, 16, 5201)
    hz = 214
    lampk = 0.4 if morning else 1.0
    lamp = Q.lightfield(W, VH, [(LOOP_LAMP[0], LOOP_LAMP[1] + 30, 150, 1.0, 1.3)]) * lampk
    case = Q.lightfield(W, VH, [((LOOP_CASE[0] + LOOP_CASE[2]) / 2, 250, 60, 1.0, 1.4)])
    sky = yy < hz
    lift = 1.6 if morning else 0.0
    p.put(sky, 'D', 2.2 + lift + (yy[sky] - 40) / (hz - 40) * 5.0 + nz[sky] * 0.4)
    # the dome of the Great Hall, far off, in the haze: a paler silhouette with ribs and the lantern
    dx, db, rx, ry = DOME
    dome = ell(dx, db, rx, ry, W) & (yy < db)
    p.put(dome, 'D', 4.6 + lift * 0.8 + (yy[dome] - (db - ry)) / ry * 0.6 + nz[dome] * 0.2)
    # meridian ribs: x = dx + rx * s_k * sqrt(1 - ((db - y) / ry)^2) (curves meeting at the lantern)
    cosv = np.sqrt(np.clip(1.0 - ((db - yy) / ry) ** 2, 0, 1))
    ribs = np.zeros_like(dome)
    for sk in np.sin(np.linspace(-1.35, 1.35, 11)):
        ribs |= np.abs(xx - (dx + rx * sk * cosv)) < 0.55
    ribs &= dome
    p.put(ribs, 'D', 4.0 + lift * 0.8)
    p.put(dome & (np.abs(yy - (db - ry * 0.35)) < 0.6), 'D', 4.0 + lift * 0.8)
    p.put(dome & C.rim(dome, 1, -1, 2), 'D', 5.6 + lift)
    p.put(box(dx - 14, db - ry - 34, dx + 14, db - ry + 2, W), 'D', 4.2 + lift * 0.8)
    p.put(box(dx - 8, db - ry - 46, dx + 8, db - ry - 34, W), 'D', 4.4 + lift * 0.8)
    # cranes of the axis, blocks of the cleared quarter, all in the haze
    for cx_, h_, jib in ((120, 96, 70), (790, 110, -80), (930, 84, 60)):
        p.put(box(cx_, hz - h_, cx_ + 4, hz, W), 'D', 3.4 + lift * 0.8)
        p.put(p.line([(cx_ - jib * 0.3, hz - h_), (cx_ + jib, hz - h_ + 3)], r=0.9), 'D', 3.4 + lift * 0.8)
        p.put(p.line([(cx_ + jib * 0.9, hz - h_ + 3), (cx_ + jib * 0.9, hz - h_ + 40)], r=0.4), 'D', 3.2 + lift)
    blocks = sky & (yy >= hz - 30) & (np.mod(np.floor(xx / 34) * 11.3, 9) > 2.6 + (hz - yy) / 9.0)
    p.put(blocks, 'D', 3.0 + lift * 0.7)
    # the cleared ground behind the loop: snow, a fence, stacked bricks
    gr = yy >= hz
    u = (yy - hz) / (VH - hz)
    p.put(gr, 'S', 4.4 + lift * 0.6 + u[gr] * 2.0 + nz[gr] * 0.8 + lamp[gr] * 1.6 + case[gr] * 0.8)
    fence = gr & (yy < hz + 18) & (xx > 700) & ((np.mod(xx, 14) < 2) | (yy == hz + 4) | (yy == hz + 12))
    p.put(fence, 'K', 2.2 + lift * 0.4)
    # the exposed party wall of the demolished neighbour: three storeys of wallpaper, rubble
    pw = box(0, 74, 44, FEET, W)
    for i, (y0_, col) in enumerate(((74, 'V'), (146, 'W'), (218, 'G'))):
        band = pw & (yy >= y0_) & (yy < y0_ + 70)
        pat = (np.mod(xx + (np.floor((yy - y0_) / 10) % 2) * 5, 10) < 2) & (np.mod(yy, 10) < 6)
        p.put(band, col, 1.6 + nz[band] * 1.0 + lift * 0.4)
        p.put(band & pat, col, 2.8 + lift * 0.4)
        p.put(band & (yy == y0_), 'B', 1.0)
        p.put(box(2, y0_ + 58, 44, y0_ + 70, W), 'B', 1.6)                        # floor slab scar
    stair = poly([(4, 286), (40, 140), (44, 140), (12, 290)], W)
    p.put(stair, 'B', 1.4)
    rubble = poly([(0, FEET + 4), (0, 266), (20, 270), (40, 280), (60, FEET + 4)], W)
    p.put(rubble, 'B', 2.0 + nz[rubble] * 1.4)
    p.put(rubble & C.rim(rubble, 0, -1), 'S', 6.0 + lift)
    # house No. 9: boarded windows, the boarded door with the sealed notice
    h9 = box(44, 62, 196, FEET, W)
    p.put(h9, 'B', 2.4 + nz[h9] * 0.6 + lamp[h9] * 0.8 + lift * 0.5)
    p.put(box(44, 58, 196, 64, W), 'S', 6.4)
    for wy in (86, 140, 194):
        for wx in (58, 100, 142, 174):
            ww = box(wx, wy, wx + 14, wy + 26, W)
            p.put(ww, 'P', 1.6 + nz[ww] * 0.8)
            p.put(ww & (np.mod(yy - wy, 7) < 1), 'B', 0.8)
            p.put(ww & (np.abs((yy - wy) - (xx - wx) * 1.6) < 1.2), 'P', 3.0)
    dr = box(96, 246, 144, FEET, W)
    p.put(dr, 'P', 2.0 + nz[dr] * 0.8)
    p.put(dr & (np.mod(xx - 96, 12) < 1), 'B', 0.8)
    p.put(dr & ((np.abs((yy - 246) - (xx - 96) * 1.1) < 1.5) | (np.abs((yy - 246) - (144 - xx) * 1.1) < 1.5)), 'P', 3.6)
    note = box(112, 258, 128, 278, W)
    p.put(note, 'X', 6.0 + lift * 0.4)
    p.put(Q.text_at('AMT', W, VH, 114, 261, 's') & note, 'X', 1.6)
    p.put(ell(120, 274, 3, 3, W), 'R', 3.4)                                       # the seal
    # house No. 11: lived in, Marta's lamp in the window
    h11 = box(196, 74, 250, FEET, W)
    p.put(h11, 'B', 3.0 + nz[h11] * 0.6 + lamp[h11] * 1.0 + lift * 0.5)
    p.put(box(196, 70, 250, 76, W), 'S', 6.4)
    for wy in (100, 158, 214):
        ww = box(222, wy, 236, wy + 16, W)
        lit = wy == MARTA_WIN[1]
        p.put(ww, 'N' if lit else 'B', (5.4 if not morning else 4.2) if lit else 1.0)
        p.put(box(220, wy + 16, 238, wy + 18, W), 'S', 6.0)
    # the shelter: iron posts, glass, a small roof, the lit timetable case
    s0, s1 = LOOP_SHELTER
    p.put(box(s0, 222, s1, 228, W), 'K', 2.4)
    p.put(box(s0 - 2, 220, s1 + 2, 222, W), 'S', 6.6)
    for px_ in (s0, s0 + 38, s1 - 3):
        p.put(box(px_, 228, px_ + 3, FEET, W), 'K', 2.0 + lamp[228:FEET, px_:px_ + 3].mean())
    glass = box(s0 + 3, 232, s1 - 3, 286, W)
    p.put(glass & (np.mod(xx + yy, 9) < 1), 'D', 6.0 + lift)
    p.put(box(s0 + 6, 270, s0 + 34, 274, W), 'P', 2.4)                             # bench
    cx0, cy0, cx1, cy1 = LOOP_CASE
    p.put(box(cx0, cy0, cx1, cy1, W), 'X', 6.0 + lift * 0.3)
    p.put(box(cx0 + 2, cy0 + 3, cx1 - 2, cy0 + 4, W) | box(cx0 + 2, cy0 + 7, cx1 - 4, cy0 + 8, W) |
          box(cx0 + 2, cy0 + 11, cx1 - 3, cy0 + 12, W), 'X', 3.0)
    p.put(Q.text_at('74', W, VH, cx0 + 5, cy0 + 15, 's'), 'X', 1.4)
    # the street lamp by the shelter (sodium)
    lx, ly = LOOP_LAMP
    p.put(box(lx - 1, ly, lx + 2, FEET, W), 'K', 2.2)
    p.put(p.line([(lx, ly), (lx + 10, ly - 6), (lx + 18, ly - 4)], r=1.0), 'K', 2.6)
    p.put(box(lx + 14, ly - 4, lx + 24, ly, W), 'N', 6.6 if not morning else 3.0)
    # overhead wire and span poles of the loop
    for px_ in (430, 760):
        p.put(box(px_, 110, px_ + 3, FEET, W), 'K', 2.4)
    p.put(box(330, 126, W, 127, W), 'K', 2.0)
    p.put(p.line([(430, 116), (760, 116)], r=0.4), 'K', 2.0)
    # the advertising column S 2 as the level paints it (env_c4_annex_loop.Street.column; LS_C4_Number n4 cuts to
    # L_C4_AnnexA): a drum with the posters „KONZERT“ (cream) and „KINO“ (red) and the official notice (a neutral
    # seal ring, no insignia), the rounded cap with its finial, the plinth with the warm-air grate.  Morning
    # (LS_C4_Voices, after c4b_inspect_column): the poster torn back from the steel door „S 2“ (v1_door swings it
    # open over this plate).
    c0, c1 = LOOP_COLUMN
    cx = (c0 + c1) / 2.0
    shade = np.abs((xx - cx) / ((c1 - c0) / 2.0))
    lit_c = lamp * 0.6 + lift * 0.3
    cyl = box(c0, 166, c1, FEET - 14, W)
    p.put(cyl, 'B', 4.4 - shade[cyl] * 2.0 + lit_c[cyl])
    for (py0, py1, col, tone, txt) in ((172, 210, 'X', 6.0, 'KONZERT'), (212, 244, 'R', 3.4, 'KINO'),
                                       (246, 282, 'X', 5.2, None)):
        post = box(c0 + 1, py0, c1 - 1, py1, W)
        p.put(post, col, tone - shade[post] * (2.6 if col == 'X' else 1.4) + lit_c[post])
        p.put(post & (yy == py0), 'B', 2.0)                                          # the paste seam
        ink, ink_t = ('B', 1.0) if col == 'X' else ('X', 7.0)
        if txt:
            tm = Q.text(txt, 's', 1)
            p.put(Q.place(tm, W, VH, int(round(cx - tm.shape[1] / 2.0)), py0 + 1), ink, ink_t)
        for k_ in range(4):                                                         # the small print
            ty = py0 + (13 if txt else 17) + k_ * 4
            if ty < py1 - 3:
                ln = box(c0 + 8, ty, c1 - 8 - (k_ % 2) * 7, ty + 1, W)
                p.put(ln, ink, ink_t + (0.6 if col == 'X' else -1.2))
    seal = ell(cx, 253, 4.2, 4.2, W) & ~ell(cx, 253, 2.2, 2.2, W)                   # the notice's seal ring
    p.put(seal, 'B', 1.6)
    p.put(poly([(c1 - 9, 212), (c1 - 1, 212), (c1 - 1, 220)], W), 'X', 6.6)        # a poster corner curling
    # the cap: crown ring, ribbed band, the rounded dome, snow, the finial
    p.put(box(c0 - 4, 162, c1 + 4, 166, W), 'B', 5.2 + lift * 0.3)
    band = box(c0 - 3, 152, c1 + 3, 162, W)
    p.put(band, 'B', 3.0 + lift * 0.3)
    p.put(band & (np.mod(xx - c0, 4) == 0), 'B', 1.8)
    dw = (c1 + 4) - (c0 - 4)
    hh = np.round(14 * np.sin(np.pi * (np.clip(xx - (c0 - 4), 0, dw - 1) + 0.5) / dw) ** 0.6)
    dome = (xx >= c0 - 4) & (xx < c1 + 4) & (yy < 152) & (yy >= 152 - hh)
    p.put(dome, 'B', 3.4 + (xx[dome] < cx) * 0.9 + lift * 0.3)
    p.put(dome & ~np.roll(dome, 1, axis=0), 'S', 7.2)                               # snow along the dome
    p.put(box(c0 - 4, 161, c1 + 4, 162, W), 'S', 7.0)
    p.put(box(int(cx) - 1, 128, int(cx) + 2, 139, W), 'T', 4.2)
    p.put(box(int(cx) - 2, 127, int(cx) + 3, 129, W), 'T', 5.6)
    # the plinth ring with the warm-air grate at its foot
    plinth = box(c0 - 3, FEET - 14, c1 + 3, FEET, W)
    p.put(plinth, 'B', 3.2 - shade[plinth] * 0.8 + lit_c[plinth])
    p.put(box(c0 - 3, FEET - 14, c1 + 3, FEET - 13, W), 'B', 5.0)
    grate = box(c0 + 8, FEET - 11, c1 - 8, FEET - 2, W)
    p.put(grate & (np.mod(xx, 2) == 0), 'N', 3.2 if not morning else 2.6)
    p.put(grate & (np.mod(xx, 2) == 1), 'K', 1.0)
    if morning:
        # the poster torn back: the steel door of the ventilation structure, stencilled S 2
        d0, dy0, d1, dy1 = LOOP_DOOR
        door = box(d0, dy0, d1, dy1, W)
        p.put(door, 'T', 3.0 + nz[door] * 0.6 - shade[door] * 0.8)
        p.put(box(d0, dy0, d1, dy0 + 1, W) | box(d0, dy0, d0 + 1, dy1, W) | box(d1 - 1, dy0, d1, dy1, W), 'T', 1.4)
        p.put(box(d0 + 1, dy0 + 1, d1 - 1, dy0 + 2, W), 'T', 5.4)
        st_ = Q.text('S 2', 's', 1)
        p.put(Q.place(st_, W, VH, int(round(cx - st_.shape[1] / 2.0)), dy0 + 5), 'X', 6.8)
        p.put(box(d1 - 5, 268, d1 - 3, 276, W), 'T', 6.0)
        flap = poly([(d0, dy0 - 3), (d0 - 9, dy0 + 5), (d0 - 7, dy0 + 34), (d0, dy0 + 38)], W)
        p.put(flap, 'X', 4.2 + lit_c[flap])
        p.put(flap & C.rim(flap, -1, 0), 'X', 6.4)
    # the freight hatch of the shaft with the stencilled crates, a few cards in the snow
    h0, h1 = LOOP_HATCH
    p.put(box(h0, FEET - 6, h1, FEET + 2, W), 'T', 3.0)
    p.put(box(h0, FEET - 6, h1, FEET - 5, W), 'T', 5.6)
    for (cx_, cy_) in ((h0 + 6, FEET - 32), (h0 + 44, FEET - 32), (h0 + 24, FEET - 58)):
        cb = box(cx_, cy_, cx_ + 36, cy_ + 26, W)
        p.put(cb, 'P', 3.6 + nz[cb] * 1.2 + lift * 0.3)
        p.put(cb & (np.mod(yy - cy_, 9) < 1), 'P', 1.8)
        p.put(box(cx_, cy_, cx_ + 36, cy_ + 2, W), 'S', 7.0)
        p.put(Q.stencil_mask('C-17/45', 6, W, VH, cx_ + 4, cy_ + 10, width=2.0), 'B', 1.0)
    # snow ground in front, the loop's rails
    st = yy >= FEET - 6
    p.put(st & ~box(h0, FEET - 6, h1, FEET + 2, W), 'S', 4.8 + lift * 0.5 + nz[st & ~box(h0, FEET - 6, h1, FEET + 2, W)]
          * 0.8 + lamp[st & ~box(h0, FEET - 6, h1, FEET + 2, W)] * 2.2 + case[st & ~box(h0, FEET - 6, h1, FEET + 2, W)])
    for ry in (FEET + 4, FEET + 11):
        rail = (yy >= ry) & (yy < ry + 2) & (xx > 300)
        p.put(rail, 'K', 3.6 + lamp[rail] * 2.0)
        p.put(rail & (yy == ry), 'K', 5.4)
    curve = p.line([(300, FEET + 4), (282, FEET + 10), (268, FEET + 24)], r=1.0) | \
        p.line([(300, FEET + 11), (288, FEET + 18), (280, FEET + 28)], r=1.0)
    p.put(curve, 'K', 3.8)
    p.resolve(band=2.0)
    L['loop_w'] = W
    L['loop_shelter'] = list(LOOP_SHELTER)
    L['loop_case'] = list(LOOP_CASE)
    L['loop_column'] = list(LOOP_COLUMN)
    L['loop_door'] = list(LOOP_DOOR)
    L['loop_lamp'] = list(LOOP_LAMP)
    L['marta_window'] = list(MARTA_WIN)
    return p.L.c


def loop_glow(light='dawn'):
    k = 0.45 if light == 'morning' else 1.0
    lx, ly = LOOP_LAMP
    cx0, cy0, cx1, cy1 = LOOP_CASE
    mx0, my0, mx1, my1 = MARTA_WIN
    return Q.glow_sprite(LOOP_W, VH, [(lx + 19, ly, 56 * k + 10, 44 * k + 8, (int(110 * k), int(64 * k), 20), 1.4),
                                      (lx + 19, FEET, 90, 14, (int(60 * k), int(36 * k), 10), 1.5),
                                      ((cx0 + cx1) / 2, (cy0 + cy1) / 2, 26, 22, (50, 52, 40), 1.5),
                                      ((mx0 + mx1) / 2, (my0 + my1) / 2, 18, 14, (int(70 * k), int(44 * k), 14), 1.5)],
                         6.0)


# ======================================================================================= the tram
TRAM_W, TRAM_H = 248, 96


def tram(face='left', ilse_hand=False, lit=1.0):
    """Two-axle motor car of line 74 No. 3518, side view, `face` = driving direction, in the livery of the level's
    tram (env_c4_annex_loop.Street.tram -- LS_C4_Number n4 cuts straight to L_C4_AnnexA): cream body, the dark belt
    rail at the window sill, a red pinstripe above the skirt, the fleet number 3518, a lantern roof with lit
    clerestory lights and the bow collector.  Marta in the cab at the front, Ilse at the last window at the rear
    (her hand on the glass when `ilse_hand`).  Drawn facing left, then mirrored WITHOUT mirroring the line board
    and the fleet number."""
    w, h = TRAM_W, TRAM_H
    R = Q.ramps(Y=CREAM, K=IRONK, N=SODIUM, D=DAWN, U=NAVYB, F=['#3A2826', '#6A4A40', '#9A7060', '#C89C84',
                                                                   '#E8C4A8'],
                H=['#2A2016', '#4A3A22', '#7A6232', '#A88A4A'], X=PAPERB, R=INKRED, T=STEEL)
    p = C.Paint(w, h, R, 'tram')
    yy, xx = p.yy, p.xx
    nz = Q.noise(w, h, 8, 5301)
    # body: cream upper and lower panels (the light falls off towards the skirt)
    body = Q.C.rrect_mask(w, h, 4, 22, w - 4, h - 12, 6)
    p.put(body, 'Y', 4.3 + nz[body] * 0.4 - (yy[body] - 22) / 62.0 * 1.1)
    edge = body & ((xx < 7) | (xx > w - 8))
    p.put(edge, 'Y', 3.2 + nz[edge] * 0.3)                                           # the rounded ends
    p.put(body & (yy == 22), 'Y', 5.4)                                               # the cant rail catches the sky
    # lantern roof: the roof slab, the raised clerestory with its lit lights, snow on both
    roof = Q.C.rrect_mask(w, h, 8, 17, w - 8, 24, 4)
    p.put(roof, 'T', 3.4 + nz[roof] * 0.4)
    lant = box(36, 11, w - 36, 17, w, h)
    p.put(lant, 'T', 2.6 + nz[lant] * 0.3)
    for lx_ in range(40, w - 42, 8):
        p.put(box(lx_, 13, lx_ + 4, 15, w, h), 'N', 5.0 * lit + 0.6)
    p.put(lant & (yy == 11), 'D', 9.0)
    p.put(roof & (yy == 17) & ((xx < 36) | (xx >= w - 36)), 'D', 9.0)
    # the bow collector up to the wire
    p.put(box(112, 8, 136, 11, w, h), 'K', 3.0)
    p.put(p.line([(116, 8), (121, 1)], r=0.6) | p.line([(132, 8), (127, 1)], r=0.6), 'K', 4.0)
    p.put(box(118, 0, 131, 2, w, h), 'K', 4.6)
    # windows: front cab, five saloon windows, the rear window
    wins = [(8, 30, 30, 58)] + [(40 + i * 34, 30, 68 + i * 34, 56) for i in range(5)] + [(214, 30, 240, 58)]
    for i, (a0, b0, a1, b1) in enumerate(wins):
        ww = box(a0, b0, a1, b1, w, h)
        p.put(ww, 'N', (3.4 + nz[ww] * 0.8) * lit + 0.6)
        p.put(ww & (yy == b0), 'N', 5.8 * lit + 0.5)
        p.put(box(a0 - 1, b0 - 1, a1 + 1, b0, w, h), 'Y', 2.4)
        p.put(box(a0, b1, a1, b1 + 1, w, h), 'Y', 2.0)
    # Marta in the cab: cap with the 74 badge, short dark-blond hair, red cheeks, navy coat
    p.put(ell(22, 44, 6, 7, w, h), 'F', 3.0)
    p.put(ell(23, 45, 2, 2, w, h), 'F', 4.0)
    p.put(box(14, 36, 30, 40, w, h) | ell(22, 37, 8, 3, w, h), 'U', 2.4)
    p.put(box(21, 37, 24, 39, w, h), 'H', 3.6)
    p.put(box(16, 40, 18, 46, w, h), 'H', 2.6)
    p.put(box(12, 50, 32, 58, w, h), 'U', 2.0)
    # Ilse at the last window: a child's head, dark plaits, her breath on the glass
    p.put(ell(228, 47, 5, 6, w, h), 'F', 3.2)
    p.put(ell(226, 44, 6, 4, w, h) & (yy < 45), 'H', 1.6)
    p.put(box(222, 46, 224, 54, w, h), 'H', 1.4)
    p.put(box(220, 52, 236, 58, w, h), 'R', 2.0)
    if ilse_hand:
        p.put(ell(219, 46, 2.6, 3.4, w, h), 'F', 4.2)
    fog = box(216, 50, 238, 58, w, h) & (Q.noise(w, h, 3, 5303) > 0.5)
    p.put(fog, 'D', 8.0)
    # door seams, then the dark belt rail at the sill, the red pinstripe above the skirt
    for dx_ in (36, 200):
        p.put(box(dx_, 30, dx_ + 1, 82, w, h), 'Y', 1.8)
    belt = body & (yy >= 59) & (yy < 63)
    p.put(belt, 'T', 1.6 + nz[belt] * 0.3)
    p.put(belt & (yy == 59), 'T', 3.4)
    p.put(body & (yy == 76), 'R', 2.8)
    # the line board over the cab (lit 74 on black, as in the level), headlight, tail lamp
    p.put(box(6, 16, 34, 26, w, h), 'K', 1.0)
    p.put(Q.place(Q.text('74', 'l', 1), w, h, 14, 18), 'N', 6.4 * lit + 0.4)
    p.put(ell(6, 70, 3, 3, w, h), 'N', 7.0 * lit)
    p.put(box(w - 7, 64, w - 4, 67, w, h), 'R', 4.0)
    # wheel skirts, axles, the underframe
    for ax in (64, 184):
        p.put(ell(ax, 86, 16, 8, w, h) & (yy > 80), 'K', 1.0)
        p.put(ell(ax, 88, 10, 8, w, h), 'K', 2.0)
    p.put(box(4, 82, w - 4, 86, w, h), 'K', 1.4)
    p.resolve(band=2.0)
    out = p.L.c
    if face == 'right':
        out = out[:, ::-1].copy()
        # re-draw the line board unmirrored
        bd = np.zeros((h, w), bool)
        bd[16:26, w - 34:w - 6] = True
        out[bd, :3] = Q.hexrgb(IRONK[2]).astype(np.uint8)
        t = Q.place(Q.text('74', 'l', 1), w, h, w - 26, 18)
        out[t, :3] = Q.hexrgb(SODIUM[6] if lit > 0.8 else SODIUM[5]).astype(np.uint8)
    # the fleet number on the lower panel towards the rear, never mirrored
    num = Q.text('3518', 's', 1)
    nx = TRAM_NUMBER_X if face != 'right' else w - TRAM_NUMBER_X - num.shape[1]
    out[Q.place(num, w, h, nx, 63), :3] = Q.hexrgb(IRONK[4]).astype(np.uint8)
    L['tram_size'] = [w, h]
    return out


TRAM_NUMBER_X = 158                    # 3518 on the lower panel (level: t0 + 154 of the 242 px car)


# ======================================================================================= the siding hall
SIDING_LAMP = (330, 96)
SIDING_WAGON = (196, 150, 456, 278)    # x0, y0 (roof), x1, y1 (sole bar) of wagon 24 318


def siding(lit=True):
    R = Q.ramps(K=KNIGHT, B=BRICK, C=CONCRETE, I=IRONK, A=AMBER, R=RUST, W=CREAM, D=DAWN,
                Y=['#0E0F12', '#1A1C20', '#2A2C30', '#3E4044', '#5A5C5E', '#7E7E7C', '#A6A49C', '#D0CCC0'])
    p = C.Paint(VW, VH, R, 'siding_%d' % int(lit))
    yy, xx = p.yy, p.xx
    nz = Q.noise(VW, VH, 12, 5401)
    lx, ly = SIDING_LAMP
    lamp = Q.lightfield(VW, VH, [(lx, ly + 90, 300, 1.0, 1.25), (lx, FEET, 200, 0.6, 1.4)]) * (1.0 if lit else 0.0)
    gate = Q.lightfield(VW, VH, [(640, 220, 160, 1.0, 1.6)])
    # the brick vault
    vault = yy < FEET
    arc = (yy < 150 - 70 * np.sqrt(np.clip(1 - ((xx - 320) / 420.0) ** 2, 0, 1)) + 40)
    p.put(vault, 'B', 0.8 + nz[vault] * 0.6 + lamp[vault] * 3.2 + gate[vault] * 0.6)
    course = vault & (np.mod(yy + np.floor(xx / 40) * 0, 7) == 0)
    p.put(course, 'B', 0.5 + lamp[course] * 2.0)
    p.put(arc, 'K', 0.6 + lamp[arc] * 1.6)
    ribs = vault & (np.abs(np.mod(xx, 160) - 80) < 4) & (yy < 200)
    p.put(ribs, 'B', 1.4 + lamp[ribs] * 2.6)
    # the shut portal at the right: plank gate, blue light through the cracks
    pg_ = box(560, 120, 640, FEET)
    p.put(pg_, 'Y', 1.2 + nz[pg_] * 0.6 + lamp[pg_] * 1.0)
    cr = pg_ & (np.mod(xx, 12) == 0)
    p.put(cr, 'D', 4.0 + (yy[cr] - 120) / 180.0 * 2.0)
    # floor: concrete, the two tracks
    fl = yy >= FEET - 22
    p.put(fl, 'C', 1.4 + nz[fl] * 0.8 + lamp[fl] * 3.0)
    for ry in (FEET - 2, FEET + 8):
        rail = (yy >= ry) & (yy < ry + 2)
        p.put(rail, 'I', 3.0 + lamp[rail] * 3.0)
    # the paint stand: board with stencils, bucket of red-brown
    p.put(box(476, 200, 530, 270), 'Y', 2.0 + lamp[200:270, 476:530].mean() * 2.0)
    for i, (sx_, sy_) in enumerate(((480, 206), (504, 206), (480, 232), (504, 232))):
        p.put(box(sx_, sy_, sx_ + 20, sy_ + 20), 'I', 3.6 + lamp[sy_:sy_ + 20, sx_:sx_ + 20].mean() * 2.0)
        p.put(Q.stencil_mask('4%d' % (2 + i), 8, VW, VH, sx_ + 3, sy_ + 6, width=2.0), 'K', 0.8)
    p.put(box(488, 276, 506, 296), 'I', 2.4)
    p.put(box(488, 276, 506, 279), 'R', 4.0)
    # the conversion kit: enamel plates, stove-pipe elbows, bench boards
    heap = poly([(80, FEET - 2), (96, 262), (140, 252), (168, 270), (176, FEET - 2)])
    p.put(heap, 'Y', 1.6 + nz[heap] * 1.4 + lamp[heap] * 2.0)
    for (ex, ey) in ((110, 264), (138, 258), (154, 274)):
        p.put(ell(ex, ey, 8, 4), 'W', 3.0 + lamp[ey, ex] * 2.0)
    # wagon 24 318 / C-17/45: planks, the fresh stencil, the stove-pipe hole, the door half open (dark)
    x0, y0, x1, y1 = SIDING_WAGON
    side = box(x0, y0, x1, y1)
    v = np.mod(yy - y0, 10)
    p.put(side, 'R', 2.4 + nz[side] * 0.6 + lamp[side] * 3.0 - (v[side] < 1) * 1.2)
    roof = poly([(x0 - 6, y0), (x1 + 6, y0), (x1 - 4, y0 - 14), (x0 + 4, y0 - 14)])
    p.put(roof, 'I', 1.6 + lamp[roof] * 2.4)
    p.put(box(x0 + 60, y0 - 24, x0 + 68, y0 - 12), 'I', 1.2 + lamp[y0 - 24:y0 - 12, x0 + 60:x0 + 68].mean())
    door = box(x0 + 120, y0 + 14, x0 + 166, y1 - 4)
    p.put(door, 'K', 0.4)
    p.put(box(x0 + 166, y0 + 14, x0 + 200, y1 - 4), 'R', 3.0 + lamp[y0 + 20, x0 + 180] * 2.4)
    p.put(box(x0 + 166, y0 + 14, x0 + 168, y1 - 4), 'R', 1.2)
    st = Q.stencil_mask('C-17/45', 12, VW, VH, x0 + 16, y0 + 40, width=1.9)
    p.put(st, 'W', 4.4 + lamp[st] * 1.6)
    p.put(box(x0, y1, x1, y1 + 8), 'I', 1.4 + lamp[y1:y1 + 8, x0:x1].mean() * 1.6)
    for ax in (x0 + 40, x1 - 40):
        p.put(ell(ax, y1 + 12, 13, 13), 'I', 0.8 + lamp[y1 + 12, ax] * 1.6)
        p.put(ell(ax, y1 + 12, 4, 4), 'I', 2.4 + lamp[y1 + 12, ax] * 2.0)
    # the lamp: cable from the vault, enamel shade, bulb
    p.put(box(lx, 40, lx + 1, ly - 6), 'I', 2.0)
    shade = poly([(lx - 14, ly), (lx + 15, ly), (lx + 6, ly - 8), (lx - 5, ly - 8)])
    p.put(shade, 'I', 3.0 + (1.6 if lit else 0.0))
    p.put(ell(lx + 0.5, ly + 2, 4, 3), 'A', 7.6 if lit else 1.2)
    p.resolve(band=2.0)
    L['siding_lamp'] = list(SIDING_LAMP)
    L['siding_wagon'] = list(SIDING_WAGON)
    return p.L.c


def siding_glow():
    lx, ly = SIDING_LAMP
    return Q.glow_sprite(VW, VH, [(lx, ly + 4, 120, 120, (90, 64, 30), 1.3), (lx, ly + 2, 16, 12, (120, 90, 50), 1.6),
                                  (lx, FEET, 160, 22, (40, 30, 14), 1.5)], 6.0)


def build(w):
    w('places/yard.png', karsk_yard())
    w('places/yard_parapet.png', yard_parapet())
    g, wm = yard_glows()
    w('places/yard_green.png', g)
    w('places/yard_warm.png', wm)
    w('places/loop_dawn.png', berlin_loop('dawn'))
    w('places/loop_morning.png', berlin_loop('morning'))
    w('places/loop_glow_dawn.png', loop_glow('dawn'))
    w('places/loop_glow_morning.png', loop_glow('morning'))
    w('places/tram_left.png', tram('left'))
    w('places/tram_right.png', Q.sheet([tram('right', False, 0.7), tram('right', True, 0.7)]))
    w('places/siding_lit.png', siding(True))
    dark = siding(False).copy()
    dark[..., :3] = (dark[..., :3].astype(np.float32) * 0.5).astype(np.uint8)
    w('places/siding_dark.png', dark)
    w('places/siding_glow.png', siding_glow())
    w('places/breath.png', Q.K.puff_sheet(6, 20, 16, ['#46556A', '#5E6D7B', '#7E8B96'], 5501, grow=(0.2, 0.42),
                                          thin=0.7))
    w('places/steam.png', Q.K.puff_sheet(8, 48, 40, ['#3C4C68', '#4E5F7C', '#64768F', '#7E8EA4'], 5503,
                                         grow=(0.26, 0.5), thin=0.5))
    w('places/steam_light.png', Q.K.puff_sheet(8, 48, 40, ['#7E8EA4', '#9CAABB', '#BFC9D5', '#E2E8EE'], 5505,
                                               grow=(0.26, 0.5), thin=0.55))
    L['feet'] = FEET
