"""env_c3p2_archive_fx -- animated strips and overlay layers of L_C3_Registry (night calm -> smoke -> fire).

Every strip is a horizontal row of frames (layer_stack.gd: hframes = frames) and loops seamlessly: noise is
periodic in the loop direction, particles live exactly one loop (or an integer fraction of it).  Colours are
palette-pure ('registry').  Round 13: everything that burns comes from the pixel fire kit (pixel_fire.py through
pixel_fire_bake.py) -- designed tongues with merged colour bands and an emission twin of their hot core, smoke as
hard-pixel billows and puffs (three tones, ordered dither instead of alpha), sparks instead of a heat shimmer;
the kit's white-hot core and smoke tones are the films' (LS_C3_Fire plays in this room).  Only the night
shafts are still soft veils with a few alpha levels.  Accessibility: no strip pulses its overall
brightness; ember brightness changes along each ember's life only (well below 3 Hz).
"""
from __future__ import annotations

import math
import os

import numpy as np
from PIL import Image

import env_c3p2_archive_kit as K
import env_c3p2_archive_layout as L
import pg
import pixel_fire as PF
import pixel_fire_bake as PFB

R = K.R


def _rgba(ramp, idx):
    return R.table[R[ramp], int(np.clip(idx, 0, R.n(ramp) - 1))].copy()


def save(arr, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    Image.fromarray(arr.astype(np.uint8), 'RGBA').save(path)


def strip(frames_list):
    return np.concatenate(frames_list, axis=1)


# =========================================================================== flames
def flame_strip(w, h, seed, frames=16, spots=(), base=0.15, height=0.85):
    """Fire over a fuel line as pixel art (pixel_fire_bake.flames): a tongue at every burning spot
    (x, half width, strength), forks, a bed of embers, low fire along the line (base > 0); the colour bands of
    all tongues are merged, so the strip reads as one mass with hot cores.  Returns (rgba strip, emission
    strip = the hot core only: added on top it lifts the core, rim and body stay pure palette)."""
    fr = PFB.flames(w, h, frames, list(spots), seed, height=height, base=base)
    return strip(fr), strip(PFB.hot(fr))


# =========================================================================== particles
def particles(w, h, frames, fps, n, seed, kind='ember', spawn=None, vy=(-24, -12), vx=(-3, 3), life=None,
              sway=2.0, cols=None):
    """Looping particle strip.  Each particle lives `life` s (default = one loop) and repeats with the loop.
    kind 'ember' (rising, fire colours, bright core) | 'ash' (falling grey flakes, some still glowing) |
    'snow' (falling flakes) | 'dust' (slow drift)."""
    rng = np.random.default_rng(seed)
    T = frames / float(fps)
    out = np.zeros((frames, h, w, 4), np.uint8)
    for i in range(n):
        m = int(rng.integers(1, 3)) if kind in ('ember', 'dust') else 1
        L_ = T / m if life is None else life
        ph = rng.uniform(0, L_)
        if spawn is not None:
            x0, y0 = spawn(rng)
        else:
            x0, y0 = rng.uniform(0, w), rng.uniform(0, h)
        v_y = rng.uniform(*vy)
        v_x = rng.uniform(*vx)
        sw = rng.uniform(0.3, 1.0) * sway
        sp = rng.uniform(0.4, 1.1)
        big = rng.random() < (0.18 if kind != 'dust' else 0.05)
        for k in range(frames):
            age = ((k / fps) + ph) % L_
            a = age / L_
            x = x0 + v_x * age + sw * math.sin(2 * math.pi * (age * sp) + i)
            y = y0 + v_y * age
            if kind in ('snow', 'ash', 'dust'):
                y = y % h if kind == 'snow' else y
            xi, yi = int(round(x)) % w if kind == 'snow' else int(round(x)), int(round(y))
            if not (0 <= xi < w and 0 <= yi < h):
                continue
            fade = min(1.0, a / 0.15, (1 - a) / 0.2)
            if kind == 'ember':
                idx = 6 if fade > 0.75 else (5 if fade > 0.45 else (4 if fade > 0.2 else 3))
                c = _rgba('F', idx)
            elif kind == 'ash':
                if a < 0.25 and i % 3 == 0:
                    c = _rgba('F', 4 if a < 0.12 else 3)
                else:
                    c = _rgba('W', 6 if fade > 0.6 else 5) if i % 2 else _rgba('S', 5 if fade > 0.6 else 4)
            elif kind == 'snow':
                c = _rgba('SN', 6 if big else (5 if fade > 0.5 else 3))
            else:
                c = _rgba('P', 5 if fade > 0.6 else 4)
            if fade <= 0.05:
                continue
            out[k, yi, xi] = c
            if big and 0 <= xi + 1 < w:
                out[k, yi, xi + 1] = c
                if kind == 'snow' and yi + 1 < h:
                    out[k, yi + 1, xi] = c
    return strip(list(out))


# =========================================================================== smoke
def smoke_layer(w, h, bottom, dens, seed, glow_x=None, glow_k=0.0, x_off=0):
    """Still smoke under the ceiling (pixel_fire_bake.ceiling): bottom(x) = lower edge (y), dens(x) = 0..1.
    Hard pixels: a solid bank with billows along its underside that frays out through the ordered dither, a
    veil where it is thin; fire-lit tones within reach of glow_x, the night's greys elsewhere."""
    xs = np.arange(w, dtype=np.float32) + x_off
    warm = None if glow_x is None else np.clip(1.15 - np.abs(xs - glow_x) / 640.0, 0, 1) * min(1.0, glow_k + 0.1)
    return PFB.ceiling(w, h, np.asarray(bottom, np.float32) * 0.86, seed, tones=PF.SMOKE_WARM, cool=PF.SMOKE_GREY,
                       warm=warm, dens=dens, x_off=x_off)


def smoke_roll_strip(w, h, frames, seed, speed=2, glow=0.0):
    """Smoke rolling along under the vaults (toward the cold side, i.e. to the left): a stretch of the kit's
    bank (pixel_fire_bake.drift) that moves half its length per loop and dissolves at both ends through the
    ordered dither; fire-lit near the fire (glow), grey and thinner further away."""
    return strip(PFB.drift(w, h, frames, seed, tones=PF.SMOKE_WARM if glow >= 0.5 else PF.SMOKE_GREY, shift=-1,
                           thin=0.0 if glow >= 0.5 else 0.25, top=0.34))


def smoke_wisp_strip(w, h, frames, seed, drift=(0.0, -1.0), dens=1.0, glow=0.0):
    """A plume rising from the bottom of the cell (pixel_fire_bake.column): puffs that swell, climb, lean a
    little and break up through the ordered dither -- fire-lit while they are young (glow), grey above."""
    s2 = max(12, int(w * 0.65))
    return strip(PFB.column(w, h, frames, (w / 2.0, h - 0.16 * s2), (w / 2.0 + 0.08 * w, 0.3 * s2), seed,
                            tones=PF.SMOKE_WARM if glow > 0.2 else PF.SMOKE_GREY, cool=PF.SMOKE_GREY,
                            sizes=(max(10, int(w * 0.45)), max(11, int(w * 0.55)), s2), count=6, loops=2,
                            sway=0.05 * w))


def bell_strip():
    """Ringing fire bell: the striker hammering against the dome (4 frames, small motion, no flashing)."""
    w, h = 16, 12
    fr = []
    dome = []
    for i in range(9):
        half = int(round(5.5 * math.sqrt(max(0.0, 1 - ((8 - i) / 9.0) ** 2))))
        dome.append(half)
    for k in range(4):
        a = np.zeros((h, w, 4), np.uint8)
        off = (0, 1, 0, -1)[k]
        for i, half in enumerate(dome):
            for x in range(8 - half + off, 8 + half + 1 + off):
                if 0 <= x < w:
                    a[i + 1, x] = _rgba('R', 3 if i < 3 else 2)
        sx = 13 if k % 2 == 0 else 14
        a[9, sx - 1:sx + 2] = _rgba('S', 5)
        a[10, sx - 1:sx + 2] = _rgba('S', 3)
        fr.append(a)
    return strip(fr)


def guard_feet_strip(w=26, h=34, frames=80):
    """Boots and coat hem of a guard walking past a high window at pavement height: across, a pause, back again,
    a pause -- like a pendulum (exp_window_feet).  Placed behind the window bars (between outside.png and the
    room layer)."""
    fr = []
    walk = 20
    plan = [(k, 1) for k in range(walk)] + [None] * 16 + [(k, -1) for k in range(walk)] + [None] * (frames - 2 * walk - 16)
    for step in plan[:frames]:
        a = np.zeros((h, w, 4), np.uint8)
        if step is not None:
            k, d = step
            x = -10 + (w + 18) * k / (walk - 1)
            if d < 0:
                x = w + 8 - (w + 18) * k / (walk - 1)
            ph = k % 4
            for leg in (0, 1):
                lx = int(round(x + (4 if leg else 0) + ((1 if ph in (1, 2) else -1) * (2 if leg else -2))))
                for yy in range(0, 9):
                    for xx in range(lx, lx + 4):
                        if 0 <= xx < w:
                            a[yy, xx] = _rgba('S', 1 if xx > lx else 2)
                toe = range(lx - 1, lx + 6) if d > 0 else range(lx - 2, lx + 5)
                for xx in toe:
                    if 0 <= xx < w:
                        a[9, xx] = _rgba('I', 1)
                        a[10, xx] = _rgba('I', 0)
                puff = lx + 6 if d > 0 else lx - 3
                if ph == (0 if leg else 2) and 0 <= puff < w:
                    a[10, puff] = _rgba('SN', 5)
            for xx in range(int(x) - 3, int(x) + 10):                       # coat hem
                if 0 <= xx < w:
                    a[0, xx] = _rgba('G', 1)
        fr.append(a)
    return strip(fr)


# =========================================================================== layers
def light_wells(windows, w=L.WORLD_W, h=L.WORLD_H):
    """outside.png: what the high windows look into -- a concrete light well with snow, the grating's shadow,
    the cold glow of the street lamps at the top."""
    out = np.zeros((h, w, 4), np.uint8)
    rng = np.random.default_rng(31)
    for (x0, y0, x1, y1) in windows:
        x0 -= 2; x1 += 2; y0 -= 2; y1 += 2
        ww, hh = x1 - x0, y1 - y0
        ys = np.arange(hh, dtype=np.float32)[:, None]
        tone = 2.0 + (1 - ys / hh) * 2.6 + K.noise(ww, hh, 4, x0) * 0.6
        wall = K.ramp_rgba('C', tone, np.full((hh, ww), 255, np.uint8), x0=x0, y0=y0)
        # the grating overhead: horizontal shadow bars near the top
        for yy in range(2, 10, 3):
            wall[yy, :] = _rgba('C', 1)
        # snow heap at the bottom of the well (rounded, lit from above)
        for xx in range(ww):
            top = int(hh - 9 - 4 * math.sin(math.pi * xx / ww) - rng.integers(0, 2))
            for yy in range(top, hh):
                wall[yy, xx] = _rgba('SN', 5 if yy == top else (4 if yy < top + 3 else 3))
        out[y0:y1, x0:x1] = wall
    return out


def shafts(windows, fire=0, w=L.WORLD_W, h=L.WORLD_H):
    """Cold light falling from the high windows (soft veil, plain alpha)."""
    a = np.zeros((h, w), np.float32)
    ys = np.arange(h, dtype=np.float32)[:, None]
    xs = np.arange(w, dtype=np.float32)[None, :]
    k = (0.45, 0.62)                                     # direction (dx per dy): the street lamps are uphill
    for (x0, y0, x1, y1) in windows:
        cx0, cx1 = x0 + 1, x1 - 1
        dy = ys - y1
        shift = dy * k[0]
        inside = (xs >= cx0 + shift) & (xs <= cx1 + shift + dy * 0.12) & (dy > 0)
        fade = np.clip(1 - dy / 210, 0, 1) ** 1.5
        a += inside * fade
    a = np.clip(a, 0, 1)
    a[:, :L.PIER[1]] = 0
    alpha = np.clip(np.round(a * 54), 0, 255).astype(np.uint8)
    col = np.zeros((h, w, 4), np.uint8)
    c = _rgba('C', 8)
    col[..., :3] = c[:3]
    col[..., 3] = alpha
    col[alpha == 0] = 0
    return col


def heat_strip(w, h, frames, seed):
    """Above a fire front: sparks on arcs that cool down the spark ramp (pixel_fire.spark_frames) -- the place
    of the former heat shimmer, which was a soft low-alpha effect."""
    return strip(PF.spark_frames(frames, w, h, count=max(5, w // 6), seed=seed))


def torch_beam(w=40, h=66):
    """Konrad's torch: a soft cone of warm-white light from his hand into the aisle (plain alpha veil)."""
    ys = np.arange(h, dtype=np.float32)[:, None]
    xs = np.arange(w, dtype=np.float32)[None, :]
    t = 1 - ys / (h - 1)                                    # 0 at the top (far end), 1 at the hand (bottom)
    cx = w / 2 + 2 * t
    half = 2 + (1 - t) * (w / 2 - 3)
    inside = np.abs(xs - cx) <= half
    edge = np.clip(1 - np.abs(xs - cx) / np.maximum(1.0, half), 0, 1)
    a = inside * (0.35 + 0.65 * t) * (0.4 + 0.6 * edge)
    alpha = np.clip(np.round(a * 70), 0, 255).astype(np.uint8)
    col = np.zeros((h, w, 4), np.uint8)
    c = _rgba('P', 6)
    col[..., :3] = c[:3]
    col[..., 3] = alpha
    col[alpha == 0] = 0
    return col
