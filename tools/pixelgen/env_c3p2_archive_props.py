"""env_c3p2_archive_props -- y-sorted props and the foreground frame of L_C3_Registry.

* cart: the handcart with the emptied crates of courier wagon 4 (yard, hotspot `crates`): seal wire dangling
  from the top crate until c3c_inspect_crates (cart_open afterwards); the railway stencil on the crates is
  the insignia site of the yard: neutral (winged wheel, "МПС") or `_hist` (hammer and sickle, "СССР").
* fg_frame: foreground silhouettes at parallax 1.25 (a snowed-in bollard, cast-iron columns of the cellar,
  stacked boxes), kept clear of every story hotspot and spawn (check_clearance).
"""
from __future__ import annotations

import math

import numpy as np

import env_c3p2_archive_kit as K
import env_c3p2_archive_layout as L

FG_PARALLAX = 1.25


class Prop:
    def __init__(self, name, x, base_y, w, h, note):
        self.name, self.x, self.base_y, self.w, self.h, self.note = name, x, base_y, w, h, note
        self.y = base_y - h + 4
        self.lay = K.tlayer(w, h, name)
        self.hist_lay = None
        self.collision = None


def _crate(lay, x, y, w, h, seed, stencil=None, hist=False, lid=True, tag=False):
    K.grain(lay, x, y, w, h, 'D', 3.0, seed=seed, amp=0.35, vertical=False)
    for yy in range(y, y + h, 5):                                      # boards
        lay.rect(x, yy, w, 1, 'D', 1.6, hgt=0.3)
    lay.rect(x, y, 2, h, 'D', 2.0, hgt=0.9)                             # corner battens
    lay.rect(x + w - 2, y, 2, h, 'D', 1.6, hgt=0.9)
    lay.rect(x, y, w, 2, 'D', 3.8 if lid else 1.2, hgt=0.9)
    lay.rect(x, y + h - 2, w, 2, 'D', 2.0, hgt=0.8)
    for (sx, sy) in ((x + 1, y + 1), (x + w - 2, y + 1), (x + 1, y + h - 2), (x + w - 2, y + h - 2)):
        lay.px(sx, sy, 'S', 3.6, hgt=1.0)                               # nail heads
    if stencil:
        cx = x + w // 2
        K.text(lay, stencil, cx + 4, y + 6, 'I', 0.8, center=True)
        ex, ey = cx - 12, y + 5
        if hist:
            pat = ['.#...', '###..', '.#...', '.##.#', '...##', '#.##.']        # star over hammer and sickle
            for yy, row in enumerate(pat):
                for xx, ch in enumerate(row):
                    if ch == '#':
                        lay.px(ex + xx, ey + yy, 'R', 2.6)
        else:
            pat = ['#.....#', '##.#.##', '.#####.', '..#.#..', '.#####.', '..###..']  # winged wheel
            for yy, row in enumerate(pat):
                for xx, ch in enumerate(row):
                    if ch == '#':
                        lay.px(ex + xx - 1, ey + yy, 'I', 1.2)
        K.text(lay, 'ВАГОН 4', cx, y + h - 8, 'I', 0.8, center=True)
    if tag:
        lay.rect(x + w - 9, y + 3, 6, 4, 'R', 3.0, hgt=1.1)            # the red C-17 tag
        lay.px(x + w - 9, y + 3, 'P', 4.0)
        lay.rect(x + w - 7, y + 7, 1, 2, 'S', 3.0)


def paint_cart(lay, hist=False, seal=True):
    w, h = lay.w, lay.h
    base = h - 4
    # platform cart: deck, frame, two spoked wheels, pull bar resting on the ground
    lay.rect(4, base - 10, w - 12, 4, 'D', 2.6, hgt=1.0)
    lay.rect(4, base - 10, w - 12, 1, 'D', 3.8, hgt=1.1)
    lay.rect(4, base - 6, w - 12, 2, 'S', 1.6, hgt=0.8)
    for wx in (14, w - 22):
        for a in range(0, 360, 10):
            for r in (5, 4):
                lay.px(wx + round(math.cos(math.radians(a)) * r), base - 4 + round(math.sin(math.radians(a)) * r),
                       'I', 1.6 if r == 5 else 1.0, hgt=0.9)
        for a in (0, 60, 120):
            lay.line(wx - round(math.cos(math.radians(a)) * 4), base - 4 - round(math.sin(math.radians(a)) * 4),
                     wx + round(math.cos(math.radians(a)) * 4), base - 4 + round(math.sin(math.radians(a)) * 4),
                     'S', 2.2)
        lay.rect(wx - 1, base - 5, 3, 3, 'S', 3.2, hgt=1.0)
    lay.line(w - 9, base - 8, w - 1, base + 2, 'S', 2.4)                 # pull bar
    lay.line(w - 8, base - 8, w, base + 2, 'S', 1.2)
    lay.rect(w - 3, base + 1, 4, 2, 'S', 3.0)
    # crates: two side by side, one on top, a lid leaning against the cart, straw spilling
    _crate(lay, 6, base - 32, 30, 22, 11, stencil='МПС' if not hist else 'СССР', hist=hist, lid=False)
    _crate(lay, 37, base - 30, 28, 20, 12, lid=False, tag=True)
    _crate(lay, 16, base - 50, 26, 18, 13, lid=False)
    for k in range(18):                                                   # straw
        sx = 8 + (k * 7) % 56
        sy = base - 33 - (k % 3)
        lay.line(sx, sy, sx + 2 + k % 3, sy - 2, 'B', 3.0 + (k % 2) * 0.6)
    lay.line(18, base - 51, 22, base - 54, 'B', 3.4)
    for k in range(20):                                                   # lid leaning against the cart
        lay.rect(w - 26 + k // 4, base - 28 + k, 14, 1, 'D', 2.4 + (k % 5 == 0) * 1.0, hgt=1.0)
    # snow dusting on the tops
    for (x0, x1, y) in ((16, 42, base - 51), (37, 65, base - 31), (6, 16, base - 33), (w - 26, w - 12, base - 29)):
        for x in range(x0, x1):
            if (x * 5) % 3:
                lay.px(x, y, 'SN', 4.6, hgt=1.2)
    if seal:
        # the cut seal wire dangling from the top crate, the lead seal at its end
        pts = [(36, base - 46), (38, base - 40), (37, base - 34), (39, base - 28)]
        for a, b in zip(pts[:-1], pts[1:]):
            lay.line(a[0], a[1], b[0], b[1], 'S', 4.2, hgt=1.2)
        lay.rect(38, base - 28, 3, 3, 'S', 3.0, hgt=1.3)
        lay.px(39, base - 27, 'S', 5.0)


def build_cart(hist=False, seal=True):
    x0, x1 = L.CART
    p = Prop('cart' if seal else 'cart_open', x0, 292, x1 - x0 + 10, 64,
             'handcart with the emptied crates of courier wagon 4 (seal wire %s, red C-17 tag)' %
             ('dangling' if seal else 'taken'))
    paint_cart(p.lay, hist=False, seal=seal)
    if hist:
        p.hist_lay = K.tlayer(p.w, p.h, p.name + '_hist')
        paint_cart(p.hist_lay, hist=True, seal=seal)
    p.collision = [[x0 + 2, 288], [x1 + 4, 288], [x1 + 4, 293], [x0 + 2, 293]]
    return p


def bake_prop(p: Prop, lights, exposure=0.7):
    for lay in [p.lay] + ([p.hist_lay] if p.hist_lay is not None else []):
        F = K.light_fields(lay, lights, origin=(p.x, p.y))
        K.resolve_state(lay, F, fire=False, exposure=exposure)


# =========================================================================== foreground frame
def build_fg():
    """Foreground silhouettes (parallax 1.25, unlit).  Coordinates are fg-layer pixels: an element at fg x
    appears at screen x = fg_x - 1.25 * camera_x."""
    w = int(math.ceil(L.VIEW_W + FG_PARALLAX * (L.WORLD_W - L.VIEW_W))) + 8
    h = L.WORLD_H
    lay = K.tlayer(w, h, 'fg_frame')
    rng = np.random.default_rng(5)

    def column(x, cw=14):
        lay.rect(x, 0, cw, h, 'N', 0.4, unlit=True)
        lay.rect(x + 2, 0, 1, h, 'C', 2.2, unlit=True)               # cold rim (window side)
        lay.rect(x + cw - 2, 0, 1, h, 'N', 1.6, unlit=True)
        for yy in (40, h - 40):                                        # capital / base collars
            lay.rect(x - 3, yy, cw + 6, 6, 'N', 0.6, unlit=True)
            lay.rect(x - 3, yy, cw + 6, 1, 'C', 2.0, unlit=True)
        for yy in range(52, h - 46, 30):
            lay.rect(x + 3, yy, cw - 6, 1, 'N', 1.2, unlit=True)

    def bollard(x):
        for yy in range(300, h):
            half = 9 if yy > 306 else int(9 * math.sqrt(max(0.0, 1 - ((306 - yy) / 7.0) ** 2)))
            lay.rect(x - half, yy, 2 * half, 1, 'N', 0.6, unlit=True)
        for xx in range(x - 10, x + 11):                              # snow cap
            top = 297 + int(abs(xx - x) * 0.3) + (rng.integers(0, 2))
            lay.rect(xx, top, 1, 4, 'SN', 2.4, unlit=True)
            lay.px(xx, top, 'SN', 3.4, unlit=True)

    def boxes(x):
        for k, (bw, bh) in enumerate(((40, 26), (34, 22), (38, 24))):
            bx = x + k * 6 - 3
            by = h - 2 - (k + 1) * 24
            lay.rect(bx, by, bw, bh, 'N', 0.8 + k * 0.2, unlit=True)
            lay.rect(bx, by, bw, 1, 'C', 1.8, unlit=True)
            lay.rect(bx + 8, by + 6, 14, 6, 'N', 1.6, unlit=True)

    def cable(x0, x1, y0, sag):
        for x in range(x0, x1):
            t = (x - x0) / (x1 - x0)
            yy = int(y0 + sag * 4 * t * (1 - t))
            lay.px(x, yy, 'N', 0.6, unlit=True)
            lay.px(x, yy + 1, 'N', 0.6, unlit=True)

    bollard(70)
    column(574)
    column(870)
    column(1450)
    column(2180)
    cable(560, 760, 6, 26)
    cable(1380, 1620, 4, 30)
    K.resolve_state(lay, None, fire=False, exposure=1.0)
    return lay


def check_clearance(fg, hotspots):
    """Story hotspots must not be covered by the fg layer where a character stands (camera centred on it)."""
    alpha = fg.c[..., 3] > 0
    issues = []
    for name, (hx, hy) in hotspots.items():
        cam = min(max(hx - L.VIEW_W / 2, 0), L.WORLD_W - L.VIEW_W)
        sx = hx - cam
        fx = int(round(sx + FG_PARALLAX * cam))
        x0, x1 = max(0, fx - 12), min(fg.w, fx + 13)
        if alpha[250:306, x0:x1].any():
            issues.append(name)
    return issues
