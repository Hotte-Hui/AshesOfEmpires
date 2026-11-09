"""env_flashback_kit -- painting kit of the flashback films of the real-history cards (TECHNICAL_ARCHITECTURE 12.15).

Every plate is painted as ONE luminance field (0 = black, 1 = paper white) with numpy masks and then resolved to a
fixed 13-step sepia ramp: a 4x4 ordered dither that only works in the middle of a ramp step (flat clusters
elsewhere), a lens falloff toward the corners and a little baked grain -- archive film that stays pixel art: hard
pixels, no blur, no smooth gradients.  Two muted accent colours exist for one fact only (the yellow and the red
lamp of the Nuremberg interpreters).  People appear at a distance or from behind, as two- or three-tone silhouettes.
Original and deterministic (fixed seeds); no downloads, no traced references.
Read-only imports: pg, env_prologue_kit (masks, value noise, the pixel fonts of the project with umlauts and Cyrillic).
"""
from __future__ import annotations

import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import pg  # noqa: E402
import env_prologue_kit as PK  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(HERE))
OUT = os.path.join(ROOT, 'assets', 'cinematics', 'flashback')
PW, PH = 512, 368            # every plate: the 480 x 360 gate plus room for the drift and the gate weave
GW, GH = 480, 360

RAMP_HEX = ['#120d0a', '#1d1510', '#2a1f17', '#39291e', '#493628', '#5b4533', '#6e5540', '#83674e',
            '#987b5f', '#ae9172', '#c4a888', '#d9c09f', '#ecd9b9']
RAMP = np.array([[int(h[1:3], 16), int(h[3:5], 16), int(h[5:7], 16)] for h in RAMP_HEX], np.float32)
ACCENT = {'yellow': ['#6b5320', '#b08a2c', '#dcb84a', '#f1dc8e'], 'red': ['#5e2319', '#9a3324', '#c94c35', '#eb9a7c']}
_B4 = np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]], np.float32)


def hexrgb(h: str) -> tuple:
    return int(h[1:3], 16), int(h[3:5], 16), int(h[5:7], 16)


def rng(seed: int) -> np.random.Generator:
    return np.random.default_rng(seed)


class Plate:
    """A luminance painting; masks are bool arrays of the size of the plate."""

    def __init__(self, w: int = PW, h: int = PH, v: float = 0.5):
        self.w, self.h = int(w), int(h)
        self.v = np.full((self.h, self.w), float(v), np.float32)
        yy, xx = np.mgrid[0:self.h, 0:self.w]
        self.yy, self.xx = yy.astype(np.float32), xx.astype(np.float32)

    # ---- masks
    def all(self):
        return np.ones((self.h, self.w), bool)

    def box(self, x0, y0, x1, y1):
        return PK.box(self.w, self.h, x0, y0, x1, y1)

    def ell(self, cx, cy, rx, ry):
        return PK.ell(self.w, self.h, cx, cy, rx, ry)

    def poly(self, pts):
        return PK.poly(self.w, self.h, pts)

    def line(self, pts, width=1):
        return PK.stroke(self.w, self.h, pts, width)

    def text(self, s, x, y, font='s', spacing=1, center=False):
        return PK.text(self.w, self.h, s, x, y, font, spacing, center)

    # ---- paint
    def _k(self, k, m):
        return k if np.isscalar(k) else np.clip(np.asarray(k, np.float32), 0.0, 1.0)[m]

    def fill(self, m, val):
        self.v[m] = val if np.isscalar(val) else np.asarray(val, np.float32)[m]

    def mix(self, m, val, k):
        kk = self._k(k, m)
        vv = val if np.isscalar(val) else np.asarray(val, np.float32)[m]
        self.v[m] = self.v[m] * (1.0 - kk) + vv * kk

    def shade(self, m, k):
        self.v[m] = self.v[m] * (1.0 - self._k(k, m))

    def lift(self, m, k):
        self.v[m] = self.v[m] + (1.0 - self.v[m]) * self._k(k, m)

    def vgrad(self, m, y0, v0, y1, v1):
        t = np.clip((self.yy - y0) / max(1e-6, float(y1 - y0)), 0.0, 1.0)
        self.v[m] = (v0 + (v1 - v0) * t)[m]

    def hgrad(self, m, x0, v0, x1, v1):
        t = np.clip((self.xx - x0) / max(1e-6, float(x1 - x0)), 0.0, 1.0)
        self.v[m] = (v0 + (v1 - v0) * t)[m]

    def tex(self, m, amp, cell, seed, sx=1.0, sy=1.0, octaves=3):
        """Value-noise texture of +-amp inside m; sx / sy > 1 stretch it into streaks."""
        if sy > 1.0:
            n = PK.noise(self.h, self.w, cell, seed, octaves, sy).T
        else:
            n = PK.noise(self.w, self.h, cell, seed, octaves, sx)
        self.v[m] += ((n - 0.5) * 2.0 * amp)[m]

    def glow(self, cx, cy, rx, ry, k, power=1.5, m=None):
        d = np.sqrt(((self.xx - cx) / rx) ** 2 + ((self.yy - cy) / ry) ** 2)
        f = np.clip(1.0 - d, 0.0, 1.0) ** power * k
        if m is not None:
            f = f * m
        self.v = self.v + (1.0 - self.v) * f

    def dusk(self, cx, cy, rx, ry, k, power=1.5):
        """Darkens away from (cx, cy): nothing inside the ellipse, k far outside."""
        d = np.sqrt(((self.xx - cx) / rx) ** 2 + ((self.yy - cy) / ry) ** 2)
        self.v = self.v * (1.0 - np.clip(d - 1.0, 0.0, 1.0) ** power * k)


def resolve(p: Plate, seed: int = 0, vignette: float = 0.34, grain: float = 0.012, blotch: float = 0.02,
            band: float = 1.9, accents=()) -> np.ndarray:
    """Luminance -> the sepia ramp (RGBA uint8).  accents = [(mask, '#rrggbb')] painted over the result."""
    v = p.v.copy()
    cx, cy = (p.w - 1) / 2.0, (p.h - 1) / 2.0
    d = np.sqrt(((p.xx - cx) / (p.w * 0.60)) ** 2 + ((p.yy - cy) / (p.h * 0.60)) ** 2)
    v *= 1.0 - vignette * np.clip(d - 0.45, 0.0, 1.0) ** 1.4 * 1.7      # the lens falls off toward the corners
    v += (PK.noise(p.w, p.h, 90, seed + 7, 2) - 0.5) * 2.0 * blotch       # uneven stock
    v += (pg.white_noise(p.w, p.h, seed + 13) - 0.5) * 2.0 * grain        # grain
    v = np.clip(v, 0.0, 1.0)
    n = len(RAMP) - 1
    f = v * n
    lo = np.floor(f).astype(np.int32)
    frac = np.clip((f - lo - 0.5) * band + 0.5, 0.0, 1.0)
    thr = (np.tile(_B4, (p.h // 4 + 1, p.w // 4 + 1))[:p.h, :p.w] + 0.5) / 16.0
    idx = np.clip(lo + (frac > thr), 0, n)
    out = np.zeros((p.h, p.w, 4), np.uint8)
    out[..., :3] = RAMP[idx].astype(np.uint8)
    out[..., 3] = 255
    out = PK._clean_orphans(out)
    for m, col in accents:
        out[m, :3] = np.array(hexrgb(col), np.uint8)
    return out


# ------------------------------------------------------------------------------------------------ small things
def greek(p: Plate, x0, y0, x1, n, pitch=4, seed=0, val=0.3, indent=0, slope=0.0, thick=1):
    """Typed lines nobody can read: word-long dashes with gaps, ragged right (slope = dy per px on a slanted sheet)."""
    r = rng(seed)
    for i in range(n):
        x = x0 + (indent if i == 0 else 0)
        end = x1 - int(r.integers(4, max(6, (x1 - x0) // 3))) if (i == n - 1 or r.random() < 0.22) else x1
        while x < end:
            wl = int(r.integers(2, 8))
            xe = min(end, x + wl)
            y = y0 + i * pitch + slope * (x - x0)
            p.fill(p.box(x, y, xe, y + thick), val)
            x = xe + int(r.integers(1, 3))


def smoke(p: Plate, x, y, length, rise, val, seed=0, k=0.55, grow=3.2):
    """A thin plume in small hard puffs; length < 0 drifts to the left."""
    r = rng(seed)
    n = max(4, int(abs(length) / 3))
    for i in range(n):
        u = i / (n - 1)
        px = x + length * u
        py = y - rise * (u ** 0.6) + float(r.normal(0, 0.6))
        rad = 1.0 + grow * u
        p.mix(p.ell(px, py, rad * 1.5, rad), val, k * (1.0 - u * 0.75))


def wheel(p: Plate, cx, cy, r, val=0.14, spokes=8):
    p.fill(p.ell(cx, cy, r, r) & ~p.ell(cx, cy, r - 2.2, r - 2.2), val)
    for i in range(spokes // 2):
        a = math.pi * i / (spokes // 2)
        dx, dy = math.cos(a) * (r - 1), math.sin(a) * (r - 1)
        p.fill(p.line([(cx - dx, cy - dy), (cx + dx, cy + dy)]), val + 0.06)
    p.fill(p.ell(cx, cy, 2.2, 2.2), val)


def pole(p: Plate, x, yb, h, w=2, val=0.16, arm=0):
    p.fill(p.box(x, yb - h, x + w, yb), val)
    if arm:
        ay = yb - h + max(2, h // 12)
        p.fill(p.box(x - arm, ay, x + w + arm, ay + max(1, w // 2)), val)


def wire(p: Plate, x0, y0, x1, y1, sag, val=0.3):
    p.fill(p.line(pg.catenary(x0, y0, x1, y1, sag)), val)


def tufts(p: Plate, x0, x1, y0, y1, n, seed, val=0.22, hmax=9):
    r = rng(seed)
    for _ in range(n):
        x = float(r.uniform(x0, x1))
        y = float(r.uniform(y0, y1))
        k = (y - y0) / max(1.0, float(y1 - y0))
        h = 2 + hmax * (0.3 + 0.7 * k) * float(r.uniform(0.5, 1.0))
        for b in range(int(r.integers(2, 5))):
            dx = float(r.uniform(-3, 3))
            p.fill(p.line([(x + b - 1, y), (x + b - 1 + dx, y - h * float(r.uniform(0.6, 1.0)))]),
                   val + float(r.uniform(-0.04, 0.06)))


def patches(p: Plate, m, seed, cell=22, sx=3.0, levels=((0.60, 0.42, 0.75), (0.70, 0.30, 0.6))):
    """Bare ground showing through thin snow: thresholded noise, in hard patches."""
    n = PK.noise(p.w, p.h, cell, seed, 4, sx)
    for thr, val, k in levels:
        p.mix(m & (n > thr), val, k)


def tree_line(p: Plate, y, amp, seed, val, x0=0, x1=None, cell=14):
    """A far line of trees: a ragged dark band whose top follows 1-D noise, down to y."""
    x1 = p.w if x1 is None else x1
    n = PK.noise1d(p.w, cell, seed, 3)
    top = y - amp * (0.35 + 0.65 * n)
    m = (p.yy >= top[None, :]) & (p.yy < y) & (p.xx >= x0) & (p.xx < x1)
    p.fill(m, val)
    return m


# ------------------------------------------------------------------------------------------------ people
def figure_back(p: Plate, x, yf, h, coat=0.16, head=0.22, hat=None, scarf=None, legs=0.11, skirt=False, rim=0.0):
    """A standing person seen from behind, feet at (x, yf), h px tall: legs, coat, hanging arms, head."""
    w = h * 0.30
    hr = h * 0.085
    hy = yf - h
    sh = hy + hr * 2.3
    hem = yf - h * (0.20 if skirt else 0.42)
    p.shade(p.ell(x, yf, w * 0.8, max(1.5, h * 0.035)), 0.25)                     # contact shadow
    if skirt:
        p.fill(p.box(x - w * 0.28, hem, x - w * 0.05, yf) | p.box(x + w * 0.05, hem, x + w * 0.28, yf), legs)
    else:
        p.fill(p.box(x - w * 0.38, hem - 1, x - w * 0.04, yf) | p.box(x + w * 0.04, hem - 1, x + w * 0.38, yf), legs)
    body = p.poly([(x - w * 0.50, sh + 2), (x - w * 0.36, sh), (x + w * 0.36, sh), (x + w * 0.50, sh + 2),
                   (x + w * 0.58, hem), (x - w * 0.58, hem)])
    p.fill(body, coat)
    arms = (p.box(x - w * 0.64, sh + 2, x - w * 0.46, sh + h * 0.36)
            | p.box(x + w * 0.46, sh + 2, x + w * 0.64, sh + h * 0.36))
    p.fill(arms, max(0.0, coat - 0.05))
    p.fill(p.box(x - hr * 0.5, hy + hr * 1.6, x + hr * 0.5, sh + 1), max(0.0, head - 0.05))
    hm = p.ell(x, hy + hr, hr, hr * 1.12)
    p.fill(hm, head)
    if scarf is not None:
        sm = p.ell(x, hy + hr, hr * 1.2, hr * 1.25) | p.poly([(x - hr * 1.2, hy + hr), (x + hr * 1.2, hy + hr),
                                                              (x + hr * 1.0, sh + hr), (x - hr * 1.0, sh + hr)])
        p.fill(sm, scarf)
        hm = hm | sm
    if hat is not None:
        hm2 = p.box(x - hr * 1.2, hy - 1, x + hr * 1.2, hy + hr * 1.0)
        p.fill(hm2, hat)
        hm = hm | hm2
    if rim > 0:
        p.lift(PK.edge(body | hm | arms, -1, 0), rim)


def seated_back(p: Plate, x, y, r, coat=0.14, head=0.18, phones=0.64, chair=0.24):
    """Head and shoulders above a chair back, from behind; y = top of the head, r = head radius."""
    sh = y + r * 2.2
    p.fill(p.poly([(x - r * 2.3, sh + r * 0.9), (x - r * 1.5, sh), (x + r * 1.5, sh), (x + r * 2.3, sh + r * 0.9),
                   (x + r * 2.3, sh + r * 4.2), (x - r * 2.3, sh + r * 4.2)]), coat)
    if chair is not None:
        p.fill(p.box(x - r * 2.0, sh + r * 1.5, x + r * 2.0, sh + r * 4.4), chair)
        p.fill(p.box(x - r * 2.0, sh + r * 1.5, x + r * 2.0, sh + r * 1.5 + max(1, r * 0.22)), chair + 0.12)
    p.fill(p.box(x - r * 0.45, y + r * 1.6, x + r * 0.45, sh + 1), max(0.0, head - 0.04))
    p.fill(p.ell(x, y + r, r, r * 1.1), head)
    if phones is not None:
        t = max(1.0, r * 0.22)
        band = (p.ell(x, y + r * 0.95, r * 1.2, r * 1.25) & ~p.ell(x, y + r * 0.95, r * 1.2 - t, r * 1.25 - t)
                & (p.yy < y + r))
        p.fill(band, phones)
        p.fill(p.box(x - r * 1.4, y + r * 0.7, x - r * 0.92, y + r * 1.7)
               | p.box(x + r * 0.92, y + r * 0.7, x + r * 1.4, y + r * 1.7), 0.09)


def tiny_head(p: Plate, x, y, r, phones=True, body=0.13, head=0.18):
    """A listener far away: shoulders, a head, the headphone band as one light pixel line."""
    p.fill(p.box(x - r * 1.9, y + r * 2.0, x + r * 1.9, y + r * 4.5), body)
    p.fill(p.ell(x, y + r, r, r * 1.1), head)
    if phones:
        p.fill(p.line([(x - r, y + r * 0.6), (x - r * 0.6, y - 0.5), (x + r * 0.6, y - 0.5), (x + r, y + r * 0.6)]), 0.66)
        p.fill(p.box(x - r - 1, y + r * 0.6, x - r + 1, y + r * 1.5)
               | p.box(x + r - 1, y + r * 0.6, x + r + 1, y + r * 1.5), 0.08)
