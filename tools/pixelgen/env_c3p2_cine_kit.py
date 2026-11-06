"""env_c3p2_cine_kit -- shared helpers of the Chapter-3 part-2 cinematics (owner: cinematics stream, round 8).

Used by env_c3p2_cine.py (build/main), env_c3p2_cine_radio.py (LS_C3_Radio), env_c3p2_cine_fire.py
(LS_C3_Fire + LS_C3_Escape), env_c3p2_cine_quay.py (LS_C3_Halves) and env_c3p2_cine_figs.py (the protagonists
through the portrait pipeline).  Builds on the round-6 cinematic tools (env_veltrava_cine: Paint, masks, light
helpers; env_veltrava_cine_kit: trilingual pixel fonts, dithered puffs) which are imported read-only.
Pure numpy, deterministic (fixed seeds, no time or global random state), no image inputs.
"""
from __future__ import annotations

import json
import math
import os
import re
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import pg  # noqa: E402
import env_berlin_kit as kit  # noqa: E402
import env_veltrava_cine as C  # noqa: E402  (Paint, masks, blur, light helpers; read-only)
import env_veltrava_cine_kit as K  # noqa: E402  (fonts, puffs, soft_quant; read-only)
import env_veltrava_lib as vlib  # noqa: E402

VW, VH = 640, 360
SAFE = (46, 314)                       # rows inside the cinematic letterbox
OUT = os.path.join(ROOT, 'assets', 'cinematics', 'c3p2')
LAYOUT: dict = {}

# ------------------------------------------------------------------------------------------------ ramps
NIGHT = ['#05070C', '#070A12', '#0C111C', '#121A26', '#1A2431', '#1E2836', '#2A3646', '#3A4859', '#4F5E70',
         '#687789']
SNOW = ['#1A2431', '#2A3646', '#3A4859', '#4F5E70', '#687789', '#7D8796', '#A1AAB7', '#C2C9D2', '#DEE2E7',
        '#F2F3F5']
LAMP = ['#22150F', '#4A2D1F', '#6E3F22', '#A8643A', '#D08F55', '#EDB777', '#FCE2B0']
IRON = ['#05070C', '#0C111C', '#15171C', '#22262D', '#323840', '#464D55', '#5E666E', '#7A828A']
OAK = ['#0E0806', '#1C120C', '#2B1B12', '#3D271A', '#553826', '#6E4A33', '#8A6040', '#A87A52']
GREEN = ['#08110C', '#14261C', '#1F3A2A', '#2E5640', '#4A7A5C', '#7FAE8C', '#B5D6BC']
PAPER = ['#2A261E', '#4A4436', '#6B6350', '#8E856C', '#B3A98D', '#D8CFB2', '#EFE8D2']
FIRE = ['#3A0F08', '#6E1E0C', '#A8381A', '#D8662A', '#F2A044', '#FCE0A0', '#FFF6DC']
RED = ['#1E0A08', '#4A1712', '#7A2218', '#A8382E', '#C8503C']
BRASS = ['#2A1D0B', '#4A3415', '#73531F', '#9C7630', '#C49A48', '#E8C779']
BAKE = ['#0E0806', '#1A0F0A', '#2A170E', '#3E2214', '#56301B', '#734124', '#93562F', '#B0703F']
SKIN = ['#3E2C3A', '#6E4442', '#8A5550', '#A2664E', '#B67D66', '#D2925E', '#F2C47E']
SMOKE = ['#0A0B0D', '#14161A', '#1E2126', '#2B2E33', '#3A3C40', '#4C4C4E', '#5E5B58']
K_COAT = ['#05070E', '#0B0F1C', '#131A2C', '#1D2442', '#2C3B5E', '#3A4A6A', '#4E556C']
A_COAT = ['#030907', '#0B1512', '#12201A', '#1B2C23', '#26392D', '#3B5443', '#5D6D57']
A_FUR = ['#15181B', '#2A3034', '#383D3A', '#474845', '#57514A', '#73624E', '#977E62']
K_HAT = ['#0E0D12', '#1F1A22', '#2D2D36', '#3D3639', '#4B4547', '#5E504C']


def ramps(**kw) -> kit.Ramps:
    return kit.Ramps(kw)


def grid(h=VH, w=VW, x0=0, y0=0):
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    return yy + y0, xx + x0


# ------------------------------------------------------------------------------------------------ io
def save(arr, rel):
    a = arr.c if hasattr(arr, 'c') else arr
    path = os.path.join(OUT, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    kit.save_rgba(np.ascontiguousarray(a), path)
    return path


def write_layout():
    os.makedirs(OUT, exist_ok=True)

    def norm(o):
        if isinstance(o, dict):
            return {str(k): norm(v) for k, v in o.items()}
        if isinstance(o, (list, tuple)):
            return [norm(v) for v in o]
        if isinstance(o, np.integer):
            return int(o)
        if isinstance(o, (np.floating, float)):
            v = float(o)
            return int(v) if v.is_integer() else round(v, 4)
        return o
    txt = json.dumps(norm(LAYOUT), indent=1, sort_keys=True, ensure_ascii=False)
    txt = re.sub(r'\[\s*(-?[\d.]+(?:,\s*-?[\d.]+)*)\s*\]',
                 lambda m: '[' + ', '.join(v.strip() for v in m.group(1).split(',')) + ']', txt)
    with open(os.path.join(OUT, 'layout.json'), 'w', encoding='utf-8', newline='\n') as f:
        f.write(txt + '\n')


def locale(key: str) -> str:
    """German text of a c3p2 cinematic key (the note art copies the subtitles' wording)."""
    with open(os.path.join(ROOT, 'data', 'locale', 'de_c3p2_cinematics.json'), encoding='utf-8') as f:
        return json.load(f)['strings'][key]


# ------------------------------------------------------------------------------------------------ colour
def hexrgb(h):
    return np.array([int(h[1:3], 16), int(h[3:5], 16), int(h[5:7], 16)], np.float32)


def requant(rgb: np.ndarray, pal, spread=18.0, ox=0, oy=0, alpha=None) -> np.ndarray:
    """Float RGB (h, w, 3) -> RGBA uint8 snapped to `pal` (hex list) with ordered dither of +-spread/2."""
    h, w = rgb.shape[:2]
    P = np.stack([hexrgb(c) for c in pal])                          # (n, 3)
    d = (pg.bayer(w, h, ox, oy) - 0.5)[..., None] * spread
    x = rgb + d
    dist = ((x[:, :, None, :] - P[None, None]) ** 2).sum(-1)
    idx = dist.argmin(-1)
    out = np.zeros((h, w, 4), np.uint8)
    out[..., :3] = P[idx].astype(np.uint8)
    out[..., 3] = 255 if alpha is None else np.where(alpha, 255, 0)
    return out


def add_glow(a, cx, cy, rx, ry, rgb, power=1.5):
    """Accumulate a soft elliptical light (additive float RGB) into a (h, w, 3) array."""
    h, w = a.shape[:2]
    yy, xx = grid(h, w)
    d = np.hypot((xx + 0.5 - cx) / max(rx, 0.5), (yy + 0.5 - cy) / max(ry, 0.5))
    g = np.clip(1 - d, 0, 1) ** power
    a += g[..., None] * np.asarray(rgb, np.float32)[None, None]
    return a


def glow_sprite(w, h, blobs, step=6.0, ox=0, oy=0):
    """Additive glow sprite: blobs = [(cx, cy, rx, ry, (r, g, b), power)] -> dithered RGBA (black = clear)."""
    a = np.zeros((h, w, 3), np.float32)
    for b in blobs:
        add_glow(a, *b)
    return K.soft_quant(a, step, ox, oy)


def blit(dst, src, x, y):
    """Alpha-over a straight RGBA uint8 sprite onto an RGBA uint8 canvas at integer (x, y)."""
    h, w = src.shape[:2]
    X0, Y0, X1, Y1 = max(0, x), max(0, y), min(dst.shape[1], x + w), min(dst.shape[0], y + h)
    if X1 <= X0 or Y1 <= Y0:
        return dst
    s = src[Y0 - y:Y1 - y, X0 - x:X1 - x]
    m = s[..., 3] > 0
    d = dst[Y0:Y1, X0:X1]
    d[m] = s[m]
    return dst


def sheet(frames):
    return np.concatenate(frames, axis=1)


# ------------------------------------------------------------------------------------------------ masks
def poly(pts, w=VW, h=VH):
    return C.poly_mask(w, h, pts)


def ell(cx, cy, rx, ry, w=VW, h=VH):
    return C.ellipse_mask(w, h, cx, cy, rx, ry)


def box(x0, y0, x1, y1, w=VW, h=VH):
    m = np.zeros((h, w), bool)
    m[max(0, int(y0)):max(0, min(h, int(y1))), max(0, int(x0)):max(0, min(w, int(x1)))] = True
    return m


def rim(m, dx, dy, width=1):
    return C.rim(m, dx, dy, width)


def edge(m):
    return m & ~(C.shift(m, 1, 0) & C.shift(m, -1, 0) & C.shift(m, 0, 1) & C.shift(m, 0, -1))


def noise(w, h, cell, seed, octaves=3):
    return pg.value_noise(w, h, cell, seed, octaves=octaves)


def lightfield(w, h, lights):
    """Sum of point lights [(x, y, radius, strength, power)] -> float field."""
    yy, xx = grid(h, w)
    f = np.zeros((h, w), np.float32)
    for (lx, ly, r, s, pw) in lights:
        f += s * np.clip(1 - np.hypot(xx + 0.5 - lx, yy + 0.5 - ly) / r, 0, 1) ** pw
    return f


# ------------------------------------------------------------------------------------------------ text
def font_mask(s: str, font='L', spacing=1) -> np.ndarray:
    """Bool mask of upper-case Veltrava pixel text (Latin, Cyrillic, digits, „“·–); font 'L' 5x7 or 's' 3x5."""
    return K.vtext(s, 'l' if font == 'L' else 's', spacing)


def hand_text(s: str, scale=2, slant=0.22, seed=0) -> np.ndarray:
    """Block capitals as written with a soft pencil: the 5x7 font scaled up, slanted, a little uneven."""
    m = font_mask(s, 'L', 1)
    m = np.repeat(np.repeat(m, scale, 0), scale, 1)
    h, w = m.shape
    pad = int(math.ceil(h * slant)) + 2
    out = np.zeros((h + 2, w + pad + 2), bool)
    rng = np.random.default_rng(seed)
    for y in range(h):
        dx = int(round((h - 1 - y) * slant))
        out[y + 1, 1 + dx:1 + dx + w] |= m[y]
    # pencil pressure: thin a few stroke pixels at the right edge of runs
    thin = rng.random(out.shape) < 0.10
    return out & ~(thin & ~C.shift(out, 1, 0))


# ------------------------------------------------------------------------------------------------ sheets
def flame_sheet(n=8, fw=26, fh=44, seed=1, cool=False):
    """n frames of a licking flame (bottom-anchored, transparent), palette FIRE; frames cycle smoothly."""
    out = np.zeros((fh, fw * n, 4), np.uint8)
    yy, xx = np.mgrid[0:fh, 0:fw].astype(np.float32)
    pal = [hexrgb(c) for c in FIRE]
    for i in range(n):
        ph = i / n * 2 * math.pi
        u = (yy + 0.5) / fh                                         # 0 top .. 1 bottom
        sway = (np.sin(ph + u * 5.0) * 2.2 + np.sin(2 * ph + u * 9.0 + 1.3) * 1.0) * (1 - u)
        nz = pg.value_noise(fw, fh * 2, 6, seed * 31 + 7, octaves=3)
        off = int((i / n) * fh) % fh
        nzs = nz[off:off + fh]
        half = (fw * 0.42) * (u ** 0.62) * (0.85 + 0.15 * np.sin(ph * 2 + 0.7))
        dx = np.abs(xx + 0.5 - fw / 2 - sway)
        dens = np.clip(1.0 - dx / (half + 1e-3), 0, 1) * np.clip(u * 1.6, 0, 1)
        dens = dens + (nzs - 0.5) * 0.9 * (1 - u * 0.6)
        tongue = np.clip(np.sin(ph * 1.0 + xx * 0.9) * 0.5 + 0.5, 0, 1) * (1 - u) * 0.35
        dens = dens - tongue
        th = pg.bayer(fw, fh, i, 0)
        m = dens > 0.18 + th * 0.10
        heat = np.clip(dens * 1.25 + u * 0.55 - 0.25, 0, 1)
        idx = np.clip((heat * (len(pal) - 1 + 0.6) + (th - 0.5) * 0.9).astype(int), 0, len(pal) - 1)
        if cool:
            idx = np.clip(idx - 1, 0, len(pal) - 2)
        fr = np.zeros((fh, fw, 4), np.uint8)
        for k, c in enumerate(pal):
            sel = m & (idx == k)
            fr[sel, :3] = c.astype(np.uint8)
            fr[sel, 3] = 255
        out[:, i * fw:(i + 1) * fw] = fr
    return out


def smoke_sheet(n=8, fw=64, fh=48, seed=5, cols=None, light=(0.4, -0.7)):
    cols = cols or ['#0E0F12', '#17191D', '#22242A', '#2E3036', '#3D3E42']
    return K.puff_sheet(n, fw, fh, cols, seed, grow=(0.26, 0.48), thin=0.45, light=light, drift=0.04)


def ember_sheet(n=4, w=3, h=3):
    """tiny glowing ember (additive), n brightness frames"""
    out = np.zeros((h, w * n, 4), np.uint8)
    for i in range(n):
        k = 0.55 + 0.45 * math.sin(i / n * 2 * math.pi)
        a = np.zeros((h, w, 3), np.float32)
        a[h // 2, w // 2] = np.array([250, 170, 80]) * k
        if w > 1:
            a[h // 2, w // 2 - 1] = a[h // 2, w // 2 + 1] = np.array([120, 50, 20]) * k
        out[:, i * w:(i + 1) * w] = K.soft_quant(a, 6.0)
    return out


# ------------------------------------------------------------------------------------------------ figures
def sil_shade(p, sil, ramp, base, warm=None, warm_ramp=None, warm_dir=(1, 0), cold=None, cold_ramp=None,
              cold_dir=(-1, 0), wk=2.6, ck=2.4):
    """Paint a flat silhouette with a soft form shading and two rims (warm key / cold back light)."""
    p.put(sil, ramp, base)
    if warm_ramp:
        e = C.edge_light(sil, warm_dir, width=3.0, soft=1)
        sel = sil & (e > 0.30)
        p.put(sel, warm_ramp, (e * wk)[sel] if warm is None else (e * warm)[sel])
    if cold_ramp:
        e2 = C.edge_light(sil, cold_dir, width=2.0, soft=1)
        sel2 = sil & (e2 > 0.42)
        p.put(sel2, cold_ramp, (e2 * ck)[sel2] if cold is None else (e2 * cold)[sel2])
