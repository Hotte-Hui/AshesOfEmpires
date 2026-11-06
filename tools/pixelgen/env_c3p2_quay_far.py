"""env_c3p2_quay_far -- the far planes of the night quay (L_C3_Quay), unlit parallax layers.
sky      (p 0.02)  overcast snow night, a faint cold glow over the Line on the horizon
pall     (p 0.55)  the smoke pall of the burning east wing: orange from below near the fire, drifting right
far_bank (p 0.10)  the other bank: hills, the Line -- double fence, floodlight masts, five watchtowers
river    (p 0.30)  the frozen river: drifts, pressure ridges, an open lead; the three-arch bridge of the city
                   arms (lamps, the barrier and the guard hut at its far abutment) on the right
oldtown  (p 0.45)  the old town of our bank behind the bridge approach: gables, warm windows, the church tower
Every function returns (pg.Layer, info dict) in layer pixels (home 0, 0).
"""
from __future__ import annotations

import math

import numpy as np

import env_c3p2_quay_kit as K
from env_c3p2_quay_kit import (Canvas, Light, Layer, resolve, ladder, value_noise, bayer, NI, SL, IR, CR, PA, LA,
                               SK, SN, RD, tone_of)

P = {'sky': 0.02, 'pall': 1.0, 'far_bank': 0.10, 'river': 0.30, 'oldtown': 0.45}
SHORE_Y = 172          # far shore line (ice begins)
ICE_NEAR_Y = 268       # the ice is hidden behind the balustrade below this row
TOWERS = [64, 232, 404, 566, 728]          # watchtowers on the far bank (layer x)
SEARCH_TOWERS = (232, 566)
MASTS = [18, 148, 318, 486, 650, 770]
BRIDGE = dict(x0=556, deck=152, spring=184, base=204, arches=[(600, 764), (788, 952), (976, 1140)])
BRIDGE_LAMPS = [586, 652, 718, 776, 842, 908, 964, 1030]


# =========================================================================== sky
def make_sky():
    W, H = K.layer_w(P['sky']), 200
    L = Layer(W, H, 'sky')
    lad = ladder(NI[0], NI[1], NI[2], NI[3], SL[0], SL[1], SL[2])
    lum = np.array([K.lum(c) for c in lad], np.float32)
    yy = np.arange(H, dtype=np.float32)[:, None]
    base = 0.015 + 0.20 * np.clip(yy / 176.0, 0, 1) ** 1.6
    n1 = value_noise(W // 3 + 2, H, 12.0, seed=801, octaves=4)
    n1 = np.repeat(n1, 3, axis=1)[:, :W]                      # horizontally stretched cloud banks
    n2 = value_noise(W, H, 12.0, seed=802, octaves=3)
    t = base + 0.055 * (n1 - 0.5) + 0.02 * (n2 - 0.5)
    # cloud undersides catch the glow of the floodlights and the town (low, cold)
    t += 0.05 * np.clip((yy - 120) / 60.0, 0, 1) * (0.6 + 0.4 * n1)
    T = K.L_LO + np.clip(t, 0, 1) * (K.L_HI - K.L_LO)
    fi = np.interp(T, lum, np.arange(len(lad), dtype=np.float32))
    idx = np.floor(fi).astype(int)
    fr = np.clip((fi - idx - 0.5) * 3.0 + 0.5, 0, 1)
    idx = np.clip(idx + (fr > bayer(W, H)), 0, len(lad) - 1)
    L.c[:] = np.stack(lad)[idx]
    L.c[..., 3] = 255
    return L, {}


# =========================================================================== smoke pall
def _blobs_density(W, H, blobs, seed, warp=0.35, cell=14.0):
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    D = np.zeros((H, W), np.float32)
    for (bx, by, r, s) in blobs:
        x0, x1 = max(0, int(bx - r * 1.4)), min(W, int(bx + r * 1.4) + 1)
        y0, y1 = max(0, int(by - r * 1.4)), min(H, int(by + r * 1.4) + 1)
        if x1 <= x0 or y1 <= y0:
            continue
        d2 = ((xx[y0:y1, x0:x1] - bx) ** 2 / 1.7 + (yy[y0:y1, x0:x1] - by) ** 2 * 1.3) / (r * r)
        D[y0:y1, x0:x1] = np.maximum(D[y0:y1, x0:x1], s * np.clip(1 - d2, 0, 1))
    n = value_noise(W, H, cell, seed=seed, octaves=4)
    return D + warp * (n - 0.5) * np.clip(D * 3, 0, 1)


def make_pall():
    """Binary-alpha smoke masses with dithered fringes; tone: lit top edge, fire-orange belly near the source."""
    W, H = 1240, 150
    rng = np.random.default_rng(810)
    blobs = []
    # the smoke of the wing gathers under the low clouds and drifts right over the quay (world coords, p 1)
    for k in range(90):
        t = k / 89.0
        x = 250 + 960 * t + rng.uniform(-30, 30)
        y = 46 - 30 * t + 12 * math.sin(t * 8.0) + rng.uniform(-14, 14)
        blobs.append((x, y, 36 - 16 * t + rng.uniform(-8, 8), 1.0 - 0.45 * t + rng.uniform(-0.08, 0.05)))
    D = _blobs_density(W, H, blobs, seed=811, warp=0.75, cell=16.0)
    cv = Canvas(W, H, 'pall')
    thr = bayer(W, H)
    mask = (D > (0.5 + 0.22 * (thr - 0.5))) & (np.arange(H)[:, None] < 118)
    # top-lit relief: compare with the density a few px above
    Dup = np.vstack([np.zeros((4, W), np.float32), D[:-4]])
    relief = np.clip((D - Dup) * 0.9, -0.2, 0.25)
    nn = value_noise(W, H, 9.0, seed=812, octaves=3)
    tone = 0.13 + 0.05 * (nn - 0.5) - relief * 0.45
    far = np.clip((np.arange(W, dtype=np.float32)[None, :] - 300) / 800.0, 0, 1)
    tone = tone + 0.05 * far                                     # distant smoke picks up the sky haze
    cv.put(mask, 0, 0, 'smoke', tone)
    # the fire lights only the belly of the trunk; the drifting smoke stays smoke-grey
    lights = [Light('fire', 200, 150, 260, 0.9, sq=1.2)]
    L = resolve(cv, lights, gains=(0.4, 0.42, 0.3), warm_bias=0.35)
    return L, {'source': [200, 140]}


# =========================================================================== far bank (the Line)
def make_far_bank():
    W, H = K.layer_w(P['far_bank']), 200
    cv = Canvas(W, H, 'far_bank')
    rng = np.random.default_rng(820)
    x = np.arange(W, dtype=np.float32)
    # hills beyond the Line
    hill = 140 + 9 * np.sin(x / 97.0 + 1.2) + 5 * np.sin(x / 41.0) + 3 * (value_noise(W, 1, 30.0, seed=821)[0] - 0.5)
    for i in range(W):
        h0 = int(hill[i])
        cv.rect(i, h0, 1, SHORE_Y - h0, 'snow', 0.06 + 0.02 * ((i * 7) % 3 == 0))
    # forest band
    tree = 152 + 3 * np.sin(x / 13.0) + 2 * np.sin(x / 5.3 + 0.7)
    for i in range(W):
        top = int(tree[i] - (3 if (i * 37) % 11 < 3 else 0) - (2 if (i * 13) % 7 == 0 else 0))
        cv.rect(i, top, 1, 163 - top, 'cloth', 0.02)
    cv.texture(0, 128, W, 36, 0.03, cell=5.0, seed=822)
    # the strip: ploughed snow between the fences, lit by the masts
    cv.rect(0, 160, W, SHORE_Y - 160, 'snow', 0.22)
    cv.texture(0, 160, W, 12, 0.05, cell=4.0, seed=823)
    for i in range(0, W, 3):                                    # plough furrows
        cv.px(i, 165 + (i // 3) % 2, 'snow', 0.16)
    # shore embankment and the first ice
    cv.rect(0, 170, W, 2, 'snow', 0.30)
    cv.rect(0, SHORE_Y, W, 4, 'ice', 0.13)
    for i in range(0, W, 2):
        cv.px(i, SHORE_Y + 1 + (i * 5) % 2, 'ice', 0.2)
    # fences: back (y 152..162) and front (158..169), posts + wires
    for (ytop, ybot, step, ph) in ((151, 162, 6, 0), (157, 169, 7, 3)):
        for xx in range(ph, W, step):
            cv.rect(xx, ytop, 1, ybot - ytop, 'iron', 0.10)
            cv.px(xx + 1, ytop, 'iron', 0.10)                   # outrigger
        for wy in range(ytop + 1, ybot - 1, 3):
            for xx in range(0, W, 2):
                cv.px(xx, wy, 'iron', 0.14)
    lights, info = [], {'masts': [], 'towers': [], 'searchlights': []}
    # floodlight masts with cold pools
    for mx in MASTS:
        cv.rect(mx, 128, 1, 42, 'iron', 0.12)
        cv.rect(mx - 2, 126, 5, 1, 'iron', 0.16)
        cv.rect(mx - 2, 127, 2, 1, 'cold_lit', 0.85)
        cv.rect(mx + 1, 127, 2, 1, 'cold_lit', 0.85)
        lights.append(Light('cold', mx, 166, 46, 1.0, sq=2.6))
        lights.append(Light('cold', mx, 132, 30, 0.35))
        info['masts'].append([mx, 127])
    # watchtowers
    for k, tx in enumerate(TOWERS):
        base = 167
        top = 122
        for side in (-1, 1):                                    # splayed legs
            cv.line(tx + side * 6, base, tx + side * 4, top + 6, 'iron', 0.09)
        for yb in range(top + 10, base, 9):                     # cross braces
            cv.line(tx - 5, yb, tx + 5, yb + 7, 'iron', 0.07)
            cv.line(tx + 5, yb, tx - 5, yb + 7, 'iron', 0.07)
        cv.rect(tx - 7, top - 10, 15, 11, 'wood', 0.08)          # cabin
        cv.rect(tx - 9, top - 13, 19, 3, 'slate', 0.10)           # roof
        cv.rect(tx - 8, top - 14, 17, 1, 'snow', 0.55)            # snow on the roof
        lit = k in (1, 3)
        for wx in (tx - 5, tx + 1):
            cv.rect(wx, top - 7, 4, 3, 'lit' if lit else 'glass', 0.35 if lit else 0.08)
        if lit:
            lights.append(Light('warm', tx, top - 5, 7, 0.35))
        cv.rect(tx - 8, top + 1, 17, 1, 'iron', 0.12)             # gallery rail
        info['towers'].append([tx, top - 6])
        if tx in SEARCH_TOWERS:
            cv.rect(tx - 2, top - 17, 5, 3, 'iron', 0.2)          # searchlight drum
            cv.rect(tx + 2, top - 16, 1, 1, 'cold_lit', 1.0)
            info['searchlights'].append([tx + 2, top - 16])
    # a few far lights of a village beyond the Line (tiny, warm, sparse)
    for (vx, vy) in ((300, 147), (306, 148), (612, 146), (690, 149)):
        cv.px(vx, vy, 'lit', 0.3)
    L = resolve(cv, lights, gains=(0.35, 0.5, 0.42), warm_bias=0.1)
    # dithered halos around the mast heads (light in the snow-filled air)
    for mx in MASTS:
        _halo(L, mx, 127, 9, [SL[3], SL[4], SL[5]], seed=mx)
    for (sx, sy) in info['searchlights']:
        _halo(L, sx, sy, 6, [SL[4], SN[1]], seed=sx)
    return L, info


def _halo(L: Layer, cx, cy, r, cols, seed=0):
    """Sparse dithered halo pixels around a light in hazy air (only over darker pixels)."""
    thr = bayer(2 * r + 1, 2 * r + 1, cx, cy)
    for dy in range(-r, r + 1):
        for dx in range(-r, r + 1):
            d = math.hypot(dx, dy) / r
            if d >= 1 or d < 0.15:
                continue
            x, y = cx + dx, cy + dy
            if not (0 <= x < L.w and 0 <= y < L.h) or L.c[y, x, 3] == 0:
                continue
            dens = (1 - d) ** 1.8 * 0.9
            if thr[dy + r, dx + r] < dens:
                c = cols[min(len(cols) - 1, int((1 - d) * len(cols)))]
                if K.lum(L.c[y, x]) < K.lum(c):
                    L.c[y, x, :3] = np.asarray(c)[:3]


# =========================================================================== river + bridge
def make_river():
    W, H = K.layer_w(P['river']), ICE_NEAR_Y + 2
    cv = Canvas(W, H, 'river')
    rng = np.random.default_rng(830)
    y0 = SHORE_Y + 2
    yy = np.arange(y0, H, dtype=np.float32)
    depth = (yy - y0) / (H - y0)                                 # 0 far .. 1 near
    t_rows = 0.25 - 0.05 * depth                                 # distant ice hazier (lighter)
    tone = np.repeat(t_rows[:, None], W, axis=1)
    n = np.repeat(value_noise(W // 3 + 2, H - y0, 9.0, seed=831, octaves=4), 3, axis=1)[:, :W]
    ns = np.repeat(value_noise(W // 6 + 2, H - y0, 7.0, seed=832, octaves=3), 6, axis=1)[:, :W]
    drift = np.clip((ns - 0.56) * 3, 0, 1)                       # long wind drifts (lighter)
    bare = np.clip((0.36 - n) * 3, 0, 1)                         # wind-swept bare ice (darker)
    tone = tone + 0.07 * drift * (0.5 + depth[:, None]) - 0.06 * bare * (0.4 + depth[:, None])
    cv.put(np.ones((H - y0, W), bool), 0, y0, 'ice', tone)
    # glints on bare ice
    for _ in range(420):
        gx, gy = int(rng.integers(0, W)), int(rng.integers(y0 + 8, H))
        if bare[gy - y0, gx] > 0.4:
            cv.px(gx, gy, 'ice', 0.62)
    # pressure ridges: jagged, lit top, dark shadow
    for k in range(7):
        ry = int(y0 + 14 + k * 12 + rng.integers(-3, 4))
        x = float(rng.integers(-60, W - 120))
        length = int(rng.integers(70, 200))
        yv = float(ry)
        i = 0
        while i < length:
            seg = int(rng.integers(4, 14))
            if rng.random() < 0.25:                              # broken ridge: gaps
                i += seg
                continue
            for q in range(seg):
                xx = int(x + i + q)
                yv += rng.uniform(-0.35, 0.35)
                hgt = 1 + (1 if rng.random() < 0.35 else 0) + (1 if rng.random() < 0.08 else 0)
                for j in range(hgt):
                    cv.px(xx, int(yv) - j, 'ice', 0.40 + 0.08 * (j == hgt - 1))
                cv.px(xx, int(yv) + 1, 'ice', 0.05)
            i += seg
    # the open lead: black water, rimmed by new ice
    lead_y = lambda xx: 214 + 5 * math.sin(xx / 70.0) + 2 * math.sin(xx / 23.0)
    for xx in range(70, 560):
        w = 2 + int(2.5 * math.sin((xx - 70) / 490.0 * math.pi) * (1 + 0.3 * math.sin(xx / 11.0)))
        yc = int(lead_y(xx))
        cv.rect(xx, yc, 1, w, 'glass', 0.02)
        cv.px(xx, yc - 1, 'ice', 0.4)
        cv.px(xx, yc + w, 'ice', 0.12)
    lights = []
    info = {'lamps': []}
    # ---------------------------------------------------------------- bridge (three arches, city arms)
    B = BRIDGE
    deck, spring, base = B['deck'], B['spring'], B['base']
    x0, x1 = B['x0'], W + 2
    cv.rect(x0, deck, x1 - x0, spring - deck + 2, 'stone', 0.24, hgt=0.5)
    cv.texture(x0, deck, x1 - x0, spring - deck, 0.03, cell=3.0, seed=833)
    for xx in range(x0, x1, 7):                                    # ashlar joints of the spandrels
        for yy_ in range(deck + 9, spring, 5):
            cv.px(xx + (3 if (yy_ // 5) % 2 else 0), yy_, 'stone', 0.17)
    for (a0, a1) in B['arches']:
        aw = a1 - a0
        crown = deck + 9
        rise = spring - crown
        for xx in range(a0, a1):
            u = (xx - a0 + 0.5) / aw * 2 - 1
            top = int(round(spring - rise * math.sqrt(max(0.0, 1 - u * u))))
            cv.rect(xx, top, 1, base - top + 1, 'ice', 0.11)        # ice seen under the arch (in shadow)
            cv.rect(xx, top - 3, 1, 3, 'stone', 0.34)               # voussoir ring
            if (xx - a0) % 5 == 0:
                cv.px(xx, top - 2, 'stone', 0.2)
            cv.px(xx, top, 'stone', 0.10)                           # soffit shadow
        cv.rect(a0, base - 1, aw, 2, 'ice', 0.22)
    # piers with cutwaters and ice collars
    for (pa, pb) in ((B['arches'][0][1], B['arches'][1][0]), (B['arches'][1][1], B['arches'][2][0])):
        cv.rect(pa, spring - 3, pb - pa, base - spring + 5, 'stone', 0.27, hgt=0.55)
        cv.rect(pa, spring - 3, 3, base - spring + 5, 'stone', 0.18)
        cv.poly([(pa - 2, base + 1), (pb + 2, base + 1), (pb, spring + 10), (pa, spring + 10)], 'stone', 0.22)
        cv.rect(pa - 4, base, pb - pa + 8, 3, 'snow', 0.5)
        cv.rect(pa + 3, spring + 8, pb - pa - 6, 1, 'stone', 0.28)
    # far abutment on its spit of land + the barrier and the guard hut of the Line
    cv.rect(x0 - 26, spring - 4, 34, base - spring + 6, 'stone', 0.16)
    cv.poly([(x0 - 60, base + 2), (x0 + 30, base + 2), (x0 + 6, spring), (x0 - 40, spring + 8)], 'snow', 0.30)
    hut_x = x0 + 8
    cv.rect(hut_x, deck - 14, 14, 14, 'wood', 0.10)
    cv.rect(hut_x - 1, deck - 16, 16, 2, 'slate', 0.12)
    cv.rect(hut_x - 1, deck - 17, 16, 1, 'snow', 0.6)
    cv.rect(hut_x + 3, deck - 10, 5, 4, 'cold_lit', 0.55)
    lights.append(Light('cold', hut_x + 5, deck - 6, 26, 0.9))
    for i in range(30):                                            # red-white boom across the deck
        cv.px(hut_x + 16 + i, deck - 4, 'red' if (i // 5) % 2 == 0 else 'snow', 0.30 if (i // 5) % 2 == 0 else 0.6)
    cv.rect(hut_x + 15, deck - 6, 2, 6, 'iron', 0.12)
    info['barrier'] = [hut_x + 30, deck - 4]
    # parapet: coping + balusters, snow on top
    cv.rect(x0, deck - 6, x1 - x0, 1, 'stone', 0.34)
    cv.rect(x0, deck - 7, x1 - x0, 1, 'snow', 0.72)
    for xx in range(x0, x1, 3):
        cv.rect(xx, deck - 5, 1, 5, 'stone', 0.22)
    cv.rect(x0, deck, x1 - x0, 1, 'stone', 0.10)
    cv.rect(x0, deck + 6, x1 - x0, 1, 'stone', 0.26)              # string course
    # the arms of the city on the middle pier: white bridge with three arches on slate blue (fictional)
    ax = (B['arches'][0][1] + B['arches'][1][0]) // 2
    cv.rect(ax - 5, deck + 9, 11, 9, 'stone', 0.32)
    cv.rect(ax - 4, deck + 10, 9, 7, 'slate', 0.30)
    for k in (-3, 0, 3):
        cv.ink_px(ax + k, deck + 13, SN[3])
    cv.ink_rect(ax - 4, deck + 12, 9, 1, SN[3])
    # lamps on the parapet
    for lx in BRIDGE_LAMPS:
        if lx >= W:
            continue
        cv.rect(lx, deck - 16, 1, 10, 'iron', 0.12)
        cv.rect(lx - 1, deck - 19, 3, 3, 'lit', 0.8)
        cv.px(lx, deck - 20, 'iron', 0.15)
        lights.append(Light('warm', lx, deck - 10, 26, 1.0, up=0.5))
        lights.append(Light('warm', lx, base + 4, 30, 0.55, sq=3.0))    # pool on the ice below
        info['lamps'].append([lx, deck - 18])
    L = resolve(cv, lights, gains=(0.42, 0.55, 0.36), warm_bias=0.1)
    for lx in BRIDGE_LAMPS:
        if lx < W:
            _halo(L, lx, deck - 18, 7, [LA[0], LA[1], LA[2]], seed=lx)
    # distance haze: the far ice and the bridge sink into the snow air
    a = L.alpha()
    rows = np.arange(L.h)[:, None]
    amt = np.clip((196 - rows) / 40.0, 0, 1) * 0.55
    hz = K.ladder(NI[3], SL[0], SL[1], SL[2], SL[3])
    _haze_toward(L, hz, amt * a)
    return L, info


def _haze_toward(L: Layer, hz, amount):
    """Move dark pixels toward the haze ladder (ordered dither), lights and lit glass untouched."""
    lumv = (L.c[..., 0] * 0.299 + L.c[..., 1] * 0.587 + L.c[..., 2] * 0.114) / 255.0
    target = np.stack(hz)
    tl = np.array([K.lum(c) for c in hz], np.float32)
    want = np.interp(lumv + amount * 0.12, tl, np.arange(len(hz), dtype=np.float32))
    pick = (bayer(L.w, L.h) < amount) & (L.em[..., 3] == 0) & (lumv < tl[-1])
    idx = np.clip(np.round(want).astype(int), 0, len(hz) - 1)
    L.c[pick, :3] = target[idx][pick][:, :3]


# =========================================================================== old town (our bank, right)
def make_oldtown():
    W, H = K.layer_w(P['oldtown']), 266
    cv = Canvas(W, H, 'oldtown')
    rng = np.random.default_rng(840)
    lights = []
    info = {'windows': [], 'chimneys': [], 'lit': []}
    ground = 262
    # the church tower with its patina spire and the lit clock (drawn first: the gables stand in front)
    tx = 1000
    cv.rect(tx, 92, 26, ground - 92, 'stone', 0.16, hgt=0.5)
    cv.rect(tx - 2, 90, 30, 3, 'stone', 0.26)
    cv.poly([(tx - 1, 90), (tx + 13, 26), (tx + 27, 90)], 'patina', 0.20, hgt=0.7)
    cv.rect(tx + 12, 16, 3, 11, 'iron', 0.2)
    cv.rect(tx + 10, 19, 7, 1, 'iron', 0.2)
    cv.ellipse(tx + 13, 112, 6, 6, 'lit', 0.55)
    cv.ink_px(tx + 13, 108, IR[1])
    cv.ink_px(tx + 13, 109, IR[1])
    cv.ink_px(tx + 14, 112, IR[1])
    cv.ink_px(tx + 15, 112, IR[1])
    lights.append(Light('warm', tx + 13, 112, 24, 0.6))
    for wy in (132, 160, 190):
        cv.rect(tx + 10, wy, 6, 12, 'glass', 0.04)
    x = 868
    k = 0
    while x < W - 4:
        w = int(rng.integers(38, 66))
        storeys = int(rng.integers(4, 6))
        sh = 17
        top = ground - storeys * sh - 6
        tone = 0.13 + 0.04 * ((k * 5) % 3) / 2.0
        cv.rect(x, top, w, ground - top, 'stone', tone, hgt=0.4)
        cv.texture(x, top, w, ground - top, 0.025, cell=4.0, seed=841 + k)
        cv.rect(x, top, w, 2, 'stone', tone + 0.1)                 # eaves cornice
        # roof: steep gable or hipped, slate with snow
        rise = int(rng.integers(22, 36))
        if k % 3 == 1:
            pts = [(x - 2, top), (x + w // 2, top - rise), (x + w + 1, top)]
        else:
            pts = [(x - 2, top), (x + 6, top - rise + 8), (x + w - 6, top - rise + 8), (x + w + 1, top)]
        cv.poly(pts, 'slate', 0.10, hgt=0.6)
        m, mx0, my0 = Layer(1, 1).poly_mask(pts)
        # snow lies on the slope (ordered dither: thicker toward the ridge)
        hh, ww = m.shape
        sn = m & (bayer(ww, hh, mx0, my0) < 0.55 + 0.35 * (1 - np.arange(hh)[:, None] / max(1, hh)))
        cv.put(sn, mx0, my0, 'snow', 0.42)
        # chimney
        cx_ = x + int(rng.integers(6, max(7, w - 10)))
        cy_ = top - rise + 8 + int(rng.integers(0, 6))
        cv.rect(cx_, cy_ - 10, 4, 12, 'stone', 0.12)
        cv.rect(cx_ - 1, cy_ - 11, 6, 1, 'snow', 0.6)
        info['chimneys'].append([cx_ + 2, cy_ - 11])
        # windows: grid, about a fifth lit (people woke to the fire bells)
        cols_n = max(2, (w - 8) // 10)
        gap = (w - cols_n * 5) / (cols_n + 1)
        for r in range(storeys):
            wy = top + 6 + r * sh
            for c in range(cols_n):
                wx = int(round(x + gap * (c + 1) + c * 5))
                if wy + 8 >= ground - 2:
                    continue
                lit = rng.random() < (0.22 if r < storeys - 1 else 0.1)
                if lit:
                    cv.rect(wx, wy, 5, 8, 'lit', 0.45 + 0.3 * rng.random())
                    cv.rect(wx + 2, wy, 1, 8, 'lit', 0.2)            # cross bar
                    cv.rect(wx, wy + 3, 5, 1, 'lit', 0.2)
                    lights.append(Light('warm', wx + 2.5, wy + 4, 13, 0.7))
                    info['lit'].append([wx, wy])
                else:
                    cv.rect(wx, wy, 5, 8, 'glass', 0.05)
                    cv.px(wx + 3, wy + 1, 'glass', 0.22)
                info['windows'].append([wx, wy, 5, 8, bool(lit)])
                cv.rect(wx - 1, wy + 8, 7, 1, 'snow', 0.5)            # sill with snow
        x += w + int(rng.integers(0, 3))
        k += 1
    # the embankment of the river bend in front of the row (stone wall, snow, iron rail, two lamps)
    e0 = 860
    cv.rect(e0, 246, W - e0, ground - 246 + 4, 'stone', 0.17, hgt=0.5)
    for yy_ in range(250, ground + 4, 5):
        cv.rect(e0, yy_, W - e0, 1, 'stone', 0.1)
    cv.rect(e0 - 6, 244, W - e0 + 6, 2, 'stone', 0.3)
    cv.rect(e0 - 6, 243, W - e0 + 6, 1, 'snow', 0.7)
    for xx in range(e0 - 4, W, 4):
        cv.rect(xx, 238, 1, 5, 'iron', 0.12)
    cv.rect(e0 - 4, 238, W - e0 + 4, 1, 'iron', 0.16)
    cv.poly([(e0 - 40, ground + 4), (e0, ground + 4), (e0, 246), (e0 - 6, 246)], 'snow', 0.34)
    for lx in (e0 + 40, e0 + 170, e0 + 300):
        cv.rect(lx, 226, 1, 12, 'iron', 0.14)
        cv.rect(lx - 1, 223, 3, 3, 'lit', 0.7)
        lights.append(Light('warm', lx, 232, 20, 0.7))
        lights.append(Light('warm', lx, 250, 22, 0.5, sq=2.0))
    L = resolve(cv, lights, gains=(0.4, 0.5, 0.3), warm_bias=0.1)
    a = L.alpha()
    rows = np.arange(L.h)[:, None]
    _haze_toward(L, K.ladder(NI[3], SL[0], SL[1], SL[2]), a * (0.25 + 0.2 * np.clip((140 - rows) / 100.0, 0, 1)))
    return L, info
