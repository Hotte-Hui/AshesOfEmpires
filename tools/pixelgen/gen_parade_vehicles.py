"""gen_parade_vehicles -- detail textures for the parade vehicles of L_M1_Parade (owner: parade).
Original, deterministic (no randomness, no references).  The vehicles are original fictional 1960s designs built
procedurally in scripts/levels/parade/parade_vehicles.gd; these maps only add the small structure the geometry
cannot carry at 1 texel ~ 1 game pixel (32 texels per metre, the knee-height barrier shot p3).
Every map is a MULTIPLY detail map for pixel3d_toon (grey = 1.0 keeps the vertex colour, darker greys shade it);
the few coloured decals (lens, glass) are drawn in pg.PALETTES['berlin'] colours and used with a white vertex
colour.  The 3D post snaps everything to the 'berlin' palette anyway.
Outputs (assets/architecture/parade/vehicles/):
  track.png    48 x 32, tiles in u (1.5 m = 8 links of 0.1875 m).  v 0..8 = outer edge of the links (end
               connectors, pins), v 8..32 = the tread face (plates, grouser bars, centre guide horns).
  wheels.png   128 x 32: four 32 x 32 wheel faces (road wheel, drive sprocket, idler, half-track front wheel).
  decals.png   128 x 64 atlas (regions in DECALS below, alpha-scissored): neutral white, louvre grille, tarp folds,
               crate planks, bolt row, weld bead, armoured visor with slits, radiator grille, jerry can, lens, glass.
Run: py -3 -P tools/pixelgen/gen_parade_vehicles.py
"""
from __future__ import annotations
import math
import os
import sys

import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pg  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
OUT = os.path.join(ROOT, 'assets', 'architecture', 'parade', 'vehicles')
B = pg.PALETTES['berlin']

# atlas regions (x, y, w, h) in decals.png -- mirrored as constants in parade_vehicles.gd (DEC_*)
DECALS = {
    'white': (0, 0, 8, 8),
    'louvre': (8, 0, 32, 16),
    'tarp': (40, 0, 32, 16),
    'planks': (72, 0, 16, 16),
    'bolts': (88, 0, 32, 4),
    'weld': (88, 4, 32, 4),
    'visor': (0, 16, 32, 16),
    'radiator': (32, 16, 32, 24),
    'jerry': (64, 16, 12, 16),
    'lens': (80, 16, 8, 8),
    'glass': (88, 16, 8, 4),
}


def grey(v):
    g = int(round(max(0.0, min(1.0, v)) * 255))
    return (g, g, g, 255)


def rgba(h):
    r, g, b = pg.hx(h)[:3]
    return (int(r), int(g), int(b), 255)


# ------------------------------------------------------------------------------------------------ track
def track():
    W, H = 48, 32
    img = np.zeros((H, W, 4), np.uint8)
    for x in range(W):
        k = x % 6                       # 6 texels per link
        for y in range(H):
            if y < 8:                   # outer edge: link side, end connector + wedge bolt at every joint
                if k == 0:
                    v = 0.30
                elif k == 1:
                    v = 0.95 if 2 <= y <= 5 else 0.62
                    if y == 3:
                        v = 1.0
                else:
                    v = 0.74
                    if y == 0:
                        v = 0.88
                    elif y == 7:
                        v = 0.50
                    if k == 4 and y in (3, 4):
                        v = 0.58          # lightening hole in the link side
            else:                       # tread face across the track width (24 texels ~ 0.58 m)
                yy = y - 8
                if k == 0:
                    v = 0.28
                else:
                    v = 0.78
                    if k == 3:
                        v = 0.92          # grouser bar
                    if k == 5:
                        v = 0.60
                    if yy in (0, 23):
                        v *= 0.72
                    if 10 <= yy <= 13:    # centre guide horn (bright cast tooth) + its shadow
                        v = 1.0 if k in (2, 3) else (0.45 if k == 4 else v)
                    if yy in (5, 18) and k in (1, 5):
                        v = 0.5           # pin bosses
            img[y, x] = grey(v)
    Image.fromarray(img, 'RGBA').save(os.path.join(OUT, 'track.png'))


# ------------------------------------------------------------------------------------------------ wheels
def _wheel(img, ox, kind):
    S = 32
    c = (S - 1) / 2.0
    for y in range(S):
        for x in range(S):
            dx, dy = x - c, y - c
            r = math.hypot(dx, dy)
            a = math.atan2(dy, dx)
            v = None
            if kind == 'road':
                if r > 15.6:
                    v = 0.0
                elif r > 13.0:
                    v = 0.34 + (0.06 if int(a * 24 / math.pi) % 2 == 0 and r > 14.5 else 0.0)   # rubber tyre
                elif r > 12.0:
                    v = 0.95                                                             # steel rim edge
                elif r > 6.0:
                    v = 0.74 + 0.10 * (dy < 0) - 0.08 * (r > 10.5)                       # dished disc
                    for k in range(6):                                                   # lightening holes
                        ha = k * math.pi / 3.0 + math.pi / 6.0
                        hx, hy = c + 9.0 * math.cos(ha), c + 9.0 * math.sin(ha)
                        d = math.hypot(x - hx, y - hy)
                        if d < 1.9:
                            v = 0.22
                        elif d < 2.6 and (y - hy) > 0:
                            v = 0.98
                else:
                    v = 0.90 if r < 3.0 else 0.70
                    for k in range(8):                                                   # hub bolts
                        ba = k * math.pi / 4.0
                        if math.hypot(x - (c + 4.6 * math.cos(ba)), y - (c + 4.6 * math.sin(ba))) < 0.9:
                            v = 1.0
                    if r < 1.2:
                        v = 0.5
            elif kind == 'sprocket':
                if r > 15.6:
                    v = 0.0
                elif r > 12.5:
                    v = 0.80 - 0.18 * (r > 14.6)
                elif r > 4.5:
                    v = 0.70 + 0.12 * (dy < 0)
                    for k in range(6):
                        ha = k * math.pi / 3.0
                        d = math.hypot(x - (c + 8.4 * math.cos(ha)), y - (c + 8.4 * math.sin(ha)))
                        if d < 2.6:
                            v = 0.20
                        elif d < 3.3:
                            v = 0.95 if (y - c) * math.sin(ha) + (x - c) * math.cos(ha) > 8.4 else 0.55
                else:
                    v = 0.92 if r > 1.5 else 0.45
                    for k in range(6):
                        ba = k * math.pi / 3.0 + 0.5
                        if math.hypot(x - (c + 3.0 * math.cos(ba)), y - (c + 3.0 * math.sin(ba))) < 0.8:
                            v = 0.55
            elif kind == 'idler':
                if r > 15.6:
                    v = 0.0
                elif r > 13.0:
                    v = 0.86 - 0.2 * (r > 15.0)
                elif r > 4.0:
                    sp = (a * 5.0 / (2.0 * math.pi)) % 1.0                                   # 5 spokes
                    v = 0.80 if (sp < 0.22 or sp > 0.92) else 0.24
                    if 0.22 <= sp < 0.27:
                        v = 0.95
                else:
                    v = 0.92 if r > 1.4 else 0.5
            elif kind == 'front':
                if r > 15.6:
                    v = 0.0
                elif r > 10.5:
                    v = 0.30 + (0.08 if int(r) % 2 == 0 else 0.0)                          # tyre sidewall ribs
                    if r > 15.0:
                        v = 0.24
                elif r > 9.5:
                    v = 0.92
                else:
                    v = 0.70 + 0.12 * (dy < 0)
                    for k in range(8):
                        ha = k * math.pi / 4.0
                        if math.hypot(x - (c + 6.6 * math.cos(ha)), y - (c + 6.6 * math.sin(ha))) < 1.2:
                            v = 0.3
                    if r < 3.2:
                        v = 0.95 if r > 1.3 else 0.5
            if v is None:
                continue
            img[y, ox + x] = grey(v) if v > 0.0 else grey(0.3)


def wheels():
    img = np.zeros((32, 128, 4), np.uint8)
    for i, k in enumerate(['road', 'sprocket', 'idler', 'front']):
        _wheel(img, i * 32, k)
    Image.fromarray(img, 'RGBA').save(os.path.join(OUT, 'wheels.png'))


# ------------------------------------------------------------------------------------------------ decals
def decals():
    W, H = 128, 64
    img = np.zeros((H, W, 4), np.uint8)

    def put(rx, ry, x, y, col):
        img[ry + y, rx + x] = col

    x0, y0, w, h = DECALS['white']
    img[y0:y0 + h, x0:x0 + w] = grey(1.0)
    # louvre grille (engine air / exhaust outlet): slats with a lit upper edge, deep slots, a frame
    x0, y0, w, h = DECALS['louvre']
    for y in range(h):
        for x in range(w):
            if x in (0, w - 1) or y in (0, h - 1):
                v = 0.62
            elif x in (1, w - 2) or y == 1:
                v = 0.85
            else:
                v = [0.98, 0.72, 0.26][(y - 2) % 3]
            put(x0, y0, x, y, grey(v))
    # tarp roll / canvas: soft folds, two straps
    x0, y0, w, h = DECALS['tarp']
    for y in range(h):
        for x in range(w):
            f = 0.5 + 0.5 * math.sin(x * 0.9 + 1.7 * math.sin(y * 0.55))
            v = 0.66 + 0.30 * f
            if y in (0, h - 1):
                v = 0.55
            if x in (7, 8, 23, 24):
                v = 0.45 if x in (7, 23) else 0.62     # straps
            put(x0, y0, x, y, grey(v))
    # crate planks: 4 boards, dark gaps, nail heads
    x0, y0, w, h = DECALS['planks']
    for y in range(h):
        for x in range(w):
            v = 0.86 - 0.08 * ((x * 7 + (y // 4) * 13) % 5 == 0)
            if y % 4 == 3:
                v = 0.35
            if x in (1, 14) and y % 4 == 1:
                v = 1.0
            put(x0, y0, x, y, grey(v))
    # bolt row (alpha-masked: only the bolt heads draw)
    x0, y0, w, h = DECALS['bolts']
    for x in range(1, w, 4):
        put(x0, y0, x, 1, grey(1.0))
        put(x0, y0, x, 2, grey(0.45))
    # weld bead (alpha-masked): a ragged bright / dark double line
    x0, y0, w, h = DECALS['weld']
    for x in range(w):
        put(x0, y0, x, 1, grey(0.95 if x % 3 else 0.75))
        put(x0, y0, x, 2, grey(0.42))
    # armoured visor with two vision slits and hinge bolts (half-track cab front)
    x0, y0, w, h = DECALS['visor']
    for y in range(h):
        for x in range(w):
            v = 0.82 + 0.08 * (y < 3)
            if x in (0, w - 1) or y == h - 1:
                v = 0.6
            for sx in (4, 18):
                if sx <= x < sx + 10 and y in (7, 8):
                    v = 0.10 if y == 8 else 0.30
                if sx <= x < sx + 10 and y == 9:
                    v = 0.95
            if y == 2 and x % 6 == 3:
                v = 1.0
            put(x0, y0, x, y, grey(v))
    # radiator armour grille: vertical bars, frame, centre post
    x0, y0, w, h = DECALS['radiator']
    for y in range(h):
        for x in range(w):
            if x in (0, w - 1) or y in (0, h - 1):
                v = 0.64
            elif x == w // 2:
                v = 0.80
            else:
                v = [0.95, 0.70, 0.22][x % 3]
                if y == 1:
                    v = 0.55
            put(x0, y0, x, y, grey(v))
    # jerry can (side view): pressed X, rim, handle
    x0, y0, w, h = DECALS['jerry']
    for y in range(h):
        for x in range(w):
            v = 0.80
            if x in (0, w - 1) or y in (0, h - 1):
                v = 0.6
            if y < 3:
                v = 0.9 if 3 <= x <= 8 and y == 1 else (0.0 if y < 2 else v)
            if 3 <= y <= h - 3:
                u = (y - 3) / float(h - 6)
                if abs(x - (1.5 + u * (w - 4))) < 0.8 or abs(x - (w - 2.5 - u * (w - 4))) < 0.8:
                    v = 0.98
            if v > 0.0:
                put(x0, y0, x, y, grey(v))
    # headlight lens (coloured, used with a white vertex colour): cold glass, ring, glint
    x0, y0, w, h = DECALS['lens']
    for y in range(h):
        for x in range(w):
            r = math.hypot(x - 3.5, y - 3.5)
            if r > 3.9:
                col = rgba(B['steel'][1])
            elif r > 3.0:
                col = rgba(B['steel'][3])
            else:
                col = rgba(B['snow'][2] if (x + y) % 2 else B['snow'][1])
                if (x, y) in ((2, 2), (3, 2), (2, 3)):
                    col = rgba(B['snow'][4])
            put(x0, y0, x, y, col)
    # periscope / vision block glass
    x0, y0, w, h = DECALS['glass']
    for y in range(h):
        for x in range(w):
            col = rgba(B['patina'][1] if y > 0 else B['steel'][1])
            if y == 1 and x in (1, 2):
                col = rgba(B['steel'][5])
            put(x0, y0, x, y, col)
    Image.fromarray(img, 'RGBA').save(os.path.join(OUT, 'decals.png'))


def main():
    os.makedirs(OUT, exist_ok=True)
    track()
    wheels()
    decals()
    prev = os.environ.get('VEHICLES_PREVIEW', '')     # optional 6x preview outside the project
    if prev:
        ims = [Image.open(os.path.join(OUT, n)).convert('RGBA') for n in ('track.png', 'wheels.png', 'decals.png')]
        Wd = max(i.width for i in ims)
        Hd = sum(i.height for i in ims) + 8
        bg = Image.new('RGBA', (Wd, Hd), (90, 40, 60, 255))
        y = 0
        for i in ims:
            bg.alpha_composite(i, (0, y))
            y += i.height + 4
        bg.resize((Wd * 6, Hd * 6), Image.NEAREST).save(prev)
    print('vehicles: track.png wheels.png decals.png ->', OUT)


if __name__ == '__main__':
    main()
