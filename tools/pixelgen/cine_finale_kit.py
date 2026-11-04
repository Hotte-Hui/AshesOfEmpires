"""cine_finale_kit -- shared pixel-art toolkit for the X1 finale montage (owner: trans-finale).

Original, deterministic pixel art for scenes/cinematics/finale (TECHNICAL_ARCHITECTURE §12.5).
Everything is drawn at 1:1 (one texel = one game pixel), on the scene palettes of pg.PALETTES, with
ordered (Bayer) dithering for light falloff.  No scaling, no rotation of finished pixels: hands, sleeves and
papers are rasterised fresh for every animation frame from their geometry.

Contents
  * palettes / ramps for Berlin (archive + berlin), Karsk and the map (sepia)
  * Lamp: screen-space light model (pool with cone cut-off, lambert on a height field)
  * shade(): tone -> ramp with Bayer dither; height-field helpers (capsules, tubes, domes)
  * arm(): sleeve + hand renderer (back of the hand seen from above, poses: flat / curl / grip / type)
  * pixel font (5x7 and 3x5), insignia masks (state eagle, swastika, hammer & sickle, neutral emblems)
  * atlas packer + JSON helpers
Seeds come from crc32 of names (never hash()).  Python: py -3 -P (Pillow + numpy).
"""
from __future__ import annotations

import json
import math
import os
import zlib
from typing import Sequence

import numpy as np
from PIL import Image

import pg

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
OUT = os.path.join(ROOT, 'assets', 'cinematics', 'finale')
H = pg.hx


def seed_of(name: str) -> int:
    return zlib.crc32(name.encode('utf-8')) & 0x7FFFFFFF


def R(*hexes) -> list:
    return [H(h) for h in hexes]


# ----------------------------------------------------------------------------------------- palettes
A = pg.PALETTES['archive']
B = pg.PALETTES['berlin']
K = pg.PALETTES['karsk']
S = pg.PALETTES['sepia']

# Berlin office at night (archive + berlin exterior).  Ramps run dark -> light.
BR = {
    'void':   R('#04090D', '#06151D', '#0B1C24', '#14272B'),
    'wall':   R('#04090D', '#06151D', '#0B1C24', '#14272B', '#1A2A2E', '#24373A', '#354448'),
    'desk':   R('#04090D', '#06151D', '#1A1210', '#2A1B16', '#3D2820', '#55372A', '#6E4A37', '#805C4E',
                '#9C7560', '#B57B59', '#D79A62'),
    'paper':  R('#0B1C24', '#14272B', '#354448', '#6E6A5C', '#8E8A78', '#B0AA93', '#CEC6AA', '#E6DEC2',
                '#F5EFDA'),
    'tracing': R('#0B1C24', '#14272B', '#354448', '#62716E', '#8E8A78', '#B0AA93', '#CEC6AA', '#E6DEC2'),
    'wool':   R('#04090D', '#06151D', '#1D2A3A', '#2B3C50', '#3E546B', '#58718A', '#7A93A8'),
    'skin':   R('#1A1210', '#2A1B16', '#3D2820', '#55372A', '#805C4E', '#9C7560', '#B57B59', '#D79A62',
                '#F2C27E'),
    'cuff':   R('#14272B', '#354448', '#62716E', '#8E8A78', '#B0AA93', '#CEC6AA', '#E6DEC2'),
    'metal':  R('#04090D', '#0B1C24', '#14272B', '#24373A', '#354448', '#4A5A5B', '#62716E', '#8E8A78',
                '#CEC6AA'),
    'brass':  R('#2A1B16', '#3D2820', '#6E3F22', '#9A5A2F', '#B57B59', '#D79A62', '#F2C27E', '#FFE3AA'),
    'black':  R('#04090D', '#06151D', '#0B1C24', '#14272B', '#1A2A2E', '#24373A', '#354448', '#4A5A5B'),
    'amber':  R('#6E3F22', '#9A5A2F', '#B57B59', '#D79A62', '#F2C27E', '#FFE3AA'),
    'lining': R('#120C14', '#1B1520', '#2A1B16', '#4A1712', '#7A2A26', '#A8382E', '#C8503C'),
    'ink':    R('#1A1C2A', '#2E3248'),
    'red':    R('#4A1712', '#7A2A26', '#A8382E', '#C8503C'),
    'violet': R('#120C14', '#1B1520', '#211623', '#2A2130', '#342F37', '#443B43', '#57494D'),
    'stamp':  R('#25202B', '#342F37', '#443B43', '#57494D'),           # violet office stamp ink
    'sky':    R('#120C14', '#1B1520', '#211623', '#2A2130', '#342F37', '#443B43'),
    'patina': R('#120C14', '#1E2E2C', '#2C4440', '#3E5D55', '#56776A', '#73927F'),
    'glow':   R('#5F4530', '#735145', '#8D5542', '#AF6C47', '#D07744', '#E5945A', '#F0AE6E', '#F4BA81',
                '#F8D2A0', '#FCE9C8'),
    'stone':  R('#120C14', '#1B1520', '#2A2130', '#4A3A35', '#5F4A40', '#7A5E4E', '#94735C'),
    'snow':   R('#443B43', '#57494D', '#6E6A73', '#8F8A92', '#B2ACB0', '#D2CCCB', '#ECE6E0'),
    'smoke':  R('#14272B', '#24373A', '#354448', '#4A5A5B', '#62716E', '#8E8A78', '#B0AA93'),
}

# Karsk signal box at night (karsk palette).
KR = {
    'void':   R('#05090F', '#0A1219', '#0E1A20', '#13252B'),
    'wall':   R('#05090F', '#0A1219', '#0E1A20', '#13252B', '#122126', '#1B3033', '#26403F', '#36534D'),
    'desk':   R('#05090F', '#0A1219', '#22180F', '#33251A', '#4A3626', '#634B35', '#7D6347', '#8D5542',
                '#AF6C47', '#C98A5C', '#DCA16E'),
    'paper':  R('#0A1219', '#13252B', '#3B3F3B', '#666A60', '#7F8275', '#9A9B8B', '#B8C7A8', '#DEE5DC',
                '#F1F4EC'),
    'ledger': R('#0A1219', '#13252B', '#3B3F3B', '#666A60', '#9A9B8B', '#C7D3BA', '#DCE2C8', '#FBE3AE'),
    'cover':  R('#05090F', '#0E1A20', '#2E1C1A', '#4A2A22', '#6B3B2C', '#8D5542', '#AF6C47'),
    'quilt':  R('#05090F', '#0A1219', '#122126', '#1B3033', '#26403F', '#36534D', '#4A675C', '#6C7A62'),
    'irina':  R('#05090F', '#0A1219', '#0E1A20', '#13252B', '#2A2D2C', '#3B3F3B', '#4F534C', '#666A60'),
    'skin':   R('#05090F', '#2E1C1A', '#4A2A22', '#6B3B2C', '#8D5542', '#AF6C47', '#BA775B', '#DCA16E',
                '#F0C487'),
    'metal':  R('#05090F', '#0A1219', '#13252B', '#2A2D2C', '#3B3F3B', '#4F534C', '#666A60', '#7F8275',
                '#9A9B8B', '#C4CFC8'),
    'brass':  R('#2E1C1A', '#4A2A22', '#6B3B2C', '#8D5542', '#AF6C47', '#C98A5C', '#DCA16E', '#F0C487',
                '#FBE3AE'),
    'glass':  R('#05090F', '#0E1A20', '#13252B', '#26403F', '#4A675C', '#7E8E8C', '#A3B1AD', '#DEE5DC'),
    'tea':    R('#2E1C1A', '#4A2A22', '#6B3B2C', '#8D5542', '#AF6C47', '#C98A5C'),
    'copper': R('#7A3E26', '#BA775B', '#DCA16E', '#F0C487', '#FBE3AE'),
    'green':  R('#05090F', '#0E1A20', '#122126', '#1B3033', '#26403F', '#36534D', '#4A675C'),
    'enamel': R('#05090F', '#0E1A20', '#1B3033', '#26403F', '#36534D', '#4A675C', '#6C7A62', '#839378'),
    'red':    R('#2E1C1A', '#4A2A22', '#7A2218', '#A8382E', '#C8503C'),
    'snow':   R('#13252B', '#26403F', '#4A675C', '#7E8E8C', '#A3B1AD', '#C4CFC8', '#DEE5DC', '#F1F4EC'),
    'sky':    R('#05090F', '#0A1219', '#0E1A20', '#13252B', '#122126', '#1B3033'),
    'steam':  R('#13252B', '#26403F', '#4F534C', '#7F8275', '#A3B1AD', '#C4CFC8', '#DEE5DC'),
    'stone':  R('#05090F', '#0A1219', '#2A2D2C', '#3B3F3B', '#4F534C', '#666A60', '#7F8275'),
    'rust':   R('#05090F', '#2E1C1A', '#4A2A22', '#6B3B2C', '#8D5542', '#AF6C47', '#C98A5C'),
    'fire':   R('#7A3E26', '#BA775B', '#DCA16E', '#F0C487', '#FBE3AE'),
    'stamp':  R('#2E1C1A', '#4A2A22', '#7A2218', '#A8382E'),            # red-violet ledger stamp
    'signal_g': R('#122126', '#36534D', '#4A675C', '#9DAF91', '#DCE2C8'),
    'signal_r': R('#2E1C1A', '#7A2218', '#A8382E', '#C8503C', '#FBE3AE'),
}

# Map (sepia + red C-17).
MR = {
    'tone':  [H(c) for c in S['tone']],
    'red':   [H(c) for c in S['red']],
    'paper_dark': R('#1E1C1D', '#2A2829', '#343232', '#494545', '#5E5A54', '#68635B'),
}


def smoothstep(e0, e1, x):
    t = np.clip((np.asarray(x, np.float32) - e0) / (e1 - e0 + 1e-9), 0.0, 1.0)
    return t * t * (3 - 2 * t)


# ----------------------------------------------------------------------------------------- canvas helpers
class Canvas(pg.Layer):
    """pg.Layer plus helpers used by the finale generators (tone painting with a light model)."""

    def grid(self):
        yy, xx = np.mgrid[0:self.h, 0:self.w].astype(np.float32)
        return xx + 0.5, yy + 0.5

    def paint(self, mask: np.ndarray, tone: np.ndarray, ramp: Sequence, x0: int = 0, y0: int = 0,
              dither: bool = True, hgt=None):
        """Fill mask (full-canvas or at x0,y0) with ramp colours chosen by tone in [0,1]."""
        self.tone_fill(mask, x0, y0, np.asarray(tone, np.float32), ramp, dither=dither, hgt=hgt)

    def put_mask(self, mask: np.ndarray, col, x0: int = 0, y0: int = 0):
        self._put(mask, x0, y0, col)


def bayer_full(w: int, h: int) -> np.ndarray:
    return pg.bayer(w, h)


def tone_to_ramp(tone: np.ndarray, ramp: Sequence, x0: int = 0, y0: int = 0, dither: bool = True) -> np.ndarray:
    """Vectorised tone -> RGBA via ordered dither (aligned to absolute canvas coords)."""
    n = len(ramp) - 1
    T = np.clip(tone, 0, 1) * n
    idx = np.floor(T).astype(int)
    if dither:
        thr = pg.bayer(tone.shape[1], tone.shape[0], x0, y0)
        idx = idx + ((T - idx) > thr)
    idx = np.clip(idx, 0, n)
    carr = np.stack([np.asarray(c, np.uint8) for c in ramp])
    return carr[idx]


def capsule_height(xx, yy, ax, ay, bx, by, r):
    """Height of a rounded rod (radius r) from A to B, sampled at xx,yy (0 outside). Returns (h, t)."""
    vx, vy = bx - ax, by - ay
    L2 = vx * vx + vy * vy + 1e-9
    t = np.clip(((xx - ax) * vx + (yy - ay) * vy) / L2, 0.0, 1.0)
    px, py = ax + t * vx, ay + t * vy
    d2 = (xx - px) ** 2 + (yy - py) ** 2
    hgt = np.sqrt(np.clip(r * r - d2, 0, None))
    return hgt, t


def poly_mask_full(w, h, pts) -> np.ndarray:
    L = pg.Layer(w, h)
    m, x0, y0 = L.poly_mask(pts)
    out = np.zeros((h, w), bool)
    X0, Y0 = max(0, x0), max(0, y0)
    X1, Y1 = min(w, x0 + m.shape[1]), min(h, y0 + m.shape[0])
    if X1 > X0 and Y1 > Y0:
        out[Y0:Y1, X0:X1] = m[Y0 - y0:Y1 - y0, X0 - x0:X1 - x0]
    return out


def ellipse_full(w, h, cx, cy, rx, ry) -> np.ndarray:
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    return (((xx + 0.5 - cx) / max(rx, 0.5)) ** 2 + ((yy + 0.5 - cy) / max(ry, 0.5)) ** 2) <= 1.0


def normals_from_height(hgt: np.ndarray, strength: float = 1.0):
    p = np.pad(hgt, 1, mode='edge')
    gx = (p[1:-1, 2:] - p[1:-1, :-2]) * 0.5 * strength
    gy = (p[2:, 1:-1] - p[:-2, 1:-1]) * 0.5 * strength
    n = np.stack([-gx, -gy, np.ones_like(hgt)], -1)
    n /= np.linalg.norm(n, axis=-1, keepdims=True)
    return n          # screen space: +x right, +y DOWN, +z towards the viewer


def outline_of(mask: np.ndarray, diagonal: bool = False) -> np.ndarray:
    """Pixels of mask that touch the outside (edge pixels)."""
    p = np.pad(mask, 1)
    inner = p[:-2, 1:-1] & p[2:, 1:-1] & p[1:-1, :-2] & p[1:-1, 2:]
    if diagonal:
        inner &= p[:-2, :-2] & p[:-2, 2:] & p[2:, :-2] & p[2:, 2:]
    return mask & ~inner


def dilate(mask: np.ndarray, r: int = 1) -> np.ndarray:
    out = mask.copy()
    for _ in range(r):
        p = np.pad(out, 1)
        out = out | p[:-2, 1:-1] | p[2:, 1:-1] | p[1:-1, :-2] | p[1:-1, 2:]
    return out


def erode(mask: np.ndarray, r: int = 1) -> np.ndarray:
    out = mask.copy()
    for _ in range(r):
        p = np.pad(out, 1)
        out = out & p[:-2, 1:-1] & p[2:, 1:-1] & p[1:-1, :-2] & p[1:-1, 2:]
    return out


def shift(mask: np.ndarray, dx: int, dy: int) -> np.ndarray:
    out = np.zeros_like(mask)
    h, w = mask.shape
    xs0, xs1 = max(0, -dx), min(w, w - dx)
    ys0, ys1 = max(0, -dy), min(h, h - dy)
    out[ys0 + dy:ys1 + dy, xs0 + dx:xs1 + dx] = mask[ys0:ys1, xs0:xs1]
    return out


def clean_singletons(rgba: np.ndarray, alpha_only: bool = False) -> np.ndarray:
    """Remove orphan pixels (no 4-neighbour of the same colour) by taking the majority neighbour colour."""
    c = rgba.astype(np.int64)
    key = (c[..., 0] << 24) | (c[..., 1] << 16) | (c[..., 2] << 8) | c[..., 3]
    p = np.pad(key, 1, mode='edge')
    nb = [p[:-2, 1:-1], p[2:, 1:-1], p[1:-1, :-2], p[1:-1, 2:]]
    same = sum((n == key).astype(int) for n in nb)
    orphan = (same == 0) & (c[..., 3] > 0)
    out = rgba.copy()
    if not orphan.any():
        return out
    ys, xs = np.nonzero(orphan)
    for y, x in zip(ys, xs):
        cands = {}
        for dy, dx in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            yy, xx = y + dy, x + dx
            if 0 <= yy < rgba.shape[0] and 0 <= xx < rgba.shape[1]:
                k = int(key[yy, xx])
                if (k & 0xFF) == 0:
                    continue
                cands[k] = cands.get(k, 0) + 1
        if cands:
            k = max(cands.items(), key=lambda kv: kv[1])[0]
            out[y, x] = [(k >> 24) & 255, (k >> 16) & 255, (k >> 8) & 255, k & 255]
    return out


# ----------------------------------------------------------------------------------------- light model
class Lamp:
    """Screen-space desk lamp.  (sx, sy) = screen point on the desk right under the bulb; z = bulb height
    in px; radius = pool radius (px, desk plane, x-units); depth = desk foreshortening (screen y per desk y).
    tone() returns light in [0, ~1.2] for points/normals."""

    def __init__(self, sx, sy, z, radius, depth=0.62, power=1.0, cone=1.0, aim=(0.0, 0.0)):
        self.sx, self.sy, self.z = float(sx), float(sy), float(z)
        self.radius = float(radius)
        self.depth = float(depth)
        self.power = float(power)
        self.cone = float(cone)
        self.aim = aim                   # pool centre offset from the foot point (screen px)

    def pool(self, X, Y, lift: float = 0.0):
        """Irradiance on a horizontal surface at screen (X, Y) lifted by `lift` px."""
        cx, cy = self.sx + self.aim[0], self.sy + self.aim[1]
        dx = (X - cx)
        dy = (Y + lift - cy) / self.depth
        r = np.sqrt(dx * dx + dy * dy) / self.radius
        core = 1.0 / (1.0 + 2.6 * r * r)
        edge = smoothstep(1.18 * self.cone, 0.78 * self.cone, r)
        return self.power * core * (0.18 + 0.82 * edge)

    def ldir(self, X, Y, lift: float = 0.0):
        dx = self.sx - X
        dy = (self.sy - (Y + lift)) / self.depth
        dz = np.full_like(np.asarray(dx, np.float32), self.z - lift)
        n = np.sqrt(dx * dx + dy * dy + dz * dz) + 1e-6
        # convert desk-space (x, depth-towards-viewer, up) into screen-ish (x, y-down, z-towards viewer):
        # a surface facing up on the desk faces the viewer at ~55 deg, so up ~= +z and -y.
        lx = dx / n
        ly = dy / n * 0.75 - dz / n * 0.35
        lz = dz / n * 0.9 + 0.1
        m = np.sqrt(lx * lx + ly * ly + lz * lz) + 1e-6
        return lx / m, ly / m, lz / m

    def lambert(self, X, Y, nrm, lift: float = 0.0, wrap: float = 0.25):
        lx, ly, lz = self.ldir(X, Y, lift)
        d = nrm[..., 0] * lx + nrm[..., 1] * ly + nrm[..., 2] * lz
        return np.clip((d + wrap) / (1 + wrap), 0, 1)


# ----------------------------------------------------------------------------------------- arms & hands
class HandPose:
    """Back of a hand seen from above.  Local frame: wrist centre at origin, fingers along +x.
    side='R' puts the thumb on the -y side (right hand seen from above, fingers pointing up-screen ->
    thumb on the left)."""

    def __init__(self, curl=0.0, spread=0.0, thumb='side', curls=None, tilt=0.0, grip=False, lifted=None):
        self.curl = curl
        self.spread = spread
        self.thumb = thumb
        self.curls = curls or [None, None, None, None]
        self.tilt = tilt        # foreshortening along the hand axis (0 flat .. 0.5 strongly tilted down)
        self.grip = grip
        self.lifted = lifted or [0, 0, 0, 0]


def _rot(px, py, ang):
    c, s = math.cos(ang), math.sin(ang)
    return px * c - py * s, px * s + py * c


def render_arm(w, h, wrist, ang, length, pose: HandPose, side: str, entry, sleeve_ramp, skin_ramp,
               lamp: Lamp, cuff_ramp=None, quilt: bool = False, sleeve_w=(30.0, 40.0), seed: int = 0,
               bend: float = 0.0, lift: float = 6.0, outline_col=None, hand_scale_w: float = 1.0,
               cuff_style: str = 'shirt', fold_phase: float = 0.0, ambient: float = 0.10, depth: float = 0.66,
               hand_only: bool = False, sleeve_dither: bool = True):
    """Rasterise one arm (sleeve from `entry` to the wrist, plus the hand) into an RGBA array (h, w).
    The hand is modelled in the desk plane (x right, y towards the viewer) and projected with the desk
    foreshortening `depth`; `ang` is the desk-plane direction wrist -> fingertips (radians, 0 = right,
    -pi/2 = away from the viewer).  length = wrist to middle fingertip (desk px).  Returns (rgba, mask)."""
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    xx += 0.5
    yy += 0.5
    sgn = 1.0 if side == 'R' else -1.0
    L = float(length)
    Wd = L * 0.42 * hand_scale_w
    fl = 1.0 - pose.tilt

    def P(lx, ly):
        rx, ry = _rot(lx * fl, ly * sgn, ang)
        return wrist[0] + rx, wrist[1] + ry * depth

    parts = []
    palm_len = L * 0.54
    q = [P(-1.5, -Wd * 0.36), P(palm_len * 0.55, -Wd * 0.50), P(palm_len, -Wd * 0.47),
         P(palm_len + 1.0, -Wd * 0.15), P(palm_len + 1.0, Wd * 0.18), P(palm_len, Wd * 0.47),
         P(palm_len * 0.55, Wd * 0.48), P(-1.5, Wd * 0.37)]
    pm = poly_mask_full(w, h, q)
    cxp, cyp = P(palm_len * 0.52, -Wd * 0.05)
    dpx, dpy = (xx - cxp), (yy - cyp) / depth
    rr = np.sqrt(dpx * dpx + dpy * dpy) / (Wd * 0.62)
    hb = np.where(pm, Wd * 0.22 * np.sqrt(np.clip(1.25 - rr * rr * 0.55, 0.08, None)), 0)
    parts.append((hb, 1))
    f_off = [-0.355, -0.115, 0.125, 0.345]
    f_len = [0.40, 0.45, 0.42, 0.33]
    f_rad = [0.054, 0.056, 0.052, 0.045]
    tips, knuckles, pips = [], [], []
    for i in range(4):
        c = pose.curls[i] if pose.curls[i] is not None else pose.curl
        ln = L * f_len[i] * (1.0 - 0.58 * c)
        rad = L * f_rad[i] * hand_scale_w
        oy = Wd * f_off[i] * (1.0 + pose.spread * 0.5)
        a_sp = f_off[i] * pose.spread * 0.8
        base = (palm_len - rad * 0.6, oy)
        dx_, dy_ = math.cos(a_sp), math.sin(a_sp)
        tip = (base[0] + dx_ * ln, base[1] + dy_ * ln)
        A_ = P(*base)
        B_ = P(*tip)
        hf, tpar = capsule_height(xx, yy, A_[0], A_[1], B_[0], B_[1], rad)
        hf = np.where(hf > 0, hf + Wd * 0.10 * (1.0 - 0.7 * c * tpar) + pose.lifted[i] * 0.8, 0)
        parts.append((hf, 10 + i))
        tips.append((B_, rad, c))
        knuckles.append(P(palm_len - 0.5, oy))
        pips.append((P(base[0] + dx_ * ln * 0.45, base[1] + dy_ * ln * 0.45), rad, c))
    if pose.thumb != 'hidden':
        if pose.thumb == 'side':
            t0, t1 = (L * 0.14, -Wd * 0.44), (L * 0.50, -Wd * 0.70)
        elif pose.thumb == 'under':
            t0, t1 = (L * 0.16, -Wd * 0.42), (L * 0.40, -Wd * 0.36)
        elif pose.thumb == 'out':
            t0, t1 = (L * 0.12, -Wd * 0.46), (L * 0.42, -Wd * 1.00)
        else:   # 'pinch' -- thumb tip meets the index tip
            t0, t1 = (L * 0.14, -Wd * 0.44), (L * 0.62, -Wd * 0.46)
        A_ = P(*t0)
        B_ = P(*t1)
        rad = L * 0.064 * hand_scale_w
        ht, tpar = capsule_height(xx, yy, A_[0], A_[1], B_[0], B_[1], rad)
        ht = np.where(ht > 0, ht + Wd * 0.08, 0)
        parts.append((ht * (0.8 if pose.thumb == 'under' else 1.0), 20))
        tips.append((B_, rad, 0.0))
    hgt = np.zeros((h, w), np.float32)
    owner = np.zeros((h, w), np.int32)
    for hh, pid in parts:
        sel = hh > hgt
        hgt[sel] = hh[sel]
        owner[sel] = pid
    hand = hgt > 0.05
    sleeve = np.zeros((h, w), bool)
    sl_h = np.zeros((h, w), np.float32)
    sl_t = np.full((h, w), -1.0, np.float32)
    sl_u = np.zeros((h, w), np.float32)
    total = 1.0
    if not hand_only:
        back = P(-L * 0.04, 0.0)
        mid = ((back[0] + entry[0]) * 0.5 + bend * math.cos(ang + math.pi / 2),
               (back[1] + entry[1]) * 0.5 + bend * math.sin(ang + math.pi / 2))
        path = pg.bezier([back, mid, entry], n=90)
        total = sum(math.dist(a, b) for a, b in zip(path[:-1], path[1:])) + 1e-6
        acc = 0.0
        for a, b in zip(path[:-1], path[1:]):
            seg = math.dist(a, b)
            t_mid = (acc + seg * 0.5) / total
            acc += seg
            grow = min(1.0, (t_mid * total) / 60.0)
            rw = (sleeve_w[0] + (sleeve_w[1] - sleeve_w[0]) * grow) * 0.5 * hand_scale_w
            hh, tp = capsule_height(xx, yy, a[0], a[1], b[0], b[1], rw)
            sel = hh > sl_h
            sl_h[sel] = hh[sel]
            sl_t[sel] = (acc - seg * (1 - tp[sel])) / total
            vx, vy = b[0] - a[0], b[1] - a[1]
            nlen = math.hypot(vx, vy) + 1e-6
            sl_u[sel] = ((xx[sel] - a[0]) * (-vy) + (yy[sel] - a[1]) * vx) / nlen / rw
        sleeve = (sl_h > 0.05) & ~hand
    rgba = np.zeros((h, w, 4), np.uint8)
    if sleeve.any():
        n_s = normals_from_height(sl_h * 0.9)
        lam = lamp.lambert(xx, yy, n_s, lift=lift + 6, wrap=0.15)
        pool = lamp.pool(xx, yy, lift=lift + 6)
        along = sl_t * total
        if quilt:
            qv = np.sin(along / 5.5 * math.pi + fold_phase + sl_u * 0.35)
            fold = np.where(qv > 0.80, -0.20, 0.0) + np.where((qv > 0.25) & (qv <= 0.80), 0.06, 0.0)
        else:
            rng = np.random.default_rng(seed)
            ph = rng.uniform(0, 6.28)
            f1 = np.sin(along / 11.0 + sl_u * 1.9 + ph)
            f2 = np.sin(along / 7.0 - sl_u * 2.4 + ph * 1.7)
            fold = np.where(f1 > 0.88, -0.17, 0.0) + np.where((f2 > 0.9) & (np.abs(sl_u) < 0.6), 0.07, 0.0)
        tone = ambient + 0.95 * lam * pool + fold
        tone = tone - 0.30 * np.clip(np.abs(sl_u) - 0.72, 0, 1)
        col = tone_to_ramp(np.clip(tone, 0, 1), sleeve_ramp, dither=sleeve_dither)
        rgba[sleeve] = col[sleeve]
        if cuff_style == 'shirt' and cuff_ramp is not None:
            shirt = sleeve & (along < 3.0)
            ctone = ambient + 1.05 * lam * pool + 0.12
            ccol = tone_to_ramp(np.clip(ctone, 0, 1), cuff_ramp, dither=False)
            rgba[shirt] = ccol[shirt]
            hem = sleeve & (along >= 3.0) & (along < 4.6)
            dark = tone_to_ramp(np.clip(tone - 0.20, 0, 1), sleeve_ramp, dither=False)
            rgba[hem] = dark[hem]
            sleeve_end = sleeve & (along >= 4.6) & (along < 6.0)
            lite = tone_to_ramp(np.clip(tone + 0.10, 0, 1), sleeve_ramp, dither=False)
            rgba[sleeve_end] = lite[sleeve_end]
        elif cuff_style == 'knit':
            knit = sleeve & (along < 6.0)
            ktone = tone - 0.05 + 0.14 * (np.sin(sl_u * 10.0) > 0.2)
            kcol = tone_to_ramp(np.clip(ktone, 0, 1), sleeve_ramp, dither=False)
            rgba[knit] = kcol[knit]
            seam = sleeve & (along >= 6.0) & (along < 7.2)
            dk = tone_to_ramp(np.clip(tone - 0.22, 0, 1), sleeve_ramp, dither=False)
            rgba[seam] = dk[seam]
    if hand.any():
        n_h = normals_from_height(hgt * 0.75)
        lam = lamp.lambert(xx, yy, n_h, lift=lift, wrap=0.2)
        pool = lamp.pool(xx, yy, lift=lift)
        tone = ambient * 0.8 + 1.0 * lam * pool
        for (tp_, rad, c) in tips:
            if c > 0.35:
                dd = np.sqrt((xx - tp_[0]) ** 2 + (yy - tp_[1]) ** 2)
                tone = np.where(dd < rad * 1.1, tone - 0.12 * c, tone)
        col = tone_to_ramp(np.clip(tone, 0, 1), skin_ramp, dither=False)
        p = np.pad(owner, 1, mode='edge')
        crease = hand & (owner >= 10) & ((((p[1:-1, 2:] != owner) & (p[1:-1, 2:] >= 10))) |
                                         (((p[2:, 1:-1] != owner) & (p[2:, 1:-1] >= 10))))
        dark = tone_to_ramp(np.clip(tone - 0.24, 0, 1), skin_ramp, dither=False)
        col[crease] = dark[crease]
        for (kx, ky) in knuckles:
            for ddx in (0, 1):
                ix, iy = int(kx) + ddx, int(ky)
                if 0 <= iy < h and 0 <= ix < w and hand[iy, ix]:
                    t_ = float(np.clip(tone[iy, ix] + 0.13, 0, 1))
                    col[iy, ix] = tone_to_ramp(np.array([[t_]], np.float32), skin_ramp, dither=False)[0, 0]
        for (pp, rad, c) in pips:
            if c > 0.25:
                ix, iy = int(pp[0]), int(pp[1])
                if 0 <= iy < h and 0 <= ix < w and hand[iy, ix]:
                    t_ = float(np.clip(tone[iy, ix] + 0.12, 0, 1))
                    col[iy, ix] = tone_to_ramp(np.array([[t_]], np.float32), skin_ramp, dither=False)[0, 0]
        for (tp_, rad, c) in tips:
            if c < 0.35:
                nx_ = tp_[0] - math.cos(ang) * rad * 0.8
                ny_ = tp_[1] - math.sin(ang) * rad * 0.8 * depth
                ix, iy = int(nx_), int(ny_)
                if 0 <= iy < h and 0 <= ix < w and hand[iy, ix]:
                    t_ = float(np.clip(tone[iy, ix] + 0.16, 0, 1))
                    col[iy, ix] = tone_to_ramp(np.array([[t_]], np.float32), skin_ramp, dither=False)[0, 0]
        rgba[hand] = col[hand]
    mask = hand | sleeve
    edge = outline_of(mask)
    if edge.any():
        lx, ly, lz = lamp.ldir(xx, yy, lift)
        p = np.pad(mask, 1)
        ox = p[1:-1, 2:].astype(np.float32) - p[1:-1, :-2]
        oy = p[2:, 1:-1].astype(np.float32) - p[:-2, 1:-1]
        facing = -(ox * lx + oy * ly)
        rgba[edge & hand & (facing <= 0.25)] = np.asarray(skin_ramp[1], np.uint8)
        rgba[edge & sleeve & (facing <= 0.25)] = np.asarray(sleeve_ramp[1], np.uint8)
        if outline_col is not None:
            rgba[edge & (facing <= -0.5)] = np.asarray(outline_col, np.uint8)
    rgba[..., 3] = np.where(mask, 255, 0).astype(np.uint8)
    return rgba, mask


# ----------------------------------------------------------------------------------------- pixel fonts
FONT5 = {   # 5x7 caps
    'A': ['.###.', '#...#', '#...#', '#####', '#...#', '#...#', '#...#'],
    'B': ['####.', '#...#', '#...#', '####.', '#...#', '#...#', '####.'],
    'C': ['.###.', '#...#', '#....', '#....', '#....', '#...#', '.###.'],
    'D': ['####.', '#...#', '#...#', '#...#', '#...#', '#...#', '####.'],
    'E': ['#####', '#....', '#....', '####.', '#....', '#....', '#####'],
    'F': ['#####', '#....', '#....', '####.', '#....', '#....', '#....'],
    'G': ['.###.', '#...#', '#....', '#.###', '#...#', '#...#', '.###.'],
    'H': ['#...#', '#...#', '#...#', '#####', '#...#', '#...#', '#...#'],
    'I': ['###', '.#.', '.#.', '.#.', '.#.', '.#.', '###'],
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
    'V': ['#...#', '#...#', '#...#', '#...#', '.#.#.', '.#.#.', '..#..'],
    'W': ['#...#', '#...#', '#...#', '#.#.#', '#.#.#', '##.##', '#...#'],
    'Z': ['#####', '....#', '...#.', '..#..', '.#...', '#....', '#####'],
    '0': ['.###.', '#...#', '#..##', '#.#.#', '##..#', '#...#', '.###.'],
    '1': ['.#.', '##.', '.#.', '.#.', '.#.', '.#.', '###'],
    '2': ['.###.', '#...#', '....#', '...#.', '..#..', '.#...', '#####'],
    '3': ['####.', '....#', '....#', '.###.', '....#', '....#', '####.'],
    '4': ['...#.', '..##.', '.#.#.', '#..#.', '#####', '...#.', '...#.'],
    '5': ['#####', '#....', '####.', '....#', '....#', '#...#', '.###.'],
    '6': ['.###.', '#....', '#....', '####.', '#...#', '#...#', '.###.'],
    '7': ['#####', '....#', '...#.', '..#..', '.#...', '.#...', '.#...'],
    '8': ['.###.', '#...#', '#...#', '.###.', '#...#', '#...#', '.###.'],
    '9': ['.###.', '#...#', '#...#', '.####', '....#', '....#', '.###.'],
    '-': ['...', '...', '...', '###', '...', '...', '...'],
    '.': ['.', '.', '.', '.', '.', '.', '#'],
    ':': ['.', '.', '#', '.', '#', '.', '.'],
    ' ': ['..', '..', '..', '..', '..', '..', '..'],
    # Cyrillic used on Karsk props
    'Л': ['..###', '.#..#', '.#..#', '.#..#', '.#..#', '#...#', '#...#'],
    'Я': ['.####', '#...#', '#...#', '.####', '..#.#', '.#..#', '#...#'],
    'Ж': ['#.#.#', '#.#.#', '.###.', '..#..', '.###.', '#.#.#', '#.#.#'],
    'Д': ['.###.', '.#.#.', '.#.#.', '.#.#.', '.#.#.', '#####', '#...#'],
    'Г': ['#####', '#....', '#....', '#....', '#....', '#....', '#....'],
    'П': ['#####', '#...#', '#...#', '#...#', '#...#', '#...#', '#...#'],
    'Ц': ['#..#.', '#..#.', '#..#.', '#..#.', '#..#.', '#####', '....#'],
    'Ы': ['#...#', '#...#', '#...#', '##..#', '#.#.#', '#.#.#', '##..#'],
    'И': ['#...#', '#...#', '#..##', '#.#.#', '##..#', '#...#', '#...#'],
}

FONT3 = {   # 3x5 caps for tiny labels
    'A': ['.#.', '#.#', '###', '#.#', '#.#'], 'B': ['##.', '#.#', '##.', '#.#', '##.'],
    'C': ['.##', '#..', '#..', '#..', '.##'], 'D': ['##.', '#.#', '#.#', '#.#', '##.'],
    'E': ['###', '#..', '##.', '#..', '###'], 'F': ['###', '#..', '##.', '#..', '#..'],
    'G': ['.##', '#..', '#.#', '#.#', '.##'], 'H': ['#.#', '#.#', '###', '#.#', '#.#'],
    'I': ['###', '.#.', '.#.', '.#.', '###'], 'K': ['#.#', '#.#', '##.', '#.#', '#.#'],
    'L': ['#..', '#..', '#..', '#..', '###'], 'M': ['#.#', '###', '###', '#.#', '#.#'],
    'N': ['##.', '#.#', '#.#', '#.#', '#.#'], 'O': ['.#.', '#.#', '#.#', '#.#', '.#.'],
    'P': ['##.', '#.#', '##.', '#..', '#..'], 'R': ['##.', '#.#', '##.', '#.#', '#.#'],
    'S': ['.##', '#..', '.#.', '..#', '##.'], 'T': ['###', '.#.', '.#.', '.#.', '.#.'],
    'U': ['#.#', '#.#', '#.#', '#.#', '.#.'], 'V': ['#.#', '#.#', '#.#', '.#.', '.#.'],
    'W': ['#.#', '#.#', '###', '###', '#.#'], 'Z': ['###', '..#', '.#.', '#..', '###'],
    'Ä': ['#.#', '.#.', '#.#', '###', '#.#'], 'Ü': ['#.#', '...', '#.#', '#.#', '.#.'],
    '0': ['.#.', '#.#', '#.#', '#.#', '.#.'], '1': ['.#.', '##.', '.#.', '.#.', '###'],
    '2': ['##.', '..#', '.#.', '#..', '###'], '3': ['##.', '..#', '.#.', '..#', '##.'],
    '4': ['#.#', '#.#', '###', '..#', '..#'], '5': ['###', '#..', '##.', '..#', '##.'],
    '6': ['.##', '#..', '###', '#.#', '.#.'], '7': ['###', '..#', '.#.', '.#.', '.#.'],
    '8': ['.#.', '#.#', '.#.', '#.#', '.#.'], '9': ['.#.', '#.#', '.##', '..#', '##.'],
    '-': ['...', '...', '###', '...', '...'], '.': ['.', '.', '.', '.', '#'],
    ' ': ['.', '.', '.', '.', '.'], '/': ['..#', '..#', '.#.', '#..', '#..'],
    'К': ['#.#', '#.#', '##.', '#.#', '#.#'], 'Р': ['##.', '#.#', '##.', '#..', '#..'],
    'С': ['.##', '#..', '#..', '#..', '.##'], 'П': ['###', '#.#', '#.#', '#.#', '#.#'],
    'М': ['#.#', '###', '###', '#.#', '#.#'], 'Т': ['###', '.#.', '.#.', '.#.', '.#.'],
    'Б': ['###', '#..', '##.', '#.#', '##.'], 'Л': ['.##', '#.#', '#.#', '#.#', '#.#'],
    'Г': ['###', '#..', '#..', '#..', '#..'], 'Д': ['.#.', '#.#', '#.#', '###', '#.#'],
    'Н': ['#.#', '#.#', '###', '#.#', '#.#'], 'О': ['.#.', '#.#', '#.#', '#.#', '.#.'],
    'Е': ['###', '#..', '##.', '#..', '###'], 'А': ['.#.', '#.#', '###', '#.#', '#.#'],
    'Я': ['.##', '#.#', '.##', '#.#', '#.#'], 'Ж': ['#.#', '###', '.#.', '###', '#.#'],
    'Ы': ['#.#', '#.#', '###', '#.#', '##.'],
}


def text_mask(txt: str, font: dict, spacing: int = 1) -> np.ndarray:
    glyphs = [font.get(ch, font.get(ch.upper(), font[' '])) for ch in txt]
    hgt = len(glyphs[0]) if glyphs else 0
    wdt = sum(len(g[0]) + spacing for g in glyphs) - spacing if glyphs else 0
    m = np.zeros((hgt, max(1, wdt)), bool)
    x = 0
    for g in glyphs:
        for r, row in enumerate(g):
            for c, ch in enumerate(row):
                if ch == '#':
                    m[r, x + c] = True
        x += len(g[0]) + spacing
    return m


def blit_mask(rgba: np.ndarray, mask: np.ndarray, x: int, y: int, col) -> None:
    h, w = rgba.shape[:2]
    mh, mw = mask.shape
    X0, Y0 = max(0, x), max(0, y)
    X1, Y1 = min(w, x + mw), min(h, y + mh)
    if X1 <= X0 or Y1 <= Y0:
        return
    m = mask[Y0 - y:Y1 - y, X0 - x:X1 - x]
    rgba[Y0:Y1, X0:X1][m] = np.asarray(col, np.uint8)


# ----------------------------------------------------------------------------------------- insignia
def raster(fn, w: int, h: int, sub: int = 8, thr: float = 0.45) -> np.ndarray:
    """Supersampled rasterisation of an implicit shape fn(x, y) -> bool (x,y in pixel units)."""
    ys, xs = np.mgrid[0:h * sub, 0:w * sub].astype(np.float32)
    xs = (xs + 0.5) / sub
    ys = (ys + 0.5) / sub
    v = fn(xs, ys).astype(np.float32)
    v = v.reshape(h, sub, w, sub).mean(axis=(1, 3))
    return v >= thr


def swastika_mask(size: int, thick: float = 0.2, thr: float = 0.45) -> np.ndarray:
    """Hakenkreuz on point (45 deg), right-facing (hooks clockwise), as used by the NS state.
    size = bounding box in px."""
    c = size / 2.0
    s = size / 2.0 / 1.41421356 * 0.98      # half-extent of the unrotated cross

    def fn(x, y):
        # rotate by -45 deg into the upright frame
        u = ((x - c) + (y - c)) / 1.41421356
        v = (-(x - c) + (y - c)) / 1.41421356
        t = s * thick
        a = s
        bar_v = (np.abs(u) <= t) & (np.abs(v) <= a)
        bar_h = (np.abs(v) <= t) & (np.abs(u) <= a)
        # hooks (clockwise): top arm (v=-a) goes +u; right arm (u=+a) goes +v; bottom (v=+a) goes -u;
        # left (u=-a) goes -v.
        h1 = (np.abs(v + a) <= t) & (u >= -t) & (u <= a)
        h2 = (np.abs(u - a) <= t) & (v >= -t) & (v <= a)
        h3 = (np.abs(v - a) <= t) & (u <= t) & (u >= -a)
        h4 = (np.abs(u + a) <= t) & (v <= t) & (v >= -a)
        return bar_v | bar_h | h1 | h2 | h3 | h4
    return raster(fn, size, size, thr=thr)


def _mask(rows: str) -> np.ndarray:
    lines = [r for r in rows.strip('\n').split('\n')]
    w = max(len(r) for r in lines)
    m = np.zeros((len(lines), w), bool)
    for y, r in enumerate(lines):
        for x, ch in enumerate(r):
            m[y, x] = ch == '#'
    return m


# State eagle (Hoheitszeichen of the Reich ministries: head to its right = viewer's left, wings spread
# with straight upper edges, wreath under the talons).  Hand-pixelled, 23 x 15.  'o' marks the wreath ring.
EAGLE_23 = """
.........##............
........####...........
.......##.##...........
.......#####...........
########.###.##########
.###########.#########.
..##########.########..
...#########.#######...
....######.#.######....
......####.#.####......
..........###..........
.........#####.........
..........#.#..........
.........#...#.........
..........###..........
"""
# wreath (ring) area for the inner symbol: 7x7 below the talons
EAGLE_SMALL = """
......#........
.....###.......
#####.#.#######
.####.#.######.
..###.#.#####..
....#####......
.....###.......
.....#.#.......
....#...#......
.....###.......
"""


def eagle_mask(kind: str = 'large') -> np.ndarray:
    return _mask(EAGLE_23 if kind == 'large' else EAGLE_SMALL)


HAMMER_SICKLE_9 = """
.....##..
.#.....#.
###....##
.###...##
..#.#.##.
....###..
..##.##..
.##...##.
##.....#.
"""
HAMMER_SICKLE_7 = """
....##.
.#....#
###...#
.#.#.#.
...##..
.##.##.
#....#.
"""
STAR_5 = """
..#..
.###.
#####
.#.#.
#...#
"""
GEAR_WHEAT_9 = """
...###...
.#.#.#.#.
..##.##..
###.#.###
#.##.##.#
###.#.###
..##.##..
.#.###.#.
...#.#...
"""
GEAR_WHEAT_7 = """
..###..
.#.#.#.
##.#.##
#.###.#
##.#.##
.#.#.#.
..###..
"""
PILLAR_5 = """
..#..
..#..
.###.
.###.
#####
"""


def mask_named(name: str) -> np.ndarray:
    return _mask({'hs9': HAMMER_SICKLE_9, 'hs7': HAMMER_SICKLE_7, 'star5': STAR_5,
                  'gw9': GEAR_WHEAT_9, 'gw7': GEAR_WHEAT_7, 'pillar5': PILLAR_5}[name])


def ring_mask(d: int, thick: float = 1.0) -> np.ndarray:
    c = d / 2.0

    def fn(x, y):
        r = np.sqrt((x - c) ** 2 + (y - c) ** 2)
        return (r <= c - 0.15) & (r >= c - 0.15 - thick)
    return raster(fn, d, d, thr=0.5)


def disc_mask(d: int) -> np.ndarray:
    c = d / 2.0
    return raster(lambda x, y: np.sqrt((x - c) ** 2 + (y - c) ** 2) <= c - 0.1, d, d, thr=0.5)


# ----------------------------------------------------------------------------------------- packing / io
def crop_bbox(rgba: np.ndarray, pad: int = 0):
    a = rgba[..., 3] > 0
    if not a.any():
        return None
    ys, xs = np.nonzero(a)
    x0, x1 = max(0, xs.min() - pad), min(rgba.shape[1], xs.max() + 1 + pad)
    y0, y1 = max(0, ys.min() - pad), min(rgba.shape[0], ys.max() + 1 + pad)
    return x0, y0, x1, y1


class Atlas:
    """Packs frames (full-canvas RGBA arrays) into a sheet; each frame keeps its offset so the player can
    place it at (anim_pos + offset).  Shelf packing, deterministic."""

    def __init__(self, name: str, max_w: int = 2048):
        self.name = name
        self.max_w = max_w
        self.frames = []          # (img, ox, oy)

    def add(self, rgba: np.ndarray, ox: int = 0, oy: int = 0) -> int:
        bb = crop_bbox(rgba)
        if bb is None:
            self.frames.append((np.zeros((1, 1, 4), np.uint8), ox, oy))
        else:
            x0, y0, x1, y1 = bb
            self.frames.append((rgba[y0:y1, x0:x1].copy(), ox + x0, oy + y0))
        return len(self.frames) - 1

    def add_cropped(self, img: np.ndarray, ox: int, oy: int) -> int:
        self.frames.append((img, ox, oy))
        return len(self.frames) - 1

    def save(self, path: str) -> list:
        # dedupe identical frames
        uniq = {}
        order = []
        for img, ox, oy in self.frames:
            k = (img.shape, zlib.crc32(img.tobytes()))
            if k not in uniq:
                uniq[k] = len(order)
                order.append(img)
        x = y = 0
        shelf_h = 0
        places = []
        W = 0
        for img in order:
            h, w = img.shape[:2]
            if x + w > self.max_w:
                x = 0
                y += shelf_h + 1
                shelf_h = 0
            places.append((x, y))
            x += w + 1
            shelf_h = max(shelf_h, h)
            W = max(W, x)
        Hh = y + shelf_h
        sheet = np.zeros((max(1, Hh), max(1, W), 4), np.uint8)
        for img, (px, py) in zip(order, places):
            h, w = img.shape[:2]
            sheet[py:py + h, px:px + w] = img
        os.makedirs(os.path.dirname(path), exist_ok=True)
        Image.fromarray(sheet, 'RGBA').save(path)
        rects = []
        for img, ox, oy in self.frames:
            k = (img.shape, zlib.crc32(img.tobytes()))
            px, py = places[uniq[k]]
            h, w = img.shape[:2]
            rects.append([int(px), int(py), int(w), int(h), int(ox), int(oy)])
        return rects


def save_rgba(arr: np.ndarray, path: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    Image.fromarray(arr.astype(np.uint8), 'RGBA').save(path)


def over(dst: np.ndarray, src: np.ndarray, x: int = 0, y: int = 0) -> None:
    """Binary-alpha blit of src onto dst at (x, y)."""
    h, w = dst.shape[:2]
    sh, sw = src.shape[:2]
    X0, Y0 = max(0, x), max(0, y)
    X1, Y1 = min(w, x + sw), min(h, y + sh)
    if X1 <= X0 or Y1 <= Y0:
        return
    s = src[Y0 - y:Y1 - y, X0 - x:X1 - x]
    m = s[..., 3] > 127
    dst[Y0:Y1, X0:X1][m] = s[m]


def upscale(arr: np.ndarray, k: int = 3) -> Image.Image:
    im = Image.fromarray(arr.astype(np.uint8), 'RGBA')
    return im.resize((im.width * k, im.height * k), Image.NEAREST)


def eagle_shapes():
    """Reichsadler-type state eagle in normalised units (x in [-1, 1], y down, 0..~1.30):
    head turned to the viewer's left, straight upper wing edges, stepped feather tips, fanned tail,
    talons on a wreath centred at (0, WREATH_Y) with radius WREATH_R."""
    head = [(-0.02, 0.02), (0.08, 0.04), (0.10, 0.14), (0.06, 0.22), (-0.06, 0.22), (-0.12, 0.15),
            (-0.22, 0.15), (-0.13, 0.08)]
    body = [(-0.10, 0.20), (0.10, 0.20), (0.13, 0.42), (0.09, 0.64), (-0.09, 0.64), (-0.13, 0.42)]
    lw = [(-0.08, 0.24), (-0.30, 0.13), (-1.00, 0.08), (-1.00, 0.17), (-0.86, 0.19), (-0.85, 0.29),
          (-0.70, 0.30), (-0.69, 0.41), (-0.54, 0.42), (-0.53, 0.52), (-0.38, 0.52), (-0.36, 0.61),
          (-0.16, 0.58), (-0.10, 0.50)]
    rw = [(-x, y) for (x, y) in lw]
    tail = [(-0.09, 0.60), (0.09, 0.60), (0.20, 0.80), (0.07, 0.76), (0.0, 0.82), (-0.07, 0.76), (-0.20, 0.80)]
    legs = [((-0.06, 0.66), (-0.12, 0.88)), ((0.06, 0.66), (0.12, 0.88))]
    return head, body, lw, rw, tail, legs


WREATH_Y, WREATH_R = 1.04, 0.30


def _pip(xs, ys, poly):
    """Vectorised point-in-polygon (even-odd)."""
    inside = np.zeros(xs.shape, bool)
    n = len(poly)
    for i in range(n):
        ax, ay = poly[i]
        bx, by = poly[(i + 1) % n]
        cond = ((ay > ys) != (by > ys))
        xint = (bx - ax) * (ys - ay) / (by - ay + 1e-12) + ax
        inside ^= cond & (xs < xint)
    return inside


def eagle_raster(width: int, inner: str = 'swastika', thr: float = 0.42, wreath: bool = True):
    """Rasterise the eagle at `width` px.  inner: 'swastika' | 'pillar' | 'none'.
    Returns (mask, eye) where eye is the (x, y) of the eye pixel (to punch out)."""
    s = (width - 1) / 2.0
    hgt = int(math.ceil((WREATH_Y + WREATH_R + 0.06) * s)) + 1 if wreath else int(math.ceil(0.84 * s)) + 1
    head, body, lw, rw, tail, legs = eagle_shapes()
    cx = width / 2.0

    def fn(x, y):
        u = (x - cx) / s
        v = y / s
        m = _pip(u, v, head) | _pip(u, v, body) | _pip(u, v, lw) | _pip(u, v, rw) | _pip(u, v, tail)
        for (a, b) in legs:
            ax, ay = a
            bx, by = b
            vx, vy = bx - ax, by - ay
            t = np.clip(((u - ax) * vx + (v - ay) * vy) / (vx * vx + vy * vy), 0, 1)
            d = np.sqrt((u - ax - t * vx) ** 2 + (v - ay - t * vy) ** 2)
            m |= d < 0.035
        if wreath:
            r = np.sqrt(u ** 2 + (v - WREATH_Y) ** 2)
            m |= (r <= WREATH_R) & (r >= WREATH_R - 0.07)
        return m
    mask = raster(fn, width, hgt, thr=thr)
    if wreath and inner != 'none':
        rin = (WREATH_R - 0.07) * s
        d = max(3, int(round(rin * 2 * 0.86)))
        cyy = WREATH_Y * s
        x0 = int(round(cx - d / 2.0))
        y0 = int(round(cyy - d / 2.0))
        sym = swastika_mask(d, thick=0.22) if inner == 'swastika' else _pillar(d)
        sh, sw = sym.shape
        mask[max(0, y0):y0 + sh, max(0, x0):x0 + sw] |= sym[:mask.shape[0] - max(0, y0), :mask.shape[1] - max(0, x0)]
    eye = (int(round(cx + 0.0 * s)), int(round(0.11 * s)))
    return mask, eye


def _pillar(d: int) -> np.ndarray:
    m = np.zeros((d, d), bool)
    c = d // 2
    m[1:d - 1, c] = True
    if d >= 5:
        m[d - 2, c - 1:c + 2] = True
        m[1, c] = True
    m[d - 1, max(0, c - 2):c + 3] = True
    return m


# hand-pixelled symbols for small sizes (on-point Hakenkreuz, hooks clockwise; Reichssiegel pillar)
SYM = {
    'swastika7': """
..#....
.#...#.
..#.#.#
...#...
#.#.#..
.#...#.
....#..""",
    'swastika9': """
....#....
...#.....
..#...#..
...#.#.#.
#...#...#
.#.#.#...
..#...#..
.....#...
....#....""",
    'pillar7': """
...#...
...#...
..###..
..###..
..###..
..###..
.#####.""",
    'pillar9': """
....#....
....#....
...###...
...###...
...###...
...###...
...###...
..#####..
.#######.""",
    'ring11': """
...#####...
..#.....#..
.#.......#.
#.........#
#.........#
#.........#
#.........#
#.........#
.#.......#.
..#.....#..
...#####...""",
    'ring13': """
....#####....
..##.....##..
.#.........#.
.#.........#.
#...........#
#...........#
#...........#
#...........#
#...........#
.#.........#.
.#.........#.
..##.....##..
....#####....""",
}


def sym(name: str) -> np.ndarray:
    return _mask(SYM[name]) if name in SYM else mask_named(name)


def state_emblem(eagle_w: int = 25, hist: bool = True, big: bool = False) -> np.ndarray:
    """Eagle on a wreath ring; inner symbol = Hakenkreuz (hist) or the fictional Reichssiegel pillar."""
    em, _ = eagle_raster(eagle_w, inner='none', wreath=False)
    ring = sym('ring13' if big else 'ring11')
    inner = sym(('swastika9' if big else 'swastika7') if hist else ('pillar9' if big else 'pillar7'))
    rh, rw = ring.shape
    W = max(em.shape[1], rw)
    Hh = em.shape[0] + rh - 1
    out = np.zeros((Hh, W), bool)
    ex = (W - em.shape[1]) // 2
    out[:em.shape[0], ex:ex + em.shape[1]] |= em
    rx = (W - rw) // 2
    ry = em.shape[0] - 1
    out[ry:ry + rh, rx:rx + rw] |= ring
    ih, iw = inner.shape
    out[ry + (rh - ih) // 2:ry + (rh - ih) // 2 + ih, rx + (rw - iw) // 2:rx + (rw - iw) // 2 + iw] |= inner
    return out


def round_stamp(d: int, center: np.ndarray, seed: int, text_ring: bool = True) -> np.ndarray:
    """Circular office stamp mask: double outer ring, a ring of 'lettering', the emblem in the middle."""
    m = np.zeros((d, d), bool)
    c = d / 2.0
    yy, xx = np.mgrid[0:d, 0:d].astype(np.float32) + 0.5
    r = np.sqrt((xx - c) ** 2 + (yy - c) ** 2)
    m |= (r <= c - 0.2) & (r >= c - 1.3)
    m |= (r <= c - 5.6) & (r >= c - 6.6)
    if text_ring:
        rng = np.random.default_rng(seed)
        ang = np.arctan2(yy - c, xx - c)
        band = (r <= c - 2.4) & (r >= c - 4.6)
        # letters: short radial strokes with gaps, a gap at the bottom for the star/date
        cells = np.floor((ang + math.pi) / (2 * math.pi) * (d * 1.3))
        on = np.array([rng.random() < 0.72 for _ in range(int(d * 1.3) + 2)])
        lettering = band & on[cells.astype(int)] & (np.abs(ang - math.pi / 2) > 0.45)
        rr = rng.random((d, d))
        m |= lettering & (rr < 0.78)
    ch, cw = center.shape
    y0 = int(round(c - ch / 2.0 + 0.5))
    x0 = int(round(c - cw / 2.0))
    sub = m[max(0, y0):y0 + ch, max(0, x0):x0 + cw]
    sub |= center[:sub.shape[0], :sub.shape[1]]
    return m


def soviet_emblem(hist: bool = True) -> np.ndarray:
    """Star over hammer & sickle (hist) or the fictional gear-and-wheat (neutral)."""
    star = sym('star5')
    inner = sym('hs9') if hist else sym('gw9')
    W = max(star.shape[1], inner.shape[1])
    out = np.zeros((star.shape[0] + inner.shape[0] + 1, W), bool)
    out[:star.shape[0], (W - star.shape[1]) // 2:(W - star.shape[1]) // 2 + star.shape[1]] |= star
    out[star.shape[0] + 1:, (W - inner.shape[1]) // 2:(W - inner.shape[1]) // 2 + inner.shape[1]] |= inner
    return out


def ink(rgba: np.ndarray, mask: np.ndarray, x: int, y: int, ramp, lamp: 'Lamp', wear: float = 0.08,
        seed: int = 0, base: float = 0.1, gain: float = 0.9) -> None:
    """Stamp ink onto rgba at (x, y): ink colour from `ramp` by local light; random wear (missing ink)."""
    h, w = rgba.shape[:2]
    mh, mw = mask.shape
    rng = np.random.default_rng(seed)
    worn = rng.random((mh, mw)) < wear
    for yy in range(mh):
        for xx in range(mw):
            if not mask[yy, xx] or worn[yy, xx]:
                continue
            X, Y = x + xx, y + yy
            if 0 <= X < w and 0 <= Y < h:
                t = float(np.clip(base + gain * lamp.pool(np.float32(X + 0.5), np.float32(Y + 0.5)), 0, 1))
                rgba[Y, X] = tone_to_ramp(np.array([[t]], np.float32), ramp, X, Y)[0, 0]


# ----------------------------------------------------------------------------------------- keyframed tracks
def _ease(t: float) -> float:
    t = min(1.0, max(0.0, t))
    return t * t * (3 - 2 * t)


def _lerp(a, b, t):
    if isinstance(a, (tuple, list)):
        return tuple(_lerp(x, y, t) for x, y in zip(a, b))
    return a + (b - a) * t


class Track:
    """Generic keyframed state: key(t, **fields).  Numeric fields (and tuples) are smoothstep-interpolated
    between keys; other fields (strings, flags) switch at the later key.  ease='lin' on a key makes the
    segment ending at that key linear."""

    def __init__(self, **defaults):
        self.defaults = defaults
        self.keys = []

    def key(self, t: float, **kw):
        prev = dict(self.keys[-1][1]) if self.keys else dict(self.defaults)
        prev.update(kw)
        self.keys.append((float(t), prev))
        self.keys.sort(key=lambda k: k[0])
        return self

    def at(self, t: float) -> dict:
        if not self.keys:
            return dict(self.defaults)
        if t <= self.keys[0][0]:
            return dict(self.keys[0][1])
        for (t0, a), (t1, b) in zip(self.keys[:-1], self.keys[1:]):
            if t0 <= t <= t1:
                f = (t - t0) / max(1e-6, t1 - t0)
                f = f if b.get('ease') == 'lin' else _ease(f)
                out = {}
                for k in b:
                    va, vb = a.get(k, b[k]), b[k]
                    if isinstance(vb, (int, float)) and not isinstance(vb, bool) and isinstance(va, (int, float)):
                        out[k] = _lerp(va, vb, f)
                    elif isinstance(vb, (tuple, list)) and isinstance(va, (tuple, list)) and len(va) == len(vb) \
                            and all(isinstance(x, (int, float)) for x in vb):
                        out[k] = _lerp(tuple(va), tuple(vb), f)
                    else:
                        out[k] = vb if f >= 1.0 or k == 'ease' else (va if f < 0.5 else vb)
                return out
        return dict(self.keys[-1][1])


TYPE_PATTERNS = [
    (0.5, 0.75, 0.5, 0.5), (0.5, 0.5, 0.78, 0.5), (0.78, 0.5, 0.5, 0.5), (0.5, 0.5, 0.5, 0.75),
    (0.5, 0.8, 0.5, 0.5), (0.75, 0.5, 0.5, 0.55), (0.5, 0.5, 0.72, 0.5), (0.5, 0.55, 0.5, 0.8)]


def render_arm_track(track: Track, side: str, atlas: 'Atlas', w: int, h: int, lamp: Lamp, t0: float, t1: float,
                     fps: float = 12.0, extra=None, **kw) -> list:
    """Renders one arm along a Track into `atlas`; returns [[t, frame], ...] (local time).  Track fields:
    wrist (x, y), ang, length, curl, thumb, tilt, spread, entry (x, y), typing (0/1), lift_y, bend, hidden.
    extra(t, state, rgba) may draw held objects under the hand (called before the arm is composited)."""
    cache = {}
    keys = []
    n = int(math.ceil((t1 - t0) * fps)) + 1
    last = None
    for i in range(n):
        t = t0 + i / fps
        s = track.at(t)
        if s.get('hidden'):
            fr = -1
        else:
            curls = None
            if s.get('typing', 0) > 0.5:
                pat = TYPE_PATTERNS[(i * 5 + (3 if side == 'L' else 0)) % len(TYPE_PATTERNS)]
                curls = list(pat)
            wx, wy = s['wrist']
            jit = 0
            if s.get('typing', 0) > 0.5:
                jit = (i * 7 + (1 if side == 'L' else 4)) % 3 - 1
            pose = HandPose(curl=s.get('curl', 0.0), spread=s.get('spread', 0.0), thumb=s.get('thumb', 'side'),
                            curls=curls, tilt=s.get('tilt', 0.0))
            sig = (round(wx + jit), round(wy), round(s['ang'], 2), round(s.get('curl', 0), 2), s.get('thumb', 'side'),
                   tuple(curls) if curls else None, round(s.get('tilt', 0), 2), round(s['entry'][0]),
                   round(s['entry'][1]), round(s.get('bend', 0)), round(s.get('spread', 0), 2),
                   extra(t, s, None) if extra else None)
            if sig in cache:
                fr = cache[sig]
            else:
                rgba, m = render_arm(w, h, (round(wx + jit) + 0.5, round(wy) + 0.5), s['ang'], s.get('length', 60), pose,
                                     side, s['entry'], bend=s.get('bend', 0.0), lamp=lamp, **kw)
                if extra:
                    under = np.zeros_like(rgba)
                    extra(t, s, under)
                    over(under, rgba)
                    rgba = under
                fr = atlas.add(rgba)
                cache[sig] = fr
        if fr != last:
            keys.append([round(t - t0, 3), fr])
            last = fr
    atlas.track_info = dict(track=track, side=side, kw=kw, lamp=lamp, extra=extra, w=w, h=h, t_end=t1)
    return keys


def render_tap(atlas: 'Atlas') -> int:
    """Rhyme beat: the arm's final pose with the index finger lifted off the desk (shorter in the top view,
    catching more light).  Returns the new frame index, or -1 when the arm ends hidden."""
    info = getattr(atlas, 'track_info', None)
    if not info:
        return -1
    s = info['track'].at(info['t_end'])
    if s.get('hidden'):
        return -1
    c = s.get('curl', 0.0)
    pose = HandPose(curl=c, spread=s.get('spread', 0.0), thumb=s.get('thumb', 'side'),
                    curls=[min(1.0, c + 0.42), None, None, None], tilt=s.get('tilt', 0.0), lifted=[4, 0, 0, 0])
    wx, wy = s['wrist']
    rgba, m = render_arm(info['w'], info['h'], (round(wx) + 0.5, round(wy) + 0.5), s['ang'], s.get('length', 60), pose,
                         info['side'], s['entry'], bend=s.get('bend', 0.0), lamp=info['lamp'], **info['kw'])
    if info['extra']:
        under = np.zeros_like(rgba)
        info['extra'](info['t_end'], s, under)
        over(under, rgba)
        rgba = under
    return atlas.add(rgba)


def frames_from_states(atlas: 'Atlas', states: list, render) -> list:
    """Render a list of distinct states via render(state) -> rgba; returns frame indices."""
    return [atlas.add(render(s)) for s in states]
