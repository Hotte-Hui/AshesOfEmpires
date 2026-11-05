"""env_berlin_insignia -- regime insignia for the Berlin area (TECHNICAL_ARCHITECTURE §12.4).

Two variants of every insignia site exist:
* neutral (base file): the fictional Reichssiegel (white pillar in a black disc) or a plain eagle without
  swastika,
* historical ('_hist' file): the real national socialist state insignia -- the Reichsadler (state eagle, head
  turned to its right = viewer's left, spread wings, talons on an oak wreath that frames the swastika) and the
  swastika itself (right-facing, standing on a corner, i.e. rotated 45 degrees) on red/white/black flags.
They are drawn ONLY as in-world iconography of the regime inside the critical narrative (StGB §86 Abs. 4
social-adequacy clause): posters, stamps, a plaque, a flag on a facade -- never UI, rewards or decoration of
the player's side.  All shapes are original pixel drawings made by the functions below (no traced images).

Masks are boolean numpy arrays (h, w); painters choose ramps/tones.
"""
from __future__ import annotations

import math

import numpy as np

import env_berlin_kit as kit


# =========================================================================== swastika
_SW5 = ['#.###',
        '#.#..',
        '#####',
        '..#.#',
        '###.#']          # right-facing (clockwise) hooked cross on a 5x5 unit grid


def swastika_mask(size: int, rotate45: bool = True, weight: float = 1.0) -> np.ndarray:
    """Right-facing swastika in a size x size box; rotate45 stands it on a corner (flag/emblem form).
    Rasterised from the 5x5 unit pattern by supersampled coverage; small sizes use hand-tuned masks."""
    if rotate45 and size in _SW_HAND:
        return np.array([[c == '#' for c in row] for row in _SW_HAND[size]], bool)
    ss = 12
    n = size * ss
    yy, xx = np.mgrid[0:n, 0:n].astype(np.float32)
    u = (xx + 0.5) / ss - size / 2.0
    v = (yy + 0.5) / ss - size / 2.0
    if rotate45:
        a = math.radians(45.0)
        ru = u * math.cos(a) + v * math.sin(a)
        rv = -u * math.sin(a) + v * math.cos(a)
        # the rotated 5-unit cross must fit the box diagonal-wise
        scale = 5.0 / (size * 0.98)
    else:
        ru, rv = u, v
        scale = 5.0 / size
    gx = ru * scale + 2.5
    gy = rv * scale + 2.5
    inside = (gx >= 0) & (gx < 5) & (gy >= 0) & (gy < 5)
    cell = np.zeros_like(inside)
    gxi = np.clip(gx.astype(np.int32), 0, 4)
    gyi = np.clip(gy.astype(np.int32), 0, 4)
    pat = np.array([[c == '#' for c in row] for row in _SW5], bool)
    cell = inside & pat[gyi, gxi]
    cov = cell.reshape(size, ss, size, ss).mean(axis=(1, 3))
    return cov >= (0.5 / weight)


# hand-tuned 45-degree swastikas for tiny sizes (pixel clusters read better than raw coverage)
_SW_HAND = {
    7: ['..#....',
        '.#...#.',
        '..#.#.#',
        '...#...',
        '#.#.#..',
        '.#...#.',
        '....#..'],
    9: ['....#....',
        '...#.....',
        '..#...#..',
        '...#.#.#.',
        '#...#...#',
        '.#.#.#...',
        '..#...#..',
        '.....#...',
        '....#....'],
}


# =========================================================================== eagles
def _poly(m, pts, ss):
    """rasterise polygon pts (in output px) into supersampled mask m (in place)"""
    h, w = m.shape
    P = [(x * ss, y * ss) for (x, y) in pts]
    xs = [p[0] for p in P]; ys = [p[1] for p in P]
    y0, y1 = max(0, int(min(ys))), min(h, int(math.ceil(max(ys))) + 1)
    n = len(P)
    for row in range(y0, y1):
        yc = row + 0.5
        cross = []
        for i in range(n):
            ax, ay = P[i]; bx, by = P[(i + 1) % n]
            if (ay <= yc < by) or (by <= yc < ay):
                cross.append(ax + (yc - ay) * (bx - ax) / (by - ay))
        cross.sort()
        for k in range(0, len(cross) - 1, 2):
            a = max(0, int(math.ceil(cross[k] - 0.5)))
            b = min(w - 1, int(math.floor(cross[k + 1] - 0.5)))
            if b >= a:
                m[row, a:b + 1] = True


def _disc(m, cx, cy, r, ss, val=True):
    h, w = m.shape
    yy, xx = np.mgrid[0:h, 0:w]
    m[((xx + 0.5) / ss - cx) ** 2 + ((yy + 0.5) / ss - cy) ** 2 <= r * r] = val


def _down(m, ss, thr=0.5):
    h, w = m.shape
    return m.reshape(h // ss, ss, w // ss, ss).mean(axis=(1, 3)) >= thr


def eagle_masks(w: int, wreath: bool = True, swastika: bool = True, ss: int = 8) -> dict:
    """State eagle (Reichsadler form): returns dict of bool masks of identical shape (h, w):
    'body' (silhouette incl. wings/tail), 'lines' (feather separations, darker), 'eye',
    'wreath' (oak ring), 'swastika' (inside the wreath), 'all'.
    Head turned to the eagle's right (viewer's left); each wing is a fan of six slanted feathers whose tips
    step down toward the tail.  wreath=False gives a plain eagle whose talons grip a short bar (neutral)."""
    W = w
    s = W / 32.0                                 # design grid: wingspan 32 units
    # the wreath must hold a legible swastika (>= 7 px) even on small eagles -> scale it up when small
    ri = max(3.25, 3.7 / s)
    ro = ri + max(1.35, 1.3 / s)
    rcy = 19.0 + ro
    H = int(round(((rcy + ro + 0.4) if wreath else 18.6) * s))
    m = np.zeros((H * ss, W * ss), bool)
    lines = np.zeros_like(m)
    cx = W / 2.0

    def P(x, y):
        return (cx + x * s, y * s)

    def lead(t, sg):
        # leading edge: shoulder (2.0, 6.0) -> tip (15.8, 1.2), bowed upward
        x = 2.0 + 13.8 * t
        y = 6.0 - 4.8 * t - 1.3 * math.sin(math.pi * t) * 0.8
        return sg * x, y
    nf = 6
    for sg in (-1, 1):
        ts = np.linspace(0.0, 1.0, nf + 1)
        for k in range(nf):
            t0, t1 = ts[k], ts[k + 1]
            # inner feathers are longer: the trailing edge falls from the tip toward the tail
            ln = 10.6 - 6.4 * ((t0 + t1) / 2)
            dx, dy = 0.42 * sg, 1.0
            a = lead(t0, sg)
            b = lead(t1, sg)
            ab = (a[0] + dx * ln, a[1] + dy * ln)
            bb = (b[0] + dx * (ln - 0.6), b[1] + dy * (ln - 0.6))
            tip = ((ab[0] + bb[0]) / 2 + dx * 0.9, (ab[1] + bb[1]) / 2 + 0.9)
            pts = [P(*a), P(*b), P(*bb), P(*tip), P(*ab)]
            _poly(m, pts, ss)
            if k > 0:
                # separation line along the feather's inner edge, below the covert band
                c0 = (a[0] + dx * 1.8, a[1] + 1.8)
                c1 = (a[0] + dx * (ln - 0.4), a[1] + dy * (ln - 0.4))
                seg = np.zeros_like(m)
                _poly(seg, [P(*c0), P(c0[0] + 0.5 * sg, c0[1]), P(c1[0] + 0.5 * sg, c1[1]), P(*c1)], ss)
                lines |= seg
        # shoulder fill between the wing root and the body
        _poly(m, [P(sg * 1.2, 6.4), P(*lead(0.0, sg)), P(*lead(0.12, sg)), P(sg * 3.4, 15.0), P(sg * 1.6, 15.0)], ss)
    # ---- body
    _disc(m, cx, 9.6 * s, 2.6 * s, ss)
    _poly(m, [P(-2.3, 9.4), P(2.3, 9.4), P(1.8, 15.6), P(-1.8, 15.6)], ss)
    # ---- neck + head (turned to the viewer's left) + hooked beak
    _poly(m, [P(-1.7, 7.4), P(1.5, 7.4), P(1.0, 3.6), P(-1.3, 3.4)], ss)
    _disc(m, cx - 0.5 * s, 2.5 * s, 1.75 * s, ss)
    _poly(m, [P(-1.9, 1.5), P(-4.2, 2.2), P(-3.4, 3.7), P(-2.0, 3.3)], ss)
    eye = np.zeros_like(m)
    _disc(eye, cx - 1.05 * s, 2.15 * s, 0.45 * s, ss)
    # ---- tail fan (three feathers)
    _poly(m, [P(-1.6, 15.0), P(1.6, 15.0), P(3.1, 18.9), P(1.5, 18.2), P(0.0, 19.2), P(-1.5, 18.2),
              P(-3.1, 18.9)], ss)
    for sg in (-1, 1):
        seg = np.zeros_like(m)
        _poly(seg, [P(sg * 0.7, 16.0), P(sg * 1.2, 16.0), P(sg * 1.6, 18.6), P(sg * 1.1, 18.6)], ss)
        lines |= seg
    wr = np.zeros_like(m)
    sw = np.zeros((H, W), bool)
    if wreath:
        for sg in (-1, 1):                       # legs reaching down to the wreath
            _poly(m, [P(sg * 1.0, 15.4), P(sg * 2.2, 15.4), P(sg * 2.9, 19.4), P(sg * 1.9, 19.4)], ss)
        _disc(wr, cx, rcy * s, ro * s, ss)
        _disc(wr, cx, rcy * s, ri * s, ss, val=False)
        wr_lo = _down(wr, ss, 0.45)
        if swastika:
            d = int(round(2 * ri * s * 1.02))
            if d % 2 == 0:
                d -= 1
            d = max(7, d)
            smask = swastika_mask(d)
            oy = int(round(rcy * s - d / 2.0))
            ox = int(round(cx - d / 2.0))
            ys0, xs0 = max(0, oy), max(0, ox)
            sub = smask[ys0 - oy:, xs0 - ox:]
            hh, ww = min(sub.shape[0], H - ys0), min(sub.shape[1], W - xs0)
            sw[ys0:ys0 + hh, xs0:xs0 + ww] = sub[:hh, :ww]
    else:
        for sg in (-1, 1):                       # plain eagle: talons on a short perch bar
            _poly(m, [P(sg * 1.0, 15.4), P(sg * 2.2, 15.4), P(sg * 2.6, 17.6), P(sg * 1.6, 17.6)], ss)
        _poly(m, [P(-5.2, 17.4), P(5.2, 17.4), P(5.2, 18.3), P(-5.2, 18.3)], ss)
        wr_lo = np.zeros((H, W), bool)
    body = _down(m, ss)
    ln = _down(lines & m, ss, 0.3) & body
    eye_lo = _down(eye, ss, 0.3) & body
    ln &= kit.erode(body, 1)                     # feather lines never cut the outline
    sw &= ~body
    allm = body | wr_lo | sw
    return {'body': body, 'lines': ln, 'eye': eye_lo, 'wreath': wr_lo & ~sw, 'swastika': sw, 'all': allm,
            'size': (H, W)}


def reichssiegel(d: int):
    """fictional state emblem (neutral variant) -- delegated to the established kit drawing"""
    return kit.reichssiegel_mask(d)


# =========================================================================== previews (dev aid)
def preview_sheet(path: str):
    from PIL import Image
    tiles = []
    for d in (7, 9, 11, 13, 15, 19, 25):
        tiles.append(('sw%d' % d, swastika_mask(d).astype(np.uint8) * 255))
    for w in (15, 21, 27, 33, 41):
        e = eagle_masks(w)
        img = np.zeros(e['body'].shape, np.uint8)
        img[e['body']] = 200
        img[e['lines']] = 110
        img[e['eye']] = 30
        img[e['wreath']] = 160
        img[e['swastika']] = 255
        tiles.append(('eagle%d' % w, img))
        p = eagle_masks(w, wreath=False)
        img2 = np.zeros(p['body'].shape, np.uint8)
        img2[p['body']] = 200
        img2[p['lines']] = 110
        img2[p['eye']] = 30
        tiles.append(('plain%d' % w, img2))
    W = sum(t[1].shape[1] + 4 for t in tiles)
    H = max(t[1].shape[0] for t in tiles) + 4
    sheet = np.zeros((H, W), np.uint8) + 40
    x = 2
    for _, t in tiles:
        sheet[2:2 + t.shape[0], x:x + t.shape[1]] = np.maximum(t, 0)
        x += t.shape[1] + 4
    Image.fromarray(sheet, 'L').resize((W * 8, H * 8), Image.NEAREST).save(path)
