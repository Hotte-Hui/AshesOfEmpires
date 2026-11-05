"""env_veltrava_hall_kit -- palette, tone-space painting, baked lighting and pixel fonts for L_C3_Hall.

Owned by the palais art stream (Chapter 3, 'Palais der Kommission', Veltrava).  Builds on
tools/pixelgen/pg.py without changing it and registers the scene palette 'palais' into
pg.PALETTES at import time (ramps of data/chapters/c3.json "palettes.palais", refined: the
daylight ramp gains one cold near-white for snow / bright overcast glass).

Painting model
--------------
Every pixel is painted as (ramp, tone): a *ramp* is a dark->light list of palette colours, the
*tone* a float index into it.  Baked light adds tone (value) and, where a light is strong, moves the
pixel onto the light's counterpart ramp at equal luminance (warm lamps -> cream/amber, daylight ->
cold blue-grey).  Fractions resolve with ordered (Bayer) dither inside a narrow band, so most pixels
form flat clusters.  Output is always palette-pure (stable under the post-process palette snap).
"""
from __future__ import annotations

import json
import math
import os
import sys

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import pg  # noqa: E402

DATE = '2026-11-04'
ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))

# --------------------------------------------------------------------------- palettes
# 'palais' = data/chapters/c3.json palettes.palais + one cold near-white (#D3DEE6) on 'daylight'.
PALAIS = {
    'night':    ['#05080C', '#0A1016', '#10181F', '#172229'],
    'wall':     ['#1B2826', '#26362F', '#344539', '#4A5B4C', '#647260'],
    'wood':     ['#22150F', '#331F16', '#4A2D1F', '#63402C', '#7E553B'],
    'marble':   ['#4E4A44', '#6A655C', '#878075', '#A59D8F', '#C4BCAD', '#E0D9CB'],
    'brass':    ['#4A3415', '#73531F', '#9C7630', '#C49A48', '#E8C779'],
    'daylight': ['#263445', '#3A4D63', '#55708A', '#7C98B0', '#A9C0D0', '#D3DEE6'],
    'amber':    ['#6E3F22', '#9A5A2F', '#C88A4E', '#E9B46E', '#FCE0A6'],
    'paper':    ['#6E6A5C', '#8E8A78', '#B0AA93', '#CEC6AA', '#E6DEC2', '#F5EFDA'],
    'ink':      ['#1A1C2A', '#2E3248', '#7A2A26', '#A8382E'],
}
pg.PALETTES['palais'] = PALAIS        # registered at import time (see module doc)

# exterior seen through the glass: the Veltrava town palette of data/chapters/c3.json (local copy,
# NOT registered here -- the station stream owns the 'veltrava' registration)
VELT = {
    'night':  ['#070A12', '#0C111C', '#121A26', '#1A2431'],
    'slate':  ['#1E2836', '#2A3646', '#3A4859', '#4F5E70', '#687789', '#8593A3'],
    'iron':   ['#15171C', '#22262D', '#323840', '#464D55', '#5E666E'],
    'cream':  ['#4A4236', '#645A49', '#80745E', '#9E9076', '#BBAD8F', '#D6CBAE'],
    'patina': ['#1E302E', '#2B4541', '#3D5E57', '#56796E', '#739585'],
    'lamp':   ['#6E3F22', '#A8643A', '#D08F55', '#EDB777', '#FCE2B0'],
    'sky':    ['#5C6B82', '#7684A0', '#95A0B8', '#B6B9C9', '#D3CDD3', '#E8DCD6'],
    'snow':   ['#7D8796', '#A1AAB7', '#C2C9D2', '#DEE2E7', '#F2F3F5'],
    'red':    ['#4A1712', '#7A2218', '#A8382E', '#C8503C'],
}


def palais_hex() -> set:
    return {h.upper() for r in PALAIS.values() for h in r}


def velt_hex() -> set:
    return {h.upper() for r in VELT.values() for h in r}


def check_c3_palettes() -> list[str]:
    """Compare the local ramps with data/chapters/c3.json (owned by integration) -> notes."""
    notes = []
    p = os.path.join(ROOT, 'data', 'chapters', 'c3.json')
    try:
        with open(p, encoding='utf-8') as f:
            pal = json.load(f).get('palettes', {})
    except (OSError, ValueError):
        return ['c3.json not readable']
    for name, local in (('palais', PALAIS), ('veltrava', VELT)):
        ref = pal.get(name, {})
        for ramp, cols in local.items():
            rc = [c.upper() for c in ref.get(ramp, [])]
            if [c.upper() for c in cols] != rc:
                notes.append('%s.%s differs from c3.json: local %s vs c3 %s' % (name, ramp, cols, rc))
    return notes


def lum(c) -> float:
    c = np.asarray(c, np.float32)[:3] / 255.0
    return float(0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2])


# --------------------------------------------------------------------------- ramps
class Ramps:
    """Named dark->light super-ramps + luminance tables (for hue switching at equal luminance)."""

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

    def color(self, name: str, i: float) -> np.ndarray:
        return self.table[self.idx[name], int(np.clip(round(i), 0, self.lens[self.idx[name]] - 1))]

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


def palais_ramps() -> Ramps:
    n, w, d, m, b = PALAIS['night'], PALAIS['wall'], PALAIS['wood'], PALAIS['marble'], PALAIS['brass']
    c, a, p, i = PALAIS['daylight'], PALAIS['amber'], PALAIS['paper'], PALAIS['ink']
    return Ramps({
        'N': [n[0], n[1], n[2], n[3]],                                          # poche / night (0..3)
        'W': [n[0], n[1], n[2], n[3], w[0], w[1], w[2], w[3], w[4], m[2], m[3]],  # sage stucco (0..10)
        'D': [n[0], d[0], d[1], d[2], d[3], d[4], a[1], a[2], a[3]],            # walnut (0..8)
        'M': [n[1], n[3], m[0], m[1], m[2], m[3], m[4], m[5]],                  # marble / cream stucco (0..7)
        'B': [d[1], b[0], b[1], b[2], b[3], b[4], a[4]],                        # brass / gilt (0..6)
        'C': [n[1], c[0], c[1], c[2], c[3], c[4], c[5]],                        # cold daylight (0..6)
        'A': [d[2], a[0], a[1], a[2], a[3], a[4]],                              # amber lamp light (0..5)
        'P': [w[2], w[3], p[0], p[1], p[2], p[3], p[4], p[5]],                  # paper (0..7)
        'I': [n[0], i[0], i[1], w[1]],                                          # ink / black (0..3)
        'R': [n[0], d[1], i[2], i[3], a[2]],                                    # wine red (0..4)
        'G': [n[0], n[1], w[0], w[1], w[2], w[3], w[4]],                        # green marble / palm (0..6)
        'S': [n[2], c[1], c[2], c[3], c[4], c[5], p[5]],                        # steel / glass glints (0..6)
    })


def velt_ramps() -> Ramps:
    V = VELT
    sk, sn, sl, cr, pa, ir, la, ni, rd = (V['sky'], V['snow'], V['slate'], V['cream'], V['patina'], V['iron'],
                                          V['lamp'], V['night'], V['red'])
    return Ramps({
        'SKY': [sl[4], sk[0], sk[1], sk[2], sk[3], sk[4], sk[5]],              # overcast morning (0..6)
        'HAZE': [sl[2], sl[3], sl[4], sl[5], sk[1], sk[2], sk[3]],             # distance haze (0..6)
        'STONE': [ni[3], sl[1], sl[2], cr[1], cr[2], cr[3], cr[4], cr[5]],     # stucco facades (0..7)
        'ROOF': [ni[1], ni[2], ni[3], sl[0], sl[1], sl[2], sl[3]],             # slate roofs (0..6)
        'PAT': [ni[2], pa[0], pa[1], pa[2], pa[3], pa[4]],                     # copper patina (0..5)
        'SNOW': [sl[3], sn[0], sn[1], sn[2], sn[3], sn[4]],                    # snow (0..5)
        'ICE': [sl[2], sl[3], sl[4], sn[0], sn[1], sn[2], sn[3]],              # river ice (0..6)
        'IRON': [ni[0], ir[0], ir[1], ir[2], ir[3], ir[4]],                    # iron, towers (0..5)
        'LAMP': [la[0], la[1], la[2], la[3], la[4]],                           # lit windows (0..4)
        'RED': [ni[1], rd[0], rd[1], rd[2], rd[3]],                            # tram, flags (0..4)
        'NIGHT': [ni[0], ni[1], ni[2], ni[3]],
    })


# hue counterparts for baked lights (src ramp -> ramp it moves onto when the light is strong)
WARM_OF = {'W': 'M', 'M': 'A', 'C': 'M', 'P': 'A', 'G': 'D', 'N': 'D', 'I': 'D', 'S': 'B', 'B': 'A', 'D': 'D',
           'R': 'R'}
COLD_OF = {'D': 'W', 'A': 'P', 'M': 'C', 'P': 'C', 'W': 'C', 'N': 'C', 'G': 'C', 'B': 'M', 'S': 'S', 'I': 'C',
           'R': 'R'}
# tone steps added per unit of light field, per source ramp: (warm, cold, white)
GAINS = {
    'W': (2.4, 2.6, 2.4), 'D': (2.6, 1.6, 2.0), 'M': (2.4, 2.4, 2.4), 'B': (2.4, 1.6, 2.0),
    'C': (1.6, 2.2, 2.0), 'A': (1.8, 0.8, 1.6), 'P': (2.2, 2.2, 2.4), 'I': (0.6, 0.6, 0.6),
    'R': (1.2, 0.8, 1.0), 'G': (2.0, 2.2, 2.0), 'S': (2.0, 2.4, 2.2), 'N': (1.4, 1.6, 1.4),
}


# --------------------------------------------------------------------------- tone layer
class TLayer(pg.Layer):
    """pg.Layer painted in (ramp, tone) space; resolve() writes palette-pure RGBA into .c / .em."""

    def __init__(self, w: int, h: int, R: Ramps, name: str = 'layer', warm_of=None, cold_of=None, gains=None):
        super().__init__(w, h, name)
        self.R = R
        self.rid = np.full((self.h, self.w), -1, np.int16)
        self.tone = np.zeros((self.h, self.w), np.float32)
        self.flat = np.zeros((self.h, self.w), bool)
        self.emis = np.zeros((self.h, self.w), bool)
        self.unlit = np.zeros((self.h, self.w), bool)
        self.lgain = np.ones((self.h, self.w), np.float32)
        self.amb = np.zeros((self.h, self.w), np.float32)
        self.crisp = np.zeros((self.h, self.w), bool)     # resolve by rounding (signage, tiny details)
        self.warm_of = warm_of or WARM_OF
        self.cold_of = cold_of or COLD_OF
        self.gains = gains or GAINS

    # ---------------------------------------------------------------- core write
    def _win(self, x0, y0, mh, mw):
        X0, Y0 = max(0, x0), max(0, y0)
        X1, Y1 = min(self.w, x0 + mw), min(self.h, y0 + mh)
        return X0, Y0, X1, Y1

    def put(self, mask, x0, y0, ramp, tone, hgt=None, flat=None, emis=None, unlit=None, gain=None, crisp=None):
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
        if crisp is not None:
            self.crisp[sl][m] = crisp

    def rect(self, x, y, w, h, ramp, tone, **kw):
        x, y, w, h = int(x), int(y), int(w), int(h)
        if w <= 0 or h <= 0:
            return
        if 'flat' not in kw:
            kw['flat'] = True
        self.put(np.ones((h, w), bool), x, y, ramp, tone, **kw)

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
        if 'flat' not in kw:
            kw['flat'] = True
        self.put(m, x0, y0, ramp, tone, **kw)
        return m, x0, y0

    def ellipse(self, cx, cy, rx, ry, ramp, tone, **kw):
        m, x0, y0 = self.ellipse_mask(cx, cy, rx, ry)
        if 'flat' not in kw:
            kw['flat'] = True
        self.put(m, x0, y0, ramp, tone, **kw)
        return m, x0, y0

    def vgrad(self, x, y, w, h, ramp, t0, t1, **kw):
        if w <= 0 or h <= 0:
            return
        t = np.linspace(t0, t1, int(h), dtype=np.float32)[:, None].repeat(int(w), 1)
        kw.setdefault('flat', False)
        self.put(np.ones((int(h), int(w)), bool), x, y, ramp, t, **kw)

    def hgrad(self, x, y, w, h, ramp, t0, t1, **kw):
        if w <= 0 or h <= 0:
            return
        t = np.linspace(t0, t1, int(w), dtype=np.float32)[None, :].repeat(int(h), 0)
        kw.setdefault('flat', False)
        self.put(np.ones((int(h), int(w)), bool), x, y, ramp, t, **kw)

    def text(self, s, x, y, ramp, tone, font='35', spacing=1, **kw):
        m = text_mask(s, font, spacing)
        kw.setdefault('flat', True)
        kw.setdefault('crisp', True)
        self.put(m, x, y, ramp, tone, **kw)
        return m.shape[1]

    def erase(self, x, y, w, h):
        X0, Y0, X1, Y1 = self._win(int(x), int(y), int(h), int(w))
        if X1 > X0 and Y1 > Y0:
            self.rid[Y0:Y1, X0:X1] = -1
            self.emis[Y0:Y1, X0:X1] = False

    def erase_mask(self, mask, x0, y0):
        mh, mw = mask.shape
        X0, Y0, X1, Y1 = self._win(x0, y0, mh, mw)
        if X1 <= X0 or Y1 <= Y0:
            return
        m = mask[Y0 - y0:Y1 - y0, X0 - x0:X1 - x0]
        self.rid[Y0:Y1, X0:X1][m] = -1
        self.emis[Y0:Y1, X0:X1][m] = False

    # ---------------------------------------------------------------- tone edits
    def shade_rect(self, x, y, w, h, dt, only=None):
        X0, Y0, X1, Y1 = self._win(int(x), int(y), int(h), int(w))
        if X1 <= X0 or Y1 <= Y0:
            return
        m = self.rid[Y0:Y1, X0:X1] >= 0
        if only is not None:
            m &= np.isin(self.rid[Y0:Y1, X0:X1], [self.R[o] for o in only])
        self.tone[Y0:Y1, X0:X1][m] += dt

    def shade_mask(self, mask, x0, y0, dt):
        mh, mw = mask.shape
        X0, Y0, X1, Y1 = self._win(int(x0), int(y0), mh, mw)
        if X1 <= X0 or Y1 <= Y0:
            return
        m = mask[Y0 - y0:Y1 - y0, X0 - x0:X1 - x0] & (self.rid[Y0:Y1, X0:X1] >= 0)
        self.tone[Y0:Y1, X0:X1][m] += dt

    def amb_field(self, field, x0=0, y0=0):
        fh, fw = field.shape
        X0, Y0, X1, Y1 = self._win(int(x0), int(y0), fh, fw)
        if X1 <= X0 or Y1 <= Y0:
            return
        self.amb[Y0:Y1, X0:X1] += field[Y0 - y0:Y1 - y0, X0 - x0:X1 - x0]

    def valid(self) -> np.ndarray:
        return self.rid >= 0

    def ramp_mask(self, *names) -> np.ndarray:
        return np.isin(self.rid, [self.R[n] for n in names])

    def tblit(self, o: 'TLayer', x: int, y: int, hoff: float = 0.0):
        X0, Y0 = max(0, x), max(0, y)
        X1, Y1 = min(self.w, x + o.w), min(self.h, y + o.h)
        if X1 <= X0 or Y1 <= Y0:
            return
        s = (slice(Y0 - y, Y1 - y), slice(X0 - x, X1 - x))
        d = (slice(Y0, Y1), slice(X0, X1))
        m = o.rid[s] >= 0
        for a in ('rid', 'tone', 'flat', 'emis', 'unlit', 'lgain', 'amb', 'crisp'):
            getattr(self, a)[d][m] = getattr(o, a)[s][m]
        self.hgt[d][m] = o.hgt[s][m] + hoff
        self.nrm[d][m] = o.nrm[s][m]

    # ---------------------------------------------------------------- resolve
    def normals(self, strength: float = 3.0) -> np.ndarray:
        img = self.normal_map(strength)[..., :3].astype(np.float32)
        return img / 127.5 - 1.0

    def resolve(self, fields: dict | None = None, seed: int = 0, band: float = 2.2, hue_sharp: float = 2.4,
                hue_gain: dict | None = None):
        """Bake light fields {'warm','cold','white'} (h,w arrays >= 0) and write .c / .em."""
        R = self.R
        valid = self.rid >= 0
        rid = self.rid.astype(np.int32).copy()
        rid[~valid] = 0
        t = np.where(self.flat, np.round(self.tone), self.tone).astype(np.float32) + self.amb
        thr_h = pg.bayer(self.w, self.h, 2 + seed, 1 + seed, 4)
        thr_q = pg.bayer(self.w, self.h, seed, seed, 4)
        if fields:
            hue_gain = hue_gain or {}
            lit = valid & ~self.unlit & ~self.emis
            g = self.lgain
            Wf = np.broadcast_to(fields.get('warm', 0) * g, t.shape)
            Cf = np.broadcast_to(fields.get('cold', 0) * g, t.shape)
            Xf = np.broadcast_to(fields.get('white', 0) * g, t.shape)
            new_rid = rid.copy()
            done = ~lit
            for kind, field, table in (('warm', Wf, self.warm_of), ('cold', Cf, self.cold_of)):
                k = hue_gain.get(kind, 1.0)
                if k <= 0:
                    continue
                v = np.clip((field * k - 0.5) * hue_sharp + 0.5, 0, 1)
                sel = (~done) & (v > thr_h)
                for src, dst in table.items():
                    if src not in R.idx or dst not in R.idx or src == dst:
                        continue
                    m = sel & (rid == R[src])
                    if m.any():
                        t[m] = R.map_tone(R[src], R[dst], t[m])
                        new_rid[m] = R[dst]
                done |= sel
            gw = np.zeros(len(R.names), np.float32); gc = gw.copy(); gx = gw.copy()
            for name, (a, b, c) in self.gains.items():
                if name in R.idx:
                    gw[R[name]], gc[R[name]], gx[R[name]] = a, b, c
            boost = gw[rid] * Wf + gc[rid] * Cf + gx[rid] * Xf
            t = np.where(lit, t + boost, t)
            rid = new_rid
        fl = np.floor(t)
        fr = t - fl
        if band and band > 1:
            fr = np.clip((fr - 0.5) * band + 0.5, 0, 1)
        idx = fl + (fr > thr_q)
        idx = np.where(self.crisp, np.round(t), idx)
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


def stroke_mask(w: int, h: int, polys, radius: float, jitter: float = 0.0, seed: int = 0,
                step: float = 0.35) -> np.ndarray:
    """Rasterise polylines with a round brush into a bool mask (h, w)."""
    rng = np.random.default_rng(seed)
    m = np.zeros((h, w), bool)
    r2 = radius * radius
    for pts in polys:
        for (ax, ay), (bx, by) in zip(pts[:-1], pts[1:]):
            L = math.hypot(bx - ax, by - ay)
            n = max(1, int(L / step))
            for k in range(n + 1):
                t = k / n
                x = ax + (bx - ax) * t + (rng.normal(0, jitter) if jitter else 0)
                y = ay + (by - ay) * t + (rng.normal(0, jitter) if jitter else 0)
                x0, x1 = int(math.floor(x - radius)), int(math.ceil(x + radius))
                y0, y1 = int(math.floor(y - radius)), int(math.ceil(y + radius))
                for yy in range(max(0, y0), min(h, y1 + 1)):
                    for xx in range(max(0, x0), min(w, x1 + 1)):
                        if (xx + 0.5 - x) ** 2 + (yy + 0.5 - y) ** 2 <= r2:
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


def box_blur(a, r):
    if r <= 0:
        return a
    k = 2 * r + 1
    p = np.pad(a, r, mode='edge')
    c = np.cumsum(np.cumsum(p, 0), 1)
    c = np.pad(c, ((1, 0), (1, 0)))
    out = (c[k:, k:] - c[:-k, k:] - c[k:, :-k] + c[:-k, :-k]) / (k * k)
    return out.astype(np.float32)


def arch_mask(w: int, h: int, rise: int) -> np.ndarray:
    """Window opening w x h whose top `rise` rows form a round (segmental) arch."""
    m = np.ones((h, w), bool)
    if rise <= 0:
        return m
    cx = (w - 1) / 2.0
    r = w / 2.0
    for y in range(rise):
        dy = rise - y - 0.5
        # ellipse with half-width r and half-height rise
        half = r * math.sqrt(max(0.0, 1 - (dy / rise) ** 2))
        x0, x1 = cx - half + 0.5, cx + half - 0.5
        for x in range(w):
            if not (x0 - 0.01 <= x <= x1 + 0.01):
                m[y, x] = False
    return m


# --------------------------------------------------------------------------- lights
def light_fields(layer: TLayer, lights: list, origin=(0, 0), strength: float = 3.0) -> dict:
    """Baked light fields for a layer placed at world `origin`.
    light: dict(pos=(x,y) world, kind='warm'|'cold'|'white', energy, radius, height, falloff=1.6,
                cone=None|(dx, dy, cos_min), wrap_add=0, box=None|(x0,y0,x1,y1) world clip)"""
    h, w = layer.h, layer.w
    N = layer.normals(strength)
    ys, xs = np.mgrid[0:h, 0:w].astype(np.float32)
    xw = xs + origin[0] + 0.5
    yw = ys + origin[1] + 0.5
    F = {k: np.zeros((h, w), np.float32) for k in ('warm', 'cold', 'white')}
    for L in lights:
        lx, ly = L['pos']
        r = float(L['radius'])
        # cheap reject
        if lx + r < origin[0] or lx - r > origin[0] + w or ly + r < origin[1] or ly - r > origin[1] + h:
            continue
        dx = lx - xw
        dyu = -(ly - yw)
        dz = float(L.get('height', 24))
        d2 = np.sqrt(dx * dx + dyu * dyu)
        d3 = np.sqrt(dx * dx + dyu * dyu + dz * dz) + 1e-6
        ndl = (N[..., 0] * dx + N[..., 1] * dyu + N[..., 2] * dz) / d3
        ndl = np.clip(ndl * float(L.get('wrap', 1.0)) + float(L.get('wrap_add', 0.0)), 0, 1)
        att = np.clip(1 - d2 / r, 0, 1) ** float(L.get('falloff', 1.6))
        if L.get('cone') is not None:
            cx, cy, cmin = L['cone']
            cl = math.hypot(cx, cy) + 1e-6
            v = ((xw - lx) * cx + (yw - ly) * cy) / ((d2 + 1e-6) * cl)
            att = att * np.clip((v - cmin) / max(1e-3, 1 - cmin), 0, 1) ** 0.7
        if L.get('box') is not None:
            bx0, by0, bx1, by1 = L['box']
            att = att * ((xw >= bx0) & (xw < bx1) & (yw >= by0) & (yw < by1))
        F[L.get('kind', 'warm')] += float(L.get('energy', 1.0)) * ndl * att
    return F


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


# --------------------------------------------------------------------------- fonts (hand-defined)
# 3x5 caps, digits and the signage symbols (Latin with German/French accents, a Cyrillic subset).
F35 = {
    'A': ['.#.', '#.#', '###', '#.#', '#.#'], 'B': ['##.', '#.#', '##.', '#.#', '##.'],
    'C': ['.##', '#..', '#..', '#..', '.##'], 'D': ['##.', '#.#', '#.#', '#.#', '##.'],
    'E': ['###', '#..', '##.', '#..', '###'], 'F': ['###', '#..', '##.', '#..', '#..'],
    'G': ['.##', '#..', '#.#', '#.#', '.##'], 'H': ['#.#', '#.#', '###', '#.#', '#.#'],
    'I': ['###', '.#.', '.#.', '.#.', '###'], 'J': ['..#', '..#', '..#', '#.#', '.#.'],
    'K': ['#.#', '#.#', '##.', '#.#', '#.#'], 'L': ['#..', '#..', '#..', '#..', '###'],
    'M': ['#.#', '###', '###', '#.#', '#.#'], 'N': ['##.', '#.#', '#.#', '#.#', '#.#'],
    'O': ['.#.', '#.#', '#.#', '#.#', '.#.'], 'P': ['##.', '#.#', '##.', '#..', '#..'],
    'Q': ['.#.', '#.#', '#.#', '##.', '.##'], 'R': ['##.', '#.#', '##.', '#.#', '#.#'],
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
    ',': ['...', '...', '...', '.#.', '#..'], ' ': ['...', '...', '...', '...', '...'],
    "'": ['.#.', '.#.', '...', '...', '...'], '+': ['...', '.#.', '###', '.#.', '...'],
    '=': ['...', '###', '...', '###', '...'], '<': ['..#', '.#.', '#..', '.#.', '..#'],
    '>': ['#..', '.#.', '..#', '.#.', '#..'], '§': ['.##', '#..', '###', '..#', '##.'],
    'Ä': ['#.#', '.#.', '#.#', '###', '#.#'], 'Ö': ['#.#', '...', '###', '#.#', '###'],
    'Ü': ['#.#', '...', '#.#', '#.#', '###'], 'É': ['.#.', '###', '##.', '#..', '###'],
    'È': ['#..', '###', '##.', '#..', '###'], 'À': ['#..', '.#.', '#.#', '###', '#.#'],
    # Cyrillic subset (signage): Б Г Д Ж З И Л П Р(=P) У Ф Ц Ч Ш Ы Ь Э Ю Я Й
    'Б': ['###', '#..', '##.', '#.#', '##.'], 'Г': ['###', '#..', '#..', '#..', '#..'],
    'Д': ['.##.', '.#.#', '.#.#', '####', '#..#'], 'Ж': ['#.#', '#.#', '.#.', '#.#', '#.#'],
    'З': ['##.', '..#', '.#.', '..#', '##.'], 'И': ['#.#', '#.#', '###', '##.', '#.#'],
    'Й': ['#.#', '#.#', '###', '##.', '#.#'], 'Л': ['.##', '#.#', '#.#', '#.#', '#.#'],
    'П': ['###', '#.#', '#.#', '#.#', '#.#'], 'У': ['#.#', '#.#', '.##', '..#', '##.'],
    'Ф': ['.#.', '###', '#.#', '###', '.#.'], 'Ц': ['#.#', '#.#', '#.#', '###', '..#'],
    'Ч': ['#.#', '#.#', '###', '..#', '..#'], 'Ш': ['#.#', '#.#', '###', '###', '###'],
    'Ы': ['#.#', '#.#', '###', '#.#', '###'], 'Ь': ['#..', '#..', '##.', '#.#', '##.'],
    'Э': ['##.', '..#', '.##', '..#', '##.'], 'Ю': ['#.#', '###', '###', '###', '#.#'],
    'Я': ['.##', '#.#', '.##', '#.#', '#.#'], 'Ё': ['#.#', '###', '##.', '#..', '###'],
    '⇄': ['...', '###', '...', '###', '...'],
}
# Cyrillic letters that look like Latin ones
for _c, _l in (('А', 'A'), ('В', 'B'), ('Е', 'E'), ('К', 'K'), ('М', 'M'), ('Н', 'H'), ('О', 'O'), ('Р', 'P'),
               ('С', 'C'), ('Т', 'T'), ('Х', 'X')):
    F35[_c] = F35[_l]

# 5x7 caps for headings / plaques
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
    'K': ['#...#', '#..#.', '#.#..', '##...', '#.#..', '#..#.', '#...#'],
    'L': ['#....', '#....', '#....', '#....', '#....', '#....', '#####'],
    'M': ['#...#', '##.##', '#.#.#', '#.#.#', '#...#', '#...#', '#...#'],
    'N': ['#...#', '##..#', '#.#.#', '#..##', '#...#', '#...#', '#...#'],
    'O': ['.###.', '#...#', '#...#', '#...#', '#...#', '#...#', '.###.'],
    'P': ['####.', '#...#', '#...#', '####.', '#....', '#....', '#....'],
    'R': ['####.', '#...#', '#...#', '####.', '#.#..', '#..#.', '#...#'],
    'S': ['.####', '#....', '#....', '.###.', '....#', '....#', '####.'],
    'T': ['#####', '..#..', '..#..', '..#..', '..#..', '..#..', '..#..'],
    'U': ['#...#', '#...#', '#...#', '#...#', '#...#', '#...#', '.###.'],
    'V': ['#...#', '#...#', '#...#', '#...#', '#...#', '.#.#.', '..#..'],
    'W': ['#...#', '#...#', '#...#', '#.#.#', '#.#.#', '#.#.#', '.#.#.'],
    'Z': ['#####', '....#', '...#.', '..#..', '.#...', '#....', '#####'],
    '1': ['..#..', '.##..', '..#..', '..#..', '..#..', '..#..', '.###.'],
    '2': ['.###.', '#...#', '....#', '...#.', '..#..', '.#...', '#####'],
    '3': ['#####', '...#.', '..#..', '...#.', '....#', '#...#', '.###.'],
    '5': ['#####', '#....', '####.', '....#', '....#', '#...#', '.###.'],
    '9': ['.###.', '#...#', '#...#', '.####', '....#', '...#.', '.##..'],
    ' ': ['.....'] * 7, '.': ['.....', '.....', '.....', '.....', '.....', '.##..', '.##..'],
    '-': ['.....', '.....', '.....', '#####', '.....', '.....', '.....'],
    'Ö': ['#...#', '.###.', '#...#', '#...#', '#...#', '#...#', '.###.'],
    'Ü': ['#...#', '.....', '#...#', '#...#', '#...#', '#...#', '.###.'],
}


# wider Cyrillic glyphs (variable width): the 3-px cell cannot hold their diagonals / triple stems
F35.update({
    'И': ['#..#', '#..#', '#.##', '##.#', '#..#'], 'Й': ['#..#', '#..#', '#.##', '##.#', '#..#'],
    'Ж': ['#.#.#', '#.#.#', '.###.', '#.#.#', '#.#.#'], 'Ш': ['#.#.#', '#.#.#', '#.#.#', '#.#.#', '#####'],
    'Ю': ['#..#.', '#.#.#', '###.#', '#.#.#', '#..#.'], 'Ы': ['#...#', '#...#', '##..#', '#.#.#', '##..#'],
    'М': ['#...#', '##.##', '#.#.#', '#...#', '#...#'],
})


def _glyph(f, ch):
    return f.get(ch, f.get(ch.upper(), f[' ']))


def text_mask(s: str, font: str = '35', spacing: int = 1) -> np.ndarray:
    f = F35 if font == '35' else F57
    gh = 5 if font == '35' else 7
    s = s.upper()
    if not s:
        return np.zeros((gh, 0), bool)
    widths = [max(len(r) for r in _glyph(f, ch)) for ch in s]
    w = sum(widths) + spacing * (len(s) - 1)
    m = np.zeros((gh, w), bool)
    x = 0
    for ch, gw in zip(s, widths):
        for yy, row in enumerate(_glyph(f, ch)):
            for xx, c in enumerate(row):
                if c == '#':
                    m[yy, x + xx] = True
        x += gw + spacing
    return m


def text_width(s: str, font: str = '35', spacing: int = 1) -> int:
    return int(text_mask(s, font, spacing).shape[1])


# --------------------------------------------------------------------------- emblems
def commission_arms(w: int, h: int) -> tuple[np.ndarray, np.ndarray]:
    """Fictional arms of the Free City / commission: a white bridge with three arches over a wavy
    line (on slate blue).  Returns (bridge, water) bool masks of shape (h, w)."""
    bridge = np.zeros((h, w), bool)
    water = np.zeros((h, w), bool)
    deck = int(round(h * 0.30))
    bridge[deck:deck + max(1, h // 9) + 1, :] = True                 # deck + parapet
    base = int(round(h * 0.70))
    for k in range(3):                                               # three arches
        x0 = int(round(w * (0.04 + k * 0.32)))
        x1 = int(round(w * (0.04 + k * 0.32 + 0.28)))
        cx = (x0 + x1) / 2.0
        r = (x1 - x0) / 2.0
        for x in range(max(0, x0 - 1), min(w, x1 + 2)):
            dx = (x + 0.5 - cx) / max(0.5, r)
            top = deck + 1 + int(round((base - deck - 2) * (1 - math.sqrt(max(0.0, 1 - dx * dx)))))
            if abs(dx) > 1:
                top = deck + 1
            bridge[deck:min(base, top + 1), x] = True
        # piers between arches
    for k in range(4):
        px_ = int(round(w * (0.02 + k * 0.32)))
        bridge[deck:base, max(0, px_):min(w, px_ + max(1, w // 14))] = True
    ww = int(round(h * 0.84))
    for x in range(w):
        y = ww + int(round(math.sin(x / max(1.0, w / 6.0) * math.pi) * max(1, h * 0.05)))
        if 0 <= y < h:
            water[y, x] = True
    return bridge, water


def reichssiegel_mask(d: int) -> tuple[np.ndarray, np.ndarray]:
    """Fictional German state emblem (ART_DIRECTION 4): white pillar/obelisk in a black disc.
    Returns (disc, pillar) bool masks (d, d).  NOT a swastika, eagle or rune."""
    yy, xx = np.mgrid[0:d, 0:d]
    c = (d - 1) / 2.0
    disc = (xx - c) ** 2 + (yy - c) ** 2 <= (d / 2.0 - 0.15) ** 2
    pillar = np.zeros((d, d), bool)
    top, bot = int(round(d * 0.16)), int(round(d * 0.80))
    for y in range(top, bot + 1):
        f = (y - top) / max(1, bot - top)
        half = 0.5 + f / 0.14 * max(0.0, d * 0.07 - 0.5) if f < 0.14 else d * (0.07 + 0.045 * (f - 0.14))
        pillar[y, int(round(c - half)):int(round(c + half)) + 1] = True
    pb = min(d - 2, bot + 1)
    ph = max(1, int(round(d * 0.06)))
    hw = d * 0.17
    pillar[pb:pb + ph, int(round(c - hw)):int(round(c + hw)) + 1] = True
    return disc, pillar & disc


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
