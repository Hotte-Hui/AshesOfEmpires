"""env_veltrava_cine_kit -- small shared helpers for the Chapter-3 cinematic art (owner: cinematics stream).

Used by env_veltrava_cine.py (trains), env_veltrava_cine_tohall.py, env_veltrava_cine_close.py and
env_veltrava_cine_figs.py.  Pure numpy, deterministic, no image inputs.
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
import env_veltrava_lib as vlib  # noqa: E402  (registers the 'veltrava' palette, trilingual fonts)


def vtext(s: str, font: str = 's', spacing: int = 1) -> np.ndarray:
    """Bool mask of pixel text in the Veltrava fonts (Latin with accents, Cyrillic, digits)."""
    w = max(1, vlib.text_width(s, font, spacing))
    gh = 5 if font == 's' else 7
    m = np.zeros((gh + 3, w + 2), bool)         # +2 rows above for accents, +1 below for cedillas
    cx = 1
    for ch in s:
        if ch == ' ':
            cx += 2 if font == 's' else 3
            continue
        g, acc = vlib._glyph(ch, font)
        if g is None:
            cx += 4
            continue
        for r, row in enumerate(g):
            for c, v in enumerate(row):
                if v == '#':
                    m[r + 2, cx + c] = True
        if acc is not None:
            kind, row = acc
            ay = len(g) + 2 if kind == 'ced' else 0
            for c, v in enumerate(row):
                if v == '#':
                    m[ay, cx + c] = True
        cx += len(g[0]) + spacing
    return m


def place(small: np.ndarray, w: int, h: int, x: int, y: int) -> np.ndarray:
    """Full-size (h, w) mask with `small` pasted at (x, y) (clipped)."""
    out = np.zeros((h, w), bool)
    sh, sw = small.shape
    X0, Y0 = max(0, x), max(0, y)
    X1, Y1 = min(w, x + sw), min(h, y + sh)
    if X1 > X0 and Y1 > Y0:
        out[Y0:Y1, X0:X1] = small[Y0 - y:Y1 - y, X0 - x:X1 - x]
    return out


def text_at(s: str, w: int, h: int, x: int, y: int, font: str = 's', spacing: int = 1, center: bool = False):
    """Mask of text whose glyph top row lands on row y (accent rows above it)."""
    m = vtext(s, font, spacing)
    if center:
        x = int(round(x - (m.shape[1] - 2) / 2))
    return place(m, w, h, x - 1, y - 2)


def ring(yy, xx, cx, cy, r0, r1):
    d = np.hypot(xx + 0.5 - cx, yy + 0.5 - cy)
    return (d >= r0) & (d < r1)


def disc(yy, xx, cx, cy, r):
    return np.hypot(xx + 0.5 - cx, yy + 0.5 - cy) < r


def polar(yy, xx, cx, cy):
    """(radius, clock angle in degrees: 0 = 12 o'clock, clockwise)."""
    dx = xx + 0.5 - cx
    dy = yy + 0.5 - cy
    r = np.hypot(dx, dy)
    a = (np.degrees(np.arctan2(dx, -dy)) + 360.0) % 360.0
    return r, a


def clock_indices(yy, xx, cx, cy, r_out, hour_len, min_len, hour_w=2.6, min_w=1.0):
    """Masks of the 12 hour bars and 48 minute bars of a railway dial (same angles in every clock)."""
    r, a = polar(yy, xx, cx, cy)
    hours = np.zeros(yy.shape, bool)
    mins = np.zeros(yy.shape, bool)
    for k in range(60):
        ang = math.radians(k * 6.0)
        ux, uy = math.sin(ang), -math.cos(ang)
        dx = xx + 0.5 - cx
        dy = yy + 0.5 - cy
        along = dx * ux + dy * uy
        across = np.abs(-dx * uy + dy * ux)
        if k % 5 == 0:
            hours |= (along > r_out - hour_len) & (along <= r_out) & (across <= hour_w / 2)
        else:
            mins |= (along > r_out - min_len) & (along <= r_out) & (across <= min_w / 2 + 0.05)
    return hours, mins


def soft_quant(a: np.ndarray, step: float = 8.0, ox: int = 0, oy: int = 0) -> np.ndarray:
    """Additive RGB float image -> RGBA uint8 quantised in `step` levels with ordered dither."""
    h, w = a.shape[:2]
    q = np.floor(a / step + pg.bayer(w, h, ox, oy)[..., None]) * step
    out = np.zeros((h, w, 4), np.uint8)
    out[..., :3] = np.clip(q, 0, 255).astype(np.uint8)
    out[..., 3] = np.where(out[..., :3].max(-1) > 0, 255, 0)
    return out


def puff_sheet(n, fw, fh, cols, seed, grow=(0.30, 0.48), thin=0.55, light=(0.5, -0.6), drift=0.0, block=1):
    """n frames of a soft steam/smoke puff (dithered density, lit from `light`), RGBA sheet n*fw x fh."""
    sheet = np.zeros((fh, fw * n, 4), np.uint8)
    yy, xx = np.mgrid[0:fh, 0:fw].astype(np.float32)
    cols = [pg.hx(c) for c in cols]
    for i in range(n):
        u = i / max(1, n - 1)
        rx = fw * (grow[0] + (grow[1] - grow[0]) * u)
        ry = fh * (grow[0] + (grow[1] - grow[0]) * u) * 0.9
        cx = fw / 2 + drift * u * fw
        cy = fh / 2 + 0.06 * fh * (1 - u)
        nz = pg.value_noise(fw, fh, max(3, fw / 9), seed + i * 17, octaves=3)
        lobes = np.zeros((fh, fw), np.float32)
        rng = np.random.default_rng(seed + 101 * i)
        for _ in range(7):
            ox, oy = rng.uniform(-0.55, 0.55) * rx, rng.uniform(-0.45, 0.45) * ry
            rr = rng.uniform(0.45, 0.75)
            d = np.hypot((xx + 0.5 - cx - ox) / (rx * rr), (yy + 0.5 - cy - oy) / (ry * rr))
            lobes = np.maximum(lobes, np.clip(1 - d, 0, 1))
        dens = np.clip(lobes ** 0.8 + (nz - 0.5) * 0.55, 0, 1) * (1.0 - thin * u)
        th = pg.bayer(fw, fh, i * 3, i * 5) if block <= 1 else \
            np.repeat(np.repeat(pg.bayer((fw + 1) // 2, (fh + 1) // 2, i, i * 2), 2, 0), 2, 1)[:fh, :fw]
        m = (dens > th * 0.85) & (dens > 0.10)
        lx, ly = light
        lit = np.clip(((xx - cx) / rx * lx + (yy - cy) / ry * ly) * 0.6 + 0.5 + (nz - 0.5) * 0.4, 0, 1)
        idx = np.clip((lit * (len(cols) - 0.6) + dens * 0.8 - 0.4).round().astype(int), 0, len(cols) - 1)
        for ci in range(len(cols)):
            sel = m & (idx == ci)
            sheet[:, i * fw:(i + 1) * fw][sel] = cols[ci]
    return sheet
