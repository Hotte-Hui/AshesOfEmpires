"""env_karsk_skyline_preview -- review composites of the Karsk scene with the skyline layers swapped in.

Reproduces the runtime rules of scripts/levels/layer_stack.gd (same as env_karsk_preview, re-implemented here
so the skyline tools never import the railyard generator):
    screen_x = pos.x - cam_x * parallax.x  (camera y is 0);  props y-sorted by base_y;  fog_band 'y' = centre;
    emission <name>_e.png added unshaded at emission_strength;  'lit' layers multiplied by canvas_modulate.
It is an approximation for art review (no PointLights, no post grade) -- the in-engine capture is the judge.
"""
from __future__ import annotations

import json
import os

import numpy as np
from PIL import Image

_CACHE = {}
BAYER4 = (np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]], np.float32) + 0.5) / 16.0


def _load(path):
    if path not in _CACHE:
        _CACHE[path] = np.asarray(Image.open(path).convert('RGBA')).copy()
    return _CACHE[path]


def clear_cache():
    _CACHE.clear()


def _hexrgb(h):
    h = h.lstrip('#')
    return np.array([int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)], np.float32)


def resolve(base_dir, f):
    if f.startswith('res://'):
        return 'C:/Spiele/AshesOfEmpires/' + f[6:]
    return os.path.normpath(os.path.join(base_dir, f))


def compose(manifest_path, cam_x, lit=True, frame=0, view=(640, 360), overrides=None, hide=(), only=None):
    """overrides: {layer name: {'rgba': arr, 'em': arr|None}} replaces a layer's pixels in memory.
    hide: layer names / 'props' / 'fx' / 'fog' to skip.  only: if given, draw only these layer names (+ sky)."""
    man = json.load(open(manifest_path, encoding='utf-8'))
    base_dir = os.path.dirname(manifest_path)
    overrides = overrides or {}
    VW, VH = view
    rgb = np.zeros((VH, VW, 3), np.float32)
    litm = np.zeros((VH, VW), bool)
    emis = np.zeros((VH, VW, 3), np.float32)
    cover = np.zeros((VH, VW), np.int16)       # index of the layer that owns each pixel (for sun checks)
    names = []

    def draw(img, x, y, is_lit, eimg=None, estr=0.22, alpha_mul=1.0, tag=0):
        h, w = img.shape[:2]
        X0, Y0, X1, Y1 = max(0, x), max(0, y), min(VW, x + w), min(VH, y + h)
        if X1 <= X0 or Y1 <= Y0:
            return
        s = img[Y0 - y:Y1 - y, X0 - x:X1 - x].astype(np.float32)
        a = (s[..., 3] / 255.0) * alpha_mul
        m = a > 0.5
        d = rgb[Y0:Y1, X0:X1]
        d[:] = d * (1 - a[..., None]) + s[..., :3] * a[..., None]
        litm[Y0:Y1, X0:X1][m] = is_lit
        emis[Y0:Y1, X0:X1][m] = 0
        cover[Y0:Y1, X0:X1][m] = tag
        if eimg is not None:
            e = eimg[Y0 - y:Y1 - y, X0 - x:X1 - x]
            em = e[..., 3] > 0
            emis[Y0:Y1, X0:X1][em] = e[..., :3][em].astype(np.float32) * estr

    items, order = [], 0
    for Ly in man['layers']:
        items.append((Ly['z'], 0, 0, order, 'layer', Ly))
        order += 1
    for F in man.get('fx', []):
        if F['type'] in ('anim_sprite', 'fog_band'):
            items.append((F.get('z', -20 if F['type'] == 'anim_sprite' else -15), 0, 0, order, F['type'], F))
            order += 1
    for P in man.get('props', []):
        items.append((P.get('z', 0), 1, P['base_y'], order, 'prop', P))
        order += 1
    items.sort(key=lambda t: (t[0], t[1], t[2], t[3]))
    for z, grp, by, _, kind, D in items:
        if kind == 'layer':
            nm = D['name']
            if nm in hide or (only is not None and nm not in only and nm != 'sky'):
                continue
            names.append(nm)
            tag = len(names)
            par = D.get('parallax', [1, 1])
            sx = int(round(D['pos'][0] - cam_x * par[0]))
            sy = int(round(D['pos'][1]))
            if nm in overrides:
                img = overrides[nm]['rgba']
                eimg = overrides[nm].get('em') if D.get('emission', True) else None
            else:
                path = resolve(base_dir, D['file'])
                img = _load(path)
                ef = path[:-4] + '_e.png'
                eimg = _load(ef) if D.get('emission') and os.path.exists(ef) else None
            draw(img, sx, sy, bool(D.get('lit', True)), eimg, float(D.get('emission_strength', 0.22)), tag=tag)
        elif kind == 'prop':
            if 'props' in hide or only is not None:
                continue
            path = resolve(base_dir, D['file'])
            img = _load(path)
            ef = path[:-4] + '_e.png'
            eimg = _load(ef) if D.get('emission') and os.path.exists(ef) else None
            draw(img, int(D['pos'][0] - cam_x), int(D['pos'][1]), True, eimg, 0.22, tag=99)
        elif kind == 'anim_sprite':
            if 'fx' in hide or (only is not None and D.get('layer') not in only):
                continue
            img = _load(resolve(base_dir, D['file']))
            n = D['frames']
            fw = img.shape[1] // n
            f = (frame + D['pos'][0]) % n
            fr = img[:, f * fw:(f + 1) * fw]
            par = D.get('parallax', 1.0)
            par = par[0] if isinstance(par, list) else par
            draw(fr, int(round(D['pos'][0] - cam_x * par)), int(D['pos'][1]), bool(D.get('lit', False)),
                 alpha_mul=float(D.get('alpha', 1.0)), tag=98)
        elif kind == 'fog_band':
            if 'fog' in hide or only is not None:
                continue
            hh = int(D['height'])
            y0 = int(D['y'] - hh * 0.5)
            col = _hexrgb(D['color'])
            a = float(D['alpha'])
            for i in range(hh):
                yy = y0 + i
                if not (0 <= yy < VH):
                    continue
                vy = 1.0 - abs((i / max(1.0, hh - 1.0)) * 2.0 - 1.0)
                dens = vy * a
                th = BAYER4[yy % 4][np.arange(VW) % 4]
                al = np.where(dens * 2.0 > th, np.clip(dens * 1.6, 0.12, 0.6), 0.0)[:, None]
                rgb[yy] = rgb[yy] * (1 - al) + col * al
    if lit:
        mod = _hexrgb(man.get('canvas_modulate', '#ffffff')) / 255.0
        out = np.where(litm[..., None], rgb * mod[None, None, :], rgb) + emis
    else:
        out = rgb + emis
    return np.clip(out, 0, 255).astype(np.uint8), cover, names


def sun_visibility(cover, names, sun=(612, 190), r=8.5):
    """Fraction of the sun disc not covered by any layer except sky / clouds."""
    yy, xx = np.mgrid[0:cover.shape[0], 0:cover.shape[1]]
    disc = (xx - sun[0]) ** 2 + (yy - sun[1]) ** 2 <= r * r
    ok = {0}
    for i, nm in enumerate(names):
        if nm in ('sky', 'clouds'):
            ok.add(i + 1)
    free = np.isin(cover, list(ok)) & disc
    return float(free.sum()) / float(disc.sum())


def save(arr, path, scale=1):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    im = Image.fromarray(arr, 'RGB')
    if scale != 1:
        im = im.resize((im.width * scale, im.height * scale), Image.NEAREST)
    im.save(path)


def crop(arr, box, path, scale=3):
    x0, y0, x1, y1 = box
    im = Image.fromarray(arr[y0:y1, x0:x1], 'RGB')
    im.resize((im.width * scale, im.height * scale), Image.NEAREST).save(path)
