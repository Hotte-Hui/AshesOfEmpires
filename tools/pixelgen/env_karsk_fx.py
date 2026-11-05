"""env_karsk_fx -- animated horizontal frame strips for scene A1 (smoke, steam, flames).

Every strip loops seamlessly: all motion terms use the phase 2*pi*f/N, and puff lumps travel
along the plume by exactly one period per loop.  Shading uses offset-silhouette bands (lit from the
low sun at the right), ordered dither only at the dissolving edges -> pixel-art clusters, no blur.
"""
from __future__ import annotations

import os as _os
import sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))

import math

import numpy as np

from env_karsk_lib import Layer, NI, TE, SA, SK, ST, RU, CO, SN, WO, bayer, value_noise


def _shade_mask(M, cols, light=(1, -1), widths=(1, 3, 6), dissolve=None, x0=0, y0=0):
    """Return RGBA array: tone bands from the silhouette offset toward the light.
    cols: [core, body, lit, rim] (dark -> light)."""
    h, w = M.shape

    def inside(dx, dy):
        S = np.zeros_like(M)
        sy0, sy1 = max(0, -dy), min(h, h - dy)
        sx0, sx1 = max(0, -dx), min(w, w - dx)
        S[sy0:sy1, sx0:sx1] = M[sy0 + dy:sy1 + dy, sx0 + dx:sx1 + dx]
        return S & M

    lx, ly = light
    out = np.zeros((h, w, 4), np.uint8)
    t = np.full((h, w), 3, np.int32)
    t[inside(lx * widths[0], ly * widths[0])] = 2
    t[inside(lx * widths[1], ly * widths[1])] = 1
    t[inside(lx * widths[2], ly * widths[2])] = 0
    carr = np.stack(cols)
    out[M] = carr[t[M]]
    if dissolve is not None:  # (h, w) 0..1 -> remove pixels by ordered dither
        keep = dissolve < bayer(w, h, x0, y0, 4) * 0.98 + 0.01
        out[~keep] = 0
    return out


def _circles_mask(w, h, circles):
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    M = np.zeros((h, w), bool)
    for cx, cy, r in circles:
        if r <= 0.4:
            continue
        M |= ((xx + 0.5 - cx) ** 2 + (yy + 0.5 - cy) ** 2) <= r * r
    # cluster cleanup: remove single-pixel spurs
    p = np.pad(M, 1)
    nb = p[:-2, 1:-1].astype(int) + p[2:, 1:-1] + p[1:-1, :-2] + p[1:-1, 2:]
    return (M & (nb >= 2)) | (~M & (nb >= 4))


def smoke_ribbon(frames=8, fw=72, fh=132, seed=0, cols=None, drift=40.0, w0=4.0, w1=16.0, wob=5.0):
    """Industrial smoke ribbon rising from the stack mouth at local (10, fh-2), bending right with
    the wind, lumps travelling upward.  Returns (strip Layer, origin (x, y) of the stack mouth)."""
    cols = cols or [TE[2], TE[3], TE[4], SK[1]]
    rng = np.random.default_rng(seed)
    S = Layer(fw * frames, fh, 'smoke')
    ox, oy = 10, fh - 2
    ph0 = rng.uniform(0, 2 * math.pi, 4)
    for f in range(frames):
        ph = 2 * math.pi * f / frames
        circles = []
        n = 70
        for i in range(n):
            t = i / (n - 1)
            # path: rise, bend toward +x (wind), sinuous wobble travelling upward
            x = ox + drift * (t ** 1.6) + wob * t * math.sin(2 * math.pi * 1.6 * t - ph + ph0[0]) \
                + 2.0 * t * math.sin(2 * math.pi * 3.1 * t - 2 * ph + ph0[1])
            y = oy - (fh - 14) * (t ** 0.92)
            r = (w0 + (w1 - w0) * t) * 0.5
            r *= 1 + 0.32 * math.sin(2 * math.pi * 4.0 * t - ph + ph0[2]) + 0.16 * math.sin(2 * math.pi * 7.0 * t - 2 * ph + ph0[3])
            circles.append((x, y, max(0.8, r)))
            if t > 0.3 and i % 3 == 0:
                circles.append((x + r * 0.6 * math.sin(ph + i), y + r * 0.4, r * 0.55))
        M = _circles_mask(fw, fh, circles)
        yy = np.arange(fh, dtype=np.float32)[:, None]
        fade = np.clip((oy - yy - (fh * 0.62)) / (fh * 0.32), 0, 1) ** 1.2
        nz = value_noise(fw, fh, 6, seed=seed * 31 + f, octaves=2)
        dis = np.repeat(fade, fw, axis=1) * (0.55 + 0.6 * nz)
        rgba = _shade_mask(M, cols, light=(1, 1), widths=(1, 2, 4), dissolve=dis, x0=f * fw)
        S.c[:, f * fw:(f + 1) * fw] = rgba
    return S, (ox, oy)


def steam_puffs(frames=6, fw=26, fh=44, seed=0, cols=None, spawn=4, grow=7.0, r0=2.0, drift=8.0):
    """Light steam/smoke puffs from a small pipe at local (6, fh-2): puffs spawn, rise, swell and
    dissolve; spawn phases are spread so the loop is seamless."""
    cols = cols or [SN[0], SN[1], SN[2], SN[3]]
    S = Layer(fw * frames, fh, 'steam')
    ox, oy = 6, fh - 2
    rng = np.random.default_rng(seed)
    jit = rng.uniform(-1, 1, spawn)
    for f in range(frames):
        circles = []
        ages = []
        for k in range(spawn):
            a = (f / frames + k / spawn) % 1.0
            y = oy - 2 - a * (fh - 8)
            x = ox + drift * a ** 1.4 + jit[k] * 2 * a
            r = r0 + grow * a
            circles.append((x, y, r))
            circles.append((x + r * 0.7, y + r * 0.3, r * 0.6))
            ages.append(a)
        circles.append((ox, oy - 1, r0 * 0.8))
        M = _circles_mask(fw, fh, circles)
        yy = np.arange(fh, dtype=np.float32)[:, None]
        fade = np.clip((oy - yy - fh * 0.45) / (fh * 0.5), 0, 1)
        nz = value_noise(fw, fh, 4, seed=seed * 7 + f, octaves=2)
        dis = np.repeat(fade, fw, axis=1) * (0.7 + 0.5 * nz)
        rgba = _shade_mask(M, cols, light=(1, -1), widths=(1, 2, 3), dissolve=dis, x0=f * fw)
        S.c[:, f * fw:(f + 1) * fw] = rgba
    return S, (ox, oy)


def tower_plume(frames=8, fw=84, fh=64, seed=0, cols=None):
    """Cooling-tower steam: broad billowing mass from a wide mouth at local (8..30, fh-2)."""
    cols = cols or [SK[2], SK[3], SK[4], SK[5]]
    S = Layer(fw * frames, fh, 'plume')
    rng = np.random.default_rng(seed)
    base = [(rng.uniform(0, 1), rng.uniform(0.6, 1.0), rng.uniform(-1, 1)) for _ in range(9)]
    for f in range(frames):
        circles = []
        for k, (ph, sz, j) in enumerate(base):
            a = (f / frames + k / len(base) + ph * 0.1) % 1.0
            x = 10 + (k % 3) * 8 + a * 34 + j * 3
            y = fh - 6 - a * (fh - 18)
            r = (5 + 10 * a) * sz
            circles.append((x, y, r))
        for k in range(4):                    # constant body over the mouth
            circles.append((12 + k * 6, fh - 6, 5.5))
        M = _circles_mask(fw, fh, circles)
        yy, xx = np.mgrid[0:fh, 0:fw].astype(np.float32)
        fade = np.clip(((fh - yy) / fh - 0.55) / 0.45, 0, 1) + np.clip((xx - fw * 0.62) / (fw * 0.38), 0, 1)
        nz = value_noise(fw, fh, 7, seed=seed * 5 + f, octaves=2)
        rgba = _shade_mask(M, cols, light=(1, 1), widths=(1, 3, 6), dissolve=np.clip(fade, 0, 1) * (0.6 + 0.6 * nz),
                           x0=f * fw)
        S.c[:, f * fw:(f + 1) * fw] = rgba
    return S, (20, fh - 2)


def barrel_flames(frames=8, fw=18, fh=20, seed=0):
    """Flames above the barrel rim: one merged, organic fire body (not separate stripes) whose tongues rise,
    split and lick upward.  Heat field = envelope (wide low base, narrowing) + rising periodic turbulence;
    banded into pale core / amber / copper / dark smoky tips.  Seamless loop: every turbulence term moves an
    integer number of periods per loop.  Origin = rim centre at local (fw//2, fh-1).  All pixels emissive."""
    S = Layer(fw * frames, fh, 'flames')
    rng = np.random.default_rng(seed)
    yy, xx = np.mgrid[0:fh, 0:fw].astype(np.float32)
    v = (fh - 1 - yy) / (fh - 1)                       # 0 at the rim .. 1 at the top
    u = (xx + 0.5 - fw / 2.0) / (fw / 2.0) * 1.3        # base ~ the barrel mouth (12 of 18 px)
    terms = [(rng.uniform(1.2, 2.6), int(rng.integers(1, 3)), rng.uniform(0, 2 * math.pi), rng.uniform(0.5, 1.0))
             for _ in range(5)]
    for f in range(frames):
        t = f / frames
        turb = np.zeros_like(u)
        for (kx, m, ph, amp) in terms:
            turb += amp * np.sin(2 * math.pi * (kx * u * 0.9 + m * (v * 1.3 - t)) + ph)
        turb /= sum(tm[3] for tm in terms)
        lean = 0.12 * math.sin(2 * math.pi * t) * v       # the whole fire sways a little
        env = 1.0 - np.abs(u - lean) ** 1.5 * (0.9 + 0.8 * v) - v ** 1.15 * 0.95
        heat = env + turb * (0.2 + 0.5 * v)
        heat[yy >= fh - 1] = np.maximum(heat[yy >= fh - 1], 0.5 - np.abs(u[yy >= fh - 1]) * 0.55)
        bands = [(0.7, CO[4]), (0.46, CO[3]), (0.27, CO[2]), (0.13, CO[1]), (0.05, CO[0])]
        for x in range(fw):
            for y in range(fh):
                h = heat[y, x]
                for thr, c in bands:
                    if h > thr:
                        if c is CO[0] and v[y, x] < 0.5:
                            break                          # dark smoky edge only on the high tips
                        S.px(f * fw + x, y, c, em=c)
                        break
        # remove isolated single pixels (clean clusters)
        sub = S.c[:, f * fw:(f + 1) * fw]
        a = sub[..., 3] > 0
        p = np.pad(a, 1)
        nb = p[:-2, 1:-1].astype(int) + p[2:, 1:-1] + p[1:-1, :-2] + p[1:-1, 2:]
        lone = a & (nb == 0)
        sub[lone] = 0
        S.em[:, f * fw:(f + 1) * fw][lone] = 0
    return S, (fw // 2, fh - 1)


def chimney_wisp(frames=8, fw=30, fh=60, seed=0, cols=None):
    """Thin grey coal-stove smoke from a stovepipe at local (5, fh-2)."""
    cols = cols or [ST[2], ST[3], ST[4], SN[0]]
    return smoke_ribbon(frames=frames, fw=fw, fh=fh, seed=seed, cols=cols, drift=16.0, w0=2.0, w1=8.0, wob=3.0)
