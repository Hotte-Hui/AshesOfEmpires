"""env_c3p2_cine_river -- the places of LS_C3_Halves, round 10 (owner: c3p2 places stream).

Before dawn on the riverside quay behind the palais (C3P2_DESIGN §2.9 / §5.2), painted as lit colour:
  h1_bg      the bench from behind and above: the far bank with the Line (a double fence on concrete posts, barbed
             wire, two watchtowers with their lamps, the dark houses behind, a few lit windows), the frozen river
             (snow drifts, pressure ridges, cracks, the fire's glow mirrored at the left, the towers' lamps in the
             ice), the stone balustrade under thick snow, the promenade with trodden tracks, the granite bench (a
             slab on two blocks, snow where nobody sits) in the figures stream's bench camera, so the men sit on it
  h2_bg      the promenade from the side: the far bank and the Line, the river, the balustrade, lanterns with snow
             caps, bare lime trees between them, their bench, a litter bin, the fire's glow from the west (left)
  h2_near    dark foreground framing (a lantern post and a tree trunk at the edges, drifted snow) for parallax
  h3_bg      wide: the palais on the near bank (dome and main block dark, the east wing burning: hot windows, the
             roof alight, soot over the windows), the quay wall, the river ice with the fire's mirror image, the far
             bank with the fence and the towers, the three-arch bridge with its lamps and the barrier of the Line
  board_bg   the departures board in the station hall (the round-8 layout of rows and cells, kept for the flaps):
             the iron roof with dawn in the glass, the board's frame on its chains, the hall clock, lamps
The runtime (scenes/cinematics/ch3_halves/ch3_halves.gd) adds snow, the searchlights and their pools on the ice,
smoke, flames, breath, crows at dawn, pigeons on the board and steam in the hall.
"""
from __future__ import annotations

import math

import numpy as np

import env_c3p2_cine_kit as Q
from env_c3p2_cine_kit import (C, K, VW, VH, NIGHT, SNOW, LAMP, IRON, OAK, PAPER, BRASS)
import env_c3p2_cine_life as LF
import pg

L = Q.LAYOUT.setdefault('halves', {})
EMBER = ['#1A0805', '#3A0F08', '#6E1E0C', '#A8381A', '#D8662A', '#F2A044', '#FCE0A0']
STONE = ['#06080C', '#0C1017', '#131922', '#1B232E', '#252F3C', '#313D4C', '#41505F', '#56677A']
ICE = ['#0A0F16', '#101823', '#18222F', '#202C3B', '#2A3848', '#36475A', '#4A5C70', '#62768C']
PAL_Q = LF.palette(NIGHT, SNOW, LAMP, STONE, ICE, EMBER, OAK[:6],
                   ['#2A1C18', '#3E2A22', '#5A3A2A', '#7A4A2E', '#4A3A36', '#66504A', '#8A6A5A', '#5A4A44',
                    '#76625A', '#927A6C', '#AE927E', '#C8A890', '#E8D0B8', '#9AA8B8', '#B8C4D0', '#3A3634'])

TOWERS = ((168, 94), (486, 90))        # far-bank watchtower lamps (h1)


# ================================================================================================ h1
def _far_bank(cv, y_water, y_top, towers, fire, scale=1.0, seed=0):
    """Houses behind the Line, the embankment, the double fence with barbed wire, watchtowers, lamps."""
    xx, yy = cv.xx, cv.yy
    rng = np.random.default_rng(1100 + seed)
    # houses: blocks of varying height, pitched and flat roofs, a few lit windows, chimneys
    x = -10.0
    while x < VW + 10:
        w = rng.uniform(26, 58) * scale
        h = rng.uniform(10, 26) * scale
        top = y_top + (26 * scale - h)
        blk = cv.box(x, top, x + w, y_water - 14 * scale)
        if rng.random() < 0.5:
            blk |= cv.poly([(x, top), (x + w, top), (x + w / 2, top - 7 * scale)])
        cv.put(blk, '#0C1017', 0.9 + fire[blk] * 0.0, z=400)
        cv.put(LF.edge_top(blk), '#41505F', 0.9)
        for wx in np.arange(x + 4 * scale, x + w - 5 * scale, 7 * scale):
            for wy in np.arange(top + 4 * scale, y_water - 18 * scale, 7 * scale):
                if LF.hsh(wx, wy, seed + 3.0) < 0.06:
                    cv.emit(cv.box(wx, wy, wx + 2 * scale, wy + 3 * scale), '#A8703A', 0.8)
        if rng.random() < 0.4:
            cx_ = x + w * rng.uniform(0.2, 0.8)
            cv.put(cv.box(cx_, top - 6 * scale, cx_ + 3 * scale, top), '#0C1017', 1.0)
        x += w + rng.uniform(-4, 6)
    # the embankment wall of the far bank, snow along its top
    emb = (yy >= y_water - 14 * scale) & (yy < y_water)
    cv.put(emb, '#1B232E', 0.85 + cv.nz(6, 1111 + seed)[emb] * 0.2)
    cv.put(emb & (np.mod(yy - y_water, 5 * scale) < 1), '#131922', 0.9)
    cv.put((yy >= y_water - 15 * scale) & (yy < y_water - 13 * scale), '#7D8796', 0.9)
    # the Line: two fences on concrete posts with barbed wire, the strip between them raked
    fy0, fy1 = y_water - 34 * scale, y_water - 14 * scale
    posts = (np.mod(xx, 11 * scale) < max(1.0, scale)) & (yy >= fy0) & (yy < fy1)
    cv.put(posts, '#252F3C', 1.0)
    for wy in np.arange(fy0 + 2 * scale, fy1, 4 * scale):
        cv.put((np.abs(yy - wy) < 0.5) & (np.mod(xx, 2) == 0), '#313D4C', 1.0)
    posts2 = (np.mod(xx + 5 * scale, 13 * scale) < max(1.0, scale * 0.8)) & (yy >= fy0 - 6 * scale) & (yy < fy0 + 4 * scale)
    cv.put(posts2, '#1B232E', 1.0)
    cv.put((np.abs(yy - (fy0 - 5 * scale)) < 0.5) & (np.mod(xx, 3) == 0), '#313D4C', 1.0)
    for i in range(0, VW, int(64 * scale)):
        lx = i + 30 * scale
        cv.emit(cv.ell(lx, fy0 - 2 * scale, 1.0, 1.0), '#DEE2E7')
    # watchtowers: legs, cabin, roof with snow, the lamp
    for (tx, ty) in towers:
        legs = cv.seg([(tx - 6 * scale, y_water - 14 * scale), (tx - 4 * scale, ty + 4 * scale)], max(0.6, 0.8 * scale)) | \
            cv.seg([(tx + 6 * scale, y_water - 14 * scale), (tx + 4 * scale, ty + 4 * scale)], max(0.6, 0.8 * scale))
        for k in range(1, 4):
            yk = ty + 4 * scale + (y_water - 18 * scale - ty) * k / 4
            legs |= cv.seg([(tx - 5 * scale, yk), (tx + 5 * scale, yk + 5 * scale)], 0.5)
        cv.put(legs, '#131922', 1.0)
        cab = cv.box(tx - 7 * scale, ty - 3 * scale, tx + 8 * scale, ty + 5 * scale)
        cv.put(cab, '#1B232E', 1.0)
        cv.emit(cv.box(tx - 5 * scale, ty - 1 * scale, tx + 6 * scale, ty + 2 * scale), '#3A4859', 0.8)
        roof = cv.poly([(tx - 9 * scale, ty - 3 * scale), (tx + 10 * scale, ty - 3 * scale), (tx + 0.5, ty - 8 * scale)])
        cv.put(roof, '#131922', 1.0)
        LF.snowcap(cv, roof, 2, '#A1AAB7', 1113 + int(tx))
        cv.emit(cv.box(tx - 1, ty, tx + 2, ty + 3), '#F2F3F5')


def _ice(cv, m, y0, y1, fire, seed, refl_x=None):
    """Frozen river: dark ice with a little sky in it, wind-packed snow in long low drifts, a few pressure
    ridges and cracks, the fire mirrored as soft vertical streaks (refl_x = (x0, x1) of the burning wing)."""
    xx, yy = cv.xx, cv.yy
    u = np.clip((yy - y0) / max(1.0, y1 - y0), 0, 1)
    n1 = LF.nz(VW, VH, 22, seed, 3)
    cv.put(m, '#202C3B', 0.66 + n1[m] * 0.14 + u[m] * 0.3)
    drift = m & (LF.vnoise(xx * 0.022 + n1 * 2.0, yy * 0.16, seed + 1) > 0.58)
    cv.put(drift, '#4A5C70', 0.62 + u[drift] * 0.3 + LF.nz(VW, VH, 3, seed + 2, 2)[drift] * 0.12)
    cv.put(drift & LF.edge_top(drift), '#62768C', 0.7 + u[drift & LF.edge_top(drift)] * 0.3)
    ridge = m & (np.abs(yy - (y0 + (y1 - y0) * 0.45 + np.sin(xx * 0.025) * 3 + LF.vnoise(xx * 0.04, 2.0, seed + 3) * 5)) < 0.8) &         (LF.vnoise(xx * 0.05, 5.0, seed + 4) > 0.35)
    cv.put(ridge, '#62768C', 0.8)
    crack = m & (np.abs(LF.nz(VW, VH, 11, seed + 5, 3) - 0.5) < 0.008)
    cv.put(crack, '#101823', 1.0)
    # the fire's glow on the ice (soft, dithered) and its mirror image in vertical streaks
    g = np.clip(fire * 1.3, 0, 1) * (0.55 + 0.45 * LF.vnoise(xx * 0.45, yy * 0.04, seed + 6))
    th = 0.25 + 0.5 * pg.bayer(VW, VH, 0, 0)
    glow_m = m & (g > th)
    cv.add(glow_m, '#4A2410', np.clip(g[glow_m] * 1.1, 0.2, 1.0))
    if refl_x is not None:
        x0, x1 = refl_x
        st = m & (xx > x0) & (xx < x1) & (LF.vnoise(xx * 0.6, yy * 0.03, seed + 7) > 0.55) &             ((1 - u) * (0.6 + 0.6 * LF.vnoise(xx * 0.2, yy * 0.08, seed + 8)) > 0.42)
        cv.add(st, '#7A3A16', np.clip(1.3 - u[st] * 1.2, 0.2, 1.2))


def _bench_geometry():
    """Screen geometry of the granite bench from the figures stream's bench camera (env_c3p2_cine_hero): slab top
    x0, y0 (far edge), x1, y1 (near edge), the front face's bottom y, the two blocks' x ranges."""
    try:
        import env_c3p2_cine_hero as HR
        cam = HR.bench_cam()
        sy = getattr(HR, 'BENCH_SEAT_Y', -100.0)
        a = cam.px((260.0, sy, -30.0))
        b = cam.px((-260.0, sy, 40.0))
        c = cam.px((0.0, sy + 20.0, -30.0))
        blocks = []
        for X in (190.0, -190.0):
            p0 = cam.px((X + 32.0, sy + 20.0, -26.0))
            p1 = cam.px((X - 32.0, sy + 20.0, -26.0))
            blocks.append((min(p0[0], p1[0]), max(p0[0], p1[0])))
        return float(a[0]), float(b[1]), float(b[0]), float(a[1]), float(c[1]), blocks
    except Exception:
        return 133.0, 256.5, 507.0, 275.3, 288.7, [(155.0, 201.0), (439.0, 485.0)]


def h1_bg():
    cv = LF.Cv(VW, VH, 0, 0, amb=(0.30, 0.34, 0.46))
    xx, yy = cv.xx, cv.yy
    fire = cv.light(-90, 170, 560, (1.2, 0.55, 0.22), 1.25)
    n1 = cv.nz(16, 1101)
    n2 = cv.nz(4, 1103)
    # sky: snow clouds, smoke drifting in from the left lit by the fire, the city glow low
    sky = yy < 96
    cl = LF.nz(VW, VH, 30, 1105, 4)
    cv.put(sky, '#1A2431', 0.5 + cl[sky] * 0.35 + (yy[sky] - 46) / 120.0)
    smoke = sky & (cl + (1 - xx / 640.0) * 0.35 > 0.72)
    cv.mix(smoke, '#5A3A2A', np.clip(1 - xx / 500.0, 0, 1) * 0.6)
    _far_bank(cv, 128, 74, TOWERS, fire)
    # the frozen river
    ice = (yy >= 128) & (yy < 197)
    _ice(cv, ice, 128, 197, fire, 1150)
    for (tx, ty) in TOWERS:
        col = ice & (np.abs(xx - tx - np.sin(yy * 0.9) * 0.8) < 0.8) & (LF.vnoise(xx * 0.3, yy * 0.5, 1159) > 0.5)
        cv.add(col, '#3A4859', 1.0)
    # the balustrade: handrail under a thick pillow of snow, vase balusters, plinth
    rail = (yy >= 199) & (yy < 207)
    cv.put(rail, '#313D4C', 0.95 + n2[rail] * 0.1)
    snow_r = (yy >= 193 + LF.vnoise(xx * 0.08, 0.0, 11) * 3) & (yy < 200)
    cv.put(snow_r, '#C2C9D2', 0.92 + n2[snow_r] * 0.1)
    cv.put(LF.edge_top(snow_r), '#DEE2E7', 0.95)
    bx = np.mod(xx - 4, 22)
    prof = 4.6 - np.abs(yy - 216) * 0.12 + np.where(np.abs(yy - 211) < 2, 1.2, 0)
    bal = (yy >= 207) & (yy < 226) & (np.abs(bx - 11) < prof)
    cv.put(bal, '#313D4C', 0.75 + np.clip((11 - bx) / 8.0, -0.3, 0.4))
    cv.put((yy >= 207) & (yy < 226) & ~bal, '#0A0F16', 1.0)
    cv.put((yy >= 207) & (yy < 213) & ~bal & (np.mod(xx + yy, 2) == 0), '#18222F', 1.0)
    plinth = (yy >= 226) & (yy < 236)
    cv.put(plinth, '#252F3C', 0.9 + n2[plinth] * 0.1)
    cv.put(plinth & (yy < 228), '#A1AAB7', 0.8)
    # the promenade: snow, trodden tracks to the bench and along the quay
    pave = yy >= 236
    v = (yy - 236) / 78.0
    cv.put(pave, '#7D8796', 0.62 + n1[pave] * 0.12 + v[pave] * 0.12)
    track = pave & (np.abs(yy - 246 - np.sin(xx * 0.02) * 2) < 3.5) & (LF.vnoise(xx * 0.4, yy * 0.4, 13) > 0.45)
    cv.put(track, '#4F5E70', 0.75)
    prints = pave & (yy > 270) & (np.abs(xx - 320 - (yy - 270) * 0.3) < 22) & (LF.vnoise(xx * 0.7, yy * 0.9, 17) > 0.7)
    cv.put(prints, '#4F5E70', 0.7)
    # the granite bench (slab on two blocks) in the bench camera of the figures stream, so the men sit on it
    x0, y0, x1, y1, front_y, blocks = _bench_geometry()
    top = cv.poly([(x0, y1), (x1, y1), (x1, y0), (x0, y0)])
    cv.put(top, '#41505F', 0.8 + n2[top] * 0.12 + np.clip((yy[top] - y0) / 40.0, 0, 0.3))
    cv.put(top & (LF.nz(VW, VH, 2, 1125, 2) > 0.7), '#56677A', 0.85)
    front = cv.box(x0, y1, x1 + 1, front_y)
    cv.put(front, '#252F3C', 0.85 + n2[front] * 0.1)
    cv.put(LF.edge_top(front), '#62768C', 0.9)
    for (bx0, bx1) in blocks:
        blk = cv.box(bx0, front_y, bx1, 360)
        cv.put(blk, '#1B232E', 0.85 + n2[blk] * 0.1)
        cv.put(blk & (cv.xx < bx0 + 2), '#313D4C', 0.9)
    # snow on the slab where nobody sits, trodden snow in front, a few prints from the stairs
    snow_s = top & ((xx < x0 + 44) | (xx > x1 - 44)) & (yy < y0 + 4 + LF.vnoise(xx * 0.2, 1.0, 19) * 16)
    snow_s |= top & ((xx < x0 + 30) | (xx > x1 - 30))
    cv.put(snow_s & (LF.nz(VW, VH, 5, 1123, 2) > 0.3), '#C2C9D2', 0.9)
    cv.put(LF.edge_top(front) & ((xx < x0 + 44) | (xx > x1 - 44)), '#DEE2E7', 0.9)
    out = cv.quant(PAL_Q, spread=10.0)
    out[..., 3] = 255
    L['bench'] = [round(x0), round(y0), round(x1), round(y1)]
    L['stack_ru'] = [276, 262]
    L['stack_de'] = [364, 262]
    L['towers'] = [list(t) for t in TOWERS]
    L['ice_y'] = [128, 196]
    return out


def h1_glow():
    blobs = [(-40, 170, 330, 160, (64, 28, 8), 1.4), (120, 180, 160, 30, (40, 18, 6), 1.5)]
    for (tx, ty) in TOWERS:
        blobs.append((tx + 0.5, ty + 1, 14, 10, (40, 44, 50), 1.5))
    return Q.glow_sprite(VW, VH, blobs, 6.0)


# ================================================================================================ h2
PROM_Y = 290
LANTERNS = (96, 256, 416, 576)


def h2_bg():
    cv = LF.Cv(VW, VH, 0, 0, amb=(0.30, 0.34, 0.46))
    xx, yy = cv.xx, cv.yy
    fire = cv.light(-110, 170, 520, (1.15, 0.52, 0.2), 1.25)
    for lx in LANTERNS:
        cv.light(lx, 150, 90, (1.2, 0.85, 0.45), 1.5)
        cv.light(lx, PROM_Y, 80, (1.1, 0.75, 0.4), 1.5, sy=0.35)
    n1 = cv.nz(14, 1201)
    n2 = cv.nz(4, 1203)
    sky = yy < 98
    cl = LF.nz(VW, VH, 30, 1205, 4)
    cv.put(sky, '#1A2431', 0.5 + cl[sky] * 0.35 + (yy[sky] - 46) / 140.0)
    smoke = sky & (cl + (1 - xx / 640.0) * 0.3 > 0.74)
    cv.mix(smoke, '#5A3A2A', np.clip(1 - xx / 420.0, 0, 1) * 0.55)
    _far_bank(cv, 118, 84, ((190, 92), (470, 90)), fire, scale=0.8, seed=5)
    ice = (yy >= 118) & (yy < 172)
    _ice(cv, ice, 118, 172, fire, 1250)
    # balustrade (side on): rail with snow, balusters, plinth
    rail = (yy >= 172) & (yy < 180)
    cv.put(rail, '#313D4C', 0.95)
    snow_r = (yy >= 166 + LF.vnoise(xx * 0.08, 0.0, 33) * 3) & (yy < 173)
    cv.put(snow_r, '#C2C9D2', 0.9)
    bx = np.mod(xx, 18)
    bal = (yy >= 180) & (yy < 204) & (np.abs(bx - 9) < 3.6 - np.abs(yy - 192) * 0.08 + np.where(np.abs(yy - 185) < 2, 1.0, 0))
    cv.put((yy >= 180) & (yy < 204), '#0A0F16', 1.0)
    cv.put(bal, '#313D4C', 0.8)
    cv.put((yy >= 204) & (yy < 214), '#252F3C', 0.9)
    cv.put((yy >= 204) & (yy < 206), '#A1AAB7', 0.8)
    # promenade
    pave = yy >= 214
    v = (yy - 214) / 100.0
    cv.put(pave, '#7D8796', 0.62 + n1[pave] * 0.12 + v[pave] * 0.1)
    cv.put(pave & (np.abs(yy - PROM_Y - 2) < 5) & (LF.vnoise(xx * 0.3, yy * 0.5, 35) > 0.5), '#4F5E70', 0.8)
    # bare lime trees between the lanterns (behind the walkers), snow on their branches
    for i, tx in enumerate((176, 336, 496)):
        LF.tree(cv, tx, 230, 150, 1211 + i, col='#0C1017', snow='#A1AAB7', spread=1.05, trunk_r=3.0)
        cv.put(cv.ell(tx, 231, 10, 2.5), '#A1AAB7', 0.85)
    # lanterns: cast-iron posts with glass globes and snow caps
    for lx in LANTERNS:
        LF.lamp_post(cv, lx, PROM_Y - 2, 150, col='#0C1017', style='globe')
    # the bench in the middle (their bench), seen from the side, a litter bin beside it
    seat = cv.box(292, 266, 352, 271)
    cv.put(seat, '#553826', 0.9)
    back = cv.box(294, 248, 350, 252) | cv.box(294, 256, 350, 260)
    cv.put(back, '#553826', 0.85)
    ends = cv.seg([(296, 246), (298, 268), (294, PROM_Y)], 1.4) | cv.seg([(348, 246), (346, 268), (350, PROM_Y)], 1.4)
    cv.put(ends, '#131922', 1.0)
    LF.snowcap(cv, seat | back, 2, '#C2C9D2', 1221)
    binm = cv.box(372, 266, 382, PROM_Y)
    cv.put(binm, '#252F3C', 0.9)
    cv.put(cv.ell(377, 266, 6, 2), '#C2C9D2', 0.9)
    out = cv.quant(PAL_Q, spread=10.0)
    out[..., 3] = 255
    L['prom_y'] = PROM_Y
    L['lanterns'] = list(LANTERNS)
    return out


def h2_near():
    """Foreground framing for parallax (700 x 300 at (-30, 60)): a lantern post at the left edge, a tree trunk at
    the right, drifted snow along the bottom."""
    x0, y0, w, h = -30, 60, 700, 300
    cv = LF.Cv(w, h, x0, y0, amb=(0.16, 0.18, 0.24))
    cv.light(320, 200, 600, (0.25, 0.22, 0.2), 1.2)
    post = cv.seg([(4, 360), (6, 70)], 4.0, 3.0)
    cv.put(post, '#05070C', 1.0)
    cv.put(cv.box(-6, 60, 18, 70), '#05070C', 1.0)
    trunk = cv.seg([(632, 360), (630, 200), (636, 120), (644, 60)], 9.0, 6.0)
    cv.put(trunk, '#05070C', 1.0)
    br = cv.seg([(630, 170), (600, 120), (590, 90)], 2.2, 1.0) | cv.seg([(634, 140), (610, 100)], 1.6, 0.8)
    cv.put(br, '#05070C', 1.0)
    LF.snowcap(cv, br | trunk, 2, '#4F5E70', 1231)
    drift = (cv.yy > 300 + LF.vnoise(cv.xx * 0.03, 0.0, 37) * 10)
    cv.put(drift, '#3A4859', 0.9 + LF.nz(w, h, 5, 1233, 2)[drift] * 0.2)
    cv.put(LF.edge_top(drift), '#687789', 0.9)
    out = cv.quant(PAL_Q, spread=8.0)
    L['h2_near_at'] = [x0, y0]
    return out


def h2_glow():
    return Q.glow_sprite(VW, VH, [(x, 142, 34, 36, (60, 44, 22), 1.4) for x in LANTERNS] +
                         [(x, PROM_Y, 54, 12, (40, 28, 12), 1.4) for x in LANTERNS] +
                         [(-60, 170, 300, 160, (70, 30, 8), 1.4)], 6.0)


# ================================================================================================ h3
H3_HORIZON = 150


def h3_bg():
    cv = LF.Cv(VW, VH, 0, 0, amb=(0.26, 0.30, 0.42))
    xx, yy = cv.xx, cv.yy
    fire = cv.light(214, 128, 300, (1.5, 0.66, 0.24), 1.3)
    cv.light(214, 250, 180, (0.9, 0.4, 0.14), 1.4)
    n1 = cv.nz(18, 1301)
    n2 = cv.nz(4, 1303)
    sky = yy < H3_HORIZON
    cl = LF.nz(VW, VH, 34, 1305, 4)
    cv.put(sky, '#1A2431', 0.45 + cl[sky] * 0.3 + (yy[sky] - 46) / 140.0)
    # (round 11: the smoke column is its own soft layer, h3_plume, drawn over the sky by the runtime)
    # far bank: houses, the Line's fence and towers, the bridge with the barrier
    _far_bank(cv, H3_HORIZON, H3_HORIZON - 30, ((372, H3_HORIZON - 40), (500, H3_HORIZON - 40)), fire, scale=0.6, seed=9)
    br = (xx >= 540) & (yy >= H3_HORIZON - 20) & (yy < H3_HORIZON + 10)
    arches = br & (yy > H3_HORIZON - 12) & (np.hypot(np.mod(xx - 540, 34) - 17, (yy - (H3_HORIZON + 10)) * 1.2) < 14)
    cv.put(br & ~arches, '#252F3C', 1.0)
    cv.put(br & (yy < H3_HORIZON - 17), '#A1AAB7', 0.85)
    cv.put(br & (yy >= H3_HORIZON - 17) & (yy < H3_HORIZON - 14) & (np.mod(xx, 4) < 1), '#0C1017', 1.0)
    for bx in range(548, 640, 17):
        cv.put(cv.box(bx, H3_HORIZON - 30, bx + 1, H3_HORIZON - 19), '#0C1017', 1.0)
        cv.emit(cv.ell(bx + 0.5, H3_HORIZON - 31, 1.2, 1.2), '#FCE2B0' if (bx // 17) % 2 == 0 else '#5A3A1C')
    cv.put(cv.box(574, H3_HORIZON - 25, 600, H3_HORIZON - 23) & (np.mod(xx, 4) < 2), '#A8382E', 1.0)
    cv.put(cv.box(578, H3_HORIZON - 26, 580, H3_HORIZON - 19), '#252F3C', 1.0)
    # the palais on the near bank: main block and dome dark, the east wing (right part) burning
    bx0, bx1, top = 0, 300, 92
    body = (xx < bx1) & (yy >= top) & (yy < 206)
    cv.put(body, '#1B232E', 0.75 + n1[body] * 0.12)
    for px_ in range(8, bx1, 19):
        cv.put(body & (np.abs(xx - px_ + 4) < 1), '#252F3C', 0.9)
    cv.put((xx < bx1) & (yy >= top - 3) & (yy < top), '#A1AAB7', 0.85)
    roof = (xx < bx1) & (yy >= top - 16) & (yy < top - 3) & (np.abs(xx - 150) < 150 - (top - 3 - yy) * 0.8)
    cv.put(roof, '#131922', 0.9)
    drum = cv.box(40, top - 30, 88, top - 14)
    cv.put(drum, '#1B232E', 0.85)
    for dx_ in range(44, 88, 8):
        cv.put(cv.box(dx_, top - 27, dx_ + 3, top - 18), '#0A0E16', 1.0)
    dome = cv.ell(64, top - 30, 28, 24) & (yy < top - 30)
    cv.put(dome, '#2C4448', 0.62 + C.edge_light(dome, (0.9, -0.2), width=5.0, soft=1)[dome] * 0.8)
    cv.put(dome & (np.mod(xx - 64, 7) < 1), '#1E3036', 1.0)
    cv.put(cv.box(60, top - 64, 68, top - 52), '#1E3036', 1.0)
    cv.put(LF.edge_top(dome) | cv.box(58, top - 66, 70, top - 64), '#7D8796', 0.85)
    cv.put(cv.box(38, top - 33, 90, top - 30), '#7D8796', 0.8)
    for dx_ in range(110, 290, 26):
        dm = cv.box(dx_, top - 13, dx_ + 9, top - 4)
        cv.put(dm, '#1B232E', 0.95)
        if dx_ > 160:
            cv.emit(cv.box(dx_ + 2, top - 11, dx_ + 7, top - 5), '#D8662A', 0.9)
        else:
            cv.put(cv.box(dx_ + 2, top - 11, dx_ + 7, top - 5), '#0A0E16', 1.0)
    for i, wx in enumerate(range(10, bx1 - 6, 19)):
        for j, wy in enumerate((106, 136, 168)):
            w_ = cv.box(wx, wy, wx + 9, wy + 16)
            east = wx > 150
            hot = east and not (j == 0 and i % 3 == 1)
            if hot:
                cv.emit(w_, '#D8662A', 0.75 + n2[w_] * 0.35 - (yy[w_] - wy) / 40.0)
                cv.emit(w_ & (yy >= wy + 10), '#F2A044', 0.9)
                soot = cv.box(wx - 1, wy - 7, wx + 10, wy)
                cv.put(soot, '#06080C', 1.0)
            else:
                cv.put(w_, '#0A0E16', 1.0)
    # the burning roof of the east wing: glow along the ridge, holes
    cv.emit(cv.box(156, top - 6, bx1, top - 2) & (LF.nz(VW, VH, 3, 1311, 2) > 0.45), '#A8381A', 1.0)
    # the quay beyond the palais: snow, a railing and a lamp
    qy = cv.box(300, H3_HORIZON, 336, 206)
    cv.put(qy, '#7D8796', 0.55 + cv.nz(5, 1371)[qy] * 0.15)
    cv.put(cv.box(300, 196, 336, 198) | (cv.box(300, 198, 336, 206) & (np.mod(xx, 4) < 1)), '#0C1017', 1.0)
    cv.put(cv.box(318, 160, 319, 196), '#0C1017', 1.0)
    cv.emit(cv.ell(318.5, 159, 1.6, 1.8), '#FCE2B0')
    # the quay wall of the near bank with two lamps
    qw = (yy >= 206) & (yy < 216) & (xx < 336)
    cv.put(qw, '#252F3C', 0.85 + n2[qw] * 0.1)
    cv.put((yy >= 204) & (yy < 206) & (xx < 336), '#A1AAB7', 0.85)
    for lx in (40, 250):
        cv.put(cv.box(lx, 186, lx + 1, 204), '#0C1017', 1.0)
        cv.emit(cv.ell(lx + 0.5, 185, 1.6, 1.8), '#FCE2B0')
    # the river ice across the frame: snow drifts, ridges, the fire's mirror image under the wing
    ice = (yy >= H3_HORIZON + 2) & ~((yy < 216) & (xx < 336) & (yy >= 92))
    ice &= ~((xx < bx1) & (yy < 206))
    _ice(cv, ice, H3_HORIZON, VH, fire, 1350, refl_x=(150, 304))
    for wx in range(158, 300, 19):
        streak = ice & (np.abs(xx - wx - 4) < 2) & (yy > 216) & (yy < 300) & (LF.vnoise(xx * 0.5, yy * 0.15, 1361) > 0.4)
        cv.add(streak, '#5A2A12', np.clip(1.2 - (yy[streak] - 216) / 90.0, 0.2, 1.0))
    out = cv.quant(PAL_Q, spread=10.0)
    out[..., 3] = 255
    L['h3_towers'] = [[372, H3_HORIZON - 40], [500, H3_HORIZON - 40]]
    L['h3_fire'] = [[172, 110], [210, 104], [248, 112], [286, 118], [230, 140], [192, 84], [262, 82], [240, 170]]
    L['h3_horizon'] = H3_HORIZON
    return out


def h3_dawn():
    """Additive first grey of dawn (east, right), faded in at runtime: the whole sky lifts from black to a deep
    slate, a broad pale band rises over the far bank, a thin rose-grey line sits on the horizon at the right, the
    ice takes a little of it."""
    a = np.zeros((VH, VW, 3), np.float32)
    yy, xx = np.mgrid[0:VH, 0:VW].astype(np.float32)
    sky = np.clip(1.0 - (H3_HORIZON - yy) / 150.0, 0, 1) * (yy < H3_HORIZON + 2)
    a += (sky * (0.45 + 0.55 * xx / VW))[..., None] * np.array([22, 26, 36], np.float32)
    Q.add_glow(a, 600, H3_HORIZON - 4, 520, 96, (38, 42, 56), 1.25)
    Q.add_glow(a, 640, H3_HORIZON - 3, 300, 22, (54, 42, 46), 1.4)
    ice = np.clip(1.0 - (yy - H3_HORIZON) / 120.0, 0, 1) * (yy > H3_HORIZON + 2) * (xx > 300)
    a += (ice * 0.6)[..., None] * np.array([14, 16, 22], np.float32)
    return K.soft_quant(a, 2.0)


def h3_plume():
    """The smoke column of the burning east wing (soft RGBA, full frame): it rises from the roof's fire, leans east
    with the wind and widens into a flat drifting cloud high over the river; the fire lights its foot orange, its
    high flank catches the first grey of dawn; billows all the way, soft at every edge."""
    rng = np.random.default_rng(1313)
    lobes = []
    for k in range(70):
        s_ = (k + rng.uniform(0, 1)) / 70.0
        cx = 214 + 300 * s_ ** 1.5 + rng.uniform(-8, 8) * (0.4 + s_)
        cy = 92 - 104 * s_ ** 0.8 + rng.uniform(-6, 6) * (0.4 + s_)
        r = 9 + 46 * s_ + rng.uniform(-3, 5) * (0.5 + s_)
        a = 0.95 - 0.35 * s_
        fire = max(0.0, 1.0 - s_ * 2.2)
        lobes.append((cx, cy, r, a, fire))
    # the column's foot over the burning roof
    for x_ in (170, 196, 222, 248, 276):
        lobes.append((x_ + rng.uniform(-4, 4), 86 + rng.uniform(-4, 2), 12 + rng.uniform(0, 5), 0.9, 1.0))
    ramp = ['#0E0C0D', '#171314', '#211A19', '#2C221E', '#3A2C24', '#523826', '#6E4628', '#8E5A2E', '#B07038']
    return LF.soft_plume(VW, VH, lobes, ramp, light=(-0.1, 1.0), alpha=0.92, seed=1315, cool=(16, 18, 26))


def h3_glow():
    return Q.glow_sprite(VW, VH, [(226, 120, 190, 110, (96, 42, 10), 1.3), (226, 260, 110, 90, (60, 26, 6), 1.4),
                                  (40, 185, 10, 10, (40, 30, 14), 1.4), (250, 185, 10, 10, (40, 30, 14), 1.4)], 6.0)


# ================================================================================================ h4 board
def board_bg():
    """The departures board in the station hall at first light (rows and cells as in round 8)."""
    import env_c3p2_cine_quay as QY
    cv = LF.Cv(VW, VH, 0, 0, amb=(0.30, 0.32, 0.40))
    xx, yy = cv.xx, cv.yy
    cv.light(320, 0, 520, (0.55, 0.62, 0.78), 1.3)
    cv.light(60, 70, 120, (1.0, 0.7, 0.36), 1.5)
    cv.light(580, 70, 120, (1.0, 0.7, 0.36), 1.5)
    n1 = cv.nz(14, 1401)
    # the hall: iron arches and glazing bars with dawn in the glass, the back wall
    cv.put(cv.full(), '#1B232E', 0.8 + n1 * 0.1)
    glass = yy < 66
    cv.put(glass, '#4A5C70', 0.7 + (66 - yy[glass]) / 60.0 * 0.4)
    bars = glass & ((np.mod(xx, 40) < 2) | (np.mod(yy, 12) < 1))
    cv.put(bars, '#0C1017', 1.0)
    arch = (np.abs(np.hypot((xx - 320) / 340.0, (yy - 120) / 90.0) - 1.0) < 0.012)
    cv.put(arch, '#0C1017', 1.0)
    # the board's chains and its brass frame
    x0, y0, x1, y1 = QY.BOARD
    for cx in (x0 + 40, x1 - 40):
        for cy in range(40, y0 - 6, 4):
            cv.put(cv.ell(cx + (cy // 4 % 2), cy, 1.2, 2.0), '#2A1D0B', 1.0)
    fr = cv.box(x0 - 6, y0 - 6, x1 + 6, y1 + 6)
    cv.put(fr, '#73531F', 0.9 + C.edge_light(fr, (0.0, -1.0), width=3.0, soft=1) * 0.8)
    cv.put(fr & ((yy == y0 - 6) | (xx == x0 - 6)), '#E8C779', 0.9)
    for (ox, oy) in ((x0 - 6, y0 - 6), (x1 + 2, y0 - 6), (x0 - 6, y1 + 2), (x1 + 2, y1 + 2)):
        cv.put(cv.box(ox, oy, ox + 4, oy + 4), '#C49A48', 1.0)
    panel = cv.box(x0, y0, x1, y1)
    cv.put(panel, '#121318', 0.9)
    head = cv.box(x0, y0, x1, y0 + 30)
    cv.put(head, '#1C2E50', 0.95)
    tm = K.vtext('ABFAHRT · ОТПРАВЛЕНИЕ · DEPART', 'l', 2)
    sm = K.place(tm, VW, VH, 320 - tm.shape[1] // 2, y0 + 10)
    cv.emit(sm & head, '#DEE2E7')
    for ry in QY.ROWS_Y:
        cv.put(cv.box(x0 + 8, ry + QY.CELL[1] + 6, x1 - 8, ry + QY.CELL[1] + 7), '#24252C', 1.0)
    # wall lamps either side of the board
    for lx in (18, 622):
        cv.put(cv.seg([(lx, 110), (lx, 82)], 1.0), '#0C1017', 1.0)
        cv.emit(cv.ell(lx, 78, 4, 5), '#FCE2B0')
    pal = LF.palette(NIGHT, SNOW, LAMP, BRASS, STONE, ICE,
                     ['#06070A', '#0C0D11', '#121318', '#1A1B21', '#24252C', '#0A1424', '#122038', '#1C2E50', '#2A4070'])
    img = cv.quant(pal, spread=8.0)
    img[..., 3] = 255
    cells = {c: QY._glyph_cell(c) for c in QY.CHARSET}
    for r, text in enumerate(QY.BOARD_ROWS):
        for i, ch in enumerate(text.upper()):
            Q.blit(img, cells.get(ch, cells[' ']), QY.ROW_X + i * QY.CELL[0], QY.ROWS_Y[r])
    for i in range(len(QY.FRESH)):
        Q.blit(img, cells[' '], QY.ROW_X + i * QY.CELL[0], QY.ROWS_Y[QY.FRESH_ROW])
    L['rows_y'] = list(QY.ROWS_Y)
    L['row_x'] = QY.ROW_X
    L['fresh_row'] = QY.FRESH_ROW
    L['fresh'] = QY.FRESH
    L['board_ledge'] = [x0 - 6, y0 - 6, x1 + 6]
    return img
