"""env_c4p2_berlin_life -- life strips and fx of L_C4P2_Berlin (people at work behind glass, the households in the
courtyard windows, steam, snow, smoke, lamps).

A life strip is a crop of the baked playfield layer with figures painted into it frame by frame in the same tone
space (env_c4p2_berlin_kit) -- so every frame is pixel-identical to the layer outside the figures and the strip sits
on the layer seamlessly.  Behind lit glass the figures are drawn in fixed tones (silhouettes with a warm rim, the
room light behind them); the glowing glass is carried by the strip's own emission frames (the figure's pixels cut
out of it).  On the open platform a figure is lit by the layer's baked light fields.  Every loop is periodic (frame
0 follows the last frame), deterministic, palette-pure.
"""
from __future__ import annotations

import math

import numpy as np

import env_c4p2_berlin_kit as K
import env_c4p2_berlin_layout as L
import pg


def _px(arr, x, y, col):
    h, w = arr.shape[:2]
    if 0 <= x < w and 0 <= y < h:
        arr[y, x] = col


def life_strip(base_c, base_em, box, frames, draw, world, fields=None, exposure=0.86, emissive_fig=False,
               clip=None, transparent=False):
    """box = (x0, y0, w, h) in layer coordinates.  draw(lay, k) paints frame k in tone space.  Returns
    (strip_rgba, strip_emission_rgba or None)."""
    x0, y0, w, h = box
    crop_c = base_c[y0:y0 + h, x0:x0 + w].copy()
    crop_e = base_em[y0:y0 + h, x0:x0 + w].copy()
    if transparent:
        crop_c[:] = 0
        crop_e[:] = 0
    sub = K.sub_fields(fields, x0, y0, w, h) if fields else None
    out_c, out_e = [], []
    for k in range(frames):
        lay = K.tlayer(w, h, 'life', world)
        draw(lay, k)
        m0 = ~lay.emis & ~lay.unlit
        lay.tone[m0] = lay.tone[m0] * (exposure if sub is not None else 1.0)
        lay.resolve(sub, seed=0)
        m = lay.c[..., 3] > 0
        if clip is not None:
            m &= clip
        fc = crop_c.copy()
        fc[m] = lay.c[m]
        fe = crop_e.copy()
        fe[m] = 0
        em = lay.emis & m
        if emissive_fig and em.any():
            fe[em] = lay.c[em]
        out_c.append(fc)
        out_e.append(fe)
    se = K.strip(out_e)
    return K.strip(out_c), (se if se[..., 3].any() else None)


# =========================================================================== small people (behind glass)
def person(lay, x, y, k=0, s=1.0, coat=('S', 2.0), skin=('Y', 1.0), hair=('I', 1.0), hat=None, face=1,
           arm=None, rim=None, apron=None, collar=None, bend=0, seated=False):
    """A waist-up person seen through a window / over a counter, its waist at (x, y), facing `face` (+1 right).
    s = size (1.0 ~ a 6 x 7 head).  arm: None | 'up' (to the mouth) | 'out' | 'table' | 'write' | 'raise'.
    rim = (ramp, tone) for the light edge from the room lamp behind; bend = head lowered by n px."""
    hw = max(3, int(round(5 * s)))
    hh = max(4, int(round(6 * s)))
    bw = max(5, int(round(9 * s)))
    bh = max(5, int(round(12 * s)))
    hx = x - hw // 2 + (bend if face > 0 else -bend) // 2
    hy = y - bh - hh + bend
    cr, ct = coat
    # body: shoulders rounded, shaded across
    for i in range(bw):
        c = (i + 0.5) / bw
        t = ct + (0.5 - c) * 0.6 * face
        top = y - bh + (1 if i in (0, bw - 1) else 0)
        lay.rect(x - bw // 2 + i, top, 1, y - top, cr, t, hgt=0.5)
    if apron:
        lay.rect(x - bw // 2 + 2, y - bh + 4, bw - 4, bh - 4, apron[0], apron[1])
    if collar:
        lay.rect(x - bw // 2 + 1, y - bh, bw - 2, 2, collar[0], collar[1])
    # neck + head
    lay.rect(x - 1, y - bh - 1, 2, 2, skin[0], skin[1] - 0.3)
    sr, st = skin
    lay.rect(hx, hy + 1, hw, hh - 1, sr, st, hgt=0.6)
    lay.vline(hx + (0 if face > 0 else hw - 1), hy + 2, hh - 3, sr, st - 0.5)
    hr, ht = hair
    lay.rect(hx, hy, hw, 2, hr, ht, hgt=0.7)
    lay.rect(hx + (0 if face > 0 else hw - 2), hy + 1, 2, max(2, hh // 2), hr, ht - 0.2)
    lay.px(hx + (hw - 1 if face > 0 else 0), hy + 3, 'I', 0.6)                         # eye
    lay.px(hx + (hw if face > 0 else -1), hy + 4, sr, st - 0.2)                         # nose
    if hat is not None:
        r, t, kind = hat
        if kind == 'cap':
            lay.rect(hx - 1, hy - 1, hw + 2, 2, r, t)
            lay.rect(hx + (hw - 1 if face > 0 else -2), hy + 1, 3, 1, r, t - 0.8)
        elif kind == 'hat':
            lay.rect(hx - 2, hy + 1, hw + 4, 1, r, t - 0.4)
            lay.rect(hx, hy - 2, hw, 3, r, t)
        elif kind == 'scarf':
            lay.rect(hx - 1, hy - 1, hw + 2, 3, r, t)
            lay.rect(hx + (-1 if face > 0 else hw - 1), hy + 1, 2, hh - 2, r, t - 0.4)
        elif kind == 'bun':
            lay.rect(hx + (-1 if face > 0 else hw - 2), hy - 1, 3, 3, hr, ht + 0.3)
        elif kind == 'field':                                                         # a soft field cap
            lay.rect(hx - 1, hy - 1, hw + 2, 2, r, t)
            lay.px(hx + (hw if face > 0 else -1), hy, r, t - 0.4)
    # arms
    ax = x + (bw // 2 - 1 if face > 0 else -bw // 2)
    sk = (sr, st)
    if arm == 'up':
        lay.rect(ax, y - bh + 2, 2, 5, cr, ct - 0.4)
        lay.rect(ax + (1 if face > 0 else -1), hy + hh - 1, 2, y - bh + 3 - (hy + hh - 1), cr, ct - 0.2)
        lay.px(ax + (2 if face > 0 else -2), hy + hh - 2, sk[0], sk[1])
    elif arm == 'out':
        lay.rect(ax + (1 if face > 0 else -5), y - bh + 6, 6, 2, cr, ct - 0.3)
        lay.px(ax + (7 if face > 0 else -6), y - bh + 6, sk[0], sk[1])
    elif arm == 'table':
        lay.rect(ax + (0 if face > 0 else -5), y - 3, 6, 2, cr, ct - 0.3)
        lay.px(ax + (6 if face > 0 else -6), y - 3, sk[0], sk[1])
    elif arm == 'write':
        lay.rect(ax + (0 if face > 0 else -4), y - 4 + (k % 2), 5, 2, cr, ct - 0.3)
        lay.px(ax + (5 if face > 0 else -5), y - 4 + (k % 2), sk[0], sk[1])
    elif arm == 'raise':
        lay.rect(ax + (1 if face > 0 else -2), hy - 2, 2, y - bh - hy + 4, cr, ct - 0.2)
        lay.px(ax + (1 if face > 0 else -2), hy - 3, sk[0], sk[1])
    if rim is not None:                                                              # backlit edge
        lay.vline(x - bw // 2 + (bw - 1 if face < 0 else 0), y - bh + 1, bh - 1, rim[0], rim[1])
        lay.px(hx + (hw - 1 if face < 0 else 0), hy + 1, rim[0], rim[1])
    return hx, hy, hw, hh


def person_front(lay, x, y, k=0, coat=('Q', 1.6), skin=('Y', 1.6), hair=('D', 1.6), bun=True, scarf=None,
                 rim=None, look_down=False, hand=None, bw=11, bh=8):
    """A waist-up person seen from the front (through a window), the waist at (x, y), x = the body's centre.
    Head 5 x 6 px with readable features: hair parted around the face, two eyes (lowered when look_down), the nose's
    shadow, the mouth; a bun; neck, scarf, the cardigan with its button line.  rim = (ramp, tone): the room lamp
    behind lights the hair's and the shoulders' edges.  hand = 'curtain': the near hand holds the curtain aside."""
    sr, st = skin
    hr, ht = hair
    cr, ct = coat
    hx, hy = x - 2, y - bh - 7
    # shoulders and body: a rounded trapezoid, darker toward the sides, the button line
    for i in range(bw):
        c = abs(i - (bw - 1) / 2.0) / (bw / 2.0)
        top = y - bh + (2 if c > 0.85 else (1 if c > 0.6 else 0))
        lay.rect(x - bw // 2 + i, top, 1, y - top + 1, cr, ct + 0.35 - c * 0.8, hgt=0.5)
    lay.vline(x, y - bh + 2, bh - 1, cr, ct - 0.7)
    for by in range(y - bh + 3, y + 1, 3):
        lay.px(x, by, 'I', 1.2)
    # neck and scarf
    lay.rect(x - 1, y - bh - 1, 3, 2, sr, st - 0.6)
    if scarf is not None:
        lay.rect(x - 2, y - bh, 5, 2, scarf[0], scarf[1])
        lay.px(x - 2, y - bh + 2, scarf[0], scarf[1] - 0.4)
        lay.px(x - 1, y - bh + 2, scarf[0], scarf[1] - 0.2)
    # the face
    lay.rect(hx, hy + 1, 5, 5, sr, st, hgt=0.6)
    lay.px(hx, hy + 3, sr, st - 0.5)
    lay.px(hx + 4, hy + 3, sr, st - 0.5)
    lay.rect(hx + 1, hy + 5, 3, 1, sr, st - 0.3)                                   # chin
    lay.px(hx, hy + 5, hr, ht - 0.2)
    lay.px(hx + 4, hy + 5, hr, ht - 0.2)
    ey = hy + (3 if look_down else 2)
    lay.px(hx + 1, ey, 'I', 0.8)                                                   # the eyes
    lay.px(hx + 3, ey, 'I', 0.8)
    if look_down:
        lay.px(hx + 1, ey - 1, sr, st - 0.6)                                       # lowered lids
        lay.px(hx + 3, ey - 1, sr, st - 0.6)
    lay.px(hx + 2, hy + 3, sr, st - 0.7)                                           # the nose's shadow
    lay.px(hx + 2, hy + 4 + (1 if look_down else 0), 'R', 1.6)                     # the mouth
    # hair: across the brow, down the sides, the bun on top
    lay.rect(hx, hy, 5, 1, hr, ht)
    lay.px(hx, hy + 1, hr, ht)
    lay.px(hx + 4, hy + 1, hr, ht - 0.2)
    lay.px(hx - 1, hy + 2, hr, ht - 0.4)
    lay.px(hx + 5, hy + 2, hr, ht - 0.5)
    lay.px(hx + 2, hy, hr, ht + 0.5)                                               # the parting
    if bun:
        lay.rect(hx + 1, hy - 2, 3, 2, hr, ht + 0.2)
    if rim is not None:
        rr, rt = rim
        lay.px(hx + 1, hy - 2 if bun else hy, rr, rt)
        lay.px(hx + 2, hy - 2 if bun else hy, rr, rt + 0.4)
        lay.px(hx - 1, hy + 2, rr, rt - 0.6)
        lay.px(hx + 5, hy + 2, rr, rt - 0.6)
        lay.hline(x - bw // 2 + 1, y - bh, 2, rr, rt - 0.4)
        lay.hline(x + bw // 2 - 2, y - bh, 2, rr, rt - 0.4)
    if hand == 'curtain':
        hxx = x - bw // 2 - 1
        lay.rect(hxx, y - bh + 1, 2, 2, sr, st)
        lay.px(hxx + 1, y - bh + 3, sr, st - 0.4)
    return hx, hy


# =========================================================================== fx (translucent, own ramps)
def snow_strip(R, w, h, frames=24, fps=8, n=110, seed=0, ramp='V', tones=(5, 4, 3), wind=(-3, 1.5), v=(12, 36),
               near_p=0.3):
    rng = np.random.default_rng(seed)
    T = frames / float(fps)
    out = np.zeros((frames, h, w, 4), np.uint8)
    for i in range(n):
        near = rng.random() < near_p
        vy = rng.uniform(v[1] * 0.72, v[1]) if near else rng.uniform(v[0], v[0] * 1.6)
        vx = rng.uniform(*wind)
        x0, y0 = rng.uniform(0, w), rng.uniform(-vy * T * 0.3, h)
        ph = rng.uniform(0, T)
        sw = rng.uniform(0.5, 1.6) * (2.0 if near else 1.0)
        for k in range(frames):
            age = ((k / fps) + ph) % T
            a = age / T
            fade = min(1.0, a / 0.18, (1 - a) / 0.18)
            if fade < 0.25:
                continue
            x = int(round(x0 + vx * age + sw * math.sin(2 * math.pi * age / T + i))) % w
            y = int(round(y0 + vy * age))
            if near:
                col = K.rgba(R, ramp, tones[0] if fade > 0.6 else tones[1])
                for dx, dy in ((0, 0), (1, 0), (0, 1), (1, 1)):
                    if dx + dy < 2 or fade > 0.7:
                        _px(out[k], x + dx, y + dy, col)
            else:
                _px(out[k], x, y, K.rgba(R, ramp, tones[1] if fade > 0.6 else tones[2]))
    return K.strip(list(out))


def drift_strip(R, w, h, frames=24, fps=8, n=60, seed=0, ramp='V', tones=(5, 4), vx=(30, 60), vy=(-4, 10)):
    """Snow blown in sideways through the open end of the hall (left to right), fading out as it goes."""
    rng = np.random.default_rng(seed)
    T = frames / float(fps)
    out = np.zeros((frames, h, w, 4), np.uint8)
    for i in range(n):
        sx = rng.uniform(*vx)
        sy = rng.uniform(*vy)
        y0 = rng.uniform(0, h)
        ph = rng.uniform(0, T)
        for k in range(frames):
            age = ((k / fps) + ph) % T
            a = age / T
            x = int(round(sx * age * (w / (vx[1] * T)) * 1.0))
            y = int(round(y0 + sy * age + 2 * math.sin(age * 3 + i)))
            fade = (1 - a) * min(1.0, a / 0.1)
            if fade < 0.2 or x >= w:
                continue
            col = K.rgba(R, ramp, tones[0] if fade > 0.55 else tones[1])
            col[3] = 255 if fade > 0.55 else 150
            _px(out[k], x, y % h, col)
            if fade > 0.7:
                _px(out[k], x - 1, y % h, col)
    return K.strip(list(out))


def plume_strip(R, w, h, frames=16, seed=0, ramp='V', base=4.0, dens=1.0, drift=0.0, warm_root=None, rise=3,
                spread=0.5, root=0.18, alphas=(0, 50, 92, 140)):
    """Steam / smoke rising from the bottom centre.  Steam (a pale base tone) is a soft veil: alpha in four
    levels, periodic noise scrolled one period per loop.  Smoke (base < 3: chimneys, an exhaust) is pixel art
    since round 13 -- the pixel fire kit's puffs (pixel_fire_bake.wisp) in three tones of the ramp, hard
    pixels, breaking up through the ordered dither."""
    if base < 3.0:
        import pixel_fire_bake as PFB
        t, n_ = int(round(base)), R.n(ramp)
        tones = tuple('#%02X%02X%02X' % tuple(int(v) for v in R.table[R[ramp], max(0, min(n_ - 1, t + d)), :3])
                      for d in (-1, 0, 1))
        return K.strip(PFB.wisp(w, h, frames, seed, tones, drift=drift))
    P = frames * rise
    nz = K.periodic_noise(w, P, 8, 10, seed, octaves=3, per_y=P)
    ys = np.arange(h, dtype=np.float32)[:, None]
    xs = np.arange(w, dtype=np.float32)[None, :]
    fr = []
    for k in range(frames):
        sh = (np.arange(h)[:, None] + k * rise) % P
        n = nz[sh, np.arange(w)[None, :]]
        up = 1 - ys / h
        cx = w / 2 + drift * up * w * 0.4 + (n - 0.5) * 4 * up
        width = (root + spread * up) * w / 2
        shape = np.clip(1 - np.abs(xs - cx) / np.maximum(1.0, width), 0, 1) ** 0.8
        shape *= np.clip(1.2 - up, 0, 1) * np.clip(ys / (h * 0.1) + 0.2, 0, 1)
        a = shape * (0.25 + 1.2 * (n - 0.3)) * dens
        thr = pg.bayer(w, h, k, 0, 4)
        level = np.zeros((h, w), np.int32)
        for cut in (0.16, 0.36, 0.6):
            level += (a + (thr - 0.5) * 0.2 > cut)
        alpha = np.array(alphas, np.uint8)[level]
        tone = base + (n - 0.5) * 1.6 + level * 0.4
        col = K.ramp_rgba(R, ramp, tone.astype(np.float32), alpha, seed=k)
        if warm_root is not None:
            rr = (ys > h * 0.8) & (alpha > 0) & ((thr + (ys - h * 0.8) / (h * 0.2)) > 1.0)
            warm = K.ramp_rgba(R, warm_root[0], np.full((h, w), warm_root[1], np.float32), alpha, seed=k)
            col[rr] = warm[rr]
        fr.append(col)
    return K.strip(fr)


def haze_strip(R, w, h, frames=24, seed=0, ramp='V', base=3.0, dens=0.6, drift=1, alphas=(0, 36, 64, 96)):
    """A slow, wide band of steam under the vault drifting sideways (periodic in x over one loop)."""
    P = frames * drift
    nz = K.periodic_noise(P + w, h, 22, 9, seed, octaves=3, per_x=P + w)
    ys = np.arange(h, dtype=np.float32)[:, None]
    env = np.clip(1 - np.abs(ys - h * 0.55) / (h * 0.5), 0, 1) ** 1.2
    fr = []
    for k in range(frames):
        n = np.roll(nz, -k * drift, axis=1)[:, :w]
        a = env * (n - 0.42) * 2.6 * dens
        thr = pg.bayer(w, h, k * drift, 0, 4)
        level = np.zeros((h, w), np.int32)
        for cut in (0.18, 0.4, 0.66):
            level += (a + (thr - 0.5) * 0.25 > cut)
        alpha = np.array(alphas, np.uint8)[level]
        tone = base + (n - 0.5) * 1.2 + level * 0.3
        fr.append(K.ramp_rgba(R, ramp, tone.astype(np.float32), alpha, seed=k))
    return K.strip(fr)


def blink_strip(on: np.ndarray, off: np.ndarray, frames=4, on_frames=(0, 1)):
    return K.strip([on.copy() if k in on_frames else off.copy() for k in range(frames)])
