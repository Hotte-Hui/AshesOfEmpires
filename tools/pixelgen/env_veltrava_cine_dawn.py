"""env_veltrava_cine_dawn -- t4 of LS_C3_Trains: dawn over Veltrava, both trains on the river bridge.

Owner: cinematics stream.  Veltrava from the near bank: the three-arch stone bridge (the commission's arms)
carries a dual track into the city; the old town, the cathedral, the castle hill and the palais dome stand
against a cold winter dawn that warms in the east (right); the river is half frozen.  Konrad's train (grey-blue
saloon cars, pennants) comes from the west on the far track, Alexei's (green carriages, the sealed courier
wagon 4 at its tail) from the east on the near track; their plumes meet over the middle arch.
Layer order in the runtime (scenes/cinematics/ch3_trains): bridge_bg, dawn_glow (add), city smoke, train_de,
train_su, loco smoke, life (glints, floes, crows, the woman with the sled), bridge_fg, fg_glow (add).
"""
from __future__ import annotations

import math

import numpy as np

import env_veltrava_cine as C
import env_veltrava_cine_kit as K
import pg

VW, VH = C.VW, C.VH
V = C.V
LAYOUT = C.LAYOUT.setdefault('trains', {})
kit = C.kit
shift = C.shift
rim = C.rim

TRAIN_H = 30
TRAIN_W = 376
DE_RAIL, SU_RAIL = 181, 191                    # rail rows of the far / near track
TRAIN_DE_Y, TRAIN_SU_Y = DE_RAIL - TRAIN_H + 2, SU_RAIL - TRAIN_H + 2
PARAPET_Y = 185                                # top of the near parapet (bridge_fg) -> hides the near wheels
ARCHES = [(44, 220), (236, 404), (420, 596)]
ARCH_CY, ARCH_RY = 238, 34
WATER_Y = 244
QUAY_LAMPS = [34, 118, 206, 294, 378, 466, 550, 626]
PARAPET_LAMPS = [36, 128, 220, 312, 404, 496, 588]
CHIMNEYS = [[58, 140], [139, 131], [231, 138], [287, 140], [437, 139], [519, 132], [604, 141]]

SKY = ['#070A12', '#0C111C', '#121A26', '#1A2431', '#1E2836', '#2A3646', '#3A4859', '#4F5E70', '#5C6B82',
       '#687789', '#7684A0', '#8593A3', '#95A0B8', '#A1AAB7', '#B6B9C9']
DAWN = ['#5C6B82', '#7684A0', '#95A0B8', '#B6B9C9', '#D3CDD3', '#E8DCD6', '#F2E4D2']
SIL = ['#070A12', '#0C111C', '#121A26', '#1A2431', '#1E2836', '#2A3646', '#3A4859', '#4F5E70', '#5C6B82',
       '#687789', '#7684A0']
STONE = ['#0C111C', '#15171C', '#22262D', '#323840', '#464D55', '#5E666E', '#687789', '#8593A3']
SNOW = ['#2A3646', '#3A4859', '#4F5E70', '#687789', '#7D8796', '#A1AAB7', '#C2C9D2', '#DEE2E7', '#F2F3F5']
WATER = ['#070A12', '#0C111C', '#121A26', '#1A2431', '#1E2836', '#2A3646', '#3A4859', '#4F5E70', '#687789',
         '#8593A3', '#A1AAB7']


def ramps_dawn():
    return C.ramps(S=SKY, D=DAWN, N=SIL, I=STONE, W=SNOW, Q=WATER, L=V['lamp'], P=V['patina'], C=V['cream'],
                   R=V['red'], G=['#0C111C', '#1E302E', '#2B4541', '#3D5E57', '#4A4236'],
                   B=['#0C111C', '#121A26', '#1E2836', '#2A3646', '#3A4859', '#4F5E70'],
                   T=['#070A12', '#0B1512', '#12201a', '#1E302E', '#2B4541', '#3D5E57', '#56796E'])


def _east(xx):
    return np.clip((xx - 120) / 520.0, 0, 1)


# =========================================================================== background
def _roof_run(p, xs, base, tone, seed, ramp='N', lit_p=0.4, snow=True):
    rng = np.random.default_rng(seed)
    out = np.zeros((VH, VW), bool)
    for a, b in zip(xs[:-1], xs[1:]):
        h = rng.uniform(9, 22)
        kind = int(rng.integers(0, 3))
        if kind == 0:
            pts = [(a, base), (a, base - h * 0.55), ((a + b) / 2, base - h), (b, base - h * 0.55), (b, base)]
        elif kind == 1:
            pts = [(a, base), (a, base - h * 0.5), (a + 4, base - h), (b - 4, base - h), (b, base - h * 0.5), (b, base)]
        else:
            pts = [(a, base), (a, base - h * 0.7), (b, base - h * 0.7), (b, base)]
        m = p.poly(pts)
        out |= m
        p.put(m, ramp, tone)
        if snow:
            p.put(m & ~shift(m, 0, -1) & (p.yy < base - h * 0.45), 'W', 2.2 + tone * 0.3)
        for _ in range(int(rng.integers(0, 4))):
            if rng.random() < lit_p:
                wx = rng.uniform(a + 2, b - 4)
                wy = base - rng.uniform(3, max(4, h * 0.45))
                p.put(p.box(wx, wy, wx + 2, wy + 2), 'L', float(rng.choice([1.6, 2.4, 3.0])), emis=True)
    return out


def bridge_bg():
    R = ramps_dawn()
    p = C.Paint(VW, VH, R, 'bridge_bg')
    yy, xx = p.yy, p.xx
    allm = np.ones((VH, VW), bool)
    east = _east(xx)
    # ---- sky: slate overhead, the cold dawn low in the east, rose-cream right at the horizon
    u = np.clip((yy - 40) / 128.0, 0, 1)
    st = 3.6 + u ** 1.35 * (6.4 + 3.6 * east) + (pg.value_noise(VW, VH, 60, 401, 3) - 0.5) * 0.7
    p.put(allm, 'S', st)
    warm = np.clip((yy - 78) / 82.0, 0, 1) ** 1.1 * east ** 0.75
    wz = (warm * 1.45 > pg.bayer(VW, VH, 1, 2)) & (yy < 170)
    p.put(wz, 'D', 1.0 + warm * 5.6 + (pg.value_noise(VW, VH, 30, 402, 2) - 0.5) * 0.6)
    # stratus banks: soft dark bodies with dithered edges, undersides catching the dawn in the east
    rng = np.random.default_rng(403)
    for _ in range(9):
        by = rng.uniform(56, 130)
        x0 = rng.uniform(-160, 520)
        ln = rng.uniform(160, 380)
        th = rng.uniform(3.0, 7.5)
        slope = rng.uniform(-0.008, 0.014)
        prof = np.clip(1 - np.abs(yy - by - slope * (xx - x0)) / th, 0, 1)
        taper = np.clip(np.minimum(xx - x0, x0 + ln - xx) / 60.0, 0, 1)
        dens = prof ** 0.7 * taper * (0.75 + 0.5 * pg.value_noise(VW, VH, 18, int(rng.integers(1 << 20)), 2))
        band = dens > pg.bayer(VW, VH, 2, 3) * 0.9 + 0.08
        p.put(band, 'S', 4.0 + u * 2.6 + east * 0.6 - dens * 0.8)
        under = band & ~shift(band, 0, 1) & (yy > by)
        lit_e = east > 0.5
        p.put(under & lit_e, 'D', 1.6 + east * 2.0)
        p.put(under & ~lit_e, 'S', 6.6 + u * 1.6)
    # ---- far rank: the castle hill (west) and the cathedral, deep in the haze
    hill = p.poly([(-5, 156), (-5, 132), (36, 120), (80, 110), (112, 106), (148, 116), (196, 132), (232, 148), (246, 156)])
    p.put(hill, 'N', 7.0 + np.clip((yy - 108) / 50, 0, 1) * 0.6)
    castle = p.box(70, 96, 126, 112) | p.box(76, 86, 84, 98) | p.box(110, 90, 118, 98) | p.box(96, 82, 102, 98)
    p.put(castle, 'N', 6.6)
    for bx in range(70, 126, 4):
        p.put(p.box(bx, 94, bx + 2, 96), 'N', 6.6)
    p.put(p.poly([(96, 82), (99, 75), (102, 82)]), 'N', 6.4)
    p.put(p.box(98, 92, 100, 94), 'L', 2.4, emis=True)
    nave = p.poly([(150, 150), (150, 118), (160, 112), (200, 112), (210, 118), (210, 150)])
    p.put(nave, 'N', 5.4)
    for (sx, top, w) in ((154, 62, 12), (198, 78, 10)):
        tw = p.box(sx, 112, sx + w, 150) | p.poly([(sx - 1, 112), (sx + w / 2, top), (sx + w + 1, 112)])
        p.put(tw, 'N', 5.2)
        p.put(p.box(sx + w / 2 - 1, 100, sx + w / 2 + 1, 106), 'N', 4.2)
        p.put(p.line([(sx + w / 2, top), (sx + w / 2, top - 5)], 0.4), 'N', 4.6)
        p.put(tw & ~shift(tw, 1, 0) & (xx > sx + w / 2), 'D', 1.0)                  # dawn on the east edge
    for k in range(5):
        p.put(p.poly([(163 + k * 8, 112), (165 + k * 8, 104), (167 + k * 8, 112)]), 'N', 5.3)
    # ---- second rank: old town roofs (hazy), the onion church, the town hall tower with its lit clock
    _roof_run(p, [-4, 30, 58, 96, 130, 168, 204, 238, 262, 286, 308, 332, 356, 380, 404, 430, 454, 478, 506, 534,
                  560, 584, 612, 644], 150, 4.6, 404, lit_p=0.5)
    body = p.box(470, 118, 504, 150)
    p.put(body, 'N', 4.4)
    onion = p.ell(487, 110, 10, 9) | p.poly([(479, 110), (487, 94), (495, 110)])
    p.put(onion, 'P', 1.4 + np.clip((xx - 480) / 14, 0, 1) * 1.6)
    p.put(onion & ~shift(onion, 1, 0) & (xx > 487), 'D', 2.0)
    p.put(p.box(486, 88, 488, 95), 'N', 3.6)
    th_ = p.box(560, 102, 576, 150) | p.poly([(557, 102), (568, 84), (579, 102)])
    p.put(th_, 'N', 4.0)
    p.put(th_ & ~shift(th_, 1, 0), 'D', 1.6)
    p.put(p.ell(568, 110, 4, 4), 'C', 3.2, emis=True)
    p.put(p.ell(568, 110, 2.5, 2.5), 'C', 4.8, emis=True)
    # ---- the palais of the commission: long classical front, the patinated dome catching the first light
    front = p.box(246, 122, 416, 150)
    p.put(front, 'N', 3.4 + east * 0.4)
    for k in range(13):
        p.put(p.box(252 + k * 13, 126, 253 + k * 13, 146), 'N', 4.2)
    for k in range(12):
        lit = k in (1, 2, 4, 7, 9, 10)
        p.put(p.box(256 + k * 13, 132, 260 + k * 13, 138), 'L' if lit else 'N', 2.6 if lit else 2.4, emis=lit)
    p.put(p.box(242, 120, 420, 122), 'N', 4.6)
    p.put(p.box(242, 119, 420, 120), 'W', 3.2)
    drum = p.box(302, 104, 360, 122)
    p.put(drum, 'N', 3.6)
    for k in range(8):
        p.put(p.box(306 + k * 7, 107, 307 + k * 7, 120), 'N', 4.4)
    dome = p.ell(331, 106, 31, 26) & (yy < 106)
    dl = np.clip((xx - 310) / 44, 0, 1)
    p.put(dome, 'P', 1.2 + dl * 2.4 + np.clip((yy - 82) / 24, 0, 1) * 0.5)
    for k in range(-3, 4):
        rx = 331 + k * 8
        p.put(p.line([(rx, 106), (331 + k * 4.5, 84)], 0.4) & dome, 'P', 0.8 + dl[106, int(rx)] * 1.4)
    p.put(dome & rim(dome, 0, -1, 1), 'W', 4.4 + dl * 1.6)
    lantern = p.box(326, 70, 336, 81) | p.poly([(324, 70), (331, 62), (338, 70)])
    p.put(lantern, 'N', 3.4)
    p.put(p.box(329, 73, 333, 78), 'L', 2.6, emis=True)
    for fx_ in (264, 298, 364, 398):
        p.put(p.box(fx_, 98, fx_ + 1, 121), 'N', 3.6)
        p.put(p.box(fx_ + 1, 99, fx_ + 3, 106), 'N', 3.0)
    # ---- the riverside rank: warehouses and the quay street (darkest, lit windows), the quay wall
    _roof_run(p, [-4, 26, 54, 88, 116, 146, 176, 202, 230, 258, 290, 320, 348, 378, 410, 440, 468, 496, 526, 556,
                  586, 616, 644], 158, 2.6, 405, lit_p=0.6)
    p.put(p.box(0, 150, VW, 160), 'N', 2.4)
    for k in range(0, VW, 9):
        if (k // 9) % 3 != 1:
            on = (k // 9) % 4 == 0
            p.put(p.box(k + 2, 152, k + 5, 157), 'L' if on else 'N', 2.2 if on else 1.4, emis=on)
    p.put(p.box(0, 160, VW, 166), 'I', 2.0 + (pg.value_noise(VW, VH, 5, 406, 1) - 0.5) * 0.8)
    p.put(p.box(0, 160, VW, 161), 'W', 3.4)
    for lx in QUAY_LAMPS:
        p.put(p.box(lx, 150, lx + 1, 160), 'N', 1.0)
        p.put(p.box(lx - 1, 147, lx + 2, 151), 'L', 3.6, emis=True)
        p.put(p.box(lx, 146, lx + 1, 147), 'L', 4.4, emis=True)
    # the river beyond the bridge (a thin band, dawn mirrored in it)
    far = p.box(0, 166, VW, 172)
    p.put(far, 'Q', 3.0 + east * 3.4 + ((yy.astype(int) + xx.astype(int) // 7) % 3 == 0) * 0.8)
    # ---- the bridge deck: far railing, deck, the far track
    p.put(p.box(0, 172, VW, 173), 'I', 4.6 + east * 1.2)
    rail = p.box(0, 173, VW, 179) & ((xx.astype(int) % 6) == 2)
    p.put(rail, 'I', 1.4)
    p.put(p.box(0, 177, VW, 178), 'I', 2.0)
    deck = p.box(0, 179, VW, PARAPET_Y)
    p.put(deck, 'W', 3.2 + (pg.value_noise(VW, VH, 9, 407, 2) - 0.5) * 0.9)
    p.put(p.box(0, DE_RAIL - 1, VW, DE_RAIL), 'I', 5.4)
    p.put(p.box(0, DE_RAIL, VW, DE_RAIL + 1), 'I', 1.4)
    # ---- the spandrel wall under the near parapet, the arches with the river and the far bank through them
    p.put(p.box(0, 194, VW, 197), 'I', 4.2 + east * 1.0)
    p.put(p.box(0, 196, VW, 197), 'I', 2.0)
    wall = p.box(0, 197, VW, WATER_Y + 6)
    stone = pg.value_noise(VW, VH, 7, 408, 2)
    p.put(wall, 'I', 2.4 + (stone - 0.5) * 0.9 - np.clip((yy - 197) / 50, 0, 1) * 0.6 + east * 0.6)
    courses = wall & ((yy.astype(int) % 6) == 0)
    p.add(courses, -0.5)
    joints = wall & ((((xx.astype(int) + (yy.astype(int) // 6) * 7) % 14) == 0))
    p.add(joints, -0.4)
    for (a, b) in ARCHES:
        cx = (a + b) / 2
        op = p.ell(cx, ARCH_CY, (b - a) / 2, ARCH_RY) & (yy < ARCH_CY + 10)
        # through the arch: the far bank's snow, the dark water, the dawn mirrored in it
        p.put(op, 'Q', 2.2 + east * 2.6 + np.clip((yy - 204) / 34, 0, 1) * 0.8)
        fb = op & (yy < 214)
        p.put(fb, 'W', 1.4 + east * 1.0)
        for lx in QUAY_LAMPS:
            stk = op & (np.abs(xx - lx) < 1.0) & ((yy.astype(int) + lx) % 3 != 0) & (yy > 214)
            p.put(stk, 'L', 0.9 + np.clip(1 - (yy - 214) / 26, 0, 1) * 1.6)
        ring = kit.dilate(op, 2) & ~op & (yy < ARCH_CY + 10)
        p.put(ring, 'I', 1.2)
        p.put(ring & (xx > cx) & (yy < 222), 'I', 4.0 + east * 0.8)
        for k in range(-6, 7):                                                     # voussoir joints
            ang = math.pi / 2 + k * 0.22
            x1 = cx + math.cos(ang) * ((b - a) / 2 + 2)
            y1 = ARCH_CY - math.sin(ang) * (ARCH_RY + 2)
            x0_ = cx + math.cos(ang) * ((b - a) / 2 - 1)
            y0_ = ARCH_CY - math.sin(ang) * (ARCH_RY - 1)
            p.put(p.line([(x0_, y0_), (x1, y1)], 0.4) & ring, 'I', 0.6)
        key = p.box(cx - 3, 201, cx + 3, 207) & ~op
        p.put(key, 'I', 4.8)
    for (a, b) in ((220, 236), (404, 420)):
        pier = p.box(a, 204, b, WATER_Y + 10)
        p.put(pier, 'I', 1.8 + np.clip((xx - a) / (b - a), 0, 1) * 1.8)
        cw = p.poly([(a - 5, WATER_Y + 10), (a - 5, 228), ((a + b) / 2, 214), (b + 5, 228), (b + 5, WATER_Y + 10)])
        p.put(cw, 'I', 1.6 + np.clip((xx - a + 5) / (b - a + 10), 0, 1) * 1.8)
        p.put(p.box(a - 6, WATER_Y - 2, b + 6, WATER_Y + 1), 'W', 3.6)
    # ---- the river in front: the open channel mirroring the dawn, ice sheets from both banks, floes
    water = p.box(0, WATER_Y, VW, VH)
    wn = pg.value_noise(VW, VH, 22, 411, 3)
    chan = np.clip(1 - np.abs(xx - 430) / 260, 0, 1)
    rip_n = pg.value_noise(VW, VH, 5, 415, 2)
    ripple = (np.sin(yy * 1.9 + rip_n * 9.0 + xx * 0.02) > 0.82) & (pg.value_noise(VW, VH, 11, 416, 2) > 0.45)
    wt = 1.6 + chan * 2.2 + east * 1.4 + (wn - 0.5) * 0.7 - np.clip((yy - WATER_Y) / 50, 0, 1) * 0.6
    p.put(water, 'Q', wt + ripple * 0.9)
    # dawn reflected as broken horizontal streaks in the eastern channel
    refl = water & (yy < 286) & ((wn + chan * 0.6 + east * 0.5) > 1.08) & ripple
    p.put(refl, 'D', 1.4 + east * 2.4)
    # the arches mirrored as dark arcs in the water right below the bridge
    for (a, b) in ARCHES:
        cx = (a + b) / 2
        mir = p.ell(cx, 2 * WATER_Y - ARCH_CY + 6, (b - a) / 2, ARCH_RY) & water & (yy < WATER_Y + 22)
        p.add(mir & ((yy.astype(int) + xx.astype(int) // 5) % 3 != 0), -0.9)
    for lx in QUAY_LAMPS + PARAPET_LAMPS:
        stk = water & (np.abs(xx - lx) < 1.0) & ((yy.astype(int) * 2 + lx) % 5 < 2) & (yy < WATER_Y + 26)
        p.put(stk, 'L', 0.6 + np.clip(1 - (yy - WATER_Y) / 26, 0, 1) * 1.4)
    # ice: flat sheets with crisp, jagged edges and a few cracks; floes in the channel
    rngi = np.random.default_rng(412)
    edge_l = 92 + np.cumsum(rngi.normal(0, 2.2, VH)).astype(np.float32) * 0.5
    edge_r = 566 + np.cumsum(rngi.normal(0, 2.0, VH)).astype(np.float32) * 0.5
    sheet_l = water & (xx < edge_l[:, None] - np.clip((yy - WATER_Y) * -0.4, -40, 0))
    sheet_r = water & (xx > edge_r[:, None] + np.clip((yy - WATER_Y) * -0.3, -30, 0))
    near_band = water & (yy > 270 + (pg.value_noise(VW, 4, 40, 413, 2)[0] * 10)[None, :].astype(int))
    ice = sheet_l | sheet_r | near_band
    floes = np.zeros((VH, VW), bool)
    for _ in range(7):
        fx = rngi.uniform(150, 540)
        fy = rngi.uniform(WATER_Y + 6, 268)
        fw = rngi.uniform(8, 26)
        fh = fw * rngi.uniform(0.18, 0.32)
        pts = [(fx - fw / 2 + rngi.uniform(-2, 2), fy + rngi.uniform(-1, 1)),
               (fx + rngi.uniform(-3, 3), fy - fh), (fx + fw / 2 + rngi.uniform(-2, 2), fy + rngi.uniform(-1, 1)),
               (fx + rngi.uniform(-3, 3), fy + fh)]
        floes |= p.poly(pts)
    ice |= floes & water
    it = 3.0 + np.clip((yy - WATER_Y) / 70, 0, 1) * 0.8 + east * 1.4 + (wn - 0.5) * 0.6
    p.put(ice, 'W', it)
    drifts = ice & (np.sin(xx * 0.09 + yy * 0.55 + pg.value_noise(VW, VH, 16, 417, 2) * 6.0) > 0.88)
    p.add(drifts, 0.9)                                                               # wind-blown snow on the ice
    p.put(ice & ~shift(ice, 0, -1), 'W', it + 1.4)                                  # lit upper edges
    p.put(ice & ~shift(ice, 0, 1) & water, 'Q', 1.0)                                # dark water line under the edge
    for _ in range(16):                                                              # cracks
        cx0 = rngi.uniform(0, VW)
        cy0 = rngi.uniform(WATER_Y + 4, 300)
        pts = [(cx0, cy0)]
        for _k in range(4):
            pts.append((pts[-1][0] + rngi.uniform(-10, 10), pts[-1][1] + rngi.uniform(-3, 3)))
        cr = p.line(pts, 0.4) & ice & kit.erode(ice, 1)
        p.add(cr, -1.6)
    p.resolve(band=2.6)
    glints = []
    rngg = np.random.default_rng(414)
    for _ in range(46):
        gx = int(rngg.uniform(250, 610))
        gy = int(rngg.uniform(WATER_Y + 3, 282))
        if not ice[gy, gx]:
            glints.append([gx, gy, int(rngg.integers(1, 4))])
    LAYOUT['glints'] = glints
    LAYOUT['chimneys'] = CHIMNEYS
    return p.L


def bridge_fg():
    """Near parapet with lanterns (in front of the trains) and the near bank with its path."""
    R = ramps_dawn()
    p = C.Paint(VW, VH, R, 'bridge_fg')
    yy, xx = p.yy, p.xx
    east = _east(xx)
    par = p.box(0, PARAPET_Y, VW, 194)
    st = pg.value_noise(VW, VH, 6, 421, 2)
    p.put(par, 'I', 2.6 + (st - 0.5) * 0.8 + east * 0.9)
    p.put(par & ((xx.astype(int) % 12) == 0), 'I', 1.2)
    p.put(p.box(0, PARAPET_Y, VW, PARAPET_Y + 1), 'W', 6.0 + east * 1.0)            # snow on the coping
    p.put(p.box(0, PARAPET_Y + 1, VW, PARAPET_Y + 2), 'I', 5.0)
    p.put(p.box(0, 193, VW, 194), 'I', 1.4)
    for lx in PARAPET_LAMPS:
        p.put(p.box(lx - 2, PARAPET_Y - 2, lx + 3, PARAPET_Y + 1), 'I', 1.4)
        p.put(p.box(lx, PARAPET_Y - 22, lx + 1, PARAPET_Y - 1), 'I', 1.2)
        p.put(p.box(lx - 1, PARAPET_Y - 24, lx + 2, PARAPET_Y - 22), 'I', 1.8)
        p.put(p.box(lx - 2, PARAPET_Y - 30, lx + 3, PARAPET_Y - 24), 'L', 3.2, emis=True)
        p.put(p.box(lx - 1, PARAPET_Y - 28, lx + 2, PARAPET_Y - 25), 'L', 4.4, emis=True)
        p.put(p.box(lx - 2, PARAPET_Y - 31, lx + 3, PARAPET_Y - 30), 'I', 3.0)
        p.put(p.box(lx - 1, PARAPET_Y - 32, lx + 2, PARAPET_Y - 31), 'W', 5.0)
    # ---- the near bank: snow slope falling into its own blue shadow, the path, reeds, a bare willow
    bank_top = 286 + (C.wrap_noise(VW, 1, 70, 422)[0] * 6).astype(int)
    bank = yy >= bank_top[None, :]
    sn = pg.value_noise(VW, VH, 14, 423, 2)
    p.put(bank, 'W', 3.4 + (sn - 0.5) * 0.8 - np.clip((yy - 290) / 24, 0, 1) * 1.8 + east * 0.5)
    p.put(bank & ~shift(bank, 0, 1), 'W', 6.6 + east * 1.0)
    p.put(bank & shift(bank, 0, 1) & ~shift(bank, 0, 2), 'W', 5.4)
    path = bank & (yy > 296) & (yy < 301)
    p.put(path, 'W', 2.6 + (sn - 0.5) * 0.6)
    trod = path & (((xx.astype(int) * 7 + yy.astype(int) * 3) % 11) < 2)
    p.add(trod, -0.8)
    p.put(bank & (yy >= 301) & (yy < 302), 'W', 4.6)
    rng = np.random.default_rng(424)
    for _ in range(16):
        rx = int(rng.uniform(16, 580))
        base = int(bank_top[rx])
        for k in range(int(rng.integers(3, 7))):
            h = int(rng.uniform(4, 11))
            dx = rng.uniform(-3, 3)
            p.put(p.line([(rx + dx, base + 2), (rx + dx + rng.uniform(-1.5, 1.5), base - h)], 0.4), 'G',
                  float(rng.uniform(0.6, 3.4)))
    # promenade fence along the bank (iron posts, a sagging top rail) with a bench and a dark lamp
    for fx in range(6, 586, 14):
        top_y = int(bank_top[min(VW - 1, fx)]) + 1
        p.put(p.box(fx, top_y - 7, fx + 1, top_y + 1), 'N', 1.4)
        p.put(p.box(fx, top_y - 8, fx + 1, top_y - 7), 'W', 6.0)
    for fx in range(6, 586):
        ty_ = int(bank_top[fx]) - 6 + int(round(0.8 * math.sin(math.pi * ((fx - 6) % 14) / 14)))
        p.put(p.box(fx, ty_, fx + 1, ty_ + 1), 'N', 2.0)
    bx0 = 214
    by0 = int(bank_top[bx0]) + 1
    p.put(p.box(bx0, by0 - 6, bx0 + 16, by0 - 5), 'G', 4.0)                          # bench back
    p.put(p.box(bx0, by0 - 3, bx0 + 16, by0 - 2), 'G', 3.4)                          # seat
    p.put(p.box(bx0, by0 - 4, bx0 + 16, by0 - 3), 'W', 6.4)                          # snow on the seat
    for lg in (bx0 + 1, bx0 + 14):
        p.put(p.box(lg, by0 - 2, lg + 1, by0 + 1), 'N', 1.2)
    lp = 472
    lpy = int(bank_top[lp]) + 1
    p.put(p.box(lp, lpy - 30, lp + 1, lpy + 1), 'N', 1.2)
    p.put(p.box(lp - 2, lpy - 34, lp + 3, lpy - 30), 'N', 1.8)
    p.put(p.box(lp - 2, lpy - 35, lp + 3, lpy - 34), 'W', 6.0)
    trunk = p.poly([(604, 324), (609, 270), (612, 242), (617, 242), (621, 270), (628, 324)])
    p.put(trunk, 'N', 1.2 + np.clip((xx - 604) / 22, 0, 1) * 1.0)
    for pts in (((614, 246), (590, 228), (566, 216)), ((614, 244), (619, 224), (611, 206)),
                ((616, 248), (637, 232), (652, 222)), ((590, 228), (582, 214)), ((596, 231), (600, 216)),
                ((619, 224), (631, 214)), ((614, 260), (597, 252), (585, 250)), ((566, 216), (558, 226)),
                ((570, 219), (566, 232)), ((582, 214), (576, 226))):
        br = p.line(list(pts), 0.8)
        p.put(br, 'N', 1.0)
        p.put(br & ~shift(br, 0, 1), 'W', 3.6)
    p.put(trunk & ~shift(trunk, 1, 0), 'D', 2.0)
    p.resolve(band=2.6)
    LAYOUT['bank_path_y'] = 299
    return p.L


# =========================================================================== trains
def _coach(p, x0, w, body_ramp, body_tone, lit, frame, stripe=None, pennant=False, boxcar=False, salon=False):
    """One coach on the TRAIN_H-row sprite, rail at row TRAIN_H - 2 (wheels hidden by the parapet later)."""
    yy, xx = p.yy, p.xx
    east = np.clip((xx - x0) / max(1, w), 0, 1)
    body = p.rr(x0 + 1, 9, x0 + w - 1, 26, 2)
    p.put(body, body_ramp, body_tone + east * 0.4)
    p.put(body & (yy >= 24), body_ramp, body_tone - 0.6)
    roof = p.rr(x0 + 1, 5, x0 + w - 1, 10, 3)
    p.put(roof, 'I', 2.6)
    p.put(roof & (yy < 7), 'W', 3.6)                                                  # snow on the roof
    p.put(p.box(x0 + 3, 9, x0 + w - 3, 10), 'I', 1.2)
    if stripe is not None:
        p.put(p.box(x0 + 2, 20, x0 + w - 2, 21) & body, stripe[0], stripe[1])
    if boxcar:
        door = p.box(x0 + w // 2 - 8, 11, x0 + w // 2 + 8, 25)
        p.put(door & ~kit.erode(door, 1), body_ramp, body_tone - 0.8)
        p.put(p.box(x0 + w // 2 - 8, 17, x0 + w // 2 + 8, 18), body_ramp, body_tone - 0.7)
        tm = C.text('4', '35')
        p.put(K.place(tm, p.w, p.h, x0 + 6, 13), 'W', 4.0)
        p.put(p.box(x0 + w // 2 + 10, 18, x0 + w // 2 + 13, 20), 'L', 1.8)        # lead seal plate
        p.put(p.box(x0 + w // 2 + 10, 18, x0 + w // 2 + 11, 19), 'C', 4.0)
    else:
        k = 0
        step = 9 if salon else 7
        ww = 6 if salon else 4
        for wx in range(x0 + 7, x0 + w - 8, step):
            win = p.box(wx, 12, wx + ww, 18)
            on = lit[k % len(lit)]
            p.put(win, 'L' if on else 'B', 2.2 + (k % 3) * 0.4 if on else 1.0, emis=on)
            if on:
                p.put(p.box(wx, 12, wx + ww, 13), 'L', 3.6, emis=True)
            k += 1
        for dx in (x0 + 2, x0 + w - 5):
            p.put(p.box(dx, 11, dx + 3, 25), body_ramp, body_tone - 0.7)
            p.put(p.box(dx + 1, 13, dx + 2, 16), 'B', 1.4)
    p.put(p.box(x0 + 1, 26, x0 + w - 1, 27), 'N', 1.0)
    for bx in (x0 + 9, x0 + w - 13):
        p.put(p.box(bx - 2, 26, bx + 6, 28), 'N', 0.6)
    p.put(p.box(x0 - 1, 21, x0 + 1, 23), 'I', 1.4)
    if pennant:
        p.put(p.box(x0 + w - 3, 0, x0 + w - 2, 6), 'I', 3.0)
        fl = [(x0 + w - 2, 0), (x0 + w + 3 + frame, 1 + frame * 0.5), (x0 + w - 2, 3)]
        p.put(p.poly(fl), 'C', 3.6 if frame == 0 else 3.0)


def _loco(p, x0, side, frame):
    """Steam locomotive (64 px) with tender (26 px); 'de' runs right (front at the right), 'su' runs left."""
    yy, xx = p.yy, p.xx
    f = (lambda dx: x0 + dx) if side == 'de' else (lambda dx: x0 + 90 - dx)       # dx from the tender end
    lo = lambda a, b: (min(a, b), max(a, b))                                         # noqa: E731
    body_r = 'B'
    a, b = lo(f(0), f(26))
    p.put(p.box(a + 1, 11, b - 1, 26), body_r, 2.0)
    p.put(p.box(a + 2, 9, b - 2, 12), 'N', 0.6)
    p.put(p.box(a + 2, 9, b - 2, 10), 'W', 3.0)                                       # snow on the coal
    p.put(p.box(a + 1, 11, b - 1, 12), 'I', 3.0)
    a, b = lo(f(26), f(41))
    p.put(p.box(a, 7, b, 26), body_r, 2.2)
    p.put(p.box(a - 1, 6, b + 1, 8), 'I', 3.0)
    p.put(p.box(a + 1, 5, b - 1, 7), 'W', 3.6)
    cw = a + 4 if side == 'de' else b - 8
    p.put(p.box(cw, 10, cw + 4, 16), 'L', 3.2, emis=True)                            # firelit cab window
    a, b = lo(f(41), f(86))
    boil = p.rr(a, 10, b, 22, 3)
    p.put(boil, body_r, 2.4 + np.clip((yy - 10) / 12, 0, 1) * -1.2)
    p.put(boil & (yy < 12), 'I', 4.2)
    p.put(boil & (yy < 11), 'W', 4.0)
    p.put(p.box(a, 22, b, 26), 'N', 0.8)
    dome_x = f(60)
    p.put(p.ell(dome_x, 10, 3.5, 2.5) & (yy < 10), 'I', 3.0)
    chim = f(78)
    p.put(p.box(chim - 2, 3, chim + 2, 10), 'I', 1.8)
    p.put(p.box(chim - 3, 3, chim + 3, 4), 'I', 3.2)
    front = f(90)
    fa, fb = lo(f(86), front)
    p.put(p.box(fa, 9, fb, 22), 'I', 1.6)
    hl = f(88)
    p.put(p.box(hl - 1, 11, hl + 1, 13), 'C', 5.0, emis=True)
    p.put(p.box(hl - 1, 18, hl + 1, 20), 'C', 4.4, emis=True)
    da, db = lo(f(82), f(83))
    p.put(p.box(da, 6, db + 1, 21), 'I', 3.4)                                         # smoke deflector
    if side == 'su':
        p.put(p.box(lo(f(70), f(84))[0], 18, lo(f(70), f(84))[1], 19), 'R', 2.0)      # red running board line
    LAYOUT['train_' + side]['chimney'] = [int(chim), 3]
    LAYOUT['train_' + side]['headlamp'] = [int(hl), 12]


def train_sheet(side):
    W = TRAIN_W
    sheet = np.zeros((TRAIN_H * 2, W, 4), np.uint8)
    LAYOUT['train_' + side] = {'front': W if side == 'de' else 0, 'y': TRAIN_DE_Y if side == 'de' else TRAIN_SU_Y,
                               'w': W, 'h': TRAIN_H}
    for fr in range(2):
        p = C.Paint(W, TRAIN_H, ramps_dawn(), 'train_' + side)
        if side == 'de':
            for i in range(4):
                _coach(p, i * 71, 71, 'B', 2.4, [1, 1, 0, 1, 0, 1, 1, 0] if i != 2 else [1, 1, 1, 1, 1, 1],
                       fr, stripe=('C', 2.4), pennant=True, salon=(i == 2))
            _loco(p, 286, 'de', fr)
        else:
            _loco(p, 0, 'su', fr)
            for i in range(3):
                _coach(p, 90 + i * 71, 71, 'T', 3.2, [0, 1, 1, 0, 1, 0, 0, 1], fr, stripe=('C', 2.0))
            _coach(p, 303, 71, 'T', 2.6, [], fr, boxcar=True)
        p.resolve(band=2.6)
        sheet[fr * TRAIN_H:(fr + 1) * TRAIN_H] = p.L.c
    return sheet


def train_de():
    return train_sheet('de')


def train_su():
    return train_sheet('su')


def smoke():
    """Eight frames of a steam puff growing and thinning (36 x 32 each), lit by the dawn from the east."""
    n, fw, fh = 8, 36, 32
    sheet = K.puff_sheet(n, fw, fh, ['#4F5E70', '#687789', '#8593A3', '#A1AAB7', '#C2C9D2', '#D3CDD3', '#E8DCD6'],
                         501, grow=(0.18, 0.5), thin=0.6, light=(0.7, -0.55), block=2)
    LAYOUT['smoke'] = {'frames': n}
    return sheet


def dawn_glow():
    """Additive warmth of the dawn (runtime fades it in): the band behind the city and the lit channel."""
    yy, xx = np.mgrid[0:VH, 0:VW].astype(np.float32)
    a = np.zeros((VH, VW, 3), np.float32)
    east = np.clip((xx - 160) / 480, 0, 1)
    band = np.clip(1 - np.abs(yy - 132) / 62, 0, 1) ** 1.6 * (0.2 + 0.8 * east) * (yy < 172)
    for c, v in enumerate((82, 50, 30)):
        a[..., c] += band * v
    water = (yy > WATER_Y) & (yy < 296)
    ref = np.clip(1 - np.abs(xx - 470) / 160, 0, 1) ** 1.3 * np.clip(1 - (yy - WATER_Y) / 52, 0, 1) * water
    for c, v in enumerate((46, 30, 16)):
        a[..., c] += ref * v
    return K.soft_quant(a, 6.0)


def fg_glow():
    """Halos of the parapet lanterns (additive, over trains and parapet)."""
    yy, xx = np.mgrid[0:VH, 0:VW].astype(np.float32)
    a = np.zeros((VH, VW, 3), np.float32)
    for lx in PARAPET_LAMPS:
        d = np.hypot((xx + 0.5 - lx - 0.5) / 14.0, (yy + 0.5 - (PARAPET_Y - 27)) / 10.0)
        g = np.clip(1 - d, 0, 1) ** 1.5
        for c, v in enumerate((60, 38, 16)):
            a[..., c] += g * v
    return K.soft_quant(a, 6.0)


def walker():
    """A woman pulling a child's sled with a milk can along the bank path: 6 walking frames (30 x 24)."""
    fw, fh, n = 30, 24, 6
    sheet = np.zeros((fh, fw * n, 4), np.uint8)
    R = C.ramps(N=SIL, W=SNOW, D=['#22150F', '#4A2D1F', '#6E3F22', '#9A5A2F'], R=['#4A1712', '#7A2218', '#A8382E'],
                I=STONE, F=['#3E2C3A', '#8A5550', '#B67D66'])
    for i in range(n):
        p = C.Paint(fw, fh, R, 'walker')
        ph = i / n * 2 * math.pi
        bob = 1 if i % 3 == 1 else 0
        # the sled behind her (she walks right): runners, slats, the milk can tied on, the rope
        p.put(p.box(1, 19, 12, 20), 'D', 2.6)
        p.put(p.box(0, 21, 13, 22), 'I', 4.6)
        p.put(p.box(12, 20, 14, 21), 'I', 4.6)
        p.put(p.box(1, 20, 2, 21) | p.box(11, 20, 12, 21), 'D', 1.4)
        can = p.rr(4, 11, 10, 19, 1)
        p.put(can, 'I', 5.0 + np.clip((p.xx - 4) / 6, 0, 1) * -1.6)
        p.put(p.box(4, 11, 10, 12), 'I', 6.6)
        p.put(p.box(6, 9, 8, 11), 'I', 3.0)
        p.put(p.line([(13, 19), (19, 14 + bob)], 0.45), 'N', 3.0)
        # her: a long dark coat, a red-brown headscarf, felt boots
        body = p.poly([(17, 8 + bob), (22, 8 + bob), (23.5, 16), (25, 20), (16, 20), (17, 15)])
        p.put(body, 'N', 2.0)
        p.put(body & ~shift(body, 1, 0), 'N', 4.0)
        p.put(body & ~shift(body, -1, 0), 'N', 1.0)
        arm = p.line([(18.5, 10 + bob), (19, 14 + bob)], 0.7)
        p.put(arm, 'N', 3.0)
        head = p.ell(20.0, 5.5 + bob, 2.4, 2.6)
        p.put(head, 'R', 1.8)
        p.put(p.box(21, 5 + bob, 23, 7 + bob), 'F', 1.4)                              # the face in profile
        p.put(p.box(19, 8 + bob, 22, 9 + bob), 'R', 1.0)                              # scarf knot
        lx = 19 + math.sin(ph) * 2.6
        rx = 21.5 - math.sin(ph) * 2.6
        p.put(p.line([(19.0, 20), (lx, 23.5)], 0.6) | p.line([(21.5, 20), (rx, 23.5)], 0.6), 'N', 1.2)
        p.resolve(band=2.0)
        sheet[:, i * fw:(i + 1) * fw] = p.L.c
    LAYOUT['walker'] = {'frames': n, 'w': fw, 'h': fh, 'y': 277}
    return sheet
