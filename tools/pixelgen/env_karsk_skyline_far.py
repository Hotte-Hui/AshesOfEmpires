"""env_karsk_skyline_far -- the two distant planes of the Karsk skyline.

far_industry (parallax 0.25, 2.64 px/m, base y 217, bypass railway rail at y 216 = KarskTrain rail):
    thermal power station (TETs) with two red/white striped chimneys at the far left, saw-tooth brick halls, a
    telescopic gasholder, rows of five-storey panel blocks (new microdistrict), a school, warehouses, a factory
    chimney east of the cooling towers; all low where the sun / train / office views need it.
far_city (parallax 0.12, 1.27 px/m, horizon y 207): the town on the horizon -- panel-block districts with
    tiny cranes, the old quarter with a small church, a guyed radio mast with red obstruction lamps, the power
    station with its two hyperboloid cooling towers flanking the sun (exp_cooling_towers), boiler house and two
    striped chimneys, a switchyard with pylon lines, and a TV mast near the sun at the east end.
Silhouettes only (detail falls off with distance), heavy haze toward the horizon.
"""
from __future__ import annotations

import math

import numpy as np

import env_karsk_skyline_lib as SL
from env_karsk_skyline_lib import (NI, TE, SA, SK, ST, RU, CO, SN, WO, RED, PLANES, put, rect, hline, vline, line,
                                   Haze, vfog, dith, cyl_normals, N_UP, N_RIGHT, N_LEFT)
import env_karsk_skyline_kit as K
from env_karsk_skyline_arch import onion_dome


# =========================================================================== far element painters
def slab(L, x, base, w, floors, fh, C, S, seed=0, win=True, wstep=3, lit=0.0, antennas=0, ant_col=None,
         stair_every=0, built=None):
    """Distant five-storey panel block: body, rim, snowy roof line, window dots in rows (one per floor)."""
    rng = np.random.default_rng(seed)
    nfl = floors if built is None else built
    h = nfl * fh + 1
    top = base - h
    K.facade(L, x, top, w, h, C)
    if win:
        for f in range(nfl):
            wy = base - 1 - (f + 1) * fh + max(1, fh // 2)
            for wx in range(x + 2, x + w - 2, wstep):
                if stair_every and ((wx - x - 2) // wstep) % stair_every == stair_every // 2:
                    continue
                r = rng.random()
                if r < lit:
                    put(L, wx, wy, S['warm'], em=S['warm'])
                elif r < 0.9:
                    put(L, wx, wy, C[0] if fh >= 5 else S['glass'])
                    if fh >= 6:
                        put(L, wx + 1, wy, C[0])
                        if fh >= 7:
                            put(L, wx, wy + 1, C[0])
                            put(L, wx + 1, wy + 1, C[0])
    hline(L, x, top, w, C[3], N_UP)
    if built is None:
        K.snow_line(L, x, top - 1, w, S, 1, seed, ragged=0.15)
    for a in range(antennas):
        ax = x + 2 + int(rng.uniform(0, 1) * (w - 4))
        ah = int(rng.integers(2, 4))
        vline(L, ax, top - 1 - ah, ah, ant_col if ant_col is not None else C[0])
        if ah >= 3:
            hline(L, ax - 1, top - ah, 3, ant_col if ant_col is not None else C[0])
    return top


def sawtooth_hall(L, x, base, w, h, C, S, tooth=10, th=6, win=True, glaze=None, arched=False):
    """Brick factory hall with north-light (saw-tooth) roof: teeth rising to the right, glazed steep faces."""
    top = base - h
    K.facade(L, x, top, w, h, C)
    for xx in range(x, x + w):
        k = (xx - x) % tooth
        hh = int(round(th * (k + 1) / tooth))
        for yy in range(top - hh, top):
            put(L, xx, yy, C[2] if k < tooth - 2 else C[3], N_UP)
        put(L, xx, top - hh - 1, S['snow'][-1], N_UP)
        if k == tooth - 1:
            vline(L, xx, top - th, th, glaze if glaze is not None else C[0])
    if win:
        step = max(4, tooth // 2 + 1)
        for wx in range(x + 2, x + w - 3, step):
            if arched:
                rect(L, wx, top + 3, 2, max(2, h - 7), C[0])
                put(L, wx, top + 2, C[1])
            else:
                rect(L, wx, top + 3, 2, max(2, h // 3), C[0])
    return top - th - 1


def gasholder(L, cx, base, h, w, C, S):
    """Telescopic gasholder: cylindrical bell inside a guide frame (columns + rings)."""
    x0 = int(round(cx - w / 2))
    bell_h = int(h * 0.75)
    K.cylinder_v(L, x0 + 1, base - bell_h, w - 2, bell_h, C)
    for yy in range(base - bell_h + 4, base, 5):
        hline(L, x0 + 2, yy, w - 4, C[1])
    hline(L, x0 + 1, base - bell_h, w - 2, S['snow'][-1], N_UP)
    for k in range(5):                                   # guide columns
        gx = x0 + int(round(k * (w - 1) / 4))
        vline(L, gx, base - h, h, C[0] if k < 4 else C[4])
    for yy in (base - h, base - h + int(h * 0.33), base - h + int(h * 0.66)):
        hline(L, x0, yy, w, C[0])
    hline(L, x0, base - h - 1, w, S['snow'][-1], N_UP)


def cooling_tower(L, cx, base, h, wb, ww, wt, C, tw=0.74, seed=0):
    """Hyperboloid cooling tower: flared base on a dark ring of diagonal legs, throat at ~3/4 height, lip.
    Light from the back right: right edge rim, left side dark, faint vertical rain streaks."""
    rng = np.random.default_rng(seed)
    legs = max(2, int(round(h * 0.06)))
    for k in range(h):
        t = k / max(1, h - 1)                    # 0 top .. 1 base
        tt = 1 - t                               # 0 base .. 1 top
        if tt > tw:
            u = (tt - tw) / (1 - tw)
            half = ww / 2 + (wt / 2 - ww / 2) * u ** 1.6
        else:
            u = (tw - tt) / tw
            half = ww / 2 + (wb / 2 - ww / 2) * u ** 1.9
        yy = base - h + k
        xa, xb = int(round(cx - half)), int(round(cx + half))
        for xx in range(xa, xb + 1):
            v = (xx + 0.5 - cx) / max(1.0, half)
            if xx == xb:
                c = C[4]
            elif v > 0.62:
                c = C[3]
            elif v > 0.4:
                c = C[3] if dith(xx, yy, 0.5) else C[2]
            elif v < -0.6:
                c = C[0]
            elif v < -0.25:
                c = C[1]
            else:
                c = C[2]
            if k >= h - legs:                    # support legs: dark ring with lighter diagonals
                c = C[0] if (xx + (h - k)) % 3 else C[2]
            put(L, xx, yy, c)
    for _ in range(int(wb * 0.4)):              # rain streaks
        k0 = int(rng.integers(2, int(h * 0.5)))
        xx = int(round(cx + rng.uniform(-0.5, 0.45) * ww))
        for k in range(k0, min(h - legs, k0 + int(rng.integers(5, 14)))):
            yy = base - h + k
            cur = L.c[yy, xx]
            if (cur[:3] == C[2][:3]).all():
                put(L, xx, yy, C[1])
    hline(L, int(round(cx - wt / 2)), base - h, int(round(wt)) + 1, C[4], N_UP)
    hline(L, int(round(cx - wt / 2)) + 1, base - h + 1, int(round(wt)) - 1, C[0])
    cyl_normals(L, int(cx - wb / 2) - 1, base - h, int(wb) + 3, h)
    return (int(round(cx)), base - h)


def tree_clump(L, x, base, w, h, cols, seed=0, density=0.55):
    """Distant bare tree grove: dithered crown mass with a few trunk pixels (winter birches / poplars)."""
    rng = np.random.default_rng(seed)
    nz = SL.value_noise(w + 2, h + 2, 3, seed, octaves=2)
    for yy in range(h):
        for xx in range(w):
            u = (xx + 0.5) / w
            env = math.sin(math.pi * u) ** 0.7
            top = h * (1 - env * (0.6 + 0.4 * nz[0, xx]))
            if yy >= top and nz[yy, xx] > (1 - density) * (1 - (yy - top) / max(1, h - top) * 0.6):
                put(L, x + xx, base - h + yy, cols[0] if dith(x + xx, base - h + yy, 0.6) else cols[1])
    for k in range(max(1, w // 6)):
        tx = x + int(rng.integers(1, max(2, w - 1)))
        vline(L, tx, base - int(h * 0.5), int(h * 0.5), cols[0])


def low_roofs(L, x0, x1, base, hmin, hmax, C, S, seed=0, gable_p=0.5):
    """Continuous band of low town roofs (1-3 storeys) with snowy tops, varied widths, some pitched."""
    rng = np.random.default_rng(seed)
    x = x0
    while x < x1:
        w = int(rng.integers(5, 14))
        h = int(rng.integers(hmin, hmax + 1))
        K.facade(L, x, base - h, w, h, C, left=False)
        if rng.random() < gable_p:
            rise = max(1, w // 4)
            for k in range(rise):
                hline(L, x + k, base - h - 1 - k, w - 2 * k, C[1] if k else C[2])
            K.snow_line(L, x + 1, base - h - rise, max(1, w - 2 * rise), S, 1, x)
        else:
            K.snow_line(L, x, base - h - 1, w, S, 1, x)
        x += w + int(rng.integers(0, 3))


def water_tower(L, cx, base, h, Cb, Ct, S):
    """Factory water tower (Intze type): tapering brick shaft with small windows, wider tank house with a
    cornice and a low conical roof with a vent."""
    sh_h = int(h * 0.72)
    for k in range(sh_h):
        t = k / max(1, sh_h - 1)                  # 0 top .. 1 base
        w = 7 + 3 * t
        x0 = int(round(cx - w / 2))
        x1 = int(round(cx + w / 2))
        yy = base - sh_h + k
        for xx in range(x0, x1):
            u = (xx - x0 + 0.5) / max(1, x1 - x0)
            put(L, xx, yy, Cb[1] if u < 0.3 else (Cb[4] if xx == x1 - 1 else Cb[2]))
    for wy in range(base - sh_h + 6, base - 6, 9):
        put(L, int(cx) - 1, wy, Cb[0])
        put(L, int(cx) - 1, wy + 1, Cb[0])
    tk_top = base - h + 6
    K.facade(L, int(cx) - 8, tk_top, 16, base - sh_h - tk_top + 1, Ct)
    for xx in range(int(cx) - 7, int(cx) + 7, 3):
        vline(L, xx, tk_top + 2, base - sh_h - tk_top - 3, Ct[1])
    hline(L, int(cx) - 9, tk_top, 18, Ct[3], N_UP)
    hline(L, int(cx) - 9, base - sh_h, 18, Ct[0])
    for k in range(5):
        hline(L, int(cx) - 8 + k * 2, tk_top - 1 - k, 16 - k * 4, S['snow'][-1] if k < 3 else S['snow'][-2], N_UP)
    vline(L, int(cx), tk_top - 8, 3, Ct[0])
    return tk_top - 8


def little_church(L, x, base, C, Cd, S, seed=0):
    """Tiny far church: cube with a dome on a drum, bell tower with a slim spire (crosses gone)."""
    K.facade(L, x, base - 12, 14, 12, C)
    K.facade(L, x + 4, base - 17, 6, 5, C)
    onion_dome(L, x + 7, base - 17, 7, 6, Cd, seed=seed, spike=2)
    K.facade(L, x + 16, base - 20, 6, 20, C)
    K.facade(L, x + 17, base - 25, 4, 5, C)
    for k in range(9):
        put(L, x + 19, base - 26 - k, Cd[1] if k > 3 else Cd[2])
        if k < 3:
            put(L, x + 18, base - 26 - k, Cd[1])
            put(L, x + 20, base - 26 - k, Cd[3])
    K.snow_line(L, x, base - 13, 14, S, 1, seed)


def embankment(L, rail_y, base, cols, seed=0):
    """Bypass railway embankment across the plane: rail glints on the track line, snowy shoulder, slope."""
    rng = np.random.default_rng(seed)
    for x in range(L.w):
        put(L, x, rail_y - 1, cols['glint'] if (x * 7) % 11 < 3 else cols['rail'])
        put(L, x, rail_y, cols['sleeper'])
        put(L, x, rail_y + 1, cols['ballast'] if rng.random() < 0.6 else cols['rail'])
        put(L, x, rail_y + 2, cols['snow'] if rng.random() < 0.6 else cols['shoulder'])
        for yy in range(rail_y + 3, base + 14):
            t = (yy - rail_y - 3) / 12.0
            put(L, x, yy, cols['slope'] if dith(x, yy, 0.8 - t * 0.5) else cols['shoulder'])
    L.nrm[rail_y - 1:rail_y + 2] = (0.0, 0.8, 0.6)


# =========================================================================== FAR INDUSTRY (0.25)
def make_far_industry():
    S = K.STYLES['far_industry']
    g = PLANES['far_industry']
    B = g['base']
    L = SL.world_layer('far_industry')
    C = S['conc']
    Cb = S['brick']
    Cp = S['pale']
    meta = {'smoke': []}
    rng = np.random.default_rng(5)
    # ---- background row of blocks / roofs filling the whole horizon band (hazier, lower contrast)
    low_roofs(L, -4, g['W'] + 4, B - 2, 6, 14, Cp, S, seed=3, gable_p=0.4)
    # ---- far left: TETs (thermal power station): boiler house, turbine hall, conveyor, two striped chimneys
    slab(L, -2, B, 26, 5, 7, C, S, seed=1, wstep=3)
    K.facade(L, 22, B - 62, 34, 62, C)                                   # boiler house
    for wx in range(26, 54, 5):
        rect(L, wx, B - 56, 2, 44, C[0])
    hline(L, 21, B - 62, 36, C[3], N_UP)
    K.snow_line(L, 21, B - 63, 36, S, 1, 2)
    K.facade(L, 56, B - 34, 40, 34, C)                                   # turbine hall
    for wx in range(59, 93, 6):
        rect(L, wx, B - 30, 3, 18, C[0])
    K.snow_line(L, 55, B - 35, 42, S, 1, 3)
    for k in range(26):                                                  # coal conveyor gallery
        put(L, 96 + k, B - 34 + k, C[1])
        put(L, 96 + k, B - 33 + k, C[0])
    band = [[S['band'], S['band'], RU[5]], [SK[2], SK[3], SK[4]]]
    meta['smoke'].append(('tets_a', K.chimney(L, 36, B - 62, 66, 7, 5, C, bands=7, band_cols=band, seed=1)))
    meta['smoke'].append(('tets_b', K.chimney(L, 50, B - 62, 56, 6, 4, C, bands=7, band_cols=band, seed=2)))
    # ---- industrial district: saw-tooth halls, gasholder, warehouses, Intze water tower (seen at cam ~500-800)
    sawtooth_hall(L, 120, B, 88, 26, Cb, S, tooth=11, th=6, arched=True)
    water_tower(L, 186, B, 64, Cb, C, S)
    gasholder(L, 226, B - 2, 44, 30, C, S)
    sawtooth_hall(L, 246, B, 76, 22, Cb, S, tooth=10, th=5)
    # ---- new microdistrict: rows of five-storey panel blocks (two depths), a school, birches
    # (gap 598-634 keeps the sun free at cam 0; 756-800 stays low for the sun at cam 640)
    for (bx, bw, fl, sd, depth) in ((322, 46, 5, 11, 1), (362, 40, 5, 12, 0), (410, 52, 5, 13, 1),
                                    (456, 44, 4, 14, 0), (504, 58, 5, 15, 1), (560, 38, 5, 16, 0),
                                    (636, 48, 5, 17, 1), (680, 42, 4, 18, 0), (720, 34, 5, 19, 1)):
        Cc = Cp if depth else C
        slab(L, bx, B - (3 if depth else 0), bw, fl, 7, Cc, S, seed=sd, wstep=3, lit=0.02, antennas=2,
             ant_col=Cc[0], stair_every=6)
    K.facade(L, 538, B - 20, 30, 20, Cb)                                # school (3 storeys, brick)
    for wy in (B - 17, B - 11):
        for wx in range(541, 566, 4):
            rect(L, wx, wy, 2, 3, Cb[0])
    K.snow_line(L, 537, B - 21, 32, S, 1, 21)
    for (tx, th) in ((350, 22), (402, 18), (498, 20), (590, 22), (708, 17)):
        K.birch(L, tx, B, th, S, seed=tx, trunk_cols=[SK[2], SK[3]], twig_cols=[SK[0], SK[1]], mark=TE[4])
    # ---- low warehouses under the sun path at cam 640 (x ~772) and the train window at cam 1280
    for (wx, ww, wh) in ((756, 40, 14), (800, 30, 16), (884, 44, 13), (930, 40, 12)):
        K.facade(L, wx, B - wh, ww, wh, C)
        for k in range(wx + 3, wx + ww - 3, 7):
            rect(L, k, B - wh + 4, 3, 4, C[0])
        K.snow_line(L, wx - 1, B - wh - 1, ww + 2, S, 1, wx)
    sawtooth_hall(L, 830, B, 52, 20, Cb, S, tooth=9, th=5)
    meta['smoke'].append(('fi_east', K.chimney(L, 872, B, 110, 6, 4, Cb, bands=5, band_cols=band, seed=7)))
    for px_ in (904, 952):
        K.pylon(L, px_, B - 2, 20, C[0], rim=C[2])
    K.wire(L, 904 - 4, B - 20, 952 - 4, B - 20, 3, C[1])
    # ---- bypass railway embankment (KarskTrain rail at y 216) and ground haze
    embankment(L, 216, B, {'glint': SK[4], 'rail': TE[4], 'sleeper': TE[3], 'ballast': SK[1], 'snow': SK[4],
                           'shoulder': SK[3], 'slope': SK[2]}, seed=4)
    hz = Haze([[TE[2], TE[3], TE[4], SK[0], SK[1], SK[2], SK[3], SK[4], SK[5]],
               [ST[3], ST[4], ST[5], SK[3], SK[4], SK[5]],
               [RU[4], RU[5], SK[3], SK[4]], [SN[2], SK[4], SK[5]]])
    hz.shift(L, vfog(L, 176, B + 1, 2.6, 1.4))
    return L, meta


# =========================================================================== FAR CITY (0.12)
def make_far_city():
    S = K.STYLES['far_city']
    g = PLANES['far_city']
    B = g['base']
    L = SL.world_layer('far_city')
    C = S['conc']
    Cp = S['pale']
    Co = S['old']
    meta = {'smoke': [], 'lamps': []}
    rng = np.random.default_rng(9)
    # ---- continuous horizon: low roofs and groves
    low_roofs(L, -4, g['W'] + 4, B, 2, 7, Cp, S, seed=5, gable_p=0.55)
    for (tx, tw, th) in ((140, 26, 9), (232, 30, 8), (300, 18, 7), (452, 24, 9), (612, 16, 6), (730, 22, 8)):
        tree_clump(L, tx, B, tw, th, [SK[1], SK[2]], seed=tx)
    # ---- west: panel-block microdistrict (two rows) + tiny cranes
    for (bx, bw, fl, sd, back) in ((-2, 36, 5, 1, 1), (26, 44, 5, 2, 0), (72, 30, 4, 3, 1), (96, 40, 5, 4, 0)):
        slab(L, bx, B - (2 if back else 0), bw, fl, 3, Cp if back else C, S, seed=sd, wstep=2, lit=0.03,
             antennas=1, ant_col=SK[0])
    slab(L, 82, B, 22, 5, 3, C, S, seed=5, wstep=2, built=3)
    K.lattice_mast(L, 88, B - 9, 26, 2, 2, SK[0], step=3)
    hline(L, 76, B - 36, 22, SK[0])
    vline(L, 80, B - 35, 6, SK[0])
    # ---- old quarter: little church, low houses
    little_church(L, 176, B, Cp, S['metal'], S, seed=3)
    # ---- town centre: blocks, a bread factory with two thin chimneys, water tower
    for (bx, bw, fl, sd, back) in ((300, 34, 5, 7, 1), (328, 40, 5, 8, 0), (372, 30, 4, 9, 1), (398, 34, 5, 10, 0),
                                   (440, 28, 5, 11, 1), (470, 36, 4, 12, 0)):
        slab(L, bx, B - (2 if back else 0), bw, fl, 3, Cp if back else C, S, seed=sd, wstep=2, lit=0.03,
             antennas=1, ant_col=SK[0])
    K.facade(L, 354, B - 10, 20, 10, Co)
    for chx, chh in ((358, 30), (366, 24)):
        K.chimney(L, chx, B - 10, chh, 2, 2, Co, lip=False)
    K.facade(L, 430, B - 22, 3, 22, Co)                                  # water tower shaft + tank
    K.facade(L, 427, B - 30, 9, 8, Co)
    hline(L, 427, B - 31, 9, SK[3], N_UP)
    # ---- power station: two cooling towers flanking the sun, boiler house, chimneys, switchyard
    # the towers are the largest far structures (exp_cooling_towers): one value step darker than the slabs
    ct1 = cooling_tower(L, 546, B, 58, 44, 27, 31, [TE[4], SK[0], SK[0], SK[1], SK[3]], seed=1)
    ct2 = cooling_tower(L, 662, B, 50, 38, 23, 27, [TE[4], SK[0], SK[0], SK[1], SK[3]], seed=2)
    meta['towers'] = [ct1, ct2]
    # boiler house east of x 698 (x 680-698 = the sun at cam 640, crossed only by the thin chimney)
    K.facade(L, 698, B - 30, 44, 30, C)
    for wx in range(702, 738, 4):
        rect(L, wx, B - 26, 1, 18, SK[0])
    K.facade(L, 742, B - 14, 14, 14, C)
    K.snow_line(L, 697, B - 31, 46, S, 1, 4)
    band = [[S['band'], S['band'], S['band']], [SK[2], SK[3], SK[3]]]
    K.facade(L, 684, B - 8, 10, 8, C)
    meta['smoke'].append(('fc_chimney', K.chimney(L, 688, B - 8, 76, 4, 3, C, bands=5, band_cols=band, seed=5)))
    K.chimney(L, 704, B - 30, 40, 4, 3, C, bands=4, band_cols=band, seed=6)
    pyl = []
    for px_ in (356, 410, 470, 590, 762, 796):
        pts = K.pylon(L, px_, B - 1, 14, SK[0], rim=SK[1])
        pyl.append(pts)
    for a, b in zip(pyl[:-1], pyl[1:]):
        if b[0][0] - a[1][0] < 140:
            for k in range(2):
                K.wire(L, a[k][0], a[k][1], b[k][0], b[k][1], 4, SK[1])
    # ---- east: blocks + TV mast close to the sun (seen from cam ~1000 on)
    for (bx, bw, fl, sd, back) in ((776, 28, 5, 14, 0),):
        slab(L, bx, B - (2 if back else 0), bw, fl, 3, Cp if back else C, S, seed=sd, wstep=2, lit=0.03,
             antennas=1, ant_col=SK[0])
    K.lattice_mast(L, 757, B, 88, 4, 1, SK[0], rim=SK[1], step=4, lights=[88, 60, 32], light_col=S['lamp'],
                   guys=[(72, -20), (72, 20)], guy_col=SK[1])
    meta['lamps'] += [(757, B - 88), (757, B - 60), (757, B - 32)]
    # ---- haze: whole plane toward the horizon colour + dense ground haze under the base
    rect(L, 0, B, L.w, 360 - B, SK[4])
    hz = Haze([[TE[4], SK[0], SK[1], SK[2], SK[3], SK[4], SK[5]], [RU[5], SK[3], SK[4]], [SN[2], SK[4], SK[5]]])
    hz.shift(L, vfog(L, 180, B + 1, 1.6, 1.3))
    hz.shift(L, vfog(L, B, B + 20, 1.0, 1.0))
    return L, meta
