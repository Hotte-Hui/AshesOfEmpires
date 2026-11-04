"""env_berlin_stills -- 640x360 cinematic stills for the A1->M1 match cut and the X1 montage.

x1_stamp_closeup.png      macro: red C-17 stamp (double impression) on the Karsk freight ledger
x1_blueprint_closeup.png  macro: pencil C-17 on a Berlin diazo plan -- SAME glyph skeleton, position
                          and size as the stamp (C17_SKELETON) so the match cut lands exactly
x1_border_map.png         neutral sepia schematic of a fictional border corridor, C-17 route in red
x1_alexei_desk.png        Karsk: Alexei files the document under a copper lamp (silhouette, hands)
x1_konrad_desk.png        Berlin: Konrad folds the matching memorandum (same framing, parallel)
"""
from __future__ import annotations

import math
import os

import numpy as np

import env_berlin_kit as kit
import pg

VW, VH = 640, 360
C17_BOX = (226, 124, 188, 88)        # x, y, w, h shared by both close-ups (match cut)


def c17_skeleton():
    """Polylines of the C-17 mark in screen px (identical for stamp and pencil)."""
    cx, cy, rx, ry = 258, 168, 24, 37
    arc = [(cx + rx * math.cos(math.radians(t)), cy - ry * math.sin(math.radians(t)))
           for t in np.linspace(42, 318, 40)]
    return [arc, [(292, 171), (316, 171)], [(331, 146), (348, 131), (348, 206)],
            [(366, 133), (406, 133), (381, 206)]]


SEP = kit.S['tone']
SRED = kit.S['red']


def sepia_ramps():
    return kit.Ramps({'S': SEP, 'X': [SRED[0], SRED[1], SRED[2], SRED[3]], 'N': SEP[:4]})


def vignette(lay, amount=1.6, cx=None, cy=None, power=1.8):
    h, w = lay.h, lay.w
    cx = w / 2 if cx is None else cx
    cy = h / 2 if cy is None else cy
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    d = np.sqrt(((xx - cx) / (w * 0.62)) ** 2 + ((yy - cy) / (h * 0.62)) ** 2)
    lay.amb_field(-amount * np.clip(d, 0, 1.4) ** power)


def stroke(lay, polys, r, ramp, tone, seed=0, jitter=0.0, keep=1.0, tone_fn=None, **kw):
    m = kit.stroke_mask(lay.w, lay.h, polys, r, jitter=jitter, seed=seed)
    if keep < 1.0:
        rng = np.random.default_rng(seed + 99)
        m &= rng.random(m.shape) < keep
    if tone_fn is not None:
        lay.put(m, 0, 0, ramp, tone_fn(m), **kw)
    else:
        lay.put(m, 0, 0, ramp, tone, **kw)
    return m


# =========================================================================== 1  stamp close-up
def stamp_closeup():
    R = sepia_ramps()
    lay = kit.MLayer(VW, VH, R, 'x1_stamp_closeup')
    yy, xx = np.mgrid[0:VH, 0:VW].astype(np.float32)
    # ledger paper: warm lamp from upper left, darker toward the binding gutter on the left
    t = 9.4 + 1.1 * np.clip(1 - np.hypot(xx - 140, yy - 30) / 620, 0, 1)
    t -= 3.4 * np.clip((64 - xx) / 64, 0, 1) ** 1.6
    t += (pg.value_noise(VW, VH, 30, 7, octaves=3) - 0.5) * 0.5
    lay.put(np.ones((VH, VW), bool), 0, 0, 'S', t)
    rng = np.random.default_rng(3)
    for _ in range(900):                                              # paper tooth / fibres
        x, y = int(rng.integers(0, VW)), int(rng.integers(0, VH))
        ln = int(rng.integers(1, 4))
        lay.shade_rect(x, y, ln, 1, -0.55)
    # ruled lines (focus falls off toward top and bottom: softer, wider lines)
    focus = 168

    def soft(y):
        return min(1.0, abs(y - focus) / 150)
    for y in range(22, VH, 34):
        b = soft(y)
        lay.shade_rect(0, y, VW, 1, -2.4 + b * 1.4)
        if b > 0.5:
            lay.shade_rect(0, y + 1, VW, 1, -0.8)
    for x in (98, 101, 476, 566):
        for y in range(0, VH):
            lay.shade_rect(x, y, 1, 1, -2.0 + soft(y) * 1.2)
    # handwritten entries (pseudo cursive), out-of-focus rows rendered broad and pale
    for row, y in enumerate(range(22 + 34 - 9, VH, 34)):
        b = soft(y) ** 1.5
        r = 0.7 + b * 2.0
        tone = 2.2 + b * 5.0
        nums = kit.hand_polys(str(10 + row * 3 % 17) + '.' + str(1 + row % 9), 22, y - 12, 12, 7, 2.5, seed=row)
        stroke(lay, nums, r, 'S', tone, seed=row)
        if 140 < y < 200:
            continue                                                  # the stamp row
        words = kit.scribble_polys(110, y, 330 - (row * 37) % 120, 6.5, seed=40 + row)
        stroke(lay, words, r, 'S', tone, seed=40 + row)
        stroke(lay, kit.hand_polys(str(3 + row % 6), 500, y - 12, 12, 7, 2.5, seed=70 + row), r, 'S', tone)
        stroke(lay, kit.hand_polys(str(12 + row), 584, y - 12, 12, 7, 2.5, seed=80 + row), r, 'S', tone)
    # the redacted recipient in the C-17 line (black marker, ragged ends)
    for k in range(3):
        y0 = 214 + k * 5
        pts = [(112 + rng.uniform(-3, 3), y0 + rng.uniform(-1, 1)), (300, y0 + rng.uniform(-1, 1)),
               (452 + rng.uniform(-6, 2), y0 + rng.uniform(-1, 1))]
        stroke(lay, [kit.smooth_poly(pts, 6)], 3.2, 'S', 0.4, seed=k + 200)
    # ---- the stamp: double frame + C-17, red ink with uneven coverage and a second (offset) strike
    sk = c17_skeleton()
    frame_polys = [[(200, 108), (440, 108), (440, 230), (200, 230), (200, 108)],
                   [(209, 116), (431, 116), (431, 222), (209, 222), (209, 116)]]
    main = kit.stroke_mask(VW, VH, sk, 6.4, jitter=0.25, seed=5)
    fr = kit.stroke_mask(VW, VH, [frame_polys[0]], 2.6, jitter=0.2, seed=6) | \
        kit.stroke_mask(VW, VH, [frame_polys[1]], 1.2, jitter=0.15, seed=7)
    # micro text slab inside the frame top
    for x in range(222, 420, 9):
        fr[121:124, x:x + 6] = True
    stamp = main | fr
    ghost = np.roll(np.roll(stamp, 5, axis=1), 4, axis=0) & ~stamp
    nz = pg.value_noise(VW, VH, 5, 11, octaves=3)
    wn = pg.white_noise(VW, VH, 12)
    edge = stamp & ~kit.erode(stamp, 1)
    tone = np.full((VH, VW), 2.0, np.float32)
    tone[edge] = 1.0
    tone[(nz > 0.62) & stamp] = 2.6                                     # thin ink
    gaps = stamp & ((wn < 0.07) | ((nz < 0.3) & (wn < 0.35)))
    m = stamp & ~gaps
    lay.put(m, 0, 0, 'X', tone, flat=True)
    gk = ghost & (pg.bayer(VW, VH, 0, 0) < 0.6) & (wn > 0.15)
    lay.put(gk, 0, 0, 'X', 1.0, flat=True)
    # lighting: lamp gradient + vignette (macro depth)
    vignette(lay, 2.2, cx=300, cy=170)
    lay.resolve(band=2.4)
    return lay


# =========================================================================== 2  blueprint close-up
def blueprint_closeup():
    R = kit.archive_ramps()
    lay = kit.MLayer(VW, VH, R, 'x1_blueprint_closeup')
    yy, xx = np.mgrid[0:VH, 0:VW].astype(np.float32)
    t = 5.5 + 0.7 * np.clip(1 - np.hypot(xx - 80, yy - 120) / 600, 0, 1)
    t += (pg.value_noise(VW, VH, 60, 21, octaves=2) - 0.5) * 0.35
    lay.put(np.ones((VH, VW), bool), 0, 0, 'P', t)
    rng = np.random.default_rng(8)
    for _ in range(1100):                                             # paper tooth
        x, y = int(rng.integers(0, VW)), int(rng.integers(0, VH))
        lay.shade_rect(x, y, int(rng.integers(1, 3)), 1, -0.6)
    # printed construction grid (light blue dots)
    for gx in (150, 262, 374, 486, 598):
        for y in range(0, VH, 5):
            lay.rect(gx, y, 2, 2, 'B', 5.4, flat=True)
    for gy in (20, 244):
        for x in range(0, VW, 5):
            lay.rect(x, gy, 2, 2, 'B', 5.4, flat=True)

    def diazo(m, tone=3.0):
        """Diazo lines: dense core, slightly bled lighter edge."""
        lay.put(kit.dilate(m, 1) & ~m, 0, 0, 'B', tone + 1.6, flat=True)
        lay.put(m, 0, 0, 'B', tone, flat=True)
    # east wall of the building (thick, with the corridor gap) at the left
    wall = np.zeros((VH, VW), bool)
    wall[0:46, 36:60] = True
    wall[122:VH, 36:60] = True
    diazo(wall, 2.6)
    # the second wall: dashed, half way into the frame
    sw = np.zeros((VH, VW), bool)
    for y in range(40, 128):
        if (y // 6) % 2 == 0:
            sw[y, 104:114] = True
    diazo(sw, 3.4)
    # corridor continuing (dashed outlines) + walking line
    cor = np.zeros((VH, VW), bool)
    for x in range(60, VW):
        if (x // 16) % 2 == 0:
            cor[44:49, x] = True
            cor[118:123, x] = True
    diazo(cor, 3.0)
    for x in range(130, VW, 22):
        lay.rect(x, 82, 6, 4, 'B', 4.2, flat=True)
    # ---- pencil C-17 on the same skeleton/position as the stamp
    sk = c17_skeleton()
    core = kit.stroke_mask(VW, VH, sk, 2.4, jitter=0.35, seed=31)
    second = kit.stroke_mask(VW, VH, [[(x + 1.2, y - 0.8) for (x, y) in p] for p in sk], 1.4, jitter=0.5, seed=32)
    gr = pg.white_noise(VW, VH, 33)
    pm = (core | second) & (gr > 0.16)                                # paper tooth breaks the graphite
    tone = np.where(gr > 0.7, 4.0, np.where(gr > 0.4, 2.6, 2.0)).astype(np.float32)
    lay.put(pm, 0, 0, 'K', tone, flat=True)
    # underline + arrow toward the corridor + a circle round the second wall
    stroke(lay, [kit.smooth_poly([(226, 226), (330, 223), (420, 226)], 6)], 1.6, 'K', 2.6, seed=34, keep=0.85)
    arr = kit.smooth_poly([(244, 118), (210, 104), (170, 96), (138, 92)], 8)
    stroke(lay, [arr], 1.4, 'K', 2.4, seed=35, keep=0.88)
    stroke(lay, [[(138, 92), (150, 84)], [(138, 92), (150, 101)]], 1.4, 'K', 2.4, seed=36, keep=0.9)
    ring = [(109 + math.cos(a) * 40, 84 + math.sin(a) * 52) for a in np.linspace(0.6, 2 * math.pi + 0.9, 60)]
    stroke(lay, [ring], 1.2, 'K', 3.0, seed=37, keep=0.8)
    # eraser crumbs
    for _ in range(14):
        x, y = rng.uniform(420, 520), rng.uniform(150, 240)
        lay.ellipse(x, y, rng.uniform(1.2, 2.6), rng.uniform(1.0, 2.0), 'P', 3.6, hgt=0.5)
    # the pencil lying across the lower right (hexagonal, dark green lacquer)
    p0, p1 = np.array([446.0, 318.0]), np.array([700.0, 262.0])
    d = (p1 - p0) / np.linalg.norm(p1 - p0)
    nrm = np.array([-d[1], d[0]])
    # cast shadow on the paper
    sh = [tuple(p0 + nrm * 9 + d * 30), tuple(p1 + nrm * 9), tuple(p1 + nrm * 16), tuple(p0 + nrm * 14 + d * 34)]
    lay.poly(sh, 'P', 3.4)
    body = [tuple(p0 + d * 34 - nrm * 7), tuple(p1 - nrm * 7), tuple(p1 + nrm * 7), tuple(p0 + d * 34 + nrm * 7)]
    lay.poly(body, 'G', 2.6)
    for off, tn in ((-6, 4.6), (-5, 4.6), (-1, 3.4), (0, 3.6), (5, 1.6), (6, 1.4)):
        a_, b_ = p0 + d * 34 + nrm * off, p1 + nrm * off
        lay.line(a_[0], a_[1], b_[0], b_[1], 'G', tn)
    # gilt lettering band and the sharpened wood cone + graphite tip
    for k in range(6):
        c = p0 + d * (120 + k * 9)
        lay.rect(int(c[0]), int(c[1] - 2), 4, 2, 'A', 4.4, flat=True)
    cone = [tuple(p0 + d * 34 - nrm * 7), tuple(p0 + d * 34 + nrm * 7), tuple(p0 + d * 8 + nrm * 2),
            tuple(p0 + d * 8 - nrm * 2)]
    lay.poly(cone, 'D', 6.0)
    lay.line(*(p0 + d * 34 - nrm * 6), *(p0 + d * 10 - nrm * 2), 'D', 7.6)
    tip = [tuple(p0 + d * 8 + nrm * 2), tuple(p0 + d * 8 - nrm * 2), tuple(p0)]
    lay.poly(tip, 'K', 1.6)
    lay.px(int(p0[0]) + 1, int(p0[1]) - 1, 'K', 4.0)
    # light: cool daylight from the left, warm desk lamp from the upper right
    F = {'warm': np.clip(1 - np.hypot(xx - 640, yy + 40) / 520, 0, 1) ** 1.6 * 0.5,
         'cold': np.clip(1 - np.hypot(xx - 0, yy - 160) / 380, 0, 1) ** 1.6 * 0.35}
    vignette(lay, 1.8, cx=320, cy=170)
    lay.resolve(F, band=2.4)
    return lay


# =========================================================================== 3  border map
def border_map():
    R = sepia_ramps()
    lay = kit.MLayer(VW, VH, R, 'x1_border_map')
    yy, xx = np.mgrid[0:VH, 0:VW].astype(np.float32)
    t = 9.6 + (pg.value_noise(VW, VH, 60, 51, octaves=3) - 0.5) * 0.8
    lay.put(np.ones((VH, VW), bool), 0, 0, 'S', t)
    rng = np.random.default_rng(52)
    # fold lines of a much-handled map
    lay.shade_rect(320, 0, 1, VH, -1.4); lay.shade_rect(321, 0, 1, VH, 0.7)
    lay.shade_rect(0, 180, VW, 1, -1.4); lay.shade_rect(0, 181, VW, 1, 0.7)

    def ink(m, tone):
        lay.put(m, 0, 0, 'S', tone, flat=True)

    def line(pts, r=0.6, tone=3.0, dash=None, seed=0):
        pts = kit.smooth_poly(pts, 8)
        m = kit.stroke_mask(VW, VH, [pts], r, seed=seed)
        if dash:
            on, off = dash
            # dash along x+y parameter
            par = (xx + yy).astype(np.int32)
            m &= (par % (on + off)) < on
        ink(m, tone)
        return m
    # frame + graticule ticks with numbers
    for (ins, tn) in ((10, 2.0), (15, 4.0)):
        line([(ins, ins), (VW - ins, ins), (VW - ins, VH - ins), (ins, VH - ins), (ins, ins)], 0.5, tn)
    for k, x in enumerate(range(40, VW - 20, 60)):
        lay.rect(x, 10, 1, 6, 'S', 2.0, flat=True); lay.rect(x, VH - 16, 1, 6, 'S', 2.0, flat=True)
        m = kit.text_mask(str(k + 1), '35')
        lay.put(m, x + 3, 3, 'S', 3.0, flat=True)
    for k, y in enumerate(range(40, VH - 20, 60)):
        lay.rect(10, y, 6, 1, 'S', 2.0, flat=True); lay.rect(VW - 16, y, 6, 1, 'S', 2.0, flat=True)
        m = kit.text_mask('ABCDEF'[k], '35')
        lay.put(m, 3, y + 3, 'S', 3.0, flat=True)
    # hills: hachure clusters
    for (hx, hy, hr) in ((120, 90, 34), (210, 290, 28), (470, 70, 40), (560, 300, 30), (380, 250, 22)):
        for a in np.linspace(0, 2 * math.pi, int(hr * 1.6), endpoint=False):
            r0 = hr * rng.uniform(0.55, 0.75)
            x0, y0 = hx + math.cos(a) * r0, hy + math.sin(a) * r0 * 0.7
            x1, y1 = hx + math.cos(a) * hr, hy + math.sin(a) * hr * 0.7
            for (px_, py_) in kit.bres(x0, y0, x1, y1):
                lay.px(px_, py_, 'S', 5.0, flat=True)
    # forests: little tree circles
    for (fx, fy, n) in ((260, 110, 22), (90, 250, 18), (520, 180, 20), (420, 320, 12)):
        for _ in range(n):
            x, y = fx + rng.normal(0, 18), fy + rng.normal(0, 12)
            m, mx, my = lay.ellipse_mask(x, y, 2.2, 2.2)
            e = kit.edge_of(m)
            lay.put(e, mx, my, 'S', 5.4, flat=True)
    # river with a lake
    river = [(20, 40), (90, 60), (150, 130), (240, 160), (300, 220), (350, 300), (420, 345)]
    line(river, 1.4, 5.6)
    line([(x, y + 3) for (x, y) in river], 0.5, 4.6)
    lake = [(500 + math.cos(a) * 34 * (1 + 0.15 * math.sin(3 * a)), 110 + math.sin(a) * 18) for a in
            np.linspace(0, 2 * math.pi, 50)]
    line(lake, 0.6, 4.4)
    for y in range(96, 126, 3):
        for x in range(472, 530, 1):
            if (x - 500) ** 2 / 30 ** 2 + (y - 110) ** 2 / 15 ** 2 < 1 and (x + y) % 2 == 0:
                lay.px(x, y, 'S', 7.0, flat=True)
    # the fictional border: dash-dot line, slightly wandering, no names, no claims
    bpts = [(300, 15), (308, 70), (296, 130), (318, 200), (306, 270), (322, 345)]
    bm = kit.stroke_mask(VW, VH, [kit.smooth_poly(bpts, 8)], 1.3, seed=60)
    par = yy.astype(np.int32)
    bm &= ((par % 14) < 7) | ((par % 14) == 10)
    ink(bm, 1.4)
    # the corridor zone: hatched band along the route
    route = [(40, 214), (120, 206), (200, 196), (300, 186), (380, 170), (460, 150), (560, 138), (600, 132)]
    sm = kit.smooth_poly(route, 10)
    band = kit.stroke_mask(VW, VH, [sm], 20)
    hatch = band & (((xx - yy).astype(np.int32) % 6) == 0)
    ink(hatch, 6.4)
    edge = band & ~kit.erode(band, 1)
    edge &= ((xx.astype(np.int32) // 4) % 2) == 0
    ink(edge, 3.6)
    # railway: classic black/white chequered line under the route
    rail = kit.stroke_mask(VW, VH, [[(x, y + 10) for (x, y) in sm]], 2.0)
    rail_core = kit.erode(rail, 1)
    ink(rail & ~rail_core, 1.8)
    seg = ((xx.astype(np.int32) // 9) % 2) == 0
    ink(rail_core & seg, 1.8)
    # a branch line leaving north
    br = kit.stroke_mask(VW, VH, [kit.smooth_poly([(200, 206), (230, 150), (260, 80), (280, 20)], 8)], 1.4)
    ink(br & ~kit.erode(br, 1), 2.2)
    ink(kit.erode(br, 1) & (((yy.astype(np.int32)) // 8) % 2 == 0), 2.2)
    # ---- the C-17 route in red with station rings and an arrow
    rr = kit.stroke_mask(VW, VH, [sm], 2.4, seed=70)
    lay.put(rr, 0, 0, 'X', 2.0, flat=True)
    for k in (0, 28, 58, 90, 112):
        if k < len(sm):
            x, y = sm[min(k * len(sm) // 120, len(sm) - 1)]
            m, mx, my = lay.ellipse_mask(x, y, 6.0, 6.0)
            lay.put(m, mx, my, 'S', 10.0, flat=True)
            lay.put(m & ~kit.erode(m, 2), mx, my, 'X', 1.4, flat=True)
    ex, ey = sm[-1]
    lay.poly([(ex + 14, ey - 3), (ex - 2, ey - 11), (ex + 1, ey + 6)], 'X', 2.0)
    # endpoints: square (west), ring (east) -- no place names on this schematic
    lay.rect(26, 206, 12, 12, 'X', 1.4, flat=True); lay.rect(29, 209, 6, 6, 'S', 10.0, flat=True)
    m, mx, my = lay.ellipse_mask(608, 131, 7.0, 7.0)
    lay.put(m, mx, my, 'X', 1.4, flat=True)
    lay.put(kit.erode(m, 2), mx, my, 'S', 10.0, flat=True)
    # label C-17 in a red box at the crossing of the border
    lm = kit.text_mask('C-17', '57')
    bx, by = 330, 158
    lay.rect(bx - 4, by - 4, lm.shape[1] + 8, 15, 'S', 10.5, flat=True)
    box = np.zeros((15, lm.shape[1] + 8), bool)
    box[0, :] = box[-1, :] = True; box[:, 0] = box[:, -1] = True
    lay.put(box, bx - 4, by - 4, 'X', 1.6, flat=True)
    lay.put(lm, bx, by, 'X', 1.0, flat=True)
    # north arrow
    lay.poly([(600, 40), (606, 66), (600, 60), (594, 66)], 'S', 2.0)
    lay.put(kit.text_mask('N', '35'), 599, 70, 'S', 2.0, flat=True)
    # cartouche + legend (bottom left)
    cx0, cy0, cw, ch = 24, 262, 150, 82
    lay.rect(cx0, cy0, cw, ch, 'S', 10.6, flat=True)
    lay.put(kit.edge_of(np.ones((ch, cw), bool)), cx0, cy0, 'S', 2.0, flat=True)
    lay.put(kit.text_mask('SCHEMA', '57'), cx0 + 6, cy0 + 5, 'S', 1.6, flat=True)
    lay.put(kit.text_mask('NICHT MASSSTÄBLICH', '35'), cx0 + 6, cy0 + 15, 'S', 3.0, flat=True)
    legend = [('BAHN', 'rail'), ('GRENZE', 'border'), ('KORRIDOR', 'corr'), ('ROUTE C-17', 'route')]
    for i, (txt, kind) in enumerate(legend):
        ly = cy0 + 28 + i * 12
        x0 = cx0 + 8
        if kind == 'rail':
            lay.rect(x0, ly + 1, 22, 3, 'S', 1.8, flat=True)
            for k in range(0, 22, 6):
                lay.rect(x0 + k, ly + 2, 3, 1, 'S', 10.0, flat=True)
        elif kind == 'border':
            for k in range(0, 22, 5):
                lay.rect(x0 + k, ly + 2, 3 if k % 10 == 0 else 1, 1, 'S', 1.4, flat=True)
        elif kind == 'corr':
            for k in range(0, 22, 3):
                lay.px(x0 + k, ly + 1, 'S', 4.0); lay.px(x0 + k + 1, ly + 3, 'S', 6.0)
        else:
            lay.rect(x0, ly + 1, 22, 3, 'X', 2.0, flat=True)
        lay.put(kit.text_mask(txt, '35'), x0 + 28, ly, 'S', 2.4, flat=True)
    vignette(lay, 1.4)
    lay.resolve(band=2.6)
    return lay


# =========================================================================== 4/5  desk tableaux
def karsk_ramps():
    k = kit.K
    return kit.Ramps({
        'W': k['night'] + k['teal'],                                                    # cold room 0..8
        'D': [k['night'][0]] + k['wood'] + [k['copper'][1], k['copper'][2], k['copper'][3], k['copper'][4]],
        'P': [k['stone'][2], k['stone'][3], k['stone'][4], k['stone'][5], k['sky'][4], k['sky'][5],
              k['snow'][3], k['snow'][4]],
        'A': [k['rust'][3], k['copper'][0], k['rust'][4], k['copper'][1], k['copper'][2], k['copper'][3],
              k['copper'][4]],
        'S': [k['rust'][1], k['rust'][2], k['rust'][3], k['copper'][1], k['copper'][2], k['copper'][3]],
        'G': [k['night'][1], k['teal'][0], k['teal'][1], k['teal'][2], k['sage'][0], k['sage'][1], k['sage'][2]],
        'K': k['sky'],
        'X': [SRED[0], SRED[1], SRED[2], SRED[3]],
        'I': [k['night'][0], k['night'][1], k['stone'][0], k['stone'][1]],
        'N': k['night'],
    })


def archive_ramps_tab():
    a = kit.A
    base = kit.archive_ramps()
    d = {n: base.hex[n] for n in base.names}
    d['S'] = [a['wood'][2], a['wood'][3], a['wood'][4], a['amber'][2], a['amber'][3], a['amber'][4]]
    d['X'] = [a['ink'][2], a['ink'][3]]
    return kit.Ramps(d)


def _xf(pts, x, y, ang, s):
    c, sn = math.cos(ang), math.sin(ang)
    return [(x + (px * c - py * sn) * s, y + (px * sn + py * c) * s) for (px, py) in pts]


def hand(lay, x, y, ang, s=1.0, pose='flat', tone=2.4, seed=0):
    """Lamp-lit hand seen from above, fingers together (no cartoon splay).
    Local frame: wrist at the origin, fingers toward +x, thumb on the -y side."""
    if pose == 'flat':
        fingers = [(-7.5, 19), (-2.5, 22), (2.5, 21), (7.2, 16)]        # (y offset, length)
    else:                                                               # curled over an edge / pinching
        fingers = [(-7.5, 11), (-2.5, 13), (2.5, 12), (7.2, 9)]
    # back of the hand
    back = [(0, -8.5), (21, -10.5), (22, 10.5), (0, 8.5)]
    lay.poly(_xf(back, x, y, ang, s), 'S', tone, hgt=0.6)
    # fingers as one mass with separating creases
    outline = [(20, -10.5)]
    for (oy, ln) in fingers:
        outline += [(20 + ln - 2, oy - 2.4), (20 + ln, oy), (20 + ln - 2, oy + 2.4)]
    outline += [(20, 10.5)]
    lay.poly(_xf(outline, x, y, ang, s), 'S', tone, hgt=0.7)
    for (oy, ln) in fingers[:-1]:
        p = _xf([(21, oy + 2.5), (20 + ln - 3, oy + 2.5)], x, y, ang, s)
        lay.line(p[0][0], p[0][1], p[1][0], p[1][1], 'S', tone - 1.2)
    # knuckle row + nails catching the light
    for (oy, ln) in fingers:
        k = _xf([(21, oy)], x, y, ang, s)[0]
        lay.px(k[0], k[1], 'S', tone + 1.0)
        nl = _xf([(20 + ln - 2.5, oy)], x, y, ang, s)[0]
        lay.px(nl[0], nl[1], 'S', tone + 1.4)
    # thumb, tucked along the -y side
    th = [(4, -8), (14, -15), (24, -15.5), (25, -12.5), (15, -10), (7, -4)]
    lay.poly(_xf(th, x, y, ang, s), 'S', tone - 0.3, hgt=0.65)
    tl = _xf([(23, -14)], x, y, ang, s)[0]
    lay.px(tl[0], tl[1], 'S', tone + 1.2)
    # wrist tendon shadow
    w0 = _xf([(1, -3), (12, -4)], x, y, ang, s)
    lay.line(w0[0][0], w0[0][1], w0[1][0], w0[1][1], 'S', tone - 0.8)
    c = _xf([(18, 0)], x, y, ang, s)[0]
    lay.dome_height(c[0], c[1], 20 * s, 16 * s, base=0.3, amp=0.6)


def ushanka(lay, x, y):
    """Fur cap lying on the desk, ear flaps tied up (Alexei)."""
    lay.ellipse(x, y + 10, 46, 11, 'N', 1.0, hgt=0.2)                               # contact shadow
    lay.ellipse(x, y, 40, 16, 'G', 1.6, hgt=0.7)                                    # fur crown
    lay.ellipse(x - 2, y - 4, 30, 9, 'G', 2.4, hgt=0.8)
    lay.ellipse(x - 26, y + 3, 14, 10, 'G', 1.2, hgt=0.6)                           # flap
    lay.ellipse(x + 28, y + 2, 13, 10, 'G', 1.2, hgt=0.6)
    lay.rect(int(x - 10), int(y - 12), 20, 3, 'G', 0.8, flat=True)                  # tie
    rng = np.random.default_rng(4)
    for _ in range(140):                                                           # fur tufts
        px_, py_ = x + rng.uniform(-38, 38), y + rng.uniform(-14, 12)
        if ((px_ - x) / 40) ** 2 + ((py_ - y) / 15) ** 2 < 1:
            lay.px(px_, py_, 'G', float(rng.choice([0.8, 2.8, 3.4])))


def fedora(lay, x, y):
    """Felt hat lying crown-up on the desk (Konrad)."""
    lay.ellipse(x, y + 12, 50, 10, 'N', 1.0, hgt=0.2)                               # contact shadow
    lay.ellipse(x, y + 4, 46, 11, 'I', 1.4, hgt=0.6)                                # brim
    lay.ellipse(x, y + 2, 44, 9, 'I', 2.0, hgt=0.65)
    lay.ellipse(x, y - 4, 27, 13, 'I', 1.2, hgt=0.8)                                # crown
    lay.ellipse(x - 3, y - 8, 20, 7, 'I', 2.0, hgt=0.9)
    lay.line(x - 6, y - 15, x - 2, y - 2, 'I', 0.8)                                 # pinch crease
    lay.rect(int(x - 27), int(y + 1), 54, 3, 'D', 1.4, flat=True)                  # ribbon band
    lay.rect(int(x - 27), int(y + 1), 54, 1, 'D', 2.6, flat=True)


def sleeve(lay, pts, width, ramp, tone, cuff=None, seed=0):
    m = kit.stroke_mask(lay.w, lay.h, [kit.smooth_poly(pts, 6)], width, seed=seed)
    lay.put(m, 0, 0, ramp, tone, hgt=0.5)
    # folds
    rng = np.random.default_rng(seed)
    for k in range(4):
        a = pts[0]
        b = pts[-1]
        t0 = rng.uniform(0.2, 0.8)
        cx = a[0] + (b[0] - a[0]) * t0
        cy = a[1] + (b[1] - a[1]) * t0
        lay.line(cx - 6, cy - width * 0.5, cx + 4, cy + width * 0.4, ramp, tone + 0.8)
    if cuff:
        (cx, cy, r, cramp, ctone) = cuff
        lay.ellipse(cx, cy, r, r * 0.9, cramp, ctone, hgt=0.6)
    return m


def tableau(kind='alexei'):
    karsk = kind == 'alexei'
    R = karsk_ramps() if karsk else archive_ramps_tab()
    lay = kit.MLayer(VW, VH, R, 'x1_%s_desk' % kind)
    yy, xx = np.mgrid[0:VH, 0:VW].astype(np.float32)
    rng = np.random.default_rng(1 if karsk else 2)
    # ---- back wall + window (upper right) ----------------------------------------------------
    lay.put(np.ones((VH, VW), bool), 0, 0, 'W', 3.4 + (pg.value_noise(VW, VH, 40, 5, octaves=2) - 0.5) * 0.4)
    wx0, wx1, wy0, wy1 = 430, 612, 0, 150
    if karsk:
        # dawn: sage sky, grain silos and a crane in haze, frost in the corners
        lay.vgrad(wx0, wy0, wx1 - wx0, wy1 - wy0, 'K', 1.0, 4.4)
        lay.unlit[wy0:wy1, wx0:wx1] = True
        for (sx, sw, sh) in ((450, 22, 70), (474, 22, 76), (498, 22, 66)):
            lay.rect(sx, wy1 - sh, sw - 2, sh, 'W', 6.0, flat=True, unlit=True)
            lay.rect(sx, wy1 - sh, 3, sh, 'W', 7.0, flat=True, unlit=True)
            lay.ellipse(sx + sw / 2 - 1, wy1 - sh, sw / 2 - 1, 3, 'W', 6.6, flat=True, unlit=True)
        kit_crane = [(540, 150), (548, 40), (606, 46)]
        lay.polyline(kit_crane, 'W', 5.4, unlit=True)
        lay.line(549, 40, 538, 52, 'W', 5.4, unlit=True)
        lay.rect(520, 120, 90, 30, 'W', 5.2, flat=True, unlit=True)
    else:
        # dusk: navy sky, tenement roofs and -- far, muted -- the dome
        lay.vgrad(wx0, wy0, wx1 - wx0, wy1 - wy0, 'B', 2.0, 4.6)
        lay.unlit[wy0:wy1, wx0:wx1] = True
        m, mx, my = lay.ellipse_mask(536, 106, 30, 26)
        m &= (np.arange(m.shape[0])[:, None] + my) < 106
        lay.put(m, mx, my, 'W', 5.6, flat=True, unlit=True)
        lay.rect(533, 72, 7, 9, 'W', 5.6, flat=True, unlit=True)
        lay.rect(500, 104, 72, 12, 'W', 5.6, flat=True, unlit=True)
        lay.rect(430, 116, 182, 34, 'W', 3.6, flat=True, unlit=True)
        for x in range(436, 612, 12):
            lay.poly([(x, 116), (x + 10, 116), (x + 5, 108)], 'W', 3.6, unlit=True)
            if rng.random() < 0.3:
                lay.rect(x + 3, 124, 3, 5, 'A', 4.0, flat=True, emis=True)
    # window frame + mullions (dark wood)
    for (x, y, w, h) in ((wx0 - 6, wy0, 6, wy1 + 8), (wx1, wy0, 8, wy1 + 8), (wx0 - 6, wy1, wx1 - wx0 + 14, 10),
                         (520, wy0, 5, wy1), (wx0, 70, wx1 - wx0, 4)):
        lay.rect(x, y, w, h, 'W', 1.4, hgt=0.6, flat=True)
    lay.rect(wx0 - 6, wy1, wx1 - wx0 + 14, 1, 'W', 4.0, hgt=0.7, flat=True)
    # ---- desk top: perspective plane from y 196 to the bottom ----------------------------------
    top = 196
    desk = [(0, top + 10), (VW, top - 6), (VW, VH), (0, VH)]
    m, mx, my = lay.poly(desk, 'D', 3.0, hgt=0.0)
    lay.paint_normal(m, mx, my, (0.0, 0.62, 0.78))
    # wood grain
    for k in range(0, 160, 7):
        y0 = top + 6 + k
        pts = [(0, y0 + rng.uniform(-1, 1)), (200, y0 - 2 + rng.uniform(-1, 1)), (420, y0 - 4), (VW, y0 - 6)]
        lay.polyline([(int(a), int(b)) for a, b in kit.smooth_poly(pts, 6)], 'D', 2.4 if k % 14 else 3.4)
    lay.line(0, top + 10, VW, top - 6, 'D', 5.0)                         # lit desk edge (far)
    # ---- lamp (upper left), its cone of light lands on the papers ------------------------------
    lx, ly = 158, 118
    if karsk:
        # simple enamel lamp: round base, straight stem, conical shade
        lay.ellipse(116, 222, 24, 7, 'W', 2.0, hgt=0.6)
        lay.rect(113, 120, 5, 100, 'W', 2.4, hgt=0.7, flat=True)
        lay.rect(113, 120, 1, 100, 'W', 5.0, hgt=0.75, flat=True)
        lay.line(116, 122, 150, 100, 'W', 2.6)
        shade = [(132, 88), (160, 92), (188, 126), (128, 124)]
    else:
        # articulated drafting lamp clamped to the desk edge
        lay.rect(104, 206, 20, 10, 'W', 2.0, hgt=0.7, flat=True)
        lay.line(114, 206, 92, 140, 'W', 4.6); lay.line(115, 206, 93, 140, 'W', 2.6)
        lay.line(92, 140, 138, 96, 'W', 4.6); lay.line(93, 141, 139, 97, 'W', 2.6)
        lay.ellipse(92, 140, 4, 4, 'W', 3.6, hgt=0.8)
        shade = [(134, 86), (162, 90), (190, 126), (126, 124)]
    lay.poly(shade, 'W', 2.6, hgt=0.8)
    lay.line(shade[0][0], shade[0][1], shade[3][0], shade[3][1], 'W', 5.0)
    lay.line(shade[3][0], shade[3][1], shade[2][0], shade[2][1], 'A', 6.0, emis=True)
    lay.line(shade[3][0] + 2, shade[3][1] + 1, shade[2][0] - 2, shade[2][1] + 1, 'A', 5.0, emis=True)
    lay.ellipse(158, 127, 9, 3, 'A', 6.0, emis=True)
    # ---- props on the desk ------------------------------------------------------------------
    if karsk:
        # open file folder (left) with a label, the freight ledger, tea glass in a metal holder
        folder = [(170, 236), (330, 230), (342, 330), (150, 338)]
        lay.poly(folder, 'P', 2.4, hgt=0.3)
        lay.poly([(176, 240), (326, 234), (334, 320), (160, 328)], 'P', 3.6, hgt=0.35)
        lay.rect(196, 252, 50, 14, 'P', 5.4, flat=True)
        lay.put(kit.text_mask('31', '57'), 212, 256, 'I', 1.0, flat=True)
        # ledger page edge with the red C-17 stamp (small, re-seen)
        lay.poly([(352, 300), (470, 296), (478, 352), (346, 358)], 'P', 4.4, hgt=0.3)
        for k in range(5):
            lay.line(356, 306 + k * 10, 472, 302 + k * 10, 'P', 2.8)
        lay.rect(420, 318, 26, 14, 'X', 2.0, flat=True)
        lay.rect(423, 321, 20, 8, 'P', 4.4, flat=True)
        lay.put(kit.text_mask('C-17', '35'), 425, 323, 'X', 2.0, flat=True)
        # tea glass in a podstakannik
        lay.rect(76, 254, 24, 30, 'A', 3.0, hgt=0.7, flat=True)
        lay.rect(78, 248, 20, 8, 'A', 5.0, hgt=0.6, flat=True)
        lay.rect(76, 284, 24, 4, 'W', 4.0, hgt=0.7, flat=True)
        lay.polyline([(100, 260), (108, 264), (108, 278), (100, 280)], 'W', 4.4)
        for k in range(5):
            lay.px(84 + k * 2, 240 - k * 5, 'P', 5.0, unlit=True)
            lay.px(86 + k * 3, 236 - k * 6, 'P', 4.0, unlit=True)
        # the document being filed (bright sheet), hands
        doc = [(206, 214), (330, 206), (344, 290), (214, 298)]
        lay.poly(doc, 'P', 6.0, hgt=0.4)
        for k in range(7):
            lay.line(218, 222 + k * 9, 320, 216 + k * 9, 'I', 2.6)
        lay.rect(290, 262, 22, 10, 'X', 2.0, flat=True)
        lay.rect(292, 264, 18, 6, 'P', 6.0, flat=True)
        sleeve(lay, [(640, 292), (540, 278), (402, 262)], 28, 'G', 2.4, seed=3)
        lay.ellipse(394, 261, 13, 12, 'G', 4.0, hgt=0.6)                # knitted cuff
        hand(lay, 382, 258, math.radians(188), 1.2, 'flat', tone=2.6)    # pushes the sheet in
        sleeve(lay, [(600, 360), (480, 350), (356, 330)], 26, 'G', 2.0, seed=4)
        lay.ellipse(348, 328, 12, 11, 'G', 3.6, hgt=0.6)
        hand(lay, 336, 324, math.radians(202), 1.1, 'hold', tone=2.4)    # holds the folder open
        ushanka(lay, 556, 222)
        # silhouette: only the shoulder mass at the frame edge (over-the-shoulder framing)
        body = [(520, 360), (548, 262), (596, 226), (640, 214), (640, 360)]
        lay.poly(body, 'N', 0.6, hgt=0.4)
        rim = 'G'
    else:
        # envelope, coffee, fountain pen, the pencil slip with C-17
        lay.poly([(170, 240), (300, 236), (306, 300), (166, 304)], 'P', 5.0, hgt=0.3)
        lay.polyline([(170, 240), (236, 276), (300, 236)], 'P', 3.4)
        lay.rect(72, 246, 30, 32, 'P', 5.6, hgt=0.7, flat=True)
        lay.rect(72, 246, 30, 4, 'D', 1.6, hgt=0.7, flat=True)
        lay.polyline([(102, 254), (110, 258), (110, 270), (102, 272)], 'P', 4.4)
        lay.line(330, 330, 420, 346, 'I', 1.4)
        lay.line(330, 331, 420, 347, 'A', 4.0)
        lay.poly([(440, 304), (520, 300), (524, 340), (444, 344)], 'P', 5.4, hgt=0.3)
        hp = kit.hand_polys('C-17', 456, 312, 14, 9, 3, seed=5)
        lay.put(kit.stroke_mask(VW, VH, hp, 0.9), 0, 0, 'K', 2.2, flat=True)
        # the memorandum being folded: lower half flat, upper half bent over (lighter, foreshortened)
        lower = [(206, 250), (334, 244), (344, 300), (214, 306)]
        lay.poly(lower, 'P', 5.6, hgt=0.4)
        upper = [(208, 250), (334, 244), (330, 222), (212, 228)]
        lay.poly(upper, 'P', 6.6, hgt=0.6)
        lay.line(206, 250, 334, 244, 'P', 3.6)                           # the crease
        disc, pillar = kit.reichssiegel_mask(9)
        lay.put(disc, 262, 254, 'N', 0.6, flat=True)
        lay.put(pillar, 262, 254, 'P', 6.4, flat=True)
        for k in range(4):
            lay.line(224, 268 + k * 8, 326, 264 + k * 8, 'I', 2.0)
        sleeve(lay, [(640, 290), (540, 270), (404, 250)], 28, 'B', 1.6, seed=3)
        lay.ellipse(396, 249, 12, 12, 'P', 5.0, hgt=0.6)                 # white shirt cuff
        hand(lay, 384, 246, math.radians(186), 1.2, 'hold', tone=2.6)    # pinches the crease
        sleeve(lay, [(600, 360), (480, 348), (356, 322)], 26, 'B', 1.4, seed=4)
        lay.ellipse(348, 320, 11, 11, 'P', 4.6, hgt=0.6)
        hand(lay, 336, 316, math.radians(200), 1.1, 'flat', tone=2.4)    # presses the lower half
        fedora(lay, 556, 220)
        body = [(520, 360), (548, 262), (596, 226), (640, 214), (640, 360)]
        lay.poly(body, 'N', 0.6, hgt=0.4)
        rim = 'B'
    # rim light from the lamp on the shoulder edge facing it
    sil = (lay.rid == R['N'])
    e = sil & ~kit.erode(sil, 1)
    left_side = xx < 600
    lay.put(e & left_side & (yy > 100), 0, 0, rim, 4.4, flat=True)
    # ---- light: one warm lamp pool + cool window spill ---------------------------------------
    lights = [{'pos': (lx, ly + 12), 'kind': 'warm', 'energy': 1.9, 'radius': 330, 'height': 60, 'falloff': 1.1,
               'cone': (0.62, 0.78, 0.62)},
              {'pos': (520, 70), 'kind': 'cold', 'energy': 0.55, 'radius': 300, 'height': -20}]
    F = kit.light_fields(lay, lights)
    # soft glow just around the shade (hand-shaped, not a sphere)
    g = np.clip(1 - np.hypot((xx - 158) / 46, (yy - 112) / 26), 0, 1) ** 1.6
    F['warm'] += g * 0.55
    vignette(lay, 1.6, cx=300, cy=250)
    lay.resolve(F, band=2.2)
    return lay


# =========================================================================== build
def build_all(doc_dir, prev_dir=None):
    os.makedirs(doc_dir, exist_ok=True)
    out = []
    items = [
        ('x1_stamp_closeup', stamp_closeup, 'A1->M1 match cut 1/2: red C-17 stamp on the Karsk ledger (sepia)'),
        ('x1_blueprint_closeup', blueprint_closeup,
         'A1->M1 match cut 2/2: pencil C-17 on a Berlin plan, same position/size as the stamp'),
        ('x1_border_map', border_map, 'X1: neutral schematic of a fictional border corridor, C-17 route in red'),
        ('x1_alexei_desk', lambda: tableau('alexei'), 'X1: Alexei files the document in Karsk (copper lamp)'),
        ('x1_konrad_desk', lambda: tableau('konrad'), 'X1: Konrad folds the matching memorandum in Berlin'),
    ]
    for name, fn, desc in items:
        lay = fn()
        p = os.path.join(doc_dir, name + '.png')
        arr = lay.c.copy()
        arr[..., 3] = 255
        kit.save_rgba(arr, p)
        out.append((p, desc + ' (640x360)'))
        if prev_dir:
            kit.ensure_gdignore(prev_dir)
            from PIL import Image
            im = Image.fromarray(arr, 'RGBA')
            pg.upscale(im.crop((160, 90, 480, 270)), 3).save(os.path.join(prev_dir, 'still_%s_x3.png' % name))
    if prev_dir:
        # match-cut check: blend the two close-ups 50/50
        from PIL import Image
        a = Image.open(os.path.join(doc_dir, 'x1_stamp_closeup.png')).convert('RGB')
        b = Image.open(os.path.join(doc_dir, 'x1_blueprint_closeup.png')).convert('RGB')
        Image.blend(a, b, 0.5).save(os.path.join(prev_dir, 'still_matchcut_blend.png'))
    return out
