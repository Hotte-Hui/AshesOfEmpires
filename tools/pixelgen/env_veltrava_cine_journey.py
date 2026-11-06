"""env_veltrava_cine_journey -- the landscape outside the compartment windows of LS_C3_Trains (round 10).

Owner: cinematics stream (LS_C3_Trains places/motion).  The night plain behind the glass gets a journey instead of
an empty strip: on Konrad's side (west of the Line) farmland with a village under its steeple, a farm road with a
car, a barn; on Alexei's side (east) a village of log houses with carved window frames, a wooden onion-dome church,
a well sweep and a kolkhoz barn; a small station that the saloon car rushes through without a stop; the frozen
river under the truss bridge on the Soviet side.

Art (assets/cinematics/ch3/trains/): ext_mid_de, ext_mid_su (tileable 640 px strips, rows 150..233, scrolled at
the plain's speed; the runtime places them at LAYOUT trains.mid_y0), pass_station (the station strip, rows 76..233),
pass_river + pass_river_obj (AD round 2: the river seen from the bridge in perspective -- a ground image that the
runtime scrolls row by row, every row at the speed of its own depth, so the river valley swings past like a wiper
and slides in from the window edge; upright things on the ice are separate sprites at the depth of their foot).
Night palette = COLD (env_veltrava_cine) + the lamp ramp.
"""
from __future__ import annotations

import math

import numpy as np

import env_veltrava_cine as C
import pg

kit = C.kit
shift = C.shift
LAYOUT = C.LAYOUT.setdefault('trains', {})
W = C.STRIP_W
MID_Y0, MID_H = 150, 84                 # abs rows 150..233
LAYOUT['mid_y0'] = MID_Y0
WARM = ['#22150F', '#4A2D1F', '#6E3F22', '#A8643A', '#D08F55', '#EDB777', '#FCE2B0']
WOOD = ['#0C0A0C', '#1A1214', '#2A1C18', '#3A2820', '#4E3828']
GREENR = ['#0C111C', '#121A1A', '#1E302E', '#2B4541', '#3D5E57']


def ramps():
    return C.ramps(C=C.COLD, L=WARM, O=WOOD, G=GREENR, R=C.V['red'])


def _snow_plain(p, seed, edge_y=188):
    """The snow plain of the old ext_mid: drifts, an old field fence, bushes, birches (tileable)."""
    yy, xx = p.yy, p.xx
    h, w = p.h, p.w
    rng = np.random.default_rng(seed)
    edge = edge_y + (C.wrap_noise(w, 1, 30, seed + 1)[0] * 2.5).astype(int)
    m = yy >= edge[None, :]
    depth = np.clip((yy - edge_y) / 44, 0, 1)
    t = 5.5 - depth * 2.4 + depth ** 2 * 1.3
    drift = C.wrap_noise(w, h, 40, seed + 2, octaves=3)
    crest = np.sin((yy - edge_y) * 0.55 + drift * 9.0)
    t += np.where(crest > 0.86, 0.75, 0.0) - np.where(crest < -0.9, 0.45, 0.0)
    t += (drift - 0.5) * 0.8
    p.put(m, 'C', t)
    fy = 199
    for px_ in range(3, w, 11):
        hgt = 3 + (px_ * 7) % 2
        p.put(p.box(px_, fy - hgt, px_ + 1, fy), 'C', 1.8)
    for px_ in range(w):
        sag = 0.6 * math.sin(math.pi * ((px_ - 3) % 11) / 11)
        p.px(px_, int(round(fy - 3 + sag)), 'C', 2.6)
    for _ in range(40):
        bx = rng.uniform(0, w)
        by = rng.uniform(194, 230)
        s = 0.8 + (by - 192) / 36 * 3.4
        for dx in (-w, 0, w):
            for k in range(int(3 + s * 1.2)):
                cx = bx + dx + rng.uniform(-s * 1.4, s * 1.4)
                cy = by - rng.uniform(0, s * 0.9)
                bm = p.ell(cx, cy, s * rng.uniform(0.5, 0.9), s * rng.uniform(0.4, 0.7))
                p.put(bm & m, 'C', 1.4 + rng.uniform(0, 0.8))
            p.px(int(bx + dx), int(by - s), 'C', 5.6)
    return m


def _birch(p, rng, bx, by, th):
    for dx in (-W, 0, W):
        X = bx + dx
        p.put(p.box(X, by - th, X + 1, by), 'C', 7.0)
        for k in range(2, th, 3):
            p.px(X, by - k, 'C', 2.0)
        for k in range(5):
            a = rng.uniform(-2.4, -0.7)
            ln = rng.uniform(3, 7)
            sy = by - th + rng.uniform(0, th * 0.4)
            p.put(p.line([(X, sy), (X + math.cos(a) * ln, sy + math.sin(a) * ln)], 0.4), 'C', 1.8)


def _house(p, x, base, w, h, rh, lit, wall='C', wall_t=1.6, timber=False, carved=False, rng=None, chimneys=None):
    """A village house at night: dark wall, steep snowy roof, warm windows (some), chimney."""
    for dx in (-W, 0, W):
        X = x + dx
        body = p.box(X, base - h, X + w, base)
        p.put(body, wall, wall_t)
        p.put(body & ~shift(body, 1, 0), wall, wall_t + 0.8)
        if timber:
            for k in range(X + 2, X + w - 1, 4):
                p.put(p.box(k, base - h, k + 1, base), 'O', 1.0)
            p.put(p.box(X, base - h // 2, X + w, base - h // 2 + 1), 'O', 1.0)
        if carved:
            for k in range(base - h + 1, base, 2):
                p.put(p.box(X, k, X + w, k + 1), 'O', 2.2)                       # log courses
        roof = p.poly([(X - 2, base - h + 1), (X + w / 2, base - h - rh), (X + w + 2, base - h + 1)])
        p.put(roof, 'C', 6.2)
        p.put(roof & ~shift(roof, 0, -1), 'C', 8.6)
        p.put(roof & (p.xx < X + w / 2), 'C', 5.0)
        p.put(roof & ~shift(roof, 0, 1), 'C', 2.4)
        nwin = max(1, w // 6)
        for i in range(nwin):
            wx = X + 2 + i * (w - 3) // nwin
            wy = base - h + max(2, h // 3)
            on = lit[i % len(lit)]
            win = p.box(wx, wy, wx + 2, wy + 3)
            p.put(win, 'L' if on else 'C', 4.4 if on else 0.6, emis=on)
            if carved:
                p.put(p.box(wx - 1, wy - 1, wx + 3, wy), 'C', 6.0)                    # the carved frame (nalichnik)
                p.put(p.box(wx - 1, wy + 3, wx + 3, wy + 4), 'C', 5.2)
                p.px(wx + 0.5, wy - 2, 'C', 6.0)
        if chimneys is not None and dx == 0:
            cx = X + int(w * 0.7)
            p.put(p.box(cx, base - h - rh + 2, cx + 2, base - h - rh // 3), 'C', 1.4)
            p.put(p.box(cx, base - h - rh + 1, cx + 2, base - h - rh + 2), 'C', 8.0)
            chimneys.append([cx + 1, base - h - rh + 1])


# =========================================================================== west (Konrad)
def ext_mid_de():
    """Western farmland: the village with its steeple and half-timbered houses, a farm road with a car (runtime
    lamps), a big barn, birches.  Tileable 640 px, rows 150..233."""
    R = ramps()
    p = C.Paint(W, MID_H, R, 'ext_mid_de', 0, MID_Y0)
    yy, xx = p.yy, p.xx
    rng = np.random.default_rng(1601)
    m = _snow_plain(p, 1602)
    # the farm road: a pale track running from the village across the plain
    road = p.line([(330, 196), (400, 203), (480, 210), (560, 216), (640, 221)], 0.9) | \
        p.line([(0, 221), (40, 224)], 0.9)
    p.put(road & m, 'C', 6.4)
    p.put(shift(road, 0, -1) & m & ~road, 'C', 3.2)
    LAYOUT['mid_de_road'] = [338, 196]
    # the village: half-timbered houses round the church
    chims = []
    houses = [(164, 196, 16, 9, 9, [1, 0]), (186, 194, 14, 8, 8, [0, 1]), (206, 197, 18, 10, 10, [1, 1, 0]),
              (276, 196, 16, 9, 9, [0]), (298, 198, 20, 10, 11, [1, 0, 1]), (322, 195, 13, 8, 8, [0, 1])]
    for (x, base, w, h, rh, lit) in houses:
        _house(p, x, base, w, h, rh, lit, wall_t=2.0, timber=True, chimneys=chims)
    # the church: nave + tall slate steeple with its little clock window
    for dx in (-W, 0, W):
        X = 232 + dx
        nave = p.box(X, 184, X + 30, 197)
        p.put(nave, 'C', 2.4)
        p.put(p.poly([(X - 2, 185), (X + 15, 175), (X + 32, 185)]), 'C', 6.0)
        p.put(p.box(X + 4, 187, X + 6, 193) | p.box(X + 12, 187, X + 14, 193) | p.box(X + 20, 187, X + 22, 193),
              'L', 2.4, emis=True)
        tw = p.box(X + 24, 166, X + 32, 197)
        p.put(tw, 'C', 2.0)
        p.put(tw & ~shift(tw, 1, 0), 'C', 3.0)
        sp = p.poly([(X + 23, 167), (X + 28, 150), (X + 33, 167)])
        p.put(sp, 'C', 1.6)
        p.put(sp & (xx > X + 28), 'C', 4.0)
        p.put(p.ell(X + 28, 171, 1.6, 1.6), 'L', 3.6, emis=True)
    _house(p, 470, 205, 34, 12, 12, [0, 0, 1], wall_t=1.4, chimneys=None)               # the barn
    for k in range(4):
        _birch(p, rng, int(rng.uniform(360, 620)), int(rng.uniform(200, 214)), int(rng.uniform(11, 18)))
    for k in range(3):
        _birch(p, rng, int(rng.uniform(20, 140)), int(rng.uniform(200, 214)), int(rng.uniform(11, 18)))
    p.resolve(band=3.0)
    LAYOUT['mid_de_chimneys'] = chims
    return p.L


# =========================================================================== east (Alexei)
def ext_mid_su():
    """Eastern land: log houses with carved frames and smoking chimneys, the wooden onion-dome church, a well
    sweep, the long kolkhoz barn.  Tileable 640 px, rows 150..233."""
    R = ramps()
    p = C.Paint(W, MID_H, R, 'ext_mid_su', 0, MID_Y0)
    yy, xx = p.yy, p.xx
    rng = np.random.default_rng(1611)
    m = _snow_plain(p, 1612)
    chims = []
    houses = [(250, 197, 16, 9, 8, [1, 0]), (272, 195, 14, 8, 7, [1]), (296, 198, 18, 10, 9, [0, 1, 1]),
              (370, 196, 15, 9, 8, [1, 0]), (392, 198, 17, 10, 9, [0, 1]), (418, 195, 14, 8, 7, [1])]
    for (x, base, w, h, rh, lit) in houses:
        _house(p, x, base, w, h, rh, lit, wall='O', wall_t=2.4, carved=True, chimneys=chims)
    # fences between the yards (wattle)
    for dx in (-W, 0, W):
        p.put(p.box(246 + dx, 198, 440 + dx, 199) & ((xx.astype(int) % 2) == 0), 'O', 2.6)
    # the wooden church with its onion dome and the little belfry
    for dx in (-W, 0, W):
        X = 330 + dx
        body = p.box(X, 182, X + 22, 198)
        p.put(body, 'O', 2.6)
        for k in range(183, 198, 2):
            p.put(p.box(X, k, X + 22, k + 1), 'O', 3.2)
        p.put(p.poly([(X - 2, 183), (X + 11, 174), (X + 24, 183)]), 'C', 6.4)
        drum = p.box(X + 8, 166, X + 14, 176)
        p.put(drum, 'O', 2.4)
        on = p.ell(X + 11, 163, 5, 4.6) | p.poly([(X + 7, 162), (X + 11, 153), (X + 15, 162)])
        p.put(on, 'G', 3.0)
        p.put(on & (xx > X + 11), 'G', 4.4)
        p.put(on & ~shift(on, 0, -1), 'C', 8.6)
        p.put(p.line([(X + 11, 153), (X + 11, 148)], 0.4) | p.line([(X + 9, 150), (X + 13, 150)], 0.4), 'C', 3.4)
        p.put(p.box(X + 4, 187, X + 6, 192), 'L', 2.0, emis=True)
    # the well sweep (zhuravl): a post and the long tilted pole with its bucket rope
    for dx in (-W, 0, W):
        X = 448 + dx
        p.put(p.box(X, 186, X + 1, 202), 'O', 2.0)
        p.put(p.line([(X - 14, 178), (X + 12, 196)], 0.5), 'O', 2.6)
        p.put(p.line([(X - 14, 178), (X - 14, 194)], 0.3), 'O', 1.6)
        p.put(p.box(X - 4, 198, X + 4, 202), 'O', 2.2)
        p.put(p.box(X - 4, 197, X + 4, 198), 'C', 8.0)
    # the long kolkhoz barn: plank walls, a big double door with its lamp, a lit gable window, the hipped roof
    # deep in snow with its dark eave (AD round 2: it read as a flat brown block against the floodlit strip)
    for dx in (-W, 0, W):
        X = 80 + dx
        b = p.box(X, 194, X + 70, 206)
        p.put(b, 'O', 1.8)
        p.put(b & ((xx.astype(int) % 3) == 0), 'O', 1.2)                                  # the planks
        p.put(b & ~shift(b, 1, 0), 'O', 2.8)
        roof = p.poly([(X - 3, 195), (X + 8, 186), (X + 62, 186), (X + 73, 195)])
        p.put(roof, 'C', 7.2)
        p.put(roof & (xx < X + 8 + (yy - 186) * -1.2 + 2), 'C', 5.4)                      # the west hip in shade
        p.put(roof & ~shift(roof, 0, 1), 'C', 1.0)                                        # the dark eave
        p.put(roof & ~shift(roof, 0, -1), 'C', 9.0)
        door = p.box(X + 44, 198, X + 54, 206)
        p.put(door, 'O', 1.0)
        p.put(p.box(X + 49, 198, X + 50, 206), 'O', 2.6)
        p.put(p.box(X + 48, 196, X + 50, 197), 'L', 4.4, emis=True)                       # the lamp over it
        p.put(p.box(X + 30, 198, X + 33, 201), 'L', 3.0, emis=True)
        hs = p.ell(X + 100, 202, 9, 7) & (yy < 203)
        p.put(hs, 'C', 6.6)
        p.put(hs & (xx < X + 98), 'C', 4.6)
    for k in range(5):
        _birch(p, rng, int(rng.uniform(470, 630)), int(rng.uniform(202, 216)), int(rng.uniform(11, 18)))
    p.resolve(band=3.0)
    LAYOUT['mid_su_chimneys'] = chims
    return p.L


# =========================================================================== the station without a stop
STATION_W = 470


def pass_station():
    """A small German halt rushing past Konrad's window (rows 76..233): the platform with its white edge and
    three lamps, the station house with a lit window and its name board, a canopy, a bench, a parcel cart,
    the signal box at the end.  Transparent above the roofs (the sky shows)."""
    R = ramps()
    w, h, y0 = STATION_W, 158, 76
    p = C.Paint(w, h, R, 'pass_station', 0, y0)
    yy, xx = p.yy, p.xx
    # the station house (behind the platform)
    house = p.box(150, 150, 300, 196)
    p.put(house, 'C', 3.0)
    p.put(house & ((yy.astype(int) % 4) == 0), 'C', 2.4)
    roof = p.poly([(144, 151), (166, 128), (284, 128), (306, 151)])
    p.put(roof, 'C', 6.6)
    p.put(roof & ~shift(roof, 0, -1), 'C', 9.6)
    p.put(roof & ~shift(roof, 0, 1), 'C', 2.4)
    p.put(p.box(196, 118, 204, 132), 'C', 2.4)                                            # chimney
    p.put(p.box(196, 117, 204, 118), 'C', 9.0)
    for wx in (168, 248, 270):
        p.put(p.box(wx, 160, wx + 10, 174), 'C', 1.2)
    p.put(p.box(168, 160, 178, 174), 'L', 4.4, emis=True)                                # the lit office window
    p.put(p.box(172, 160, 173, 174) | p.box(168, 166, 178, 167), 'O', 1.4)
    p.put(p.box(214, 164, 228, 196), 'O', 2.0)                                            # door
    # name board between the windows: dark enamel, cream letters
    board = p.box(182, 137, 268, 151)
    p.put(board, 'G', 1.4)
    p.put(board & ~kit.erode(board, 1), 'C', 7.0)
    txt = C.text('ERLENGRUND', '35')
    th, tw = txt.shape
    yb, xb = 144 - th // 2, int(225 - tw / 2)
    m = np.zeros((h, w), bool)
    m[yb - y0:yb - y0 + th, xb:xb + tw] = txt[:min(th, h - (yb - y0)), :]
    p.put(m & board, 'C', 9.6)
    # the canopy over the platform on cast-iron posts, snow on top
    can = p.box(140, 166, 330, 170)
    p.put(can, 'C', 1.6)
    p.put(p.box(140, 165, 330, 166), 'C', 9.0)
    for k in range(144, 330, 8):
        p.put(p.box(k, 170, k + 4, 172), 'C', 1.2)                                       # valance
    for px_ in (150, 238, 324):
        p.put(p.box(px_, 170, px_ + 2, 205), 'C', 1.2)
    # the platform: surface, snow, the white edge, the face of the platform wall
    plat = p.box(0, 198, w, 207)
    p.put(plat, 'C', 6.2 + (pg.value_noise(w, h, 8, 1621, 2) - 0.5) * 0.8)
    p.put(p.box(0, 205, w, 207), 'C', 10.4)
    p.put(p.box(0, 207, w, 214), 'C', 1.6)
    p.put(p.box(0, 207, w, 208), 'C', 3.4)
    p.put(p.box(0, 214, w, 233), 'C', 3.0 + (pg.value_noise(w, h, 5, 1622, 2) - 0.5) * 0.8)
    for k in range(0, w, 7):
        p.put(p.box(k, 216, k + 4, 217), 'C', 1.8)                                         # the other rail's sleepers
    # the bench, a parcel cart with two crates, a fire bucket rack
    p.put(p.box(64, 192, 90, 194), 'O', 2.6)
    p.put(p.box(64, 188, 90, 189), 'O', 2.6)
    p.put(p.box(64, 187, 90, 188), 'C', 9.0)
    p.put(p.box(64, 191, 90, 192), 'C', 9.0)
    for lg in (66, 87):
        p.put(p.box(lg, 194, lg + 1, 198), 'C', 1.0)
    cart = p.box(340, 190, 372, 194)
    p.put(cart, 'O', 2.2)
    p.put(p.box(342, 180, 356, 190), 'O', 3.4)
    p.put(p.box(356, 184, 368, 190), 'O', 3.0)
    p.put(p.box(342, 179, 368, 180), 'C', 9.0)
    for wx in (346, 366):
        p.put(p.ell(wx, 195.5, 2.5, 2.5), 'C', 1.0)
    p.put(p.line([(372, 192), (382, 186)], 0.5), 'O', 2.0)
    # the signal box at the far end (lit window) and the lamp posts
    sbx = p.box(410, 156, 452, 198)
    p.put(sbx, 'O', 2.0)
    p.put(p.box(414, 166, 448, 178), 'L', 3.0, emis=True)
    for k in range(414, 448, 6):
        p.put(p.box(k, 166, k + 1, 178), 'O', 1.6)
    p.put(p.poly([(406, 157), (431, 144), (456, 157)]), 'C', 6.6)
    p.put(p.poly([(406, 157), (431, 144), (456, 157)]) & ~shift(p.poly([(406, 157), (431, 144), (456, 157)]), 0, -1),
          'C', 9.6)
    lamps = [40, 298, 394]
    for lx in lamps:
        p.put(p.box(lx, 128, lx + 2, 198), 'C', 1.2)
        p.put(p.box(lx - 4, 124, lx + 6, 128), 'C', 1.8)
        p.put(p.box(lx - 3, 128, lx + 5, 130), 'L', 6.0, emis=True)
        p.put(p.box(lx - 4, 123, lx + 6, 124), 'C', 9.0)
        # the lamp's pool on the platform
        pool = p.ell(lx + 1, 201, 18, 2.5) & plat
        lv = C.point_light(h, w, lx + 1, 201, 18, 0, y0)
        p.put(pool & (lv * 1.5 > pg.bayer(w, h, 0, y0)), 'L', 2.0 + lv * 1.8)
    # the light of the office window falling on the snow of the platform
    p.put(p.poly([(168, 198), (178, 198), (186, 205), (160, 205)]) & plat, 'L', 2.2)
    # the station master's lantern throws a small warm pool round his boots
    lp = p.ell(SM_X - 3, 203.5, 8, 1.6) & plat
    lv = np.clip(1 - np.abs(xx - (SM_X - 3)) / 8.0, 0, 1)
    p.put(lp & (lv * 1.3 > pg.bayer(w, h, 1, y0)), 'L', 2.4 + lv * 1.4)
    p.resolve(band=2.6)
    LAYOUT['station_lamps'] = [lx + 1 for lx in lamps]
    # AD round 2: the station master with his lantern under the lamp, watching the special run through, and a
    # porter at the parcel cart (figures stream sheets).  The canvas starts at row y0, so the soles (world row 204)
    # go to canvas row 204 - y0 -- the first version passed the world row and the figure was clipped away.
    import env_veltrava_cine_cast as CAST
    sm = CAST.person('railwayman', 25, frames=4, pose='stand', facing=-1, light='night_lamp', seed=11)
    CAST.stamp(p.L.c, sm, 4, 0, SM_X, 204 - y0)
    po = CAST.person('porter', 23, frames=4, pose='stand', facing=-1, light='night_lamp', seed=12)
    CAST.stamp(p.L.c, po, 4, 0, 386, 203 - y0)
    LAYOUT['station_people'] = [[SM_X, 204], [386, 203]] if sm is not None else []
    return p.L


SM_X = 286                               # the station master stands in the pool of the lamp at x 298


# =========================================================================== the river below the truss bridge
def _hn(ix, iy, seed):
    """Hash noise in 0..1 on an integer lattice (numpy int64 arrays)."""
    n = (ix * 374761393 + iy * 668265263 + seed * 1442695041) & 0xFFFFFFFF
    n = ((n ^ (n >> 13)) * 1274126177) & 0xFFFFFFFF
    return ((n ^ (n >> 16)) & 0xFFFF).astype(np.float32) / 65535.0


def _vn(x, y, seed, octaves=3):
    """Smooth value noise in 0..1 at arbitrary (world) coordinates -- the river is painted in world units and
    projected, so its texture needs noise that is not tied to the pixel grid."""
    out = np.zeros(np.shape(x), np.float32)
    amp, tot = 1.0, 0.0
    fx_, fy_ = np.asarray(x, np.float64), np.asarray(y, np.float64)
    for o in range(octaves):
        xi = np.floor(fx_).astype(np.int64)
        yi = np.floor(fy_).astype(np.int64)
        u = (fx_ - xi).astype(np.float32)
        v = (fy_ - yi).astype(np.float32)
        u = u * u * (3 - 2 * u)
        v = v * v * (3 - 2 * v)
        s = seed + o * 101
        a = _hn(xi, yi, s)
        b = _hn(xi + 1, yi, s)
        c = _hn(xi, yi + 1, s)
        d = _hn(xi + 1, yi + 1, s)
        out += amp * ((a + (b - a) * u) + ((c + (d - c) * u) - (a + (b - a) * u)) * v)
        tot += amp
        amp *= 0.5
        fx_, fy_ = fx_ * 2.0, fy_ * 2.0
    return out / tot


# river view geometry (abs rows; the glass ends at row 226): the ground plane vanishes at row RIV_HY; row y shows
# lateral world offsets scaled by k(y) = (y + 0.5 - RIV_HY) / (RIV_BOT + 0.5 - RIV_HY) (1 at the bottom row).
# Above RIV_BEND the river turns
# away behind a belt of willows: those rows stand at the bend's depth and share its k.  X is measured in
# bottom-row pixels, D = 1 / k is the relative distance (1 at the bottom row).
RIV_Y0, RIV_BOT, RIV_HY, RIV_BEND = 189, 229, 188.0, 203
RIV_H = RIV_BOT - RIV_Y0 + 1
RIV_W, RIV_CX = 520, 260
RIV_HW = 128                                # half width of the ice at the bottom row (inside the bridge's span)
RIV_V = 150.0                               # bottom-row speed (px/s at full motion; below the embankment's 150, the ice
                                            # lies deeper); row y moves at RIV_V * k(y)


def riv_k(y):
    y = np.maximum(np.asarray(y, np.float32), RIV_BEND)
    return (y + 0.5 - RIV_HY) / (RIV_BOT + 0.5 - RIV_HY)


def riv_proj(X, D):
    """World (X bottom-row px, D relative distance) on the ground -> image (x, y) of pass_river (abs row)."""
    k = 1.0 / D
    y = RIV_HY - 0.5 + k * (RIV_BOT + 0.5 - RIV_HY)
    return RIV_CX + X * k, y


def _riv_centre(D):
    return 10.0 * np.sin(D * 1.9 + 0.4) - 6.0


def pass_river():
    """The frozen river seen from the truss bridge, in perspective (rows 189..229): wind-scoured ice with snow drifts
    running down the river, an open lead of black water with sea smoke and frost on its rims, white fracture lines,
    a trodden path and a sled track across, fishing holes; the snowy banks with reeds frozen in at the waterline; at
    the top the bend where the river turns away between two clumps of pollard willows, a fisherman's hut with a lit
    window.  Both lateral ends fade into
    transparency so the plain of ext_mid shows on (the runtime scrolls every row at its own depth's speed)."""
    R = ramps()
    w, h, y0 = RIV_W, RIV_H, RIV_Y0
    p = C.Paint(w, h, R, 'pass_river', 0, y0)
    yy, xx = p.yy, p.xx
    bay = pg.bayer(w, h, 0, y0)
    k = riv_k(yy)
    X = (xx + 0.5 - RIV_CX) / k
    D = 1.0 / k
    ground = yy >= RIV_BEND
    rel = X - _riv_centre(D)
    ax = np.abs(rel)
    # lateral fade into the plain (dithered alpha), wider than the banks
    fade = np.clip(1 - (ax - (RIV_HW + 34)) / 40.0, 0, 1)
    keep = ground & (fade > bay * 0.98)
    # ---- the plain at both ends + the banks sloping down to the ice
    plain = keep & (ax >= RIV_HW + 26)
    pn = _vn(X / 46.0, D * 3.0, 1641)
    p.put(plain, 'C', 4.5 - (k - 0.3) * 0.5 + (pn - 0.5) * 0.9)
    crest = np.sin(rel * 0.09 + pn * 7.0) > 0.9
    p.add(plain & crest, 0.8)
    bank = keep & (ax >= RIV_HW) & (ax < RIV_HW + 26)
    bu = (ax - RIV_HW) / 26.0                                   # 0 at the waterline .. 1 at the top of the bank
    p.put(bank, 'C', 3.6 + bu * 2.2 + (pn - 0.5) * 0.7)
    top = keep & (ax >= RIV_HW + 22) & (ax < RIV_HW + 27)
    p.put(top, 'C', 6.8)                                        # the snow lip of the bank catching the Line's glow
    p.put(keep & (ax >= RIV_HW + 27) & (ax < RIV_HW + 30), 'C', 3.4)        # its shadow on the plain side
    # the waterline: wet dark snow and reeds frozen in, bushes and stones on the slope (ground marks)
    rr = _vn(X / 5.0, D * 22.0, 1642, 1)
    p.put(bank & (bu < 0.16), 'C', 1.6 + (rr - 0.5) * 0.8)
    p.put(bank & (rr > 0.72) & (bu < 0.4), 'C', 1.0)
    p.put(bank & (rr > 0.82) & (bu >= 0.4) & (bu < 0.8), 'O', 1.6)
    p.put(plain & (_vn(X / 9.0, D * 14.0, 1643, 1) > 0.86), 'C', 1.6)
    # ---- the ice: scoured black-blue, snow drifts in long tongues down the river, polished patches with glints
    ice = keep & (ax < RIV_HW)
    n1 = _vn(X / 38.0, D * 2.6, 1644)
    n2 = _vn(X / 12.0, D * 7.0, 1645)
    t = 2.4 + (n1 - 0.5) * 0.9 + (n2 - 0.5) * 0.4 + (1 - k) * 0.7
    p.put(ice, 'C', t)
    drift = ice & (np.sin((X + 30.0 * n1) * 0.06) + (n2 - 0.5) * 0.9 > 0.7)
    p.put(drift, 'C', 4.2 + (n2 - 0.5) * 0.7 + (1 - k) * 0.4)
    p.put(drift & ~shift(drift, 0, -1), 'C', 5.4)
    polish = ice & ~drift & (n1 < 0.32)
    p.put(polish, 'C', 1.5 + (1 - k) * 0.4)
    p.put(polish & (_vn(X / 3.0, D * 30.0, 1646, 1) > 0.86), 'C', 6.2)          # glints of the Line's light
    # the open lead: black water winding down the middle, sea smoke over it, grey ice and frost flowers on its rims
    lead_c = -30.0 + 22.0 * np.sin(D * 2.5 + 1.1)
    lw = 11.0 + 3.0 * np.sin(D * 4.0)
    ld = np.abs(X - lead_c)
    p.put(ice & (ld < lw + 3) & (ld >= lw), 'C', 2.0)
    water = ice & (ld < lw)
    p.put(water, 'C', 0.3 + (_vn(X / 6.0, D * 10.0, 1647, 1) - 0.5) * 0.5)
    p.put(water & (_vn(X / 4.0, D * 12.0, 1654, 1) > 0.55) & (bay < 0.32), 'C', 3.8)        # vapour
    p.put(ice & (ld >= lw + 2) & (ld < lw + 4) & (_vn(X / 2.0, D * 40.0, 1648, 1) > 0.5), 'C', 5.9)
    # cracks (straight world segments project to straight lines)
    rng = np.random.default_rng(1649)
    for _ in range(7):
        x0, d0 = rng.uniform(-RIV_HW + 10, RIV_HW - 10), rng.uniform(1.05, 3.0)
        pts = [riv_proj(x0, d0)]
        xc, dc = x0, d0
        for _k in range(3):
            xc += rng.uniform(-30, 30)
            dc = float(np.clip(dc + rng.uniform(-0.25, 0.25), 1.0, 3.1))
            pts.append(riv_proj(xc, dc))
        p.add(p.line(pts, 0.35) & ice & ~(ld < lw + 3) & ~drift, 1.6)      # white fracture lines in the dark ice
    # a trodden path across the river (the fishers' way), and a sled track to the holes
    for i in range(34):
        u = i / 33.0
        fx_ = -RIV_HW - 20 + u * (2 * RIV_HW + 40)
        fd = 2.05 - u * 0.55 + (0.035 if i % 2 else -0.035)
        if abs(fx_ - float(-30.0 + 22.0 * math.sin(fd * 2.5 + 1.1))) < 15:
            continue                                                           # they cross the lead on a plank
        qx, qy = riv_proj(fx_, fd)
        p.put(p.box(qx, qy, qx + max(1.0, 2.2 / fd), qy + 1) & keep, 'C', 5.0)
    for side in (-1.0, 1.0):
        a = riv_proj(-74 + side * 2.5, 1.18)
        b = riv_proj(-RIV_HW - 30 + side * 2.5, 1.62)
        p.put(p.line([a, b], 0.3) & keep, 'C', 4.8)
    for (hx, hd) in ((-78.0, 1.16), (-60.0, 1.3), (-90.0, 1.42)):
        qx, qy = riv_proj(hx, hd)
        hole = p.ell(qx, qy, 2.6 / hd, 1.0)
        p.put(hole & ice, 'C', 5.6)
        p.put(p.ell(qx, qy, 1.4 / hd, 0.6) & ice, 'C', 0.3)
    plank = p.line([riv_proj(-12, 1.8), riv_proj(-52, 1.86)], 0.45)
    p.put(plank & ice, 'O', 3.0)
    # ---- the bend: the river turns away behind a willow clump on each bank; reeds, the fisherman's hut
    kb = float(riv_k(RIV_BEND))
    cb = float(_riv_centre(1 / kb))
    bx = (xx + 0.5 - RIV_CX) / kb
    bax = np.abs(bx - cb)
    bfade = np.clip(1 - (bax - (RIV_HW + 40)) / 36.0, 0, 1)
    bkeep = (bfade > bay * 0.98)
    base = RIV_BEND - 1
    fb = bkeep & (yy >= RIV_BEND - 3) & (yy < RIV_BEND)
    p.put(fb, 'C', 4.8 + (_vn(bx / 9.0, yy / 2.0, 1650, 2) - 0.5) * 0.8)
    beyond = fb & (bax < RIV_HW - 6)                              # the snowed-over ice beyond the bend
    p.put(beyond, 'C', 5.6)
    p.put(fb & (yy == RIV_BEND - 3) & ~beyond, 'C', 6.2)
    reed = bkeep & (yy >= base - 2) & (yy <= base) & (bax > RIV_HW - 14) & (bax < RIV_HW + 8) & \
        (((xx.astype(int) * 7 + yy.astype(int) * 3) % 4) == 0)
    p.put(reed, 'O', 2.0)
    rng = np.random.default_rng(1651)
    for side in (-1.0, 1.0):
        for j, off in enumerate((-4.0, 14.0, 30.0)):
            tx = cb + side * (RIV_HW + off)
            sx = int(round(RIV_CX + tx * kb))
            th = int(rng.integers(4, 7))
            if j == 2 and side > 0:                                    # a young fir behind the hut
                fh = 9.0
                fir = p.poly([(sx - 3, base + 1), (sx, base - fh), (sx + 3, base + 1)])
                p.put(fir, 'G', 1.2)
                p.put(fir & ((yy.astype(int) - int(base)) % 3 == 0), 'C', 6.0)
                continue
            # pollard willow: a stout trunk, the knobbed head, a fan of thin rods dusted with snow
            p.put(p.box(sx, base - th, sx + 2, base + 1), 'O', 1.2)
            p.put(p.box(sx - 1, base - th - 1, sx + 3, base - th + 1), 'O', 1.6)
            for _r in range(7):
                a_ = rng.uniform(-2.6, -0.55)
                ln = rng.uniform(3.5, 7.5)
                p.put(p.line([(sx + 1, base - th), (sx + 1 + math.cos(a_) * ln, base - th + math.sin(a_) * ln)], 0.28),
                      'C', 2.4 + rng.uniform(0, 0.8))
            p.px(sx, base - th - 2, 'C', 7.0)                                       # snow on the head
            p.px(sx + 2, base - th - 1, 'C', 6.2)
    # the fisherman's hut on the far bank, its window lit, the stovepipe (runtime smoke: LAYOUT river.hut)
    hx = int(round(RIV_CX + (cb + RIV_HW + 22.0) * kb))
    p.put(p.box(hx, base - 5, hx + 8, base + 1), 'O', 1.6)
    hroof = p.poly([(hx - 1, base - 4), (hx + 4, base - 8), (hx + 9, base - 4)])
    p.put(hroof, 'C', 6.6)
    p.put(p.box(hx + 2, base - 3, hx + 4, base - 1), 'L', 4.2, emis=True)
    p.put(p.box(hx + 6, base - 10, hx + 7, base - 6), 'C', 1.2)
    p.resolve(band=3.0)
    LAYOUT['river'] = {'y0': RIV_Y0, 'h': RIV_H, 'w': RIV_W, 'cx': RIV_CX, 'hy': RIV_HY, 'bot': RIV_BOT,
                       'bend': RIV_BEND, 'v': RIV_V, 'half': RIV_HW + 82, 'hut': [hx + 6.5, base - 10],
                       'objs': _RIV_OBJS_LAYOUT}
    return p.L


# upright things on the ice (drawn by the runtime at the depth of their foot): name, X, D
RIV_OBJS = [('tent', 58.0, 1.5), ('fisher', -70.0, 1.2), ('boat', 142.0, 1.75), ('pole', -92.0, 1.4)]
_RIV_OBJS_LAYOUT: list = []


def pass_river_obj():
    """The atlas of upright things on the river (one 24 x 18 cell each, foot centre at (12, 17)): an ice-fishing
    tent with a lantern glowing through the canvas, a fisher on his box at the hole (figures stream), a rowing boat
    frozen in by the bank, a marker pole with a rag."""
    R = ramps()
    cw, ch = 24, 18
    n = len(RIV_OBJS)
    p = C.Paint(cw * n, ch, R, 'pass_river_obj', 0, 0)
    for i, (name, _x, _d) in enumerate(RIV_OBJS):
        ox = i * cw + 12
        fy = ch - 1
        if name == 'tent':
            tent = p.poly([(ox - 6, fy + 1), (ox, fy - 8), (ox + 6, fy + 1)])
            p.put(tent, 'O', 2.4)
            p.put(tent & (p.xx >= ox), 'O', 3.0)
            p.put(tent & ~shift(tent, 0, -1), 'C', 7.0)
            glow = p.ell(ox + 1, fy - 2, 2.5, 2.5) & tent
            p.put(glow, 'L', 3.0, emis=True)
            p.put(p.box(ox, fy - 2, ox + 2, fy + 1), 'L', 4.6, emis=True)          # the door flap, lit inside
            p.put(p.box(ox - 7, fy, ox + 7, fy + 1), 'C', 5.4)                      # snow banked round it
        elif name == 'boat':
            hull = p.poly([(ox - 8, fy - 2), (ox + 8, fy - 2), (ox + 6, fy + 1), (ox - 6, fy + 1)])
            p.put(hull, 'O', 1.8)
            p.put(p.box(ox - 8, fy - 3, ox + 8, fy - 2), 'C', 7.0)                  # snow on the gunwale
            p.put(p.box(ox - 5, fy - 2, ox + 5, fy - 1), 'C', 6.0)                  # snow in the boat
            p.put(p.box(ox - 9, fy, ox + 9, fy + 1), 'C', 5.2)
        elif name == 'pole':
            p.put(p.box(ox, fy - 9, ox + 1, fy + 1), 'O', 2.0)
            p.put(p.poly([(ox + 1, fy - 9), (ox + 5, fy - 8), (ox + 1, fy - 6)]), 'R', 2.0)
            p.put(p.box(ox - 1, fy, ox + 2, fy + 1), 'C', 5.4)
    p.resolve(band=2.6)
    a = p.L.c
    # the fisher: the figures stream's sitting fisher, night light (frame 0)
    import env_veltrava_cine_cast as CAST
    fi = [i for i, o in enumerate(RIV_OBJS) if o[0] == 'fisher'][0]
    sh = CAST.person('fisher', 12, frames=4, pose='sit', facing=-1, light='night', seed=21)
    CAST.stamp(a, sh, 4, 0, fi * cw + 12, ch - 1)
    _RIV_OBJS_LAYOUT.clear()
    for i, (name, ox_, od) in enumerate(RIV_OBJS):
        cell = a[:, i * cw:(i + 1) * cw]
        if not (cell[..., 3] > 0).any():
            continue
        _RIV_OBJS_LAYOUT.append([name, i * cw, cw, ch, ox_, od])
    if 'river' in LAYOUT:
        LAYOUT['river']['objs'] = list(_RIV_OBJS_LAYOUT)
    return a


def preview():
    import os
    from PIL import Image
    out = os.environ.get('TEMP', '.')
    for name, fn in (('ext_mid_de', ext_mid_de), ('ext_mid_su', ext_mid_su), ('pass_station', pass_station),
                     ('pass_river', pass_river), ('pass_river_obj', pass_river_obj)):
        a = fn()
        a = a.c if hasattr(a, 'c') else a
        bg = np.zeros_like(a)
        bg[..., :3] = (30, 38, 52)
        bg[..., 3] = 255
        al = a[..., 3:4] / 255.0
        img = (a[..., :3] * al + bg[..., :3] * (1 - al)).astype(np.uint8)
        Image.fromarray(img).resize((img.shape[1] * 2, img.shape[0] * 2), Image.NEAREST).save(
            os.path.join(out, name + '_prev.png'))
    print(out)
