"""env_veltrava_hall_fx -- seamless looping sprite strips for L_C3_Hall (fx type 'anim_sprite').

fx_snow_square.png    snowfall over the square, BEHIND the room layer -> only seen through the entrance glass
fx_snow_river.png     snowfall in front of the river view (foyer window, office window)
fx_dust_vestibule.png dust motes hovering in the entrance daylight
fx_dust_foyer.png     dust motes in the lunette / tall-window shafts of the foyer
fx_dust_office.png    dust motes in the office window shaft
fx_glints.png         crystal glints on the chandelier (2 slow cycles per loop, never a strobe)
Every element moves on a closed path, so each 16-frame loop has no seam.
"""
from __future__ import annotations

import math
import os

import numpy as np

import env_veltrava_hall_kit as kit
import env_veltrava_hall_layout as L
import pg

SNOW_SQ_P = 0.5
SNOW_RV_P = 0.45


def snow_strip(w, h, frames=16, seed=11, density=520):
    rng = np.random.default_rng(seed)
    far = [pg.hx(c) for c in (kit.VELT['snow'][1], kit.VELT['snow'][2])]
    near = [pg.hx(c) for c in (kit.VELT['snow'][3], kit.VELT['snow'][4])]
    flakes = []
    for _ in range(int(w * h / density)):
        nr = rng.random() < 0.3
        flakes.append({'x': rng.uniform(0, w), 'y': rng.uniform(0, h), 'near': nr, 'laps': 2 if nr else 1,
                       'amp': rng.uniform(1.0, 3.0), 'ph': rng.uniform(0, 2 * math.pi),
                       'drift': int(rng.integers(0, 2)) * (1 if rng.random() < 0.7 else -1),
                       'c': (near if nr else far)[int(rng.integers(0, 2))]})
    strip = np.zeros((h, w * frames, 4), np.uint8)
    for f in range(frames):
        u = f / frames
        for fl in flakes:
            y = (fl['y'] + u * h * fl['laps']) % h
            x = (fl['x'] + fl['amp'] * math.sin(2 * math.pi * u + fl['ph']) + fl['drift'] * u * w) % w
            xi, yi = int(x), int(y)
            s = 2 if fl['near'] else 1
            strip[yi:yi + s, f * w + xi:f * w + min(w, xi + s)] = fl['c']
    return strip


def motes_strip(rect, density_fn, n, colors, frames=16, seed=0, radius=(1.5, 4.0)):
    x0, y0, w, h = rect
    rng = np.random.default_rng(seed)
    motes = []
    tries = 0
    while len(motes) < n and tries < n * 60:
        tries += 1
        x, y = rng.uniform(0, w), rng.uniform(0, h)
        if rng.random() < density_fn(x0 + x, y0 + y):
            motes.append({'x': x, 'y': y, 'r': rng.uniform(*radius), 'ph': rng.uniform(0, 2 * math.pi),
                          'tw': rng.uniform(0, 2 * math.pi), 'c': colors[int(rng.integers(0, len(colors)))],
                          'dir': rng.choice([-1, 1])})
    strip = np.zeros((h, w * frames, 4), np.uint8)
    for f in range(frames):
        u = f / frames
        for m in motes:
            a = 2 * math.pi * u * m['dir'] + m['ph']
            x = m['x'] + m['r'] * math.cos(a)
            y = m['y'] + m['r'] * 0.6 * math.sin(a)
            vis = 0.5 + 0.5 * math.sin(2 * math.pi * u * 2 + m['tw'])
            if vis < 0.35:
                continue
            xi, yi = int(round(x)), int(round(y))
            if 0 <= xi < w and 0 <= yi < h:
                c = m['c'].copy()
                c[3] = int(140 + 100 * vis)
                strip[yi, f * w + xi] = c
    return strip


def glints_strip(points, w, h, frames=16, seed=4):
    """Soft twinkle on a few crystal drops: each glint fades in/out once or twice per loop (no strobe)."""
    rng = np.random.default_rng(seed)
    strip = np.zeros((h, w * frames, 4), np.uint8)
    cols = [pg.hx(kit.PALAIS['daylight'][5]), pg.hx(kit.PALAIS['amber'][4])]
    for (x, y) in points:
        ph = rng.uniform(0, 1)
        c = cols[int(rng.integers(0, 2))]
        cyc = int(rng.integers(1, 3))
        for f in range(frames):
            v = 0.5 + 0.5 * math.sin(2 * math.pi * (f / frames * cyc + ph))
            if v < 0.55:
                continue
            a = int(120 + 120 * (v - 0.55) / 0.45)
            cc = c.copy(); cc[3] = a
            strip[y, f * w + x] = cc
            if v > 0.9:
                for (dx, dy) in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    xx, yy = x + dx, y + dy
                    if 0 <= xx < w and 0 <= yy < h:
                        c2 = c.copy(); c2[3] = 90
                        strip[yy, f * w + xx] = c2
    return strip


def build_all(env_dir, room):
    out, fx = [], []
    os.makedirs(env_dir, exist_ok=True)
    # --- snow over the square (behind the entrance glass)
    pos_sq = -50
    w, y0, y1 = 170, 34, 292
    strip = snow_strip(w, y1 - y0, seed=11)
    p = os.path.join(env_dir, 'fx_snow_square.png')
    kit.save_rgba(strip, p)
    out.append((p, 'snowfall over the square, seen through the entrance glazing (16-frame loop)'))
    fx.append({'type': 'anim_sprite', 'file': 'fx_snow_square.png', 'frames': 16, 'fps': 6, 'pos': [pos_sq, y0],
               'parallax': [SNOW_SQ_P, 1.0], 'z': -88, 'lit': False,
               'note': 'between ext_square (z -90) and room (z -50): only visible through the glass'})
    # --- snow in front of the river view (foyer window + office window)
    pos_rv = 350
    w2, ry0, ry1 = 580, 64, 254
    strip = snow_strip(w2, ry1 - ry0, seed=12, density=640)
    p = os.path.join(env_dir, 'fx_snow_river.png')
    kit.save_rgba(strip, p)
    out.append((p, 'snowfall in front of the river view (foyer + office windows, 16-frame loop)'))
    fx.append({'type': 'anim_sprite', 'file': 'fx_snow_river.png', 'frames': 16, 'fps': 6, 'pos': [pos_rv, ry0],
               'parallax': [SNOW_RV_P, 1.0], 'z': -93, 'lit': False,
               'note': 'between ext_river (z -95) and the square/Saal layers: only visible through the glass'})
    # --- dust motes in the daylight shafts
    air = room.shaft_air
    glass = room.glass

    def dens_factory(power=1.4):
        def dens(x, y):
            x, y = int(x), int(y)
            if not (0 <= x < air.shape[1] and 0 <= y < air.shape[0]):
                return 0.0
            if glass[max(0, y - 6):y + 6, max(0, x - 6):x + 6].any():
                return 0.0
            return float(np.clip(air[y, x], 0, 1)) ** power
        return dens
    cold = [pg.hx(kit.PALAIS['daylight'][5]), pg.hx(kit.PALAIS['paper'][5])]
    warm = [pg.hx(kit.PALAIS['amber'][3]), pg.hx(kit.PALAIS['amber'][4])]
    for name, rect, n, seed, cols, desc in (
            ('fx_dust_vestibule', (16, 60, 300, 236), 40, 21, cold, 'dust motes in the entrance daylight'),
            ('fx_dust_foyer', (470, 40, 480, 250), 56, 22, cold + warm[:1], 'dust motes in the foyer shafts'),
            ('fx_dust_office', (1170, 110, 170, 180), 18, 23, cold, 'dust motes in the office window shaft')):
        strip = motes_strip(rect, dens_factory(), n, cols, seed=seed)
        p = os.path.join(env_dir, name + '.png')
        kit.save_rgba(strip, p)
        out.append((p, desc + ' (16-frame loop)'))
        fx.append({'type': 'anim_sprite', 'file': name + '.png', 'frames': 16, 'fps': 5,
                   'pos': [rect[0], rect[1]], 'parallax': [1.0, 1.0], 'z': 12, 'lit': False})
    # --- chandelier glints
    cx, bot = L.CHANDELIER
    gx0, gy0, gw, gh = cx - 28, bot - 74, 57, 76
    pts = []
    rng = np.random.default_rng(31)
    for _ in range(14):
        pts.append((int(rng.integers(4, gw - 4)), int(rng.integers(26, gh - 2))))
    strip = glints_strip(pts, gw, gh)
    p = os.path.join(env_dir, 'fx_glints.png')
    kit.save_rgba(strip, p)
    out.append((p, 'slow crystal glints on the foyer chandelier (16-frame loop)'))
    fx.append({'type': 'anim_sprite', 'file': 'fx_glints.png', 'frames': 16, 'fps': 3, 'pos': [gx0, gy0],
               'parallax': [1.0, 1.0], 'z': -40, 'lit': False})
    return out, fx
