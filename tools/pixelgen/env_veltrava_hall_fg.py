"""env_veltrava_hall_fg -- foreground framing silhouettes for L_C3_Hall (parallax 1.25, unlit, near-black).

Placement rule: fg screen x = X - 1.25 * cam_x.  For every hotspot (and the spawn), at the camera that
centres the player on it (cam_x = clamp(hx - 320, 0, 1280)), nothing of this layer may cover a 120 px
window around it in the figure band y 236..306 (check_clearance()).  Top drapes only hang from the top
edge and stay above y 120.
"""
from __future__ import annotations

import math

import numpy as np

import env_veltrava_hall_kit as kit
import env_veltrava_hall_layout as L

R = kit.palais_ramps()
P = L.PARALLAX['fg_frame']


def column(lay, x0, x1, rim_left=False, rim_right=True):
    H = L.WORLD_H
    w = x1 - x0
    lay.rect(x0, 0, w, H, 'N', 0.0)
    lay.rect(x0 + 3, 0, w - 6, H, 'N', 1.0)
    for k in range(x0 + 6, x1 - 6, 5):                               # flutes
        lay.rect(k, 46, 1, H - 100, 'N', 0.0)
    lay.rect(x0 - 7, 22, w + 14, 10, 'N', 0.0)                       # capital
    lay.rect(x0 - 5, 32, w + 10, 5, 'N', 1.0)
    lay.rect(x0 - 6, H - 36, w + 12, 36, 'N', 0.0)                   # base
    lay.rect(x0 - 4, H - 40, w + 8, 4, 'N', 1.0)
    if rim_right:
        lay.rect(x1 - 1, 37, 1, H - 77, 'W', 3.0)
        lay.rect(x1 + 5, H - 36, 1, 36, 'W', 2.2)
    if rim_left:
        lay.rect(x0, 37, 1, H - 77, 'W', 3.0)
        lay.rect(x0 - 6, H - 36, 1, 36, 'W', 2.2)


def drape(lay, x0, x1, depth, seed, side='left'):
    """Heavy velvet swag hanging from the top edge with a tassel (dark wine silhouette, cold rim)."""
    rng = np.random.default_rng(seed)
    w = x1 - x0
    for x in range(x0, x1):
        u = (x - x0) / max(1, w - 1)
        hang = depth * (0.35 + 0.65 * (u if side == 'left' else 1 - u)) + 4 * math.sin(u * math.pi * 3)
        hh = int(round(hang))
        fold = (x - x0) % 6
        t = 1.0 if fold in (1, 2) else 0.0
        lay.rect(x, 0, 1, hh, 'R', t)
        lay.px(x, hh, 'R', 1.0)
    # swag (draped valance) + fringe
    for x in range(x0, x1):
        u = (x - x0) / max(1, w - 1)
        sy = int(round(10 + 8 * math.sin(u * math.pi)))
        lay.rect(x, 0, 1, sy, 'N', 1.0)
        if x % 2 == 0:
            lay.px(x, sy, 'B', 1.2)
    tx = x1 - 6 if side == 'left' else x0 + 4
    ty = int(round(depth * 0.9))
    lay.rect(tx, ty, 2, 10, 'N', 0.0)
    lay.rect(tx - 2, ty + 10, 6, 6, 'N', 0.0)
    lay.px(tx - 2, ty + 15, 'B', 1.4)
    rim = (x0 + 2) if side == 'left' else (x1 - 3)
    lay.rect(rim, 18, 1, int(depth * 0.5), 'W', 2.4)


def palm(lay, cx, base, seed=9, scale=1.0):
    """Kentia palm in a jardiniere, near-black silhouette, a cold rim from the windows."""
    rng = np.random.default_rng(seed)
    lay.poly([(cx - 13, base - 28), (cx + 13, base - 28), (cx + 10, base), (cx - 10, base)], 'N', 0.0)
    lay.rect(cx - 14, base - 31, 28, 4, 'N', 1.0)
    lay.rect(cx - 14, base - 31, 1, 4, 'W', 2.2)
    for k in range(11):
        ang = math.radians(-168 + k * 15 + rng.uniform(-6, 6))
        ln = rng.uniform(46, 66) * scale
        pts = []
        for j in range(18):
            t = j / 17
            pts.append((cx + math.cos(ang) * ln * t, base - 30 + math.sin(ang) * ln * t + (t ** 2) * ln * 0.6))
        for (a, b) in zip(pts[:-1], pts[1:]):
            lay.line(a[0], a[1], b[0], b[1], 'N', 0.0)
        for j in range(4, 18):
            px_, py_ = pts[j]
            for s in (-1, 1):
                ll = 6 + (j % 4)
                lay.line(px_, py_, px_ + s * 2, py_ + ll, 'N', 1.0 if s < 0 else 0.0)
        if k < 5:
            for j in range(5, 16, 2):
                lay.px(pts[j][0], pts[j][1] - 1, 'W', 2.0)


def chair(lay, x0, top):
    H = L.WORLD_H
    lay.rect(x0, top, 30, 6, 'N', 1.0)
    lay.rect(x0, top, 30, 1, 'D', 1.6)
    lay.rect(x0 + 3, top + 6, 24, 18, 'R', 0.0)                     # upholstered back
    lay.rect(x0 + 2, top + 6, 2, H - top - 6, 'N', 0.0)
    lay.rect(x0 + 26, top + 6, 2, H - top - 6, 'N', 0.0)
    lay.rect(x0 - 2, top + 28, 34, 5, 'N', 1.0)


def build():
    w = L.layer_width(P)
    lay = kit.TLayer(w, L.WORLD_H, R, 'fg_frame')
    H = L.WORLD_H
    column(lay, -30, 8, rim_right=True)
    drape(lay, -10, 64, 70, seed=1, side='left')
    palm(lay, 431, H, seed=4, scale=0.9)
    drape(lay, 1160, 1236, 66, seed=2, side='right')
    column(lay, 1694, 1730, rim_left=True, rim_right=False)
    chair(lay, 2100, 300)
    column(lay, w - 40, w + 10, rim_left=True, rim_right=False)
    lay.unlit[:] = True
    lay.resolve()
    return lay


def check_clearance(lay, margin: int = 60):
    alpha = lay.rid >= 0
    issues = []
    pts = dict(L.HOTSPOTS)
    pts.update({k: v for k, v in L.SPAWNS.items()})
    for name, (hx, hy) in pts.items():
        cx = int(min(max(hx - L.VIEW_W // 2, 0), L.WORLD_W - L.VIEW_W))
        sx = hx - cx
        X0 = int(round(sx - margin + P * cx))
        X1 = int(round(sx + margin + P * cx))
        sub = alpha[236:306, max(0, X0):max(0, X1)]
        n = int(sub.sum())
        if n:
            issues.append((name, cx, n))
    return issues
