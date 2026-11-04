"""gen_great_hall -- 2D pixel-art assets for the 3D Great Hall reveal (L_M1_HallReveal, shot S011).

Owner: great_hall_3d.  Builds on tools/pixelgen/pg.py (palette 'berlin', Bayer dithering, Layer, puffs,
smoke ribbons, normal maps).  Everything is original and deterministic (fixed seeds, no network).

Outputs (assets/architecture/great_hall/):
  sky.png      1024x720 painted sky matte.  Screen-space mapped 1:1 by pixel3d_post (the camera never rotates):
               texel (512, 430) = optical axis at elevation 0; FOV 24 deg -> focal 846.8 px @ 360 px height.
  fog.png      same mapping, distance-haze colour (no clouds).
  smoke.png    same mapping, transparent; drifting smoke ribbons (scrolled slowly by the post shader).
  people/<role>.png + _n.png   placeholder sprites: berlin_father, berlin_mother, berlin_child, guard
               (side view facing right, feet = bottom centre pixel) and tiny distant figures crowd_*.png.
  props/suitcase_a.png, suitcase_b.png, bundle.png (+ _n)
  textures/door_sealed.png  the sealed apartment door (official seal strip + notice)
  textures/drawing.png      the elevation drawing on the archive desk (shot h1)
  textures/banner.png       grey-black banner with the small fictional Reichssiegel
  textures/posters.png      notice board next to the door
Run:  py -3 -P tools/pixelgen/gen_great_hall.py
"""
from __future__ import annotations

import math
import os
import sys

import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pg  # noqa: E402

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..',
                                     'assets', 'architecture', 'great_hall'))
B = pg.PALETTES['berlin']
ALL = pg.all_colors('berlin')
H = pg.hx

# Matte geometry (must match hall_reveal.gd / pixel3d_post.gdshader)
SKY_W, SKY_H = 1024, 720
ANCHOR = (512, 430)
# Final composed frame: lens shift 56 px -> screen (x, y) maps to texel (x + 192, y + 194)
SUN = (612, 346)          # texel position of the sun disc (hidden behind the dome's right shoulder)


def out(*parts):
    p = os.path.join(ROOT, *parts)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    return p


def save_rgba(arr, path):
    Image.fromarray(arr.astype(np.uint8), 'RGBA').save(path)


# ============================================================================ banded dithered ramps
def ramp_fill(t: np.ndarray, cols, seam: float = 0.3, x0: int = 0, y0: int = 0) -> np.ndarray:
    """Map tone t (0..1) onto colour list with solid bands and narrow Bayer-dithered seams."""
    h, w = t.shape
    n = len(cols) - 1
    s = np.clip(t, 0, 1) * n
    base = np.floor(s)
    f = s - base
    thr = pg.bayer(w, h, x0, y0)
    up = (np.clip((f - 0.5) / max(seam, 1e-3) + 0.5, 0, 1) > thr).astype(int)
    idx = np.clip(base.astype(int) + up, 0, n)
    carr = np.stack([H(c) for c in cols])
    return carr[idx]


SKY_RAMP = ['#211623', '#2A2130', '#342F37', '#443B43', '#57494D', '#735145', '#8D5542', '#AF6C47',
            '#D07744', '#E5945A', '#F0AE6E', '#F4BA81', '#F8D2A0', '#FCE9C8']


def sky_tone():
    yy, xx = np.mgrid[0:SKY_H, 0:SKY_W].astype(np.float32)
    elev = (ANCHOR[1] - yy)                       # pixels above the horizon
    up = np.clip(elev / 250.0, 0.0, 1.0) ** 0.85
    t = np.where(elev > 0, 0.50 - 0.42 * up, 0.52 - np.clip(-elev / 200.0, 0, 1) * 0.1)
    # broad warm band along the horizon
    t += 0.13 * np.exp(-((elev - 22) / 46.0) ** 2)
    # sun glow (elliptic, wider than tall), plus a tight core
    dx = (xx - SUN[0]) / 300.0
    dy = (yy - SUN[1]) / 120.0
    g = np.exp(-(dx * dx + dy * dy) * 1.6)
    t += 0.36 * g
    dx2 = (xx - SUN[0]) / 70.0
    dy2 = (yy - SUN[1]) / 46.0
    t += 0.22 * np.exp(-(dx2 * dx2 + dy2 * dy2) * 1.4)
    # very slow large-scale variation so the bands are not ruler-straight
    nz = pg.value_noise(SKY_W, SKY_H, 90, seed=5, octaves=3)
    t += (nz - 0.5) * 0.05
    return np.clip(t, 0, 1)


def stratus_mask(w, h, x0, y0, length, thick, seed, taper=0.22):
    """One long sunset cloud streak: lumpy top edge, nearly flat bottom, tapered ends.
    Returns (mask, bottom_row_mask) in full-size arrays."""
    m = np.zeros((h, w), bool)
    bot = np.zeros((h, w), bool)
    n = pg.value_noise(int(length) + 4, 1, max(6.0, length / 9.0), seed=seed, octaves=3)[0]
    n2 = pg.value_noise(int(length) + 4, 1, 5.0, seed=seed + 7, octaves=2)[0]
    for i in range(int(length)):
        x = x0 + i
        if x < 0 or x >= w:
            continue
        t = i / max(1.0, length - 1)
        env = min(1.0, t / taper, (1 - t) / taper) ** 0.6
        top = thick * env * (0.45 + 0.75 * n[i])
        b = 1.0 + (n2[i] - 0.5) * 1.6 * env
        ya = int(round(y0 - top))
        yb = int(round(y0 + b))
        if yb <= ya:
            continue
        ya = max(0, ya)
        yb = min(h - 1, yb)
        m[ya:yb + 1, x] = True
        bot[yb, x] = True
    return m, bot


def make_sky():
    t = sky_tone()
    img = ramp_fill(t, SKY_RAMP, seam=0.28)
    yy, xx = np.mgrid[0:SKY_H, 0:SKY_W]
    sund = np.sqrt(((xx - SUN[0]) / 360.0) ** 2 + ((yy - SUN[1]) / 170.0) ** 2)
    warm = np.clip(1.15 - sund, 0, 1)
    rng = np.random.default_rng(11)
    hy = ANCHOR[1]
    # cloud streaks in layers: (elevation px, count, length range, thickness range)
    layers = [(18, 9, (60, 190), (2, 4)), (44, 10, (80, 260), (3, 6)), (82, 9, (120, 320), (4, 9)),
              (135, 8, (160, 380), (6, 12)), (200, 7, (200, 460), (8, 16))]
    cloud = np.zeros((SKY_H, SKY_W), bool)
    belly = np.zeros((SKY_H, SKY_W), bool)
    seed = 100
    for elev, count, lr, tr in layers:
        for k in range(count):
            seed += 1
            length = rng.uniform(*lr)
            x0 = rng.uniform(-80, SKY_W - length * 0.4)
            y0 = hy - elev + rng.uniform(-8, 8) * (1 + elev / 120)
            m, b = stratus_mask(SKY_W, SKY_H, int(x0), y0, length, rng.uniform(*tr), seed)
            cloud |= m
            belly |= b
    belly &= cloud
    belly2 = np.zeros_like(cloud)
    belly2[:-1] = belly[1:] & cloud[:-1]
    belly2 &= ~belly
    elev = hy - yy
    body_t = np.clip(0.12 + 0.18 * warm + 0.12 * np.clip(elev / 260.0, 0, 1), 0, 1)
    body = ramp_fill(body_t, ['#211623', '#2A2130', '#342F37', '#443B43', '#57494D'], seam=0.35)
    img[cloud] = body[cloud]
    lit_t = np.clip(0.15 + 0.85 * warm, 0, 1)
    lit = ramp_fill(lit_t, ['#57494D', '#735145', '#AF6C47', '#D07744', '#F0AE6E', '#F8D2A0'], seam=0.4)
    img[belly] = lit[belly]
    lit2 = ramp_fill(np.clip(lit_t - 0.3, 0, 1), ['#443B43', '#57494D', '#735145', '#AF6C47', '#E5945A'],
                     seam=0.5)
    sel = belly2 & (warm > 0.25)
    img[sel] = lit2[sel]
    # sun disc (mostly hidden by the dome)
    d = np.sqrt((xx - SUN[0]) ** 2 + (yy - SUN[1]) ** 2)
    img[d <= 13.5] = H('#F8D2A0')
    img[d <= 11.0] = H('#FCE9C8')
    # distant skyline at the horizon (hazy): blocks, chimneys, a crane, a radio mast
    sk = pg.Layer(SKY_W, SKY_H)
    rng2 = np.random.default_rng(3)
    x = 0
    while x < SKY_W:
        w = int(rng2.integers(14, 46))
        h = int(rng2.integers(3, 12))
        sk.rect(x, hy - h, w, h + 12, H('#443B43'))
        if rng2.random() < 0.3:
            cx = x + int(rng2.integers(2, max(3, w - 3)))
            ch = int(rng2.integers(10, 22))
            sk.rect(cx, hy - h - ch, 2, ch, H('#443B43'))
        x += w + int(rng2.integers(0, 6))
    sk.line(250, hy - 40, 250, hy, H('#443B43'))
    sk.line(232, hy - 40, 274, hy - 40, H('#443B43'))
    sk.line(250, hy - 46, 274, hy - 40, H('#443B43'))
    sk.line(842, hy - 64, 842, hy, H('#443B43'))
    for k in range(0, 64, 8):
        sk.px(841, hy - 64 + k, H('#443B43'))
        sk.px(843, hy - 64 + k + 4, H('#443B43'))
    a = sk.alpha()
    sk_t = np.clip(0.35 + 0.5 * warm, 0, 1)
    skc = ramp_fill(sk_t, ['#342F37', '#443B43', '#57494D', '#735145', '#8D5542'], seam=0.4)
    img[a] = skc[a]
    # a few crows (2-3 px)
    for (bx, by) in [(300, 300), (309, 296), (318, 303), (700, 270)]:
        for dx, dy in ((-2, -1), (-1, 0), (0, 0), (1, 0), (2, -1)):
            img[by + dy, bx + dx] = H('#211623')
    rgba = np.concatenate([img[..., :3], np.full((SKY_H, SKY_W, 1), 255, np.uint8)], -1)
    save_rgba(rgba, out('sky.png'))
    return rgba


def make_fog():
    yy, xx = np.mgrid[0:SKY_H, 0:SKY_W].astype(np.float32)
    elev = ANCHOR[1] - yy
    t = 0.62 - 0.5 * np.clip(elev / 260.0, 0, 1) ** 0.8
    t = np.where(elev < 0, 0.6, t)
    dx = (xx - SUN[0]) / 360.0
    dy = (yy - SUN[1]) / 150.0
    t += 0.22 * np.exp(-(dx * dx + dy * dy) * 1.5)
    rgb = ramp_fill(np.clip(t, 0, 1), ['#2A2130', '#342F37', '#443B43', '#57494D', '#735145', '#8D5542',
                                      '#AF6C47'], seam=0.6)
    rgba = np.concatenate([rgb[..., :3], np.full((SKY_H, SKY_W, 1), 255, np.uint8)], -1)
    save_rgba(rgba, out('fog.png'))


def smoke_band(L, path, w0, w1, seed, cols):
    """Smooth smoke band along a bezier path: noisy width, top side lit, bottom side dark."""
    pts = np.asarray(pg.bezier(path, n=400), np.float32)
    h, w = L.h, L.w
    x0 = int(max(0, pts[:, 0].min() - w1 * 1.5))
    x1 = int(min(w, pts[:, 0].max() + w1 * 1.5))
    y0 = int(max(0, pts[:, 1].min() - w1 * 1.5))
    y1 = int(min(h, pts[:, 1].max() + w1 * 1.5))
    yy, xx = np.mgrid[y0:y1, x0:x1].astype(np.float32)
    best = np.full(xx.shape, 1e9, np.float32)
    tbest = np.zeros(xx.shape, np.float32)
    sgn = np.zeros(xx.shape, np.float32)
    n = len(pts)
    for i in range(0, n, 2):
        px, py = pts[i]
        d = (xx - px) ** 2 + (yy - py) ** 2
        m = d < best
        best[m] = d[m]
        tbest[m] = i / (n - 1)
        sgn[m] = (yy - py)[m]
    dist = np.sqrt(best)
    nz = pg.value_noise(x1 - x0, y1 - y0, 9, seed=seed, octaves=4)
    width = (w0 + (w1 - w0) * tbest ** 0.8) * (0.55 + 0.75 * nz)
    inside = dist < width * 0.5
    tone = np.clip(0.45 - 0.5 * np.tanh(sgn / np.maximum(width * 0.35, 1.0)) * 0.6 + (nz - 0.5) * 0.5, 0, 1)
    sub = ramp_fill(tone, cols, seam=0.5, x0=x0, y0=y0)
    reg = L.c[y0:y1, x0:x1]
    reg[inside] = sub[inside]
    fringe = inside & (dist > width * 0.5 * 0.72)
    thr = pg.bayer(x1 - x0, y1 - y0, x0, y0)
    reg[fringe & (thr > 0.5)] = 0


def make_smoke():
    """Two broad chimney plumes far behind the city, bent by the wind into long bands."""
    L = pg.Layer(SKY_W, SKY_H, 'smoke')
    hy = ANCHOR[1]
    cols = ['#211623', '#2A2130', '#342F37', '#443B43', '#57494D']
    smoke_band(L, [(214, hy - 18), (220, hy - 64), (262, hy - 100), (360, hy - 118), (520, hy - 126)], 4, 30, 31,
               cols)
    smoke_band(L, [(808, hy - 14), (814, hy - 50), (850, hy - 84), (930, hy - 100), (1060, hy - 106)], 3, 24, 32,
               cols)
    save_rgba(L.c, out('smoke.png'))


# ============================================================================ figures
OUTLINE = '#120C14'
MATS = {
    'coat_f': ['#1E2329', '#2F363F', '#454E58'],
    'cap_f': ['#1B1520', '#25202B', '#342F37'],
    'skin': ['#7A5E4E', '#94735C', '#AE8A6C'],
    'trou': ['#1B1520', '#25202B', '#342F37'],
    'shoe': ['#120C14', '#1B1520', '#25202B'],
    'scarf_f': ['#5F4530', '#735145', '#8D5542'],
    'coat_m': ['#4A3A35', '#5F4A40', '#7A5E4E'],
    'scarf_m': ['#2C4440', '#3E5D55', '#56776A'],
    'stock': ['#25202B', '#342F37', '#443B43'],
    'coat_c': ['#5F4530', '#735145', '#8D5542'],
    'cap_c': ['#8D5542', '#AF6C47', '#D07744'],
    'coat_g': ['#2F363F', '#454E58', '#5F6973'],
    'cap_g': ['#1E2329', '#2F363F', '#454E58'],
    'leath': ['#120C14', '#1B1520', '#25202B'],
    'rifle': ['#120C14', '#1E2329', '#2F363F'],
    'bag': ['#4A3A35', '#5F4530', '#735145'],
    'hair_m': ['#25202B', '#342F37', '#4A3A35'],
    'paper': ['#B2ACB0', '#D2CCCB', '#ECE6E0'],
    'case_a': ['#4A3A35', '#5F4530', '#735145'],
    'case_b': ['#2C4440', '#3E5D55', '#56776A'],
    'strap': ['#120C14', '#1B1520', '#25202B'],
    'metal': ['#5F6973', '#7C8690', '#A3ACB4'],
    'cloth': ['#5F4A40', '#7A5E4E', '#94735C'],
}


class Fig:
    """Tiny paper-doll rasteriser: parts are drawn back to front into a material-id map with a height
    field (rounded per part), then shaded with 3-tone ramps, outlined and turned into a normal map."""

    def __init__(self, w, h):
        self.w, self.h = w, h
        self.mid = np.full((h, w), '', dtype=object)
        self.hgt = np.zeros((h, w), np.float32)
        self.part = np.zeros((h, w), np.int32)
        self.n = 0
        self.fixed = {}

    def _mask_poly(self, pts):
        L = pg.Layer(self.w, self.h)
        m, x0, y0 = L.poly_mask(pts)
        full = np.zeros((self.h, self.w), bool)
        X0, Y0 = max(0, x0), max(0, y0)
        X1, Y1 = min(self.w, x0 + m.shape[1]), min(self.h, y0 + m.shape[0])
        if X1 > X0 and Y1 > Y0:
            full[Y0:Y1, X0:X1] = m[Y0 - y0:Y1 - y0, X0 - x0:X1 - x0]
        return full

    def _mask_ell(self, cx, cy, rx, ry):
        yy, xx = np.mgrid[0:self.h, 0:self.w]
        return (((xx + 0.5 - cx) / rx) ** 2 + ((yy + 0.5 - cy) / ry) ** 2) <= 1.0

    def _put(self, mask, mat, bump=1.0, z=0.0):
        self.n += 1
        # rounded height inside the part: distance to its own edge (cheap chamfer)
        d = mask.astype(np.float32)
        acc = d.copy()
        cur = mask.copy()
        for k in range(1, 4):
            p = np.pad(cur, 1)
            cur = cur & p[:-2, 1:-1] & p[2:, 1:-1] & p[1:-1, :-2] & p[1:-1, 2:]
            acc += cur
        hh = z + bump * np.sqrt(acc / 4.0)
        self.mid[mask] = mat
        self.hgt[mask] = hh[mask]
        self.part[mask] = self.n

    def poly(self, pts, mat, bump=1.0, z=0.0):
        self._put(self._mask_poly(pts), mat, bump, z)

    def ell(self, cx, cy, rx, ry, mat, bump=1.0, z=0.0):
        self._put(self._mask_ell(cx, cy, rx, ry), mat, bump, z)

    def rect(self, x0, y0, x1, y1, mat, bump=1.0, z=0.0):
        self.poly([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], mat, bump, z)

    def px(self, x, y, col):
        self.fixed[(int(x), int(y))] = col

    def render(self, light=(-0.55, -0.55, 0.65), rim_side=-1):
        a = self.mid != ''
        hp = np.pad(self.hgt, 1, mode='edge')
        gx = (hp[1:-1, 2:] - hp[1:-1, :-2]) * 0.5
        gy = (hp[2:, 1:-1] - hp[:-2, 1:-1]) * 0.5
        # part boundaries inside the figure read as creases (slightly darker)
        pp = np.pad(self.part, 1, mode='edge')
        seam = ((pp[1:-1, 2:] != self.part) | (pp[2:, 1:-1] != self.part)) & a
        nrm = np.stack([-gx * 2.2, -gy * 2.2, np.ones_like(gx)], -1)
        nrm /= np.linalg.norm(nrm, axis=-1, keepdims=True)
        Lv = np.asarray(light, np.float32)
        Lv /= np.linalg.norm(Lv)
        lam = np.clip((nrm * Lv).sum(-1), 0, 1)
        tone = 0.25 + 0.85 * lam
        tone[seam] -= 0.22
        img = np.zeros((self.h, self.w, 4), np.uint8)
        thr = pg.bayer(self.w, self.h)
        for mat in set(self.mid[a].tolist()):
            m = (self.mid == mat)
            cols = MATS[mat]
            s = np.clip(tone, 0, 0.999) * len(cols)
            idx = np.floor(s).astype(int)
            f = s - idx
            idx = idx + ((f > 0.75) & (thr < 0.5))       # sparse dither only near the band edge
            idx = np.clip(idx, 0, len(cols) - 1)
            carr = np.stack([H(c) for c in cols])
            img[m] = carr[idx[m]]
        # selective outline: on the figure's own edge pixels; facing the key light it uses the material's
        # darkest shade instead of the outline colour
        p = np.pad(a, 1)
        edge = a & ~(p[:-2, 1:-1] & p[2:, 1:-1] & p[1:-1, :-2] & p[1:-1, 2:])
        lit_edge = edge & (nrm[..., 0] * Lv[0] + nrm[..., 1] * Lv[1] > 0.18)
        img[edge] = H(OUTLINE)
        for mat in set(self.mid[lit_edge].tolist()):
            m = lit_edge & (self.mid == mat)
            img[m] = H(MATS[mat][0])
        for (x, y), col in self.fixed.items():
            if 0 <= x < self.w and 0 <= y < self.h:
                img[y, x] = H(col)
        # normal map (OpenGL, +Y up): image y grows downward
        nm = np.stack([nrm[..., 0], -nrm[..., 1], nrm[..., 2]], -1)
        nimg = np.clip((nm * 0.5 + 0.5) * 255, 0, 255).astype(np.uint8)
        nimg = np.concatenate([nimg, (a * 255).astype(np.uint8)[..., None]], -1)
        return img, nimg

    def save(self, path, **kw):
        img, nimg = self.render(**kw)
        save_rgba(img, path + '.png')
        save_rgba(nimg, path + '_n.png')
        return img


def fig_father():
    f = Fig(18, 46)
    # legs (back then front), shoes
    f.poly([(6.0, 31), (9.0, 31), (8.8, 44), (6.2, 44)], 'trou', 0.8)
    f.poly([(8.4, 31), (11.0, 31), (11.6, 44), (9.0, 44)], 'trou', 0.9, 0.2)
    f.poly([(5.2, 43.6), (9.2, 43.6), (9.4, 46), (5.0, 46)], 'shoe', 0.5)
    f.poly([(8.6, 43.8), (12.6, 44.2), (13.2, 46), (8.6, 46)], 'shoe', 0.5, 0.2)
    # coat body (overcoat to the knees)
    f.poly([(4.6, 10.2), (10.8, 10.0), (11.8, 13), (12.0, 22), (12.8, 33.2), (3.6, 33.2), (4.2, 22),
            (3.9, 13)], 'coat_f', 1.6)
    # coat front edge / opening line
    for y in range(14, 33):
        f.px(11 if y < 22 else 12, y, '#1E2329') if y % 3 == 0 else None
    # arm (hanging, slightly forward) + hand
    f.poly([(6.6, 11.0), (10.2, 11.0), (10.6, 25.6), (7.4, 25.6)], 'coat_f', 1.2, 0.8)
    f.ell(9.1, 26.9, 1.6, 1.5, 'skin', 0.6, 1.0)
    # scarf / raised collar
    f.poly([(5.6, 8.6), (10.6, 8.4), (11.4, 11.4), (5.2, 11.6)], 'scarf_f', 0.9, 0.6)
    # head
    f.ell(8.9, 5.2, 3.0, 3.3, 'skin', 1.0, 0.5)
    f.px(12, 5, '#94735C')          # nose
    f.px(10, 4, '#1B1520')          # eye
    f.px(7, 5, '#7A5E4E')           # ear
    # flat cap with brim to the front
    f.poly([(5.2, 1.2), (8.8, 0.2), (11.6, 1.0), (12.4, 2.4), (14.2, 3.2), (13.6, 3.9), (5.4, 3.7)], 'cap_f',
           0.8, 0.8)
    return f


def fig_mother():
    f = Fig(18, 43)
    f.poly([(6.8, 31), (8.8, 31), (8.6, 41), (6.9, 41)], 'stock', 0.6)
    f.poly([(8.6, 31), (10.6, 31), (10.9, 41), (9.0, 41)], 'stock', 0.7, 0.2)
    f.poly([(6.0, 40.8), (9.0, 40.8), (9.2, 43), (6.0, 43)], 'shoe', 0.4)
    f.poly([(8.8, 40.8), (12.0, 41.2), (12.2, 43), (8.8, 43)], 'shoe', 0.4, 0.2)
    # coat with belt, flaring to below the knee
    f.poly([(5.0, 10.4), (10.6, 10.2), (11.4, 13), (11.2, 20), (12.8, 31.4), (4.0, 31.4), (4.8, 20),
            (4.4, 13)], 'coat_m', 1.6)
    f.rect(4.6, 19.4, 11.6, 20.6, 'leath', 0.3, 1.2)
    # arm hanging, hand holding a handbag in front of the coat
    f.poly([(7.0, 11.2), (10.2, 11.0), (10.8, 23.6), (7.8, 23.8)], 'coat_m', 1.1, 0.8)
    f.ell(9.6, 24.6, 1.4, 1.3, 'skin', 0.5, 1.0)
    f.poly([(7.6, 25.0), (12.4, 25.0), (12.6, 29.4), (7.4, 29.4)], 'bag', 0.7, 1.3)
    f.px(9, 24, '#1B1520')
    f.px(10, 24, '#1B1520')
    # head with headscarf tied under the chin
    f.ell(9.2, 5.6, 2.8, 3.1, 'skin', 1.0, 0.5)
    f.px(12, 5, '#94735C')
    f.px(10, 5, '#1B1520')
    f.poly([(5.6, 2.8), (8.0, 1.0), (10.8, 1.2), (12.0, 3.0), (11.0, 3.4), (8.0, 3.2), (7.6, 7.6),
            (8.6, 9.6), (6.8, 10.2), (5.2, 7.0)], 'scarf_m', 0.9, 0.7)
    f.px(9, 9, '#3E5D55')
    return f


def fig_child():
    f = Fig(14, 30)
    f.poly([(5.0, 21), (7.0, 21), (6.9, 28), (5.1, 28)], 'trou', 0.6)
    f.poly([(6.6, 21), (8.6, 21), (8.9, 28), (7.0, 28)], 'trou', 0.7, 0.2)
    f.poly([(4.4, 27.6), (7.2, 27.6), (7.3, 30), (4.2, 30)], 'shoe', 0.4)
    f.poly([(6.8, 27.8), (9.6, 28.0), (9.8, 30), (6.8, 30)], 'shoe', 0.4, 0.2)
    # short coat
    f.poly([(3.8, 8.6), (8.8, 8.4), (9.6, 11), (9.8, 21.6), (3.2, 21.6), (3.6, 11)], 'coat_c', 1.4)
    # arm hanging, clutching a small bag
    f.poly([(5.4, 9.4), (8.0, 9.4), (8.4, 17.0), (5.8, 17.0)], 'coat_c', 1.0, 0.8)
    f.ell(7.2, 17.8, 1.2, 1.1, 'skin', 0.5, 1.0)
    f.poly([(5.8, 18.4), (9.4, 18.4), (9.6, 21.4), (5.6, 21.4)], 'case_b', 0.6, 1.2)
    # big head (child proportions), knit cap with pompom
    f.ell(6.9, 4.9, 3.0, 3.1, 'skin', 1.0, 0.5)
    f.px(10, 5, '#94735C')
    f.px(8, 4, '#1B1520')
    f.poly([(3.8, 3.8), (4.6, 1.6), (7.0, 0.8), (9.4, 1.6), (10.2, 3.4), (3.8, 4.4)], 'cap_c', 0.8, 0.7)
    f.ell(6.4, 0.9, 1.1, 0.9, 'cap_c', 0.5, 1.0)
    # scarf
    f.rect(4.2, 7.6, 9.2, 9.0, 'scarf_m', 0.5, 0.9)
    return f


def fig_guard():
    f = Fig(20, 47)
    f.poly([(7.0, 32), (10.0, 32), (10.0, 44.4), (7.2, 44.4)], 'coat_g', 0.8)
    f.poly([(9.2, 32), (12.0, 32), (12.0, 44.4), (9.6, 44.4)], 'coat_g', 0.9, 0.2)
    # boots
    f.poly([(6.6, 38.0), (10.0, 38.0), (10.2, 47), (6.2, 47)], 'leath', 0.6, 0.4)
    f.poly([(9.4, 38.0), (12.2, 38.0), (13.8, 45.6), (13.8, 47), (9.4, 47)], 'leath', 0.6, 0.6)
    # long greatcoat
    f.poly([(5.4, 10.6), (12.4, 10.4), (13.2, 13), (13.0, 22), (14.0, 37.0), (4.8, 37.0), (5.2, 22),
            (4.8, 13)], 'coat_g', 1.7)
    f.rect(5.0, 21.0, 13.2, 22.4, 'leath', 0.3, 1.2)
    f.px(12, 21, '#7C8690')          # buckle
    # rifle slung on the back shoulder (vertical, barrel above the shoulder)
    f.poly([(4.0, 4.0), (5.0, 4.0), (5.0, 28.0), (4.0, 28.0)], 'rifle', 0.3, 1.5)
    f.poly([(3.4, 22.0), (5.4, 22.0), (5.6, 31.0), (3.2, 31.0)], 'rifle', 0.4, 1.5)
    f.poly([(5.0, 11.0), (12.0, 21.0), (11.2, 21.8), (4.6, 12.2)], 'leath', 0.2, 1.6)   # sling strap
    # arm hanging straight
    f.poly([(8.0, 11.4), (11.4, 11.4), (11.8, 26.0), (8.6, 26.0)], 'coat_g', 1.2, 0.9)
    f.ell(10.3, 27.2, 1.5, 1.4, 'skin', 0.5, 1.0)
    # head + peaked cap (high crown, visor to the front)
    f.ell(10.0, 6.4, 2.9, 3.2, 'skin', 1.0, 0.5)
    f.px(13, 6, '#94735C')
    f.px(11, 6, '#1B1520')
    f.poly([(6.4, 1.4), (12.6, 0.4), (13.4, 3.6), (6.8, 4.2)], 'cap_g', 0.8, 0.7)
    f.poly([(11.6, 3.4), (15.0, 4.0), (14.6, 4.9), (11.6, 4.6)], 'leath', 0.3, 1.0)
    # collar
    f.poly([(7.2, 9.0), (12.4, 9.0), (12.8, 11.4), (6.8, 11.6)], 'coat_g', 0.7, 0.9)
    return f


def crowd_figure(variant: int, size: str):
    """Tiny far figures: s = 6-8 px (plaza, 200-600 m), m = 12-14 px (end of the street)."""
    rng = np.random.default_rng(100 + variant + (50 if size == 'm' else 0))
    h = int(rng.integers(6, 8)) if size == 's' else int(rng.integers(12, 15))
    w = 5 if size == 's' else 8
    img = np.zeros((h, w, 4), np.uint8)
    dark = H('#1B1520') if size == 's' else H('#211623')
    mid = H('#342F37') if size == 's' else H('#443B43')
    cx = w // 2
    if size == 's':
        img[0:2, cx] = dark                      # head
        img[2:h - 2, cx - 1:cx + 1] = dark       # body
        img[2:h - 3, cx + 1] = mid if variant % 2 else dark
        img[h - 2:h, cx - 1] = dark              # legs
        img[h - 2:h, cx + (1 if variant % 3 else 0)] = dark
        if variant in (3, 6):                    # hat
            img[0, cx - 1:cx + 2] = dark
    else:
        hy = 0
        img[hy:hy + 3, cx - 1:cx + 1] = dark
        if variant % 2 == 0:
            img[hy, cx - 2:cx + 2] = dark        # hat brim
        img[3:h - 3, cx - 2:cx + 2] = dark
        img[4:h - 4, cx + 1] = mid
        img[h - 3:h, cx - 1] = dark
        img[h - 3:h, cx + 1] = dark
        if variant == 1:
            img[6:9, cx + 2] = dark              # carried bag
    return img


# ============================================================================ props
def prop_suitcase(name, w, h, mat, seed):
    f = Fig(w + 2, h + 4)
    f.rect(1, 3, w + 1, h + 4, mat, 1.0)
    f.rect(1, 3 + h // 2, w + 1, 4 + h // 2, 'strap', 0.2, 0.6)
    f.rect(w // 2 - 1, 1, w // 2 + 3, 3, 'strap', 0.3, 0.2)        # handle
    f.px(1, 3, '#7C8690')
    f.px(w, 3, '#7C8690')
    f.px(1, h + 3, '#5F6973')
    f.px(w, h + 3, '#5F6973')
    return f


def make_people():
    fig_father().save(out('people', 'berlin_father'))
    fig_mother().save(out('people', 'berlin_mother'))
    fig_child().save(out('people', 'berlin_child'))
    fig_guard().save(out('people', 'guard'))
    for size in ('s', 'm'):
        for v in range(8):
            img = crowd_figure(v, size)
            save_rgba(img, out('people', 'crowd_%s%d.png' % (size, v)))
    prop_suitcase('suitcase_a', 16, 10, 'case_a', 1).save(out('props', 'suitcase_a'))
    prop_suitcase('suitcase_b', 13, 8, 'case_b', 2).save(out('props', 'suitcase_b'))
    b = Fig(14, 10)
    b.ell(7, 5.6, 6.2, 4.2, 'cloth', 1.2)
    b.rect(6, 1, 8, 10, 'strap', 0.1, 1.0)
    b.px(7, 0, '#1B1520')
    b.save(out('props', 'bundle'))


# ============================================================================ textures
def make_door():
    w, h = 40, 78
    L = pg.Layer(w, h)
    wood = [H(c) for c in ['#2A2130', '#4A3A35', '#5F4A40', '#7A5E4E']]
    L.rect(0, 0, w, h, wood[1])
    # two leaves with raised panels
    for lx in (0, w // 2):
        L.rect(lx + 2, 2, w // 2 - 4, 30, wood[2])
        L.rect(lx + 3, 3, w // 2 - 6, 28, wood[1])
        L.rect(lx + 2, 36, w // 2 - 4, 36, wood[2])
        L.rect(lx + 3, 37, w // 2 - 6, 34, wood[1])
        L.vline(lx + 2, 2, 30, wood[3])
        L.vline(lx + 2, 36, 36, wood[3])
        L.hline(lx + 2, 2, w // 2 - 4, wood[3])
        L.hline(lx + 2, 36, w // 2 - 4, wood[3])
    L.vline(w // 2, 0, h, wood[0])
    L.vline(0, 0, h, wood[0])
    L.vline(w - 1, 0, h, wood[0])
    L.hline(0, 0, w, wood[0])
    # handles
    L.rect(w // 2 - 3, 38, 2, 1, H('#A3ACB4'))
    L.rect(w // 2 + 1, 38, 2, 1, H('#A3ACB4'))
    # notice pinned on the left leaf (unreadable lines)
    L.rect(5, 12, 11, 14, H('#D2CCCB'))
    L.rect(5, 12, 11, 1, H('#ECE6E0'))
    for yy in range(15, 25, 2):
        L.hline(6, yy, 8 if yy % 4 else 6, H('#8F8A92'))
    L.rect(6, 13, 4, 1, H('#454E58'))
    L.px(10, 12, H('#1B1520'))
    # official seal strip, diagonal across both leaves and the gap
    for i in range(-2, 46):
        x = 3 + i * 0.75
        y = 26 + i
        for k in range(3):
            xx = int(round(x)) + k
            if 0 <= xx < w and 0 <= y < h:
                L.px(xx, y, H('#ECE6E0') if k < 2 else H('#B2ACB0'))
    # round stamp over the gap (terracotta ink ring)
    cx, cy = w // 2, 47
    for yy in range(cy - 3, cy + 4):
        for xx in range(cx - 3, cx + 4):
            d = math.hypot(xx - cx, yy - cy)
            if 2.2 <= d <= 3.4:
                L.px(xx, yy, H('#8D5542'))
    L.px(cx, cy, H('#8D5542'))
    # snow drift at the threshold
    for x in range(w):
        dh = 2 + int(2 * math.sin(x * 0.35) ** 2)
        for k in range(dh):
            L.px(x, h - 1 - k, H('#D2CCCB') if k < dh - 1 else H('#ECE6E0'))
    save_rgba(L.c, out('textures', 'door_sealed.png'))


def make_drawing():
    w, h = 320, 224
    L = pg.Layer(w, h)
    paper = H('#D2CCCB')
    L.rect(0, 0, w, h, paper)
    # subtle paper tone variation
    nz = pg.value_noise(w, h, 24, seed=9)
    m = nz > 0.62
    L.c[m] = H('#B2ACB0')
    L.c[nz < 0.3] = H('#ECE6E0')
    ink = H('#454E58')
    ink2 = H('#7C8690')
    # border and title block
    L.rect(6, 6, w - 12, 1, ink)
    L.rect(6, h - 7, w - 12, 1, ink)
    L.rect(6, 6, 1, h - 12, ink)
    L.rect(w - 7, 6, 1, h - 12, ink)
    L.rect(w - 92, h - 40, 85, 1, ink)
    L.rect(w - 92, h - 40, 1, 33, ink)
    for yy in range(h - 34, h - 10, 6):
        L.hline(w - 86, yy, 60 + (yy % 3) * 6, ink2)
    # elevation of the hall: podium, pilasters, portico, drum, dome, lantern
    base = 168
    L.hline(20, base, 220, ink)
    L.rect(40, base - 40, 180, 1, ink)
    L.rect(40, base - 40, 1, 40, ink)
    L.rect(219, base - 40, 1, 40, ink)
    for x in range(46, 216, 8):
        L.vline(x, base - 38, 36, ink2)
    L.rect(36, base - 46, 188, 1, ink)
    L.rect(36, base - 44, 188, 1, ink2)
    for x in range(98, 164, 7):
        L.rect(x, base - 36, 3, 36, ink)
    cx = 130
    L.rect(cx - 62, base - 60, 124, 1, ink)
    L.rect(cx - 62, base - 60, 1, 14, ink)
    L.rect(cx + 61, base - 60, 1, 14, ink)
    for x in range(cx - 58, cx + 60, 6):
        L.vline(x, base - 58, 12, ink2)
    # dome profile
    prev = None
    for i in range(0, 91, 2):
        th = math.radians(i)
        x = cx + 60 * math.cos(th)
        y = base - 61 - 66 * math.sin(th)
        x2 = cx - 60 * math.cos(th)
        if prev:
            L.line(prev[0], prev[1], x, y, ink)
            L.line(prev[2], prev[1], x2, y, ink)
        prev = (x, y, x2)
    for k in range(-5, 6):
        a = k / 6.0
        pts = []
        for i in range(0, 91, 3):
            th = math.radians(i)
            pts.append((cx + 60 * math.cos(th) * a, base - 61 - 66 * math.sin(th)))
        L.polyline(pts, ink2)
    L.rect(cx - 8, base - 140, 16, 13, ink)
    L.rect(cx - 7, base - 139, 14, 11, paper)
    for x in range(cx - 6, cx + 7, 3):
        L.vline(x, base - 138, 9, ink2)
    L.line(cx, base - 148, cx, base - 140, ink)
    # dimension lines
    L.hline(40, base + 14, 180, ink2)
    for x in (40, 219):
        L.vline(x, base + 10, 8, ink2)
    L.vline(250, base - 150, 150, ink2)
    for y in (base - 150, base):
        L.hline(246, y, 8, ink2)
    # plan inset (floor plan square with the hidden corridor)
    L.rect(256, 30, 52, 1, ink)
    L.rect(256, 81, 52, 1, ink)
    L.rect(256, 30, 1, 52, ink)
    L.rect(307, 30, 1, 52, ink)
    L.ellipse(282, 56, 18, 18, ink2)
    L.ellipse(282, 56, 17, 17, paper)
    # the omitted service corridor (dashed) and the red annotation ring (C-17, no lettering)
    red = H('#8D5542')
    for x in range(232, 300, 4):
        L.hline(x, 92, 2, red)
    L.line(300, 92, 300, 76, red)
    for yy in range(-7, 8):
        for xx in range(-11, 12):
            d = math.hypot(xx / 11.0, yy / 7.0)
            if 0.86 <= d <= 1.0:
                L.px(272 + xx, 100 + yy, red)
    save_rgba(L.c, out('textures', 'drawing.png'))


def make_banner():
    w, h = 16, 64
    L = pg.Layer(w, h)
    cols = [H(c) for c in ['#1B1520', '#1E2329', '#2F363F', '#454E58']]
    L.rect(0, 0, w, h, cols[1])
    # vertical folds (cloth hangs limp, frozen)
    for x in (3, 8, 12):
        L.vline(x, 0, h, cols[0])
        L.vline(x + 1, 0, h, cols[2])
    L.vline(0, 0, h, cols[3])
    L.vline(w - 1, 0, h, cols[0])
    L.hline(0, 0, w, cols[3])
    # the fictional Reichssiegel: small black disc with a white pillar, near the top
    cx, cy, r = 8, 12, 4.6
    for yy in range(h):
        for xx in range(w):
            if math.hypot(xx + 0.5 - cx, yy + 0.5 - cy) <= r:
                L.px(xx, yy, H('#120C14'))
    L.rect(7, 9, 2, 7, H('#ECE6E0'))
    L.rect(6, 15, 4, 1, H('#ECE6E0'))
    L.px(7, 8, H('#ECE6E0'))
    # frayed bottom edge with snow crust
    for x in range(w):
        cut = 2 if (x * 7) % 5 < 2 else 0
        for k in range(cut):
            L.c[h - 1 - k, x] = 0
    L.hline(0, 1, w, H('#8F8A92'))
    save_rgba(L.c, out('textures', 'banner.png'))


def make_posters():
    w, h = 24, 32
    L = pg.Layer(w, h)
    L.rect(0, 0, w, h, H('#4A3A35'))
    L.rect(1, 1, w - 2, h - 2, H('#5F4A40'))
    sheets = [(2, 2, 9, 12, '#D2CCCB'), (12, 3, 10, 8, '#B2ACB0'), (3, 16, 8, 10, '#ECE6E0'),
              (13, 13, 9, 14, '#C9A585')]
    for x, y, sw, sh, col in sheets:
        L.rect(x, y, sw, sh, H(col))
        for yy in range(y + 2, y + sh - 1, 2):
            L.hline(x + 1, yy, sw - 2 - (yy % 3), H('#8F8A92'))
        L.px(x + sw // 2, y, H('#1B1520'))
    L.rect(13, 13, 9, 3, H('#120C14'))       # official header bar on the newest notice
    save_rgba(L.c, out('textures', 'posters.png'))


def contact_sheet():
    """Debug overview of the people & props at 6x (written to _preview, ignored by Godot)."""
    names = ['people/berlin_father', 'people/berlin_mother', 'people/berlin_child', 'people/guard',
             'props/suitcase_a', 'props/suitcase_b', 'props/bundle']
    ims = [Image.open(out(n + '.png')) for n in names]
    W = sum(i.width for i in ims) + 4 * len(ims) + 4
    Hh = max(i.height for i in ims) + 8
    sheet = Image.new('RGBA', (W, Hh), (110, 106, 115, 255))
    x = 4
    for im in ims:
        sheet.paste(im, (x, Hh - 4 - im.height), im)
        x += im.width + 4
    os.makedirs(os.path.join(ROOT, '_preview'), exist_ok=True)
    open(out('_preview', '.gdignore'), 'a').close()
    pg.upscale(sheet, 6).save(out('_preview', 'people_sheet_x6.png'))


def main():
    os.makedirs(ROOT, exist_ok=True)
    make_sky()
    make_fog()
    make_smoke()
    make_people()
    make_door()
    make_drawing()
    make_banner()
    make_posters()
    contact_sheet()
    write_import_settings()
    print('great hall assets written to', ROOT)



# ============================================================================ Godot import settings
MIPMAPPED = {'drawing.png', 'banner.png'}


def write_import_settings():
    """Pin lossless, non-VRAM import for every texture of this area (pixel art must never be block
    compressed; Godot's 3D-usage detection would otherwise switch them to VRAM compression)."""
    for dp, dn, fn in os.walk(ROOT):
        if '_preview' in dp:
            continue
        for f in fn:
            if not f.endswith('.png'):
                continue
            p = os.path.join(dp, f)
            imp = p + '.import'
            mip = 'true' if f in MIPMAPPED else 'false'
            body = ('[remap]\n\nimporter="texture"\ntype="CompressedTexture2D"\n\n[params]\n\n'
                    'compress/mode=0\ncompress/high_quality=false\ncompress/lossy_quality=0.7\n'
                    'compress/hdr_compression=1\ncompress/normal_map=2\ncompress/channel_pack=0\n'
                    'mipmaps/generate=%s\nmipmaps/limit=-1\nroughness/mode=0\nroughness/src_normal=""\n'
                    'process/fix_alpha_border=true\nprocess/premult_alpha=false\n'
                    'process/normal_map_invert_y=false\nprocess/hdr_as_srgb=false\n'
                    'process/hdr_clamp_exposure=false\nprocess/size_limit=0\ndetect_3d/compress_to=0\n' % mip)
            if os.path.exists(imp):
                old = open(imp, encoding='utf-8').read()
                if 'detect_3d/compress_to=0' in old and ('mipmaps/generate=%s' % mip) in old \
                        and 'compress/mode=0' in old:
                    continue
                # keep uid/path lines Godot generated, replace params
                head = old.split('[params]')[0]
                body = head + body.split('\n\n[params]', 1)[1].join(['', '']) if False else \
                    head + '[params]' + body.split('[params]', 1)[1]
            with open(imp, 'w', encoding='utf-8') as fh:
                fh.write(body)



if __name__ == '__main__':
    if '--imports' in sys.argv:
        write_import_settings()
    else:
        main()
