"""pixel_fire_bake -- strips for the level scenes and small props, baked from the pixel fire kit's parts.

The films play the kit (pixel_fire.py -> assets/fx/pixel_fire/) live through scripts/render/pixel_fire.gd.  The
levels show fire as baked strips (scene.json decals / fx: n frames side by side at a fixed fps), so their
generators call these helpers instead: the same designed tongues, cauliflower puffs, sparks and flat light bands,
composed for a cell of any size and any loop length.  Hard pixels only (alpha 0 / 255, soft edges are ordered
dither), deterministic (seeded), every loop seamless.

    flames    fire over a fuel line: tongues at the burning spots, a low bed along the line -> frames
    hot       the hot core of flame frames (the additive emission twin of a level strip)
    column    a looping column of puffs (the smoke of a fire, a stovepipe, a chimney); wisp = a thin one
    ceiling   a still bank of smoke under a ceiling whose underside follows a line
    drift     a stretch of that bank rolling along (looping strip)
    halo      fire light as flat bands with dithered edges (one image; additive or as hard alpha)
    recolor   kit colours -> a scene's own palette (never tint at runtime)
    sparks / breathing pools are pixel_fire.spark_frames / pool_frames

    py -3 -P tools/pixelgen/pixel_fire_bake.py --preview FILE.png
"""
from __future__ import annotations

import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pixel_fire as PF  # noqa: E402

XS3 = (PF.FIRE[1], PF.FIRE[3], PF.FIRE[4])                          # a candle, a slit: three bands
HOT4 = (PF.FIRE[0], PF.FIRE[1], PF.FIRE[3], PF.FIRE[4])             # a small fire: four


def _cycles(hh, n, tick=PF.TICK):
    """cycles per loop of a tongue hh px high: small flames lick fast, tall ones slowly (whole cycles: seamless)"""
    return max(1, int(round((n / float(tick)) / (0.45 + hh / 130.0))))


def flames(w, h, n, spots, seed, height=1.0, base=0.15, cols=None, tick=PF.TICK, fill=True, cool=PF.COOL):
    """Fire over a fuel line along the bottom of a (h, w) cell, n looping frames.
    spots = [(x, half width of the burning place, strength 0..1)]: every spot gets a tongue (the strongest
    stand tallest, a neighbour of a taller tongue stays lower -- one mass with one summit), most of them a fork
    or two, and a mound of embers; base > 0 = a low fire along the whole line with small tongues in the gaps.
    height = share of the cell the tallest tongue may take (its flamelet still fits).  cols = the band
    colours, rim first (default: the kit's, as many bands as the size carries), cool = a flamelet going out.
    tick = the fps it is played at."""
    rng = np.random.default_rng(seed)
    low = (h - 1) / 1.27 < 24.0                                    # a low cell: no flamelets, the tongues use it all
    top = height * ((h - 1.5) if low else (h - 1) / 1.27)
    k_sway = max(1, int(round(n / float(tick) / 0.8)))
    T, beds, placed = [], [], []

    def put(x, ww, hh, ph, lean, **kw):
        if low:
            kw['det'] = False
        sw = 0.2 * ww + 0.4
        mar = ww + sw + abs(lean) + 1.0
        if 2 * mar > w:                                            # a narrow cell: a slimmer tongue in its middle
            lean = 0.0
            ww = max(1.2, (w / 2.0 - 1.4) / 1.2)
            sw = 0.2 * ww + 0.4
            mar = w / 2.0
        x = min(max(x, mar), w - mar)
        T.append(PF.tongue(x, ww, hh, ph, _cycles(hh, n, tick), lean, sw, k=k_sway, **kw))
        return x, ww

    for (x, sw_, k) in sorted(spots, key=lambda s: -(s[2] * (1.0 + 0.02 * s[1]))):
        hh = max(4.0, top * k)
        for (px, pw, ph_) in placed:
            if abs(x - px) < 2.0 * pw + 2.0:
                hh = min(hh, max(4.0, ph_ * rng.uniform(0.5, 0.72)))
        ww = min(1.5 * math.sqrt(hh), hh / 3.9, max(2.0, 1.4 * sw_))
        ph = rng.random()
        x1, ww1 = put(x, ww, hh, ph, rng.uniform(-0.25, 0.25) * ww, fat=0.25 if hh > 40 else 0.0)
        placed.append((x1, ww1, hh))
        side = 1.0 if (x1 < w / 2.0) == (rng.random() < 0.7) else -1.0
        if hh >= 9.0:
            for j, (share, p) in enumerate(((rng.uniform(0.5, 0.75), 0.85), (rng.uniform(0.3, 0.45), 0.55))):
                if rng.random() < p:
                    fw_ = ww1 * rng.uniform(0.5, 0.65)
                    s = side if j == 0 else -side
                    put(x1 + s * ww1 * rng.uniform(0.6, 1.0), fw_, hh * share, (ph + rng.uniform(0.3, 0.6)) % 1.0,
                        s * fw_ * 0.6)
        beds.append(dict(x=x1, w=max(sw_, ww1) * 1.2 + 1.0, h=min(14.0, max(2.5, hh * 0.12))))
    hmax = max([p[2] for p in placed] or [4.0])
    if base > 0:
        bh = min(12.0, max(3.0, 2.5 + 0.07 * top))                 # the burning line itself: a wavy band of embers
        beds.append(dict(x0=0.5, x1=w - 0.5, h=bh, amp=min(2.4, 0.8 + 0.15 * bh), lam=max(14.0, 4.0 * bh),
                         cyc=k_sway, step=max(1.0, bh / 4.5)))
        if fill:
            step = max(7.0, min(22.0, top * 0.13))
            lo, hi = (0.3, 0.7) if low else (0.14, 0.42)
            x = step * 0.6
            while x < w - 2:
                if all(abs(x - px) > pw * 1.1 for (px, pw, _) in placed):
                    hh = max(5.0, top * rng.uniform(lo, hi) * min(1.0, 0.55 + 3.0 * base))
                    put(x, min(1.5 * math.sqrt(hh), hh / 3.4), hh, rng.random(), rng.uniform(-0.6, 0.6),
                        fat=0.4 if hh > 24 else 0.0)
                x += step * rng.uniform(0.75, 1.25)
    if cols is None:
        cols = PF.FIRE if hmax >= 24 else HOT4 if hmax >= 13 else XS3
    return PF.flame_frames(dict(n=n, fw=w, fh=h, inset=min(3.0, max(1.0, 0.9 + hmax / 75.0)), cols=cols,
                                cool=cool, tongues=T, bed=beds))


def hot(frames, keep=PF.FIRE[2:]):
    """the hot core of flame frames: only the pixels in one of the `keep` colours (a level strip's emission twin:
    added on top it lifts the core, rim and body stay pure palette)"""
    cs = [PF.rgb(c) if isinstance(c, str) else tuple(c) for c in keep]
    out = []
    for fr in frames:
        m = np.zeros(fr.shape[:2], bool)
        for c in cs:
            m |= (fr[..., 0] == c[0]) & (fr[..., 1] == c[1]) & (fr[..., 2] == c[2]) & (fr[..., 3] > 0)
        e = np.zeros_like(fr)
        e[m] = fr[m]
        out.append(e)
    return out


def recolor(frames, table):
    """frames with every colour of `table` ({'#from': '#to' | (r, g, b)}) replaced: the kit's ramp -> a scene's"""
    tb = [(PF.rgb(a), PF.rgb(b) if isinstance(b, str) else tuple(b)[:3]) for a, b in table.items()]
    out = []
    for fr in frames:
        g = fr.copy()
        for a, b in tb:
            m = (fr[..., 0] == a[0]) & (fr[..., 1] == a[1]) & (fr[..., 2] == a[2]) & (fr[..., 3] > 0)
            g[m, 0], g[m, 1], g[m, 2] = b[0], b[1], b[2]
        out.append(g)
    return out


def paste(dst, src, x, y):
    """src over dst at (x, y), hard alpha, clipped"""
    h, w = src.shape[:2]
    H, W = dst.shape[:2]
    x0, y0, x1, y1 = max(0, x), max(0, y), min(W, x + w), min(H, y + h)
    if x1 <= x0 or y1 <= y0:
        return
    s = src[y0 - y:y1 - y, x0 - x:x1 - x]
    m = s[..., 3] > 0
    dst[y0:y1, x0:x1][m] = s[m]


def column(w, h, n, src, top, seed, tones=PF.SMOKE_WARM, cool=None, sizes=(16, 24, 32), count=7, loops=2,
           sway=3.0, slow=0.5, spread=1.5, warm_until=0.3, bend=1.6, life=10, start=0.28, fade=0.5):
    """A column of smoke, n looping frames of a (h, w) cell: `count` puffs are born per loop at src (x, y), live
    `loops` loops and climb to top (x, y) -- fast at first, slowing (slow = share of the rise lost), the wind
    taking them more the older they are (bend), swaying +-sway px.  Every puff runs the life drawn into its
    sheet (pixel_fire.puff_frames: it swells, then breaks up through the ordered dither), so nothing fades.
    sizes = the puffs' cell widths; tones = (dark, body, lit) near the fire, cool = the tones it takes once it
    is older than warm_until (out of the fire's light)."""
    rng = np.random.default_rng(seed)
    cache = {}

    def sprite(s, sd, tn, key):
        if (s, sd, key) not in cache:
            cache[(s, sd, key)] = PF.puff_frames(life, s, max(6, int(round(s * 0.92))), tn, sd,
                                                 lobes=min(9, 3 + s // 10), start=start, fade=fade)
        return cache[(s, sd, key)]

    P = []
    for p in range(count):
        P.append(((p + rng.uniform(-0.3, 0.3)) * n / float(count),
                  sizes[(p * 2 + int(rng.integers(0, 2))) % len(sizes)], seed * 7 + p % 4,
                  rng.uniform(-spread, spread), rng.random(), sway * rng.uniform(0.6, 1.0)))
    out = []
    for f in range(n):
        fr = np.zeros((h, w, 4), np.uint8)
        alive = []
        for p in P:
            for g in range(loops):
                alive.append(((((f - p[0]) % n) + g * n) / float(loops * n), p))
        for a, (b, s, sd, dx, ph, amp) in sorted(alive, key=lambda t: -t[0]):
            e = (a - slow * a * a / 2.0) / (1.0 - slow / 2.0)
            x = (src[0] + dx + (top[0] - src[0]) * a ** bend
                 + amp * math.sin(2 * math.pi * (1.3 * a + ph)) * min(1.0, 4 * a))
            y = src[1] + (top[1] - src[1]) * e
            warm = cool is None or a < warm_until
            S = sprite(s, sd, tones if warm else cool, warm)
            paste(fr, S[min(life - 1, int(a * life))], int(round(x)) - s // 2, int(round(y)) - S[0].shape[0] // 2)
        out.append(fr)
    return out


def wisp(w, h, n, seed, tones, drift=0.6, count=None):
    """A thin plume for a small cell (a stovepipe, a brazier, a kettle, a chimney far away): column() from the
    bottom centre, leaning with the draught (drift, about -1.5 .. 1.5); the puffs are large for the cell and
    stand close, so it reads as one trail."""
    ref = min(float(w), 0.8 * h)                                 # a wide cell (a vent): puffs sized by its height
    s2 = max(7, int(ref * 0.85))
    lean = 0.12 * ref * drift
    if count is None:
        count = max(5, min(10, int(math.ceil(h / (0.42 * ref)) * max(1.0, w / (1.6 * ref)))))
    return column(w, h, n, (w / 2.0 - lean, h - 0.26 * s2), (w / 2.0 + lean, 0.34 * s2), seed, tones=tones,
                  sizes=(max(5, int(ref * 0.55)), max(6, int(ref * 0.7)), s2), count=count, loops=2,
                  sway=0.04 * ref, spread=max(1.5, 0.4 * (w - ref)), start=0.45, fade=0.5)


MARKS = ('#010000', '#020000', '#030000', '#040000', '#050000')    # band 0 .. 4 as red values (see bands())
MARK_COOL = '#090000'


def bands(frame):
    """(band index map, -1 = empty, 9 = cooling flamelet) of a frame drawn with cols=MARKS[:k], cool=MARK_COOL:
    for generators that paint through their own layer API (height, emission) instead of pasting RGBA"""
    idx = np.full(frame.shape[:2], -1, np.int8)
    on = frame[..., 3] > 0
    idx[on] = frame[..., 0][on].astype(np.int8) - 1
    idx[on & (frame[..., 0] == 9)] = 9
    return idx


def _quarters(v):
    return np.floor(np.clip(v, 0.0, 1.0) * 4.0 + 0.5) / 4.0


def ceiling(w, h, bottom, seed, tones=PF.SMOKE_WARM, cool=None, warm=None, dens=None, fray=0.42, x_off=0,
            light=(0.28, 0.96)):
    """A still bank of smoke under a ceiling as one (h, w, 4) image: solid from the top, billows of uneven size
    along its underside at bottom[x] (px below the top, one value per column), the underside frayed through the
    ordered dither.  dens[x] 0..1 thins it to a veil (dither holes in quarters); warm[x] 0..1 = how much of it
    takes the fire-lit `tones` instead of `cool` (mixed by the dither)."""
    rng = np.random.default_rng(seed)
    bottom = np.maximum(np.asarray(bottom, np.float32), 1.0)
    idx = np.full((h, w), -1, np.int8)
    yy = np.arange(h, dtype=np.float32)[:, None] + 0.5
    rel = yy / bottom[None, :]
    chk = ((np.arange(w)[None, :] + x_off) // 2 + np.arange(h)[:, None] // 2) % 2 == 0
    idx[rel < 0.6] = 1
    idx[(rel < 0.22) | ((rel < 0.32) & chk)] = 0
    for (r0, r1, y0, y1, s0, s1) in ((0.2, 0.32, 0.36, 0.5, 0.2, 0.42), (0.13, 0.22, 0.54, 0.68, 0.14, 0.3),
                                     (0.07, 0.13, 0.7, 0.86, 0.1, 0.22)):
        x = float(rng.uniform(0.0, 12.0))
        while x < w:
            b = float(bottom[min(w - 1, int(x))])
            if b > 10.0:
                PF._disc_tones(idx, round(x), round(b * rng.uniform(y0, y1)), b * rng.uniform(r0, r1), light,
                               ox=x_off, body=(x, b * 0.5, b * 0.5))
            x += max(5.0, b * rng.uniform(s0, s1))
    q = _quarters((1.0 - rel) / fray)                                # the underside frays in quarters, like the kit's
    if dens is not None:                                             # .. the veil thins along x in the dither's 16 steps
        q = np.minimum(q, np.clip(np.asarray(dens, np.float32), 0.0, 1.0)[None, :])
    keep = PF.bayer(h, w, x_off, 0) < q
    out = PF._tones_rgba(idx, tones if cool is None else cool, keep)
    if cool is not None and warm is not None:
        lit = PF._tones_rgba(idx, tones, keep)
        m = PF.bayer(h, w, x_off + 2, 1) < np.clip(np.asarray(warm, np.float32), 0.0, 1.0)[None, :]
        out[m] = lit[m]
    return out


def drift(w, h, n, seed, tones=PF.SMOKE_WARM, shift=-1, thin=0.0, ends=28, periods=2, top=0.0):
    """A stretch of bank rolling along under a ceiling, n looping frames of a (h, w) cell: the kit's bank tile
    (w / periods wide) moved one tile width per loop (shift -1 = to the left), both ends of the stretch
    dissolving through the ordered dither; top > 0 = that share of its height frays out upward too (a
    stretch that hangs free under a veil, not against a ceiling)."""
    tw = int(math.ceil(w / float(periods)))
    tile = PF.bank_frames(n, tw, h, tones, seed, thin=thin, big=max(3, tw // 30), small=max(5, tw // 15))
    xs = np.arange(w)
    q = np.repeat(_quarters(np.minimum(xs + 0.5, w - xs - 0.5) / float(ends))[None, :], h, axis=0)
    if top > 0:
        q = np.minimum(q, _quarters((np.arange(h) + 0.5) / (top * h))[:, None])
    keep = PF.bayer(h, w) < q
    out = []
    for f in range(n):
        fr = tile[f][:, (xs - shift * int(round(f * tw / float(n)))) % tw].copy()
        fr[~keep] = 0
        out.append(fr)
    return out


def halo(w, h, cx, cy, rx, ry, tints=PF.LIGHT, zone=0.6, gamma=0.9):
    """Fire light around (cx, cy) as one (h, w, 4) image of flat bands (tints: rim .. centre, RGB), each band
    dithered into the next and the rim into nothing -- the still twin of the kit's breathing pools.  Shown
    additively (a level's emission twin, a glow layer) the tints are what it adds."""
    return PF.pool_frames(w, h, cx, cy, rx, ry, tints, n=1, breathe=0.0, zone=zone, gamma=gamma)[0]


def main(argv=None):
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument('--preview', required=True)
    a = ap.parse_args(argv)
    xs = np.arange(360, dtype=np.float32)
    z = np.zeros((40, 6, 4), np.uint8)
    small = (flames(30, 40, 16, [(15, 7, 0.9)], 34, 0.9, base=0.0)[::3] + [z]
             + [np.pad(f, ((14, 0), (0, 0), (0, 0))) for f in flames(20, 26, 8, [(10, 6, 1.0)], 5, 1.0, base=0.3)[::2]]
             + [z] + [np.pad(f, ((28, 0), (0, 0), (0, 0))) for f in flames(9, 12, 8, [(4.5, 2, 1.0)], 6, 1.0, base=0.0)[::2]])
    S = {
        'front': flames(52, 118, 16, [(14, 8, 1.0), (30, 10, 1.0), (44, 6, 0.8)], 31, 0.95)[::2],
        'chests': flames(196, 30, 16, [(20, 10, 0.7), (70, 14, 0.9), (120, 10, 0.6), (170, 12, 0.8)], 33, 0.7)[::6],
        'rows': flames(196, 160, 16, [(24, 10, 0.9), (84, 12, 1.0), (146, 12, 0.9), (180, 8, 0.6)], 42, 0.9)[::6],
        'c17': flames(64, 190, 16, [(16, 8, 1.0), (34, 12, 1.0), (52, 8, 0.9)], 36, 1.0)[::2],
        'small': small,
        'column': column(80, 220, 16, (40, 206), (52, 24), 7, cool=PF.SMOKE_GREY, sizes=(36, 44, 52))[::3],
        'xs': PF.flame_frames(PF.kit_flames()['flame_xs'])[::2] + flames(9, 12, 8, [(4.5, 2, 1.0)], 6, 1.0, base=0.0)[::2],
        'ceiling': [ceiling(360, 150, np.interp(xs, [0, 360], [60, 140]), 3, cool=PF.SMOKE_GREY,
                            warm=np.interp(xs, [0, 150, 360], [0, 0.2, 1.0]),
                            dens=np.interp(xs, [0, 120, 360], [0.3, 0.6, 1.0]))],
        'drift': drift(220, 70, 32, 9)[::16],
    }
    PF.contact(S, scale=2, max_w=1280).save(a.preview)


if __name__ == '__main__':
    main()
