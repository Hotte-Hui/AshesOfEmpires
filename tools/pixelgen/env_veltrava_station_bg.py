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

SUN = (548, 158)                      # screen position of the hazy dawn sun (sky layer, parallax 0)
SKY_LADDER = [SL[1], SL[2], SL[3], SK[0], SK[1], SK[2], SK[3], SK[4], SK[5], LA[4], SN[4]]
SKY_STOPS = [(0, 0.55), (26, 1.1), (54, 1.9), (84, 2.8), (110, 3.75), (134, 4.7), (154, 5.6), (172, 6.5),
             (188, 7.25), (204, 7.75), (360, 7.8)]


def sky_index(y):
    return np.interp(y, [s[0] for s in SKY_STOPS], [s[1] for s in SKY_STOPS])


# =========================================================================== SKY (parallax 0)
def make_sky():
    W, H = layer_w(0.0), 360
    L = Layer(W, H, 'sky')
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    T = sky_index(yy)
    nz = value_noise(W, H // 5 + 2, 46, seed=11, octaves=2)
    band = np.repeat(nz, 5, axis=0)[:H]
    T += (band - 0.5) * 0.34 * np.clip((yy - 16) / 80, 0, 1) * (yy < 168)
    d = np.sqrt(((xx - SUN[0]) / 250.0) ** 2 + ((yy - SUN[1]) / 92.0) ** 2)
    T += np.clip(1 - d, 0, 1) ** 1.6 * 1.6
    d2 = np.sqrt(((xx - SUN[0]) / 70.0) ** 2 + ((yy - SUN[1]) / 28.0) ** 2)
    T += np.clip(1 - d2, 0, 1) ** 1.25 * 0.85
    hb = np.clip(1 - np.abs(yy - 190) / 16.0, 0, 1) * np.clip(1 - np.abs(xx - SUN[0]) / 330.0, 0, 1)
    T += hb * 0.75
    T = np.minimum(T, 8.85)
    dd = np.sqrt((xx - SUN[0]) ** 2 + ((yy - SUN[1]) * 1.1) ** 2)
    T[dd < 8.6] = np.maximum(T[dd < 8.6], 9.0)
    T[dd < 6.4] = 10.0
    for (ly, x0, x1, amt) in [(154, 470, 640, -1.3), (157, 500, 600, -0.8), (162, 430, 620, -1.1),
                              (149, 520, 610, -0.6), (167, 470, 590, -0.6), (171, 380, 560, -0.4)]:
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
    tone = np.full((h, w), 1.9, np.float32)
    tone[b1b & ~b1] = 1.2
    tone[b1] = 0.8
    tone[b2] = 0.25
    tone[b3] = -0.35
    cy_m = float(np.mean([c[1] for c in circles]))
    base = sky_index(cy_m) * 0.72 + sky_index(Y) * 0.28 - 0.35
    d = np.sqrt(((X - SUN[0]) / 290.0) ** 2 + ((Y - SUN[1]) / 120.0) ** 2)
    boost = np.clip(1 - d, 0, 1) ** 1.1 * (1.5 + sun_boost)
    T = np.minimum(base + tone + boost * np.clip(tone, 0, 2.0) * 0.72, 8.9)
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
    # high thin altocumulus (sparse, flat) under the canopy edge
    for i, (x, yb, w) in enumerate([(30, 46, 80), (250, 40, 70), (470, 52, 96), (360, 64, 44), (600, 44, 60)]):
        band_cloud(L, cloud_circles(rng, x, yb, w, 6, rmin=0.6, rmax=1.0), flat_bottom=yb, seed=100 + i, wisp=0.35)
    # stratocumulus banks in the middle sky; the right ones catch the dawn
    specs = [(-50, 112, 230, 30), (150, 92, 120, 20), (240, 128, 200, 28), (430, 102, 130, 22),
             (530, 136, 170, 20), (70, 146, 130, 14), (640, 118, 80, 18), (330, 76, 110, 14)]
    for i, (x, yb, w, h) in enumerate(specs):
        band_cloud(L, cloud_circles(rng, x, yb, w, h), flat_bottom=yb + 1, seed=200 + i, wisp=0.18)
    # low stratus streaks glowing near the sun
    for i, (x0, y, ln) in enumerate([(400, 150, 150), (500, 168, 160), (210, 166, 110), (590, 145, 80),
                                     (30, 158, 120)]):
        circ = [(x0 + k, y + math.sin(k / 17.0) * 1.4, 2.0 + 1.3 * math.sin(math.pi * k / ln)) for k in range(0, ln, 3)]
        band_cloud(L, circ, seed=300 + i, sun_boost=0.7)
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
    """Veltrava old town beyond the river, in deep haze.  Castle hill x 70-380 (cam0 left/centre), cathedral
    spires x 440-460, baroque domes x 40 / 545, the commission palais dome with flagpoles x 610 (cam0 right,
    cam640 above the station's right wing).  Base y 202."""
    p = 0.10
    W = layer_w(p, 16)
    L = Layer(W, 360, 'skyline')
    B = 202
    C = dict(deep=SK[0], sh=SK[0], body=SK[1], lit=SK[2], rim=SK[3], top=SK[3], roof=SK[0], roof_sh=SK[0],
             win=SK[0])
    CD = dict(C, sh=SK[0], body=PA[4], lit=SK[2], rim=SK[3])          # copper domes: a hint of patina
    rng = np.random.default_rng(5)
    # ---- castle hill: rounded mass with rock steps, the castle on the crown
    for x in range(40, 420):
        t = (x - 40) / 380.0
        hh = 70 * math.sin(math.pi * min(1, max(0, t))) ** 0.75 + 5 * math.sin(x / 9.0) + 3 * math.sin(x / 3.7)
        top = int(B - max(0, hh))
        for y in range(top, B):
            c = C['body'] if (x + y // 3) % 7 else C['sh']
            L.px(x, y, c, 0.4)
        if top < B:
            L.px(x, top, C['lit'] if x > 230 else C['body'])
    for (x0, x1, y) in [(150, 250, 150), (260, 330, 166), (90, 140, 176)]:     # terraces / walls
        L.hline(x0, y, x1 - x0, C['rim'])
        L.hline(x0, y + 1, x1 - x0, C['sh'])
    cx0 = 150
    tone_box(L, cx0, 126, 110, 22, C, top=C['top'])                          # castle range
    for k in range(cx0, cx0 + 110, 4):
        L.rect(k, 123, 2, 3, C['body'])
    for k in range(cx0 + 6, cx0 + 104, 9):
        L.rect(k, 132, 2, 4, C['win'])
    tone_box(L, 178, 96, 16, 30, C, top=C['top'])                            # keep
    for k in range(9):
        L.hline(178 + k, 95 - k, 16 - 2 * k, C['roof'] if k % 2 else C['lit'])
    L.vline(186, 80, 7, C['sh'])
    tone_box(L, 232, 108, 13, 18, C, top=C['top'])                           # round tower + cupola
    dome(L, 238.5, 108, 6.5, 6, C, lantern=4, ribs=False)
    tone_box(L, 204, 112, 20, 14, C)                                          # castle church
    gable_roof(L, 202, 111, 24, 8, C)
    spire(L, 220, 104, 5, 16, C)
    L.px(186, 135, LA[3], em=LA[3])
    L.px(242, 117, LA[3], em=LA[3])
    # ---- old town roofs along the river (dense band, gabled + hipped)
    x = -4
    while x < W:
        w = int(rng.integers(10, 26))
        h = int(rng.integers(10, 24))
        if 150 < x < 330:
            h = int(rng.integers(6, 12))
        tone_box(L, x, B - h, w, h, C, top=None)
        rise = int(rng.integers(3, 8))
        gable_roof(L, x - 1, B - h - 1, w + 2, rise, C)
        for wy in range(B - h + 3, B - 2, 4):
            for wx in range(x + 2, x + w - 2, 4):
                if rng.random() < 0.5:
                    L.px(wx, wy, C['win'])
        if rng.random() < 0.12:
            L.px(x + w // 2, B - h + 4, LA[3], em=LA[3])
        x += w + int(rng.integers(-2, 2))
    # ---- western baroque church (dome x 40)
    tone_box(L, 26, 150, 30, 52, C, top=C['top'])
    dome(L, 41, 150, 11, 12, CD, lantern=6, drum=8)
    # ---- Gothic cathedral: long nave + two west spires
    tone_box(L, 400, 150, 70, 52, C, top=C['top'])
    gable_roof(L, 398, 149, 50, 10, C)
    for k in range(404, 468, 7):
        L.rect(k, 160, 3, 12, C['win'])
        L.px(k + 1, 159, C['win'])
    for sx in (446, 462):
        tone_box(L, sx - 5, 128, 10, 74, C, top=C['top'])
        spire(L, sx, 128, 11, 46, C)
        L.rect(sx - 2, 136, 3, 8, C['win'])
        for k in range(4):                                                    # crockets
            L.px(sx - 4 + k * 3, 127 - k * 2, C['rim'])
    # ---- baroque dome east (x 545)
    tone_box(L, 528, 150, 34, 52, C, top=C['top'])
    dome(L, 545, 150, 13, 14, CD, lantern=7, drum=10)
    for sx in (531, 559):
        tone_box(L, sx - 3, 132, 6, 18, C)
        dome(L, sx, 132, 3.5, 4, C, lantern=2, ribs=False)
    # ---- the commission palais (former Kurhaus): broad block, flat dome, six flagpoles
    tone_box(L, 588, 158, 74, 44, C, top=C['top'])
    for k in range(592, 660, 6):
        L.rect(k, 166, 3, 8, C['win'])
        L.rect(k, 180, 3, 8, C['win'])
    L.px(604, 168, LA[3], em=LA[3])
    L.px(634, 182, LA[3], em=LA[3])
    tone_box(L, 606, 146, 38, 12, C, top=C['top'])
    dome(L, 625, 146, 17, 13, CD, lantern=5, drum=0)
    flag_cols = [SL[3], RD[2], IR[1], SL[3], RD[3], SN[3]]                    # tiny cloth, no insignia at 3 px
    for i, fx in enumerate((590, 600, 610, 640, 650, 660)):
        L.vline(fx, 144, 14, C['sh'])
        L.rect(fx + 1, 144, 3, 2, flag_cols[i])
    # ---- radio mast and a far chimney (east)
    L.vline(700, 120, 82, C['sh'])
    for y in range(124, 200, 6):
        L.px(699, y, C['sh'])
        L.px(701, y, C['sh'])
    L.px(700, 119, RD[2], em=RD[2])
    tone_box(L, 724, 160, 6, 42, C)
    # haze toward the base (the river mist)
    fog_base(L, [SK[0], SK[1], SK[2], SK[3], SK[4]], B - 30, B + 1, 1.6)
    return L


# =========================================================================== MANSARD CITY (parallax 0.30)
def make_city():
    """Gründerzeit blocks with mansard roofs between the station and the old town: slate roofs with snow,
    copper-green corner domes and turrets, chimneys (smoke fx anchors returned).  Base y 210 (hidden by the
    station building / trains), roofs 130..170.  A copper onion-dome church x 300 (cam0), corner dome x 590."""
    p = 0.30
    W = layer_w(p, 16)
    L = Layer(W, 360, 'city')
    B = 212
    C = dict(deep=SL[2], sh=SL[3], body=SL[4], lit=SK[1], rim=SK[2], top=SK[2], roof=SL[2], roof_sh=SL[1],
             win=SL[2], snow=SN[1])
    CF = dict(C, sh=SL[3], body=CR[2], lit=CR[3], rim=CR[4])                   # cream façades catching dawn
    CP = dict(C, sh=PA[1], body=PA[2], lit=PA[3], rim=PA[4])                   # copper patina
    rng = np.random.default_rng(17)
    chimneys = []
    x = -6
    i = 0
    while x < W:
        w = int(rng.integers(44, 86))
        h = int(rng.integers(34, 58))
        if 260 < x < 340:
            h = int(rng.integers(26, 34))
        face = CF if i % 3 == 1 else C
        y = B - h
        tone_box(L, x, y, w, h, face, top=face['top'])
        for fl in range(3):
            wy = y + 4 + fl * 9
            if wy > B - 6:
                break
            for wx in range(x + 3, x + w - 3, 6):
                L.rect(wx, wy, 3, 5, face['win'] if face is C else SL[2], hgt=0.3)
                L.px(wx + 2, wy, face['rim'])
                if rng.random() < 0.035:
                    L.rect(wx, wy + 1, 3, 4, LA[2], em=LA[2])
        L.hline(x, y, w, SN[1])
        hr = int(rng.integers(8, 13))
        mansard(L, x + 1, y - hr, w - 2, hr, dict(C, rim=C['rim']), snow=SN[1], dormers=max(1, w // 18), seed=x)
        for k in range(int(rng.integers(1, 4))):
            chx = x + 6 + int(rng.integers(0, max(1, w - 12)))
            chh = int(rng.integers(5, 10))
            L.rect(chx, y - hr - chh, 3, chh, C['sh'])
            L.px(chx + 2, y - hr - chh, C['rim'])
            L.hline(chx - 1, y - hr - chh - 1, 5, SN[1])
            chimneys.append((chx + 1, y - hr - chh - 2))
        if rng.random() < 0.4:            # corner turret with a small copper helm
            tx = x + w - 10
            tone_box(L, tx, y - hr - 6, 9, hr + 6, face)
            dome(L, tx + 4.5, y - hr - 6, 5, 7, CP, lantern=3, ribs=False)
        x += w + int(rng.integers(0, 6))
        i += 1
    # copper onion dome church (cam 0, between castle hill and station tower)
    tone_box(L, 286, 150, 30, 62, CF, top=CF['top'])
    for k in (292, 302):
        L.rect(k, 160, 4, 14, SL[2])
        L.px(k + 1, 159, SL[2])
    tone_box(L, 292, 128, 18, 22, CF, top=CF['top'])
    dome(L, 301, 128, 9, 11, CP, lantern=6, onion=True)
    L.rect(296, 136, 3, 6, SL[2])
    L.rect(303, 136, 3, 6, SL[2])
    # big corner dome of a bank / hotel (cam 640 right, 'Hotel an der Linie')
    tone_box(L, 572, 148, 40, 64, CF, top=CF['top'])
    dome(L, 592, 148, 16, 15, CP, lantern=7, drum=7)
    for wy in range(156, 206, 10):
        for wx in range(576, 610, 7):
            L.rect(wx, wy, 3, 6, SL[2])
    L.rect(583, 166, 3, 6, LA[2], em=LA[2])
    # a brewery chimney (east) and a church tower (west)
    tone_box(L, 860, 106, 7, 106, dict(C, body=SL[3], sh=SL[2], rim=SK[1]))
    L.hline(859, 106, 9, SL[2])
    chimneys.append((863, 104))
    tone_box(L, 120, 136, 16, 76, CF, top=CF['top'])
    dome(L, 128, 136, 8, 8, CP, lantern=8, onion=True)
    fog_base(L, [SL[2], SL[3], SL[4], SK[1], SK[2], SK[3]], 150, B + 2, 2.2)
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
    """Neo-renaissance Hauptbahnhof Veltrava across the tracks.  Clock tower x 434-474 (cam0 screen ~450,
    rises above the Soviet carriages), left wing x 300-600, central hall x 600-776 with the BIG LIT arched
    window (cam640 screen ~335), right wing x 776-1086 with a corner pavilion.  Base y 214 (hidden)."""
    p = 0.55
    W = layer_w(p, 16)
    L = Layer(W, 360, 'station')
    B = 214
    C = dict(deep=CR[0], sh=CR[1], body=CR[2], lit=CR[3], rim=CR[4], top=CR[4], hi=CR[5], joint=CR[1],
             roof=SL[2], roof_sh=SL[1], win=SL[1], glass=NI[3])
    CP = dict(sh=PA[1], body=PA[2], lit=PA[3], rim=PA[4], top=PA[4])
    E = {}
    rng = np.random.default_rng(23)

    def wing(x0, x1, roof_y, seed, pavilion=None):
        # ground-floor arcade (mostly hidden by the far train / island canopy)
        rustication(L, x0, 176, x1 - x0, B - 176, C['body'], C['joint'], hi=C['lit'], course=5, seed=seed)
        for ax in range(x0 + 6, x1 - 16, 22):
            m = arch_mask(14, 30, 7)
            put_mask(L, m, ax, 182, C['glass'], hgt=0.2)
            L.px(ax + 7, 181, C['hi'])                       # keystone
            L.vline(ax + 13, 186, 26, C['sh'])
        L.rect(x0 - 1, 171, x1 - x0 + 2, 5, C['lit'], hgt=0.7)  # string course
        L.hline(x0 - 1, 171, x1 - x0 + 2, C['hi'])
        L.hline(x0 - 1, 175, x1 - x0 + 2, C['sh'])
        snow_top(L, x0 - 1, 170, x1 - x0 + 2, [SN[1], SN[2]], depth=1, seed=seed)
        # piano nobile: arched windows with aedicules
        L.rect(x0, roof_y + 6, x1 - x0, 171 - roof_y - 6, C['body'], hgt=0.5)
        for yy in range(roof_y + 8, 171, 4):
            for xx in range(x0, x1):
                if (xx + yy // 4 * 3) % 9 == 0:
                    L.px(xx, yy, C['sh'])
        for k, wx in enumerate(range(x0 + 8, x1 - 12, 22)):
            _round_window(L, wx, roof_y + 14, 8, 18, C['lit'], C['win'], refl=SK[1])
            L.hline(wx - 2, roof_y + 33, 12, C['hi'])          # sill
            L.hline(wx - 2, roof_y + 12, 12, C['hi'])          # cornice cap
            snow_top(L, wx - 2, roof_y + 32, 12, [SN[1], SN[2]], depth=1, seed=wx)
            if rng.random() < 0.08:
                put_mask(L, arch_mask(8, 18, 4)[2:, :], wx, roof_y + 16, LA[2], em=LA[2])
            if (k % 3) == 1:                                   # pilaster
                L.rect(wx + 13, roof_y + 8, 3, 163 - roof_y, C['lit'], hgt=0.6)
                L.vline(wx + 15, roof_y + 8, 163 - roof_y, C['rim'])
        L.vline(x0, roof_y + 6, B - roof_y - 6, C['sh'])
        L.vline(x1 - 1, roof_y + 6, B - roof_y - 6, C['rim'])
        # main cornice + balustrade + hipped slate roof with snow
        L.rect(x0 - 2, roof_y + 3, x1 - x0 + 4, 4, C['lit'], hgt=0.7)
        L.hline(x0 - 2, roof_y + 3, x1 - x0 + 4, C['hi'])
        L.hline(x0 - 2, roof_y + 6, x1 - x0 + 4, C['sh'])
        for k in range(10):
            L.hline(x0 + k * 2, roof_y + 2 - k, x1 - x0 - k * 4, C['roof'] if k % 3 else C['roof_sh'], 0.62)
            L.px(x1 - 1 - k * 2, roof_y + 2 - k, SK[0])
        snow_top(L, x0 + 18, roof_y - 8, x1 - x0 - 36, [SN[0], SN[1], SN[2]], depth=2, seed=seed + 2)
        for k in range(2, 9, 2):
            for xx in range(x0 + k * 2, x1 - k * 2):
                if (xx * 7 + k) % 11 < 4:
                    L.px(xx, roof_y + 2 - k, SN[1])
        for k in range(3):                                    # dormers
            dx = x0 + int((k + 0.5) * (x1 - x0) / 3) - 4
            L.rect(dx, roof_y - 5, 8, 7, C['lit'])
            put_mask(L, arch_mask(4, 6, 2), dx + 2, roof_y - 4, C['win'])
            L.hline(dx - 1, roof_y - 6, 10, SN[2])
        for k in range(2):                                    # chimneys
            chx = x0 + 30 + k * (x1 - x0 - 60)
            L.rect(chx, roof_y - 14, 4, 10, C['sh'])
            L.vline(chx + 3, roof_y - 14, 10, C['rim'])
            L.hline(chx - 1, roof_y - 15, 6, SN[2])
            E.setdefault('chimneys', []).append((chx + 2, roof_y - 16))
        if pavilion:                                          # corner pavilion with a copper dome
            px0 = pavilion
            tone_box(L, px0, roof_y - 8, 34, B - roof_y + 8, C, top=C['hi'])
            for wy in (roof_y + 2, roof_y + 30):
                _round_window(L, px0 + 13, wy, 8, 16, C['lit'], C['win'], refl=SK[1])
            dome(L, px0 + 17, roof_y - 8, 15, 16, CP, lantern=6, drum=5)

    wing(300, 602, 136, 1)
    wing(776, 1086, 140, 2, pavilion=1052)
    # ---- clock tower (cam 0 accent): rusticated shaft, clock face, arched belfry, copper helm, flag
    tx, tw = 434, 40
    rustication(L, tx, 66, tw, B - 66, C['body'], C['joint'], hi=C['lit'], course=6, block=(10, 14), seed=7)
    L.vline(tx, 66, B - 66, C['sh'])
    L.rect(tx + tw - 3, 66, 3, B - 66, C['lit'])
    L.vline(tx + tw - 1, 66, B - 66, C['rim'])
    for wy in (120, 150):
        _round_window(L, tx + 16, wy, 8, 16, C['lit'], C['win'], refl=SK[1])
    L.rect(tx - 2, 104, tw + 4, 4, C['lit'], hgt=0.7)
    L.hline(tx - 2, 104, tw + 4, C['hi'])
    snow_top(L, tx - 2, 103, tw + 4, [SN[1], SN[2]], depth=1, seed=8)
    # clock face (station time 8:55 Veltrava)
    ccx, ccy, cr = tx + tw // 2, 86, 9
    L.ellipse(ccx, ccy, cr + 1.5, cr + 1.5, C['hi'], hgt=0.7)
    L.ellipse(ccx, ccy, cr, cr, CR[5], hgt=0.75, em=SN[2])
    for a in range(0, 360, 30):
        L.px(int(round(ccx + math.cos(math.radians(a)) * (cr - 1.6))), int(round(ccy + math.sin(math.radians(a)) * (cr - 1.6))),
             NI[2], em=SN[1])
    for ang, ln in ((math.radians(-90 + 8.92 * 30), 4.6), (math.radians(-90 + 55 * 6), 7.2)):   # hour / minute
        for k in range(1, int(ln) + 1):
            L.px(int(round(ccx + 0.5 + math.cos(ang) * k)) - 0, int(round(ccy + 0.5 + math.sin(ang) * k)) - 0, NI[1],
                 em=SN[0])
    L.px(ccx, ccy, NI[1], em=SN[0])
    E['tower_clock'] = (ccx, ccy)
    # belfry with three arches + balcony
    L.rect(tx - 3, 62, tw + 6, 4, C['lit'], hgt=0.7)
    L.hline(tx - 3, 62, tw + 6, C['hi'])
    L.rect(tx + 2, 40, tw - 4, 22, C['body'], hgt=0.55)
    for k in range(3):
        put_mask(L, arch_mask(7, 16, 3), tx + 5 + k * 11, 44, NI[3], hgt=0.2)
    L.vline(tx + tw - 3, 40, 22, C['rim'])
    L.rect(tx, 37, tw, 3, C['lit'], hgt=0.7)
    L.hline(tx, 37, tw, C['hi'])
    snow_top(L, tx, 36, tw, [SN[1], SN[2], SN[3]], depth=1, seed=9)
    # copper helm (bell roof) + lantern + flagpole
    for k in range(18):
        t = k / 17.0
        hw = (tw / 2 - 1) * (1 - t ** 1.7) + 1.5
        y = 36 - k
        x0, x1 = int(round(ccx - hw)), int(round(ccx + hw))
        for x in range(x0, x1):
            u = (x - ccx) / max(1.0, hw)
            c = CP['rim'] if x == x1 - 1 else (CP['lit'] if u > 0.4 else (CP['sh'] if u < -0.4 else CP['body']))
            L.px(x, y, c, 0.6)
        if k in (4, 10):
            L.hline(x0, y, x1 - x0, SN[2])
    cyl_normal(L, tx, 18, tw, 19)
    L.rect(ccx - 2, 12, 4, 7, CP['body'])
    L.vline(ccx + 1, 12, 7, CP['rim'])
    L.vline(ccx, 0, 12, IR[2])
    E['tower_flag'] = (ccx + 1, 1)
    # ---- central hall: tall gable front with the big lit arched window (iron mullions, lamps inside)
    hx0, hx1 = 600, 776
    L.rect(hx0, 64, hx1 - hx0, B - 64, C['body'], hgt=0.5)
    rustication(L, hx0, 168, hx1 - hx0, B - 168, C['body'], C['joint'], hi=C['lit'], course=6, seed=12)
    for (px0, pw) in ((hx0, 20), (hx1 - 20, 20)):                       # corner piers
        L.rect(px0, 58, pw, B - 58, C['lit'], hgt=0.6)
        L.vline(px0, 58, B - 58, C['sh'])
        L.vline(px0 + pw - 1, 58, B - 58, C['rim'])
        for yy in range(60, B, 6):
            L.hline(px0, yy, pw, C['joint'])
        L.rect(px0 - 2, 50, pw + 4, 8, C['lit'])
        L.hline(px0 - 2, 50, pw + 4, C['hi'])
        dome(L, px0 + pw / 2, 50, pw / 2 - 1, 9, CP, lantern=5, ribs=False)
    # the window: 120 x 92, semicircular head, radial + grid mullions, warm glow, interior silhouettes
    wx0, wy0, ww, wh = hx0 + 28, 70, 120, 94
    m = arch_mask(ww, wh, ww // 2)
    put_mask(L, dilate(m, 3), wx0 - 3, wy0 - 3, C['hi'], hgt=0.65)
    put_mask(L, dilate(m, 1), wx0 - 1, wy0 - 1, C['sh'], hgt=0.6)
    yy, xx = np.mgrid[0:wh, 0:ww].astype(np.float32)
    glow = 1 - np.clip(np.sqrt(((xx - ww / 2) / (ww * 0.6)) ** 2 + ((yy - wh * 0.72) / (wh * 0.75)) ** 2), 0, 1)
    T = 0.4 + glow * 3.2
    lad = [LA[0], LA[1], LA[2], LA[3], LA[4]]
    ladder_paint(L, m, wx0, wy0, T, lad, steep=2.0, hgt=0.3)
    # interior: hall trusses + hanging lamps + a gallery line, as warm-shadow shapes
    for k in range(-2, 3):
        L.line(wx0 + ww // 2 + k * 26, wy0 + 30, wx0 + ww // 2 + k * 14, wy0 + 8, LA[1])
    L.hline(wx0 + 4, wy0 + 62, ww - 8, LA[1])
    for k in range(5):
        lx = wx0 + 16 + k * 22
        L.vline(lx, wy0 + 20, 12 + (k % 2) * 6, LA[0])
        L.rect(lx - 2, wy0 + 32 + (k % 2) * 6, 5, 2, LA[0])
        L.px(lx, wy0 + 34 + (k % 2) * 6, SN[4])
    for k in range(9):                                                      # people in the hall (tiny)
        tiny_person(L, wx0 + 8 + k * 13, wy0 + wh - 2, 9 + (k % 3), LA[0], head=LA[1])
    # mullions: grid + radial in the head
    for k in range(1, 6):
        L.vline(wx0 + k * ww // 6, wy0 + ww // 2 - 6, wh - ww // 2 + 6, NI[3], 0.55)
    for k in range(1, 5):
        L.hline(wx0, wy0 + ww // 2 - 6 + k * 13, ww, NI[3], 0.55)
    rcx, rcy = wx0 + ww / 2, wy0 + ww / 2
    for a in range(0, 181, 20):
        for r in range(8, ww // 2):
            px_ = int(round(rcx + math.cos(math.radians(180 + a)) * r))
            py_ = int(round(rcy + math.sin(math.radians(180 + a)) * r))
            if 0 <= py_ - wy0 < wh and 0 <= px_ - wx0 < ww and m[py_ - wy0, px_ - wx0]:
                L.px(px_, py_, NI[3])
    for r in (8, 30):
        for a in range(0, 181, 3):
            px_ = int(round(rcx + math.cos(math.radians(180 + a)) * r))
            py_ = int(round(rcy + math.sin(math.radians(180 + a)) * r))
            if 0 <= py_ - wy0 < wh and 0 <= px_ - wx0 < ww and m[py_ - wy0, px_ - wx0]:
                L.px(px_, py_, NI[3])
    sub = L.c[wy0:wy0 + wh, wx0:wx0 + ww]
    L.em[wy0:wy0 + wh, wx0:wx0 + ww][m] = sub[m]
    E['hall_window'] = (wx0, wy0, ww, wh)
    # pediment with the city arms and the station name
    L.rect(hx0 + 18, 58, hx1 - hx0 - 36, 8, C['lit'], hgt=0.7)
    L.hline(hx0 + 18, 58, hx1 - hx0 - 36, C['hi'])
    text_center(L, (hx0 + hx1) // 2, 60, 'VELTRAVA', C['sh'], font='s')
    for k in range(16):
        inset = int(k * 5.5)
        L.hline(hx0 + 18 + inset, 57 - k, hx1 - hx0 - 36 - 2 * inset, C['lit'] if k % 4 else C['hi'], 0.7)
        L.px(hx1 - 19 - inset, 57 - k, C['rim'])
    snow_top(L, hx0 + 20, 57 - 15, hx1 - hx0 - 40, [SN[1], SN[2], SN[3]], depth=1, seed=13)
    acx = (hx0 + hx1) // 2                                                  # bridge arms in relief
    L.hline(acx - 8, 50, 17, C['hi'])
    for k in (-6, 0, 6):
        L.px(acx + k - 1, 51, C['hi'])
        L.px(acx + k + 1, 51, C['hi'])
    for k in range(-7, 8, 2):
        L.px(acx + k, 53 + (k // 2) % 2, C['hi'])
    for k in range(-1, 2):                                                  # finial statues
        L.rect(acx + k * 60 - 1, 34 + abs(k) * 12, 3, 6, C['lit'])
    # barrel roof of the hall behind the gable (patina)
    for k in range(10):
        L.hline(hx0 + 20 + k, 63 - 16 - k, hx1 - hx0 - 40 - 2 * k, CP['body'] if k % 3 else CP['sh'], 0.6)
    fog_base(L, [CR[1], CR[2], CR[3], CR[4]], 120, B + 6, 0.8)
    # light haze over the whole building (it stands ~60 m away): one step toward the sky
    ladder_shift(L, [SL[1], SL[2], SL[3], SL[4], SK[1]], 0.5)
    return L, E
