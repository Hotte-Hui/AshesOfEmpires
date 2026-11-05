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


SNOW_TILE = 160
SNOW_Y = (80, 256)


def snow_strip(frames=16, seed=11):
    """Seamless snowfall TILE (wraps horizontally and vertically): placed side by side behind every window."""
    w = SNOW_TILE
    y0, y1 = SNOW_Y
    h = y1 - y0
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
            s_ = 2 if fl['near'] else 1
            for dy in range(s_):
                for dx in range(s_):
                    strip[(yi + dy) % h, f * w + (xi + dx) % w] = fl['c']
    return strip, (0, y0), (w, h)


def snow_span():
    """local-x span (parallax SNOW_P) that any window can show, for every camera position"""
    lo, hi = 1e9, -1e9
    for (x0, x1) in L.ALL_WINDOWS:
        lo = min(lo, x0 - (1 - SNOW_P) * x1)
        hi = max(hi, x1 - (1 - SNOW_P) * max(0, x0 - L.VIEW_W))
    return int(math.floor(lo / 8) * 8) - 8, int(math.ceil(hi)) + 8


def smoke_curl_strip(frames=16, seed=31, w=16, h=36):
    """Cigarette smoke from a point at the bottom centre (16-frame seamless loop): a thin laminar thread for
    the first third, then it breaks into slow curls that widen, drift right and fade."""
    cols = [kit.pg.hx('#DEE5DC'), kit.pg.hx('#A7BCCB'), kit.pg.hx('#7A93A8')]
    strip = np.zeros((h, w * frames, 4), np.uint8)
    rng = np.random.default_rng(seed)
    ph = rng.uniform(0, 2 * math.pi, 60)
    for f in range(frames):
        u = f / frames
        for k in range(60):
            t = (k / 60.0 + u / 4.0) % 1.0                 # particles stream upward (4 loops per particle cycle)
            y = h - 1 - t * (h - 3)
            lam = 0.3
            if t < lam:
                sway = math.sin(t * 9.0 + 2 * math.pi * u) * 0.35
            else:
                tt = (t - lam) / (1 - lam)
                sway = (math.sin(tt * 6.5 + 2 * math.pi * u + ph[k] * 0.3) * (0.8 + tt * 3.4)
                        + tt * 3.0)                          # drift toward the window side
            x = w / 2 - 2 + sway
            a = (1 - t) ** 0.9
            size = 1 if t < 0.55 else 2
            if t > lam and (k + f) % 3 == 0:
                continue
            xi, yi = int(round(x)), int(round(y))
            for dy in range(size):
                for dx in range(size):
                    X, Y = xi + dx, yi - dy
                    if 0 <= X < w and 0 <= Y < h and strip[Y, f * w + X, 3] == 0:
                        c = cols[0 if t < 0.3 else (1 if t < 0.65 else 2)].copy()
                        c[3] = int(40 + 120 * a)
                        strip[Y, f * w + X] = c
    return strip


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
    # window snow: one seamless tile, repeated over the span every window can show
    strip, (sx, sy), (w, h) = snow_strip()
    p = os.path.join(env_dir, 'fx_window_snow.png')
    kit.save_rgba(strip, p)
    out.append((p, 'seamless snowfall tile seen through the windows (16-frame loop, behind the room layer)'))
    lo, hi = snow_span()
    for x in range(lo, hi, SNOW_TILE):
        fx.append({'type': 'anim_sprite', 'file': 'fx_window_snow.png', 'frames': 16, 'fps': 6, 'pos': [x, sy],
                   'parallax': [SNOW_P, 1.0], 'z': -88, 'lit': False,
                   'note': 'between ext_near (z -90) and room (z -50): only visible through the glass'})
    air = room.shaft_air

    def dens_for(windows):
        def dens(x, y):
            x, y = int(x), int(y)
            if not (0 <= x < air.shape[1] and 0 <= y < air.shape[0]):
                return 0.0
            for (a, b) in windows:                        # not over the glass
                wy0, wy1 = L.win_y(a)
                if a - 6 <= x < b + 6 and wy0 - 8 <= y < wy1 + 2:
                    return 0.0
            return float(np.clip(air[y, x], 0, 1)) ** 1.5
        return dens
    cols = [kit.pg.hx(kit.A['blue'][5]), kit.pg.hx('#DEE5DC')]
    for (name, rect, wins, n, seed) in (
            ('fx_dust_office.png', (L.X(104), 84, 360, 210), L.WINDOWS, 46, 21),
            ('fx_dust_library.png', (700, 84, 460, 214), L.LIB_WINDOWS, 40, 23),
            ('fx_dust_hall.png', (300, 84, 120, 210), L.HALL_WINDOWS, 16, 24)):
        strip = motes_strip(rect, dens_for(wins), n, cols, seed=seed)
        p = os.path.join(env_dir, name)
        kit.save_rgba(strip, p)
        out.append((p, 'dust motes hovering in the window shafts (16-frame loop)'))
        fx.append({'type': 'anim_sprite', 'file': name, 'frames': 16, 'fps': 5,
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
    # motes in the green lamp light of the reading table
    rect3 = (L.LIB_READ_TABLE[0] + 4, 228, 76, 40)

    def dens3(x, y):
        best = 0.0
        for lx in (L.LIB_READ_TABLE[0] + 17, L.LIB_READ_TABLE[1] - 17):
            dx = abs(x - lx) / (6 + (y - 228) * 0.5)
            best = max(best, 1 - dx)
        return float(np.clip(best, 0, 1))
    cols3 = [kit.pg.hx(kit.GREEN[5]), kit.pg.hx(kit.A['amber'][5])]
    strip3 = motes_strip(rect3, dens3, 10, cols3, seed=25, radius=(1.0, 2.0))
    p = os.path.join(env_dir, 'fx_dust_reading.png')
    kit.save_rgba(strip3, p)
    out.append((p, 'motes in the green reading-lamp light (16-frame loop)'))
    fx.append({'type': 'anim_sprite', 'file': 'fx_dust_reading.png', 'frames': 16, 'fps': 4,
               'pos': [rect3[0], rect3[1]], 'parallax': [1.0, 1.0], 'z': 12, 'lit': False})
    return out, fx


def build_smoke(actor_dir):
    """cigarette smoke curl strip for the porter's ashtray (used by an anim actor, y-sorted)"""
    strip = smoke_curl_strip()
    p = os.path.join(actor_dir, 'smoke_curl.png')
    kit.save_rgba(strip, p)
    return p
