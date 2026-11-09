"""env_c3p2_quay_near -- the near planes and props of the night quay (L_C3_Quay), lit with normal maps.
wing       (p 1)     the corner of the burning east wing (the old Kurhaus, 1909): rusticated base with five
                     souterrain windows full of fire, dark upper windows mirroring it, mansard + one lit dormer,
                     the yard railing with the open gate and the iron coal hatch they came out of (x ~178)
promenade  (p 1)     the quay: snow, hoses, tyre tracks, footprints from the hatch to the bench, the stone
                     balustrade with its lanterns, two snowed-in benches, the guard's trestle, the bridgehead
                     pylon with the city arms, the ramp wall, the tram stop and its shelter, catenary poles
fg         (p 1.25)  low dark snow banks, bollards and the hydrant line along the bottom edge (unlit)
glow_air   (p 1)     soft additive halos: lanterns, the fire, headlights (alpha in dithered steps)
props      (y-sorted) fire engine with turntable ladder, the two delegation cars (+ *_hist pennants), the bench
                     with the broken file
All p 1 canvases share the scene lights below, so props and layers carry one coherent light bake.
"""
from __future__ import annotations

import math

import numpy as np

import env_c3p2_quay_kit as K
from env_c3p2_quay_kit import (Canvas, Light, Layer, resolve, bayer, value_noise, NI, SL, IR, CR, PA, LA, SK, SN, RD,
                               SKIN, glow_image)

# ------------------------------------------------------------------------------------------------ layout (world)
WING = dict(x1=380, quoin=356, base=266, cornice=46, roof=12)
BASE_WIN = [30, 104, 178, 252, 326]            # souterrain window axes (fire)
BASE_WIN_Y = (244, 262)
FENCE = dict(x0=0, x1=392, top=254, plinth=278, ground=290, gate=(154, 200))
HATCH = (166, 190, 268, 276)
BALU = dict(x0=392, x1=1548, step=64, first=400, top=258, rail=261, plinth=280, base=288)
LAMPS = [464, 592, 784, 976, 1168, 1360]         # on balustrade pedestals; 784 lights the bench
LAMP_Y = 194                                   # lantern glass centre
SNOW_BENCHES = [496, 880]
TRESTLE = (1064, 1100)
PYLON = (1548, 1584)
PYLON_LAMP = (1566, 176)
TRAM_SIGN_X = 1700
SHELTER = (1768, 1852)
SHELTER_LAMP = (1810, 230)
ARMS_PLAQUE = (1672, 259)                      # the city arms on the ramp wall (find exp_bridge_arms ~ x 1690)
WALL_LAMP = (1650, 244)
POLES = [1640, 1890]
TRUCK = dict(x0=258, x1=430, ground=292)
CAR_REICH = dict(x0=1112, x1=1232)
CAR_USSR = dict(x0=1286, x1=1416)
BENCH = dict(x0=734, x1=786)
P_FG = 1.25


def scene_lights():
    L = []
    for lx in LAMPS:
        L.append(Light('warm', lx, LAMP_Y + 2, 62, 1.0, up=0.35, name='lamp'))
        L.append(Light('warm', lx, 292, 78, 0.9, sq=2.8, name='pool'))
    L.append(Light('warm', PYLON_LAMP[0], PYLON_LAMP[1] + 4, 74, 1.0, up=0.4))
    L.append(Light('warm', PYLON_LAMP[0] + 6, 292, 86, 0.75, sq=2.8))
    L.append(Light('warm', SHELTER_LAMP[0], SHELTER_LAMP[1] + 4, 40, 0.7, up=0.5))
    L.append(Light('warm', SHELTER_LAMP[0], 290, 60, 0.6, sq=2.6))
    L.append(Light('warm', WALL_LAMP[0] + 2, WALL_LAMP[1] + 4, 46, 0.85, up=0.5))
    L.append(Light('warm', WALL_LAMP[0] + 8, 292, 50, 0.45, sq=2.6))
    for c in BASE_WIN:
        L.append(Light('fire', c, 250, 74, 1.0, pw=2.2))
        L.append(Light('fire', c, 284, 70, 0.4, sq=2.2, pw=2.2))
    L.append(Light('fire', 180, 240, 300, 0.12))
    L.append(Light('fire', 190, 268, 240, 0.5, sq=4.0, up=6.0, pw=1.5))     # amber glow rising up the facade
    L.append(Light('warm', TRUCK['x1'] + 2, 262, 42, 0.7))                  # headlight
    L.append(Light('warm', TRUCK['x1'] + 46, 298, 70, 0.55, sq=3.0))       # its beam on the snow
    L.append(Light('warm', CAR_REICH['x0'] + 4, 272, 16, 0.45))            # sidelights
    L.append(Light('warm', CAR_USSR['x0'] + 4, 272, 16, 0.45))
    L.append(Light('warm', 1262, 262, 12, 0.5))                            # the drivers' lighter
    return L


def snow_cap(cv: Canvas, x, y, w, depth=2, seed=0, tone=0.72):
    rng = np.random.default_rng(abs(int(seed)) + 31)
    for xx in range(int(x), int(x + w)):
        d = depth + (1 if rng.random() < 0.3 else 0) - (1 if rng.random() < 0.15 else 0)
        for k in range(max(1, d)):
            cv.px(xx, y - k, 'snow', tone - 0.06 * k + (0.04 if k == max(1, d) - 1 else 0), hgt=0.8)


# ================================================================================================= wing
def make_wing(lights):
    W, H = 400, 296
    cv = Canvas(W, H, 'wing')
    x1, qx, base = WING['x1'], WING['quoin'], WING['base']
    # ---- body + quoins
    cv.rect(0, 52, x1, base - 52, 'stone', 0.15, hgt=0.4)
    cv.texture(0, 52, x1, base - 52, 0.022, cell=5.0, seed=901)
    for k, y in enumerate(range(58, 232, 10)):
        w = 24 if k % 2 == 0 else 15
        cv.rect(x1 - w, y, w, 9, 'stone', 0.25, hgt=0.5)
        cv.rect(x1 - w, y + 9, w, 1, 'stone', 0.11)
    cv.rect(x1 - 1, 52, 1, base - 52, 'stone', 0.12)                 # shaded return of the corner
    # ---- band courses
    for (by, bh) in ((166, 4), (100, 3)):
        cv.rect(0, by, x1 + 2, bh, 'stone', 0.27, hgt=0.6)
        cv.rect(0, by + bh, x1 + 2, 1, 'stone', 0.09)
        snow_cap(cv, 0, by - 1, x1 + 2, 1, seed=by)
    # ---- rusticated base (souterrain storey above the yard)
    cv.rect(0, 232, x1, base - 232, 'stone', 0.17, hgt=0.45)
    for y in range(236, base, 6):
        cv.rect(0, y, x1, 1, 'stone', 0.08)
        for xx in range((y // 6) % 2 * 9, x1, 18):
            cv.px(xx, y + 1, 'stone', 0.08)
            cv.px(xx, y + 2, 'stone', 0.08)
    cv.rect(0, 230, x1 + 2, 2, 'stone', 0.28, hgt=0.6)               # water table
    snow_cap(cv, 0, 229, x1 + 2, 1, seed=230)
    # ---- windows of the three upper storeys on the five axes (+ one beyond the left edge)
    axes = [-44] + BASE_WIN
    for ax in axes:
        _window(cv, ax - 11, 178, 22, 46, arched=True)               # Hochparterre
        _window(cv, ax - 10, 114, 20, 40, pediment=True)             # 1st floor
        _window(cv, ax - 9, 68, 18, 28)                              # 2nd floor
    # ---- cornice + mansard
    cy = WING['cornice']
    cv.rect(0, cy, x1 + 6, 8, 'stone', 0.26, hgt=0.7)
    cv.rect(0, cy + 6, x1 + 6, 2, 'stone', 0.10)
    for xx in range(0, x1 + 6, 4):
        cv.px(xx, cy + 5, 'stone', 0.12)                             # dentils
    cv.rect(0, 14, x1 - 4, cy - 14, 'slate', 0.07, hgt=0.55)
    for xx in range(2, x1 - 4, 5):
        cv.rect(xx, 16, 1, cy - 16, 'slate', 0.03)                    # standing seams
    for yy in range(20, cy, 8):
        snow_cap(cv, 0, yy, x1 - 4, 1, seed=yy, tone=0.6)
    snow_cap(cv, 0, cy - 1, x1 + 6, 3, seed=cy, tone=0.74)
    cv.rect(0, 6, x1 - 8, 8, 'snow', 0.62, hgt=0.7)                   # snow on the upper roof
    cv.texture(0, 6, x1 - 8, 8, 0.05, cell=3.0, seed=905)
    for (chx, chw) in ((62, 12), (238, 14)):
        cv.rect(chx, -2, chw, 10, 'stone', 0.15, hgt=0.7)
        snow_cap(cv, chx - 1, 0, chw + 2, 2, seed=chx)
    info = {'dormer_lit': None}
    for i, ax in enumerate(BASE_WIN):
        dx = ax - 8
        cv.rect(dx, 22, 16, 22, 'stone', 0.21, hgt=0.65)
        cv.poly([(dx - 2, 23), (ax, 14), (dx + 18, 23)], 'slate', 0.09)
        snow_cap(cv, dx - 2, 22, 20, 2, seed=ax)
        lit = (i == 1)
        cv.rect(dx + 4, 27, 8, 13, 'lit' if lit else 'glass', 0.55 if lit else 0.05)
        cv.rect(dx + 7, 27, 2, 13, 'stone', 0.16)
        if lit:
            info['dormer_lit'] = [ax, 33]
    # ---- souterrain windows: fire behind iron bars
    for c in BASE_WIN:
        x0 = c - 13
        y0, y1 = BASE_WIN_Y
        cv.rect(x0 - 2, y0 - 2, 30, y1 - y0 + 4, 'stone', 0.24, hgt=0.55)       # lighter surround
        T = np.zeros((y1 - y0, 26), np.float32)
        yy, xx = np.mgrid[0:y1 - y0, 0:26].astype(np.float32)
        core = 1 - np.clip(np.hypot((xx - 13) / 13.0, (yy - (y1 - y0)) / (y1 - y0) * 1.1), 0, 1)
        n = value_noise(26, y1 - y0, 3.0, seed=c, octaves=2)
        T = 0.15 + 0.85 * core + 0.25 * (n - 0.5)
        cv.put(np.ones((y1 - y0, 26), bool), x0, y0, 'flame', T)
        for bx in (x0 + 6, x0 + 13, x0 + 20):
            cv.rect(bx, y0, 1, y1 - y0, 'iron', 0.02)
        cv.rect(x0, y0 + 8, 26, 1, 'iron', 0.02)
        # soot plumes painted above the window (smoke-stained rustication)
        for k in range(26):
            hgt_ = int(10 + 22 * math.sin((k + 2) / 30.0 * math.pi))
            cv.shade_rect(x0 + k, y0 - 2 - hgt_, 1, hgt_, -0.07)
        cv.rect(x0 - 3, y1 + 2, 32, 2, 'stone', 0.12)               # light well rim
    # ---- yard behind the railing: trampled snow, the open coal hatch, two body prints, coal dust
    gy = base
    cv.rect(0, gy, FENCE['x1'], FENCE['plinth'] - gy, 'snow', 0.50, hgt=0.3)
    cv.texture(0, gy, FENCE['x1'], FENCE['plinth'] - gy, 0.05, cell=3.0, seed=907)
    hx0, hx1, hy0, hy1 = HATCH
    cv.rect(hx0 - 2, hy0 - 1, hx1 - hx0 + 4, hy1 - hy0 + 2, 'iron', 0.14, hgt=0.35)   # frame
    cv.rect(hx0, hy0, hx1 - hx0, hy1 - hy0, 'glass', 0.0)                             # the black chute
    cv.poly([(hx1, hy0), (hx1 + 9, hy0 - 12), (hx1 + 12, hy0 - 11), (hx1 + 3, hy0 + 1)], 'iron', 0.2, hgt=0.6)
    cv.line(hx1 + 2, hy0 - 2, hx1 + 9, hy0 - 10, 'iron', 0.32)                        # cast rib of the lid
    rng = np.random.default_rng(909)
    for _ in range(70):                                                                 # coal dust
        cv.px(hx0 - 10 + rng.integers(0, 50), hy0 - 2 + rng.integers(0, 12), 'stone', 0.03)
    for (bx, by) in ((214, 270), (236, 273)):                                           # where they lay
        cv.shade(Layer(1, 1).ellipse_mask(0, 0, 11, 2.5)[0], bx - 11, by - 2, -0.13)
    # ---- the railing on its plinth, the gate posts and one open gate leaf
    pt, pl, gr = FENCE['top'], FENCE['plinth'], FENCE['ground']
    g0, g1 = FENCE['gate']
    cv.rect(0, pl, FENCE['x1'], gr - pl, 'stone', 0.17, hgt=0.5)
    cv.rect(0, pl, FENCE['x1'], 1, 'stone', 0.3)
    snow_cap(cv, 0, pl - 1, FENCE['x1'], 2, seed=278)
    for bx in range(2, FENCE['x1'], 5):
        if g0 - 8 <= bx <= g1 + 8:
            continue
        cv.rect(bx, pt, 1, pl - pt, 'iron', 0.05, hgt=0.7)
        cv.px(bx, pt - 1, 'iron', 0.14)
        cv.px(bx, pt - 2, 'iron', 0.10)
    for ry in (pt + 4, pl - 4):
        for seg in ((0, g0 - 8), (g1 + 8, FENCE['x1'])):
            cv.rect(seg[0], ry, seg[1] - seg[0], 1, 'iron', 0.07)
    for (px0, px1) in ((g0 - 8, g0), (g1, g1 + 8)):
        cv.rect(px0, 244, px1 - px0, gr - 244, 'stone', 0.22, hgt=0.6)
        cv.rect(px0 - 1, 242, px1 - px0 + 2, 3, 'stone', 0.3)
        cv.ellipse((px0 + px1) / 2, 238.5, 3, 3, 'stone', 0.28)
        snow_cap(cv, px0 - 1, 241, px1 - px0 + 2, 2, seed=px0)
    for k in range(12):                                               # open leaf, swung into the yard
        bx = g0 + 1 + k
        top = pt + 2 + k // 3
        cv.rect(bx, top, 1, pl - 3 - top, 'iron', 0.06)
    cv.rect(g0 + 1, pt + 6, 12, 1, 'iron', 0.1)
    L = resolve(cv, lights)
    info['size'] = [W, H]
    return L, info


def _window(cv: Canvas, x, y, w, h, arched=False, pediment=False):
    cv.rect(x - 2, y - 2, w + 4, h + 4, 'stone', 0.23, hgt=0.6)        # surround
    cv.rect(x, y, w, h, 'glass', 0.05, hgt=0.2)
    if arched:
        for xx in range(w + 4):
            u = (xx + 0.5) / (w + 4) * 2 - 1
            lift = int(round(5 * math.sqrt(max(0.0, 1 - u * u))))
            cv.rect(x - 2 + xx, y - 2 - lift, 1, lift, 'stone', 0.27)
        cv.rect(x + w // 2 - 2, y - 8, 4, 5, 'stone', 0.33)            # keystone
    if pediment:
        cv.poly([(x - 4, y - 3), (x + w / 2, y - 10), (x + w + 4, y - 3)], 'stone', 0.27, hgt=0.65)
        snow_cap(cv, x - 3, y - 4, w + 7, 1, seed=x + y)
    # mullion + transom, reflections streak
    cv.rect(x + w // 2, y, 1, h, 'stone', 0.15)
    cv.rect(x, y + h // 3, w, 1, 'stone', 0.15)
    for k in range(min(w, h) // 3):
        cv.px(x + 2 + k, y + h - 4 - 2 * k, 'glass', 0.18)
    cv.rect(x - 3, y + h + 2, w + 6, 2, 'stone', 0.3, hgt=0.65)        # sill
    snow_cap(cv, x - 3, y + h + 1, w + 6, 1, seed=x * 3 + y)


# ================================================================================================= promenade
def make_promenade(lights):
    W, H = 1920, 360
    cv = Canvas(W, H, 'promenade')
    rng = np.random.default_rng(920)
    # ---- the quay pavement under snow
    gy = 286
    yy = np.arange(gy, H, dtype=np.float32)[:, None]
    tone = np.where(yy < 296, 0.40 + 0.04 * (yy - gy) / 10, np.where(yy < 307, 0.43, 0.47 + 0.02 * (yy - 307) / 53))
    tone = np.repeat(tone, W, axis=1)
    n = np.repeat(value_noise(W // 4 + 2, H - gy, 3.0, seed=921, octaves=3), 4, axis=1)[:, :W]
    tone = tone + 0.05 * (n - 0.5)
    cv.put(np.ones((H - gy, W), bool), 0, gy, 'snow', tone, hgt=0.3)
    band = (slice(296 - gy, 307 - gy), slice(0, W))                   # walk band: trampled, slushy
    sl = value_noise(W, 11, 2.5, seed=922, octaves=2)
    cv.tone[296:307, :] -= 0.07 * np.clip((sl - 0.4) * 3, 0, 1)
    for _ in range(1400):                                               # sparkle
        cv.px(int(rng.integers(0, W)), int(rng.integers(308, H)), 'snow', 0.85)
    cv.rect(0, 342, W, 1, 'snow', 0.34)                                 # gutter of the quay street
    cv.rect(0, 343, W, 2, 'snow', 0.4)
    # footprints of two men from the hatch to the bench (one drags a foot)
    for i, x in enumerate(range(186, 748, 7)):
        cv.px(x, 299 + (i % 2), 'snow', 0.30)
        cv.px(x + 1, 299 + (i % 2), 'snow', 0.33)
        cv.px(x + 3, 303 + ((i + 1) % 2), 'snow', 0.30)
        if i % 2:
            cv.px(x + 4, 304, 'snow', 0.35)
    # tyre tracks of the fire engine and the cars (curving in from the bridge side)
    for (yb, x0_, x1_) in ((318, 430, 1560), (326, 430, 1560), (312, 1100, 1530), (316, 1100, 1530)):
        for x in range(x0_, x1_):
            y = int(yb + 4 * math.sin((x - x0_) / 260.0))
            cv.px(x, y, 'snow', 0.30)
            cv.px(x, y + 1, 'snow', 0.36)
    # tram rails along the quay street, toward the bridge
    for ry in (330, 337):
        for x in range(1160, W):
            cv.px(x, ry, 'iron', 0.30 if (x * 7) % 9 else 0.2)
            cv.px(x, ry + 1, 'snow', 0.30)
    # hoses: hydrant (in the street) -> pump inlet; delivery lines -> the hose team and into the yard gate
    cv.rect(468, 322, 5, 15, 'red', 0.28, hgt=0.6)                     # hydrant
    cv.rect(466, 320, 9, 2, 'red', 0.36)
    cv.rect(467, 336, 7, 2, 'iron', 0.12)
    snow_cap(cv, 466, 319, 9, 2, seed=468)
    _hose(cv, [(470, 330), (452, 324), (440, 314), (426, 300), (414, 291)], seed=1)
    _hose(cv, [(276, 291), (250, 298), (214, 301), (178, 297), (150, 293)], seed=2)
    _hose(cv, [(284, 291), (258, 302), (226, 308), (196, 304), (180, 296), (176, 286)], seed=3)
    # ---- balustrade (the river shows through above and between the balusters)
    b = BALU
    x0, x1 = b['x0'], b['x1']
    cv.rect(x0, b['plinth'], x1 - x0, b['base'] - b['plinth'], 'stone', 0.18, hgt=0.5)
    cv.rect(x0, b['plinth'], x1 - x0, 1, 'stone', 0.30)
    for x in range(x0 + 2, x1, 4):
        cv.rect(x, 266, 2, 14, 'stone', 0.22, hgt=0.6)
        cv.px(x - 1, 271, 'stone', 0.20)
        cv.px(x + 2, 272, 'stone', 0.13)
        cv.rect(x, 273, 2, 3, 'stone', 0.25)
        cv.px(x + 1, 268, 'stone', 0.12)
    cv.rect(x0, b['rail'], x1 - x0, 5, 'stone', 0.28, hgt=0.7)
    cv.rect(x0, b['rail'] + 4, x1 - x0, 1, 'stone', 0.12)
    snow_cap(cv, x0, b['rail'] - 1, x1 - x0, 3, seed=261, tone=0.74)
    peds = list(range(b['first'], x1, b['step']))
    for px_ in peds:
        cv.rect(px_ - 5, 255, 11, b['base'] - 255, 'stone', 0.23, hgt=0.65)
        cv.rect(px_ - 5, 255, 2, b['base'] - 255, 'stone', 0.31)
        cv.rect(px_ + 4, 255, 2, b['base'] - 255, 'stone', 0.14)
        cv.rect(px_ - 6, 252, 13, 3, 'stone', 0.32, hgt=0.7)
        snow_cap(cv, px_ - 6, 251, 13, 3, seed=px_, tone=0.78)
    # ---- lanterns on every third pedestal
    for lx in LAMPS:
        _lantern(cv, lx, 251, LAMP_Y)
    # ---- snowed-in benches against the balustrade
    for bx in SNOW_BENCHES:
        _bench(cv, bx - 26, snowed=True)
    # ---- bridgehead pylon with the great lantern and the city arms (exp_bridge_arms)
    p0, p1 = PYLON
    cv.rect(p0, 200, p1 - p0, 290 - 200, 'stone', 0.21, hgt=0.6)
    for y in range(204, 290, 7):
        cv.rect(p0, y, p1 - p0, 1, 'stone', 0.1)
        cv.px(p0 + (12 if (y // 7) % 2 else 24), y + 3, 'stone', 0.1)
    cv.rect(p0, 200, 3, 90, 'stone', 0.3)
    cv.rect(p1 - 3, 200, 3, 90, 'stone', 0.13)
    cv.rect(p0 - 3, 196, p1 - p0 + 6, 5, 'stone', 0.32, hgt=0.75)
    snow_cap(cv, p0 - 3, 195, p1 - p0 + 6, 3, seed=1548, tone=0.78)
    _arms(cv, (p0 + p1) // 2, 222)
    cx = PYLON_LAMP[0]
    cv.rect(cx - 2, 184, 5, 12, 'iron', 0.12)
    cv.rect(cx - 6, 164, 13, 2, 'iron', 0.2)
    snow_cap(cv, cx - 6, 163, 13, 2, seed=1566)
    cv.poly([(cx - 4, 167), (cx + 5, 167), (cx + 3, 181), (cx - 2, 181)], 'lit', 0.7)
    cv.rect(cx, 167, 1, 14, 'iron', 0.1)
    cv.rect(cx - 4, 173, 9, 1, 'iron', 0.12)
    cv.rect(cx - 4, 182, 9, 2, 'iron', 0.2)
    cv.rect(cx, 158, 1, 5, 'iron', 0.2)
    # ---- the ramp wall rising toward the bridge
    for x in range(p1, W):
        top = int(round(262 - (x - p1) / (W - p1) * 26))
        cv.rect(x, top, 1, 290 - top, 'stone', 0.19, hgt=0.5)
        cv.px(x, top, 'stone', 0.32)
        cv.px(x, top + 1, 'stone', 0.27)
        if (x - p1) % 9 == 0:
            for y in range(top + 6, 290, 6):
                cv.px(x, y, 'stone', 0.11)
    for x in range(p1, W):
        top = int(round(262 - (x - p1) / (W - p1) * 26))
        snow_cap(cv, x, top - 1, 1, 2, seed=x, tone=0.75)
    for y in range(266, 290, 6):
        cv.rect(p1, y, W - p1, 1, 'stone', 0.12)
    # the city arms as a bronze-framed stone relief on the ramp wall, under a bracket lamp
    ax_, ay_ = ARMS_PLAQUE
    cv.rect(ax_ - 15, ay_ - 2, 31, 31, 'iron', 0.2, hgt=0.7)
    cv.rect(ax_ - 14, ay_ - 1, 29, 29, 'stone', 0.2, hgt=0.75)
    _arms(cv, ax_, ay_)
    tw = K.V.text_width('VELTRAVA', 's')
    cv.text(ax_ - tw // 2, ay_ + 22, 'VELTRAVA', NI[3])
    wx_, wy_ = WALL_LAMP
    cv.rect(wx_ - 6, wy_ + 6, 8, 1, 'iron', 0.2)
    cv.rect(wx_ - 6, wy_ + 6, 1, 8, 'iron', 0.2)
    cv.poly([(wx_ - 2, wy_ - 4), (wx_ + 4, wy_ - 4), (wx_ + 3, wy_ + 5), (wx_ - 1, wy_ + 5)], 'lit', 0.7)
    cv.rect(wx_ - 3, wy_ - 6, 8, 2, 'iron', 0.2)
    snow_cap(cv, wx_ - 3, wy_ - 7, 8, 2, seed=1650)
    # ---- tram stop sign (trilingual plate), shelter with its lamp and a commission poster
    sx = TRAM_SIGN_X
    cv.rect(sx, 214, 2, 76, 'iron', 0.16, hgt=0.7)
    cv.ellipse(sx + 1, 212, 7, 7, 'patina', 0.30, hgt=0.75)
    cv.ellipse(sx + 1, 212, 5.5, 5.5, 'snow', 0.62)
    cv.ink_rect(sx - 1, 209, 1, 6, PA[1])
    cv.ink_rect(sx + 3, 209, 1, 6, PA[1])
    cv.ink_rect(sx, 211, 3, 1, PA[1])
    snow_cap(cv, sx - 5, 205, 12, 2, seed=1700)
    cv.rect(sx - 7, 224, 16, 15, 'iron', 0.10)
    cv.rect(sx - 6, 225, 14, 13, 'snow', 0.5)
    cv.text(sx - 5, 226, '7 12', NI[2])
    cv.ink_rect(sx - 5, 232, 12, 1, NI[3])
    cv.ink_rect(sx - 5, 235, 9, 1, NI[3])
    s0, s1 = SHELTER
    cv.rect(s0, 224, 2, 66, 'iron', 0.14, hgt=0.7)
    cv.rect(s1 - 2, 224, 2, 66, 'iron', 0.14, hgt=0.7)
    cv.rect(s0 - 3, 220, s1 - s0 + 6, 4, 'iron', 0.2, hgt=0.75)
    snow_cap(cv, s0 - 3, 219, s1 - s0 + 6, 3, seed=1768, tone=0.78)
    for gx in range(s0 + 2, s1 - 2, 20):
        cv.rect(gx, 226, 19, 52, 'glass', 0.08, hgt=0.3, recv=0.25)
        cv.rect(gx + 19, 226, 1, 52, 'iron', 0.12)
        for k in range(10):
            cv.px(gx + 3 + k, 270 - 3 * k, 'glass', 0.24)
    cv.rect(s0 + 2, 278, s1 - s0 - 4, 2, 'iron', 0.14)
    cv.rect(s0 + 10, 266, 40, 3, 'wood', 0.22, hgt=0.6)                  # bench in the shelter
    cv.rect(s0 + 12, 269, 2, 9, 'iron', 0.1)
    cv.rect(s0 + 46, 269, 2, 9, 'iron', 0.1)
    cv.rect(s1 - 22, 232, 16, 22, 'snow', 0.55)                           # poster (cream), red band
    cv.rect(s1 - 22, 232, 16, 4, 'red', 0.3)
    cv.ink_rect(s1 - 20, 240, 12, 1, NI[3])
    cv.ink_rect(s1 - 20, 243, 10, 1, NI[3])
    cv.ink_rect(s1 - 20, 246, 12, 1, NI[3])
    lx_, ly_ = SHELTER_LAMP
    cv.rect(lx_ - 3, 224, 7, 3, 'lit', 0.8)
    # ---- catenary poles and the tram wire
    for px_ in POLES:
        cv.rect(px_, 150, 3, 140, 'iron', 0.13, hgt=0.7)
        cv.rect(px_ - 1, 288, 5, 2, 'iron', 0.2)
        cv.rect(px_ - 14, 156, 17, 1, 'iron', 0.16)
        cv.line(px_ - 12, 157, px_, 168, 'iron', 0.12)
        snow_cap(cv, px_ - 1, 149, 5, 2, seed=px_)
    for x in range(1500, W):
        y = 158 + int(round(3 * math.sin(((x - 1500) % 250) / 250.0 * math.pi)))
        cv.px(x, y, 'iron', 0.18)
    L = resolve(cv, lights)
    return L, {'pedestals': peds}


def _hose(cv: Canvas, pts, seed=0):
    import pg
    path = pg.bezier(pts, n=90)
    for i, (x, y) in enumerate(path):
        cv.rect(int(round(x)), int(round(y)), 2, 2, 'cloth', 0.08, hgt=0.6)
        cv.px(int(round(x)), int(round(y)) - 1, 'cloth', 0.16)
        if i % 30 == 15:
            cv.rect(int(round(x)) - 1, int(round(y)) - 1, 3, 3, 'iron', 0.34)       # coupling


def _lantern(cv: Canvas, x, base_y, glass_y):
    cv.rect(x - 2, base_y - 6, 5, 6, 'iron', 0.14, hgt=0.7)              # foot on the pedestal
    cv.rect(x - 1, glass_y + 8, 3, base_y - 6 - glass_y - 8, 'iron', 0.12, hgt=0.75)
    cv.px(x - 1, glass_y + 20, 'iron', 0.22)
    cv.rect(x - 3, glass_y + 6, 7, 2, 'iron', 0.2)
    cv.poly([(x - 4, glass_y - 6), (x + 5, glass_y - 6), (x + 3, glass_y + 6), (x - 2, glass_y + 6)], 'lit', 0.72)
    cv.rect(x, glass_y - 6, 1, 12, 'iron', 0.08)
    cv.rect(x - 5, glass_y - 8, 11, 2, 'iron', 0.2, hgt=0.8)
    cv.rect(x - 3, glass_y - 10, 7, 2, 'iron', 0.16)
    cv.rect(x, glass_y - 13, 1, 3, 'iron', 0.2)
    snow_cap(cv, x - 5, glass_y - 9, 11, 2, seed=x, tone=0.8)


def _bench(cv: Canvas, x0, snowed=False):
    """Bench facing the promenade, backrest against the balustrade; x0 = left end (52 px wide)."""
    for lx in (x0 + 3, x0 + 46):
        cv.rect(lx, 270, 3, 22, 'iron', 0.1, hgt=0.6)
        cv.rect(lx - 1, 291, 5, 1, 'iron', 0.12)
        cv.px(lx + 3, 284, 'iron', 0.1)
    for k, y in enumerate((268, 271, 274)):
        cv.rect(x0, y, 52, 2, 'wood', 0.24 - 0.03 * k, hgt=0.6)
    cv.rect(x0 - 1, 281, 54, 3, 'wood', 0.27, hgt=0.65)
    cv.rect(x0, 284, 52, 1, 'wood', 0.1)
    if snowed:
        snow_cap(cv, x0 - 1, 267, 54, 3, seed=x0, tone=0.76)
        for xx in range(x0 - 1, x0 + 53):
            d = 3 + int(2 * math.sin((xx - x0) / 52.0 * math.pi))
            for k in range(d):
                cv.px(xx, 280 - k, 'snow', 0.7 + 0.04 * (k == d - 1))


def _arms(cv: Canvas, cx, y):
    """The fictional city arms of Veltrava: a white three-arch bridge over waves on a slate-blue shield."""
    cv.poly([(cx - 10, y), (cx + 10, y), (cx + 10, y + 14), (cx, y + 21), (cx - 10, y + 14)], 'stone', 0.34, hgt=0.8)
    cv.poly([(cx - 8, y + 2), (cx + 8, y + 2), (cx + 8, y + 13), (cx, y + 19), (cx - 8, y + 13)], 'slate', 0.26)
    cv.ink_rect(cx - 7, y + 7, 15, 1, SN[3])
    for k in (-5, 0, 5):
        cv.ink_px(cx + k - 2, y + 8, SN[3])
        cv.ink_px(cx + k + 2, y + 8, SN[3])
        cv.ink_px(cx + k - 2, y + 9, SN[3])
        cv.ink_px(cx + k + 2, y + 9, SN[3])
    for k in range(-7, 8):
        cv.ink_px(cx + k, y + 12 + ((k + 8) // 2) % 2, SN[1])


# ================================================================================================= foreground
def make_fg():
    W, H = K.layer_w(P_FG), 360
    L = Layer(W, H, 'fg')
    rng = np.random.default_rng(940)
    dark, mid, top = NI[0], NI[1], SL[1]
    x = 0
    while x < W:
        seg = int(rng.integers(60, 180))
        gap = int(rng.integers(30, 120))
        for xx in range(x, min(W, x + seg)):
            u = (xx - x) / seg
            h = int(8 + 12 * math.sin(u * math.pi) + 3 * math.sin(xx / 7.0))
            y0 = H - h
            L.rect(xx, y0, 1, h, dark)
            L.px(xx, y0, top)
            if h > 6:
                L.px(xx, y0 + 1, mid)
        x += seg + gap
    for bx in range(90, W, 230):
        L.rect(bx, 322, 5, 38, dark)
        L.rect(bx - 1, 320, 7, 2, mid)
        L.rect(bx - 1, 318, 7, 2, top)
    L.c[..., 3] = np.where(L.c[..., 3] > 0, 255, 0).astype(np.uint8)
    return L, {}


# ================================================================================================= glow (add)
def make_glow():
    g = []
    for lx in LAMPS:
        g.append((lx + 0.5, LAMP_Y, 26, 0.42, LA[3], 1.0))
    g.append((PYLON_LAMP[0], PYLON_LAMP[1] + 2, 30, 0.42, LA[3], 1.0))
    g.append((SHELTER_LAMP[0], SHELTER_LAMP[1], 18, 0.3, LA[3], 1.0))
    g.append((WALL_LAMP[0] + 1, WALL_LAMP[1], 16, 0.36, LA[3], 1.0))
    g.append((TRUCK['x1'] + 2, 262, 18, 0.4, LA[4], 1.0))
    arr = glow_image(K.WORLD_W, K.WORLD_H, g, levels=6, max_a=0.5)
    # round 13: the fire's own halos are pixel fire light -- flat additive bands with dithered edges
    # (pixel_fire_bake.halo) in the lamp ramp's hue, summed with whatever lantern light lies under them
    import pixel_fire_bake as PFB
    tints = tuple(tuple(int(round(v * k)) for v in LA[2][:3]) for k in (0.09, 0.17, 0.27))
    for c in BASE_WIN:
        hl = PFB.halo(92, 72, 46, 36, 44, 34, tints)
        x0, y0 = int(c) - 46, 250 - 36
        xa, xb = max(0, x0), min(K.WORLD_W, x0 + 92)
        sub, hs = arr[y0:y0 + 72, xa:xb], hl[:, xa - x0:xb - x0]
        m = hs[..., 3] > 0
        add = sub[..., :3].astype(np.float32) * (sub[..., 3:4].astype(np.float32) / 255.0) + hs[..., :3]
        sub[m, :3] = np.clip(np.rint(add[m]), 0, 255).astype(np.uint8)
        sub[m, 3] = 255
    L = Layer(K.WORLD_W, K.WORLD_H, 'glow_air')
    L.c = arr
    return L, {}


# ================================================================================================= props
def _prop_canvas(x0, y0, w, h, name):
    return Canvas(w, h, name, ox=x0, oy=y0)


def make_fire_engine(lights):
    """Ladder truck of the Veltrava fire brigade (round-nosed 1950s type), facing right, ladder raised."""
    X0, Y0, W, H = 160, 84, 280, 210
    cv = _prop_canvas(X0, Y0, W, H, 'fire_engine')
    gx = lambda x: x - X0
    gy = lambda y: y - Y0
    t0, t1, gnd = TRUCK['x0'], TRUCK['x1'], TRUCK['ground']
    # turntable ladder (behind the body top), leaning to the 1st floor window at x ~ 190
    lx0, ly0, lx1, ly1 = 312, 236, 196, 112
    ln = math.hypot(lx1 - lx0, ly1 - ly0)
    ux, uy = (lx1 - lx0) / ln, (ly1 - ly0) / ln
    nx, ny = -uy, ux
    for side in (-2.5, 2.5):
        cv.line(gx(lx0 + nx * side), gy(ly0 + ny * side), gx(lx1 + nx * side), gy(ly1 + ny * side), 'iron', 0.34, hgt=0.8)
    for k in range(4, int(ln), 5):
        ax, ay = lx0 + ux * k, ly0 + uy * k
        cv.line(gx(ax - nx * 2), gy(ay - ny * 2), gx(ax + nx * 2), gy(ay + ny * 2), 'iron', 0.24)
    for k in range(10, int(ln), 23):                                   # snow on the upper rail
        ax, ay = lx0 + ux * k + nx * 3.5, ly0 + uy * k + ny * 3.5
        cv.px(gx(ax), gy(ay), 'snow', 0.7)
        cv.px(gx(ax) + 1, gy(ay), 'snow', 0.66)
    # body (rear): red lockers with roller shutters
    by0 = 240
    cv.rect(gx(t0 + 4), gy(by0), 112, 40, 'red', 0.22, hgt=0.55)
    for x in range(t0 + 6, t0 + 114, 2):
        cv.rect(gx(x), gy(by0 + 4), 1, 22, 'red', 0.16)                 # shutter ribs
    for xs in (t0 + 40, t0 + 78):
        cv.rect(gx(xs), gy(by0 + 2), 1, 36, 'red', 0.08)
    cv.rect(gx(t0 + 30), gy(by0 + 19), 52, 8, 'red', 0.22)              # plain panel for the lettering
    cv.text(gx(t0 + 34), gy(by0 + 20), 'FEUERWEHR', SN[2])
    cv.rect(gx(t0 + 4), gy(by0 + 30), 112, 3, 'snow', 0.6)              # white band
    cv.rect(gx(t0 + 4), gy(by0), 112, 1, 'red', 0.34)
    snow_cap(cv, gx(t0 + 4), gy(by0) - 1, 112, 2, seed=258, tone=0.7)
    # the equipment locker directly behind the cab (Gerätekasten of the side task „Eine Decke für Frau Brunner“,
    # hotspot exp_task_blanket): a framed roller shutter -- door gap, horizontal slats, bottom bar + pull handle
    k0, k1, ky0, ky1 = t0 + 79, t0 + 115, by0 + 3, by0 + 27         # x 337..373, y 243..267
    cv.rect(gx(k0), gy(ky0), k1 - k0 + 1, ky1 - ky0 + 1, 'red', 0.06, hgt=0.45)
    cv.rect(gx(k0 + 1), gy(ky0 + 1), k1 - k0 - 1, ky1 - ky0 - 1, 'red', 0.22, hgt=0.55)
    for yy in range(ky0 + 2, ky1 - 3, 2):
        cv.rect(gx(k0 + 1), gy(yy), k1 - k0 - 1, 1, 'red', 0.14)
    cv.rect(gx(k0 + 1), gy(ky1 - 3), k1 - k0 - 1, 2, 'iron', 0.2, hgt=0.65)
    cv.rect(gx((k0 + k1) // 2 - 2), gy(ky1 - 3), 5, 1, 'iron', 0.62, hgt=0.7)
    # turntable + ladder base
    cv.rect(gx(296), gy(230), 34, 10, 'iron', 0.2, hgt=0.7)
    cv.rect(gx(300), gy(226), 22, 5, 'iron', 0.28)
    # pump panel at the rear end: gauges with warm faces, levers
    cv.rect(gx(t0 + 6), gy(by0 + 6), 22, 18, 'iron', 0.18)
    for (cx_, cy_) in ((t0 + 12, by0 + 12), (t0 + 21, by0 + 12)):
        cv.ellipse(gx(cx_), gy(cy_), 3, 3, 'lit', 0.45)
        cv.ink_px(gx(cx_), gy(cy_) - 1, NI[1])
    cv.rect(gx(t0 + 9), gy(by0 + 18), 14, 2, 'iron', 0.34)
    cv.rect(gx(t0 - 2), gy(by0 + 22), 8, 5, 'iron', 0.3)                # outlets
    # hose reel at the very back
    cv.ellipse(gx(t0 + 2), gy(by0 + 10), 7, 9, 'cloth', 0.1)
    cv.ellipse(gx(t0 + 2), gy(by0 + 10), 3, 4, 'iron', 0.24)
    # cab + round bonnet
    c0 = t0 + 116
    cv.poly([(gx(c0), gy(by0 + 40)), (gx(c0), gy(236)), (gx(c0 + 6), gy(230)), (gx(c0 + 34), gy(230)),
             (gx(c0 + 42), gy(250)), (gx(t1), gy(256)), (gx(t1 + 2), gy(268)), (gx(t1), gy(280)),
             (gx(c0), gy(280))], 'red', 0.24, hgt=0.6)
    cv.poly([(gx(c0 + 26), gy(233)), (gx(c0 + 33), gy(233)), (gx(c0 + 40), gy(249)), (gx(c0 + 26), gy(249))],
            'glass', 0.08)
    cv.rect(gx(c0 + 6), gy(234), 17, 14, 'glass', 0.08)
    cv.rect(gx(c0 + 4), gy(232), 1, 44, 'red', 0.1)
    for k in range(6):
        cv.px(gx(c0 + 9 + k), gy(246 - 2 * k), 'glass', 0.22)
    _arms_small(cv, gx(c0 + 14), gy(254))
    cv.rect(gx(c0 + 44), gy(256), 8, 1, 'red', 0.34)
    for k in range(5):                                                   # grille
        cv.rect(gx(t1 - 8 + k * 2), gy(260), 1, 12, 'iron', 0.34)
    cv.ellipse(gx(t1 - 1), gy(262), 2.5, 2.5, 'lit', 0.9)                 # headlight
    cv.rect(gx(t1 - 6), gy(276), 10, 3, 'iron', 0.42)                     # bumper
    cv.rect(gx(t0 - 4), gy(276), 8, 3, 'iron', 0.36)
    snow_cap(cv, gx(c0 + 6), gy(229), 28, 2, seed=374, tone=0.72)
    cv.rect(gx(c0 + 12), gy(226), 6, 3, 'iron', 0.2)                      # beacon base (decal on top)
    # running board, mudguards, wheels
    cv.rect(gx(t0 + 2), gy(280), t1 - t0 - 2, 3, 'iron', 0.16)
    for (wx, r) in ((t0 + 34, 10), (t0 + 58, 10), (t1 - 26, 10)):
        cv.ellipse(gx(wx), gy(gnd - r), r, r, 'iron', 0.05, hgt=0.6)
        cv.ellipse(gx(wx), gy(gnd - r), r - 4, r - 4, 'iron', 0.2)
        cv.ellipse(gx(wx), gy(gnd - r), 2, 2, 'iron', 0.42)
        for a in range(0, 360, 60):
            cv.px(gx(wx + (r - 6) * math.cos(math.radians(a))), gy(gnd - r + (r - 6) * math.sin(math.radians(a))),
                  'iron', 0.34)
        cv.poly([(gx(wx - r - 2), gy(gnd - r)), (gx(wx - r + 2), gy(gnd - 2 * r - 2)), (gx(wx + r - 2), gy(gnd - 2 * r - 2)),
                 (gx(wx + r + 2), gy(gnd - r)), (gx(wx + r), gy(gnd - r)), (gx(wx - r), gy(gnd - r))], 'red', 0.18)
    L = resolve(cv, lights)
    beacon = [c0 + 15, 225]
    return L, {'origin': [X0, Y0], 'beacon': beacon, 'ladder_top': [lx1, ly1], 'pump': [t0 + 16, by0 + 12],
               'headlight': [t1 - 1, 262]}


def _arms_small(cv: Canvas, x, y):
    cv.poly([(x - 5, y), (x + 5, y), (x + 5, y + 7), (x, y + 10), (x - 5, y + 7)], 'snow', 0.62)
    cv.poly([(x - 4, y + 1), (x + 4, y + 1), (x + 4, y + 6), (x, y + 9), (x - 4, y + 6)], 'red', 0.3)
    cv.ink_rect(x - 3, y + 4, 7, 1, SN[3])
    for k in (-2, 0, 2):
        cv.ink_px(x + k, y + 5, SN[3])


def _car(lights, kind):
    """Black delegation limousine facing left (toward the fire).  kind 'reich' (rounded 1950s saloon) |
    'ussr' (longer, squarer, more chrome).  Returns (Layer, Layer_hist, info)."""
    spec = CAR_REICH if kind == 'reich' else CAR_USSR
    x0, x1 = spec['x0'], spec['x1']
    X0, Y0, W, H = x0 - 6, 236, x1 - x0 + 12, 60
    cv = _prop_canvas(X0, Y0, W, H, 'car_' + kind)
    gx = lambda x: x - X0
    gy = lambda y: y - Y0
    gnd = 293
    L_ = x1 - x0
    if kind == 'reich':
        prof = [(0, 278), (2, 268), (10, 264), (30, 262), (40, 252), (48, 248), (78, 248), (92, 256), (112, 262),
                (L_, 268), (L_, 280), (0, 282)]
        win = [(44, 253), (50, 250), (76, 250), (86, 257), (44, 257)]
        wheels = (22, 92)
    else:
        prof = [(0, 276), (1, 266), (6, 263), (36, 262), (44, 251), (52, 248), (92, 248), (104, 257), (124, 261),
                (L_, 264), (L_, 280), (0, 282)]
        win = [(48, 253), (54, 250), (90, 250), (99, 257), (48, 257)]
        wheels = (24, 104)
    cv.poly([(gx(x0 + a), gy(b)) for (a, b) in prof], 'iron', 0.08, hgt=0.6)
    cv.poly([(gx(x0 + a), gy(b)) for (a, b) in win], 'glass', 0.1)
    pil = x0 + (win[0][0] + win[2][0]) // 2
    cv.rect(gx(pil), gy(250), 2, 7, 'iron', 0.06)
    for k in range(5):
        cv.px(gx(x0 + win[0][0] + 6 + k * 2), gy(256 - k), 'glass', 0.26)
    cv.rect(gx(x0 + 4), gy(268), L_ - 8, 1, 'iron', 0.42 if kind == 'ussr' else 0.34)     # chrome strip
    cv.rect(gx(x0 + 1), gy(276), 6, 3, 'iron', 0.44)                                    # bumpers
    cv.rect(gx(x1 - 5), gy(276), 6, 3, 'iron', 0.4)
    if kind == 'ussr':
        for k in range(4):
            cv.rect(gx(x0 + 1), gy(266 + k * 2), 2, 1, 'iron', 0.46)                    # grille bars
    cv.rect(gx(x0 + 2), gy(268), 3, 2, 'lit', 0.5)                                       # sidelight
    cv.rect(gx(x1 - 2), gy(268), 2, 2, 'flame', 0.05)                                    # tail light
    # roof and bonnet catch the cold sky (+ thin snow), doors
    for (a, b) in zip(prof[:-3], prof[1:-2]):
        cv.line(gx(x0 + a[0]), gy(a[1]), gx(x0 + b[0]), gy(b[1]), 'iron', 0.3)
    cv.rect(gx(x0 + prof[5][0] + 2), gy(247), prof[6][0] - prof[5][0] - 4, 1, 'snow', 0.55)
    for dx in (win[0][0] + 2, pil - x0 + 3):
        cv.rect(gx(x0 + dx), gy(258), 1, 18, 'iron', 0.03)
    for wx in wheels:
        cv.ellipse(gx(x0 + wx), gy(gnd - 7), 7.5, 7.5, 'iron', 0.04, hgt=0.6)
        cv.ellipse(gx(x0 + wx), gy(gnd - 7), 4, 4, 'iron', 0.34)
        cv.ellipse(gx(x0 + wx), gy(gnd - 7), 1.5, 1.5, 'iron', 0.12)
    L = resolve(cv, lights)
    Lh = K.sub_layer(L, 0, 0, L.w, L.h)
    staff = (gx(x0 + 6), gy(265))
    _pennant(L, staff, kind, hist=False)
    _pennant(Lh, staff, kind, hist=True)
    return L, Lh, {'origin': [X0, Y0], 'pennant': [X0 + staff[0], Y0 + staff[1]]}


def _pennant(L: Layer, staff, kind, hist):
    """Fender pennant on a short chrome staff.  ussr: neutral red with a fictional gear-and-wheat badge,
    hist: star + hammer and sickle; reich: neutral grey with the Reichssiegel (white pillar in a black
    disc), hist: the historical red pennant with the white disc and the hooked cross (Symbols.pick)."""
    sx, sy = staff
    for k in range(12):
        L.px(sx, sy - k, IR[4], 0.7)
    L.px(sx, sy - 12, SN[3])
    fx, fy = sx + 1, sy - 12
    w, h = 9, 6
    if kind == 'ussr':
        base, dark, hi = RD[2], RD[1], RD[3]
    else:
        base, dark, hi = (RD[2], RD[1], RD[3]) if hist else (SL[4], SL[3], SL[5])
    for x in range(w):
        hh = h - (x * 3) // w
        for y in range(hh):
            c = dark if x == w - 1 or y == hh - 1 else base
            L.px(fx + x, fy + y + x // 4, c, 0.62)
        L.px(fx + x, fy + x // 4, hi, 0.62)
    cx, cy = fx + 2, fy + 2
    if kind == 'ussr':
        if hist:
            L.px(cx, cy - 1, LA[3]); L.px(cx + 1, cy, LA[3]); L.px(cx, cy + 1, LA[3])
            L.px(cx + 2, cy + 1, LA[3]); L.px(cx - 1, cy + 1, LA[3])
        else:
            for (dx, dy) in ((0, -1), (1, -1), (-1, 0), (2, 0), (0, 1), (1, 1)):
                L.px(cx + dx, cy + dy, LA[3])
    else:
        if hist:
            L.px(cx, cy, SN[4]); L.px(cx + 1, cy, SN[4]); L.px(cx, cy + 1, SN[4]); L.px(cx + 1, cy + 1, SN[4])
            L.px(cx, cy, NI[0]); L.px(cx + 1, cy + 1, NI[0])
        else:
            L.px(cx, cy, NI[0]); L.px(cx + 1, cy, NI[0]); L.px(cx, cy + 1, NI[0]); L.px(cx + 1, cy + 1, NI[0])
            L.px(cx, cy, SN[4]); L.px(cx, cy + 1, SN[4])


def make_bench_file(lights):
    """The bench at x 760 (story hotspot 'bench'): the file burst open on the seat, sheets in the snow."""
    X0, Y0 = BENCH['x0'] - 4, 0
    W, H = BENCH['x1'] - BENCH['x0'] + 10, 300
    cv = _prop_canvas(X0, Y0, W, H, 'bench_file')             # world rows (cropped when saved)
    _bench(cv, BENCH['x0'] - X0, snowed=False)
    gx = lambda x: x - X0
    gy = lambda y: y - Y0
    snow_cap(cv, gx(BENCH['x0'] - 1), gy(267), 14, 2, seed=11, tone=0.74)          # snow left on the ends
    snow_cap(cv, gx(BENCH['x1'] - 12), gy(267), 13, 2, seed=12, tone=0.74)
    # the file: grey cardboard covers burst open, two fans of sheets (Cyrillic | Latin typing as dots)
    cv.poly([(gx(740), gy(281)), (gx(757), gy(278)), (gx(759), gy(281)), (gx(742), gy(283))], 'wood', 0.34)
    cv.poly([(gx(763), gy(281)), (gx(780), gy(279)), (gx(781), gy(282)), (gx(764), gy(283))], 'wood', 0.34)
    rng = np.random.default_rng(951)
    for k in range(6):                                                                 # Russian half (left)
        x, y = 741 + k * 2, 277 - (k % 3)
        cv.rect(gx(x), gy(y), 10, 3, 'stone', 0.66)
        for q in range(1, 9, 2):
            cv.px(gx(x + q), gy(y + 1), 'stone', 0.34)
    for k in range(5):                                                                 # German half (right)
        x, y = 764 + k * 3, 278 - (k % 2)
        cv.rect(gx(x), gy(y), 9, 3, 'stone', 0.68)
        for q in range(1, 8, 3):
            cv.rect(gx(x + q), gy(y + 1), 2, 1, 'stone', 0.36)
    cv.rect(gx(759), gy(280), 4, 2, 'red', 0.32)                                       # the red C-17 tag
    cv.line(gx(760), gy(282), gx(766), gy(292), 'red', 0.24)                           # its string, hanging
    for (x, y, w_) in ((744, 292, 7), (770, 293, 8), (782, 290, 6), (752, 295, 5)):    # sheets in the snow
        cv.rect(gx(x), gy(y), w_, 2, 'stone', 0.62)
        cv.px(gx(x + 2), gy(y), 'stone', 0.34)
    for _ in range(14):                                                                 # soot smudges
        cv.px(gx(744 + rng.integers(0, 36)), gy(277 + rng.integers(0, 6)), 'stone', 0.04)
    L = resolve(cv, lights)
    return L, {'origin': [X0, Y0]}


def make_trestle(lights):
    """The commission guard's striped trestle barrier (a prop: the onlookers stand behind it)."""
    t0, t1 = TRESTLE
    X0, Y0 = t0 - 4, 0
    cv = _prop_canvas(X0, Y0, t1 - t0 + 8, 300, 'trestle')
    gx = lambda x: x - X0
    for lx_ in (t0 + 2, t1 - 3):
        cv.line(gx(lx_ - 3), 292, gx(lx_), 276, 'wood', 0.2)
        cv.line(gx(lx_ + 3), 292, gx(lx_), 276, 'wood', 0.16)
    for k in range(t1 - t0):
        red = (k // 6) % 2 == 0
        cv.rect(gx(t0 + k), 276, 1, 4, 'red' if red else 'snow', 0.3 if red else 0.66, hgt=0.6)
    snow_cap(cv, gx(t0), 275, t1 - t0, 1, seed=1064)
    return resolve(cv, lights), {'origin': [X0, Y0]}
