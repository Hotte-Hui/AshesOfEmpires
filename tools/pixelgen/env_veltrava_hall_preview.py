"""env_veltrava_hall_preview -- composite previews of assets/environments/veltrava_hall/scene.json.

Reproduces the runtime placement of scripts/levels/layer_stack.gd:
    screen_x = pos.x - cam_x * parallax.x   (camera y is always 0 in this 360 px tall level)
    props y-sorted by base_y inside the Playfield (z 0), fx anim sprites at their z (frame 0 here),
    emission <name>_e.png added on top (additive, unshaded) at 0.22.
'lit' previews approximate CanvasModulate + PointLight2D with normal maps (Lambert + light height).
Konrad's real sprite (assets/characters/konrad, frame 0) stands in for scale; NPC anchors get grey
placeholder silhouettes (the C3 characters are another stream).  Review aid only -- not a renderer.

Run:  python3 -P tools/pixelgen/env_veltrava_hall_preview.py [OUT_DIR] [--hist]
"""
from __future__ import annotations

import json
import os
import sys

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))
ENV_DIR = os.path.join(ROOT, 'assets', 'environments', 'veltrava_hall')
VIEW_W, VIEW_H = 640, 360
_CACHE: dict = {}


def _img(path):
    if path not in _CACHE:
        _CACHE[path] = (np.asarray(Image.open(path).convert('RGBA'), np.float32) / 255.0) if os.path.exists(path) \
            else None
    return _CACHE[path]


def _hex(h):
    h = h.lstrip('#')
    return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], np.float32) / 255.0


def konrad_frame():
    p = os.path.join(ROOT, 'assets', 'characters', 'konrad')
    try:
        meta = json.load(open(os.path.join(p, 'sheet.json'), encoding='utf-8'))
        sheet = _img(os.path.join(p, 'sheet.png'))
        cw, ch = meta['cell']
        ox, oy = meta['origin']
        return sheet[0:ch, 0:cw], (ox, oy)
    except (OSError, KeyError, ValueError, TypeError):
        return None, (0, 0)


def npc_silhouette(h=46, w=12):
    a = np.zeros((h + 2, w + 2, 4), np.float32)
    a[8:h, 2:w, :3] = (0.16, 0.18, 0.2)
    a[8:h, 2:w, 3] = 1
    a[1:8, 4:w - 2, :3] = (0.55, 0.45, 0.4)
    a[1:8, 4:w - 2, 3] = 1
    return a, (w // 2 + 1, h)


def compose(scene, cx, lit=False, figures=True, hist=False):
    out = np.zeros((VIEW_H, VIEW_W, 3), np.float32)
    nrm = np.zeros((VIEW_H, VIEW_W, 3), np.float32); nrm[..., 2] = 1
    litm = np.zeros((VIEW_H, VIEW_W), bool)
    emis = np.zeros((VIEW_H, VIEW_W, 3), np.float32)
    items = []
    for ly in scene['layers']:
        items.append((ly['z'], 0, 'layer', ly))
    for pr in scene['props']:
        items.append((pr.get('z', 0), pr['base_y'], 'prop', pr))
    for fx in scene.get('fx', []):
        if fx.get('type') == 'anim_sprite':
            items.append((fx.get('z', -20), 0, 'fx', fx))
    figs = []
    if figures:
        k, ko = konrad_frame()
        px_ = scene['spawns']['SP_C3_Vestibule'][0] if cx < 120 else cx + 320
        if k is not None:
            figs.append((0, 300, 'fig', (k, ko, px_)))
        sil = npc_silhouette()
        for name, info in scene.get('npcs', {}).items():
            if name == 'alexei':
                continue
            figs.append((0, info['feet'][1] - 0.5, 'fig', (sil[0], sil[1], info['feet'][0])))
    items += [(z, by, kind, d) for (z, by, kind, d) in figs]
    items.sort(key=lambda t: (t[0], t[1]))

    def blit(arr, x, y, is_lit, narr=None, earr=None):
        if arr is None:
            return
        h, w = arr.shape[:2]
        X0, Y0, X1, Y1 = max(0, x), max(0, y), min(VIEW_W, x + w), min(VIEW_H, y + h)
        if X1 <= X0 or Y1 <= Y0:
            return
        sub = arr[Y0 - y:Y1 - y, X0 - x:X1 - x]
        a = sub[..., 3:4]
        solid = a > 0.5
        if (a < 0.5).all() and a.max() > 0:      # soft veil layer: plain alpha blend
            out[Y0:Y1, X0:X1] = out[Y0:Y1, X0:X1] * (1 - a) + sub[..., :3] * a
            return
        out[Y0:Y1, X0:X1] = np.where(solid, sub[..., :3], out[Y0:Y1, X0:X1])
        m = solid[..., 0]
        litm[Y0:Y1, X0:X1] = np.where(m, is_lit, litm[Y0:Y1, X0:X1])
        if narr is not None:
            n = narr[Y0 - y:Y1 - y, X0 - x:X1 - x, :3] * 2 - 1
            nrm[Y0:Y1, X0:X1] = np.where(solid, n, nrm[Y0:Y1, X0:X1])
        else:
            nrm[Y0:Y1, X0:X1] = np.where(solid, np.array([0, 0, 1.0]), nrm[Y0:Y1, X0:X1])
        emis[Y0:Y1, X0:X1] = np.where(solid, 0, emis[Y0:Y1, X0:X1])
        if earr is not None:
            e = earr[Y0 - y:Y1 - y, X0 - x:X1 - x]
            emis[Y0:Y1, X0:X1] += e[..., :3] * e[..., 3:4] * 0.22

    def files(rel):
        base = os.path.join(ENV_DIR, rel[:-4])
        main = base + '.png'
        if hist and os.path.exists(base + '_hist.png'):
            main = base + '_hist.png'
        return _img(main), _img(base + '_n.png'), _img(base + '_e.png')

    for z, by, kind, d in items:
        if kind == 'layer':
            c, n, e = files(d['file'])
            x = int(round(d['pos'][0] - cx * d['parallax'][0]))
            blit(c, x, int(d['pos'][1]), d.get('lit', False), n if d.get('normal') else None,
                 e if d.get('emission') else None)
        elif kind == 'prop':
            c, n, e = files(d['file'])
            blit(c, d['pos'][0] - cx, d['pos'][1], True, n, e if d.get('emission') else None)
        elif kind == 'fx':
            strip = _img(os.path.join(ENV_DIR, d['file']))
            fw = strip.shape[1] // int(d.get('frames', 1))
            pv = d['parallax'][0] if isinstance(d['parallax'], list) else d['parallax']
            fr = strip[:, 0:fw].copy()
            # fx strips use soft alpha: treat >0 as visible
            fr[..., 3] = np.where(fr[..., 3] > 0, np.maximum(fr[..., 3], 0.6), 0)
            blit(fr, int(round(d['pos'][0] - cx * pv)), d['pos'][1], False)
        else:
            arr, (ox, oy), fxw = d
            blit(arr, int(fxw - cx - ox), int(300 - oy) if by >= 299 else int(by + 0.5 - oy), True)
    if lit:
        mod = _hex(scene['canvas_modulate'])
        shade = np.ones((VIEW_H, VIEW_W, 3), np.float32) * mod
        ys, xs = np.mgrid[0:VIEW_H, 0:VIEW_W].astype(np.float32)
        for lt in scene['lights']:
            lx, lyy = lt['pos']
            dx = lx - (xs + cx); dyu = -(lyy - ys); dz = float(lt['height'])
            d2 = np.sqrt(dx * dx + dyu * dyu)
            d3 = np.sqrt(dx * dx + dyu * dyu + dz * dz) + 1e-6
            ndl = np.clip((nrm[..., 0] * dx + nrm[..., 1] * dyu + nrm[..., 2] * dz) / d3, 0, 1)
            att = np.clip(1 - d2 / lt['radius'], 0, 1) ** 1.5
            shade += (_hex(lt['color']) * lt['energy'])[None, None, :] * (ndl * att)[..., None]
        out = np.where(litm[..., None], out * shade, out * mod)
        out = out + emis
    return Image.fromarray((np.clip(out, 0, 1) * 255).astype(np.uint8), 'RGB')


def render_all(out_dir, hist=False):
    os.makedirs(out_dir, exist_ok=True)
    if os.path.abspath(out_dir).startswith(os.path.abspath(ROOT)):
        open(os.path.join(out_dir, '.gdignore'), 'a').close()
    _CACHE.clear()
    scene = json.load(open(os.path.join(ENV_DIR, 'scene.json'), encoding='utf-8'))
    names = []
    for cx in (0, 640, 1280):
        for lit in (False, True):
            im = compose(scene, cx, lit=lit, hist=hist)
            fn = os.path.join(out_dir, 'prev_cam%04d_%s%s.png' % (cx, 'lit' if lit else 'albedo',
                                                                 '_hist' if hist else ''))
            im.resize((VIEW_W * 3, VIEW_H * 3), Image.NEAREST).save(fn)
            names.append(fn)
    world = Image.new('RGB', (1920, 360))
    for cx in range(0, 1281, 320):
        world.paste(compose(scene, cx, lit=False, figures=False, hist=hist), (cx, 0))
    fn = os.path.join(out_dir, 'prev_world%s.png' % ('_hist' if hist else ''))
    world.save(fn)
    names.append(fn)
    print('  previews:', len(names), 'files in', out_dir)
    return names


if __name__ == '__main__':
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    render_all(args[0] if args else os.path.join(ENV_DIR, '_preview'), hist='--hist' in sys.argv)
