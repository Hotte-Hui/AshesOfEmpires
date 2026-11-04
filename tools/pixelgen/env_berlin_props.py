"""env_berlin_props -- y-sorted prop sprites for M1 (drawn in tone space, baked with scene lights).

Each prop: MLayer + world top-left pos + base_y (footprint y used as sort key).  Props that stand
against the back wall have base_y < WALK_BAND[0] (drawn behind walking actors); the plan basket
stands in front of the walk band (base_y > WALK_BAND[1]) so actors pass behind it.
"""
from __future__ import annotations

import math

import numpy as np

import env_berlin_kit as kit
import env_berlin_layout as L
import pg

X = L.X

R = kit.archive_ramps()


class Prop:
    def __init__(self, name, x, base_y, w, h, note=''):
        self.name = name
        self.w, self.h = w, h
        self.base_y = base_y
        self.x = int(x)
        self.y = int(base_y - (h - 1))
        self.lay = kit.MLayer(w, h, R, name)
        self.note = note
        self.lights = []

    @property
    def pos(self):
        return (self.x, self.y)


# --------------------------------------------------------------------------- shared bits
def iron_trestle(lay, xl, xr, top, bot):
    """Cast-iron drafting stand: two splayed legs, foot bar, cross brace."""
    for (x, s) in ((xl, -1), (xr, 1)):
        lay.rect(x, top, 3, bot - top - 4, 'W', 2.4, hgt=0.6, flat=True)
        lay.rect(x, top, 1, bot - top - 4, 'W', 4.6, hgt=0.65, flat=True)
        # splayed foot
        for k in range(5):
            lay.rect(x + s * k - (1 if s < 0 else 0), bot - 5 + k, 4, 1, 'W', 2.2, hgt=0.5, flat=True)
        lay.rect(x + s * 4 - 2, bot - 1, 7, 1, 'W', 1.4, hgt=0.4, flat=True)
    lay.rect(xl + 3, bot - 9, xr - xl - 3, 2, 'W', 2.6, hgt=0.5, flat=True)
    lay.rect(xl + 3, bot - 9, xr - xl - 3, 1, 'W', 4.4, hgt=0.55, flat=True)
    # diagonal brace
    lay.line(xl + 3, top + 6, xr, bot - 10, 'W', 2.0)


def paper_plan(lay, x, y, w, h, seed, tone=5.0, lines=True):
    lay.rect(x, y, w, h, 'P', tone, hgt=0.4, flat=True)
    lay.rect(x, y + h - 1, w, 1, 'P', tone - 1.2, hgt=0.4, flat=True)
    if not lines:
        return
    rng = np.random.default_rng(seed)
    # a simplified diazo plan: outer wall, partitions, a stair hatch
    lay.rect(x + 3, y + 2, w - 6, 1, 'B', 3.4, flat=True)
    lay.rect(x + 3, y + h - 4, w - 6, 1, 'B', 3.4, flat=True)
    lay.rect(x + 3, y + 2, 1, h - 5, 'B', 3.4, flat=True)
    lay.rect(x + w - 4, y + 2, 1, h - 5, 'B', 3.4, flat=True)
    for k in range(int(rng.integers(2, 4))):
        xx = x + 6 + int(rng.integers(0, max(1, w - 12)))
        lay.rect(xx, y + 2, 1, h - 5, 'B', 4.0, flat=True)
    yy = y + h // 2
    lay.rect(x + 3, yy, w - 6, 1, 'B', 4.0, flat=True)
    for k in range(4):
        lay.rect(x + 6 + k * 2, y + 4, 1, 4, 'B', 4.4, flat=True)


def tape(lay, x, y):
    lay.rect(x, y, 3, 2, 'P', 3.4, hgt=0.5, flat=True)


# --------------------------------------------------------------------------- props
def coat_stand():
    p = Prop('coat_stand', X(96), 291, 22, 66, 'bentwood coat stand with a grey coat, hat and umbrella')
    lay = p.lay
    cx = 10
    # pole + finial
    lay.rect(cx, 4, 2, 58, 'D', 3.0, hgt=0.6, flat=True)
    lay.rect(cx + 1, 4, 1, 58, 'D', 4.4, hgt=0.65, flat=True)
    lay.rect(cx - 1, 1, 4, 3, 'D', 4.0, hgt=0.7, flat=True)
    lay.px(cx, 0, 'D', 4.6)
    lay.px(cx + 1, 0, 'D', 4.6)
    # bentwood hooks
    for s in (-1, 1):
        pts = [(cx + (0 if s < 0 else 1), 8), (cx + s * 3 + (0 if s < 0 else 1), 7), (cx + s * 5 + (0 if s < 0 else 1), 9),
               (cx + s * 5 + (0 if s < 0 else 1), 11)]
        lay.polyline(pts, 'D', 3.4)
    # umbrella ring + legs
    lay.rect(cx - 5, 47, 12, 1, 'D', 3.4, hgt=0.5, flat=True)
    lay.px(cx - 6, 46, 'D', 3.0); lay.px(cx + 7, 46, 'D', 3.0)
    for (a, b) in (((cx, 58), (cx - 8, 65)), ((cx + 1, 58), (cx + 9, 65))):
        lay.line(a[0], a[1], b[0], b[1], 'D', 2.6)
        lay.line(a[0] + (1 if b[0] > a[0] else -1), a[1], b[0], b[1] - 1, 'D', 3.6)
    lay.rect(cx, 58, 2, 8, 'D', 2.4, hgt=0.5, flat=True)
    # grey overcoat on the right hook (folds, collar, sleeve)
    coat = [(14, 10), (19, 12), (20, 30), (21, 46), (13, 47), (12, 30), (12, 13)]
    lay.poly(coat, 'W', 5.4, hgt=0.6)
    lay.line(15, 13, 15, 46, 'W', 3.6)
    lay.line(18, 16, 19, 45, 'W', 4.4)
    lay.line(20, 14, 21, 44, 'W', 6.4)
    lay.rect(13, 10, 6, 3, 'W', 6.4, hgt=0.7, flat=True)      # collar
    lay.rect(13, 47, 8, 1, 'W', 3.0, flat=True)
    lay.line(13, 18, 12, 34, 'W', 3.0)                         # sleeve shadow
    # fedora on the left hook
    lay.rect(2, 7, 9, 2, 'I', 1.8, hgt=0.6, flat=True)
    lay.rect(4, 3, 5, 4, 'I', 2.0, hgt=0.7, flat=True)
    lay.rect(4, 6, 5, 1, 'D', 2.0, hgt=0.7, flat=True)        # hat band
    lay.px(4, 3, 'W', 4.0)
    # umbrella in the ring
    lay.poly([(4, 44), (7, 44), (7, 64), (6, 65)], 'I', 1.6, hgt=0.5)
    lay.line(5, 44, 6, 64, 'I', 2.6)
    lay.polyline([(5, 44), (5, 40), (3, 38), (2, 40)], 'D', 2.4)
    return p


def drafting_konrad():
    p = Prop('drafting_konrad', X(284), 294, 78, 76, "Konrad's drafting board with the approved plan (plan_a)")
    lay = p.lay
    by0, by1 = 27, 50                      # board top / bottom edge (local y)
    # stand: splayed iron legs + central tilting column with its knob
    iron_trestle(lay, 14, 58, by1 + 5, 75)
    lay.rect(35, by1 + 3, 5, 14, 'W', 2.6, hgt=0.7, flat=True)
    lay.rect(35, by1 + 3, 1, 14, 'W', 4.6, hgt=0.75, flat=True)
    lay.ellipse(37.5, by1 + 9.5, 3.0, 3.0, 'W', 3.4, hgt=0.85, flat=True)
    lay.px(36, by1 + 8, 'W', 6.4)
    # board: tilted back, so the far (top) edge is a little narrower -> trapezoid
    board = [(8, by0), (70, by0), (74, by1), (4, by1)]
    lay.poly(board, 'W', 6.0, hgt=0.35)
    lay.paint_normal(*lay.poly_mask(board), (0.0, 0.55, 0.83))
    lay.line(8, by0, 70, by0, 'D', 4.6)                      # far edge of the frame (lit)
    lay.line(8, by0, 4, by1, 'D', 3.0)
    lay.line(70, by0, 74, by1, 'D', 1.6)
    # the approved plan pinned on the board (its own little trapezoid)
    sheet = [(14, by0 + 2), (56, by0 + 2), (58, by1 - 2), (12, by1 - 2)]
    m, sx0, sy0 = lay.poly(sheet, 'P', 6.0, hgt=0.4)
    lay.paint_normal(m, sx0, sy0, (0.0, 0.55, 0.83))
    for yy, t in ((by0 + 4, 3.4), (by1 - 5, 3.4), (by0 + 12, 4.2)):
        f = (yy - by0) / (by1 - by0)
        lay.hline(int(round(16 - 2 * f)), yy, int(round(39 + 4 * f)), 'B', t, flat=True)
    for xx in (17, 29, 41, 52):
        lay.line(xx, by0 + 4, xx - 1, by1 - 5, 'B', 3.6)
    # hatched closed supply wing (right end of the plan)
    for k in range(0, 9, 2):
        lay.line(44 + k, by0 + 11, 44 + k + 4, by0 + 5, 'B', 3.0)
    lay.rect(43, by0 + 4, 1, 8, 'B', 2.6, flat=True)
    for (tx, ty) in ((13, by0 + 1), (55, by0 + 1), (11, by1 - 3), (57, by1 - 3)):
        tape(lay, tx, ty)
    # set square (transparent) + a pencil
    lay.polyline([(46, by0 + 13), (55, by0 + 20), (46, by0 + 20), (46, by0 + 13)], 'B', 5.4)
    lay.line(22, by0 + 18, 31, by0 + 16, 'R', 1.0)
    lay.px(31, by0 + 16, 'D', 6.0)
    # parallel rule with its guide cords
    lay.rect(6, by0 + 14, 66, 2, 'D', 5.0, hgt=0.6, flat=True)
    lay.rect(6, by0 + 14, 66, 1, 'D', 6.6, hgt=0.65, flat=True)
    lay.rect(6, by0 + 16, 66, 1, 'B', 5.4, hgt=0.5, flat=True)
    lay.line(6, by0 + 15, 5, by1, 'P', 3.0)
    lay.line(71, by0 + 15, 73, by1, 'P', 3.0)
    # board thickness + pencil trough
    lay.rect(3, by1, 72, 2, 'D', 2.6, hgt=0.6, flat=True)
    lay.rect(3, by1 + 2, 72, 2, 'D', 4.0, hgt=0.75, flat=True)
    lay.rect(3, by1 + 2, 72, 1, 'D', 5.6, hgt=0.8, flat=True)
    lay.rect(3, by1 + 4, 72, 1, 'D', 1.2, hgt=0.3, flat=True)
    for (x, c, t) in ((12, 'G', 4.0), (16, 'D', 6.0), (20, 'A', 4.0)):
        lay.rect(x, by1 + 1, 6, 1, c, t, hgt=0.85, flat=True)
    lay.rect(28, by1 + 1, 3, 1, 'P', 6.0, hgt=0.85, flat=True)
    # drafting tube leaning on the right leg + coffee cup on the trough end
    for k, t in ((0, 2.4), (1, 3.6), (2, 2.0)):
        lay.line(62 + k, by1 + 7, 66 + k, 74, 'B', t)
    lay.rect(61, by1 + 5, 5, 3, 'B', 4.6, hgt=0.6, flat=True)
    lay.rect(66, by1 - 3, 4, 5, 'P', 5.6, hgt=0.7, flat=True)
    lay.px(70, by1 - 2, 'P', 4.6); lay.px(70, by1 - 1, 'P', 4.6)
    lay.rect(66, by1 - 3, 4, 1, 'D', 1.0, flat=True)
    # articulated lamp: clamp top-right, two 2-px arms with spring, conical shade over the sheet
    lay.rect(67, by0 - 3, 5, 5, 'W', 3.0, hgt=0.7, flat=True)
    lay.rect(67, by0 - 3, 5, 1, 'W', 5.4, hgt=0.75, flat=True)
    for (ax, ay, bx, by_, t) in ((69, by0 - 3, 61, 3, 4.8), (70, by0 - 3, 62, 3, 2.6)):
        lay.line(ax, ay, bx, by_, 'W', t)
    for k in range(5, by0 - 4, 3):
        f = (k - 3) / (by0 - 6)
        lay.px(int(round(62 + 8 * f)) + 1, k, 'W', 6.6)                         # spring glints
    lay.ellipse(61.5, 3.5, 2.0, 2.0, 'W', 3.6, hgt=0.85, flat=True)            # elbow joint
    lay.px(61, 2, 'W', 6.4)
    lay.line(60, 4, 54, 9, 'W', 4.8)
    lay.line(61, 5, 55, 10, 'W', 2.6)
    shade = [(50, 9), (56, 8), (60, 16), (45, 18)]
    lay.poly(shade, 'W', 3.0, hgt=0.85)
    lay.line(50, 9, 45, 18, 'W', 5.6)                                           # lit left flank
    lay.line(56, 8, 60, 16, 'W', 1.4)
    lay.line(45, 18, 60, 16, 'A', 6.0, emis=True)                               # glowing rim
    lay.line(46, 19, 59, 17, 'A', 5.0, emis=True)
    lay.rect(51, 18, 4, 2, 'A', 6.0, emis=True, flat=True)                      # bulb
    p.lights.append({'name': 'lamp_konrad', 'pos': (X(284) + 53, p.y + 20), 'kind': 'warm', 'energy': 1.45,
                     'radius': 118, 'height': 22, 'cone': (-0.25, 1.0, -0.05)})
    return p


def stool_konrad():
    p = Prop('stool_konrad', X(362), 295, 16, 30, 'tall drafting stool pushed aside')
    lay = p.lay
    lay.ellipse(8, 2.5, 7.0, 2.4, 'D', 4.4, hgt=0.6, flat=True)
    lay.rect(2, 3, 13, 2, 'D', 2.6, hgt=0.5, flat=True)
    lay.rect(3, 1, 9, 1, 'D', 6.0, hgt=0.7, flat=True)
    for (a, b) in (((4, 5), (1, 29)), ((12, 5), (15, 29)), ((8, 5), (8, 28))):
        lay.line(a[0], a[1], b[0], b[1], 'D', 2.6)
        lay.line(a[0] + 1, a[1], b[0] + 1, b[1], 'D', 1.4)
    lay.rect(2, 19, 13, 1, 'W', 5.0, hgt=0.5, flat=True)                       # foot ring
    return p


def drafting_covered():
    p = Prop('drafting_covered', X(172), 293, 66, 74, "absent colleague's board under a dust sheet (obs_photo)")
    lay = p.lay
    iron_trestle(lay, 12, 50, 50, 73)
    # dust sheet draped over the board: hem waves, vertical folds
    top, hem = 22, 60
    pts = [(2, top + 2), (8, top - 1), (58, top - 1), (63, top + 3), (64, hem - 4)]
    rng = np.random.default_rng(4)
    for x in range(64, 1, -4):
        pts.append((x, hem + int(round(2 * math.sin(x * 0.45))) + int(rng.integers(0, 2))))
    pts.append((1, hem - 6))
    lay.poly(pts, 'P', 1.6, hgt=0.45)
    # folds (light ridge + dark valley)
    for fx in (9, 19, 31, 42, 54):
        lay.line(fx, top + 3, fx + int(rng.integers(-2, 3)), hem - 1, 'P', 2.6)
        lay.line(fx + 2, top + 5, fx + 2 + int(rng.integers(-2, 3)), hem, 'P', 0.6)
    lay.rect(4, top - 1, 56, 1, 'P', 3.0, flat=True)
    lay.rect(2, top, 1, hem - top - 6, 'P', 2.8, flat=True)
    # the office photo leaning on the sheet (obs_photo): a small sepia print, white border,
    # five colleagues in a row -- one face scratched out with a needle (pale jagged mark)
    fx, fy = 21, top + 7
    lay.rect(fx - 1, fy - 1, 16, 13, 'D', 1.6, hgt=0.75, flat=True)            # dark frame
    lay.rect(fx - 1, fy - 1, 16, 1, 'D', 3.4, hgt=0.8, flat=True)
    lay.rect(fx, fy, 14, 11, 'P', 6.0, hgt=0.7, flat=True)                     # white border
    lay.rect(fx + 1, fy + 1, 12, 8, 'P', 3.0, hgt=0.65, flat=True)             # sepia image
    lay.rect(fx + 1, fy + 1, 12, 3, 'P', 4.0, hgt=0.65, flat=True)             # pale background
    for k, hx in enumerate((fx + 2, fx + 4, fx + 6, fx + 8, fx + 10)):
        lay.rect(hx, fy + 5, 2, 4, 'P', 1.0 if k % 2 else 0.6, flat=True)      # dark suits
        lay.px(hx, fy + 4, 'P', 5.0)                                            # faces
        lay.px(hx + 1, fy + 4, 'P', 4.4)
    # the scratched face (third from the right)
    sx = fx + 6
    for (dx, dy) in ((0, 3), (1, 4), (0, 4), (1, 3), (-1, 5), (2, 2)):
        lay.px(sx + dx, fy + dy, 'P', 7.0)
    lay.rect(fx + 4, fy + 11, 6, 1, 'D', 1.0, flat=True)                       # stand shadow
    # folded lamp, switched off
    lay.rect(58, top - 4, 3, 4, 'W', 2.4, hgt=0.6, flat=True)
    lay.line(59, top - 4, 50, top - 12, 'W', 3.6)
    lay.poly([(46, top - 13), (52, top - 14), (53, top - 9), (45, top - 8)], 'W', 2.2, hgt=0.6)
    lay.line(45, top - 8, 53, top - 9, 'W', 1.2)
    return p


def typist_desk():
    T = 36                     # desk top (local y)
    p = Prop('typist_desk', X(446), 293, 60, T + 30, 'typist desk: typewriter, telephone, gooseneck lamp, chair')
    lay = p.lay
    # desk body: two pedestals + kneehole
    lay.rect(2, T, 56, 3, 'D', 5.0, hgt=0.6, flat=True)
    lay.rect(2, T, 56, 1, 'D', 6.4, hgt=0.65, flat=True)
    lay.rect(3, T + 3, 54, 26, 'D', 2.6, hgt=0.4, flat=True)
    for (x0, x1) in ((4, 20), (40, 56)):
        for k in range(3):
            yy = T + 5 + k * 8
            lay.rect(x0, yy, x1 - x0, 7, 'D', 3.2, hgt=0.5, flat=True)
            lay.rect(x0, yy, x1 - x0, 1, 'D', 4.4, hgt=0.55, flat=True)
            lay.rect(x0 + (x1 - x0) // 2 - 1, yy + 3, 3, 1, 'A', 3.6, hgt=0.7, flat=True)
    lay.rect(21, T + 4, 18, 22, 'D', 1.2, hgt=0.0, flat=True)            # kneehole shadow
    lay.rect(3, T + 27, 54, 2, 'D', 1.4, hgt=0.3, flat=True)
    # typewriter
    lay.poly([(18, T), (38, T), (35, T - 9), (21, T - 9)], 'I', 1.6, hgt=0.7)
    lay.rect(19, T - 11, 18, 3, 'I', 2.0, hgt=0.8, flat=True)             # carriage
    lay.rect(18, T - 11, 20, 1, 'W', 6.4, hgt=0.85, flat=True)            # chrome bar
    lay.rect(16, T - 10, 2, 2, 'W', 5.0, hgt=0.8, flat=True)              # return lever
    for k in range(5):
        for j in range(3):
            lay.px(21 + k * 3 + j % 2, T - 6 + j * 2, 'W', 4.6 if (k + j) % 2 else 3.6)
    lay.rect(22, T - 21, 12, 10, 'P', 6.0, hgt=0.6, flat=True)            # sheet in the platen
    for k in range(4):
        lay.hline(23, T - 19 + k * 2, 7 + (k % 2) * 2, 'I', 2.0, flat=True)
    # telephone (black bakelite)
    lay.rect(44, T - 5, 10, 5, 'I', 1.6, hgt=0.7, flat=True)
    lay.ellipse(48.5, T - 3, 2.5, 1.6, 'W', 5.0, hgt=0.75, flat=True)    # dial
    lay.rect(43, T - 8, 12, 2, 'I', 2.0, hgt=0.8, flat=True)              # handset
    lay.rect(43, T - 8, 12, 1, 'W', 4.6, hgt=0.85, flat=True)
    # stack of files
    for k, t in enumerate((4.6, 3.6, 5.0, 4.0)):
        lay.rect(4, T - 2 - k * 2, 12, 2, 'P', t, hgt=0.6, flat=True)
    # gooseneck lamp standing on the files, shade toward the typewriter
    lay.rect(4, T - 10, 6, 2, 'I', 2.0, hgt=0.6, flat=True)
    lay.polyline([(7, T - 10), (6, T - 19), (9, T - 27), (14, T - 28)], 'W', 3.4)
    shade = [(11, T - 31), (18, T - 30), (19, T - 25), (12, T - 25)]
    lay.poly(shade, 'G', 2.6, hgt=0.7)
    lay.line(11, T - 31, 18, T - 30, 'G', 4.4)
    lay.line(12, T - 25, 19, T - 25, 'A', 6.0, emis=True)
    lay.rect(14, T - 24, 3, 1, 'A', 5.0, emis=True, flat=True)
    p.lights.append({'name': 'lamp_typist', 'pos': (X(446) + 15, p.y + T - 23), 'kind': 'warm', 'energy': 0.8,
                     'radius': 88, 'height': 18, 'cone': (0.3, 1.0, -0.1)})
    # chair seen from behind (pushed in)
    lay.rect(24, T + 4, 12, 9, 'D', 3.0, hgt=0.7, flat=True)             # backrest
    lay.rect(24, T + 4, 12, 1, 'D', 5.0, hgt=0.75, flat=True)
    lay.rect(25, T + 6, 10, 1, 'D', 2.0, hgt=0.6, flat=True)
    lay.rect(25, T + 13, 2, 16, 'D', 2.2, hgt=0.5, flat=True)
    lay.rect(33, T + 13, 2, 16, 'D', 2.2, hgt=0.5, flat=True)
    lay.rect(23, T + 18, 14, 2, 'D', 3.6, hgt=0.6, flat=True)            # seat edge
    return p


def plan_basket():
    p = Prop('plan_basket', X(612), 309, 20, 38, 'wicker stand with rolled plans (in front of the walk line)')
    lay = p.lay
    # wicker body
    for y in range(16, 37):
        for x in range(3, 17):
            t = 3.0 + (0.8 if ((x // 2 + y // 2) % 2 == 0) else 0.0)
            lay.px(x, y, 'D', t, hgt=0.5)
    lay.rect(2, 15, 16, 2, 'D', 4.6, hgt=0.6, flat=True)
    lay.rect(2, 15, 16, 1, 'D', 5.6, hgt=0.65, flat=True)
    lay.rect(3, 36, 14, 1, 'D', 1.4, hgt=0.3, flat=True)
    lay.rect(16, 17, 1, 19, 'D', 1.6, hgt=0.4, flat=True)
    # rolls sticking out
    rolls = [(5, 0, 'P', 4.4), (8, 4, 'B', 3.6), (11, 2, 'P', 5.0), (14, 7, 'P', 3.8), (7, 9, 'P', 5.4)]
    for (x, top, rm, t) in rolls:
        lay.rect(x - 1, top + 1, 3, 16 - top, rm, t, hgt=0.6, flat=True)
        lay.rect(x - 1, top + 1, 1, 16 - top, rm, t + 1.0, hgt=0.65, flat=True)
        lay.rect(x + 1, top + 1, 1, 16 - top, rm, t - 1.2, hgt=0.55, flat=True)
        lay.rect(x - 1, top, 3, 1, rm, t + 1.4, hgt=0.7, flat=True)
        lay.px(x, top + 1, 'D', 1.0)
    return p


def ladder():
    p = Prop('ladder', X(652), 291, 26, 142, 'rolling library ladder hooked on the shelf rail')
    lay = p.lay
    h = p.h
    for k in range(h):
        f = k / (h - 1)
        xl = int(round(4 - 2 * f))
        xr = int(round(20 + 2 * f))
        lay.rect(xl, k, 2, 1, 'D', 3.6, hgt=0.6, flat=True)
        lay.px(xl, k, 'D', 5.0, hgt=0.65)
        lay.rect(xr, k, 2, 1, 'D', 3.2, hgt=0.6, flat=True)
        lay.px(xr + 1, k, 'D', 1.8, hgt=0.55)
    for y in range(8, h - 6, 10):
        f = y / (h - 1)
        xl = int(round(4 - 2 * f)) + 2
        xr = int(round(20 + 2 * f))
        lay.rect(xl, y, xr - xl, 2, 'D', 3.4, hgt=0.55, flat=True)
        lay.rect(xl, y, xr - xl, 1, 'D', 5.2, hgt=0.6, flat=True)
        lay.rect(xl, y + 2, xr - xl, 1, 'D', 1.0, hgt=0.2, flat=True)
    # hooks at the top + wheels at the bottom
    for x in (3, 20):
        lay.rect(x, 0, 3, 2, 'A', 3.4, hgt=0.8, flat=True)
        lay.px(x + (2 if x < 10 else 0), 2, 'A', 2.4)
    for x in (1, 22):
        lay.ellipse(x + 1.5, h - 2.5, 2.0, 2.0, 'I', 1.4, hgt=0.6, flat=True)
        lay.px(x + 1, h - 3, 'W', 5.0)
    return p


def flat_file():
    p = Prop('flat_file', X(790), 293, 108, 50, 'plan chest; the drawer with the archived draft is pulled out (plan_b)')
    lay = p.lay
    top = 8
    # carcass
    lay.rect(2, top, 104, 50 - top - 1, 'D', 2.6, hgt=0.4, flat=True)
    lay.rect(1, top - 2, 106, 3, 'D', 4.6, hgt=0.6, flat=True)
    lay.rect(1, top - 2, 106, 1, 'D', 6.0, hgt=0.65, flat=True)
    lay.rect(2, 45, 104, 4, 'D', 1.4, hgt=0.3, flat=True)
    dh = 5
    for k in range(7):
        yy = top + 2 + k * dh
        lay.rect(4, yy, 100, dh - 1, 'D', 3.2, hgt=0.5, flat=True)
        lay.rect(4, yy, 100, 1, 'D', 4.2, hgt=0.55, flat=True)
        lay.rect(4, yy + dh - 1, 100, 1, 'D', 1.2, hgt=0.2, flat=True)
        for hx in (18, 82):
            lay.rect(hx, yy + 2, 6, 1, 'A', 3.4, hgt=0.7, flat=True)
        lay.rect(47, yy + 1, 12, 2, 'P', 4.6, hgt=0.6, flat=True)
        lay.px(49, yy + 1, 'I', 2.0); lay.px(52, yy + 1, 'I', 2.0); lay.px(55, yy + 1, 'I', 2.0)
    # third drawer pulled out: its front moves forward (down on screen), paper visible inside
    k = 2
    yy = top + 2 + k * dh
    lay.rect(3, yy - 1, 102, 4, 'P', 5.6, hgt=0.7, flat=True)                # paper in the drawer
    lay.rect(3, yy - 1, 102, 1, 'P', 6.4, hgt=0.75, flat=True)
    for j in range(6, 98, 9):
        lay.rect(3 + j, yy, 5, 1, 'B', 4.0, flat=True)                         # diazo lines
    lay.rect(70, yy - 3, 16, 3, 'P', 6.0, hgt=0.8, flat=True)                  # a corner lifted
    lay.line(70, yy - 3, 85, yy - 3, 'B', 4.4)
    lay.rect(2, yy + 3, 104, dh, 'D', 3.6, hgt=0.75, flat=True)                # drawer front (forward)
    lay.rect(2, yy + 3, 104, 1, 'D', 5.0, hgt=0.8, flat=True)
    lay.rect(2, yy + 3 + dh, 104, 1, 'D', 0.6, hgt=0.2, flat=True)
    for hx in (18, 82):
        lay.rect(hx, yy + 5, 6, 1, 'A', 4.4, hgt=0.9, flat=True)
    lay.rect(47, yy + 4, 12, 2, 'P', 5.4, hgt=0.85, flat=True)
    # on top: stacked sheets, magnifier, brass weight
    for k2, t in enumerate((5.0, 4.0, 5.6)):
        lay.rect(10 + k2 * 3, top - 4 - k2, 34, 2, 'P', t, hgt=0.7, flat=True)
    lay.ellipse(66, top - 4, 4.0, 2.0, 'A', 3.0, hgt=0.8, flat=True)
    lay.ellipse(66, top - 4, 3.0, 1.2, 'B', 5.0, hgt=0.85, flat=True)
    lay.line(70, top - 3, 75, top - 2, 'D', 2.0)
    lay.rect(88, top - 5, 4, 3, 'A', 3.6, hgt=0.8, flat=True)
    lay.px(89, top - 6, 'A', 5.0)
    return p


def card_catalogue():
    p = Prop('card_catalogue', X(990), 292, 46, 62, 'card catalogue cabinet with a drawer pulled out')
    lay = p.lay
    top = 8
    lay.rect(1, top, 44, 38, 'D', 2.4, hgt=0.4, flat=True)
    lay.rect(0, top - 2, 46, 3, 'D', 4.4, hgt=0.6, flat=True)
    lay.rect(0, top - 2, 46, 1, 'D', 5.8, hgt=0.65, flat=True)
    for r in range(6):
        for c in range(4):
            x, y = 2 + c * 11, top + 2 + r * 6
            lay.rect(x, y, 10, 5, 'D', 3.4, hgt=0.5, flat=True)
            lay.rect(x, y, 10, 1, 'D', 4.4, hgt=0.55, flat=True)
            lay.rect(x + 3, y + 1, 4, 2, 'P', 4.6, hgt=0.6, flat=True)
            lay.px(x + 4, y + 3, 'A', 4.0, hgt=0.7)
            lay.px(x + 5, y + 3, 'A', 3.0, hgt=0.7)
    # pulled-out drawer with index cards
    x, y = 2 + 2 * 11, top + 2 + 2 * 6
    lay.rect(x - 1, y - 3, 12, 3, 'P', 5.6, hgt=0.7, flat=True)
    for k in range(0, 11, 2):
        lay.px(x - 1 + k, y - 3, 'P', 4.0)
    lay.rect(x - 1, y, 12, 6, 'D', 3.8, hgt=0.75, flat=True)
    lay.rect(x - 1, y, 12, 1, 'D', 5.0, hgt=0.8, flat=True)
    lay.rect(x + 2, y + 2, 4, 2, 'P', 5.4, hgt=0.8, flat=True)
    lay.px(x + 3, y + 4, 'A', 5.0)
    # stand with legs
    lay.rect(2, 46, 42, 3, 'D', 3.0, hgt=0.5, flat=True)
    lay.rect(2, 46, 42, 1, 'D', 4.4, hgt=0.55, flat=True)
    for lx in (3, 40):
        lay.rect(lx, 49, 3, 13, 'D', 2.6, hgt=0.5, flat=True)
        lay.rect(lx, 49, 1, 13, 'D', 3.8, hgt=0.55, flat=True)
    lay.rect(6, 56, 34, 1, 'D', 2.0, hgt=0.4, flat=True)
    # card boxes on top
    lay.rect(6, top - 7, 12, 5, 'P', 3.6, hgt=0.6, flat=True)
    lay.rect(6, top - 7, 12, 1, 'P', 4.6, hgt=0.65, flat=True)
    lay.rect(20, top - 6, 9, 4, 'D', 3.4, hgt=0.6, flat=True)
    for k in range(7):
        lay.px(7 + k, top - 8, 'P', 5.4)
    return p


def light_table():
    p = Prop('light_table', X(1136), 294, 84, 50, 'light table for overlaying drawings (overlay_table)')
    lay = p.lay
    gy0, gy1 = 10, 21
    # frame + glowing frosted glass top (seen from above, tilted toward the viewer)
    lay.rect(1, gy0 - 2, 82, gy1 - gy0 + 4, 'W', 5.0, hgt=0.7, flat=True)
    lay.rect(1, gy0 - 2, 82, 1, 'W', 6.6, hgt=0.75, flat=True)
    glass = np.zeros((gy1 - gy0, 76), bool); glass[:] = True
    tt = np.linspace(9.6, 10.4, gy1 - gy0)[:, None] + np.zeros((1, 76))
    lay.put(glass, 4, gy0, 'W', tt, emis=True)
    # two drawings on the glass: the lower sheet's lines show through the upper one
    lay.rect(10, gy0 + 1, 40, gy1 - gy0 - 2, 'P', 7.0, emis=True, flat=True)
    lay.rect(26, gy0 + 2, 44, gy1 - gy0 - 3, 'P', 6.0, emis=True, flat=True)
    for k in range(3):
        lay.hline(12, gy0 + 3 + k * 3, 30, 'B', 5.0, emis=True, flat=True)
        lay.hline(28, gy0 + 4 + k * 3, 38, 'B', 4.0, emis=True, flat=True)
    lay.vline(30, gy0 + 2, gy1 - gy0 - 4, 'B', 4.0, emis=True, flat=True)
    lay.vline(56, gy0 + 3, gy1 - gy0 - 5, 'B', 4.0, emis=True, flat=True)
    lay.rect(44, gy0 + 5, 12, 2, 'B', 3.0, emis=True, flat=True)                # the corridor band
    # weights / pins
    for x in (11, 48, 69):
        lay.rect(x, gy0 + 1, 2, 2, 'A', 3.0, hgt=0.9, flat=True)
    # front edge of the top (lit from the glass)
    lay.rect(1, gy1 + 1, 82, 2, 'W', 6.0, hgt=0.7, flat=True)
    lay.rect(1, gy1 + 3, 82, 1, 'W', 3.0, hgt=0.5, flat=True)
    # cabinet body
    lay.rect(4, gy1 + 4, 76, 18, 'W', 3.6, hgt=0.5, flat=True)
    lay.rect(4, gy1 + 4, 76, 1, 'W', 5.4, hgt=0.55, flat=True)
    lay.rect(4, gy1 + 4, 1, 18, 'W', 4.6, hgt=0.55, flat=True)
    for x in range(10, 74, 4):
        lay.rect(x, gy1 + 10, 2, 7, 'W', 2.2, hgt=0.3, flat=True)
    lay.rect(66, gy1 + 7, 6, 4, 'W', 2.0, hgt=0.6, flat=True)                   # switch box
    lay.px(68, gy1 + 8, 'A', 6.0, emis=True)
    # legs
    for x in (6, 74):
        lay.rect(x, gy1 + 22, 3, 50 - gy1 - 22, 'W', 3.0, hgt=0.5, flat=True)
        lay.rect(x, gy1 + 22, 1, 50 - gy1 - 22, 'W', 5.0, hgt=0.55, flat=True)
    lay.rect(8, 44, 68, 2, 'W', 2.6, hgt=0.4, flat=True)
    p.lights.append({'name': 'light_table', 'pos': (X(1136) + 42, p.y + gy0 + 3), 'kind': 'white', 'energy': 1.0,
                     'radius': 96, 'height': 6})
    return p


def counter():
    ct = 26                    # counter top front edge (local y); lamp and props rise above it
    H = ct + 27                # front 26 px ~ 1.05 m
    p = Prop('counter', X(1334), 292, 160, H, "Emil's issue counter: banker's lamp, stamps, card files")
    lay = p.lay
    # counter top surface seen from above + brass edge
    lay.rect(0, ct - 4, 160, 4, 'D', 4.4, hgt=0.6, flat=True)
    lay.rect(0, ct - 4, 160, 1, 'D', 3.0, hgt=0.55, flat=True)
    top_m = np.zeros((4, 160), bool); top_m[:] = True
    lay.paint_normal(top_m, 0, ct - 4, (0.0, 0.9, 0.44))
    lay.rect(0, ct, 160, 1, 'A', 3.4, hgt=0.75, flat=True)
    # front with raised panels
    lay.rect(1, ct + 1, 158, 26, 'D', 2.6, hgt=0.4, flat=True)
    for k in range(5):
        x = 5 + k * 31
        lay.rect(x, ct + 3, 27, 17, 'D', 2.0, hgt=0.3, flat=True)
        lay.rect(x + 2, ct + 5, 23, 13, 'D', 3.0, hgt=0.45, flat=True)
        lay.rect(x + 2, ct + 5, 23, 1, 'D', 4.0, hgt=0.5, flat=True)
        lay.rect(x + 2, ct + 17, 23, 1, 'D', 1.6, hgt=0.35, flat=True)
    lay.rect(1, ct + 22, 158, 4, 'D', 1.2, hgt=0.3, flat=True)               # kick plate
    lay.rect(1, ct + 22, 158, 1, 'D', 2.6, hgt=0.35, flat=True)
    # stamp carousel with rubber stamps
    sx = 14
    lay.rect(sx, ct - 6, 18, 2, 'D', 3.0, hgt=0.7, flat=True)
    lay.rect(sx + 8, ct - 14, 2, 8, 'A', 3.0, hgt=0.75, flat=True)
    lay.rect(sx + 1, ct - 15, 16, 1, 'D', 3.6, hgt=0.75, flat=True)
    for k in range(5):
        x = sx + 1 + k * 3 + (k > 2)
        lay.rect(x, ct - 13, 2, 3, 'D', 4.6, hgt=0.8, flat=True)               # handles
        lay.px(x, ct - 14, 'D', 6.0)
        lay.rect(x, ct - 10, 2, 2, 'I', 1.4, hgt=0.7, flat=True)               # rubber
    lay.rect(sx + 21, ct - 6, 9, 3, 'I', 1.6, hgt=0.7, flat=True)              # ink pad
    lay.rect(sx + 22, ct - 6, 7, 1, 'R', 1.0, hgt=0.75, flat=True)
    # card file box with index cards standing up
    lay.rect(46, ct - 9, 18, 6, 'D', 3.2, hgt=0.7, flat=True)
    lay.rect(46, ct - 9, 18, 1, 'D', 4.6, hgt=0.75, flat=True)
    for k in range(16):
        lay.px(47 + k, ct - 11 + (k % 3 == 0), 'P', 5.0 if k % 2 else 4.2)
        lay.px(47 + k, ct - 10, 'P', 4.6)
    lay.rect(52, ct - 6, 5, 2, 'P', 5.0, hgt=0.8, flat=True)
    # hand bell
    lay.ellipse(84.5, ct - 6, 3.0, 2.2, 'A', 3.6, hgt=0.8, flat=True)
    lay.rect(84, ct - 10, 1, 3, 'A', 4.6, hgt=0.85, flat=True)
    lay.px(83, ct - 7, 'A', 5.6)
    # open register book
    lay.poly([(92, ct - 4), (106, ct - 5), (120, ct - 4), (120, ct - 2), (92, ct - 2)], 'P', 5.4, hgt=0.7)
    lay.line(106, ct - 5, 106, ct - 2, 'P', 3.0)
    for k in range(3):
        lay.hline(94, ct - 4 + k, 10, 'I', 2.6 if k % 2 else 3.0, flat=True)
    lay.rect(122, ct - 3, 6, 1, 'I', 2.0, hgt=0.75, flat=True)                # pen
    # banker's lamp: brass base, arm, green glass shade (glowing underside)
    bx = 128
    lay.rect(bx - 4, ct - 5, 10, 2, 'A', 2.8, hgt=0.8, flat=True)
    lay.rect(bx - 4, ct - 5, 10, 1, 'A', 4.4, hgt=0.85, flat=True)
    lay.rect(bx, ct - 13, 2, 8, 'A', 3.2, hgt=0.85, flat=True)
    lay.px(bx, ct - 13, 'A', 5.0)
    shade_y = ct - 19
    lay.poly([(bx - 9, shade_y + 5), (bx + 10, shade_y + 5), (bx + 8, shade_y), (bx - 7, shade_y)], 'G', 3.0,
             hgt=0.85)
    lay.rect(bx - 7, shade_y, 16, 1, 'G', 6.0, hgt=0.9, flat=True, emis=True)
    lay.rect(bx - 8, shade_y + 2, 18, 1, 'G', 4.4, hgt=0.88, flat=True, emis=True)
    lay.rect(bx - 9, shade_y + 5, 20, 1, 'G', 5.0, flat=True, emis=True)
    lay.rect(bx - 6, shade_y + 6, 14, 1, 'A', 6.0, flat=True, emis=True)       # bulb glow under the shade
    lay.rect(bx - 2, shade_y + 6, 1, 2, 'A', 5.0, flat=True)                   # pull chain
    p.lights.append({'name': 'lamp_emil', 'pos': (X(1334) + bx + 1, p.y + shade_y + 7), 'kind': 'green',
                     'energy': 1.7, 'radius': 96, 'height': -3, 'wrap_add': 0.06})
    return p


def bench():
    p = Prop('bench', X(1296), 291, 46, 24, 'waiting bench; a forgotten hat and a newspaper')
    lay = p.lay
    for k in range(3):
        lay.rect(2, 1 + k * 3, 42, 2, 'D', 3.4, hgt=0.5, flat=True)
        lay.rect(2, 1 + k * 3, 42, 1, 'D', 4.6, hgt=0.55, flat=True)
    lay.rect(2, 11, 42, 3, 'D', 4.0, hgt=0.6, flat=True)
    lay.rect(2, 11, 42, 1, 'D', 5.4, hgt=0.65, flat=True)
    lay.rect(2, 14, 42, 1, 'D', 1.4, hgt=0.3, flat=True)
    for x in (4, 40):
        lay.rect(x, 0, 2, 24, 'W', 2.2, hgt=0.6, flat=True)
        lay.rect(x, 0, 1, 24, 'W', 4.0, hgt=0.65, flat=True)
        lay.rect(x - 1, 22, 4, 2, 'W', 2.0, hgt=0.5, flat=True)
    # newspaper + hat
    lay.rect(10, 9, 12, 2, 'P', 5.0, hgt=0.7, flat=True)
    lay.rect(10, 9, 12, 1, 'P', 5.8, hgt=0.75, flat=True)
    lay.hline(12, 10, 7, 'I', 2.6, flat=True)
    lay.rect(28, 8, 9, 2, 'I', 2.0, hgt=0.7, flat=True)
    lay.rect(30, 5, 5, 3, 'I', 2.2, hgt=0.75, flat=True)
    lay.px(30, 5, 'W', 4.4)
    return p


def build_all():
    import env_berlin_hall as EH
    import env_berlin_library as ELB
    return (EH.props_hall(Prop) + ELB.props_library(Prop) +
            [coat_stand(), drafting_covered(), drafting_konrad(), stool_konrad(), typist_desk(), plan_basket(),
             ladder(), flat_file(), card_catalogue(), light_table(), counter(), bench()])


def bake_prop(p: Prop, lights, room_fields=None, shaft_air=None):
    F = kit.light_fields(p.lay, lights, origin=(p.x, p.y))
    if shaft_air is not None:
        sub = kit.sub_fields({'cold': shaft_air}, p.x, p.y, p.w, p.h)['cold']
        F['cold'] += (sub ** 0.85) * 0.62
    p.lay.resolve(F)
    return p
