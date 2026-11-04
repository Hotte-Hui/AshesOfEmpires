"""gen_great_hall_symbols -- regime iconography for the Great Hall reveal (L_M1_HallReveal).

Owner: hall (great_hall_3d).  Original, deterministic pixel art on the berlin palette (pg.PALETTES['berlin']).
TECHNICAL_ARCHITECTURE section 12.4: every image that shows a real regime insignia exists twice --
    <name>.png       neutral / fictional emblem (the Reichssiegel: white pillar in a black disc, grey-black cloth)
    <name>_hist.png  the same object with the real insignia (red cloth, white disc, black swastika on point)
Loaders resolve the path with Symbols.pick().  The insignia are in-world iconography of the regime inside a
critical narrative (the evicted family is the focus of the shot); they are never UI, reward or decoration.

Outputs (assets/architecture/great_hall/symbols/):
  banner_portico(.png|_hist.png)   10x36  giant vertical banners hung on the portico (d ~ 950 m, ~1 texel/px)
  flag_street(.png|_hist.png)      30x90  hanging banners on the tenement facades (d ~ 30 m, ~1 texel/px)
  flag_pole(.png|_hist.png)        16x44  flags on the plaza masts (mipmapped, 120-600 m)
  eagle_portico(.png|_hist.png)    +_n   free-standing stone eagle on the portico attic, claws on a wreath
                                         (hist: swastika in the wreath; neutral: the Reichssiegel pillar)
  eagle_lantern.png (+_n)               the crowning bronze eagle above the globe on the dome lantern -- the
                                         real 1939 design of Speer's "Grosse Halle" (no swastika -> no variant)
Run:  py -3 -P tools/pixelgen/gen_great_hall_symbols.py
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
                                     'assets', 'architecture', 'great_hall', 'symbols'))
PREV = os.path.normpath(os.path.join(ROOT, '..', '_preview'))
H = pg.hx

NIGHT = ['#120C14', '#1B1520', '#211623', '#2A2130']
VIOLET = ['#25202B', '#342F37', '#443B43', '#57494D']
STONE = ['#4A3A35', '#5F4A40', '#7A5E4E', '#94735C', '#AE8A6C', '#C9A585']
OCHRE = ['#5F4530', '#735145', '#8D5542', '#AF6C47', '#D07744', '#E5945A']
STEEL = ['#1E2329', '#2F363F', '#454E58', '#5F6973', '#7C8690', '#A3ACB4']
PATINA = ['#1E2E2C', '#2C4440', '#3E5D55', '#56776A', '#73927F']
SNOW = ['#6E6A73', '#8F8A92', '#B2ACB0', '#D2CCCB', '#ECE6E0']

# cloth ramps (dark -> light): the real flag red is pushed into the palette's terracotta ramp (no saturated red
# exists in the berlin palette; the banners stay part of the dusk instead of glowing like a reward)
RED = [OCHRE[0], OCHRE[1], OCHRE[2], OCHRE[3]]
GREYBLACK = [NIGHT[1], STEEL[0], STEEL[1], STEEL[2]]
WHITE = [SNOW[2], SNOW[3], SNOW[4]]
BLACK = NIGHT[0]


def out(*parts):
    p = os.path.join(ROOT, *parts)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    return p


def save_rgba(arr, path):
    Image.fromarray(np.asarray(arr, np.uint8), 'RGBA').save(path)


# ============================================================================ the two emblems
# Upright right-facing swastika on its own 5x5 unit grid (row 0 = top).  Rotated 45 deg it stands on a point
# as on the regime's flag: the NE arm hooks to the SE, the NW arm to the NE, etc.
_SW = ["X.XXX",
       "X.X..",
       "XXXXX",
       "..X.X",
       "XXX.X"]


def swastika_mask(size: int, sub: int = 8, thr: float = 0.42) -> np.ndarray:
    """Rasterise the swastika rotated 45 deg into a size x size mask (supersampled, thresholded).
    The diamond of the rotated 5x5 unit square fits exactly into the size x size box."""
    unit = size / (5.0 * math.sqrt(2.0))
    acc = np.zeros((size, size), np.float32)
    c = size / 2.0
    ca = math.cos(math.radians(45.0))
    for sy in range(sub):
        for sx in range(sub):
            yy, xx = np.mgrid[0:size, 0:size].astype(np.float32)
            px = xx + (sx + 0.5) / sub - c
            py = yy + (sy + 0.5) / sub - c
            # rotate back by -45 deg into the upright frame
            ux = (px * ca + py * ca) / unit + 2.5
            uy = (-px * ca + py * ca) / unit + 2.5
            ix = np.floor(ux).astype(int)
            iy = np.floor(uy).astype(int)
            ok = (ix >= 0) & (ix < 5) & (iy >= 0) & (iy < 5)
            v = np.zeros_like(px, dtype=bool)
            for r in range(5):
                for q in range(5):
                    if _SW[r][q] == 'X':
                        v |= ok & (iy == r) & (ix == q)
            acc += v
    return (acc / (sub * sub)) >= thr


# Threshold per size, chosen by eye from rasterisations at 10x (below ~11 px the hooks only survive with the
# right coverage threshold; the result reads as the regime's on-point swastika, not as a blob or a cross).
_SW_THR = {7: 0.46, 8: 0.46, 9: 0.5, 10: 0.46, 11: 0.54, 12: 0.46}


def swastika(size: int) -> np.ndarray:
    return swastika_mask(size, sub=12, thr=_SW_THR.get(size, 0.46))


def reichssiegel(size: int) -> tuple[np.ndarray, np.ndarray]:
    """Fictional state seal (ART_DIRECTION section 4): a white pillar/obelisk standing in a black disc.
    Obelisk = pyramidion tip, slightly tapering shaft, two-step plinth (reads as a monument, not as a digit).
    Returns (disc mask, pillar mask) for a size x size box."""
    yy, xx = np.mgrid[0:size, 0:size].astype(np.float32)
    c = (size - 1) / 2.0
    disc = (xx - c) ** 2 + (yy - c) ** 2 <= (size / 2.0 - 0.15) ** 2
    pillar = np.zeros((size, size), bool)
    top = int(round(size * 0.14))
    bot = int(round(size * 0.70))           # first plinth row
    shaft_bot = max(1, int(round(size * 0.17)))
    shaft_top = max(1, shaft_bot - (1 if size >= 13 else 0))
    for y in range(top, bot):
        k = (y - top) / max(1, bot - top - 1)
        w = shaft_top if k < 0.5 else shaft_bot
        if y == top:
            w = 1
        x0 = int(round(c - (w - 1) / 2.0))
        pillar[y, x0:x0 + w] = True
    steps = [shaft_bot + 2, shaft_bot + 4] if size >= 11 else [shaft_bot + 2]
    y = bot
    for sw in steps:
        x0 = int(round(c - (sw - 1) / 2.0))
        hgt = max(1, size // 12)
        pillar[y:y + hgt, x0:x0 + sw] = True
        y += hgt
    return disc, pillar & disc


# ============================================================================ cloth
def cloth(w: int, h: int, ramp, folds, seed: int, hem: int = 2) -> np.ndarray:
    """Limp, frozen cloth: vertical folds (light crest, dark trough), hem at the bottom, rod pocket at the top."""
    img = np.zeros((h, w, 4), np.uint8)
    rng = np.random.default_rng(seed)
    tone = np.full((h, w), 1.0, np.float32)
    for fx, depth in folds:
        for x in range(w):
            d = x - fx
            tone[:, x] += depth * math.exp(-(d * d) / 1.6) * (1.0 if d >= 0 else -0.6)
    # a slow sideways drift of the folds downwards (cloth does not hang ruler-straight)
    for y in range(h):
        sh = int(round(math.sin(y / max(8.0, h / 3.0) + seed) * 0.6))
        tone[y] = np.roll(tone[y], sh)
    tone[:, 0] -= 0.7
    tone[:, -1] -= 0.9
    cols = np.stack([H(c) for c in ramp])
    idx = np.clip(np.round(tone).astype(int), 0, len(ramp) - 1)
    img[:] = cols[idx]
    # rod pocket and hem
    img[0, :] = H(ramp[-1])
    img[1, :] = H(ramp[0])
    for k in range(hem):
        img[h - 1 - k, :] = H(ramp[max(0, 1 - k)])
    # frayed, frozen lower corners
    for x in range(w):
        if rng.random() < 0.18:
            img[h - 1, x, 3] = 0
    return img


def stamp(img: np.ndarray, mask: np.ndarray, x0: int, y0: int, col) -> None:
    h, w = mask.shape
    sub = img[y0:y0 + h, x0:x0 + w]
    sub[mask] = H(col) if isinstance(col, str) else col


def disc_mask(d: int) -> np.ndarray:
    yy, xx = np.mgrid[0:d, 0:d].astype(np.float32)
    c = (d - 1) / 2.0
    return (xx - c) ** 2 + (yy - c) ** 2 <= (d / 2.0 - 0.2) ** 2


def banner(w: int, h: int, cy: int, disc_d: int, sym: int, hist: bool, folds, seed: int) -> np.ndarray:
    """Vertical banner.  hist: red cloth, white disc, black swastika on point.
    neutral: grey-black cloth with the Reichssiegel (black disc with a white pillar) on a pale ring."""
    if hist:
        img = cloth(w, h, RED, folds, seed)
        x0 = (w - disc_d) // 2
        y0 = cy - disc_d // 2
        dm = disc_mask(disc_d)
        stamp(img, dm, x0, y0, WHITE[1])
        # disc shading: the folds still read through the white (lower-right shade, upper-left light)
        yy, xx = np.mgrid[0:disc_d, 0:disc_d]
        shade = dm & ((xx + yy) > disc_d * 1.25)
        stamp(img, shade, x0, y0, WHITE[0])
        lit = dm & ((xx + yy) < disc_d * 0.55)
        stamp(img, lit, x0, y0, WHITE[2])
        sm = swastika(sym)
        stamp(img, sm, x0 + (disc_d - sym) // 2, y0 + (disc_d - sym) // 2, BLACK)
    else:
        img = cloth(w, h, GREYBLACK, folds, seed)
        x0 = (w - disc_d) // 2
        y0 = cy - disc_d // 2
        ring = disc_mask(disc_d)
        stamp(img, ring, x0, y0, SNOW[1])
        inner = disc_d - 2 if disc_d < 14 else disc_d - 4
        disc, pillar = reichssiegel(inner)
        o = (disc_d - inner) // 2
        stamp(img, disc, x0 + o, y0 + o, BLACK)
        stamp(img, pillar, x0 + o, y0 + o, WHITE[1])
        # two thin pale border stripes (state banner, not a party flag)
        for x in (1, w - 2):
            img[3:h - 3, x] = H(STEEL[3])
    return img


# ============================================================================ eagles
class Relief:
    """Small relief rasteriser: polygons into a material map with a per-part height bump, shaded by a
    light from above (floodlit from below at night is done by the engine lights through the normal map)."""

    def __init__(self, w, h):
        self.w, self.h = w, h
        self.mat = np.zeros((h, w), np.int8)          # 0 empty, 1.. material index
        self.hgt = np.zeros((h, w), np.float32)
        self.part = np.zeros((h, w), np.int32)
        self.n = 0

    def _poly(self, pts):
        L = pg.Layer(self.w, self.h)
        m, x0, y0 = L.poly_mask(pts)
        full = np.zeros((self.h, self.w), bool)
        X0, Y0 = max(0, x0), max(0, y0)
        X1, Y1 = min(self.w, x0 + m.shape[1]), min(self.h, y0 + m.shape[0])
        if X1 > X0 and Y1 > Y0:
            full[Y0:Y1, X0:X1] = m[Y0 - y0:Y1 - y0, X0 - x0:X1 - x0]
        return full

    def put(self, mask, mat=1, bump=1.0, z=0.0):
        self.n += 1
        acc = mask.astype(np.float32)
        cur = mask.copy()
        for _ in range(3):
            p = np.pad(cur, 1)
            cur = cur & p[:-2, 1:-1] & p[2:, 1:-1] & p[1:-1, :-2] & p[1:-1, 2:]
            acc += cur
        hh = z + bump * np.sqrt(acc / 3.0)
        self.mat[mask] = mat
        self.hgt[mask] = hh[mask]
        self.part[mask] = self.n

    def poly(self, pts, mat=1, bump=1.0, z=0.0):
        self.put(self._poly(pts), mat, bump, z)

    def ell(self, cx, cy, rx, ry, mat=1, bump=1.0, z=0.0):
        yy, xx = np.mgrid[0:self.h, 0:self.w]
        m = (((xx + 0.5 - cx) / rx) ** 2 + ((yy + 0.5 - cy) / ry) ** 2) <= 1.0
        self.put(m, mat, bump, z)

    def mask_put(self, m, mat=1, bump=0.3, z=0.0):
        self.put(m, mat, bump, z)

    def render(self, ramps: dict, light=(0.0, -0.75, 0.66), outline=None):
        a = self.mat > 0
        hp = np.pad(self.hgt, 1, mode='edge')
        gx = (hp[1:-1, 2:] - hp[1:-1, :-2]) * 0.5
        gy = (hp[2:, 1:-1] - hp[:-2, 1:-1]) * 0.5
        pp = np.pad(self.part, 1, mode='edge')
        seam = ((pp[1:-1, 2:] != self.part) | (pp[2:, 1:-1] != self.part)) & a
        nrm = np.stack([-gx * 2.4, -gy * 2.4, np.ones_like(gx)], -1)
        nrm /= np.linalg.norm(nrm, axis=-1, keepdims=True)
        Lv = np.asarray(light, np.float32)
        Lv /= np.linalg.norm(Lv)
        lam = np.clip((nrm * Lv).sum(-1), 0, 1)
        tone = 0.2 + 0.85 * lam
        tone[seam] -= 0.28
        img = np.zeros((self.h, self.w, 4), np.uint8)
        thr = pg.bayer(self.w, self.h)
        for mi, cols in ramps.items():
            m = self.mat == mi
            if not m.any():
                continue
            s = np.clip(tone, 0, 0.999) * len(cols)
            idx = np.floor(s).astype(int)
            f = s - idx
            idx = idx + ((f > 0.8) & (thr < 0.5))
            idx = np.clip(idx, 0, len(cols) - 1)
            carr = np.stack([H(c) for c in cols])
            img[m] = carr[idx[m]]
        if outline:
            p = np.pad(a, 1)
            edge = a & ~(p[:-2, 1:-1] & p[2:, 1:-1] & p[1:-1, :-2] & p[1:-1, 2:])
            # outline only on the lower/shadow side (selective outline)
            low = edge & ((nrm[..., 1] > 0.05) | (np.pad(a, 1)[2:, 1:-1] == 0))
            img[low] = H(outline)
        nm = np.stack([nrm[..., 0], -nrm[..., 1], nrm[..., 2]], -1)
        nimg = np.clip((nm * 0.5 + 0.5) * 255, 0, 255).astype(np.uint8)
        nimg = np.concatenate([nimg, (a * 255).astype(np.uint8)[..., None]], -1)
        return img, nimg


def _wing(R: Relief, cx: float, side: int, y_sh: float, span: float, rise: float, feathers: int,
          fth: float, mat: int = 1):
    """One stylised wing (Art-Deco state eagle): a covert band from the shoulder to the tip, then `feathers`
    long primaries stacked downwards, each shorter, tips pointing out and slightly down."""
    s = side
    x_in = cx + s * 1.5
    tip = cx + s * span
    # coverts (top band) -- the leading edge rises towards the tip
    R.poly([(x_in, y_sh + 1.0), (x_in + s * 2.0, y_sh - 0.6), (tip, y_sh - rise - 0.6), (tip - s * 0.6,
            y_sh - rise + 1.6), (x_in, y_sh + 3.4)], mat, 0.9, 0.6)
    for k in range(feathers):
        y0 = y_sh + 2.2 + k * fth
        x_end = tip - s * (1.2 + k * (span * 0.14))
        y_end = y0 - rise * (abs(x_end - x_in) / span) + 0.4
        R.poly([(x_in, y0), (x_end + s * 0.3, y_end - 0.4), (x_end + s * 1.2, y_end + fth * 0.6),
                (x_end - s * 0.8, y_end + fth + 0.2), (x_in, y0 + fth + 0.4)], mat, 0.7, 0.3 - k * 0.05)


def eagle_portico(hist: bool):
    """Free-standing state eagle on the portico attic: wings spread level, head turned to the eagle's right
    (viewer's left), claws on an oak wreath.  hist: swastika in the wreath; neutral: the Reichssiegel pillar."""
    w, h = 39, 31
    R = Relief(w, h)
    cx = 19.0
    # wings (behind the body): coverts + 4 stepped primaries, leading edge rising to the tips
    for s in (-1, 1):
        x_in = cx + s * 1.0
        R.poly([(x_in, 6.6), (cx + s * 4.0, 5.4), (cx + s * 18.9, 1.0), (cx + s * 18.9, 3.0),
                (cx + s * 4.0, 8.6), (x_in, 9.0)], 1, 0.9, 0.7)
        for k in range(4):
            y0 = 8.4 + k * 2.0
            tip = 18.6 - k * 2.4
            y_tip = 3.0 + k * 2.2
            R.poly([(x_in, y0), (cx + s * tip, y_tip), (cx + s * (tip + 0.2), y_tip + 1.7),
                    (cx + s * (tip - 1.3), y_tip + 2.3), (x_in, y0 + 2.2)], 1, 0.7, 0.45 - k * 0.08)
    # tail fan (vertical feathers)
    R.poly([(cx - 2.2, 14.6), (cx + 2.2, 14.6), (cx + 3.6, 19.6), (cx - 3.6, 19.6)], 1, 0.8, 0.5)
    # body + chest
    R.ell(cx, 10.6, 3.2, 5.6, 1, 1.4, 1.0)
    # legs / claws gripping the wreath top
    R.poly([(cx - 2.6, 15.0), (cx - 1.0, 15.0), (cx - 1.4, 20.4), (cx - 3.2, 20.4)], 1, 0.4, 1.1)
    R.poly([(cx + 1.0, 15.0), (cx + 2.6, 15.0), (cx + 3.2, 20.4), (cx + 1.4, 20.4)], 1, 0.4, 1.1)
    # neck and head turned to the viewer's left, strong hooked beak
    R.ell(cx - 0.3, 4.9, 2.3, 2.7, 1, 1.0, 1.4)
    R.poly([(cx - 2.2, 3.6), (cx - 4.9, 4.2), (cx - 4.6, 5.9), (cx - 3.4, 5.0), (cx - 2.2, 6.0)], 1, 0.6, 1.8)
    # oak wreath: a ring under the claws, leaves as alternating notches
    wy = 25.0
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    d = np.sqrt((xx + 0.5 - (cx + 0.5)) ** 2 + (yy + 0.5 - wy) ** 2)
    ring = (d <= 5.9) & (d >= 3.9)
    R.mask_put(ring, 2, 0.9, 0.8)
    inner = d < 3.9
    R.mask_put(inner, 3, 0.05, 0.2)
    ramps = {1: [STONE[0], STONE[1], STONE[2], STONE[3], STONE[4], STONE[5]],
             2: [STONE[0], STONE[1], STONE[3], STONE[4]],
             3: [NIGHT[1], NIGHT[2]]}
    img, nimg = R.render(ramps, outline=NIGHT[1])
    ang = np.arctan2(yy + 0.5 - wy, xx + 0.5 - (cx + 0.5))
    notch = ring & (np.floor((ang + math.pi) / (2 * math.pi) * 14).astype(int) % 2 == 0) & (d > 5.0)
    img[notch] = H(STONE[1])
    # the eye: one dark pixel
    img[4, int(cx) - 1] = H(NIGHT[1])
    # emblem inside the wreath
    ex, ey = int(cx + 0.5) - 3, int(wy) - 4
    if hist:
        sm = swastika(7)
        field = inner[ey:ey + 7, ex:ex + 7] & ~sm
        img[ey:ey + 7, ex:ex + 7][field] = H(STONE[3])
        img[ey:ey + 7, ex:ex + 7][sm] = H(BLACK)
    else:
        img[ey:ey + 7, ex:ex + 7][inner[ey:ey + 7, ex:ex + 7]] = H(NIGHT[1])
        # the Reichssiegel pillar: tip, shaft, foot
        px = ex + 3
        img[ey + 1, px] = H(STONE[4])
        img[ey + 2:ey + 5, px] = H(STONE[5])
        img[ey + 5, px - 1:px + 2] = H(STONE[4])
    # pedestal plinth under the wreath (stands on the attic)
    for yy0, cols in ((h - 2, STONE[2]), (h - 1, STONE[1])):
        img[yy0, int(cx) - 6:int(cx) + 8] = H(cols)
        nimg[yy0, int(cx) - 6:int(cx) + 8] = [128, 160, 230, 255]
    return img, nimg


# Hand-drawn crowning eagle (21 x 22): wings raised with spread primaries, head to the viewer's left,
# standing on the globe.  # outline, d dark bronze, m mid, l light edge (sky side), g globe, e equator/meridian
_LANTERN = [
    "#...................#",
    "#d#...............#d#",
    "#dd#.............#dd#",
    ".#dd#...........#dd#.",
    ".#mdd#..##.....#ddm#.",
    "..#mdd##ml#...#ddm#..",
    "..#lmdd#mmd#.#ddml#..",
    "...#lmmdmmmd#dmml#...",
    "....#llmdmmmdmml#....",
    ".....##lmmmmmll##....",
    ".......#mmmmmm#......",
    ".......#dmmmmd#......",
    "........#dmmd#.......",
    ".......#d#dd#d#......",
    "........#gggg#.......",
    "......##ggeggg##.....",
    ".....#gggeggggdg#....",
    ".....#eeeeeeeeee#....",
    ".....#ggggegggdd#....",
    "......#ggdeggdd#.....",
    ".......##ddddd##.....",
    ".........#####.......",
]


def eagle_lantern():
    """The crowning eagle of the dome: wings raised, standing on the globe (Speer's 1939 design put the eagle
    above the globe instead of the swastika).  Dark bronze; reads as a silhouette against the sky."""
    cmap = {'#': NIGHT[0], 'd': NIGHT[2], 'm': PATINA[0], 'l': PATINA[2], 'g': PATINA[1], 'e': NIGHT[2]}
    hgt = {'#': 0.2, 'd': 0.5, 'm': 0.8, 'l': 1.0, 'g': 0.9, 'e': 0.7}
    rows = _LANTERN
    h, w = len(rows), max(len(r) for r in rows)
    img = np.zeros((h, w, 4), np.uint8)
    hf = np.zeros((h, w), np.float32)
    for y, r in enumerate(rows):
        for x, ch in enumerate(r):
            if ch in cmap:
                img[y, x] = H(cmap[ch])
                hf[y, x] = hgt[ch]
    a = img[..., 3] > 0
    hp = np.pad(hf, 1, mode='edge')
    gx = (hp[1:-1, 2:] - hp[1:-1, :-2]) * 0.5
    gy = (hp[2:, 1:-1] - hp[:-2, 1:-1]) * 0.5
    nrm = np.stack([-gx * 2.0, -gy * 2.0, np.ones_like(gx)], -1)
    nrm /= np.linalg.norm(nrm, axis=-1, keepdims=True)
    nm = np.stack([nrm[..., 0], -nrm[..., 1], nrm[..., 2]], -1)
    nimg = np.clip((nm * 0.5 + 0.5) * 255, 0, 255).astype(np.uint8)
    nimg = np.concatenate([nimg, (a * 255).astype(np.uint8)[..., None]], -1)
    return img, nimg


# ============================================================================ preview
def preview(items):
    """Contact sheet at 4x on a dusk-coloured ground (written to _preview, ignored by Godot)."""
    pad = 4
    ims = [Image.fromarray(a, 'RGBA') for a in items]
    W = sum(i.width for i in ims) + pad * (len(ims) + 1)
    Hh = max(i.height for i in ims) + 2 * pad
    sheet = Image.new('RGBA', (W, Hh), (68, 59, 67, 255))
    x = pad
    for im in ims:
        sheet.paste(im, (x, Hh - pad - im.height), im)
        x += im.width + pad
    os.makedirs(PREV, exist_ok=True)
    open(os.path.join(PREV, '.gdignore'), 'a').close()
    pg.upscale(sheet, 4).save(os.path.join(PREV, 'symbols_x4.png'))


def main():
    os.makedirs(ROOT, exist_ok=True)
    made = []
    # portico banners: 10 px wide (one pier gap + overlap), 36 px tall at ~0.9 px/m
    for hist in (False, True):
        b = banner(10, 36, 12, 9, 7, hist, [(3, 0.9), (7, 0.7)], 5)
        save_rgba(b, out('banner_portico%s.png' % ('_hist' if hist else '')))
        made.append(b)
    # street banners on the facades: 30x90 (~1.2 x 3.6 m at 25 px/m)
    for hist in (False, True):
        b = banner(30, 90, 34, 23, 17, hist, [(5, 1.0), (12, 0.8), (19, 1.0), (25, 0.7)], 9)
        save_rgba(b, out('flag_street%s.png' % ('_hist' if hist else '')))
        made.append(b)
    # plaza mast flags
    for hist in (False, True):
        b = banner(16, 44, 15, 13, 11, hist, [(4, 0.8), (9, 0.9), (13, 0.6)], 13)
        save_rgba(b, out('flag_pole%s.png' % ('_hist' if hist else '')))
        made.append(b)
    for hist in (False, True):
        img, nimg = eagle_portico(hist)
        base = out('eagle_portico%s' % ('_hist' if hist else ''))
        save_rgba(img, base + '.png')
        save_rgba(nimg, base + '_n.png')
        made.append(img)
    img, nimg = eagle_lantern()
    save_rgba(img, out('eagle_lantern.png'))
    save_rgba(nimg, out('eagle_lantern_n.png'))
    made.append(img)
    preview(made)
    print('symbols written to', ROOT)


if __name__ == '__main__':
    main()
