"""env_veltrava_station_preview -- composite previews of assets/environments/veltrava_station/scene.json.

Reproduces the runtime rules of scripts/levels/layer_stack.gd:
    screen_x = pos.x - cam_x * parallax.x      (the camera never moves vertically in this level)
    props: y-sorted by base_y inside the Playfield (z 0); fx anim sprites / fog bands live in the Backdrop
    fog_band: 'y' is the band centre; ordered-dither alpha band
    emission: <name>_e.png added on top (additive, unshaded) at emission_strength (props: 0.22)
    hist: Symbols.pick -> <name>_hist.png when the historical-insignia setting is on
The 'lit' variant approximates CanvasModulate + PointLight2D with the normal maps (Lambert, light height).
Approximations for art review, not a renderer.

    python3 -P tools/pixelgen/env_veltrava_station_preview.py [--out=DIR] [--hist] [--frame=N]
Writes world_cam0000/0640/1280.png (640x360), *_x3.png (1920x1080), *_lit_x3.png and a scroll-stitched
panorama into DIR (default: <system temp>/veltrava_station_preview; never into the repo).
"""
from __future__ import annotations

import json
import os
import sys
import tempfile

import numpy as np
from PIL import Image

_HERE = os.path.dirname(os.path.abspath(__file__))
ENV = os.path.normpath(os.path.join(_HERE, '..', '..', 'assets', 'environments', 'veltrava_station'))
BAYER4 = (np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]], np.float32) + 0.5) / 16.0
_CACHE = {}


def _load(path):
    if path not in _CACHE:
        _CACHE[path] = np.asarray(Image.open(path).convert('RGBA')).copy()
    return _CACHE[path]


def _hexrgb(h):
    h = h.lstrip('#')
    return np.array([int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)], np.float32)


def _pick(env, rel, hist):
    if hist:
        b, e = os.path.splitext(rel)
        if os.path.exists(os.path.join(env, b + '_hist' + e)):
            return os.path.join(env, b + '_hist' + e)
    return os.path.join(env, rel)


class _Canvas:
    def __init__(self, W, H):
        self.W, self.H = W, H
        self.rgb = np.zeros((H, W, 3), np.float32)
        self.lit = np.zeros((H, W), bool)
        self.nrm = np.zeros((H, W, 3), np.float32)
        self.nrm[..., 2] = 1
        self.emis = np.zeros((H, W, 3), np.float32)

    def draw(self, img, x, y, lit=False, nimg=None, eimg=None, estr=0.22, alpha_mul=1.0):
        H, W = self.H, self.W
        h, w = img.shape[:2]
        X0, Y0, X1, Y1 = max(0, x), max(0, y), min(W, x + w), min(H, y + h)
        if X1 <= X0 or Y1 <= Y0:
            return
        s = img[Y0 - y:Y1 - y, X0 - x:X1 - x].astype(np.float32)
        a = (s[..., 3] / 255.0) * alpha_mul
        m = a > 0.5
        d = self.rgb[Y0:Y1, X0:X1]
        d[:] = d * (1 - a[..., None]) + s[..., :3] * a[..., None]
        self.lit[Y0:Y1, X0:X1][m] = lit
        self.emis[Y0:Y1, X0:X1][m] = 0
        if nimg is not None:
            n = nimg[Y0 - y:Y1 - y, X0 - x:X1 - x, :3].astype(np.float32) / 127.5 - 1
            self.nrm[Y0:Y1, X0:X1][m] = n[m]
        elif m.any():
            self.nrm[Y0:Y1, X0:X1][m] = (0, 0, 1)
        if eimg is not None:
            e = eimg[Y0 - y:Y1 - y, X0 - x:X1 - x]
            em = (e[..., 3] > 0)
            self.emis[Y0:Y1, X0:X1][em] = e[..., :3][em].astype(np.float32) * estr


def compose(env_dir=ENV, cam_x=0, lit=False, frame=0, view=(640, 360), hist=False):
    man = json.load(open(os.path.join(env_dir, 'scene.json'), encoding='utf-8'))
    VW, VH = view
    C = _Canvas(VW, VH)
    items = []
    order = 0
    for Ly in man['layers']:
        items.append((Ly['z'], 0, 0, order, 'layer', Ly))
        order += 1
    for F in man.get('fx', []):
        if F['type'] in ('anim_sprite', 'fog_band', 'smoke', 'steam'):
            items.append((F.get('z', -20 if F['type'] != 'fog_band' else -15), 0, 0, order, F['type'], F))
            order += 1
    for P in man.get('props', []):
        items.append((P.get('z', 0), 1, P['base_y'], order, 'prop', P))
        order += 1
    items.sort(key=lambda t: (t[0], t[1], t[2], t[3]))
    for z, grp, by, _, kind, D in items:
        if kind in ('layer', 'prop'):
            path = _pick(env_dir, D['file'], hist)
            img = _load(path)
            par = D.get('parallax', [1, 1])
            sx = int(round(D['pos'][0] - cam_x * par[0]))
            sy = int(round(D['pos'][1]))
            base = os.path.join(env_dir, D['file'][:-4])
            nimg = _load(base + '_n.png') if D.get('normal') and os.path.exists(base + '_n.png') else None
            eimg = _load(base + '_e.png') if D.get('emission') and os.path.exists(base + '_e.png') else None
            estr = float(D.get('emission_strength', 0.22))
            C.draw(img, sx, sy, lit=bool(D.get('lit', True)), nimg=nimg, eimg=eimg, estr=estr)
        elif kind in ('anim_sprite', 'smoke', 'steam'):
            img = _load(_pick(env_dir, D['file'], hist))
            n = D['frames']
            fw = img.shape[1] // n
            f = (frame + D['pos'][0] // 7 + D['pos'][1] // 5) % n
            fr = img[:, f * fw:(f + 1) * fw]
            par = D.get('parallax', 1.0)
            par = par[0] if isinstance(par, list) else par
            sx = int(round(D['pos'][0] - cam_x * par))
            eimg = fr if D.get('emission') else None
            C.draw(fr, sx, int(D['pos'][1]), lit=bool(D.get('lit', False)), alpha_mul=float(D.get('alpha', 1.0)),
                   eimg=eimg, estr=0.22 if eimg is not None else 0.0)
        elif kind == 'fog_band':
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
                th = BAYER4[i % 4][np.arange(VW) % 4]
                al = np.where(dens * 2.0 > th, np.clip(dens * 1.6, 0.12, 0.6), 0.0)[:, None]
                C.rgb[yy] = C.rgb[yy] * (1 - al) + col * al
    rgb = C.rgb
    if lit:
        mod = _hexrgb(man.get('canvas_modulate', '#ffffff')) / 255.0
        acc = np.zeros_like(rgb)
        yy, xx = np.mgrid[0:VH, 0:VW].astype(np.float32)
        lay_par = {Ly['name']: Ly['parallax'][0] for Ly in man['layers']}
        for Lt in man.get('lights', []):
            par = lay_par.get(Lt.get('on_layer', 'playfield'), 1.0)
            lx = Lt['pos'][0] - cam_x * par
            ly = Lt['pos'][1]
            r = Lt['radius']
            d = np.sqrt((xx - lx) ** 2 + (yy - ly) ** 2)
            t = np.clip(d / r, 0, 1)
            fall = np.clip(np.where(t < 0.45, 1 - t / 0.45 * 0.58, 0.42 * (1 - (t - 0.45) / 0.55)), 0, 1)
            if not (fall > 0).any():
                continue
            hgt = float(Lt.get('height', 24))
            Lv = np.stack([lx - xx, -(ly - yy), np.full_like(xx, hgt)], -1)
            Lv /= np.linalg.norm(Lv, axis=-1, keepdims=True)
            ndl = np.clip((C.nrm * Lv).sum(-1), 0, 1)
            c = _hexrgb(Lt['color']) / 255.0
            acc += (fall * ndl * Lt['energy'])[..., None] * c[None, None, :]
        lm = C.lit[..., None]
        rgb = np.where(lm, rgb * (mod[None, None, :] + acc), rgb * mod[None, None, :]) + C.emis
    return np.clip(rgb, 0, 255).astype(np.uint8)


def save(arr, path, scale=1):
    im = Image.fromarray(arr, 'RGB')
    if scale != 1:
        im = im.resize((im.width * scale, im.height * scale), Image.NEAREST)
    im.save(path)


def crop3(arr, box, path):
    x0, y0, x1, y1 = box
    im = Image.fromarray(arr[y0:y1, x0:x1], 'RGB')
    im.resize((im.width * 3, im.height * 3), Image.NEAREST).save(path)


def run(out_dir=None, hist=False, frame=0, crops=None):
    out_dir = out_dir or os.path.join(tempfile.gettempdir(), 'veltrava_station_preview')
    os.makedirs(out_dir, exist_ok=True)
    _CACHE.clear()
    tag = '_hist' if hist else ''
    for cam in (0, 640, 1280):
        img = compose(ENV, cam, lit=False, frame=frame, hist=hist)
        save(img, os.path.join(out_dir, 'world_cam%04d%s.png' % (cam, tag)))
        save(img, os.path.join(out_dir, 'world_cam%04d%s_x3.png' % (cam, tag)), 3)
        lit = compose(ENV, cam, lit=True, frame=frame, hist=hist)
        save(lit, os.path.join(out_dir, 'world_cam%04d%s_lit_x3.png' % (cam, tag)), 3)
    for name, (cam, box) in (crops or {}).items():
        img = compose(ENV, cam, lit=False, frame=frame, hist=hist)
        crop3(img, box, os.path.join(out_dir, name + tag + '_x3.png'))
    pano = np.zeros((360, 1920, 3), np.uint8)
    for cam in range(0, 1281, 64):
        pano[:, cam:cam + 640] = compose(ENV, cam, lit=False, frame=frame, hist=hist)
    save(pano, os.path.join(out_dir, 'world_panorama%s.png' % tag))
    return out_dir


if __name__ == '__main__':
    out = None
    fr = 0
    for a in sys.argv[1:]:
        if a.startswith('--out='):
            out = a.split('=', 1)[1]
        elif a.startswith('--frame='):
            fr = int(a.split('=', 1)[1])
    print('previews ->', run(out, hist='--hist' in sys.argv, frame=fr))
