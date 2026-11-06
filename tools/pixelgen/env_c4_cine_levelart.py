"""env_c4_cine_levelart -- the levels' own art as the base of the Chapter-4 cinematic plates (owner: cine stream).

The places of the Chapter-4 films are places the player walks through: the tram loop Süd 8 (L_C4_AnnexA), the
siding hall under the Karsk freight yard (L_C4_TunnelsB), the card hall of the annex (L_C4_AnnexB) and the Karsk
skyline (the railyard of chapter 1).  The cinematics build their plates from the levels' own layers so every film
shows the same buildings, signs and objects the player knows -- re-lit for the hour of the shot:

  layer(env, name)            albedo / normal map / emission of a level layer (assets/environments/<env>/)
  relight(L, ambient, lights) albedo x (ambient + sum of the point lights through the normal map) + emission;
                              the point lights fall off like the runtime's light texture (layer_stack.gd)
  CineStreet(light)           the loop street of env_c4_annex_loop re-baked WITHOUT the tram (the films move
                              their own tram) and with the hour's sky light ('dawn' 5.10 / 'morning' ~7.30)
  street_tram()               the tram of line 74 alone, baked by the same painter (cropped, facing left)

Everything is read-only use of the level generators and their PNGs (no level file is written).  Deterministic.
"""
from __future__ import annotations

import os

import numpy as np
from PIL import Image

import env_c4_cine_kit as Q

ENV = os.path.join(Q.ROOT, 'assets', 'environments')


# ----------------------------------------------------------------------------------------------- level layers
def _img(path):
    return np.asarray(Image.open(path).convert('RGBA')).astype(np.float32) / 255.0


def layer(env, name, crop=None):
    """dict(alb, nrm, emi) of assets/environments/<env>/<name>.png (+ _n, _e); crop = (x0, y0, x1, y1)."""
    base = os.path.join(ENV, env, name)
    out = {'alb': _img(base + '.png'), 'nrm': None, 'emi': None}
    if os.path.exists(base + '_n.png'):
        n = _img(base + '_n.png')[..., :3] * 2.0 - 1.0
        n /= np.linalg.norm(n, axis=-1, keepdims=True) + 1e-6
        out['nrm'] = n
    if os.path.exists(base + '_e.png'):
        out['emi'] = _img(base + '_e.png')
    if crop is not None:
        x0, y0, x1, y1 = crop
        for k in ('alb', 'nrm', 'emi'):
            if out[k] is not None:
                out[k] = out[k][y0:y1, x0:x1].copy()
    return out


def _att(d, r):
    """The runtime light texture (layer_stack.gd): 1 at the centre, 0.42 at 45 % of the radius, 0 at the radius."""
    u = np.clip(d / max(1.0, r), 0, 1)
    return np.where(u < 0.45, 1.0 - u / 0.45 * 0.58, 0.42 * (1.0 - (u - 0.45) / 0.55))


def light_field(h, w, nrm, lights, origin=(0, 0)):
    """Sum of point lights (dicts: pos, height, rgb 0..1, energy, radius[, cone=(dx, dy, cos_min)]) as RGB."""
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    xw = xx + origin[0] + 0.5
    yw = yy + origin[1] + 0.5
    acc = np.zeros((h, w, 3), np.float32)
    for L in lights:
        lx, ly = L['pos']
        r = float(L['radius'])
        dx = lx - xw
        dyu = -(ly - yw)
        dz = float(L.get('height', 24))
        d2 = np.sqrt(dx * dx + dyu * dyu)
        a = _att(d2, r)
        if nrm is not None:
            d3 = np.sqrt(dx * dx + dyu * dyu + dz * dz) + 1e-6
            ndl = (nrm[..., 0] * dx + nrm[..., 1] * dyu + nrm[..., 2] * dz) / d3
            a = a * np.clip(ndl * float(L.get('wrap', 1.0)) + float(L.get('wrap_add', 0.0)), 0, 1)
        if L.get('cone') is not None:
            cx, cy, cmin = L['cone']
            cl = float(np.hypot(cx, cy)) + 1e-6
            v = ((xw - lx) * cx + (yw - ly) * cy) / ((d2 + 1e-6) * cl)
            a = a * np.clip((v - cmin) / max(1e-3, 1 - cmin), 0, 1) ** 0.8
        acc += a[..., None] * np.asarray(L['rgb'], np.float32)[None, None] * float(L.get('energy', 1.0))
    return acc


def relight(Ld, ambient, lights=(), origin=(0, 0), emis_k=1.0, gain=1.0, extra=None):
    """Lit RGBA (float 0..1) of a level layer: albedo x (ambient + lights) + emission x emis_k.
    `extra` = an RGB field (h, w, 3) added to the light (painted pools, bounce)."""
    alb = Ld['alb']
    h, w = alb.shape[:2]
    lf = np.zeros((h, w, 3), np.float32) + np.asarray(ambient, np.float32)[None, None]
    if lights:
        lf += light_field(h, w, Ld['nrm'], lights, origin)
    if extra is not None:
        lf += extra
    rgb = alb[..., :3] * lf * gain
    if Ld['emi'] is not None and emis_k > 0:
        e = Ld['emi']
        rgb = np.where(e[..., 3:4] > 0, np.maximum(rgb, e[..., :3] * emis_k), rgb)
    out = np.concatenate([np.clip(rgb, 0, 1), alb[..., 3:4]], -1)
    return out


def to8(a):
    """float RGBA 0..1 -> uint8 RGBA; alpha binarised (pixel art)."""
    out = np.clip(np.round(a * 255.0), 0, 255).astype(np.uint8)
    out[..., 3] = np.where(out[..., 3] > 127, 255, 0)
    return out


def hexf(h):
    return tuple(float(v) / 255.0 for v in Q.hexrgb(h))


def over(dst, src, x=0, y=0):
    """Alpha-composite float RGBA `src` onto `dst` at (x, y) (in place; clipped)."""
    H, W = dst.shape[:2]
    h, w = src.shape[:2]
    X0, Y0 = max(0, x), max(0, y)
    X1, Y1 = min(W, x + w), min(H, y + h)
    if X1 <= X0 or Y1 <= Y0:
        return dst
    s = src[Y0 - y:Y1 - y, X0 - x:X1 - x]
    a = s[..., 3:4]
    d = dst[Y0:Y1, X0:X1]
    d[..., :3] = s[..., :3] * a + d[..., :3] * (1 - a)
    d[..., 3:4] = np.maximum(d[..., 3:4], a)
    return dst


def grade(a, mul=(1, 1, 1), add=(0, 0, 0), sat=1.0):
    """Colour grade of a float RGBA (multiply, lift, saturation)."""
    rgb = a[..., :3]
    if sat != 1.0:
        g = rgb.mean(-1, keepdims=True)
        rgb = g + (rgb - g) * sat
    rgb = rgb * np.asarray(mul, np.float32) + np.asarray(add, np.float32)
    return np.concatenate([np.clip(rgb, 0, 1), a[..., 3:4]], -1)


def dither_quant(a, levels=24, seed=0):
    """Ordered-dither each channel to `levels` steps (keeps relit gradients pixel-crisp)."""
    h, w = a.shape[:2]
    th = Q.pg.bayer(w, h, seed, seed)[..., None] - 0.5
    rgb = np.floor(a[..., :3] * (levels - 1) + 0.5 + th * 0.9) / (levels - 1)
    return np.concatenate([np.clip(rgb, 0, 1), a[..., 3:4]], -1)


# ----------------------------------------------------------------------------------------------- the loop street
def _loop_mods():
    import env_c4_annex_kit as AK      # noqa: F401  (imported read-only by the street painter)
    import env_c4_annex_layout as AL
    import env_c4_annex_loop as LP
    return LP, AL


def _street_class():
    LP, AL = _loop_mods()

    class CineStreet(LP.Street):
        """The level's street, re-baked for the films: no tram (the films drive their own), the hour's sky."""

        def __init__(self, light='dawn', cfg=None, keep=None):
            super().__init__(cfg or {})
            self.hour = light
            self.keep = keep               # None = everything but the tram; a set = only these painters

        def tram(self):
            if self.keep is not None and 'tram' in self.keep:
                return super().tram()
            return None

        def scene_lights(self):
            if self.hour == 'morning':
                return [
                    {'name': 'day_sky', 'pos': (420.0, -80.0), 'kind': 'white', 'energy': 0.95, 'radius': 820,
                     'height': 140},
                    {'name': 'snow_bounce', 'pos': (420.0, 360.0), 'kind': 'white', 'energy': 0.5, 'radius': 460,
                     'height': 40},
                ]
            return super().scene_lights()

        def build(self):
            if self.keep is None:
                return super().build()
            for nm in ('tram',):
                if nm in self.keep:
                    getattr(self, nm)()
            self.ambient()
            return self.lay

    return CineStreet


def bake_street(light='dawn', bared=False, keep=None):
    """The baked street (TLayer: .c RGBA, .em emission mask) for the hour, without the tram."""
    LP, AL = _loop_mods()
    import env_c4_annex_kit as AK
    CS = _street_class()
    st = CS(light, {'bared': bared}, keep)
    st.build()
    lights = st.all_lights()
    if light == 'morning':                 # the sodium lamp is off in the morning
        lights = [dict(L, energy=float(L['energy']) * 0.25) if 'sodium' in str(L.get('name', '')) else L
                  for L in lights]
    F = AK.light_fields(st.lay, lights)
    AK.add_pools(F, lights, AL.BASE_Y + 6, AL.WORLD_H, AL.SEAM)
    AK.resolve(st.lay, F, exposure=0.92 if light == 'dawn' else 1.0)
    return st


def street_tram():
    """(rgba uint8, (x0, y0)) -- the level tram of line 74 alone (front to the LEFT), cropped with a margin."""
    LP, AL = _loop_mods()
    st = bake_street('dawn', keep={'tram'})
    t0, t1 = AL.TRAM
    y0, y1 = AL.TRAM_Y
    x0, x1 = t0 - 4, t1 + 4
    yy0, yy1 = AL.WIRE_Y - 2, y1 + 4
    return st.lay.c[yy0:yy1, x0:x1].copy(), (x0, yy0)
