"""env_veltrava_station_bg -- sky and far parallax planes for L_C3_Station 'Bahnhof Veltrava'.

All make_* functions draw in SCREEN y (= world y, the camera never moves vertically) on full-height
layers of the parallax width (layer x 0 = layer left edge); env_veltrava_station.py crops them.
Screen x of a layer pixel = x - cam_x * parallax.  Planned visibility (cam 0 / 640 / 1280) is noted
next to each landmark.  Value plan (far -> near = light -> dark): skyline in sky haze, mansard city in
slate haze, station building in cream sandstone.  Key light: low dawn sun behind haze at the right
(SUN), 1 px rim light on right edges, lit cloud undersides, cold ambient.
"""
from __future__ import annotations

import math

import numpy as np

import pg
from env_veltrava_lib import (Layer, NI, SL, IR, CR, PA, LA, SK, SN, RD, CLEAR, bayer, value_noise, dmask,
                              ladder_paint, ladder_shift, text, text_width, text_center, cyl_normal, flat_normal,
                              snow_top, tiny_person, layer_w, arch_mask, put_mask, rustication)

SUN = (575, 103)                      # screen position of the hazy dawn sun (sky layer, parallax 0)
SKY_LADDER = [SL[2], SL[3], SK[0], SK[1], SK[2], SK[3], SK[4], SK[5], LA[4], SN[4]]
SKY_STOPS = [(0, 0.3), (24, 0.95), (50, 1.8), (76, 2.65), (100, 3.45), (120, 4.2), (140, 4.9), (158, 5.5),
             (176, 6.0), (200, 6.4), (360, 6.5)]


def sky_index(y):
    return np.interp(y, [s[0] for s in SKY_STOPS], [s[1] for s in SKY_STOPS])


# =========================================================================== SKY (parallax 0)
def make_sky():
    """Cold dawn: slate zenith (mostly under the canopy edge), lavender middle sky, rose-pale horizon and a
    pale gold glow around the low sun at the right (it rises behind the station roof at cam 0 and 640)."""
    W, H = layer_w(0.0), 360
    L = Layer(W, H, 'sky')
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    T = sky_index(yy)
    nz = value_noise(W, H // 5 + 2, 52, seed=11, octaves=2)
    band = np.repeat(nz, 5, axis=0)[:H]
    T += (band - 0.5) * 0.36 * np.clip((yy - 20) / 70, 0, 1) * (yy < 160)
    d = np.sqrt(((xx - SUN[0]) / 330.0) ** 2 + ((yy - SUN[1]) / 120.0) ** 2)
    T += np.clip(1 - d, 0, 1) ** 1.5 * 1.7
    d2 = np.sqrt(((xx - SUN[0]) / 86.0) ** 2 + ((yy - SUN[1]) / 30.0) ** 2)
    T += np.clip(1 - d2, 0, 1) ** 1.2 * 1.0
    hb = np.clip(1 - np.abs(yy - 132) / 24.0, 0, 1) * np.clip(1 - np.abs(xx - SUN[0]) / 440.0, 0, 1)
    T += hb * 0.6
    T = np.minimum(T, 7.7)
    dd = np.sqrt((xx - SUN[0]) ** 2 + ((yy - SUN[1]) * 1.1) ** 2)
    T[dd < 9.0] = np.maximum(T[dd < 9.0], 7.9)
    T[dd < 7.4] = 8.0
    T[dd < 5.0] = 9.0
    for (ly, x0, x1, amt) in [(99, 500, 650, -1.1), (102, 530, 630, -0.7), (107, 470, 660, -1.0),
                              (95, 540, 620, -0.5), (112, 500, 610, -0.5), (116, 420, 590, -0.4)]:
        wob = value_noise(W, 1, 14, seed=ly, octaves=2)[0]
        seg = (yy == ly) & (xx >= x0) & (xx < x1) & (wob[None, :] > 0.42)
        T[seg] += amt
    ladder_paint(L, np.ones((H, W), bool), 0, 0, T, SKY_LADDER)
    L.hgt[:] = 0
    return L


# =========================================================================== CLOUDS (parallax 0.03)
def band_cloud(L, circles, sun_boost=0.0, flat_bottom=None, light=(1, 1), seed=0, wisp=0.0):
    """Pixel cloud: silhouette from circles, tone bands by offsetting the silhouette toward the low sun
    (lit crescent bottom-right), tones taken from the sky ladder relative to the local sky."""
    xs0 = int(min(c[0] - c[2] for c in circles)) - 2
    ys0 = int(min(c[1] - c[2] for c in circles)) - 2
    xs1 = int(max(c[0] + c[2] for c in circles)) + 3
    ys1 = int(max(c[1] + c[2] for c in circles)) + 3
    w, h = xs1 - xs0, ys1 - ys0
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    X, Y = xx + xs0, yy + ys0
    M = np.zeros((h, w), bool)
    for cx, cy, r in circles:
        M |= ((X + 0.5 - cx) ** 2 + (Y + 0.5 - cy) ** 2) <= r * r
    if flat_bottom is not None:
        M &= Y <= flat_bottom
    if wisp > 0:
        nz = value_noise(w, h, 4, seed, octaves=2)
        edge = M & ~(np.roll(M, 3, 0) & np.roll(M, -3, 0) & np.roll(M, 3, 1) & np.roll(M, -3, 1))
        M &= ~(edge & (nz < wisp))

    def inside(dx, dy):
        S = np.zeros_like(M)
        sy0, sy1 = max(0, -dy), min(h, h - dy)
        sx0, sx1 = max(0, -dx), min(w, w - dx)
        S[sy0:sy1, sx0:sx1] = M[sy0 + dy:sy1 + dy, sx0 + dx:sx1 + dx]
        return S & M

    lx, ly = light
    b1 = inside(lx * 2, ly * 2)
    b1b = inside(lx * 3, ly * 4)
    b2 = inside(lx * 5, ly * 7)
    b3 = inside(lx * 9, ly * 12)
    tone = np.full((h, w), 1.0, np.float32)       # lit rim (bottom-right, facing the low sun)
    tone[b1b & ~b1] = 0.65
    tone[b1] = 0.25
    tone[b2] = -0.35
    tone[b3] = -0.8                               # shaded core
    cy_m = float(np.mean([c[1] for c in circles]))
    base = sky_index(cy_m) * 0.75 + sky_index(Y) * 0.25 - 0.1
    d = np.sqrt(((X - SUN[0]) / 300.0) ** 2 + ((Y - SUN[1]) / 120.0) ** 2)
    boost = np.clip(1 - d, 0, 1) ** 1.1 * (1.5 + sun_boost)
    T = np.minimum(base + tone + boost * np.clip(tone + 0.5, 0, 2.0) * 0.8, 7.85)
    ladder_paint(L, M, xs0, ys0, T, SKY_LADDER)
    hg = np.zeros((h, w), np.float32)
    hg[M] = 0.3
    hg[b2] = 0.6
    L._put(M, xs0, ys0, None, hgt=hg)
    return M


def cloud_circles(rng, x, yb, w, h, lobes=None, rmin=0.35, rmax=0.9):
    n = lobes or max(4, int(w / (h * 0.7)))
    out = []
    for i in range(n):
        t = (i + rng.uniform(0.1, 0.9)) / n
        env = math.sin(math.pi * t) ** 0.6
        r = h * (rmin + (rmax - rmin) * env) * rng.uniform(0.75, 1.05)
        out.append((x + t * w, yb - r * rng.uniform(0.45, 0.75), r))
        if rng.random() < 0.45:
            out.append((x + t * w + rng.uniform(-r, r) * 0.6, yb - r * 1.1, r * rng.uniform(0.4, 0.6)))
    return out


def make_clouds():
    W = layer_w(0.03, 40)
    L = Layer(W, 360, 'clouds')
    rng = np.random.default_rng(31)
    # high thin altocumulus just under the canopy edge (sparse, flat)
    for i, (x, yb, w) in enumerate([(30, 40, 80), (250, 34, 70), (470, 46, 96), (360, 56, 44), (600, 38, 60)]):
        band_cloud(L, cloud_circles(rng, x, yb, w, 6, rmin=0.6, rmax=1.0), flat_bottom=yb, seed=100 + i, wisp=0.35)
    # stratocumulus banks in the visible middle sky; the right ones catch the dawn from below
    specs = [(-50, 92, 230, 26), (160, 74, 120, 18), (250, 106, 200, 24), (440, 84, 130, 18),
             (540, 104, 150, 16), (70, 122, 130, 12), (650, 96, 80, 16), (330, 62, 110, 12)]
    for i, (x, yb, w, h) in enumerate(specs):
        band_cloud(L, cloud_circles(rng, x, yb, w, h), flat_bottom=yb + 1, seed=200 + i, wisp=0.18)
    # low stratus streaks glowing near the sun
    for i, (x0, y, ln) in enumerate([(420, 112, 150), (500, 130, 160), (220, 128, 110), (600, 108, 80),
                                     (40, 120, 120)]):
        circ = [(x0 + k, y + math.sin(k / 17.0) * 1.4, 1.8 + 1.2 * math.sin(math.pi * k / ln)) for k in range(0, ln, 3)]
        band_cloud(L, circ, seed=300 + i, sun_boost=0.8)
    L.hgt *= 0.6
    return L


# =========================================================================== shared painters
def tone_box(L, x, y, w, h, C, hgt=0.5, rim=True, left=True, top=None):
    L.rect(x, y, w, h, C['body'], hgt=hgt)
    if left:
        L.rect(x, y, 1, h, C['sh'], hgt=hgt - 0.05)
    if rim:
        L.rect(x + w - 1, y, 1, h, C['rim'], hgt=hgt + 0.05)
    if top is not None:
        L.hline(x, y, w, top, hgt + 0.1)


def fog_base(L, ladder, y0, y1, steps, power=1.4):
    rows = np.arange(L.h, dtype=np.float32)
    t = np.clip((rows - y0) / max(1, y1 - y0), 0, 1) ** power * steps
    ladder_shift(L, ladder, np.repeat(t[:, None], L.w, axis=1))


def dome(L, cx, base, rx, ry, C, lantern=0, drum=0, ribs=True, onion=False):
    """Front-facing dome on an optional drum, lit from the right (patina / slate)."""
    if drum:
        tone_box(L, int(cx - rx * 0.86), base - drum, int(rx * 1.72), drum, C, top=C.get('top'))
        for k in range(int(cx - rx * 0.86) + 2, int(cx + rx * 0.86) - 1, 3):
            L.vline(k, base - drum + 2, drum - 3, C['sh'])
        base -= drum
    for yy in range(int(ry) + 1):
        t = yy / max(1.0, ry)
        if onion:     # bulb: pointed top, widest at ~60 %, narrower neck at the drum
            hw = rx * 1.12 * math.sin(math.pi * t * 0.82) ** 0.9
        else:
            hw = rx * math.sqrt(max(0.0, 1 - (1 - t) ** 2))
        y = base - int(ry) + yy
        x0, x1 = int(round(cx - hw)), int(round(cx + hw))
        for x in range(x0, x1 + 1):
            u = (x - cx) / max(1.0, hw)
            if x == x1:
                c = C['rim']
            elif u > 0.45:
                c = C['lit'] if ((x + y) % 2 == 0 or u > 0.7) else C['body']
            elif u < -0.45:
                c = C['sh']
            else:
                c = C['body']
            L.px(x, y, c, 0.5 + 0.3 * (1 - t))
    if ribs and rx >= 6:
        for k in (-0.5, 0.0, 0.5):
            xr = int(round(cx + k * rx * 0.8))
            for yy in range(int(ry * 0.25), int(ry)):
                if L.c[base - int(ry) + yy, xr, 3]:
                    L.px(xr, base - int(ry) + yy, C['sh'] if k < 0.3 else C['body'])
    cyl_normal(L, int(cx - rx) - 1, base - int(ry) - 1, int(2 * rx) + 3, int(ry) + 2)
    if lantern:
        lx = int(round(cx))
        L.rect(lx - 2, base - int(ry) - lantern, 4, lantern, C['body'])
        L.vline(lx + 1, base - int(ry) - lantern, lantern, C['rim'])
        L.rect(lx - 1, base - int(ry) - lantern - 3, 2, 3, C['lit'])
        L.vline(lx, base - int(ry) - lantern - 7, 4, C['sh'])
    return base - int(ry)


def spire(L, cx, base, w, h, C):
    for k in range(h):
        t = k / max(1, h - 1)
        hw = w / 2 * (1 - t) ** 1.05
        y = base - k
        x0, x1 = int(round(cx - hw)), int(round(cx + hw))
        for x in range(x0, max(x0 + 1, x1)):
            c = C['rim'] if x == max(x0, x1 - 1) else (C['sh'] if x < cx - hw * 0.2 else C['body'])
            L.px(x, y, c, 0.5)
    L.vline(int(cx), base - h - 3, 3, C['sh'])


def gable_roof(L, x, y_eave, w, rise, C, snow=None, step=2):
    for k in range(rise):
        inset = int(k * w / (2 * rise))
        L.hline(x + inset, y_eave - k, w - 2 * inset, C['roof'] if k % 3 else C['roof_sh'], 0.6)
        L.px(x + w - inset - 1, y_eave - k, C['rim'])
    if snow is not None:
        for k in range(1, rise, step):
            inset = int(k * w / (2 * rise))
            L.px(x + inset, y_eave - k, snow)
            L.px(x + w - inset - 1, y_eave - k, snow)


def mansard(L, x, y_top, w, h_roof, C, snow=None, dormers=0, seed=0):
    """Mansard roof seen from the front: steep lower slope with dormers, flat-ish cap, snow on ledges."""
    rng = np.random.default_rng(abs(int(seed)) + 1)
    for k in range(h_roof):
        inset = 1 if k < h_roof - 2 else 0
        L.hline(x + inset, y_top + k, w - 2 * inset, C['roof'] if (k % 3) else C['roof_sh'], 0.62)
        L.px(x + w - 1 - inset, y_top + k, C['rim'])
        L.px(x + inset, y_top + k, C['roof_sh'])
    L.hline(x + 2, y_top - 1, w - 4, C['roof_sh'], 0.7)
    if snow is not None:
        L.hline(x + 2, y_top - 2, w - 4, snow, 0.75)
        for xx in range(x + 1, x + w - 1):
            if rng.random() < 0.35:
                L.px(xx, y_top + 1 + int(rng.integers(0, max(1, h_roof - 2))), snow)
    for i in range(dormers):
        dx = x + 4 + int((i + 0.5) * (w - 8) / dormers) - 2
        L.rect(dx, y_top + 1, 4, h_roof - 2, C['win'])
        L.hline(dx - 1, y_top, 6, C['rim'])
        if snow is not None:
            L.hline(dx - 1, y_top - 1, 6, snow)


# =========================================================================== SKYLINE (parallax 0.10)
def make_skyline():
    """Veltrava old town beyond the river, in deep haze.  Everything that matters stands above y ~150 (the
    trains and canopies cover the rest).  Castle hill x 20-430 with the palace range, keep and the Gothic
    cathedral's twin spires (cam0 left/centre), town-hall tower x 412, baroque dome x 476, the commission
    palais with its flat dome and six flagpoles x 560-690 (cam0 right, cam640 above the station's right wing)."""
    p = 0.10
    W = layer_w(p, 16)
    L = Layer(W, 360, 'skyline')
    B = 200
    C = dict(deep=SK[0], sh=SK[1], body=SK[2], lit=SK[3], rim=SK[4], top=SK[3], roof=SK[1], roof_sh=SK[1],
             win=SK[1])
    CD = dict(C, sh=SK[1], body=PA[4], lit=SK[3], rim=SK[4])          # copper domes: a hint of patina
    rng = np.random.default_rng(5)
    # ---- far ridge (palest, beyond the town)
    for x in range(W):
        top = int(150 + 8 * math.sin(x / 61.0) + 4 * math.sin(x / 23.0 + 1.3))
        L.rect(x, top, 1, B - top, SK[3], hgt=0.3)
        L.px(x, top, SK[4])
    # ---- castle hill: rounded mass with rock steps, the castle on the crown
    for x in range(10, 440):
        t = (x - 10) / 430.0
        hh = 74 * math.sin(math.pi * min(1, max(0, t))) ** 0.6 + 4 * math.sin(x / 9.0) + 2 * math.sin(x / 3.7)
        top = int(B - max(0, hh))
        for y in range(top, B):
            L.px(x, y, C['body'] if (x * 3 + y) % 11 else C['sh'], 0.4)
        L.px(x, top, C['lit'] if x > 240 else C['body'])
    for (x0, x1, y) in [(90, 360, 136), (60, 120, 150), (330, 400, 148)]:      # terrace walls
        L.hline(x0, y, x1 - x0, C['rim'])
        L.hline(x0, y + 1, x1 - x0, C['sh'])
        for k in range(x0, x1, 5):
            L.px(k, y - 1, C['lit'])
    # palace range on the crown
    tone_box(L, 100, 110, 236, 26, C, top=C['top'])
    for k in range(100, 336):
        L.px(k, 109, C['roof'])
    for k in range(102, 334, 2):
        L.px(k, 108, C['roof'])
    for fl in range(2):
        for k in range(106, 330, 7):
            L.rect(k, 116 + fl * 9, 2, 4, C['win'])
    for (lx, ly) in ((141, 125), (232, 116), (288, 125)):
        L.px(lx, ly, LA[3], em=LA[3])
    tone_box(L, 140, 84, 18, 26, C, top=C['top'])                              # keep
    for k in range(10):
        L.hline(140 + k, 83 - k, 18 - 2 * k, C['roof'] if k % 2 else C['lit'])
    L.vline(149, 66, 8, C['sh'])
    tone_box(L, 318, 98, 14, 12, C, top=C['top'])                              # round tower + cupola
    dome(L, 325, 98, 7, 7, CD, lantern=5, ribs=False)
    # Gothic cathedral on the castle hill: nave, apse, twin west spires
    tone_box(L, 196, 96, 70, 14, C, top=C['top'])
    for k in range(8):
        L.hline(198 + k, 95 - k, 66 - 2 * k, C['roof'])
    for k in range(200, 262, 6):
        L.rect(k, 99, 2, 8, C['win'])
        L.px(k, 98, C['win'])
    for sx in (204, 220):
        tone_box(L, sx - 5, 72, 11, 38, C, top=C['top'])
        spire(L, sx + 0.5, 72, 12, 26, C)
        L.rect(sx - 1, 80, 3, 9, C['win'])
        for k in range(4):                                                     # crockets on the spire
            L.px(sx - 4 + k, 70 - k * 3, C['rim'])
    spire(L, 250, 86, 4, 12, C)                                                # crossing turret
    # ---- old town below the hill: gables, hipped roofs (mostly hidden; only the top fringe reads)
    x = -4
    while x < W:
        w = int(rng.integers(10, 26))
        h = int(rng.integers(26, 46))
        if 60 < x < 380:
            h = int(rng.integers(16, 30))
        tone_box(L, x, B - h, w, h, C, top=None)
        gable_roof(L, x - 1, B - h - 1, w + 2, int(rng.integers(3, 8)), C)
        for wy in range(B - h + 3, B - 2, 5):
            for wx in range(x + 2, x + w - 2, 4):
                if rng.random() < 0.5:
                    L.px(wx, wy, C['win'])
        if rng.random() < 0.1:
            L.px(x + w // 2, B - h + 4, LA[3], em=LA[3])
        x += w + int(rng.integers(-2, 2))
    # ---- town-hall tower (x 412) and baroque church dome (x 476)
    tone_box(L, 404, 92, 16, 108, C, top=C['top'])
    L.rect(408, 104, 7, 7, C['lit'])
    L.px(411, 107, C['sh'])
    for k in range(6):
        L.hline(404 + k, 91 - k, 16 - 2 * k, C['roof'])
    spire(L, 412, 86, 4, 16, C)
    tone_box(L, 460, 120, 34, 80, C, top=C['top'])
    dome(L, 477, 120, 13, 14, CD, lantern=7, drum=10)
    for sx in (463, 491):
        tone_box(L, sx - 3, 104, 6, 16, C)
        dome(L, sx, 104, 3.5, 4, C, lantern=2, ribs=False)
    # ---- the commission palais (former Kurhaus): broad block, flat dome, six flagpoles on the attic
    tone_box(L, 566, 118, 120, 82, C, top=C['top'])
    for fl in range(3):
        for k in range(570, 682, 6):
            L.rect(k, 124 + fl * 10, 3, 6, C['win'])
    for (lx, ly) in ((588, 125), (630, 135), (660, 125)):
        L.rect(lx, ly, 3, 5, LA[3], em=LA[3])
    tone_box(L, 604, 104, 44, 14, C, top=C['top'])
    dome(L, 626, 104, 19, 14, CD, lantern=6, drum=0)
    flag_cols = [SL[3], RD[2], IR[1], SL[3], RD[3], SN[3]]                     # tiny cloth, no insignia at 3 px
    for i, fx in enumerate((570, 582, 594, 658, 670, 682)):
        L.vline(fx, 102, 16, C['sh'])
        L.rect(fx + 1, 102, 3, 2, flag_cols[i])
    # ---- radio mast and a far chimney (east)
    L.vline(722, 96, 104, C['sh'])
    for y in range(100, 196, 6):
        L.px(721, y, C['sh'])
        L.px(723, y, C['sh'])
    L.px(722, 95, RD[2], em=RD[2])
    tone_box(L, 744, 128, 6, 72, C)
    fog_base(L, [SK[1], SK[2], SK[3], SK[4]], 128, B, 1.4)
    return L


# =========================================================================== MANSARD CITY (parallax 0.30)
def make_city():
    """Gründerzeit blocks with mansard roofs between the station and the old town: slate roofs with snow,
    copper-green corner domes and turrets, chimneys (smoke fx anchors returned).  Roofs 120..150 (above the
    carriage roofs at y ~159).  Accents: copper onion-dome church x 250 (cam0 screen 250 / cam640 screen 58,
    above the station's left wing) and the domed 'Hotel an der Linie' x 790 (cam640 screen ~598)."""
    p = 0.30
    W = layer_w(p, 16)
    L = Layer(W, 360, 'city')
    B = 214
    C = dict(deep=SL[2], sh=SL[3], body=SL[4], lit=SL[5], rim=SK[1], top=SK[1], roof=SL[2], roof_sh=SL[1],
             win=SL[2], snow=SN[1])
    CF = dict(C, sh=SL[3], body=SL[4], lit=SL[5], rim=CR[4], top=CR[3], win=SL[2])  # rims catch the dawn
    CP = dict(C, sh=PA[1], body=PA[2], lit=PA[3], rim=PA[4])                        # copper patina
    rng = np.random.default_rng(17)
    chimneys = []
    x = -6
    i = 0
    while x < W:
        w = int(rng.integers(40, 80))
        top = int(rng.integers(136, 152))
        face = CF if i % 3 == 1 else C
        tone_box(L, x, top, w, B - top, face, top=face['top'])
        for fl in range(7):
            wy = top + 4 + fl * 9
            if wy > B - 6:
                break
            for wx in range(x + 3, x + w - 3, 6):
                L.rect(wx, wy, 3, 5, face['win'], hgt=0.3)
                L.px(wx + 2, wy, face['rim'])
                if rng.random() < 0.03:
                    L.rect(wx, wy + 1, 3, 4, LA[2], em=LA[2])
        L.hline(x, top, w, SN[1])
        kind = i % 4
        hr = int(rng.integers(9, 15))
        if kind == 2:                                   # firewall + flat roof with a chimney row
            L.rect(x, top - 4, w, 4, face['sh'])
            L.hline(x, top - 5, w, SN[1])
        else:
            mansard(L, x + 1, top - hr, w - 2, hr, C, snow=SN[1], dormers=max(1, w // 16), seed=x)
        for k in range(int(rng.integers(1, 4))):
            chx = x + 6 + int(rng.integers(0, max(1, w - 12)))
            chh = int(rng.integers(5, 10))
            ctop = top - (hr if kind != 2 else 4) - chh
            L.rect(chx, ctop, 3, chh, C['sh'])
            L.px(chx + 2, ctop, C['rim'])
            L.hline(chx - 1, ctop - 1, 5, SN[1])
            chimneys.append((chx + 1, ctop - 2))
        if rng.random() < 0.45 and kind != 2:          # corner turret with a copper helm
            tx = x + w - 11
            tone_box(L, tx, top - hr - 8, 10, hr + 8, face)
            dome(L, tx + 5, top - hr - 8, 5.5, 8, CP, lantern=3, ribs=False)
        x += w + int(rng.integers(0, 5))
        i += 1
    # copper onion-dome church (cam 0 left; cam 640 above the station's left wing)
    tone_box(L, 236, 120, 30, 94, CF, top=CF['top'])
    for k in (242, 252):
        L.rect(k, 130, 4, 14, SL[2])
        L.px(k + 1, 129, SL[2])
    tone_box(L, 242, 98, 18, 22, CF, top=CF['top'])
    dome(L, 251, 98, 9, 12, CP, lantern=6, onion=True)
    L.rect(246, 106, 3, 6, SL[2])
    L.rect(253, 106, 3, 6, SL[2])
    # domed corner hotel 'Hotel an der Linie' (cam 640 right, above the station's right wing)
    tone_box(L, 768, 122, 46, 92, CF, top=CF['top'])
    dome(L, 791, 122, 17, 15, CP, lantern=7, drum=7)
    for wy in range(130, 206, 10):
        for wx in range(772, 812, 7):
            L.rect(wx, wy, 3, 6, SL[2])
    L.rect(779, 140, 3, 6, LA[2], em=LA[2])
    L.rect(800, 150, 3, 6, LA[2], em=LA[2])
    # brewery chimney (east) and a slim church tower (west)
    tone_box(L, 940, 84, 7, 130, dict(C, body=SL[3], sh=SL[2], rim=SK[1]))
    L.hline(939, 84, 9, SL[2])
    chimneys.append((943, 82))
    tone_box(L, 96, 112, 16, 102, CF, top=CF['top'])
    dome(L, 104, 112, 8, 9, CP, lantern=8, onion=True)
    fog_base(L, [SL[2], SL[3], SL[4], SK[1], SK[2], SK[3]], 150, B, 1.6)
    return L, chimneys


# =========================================================================== STATION BUILDING (parallax 0.55)
def dilate(m: np.ndarray, r: int = 1) -> np.ndarray:
    """Grow a bool mask by r px (4-neighbourhood per step); output is padded by r on every side."""
    out = np.pad(m, r)
    for _ in range(r):
        p = np.pad(out, 1)
        out = out | p[:-2, 1:-1] | p[2:, 1:-1] | p[1:-1, :-2] | p[1:-1, 2:]
    return out


def _round_window(L, x, y, w, h, frame, glass, refl=None, lit=None, mull=True):
    m = arch_mask(w, h, w // 2)
    put_mask(L, dilate(m, 1), x - 1, y - 1, frame, hgt=0.6)
    if lit is not None:
        put_mask(L, m, x, y, lit, hgt=0.3, em=lit)
    else:
        put_mask(L, m, x, y, glass, hgt=0.3)
        if refl is not None:
            L.px(x + w - 2, y + max(1, w // 2), refl)
            L.px(x + w - 2, y + max(2, w // 2) + 1, refl)
    if mull and w >= 5:
        L.vline(x + w // 2, y + 1, h - 1, frame, 0.5)


def make_station():
    """Neo-renaissance Hauptbahnhof Veltrava across the tracks (parallax 0.55).  Left wing x 330-640 with the
    clock tower x 470-510 (cam0 screen ~490: the vertical accent above the Soviet carriages), central hall
    x 640-816 with the big LIT arched window (cam640 screen ~376), right wing x 816-1120 ending in a domed
    corner pavilion.  Wing cornice y 128; arcades y 176-214 seen only through the island colonnade."""
    p = 0.55
    W = layer_w(p, 16)
    L = Layer(W, 360, 'station')
    B = 216
    # backlit by the low sun behind it: front faces in cool shade (slate), cornice tops and right edges
    # catch warm light (cream), snow on every ledge
    C = dict(deep=SL[1], sh=SL[2], body=SL[3], lit=SL[4], rim=CR[4], top=CR[3], hi=CR[3], joint=SL[2],
             roof=SL[1], roof_sh=SL[0], win=SL[0], glass=SL[0])
    CP = dict(sh=PA[1], body=PA[2], lit=PA[3], rim=PA[4], top=PA[4])
    E = {'chimneys': []}
    rng = np.random.default_rng(23)

    def wing(x0, x1, roof_y, seed, pavilion=None):
        rustication(L, x0, 178, x1 - x0, B - 178, C['body'], C['joint'], hi=C['lit'], course=5, seed=seed)
        for ax in range(x0 + 6, x1 - 16, 22):                  # ground-floor arcade
            put_mask(L, arch_mask(14, 32, 7), ax, 184, C['glass'], hgt=0.2)
            L.px(ax + 7, 183, C['hi'])
            L.vline(ax + 13, 188, 26, C['sh'])
            if rng.random() < 0.25:
                tiny_person(L, ax + 5, B - 1, 12, SL[1], head=CR[1])
        L.rect(x0 - 1, 173, x1 - x0 + 2, 5, C['lit'], hgt=0.7)
        L.hline(x0 - 1, 173, x1 - x0 + 2, C['hi'])
        L.hline(x0 - 1, 177, x1 - x0 + 2, C['sh'])
        snow_top(L, x0 - 1, 172, x1 - x0 + 2, [SN[1], SN[2]], depth=1, seed=seed)
        L.rect(x0, roof_y + 6, x1 - x0, 173 - roof_y - 6, C['body'], hgt=0.5)
        for yy in range(roof_y + 9, 173, 4):
            for xx in range(x0, x1):
                if (xx + yy // 4 * 3) % 9 == 0:
                    L.px(xx, yy, C['sh'])
        for k, wx in enumerate(range(x0 + 8, x1 - 12, 22)):
            _round_window(L, wx, roof_y + 14, 8, 20, C['lit'], C['win'], refl=SK[1])
            L.hline(wx - 2, roof_y + 35, 12, C['hi'])
            L.hline(wx - 2, roof_y + 12, 12, C['hi'])
            snow_top(L, wx - 2, roof_y + 34, 12, [SN[1], SN[2]], depth=1, seed=wx)
            if rng.random() < 0.07:
                put_mask(L, arch_mask(8, 20, 4)[3:, :], wx, roof_y + 17, LA[2], em=LA[2])
            if (k % 3) == 1:
                L.rect(wx + 13, roof_y + 8, 3, 165 - roof_y, C['lit'], hgt=0.6)
                L.vline(wx + 15, roof_y + 8, 165 - roof_y, C['rim'])
        L.vline(x0, roof_y + 6, B - roof_y - 6, C['sh'])
        L.vline(x1 - 1, roof_y + 6, B - roof_y - 6, C['rim'])
        L.rect(x0 - 2, roof_y + 3, x1 - x0 + 4, 4, C['lit'], hgt=0.7)       # main cornice
        L.hline(x0 - 2, roof_y + 3, x1 - x0 + 4, C['hi'])
        L.hline(x0 - 2, roof_y + 6, x1 - x0 + 4, C['sh'])
        for k in range(10):                                                  # hipped slate roof
            L.hline(x0 + k * 2, roof_y + 2 - k, x1 - x0 - k * 4, C['roof'] if k % 3 else C['roof_sh'], 0.62)
            L.px(x1 - 1 - k * 2, roof_y + 2 - k, SK[0])
        snow_top(L, x0 + 18, roof_y - 8, x1 - x0 - 36, [SN[0], SN[1], SN[2]], depth=2, seed=seed + 2)
        for k in range(2, 9, 2):
            for xx in range(x0 + k * 2, x1 - k * 2):
                if (xx * 7 + k) % 11 < 4:
                    L.px(xx, roof_y + 2 - k, SN[1])
        for k in range(4):                                                   # dormers
            dx = x0 + int((k + 0.5) * (x1 - x0) / 4) - 4
            L.rect(dx, roof_y - 5, 8, 7, C['lit'])
            put_mask(L, arch_mask(4, 6, 2), dx + 2, roof_y - 4, C['win'])
            L.hline(dx - 1, roof_y - 6, 10, SN[2])
        for k in range(2):                                                   # chimneys (smoke anchors)
            chx = x0 + 34 + k * (x1 - x0 - 68)
            L.rect(chx, roof_y - 15, 4, 11, C['sh'])
            L.vline(chx + 3, roof_y - 15, 11, C['rim'])
            L.hline(chx - 1, roof_y - 16, 6, SN[2])
            E['chimneys'].append((chx + 2, roof_y - 17))
        if pavilion:                                                         # domed corner pavilion
            px0 = pavilion
            tone_box(L, px0, roof_y - 10, 34, B - roof_y + 10, C, top=C['hi'])
            for yy in range(roof_y - 8, B, 6):
                L.hline(px0, yy, 34, C['joint'])
            for wy in (roof_y + 2, roof_y + 30):
                _round_window(L, px0 + 13, wy, 8, 18, C['lit'], C['win'], refl=SK[1])
            dome(L, px0 + 17, roof_y - 10, 15, 16, CP, lantern=6, drum=5)

    wing(330, 642, 128, 1)
    wing(814, 1120, 130, 2, pavilion=1086)
    # ---- clock tower: rusticated shaft, clock face, arched belfry, copper helm, flagstaff
    tx, tw = 470, 40
    rustication(L, tx, 64, tw, B - 64, C['body'], C['joint'], hi=C['lit'], course=6, block=(10, 14), seed=7)
    L.vline(tx, 64, B - 64, C['sh'])
    L.rect(tx + tw - 3, 64, 3, B - 64, C['lit'])
    L.vline(tx + tw - 1, 64, B - 64, C['rim'])
    for wy in (112, 142):
        _round_window(L, tx + 16, wy, 8, 18, C['lit'], C['win'], refl=SK[1])
    L.rect(tx - 2, 100, tw + 4, 4, C['lit'], hgt=0.7)
    L.hline(tx - 2, 100, tw + 4, C['hi'])
    snow_top(L, tx - 2, 99, tw + 4, [SN[1], SN[2]], depth=1, seed=8)
    ccx, ccy, cr = tx + tw // 2, 82, 9                                     # clock: Veltrava time 8:55
    L.ellipse(ccx, ccy, cr + 1.5, cr + 1.5, C['hi'], hgt=0.7)
    L.ellipse(ccx, ccy, cr, cr, CR[5], hgt=0.75, em=SN[1])
    for a in range(0, 360, 30):
        L.px(int(round(ccx + math.cos(math.radians(a)) * (cr - 1.6))),
             int(round(ccy + math.sin(math.radians(a)) * (cr - 1.6))), CR[1], em=SN[0])
    for ang, ln in ((math.radians(-90 + 8.92 * 30), 4.6), (math.radians(-90 + 55 * 6), 7.2)):
        for k in range(1, int(ln) + 1):
            L.px(int(round(ccx + 0.5 + math.cos(ang) * k)), int(round(ccy + 0.5 + math.sin(ang) * k)), NI[2],
                 em=SN[0])
    L.px(ccx, ccy, NI[2], em=SN[0])
    E['tower_clock'] = (ccx, ccy)
    L.rect(tx - 3, 60, tw + 6, 4, C['lit'], hgt=0.7)
    L.hline(tx - 3, 60, tw + 6, C['hi'])
    L.rect(tx + 2, 38, tw - 4, 22, C['body'], hgt=0.55)                    # belfry
    for k in range(3):
        put_mask(L, arch_mask(7, 16, 3), tx + 5 + k * 11, 42, SL[0], hgt=0.2)
    L.vline(tx + tw - 3, 38, 22, C['rim'])
    L.rect(tx, 35, tw, 3, C['lit'], hgt=0.7)
    L.hline(tx, 35, tw, C['hi'])
    snow_top(L, tx, 34, tw, [SN[1], SN[2], SN[3]], depth=1, seed=9)
    for k in range(18):                                                    # copper helm
        t = k / 17.0
        hw = (tw / 2 - 1) * (1 - t ** 1.7) + 1.5
        y = 34 - k
        x0, x1 = int(round(ccx - hw)), int(round(ccx + hw))
        for x in range(x0, x1):
            u = (x - ccx) / max(1.0, hw)
            c = CP['rim'] if x == x1 - 1 else (CP['lit'] if u > 0.4 else (CP['sh'] if u < -0.4 else CP['body']))
            L.px(x, y, c, 0.6)
        if k in (4, 10):
            L.hline(x0, y, x1 - x0, SN[2])
    cyl_normal(L, tx, 16, tw, 19)
    L.rect(ccx - 2, 10, 4, 7, CP['body'])
    L.vline(ccx + 1, 10, 7, CP['rim'])
    L.vline(ccx, 0, 10, IR[2])
    E['tower_flag'] = (ccx + 1, 0)
    # ---- central hall: gable front with the big lit arched window
    hx0, hx1 = 642, 814
    L.rect(hx0, 62, hx1 - hx0, B - 62, C['body'], hgt=0.5)
    rustication(L, hx0, 170, hx1 - hx0, B - 170, C['body'], C['joint'], hi=C['lit'], course=6, seed=12)
    for (px0, pw) in ((hx0, 20), (hx1 - 20, 20)):                          # corner piers with small domes
        L.rect(px0, 56, pw, B - 56, C['lit'], hgt=0.6)
        L.vline(px0, 56, B - 56, C['sh'])
        L.vline(px0 + pw - 1, 56, B - 56, C['rim'])
        for yy in range(58, B, 6):
            L.hline(px0, yy, pw, C['joint'])
        L.rect(px0 - 2, 48, pw + 4, 8, C['lit'])
        L.hline(px0 - 2, 48, pw + 4, C['hi'])
        snow_top(L, px0 - 2, 47, pw + 4, [SN[1], SN[2]], depth=1, seed=px0)
        dome(L, px0 + pw / 2, 47, pw / 2 - 1, 9, CP, lantern=5, ribs=False)
    wx0, wy0, ww, wh = hx0 + 36, 74, 100, 84
    m = arch_mask(ww, wh, ww // 2)
    put_mask(L, dilate(m, 3), wx0 - 3, wy0 - 3, C['hi'], hgt=0.65)
    put_mask(L, dilate(m, 1), wx0 - 1, wy0 - 1, C['sh'], hgt=0.6)
    yy, xx = np.mgrid[0:wh, 0:ww].astype(np.float32)
    glow = 1 - np.clip(np.sqrt(((xx - ww / 2) / (ww * 0.62)) ** 2 + ((yy - wh * 0.86) / (wh * 0.62)) ** 2), 0, 1)
    T = 0.3 + glow * 2.6
    ladder_paint(L, m, wx0, wy0, T * 0.85, [LA[0], LA[1], LA[2], LA[3]], steep=2.0, hgt=0.3)
    for k in range(-2, 3):                                                 # iron trusses inside (silhouette)
        L.line(wx0 + ww // 2 + k * 22, wy0 + 34, wx0 + ww // 2 + k * 12, wy0 + 10, LA[0])
    L.hline(wx0 + 3, wy0 + 58, ww - 6, LA[0])                              # gallery
    for k in range(4):                                                     # pendant lamps
        lx = wx0 + 18 + k * 22
        L.vline(lx, wy0 + 24, 12 + (k % 2) * 5, LA[0])
        L.rect(lx - 2, wy0 + 36 + (k % 2) * 5, 5, 2, LA[0])
        L.px(lx, wy0 + 38 + (k % 2) * 5, SN[4])
    for k in range(8):                                                     # travellers in the hall
        tiny_person(L, wx0 + 8 + k * 12, wy0 + wh - 2, 9 + (k % 3), LA[0], head=LA[1])
    for k in range(1, 5):                                                  # mullions
        L.vline(wx0 + k * ww // 5, wy0 + ww // 2 - 4, wh - ww // 2 + 4, SL[1], 0.55)
    for k in range(1, 4):
        L.hline(wx0, wy0 + ww // 2 - 4 + k * 12, ww, SL[1], 0.55)
    rcx, rcy = wx0 + ww / 2, wy0 + ww / 2
    for a in range(0, 181, 20):
        for r in range(7, ww // 2):
            px_ = int(round(rcx + math.cos(math.radians(180 + a)) * r))
            py_ = int(round(rcy + math.sin(math.radians(180 + a)) * r))
            if 0 <= py_ - wy0 < wh and 0 <= px_ - wx0 < ww and m[py_ - wy0, px_ - wx0]:
                L.px(px_, py_, SL[1])
    for r in (7, 26):
        for a in range(0, 181, 3):
            px_ = int(round(rcx + math.cos(math.radians(180 + a)) * r))
            py_ = int(round(rcy + math.sin(math.radians(180 + a)) * r))
            if 0 <= py_ - wy0 < wh and 0 <= px_ - wx0 < ww and m[py_ - wy0, px_ - wx0]:
                L.px(px_, py_, SL[1])
    sub = L.c[wy0:wy0 + wh, wx0:wx0 + ww]
    L.em[wy0:wy0 + wh, wx0:wx0 + ww][m] = sub[m]
    E['hall_window'] = (wx0, wy0, ww, wh)
    # pediment with the city arms (bridge with three arches over a wavy line) and the name
    L.rect(hx0 + 18, 56, hx1 - hx0 - 36, 8, C['lit'], hgt=0.7)
    L.hline(hx0 + 18, 56, hx1 - hx0 - 36, C['hi'])
    text_center(L, (hx0 + hx1) // 2, 58, 'VELTRAVA', C['sh'], font='s')
    for k in range(16):
        inset = int(k * 5.4)
        L.hline(hx0 + 18 + inset, 55 - k, hx1 - hx0 - 36 - 2 * inset, C['lit'] if k % 4 else C['hi'], 0.7)
        L.px(hx1 - 19 - inset, 55 - k, C['rim'])
    snow_top(L, hx0 + 20, 55 - 15, hx1 - hx0 - 40, [SN[1], SN[2], SN[3]], depth=1, seed=13)
    acx = (hx0 + hx1) // 2
    L.hline(acx - 8, 47, 17, C['hi'])
    for k in (-6, 0, 6):
        L.px(acx + k - 1, 48, C['hi'])
        L.px(acx + k + 1, 48, C['hi'])
    for k in range(-7, 8, 2):
        L.px(acx + k, 51 + (k // 2) % 2, C['hi'])
    for k in (-1, 1):
        L.rect(acx + k * 56 - 1, 34, 3, 6, C['lit'])                        # finial statues
        L.px(acx + k * 56, 33, C['hi'])
    for k in range(10):                                                    # barrel roof of the hall (patina)
        L.hline(hx0 + 20 + k, 61 - 16 - k, hx1 - hx0 - 40 - 2 * k, CP['body'] if k % 3 else CP['sh'], 0.6)
    fog_base(L, [SL[1], SL[2], SL[3], SL[4], SL[5]], 150, B + 6, 1.0)
    return L, E
