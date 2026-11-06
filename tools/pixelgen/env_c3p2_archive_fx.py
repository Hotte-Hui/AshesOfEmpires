"""env_c3p2_archive_fx -- animated strips and overlay layers of L_C3_Registry (night calm -> smoke -> fire).

Every strip is a horizontal row of frames (layer_stack.gd: hframes = frames) and loops seamlessly: noise is
periodic in the loop direction, particles live exactly one loop (or an integer fraction of it).  Colours are
palette-pure ('registry'); flames are binary-alpha pixel art with an emission twin (additive glow); smoke and
the night shafts are soft veils with a few alpha levels.  Accessibility: no strip pulses its overall
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

R = K.R


def _rgba(ramp, idx):
    return R.table[R[ramp], int(np.clip(idx, 0, R.n(ramp) - 1))].copy()


def save(arr, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    Image.fromarray(arr.astype(np.uint8), 'RGBA').save(path)


def strip(frames_list):
    return np.concatenate(frames_list, axis=1)


# =========================================================================== flames
def flame_strip(w, h, seed, frames=16, fuel=None, height=0.85, rise=6, core=1.0, lick=1.0):
    """Animated flames over a fuel line (fuel: (w,) 0..1).  The silhouette is carved by noise rising one period
    per loop; the colour follows a smooth heat field (pale core low in each tongue -> yellow -> orange -> red,
    a dark-red rim), so the tongues read as clean bands, not speckle.  Returns (rgba strip, emission strip)."""
    rng = np.random.default_rng(seed)
    xs = np.arange(w, dtype=np.float32)
    if fuel is None:
        fuel = np.zeros(w, np.float32)
        for _ in range(max(2, w // 14)):
            c = rng.uniform(0, w)
            s_ = rng.uniform(4, 10)
            fuel += rng.uniform(0.5, 1.0) * np.exp(-((xs - c) / s_) ** 2)
        fuel = np.clip(fuel / max(1e-3, fuel.max()), 0, 1)
    P = frames * rise
    nz = K.periodic_noise(w, P, 6, 18, seed, octaves=3, per_y=P)
    nw = K.periodic_noise(w, P, 3, 7, seed + 1, octaves=2, per_y=P)
    nh = K.periodic_noise(w, frames * 4, 10, 16, seed + 2, octaves=2, per_y=frames * 4)
    sway = K.periodic_noise(P, 1, 12, 1, seed + 3, octaves=2, per_x=P)[0]
    ys = np.arange(h, dtype=np.float32)[:, None]
    up = (h - 1 - ys)
    F = R.table[R['F'], :R.n('F')]
    rgba_frames, em_frames = [], []
    for k in range(frames):
        sh = (np.arange(h)[:, None] + k * rise) % P
        # columns lean a little with height (the draught), different per row band
        lean = (sway[(np.arange(h) + k * rise) % P] - 0.5) * 3.0 * (up[:, 0] / h)
        xi = np.clip(np.round(np.arange(w)[None, :] + lean[:, None]).astype(int), 0, w - 1)
        n = nz[sh, xi]
        n2 = nw[sh, xi]
        f = fuel[xi]
        hk = nh[(k * 4) % (frames * 4), :][xi]
        Hx = h * height * (0.28 + 0.72 * f) * (0.82 + 0.36 * hk) * lick
        rel = np.clip(up / np.maximum(1.0, Hx), 0, 1.5)
        body = (1 - rel) * (0.55 + 1.05 * (n - 0.5) + 0.5 * (n2 - 0.5)) + 0.28 * f * np.clip(1 - rel, 0, 1)
        on = body > 0.2 + pg.bayer(w, h, k, 0, 4) * 0.05
        heat = (f ** 0.6) * np.clip(body * 1.3, 0, 1) ** 0.9 + 0.25 * core * np.clip(1 - up / 5.0, 0, 1)
        idx = np.full((h, w), 2, np.int32)
        idx[heat > 0.16] = 3
        idx[heat > 0.34] = 4
        idx[heat > 0.55] = 5
        idx[heat > 0.76] = 6
        # one dithered pixel row between bands keeps the steps soft without speckle
        band = pg.bayer(w, h, 1 + k, 2, 4)
        for (lo, hi, lo_i) in ((0.14, 0.18, 2), (0.32, 0.36, 3), (0.53, 0.57, 4), (0.74, 0.78, 5)):
            m = (heat > lo) & (heat < hi)
            idx[m & (band > (heat - lo) / (hi - lo))] = lo_i
        inner = on.copy()
        inner[1:, :] &= on[:-1, :]
        inner[:, 1:] &= on[:, :-1]
        inner[:, :-1] &= on[:, 1:]
        rim = on & ~inner
        idx[rim] = np.minimum(idx[rim], 2)
        idx[rim & (rel > 0.55)] = 1
        col = F[idx].copy()
        col[..., 3] = 255
        col[~on] = 0
        em = col.copy()
        em[(idx < 4) | ~on] = 0
        rgba_frames.append(col)
        em_frames.append(em)
    return strip(rgba_frames), strip(em_frames)


def fuel_line(w, spots, base=0.15):
    """fuel profile from [(x, width, strength)]."""
    xs = np.arange(w, dtype=np.float32)
    f = np.full(w, base, np.float32)
    for (c, s, a) in spots:
        f = np.maximum(f, a * np.exp(-((xs - c) / max(1.0, s)) ** 2))
    return np.clip(f, 0, 1)


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
    """Static smoke under the ceiling: bottom(x) = lower edge (y), dens(x) = 0..1.  Soft alpha (5 levels),
    billows: lighter rolls with darker folds, the lower edge scalloped, lit orange from below near the fire and
    a little cold where the high windows are."""
    xs = np.arange(w, dtype=np.float32)[None, :]
    ys = np.arange(h, dtype=np.float32)[:, None]
    n1 = K.noise(w, h, 26, seed)
    n2 = K.noise(w, h, 9, seed + 1, octaves=2)
    n3 = K.noise(w, h, 4, seed + 2, octaves=1)
    scallop = 7 * np.abs(np.sin((xs + x_off) / 23.0 + n1 * 3)) + n2 * 10
    B = bottom[None, :] + scallop + n1 * 18
    t = np.clip((B - ys) / 46.0, 0, 1)                    # 0 at the edge, 1 deep in the layer
    bill = n1 * 0.9 + n2 * 0.6 + n3 * 0.25                 # billow field
    a = np.clip(t ** 0.7 * dens[None, :] * (0.8 + 0.6 * bill), 0, 1)
    thr = pg.bayer(w, h, x_off, 0, 4)
    level = np.zeros((h, w), np.int32)
    for cut in (0.14, 0.32, 0.52, 0.74):
        level += (a + (thr - 0.5) * 0.16 > cut)
    alpha = np.array([0, 96, 140, 182, 216], np.uint8)[level]
    # tone: rolls lighter, folds darker, the underside (near the edge) lighter still
    tone = 2.6 + bill * 2.2 + (1 - t) * 1.2
    edge = (t < 0.3) & (t > 0)
    fl = np.floor(tone)
    bthr = pg.bayer(w, h, x_off + 2, 1, 4)
    frac = np.clip((tone - fl - 0.5) * 2.0 + 0.5, 0, 1)
    idx = np.clip(fl + (frac > bthr), 0, R.n('S') - 1).astype(np.int32)
    base = R.table[R['S'], :R.n('S')]
    col = base[idx].copy()
    if glow_x is not None and glow_k > 0:
        g = np.clip(1 - np.abs(xs + x_off - glow_x) / 760.0, 0, 1) ** 1.2 * np.clip((ys - (B - 60)) / 60, 0, 1)
        g = g * glow_k * (0.8 + 0.4 * (bill + 0.5))
        fire = R.table[R['F'], :R.n('F')]
        gi = np.clip(1 + g * 3.4 + (bthr - 0.5) * 0.9, 1, 5).astype(np.int32)
        warm = (g + (bthr - 0.5) * 0.25 > 0.2) & (alpha > 0)
        col[warm] = fire[gi][warm]
    col[edge & (bthr > 0.75) & (alpha > 0)] = base[np.clip(idx + 1, 0, R.n('S') - 1)][edge & (bthr > 0.75) & (alpha > 0)]
    col[..., 3] = alpha
    col[alpha == 0] = 0
    return col


def smoke_roll_strip(w, h, frames, seed, speed=2, glow=0.0):
    """Smoke rolling along under the vaults (toward the cold side, i.e. to the left): periodic noise scrolled
    by `speed` px per frame, periodic over the loop; soft envelope at the strip's edges."""
    P = frames * speed
    nz = K.periodic_noise(P, h, 16, 8, seed, octaves=3, per_x=P)
    ys = np.arange(h, dtype=np.float32)[:, None]
    xs = np.arange(w, dtype=np.float32)[None, :]
    env = np.clip(np.minimum(xs, w - 1 - xs) / (w * 0.25), 0, 1) * np.clip(np.minimum(ys, h - 1 - ys) / (h * 0.3), 0, 1)
    base = R.table[R['S'], :R.n('S')]
    fire = R.table[R['F'], :R.n('F')]
    fr = []
    for k in range(frames):
        n = nz[:, ((np.arange(w) + k * speed) % P)]
        a = env * np.clip((n - 0.42) * 2.6, 0, 1)
        thr = pg.bayer(w, h, k, 0, 4)
        level = np.zeros((h, w), np.int32)
        for cut in (0.2, 0.45, 0.7):
            level += (a + (thr - 0.5) * 0.2 > cut)
        alpha = np.array([0, 70, 118, 160], np.uint8)[level]
        tone = 2.4 + n * 2.6
        idx = np.clip(np.floor(tone + (thr - 0.5) * 0.6), 0, R.n('S') - 1).astype(np.int32)
        col = base[idx].copy()
        if glow > 0:
            g = np.clip(ys / h, 0, 1) * glow * np.ones((1, w), np.float32)
            warm = (g + (thr - 0.5) * 0.3 > 0.45) & (alpha > 0)
            col[warm] = fire[np.clip((1 + g * 2.6).astype(np.int32), 1, 5)][warm]
        col[..., 3] = alpha
        col[alpha == 0] = 0
        fr.append(col)
    return strip(fr)


def smoke_wisp_strip(w, h, frames, seed, drift=(0.0, -1.0), dens=1.0, glow=0.0):
    """Animated plume (rises / drifts), soft alpha.  Periodic noise scrolled one period per loop."""
    P = frames * 3
    nz = K.periodic_noise(w, P, 10, 12, seed, octaves=3, per_y=P)
    ys = np.arange(h, dtype=np.float32)[:, None]
    xs = np.arange(w, dtype=np.float32)[None, :]
    shape = np.clip(1 - np.abs(xs - w / 2) / (w / 2), 0, 1) ** 0.7 * np.clip(ys / (h * 0.3), 0, 1) ** 0.5
    shape *= np.clip((h - ys) / (h * 0.15), 0, 1)
    fr = []
    base = R.table[R['S'], :R.n('S')]
    fire = R.table[R['F'], :R.n('F')]
    for k in range(frames):
        sh = (np.arange(h)[:, None] + k * 3) % P
        n = nz[sh, np.arange(w)[None, :]]
        a = shape * (0.3 + 1.1 * (n - 0.35)) * dens
        thr = pg.bayer(w, h, k, 0, 4)
        level = np.zeros((h, w), np.int32)
        for cut in (0.18, 0.4, 0.62):
            level += (a + (thr - 0.5) * 0.2 > cut)
        alpha = np.array([0, 64, 110, 156], np.uint8)[level]
        tone = 1.4 + n * 1.6
        idx = np.clip(np.floor(tone + thr - 0.5), 0, R.n('S') - 1).astype(np.int32)
        col = base[idx].copy()
        if glow > 0:
            g = np.clip((ys - h * 0.55) / (h * 0.45), 0, 1) * glow * np.ones((1, w), np.float32)
            warm = (g + (thr - 0.5) * 0.3 > 0.3) & (alpha > 0)
            col[warm] = fire[np.clip((1 + g * 2.4).astype(np.int32), 0, 5)][warm]
        col[..., 3] = alpha
        col[alpha == 0] = 0
        fr.append(col)
    return strip(fr)


# =========================================================================== small decals
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
    """Heat shimmer above a fire front: faint rising wavy streaks (unlit, low alpha)."""
    P = frames * 2
    nz = K.periodic_noise(w, P, 4, 10, seed, octaves=2, per_y=P)
    fr = []
    ys = np.arange(h, dtype=np.float32)[:, None]
    env = np.clip(1 - np.abs(np.arange(w) - w / 2) / (w / 2), 0, 1)[None, :] * np.clip(ys / h, 0, 1)
    for k in range(frames):
        sh = (np.arange(h)[:, None] + k * 2) % P
        n = nz[sh, np.arange(w)[None, :]]
        on = (np.abs(n - 0.5) < 0.035) & (env > 0.15)
        col = np.zeros((h, w, 4), np.uint8)
        col[on] = _rgba('F', 5)
        col[on, 3] = 60
        fr.append(col)
    return strip(fr)


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
