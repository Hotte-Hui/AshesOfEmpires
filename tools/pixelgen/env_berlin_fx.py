"""env_berlin_fx -- seamless looping sprite strips for M1 (consumed as fx type 'anim_sprite').

fx_window_snow.png   snowfall in the street, drawn BEHIND the room layer (z between ext_near and room)
                     so it is only visible through the window glass.  Parallax 0.3.
fx_dust_office.png   dust motes hovering in the window shafts (only where the shafts are dense).
fx_dust_archive.png  warm motes under the archive pendant lamp.
All strips: hframes, every element moves on a closed path -> the loop has no seam.
"""
from __future__ import annotations

import math
import os

import numpy as np

import env_berlin_kit as kit
import env_berlin_layout as L

SNOW_P = 0.3


def snow_strip(frames=16, seed=11):
    # local x range seen through the windows for camera x in [0, 404]: world_x - (1-p)*cam_x
    x0 = int(math.floor(L.WINDOWS[0][0] - (1 - SNOW_P) * L.WINDOWS[-1][1])) - 8
    x1 = L.WINDOWS[-1][1] + 8
    y0, y1 = L.WIN_Y[0] - 4, L.WIN_Y[1] + 4
    w, h = x1 - x0, y1 - y0
    rng = np.random.default_rng(seed)
    cols_far = [kit.pg.hx(c) for c in (kit.B['snow'][1], kit.B['snow'][2])]
    cols_near = [kit.pg.hx(c) for c in (kit.B['snow'][3], kit.B['snow'][4])]
    flakes = []
    for _ in range(int(w * h / 520)):
        near = rng.random() < 0.3
        flakes.append({'x': rng.uniform(0, w), 'y': rng.uniform(0, h), 'near': near,
                       'laps': 2 if near else 1, 'amp': rng.uniform(1.0, 3.0), 'ph': rng.uniform(0, 2 * math.pi),
                       'drift': int(rng.integers(0, 2)) * (1 if rng.random() < 0.7 else -1),
                       'c': (cols_near if near else cols_far)[int(rng.integers(0, 2))]})
    strip = np.zeros((h, w * frames, 4), np.uint8)
    for f in range(frames):
        u = f / frames
        for fl in flakes:
            y = (fl['y'] + u * h * fl['laps']) % h
            x = (fl['x'] + fl['amp'] * math.sin(2 * math.pi * u + fl['ph']) + fl['drift'] * u * w) % w
            xi, yi = int(x), int(y)
            s = 2 if fl['near'] else 1
            strip[yi:yi + s, f * w + xi:f * w + min(w, xi + s)] = fl['c']
    return strip, (x0, y0), (w, h)


def motes_strip(rect, density_fn, n, colors, frames=16, seed=0, radius=(1.5, 4.0)):
    x0, y0, w, h = rect
    rng = np.random.default_rng(seed)
    motes = []
    tries = 0
    while len(motes) < n and tries < n * 50:
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
            vis = 0.5 + 0.5 * math.sin(2 * math.pi * u * 2 + m['tw'])     # twinkle (2 cycles/loop)
            if vis < 0.35:
                continue
            xi, yi = int(round(x)), int(round(y))
            if 0 <= xi < w and 0 <= yi < h:
                c = m['c'].copy()
                c[3] = int(150 + 105 * vis)
                strip[yi, f * w + xi] = c
    return strip


def build_all(env_dir, room):
    out = []
    os.makedirs(env_dir, exist_ok=True)
    fx = []
    # window snow
    strip, (sx, sy), (w, h) = snow_strip()
    p = os.path.join(env_dir, 'fx_window_snow.png')
    kit.save_rgba(strip, p)
    out.append((p, 'snowfall seen through the windows (16-frame loop, behind the room layer)'))
    fx.append({'type': 'anim_sprite', 'file': 'fx_window_snow.png', 'frames': 16, 'fps': 6, 'pos': [sx, sy],
               'parallax': [SNOW_P, 1.0], 'z': -88, 'lit': False,
               'note': 'between ext_near (z -90) and room (z -50): only visible through the glass'})
    # office shaft motes
    air = room.shaft_air
    rect = (104, 84, 360, 210)

    def dens(x, y):
        x, y = int(x), int(y)
        if not (0 <= x < air.shape[1] and 0 <= y < air.shape[0]):
            return 0.0
        for (a, b) in L.WINDOWS:                        # not over the glass
            if a - 6 <= x < b + 6 and L.WIN_Y[0] - 8 <= y < L.WIN_Y[1] + 2:
                return 0.0
        return float(np.clip(air[y, x], 0, 1)) ** 1.5
    cols = [kit.pg.hx(kit.A['blue'][5]), kit.pg.hx('#DEE5DC')]
    strip = motes_strip(rect, dens, 46, cols, seed=21)
    p = os.path.join(env_dir, 'fx_dust_office.png')
    kit.save_rgba(strip, p)
    out.append((p, 'dust motes hovering in the window shafts (16-frame loop)'))
    fx.append({'type': 'anim_sprite', 'file': 'fx_dust_office.png', 'frames': 16, 'fps': 5,
               'pos': [rect[0], rect[1]], 'parallax': [1.0, 1.0], 'z': 12, 'lit': False})
    # archive pendant motes (warm)
    rect2 = (L.HOTSPOTS['plan_b'][0] - 42, 196, 84, 56)

    def dens2(x, y):
        cx = L.HOTSPOTS['plan_b'][0]
        dx = abs(x - cx) / (8 + (y - 196) * 0.55)
        return float(np.clip(1 - dx, 0, 1))
    cols2 = [kit.pg.hx(kit.A['amber'][4]), kit.pg.hx(kit.A['amber'][5])]
    strip2 = motes_strip(rect2, dens2, 14, cols2, seed=22, radius=(1.0, 2.5))
    p = os.path.join(env_dir, 'fx_dust_archive.png')
    kit.save_rgba(strip2, p)
    out.append((p, 'warm dust motes under the archive pendant (16-frame loop)'))
    fx.append({'type': 'anim_sprite', 'file': 'fx_dust_archive.png', 'frames': 16, 'fps': 4,
               'pos': [rect2[0], rect2[1]], 'parallax': [1.0, 1.0], 'z': 12, 'lit': False})
    return out, fx
