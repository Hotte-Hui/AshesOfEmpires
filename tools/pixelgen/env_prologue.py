"""env_prologue -- the painted shots of the prologue LS_Prologue (scenes/cinematics/prologue, round 11).

Run:  py -3 -P tools/pixelgen/env_prologue.py [--preview DIR]

Five shots (640 x 360 frame, letterbox band y 46..314), written to assets/cinematics/prologue/:
  p1_line.png      dusk over the snowfield: the armistice Line (posts, wire, control strip, dragon's teeth, a
                   watchtower against the last light), ruined villages on the horizon, a birch in front (680 wide:
                   the camera drifts right)
  p2_map.png       a paper map under a desk lamp: Baltic and Black Sea, rivers, BERLIN / KARSK; the Line, Veltrava
                   and the three corridors are drawn on it at runtime (points in layout.json) + p2_veltrava.png
  p3_papers.png    a freight office desk: the bilingual Frachtbrief (wagons 17-0417 ...), a card index, a lead
                   seal, the ink pad; p3_stamp.png / p3_shadow.png / p3_imprint.png (the C-17 stamp lands)
  p4_berlin.png    a drafting hall in Berlin at dawn: a tall window, rooftops in snow, the dome of the Great Hall in
                   the haze; blueprints, a desk lamp (p4_lampglow.png); Konrad (p4_konrad.png, idle_back re-lit)
  p5_karsk.png     the Karsk yard at night: tracks into the dark, a floodlight, the lit signal box, a waiting
                   locomotive, a wagon with a chalked number; p5_alexei_walk.png / p5_alexei_idle.png (re-lit),
                   p5_cone.png (floodlight, additive), p5_signal.png (red | green), p5_headlamp.png
No insignia anywhere (nothing for Symbols.pick() to swap).  layout.json carries every runtime anchor.
"""
from __future__ import annotations

import os
import sys

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import env_prologue_kit as K  # noqa: E402

LAYOUT: dict = {}


def _h(i, seed):
    """Deterministic 0..1 hash."""
    x = (int(i) * 374761393 + int(seed) * 668265263) & 0xFFFFFFFF
    x = ((x ^ (x >> 13)) * 1274126177) & 0xFFFFFFFF
    return ((x ^ (x >> 16)) & 0xFFFF) / 65535.0


def near(m, r):
    return K.blur(m.astype(np.float32), r) > 0.001


# ================================================================================================ p1 the Line
def shot_line():
    W, H, HZ = 680, 360, 222
    cv = K.Canvas(W, H)
    yy, xx = cv.yy, cv.xx
    sky = cv.box(0, 0, W, HZ + 1)
    cv.vgrad(sky, [(30, '#121826'), (96, '#1f283d'), (148, '#333b55'), (188, '#55526a'), (210, '#86707a'),
                   (HZ, '#b78a76')])
    cv.glow(470, HZ + 12, 340, 96, '#d4966c', 0.55, m=sky)
    cv.glow(470, HZ + 4, 150, 30, '#f0c48c', 0.8, m=sky)
    lit = cv.falloff(470, HZ, 380, 170, 1.1)
    n = K.noise(W, H, 30, 11, 3, sx=6.0)
    band = np.clip(1 - np.abs(yy - 118) / 64, 0, 1)
    cl = sky & (n * (0.5 + 0.62 * band) > 0.6)
    cv.mix(cl, '#232a3b', 0.8)
    rim = K.edge(cl, 0, 1) | K.edge(cl, 0, 2)
    cv.mix(rim, '#a8786a', lit * 0.85)
    thin = sky & ~cl & (n * (0.5 + 0.62 * band) > 0.55)
    cv.mix(thin, '#2c3348', 0.45)
    # ground: blue snow, warm sheen under the glow, wind-streaked drifts
    gr = cv.box(0, HZ, W, H)
    cv.vgrad(gr, [(HZ, '#a08e98'), (238, '#8a8ca5'), (282, '#707b98'), (H, '#5b6685')])
    cv.glow(470, HZ + 2, 300, 42, '#d6a68c', 0.55, m=gr)
    persp = np.clip((yy - HZ) / (H - HZ), 0, 1)
    dn = K.noise(W, H, 70, 31, 3, sx=4.0)
    cv.mix(gr, '#b9c1d3', np.clip((dn - 0.5) * 1.6, 0, 1) * (0.2 + 0.4 * persp))
    cv.mix(gr, '#4d5774', np.clip((0.5 - dn) * 1.6, 0, 1) * (0.1 + 0.4 * persp))
    for i in range(60):
        y0 = HZ + 8 + (H - HZ) * _h(i, 32) ** 1.6
        x0 = _h(i, 33) * W
        ln = 20 + 90 * (y0 - HZ) / (H - HZ)
        cv.mix(cv.stroke([(x0, y0), (x0 + ln, y0 - 1)], 1) & gr, '#c9d0de', 0.45)
        cv.mix(cv.stroke([(x0 + 4, y0 + 1), (x0 + ln * 0.8, y0)], 1) & gr, '#4f5a78', 0.35)
    # hills, a dark tree line and ruined villages on the horizon
    top = HZ - 2 - 6 * K.noise1d(W, 70, 21)
    tr = K.noise1d(W, 2.5, 22, 2)
    top = top - np.where(tr > 0.56, (tr - 0.56) * 22, 0) * (K.noise1d(W, 90, 23) > 0.45)
    far = (yy >= top[None, :]) & (yy <= HZ + 1)
    cv.fill(far, '#363b52')
    cv.mix(far, '#5e5262', cv.falloff(470, HZ, 170, 30, 1.0) * 0.8)
    ru = np.zeros((H, W), bool)
    for x0, w, hh in [(52, 16, 7), (70, 12, 9), (112, 22, 10), (168, 26, 8), (202, 14, 7), (610, 20, 8), (636, 14, 6)]:
        ru |= cv.box(x0, HZ - hh, x0 + w, HZ + 1)
        ru |= cv.poly([(x0, HZ - hh), (x0 + w / 2, HZ - hh - w * 0.4), (x0 + w, HZ - hh)])
    ru |= cv.box(96, HZ - 32, 105, HZ)                                     # the broken church tower
    ru |= cv.poly([(96, HZ - 32), (99, HZ - 39), (101, HZ - 34), (103, HZ - 41), (105, HZ - 32)])
    for x, hh in [(150, 27), (157, 19), (240, 17), (596, 22)]:
        ru |= cv.box(x, HZ - hh, x + 3, HZ)
    holes = cv.box(116, HZ - 8, 120, HZ - 5) | cv.box(176, HZ - 6, 181, HZ - 3) | cv.box(99, HZ - 26, 102, HZ - 22)
    cv.fill(ru & ~holes, '#2e3347')
    cv.fill(ru & holes, '#6e6070')
    # the Line: control strip, fence, dragon's teeth (all toward one vanishing point)
    VP = np.array([214.0, HZ - 1.0])

    def on(p0, s):
        return VP + (np.asarray(p0, np.float32) - VP) * s

    A0, C0, D0 = (730.0, 342.0), (626.0, 372.0), (500.0, 372.0)
    strip_m = cv.poly([tuple(VP), A0, (760, 372), C0]) & gr
    cv.mix(strip_m, '#56607c', 0.5)
    for i in range(16):
        x = K.lerp(C0[0], 770, i / 15)
        cv.mix(cv.stroke([tuple(VP), (x, 372)], 1) & strip_m & (yy > HZ + 6), '#454d68', 0.5)
    posts = []
    i = 0
    while True:
        s = 1.0 / (1.0 + 0.42 * i)
        i += 1
        if s < 0.045:
            break
        b = on(A0, s)
        hgt, wd = 54 * s, max(1, int(round(4.2 * s)))
        x0 = int(round(b[0] - wd / 2))
        m = cv.box(x0, b[1] - hgt, x0 + wd, b[1] + 1)
        cv.fill(m, '#24273a')
        if wd >= 2:
            side = x0 + wd - 1 if b[0] < 470 else x0
            cv.fill(m & cv.box(side, 0, side + 1, H), '#6c5f6c')
            cv.fill(cv.box(x0, b[1] - hgt, x0 + wd, b[1] - hgt + 1), '#d9dde6')
        posts.append((b[0], b[1], hgt))
    for (xa, ya, ha), (xb, yb, hb) in zip(posts, posts[1:]):
        for f in (0.32, 0.58, 0.84):
            pa, pb = (xa, ya - ha * f), (xb, yb - hb * f)
            sag = 2.5 * ha / 54
            pts = [(K.lerp(pa[0], pb[0], u), K.lerp(pa[1], pb[1], u) + sag * 4 * u * (1 - u)) for u in np.linspace(0, 1, 9)]
            wire = cv.stroke(pts, 1)
            cv.fill(wire, '#2b2e3e')
            if ha > 14:
                for j, (px, py) in enumerate(pts[1:-1]):
                    if j % 2 == 0:
                        cv.fill(cv.box(px, py - 1, px + 1, py + 2), '#2b2e3e')
    for i in range(3, 13):
        s = 1.0 / (1.0 + 0.5 * i) * 1.9
        if s > 0.95:
            continue
        b = on(D0, s)
        w2, hh = 9 * s, 13 * s
        tooth = cv.poly([(b[0] - w2, b[1]), (b[0] - w2 * 0.15, b[1] - hh), (b[0] + w2, b[1])])
        cv.fill(tooth, '#41465a')
        cv.fill(tooth & (xx > b[0] - w2 * 0.15), '#33374a')
        cv.fill(K.edge(tooth, 0, -1) & (xx < b[0] + 1), '#c9b4ac')
        cv.fill(tooth & (yy < b[1] - hh * 0.7), '#d6dbe5')
        cv.mix(cv.ell(b[0] + w2 * 0.6, b[1] + 1, w2 * 1.3, 2 + 2 * s) & ~tooth & gr, '#3e4662', 0.45)
    # the watchtower, black against the last light
    tx, ty = 414, 262
    tw = np.zeros((H, W), bool)
    for sx in (-1, 1):
        tw |= cv.stroke([(tx + 13 * sx, ty), (tx + 7 * sx, ty - 62)], 2)
    tw |= cv.stroke([(tx - 12, ty - 8), (tx + 8, ty - 40)], 1) | cv.stroke([(tx + 12, ty - 8), (tx - 8, ty - 40)], 1)
    tw |= cv.stroke([(tx - 9, ty - 42), (tx + 7, ty - 60)], 1) | cv.stroke([(tx + 9, ty - 42), (tx - 7, ty - 60)], 1)
    tw |= cv.box(tx - 10, ty - 41, tx + 10, ty - 39)
    tw |= cv.box(tx - 12, ty - 78, tx + 12, ty - 61)
    roof = cv.poly([(tx - 16, ty - 78), (tx, ty - 88), (tx + 16, ty - 78)])
    tw |= roof | cv.box(tx + 7, ty - 84, tx + 12, ty - 80)
    cv.fill(tw, '#1c1f2c')
    cv.fill(K.edge(tw, 1, 0) & (yy > ty - 90), '#6d5a64')
    cv.fill(roof & ~cv.poly([(tx - 14, ty - 77), (tx, ty - 85), (tx + 14, ty - 77)]), '#d8dce6')
    win = cv.box(tx - 9, ty - 75, tx + 9, ty - 71)
    cv.fill(win, '#f1b65f')
    cv.fill(cv.box(tx - 3, ty - 75, tx - 2, ty - 71) | cv.box(tx + 3, ty - 75, tx + 4, ty - 71), '#1c1f2c')
    cv.fill(cv.box(tx + 11, ty - 83, tx + 13, ty - 81), '#fff3d2')
    cv.mix(cv.ell(tx + 2, ty + 2, 22, 4) & gr, '#3b4360', 0.5)
    # the birch in front (left), dry grass
    trunk = cv.poly([(26, 372), (43, 372), (39, 26), (34, 26)])
    cv.fill(trunk, '#b6b9c6')
    cx_t = 30 + (39 - 30) * (372 - yy) / 346
    cv.fill(trunk & (xx > cx_t + 3), '#7c8294')
    cv.fill(trunk & (xx > cx_t + 5) & (yy > 150), '#5c6276')
    for i in range(30):
        y = 34 + i * 11 + int(_h(i, 5) * 6)
        x0 = 30 + (39 - 30) * (372 - y) / 346 - 4
        w = 2 + int(_h(i, 6) * 5)
        cv.fill(trunk & cv.box(x0 + _h(i, 7) * 5, y, x0 + _h(i, 7) * 5 + w, y + 1 + (i % 3 == 0)), '#25252e')
    br = np.zeros((H, W), bool)
    for i, (y0, dx, dy) in enumerate([(70, -40, -50), (96, 44, -40), (128, -52, -30), (150, 60, -46), (190, -34, -28),
                                      (226, 48, -22), (60, 30, -44), (110, -26, -56)]):
        x0 = 30 + (39 - 30) * (372 - y0) / 346 + 3
        pts = [(x0, y0), (x0 + dx * 0.5, y0 + dy * 0.55 + 4), (x0 + dx, y0 + dy)]
        br |= cv.stroke(pts, 2 if i < 4 else 1)
        for j in range(4):
            u = 0.35 + 0.18 * j
            px, py = x0 + dx * u, y0 + dy * u
            br |= cv.stroke([(px, py), (px + dx * 0.25 * (1 if j % 2 else -0.4), py - 10 - 6 * _h(i * 7 + j, 8))], 1)
    cv.fill(br & ~trunk, '#2c2a35')
    for i in range(70):
        x = int(_h(i, 9) * 230)
        y = 346 + int(_h(i, 10) * 18)
        h = 5 + int(_h(i, 11) * 12)
        cv.fill(cv.stroke([(x, y), (x + (_h(i, 12) - 0.5) * 8, y - h)], 1), '#7d6f58' if i % 3 else '#4c4538')
    img = K.resolve(cv, 56, keep=('#f1b65f', '#fff3d2', '#24273a', '#d9dde6'))
    K.save(img, 'p1_line.png')
    LAYOUT['line'] = {'pan': W - 640, 'lamp': [tx + 12, ty - 82], 'window': [tx - 9, ty - 75, tx + 9, ty - 71],
                      'horizon': HZ, 'beam_y': [262, 330]}
    K.save(K.glow_sprite(48, 24, 24, 12, 22, 11, '#f0a050', levels=5, amax=0.55), 'p1_windowglow.png')
    return img


# ================================================================================================ p2 the map
def shot_map():
    W, H = 640, 360
    cv = K.Canvas(W, H)
    yy, xx = cv.yy, cv.xx
    full = cv.box(0, 0, W, H)
    cv.fill(full, '#261b16')
    cv.mix(full, '#3c2b20', K.noise(W, H, 10, 41, 3, sx=9.0) * 0.9)
    P0, P1 = (34, 50), (606, 340)
    cv.mix(cv.box(P0[0] + 3, P0[1] + 4, P1[0] + 4, P1[1] + 5), '#0e0a08', 0.6)
    paper = cv.box(P0[0], P0[1], P1[0], P1[1])
    cv.fill(paper, '#d8caa4')
    st = K.noise(W, H, 46, 42, 4)
    cv.mix(paper, '#c2b08a', np.clip((st - 0.52) * 2.2, 0, 1) * 0.55)
    cv.mix(paper, '#e4d9ba', np.clip((0.42 - st) * 2.5, 0, 1) * 0.5)
    cv.mix(cv.ell(470, 120, 22, 16) & ~cv.ell(470, 120, 19, 13) & paper, '#b39d78', 0.45)   # a cup ring
    land = paper.copy()

    def sea_fill(m):
        cv.fill(m, '#a3b2aa')
        lm = land & ~m
        for r, k in ((2, 0.0), (4, 0.55), (7, 0.35)):
            ring = m & near(lm, r) & ~near(lm, r - 1)
            cv.mix(ring, '#7f928d', 0.8 if r == 2 else k)
        cv.fill(m & near(lm, 1), '#5c6c68')

    coast = [(34, 96), (70, 101), (104, 108), (128, 113), (150, 108), (176, 114), (204, 118), (232, 113), (256, 121),
             (276, 129), (290, 124), (304, 116), (322, 108), (338, 96), (346, 82), (352, 70), (366, 62), (396, 65),
             (424, 71), (452, 66), (486, 71), (514, 63), (544, 58), (572, 53), (606, 51)]
    sea = cv.poly([(34, 50)] + coast + [(606, 50)]) & paper
    sea &= ~cv.poly([(116, 50), (124, 58), (140, 66), (160, 70), (182, 67), (200, 61), (214, 55), (222, 50)])
    sea &= ~cv.ell(262, 76, 4, 9) & ~cv.ell(318, 60, 3, 6)
    black = cv.poly([(458, 341), (468, 312), (486, 298), (512, 290), (540, 293), (566, 301), (590, 296), (606, 300),
                     (606, 341)]) & paper
    land &= ~sea & ~black
    sea_fill(sea)
    sea_fill(black)
    for xg in (96, 216, 336, 456, 576):
        cv.mix(paper & cv.box(xg, 50, xg + 1, 340) & ((yy.astype(int) % 4) == 0), '#a8987a', 0.6)
    for yg in (110, 190, 270):
        cv.mix(paper & cv.box(34, yg, 606, yg + 1) & ((xx.astype(int) % 4) == 0), '#a8987a', 0.6)
    rivers = [[(150, 336), (156, 300), (146, 262), (154, 226), (148, 190), (158, 160), (150, 132), (146, 112)],
              [(300, 336), (292, 300), (304, 268), (286, 232), (298, 198), (284, 160), (290, 136), (282, 126)],
              [(430, 98), (440, 140), (452, 180), (470, 220), (498, 256), (514, 292)],
              [(410, 196), (392, 164), (372, 132), (352, 104)]]
    for k, rv in enumerate(rivers):
        pts = []
        for (a, b) in zip(rv, rv[1:]):
            for u in np.linspace(0, 1, 7)[:-1]:
                px, py = K.lerp(a[0], b[0], u), K.lerp(a[1], b[1], u)
                pts.append((px + 3 * np.sin(py * 0.21 + k), py))
        pts.append(rv[-1])
        cv.fill(cv.stroke(pts, 1) & land, '#6f8890')
    for i in range(46):
        x = 240 + _h(i, 51) * 200
        y = 262 + _h(i, 52) * 30
        if not land[int(y), int(x)]:
            continue
        cv.fill(cv.stroke([(x - 2, y + 2), (x, y), (x + 2, y + 2)], 1), '#9a8262')
    for i in range(120):
        x, y = 360 + _h(i, 53) * 230, 90 + _h(i, 54) * 70
        if land[int(y), int(x)] and _h(i, 55) > 0.4:
            cv.fill(cv.box(x, y, x + 1, y + 1), '#9a9a74')
    ink = '#5e4632'
    cv.fill(cv.text('OSTSEE', 176, 80, 'l', 3), '#5f716c')
    cv.fill(cv.text('DEUTSCHES REICH', 62, 232, 'l', 2), ink)
    cv.fill(cv.text('SOWJETUNION', 396, 162, 'l', 2), ink)
    for (cx, cy, name, left) in ((116, 150, 'BERLIN', True), (524, 214, 'KARSK', False)):
        cv.fill(cv.box(cx - 2, cy - 2, cx + 3, cy + 3), '#2e211a')
        cv.fill(cv.box(cx - 1, cy - 1, cx + 2, cy + 2), '#d8caa4')
        cv.fill(cv.box(cx, cy, cx + 1, cy + 1), '#2e211a')
        tx = cx - 6 - K.text_width(name) if left else cx + 6        # labels clear of the corridors
        cv.fill(cv.text(name, tx, cy - 3, 's', 1), '#2e211a')
    pen = cv.poly([(64, 302), (176, 286), (177, 290), (65, 306)])
    cv.fill(pen, '#8a2b24')
    cv.fill(pen & (yy < 296 - (xx - 64) * 0.14), '#b0453a')
    tip = cv.poly([(176, 286), (190, 286), (177, 290)])
    cv.fill(tip, '#d6b088')
    cv.fill(cv.box(187, 286, 190, 288), '#3a3330')
    cv.glow(70, 30, 760, 560, '#f2deb2', 0.22, m=paper)
    cv.shade(paper, (1 - cv.falloff(120, 60, 760, 520, 1.0)) * 0.28)
    cv.shade(full & ~paper, (1 - cv.falloff(120, 60, 700, 520, 1.0)) * 0.4)
    for i in range(16):
        x, y = 60 + _h(i, 56) * 520, 130 + _h(i, 57) * 170
        if land[int(y), int(x)] and abs(x - 322) > 14:
            cv.fill(cv.box(x, y, x + 2, y + 2), '#5e4632')
    img = K.resolve(cv, 48, keep=('#8a2b24', '#2e211a', '#5e4632', '#5f716c', '#9a8262', '#6f8890', '#5c6c68',
                                  '#a8987a', '#9a9a74', '#d8caa4'))
    K.save(img, 'p2_map.png')
    lab = K.Canvas(112, 12, opaque=False)
    m = lab.text('FREIE STADT VELTRAVA', 1, 3, 's', 1)
    lab.fill(m, '#2e211a')
    K.save(K.resolve(lab, 4, dither=False), 'p2_veltrava.png')
    LAYOUT['map'] = {
        'line': [[334, 104], [342, 128], [326, 152], [334, 176], [322, 196], [314, 222], [326, 248], [312, 274],
                 [320, 300], [312, 330]],
        'veltrava': [322, 196], 'label_at': [330, 202],
        'corridors': [[[116, 150], [190, 140], [262, 136], [338, 134], [410, 128], [480, 122], [560, 116]],
                      [[116, 150], [190, 168], [262, 184], [322, 196], [390, 204], [456, 210], [524, 214]],
                      [[122, 156], [196, 210], [262, 238], [324, 250], [392, 252], [460, 246], [560, 262]]],
        'berlin': [116, 150], 'karsk': [524, 214]}
    return img


# ================================================================================================ p3 the papers
def shot_papers():
    W, H = 660, 360
    cv = K.Canvas(W, H)
    yy, xx = cv.yy, cv.xx
    full = cv.box(0, 0, W, H)
    cv.fill(full, '#2a1d16')
    cv.mix(full, '#45301f', K.noise(W, H, 9, 61, 3, sx=10.0) * 0.85)
    cv.glow(110, 30, 640, 430, '#b88250', 0.32)
    px0, py0, px1, py1 = 120, 52, 440, 344
    cv.mix(cv.box(px0 + 4, py0 + 5, px1 + 5, py1 + 6), '#0c0806', 0.7)
    paper = cv.box(px0, py0, px1, py1)
    cv.fill(paper, '#d8ccae')
    st = K.noise(W, H, 34, 62, 4)
    cv.mix(paper, '#c3b493', np.clip((st - 0.55) * 2.4, 0, 1) * 0.5)
    ink, rule = '#36323c', '#a29479'
    cv.fill(cv.text('FRACHTBRIEF', px0 + 14, py0 + 11, 'l', 2), ink)
    cv.fill(cv.text('НАКЛАДНАЯ', px0 + 14, py0 + 23, 's', 1), '#4c4652')
    cv.fill(cv.text('KORRIDOR II', px0 + 214, py0 + 11, 's', 1), '#4c4652')
    cv.fill(cv.text('KARSK - BERLIN', px0 + 214, py0 + 20, 's', 1), '#4c4652')
    cv.fill(cv.box(px0 + 12, py0 + 34, px1 - 12, py0 + 36), ink)
    cols = [px0 + 12, px0 + 94, px0 + 188, px0 + 238, px1 - 12]
    heads = ['WAGEN', 'LADUNG', 'GEWICHT', 'VERTRAG']
    for c, hd in zip(cols, heads):
        cv.fill(cv.text(hd, c + 4, py0 + 42, 's', 1), '#4c4652')
    rows = [('17-0417', 'GETREIDE', '21 T'), ('17-0418', 'KOHLE', '30 T'), ('17-0422', 'MEDIZIN', '4 T'),
            ('17-0431', 'GETREIDE', '21 T'), ('17-0433', 'HOLZ', '18 T'), ('17-0440', 'ZEMENT', '26 T'),
            ('17-0441', 'KOHLE', '30 T'), ('17-0446', 'MEDIZIN', '3 T'), ('17-0452', 'GETREIDE', '21 T'),
            ('17-0458', 'ERZ', '34 T'), ('17-0460', 'GETREIDE', '20 T'), ('17-0463', 'MASCHINEN', '12 T'),
            ('17-0470', 'KOHLE', '29 T'), ('17-0471', 'ZUCKER', '16 T')]
    y = py0 + 52
    for r, row in enumerate(rows):
        cv.fill(cv.box(px0 + 12, y + 13, px1 - 12, y + 14), rule)
        for c, val in zip(cols, row):
            m = cv.text(val, c + 4, y + 4, 's', 1)
            cv.fill(m, ink)
            cv.mix(m & (K.noise(W, H, 3, 63 + r, 1) > 0.66), '#d8ccae', 0.5)
        y += 17
    for c in cols:
        cv.fill(cv.box(c, py0 + 38, c + 1, y), rule)
    cv.mix(cv.stroke([(px0 + 30, py1 - 14), (px0 + 52, py1 - 22), (px0 + 70, py1 - 14), (px0 + 96, py1 - 20)], 1),
           '#2c3a66', 0.85)
    cv.glow(150, 40, 540, 420, '#f4e2bc', 0.25, m=paper)
    cv.shade(paper, (1 - cv.falloff(150, 40, 620, 470, 1.0)) * 0.3)
    # the card index (seen from above), a lead seal, the ink pad
    bx0, by0, bx1, by1 = 470, 62, 632, 250
    cv.mix(cv.box(bx0 + 4, by0 + 6, bx1 + 6, by1 + 8), '#0c0806', 0.7)
    cv.fill(cv.box(bx0, by0, bx1, by1), '#6a4630')
    cv.fill(cv.box(bx0 + 2, by0 + 2, bx1 - 2, by0 + 4), '#93684a')
    cv.fill(cv.box(bx0 + 6, by0 + 6, bx1 - 6, by1 - 6), '#22170f')
    for i in range(24):
        cy = by0 + 10 + i * 7
        cv.fill(cv.box(bx0 + 9, cy, bx1 - 9, cy + 2), '#e3d8c0')
        cv.fill(cv.box(bx0 + 9, cy + 2, bx1 - 9, cy + 3), '#a99c80')
    for (i, tx, letter) in ((2, bx0 + 18, 'A'), (9, bx0 + 66, 'C'), (16, bx0 + 112, 'K')):
        cy = by0 + 10 + i * 7
        cv.fill(cv.box(tx, cy - 6, tx + 18, cy), '#ece3cc')
        cv.fill(cv.text(letter, tx + 7, cy - 5, 's', 1), ink)
    cv.mix(cv.box(bx0, by0, bx1, by1), '#000000', np.clip((xx - bx0) / (bx1 - bx0), 0, 1) * 0.25)
    cv.fill(cv.stroke([(498, 294), (520, 306), (560, 304), (600, 318), (660, 322)], 1), '#7a776f')
    seal = cv.ell(490, 290, 8, 8)
    cv.fill(seal, '#7f838c')
    cv.fill(seal & (xx + yy < 490 + 290 - 3), '#b2b6be')
    cv.fill(cv.text('C', 488, 288, 's', 1) & seal, '#4e525a')
    cv.mix(cv.box(552, 262, 624, 296), '#0c0806', 0.6)
    cv.fill(cv.box(548, 258, 620, 292), '#5b616a')
    cv.fill(cv.box(552, 262, 616, 288), '#2f2240')
    cv.fill(cv.box(548, 258, 620, 259), '#8d939c')
    img = K.resolve(cv, 52, keep=('#36323c', '#4c4652', '#e3d8c0'))
    K.save(img, 'p3_papers.png')
    # the stamp (from above: knob over the block), its shadow, the imprint
    sc = K.Canvas(92, 52, opaque=False)                 # the block is as big as its imprint (84 x 40)
    blk = sc.box(2, 6, 90, 48)
    sc.fill(blk, '#4a3324')
    sc.fill(sc.box(2, 45, 90, 48), '#24160f')
    sc.fill(sc.box(2, 6, 90, 8), '#6e4d36')
    sc.fill(sc.box(2, 6, 4, 48), '#5d402d')
    knob = sc.ell(46, 24, 15, 13)
    sc.fill(sc.ell(48, 28, 16, 12), '#2b1b12')
    sc.fill(knob, '#7b4e2e')
    sc.fill(knob & sc.ell(42, 20, 9, 8), '#a5714a')
    sc.fill(sc.ell(39, 17, 2, 2), '#d8a97c')
    K.save(K.resolve(sc, 12, dither=False), 'p3_stamp.png')
    sh = np.zeros((56, 100, 4), np.uint8)
    m = K.ell(100, 56, 50, 28, 46, 24)
    sh[m] = (8, 5, 4, 255)
    K.save(sh, 'p3_shadow.png')
    ic = K.Canvas(84, 40, opaque=False)
    m = ic.box(2, 2, 82, 38) & ~ic.box(4, 4, 80, 36)
    tb = K.big(K.VK.vtext('C-17', 'l', 1), 2)
    oy, ox = 4, 42 - tb.shape[1] // 2
    m[oy:oy + tb.shape[0], ox:ox + tb.shape[1]] |= tb[:40 - oy, :84 - ox]
    m |= ic.text('ANLAGE C', 42, 29, 's', 1, center=True)
    rough = K.noise(84, 40, 2, 64, 1)
    m &= rough > 0.2
    ic.fill(m, '#5a3a76')
    ic.fill(m & (K.noise(84, 40, 4, 65, 2) > 0.62), '#43285c')
    K.save(K.resolve(ic, 4, dither=False), 'p3_imprint.png')
    LAYOUT['papers'] = {'pan': W - 640, 'imprint_at': [px0 + 238 - 10, py0 + 52 + 17 * 4 - 6],
                        'stamp_from': [600, -60]}
    return img


# ================================================================================================ p4 Berlin
def shot_berlin():
    W, H = 680, 360
    cv = K.Canvas(W, H)
    yy, xx = cv.yy, cv.xx
    WX0, WY0, WX1, WY1, FLOOR = 290, 64, 470, 296, 296
    o = K.Canvas(W, H)
    full = o.box(0, 0, W, H)
    o.vgrad(full, [(60, '#8e98ab'), (140, '#b2b8c5'), (206, '#d3d4d8'), (240, '#c6c9cf')])
    o.glow(330, 150, 260, 120, '#e3ddd2', 0.35)
    cx, base = 404, 214
    drum = o.box(cx - 82, base - 6, cx + 82, base + 14)
    o.fill(drum, '#8f97a8')
    for x in range(cx - 80, cx + 80, 6):
        o.fill(o.box(x, base - 4, x + 2, base + 12), '#7f8798')
    dome = o.ell(cx, base - 6, 84, 66) & (yy < base - 6)
    o.fill(dome, '#97a0b1')
    o.mix(dome, '#b4bac6', np.clip((cx - 10 - xx) / 80, 0, 1) * 0.8)
    o.mix(dome, '#7d8597', np.clip((xx - cx - 20) / 70, 0, 1) * 0.7)
    for k in range(-5, 6):
        a = k / 6.0 * np.pi / 2
        pts = [(cx + 84 * np.sin(a) * np.cos(ph), base - 6 - 66 * np.sin(ph)) for ph in np.linspace(0, np.pi / 2, 16)]
        o.mix(o.stroke(pts, 1) & dome, '#828a9b', 0.6)
    lan = o.box(cx - 6, base - 84, cx + 6, base - 70) | o.poly([(cx - 8, base - 84), (cx, base - 92), (cx + 8, base - 84)])
    o.fill(lan, '#8b93a4')
    o.mix(dome | drum | lan, '#c8ccd3', 0.32)
    chim = []
    rows = [(236, '#7c8495', '#c7ccd5', 0.0, 71), (262, '#5f6676', '#d4d8df', 0.0, 72), (294, '#454b59', '#dfe3ea', 0.0, 73)]
    for ri, (yb, col, snow, _, seed) in enumerate(rows):
        x = 270 + int(_h(ri, seed) * 10)
        while x < 500:
            w = 22 + int(_h(x, seed) * 30)
            hh = 12 + int(_h(x, seed + 1) * 12) + ri * 6
            blk = o.box(x, yb - hh, x + w, yb + 40)
            ridge = yb - hh - 6 - int(_h(x, seed + 2) * 6)
            rf = o.poly([(x - 2, yb - hh), (x + w * 0.5, ridge), (x + w + 2, yb - hh)])
            o.fill(blk, col)
            o.fill(rf, snow)
            o.fill(K.edge(rf, 1, 0) & (xx > x + w * 0.5), '#9ea5b3')
            for wx in range(x + 3, x + w - 3, 6):
                for wy in range(yb - hh + 4, yb + 30, 8):
                    if _h(wx * 7 + wy, seed) > 0.25:
                        o.fill(o.box(wx, wy, wx + 2, wy + 3), '#3b404c' if ri == 2 else '#596070')
            if _h(x, seed + 3) > 0.35:
                chx = x + int(w * (0.2 + 0.6 * _h(x, seed + 4)))
                o.fill(o.box(chx, ridge - 6, chx + 4, ridge + 8), col)
                o.fill(o.box(chx - 1, ridge - 7, chx + 5, ridge - 5), snow)
                chim.append([chx + 2, ridge - 8])
            x += w + 3 + int(_h(x, seed + 5) * 8)
    wall = cv.box(0, 0, W, FLOOR)
    cv.fill(wall, '#2a2e30')
    cv.mix(wall, '#33393a', K.noise(W, H, 22, 81, 3) * 0.6)
    cv.fill(cv.box(0, 228, W, 232) & ~cv.box(WX0 - 10, 0, WX1 + 10, H), '#232726')
    cv.glow((WX0 + WX1) / 2, 190, 300, 230, '#7b8290', 0.32, m=wall)
    cv.fill(cv.box(WX0 - 10, WY0 - 10, WX1 + 10, FLOOR), '#3c3a36')
    cv.fill(cv.box(WX0 - 10, WY0 - 10, WX1 + 10, WY0 - 8), '#59554e')
    glass = cv.box(WX0, WY0, WX1, WY1)
    cv.c[glass] = o.c[glass]
    bars = np.zeros((H, W), bool)
    for x in (WX0 + 58, WX0 + 118):
        bars |= cv.box(x, WY0, x + 4, WY1)
    for y in (126, 188, 250):
        bars |= cv.box(WX0, y, WX1, y + 4)
    cv.fill(bars & glass, '#2e2c29')
    cv.fill(K.edge(bars & glass, 0, -1) & glass, '#64605a')
    cv.fill(cv.box(WX0, WY0, WX1, WY0 + 3) | cv.box(WX0, WY0, WX0 + 3, WY1) | cv.box(WX1 - 3, WY0, WX1, WY1), '#2e2c29')
    fl = cv.box(0, FLOOR, W, H)
    cv.fill(fl, '#2b231f')
    for y in range(FLOOR + 3, H, 7):
        cv.fill(cv.box(0, y, W, y + 1), '#211a17')
    cv.pool((WX0 + WX1) / 2, FLOOR + 6, 120, 16, '#6f6e72', ks=(0.10, 0.10), m=fl)
    # pinned plans (left wall): a dome elevation on blueprint, a floor plan on paper
    for (x0, y0, x1, y1, blue) in ((44, 92, 136, 168, True), (146, 100, 226, 172, False), (60, 176, 120, 214, True)):
        sh = cv.box(x0, y0, x1, y1)
        cv.fill(sh, '#3a5482' if blue else '#cfc6b0')
        lc = '#a7b9d4' if blue else '#6d6758'
        if blue and y0 == 92:
            cv.fill(cv.box(x0 + 10, y1 - 16, x1 - 10, y1 - 15), lc)
            d = cv.ell((x0 + x1) / 2, y1 - 16, 30, 28) & ~cv.ell((x0 + x1) / 2, y1 - 16, 29, 27) & (yy < y1 - 16)
            cv.fill(d, lc)
            for xc in range(x0 + 16, x1 - 14, 6):
                cv.fill(cv.box(xc, y1 - 15, xc + 1, y1 - 6), lc)
        else:
            for k in range(4):
                cv.fill(cv.box(x0 + 6, y0 + 8 + k * 9, x1 - 6, y0 + 9 + k * 9), lc)
                cv.fill(cv.box(x0 + 8 + k * 14, y0 + 6, x0 + 9 + k * 14, y1 - 6), lc)
        cv.fill(cv.box(x0 + 2, y0 + 1, x0 + 4, y0 + 3) | cv.box(x1 - 4, y0 + 1, x1 - 2, y0 + 3), '#b8954a')
        cv.mix(sh, '#000000', 0.25)
    # the drafting table (left), the plan chest and lamp (right)
    board = cv.poly([(60, 214), (236, 196), (242, 240), (66, 258)])
    cv.fill(board, '#3b3733')
    bp = cv.poly([(76, 216), (226, 201), (230, 236), (80, 252)])
    cv.fill(bp, '#3a5684')
    for k in range(5):
        cv.fill(cv.stroke([(88 + k * 26, 214 - k * 2.6), (92 + k * 26, 248 - k * 2.6)], 1) & bp, '#94abcd')
    cv.fill(cv.stroke([(84, 232), (224, 218)], 1) & bp, '#94abcd')
    cv.fill(cv.stroke([(100, 224), (210, 212)], 2), '#b9ad8e')
    legs = cv.stroke([(84, 256), (78, 300)], 3) | cv.stroke([(226, 240), (232, 300)], 3) | cv.stroke([(80, 282), (230, 278)], 2)
    cv.fill(legs, '#1b1918')
    stool = cv.box(150, 262, 176, 266) | cv.stroke([(154, 266), (150, 300)], 2) | cv.stroke([(172, 266), (176, 300)], 2)
    cv.fill(stool, '#1b1918')
    chest = cv.box(520, 236, 668, 300)
    cv.fill(chest, '#2e2925')
    for y in range(244, 298, 11):
        cv.fill(cv.box(522, y, 666, y + 1), '#1d1a18')
        cv.fill(cv.box(586, y + 4, 600, y + 6), '#8d7444')
    for k in range(4):
        r = cv.box(530 + k * 24, 226, 552 + k * 24, 236)
        cv.fill(r, '#cfc6ae')
        cv.fill(cv.box(530 + k * 24, 233, 552 + k * 24, 236), '#9e967f')
    lamp = (612, 206)
    arm = cv.stroke([(640, 236), (628, 214), lamp], 2)
    cv.fill(arm, '#1b1918')
    shade = cv.poly([(lamp[0] - 10, lamp[1] + 4), (lamp[0] - 4, lamp[1] - 6), (lamp[0] + 6, lamp[1] - 4), (lamp[0] + 6, lamp[1] + 6)])
    cv.fill(shade, '#2f4136')
    cv.fill(cv.box(lamp[0] - 6, lamp[1] + 5, lamp[0] + 4, lamp[1] + 7), '#ffe2a2')
    cv.pool(lamp[0] - 4, 232, 96, 22, '#d9a868', ks=(0.14, 0.14, 0.14), m=chest | cv.box(500, 180, W, 236))
    img = K.resolve(cv, 60, keep=('#ffe2a2', '#3a5684', '#94abcd'))
    K.save(img, 'p4_berlin.png')
    fr = K.sheet_frames('konrad', 'idle_back')
    fr = [K.relight(f, '#4a5266', 0.62, rim='#d9dde6', rim_dir=(1, 0), rim_k=0.55) for f in fr]
    fr = [K.relight(f, '#ffffff', 0.0, rim='#c4cad6', rim_dir=(-1, 0), rim_k=0.4) for f in fr]
    K.save(K.strip(fr), 'p4_konrad.png')
    K.save(K.glow_sprite(120, 80, 60, 40, 56, 36, '#e09a50', levels=6, amax=0.45), 'p4_lampglow.png')
    LAYOUT['berlin'] = {'pan': W - 640, 'window': [WX0, WY0, WX1, WY1], 'konrad_feet': [392, 302],
                        'konrad_frames': len(fr), 'lampglow_at': [lamp[0] - 62, lamp[1] - 32], 'chimneys': chim}
    return img


# ================================================================================================ p5 Karsk
def shot_karsk():
    W, H, HZ = 680, 360, 206
    cv = K.Canvas(W, H)
    yy, xx = cv.yy, cv.xx
    sky = cv.box(0, 0, W, HZ + 1)
    cv.vgrad(sky, [(40, '#0b0f17'), (140, '#141a27'), (HZ, '#222a3a')])
    cv.glow(560, HZ, 280, 80, '#563d36', 0.65, m=sky)
    cv.glow(150, HZ, 220, 50, '#2f3546', 0.5, m=sky)
    n = K.noise(W, H, 20, 91, 4, sx=4.0)
    cv.mix(sky & (n > 0.6) & (yy < HZ - 20), '#1b2130', 0.6)
    gr = cv.box(0, HZ, W, H)
    cv.vgrad(gr, [(HZ, '#262d3e'), (250, '#2c3446'), (H, '#3a4459')])
    dn = K.noise(W, H, 70, 92, 3, sx=4.0)
    cv.mix(gr, '#4a5570', np.clip((dn - 0.5) * 1.6, 0, 1) * 0.45)
    ind = np.zeros((H, W), bool)
    for x0, w, hh in [(380, 70, 22), (446, 60, 30), (512, 40, 18), (640, 50, 26), (0, 46, 30), (40, 60, 22), (96, 40, 34)]:
        ind |= cv.box(x0, HZ - hh, x0 + w, HZ + 1)
        if x0 >= 380:
            for k in range(0, w, 10):
                ind |= cv.poly([(x0 + k, HZ - hh), (x0 + k + 10, HZ - hh - 6), (x0 + k + 10, HZ - hh)])
    for x, hh in [(470, 96), (488, 84), (530, 70), (420, 60)]:
        ind |= cv.box(x, HZ - hh, x + 5, HZ)
    ind |= cv.poly([(574, HZ), (580, HZ - 30), (576, HZ - 54), (612, HZ - 54), (608, HZ - 30), (614, HZ)])
    cv.fill(ind, '#121620')
    cv.fill(K.edge(ind, 0, -1) & (xx > 360), '#3c2e2e')
    for i in range(90):
        x, y = int(_h(i, 93) * W), int(HZ - 4 - _h(i, 94) * 30)
        if ind[y, x] and ind[y + 1, x + 1]:
            cv.fill(cv.box(x, y, x + 2, y + 1), '#d79c56' if _h(i, 95) > 0.3 else '#8c9cbc')
    smoke = np.zeros((H, W), bool)
    for (x, hh, k) in [(472, 96, 0), (490, 84, 1), (532, 70, 2)]:
        for j in range(14):
            cx, cy = x + 3 + j * 7 + 4 * np.sin(j + k), HZ - hh - 4 - j * 2.2
            smoke |= cv.ell(cx, cy, 5 + j * 0.8, 3 + j * 0.4)
    cv.mix(smoke & sky, '#2a2c36', 0.75)
    cv.mix(K.edge(smoke, 0, 1) & sky, '#5b4440', 0.6)
    VP = np.array([330.0, HZ + 1.0])
    for cxb in (-140, 120, 380, 660):
        for g in (-20, 20):
            p = (cxb + g, 372.0)
            rail = cv.stroke([tuple(VP), p], 1)
            cv.fill(rail & gr, '#6d7789')
            cv.fill(K.edge(rail, 0, 1) & gr & (yy > HZ + 30), '#20242f')
        for i in range(1, 30):
            s = 1.0 / (1.0 + 0.16 * i)
            a = VP + (np.array([cxb - 24, 372.0]) - VP) * s
            b = VP + (np.array([cxb + 24, 372.0]) - VP) * s
            if _h(i + cxb, 96) > 0.4:
                cv.fill(cv.stroke([tuple(a), tuple(b)], 1 if s < 0.5 else 2) & gr, '#1d212b')
    cv.pool(236, 300, 230, 56, '#c9c0ae', ks=(0.12, 0.12, 0.14), m=gr)
    mast = cv.box(176, 68, 180, 302) | cv.stroke([(170, 302), (178, 280), (186, 302)], 1)
    cv.fill(mast, '#161921')
    cv.fill(cv.box(164, 62, 194, 70), '#1d2029')
    for k in range(3):
        cv.fill(cv.box(167 + k * 9, 68, 173 + k * 9, 71), '#fff1cc')
    # the signal box (right)
    base = cv.box(508, 188, 632, 254)
    cv.fill(base, '#2d2321')
    for y in range(190, 254, 4):
        cv.fill(cv.box(508, y, 632, y + 1), '#241c1a')
    cab = cv.box(498, 142, 642, 190)
    cv.fill(cab, '#252830')
    win = cv.box(506, 150, 634, 178)
    cv.fill(win, '#e3a956')
    cv.mix(win, '#f6d08a', cv.falloff(570, 160, 70, 20, 1.0))
    for x in range(506, 634, 16):
        cv.fill(cv.box(x, 150, x + 2, 178), '#2b2a2c')
    cv.fill(cv.box(506, 162, 634, 164), '#2b2a2c')
    roof = cv.poly([(490, 142), (570, 124), (650, 142)])
    cv.fill(roof, '#c3cad7')
    cv.fill(cv.poly([(490, 142), (570, 128), (650, 142), (650, 145), (490, 145)]) & ~roof, '#1b1d24')
    stairs = cv.stroke([(504, 190), (462, 254)], 3)
    for k in range(9):
        stairs |= cv.box(504 - k * 4.7 - 6, 190 + k * 7.1, 504 - k * 4.7 + 2, 190 + k * 7.1 + 1)
    cv.fill(stairs, '#171a22')
    cv.pool(570, 262, 130, 28, '#c48a4e', ks=(0.14, 0.14, 0.14), m=gr)
    sig = (448, 150)
    cv.fill(cv.box(sig[0] - 1, sig[1], sig[0] + 2, 262), '#161921')
    cv.fill(cv.box(sig[0] - 5, sig[1] - 2, sig[0] + 6, sig[1] + 16), '#1d2029')
    # the waiting locomotive (front) far down the line
    lx, ly = 330, 198
    loco = cv.ell(lx, ly - 8, 8, 8) | cv.box(lx - 10, ly - 4, lx + 10, ly + 4) | cv.box(lx - 2, ly - 19, lx + 2, ly - 13)
    loco |= cv.box(lx - 12, ly - 14, lx - 8, ly + 2) | cv.box(lx + 8, ly - 14, lx + 12, ly + 2)
    cv.fill(loco, '#11141b')
    cv.fill(cv.box(lx - 12, ly + 2, lx + 12, ly + 4), '#3e1a18')
    cv.fill(cv.box(lx - 1, ly - 5, lx + 2, ly - 2), '#fff4d6')
    # a wagon on the left with the chalked number
    wg = cv.box(-4, 196, 150, 288)
    cv.fill(wg, '#2b201d')
    for x in range(0, 150, 9):
        cv.fill(cv.box(x, 198, x + 1, 286), '#231a18')
    cv.fill(cv.box(-4, 196, 150, 199), '#c4cbd7')
    cv.fill(cv.box(54, 204, 118, 284), '#30241f')
    cv.fill(cv.box(54, 204, 56, 284) | cv.box(116, 204, 118, 284), '#1c1513')
    cv.fill(cv.box(-4, 288, 150, 296), '#14110f')
    for wx in (20, 120):
        cv.fill(cv.ell(wx, 298, 11, 11) & ~cv.ell(wx, 298, 8, 8), '#121012')
    chalk = cv.text('C-17', 68, 224, 'l', 2)
    cv.fill(chalk, '#bfc4cc')
    cv.mix(chalk & (K.noise(W, H, 2, 97, 1) > 0.6), '#30241f', 0.6)
    cv.fill(cv.stroke([(66, 236), (110, 234)], 1), '#a9aeb7')
    cv.fill(cv.ell(122, 246, 3, 3), '#8d9198')
    cv.mix(wg, '#000000', np.clip((150 - xx) / 160, 0, 1) * 0.35)
    for i in range(80):
        x, y = int(_h(i, 98) * W), 330 + int(_h(i, 99) * 30)
        cv.fill(cv.box(x, y, x + 2 + int(_h(i, 100) * 6), y + 1), '#4a5670')
    img = K.resolve(cv, 60, keep=('#fff1cc', '#e3a956', '#fff4d6', '#bfc4cc'))
    K.save(img, 'p5_karsk.png')
    walk = K.sheet_frames('alexei', 'walk_side')
    idle = K.sheet_frames('alexei', 'idle_side')
    rl = dict(tint='#5d6a8c', k=0.55, rim='#e0aa66', rim_dir=(-1, 0), rim_k=0.55)
    K.save(K.strip([K.relight(f, **rl) for f in walk]), 'p5_alexei_walk.png')
    K.save(K.strip([K.relight(f, **rl) for f in idle]), 'p5_alexei_idle.png')
    cone = np.zeros((240, 220, 4), np.uint8)
    c = K.Canvas(220, 240)
    m = c.poly([(100, 0), (118, 0), (218, 236), (0, 236)])
    f = (1 - c.yy / 260.0) * 0.32 * (1 - np.abs(c.xx - 109 - (c.yy / 236) * 0) / 140).clip(0, 1)
    q = np.floor(f * 6 + K.pg.bayer(220, 240)) / 6
    cone[..., :3] = (np.array([220, 210, 180])[None, None, :] * q[..., None] * m[..., None]).astype(np.uint8)
    cone[..., 3] = 255
    K.save(cone, 'p5_cone.png')
    sg = np.concatenate([K.glow_sprite(24, 24, 12, 12, 11, 11, '#ff4a3a', levels=5, amax=0.9),
                         K.glow_sprite(24, 24, 12, 12, 11, 11, '#5cff9a', levels=5, amax=0.9)], axis=1)
    K.save(sg, 'p5_signal.png')
    K.save(K.glow_sprite(40, 30, 20, 15, 19, 14, '#ffe9b8', levels=5, amax=0.7), 'p5_headlamp.png')
    LAYOUT['karsk'] = {'pan': W - 640, 'cone_at': [178 - 109, 70], 'signal': [sig[0], sig[1] + 4],
                       'headlamp': [lx, ly - 4], 'chimney': [lx, ly - 20], 'walk': [684, 380, 304],
                       'walk_frames': len(walk), 'idle_frames': len(idle), 'flood': [178, 70]}
    return img


def main():
    shots = [shot_line(), shot_map(), shot_papers(), shot_berlin(), shot_karsk()]
    K.write_layout(LAYOUT)
    if '--preview' in sys.argv:
        out = sys.argv[sys.argv.index('--preview') + 1]
        os.makedirs(out, exist_ok=True)
        sheet = Image.new('RGB', (1280, 1080), (0, 0, 0))
        for i, s in enumerate(shots):
            sheet.paste(Image.fromarray(s[:, :640, :3]), ((i % 2) * 640, (i // 2) * 360))
        sheet.save(os.path.join(out, 'prologue_sheet.png'))
    print('prologue art written to', K.OUT)


if __name__ == '__main__':
    main()
