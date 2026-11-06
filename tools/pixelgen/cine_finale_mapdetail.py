"""cine_finale_mapdetail -- cartographic detail for the border map of the X1 finale (owner: trans-finale).

Adds to the schematic map paper (cine_finale_rest.map_paper): forests (tree symbols), hill hachures, a
railway network with stations (black-and-white railway line symbol), roads, lakes, a coordinate grid with
letters/numbers on the frame, a legend, a scale bar, a north arrow, pencil work (a circle round Veltrava,
the corridor kilometre marks), wear (stains of a coffee cup and of a tea glass, a torn corner, tape), and the
things lying in the two lamp pools: Konrad's pencil and eraser crumbs (left), Alexei's pencil stub and the
ring of his tea glass (right).  In the 'dark' state the cold light of a window falls across the paper.
All marks are inked through the paper's own light (ink darker where the lamps shine), deterministic.
"""
from __future__ import annotations

import math

import numpy as np

import cine_finale_kit as kit
import pg

W, H = 680, 380


def enrich(cv: kit.Canvas, t: np.ndarray, tone_ramp, state: str, cities: dict, line_x: int, route_pts):
    """cv: map canvas (paper already painted); t: paper tone field; cities: name -> (x, y)."""
    xx, yy = cv.grid()
    rng = np.random.default_rng(kit.seed_of('mapdetail'))

    def ink_at(x, y, k=0.45):
        ix = int(np.clip(x, 0, W - 1))
        iy = int(np.clip(y, 0, H - 1))
        return kit.tone_to_ramp(np.array([[float(t[iy, ix]) * k]], np.float32), tone_ramp, dither=False)[0, 0]

    def px(x, y, k=0.45):
        ix, iy = int(x), int(y)
        if 0 <= ix < W and 0 <= iy < H:
            cv.c[iy, ix] = ink_at(ix, iy, k)

    x0f, y0f, x1f, y1f = 34, 62, 646, 316
    # --- coordinate grid labels on the frame (letters along the top, numbers down the side)
    for i, gx in enumerate(range(x0f + 30, x1f, 60)):
        tm = kit.text_mask('ABCDEFGHIK'[i % 10], kit.FONT3)
        kit.blit_mask(cv.c, tm, gx, y0f - 7, ink_at(gx, y0f - 6, 0.5))
    for i, gy in enumerate(range(y0f + 26, y1f, 52)):
        tm = kit.text_mask(str(i + 1), kit.FONT3)
        kit.blit_mask(cv.c, tm, x0f - 6, gy, ink_at(x0f - 5, gy, 0.5))
    # faint grid crosses inside
    for gx in range(x0f + 60, x1f, 60):
        for gy in range(y0f + 52, y1f, 52):
            for d in (-2, -1, 1, 2):
                px(gx + d, gy, 0.7)
                px(gx, gy + d, 0.7)
    # --- forests: clusters of tiny tree symbols (circle + trunk)
    for (fx, fy, n, rx, ry) in ((90, 120, 26, 40, 22), (230, 280, 18, 34, 14), (470, 100, 24, 46, 20),
                                (590, 200, 16, 26, 26), (400, 290, 14, 30, 10), (180, 90, 12, 26, 12)):
        for _ in range(n):
            a = rng.uniform(0, 2 * math.pi)
            r = math.sqrt(rng.random())
            tx, ty = fx + math.cos(a) * rx * r, fy + math.sin(a) * ry * r
            for (dx, dy) in ((0, -1), (-1, 0), (1, 0), (0, 0)):
                px(tx + dx, ty + dy, 0.55)
            px(tx, ty + 1, 0.4)
    # --- lakes: outlined blobs with horizontal water lines
    for (lx_, ly_, rx, ry) in ((262, 160, 12, 6), (520, 280, 9, 5), (96, 286, 8, 4)):
        lm = kit.ellipse_full(W, H, lx_, ly_, rx, ry)
        cv.c[kit.outline_of(lm)] = [ink_at(lx_, ly_, 0.5)] * int(kit.outline_of(lm).sum()) if False else cv.c[kit.outline_of(lm)]
        for (yy_, xx_) in zip(*np.nonzero(kit.outline_of(lm))):
            cv.c[yy_, xx_] = ink_at(xx_, yy_, 0.5)
        for k in range(-ry + 2, ry - 1, 2):
            for xk in range(int(lx_ - rx * 0.6), int(lx_ + rx * 0.6), 2):
                if lm[int(ly_ + k), xk]:
                    px(xk, ly_ + k, 0.7)
    # --- railway network (black-and-white line symbol) and stations
    rails = [[(138, 238), (110, 180), (84, 110)], [(138, 238), (200, 300), (230, 316)],
             [(340, 224), (380, 150), (420, 66)], [(340, 224), (300, 290), (290, 316)],
             [(546, 248), (590, 170), (640, 120)], [(546, 248), (600, 300), (630, 316)]]
    for ctrl in rails:
        pts = pg.bezier(ctrl, n=140)
        for i, (x, y) in enumerate(pts):
            px(x, y, 0.40)
            if (i // 4) % 2 == 0:
                px(x, y + 1, 0.40)
        for (sx, sy) in ctrl[1:2]:
            st = kit.ellipse_full(W, H, sx, sy, 2.2, 2.2)
            for (yy_, xx_) in zip(*np.nonzero(st)):
                cv.c[yy_, xx_] = ink_at(xx_, yy_, 0.35)
    # roads: fine dotted lines between the stations
    for (a, b_) in (((110, 180), (200, 120)), ((380, 150), (470, 160)), ((590, 170), (520, 120)), ((300, 290), (420, 300))):
        for k in range(0, 60):
            f = k / 59.0
            if k % 3 == 0:
                px(a[0] + (b_[0] - a[0]) * f, a[1] + (b_[1] - a[1]) * f + math.sin(f * 5) * 3, 0.6)
    # --- pencil work: a hand-drawn circle round Veltrava, kilometre ticks along the corridor
    vx, vy = cities['VELTRAVA']
    for k in range(64):
        a = k / 64.0 * 2 * math.pi
        r = 13 + math.sin(a * 3 + 1.0) * 1.2
        if k % 9 != 4:
            px(vx + math.cos(a) * r * 1.3, vy + math.sin(a) * r * 0.8, 0.62)
    for i, (x, y) in enumerate(route_pts[::28]):
        px(x, y - 5, 0.6)
        px(x, y - 6, 0.6)
    tm = kit.text_mask('KM 412', kit.FONT3)
    kit.blit_mask(cv.c, tm, 414, 206, ink_at(414, 206, 0.55))
    # --- legend (bottom right), scale bar, north arrow (top right)
    lx0, ly0 = 552, 270
    lg = (xx >= lx0) & (xx < lx0 + 88) & (yy >= ly0) & (yy < ly0 + 40)
    cv.c[kit.outline_of(lg)] = [ink_at(lx0, ly0, 0.45)][0]
    rows = (('LINIE', 'dash'), ('BAHN', 'rail'), ('KORRIDOR', 'hatch'))
    for i, (label, kind) in enumerate(rows):
        yy0 = ly0 + 7 + i * 11
        for k in range(16):
            if kind == 'dash' and (k % 6) < 4:
                px(lx0 + 5 + k, yy0, 0.35)
            elif kind == 'rail':
                px(lx0 + 5 + k, yy0, 0.4)
                if (k // 4) % 2 == 0:
                    px(lx0 + 5 + k, yy0 + 1, 0.4)
            elif kind == 'hatch' and k % 3 == 0:
                px(lx0 + 5 + k, yy0 - 1, 0.55)
                px(lx0 + 5 + k, yy0 + 2, 0.55)
        tm = kit.text_mask(label, kit.FONT3)
        kit.blit_mask(cv.c, tm, lx0 + 26, yy0 - 2, ink_at(lx0 + 26, yy0, 0.45))
    sx0, sy0 = 60, 300
    for k in range(80):
        px(sx0 + k, sy0, 0.4)
        if (k // 20) % 2 == 0:
            px(sx0 + k, sy0 + 1, 0.4)
    for k in (0, 40, 80):
        px(sx0 + k, sy0 - 1, 0.4)
        px(sx0 + k, sy0 - 2, 0.4)
    tm = kit.text_mask('0   25   50 KM', kit.FONT3)
    kit.blit_mask(cv.c, tm, sx0 - 1, sy0 + 3, ink_at(sx0, sy0 + 4, 0.5))
    nx_, ny_ = 616, 86
    for k in range(14):
        px(nx_, ny_ - 7 + k, 0.4)
    for k in range(5):
        px(nx_ - k * 0.6, ny_ - 7 + k, 0.4)
        px(nx_ + k * 0.6, ny_ - 7 + k, 0.4)
    tm = kit.text_mask('N', kit.FONT3)
    kit.blit_mask(cv.c, tm, nx_ - 1, ny_ - 15, ink_at(nx_, ny_ - 14, 0.45))
    # --- wear: coffee ring (Berlin side), tea-glass ring (Karsk side), torn corner and a strip of tape
    for (cx, cy, r, k) in ((206, 262, 9, 0.75), (470, 212, 11, 0.72)):
        for i in range(90):
            a = i / 90.0 * 2 * math.pi
            if rng.random() < 0.8:
                px(cx + math.cos(a) * r, cy + math.sin(a) * r * 0.62, k)
                if rng.random() < 0.4:
                    px(cx + math.cos(a) * (r - 1), cy + math.sin(a) * (r - 1) * 0.62, k + 0.1)
    torn = kit.poly_mask_full(W, H, [(x1f - 2, y0f - 1), (x1f + 8, y0f - 1), (x1f + 8, y0f + 14)])
    cv.c[torn] = np.asarray(tone_ramp[0], np.uint8)
    tape = kit.poly_mask_full(W, H, [(26, 54), (52, 48), (56, 58), (30, 64)])
    tt = np.clip(t * 1.15 + 0.06, 0, 1)
    tc = kit.tone_to_ramp(tt, tone_ramp)
    cv.c[tape] = tc[tape]
    # --- lying in the lamp pools: Konrad's pencil + eraser crumbs; Alexei's pencil stub
    if state in ('both', 'berlin', 'dark'):
        pa, pb = (88, 196), (132, 182)
        for k in range(46):
            f = k / 45.0
            x = pa[0] + (pb[0] - pa[0]) * f
            y = pa[1] + (pb[1] - pa[1]) * f
            col = kit.tone_to_ramp(np.array([[float(np.clip(t[int(y), int(x)] * 1.25, 0, 1))]], np.float32),
                                   [pg.hx(c) for c in ('#2A1B16', '#6E3F22', '#9A5A2F', '#D79A62', '#F2C27E')], dither=False)[0, 0]
            cv.c[int(y), int(x)] = col
            cv.c[int(y) + 1, int(x)] = kit.tone_to_ramp(np.array([[float(t[int(y), int(x)] * 0.6)]], np.float32),
                                                        [pg.hx(c) for c in ('#2A1B16', '#6E3F22', '#9A5A2F', '#D79A62')], dither=False)[0, 0]
        px(pa[0] - 1, pa[1] + 1, 0.2)
        for _ in range(9):
            px(150 + rng.uniform(-8, 8), 214 + rng.uniform(-3, 3), 1.15)
    if state in ('both', 'dark'):
        pa, pb = (556, 196), (580, 206)
        for k in range(26):
            f = k / 25.0
            x = pa[0] + (pb[0] - pa[0]) * f
            y = pa[1] + (pb[1] - pa[1]) * f
            col = kit.tone_to_ramp(np.array([[float(np.clip(t[int(y), int(x)] * 1.25, 0, 1))]], np.float32),
                                   [pg.hx(c) for c in ('#2E1C1A', '#4A2A22', '#8D5542', '#C98A5C', '#F0C487')], dither=False)[0, 0]
            cv.c[int(y), int(x)] = col
            cv.c[int(y) + 1, int(x)] = kit.tone_to_ramp(np.array([[float(t[int(y), int(x)] * 0.6)]], np.float32),
                                                        [pg.hx(c) for c in ('#2E1C1A', '#4A2A22', '#8D5542')], dither=False)[0, 0]
        px(pb[0] + 1, pb[1], 0.3)


def window_light(cv: kit.Canvas, tone_ramp, seed='map_window'):
    """Cold light of a tall window falling across the dark map: four panes with mullion shadows (a faint
    dithered lift of the paper towards the blue-grey of the ramp)."""
    xx, yy = cv.grid()
    bay = kit.bayer_full(W, H)
    # skewed window shape (light comes in from the upper left)
    def inside(x0, y0, x1, y1):
        sk = (yy - y0) * 0.45
        return (xx >= x0 + sk) & (xx < x1 + sk) & (yy >= y0) & (yy < y1)
    lit = np.zeros((H, W), bool)
    for (x0, y0, x1, y1) in ((150, 60, 238, 170), (246, 60, 334, 170), (150, 178, 238, 300), (246, 178, 334, 300)):
        lit |= inside(x0, y0, x1, y1)
    fall = np.clip(1.0 - (xx - 150) / 420.0, 0.3, 1.0)
    sel = lit & (bay < 0.45 * fall)
    # palette step: every lit pixel moves one step up the paper ramp (stays on the palette)
    ramp = np.stack([np.asarray(c, np.int32)[:3] for c in tone_ramp])
    rgb = cv.c[..., :3].astype(np.int32)
    d = ((rgb[:, :, None, :] - ramp[None, None, :, :]) ** 2).sum(-1)
    idx = np.clip(d.argmin(-1) + 1, 0, len(tone_ramp) - 1)
    up = np.stack([np.asarray(c, np.uint8) for c in tone_ramp])[idx]
    cv.c[sel] = up[sel]
    return lit
