"""env_prologue_kit -- shared helpers of the prologue art (env_prologue*.py, round 11).

Painting model: a shot is painted in float RGB (gradients, light falloff, value noise) on crisp masks (polygons,
ellipses, strokes -- never anti-aliased) and resolved ONCE into its own small palette (median cut of the painting)
with ordered Bayer dithering: flat colours stay flat clusters, only light and air dither.  Sprites (alpha) are
resolved the same way.  The two men are the game's own character sheets (assets/characters/<id>/sheet.png),
re-lit per shot, never redrawn.  Pure numpy + Pillow, fixed seeds: a re-run writes byte-identical files.
"""
from __future__ import annotations

import json
import math
import os
import sys

import numpy as np
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import pg  # noqa: E402
import env_veltrava_cine_kit as VK  # noqa: E402  (pixel fonts with umlauts and Cyrillic; read-only)

ROOT = os.path.dirname(os.path.dirname(HERE))
OUT = os.path.join(ROOT, 'assets', 'cinematics', 'prologue')
CHARS = os.path.join(ROOT, 'assets', 'characters')


def rgb(h) -> np.ndarray:
    if not isinstance(h, str):
        return np.asarray(h, np.float32)[:3]
    return np.array([int(h[1:3], 16), int(h[3:5], 16), int(h[5:7], 16)], np.float32)


def lerp(a, b, t):
    return a + (b - a) * t


# ------------------------------------------------------------------------------------------------ masks
def poly(w, h, pts) -> np.ndarray:
    img = Image.new('1', (w, h), 0)
    ImageDraw.Draw(img).polygon([(float(x), float(y)) for x, y in pts], fill=1)
    return np.array(img, bool)


def ell(w, h, cx, cy, rx, ry) -> np.ndarray:
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    return ((xx + 0.5 - cx) / max(rx, 0.5)) ** 2 + ((yy + 0.5 - cy) / max(ry, 0.5)) ** 2 <= 1.0


def box(w, h, x0, y0, x1, y1) -> np.ndarray:
    m = np.zeros((h, w), bool)
    X0, Y0, X1, Y1 = max(0, int(x0)), max(0, int(y0)), min(w, int(x1)), min(h, int(y1))
    if X1 > X0 and Y1 > Y0:
        m[Y0:Y1, X0:X1] = True
    return m


def stroke(w, h, pts, width=1) -> np.ndarray:
    img = Image.new('1', (w, h), 0)
    d = ImageDraw.Draw(img)
    pts = [(float(x), float(y)) for x, y in pts]
    if width <= 1:
        d.line(pts, fill=1, width=1)
    else:
        d.line(pts, fill=1, width=int(width), joint='curve')
    return np.array(img, bool)


def text(w, h, s, x, y, font='s', spacing=1, center=False) -> np.ndarray:
    return VK.text_at(s, w, h, int(x), int(y), font, spacing, center)


def text_width(s, font='s', spacing=1) -> int:
    return VK.vtext(s, font, spacing).shape[1] - 2


def big(m: np.ndarray, k: int) -> np.ndarray:
    return np.repeat(np.repeat(m, k, 0), k, 1)


def noise(w, h, cell, seed, octaves=4, sx=1.0) -> np.ndarray:
    """fBm value noise in [0, 1]; sx > 1 stretches it horizontally (wind streaks, cloud bands)."""
    if sx <= 1.0:
        return pg.value_noise(w, h, cell, seed, octaves)
    small = pg.value_noise(max(2, int(w / sx)), h, cell / sx, seed, octaves)
    return np.array(Image.fromarray(small).resize((w, h), Image.BILINEAR), np.float32)


def noise1d(w, cell, seed, octaves=3) -> np.ndarray:
    return pg.value_noise(w, 3, cell, seed, octaves)[1]


def blur(a: np.ndarray, r: int) -> np.ndarray:
    if r <= 0:
        return a.astype(np.float32)
    a = a.astype(np.float32)
    for axis in (0, 1):
        p = np.pad(a, [(r, r) if i == axis else (0, 0) for i in range(2)], mode='edge')
        c = np.cumsum(p, axis=axis, dtype=np.float64)
        c = np.concatenate([np.zeros_like(np.take(c, [0], axis=axis)), c], axis=axis)
        n = a.shape[axis]
        hi = np.take(c, np.arange(2 * r + 1, 2 * r + 1 + n), axis=axis)
        lo = np.take(c, np.arange(0, n), axis=axis)
        a = ((hi - lo) / (2 * r + 1)).astype(np.float32)
    return a


def edge(m: np.ndarray, dx: int, dy: int) -> np.ndarray:
    """Pixels of m whose neighbour at (dx, dy) is outside m (the lit / shadowed rim)."""
    s = np.zeros_like(m)
    H, W = m.shape
    ys, ye = max(0, -dy), H - max(0, dy)
    xs, xe = max(0, -dx), W - max(0, dx)
    s[ys:ye, xs:xe] = m[ys + dy:ye + dy, xs + dx:xe + dx]
    return m & ~s


# ------------------------------------------------------------------------------------------------ canvas
class Canvas:
    """Float RGB painting with an alpha coverage mask (sprites) in frame coordinates."""

    def __init__(self, w, h, opaque=True):
        self.w, self.h = int(w), int(h)
        self.c = np.zeros((self.h, self.w, 3), np.float32)
        self.a = np.full((self.h, self.w), bool(opaque))
        yy, xx = np.mgrid[0:self.h, 0:self.w]
        self.yy, self.xx = yy.astype(np.float32), xx.astype(np.float32)
        self.em = np.zeros((self.h, self.w), bool)   # never darkened by the ambient grade (lamps, windows)

    # masks in this canvas' size
    def poly(self, pts):
        return poly(self.w, self.h, pts)

    def ell(self, cx, cy, rx, ry):
        return ell(self.w, self.h, cx, cy, rx, ry)

    def box(self, x0, y0, x1, y1):
        return box(self.w, self.h, x0, y0, x1, y1)

    def stroke(self, pts, width=1):
        return stroke(self.w, self.h, pts, width)

    def text(self, s, x, y, font='s', spacing=1, center=False):
        return text(self.w, self.h, s, x, y, font, spacing, center)

    # paint
    def fill(self, m, col):
        self.c[m] = rgb(col)
        self.a |= m

    def mix(self, m, col, k):
        """Blend toward col by k (scalar or per-pixel field) inside m."""
        if np.isscalar(k):
            self.c[m] = self.c[m] * (1.0 - k) + rgb(col) * k
        else:
            kk = np.clip(np.asarray(k, np.float32), 0.0, 1.0)[m][:, None]
            self.c[m] = self.c[m] * (1.0 - kk) + rgb(col) * kk
        self.a |= m

    def vgrad(self, m, stops):
        """Vertical gradient through (y, colour) stops inside m."""
        ys = [float(s[0]) for s in stops]
        cols = np.stack([rgb(s[1]) for s in stops])
        rows = np.arange(self.h, dtype=np.float32)
        g = np.stack([np.interp(rows, ys, cols[:, i]) for i in range(3)], -1)
        self.c[m] = np.broadcast_to(g[:, None, :], (self.h, self.w, 3))[m]
        self.a |= m

    def hgrad(self, m, stops):
        xs = [float(s[0]) for s in stops]
        cols = np.stack([rgb(s[1]) for s in stops])
        cs = np.arange(self.w, dtype=np.float32)
        g = np.stack([np.interp(cs, xs, cols[:, i]) for i in range(3)], -1)
        self.c[m] = np.broadcast_to(g[None, :, :], (self.h, self.w, 3))[m]
        self.a |= m

    def falloff(self, cx, cy, rx, ry, power=1.6):
        d = np.sqrt(((self.xx - cx) / rx) ** 2 + ((self.yy - cy) / ry) ** 2)
        return np.clip(1.0 - d, 0.0, 1.0) ** power

    def glow(self, cx, cy, rx, ry, col, k, m=None, power=1.6):
        """Light pool: blend toward col by k * falloff (inside m when given)."""
        f = self.falloff(cx, cy, rx, ry, power) * k
        if m is not None:
            f = f * m
        self.c += (rgb(col)[None, None, :] - self.c) * f[..., None]

    def pool(self, cx, cy, rx, ry, col, ks=(0.10, 0.10, 0.12), m=None):
        """A pixel-art light pool: nested hard-edged ellipses (1, .68, .4 of the radii), each a step brighter,
        with a 2-px checker seam at every edge instead of a smooth gradient (no concentric dither rings)."""
        chk = ((self.xx.astype(int) + self.yy.astype(int)) % 2) == 0
        for i, k in enumerate(ks):
            s = (1.0, 0.68, 0.4)[min(i, 2)]
            d = np.sqrt(((self.xx + 0.5 - cx) / (rx * s)) ** 2 + ((self.yy + 0.5 - cy) / (ry * s)) ** 2)
            inside = (d <= 1.0 - 2.0 / max(rx * s, 1)) | ((d <= 1.0) & chk)
            if m is not None:
                inside &= m
            self.mix(inside, col, k)

    def shade(self, m, k):
        """Multiply by (1 - k) inside m (k scalar or field)."""
        if np.isscalar(k):
            self.c[m] *= (1.0 - k)
        else:
            self.c[m] *= (1.0 - np.clip(np.asarray(k, np.float32), 0, 1)[m])[:, None]

    def paste(self, sprite: np.ndarray, x: int, y: int):
        """Paste an RGBA uint8 array (alpha > 0 pixels) at (x, y)."""
        h, w = sprite.shape[:2]
        X0, Y0, X1, Y1 = max(0, x), max(0, y), min(self.w, x + w), min(self.h, y + h)
        if X1 <= X0 or Y1 <= Y0:
            return
        s = sprite[Y0 - y:Y1 - y, X0 - x:X1 - x]
        m = s[..., 3] > 0
        self.c[Y0:Y1, X0:X1][m] = s[..., :3][m].astype(np.float32)
        self.a[Y0:Y1, X0:X1] |= m


# ------------------------------------------------------------------------------------------------ resolve
def palette_of(cv: Canvas, n: int, keep=()) -> list:
    """Median-cut palette of the painting (opaque pixels) plus colours that must survive exactly."""
    px = np.clip(cv.c[cv.a], 0, 255).astype(np.uint8)
    if px.size == 0:
        return [rgb(k) for k in keep] or [np.zeros(3, np.float32)]
    side = int(math.ceil(math.sqrt(len(px))))
    buf = np.zeros((side * side, 3), np.uint8)
    buf[:len(px)] = px
    buf[len(px):] = px[0]
    q = Image.fromarray(buf.reshape(side, side, 3)).quantize(colors=n, method=Image.Quantize.MEDIANCUT,
                                                              dither=Image.Dither.NONE)
    pal = np.array(q.getpalette()[:n * 3], np.float32).reshape(-1, 3)
    used = sorted(set(np.array(q).reshape(-1).tolist()))
    out = [pal[i] for i in used]
    for k in keep:
        out.append(rgb(k))
    return out


def resolve(cv: Canvas, n=40, keep=(), dither=True) -> np.ndarray:
    P = palette_of(cv, n, keep)
    if len(P) < 2:
        P = P + [np.zeros(3, np.float32)]
    q = pg.quantize_rgb(np.clip(cv.c, 0, 255), P, dither=dither)
    out = np.zeros((cv.h, cv.w, 4), np.uint8)
    out[..., :3] = np.clip(np.round(q), 0, 255).astype(np.uint8)
    out[..., 3] = np.where(cv.a, 255, 0).astype(np.uint8)
    return _clean_orphans(out)


def _clean_orphans(img: np.ndarray) -> np.ndarray:
    """A lone pixel whose four neighbours share one other colour takes that colour (crisper clusters)."""
    c = img[..., :3].astype(np.int32)
    key = (c[..., 0] << 16) | (c[..., 1] << 8) | c[..., 2]
    k = key.copy()
    up, dn, lf, rt = k[:-2, 1:-1], k[2:, 1:-1], k[1:-1, :-2], k[1:-1, 2:]
    mid = k[1:-1, 1:-1]
    lone = (up == dn) & (dn == lf) & (lf == rt) & (mid != up)
    a = img[..., 3]
    lone &= np.abs(c[1:-1, 1:-1] - c[:-2, 1:-1]).sum(-1) < 60     # only dither specks, never ink, wire or a lamp
    lone &= (a[1:-1, 1:-1] > 0) & (a[:-2, 1:-1] > 0) & (a[2:, 1:-1] > 0) & (a[1:-1, :-2] > 0) & (a[1:-1, 2:] > 0)
    out = img.copy()
    src = img[:-2, 1:-1, :3]
    out[1:-1, 1:-1, :3][lone] = src[lone]
    return out


def save(arr: np.ndarray, name: str) -> str:
    os.makedirs(OUT, exist_ok=True)
    path = os.path.join(OUT, name)
    Image.fromarray(arr, 'RGBA').save(path, optimize=False)
    return path


def glow_sprite(w, h, cx, cy, rx, ry, col, levels=6, power=1.4, amax=1.0) -> np.ndarray:
    """Additive glow (black where dark): stepped rings in `col`, for sprites drawn with an additive material."""
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    d = np.sqrt(((xx + 0.5 - cx) / rx) ** 2 + ((yy + 0.5 - cy) / ry) ** 2)
    f = np.clip(1.0 - d, 0, 1) ** power * amax
    thr = pg.bayer(w, h)
    q = np.floor(f * levels + thr) / levels
    out = np.zeros((h, w, 4), np.uint8)
    out[..., :3] = np.clip(rgb(col)[None, None, :] * q[..., None], 0, 255).astype(np.uint8)
    out[..., 3] = 255
    return out


# ------------------------------------------------------------------------------------------------ the men
def sheet_frames(char: str, anim: str) -> list:
    """The non-empty 32x56 frames of one animation row of the game's own sheet."""
    meta = json.load(open(os.path.join(CHARS, char, 'sheet.json'), encoding='utf-8'))
    cw, ch = meta['cell']
    row = int(meta['anims'][anim]['row'])
    img = np.array(Image.open(os.path.join(CHARS, char, 'sheet.png')).convert('RGBA'))
    out = []
    for i in range(img.shape[1] // cw):
        f = img[row * ch:(row + 1) * ch, i * cw:(i + 1) * cw]
        if f[..., 3].any():
            out.append(f.copy())
    return out


def relight(frame: np.ndarray, tint, k: float, rim=None, rim_dir=(1, 0), rim_k=0.6, lift=0.0) -> np.ndarray:
    """Re-light a sheet frame: multiply toward `tint` by k, then a 1-px rim of `rim` on the side the light
    comes from (rim_dir points FROM the figure TO the light)."""
    f = frame.astype(np.float32)
    m = frame[..., 3] > 0
    t = rgb(tint) / 255.0
    f[..., :3] = f[..., :3] * ((1.0 - k) + k * t[None, None, :]) + lift
    if rim is not None:
        e = edge(m, int(rim_dir[0]), int(rim_dir[1]))
        f[..., :3][e] = f[..., :3][e] * (1 - rim_k) + rgb(rim) * rim_k
    out = frame.copy()
    out[..., :3] = np.clip(f[..., :3], 0, 255).astype(np.uint8)
    return out


def strip(frames: list) -> np.ndarray:
    h, w = frames[0].shape[:2]
    out = np.zeros((h, w * len(frames), 4), np.uint8)
    for i, f in enumerate(frames):
        out[:, i * w:(i + 1) * w] = f
    return out


def write_layout(data: dict):
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, 'layout.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(data, f, indent=1, ensure_ascii=False, sort_keys=True)
        f.write('\n')
