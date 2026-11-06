"""env_veltrava_cine_tohall -- art of LS_C3_ToHall (owner: cinematics stream).

k1  the cast-iron platform clock of Bahnhof Veltrava, 9:39:57, seen from below the glazed canopy; beyond
    the fretwork valance the misty morning over the tracks, the green Soviet carriages, the old town.
k2  the gilded Jugendstil clock above the doors of the Grosser Saal in the palais of the commission, 9:40;
    the same dial geometry (centre, radius, index angles) so the match cut lands on the same hands.
Both dials share CENTER / DIAL_R with scenes/cinematics/ch3_tohall/ch3_tohall.gd (checked by the test via
assets/cinematics/ch3/layout.json).  Called by env_veltrava_cine.main(); every function returns RGBA arrays.
"""
from __future__ import annotations

import math

import numpy as np

import env_veltrava_cine as C
import env_veltrava_cine_kit as K
import pg

VW, VH = C.VW, C.VH
V = C.V
PL = C.P                     # palais palette
CENTER = (320, 170)
DIAL_R = 50
CASE_R = 61
LAYOUT = C.LAYOUT.setdefault('tohall', {})
LAYOUT.update({'center': list(CENTER), 'dial_r': DIAL_R})

GLASS = ['#3A4859', '#4F5E70', '#687789', '#8593A3', '#95A0B8', '#A1AAB7', '#B6B9C9', '#C2C9D2', '#D3CDD3',
         '#DEE2E7']
IRON = ['#070A12', '#0C111C', '#121A26', '#1A2431', '#1E2836', '#2A3646', '#3A4859', '#4F5E70', '#687789']
GREEN = ['#070A12', '#0C111C', '#121A26', '#1E302E', '#2B4541', '#3D5E57', '#56796E', '#739585']
DIAL = ['#687789', '#8593A3', '#A1AAB7', '#C2C9D2', '#DEE2E7', '#F2F3F5']
MIST = ['#4F5E70', '#687789', '#7684A0', '#8593A3', '#95A0B8', '#A1AAB7', '#B6B9C9', '#C2C9D2', '#D3CDD3']


def _grid():
    return np.mgrid[0:VH, 0:VW].astype(np.float32)


# =========================================================================== k1: the station clock
def k1_bg():
    R = C.ramps(G=GLASS, I=IRON, M=MIST, P=GREEN, L=V['lamp'], C=V['cream'], R=V['red'], W=V['snow'])
    p = C.Paint(VW, VH, R, 'k1_bg')
    yy, xx = p.yy, p.xx
    allm = np.ones((VH, VW), bool)
    # ---- outside, beyond the canopy edge: the morning mist over the tracks (brightest band at the horizon)
    hz = 258.0
    mist_t = 7.4 - np.clip(np.abs(yy - hz) / 60.0, 0, 1) * 2.6 + (pg.value_noise(VW, VH, 40, 601, 3) - 0.5) * 0.7
    p.put(allm, 'M', mist_t)
    # old town in the mist (far, pale): domes, a spire, the castle hill on the right
    sky = p.box(0, 0, VW, VH)
    rng = np.random.default_rng(602)
    town = np.zeros((VH, VW), bool)
    x = -10.0
    while x < VW:
        w_ = rng.uniform(14, 34)
        h_ = rng.uniform(6, 15)
        town |= p.box(x, hz - h_, x + w_, hz + 4)
        if rng.random() < 0.35:
            town |= p.poly([(x, hz - h_), (x + w_ / 2, hz - h_ - rng.uniform(4, 8)), (x + w_, hz - h_)])
        x += w_ + rng.uniform(-3, 3)
    for (dx, dr) in ((96, 9), (452, 12), (566, 7)):
        town |= p.ell(dx, hz - 16, dr, dr * 0.9) & (yy < hz - 14)
        town |= p.box(dx - dr * 0.8, hz - 16, dx + dr * 0.8, hz)
        town |= p.box(dx - 0.5, hz - 16 - dr - 6, dx + 1.5, hz - 16 - dr + 1)
    town |= p.poly([(196, hz), (203, hz - 44), (210, hz)]) | p.box(198, hz - 22, 209, hz)
    town |= p.poly([(600, hz), (612, hz - 26), (640, hz - 28), (640, hz)])
    p.put(town & sky, 'M', 4.6 + np.clip((hz - yy) / 40, 0, 1) * 0.3)
    p.put(town & ~shift_m(town, 0, -1), 'M', 5.8)                              # snow on the roofs
    # the far platform: its canopy, columns and the dark gap under it
    p.put(p.box(0, 262, VW, 266), 'I', 5.6)
    p.put(p.box(0, 261, VW, 262), 'W', 1.6)
    p.put(p.box(0, 266, VW, 274), 'M', 2.2)
    for cx in range(14, VW, 46):
        p.put(p.box(cx, 266, cx + 2, 276), 'I', 5.0)
    # track bed: snow, rails, sleepers (fore-shortened)
    bed = p.box(0, 276, VW, VH)
    p.put(bed, 'W', 2.0 + np.clip((yy - 276) / 40, 0, 1) * 1.2 + (pg.value_noise(VW, VH, 12, 603, 2) - 0.5) * 0.8)
    for ry, th in ((280, 1), (286, 1), (296, 1), (306, 2)):
        p.put(p.box(0, ry, VW, ry + th), 'I', 5.2)
        p.put(p.box(0, ry - 1, VW, ry), 'W', 3.6)
    for k in range(0, VW, 9):
        p.put(p.box(k, 300, k + 5, 302), 'I', 6.4)
    # the Soviet carriage standing on the near track (left), steam heating hoses, a lit window
    car = p.box(0, 246, 236, 300)
    p.put(car, 'P', 3.2 + np.clip((yy - 246) / 54, 0, 1) * -1.0)
    p.put(p.box(0, 244, 236, 248), 'I', 5.0)
    p.put(p.box(0, 243, 236, 245), 'W', 3.0)                                  # snow on the roof
    for k, wx in enumerate(range(12, 230, 22)):
        win = p.box(wx, 256, wx + 13, 270)
        p.put(win, 'I', 3.4)
        lit = wx in (34, 56, 122, 188)
        if lit:                                          # round 10: lit compartments, white half-curtains
            p.put(p.box(wx + 1, 257, wx + 12, 269), 'L', 2.4 + (k % 2) * 0.5, emis=True)
            p.put(p.box(wx + 4, 258, wx + 9, 261), 'L', 4.0, emis=True)          # the compartment lamp
        else:
            p.put(p.box(wx + 1, 257, wx + 12, 269), 'M', 5.0)
            p.put(p.box(wx + 1, 257, wx + 12, 259), 'M', 6.4)                    # the sky in the upper pane
        p.put(p.box(wx + 1, 263, wx + 12, 269), 'W', 3.6 if lit else 2.8)       # the lower half-curtain
        p.put(p.box(wx + 1, 263, wx + 12, 264), 'W', 4.6)
        p.put(p.box(wx + 6, 256, wx + 7, 270), 'I', 3.0)                          # the sash bar
    # the route board under the windows, the conductor's door with its handrails, the heater chimney with snow
    p.put(p.box(70, 276, 176, 282), 'I', 4.6)
    p.put(K.text_at('МОСКВА · KORDON-17 · VELTRAVA', VW, VH, 123, 277, font='s', center=True) & p.box(70, 276, 176, 282),
          'W', 5.0)
    p.put(p.box(214, 252, 232, 290), 'P', 2.4)
    p.put(p.box(216, 256, 230, 266), 'M', 5.2)
    for hx in (212, 233):
        p.put(p.box(hx, 258, hx + 1, 288), 'W', 4.4)
    p.put(p.box(196, 236, 202, 245), 'I', 2.6)
    p.put(p.box(195, 235, 203, 236), 'W', 5.0)
    LAYOUT['k1_chimney'] = [199, 234]
    p.put(p.box(0, 288, 236, 291), 'P', 1.2)
    p.put(p.box(0, 291, 236, 300), 'I', 2.0)
    p.put(p.box(237, 270, 241, 296), 'I', 3.0)                                # gangway bellows
    # a signal at the right with its red lamp
    p.put(p.box(584, 214, 586, 300), 'I', 3.0)
    p.put(p.ell(585, 240, 4, 4), 'I', 1.0)
    p.put(p.ell(585, 240, 2.2, 2.2), 'R', 3.0, emis=True)
    # ---- the canopy (glazed roof seen from below); rafters converge toward the far edge
    roof = p.box(0, 0, VW, 226)
    vp = (320.0, 640.0)
    # frosted panes under a skin of snow: dim, a slow wash toward the open edge, a few clear panes
    wash = pg.value_noise(VW, VH, 70, 604, 2)
    pane_t = 2.6 + np.clip((yy - 70) / 156, 0, 1) ** 1.4 * 2.6 + (wash - 0.5) * 0.9
    p.put(roof, 'G', pane_t)
    # snow drifted against every purlin darkens the glass just above it (ragged top edge)
    drift_n = pg.value_noise(VW, 8, 6, 605, 2)
    # purlins (horizontal iron), spacing shrinking toward the far edge
    for i, (py, th) in enumerate(((52, 6), (104, 5), (146, 4), (176, 3), (198, 3), (213, 2))):
        dh = (3 + drift_n[i] * 7 * (1.0 - i * 0.12)).astype(int)
        drift = (yy >= py - dh[None, :]) & (yy < py) & roof
        p.add(drift, -1.4)
        p.add(drift & ~C.shift(drift, 0, -1), 0.8)
        b = p.box(0, py, VW, py + th)
        p.put(b, 'I', 1.6)
        p.put(p.box(0, py + th - 1, VW, py + th), 'I', 3.4)
    # rafters
    for k in range(-7, 8):
        xt = 320 + k * 64
        xb = vp[0] + (xt - vp[0]) * (vp[1] - 226) / (vp[1] - 46)
        w_top = 4
        pts = [(xt - w_top / 2, 46), (xt + w_top / 2, 46), (xb + 1, 226), (xb - 1, 226)]
        m = p.poly(pts) & roof
        p.put(m, 'I', 1.4)
        p.put(m & ~shift_m(m, -1, 0), 'I', 3.0)
    # the transverse lattice girder the clock hangs from
    g0, g1 = 88, 106
    p.put(p.box(0, g0, VW, g0 + 3), 'I', 1.2)
    p.put(p.box(0, g0 + 3, VW, g0 + 4), 'I', 3.2)
    p.put(p.box(0, g1 - 3, VW, g1), 'I', 1.0)
    p.put(p.box(0, g1 - 1, VW, g1), 'I', 3.6)
    for k in range(-1, 40):
        x0 = k * 18
        for (a, b) in (((x0, g0 + 3), (x0 + 9, g1 - 3)), ((x0 + 9, g1 - 3), (x0 + 18, g0 + 3))):
            m = p.line([a, b], 0.9) & p.box(0, g0 + 3, VW, g1 - 3)
            p.put(m, 'I', 1.4)
    for k in range(0, VW, 6):
        p.px(k + 2, g0 + 1, 'I', 4.0)
        p.px(k + 2, g1 - 2, 'I', 4.0)
    # the fretwork valance along the canopy edge, dark against the bright mist
    fas = p.box(0, 218, VW, 231)
    p.put(fas, 'I', 1.6 + np.clip((yy - 218) / 13, 0, 1) * 0.6)
    p.put(p.box(0, 218, VW, 219), 'I', 3.0)
    teeth = np.zeros((VH, VW), bool)
    for k in range(-1, VW // 10 + 2):
        cx = k * 10 + 5
        teeth |= p.poly([(cx - 5, 231), (cx + 5, 231), (cx + 2, 240), (cx, 244), (cx - 2, 240)])
    holes = np.zeros((VH, VW), bool)
    for k in range(-1, VW // 10 + 2):
        holes |= p.ell(k * 10 + 5, 235.5, 1.0, 1.3)
        if k % 2 == 0:
            holes |= p.ell(k * 10 + 10, 224.5, 1.6, 2.0)
    p.put(teeth & ~holes, 'I', 1.2)
    p.put(holes & (fas | teeth), 'M', 4.6)
    # an enamel platform sign on two rods (left) and an unlit pendant lamp (right)
    for rx in (58, 132):
        p.put(p.box(rx, 106, rx + 1, 150), 'I', 2.0)
    sign = p.box(42, 150, 150, 178)
    p.put(sign, 'P', 3.0)
    p.put(sign & ~kit_erode(sign, 1), 'W', 2.6)
    p.put(K.text_at('3', VW, VH, 54, 155, font='l') & sign, 'W', 3.6)
    p.put(K.text_at('GLEIS · ПУТЬ · VOIE', VW, VH, 70, 157, font='s') & sign, 'W', 3.2)
    p.put(K.text_at('KORDON · MOSKVA', VW, VH, 70, 167, font='s') & sign, 'W', 2.4)
    for (lx, ly) in ((264, 120), (430, 126)):                      # round 10: more hanging lamps
        p.put(p.box(lx, 106, lx + 1, ly), 'I', 2.0)
        sh2 = p.poly([(lx - 11, ly + 8), (lx + 12, ly + 8), (lx + 7, ly), (lx - 6, ly)])
        p.put(sh2, 'P', 2.4 + np.clip((xx - lx + 11) / 23, 0, 1) * 1.6)
        p.put(p.box(lx - 11, ly + 8, lx + 13, ly + 9), 'G', 4.0)
        p.put(p.ell(lx + 0.5, ly + 10, 2.4, 1.6), 'G', 5.4)
    p.put(p.box(562, 106, 563, 138), 'I', 2.0)
    shade = p.poly([(548, 146), (577, 146), (570, 136), (555, 136)])
    p.put(shade, 'P', 2.4 + np.clip((xx - 548) / 29, 0, 1) * 1.6)
    p.put(p.box(548, 146, 578, 147), 'G', 4.0)
    p.put(p.ell(562.5, 148, 3, 2), 'G', 5.4)
    # cold light falling in from the open side lifts the lower rafters
    p.L.amb_field(np.clip((yy - 150) / 76, 0, 1) * 0.6 * (yy < 226))
    p.resolve(band=2.6)
    return p.L


def shift_m(m, dx, dy):
    return C.shift(m, dx, dy)


def kit_erode(m, r):
    return C.kit.erode(m, r)


def k1_clock():
    R = C.ramps(P=GREEN, D=DIAL, I=IRON, K=['#070A12', '#15171C', '#22262D', '#323840', '#464D55'],
                B=['#2A1E16', '#4A3415', '#73531F', '#9C7630', '#C49A48'])
    p = C.Paint(VW, VH, R, 'k1_clock')
    yy, xx = p.yy, p.xx
    cx, cy = CENTER
    r, a = K.polar(yy, xx, cx, cy)
    # ---- hanger: a forged bracket with two C-scrolls from the girder to the crown of the drum
    rod = p.box(318, 104, 323, 113)
    p.put(rod, 'I', 1.4)
    p.put(p.box(318, 104, 319, 113), 'I', 3.4)
    for s in (-1, 1):
        pts = [(320 + s * 2, 106), (320 + s * 12, 104), (320 + s * 20, 108), (320 + s * 19, 114), (320 + s * 13, 114),
               (320 + s * 13, 110), (320 + s * 17, 110)]
        sc = p.line(pts, 0.8)
        p.put(sc, 'I', 1.4)
        p.put(sc & ~C.shift(sc, 0, -1), 'I', 3.8)
    p.put(p.ell(320.5, 103.5, 3.5, 2.5), 'I', 2.2)                            # collar on the girder
    p.put(p.ell(320.5, 110.5, 4.5, 2.5), 'P', 3.0)                            # crown boss of the drum
    # ---- drum: painted cast iron, seen a little from below (its side shows under the bezel)
    side = K.disc(yy, xx, cx + 1, cy + 4, CASE_R) & ~K.disc(yy, xx, cx, cy, CASE_R - 3)
    p.put(side, 'P', 1.6)
    p.put(side & (yy > cy + 40), 'P', 2.2)                                    # side catches the outside light
    drum = K.disc(yy, xx, cx, cy, CASE_R)
    p.put(drum, 'P', 2.4 + np.cos(np.radians(a - 300)) * 0.9)
    lip = K.ring(yy, xx, cx, cy, CASE_R - 1.5, CASE_R)
    p.put(lip, 'P', 4.2 * (np.cos(np.radians(a - 320)) > 0.2) + 1.2)
    # bezel: a dark iron ring, its rounded top catching the bright canopy edge
    bez = K.ring(yy, xx, cx, cy, DIAL_R, DIAL_R + 6)
    p.put(bez, 'I', 2.2 + np.cos(np.radians(a - 330)) * 1.2)
    p.put(K.ring(yy, xx, cx, cy, DIAL_R + 4.4, DIAL_R + 6) & bez, 'I', 1.0)
    shine = bez & (np.cos(np.radians(a - 320)) > 0.6) & K.ring(yy, xx, cx, cy, DIAL_R + 1.6, DIAL_R + 3.0)
    p.put(shine, 'I', 5.6 + np.cos(np.radians(a - 320)) * 1.2)
    p.put(K.ring(yy, xx, cx, cy, DIAL_R - 0.6, DIAL_R + 0.6), 'K', 1.0)
    # rivets around the drum
    for k in range(12):
        ang = math.radians(k * 30 + 15)
        rx_, ry_ = cx + math.sin(ang) * (CASE_R - 3.5), cy - math.cos(ang) * (CASE_R - 3.5)
        p.px(int(rx_), int(ry_), 'P', 5.0 if math.cos(ang - math.radians(320)) > 0 else 1.0)
    # ---- dial: white enamel, a soft fall-off toward the lower right, the railway indices
    dial = K.disc(yy, xx, cx, cy, DIAL_R)
    p.put(dial, 'D', 4.6 - np.clip(r / DIAL_R, 0, 1) ** 2 * 0.7 - np.clip((xx - cx + yy - cy) / 120, -0.4, 1) * 0.5)
    hrs, mins = K.clock_indices(yy, xx, cx, cy, DIAL_R - 3.0, 10.0, 4.0, hour_w=3.4, min_w=1.0)
    p.put(hrs & dial, 'K', 0.4)
    p.put(mins & dial, 'K', 1.0)
    p.put(K.ring(yy, xx, cx, cy, DIAL_R - 2.2, DIAL_R - 1.2) & dial, 'D', 3.0)   # enamel bevel line
    name = K.text_at('VELTRAVA', VW, VH, cx, cy + 18, font='s', center=True) & dial
    p.put(name, 'K', 3.0)
    p.put(K.text_at('KB', VW, VH, cx, cy - 26, font='s', center=True) & dial, 'K', 3.2)
    p.resolve(band=2.6)
    LAYOUT['k1_case_r'] = CASE_R
    return p.L


def k1_glass():
    """Additive glare of the curved crystal over the station dial (drawn above the hands)."""
    yy, xx = _grid()
    cx, cy = CENTER
    a = np.zeros((VH, VW, 3), np.float32)
    inside = K.disc(yy, xx, cx, cy, DIAL_R)
    # a crescent reflection of the bright canopy edge at the upper left + a small window glint
    d1 = np.hypot((xx - cx + 12) / 40, (yy - cy + 20) / 34)
    cres = np.clip(1 - np.abs(d1 - 1.0) / 0.10, 0, 1) * (xx < cx + 6) * (yy < cy + 4)
    for c, v in enumerate((26, 30, 36)):
        a[..., c] += cres * v * inside
    glint = K.disc(yy, xx, cx - 30, cy - 26, 2.4)
    a[glint & inside] += (38, 42, 48)
    return K.soft_quant(a, 6.0)


def steam_puffs():
    """Eight frames of the carriage heating's steam drifting along the platform (112 x 80), soft morning light.
    AD round 2: one cloud at eight successive ages (CT._drift_frames), so the runtime steps through them with a
    cross-fade -- the puffs swell and thin instead of snapping back to a small shape every 0.67 s."""
    import env_veltrava_cine_city as CT
    n, fw, fh = 8, 112, 80
    LAYOUT['steam_frames'] = n
    return CT._drift_frames(n, fw, fh, ['#687789', '#8593A3', '#A1AAB7', '#B6B9C9', '#C2C9D2'], 611,
                            light=(0.3, -0.85), aspect=1.8, lobes=12, grow=(0.62, 1.0), thin=0.5)


# =========================================================================== k2: the palais clock
PAL_WALL = ['#05080C', '#0A1016', '#10181F', '#172229', '#1B2826', '#26362F', '#344539', '#4A5B4C', '#647260']
BRASS = ['#22150F', '#4A3415', '#73531F', '#9C7630', '#C49A48', '#E8C779', '#FCE0A6']
MARBLE = ['#344539', '#4E4A44', '#6A655C', '#878075', '#A59D8F', '#C4BCAD', '#E0D9CB']
WOOD = ['#05080C', '#22150F', '#331F16', '#4A2D1F', '#63402C', '#7E553B', '#9A5A2F']
PAPER = ['#6E6A5C', '#8E8A78', '#B0AA93', '#CEC6AA', '#E6DEC2', '#F5EFDA']
DAY = ['#172229', '#263445', '#3A4D63', '#55708A', '#7C98B0', '#A9C0D0', '#D3DEE6']


def k2_bg():
    R = C.ramps(W=PAL_WALL, B=BRASS, M=MARBLE, D=WOOD, A=['#6E3F22', '#9A5A2F', '#C88A4E', '#E9B46E', '#FCE0A6'],
                Y=DAY)
    p = C.Paint(VW, VH, R, 'k2_bg')
    yy, xx = p.yy, p.xx
    allm = np.ones((VH, VW), bool)
    cx, cy = CENTER
    # warm chandelier light from the upper right, cold window light from the left
    warm = np.clip(1 - np.hypot((xx - 560) / 420, (yy - 20) / 300), 0, 1) ** 1.3
    cold = np.clip(1 - np.abs((xx - 0.55 * (yy - 40)) - 70) / 120, 0, 1) * np.clip(1 - yy / 330, 0, 1)
    # ---- silk wall: dark green damask
    dam = ((np.sin(xx * 0.39) * np.sin(yy * 0.31 + np.sin(xx * 0.2) * 1.2)) > 0.55)
    wall_t = 3.6 + warm * 2.4 + cold * 1.4 + (pg.value_noise(VW, VH, 30, 621, 2) - 0.5) * 0.5
    p.put(allm, 'W', wall_t)
    p.add(dam & (yy < 250), 0.5)
    # gilt frieze along the top
    p.put(p.box(0, 46, VW, 56), 'D', 2.0 + warm[46:56].mean() * 2)
    p.put(p.box(0, 56, VW, 59), 'B', 3.0 + warm * 1.5)
    p.put(p.box(0, 59, VW, 60), 'B', 1.4)
    for k in range(0, VW, 16):
        p.put(p.ell(k + 8, 51, 3, 2.5), 'B', 2.6 + warm[51, min(VW - 1, k + 8)] * 2.4)
    # ---- a recessed panel of dark green marble (verde antico) behind the clock, gilt moulding
    pan = p.box(222, 70, 418, 300)
    vein_f = pg.value_noise(VW, VH, 26, 622, 3)
    flow = np.sin((xx * 0.06 + yy * 0.11) + vein_f * 7.0)
    vt = 4.4 + warm * 1.0 + cold * 0.5 + (pg.value_noise(VW, VH, 6, 623, 2) - 0.5) * 0.7
    p.put(pan, 'W', vt)
    vein = pan & (np.abs(flow) < 0.05)
    p.put(vein, 'M', 2.6 + warm * 0.8)
    p.add(pan & (np.abs(flow) >= 0.05) & (np.abs(flow) < 0.16), 0.5)
    mould = pan & ~C.kit.erode(pan, 3)
    p.put(mould, 'B', 2.2 + warm * 2.0)
    p.put(pan & ~C.kit.erode(pan, 1), 'B', 1.0)
    p.put(C.kit.erode(pan, 2) & ~C.kit.erode(pan, 3), 'B', 3.8 + warm * 1.0)
    p.add(C.kit.erode(pan, 3) & ~C.kit.erode(pan, 6) & (yy < 140), -0.8)          # recess shadow under the top
    # ---- pilasters (darker marble) with gilt capitals at both sides of the panel
    for (x0, x1) in ((154, 184), (456, 486)):
        pil = p.box(x0, 60, x1, 300)
        p.put(pil, 'M', 1.6 + np.clip((xx - x0) / (x1 - x0), 0, 1) * 1.2 + warm * 1.4 + cold * 0.6)
        for fx in range(x0 + 5, x1 - 3, 6):
            p.put(p.box(fx, 94, fx + 1, 282), 'M', 0.6 + warm[150, fx] * 1.0)
            p.put(p.box(fx + 1, 94, fx + 2, 282), 'M', 2.4 + warm[150, fx] * 1.0)
        cap = p.box(x0 - 4, 60, x1 + 4, 92)
        p.put(cap, 'B', 2.0 + warm * 2.2 + np.sin((xx - x0) * 0.8) * 0.6)
        p.put(p.box(x0 - 4, 88, x1 + 4, 92), 'B', 1.2)
        for k in range(3):
            p.put(p.ell(x0 + 6 + k * ((x1 - x0) - 12) / 2, 75, 3.6, 4.6), 'B', 3.8 + warm[75, x0] * 1.4)
        p.put(p.box(x0 - 3, 282, x1 + 3, 300), 'M', 1.8 + warm * 0.8)
    # ---- walnut dado and the doorway leaves of the Grosser Saal at both sides
    dado = p.box(0, 252, VW, 300) & ~p.box(146, 252, 494, 300)
    p.put(dado, 'D', 2.6 + warm * 3.2)
    p.put(p.box(0, 252, 146, 255), 'B', 3.0 + warm * 1.5)
    p.put(p.box(494, 252, VW, 255), 'B', 3.0 + warm * 1.5)
    for (x0, x1) in ((8, 70), (78, 140), (500, 562), (570, 632)):
        pb = p.box(x0, 262, x1, 294)
        p.add(pb & ~C.kit.erode(pb, 1), -0.8)
        p.add(C.kit.erode(pb, 1) & ~C.kit.erode(pb, 2), 0.9)
    # tall window light at the left (the shaft itself is drawn by the runtime dust; here a soft wash)
    shaft = (np.abs((xx - 0.55 * (yy - 40)) - 60) < 46) & (yy < 300)
    p.add(shaft & ~pan, 0.6)
    # ---- floor: polished black-and-white marble in the side view of the hall level
    fl = p.box(0, 300, VW, VH)
    chk = (((xx // 22).astype(int) + ((yy - 300) // 7).astype(int)) % 2 == 0)
    p.put(fl, 'M', np.where(chk, 5.0, 1.0) + warm * 1.0 - np.clip((yy - 300) / 40, 0, 1) * 0.8)
    p.put(p.box(0, 300, VW, 302), 'D', 1.6)
    # the clock's reflection in the polish (soft, broken by the joints)
    refl = fl & (np.abs(xx - cx) < 34) & (yy < 318) & ((yy.astype(int) + (xx.astype(int) // 3)) % 3 != 0)
    p.add(refl, 0.9)
    p.L.amb_field(-np.clip(np.hypot((xx - 330) / 520, (yy - 170) / 280) - 0.4, 0, 1) * 1.8)
    p.resolve(band=2.6)
    return p.L


def k2_clock():
    R = C.ramps(B=BRASS, P=PAPER, K=['#1A1C2A', '#2E3248', '#4A3415', '#73531F'], W=PAL_WALL,
                G=['#0A1016', '#172229', '#26362F', '#4A5B4C', '#7C98B0', '#A9C0D0'])
    p = C.Paint(VW, VH, R, 'k2_clock')
    yy, xx = p.yy, p.xx
    cx, cy = CENTER
    r, a = K.polar(yy, xx, cx, cy)
    warm = np.clip(1 - np.hypot((xx - 560) / 420, (yy - 20) / 300), 0, 1) ** 1.3
    lit = np.cos(np.radians(a - 40))            # chandelier from the upper right
    # ---- Jugendstil frame: two whiplash stems rise from the pendant case, sweep round the ring and end in
    #      leaf tips above it; a stylised poppy crest at the top, small leaves where the stems cross
    orn = np.zeros((VH, VW), bool)
    lw = np.zeros((VH, VW), bool)             # leaves (filled)
    for s_ in (-1, 1):
        stem = [(cx + s_ * 10, cy + 56), (cx + s_ * 34, cy + 52), (cx + s_ * 58, cy + 34), (cx + s_ * 68, cy + 4),
                (cx + s_ * 64, cy - 30), (cx + s_ * 48, cy - 54), (cx + s_ * 24, cy - 66), (cx + s_ * 12, cy - 64)]
        orn |= p.line(stem, 1.6)
        whip = [(cx + s_ * 62, cy + 26), (cx + s_ * 80, cy + 22), (cx + s_ * 88, cy + 4), (cx + s_ * 82, cy - 10),
                (cx + s_ * 74, cy - 6)]
        orn |= p.line(whip, 1.1)
        for (lx, ly, rot_, ln) in ((cx + s_ * 70, cy + 16, 0.6, 9), (cx + s_ * 66, cy - 20, -0.4, 8),
                                    (cx + s_ * 52, cy - 50, -1.0, 7)):
            ux, uy = math.cos(rot_) * s_, math.sin(rot_)
            pts = [(lx, ly), (lx + ux * ln * 0.5 - uy * 3, ly + uy * ln * 0.5 + ux * 3 * s_),
                   (lx + ux * ln, ly + uy * ln), (lx + ux * ln * 0.5 + uy * 3, ly + uy * ln * 0.5 - ux * 3 * s_)]
            lw |= p.poly(pts)
    # crest: a poppy head between two drooping petals on a short stalk
    orn |= p.line([(cx, cy - 62), (cx, cy - 72)], 1.0)
    lw |= p.ell(cx, cy - 78, 5.5, 6.5)
    for s_ in (-1, 1):
        lw |= p.poly([(cx + s_ * 3, cy - 74), (cx + s_ * 14, cy - 82), (cx + s_ * 18, cy - 74), (cx + s_ * 10, cy - 70)])
    orn |= lw
    # pendant case with the pendulum window (the pendulum sprite swings behind it)
    case = p.rr(cx - 24, cy + 52, cx + 24, cy + 126, 12)
    win = p.rr(cx - 16, cy + 60, cx + 16, cy + 118, 9)
    p.put(case & ~win, 'B', 2.4 + lit * 1.0 + warm * 1.5)
    p.put(case & ~C.kit.erode(case, 1), 'B', 1.2)
    p.put(win & ~C.kit.erode(win, 1) & case, 'B', 4.4)
    p.put(p.ell(cx, cy + 128, 5, 3.5), 'B', 3.2)                             # finial drop
    p.put(p.ell(cx, cy + 133, 2.5, 2.5), 'B', 2.4)
    nd = ~K.disc(yy, xx, cx, cy, DIAL_R + 6)
    p.put(orn & nd, 'B', 2.2 + np.clip(lit, -1, 1) * 1.2 + warm * 1.6)
    p.put(lw & nd, 'B', 2.8 + np.clip(lit, -1, 1) * 1.2 + warm * 1.6)
    p.put(orn & ~C.shift(orn, 1, 1) & nd, 'B', 1.0)            # shadow side
    p.put(orn & ~C.shift(orn, -1, -1) & nd, 'B', 5.0)          # lit edge
    p.put(lw & C.shift(lw, -2, 0) & C.shift(lw, 2, 0) & nd & ((yy.astype(int) + xx.astype(int)) % 2 == 0), 'B', 1.8)
    # ---- the gilt ring: three beads and a reeded band
    bez = K.ring(yy, xx, cx, cy, DIAL_R, DIAL_R + 8)
    p.put(bez, 'B', 2.6 + lit * 1.2 + warm * 0.8)
    p.put(K.ring(yy, xx, cx, cy, DIAL_R + 2.6, DIAL_R + 4) & bez, 'B', 1.4)
    p.put(K.ring(yy, xx, cx, cy, DIAL_R + 6.6, DIAL_R + 8), 'B', 1.6)
    reed = K.ring(yy, xx, cx, cy, DIAL_R + 4, DIAL_R + 6.6) & ((np.floor(a / 3.0).astype(int) % 2) == 0)
    p.add(reed, 1.2)
    shine = bez & (lit > 0.9) & K.ring(yy, xx, cx, cy, DIAL_R + 0.5, DIAL_R + 2.6)
    p.put(shine, 'B', 5.6)
    # ---- dial: ivory porcelain, gilt lozenges on the railway angles, a painted floral wreath
    dial = K.disc(yy, xx, cx, cy, DIAL_R)
    p.put(dial, 'P', 4.4 - np.clip(r / DIAL_R, 0, 1) ** 2 * 0.9 + lit * 0.25 + warm * 0.3)
    hrs, mins = K.clock_indices(yy, xx, cx, cy, DIAL_R - 3.0, 10.0, 3.0, hour_w=3.4, min_w=1.0)
    p.put(hrs & dial, 'B', 2.2)
    p.put(hrs & dial & ~C.shift(hrs, -1, 0), 'B', 4.2)
    p.put(mins & dial, 'K', 1.0)
    p.put(K.ring(yy, xx, cx, cy, DIAL_R - 17.5, DIAL_R - 16.5) & dial, 'B', 3.0)    # inner chapter ring
    p.put(K.text_at('VELTRAVA', VW, VH, cx, cy + 20, font='s', center=True) & dial, 'K', 1.2)
    p.resolve(band=2.6)
    LAYOUT['pendulum_window'] = [cx - 17, cy + 60, cx + 17, cy + 120]
    return p.L


def k2_glass():
    yy, xx = _grid()
    cx, cy = CENTER
    a = np.zeros((VH, VW, 3), np.float32)
    inside = K.disc(yy, xx, cx, cy, DIAL_R)
    d1 = np.hypot((xx - cx - 14) / 40, (yy - cy + 18) / 34)
    cres = np.clip(1 - np.abs(d1 - 1.0) / 0.09, 0, 1) * (xx > cx - 8) * (yy < cy + 6)
    for c, v in enumerate((34, 26, 14)):
        a[..., c] += cres * v * inside
    glint = K.disc(yy, xx, cx + 31, cy - 25, 2.2)
    a[glint & inside] += (48, 38, 22)
    # the pendulum window glass: two faint vertical streaks
    for gx in (cx - 9, cx + 6):
        st = (np.abs(xx - gx) < 0.6) & (yy > cy + 64) & (yy < cy + 116) & ((yy.astype(int) % 3) != 0)
        a[st] += (14, 12, 8)
    return K.soft_quant(a, 6.0)


def pendulum():
    """8 swing positions of the gilt lyre pendulum (frame 0 = far left .. 7 = far right)."""
    cx, cy = CENTER
    fw, fh = 34, 62
    x0, y0 = cx - 17, cy + 58
    R = C.ramps(B=BRASS, K=['#05080C', '#10181F', '#22150F'])
    sheet = np.zeros((fh, fw * 8, 4), np.uint8)
    pivot = (fw / 2, 0.0)
    for i in range(8):
        ang = math.radians(-9.0 + 18.0 * i / 7.0)
        p = C.Paint(fw, fh, R, 'pendulum')
        L = 48.0
        bx, by = pivot[0] + math.sin(ang) * L, pivot[1] + math.cos(ang) * L
        for off in (-2.2, 2.2):
            ox, oy = math.cos(ang) * off, -math.sin(ang) * off
            p.put(p.line([(pivot[0] + ox * 0.4, 1), (bx + ox, by - 6)], 0.5), 'B', 2.6 if off < 0 else 3.6)
        p.put(p.ell(bx, by, 7.5, 7.5), 'B', 2.0)
        p.put(p.ell(bx - 1.5, by - 1.5, 5.5, 5.5), 'B', 3.8)
        p.put(p.ell(bx - 3, by - 3, 1.8, 1.8), 'B', 5.6)
        p.put(p.ell(bx, by, 7.5, 7.5) & ~p.ell(bx, by, 6.6, 6.6), 'B', 1.2)
        p.resolve(band=2.0)
        sheet[:, i * fw:(i + 1) * fw] = p.L.c
    LAYOUT['pendulum'] = [x0, y0]
    return sheet


def k2_konrad():
    """Round 10 (figures stream): Konrad walking right under the palais clock is a full SDF figure with an
    8-frame walk cycle -- the near arm swings from the shoulder with the elbow bending on the forward swing, the
    hand open, the far arm swings against it, the shoulders counter-rotate, the body rises on the passing step,
    the drafting tube hangs on its strap across his back -- still back-lit (warm chandelier rim on the front,
    cold window rim on the back).  env_veltrava_cine_heroes.walking_konrad; sets konrad_y / konrad_frames."""
    import env_veltrava_cine_heroes as H
    return H.k2_konrad_sheet(LAYOUT)
