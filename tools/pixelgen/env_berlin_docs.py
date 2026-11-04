"""env_berlin_docs -- inspect/puzzle documents for M1 (pixel art 1:1, shown at 3x in the UI).

berlin_plan_a.png   approved public floor plan: the supply wing is closed off.
berlin_plan_b.png   older archived draft: the corridor continues behind a second wall; pencil 'C-17'.
berlin_plan_*_lines.png   the same drawings without paper (transparent) for the overlay UI.
berlin_plans.json   cell size, grid, landmark cells, solution, hidden-corridor rects.
berlin_emil_note.png      Emil's handwritten archive slip with 'C-17'.

Geometry (cells of 16 px, sheet 18 x 12 cells = 288 x 192 px):
  plan A  staircase anchor (4,2) [2x2], chimney (9,7) [1x1]
  plan B  staircase anchor (2,3),        chimney (7,8)
  B shifted by (+2, -1) cells, rotation 0  ->  landmarks coincide (canonical pz_blueprint solution).
"""
from __future__ import annotations

import json
import math
import os

import numpy as np

import env_berlin_kit as kit
import pg

R = kit.archive_ramps()
CELL = 16
GW, GH = 18, 12
W, H = GW * CELL, GH * CELL
SOLUTION = {'rotation_steps': 0, 'offset_x': 2, 'offset_y': -1}
DX, DY = -SOLUTION['offset_x'], -SOLUTION['offset_y']     # A-cell -> B-cell transform

# ---- building in plan-A cell coordinates (grid lines)
BLD = (3, 1, 16, 9)                 # outer wall rectangle x0, y0, x1, y1 (grid lines)
CORR_Y = (5, 6)                     # corridor between grid lines 5 and 6
WING_X = 12                         # supply wing starts at this grid line (closed in plan A)
STAIR_A = (4, 2)                    # anchor cell, 2x2
CHIM_A = (9, 7)                     # anchor cell, 1x1
STAIR_B = (STAIR_A[0] + DX, STAIR_A[1] + DY)
CHIM_B = (CHIM_A[0] + DX, CHIM_A[1] + DY)


class Sheet:
    """A document drawn in tone space; .ink marks drawing pixels (for the line-only export)."""

    def __init__(self, w, h, name):
        self.lay = kit.MLayer(w, h, R, name)
        self.ink = np.zeros((h, w), bool)
        self.w, self.h = w, h

    def ink_px(self, x, y, ramp, tone):
        x, y = int(x), int(y)
        if 0 <= x < self.w and 0 <= y < self.h:
            self.lay.px(x, y, ramp, tone, flat=True)
            self.ink[y, x] = True

    def ink_rect(self, x, y, w, h, ramp, tone):
        x, y, w, h = int(x), int(y), int(w), int(h)
        x0, y0, x1, y1 = max(0, x), max(0, y), min(self.w, x + w), min(self.h, y + h)
        if x1 > x0 and y1 > y0:
            self.lay.rect(x0, y0, x1 - x0, y1 - y0, ramp, tone, flat=True)
            self.ink[y0:y1, x0:x1] = True

    def ink_line(self, x0, y0, x1, y1, ramp, tone, dash=None):
        pts = kit.bres(x0, y0, x1, y1)
        for i, (x, y) in enumerate(pts):
            if dash and (i % (dash[0] + dash[1])) >= dash[0]:
                continue
            self.ink_px(x, y, ramp, tone)

    def ink_mask(self, m, x0, y0, ramp, tone):
        mh, mw = m.shape
        for yy in range(mh):
            for xx in range(mw):
                if m[yy, xx]:
                    self.ink_px(x0 + xx, y0 + yy, ramp, tone)


# =========================================================================== paper
def paper(sh: Sheet, seed, age=0.0, folds=False, torn=False, stains=0):
    lay = sh.lay
    w, h = sh.w, sh.h
    rng = np.random.default_rng(seed)
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    # base: off-white diazo paper, yellowing toward the edges
    edge = np.minimum(np.minimum(xx, w - 1 - xx), np.minimum(yy, h - 1 - yy))
    t = 6.2 - age * 0.9 - np.clip((14 - edge) / 14, 0, 1) * (0.9 + age * 0.8)
    t += (pg.value_noise(w, h, 40, seed, octaves=2) - 0.5) * (0.35 + age * 0.3)
    lay.put(np.ones((h, w), bool), 0, 0, 'P', t)
    # fibre speckles / foxing
    for _ in range(int(30 + age * 70)):
        x, y = int(rng.integers(0, w)), int(rng.integers(0, h))
        lay.px(x, y, 'P', float(rng.choice([4.0, 4.6])) - age * 0.4)
    for _ in range(int(age * 14)):                                    # foxing spots (2x2, soft)
        x, y = int(rng.integers(8, w - 8)), int(rng.integers(8, h - 8))
        lay.rect(x, y, 2, 2, 'P', 4.4 - age * 0.4)
    for _ in range(stains):
        cx, cy, r = rng.uniform(30, w - 30), rng.uniform(30, h - 30), rng.uniform(9, 14)
        for a in np.linspace(0, 2 * math.pi, 90):
            rr = r + rng.normal(0, 0.4)
            lay.shade_rect(int(cx + math.cos(a) * rr), int(cy + math.sin(a) * rr), 1, 1, -1.0)
        m, mx, my = lay.ellipse_mask(cx, cy, r - 1.5, r - 1.5)
        sub = np.zeros_like(m)
        sub[m] = True
        tt = np.where(m, -0.35, 0).astype(np.float32)
        lay.shade_field(tt, mx, my)
    if folds:
        fx = w // 2 + 3
        lay.shade_rect(fx, 0, 1, h, -1.0)
        lay.shade_rect(fx + 1, 0, 1, h, 0.6)
        fy = h // 2 - 5
        lay.shade_rect(0, fy, w, 1, -1.0)
        lay.shade_rect(0, fy + 1, w, 1, 0.6)
    if torn:
        # torn top-left corner (transparent) with a ragged edge
        for y in range(0, 22):
            lim = int(22 - y + rng.integers(-2, 2))
            if lim > 0:
                lay.erase(0, y, lim, 1)
                lay.px(lim, y, 'P', 3.4)
    lay.amb_field(np.zeros((h, w), np.float32))


def grid(sh: Sheet, ox=0, oy=0, tone=5.4):
    """Printed construction grid (Rastermass) every 16 px, dotted."""
    for gx in range(0, sh.w, CELL):
        for y in range(0, sh.h, 2):
            sh.lay.px(gx, y, 'B', tone, flat=True)
            sh.ink[y, gx] = True
    for gy in range(0, sh.h, CELL):
        for x in range(0, sh.w, 2):
            sh.lay.px(x, gy, 'B', tone, flat=True)
            sh.ink[gy, x] = True


# =========================================================================== drawing primitives
def gx(c):      # grid line -> pixel
    return c * CELL


def wall_h(sh, x0c, x1c, yc, thick=3, tone=2.6, gap=None):
    y = gx(yc) - thick // 2
    x0, x1 = gx(x0c) - thick // 2, gx(x1c) + thick // 2 + 1
    for x in range(x0, x1):
        if gap and gap[0] <= x < gap[1]:
            continue
        for k in range(thick):
            sh.ink_px(x, y + k, 'B', tone)


def wall_v(sh, xc, y0c, y1c, thick=3, tone=2.6, gap=None):
    x = gx(xc) - thick // 2
    y0, y1 = gx(y0c) - thick // 2, gx(y1c) + thick // 2 + 1
    for y in range(y0, y1):
        if gap and gap[0] <= y < gap[1]:
            continue
        for k in range(thick):
            sh.ink_px(x + k, y, 'B', tone)


def door_arc(sh, hx, hy, r, quadrant, tone=4.0):
    """Quarter-circle door swing; (hx,hy) hinge pixel; quadrant (sx, sy) in {-1,1}."""
    sx, sy = quadrant
    for a in np.linspace(0, math.pi / 2, 3 * r):
        sh.ink_px(hx + sx * round(math.cos(a) * r), hy + sy * round(math.sin(a) * r), 'B', tone)
    sh.ink_line(hx, hy, hx, hy + sy * r, 'B', tone)


def window_mark(sh, x0, x1, y, tone=3.6):
    """Window in a horizontal outer wall: wall gap with thin double line."""
    for x in range(x0, x1):
        sh.lay.px(x, y - 1, 'P', 6.0, flat=True)
        sh.lay.px(x, y + 1, 'P', 6.0, flat=True)
        sh.ink_px(x, y - 1, 'B', tone)
        sh.ink_px(x, y + 1, 'B', tone)
        sh.lay.px(x, y, 'P', 6.4, flat=True)
        sh.ink[y, x] = False


def staircase(sh, ax, ay, tone=3.0):
    """Landmark 1: straight-flight staircase over 2x2 cells (outline, treads, walking arrow)."""
    x0, y0 = gx(ax) + 2, gx(ay) + 2
    w, h = 2 * CELL - 4, 2 * CELL - 4
    sh.ink_rect(x0, y0, w, 1, 'B', tone); sh.ink_rect(x0, y0 + h - 1, w, 1, 'B', tone)
    sh.ink_rect(x0, y0, 1, h, 'B', tone); sh.ink_rect(x0 + w - 1, y0, 1, h, 'B', tone)
    for k in range(3, w - 1, 3):
        sh.ink_rect(x0 + k, y0 + 1, 1, h - 2, 'B', tone + 1.0)
    mid = y0 + h // 2
    sh.ink_line(x0 + 2, mid, x0 + w - 4, mid, 'B', tone - 0.6)
    for k in range(4):
        sh.ink_px(x0 + w - 4 - k, mid - k, 'B', tone - 0.6)
        sh.ink_px(x0 + w - 4 - k, mid + k, 'B', tone - 0.6)
    sh.ink_rect(x0 + 1, mid - 1, 3, 3, 'B', tone - 0.6)      # start dot


def chimney(sh, ax, ay, tone=2.2):
    """Landmark 2: chimney stack (solid square with a light cross) in one cell."""
    x0, y0 = gx(ax) + 3, gx(ay) + 3
    s = CELL - 6
    sh.ink_rect(x0, y0, s, s, 'B', tone)
    for k in range(s):
        sh.lay.px(x0 + k, y0 + k, 'P', 6.0, flat=True)
        sh.lay.px(x0 + s - 1 - k, y0 + k, 'P', 6.0, flat=True)
        sh.ink[y0 + k, x0 + k] = False
        sh.ink[y0 + k, x0 + s - 1 - k] = False
    sh.ink_rect(x0 - 1, y0 - 1, s + 2, 1, 'B', tone + 1.2)
    sh.ink_rect(x0 - 1, y0 + s, s + 2, 1, 'B', tone + 1.2)


def hatch_rect(sh, x0, y0, x1, y1, step=4, tone=4.6):
    for k in range(-(y1 - y0), x1 - x0, step):
        for t in range(0, y1 - y0):
            x = x0 + k + t
            y = y1 - 1 - t
            if x0 <= x < x1 and y0 <= y < y1:
                sh.ink_px(x, y, 'B', tone)


def label(sh, text, x, y, tone=3.4, font='35'):
    m = kit.text_mask(text, font)
    sh.ink_mask(m, int(x), int(y), 'B', tone)
    return m.shape[1]


# =========================================================================== building
def building(sh: Sheet, dx=0, dy=0, variant='A'):
    """Draw the shared building at a cell offset (dx,dy).  variant 'A' closes the supply wing;
    'B' shows the corridor continuing behind a second wall."""
    x0, y0, x1, y1 = BLD[0] + dx, BLD[1] + dy, BLD[2] + dx, BLD[3] + dy
    cy0, cy1 = CORR_Y[0] + dy, CORR_Y[1] + dy
    wing = WING_X + dx
    old = variant == 'B'
    tw = 3.0 if old else 2.6            # older print: slightly paler lines
    # outer walls with windows
    wall_h(sh, x0, x1, y0, tone=tw)
    wall_h(sh, x0, x1, y1, tone=tw)
    wall_v(sh, x0, y0, y1, tone=tw, gap=(gx(cy0) + 3, gx(cy1) - 2))        # main entrance west
    if old:
        wall_v(sh, x1, y0, y1, tone=tw, gap=(gx(cy0) + 2, gx(cy1) - 1))    # draft: corridor exits east
    else:
        wall_v(sh, x1, y0, y1, tone=tw)
    for c in range(x0, x1):
        if c in (wing - 1, wing):
            continue
        window_mark(sh, gx(c) + 4, gx(c) + 12, gx(y0))
        window_mark(sh, gx(c) + 4, gx(c) + 12, gx(y1))
    # corridor walls (with door gaps)
    doors_n = [x0 + 2, x0 + 5, x0 + 7]
    doors_s = [x0 + 1, x0 + 4, x0 + 8]
    gaps_n = [(gx(c) + 4, gx(c) + 12) for c in doors_n]
    gaps_s = [(gx(c) + 4, gx(c) + 12) for c in doors_s]

    def wall_with_gaps(yc, gaps, x_from, x_to):
        y = gx(yc) - 1
        for x in range(gx(x_from) - 1, gx(x_to) + 2):
            if any(a <= x < b for a, b in gaps):
                continue
            for k in range(2):
                sh.ink_px(x, y + k, 'B', tw + 0.2)
    corr_end = x1 if old else wing
    wall_with_gaps(cy0, gaps_n, x0, corr_end)
    wall_with_gaps(cy1, gaps_s, x0, corr_end)
    for (a, b) in gaps_n:
        door_arc(sh, a, gx(cy0) - 1, 7, (1, -1))
    for (a, b) in gaps_s:
        door_arc(sh, a, gx(cy1) + 1, 7, (1, 1))
    # room partitions (north and south of the corridor)
    for c in (x0 + 3, x0 + 6):
        wall_v(sh, c, y0, cy0, thick=2, tone=tw + 0.2)
    for c in (x0 + 3, x0 + 7):
        wall_v(sh, c, cy1, y1, thick=2, tone=tw + 0.2)
    # supply wing
    if not old:
        wall_v(sh, wing, y0, y1, thick=3, tone=tw)              # closes the corridor
        hatch_rect(sh, gx(wing) + 3, gx(y0) + 3, gx(x1) - 2, gx(y1) - 2, step=4, tone=4.8)
        lw = kit.text_width('VERSORGUNG')
        lx = gx(wing) + (gx(x1) - gx(wing) - lw) // 2
        ly = gx(cy0) - 2
        sh.lay.rect(lx - 2, ly - 2, lw + 4, 9, 'P', 6.2, flat=True)
        sh.ink[ly - 2:ly + 7, lx - 2:lx + lw + 2] = False
        label(sh, 'VERSORGUNG', lx, ly, tone=2.6)
        lw2 = kit.text_width('GESCHLOSSEN')
        lx2 = gx(wing) + (gx(x1) - gx(wing) - lw2) // 2
        sh.lay.rect(lx2 - 2, ly + 9, lw2 + 4, 8, 'P', 6.2, flat=True)
        sh.ink[ly + 9:ly + 17, lx2 - 2:lx2 + lw2 + 2] = False
        label(sh, 'GESCHLOSSEN', lx2, ly + 10, tone=3.4)
    else:
        # the first wall (where plan A closes the wing) -- here a concealed door, dashed
        x = gx(wing) - 1
        for y in range(gx(y0), gx(y1)):
            inside = gx(cy0) + 1 <= y <= gx(cy1) - 1
            if inside and (y % 4) >= 2:
                continue
            for k in range(3):
                sh.ink_px(x + k, y, 'B', tw)
        # second wall half a cell further east: the corridor runs on behind it
        x2 = gx(wing) + 7
        for y in range(gx(cy0) - 1, gx(cy1) + 2):
            if (y % 3) == 0:
                continue
            for k in range(2):
                sh.ink_px(x2 + k, y, 'B', tw + 0.6)
        # wing rooms as plain rooms (not closed off) in the draft
        wall_v(sh, wing + 2, y0, cy0, thick=2, tone=tw + 0.2)
        wall_v(sh, wing + 2, cy1, y1, thick=2, tone=tw + 0.2)
        # corridor continues beyond the east wall as a covered passage (dashed)
        for x in range(gx(x1) + 2, sh.w - 6):
            if (x // 3) % 2 == 0:
                sh.ink_px(x, gx(cy0) - 1, 'B', tw + 0.4)
                sh.ink_px(x, gx(cy1), 'B', tw + 0.4)
        # walking line along the hidden corridor
        for x in range(gx(wing) + 2, sh.w - 8, 5):
            sh.ink_px(x, (gx(cy0) + gx(cy1)) // 2, 'B', 4.2)
            sh.ink_px(x + 1, (gx(cy0) + gx(cy1)) // 2, 'B', 4.2)
    # landmarks (identical drawing on both sheets)
    staircase(sh, STAIR_A[0] + dx, STAIR_A[1] + dy)
    chimney(sh, CHIM_A[0] + dx, CHIM_A[1] + dy)
    # room labels
    lab = [('BÜRO', x0 + 1, y0 + 0), ('ARCHIV', x0 + 4, y0 + 1), ('FLUR', x0 + 1, cy0),
           ('LAGER', x0 + 4, cy1 + 1), ('BÜRO', x0 + 7, cy1 + 1)]
    for (t, cx, cy) in lab:
        tx = gx(cx) + 3
        ty = gx(cy) + 5 if t != 'FLUR' else gx(cy) + 6
        label(sh, t, tx, ty, tone=4.0)


def frame(sh: Sheet, tone=3.0):
    sh.ink_rect(3, 3, sh.w - 6, 1, 'B', tone); sh.ink_rect(3, sh.h - 4, sh.w - 6, 1, 'B', tone)
    sh.ink_rect(3, 3, 1, sh.h - 6, 'B', tone); sh.ink_rect(sh.w - 4, 3, 1, sh.h - 6, 'B', tone)
    sh.ink_rect(5, 5, sh.w - 10, 1, 'B', tone + 1.4); sh.ink_rect(5, sh.h - 6, sh.w - 10, 1, 'B', tone + 1.4)
    sh.ink_rect(5, 5, 1, sh.h - 10, 'B', tone + 1.4); sh.ink_rect(sh.w - 6, 5, 1, sh.h - 10, 'B', tone + 1.4)


def title_block(sh, x, y, w, h, lines, tone=2.8):
    lay = sh.lay
    lay.rect(x, y, w, h, 'P', 6.2, flat=True)
    sh.ink[y:y + h, x:x + w] = False
    sh.ink_rect(x, y, w, 1, 'B', tone); sh.ink_rect(x, y + h - 1, w, 1, 'B', tone)
    sh.ink_rect(x, y, 1, h, 'B', tone); sh.ink_rect(x + w - 1, y, 1, h, 'B', tone)
    yy = y + 3
    for (txt, font, t) in lines:
        if txt == '---':
            sh.ink_rect(x + 1, yy, w - 2, 1, 'B', tone + 1.0)
            yy += 3
            continue
        m = kit.text_mask(txt, font)
        sh.ink_mask(m, x + 3, yy, 'B', t)
        yy += m.shape[0] + 2


def stamp_box(sh, x, y, text, ramp='I', tone=2.0, seed=0, emblem=True):
    """Rubber stamp in violet-black office ink: double border, optional Reichssiegel, uneven
    coverage (never the red story accent, which is reserved for C-17)."""
    rng = np.random.default_rng(seed)
    m = kit.text_mask(text, '57')
    pad = 4
    ew = 11 if emblem else 0
    w = m.shape[1] + 2 * pad + ew + 2
    h = m.shape[0] + 2 * pad + 2
    box = np.zeros((h, w), bool)
    box[0, :] = box[-1, :] = True
    box[:, 0] = box[:, -1] = True
    box[2, 2:-2] = box[-3, 2:-2] = True
    box[2:-2, 2] = box[2:-2, -3] = True
    ty = pad + 1
    tx = pad + 1 + ew
    box[ty:ty + m.shape[0], tx:tx + m.shape[1]] |= m
    if emblem:
        d, p = kit.reichssiegel_mask(9)
        oy = (h - 9) // 2
        box[oy:oy + 9, pad + 1:pad + 10] |= d & ~p
    keep = rng.random(box.shape) > 0.1
    sh.ink_mask(box & keep, x, y, ramp, tone)
    return w, h


# =========================================================================== handwriting (pencil)
def pencil(sh: Sheet, polys, radius=0.9, seed=0, tones=(2.4, 3.2)):
    m = kit.stroke_mask(sh.w, sh.h, polys, radius, jitter=0.12, seed=seed)
    rng = np.random.default_rng(seed + 5)
    ys, xs = np.nonzero(m)
    for y, x in zip(ys, xs):
        sh.ink_px(x, y, 'K', tones[0] if rng.random() < 0.6 else tones[1])


def arrow(sh, pts, seed=0, head=4):
    pencil(sh, [kit.smooth_poly(pts, 8)], radius=0.55, seed=seed)
    (ax, ay), (bx, by) = pts[-2], pts[-1]
    ang = math.atan2(by - ay, bx - ax)
    for s in (-1, 1):
        a2 = ang + math.pi + s * 0.5
        pencil(sh, [[(bx, by), (bx + math.cos(a2) * head, by + math.sin(a2) * head)]], radius=0.55, seed=seed + s)


# =========================================================================== sheets
def plan_a():
    sh = Sheet(W, H, 'berlin_plan_a')
    paper(sh, seed=301, age=0.15, stains=0)
    grid(sh)
    frame(sh)
    building(sh, 0, 0, 'A')
    # title block (bottom right) + approval stamp
    title_block(sh, 190, 150, 92, 36, [('BAUAMT BERLIN', '35', 2.4), ('GRUNDRISS 2.OG', '35', 3.0),
                                       ('---', '', 0), ('BLATT 3/A  M 1:200', '35', 3.0)])
    stamp_box(sh, 100, 150, 'GENEHMIGT', 'I', 2.0, seed=4)
    # signature + date beside the stamp (ink)
    pol = kit.scribble_polys(104, 182, 34, 3, seed=8, words=5)
    m = kit.stroke_mask(W, H, pol, 0.45)
    sh.ink_mask(m, 0, 0, 'I', 2.0)
    label(sh, '12.3.1962', 146, 178, tone=2.6)
    return sh


def plan_b():
    sh = Sheet(W, H, 'berlin_plan_b')
    paper(sh, seed=417, age=0.85, folds=True, torn=True, stains=1)
    grid(sh, tone=5.6)
    frame(sh, tone=3.4)
    building(sh, DX, DY, 'B')
    # title block top right (older sheet layout)
    title_block(sh, 196, 9, 86, 22, [('VORENTWURF 1958', '35', 3.0), ('ARCHIV NR. 31/4', '35', 3.4)], tone=3.4)
    # pencil annotation 'C-17' with an arrow to the hidden corridor + a circle round the 2nd wall
    hx, hy = 236, 118
    polys = kit.hand_polys('C-17', hx, hy, 11, 7, 2.5, slant=0.15, seed=21)
    pencil(sh, polys, radius=0.75, seed=21)
    pencil(sh, [[(hx - 1, hy + 14), (hx + 30, hy + 13)]], radius=0.5, seed=22)            # underline
    arrow(sh, [(hx + 4, hy - 2), (hx - 4, hy - 9), (hx - 16, hy - 13)], seed=23, head=4)
    ring = []
    cxr, cyr = gx(WING_X + DX) + 4, (gx(CORR_Y[0] + DY) + gx(CORR_Y[1] + DY)) // 2
    for a in np.linspace(0.3, 2 * math.pi + 0.5, 40):
        ring.append((cxr + math.cos(a) * 13, cyr + math.sin(a) * 11))
    pencil(sh, [ring], radius=0.5, seed=24)
    return sh, (hx - 2, hy - 2, 36, 18)


def lines_only(sh: Sheet) -> np.ndarray:
    out = sh.lay.c.copy()
    out[~sh.ink] = 0
    return out


def emil_note():
    w, h = 220, 150
    sh = Sheet(w, h, 'berlin_emil_note')
    lay = sh.lay
    paper(sh, seed=505, age=0.35)
    # printed form: header, ruled lines, field labels (pale blue print)
    label(sh, 'BAUARCHIV', 34, 12, tone=2.4, font='57')
    label(sh, 'AUSKUNFT / LEIHSCHEIN', 34, 22, tone=3.4)
    lay.rect(34, 30, 176, 1, 'B', 4.0, flat=True)
    rows = [('SIGNATUR', 48), ('SERIE', 68), ('BETREFF', 88), ('VERMERK', 108), ('DATUM', 128)]
    for (t, y) in rows:
        label(sh, t, 12, y - 6, tone=4.0)
        for x in range(56, 208, 1):
            lay.px(x, y, 'B', 5.2 if x % 2 else 4.8, flat=True)
    lay.rect(52, 36, 1, 100, 'R', 2.0, flat=True)          # red margin line of the form
    # punched hole + paper clip
    lay.ellipse(16, 14, 4.0, 4.0, 'N', 0.0, flat=True)
    lay.erase_mask(lay.ellipse_mask(16, 14, 3.0, 3.0)[0], *lay.ellipse_mask(16, 14, 3.0, 3.0)[1:])
    clip = [[(186, -2), (186, 20), (192, 24), (198, 20), (198, 2), (194, -1), (190, 2), (190, 16)]]
    m = kit.stroke_mask(w, h, [kit.smooth_poly(clip[0], 4)], 0.8)
    lay.put(m, 0, 0, 'W', 8.0, flat=True)
    hi = m & ~np.roll(m, 1, axis=1)
    lay.put(hi, 0, 0, 'W', 10.0, flat=True)
    # handwriting in blue-black fountain-pen ink
    def ink(polys, seed, r=0.6):
        mm = kit.stroke_mask(w, h, polys, r, jitter=0.08, seed=seed)
        lay.put(mm, 0, 0, 'I', 2.0, flat=True)
    ink(kit.scribble_polys(60, 46, 70, 4, seed=1), 1)
    ink(kit.hand_polys('31/4', 140, 37, 9, 6, 2, seed=2), 2)
    # SERIE: C-17, bigger and underlined twice
    ink(kit.hand_polys('C-17', 64, 52, 14, 9, 3, slant=0.18, seed=3), 3, r=0.8)
    ink([[(62, 69), (112, 68)]], 4, r=0.5)
    ink([[(65, 72), (106, 72)]], 5, r=0.5)
    ink(kit.scribble_polys(60, 86, 82, 4, seed=6), 6)
    ink(kit.scribble_polys(60, 106, 120, 4, seed=7), 7)
    ink(kit.hand_polys('3.11.64', 62, 119, 8, 5, 1.5, seed=9), 9)
    ink(kit.hand_polys('E.H.', 168, 117, 8, 5, 1.5, seed=10), 10)
    # internal-use stamp in office ink, placed in the empty end of the BETREFF row
    stamp_box(sh, 150, 75, 'INTERN', 'I', 3.0, seed=12, emblem=False)
    return sh


# =========================================================================== build
def build_all(doc_dir, prev_dir=None):
    os.makedirs(doc_dir, exist_ok=True)
    out = []
    a = plan_a()
    a.lay.resolve()
    b, note_rect = plan_b()
    b.lay.resolve()
    for sh, name, desc in ((a, 'berlin_plan_a', 'approved public floor plan (supply wing closed), 18x12 cells'),
                           (b, 'berlin_plan_b', 'archived 1958 draft: corridor behind a second wall, pencil C-17')):
        p = os.path.join(doc_dir, name + '.png')
        kit.save_rgba(sh.lay.c, p)
        out.append((p, desc))
        pl = os.path.join(doc_dir, name + '_lines.png')
        kit.save_rgba(lines_only(sh), pl)
        out.append((pl, desc + ' -- lines only on transparent (overlay UI)'))
    e = emil_note()
    e.lay.resolve()
    pe = os.path.join(doc_dir, 'berlin_emil_note.png')
    kit.save_rgba(e.lay.c, pe)
    out.append((pe, "Emil's handwritten archive slip (Serie C-17)"))
    # ---- json
    hid_b = [gx(WING_X + DX), gx(CORR_Y[0] + DY), W - gx(WING_X + DX), CELL]
    hid_a = [hid_b[0] + SOLUTION['offset_x'] * CELL, hid_b[1] + SOLUTION['offset_y'] * CELL,
             min(W, hid_b[0] + hid_b[2] + SOLUTION['offset_x'] * CELL) - (hid_b[0] + SOLUTION['offset_x'] * CELL),
             CELL]
    data = {
        'puzzle_id': 'pz_blueprint',
        'cell_px': CELL, 'grid': [GW, GH], 'size_px': [W, H], 'display_scale': 3,
        'coords': 'pixels/cells from the top-left of each sheet; +x right, +y down',
        'plan_a': {'file': 'berlin_plan_a.png', 'lines': 'berlin_plan_a_lines.png', 'item': 'ev_plan_a',
                   'landmarks': {'staircase': {'cell': list(STAIR_A), 'size': [2, 2]},
                                 'chimney': {'cell': list(CHIM_A), 'size': [1, 1]}},
                   'building_cells': list(BLD), 'closed_wing_x_cell': WING_X},
        'plan_b': {'file': 'berlin_plan_b.png', 'lines': 'berlin_plan_b_lines.png', 'item': 'ev_plan_b',
                   'landmarks': {'staircase': {'cell': list(STAIR_B), 'size': [2, 2]},
                                 'chimney': {'cell': list(CHIM_B), 'size': [1, 1]}},
                   'annotation': {'text': 'C-17', 'medium': 'pencil', 'rect_px': list(note_rect)}},
        'solution': dict(SOLUTION, applies_to='plan_b', units='cells',
                         check='landmark_b + offset == landmark_a for both landmarks'),
        'hidden_corridor': {'rect_in_plan_b_px': hid_b, 'rect_in_plan_a_px': hid_a,
                            'note': 'corridor that exists only in the draft; after alignment it runs through '
                                    'the closed supply wing of plan A and out of the east wall'},
        'accessibility': 'landmarks differ by shape (stair treads + arrow vs. solid square with cross), '
                         'readable in greyscale; no colour coding needed',
        'world_note': 'Simplified fictional overlay, not an authentic architectural document.',
        'generator': 'tools/pixelgen/env_berlin_docs.py', 'date': kit.DATE,
    }
    # self-check of the canonical solution
    for lm in ('staircase', 'chimney'):
        bx, by = data['plan_b']['landmarks'][lm]['cell']
        ax, ay = data['plan_a']['landmarks'][lm]['cell']
        assert (bx + SOLUTION['offset_x'], by + SOLUTION['offset_y']) == (ax, ay), lm
    pj = os.path.join(doc_dir, 'berlin_plans.json')
    with open(pj, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=1, ensure_ascii=False)
    out.append((pj, 'overlay puzzle data: cells, landmarks, solution (+2,-1,rot 0), hidden corridor rects'))
    if prev_dir:
        kit.ensure_gdignore(prev_dir)
        for sh, name in ((a, 'plan_a'), (b, 'plan_b'), (e, 'emil_note')):
            pg.upscale(sh.lay.image(), 3).save(os.path.join(prev_dir, 'doc_%s_x3.png' % name))
        # overlay check: plan A with plan B lines shifted by the solution
        comp = a.lay.c.copy()
        bl = lines_only(b)
        ox, oy = SOLUTION['offset_x'] * CELL, SOLUTION['offset_y'] * CELL
        for y in range(H):
            for x in range(W):
                sx, sy = x - ox, y - oy
                if 0 <= sx < W and 0 <= sy < H and bl[sy, sx, 3] > 0:
                    comp[y, x] = (bl[sy, sx] * 0.5 + comp[y, x] * 0.5).astype(np.uint8)
                    comp[y, x, 3] = 255
        from PIL import Image
        pg.upscale(Image.fromarray(comp, 'RGBA'), 3).save(os.path.join(prev_dir, 'doc_overlay_solved_x3.png'))
    return out
