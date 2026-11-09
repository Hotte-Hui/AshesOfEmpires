"""env_flashback_soviet -- the six plates of the two flashback films on the Soviet side (TECHNICAL_ARCHITECTURE 12.15).

  settlement  (card hist.soviet.special_settlements)  steppe / kommandantur / boundary
  kyshtym     (card hist.soviet.kyshtym)              plant / village / fence
Only what the cards say is shown: a settlement of barracks and earth huts in open country; the office of the
commandant with people waiting to report (from behind); the road out of the district, closed by a barrier; the
works across the water on a still day (no blast, no cloud); a village left behind with open doors and cold
chimneys; the wire and the gate of the closed city.  No uniforms, no insignia, no flags.
Painted with env_flashback_kit (luminance -> sepia ramp); deterministic.
"""
from __future__ import annotations

import math

import numpy as np

import env_prologue_kit as PK
import env_veltrava_lib as vlib
from env_flashback_kit import (PW, PH, Plate, rng, greek, smoke, wheel, pole, wire, tufts, patches, tree_line,
                               figure_back)


# ================================================================================================ special settlement
def steppe() -> Plate:
    p = Plate(v=0.6)
    hz = 222
    sky = p.box(0, 0, PW, hz)
    p.vgrad(sky, 0, 0.50, hz, 0.82)
    p.tex(sky, 0.10, 60, 71, sx=6.0)
    p.tex(sky, 0.04, 16, 72, sx=4.0)
    p.fill(p.poly([(0, hz - 7), (120, hz - 11), (260, hz - 6), (400, hz - 12), (PW, hz - 8), (PW, hz), (0, hz)]), 0.56)
    gr = p.box(0, hz, PW, PH)
    p.vgrad(gr, hz, 0.72, PH, 0.82)
    patches(p, gr, 73)
    for off in (-1, 1):                                               # the track: two ruts toward the settlement
        pts = [(246 + off * 62, PH), (262 + off * 30, 322), (276 + off * 13, 276), (286 + off * 6, 250),
               (292 + off * 2, hz + 8)]
        for i, w in enumerate((9, 6, 3, 2)):
            p.fill(p.line([pts[i], pts[i + 1]], w), 0.40)

    def barrack(x, yb, w, h, seed):
        p.fill(p.box(x, yb - h, x + w, yb), 0.2)
        p.fill(p.poly([(x - 2, yb - h), (x + w + 2, yb - h), (x + w - 3, yb - h - 5), (x + 3, yb - h - 5)]), 0.86)
        p.fill(p.box(x - 2, yb - h, x + w + 2, yb - h + 1), 0.32)
        for wx in range(x + 5, x + w - 5, 9):
            p.fill(p.box(wx, yb - h + 3, wx + 3, yb - h + 6), 0.56 if (wx // 9) % 3 else 0.1)
        p.fill(p.box(x + w // 2, yb - 7, x + w // 2 + 4, yb), 0.09)
        sx = x + w // 3
        p.fill(p.box(sx, yb - h - 11, sx + 2, yb - h - 4), 0.14)
        smoke(p, sx + 1, yb - h - 12, 50, 13, 0.60, seed=seed, k=0.5, grow=2.6)

    for i, (x, yb, w, h) in enumerate(((148, 235, 54, 9), (212, 233, 46, 8), (270, 236, 60, 10), (342, 234, 50, 9),
                                        (402, 238, 46, 9), (176, 248, 72, 12), (300, 252, 78, 13))):
        barrack(x, yb, w, h, 74 + i)
    for i, (x, yb) in enumerate(((116, 244), (262, 266), (404, 258))):   # earth huts
        m = p.ell(x, yb, 17, 8) & (p.yy < yb)
        p.fill(m, 0.5)
        p.fill(PK.edge(m, 0, -1), 0.86)
        p.fill(p.box(x - 2, yb - 5, x + 2, yb), 0.09)
        p.fill(p.box(x + 7, yb - 13, x + 9, yb - 6), 0.14)
        smoke(p, x + 8, yb - 14, 40, 10, 0.60, seed=90 + i, k=0.5, grow=2.4)
    tops = []
    for x, yb, h in ((466, 344, 128), (424, 296, 74), (398, 270, 46), (382, 255, 30), (372, 246, 20)):
        pole(p, x, yb, h, 3 if h > 60 else 2, 0.15, arm=max(2, h // 14))
        tops.append((x + 1, yb - h + max(2, h // 12)))
    for a, b in zip(tops, tops[1:]):
        wire(p, a[0], a[1], b[0], b[1], max(1.0, (a[0] - b[0]) * 0.06), 0.3)
    wire(p, tops[0][0], tops[0][1], PW + 40, tops[0][1] - 30, 6, 0.3)
    for x, yf in ((252, 247), (258, 248), (330, 258)):                # people, far off
        p.fill(p.box(x, yf - 6, x + 2, yf), 0.12)
        p.fill(p.box(x, yf - 8, x + 2, yf - 6), 0.3)
    tufts(p, 0, PW, 300, PH + 4, 70, 76, 0.24, 12)
    p.fill(p.poly([(58, PH), (62, 300), (68, 298), (70, PH)]), 0.14)  # an old post in front
    p.fill(p.line([(64, 318), (20, 334)], 1), 0.2)
    return p


def kommandantur() -> Plate:
    up = 30                                                           # painted lower, cropped at the top:
    hh = PH + up                                                      # the queue stays above the caption plate
    p = Plate(PW, hh, v=0.6)
    hz = 198
    sky = p.box(0, 0, PW, hz)
    p.vgrad(sky, 0, 0.55, hz, 0.76)
    p.tex(sky, 0.08, 70, 81, sx=5.0)
    p.fill(p.box(0, hz - 3, PW, hz), 0.52)
    for x, w in ((6, 62), (82, 50), (150, 40)):                       # barracks, far off
        p.fill(p.box(x, hz - 11, x + w, hz), 0.3)
        p.fill(p.poly([(x - 2, hz - 11), (x + w + 2, hz - 11), (x + w - 3, hz - 16), (x + 3, hz - 16)]), 0.84)
    gr = p.box(0, hz, PW, hh)
    p.vgrad(gr, hz, 0.72, hh, 0.80)
    patches(p, gr, 82, cell=18, sx=2.5, levels=((0.62, 0.52, 0.6), (0.74, 0.40, 0.5)))
    path = p.poly([(40, hh), (250, hh), (372, 262), (336, 262)])      # trodden to the porch
    p.mix(path, 0.48, 0.75)
    p.tex(path, 0.06, 6, 83)
    # the office: a log house
    hx0, hx1, hy0, hy1 = 268, 474, 134, 258
    p.fill(p.box(hx0, hy0, hx1, hy1), 0.28)
    for y in range(hy0, hy1, 7):
        p.fill(p.box(hx0, y, hx1, y + 1), 0.18)
        p.fill(p.box(hx0, y + 1, hx1, y + 2), 0.35)
    for x in (hx0 - 3, hx1 - 3):                                      # the crossed log ends
        for y in range(hy0, hy1, 7):
            p.fill(p.box(x, y + 1, x + 6, y + 6), 0.22)
            p.fill(p.box(x + 1, y + 2, x + 5, y + 5), 0.36)
    roof = p.poly([(hx0 - 16, hy0 + 2), (hx1 + 16, hy0 + 2), (hx1 - 14, hy0 - 46), (hx0 + 14, hy0 - 46)])
    p.fill(roof, 0.86)
    p.tex(roof, 0.03, 12, 84)
    p.fill(p.box(hx0 - 16, hy0 + 2, hx1 + 16, hy0 + 6), 0.16)
    p.fill(p.box(412, hy0 - 66, 424, hy0 - 40), 0.22)
    p.fill(p.box(410, hy0 - 68, 426, hy0 - 65), 0.86)
    smoke(p, 418, hy0 - 70, 86, 30, 0.58, seed=85, k=0.6, grow=4.0)
    for wx in (284, 432):
        p.fill(p.box(wx - 3, 164, wx + 31, 214), 0.88)
        p.fill(p.box(wx, 167, wx + 28, 211), 0.11)
        p.mix(p.box(wx + 1, 168, wx + 12, 186), 0.62, 0.7)
        p.fill(p.box(wx + 13, 167, wx + 15, 211), 0.88)
        p.fill(p.box(wx, 187, wx + 28, 189), 0.88)
    # the sign, the porch on two posts, three steps, the door
    sign = p.box(326, 146, 414, 162)
    p.fill(sign, 0.86)
    p.fill(sign & ~p.box(327, 147, 413, 161), 0.3)
    word = 'КОМЕНДАТУРА'
    if all(vlib._glyph(ch, 's')[0] is not None for ch in word):
        p.fill(p.text(word, 370, 152, 's', 1, True), 0.14)
    else:
        greek(p, 332, 152, 408, 2, 4, seed=87, val=0.2)
    p.fill(p.poly([(318, 166), (422, 166), (428, 174), (312, 174)]), 0.86)
    p.fill(p.box(312, 174, 428, 177), 0.18)
    p.fill(p.box(345, 179, 395, 258), 0.5)
    p.fill(p.box(348, 182, 392, 258), 0.1)
    p.fill(p.box(320, 177, 324, 260) | p.box(416, 177, 420, 260), 0.2)
    for i in range(3):
        p.fill(p.box(314 - i * 5, 258 + i * 5, 426 + i * 5, 263 + i * 5), 0.56 - 0.08 * i)
        p.fill(p.box(314 - i * 5, 258 + i * 5, 426 + i * 5, 259 + i * 5), 0.8)
    # a notice board
    p.fill(p.box(200, 196, 256, 236), 0.3)
    p.fill(p.box(198, 192, 258, 196), 0.86)
    p.fill(p.box(204, 236, 207, 266) | p.box(249, 236, 252, 266), 0.2)
    for i, (sx, sy, sw, sh) in enumerate(((204, 200, 14, 18), (221, 201, 15, 22), (239, 200, 13, 16))):
        p.fill(p.box(sx, sy, sx + sw, sy + sh), 0.88)
        greek(p, sx + 2, sy + 3, sx + sw - 2, sh // 4, 3, seed=86 + i, val=0.4)
    # the line of people waiting to report, seen from behind (far -> near)
    q = ((352, 276, 36, 0.20, None, 0.56, True), (329, 281, 39, 0.15, 0.12, None, False),
         (305, 287, 42, 0.24, None, 0.62, True), (279, 294, 46, 0.13, 0.10, None, False),
         (250, 302, 50, 0.19, None, 0.50, True), (218, 311, 55, 0.12, 0.16, None, False),
         (182, 321, 60, 0.17, None, 0.58, True))
    for i, (x, yf, h, coat, hat, scarf, skirt) in enumerate(q):
        figure_back(p, x, yf, h, coat=coat, head=0.3, hat=hat, scarf=scarf, skirt=skirt, rim=0.12)
        if i == 4:
            figure_back(p, 270, 305, 28, coat=0.22, head=0.3, hat=0.14)   # a child beside its mother
    out = Plate()
    out.v = p.v[up:up + PH].copy()
    return out


def boundary() -> Plate:
    p = Plate(v=0.6)
    hz = 180
    vp = (198, hz)
    sky = p.box(0, 0, PW, hz)
    p.vgrad(sky, 0, 0.36, hz, 0.80)
    p.tex(sky, 0.09, 64, 91, sx=7.0)
    p.lift(p.box(0, hz - 22, PW, hz), np.clip((p.yy - (hz - 22)) / 22.0, 0, 1) * 0.3)   # the last light, low
    p.fill(p.poly([(0, hz - 5), (150, hz - 9), (300, hz - 4), (430, hz - 8), (PW, hz - 5), (PW, hz), (0, hz)]), 0.5)
    gr = p.box(0, hz, PW, PH)
    p.vgrad(gr, hz, 0.66, PH, 0.76)
    patches(p, gr, 92)
    # the road out of the district: from the foreground on the right to the horizon on the left
    l0, r0 = (128.0, float(PH)), (452.0, float(PH))
    road = p.poly([l0, r0, (vp[0] + 2, hz), (vp[0] - 2, hz)])
    p.mix(road, 0.50, 0.9)
    p.tex(road, 0.05, 10, 93)
    n = PK.noise(PW, PH, 9, 98, 3, 2.0)
    for u in (0.27, 0.71):                                            # two wheel ruts, broken where snow lies in them
        xb = l0[0] + (r0[0] - l0[0]) * u
        p.fill(p.line([(xb, PH), vp], 4) & road & (n < 0.62), 0.34)
    mid_x = (l0[0] + r0[0]) / 2.0
    p.mix(p.line([(mid_x, PH), vp], 9) & road & (n > 0.45), 0.76, 0.8)   # snow left on the crown of the road
    for e in (l0, r0):                                                # and thrown to the verges, in patches
        p.mix(p.line([e, vp], 5) & (n > 0.5), 0.86, 0.9)

    def at(yb):
        t = (PH - yb) / float(PH - hz)
        return l0[0] + (vp[0] - 2 - l0[0]) * t, r0[0] + (vp[0] + 2 - r0[0]) * t

    tops = []
    for s in (1.0, 0.60, 0.36, 0.22, 0.13, 0.08):                     # the telegraph line runs on with the road
        x = int(vp[0] + (500 - vp[0]) * s)
        yb = int(hz + (352 - hz) * s)
        h = int(150 * s)
        pole(p, x, yb, h, 3 if s > 0.5 else (2 if s > 0.15 else 1), 0.14, arm=max(1, int(12 * s)))
        tops.append((x + 1, yb - h + max(2, h // 12)))
    for a, b in zip(tops, tops[1:]):
        wire(p, a[0], a[1], b[0], b[1], max(0.5, (a[0] - b[0]) * 0.05), 0.26)
    wire(p, tops[0][0], tops[0][1], PW + 60, tops[0][1] - 50, 8, 0.26)
    # the hut beside the barrier
    yb = 262
    xl, xr = at(yb)
    hx, hy = int(xl) - 86, yb - 50
    p.fill(p.box(hx, hy, hx + 60, yb + 4), 0.25)
    for y in range(hy, yb + 4, 6):
        p.fill(p.box(hx, y, hx + 60, y + 1), 0.19)
    p.fill(p.poly([(hx - 7, hy + 1), (hx + 67, hy + 1), (hx + 56, hy - 17), (hx + 4, hy - 17)]), 0.86)
    p.fill(p.box(hx - 7, hy + 1, hx + 67, hy + 4), 0.16)
    p.fill(p.box(hx + 34, hy + 12, hx + 52, hy + 30), 0.6)            # a lit pane
    p.fill(p.box(hx + 42, hy + 12, hx + 43, hy + 30) | p.box(hx + 34, hy + 20, hx + 52, hy + 21), 0.2)
    p.fill(p.box(hx + 8, hy + 14, hx + 24, yb + 4), 0.1)
    p.fill(p.box(hx + 46, hy - 31, hx + 49, hy - 15), 0.14)
    smoke(p, hx + 47, hy - 32, 70, 22, 0.56, seed=94, k=0.55, grow=3.6)
    # the barrier across the road: two posts, the striped pole down, its counterweight
    bar_y = yb - 27
    for x in (xl - 12, xr + 9):
        p.fill(p.box(x, yb - 33, x + 5, yb + 2), 0.12)
        p.fill(p.box(x + 5, yb - 33, x + 6, yb + 2), 0.3)
    x, k = int(xl - 26), 0
    end = int(xr + 18)
    while x < end:
        p.fill(p.box(x, bar_y, min(x + 12, end), bar_y + 4), 0.9 if k % 2 == 0 else 0.12)
        x += 12
        k += 1
    p.fill(p.box(xl - 38, bar_y - 4, xl - 25, bar_y + 9), 0.12)
    p.shade(p.box(int(xl - 26), yb + 3, end, yb + 5) & road, 0.25)    # its thin shadow on the road
    sx = int(xr) + 58                                                 # a board on a post: nobody reads it from here
    p.fill(p.box(sx, yb - 56, sx + 3, yb + 4), 0.14)
    p.fill(p.box(sx - 18, yb - 62, sx + 21, yb - 40), 0.88)
    p.fill(p.box(sx - 18, yb - 62, sx + 21, yb - 61) | p.box(sx - 18, yb - 41, sx + 21, yb - 40), 0.3)
    greek(p, sx - 14, yb - 57, sx + 17, 3, 5, seed=95, val=0.25, thick=2)
    tufts(p, 0, 120, 300, PH + 4, 30, 96, 0.22, 12)
    tufts(p, 462, PW, 322, PH + 4, 14, 97, 0.22, 12)
    p.dusk(250, 176, 330, 230, 0.35)
    return p


# ================================================================================================ Mayak, 1957
def plant() -> Plate:
    p = Plate(v=0.6)
    hz = 188
    sky = p.box(0, 0, PW, hz)
    p.vgrad(sky, 0, 0.56, hz, 0.82)
    p.tex(sky, 0.09, 70, 101, sx=6.0)
    p.tex(sky, 0.03, 14, 102, sx=4.0)
    tree_line(p, hz, 14, 103, 0.36)
    dark = 0.2                                                        # the works: halls, stacks, the tank field
    p.fill(p.box(58, hz - 14, 142, hz), dark + 0.04)
    p.fill(p.box(150, hz - 32, 232, hz), dark)
    p.fill(p.box(238, hz - 22, 300, hz), dark + 0.03)
    for i in range(5):                                                # a saw-tooth roof
        x = 302 + i * 15
        p.fill(p.poly([(x, hz - 16), (x + 15, hz - 16), (x + 15, hz - 26)]), dark)
    p.fill(p.box(302, hz - 16, 378, hz), dark + 0.02)
    p.fill(p.box(384, hz - 48, 414, hz), dark)
    for wx in range(156, 228, 8):
        p.fill(p.box(wx, hz - 24, wx + 3, hz - 14), 0.5)
    stacks = ((196, 100, 5), (262, 72, 4), (394, 86, 5))
    for x, h, w in stacks:
        p.fill(p.box(x, hz - h, x + w, hz - 20), dark - 0.02)
        p.fill(p.box(x - 1, hz - h, x + w + 1, hz - h + 2), dark - 0.05)
        for by in range(hz - h + 12, hz - 30, 14):
            p.fill(p.box(x, by, x + w, by + 2), 0.44)
        smoke(p, x + w // 2, hz - h - 2, -70, 14, 0.62, seed=104 + x, k=0.5, grow=4.2)
    for i in range(6):                                                # low concrete lids, a vent on each
        x = 428 + i * 13
        p.fill(p.ell(x, hz - 1, 6, 5) & (p.yy < hz), dark + 0.06)
        p.fill(p.box(x, hz - 9, x + 1, hz - 5), dark)
    for x in range(40, 500, 11):                                      # the fence along the shore
        p.fill(p.box(x, hz - 6, x + 1, hz), 0.3)
    p.fill(p.box(40, hz - 5, 500, hz - 4), 0.3)
    water = p.box(0, hz, PW, 306)
    p.vgrad(water, hz, 0.70, 306, 0.54)
    p.tex(water, 0.05, 30, 105, sx=10.0)
    rip = (p.yy.astype(np.int32) % 3) != 2                            # everything once more in the water, broken
    for x0, x1, depth in ((58, 142, 12), (150, 232, 26), (238, 300, 18), (302, 378, 20), (384, 414, 40), (428, 500, 6)):
        p.mix(p.box(x0, hz, x1, hz + depth) & rip, 0.30, 0.5)
    for x, h, w in stacks:
        p.mix(p.box(x, hz, x + w, hz + int(h * 0.8)) & rip, 0.30, 0.45)
    p.fill(p.box(0, hz, PW, hz + 1), 0.86)
    r = rng(106)
    for _ in range(60):
        x, y = int(r.integers(0, PW)), int(r.integers(hz + 6, 300))
        p.fill(p.box(x, y, x + int(r.integers(4, 14)), y + 1), 0.80)
    bank = p.poly([(0, 304), (140, 296), (300, 308), (PW, 300), (PW, PH), (0, PH)])
    p.fill(bank, 0.36)
    p.tex(bank, 0.06, 14, 107, sx=3.0)
    p.fill(PK.edge(bank, 0, -1), 0.5)
    for _ in range(90):                                               # reeds
        x = float(r.uniform(-4, PW + 4))
        yb = 300 + float(r.uniform(0, 30))
        h = float(r.uniform(14, 34))
        lean = float(r.uniform(-4, 5))
        p.fill(p.line([(x, yb), (x + lean, yb - h)]), 0.2)
        if r.random() < 0.5:
            p.fill(p.box(x + lean - 1, yb - h - 4, x + lean + 1, yb - h + 2), 0.13)
    p.fill(p.poly([(318, 322), (412, 318), (402, 336), (330, 338)]), 0.16)   # a boat drawn up on the bank
    p.fill(p.poly([(318, 322), (412, 318), (410, 321), (320, 325)]), 0.44)
    p.fill(p.box(350, 322, 352, 336) | p.box(378, 321, 380, 335), 0.3)
    for x0, x1, top in ((30, 43, -4), (70, 79, 60)):                  # two birches
        trunk = p.poly([(x0, PH), (x1, PH), (x1 - 2, top), (x0 + 2, top)])
        p.fill(trunk, 0.88)
        p.fill(PK.edge(trunk, 1, 0), 0.6)
        for _ in range(26):
            y = int(r.integers(max(0, top), PH))
            xx = int(r.integers(x0 + 1, x1 - 3))
            p.fill(p.box(xx, y, xx + int(r.integers(2, 6)), y + int(r.integers(1, 3))) & trunk, 0.16)
    for _ in range(9):                                                # hanging twigs with the last leaves
        x = int(r.integers(4, 140))
        ln = int(r.integers(30, 110))
        for y in range(0, ln, 3):
            if r.random() < 0.8:
                dx = int(r.integers(-1, 2))
                p.fill(p.box(x + dx, y, x + dx + 2, y + 2), 0.24 if r.random() < 0.7 else 0.5)
    return p


def village() -> Plate:
    p = Plate(v=0.6)
    hz = 172
    base = 252
    sky = p.box(0, 0, PW, hz)
    p.vgrad(sky, 0, 0.60, hz, 0.80)
    p.tex(sky, 0.08, 70, 111, sx=6.0)
    tree_line(p, hz, 34, 112, 0.36, cell=9)
    tree_line(p, hz, 16, 113, 0.27, cell=20)
    gr = p.box(0, hz, PW, PH)
    p.vgrad(gr, hz, 0.54, PH, 0.42)
    p.tex(gr, 0.05, 26, 114, sx=6.0)
    for y0, amp in ((286, 3), (300, 4), (322, 5), (344, 6)):          # the street: ruts, standing water
        pts = [(x, y0 + amp * math.sin(x / 47.0 + y0)) for x in range(-10, PW + 20, 12)]
        p.fill(p.line(pts, 2 if y0 < 310 else 3), 0.32)
    for cx, cy, rx, ry in ((120, 314, 30, 4), (330, 336, 44, 5), (236, 293, 18, 2.5)):
        p.fill(p.ell(cx, cy, rx, ry), 0.72)
        p.fill(p.ell(cx, cy, rx, ry) & (p.yy > cy), 0.6)

    def izba(x, w, h, gable, door):
        p.fill(p.box(x, base - h, x + w, base), 0.29)
        for y in range(base - h, base, 6):
            p.fill(p.box(x, y, x + w, y + 1), 0.19)
            p.fill(p.box(x, y + 1, x + w, y + 2), 0.36)
        if gable:
            p.fill(p.poly([(x - 9, base - h + 1), (x + w + 9, base - h + 1), (x + w / 2.0, base - h - w * 0.38)]), 0.17)
            tri = p.poly([(x, base - h), (x + w, base - h), (x + w / 2.0, base - h - w * 0.34)])
            p.fill(tri, 0.31)
            for yy in range(int(base - h - w * 0.34), base - h, 5):
                p.fill(p.box(x, yy, x + w, yy + 1) & tri, 0.23)
            ay = base - h - int(w * 0.2)
            p.fill(p.box(x + w // 2 - 6, ay - 1, x + w // 2 + 6, ay + 10) & tri, 0.8)
            p.fill(p.box(x + w // 2 - 4, ay + 1, x + w // 2 + 4, ay + 8) & tri, 0.1)
        else:
            roof = p.poly([(x - 9, base - h + 1), (x + w + 9, base - h + 1), (x + w - 6, base - h - 30), (x + 6, base - h - 30)])
            p.fill(roof, 0.18)
            for yy in range(base - h - 28, base - h, 5):
                p.fill(p.box(x - 9, yy, x + w + 9, yy + 1) & roof, 0.25)
        p.fill(p.box(x - 9, base - h + 1, x + w + 9, base - h + 3), 0.12)
        cxm = x + int(w * 0.7)                                        # a cold chimney
        p.fill(p.box(cxm, base - h - 44, cxm + 9, base - h - 20), 0.24)
        p.fill(p.box(cxm - 1, base - h - 46, cxm + 10, base - h - 43), 0.36)
        n = max(2, w // 46)
        for k in range(n):
            wx = x + int((k + 0.5) * w / n) - 9
            wy = base - h + 16
            if door is not None and abs(wx + 9 - door) < 22:
                continue
            p.fill(p.box(wx - 4, wy - 3, wx + 22, wy + 27), 0.88)     # the carved frame
            p.fill(p.poly([(wx - 5, wy - 3), (wx + 23, wy - 3), (wx + 9, wy - 11)]), 0.88)
            p.fill(p.box(wx, wy, wx + 18, wy + 24), 0.09)
            p.fill(p.box(wx + 8, wy, wx + 10, wy + 24) | p.box(wx, wy + 9, wx + 18, wy + 10), 0.88)
            p.fill(p.box(wx - 5, wy + 27, wx + 23, wy + 29), 0.7)
        if door is not None:                                          # the door stands open
            p.fill(p.box(door - 12, base - 46, door + 12, base), 0.6)
            p.fill(p.box(door - 10, base - 44, door + 10, base), 0.06)
            p.fill(p.poly([(door + 10, base - 44), (door + 22, base - 40), (door + 22, base + 3), (door + 10, base)]), 0.4)
            p.fill(p.box(door - 14, base, door + 16, base + 4), 0.5)

    izba(26, 132, 62, True, None)
    izba(206, 110, 58, False, 290)
    izba(368, 126, 64, True, 400)

    def fence_run(x0, x1, seed):
        rr = rng(seed)
        for x in range(x0, x1, 4):
            top = base - 20 + int(rr.integers(0, 3))
            p.fill(p.box(x, top, x + 3, base + 6), 0.36 + 0.05 * ((x // 4) % 2))
        p.fill(p.box(x0, base - 14, x1, base - 13) | p.box(x0, base - 2, x1, base - 1), 0.24)

    fence_run(-6, 22, 4)
    fence_run(162, 184, 5)
    fence_run(320, 342, 6)
    fence_run(496, PW + 6, 7)
    for gx in (184, 342):                                             # the gates stand open
        p.fill(p.box(gx - 2, base - 26, gx + 2, base + 6), 0.2)
        p.fill(p.box(gx + 20, base - 26, gx + 24, base + 6), 0.2)
        p.fill(p.poly([(gx + 2, base - 20), (gx + 13, base - 13), (gx + 13, base + 15), (gx + 2, base + 6)]), 0.4)
        p.fill(p.line([(gx + 2, base - 12), (gx + 13, base - 5)]) | p.line([(gx + 2, base + 1), (gx + 13, base + 9)]), 0.26)
    # the well, its bucket on the ground
    p.fill(p.box(118, 270, 152, 286), 0.3)
    for y in (274, 280):
        p.fill(p.box(118, y, 152, y + 1), 0.2)
    p.fill(p.box(120, 240, 123, 270) | p.box(147, 240, 150, 270), 0.2)
    p.fill(p.poly([(110, 243), (160, 243), (135, 227)]), 0.19)
    p.fill(p.box(123, 252, 147, 254), 0.26)
    p.fill(p.box(135, 254, 136, 268), 0.6)
    p.fill(p.ell(168, 289, 6, 4), 0.26)
    p.fill(p.ell(172, 289, 2.5, 3.5), 0.1)
    # a cart left where it stood, the shafts on the ground
    wheel(p, 388, 282, 11, 0.13)
    wheel(p, 426, 282, 11, 0.13)
    p.fill(p.box(370, 268, 442, 273), 0.21)
    for x in range(372, 442, 9):
        p.fill(p.box(x, 258, x + 1, 268), 0.21)
    p.fill(p.box(370, 258, 442, 259), 0.21)
    p.fill(p.line([(442, 271), (484, 292)], 2) | p.line([(442, 269), (490, 287)], 2), 0.21)
    tufts(p, 0, PW, base + 5, base + 16, 46, 115, 0.26, 6)
    tufts(p, 0, PW, 346, PH + 4, 30, 116, 0.22, 12)
    p.dusk(256, 180, 340, 240, 0.3)
    return p


def fence() -> Plate:
    p = Plate(v=0.5)
    A = p.all()
    p.vgrad(A, 0, 0.62, PH, 0.50)
    p.glow(258, 170, 150, 200, 0.34)                                  # the haze where the road goes on
    canopy = PK.noise(PW, PH, 26, 121, 4)
    p.mix(p.box(0, 0, PW, 96) & (canopy > 0.46), 0.24, np.clip(1.0 - p.yy / 96.0, 0, 1) * 0.9)
    r = rng(122)
    trunks = []
    for _ in range(40):
        x = int(r.integers(-6, PW))
        near = float(r.random()) ** 1.6
        birch = bool(r.random() < 0.3)
        if 196 < x < 318 and (near > 0.12 or 226 < x < 292):
            continue
        trunks.append((near, x, birch))
    trunks.sort()
    gy = 248
    floor_m = p.box(0, gy, PW, PH)
    p.vgrad(floor_m, gy, 0.46, PH, 0.36)
    p.tex(floor_m, 0.06, 16, 123, sx=3.0)
    road = p.poly([(176, PH), (340, PH), (276, 226), (242, 226)])
    p.fill(road, 0.56)
    p.tex(road, 0.04, 12, 124)
    for xb, xt in ((214, 250), (300, 268)):
        p.fill(p.line([(xb, PH), (xt, 228)], 2) & road, 0.42)
    for near, x, birch in trunks:                                     # far trunks first (pale, thin)
        w = int(2 + near * 12)
        yb = int(gy - 6 + near * 110)
        m = p.box(x, 0, x + w, yb)
        if birch:
            p.fill(m, 0.84 - (1.0 - near) * 0.2)
            for _ in range(int(8 + near * 16)):
                y = int(r.integers(0, max(1, yb)))
                p.fill(p.box(x, y, x + int(r.integers(1, max(2, w))), y + int(r.integers(1, 3))) & m, 0.18)
        else:
            val = 0.40 - near * 0.26
            p.fill(m, val)
            if w > 5:
                p.fill(p.box(x, 0, x + 1, yb), min(0.9, val + 0.12))
    # the inner fence, far and pale; then the outer one across everything: posts, six wires with barbs, the arms on top
    for x in range(-4, PW, 22):
        if not 236 < x < 284:
            p.fill(p.box(x, 196, x + 2, 240), 0.40)
    for y in (204, 212, 220, 228):
        p.fill(p.box(0, y, PW, y + 1) & ~p.box(240, 0, 282, PH), 0.42)
    fy = 268
    for k in range(6):
        y = fy - 14 - k * 12
        p.fill(p.box(0, y, PW, y + 1), 0.17)
        for x in range((k * 5) % 9, PW, 9):
            p.fill(p.box(x, y - 1, x + 1, y + 2), 0.17)
    for y in (fy - 86, fy - 91):
        p.fill(p.box(0, y, PW, y + 1), 0.2)
    for x in range(-12, PW + 20, 34):
        p.fill(p.box(x, fy - 82, x + 3, fy + 2), 0.13)
        p.fill(p.box(x + 3, fy - 82, x + 4, fy + 2), 0.3)
        p.fill(p.line([(x + 1, fy - 82), (x + 9, fy - 93)], 2), 0.13)
    # the gate: two leaves of mesh in a frame, chained; a board on it that says nothing we can read
    gx0, gx1 = 190, 326
    gate = p.box(gx0, fy - 80, gx1, fy)
    p.mix(gate, 0.5, 0.25)
    mesh = ((p.xx + p.yy) % 6 < 1) | ((p.xx - p.yy) % 6 < 1)
    p.fill(gate & mesh, 0.24)
    mid = (gx0 + gx1) // 2
    for a, b in ((gx0, mid - 1), (mid + 1, gx1)):
        p.fill(p.box(a, fy - 80, b, fy) & ~p.box(a + 3, fy - 77, b - 3, fy - 3), 0.13)
        p.fill(p.line([(a + 2, fy - 2), (b - 2, fy - 78)], 2), 0.13)
    for x in (gx0 - 5, gx1):
        p.fill(p.box(x, fy - 96, x + 6, fy + 3), 0.11)
        p.fill(p.box(x + 6, fy - 96, x + 7, fy + 3), 0.3)
    p.fill(p.box(mid - 4, fy - 44, mid + 5, fy - 34), 0.09)
    board = p.box(210, fy - 66, 250, fy - 42)
    p.fill(board, 0.88)
    p.fill(board & ~p.box(211, fy - 65, 249, fy - 43), 0.2)
    greek(p, 214, fy - 61, 246, 4, 5, seed=125, val=0.2, thick=2)
    by = fy + 22                                                      # the barrier pole in front of it
    for x in (168, 344):
        p.fill(p.box(x, by - 20, x + 5, by + 6), 0.12)
    x, k = 150, 0
    while x < 352:
        p.fill(p.box(x, by - 16, min(x + 12, 352), by - 12), 0.9 if k % 2 == 0 else 0.12)
        x += 12
        k += 1
    p.fill(p.box(140, by - 20, 152, by - 8), 0.12)
    hx, hy = 362, fy - 64                                             # the hut of the guard
    p.fill(p.box(hx, hy, hx + 46, fy + 8), 0.25)
    for y in range(hy, fy + 8, 6):
        p.fill(p.box(hx, y, hx + 46, y + 1), 0.18)
    p.fill(p.poly([(hx - 6, hy + 2), (hx + 52, hy + 2), (hx + 46, hy - 10), (hx, hy - 10)]), 0.14)
    p.fill(p.box(hx + 6, hy + 12, hx + 24, hy + 30), 0.56)
    p.fill(p.box(hx + 14, hy + 12, hx + 15, hy + 30) | p.box(hx + 6, hy + 20, hx + 24, hy + 21), 0.2)
    p.fill(p.box(hx + 30, hy + 14, hx + 42, fy + 8), 0.1)
    p.fill(p.box(336, fy - 128, 338, fy + 2), 0.12)                   # a lamp on its mast, not lit
    p.fill(p.line([(337, fy - 128), (322, fy - 134)], 2), 0.12)
    p.fill(p.poly([(314, fy - 132), (328, fy - 138), (330, fy - 132)]), 0.16)
    tufts(p, 0, 176, 290, PH + 4, 34, 126, 0.2, 14)
    tufts(p, 344, PW, 290, PH + 4, 34, 127, 0.2, 14)
    p.dusk(258, 180, 320, 230, 0.4)
    return p
