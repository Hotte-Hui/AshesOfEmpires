"""env_veltrava_station_thaw -- payoff art of the station side task „Wagen drei ist kalt" (round 8, feel_r8).

    py -3 -P tools/pixelgen/env_veltrava_station_thaw.py              # writes thaw/*.png
    py -3 -P tools/pixelgen/env_veltrava_station_thaw.py --preview=DIR  # + DIR/thaw_preview_8x.png

Car 3 of the Moscow train (layer train_near, pos [0, 157]) has seven compartment windows at layer x 359, 383,
..., 503 (glass 16 x 17 px from layer y 26 = world y 183): two lit and frosted (the checker of a8643a crystals),
four dark with rime at the edges, one lit and clear (the saloon).  When the heating coupling is thawed, the
frost recedes from the top (warm air rises; the sill keeps its rime longest), a lamp goes on in the fourth
compartment (the typists, coats off), and before that somebody wipes a peephole into the frosted sixth window
and waves -- the figure of window_life.png frame 3 (a raised hand) seen through the wiped oval.

Every frame is cut from the layer's own pixels (train_near.png / _n / _e): frame 0 of each strip is identical
to the layer, so the overlay can appear without a seam.  Palette = colours already in the car-3 windows.
Outputs (assets/environments/veltrava_station/thaw/, runtime scripts/levels/veltrava_station/station_thaw.gd):
  car3_thaw.png  (+ _n, _e)   5 frames of the window band (layer x 357..520, y 25..43): 0 = as painted,
                              1..3 = frost receding (peephole kept), 4 = thawed (W4 lit, W5/W6 people inside)
  car3_peephole.png (+ _n, _e) 10 frames of window 6 incl. its frame (layer x 478..495, y 25..43):
                              0 frosted, 1-4 a hand wipes a circle, 5 a face, 6/7 waving, 8 face, 9 hand down
Deterministic (hash-based thaw edge, no randomness).  Provenance: documentation/asset_manifest_parts/feel_r8.md.
"""
from __future__ import annotations

import os
import sys
import zlib

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, '..', '..'))
ENV = os.path.join(ROOT, 'assets', 'environments', 'veltrava_station')
OUT = os.path.join(ENV, 'thaw')

BAND = (357, 25, 521, 44)              # layer px box of the window band (x0, y0, x1, y1)
PEEP = (478, 25, 496, 44)              # window 6 incl. its frame
GLASS_X = [359, 383, 407, 431, 455, 479, 503]
GLASS_Y = 26
GW, GH = 16, 17
LIT_FROSTED = (4, 5)                   # W5, W6
DARK = (0, 2, 3, 6)                    # W1, W3, W4, W7
LIGHT_ON = 3                           # W4: lamp goes on at the end
STAGES = 5

HEX = {'o': 'd08f55', 'd': '6e3f22', 'l': 'edb777', 'L': 'fce2b0', 'm': 'a8643a', 's': '9e9076',
       '.': '1a2431', ',': '121a26', 'F': '2b4541', 'g': '3d5e57', 'i': 'a1aab7', 'j': '7d8796',
       'k': '687789', 'c': 'c2c9d2'}
RGB = {k: tuple(int(v[i:i + 2], 16) for i in (0, 2, 4)) for k, v in HEX.items()}
CODE = {v: k for k, v in RGB.items()}
ICE = set('ijkc')


def load(name):
    return np.asarray(Image.open(os.path.join(ENV, name)).convert('RGBA')).copy()


def glyphs(rgba, x0, y0, w=GW, h=GH):
    """Window glass as a char grid (unknown colours kept as '?<index>' tuples)."""
    g = []
    for y in range(h):
        row = []
        for x in range(w):
            p = tuple(int(c) for c in rgba[y0 + y, x0 + x, :3])
            row.append(CODE.get(p, p))
        g.append(row)
    return g


def h01(x, y, salt):
    return (zlib.crc32(f'{salt}:{x},{y}'.encode()) & 0xFFFF) / 65535.0


# ------------------------------------------------------------------ clear (thawed) art per window
def clear_dark(g):
    """Rime gone: ice pixels become glass, or blind/curtain cloth where cloth surrounds them; the bottom row
    (outer sill) keeps its snow as plain sill; two condensation drops run down the glass."""
    out = [r[:] for r in g]
    for y in range(GH):
        for x in range(GW):
            c = g[y][x]
            if c not in ICE:
                continue
            if y == GH - 1:
                out[y][x] = 's' if c == 'i' else ','
                continue
            nb = [g[y][xx] for xx in (x - 1, x + 1) if 0 <= xx < GW]
            out[y][x] = 's' if nb.count('s') >= 1 and x not in (0, GW - 1) else '.'
    for x, y0 in ((4, 10), (11, 12)):          # drops on the glass (only where glass shows)
        for y in (y0, y0 + 1):
            if out[y][x] == '.':
                out[y][x] = 'F'
    return out


def lit_base(curtains=True):
    g = [['o'] * GW for _ in range(GH)]
    g[0][0] = g[0][GW - 1] = 'm'
    if curtains:
        for y in range(3, GH - 1):
            g[y][1] = g[y][GW - 2] = 'd'
    g[GH - 1] = ['s'] * GW
    return g


def rect(g, x0, y0, x1, y1, c):
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            if 0 <= x < GW and 0 <= y < GH - 1:
                g[y][x] = c


def lamp(g, x0, y0, w=5, h=4):
    rect(g, x0, y0, x0 + w - 1, y0 + h - 1, 'l')
    g[y0 + 1][x0 + 1] = 'L'


def person(g, hx, hy, shoulders=6, coat=False):
    """Back-lit silhouette: 3x3 head, neck, shoulders down to the table."""
    rect(g, hx, hy, hx + 2, hy + 2, 'd')
    g[hy][hx] = g[hy][hx + 2] = 'o'
    g[hy + 3][hx + 1] = 'd'
    rect(g, hx + 1 - shoulders // 2, hy + 4, hx + 1 + (shoulders - 1) // 2, GH - 2, 'd')
    if not coat:                                # coat off: a lighter blouse front catches the lamp
        rect(g, hx + 1, hy + 5, hx + 1, GH - 3, 'm')


def clear_w5():
    g = lit_base()
    lamp(g, 9, 2)
    rect(g, 3, 4, 5, 12, 'm')                  # her coat on the hook, finally off
    g[3][4] = 'd'
    rect(g, 3, 4, 5, 4, 'd')
    person(g, 8, 6)
    return g


def clear_w6():
    g = lit_base()
    lamp(g, 8, 2)
    person(g, 3, 6, shoulders=7)
    rect(g, 3, 14, 13, 14, 'm')                # window table
    rect(g, 10, 11, 11, 13, 'l')               # tea glass (samovar of car 3) ...
    rect(g, 10, 13, 11, 13, 'd')               # ... in its holder
    g[12][12] = 'd'                            # handle
    return g


def lit_w4(g_orig):
    """Lamp on behind the half-drawn blind: glass above glows, the blind turns to lit cloth, a typist's head
    shows above the blind."""
    out = [r[:] for r in clear_dark(g_orig)]
    for y in range(GH - 1):
        for x in range(GW):
            c = out[y][x]
            if c in ('.', 'g', 'F'):
                out[y][x] = 'o'
            elif c == 's':
                out[y][x] = 'm'
            elif c == ',':
                out[y][x] = 'd'
    lamp(out, 10, 1, w=4, h=3)
    rect(out, 4, 5, 6, 7, 'd')                 # head + shoulders above the blind (rail at row 8)
    out[5][4] = out[5][6] = 'o'
    rect(out, 3, 8, 7, 8, 'd')
    out[GH - 1] = ['s'] * GW
    return out


# ------------------------------------------------------------------ peephole sequence (window 6)
CENTER = (8.0, 8.5)
HAND_PATH = [(5.0, 11.0), (4.5, 6.5), (9.5, 4.5), (12.0, 9.0)]   # lower left -> up -> over -> right


def disk(cx, cy, r):
    return {(x, y) for x in range(GW) for y in range(GH - 1) if (x - cx) ** 2 + (y - cy) ** 2 <= r * r}


def hole():
    cx, cy = CENTER
    return {(x, y) for x in range(GW) for y in range(GH - 1) if ((x - cx) / 4.6) ** 2 + ((y - cy) / 4.2) ** 2 <= 1.0}


def blurred_hand(g, cx, cy):
    """A hand behind frosted glass: dark core, mid-tone halo."""
    for (x, y) in disk(cx, cy, 2.3):
        g[y][x] = 'm' if g[y][x] in ('o', 'm') else g[y][x]
    for (x, y) in disk(cx, cy, 1.2):
        g[y][x] = 'd'


def wiped(frost, clear, region):
    g = [r[:] for r in frost]
    for (x, y) in region:
        g[y][x] = clear[y][x]
    return g


def peep_interior():
    """What the wiped oval shows: the compartment, lamp at the top right."""
    g = lit_base()
    lamp(g, 9, 2)
    return g


def face(g, region, dx=0):
    """The man leans to the glass: head + shoulders in the oval (window_life frame 3 body, shifted)."""
    for (x, y) in ((6, 6), (7, 6), (8, 6), (6, 7), (7, 7), (8, 7), (7, 8), (6, 9), (7, 9), (8, 9),
                   (5, 10), (6, 10), (7, 10), (8, 10), (9, 10), (5, 11), (6, 11), (7, 11), (8, 11), (9, 11),
                   (4, 12), (5, 12), (6, 12), (7, 12), (8, 12), (9, 12), (10, 12)):
        x += dx
        if (x, y) in region:
            g[y][x] = 'd'
    g[5][7 + dx] = 'd' if (7 + dx, 5) in region else g[5][7 + dx]


def palm(g, x0, y0):
    """window_life frame 3: the raised palm (9e9076) on its forearm."""
    for (x, y) in ((x0 + 1, y0), (x0, y0 + 1), (x0 + 1, y0 + 1), (x0 + 2, y0 + 1), (x0, y0 + 2),
                   (x0 + 1, y0 + 2), (x0 + 2, y0 + 2), (x0, y0 + 3), (x0 + 1, y0 + 3), (x0 + 2, y0 + 3)):
        if 0 <= x < GW and 0 <= y < GH - 1:
            g[y][x] = 's'
    for y in range(y0 + 4, min(GH - 1, y0 + 8)):
        if 0 <= x0 + 1 < GW:
            g[y][x0 + 1] = 'd'


def peep_frames(frost):
    inner = peep_interior()
    frames = [frost]
    trail = set()
    for i, (hx, hy) in enumerate(HAND_PATH):
        trail |= disk(hx, hy, 2.4)
        if i == len(HAND_PATH) - 1:
            trail |= hole()
        g = wiped(frost, inner, trail)
        blurred_hand(g, hx + 0.8, hy + 0.6)
        frames.append(g)
    H = hole() | trail
    f5 = wiped(frost, inner, H)
    face(f5, H)
    frames.append(f5)
    for px, py in ((11, 3), (12, 2)):           # waving: the palm moves up and to the side
        g = wiped(frost, inner, H | disk(px + 1, py + 2, 2.0))
        face(g, H)
        palm(g, px, py)
        frames.append(g)
    f8 = wiped(frost, inner, H | disk(12, 4, 2.0))
    face(f8, H)
    frames.append(f8)
    f9 = wiped(frost, inner, H | disk(12, 4, 2.0))
    face(f9, H, dx=-1)
    frames.append(f9)
    return frames, H | disk(12, 4, 2.0)


# ------------------------------------------------------------------ stages
def stage(frost, clear, s, keep_clear=frozenset(), salt=0):
    """Frost recedes from the top: a pixel is clear when its threshold is below s (s = 0 .. 1)."""
    g = [r[:] for r in frost]
    for y in range(GH):
        for x in range(GW):
            t = 0.72 * (y / (GH - 1)) + 0.28 * h01(x, y, salt)
            if t < s or (x, y) in keep_clear:
                g[y][x] = clear[y][x]
    return g


def paint(canvas, g, x0, y0):
    for y in range(GH):
        for x in range(GW):
            c = g[y][x]
            rgb = RGB[c] if isinstance(c, str) else c
            canvas[y0 + y, x0 + x, :3] = rgb
            canvas[y0 + y, x0 + x, 3] = 255


def build():
    d = load('train_near.png')
    n = load('train_near_n.png')
    e = load('train_near_e.png')
    x0, y0, x1, y1 = BAND
    bw, bh = x1 - x0, y1 - y0
    frost = [glyphs(d, gx, GLASS_Y) for gx in GLASS_X]
    clear = [clear_dark(frost[i]) if i in DARK else frost[i] for i in range(7)]
    clear[4] = clear_w5()
    clear[5] = clear_w6()
    clear_lit4 = lit_w4(frost[3])
    pf, _peep_region = peep_frames(frost[5])
    mid6 = peep_interior()
    face(mid6, {(x, y) for x in range(GW) for y in range(GH)}, dx=-1)
    # band strip
    band = np.zeros((bh, bw * STAGES, 4), np.uint8)
    band_e = np.zeros_like(band)
    band_n = np.zeros_like(band)
    for f in range(STAGES):
        band[:, f * bw:(f + 1) * bw] = d[y0:y1, x0:x1]
        band_e[:, f * bw:(f + 1) * bw] = e[y0:y1, x0:x1]
        band_n[:, f * bw:(f + 1) * bw] = n[y0:y1, x0:x1]
        if f == 0:
            continue
        s = f / (STAGES - 1)
        for i, gx in enumerate(GLASS_X):
            if i == 1:
                continue                                      # the saloon window was never frosted
            if i == 5:
                # the man stays at his peephole while the rest of the glass clears; at the end he sits back
                g = stage(pf[-1], mid6, s, salt=i) if f < STAGES - 1 else clear[5]
            elif i == LIGHT_ON and f == STAGES - 1:
                g = clear_lit4
            else:
                g = stage(frost[i], clear[i], s, salt=i) if f < STAGES - 1 else clear[i]
            lx = f * bw + gx - x0
            ly = GLASS_Y - y0
            paint(band, g, lx, ly)
            lit = i in LIT_FROSTED or (i == LIGHT_ON and f == STAGES - 1)
            band_e[ly:ly + GH, lx:lx + GW] = 0
            if lit:
                sub = e[y0:y1, x0:x1]
                for yy in range(GH):
                    for xx in range(GW):
                        c = g[yy][xx]
                        rgb = RGB[c] if isinstance(c, str) else c
                        if yy == GH - 1:
                            o = sub[ly + yy, gx - x0 + xx]
                            band_e[ly + yy, lx + xx] = o if o[3] else (208, 143, 85, 255)
                        else:
                            band_e[ly + yy, lx + xx] = (*rgb, 255)
    # peephole strip
    px0, py0, px1, py1 = PEEP
    pw, ph = px1 - px0, py1 - py0
    peep = np.zeros((ph, pw * len(pf), 4), np.uint8)
    peep_e = np.zeros_like(peep)
    peep_n = np.zeros_like(peep)
    for f, g in enumerate(pf):
        peep[:, f * pw:(f + 1) * pw] = d[py0:py1, px0:px1]
        peep_e[:, f * pw:(f + 1) * pw] = e[py0:py1, px0:px1]
        peep_n[:, f * pw:(f + 1) * pw] = n[py0:py1, px0:px1]
        lx, ly = f * pw + GLASS_X[5] - px0, GLASS_Y - py0
        paint(peep, g, lx, ly)
        sub = e[py0:py1, px0:px1]
        for yy in range(GH):
            for xx in range(GW):
                c = g[yy][xx]
                rgb = RGB[c] if isinstance(c, str) else c
                if yy == GH - 1:
                    o = sub[ly + yy, GLASS_X[5] - px0 + xx]
                    peep_e[ly + yy, lx + xx] = o if o[3] else (208, 143, 85, 255)
                else:
                    peep_e[ly + yy, lx + xx] = (*rgb, 255)
    # frame 0 of both strips must be the layer itself (seamless appearance)
    assert np.array_equal(band[:, :bw], d[y0:y1, x0:x1])
    assert np.array_equal(peep[:, :pw, :3], d[py0:py1, px0:px1, :3])
    return {'car3_thaw': (band, band_n, band_e), 'car3_peephole': (peep, peep_n, peep_e)}


def save(arts):
    os.makedirs(OUT, exist_ok=True)
    for name, (a, nm, em) in arts.items():
        Image.fromarray(a, 'RGBA').save(os.path.join(OUT, name + '.png'))
        Image.fromarray(nm, 'RGBA').save(os.path.join(OUT, name + '_n.png'))
        Image.fromarray(em, 'RGBA').save(os.path.join(OUT, name + '_e.png'))
        print('env_veltrava_station_thaw:', name, a.shape[1], 'x', a.shape[0])


def preview(arts, path):
    band = arts['car3_thaw'][0]
    peep = arts['car3_peephole'][0]
    bw = band.shape[1] // STAGES
    rows = [band[:, f * bw:(f + 1) * bw] for f in range(STAGES)]
    k = 6
    W = max(bw, peep.shape[1]) * k
    H = (len(rows) * (band.shape[0] + 2) + peep.shape[0]) * k
    img = Image.new('RGBA', (W, H), (30, 30, 34, 255))
    y = 0
    for r in rows:
        im = Image.fromarray(r, 'RGBA').resize((r.shape[1] * k, r.shape[0] * k), Image.NEAREST)
        img.alpha_composite(im, (0, y))
        y += (band.shape[0] + 2) * k
    im = Image.fromarray(peep, 'RGBA').resize((peep.shape[1] * k, peep.shape[0] * k), Image.NEAREST)
    img.alpha_composite(im, (0, y))
    img.save(path)


def main(argv):
    arts = build()
    save(arts)
    prev = next((a.split('=', 1)[1] for a in argv if a.startswith('--preview=')), '')
    if prev:
        os.makedirs(prev, exist_ok=True)
        preview(arts, os.path.join(prev, 'thaw_preview_6x.png'))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
