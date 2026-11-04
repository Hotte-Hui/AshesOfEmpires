"""pixelgen core -- shared pixel-art toolkit for ASHES OF EMPIRES: THE LAST WINTER.

Every environment / prop / character generator builds on this module so the whole game
shares one pixel grammar: palette ramps, ordered (Bayer) dithering, selective outlines,
clean clusters, height-derived normal maps for Godot 2D lighting and emission masks.

Conventions
-----------
* 1 pixel = 1 logical game pixel (world viewport is 640x360, human height ~46 px).
* Colours are RGBA uint8 numpy arrays; use hx('#RRGGBB').
* Layer.hgt is a height field (0..1, arbitrary units) -> normal map (OpenGL convention,
  +X right, +Y UP, encoded n*0.5+0.5).  Layer.nrm lets you paint explicit normals.
* Layer.em is an emission mask: pixels that glow and must NOT be darkened by scene light
  (lit windows, fire, lamps).  Saved as <name>_e.png when non-empty.
* save(base) writes <base>.png, <base>_n.png and optionally <base>_e.png.
Run with:  py -3 -P tools/pixelgen/<generator>.py   (no network, deterministic seeds).
"""
from __future__ import annotations

import json
import math
import os
from typing import Iterable, Sequence

import numpy as np
from PIL import Image

# --------------------------------------------------------------------------- colour
def hx(h: str, a: int = 255) -> np.ndarray:
    h = h.lstrip('#')
    return np.array([int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), a], np.uint8)


def mix(c1, c2, t: float) -> np.ndarray:
    c1 = np.asarray(c1, np.float32); c2 = np.asarray(c2, np.float32)
    out = c1 + (c2 - c1) * float(t)
    return np.clip(np.round(out), 0, 255).astype(np.uint8)


# Scene palettes (dark -> light within each ramp).  Derived from the reference analysis in
# documentation/ART_DIRECTION.md (median-cut measurements) and art-directed by hand.
PALETTES = {
    # Soviet industrial dawn (Karsk): sage/teal body, blue-black shadows, copper accents.
    'karsk': {
        'night':  ['#05090F', '#0A1219', '#0E1A20', '#13252B'],
        'teal':   ['#122126', '#1B3033', '#26403F', '#36534D', '#4A675C'],
        'sage':   ['#3E4E3D', '#53614F', '#6C7A62', '#839378', '#9DAF91', '#B8C7A8'],
        'sky':    ['#6F8576', '#83998A', '#98AD9A', '#AFC1AA', '#C7D3BA', '#DCE2C8'],
        'stone':  ['#2A2D2C', '#3B3F3B', '#4F534C', '#666A60', '#7F8275', '#9A9B8B'],
        'rust':   ['#2E1C1A', '#4A2A22', '#6B3B2C', '#8D5542', '#AF6C47', '#C98A5C'],
        'copper': ['#7A3E26', '#BA775B', '#DCA16E', '#F0C487', '#FBE3AE'],
        'snow':   ['#7E8E8C', '#A3B1AD', '#C4CFC8', '#DEE5DC', '#F1F4EC'],
        'wood':   ['#22180F', '#33251A', '#4A3626', '#634B35', '#7D6347'],
    },
    # Berlin exterior at dusk: terracotta / ochre stone, violet-black shadows, cold blue greys.
    'berlin': {
        'night':  ['#120C14', '#1B1520', '#211623', '#2A2130'],
        'violet': ['#25202B', '#342F37', '#443B43', '#57494D'],
        'stone':  ['#4A3A35', '#5F4A40', '#7A5E4E', '#94735C', '#AE8A6C', '#C9A585'],
        'ochre':  ['#5F4530', '#735145', '#8D5542', '#AF6C47', '#D07744', '#E5945A'],
        'glow':   ['#E5945A', '#F0AE6E', '#F4BA81', '#F8D2A0', '#FCE9C8'],
        'steel':  ['#1E2329', '#2F363F', '#454E58', '#5F6973', '#7C8690', '#A3ACB4'],
        'patina': ['#1E2E2C', '#2C4440', '#3E5D55', '#56776A', '#73927F'],
        'snow':   ['#6E6A73', '#8F8A92', '#B2ACB0', '#D2CCCB', '#ECE6E0'],
    },
    # Berlin archive interior: deep navy-teal room, amber lamps, paper.
    'archive': {
        'night':  ['#04090D', '#06151D', '#0B1C24', '#14272B'],
        'wall':   ['#1A2A2E', '#24373A', '#354448', '#4A5A5B', '#62716E'],
        'wood':   ['#2A1B16', '#3D2820', '#55372A', '#6E4A37', '#805C4E', '#9C7560'],
        'amber':  ['#6E3F22', '#9A5A2F', '#B57B59', '#D79A62', '#F2C27E', '#FFE3AA'],
        'paper':  ['#6E6A5C', '#8E8A78', '#B0AA93', '#CEC6AA', '#E6DEC2', '#F5EFDA'],
        'blue':   ['#1D2A3A', '#2B3C50', '#3E546B', '#58718A', '#7A93A8', '#A7BCCB'],
        'ink':    ['#1A1C2A', '#2E3248', '#7A2A26', '#A8382E'],
    },
    # Monochrome transition / memory scenes (sepia-grey dust).
    'sepia': {
        'tone':   ['#1E1C1D', '#2A2829', '#343232', '#494545', '#5E5A54', '#68635B',
                   '#7A7364', '#857F6E', '#969185', '#ACA99F', '#C4C0B4', '#DCD8CC'],
        'red':    ['#4A1712', '#7A2218', '#A8382E', '#C8503C'],
    },
}


def pal(scene: str, ramp: str) -> list[np.ndarray]:
    return [hx(c) for c in PALETTES[scene][ramp]]


def all_colors(scene: str) -> list[np.ndarray]:
    out = []
    for r in PALETTES[scene].values():
        out += [hx(c) for c in r]
    return out


# --------------------------------------------------------------------------- dithering
BAYER4 = np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]], np.float32) / 16.0 + 1 / 32


def _bayer8() -> np.ndarray:
    b = np.zeros((8, 8), np.float32)
    for y in range(8):
        for x in range(8):
            v = 0; xc = x ^ y; yc = y
            for bit in range(3):
                v = (v << 2) | (((xc >> (2 - bit)) & 1) << 1) | ((yc >> (2 - bit)) & 1)
            b[y, x] = v
    return b / 64.0 + 1 / 128


BAYER8 = _bayer8()


def bayer(w: int, h: int, x0: int = 0, y0: int = 0, size: int = 4) -> np.ndarray:
    m = BAYER4 if size == 4 else BAYER8
    n = m.shape[0]
    ys = (np.arange(h) + y0) % n
    xs = (np.arange(w) + x0) % n
    return m[ys[:, None], xs[None, :]]


# --------------------------------------------------------------------------- noise
def value_noise(w: int, h: int, cell: float, seed: int = 0, octaves: int = 4,
                persistence: float = 0.5, tile_x: bool = False) -> np.ndarray:
    """Smooth fBm value noise in [0,1], shape (h, w)."""
    rng = np.random.default_rng(seed)
    out = np.zeros((h, w), np.float32)
    amp, tot, c = 1.0, 0.0, float(cell)
    for _ in range(octaves):
        gw = int(math.ceil(w / c)) + 2
        gh = int(math.ceil(h / c)) + 2
        grid = rng.random((gh, gw)).astype(np.float32)
        if tile_x:
            per = max(1, int(round(w / c)))
            grid[:, per:] = grid[:, :gw - per][:, :gw - per] if gw - per > 0 else grid[:, per:]
            for i in range(per, gw):
                grid[:, i] = grid[:, i % per]
        ys = np.arange(h) / c
        xs = np.arange(w) / c
        y0 = np.floor(ys).astype(int); x0 = np.floor(xs).astype(int)
        fy = ys - y0; fx = xs - x0
        fy = fy * fy * (3 - 2 * fy); fx = fx * fx * (3 - 2 * fx)
        a = grid[y0[:, None], x0[None, :]]
        b = grid[y0[:, None], x0[None, :] + 1]
        cc = grid[y0[:, None] + 1, x0[None, :]]
        d = grid[y0[:, None] + 1, x0[None, :] + 1]
        top = a + (b - a) * fx[None, :]
        bot = cc + (d - cc) * fx[None, :]
        out += amp * (top + (bot - top) * fy[:, None])
        tot += amp
        amp *= persistence
        c = max(1.0, c / 2)
    return out / tot


def white_noise(w: int, h: int, seed: int = 0) -> np.ndarray:
    return np.random.default_rng(seed).random((h, w)).astype(np.float32)


# --------------------------------------------------------------------------- layer
class Layer:
    """A paintable RGBA layer with height field, optional explicit normals and emission."""

    def __init__(self, w: int, h: int, name: str = 'layer'):
        self.w, self.h, self.name = int(w), int(h), name
        self.c = np.zeros((self.h, self.w, 4), np.uint8)
        self.hgt = np.zeros((self.h, self.w), np.float32)
        self.nrm = np.full((self.h, self.w, 3), np.nan, np.float32)
        self.em = np.zeros((self.h, self.w, 4), np.uint8)

    # ---- helpers
    def _box(self, x: int, y: int, w: int, h: int):
        x0, y0 = max(0, int(x)), max(0, int(y))
        x1, y1 = min(self.w, int(x) + int(w)), min(self.h, int(y) + int(h))
        return x0, y0, x1, y1

    def _put(self, mask: np.ndarray, x0: int, y0: int, col, hgt=None, em=None):
        """mask: bool array placed at (x0,y0); writes colour/height/emission where True."""
        mh, mw = mask.shape
        X0, Y0 = max(0, x0), max(0, y0)
        X1, Y1 = min(self.w, x0 + mw), min(self.h, y0 + mh)
        if X1 <= X0 or Y1 <= Y0:
            return
        m = mask[Y0 - y0:Y1 - y0, X0 - x0:X1 - x0]
        if col is not None:
            col = np.asarray(col, np.uint8)
            if col.ndim == 1:
                self.c[Y0:Y1, X0:X1][m] = col
            else:  # per-pixel colour array aligned with mask
                self.c[Y0:Y1, X0:X1][m] = col[Y0 - y0:Y1 - y0, X0 - x0:X1 - x0][m]
        if hgt is not None:
            if np.isscalar(hgt):
                self.hgt[Y0:Y1, X0:X1][m] = hgt
            else:
                self.hgt[Y0:Y1, X0:X1][m] = np.asarray(hgt)[Y0 - y0:Y1 - y0, X0 - x0:X1 - x0][m]
        if em is not None:
            self.em[Y0:Y1, X0:X1][m] = np.asarray(em, np.uint8)

    # ---- primitives
    def px(self, x, y, col, hgt=None, em=None):
        x, y = int(x), int(y)
        if 0 <= x < self.w and 0 <= y < self.h:
            self.c[y, x] = col
            if hgt is not None:
                self.hgt[y, x] = hgt
            if em is not None:
                self.em[y, x] = em

    def rect(self, x, y, w, h, col, hgt=None, em=None):
        x0, y0, x1, y1 = self._box(x, y, w, h)
        if x1 <= x0 or y1 <= y0:
            return
        self.c[y0:y1, x0:x1] = col
        if hgt is not None:
            self.hgt[y0:y1, x0:x1] = hgt
        if em is not None:
            self.em[y0:y1, x0:x1] = em

    def hline(self, x, y, w, col, hgt=None):
        self.rect(x, y, w, 1, col, hgt)

    def vline(self, x, y, h, col, hgt=None):
        self.rect(x, y, 1, h, col, hgt)

    def line(self, x0, y0, x1, y1, col, hgt=None, em=None):
        x0, y0, x1, y1 = int(round(x0)), int(round(y0)), int(round(x1)), int(round(y1))
        dx, dy = abs(x1 - x0), -abs(y1 - y0)
        sx, sy = (1 if x0 < x1 else -1), (1 if y0 < y1 else -1)
        err = dx + dy
        while True:
            self.px(x0, y0, col, hgt, em)
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy; x0 += sx
            if e2 <= dx:
                err += dx; y0 += sy

    def polyline(self, pts, col, hgt=None):
        for a, b in zip(pts[:-1], pts[1:]):
            self.line(a[0], a[1], b[0], b[1], col, hgt)

    def poly_mask(self, pts: Sequence[tuple]) -> tuple[np.ndarray, int, int]:
        xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
        x0, x1 = int(math.floor(min(xs))), int(math.ceil(max(xs)))
        y0, y1 = int(math.floor(min(ys))), int(math.ceil(max(ys)))
        w, h = max(1, x1 - x0 + 1), max(1, y1 - y0 + 1)
        mask = np.zeros((h, w), bool)
        n = len(pts)
        for row in range(h):
            yc = y0 + row + 0.5
            xs_cross = []
            for i in range(n):
                ax, ay = pts[i]; bx, by = pts[(i + 1) % n]
                if (ay <= yc < by) or (by <= yc < ay):
                    xs_cross.append(ax + (yc - ay) * (bx - ax) / (by - ay))
            xs_cross.sort()
            for k in range(0, len(xs_cross) - 1, 2):
                a = int(math.ceil(xs_cross[k] - 0.5)) - x0
                b = int(math.floor(xs_cross[k + 1] - 0.5)) - x0
                if b >= a:
                    mask[row, max(0, a):min(w, b + 1)] = True
        return mask, x0, y0

    def poly(self, pts, col, hgt=None, em=None):
        m, x0, y0 = self.poly_mask(pts)
        self._put(m, x0, y0, col, hgt, em)
        return m, x0, y0

    def ellipse_mask(self, cx, cy, rx, ry):
        x0, y0 = int(math.floor(cx - rx)), int(math.floor(cy - ry))
        w, h = int(math.ceil(2 * rx)) + 2, int(math.ceil(2 * ry)) + 2
        yy, xx = np.mgrid[0:h, 0:w]
        dx = (xx + x0 + 0.5 - cx) / max(rx, 0.5)
        dy = (yy + y0 + 0.5 - cy) / max(ry, 0.5)
        return (dx * dx + dy * dy) <= 1.0, x0, y0

    def ellipse(self, cx, cy, rx, ry, col, hgt=None, em=None):
        m, x0, y0 = self.ellipse_mask(cx, cy, rx, ry)
        self._put(m, x0, y0, col, hgt, em)
        return m, x0, y0

    def dome_height(self, cx, cy, rx, ry, base=0.0, amp=1.0):
        """Adds a rounded height bump (pillow) inside an ellipse -- gives soft normals."""
        m, x0, y0 = self.ellipse_mask(cx, cy, rx, ry)
        h, w = m.shape
        yy, xx = np.mgrid[0:h, 0:w]
        dx = (xx + x0 + 0.5 - cx) / max(rx, 0.5)
        dy = (yy + y0 + 0.5 - cy) / max(ry, 0.5)
        z = np.sqrt(np.clip(1 - dx * dx - dy * dy, 0, 1)) * amp + base
        self._put(m, x0, y0, None, hgt=z)

    def vgrad(self, x, y, w, h, cols: Sequence, dither: bool = True, dsize: int = 4):
        """Vertical gradient through colour list with ordered-dither transitions."""
        x0, y0, x1, y1 = self._box(x, y, w, h)
        if x1 <= x0 or y1 <= y0:
            return
        n = len(cols) - 1
        t = (np.arange(y0, y1) - y) / max(1, h - 1) * n
        T = np.repeat(t[:, None], x1 - x0, axis=1)
        idx = np.floor(T).astype(int)
        frac = T - idx
        if dither:
            thr = bayer(x1 - x0, y1 - y0, x0, y0, dsize)
            idx = idx + (frac > thr)
        else:
            idx = np.round(T).astype(int)
        idx = np.clip(idx, 0, n)
        carr = np.stack([np.asarray(c, np.uint8) for c in cols])
        self.c[y0:y1, x0:x1] = carr[idx]

    def tone_fill(self, mask: np.ndarray, x0: int, y0: int, t: np.ndarray, cols: Sequence,
                  dither: bool = True, hgt=None):
        """Fill mask with colours chosen from ramp by tone t in [0,1] (same shape as mask)."""
        n = len(cols) - 1
        T = np.clip(t, 0, 1) * n
        idx = np.floor(T).astype(int)
        if dither:
            thr = bayer(mask.shape[1], mask.shape[0], x0, y0)
            idx = idx + ((T - idx) > thr)
        idx = np.clip(idx, 0, n)
        carr = np.stack([np.asarray(c, np.uint8) for c in cols])
        self._put(mask, x0, y0, carr[idx], hgt)

    # ---- compositing
    def blit(self, o: 'Layer', x: int, y: int, height_offset: float = 0.0):
        """Alpha-over blit (binary alpha: pixel art). Copies height/normal/emission."""
        X0, Y0 = max(0, x), max(0, y)
        X1, Y1 = min(self.w, x + o.w), min(self.h, y + o.h)
        if X1 <= X0 or Y1 <= Y0:
            return
        sub = o.c[Y0 - y:Y1 - y, X0 - x:X1 - x]
        m = sub[..., 3] > 127
        self.c[Y0:Y1, X0:X1][m] = sub[m]
        self.hgt[Y0:Y1, X0:X1][m] = o.hgt[Y0 - y:Y1 - y, X0 - x:X1 - x][m] + height_offset
        on = o.nrm[Y0 - y:Y1 - y, X0 - x:X1 - x]
        self.nrm[Y0:Y1, X0:X1][m] = on[m]
        oe = o.em[Y0 - y:Y1 - y, X0 - x:X1 - x]
        em = m & (oe[..., 3] > 0)
        self.em[Y0:Y1, X0:X1][em] = oe[em]

    def alpha(self) -> np.ndarray:
        return self.c[..., 3] > 127

    def outline(self, col, outer: bool = True, diagonal: bool = False, only_where=None):
        """1-px outline. outer=True draws outside the shape, else on its edge pixels."""
        a = self.alpha()
        p = np.pad(a, 1)
        nb = p[:-2, 1:-1] | p[2:, 1:-1] | p[1:-1, :-2] | p[1:-1, 2:]
        if diagonal:
            nb |= p[:-2, :-2] | p[:-2, 2:] | p[2:, :-2] | p[2:, 2:]
        if outer:
            m = nb & ~a
        else:
            inner = p[:-2, 1:-1] & p[2:, 1:-1] & p[1:-1, :-2] & p[1:-1, 2:]
            m = a & ~inner
        if only_where is not None:
            m &= only_where
        self.c[m] = col
        return m

    def clean_orphans(self, passes: int = 1):
        """Remove isolated single pixels of a colour (cluster cleanup)."""
        for _ in range(passes):
            c = self.c.astype(np.int32)
            key = (c[..., 0] << 24) | (c[..., 1] << 16) | (c[..., 2] << 8) | c[..., 3]
            p = np.pad(key, 1, mode='edge')
            same = ((p[:-2, 1:-1] == key).astype(int) + (p[2:, 1:-1] == key) +
                    (p[1:-1, :-2] == key) + (p[1:-1, 2:] == key))
            orphan = same == 0
            # replace with left neighbour (or up) colour
            src = np.roll(self.c, 1, axis=1)
            self.c[orphan] = src[orphan]

    def darken_bottom(self, cols_from: Sequence, cols_to: Sequence, height: int, seed: int = 1):
        """Grime: remaps colours near the bottom towards darker ramp entries using noise."""
        pass  # generators implement scene-specific grime with remap()

    def remap(self, mapping: dict, mask: np.ndarray | None = None):
        """Replace exact colours: mapping {hex_from: hex_to}. Optional bool mask."""
        for a, b in mapping.items():
            ca, cb = hx(a), hx(b)
            m = np.all(self.c == ca, axis=-1)
            if mask is not None:
                m &= mask
            self.c[m] = cb

    def shift_ramp(self, ramp: Sequence, steps: int, mask: np.ndarray):
        """Move pixels that use colours of `ramp` by `steps` along it (darker <0, lighter >0)."""
        carr = [np.asarray(c, np.uint8) for c in ramp]
        res = self.c.copy()
        for i, c in enumerate(carr):
            j = int(np.clip(i + steps, 0, len(carr) - 1))
            m = np.all(self.c == c, axis=-1) & mask
            res[m] = carr[j]
        self.c = res

    # ---- normals / output
    def normal_map(self, strength: float = 3.0) -> np.ndarray:
        hgt = self.hgt
        p = np.pad(hgt, 1, mode='edge')
        dx = (p[1:-1, 2:] - p[1:-1, :-2]) * 0.5
        dy = (p[2:, 1:-1] - p[:-2, 1:-1]) * 0.5
        # image y grows downward; OpenGL normal map: +Y = up => ny = +dh/dy(image)
        n = np.stack([-dx * strength, dy * strength, np.ones_like(hgt)], -1)
        over = ~np.isnan(self.nrm[..., 0])
        n[over] = self.nrm[over]
        n /= np.linalg.norm(n, axis=-1, keepdims=True) + 1e-6
        img = np.clip((n * 0.5 + 0.5) * 255, 0, 255).astype(np.uint8)
        a = self.c[..., 3:4]
        return np.concatenate([img, a], -1)

    def paint_normal(self, mask: np.ndarray, x0: int, y0: int, n: Sequence[float]):
        v = np.asarray(n, np.float32); v = v / (np.linalg.norm(v) + 1e-6)
        mh, mw = mask.shape
        X0, Y0 = max(0, x0), max(0, y0)
        X1, Y1 = min(self.w, x0 + mw), min(self.h, y0 + mh)
        m = mask[Y0 - y0:Y1 - y0, X0 - x0:X1 - x0]
        self.nrm[Y0:Y1, X0:X1][m] = v

    def save(self, base: str, normal: bool = True, emission: bool | None = None,
             strength: float = 3.0):
        os.makedirs(os.path.dirname(base) or '.', exist_ok=True)
        Image.fromarray(self.c, 'RGBA').save(base + '.png')
        if normal:
            Image.fromarray(self.normal_map(strength), 'RGBA').save(base + '_n.png')
        has_em = bool(self.em[..., 3].any())
        if emission or (emission is None and has_em):
            Image.fromarray(self.em, 'RGBA').save(base + '_e.png')
        return {'file': os.path.basename(base) + '.png', 'w': self.w, 'h': self.h,
                'normal': bool(normal), 'emission': bool(emission or (emission is None and has_em))}

    def image(self) -> Image.Image:
        return Image.fromarray(self.c, 'RGBA')


# --------------------------------------------------------------------------- curves
def bezier(pts: Sequence[tuple], n: int = 64) -> list[tuple]:
    pts = np.asarray(pts, np.float32)
    out = []
    for i in range(n + 1):
        t = i / n
        p = pts.copy()
        while len(p) > 1:
            p = p[:-1] * (1 - t) + p[1:] * t
        out.append((float(p[0][0]), float(p[0][1])))
    return out


def catenary(x0, y0, x1, y1, sag: float, n: int = 0) -> list[tuple]:
    n = n or max(2, int(abs(x1 - x0)))
    out = []
    for i in range(n + 1):
        t = i / n
        x = x0 + (x1 - x0) * t
        y = y0 + (y1 - y0) * t + sag * 4 * t * (1 - t)
        out.append((x, y))
    return out


# --------------------------------------------------------------------------- reusable elements
def sky(layer: Layer, cols: Sequence, horizon_glow: tuple | None = None, seed: int = 0):
    """Full-layer sky gradient (top->bottom) with optional elliptical glow (x, y, rx, ry, cols)."""
    layer.vgrad(0, 0, layer.w, layer.h, cols)
    if horizon_glow:
        gx, gy, rx, ry, gcols = horizon_glow
        yy, xx = np.mgrid[0:layer.h, 0:layer.w]
        d = np.sqrt(((xx - gx) / rx) ** 2 + ((yy - gy) / ry) ** 2)
        t = np.clip(1 - d, 0, 1) ** 1.5
        m = t > 0.02
        thr = bayer(layer.w, layer.h)
        n = len(gcols)
        T = t * n
        idx = np.floor(T).astype(int) + ((T - np.floor(T)) > thr)
        sel = m & (idx >= 1)
        carr = np.stack([np.asarray(c, np.uint8) for c in gcols])
        layer.c[sel] = carr[np.clip(idx[sel] - 1, 0, n - 1)]
    layer.hgt[:] = 0


def puffs(layer: Layer, circles, cols: Sequence, light=(-0.55, -0.75, 0.45), ambient: float = 0.18,
          flat_bottom: float | None = None, bottom_dark: float = 0.35, seed: int = 0, gaps=None,
          height_scale: float = 1.0):
    """Volumetric pixel blobs (clouds, smoke, steam, foliage).  circles: [(cx, cy, r), ...].
    Builds a max-of-spherical-caps height field, lights it (Lambert, light from upper-left by
    default) and snaps the tone onto `cols` (dark -> light) with ordered dither.  Returns mask."""
    if not circles:
        return None
    xs0 = int(math.floor(min(c[0] - c[2] for c in circles))) - 1
    ys0 = int(math.floor(min(c[1] - c[2] for c in circles))) - 1
    xs1 = int(math.ceil(max(c[0] + c[2] for c in circles))) + 2
    ys1 = int(math.ceil(max(c[1] + c[2] for c in circles))) + 2
    W, H = xs1 - xs0, ys1 - ys0
    field = np.zeros((H, W), np.float32)
    for cx, cy, r in circles:
        r = max(0.6, float(r))
        bx0, by0 = int(math.floor(cx - r)) - xs0, int(math.floor(cy - r)) - ys0
        bw, bh = int(math.ceil(2 * r)) + 2, int(math.ceil(2 * r)) + 2
        yy, xx = np.mgrid[0:bh, 0:bw]
        dx = (xx + bx0 + xs0 + 0.5 - cx) / r
        dy = (yy + by0 + ys0 + 0.5 - cy) / r
        cap = np.sqrt(np.clip(1 - dx * dx - dy * dy, 0, 1)) * r * height_scale
        cap[(dx * dx + dy * dy) > 1] = 0
        sl = field[by0:by0 + bh, bx0:bx0 + bw]
        cap = cap[:sl.shape[0], :sl.shape[1]]
        np.maximum(sl, cap, out=sl)
    mask = field > 0
    if flat_bottom is not None:
        rows = np.arange(H)[:, None] + ys0
        mask &= rows <= flat_bottom
    if gaps is not None:  # (cell, threshold) noise holes for wispy edges
        nz = value_noise(W, H, gaps[0], seed + 11, octaves=3)
        edge = field < np.percentile(field[mask], 35) if mask.any() else mask
        mask &= ~(edge & (nz < gaps[1]))
    p = np.pad(field, 1, mode='edge')
    gx = (p[1:-1, 2:] - p[1:-1, :-2]) * 0.5
    gy = (p[2:, 1:-1] - p[:-2, 1:-1]) * 0.5
    n = np.stack([-gx, -gy, np.ones_like(field) * 1.2], -1)
    n /= np.linalg.norm(n, axis=-1, keepdims=True)
    L = np.asarray(light, np.float32); L /= np.linalg.norm(L)
    lam = np.clip((n * L).sum(-1), 0, 1)
    if mask.any():
        rows = (np.arange(H)[:, None] + ys0).astype(np.float32)
        top, bot = rows[mask[:, :1].any(1) | True].min(), rows.max()
        yrel = (rows - (ys0)) / max(1, H - 1)
    else:
        yrel = np.zeros((H, 1), np.float32)
    tone = ambient + lam * (1 - ambient) - bottom_dark * np.clip(yrel - 0.35, 0, 1)
    tone = np.clip(tone, 0, 1)
    p = np.pad(mask, 1)
    nb = p[:-2, 1:-1].astype(int) + p[2:, 1:-1] + p[1:-1, :-2] + p[1:-1, 2:]
    mask = (mask & (nb >= 2)) | (~mask & (nb >= 4))
    layer.tone_fill(mask, xs0, ys0, tone, cols)
    sub = np.zeros_like(field); sub[mask] = field[mask] / (field.max() + 1e-6)
    layer._put(mask, xs0, ys0, None, hgt=sub * 0.8)
    return mask


def cumulus(layer: Layer, x: float, y_base: float, width: float, height: float, cols: Sequence,
            seed: int = 0, density: float = 1.0, **kw):
    """One cumulus / cloud bank: big rounded lobes over a mostly flat base."""
    rng = np.random.default_rng(seed)
    circles = []
    n = max(4, int(width / max(4.0, height * 0.35) * 2.2 * density))
    for i in range(n):
        t = rng.random()
        env = math.sin(math.pi * t) ** 0.7  # taller in the middle
        r = height * (0.25 + 0.55 * env) * rng.uniform(0.6, 1.0)
        cx = x + t * width
        cy = y_base - r * rng.uniform(0.35, 0.8) - env * height * 0.25
        circles.append((cx, cy, r))
        if rng.random() < 0.5:  # small satellite lobe
            circles.append((cx + rng.uniform(-r, r), cy - r * 0.6, r * rng.uniform(0.3, 0.55)))
    return puffs(layer, circles, cols, flat_bottom=y_base + rng.uniform(0, 2), seed=seed, **kw)


def clouds(layer: Layer, y_top: int, y_bot: int, cols: Sequence, seed: int = 0, count: int = 7,
           min_w: float = 60, max_w: float = 220, wrap: bool = True, **kw):
    """Scatter several cumulus banks between y_top and y_bot (bigger ones lower)."""
    rng = np.random.default_rng(seed)
    for i in range(count):
        wdt = rng.uniform(min_w, max_w)
        x = rng.uniform(-wdt * 0.3, layer.w - wdt * 0.7)
        yb = rng.uniform(y_top + (y_bot - y_top) * 0.35, y_bot)
        hgt = wdt * rng.uniform(0.18, 0.32)
        cumulus(layer, x, yb, wdt, hgt, cols, seed=seed * 101 + i, **kw)
        if wrap and x + wdt > layer.w:
            cumulus(layer, x - layer.w, yb, wdt, hgt, cols, seed=seed * 101 + i, **kw)


def smoke_ribbon(layer: Layer, path: Sequence[tuple], w0: float, w1: float, cols: Sequence,
                 seed: int = 0, gaps: float = 0.22, lumpiness: float = 0.45, **kw):
    """Twisting volumetric smoke ribbon (industrial skies). cols: dark core -> lit edge."""
    rng = np.random.default_rng(seed)
    L = sum(math.dist(a, b) for a, b in zip(path[:-1], path[1:]))
    pts = bezier(path, n=max(30, int(L / 1.2)))
    nz = value_noise(len(pts) + 2, 2, 7, seed, octaves=3)[0]
    circles = []
    for i, (px_, py_) in enumerate(pts):
        t = i / max(1, len(pts) - 1)
        r = (w0 + (w1 - w0) * t) * 0.5 * (1 - lumpiness + lumpiness * 2 * nz[i])
        if t > 0.55 and rng.random() < gaps * (t - 0.4):
            continue
        circles.append((px_, py_, max(0.8, r)))
        if rng.random() < 0.25 * t:
            circles.append((px_ + rng.uniform(-r, r), py_ + rng.uniform(-r, r) * 0.6, r * rng.uniform(0.4, 0.7)))
    return puffs(layer, circles, cols, seed=seed, bottom_dark=0.1, ambient=0.12, **kw)


def window_grid(layer: Layer, x: int, y: int, cols_n: int, rows_n: int, ww: int, wh: int,
                gx: int, gy: int, frame, glass_dark, glass_light=None, lit=None,
                lit_prob: float = 0.0, broken_prob: float = 0.0, boarded=None,
                boarded_prob: float = 0.0, seed: int = 0, recess: float = -0.35):
    """Grid of windows on a facade. Returns list of lit window rects (for light placement)."""
    rng = np.random.default_rng(seed)
    lit_rects = []
    for r in range(rows_n):
        for c in range(cols_n):
            wx, wy = x + c * (ww + gx), y + r * (wh + gy)
            roll = rng.random()
            layer.rect(wx - 1, wy - 1, ww + 2, wh + 2, frame, hgt=0.15)
            if roll < broken_prob:
                layer.rect(wx, wy, ww, wh, glass_dark, hgt=recess - 0.2)
                # jagged shard
                if ww > 2 and wh > 3:
                    layer.px(wx + rng.integers(0, ww), wy, frame)
            elif lit is not None and roll < broken_prob + lit_prob:
                layer.rect(wx, wy, ww, wh, lit, hgt=recess, em=lit)
                lit_rects.append((wx, wy, ww, wh))
            elif boarded is not None and roll < broken_prob + lit_prob + boarded_prob:
                layer.rect(wx, wy, ww, wh, boarded, hgt=0.05)
                for k in range(0, wh, 2):
                    layer.hline(wx, wy + k, ww, frame)
            else:
                layer.rect(wx, wy, ww, wh, glass_dark, hgt=recess)
                if glass_light is not None and ww >= 2:
                    layer.px(wx, wy, glass_light)  # cold sky reflection pixel
                    if wh > 3 and rng.random() < 0.5:
                        layer.px(wx + 1, wy, glass_light)
    return lit_rects


def truss(layer: Layer, x0, y0, x1, y1, depth: int, col, step: int = 6, hgt: float = 0.3):
    """Lattice girder between two points (crane arms, bridges, towers)."""
    L = math.dist((x0, y0), (x1, y1))
    if L < 1:
        return
    ux, uy = (x1 - x0) / L, (y1 - y0) / L
    nx, ny = -uy * depth, ux * depth
    layer.line(x0, y0, x1, y1, col, hgt)
    layer.line(x0 + nx, y0 + ny, x1 + nx, y1 + ny, col, hgt)
    k, flip = 0.0, False
    while k <= L:
        ax, ay = x0 + ux * k, y0 + uy * k
        bx, by = ax + ux * step + nx, ay + uy * step + ny
        if flip:
            layer.line(ax + nx, ay + ny, ax + ux * step, ay + uy * step, col, hgt)
        else:
            layer.line(ax, ay, bx, by, col, hgt)
        layer.line(ax, ay, ax + nx, ay + ny, col, hgt)
        flip = not flip
        k += step


def wire(layer: Layer, x0, y0, x1, y1, sag: float, col):
    layer.polyline([(round(a), round(b)) for a, b in catenary(x0, y0, x1, y1, sag)], col)


def snow_caps(layer: Layer, cols: Sequence, depth: int = 2, seed: int = 0, coverage: float = 0.85,
              mask: np.ndarray | None = None):
    """Adds snow on every upward-facing top edge of opaque pixels (roofs, ledges)."""
    a = layer.alpha() if mask is None else mask
    rng = np.random.default_rng(seed)
    top = a & ~np.vstack([np.zeros((1, layer.w), bool), a[:-1]])
    noise = value_noise(layer.w, 1, 6, seed, octaves=2)[0]
    ys, xs = np.nonzero(top)
    for yv, xv in zip(ys, xs):
        if noise[xv] < (1 - coverage):
            continue
        d = depth + (1 if noise[xv] > 0.75 else 0)
        for k in range(d):
            yk = yv + k
            if yk < layer.h and a[yk, xv]:
                layer.c[yk, xv] = cols[-1 - min(k, len(cols) - 1)] if k < len(cols) else cols[0]
                layer.hgt[yk, xv] += 0.3
                layer.nrm[yk, xv] = (0.0, 0.8, 0.6)


def grass_tufts(layer: Layer, x0: int, x1: int, ybase: int, cols: Sequence, density: float = 0.6,
                hmax: int = 7, seed: int = 0):
    rng = np.random.default_rng(seed)
    for x in range(int(x0), int(x1)):
        if rng.random() > density:
            continue
        hgt = int(rng.integers(2, hmax + 1))
        lean = rng.choice([-1, 0, 0, 1])
        col = cols[int(rng.integers(0, len(cols)))]
        for k in range(hgt):
            xx = x + (lean if k > hgt * 0.6 else 0)
            layer.px(xx, ybase - k, col, hgt=0.2 + k * 0.03)


def rubble(layer: Layer, x0: int, x1: int, ybase: int, cols: Sequence, n: int = 30, seed: int = 0,
           max_r: float = 3.5):
    rng = np.random.default_rng(seed)
    for _ in range(n):
        x = rng.uniform(x0, x1); r = rng.uniform(0.8, max_r)
        y = ybase - rng.uniform(0, r)
        m, mx, my = layer.ellipse_mask(x, y, r * 1.3, r)
        hh, ww = m.shape
        yy, xx = np.mgrid[0:hh, 0:ww]
        tone = np.clip(0.75 - (yy / max(1, hh - 1)) * 0.6 - (xx / max(1, ww - 1)) * 0.2, 0, 1)
        layer.tone_fill(m, mx, my, tone, cols)
        layer.dome_height(x, y, r * 1.3, r, amp=0.6)


def atmos(layer: Layer, fog, amount: float, palette_cols: Sequence | None = None, dither: bool = True):
    """Atmospheric perspective: blend opaque pixels toward fog colour (then optionally snap to
    palette with ordered dither for clean clusters)."""
    a = layer.alpha()
    c = layer.c[..., :3].astype(np.float32)
    f = np.asarray(fog, np.float32)[:3]
    out = c + (f - c) * amount
    if palette_cols is not None:
        out = quantize_rgb(out, palette_cols, dither=dither)
    layer.c[..., :3][a] = np.clip(out, 0, 255).astype(np.uint8)[a]


def quantize_rgb(rgb: np.ndarray, palette_cols: Sequence, dither: bool = True) -> np.ndarray:
    P = np.stack([np.asarray(c, np.float32)[:3] for c in palette_cols])
    h, w, _ = rgb.shape
    flat = rgb.reshape(-1, 3)
    d = ((flat[:, None, :] - P[None, :, :]) ** 2).sum(-1)
    order = np.argsort(d, axis=1)
    i1, i2 = order[:, 0], order[:, 1]
    if not dither:
        return P[i1].reshape(h, w, 3)
    d1 = np.sqrt(d[np.arange(len(flat)), i1]); d2 = np.sqrt(d[np.arange(len(flat)), i2])
    t = d1 / (d1 + d2 + 1e-6)  # 0 => exactly c1, 0.5 => halfway
    thr = bayer(w, h).reshape(-1) * 0.5
    pick = np.where(t > thr, i2, i1)
    return P[pick].reshape(h, w, 3)


def compose(layers: Iterable[tuple[Layer, int, int]], w: int, h: int, bg=(0, 0, 0, 255)) -> Image.Image:
    """Quick preview composite: [(layer, x, y), ...] back to front."""
    out = Layer(w, h)
    out.c[:] = np.asarray(bg, np.uint8)
    for L, x, y in layers:
        out.blit(L, x, y)
    return out.image()


def upscale(img: Image.Image, k: int = 3) -> Image.Image:
    return img.resize((img.width * k, img.height * k), Image.NEAREST)


def write_manifest(path: str, data: dict):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=1, ensure_ascii=False)
