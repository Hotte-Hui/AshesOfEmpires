"""explore_berlin -- close-ups for the Berlin archive exploration finds (owner: berlin-explore).

Writes assets/explore/berlin/<name>.png (240 x 150 px, pixel art 1:1, shown x3 by the discovery view,
TECHNICAL_ARCHITECTURE 12.1). Close-ups whose subject is regime iconography also get <name>_hist.png with the
real historical insignia (12.4: the neutral file always exists; loaders resolve via Symbols.pick):
  poster_aufbau      the 1964 'AUFBAU' poster: banners + top emblem (neutral: fictional Reichssiegel)
  master_plan        the round office stamp in the title block of the general plan
Everything is painted procedurally in "tone space" (ramp + tone in ramp steps) and quantised with ordered
(Bayer) dithering onto the scene palettes of tools/pixelgen/pg.py (archive, berlin, sepia) plus the two
archive extras of the Berlin room (green lamp glass, graphite).  Key light = the archive's: cold daylight from
the tall windows on the left, warm lamp accents.  Nothing is traced or sampled; all text is in-world fiction.
Deterministic: seeds are crc32 of the asset names (no wall clock, no hash()).

Run:  py -3 -P tools/pixelgen/explore_berlin.py [--preview DIR]
"""
from __future__ import annotations

import math
import os
import sys
import zlib

import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pg  # noqa: E402  (read-only shared helpers)

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
OUT = os.path.join(ROOT, 'assets', 'explore', 'berlin')
W, H = 240, 150

A = pg.PALETTES['archive']
B = pg.PALETTES['berlin']
SP = pg.PALETTES['sepia']
GREEN = ['#0F1F1C', '#183129', '#22473A', '#30614C', '#4A8266', '#7FB08D', '#BFE0B4']   # archive lamp glass
GRAPHITE = ['#3A3D44', '#55585F', '#6F7178', '#8B8C90']                               # archive pencil

# Ramps are dark -> light; shadows drift to navy/violet, highlights to amber (ART_DIRECTION 2).
RAMPS = {
    'room': A['night'] + A['wall'],
    'wood': ['#06151D'] + A['wood'] + ['#B57B59', '#D79A62'],
    'paper': ['#24373A', '#4A5A5B'] + A['paper'],
    'brass': ['#2A1B16', '#6E3F22', '#9A5A2F', '#B57B59', '#D79A62', '#F2C27E', '#FFE3AA'],
    'amber': A['amber'],
    'steel': ['#0B1C24'] + B['steel'],
    'blue': A['blue'],
    'ink': A['ink'][:2],
    'red': ['#2A1B16'] + SP['red'] + ['#D07744'],
    'green': GREEN,
    'graphite': GRAPHITE,
    'sepia': SP['tone'],
    'snow': B['snow'],
    'violet': B['night'] + B['violet'],
    'dusk': B['night'] + B['violet'][1:] + ['#735145', '#8D5542', '#AF6C47', '#D07744'] + B['glow'],
    'patina': B['patina'],
    'stone': B['stone'],
    'glow': B['glow'],
}
ALLOWED = {c.upper() for r in RAMPS.values() for c in r}


def seed_of(name: str) -> int:
    return zlib.crc32(name.encode('utf-8')) & 0x7FFFFFFF


# =========================================================================== masks
def poly_mask(pts):
    xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
    x0, x1 = int(math.floor(min(xs))), int(math.ceil(max(xs)))
    y0, y1 = int(math.floor(min(ys))), int(math.ceil(max(ys)))
    w, h = max(1, x1 - x0 + 1), max(1, y1 - y0 + 1)
    m = np.zeros((h, w), bool)
    n = len(pts)
    for row in range(h):
        yc = y0 + row + 0.5
        cr = []
        for i in range(n):
            ax, ay = pts[i]; bx, by = pts[(i + 1) % n]
            if (ay <= yc < by) or (by <= yc < ay):
                cr.append(ax + (yc - ay) * (bx - ax) / (by - ay))
        cr.sort()
        for k in range(0, len(cr) - 1, 2):
            a = int(math.ceil(cr[k] - 0.5)) - x0
            b = int(math.floor(cr[k + 1] - 0.5)) - x0
            if b >= a:
                m[row, max(0, a):min(w, b + 1)] = True
    return m, x0, y0


def ellipse_mask(cx, cy, rx, ry):
    x0, y0 = int(math.floor(cx - rx)) - 1, int(math.floor(cy - ry)) - 1
    w, h = int(math.ceil(2 * rx)) + 3, int(math.ceil(2 * ry)) + 3
    yy, xx = np.mgrid[0:h, 0:w]
    dx = (xx + x0 + 0.5 - cx) / max(rx, 0.5)
    dy = (yy + y0 + 0.5 - cy) / max(ry, 0.5)
    return (dx * dx + dy * dy) <= 1.0, x0, y0


def bres(x0, y0, x1, y1):
    x0, y0, x1, y1 = int(round(x0)), int(round(y0)), int(round(x1)), int(round(y1))
    pts = []
    dx, dy = abs(x1 - x0), -abs(y1 - y0)
    sx, sy = (1 if x0 < x1 else -1), (1 if y0 < y1 else -1)
    err = dx + dy
    while True:
        pts.append((x0, y0))
        if x0 == x1 and y0 == y1:
            break
        e2 = 2 * err
        if e2 >= dy:
            err += dy; x0 += sx
        if e2 <= dx:
            err += dx; y0 += sy
    return pts


def dilate(m, r=1):
    out = m.copy()
    for _ in range(r):
        p = np.pad(out, 1)
        out = p[1:-1, 1:-1] | p[:-2, 1:-1] | p[2:, 1:-1] | p[1:-1, :-2] | p[1:-1, 2:]
    return out


def edge(m):
    p = np.pad(m, 1)
    inner = p[:-2, 1:-1] & p[2:, 1:-1] & p[1:-1, :-2] & p[1:-1, 2:]
    return m & ~inner


def smooth(pts, sub=5):
    if len(pts) < 3:
        return list(pts)
    P = [pts[0]] + list(pts) + [pts[-1]]
    out = []
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = P[i - 1], P[i], P[i + 1], P[i + 2]
        for k in range(sub):
            t = k / sub; t2, t3 = t * t, t * t * t
            out.append(tuple(0.5 * ((2 * p1[j]) + (-p0[j] + p2[j]) * t + (2 * p0[j] - 5 * p1[j] + 4 * p2[j] - p3[j]) * t2
                                    + (-p0[j] + 3 * p1[j] - 3 * p2[j] + p3[j]) * t3) for j in (0, 1)))
    out.append(pts[-1])
    return out


# =========================================================================== fonts
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
    ',': ['...', '...', '...', '.#.', '#..'], ' ': ['...'] * 5, '?': ['##.', '..#', '.#.', '...', '.#.'],
    "'": ['.#.', '.#.', '...', '...', '...'], '+': ['...', '.#.', '###', '.#.', '...'],
    'Ä': ['#.#', '.#.', '#.#', '###', '#.#'], 'Ö': ['#.#', '.#.', '#.#', '#.#', '.#.'],
    'Ü': ['#.#', '...', '#.#', '#.#', '###'], '·': ['...', '...', '.#.', '...', '...'],
}
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
    'R': ['####.', '#...#', '#...#', '####.', '#.#..', '#..#.', '#...#'],
    'S': ['.####', '#....', '#....', '.###.', '....#', '....#', '####.'],
    'T': ['#####', '..#..', '..#..', '..#..', '..#..', '..#..', '..#..'],
    'U': ['#...#', '#...#', '#...#', '#...#', '#...#', '#...#', '.###.'],
    'V': ['#...#', '#...#', '#...#', '#...#', '#...#', '.#.#.', '..#..'],
    'W': ['#...#', '#...#', '#...#', '#.#.#', '#.#.#', '#.#.#', '.#.#.'],
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
    ' ': ['.....'] * 7, '?': ['.###.', '#...#', '....#', '...#.', '..#..', '.....', '..#..'],
    'Ä': ['#...#', '.###.', '#...#', '#####', '#...#', '#...#', '#...#'],
    'Ö': ['#...#', '.###.', '#...#', '#...#', '#...#', '#...#', '.###.'],
    'Ü': ['#...#', '.....', '#...#', '#...#', '#...#', '#...#', '.###.'],
}


# round 9 (feel pass 2, tools/pixelgen/pixfont_umlauts.py): distinct Ä / Ö / Ü -- the dots one row ABOVE the cap
# line, a blank row, the letter one row shorter.  Used by Canvas.text and every caller passing overhang=True.
import pixfont_umlauts as _UML  # noqa: E402
F35_UML = _UML.install(dict(F35), 5)
F57_UML = _UML.install(dict(F57), 7)


def text_mask(s: str, font: str = '35', spacing: int = 1, scale: int = 1, overhang: bool = False) -> np.ndarray:
    """Bool mask of the capitals.  overhang=True: the distinct umlauts -- the mask then has `extra` more rows at
    the TOP (text_overhang()), so the caller draws it that many rows (x scale) above the cap line."""
    if overhang:
        f = F35_UML if font == '35' else F57_UML
    else:
        f = F35 if font == '35' else F57
    gw, gh = (3, 5) if font == '35' else (5, 7)
    s = s.upper()
    if not s:
        return np.zeros((gh * scale, 0), bool)
    extra = _UML.overhang(f, s, gh)
    w = len(s) * (gw + spacing) - spacing
    m = np.zeros((gh + extra, w), bool)
    for i, ch in enumerate(s):
        g = f.get(ch, f[' '])
        top = extra - (len(g) - gh)
        for yy, row in enumerate(g):
            for xx, c in enumerate(row):
                if c == '#':
                    m[top + yy, i * (gw + spacing) + xx] = True
    if scale > 1:
        m = np.repeat(np.repeat(m, scale, 0), scale, 1)
    return m


def text_overhang(s: str, font: str = '35') -> int:
    """Rows (unscaled) the overhang mask of `s` reaches above the cap line."""
    return _UML.overhang(F35_UML if font == '35' else F57_UML, s, 5 if font == '35' else 7)


def text_w(s: str, font: str = '35', spacing: int = 1, scale: int = 1) -> int:
    gw = 3 if font == '35' else 5
    return (len(s) * (gw + spacing) - spacing) * scale if s else 0


# =========================================================================== canvas
class Canvas:
    """Tone-space painting: every pixel has a ramp and a tone (in ramp steps, float).  `flat` pixels (ink,
    text, hard accents) are never lit, dithered or vignetted."""

    def __init__(self, name: str, w: int = W, h: int = H):
        self.name, self.w, self.h = name, w, h
        self.seed = seed_of(name)
        self.rid = np.zeros((h, w), np.int16)
        self.t = np.zeros((h, w), np.float32)
        self.flat = np.zeros((h, w), bool)
        self.names: list[str] = []
        self.rgb: list[np.ndarray] = []

    def R(self, ramp: str) -> int:
        if ramp not in self.names:
            self.names.append(ramp)
            self.rgb.append(np.array([pg.hx(c)[:3] for c in RAMPS[ramp]], np.uint8))
        return self.names.index(ramp)

    def n(self, ramp: str) -> int:
        return len(RAMPS[ramp])

    # ---- placement
    def put(self, m, x0, y0, ramp, tone, flat=False):
        mh, mw = m.shape
        X0, Y0 = max(0, x0), max(0, y0)
        X1, Y1 = min(self.w, x0 + mw), min(self.h, y0 + mh)
        if X1 <= X0 or Y1 <= Y0:
            return
        mm = m[Y0 - y0:Y1 - y0, X0 - x0:X1 - x0]
        r = self.R(ramp)
        self.rid[Y0:Y1, X0:X1][mm] = r
        if np.isscalar(tone):
            self.t[Y0:Y1, X0:X1][mm] = float(tone)
        else:
            tt = np.asarray(tone, np.float32)
            if tt.shape == m.shape:
                tt = tt[Y0 - y0:Y1 - y0, X0 - x0:X1 - x0]
            else:   # full-canvas tone field
                tt = tt[Y0:Y1, X0:X1]
            self.t[Y0:Y1, X0:X1][mm] = tt[mm]
        self.flat[Y0:Y1, X0:X1][mm] = flat

    def full(self, m):
        """Canvas-sized bool mask from a placed mask (m, x0, y0)."""
        mm, x0, y0 = m
        out = np.zeros((self.h, self.w), bool)
        mh, mw = mm.shape
        X0, Y0 = max(0, x0), max(0, y0)
        X1, Y1 = min(self.w, x0 + mw), min(self.h, y0 + mh)
        if X1 > X0 and Y1 > Y0:
            out[Y0:Y1, X0:X1] = mm[Y0 - y0:Y1 - y0, X0 - x0:X1 - x0]
        return out

    def rect(self, x, y, w, h, ramp, tone, flat=False):
        if w <= 0 or h <= 0:
            return np.zeros((0, 0), bool), x, y
        m = np.ones((int(h), int(w)), bool)
        self.put(m, int(x), int(y), ramp, tone, flat)
        return m, int(x), int(y)

    def grad(self, x, y, w, h, ramp, t0, t1, axis='v', flat=False, ease=1.0):
        x, y, w, h = int(x), int(y), int(w), int(h)
        if w <= 0 or h <= 0:
            return
        if axis == 'v':
            f = (np.arange(h) / max(1, h - 1)) ** ease
            T = np.repeat((t0 + (t1 - t0) * f)[:, None], w, 1)
        else:
            f = (np.arange(w) / max(1, w - 1)) ** ease
            T = np.repeat((t0 + (t1 - t0) * f)[None, :], h, 0)
        self.put(np.ones((h, w), bool), x, y, ramp, T, flat)

    def ellipse(self, cx, cy, rx, ry, ramp, tone, flat=False):
        m, x0, y0 = ellipse_mask(cx, cy, rx, ry)
        self.put(m, x0, y0, ramp, tone, flat)
        return m, x0, y0

    def poly(self, pts, ramp, tone, flat=False):
        m, x0, y0 = poly_mask(pts)
        self.put(m, x0, y0, ramp, tone, flat)
        return m, x0, y0

    def px(self, x, y, ramp, tone, flat=True):
        x, y = int(x), int(y)
        if 0 <= x < self.w and 0 <= y < self.h:
            self.rid[y, x] = self.R(ramp); self.t[y, x] = tone; self.flat[y, x] = flat

    def line(self, x0, y0, x1, y1, ramp, tone, flat=True, dash=None):
        for i, (x, y) in enumerate(bres(x0, y0, x1, y1)):
            if dash and (i % (dash[0] + dash[1])) >= dash[0]:
                continue
            self.px(x, y, ramp, tone, flat)

    def polyline(self, pts, ramp, tone, flat=True, width=1):
        m = np.zeros((self.h, self.w), bool)
        for a, b in zip(pts[:-1], pts[1:]):
            for (x, y) in bres(a[0], a[1], b[0], b[1]):
                if 0 <= x < self.w and 0 <= y < self.h:
                    m[y, x] = True
        if width > 1:
            m = dilate(m, width - 1)
        self.put(m, 0, 0, ramp, tone, flat)
        return m

    def text(self, x, y, s, ramp, tone, font='35', spacing=1, scale=1, flat=True, align='left'):
        m = text_mask(s, font, spacing, scale, overhang=True)
        if align == 'center':
            x = x - m.shape[1] // 2
        elif align == 'right':
            x = x - m.shape[1]
        self.put(m, int(x), int(y) - text_overhang(s, font) * scale, ramp, tone, flat)   # umlaut dots above y
        return m.shape[1]

    # ---- tone adjustments (never on flat pixels)
    def adjust(self, field, mask=None):
        f = np.asarray(field, np.float32)
        sel = ~self.flat if mask is None else (~self.flat & mask)
        if f.ndim == 0:
            self.t[sel] += float(f)
        else:
            self.t[sel] += f[sel]

    def field_radial(self, cx, cy, r, amount, power=1.6):
        yy, xx = np.mgrid[0:self.h, 0:self.w]
        d = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2) / max(1.0, r)
        return np.clip(1 - d, 0, 1) ** power * amount

    def spot(self, cx, cy, r, amount, mask=None, power=1.6):
        self.adjust(self.field_radial(cx, cy, r, amount, power), mask)

    def linear(self, amount_left, amount_right, mask=None):
        f = np.repeat(np.linspace(amount_left, amount_right, self.w)[None, :], self.h, 0)
        self.adjust(f, mask)

    def vignette(self, amount=1.4, power=2.2):
        yy, xx = np.mgrid[0:self.h, 0:self.w]
        dx = (xx - (self.w - 1) / 2) / (self.w / 2)
        dy = (yy - (self.h - 1) / 2) / (self.h / 2)
        d = np.clip(np.sqrt(dx * dx * 0.8 + dy * dy * 0.9), 0, 1.6)
        self.adjust(-amount * d ** power)

    def noise(self, cell, amp, mask=None, seed_add=0, octaves=3):
        nz = pg.value_noise(self.w, self.h, cell, self.seed + seed_add, octaves=octaves)
        self.adjust((nz - 0.5) * 2 * amp, mask)

    def grain(self, amp, mask=None, seed_add=0):
        nz = pg.white_noise(self.w, self.h, self.seed + 97 + seed_add)
        self.adjust((nz - 0.5) * 2 * amp, mask)

    def shadow(self, m, dx, dy, amount, under=None):
        """Darken what lies under the shape m (canvas mask) shifted by (dx, dy)."""
        sh = np.zeros_like(m)
        H_, W_ = m.shape
        ys0, ys1 = max(0, dy), min(H_, H_ + dy)
        xs0, xs1 = max(0, dx), min(W_, W_ + dx)
        sh[ys0:ys1, xs0:xs1] = m[ys0 - dy:ys1 - dy, xs0 - dx:xs1 - dx]
        sh &= ~m
        if under is not None:
            sh &= under
        self.adjust(-amount, sh)

    def bevel(self, m, light=1.0, dark=1.0, flat=False):
        """1-px light top/left rim and dark bottom/right rim inside the canvas mask m."""
        p = np.pad(m, 1)
        top = m & ~p[:-2, 1:-1]
        left = m & ~p[1:-1, :-2]
        bot = m & ~p[2:, 1:-1]
        right = m & ~p[1:-1, 2:]
        if flat:
            self.t[(top | left)] += light
            self.t[(bot | right) & ~(top | left)] -= dark
        else:
            self.adjust(light, top | left)
            self.adjust(-dark, (bot | right) & ~(top | left))

    def outline(self, m, ramp, tone, flat=True):
        p = np.pad(m, 1)
        nb = p[:-2, 1:-1] | p[2:, 1:-1] | p[1:-1, :-2] | p[1:-1, 2:]
        o = nb & ~m
        self.put(o, 0, 0, ramp, tone, flat)
        return o

    # ---- output
    def render(self) -> np.ndarray:
        out = np.zeros((self.h, self.w, 4), np.uint8)
        out[..., 3] = 255
        thr = pg.bayer(self.w, self.h, 0, 0, 4)
        for i, rgb in enumerate(self.rgb):
            sel = self.rid == i
            if not sel.any():
                continue
            n = len(rgb)
            T = np.clip(self.t, 0, n - 1)
            fl = np.floor(T)
            idx = np.where(self.flat, np.round(T), fl + ((T - fl) > thr)).astype(np.int32)
            idx = np.clip(idx, 0, n - 1)
            out[sel, :3] = rgb[idx[sel]]
        return out


# =========================================================================== reusable pieces
def scribble(cv: Canvas, x, y, width, ramp, tone, seed, xh=2.0, slant=0.25, flat=True, gap=(2.5, 4.5)):
    """Pseudo cursive handwriting along baseline y (1-px pen)."""
    rng = np.random.default_rng(seed)
    T = {
        'n': [(0, 0), (0.15, -1), (0.55, -1.05), (0.75, -0.2), (0.85, -0.9), (1.25, -1), (1.45, 0)],
        'u': [(0, -1), (0.1, -0.15), (0.45, 0.02), (0.8, -1), (0.85, -0.1), (1.1, 0)],
        'e': [(0, -0.35), (0.7, -0.65), (0.55, -1.05), (0.1, -0.7), (0.25, -0.05), (0.85, -0.2)],
        'l': [(0, -0.3), (0.55, -1.9), (0.35, -2.25), (0.15, -1.6), (0.3, -0.05), (0.75, -0.3)],
        'o': [(0.45, -1), (0.05, -0.55), (0.3, 0), (0.75, -0.45), (0.45, -1), (0.95, -0.85)],
        'a': [(0.75, -0.9), (0.3, -1.0), (0.05, -0.4), (0.4, 0), (0.75, -0.8), (0.8, -0.05), (1.05, -0.2)],
        't': [(0, -0.3), (0.35, -1.7), (0.3, -0.05), (0.7, -0.25)],
        'i': [(0, -0.2), (0.25, -1.0), (0.3, -0.05), (0.6, -0.25)],
        'r': [(0, 0), (0.2, -1.0), (0.45, -0.75), (0.8, -1.0), (0.85, -0.6)],
    }
    freq = list('neeuaairtlonneur')
    cx = x
    while cx < x + width - 4:
        pts = []
        u = cx
        for _ in range(int(rng.integers(2, 6))):
            tpl = T[freq[int(rng.integers(0, len(freq)))]]
            sc = xh * rng.uniform(0.85, 1.15)
            wsc = xh * rng.uniform(0.9, 1.2)
            for (dx, dy) in tpl:
                pts.append((u + dx * wsc + (-dy) * sc * slant, y + dy * sc))
            u += (max(p[0] for p in tpl) + 0.25) * wsc
            if u > x + width:
                break
        if len(pts) >= 3:
            cv.polyline(smooth(pts, 3), ramp, tone, flat)
        cx = u + rng.uniform(*gap)


def typed_line(cv: Canvas, x, y, width, ramp, tone, seed, h=2):
    """Typewriter text too small to read: word blocks of 1-2 px height with gaps."""
    rng = np.random.default_rng(seed)
    cx = x
    while cx < x + width - 2:
        wl = int(rng.integers(3, 12))
        wl = min(wl, x + width - cx)
        for i in range(wl):
            if rng.random() < 0.82:
                cv.px(cx + i, y, ramp, tone)
            if h > 1 and rng.random() < 0.45:
                cv.px(cx + i, y + 1, ramp, tone)
        cx += wl + int(rng.integers(2, 4))


def paper_sheet(cv: Canvas, x, y, w, h, tone=6.0, seed=0, age=0.4, edge_dark=0.8, ramp='paper'):
    m = cv.rect(x, y, w, h, ramp, tone)
    full = cv.full(m)
    nz = pg.value_noise(cv.w, cv.h, 9, cv.seed + seed, octaves=3)
    cv.adjust((nz - 0.5) * 2 * age, full)
    cv.grain(0.25, full, seed)
    e = edge(full)
    cv.adjust(-edge_dark, e)
    return full


def shade_box(cv: Canvas, full, light_from='left', amount=0.6):
    ys, xs = np.nonzero(full)
    if len(xs) == 0:
        return
    x0, x1 = xs.min(), xs.max()
    f = np.zeros((cv.h, cv.w), np.float32)
    span = max(1, x1 - x0)
    lin = (np.arange(cv.w) - x0) / span
    lin = np.clip(lin, 0, 1)
    f[:] = (0.5 - lin)[None, :] * 2 * amount if light_from == 'left' else (lin - 0.5)[None, :] * 2 * amount
    cv.adjust(f, full)


def tack(cv: Canvas, x, y, ramp='red'):
    cv.px(x, y, ramp, cv.n(ramp) - 2)
    cv.px(x + 1, y, ramp, cv.n(ramp) - 3)
    cv.px(x, y + 1, ramp, cv.n(ramp) - 4)
    cv.px(x + 1, y + 1, ramp, 1)
    cv.px(x + 2, y + 2, 'room', 1)


def wall(cv: Canvas, tone=5.2, ramp='room', seed=1):
    cv.rect(0, 0, cv.w, cv.h, ramp, tone)
    cv.noise(14, 0.35, seed_add=seed)
    cv.grain(0.18, seed_add=seed)


def wood_planks(cv: Canvas, x, y, w, h, tone=4.0, plank=7, seed=3, ramp='wood', vertical=False):
    m = cv.rect(x, y, w, h, ramp, tone)
    full = cv.full(m)
    rng = np.random.default_rng(cv.seed + seed)
    yy, xx = np.mgrid[0:cv.h, 0:cv.w]
    nz = pg.value_noise(cv.w, cv.h, 5, cv.seed + seed, octaves=2)
    if vertical:
        grain = np.sin((xx + nz * 6) * 1.7 + yy * 0.02) * 0.25
    else:
        grain = np.sin((yy + nz * 6) * 1.9 + xx * 0.015) * 0.25
    cv.adjust(grain + (nz - 0.5) * 0.7, full)
    if vertical:
        for px_ in range(x + plank, x + w, plank):
            cv.adjust(-1.2, full & (xx == px_))
            cv.adjust(0.4, full & (xx == px_ + 1))
    else:
        for py_ in range(y + plank, y + h, plank):
            cv.adjust(-1.2, full & (yy == py_))
            cv.adjust(0.4, full & (yy == py_ + 1))
            off = int(rng.integers(0, w))
            cv.adjust(-1.0, full & (yy > py_) & (yy < py_ + plank) & (xx == x + off))
    return full


# =========================================================================== emblems (12.4)
def reichssiegel(d: int):
    """Fictional state emblem of the game world: white pillar/obelisk in a black disc (neutral variant)."""
    yy, xx = np.mgrid[0:d, 0:d]
    c = (d - 1) / 2.0
    disc = (xx - c) ** 2 + (yy - c) ** 2 <= (d / 2.0 - 0.15) ** 2
    pillar = np.zeros((d, d), bool)
    top, bot = int(round(d * 0.16)), int(round(d * 0.80))
    for y in range(top, bot + 1):
        f = (y - top) / max(1, bot - top)
        half = (0.5 + f / 0.14 * max(0.0, d * 0.07 - 0.5)) if f < 0.14 else d * (0.07 + 0.045 * (f - 0.14))
        pillar[y, int(round(c - half)):int(round(c + half)) + 1] = True
    pb, ph, hw = min(d - 2, bot + 1), max(1, int(round(d * 0.06))), d * 0.17
    pillar[pb:pb + ph, int(round(c - hw)):int(round(c + hw)) + 1] = True
    return disc, pillar & disc


# Historical swastika as used by the regime (black, standing on a corner, hooks turning clockwise).  Drawn ONLY
# into the *_hist.png variants of in-world regime iconography (TECHNICAL_ARCHITECTURE 12.4), never as decoration
# of the player's side, the UI or a reward.
# Hand-placed bitmaps for the small sizes (a rasteriser cannot keep the four hooks distinct below ~11 px):
# arms on the two diagonals, every hook turning clockwise.
HK_BITMAPS = {
    7: ['..#....',
        '.#...#.',
        '..#.#.#',
        '...#...',
        '#.#.#..',
        '.#...#.',
        '....#..'],
    9: ['....#....',
        '...#.....',
        '..#...#..',
        '...#.#.#.',
        '#...#...#',
        '.#.#.#...',
        '..#...#..',
        '.....#...',
        '....#....'],
}


def hakenkreuz(size: int) -> np.ndarray:
    """Swastika rotated 45 deg (clockwise hooks), size x size: hand bitmaps for 7/9 px, rasterised above."""
    if size in HK_BITMAPS:
        return np.array([[ch == '#' for ch in r] for r in HK_BITMAPS[size]], bool)
    # unrotated arms in unit coords (-1..1): centre cross + clockwise hooks
    segs = [((0, -1), (0, 1)), ((-1, 0), (1, 0)),
            ((0, -1), (1, -1)),    # top arm -> hook right
            ((1, 0), (1, 1)),      # right arm -> hook down
            ((0, 1), (-1, 1)),     # bottom arm -> hook left
            ((-1, 0), (-1, -1))]   # left arm -> hook up
    sup = 8
    S = size * sup
    m = np.zeros((S, S), bool)
    th = max(1.0, size * sup * 0.085)
    c = (S - 1) / 2.0
    rad = S * 0.36
    yy, xx = np.mgrid[0:S, 0:S]
    for (a, b) in segs:
        pts = []
        for (u, v) in (a, b):
            ru = (u - v) * math.sqrt(0.5)
            rv = (u + v) * math.sqrt(0.5)
            pts.append((c + ru * rad, c + rv * rad))
        (x0, y0), (x1, y1) = pts
        vx, vy = x1 - x0, y1 - y0
        L2 = vx * vx + vy * vy
        tt = np.clip(((xx - x0) * vx + (yy - y0) * vy) / L2, 0, 1)
        d2 = (xx - (x0 + tt * vx)) ** 2 + (yy - (y0 + tt * vy)) ** 2
        m |= d2 <= th * th
    small = m.reshape(size, sup, size, sup).mean(axis=(1, 3))
    return small >= 0.42


def eagle_mask(w: int, claws: bool = False) -> np.ndarray:
    """Plain heraldic eagle, wings spread, head turned to the viewer's left (simplified fictional drawing,
    no insignia).  Supersampled polygons -> clean 1-bit silhouette of width w."""
    h = int(round(w * 0.62))
    sup = 8
    Wb, Hb = w * sup, h * sup
    big = np.zeros((Hb, Wb), bool)

    def P(u, v):          # unit coords: u -0.5..0.5 (x), v -0.30..0.32 (y)
        return ((u + 0.5) * (Wb - 1), (v + 0.30) / 0.62 * (Hb - 1))

    def fill(pts):
        m, x0, y0 = poly_mask([P(u, v) for (u, v) in pts])
        mh, mw = m.shape
        X0, Y0 = max(0, x0), max(0, y0)
        X1, Y1 = min(Wb, x0 + mw), min(Hb, y0 + mh)
        big[Y0:Y1, X0:X1] |= m[Y0 - y0:Y1 - y0, X0 - x0:X1 - x0]

    for sgn in (-1, 1):
        wing = [(0.04, -0.06), (0.22, -0.20), (0.50, -0.28), (0.48, -0.17), (0.43, -0.13), (0.45, -0.05),
                (0.38, -0.07), (0.38, 0.02), (0.30, -0.01), (0.29, 0.08), (0.21, 0.04), (0.19, 0.12),
                (0.11, 0.07), (0.07, 0.12)]
        fill([(sgn * u, v) for (u, v) in wing])
    fill([(-0.09, -0.12), (0.09, -0.12), (0.10, 0.12), (0.06, 0.20), (-0.06, 0.20), (-0.10, 0.12)])   # body
    fill([(-0.07, 0.17), (0.07, 0.17), (0.13, 0.30), (0.06, 0.27), (0.0, 0.32), (-0.06, 0.27), (-0.13, 0.30)])  # tail
    fill([(-0.07, -0.13), (-0.03, -0.25), (0.04, -0.24), (0.06, -0.14)])                                # neck
    fill([(-0.04, -0.28), (0.03, -0.29), (0.05, -0.23), (-0.02, -0.20), (-0.08, -0.22)])               # head
    fill([(-0.08, -0.25), (-0.15, -0.23), (-0.08, -0.21)])                                              # beak
    if claws:
        fill([(-0.06, 0.16), (-0.03, 0.16), (-0.04, 0.26), (-0.07, 0.26)])
        fill([(0.03, 0.16), (0.06, 0.16), (0.07, 0.26), (0.04, 0.26)])
    small = big.reshape(h, sup, w, sup).mean(axis=(1, 3))
    m = small >= 0.45
    # the eye: one pixel hole in the head
    ey, ex = int(round(0.03 / 0.62 * (h - 1))), int(round(0.48 * (w - 1)))
    if w >= 20 and 0 <= ey < h and 0 <= ex < w:
        m[ey, ex] = False
    return m


# =========================================================================== scenes
# Each scene paints one 240x150 close-up.  `hist` only matters for the regime-iconography scenes.
YY, XX = np.mgrid[0:H, 0:W]


def s_coat_stand(cv: Canvas, hist=False):
    yy, xx = YY, XX
    wall(cv, 4.4)
    cv.linear(1.4, -0.9)
    wood_planks(cv, 0, 100, W, 36, tone=2.4, plank=40, vertical=True, seed=5)
    cv.rect(0, 98, W, 3, 'wood', 4.6)
    cv.rect(0, 101, W, 1, 'wood', 1.0)
    wood_planks(cv, 0, 136, W, 14, 2.0, plank=5, seed=6)
    # bentwood stand: pole, three feet, curled hooks
    pole = cv.full(cv.rect(117, 20, 5, 118, 'wood', 3.4))
    cv.bevel(pole, 1.2, 1.0)
    cv.adjust(-0.6, pole & (xx >= 120))
    for (a, b) in [((119, 132), (96, 147)), ((119, 132), (144, 147)), ((119, 134), (120, 148))]:
        cv.polyline(smooth([a, ((a[0] + b[0]) / 2, a[1] + 8), b], 4), 'wood', 2.2, width=2)
    cv.ellipse(119.5, 20, 5, 3, 'wood', 4.4)
    for side in (-1, 1):
        pts = [(119 + side * 2, 26), (119 + side * 12, 22), (119 + side * 20, 28), (119 + side * 18, 36), (119 + side * 13, 34)]
        cv.polyline(smooth(pts, 5), 'wood', 4.0, width=2)
    # Emil's grey archive coat on the left hook
    coat = [(100, 32), (108, 30), (112, 40), (114, 64), (118, 112), (84, 114), (80, 96), (86, 60), (92, 40)]
    cm = cv.full(cv.poly(coat, 'steel', 4.6))
    cv.adjust(np.sin((xx - 80) * 0.55 + yy * 0.05) * 0.5, cm)
    cv.adjust(-1.3, cm & (xx > 106) & (yy > 44))
    cv.bevel(cm, 0.8, 1.2)
    for yb in (66, 76):
        cv.px(103, yb, 'steel', 2.0); cv.px(104, yb, 'steel', 1.6)
    cv.line(96, 40, 102, 58, 'steel', 2.6)
    cv.shadow(cm, 3, 2, 1.0, ~pole)
    # two black umbrellas leaning against the pole (right)
    for k, (x0, cur) in enumerate([(150, 1), (160, -1)]):
        um = cv.full(cv.poly([(x0, 52), (x0 + 3, 52), (x0 + 6 - k, 128), (x0 + 4 - k, 130), (x0 - 1, 60)], 'violet', 2.0))
        cv.bevel(um, 1.0, 0.4)
        cv.polyline(smooth([(x0 + 1, 52), (x0 + 1, 46), (x0 + 4 + cur * 2, 42), (x0 + 7, 46)], 4), 'wood', 3.0, width=1)
        cv.line(x0 + 5 - k, 129, x0 + 5 - k, 137, 'steel', 3.0)
    # Brandt's dark-green wool scarf on the right hook (focal point, a little lamp light on it)
    scarf = [(136, 30), (142, 32), (146, 46), (147, 92), (141, 94), (139, 52), (134, 40)]
    sm = cv.full(cv.poly(scarf, 'green', 2.6))
    cv.adjust(np.where((yy // 3) % 2 == 0, 0.35, -0.35), sm)
    cv.adjust(-0.9, sm & (xx > 143))
    scarf2 = [(131, 34), (136, 36), (138, 82), (132, 84), (130, 50)]
    sm2 = cv.full(cv.poly(scarf2, 'green', 2.0))
    cv.adjust(np.where((yy // 3) % 2 == 0, 0.3, -0.3), sm2)
    for fx in range(141, 148, 2):
        cv.line(fx, 94, fx, 98, 'green', 2.0)
    for fx in range(132, 138, 2):
        cv.line(fx, 84, fx, 88, 'green', 1.6)
    cv.bevel(sm | sm2, 0.7, 0.8)
    cv.shadow(sm | sm2, 3, 2, 1.1, ~pole)
    cv.spot(170, 30, 110, 1.4)
    cv.spot(140, 60, 40, 0.8, sm | sm2)
    cv.vignette(1.6)


def s_clock(cv: Canvas, hist=False):
    """The regulator next to the porter's lodge: wooden case, enamel dial, brass pendulum and weights."""
    yy, xx = YY, XX
    wall(cv, 4.6)
    cv.linear(1.2, -0.8)
    # case
    case = cv.full(cv.rect(82, 14, 76, 136, 'wood', 3.0))
    cv.adjust(np.clip((120 - xx) * 0.03, -0.9, 0.9), case)
    cv.noise(5, 0.35, case, seed_add=4)
    cv.bevel(case, 1.4, 1.2)
    crown = cv.full(cv.poly([(76, 16), (164, 16), (156, 8), (130, 8), (120, 1), (110, 8), (84, 8)], 'wood', 3.6))
    cv.bevel(crown, 1.6, 1.0)
    cv.rect(118, 0, 4, 3, 'brass', 4.4)
    for x_ in (78, 160):
        col = cv.full(cv.rect(x_ - 2, 18, 6, 132, 'wood', 3.8))
        cv.bevel(col, 1.4, 1.2)
        for yb in range(24, 150, 22):
            cv.rect(x_ - 2, yb, 6, 2, 'wood', 5.0)
    cv.shadow(case | crown, 5, 4, 1.6)
    # glass door: dark interior behind glass
    door = cv.full(cv.rect(90, 22, 60, 128, 'room', 1.2))
    cv.put(edge(door), 0, 0, 'brass', 3, flat=True)
    # dial
    cx, cy, R_ = 120, 50, 23
    bez = cv.full(cv.ellipse(cx, cy, R_ + 2, R_ + 2, 'brass', 4.0))
    cv.adjust(np.clip((cx - xx) * 0.06 + (cy - yy) * 0.06, -1.2, 1.4), bez)
    dial = cv.full(cv.ellipse(cx, cy, R_, R_, 'paper', 6.4))
    d = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2)
    cv.adjust(-(d / R_) ** 2 * 1.0 + np.clip((cx - xx) * 0.02, -0.4, 0.4), dial)
    for i in range(60):
        a = i / 60 * 2 * math.pi
        if i % 5 == 0:
            cv.line(cx + math.sin(a) * (R_ - 2), cy - math.cos(a) * (R_ - 2), cx + math.sin(a) * (R_ - 5), cy - math.cos(a) * (R_ - 5), 'ink', 0)
        else:
            cv.px(cx + math.sin(a) * (R_ - 2), cy - math.cos(a) * (R_ - 2), 'ink', 1)
    for num, ang in (('12', 0), ('3', 90), ('6', 180), ('9', 270)):
        a = math.radians(ang)
        cv.text(cx + math.sin(a) * (R_ - 10), cy - math.cos(a) * (R_ - 10) - 2, num, 'ink', 0, align='center')
    # hands: a quarter past eight -- three minutes ahead, as ever
    for ang, ln, wd in ((8 * 30 + 18 * 0.5, 12, 2), (18 * 6, 18, 1)):
        a = math.radians(ang)
        cv.polyline([(cx - math.sin(a) * 3, cy + math.cos(a) * 3), (cx + math.sin(a) * ln, cy - math.cos(a) * ln)], 'ink', 0, width=wd)
    cv.px(cx, cy, 'brass', 5)
    # pendulum rod + bob (slightly out of centre: it swings), two weights on chains
    rod_x = 124
    cv.line(120, 74, rod_x, 128, 'brass', 3)
    cv.line(119, 74, rod_x - 1, 128, 'brass', 5)
    bob = cv.full(cv.ellipse(rod_x, 132, 11, 11, 'brass', 4.2))
    cv.adjust(np.clip((rod_x - xx) * 0.12 + (132 - yy) * 0.12, -1.6, 2.0), bob)
    cv.put(edge(bob), 0, 0, 'brass', 1, flat=True)
    for wx in (100, 140):
        cv.line(wx, 74, wx, 96, 'steel', 4, dash=(1, 1))
        wt = cv.full(cv.rect(wx - 4, 96, 9, 26, 'brass', 4.0))
        cv.adjust(np.clip((wx - xx) * 0.35, -1.2, 1.2), wt)
        cv.rect(wx - 4, 96, 9, 2, 'brass', 5.6)
    # glass reflections on the door
    cv.adjust(1.0, door & (np.abs((xx - 96) - (yy - 22) * 0.35) < 2))
    cv.adjust(0.6, door & (np.abs((xx - 104) - (yy - 22) * 0.35) < 1))
    cv.spot(60, 20, 150, 1.0)
    cv.vignette(1.4)


def s_heater(cv: Canvas, hist=False):
    yy, xx = YY, XX
    wall(cv, 4.2)
    cv.grad(0, 0, W, 34, 'blue', 3.6, 2.4)
    cv.noise(8, 0.4, cv.full((np.ones((34, W), bool), 0, 0)), seed_add=3)
    sill = cv.full(cv.rect(0, 34, W, 7, 'stone', 4.0))
    cv.bevel(sill, 1.6, 1.2)
    cv.rect(0, 41, W, 3, 'room', 1.5)
    wood_planks(cv, 0, 132, W, 18, 2.3, plank=6, seed=4)
    rx0, ry0, n_rib, rib = 34, 58, 13, 13
    rad = np.zeros((H, W), bool)
    for i in range(n_rib):
        x0 = rx0 + i * rib
        m = cv.full(cv.rect(x0 + 1, ry0 + 4, rib - 3, 66, 'steel', 4.6))
        m |= cv.full(cv.ellipse(x0 + (rib - 2) / 2 + 0.5, ry0 + 4, (rib - 3) / 2, 4, 'steel', 5.0))
        cv.adjust(np.clip((x0 + rib / 2 - xx) * 0.28, -1.4, 1.2), m)
        cv.bevel(m, 0.8, 0.8)
        rad |= m
    tubes = cv.full(cv.rect(rx0, ry0 + 14, n_rib * rib - 2, 4, 'steel', 3.4)) | cv.full(cv.rect(rx0, ry0 + 58, n_rib * rib - 2, 4, 'steel', 3.2))
    cv.adjust(-0.6, tubes & ~rad)
    cv.rect(rx0 + 4, ry0 + 70, 5, 6, 'steel', 2.4)
    cv.rect(rx0 + n_rib * rib - 12, ry0 + 70, 5, 6, 'steel', 2.4)
    valve = cv.full(cv.rect(rx0 - 10, ry0 + 50, 10, 5, 'brass', 3.4))
    cv.ellipse(rx0 - 12, ry0 + 52, 4, 4, 'ink', 1)
    cv.bevel(valve, 1, 1)
    cv.rect(rx0 - 14, ry0 + 55, 4, 77, 'steel', 2.0)
    cv.shadow(rad, 3, 3, 1.4)

    def mitten(x0, y0, h_, flip):
        pts = [(x0, y0), (x0 + 12, y0), (x0 + 13, y0 + h_ - 6), (x0 + 9, y0 + h_), (x0 + 3, y0 + h_), (x0 - 1, y0 + h_ - 6)]
        m = cv.full(cv.poly(pts, 'red', 3.6))
        thumb_x = x0 - 3 if not flip else x0 + 13
        m |= cv.full(cv.ellipse(thumb_x + 1.5, y0 + h_ * 0.45, 2.6, 4.5, 'red', 3.2))
        cv.adjust(np.where((yy % 2) == 0, 0.35, -0.25), m)
        band = m & (yy >= y0 + 4) & (yy <= y0 + 6)
        cv.put(band & ((xx + yy) % 3 != 0), 0, 0, 'snow', 4, flat=True)
        cv.adjust(-0.7, m & (yy < y0 + 3))
        cv.bevel(m, 0.6, 0.9)
        cv.shadow(m, 2, 2, 1.2)
        return m
    m1 = mitten(78, ry0 - 2, 30, False)
    m2 = mitten(98, ry0 - 2, 22, True)
    cv.polyline(smooth([(86, ry0 - 2), (92, ry0 - 6), (104, ry0 - 2)], 4), 'snow', 3)
    cv.spot(40, 0, 170, 1.0)
    cv.spot(95, 75, 40, 0.6, m1 | m2)
    cv.vignette(1.5)


def s_mouse(cv: Canvas, hist=False):
    yy, xx = YY, XX
    wall(cv, 5.0, seed=4)
    cv.linear(0.8, -0.6)
    pm = cv.full(cv.poly([(70, 40), (160, 34), (184, 56), (178, 92), (64, 96), (54, 66)], 'stone', 2.6))
    cv.noise(4, 0.7, pm, seed_add=9)
    cv.put(edge(pm), 0, 0, 'room', 3.0)
    cv.put(edge(pm) & np.roll(edge(pm), 1, 0), 0, 0, 'stone', 4.4)
    for (bx, by) in [(84, 50), (110, 44), (150, 48), (168, 70), (76, 80), (130, 84)]:
        cv.rect(bx, by, 3, 1, 'stone', 4.4, flat=True)
        cv.px(bx, by + 1, 'stone', 1.2)
    skirt = cv.full(cv.rect(0, 94, W, 30, 'wood', 2.8))
    cv.adjust(np.where(yy == 94, 2.2, 0.0) + np.where(yy == 95, 1.2, 0.0) + np.where(yy == 99, -0.8, 0.0), skirt)
    cv.noise(6, 0.3, skirt, seed_add=2)
    cv.rect(0, 123, W, 1, 'wood', 0.6)
    wood_planks(cv, 0, 124, W, 26, 2.6, plank=7, seed=8)
    # the hole: an arch gnawed into the skirting board
    r_h = 17
    hole_pts = [(122 - r_h, 124)] + [(122 + r_h * math.cos(math.pi - a / 20 * math.pi), 108 - r_h * math.sin(a / 20 * math.pi)) for a in range(0, 21)] + [(122 + r_h, 124)]
    hm = cv.full(cv.poly(hole_pts, 'ink', 0.0, flat=True))
    rim = edge(hm) & (yy < 123)
    cv.put(rim, 0, 0, 'wood', 1.4, flat=True)
    cv.put(dilate(rim, 1) & ~hm & skirt, 0, 0, 'wood', 4.2)
    # the mouse, peeking out: grey-brown fur, pink ear, black bead eye with a highlight, whiskers
    body = cv.full(cv.ellipse(124, 117, 11, 7, 'stone', 3.2))
    head = cv.full(cv.ellipse(135, 112, 7, 5.6, 'stone', 3.6))
    snout = cv.full(cv.poly([(139, 108), (149, 113), (139, 117)], 'stone', 3.9))
    mm = body | head | snout
    cv.adjust(np.clip((xx - 128) * 0.06, -0.7, 0.7) + np.clip((112 - yy) * 0.08, -0.4, 0.6), mm)
    cv.grain(0.3, mm, seed_add=6)
    cv.bevel(mm, 0.8, 0.8)
    ear = cv.full(cv.ellipse(131, 104, 3.6, 3.6, 'red', 5.0, flat=True))
    cv.put(cv.full(ellipse_mask(131, 104.5, 2.0, 2.0)), 0, 0, 'red', 4, flat=True)
    cv.put(edge(ear), 0, 0, 'stone', 2.2, flat=True)
    cv.rect(138, 110, 2, 2, 'ink', 0, flat=True)
    cv.px(138, 110, 'paper', 7)
    cv.rect(148, 112, 2, 2, 'red', 3, flat=True)
    for (wx, wy, ex_, ey_) in [(146, 111, 154, 108), (146, 114, 155, 114), (146, 116, 153, 119)]:
        cv.line(wx, wy, ex_, ey_, 'paper', 4)
    cv.polyline(smooth([(113, 119), (106, 122), (98, 121), (92, 123)], 4), 'stone', 2.6)
    cv.px(128, 123, 'red', 4); cv.px(132, 123, 'red', 4)
    # three crumbs in an orderly row and a thimble of water
    for i, cx_ in enumerate((158, 166, 174)):
        cv.rect(cx_, 125, 4, 3, 'amber', 3)
        cv.px(cx_, 125, 'amber', 4.4); cv.px(cx_ + 3, 127, 'amber', 1.4)
    th = cv.full(cv.poly([(186, 112), (198, 112), (197, 128), (187, 128)], 'steel', 4.6))
    cv.adjust(np.where((xx + yy) % 2 == 0, 0.6, -0.4), th & (yy > 114))
    cv.adjust(np.clip((192 - xx) * 0.12, -0.8, 0.8), th)
    cv.bevel(th, 1.0, 1.0)
    cv.rect(187, 112, 11, 2, 'blue', 4, flat=True)
    cv.shadow(th, 2, 1, 1.0)
    # the typed sign (with two dabs of glue) and the pencil line under it
    sign = paper_sheet(cv, 92, 56, 62, 20, tone=6.2, seed=5, age=0.3, edge_dark=0.6)
    cv.text(123, 59, 'ZUTRITT NUR', 'ink', 0, align='center')
    cv.text(123, 67, 'FÜR BEFUGTE', 'ink', 0, align='center')
    cv.shadow(sign, 1, 1, 0.8)
    cv.rect(93, 55, 3, 2, 'amber', 3, flat=True)
    cv.rect(150, 55, 3, 2, 'amber', 3, flat=True)
    lab = cv.full(cv.rect(97, 79, 54, 9, 'stone', 3.6))
    cv.text(124, 81, 'BEWOHNERIN: AKTE', 'graphite', 0, align='center')
    cv.spot(130, 112, 80, 1.1)
    cv.spot(120, 60, 60, 0.6)
    cv.vignette(1.6)


def s_radio(cv: Canvas, hist=False):
    yy, xx = YY, XX
    wall(cv, 4.2)
    cv.linear(1.0, -0.4)
    wood_planks(cv, 0, 124, W, 26, 3.2, plank=8, seed=2)
    cv.rect(0, 123, W, 1, 'wood', 6.0)
    bm = cv.full(cv.poly([(46, 124), (46, 40), (60, 22), (180, 22), (194, 40), (194, 124)], 'wood', 2.6))
    cv.adjust(np.clip((120 - xx) * 0.018, -0.8, 0.8) + np.clip((60 - yy) * 0.03, -0.4, 0.8), bm)
    cv.bevel(bm, 1.4, 1.2)
    cv.adjust(1.8, bm & (np.abs((xx - 60) - (yy - 30) * 0.6) < 2) & (yy < 80))
    cv.shadow(bm, 5, 3, 1.4)
    sp = cv.full(cv.rect(60, 34, 120, 52, 'wood', 1.4))
    cv.adjust(np.where((xx + yy) % 2 == 0, 0.6, 0.0), sp)
    for k in range(-5, 6):
        cv.polyline([(120 + k * 3, 86), (120 + k * 11, 36)], 'wood', 3.6, width=2)
    cv.bevel(sp, -0.8, -0.8)
    eye = cv.full(cv.ellipse(170, 44, 6, 6, 'ink', 0, flat=True))
    glow = cv.full(ellipse_mask(170, 44, 4.6, 4.6))
    cv.put(glow, 0, 0, 'green', 5, flat=True)
    cv.put(glow & (np.abs(XX - 170) <= 1) & (YY < 44), 0, 0, 'green', 1, flat=True)
    cv.put(cv.full(ellipse_mask(170, 44, 1.6, 1.6)), 0, 0, 'green', 6, flat=True)
    cv.put(edge(eye), 0, 0, 'brass', 3, flat=True)
    dw = cv.full(cv.rect(58, 92, 124, 18, 'amber', 3.8))
    cv.adjust(np.clip(1.4 - np.abs(xx - 110) * 0.025, -0.6, 1.4), dw)
    for i in range(0, 120, 4):
        cv.line(60 + i, 94, 60 + i, 95 if i % 20 else 97, 'wood', 1)
    for (name, x_) in (('BERLIN', 76), ('HAMBURG', 106), ('WIEN', 132), ('MÜNCHEN', 160)):
        cv.text(x_, 101, name, 'wood', 1, align='center')
    cv.line(75, 93, 75, 108, 'red', 2)
    cv.px(177, 104, 'graphite', 0)
    cv.px(178, 104, 'graphite', 1)
    cv.px(177, 105, 'graphite', 1)
    cv.put(edge(dw), 0, 0, 'brass', 3, flat=True)
    for kx in (82, 158):
        km = cv.full(cv.ellipse(kx, 117, 6, 5, 'wood', 1.8))
        cv.bevel(km, 1.6, 1.0)
        cv.line(kx, 113, kx, 116, 'wood', 5.0)
    paper_sheet(cv, 188, 128, 46, 18, 6.0, seed=8)
    cv.text(211, 131, 'HAUSORDNUNG', 'ink', 1, align='center')
    typed_line(cv, 192, 138, 38, 'ink', 1, 21, h=1)
    typed_line(cv, 192, 141, 30, 'ink', 1, 22, h=1)
    cv.spot(110, 100, 80, 1.2)
    cv.vignette(1.4)


def s_pigeons(cv: Canvas, hist=False):
    yy, xx = YY, XX
    # outside at dusk: sky, roofs with snow, the dome in the haze, a few lit windows, falling snow
    cv.grad(0, 0, W, 84, 'dusk', 4.0, 9.8, ease=1.5)
    cv.noise(24, 0.6, cv.full((np.ones((84, W), bool), 0, 0)), seed_add=1)
    dome = cv.full(ellipse_mask(182, 58, 26, 23)) & (yy < 60)
    cv.put(dome, 0, 0, 'patina', 1.4)
    cv.adjust(np.clip((182 - xx) * 0.03, -0.5, 0.6), dome)
    cv.rect(176, 31, 12, 5, 'patina', 1.2)
    cv.rect(181, 26, 2, 5, 'patina', 1.2)
    roofs = [(0, 64), (16, 56), (40, 56), (52, 62), (86, 62), (98, 50), (126, 50), (134, 60), (160, 60), (160, 58), (240, 58), (240, 84), (0, 84)]
    rm = cv.full(cv.poly(roofs, 'violet', 2.2))
    cv.adjust(np.where(yy < 66, 0.8, 0.0), rm)
    cv.put(rm & ~np.roll(rm, 1, 0), 0, 0, 'snow', 2, flat=True)
    for (wx_, wy_) in [(12, 70), (28, 74), (66, 70), (106, 64), (114, 72), (204, 68), (222, 72), (150, 70)]:
        cv.rect(wx_, wy_, 2, 3, 'glow', 2, flat=True)
    for (cx_, top) in [(24, 44), (110, 38)]:
        cv.rect(cx_, top, 3, 14, 'violet', 1.4)
    rng = np.random.default_rng(cv.seed)
    for _ in range(46):
        cv.px(int(rng.integers(0, W)), int(rng.integers(0, 80)), 'snow', 3 + int(rng.integers(0, 2)))
    # the sill outside the glass: stone ledge under fresh snow, a few crusts of bread
    sill = cv.full(cv.rect(0, 84, W, 44, 'stone', 2.2))
    cv.adjust(np.where(yy < 90, 1.4, 0.0) + np.where(yy > 118, -0.8, 0.0), sill)
    snow = cv.full(cv.rect(0, 84, W, 8, 'snow', 3.0))
    cv.noise(3, 0.7, snow, seed_add=4)
    cv.put(snow & (yy == 84), 0, 0, 'snow', 4, flat=True)
    for (bx, by) in [(66, 90), (71, 91), (148, 90), (153, 89), (200, 91)]:
        cv.rect(bx, by, 4, 2, 'amber', 2.2)
        cv.px(bx, by, 'amber', 3.4)

    def pigeon(px_, base, s, face, ring=False, fat=1.0, front=False):
        """Puffed winter pigeon; front=True faces the room (chest, both eyes), else 3/4 view."""
        body = cv.full(cv.ellipse(px_, base - 10 * s, 11 * s * fat, 9.5 * s, 'steel', 4.6))
        hx_ = px_ + (0 if front else face * 5 * s)
        neck = cv.full(cv.ellipse(hx_, base - 17 * s, 6.4 * s, 4.6 * s, 'patina', 3.2))
        head = cv.full(cv.ellipse(hx_, base - 23 * s, 4.8 * s, 4.6 * s, 'steel', 5.0))
        m = body | neck | head
        cv.adjust(np.clip((xx - px_) * -0.06, -0.7, 0.7) + np.clip((base - 12 * s - yy) * 0.06, -0.6, 0.6), body)
        cv.adjust(np.where((xx + yy) % 2 == 0, 0.4, -0.2), neck)
        if front:
            chest = body & (np.abs(xx - px_) < 6 * s * fat) & (yy < base - 4 * s)
            cv.adjust(0.6, chest)
            for sx in (-1, 1):
                wing = body & ((xx - px_) * sx > 5 * s * fat)
                cv.adjust(-1.2, wing)
                for k in (0, 3):
                    cv.line(px_ + sx * (7 + k) * s * fat, base - 13 * s, px_ + sx * (8 + k) * s * fat, base - 8 * s, 'steel', 1.4)
            for sx in (-1, 1):
                ex = int(round(hx_ + sx * 2.4 * s)); ey = int(round(base - 24 * s))
                cv.px(ex, ey, 'red', 5); cv.px(ex, ey + 1, 'ink', 0)
            bx_ = int(round(hx_)); by_ = int(round(base - 21.5 * s))
            cv.px(bx_, by_, 'snow', 4); cv.px(bx_, by_ + 1, 'snow', 1)
        else:
            wing = body & ((xx - px_) * -face > -3 * s)
            cv.adjust(-1.0, wing)
            for k in (0, 4):
                cv.line(px_ - face * (1 + k) * s, base - 12 * s, px_ - face * (5 + k) * s, base - 9 * s, 'steel', 1.4)
            cv.line(px_ - face * 9 * s, base - 9 * s, px_ - face * 15 * s, base - 6 * s, 'steel', 2.0)
            ex = int(round(hx_ + face * 1.8 * s)); ey = int(round(base - 24 * s))
            cv.px(ex, ey, 'red', 5); cv.px(ex + face, ey, 'ink', 0)
            bx_ = int(round(hx_ + face * 5.0 * s))
            cv.px(bx_, ey + 1, 'snow', 4); cv.px(bx_ + face, ey + 1, 'snow', 1); cv.px(bx_, ey + 2, 'snow', 1)
        cv.bevel(m, 0.9, 0.9)
        for fxo in (-3, 2):
            cv.line(px_ + fxo * s, base - 1, px_ + fxo * s, base, 'red', 4)
            cv.px(px_ + fxo * s - 1, base, 'red', 3)
        if ring:
            cv.px(px_ + 2 * s, base - 2, 'glow', 4)
            cv.px(px_ + 2 * s + 1, base - 2, 'glow', 3)
        cv.shadow(m, 2, 2, 0.9, sill | snow)
        return m
    pigeon(40, 104, 1.25, 1, fat=1.3, front=True)      # the fat one: has doubts
    pigeon(86, 104, 1.0, -1)
    pigeon(124, 104, 1.05, 1, ring=True, front=True)
    pigeon(162, 104, 0.95, -1, front=True)
    pigeon(202, 104, 1.0, 1)
    # inside: window frame, frost creeping in from the edges of the single big pane
    frame = np.zeros((H, W), bool)
    frame[:, :8] = True; frame[:, 232:] = True; frame[:6, :] = True; frame[126:, :] = True
    pane = ~frame
    nz = pg.value_noise(W, H, 5, cv.seed + 7, octaves=2)
    dd = np.minimum(np.minimum(xx - 8, 231 - xx), np.minimum(yy - 6, 125 - yy))
    fr = pane & (dd < 2 + nz * 9)
    cv.put(fr, 0, 0, 'snow', 3.0)
    cv.noise(3, 0.7, fr, seed_add=8)
    cv.put(fr & (dd > 1 + nz * 9 - 1.2), 0, 0, 'snow', 4, flat=True)
    cv.put(frame, 0, 0, 'wood', 2.2)
    cv.bevel(frame, 1.0, 0.8)
    cv.adjust(0.9, pane & (np.abs((xx - 30) + (yy - 10) * 1.1) < 3))
    wood_planks(cv, 0, 126, W, 24, 2.2, plank=8, seed=9)
    cv.rect(0, 126, W, 2, 'wood', 4.8)
    cv.vignette(1.2)


def s_photo(cv: Canvas, hist=False):
    yy, xx = YY, XX
    wall(cv, 4.6)
    cv.linear(1.0, -0.6)
    frame = cv.full(cv.rect(30, 1, 180, 148, 'wood', 1.6))
    cv.bevel(frame, 1.4, 1.0)
    cv.shadow(frame, 4, 3, 1.6)
    mount = paper_sheet(cv, 34, 4, 172, 142, tone=5.8, seed=2, age=0.35, edge_dark=1.2)
    pxa, pya, pw, ph = 44, 12, 152, 100
    ph_m = cv.full(cv.rect(pxa, pya, pw, ph, 'sepia', 6.0))
    cv.put(edge(dilate(ph_m, 1)) & ~ph_m, 0, 0, 'paper', 7.4)
    # studio: wall, the big hall model on its table
    cv.grad(pxa, pya, pw, 60, 'sepia', 4.4, 6.4)
    cv.noise(10, 0.4, ph_m, seed_add=5)
    dome = cv.full(ellipse_mask(120, 46, 34, 27)) & (yy < 47) & ph_m
    cv.put(dome, 0, 0, 'sepia', 8.4)
    nxs = (xx - 120) / 34.0
    cv.adjust(np.clip(-nxs * 1.6, -1.6, 1.4), dome)
    for k in range(-30, 31, 6):
        cv.line(120 + k, 46, 120 + k * 0.38, 20 + abs(k) * 0.34, 'sepia', 6.4, flat=False)
    cv.rect(115, 15, 10, 5, 'sepia', 7.8)
    cv.rect(119, 11, 2, 4, 'sepia', 7.8)
    cv.rect(80, 46, 80, 18, 'sepia', 7.2)
    for k in range(82, 160, 4):
        cv.line(k, 48, k, 62, 'sepia', 5.2, flat=False)
    cv.rect(80, 46, 80, 1, 'sepia', 9.4)
    cv.rect(66, 64, 108, 4, 'sepia', 2.6)
    rng = np.random.default_rng(cv.seed)

    def man(x_, hy, s, shirt=10.2, hair=2.4, bald=False, glasses=False, waist=None):
        sh_w = 7.5 * s
        top = hy + 5 * s
        bottom = pya + ph if waist is None else waist
        torso = cv.full(cv.poly([(x_ - sh_w, top + 2 * s), (x_ - sh_w + 2, top), (x_ + sh_w - 2, top), (x_ + sh_w, top + 2 * s),
                                 (x_ + sh_w - 1, bottom), (x_ - sh_w + 1, bottom)], 'sepia', shirt)) & ph_m
        cv.adjust(np.clip((xx - x_) * -0.10, -0.9, 0.6), torso)
        cv.line(x_, top + 1, x_, top + 9 * s, 'sepia', 1.6, flat=False)        # tie
        cv.px(x_ - 1, top, 'sepia', 8.0, flat=False); cv.px(x_ + 1, top, 'sepia', 8.0, flat=False)   # collar
        if waist is not None:
            cv.rect(x_ - sh_w + 1, waist, 2 * sh_w - 2, pya + ph - waist, 'sepia', 2.2)
        # rolled sleeves: forearms in skin tone at the sides
        for sx in (-1, 1):
            cv.rect(x_ + sx * sh_w - (1 if sx > 0 else 1), top + 10 * s, 2, 6 * s, 'sepia', 6.6)
        cv.rect(x_ - 1.5 * s, hy + 3 * s, 3 * s, 2.5 * s, 'sepia', 6.2)              # neck
        face = cv.full(cv.ellipse(x_, hy, 3.4 * s, 4.0 * s, 'sepia', 7.2))
        cv.adjust(np.clip((xx - x_) * -0.18, -0.8, 0.6), face)
        if bald:
            cv.put(face & (yy < hy - 1.5 * s) & (np.abs(xx - x_) > 2 * s), 0, 0, 'sepia', 3.0)
            cv.adjust(1.0, face & (yy < hy - 2 * s) & (np.abs(xx - x_) <= 2 * s))
        else:
            cv.put(face & (yy < hy - 1.4 * s), 0, 0, 'sepia', hair)
        if glasses:
            cv.px(x_ - 1.5 * s, hy, 'sepia', 1.0); cv.px(x_ + 1.5 * s, hy, 'sepia', 1.0)
        return face | torso
    back = [(62, 64), (80, 63), (98, 64), (116, 63), (134, 64), (152, 63), (170, 64)]
    for i, (x_, hy) in enumerate(back):
        man(x_, hy, 1.0, shirt=10.0 + (i % 2) * 0.6, hair=1.8 + (i % 3) * 0.6)
    front = [(70, 80), (95, 81), (120, 80), (145, 81), (170, 80)]
    for i, (x_, hy) in enumerate(front):
        man(x_, hy, 1.25, shirt=10.6 - (i % 2) * 0.5, hair=2.0 + (i % 2) * 1.0, bald=(i == 2), glasses=(i == 2), waist=104)
    # Brandt, back row, sixth from the left: the face scratched out with a needle, down to the white paper
    bx_, by_ = 152, 63
    cv.ellipse(bx_, by_, 3.6, 4.2, 'sepia', 11, flat=True)
    for k in range(10):
        a = rng.uniform(0, math.pi)
        r_ = rng.uniform(3, 7)
        cv.line(bx_ - math.cos(a) * r_, by_ - math.sin(a) * r_ * 0.8, bx_ + math.cos(a) * r_, by_ + math.sin(a) * r_ * 0.8, 'sepia', 11)
    for k in range(4):
        cv.line(bx_ + rng.uniform(-4, 4), by_ - 6, bx_ + rng.uniform(-7, 7), by_ + rng.uniform(0, 9), 'sepia', 10.4)
    cv.grain(0.45, ph_m, seed_add=11)
    cv.adjust(-((np.abs(xx - 120) / 78.0) ** 3 + (np.abs(yy - 62) / 52.0) ** 3) * 1.6, ph_m)

    def emboss(text, y0):
        m = text_mask(text, overhang=True)
        e = m.shape[0] - 5                                  # umlaut dots above the cap line
        w_ = m.shape[1]
        x0 = 120 - w_ // 2
        hi = np.zeros((H, W), bool); lo = np.zeros((H, W), bool)
        hi[y0 - e:y0 + 5, x0:x0 + w_] = m
        lo[y0 + 1 - e:y0 + 6, x0 + 1:x0 + 1 + w_] = m
        cv.adjust(-1.4, lo & ~hi & mount)
        cv.adjust(1.2, hi & mount)
    emboss('ABTEILUNG ACHSE SÜD', 119)
    emboss('NACH ABSCHLUSS DER FREIMACHUNG', 127)
    emboss('JULI 1961', 135)
    cv.spot(30, 0, 220, 1.3)
    cv.vignette(1.4)


def s_notice(cv: Canvas, hist=False):
    yy, xx = YY, XX
    wall(cv, 4.4)
    cv.linear(1.0, -0.8)
    board = cv.full(cv.rect(16, 8, 208, 136, 'wood', 1.6))
    cv.bevel(board, 1.6, 1.2)
    cork = cv.full(cv.rect(22, 14, 196, 124, 'wood', 4.8))
    cv.grain(0.9, cork, seed_add=4)
    cv.noise(6, 0.5, cork, seed_add=5)
    cv.shadow(board, 4, 4, 1.4)
    paper_sheet(cv, 30, 22, 56, 70, 4.2, seed=3, age=0.6)
    for ly in range(30, 88, 5):
        typed_line(cv, 34, ly, 32, 'paper', 2, 40 + ly, h=1)
    paper_sheet(cv, 190, 96, 24, 34, 5.0, seed=4, age=0.5)
    scribble(cv, 192, 106, 20, 'blue', 1, 77, xh=1.6)
    scribble(cv, 192, 114, 18, 'blue', 1, 78, xh=1.6)
    tack(cv, 200, 97, 'brass')
    sx, sy, sw, sh_ = 68, 18, 118, 118
    sheet = paper_sheet(cv, sx, sy, sw, sh_, 6.4, seed=6, age=0.3)
    cv.shadow(sheet, 2, 2, 1.2, cork)
    cv.text(sx + sw // 2, sy + 5, 'BESTANDSÄNDERUNGEN', 'ink', 0, align='center')
    cv.text(sx + sw // 2, sy + 12, 'ACHSE SÜD', 'ink', 0, align='center')
    cv.line(sx + 6, sy + 19, sx + sw - 7, sy + 19, 'ink', 1)
    cv.text(sx + 6, sy + 22, 'NAME', 'ink', 1)
    cv.text(sx + 44, sy + 22, 'VERMERK', 'ink', 1)
    cv.text(sx + 86, sy + 22, 'NEU', 'ink', 1)
    cv.line(sx + 6, sy + 28, sx + sw - 7, sy + 28, 'ink', 1)
    cv.line(sx + 82, sy + 20, sx + 82, sy + sh_ - 8, 'ink', 1)
    for r in range(10):
        y_ = sy + 31 + r * 7
        typed_line(cv, sx + 6, y_ + 2, 34, 'ink', 1, 300 + r, h=2)
        cv.text(sx + 44, y_, 'UMGESETZT', 'ink', 0)
    y_last = sy + 31 + 10 * 7
    cv.text(sx + 6, y_last + 1, 'KOLONNENSTR. 12', 'ink', 0)
    for (tx, ty) in [(sx + 3, sy + 2), (sx + sw - 5, sy + 2)]:
        tack(cv, tx, ty, 'red')
    tack(cv, 56, 23, 'red')
    cv.spot(200, 120, 90, 0.8)
    cv.spot(40, 20, 120, 0.7)
    cv.vignette(1.3)


def s_pneumatic_tube(cv: Canvas, hist=False):
    yy, xx = YY, XX
    wall(cv, 4.6)
    cv.linear(1.1, -0.6)
    tube = cv.full(cv.rect(30, 0, 12, 50, 'brass', 3.4))
    cv.adjust(np.clip((36 - xx) * 0.35, -1.6, 1.6), tube)
    for cy_ in (10, 30):
        cv.rect(28, cy_, 16, 3, 'brass', 2.2)
    st = cv.full(cv.rect(14, 46, 60, 40, 'steel', 3.6))
    cv.bevel(st, 1.4, 1.4)
    flap = cv.full(cv.rect(22, 54, 44, 22, 'steel', 2.6))
    cv.bevel(flap, -0.8, -0.8)
    cv.text(44, 79, 'ROHRPOST', 'ink', 0, align='center')
    cv.shadow(st | tube, 4, 3, 1.4)
    wood_planks(cv, 0, 112, W, 38, 3.4, plank=9, seed=3)
    cv.rect(0, 111, W, 1, 'wood', 6.4)
    bm = cv.full(cv.poly([(20, 98), (150, 98), (142, 132), (28, 132)], 'steel', 1.6))
    for x_ in range(22, 150, 8):
        cv.line(x_, 98, x_ - (x_ - 85) * 0.06, 132, 'steel', 3.0)
    cap = cv.full(cv.rect(40, 100, 72, 18, 'wood', 3.6))
    cv.adjust(np.clip((109 - yy) * 0.22 - 0.8, -1.2, 1.4), cap)
    ends = cv.full(cv.rect(40, 100, 10, 18, 'steel', 5.0)) | cv.full(cv.rect(104, 100, 8, 18, 'steel', 4.6))
    cv.adjust(np.clip((109 - yy) * 0.25 - 0.6, -1.4, 1.4), ends)
    cv.line(70, 100, 70, 117, 'wood', 1.6)
    cv.line(84, 100, 84, 117, 'wood', 1.6)
    cv.rect(52, 101, 16, 1, 'wood', 6.0)
    lid = cv.full(cv.ellipse(126, 118, 6, 8, 'steel', 4.4))
    cv.bevel(lid, 1.4, 1.0)
    cv.ellipse(126, 118, 3, 4.5, 'steel', 2.6)
    cv.shadow(cap | ends | lid, 2, 3, 1.4, bm)
    cv.line(20, 98, 150, 98, 'steel', 5.0)
    cv.line(28, 132, 142, 132, 'steel', 3.0)
    slip = paper_sheet(cv, 108, 72, 84, 58, 6.4, seed=4, age=0.25)
    cv.shadow(slip, 3, 3, 1.4)
    cv.text(150, 76, 'LAUFZETTEL', 'ink', 0, align='center')
    cv.line(112, 83, 188, 83, 'ink', 1)
    cv.text(112, 86, 'AN ABT. III PERS.', 'ink', 0)
    cv.text(112, 93, 'PLANSTÄNDE ACHSE SÜD', 'ink', 1)
    cv.text(112, 100, 'REV. VOR STAND 4', 'ink', 1)
    cv.text(112, 107, 'ZUR AUSSONDERUNG', 'ink', 0)
    stamp = np.zeros((H, W), bool)
    stamp[116:125, 160:184] = True
    cv.put(edge(stamp) & ((xx * 7 + yy * 3) % 5 != 0), 0, 0, 'red', 3, flat=True)
    tm = text_mask('EILT')
    cv.put(tm & (np.arange(tm.shape[1])[None, :] % 7 != 3), 164, 118, 'red', 3, flat=True)
    paper_sheet(cv, 194, 108, 40, 30, 5.6, seed=9, age=0.5)
    heart = [(206, 117), (209, 114), (212, 116), (215, 114), (218, 117), (212, 124)]
    cv.polyline(smooth(heart + [heart[0]], 4), 'graphite', 1)
    cv.text(214, 127, '17 UHR?', 'graphite', 0, align='center')
    cv.spot(230, 20, 160, 1.2)
    cv.vignette(1.4)


def s_card_catalogue(cv: Canvas, hist=False):
    yy, xx = YY, XX
    wood_planks(cv, 0, 0, W, H, 2.4, plank=37, seed=2)
    for (dx_, dy_) in [(4, 10), (4, 56), (214, 10), (214, 56), (4, 102), (214, 102)]:
        dm = cv.full(cv.rect(dx_, dy_, 22, 40, 'wood', 3.0))
        cv.bevel(dm, 1.0, 1.2)
        cv.rect(dx_ + 5, dy_ + 10, 12, 6, 'brass', 3.4)
        cv.rect(dx_ + 6, dy_ + 11, 10, 4, 'paper', 5.0)
    cv.grad(36, 6, 168, 106, 'wood', 0.6, 2.0)
    side = cv.full(cv.poly([(30, 6), (38, 6), (38, 110), (30, 112)], 'wood', 3.2)) | cv.full(cv.poly([(202, 6), (210, 6), (210, 112), (202, 110)], 'wood', 2.4))
    cv.bevel(side, 0.8, 0.6)

    def cards(y0, y1, step=2):
        for y_ in range(y0, y1, step):
            cv.rect(40, y_, 160, step, 'paper', 4.6)
            cv.rect(40, y_, 160, 1, 'paper', 6.6)

    def guide(y_, tab_x, label, tone=3.6):
        cv.rect(40, y_, 160, 3, 'blue', tone)
        cv.rect(40, y_, 160, 1, 'blue', tone + 1.2)
        tab = cv.full(cv.rect(tab_x, y_ - 7, 22, 7, 'blue', tone))
        cv.bevel(tab, 1.0, 0.6)
        cv.rect(tab_x + 2, y_ - 6, 18, 5, 'paper', 6.0, flat=True)
        cv.text(tab_x + 11, y_ - 6, label, 'ink', 0, align='center')
    cards(12, 30)
    guide(30, 150, 'C-18')
    cards(33, 40)
    gap = cv.full(cv.rect(40, 40, 160, 12, 'wood', 1.2))
    cv.adjust(np.where(yy > 46, -0.5, 0.2), gap)
    lm = cv.full(cv.poly([(40, 52), (200, 52), (200, 80), (40, 80)], 'blue', 3.0))
    cv.adjust(np.clip((yy - 52) * 0.03, 0, 0.9), lm)
    cv.rect(40, 52, 160, 1, 'blue', 4.6)
    tab = cv.full(cv.rect(96, 45, 24, 8, 'blue', 3.0))
    cv.bevel(tab, 1.0, 0.6)
    cv.rect(98, 46, 20, 6, 'paper', 6.2, flat=True)
    cv.text(108, 47, 'C-17', 'ink', 0, align='center')
    paper_sheet(cv, 56, 58, 128, 18, 5.8, seed=7, age=0.2, edge_dark=0.5)
    cv.text(62, 61, 'ENTNOMMEN', 'graphite', 0)
    cv.text(62, 68, 'S. ABT. III', 'graphite', 0)
    cv.line(104, 65, 170, 63, 'graphite', 2)
    cv.shadow(lm, 0, 3, 1.4)
    cards(80, 94)
    guide(94, 56, 'C-16')
    cards(97, 104)
    guide(104, 168, 'C-15')
    cards(107, 112)
    front = cv.full(cv.rect(28, 112, 184, 38, 'wood', 3.6))
    cv.bevel(front, 1.6, 1.0)
    cv.noise(5, 0.4, front, seed_add=3)
    plate = cv.full(cv.rect(100, 118, 40, 12, 'brass', 3.6))
    cv.bevel(plate, 1.2, 1.2)
    cv.rect(103, 120, 34, 8, 'paper', 6.0, flat=True)
    cv.text(120, 122, 'C 1-40', 'ink', 0, align='center')
    hole = cv.full(cv.ellipse(120, 140, 3.5, 2.5, 'wood', 2.6))
    ring = cv.full(cv.ellipse(120, 140, 6, 5, 'brass', 4.0)) & ~hole
    cv.put(ring, 0, 0, 'brass', 4.0)
    cv.put(hole, 0, 0, 'wood', 2.6)
    cv.bevel(ring, 1.4, 1.0)
    cv.spot(200, 10, 150, 1.4)
    cv.linear(0.6, -0.2)
    cv.vignette(1.3)


def s_reading_table(cv: Canvas, hist=False):
    yy, xx = YY, XX
    cv.rect(0, 0, W, 70, 'room', 2.0)
    for x_ in range(0, W, 7):
        h_ = 24 + (x_ * 37 % 9)
        cv.rect(x_, 46 - h_ // 2, 5, h_ // 2 + 22, 'wood', 1.4 + (x_ * 13 % 5) * 0.2)
    cv.rect(0, 66, W, 4, 'wood', 1.6)
    cv.rect(0, 18, W, 3, 'wood', 1.8)
    table = wood_planks(cv, 0, 70, W, 80, 3.4, plank=20, seed=4)
    cv.rect(0, 70, W, 2, 'wood', 6.0)
    cv.rect(186, 64, 4, 34, 'brass', 3.4)
    base = cv.full(cv.ellipse(188, 99, 16, 4, 'brass', 3.4))
    cv.bevel(base, 1.2, 1.0)
    shade = cv.full(cv.poly([(160, 52), (214, 52), (210, 64), (164, 64)], 'green', 3.2))
    cv.adjust(np.clip((yy - 52) * 0.1, -1, 1), shade)
    cv.bevel(shade, 2.0, 1.0)
    cv.rect(166, 64, 42, 2, 'amber', 5, flat=True)
    cv.spot(180, 92, 120, 2.4, table)
    cv.spot(180, 66, 60, 1.0, ~table)
    slip = paper_sheet(cv, 70, 86, 92, 50, 6.0, seed=6, age=0.25)
    cv.text(116, 89, 'BESTELLSCHEIN', 'ink', 0, align='center')
    cv.line(74, 96, 158, 96, 'ink', 1)
    cv.text(74, 99, 'LESER NR. 114', 'ink', 0)
    for i in range(3):
        typed_line(cv, 74, 107 + i * 4, 60, 'ink', 1, 500 + i, h=1)
    cv.text(74, 121, 'AUSWEIS EINGEZOGEN', 'green', 2)
    cv.text(74, 128, '2.11.', 'green', 2)
    cv.shadow(slip, 3, 3, 1.6, table)
    for (lx, ly) in ((112, 110), (132, 110)):
        lens = cv.full(cv.ellipse(lx, ly, 8, 6, 'paper', 6.6))
        cv.put(edge(lens), 0, 0, 'brass', 2, flat=True)
        cv.px(lx - 3, ly - 3, 'paper', 7)
        cv.px(lx - 2, ly - 3, 'paper', 7)
        cv.shadow(lens, 2, 3, 1.2, slip | table)
    cv.line(120, 109, 124, 109, 'brass', 2)
    cv.polyline(smooth([(104, 108), (98, 104), (90, 105), (88, 112)], 4), 'brass', 2)
    cv.polyline(smooth([(140, 108), (146, 104), (154, 103), (158, 108)], 4), 'brass', 2)
    cv.vignette(1.6)


def s_globe(cv: Canvas, hist=False):
    yy, xx = YY, XX
    cv.rect(0, 0, W, H, 'room', 2.2)
    for x_ in range(0, W, 6):
        cv.rect(x_, 10, 4, 54, 'wood', 1.0 + (x_ * 7 % 5) * 0.25)
        cv.rect(x_, 74, 4, 50, 'wood', 1.0 + (x_ * 11 % 5) * 0.25)
    cv.rect(0, 64, W, 6, 'wood', 1.8)
    cv.rect(0, 124, W, 26, 'wood', 2.4)
    cv.rect(0, 124, W, 1, 'wood', 4.6)
    cv.vignette(1.0)
    gx, gy, gr = 120, 66, 46
    foot = cv.full(cv.ellipse(120, 136, 26, 6, 'wood', 3.0))
    cv.bevel(foot, 1.4, 1.0)
    cv.rect(117, 112, 6, 24, 'wood', 3.2)
    ring = (cv.full(cv.ellipse(gx, gy, gr + 6, gr + 6, 'brass', 3.6)) & ~cv.full(ellipse_mask(gx, gy, gr + 3, gr + 3))) & (xx > gx - 10)
    cv.put(ring, 0, 0, 'brass', 3.6)
    cv.adjust(np.clip((gy - yy) * 0.03, -1, 1), ring)
    sph = cv.full(cv.ellipse(gx, gy, gr, gr, 'blue', 3.0))
    nz = pg.value_noise(W, H, 16, cv.seed + 3, octaves=4)
    land = sph & (nz > 0.53)
    cv.put(land, 0, 0, 'stone', 4.2)
    cv.adjust((nz - 0.55) * 3.0, land)
    nxs = (xx - gx) / gr
    nys = (yy - gy) / gr
    nz_ = np.sqrt(np.clip(1 - nxs ** 2 - nys ** 2, 0, 1))
    lam = np.clip(-0.55 * nxs - 0.6 * nys + 0.6 * nz_, 0, 1)
    cv.adjust((lam - 0.45) * 3.2, sph)
    cv.put(edge(land) & sph & ((xx + yy) % 3 != 0), 0, 0, 'ink', 1, flat=True)
    rng = np.random.default_rng(cv.seed)
    for _ in range(4):
        sx = int(rng.integers(gx - 26, gx + 14)); sy = int(rng.integers(gy - 24, gy + 18))
        strip = cv.full(cv.rect(sx, sy, int(rng.integers(8, 15)), int(rng.integers(4, 7)), 'paper', 5.2)) & sph
        cv.adjust((lam - 0.45) * 2.0, strip)
        cv.put(edge(strip), 0, 0, 'paper', 3.4)
    pts = [(gx + 14 + math.sin(i / 32 * 7.0) * 4 + i / 32 * 6, gy - gr * 0.92 + i / 32 * gr * 1.84) for i in range(33)]
    m = cv.polyline(pts, 'red', 4, flat=True)
    cv.put(m & ~sph, 0, 0, 'room', 2.2)
    cv.put(edge(sph), 0, 0, 'ink', 0, flat=True)
    cv.adjust(1.4, sph & (((xx - (gx - 18)) ** 2 + (yy - (gy - 20)) ** 2) < 30))
    cv.spot(40, 20, 160, 1.0)
    cv.vignette(1.2)


def open_book(cv: Canvas, x, y, w, h, tone=6.2, seed=0):
    """Two pages with a gutter shadow and gilt edges; returns (left_mask, right_mask)."""
    yy, xx = YY, XX
    cover = cv.full(cv.rect(x - 4, y + 2, w + 8, h + 4, 'red', 2.0))
    cv.bevel(cover, 0.8, 0.8)
    pages = cv.full(cv.rect(x, y, w, h, 'paper', tone))
    cv.grain(0.25, pages, seed)
    mid = x + w // 2
    cv.adjust(-np.clip(1 - np.abs(xx - mid) / 14.0, 0, 1) ** 2 * 2.4, pages)
    for k in (1, 2):
        cv.rect(x, y + h - 1 + k, w, 1, 'brass', 4.4 - k)
    return pages & (xx < mid), pages & (xx >= mid)


def s_lib_shelf_1(cv: Canvas, hist=False):
    wood_planks(cv, 0, 0, W, H, 1.8, plank=11, seed=1)
    left, right = open_book(cv, 24, 14, 192, 118, seed=2)
    cv.shadow(left | right, 4, 4, 1.6)
    cv.text(70, 20, 'CHRONIK 1942', 'ink', 1, align='center')
    cv.text(170, 20, 'CHRONIK 1942', 'ink', 1, align='center')
    cv.text(30, 30, '19. JANUAR', 'ink', 0, font='57')
    cv.text(126, 30, '21. JANUAR', 'ink', 0, font='57')
    for i in range(11):
        typed_line(cv, 30, 42 + i * 7, 84 if i != 10 else 40, 'ink', 1, 600 + i, h=2)
        typed_line(cv, 126, 42 + i * 7, 84 if i != 0 else 52, 'ink', 1, 700 + i, h=2)
    cv.text(30, 122, '41', 'ink', 1)
    cv.text(208, 122, '42', 'ink', 1)
    cv.polyline([(121, 14), (122, 60), (119, 110), (121, 140)], 'red', 3, width=2)
    cv.spot(200, 0, 180, 1.2)
    cv.vignette(1.4)


def s_lib_shelf_2(cv: Canvas, hist=False):
    xx = XX
    cv.rect(0, 0, W, H, 'room', 1.4)
    cv.rect(0, 128, W, 22, 'wood', 3.0)
    cv.rect(0, 128, W, 2, 'wood', 5.6)
    rng = np.random.default_rng(cv.seed)
    x_ = 6
    done = False
    while x_ < 234:
        bw = int(rng.integers(13, 17))
        if x_ >= 104 and not done:
            # the wooden dummy: grey linen spine a finger's breadth proud of the row; its top shows end grain
            bx, top = x_, 28
            spine = cv.full(cv.rect(bx, top, 16, 100, 'steel', 4.0))
            cv.bevel(spine, 1.0, 1.0)
            cv.noise(3, 0.4, spine, seed_add=12)
            cv.poly([(bx, top), (bx + 16, top), (bx + 20, top - 4), (bx + 4, top - 4)], 'wood', 4.6)
            for k in range(0, 18, 3):
                cv.line(bx + 1 + k * 0.9, top - 1, bx + 4 + k * 0.9, top - 3, 'wood', 3.0 + (k % 4) * 0.4)
            side = cv.full(cv.poly([(bx + 16, top), (bx + 20, top - 4), (bx + 20, 124), (bx + 16, 128)], 'steel', 2.0))
            cv.rect(bx + 2, top + 10, 12, 54, 'paper', 6.0)
            for j, ch in enumerate('SONDERZ'):
                cv.text(bx + 8, top + 13 + j * 7, ch, 'ink', 0, align='center')
            cv.text(bx + 8, top + 70, '42', 'ink', 1, align='center')
            cv.text(bx + 8, top + 77, '44', 'ink', 1, align='center')
            cv.shadow(spine | side, 3, 0, 1.4)
            x_ += 22
            done = True
            continue
        top = 26 + int(rng.integers(0, 6))
        tone = 2.6 + rng.uniform(-0.4, 0.4)
        sp = cv.full(cv.rect(x_, top, bw, 128 - top, 'red', tone))
        cv.adjust(np.clip((x_ + bw / 2 - xx) * 0.18, -0.8, 0.8), sp)
        cv.rect(x_ + 1, top + 8, bw - 2, 2, 'brass', 4.2)
        cv.rect(x_ + 1, top + 86, bw - 2, 2, 'brass', 4.2)
        cv.text(x_ + bw // 2, top + 14, str(1934 + x_ // 16)[2:], 'brass', 5, align='center')
        cv.put(np.ones((128 - top, 1), bool), x_, top, 'red', 0.6)
        x_ += bw + 1
    cv.spot(60, 0, 200, 1.4)
    cv.vignette(1.4)


def s_lib_shelf_3(cv: Canvas, hist=False):
    yy, xx = YY, XX
    wood_planks(cv, 0, 0, W, H, 1.8, plank=11, seed=2)
    left, right = open_book(cv, 14, 10, 212, 126, tone=6.0, seed=3)
    pages = left | right
    cv.shadow(pages, 4, 4, 1.6)
    cv.text(120, 14, 'DIE NEUE SIEDLUNG IM OSTEN', 'ink', 0, align='center')
    nz = pg.value_noise(W, H, 22, cv.seed + 5, octaves=3)
    mapm = pages & (yy > 22) & (yy < 110) & (xx > 20) & (xx < 220)
    green = mapm & (nz + (xx - 120) * -0.004 > 0.5)
    grey = mapm & ~green
    cv.put(grey, 0, 0, 'paper', 3.6)
    cv.grain(0.3, grey, seed_add=4)
    cv.put(green, 0, 0, 'green', 4.6)
    cv.adjust(np.where((xx + yy) % 2 == 0, 0.4, -0.4), green)
    for gx_ in range(26, 216, 12):
        for gy_ in range(28, 106, 10):
            if green[gy_, gx_] and green[gy_ + 2, gx_ + 3]:
                cv.rect(gx_, gy_, 3, 2, 'green', 1, flat=True)
    rng = np.random.default_rng(cv.seed)
    for _ in range(14):
        tx, ty = int(rng.integers(26, 200)), int(rng.integers(30, 104))
        if grey[ty, tx]:
            cv.rect(tx, ty, 2, 2, 'ink', 0, flat=True)
            scribble(cv, tx + 4, ty + 2, 16, 'ink', 1, int(rng.integers(0, 9999)), xh=1.2, slant=0.1)
    cv.put(edge(green) & mapm, 0, 0, 'green', 2, flat=True)
    inset = cv.full(cv.rect(24, 26, 42, 30, 'paper', 6.4))
    cv.put(edge(inset), 0, 0, 'ink', 1, flat=True)
    cv.rect(30, 32, 14, 9, 'paper', 4.2)
    cv.rect(48, 34, 10, 6, 'paper', 4.2)
    for ox in range(30, 62, 4):
        for oy in (46, 50):
            cv.px(ox, oy, 'green', 3)
    cv.text(45, 51, '1:500', 'ink', 1, align='center')
    leg = cv.full(cv.rect(116, 112, 108, 20, 'paper', 6.4))
    cv.put(edge(leg), 0, 0, 'ink', 1, flat=True)
    cv.rect(119, 115, 6, 5, 'green', 4.6)
    cv.text(128, 115, 'SIEDLUNGSGEBIET', 'ink', 0)
    cv.rect(119, 123, 6, 5, 'paper', 3.6)
    cv.text(128, 123, 'FREIZUMACHENDE FLÄCHE', 'ink', 0)
    cv.adjust(-np.clip(1 - np.abs(xx - 120) / 14.0, 0, 1) ** 2 * 2.0, pages)
    cv.spot(210, 0, 200, 1.0)
    cv.vignette(1.3)


def s_lib_shelf_4(cv: Canvas, hist=False):
    wood_planks(cv, 0, 0, W, H, 1.6, plank=12, seed=3)
    folder = cv.full(cv.rect(10, 8, 220, 136, 'steel', 3.2))
    cv.bevel(folder, 1.0, 1.0)
    cv.noise(8, 0.4, folder, seed_add=2)
    cv.shadow(folder, 4, 4, 1.6)
    paper_sheet(cv, 18, 14, 204, 124, 6.0, seed=5, age=0.35)
    cv.text(26, 18, 'BETTENHAUS II', 'blue', 1)
    cv.text(214, 18, 'UMBAU 1940', 'blue', 1, align='right')
    wall_m = np.zeros((H, W), bool)
    wall_m[30:32, 28:212] = True; wall_m[104:106, 28:212] = True
    wall_m[30:106, 28:30] = True; wall_m[30:106, 210:212] = True
    wall_m[66:68, 28:212] = True
    for dx_ in (60, 120, 180):
        wall_m[66:68, dx_:dx_ + 8] = False
    cv.put(wall_m, 0, 0, 'blue', 1, flat=True)
    for row_y in (36, 86):
        for k in range(10):
            bx = 34 + k * 17
            cv.put(edge(np.ones((12, 7), bool)), bx, row_y, 'blue', 2, flat=True)
            cv.px(bx + 3, row_y + 2, 'blue', 3)
    for k in range(8):
        cv.line(36 + k * 22, 31, 44 + k * 22, 31, 'paper', 6)
    cv.line(28, 112, 212, 112, 'blue', 3)
    cv.text(120, 115, '80 BETTEN', 'blue', 2, align='center')
    cv.polyline([(34, 40), (206, 100)], 'red', 3, width=2)
    cv.polyline([(206, 40), (34, 100)], 'red', 3, width=2)
    w_ = text_w('ENTFÄLLT', '57', 1, 2)
    cv.rect(120 - w_ // 2 - 3, 56, w_ + 6, 20, 'paper', 6.0)
    cv.text(120, 59, 'ENTFÄLLT', 'red', 3, font='57', scale=2, align='center')
    cv.spot(30, 0, 200, 1.0)
    cv.vignette(1.3)


def s_lib_shelf_5(cv: Canvas, hist=False):
    xx = XX
    wood_planks(cv, 0, 0, W, H, 1.8, plank=11, seed=5)
    left, right = open_book(cv, 14, 10, 212, 128, tone=6.2, seed=6)
    cv.shadow(left | right, 4, 4, 1.6)
    ph = cv.full(cv.rect(24, 20, 88, 70, 'sepia', 6.0))
    cv.grad(24, 20, 88, 40, 'sepia', 8.0, 6.4)
    cv.rect(40, 30, 54, 30, 'sepia', 4.2)
    for k in range(42, 94, 6):
        cv.line(k, 30, k, 60, 'sepia', 3.0, flat=False)
    cv.rect(24, 60, 88, 30, 'sepia', 5.0)
    for (x_, s, tone) in ((52, 1.2, 2.4), (70, 1.1, 9.0)):
        cv.ellipse(x_, 62, 3 * s, 3.5 * s, 'sepia', 7.0)
        cv.rect(x_ - 6 * s, 66, 12 * s, 24, 'sepia', tone)
        cv.rect(x_ - 4 * s, 57, 8 * s, 2, 'sepia', 10.4 if tone > 5 else 2.0)
    cv.rect(106, 64, 6, 26, 'sepia', 3.4)
    cv.ellipse(110, 60, 3, 3.5, 'sepia', 5.6)
    cv.put(cv.full((np.ones((70, 2), bool), 112, 20)), 0, 0, 'paper', 6.2)
    cv.grain(0.4, ph, seed_add=3)
    cv.text(68, 94, 'RICHTFEST 1959', 'ink', 1, align='center')
    for i in range(4):
        typed_line(cv, 24, 104 + i * 6, 88, 'ink', 1, 800 + i, h=2)
    cv.text(172, 20, 'ANHANG', 'ink', 1, align='center')
    cv.text(172, 28, 'HERKUNFT DER WERKSTOFFE', 'ink', 0, align='center')
    cv.line(128, 35, 216, 35, 'ink', 1)
    cv.text(130, 40, 'GRANIT', 'ink', 0)
    for name, y_ in [('FLOSSENBÜRG', 52), ('MAUTHAUSEN', 60), ('GROSS-ROSEN', 68)]:
        cv.text(132, y_, name, 'ink', 0)
        for dx_ in range(180, 204, 2):
            cv.px(dx_, y_ + 4, 'ink', 1)
        cv.text(214, y_, 'T', 'ink', 1, align='right')
    cv.text(130, 80, 'KALKSTEIN', 'ink', 0)
    typed_line(cv, 132, 90, 70, 'ink', 1, 900, h=1)
    typed_line(cv, 132, 96, 60, 'ink', 1, 901, h=1)
    cv.text(130, 106, 'ZIEGEL', 'ink', 0)
    typed_line(cv, 132, 116, 72, 'ink', 1, 902, h=1)
    typed_line(cv, 132, 122, 50, 'ink', 1, 903, h=1)
    cv.adjust(-np.clip(1 - np.abs(xx - 120) / 14.0, 0, 1) ** 2 * 2.0, left | right)
    cv.spot(200, 0, 190, 1.1)
    cv.vignette(1.3)


def s_lib_hidden(cv: Canvas, hist=False):
    xx = XX
    cv.rect(0, 0, W, H, 'wood', 1.4)
    cv.rect(0, 0, W, 10, 'wood', 3.6)
    cv.rect(0, 10, W, 2, 'wood', 0.6)
    cv.rect(0, 132, W, 18, 'wood', 3.4)
    cv.rect(0, 132, W, 1, 'wood', 5.6)
    x_ = 4
    rng = np.random.default_rng(cv.seed)
    while x_ < 70:
        bw = int(rng.integers(9, 14))
        top = 30 + int(rng.integers(0, 8))
        ramp = ['steel', 'red', 'wood'][int(rng.integers(0, 3))]
        b = cv.full(cv.rect(x_, top, bw, 132 - top, ramp, 2.4 + rng.uniform(0, 0.8)))
        cv.adjust(np.clip((x_ + bw / 2 - xx) * 0.2, -0.7, 0.7), b)
        x_ += bw + 1
    cv.poly([(76, 14), (232, 14), (232, 132), (76, 132)], 'wood', 2.2)
    cav = cv.full(cv.poly([(92, 22), (222, 30), (222, 126), (92, 128)], 'room', 0.6))
    tilt = cv.full(cv.poly([(76, 14), (92, 22), (92, 128), (76, 132)], 'wood', 3.4))
    cv.bevel(tilt, 1.4, 0.8)
    env = paper_sheet(cv, 104, 70, 70, 44, 4.8, seed=3, age=0.4)
    cv.polyline([(104, 70), (139, 92), (173, 70)], 'paper', 3.2)
    card = paper_sheet(cv, 118, 34, 112, 66, 6.2, seed=4, age=0.25)
    for ly in range(46, 98, 8):
        cv.line(120, ly, 228, ly, 'blue', 4)
    cv.line(130, 36, 130, 98, 'red', 3)
    for i, s in enumerate(['K. - FALLS DU SUCHST:', 'SIE ZÄHLEN ADRESSEN.', 'ICH HABE GEFRAGT, WO.', 'GIESS MEINEN KAKTUS.', 'W.B. 3/64']):
        cv.text(134, 39 + i * 8 + (i % 2), s, 'graphite', 0)
    cv.shadow(card, 3, 3, 1.6, env | cav)
    cv.shadow(env, 2, 3, 1.2, cav)
    cv.spot(170, 70, 80, 1.6, card | env)
    cv.spot(20, 0, 120, 0.8)
    cv.vignette(1.4)


def s_master_plan(cv: Canvas, hist=False):
    yy, xx = YY, XX
    cv.rect(0, 0, W, H, 'wood', 2.2)
    cv.noise(4, 0.5, None, seed_add=1)
    inner = cv.full(cv.rect(8, 7, W - 16, H - 14, 'paper', 5.4))
    cv.put(edge(dilate(inner, 1)) & ~inner, 0, 0, 'wood', 0.8)
    cv.grain(0.25, inner, seed_add=2)
    for gx_ in range(16, W - 8, 16):
        cv.line(gx_, 8, gx_, H - 8, 'blue', 5, dash=(1, 3))
    for gy_ in range(15, H - 8, 16):
        cv.line(9, gy_, W - 9, gy_, 'blue', 5, dash=(1, 3))
    rng = np.random.default_rng(cv.seed)
    for _ in range(26):
        bx, by = int(rng.integers(12, 220)), int(rng.integers(10, 132))
        if abs(bx - 128) < 16 or (bx > 150 and 52 < by < 92) or (bx < 100 and by > 96):
            continue
        bw, bh = int(rng.integers(10, 24)), int(rng.integers(8, 18))
        sk = rng.uniform(-3, 3)
        m = cv.full(cv.poly([(bx, by), (bx + bw, by + sk), (bx + bw, by + bh + sk), (bx, by + bh)], 'paper', 4.8)) & inner
        cv.put(m & ((xx + yy) % 3 == 0), 0, 0, 'blue', 4, flat=True)
        cv.put(edge(m), 0, 0, 'blue', 2, flat=True)
    river = [(8 + i / 60 * 224, 44 + math.sin(i / 60 * 6.0) * 7 + i / 60 * 6) for i in range(61)]
    rm = cv.polyline(river, 'blue', 3, flat=True, width=4)
    cv.put(rm & inner, 0, 0, 'blue', 3.2)
    park = cv.full(cv.ellipse(52, 96, 22, 14, 'green', 4.8)) & inner
    cv.adjust(np.where((xx + yy) % 2 == 0, 0.5, -0.5), park)
    cv.put(edge(park), 0, 0, 'green', 2, flat=True)
    tf = cv.full(cv.ellipse(196, 116, 26, 14, 'green', 5.0)) & inner
    cv.put(edge(tf), 0, 0, 'green', 2, flat=True)
    cv.rect(118, 8, 20, H - 16, 'paper', 6.2)
    cv.line(118, 8, 118, H - 9, 'blue', 1)
    cv.line(137, 8, 137, H - 9, 'blue', 1)
    for ty in range(12, H - 10, 4):
        cv.px(121, ty, 'green', 3); cv.px(134, ty, 'green', 3)
    hall = cv.full(cv.rect(108, 12, 40, 34, 'paper', 6.0))
    cv.put(edge(hall), 0, 0, 'blue', 1, flat=True)
    dome = cv.full(cv.ellipse(128, 29, 14, 14, 'blue', 4.2))
    cv.put(edge(dome), 0, 0, 'blue', 0, flat=True)
    for a in range(0, 360, 30):
        cv.line(128, 29, 128 + math.cos(math.radians(a)) * 13, 29 + math.sin(math.radians(a)) * 13, 'blue', 2)
    arch = cv.full(cv.rect(116, 98, 24, 10, 'blue', 4.0))
    cv.put(edge(arch), 0, 0, 'blue', 0, flat=True)
    cv.rect(124, 98, 8, 10, 'paper', 6.2)
    pc = [(172 + math.cos(i / 40 * 2 * math.pi * 1.08) * (10 + i * 0.05), 96 + math.sin(i / 40 * 2 * math.pi * 1.08) * (8 + i * 0.04)) for i in range(41)]
    cv.polyline(pc, 'graphite', 0)
    cv.rect(170, 94, 4, 4, 'graphite', 1, flat=True)
    cv.polyline([(182, 90), (196, 80), (204, 79)], 'graphite', 1)
    cv.rect(184, 66, 48, 20, 'paper', 5.6)
    cv.text(186, 68, 'PROBEKÖRPER', 'graphite', 0)
    cv.text(186, 74, '1941', 'graphite', 0)
    cv.text(186, 80, 'SETZUNG X3', 'graphite', 0)
    tb = cv.full(cv.rect(12, 108, 96, 34, 'paper', 6.2))
    cv.put(edge(tb), 0, 0, 'ink', 1, flat=True)
    cv.line(12, 118, 107, 118, 'ink', 1)
    cv.text(15, 111, 'GENERALPLAN', 'ink', 0)
    cv.text(15, 121, 'NORD-SÜD-ACHSE', 'ink', 0)
    cv.text(15, 129, 'M 1:5000', 'ink', 1)
    cv.text(15, 135, 'BLATT 3', 'ink', 1)
    sc = (93, 125)
    ring_o = cv.full(ellipse_mask(sc[0], sc[1], 13.0, 13.0))
    ring_i = cv.full(ellipse_mask(sc[0], sc[1], 11.6, 11.6))
    inner_r = cv.full(ellipse_mask(sc[0], sc[1], 9.6, 9.6))
    cv.put(ring_o & ~ring_i & ((xx * 5 + yy * 3) % 9 != 0), 0, 0, 'blue', 1, flat=True)
    cv.put(ring_i & ~inner_r & ((xx + yy * 2) % 3 == 0), 0, 0, 'blue', 2, flat=True)
    cv.put(inner_r, 0, 0, 'paper', 6.2)
    if hist:
        eg = eagle_mask(15)
        cv.put(eg, sc[0] - 7, sc[1] - 8, 'blue', 1, flat=True)
        cv.put(hakenkreuz(7), sc[0] - 3, sc[1] + 1, 'blue', 1, flat=True)
    else:
        disc, pillar = reichssiegel(13)
        cv.put(disc & ~pillar, sc[0] - 6, sc[1] - 6, 'blue', 1, flat=True)
    cv.adjust(0.8, inner & (np.abs((xx - 40) + (yy - 10) * 1.2) < 9))
    cv.adjust(0.9, inner & (np.abs((xx - 70) + (yy - 10) * 1.2) < 2))
    cv.spot(220, 30, 160, 0.9)
    cv.vignette(1.2)


def s_poster_aufbau(cv: Canvas, hist=False):
    """The 1964 poster as it hangs in the office (same design as berlin-env's wall decal): the Great Hall as a
    cream line drawing on night blue, the state emblem above the dome, the figures below."""
    yy, xx = YY, XX
    wall(cv, 4.4)
    cv.linear(1.2, -0.6)
    px0, py0, pw, ph = 62, 4, 116, 142
    poster = cv.full(cv.rect(px0, py0, pw, ph, 'paper', 6.0))
    cv.grain(0.2, poster, seed_add=2)
    cv.shadow(poster, 3, 3, 1.4)
    field = cv.full(cv.rect(px0 + 4, py0 + 4, pw - 8, 106, 'room', 2.2))
    cv.adjust(np.clip((yy - py0) * 0.012, 0, 1.2), field)
    cv.noise(10, 0.25, field, seed_add=7)
    LN = ('paper', 6.6)
    # dome elevation: outline, meridian ribs, lantern, drum with windows, colonnade with entablature
    cx, base = 120, py0 + 86
    rx, ry = 40, 36
    arc = []
    for i in range(0, 61):
        a = math.pi - i / 60 * math.pi
        arc.append((cx + math.cos(a) * rx, base - math.sin(a) * ry))
    cv.polyline(arc, *LN)
    for k in (-3, -2, -1, 1, 2, 3):
        rib = []
        f = k / 4.0
        for i in range(0, 31):
            t = i / 30
            ang = t * math.pi / 2
            x_ = cx + f * rx * math.cos(ang)
            y_ = base - ry * math.sin(ang)
            rib.append((x_, y_))
        cv.polyline(rib, 'paper', 5.0)
    cv.line(cx, base - ry, cx, base, 'paper', 5.0)
    cv.rect(cx - 5, base - ry - 8, 11, 8, 'room', 2.2)
    cv.put(edge(cv.full((np.ones((8, 11), bool), cx - 5, base - ry - 8))), 0, 0, *LN, flat=True)
    cv.line(cx, base - ry - 12, cx, base - ry - 8, *LN)
    cv.line(px0 + 14, base, px0 + pw - 14, base, *LN)
    cv.line(px0 + 14, base + 2, px0 + pw - 14, base + 2, 'paper', 5.0)
    for x_ in range(px0 + 16, px0 + pw - 14, 6):
        cv.line(x_, base + 3, x_, base + 16, *LN)
    cv.line(px0 + 12, base + 17, px0 + pw - 12, base + 17, *LN)
    cv.line(px0 + 10, base + 19, px0 + pw - 10, base + 19, 'paper', 5.0)
    # state emblem above the dome: neutral = the fictional Reichssiegel, historical = eagle and wreathed swastika
    ey = py0 + 12
    if hist:
        eg = eagle_mask(31, claws=True)
        cv.put(eg, cx - eg.shape[1] // 2, ey - 6, 'paper', 6.6, flat=True)
        wo = cv.full(ellipse_mask(cx, ey + 18.5, 5.6, 5.6))
        wi = cv.full(ellipse_mask(cx, ey + 18.5, 4.5, 4.5))
        cv.put(wo & ~wi, 0, 0, 'paper', 6.6, flat=True)
        cv.put(wi, 0, 0, 'paper', 7.4, flat=True)
        cv.put(hakenkreuz(7), cx - 3, ey + 15, 'ink', 0, flat=True)
    else:
        d_, p_ = reichssiegel(21)
        cv.put(d_, cx - 10, ey - 4, 'ink', 0, flat=True)
        cv.put(p_, cx - 10, ey - 4, 'paper', 6.6, flat=True)
        cv.put(edge(d_), cx - 10, ey - 4, 'paper', 5.0, flat=True)
    # the band with the year and the figures
    cv.text(cx, py0 + 114, 'AUFBAU 1964', 'room', 1, font='57', align='center')
    cv.line(px0 + 14, py0 + 124, px0 + pw - 14, py0 + 124, 'room', 3)
    cv.text(cx, py0 + 128, '290 M · 250 M', 'room', 2, align='center')
    cv.text(cx, py0 + 135, '180000 PLÄTZE', 'room', 2, align='center')
    for (tx, ty) in ((px0 + 2, py0 + 2), (px0 + pw - 4, py0 + 2), (px0 + 2, py0 + ph - 4)):
        tack(cv, tx, ty, 'brass')
    cv.poly([(px0 + pw - 14, py0 + ph), (px0 + pw, py0 + ph - 14), (px0 + pw, py0 + ph)], 'room', 4.4)
    back = cv.full(cv.poly([(px0 + pw - 14, py0 + ph), (px0 + pw, py0 + ph - 14), (px0 + pw - 10, py0 + ph - 10)], 'paper', 4.2))
    cv.bevel(back, 0.8, 0.6)
    cv.spot(40, 0, 220, 1.0)
    cv.vignette(1.3)


SCENES = {
    'master_plan': (s_master_plan, True),
    'notice': (s_notice, False),
    'pneumatic_tube': (s_pneumatic_tube, False),
    'clock': (s_clock, False),
    'card_catalogue': (s_card_catalogue, False),
    'reading_table': (s_reading_table, False),
    'globe': (s_globe, False),
    'lib_shelf_1': (s_lib_shelf_1, False),
    'lib_shelf_2': (s_lib_shelf_2, False),
    'lib_shelf_3': (s_lib_shelf_3, False),
    'lib_shelf_4': (s_lib_shelf_4, False),
    'lib_shelf_5': (s_lib_shelf_5, False),
    'lib_hidden': (s_lib_hidden, False),
    'mouse': (s_mouse, False),
    'radio': (s_radio, False),
    'poster_aufbau': (s_poster_aufbau, True),
    'heater': (s_heater, False),
    'pigeons': (s_pigeons, False),
    'photo': (s_photo, False),
    'coat_stand': (s_coat_stand, False),
}


def render(name: str, hist: bool = False) -> np.ndarray:
    cv = Canvas(name)
    SCENES[name][0](cv, hist)
    return cv.render()


def palette_problems(arr: np.ndarray) -> list[str]:
    cols = {('#%02X%02X%02X' % tuple(c[:3])) for c in arr.reshape(-1, 4)}
    return sorted(c for c in cols if c not in ALLOWED)


def main(argv: list[str]) -> int:
    preview = None
    only = []
    i = 0
    while i < len(argv):
        if argv[i] == '--preview' and i + 1 < len(argv):
            preview = argv[i + 1]; i += 2; continue
        only.append(argv[i]); i += 1
    os.makedirs(OUT, exist_ok=True)
    shots = []
    for name, (fn, has_hist) in SCENES.items():
        if only and name not in only:
            continue
        for hist, fname in [(False, name)] + ([(True, name + '_hist')] if has_hist else []):
            arr = render(name, hist)
            bad = palette_problems(arr)
            if bad:
                print('PALETTE', fname, bad[:6])
            Image.fromarray(arr, 'RGBA').save(os.path.join(OUT, fname + '.png'))
            shots.append((fname, arr))
            print('wrote', fname, arr.shape[1], 'x', arr.shape[0])
    if preview:
        os.makedirs(preview, exist_ok=True)
        cols = 2
        rows = (len(shots) + cols - 1) // cols
        sheet = Image.new('RGBA', (cols * (W * 2 + 8), rows * (H * 2 + 8)), (10, 10, 12, 255))
        for k, (fname, arr) in enumerate(shots):
            im = Image.fromarray(arr, 'RGBA')
            sheet.paste(im.resize((W * 2, H * 2), Image.NEAREST), ((k % cols) * (W * 2 + 8), (k // cols) * (H * 2 + 8)))
            im.resize((W * 3, H * 3), Image.NEAREST).save(os.path.join(preview, fname + '_x3.png'))
        sheet.save(os.path.join(preview, 'contact_sheet.png'))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
