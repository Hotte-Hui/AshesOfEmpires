"""chargen_core -- articulated paper-doll rig renderer for ASHES OF EMPIRES character sprites.

Pipeline per animation frame (one 32x56 cell):
  1. A pose (keyframed joint angles + IK foot targets) is turned into 2D joint positions.
  2. Body parts are rasterised in draw order into a *G-buffer* (`Frame`): material id, explicit
     tone (hand-shaded pixel shapes) or auto tone, analytic / height-derived normal, part id.
       * limbs  -> tapered capsules (cylindrical normals)
       * torso / coat / skirt -> polygons with a height field (cylinder x pillow) -> normals
       * heads, hands, boots, props -> hand-designed pixel bitmaps (explicit palette tones)
  3. `shade()` resolves the G-buffer into palette colours: hue-shifted material ramps, baked
     front-top key light, directional contact shadows between parts, a cool rim light on edges
     facing the rim direction and a *selective* outline (outer edge pixels only, tinted to the
     material's darkest hue-shifted shade, lighter where the edge faces the key light).
  4. The same normals are encoded as an OpenGL (+Y up) normal map for Godot 2D lights.

No randomness: everything is deterministic and reproducible.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

import numpy as np

# ----------------------------------------------------------------------------------- colour
_M1 = np.array([[0.4122214708, 0.5363325363, 0.0514459929],
                [0.2119034982, 0.6806995451, 0.1073969566],
                [0.0883024619, 0.2817188376, 0.6299787005]])
_M2 = np.array([[0.2104542553, 0.7936177850, -0.0040720468],
                [1.9779984951, -2.4285922050, 0.4505937099],
                [0.0259040371, 0.7827717662, -0.8086757660]])
_M2i = np.linalg.inv(_M2)
_M1i = np.linalg.inv(_M1)


def hex_rgb(h: str) -> np.ndarray:
    h = h.lstrip('#')
    return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], np.float64)


def rgb_hex(c) -> str:
    c = np.clip(np.round(np.asarray(c, np.float64)[:3]), 0, 255).astype(int)
    return '#%02X%02X%02X' % tuple(c)


def _to_lin(c):
    c = np.asarray(c, np.float64) / 255.0
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def _to_srgb(c):
    c = np.asarray(c, np.float64)
    c = np.where(c <= 0.0031308, c * 12.92, 1.055 * np.clip(c, 0, None) ** (1 / 2.4) - 0.055)
    return c * 255.0


def rgb_to_oklch(rgb):
    lin = _to_lin(rgb)
    lms = _M1 @ lin
    lab = _M2 @ np.cbrt(lms)
    L, a, b = lab
    return float(L), float(math.hypot(a, b)), float(math.degrees(math.atan2(b, a)) % 360)


def oklch_to_rgb(L, C, h):
    """OKLCh -> sRGB (0..255), reducing chroma until inside the gamut."""
    for _ in range(40):
        a, b = C * math.cos(math.radians(h)), C * math.sin(math.radians(h))
        lms = (_M2i @ np.array([L, a, b])) ** 3
        lin = _M1i @ lms
        if np.all(lin >= -1e-4) and np.all(lin <= 1 + 1e-4):
            break
        C *= 0.9
    return np.clip(_to_srgb(np.clip(lin, 0, 1)), 0, 255)


def _hue_towards(h, target, t):
    d = ((target - h + 180) % 360) - 180
    return (h + d * t) % 360


# Scene lighting temperature used for ramp hue shifting (OKLCh hue/chroma of the shadow / light tint).
SCENE_TINT = {
    'karsk': dict(shadow_h=215.0, shadow_c=0.050, light_h=80.0, light_c=0.060),
    'berlin': dict(shadow_h=295.0, shadow_c=0.050, light_h=62.0, light_c=0.065),
    'archive': dict(shadow_h=232.0, shadow_c=0.045, light_h=72.0, light_c=0.060),
}

# lightness offsets for the 6 ramp slots [outline, deep, shadow, base, light, highlight]
RAMP_DL = (-0.25, -0.165, -0.085, 0.0, 0.095, 0.17)
RAMP_HT = (0.55, 0.42, 0.26, 0.0, 0.20, 0.34)    # how far a slot's chroma vector moves to the tint
RAMP_CH = (0.70, 0.85, 0.95, 1.0, 1.0, 0.90)     # chroma scale of the material's own colour


def make_ramp(base_hex: str, scene: str = 'karsk', dl=RAMP_DL, ht=RAMP_HT, chroma=RAMP_CH,
              floor_l: float = 0.13) -> list[np.ndarray]:
    """Hue-shifted 6-tone ramp around a base (slot 3) colour, built in OKLab: dark slots blend their
    chroma vector towards the scene's shadow tint (teal / violet), light slots towards warm ochre.
    Blending vectors (not rotating hue) avoids detours through unrelated hues.  Returns RGBA uint8."""
    t = SCENE_TINT[scene]
    L0, C0, h0 = rgb_to_oklch(hex_rgb(base_hex))
    a0, b0 = C0 * math.cos(math.radians(h0)), C0 * math.sin(math.radians(h0))
    sa, sb = t['shadow_c'] * math.cos(math.radians(t['shadow_h'])), t['shadow_c'] * math.sin(math.radians(t['shadow_h']))
    la, lb = t['light_c'] * math.cos(math.radians(t['light_h'])), t['light_c'] * math.sin(math.radians(t['light_h']))
    out = []
    for i, (d, k) in enumerate(zip(dl, ht)):
        L = max(floor_l * (1.0 if i else 0.75), L0 + d)
        ca, cb = a0 * chroma[i], b0 * chroma[i]
        if i < 3:
            ta, tb = sa, sb
        else:
            ta, tb = la, lb
        A_ = ca + (ta - ca) * k
        B_ = cb + (tb - cb) * k
        C = math.hypot(A_, B_)
        h = math.degrees(math.atan2(B_, A_)) % 360
        rgb = oklch_to_rgb(L, C, h)
        out.append(np.array([*np.round(rgb), 255], np.uint8))
    return out


def ramp_from_hex(hexes: list[str]) -> list[np.ndarray]:
    return [np.array([*hex_rgb(h), 255], np.uint8) for h in hexes]


@dataclass
class Material:
    name: str
    ramp: list            # 6 RGBA colours, 0 = outline / darkest ... 5 = highlight
    rim: np.ndarray | None = None
    bias: float = 0.0     # added to auto light value
    outline: bool = True  # participates in selective outline
    glossy: bool = False  # allows the highlight slot (5) for auto tones
    max_tone: int = 4     # brightest slot reachable by auto shading (before rim)
    texture: str | None = None   # 'fur' | 'knit' | 'felt' | 'tweed': deterministic tone pattern on auto pixels
    min_tone: int = 1     # darkest slot reachable by auto shading (outline stays 0)
    rim_ok: bool = True   # receives the cool rim light on back edges
    rim_k: float = 1.0    # rim blend strength multiplier


RIM_TONE = 9.0   # explicit tone marker: paint with the material's rim colour


# ----------------------------------------------------------------------------------- G-buffer
class Frame:
    """G-buffer for one sprite cell."""

    def __init__(self, w: int = 32, h: int = 56):
        self.w, self.h = w, h
        self.mat = np.full((h, w), -1, np.int16)
        self.tone = np.full((h, w), np.nan, np.float32)
        self.bias = np.zeros((h, w), np.float32)
        self.n = np.zeros((h, w, 3), np.float32)
        self.n[..., 2] = 1.0
        self.part = np.full((h, w), -1, np.int16)
        self.cast = np.zeros((h, w), bool)
        self.recv = np.ones((h, w), bool)
        self.fixed = np.zeros((h, w), bool)   # pixels exempt from outline / rim (eyes, glints)
        self.ao = np.zeros((h, w), bool)      # part darkens neighbours behind it in every direction
        self.norim = np.zeros((h, w), bool)   # pixels that never receive rim light
        self.inline = np.zeros((h, w), bool)  # part draws a dark inner line where it overlaps parts behind
        self.edgelit = np.zeros((h, w), bool) # part draws a light line on its key-facing border over parts behind
        self.nparts = 0
        self.names: list[str] = []

    def put(self, mask, x0, y0, mat: int | np.ndarray, normals=None, tone=None, bias: float = 0.0,
            cast: bool = True, recv: bool = True, fixed=None, name: str = '', ao: bool = False,
            norim: bool = False, inline: bool = False, edge_light: bool = False):
        """Write a part.  mask: bool (h,w) at (x0,y0).  mat: int or per-pixel int array.
        normals: (h,w,3) or None (flat).  tone: None (auto) / float / per-pixel array (nan=auto)."""
        mh, mw = mask.shape
        X0, Y0 = max(0, x0), max(0, y0)
        X1, Y1 = min(self.w, x0 + mw), min(self.h, y0 + mh)
        pid = self.nparts
        self.nparts += 1
        self.names.append(name)
        if X1 <= X0 or Y1 <= Y0:
            return pid
        sl = (slice(Y0 - y0, Y1 - y0), slice(X0 - x0, X1 - x0))
        m = mask[sl]
        if not m.any():
            return pid
        dst = (slice(Y0, Y1), slice(X0, X1))
        if np.isscalar(mat) or np.ndim(mat) == 0:
            self.mat[dst][m] = int(mat)
        else:
            self.mat[dst][m] = np.asarray(mat)[sl][m]
        if normals is None:
            self.n[dst][m] = (0.0, 0.0, 1.0)
        else:
            self.n[dst][m] = np.asarray(normals)[sl][m]
        if tone is None:
            self.tone[dst][m] = np.nan
        elif np.isscalar(tone) or np.ndim(tone) == 0:
            self.tone[dst][m] = float(tone)
        else:
            self.tone[dst][m] = np.asarray(tone, np.float32)[sl][m]
        if np.isscalar(bias) or np.ndim(bias) == 0:
            self.bias[dst][m] = bias
        else:
            self.bias[dst][m] = np.asarray(bias, np.float32)[sl][m]
        self.part[dst][m] = pid
        self.cast[dst][m] = cast
        self.recv[dst][m] = recv
        self.ao[dst][m] = ao
        self.norim[dst][m] = norim
        self.inline[dst][m] = inline
        self.edgelit[dst][m] = edge_light
        if fixed is None:
            self.fixed[dst][m] = False
        elif np.isscalar(fixed) or np.ndim(fixed) == 0:
            self.fixed[dst][m] = bool(fixed)
        else:
            self.fixed[dst][m] = np.asarray(fixed)[sl][m]
        return pid

    def px(self, x, y, mat, tone, n=None, fixed=True, name='px', cast=False):
        x, y = int(math.floor(x)), int(math.floor(y))
        if 0 <= x < self.w and 0 <= y < self.h:
            m = np.ones((1, 1), bool)
            nn = None if n is None else np.asarray(n, np.float32).reshape(1, 1, 3)
            self.put(m, x, y, mat, nn, tone, fixed=fixed, name=name, cast=cast)

    def recolor(self, x, y, mat, tone, fixed=True):
        """Change material/tone of an already-occupied pixel (keeps its normal/part)."""
        x, y = int(math.floor(x)), int(math.floor(y))
        if 0 <= x < self.w and 0 <= y < self.h and self.mat[y, x] >= 0:
            self.mat[y, x] = mat
            self.tone[y, x] = tone
            self.fixed[y, x] = fixed

    def shift(self, dx: int, dy: int):
        for a in ('mat', 'tone', 'bias', 'n', 'part', 'cast', 'recv', 'fixed', 'ao', 'norim', 'inline', 'edgelit'):
            arr = getattr(self, a)
            fill = {'mat': -1, 'tone': np.nan, 'part': -1}.get(a, 0)
            out = np.empty_like(arr)
            out[...] = fill if a != 'n' else 0
            if a == 'n':
                out[..., 2] = 1
            H, W = arr.shape[:2]
            ys = slice(max(0, dy), min(H, H + dy)); yd = slice(max(0, -dy), min(H, H - dy))
            xs = slice(max(0, dx), min(W, W + dx)); xd = slice(max(0, -dx), min(W, W - dx))
            out[ys, xs] = arr[yd, xd]
            setattr(self, a, out)


# ----------------------------------------------------------------------------------- shapes
def _grid(x0, y0, w, h):
    yy, xx = np.mgrid[0:h, 0:w]
    return xx + x0 + 0.5, yy + y0 + 0.5


def capsule(a, b, ra, rb=None, nz_min: float = 0.25):
    """Tapered capsule between points a and b (cell coords, y down).
    Returns (mask, x0, y0, normals).  Normals are cylindrical around the segment axis."""
    rb = ra if rb is None else rb
    ax, ay = a; bx, by = b
    r = max(ra, rb)
    x0 = int(math.floor(min(ax, bx) - r - 1)); y0 = int(math.floor(min(ay, by) - r - 1))
    x1 = int(math.ceil(max(ax, bx) + r + 1)); y1 = int(math.ceil(max(ay, by) + r + 1))
    w, h = x1 - x0 + 1, y1 - y0 + 1
    X, Y = _grid(x0, y0, w, h)
    abx, aby = bx - ax, by - ay
    L2 = abx * abx + aby * aby
    if L2 < 1e-9:
        t = np.zeros_like(X)
    else:
        t = np.clip(((X - ax) * abx + (Y - ay) * aby) / L2, 0, 1)
    cx, cy = ax + t * abx, ay + t * aby
    rr = ra + (rb - ra) * t
    vx, vy = (X - cx) / rr, (Y - cy) / rr
    d2 = vx * vx + vy * vy
    mask = d2 < 1.0
    s = np.sqrt(np.clip(d2, 0, 1))
    k = np.where(s > 0, np.minimum(s, math.sqrt(1 - nz_min ** 2)) / np.maximum(s, 1e-6), 0)
    nx, ny = vx * k, -vy * k
    nz = np.sqrt(np.clip(1 - nx * nx - ny * ny, 0, 1))
    nrm = np.stack([nx, ny, nz], -1).astype(np.float32)
    return mask, x0, y0, nrm


def poly_mask(pts):
    xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
    x0, x1 = int(math.floor(min(xs))) - 1, int(math.ceil(max(xs))) + 1
    y0, y1 = int(math.floor(min(ys))) - 1, int(math.ceil(max(ys))) + 1
    w, h = x1 - x0 + 1, y1 - y0 + 1
    mask = np.zeros((h, w), bool)
    n = len(pts)
    for row in range(h):
        yc = y0 + row + 0.5
        cross = []
        for i in range(n):
            ax, ay = pts[i]; bx, by = pts[(i + 1) % n]
            if (ay <= yc < by) or (by <= yc < ay):
                cross.append(ax + (yc - ay) * (bx - ax) / (by - ay))
        cross.sort()
        for k in range(0, len(cross) - 1, 2):
            xa = int(math.ceil(cross[k] - 0.5)) - x0
            xb = int(math.floor(cross[k + 1] - 0.5)) - x0
            if xb >= xa:
                mask[row, max(0, xa):min(w, xb + 1)] = True
    return mask, x0, y0


def dist_inside(mask: np.ndarray) -> np.ndarray:
    """Euclidean distance (px) from each inside pixel centre to the nearest outside pixel centre."""
    h, w = mask.shape
    p = np.pad(mask, 1)
    oy, ox = np.nonzero(~p)
    iy, ix = np.nonzero(p)
    out = np.zeros(p.shape, np.float32)
    if len(iy) and len(oy):
        # chunked brute force (masks are tiny)
        res = np.empty(len(iy), np.float32)
        for s in range(0, len(iy), 512):
            dy = iy[s:s + 512, None] - oy[None, :]
            dx = ix[s:s + 512, None] - ox[None, :]
            res[s:s + 512] = np.sqrt((dx * dx + dy * dy).min(1))
        out[iy, ix] = res
    return out[1:-1, 1:-1]


def height_normals(hgt: np.ndarray, mask: np.ndarray, strength: float = 1.0) -> np.ndarray:
    """Normals from a height field (outside = 0).  OpenGL convention (+y up)."""
    hh = np.where(mask, hgt, 0.0)
    p = np.pad(hh, 1)
    gx = (p[1:-1, 2:] - p[1:-1, :-2]) * 0.5
    gy = (p[2:, 1:-1] - p[:-2, 1:-1]) * 0.5
    n = np.stack([-gx * strength, gy * strength, np.ones_like(hh)], -1)
    n /= np.linalg.norm(n, axis=-1, keepdims=True)
    return n.astype(np.float32)


def poly(pts, R: float = 2.5, cyl: float = 0.7, strength: float = 1.0, axis_x: float | None = None,
         extra_h=None):
    """Polygon part with a height-derived normal field:
    height = cyl * (cylinder across each row) + (1-cyl) * (pillow of radius R from the outline).
    `extra_h(X, Y) -> array` may add relief (folds, quilting) before the normals are derived."""
    mask, x0, y0 = poly_mask(pts)
    d = dist_inside(mask)
    q = np.clip(d / R, 0, 1)
    pillow = R * np.sqrt(np.clip(1 - (1 - q) ** 2, 0, 1))
    cylh = np.zeros_like(pillow)
    if cyl > 0:
        for r in range(mask.shape[0]):
            xs = np.nonzero(mask[r])[0]
            if len(xs) == 0:
                continue
            a, b = xs.min(), xs.max() + 1
            mid = (a + b) / 2.0 if axis_x is None else axis_x - x0
            half = max(1.0, (b - a) / 2.0)
            u = (np.arange(a, b) + 0.5 - mid) / half
            cylh[r, a:b] = half * np.sqrt(np.clip(1 - np.clip(u, -1, 1) ** 2, 0, 1))
    hgt = cyl * cylh + (1 - cyl) * pillow
    if extra_h is not None:
        X, Y = _grid(x0, y0, mask.shape[1], mask.shape[0])
        hgt = hgt + extra_h(X, Y)
    hgt = np.where(mask, hgt, 0)
    nrm = height_normals(hgt, mask, strength)
    return mask, x0, y0, nrm


def ellipse(cx, cy, rx, ry, nz_min=0.25):
    x0, y0 = int(math.floor(cx - rx)) - 1, int(math.floor(cy - ry)) - 1
    w, h = int(math.ceil(2 * rx)) + 3, int(math.ceil(2 * ry)) + 3
    X, Y = _grid(x0, y0, w, h)
    vx, vy = (X - cx) / rx, (Y - cy) / ry
    d2 = vx * vx + vy * vy
    mask = d2 < 1.0
    s = np.sqrt(np.clip(d2, 0, 1))
    k = np.where(s > 0, np.minimum(s, math.sqrt(1 - nz_min ** 2)) / np.maximum(s, 1e-6), 0)
    nx, ny = vx * k, -vy * k
    nz = np.sqrt(np.clip(1 - nx * nx - ny * ny, 0, 1))
    return mask, x0, y0, np.stack([nx, ny, nz], -1).astype(np.float32)


# ----------------------------------------------------------------------------------- bitmaps
class Bitmap:
    """Hand-designed pixel shape.  rows: list of strings; legend: char -> (material, tone|None, flags).
    tone None = auto-shaded from normals.  '.' / ' ' = transparent.  anchor = attachment pixel."""

    def __init__(self, rows: list[str] | str, legend: dict, anchor=(0, 0), dome=(1.0, 1.0), nz_min=0.35,
                 normals: dict | None = None):
        if isinstance(rows, str):
            rows = [r for r in (ln.strip() for ln in rows.strip('\n').split('\n')) if r]
        rows = [r.replace(' ', '') for r in rows]
        self.rows = rows
        self.legend = legend
        self.h = len(rows)
        self.w = max(len(r) for r in rows)
        self.anchor = anchor
        self.dome = dome
        self.nz_min = nz_min
        self.normals = normals or {}

    def variant(self, subs: dict) -> 'Bitmap':
        """Return a copy with some chars substituted ({(x,y): char} or {char: char})."""
        rows = [list(r.ljust(self.w, '.')) for r in self.rows]
        for k, v in subs.items():
            if isinstance(k, tuple):
                x, y = k
                rows[y][x] = v
            else:
                rows = [[v if c == k else c for c in r] for r in rows]
        b = Bitmap([''.join(r) for r in rows], self.legend, self.anchor, self.dome, self.nz_min, self.normals)
        return b

    def paint(self, layer_rows: list[str] | str, at=(0, 0)) -> 'Bitmap':
        """Copy with another ASCII layer painted on top (non-'.' chars win), `at` = layer's top-left in this
        bitmap's pixel frame (may be negative: the canvas grows and the anchor is kept on the same pixel)."""
        if isinstance(layer_rows, str):
            layer_rows = [r for r in (ln.strip() for ln in layer_rows.strip('\n').split('\n')) if r]
        layer_rows = [r.replace(' ', '') for r in layer_rows]
        lw = max(len(r) for r in layer_rows)
        lh = len(layer_rows)
        ax, ay = at
        x0, y0 = min(0, ax), min(0, ay)
        x1, y1 = max(self.w, ax + lw), max(self.h, ay + lh)
        W, H = x1 - x0, y1 - y0
        grid = [['.'] * W for _ in range(H)]
        for y, r in enumerate(self.rows):
            for x, ch in enumerate(r):
                grid[y - y0][x - x0] = ch
        for y, r in enumerate(layer_rows):
            for x, ch in enumerate(r):
                if ch not in '. ':
                    grid[ay + y - y0][ax + x - x0] = ch
        return Bitmap([''.join(r) for r in grid], self.legend, (self.anchor[0] - x0, self.anchor[1] - y0),
                      self.dome, self.nz_min, self.normals)

    def with_legend(self, extra: dict) -> 'Bitmap':
        lg = dict(self.legend)
        lg.update(extra)
        return Bitmap(list(self.rows), lg, self.anchor, self.dome, self.nz_min, self.normals)

    def flipped(self) -> 'Bitmap':
        rows = [r.ljust(self.w, '.')[::-1] for r in self.rows]
        flipn = {k: (-v[0], v[1], v[2]) for k, v in self.normals.items()}
        return Bitmap(rows, self.legend, (self.w - 1 - self.anchor[0], self.anchor[1]), self.dome, self.nz_min, flipn)

    def arrays(self, mats: dict):
        h, w = self.h, self.w
        mask = np.zeros((h, w), bool)
        mat = np.full((h, w), -1, np.int16)
        tone = np.full((h, w), np.nan, np.float32)
        fixed = np.zeros((h, w), bool)
        bias = np.zeros((h, w), np.float32)
        nrm_over = np.full((h, w, 3), np.nan, np.float32)
        for y, r in enumerate(self.rows):
            for x, ch in enumerate(r):
                if ch in '. ':
                    continue
                if ch not in self.legend:
                    raise KeyError(f'bitmap char {ch!r} missing in legend')
                spec = self.legend[ch]
                mname, t = spec[0], spec[1]
                flags = spec[2] if len(spec) > 2 else ''
                mask[y, x] = True
                mat[y, x] = mats[mname]
                tone[y, x] = np.nan if t is None else (RIM_TONE if t == 'rim' else t)
                # hand-drawn (explicit tone) pixels carry their own outline / rim unless flagged 'o'
                fixed[y, x] = ('f' in flags) or (t is not None and 'o' not in flags)
                if 'd' in flags:
                    bias[y, x] = -1.0
                if ch in self.normals:
                    nrm_over[y, x] = self.normals[ch]
        # dome normals over the whole bitmap mask (head / boot / hand volumes)
        ys, xs = np.nonzero(mask)
        nrm = np.zeros((h, w, 3), np.float32); nrm[..., 2] = 1
        if len(xs):
            cx = (xs.min() + xs.max() + 1) / 2.0
            cy = (ys.min() + ys.max() + 1) / 2.0
            rx = max(1.0, (xs.max() + 1 - xs.min()) / 2.0) * self.dome[0]
            ry = max(1.0, (ys.max() + 1 - ys.min()) / 2.0) * self.dome[1]
            X, Y = np.meshgrid(np.arange(w) + 0.5, np.arange(h) + 0.5)
            vx, vy = (X - cx) / rx, (Y - cy) / ry
            s = np.sqrt(vx * vx + vy * vy)
            lim = math.sqrt(1 - self.nz_min ** 2)
            k = np.where(s > lim, lim / np.maximum(s, 1e-6), 1.0)
            nx, ny = vx * k, -vy * k
            nz = np.sqrt(np.clip(1 - nx * nx - ny * ny, 0, 1))
            nrm = np.stack([nx, ny, nz], -1).astype(np.float32)
        over = ~np.isnan(nrm_over[..., 0])
        if over.any():
            v = nrm_over[over]
            v /= np.linalg.norm(v, axis=-1, keepdims=True)
            nrm[over] = v
        return mask, mat, tone, fixed, bias, nrm


def put_bitmap(fr: Frame, bm: Bitmap, mats: dict, at_x: float, at_y: float, cast=True, name='bitmap',
               bias=0.0, recv=True):
    """Place bitmap so that its anchor pixel lands on (floor(at_x), floor(at_y))."""
    mask, mat, tone, fixed, b2, nrm = bm.arrays(mats)
    x0 = int(math.floor(at_x)) - bm.anchor[0]
    y0 = int(math.floor(at_y)) - bm.anchor[1]
    return fr.put(mask, x0, y0, mat, nrm, tone, bias=b2 + bias, cast=cast, recv=recv, fixed=fixed, name=name)


# ----------------------------------------------------------------------------------- shading
@dataclass
class Light:
    key: tuple = (0.55, 0.62, 0.56)      # baked key (x right, y up, z towards viewer)
    rim: tuple = (-0.80, 0.42, -0.30)     # cool back rim
    ambient: float = 0.30
    thresholds: tuple = (0.30, 0.50, 0.72, 0.90)   # value -> tone slots 1..5
    shadow_dirs: tuple = ((0, -1), (1, -1), (1, 0))   # where the occluder sits relative to receiver
    rim_dirs: tuple = ((-1, 0), (-1, -1), (0, -1))     # outward edge dirs that may receive rim
    lit_dirs: tuple = ((1, 0), (1, -1), (0, -1))       # outward edge dirs facing the key
    inline_dirs: tuple = ((-1, 0), (0, 1), (-1, 1))    # inner line where an overlapping part ends


def _norm(v):
    v = np.asarray(v, np.float32)
    return v / (np.linalg.norm(v) + 1e-9)


# deterministic 4x4 texture patterns (tone offsets) for cloth / fur on auto-shaded pixels
_TEX = {
    'fur': np.array([[0, -1, 0, 0], [0, 0, 0, 1], [-1, 0, 0, 0], [0, 0, 1, -1]], np.float32),
    'knit': np.array([[0, -1, 0, -1], [0, 0, 0, 0], [-1, 0, -1, 0], [0, 0, 0, 0]], np.float32) * 0.6,
    'felt': np.array([[0, 0, 0, 0], [0, -1, 0, 0], [0, 0, 0, 0], [0, 0, 0, -1]], np.float32) * 0.7,
    'tweed': np.array([[0, -1, 0, 0], [0, 0, 0, -1], [0, 0, -1, 0], [-1, 0, 0, 0]], np.float32) * 0.6,
}


def _clean_orphans(tone, mat, editable, passes=2):
    """A pixel whose 4 neighbours (same material, at least 3 present) all share one tone that differs
    from its own is a noise orphan -> take the neighbours' tone.  Only `editable` pixels change."""
    h, w = tone.shape
    for _ in range(passes):
        pt = np.pad(tone, 1, constant_values=-99)
        pm = np.pad(mat, 1, constant_values=-1)
        nbs_t = [pt[1 + dy:1 + dy + h, 1 + dx:1 + dx + w] for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))]
        nbs_m = [pm[1 + dy:1 + dy + h, 1 + dx:1 + dx + w] for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))]
        same = [m == mat for m in nbs_m]
        cnt = sum(s.astype(np.int16) for s in same)
        # candidate tone: the first same-material neighbour's tone
        cand = np.full((h, w), -99.0, np.float32)
        for t, s in zip(nbs_t[::-1], same[::-1]):
            cand = np.where(s, t, cand)
        agree = np.ones((h, w), bool)
        for t, s in zip(nbs_t, same):
            agree &= ~s | (t == cand)
        fix = editable & (cnt >= 3) & agree & (cand != tone) & (cand > -99)
        if not fix.any():
            break
        tone = np.where(fix, cand, tone)
    return tone


def shade(fr: Frame, mats: list[Material], light: Light, rim_color=None, rim_strength: float = 1.0,
          rim_ymax: float = 1e9, lit_edge_drop: int = 0, aa: bool = True, tex_phase=(0, 0),
          lit_boost: float = 1.0, norim_mats=()):
    """Resolve the G-buffer into RGBA colours + OpenGL normal map.  Returns (rgba, nmap, tone_idx).
    Extra passes (v2): deterministic material textures (fur / knit / felt / tweed), orphan-pixel cleanup
    of auto tones, and hand-style anti-aliasing of the dark outline at convex stair corners."""
    h, w = fr.h, fr.w
    occ = fr.mat >= 0
    Lk = _norm(light.key); Lr = _norm(light.rim)
    ndl = np.clip((fr.n * Lk).sum(-1), 0, 1)
    val = light.ambient + (1 - light.ambient) * ndl
    mbias = np.zeros((h, w), np.float32)
    maxt = np.full((h, w), 4, np.int16)
    mint = np.ones((h, w), np.int16)
    texo = np.zeros((h, w), np.float32)
    yy, xx = np.mgrid[0:h, 0:w]
    for i, m in enumerate(mats):
        sel = fr.mat == i
        mbias[sel] = m.bias
        maxt[sel] = 5 if m.glossy else m.max_tone
        mint[sel] = m.min_tone
        if m.texture in _TEX and sel.any():
            pat = _TEX[m.texture]
            texo[sel] = pat[(yy[sel] + tex_phase[1]) % 4, (xx[sel] + tex_phase[0]) % 4]
    val = val + mbias
    auto = np.ones((h, w), np.float32)
    for t in light.thresholds:
        auto += (val >= t)
    auto_px = np.isnan(fr.tone)
    rim_mark = fr.tone == RIM_TONE
    auto = np.clip(auto + texo, mint, maxt)
    tone = np.where(auto_px, np.minimum(auto, maxt), np.where(rim_mark, 3.0, fr.tone))
    tone = tone + fr.bias

    # contact shadows: (a) directional -- an occluding later part sits towards the key light;
    # (b) ambient occlusion around parts flagged `ao` (sleeves over the coat) in every direction.
    pad_part = np.pad(fr.part, 1, constant_values=-1)
    pad_cast = np.pad(fr.cast, 1)
    pad_ao = np.pad(fr.ao, 1)
    pad_mat = np.pad(fr.mat, 1, constant_values=-1)
    shadowed = np.zeros((h, w), bool)
    for dx, dy in light.shadow_dirs:
        nb_part = pad_part[1 + dy:1 + dy + h, 1 + dx:1 + dx + w]
        nb_cast = pad_cast[1 + dy:1 + dy + h, 1 + dx:1 + dx + w]
        shadowed |= occ & fr.recv & (nb_part > fr.part) & nb_cast
    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        nb_part = pad_part[1 + dy:1 + dy + h, 1 + dx:1 + dx + w]
        nb_ao = pad_ao[1 + dy:1 + dy + h, 1 + dx:1 + dx + w]
        shadowed |= occ & fr.recv & (nb_part > fr.part) & nb_ao
    tone = np.where(shadowed & ~fr.fixed, tone - 1, tone)
    # inner lines: an `inline` part darkens its own border pixels where a part behind it shows next to it
    inl = np.zeros((h, w), bool)
    for dx, dy in light.inline_dirs:
        nb_part = pad_part[1 + dy:1 + dy + h, 1 + dx:1 + dx + w]
        inl |= occ & fr.inline & (nb_part >= 0) & (nb_part < fr.part)
    tone = np.where(inl & ~fr.fixed, np.minimum(tone, 1), tone)
    # key-side edge light: separates sleeves / scarves / straps from the torso they overlap
    elit = np.zeros((h, w), bool)
    for dx, dy in light.lit_dirs[:2]:
        nb_part = pad_part[1 + dy:1 + dy + h, 1 + dx:1 + dx + w]
        elit |= occ & fr.edgelit & (nb_part >= 0) & (nb_part < fr.part)
    elit &= ~inl & ~fr.fixed
    # a crisp 1-px seam on the key side (tone 1) frames the part like a selective inner outline
    tone = np.where(elit, np.minimum(tone, 1), tone)
    tone = np.round(tone)
    tone = _clean_orphans(tone, fr.mat, auto_px & occ & ~fr.fixed & ~shadowed & ~inl & ~elit)

    # silhouette edges
    pad_occ = np.pad(occ, 1)

    def nb_empty(dx, dy):
        return ~pad_occ[1 + dy:1 + dy + h, 1 + dx:1 + dx + w]
    edge = occ & (nb_empty(1, 0) | nb_empty(-1, 0) | nb_empty(0, 1) | nb_empty(0, -1))
    lit_edge = np.zeros((h, w), bool)
    for dx, dy in light.lit_dirs:
        lit_edge |= nb_empty(dx, dy)
    rim_edge = np.zeros((h, w), bool)
    for dx, dy in light.rim_dirs:
        rim_edge |= nb_empty(dx, dy)
    down_edge = nb_empty(0, 1)
    ndr = (fr.n * Lr).sum(-1)
    outl = np.zeros((h, w), bool)
    for i, m in enumerate(mats):
        if m.outline:
            outl |= fr.mat == i
    outl &= edge & ~fr.fixed
    rows = np.arange(h)[:, None] * np.ones((1, w))
    norim_m = np.zeros((h, w), bool)
    for i, m in enumerate(mats):
        if not m.rim_ok:
            norim_m |= fr.mat == i
    rim_px = (outl & rim_edge & (ndr > 0.2) & ~down_edge & ~fr.norim & ~norim_m & (rows < rim_ymax)) | rim_mark
    lit_px = outl & lit_edge & ~rim_px & ~down_edge & (ndl > 0.42)
    dark_px = outl & ~rim_px & ~lit_px
    tone = np.where(dark_px, 0, tone)
    if aa:
        # hand AA: a dark outline pixel at a convex stair corner (two perpendicular empty neighbours and the
        # diagonal between them empty, but continuing edge on both other sides) is softened to tone 1 so
        # diagonal silhouettes read as smooth steps instead of jaggies.  Bottom (ground) corners stay dark.
        corner = np.zeros((h, w), bool)
        for (ax, ay), (bx, by) in (((1, 0), (0, -1)), ((-1, 0), (0, -1)), ((1, 0), (0, 1)), ((-1, 0), (0, 1))):
            c = nb_empty(ax, ay) & nb_empty(bx, by) & nb_empty(ax + bx, ay + by)
            c &= ~nb_empty(-ax, -ay) & ~nb_empty(-bx, -by)
            corner |= c
        soft = dark_px & corner & ~down_edge
        tone = np.where(soft, 1, tone)
    if lit_edge_drop:
        tone = np.where(lit_px, tone - lit_edge_drop, tone)
    if lit_boost:
        # crisp key-light edge: silhouette pixels facing the key get one tone brighter (capped per material)
        tone = np.where(lit_px & auto_px, np.minimum(tone + lit_boost, maxt + 0.0), tone)
    tone = np.clip(np.round(tone), 0, 5).astype(np.int16)

    rgba = np.zeros((h, w, 4), np.uint8)
    for i, m in enumerate(mats):
        sel = fr.mat == i
        if not sel.any():
            continue
        R = np.stack(m.ramp)
        rgba[sel] = R[np.clip(tone[sel], 0, len(R) - 1)]
        rc = m.rim if m.rim is not None else rim_color
        if rc is not None:
            rs = sel & rim_px
            if rs.any():
                base = R[3].astype(np.float32)
                k = 0.5 * rim_strength * m.rim_k
                rgba[rs] = np.clip(base * (1 - k) + np.asarray(rc, np.float32) * k, 0, 255).astype(np.uint8)
    n = fr.n.copy()
    n /= np.linalg.norm(n, axis=-1, keepdims=True) + 1e-9
    nm = np.zeros((h, w, 4), np.uint8)
    nm[..., :3] = np.clip(np.round((n * 0.5 + 0.5) * 255), 0, 255).astype(np.uint8)
    nm[..., 3] = np.where(occ, 255, 0)
    rgba[..., 3] = np.where(occ, 255, 0)
    rgba[~occ] = 0
    nm[~occ] = 0
    return rgba, nm, tone


# ----------------------------------------------------------------------------------- kinematics
def rot(v, deg):
    a = math.radians(deg)
    c, s = math.cos(a), math.sin(a)
    return (v[0] * c - v[1] * s, v[0] * s + v[1] * c)


def add(a, b):
    return (a[0] + b[0], a[1] + b[1])


def polar(origin, length, deg_from_down, forward: int = 1):
    """Point at `length` from origin; angle measured from straight down, positive = forward (+x)."""
    a = math.radians(deg_from_down)
    return (origin[0] + forward * math.sin(a) * length, origin[1] + math.cos(a) * length)


def ik2(hip, target, l1, l2, forward: int = 1):
    """Two-bone IK in the image plane; knee bends towards +forward x.  Returns (knee, ankle)."""
    dx, dy = target[0] - hip[0], target[1] - hip[1]
    d = math.hypot(dx, dy)
    d = max(1e-3, min(d, l1 + l2 - 1e-3))
    base = math.atan2(dy, dx)
    c = (l1 * l1 + d * d - l2 * l2) / (2 * l1 * d)
    a = math.acos(max(-1.0, min(1.0, c)))
    ang = base - forward * a
    knee = (hip[0] + math.cos(ang) * l1, hip[1] + math.sin(ang) * l1)
    dd = math.hypot(dx, dy)
    if dd > l1 + l2:
        ankle = (hip[0] + dx / dd * (l1 + l2), hip[1] + dy / dd * (l1 + l2))
    else:
        ankle = target
    return knee, ankle
