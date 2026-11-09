"""pixel_fire -- the pixel fire kit: flames, smoke, sparks and fire light authored on the game's pixel grid.

Everything here is drawn at 1 texel = 1 px of the 640x360 world with HARD pixels: alpha is 0 or 255, no blur, no
gradients; soft transitions are ordered dither.  Deterministic (fixed seeds, no time, no global random state).

  flames   designed tongues, not noise: every tongue rises, leans into a travelling sway (the lick), pinches at
           the neck and lets its tip go as a flamelet that climbs on and cools; neighbouring tongues share one
           hot core (the colour bands are merged over all tongues of a sheet), forks split the tips.  Seamless
           loops of 8-12 frames: every tongue runs a whole number of cycles per loop.
  smoke    chunky cauliflower puffs (pixel discs, three tones, 2x2 checker between the tones) that swell and
           break up through an ordered dither; a tileable rolling bank for ceilings (and its veil).
  sparks   single pixels on arcs, cooling down the spark ramp (white -> yellow -> orange -> red -> gone).
  light    pools of flat additive bands, dithered into each other and into nothing; a few frames that breathe.

Colours: FIRE (5, rim .. white-hot core) + COOL from the scenes' fire ramp, three smoke tones per variant.
Runtime: scripts/render/pixel_fire.gd plays the sheets pixel-snapped (integer positions, no scaling, phase and
mirror per instance); the sheet table is assets/fx/pixel_fire/kit.json.

    py -3 -P tools/pixelgen/pixel_fire.py [--preview FILE.png]

Other generators import this module for sheets in their own palette or size (see env_c3p2_cine_fire.build_fx).
Level strips of any cell size and loop length are baked from the same parts by pixel_fire_bake.py.
"""
from __future__ import annotations

import json
import math
import os
import sys

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
OUT = os.path.join(ROOT, 'assets', 'fx', 'pixel_fire')
TICK = 10                                                         # frames per second of the flame sheets

FIRE = ('#A8381A', '#D8662A', '#F2A044', '#FCE0A0', '#FFF6DC')    # rim .. white-hot core
COOL = '#6E1E0C'                                                  # a flamelet about to go out, a cooling spark
SPARK = ('#FFF6DC', '#FCE0A0', '#F2A044', '#D8662A', '#A8381A', '#6E1E0C')
SMOKE_WARM = ('#1A1412', '#4C3020', '#844E2A')                    # dark / body / lit by the fire below
SMOKE_GREY = ('#14161A', '#2B2E33', '#4C4C4E')                    # away from the fire, in the night
LIGHT = ((22, 10, 4), (44, 20, 8), (70, 33, 13))                  # additive bands of a light pool, rim .. centre
BAYER4 = np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]], np.float32)
HF = (1.0, 0.88, 0.72, 0.52, 0.30)                                # height of each colour band's tongue
IN = (0.0, 0.16, 0.34, 0.54, 0.76)                                # .. and how far it stands in (share of w)


def rgb(h):
    return (int(h[1:3], 16), int(h[3:5], 16), int(h[5:7], 16))


def bayer(h, w, ox=0, oy=0):
    """ordered-dither thresholds in (0, 1), one cell per pixel"""
    ys = (np.arange(h) + oy) % 4
    xs = (np.arange(w) + ox) % 4
    return (BAYER4[ys[:, None], xs[None, :]] + 0.5) / 16.0


def sheet(frames):
    return np.concatenate(frames, axis=1)


# ------------------------------------------------------------------------------------------------ flames
def _shape(q, fat=0.0):
    """half width of a tongue at q = distance from its tip / taper length: a lick over a belly; fat = the
    share of a fuller, convex outline (tongues of a wall of fire)"""
    q = np.clip(q, 0.0, 1.0)
    return (1.0 - fat) * (0.55 * q + 0.45 * q * q * (3.0 - 2.0 * q)) + fat * q ** 0.62


def _cycle(u, rest):
    """one tongue cycle at phase u: (height share, None) while it rises, (.., v) while its tip leaves (v 0..1)"""
    g0 = 0.62
    if u < g0:
        g = u / g0
        return rest + (1.0 - rest) * g * g * (3.0 - 2.0 * g), None
    v = (u - g0) / (1.0 - g0)
    return 1.0 - (1.0 - rest) * v ** 1.5, v


def _span(m, y, x0, x1, wrap):
    fh, fw = m.shape
    if y < 0 or y >= fh or x1 <= x0:
        return
    if wrap:
        for x in range(x0, x1):
            m[y, x % fw] = True
    else:
        m[y, max(0, x0):min(fw, x1)] = True


def tongue(x, w, h, ph=0.0, m=1, lean=0.0, sway=None, lam=None, **kw):
    """One tongue: base centre x, half width w, full height h (px); ph = phase (0..1), m = cycles per loop;
    lean = how far the tip stands off the base; sway/lam = amplitude and wavelength of the travelling lick;
    rest = its height at the low point (share of h); foot = width at the very base (share of w, 1 = a wall);
    fat = fuller outline (0..1); det = the tip leaves as a flamelet; ps = phase of the sway; k = sway cycles
    per loop."""
    d = dict(x=float(x), w=float(w), h=float(h), ph=float(ph), m=int(m), lean=float(lean),
             sway=0.22 * w + 0.4 if sway is None else float(sway), lam=0.62 * h if lam is None else float(lam))
    d.update(kw)
    return d


def _tongue(M, cool, T, f, n, inset, wrap):
    nb, fh, fw = M.shape
    h, w, x = T['h'], T['w'], T['x']
    share, v = _cycle((f / n * T['m'] + T['ph']) % 1.0, T.get('rest', 0.62))
    lean, sway, lam = T['lean'], T['sway'], T['lam']
    ps, kw, foot, fat = T.get('ps', T['ph'] * 0.37), T.get('k', 1), T.get('foot', 1.0), T.get('fat', 0.0)

    def centre(r):
        r = np.asarray(r, np.float32)
        return (x + lean * (r / h) ** 1.4
                + sway * np.minimum(1.0, r / (0.45 * h)) * np.sin(2 * math.pi * (r / lam - kw * f / n + ps)))

    hn = h * share
    for j in range(nb):
        hj, wj = hn * HF[j], w - max(j * inset, IN[j] * w)        # broad tongues get broad colour bands
        if wj < 0.75 or hj < 1.0:
            break
        r = np.arange(int(math.ceil(hj)))
        ft = foot + (1.0 - foot) * np.minimum(1.0, r / max(1.0, 0.22 * h))
        wd = np.maximum(1, np.rint(2 * wj * ft * _shape((hj - r - 0.5) / (h * 0.8 * HF[j]), fat))).astype(int)
        if wj >= 3.0:                                               # a chunky tip: one pixel only at the very end
            wd = np.maximum(wd, np.where(hj - r > 2.5, 2, 1))
        lf = np.rint(centre(r) - wd / 2.0).astype(int)
        for i in range(len(r)):
            _span(M[j], fh - 1 - int(r[i]), int(lf[i]), int(lf[i] + wd[i]), wrap)
    if v is None or not T.get('det', True) or v > 0.82:
        return
    # the flamelet: the tip thickens over a neck, comes free, climbs on, thins out and cools
    rb, rt = h * (0.80 + 0.40 * v), h * (1.0 + 0.30 * v)
    wt = max(1.2, w * 0.34) * (1.0 - 0.6 * v)
    r = np.arange(int(math.ceil(rb)), int(math.floor(rt)) + 1)
    if len(r) == 0:
        return
    q = (r - rb) / max(1.0, rt - rb)
    hw = wt * np.where(q < 0.3, np.sqrt(np.maximum(q, 0.03) / 0.3), (1.0 - q) / 0.7)
    wd = np.maximum(1, np.rint(2 * hw)).astype(int)
    lf = np.rint(centre(r) - wd / 2.0).astype(int)
    dst = cool if v > 0.5 else M[0]
    for i in range(len(r)):
        y = fh - 1 - int(r[i])
        _span(dst, y, int(lf[i]), int(lf[i] + wd[i]), wrap)
        if v < 0.3 and nb > 1 and wd[i] >= 3:
            _span(M[1], y, int(lf[i]) + 1, int(lf[i] + wd[i]) - 1, wrap)


def _bed(M, B, f, n, inset, wrap):
    """the burning bed the tongues stand in: a mound (w, h at x), a wavy band of height h from x0 to x1
    (lam = wavelength, cyc = cycles per loop) or, for tiles, a wavy band across the tile"""
    nb, fh, fw = M.shape
    xs = np.arange(fw) + 0.5
    for j in range(nb):
        hj = B['h'] - j * B.get('step', inset)
        if hj < 0.5:
            break
        if 'x0' in B:                                           # a band from x0 to x1, its ends tapering
            amp, lam, c = B.get('amp', 1.2), B.get('lam', 22.0), B.get('cyc', 1)
            e = np.clip(np.minimum(xs - B['x0'], B['x1'] - xs) / max(3.0, 1.5 * B['h']), 0.0, 1.0)
            top = (hj + amp * np.sin(2 * math.pi * (xs / lam + c * f / n) + 0.8 * j)
                   + amp * 0.6 * np.sin(2 * math.pi * (xs / (lam * 0.62) - 2 * c * f / n) + 1.7 + 1.3 * j)) * np.sqrt(e)
        elif wrap:
            amp, nx = B.get('amp', 2.0), B.get('nx', 2)
            top = (hj + amp * np.sin(2 * math.pi * (xs / fw * nx + f / n) + 0.8 * j)
                   + amp * 0.6 * np.sin(2 * math.pi * (xs / fw * (nx + 1) - 2 * f / n) + 1.7 + 1.3 * j))
        else:
            wj = B['w'] - j * inset
            if wj < 1.0:
                break
            e = np.clip(1.0 - ((xs - B['x']) / wj) ** 2, 0.0, 1.0)
            top = (hj + 0.6 * math.sin(2 * math.pi * (f / n + 0.13 * j))) * np.sqrt(e)
        rows = np.clip(np.rint(top).astype(int), 0, fh)
        for xi in range(fw):
            if rows[xi] > 0:
                M[j, fh - rows[xi]:fh, xi] = True


def flame_frames(spec):
    """spec: n, fw, fh, tongues [tongue(..)], bed {x, w, h} | {h, amp, nx} (tile) | a list of beds,
    inset (px between two colour
    bands), cols (band colours, rim first), cool (a flamelet going out), wrap (True = horizontally tileable).  -> list of RGBA frames"""
    n, fw, fh = spec['n'], spec['fw'], spec['fh']
    cols = spec.get('cols', FIRE)
    nb = len(cols)
    inset = float(spec.get('inset', 1.0))
    wrap = bool(spec.get('wrap', False))
    out = []
    for f in range(n):
        M = np.zeros((nb, fh, fw), bool)
        cool = np.zeros((fh, fw), bool)
        for T in spec['tongues']:
            _tongue(M, cool, T, f, n, inset, wrap)
        beds = spec.get('bed') or []
        for B in (beds if isinstance(beds, list) else [beds]):      # one bed, or one per burning spot
            _bed(M, B, f, n, inset, wrap)
        # every inner band keeps a rim of the band outside it: left, right and above
        for j in range(1, nb):
            p = M[j - 1]
            if wrap:
                lr = np.roll(p, 1, 1) & np.roll(p, -1, 1)
            else:
                lr = np.zeros_like(p)
                lr[:, 1:-1] = p[:, :-2] & p[:, 2:]
            up = np.zeros_like(p)
            up[1:] = p[:-1]
            M[j] &= p & lr & up
        fr = np.zeros((fh, fw, 4), np.uint8)
        fr[cool] = rgb(spec.get('cool', COOL)) + (255,)
        for j in range(nb):
            fr[M[j]] = rgb(cols[j]) + (255,)
        out.append(fr)
    return out


def flame_sheet(spec):
    return sheet(flame_frames(spec))


def tile_tongues(tw, seed, sites, h, slim=(4.4, 5.6), seam=None, fat=0.5):
    """Tongues of a tileable wall of fire: `sites` places across tw, heights h = (low, high), each tongue
    h / slim wide; most sites fork (a smaller tongue leaning the other way).  Only the seam tongue (x = 0, the
    same in every tile of a set) crosses the tile's edge, so tiles of one set join in any order."""
    rng = np.random.default_rng(seed)
    out = [seam] if seam else []

    def put(x, w, hh, ph, m, ln):
        sw = 0.2 * w + 0.4
        mar = w + sw + abs(ln) + 2.0
        out.append(tongue(min(max(x, mar), tw - mar), w, hh, ph, m, ln, sw, fat=fat))

    for i in range(sites):
        k = (i + 0.5 + rng.uniform(-0.22, 0.22)) / sites
        tall = rng.random() ** 1.6 if i % 3 else 0.75 + 0.25 * rng.random()
        hh = h[0] + (h[1] - h[0]) * tall
        ww = hh / rng.uniform(*slim)
        ln = rng.uniform(-0.45, 0.45) * ww
        ph = rng.random()
        put(k * tw, ww, hh, ph, 1 if hh > 0.5 * h[1] else 2, ln)
        if rng.random() < 0.75:
            side = -1.0 if ln > 0 else 1.0
            fw_ = ww * rng.uniform(0.5, 0.65)
            put(k * tw + side * ww * rng.uniform(0.6, 1.0), fw_, hh * rng.uniform(0.5, 0.75),
                (ph + rng.uniform(0.3, 0.6)) % 1.0, 2 if hh < 0.8 * h[1] else 1, side * fw_ * 0.6)
    return out


# ------------------------------------------------------------------------------------------------ the kit's flames
def kit_flames():
    """name -> spec of every flame sheet of the standard kit (bottom-centre anchored; tiles: bottom-left)."""
    t = tongue
    hot4 = (FIRE[0], FIRE[1], FIRE[3], FIRE[4])
    S = {}
    # a candle, a stove's slit, the first flame of something catching
    S['flame_xs'] = dict(n=8, fw=10, fh=16, inset=1.0, cols=(FIRE[1], FIRE[3], FIRE[4]),
                         tongues=[t(5, 2.6, 10, 0.0, 1, 0.6, 0.7, 9, foot=0.55, rest=0.72)])
    S['flame_s'] = dict(n=8, fw=20, fh=30, inset=1.0, cols=hot4, bed=dict(x=10, w=7, h=3.5),
                        tongues=[t(10, 4.6, 18, 0.0, 1, 1.0, foot=0.7), t(6, 2.8, 11, 0.4, 1, -1.6, foot=0.8),
                                 t(14.5, 2.4, 9, 0.7, 2, 1.3, foot=0.8)])
    S['flame_m'] = dict(n=8, fw=36, fh=54, inset=1.4, bed=dict(x=18, w=14, h=5.5),
                        tongues=[t(18, 7.6, 33, 0.0, 1, 2.0), t(10, 5.2, 23, 0.38, 1, -3.0),
                                 t(26.5, 4.6, 19, 0.7, 1, 2.6), t(14.5, 3.2, 15, 0.2, 2, -1.5),
                                 t(22.5, 3.0, 12, 0.55, 2, 1.6)])
    S['flame_l'] = dict(n=10, fw=56, fh=92, inset=2.0, bed=dict(x=28, w=23, h=9),
                        tongues=[t(29, 11.0, 60, 0.0, 1, 3.0), t(16, 8.0, 43, 0.33, 1, -5.0),
                                 t(41, 7.2, 35, 0.66, 1, 4.2), t(23, 5.0, 30, 0.5, 1, -3.0),
                                 t(35, 4.6, 24, 0.15, 2, 3.0), t(9, 4.0, 18, 0.8, 2, -2.2),
                                 t(48, 3.6, 15, 0.25, 2, 2.0)])
    S['flame_xl'] = dict(n=12, fw=80, fh=144, inset=2.6, bed=dict(x=40, w=34, h=12),
                         tongues=[t(41, 15.0, 100, 0.0, 1, 4.0), t(24, 11.0, 74, 0.3, 1, -7.0),
                                  t(58, 10.0, 62, 0.62, 1, 6.0), t(33, 7.0, 52, 0.48, 1, -4.0),
                                  t(49, 6.4, 40, 0.14, 2, 4.4), t(14, 6.0, 34, 0.78, 2, -3.4),
                                  t(67, 5.2, 28, 0.22, 2, 3.0), t(38, 4.4, 26, 0.9, 2, 1.0)])
    S['flame_xxl'] = dict(n=12, fw=112, fh=212, inset=3.0, bed=dict(x=56, w=46, h=15),
                          tongues=[t(57, 19.0, 152, 0.0, 1, 6.0), t(34, 14.0, 116, 0.36, 1, -9.0),
                                   t(80, 13.0, 98, 0.66, 1, 8.0), t(46, 9.0, 84, 0.52, 1, -5.0),
                                   t(68, 8.4, 66, 0.18, 2, 5.6), t(20, 8.0, 56, 0.8, 2, -4.6),
                                   t(93, 7.0, 46, 0.26, 2, 4.0), t(56, 6.0, 44, 0.9, 2, 1.4),
                                   t(10, 5.0, 30, 0.44, 2, -2.4), t(102, 4.6, 26, 0.6, 2, 2.2)])
    # flames licking out of an opening and up the wall above it, leaning with the draught
    S['lick'] = dict(n=10, fw=48, fh=80, inset=1.7, bed=dict(x=20, w=15, h=5),
                     tongues=[t(18, 8.0, 54, 0.0, 1, 9.0, 2.6), t(28, 6.0, 40, 0.45, 1, 8.0, 2.0),
                              t(10, 5.0, 30, 0.7, 1, 5.0), t(23, 4.0, 22, 0.2, 2, 4.0), t(33, 3.4, 16, 0.85, 2, 3.0)])
    # tiles (wrap): fire filling an opening, a low ground fire, a low and a tall wall of fire (a / b join in any order)
    S['window'] = dict(n=8, fw=48, fh=32, inset=1.2, wrap=True, bed=dict(h=5, amp=1.6, nx=2, step=1.4),
                       tongues=tile_tongues(48, 411, 5, (12, 23), (2.7, 3.5), t(0, 5.0, 16, 0.1, 1, 0.0, fat=0.5)))
    S['ground'] = dict(n=8, fw=64, fh=26, inset=1.0, wrap=True, bed=dict(h=3, amp=1.0, nx=3, step=1.0),
                       tongues=tile_tongues(64, 421, 7, (6, 16), (2.5, 3.3), t(0, 3.4, 9, 0.1, 2, 0.0, fat=0.5)))
    for k, sd in (('a', 431), ('b', 437)):
        S['low_' + k] = dict(n=10, fw=96, fh=60, inset=1.5, wrap=True, bed=dict(h=8, amp=2.4, nx=3, step=1.8),
                             tongues=tile_tongues(96, sd, 6, (18, 44), (3.2, 4.2),
                                                  t(0, 8.0, 30, 0.1, 1, 0.0, fat=0.5)))
    for k, sd in (('a', 441), ('b', 447)):
        S['wall_' + k] = dict(n=12, fw=128, fh=136, inset=2.2, wrap=True, bed=dict(h=18, amp=3.0, nx=2, step=3.6),
                              tongues=tile_tongues(128, sd, 6, (44, 100), (4.4, 5.6),
                                                   t(0, 15.0, 70, 0.1, 1, 0.0, fat=0.5)))
    return S


# ------------------------------------------------------------------------------------------------ preview
def contact(frames_by_name, scale=3, every=1, bg=(10, 13, 19), pad=4, max_w=1500):
    """dev: rows of frames (name -> list of RGBA frames) magnified with NEAREST on a night-coloured ground"""
    rows = []
    for name, fr in frames_by_name.items():
        fr = fr[::every]
        h, w = fr[0].shape[:2]
        k = scale
        while k > 1 and (w * k + pad) * len(fr) > max_w:
            k -= 1
        row = Image.new('RGB', ((w * k + pad) * len(fr) + pad, h * k + 2 * pad), bg)
        for i, a in enumerate(fr):
            im = Image.fromarray(a, 'RGBA').resize((w * k, h * k), Image.NEAREST)
            row.paste(im, (pad + i * (w * k + pad), pad), im)
        rows.append(row)
    W = max(r.width for r in rows)
    out = Image.new('RGB', (W, sum(r.height for r in rows)), bg)
    y = 0
    for r in rows:
        out.paste(r, (0, y))
        y += r.height
    return out


# ------------------------------------------------------------------------------------------------ smoke
def _disc_tones(idx, cx, cy, r, light, ox=0, body=None):
    """paint one pixel disc into the tone-index map: 0 dark / 1 body / 2 lit, 2x2 checker between the tones;
    body = (x, y, radius) of the whole puff: the light falls on that volume, the disc adds its own roundness"""
    fh, fw = idx.shape
    x0, x1 = max(0, int(cx - r - 1)), min(fw, int(cx + r + 2))
    y0, y1 = max(0, int(cy - r - 1)), min(fh, int(cy + r + 2))
    if x1 <= x0 or y1 <= y0:
        return
    yy, xx = np.mgrid[y0:y1, x0:x1].astype(np.float32)
    dx, dy = xx + 0.5 - cx, yy + 0.5 - cy
    disc = dx * dx + dy * dy <= r * r + r * 0.6
    lv = (dx * light[0] + dy * light[1]) / max(r, 1.0)
    if body is not None:
        lv = 0.5 * lv + 0.75 * ((xx + 0.5 - body[0]) * light[0] + (yy + 0.5 - body[1]) * light[1]) / max(body[2], 1.0)
    chk = ((xx.astype(int) + ox) // 2 + yy.astype(int) // 2) % 2 == 0
    tone = np.ones(disc.shape, np.int8)
    tone[lv > 0.56] = 2
    tone[(lv > 0.36) & (lv <= 0.56) & chk] = 2
    tone[lv < -0.52] = 0
    tone[(lv < -0.3) & (lv >= -0.52) & chk] = 0
    sub = idx[y0:y1, x0:x1]
    sub[disc] = tone[disc]


def _tones_rgba(idx, tones, keep=None):
    fh, fw = idx.shape
    fr = np.zeros((fh, fw, 4), np.uint8)
    for k, c in enumerate(tones):
        sel = idx == k
        if keep is not None:
            sel &= keep
        fr[sel] = rgb(c) + (255,)
    return fr


def puff_frames(n, fw, fh, tones=SMOKE_WARM, seed=1, lobes=6, light=(0.28, 0.96), start=0.42, fade=0.38):
    """One puff's life in n frames: a tight ball swells into a cauliflower of discs that drift apart and
    turn, then breaks up through an ordered dither from the rim inward (from fade = share of its life on).
    tones = (dark, body, lit); light = the lit side (x, y; y down: (0, 1) is lit from straight below)."""
    rng = np.random.default_rng(seed)
    R = min(fw, fh) / 2.0 - 1.0
    cx, cy = fw / 2.0, fh / 2.0
    L = []
    for i in range(lobes):
        a = (i + rng.uniform(-0.45, 0.45)) / max(1, lobes - 1) * 2 * math.pi
        L.append((a, 0.0 if i == 0 else rng.uniform(0.30, 0.66), rng.uniform(0.24, 0.50) if i else 0.56,
                  rng.uniform(-0.6, 0.6)))
    order = list(rng.permutation(lobes))
    b = bayer(fh, fw)
    yy, xx = np.mgrid[0:fh, 0:fw].astype(np.float32)
    out = []
    for k in range(n):
        age = k / max(1, n - 1)
        grow = start + (1.0 - start) * (1.0 - (1.0 - age) ** 2)
        idx = np.full((fh, fw), -1, np.int8)
        for i in order:
            a, d, r, spin = L[i]
            aa = a + spin * age * 1.4
            px = round(cx + math.cos(aa) * d * R * grow)
            py = round(cy + math.sin(aa) * d * R * grow * 0.86)
            _disc_tones(idx, px, py, max(1.0, r * R * grow * (1.0 + 0.07 * math.sin(6.3 * age + a))), light,
                        body=(cx, cy, R * grow))
        keep = None
        if age > fade:
            ad = (age - fade) / (1.0 - fade)
            rn = np.hypot(xx + 0.5 - cx, yy + 0.5 - cy) / max(1.0, R * grow)
            lv = np.clip(1.35 - 1.5 * ad - 0.75 * rn * (0.3 + ad), 0.0, 1.0)
            keep = b < np.floor(lv * 4.0 + 0.5) / 4.0                # solid, 3/4, checker, 1/4, gone
        out.append(_tones_rgba(idx, tones, keep))
    return out


def bank_frames(n, tw, th, tones=SMOKE_WARM, seed=1, light=(0.28, 0.96), thin=0.0, fray=0.34, big=5, small=10):
    """A rolling bank of smoke hanging under a ceiling or a cornice, tileable in x, n looping frames: a few big
    billows of uneven size along its upper half, small ones hanging below, each breathing and circling a
    little; the underside frays out through the ordered dither (fray = share of the height).  thin = share of
    dither holes all over (a veil: the same seed gives the same billows, so a veil joins its bank).  The two
    billows on the seam are the same for every seed of one size, so banks of one size join in any order."""
    def billows(rng, seam):
        if seam:
            return [(0.0, th * 0.42, th * 0.33, 0.1, 1.6, 0), (tw * 0.04, th * 0.68, th * 0.2, 0.6, 1.4, 1)]
        out = []
        for i in range(big):
            r = th * rng.uniform(0.25, 0.4)
            m = r + 5.0
            out.append((min(max(tw * (i + 0.5 + rng.uniform(-0.3, 0.3)) / big, m), tw - m),
                        max(r + 3.0, th * rng.uniform(0.36, 0.48)), r, rng.random(), rng.uniform(1.0, 2.6), 0))
        for i in range(small):
            r = th * rng.uniform(0.12, 0.24)
            m = r + 5.0
            out.append((min(max(tw * (i + 0.5 + rng.uniform(-0.4, 0.4)) / small, m), tw - m),
                        min(th - r - 3.0, th * rng.uniform(0.56, 0.76)), r, rng.random(), rng.uniform(1.0, 2.2), 1))
        return out
    L = billows(None, True) + billows(np.random.default_rng(seed), False)
    L.sort(key=lambda l: (l[5], l[1]))
    yy = (np.arange(th, dtype=np.float32)[:, None] + 0.5) / th
    lv = np.clip((1.0 - yy) / max(fray, 1e-3), 0.0, 1.0)             # 1 above the fray, 0 at the underside
    keep = bayer(th, tw) < np.minimum(np.floor(lv * 4.0 + 0.5) / 4.0, 1.0 - thin)
    out = []
    for f in range(n):
        idx = np.full((th, tw), -1, np.int8)
        for (x, y, r, ph, orb, _) in L:
            a = 2 * math.pi * (f / n + ph)
            px, py = round(x + orb * math.cos(a)), round(y + orb * 0.6 * math.sin(a))
            rr = r + 1.2 * math.sin(a + 1.3)
            for dx in (-tw, 0, tw):
                _disc_tones(idx, px + dx, py, rr, light, ox=-dx, body=(px + dx, th * 0.5, th * 0.5))
        out.append(_tones_rgba(idx, tones, keep))
    return out


# ------------------------------------------------------------------------------------------------ sparks
def spark_frames(n, fw, fh, count=7, seed=1, rise=1.0):
    """A looping field of sparks over a fire: single pixels on arcs (a kick sideways that the updraught bends
    upward), cooling down SPARK as they age; each lives a part of the loop.  Bottom-centre anchored."""
    rng = np.random.default_rng(seed)
    P = []
    for i in range(count):
        life = int(rng.integers(max(3, n // 2), n))
        P.append((int(rng.integers(0, n)), life, fw / 2.0 + rng.uniform(-0.3, 0.3) * fw, rng.uniform(-1.3, 1.3),
                  rise * (fh - 3) / life * rng.uniform(0.7, 1.0), rng.uniform(0.0, 6.3)))
    out = []
    for f in range(n):
        fr = np.zeros((fh, fw, 4), np.uint8)
        for (t0, life, x0, vx, vy, ph) in P:
            a = (f - t0) % n
            if a >= life:
                continue
            u = a / life
            x = int(round(x0 + vx * a * (1.0 - 0.5 * u) + 1.2 * math.sin(ph + a * 0.9)))
            y = int(round(fh - 2 - vy * a))
            if 0 <= x < fw and 0 <= y < fh:
                fr[y, x] = rgb(SPARK[min(len(SPARK) - 1, int(u * len(SPARK)))]) + (255,)
                if a < 2 and y + 1 < fh:                              # a young spark draws a short tail
                    fr[y + 1, x] = rgb(SPARK[2]) + (255,)
        out.append(fr)
    return out


# ------------------------------------------------------------------------------------------------ light
def pool_frames(w, h, cx, cy, rx, ry, tints=LIGHT, n=4, breathe=1.5, zone=0.6, gamma=0.9, scales=None):
    """Fire light as a pool of flat ADDITIVE bands (tints: rim .. centre), every band dithered into the next
    and the rim into nothing; n frames in which the pool breathes by +-breathe px.  The ellipse (cx, cy,
    rx, ry) may lie partly outside the sprite (a wash from an edge).  zone = dithered share of each band.
    scales = one frame per radius scale instead (a pool that grows in steps: play the frames as stages)."""
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    b = bayer(h, w)
    nb = len(tints)
    out = []
    for f in range(len(scales) if scales else n):
        k = scales[f] if scales else 1.0 + breathe * (0.0, 1.0, 0.0, -1.0)[f % 4] / max(rx, ry)
        d = np.hypot((xx + 0.5 - cx) / (rx * k), (yy + 0.5 - cy) / (ry * k))
        lv = nb * np.clip(1.0 - d, 0.0, 1.0) ** gamma + (1.0 - zone / 2.0)
        band = np.clip(np.floor(lv + (b - 0.5) * zone), 0, nb).astype(int)
        band[d >= 1.0] = 0
        fr = np.zeros((h, w, 4), np.uint8)
        for i, c in enumerate(tints):
            fr[band == i + 1] = tuple(c) + (255,)
        out.append(fr)
    return out


# ------------------------------------------------------------------------------------------------ the kit
def build_kit():
    """name -> (list of frames, kind) for every sheet of the standard kit"""
    K = {}
    for name, spec in kit_flames().items():
        K[name] = (flame_frames(spec), 'tile' if spec.get('wrap') else 'flame')
    for tag, tones in (('', SMOKE_WARM), ('_grey', SMOKE_GREY)):
        K['puff_s' + tag] = (puff_frames(8, 16, 16, tones, 501, 4), 'puff')
        K['puff_m' + tag] = (puff_frames(10, 32, 30, tones, 502, 6), 'puff')
        K['puff_l' + tag] = (puff_frames(10, 60, 52, tones, 503, 7), 'puff')
        K['puff_xl' + tag] = (puff_frames(12, 104, 84, tones, 504, 9), 'puff')
        for v, sd in (('a', 511), ('b', 517)):                      # a / b join in any order; a veil joins its bank
            K['bank_%s%s' % (v, tag)] = (bank_frames(8, 160, 48, tones, sd), 'tile')
            K['veil_%s%s' % (v, tag)] = (bank_frames(8, 160, 48, tones, sd, thin=0.5), 'tile')
    K['sparks_s'] = (spark_frames(12, 24, 40, 5, 521), 'flame')
    K['sparks_m'] = (spark_frames(12, 56, 80, 11, 523), 'flame')
    for name, (w, h) in (('glow_s', (48, 48)), ('glow_m', (96, 96)), ('glow_l', (176, 176))):
        K[name] = (pool_frames(w, h, w / 2, h / 2, w / 2 - 2, h / 2 - 2, breathe=max(1.5, w * 0.02)), 'light')
    for name, (w, h) in (('pool_s', (64, 24)), ('pool_m', (120, 40)), ('pool_l', (200, 64))):
        K[name] = (pool_frames(w, h, w / 2, h / 2, w / 2 - 3, h / 2 - 2, breathe=max(1.5, w * 0.02)), 'light')
    return K


def save(arr, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    Image.fromarray(np.ascontiguousarray(arr), 'RGBA').save(path)


def main(argv=None):
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument('--preview', default='')
    ap.add_argument('--only', default='')
    a = ap.parse_args(argv)
    K = build_kit()
    if a.preview:
        names = [s for s in a.only.split(',') if s] or list(K)
        contact({k: K[k][0] for k in names}).save(a.preview)
        return
    meta = {'tick': TICK, 'fire': list(FIRE), 'cool': COOL, 'spark': list(SPARK), 'sheets': {}}
    for name, (frames, kind) in K.items():
        save(sheet(frames), os.path.join(OUT, name + '.png'))
        h, w = frames[0].shape[:2]
        meta['sheets'][name] = dict(n=len(frames), w=w, h=h, kind=kind)
    with open(os.path.join(OUT, 'kit.json'), 'w', encoding='utf-8', newline='\n') as f:
        f.write(json.dumps(meta, indent=1, sort_keys=True) + '\n')
    print('pixel_fire: %d sheets -> %s' % (len(K), OUT))


if __name__ == '__main__':
    main()
