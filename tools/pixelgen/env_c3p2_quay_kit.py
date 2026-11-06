"""env_c3p2_quay_kit -- shared kit of the night quay (L_C3_Quay, Chapter 3 part 2, area env_c3p2_night).

Painting model ("deferred" night bake): geometry is drawn into a Canvas as (material, tone, height) per pixel;
tone = the surface value under the cold ambient night light (0 = black, 1 = snow white, as luminance).  resolve()
adds the light fields of the scene (warm lanterns / windows, the fire, cold floodlights) and picks, per pixel,
the material's cold, warm or fire ladder (ordered dither in a narrow band) and the ladder entry of matching
luminance.  Every output pixel is a colour of the Veltrava palette (data/chapters/c3.json "palettes.veltrava",
registered by env_veltrava_lib) -- stable under the post-grade palette snap.  Emissive materials (lit glass,
flames, lamp mantles) ignore the lights and also write the emission map (_e, added unshaded by layer_stack).
Pure numpy, fixed seeds, no image inputs: deterministic, original procedural art.
"""
from __future__ import annotations

import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import numpy as np  # noqa: E402
from PIL import Image  # noqa: E402

import pg  # noqa: E402
from pg import Layer, hx, bayer, value_noise  # noqa: E402,F401
import env_veltrava_lib as V  # noqa: E402  (registers pg.PALETTES['veltrava'])

ROOT = V.ROOT
ENV_ID = 'veltrava_quay'
ENV_DIR = os.path.join(ROOT, 'assets', 'environments', ENV_ID)
DATE = '2026-11-06'
WORLD_W, WORLD_H, VIEW_W, VIEW_H = 1920, 360, 640, 360
FEET_Y = 300
WALK_BAND = (296, 306)
WALK_X = (18, 1902)

NI, SL, IR, CR, PA, LA, SK, SN, RD = V.NI, V.SL, V.IR, V.CR, V.PA, V.LA, V.SK, V.SN, V.RD
SKIN = [hx('#885551'), hx('#B47B65'), hx('#D5A081')]        # c3.json palettes.veltrava.skin
CLEAR = np.zeros(4, np.uint8)


def hexc(c) -> str:
    return '#%02X%02X%02X' % (int(c[0]), int(c[1]), int(c[2]))


def allowed_hex() -> set:
    s = {hexc(c) for c in V.ALL}
    s |= {hexc(c) for c in SKIN}
    return s


def lum(c) -> float:
    return (0.299 * float(c[0]) + 0.587 * float(c[1]) + 0.114 * float(c[2])) / 255.0


def ladder(*cols):
    """Palette colours sorted by luminance (duplicates removed) -> a ramp for tone painting."""
    seen, out = set(), []
    for c in cols:
        k = hexc(c)
        if k not in seen:
            seen.add(k)
            out.append(np.asarray(c, np.uint8))
    out.sort(key=lum)
    return out


L_LO, L_HI = lum(NI[0]), lum(SN[4])

# --------------------------------------------------------------------------- materials
# cold = under the night sky, warm = lantern / window light, fire = the burning wing
COLD_FULL = ladder(*NI, *SL, *SN)
MATS = {
    'snow':   dict(cold=COLD_FULL,
                   warm=ladder(NI[0], NI[1], CR[0], LA[0], CR[1], CR[2], LA[1], CR[3], LA[2], CR[4], LA[3], CR[5], LA[4]),
                   fire=ladder(NI[0], NI[1], RD[0], LA[0], LA[1], LA[2], LA[3]), fire_cap=0.58),
    'stone':  dict(cold=ladder(*NI, SL[0], SL[1], SL[2], SL[3], SL[4], SL[5]),
                   warm=ladder(NI[0], NI[1], IR[1], CR[0], CR[1], CR[2], CR[3], CR[4], CR[5]),
                   fire=ladder(NI[0], NI[1], IR[1], RD[0], LA[0], CR[1], LA[1], LA[2]), fire_cap=0.5),
    'iron':   dict(cold=ladder(NI[0], IR[0], NI[1], IR[1], NI[2], IR[2], NI[3], IR[3], SL[2], IR[4], SL[3], SL[4]),
                   warm=ladder(NI[0], IR[0], IR[1], CR[0], LA[0], CR[1], LA[1], CR[3], LA[2], LA[3]),
                   fire=ladder(NI[0], IR[0], RD[0], RD[1], LA[0], RD[2], LA[1], LA[2]), fire_cap=0.45),
    'slate':  dict(cold=ladder(*NI, SL[0], SL[1], SL[2], SL[3]),
                   warm=ladder(NI[0], NI[1], IR[1], CR[0], CR[1], CR[2]),
                   fire=ladder(NI[0], NI[1], RD[0], RD[1], RD[2], LA[1])),
    'patina': dict(cold=ladder(NI[0], NI[1], NI[2], PA[0], PA[1], PA[2], PA[3], PA[4]),
                   warm=ladder(NI[0], PA[0], CR[0], PA[2], CR[2], PA[4], CR[3]),
                   fire=ladder(NI[0], RD[0], PA[1], RD[1], LA[0], RD[2], LA[1])),
    'red':    dict(cold=ladder(NI[0], NI[1], RD[0], RD[1], RD[2], RD[3], LA[1]),
                   warm=ladder(NI[0], RD[0], RD[1], RD[2], RD[3], LA[1], LA[2], LA[3]),
                   fire=ladder(NI[0], RD[0], RD[1], RD[2], RD[3], LA[2]), fire_cap=0.5),
    'wood':   dict(cold=ladder(NI[0], NI[1], NI[2], IR[1], NI[3], IR[2], SL[1], SL[2], SL[3]),
                   warm=ladder(NI[0], IR[0], CR[0], LA[0], CR[1], LA[1], CR[2], CR[3]),
                   fire=ladder(NI[0], RD[0], LA[0], RD[1], RD[2], LA[1], LA[2]), fire_cap=0.45),
    'ice':    dict(cold=ladder(*NI, *SL, SN[0], SN[1], SN[2]),
                   warm=ladder(NI[0], NI[1], CR[0], LA[0], CR[1], LA[1], CR[2], LA[2], CR[4], LA[3]),
                   fire=ladder(NI[0], RD[0], RD[1], LA[0], RD[2], LA[1], RD[3], LA[2]), fire_cap=0.5),
    'glass':  dict(cold=ladder(NI[0], NI[1], NI[2], NI[3], SL[0], SL[1], SL[2], SL[3]),
                   warm=ladder(NI[0], NI[1], LA[0], LA[1], LA[2], LA[3]),
                   fire=ladder(NI[0], RD[0], RD[1], RD[2], LA[1], LA[2], LA[3]), fire_cap=0.55),
    'smoke':  dict(cold=ladder(NI[1], NI[2], NI[3], SL[0], SL[1], SL[2], SL[3], SL[4]),
                   warm=ladder(NI[1], IR[1], CR[0], CR[1], CR[2], CR[3]),
                   fire=ladder(NI[1], RD[0], RD[1], LA[0], RD[2], LA[1], RD[3], LA[2]), fire_cap=0.42),
    'cloth':  dict(cold=ladder(NI[0], NI[1], NI[2], NI[3], SL[0], SL[1], SL[2]),
                   warm=ladder(NI[0], NI[1], IR[1], CR[0], CR[1], LA[1]),
                   fire=ladder(NI[0], NI[1], RD[0], RD[1], LA[0]), fire_cap=0.15, gain=0.4),
    'skin':   dict(cold=ladder(NI[2], SL[1], SL[3], SKIN[0], SKIN[1]),
                   warm=ladder(NI[1], RD[0], SKIN[0], SKIN[1], SKIN[2], LA[3]),
                   fire=ladder(NI[1], RD[0], RD[1], SKIN[0], RD[3], SKIN[1], LA[2])),
    # emissive (no light response; tone indexes the ladder directly; written to the emission map)
    'lit':    dict(cold=ladder(LA[0], LA[1], LA[2], LA[3], LA[4]), emissive=True),
    'flame':  dict(cold=ladder(RD[1], RD[2], LA[1], RD[3], LA[2], LA[3], LA[4]), emissive=True),
    'cold_lit': dict(cold=ladder(SL[4], SL[5], SN[1], SN[2], SN[3], SN[4]), emissive=True),
    'blue_lit': dict(cold=ladder(SL[3], SL[4], SK[1], SK[2], SN[2], SN[3]), emissive=True),
}
MAT_NAMES = list(MATS)
MID = {n: i for i, n in enumerate(MAT_NAMES)}
for _n, _s in MATS.items():
    for _k in ('cold', 'warm', 'fire'):
        if _k in _s:
            _s[_k + '_lum'] = np.array([lum(c) for c in _s[_k]], np.float32)


def tone_of(col) -> float:
    """Tone value that reproduces a palette colour's luminance."""
    return float(np.clip((lum(col) - L_LO) / (L_HI - L_LO), 0, 1))


# --------------------------------------------------------------------------- canvas
class Canvas:
    """Deferred painter: material id, tone and height per pixel + ink (direct colours) on top."""

    def __init__(self, w: int, h: int, name: str = 'canvas', ox: int = 0, oy: int = 0):
        self.w, self.h, self.name = int(w), int(h), name
        self.ox, self.oy = int(ox), int(oy)          # world offset of pixel (0, 0) for the light fields
        self.mat = np.full((self.h, self.w), -1, np.int16)
        self.tone = np.zeros((self.h, self.w), np.float32)
        self.hgt = np.zeros((self.h, self.w), np.float32)
        self.recv = np.ones((self.h, self.w), np.float32)
        self.ink = np.zeros((self.h, self.w, 4), np.uint8)
        self.ink_em = np.zeros((self.h, self.w), bool)

    # ---- low level
    def _clip(self, mask: np.ndarray, x0: int, y0: int):
        mh, mw = mask.shape
        X0, Y0 = max(0, x0), max(0, y0)
        X1, Y1 = min(self.w, x0 + mw), min(self.h, y0 + mh)
        if X1 <= X0 or Y1 <= Y0:
            return None
        return mask[Y0 - y0:Y1 - y0, X0 - x0:X1 - x0], X0, Y0, X1, Y1

    def put(self, mask, x0, y0, mat, tone, hgt=None, recv=None, keep_ink=False):
        r = self._clip(np.asarray(mask, bool), int(x0), int(y0))
        if r is None:
            return
        m, X0, Y0, X1, Y1 = r
        sl = (slice(Y0, Y1), slice(X0, X1))
        if mat is None:            # erase
            self.mat[sl][m] = -1
            self.ink[sl][m] = 0
            return
        self.mat[sl][m] = MID[mat]
        if np.isscalar(tone):
            self.tone[sl][m] = tone
        else:
            t = np.asarray(tone, np.float32)[Y0 - y0:Y1 - y0, X0 - x0:X1 - x0]
            self.tone[sl][m] = t[m]
        if hgt is not None:
            if np.isscalar(hgt):
                self.hgt[sl][m] = hgt
            else:
                self.hgt[sl][m] = np.asarray(hgt, np.float32)[Y0 - y0:Y1 - y0, X0 - x0:X1 - x0][m]
        if recv is not None:
            self.recv[sl][m] = recv
        if not keep_ink:
            self.ink[sl][m] = 0
            self.ink_em[sl][m] = False

    def rect(self, x, y, w, h, mat, tone, hgt=None, recv=None):
        w, h = int(round(w)), int(round(h))
        if w <= 0 or h <= 0:
            return
        self.put(np.ones((h, w), bool), int(round(x)), int(round(y)), mat, tone, hgt, recv)

    def poly(self, pts, mat, tone, hgt=None, recv=None):
        m, x0, y0 = Layer(1, 1).poly_mask(pts)
        self.put(m, x0, y0, mat, tone, hgt, recv)
        return m, x0, y0

    def ellipse(self, cx, cy, rx, ry, mat, tone, hgt=None, recv=None):
        m, x0, y0 = Layer(1, 1).ellipse_mask(cx, cy, rx, ry)
        self.put(m, x0, y0, mat, tone, hgt, recv)
        return m, x0, y0

    def px(self, x, y, mat, tone, hgt=None):
        x, y = int(round(x)), int(round(y))
        if 0 <= x < self.w and 0 <= y < self.h:
            self.mat[y, x] = MID[mat]
            self.tone[y, x] = tone
            self.ink[y, x] = 0
            if hgt is not None:
                self.hgt[y, x] = hgt

    def line(self, x0, y0, x1, y1, mat, tone, hgt=None, width=1):
        n = int(max(abs(x1 - x0), abs(y1 - y0))) + 1
        for i in range(n):
            t = i / max(1, n - 1)
            x, y = x0 + (x1 - x0) * t, y0 + (y1 - y0) * t
            if width <= 1:
                self.px(x, y, mat, tone, hgt)
            else:
                self.rect(int(round(x - width / 2 + 0.5)), int(round(y - width / 2 + 0.5)), width, width, mat, tone, hgt)

    def ink_px(self, x, y, col, em=False):
        x, y = int(round(x)), int(round(y))
        if 0 <= x < self.w and 0 <= y < self.h:
            self.ink[y, x, :3] = np.asarray(col)[:3]
            self.ink[y, x, 3] = 255
            self.ink_em[y, x] = bool(em)
            if self.mat[y, x] < 0:
                self.mat[y, x] = MID['stone']        # keeps the pixel opaque in alpha()

    def ink_mask(self, mask, x0, y0, col, em=False):
        r = self._clip(np.asarray(mask, bool), int(x0), int(y0))
        if r is None:
            return
        m, X0, Y0, X1, Y1 = r
        sl = (slice(Y0, Y1), slice(X0, X1))
        self.ink[sl][m] = np.concatenate([np.asarray(col, np.uint8)[:3], [255]])
        self.ink_em[sl][m] = bool(em)
        mm = self.mat[sl]
        mm[m & (mm < 0)] = MID['stone']

    def ink_rect(self, x, y, w, h, col, em=False):
        if w > 0 and h > 0:
            self.ink_mask(np.ones((int(h), int(w)), bool), int(x), int(y), col, em)

    def text(self, x, y, s, col, font='s', em=False, spacing=1):
        tw = V.text_width(s, font, spacing) + 4
        th = 12
        T = Layer(tw, th + 4)
        V.text(T, 2, 2, s, col, font=font, spacing=spacing)
        m = T.c[..., 3] > 0
        self.ink_mask(m, int(x) - 2, int(y) - 2, col, em)
        return tw - 4

    def shade(self, mask, x0, y0, delta):
        """Add delta (scalar or array) to the tone of painted pixels inside mask."""
        r = self._clip(np.asarray(mask, bool), int(x0), int(y0))
        if r is None:
            return
        m, X0, Y0, X1, Y1 = r
        sl = (slice(Y0, Y1), slice(X0, X1))
        m = m & (self.mat[sl] >= 0)
        if np.isscalar(delta):
            self.tone[sl][m] += delta
        else:
            d = np.asarray(delta, np.float32)[Y0 - y0:Y1 - y0, X0 - x0:X1 - x0]
            self.tone[sl][m] += d[m]

    def shade_rect(self, x, y, w, h, delta):
        if w > 0 and h > 0:
            self.shade(np.ones((int(h), int(w)), bool), int(x), int(y), delta)

    def texture(self, x, y, w, h, amp, cell=6.0, seed=0, octaves=3, mats=None):
        """Value-noise tone texture (plaster, snow, ice) on painted pixels of the box."""
        x, y, w, h = int(x), int(y), int(w), int(h)
        if w <= 0 or h <= 0:
            return
        n = value_noise(w, h, cell, seed=seed, octaves=octaves) - 0.5
        m = np.ones((h, w), bool)
        if mats is not None:
            X0, Y0 = max(0, x), max(0, y)
            sub = np.full((h, w), -1, np.int16)
            X1, Y1 = min(self.w, x + w), min(self.h, y + h)
            if X1 > X0 and Y1 > Y0:
                sub[Y0 - y:Y1 - y, X0 - x:X1 - x] = self.mat[Y0:Y1, X0:X1]
            m = np.isin(sub, [MID[k] for k in mats])
        self.shade(m, x, y, n * amp * 2.0)

    def alpha(self) -> np.ndarray:
        return (self.mat >= 0) | (self.ink[..., 3] > 0)


# --------------------------------------------------------------------------- lights
class Light:
    """kind: 'warm' | 'fire' | 'cold'.  sq > 1 squashes the falloff vertically (pools on the ground plane).
    up < 1 weakens the light above the source (lamps shine down; their caps shade the sky side)."""

    def __init__(self, kind, x, y, r, i=1.0, sq=1.0, up=1.0, name='', pw=1.7):
        self.kind, self.x, self.y, self.r, self.i, self.sq, self.up, self.name = kind, x, y, r, i, sq, up, name
        self.pw = pw


def light_fields(lights, w, h, ox=0, oy=0, power=1.7):
    F = {'warm': np.zeros((h, w), np.float32), 'fire': np.zeros((h, w), np.float32),
         'cold': np.zeros((h, w), np.float32)}
    for L in lights:
        x0 = int(math.floor(L.x - L.r - ox)) - 1
        x1 = int(math.ceil(L.x + L.r - ox)) + 2
        ry = L.r / max(0.2, L.sq)
        y0 = int(math.floor(L.y - max(ry, ry / max(L.up, 0.05)) - oy)) - 1
        y1 = int(math.ceil(L.y + ry - oy)) + 2
        X0, X1, Y0, Y1 = max(0, x0), min(w, x1), max(0, y0), min(h, y1)
        if X1 <= X0 or Y1 <= Y0:
            continue
        yy, xx = np.mgrid[Y0:Y1, X0:X1].astype(np.float32)
        dx = (xx + ox + 0.5 - L.x) / L.r
        dy = (yy + oy + 0.5 - L.y) / L.r * L.sq
        dy = np.where(dy < 0, dy / max(L.up, 0.05), dy)
        d = np.sqrt(dx * dx + dy * dy)
        v = L.i * np.clip(1.0 - d, 0, 1) ** L.pw
        F[L.kind][Y0:Y1, X0:X1] += v
    return F


def _ladder_pick(lad, lad_lum, t, thr, steep=2.6):
    T = L_LO + np.clip(t, 0, 1.2) * (L_HI - L_LO)
    fi = np.interp(T, lad_lum, np.arange(len(lad), dtype=np.float32))
    idx = np.floor(fi).astype(np.int32)
    fr = np.clip((fi - idx - 0.5) * steep + 0.5, 0, 1)
    idx = np.clip(idx + (fr > thr), 0, len(lad) - 1)
    return np.stack(lad)[idx]


def resolve(cv: Canvas, lights=(), gains=(0.42, 0.46, 0.30), warm_bias=0.18, steep=2.6,
            hgt_scale=1.0) -> Layer:
    """Bake the lights into palette colours -> pg.Layer (colours, heights, emission)."""
    H, W = cv.h, cv.w
    F = light_fields(lights, W, H, cv.ox, cv.oy)
    out = Layer(W, H, cv.name)
    thr = bayer(W, H, cv.ox, cv.oy)
    thr2 = bayer(W, H, cv.ox + 2, cv.oy + 1)
    gw, gf, gc = gains
    for mid, name in enumerate(MAT_NAMES):
        m = cv.mat == mid
        if not m.any():
            continue
        spec = MATS[name]
        t = cv.tone[m]
        th = thr[m]
        if spec.get('emissive'):
            cols = _ladder_pick(spec['cold'], spec['cold_lum'], t, th, steep)
            out.c[m] = cols
            out.em[m] = cols
            out.em[..., 3][m] = 255
            continue
        rcv = cv.recv[m] * spec.get('gain', 1.0)
        w, f, c = F['warm'][m] * rcv, F['fire'][m] * rcv, F['cold'][m] * rcv
        w = 1.0 - np.exp(-1.25 * w)                                   # lights saturate (no white-out)
        f = 1.0 - np.exp(-1.25 * f)
        tl = t + gw * w + gf * f + gc * c
        hot = w + f
        warmness = hot / (hot + warm_bias + c * 0.8)
        pw = np.clip((warmness - 0.45) * 3.2 + 0.5, 0, 1)
        use_hot = pw > thr2[m]
        fire_dom = f > w * 0.9
        res = _ladder_pick(spec['cold'], spec['cold_lum'], tl, th, steep)
        sel = use_hot & fire_dom
        if sel.any():
            res[sel] = _ladder_pick(spec['fire'], spec['fire_lum'], np.minimum(tl[sel], spec.get('fire_cap', 0.55)),
                                    th[sel], steep)
        sel = use_hot & ~fire_dom
        if sel.any():
            res[sel] = _ladder_pick(spec['warm'], spec['warm_lum'], np.minimum(tl[sel], spec.get('warm_cap', 0.9)),
                                    th[sel], steep)
        out.c[m] = res
    ink = cv.ink[..., 3] > 0
    out.c[ink] = cv.ink[ink]
    em = ink & cv.ink_em
    out.em[em] = cv.ink[em]
    a = cv.alpha()
    out.c[..., 3] = np.where(a, 255, 0).astype(np.uint8)
    out.c[~a] = 0
    out.hgt = cv.hgt * hgt_scale
    return out


# --------------------------------------------------------------------------- glow (soft alpha, add blend)
def glow_image(w, h, glows, ox=0, oy=0, levels=6, power=1.6, max_a=0.85):
    """glows: [(x, y, r, i, colour, sq)] in world px.  RGBA with alpha in `levels` dithered steps."""
    acc = np.zeros((h, w), np.float32)
    rgb = np.zeros((h, w, 3), np.float32)
    for (gx, gy, r, i, col, sq) in glows:
        x0, x1 = max(0, int(gx - r - ox) - 1), min(w, int(gx + r - ox) + 2)
        ry = r / max(0.2, sq)
        y0, y1 = max(0, int(gy - ry - oy) - 1), min(h, int(gy + ry - oy) + 2)
        if x1 <= x0 or y1 <= y0:
            continue
        yy, xx = np.mgrid[y0:y1, x0:x1].astype(np.float32)
        d = np.sqrt(((xx + ox + 0.5 - gx) / r) ** 2 + ((yy + oy + 0.5 - gy) / r * sq) ** 2)
        v = i * np.clip(1 - d, 0, 1) ** power
        acc[y0:y1, x0:x1] += v
        rgb[y0:y1, x0:x1] += v[..., None] * np.asarray(col, np.float32)[:3][None, None, :]
    a = np.clip(acc, 0, max_a)
    col = rgb / np.maximum(acc, 1e-6)[..., None]
    q = a * (levels - 1)
    qi = np.floor(q)
    qi = qi + ((q - qi) > bayer(w, h, ox, oy))
    a = qi / (levels - 1) * max_a
    out = np.zeros((h, w, 4), np.uint8)
    out[..., :3] = np.clip(col, 0, 255).astype(np.uint8)
    out[..., 3] = np.clip(np.round(a * 255), 0, 255).astype(np.uint8)
    out[out[..., 3] == 0] = 0
    return out


# --------------------------------------------------------------------------- strips + export
def parallax_x(world_x: float, cam: float, p: float) -> float:
    """Layer pixel x (home 0) that shows at the same screen x as world_x (p = 1) for camera top-left cam."""
    return world_x - cam + cam * p


def layer_w(p: float, margin: int = 8) -> int:
    return int(math.ceil(VIEW_W + p * (WORLD_W - VIEW_W))) + margin


def crop_v(L: Layer):
    return V.crop_v(L)


def crop_box(L: Layer):
    return V.crop_box(L)


def sub_layer(L: Layer, x0, y0, w, h) -> Layer:
    return V.sub_layer(L, x0, y0, w, h)


def palette_off(arr: np.ndarray) -> list:
    ok = allowed_hex()
    a = arr[..., 3] > 0
    if not a.any():
        return []
    keys = np.unique((arr[..., 0].astype(np.int64) << 16 | arr[..., 1].astype(np.int64) << 8 | arr[..., 2])[a])
    return ['#%06X' % int(k) for k in keys if '#%06X' % int(k) not in ok]


def save_rgba(arr: np.ndarray, path: str):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    Image.fromarray(arr, 'RGBA').save(path)


def strip_layer(n: int, fw: int, fh: int, name='strip') -> Layer:
    return Layer(n * fw, fh, name)


def dither_mask(w, h, density, ox=0, oy=0) -> np.ndarray:
    return bayer(w, h, ox, oy) < density
