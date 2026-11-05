"""env_veltrava_station_fx -- animated horizontal frame strips for L_C3_Station.

Seamless loops: every motion term uses the phase 2*pi*f/N; falling snow moves each flake by exactly one
tile height per loop (and wraps), puffs travel one period per loop.  Shading = offset-silhouette bands lit from
the low sun at the right; ordered dither only at dissolving edges (clean clusters, no blur).

Snow is region-limited on purpose: the engine's 'snow' fx is screen-wide, but in Veltrava snow falls only
OUTSIDE our platform canopy, so it is built from tiles of these strips placed in the open band between the
canopy edge and the tracks (z behind the near train and the platform) and inside the exit arch.
"""
from __future__ import annotations

import math

import numpy as np

from env_veltrava_lib import Layer, NI, SL, IR, CR, PA, LA, SK, SN, RD, bayer, value_noise


def _shade_mask(M, cols, light=(1, -1), widths=(1, 3, 6), dissolve=None, x0=0, y0=0):
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
    if dissolve is not None:
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
    p = np.pad(M, 1)
    nb = p[:-2, 1:-1].astype(int) + p[2:, 1:-1] + p[1:-1, :-2] + p[1:-1, 2:]
    return (M & (nb >= 2)) | (~M & (nb >= 4))


def snow_tile(frames=24, fw=160, fh=80, n=22, size=1, seed=0, cols=None, wobble=3.0):
    """Falling snow tile: n flakes, each falls exactly fh px per loop (wraps) with a small sine sway."""
    cols = cols or ([SN[1], SN[2]] if size == 1 else [SN[3], SN[4]])
    rng = np.random.default_rng(seed)
    S = Layer(fw * frames, fh, 'snow')
    fl = [(rng.uniform(0, fw), rng.uniform(0, fh), rng.uniform(0, 2 * math.pi), rng.integers(1, 3),
           int(rng.integers(0, len(cols)))) for _ in range(n)]
    for f in range(frames):
        ph = f / frames
        for (x0, y0, p0, cyc, ci) in fl:
            y = (y0 + ph * fh) % fh
            x = (x0 + wobble * math.sin(2 * math.pi * ph * cyc + p0)) % fw
            xi, yi = int(x), int(y)
            for dy in range(size):
                for dx in range(size):
                    xx, yy = (xi + dx) % fw, (yi + dy) % fh
                    S.px(f * fw + xx, yy, cols[ci])
    return S


def steam_plume(frames=8, fw=176, fh=150, seed=0, cols=None):
    """Big locomotive steam plume rising from an off-screen chimney at local (8, fh-8), billowing up and to the
    right over the carriage roofs; lumps travel one period per loop."""
    cols = cols or [SN[0], SN[1], SN[2], SN[3]]
    S = Layer(fw * frames, fh, 'plume')
    rng = np.random.default_rng(seed)
    base = [(rng.uniform(0, 1), rng.uniform(0.7, 1.15), rng.uniform(-1, 1)) for _ in range(12)]
    for f in range(frames):
        circles = []
        for k, (ph, sz, j) in enumerate(base):
            a = (f / frames + k / len(base) + ph * 0.07) % 1.0
            x = 8 + a ** 1.25 * (fw - 52) + j * 6
            y = fh - 10 - a * (fh - 40) - 10 * math.sin(a * 3.1)
            r = (7 + 20 * a) * sz
            circles.append((x, y, r))
            circles.append((x + r * 0.6, y + r * 0.35, r * 0.55))
        for k in range(3):
            circles.append((6 + k * 5, fh - 8 - k * 6, 7 + k))
        M = _circles_mask(fw, fh, circles)
        yy, xx = np.mgrid[0:fh, 0:fw].astype(np.float32)
        fade = np.clip((xx - fw * 0.55) / (fw * 0.45), 0, 1) + np.clip(((fh - yy) / fh - 0.62) / 0.38, 0, 1)
        nz = value_noise(fw, fh, 9, seed=seed * 5 + f, octaves=2)
        rgba = _shade_mask(M, cols, light=(1, 1), widths=(1, 3, 7), dissolve=np.clip(fade, 0, 1) * (0.55 + 0.7 * nz),
                           x0=f * fw)
        S.c[:, f * fw:(f + 1) * fw] = rgba
    return S, (8, fh - 8)


def steam_puffs(frames=6, fw=28, fh=56, seed=0, cols=None, spawn=4, grow=7.0, r0=2.0, drift=6.0):
    """Steam-heating leak between carriages: puffs spawn at local (8, fh-2), rise, swell and dissolve."""
    cols = cols or [SN[0], SN[1], SN[2], SN[3]]
    S = Layer(fw * frames, fh, 'steam')
    ox, oy = 8, fh - 2
    rng = np.random.default_rng(seed)
    jit = rng.uniform(-1, 1, spawn)
    for f in range(frames):
        circles = []
        for k in range(spawn):
            a = (f / frames + k / spawn) % 1.0
            y = oy - 2 - a * (fh - 10)
            x = ox + drift * a ** 1.4 + jit[k] * 2 * a
            r = r0 + grow * a
            circles.append((x, y, r))
            circles.append((x + r * 0.7, y + r * 0.3, r * 0.6))
        circles.append((ox, oy - 1, r0 * 0.8))
        M = _circles_mask(fw, fh, circles)
        yy = np.arange(fh, dtype=np.float32)[:, None]
        fade = np.clip((oy - yy - fh * 0.42) / (fh * 0.5), 0, 1)
        nz = value_noise(fw, fh, 4, seed=seed * 7 + f, octaves=2)
        dis = np.repeat(fade, fw, axis=1) * (0.7 + 0.5 * nz)
        rgba = _shade_mask(M, cols, light=(1, -1), widths=(1, 2, 3), dissolve=dis, x0=f * fw)
        S.c[:, f * fw:(f + 1) * fw] = rgba
    return S, (ox, oy)


def smoke_ribbon(frames=8, fw=40, fh=72, seed=0, cols=None, drift=22.0, w0=2.0, w1=9.0, wob=3.0):
    """Thin coal smoke from a chimney mouth at local (6, fh-2), bending right with the wind."""
    cols = cols or [SL[3], SL[4], SK[1], SK[2]]
    rng = np.random.default_rng(seed)
    S = Layer(fw * frames, fh, 'smoke')
    ox, oy = 6, fh - 2
    ph0 = rng.uniform(0, 2 * math.pi, 4)
    for f in range(frames):
        ph = 2 * math.pi * f / frames
        circles = []
        n = 50
        for i in range(n):
            t = i / (n - 1)
            x = ox + drift * (t ** 1.6) + wob * t * math.sin(2 * math.pi * 1.6 * t - ph + ph0[0]) \
                + 1.5 * t * math.sin(2 * math.pi * 3.1 * t - 2 * ph + ph0[1])
            y = oy - (fh - 10) * (t ** 0.92)
            r = (w0 + (w1 - w0) * t) * 0.5
            r *= 1 + 0.3 * math.sin(2 * math.pi * 4.0 * t - ph + ph0[2]) + 0.15 * math.sin(2 * math.pi * 7.0 * t - 2 * ph + ph0[3])
            circles.append((x, y, max(0.8, r)))
        M = _circles_mask(fw, fh, circles)
        yy = np.arange(fh, dtype=np.float32)[:, None]
        fade = np.clip((oy - yy - (fh * 0.58)) / (fh * 0.36), 0, 1) ** 1.2
        nz = value_noise(fw, fh, 6, seed=seed * 31 + f, octaves=2)
        dis = np.repeat(fade, fw, axis=1) * (0.55 + 0.6 * nz)
        S.c[:, f * fw:(f + 1) * fw] = _shade_mask(M, cols, light=(1, 1), widths=(1, 2, 4), dissolve=dis, x0=f * fw)
    return S, (ox, oy)


def pigeons(frames=8, fw=52, fh=14, seed=0):
    """Five town pigeons pecking at crumbs (heads bob on different phases); grey-blue bodies, iridescent neck
    pixel, pale wing bars.  Origin = local (0, fh-1) = their feet line."""
    S = Layer(fw * frames, fh, 'pigeons')
    rng = np.random.default_rng(seed)
    birds = [(4, 0.0, 1), (14, 0.35, -1), (24, 0.6, 1), (33, 0.15, 1), (43, 0.8, -1)]
    for f in range(frames):
        for (bx, ph, face) in birds:
            a = (f / frames + ph) % 1.0
            peck = a < 0.35
            ox = f * fw + bx
            yb = fh - 1
            S.rect(ox, yb - 4, 6, 3, SL[3])                     # body
            S.hline(ox, yb - 4, 6, SL[4])
            S.px(ox + (1 if face > 0 else 4), yb - 3, SN[1])    # wing bar
            S.px(ox + (2 if face > 0 else 3), yb - 3, SN[1])
            tail = ox - 1 if face > 0 else ox + 6
            S.px(tail, yb - 4, SL[2])
            hx = ox + (5 if face > 0 else 0)
            if peck:
                S.px(hx + face, yb - 2, SL[3])
                S.px(hx + 2 * face, yb - 1, SL[4])
                S.px(hx, yb - 3, PA[3])
            else:
                S.px(hx, yb - 5, PA[3])
                S.px(hx, yb - 6, SL[4])
                S.px(hx + face, yb - 6, CR[3])
            S.px(ox + 2, yb, LA[1])                             # feet
            S.px(ox + 4, yb, LA[1])
        for k in range(6):                                      # crumbs
            S.px(f * fw + 3 + k * 8 + (k % 2), fh - 1, CR[4])
    return S, (0, fh - 1)
