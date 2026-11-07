"""env_c4p2_cine_flat -- the flat painter of the Chapter-4-part-2 close shots (owner: cine stream, round 10).

Close and macro plates (the dining-car table, the canteen table, the book's fore-edge, the valves, the teleprinter
desk) are painted like pixel art, not lit like a render: every surface is a flat colour from a short ramp, light is
laid on in stepped rings (each step one ramp tone, a one-pixel checker seam between steps), objects carry a dark
outline on their shadow side and a lit edge on the key side, and cast shadows are flat offset silhouettes.  Masks
come from the kit's GB (box / poly / ell / line / text); colours are sRGB hex.  Deterministic.
"""
from __future__ import annotations

import math

import numpy as np

import env_c4p2_cine_kit as K

VW, VH = K.VW, K.VH


def hx(c):
    return np.asarray(K.hx(c), np.float32)


class Flat:
    """An sRGB float canvas with GB masks."""

    def __init__(self, w=VW, h=VH, ox=0, oy=0, bg='#000000'):
        self.g = K.GB(w, h, ox, oy)
        self.w, self.h = int(w), int(h)
        self.rgb = np.broadcast_to(hx(bg), (self.h, self.w, 3)).copy()
        self.a = np.zeros((self.h, self.w), bool)
        self.yy, self.xx = self.g.yy, self.g.xx

    # ------------------------------------------------------------------ masks
    def box(self, *a):
        return self.g.box(*a)

    def poly(self, pts):
        return self.g.poly(pts)

    def ell(self, cx, cy, rx, ry):
        return self.g.ell(cx, cy, rx, ry)

    def line(self, pts, r=0.5):
        return self.g.line(pts, r)

    def text(self, s, x, y, font='s', spacing=1):
        return self.g.text(s, x, y, font, spacing)

    # ------------------------------------------------------------------ paint
    def fill(self, m, col):
        m = np.asarray(m, bool)
        if isinstance(col, np.ndarray) and col.ndim == 3:
            self.rgb[m] = col[m]
        else:
            self.rgb[m] = hx(col) if isinstance(col, str) else np.asarray(col, np.float32)
        self.a |= m
        return m

    def mul(self, m, k):
        m = np.asarray(m, bool)
        self.rgb[m] *= k
        return m

    def tint(self, m, col, k):
        m = np.asarray(m, bool)
        self.rgb[m] = self.rgb[m] * (1 - k) + hx(col) * k
        return m

    def outline(self, m, col=None, k=0.45, sides='all', width=1):
        """Darken the border pixels of mask m (inside it).  sides: 'all' or a subset of 'lrtb'."""
        m = np.asarray(m, bool)
        e = edge(m, sides, width)
        if col is None:
            self.rgb[e] *= k
        else:
            self.rgb[e] = hx(col)
        return e

    def lit_edge(self, m, col=None, k=1.25, sides='t', width=1):
        m = np.asarray(m, bool)
        e = edge(m, sides, width)
        if col is None:
            self.rgb[e] = np.clip(self.rgb[e] * k, 0, 1)
        else:
            self.rgb[e] = hx(col)
        return e

    def shadow(self, m, dx, dy, k=0.62, under=None, col=None):
        """A flat cast shadow: m shifted by (dx, dy), outside m (and inside `under` when given)."""
        m = np.asarray(m, bool)
        s = shift(m, int(round(dx)), int(round(dy))) & ~m
        if under is not None:
            s &= under
        if col is None:
            self.rgb[s] *= k
        else:
            self.rgb[s] = self.rgb[s] * 0.35 + hx(col) * 0.65
        return s

    def pool(self, m, cx, cy, rx, ry, steps=((1.0, 1.22), (0.66, 1.12), (0.36, 1.05)), seam=True, col=None):
        """Stepped light: inside the ellipse of relative radius r the colour is multiplied by k (inner rings
        win); a one-pixel checker seam softens each step like a dithered pixel-art gradient."""
        m = np.asarray(m, bool)
        d = np.hypot((self.xx - cx) / max(rx, 1e-3), (self.yy - cy) / max(ry, 1e-3))
        chk = ((self.xx.astype(np.int32) + self.yy.astype(np.int32)) & 1) == 0
        out = np.ones((self.h, self.w), np.float32)
        for r, k in sorted(steps, key=lambda s: -s[0]):
            inside = d < r
            if seam:
                band = (d >= r) & (d < r + 1.6 / max(rx, 1.0)) & chk
                inside = inside | band
            out = np.where(inside, k, out)
        if col is None:
            self.rgb[m] = np.clip(self.rgb[m] * out[m][:, None], 0, 1)
        else:
            c = hx(col)
            kk = (out[m] - 1.0)[:, None]
            self.rgb[m] = np.clip(self.rgb[m] * out[m][:, None] + c * np.clip(kk, 0, None) * 0.3, 0, 1)
        return out

    def grad(self, m, y0, y1, c0, c1, steps=5, axis='y'):
        """A stepped vertical (or horizontal) gradient with checker seams between the steps."""
        m = np.asarray(m, bool)
        t = (self.yy - y0) / max(1e-3, (y1 - y0)) if axis == 'y' else (self.xx - y0) / max(1e-3, (y1 - y0))
        t = np.clip(t, 0, 1) * steps
        chk = ((self.xx.astype(np.int32) + self.yy.astype(np.int32)) & 1) == 0
        q = np.floor(t + np.where(chk, 0.18, -0.18))
        q = np.clip(q, 0, steps) / steps
        A, B = hx(c0), hx(c1)
        col = A[None, None] * (1 - q[..., None]) + B[None, None] * q[..., None]
        self.rgb[m] = col[m]
        self.a |= m
        return m

    def pattern(self, m, fn, col):
        """Paint col where fn(xx, yy) is True inside m."""
        mm = np.asarray(m, bool) & fn(self.xx, self.yy)
        self.rgb[mm] = hx(col)
        return mm

    def speckle(self, m, density, col, seed=0, k=None):
        mm = np.asarray(m, bool) & (K.hash2(self.xx.astype(np.int64), self.yy.astype(np.int64), seed) < density)
        if k is not None:
            self.rgb[mm] *= k
        else:
            self.rgb[mm] = hx(col)
        return mm

    def paste(self, rgba, x, y, clip=None):
        """Composite an RGBA image (a figure, a prop) with its top-left at world (x, y); `clip` limits it to a
        mask.  Returns the mask it covered."""
        rgba = np.asarray(rgba)
        h, w = rgba.shape[:2]
        X0, Y0 = int(round(x - self.g.ox)), int(round(y - self.g.oy))
        xa, ya, xb, yb = max(0, X0), max(0, Y0), min(self.w, X0 + w), min(self.h, Y0 + h)
        m = np.zeros((self.h, self.w), bool)
        if xb <= xa or yb <= ya:
            return m
        sub = rgba[ya - Y0:yb - Y0, xa - X0:xb - X0].astype(np.float32)
        a = sub[..., 3] / 255.0
        if clip is not None:
            a = a * np.asarray(clip, bool)[ya:yb, xa:xb]
        self.rgb[ya:yb, xa:xb] = self.rgb[ya:yb, xa:xb] * (1 - a[..., None]) + sub[..., :3] / 255.0 * a[..., None]
        m[ya:yb, xa:xb] = a > 0
        self.a |= m
        return m

    def rgba(self, alpha=None):
        out = np.zeros((self.h, self.w, 4), np.uint8)
        out[..., :3] = np.round(np.clip(self.rgb, 0, 1) * 255).astype(np.uint8)
        a = self.a if alpha is None else alpha
        out[..., 3] = np.where(a, 255, 0)
        return out

    def opaque(self):
        out = self.rgba(np.ones((self.h, self.w), bool))
        return out


def shift(m, dx, dy):
    out = np.zeros_like(m)
    H, W = m.shape
    ys, yd = slice(max(0, dy), min(H, H + dy)), slice(max(0, -dy), min(H, H - dy))
    xs, xd = slice(max(0, dx), min(W, W + dx)), slice(max(0, -dx), min(W, W - dx))
    out[ys, xs] = m[yd, xd]
    return out


def edge(m, sides='all', width=1):
    out = np.zeros_like(m)
    cur = m.copy()
    for _ in range(width):
        p = np.pad(cur, 1)
        e = np.zeros_like(cur)
        if sides == 'all' or 'l' in sides:
            e |= cur & ~p[1:-1, :-2]
        if sides == 'all' or 'r' in sides:
            e |= cur & ~p[1:-1, 2:]
        if sides == 'all' or 't' in sides:
            e |= cur & ~p[:-2, 1:-1]
        if sides == 'all' or 'b' in sides:
            e |= cur & ~p[2:, 1:-1]
        out |= e
        cur = cur & ~e
    return out


def outline_rgba(rgba, k=0.42, col=None, sides='all'):
    """Darken (or colour) the silhouette edge of a sprite."""
    out = rgba.copy()
    a = out[..., 3] > 0
    e = edge(a, sides)
    if col is None:
        out[e, :3] = (out[e, :3].astype(np.float32) * k).astype(np.uint8)
    else:
        out[e, :3] = np.asarray(K.hx(col) * 255, np.uint8)
    return out


def shadow_rgba(rgba, dx, dy, col=(16, 10, 8, 96)):
    """A flat translucent cast shadow behind a sprite (inside the same canvas)."""
    a = rgba[..., 3] > 0
    s = shift(a, int(round(dx)), int(round(dy))) & ~a
    out = rgba.copy()
    out[s] = np.asarray(col, np.uint8)
    return out


def over(dst, src, x, y):
    """Alpha-over a straight RGBA uint8 sprite onto an RGBA canvas (translucent pixels blend)."""
    h, w = src.shape[:2]
    X0, Y0, X1, Y1 = max(0, x), max(0, y), min(dst.shape[1], x + w), min(dst.shape[0], y + h)
    if X1 <= X0 or Y1 <= Y0:
        return dst
    s = src[Y0 - y:Y1 - y, X0 - x:X1 - x].astype(np.float32)
    d = dst[Y0:Y1, X0:X1].astype(np.float32)
    a = s[..., 3:4] / 255.0
    d[..., :3] = s[..., :3] * a + d[..., :3] * (1 - a)
    d[..., 3:4] = np.maximum(d[..., 3:4], s[..., 3:4])
    dst[Y0:Y1, X0:X1] = np.round(d).astype(np.uint8)
    return dst
