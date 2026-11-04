"""env_berlin_fg -- foreground framing silhouettes for M1 (parallax 1.25, unlit, near-black).

Placement rule: fg screen x = X - 1.25 * cam_x.  For every hotspot, at the camera position that
centres the player on it (cam_x = clamp(hx - 320, 0, 960)), the silhouettes keep clear of a
120 px window around the hotspot (checked by check_clearance()).
"""
from __future__ import annotations

import math

import numpy as np

import env_berlin_kit as kit
import env_berlin_layout as L

R = kit.archive_ramps()
P = L.PARALLAX['fg_frame']


def column(lay, x0, x1, rim_left=False, rim_right=True, capital=True):
    H = L.WORLD_H
    w = x1 - x0
    lay.rect(x0, 0, w, H, 'N', 0.0, flat=True)
    lay.rect(x0 + 3, 0, w - 6, H, 'N', 1.0, flat=True)              # slightly lifted face
    for k in range(x0 + 6, x1 - 6, 6):                              # flutes (barely visible)
        lay.rect(k, 40, 1, H - 90, 'N', 0.0, flat=True)
    if capital:
        lay.rect(x0 - 6, 18, w + 12, 10, 'N', 0.0, flat=True)
        lay.rect(x0 - 4, 28, w + 8, 4, 'N', 1.0, flat=True)
    lay.rect(x0 - 5, H - 34, w + 10, 34, 'N', 0.0, flat=True)        # base
    lay.rect(x0 - 3, H - 38, w + 6, 4, 'N', 1.0, flat=True)
    if rim_right:
        lay.rect(x1 - 1, 32, 1, H - 70, 'W', 3.0, flat=True)
        lay.rect(x1 + 4, H - 34, 1, 34, 'W', 2.0, flat=True)
    if rim_left:
        lay.rect(x0, 32, 1, H - 70, 'W', 3.0, flat=True)


def rubber_plant(lay, cx, base):
    """Office rubber plant (Gummibaum) in a pot, silhouette with a cold rim from the windows."""
    # pot
    lay.poly([(cx - 12, base - 26), (cx + 12, base - 26), (cx + 9, base), (cx - 9, base)], 'N', 0.0)
    lay.rect(cx - 13, base - 29, 26, 4, 'N', 1.0, flat=True)
    lay.rect(cx - 13, base - 29, 1, 4, 'W', 2.0, flat=True)
    # stems
    stems = [[(cx, base - 28), (cx - 2, base - 70), (cx - 6, base - 110)],
             [(cx, base - 28), (cx + 4, base - 64), (cx + 10, base - 92)],
             [(cx - 1, base - 50), (cx - 12, base - 78)]]
    for st in stems:
        lay.polyline([(int(a), int(b)) for a, b in st], 'N', 1.0)
    # big ovate leaves
    rng = np.random.default_rng(9)
    leaves = [(-6, -112, 30), (10, -94, -25), (-12, -80, 40), (4, -70, -35), (-3, -56, 25), (12, -48, -40),
              (-14, -40, 55), (2, -100, -10), (-10, -98, 70), (14, -76, -55)]
    for (dx, dy, ang) in leaves:
        a = math.radians(ang)
        lx, ly = cx + dx, base + dy
        ln, wd = 13 + rng.uniform(-2, 3), 5.5
        pts = []
        for k in range(24):
            t = k / 23 * 2 * math.pi
            u = math.cos(t) * ln / 2
            v = math.sin(t) * wd / 2 * (1 - 0.35 * math.cos(t))
            pts.append((lx + u * math.cos(a) - v * math.sin(a), ly + u * math.sin(a) + v * math.cos(a)))
        m, x0, y0 = lay.poly(pts, 'N', 0.0)
        # rim on the upper-left edge (window light)
        e = kit.edge_of(m)
        hh, ww = m.shape
        yy, xx = np.mgrid[0:hh, 0:ww]
        upleft = (xx + yy) < (ww + hh) * 0.42
        lay.put(e & upleft, x0, y0, 'W', 2.6, flat=True)
        # midrib
        lay.line(lx - math.cos(a) * ln * 0.4, ly - math.sin(a) * ln * 0.4,
                 lx + math.cos(a) * ln * 0.4, ly + math.sin(a) * ln * 0.4, 'N', 1.0)


def desk_corner(lay, x0, x1, top):
    H = L.WORLD_H
    lay.rect(x0, top, x1 - x0, 6, 'N', 1.0, flat=True)                 # desk top edge
    lay.rect(x0, top, x1 - x0, 1, 'W', 2.4, flat=True)
    lay.rect(x0 + 6, top + 6, x1 - x0 - 12, H - top - 6, 'N', 0.0, flat=True)
    # books / file stack + an upturned chair back
    lay.rect(x0 + 10, top - 12, 22, 12, 'N', 0.0, flat=True)
    lay.rect(x0 + 13, top - 18, 16, 6, 'N', 1.0, flat=True)
    lay.rect(x0 + 10, top - 12, 22, 1, 'W', 1.6, flat=True)
    lay.rect(x1 - 30, top - 26, 3, 26, 'N', 0.0, flat=True)            # lamp post (off)
    lay.poly([(x1 - 38, top - 26), (x1 - 20, top - 26), (x1 - 24, top - 34), (x1 - 34, top - 34)], 'N', 1.0)


def chair_back(lay, x0, top):
    H = L.WORLD_H
    lay.rect(x0, top, 26, 5, 'N', 1.0, flat=True)
    lay.rect(x0, top, 26, 1, 'W', 2.0, flat=True)
    lay.rect(x0 + 2, top + 5, 3, H - top - 5, 'N', 0.0, flat=True)
    lay.rect(x0 + 21, top + 5, 3, H - top - 5, 'N', 0.0, flat=True)
    for k in range(4):
        lay.rect(x0 + 6 + k * 4, top + 5, 2, 18, 'N', 0.0, flat=True)
    lay.rect(x0 - 2, top + 26, 30, 4, 'N', 1.0, flat=True)


def boxes(lay, x0, base):
    lay.rect(x0, base - 22, 34, 22, 'N', 0.0, flat=True)
    lay.rect(x0 + 4, base - 38, 28, 16, 'N', 1.0, flat=True)
    lay.rect(x0 + 4, base - 38, 28, 1, 'W', 1.8, flat=True)
    lay.rect(x0, base - 22, 34, 1, 'W', 1.6, flat=True)
    lay.rect(x0 + 12, base - 31, 10, 4, 'N', 0.0, flat=True)          # handle hole


def pendant_silhouette(lay, cx, drop):
    lay.rect(cx, 0, 1, drop, 'N', 1.0, flat=True)
    lay.poly([(cx - 14, drop + 12), (cx + 15, drop + 12), (cx + 6, drop), (cx - 5, drop)], 'N', 0.0)
    lay.rect(cx - 14, drop + 12, 30, 1, 'N', 1.0, flat=True)


def wastebasket(lay, cx, base):
    lay.poly([(cx - 9, base - 20), (cx + 9, base - 20), (cx + 7, base), (cx - 7, base)], 'N', 0.0)
    for k in range(-6, 7, 3):
        lay.line(cx + k, base - 19, cx + int(k * 0.8), base - 1, 'N', 1.0)
    lay.rect(cx - 10, base - 21, 20, 2, 'N', 1.0, flat=True)
    lay.rect(cx - 4, base - 25, 7, 5, 'N', 1.0, flat=True)              # crumpled paper


def build():
    """Silhouettes are placed in the free zones between hotspot windows (see check_clearance): floor-standing
    shapes only between rooms, hanging shapes (lamps) anywhere above the playfield band."""
    w = L.layer_width(P)
    lay = kit.MLayer(w, L.WORLD_H, R, 'fg_frame')
    H = L.WORLD_H
    column(lay, -10, 30, rim_right=True)                 # far left: the building's end
    rubber_plant(lay, 560, H)                            # hall -> reading room arch
    pendant_silhouette(lay, 700, 18)                     # reading room, hanging
    pendant_silhouette(lay, 1180, 26)
    pendant_silhouette(lay, 1460, 14)
    column(lay, 1592, 1632, rim_left=True, rim_right=True)   # reading room | office partition
    wastebasket(lay, 2085, H)
    rubber_plant(lay, 2270, H)
    desk_corner(lay, 2363, 2491, 322)
    pendant_silhouette(lay, 2615, 22)
    chair_back(lay, 2800, 318)
    column(lay, 3110, 3150, rim_left=True, rim_right=False)
    boxes(lay, 3472, H)
    column(lay, w - 46, w + 10, rim_left=True, rim_right=False)
    lay.unlit[:] = True
    lay.resolve()
    return lay


def check_clearance(lay, margin: int = 60):
    """Return list of (hotspot, cam_x, covered_px) where fg pixels cover the hotspot zone."""
    alpha = lay.rid >= 0
    issues = []
    for name, (hx, hy) in L.HOTSPOTS.items():
        cx = int(L.cam_for(hx))
        sx = hx - cx
        X0 = int(round(sx - margin + P * cx))
        X1 = int(round(sx + margin + P * cx))
        y0, y1 = 236, 306
        sub = alpha[y0:y1, max(0, X0):max(0, X1)]
        n = int(sub.sum())
        if n:
            issues.append((name, cx, n))
    return issues
