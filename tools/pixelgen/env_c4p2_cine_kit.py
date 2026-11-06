"""env_c4p2_cine_kit -- the painter of the Chapter-4-part-2 cinematics (owner: cine stream, round 10).

The five films LS_C4P2_Depot / _Steam / _Book / _Express / _Clock (documentation/C4P2_DESIGN.md §2.9) are painted
by env_c4p2_cine.py through this kit.  Unlike the flat tone ramps of earlier plates, every plate here is a small
deferred renderer, so a place is lit like a place:
  GB        a G-buffer canvas in frame pixels: albedo, normal (x right, y UP, z toward the viewer, like the
            character normal maps), depth, emission, gloss, ambient occlusion.  The painters put surfaces with
            procedural textures whose normals carry the relief (bricks, planks, corrugated iron, coal, snow,
            cobbles, frost, glass, cloth)
  Lt        point / spot lights with a depth (floodlights, sodium lamps, a barrel fire, lamps behind glass)
  shade()   hemisphere ambient + wrapped Lambert + Blinn specular per light, depth haze, a filmic shoulder
  quant()   the result snapped to the film's hand-picked palette (nearest colour in OKLab after an ordered Bayer
            dither in sRGB): every pixel of a plate is a palette colour, like the game's art
Figures: the game's own rig (chargen_body + the cast specs of chargen_cast*/characters_c4) renders the people of
the wide shots in poses made for these films (shovels, a toolbox, band instruments, a match, a canister, carbons)
at 1 texel = 1 px, placed and graded by env_c4p2_cine_people.py.  Close shots are not rendered with this kit but
painted flat (env_c4p2_cine_flat.py) with hands from the sprite shader (env_c4p2_cine_hands.py), the cast's
dialogue busts (env_c4p2_cine_busts.py) and the engines of env_c4p2_cine_loco.py.
A cast member whose rig spec is not delivered yet is drawn from a declared stand-in and recorded in layout.json
"standins" (the tests report it).  Deterministic: fixed seeds, no time or global random state.
"""
from __future__ import annotations

import contextlib
import copy
import dataclasses
import json
import math
import os
import re
import sys
import zlib

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import pg  # noqa: E402
import env_berlin_kit as BK  # noqa: E402  (save_rgba; read-only)
import env_veltrava_cine as VC  # noqa: E402  (poly / ellipse masks, strokes, blur; read-only)
import env_veltrava_cine_kit as VK  # noqa: E402  (pixel fonts incl. Cyrillic, puffs, soft_quant; read-only)
import env_c3p2_cine_kit as Q3  # noqa: E402  (glow sprites, flame / smoke / ember sheets; read-only)

VW, VH = 640, 360
SAFE = (46, 314)
OUT = os.path.join(ROOT, 'assets', 'cinematics', 'c4p2')
CHARS = os.path.join(ROOT, 'assets', 'characters')
LAYOUT: dict = {}
STANDINS: dict = {}


def sd(*parts) -> int:
    return zlib.crc32('/'.join(str(p) for p in parts).encode('utf-8')) & 0x7FFFFFFF


# ================================================================================================= io
def save(arr, rel):
    path = os.path.join(OUT, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    BK.save_rgba(np.ascontiguousarray(np.asarray(arr).astype(np.uint8)), path)
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
    data = dict(LAYOUT)
    data['standins'] = dict(STANDINS)
    txt = json.dumps(norm(data), indent=1, sort_keys=True, ensure_ascii=False)
    txt = re.sub(r'\[\s*(-?[\d.]+(?:,\s*-?[\d.]+)*)\s*\]',
                 lambda m: '[' + ', '.join(v.strip() for v in m.group(1).split(',')) + ']', txt)
    with open(os.path.join(OUT, 'layout.json'), 'w', encoding='utf-8', newline='\n') as f:
        f.write(txt + '\n')


# ================================================================================================= colour
def hx(c):
    """'#rrggbb' / (r, g, b) 0..255 -> sRGB float32 0..1."""
    if isinstance(c, str):
        return np.array([int(c[1:3], 16), int(c[3:5], 16), int(c[5:7], 16)], np.float32) / 255.0
    return np.asarray(c, np.float32)[:3] / 255.0


def to_lin(s):
    s = np.asarray(s, np.float32)
    return np.where(s <= 0.04045, s / 12.92, ((np.clip(s, 0, None) + 0.055) / 1.055) ** 2.4).astype(np.float32)


def to_srgb(l):
    l = np.clip(np.asarray(l, np.float32), 0, 1)
    return np.where(l <= 0.0031308, l * 12.92, 1.055 * l ** (1 / 2.4) - 0.055).astype(np.float32)


def lc(c):
    """Colour -> linear float (3,)."""
    return to_lin(hx(c))


_M1 = np.array([[0.4122214708, 0.5363325363, 0.0514459929], [0.2119034982, 0.6806995451, 0.1073969566],
                [0.0883024619, 0.2817188376, 0.6299787005]], np.float32)
_M2 = np.array([[0.2104542553, 0.7936177850, -0.0040720468], [1.9779984951, -2.4285922050, 0.4505937099],
                [0.0259040371, 0.7827717662, -0.8086757660]], np.float32)


def oklab(lin):
    lms = np.cbrt(np.clip(lin, 0, None) @ _M1.T)
    return lms @ _M2.T


def palette(*ramps):
    """Flat, de-duplicated list of hex colours from ramps (lists of hex)."""
    out, seen = [], set()
    for r in ramps:
        for c in r:
            c = c.lower()
            if c not in seen:
                seen.add(c)
                out.append(c)
    return out


def quant(rgb_lin, pal, spread=0.05, ox=0, oy=0, alpha=None, dither=True, weights=(1.0, 1.0, 1.0)):
    """Linear RGB (h, w, 3) -> RGBA uint8 whose every opaque pixel is a palette colour: an ordered 4x4 Bayer offset
    of +-spread/2 in sRGB, then the nearest palette colour in OKLab (weights scale L, a, b)."""
    h, w = rgb_lin.shape[:2]
    s = to_srgb(rgb_lin)
    if dither and spread > 0:
        s = s + (pg.bayer(w, h, ox, oy) - 0.5)[..., None] * spread
    lab = oklab(to_lin(np.clip(s, 0, 1))) * np.asarray(weights, np.float32)
    P = np.stack([hx(c) for c in pal])
    Pl = oklab(to_lin(P)) * np.asarray(weights, np.float32)
    idx = np.zeros((h, w), np.int32)
    step = max(1, 200000 // (w * max(1, len(pal))) + 1)
    for y0 in range(0, h, step):
        d = ((lab[y0:y0 + step, :, None, :] - Pl[None, None]) ** 2).sum(-1)
        idx[y0:y0 + step] = d.argmin(-1)
    out = np.zeros((h, w, 4), np.uint8)
    out[..., :3] = np.round(P[idx] * 255).astype(np.uint8)
    out[..., 3] = 255 if alpha is None else np.where(alpha, 255, 0)
    return out


def quant_rgba(rgba, pal, spread=0.0):
    """An RGBA uint8 sprite snapped to a palette (alpha kept)."""
    lin = to_lin(rgba[..., :3].astype(np.float32) / 255.0)
    return quant(lin, pal, spread=spread, dither=spread > 0, alpha=rgba[..., 3] > 0)


# ================================================================================================= hashing / noise
def hash2(ix, iy, seed=0):
    ix = np.asarray(ix).astype(np.int64)
    iy = np.asarray(iy).astype(np.int64)
    n = (ix * 374761393 + iy * 668265263 + int(seed) * 2246822519) & 0xFFFFFFFF
    n = ((n ^ (n >> 13)) * 1274126177) & 0xFFFFFFFF
    return (((n ^ (n >> 16)) & 0xFFFF) / 65535.0).astype(np.float32)


def noise(w, h, cell, seed, octaves=3):
    return pg.value_noise(int(w), int(h), max(1.0, float(cell)), int(seed), octaves=octaves).astype(np.float32)


def blur(a, r):
    return VC.blur(np.asarray(a, np.float32), int(r)) if r >= 1 else np.asarray(a, np.float32)


def smooth(x, a, b):
    u = np.clip((np.asarray(x, np.float32) - a) / max(1e-6, b - a), 0, 1)
    return u * u * (3 - 2 * u)


def nrm(v):
    v = np.asarray(v, np.float32)
    return v / (np.linalg.norm(v, axis=-1, keepdims=True) + 1e-6)


def normals_from_height(hm, k=1.0):
    """Height map (image y down) -> normals (x right, y up, z toward the viewer)."""
    gy, gx = np.gradient(np.asarray(hm, np.float32))
    n = np.stack([-gx * k, gy * k, np.ones_like(gx)], -1)
    return nrm(n)


# ================================================================================================= masks
def shift(m, dx, dy):
    out = np.zeros_like(m)
    h, w = m.shape
    ys, yd = slice(max(0, dy), min(h, h + dy)), slice(max(0, -dy), min(h, h - dy))
    xs, xd = slice(max(0, dx), min(w, w + dx)), slice(max(0, -dx), min(w, w - dx))
    out[ys, xs] = m[yd, xd]
    return out


def dilate(m, r=1):
    out = m.copy()
    for dy in range(-r, r + 1):
        for dx in range(-r, r + 1):
            if dx * dx + dy * dy <= r * r + r:
                out |= shift(m, dx, dy)
    return out


def erode(m, r=1):
    return ~dilate(~m, r)


def top_edge(m):
    return m & ~shift(m, 0, 1)


def snow_on(m, thick=2, seed=0, jag=1.0):
    """Snow lying ON the upper edges of `m` (outside it): a cap 1..thick px high with a noisy outline."""
    h, w = m.shape
    top = top_edge(m)
    nz = noise(w, h, 5, seed, 2)
    out = np.zeros_like(m)
    for k in range(1, int(thick) + 1):
        lay = shift(top, 0, -k)
        if k > 1:
            lay &= nz > (k - 1) / (thick + jag)
        out |= lay
    return out & ~m


# ================================================================================================= G-buffer
class Lt:
    """A light in frame space: (x, y) pixels, z depth (larger = farther from the camera, like GB.z).
    col/I colour and intensity, r reach (px), wrap (soft terminator), spot=(dir (x, y up, z toward viewer),
    inner deg, outer deg), spec (specular gain)."""

    def __init__(self, x, y, z, col, I=1.0, r=300.0, wrap=0.15, spot=None, spec=0.7, fall=2.0):
        self.x, self.y, self.z = float(x), float(y), float(z)
        self.col = lc(col) * float(I)
        self.r = float(r)
        self.wrap = float(wrap)
        self.spot = spot
        self.spec = float(spec)
        self.fall = float(fall)


class GB:
    """G-buffer canvas: w x h pixels whose top-left is frame position (ox, oy)."""

    def __init__(self, w=VW, h=VH, ox=0, oy=0, z=600.0):
        self.w, self.h, self.ox, self.oy = int(w), int(h), int(ox), int(oy)
        yy, xx = np.mgrid[0:self.h, 0:self.w].astype(np.float32)
        self.yy, self.xx = yy + oy, xx + ox
        self.alb = np.zeros((self.h, self.w, 3), np.float32)
        self.n = np.zeros((self.h, self.w, 3), np.float32)
        self.n[..., 2] = 1.0
        self.z = np.full((self.h, self.w), float(z), np.float32)
        self.em = np.zeros((self.h, self.w, 3), np.float32)
        self.gl = np.zeros((self.h, self.w), np.float32)
        self.ao = np.ones((self.h, self.w), np.float32)
        self.cov = np.zeros((self.h, self.w), bool)
        self.nofog = np.zeros((self.h, self.w), bool)

    # ------------------------------------------------------------------ masks in frame coordinates
    def box(self, x0, y0, x1, y1):
        m = np.zeros((self.h, self.w), bool)
        X0, Y0 = max(0, int(round(x0 - self.ox))), max(0, int(round(y0 - self.oy)))
        X1, Y1 = min(self.w, int(round(x1 - self.ox))), min(self.h, int(round(y1 - self.oy)))
        if X1 > X0 and Y1 > Y0:
            m[Y0:Y1, X0:X1] = True
        return m

    def poly(self, pts):
        return VC.poly_mask(self.w, self.h, [(x - self.ox, y - self.oy) for (x, y) in pts])

    def ell(self, cx, cy, rx, ry):
        return VC.ellipse_mask(self.w, self.h, cx - self.ox, cy - self.oy, rx, ry)

    def line(self, pts, r=0.5):
        return VC.stroke(self.w, self.h, pts, r, 0.0, 0, self.ox, self.oy)

    def text(self, s, x, y, font='s', spacing=1):
        return VK.place(VK.vtext(s, font, spacing), self.w, self.h, int(x - self.ox), int(y - self.oy))

    # ------------------------------------------------------------------ writing
    def _vals(self, v, m, dim3=True):
        v = np.asarray(v, np.float32)
        if dim3:
            if v.ndim == 1:
                return np.broadcast_to(v, (int(m.sum()), 3))
            return v[m]
        if v.ndim == 0:
            return float(v)
        return v[m]

    def put(self, m, col, tex=None, n=None, z=None, em=None, gl=None, ao=None, nofog=None):
        """Write a surface: col hex / (r, g, b) / linear (h, w, 3) array; tex an albedo multiplier (h, w) or
        scalar; n a normal (3,) or (h, w, 3); z depth; em emission (hex, linear (3,) or (h, w, 3)) x 1;
        gl gloss 0..1; ao occlusion multiplier."""
        m = np.asarray(m, bool)
        if not m.any():
            return m
        if isinstance(col, (str, tuple, list)):
            c = lc(col)
        else:
            c = np.asarray(col, np.float32)
        a = self._vals(c, m).copy()
        if tex is not None:
            t = self._vals(tex, m, False)
            a = a * (np.asarray(t, np.float32)[:, None] if np.ndim(t) else t)
        self.alb[m] = a
        if n is None:
            self.n[m] = (0.0, 0.0, 1.0)
        else:
            nn = np.asarray(n, np.float32)
            self.n[m] = nrm(nn)[m] if nn.ndim == 3 else nrm(nn)
        if z is not None:
            self.z[m] = self._vals(z, m, False)
        if em is None:
            self.em[m] = 0.0
        else:
            e = lc(em) if isinstance(em, (str, tuple, list)) else np.asarray(em, np.float32)
            self.em[m] = self._vals(e, m)
        self.gl[m] = 0.0 if gl is None else self._vals(gl, m, False)
        self.ao[m] = 1.0 if ao is None else self._vals(ao, m, False)
        if nofog is not None:
            self.nofog[m] = nofog
        self.cov[m] = True
        return m

    def mul(self, m, k):
        """Darken / brighten the albedo already painted under m (soot, wet patches, contact shadows)."""
        m = np.asarray(m, bool) & self.cov
        kk = self._vals(k, m, False)
        self.alb[m] *= (np.asarray(kk, np.float32)[:, None] if np.ndim(kk) else kk)

    def glow(self, m, col, k=1.0):
        """Add emission under m (lit windows, lamp lenses, embers)."""
        m = np.asarray(m, bool)
        e = lc(col) * k
        self.em[m] += e
        self.cov[m] = True

    # ------------------------------------------------------------------ shading
    def shade(self, lights, sky='#3a4658', gnd='#20242a', amb=0.35, fog=None, fogz=(200.0, 1200.0), fogmax=0.85,
              exposure=1.0, spec_pow=24.0):
        n = self.n
        hemi = lc(gnd)[None, None] + (lc(sky) - lc(gnd))[None, None] * (0.5 + 0.5 * n[..., 1:2])
        acc = hemi * amb
        spec = np.zeros_like(acc)
        for lt in lights:
            dx = lt.x - self.xx
            dy = self.yy - lt.y
            dz = self.z - lt.z
            d = np.sqrt(dx * dx + dy * dy + dz * dz) + 1e-3
            lx, ly, lz = dx / d, dy / d, dz / d
            ndl = n[..., 0] * lx + n[..., 1] * ly + n[..., 2] * lz
            lam = np.clip((ndl + lt.wrap) / (1 + lt.wrap), 0, 1)
            att = np.clip(1 - (d / lt.r) ** 2, 0, 1) ** lt.fall
            if lt.spot is not None:
                sdir, inner, outer = lt.spot
                sdir = nrm(np.asarray(sdir, np.float32))
                ca = -(lx * sdir[0] + ly * sdir[1] + lz * sdir[2])
                att = att * smooth(ca, math.cos(math.radians(outer)), math.cos(math.radians(inner)))
            acc += lt.col[None, None] * (att * lam)[..., None]
            if lt.spec > 0:
                hx_, hy_, hz_ = lx, ly, lz + 1.0
                hn = np.sqrt(hx_ * hx_ + hy_ * hy_ + hz_ * hz_) + 1e-6
                ndh = np.clip((n[..., 0] * hx_ + n[..., 1] * hy_ + n[..., 2] * hz_) / hn, 0, 1)
                spec += lt.col[None, None] * (self.gl * att * lt.spec * ndh ** spec_pow)[..., None]
        out = self.alb * acc * self.ao[..., None] + spec + self.em
        if fog is not None:
            f = np.clip((self.z - fogz[0]) / max(1.0, fogz[1] - fogz[0]), 0, 1) ** 1.2 * fogmax
            f = np.where(self.nofog, 0.0, f)
            out = out * (1 - f[..., None]) + lc(fog)[None, None] * f[..., None]
        out = 1.0 - np.exp(-out * exposure)
        return out.astype(np.float32)

    def final(self, lights, pal, spread=0.05, **kw):
        """shade() + quant(): an RGBA plate (uncovered pixels transparent)."""
        return quant(self.shade(lights, **kw), pal, spread, self.ox, self.oy, alpha=self.cov)


def light_at(lights, x, y, z, nrm_=(0.0, 0.0, 1.0), sky='#3a4658', gnd='#20242a', amb=0.35):
    """The linear light colour arriving at one point (for tinting sprites and checking a composition)."""
    g = GB(1, 1, int(x), int(y), z)
    g.n[0, 0] = nrm(nrm_)
    g.alb[0, 0] = 1.0
    g.cov[0, 0] = True
    n = g.n
    hemi = lc(gnd) + (lc(sky) - lc(gnd)) * (0.5 + 0.5 * n[0, 0, 1])
    acc = hemi * amb
    for lt in lights:
        dx, dy, dz = lt.x - x, y - lt.y, z - lt.z
        d = math.sqrt(dx * dx + dy * dy + dz * dz) + 1e-3
        l = np.array([dx, dy, dz]) / d
        lam = max(0.0, (float(np.dot(n[0, 0], l)) + lt.wrap) / (1 + lt.wrap))
        att = max(0.0, 1 - (d / lt.r) ** 2) ** lt.fall
        if lt.spot is not None:
            sdir, inner, outer = lt.spot
            sdir = nrm(np.asarray(sdir, np.float32))
            ca = -float(np.dot(l, sdir))
            att *= float(smooth(ca, math.cos(math.radians(outer)), math.cos(math.radians(inner))))
        acc = acc + lt.col * att * lam
    return acc


# ================================================================================================= textures
def tex_noise(g: GB, cell, seed, amp=0.15, octaves=3):
    return 1.0 + (noise(g.w, g.h, cell, seed, octaves) - 0.5) * 2 * amp


def bricks(g: GB, m, col, mortar, bw=9, bh=4, seed=1, var=0.2, x0=0, y0=0, z=None, soot=None, relief=0.55,
           ao=None, gl=None):
    """Running-bond brickwork with per-brick tint, mortar joints set back (their lower lip catches top light)."""
    xx, yy = g.xx - x0, g.yy - y0
    row = np.floor(yy / bh)
    off = np.where(np.mod(row, 2) == 0, 0.0, bw / 2.0)
    bx = np.floor((xx + off) / bw)
    u = xx + off - bx * bw
    v = yy - row * bh
    mort = (u < 1) | (v < 1)
    hsh = hash2(bx, row, seed)
    tint = 1 + (hsh - 0.5) * 2 * var + (noise(g.w, g.h, 3, seed + 7, 2) - 0.5) * 0.18
    al = lc(col)[None, None] * tint[..., None]
    burnt = hash2(bx + 31, row - 7, seed) > 0.86
    al = np.where(burnt[..., None], al * np.array([0.62, 0.55, 0.52], np.float32), al)
    nn = np.zeros((g.h, g.w, 3), np.float32)
    nn[..., 2] = 1
    nn[..., 1] = np.where(v < 1.0, -relief, np.where(v < 2.0, relief * 0.6, 0.0))
    nn[..., 0] = np.where(u < 1.0, relief * 0.5, 0.0)
    if soot is not None:
        al = al * soot[..., None]
    g.put(m & ~mort, al, n=nn, z=z, ao=ao, gl=gl)
    mc = lc(mortar)[None, None] * (0.85 + 0.3 * noise(g.w, g.h, 2, seed + 3, 1))[..., None]
    if soot is not None:
        mc = mc * soot[..., None]
    g.put(m & mort, mc, n=nn, z=z, ao=0.8 if ao is None else ao)


def planks(g: GB, m, col, pw=6, vertical=True, seed=2, var=0.16, gap='#120c08', z=None, x0=0, y0=0, gl=None,
           grain=0.12, ao=None):
    xx, yy = g.xx - x0, g.yy - y0
    a, b = (xx, yy) if vertical else (yy, xx)
    k = np.floor(a / pw)
    u = a - k * pw
    joint = u < 1
    tint = 1 + (hash2(k, 3, seed) - 0.5) * 2 * var
    along = noise(g.w, g.h, 2, seed + 1, 2)
    gr = 1 + (np.sin(b * 0.9 + hash2(k, 9, seed) * 30 + along * 6) * 0.5) * grain
    al = lc(col)[None, None] * (tint * gr)[..., None]
    nn = np.zeros((g.h, g.w, 3), np.float32)
    nn[..., 2] = 1
    if vertical:
        nn[..., 0] = np.where(u < 2, 0.45, np.where(u > pw - 1.5, -0.35, 0.0))
    else:
        nn[..., 1] = np.where(u < 2, -0.45, np.where(u > pw - 1.5, 0.35, 0.0))
    g.put(m & ~joint, al, n=nn, z=z, gl=gl, ao=ao)
    g.put(m & joint, gap, z=z, ao=0.7)


def corrugated(g: GB, m, col, period=4.0, vertical=True, z=None, gl=0.25, rust=None, seed=3, amp=0.75):
    a = g.xx if vertical else g.yy
    ph = np.sin(a * 2 * math.pi / period)
    nn = np.zeros((g.h, g.w, 3), np.float32)
    nn[..., 2] = 1
    if vertical:
        nn[..., 0] = ph * amp
    else:
        nn[..., 1] = ph * amp
    al = np.broadcast_to(lc(col), (g.h, g.w, 3)).copy()
    if rust is not None:
        r = noise(g.w, g.h, 9, seed, 3)
        streak = noise(g.w, g.h * 1, 3, seed + 1, 2)
        k = np.clip((r - 0.55) * 4 + (streak - 0.5) * 0.6, 0, 1)
        al = al * (1 - k[..., None]) + lc(rust)[None, None] * k[..., None]
    g.put(m, al, tex=tex_noise(g, 6, seed + 2, 0.08), n=nn, z=z, gl=gl)


def coal(g: GB, m, seed=4, scale=3.0, z=None, base=('#101013', '#2a2a31'), gl=0.3, dust=None):
    """Heaped coal: lumps (cellular height -> normals), a few glossy facets that glint under the lamps."""
    h1 = noise(g.w, g.h, scale, seed, 2)
    h2 = noise(g.w, g.h, scale * 2.4, seed + 1, 2)
    cell = np.abs(np.sin(g.xx * 1.7 / scale + h2 * 6.0) * np.sin(g.yy * 2.1 / scale + h1 * 6.0))
    hm = h1 * 0.6 + h2 * 1.2 + cell * 0.8
    n = normals_from_height(hm, 1.6)
    t = np.clip((h2 - 0.25) * 1.5, 0, 1)
    al = lc(base[0])[None, None] * (1 - t[..., None]) + lc(base[1])[None, None] * t[..., None]
    if dust is not None:
        dk = np.clip((noise(g.w, g.h, 11, seed + 5, 3) - 0.55) * 2.5, 0, 1) * dust
        al = al * (1 - dk[..., None]) + lc('#4a4744')[None, None] * dk[..., None]
    g.put(m, al, n=n, z=z, gl=gl * np.clip(cell - 0.6, 0, 1) * 2.5)


def snow(g: GB, m, seed=5, z=None, col='#dfe6ee', shade_col='#aab6c4', up=0.85, gl=0.12, foot=None):
    """Lying snow, painted calm: a few broad, low drifts (two tones only, long and flat like wind-laid snow),
    thin wind streaks along the ground, sparse sparkle; an optional trodden mask darkens it."""
    h1 = noise(g.w, g.h, 48, seed, 2)
    streak = np.abs(np.sin(g.yy * 0.9 + noise(g.w, g.h, 30, seed + 1, 1) * 9.0)) > 0.94
    k = (h1 > 0.5).astype(np.float32)
    al = lc(shade_col)[None, None] * (1 - k[..., None]) * 0.35 + lc(col)[None, None] * (0.65 + 0.35 * k[..., None])
    al = np.where(streak[..., None], al * 0.93, al)
    spark = hash2(g.xx.astype(np.int64), g.yy.astype(np.int64), seed + 2) > 0.992
    al = np.where(spark[..., None], np.minimum(al * 1.12, 1.0), al)
    if foot is not None:
        al = np.where(foot[..., None], al * np.array([0.72, 0.74, 0.8], np.float32), al)
    n = np.zeros((g.h, g.w, 3), np.float32)
    n[..., 1] = up
    n[..., 2] = 1 - up * 0.5
    g.put(m, al, n=nrm(n), z=z, gl=gl)


def cobbles(g: GB, m, col, seed=6, cw=6, ch=4, z=None, wet=0.0, snow_k=0.0, persp=None):
    xx, yy = g.xx, g.yy
    row = np.floor(yy / ch)
    off = hash2(row, 1, seed) * cw
    bx = np.floor((xx + off) / cw)
    u = (xx + off - bx * cw) / cw
    v = (yy - row * ch) / ch
    dome = np.clip(1 - ((u - 0.5) * 2) ** 2, 0, 1) * np.clip(1 - ((v - 0.5) * 2) ** 2, 0, 1)
    n = normals_from_height(dome * 2.0, 1.2)
    tint = 0.8 + hash2(bx, row, seed) * 0.4
    al = lc(col)[None, None] * tint[..., None] * (0.55 + 0.45 * np.sqrt(dome))[..., None]
    if snow_k > 0:
        sk = (1 - dome) * snow_k
        al = al * (1 - sk[..., None]) + lc('#c8d0da')[None, None] * sk[..., None]
    g.put(m, al, n=n, z=z, gl=0.15 + wet * dome)


def frost(g: GB, m, seed=7, col='#cfe0ea', k=0.9, edge=10):
    """Frost flowers creeping in from a pane's edges (adds albedo + a little emission)."""
    h, w = g.h, g.w
    d = np.full((h, w), 99.0, np.float32)
    ys, xs = np.nonzero(m)
    if len(ys) == 0:
        return
    y0, y1, x0, x1 = ys.min(), ys.max(), xs.min(), xs.max()
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    d = np.minimum.reduce([yy - y0, y1 - yy, xx - x0, x1 - xx])
    nz = noise(w, h, 2, seed, 3)
    fern = np.abs(np.sin((xx * 0.9 + yy * 0.6) * 0.7 + nz * 9))
    f = m & (d < edge * (0.4 + nz)) & ((fern > 0.55) | (d < 2))
    g.alb[f] = g.alb[f] * (1 - k) + lc(col) * k
    g.em[f] += lc(col) * 0.04


def cloth(g: GB, m, col, seed=8, folds=0.5, period=7.0, vertical=True, z=None, var=0.1):
    a = g.xx if vertical else g.yy
    nz = noise(g.w, g.h, 6, seed, 2)
    ph = np.sin(a * 2 * math.pi / period + nz * 5)
    nn = np.zeros((g.h, g.w, 3), np.float32)
    nn[..., 2] = 1
    if vertical:
        nn[..., 0] = ph * folds
    else:
        nn[..., 1] = ph * folds
    g.put(m, col, tex=1 + (nz - 0.5) * 2 * var, n=nn, z=z)


def ground_light_pool(g: GB, cx, cy, rx, ry, col, k=0.3):
    """A soft emission pool on a surface (light falling through a door or a window onto snow)."""
    d = np.hypot((g.xx - cx) / rx, (g.yy - cy) / ry)
    f = np.clip(1 - d, 0, 1) ** 1.6
    g.em += lc(col)[None, None] * (f * k)[..., None] * g.cov[..., None]


# ================================================================================================= common objects
def window(g: GB, x0, y0, x1, y1, lit=0.0, seed=0, frame='#3a2e24', glass='#0e141c', warm='#f0b860', z=None,
           mullion=True, sill_snow=True, curtain=None, plant=False, figure=None, cross=True, frame_w=1):
    """A sash window: frame, panes (dark glass with a sky reflection, or lit with an interior: a curtain, a
    lamp's warm falloff, plants, a figure's silhouette), sill with snow."""
    fr = g.box(x0, y0, x1, y1)
    inner = g.box(x0 + frame_w, y0 + frame_w, x1 - frame_w, y1 - frame_w)
    g.put(fr & ~inner, frame, tex=tex_noise(g, 3, seed, 0.1), z=z)
    if lit > 0:
        cx, cy = (x0 + x1) / 2 + (hash2(seed, 1, 5) - 0.5) * (x1 - x0) * 0.5, y0 + (y1 - y0) * 0.35
        d = np.hypot((g.xx - cx) / max(4, (x1 - x0)), (g.yy - cy) / max(4, (y1 - y0)))
        f = np.clip(1.15 - d, 0.25, 1.0)
        e = lc(warm)[None, None] * (f * lit)[..., None]
        g.put(inner, '#3a2a1c', em=e, z=z)
        if curtain:
            cw = max(2, int((x1 - x0) * 0.22))
            for (a, b) in ((x0 + frame_w, x0 + frame_w + cw), (x1 - frame_w - cw, x1 - frame_w)):
                cm = g.box(a, y0 + frame_w, b, y1 - frame_w)
                g.put(cm, curtain, tex=1 + 0.25 * np.sin(g.xx * 2.2), em=lc(warm) * lit * 0.35, z=z)
        if plant:
            pm = g.ell((x0 + x1) / 2 - 3, y1 - 4, 3, 3) & inner
            g.put(pm, '#1e2a14', em=lc(warm) * lit * 0.08, z=z)
        if figure:
            fx, fh = figure
            hx_, top = x0 + (x1 - x0) * fx, y1 - fh
            body = g.poly([(hx_ - 4, y1 - 1), (hx_ - 3, top + 5), (hx_ + 3, top + 5), (hx_ + 4, y1 - 1)])
            head = g.ell(hx_, top + 2.5, 2.2, 2.6)
            g.put((body | head) & inner, '#140e0a', em=lc(warm) * lit * 0.12, z=z)
    else:
        refl = noise(g.w, g.h, 5, seed + 9, 2)
        grad = np.clip(1 - (g.yy - y0) / max(1, y1 - y0), 0, 1)
        g.put(inner, glass, tex=0.8 + 0.4 * refl * grad, z=z, gl=0.9)
    if mullion:
        mx = int((x0 + x1) // 2)
        g.put(g.box(mx, y0, mx + 1, y1) & inner, frame, z=z)
        if cross:
            my = int(y0 + (y1 - y0) * 0.38)
            g.put(g.box(x0, my, x1, my + 1) & inner, frame, z=z)
    sill = g.box(x0 - 1, y1, x1 + 1, y1 + 2)
    g.put(sill, '#5a5a58', z=z)
    if sill_snow:
        g.put(snow_on(sill, 2, seed), '#e2e8ee', n=(0, 0.9, 0.4), z=z)


def lattice_mast(g: GB, x, top, base, z, col='#2a2f36', w=5, seed=0):
    """A lattice floodlight mast: two legs and zig-zag bracing."""
    for dx in (-w // 2, w // 2):
        g.put(g.box(x + dx, top, x + dx + 1, base), col, z=z, gl=0.3)
    y = top + 2
    k = 0
    while y < base - 2:
        a = (x - w // 2, y) if k % 2 == 0 else (x + w // 2, y)
        b = (x + w // 2, y + w) if k % 2 == 0 else (x - w // 2, y + w)
        g.put(g.line([a, b], 0.5), col, z=z)
        y += w
        k += 1


def rail_side(g: GB, y, x0, x1, z, steel='#3c4248', sleeper='#2a2018', ballast='#3a3836', snowy=0.6, seed=0):
    """Side view of a track: ballast shoulder, sleepers ends, the rail head catching light."""
    bal = g.box(x0, y + 1, x1, y + 5)
    nz = noise(g.w, g.h, 3, seed, 2)
    g.put(bal, ballast, tex=tex_noise(g, 4, seed, 0.15), z=z + 1)
    for sx in range(int(x0) - (int(x0) % 9), int(x1), 9):
        if hash2(sx, 2, seed) > 0.45:
            g.put(g.box(sx, y + 1, sx + 5, y + 3), sleeper, z=z + 0.5)
    g.put(g.box(x0, y - 2, x1, y + 1), steel, z=z, gl=0.6)
    g.put(g.box(x0, y - 2, x1, y - 1), '#8a949c', z=z, gl=1.0, n=(0, 0.8, 0.6))
    if snowy > 0:
        sn = bal & ((nz < snowy + 0.25) | (g.yy > y + 2))
        g.put(sn, '#d6dde6', n=(0, 0.9, 0.4), z=z + 1)


def tiny(g: GB, x, base, h, coat='#2a2a30', hat=None, face=1, z=300.0, skin='#b08060', pose='stand', seed=0,
         hat_col=None, legs='#1a1a1e', carry=None, scarf=None):
    """A small far figure (h 6..24 px) painted into the G-buffer with rounded normals, so the shot's lights
    model it (rim from behind, key from the lamps).  pose: stand | walk1 | walk2 | arms_up | bend | sit."""
    k = h / 20.0
    top = base - h
    head_r = max(1.0, 1.6 * k)
    hx_ = x + face * 0.3 * k
    sh = top + head_r * 2 + 0.5
    hip = base - h * 0.42
    bw = max(2.0, 3.2 * k)
    hem = base - h * (0.22 if pose != 'sit' else 0.0)
    lean = {'bend': 3.0 * k * face}.get(pose, 0.0)
    pts = [(x - bw + lean * 0.3, sh + 0.5), (x + bw + lean * 0.3, sh + 0.5), (x + bw * 1.15, hem),
           (x - bw * 1.15, hem)]
    body = g.poly(pts)
    yy = g.yy
    xc = (g.xx - x) / (bw * 1.2)
    nn = np.stack([np.clip(xc, -1, 1) * 0.8, np.full_like(xc, 0.15), np.ones_like(xc)], -1)
    legm = np.zeros_like(body)
    for side in (-1, 1):
        st = 0.0
        if pose == 'walk1':
            st = side * 1.6 * k
        elif pose == 'walk2':
            st = -side * 1.6 * k
        legm |= g.line([(x + side * 0.9 * k, hem - 1), (x + side * 0.9 * k + st, base - 0.5)], max(0.5, 0.6 * k))
    g.put(legm, legs, n=nn, z=z)
    g.put(body, coat, n=nn, z=z, tex=tex_noise(g, 2, seed, 0.06))
    headm = g.ell(hx_ + lean, top + head_r, head_r, head_r * 1.1)
    hn = np.stack([np.clip((g.xx - hx_) / (head_r + 0.5), -1, 1), np.clip(-(yy - top - head_r) / (head_r + 0.5),
                   -1, 1), np.full_like(xc, 0.8)], -1)
    g.put(headm, skin, n=hn, z=z)
    if hat:
        hc = hat_col or coat
        if hat == 'cap':
            g.put(g.box(hx_ - head_r + lean, top - 0.5, hx_ + head_r + lean + face, top + head_r * 0.8), hc, z=z)
        elif hat == 'hat':
            g.put(g.box(hx_ - head_r - 1 + lean, top + head_r * 0.6, hx_ + head_r + 1 + lean, top + head_r * 0.9),
                  hc, z=z)
            g.put(g.box(hx_ - head_r * 0.8 + lean, top - 1, hx_ + head_r * 0.8 + lean, top + head_r * 0.7), hc, z=z)
        elif hat == 'scarf':
            g.put(g.ell(hx_ + lean, top + head_r * 0.8, head_r * 1.15, head_r * 1.05) & ~g.box(
                hx_ + face * head_r * 0.2 - 0.5 + lean, top + head_r * 0.6, hx_ + face * head_r * 1.5 + lean,
                top + head_r * 2), hc, z=z)
        elif hat == 'ushanka':
            g.put(g.ell(hx_ + lean, top + head_r * 0.6, head_r * 1.35, head_r * 0.95), hc, n=hn, z=z)
    if scarf:
        g.put(g.box(x - bw * 0.9, sh - 0.5, x + bw * 0.9, sh + 1.2 * k), scarf, z=z)
    arms = []
    if pose == 'arms_up':
        arms = [[(x - bw * 0.6, sh + 1), (x - bw * 0.9, top - 2 * k)], [(x + bw * 0.6, sh + 1), (x + bw * 0.9, top - 2 * k)]]
    elif pose == 'bend':
        arms = [[(x + face * bw * 0.5, sh + 1), (x + face * (bw + 3 * k), hip + 2 * k)]]
    else:
        arms = [[(x + face * bw * 0.7, sh + 1), (x + face * bw * 0.9, hip + 1)]]
    for a in arms:
        g.put(g.line(a, max(0.5, 0.65 * k)), coat, n=nn, z=z)
    if carry == 'bag':
        g.put(g.box(x + face * bw, hip, x + face * bw + 2.5 * k * face if face > 0 else x + face * bw, hip + 3 * k),
              '#3a2a1c', z=z)
    return body | headm | legm


# ================================================================================================= glow / FX sheets
def glow_sprite(w, h, blobs, step=6.0, ox=0, oy=0):
    """Additive glow sprite: blobs = [(cx, cy, rx, ry, (r, g, b), power)] -> dithered RGBA (black = clear)."""
    return Q3.glow_sprite(w, h, blobs, step, ox, oy)


def beam_sprite(w, h, x, y, ang_deg, length, half_deg, rgb, step=6.0, power=1.3, haze=0.6, seed=0):
    """An additive light cone (a floodlight in falling snow / haze) from (x, y) along ang (0 = down, + = toward
    +x), dithered steps, a little noise so the haze is not a clean wedge."""
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    dx, dy = xx + 0.5 - x, yy + 0.5 - y
    a = math.radians(ang_deg)
    ux, uy = math.sin(a), math.cos(a)
    along = dx * ux + dy * uy
    across = dx * uy - dy * ux
    half = math.tan(math.radians(half_deg)) * np.maximum(along, 0) + 1.5
    f = np.clip(1 - np.abs(across) / half, 0, 1) ** 0.8 * np.clip(1 - along / length, 0, 1) ** power
    f *= (along > 0)
    nz = noise(w, h, 9, seed, 3)
    f *= (1 - haze) + haze * nz
    a3 = f[..., None] * np.asarray(rgb, np.float32)[None, None]
    return VK.soft_quant(a3, step, 0, 0)


def puff_sheet(n, fw, fh, cols, seed, **kw):
    return VK.puff_sheet(n, fw, fh, cols, seed, **kw)


def flame_sheet(n=8, fw=26, fh=44, seed=1, cool=False):
    return Q3.flame_sheet(n, fw, fh, seed, cool)


def ember_sheet(n=4, w=3, h=3):
    return Q3.ember_sheet(n, w, h)


def hsheet(frames):
    return np.concatenate(frames, axis=1)


def blit(dst, src, x, y):
    """Alpha-over (straight, binary alpha) of an RGBA uint8 sprite at integer (x, y)."""
    return Q3.blit(dst, src, int(x), int(y))


def crop_alpha(rgba, pad=1):
    """Tight bounding box of the opaque pixels -> (sprite, x0, y0)."""
    ys, xs = np.nonzero(rgba[..., 3] > 0)
    if len(ys) == 0:
        return rgba[:1, :1], 0, 0
    y0, y1 = max(0, ys.min() - pad), min(rgba.shape[0], ys.max() + 1 + pad)
    x0, x1 = max(0, xs.min() - pad), min(rgba.shape[1], xs.max() + 1 + pad)
    return rgba[y0:y1, x0:x1].copy(), int(x0), int(y0)


# ================================================================================================= the game's rig
_RIG: dict = {}


def rig():
    """(characters, chargen_body, chargen_anim, chargen_core) with every cast table installed in memory."""
    if not _RIG:
        import characters as CH
        import characters_c4 as C4
        C4.install()
        try:                                     # the round-10 cast (cast stream), when it is delivered
            import importlib
            m5 = importlib.import_module('characters_c4p2')
            if hasattr(m5, 'install'):
                m5.install()
        except Exception:                        # noqa: BLE001 -- not delivered yet: stand-ins are recorded
            pass
        import chargen_anim as A
        import chargen_body as CB
        import chargen_core as CC
        _RIG.update(CH=CH, CB=CB, A=A, CC=CC)
    return _RIG['CH'], _RIG['CB'], _RIG['A'], _RIG['CC']


def spec_of(cid, standin=None):
    """A fresh rig spec of `cid` (deep copy, safe to recolour); a stand-in is recorded when `cid` is missing."""
    CH, CB, A, CC = rig()
    if cid in CH.CAST:
        STANDINS.pop(cid, None)
        return CH.CAST[cid](), cid
    if standin is None:
        raise KeyError(cid)
    STANDINS[cid] = standin
    return CH.CAST[standin](), standin


def recolor(spec, name, base_hex, scene=None):
    """Give material `name` a new 6-tone ramp around base_hex (chargen_core.make_ramp, the scene's tint)."""
    CH, CB, A, CC = rig()
    if name not in spec.names:
        return spec
    i = spec.names[name]
    spec.mats[i] = dataclasses.replace(spec.mats[i], ramp=CC.make_ramp(base_hex, scene or spec.scene))
    return spec


def add_mat(spec, name, ramp_hex, **kw):
    CH, CB, A, CC = rig()
    if name in spec.names:
        return spec.names[name]
    ramp = [np.array([*CC.hex_rgb(h), 255], np.uint8) for h in ramp_hex]
    spec.mats.append(CC.Material(name, ramp, **kw))
    spec.names[name] = len(spec.mats) - 1
    return spec.names[name]


def key_light(spec, side='left', up=0.55, front=0.5, ambient=None):
    """Point the rig's baked key at the shot's dominant light (left / right of the figure in frame space,
    for a figure facing +x) and mirror the outline directions with it."""
    s = 1 if side == 'right' else -1
    lt = spec.light
    spec.light = dataclasses.replace(
        lt, key=(s * 0.62, up, front), rim=(-s * 0.80, 0.42, -0.30),
        ambient=lt.ambient if ambient is None else ambient,
        lit_dirs=((s, 0), (s, -1), (0, -1)), shadow_dirs=((0, -1), (s, -1), (s, 0)),
        rim_dirs=((-s, 0), (-s, -1), (0, -1)), inline_dirs=((-s, 0), (0, 1), (-s, 1)))
    return spec


@contextlib.contextmanager
def wide_cells(width=48, height=56):
    """Render rig cells wider than 32 px (shovels, raised instruments): the pelvis stays centred."""
    CH, CB, A, CC = rig()
    old = (CB.CELL_W, CB.CELL_H, CB.CX)
    CB.CELL_W, CB.CX = int(width), width / 2.0 + 0.5
    try:
        yield
    finally:
        CB.CELL_W, CB.CELL_H, CB.CX = old


def rig_frames(spec, poses, view='side', width=32, hooks=()):
    """Render pose dicts -> [(rgba, normals, joints)].  hooks: [(layer, fn(fr, J, P, spec))] added for this call."""
    CH, CB, A, CC = rig()
    spec = copy.copy(spec)
    spec.hooks = dict(spec.hooks)
    spec.hooks[view] = list(spec.hooks.get(view, [])) + list(hooks)
    out = []
    with wide_cells(width):
        for P in poses:
            rgba, nm, fr, J = CB.render(spec, view, P)
            out.append((rgba, nm, J))
    return out


def fig_tint(rgba, nm, lights, x0, y0, z, pal=None, sky='#3a4658', gnd='#20242a', amb=0.35, gain=1.0, wrap=0.6,
             rim=0.0, flip=False):
    """Tint a rig cell by the shot's lights at its frame position (x0, y0 = top-left, z depth): the baked cel
    shading stays, the colour and level of the place's light multiply it (wrapped Lambert on the sheet's normal
    map, normalised by `gain`), an optional rim adds the back lights' edge; then the shot palette."""
    h, w = rgba.shape[:2]
    a = rgba[..., 3] > 0
    if nm is None:
        n = np.zeros((h, w, 3), np.float32)
        n[..., 2] = 1
    else:
        n = nm[..., :3].astype(np.float32) / 127.5 - 1.0
        if flip:
            n[..., 0] = -n[..., 0]
        n = nrm(n)
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    X, Y = xx + x0, yy + y0
    hemi = lc(gnd)[None, None] + (lc(sky) - lc(gnd))[None, None] * (0.5 + 0.5 * n[..., 1:2])
    acc = hemi * amb
    edge = np.zeros((h, w, 3), np.float32)
    for lt in lights:
        dx, dy, dz = lt.x - X, Y - lt.y, z - lt.z
        d = np.sqrt(dx * dx + dy * dy + dz * dz) + 1e-3
        lx, ly, lz = dx / d, dy / d, dz / d
        ndl = n[..., 0] * lx + n[..., 1] * ly + n[..., 2] * lz
        att = np.clip(1 - (d / lt.r) ** 2, 0, 1) ** lt.fall
        if lt.spot is not None:
            sdir, inner, outer = lt.spot
            sdir = nrm(np.asarray(sdir, np.float32))
            ca = -(lx * sdir[0] + ly * sdir[1] + lz * sdir[2])
            att = att * smooth(ca, math.cos(math.radians(outer)), math.cos(math.radians(inner)))
        lam = np.clip((ndl + wrap) / (1 + wrap), 0, 1)
        acc += lt.col[None, None] * (att * lam)[..., None]
        if rim > 0:
            grazing = np.clip(ndl, 0, 1) * np.clip(-lz + 0.2, 0, 1)
            edge += lt.col[None, None] * (att * grazing * rim)[..., None]
    base = to_lin(rgba[..., :3].astype(np.float32) / 255.0)
    out = base * acc * gain + edge
    res = np.zeros_like(rgba)
    if pal is None:
        res[..., :3] = np.round(to_srgb(out) * 255).astype(np.uint8)
        res[..., 3] = rgba[..., 3]
        return res
    return quant(out, pal, spread=0.0, dither=False, alpha=a)


# ================================================================================================= small helpers
def fliph(a):
    return np.ascontiguousarray(a[:, ::-1])


def clamp_safe(y):
    return max(SAFE[0], min(SAFE[1], y))


def put_layout(section, **kw):
    LAYOUT.setdefault(section, {}).update(kw)
