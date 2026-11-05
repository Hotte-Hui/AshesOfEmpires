"""env_veltrava_hall_ext -- what L_C3_Hall shows through its glass (unlit parallax layers).

ext_sky    (p 0.04)  overcast winter morning, pale toward the horizon (all windows)
ext_square (p 0.30)  the snowy square in front of the palais: stucco houses, tram stop, lamp post,
                     two waiting figures (seen through the entrance glazing)
ext_town   (p 0.12)  the far river bank: the Line -- double fence, watchtowers, floodlight masts, haze
ext_river  (p 0.20)  the frozen river with the three-arched bridge, old-town roofs, dome and spire
                     (seen through the tall foyer window and the office window)
saal_far   (p 0.46)  the Grosser Saal's head wall: tall windows, panelling, the six flags on the dais,
                     chandeliers   (+ saal_far_hist.png with the historical USSR / Reich flags)
saal_near  (p 0.66)  the horseshoe table seen from the booths, tiny delegates, the secretariat table
Exterior layers use the Veltrava town palette (c3.json 'veltrava'), the Saal layers the 'palais' palette.
"""
from __future__ import annotations

import math

import numpy as np

import env_veltrava_hall_kit as kit
import env_veltrava_hall_layout as L
import pg

RV = kit.velt_ramps()
RP = kit.palais_ramps()


def ext_layer(name, p, x0_world_needed, width, height=L.WORLD_H, ramps=RV):
    lay = kit.TLayer(width, height, ramps, name)
    lay.unlit[:] = True
    return lay


# =========================================================================== sky
def build_sky():
    w = L.layer_width(L.PARALLAX['ext_sky'])
    lay = kit.TLayer(w, L.WORLD_H, RV, 'ext_sky')
    H = L.WORLD_H
    y = np.arange(H, dtype=np.float32)[:, None] + np.zeros((1, w), np.float32)
    xs = np.arange(w, dtype=np.float32)[None, :]
    # overcast: slate-lilac at the top, pale milky toward the horizon; a diffuse brighter patch where
    # the winter sun stands behind the cloud deck (upper left)
    t = 0.6 + np.clip((y - 10) / 190, 0, 1) ** 0.8 * 4.6
    glow = np.exp(-(((xs - 150) / 260) ** 2 + ((y - 90) / 120) ** 2)) * 0.9
    t = t + glow
    lay.put(np.ones((H, w), bool), 0, 0, 'SKY', np.clip(t, 0, 6), flat=False)
    rng = np.random.default_rng(5)
    for (by, th, x0, ln) in [(46, 2, -20, 300), (62, 3, 260, 360), (84, 2, 40, 240), (102, 3, 420, 300),
                             (126, 2, 120, 330), (150, 3, 500, 240), (170, 2, -10, 280)]:
        nz = pg.value_noise(ln + 2, 1, 16, int(rng.integers(0, 999)), octaves=2)[0]
        for i in range(ln):
            x = x0 + i
            if not 0 <= x < w:
                continue
            e = math.sin(math.pi * i / ln) ** 0.6
            hh = max(1, int(round(th * e * (0.6 + nz[i]))))
            base = float(np.clip(0.6 + (by - 10) / 190 * 4.6, 0, 6))
            lay.rect(x, by - hh, 1, hh, 'SKY', max(0.0, base - 0.9), flat=True)
            lay.px(x, by, 'SKY', min(6.0, base + 0.6), flat=True)
    lay.unlit[:] = True
    lay.resolve(band=3.0)
    return lay


# =========================================================================== the square
SQ_POS = -80


def facade(lay, x0, x1, cornice, rng, tone=4.2, lit_p=0.12, shop=False, dome=False):
    W = x1 - x0
    bot = 262
    lay.rect(x0, cornice, W, bot - cornice, 'STONE', tone)
    lay.rect(x0, cornice, 1, bot - cornice, 'STONE', tone + 0.8)
    lay.rect(x1 - 1, cornice, 1, bot - cornice, 'STONE', tone - 1.2)
    # cornice with snow
    lay.rect(x0 - 2, cornice - 4, W + 4, 4, 'STONE', tone + 0.6)
    lay.rect(x0 - 2, cornice - 5, W + 4, 1, 'SNOW', 4.0)
    lay.rect(x0 - 2, cornice - 1, W + 4, 1, 'STONE', tone - 1.6)
    # windows: three storeys of tall windows with stucco hoods and snowy sills
    ww, wh, gap = 6, 16, 8
    n = max(1, (W - 6) // (ww + gap))
    ox = x0 + (W - (n * ww + (n - 1) * gap)) // 2
    for row in range(3):
        wy = cornice + 10 + row * 34
        for i in range(n):
            wx = ox + i * (ww + gap)
            lay.rect(wx - 2, wy - 4, ww + 4, 2, 'STONE', tone + 1.0)
            lay.rect(wx - 2, wy - 5, ww + 4, 1, 'SNOW', 3.4)
            lay.rect(wx - 1, wy - 1, ww + 2, wh + 2, 'STONE', tone + 0.4)
            if rng.random() < lit_p:
                lay.rect(wx, wy, ww, wh, 'LAMP', 2.0, emis=True)
                lay.rect(wx, wy, ww, 2, 'LAMP', 1.0, emis=True)
                lay.rect(wx + ww // 2, wy, 1, wh, 'LAMP', 0.6, emis=True)
            else:
                lay.rect(wx, wy, ww, wh, 'ROOF', 2.0 + rng.random() * 1.6)
                lay.rect(wx + ww // 2, wy, 1, wh, 'STONE', tone - 0.8)
                lay.px(wx, wy, 'SKY', 3.0)
                lay.px(wx + 1, wy, 'SKY', 2.4)
            lay.rect(wx - 1, wy + wh + 1, ww + 2, 1, 'SNOW', 4.4)
    # ground floor: shop front or arcade
    gy = bot - 26
    lay.rect(x0, gy, W, 26, 'STONE', tone - 0.8)
    if shop:
        lay.rect(x0 + 4, gy + 6, W - 8, 16, 'LAMP', 2.4, emis=True)        # lit café window
        lay.rect(x0 + 4, gy + 6, W - 8, 2, 'LAMP', 1.2, emis=True)
        for k in range(x0 + 10, x1 - 6, 10):
            lay.rect(k, gy + 6, 1, 16, 'ROOF', 2.0)
        lay.rect(x0 + 2, gy + 1, W - 4, 4, 'RED', 2.4)                      # awning
        for k in range(x0 + 2, x1 - 2, 4):
            lay.rect(k, gy + 1, 2, 4, 'RED', 3.2)
        lay.rect(x0 + 2, gy, W - 4, 1, 'SNOW', 4.4)
    else:
        for k in range(x0 + 4, x1 - 8, 14):
            lay.rect(k, gy + 4, 8, 22, 'ROOF', 1.6)
            lay.rect(k, gy + 4, 8, 4, 'STONE', tone - 1.4)
    # roof: mansard with dormers, patina dome on a corner house
    rt = cornice - 5
    if dome:
        cx = (x0 + x1) // 2
        m, mx, my = lay.ellipse(cx, rt, W / 2.6, 22, 'PAT', 3.0)
        rows = np.arange(m.shape[0])[:, None] + my
        lay.put(m & (rows >= rt), mx, my, 'STONE', tone)                 # (hidden by facade below)
        for a in np.linspace(-0.8, 0.8, 7):
            for yv in np.linspace(-1, -0.05, 20):
                xv = a * math.sqrt(max(0.0, 1 - yv * yv))
                lay.px(int(round(cx + xv * W / 2.6)), int(round(rt + yv * 22)), 'PAT', 1.6 if a > 0 else 4.0)
        lay.rect(cx - 2, rt - 30, 5, 8, 'PAT', 2.4)
        lay.rect(cx, rt - 34, 1, 4, 'IRON', 2.0)
        lay.rect(cx - 9, rt - 24, 18, 2, 'SNOW', 4.4)
        lay.rect(x0, rt, W, 5, 'STONE', tone - 0.4)
        return
    steep = 16
    lay.poly([(x0 - 1, rt), (x1, rt), (x1 - 4, rt - steep), (x0 + 3, rt - steep)], 'ROOF', 3.0)
    lay.rect(x0 + 3, rt - steep - 5, W - 7, 5, 'ROOF', 2.0)
    for yy in range(rt - steep + 2, rt, 3):
        lay.rect(x0 + 1, yy, W - 2, 1, 'ROOF', 2.2)
    lay.rect(x0 + 3, rt - steep - 6, W - 7, 2, 'SNOW', 4.0)
    lay.rect(x0 + 2, rt - steep, W - 4, 1, 'SNOW', 3.4)
    for dx in range(x0 + 8, x1 - 10, 22):
        lay.rect(dx, rt - steep + 3, 8, steep - 4, 'STONE', tone - 0.6)
        lay.poly([(dx - 1, rt - steep + 3), (dx + 8, rt - steep + 3), (dx + 3, rt - steep - 2)], 'ROOF', 3.4)
        lay.line(dx - 1, rt - steep + 3, dx + 3, rt - steep - 2, 'SNOW', 4.4)
        lay.line(dx + 4, rt - steep - 2, dx + 8, rt - steep + 3, 'SNOW', 3.6)
        lay.rect(dx + 2, rt - steep + 5, 4, 5, 'ROOF', 1.4)
    for k in range(int(rng.integers(1, 3))):
        cx = x0 + int(rng.integers(6, max(7, W - 10)))
        top = rt - steep - 5
        lay.rect(cx, top - 12, 5, 13, 'STONE', 2.4)
        lay.rect(cx - 1, top - 14, 7, 2, 'STONE', 3.0)
        lay.rect(cx - 1, top - 15, 7, 1, 'SNOW', 4.4)
        for j in range(6):                                                  # thin chimney smoke
            lay.rect(cx + 1 + j * 2, top - 18 - j * 3 - (j * j) // 3, 3 + j // 2, 2, 'HAZE', 5.0 - j * 0.3)


def build_square():
    w = 260
    lay = kit.TLayer(w, L.WORLD_H, RV, 'ext_square')
    rng = np.random.default_rng(23)
    plan = [(-6, 40, 112, 4.0, 0.10, False, False), (40, 112, 96, 4.6, 0.16, True, False),
            (112, 150, 124, 3.6, 0.08, False, True), (150, 214, 100, 4.4, 0.14, False, False),
            (214, 266, 108, 3.8, 0.1, False, False)]
    for (x0, x1, cor, tone, lp, shop, dome) in plan:
        facade(lay, x0, x1, cor, rng, tone=tone, lit_p=lp, shop=shop, dome=dome)
    # the square: snow over cobbles, tram tracks, footprints, a kerb of shovelled snow
    gy0 = 262
    t = 4.2 + (pg.value_noise(w, L.WORLD_H - gy0, 9, 4, octaves=2) - 0.5) * 0.9
    lay.put(np.ones((L.WORLD_H - gy0, w), bool), 0, gy0, 'SNOW', t, flat=False)
    lay.rect(0, gy0, w, 2, 'SNOW', 2.4)
    for ty in (270, 274, 280, 286):
        for x in range(0, w):
            if (x + ty) % 7 != 0:
                lay.px(x, ty, 'IRON', 3.0 if ty < 280 else 2.4)
    for k in range(26):                                                    # footprints
        fx = int(rng.integers(0, w)); fy = int(rng.integers(gy0 + 3, gy0 + 26))
        lay.rect(fx, fy, 2, 1, 'SNOW', 1.6)
    lay.rect(0, 296, w, 64, 'SNOW', 4.6)                                    # steps outside (snowed)
    lay.rect(0, 296, w, 1, 'SNOW', 3.0)
    lay.rect(0, 306, w, 1, 'SNOW', 3.2)
    # tram stop shelter + sign, two figures waiting, a street lamp nearer the door
    sx = 150
    lay.rect(sx, 214, 34, 3, 'IRON', 2.4)
    lay.rect(sx - 1, 213, 36, 1, 'SNOW', 4.4)
    lay.rect(sx + 1, 217, 1, 46, 'IRON', 2.0)
    lay.rect(sx + 32, 217, 1, 46, 'IRON', 2.0)
    lay.rect(sx + 2, 217, 30, 20, 'HAZE', 5.2)                              # glass back wall
    lay.rect(sx + 40, 206, 1, 56, 'IRON', 2.2)
    lay.rect(sx + 37, 204, 8, 6, 'RED', 3.2)
    lay.rect(sx + 38, 205, 6, 4, 'SNOW', 4.6)
    lay.text('7', sx + 40, 205, 'NIGHT', 0.0)
    for (fx, h, coat) in ((sx + 10, 18, 'NIGHT'), (sx + 20, 17, 'IRON')):
        lay.rect(fx, 262 - h + 4, 4, h - 6, coat, 1.4)
        lay.rect(fx + 1, 262 - h + 1, 2, 3, 'STONE', 4.4)
        lay.rect(fx, 262 - h, 4, 1, coat, 1.0)
        lay.rect(fx, 260, 1, 2, coat, 1.0); lay.rect(fx + 3, 260, 1, 2, coat, 1.0)
    lx = 96
    lay.rect(lx, 120, 2, 176, 'IRON', 1.6)
    lay.rect(lx - 1, 286, 4, 10, 'IRON', 1.4)
    lay.rect(lx - 5, 116, 12, 3, 'IRON', 2.0)
    lay.rect(lx - 4, 119, 10, 7, 'SNOW', 3.4)                               # unlit lamp glass
    lay.rect(lx - 5, 115, 12, 1, 'SNOW', 4.6)
    # a parked car with snow on the roof (left)
    cx0 = 6
    lay.poly([(cx0, 262), (cx0 + 40, 262), (cx0 + 38, 252), (cx0 + 30, 250), (cx0 + 26, 242), (cx0 + 10, 242),
              (cx0 + 5, 250), (cx0, 252)], 'IRON', 2.6)
    lay.rect(cx0 + 10, 241, 16, 2, 'SNOW', 4.6)
    lay.rect(cx0 + 11, 244, 6, 5, 'HAZE', 4.0); lay.rect(cx0 + 19, 244, 6, 5, 'HAZE', 4.0)
    lay.rect(cx0, 251, 40, 1, 'SNOW', 4.0)
    for wx in (cx0 + 8, cx0 + 32):
        lay.ellipse(wx, 262, 3.0, 3.0, 'NIGHT', 0.0)
    lay.unlit[:] = True
    lay.resolve()
    return lay


# =========================================================================== the far bank (the Line)
TOWN_POS = 60
RIVER_POS = 120


def watchtower(lay, x, base, h, rng):
    """Line watchtower: four splayed legs, cross bracing, a glazed cabin with a flat roof (snow)."""
    top = base - h
    for (a, b) in ((x - 5, x - 2), (x + 5, x + 2)):
        lay.line(a, base, b, top + 6, 'IRON', 1.6)
    for k in range(top + 8, base - 2, 6):
        f = (k - top) / h
        hw = 2 + 3 * f
        lay.line(x - hw, k, x + hw, k + 5, 'IRON', 1.4)
        lay.line(x + hw, k, x - hw, k + 5, 'IRON', 1.4)
    lay.rect(x - 5, top, 11, 7, 'IRON', 2.0)
    lay.rect(x - 4, top + 2, 9, 3, 'HAZE', 3.0)
    lay.rect(x - 6, top - 2, 13, 2, 'IRON', 1.6)
    lay.rect(x - 6, top - 3, 13, 1, 'SNOW', 3.6)
    lay.rect(x + 6, top + 2, 3, 2, 'IRON', 2.6)                             # searchlight (off)


def build_town():
    w = 740
    lay = kit.TLayer(w, L.WORLD_H, RV, 'ext_town')
    rng = np.random.default_rng(41)
    horizon = 146
    # distant hills (very hazy)
    nz = pg.value_noise(w, 1, 60, 8, octaves=3)[0]
    for x in range(w):
        top = int(horizon - 14 - nz[x] * 16)
        lay.rect(x, top, 1, 220, 'HAZE', 5.4)
    # forest band on the far bank
    nz2 = pg.value_noise(w, 1, 14, 9, octaves=3)[0]
    for x in range(w):
        top = int(horizon - 4 - nz2[x] * 8)
        lay.rect(x, top, 1, 220, 'HAZE', 4.0 + (x % 5 == 0) * 0.6)
    # snowy field strip + the raked border strip + double fence
    lay.rect(0, horizon + 2, w, 30, 'SNOW', 3.6)
    lay.rect(0, horizon + 7, w, 3, 'HAZE', 3.4)                             # raked strip
    for fy, t in ((horizon + 1, 2.6), (horizon + 5, 2.0)):
        for x in range(0, w):
            if x % 5 == 0:
                lay.rect(x, fy - 5, 1, 6, 'IRON', t)
        lay.rect(0, fy - 4, w, 1, 'IRON', t + 0.4)
        lay.rect(0, fy - 2, w, 1, 'IRON', t + 0.4)
    # watchtowers + floodlight masts along the Line
    for tx in range(30, w, 118):
        watchtower(lay, tx + int(rng.integers(-10, 10)), horizon + 2, int(rng.integers(26, 32)), rng)
    for mx in range(88, w, 118):
        lay.rect(mx, horizon - 30, 1, 32, 'IRON', 2.0)
        lay.rect(mx - 3, horizon - 32, 7, 2, 'IRON', 2.4)
    # the water's edge on the far side (ice margin)
    lay.rect(0, horizon + 14, w, 20, 'ICE', 3.4)
    lay.unlit[:] = True
    lay.resolve()
    return lay


def build_river():
    w = 700
    lay = kit.TLayer(w, L.WORLD_H, RV, 'ext_river')
    rng = np.random.default_rng(44)
    ice_top = 158
    # frozen river: snow-dusted ice, pressure ridges, a dark open channel near the far bank
    t = 4.4 + (pg.value_noise(w, 40, 12, 2, octaves=3) - 0.5) * 1.4
    lay.put(np.ones((40, w), bool), 0, ice_top, 'ICE', t, flat=False)
    lay.rect(0, ice_top, w, 2, 'ICE', 1.6)
    for k in range(16):
        x0 = int(rng.integers(0, w - 40)); y0 = ice_top + int(rng.integers(4, 30))
        for j in range(int(rng.integers(12, 40))):
            lay.px(x0 + j, y0 + int(round(math.sin(j * 0.4) * 1.2)), 'ICE', 2.6)
    # the three-arched bridge (the city's arms) crossing toward the far bank, with a barrier
    by = ice_top + 6
    bx0, bx1 = 230, 560
    lay.rect(bx0, by - 8, bx1 - bx0, 6, 'STONE', 3.8)
    lay.rect(bx0, by - 9, bx1 - bx0, 1, 'SNOW', 4.6)
    lay.rect(bx0, by - 2, bx1 - bx0, 1, 'STONE', 2.6)
    span = (bx1 - bx0) // 3
    for k in range(3):
        ax0 = bx0 + k * span
        for x in range(ax0 + 6, ax0 + span - 6):
            u = (x - ax0 - 6) / max(1, span - 12)
            dh = int(round(14 * math.sqrt(max(0.0, 1 - (2 * u - 1) ** 2))))
            lay.rect(x, by - 2, 1, 16 - dh, 'STONE', 3.2)
        lay.rect(ax0, by - 2, 7, 18, 'STONE', 3.4)
        lay.rect(ax0 + 1, by + 14, 5, 2, 'SNOW', 4.0)
    lay.rect(bx1 - 6, by - 2, 7, 18, 'STONE', 3.4)
    for x in range(bx0, bx1, 5):                                            # balustrade
        lay.rect(x, by - 12, 1, 4, 'STONE', 4.4)
    lay.rect(bx0, by - 13, bx1 - bx0, 1, 'SNOW', 4.4)
    lay.rect(bx1 - 40, by - 16, 20, 2, 'RED', 3.0)                          # barrier boom
    for x in range(bx1 - 40, bx1 - 20, 4):
        lay.rect(x, by - 16, 2, 2, 'SNOW', 4.6)
    lay.rect(bx1 - 46, by - 20, 6, 12, 'IRON', 2.0)                         # guard hut
    lay.rect(bx1 - 46, by - 21, 6, 1, 'SNOW', 4.4)
    # near bank: old-town roofs, a baroque dome and a Gothic spire
    x = -6
    while x < w + 6:
        bw = int(rng.integers(18, 40))
        top = int(rng.integers(186, 204))
        lay.rect(x, top, bw, 200, 'STONE', float(rng.choice([2.6, 3.0, 3.6])))
        lay.poly([(x, top), (x + bw, top), (x + bw - 5, top - 9), (x + 5, top - 9)], 'ROOF',
                 float(rng.choice([2.4, 3.0, 3.4])))
        lay.rect(x + 5, top - 10, bw - 10, 2, 'SNOW', 4.4)
        lay.rect(x, top - 1, bw, 1, 'SNOW', 3.6)
        for k in range(x + 4, x + bw - 4, 7):
            lay.rect(k, top + 6, 3, 5, 'ROOF', 1.4 if rng.random() > 0.15 else 1.4)
            if rng.random() < 0.1:
                lay.rect(k, top + 6, 3, 5, 'LAMP', 2.0, emis=True)
        if rng.random() < 0.5:
            cxx = x + int(rng.integers(3, max(4, bw - 6)))
            lay.rect(cxx, top - 16, 3, 7, 'STONE', 2.2)
            lay.rect(cxx, top - 17, 3, 1, 'SNOW', 4.4)
        x += bw
    dx = 120
    m, mx, my = lay.ellipse(dx, 186, 16, 13, 'PAT', 3.0)
    for a in np.linspace(-0.8, 0.8, 7):
        for yv in np.linspace(-1, -0.05, 18):
            xv = a * math.sqrt(max(0.0, 1 - yv * yv))
            lay.px(int(round(dx + xv * 16)), int(round(186 + yv * 13)), 'PAT', 1.6 if a > 0 else 4.2)
    lay.rect(dx - 18, 186, 36, 20, 'STONE', 3.6)
    lay.rect(dx - 2, 165, 5, 9, 'PAT', 2.4)
    lay.rect(dx, 160, 1, 5, 'IRON', 2.0)
    lay.rect(dx - 10, 172, 20, 1, 'SNOW', 4.4)
    sx = 610
    lay.poly([(sx - 4, 190), (sx + 5, 190), (sx + 1, 128)], 'ROOF', 3.2)
    lay.rect(sx - 6, 190, 13, 30, 'STONE', 3.0)
    lay.line(sx - 3, 188, sx, 132, 'SNOW', 4.0)
    lay.px(sx + 1, 126, 'IRON', 2.0)
    lay.unlit[:] = True
    lay.resolve()
    return lay


# =========================================================================== Grosser Saal
SAAL_Y = 200
SAAL_H = 66
NEAR_POS = int(round(1652 - 200 - 1280 * (1 - L.PARALLAX['saal_near'])))
FAR_POS = int(round(1652 - 200 - 1280 * (1 - L.PARALLAX['saal_far'])))


def tiny_delegate(lay, x, y, facing='down', s=1, suit='I', t=1.4):
    """A seated delegate seen from the booths (2-3 px head, 4-5 px shoulders)."""
    if s >= 2:
        lay.rect(x - 2, y + 2, 5, 3, suit, t)
        lay.rect(x - 1, y, 3, 2, 'P', 4.2 if facing == 'down' else 2.0)
        if facing != 'down':
            lay.rect(x - 1, y, 3, 1, 'I', 1.0)
    else:
        lay.rect(x - 1, y + 1, 3, 2, suit, t)
        lay.px(x, y, 'P', 4.2 if facing == 'down' else 2.0)


def build_saal_far(hist=False):
    w = 540
    lay = kit.TLayer(w, SAAL_H, RP, 'saal_far_hist' if hist else 'saal_far')
    H = SAAL_H
    # head wall: upper stucco (light, daylit), tall windows, walnut panelling, dais
    lay.vgrad(0, 0, w, H, 'M', 4.6, 3.6)
    for wx in range(14, w, 44):
        lay.rect(wx, 0, 16, 30, 'C', 5.4)                                     # tall windows (bright)
        lay.rect(wx, 0, 16, 2, 'C', 4.4)
        lay.rect(wx + 7, 0, 2, 30, 'M', 3.0)
        lay.rect(wx - 3, 0, 3, 32, 'R', 1.8)                                  # curtains
        lay.rect(wx + 16, 0, 3, 32, 'R', 1.8)
    lay.rect(0, 30, w, 10, 'D', 3.0)                                          # panelling
    lay.rect(0, 30, w, 1, 'B', 4.0)
    for k in range(0, w, 9):
        lay.rect(k, 32, 1, 7, 'D', 2.0)
    lay.rect(0, 40, w, 4, 'D', 4.2)                                           # dais front
    lay.rect(0, 40, w, 1, 'M', 5.6)
    lay.rect(0, 44, w, H - 44, 'R', 1.8)
    # the commission emblem above the presidium + the six flags on the dais
    cx = 200
    lay.rect(cx - 12, 10, 24, 16, 'C', 2.4)
    lay.rect(cx - 12, 10, 24, 1, 'B', 4.4)
    br, wa = kit.commission_arms(18, 12)
    lay.put(br, cx - 9, 12, 'P', 6.6)
    lay.put(wa, cx - 9, 12, 'P', 5.4)
    order = ['finland', 'switzerland', 'ussr', 'commission', 'reich', 'sweden']
    for i, kind in enumerate(order):
        fx = cx - 38 + i * 15
        if i >= 3:
            fx += 6
        lay.rect(fx, 22, 1, 18, 'B', 4.0)                                      # pole
        lay.px(fx, 21, 'B', 5.0)
        col = {'finland': ('P', 6.4), 'switzerland': ('R', 3.0), 'ussr': ('R', 2.8), 'commission': ('C', 3.0),
               'reich': ('M', 1.8), 'sweden': ('C', 2.6)}[kind]
        lay.rect(fx + 1, 23, 5, 9, *col)
        lay.rect(fx + 1, 23, 1, 9, col[0], col[1] - 0.6)
        if kind == 'finland':
            lay.rect(fx + 2, 23, 1, 9, 'C', 2.6); lay.rect(fx + 1, 26, 5, 1, 'C', 2.6)
        elif kind == 'sweden':
            lay.rect(fx + 2, 23, 1, 9, 'B', 4.4); lay.rect(fx + 1, 26, 5, 1, 'B', 4.4)
        elif kind == 'switzerland':
            lay.rect(fx + 3, 25, 1, 4, 'P', 6.6); lay.rect(fx + 2, 26, 3, 1, 'P', 6.6)
        elif kind == 'commission':
            lay.rect(fx + 2, 26, 3, 1, 'P', 6.6)
        elif kind == 'ussr':
            if hist:
                lay.px(fx + 2, 24, 'B', 4.6); lay.px(fx + 2, 26, 'B', 4.2); lay.px(fx + 3, 25, 'B', 4.2)
            else:
                lay.px(fx + 2, 24, 'B', 4.0); lay.px(fx + 3, 25, 'B', 3.6)
        elif kind == 'reich':
            if hist:
                lay.rect(fx + 1, 23, 5, 9, 'R', 2.8)
                lay.rect(fx + 2, 26, 3, 3, 'P', 6.4)
                lay.px(fx + 3, 27, 'I', 1.0)
            else:
                lay.rect(fx + 2, 26, 3, 3, 'N', 0.0)
                lay.px(fx + 3, 27, 'P', 6.0)
    # chandeliers of the Saal hanging into view (warm)
    for chx in (90, 200, 310, 420):
        lay.rect(chx, 0, 1, 6, 'B', 3.0)
        lay.rect(chx - 6, 6, 13, 2, 'B', 3.6)
        for k in range(-6, 7, 3):
            lay.px(chx + k, 5, 'A', 5.0, emis=True)
        lay.rect(chx - 4, 8, 9, 2, 'S', 5.0)
        lay.px(chx, 11, 'S', 6.0)
    lay.unlit[:] = True
    lay.resolve()
    return lay


def build_saal_near():
    w = 440
    lay = kit.TLayer(w, SAAL_H, RP, 'saal_near')
    H = SAAL_H
    cx = 200
    # carpet floor of the hall (wine red, darker toward the booths), opaque from the dais down
    t = np.linspace(2.0, 1.4, H - 38)[:, None] + np.zeros((1, w))
    lay.put(np.ones((H - 38, w), bool), 0, 38, 'R', t, flat=False)
    for x in range(0, w, 2):                                                  # carpet border pattern
        lay.px(x, 41, 'B', 2.4)
    # presidium table (far end), arms of the horseshoe (perspective), secretariat table (open end)
    pt0, pt1, py = cx - 46, cx + 46, 38
    lay.rect(pt0, py, pt1 - pt0, 3, 'G', 5.0)
    lay.rect(pt0, py, pt1 - pt0, 1, 'G', 6.0)
    lay.rect(pt0, py + 3, pt1 - pt0, 1, 'G', 3.0)
    for k in range(9):                                                        # presidium (facing the hall)
        dx = pt0 + 6 + k * 10
        tiny_delegate(lay, dx, py - 4, 'down', s=1, suit='I', t=1.2 if k != 4 else 2.0)
        lay.px(dx, py, 'P', 6.4)                                              # papers
    yb = H - 2
    for side in (-1, 1):
        for y in range(py + 3, yb):
            f = (y - py) / (yb - py)
            xin = cx + side * (46 + 34 * f)
            wd = 2 + int(round(2 * f))
            x0 = int(round(xin)) if side > 0 else int(round(xin)) - wd
            lay.rect(x0, y, wd, 1, 'G', 5.0)
            lay.px(x0 + (wd - 1 if side < 0 else 0), y, 'G', 3.2)
            lay.px(x0 + (0 if side < 0 else wd - 1), y, 'G', 6.0)
        # delegates along the outer side of each arm (facing inward), mics, papers
        for k in range(5):
            f = (k + 0.7) / 5.4
            y = int(round(py + 3 + f * (yb - py - 5)))
            xin = cx + side * (46 + 34 * f)
            xo = int(round(xin + side * (5 + 2 * f)))
            tiny_delegate(lay, xo, y - 2, 'side', s=2 if f > 0.55 else 1, suit='I', t=1.4)
            lay.px(int(round(xin + side * 1)), y, 'P', 6.6)
    # secretariat table at the open end, three staff, a typewriter
    sy = H - 9
    lay.rect(cx - 12, sy, 24, 3, 'P', 5.8)
    lay.rect(cx - 12, sy, 24, 1, 'P', 6.8)
    for k in range(3):
        tiny_delegate(lay, cx - 8 + k * 8, sy + 3, 'up', s=2, suit='C', t=1.6)
    lay.rect(cx - 3, sy - 2, 5, 2, 'I', 1.6)
    # observers at the corners (bottom), a few people standing in the aisle (break)
    for (x, y) in ((cx - 92, H - 8), (cx + 92, H - 8), (cx - 30, 50), (cx + 26, 47)):
        lay.rect(x - 1, y - 4, 3, 5, 'I', 1.6)
        lay.px(x, y - 5, 'P', 4.4)
    lay.unlit[:] = True
    lay.resolve()
    return lay


def build_all():
    return {
        'ext_sky': (build_sky(), 0),
        'ext_town': (build_town(), TOWN_POS),
        'ext_river': (build_river(), RIVER_POS),
        'ext_square': (build_square(), SQ_POS),
        'saal_far': (build_saal_far(False), FAR_POS),
        'saal_far_hist': (build_saal_far(True), FAR_POS),
        'saal_near': (build_saal_near(), NEAR_POS),
    }
