"""env_c4p2_cine_kordon -- Kordon-17 wide and from far (LS_C4P2_Clock k2; owner: cine stream, round 11).

The checkpoint on the Line at 23.40 Korridorzeit, seen from the snow outside the outer fence: the night sky with the
pale dome the floodlights raise in the haze, the forest in two bands (the far one blue in the cold air, the near one
black, single firs taller at the clearing's edges), the plain in drifts; the compound in its pools of light -- three
floodlight masts with their lamp banks, two wooden watch towers (a guard in the right cabin), the sentry hut at the
gate with its stovepipe and the lowered boom, a sentry beside it, the long low building on the Line (the German
hall's taller west end with its gable, the long hall, Tür Ost at the east end under its lamp, chimneys, snow on the
roofs), the track of the Line and the siding with wagon C-17/45, its signal, the lorry under its tarpaulin, drums
and sleepers; the inner fence with its wire and coils, the raked control strip, the patrol road; in front the road
to the gate with its telegraph poles walking towards the camera, the outer fence's posts close by, dead stalks in
the drifts.  Restrained: no faces, no weapons shown, no sweeping searchlights.  The anchors (HALL, DOOR_E, WAGON,
FENCE_Y, the witness's place at the fence) are env_c4p2_cine_clock's; people that move are sprites of the runtime.
Painted flat (env_c4p2_cine_flat), original, deterministic.
"""
from __future__ import annotations

import math

import numpy as np

import env_c4p2_cine_flat as FL
import env_c4p2_cine_kit as K

SNOW = '#c8d4e8'
DARK = '#0a0c12'
MASTS = (160, 300, 520)                   # floodlight masts (x); their lamp banks at y 146..152
LAMP_Y = 150
TOWERS = (206, 590)
HUT = (132, 150, 212, 230)                # the sentry hut at the gate (x0, x1, roof, ground)
SMOKES = ((141, 205), (306, 180), (414, 184))     # stovepipe / chimney mouths (sentry hut, hall west, hall east)
PATROL = (164, 236, 233, 5.4, 12.0)       # the two guards on the patrol road: from x, to x, feet y, start, px/s


def _xy(F):
    return F.xx.astype(np.int64), F.yy.astype(np.int64)


def _fir(F, x, base, h, col, snow=None, seed=0):
    """A spruce silhouette: stacked tiers narrowing to the tip, snow lying on the tiers' tops."""
    tiers = max(3, int(h / 5))
    m = np.zeros(F.a.shape, bool)
    for t in range(tiers):
        u = t / tiers
        y0 = base - h + u * h
        hw = 1.0 + (h * 0.32) * (u + 1.0 / tiers)
        m |= F.poly([(x - hw, y0 + h / tiers + 1), (x + hw, y0 + h / tiers + 1), (x + 0.5, y0)])
    m |= F.box(x, base - 2, x + 1, base)
    F.fill(m, col)
    if snow:
        F.fill(m & FL.edge(m, 't') & (K.hash2(F.xx.astype(np.int64), F.yy.astype(np.int64), seed) > 0.35), snow)
    return m


def _tower(F, tx, guard=False):
    """A wooden watch tower: four legs braced, the ladder, the cabin with its windows and railing, the roof under
    snow, the unlit searchlight on the roof's edge."""
    xx, yy = _xy(F)
    legs = F.line([(tx - 7, 232), (tx - 3, 160)], 0.6) | F.line([(tx + 7, 232), (tx + 3, 160)], 0.6) \
        | F.line([(tx - 3, 232), (tx - 1, 160)], 0.5) | F.line([(tx + 3, 232), (tx + 1, 160)], 0.5)
    for y in (176, 196, 216):
        legs |= F.line([(tx - 6, y + 18), (tx + 6, y)], 0.4) | F.line([(tx + 6, y + 18), (tx - 6, y)], 0.4)
        legs |= F.box(tx - 6, y, tx + 7, y + 1)
    F.fill(legs, '#14161e')
    for y in range(166, 232, 4):
        F.fill(F.box(tx + 9, y, tx + 12, y + 1), '#1c1e28')
    F.fill(F.box(tx + 9, 166, tx + 10, 232) | F.box(tx + 11, 166, tx + 12, 232), '#1c1e28')
    cab = F.box(tx - 10, 148, tx + 11, 162)
    F.fill(cab, '#1a1e2a')
    F.fill(F.box(tx - 8, 151, tx + 9, 157), '#2e3446')
    F.fill(F.box(tx - 8, 151, tx + 9, 157) & (np.mod(xx - tx, 6) == 0), '#1a1e2a')
    if guard:                                                        # a guard's head and shoulders in the window
        F.fill(F.ell(tx + 2, 153.5, 1.6, 1.8) | F.box(tx, 155, tx + 5, 157), '#0c0e14')
        F.fill(F.box(tx, 151, tx + 4, 152), '#0c0e14')
    F.fill(F.box(tx - 12, 161, tx + 13, 163), '#22262e')
    F.fill(F.box(tx - 12, 160, tx + 13, 161), SNOW)
    roof = F.poly([(tx - 14, 148), (tx + 15, 148), (tx + 9, 141), (tx - 8, 141)])
    F.fill(roof, '#1e222c')
    F.fill(F.poly([(tx - 14, 147), (tx + 15, 147), (tx + 9, 140), (tx - 8, 140)]) & ~F.box(0, 146, 9999, 9999)
           & FL.edge(roof | F.box(tx - 8, 140, tx + 9, 142), 't'), SNOW)
    F.fill(F.box(tx - 8, 139, tx + 9, 141), SNOW)
    F.fill(F.box(tx + 10, 136, tx + 15, 140), '#22262e')                  # the searchlight, off
    F.fill(F.box(tx + 14, 137, tx + 16, 139), '#5a6070')


def _mast(F, mx):
    """A floodlight mast: lattice, the bank of four lamps on its crossarm (the beams are a glow sprite)."""
    xx, yy = _xy(F)
    lat = F.box(mx - 1, 152, mx + 2, 232)
    F.fill(lat, '#0e1018')
    for y in range(156, 230, 5):
        F.fill(F.line([(mx - 1, y), (mx + 2, y + 5)], 0.3), '#1c2030')
    F.fill(F.box(mx - 7, 150, mx + 8, 152), '#1c2030')
    for k in range(4):
        lx = mx - 6 + k * 4
        F.fill(F.box(lx, 146, lx + 3, 150), '#fff2c8')
        F.fill(F.box(lx, 146, lx + 3, 147), '#ffffff')
    F.fill(F.box(mx - 7, 145, mx + 8, 146), SNOW)


def k2_plate(hall, door_e, wagon, fence_y, horizon=178):
    """(640 x 360, opaque) -- see the module docstring."""
    F = FL.Flat(bg='#020306')
    xx, yy = _xy(F)
    x0h, x1h, yr, yg = hall
    # the sky: stepped night, faint strata lit from below, the floodlights' dome in the haze, few stars
    sky = F.box(0, 0, 640, horizon)
    F.grad(sky, 0, horizon, '#020306', '#161e30', steps=7)
    for k in range(70):
        sx, sy = int(K.hash2(k, 1, 301) * 640), int(K.hash2(k, 2, 301) * (horizon - 70))
        F.fill(F.box(sx, sy, sx + 1, sy + 1), '#c8d0e0' if K.hash2(k, 3, 301) > 0.7 else '#5a6478')
    for k, (y0, amp) in enumerate(((118, 4.0), (134, 3.0))):
        band = (np.abs(yy - (y0 + amp * np.sin(xx * 0.02 + k * 2.0))) < 3 + k) & sky
        F.fill(band & (K.hash2(np.floor_divide(xx, 30), k, 311) > 0.25), ('#0c1120', '#101626')[k])
        F.fill(band & FL.edge(band, 'b') & (K.hash2(np.floor_divide(xx, 30), k, 311) > 0.25), '#1e2434')
    # round 11b: the low cloud deck over the clearing (the top third): ragged banks hiding the stars, their
    # undersides lit by the compound's lights near the masts
    cl = K.noise(640, 360, 34, 331, octaves=3)
    cl = (cl - cl.min()) / max(1e-6, float(cl.max() - cl.min()))
    dens = cl * 0.75 + np.clip(1.0 - np.abs(yy - 84) / 34.0, 0, 1) * 0.45
    deck = sky & (dens > 0.78)
    F.fill(deck, '#0a0e1a')
    F.fill(sky & (dens > 0.9), '#0c1120')
    near = np.zeros((360, 640), np.float32)
    for mx in MASTS:
        near = np.maximum(near, np.clip(1.0 - np.abs(xx - mx) / 130.0, 0, 1))
    und = deck & ~FL.shift(deck, 0, -4)
    chk = ((xx + yy) & 1) == 0
    F.fill(und & (near > 0.1) & (chk | ~FL.shift(deck, 0, -2)), '#141824')
    F.fill(und & (near > 0.45) & ~FL.shift(deck, 0, -2), '#1e202a')
    F.fill(und & (near > 0.7) & FL.edge(deck, 'b') & chk, '#2a2a30')
    F.pool(sky, 370, horizon + 4, 250, 44, steps=((1.0, 1.1), (0.6, 1.22), (0.32, 1.36)), col='#d8c890')
    for mx in MASTS:                                    # the floodlights' haze rising from each bank into the cold air
        F.pool(sky, mx + 1, LAMP_Y, 24, 104, steps=((1.0, 1.08), (0.6, 1.18), (0.3, 1.32)), col='#d8c890')
    # the forest: a far blue band, a near black band, single firs at the clearing's edges
    farm = np.zeros(F.a.shape, bool)
    for x in range(0, 640, 3):
        h_ = 7 + int(6 * abs(math.sin(x * 0.031)) + 5 * K.hash2(x // 3, 1, 303))
        farm |= F.poly([(x - 2, horizon - 2), (x + 3.5, horizon - 2), (x + 0.75, horizon - 2 - h_)])
    farm |= F.box(0, horizon - 4, 640, horizon)
    F.fill(farm, '#141a28')
    F.fill(farm & FL.edge(farm, 't') & (K.hash2(xx, yy, 302) > 0.5), '#2a3246')
    for x in range(0, 640, 5):
        if 150 < x < 600 and K.hash2(x, 3, 304) > 0.25:
            continue
        h_ = 9 + int(12 * K.hash2(x, 4, 304)) + (8 if (x < 120 or x > 600) else 0)
        _fir(F, x + 2, horizon + 1, h_, '#05070c', snow='#3a4458', seed=305 + x)
    F.fill(F.box(0, horizon - 1, 640, horizon + 1), '#06080e')
    # the plain in drifts
    bands = ((horizon, '#2a3448'), (190, '#323e54'), (204, '#3c4a62'), (226, '#46566e'), (256, '#50627e'),
             (290, '#5a6e8c'))
    for (y0, c) in bands:
        F.fill(F.box(0, y0, 640, 360) & ~F.box(0, 0, 640, y0 - 0), c)
    for k in range(9):
        y0_ = 252 + k * 9 + (k * k) % 5
        rid = np.abs(yy - (y0_ + 3 * np.sin(xx * 0.025 + k * 1.3))) < 0.6
        F.fill(rid & (K.hash2(np.floor_divide(xx, 50), k, 306) > 0.25), '#7c8caa')
        F.fill((np.abs(yy - 1 - (y0_ + 3 * np.sin(xx * 0.025 + k * 1.3))) < 0.6)
               & (K.hash2(np.floor_divide(xx, 50), k, 306) > 0.25), '#3e4c64')
    for k in range(16):                                                      # bushes in the drifts
        bx = int(K.hash2(k, 1, 312) * 640)
        by = 254 + int(K.hash2(k, 2, 312) * 12)
        if 90 < bx < 150:
            continue
        bw = 3 + int(K.hash2(k, 3, 312) * 5)
        bm = F.ell(bx, by, bw, 2 + bw * 0.4) & (yy < by + 1)
        F.fill(bm, '#1e2432')
        F.fill(bm & FL.edge(bm, 't') & (K.hash2(xx, yy, 313) > 0.3), '#8a9ab6')
        F.fill(F.box(bx - bw - 1, by + 1, bx + bw + 2, by + 2), '#3e4c64')
    # the road from the gate towards the camera, its ruts, the telegraph poles and their sagging wires
    road = F.poly([(150, 232), (176, 232), (60, 360), (-60, 360)])
    F.fill(road & F.box(0, 232, 640, 360), '#3e4a60')
    for (a, b) in (((158, 232), (-10, 360)), ((168, 232), (34, 360))):
        F.fill(F.line([a, b], 1.0), '#2c364a')
    poles = [(128, 230, 20), (98, 262, 34), (54, 306, 56), (-6, 372, 92)]
    tops = []
    for (px, base, h) in poles:
        w = max(1, int(h / 30))
        F.fill(F.box(px, base - h, px + w + 1, base), '#10141c')
        F.fill(F.box(px - h * 0.16, base - h + 2, px + w + 1 + h * 0.16, base - h + 2 + max(1, w)), '#10141c')
        F.fill(F.box(px, base - h, px + 1, base) & (K.hash2(xx, yy, 307) > 0.5), '#2a3040')
        tops.append((px + w / 2, base - h + 2))
    for (a, b) in zip(tops, tops[1:]):
        for dy in (0, 3):
            pts = [(a[0] + (b[0] - a[0]) * u, a[1] + dy + (b[1] - a[1]) * u + 6 * math.sin(math.pi * u)
                    * (abs(b[0] - a[0]) / 60.0)) for u in np.linspace(0, 1, 12)]
            F.fill(F.line(pts, 0.35), '#1a2030')
    # the compound's ground in the floodlights: pale snow, stepped pools
    comp = F.poly([(150, 226), (626, 226), (640, 236), (640, 252), (120, 252), (140, 232)])
    F.fill(comp, '#6a7a96')
    for mx in MASTS:
        F.pool(F.box(0, 200, 640, 270), mx, 238, 104, 18, steps=((1.0, 1.12), (0.62, 1.3), (0.32, 1.48)),
               col='#f2e2b0')
    # the track of the Line and the siding
    F.fill(F.box(0, 230, 640, 231), '#2a2e3a')
    F.fill(F.box(0, 232, 640, 233), '#22262e')
    F.fill(F.box(0, 230, 640, 233) & (np.mod(xx, 4) == 0), '#1a1c24')
    wx0, wx1, wy0, wy1 = wagon
    F.fill(F.box(wx0 - 40, wy1, 630, wy1 + 1), '#2a2e3a')
    F.fill(F.box(wx0 - 40, wy1 + 1, 630, wy1 + 2) & (np.mod(xx, 3) == 0), '#1a1c24')
    F.fill(F.box(628, wy1 - 4, 632, wy1 + 1), '#6a2a1a')                     # the buffer stop
    F.fill(F.box(606, 198, 607, 230), '#14161e')                              # the signal, at danger
    F.fill(F.box(603, 196, 610, 205), '#14161e')
    F.fill(F.ell(606.5, 199.5, 1.5, 1.5), '#ff4a30')
    # the hall on the Line: the German hall's west end with its gable, the long hall, Tür Ost and its lamp
    west = F.box(x0h - 30, yr - 12, x0h + 42, yg)
    F.fill(west, '#22283a')
    F.fill(west & (np.mod(xx, 3) == 0), '#1e2434')
    gab = F.poly([(x0h - 34, yr - 12), (x0h + 46, yr - 12), (x0h + 6, yr - 26)])
    F.fill(gab, '#262c40')
    F.fill(gab & FL.edge(gab, 't', 2), SNOW)
    F.fill(F.ell(x0h + 6, yr - 17, 3, 3), '#e8d8a0')                         # the round gable window, lit
    hb = F.box(x0h, yr, x1h, yg)
    F.fill(hb, '#1c2030')
    F.fill(hb & (np.mod(xx, 6) == 0), '#181c2a')
    F.fill(F.box(x0h, yr - 3, x1h + 2, yr + 1), '#22283a')
    F.fill(F.box(x0h, yr - 4, x1h + 2, yr - 2), SNOW)
    F.fill(F.box(x0h - 30, yr - 13, x0h + 42, yr - 11), SNOW)
    for wx in range(x0h + 54, x1h - 24, 20):
        F.fill(F.box(wx, yr + 9, wx + 7, yr + 15), '#d8c070')
        F.fill(F.box(wx + 3, yr + 9, wx + 4, yr + 15), '#6a5a30')
        F.fill(F.box(wx - 1, yr + 15, wx + 8, yr + 16), SNOW)
    for wx in (x0h - 22, x0h - 4, x0h + 14, x0h + 30):
        F.fill(F.box(wx, yr - 4, wx + 7, yr + 4), '#e8d8a0')
        F.fill(F.box(wx, yr, wx + 7, yr + 1), '#7a6a3a')
    for (cx, top) in ((SMOKES[1][0], SMOKES[1][1]), (SMOKES[2][0], SMOKES[2][1])):
        F.fill(F.box(cx - 2, top, cx + 3, yr - 2 if cx < x0h + 42 else yr), '#141822')
        F.fill(F.box(cx - 3, top - 1, cx + 4, top + 1), SNOW)
    dx0, dy0, dx1, dy1 = door_e
    F.fill(F.box(dx0 - 2, dy0 - 2, dx1 + 2, dy1), '#2a3042')
    F.fill(F.box(dx0, dy0, dx1, dy1), '#0c0e14')
    F.fill(F.box(dx0 - 4, dy0 - 4, dx1 + 4, dy0 - 3), '#2a3042')
    F.fill(F.box(dx0 - 4, dy0 - 5, dx1 + 4, dy0 - 4), SNOW)
    F.fill(F.box((dx0 + dx1) // 2 - 1, dy0 - 3, (dx0 + dx1) // 2 + 2, dy0 - 1), '#fff2c8')
    F.fill(F.box(x0h - 30, yg, x1h + 4, yg + 3), '#8a98b2')                     # the platform along the hall
    F.fill(F.box(x0h - 30, yg + 3, x1h + 4, yg + 4), '#3a4458')
    F.outline(hb | west, col=DARK, k=0.6)
    for k in range(5):                                                       # drums and a stack of sleepers
        F.fill(F.box(x0h - 52 + k * 4, yg - 6, x0h - 49 + k * 4, yg), ('#3a4a3a', '#2e3c30')[k % 2])
        F.fill(F.box(x0h - 52 + k * 4, yg - 7, x0h - 49 + k * 4, yg - 6), SNOW)
    F.fill(F.box(x0h - 72, yg - 4, x0h - 56, yg), '#2a2018')
    F.fill(F.box(x0h - 72, yg - 2, x0h - 56, yg - 1), '#1a140e')
    F.fill(F.box(x0h - 72, yg - 5, x0h - 56, yg - 4), SNOW)
    # wagon C-17/45 on its siding
    wg = F.box(wx0, wy0, wx1, wy1 - 2)
    F.fill(wg, '#5a2a1c')
    F.fill(wg & (np.mod(xx, 4) == 0), '#4a2216')
    F.fill(F.box(wx0 - 1, wy0 - 2, wx1 + 1, wy0), '#3a1c14')
    F.fill(F.box(wx0 - 1, wy0 - 3, wx1 + 1, wy0 - 1), SNOW)
    F.fill(F.box(wx0 + 24, wy0 + 3, wx0 + 34, wy1 - 3), '#24120c')
    F.fill(F.box(wx0 + 22, wy0 + 2, wx0 + 36, wy0 + 3), '#2a2a30')
    F.fill(F.text('C-17', wx0 + 4, wy0 + 4, 's') & wg, '#e8e0d0')
    for whx in (wx0 + 7, wx0 + 13, wx1 - 13, wx1 - 7):
        F.fill(F.ell(whx, wy1 - 1, 2.4, 2.4), DARK)
    F.fill(F.box(wx0 + 4, wy1 - 2, wx1 - 4, wy1 - 1), '#1a1010')
    F.outline(wg, col='#140806', k=0.6)
    # the lorry under its tarpaulin
    tarp = F.box(564, 212, 594, 226)
    F.fill(tarp, '#3a4230')
    F.fill(F.ell(579, 213, 15, 3) & (yy < 213), '#3a4230')
    F.fill(F.box(564, 210, 594, 212) | (F.ell(579, 211, 15, 3) & (yy < 211)), SNOW)
    F.fill(tarp & (np.mod(xx, 7) == 0), '#2e3626')
    cab = F.poly([(595, 226), (595, 214), (603, 214), (607, 219), (607, 226)])
    F.fill(cab, '#2a3024')
    F.fill(F.poly([(597, 219), (597, 216), (602, 216), (605, 219)]), '#5a6a7a')
    F.fill(F.box(595, 213, 604, 214), SNOW)
    F.fill(F.box(562, 226, 608, 228), '#14161a')
    for whx in (570, 586, 601):
        F.fill(F.ell(whx, 228, 3, 3), '#0a0a0e')
    # the sentry hut and the lowered boom, the sentry beside it
    h0, h1, hr, hg = HUT
    hut = F.box(h0, hr, h1, hg)
    F.fill(hut, '#2a2e3a')
    F.fill(hut & (np.mod(yy, 3) == 0), '#242834')
    F.fill(F.box(h0 + 4, hr + 5, h0 + 11, hr + 11), '#e8c878')
    F.fill(F.box(h0 + 7, hr + 5, h0 + 8, hr + 11), '#6a5a30')
    F.fill(F.box(h0 - 2, hr - 3, h1 + 2, hr), '#1e222c')
    F.fill(F.box(h0 - 2, hr - 4, h1 + 2, hr - 2), SNOW)
    F.fill(F.box(SMOKES[0][0] - 1, SMOKES[0][1], SMOKES[0][0] + 1, hr - 3), '#14161c')
    F.outline(hut, col=DARK, k=0.6)
    F.fill(F.box(h1 + 2, 220, h1 + 5, 230), '#1a1c24')
    boom = F.box(h1 + 4, 222, 204, 224)
    F.fill(boom, '#e8e0d4')
    F.fill(boom & (np.mod(xx, 10) < 5), '#b8241a')
    F.fill(F.box(201, 222, 203, 230), '#1a1c24')
    import env_c4p2_cine_figs as FG                                           # the sentry (figure stream)
    F.paste(FG.far_figure('stand', h=12, coat='#242a30', frames=1, face=-1, light=('r', '#f2e2b0'), hat='ushanka',
                          seed=5), h1 + 5, 231 - 12)
    # masts and towers
    for mx in MASTS:
        _mast(F, mx)
    for k, tx in enumerate(TOWERS):
        _tower(F, tx, guard=(k == 1))
    # the inner fence: posts with outriggers, wire, snow on the wire, coils on top; the raked control strip
    strip = F.box(0, 240, 640, 251)
    F.fill(strip, '#4e5c76')
    for k in range(0, 640, 5):
        F.fill(F.box(k, 242 + (k % 4), k + 3, 243 + (k % 4)), '#3e4a62')
    F.fill(F.box(0, 240, 640, 241), '#36425a')
    for px_ in range(4, 640, 14):
        F.fill(F.box(px_, fence_y - 13, px_ + 1, fence_y), DARK)
        F.fill(F.line([(px_ + 0.5, fence_y - 13), (px_ + 3, fence_y - 15)], 0.3), DARK)
        F.fill(F.box(px_ - 1, fence_y - 1, px_ + 2, fence_y + 1), SNOW)
    for wy in (fence_y - 11, fence_y - 8, fence_y - 5, fence_y - 2):
        F.fill(F.box(0, wy, 640, wy + 1) & (np.mod(xx, 3) != 0), '#141822')
        F.fill(F.box(0, wy - 1, 640, wy) & (K.hash2(xx, wy, 308) > 0.86), '#8a98b2')
    coil = (np.abs(np.hypot(np.mod(xx, 6) - 3.0, yy - (fence_y - 15.5)) - 2.2) < 0.55) & F.box(0, fence_y - 19, 640, fence_y - 12)
    F.fill(coil, '#1a1e28')
    # round 11b: the near drifts, wind-carved crests catching the light, their lee sides in shade
    for k, (yc, amp, fq) in enumerate(((296, 4.0, 0.018), (311, 5.0, 0.013), (328, 6.0, 0.01))):
        crest = yc + amp * np.sin(xx * fq + k * 2.1) + 2.0 * np.sin(xx * 0.051 + k)
        F.mul((yy > crest) & (yy < crest + 6), 0.86)
        F.mul((yy >= crest + 6) & (yy < crest + 9) & (((xx + yy) & 1) == 0), 0.9)
        F.fill((np.abs(yy - crest) < 0.7) & (K.hash2(np.floor_divide(xx, 40), k, 341) > 0.2), '#8a9ab8')
    # the near field: the outer fence close by, its wire with snow, the sign, dead stalks in the drifts
    for px_ in range(-20, 660, 46):
        post = F.box(px_, 266, px_ + 3, 316)
        F.fill(post, '#1a1e28')
        F.fill(F.box(px_, 266, px_ + 1, 316), '#2e3446')
        F.fill(F.box(px_ - 1, 264, px_ + 4, 266), SNOW)
        F.fill(F.ell(px_ + 1.5, 314, 6, 3), '#7c8caa')
    for wy in (274, 284, 294, 304):
        F.fill(F.box(0, wy, 640, wy + 1) & (np.mod(xx + wy, 4) != 0), '#22283a')
        F.fill(F.box(0, wy - 1, 640, wy) & (K.hash2(xx, wy, 309) > 0.8), '#a8b6cc')
        F.fill(F.box(0, wy, 640, wy + 2) & (np.mod(xx + wy, 9) == 0), '#22283a')            # the barbs
    for k in range(0, 640, 46):
        F.fill(F.line([(k + 2, 276), (k + 44, 302)], 0.4) | F.line([(k + 44, 276), (k + 2, 302)], 0.4), '#1c2232')
    sg = F.box(96, 248, 140, 262)
    F.fill(sg, '#c8c0a8')
    F.fill(F.text('КОРДОН-17', 99, 252, 's') & sg, '#3a1410')
    F.fill(F.box(116, 262, 119, 282), '#1a1e28')
    F.fill(F.box(95, 246, 141, 248), SNOW)
    F.outline(sg, col='#2a2a24', k=0.6)
    for k in range(60):
        sx = int(K.hash2(k, 1, 310) * 640)
        sy = 300 + int(K.hash2(k, 2, 310) * 16)
        ln = 4 + int(K.hash2(k, 3, 310) * 9)
        lean = (K.hash2(k, 4, 310) - 0.5) * 4
        F.fill(F.line([(sx, sy), (sx + lean, sy - ln)], 0.35), '#2a2a30')
    _near_pole(F)
    chk = ((xx + yy) & 1) == 0                          # the near snow lies outside the light: darker towards us
    F.mul((yy > 290) | ((yy > 286) & chk), 0.93)
    F.mul((yy > 304) | ((yy > 300) & chk), 0.93)
    return F.opaque()


def _near_pole(F):
    """Round 11b: the camp's power line comes in over the plain -- a wooden pole close to the camera at the right
    edge (crossarm, insulators, snow on the arm and the cap, climbing pins, the compound's light on its rims), its
    wires sweeping down to a pole on the strip outside the inner fence and on to the hall's east end."""
    xx, yy = _xy(F)
    p = F.box(618, 56, 625, 360)
    F.fill(p, '#12141c')
    F.fill(p & (np.mod(xx * 7 + np.floor_divide(yy, 9), 5) == 0), '#1a1d26')
    F.fill(F.box(618, 56, 619, 360), '#2e3038')
    F.fill(F.box(624, 56, 625, 360), '#3a3632')
    F.fill(F.box(617, 53, 626, 56), SNOW)
    for k, y in enumerate(range(118, 360, 13)):
        F.fill(F.box(613 if k % 2 == 0 else 625, y, 618 if k % 2 == 0 else 630, y + 1), '#22242c')
    arm = F.box(602, 66, 640, 70)
    F.fill(arm, '#14161e')
    F.fill(F.box(602, 69, 640, 70), '#0a0b10')
    F.fill(F.box(602, 64, 640, 66), SNOW)
    F.fill(F.line([(606, 70), (618, 82)], 0.6) | F.line([(637, 70), (625, 82)], 0.6), '#14161e')    # the braces
    ins = []
    for ix in (606, 613, 633):
        F.fill(F.box(ix - 1, 59, ix + 2, 64), '#7a8292')
        F.fill(F.box(ix - 1, 59, ix + 2, 60), '#b8c0cc')
        F.fill(F.box(ix, 64, ix + 1, 66), '#3a3e48')
        ins.append((ix + 0.5, 60.0))
    mp = F.box(486, 222, 488, 258)                       # the next pole, on the strip
    F.fill(mp, '#10131a')
    F.fill(F.box(482, 224, 493, 225), '#10131a')
    F.fill(F.box(482, 223, 493, 224), SNOW)
    far = [(483.0, 223.0), (487.0, 223.0), (491.0, 223.0)]
    for a, b in zip(ins, far):
        pts = [(a[0] + (b[0] - a[0]) * u, a[1] + (b[1] - a[1]) * u + 10.0 * math.sin(math.pi * u)) for u in np.linspace(0, 1, 28)]
        F.fill(F.line(pts, 0.4), '#0c0e14')
    for b in far[:2]:
        pts = [(b[0] + (470.0 - b[0]) * u, b[1] + (199.0 - b[1]) * u + 1.5 * math.sin(math.pi * u)) for u in np.linspace(0, 1, 8)]
        F.fill(F.line(pts, 0.35), '#0c0e14')


def smoke_sheet():
    """A small far puff for the chimneys and the stovepipe (8 frames, 12 x 16)."""
    return K.puff_sheet(8, 12, 16, ['#3a4252', '#4e586a', '#626e80', '#7a8698'], 321, grow=(0.25, 0.5), thin=0.6,
                        light=(0.5, -0.6), drift=0.2)


def patrol_sheet():
    """The two guards of the patrol (2-frame walk, facing +x, greatcoat and ushanka, the floodlight's rim on their
    backs) -- the figure stream's far figure: (sheet, cell w, cell h)."""
    import env_c4p2_cine_figs as FG
    sh = FG.far_figure('walk', h=13, coat='#2a3036', frames=2, face=1, light=('l', '#f2e2b0'), hat='ushanka', seed=7)
    return sh, sh.shape[1] // 2, sh.shape[0]


def layout(cell=(10, 13)):
    return dict(k2_smokes=[list(s) for s in SMOKES], k2_patrol=list(PATROL), k2_patrol_cell=list(cell))
