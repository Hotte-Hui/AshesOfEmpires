"""env_veltrava_cine_close -- art of LS_C3_Close (owner: cinematics stream).

n1  platform 5 at 23.40, one-point perspective down the track (pinhole PROJ shared with
    scenes/cinematics/ch3_close/ch3_close.gd, which draws the departing special train in the same projection):
    the canopy and its lamps, the empty dual-gauge track, the dark yard beyond, the split-flap indicator.
n2  the station square at night in snow: two hotels far apart, one lit window each (Konrad left, Alexei
    right), a street lamp, a parked car under the limes with someone smoking in it.
Called by env_veltrava_cine.main(); every function returns RGBA arrays (or MLayers).
"""
from __future__ import annotations

import math

import numpy as np

import env_veltrava_cine as C
import env_veltrava_cine_kit as K
import pg

VW, VH = C.VW, C.VH
V = C.V
PROJ = {'vpx': 236.0, 'vpy': 168.0, 'f': 420.0, 'eye': 1.7}
LAYOUT = C.LAYOUT.setdefault('close', {})
LAYOUT['proj'] = dict(PROJ)
LAMPS_Z = [6.0, 16.0, 26.0, 36.0, 46.0, 56.0]
LAMP_X, LAMP_Y = 0.8, 3.75
CANOPY_Y = 4.35
EDGE_X = 1.0
RAILS = (2.18, 3.62)          # broad-gauge pair ...
RAILS_STD = (2.18, 3.29)      # ... and the inner standard-gauge rail (four-rail dual gauge, WORLD_BIBLE)

NIGHT = ['#05070C', '#070A12', '#0C111C', '#121A26', '#1A2431', '#1E2836', '#2A3646', '#3A4859', '#4F5E70',
         '#687789', '#8593A3']
LAMPR = ['#22150F', '#4A2D1F', '#6E3F22', '#A8643A', '#D08F55', '#EDB777', '#FCE2B0']
SNOWR = ['#1A2431', '#2A3646', '#3A4859', '#4F5E70', '#687789', '#7D8796', '#A1AAB7', '#C2C9D2', '#DEE2E7']
IRONR = ['#05070C', '#0C111C', '#15171C', '#22262D', '#323840', '#464D55', '#5E666E']


def proj(x, y, z):
    zz = max(z, 0.3)
    return (PROJ['vpx'] + PROJ['f'] * x / zz, PROJ['vpy'] - PROJ['f'] * (y - PROJ['eye']) / zz)


def _grid():
    return np.mgrid[0:VH, 0:VW].astype(np.float32)


def plane_y(yy, xx, y_world):
    """For a horizontal plane at height y_world: per-pixel depth z and lateral x (nan where not visible)."""
    dy = yy - PROJ['vpy']
    with np.errstate(divide='ignore', invalid='ignore'):
        z = -PROJ['f'] * (y_world - PROJ['eye']) / dy
        x = (xx - PROJ['vpx']) * z / PROJ['f']
    bad = ~(z > 0.2)
    z = np.where(bad, np.nan, z)
    x = np.where(bad, np.nan, x)
    return z, x


def lamp_pool(z, x, strength=1.0):
    """Warm light on the platform/track from the canopy lamps (falls off with distance)."""
    out = np.zeros(np.shape(z), np.float32)
    for lz in LAMPS_Z:
        d = np.hypot(np.nan_to_num(z, nan=1e3, posinf=1e3, neginf=1e3) - lz,
                     (np.nan_to_num(x, nan=1e3, posinf=1e3, neginf=1e3) - LAMP_X) * 1.3)
        out = np.maximum(out, np.clip(1 - d / 3.6, 0, 1) ** 1.5)
    return out * strength


# =========================================================================== n1: platform 5
def n1_bg():
    R = C.ramps(N=NIGHT, L=LAMPR, W=SNOWR, I=IRONR, R=V['red'], G=['#0C111C', '#1E302E', '#3D5E57', '#739585'])
    p = C.Paint(VW, VH, R, 'n1_bg')
    yy, xx = p.yy, p.xx
    allm = np.ones((VH, VW), bool)
    vpx, vpy = PROJ['vpx'], PROJ['vpy']
    # ---- the night beyond: low cloud lit faintly by the city (warm-grey near the horizon), the yard dark
    sky_t = 1.6 + np.clip(1 - np.abs(yy - vpy + 10) / 90, 0, 1) * 1.6 + (pg.value_noise(VW, VH, 50, 701, 3) - 0.5) * 0.6
    p.put(allm, 'N', sky_t)
    # distant city glow on the cloud base behind the VP
    glow = np.clip(1 - np.hypot((xx - 300) / 260, (yy - 150) / 40), 0, 1) ** 1.5
    p.add(allm, glow * 1.4)
    # far skyline (domes, a spire, the palais dome with a red aircraft light)
    sk = np.zeros((VH, VW), bool)
    rng = np.random.default_rng(702)
    x = 240.0
    while x < VW:
        w_ = rng.uniform(10, 26)
        sk |= p.box(x, vpy - rng.uniform(3, 10), x + w_, vpy + 2)
        x += w_
    sk |= p.ell(402, vpy - 10, 9, 8) & (yy < vpy - 8) | p.box(394, vpy - 10, 411, vpy)
    sk |= p.box(401, vpy - 26, 403, vpy - 17)
    sk |= p.poly([(470, vpy), (474, vpy - 30), (478, vpy)])
    p.put(sk, 'N', 2.0)
    for _ in range(26):
        wx, wy = rng.uniform(250, 636), rng.uniform(vpy - 8, vpy)
        if sk[int(wy), int(wx)]:
            p.px(wx, wy, 'L', float(rng.choice([1.6, 2.4, 3.0])))
    p.px(402, vpy - 27, 'R', 3.0)
    # ---- ground plane (rail level, y = -1): track bed beyond the platform, snow, sleepers, rails
    zg, xg = plane_y(yy, xx, -1.0)
    ground = (yy > vpy + 0.5) & np.isfinite(zg)
    gtone = 2.6 - np.clip((np.nan_to_num(zg) - 8) / 60, 0, 1) * 1.2 + (pg.value_noise(VW, VH, 14, 703, 2) - 0.5) * 0.8
    p.put(ground, 'W', gtone)
    # lamp light spilled onto the track bed (near the platform)
    pool_g = lamp_pool(zg, xg, 1.0) * ground
    # sleepers every 0.65 m between the outer rails
    zi = np.clip(np.nan_to_num(zg, nan=0.0, posinf=0.0, neginf=0.0), 0.0, 1e4)
    sl = ground & (np.nan_to_num(xg) > 1.8) & (np.nan_to_num(xg) < 4.0) & (np.mod(zi, 0.65) < 0.22) & (zi < 70)
    p.put(sl, 'N', 2.6 + pool_g * 3.0)
    ballast = ground & (np.nan_to_num(xg) > 1.7) & (np.nan_to_num(xg) < 4.1)
    p.add(ballast & ~sl, -0.6)
    # the rails: four-rail dual gauge, the inner rail of the standard gauge
    for rx in (2.18, 3.29, 3.62):
        a_ = proj(rx, -1.0, 2.5)
        b_ = proj(rx, -1.0, 400.0)
        rm = p.line([a_, b_], 0.55) & ground
        p.put(rm, 'I', 3.4)
        p.put(rm & ~C.shift(rm, 0, -1), 'W', 5.6)
    # far tracks and platform 6 to the right (in the same perspective), its canopy dark
    for rx in (6.4, 7.9):
        a_ = proj(rx, -1.0, 3.0)
        b_ = proj(rx, -1.0, 400.0)
        rm = p.line([a_, b_], 0.5) & ground
        p.put(rm, 'W', 4.6)
    pl6 = np.isfinite(zg) & (np.nan_to_num(xg) > 9.2) & ground
    p.put(pl6, 'W', 3.2 - np.clip((np.nan_to_num(zg) - 8) / 60, 0, 1) * 1.4)
    edge6 = p.line([proj(9.2, -1.0, 6.0), proj(9.2, -1.0, 400.0)], 0.5)
    p.put(edge6 & ground, 'W', 6.0)
    # platform 6 canopy underside + its fascia (dark band in perspective), a few lamps
    za, xa = plane_y(yy, xx, 4.2)
    can6 = (yy < vpy - 0.5) & np.isfinite(za) & (np.nan_to_num(xa) > 8.6)
    p.put(can6, 'N', 1.2 + np.clip(1 - (np.nan_to_num(za) - 10) / 50, 0, 1) * 0.6)
    for lz in (9.0, 21.0, 33.0, 45.0):
        lx_, ly_ = proj(10.4, 3.6, lz)
        r_ = max(1.0, 18.0 / lz)
        p.put(p.ell(lx_, ly_, r_ + 0.6, r_), 'L', 4.4)
    # ---- platform 5 (left): surface y = 0, the white edge, lamp pools, snow trodden into slush
    zp, xp = plane_y(yy, xx, 0.0)
    plat = (yy > vpy + 0.5) & np.isfinite(zp) & (np.nan_to_num(xp, nan=99) < EDGE_X)
    pool = lamp_pool(zp, xp, 1.0)
    pt = 2.0 + pool * 2.2 - np.clip((np.nan_to_num(zp) - 6) / 70, 0, 1) * 1.0
    pt += (pg.value_noise(VW, VH, 8, 704, 2) - 0.5) * 0.7
    p.put(plat, 'W', pt)
    # the lamps mirrored in the wet, trodden snow: short warm streaks running toward the camera
    for lz in LAMPS_Z:
        qx, qy = proj(LAMP_X - 0.15, 0.0, lz)
        ln = max(2.0, 90.0 / lz)
        streak = plat & (np.abs(xx - qx) < max(0.6, 6.0 / lz)) & (yy > qy - 1) & (yy < qy + ln) &             (((yy.astype(int) + int(lz)) % 3) != 0)
        p.put(streak, 'L', 2.6)
    slabs = plat & (np.mod(np.nan_to_num(zp), 2.0) < 0.07)
    p.add(slabs, -0.8)
    edge = plat & (np.nan_to_num(xp) > EDGE_X - 0.28)
    p.put(edge, 'W', 6.2 + pool * 1.6)
    p.put(plat & (np.nan_to_num(xp) > EDGE_X - 0.34) & (np.nan_to_num(xp) <= EDGE_X - 0.28), 'N', 3.0)
    # ---- canopy over platform 5: underside boards, purlins, the fascia over the track edge
    zc, xc = plane_y(yy, xx, CANOPY_Y)
    can = (yy < vpy - 0.5) & np.isfinite(zc) & (np.nan_to_num(xc, nan=99) < 1.8)
    ct = 1.4 + lamp_pool(zc, xc, 1.0) * 2.4 + np.clip(1 - np.nan_to_num(zc) / 30, 0, 1) * 0.6
    p.put(can, 'N', ct)
    purl = can & (np.mod(np.nan_to_num(zc), 3.0) < 0.22)
    p.add(purl, 1.4)
    boards = can & (np.mod(np.nan_to_num(xc) + 20.0, 0.5) < 0.06)
    p.add(boards, -0.5)
    # fascia board at x = 1.8 hanging 0.45 m below the roof edge (vertical strip in perspective)
    f_top = proj(1.8, CANOPY_Y, 3.0)
    f_bot_near = proj(1.8, CANOPY_Y - 0.45, 3.0)
    fas = p.poly([f_top, proj(1.8, CANOPY_Y, 300.0), proj(1.8, CANOPY_Y - 0.45, 300.0), f_bot_near])
    p.put(fas, 'I', 1.6)
    p.put(fas & ~C.shift(fas, 0, 1), 'W', 3.0)                                 # snow on top of the fascia
    # ---- columns down the middle of the platform (cast iron, fluted, lit from the lamps)
    for cz in (3.6, 10.6, 17.6, 24.6, 31.6, 38.6, 45.6):
        x0_, y0_ = proj(-2.4, CANOPY_Y, cz)
        x1_, y1_ = proj(-2.1, 0.0, cz)
        if x1_ < 0:
            continue
        col = p.box(x0_, y0_, x1_ + 1, y1_)
        li = lamp_pool(np.array(cz), np.array(-0.9), 1.0)
        p.put(col, 'I', 1.2 + float(li) * 3.0 + np.clip((xx - x0_) / max(1.0, x1_ - x0_), 0, 1) * 1.4)
        cap_w = max(1.0, (x1_ - x0_) * 0.4)
        p.put(p.box(x0_ - cap_w, y0_, x1_ + cap_w + 1, y0_ + max(1.0, 12.0 / cz)), 'I', 2.6)
    # ---- a goods train standing on the next track: dark box cars receding, snow on their roofs
    for c in range(8):
        z0 = 17.0 + c * 13.6
        z1 = z0 + 12.8
        xl, xr = 5.7, 8.6
        side = p.poly([proj(xl, -0.6, z0), proj(xl, 3.0, z0), proj(xl, 3.0, z1), proj(xl, -0.6, z1)])
        p.put(side, 'N', 2.2 + (c % 2) * 0.3)
        for k in range(1, 6):                                                      # vertical boards / ribs
            zr = z0 + k * (z1 - z0) / 6
            p.put(p.line([proj(xl, -0.4, zr), proj(xl, 2.8, zr)], 0.4) & side, 'N', 2.4)
        p.put(p.line([proj(xl, 3.0, z0), proj(xl, 3.0, z1)], 0.5), 'W', 4.6)       # snow on the roof edge
        roof = p.poly([proj(xl, 3.0, z0), proj(xr, 3.1, z0), proj(xr, 3.1, z1), proj(xl, 3.0, z1)])
        p.put(roof, 'W', 3.0)
        if c == 0:
            face = p.poly([proj(xl, -0.6, z0), proj(xl, 3.0, z0), proj(xr, 3.1, z0), proj(xr, -0.6, z0)])
            p.put(face, 'N', 1.0)
            p.put(face & ~C.shift(face, 0, -1), 'W', 4.0)
    # ---- the far end: a signal at red where the track vanishes, tiny yard lamps
    sx, sy = proj(2.6, 3.2, 160.0)
    p.put(p.box(sx, sy, sx + 1, proj(2.6, -1.0, 160.0)[1]), 'I', 2.0)
    p.px(sx, sy, 'R', 3.0)
    for (lx, ly_, lz) in ((-4.0, 5.0, 120.0), (6.0, 6.0, 140.0), (12.0, 7.0, 90.0), (16.0, 6.0, 70.0)):
        qx, qy = proj(lx, ly_, lz)
        p.px(qx, qy, 'L', 3.4)
    p.resolve(band=2.6)
    LAYOUT['edge_x'] = EDGE_X
    return p.L


def n1_mid():
    """In front of the train: the hanging canopy lamps (shade + bulb), the platform-5 sign, the clock."""
    R = C.ramps(N=NIGHT, L=LAMPR, W=SNOWR, I=IRONR, D=['#8593A3', '#A1AAB7', '#C2C9D2', '#DEE2E7'])
    p = C.Paint(VW, VH, R, 'n1_mid')
    for lz in LAMPS_Z:
        top = proj(LAMP_X, CANOPY_Y, lz)
        bot = proj(LAMP_X, LAMP_Y + 0.25, lz)
        if top[1] < -10 and bot[1] < 40:
            continue
        p.put(p.box(top[0], top[1], top[0] + 1, bot[1]), 'I', 2.4)
        sw = max(2.0, 260.0 / lz / 2)
        sh = max(1.0, 110.0 / lz)
        shade = p.poly([(bot[0] - sw * 0.4, bot[1]), (bot[0] + sw * 0.4, bot[1]), (bot[0] + sw, bot[1] + sh),
                        (bot[0] - sw, bot[1] + sh)])
        p.put(shade, 'I', 3.0)
        p.put(shade & ~C.shift(shade, 0, -1), 'W', 5.0)
        p.put(p.ell(bot[0], bot[1] + sh + max(0.8, 40.0 / lz), max(1.0, sw * 0.45), max(0.8, 40.0 / lz)), 'L', 6.0,
              emis=True)
    # the platform sign "5" hanging under the canopy (enamel, slate blue, white numeral)
    sz = 9.0
    c0 = proj(0.1, 3.95, sz)
    c1 = proj(0.9, 3.35, sz)
    sign = p.box(c0[0], c0[1], c1[0], c1[1])
    p.put(sign, 'N', 6.0)
    p.put(sign & ~C.kit.erode(sign, 1), 'W', 6.6)
    p.put(K.text_at('5', VW, VH, int((c0[0] + c1[0]) / 2), int(c0[1] + 3), font='l', center=True) & sign, 'W', 8.2)
    for hx_ in (c0[0] + 3, c1[0] - 4):
        p.put(p.box(hx_, proj(0.5, CANOPY_Y, sz)[1], hx_ + 1, c0[1]), 'I', 2.6)
    # a small platform clock (23.40) further down
    ck = proj(0.4, 3.55, 21.0)
    rr_ = 6
    yy, xx = p.yy, p.xx
    dial = K.disc(yy, xx, ck[0], ck[1], rr_)
    p.put(K.disc(yy, xx, ck[0], ck[1], rr_ + 1.4), 'I', 2.0)
    p.put(dial, 'D', 1.6)
    for (deg, ln) in ((350.0, 3.2), (240.0, 5.0)):
        u = (math.sin(math.radians(deg)), -math.cos(math.radians(deg)))
        p.put(p.line([(ck[0], ck[1]), (ck[0] + u[0] * ln, ck[1] + u[1] * ln)], 0.45), 'N', 1.0)
    p.put(p.box(ck[0], proj(0.4, CANOPY_Y, 21.0)[1], ck[0] + 1, ck[1] - rr_), 'I', 2.6)
    p.resolve(band=2.0)
    return p.L


def n1_fg():
    """Near foreground: a bench at the platform edge with snow on it, a litter bin, the near column base."""
    R = C.ramps(N=NIGHT, L=LAMPR, W=SNOWR, I=IRONR, D=['#22150F', '#331F16', '#4A2D1F', '#63402C'])
    p = C.Paint(VW, VH, R, 'n1_fg')
    yy, xx = p.yy, p.xx
    # bench (left foreground, side-on in perspective: seat from z 2.6 to 4.2)
    for (z0, z1) in ((2.8, 4.6),):
        seat = p.poly([proj(-0.9, 0.46, z0), proj(-0.9, 0.46, z1), proj(-0.45, 0.46, z1), proj(-0.45, 0.46, z0)])
        p.put(seat, 'D', 1.6)
        p.put(seat & ~C.shift(seat, 0, -1), 'W', 5.4)
        back = p.poly([proj(-0.95, 0.5, z0), proj(-0.95, 0.5, z1), proj(-0.95, 0.95, z1), proj(-0.95, 0.95, z0)])
        p.put(back, 'D', 1.2)
        for k in range(3):
            yb = 0.58 + k * 0.13
            sl = p.line([proj(-0.95, yb, z0), proj(-0.95, yb, z1)], 0.7)
            p.put(sl & back, 'D', 2.4)
        for lz in (z0 + 0.15, z1 - 0.15):
            leg = p.poly([proj(-0.9, 0.0, lz), proj(-0.9, 0.46, lz), proj(-0.86, 0.46, lz), proj(-0.86, 0.0, lz)])
            p.put(leg, 'I', 1.2)
    # litter bin on a post
    bx0, by0 = proj(-0.3, 0.9, 6.5)
    bx1, by1 = proj(-0.05, 0.45, 6.5)
    binm = p.box(bx0, by0, bx1, by1)
    p.put(binm, 'I', 2.0)
    p.put(binm & ~C.shift(binm, 0, -1), 'W', 5.0)
    p.put(p.box((bx0 + bx1) / 2, by1, (bx0 + bx1) / 2 + 1, proj(-0.2, 0.0, 6.5)[1]), 'I', 1.6)
    p.resolve(band=2.0)
    return p.L


def board():
    """The split-flap indicator hanging under the canopy at the left: 4 frames
    (0 = the special train, 1-2 = flaps turning, 3 = the row cleared)."""
    bw, bh = 196, 46
    x0, y0 = 24, 64
    R = C.ramps(N=NIGHT, I=IRONR, P=['#1A2431', '#2A3646', '#4A4236', '#80745E', '#BBAD8F', '#D6CBAE', '#F2F3F5'],
                L=LAMPR)
    sheet = np.zeros((bh * 4, bw, 4), np.uint8)
    rows = [('23.40', 'SONDERZUG', 'KORDON-17', '5')]
    cols_x = [6, 34, 92, 178]
    for fr in range(4):
        p = C.Paint(bw, bh, R, 'board')
        box = p.box(0, 0, bw, bh)
        p.put(box, 'I', 1.4)
        p.put(box & ~C.kit.erode(box, 1), 'I', 3.4)
        p.put(p.box(0, 0, bw, 1), 'I', 5.0)
        hdr = K.text_at('ABFAHRT · ОТПРАВЛЕНИЕ · DÉPART', bw, bh, bw // 2, 4, font='s', center=True)
        p.put(hdr, 'P', 4.2)
        p.put(p.box(4, 12, bw - 4, 13), 'I', 3.0)
        # the flap cells of the one live row
        ry = 20
        cells = np.zeros((bh, bw), bool)
        for k in range(0, (bw - 12) // 6):
            cells |= p.box(6 + k * 6, ry - 2, 6 + k * 6 + 5, ry + 9)
        p.put(cells, 'N', 4.0)
        p.put(cells & (p.yy == ry + 3), 'N', 1.0)                             # the split of every flap
        rng = np.random.default_rng(711 + fr)
        if fr == 0:
            for (txt, cx) in zip(rows[0], cols_x):
                m = K.text_at(txt, bw, bh, cx, ry, font='s')
                p.put(m, 'P', 5.6)
        elif fr in (1, 2):
            for (txt, cx) in zip(rows[0], cols_x):
                m = K.text_at(txt, bw, bh, cx, ry, font='s')
                keep = (rng.random((bh, bw)) > (0.45 if fr == 1 else 0.75)) & ((p.yy < ry + 3) if fr == 1 else (p.yy >= ry + 2))
                p.put(m & keep, 'P', 5.0)
                p.put(m & ~keep & (p.yy >= ry + 3), 'P', 3.4)
        # second row: an older, already cleared slot (blank flaps), a third with the next morning train
        for k in range(0, (bw - 12) // 6):
            p.put(p.box(6 + k * 6, 33, 6 + k * 6 + 5, 44), 'N', 3.4)
        m2 = K.text_at('06:12', bw, bh, 6, 35, font='s') | K.text_at('BERLIN', bw, bh, 34, 35, font='s') | \
            K.text_at('4', bw, bh, 178, 35, font='s')
        p.put(m2, 'P', 4.6)
        p.resolve(band=2.0)
        sheet[fr * bh:(fr + 1) * bh] = p.L.c
    LAYOUT['board'] = [x0, y0]
    return sheet


def steam():
    n, fw, fh = 4, 120, 70
    LAYOUT['steam_frames'] = n
    return K.puff_sheet(n, fw, fh, ['#2A3646', '#3A4859', '#4F5E70', '#687789', '#8593A3'], 721, grow=(0.36, 0.5),
                        thin=0.45, light=(-0.5, -0.5))


# =========================================================================== n2: the station square
def n2_bg():
    R = C.ramps(N=NIGHT, L=LAMPR, W=SNOWR, I=IRONR, R=V['red'],
                F=['#070A12', '#0C111C', '#121A26', '#1A2431', '#2A3646', '#3A4859', '#4A4236', '#645A49', '#80745E'],
                G=['#070A12', '#0C111C', '#15171C', '#1E2836', '#2A3646', '#3A4859', '#4F5E70'],
                P=['#0C111C', '#1E302E', '#2B4541', '#3D5E57', '#56796E'])
    p = C.Paint(VW, VH, R, 'n2_bg')
    yy, xx = p.yy, p.xx
    allm = np.ones((VH, VW), bool)
    # night sky heavy with snow; the old town's glow low in the street between the hotels
    st = 1.4 + np.clip(1 - np.abs(xx - 320) / 260, 0, 1) * np.clip((yy - 60) / 170, 0, 1) * 2.4
    st += (pg.value_noise(VW, VH, 60, 731, 3) - 0.5) * 0.7
    p.put(allm, 'N', st)
    # ---- the street into the old town: gables, the dome of the palais, a few lit windows
    town = np.zeros((VH, VW), bool)
    rng = np.random.default_rng(732)
    x = 196.0
    while x < 444:
        w_ = rng.uniform(12, 22)
        h_ = rng.uniform(28, 52)
        top = 236 - h_
        town |= p.box(x, top, x + w_, 244)
        town |= p.poly([(x, top), (x + w_ / 2, top - rng.uniform(6, 11)), (x + w_, top)])
        x += w_
    dome = p.ell(322, 168, 17, 16) & (yy < 170)
    town |= dome | p.box(305, 168, 340, 244) | p.box(321, 142, 323, 152)
    p.put(town, 'N', 2.6)
    p.put(dome, 'P', 1.4)
    for _ in range(46):
        wx, wy = int(rng.uniform(200, 440)), int(rng.uniform(190, 238))
        if town[wy, wx] and town[wy + 1, wx + 1] and not dome[wy, wx]:
            p.put(p.box(wx, wy, wx + 2, wy + 2), 'L', float(rng.choice([1.6, 2.4, 3.0])), emis=True)
    p.put(town & ~C.shift(town, 0, -1), 'W', 3.2)
    p.px(322, 141, 'R', 3.0)                                                   # aircraft light on the lantern

    def facade(x0, x1, top, name, floors, tone, seed, kind):
        """A hotel front at night: dark masonry, snow on every ledge, the ground floor lit from the street."""
        fm = p.box(x0, top, x1, 254)
        lit_low = np.clip((yy - 180) / 74, 0, 1) ** 1.6                       # street light climbing the wall
        p.put(fm, 'F', tone + lit_low * 2.4 + (pg.value_noise(VW, VH, 9, seed, 2) - 0.5) * 0.5)
        rows = []
        fy = top + 14
        for k in range(floors):
            rows.append(fy)
            fy += 34 if k == 0 else 30
        ground = rows[-1] + 30
        # string courses and cornices with snow on them
        for cy in [top + 6] + [r - 6 for r in rows[1:]] + [ground - 4]:
            p.put(p.box(x0 - 2, cy, x1 + 2, cy + 3), 'F', tone + 1.2 + float(lit_low[cy, 0]) * 2.0)
            p.put(p.box(x0 - 2, cy - 1, x1 + 2, cy), 'W', 5.6)
        # windows (dark panes, white frames catching the snow light, sills with snow)
        wins = []
        step = 22 if kind == 'old' else 20
        for r_i, wy in enumerate(rows):
            for wx in range(x0 + 12, x1 - 14, step):
                ww, wh = (11, 18) if kind == 'old' else (13, 14)
                wm = p.box(wx, wy, wx + ww, wy + wh)
                p.put(wm, 'G', 1.2 + float(lit_low[wy, 0]) * 1.6)
                p.put(wm & ~C.kit.erode(wm, 1), 'F', tone + 2.2 + float(lit_low[wy, 0]) * 1.6)
                p.put(p.box(wx + ww // 2, wy, wx + ww // 2 + 1, wy + wh), 'F', tone + 1.6)
                p.put(p.box(wx - 1, wy + wh, wx + ww + 1, wy + wh + 1), 'W', 6.0)
                if kind == 'old':
                    p.put(p.box(wx - 1, wy - 3, wx + ww + 1, wy - 1), 'F', tone + 1.6)     # window hood
                    p.put(p.box(wx - 1, wy - 4, wx + ww + 1, wy - 3), 'W', 5.0)
                wins.append((wx, wy))
        # balconies with iron railings on the first floor (old hotel)
        if kind == 'old':
            for wx in range(x0 + 12, x1 - 14, step * 2):
                by = rows[1] + 18
                p.put(p.box(wx - 4, by, wx + 15, by + 2), 'F', tone + 1.4)
                p.put(p.box(wx - 4, by - 1, wx + 15, by), 'W', 6.0)
                for rx in range(wx - 4, wx + 16, 2):
                    p.put(p.box(rx, by - 6, rx + 1, by), 'I', 1.4)
                p.put(p.box(wx - 4, by - 7, wx + 15, by - 6), 'I', 2.0)
        # ground floor: arched shop windows / the lobby (lit), the entrance with a canopy and two lamps
        ex = (x0 + x1) // 2
        for k, gx in enumerate(range(x0 + 10, x1 - 16, 26)):
            arch = p.box(gx, ground + 8, gx + 16, 254) | (p.ell(gx + 8, ground + 8, 8, 6) & (yy < ground + 8))
            lobby = abs(gx + 8 - ex) < 30
            p.put(arch, 'L' if lobby else 'G', 2.2 if lobby else 1.0, emis=lobby)
            p.put(arch & ~C.kit.erode(arch, 1), 'F', tone + 3.0)
        p.put(p.box(ex - 22, ground + 4, ex + 22, ground + 8), 'I', 2.6)
        p.put(p.box(ex - 22, ground + 3, ex + 22, ground + 4), 'W', 6.6)
        for lx in (ex - 25, ex + 24):
            p.put(p.box(lx, ground + 10, lx + 2, ground + 14), 'L', 5.4, emis=True)
        # roof: mansard with dormers (old) or a flat roof with a parapet (new), snow on top
        if kind == 'old':
            roof = p.poly([(x0 - 4, top), (x0 + 8, top - 20), (x1 - 8, top - 20), (x1 + 4, top)])
            p.put(roof, 'N', 1.8)
            p.put(roof & ~C.shift(roof, 0, -2), 'W', 6.0)
            for dx in range(x0 + 16, x1 - 16, 34):
                dm = p.box(dx, top - 15, dx + 10, top - 3) | p.poly([(dx - 1, top - 15), (dx + 5, top - 21), (dx + 11, top - 15)])
                p.put(dm, 'N', 2.6)
                p.put(p.box(dx + 3, top - 12, dx + 7, top - 5), 'G', 0.8)
                p.put(dm & ~C.shift(dm, 0, -1), 'W', 6.2)
            for cx in (x0 + 30, x1 - 40):
                p.put(p.box(cx, top - 30, cx + 5, top - 18), 'N', 2.2)
                p.put(p.box(cx, top - 31, cx + 5, top - 30), 'W', 5.6)
        else:
            p.put(p.box(x0 - 2, top - 6, x1 + 2, top), 'F', tone + 0.8)
            p.put(p.box(x0 - 2, top - 7, x1 + 2, top - 6), 'W', 6.2)
        nm = K.text_at(name, VW, VH, ex, top - (16 if kind == 'old' else 4) - 8, font='s', center=True)
        p.put(nm, 'L', 4.4, emis=True)
        return wins, rows, ground
    wl, rows_l, gl = facade(0, 214, 104, 'HOTEL EUROPA', 3, 1.0, 733, 'old')
    wr, rows_r, gr = facade(428, 640, 92, 'HOTEL NORD', 4, 0.8, 734, 'new')
    # ---- the square: snow over the cobbles, the tram rails curving away, tyre tracks, footprints
    sq = p.box(0, 254, VW, VH)
    p.put(sq, 'W', 3.2 + (pg.value_noise(VW, VH, 20, 735, 2) - 0.5) * 0.8 - np.clip((yy - 254) / 60, 0, 1) * 0.5)
    for a_ in (0.0, 6.0):
        pts = [(330 + a_, 254), (318 + a_, 270), (276 + a_, 292), (180 + a_, 314), (80 + a_, 330)]
        p.put(p.line(pts, 0.45), 'I', 2.6)
    tyre = p.line([(250, 254), (262, 280), (300, 316)], 0.6) | p.line([(262, 254), (276, 280), (318, 316)], 0.6)
    p.put(tyre, 'W', 2.0)
    for k in range(14):
        fx = 560 - k * 13 + (k % 2) * 3
        fy = 264 + k * 4
        p.put(p.box(fx, fy, fx + 2, fy + 1), 'W', 1.8)
    # ---- limes along the street and the parked car under them
    for (tx, th) in ((236, 70), (404, 64), (276, 54), (366, 50)):
        p.put(p.box(tx, 254 - th, tx + 2, 256), 'N', 0.8)
        for k in range(7):
            ang = -math.pi / 2 + (k - 3) * 0.42
            ln = th * 0.35 + (k % 3) * 4
            sx0, sy0 = tx + 1, 254 - th * 0.55 - (k % 2) * 6
            br = p.line([(sx0, sy0), (sx0 + math.cos(ang) * ln, sy0 + math.sin(ang) * ln)], 0.45)
            p.put(br, 'N', 1.2)
            p.put(br & ~C.shift(br, 0, -1), 'W', 4.4)
    car = p.rr(250, 238, 306, 254, 4) | p.rr(262, 228, 294, 242, 5)
    p.put(car, 'N', 1.2)
    p.put(car & ~C.shift(car, 0, -1), 'W', 6.0)
    p.put(p.rr(266, 231, 290, 239, 3), 'N', 0.4)
    for wx in (258, 298):
        p.put(p.ell(wx, 254, 4, 3) & (yy < 255), 'N', 0.2)
    LAYOUT['ember'] = [281, 235]
    # the street lamp in the middle of the square
    lpx = 352
    p.put(p.box(lpx, 198, lpx + 2, 264), 'I', 1.6)
    p.put(p.box(lpx - 3, 260, lpx + 5, 266), 'I', 1.4)
    for s_ in (-1, 1):
        arm = p.line([(lpx + 1, 202), (lpx + 1 + s_ * 9, 198), (lpx + 1 + s_ * 13, 201)], 0.5)
        p.put(arm, 'I', 1.6)
        p.put(p.box(lpx + 1 + s_ * 13 - 2, 201, lpx + 1 + s_ * 13 + 3, 207), 'L', 5.4, emis=True)
    LAYOUT['lamp'] = [lpx + 1, 204]
    pool = np.clip(1 - np.hypot((xx - lpx) / 70, (yy - 266) / 14), 0, 1) * sq
    p.put(pool > 0.2, 'W', 3.6 + pool * 3.2)
    p.put(pool > 0.62, 'L', 3.0 + pool * 1.4)
    p.L.amb_field(-np.clip(np.hypot((xx - 320) / 420, (yy - 200) / 260) - 0.45, 0, 1) * 1.4)
    p.resolve(band=2.6)
    LAYOUT['windows_left'] = wl
    LAYOUT['windows_right'] = wr
    # the lit windows: second floor of Europa (Konrad), third floor of Nord (Alexei)
    kx, ky = wl[(len(wl) // 3) * 1 + 6]
    ax, ay = wr[(len(wr) // 4) * 2 + 4]
    LAYOUT['win_konrad'] = [int(kx) - 1, int(ky) - 1]
    LAYOUT['win_alexei'] = [int(ax) - 1, int(ay) - 1]
    LAYOUT['win_size'] = {'konrad': [13, 20], 'alexei': [15, 16]}
    return p.L


def _window_frames(who):
    """3 frames of one lit hotel window: curtains half open, the lit room; 0 = empty, 1 = the man steps to the
    glass, 2 = he turns his head toward the station (the whistle)."""
    ww, wh = (13, 20) if who == 'konrad' else (15, 16)
    R = C.ramps(L=LAMPR, N=NIGHT, C=['#4A2D1F', '#6E3F22', '#A8643A', '#D08F55'],
                F=['#121A26', '#1A2431', '#2A3646', '#3A4859', '#4A4236', '#645A49', '#80745E'])
    sheet = np.zeros((wh, ww * 3, 4), np.uint8)
    for fr in range(3):
        p = C.Paint(ww, wh, R, 'win')
        yy, xx = p.yy, p.xx
        room = p.box(1, 1, ww - 1, wh - 1)
        p.put(p.box(0, 0, ww, wh), 'F', 4.0)                                  # the frame
        p.put(room, 'L', 4.4 - np.clip((yy - 2) / wh, 0, 1) * 1.6 - np.abs(xx - ww / 2) * 0.06)
        p.put(p.box(ww // 2 - 2, 2, ww // 2 + 2, 4), 'L', 6.0)               # the ceiling lamp of the room
        p.put(p.box(1, 1, 3, wh - 1), 'C', 2.2)                               # curtains
        p.put(p.box(ww - 3, 1, ww - 1, wh - 1), 'C', 2.0)
        p.put(p.box(ww // 2, 0, ww // 2 + 1, wh), 'F', 3.4)                    # mullion
        cx = ww / 2.0
        if fr >= 1:
            if who == 'konrad':                                              # slim, upright
                hx = cx + (0.0 if fr == 1 else 0.7)
                head = p.ell(hx, 7.0, 1.8, 2.2)
                body = p.poly([(cx - 3.0, wh), (cx - 2.5, 11), (cx - 1.4, 9.4), (cx + 1.4, 9.4), (cx + 2.5, 11),
                               (cx + 3.0, wh)])
            else:                                                            # broader, a glass in his hand
                hx = cx + (0.0 if fr == 1 else 0.8)
                head = p.ell(hx, 6.4, 2.0, 2.3)
                body = p.poly([(cx - 4.0, wh), (cx - 3.5, 10.8), (cx - 2.0, 9.0), (cx + 2.0, 9.0), (cx + 3.5, 10.8),
                               (cx + 4.0, wh)])
            p.put(head | body, 'N', 0.6)
            if who == 'alexei':
                p.put(p.box(int(cx + 3), 11, int(cx + 5), 13), 'L', 5.0)    # the tea glass catches the lamp
        p.put(p.box(0, wh - 1, ww, wh), 'F', 5.0)
        p.resolve(band=2.0)
        sheet[:, fr * ww:(fr + 1) * ww] = p.L.c
    return sheet


def n2_win_konrad():
    return _window_frames('konrad')


def n2_win_alexei():
    return _window_frames('alexei')


def n2_lamp_glow():
    yy, xx = _grid()
    a = np.zeros((VH, VW, 3), np.float32)
    lx, ly = LAYOUT.get('lamp', [353, 202])
    for s_ in (-1, 1):
        cx = lx + s_ * 13
        d = np.hypot((xx - cx) / 26, (yy - ly) / 20)
        g = np.clip(1 - d, 0, 1) ** 1.6
        for c, v in enumerate((70, 46, 22)):
            a[..., c] += g * v
    # the two lit hotel windows breathe a little light into the snow-filled air in front of them
    for (wx, wy) in (LAYOUT.get('win_konrad', [119, 157]), LAYOUT.get('win_alexei', [547, 147])):
        d = np.hypot((xx - wx - 6) / 22, (yy - wy - 10) / 22)
        g = np.clip(1 - d, 0, 1) ** 2.0
        for c, v in enumerate((30, 20, 9)):
            a[..., c] += g * v
    return K.soft_quant(a, 8.0)
