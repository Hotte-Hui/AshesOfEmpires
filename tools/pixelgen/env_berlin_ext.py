"""env_berlin_ext -- Berlin dusk seen through the archive windows (parallax layers, 'berlin' palette).

ext_sky  (p 0.05): winter dusk gradient, flat stratus bands, a muted afterglow low in the west.
ext_far  (p 0.10): hazy city silhouettes, chimney smoke and -- far away, muted -- the dome of the
                   fictional completed Great Hall (no insignia, no heroic light).
ext_near (p 0.18): Gruenderzeit tenements across the street: mansards, dormers, chimneys, snow,
                   a few lit windows (emission), a stovepipe, a sealed flat, tram wires.
These layers are only seen through the window cut-outs of the room layer.
"""
from __future__ import annotations

import math

import numpy as np

import env_berlin_insignia as INS
import env_berlin_kit as kit
import env_berlin_layout as L
import pg

Bp = kit.B
RB = kit.Ramps({
    'SKY': [Bp['steel'][1], Bp['steel'][2], Bp['steel'][3], Bp['steel'][4], Bp['steel'][5]],
    'DUSK': [Bp['violet'][1], Bp['violet'][2], Bp['violet'][3], Bp['stone'][2], Bp['stone'][3],
             Bp['stone'][4], Bp['stone'][5], Bp['glow'][3]],
    'HAZE': [Bp['night'][3], Bp['violet'][1], Bp['steel'][1], Bp['violet'][2], Bp['steel'][2],
             Bp['steel'][3], Bp['steel'][4]],
    'DOME': ['#2A2130', '#2C4440', '#454E58', '#3E5D55', '#5F6973'],
    'PAT': [Bp['night'][1], Bp['patina'][0], Bp['patina'][1], Bp['patina'][2], Bp['patina'][3], Bp['patina'][4]],
    'ROOF': [Bp['night'][0], Bp['night'][1], Bp['night'][2], Bp['night'][3], Bp['violet'][1], Bp['violet'][2]],
    'STU': [Bp['night'][2], Bp['violet'][0], Bp['violet'][1], Bp['violet'][2], Bp['violet'][3], Bp['stone'][1],
            Bp['stone'][2]],
    'BRK': [Bp['night'][2], Bp['ochre'][0], Bp['ochre'][1], Bp['ochre'][2], Bp['ochre'][3]],
    'GLW': [Bp['ochre'][3], Bp['ochre'][4], Bp['glow'][0], Bp['glow'][1], Bp['glow'][2], Bp['glow'][3],
            Bp['glow'][4]],
    'SNW': [Bp['violet'][2], Bp['snow'][0], Bp['snow'][1], Bp['snow'][2], Bp['snow'][3], Bp['snow'][4]],
    'WIN': [Bp['night'][0], Bp['steel'][0], Bp['night'][3], Bp['steel'][1], Bp['steel'][2]],
    # flag cloth (archive ink reds -- the post-process snaps to the archive palette)
    'RED': [Bp['night'][1], '#2A1B16', '#7A2A26', '#A8382E'],
})

# far-layer local x of the dome axis: seen through the middle office window when the player stands at it
DOME_X = int(round(L.local_x(L.X(262), L.PARALLAX['ext_far'], L.cam_for(L.X(262)))))
# near-layer anchors (same idea): the low house that opens the dome view, and the two banner positions
LOW_C = int(round(L.local_x(L.X(262), L.PARALLAX['ext_near'], L.cam_for(L.X(262)))))
BANNERS = [  # (local x, through which windows it is mostly seen)
    (int(round(L.local_x(L.LIB_WINDOWS[1][0] + 10, L.PARALLAX['ext_near'], L.cam_for(L.HOTSPOTS['exp_reading_table'][0])))), 'library'),
    (int(round(L.local_x(L.WINDOWS[2][0] + 12, L.PARALLAX['ext_near'], L.cam_for(L.HOTSPOTS['plan_a'][0])))), 'office'),
]
NEAR_SITES = []       # filled by build_near(): (name, x, y, w, h) of insignia sites (banners)


# =========================================================================== sky
def build_sky():
    w = L.layer_width(L.PARALLAX['ext_sky'])
    lay = kit.MLayer(w, L.WORLD_H, RB, 'ext_sky')
    H = L.WORLD_H
    y = np.arange(H, dtype=np.float32)[:, None] + np.zeros((1, w), np.float32)
    # upper sky: cold steel, getting lighter toward the horizon
    t_sky = np.clip(0.4 + (y - 40) / 150 * 2.6, 0.2, 3.4)
    lay.put(np.ones((H, w), bool), 0, 0, 'SKY', t_sky)
    # low afterglow band (muted ochre-mauve), stronger toward the west (left)
    xs = np.arange(w, dtype=np.float32)[None, :]
    glow_y = np.clip((y - 150) / 70, 0, 1)
    west = 0.75 + 0.25 * np.clip((420 - xs) / 420, 0, 1)
    t_dusk = 1.6 + glow_y * 4.6 * west
    m = (y > 148)
    lay.put(m, 0, 0, 'DUSK', t_dusk)
    # flat stratus bands (dark mauve) with thin lit undersides
    rng = np.random.default_rng(7)
    for (by, th, x0, ln) in [(96, 3, -30, 260), (104, 2, 180, 220), (118, 4, 380, 300), (131, 2, 40, 210),
                             (142, 3, 300, 240), (88, 2, 520, 200), (160, 2, 120, 260), (170, 3, 470, 260)]:
        nz = pg.value_noise(ln + 2, 1, 14, int(rng.integers(0, 999)), octaves=2)[0]
        for i in range(ln):
            x = x0 + i
            if not (0 <= x < w):
                continue
            e = math.sin(math.pi * i / ln) ** 0.6
            hh = max(1, int(round(th * e * (0.6 + nz[i]))))
            ramp, tone = ('SKY', 0.6) if by < 148 else ('DUSK', 1.4)
            lay.rect(x, by - hh, 1, hh, ramp, tone, flat=True)
            if by >= 140:
                lay.px(x, by, 'DUSK', 4.2 if by >= 148 else 3.0, flat=True)
            else:
                lay.px(x, by, 'SKY', 1.6, flat=True)
    lay.unlit[:] = True
    lay.resolve(band=3.2)
    return lay


# =========================================================================== far city + Great Hall
def great_hall(lay, cx, base_y):
    """The fictional completed Great Hall, far away: muted patina dome on a colossal block."""
    # colossal cubic base (mostly hidden by nearer roofs) with pilaster rhythm suggested
    bw = 104
    lay.rect(cx - bw // 2, base_y - 14, bw, 60, 'HAZE', 3.0, flat=True)
    lay.rect(cx - bw // 2, base_y - 14, bw, 1, 'HAZE', 4.0, flat=True)
    for k in range(cx - bw // 2 + 3, cx + bw // 2 - 2, 4):
        lay.rect(k, base_y - 12, 1, 58, 'HAZE', 2.4, flat=True)
    # attic step
    lay.rect(cx - 34, base_y - 20, 68, 6, 'HAZE', 3.4, flat=True)
    lay.rect(cx - 34, base_y - 20, 68, 1, 'HAZE', 4.4, flat=True)
    # drum with colonnade
    dw = 42
    dy0 = base_y - 28
    lay.rect(cx - dw // 2, dy0, dw, 10, 'HAZE', 3.6, flat=True)
    for k in range(cx - dw // 2 + 1, cx + dw // 2 - 1, 3):
        lay.rect(k, dy0 + 2, 1, 7, 'HAZE', 2.6, flat=True)
    lay.rect(cx - dw // 2, dy0, dw, 1, 'HAZE', 4.6, flat=True)
    # dome cap (patina green-black, heavily hazed)
    r = 21.0
    ry = 17.0
    m, mx, my = lay.ellipse_mask(cx, dy0, r, ry)
    rows = np.arange(m.shape[0])[:, None] + my
    m &= rows < dy0
    yy, xx = np.mgrid[0:m.shape[0], 0:m.shape[1]]
    u = (xx + mx + 0.5 - cx) / r
    v = (yy + my + 0.5 - dy0) / ry
    # soft light from the upper left (sky dome) -> slightly lighter left flank, no hot rim
    tone = 1.6 + 1.1 * np.clip(-u * 0.8 - v * 0.4, -1, 1)
    lay.put(m, mx, my, 'DOME', tone)
    # ribs
    for a in np.linspace(-0.8, 0.8, 7):
        for yv in np.linspace(-1, -0.05, 26):
            xv = a * math.sqrt(max(0.0, 1 - yv * yv))
            px_, py_ = int(round(cx + xv * r)), int(round(dy0 + yv * ry))
            if 0 <= py_ - my < m.shape[0] and 0 <= px_ - mx < m.shape[1] and m[py_ - my, px_ - mx]:
                lay.px(px_, py_, 'DOME', 0.0 if a > 0 else 1.0, flat=True)
    # lantern
    lay.rect(cx - 3, dy0 - int(ry) - 7, 7, 8, 'HAZE', 2.6, flat=True)
    lay.rect(cx - 3, dy0 - int(ry) - 7, 1, 8, 'HAZE', 3.6, flat=True)
    lay.rect(cx - 1, dy0 - int(ry) - 10, 3, 3, 'DOME', 1.0, flat=True)
    lay.px(cx, dy0 - int(ry) - 12, 'HAZE', 2.4, flat=True)
    lay.px(cx, dy0 - int(ry) - 11, 'HAZE', 2.4, flat=True)
    # atmospheric haze veil over the whole monument (it is kilometres away)
    hm = (lay.rid >= 0)
    box = np.zeros_like(hm)
    box[dy0 - int(ry) - 14:base_y + 50, cx - bw // 2 - 2:cx + bw // 2 + 2] = True
    sel = hm & box
    th = pg.bayer(lay.w, lay.h, 1, 3)
    up = sel & (th < 0.22) & (lay.rid == RB['DOME'])
    lay.tone[up] += 1.0


def build_far():
    w = L.layer_width(L.PARALLAX['ext_far'])
    lay = kit.MLayer(w, L.WORLD_H, RB, 'ext_far')
    rng = np.random.default_rng(31)
    horizon = 196
    # back row of city silhouettes (very hazy)
    x = -10
    while x < w + 10:
        bw = int(rng.integers(26, 70))
        bh = int(rng.integers(16, 34))
        top = horizon - bh
        lay.rect(x, top, bw, 200, 'HAZE', 4.0, flat=True)
        # roof shapes
        if rng.random() < 0.5:
            for k in range(6):
                lay.rect(x + k, top - 6 + k, bw - 2 * k, 1, 'HAZE', 4.0, flat=True)
        if rng.random() < 0.5:
            cxx = x + int(rng.integers(4, max(5, bw - 4)))
            lay.rect(cxx, top - int(rng.integers(5, 12)), 2, 14, 'HAZE', 3.6, flat=True)
        x += bw
    # mid row (a bit darker, a few lit windows)
    x = -20
    lit = []
    while x < w + 20:
        bw = int(rng.integers(30, 64))
        bh = int(rng.integers(8, 22))
        top = horizon + 4 - bh
        lay.rect(x, top, bw, 200, 'HAZE', 2.8, flat=True)
        lay.rect(x, top, bw, 1, 'HAZE', 3.6, flat=True)
        if rng.random() < 0.6:     # pitched/mansard roof
            for k in range(5):
                lay.rect(x + k + 1, top - 5 + k, bw - 2 * k - 2, 1, 'HAZE', 2.4, flat=True)
        for _ in range(int(rng.integers(0, 4))):
            lx_ = x + int(rng.integers(2, max(3, bw - 2)))
            ly_ = top + int(rng.integers(3, 14))
            lit.append((lx_, ly_))
        if rng.random() < 0.45:     # chimney stacks
            cxx = x + int(rng.integers(3, max(4, bw - 6)))
            lay.rect(cxx, top - 8, 3, 9, 'HAZE', 2.2, flat=True)
        x += bw
    # gasholder frame far right and a slim church spire left (generic, not a real landmark)
    gx = DOME_X + 330
    for k in range(5):
        lay.rect(gx + k * 9, horizon - 30, 1, 30, 'HAZE', 3.0, flat=True)
    for yy in range(horizon - 30, horizon, 6):
        lay.rect(gx, yy, 37, 1, 'HAZE', 3.0, flat=True)
    lay.rect(gx + 2, horizon - 20, 33, 20, 'HAZE', 3.4, flat=True)
    sx = DOME_X - 240
    lay.poly([(sx - 3, horizon - 22), (sx + 4, horizon - 22), (sx + 1, horizon - 58)], 'HAZE', 3.2)
    lay.rect(sx - 4, horizon - 22, 9, 30, 'HAZE', 3.2, flat=True)
    lay.px(sx + 1, horizon - 60, 'HAZE', 3.2)
    # the Great Hall
    great_hall(lay, DOME_X, horizon - 6)
    # tall industrial chimneys with smoke drifting east (coal heating, winter)
    for (cx_, top, seed) in [(DOME_X - 300, 124, 1), (DOME_X - 110, 120, 3), (DOME_X + 190, 132, 5),
                             (DOME_X + 420, 126, 9)]:
        lay.rect(cx_ - 2, top, 4, horizon - top + 4, 'HAZE', 2.6, flat=True)
        lay.rect(cx_ - 2, top, 1, horizon - top + 4, 'HAZE', 3.4, flat=True)
        lay.rect(cx_ - 3, top, 6, 2, 'HAZE', 2.2, flat=True)
        smoke = pg.Layer(260, 120, 'smoke')
        path = [(10, 108), (40, 96), (90, 84), (160, 78), (250, 70)]
        tones = [3, 4, 5]
        cols = [RB.color('HAZE', t) for t in tones]
        pg.smoke_ribbon(smoke, path, 2, 9, cols, seed=seed, gaps=0.45)
        # smoke_ribbon wrote palette RGB into .c -> transfer back to tone indices exactly
        a = smoke.c[..., 3] > 0
        tt = np.zeros(a.shape, np.float32)
        for t, c in zip(tones, cols):
            tt[np.all(smoke.c == c, axis=-1)] = t
        lay.put(a, cx_ - 10, top - 108 + 1, 'HAZE', tt, flat=True)
    # dim lit windows (emission)
    for (lx_, ly_) in lit:
        if 0 <= lx_ < w and lay.rid[ly_, lx_] >= 0:
            lay.px(lx_, ly_, 'GLW', float(rng.choice([1.0, 2.0])), emis=True, flat=True)
    lay.unlit[:] = True
    lay.resolve()
    return lay


# =========================================================================== near tenements
def tenement(lay, x0, x1, cornice_y, rng, kind='mansard', lit_p=0.22, sealed=False, stovepipe=False,
             firewall=False, ghost=None):
    """Upper part of a Gruenderzeit tenement seen across the street at dusk."""
    W = x1 - x0
    bottom = L.WORLD_H
    # facade (stucco) in shadow
    face = float(rng.choice([3.0, 3.4, 3.8]))
    lay.rect(x0, cornice_y, W, bottom - cornice_y, 'STU', face, flat=True)
    lay.rect(x0, cornice_y, 1, bottom - cornice_y, 'STU', face + 0.8, flat=True)
    lay.rect(x1 - 1, cornice_y, 1, bottom - cornice_y, 'STU', face - 1.0, flat=True)
    # heavy cornice with brackets
    lay.rect(x0 - 2, cornice_y - 5, W + 4, 5, 'STU', face + 0.6, flat=True)
    lay.rect(x0 - 2, cornice_y - 5, W + 4, 1, 'SNW', 2.0, flat=True)      # snow on the cornice
    lay.rect(x0 - 2, cornice_y - 1, W + 4, 1, 'STU', face - 1.4, flat=True)
    for k in range(x0 + 2, x1 - 2, 6):
        lay.rect(k, cornice_y, 2, 3, 'STU', face + 0.4, flat=True)
        lay.px(k + 1, cornice_y + 3, 'STU', face - 1.2)
    # window rows below the cornice
    lit_rects = []
    ww, wh, gap = 6, 14, 7
    n = max(1, (W - 6) // (ww + gap))
    ox = x0 + (W - (n * ww + (n - 1) * gap)) // 2
    for row in range(2):
        wy = cornice_y + 10 + row * 34
        for i in range(n):
            wx = ox + i * (ww + gap)
            # stucco surround + hood
            lay.rect(wx - 2, wy - 4, ww + 4, 2, 'STU', face + 0.8, flat=True)
            lay.rect(wx - 2, wy - 2, ww + 4, 1, 'SNW', 1.6, flat=True)
            lay.rect(wx - 1, wy - 1, ww + 2, wh + 2, 'STU', face + 0.5, flat=True)
            roll = rng.random()
            if sealed and row == 0 and i == n // 2:
                lay.rect(wx, wy, ww, wh, 'ROOF', 4.0, flat=True)            # boarded
                for (a, b) in ((0, 0), (ww - 1, 0)):
                    lay.line(wx + a, wy, wx + (ww - 1 - a), wy + wh - 1, 'STU', 5.0)
            elif roll < lit_p:
                lay.rect(wx, wy, ww, wh, 'GLW', 2.4, emis=True, flat=True)
                lay.rect(wx, wy, ww, 2, 'GLW', 1.4, emis=True, flat=True)
                # curtain shapes / a sash bar
                lay.rect(wx + ww // 2, wy, 1, wh, 'GLW', 0.6, emis=True, flat=True)
                if rng.random() < 0.6:
                    lay.rect(wx, wy + 2, 2, wh - 2, 'GLW', 1.2, emis=True, flat=True)
                if rng.random() < 0.25:     # a silhouette at the window
                    lay.rect(wx + 2, wy + 5, 2, wh - 5, 'ROOF', 1.0, flat=True)
                    lay.px(wx + 2, wy + 4, 'ROOF', 1.0)
                lit_rects.append((wx, wy, ww, wh))
            else:
                lay.rect(wx, wy, ww, wh, 'WIN', 1.0 + rng.random() * 1.5, flat=True)
                lay.rect(wx + ww // 2, wy, 1, wh, 'STU', face - 0.6, flat=True)
                lay.px(wx, wy, 'WIN', 4.0)
            # sill with snow
            lay.rect(wx - 1, wy + wh + 1, ww + 2, 1, 'SNW', 2.2, flat=True)
            lay.rect(wx - 1, wy + wh + 2, ww + 2, 1, 'STU', face - 1.4, flat=True)
        if stovepipe and row == 0:
            sx = ox + (n - 1) * (ww + gap) + ww // 2
            lay.rect(sx, wy + 3, 1, 2, 'BRK', 1.0, flat=True)
            lay.rect(sx, wy + 3, 9, 1, 'ROOF', 3.0, flat=True)
            lay.rect(sx + 8, wy - 10, 1, 14, 'ROOF', 3.0, flat=True)
            lay.rect(sx + 7, wy - 11, 3, 1, 'ROOF', 3.6, flat=True)
            for k, (dx, dy) in enumerate([(9, -14), (10, -17), (12, -19), (15, -21), (18, -22)]):
                lay.rect(sx + dx, wy + dy, 2 + k // 2, 2, 'HAZE', 4.0 - k * 0.3, flat=True)
    # roof
    if kind == 'mansard':
        rt = cornice_y - 5
        steep = 15
        lay.poly([(x0 - 1, rt), (x1, rt), (x1 - 4, rt - steep), (x0 + 3, rt - steep)], 'ROOF', 2.6)
        lay.rect(x0 + 3, rt - steep - 6, W - 7, 6, 'ROOF', 1.8, flat=True)
        # slate courses
        for yy in range(rt - steep + 2, rt, 3):
            lay.rect(x0 + 1, yy, W - 2, 1, 'ROOF', 1.6, flat=True)
        # snow on the upper flat and the mansard break
        lay.rect(x0 + 3, rt - steep - 7, W - 7, 2, 'SNW', 2.4, flat=True)
        lay.rect(x0 + 3, rt - steep - 7, W - 7, 1, 'SNW', 3.2, flat=True)
        lay.rect(x0 + 2, rt - steep, W - 4, 1, 'SNW', 2.0, flat=True)
        # dormers
        for dx in range(x0 + 10, x1 - 12, 26):
            lay.rect(dx, rt - steep + 2, 9, steep - 3, 'STU', 2.6, flat=True)
            lay.poly([(dx - 1, rt - steep + 2), (dx + 9, rt - steep + 2), (dx + 4, rt - steep - 3)], 'ROOF', 3.0)
            lay.line(dx - 1, rt - steep + 2, dx + 4, rt - steep - 3, 'SNW', 3.6)
            lay.line(dx + 4, rt - steep - 3, dx + 9, rt - steep + 2, 'SNW', 2.8)
            if rng.random() < 0.4:
                lay.rect(dx + 2, rt - steep + 4, 5, 6, 'GLW', 2.0, emis=True, flat=True)
                lit_rects.append((dx + 2, rt - steep + 4, 5, 6))
            else:
                lay.rect(dx + 2, rt - steep + 4, 5, 6, 'WIN', 1.4, flat=True)
        roof_top = rt - steep - 7
    else:  # flat roof with parapet
        roof_top = cornice_y - 8
        lay.rect(x0 - 1, roof_top, W + 2, 3, 'STU', face - 0.6, flat=True)
        lay.rect(x0 - 1, roof_top, W + 2, 1, 'SNW', 3.6, flat=True)
    # chimney stacks with snow caps and thin smoke
    for k in range(int(rng.integers(1, 3))):
        cx = x0 + int(rng.integers(6, max(7, W - 10)))
        ch = int(rng.integers(10, 18))
        lay.rect(cx, roof_top - ch, 6, ch + 2, 'BRK', 1.6, flat=True)
        lay.rect(cx, roof_top - ch, 1, ch + 2, 'BRK', 2.6, flat=True)
        lay.rect(cx + 5, roof_top - ch, 1, ch + 2, 'BRK', 0.6, flat=True)
        for yy in range(roof_top - ch + 3, roof_top, 3):
            lay.rect(cx + 1, yy, 4, 1, 'BRK', 0.8, flat=True)
        lay.rect(cx - 1, roof_top - ch - 2, 8, 2, 'STU', 2.0, flat=True)
        lay.rect(cx - 1, roof_top - ch - 3, 8, 1, 'SNW', 4.0, flat=True)
        if rng.random() < 0.7:
            for j in range(6):
                lay.rect(cx + 1 + j * 2, roof_top - ch - 5 - j * 2 - (j * j) // 4, 3 + j // 2, 2, 'HAZE',
                         4.6 - j * 0.35, flat=True)
    # firewall (blank side wall where the neighbour was torn down) with a faded ghost sign
    if firewall:
        fx0 = x1
        fw = 26
        top = roof_top + 2
        lay.rect(fx0, top, fw, L.WORLD_H - top, 'STU', 2.2, flat=True)
        lay.rect(fx0, top, fw, 1, 'SNW', 2.8, flat=True)
        for yy in range(top + 6, L.WORLD_H, 9):
            lay.rect(fx0 + 2, yy, fw - 4, 1, 'STU', 1.6, flat=True)
        if ghost:
            m = kit.text_mask(ghost, '35')
            mm = m[:, :min(m.shape[1], fw - 4)]
            lay.put(mm, fx0 + 2, top + 14, 'STU', 3.0, flat=True)
    return lit_rects, roof_top


def banner(lay, x, top, w, h, hist: bool):
    """Long state banner hanging down a facade (insignia site).  neutral: grey-black cloth with the fictional
    Reichssiegel (black disc, white pillar); hist: red cloth, white disc, black swastika standing on a corner."""
    rng = np.random.default_rng(900 + x)
    field_r, t0 = ('RED', 2.0) if hist else ('HAZE', 4.4)       # neutral: grey cloth that reads on the facade
    # rod + cords
    lay.rect(x - 2, top - 2, w + 4, 2, 'ROOF', 1.0, flat=True)
    lay.px(x - 2, top - 3, 'SNW', 3.0)
    # cloth with vertical folds and a waving lower edge
    for xx in range(w):
        fold = 0.55 * math.sin(xx / w * math.pi * 3.0 + 0.6)
        hh = h - int(round(1.5 + 1.5 * math.sin(xx * 0.9)))
        lay.rect(x + xx, top, 1, hh, field_r, t0 + fold, flat=False)
    lay.rect(x, top, 1, h - 2, field_r, t0 + 0.7, flat=True)
    lay.rect(x + w - 1, top, 1, h - 3, field_r, t0 - 0.9, flat=True)
    # emblem disc in the upper third
    d = w - 4 if (w - 4) % 2 == 1 else w - 5
    cx, cy = x + w // 2, top + 6 + d // 2
    m, mx, my = lay.ellipse_mask(cx + 0.5, cy + 0.5, d / 2.0, d / 2.0)
    if hist:
        lay.put(m, mx, my, 'SNW', 4.0, flat=True)
        sd = d - 3 if (d - 3) % 2 == 1 else d - 4
        sw = INS.swastika_mask(sd)
        lay.put(sw, cx - sd // 2, cy - sd // 2 + (0 if sd % 2 else 0), 'ROOF', 0.0, flat=True)
    else:
        lay.put(m, mx, my, 'ROOF', 0.0, flat=True)
        disc, pillar = kit.reichssiegel_mask(d)
        lay.put(pillar, cx - d // 2, cy - d // 2, 'SNW', 3.6, flat=True)
    # a thin stripe of snow on the rod
    lay.rect(x - 1, top - 3, w + 2, 1, 'SNW', 4.0, flat=True)


def build_near(hist: bool = False):
    w = L.layer_width(L.PARALLAX['ext_near'])
    lay = kit.MLayer(w, L.WORLD_H, RB, 'ext_near')
    rng = np.random.default_rng(57)
    lits = []
    lc = LOW_C
    plan = [
        # x0, x1, cornice_y, kind, sealed, stovepipe, firewall, ghost
        (-8, 96, 190, 'mansard', False, False, False, None),
        (96, 196, 184, 'mansard', True, False, True, 'KOHLEN'),
        (222, 318, 196, 'mansard', False, True, False, None),
        (318, 410, 188, 'mansard', False, False, False, None),
        (410, lc - 48, 186, 'mansard', True, True, False, None),
        (lc - 48, lc + 48, 206, 'flat', False, True, False, None),       # low house: opens the view to the dome
        (lc + 48, lc + 152, 184, 'mansard', False, False, False, None),
        (lc + 152, lc + 250, 192, 'mansard', True, True, False, None),
        (lc + 250, lc + 340, 182, 'mansard', False, False, True, None),
        (lc + 366, lc + 460, 188, 'mansard', False, False, False, None),
        (lc + 460, w + 8, 194, 'mansard', False, True, False, None),
    ]
    cornice_at = {}
    for (x0, x1, cy, kind, sealed, stove, fw, ghost) in plan:
        if x1 <= x0:
            continue
        lr, top = tenement(lay, x0, x1, cy, rng, kind=kind, sealed=sealed, stovepipe=stove, firewall=fw,
                           ghost=ghost)
        lits += lr
        for xx in range(max(0, x0), min(w, x1)):
            cornice_at[xx] = cy
    # state banners hanging from the cornices (insignia sites; the _hist decals overlay them)
    NEAR_SITES.clear()
    for i, (bx, _) in enumerate(BANNERS):
        cy = cornice_at.get(bx + 10, 186)
        bw, bh = 20, 70
        banner(lay, bx, cy + 1, bw, bh, hist=hist)
        NEAR_SITES.append(('banner_%d' % (i + 1), (bx - 3, cy - 4, bw + 6, bh + 6), (bx, cy + 1, bw, bh)))
    # tram line: straight contact wires (pantographs touch L.TRAM_WIRE_Y), bracket arms on poles, mercury lamps
    for wy in (L.TRAM_WIRE_Y, L.TRAM_WIRE_Y + 3):
        lay.rect(0, wy, w, 1, 'ROOF', 1.0, flat=True)
    for x0 in range(-40, w + 40, 120):
        wy = L.TRAM_WIRE_Y
        lay.rect(x0, wy - 10, 1, 170, 'ROOF', 2.4, flat=True)
        lay.rect(x0 - 3, wy - 6, 7, 1, 'ROOF', 1.4, flat=True)
        lay.line(x0, wy - 5, x0 + 22, wy - 3, 'ROOF', 1.6)                          # bracket arm
        lay.line(x0 + 1, wy + 4, x0 + 22, wy - 3, 'ROOF', 1.4)                      # brace
        lay.rect(x0 + 21, wy - 3, 1, 3, 'ROOF', 1.2, flat=True)                     # hanger to the wire
        # street lamp hanging from the span wire (a cold mercury lamp), clear of the banners
        lx = x0 + 36
        lay.rect(lx, wy - 9, 1, 5, 'ROOF', 1.4, flat=True)
        lay.rect(lx - 2, wy - 4, 5, 2, 'ROOF', 2.0, flat=True)
        lay.rect(lx - 1, wy - 2, 3, 1, 'SNW', 5.0, emis=True, flat=True)
    lay.unlit[:] = True
    lay.resolve()
    lay.lit_windows = lits
    return lay


def build_all():
    return {'ext_sky': build_sky(), 'ext_far': build_far(), 'ext_near': build_near()}
