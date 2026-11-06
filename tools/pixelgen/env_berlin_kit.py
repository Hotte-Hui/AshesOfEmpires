"""env_berlin_kit -- tone-space painting, baked palette lighting and tiny fonts for env_berlin.

Owned by the env_berlin area (Berliner Bauarchiv, M1).  Builds on tools/pixelgen/pg.py without
changing it.

Core idea
---------
Everything is painted as (ramp, tone) per pixel instead of raw RGB:
* a *ramp* is a dark->light list of palette colours (hue-shifted super-ramps built from the
  'archive' / 'berlin' / 'sepia' palettes of pg.PALETTES),
* the *tone* is a float index into that ramp.
Lighting is baked by adding tone (value) and -- where a light is strong enough -- by switching
the pixel to the warm / cold counterpart ramp at the same luminance (hue shift).  Fractional
tones are resolved with ordered (Bayer) dithering, integer tones stay flat clusters.  The result
is always palette-pure, which keeps the post-process palette snap stable.
"""
from __future__ import annotations

import math
import os
import sys

import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pg  # noqa: E402

DATE = '2026-11-04'

# --------------------------------------------------------------------------- palettes
A = pg.PALETTES['archive']
B = pg.PALETTES['berlin']
S = pg.PALETTES['sepia']
K = pg.PALETTES['karsk']

# Additional ramps local to this area (do NOT write them into pg.PALETTES).
# Banker's-lamp glass green (muted, teal leaning so it sits in the navy room) and pencil graphite.
GREEN = ['#0F1F1C', '#183129', '#22473A', '#30614C', '#4A8266', '#7FB08D', '#BFE0B4']
GRAPHITE = ['#3A3D44', '#55585F', '#6F7178', '#8B8C90']

ARCHIVE_EXTRA = {'green': GREEN, 'graphite': GRAPHITE}


def archive_palette_hex() -> list[str]:
    out = []
    for r in A.values():
        out += r
    for r in ARCHIVE_EXTRA.values():
        out += r
    return out


def berlin_palette_hex() -> list[str]:
    out = []
    for r in B.values():
        out += r
    return out


def lum(c) -> float:
    c = np.asarray(c, np.float32)[:3] / 255.0
    return float(0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2])


# --------------------------------------------------------------------------- ramps
class Ramps:
    """Named dark->light colour ramps + luminance tables for hue-shift remapping."""

    def __init__(self, ramps: dict):
        self.names = list(ramps)
        self.idx = {n: i for i, n in enumerate(self.names)}
        self.hex = {n: list(ramps[n]) for n in self.names}
        cols = [np.stack([pg.hx(h) for h in ramps[n]]) for n in self.names]
        self.lens = np.array([len(c) for c in cols], np.int32)
        self.maxlen = int(self.lens.max())
        self.table = np.zeros((len(cols), self.maxlen, 4), np.uint8)
        for i, c in enumerate(cols):
            self.table[i, :len(c)] = c
            self.table[i, len(c):] = c[-1]
        self.lums = [np.array([lum(x) for x in c], np.float32) for c in cols]

    def __getitem__(self, name: str) -> int:
        return self.idx[name]

    def n(self, name: str) -> int:
        return int(self.lens[self.idx[name]])

    def color(self, name: str, i: int) -> np.ndarray:
        return self.table[self.idx[name], int(np.clip(i, 0, self.lens[self.idx[name]] - 1))]

    def map_tone(self, src: int, dst: int, t: np.ndarray) -> np.ndarray:
        ls, ld = self.lums[src], self.lums[dst]
        L = np.interp(t, np.arange(len(ls)), ls)
        order = np.argsort(ld)
        return np.interp(L, ld[order], np.arange(len(ld), dtype=np.float32)[order]).astype(np.float32)

    def all_hex(self) -> set:
        s = set()
        for n in self.names:
            s |= {h.upper() for h in self.hex[n]}
        return s


def archive_ramps() -> Ramps:
    """Super-ramps for the archive interior (all colours from 'archive' + local extras)."""
    n, w, d, a, p, b, i = A['night'], A['wall'], A['wood'], A['amber'], A['paper'], A['blue'], A['ink']
    g, gr = GREEN, GRAPHITE
    return Ramps({
        'W': [n[0], n[1], n[2], n[3], w[0], w[1], w[2], w[3], w[4], b[4], b[5]],      # cold room (0..10)
        'D': [n[0], d[0], d[1], d[2], d[3], d[4], d[5], a[2], a[3], a[4], a[5]],      # warm wood (0..10)
        'P': [w[2], w[3], p[0], p[1], p[2], p[3], p[4], p[5]],                        # paper (0..7)
        'B': [n[1], b[0], b[1], b[2], b[3], b[4], b[5]],                              # blue (0..6)
        'A': [d[2], a[0], a[1], a[2], a[3], a[4], a[5]],                              # amber light (0..6)
        'G': [n[1]] + g,                                                              # green glass (0..7)
        'I': [n[0], i[0], i[1], w[1]],                                                # ink / black (0..3)
        'R': [i[0], i[2], i[3], a[2]],                                                # red ink (0..3)
        'K': [n[0], gr[0], gr[1], gr[2], gr[3], w[4], b[5]],                          # graphite/steel
        'N': [n[0], n[1], n[2], n[3]],                                                # pure night (poche)
    })


# counterpart ramps for baked hue shifts
WARM_OF = {'W': 'D', 'P': 'A', 'K': 'D', 'B': 'W', 'N': 'D'}
COLD_OF = {'D': 'W', 'A': 'P', 'P': 'P', 'K': 'W', 'N': 'W', 'W': 'W'}
GREEN_OF = {'W': 'G', 'P': 'G', 'D': 'G', 'K': 'G', 'N': 'G', 'A': 'G'}

# tone steps added per unit of light field, per ramp: (warm, cold, green, white)
GAINS = {
    'W': (2.2, 2.6, 1.4, 2.6), 'D': (2.6, 1.6, 1.0, 2.2), 'P': (2.2, 2.2, 1.2, 2.6),
    'B': (1.4, 1.8, 0.8, 2.0), 'A': (1.8, 0.6, 0.5, 1.6), 'G': (0.8, 0.6, 2.2, 1.0),
    'I': (0.6, 0.6, 0.4, 0.6), 'R': (0.8, 0.5, 0.4, 0.8), 'K': (2.0, 2.2, 1.2, 2.4),
    'N': (1.2, 1.4, 0.8, 1.4),
}


# --------------------------------------------------------------------------- tone layer
class MLayer(pg.Layer):
    """pg.Layer painted in (ramp, tone) space; resolve() writes palette-pure RGBA into .c"""

    def __init__(self, w: int, h: int, R: Ramps, name: str = 'layer'):
        super().__init__(w, h, name)
        self.R = R
        self.rid = np.full((self.h, self.w), -1, np.int16)
        self.tone = np.zeros((self.h, self.w), np.float32)
        self.flat = np.zeros((self.h, self.w), bool)     # round instead of dither
        self.emis = np.zeros((self.h, self.w), bool)     # emission pixels (never darkened)
        self.unlit = np.zeros((self.h, self.w), bool)    # ignore baked lights
        self.lgain = np.ones((self.h, self.w), np.float32)
        self.amb = np.zeros((self.h, self.w), np.float32)  # ambient offset added after rounding

    # ---------------------------------------------------------------- core write
    def _win(self, x0, y0, mh, mw):
        X0, Y0 = max(0, x0), max(0, y0)
        X1, Y1 = min(self.w, x0 + mw), min(self.h, y0 + mh)
        return X0, Y0, X1, Y1

    def put(self, mask, x0, y0, ramp, tone, hgt=None, flat=None, emis=None, unlit=None, gain=None):
        mask = np.asarray(mask, bool)
        mh, mw = mask.shape
        x0, y0 = int(x0), int(y0)
        X0, Y0, X1, Y1 = self._win(x0, y0, mh, mw)
        if X1 <= X0 or Y1 <= Y0:
            return
        m = mask[Y0 - y0:Y1 - y0, X0 - x0:X1 - x0]
        sl = (slice(Y0, Y1), slice(X0, X1))

        def sub(v):
            v = np.asarray(v)
            return v[Y0 - y0:Y1 - y0, X0 - x0:X1 - x0][m]
        if ramp is not None:
            self.rid[sl][m] = self.R[ramp] if isinstance(ramp, str) else ramp
        if tone is not None:
            self.tone[sl][m] = tone if np.isscalar(tone) else sub(tone)
        if hgt is not None:
            self.hgt[sl][m] = hgt if np.isscalar(hgt) else sub(hgt)
        if flat is not None:
            self.flat[sl][m] = flat
        if emis is not None:
            self.emis[sl][m] = emis
        if unlit is not None:
            self.unlit[sl][m] = unlit
        if gain is not None:
            self.lgain[sl][m] = gain

    def rect(self, x, y, w, h, ramp, tone, **kw):  # noqa: D401  (tone-space rect)
        x, y, w, h = int(x), int(y), int(w), int(h)
        if w <= 0 or h <= 0:
            return
        self.put(np.ones((h, w), bool), x, y, ramp, tone, **kw)

    def erase(self, x, y, w, h):
        X0, Y0, X1, Y1 = self._win(int(x), int(y), int(h), int(w))
        if X1 > X0 and Y1 > Y0:
            self.rid[Y0:Y1, X0:X1] = -1
            self.emis[Y0:Y1, X0:X1] = False

    def erase_mask(self, mask, x0, y0):
        mh, mw = mask.shape
        X0, Y0, X1, Y1 = self._win(x0, y0, mh, mw)
        m = mask[Y0 - y0:Y1 - y0, X0 - x0:X1 - x0]
        self.rid[Y0:Y1, X0:X1][m] = -1

    def px(self, x, y, ramp, tone, **kw):
        self.rect(x, y, 1, 1, ramp, tone, **kw)

    def hline(self, x, y, w, ramp, tone, **kw):
        self.rect(x, y, w, 1, ramp, tone, **kw)

    def vline(self, x, y, h, ramp, tone, **kw):
        self.rect(x, y, 1, h, ramp, tone, **kw)

    def line(self, x0, y0, x1, y1, ramp, tone, **kw):
        for (x, y) in bres(x0, y0, x1, y1):
            self.px(x, y, ramp, tone, **kw)

    def polyline(self, pts, ramp, tone, **kw):
        for a, b in zip(pts[:-1], pts[1:]):
            self.line(a[0], a[1], b[0], b[1], ramp, tone, **kw)

    def poly(self, pts, ramp, tone, **kw):
        m, x0, y0 = self.poly_mask(pts)
        self.put(m, x0, y0, ramp, tone, **kw)
        return m, x0, y0

    def ellipse(self, cx, cy, rx, ry, ramp, tone, **kw):
        m, x0, y0 = self.ellipse_mask(cx, cy, rx, ry)
        self.put(m, x0, y0, ramp, tone, **kw)
        return m, x0, y0

    def vgrad(self, x, y, w, h, ramp, t0, t1, **kw):
        if w <= 0 or h <= 0:
            return
        t = np.linspace(t0, t1, h, dtype=np.float32)[:, None].repeat(w, 1)
        self.put(np.ones((h, w), bool), x, y, ramp, t, **kw)

    def hgrad(self, x, y, w, h, ramp, t0, t1, **kw):
        if w <= 0 or h <= 0:
            return
        t = np.linspace(t0, t1, w, dtype=np.float32)[None, :].repeat(h, 0)
        self.put(np.ones((h, w), bool), x, y, ramp, t, **kw)

    # ---------------------------------------------------------------- tone edits
    def shade_rect(self, x, y, w, h, dt, only=None):
        X0, Y0, X1, Y1 = self._win(int(x), int(y), int(h), int(w))
        if X1 <= X0 or Y1 <= Y0:
            return
        m = self.rid[Y0:Y1, X0:X1] >= 0
        if only is not None:
            m &= self.rid[Y0:Y1, X0:X1] == self.R[only]
        self.tone[Y0:Y1, X0:X1][m] += dt

    def shade_field(self, field, x0=0, y0=0, only=None):
        fh, fw = field.shape
        X0, Y0, X1, Y1 = self._win(int(x0), int(y0), fh, fw)
        if X1 <= X0 or Y1 <= Y0:
            return
        f = field[Y0 - y0:Y1 - y0, X0 - x0:X1 - x0]
        m = self.rid[Y0:Y1, X0:X1] >= 0
        if only is not None:
            m &= np.isin(self.rid[Y0:Y1, X0:X1], [self.R[o] for o in only])
        self.tone[Y0:Y1, X0:X1][m] += f[m]

    def amb_field(self, field, x0=0, y0=0):
        """Add a smooth ambient/occlusion offset (applied after the flat rounding -> dithers)."""
        fh, fw = field.shape
        X0, Y0, X1, Y1 = self._win(int(x0), int(y0), fh, fw)
        if X1 <= X0 or Y1 <= Y0:
            return
        self.amb[Y0:Y1, X0:X1] += field[Y0 - y0:Y1 - y0, X0 - x0:X1 - x0]

    def valid(self) -> np.ndarray:
        return self.rid >= 0

    # ---------------------------------------------------------------- blit (tone space)
    def tblit(self, o: 'MLayer', x: int, y: int, hoff: float = 0.0):
        X0, Y0 = max(0, x), max(0, y)
        X1, Y1 = min(self.w, x + o.w), min(self.h, y + o.h)
        if X1 <= X0 or Y1 <= Y0:
            return
        s = (slice(Y0 - y, Y1 - y), slice(X0 - x, X1 - x))
        d = (slice(Y0, Y1), slice(X0, X1))
        m = o.rid[s] >= 0
        for a in ('rid', 'tone', 'flat', 'emis', 'unlit', 'lgain', 'amb'):
            getattr(self, a)[d][m] = getattr(o, a)[s][m]
        self.hgt[d][m] = o.hgt[s][m] + hoff
        self.nrm[d][m] = o.nrm[s][m]

    # ---------------------------------------------------------------- resolve
    def normals(self, strength: float = 3.0) -> np.ndarray:
        img = self.normal_map(strength)[..., :3].astype(np.float32)
        return img / 127.5 - 1.0

    def resolve(self, fields: dict | None = None, hue: dict | None = None, seed: int = 0,
                dither_size: int = 4, band: float = 2.0, hue_sharp: float = 2.2):
        """Bake light fields (warm/cold/green/white, each (h,w) >= 0) and write .c / .em.
        band > 1 compresses every fractional tone step so most pixels form flat clusters and only
        a narrow band around the step is ordered-dithered (hand-dithered look instead of noise).
        hue_sharp > 1 narrows the dithered zone where a light switches the hue ramp."""
        R = self.R
        valid = self.rid >= 0
        rid = self.rid.astype(np.int32).copy()
        rid[~valid] = 0
        # 'flat' pixels keep a crisp albedo (rounded base tone); light still dithers on top
        t = np.where(self.flat, np.round(self.tone), self.tone).astype(np.float32) + self.amb
        thr_h = pg.bayer(self.w, self.h, 2 + seed, 1 + seed, 4)
        thr_q = pg.bayer(self.w, self.h, seed, seed, dither_size)
        if fields:
            hue = hue or {'warm': 1.0, 'cold': 1.0, 'green': 1.0}
            lit = valid & ~self.unlit & ~self.emis
            g = self.lgain
            Wf = fields.get('warm', 0) * g
            Cf = fields.get('cold', 0) * g
            Gf = fields.get('green', 0) * g
            Xf = fields.get('white', 0) * g
            Wf = np.broadcast_to(Wf, t.shape); Cf = np.broadcast_to(Cf, t.shape)
            Gf = np.broadcast_to(Gf, t.shape); Xf = np.broadcast_to(Xf, t.shape)
            # hue switches (dithered thresholds)
            new_rid = rid.copy()
            done = ~lit
            for kind, field, table in (('green', Gf, GREEN_OF), ('warm', Wf, WARM_OF), ('cold', Cf, COLD_OF)):
                k = hue.get(kind, 1.0)
                if k <= 0:
                    continue
                v = np.clip((field * k - 0.5) * hue_sharp + 0.5, 0, 1)
                sel = (~done) & (v > thr_h)
                for src, dst in table.items():
                    if src not in R.idx or dst not in R.idx:
                        continue
                    m = sel & (rid == R[src])
                    if m.any():
                        t[m] = R.map_tone(R[src], R[dst], t[m])
                        new_rid[m] = R[dst]
                done |= sel
            # value boost in the *original* ramp's gain
            gw = np.zeros(len(R.names), np.float32); gc = gw.copy(); gg = gw.copy(); gx = gw.copy()
            for name, (a, b, c, d) in GAINS.items():
                if name in R.idx:
                    gw[R[name]], gc[R[name]], gg[R[name]], gx[R[name]] = a, b, c, d
            boost = gw[rid] * Wf + gc[rid] * Cf + gg[rid] * Gf + gx[rid] * Xf
            t = np.where(lit, t + boost, t)
            rid = new_rid
        fl = np.floor(t)
        fr = t - fl
        if band and band > 1:
            fr = np.clip((fr - 0.5) * band + 0.5, 0, 1)
        idx = fl + (fr > thr_q)
        idx = np.clip(idx, 0, R.lens[rid] - 1).astype(np.int32)
        col = R.table[rid, idx].copy()
        col[~valid] = 0
        self.c = col
        em = np.zeros_like(col)
        em[self.emis & valid] = col[self.emis & valid]
        self.em = em
        return self


# --------------------------------------------------------------------------- geometry
def bres(x0, y0, x1, y1):
    x0, y0, x1, y1 = int(round(x0)), int(round(y0)), int(round(x1)), int(round(y1))
    dx, dy = abs(x1 - x0), -abs(y1 - y0)
    sx, sy = (1 if x0 < x1 else -1), (1 if y0 < y1 else -1)
    err = dx + dy
    out = []
    while True:
        out.append((x0, y0))
        if x0 == x1 and y0 == y1:
            break
        e2 = 2 * err
        if e2 >= dy:
            err += dy; x0 += sx
        if e2 <= dx:
            err += dx; y0 += sy
    return out


def disc_mask(r: float):
    n = int(math.ceil(r)) * 2 + 1
    c = n // 2
    yy, xx = np.mgrid[0:n, 0:n]
    return ((xx - c) ** 2 + (yy - c) ** 2) <= r * r + 0.3, c


def stroke_mask(w: int, h: int, polys, radius: float, jitter: float = 0.0, seed: int = 0,
                step: float = 0.35) -> np.ndarray:
    """Rasterise polylines with a round brush of `radius` into a bool mask (w,h)."""
    rng = np.random.default_rng(seed)
    m = np.zeros((h, w), bool)
    for pts in polys:
        for (ax, ay), (bx, by) in zip(pts[:-1], pts[1:]):
            L = math.hypot(bx - ax, by - ay)
            n = max(1, int(L / step))
            for k in range(n + 1):
                t = k / n
                x = ax + (bx - ax) * t + (rng.normal(0, jitter) if jitter else 0)
                y = ay + (by - ay) * t + (rng.normal(0, jitter) if jitter else 0)
                r = radius
                x0, x1 = int(math.floor(x - r)), int(math.ceil(x + r))
                y0, y1 = int(math.floor(y - r)), int(math.ceil(y + r))
                for yy in range(max(0, y0), min(h, y1 + 1)):
                    for xx in range(max(0, x0), min(w, x1 + 1)):
                        if (xx + 0.5 - x) ** 2 + (yy + 0.5 - y) ** 2 <= r * r:
                            m[yy, xx] = True
    return m


def dilate(m: np.ndarray, r: int = 1, diag: bool = True) -> np.ndarray:
    out = m.copy()
    for _ in range(r):
        p = np.pad(out, 1)
        nb = p[:-2, 1:-1] | p[2:, 1:-1] | p[1:-1, :-2] | p[1:-1, 2:]
        if diag:
            nb |= p[:-2, :-2] | p[:-2, 2:] | p[2:, :-2] | p[2:, 2:]
        out = out | nb
    return out


def erode(m: np.ndarray, r: int = 1) -> np.ndarray:
    return ~dilate(~m, r, diag=False)


def edge_of(m: np.ndarray) -> np.ndarray:
    return m & ~erode(m, 1)


# --------------------------------------------------------------------------- lights
def light_fields(layer: MLayer, lights: list, origin=(0, 0), strength: float = 3.0,
                 shape=None) -> dict:
    """Accumulate baked light fields for a layer placed at world `origin`.
    light: dict(pos=(x,y) world px, kind='warm'|'cold'|'green'|'white', energy, radius, height,
                falloff=1.6, cone=None|(dir_x, dir_y, cos_min))"""
    h, w = layer.h, layer.w
    N = layer.normals(strength)
    ys, xs = np.mgrid[0:h, 0:w].astype(np.float32)
    xw = xs + origin[0] + 0.5
    yw = ys + origin[1] + 0.5
    F = {k: np.zeros((h, w), np.float32) for k in ('warm', 'cold', 'green', 'white')}
    for L in lights:
        lx, ly = L['pos']
        dx = lx - xw
        dyu = -(ly - yw)            # +up
        dz = float(L.get('height', 24))
        d2 = np.sqrt(dx * dx + dyu * dyu)
        d3 = np.sqrt(dx * dx + dyu * dyu + dz * dz) + 1e-6
        ndl = (N[..., 0] * dx + N[..., 1] * dyu + N[..., 2] * dz) / d3
        ndl = np.clip(ndl * float(L.get('wrap', 1.0)) + float(L.get('wrap_add', 0.0)), 0, 1)
        att = np.clip(1 - d2 / float(L['radius']), 0, 1) ** float(L.get('falloff', 1.6))
        if L.get('cone') is not None:
            cx, cy, cmin = L['cone']
            cl = math.hypot(cx, cy) + 1e-6
            # cosine between the light->pixel vector (xw-lx, yw-ly) and the cone axis
            v = ((xw - lx) * cx + (yw - ly) * cy) / ((d2 + 1e-6) * cl)
            att = att * np.clip((v - cmin) / max(1e-3, 1 - cmin), 0, 1) ** 0.7
        F[L.get('kind', 'warm')] += float(L.get('energy', 1.0)) * ndl * att
    return F


def add_fields(a: dict, b: dict, x0: int = 0, y0: int = 0):
    """Add field dict b (smaller, at offset) into a (in place)."""
    for k, v in b.items():
        if k not in a:
            continue
        h, w = v.shape
        H, W = a[k].shape
        X0, Y0 = max(0, x0), max(0, y0)
        X1, Y1 = min(W, x0 + w), min(H, y0 + h)
        if X1 > X0 and Y1 > Y0:
            a[k][Y0:Y1, X0:X1] += v[Y0 - y0:Y1 - y0, X0 - x0:X1 - x0]


def sub_fields(F: dict, x0: int, y0: int, w: int, h: int) -> dict:
    out = {}
    for k, v in F.items():
        H, W = v.shape
        o = np.zeros((h, w), np.float32)
        X0, Y0 = max(0, x0), max(0, y0)
        X1, Y1 = min(W, x0 + w), min(H, y0 + h)
        if X1 > X0 and Y1 > Y0:
            o[Y0 - y0:Y1 - y0, X0 - x0:X1 - x0] = v[Y0:Y1, X0:X1]
        out[k] = o
    return out


# --------------------------------------------------------------------------- fonts
# 3x5 caps (plus a few symbols).  '#' = ink.
F35 = {
    'A': ['.#.', '#.#', '###', '#.#', '#.#'], 'B': ['##.', '#.#', '##.', '#.#', '##.'],
    'C': ['.##', '#..', '#..', '#..', '.##'], 'D': ['##.', '#.#', '#.#', '#.#', '##.'],
    'E': ['###', '#..', '##.', '#..', '###'], 'F': ['###', '#..', '##.', '#..', '#..'],
    'G': ['.##', '#..', '#.#', '#.#', '.##'], 'H': ['#.#', '#.#', '###', '#.#', '#.#'],
    'I': ['###', '.#.', '.#.', '.#.', '###'], 'J': ['..#', '..#', '..#', '#.#', '.#.'],
    'K': ['#.#', '#.#', '##.', '#.#', '#.#'], 'L': ['#..', '#..', '#..', '#..', '###'],
    'M': ['#.#', '###', '###', '#.#', '#.#'], 'N': ['##.', '#.#', '#.#', '#.#', '#.#'],
    'O': ['.#.', '#.#', '#.#', '#.#', '.#.'], 'P': ['##.', '#.#', '##.', '#..', '#..'],
    'Q': ['.#.', '#.#', '#.#', '##.', '.##'], 'R': ['##.', '#.#', '##.', '##.', '#.#'],
    'S': ['.##', '#..', '.#.', '..#', '##.'], 'T': ['###', '.#.', '.#.', '.#.', '.#.'],
    'U': ['#.#', '#.#', '#.#', '#.#', '###'], 'V': ['#.#', '#.#', '#.#', '#.#', '.#.'],
    'W': ['#.#', '#.#', '###', '###', '#.#'], 'X': ['#.#', '#.#', '.#.', '#.#', '#.#'],
    'Y': ['#.#', '#.#', '.#.', '.#.', '.#.'], 'Z': ['###', '..#', '.#.', '#..', '###'],
    '0': ['###', '#.#', '#.#', '#.#', '###'], '1': ['.#.', '##.', '.#.', '.#.', '###'],
    '2': ['##.', '..#', '.#.', '#..', '###'], '3': ['##.', '..#', '.#.', '..#', '##.'],
    '4': ['#.#', '#.#', '###', '..#', '..#'], '5': ['###', '#..', '##.', '..#', '##.'],
    '6': ['.##', '#..', '###', '#.#', '###'], '7': ['###', '..#', '.#.', '.#.', '.#.'],
    '8': ['###', '#.#', '###', '#.#', '###'], '9': ['###', '#.#', '###', '..#', '##.'],
    '-': ['...', '...', '###', '...', '...'], '.': ['...', '...', '...', '...', '.#.'],
    ':': ['...', '.#.', '...', '.#.', '...'], '/': ['..#', '..#', '.#.', '#..', '#..'],
    ',': ['...', '...', '...', '.#.', '#..'], '(': ['.#.', '#..', '#..', '#..', '.#.'],
    ')': ['.#.', '..#', '..#', '..#', '.#.'], ' ': ['...', '...', '...', '...', '...'],
    "'": ['.#.', '.#.', '...', '...', '...'], '+': ['...', '.#.', '###', '.#.', '...'],
    '=': ['...', '###', '...', '###', '...'], '#': ['#.#', '###', '#.#', '###', '#.#'],
    'Ä': ['#.#', '.#.', '#.#', '###', '#.#'], 'Ö': ['#.#', '...', '###', '#.#', '###'],
    'Ü': ['#.#', '...', '#.#', '#.#', '###'], 'ß': ['##.', '#.#', '##.', '#.#', '##.'],
    '№': ['#.#', '###', '###', '#.#', '#.#'],
}

# 5x7 caps for headings
F57 = {
    'A': ['.###.', '#...#', '#...#', '#####', '#...#', '#...#', '#...#'],
    'B': ['####.', '#...#', '#...#', '####.', '#...#', '#...#', '####.'],
    'C': ['.###.', '#...#', '#....', '#....', '#....', '#...#', '.###.'],
    'D': ['####.', '#...#', '#...#', '#...#', '#...#', '#...#', '####.'],
    'E': ['#####', '#....', '#....', '####.', '#....', '#....', '#####'],
    'F': ['#####', '#....', '#....', '####.', '#....', '#....', '#....'],
    'G': ['.###.', '#...#', '#....', '#.###', '#...#', '#...#', '.####'],
    'H': ['#...#', '#...#', '#...#', '#####', '#...#', '#...#', '#...#'],
    'I': ['.###.', '..#..', '..#..', '..#..', '..#..', '..#..', '.###.'],
    'J': ['..###', '...#.', '...#.', '...#.', '...#.', '#..#.', '.##..'],
    'K': ['#...#', '#..#.', '#.#..', '##...', '#.#..', '#..#.', '#...#'],
    'L': ['#....', '#....', '#....', '#....', '#....', '#....', '#####'],
    'M': ['#...#', '##.##', '#.#.#', '#.#.#', '#...#', '#...#', '#...#'],
    'N': ['#...#', '##..#', '#.#.#', '#..##', '#...#', '#...#', '#...#'],
    'O': ['.###.', '#...#', '#...#', '#...#', '#...#', '#...#', '.###.'],
    'P': ['####.', '#...#', '#...#', '####.', '#....', '#....', '#....'],
    'Q': ['.###.', '#...#', '#...#', '#...#', '#.#.#', '#..#.', '.##.#'],
    'R': ['####.', '#...#', '#...#', '####.', '#.#..', '#..#.', '#...#'],
    'S': ['.####', '#....', '#....', '.###.', '....#', '....#', '####.'],
    'T': ['#####', '..#..', '..#..', '..#..', '..#..', '..#..', '..#..'],
    'U': ['#...#', '#...#', '#...#', '#...#', '#...#', '#...#', '.###.'],
    'V': ['#...#', '#...#', '#...#', '#...#', '#...#', '.#.#.', '..#..'],
    'W': ['#...#', '#...#', '#...#', '#.#.#', '#.#.#', '#.#.#', '.#.#.'],
    'X': ['#...#', '#...#', '.#.#.', '..#..', '.#.#.', '#...#', '#...#'],
    'Y': ['#...#', '#...#', '.#.#.', '..#..', '..#..', '..#..', '..#..'],
    'Z': ['#####', '....#', '...#.', '..#..', '.#...', '#....', '#####'],
    '0': ['.###.', '#...#', '#..##', '#.#.#', '##..#', '#...#', '.###.'],
    '1': ['..#..', '.##..', '..#..', '..#..', '..#..', '..#..', '.###.'],
    '2': ['.###.', '#...#', '....#', '...#.', '..#..', '.#...', '#####'],
    '3': ['#####', '...#.', '..#..', '...#.', '....#', '#...#', '.###.'],
    '4': ['...#.', '..##.', '.#.#.', '#..#.', '#####', '...#.', '...#.'],
    '5': ['#####', '#....', '####.', '....#', '....#', '#...#', '.###.'],
    '6': ['..##.', '.#...', '#....', '####.', '#...#', '#...#', '.###.'],
    '7': ['#####', '....#', '...#.', '..#..', '.#...', '.#...', '.#...'],
    '8': ['.###.', '#...#', '#...#', '.###.', '#...#', '#...#', '.###.'],
    '9': ['.###.', '#...#', '#...#', '.####', '....#', '...#.', '.##..'],
    '-': ['.....', '.....', '.....', '#####', '.....', '.....', '.....'],
    '.': ['.....', '.....', '.....', '.....', '.....', '.##..', '.##..'],
    ' ': ['.....'] * 7, '/': ['....#', '....#', '...#.', '..#..', '.#...', '#....', '#....'],
    ':': ['.....', '.##..', '.##..', '.....', '.##..', '.##..', '.....'],
    'Ä': ['#...#', '.###.', '#...#', '#####', '#...#', '#...#', '#...#'],
    'Ö': ['#...#', '.###.', '#...#', '#...#', '#...#', '#...#', '.###.'],
    'Ü': ['#...#', '.....', '#...#', '#...#', '#...#', '#...#', '.###.'],
}


def text_mask(s: str, font: str = '35', spacing: int = 1, overhang: bool = False) -> np.ndarray:
    """overhang=True (round 9, tools/pixelgen/pixfont_umlauts.py): the distinct umlauts -- dots one row above the
    cap line; the mask then has that row more at the TOP, the caller draws it one row higher."""
    if overhang:
        f = F35_UML if font == '35' else F57_UML
    else:
        f = F35 if font == '35' else F57
    gw = 3 if font == '35' else 5
    gh = 5 if font == '35' else 7
    s = s.upper()
    if not s:
        return np.zeros((gh, 0), bool)
    extra = _UML.overhang(f, s, gh)
    w = len(s) * (gw + spacing) - spacing
    m = np.zeros((gh + extra, w), bool)
    for i, ch in enumerate(s):
        g = f.get(ch, f.get(' '))
        top = extra - (len(g) - gh)
        for yy, row in enumerate(g):
            for xx, c in enumerate(row):
                if c == '#':
                    m[top + yy, i * (gw + spacing) + xx] = True
    return m


import pixfont_umlauts as _UML  # noqa: E402
F35_UML = _UML.install(dict(F35), 5)
F57_UML = _UML.install(dict(F57), 7)


def text_width(s: str, font: str = '35', spacing: int = 1) -> int:
    gw = 3 if font == '35' else 5
    return len(s) * (gw + spacing) - spacing if s else 0


# --------------------------------------------------------------------------- handwriting
# Unit-box skeletons (x 0..1, y 0..1 top->bottom) for a few handwritten glyphs.
HAND = {
    'C': [[(0.92, 0.18), (0.70, 0.02), (0.38, 0.02), (0.12, 0.22), (0.04, 0.52), (0.14, 0.82),
           (0.42, 0.98), (0.72, 0.96), (0.94, 0.80)]],
    '-': [[(0.08, 0.54), (0.92, 0.50)]],
    '1': [[(0.10, 0.30), (0.62, 0.02), (0.56, 0.98)]],
    '7': [[(0.06, 0.06), (0.94, 0.04), (0.62, 0.48), (0.40, 0.98)], [(0.30, 0.52), (0.86, 0.50)]],
    '3': [[(0.10, 0.12), (0.50, 0.0), (0.86, 0.16), (0.50, 0.46), (0.90, 0.68), (0.56, 0.98), (0.08, 0.86)]],
    '4': [[(0.70, 0.98), (0.66, 0.0), (0.06, 0.66), (0.96, 0.66)]],
    '/': [[(0.9, 0.0), (0.1, 1.0)]],
    '2': [[(0.1, 0.2), (0.5, 0.0), (0.9, 0.2), (0.1, 0.98), (0.95, 0.98)]],
    '0': [[(0.5, 0.0), (0.12, 0.3), (0.12, 0.7), (0.5, 1.0), (0.88, 0.7), (0.88, 0.3), (0.5, 0.0)]],
    '6': [[(0.8, 0.05), (0.3, 0.3), (0.12, 0.72), (0.45, 1.0), (0.85, 0.75), (0.5, 0.5), (0.15, 0.68)]],
    '9': [[(0.86, 0.32), (0.5, 0.0), (0.14, 0.28), (0.5, 0.55), (0.86, 0.32), (0.7, 1.0)]],
    '8': [[(0.5, 0.48), (0.15, 0.22), (0.5, 0.0), (0.85, 0.22), (0.5, 0.48), (0.12, 0.75), (0.5, 1.0),
           (0.88, 0.75), (0.5, 0.48)]],
    '5': [[(0.85, 0.02), (0.2, 0.02), (0.14, 0.45), (0.6, 0.4), (0.9, 0.7), (0.55, 1.0), (0.1, 0.88)]],
    '.': [[(0.3, 0.92), (0.4, 1.0)]],
    'E': [[(0.85, 0.05), (0.15, 0.05), (0.1, 0.95), (0.85, 0.95)], [(0.12, 0.5), (0.7, 0.5)]],
    'H': [[(0.1, 0.0), (0.1, 1.0)], [(0.85, 0.0), (0.85, 1.0)], [(0.1, 0.5), (0.85, 0.5)]],
}


def hand_polys(text: str, x: float, y: float, h: float, w_per: float, gap: float, slant: float = 0.12,
               seed: int = 0, wobble: float = 0.0):
    """Polylines (in px) for handwritten `text` with its top-left at (x, y)."""
    rng = np.random.default_rng(seed)
    polys = []
    cx = x
    for ch in text:
        if ch == ' ':
            cx += w_per * 0.6
            continue
        sk = HAND.get(ch)
        if sk is None:
            cx += w_per + gap
            continue
        gw = w_per * (0.55 if ch in '-1' else (0.35 if ch == '.' else 1.0))
        for stroke in sk:
            pts = []
            for (u, v) in stroke:
                px_ = cx + u * gw + (1 - v) * h * slant + (rng.normal(0, wobble) if wobble else 0)
                py_ = y + v * h + (rng.normal(0, wobble) if wobble else 0)
                pts.append((px_, py_))
            polys.append(smooth_poly(pts, 6))
        cx += gw + gap
    return polys


def smooth_poly(pts, sub: int = 6):
    """Catmull-Rom smoothing of a polyline."""
    if len(pts) < 3:
        return list(pts)
    P = [pts[0]] + list(pts) + [pts[-1]]
    out = []
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = P[i - 1], P[i], P[i + 1], P[i + 2]
        for k in range(sub):
            t = k / sub
            t2, t3 = t * t, t * t * t
            x = 0.5 * ((2 * p1[0]) + (-p0[0] + p2[0]) * t + (2 * p0[0] - 5 * p1[0] + 4 * p2[0] - p3[0]) * t2 +
                       (-p0[0] + 3 * p1[0] - 3 * p2[0] + p3[0]) * t3)
            y = 0.5 * ((2 * p1[1]) + (-p0[1] + p2[1]) * t + (2 * p0[1] - 5 * p1[1] + 4 * p2[1] - p3[1]) * t2 +
                       (-p0[1] + 3 * p1[1] - 3 * p2[1] + p3[1]) * t3)
            out.append((x, y))
    out.append(pts[-1])
    return out


def scribble_polys(x: float, y: float, width: float, xh: float, seed: int = 0, words=None,
                   asc: float = 0.9, slant: float = 0.25):
    """Pseudo cursive handwriting: smoothed letter templates (n, u, e, l, o, a, t, g ...) joined
    into words on baseline y with x-height xh.  Returns a list of polylines (one per word)."""
    rng = np.random.default_rng(seed)
    T = {  # (dx, dy) in units of x-height; dy negative = up
        'n': [(0, 0), (0.15, -1), (0.55, -1.05), (0.75, -0.2), (0.85, -0.9), (1.25, -1), (1.45, 0)],
        'u': [(0, -1), (0.1, -0.15), (0.45, 0.02), (0.8, -1), (0.85, -0.1), (1.1, 0)],
        'e': [(0, -0.35), (0.7, -0.65), (0.55, -1.05), (0.1, -0.7), (0.25, -0.05), (0.85, -0.2)],
        'l': [(0, -0.3), (0.55, -1.9), (0.35, -2.25), (0.15, -1.6), (0.3, -0.05), (0.75, -0.3)],
        'o': [(0.45, -1), (0.05, -0.55), (0.3, 0), (0.75, -0.45), (0.45, -1), (0.95, -0.85)],
        'a': [(0.75, -0.9), (0.3, -1.0), (0.05, -0.4), (0.4, 0), (0.75, -0.8), (0.8, -0.05), (1.05, -0.2)],
        't': [(0, -0.3), (0.35, -1.7), (0.3, -0.05), (0.7, -0.25)],
        'g': [(0.7, -0.9), (0.25, -1.0), (0.1, -0.4), (0.6, -0.2), (0.75, -0.9), (0.6, 0.9), (0.15, 0.7),
              (0.85, 0.0)],
        'i': [(0, -0.2), (0.25, -1.0), (0.3, -0.05), (0.6, -0.25)],
        'r': [(0, 0), (0.2, -1.0), (0.45, -0.75), (0.8, -1.0), (0.85, -0.6)],
        'h': [(0, -0.3), (0.5, -2.0), (0.3, -2.2), (0.2, 0), (0.45, -0.9), (0.8, -1.0), (0.95, 0)],
    }
    freq = list('neeuaairtlhonnegeuirt')
    polys = []
    cx = x
    while cx < x + width - 3:
        n_letters = int(rng.integers(2, 7)) if words is None else int(words)
        pts = []
        u = cx
        for i in range(n_letters):
            ch = freq[int(rng.integers(0, len(freq)))]
            tpl = T[ch]
            sc = xh * rng.uniform(0.85, 1.15)
            wsc = xh * rng.uniform(0.9, 1.25)
            for (dx, dy) in tpl:
                px_ = u + dx * wsc + (-dy) * sc * slant
                py_ = y + dy * sc
                pts.append((px_, py_))
            u += (max(p[0] for p in tpl) + 0.25) * wsc
            if u > x + width:
                break
        if len(pts) >= 3:
            polys.append(smooth_poly(pts, 3))
        cx = u + rng.uniform(2.5, 4.5)
    return polys


# --------------------------------------------------------------------------- emblem
def reichssiegel_mask(d: int) -> tuple[np.ndarray, np.ndarray]:
    """Fictional state emblem: white pillar/obelisk in a black disc.  Returns (disc, pillar)
    boolean masks of size (d, d).  (NOT a swastika/eagle/rune -- see ART_DIRECTION §4.)"""
    yy, xx = np.mgrid[0:d, 0:d]
    c = (d - 1) / 2.0
    r = d / 2.0
    disc = (xx - c) ** 2 + (yy - c) ** 2 <= (r - 0.15) ** 2
    pillar = np.zeros((d, d), bool)
    top = int(round(d * 0.16))
    bot = int(round(d * 0.80))
    for y in range(top, bot + 1):
        f = (y - top) / max(1, bot - top)
        if f < 0.14:                                  # pyramidion tip
            half = 0.5 + f / 0.14 * max(0.0, d * 0.07 - 0.5)
        else:                                         # tapering shaft
            half = d * (0.07 + 0.045 * (f - 0.14))
        x0 = int(round(c - half)); x1 = int(round(c + half))
        pillar[y, x0:x1 + 1] = True
    # plinth
    pb = min(d - 2, bot + 1)
    ph = max(1, int(round(d * 0.06)))
    hw = d * 0.17
    pillar[pb:pb + ph, int(round(c - hw)):int(round(c + hw)) + 1] = True
    pillar &= disc
    return disc, pillar


# --------------------------------------------------------------------------- io helpers
def save_rgba(arr: np.ndarray, path: str):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    Image.fromarray(arr, 'RGBA').save(path)


def ensure_gdignore(folder: str):
    os.makedirs(folder, exist_ok=True)
    p = os.path.join(folder, '.gdignore')
    if not os.path.exists(p):
        open(p, 'w').close()


def palette_report(arr: np.ndarray, allowed_hex: set) -> tuple[int, list]:
    a = arr[..., 3] > 0
    cols = {('#%02X%02X%02X' % tuple(c[:3])) for c in arr[a].reshape(-1, 4)}
    bad = sorted(c for c in cols if c not in allowed_hex)
    return len(cols), bad


def quantize_tone(tone: np.ndarray, ramp_rgb: np.ndarray, dither=True, x0=0, y0=0, size=4):
    """Map float tone image (h,w) in ramp-index units onto ramp colours (n,3|4)."""
    h, w = tone.shape
    n = len(ramp_rgb)
    t = np.clip(tone, 0, n - 1)
    fl = np.floor(t)
    if dither:
        idx = fl + ((t - fl) > pg.bayer(w, h, x0, y0, size))
    else:
        idx = np.round(t)
    idx = np.clip(idx, 0, n - 1).astype(np.int32)
    return ramp_rgb[idx]
