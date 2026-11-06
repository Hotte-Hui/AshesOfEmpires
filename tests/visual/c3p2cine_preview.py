"""c3p2cine_preview -- quick offline composites of the Chapter-3 part-2 cinematic layers (owner: cinematics stream).

Not a test: a review tool for the art generators (tools/pixelgen/env_c3p2_cine*.py).  It composes the layers of
selected shots roughly as the runtime does (sprites over, glows added) from assets/cinematics/c3p2/ and
layout.json, crops the letterbox band (y 46..314) and writes one contact sheet (<= 1280 px wide):

    py -3 -P tests/visual/c3p2cine_preview.py OUT.png radio|fire|escape|halves [--scale 1]
The final review happens in the game (tests/visual/c3cine_harness.tscn with --c3-id=LS_C3_...).
"""
from __future__ import annotations

import json
import os
import sys

import numpy as np
from PIL import Image

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
A = os.path.join(ROOT, 'assets', 'cinematics', 'c3p2')


def load(rel):
    p = os.path.join(A, rel)
    if not os.path.exists(p):
        return None
    return np.asarray(Image.open(p).convert('RGBA')).copy()


def frame(img, i, n):
    w = img.shape[1] // n
    return img[:, i * w:(i + 1) * w]


def over(dst, src, x, y):
    if src is None:
        return dst
    h, w = src.shape[:2]
    X0, Y0, X1, Y1 = max(0, x), max(0, y), min(dst.shape[1], x + w), min(dst.shape[0], y + h)
    if X1 <= X0 or Y1 <= Y0:
        return dst
    s = src[Y0 - y:Y1 - y, X0 - x:X1 - x]
    m = s[..., 3] > 0
    dst[Y0:Y1, X0:X1][m] = s[m]
    return dst


def add(dst, src, x=0, y=0):
    if src is None:
        return dst
    h, w = src.shape[:2]
    X0, Y0, X1, Y1 = max(0, x), max(0, y), min(dst.shape[1], x + w), min(dst.shape[0], y + h)
    s = src[Y0 - y:Y1 - y, X0 - x:X1 - x, :3].astype(np.int32)
    d = dst[Y0:Y1, X0:X1, :3].astype(np.int32)
    dst[Y0:Y1, X0:X1, :3] = np.clip(d + s, 0, 255).astype(np.uint8)
    return dst


def canvas():
    c = np.zeros((360, 640, 4), np.uint8)
    c[..., 3] = 255
    return c


def shots(part, L):
    out = []
    if part == 'radio':
        R = L.get('radio', {})
        c = over(canvas(), load('radio/square_bg.png'), 0, 0)
        for k in ('konrad', 'alexei'):
            over(c, load('radio/win_%s.png' % k), *R['win_' + k])
        add(c, load('radio/square_glow.png'))
        st = load('radio/steam.png')
        if st is not None:
            over(c, frame(st, 2, 6), 40, 250)
            over(c, frame(st, 4, 6), 300, 268)
        out.append(('r1', c))
        for kind in ('alexei', 'konrad'):
            c = over(canvas(), load('radio/room_%s.png' % kind), 0, 0)
            over(c, load('radio/radio.png'), *R['radio'])
            add(c, load('radio/dial_glow.png'))
            if kind == 'konrad':
                add(c, load('radio/lamp_glow.png'))
                hk = load('radio/hand_konrad.png')
                over(c, frame(hk, 1, 5), *R['hand_konrad'])
            else:
                st = load('radio/steam_tea.png')
                over(c, frame(st, 1, 6), *R['steam_tea'])
                arm = load('radio/arm_alexei.png')
                over(c, frame(arm, 2, 4), *R['arm_alexei'])
            fig = load('radio/fig_%s.png' % kind)
            over(c, frame(fig, 0, 2), *R['fig_' + kind])
            out.append(('r2' if kind == 'alexei' else 'r3', c))
        c = over(canvas(), load('radio/doors.png'), 0, 0)
        nf = load('radio/note_fold.png')
        for cx in R.get('door_cx', [160, 480]):
            over(c, nf, cx - 23, R['door_floor'] + 10)
        out.append(('r4', c))
        out.append(('r4b', over(canvas(), load('radio/note_close.png'), 0, 0)))
        c = over(canvas(), load('radio/cafe.png'), 0, 0)
        add(c, load('radio/cafe_glow.png'))
        out.append(('r5', c))
        c = over(canvas(), load('radio/square_bg.png'), 0, 0)
        add(c, load('radio/square_glow.png'))
        for k in ('konrad', 'alexei'):
            over(c, load('radio/door_%s.png' % k), *R['door_' + k])
            wk = load('radio/walker_%s.png' % k)
            pth = R['path_' + k][30]
            fw = wk.shape[1] // 4
            over(c, frame(wk, 1, 4), int(pth[0] - fw / 2), int(pth[1] - wk.shape[0]))
        out.append(('r6', c))
    else:
        P = L.get(part, {})
        for spec in P.get('preview', []):
            c = canvas()
            for item in spec['layers']:
                img = load(item[0])
                if img is None:
                    continue
                if len(item) > 3 and item[3] > 1:
                    img = frame(img, item[4] if len(item) > 4 else 0, item[3])
                if len(item) > 2 and item[2] == 'add':
                    add(c, img, *item[1])
                else:
                    over(c, img, *item[1])
            out.append((spec['id'], c))
    return out


def main():
    out_path, part = sys.argv[1], sys.argv[2]
    with open(os.path.join(A, 'layout.json'), encoding='utf-8') as f:
        L = json.load(f)
    tiles = shots(part, L)
    cols = 2
    tw, th = 640, 268
    rows = (len(tiles) + cols - 1) // cols
    sheet = Image.new('RGB', (tw * cols, th * rows), (0, 0, 0))
    for i, (sid, c) in enumerate(tiles):
        im = Image.fromarray(c[46:314, :, :3])
        sheet.paste(im, ((i % cols) * tw, (i // cols) * th))
    sheet.save(out_path)
    print('preview', part, len(tiles), 'tiles ->', out_path)


if __name__ == '__main__':
    main()
