"""gen_parade -- sprites and mattes for L_M1_Parade (the regime's parade before the Great Hall).
Owner: parade.  Original, deterministic, berlin palette only (pg.PALETTES['berlin']).
Outputs (assets/architecture/parade/):
  figures.png + figures.json  LOD atlas of the parade figures.  13 LOD strips (figure heights 2..104 px); every
                              strip holds the same 18 slots side by side: marching soldier in profile (4 frames),
                              soldier at attention (front), guard (front, gorget + white belt), 6 civilians seen
                              from behind (hunched, still), a child with a limp little flag, 2 grey officials
                              (front, featureless faces under the cap), 3 dust/snow puff frames.  Faces of the
                              troops are always a shadow band under the helmet: anonymous ranks, no individuals.
                              parade_figures.gdshader picks the strip whose height matches the projected size.
  flag_limp.png / flag_limp_hist.png   the child's limp hand flag (neutral cloth / historical variant, §12.4)
  sky_parade.png, fog_parade.png       cold overcast dusk matte + cold fog gradient (same mapping as the hall's)
Run: py -3 -P tools/pixelgen/gen_parade.py
"""
from __future__ import annotations
import json
import math
import os
import sys

import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pg  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
OUT = os.path.join(ROOT, 'assets', 'architecture', 'parade')
B = pg.PALETTES['berlin']
LODS = [2, 3, 4, 6, 8, 11, 15, 21, 29, 40, 54, 76, 104]
SS = 8
OUTLINE = B['night'][0]


def c(r, i):
    return B[r][i]


# ------------------------------------------------------------------------------------------- figures
# Shapes in figure units: x right, y up, feet centre at (0, 0), full adult height 1.0.
def _leg(hip, knee, foot, w, col, boot):
    return [('line', col, (hip[0], hip[1], knee[0], knee[1], w)),
            ('line', col, (knee[0], knee[1], foot[0], foot[1] + 0.05, w * 0.92)),
            ('poly', boot, [(foot[0] - w * 0.55, foot[1]), (foot[0] - w * 0.55, foot[1] + 0.1),
                            (foot[0] + w * 0.5, foot[1] + 0.1), (foot[0] + w * 0.95, foot[1])])]


def soldier_side(f):
    coat, dark, lit = c('steel', 2), c('steel', 1), c('steel', 3)
    boot, belt, face = c('night', 1), c('night', 2), c('night', 3)
    hip = (0.0, 0.46)
    # stiff parade step: legs spread / passing, near leg alternates with the far (darker) leg
    feet = [((0.15, 0.0), (-0.13, 0.0)), ((0.03, 0.05), (-0.02, 0.0)),
            ((-0.13, 0.0), (0.15, 0.0)), ((-0.02, 0.0), (0.03, 0.05))][f]
    sh = []
    far, near = (feet[1], feet[0]) if f in (0, 1) else (feet[0], feet[1])
    for foot, col in ((far, dark), (near, coat)):
        knee = ((hip[0] + foot[0]) * 0.5 + 0.02, (hip[1] + foot[1]) * 0.5 + 0.01)
        sh += _leg(hip, knee, foot, 0.075, col, boot)
    # rifle shouldered on the far side (drawn behind the body)
    sh.append(('line', c('ochre', 0), (0.06, 0.6, -0.08, 0.92, 0.035)))
    sh.append(('line', c('steel', 0), (-0.08, 0.92, -0.115, 1.0, 0.02)))
    sh.append(('poly', coat, [(-0.09, 0.80), (0.07, 0.80), (0.1, 0.62), (0.12, 0.42), (0.13, 0.36),
                              (-0.12, 0.36), (-0.1, 0.6)]))
    sh.append(('poly', dark, [(-0.09, 0.80), (-0.03, 0.80), (-0.05, 0.6), (-0.06, 0.36), (-0.12, 0.36),
                              (-0.1, 0.6)]))
    sh.append(('poly', belt, [(-0.105, 0.545), (0.11, 0.545), (0.112, 0.575), (-0.1, 0.575)]))
    hand = [(-0.09, 0.53), (0.0, 0.5), (0.1, 0.54), (0.0, 0.5)][f]
    sh.append(('line', lit, (0.0, 0.77, hand[0], hand[1] + 0.03, 0.06)))
    sh.append(('ell', c('night', 3), (hand[0], hand[1], 0.025, 0.025)))
    sh.append(('poly', face, [(-0.02, 0.8), (0.06, 0.8), (0.07, 0.9), (-0.02, 0.9)]))
    sh.append(('ell', dark, (-0.01, 0.925, 0.078, 0.07)))
    sh.append(('poly', dark, [(-0.08, 0.93), (-0.12, 0.855), (-0.05, 0.87)]))
    sh.append(('poly', dark, [(0.04, 0.88), (0.09, 0.872), (0.085, 0.895), (0.05, 0.9)]))
    sh.append(('ell', lit, (-0.025, 0.955, 0.035, 0.022)))
    return sh


def soldier_front(guard=False):
    coat, dark, lit = c('steel', 2), c('steel', 1), c('steel', 3)
    boot, belt = c('night', 1), (c('snow', 1) if guard else c('night', 2))
    sh = [('poly', dark, [(-0.065, 0.0), (-0.012, 0.0), (-0.012, 0.4), (-0.065, 0.4)]),
          ('poly', dark, [(0.012, 0.0), (0.065, 0.0), (0.065, 0.4), (0.012, 0.4)]),
          ('poly', boot, [(-0.07, 0.0), (-0.01, 0.0), (-0.01, 0.1), (-0.068, 0.1)]),
          ('poly', boot, [(0.01, 0.0), (0.07, 0.0), (0.068, 0.1), (0.01, 0.1)]),
          ('line', c('ochre', 0), (0.19, 0.04, 0.19, 0.6, 0.04)),
          ('line', c('steel', 0), (0.19, 0.6, 0.19, 0.8, 0.022)),
          ('poly', coat, [(-0.125, 0.79), (0.125, 0.79), (0.14, 0.62), (0.15, 0.36), (-0.15, 0.36),
                          (-0.14, 0.62)]),
          ('poly', dark, [(0.06, 0.79), (0.125, 0.79), (0.14, 0.62), (0.15, 0.36), (0.07, 0.36)]),
          ('poly', lit, [(-0.17, 0.48), (-0.125, 0.48), (-0.125, 0.78), (-0.165, 0.76)]),
          ('poly', dark, [(0.125, 0.48), (0.17, 0.48), (0.165, 0.76), (0.125, 0.78)]),
          ('poly', belt, [(-0.145, 0.545), (0.145, 0.545), (0.145, 0.58), (-0.145, 0.58)]),
          ('poly', c('night', 2), [(-0.05, 0.79), (0.05, 0.79), (0.045, 0.83), (-0.045, 0.83)]),
          ('poly', c('night', 3), [(-0.045, 0.83), (0.045, 0.83), (0.045, 0.9), (-0.045, 0.9)]),
          ('ell', dark, (0.0, 0.93, 0.085, 0.07)),
          ('poly', dark, [(-0.105, 0.86), (0.105, 0.86), (0.1, 0.89), (-0.1, 0.89)]),
          ('ell', lit, (-0.03, 0.96, 0.035, 0.02))]
    if guard:
        sh.append(('ell', c('snow', 2), (0.0, 0.725, 0.045, 0.018)))
    return sh


CIVIL = [  # coat, shadow, head kind, head colour, height, hunch
    (c('violet', 2), c('violet', 1), 'fedora', c('night', 2), 0.97, 0.0),
    (c('ochre', 1), c('ochre', 0), 'scarf', c('stone', 2), 0.91, 0.02),
    (c('steel', 1), c('steel', 0), 'cap', c('night', 3), 0.95, 0.01),
    (c('violet', 3), c('violet', 2), 'hat', c('night', 2), 0.9, 0.0),
    (c('stone', 1), c('stone', 0), 'cap', c('night', 2), 0.86, 0.05),
    (c('night', 3), c('night', 2), 'hair', c('night', 1), 0.98, 0.01),
]


def civilian_back(v):
    coat, dark, head, hcol, h, hunch = CIVIL[v]
    leg = c('night', 1)
    sh = [('poly', leg, [(-0.06, 0.0), (-0.015, 0.0), (-0.015, 0.32 * h), (-0.06, 0.32 * h)]),
          ('poly', leg, [(0.015, 0.0), (0.06, 0.0), (0.06, 0.32 * h), (0.015, 0.32 * h)])]
    top = 0.79 * h - hunch
    hem = (0.27 if head in ('scarf', 'hat') else 0.33) * h
    sh.append(('poly', coat, [(-0.115, top), (0.115, top), (0.15, top - 0.12), (0.15, hem), (-0.15, hem),
                              (-0.15, top - 0.12)]))
    sh.append(('poly', dark, [(0.04, top), (0.115, top), (0.15, top - 0.12), (0.15, hem), (0.05, hem)]))
    hy = top + 0.085 + hunch * 0.6
    sh.append(('ell', c('night', 2) if head != 'scarf' else hcol, (0.0, hy, 0.06, 0.075)))
    if head == 'fedora':
        sh += [('ell', hcol, (0.0, hy + 0.04, 0.1, 0.02)), ('poly', hcol, [(-0.055, hy + 0.04), (0.055, hy + 0.04),
                                                                          (0.05, hy + 0.1), (-0.05, hy + 0.1)])]
    elif head == 'scarf':
        sh += [('poly', c('stone', 1), [(-0.02, hy - 0.07), (0.02, hy - 0.07), (0.03, hy - 0.11),
                                        (-0.01, hy - 0.11)])]
    elif head == 'cap':
        sh += [('ell', hcol, (0.0, hy + 0.04, 0.07, 0.035))]
    elif head == 'hat':
        sh += [('ell', hcol, (0.0, hy + 0.045, 0.065, 0.04))]
    else:
        sh += [('ell', hcol, (0.0, hy + 0.02, 0.06, 0.06))]
    return sh


def child_flag():
    h = 0.58
    sh = [('poly', c('night', 1), [(-0.04, 0.0), (-0.008, 0.0), (-0.008, 0.2), (-0.04, 0.2)]),
          ('poly', c('night', 1), [(0.008, 0.0), (0.04, 0.0), (0.04, 0.2), (0.008, 0.2)]),
          ('poly', c('ochre', 2), [(-0.075, 0.46), (0.075, 0.46), (0.095, 0.2), (-0.095, 0.2)]),
          ('poly', c('ochre', 1), [(0.02, 0.46), (0.075, 0.46), (0.095, 0.2), (0.03, 0.2)]),
          ('line', c('ochre', 1), (0.07, 0.44, 0.13, 0.36, 0.035)),
          ('line', c('ochre', 0), (0.13, 0.34, 0.15, 0.64, 0.012)),
          ('poly', c('ochre', 3), [(0.15, 0.64), (0.19, 0.63), (0.185, 0.53), (0.165, 0.5), (0.155, 0.52)]),
          ('poly', c('ochre', 2), [(0.165, 0.6), (0.185, 0.6), (0.18, 0.53), (0.165, 0.51)]),
          ('ell', c('night', 2), (0.0, 0.52, 0.05, 0.06)),
          ('ell', c('steel', 1), (0.0, 0.56, 0.055, 0.035))]
    for s in sh:
        if s[1] is None:
            raise ValueError
    return sh if h else sh


def official_front(v):
    coat, dark = (c('steel', 4), c('steel', 3)) if v == 0 else (c('night', 3), c('violet', 1))
    cap = c('steel', 1) if v == 0 else c('steel', 3)
    return [('poly', c('night', 1), [(-0.06, 0.0), (-0.012, 0.0), (-0.012, 0.25), (-0.06, 0.25)]),
            ('poly', c('night', 1), [(0.012, 0.0), (0.06, 0.0), (0.06, 0.25), (0.012, 0.25)]),
            ('poly', coat, [(-0.125, 0.8), (0.125, 0.8), (0.14, 0.62), (0.16, 0.2), (-0.16, 0.2), (-0.14, 0.62)]),
            ('poly', dark, [(0.05, 0.8), (0.125, 0.8), (0.14, 0.62), (0.16, 0.2), (0.06, 0.2)]),
            ('poly', dark, [(-0.01, 0.8), (0.01, 0.8), (0.01, 0.2), (-0.01, 0.2)]),
            ('poly', c('night', 2), [(-0.05, 0.8), (0.05, 0.8), (0.04, 0.84), (-0.04, 0.84)]),
            ('poly', c('stone', 2), [(-0.042, 0.84), (0.042, 0.84), (0.042, 0.905), (-0.042, 0.905)]),
            ('poly', c('night', 3), [(-0.045, 0.885), (0.045, 0.885), (0.045, 0.91), (-0.045, 0.91)]),
            ('poly', c('night', 1), [(-0.07, 0.905), (0.07, 0.905), (0.06, 0.93), (-0.06, 0.93)]),
            ('ell', cap, (0.0, 0.955, 0.085, 0.032))]


def puff(k):
    r = [0.16, 0.24, 0.3][k]
    return [('ell', c('snow', 2), (0.0, r * 0.9, r, r * 0.85)),
            ('ell', c('snow', 3), (-r * 0.3, r * 1.15, r * 0.65, r * 0.55)),
            ('ell', c('snow', 1), (r * 0.35, r * 0.5, r * 0.55, r * 0.4))]


SLOTS = ([('march', soldier_side(f)) for f in range(4)] + [('stand', soldier_front())]
         + [('guard', soldier_front(True))] + [('crowd', civilian_back(v)) for v in range(6)]
         + [('child_flag', child_flag())] + [('official', official_front(v)) for v in range(2)]
         + [('puff', puff(k)) for k in range(3)])


def cell_size(h):
    return max(3, int(round(0.7 * h)) + 3), h + 2


def _draw(sh, cw, ch, h, ss, labels):
    im = Image.new('L', (cw * ss, ch * ss), 0)
    dr = ImageDraw.Draw(im)
    ax, ay = cw // 2, h + 1

    def P(x, y):
        return ((ax + x * h) * ss, (ay - y * h) * ss)
    for kind, col, prm in sh:
        lab = labels.setdefault(col, len(labels) + 1)
        if kind == 'poly':
            dr.polygon([P(x, y) for x, y in prm], fill=lab)
        elif kind == 'ell':
            cx, cy, rx, ry = prm
            x0, y0 = P(cx - rx, cy + ry)
            x1, y1 = P(cx + rx, cy - ry)
            dr.ellipse([x0, y0, x1, y1], fill=lab)
        else:
            x0, y0, x1, y1, w = prm
            dx, dy = x1 - x0, y1 - y0
            ln = math.hypot(dx, dy) or 1.0
            nx, ny = -dy / ln * w * 0.5, dx / ln * w * 0.5
            dr.polygon([P(x0 + nx, y0 + ny), P(x1 + nx, y1 + ny), P(x1 - nx, y1 - ny), P(x0 - nx, y0 - ny)],
                       fill=lab)
    return np.asarray(im)


def render(sh, h, puff_slot=False):
    cw, ch = cell_size(h)
    labels: dict = {}
    out = np.zeros((ch, cw, 4), np.uint8)
    inv = {}
    if h <= 4:
        # tiny figures: one (puffs: two) pixel column, colours sampled from a 40 px reference render
        ref_h = 40
        rcw, rch = cell_size(ref_h)
        ref = _draw(sh, rcw, rch, ref_h, 1, labels)
        inv = {v: k for k, v in labels.items()}
        ax = cw // 2
        cols = [ax - 1, ax] if puff_slot else [ax]
        for r in range(h):
            y = (h - r - 0.5) / h
            ry = int((ref_h + 1) - y * ref_h)
            lab = int(ref[min(max(ry, 0), rch - 1), rcw // 2])
            if lab:
                for cx in cols:
                    out[1 + r, cx, :3] = pg.hx(inv[lab])[:3]
                    out[1 + r, cx, 3] = 255
        return out
    big = _draw(sh, cw, ch, h, SS, labels)
    inv = {v: k for k, v in labels.items()}
    blk = big.reshape(ch, SS, cw, SS).transpose(0, 2, 1, 3).reshape(ch, cw, SS * SS)
    cov = (blk > 0).mean(-1)
    n = len(labels) + 1
    counts = np.stack([(blk == i).sum(-1) for i in range(1, n)], -1)
    lab = counts.argmax(-1) + 1
    solid = cov >= (0.42 if h >= 8 else 0.3)
    for i in range(1, n):
        m = solid & (lab == i)
        out[m, :3] = pg.hx(inv[i])[:3]
        out[m, 3] = 255
    if h >= 11 and not puff_slot:
        a = out[:, :, 3] > 0
        nb = np.zeros_like(a)
        nb[1:, :] |= a[:-1, :]
        nb[:-1, :] |= a[1:, :]
        nb[:, 1:] |= a[:, :-1]
        nb[:, :-1] |= a[:, 1:]
        edge = nb & ~a
        out[edge, :3] = pg.hx(OUTLINE)[:3]
        out[edge, 3] = 255
    if puff_slot and h >= 6:
        # thin dissolving edge: drop every other pixel on the rim (ordered pattern)
        a = out[:, :, 3] > 0
        inner = a.copy()
        inner[1:, :] &= a[:-1, :]
        inner[:-1, :] &= a[1:, :]
        inner[:, 1:] &= a[:, :-1]
        inner[:, :-1] &= a[:, 1:]
        rim = a & ~inner
        yy, xx = np.mgrid[0:ch, 0:cw]
        out[rim & (((xx + yy) % 2) == 0), 3] = 0
    return out


def build_atlas():
    strips = []
    width = 0
    for h in LODS:
        cw, ch = cell_size(h)
        strip = np.zeros((ch, cw * len(SLOTS), 4), np.uint8)
        for i, (kind, sh) in enumerate(SLOTS):
            strip[:, i * cw:(i + 1) * cw] = render(sh, h, kind == 'puff')
        strips.append(strip)
        width = max(width, strip.shape[1])
    height = sum(s.shape[0] for s in strips)
    atlas = np.zeros((height, width, 4), np.uint8)
    lods = []
    y = 0
    for h, s in zip(LODS, strips):
        atlas[y:y + s.shape[0], :s.shape[1]] = s
        cw, ch = cell_size(h)
        lods.append([y, cw, ch, h])
        y += s.shape[0]
    Image.fromarray(atlas, 'RGBA').save(os.path.join(OUT, 'figures.png'))
    names = [k for k, _ in SLOTS]
    slots = {}
    for i, k in enumerate(names):
        if k not in slots:
            slots[k] = [i, names.count(k)]
    meta = {'atlas': [width, height], 'lods': lods, 'slots': slots, 'height_m': 1.8,
            'anchor': 'x = floor(cell_w / 2), y = fig_h + 1 (feet bottom boundary)',
            'generator': 'tools/pixelgen/gen_parade.py'}
    with open(os.path.join(OUT, 'figures.json'), 'w', encoding='utf-8') as f:
        json.dump(meta, f, indent=1)
    return atlas, meta


# ------------------------------------------------------------------------------------------- hand flag
def limp_flag(hist):
    w, h = 9, 19
    a = np.zeros((h, w, 4), np.uint8)

    def px(x, y, col):
        a[y, x, :3] = pg.hx(col)[:3]
        a[y, x, 3] = 255
    for y in range(2, h):
        px(1, y, c('ochre', 0))
    cloth = [c('ochre', 3), c('ochre', 2)] if hist else [c('steel', 3), c('steel', 2)]
    for y in range(2, 12):
        for x in range(2, 2 + max(1, 5 - (y - 2) // 3)):
            px(x, y, cloth[(x + y // 4) % 2] if y < 10 else cloth[1])
    if hist:   # a fold of the white disc shows, the emblem itself is crumpled out of sight
        px(3, 5, c('snow', 3))
        px(3, 6, c('snow', 2))
        px(2, 6, c('night', 2))
    px(1, 1, c('steel', 4))
    Image.fromarray(a, 'RGBA').save(os.path.join(OUT, 'flag_limp%s.png' % ('_hist' if hist else '')))


# ------------------------------------------------------------------------------------------- mattes
def sky_and_fog():
    W, H = 1024, 720
    AX, AY = 512, 430
    yy = np.arange(H, dtype=np.float32)[:, None] * np.ones((1, W), np.float32)
    xx = np.ones((H, 1), np.float32) * np.arange(W, dtype=np.float32)[None, :]
    k = np.clip((yy - 40.0) / (AY - 40.0), 0.0, 1.0)            # 0 zenith .. 1 horizon
    ramp = [pg.hx(x)[:3].astype(np.float32) for x in ['#120C14', '#1B1520', '#211623', '#2A2130', '#342F37',
                                                       '#443B43', '#454E58', '#5F6973', '#6E6A73']]
    pos = np.clip(k ** 1.6 * (len(ramp) - 1), 0, len(ramp) - 1.001)
    i0 = pos.astype(int)
    f = (pos - i0)[..., None]
    R = np.stack(ramp)
    rgb = R[i0] * (1 - f) + R[i0 + 1] * f
    # low overcast deck: dark bellies, edges catching the cold city glow from below
    n = pg.value_noise(W, H, 90.0, seed=1964, octaves=5)
    n2 = pg.value_noise(W, H, 28.0, seed=77, octaves=3)
    band = np.clip(1.0 - np.abs(yy - 300.0) / 170.0, 0.0, 1.0)
    cloud = np.clip((n * 0.8 + n2 * 0.3 - 0.52) * 3.2, 0.0, 1.0) * band
    belly = pg.hx('#2A2130')[:3].astype(np.float32)
    rgb = rgb * (1 - cloud[..., None] * 0.75) + belly * cloud[..., None] * 0.75
    lit = np.clip((n2 - 0.55) * 4.0, 0, 1) * cloud * np.clip((yy - 260.0) / 140.0, 0, 1)
    rgb = rgb * (1 - lit[..., None] * 0.5) + pg.hx('#5F6973')[:3].astype(np.float32) * lit[..., None] * 0.5
    # faint cold glow of the floodlit plaza on the horizon, centred under the dome
    glow = np.exp(-((xx - AX) / 330.0) ** 2) * np.exp(-((yy - AY) / 46.0) ** 2)
    rgb = rgb * (1 - glow[..., None] * 0.45) + pg.hx('#8F8A92')[:3].astype(np.float32) * glow[..., None] * 0.45
    below = yy > AY
    rgb[below] = pg.hx('#443B43')[:3]
    cols = ['#120C14', '#1B1520', '#211623', '#2A2130', '#25202B', '#342F37', '#443B43', '#57494D', '#454E58',
            '#5F6973', '#6E6A73', '#8F8A92']
    q = pg.quantize_rgb(rgb, [pg.hx(x) for x in cols], dither=True).astype(np.uint8)
    img = np.concatenate([q, np.full((H, W, 1), 255, np.uint8)], -1)
    Image.fromarray(img, 'RGBA').save(os.path.join(OUT, 'sky_parade.png'))
    # fog: cold violet-grey, slightly lighter towards the horizon glow
    fk = np.clip((yy - 200.0) / (AY - 200.0), 0.0, 1.0)
    fcol = (pg.hx('#342F37')[:3] * (1 - fk[..., None]) + pg.hx('#57494D')[:3] * fk[..., None]).astype(np.float32)
    fcol = fcol * (1 - glow[..., None] * 0.5) + pg.hx('#6E6A73')[:3].astype(np.float32) * glow[..., None] * 0.5
    fcol[below] = pg.hx('#57494D')[:3]
    q = pg.quantize_rgb(fcol, [pg.hx(x) for x in ['#342F37', '#443B43', '#57494D', '#6E6A73']],
                        dither=True).astype(np.uint8)
    img = np.concatenate([q, np.full((H, W, 1), 255, np.uint8)], -1)
    Image.fromarray(img, 'RGBA').save(os.path.join(OUT, 'fog_parade.png'))


def main():
    os.makedirs(OUT, exist_ok=True)
    atlas, meta = build_atlas()
    limp_flag(False)
    limp_flag(True)
    sky_and_fog()
    prev = os.environ.get('PARADE_PREVIEW', '')       # optional 2x preview outside the project
    if prev:
        big = Image.fromarray(atlas, 'RGBA')
        bg = Image.new('RGBA', big.size, (60, 70, 80, 255))
        bg.alpha_composite(big)
        bg.resize((big.size[0] * 2, big.size[1] * 2), Image.NEAREST).save(prev)
    print('figures', meta['atlas'], 'slots', meta['slots'])


if __name__ == '__main__':
    main()
