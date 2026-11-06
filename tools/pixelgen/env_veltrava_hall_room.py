"""env_veltrava_hall_room -- the main interior layer of L_C3_Hall (walls, glazing, staircase, booths, floor).

Painted in tone space (env_veltrava_hall_kit.TLayer on the 'palais' super-ramps), baked with the scene
lights + volumetric daylight shafts, resolved to palette-pure RGBA, then the polished marble floor gets
a dithered mirror reflection of the lower walls and the props standing on it.
Glass areas are left transparent: the exterior / Grosser Saal parallax layers show through them.
"""
from __future__ import annotations

import math

import numpy as np

import env_veltrava_hall_kit as kit
import env_veltrava_hall_layout as L
import pg

R = kit.palais_ramps()


# =========================================================================== helpers
def noise(w, h, cell, seed, octaves=3):
    return pg.value_noise(w, h, cell, seed, octaves=octaves) - 0.5


def molding(lay, x, y, w, profile, ramp):
    """Horizontal moulding: profile = [(tone, height), ...] rows from top to bottom."""
    for i, (t, hh) in enumerate(profile):
        lay.rect(x, y + i, w, 1, ramp, t, hgt=hh)


def bevel(lay, x, y, w, h, ramp, face, hi=None, lo=None, hgt=0.5):
    lay.rect(x, y, w, h, ramp, face, hgt=hgt)
    if hi is not None:
        lay.rect(x, y, w, 1, ramp, hi, hgt=hgt * 0.8)
        lay.rect(x, y, 1, h, ramp, hi, hgt=hgt * 0.8)
    if lo is not None:
        lay.rect(x, y + h - 1, w, 1, ramp, lo, hgt=hgt * 0.6)
        lay.rect(x + w - 1, y, 1, h, ramp, lo, hgt=hgt * 0.6)


def recess(lay, x, y, w, h, ramp, face, shadow=None, light=None, hgt=-0.3):
    lay.rect(x, y, w, h, ramp, face, hgt=hgt)
    if shadow is not None:
        lay.rect(x, y, w, 1, ramp, shadow, hgt=hgt)
        lay.rect(x, y, 1, h, ramp, shadow, hgt=hgt)
    if light is not None:
        lay.rect(x, y + h - 1, w, 1, ramp, light, hgt=hgt)
        lay.rect(x + w - 1, y + 1, 1, h - 1, ramp, light, hgt=hgt)


def pseudo_text(lay, x, y, w, rows, ramp, tone, seed=0, gap=2, rag=0.35):
    rng = np.random.default_rng(seed)
    for r in range(rows):
        xx = x
        end = x + w - int(rng.random() * w * rag)
        while xx < end:
            wl = int(rng.integers(2, 6))
            lay.hline(xx, y + r * gap, min(wl, end - xx), ramp, tone)
            xx += wl + 1


def frame_box(lay, x, y, w, h, ramp='B', face=3.0, hi=4.6, lo=1.6, hgt=0.6):
    """Picture / plaque frame: 1-2 px moulded border (gilt by default) with a shadow on the wall."""
    lay.rect(x - 2, y - 2, w + 4, h + 4, ramp, face, hgt=hgt)
    lay.rect(x - 2, y - 2, w + 4, 1, ramp, hi, hgt=hgt + 0.05)
    lay.rect(x - 2, y - 2, 1, h + 4, ramp, hi - 0.6, hgt=hgt)
    lay.rect(x - 2, y + h + 1, w + 4, 1, ramp, lo, hgt=hgt - 0.1)
    lay.rect(x + w + 1, y - 2, 1, h + 4, ramp, lo, hgt=hgt - 0.1)
    lay.rect(x + w + 2, y, 1, h + 3, 'W', 2.6)             # drop shadow on the wall
    lay.rect(x, y + h + 2, w + 2, 1, 'W', 2.8)


# Jugendstil ornament stamps ('c' cream relief, 'g' gilt, 'd' shadow, '.' none)
LILY = ['...g...',
        '..ccc..',
        '.cc.cc.',
        'c..c..c',
        '...c...',
        '.d.c.d.',
        'cc.c.cc',
        '.cc.cc.',
        '..ccc..',
        '...c...']
ROSE = ['.ccc.',
        'cgcgc',
        'ccgcc',
        'cgcgc',
        '.ccc.']


def stamp(lay, x, y, pat, cream=('M', 5.0), gilt=('B', 4.0), shadow=('W', 3.0), hgt=0.6, flip=False):
    for yy, row in enumerate(pat):
        if flip:
            row = row[::-1]
        for xx, ch in enumerate(row):
            if ch == 'c':
                lay.px(x + xx, y + yy, cream[0], cream[1], hgt=hgt)
            elif ch == 'g':
                lay.px(x + xx, y + yy, gilt[0], gilt[1], hgt=hgt + 0.1)
            elif ch == 'd':
                lay.px(x + xx, y + yy, shadow[0], shadow[1], hgt=hgt * 0.3)


# =========================================================================== room
class Room:
    def __init__(self):
        self.lay = kit.TLayer(L.WORLD_W, L.WORLD_H, R, 'room')
        self.glass = np.zeros((L.WORLD_H, L.WORLD_W), bool)        # transparent cut-outs
        self.shaft_windows = []    # (mask, x0, y0, strength) daylight sources
        self.lights = []           # baked lights (world coords); some are also exported to Godot
        self.saal_windows = []     # booth far windows (glow sources)
        self.frieze_bottom = L.CEIL + 26

    # ------------------------------------------------------------------ glass helpers
    def cut_glass(self, mask, x0, y0, shaft=0.0):
        self.lay.erase_mask(mask, x0, y0)
        mh, mw = mask.shape
        X0, Y0 = max(0, x0), max(0, y0)
        X1, Y1 = min(L.WORLD_W, x0 + mw), min(L.WORLD_H, y0 + mh)
        self.glass[Y0:Y1, X0:X1] |= mask[Y0 - y0:Y1 - y0, X0 - x0:X1 - x0]
        if shaft > 0:
            self.shaft_windows.append((mask.copy(), x0, y0, shaft))

    def frost(self, x0, y0, w, h, seed, corners=True, rim=True):
        """Frost feathers in the lower corners of a pane (painted ON the glass)."""
        rng = np.random.default_rng(seed)
        lay = self.lay
        for (cx, sgn) in ((x0, 1), (x0 + w - 1, -1)):
            if not corners:
                break
            rad = 5.5 + rng.uniform(-1, 1.5)
            for yy in range(max(y0, int(y0 + h - rad - 2)), y0 + h):
                for xx in range(x0, x0 + w):
                    dx = (xx - cx) * sgn
                    dy = y0 + h - 1 - yy
                    if dx < 0:
                        continue
                    d = math.hypot(dx * 1.15, dy)
                    edge = rad + 1.2 * math.sin(math.atan2(dy, dx + 0.01) * 5 + seed) + rng.normal(0, 0.4)
                    if d < edge:
                        lay.px(xx, yy, 'C', 5.0 if d < edge - 2 else 4.0, hgt=0.05, unlit=True)
                        self.glass[yy, xx] = False
        if rim:
            for xx in range(x0, x0 + w):
                if rng.random() < 0.7:
                    lay.px(xx, y0 + h - 1, 'C', 5.0, unlit=True)
                    self.glass[y0 + h - 1, xx] = False

    # ------------------------------------------------------------------ base wall, ceiling, cornice
    def base(self):
        lay = self.lay
        W, H = L.WORLD_W, L.WORLD_H
        y = np.arange(H, dtype=np.float32)[:, None]
        t = 4.7 + 1.25 * np.clip((y - 40) / 160, 0, 1) ** 0.85 - 0.25 * np.clip((y - 230) / 50, 0, 1)
        t = t + np.zeros((1, W), np.float32) + noise(W, H, 26, 3) * 0.28
        lay.put(np.ones((H, W), bool), 0, 0, 'W', t, hgt=0.0, flat=False)
        # ceiling underside: coffers converging toward each room's centre (seen from below)
        lay.vgrad(0, 0, W, L.CEIL, 'W', 2.2, 3.2, hgt=0.0)
        for (rx0, rx1) in (L.VEST, L.FOYER, L.OFFICE, L.INTERP):
            vp = (rx0 + rx1) / 2
            for bx in range(rx0 + 16, rx1 - 4, 32):
                for yy in range(0, L.CEIL):
                    f = (L.HORIZON - yy) / (L.HORIZON - L.CEIL)
                    xx = int(round(vp + (bx - vp) * f))
                    lay.rect(xx - 2, yy, 5, 1, 'W', 4.0, hgt=0.3)
                    lay.rect(xx + 3, yy, 1, 1, 'W', 1.6, hgt=0.0)
                    lay.rect(xx - 3, yy, 1, 1, 'W', 5.0, hgt=0.15)
            for yy in (3, 7):
                lay.rect(rx0, yy, rx1 - rx0, 1, 'W', 1.8, hgt=0.0)
        # grand cornice (vestibule + foyer): cream stucco with dentils and egg-and-dart
        cy = L.CEIL
        grand = [(1.2, 0.0), (2.4, 0.2), (6.0, 1.0), (5.0, 0.9), (3.2, 0.7), (5.6, 0.95), (6.2, 1.0),
                 (4.4, 0.8), (2.6, 0.5), (5.0, 0.7), (4.6, 0.6), (3.0, 0.45), (5.4, 0.6), (4.8, 0.5),
                 (2.2, 0.2), (3.6, 0.3)]
        plain = [(1.2, 0.0), (2.6, 0.2), (5.0, 0.8), (4.0, 0.7), (2.6, 0.5), (4.6, 0.6), (4.0, 0.5),
                 (2.2, 0.3), (3.4, 0.35), (3.0, 0.3)]
        gx1 = L.PART2[0]
        molding(lay, 0, cy, gx1, grand, 'M')
        molding(lay, gx1, cy, W - gx1, plain, 'W')
        for x in range(0, gx1, 4):                                   # dentils
            lay.rect(x, cy + 7, 2, 2, 'M', 5.6, hgt=0.9)
            lay.rect(x + 2, cy + 7, 2, 2, 'M', 2.6, hgt=0.4)
        for x in range(0, gx1, 6):                                   # egg-and-dart
            lay.rect(x + 1, cy + 11, 3, 2, 'M', 5.8, hgt=0.7)
            lay.px(x + 2, cy + 13, 'M', 4.4, hgt=0.5)
            lay.px(x + 4, cy + 11, 'M', 2.6, hgt=0.3)
            lay.px(x + 4, cy + 12, 'B', 3.0, hgt=0.35)
        # Jugendstil frieze (vestibule + foyer): sage band, cream tendril, lilies and gilt buds
        fy = cy + len(grand)
        fh = 11
        lay.rect(0, fy, gx1, fh, 'W', 6.0, hgt=0.15)
        lay.rect(0, fy, gx1, 1, 'M', 3.0, hgt=0.3)
        lay.rect(0, fy + fh - 1, gx1, 1, 'M', 4.6, hgt=0.35)
        lay.rect(0, fy + fh, gx1, 1, 'W', 3.0, hgt=0.0)
        for x in range(0, gx1):
            ph = 2 * math.pi * x / 32.0
            yv = fy + 5 + int(round(2.2 * math.sin(ph)))
            lay.px(x, yv, 'M', 5.2, hgt=0.6)
            lay.px(x, yv + 1, 'W', 3.6, hgt=0.2)
        for x in range(0, gx1, 32):
            stamp(lay, x + 5, fy + 1, ['.c.', 'cgc', '.c.'])
            stamp(lay, x + 21, fy + 6, ['.c.', 'cgc', '.c.'])
            lay.px(x + 13, fy + 2, 'B', 4.6, hgt=0.7)
            lay.px(x + 29, fy + 8, 'B', 4.6, hgt=0.7)
        # plain band (office + interpreters)
        lay.rect(gx1, cy + len(plain), W - gx1, 4, 'W', 5.2, hgt=0.2)
        lay.rect(gx1, cy + len(plain) + 4, W - gx1, 1, 'W', 3.0, hgt=0.0)
        self.frieze_bottom = fy + fh + 1

    # ------------------------------------------------------------------ wainscots
    def marble_dado(self, x0, x1, top=236, seed=0):
        """Green-marble wainscot (verde antico panels in cream marble frames)."""
        lay = self.lay
        h = L.FLOOR - top
        lay.rect(x0, top, x1 - x0, h, 'M', 4.0, hgt=0.3)
        lay.rect(x0, top, x1 - x0, 1, 'M', 6.2, hgt=0.7)                 # rail
        lay.rect(x0, top + 1, x1 - x0, 2, 'M', 5.0, hgt=0.6)
        lay.rect(x0, top + 3, x1 - x0, 1, 'M', 2.4, hgt=0.2)
        pw = 26
        n = max(1, int((x1 - x0 - 4) // (pw + 5)))
        pw = (x1 - x0 - 4 - (n - 1) * 5) // n
        ox = x0 + 2 + ((x1 - x0 - 4) - (n * pw + (n - 1) * 5)) // 2
        vein = noise(x1 - x0, h, 9, seed + 7, octaves=3)
        for i in range(n):
            xx = ox + i * (pw + 5)
            py0, ph = top + 7, h - 17
            recess(lay, xx, py0, pw, ph, 'M', 3.0, shadow=2.0, light=5.0, hgt=-0.1)
            sub = vein[py0 - top:py0 - top + ph - 2, xx - x0 + 1:xx - x0 + pw - 1]
            t = 3.2 + (np.abs(sub) < 0.045) * 1.6 + (sub > 0.22) * -0.6
            lay.put(np.ones(sub.shape, bool), xx + 1, py0 + 1, 'G', t, hgt=0.05, flat=True)
        lay.rect(x0, L.FLOOR - 7, x1 - x0, 7, 'G', 2.4, hgt=0.4)          # dark marble skirting
        lay.rect(x0, L.FLOOR - 7, x1 - x0, 1, 'M', 5.0, hgt=0.5)

    def wood_dado(self, x0, x1, top=214, panel_w=24):
        """Walnut panelling with raised fielded panels and a moulded rail."""
        lay = self.lay
        h = L.FLOOR - top
        lay.rect(x0, top, x1 - x0, h, 'D', 2.4, hgt=0.2)
        lay.rect(x0, top, x1 - x0, 1, 'D', 5.0, hgt=0.7)
        lay.rect(x0, top + 1, x1 - x0, 2, 'D', 3.8, hgt=0.6)
        lay.rect(x0, top + 3, x1 - x0, 1, 'D', 1.2, hgt=0.1)
        n = max(1, int((x1 - x0 - 4) // (panel_w + 4)))
        pw = (x1 - x0 - 4 - (n - 1) * 4) // n
        ox = x0 + 2 + ((x1 - x0 - 4) - (n * pw + (n - 1) * 4)) // 2
        for i in range(n):
            xx = ox + i * (pw + 4)
            recess(lay, xx, top + 7, pw, h - 17, 'D', 1.8, shadow=1.0, light=3.6, hgt=-0.2)
            bevel(lay, xx + 2, top + 9, pw - 4, h - 21, 'D', 2.8, hi=3.6, lo=1.6, hgt=0.1)
            # grain
            for k in range(xx + 4, xx + pw - 4, 3):
                lay.vline(k, top + 11, h - 25, 'D', 2.4, hgt=0.1)
        lay.rect(x0, L.FLOOR - 6, x1 - x0, 6, 'D', 1.6, hgt=0.3)
        lay.rect(x0, L.FLOOR - 6, x1 - x0, 1, 'D', 3.4, hgt=0.4)

    def stucco_panel(self, x0, y0, x1, y1, ramp='M', tone=4.4, rounded=True, rose=True):
        """Raised stucco frame on the sage wall (with rounded corners and an optional rosette)."""
        lay = self.lay
        w, h = x1 - x0, y1 - y0
        r = 3 if rounded else 0
        for (xx, yy, ww, hh) in ((x0 + r, y0, w - 2 * r, 1), (x0 + r, y1 - 1, w - 2 * r, 1),
                                 (x0, y0 + r, 1, h - 2 * r), (x1 - 1, y0 + r, 1, h - 2 * r)):
            lay.rect(xx, yy, ww, hh, ramp, tone, hgt=0.5)
        lay.rect(x0 + r, y0 + 1, w - 2 * r, 1, 'W', 4.2, hgt=0.1)        # shadow below the top bar
        lay.rect(x0 + 1, y0 + r, 1, h - 2 * r, 'W', 4.4, hgt=0.1)
        lay.rect(x0 + r, y1, w - 2 * r, 1, 'W', 3.6, hgt=0.0)
        lay.rect(x1, y0 + r, 1, h - 2 * r, 'W', 3.8, hgt=0.0)
        if rounded:
            for (cx, cy, sx, sy) in ((x0, y0, 1, 1), (x1 - 1, y0, -1, 1), (x0, y1 - 1, 1, -1),
                                     (x1 - 1, y1 - 1, -1, -1)):
                lay.px(cx + sx * 1, cy + sy * 2, ramp, tone, hgt=0.5)
                lay.px(cx + sx * 2, cy + sy * 1, ramp, tone, hgt=0.5)
                lay.px(cx + sx * 1, cy + sy * 1, ramp, tone + 0.8, hgt=0.55)
        if rose and w > 12:
            stamp(lay, (x0 + x1) // 2 - 2, y0 - 2, ROSE)

    def pilaster(self, x0, x1, top, bot=L.FLOOR, ramp='M', face=4.6, fluted=True, capital=True):
        lay = self.lay
        w = x1 - x0
        lay.rect(x0, top, w, bot - top, ramp, face, hgt=0.6)
        lay.rect(x0, top, 1, bot - top, ramp, face + 1.4, hgt=0.45)
        lay.rect(x1 - 1, top, 1, bot - top, ramp, face - 1.6, hgt=0.45)
        lay.rect(x1, top, 1, bot - top, 'W', 3.0, hgt=0.0)
        if fluted:
            for k in range(x0 + 3, x1 - 2, 3):
                lay.rect(k, top + 10, 1, bot - top - 34, ramp, face - 1.0, hgt=0.5)
        if capital:   # Jugendstil capital: volutes + a hanging garland
            lay.rect(x0 - 3, top - 7, w + 6, 3, ramp, face + 1.0, hgt=0.8)
            lay.rect(x0 - 3, top - 7, w + 6, 1, ramp, face + 2.0, hgt=0.85)
            lay.rect(x0 - 2, top - 4, w + 4, 3, ramp, face - 0.4, hgt=0.7)
            lay.px(x0 - 2, top - 3, 'B', 4.0, hgt=0.9)
            lay.px(x1 + 1, top - 3, 'B', 4.0, hgt=0.9)
            for k in range(w):
                lay.px(x0 + k, top + 1 + int(round(2 * math.sin(math.pi * k / max(1, w - 1)))), 'M',
                       face + 0.8, hgt=0.7)
            lay.rect(x0 - 3, top - 1, w + 6, 1, 'W', 3.0, hgt=0.5)
        lay.rect(x0 - 2, bot - 12, w + 4, 12, ramp, face - 0.6, hgt=0.7)       # base
        lay.rect(x0 - 2, bot - 12, w + 4, 1, ramp, face + 1.2, hgt=0.75)
        lay.rect(x0 - 1, bot - 15, w + 2, 3, ramp, face + 0.2, hgt=0.65)
        lay.rect(x1 + 2, bot - 12, 1, 12, 'W', 2.6, hgt=0.0)

    def sconce(self, cx, y, name, energy=0.55, radius=70, lit=True):
        """Jugendstil wall sconce: brass bracket, tulip glass shade (glowing when lit)."""
        lay = self.lay
        lay.rect(cx - 2, y + 4, 5, 6, 'B', 2.6, hgt=0.7)
        lay.rect(cx - 2, y + 4, 5, 1, 'B', 4.4, hgt=0.75)
        lay.polyline([(cx, y + 4), (cx - 3, y + 1), (cx - 4, y - 3)], 'B', 3.6, hgt=0.8)
        lay.polyline([(cx, y + 4), (cx + 3, y + 1), (cx + 4, y - 3)], 'B', 3.0, hgt=0.8)
        for sx in (cx - 4, cx + 4):
            if lit:
                lay.rect(sx - 2, y - 9, 5, 6, 'A', 4.0, emis=True)
                lay.rect(sx - 1, y - 8, 2, 3, 'A', 5.0, emis=True)
                lay.rect(sx - 2, y - 10, 5, 1, 'A', 3.0, emis=True)
            else:
                lay.rect(sx - 2, y - 9, 5, 6, 'M', 5.0, hgt=0.6)
                lay.rect(sx - 2, y - 10, 5, 1, 'M', 6.0, hgt=0.6)
        if lit:
            self.lights.append({'name': name, 'pos': (cx, y - 6), 'kind': 'warm', 'energy': energy,
                                'radius': radius, 'height': 14})

    # ------------------------------------------------------------------ vestibule
    def vestibule(self):
        lay = self.lay
        x0, x1 = L.VEST
        # end wall poche
        lay.rect(0, 0, 11, L.FLOOR, 'N', 1.0, hgt=0.9)
        lay.rect(10, 0, 1, L.FLOOR, 'W', 3.0, hgt=0.8)
        self.marble_dado(112, L.CLOAK[0] - 4, top=240, seed=1)
        self.marble_dado(L.CLOAK[1] + 4, x1, top=240, seed=2)
        self.entrance()
        # pilasters framing the flag wall and the cloakroom
        self.pilaster(112, 122, self.frieze_bottom + 10)
        self.pilaster(204, 212, self.frieze_bottom + 10, fluted=False)
        self.pilaster(302, 310, self.frieze_bottom + 10, fluted=False)
        # flag wall: stucco panel + bronze plaque + commission arms in relief
        self.stucco_panel(128, 76, 198, 206)
        px_, py_ = 132, 150
        lay.rect(px_, py_, 62, 24, 'B', 2.4, hgt=0.6)
        lay.rect(px_, py_, 62, 1, 'B', 4.4, hgt=0.65)
        lay.rect(px_, py_ + 23, 62, 1, 'B', 1.2, hgt=0.5)
        lay.rect(px_ + 1, py_ + 2, 60, 20, 'I', 1.6, hgt=0.55)
        lay.text('KOMMISSION', px_ + 2, py_ + 4, 'B', 5.0, font='57')
        lay.text('VELTRAVA  1953', px_ + 4, py_ + 14, 'B', 4.0)
        lay.rect(px_ + 62, py_ + 1, 1, 24, 'W', 3.0)
        br, wa = kit.commission_arms(34, 22)
        lay.put(np.ones((26, 40), bool), 143, 108, 'C', 2.2, hgt=0.4, flat=True)  # slate shield
        lay.rect(143, 108, 40, 1, 'B', 4.4, hgt=0.6)
        lay.rect(143, 133, 40, 1, 'B', 2.4, hgt=0.5)
        lay.rect(142, 108, 1, 26, 'B', 3.6, hgt=0.6)
        lay.rect(183, 108, 1, 26, 'B', 2.2, hgt=0.5)
        lay.put(br, 146, 110, 'M', 6.2, hgt=0.7)
        lay.put(wa, 146, 110, 'M', 5.0, hgt=0.6)
        # lantern hanging from the ceiling (dim, warm)
        self.lantern(*L.VEST_LANTERN)
        # cloakroom alcove
        self.cloakroom()
        # vestibule right: clock (9:41, the match cut), framed directory board, mirror
        self.wall_clock(336, 120, hour=9, minute=41)
        self.stucco_panel(314, 150, 362, 236, rose=False)
        self.directory_board(316, 162)
        self.mirror(372, 160, 30, 68)
        self.radiator(366, 254, 40, 26)

    def entrance(self):
        """Glazed entrance screen: arched window, leaded fanlight, sidelights, revolving door."""
        lay = self.lay
        ex0, ex1 = L.ENTRANCE
        # stucco surround of the whole screen
        lay.rect(ex0, 30, ex1 - ex0, L.FLOOR - 30, 'M', 4.2, hgt=0.5)
        lay.rect(ex0, 30, 1, L.FLOOR - 30, 'M', 5.6, hgt=0.45)
        lay.rect(ex1 - 1, 30, 1, L.FLOOR - 30, 'M', 2.8, hgt=0.45)
        lay.rect(ex1, 32, 1, L.FLOOR - 32, 'W', 3.0, hgt=0.0)
        # --- big arched window (round arch)
        ax0, ax1, atop, abot = L.ARCHWIN
        aw, ah = ax1 - ax0, abot - atop
        rise = aw // 2
        m = kit.arch_mask(aw, ah, rise)
        outer = kit.arch_mask(aw + 8, ah + 4, rise + 4)
        lay.put(outer, ax0 - 4, atop - 4, 'M', 5.4, hgt=0.7)           # archivolt
        edge = kit.edge_of(outer)
        lay.put(edge, ax0 - 4, atop - 4, 'M', 6.4, hgt=0.75)
        for a in range(8, 180, 12):                                     # voussoir joints
            r = math.radians(a)
            cx, cy = ax0 + aw / 2 - 0.5, atop + rise
            for rr in (rise + 1, rise + 2, rise + 3):
                lay.px(int(round(cx + math.cos(r) * rr)), int(round(cy - math.sin(r) * rr)), 'M', 3.4, hgt=0.6)
        lay.rect(ax0 + aw // 2 - 3, atop - 6, 7, 8, 'M', 6.0, hgt=1.0)  # keystone (mask of a nymph, stylised)
        lay.rect(ax0 + aw // 2 - 2, atop - 4, 5, 1, 'B', 4.0, hgt=1.0)
        lay.px(ax0 + aw // 2 - 1, atop - 2, 'M', 3.0)
        lay.px(ax0 + aw // 2 + 1, atop - 2, 'M', 3.0)
        lay.put(m, ax0, atop, 'D', 3.0, hgt=0.2)                        # sash frame (walnut)
        glass = m & kit.erode(m, 2)
        bars = np.zeros_like(m)
        cx, cy = aw / 2 - 0.5, rise
        yy, xx = np.mgrid[0:ah, 0:aw]
        ang = np.degrees(np.arctan2(cy - yy, xx - cx))
        rad = np.hypot(xx - cx, (yy - cy))
        for a in (36, 72, 108, 144):
            bars |= (np.abs(ang - a) < 2.2) & (yy < cy) & (rad > 9)
        bars |= (np.abs(rad - 9.5) < 0.9) & (yy <= cy)
        bars |= (np.abs(rad - rise * 0.62) < 0.6) & (yy <= cy) & (rad > 9)
        bars[int(cy):int(cy) + 2, :] = True
        for xv in (aw // 4, aw // 2, 3 * aw // 4):
            bars[int(cy):, xv - 1:xv + 1] = True
        glass &= ~bars
        lay.put(m & ~glass, ax0, atop, 'D', 3.4, hgt=0.3)
        lay.put(kit.edge_of(glass) & ~glass, ax0, atop, 'D', 4.4)
        self.cut_glass(glass, ax0, atop, shaft=0.8)
        # --- transom beam + leaded fanlight
        fx0, fx1, fy0, fy1 = L.FANLIGHT
        lay.rect(ex0 + 2, abot, ex1 - ex0 - 4, fy0 - abot, 'D', 3.0, hgt=0.6)
        lay.rect(ex0 + 2, abot, ex1 - ex0 - 4, 1, 'D', 5.0, hgt=0.65)
        lay.rect(ex0 + 2, abot + 3, ex1 - ex0 - 4, 1, 'B', 4.4, hgt=0.7)
        fw, fh = fx1 - fx0, fy1 - fy0
        lay.rect(fx0, fy0, fw, fh, 'D', 2.6, hgt=0.3)
        fg = np.zeros((fh, fw), bool)
        cols = 8
        cw = fw // cols
        for c in range(cols):
            for r_ in range(3):
                px0 = c * cw + 1
                py0 = 1 + r_ * (fh - 2) // 3
                ph = (fh - 2) // 3 - 1
                fg[py0:py0 + ph, px0:px0 + cw - 1] = True
        # stylised tulips in coloured glass in the middle panes (backlit -> emission)
        tul = np.zeros((fh, fw), bool)
        for tx in (fw // 2 - cw - 2, fw // 2 + cw - 2):
            for (dx, dy) in ((1, 3), (2, 2), (3, 3), (1, 4), (2, 4), (3, 4), (2, 5), (2, 6), (2, 7), (2, 8),
                             (1, 9), (3, 9), (0, 8), (4, 8)):
                if 0 <= tx + dx < fw and 0 <= dy + 8 < fh:
                    tul[dy + 8, tx + dx] = True
        leaf = np.zeros((fh, fw), bool)
        for tx in (fw // 2 - cw - 2, fw // 2 + cw - 2):
            for (dx, dy) in ((0, 14), (1, 15), (4, 14), (3, 15), (2, 16), (2, 17)):
                if 0 <= tx + dx < fw and 0 <= dy + 8 < fh:
                    leaf[dy + 8, tx + dx] = True
        clear = fg & ~tul & ~leaf
        lay.put(tul & fg, fx0, fy0, 'A', 3.0, emis=True)
        lay.put(leaf & fg, fx0, fy0, 'G', 6.0, emis=True)
        self.cut_glass(clear, fx0, fy0, shaft=0.6)
        lay.rect(fx0, fy1, fw, 4, 'D', 3.2, hgt=0.6)                     # head beam over the doors
        lay.rect(fx0, fy1, fw, 1, 'B', 4.6, hgt=0.7)
        # --- sidelights
        for i, (sx0, sx1) in enumerate(L.SIDELIGHTS):
            sy0, sy1 = L.SIDE_Y
            lay.rect(sx0 - 2, sy0 - 2, sx1 - sx0 + 4, sy1 - sy0 + 4, 'D', 3.0, hgt=0.4)
            gm = np.ones((sy1 - sy0, sx1 - sx0), bool)
            gm[58:60, :] = False                                         # brass glazing bar
            gm[110:, :] = False                                          # kick panel
            self.cut_glass(gm, sx0, sy0, shaft=0.5)
            lay.rect(sx0, sy0 + 58, sx1 - sx0, 2, 'B', 4.0, hgt=0.7)
            bevel(lay, sx0 + 1, sy0 + 112, sx1 - sx0 - 2, sy1 - sy0 - 114, 'D', 3.0, hi=4.2, lo=1.6, hgt=0.4)
            self.frost(sx0, sy0 + 92, sx1 - sx0, 18, seed=30 + i)
        # transom light above the revolving door (was a blank stucco panel): clear glass in a brass grid,
        # the square and the falling snow show through, frost creeps up from the canopy
        rx0_, rx1_ = L.REVOLVING
        ty0, ty1 = fy1 + 4, L.DRUM_TOP - 16
        lay.rect(rx0_, ty0 - 1, rx1_ - rx0_, ty1 - ty0 + 2, 'D', 3.2, hgt=0.5)
        tg = np.zeros((ty1 - ty0, rx1_ - rx0_), bool)
        tg[1:-1, 1:-1] = True
        for bx in ((rx1_ - rx0_) // 3, 2 * (rx1_ - rx0_) // 3):
            tg[:, bx - 1:bx + 1] = False
        tg[(ty1 - ty0) // 2 - 1:(ty1 - ty0) // 2 + 1, :] = False
        lay.put(~tg & (np.ones_like(tg)), rx0_, ty0, 'B', 3.2, hgt=0.6)
        lay.put(kit.edge_of(np.ones_like(tg)) & ~tg, rx0_, ty0, 'D', 4.0, hgt=0.6)
        self.cut_glass(tg, rx0_, ty0, shaft=0.5)
        self.frost(rx0_ + 1, ty1 - 9, rx1_ - rx0_ - 2, 8, seed=44, rim=True)
        # mullions
        for (mx0, mx1) in ((ex0 + 1, ex0 + 4), (32, 36), (88, 92), (ex1 - 4, ex1 - 1)):
            lay.rect(mx0, fy1, mx1 - mx0, L.FLOOR - fy1, 'D', 3.4, hgt=0.6)
            lay.rect(mx0, fy1, 1, L.FLOOR - fy1, 'D', 5.0, hgt=0.65)
        # --- revolving door
        rx0, rx1 = L.REVOLVING
        top = L.DRUM_TOP
        lay.rect(rx0 - 2, top - 14, rx1 - rx0 + 4, 14, 'D', 3.2, hgt=0.7)        # canopy
        lay.rect(rx0 - 3, top - 14, rx1 - rx0 + 6, 2, 'B', 4.6, hgt=0.8)
        lay.rect(rx0 - 2, top - 12, rx1 - rx0 + 4, 1, 'D', 1.6, hgt=0.6)
        lay.rect(rx0 - 2, top - 2, rx1 - rx0 + 4, 2, 'B', 3.4, hgt=0.7)
        lay.text('EINGANG', rx0 + (rx1 - rx0 - kit.text_width('EINGANG')) // 2, top - 10, 'B', 5.0)
        dh = L.FLOOR - top
        g = np.ones((dh - 2, rx1 - rx0), bool)
        mid = (rx1 - rx0) // 2
        # curved enclosure frames (outer), central post, front wing frame, push bar, kick plates
        frame = np.zeros_like(g)
        frame[:, 0:2] = True; frame[:, -2:] = True
        frame[:, 8:9] = True; frame[:, -9:-8] = True
        frame[:, mid - 1:mid + 1] = True
        frame[24:26, 8:-8] = True                                       # push bar
        frame[dh - 14:, :] = True                                       # kick plates
        frame[0:2, :] = True
        g &= ~frame
        self.cut_glass(g, rx0, top, shaft=0.55)
        lay.put(frame, rx0, top, 'B', 3.4, hgt=0.6)
        lay.put(frame & np.roll(~frame, 1, axis=1), rx0, top, 'B', 4.8)
        lay.rect(rx0 + 8, top + dh - 14, rx1 - rx0 - 16, 12, 'D', 3.2, hgt=0.5)
        lay.rect(rx0 + 8, top + dh - 14, rx1 - rx0 - 16, 1, 'B', 4.4, hgt=0.6)
        lay.rect(rx0, top + dh - 14, 8, 12, 'D', 2.4, hgt=0.4)
        lay.rect(rx1 - 8, top + dh - 14, 8, 12, 'D', 2.0, hgt=0.4)
        # vertical highlights on the curved glass (reads as a drum)
        for (gx, t) in ((rx0 + 4, 5.0), (rx0 + 5, 4.0), (rx1 - 5, 3.6)):
            for yy in range(top + 4, top + dh - 16, 1):
                if (yy // 3) % 3 != 0:
                    lay.px(gx, yy, 'S', t, unlit=True)
                    self.glass[yy, gx] = False
        lay.rect(rx0 - 2, L.FLOOR - 2, rx1 - rx0 + 4, 2, 'B', 4.0, hgt=0.4)   # floor ring
        self.frost(rx0 + 2, top + dh - 26, mid - 3, 10, seed=41, rim=False)

    def lantern(self, cx, bot):
        lay = self.lay
        lay.rect(cx, 0, 1, bot - 26, 'B', 2.6, hgt=0.5)                 # rod
        for k in range(0, bot - 26, 4):
            lay.px(cx, k, 'B', 3.8)
        lay.rect(cx - 6, bot - 26, 13, 3, 'B', 3.0, hgt=0.8)            # crown
        lay.rect(cx - 6, bot - 26, 13, 1, 'B', 4.6, hgt=0.85)
        body = [(cx - 7, bot - 23), (cx + 7, bot - 23), (cx + 5, bot - 6), (cx - 5, bot - 6)]
        m, mx, my = lay.poly(body, 'A', 3.0, emis=True)
        lay.put(kit.edge_of(m), mx, my, 'B', 3.2)
        for k in (-3, 0, 3):
            lay.line(cx + k, bot - 22, cx + int(k * 0.7), bot - 7, 'B', 2.8)
        lay.rect(cx - 2, bot - 18, 5, 6, 'A', 4.6, emis=True)
        lay.rect(cx - 4, bot - 6, 9, 3, 'B', 3.2, hgt=0.8)
        lay.px(cx, bot - 2, 'B', 4.0)
        lay.px(cx, bot - 1, 'B', 3.0)
        self.lights.append({'name': 'vest_lantern', 'pos': (cx, bot - 14), 'kind': 'warm', 'energy': 0.55,
                            'radius': 110, 'height': 30, 'pool': True})

    def cloakroom(self):
        lay = self.lay
        cx0, cx1 = L.CLOAK
        # alcove
        recess(lay, cx0 - 2, 170, cx1 - cx0 + 4, L.FLOOR - 170, 'W', 4.0, shadow=2.6, light=5.4, hgt=-0.4)
        lay.rect(cx0 - 4, 164, cx1 - cx0 + 8, 6, 'D', 3.0, hgt=0.7)                # lintel board
        lay.rect(cx0 - 4, 164, cx1 - cx0 + 8, 1, 'D', 5.0, hgt=0.75)
        lay.rect(cx0 - 4, 169, cx1 - cx0 + 8, 1, 'D', 1.4, hgt=0.5)
        # sign board above: GARDEROBE / VESTIAIRE / ГАРДЕРОБ
        sx, sy, sw = cx0 + 4, 140, cx1 - cx0 - 8
        lay.rect(sx, sy, sw, 22, 'D', 2.0, hgt=0.6)
        lay.rect(sx, sy, sw, 1, 'D', 4.2, hgt=0.65)
        lay.rect(sx, sy + 21, sw, 1, 'D', 1.0, hgt=0.55)
        tw = kit.text_width('GARDEROBE', '57')
        lay.text('GARDEROBE', sx + (sw - tw) // 2, sy + 3, 'B', 4.6, font='57')
        t2 = 'VESTIAIRE  ГАРДЕРОБ'
        lay.text(t2, sx + (sw - kit.text_width(t2)) // 2, sy + 13, 'B', 3.2)
        lay.rect(sx + sw, sy + 1, 1, 22, 'W', 3.0)
        # hat shelf + hook rail with numbered brass tags
        lay.rect(cx0, 200, cx1 - cx0, 3, 'D', 3.4, hgt=0.7)
        lay.rect(cx0, 200, cx1 - cx0, 1, 'D', 5.2, hgt=0.75)
        lay.rect(cx0, 203, cx1 - cx0, 1, 'D', 1.0, hgt=0.3)
        ry = L.CLOAK_RAIL_Y
        lay.rect(cx0, ry, cx1 - cx0, 3, 'D', 3.0, hgt=0.6)
        lay.rect(cx0, ry, cx1 - cx0, 1, 'D', 4.6, hgt=0.65)
        hooks = list(range(cx0 + 5, cx1 - 2, 9))
        for i, hx in enumerate(hooks):
            lay.rect(hx, ry + 3, 1, 3, 'B', 4.0, hgt=0.8)
            lay.px(hx + 1, ry + 5, 'B', 3.4, hgt=0.8)
            lay.rect(hx - 1, ry - 5, 4, 4, 'B', 3.0, hgt=0.7)              # number tag
            lay.px(hx, ry - 4, 'I', 1.0)
            lay.px(hx + 1, ry - 3, 'I', 1.0)
        # hats on the shelf: homburg, karakul hat, a lady's felt hat
        lay.rect(222, 195, 10, 2, 'I', 1.6, hgt=0.7); lay.rect(224, 191, 6, 4, 'I', 2.0, hgt=0.75)
        lay.rect(224, 194, 6, 1, 'D', 2.2)
        lay.rect(246, 192, 9, 8, 'D', 1.8, hgt=0.7)                      # karakul
        for k in range(0, 9, 2):
            lay.px(246 + k, 192 + (k % 3), 'D', 3.0)
        lay.ellipse(278, 197, 5.5, 1.6, 'R', 1.4, hgt=0.7); lay.rect(275, 193, 6, 3, 'R', 1.6, hgt=0.7)
        # coats on the hooks (hanging silhouettes with folds and collars)
        coats = [
            (hooks[0], 'I', 2.0, 38, 10, None),          # navy greatcoat
            (hooks[1], 'W', 4.6, 34, 9, None),            # grey overcoat
            (hooks[3], 'D', 2.6, 40, 11, 'fur'),          # black/brown coat, karakul collar
            (hooks[5], 'W', 3.2, 42, 9, 'elena'),         # Elena: charcoal wool to mid-calf + wine scarf
            (hooks[6], 'G', 3.2, 36, 10, None),           # loden
            (hooks[8], 'I', 1.6, 37, 10, None),           # dark navy
        ]
        for (hx, rmp, t, ln, wd, extra) in coats:
            self.coat(hx, ry + 6, rmp, t, ln, wd, extra)
        # brass bell + tokens are on the counter prop

    def coat(self, hx, y, rmp, t, ln, wd, extra=None):
        lay = self.lay
        hw = wd // 2
        pts = [(hx - 2, y), (hx + 3, y), (hx + hw + 1, y + 6), (hx + hw + 2, y + ln), (hx - hw - 1, y + ln),
               (hx - hw, y + 6)]
        m, mx, my = lay.poly(pts, rmp, t, hgt=0.6)
        e = kit.edge_of(m)
        hh, ww = m.shape
        yy, xx = np.mgrid[0:hh, 0:ww]
        lay.put(e & (xx < ww // 2), mx, my, rmp, t + 0.9)
        lay.put(e & (xx >= ww // 2), mx, my, rmp, t - 1.0)
        lay.line(hx, y + 4, hx - 1, y + ln - 1, rmp, t - 1.0)               # front opening / fold
        lay.line(hx + hw - 1, y + 9, hx + hw, y + ln - 2, rmp, t - 0.7)
        lay.line(hx - hw + 1, y + 8, hx - hw + 1, y + ln - 3, rmp, t + 0.6)
        lay.rect(hx - hw, y + ln - 1, wd + 1, 1, rmp, t - 1.2)
        lay.rect(hx - 1, y + 1, 4, 3, rmp, t + 0.8, hgt=0.7)               # collar
        if extra == 'fur':
            lay.rect(hx - 3, y + 1, 7, 4, 'D', 1.6, hgt=0.75)
            for k in range(7):
                lay.px(hx - 3 + k, y + 1 + (k % 2), 'D', 2.8)
        if extra == 'elena':
            # wine-red scarf looped over the hook, one end hanging long down the front
            lay.rect(hx - 2, y + 1, 6, 3, 'R', 2.6, hgt=0.8)
            lay.rect(hx - 2, y + 1, 6, 1, 'R', 3.4, hgt=0.85)
            lay.rect(hx + 2, y + 4, 2, 18, 'R', 2.4, hgt=0.75)
            lay.rect(hx + 2, y + 4, 1, 18, 'R', 3.0, hgt=0.8)
            lay.rect(hx + 1, y + 22, 4, 2, 'R', 2.0, hgt=0.7)              # fringe
            for k in range(4):
                lay.px(hx + 1 + k, y + 24, 'R', 1.6)
            lay.rect(hx - 2, y + 6, 1, 6, 'R', 2.0, hgt=0.7)               # short end behind
            # the white commission armband peeking out of the pocket (slate stripe)
            lay.rect(hx - hw + 2, y + 24, 3, 2, 'P', 6.0, hgt=0.7)
            lay.px(hx - hw + 3, y + 24, 'C', 3.0)

    def wall_clock(self, cx, cy, hour, minute):
        lay = self.lay
        lay.ellipse(cx + 0.5, cy + 0.5, 9.0, 9.0, 'B', 3.0, hgt=0.7)
        lay.ellipse(cx + 0.5, cy + 0.5, 7.5, 7.5, 'P', 6.0, hgt=0.6)
        lay.ellipse(cx - 1.0, cy - 1.0, 3.5, 3.5, 'P', 7.0, hgt=0.6)
        for a in range(0, 360, 30):
            r = math.radians(a)
            lay.px(cx + round(math.cos(r) * 6), cy + round(math.sin(r) * 6), 'I', 1.0)
        ma = minute / 60 * 360
        ha = (hour % 12 + minute / 60) / 12 * 360
        for (ang, ln) in ((ma, 6.0), (ha, 4.0)):
            r = math.radians(ang - 90)
            lay.line(cx, cy, cx + math.cos(r) * ln, cy + math.sin(r) * ln, 'I', 1.0)
        lay.px(cx, cy, 'R', 3.0)
        for a in range(200, 300, 7):
            r = math.radians(a)
            lay.px(cx + 0.5 + math.cos(r) * 8.5, cy + 0.5 + math.sin(r) * 8.5, 'B', 5.0)
        lay.rect(cx - 1, cy - 14, 3, 5, 'B', 3.4, hgt=0.6)                  # bracket
        lay.rect(cx + 10, cy - 6, 1, 14, 'W', 3.0)                         # wall shadow

    def directory_board(self, x, y):
        """Black glass building directory with white enamel letters and arrows (trilingual)."""
        lay = self.lay
        w, h = 44, 34
        frame_box(lay, x, y, w, h, 'B', 3.0, 4.4, 1.6)
        lay.rect(x, y, w, h, 'I', 1.0, hgt=0.5)
        rows = [('SAAL', '>'), ('PROTOKOLL', '>'), ('KABINEN', '>'), ('GARDEROBE', '<')]
        for i, (t, arr) in enumerate(rows):
            yy = y + 3 + i * 8
            lay.text(t, x + 2, yy, 'P', 5.0)
            lay.text(arr, x + w - 5, yy, 'B', 4.4)
        lay.rect(x, y, w, 1, 'S', 3.0)                                      # glass sheen

    def mirror(self, x, y, w, h):
        lay = self.lay
        # carved gilt frame with a Jugendstil crest
        lay.rect(x - 3, y - 3, w + 6, h + 6, 'B', 3.0, hgt=0.7)
        lay.rect(x - 3, y - 3, w + 6, 1, 'B', 4.8, hgt=0.75)
        lay.rect(x - 3, y - 3, 1, h + 6, 'B', 4.2, hgt=0.7)
        lay.rect(x + w + 2, y - 3, 1, h + 6, 'B', 1.8, hgt=0.6)
        lay.rect(x - 3, y + h + 2, w + 6, 1, 'B', 1.6, hgt=0.6)
        stamp(lay, x + w // 2 - 3, y - 11, LILY[:8], cream=('B', 3.6), gilt=('B', 5.0), shadow=('W', 3.0))
        # the glass: dark cold depth, a soft reflection of the window light, diagonal sheen
        t = np.linspace(3.2, 2.2, h)[:, None] + np.zeros((1, w))
        lay.put(np.ones((h, w), bool), x, y, 'C', t, hgt=0.0, flat=False, gain=0.5)
        for k in range(-h, w, 9):
            for j in range(h):
                xx = x + k + j // 2
                if x <= xx < x + w and (j + k) % 5 != 0:
                    lay.px(xx, y + j, 'C', 4.0 if (k // 9) % 2 else 3.6, gain=0.5)
        lay.rect(x, y + h - 10, w, 10, 'C', 2.0, gain=0.5)                  # reflected dark dado
        lay.rect(x + w + 3, y - 1, 1, h + 5, 'W', 2.8)
        # console under the mirror
        lay.rect(x - 4, y + h + 8, w + 8, 3, 'M', 5.4, hgt=0.8)
        lay.rect(x - 4, y + h + 8, w + 8, 1, 'M', 6.6, hgt=0.85)
        lay.rect(x - 2, y + h + 11, w + 4, 2, 'B', 3.0, hgt=0.6)

    def radiator(self, x, y, w, h):
        lay = self.lay
        lay.rect(x, y, w, 2, 'M', 4.6, hgt=0.5)
        cols = w // 3
        for c in range(cols):
            cx = x + c * 3
            lay.rect(cx, y + 2, 2, h - 4, 'M', 3.8, hgt=0.6)
            lay.rect(cx, y + 2, 1, h - 4, 'M', 4.8, hgt=0.65)
            lay.rect(cx + 2, y + 2, 1, h - 4, 'W', 2.0, hgt=0.1)
        lay.rect(x, y + h - 2, w, 2, 'M', 3.0, hgt=0.5)

    # ------------------------------------------------------------------ cut walls between rooms
    def open_arch(self, x0, x1, spring):
        """Wide archway between two rooms: the cut wall (poche) only ABOVE the arch; through the opening the
        back wall runs on (stucco, marble dado, skirting), under a deep coffered soffit with a keystone.
        Reads as an open arch instead of a dark slot."""
        lay = self.lay
        w = x1 - x0
        crown = spring - 14
        # poche above the arch (near-black, faint coursing, a lighter cut edge)
        lay.rect(x0, 0, w, crown, 'N', 1.4, hgt=0.9)
        for yy in range(6, crown, 9):
            lay.rect(x0 + 1, yy, w - 2, 1, 'N', 0.6, hgt=0.85)
        for yy in range(6, crown, 18):
            lay.rect(x0 + w // 2, yy - 8, 1, 8, 'N', 0.6, hgt=0.85)
        lay.rect(x0, 0, 1, crown, 'W', 3.2, hgt=0.8)
        lay.rect(x1 - 1, 0, 1, crown, 'W', 2.6, hgt=0.8)
        # the back wall continues through the opening (same stucco gradient as base())
        yy = np.arange(crown, L.FLOOR, dtype=np.float32)[:, None]
        t = 4.7 + 1.25 * np.clip((yy - 40) / 160, 0, 1) ** 0.85 - 0.25 * np.clip((yy - 230) / 50, 0, 1)
        t = t + np.zeros((1, w), np.float32) - 0.35
        lay.put(np.ones((L.FLOOR - crown, w), bool), x0, crown, 'W', t, hgt=0.0, flat=False)
        # coffered soffit seen from below: a band that bends down at both springings
        for i in range(w):
            u = (i + 0.5) / w
            dy = int(round(12 * math.sin(math.pi * u) ** 0.5))
            top = spring - dy
            lay.rect(x0 + i, top - 2, 1, 2, 'M', 5.4, hgt=0.7)
            lay.rect(x0 + i, top, 1, 6, 'M', 3.6, hgt=0.5)
            lay.rect(x0 + i, top + 6, 1, 1, 'M', 2.4, hgt=0.3)
            if i % 6 == 3:
                lay.rect(x0 + i, top, 1, 6, 'M', 2.8, hgt=0.4)
        lay.vgrad(x0, spring + 6, w, 30, 'W', 3.6, 5.0, hgt=0.0)            # shadow under the soffit
        kx = x0 + w // 2
        lay.rect(kx - 4, crown - 4, 8, 13, 'M', 5.4, hgt=1.0)                 # keystone (Jugendstil mask)
        lay.rect(kx - 4, crown - 4, 8, 1, 'M', 6.6, hgt=1.0)
        lay.rect(kx + 3, crown - 3, 1, 12, 'M', 3.4, hgt=0.9)
        lay.rect(kx - 2, crown + 1, 4, 1, 'B', 4.2, hgt=1.0)
        lay.px(kx - 2, crown + 4, 'M', 3.2); lay.px(kx + 1, crown + 4, 'M', 3.2)
        lay.rect(kx - 1, crown + 7, 2, 1, 'M', 3.6)
        # marble dado + skirting continue on the wall seen through the arch
        top = 240
        lay.rect(x0, top, w, L.FLOOR - top, 'M', 3.6, hgt=0.3)
        lay.rect(x0, top, w, 1, 'M', 5.8, hgt=0.7)
        lay.rect(x0, top + 1, w, 2, 'M', 4.6, hgt=0.6)
        lay.rect(x0, top + 3, w, 1, 'M', 2.4, hgt=0.2)
        recess(lay, x0 + 3, top + 7, w - 6, L.FLOOR - top - 17, 'M', 2.8, shadow=2.0, light=4.6, hgt=-0.1)
        lay.rect(x0 + 4, top + 8, w - 8, L.FLOOR - top - 19, 'G', 3.0, hgt=0.05)
        lay.rect(x0, L.FLOOR - 7, w, 7, 'G', 2.4, hgt=0.4)
        lay.rect(x0, L.FLOOR - 7, w, 1, 'M', 4.6, hgt=0.5)
        # pilaster jambs framing the opening on both room sides
        for (jx, hi) in ((x0 - 5, True), (x1, False)):
            lay.rect(jx, spring - 14, 5, L.FLOOR - spring + 14, 'M', 5.0 if hi else 4.2, hgt=0.6)
            lay.rect(jx + (0 if hi else 4), spring - 14, 1, L.FLOOR - spring + 14, 'M', 6.4 if hi else 2.6,
                     hgt=0.6)
            lay.rect(jx - 1, spring - 18, 7, 4, 'M', 5.8, hgt=0.8)               # impost block
            lay.rect(jx - 1, spring - 18, 7, 1, 'M', 6.8, hgt=0.85)
            lay.rect(jx - 1, spring - 14, 7, 1, 'M', 3.0, hgt=0.6)
            lay.rect(jx - 1, L.FLOOR - 12, 7, 12, 'M', 4.4, hgt=0.7)              # plinth
            lay.rect(jx - 1, L.FLOOR - 12, 7, 1, 'M', 5.8, hgt=0.75)

    def arch_cut(self, x0, x1, lintel, opening=True):
        """Partition cut by the section plane (poche) with a round-arched or square opening."""
        lay = self.lay
        w = x1 - x0
        lay.rect(x0, 0, w, lintel, 'N', 1.2, hgt=0.9)
        for yy in range(8, lintel, 10):
            lay.rect(x0 + 1, yy, w - 2, 1, 'N', 0.6, hgt=0.85)
        lay.rect(x0, 0, 1, lintel, 'W', 3.0, hgt=0.8)
        lay.rect(x1 - 1, 0, 1, lintel, 'W', 2.4, hgt=0.8)
        if not opening:
            lay.rect(x0, lintel, w, L.FLOOR - lintel, 'N', 1.2, hgt=0.9)
            return
        for i in range(w):
            u = (i + 0.5) / w
            dy = int(round(5 * math.sin(math.pi * u)))
            lay.rect(x0 + i, lintel - dy, 1, dy + 4, 'M', 3.4, hgt=0.5)
            lay.rect(x0 + i, lintel + 4, 1, 1, 'M', 1.6, hgt=0.3)
        lay.rect(x0 + w // 2 - 3, lintel - 10, 6, 10, 'M', 5.0, hgt=1.0)
        lay.rect(x0 + w // 2 - 3, lintel - 10, 6, 1, 'M', 6.4, hgt=1.0)
        lay.rect(x0 + w // 2 - 1, lintel - 7, 2, 2, 'B', 4.2, hgt=1.0)
        lay.rect(x0, lintel + 5, w, L.FLOOR - lintel - 5, 'W', 3.0, hgt=-0.2)
        lay.vgrad(x0, lintel + 5, w, 26, 'W', 1.6, 3.0, hgt=-0.2)
        lay.rect(x0, L.FLOOR - 22, w, 22, 'D', 1.6, hgt=-0.1)
        lay.rect(x0, L.FLOOR - 22, w, 1, 'D', 3.0, hgt=-0.05)
        for (jx, hi) in ((x0 - 4, True), (x1, False)):
            lay.rect(jx, lintel - 12, 4, L.FLOOR - lintel + 12, 'M', 5.2 if hi else 4.2, hgt=0.6)
            lay.rect(jx + (0 if hi else 3), lintel - 12, 1, L.FLOOR - lintel + 12, 'M', 6.4 if hi else 2.6,
                     hgt=0.6)

    # ------------------------------------------------------------------ foyer
    def foyer(self):
        lay = self.lay
        fx0, fx1 = L.FOYER
        self.marble_dado(fx0, L.STAIR_FOOT - 10, top=240, seed=5)
        self.marble_dado(L.LANDING[1], L.SAAL_DOOR[0] - 10, top=240, seed=6)
        # pilasters: left of the photo wall, between buffet and window, right of the easel
        self.pilaster(440, 450, self.frieze_bottom + 10)
        self.pilaster(L.LANDING[1] + 2, L.LANDING[1] + 12, self.frieze_bottom + 10)
        self.pilaster(902, 912, self.frieze_bottom + 10)
        # high lunette windows (cold light from above)
        for i, (a, b) in enumerate(L.LUNETTES):
            self.lunette(a, b, i)
        # stucco panels on the upper wall between the lunettes
        self.stucco_panel(456, 96, 508, 176)
        self.stucco_panel(786, 96, 826, 214)
        self.photo_wall()
        self.portrait_medallion(482, 122, 12, 16)
        self.staircase()
        self.chandelier(*L.CHANDELIER)
        self.buffet_wall()
        self.tall_window()
        self.saal_doors()
        self.sconce(L.BUFFET[0] + 8, 200, 'sconce_buffet_l', energy=0.35, radius=60)
        self.sconce(L.BUFFET[1] - 8, 200, 'sconce_buffet_r', energy=0.35, radius=60)

    def lunette(self, x0, x1, idx):
        lay = self.lay
        y0, y1 = L.LUNETTE_Y
        w, h = x1 - x0, y1 - y0
        rise = h - 2
        outer = kit.arch_mask(w + 8, h + 5, rise + 4)
        lay.put(outer, x0 - 4, y0 - 4, 'M', 5.0, hgt=0.7)
        lay.put(kit.edge_of(outer), x0 - 4, y0 - 4, 'M', 6.2, hgt=0.75)
        m = kit.arch_mask(w, h, rise)
        lay.put(m, x0, y0, 'D', 3.0, hgt=0.3)
        glass = m & kit.erode(m, 1)
        yy, xx = np.mgrid[0:h, 0:w]
        cx, cy = w / 2 - 0.5, h - 0.5
        ang = np.degrees(np.arctan2(cy - yy, xx - cx))
        bars = np.zeros_like(m)
        for a in (30, 60, 90, 120, 150):
            bars |= np.abs(ang - a) < 3.0
        bars |= np.hypot(xx - cx, (yy - cy) * w / (2 * rise)) < 5
        glass &= ~bars
        lay.put(m & ~glass, x0, y0, 'D', 3.4, hgt=0.35)
        self.cut_glass(glass, x0, y0, shaft=0.75)
        lay.rect(x0 - 6, y1, w + 12, 3, 'M', 5.4, hgt=0.7)                  # sill
        lay.rect(x0 - 6, y1 + 3, w + 12, 1, 'W', 3.0)

    def photo_wall(self):
        lay = self.lay
        x0, x1 = L.PHOTO_WALL
        # the big photo: the 1953 armistice signing (long table, signatories, flags behind)
        px_, py_, pw, ph = 456, 190, 44, 28
        frame_box(lay, px_, py_, pw, ph, 'D', 2.0, 3.6, 1.0)
        lay.rect(px_, py_, pw, ph, 'P', 5.4, hgt=0.4)
        lay.rect(px_ + 2, py_ + 2, pw - 4, ph - 4, 'P', 3.6, hgt=0.4)
        lay.rect(px_ + 2, py_ + 2, pw - 4, 9, 'P', 4.6, hgt=0.4)            # pale back wall
        for k in range(6):                                                   # flags behind
            lay.rect(px_ + 5 + k * 6, py_ + 3, 3, 6, 'P', 2.4 + (k % 2) * 0.8)
        lay.rect(px_ + 3, py_ + 17, pw - 6, 2, 'P', 6.0)                    # table cloth
        lay.rect(px_ + 3, py_ + 19, pw - 6, 4, 'P', 2.6)
        for k in range(7):                                                   # seated signatories
            hx = px_ + 5 + k * 5
            lay.rect(hx, py_ + 13, 3, 4, 'P', 1.0)
            lay.px(hx + 1, py_ + 12, 'P', 5.0)
        lay.px(px_ + 21, py_ + 16, 'P', 7.0); lay.px(px_ + 22, py_ + 16, 'P', 7.0)  # the document
        for k in range(4):                                                   # standing officials
            hx = px_ + 7 + k * 10
            lay.rect(hx, py_ + 9, 2, 6, 'P', 1.6)
            lay.px(hx, py_ + 8, 'P', 4.6)
        # brass plaque under it
        lay.rect(px_ + 6, py_ + ph + 5, pw - 12, 6, 'B', 3.0, hgt=0.6)
        lay.rect(px_ + 6, py_ + ph + 5, pw - 12, 1, 'B', 4.6, hgt=0.65)
        lay.text('1953', px_ + (pw - 15) // 2, py_ + ph + 6, 'I', 1.0)
        # smaller portraits / group photos around
        for (fx, fy, fw, fh, seed) in ((458, 160, 14, 18, 1), (476, 162, 12, 14, 2), (492, 160, 14, 18, 3),
                                        (462, 234, 12, 10, 4), (486, 234, 14, 10, 5)):
            frame_box(lay, fx, fy, fw, fh, 'D', 2.2, 3.6, 1.0)
            lay.rect(fx, fy, fw, fh, 'P', 3.2, hgt=0.4)
            lay.rect(fx + 1, fy + 1, fw - 2, fh // 2, 'P', 4.4, hgt=0.4)
            rng = np.random.default_rng(seed)
            n = int(rng.integers(1, 4))
            for k in range(n):
                hx = fx + 2 + k * (fw - 4) // max(1, n)
                lay.rect(hx, fy + fh // 2 - 1, 3, fh // 2, 'P', 1.2)
                lay.px(hx + 1, fy + fh // 2 - 2, 'P', 5.2)

    def staircase(self):
        """Grand marble staircase rising to the right along the back wall, red runner, wrought-iron
        Jugendstil balustrade with a walnut handrail, landing with a balustrade and the upper door."""
        lay = self.lay
        x0 = L.STAIR_FOOT
        xt, yt = L.STAIR_TOP
        steps = 16
        rise = (L.FLOOR - yt) / steps
        run = (xt - x0) / steps
        # upper wall above the flight: a raking marble wainscot that climbs with the stair (verde panels in
        # a cream frame, moulded top rail) + a brass wall rail on brackets -- instead of loose rake lines
        slope = (L.FLOOR - yt) / (xt - x0)
        dado_h = 36
        for xx in range(x0 - 2, xt + 1):
            ty = L.FLOOR - (xx - x0) * slope
            top = int(round(ty - dado_h))
            bot = int(round(ty)) + 2
            lay.rect(xx, top, 1, bot - top, 'M', 2.7, hgt=0.3)
            lay.px(xx, top, 'M', 4.8, hgt=0.7)
            lay.px(xx, top + 1, 'M', 3.8, hgt=0.6)
            lay.px(xx, top + 2, 'M', 2.0, hgt=0.2)
            lay.px(xx, top - 1, 'W', 4.2, hgt=0.0)                         # contact shadow above the rail
        for k in range(6):                                                  # raking verde panels
            a = x0 + 8 + k * 29
            b = a + 24
            if b > xt - 4:
                break
            for xx in range(a, b):
                ty = L.FLOOR - (xx - x0) * slope
                p0 = int(round(ty - dado_h + 6))
                p1 = int(round(ty - 7))
                lay.rect(xx, p0, 1, p1 - p0, 'G', 2.9 + 0.5 * (((xx * 7 + k * 3) % 11) < 2), hgt=0.05)
                lay.px(xx, p0 - 1, 'M', 1.8, hgt=0.0)
                lay.px(xx, p1, 'M', 3.8, hgt=0.1)
            ta = L.FLOOR - (a - x0) * slope
            tb = L.FLOOR - (b - x0) * slope
            lay.line(a - 1, ta - dado_h + 5, a - 1, ta - 8, 'M', 1.8)
            lay.line(b, tb - dado_h + 5, b, tb - 8, 'M', 3.8)
        self.pax_painting(538, 70, 70, 54)
        # spandrel (below the flight): panelled dark-marble wall in shadow
        span = []
        for i in range(steps):
            sx = int(round(x0 + i * run))
            sy = int(round(L.FLOOR - (i + 1) * rise))
            span.append((sx, sy))
        sp_pts = [(x0, L.FLOOR)] + [(int(round(x0 + (i + 1) * run)), int(round(L.FLOOR - (i + 1) * rise)) + 10)
                                    for i in range(steps)] + [(xt, L.FLOOR)]
        lay.poly(sp_pts, 'G', 2.6, hgt=0.2)
        for k in range(3):                                                  # raking panels on the spandrel
            a = x0 + 30 + k * 52
            b = a + 40
            ya = L.FLOOR - (a - x0) / run * rise + 18
            yb = L.FLOOR - (b - x0) / run * rise + 18
            lay.line(a, ya, b, yb, 'M', 4.0)
            lay.line(a, ya, a, L.FLOOR - 14, 'M', 3.6)
            lay.line(b, yb, b, L.FLOOR - 14, 'M', 3.0)
            lay.line(a, L.FLOOR - 14, b, L.FLOOR - 14, 'M', 3.0)
        # outer string (the flight's side face) with a moulding
        for i in range(steps):
            sx0 = int(round(x0 + i * run))
            sx1 = int(round(x0 + (i + 1) * run))
            ty = int(round(L.FLOOR - (i + 1) * rise))
            # tread (marble) + nosing + red runner draped over it
            lay.rect(sx0, ty, sx1 - sx0 + 1, 2, 'M', 6.2, hgt=0.6)
            lay.rect(sx0, ty + 2, sx1 - sx0 + 1, int(rise) - 1, 'M', 4.6, hgt=0.5)   # riser of the next
            lay.rect(sx0 + 2, ty - 1, sx1 - sx0 - 3, 2, 'R', 2.4, hgt=0.7)            # runner on the tread
            lay.rect(sx0 + 2, ty - 1, sx1 - sx0 - 3, 1, 'R', 3.0, hgt=0.75)
            lay.px(sx0 + 2, ty + 1, 'B', 4.6, hgt=0.8)                                 # stair rod end
        # the string band
        for xx in range(x0 - 2, xt + 2):
            u = (xx - x0) / (xt - x0)
            yy = int(round(L.FLOOR - u * (L.FLOOR - yt))) + 2
            lay.rect(xx, yy + 6, 1, 6, 'M', 5.2, hgt=0.7)
            lay.px(xx, yy + 6, 'M', 6.4, hgt=0.75)
            lay.px(xx, yy + 11, 'M', 2.6, hgt=0.5)
            lay.px(xx, yy + 12, 'G', 1.4, hgt=0.2)
        # landing slab + front moulding
        lx0, lx1 = L.LANDING
        lay.rect(xt - 2, yt, lx1 - xt + 2, 3, 'M', 6.0, hgt=0.7)
        lay.rect(xt - 2, yt + 3, lx1 - xt + 2, 8, 'M', 4.8, hgt=0.7)
        lay.rect(xt - 2, yt + 3, lx1 - xt + 2, 1, 'M', 6.4, hgt=0.75)
        lay.rect(xt - 2, yt + 10, lx1 - xt + 2, 1, 'M', 2.6, hgt=0.5)
        lay.rect(xt - 2, yt + 11, lx1 - xt + 2, 3, 'W', 2.6, hgt=0.0)       # soffit shadow
        # under the landing: a shadowed niche with a marble bust of the Kurhaus founder
        recess(lay, 734, 206, 26, 56, 'W', 3.2, shadow=2.2, light=4.4, hgt=-0.3)
        lay.rect(740, 238, 14, 24, 'M', 4.6, hgt=0.6)                       # pedestal
        lay.rect(739, 238, 16, 2, 'M', 6.0, hgt=0.7)
        lay.ellipse(747, 228, 4.2, 5.5, 'M', 5.4, hgt=0.8, flat=False)      # bust head
        lay.rect(742, 232, 11, 6, 'M', 5.0, hgt=0.7)
        lay.px(746, 226, 'M', 3.4); lay.px(748, 226, 'M', 3.4)
        # upper door on the landing (to the Saal gallery), closed
        ux0, ux1 = L.UPPER_DOOR
        utop = 112
        lay.rect(ux0 - 4, utop - 6, ux1 - ux0 + 8, yt - utop + 6, 'M', 5.2, hgt=0.6)
        lay.rect(ux0 - 4, utop - 6, ux1 - ux0 + 8, 1, 'M', 6.4, hgt=0.65)
        lay.rect(ux0, utop, ux1 - ux0, yt - utop, 'D', 2.4, hgt=0.3)
        half = (ux1 - ux0) // 2
        for k in range(2):
            lx = ux0 + k * half
            lay.rect(lx, utop, 1, yt - utop, 'D', 1.0)
            bevel(lay, lx + 3, utop + 4, half - 6, 26, 'D', 2.8, hi=4.0, lo=1.4, hgt=0.4)
            bevel(lay, lx + 3, utop + 34, half - 6, yt - utop - 40, 'D', 2.8, hi=4.0, lo=1.4, hgt=0.4)
        lay.rect(ux0 + half - 3, utop + 32, 2, 4, 'B', 4.4, hgt=0.8)
        lay.rect(ux0 + half + 1, utop + 32, 2, 4, 'B', 4.4, hgt=0.8)
        lay.text('GALERIE', ux0 + (ux1 - ux0 - kit.text_width('GALERIE')) // 2, utop - 14, 'M', 2.6)
        # wrought-iron balustrade along the flight + walnut handrail
        hr = 24
        for i in range(steps + 1):
            bx = int(round(x0 + i * run)) + 3
            by = int(round(L.FLOOR - (i + 0.5) * rise))
            top = int(round(by - hr + run * 0.0))
            lay.rect(bx, top, 1, by - top, 'I', 1.2, hgt=0.6)
            if i % 2 == 0 and i < steps:   # whiplash scroll between balusters
                cx_ = bx + run / 2
                cy_ = by - hr / 2 - rise / 2
                for a in range(0, 330, 22):
                    r_ = math.radians(a)
                    rr = 3.2 * (1 - a / 520)
                    lay.px(int(round(cx_ + math.cos(r_) * rr)), int(round(cy_ + math.sin(r_) * rr)), 'I', 1.4,
                           hgt=0.6)
                lay.line(cx_ + 3, cy_ + 2, cx_ + 5, cy_ + 7, 'I', 1.2, hgt=0.6)
        for xx in range(x0 - 4, xt + 1):
            u = (xx - x0) / (xt - x0)
            yy = L.FLOOR - u * (L.FLOOR - yt) - hr - 1
            lay.rect(xx, int(round(yy)), 1, 2, 'D', 4.0, hgt=0.9)
            lay.px(xx, int(round(yy)), 'D', 6.0, hgt=0.95)
            lay.px(xx, int(round(yy)) + 6, 'I', 1.2, hgt=0.6)                # lower rail
        # landing balustrade (horizontal); its pixels are remembered (landing_front) so figures standing on
        # the landing (env_veltrava_hall_life) can be drawn behind it
        front = np.zeros((L.WORLD_H, L.WORLD_W), bool)
        for bx in range(xt + 2, lx1, 5):
            lay.rect(bx, yt - hr, 1, hr, 'I', 1.2, hgt=0.6)
            front[yt - hr:yt, bx] = True
        for bx in range(xt + 4, lx1 - 2, 10):
            for a in range(0, 360, 30):
                r_ = math.radians(a)
                qx, qy = int(round(bx + 2.5 + math.cos(r_) * 2.2)), int(round(yt - hr / 2 + math.sin(r_) * 3.2))
                lay.px(qx, qy, 'I', 1.4, hgt=0.6)
                front[qy, qx] = True
        lay.rect(xt - 1, yt - hr - 1, lx1 - xt + 1, 2, 'D', 4.0, hgt=0.9)
        lay.rect(xt - 1, yt - hr - 1, lx1 - xt + 1, 1, 'D', 6.0, hgt=0.95)
        lay.rect(xt, yt - 6, lx1 - xt, 1, 'I', 1.2, hgt=0.6)
        front[yt - hr - 1:yt - hr + 1, xt - 1:lx1] = True
        front[yt - 6, xt:lx1] = True
        self.landing_front = front
        # newel post with a bronze torchere (switched off in the morning)
        nx = x0 - 10
        lay.rect(nx, L.FLOOR - 40, 8, 40, 'M', 5.0, hgt=0.8)
        lay.rect(nx, L.FLOOR - 40, 1, 40, 'M', 6.4, hgt=0.75)
        lay.rect(nx + 7, L.FLOOR - 40, 1, 40, 'M', 3.0, hgt=0.75)
        lay.rect(nx - 1, L.FLOOR - 42, 10, 3, 'M', 6.0, hgt=0.85)
        lay.rect(nx - 1, L.FLOOR - 8, 10, 8, 'M', 4.2, hgt=0.8)
        lay.rect(nx + 3, L.FLOOR - 58, 2, 16, 'B', 3.2, hgt=0.9)
        lay.ellipse(nx + 4, L.FLOOR - 62, 4.0, 4.5, 'M', 6.2, hgt=0.9, flat=False)   # opal globe (off)
        lay.px(nx + 2, L.FLOOR - 64, 'M', 7.0)

    def chandelier(self, cx, bot):
        """Crystal chandelier: ceiling rose, chain, brass crown, two rings of candle bulbs, crystal
        drops in tiers -- the warm focal light of the foyer."""
        lay = self.lay
        lay.ellipse(cx + 0.5, L.CEIL + 2, 9, 3, 'M', 5.4, hgt=0.8)          # ceiling rose
        top = L.CEIL + 4
        for yy in range(top, bot - 70):                                     # chain
            lay.px(cx, yy, 'B', 3.6 if yy % 3 else 4.8, hgt=0.8)
            if yy % 3 == 0:
                lay.px(cx + 1, yy, 'B', 2.6)
        cy0 = bot - 70
        lay.rect(cx - 5, cy0, 11, 3, 'B', 3.4, hgt=0.9)                     # crown
        lay.rect(cx - 5, cy0, 11, 1, 'B', 5.0, hgt=0.95)
        # crystal swags from the crown to the upper ring
        for side in (-1, 1):
            for k in range(4):
                xa = cx + side * (2 + k)
                pts = pg.catenary(cx + side * 2, cy0 + 3, cx + side * (14 + k * 4), cy0 + 22 + k, 4 + k)
                for j, (px_, py_) in enumerate(pts[::2]):
                    if j % 2 == 0:
                        lay.px(int(round(px_)), int(round(py_)), 'S', 5.0 if j % 4 == 0 else 4.0, unlit=True)
        # stem + body
        lay.rect(cx - 1, cy0 + 3, 3, 46, 'B', 3.2, hgt=0.9)
        lay.rect(cx - 1, cy0 + 3, 1, 46, 'B', 4.8, hgt=0.95)
        lay.ellipse(cx + 0.5, cy0 + 30, 5, 3, 'B', 3.6, hgt=0.9)
        lay.ellipse(cx + 0.5, cy0 + 50, 4, 4, 'B', 3.0, hgt=0.9)
        # upper ring (r 16) and lower ring (r 24) of arms with candle bulbs
        for (ry, rr, n, arm_t) in ((cy0 + 26, 15, 6, 3.6), (cy0 + 44, 23, 8, 3.2)):
            lay.ellipse(cx + 0.5, ry + 2, rr, 2.2, 'B', arm_t - 0.6, hgt=0.85)
            lay.ellipse(cx + 0.5, ry + 1.5, rr - 1, 1.2, 'B', arm_t + 1.0, hgt=0.9)
            for k in range(n):
                a = math.pi * (k + 0.5) / n
                bx = int(round(cx + math.cos(a) * rr))
                lay.rect(bx, ry - 4, 1, 4, 'M', 6.4, hgt=0.9)                 # candle sleeve
                lay.rect(bx - 1, ry - 7, 3, 3, 'A', 5.0, emis=True)          # bulb flame
                lay.px(bx, ry - 8, 'A', 5.0, emis=True)
            # crystal drops hanging from the ring
            for k in range(int(rr * 2) + 1):
                xx = cx - rr + k
                if k % 2 == 0:
                    ln = 3 + (k % 6 == 0) * 3
                    for j in range(ln):
                        lay.px(xx, ry + 3 + j, 'S', 5.0 if j == ln - 1 else 3.6, unlit=True)
        # bottom finial: a cascade of drops
        for j in range(14):
            w = max(1, 5 - j // 3)
            for k in range(-w, w + 1, 2):
                lay.px(cx + k, cy0 + 54 + j, 'S', 5.0 if (j + k) % 3 == 0 else 3.6, unlit=True)
        lay.px(cx, bot, 'S', 6.0, unlit=True)
        self.lights.append({'name': 'chandelier', 'pos': (cx, cy0 + 40), 'kind': 'warm', 'energy': 1.55,
                            'radius': 220, 'height': 40, 'falloff': 1.35, 'pool': True})

    def pax_painting(self, x, y, w, h):
        """Large commissioned allegory over the stair (1953): a pale standing 'Pax' with a branch between two
        kneeling groups, the three-arched bridge of the city arms behind -- academic, cool, a little empty.
        A brass plate: PAX 1953."""
        lay = self.lay
        frame_box(lay, x, y, w, h, 'B', 3.0, 4.8, 1.6)
        lay.rect(x - 1, y - 1, w + 2, 1, 'B', 5.4, hgt=0.75)
        # sky: cold, pale toward a low horizon; a faint warm break above the bridge
        sky = np.linspace(3.2, 5.2, int(h * 0.62))[:, None] + np.zeros((1, w))
        lay.put(np.ones(sky.shape, bool), x, y, 'C', sky, hgt=0.3, flat=False, gain=0.7)
        hy = y + int(h * 0.62)
        lay.rect(x, hy, w, h - int(h * 0.62), 'M', 3.2, hgt=0.3)            # ground
        lay.rect(x, hy, w, 1, 'M', 4.4, hgt=0.3)
        for k in range(0, w, 3):
            lay.px(x + k, hy + 4 + (k % 2), 'M', 2.6)
        # the bridge (three arches) far behind, river line
        by = hy - 5
        lay.rect(x + 8, by, w - 16, 2, 'M', 4.2, hgt=0.3)
        for k in range(3):
            ax = x + 10 + k * (w - 20) // 3
            lay.rect(ax, by + 2, 2, 4, 'M', 3.8)
            lay.rect(ax + (w - 20) // 3 - 2, by + 2, 2, 4, 'M', 3.8)
        lay.rect(x, hy - 1, w, 1, 'C', 5.6)
        # Pax: a standing woman in white drapery on a low plinth, right arm raised with an olive branch,
        # left hand open toward the kneeling groups; a paler patch of sky behind her (no halo)
        cx = x + w // 2
        lay.ellipse(cx + 0.5, y + 16, 12, 10, 'C', 5.2, flat=False, hgt=0.3)
        lay.rect(cx - 5, y + h - 13, 11, 3, 'M', 4.6, hgt=0.5)                # plinth
        lay.rect(cx - 5, y + h - 13, 11, 1, 'M', 5.6, hgt=0.55)
        lay.rect(cx - 1, y + 6, 3, 2, 'D', 3.4, hgt=0.5)                     # hair (knot)
        lay.rect(cx - 1, y + 8, 3, 3, 'P', 5.2, hgt=0.55)                    # face in profile
        lay.px(cx + 2, y + 9, 'P', 5.2)
        lay.px(cx, y + 11, 'P', 4.6)                                          # neck
        robe = [(cx - 3, y + 12), (cx + 3, y + 12), (cx + 4, y + 20), (cx + 6, y + h - 13), (cx - 6, y + h - 13),
                (cx - 3, y + 20)]
        lay.poly(robe, 'P', 6.4, hgt=0.5)
        for (a0, a1) in ((-1, -3), (1, 1), (2, 4)):                           # drapery folds
            lay.line(cx + a0, y + 15, cx + a1, y + h - 14, 'P', 4.8)
        lay.line(cx - 6, y + h - 14, cx + 6, y + h - 14, 'P', 5.0)
        lay.line(cx + 3, y + 13, cx + 7, y + 7, 'P', 6.0)                     # raised right arm
        lay.line(cx + 7, y + 7, cx + 8, y + 3, 'P', 5.6)
        for (dx, dy) in ((8, 2), (9, 1), (10, 1), (9, 0), (11, 0), (7, 1), (10, 2)):
            lay.px(cx + dx, y + dy, 'G', 5.4)                                 # olive branch
        lay.line(cx - 3, y + 14, cx - 7, y + 20, 'P', 5.6)                    # left arm, open hand
        # the two kneeling groups (east, west): heads, bowed backs, arms reaching toward her
        for side in (-1, 1):
            for k in range(3):
                fx = cx + side * (12 + k * 7)
                fy = y + h - 21 + k
                lay.rect(fx - 2, fy + 2, 5, 7, 'D', 2.2 + k * 0.4, hgt=0.4)  # cloak
                lay.rect(fx - 2 + (side > 0), fy, 3, 2, 'P', 3.6, hgt=0.45)   # head
                lay.px(fx - 1 + (side > 0), fy - 1, 'D', 2.4)
                lay.line(fx - side * 2, fy + 3, fx - side * 6, fy - 1, 'P', 3.6)  # reaching arm
                lay.rect(fx - 3, fy + 8, 7, 1, 'D', 1.8)                      # kneeling hem
        lay.rect(x, y + h - 9, w, 9, 'M', 2.8, hgt=0.3)                       # dark foreground
        # varnish sheen (cold window light from the lunettes) + brass plate
        for k in range(0, h, 2):
            xx = x + w - 18 + k // 3
            if xx < x + w:
                lay.px(xx, y + k, 'C', 5.0, gain=0.6)
        pw = kit.text_width('PAX  1953') + 6
        lay.rect(x + (w - pw) // 2, y + h + 4, pw, 7, 'B', 3.0, hgt=0.6)
        lay.rect(x + (w - pw) // 2, y + h + 4, pw, 1, 'B', 4.6, hgt=0.65)
        lay.text('PAX  1953', x + (w - pw) // 2 + 3, y + h + 5, 'I', 1.0)

    def portrait_medallion(self, cx, cy, rx, ry):
        """Oval portrait of the commission's first president (fictional, unnamed) in a gilt frame."""
        lay = self.lay
        lay.ellipse(cx + 0.5, cy + 0.5, rx + 3, ry + 3, 'B', 3.0, hgt=0.7)
        lay.ellipse(cx - 0.5, cy - 0.5, rx + 2, ry + 2, 'B', 4.6, hgt=0.75)
        lay.ellipse(cx + 0.5, cy + 0.5, rx + 1.5, ry + 1.5, 'B', 2.4, hgt=0.6)
        m, mx, my = lay.ellipse(cx + 0.5, cy + 0.5, rx, ry, 'D', 2.0, hgt=0.3)
        t = np.linspace(2.2, 1.4, m.shape[0])
        lay.put(m, mx, my, 'D', (t[:, None] + np.zeros((1, m.shape[1]))), flat=False)
        # sitter: dark suit, white collar, silver hair, a sash of the commission (slate)
        hx, hy = cx, cy - ry // 3
        lay.poly([(cx - rx + 3, cy + ry), (cx - 5, cy + 2), (cx + 6, cy + 2), (cx + rx - 2, cy + ry)], 'I', 1.4,
                 hgt=0.4)
        lay.rect(cx - 2, cy + 1, 5, 3, 'P', 6.4, hgt=0.5)
        lay.line(cx - 6, cy + 4, cx + 4, cy + ry - 1, 'C', 3.0)
        lay.ellipse(hx + 0.5, hy + 0.5, 4.0, 5.0, 'P', 4.6, hgt=0.6, flat=False)
        lay.rect(hx - 3, hy - 5, 7, 2, 'M', 6.0, hgt=0.6)
        lay.px(hx - 4, hy - 3, 'M', 5.4); lay.px(hx + 4, hy - 3, 'M', 5.4)
        lay.px(hx - 1, hy, 'P', 2.6); lay.px(hx + 2, hy, 'P', 2.6)
        lay.px(hx + 1, hy + 3, 'P', 3.0)
        lay.rect(cx - 5, cy + ry + 6, 11, 4, 'B', 3.4, hgt=0.6)               # name plate (unreadable)
        lay.hline(cx - 3, cy + ry + 8, 7, 'I', 1.4)
        stamp(lay, cx - 2, cy - ry - 8, ROSE)

    def buffet_wall(self):
        """Above the buffet: a large painting of Veltrava in winter (the old town and the bridge)."""
        lay = self.lay
        x0, x1 = L.BUFFET
        px_, py_, pw, ph = x0 + 6, 132, x1 - x0 - 12, 44
        frame_box(lay, px_, py_, pw, ph, 'B', 3.0, 4.8, 1.6)
        lay.vgrad(px_, py_, pw, 24, 'C', 3.6, 4.4)
        rng = np.random.default_rng(12)
        x = px_
        while x < px_ + pw:                                                 # roofs
            bw = int(rng.integers(4, 9))
            bh = int(rng.integers(4, 12))
            lay.rect(x, py_ + 26 - bh, bw, bh + 6, 'M', float(rng.choice([2.2, 2.8, 3.4])))
            x += bw
        lay.rect(px_ + 18, py_ + 8, 2, 14, 'M', 2.2)                        # dome + spire
        lay.ellipse(px_ + 30, py_ + 16, 5, 4, 'G', 4.0)
        lay.rect(px_, py_ + 30, pw, 6, 'C', 5.0)                            # frozen river
        lay.rect(px_, py_ + 30, pw, 1, 'C', 6.0)
        for k in range(px_ + 2, px_ + pw - 4, 8):                           # bridge with three arches
            pass
        lay.rect(px_ + 8, py_ + 28, pw - 16, 2, 'M', 4.0)
        for k in range(3):
            ax = px_ + 12 + k * ((pw - 24) // 3)
            lay.rect(ax, py_ + 30, 2, 5, 'M', 3.0)
        lay.rect(px_, py_ + 36, pw, ph - 36, 'M', 3.6)
        lay.text('VELTRAVA 1912', px_ + 2, py_ + ph - 6, 'M', 2.0)

    def tall_window(self):
        lay = self.lay
        wx0, wx1 = L.WINDOW
        y0, y1 = L.WIN_Y
        w, h = wx1 - wx0, y1 - y0
        rise = w // 2
        # architrave + hood with a Jugendstil keystone
        outer = kit.arch_mask(w + 18, h + 14, rise + 9)
        lay.put(outer, wx0 - 9, y0 - 9, 'M', 5.0, hgt=0.6)
        lay.put(kit.edge_of(outer), wx0 - 9, y0 - 9, 'M', 6.2, hgt=0.65)
        inner = kit.arch_mask(w + 8, h + 6, rise + 4)
        lay.put(inner, wx0 - 4, y0 - 4, 'W', 3.2, hgt=-0.5)                 # reveal
        lay.rect(wx0 - 4, y0 + rise, 3, h, 'W', 4.6, hgt=-0.45)
        lay.rect(wx1 + 1, y0 + rise, 3, h, 'W', 3.6, hgt=-0.45)
        stamp(lay, (wx0 + wx1) // 2 - 3, y0 - 16, LILY)
        m = kit.arch_mask(w, h, rise)
        lay.put(m, wx0, y0, 'D', 3.0, hgt=0.1)
        glass = m & kit.erode(m, 1)
        bars = np.zeros_like(m)
        mid = w // 2
        bars[:, mid - 1:mid + 1] = True
        for gy in (rise, rise + 1, rise + 46, rise + 92, rise + 93, rise + 136):
            if gy < h:
                bars[gy, :] = True
        bars[rise + 92:, 2:4] = True
        bars[rise + 92:, -4:-2] = True
        bars[rise + 92:, mid - 3:mid + 3] = True
        glass &= ~bars
        # leaded coloured glass in the arch (stylised lily, backlit)
        yy, xx = np.mgrid[0:h, 0:w]
        arch_part = glass & (yy < rise)
        lily = arch_part & ((np.abs(xx - (mid - 0.5)) < 1.2) | (np.hypot(xx - mid + 0.5, yy - rise * 0.55) < 3.2))
        leaf = arch_part & ~lily & (np.abs((xx - mid + 0.5) + (yy - rise) * 0.8) < 1.4) | \
            (arch_part & (np.abs((xx - mid + 0.5) - (yy - rise) * 0.8) < 1.4))
        lay.put(lily, wx0, y0, 'A', 3.4, emis=True)
        lay.put(leaf & ~lily, wx0, y0, 'G', 6.0, emis=True)
        lay.put(m & ~glass, wx0, y0, 'D', 3.4, hgt=0.2)
        clear = glass & ~lily & ~leaf
        self.cut_glass(clear, wx0, y0, shaft=1.0)
        for i, (fx0, fw) in enumerate(((wx0 + 4, mid - 7), (wx0 + mid + 3, mid - 7))):
            self.frost(fx0, y1 - 18, fw, 14, seed=60 + i)
        # sill + radiator niche
        lay.rect(wx0 - 12, y1 + 3, w + 24, 2, 'M', 6.4, hgt=0.7)
        lay.rect(wx0 - 12, y1 + 5, w + 24, 3, 'M', 4.6, hgt=0.6)
        lay.rect(wx0 - 12, y1 + 8, w + 24, 1, 'W', 2.6)
        recess(lay, wx0 - 4, y1 + 12, w + 8, L.FLOOR - y1 - 16, 'W', 3.0, shadow=2.0, light=4.0, hgt=-0.4)
        self.radiator(wx0 - 1, y1 + 16, w + 2, L.FLOOR - y1 - 22)
        # velvet curtains tied back + gilt pelmet
        for (cx0, cx1, side) in ((wx0 - 18, wx0 - 6, -1), (wx1 + 6, wx1 + 18, 1)):
            for xx_ in range(cx0, cx1):
                k = xx_ - cx0
                fold = (k % 4)
                t = 2.6 + (0.8 if fold == 1 else 0) - (0.8 if fold == 3 else 0)
                tie = 204
                pinch = 3 if side < 0 else -3
                lay.rect(xx_, y0 - 10, 1, tie - (y0 - 10), 'R', t, hgt=0.6)
                lay.rect(xx_ + (pinch if xx_ < (cx0 + cx1) / 2 else 0), tie, 1, y1 + 14 - tie, 'R', t - 0.3,
                         hgt=0.6)
            lay.rect(cx0 - 1, 202, cx1 - cx0 + 2, 3, 'B', 4.0, hgt=0.8)        # tie-back
            lay.rect(cx0 + 2, 205, 3, 8, 'B', 3.0, hgt=0.7)                     # tassel
        lay.rect(wx0 - 22, y0 - 14, w + 44, 8, 'R', 2.2, hgt=0.7)               # pelmet
        lay.rect(wx0 - 22, y0 - 14, w + 44, 2, 'B', 4.4, hgt=0.8)
        lay.rect(wx0 - 22, y0 - 7, w + 44, 1, 'B', 3.0, hgt=0.7)
        for k in range(wx0 - 20, wx1 + 22, 4):
            lay.px(k, y0 - 6, 'B', 3.6)

    def saal_doors(self):
        lay = self.lay
        x0, x1 = L.SAAL_DOOR
        top = L.SAAL_DOOR_TOP
        bot = L.FLOOR
        # marble architrave + overdoor with the commission arms in a gilt cartouche
        lay.rect(x0 - 7, top - 9, x1 - x0 + 14, bot - top + 9, 'M', 5.0, hgt=0.6)
        lay.rect(x0 - 7, top - 9, 1, bot - top + 9, 'M', 6.4, hgt=0.55)
        lay.rect(x1 + 6, top - 9, 1, bot - top + 9, 'M', 3.0, hgt=0.55)
        lay.rect(x1 + 7, top - 8, 1, bot - top + 8, 'W', 2.6)
        lay.rect(x0 - 11, top - 16, x1 - x0 + 22, 7, 'M', 5.2, hgt=0.8)
        lay.rect(x0 - 12, top - 16, x1 - x0 + 24, 2, 'M', 6.6, hgt=0.9)
        lay.rect(x0 - 10, top - 10, x1 - x0 + 20, 1, 'M', 2.6, hgt=0.6)
        cx = (x0 + x1) // 2
        cart = kit.arch_mask(36, 26, 8)
        lay.put(cart, cx - 18, top - 44, 'B', 3.0, hgt=0.7)
        lay.put(kit.edge_of(cart), cx - 18, top - 44, 'B', 4.6, hgt=0.75)
        lay.put(kit.erode(cart, 2), cx - 18, top - 44, 'C', 2.4, hgt=0.5)
        br, wa = kit.commission_arms(26, 16)
        lay.put(br, cx - 13, top - 39, 'M', 6.4, hgt=0.7)
        lay.put(wa, cx - 13, top - 39, 'M', 5.2, hgt=0.6)
        for s in (-1, 1):                                                   # stucco garlands
            for k in range(14):
                xx = cx + s * (19 + k)
                yy = top - 34 + int(round(4 * math.sin(math.pi * k / 13)))
                lay.px(xx, yy, 'M', 5.4, hgt=0.6)
                lay.px(xx, yy + 1, 'W', 3.6)
        # sign plaque on the cornice
        tw = kit.text_width('GROSSER SAAL')
        lay.rect(cx - tw // 2 - 3, top - 26, tw + 6, 8, 'I', 1.4, hgt=0.6)
        lay.rect(cx - tw // 2 - 3, top - 26, tw + 6, 1, 'B', 4.0, hgt=0.65)
        lay.text('GROSSER SAAL', cx - tw // 2, top - 25, 'B', 4.8)
        # leaves: walnut, glazed upper panels glowing warm (the lit Saal behind), brass push plates
        w = x1 - x0
        half = w // 2
        lay.rect(x0, top, w, bot - top, 'D', 2.6, hgt=0.3)
        for k in range(2):
            lx = x0 + k * half
            lay.rect(lx, top, 1, bot - top, 'D', 1.0)
            gx, gy, gw, gh = lx + 4, top + 7, half - 8, 38
            tt = 2.6 + pg.value_noise(gw, gh, 8, 70 + k, octaves=2) * 1.4
            lay.put(np.ones((gh, gw), bool), gx, gy, 'A', tt, emis=True, flat=False)
            lay.rect(gx, gy, gw, 1, 'A', 1.6, emis=True)
            for yy in range(gy + 3, gy + gh - 2, 6):                         # etched lines
                lay.rect(gx + 2, yy, gw - 4, 1, 'A', 4.0, emis=True)
            bevel(lay, gx - 1, gy - 1, gw + 2, gh + 2, 'D', 3.4, hi=4.6, lo=1.2, hgt=0.4)
            lay.put(np.ones((gh, gw), bool), gx, gy, 'A', tt, emis=True, flat=False)
            for (py, ph_) in ((top + 50, 14), (top + 68, bot - top - 76)):
                bevel(lay, lx + 4, py, half - 8, ph_, 'D', 3.0, hi=4.2, lo=1.4, hgt=0.35)
            lay.rect(lx + half - 6 if k == 0 else lx + 3, top + 48, 3, 10, 'B', 4.0, hgt=0.8)
        lay.rect(x0 - 2, bot - 2, w + 4, 2, 'M', 6.2, hgt=0.3)
        self.lights.append({'name': 'saal_doors', 'pos': (cx, top + 24), 'kind': 'warm', 'energy': 0.75,
                            'radius': 96, 'height': 8, 'wrap_add': 0.05})

    # ------------------------------------------------------------------ corridor + Protokollbuero
    def office(self):
        lay = self.lay
        x0, x1 = L.OFFICE
        self.wood_dado(x0, x1, top=214)
        self.office_upper()
        # evacuation plan (Fluchtwegplan): the staff corridor down to the cellar archive
        ex0, ex1, ey0, ey1 = L.EVAC
        self.evac_plan(ex0, ey0, ex1 - ex0, ey1 - ey0)
        self.treaty_shelf(*L.TREATY)
        # glazed partition post + office sign
        px0, px1 = L.OFFICE_DOOR
        lay.rect(px0, 92, px1 - px0, L.FLOOR - 92, 'D', 3.0, hgt=0.8)
        lay.rect(px0, 92, 1, L.FLOOR - 92, 'D', 4.8, hgt=0.8)
        lay.rect(px1 - 1, 92, 1, L.FLOOR - 92, 'D', 1.6, hgt=0.7)
        sw = kit.text_width('PROTOKOLLBÜRO') + 8
        sx = px1 + 6
        lay.rect(sx, 104, sw, 16, 'D', 2.0, hgt=0.6)
        lay.rect(sx, 104, sw, 1, 'D', 4.2, hgt=0.65)
        # both lines one row lower than before: the distinct Ü's dots (row 106) keep a row off the plate's top edge
        lay.text('PROTOKOLLBÜRO', sx + 4, 107, 'B', 4.6, overhang=True)
        lay.text('PROTOCOLE', sx + 4, 114, 'B', 3.0)
        # calendar + framed photo of the commission over the typist desk
        lay.rect(1120, 160, 14, 20, 'P', 6.0, hgt=0.3)
        lay.rect(1120, 160, 14, 5, 'R', 2.6, hgt=0.3)
        lay.text('II', 1125, 166, 'I', 1.0)
        for k in range(3):
            lay.hline(1122, 173 + k * 2, 10, 'I', 2.0)
        lay.px(1133, 158, 'B', 4.0)
        frame_box(lay, 1142, 156, 16, 12, 'D', 2.0, 3.4, 1.0)
        lay.rect(1142, 156, 16, 12, 'P', 3.4, hgt=0.4)
        for k in range(4):
            lay.rect(1144 + k * 4, 161, 2, 6, 'P', 1.2)
            lay.px(1144 + k * 4, 160, 'P', 5.0)
        # office window with a half-lowered blind
        self.office_window()
        # the corridor map over the big table: three rail corridors across the Line
        self.corridor_map(1232, 128, 80, 52)
        # pendant lamp over the big table (switched off: the desk lamp is used)
        cx = (L.TABLE[0] + L.TABLE[1]) // 2
        py0 = 106
        lay.rect(cx, L.CEIL + 14, 1, py0 - L.CEIL - 14, 'W', 3.0, hgt=0.4)
        for i in range(6):
            lay.rect(cx - 2 - i, py0 + i, 5 + 2 * i, 1, 'G', 3.0 + (i < 2) * 0.6, hgt=0.6)
        lay.rect(cx - 7, py0 + 6, 15, 1, 'M', 5.4, hgt=0.5)
        # shelves behind the mimeograph: paper reams, stencil boxes, ink tins
        mx0, mx1 = L.MIMEO
        for (sy, items) in ((196, 'reams'), (220, 'boxes')):
            lay.rect(mx0 - 6, sy, mx1 - mx0 + 12, 2, 'D', 3.6, hgt=0.7)
            lay.rect(mx0 - 6, sy, mx1 - mx0 + 12, 1, 'D', 5.0, hgt=0.75)
            rng = np.random.default_rng(sy)
            xx = mx0 - 5
            while xx < mx1 + 4:
                if items == 'reams':
                    bw = int(rng.integers(7, 11))
                    for k in range(int(rng.integers(2, 4))):
                        lay.rect(xx, sy - 3 - k * 3, bw, 3, 'P', float(rng.choice([4.6, 5.4, 6.0])), hgt=0.5)
                        lay.rect(xx, sy - 3 - k * 3, bw, 1, 'P', 3.6)
                    xx += bw + 2
                else:
                    bw = int(rng.integers(6, 9))
                    lay.rect(xx, sy - 8, bw, 8, 'D', float(rng.choice([3.0, 3.6])), hgt=0.5)
                    lay.rect(xx + 1, sy - 6, bw - 2, 2, 'P', 5.0, hgt=0.55)
                    xx += bw + 1
        lay.rect(mx0 - 20, 178, kit.text_width('VERVIELFÄLTIGUNG') + 4, 9, 'D', 2.0, hgt=0.6)
        lay.text('VERVIELFÄLTIGUNG', mx0 - 18, 180, 'P', 5.0, overhang=True)
        # filing cabinet + coat stand at the far end
        fx0 = 1368
        lay.rect(fx0, 238, 20, L.FLOOR - 238, 'W', 5.4, hgt=0.5)
        lay.rect(fx0, 238, 20, 1, 'W', 7.0, hgt=0.55)
        lay.rect(fx0 + 19, 238, 1, L.FLOOR - 238, 'W', 3.4, hgt=0.5)
        for k in range(4):
            yy = 241 + k * 12
            lay.rect(fx0 + 2, yy, 16, 11, 'W', 6.0, hgt=0.45)
            lay.rect(fx0 + 2, yy + 10, 16, 1, 'W', 4.0, hgt=0.4)
            lay.rect(fx0 + 7, yy + 3, 6, 2, 'P', 5.0, hgt=0.5)
            lay.rect(fx0 + 8, yy + 7, 4, 1, 'W', 8.0, hgt=0.6)

    def office_upper(self):
        """Structure for the office's high wall: heating pipe on brackets, a walnut picture rail with the map
        wires, the delegations' pigeonholes, the session indicator and the Saal monitor loudspeaker."""
        lay = self.lay
        x0, x1 = L.OFFICE
        # heating pipe (painted iron) with brackets, a drop down beside the window
        py_ = 66
        lay.rect(x0, py_, x1 - x0, 3, 'M', 2.4, hgt=0.8)                    # painted to match the wall
        lay.rect(x0, py_, x1 - x0, 1, 'M', 3.6, hgt=0.85)
        lay.rect(x0, py_ + 3, x1 - x0, 1, 'W', 3.4, hgt=0.0)
        for bx in range(x0 + 20, x1 - 10, 46):
            lay.rect(bx, py_ - 2, 2, 7, 'M', 2.8, hgt=0.9)
            lay.px(bx, py_ - 2, 'M', 4.0)
        dx = L.OFFICE_WIN[1] + 14
        lay.rect(dx, py_ + 2, 3, 214 - py_ - 2, 'M', 2.4, hgt=0.8)
        lay.rect(dx, py_ + 2, 1, 214 - py_ - 2, 'M', 3.4, hgt=0.85)
        lay.rect(dx + 3, py_ + 4, 1, 214 - py_ - 4, 'W', 3.4, hgt=0.0)
        lay.rect(dx - 1, py_ + 1, 5, 3, 'M', 3.0, hgt=0.9)                  # elbow
        # walnut picture rail with brass hooks; wires down to the corridor map
        ry = 96
        lay.rect(x0, ry, x1 - x0, 3, 'D', 3.6, hgt=0.7)
        lay.rect(x0, ry, x1 - x0, 1, 'D', 5.0, hgt=0.75)
        lay.rect(x0, ry + 3, x1 - x0, 1, 'W', 3.4, hgt=0.0)
        for (ax, bx_) in ((1246, 1240), (1298, 1304)):
            lay.px(ax, ry + 3, 'B', 4.4, hgt=0.9)
            lay.line(ax, ry + 4, bx_, 127, 'B', 2.8, hgt=0.6)
        # pigeonholes of the delegations (above the evacuation plan)
        gx0, gy0, cw, ch, cols, rows_ = 1023, 126, 11, 15, 2, 3
        W_ = cols * (cw + 2) + 2
        H_ = rows_ * (ch + 2) + 2
        lay.rect(gx0 - 1, gy0 - 5, W_ + 2, 5, 'D', 3.6, hgt=0.8)             # cornice
        lay.rect(gx0 - 2, gy0 - 5, W_ + 4, 1, 'D', 5.0, hgt=0.85)
        lay.rect(gx0, gy0, W_, H_, 'D', 3.0, hgt=0.6)
        lay.rect(gx0 + W_, gy0 + 1, 1, H_, 'W', 3.0)
        labels = ['SU', 'DR', 'S', 'CH', 'SF', 'K']
        rng = np.random.default_rng(1964)
        for r in range(rows_):
            for c in range(cols):
                cx_ = gx0 + 2 + c * (cw + 2)
                cy_ = gy0 + 2 + r * (ch + 2)
                recess(lay, cx_, cy_, cw, ch, 'D', 1.2, shadow=0.6, light=2.2, hgt=-0.3)
                n = int(rng.integers(0, 5))
                for k in range(n):                                          # papers / folders lying in it
                    lay.rect(cx_ + 1, cy_ + ch - 2 - k * 2, cw - 2, 2, 'P', [5.6, 4.6, 6.2, 3.8][k % 4], hgt=0.4)
                if r * cols + c < len(labels):
                    t = labels[r * cols + c]
                    lay.rect(cx_ + 1, cy_ - 1, cw - 2, 1, 'B', 3.8, hgt=0.7)
                    lay.text(t, cx_ + (cw - kit.text_width(t)) // 2, cy_ + 1, 'P', 5.4)
        # session indicator (SITZUNG lit) and the monitor loudspeaker for the Saal sound
        ix, iy = 1330, 118
        lay.rect(ix, iy, 46, 30, 'D', 2.2, hgt=0.6)
        lay.rect(ix, iy, 46, 1, 'D', 4.2, hgt=0.65)
        lay.rect(ix + 46, iy + 1, 1, 30, 'W', 3.0)
        for k, (t, on) in enumerate((('SITZUNG', True), ('PAUSE', False), ('ENDE', False))):
            yy = iy + 3 + k * 9
            if on:
                lay.rect(ix + 3, yy, 5, 5, 'R', 3.4, emis=True)
                lay.px(ix + 4, yy + 1, 'A', 4.6, emis=True)
            else:
                lay.rect(ix + 3, yy, 5, 5, 'I', 1.6, hgt=0.7)
                lay.px(ix + 4, yy + 1, 'S', 2.6)
            lay.text(t, ix + 11, yy, 'P' if on else 'P', 5.6 if on else 3.4)
        self.lights.append({'name': 'session_lamp', 'pos': (ix + 5, iy + 5), 'kind': 'warm', 'energy': 0.12,
                            'radius': 22, 'height': 4})
        sx_, sy_ = 1338, 154
        lay.rect(sx_, sy_, 28, 18, 'D', 3.2, hgt=0.7)                         # loudspeaker cabinet
        lay.rect(sx_, sy_, 28, 1, 'D', 4.8, hgt=0.75)
        lay.rect(sx_ + 3, sy_ + 3, 22, 12, 'M', 2.6, hgt=0.3)                 # fabric grille
        for k in range(sy_ + 4, sy_ + 14, 2):
            lay.rect(sx_ + 4, k, 20, 1, 'M', 3.4, hgt=0.35)
        for k in range(5):                                                    # Jugendstil fretwork
            lay.px(sx_ + 6 + k * 4, sy_ + 9, 'D', 2.4)
        lay.rect(sx_ + 28, sy_ + 1, 1, 18, 'W', 3.0)
        lay.line(sx_ + 14, sy_, sx_ + 14, py_ + 3, 'I', 1.4)                 # cable up to the pipe run

    def evac_plan(self, x, y, w, h):
        lay = self.lay
        frame_box(lay, x, y, w, h, 'D', 2.0, 3.4, 1.0)
        lay.rect(x, y, w, h, 'P', 6.2, hgt=0.4)
        lay.rect(x, y, w, 5, 'G', 3.6, hgt=0.4)                             # green title band
        lay.text('FLUCHTWEG', x + (w - kit.text_width('FLUCHTWEG')) // 2, y - 9, 'P', 5.0)
        # floor outline (thin ink), corridor (light), the dashed staff corridor down to the cellar
        lay.rect(x + 2, y + 7, w - 4, 1, 'I', 1.6)
        lay.rect(x + 2, y + 16, w - 4, 1, 'I', 1.6)
        lay.rect(x + 2, y + 7, 1, 10, 'I', 1.6)
        lay.rect(x + w - 3, y + 7, 1, 10, 'I', 1.6)
        for k in range(x + 6, x + w - 4, 6):
            lay.rect(k, y + 7, 1, 4, 'I', 1.6)
        for k in range(0, 8):                                               # green arrows (escape route)
            lay.px(x + 4 + k * 2, y + 12, 'G', 4.0)
        lay.px(x + w - 6, y + 11, 'G', 4.0); lay.px(x + w - 6, y + 13, 'G', 4.0)
        for k in range(0, 7):                                               # dashed: staff corridor -> UG
            if k % 2 == 0:
                lay.px(x + 10 + k, y + 18 + k, 'R', 2.6)
        lay.rect(x + 16, y + 24, 6, 3, 'I', 1.6)                            # the cellar room
        lay.px(x + 7, y + 12, 'R', 3.4)                                     # you-are-here dot
        lay.px(x + 7, y + 13, 'R', 3.4)

    def treaty_shelf(self, x0, x1):
        """Walnut bookcase with glazed doors: bound treaty volumes (spines with gilt bands)."""
        lay = self.lay
        top = 118
        w = x1 - x0
        lay.rect(x0 - 2, top - 8, w + 4, 8, 'D', 3.4, hgt=0.8)               # cornice
        lay.rect(x0 - 3, top - 8, w + 6, 2, 'D', 5.0, hgt=0.85)
        lay.rect(x0, top, w, L.FLOOR - top, 'D', 2.0, hgt=0.5)
        lay.rect(x0, top, 2, L.FLOOR - top, 'D', 4.0, hgt=0.6)
        lay.rect(x1 - 2, top, 2, L.FLOOR - top, 'D', 1.4, hgt=0.6)
        rng = np.random.default_rng(1953)
        rows = [(top + 4, 22), (top + 30, 22), (top + 56, 22), (top + 82, 22), (top + 108, 22)]
        spine_cols = [('R', 2.0), ('G', 3.0), ('D', 3.4), ('I', 2.0), ('R', 2.6), ('D', 4.0), ('G', 4.0)]
        for ri, (ry, rh) in enumerate(rows):
            lay.rect(x0 + 2, ry, w - 4, rh, 'D', 1.0, hgt=-0.3)
            xx = x0 + 3
            while xx < x1 - 4:
                sw = int(rng.integers(3, 6))
                sh = rh - int(rng.integers(1, 5))
                rm, t = spine_cols[int(rng.integers(0, len(spine_cols)))]
                if rng.random() < 0.05 and xx < x1 - 12:
                    for k in range(sh - 4):
                        lay.rect(xx + k // 4, ry + rh - 2 - k, sw, 1, rm, t, hgt=0.3)
                    xx += sw + 4
                    continue
                lay.rect(xx, ry + rh - sh, sw, sh, rm, t, hgt=0.4)
                lay.rect(xx, ry + rh - sh, 1, sh, rm, t + 0.8, hgt=0.45)
                lay.rect(xx, ry + rh - sh + 2, sw, 1, 'B', 3.6, hgt=0.5)         # gilt bands
                lay.rect(xx, ry + rh - 5, sw, 1, 'B', 3.2, hgt=0.5)
                if sw >= 4 and rng.random() < 0.4:
                    lay.rect(xx + 1, ry + rh - sh + 5, sw - 2, 3, 'P', 4.6, hgt=0.5)  # label
                xx += sw
            lay.rect(x0 + 2, ry + rh, w - 4, 4, 'D', 3.4, hgt=0.6)                # shelf board
            lay.rect(x0 + 2, ry + rh, w - 4, 1, 'D', 4.8, hgt=0.65)
        # glazed doors over the upper rows (glass sheen, brass frame)
        for k in range(2):
            gx = x0 + 2 + k * (w - 4) // 2
            gw = (w - 4) // 2
            lay.rect(gx, top + 2, gw, 1, 'B', 3.4, hgt=0.7)
            lay.rect(gx, top + 2, 1, 132, 'B', 3.0, hgt=0.7)
            lay.rect(gx + gw - 1, top + 2, 1, 132, 'B', 2.4, hgt=0.7)
            for j in range(0, 130, 1):
                xx = gx + 3 + (j * 3) // 10
                if (j // 4) % 4 != 0 and xx < gx + gw - 2:
                    lay.px(xx, top + 4 + j, 'S', 3.0, gain=0.6)
        lay.rect(x0 + 2, top + 134, w - 4, 2, 'B', 3.0, hgt=0.7)
        # brass labels on the cornice
        lay.text('1953', x0 + 4, top - 6, 'B', 4.6)
        lay.text('1963', x1 - 19, top - 6, 'B', 4.6)
        # lower cupboard doors
        bevel(lay, x0 + 3, top + 140, w // 2 - 4, L.FLOOR - top - 148, 'D', 2.8, hi=4.0, lo=1.4, hgt=0.5)
        bevel(lay, x0 + w // 2 + 1, top + 140, w // 2 - 4, L.FLOOR - top - 148, 'D', 2.8, hi=4.0, lo=1.4, hgt=0.5)
        lay.rect(x0 + w // 2 - 2, top + 150, 1, 4, 'B', 4.4)
        lay.rect(x0 + w // 2 + 1, top + 150, 1, 4, 'B', 4.4)
        lay.rect(x1 + 2, top - 6, 1, L.FLOOR - top + 6, 'W', 2.6)

    def office_window(self):
        lay = self.lay
        x0, x1, y0, y1 = L.OFFICE_WIN
        w, h = x1 - x0, y1 - y0
        lay.rect(x0 - 6, y0 - 6, w + 12, h + 12, 'M', 4.6, hgt=0.5)
        lay.rect(x0 - 6, y0 - 6, w + 12, 1, 'M', 6.0, hgt=0.55)
        lay.rect(x0 - 3, y0 - 3, w + 6, h + 4, 'W', 3.0, hgt=-0.5)
        lay.rect(x0, y0, w, h, 'D', 3.0, hgt=0.1)
        gm = np.ones((h, w), bool)
        gm[:, w // 2 - 1:w // 2 + 1] = False
        gm[:, :2] = False; gm[:, -2:] = False
        gm[:2, :] = False; gm[-2:, :] = False
        gm[h // 2:h // 2 + 2, :] = False
        blind = 34
        gm[:blind, :] = False
        self.cut_glass(gm, x0, y0, shaft=0.6)
        lay.rect(x0, y0, w, blind, 'P', 4.0, hgt=0.15)                      # roller blind
        for k in range(0, blind, 4):
            lay.rect(x0, y0 + k, w, 1, 'P', 3.4)
        lay.rect(x0, y0 + blind - 2, w, 2, 'D', 3.4, hgt=0.4)
        lay.rect(x0 + w // 2 - 1, y0 + blind, 2, 4, 'P', 5.0)
        self.frost(x0 + 2, y1 - 14, w // 2 - 3, 12, seed=81)
        lay.rect(x0 - 10, y1 + 3, w + 20, 3, 'M', 5.6, hgt=0.7)
        lay.rect(x0 - 10, y1 + 6, w + 20, 1, 'W', 2.6)
        # a potted fern on the sill
        lay.rect(x0 + 3, y1 - 4, 7, 7, 'D', 4.0, hgt=0.6)
        for (a, b) in ((-4, -8), (0, -11), (4, -9), (7, -6), (-6, -4)):
            lay.line(x0 + 6, y1 - 4, x0 + 6 + a, y1 - 4 + b, 'G', 4.6)

    def corridor_map(self, x, y, w, h):
        """Framed map: three rail corridors (red) across the Line (dark jagged), Veltrava on the river."""
        lay = self.lay
        frame_box(lay, x, y, w, h, 'D', 2.0, 3.6, 1.0)
        lay.rect(x, y, w, h, 'P', 5.4, hgt=0.3)
        rng = np.random.default_rng(64)
        for k in range(30):
            bx = x + 2 + int(rng.integers(0, w - 8))
            by = y + 2 + int(rng.integers(0, h - 6))
            lay.rect(bx, by, int(rng.integers(3, 7)), int(rng.integers(2, 4)), 'P', 4.4)
        pts = [(x + 30, y), (x + 34, y + 10), (x + 29, y + 20), (x + 36, y + 30), (x + 32, y + 40),
               (x + 38, y + h)]
        for a, b in zip(pts[:-1], pts[1:]):                                 # the Line
            for (px_, py_) in kit.bres(a[0], a[1], b[0], b[1]):
                lay.rect(px_, py_, 2, 1, 'I', 1.0)
        for (ya, yb) in ((y + 10, y + 8), (y + 26, y + 28), (y + 42, y + 40)):  # corridors
            for (px_, py_) in kit.bres(x + 3, ya, x + w - 4, yb):
                lay.px(px_, py_, 'R', 3.0)
        lay.ellipse(x + 34, y + 27, 2.0, 2.0, 'B', 4.4)                     # Veltrava
        river = [(x, y + 34), (x + 20, y + 30), (x + 34, y + 28), (x + 50, y + 33), (x + w, y + 31)]
        for a, b in zip(river[:-1], river[1:]):
            for (px_, py_) in kit.bres(a[0], a[1], b[0], b[1]):
                lay.px(px_, py_, 'C', 4.0)
        lay.text('C', x + w - 8, y + h - 7, 'R', 3.0)

    # ------------------------------------------------------------------ interpreters' corridor
    def interp(self):
        lay = self.lay
        x0, x1 = L.INTERP
        self.wood_dado(x0, x1, top=236, panel_w=20)
        # acoustic wall: diamond-tufted sage leather bays between walnut battens (each diamond a padded
        # cushion: height field -> the normal map lets the lamps model the quilting)
        uy0, uy1 = 96, 232
        hh, ww = uy1 - uy0, x1 - x0
        yy_, xx_ = np.mgrid[0:hh, 0:ww].astype(np.float32)
        P_ = 12.0
        a_ = (xx_ + yy_) / P_
        b_ = (xx_ - yy_) / P_
        fa, fb = a_ - np.floor(a_), b_ - np.floor(b_)
        da, db = np.minimum(fa, 1 - fa), np.minimum(fb, 1 - fb)
        crease = np.minimum(da, db)
        cushion = np.clip(crease * 2.4, 0, 1) ** 0.6
        tone = 3.55 + cushion * 0.75 - (crease < 0.06) * 0.9
        lay.put(np.ones((hh, ww), bool), x0, uy0, 'G', tone, hgt=0.1 + cushion * 0.45, flat=False)
        button = (da < 0.07) & (db < 0.07)
        lay.put(button, x0, uy0, 'G', 2.0, hgt=0.15)
        q = noise(ww, hh, 6, 77, octaves=2)
        lay.amb_field(q * 0.25, x0, uy0)
        # three etched-glass transoms over the booths: frosted, lit from the daylit Saal behind (cold glow),
        # Jugendstil lilies etched clear, the blurred shadows of the Saal chandeliers
        for i, (b0, b1) in enumerate(L.BOOTHS):
            self.etched_transom(b0 + 2, 104, b1 - b0 - 4, 54, i)
        for bx in range(x0 + 24, x1 - 10, 64):
            lay.rect(bx, uy0, 4, uy1 - uy0, 'D', 3.0, hgt=0.6)
            lay.rect(bx, uy0, 1, uy1 - uy0, 'D', 4.6, hgt=0.65)
            lay.rect(bx + 4, uy0, 1, uy1 - uy0, 'G', 1.4)
        lay.rect(x0, uy0 - 4, x1 - x0, 4, 'D', 3.6, hgt=0.6)
        lay.rect(x0, uy0 - 4, x1 - x0, 1, 'D', 5.0, hgt=0.65)
        lay.rect(x0, uy1, x1 - x0, 4, 'D', 3.0, hgt=0.6)
        lay.rect(x0, uy1, x1 - x0, 1, 'D', 4.4, hgt=0.65)
        # upper zone: cable tray, ventilation grilles, two opal globe lamps
        lay.rect(x0, 62, x1 - x0, 4, 'S', 1.6, hgt=0.5)
        lay.rect(x0, 62, x1 - x0, 1, 'S', 2.6, hgt=0.55)
        for xx in range(x0 + 8, x1, 40):
            lay.rect(xx, L.CEIL + 12, 1, 50 - L.CEIL, 'S', 1.2, hgt=0.4)
        for gx in (1508, 1786):
            lay.rect(gx, 74, 28, 10, 'W', 4.4, hgt=0.5)
            for k in range(gx + 2, gx + 27, 2):
                lay.rect(k, 76, 1, 6, 'W', 2.6, hgt=0.3)
        for gx in (1470, 1830):
            lay.rect(gx, L.CEIL + 10, 1, 52, 'B', 2.6, hgt=0.5)
            lay.ellipse(gx + 0.5, L.CEIL + 68, 5.5, 5.5, 'A', 3.4, emis=True)
            lay.ellipse(gx - 0.5, L.CEIL + 66, 2.5, 2.5, 'A', 4.6, emis=True)
            lay.rect(gx - 2, L.CEIL + 61, 5, 2, 'B', 3.4, hgt=0.7)
            self.lights.append({'name': 'globe_%d' % gx, 'pos': (gx, L.CEIL + 70), 'kind': 'warm',
                                'energy': 0.8, 'radius': 140, 'height': 36})
        # interpreters' sign by the door
        sx = 1414
        lay.rect(sx - 2, 112, kit.text_width('INTERPRÈTES  ПЕРЕВОДЧИКИ') + 4, 20, 'D', 2.0, hgt=0.6)
        lay.rect(sx - 2, 112, kit.text_width('INTERPRÈTES  ПЕРЕВОДЧИКИ') + 4, 1, 'D', 4.0, hgt=0.65)
        lay.text('DOLMETSCHER', sx, 115, 'B', 5.0)
        lay.text('INTERPRÈTES  ПЕРЕВОДЧИКИ', sx, 123, 'B', 3.6)
        # session sign (lit red) above the booths: RUHE - SITZUNG
        tw = kit.text_width('RUHE  SITZUNG')
        sx, sy = 1652 - tw // 2, 168
        lay.rect(sx - 3, sy - 3, tw + 6, 11, 'I', 1.2, hgt=0.6)
        lay.rect(sx - 3, sy - 3, tw + 6, 1, 'S', 2.6, hgt=0.65)
        lay.text('RUHE  SITZUNG', sx, sy, 'R', 3.6, emis=True)
        t2 = 'SILENCE  ТИШИНА'
        lay.text(t2, 1652 - kit.text_width(t2) // 2, sy + 12, 'B', 3.6)
        self.lights.append({'name': 'sign_ruhe', 'pos': (1652, sy + 3), 'kind': 'warm', 'energy': 0.2,
                            'radius': 36, 'height': 6})
        self.wall_clock(1470, 160, hour=10, minute=47)
        self.headset_cabinet(*L.HEADSETS)
        # booth platform kick strip
        bx0, bx1 = L.BOOTHS[0][0] - 6, L.BOOTHS[-1][1] + 6
        for i, (b0, b1) in enumerate(L.BOOTHS):
            self.booth(b0, b1, i)
        lay.rect(bx0, L.BOOTH_TOP - 6, bx1 - bx0, 6, 'D', 3.4, hgt=0.7)          # common cornice
        lay.rect(bx0 - 1, L.BOOTH_TOP - 6, bx1 - bx0 + 2, 1, 'D', 5.2, hgt=0.75)
        lay.rect(bx0, L.BOOTH_TOP - 1, bx1 - bx0, 1, 'D', 1.4, hgt=0.5)
        self.fire_cabinet(*L.FIRE_CAB)
        self.staff_door(*L.STAFF_DOOR)
        self.sconce(1772, 198, 'sconce_interp', energy=0.3, radius=60)
        self.agenda_board(1790, 116)
        lay.rect(x1 - 10, 0, 10, L.FLOOR, 'N', 1.0, hgt=0.9)                 # end wall
        lay.rect(x1 - 10, 0, 1, L.FLOOR, 'W', 3.0, hgt=0.8)

    def agenda_board(self, x, y):
        """Black felt board with white slide-in letters: the order of the day (procedure, not people)."""
        lay = self.lay
        rows = ['TAGESORDNUNG', '1 ERÖFFNUNG', '2 KORRIDORE', '3 GRENZVERKEHR', '4 ANLAGE C']
        w = max(kit.text_width(r) for r in rows) + 8
        h = 7 * len(rows) + 6
        frame_box(lay, x, y, w, h, 'B', 3.0, 4.6, 1.6)
        lay.rect(x, y, w, h, 'I', 0.8, hgt=0.4)
        for yy in range(y + 1, y + h - 1, 2):                                # felt grooves
            lay.rect(x + 1, yy, w - 2, 1, 'I', 1.2, hgt=0.38)
        for i, r in enumerate(rows):
            ty = y + 3 + i * 7 + (2 if i else 0)        # items 2 px lower: the distinct Ö's dots stay clear of the rule
            lay.text(r, x + 4, ty, 'P', 6.0 if i else 5.2, overhang=True)
        lay.rect(x + 4, y + 9, w - 8, 1, 'P', 3.6)                            # rule under the heading
        lay.px(x + w - 6, y + 5 + 4 * 7 + 1, 'R', 3.0)                        # a red pin at Anlage C (TOP 4)

    def etched_transom(self, x, y, w, h, idx):
        """Frosted Jugendstil transom between the corridor and the Grosser Saal (emissive cold glow)."""
        lay = self.lay
        rise = 14
        outer = kit.arch_mask(w + 8, h + 5, rise + 4)
        lay.put(outer, x - 4, y - 4, 'D', 3.0, hgt=0.7)                     # walnut surround
        lay.put(kit.edge_of(outer), x - 4, y - 4, 'D', 4.6, hgt=0.75)
        m = kit.arch_mask(w, h, rise)
        yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
        t = 4.75 - yy / h * 0.6 + (pg.value_noise(w, h, 7, 300 + idx, octaves=2) - 0.5) * 0.12
        # the blurred dark shape of a Saal chandelier behind the frosted glass
        cxs = w / 2 - 0.5
        blob = np.exp(-(((xx - cxs) / 9.0) ** 2 + ((yy - 24) / 6.0) ** 2))
        t = t - blob * 0.55
        lay.put(m, x, y, 'C', t, emis=True, flat=False, unlit=True)
        mid = w // 2
        bars = np.zeros((h, w), bool)
        bars[:, mid - 1:mid + 1] = True
        bars[int(h * 0.66):int(h * 0.66) + 2, :] = True
        bars &= m
        lay.put(bars, x, y, 'D', 3.4, hgt=0.6)
        lay.put(kit.edge_of(m), x, y, 'D', 2.6, hgt=0.6)
        # etched Jugendstil fan (clear rays read darker against the frost): rays from a half-sun at the
        # foot of the lower panes, a ring in the arch, a bright etched rim
        fy_ = int(h * 0.66)
        for k in range(7):
            a = math.pi * (k + 0.5) / 7
            for r_ in range(5, int(min(w * 0.5, fy_)) - 2):
                px_ = int(round(mid - 0.5 + math.cos(a) * r_ * (w * 0.5 / fy_)))
                py_ = int(round(fy_ - math.sin(a) * r_))
                if 0 <= px_ < w and 0 <= py_ < h and m[py_, px_] and not bars[py_, px_]:
                    lay.px(x + px_, y + py_, 'C', 3.0, emis=True, unlit=True, crisp=True)
        sun = (np.hypot((xx - mid + 0.5) * (fy_ / (w * 0.5)), yy - fy_) < 4.5) & (yy < fy_) & m & ~bars
        lay.put(sun, x, y, 'C', 3.0, emis=True, unlit=True, crisp=True)
        ring = (np.abs(np.hypot(xx - mid + 0.5, (yy - rise) * 1.1) - (w * 0.5 - 6)) < 0.6) & (yy < rise + 2) & m
        lay.put(ring & ~bars, x, y, 'C', 3.0, emis=True, unlit=True, crisp=True)
        for k in range(2, w - 2, 4):                                          # beaded band below the transom bar
            if m[fy_ + 4, k] and not bars[fy_ + 4, k]:
                lay.px(x + k, y + fy_ + 4, 'C', 3.0, emis=True, unlit=True, crisp=True)
        inner = m & ~kit.erode(m, 2) & ~kit.edge_of(m)
        lay.put(inner, x, y, 'C', 5.6, emis=True, unlit=True)
        lay.rect(x - 6, y + h + 1, w + 12, 3, 'M', 5.2, hgt=0.7)              # sill
        lay.rect(x - 6, y + h + 1, w + 12, 1, 'M', 6.2, hgt=0.75)
        lay.rect(x - 6, y + h + 4, w + 12, 1, 'W', 3.0)
        self.shaft_windows.append((m & ~bars, x, y, 0.5))
        self.lights.append({'name': 'transom_%d' % (idx + 1), 'pos': (x + w / 2, y + h * 0.55), 'kind': 'white',
                            'energy': 0.6, 'radius': 96, 'height': 26})

    def headset_cabinet(self, x0, x1):
        lay = self.lay
        top, bot = 196, 276
        w = x1 - x0
        lay.rect(x0, top, w, bot - top, 'D', 2.2, hgt=0.6)
        lay.rect(x0, top, w, 2, 'D', 4.6, hgt=0.7)
        lay.rect(x0, bot - 2, w, 2, 'D', 1.4, hgt=0.5)
        lay.rect(x0 + w, top + 1, 1, bot - top, 'W', 2.6)
        lay.text('KOPFHÖRER', x0 + (w - kit.text_width('KOPFHÖRER')) // 2, top - 8, 'B', 4.4, overhang=True)
        for r in range(3):
            for c in range(4):
                cx = x0 + 3 + c * 12
                cy = top + 4 + r * 24
                recess(lay, cx, cy, 11, 22, 'D', 1.0, shadow=0.6, light=2.4, hgt=-0.3)
                lay.rect(cx + 4, cy + 1, 3, 2, 'B', 3.8, hgt=0.6)            # number plate / hook
                if (r, c) in ((1, 2), (2, 0)):                               # hooks left empty
                    continue
                for a in range(200, 341, 20):                                # headband
                    rr = math.radians(a)
                    lay.px(int(round(cx + 5 + math.cos(rr) * 4)), int(round(cy + 8 + math.sin(rr) * 4.5)), 'I',
                           1.6, hgt=0.6)
                lay.rect(cx + 1, cy + 8, 2, 4, 'I', 1.4, hgt=0.6)            # earpieces
                lay.rect(cx + 8, cy + 8, 2, 4, 'I', 1.4, hgt=0.6)
                lay.px(cx + 1, cy + 8, 'S', 2.6)
                lay.px(cx + 8, cy + 8, 'S', 2.6)
                lay.line(cx + 2, cy + 12, cx + 4, cy + 18, 'I', 1.6)        # cable
                lay.rect(cx + 3, cy + 18, 3, 2, 'I', 2.0)
        for k in range(top + 4, bot - 4):                                    # glass sheen
            xx = x0 + 6 + (k - top) // 3
            if (k // 5) % 3 == 0 and xx < x1 - 2:
                lay.px(xx, k, 'S', 2.2, gain=0.6)

    def booth(self, x0, x1, idx):
        """Interpreter booth (cabin ~2.4 m): walnut casing, corridor-side glazing, interior (desk,
        console, lamp, chair), far window to the Grosser Saal (transparent -> saal layers)."""
        lay = self.lay
        top = L.BOOTH_TOP
        gy0, gy1 = L.BOOTH_GLASS
        wy0, wy1 = L.BOOTH_WIN
        dy = L.BOOTH_DESK_Y
        w = x1 - x0
        cx = (x0 + x1) // 2
        # casing
        lay.rect(x0 - 3, top, w + 6, L.FLOOR - top, 'D', 2.6, hgt=0.6)
        lay.rect(x0 - 3, top, 2, L.FLOOR - top, 'D', 4.0, hgt=0.6)
        lay.rect(x1 + 1, top, 2, L.FLOOR - top, 'D', 1.4, hgt=0.6)
        # number + language plate, 'besetzt' lamp
        plate = '%d  %s' % (idx + 1, ['FR', 'RU  DE', 'EN'][idx])
        pw = kit.text_width(plate) + 6
        lay.rect(cx - pw // 2, top + 3, pw, 9, 'P', 5.6, hgt=0.65)
        lay.rect(cx - pw // 2, top + 3, pw, 1, 'P', 6.6, hgt=0.7)
        lay.text(plate, cx - pw // 2 + 3, top + 5, 'I', 1.0)
        if idx == 1:   # two-way arrow between RU and DE
            ax = cx - pw // 2 + 3 + kit.text_width('2  RU') + 1
            for (xx, yy) in ((ax, top + 6), (ax + 1, top + 6), (ax + 2, top + 6), (ax + 3, top + 6), (ax + 3, top + 5),
                             (ax, top + 8), (ax + 1, top + 8), (ax + 2, top + 8), (ax + 3, top + 8), (ax, top + 9)):
                lay.px(xx, yy, 'I', 1.0, crisp=True)
        lx_ = x1 - 6
        if idx != 1:
            lay.rect(lx_, top + 4, 3, 3, 'R', 3.4, emis=True)
            self.lights.append({'name': 'busy_%d' % (idx + 1), 'pos': (lx_ + 1, top + 5), 'kind': 'warm',
                                'energy': 0.1, 'radius': 16, 'height': 4})
        else:
            lay.rect(lx_, top + 4, 3, 3, 'I', 2.0, hgt=0.7)
        # interior: acoustic far wall around the window to the Saal
        ix0, ix1 = x0 + 3, x1 - 3
        lay.rect(ix0, gy0, ix1 - ix0, gy1 - gy0, 'G', 1.6, hgt=-0.6)
        fx0, fx1 = x0 + 6, x1 - 6
        lay.rect(fx0 - 2, wy0 - 2, fx1 - fx0 + 4, wy1 - wy0 + 3, 'S', 1.6, hgt=-0.5)
        win = np.ones((wy1 - wy0, fx1 - fx0), bool)
        win[:, (fx1 - fx0) // 2] = False
        self.cut_glass(win, fx0, wy0, shaft=0.35)      # the daylit Saal throws cold light into the corridor
        lay.rect(fx0 + (fx1 - fx0) // 2, wy0, 1, wy1 - wy0, 'S', 1.4, hgt=-0.5)
        self.saal_windows.append((fx0, wy0, fx1, wy1))
        self.lights.append({'name': 'booth_glow_%d' % (idx + 1), 'pos': (cx, gy1 + 6), 'kind': 'white',
                            'energy': 0.5, 'radius': 66, 'height': 6})
        # desk top (seen slightly from above), console, microphone
        lay.rect(ix0, dy - 3, ix1 - ix0, 3, 'D', 4.0, hgt=0.6)
        lay.rect(ix0, dy - 3, ix1 - ix0, 1, 'D', 3.0, hgt=0.55)
        lay.rect(ix0, dy, ix1 - ix0, 3, 'D', 2.2, hgt=0.5)
        lay.rect(ix0, dy, ix1 - ix0, 1, 'B', 3.4, hgt=0.6)
        lay.rect(cx - 6, dy - 6, 12, 4, 'I', 1.6, hgt=0.7)                   # console
        lay.px(cx - 4, dy - 5, 'R', 3.4 if idx != 1 else 1.4, emis=idx != 1, crisp=True)   # live lamp
        for k in range(3):
            lay.px(cx - 1 + k * 2, dy - 5, 'S', 3.6, crisp=True)
        lay.line(cx + 4, dy - 6, cx + 7, dy - 12, 'S', 2.4)                  # gooseneck microphone
        lay.rect(cx + 6, dy - 14, 3, 2, 'I', 2.0)
        # booth lamp at the left end of the desk
        lx = ix0 + 4
        lay.rect(lx - 2, dy - 5, 6, 2, 'B', 3.0, hgt=0.7)
        lay.polyline([(lx, dy - 5), (lx - 1, dy - 11), (lx + 3, dy - 15)], 'B', 3.4, hgt=0.75)
        lit = idx == 1
        shade = [(lx + 1, dy - 18), (lx + 7, dy - 17), (lx + 8, dy - 14), (lx + 2, dy - 14)]
        lay.poly(shade, 'G', 3.4, hgt=0.8)
        if lit:
            lay.line(lx + 2, dy - 14, lx + 8, dy - 14, 'A', 5.0, emis=True)
            lay.rect(lx + 4, dy - 13, 3, 1, 'A', 4.6, emis=True)
            self.lights.append({'name': 'booth_2_lamp', 'pos': (lx + 5, dy - 12), 'kind': 'warm', 'energy': 1.4,
                                'radius': 110, 'height': 10, 'cone': (0.25, 1.0, -0.25)})
        else:
            lay.line(lx + 2, dy - 14, lx + 8, dy - 14, 'A', 2.4, emis=True)
            self.lights.append({'name': 'booth_%d_lamp' % (idx + 1), 'pos': (lx + 5, dy - 12), 'kind': 'warm',
                                'energy': 0.4, 'radius': 46, 'height': 8, 'cone': (0.25, 1.0, -0.25)})
        if idx == 1:
            # Elena's booth: blotter pad (her last note pressed through), pencil, headset dangling off the
            # desk edge on its cable, the chair pushed back and turned, no notebook
            lay.rect(cx + 9, dy - 3, 12, 3, 'P', 4.6, hgt=0.65)
            lay.rect(cx + 9, dy - 3, 12, 1, 'P', 5.8, hgt=0.7)
            lay.rect(cx + 8, dy - 3, 1, 3, 'D', 1.6)
            lay.line(cx + 11, dy - 4, cx + 17, dy - 5, 'B', 4.6)
            lay.px(cx + 17, dy - 5, 'I', 1.0)
            lay.rect(cx - 17, dy - 2, 5, 1, 'I', 1.2, hgt=0.7)              # headset band on the edge
            lay.line(cx - 14, dy + 1, cx - 15, dy + 7, 'I', 1.4)
            lay.rect(cx - 18, dy + 7, 2, 3, 'I', 1.6, hgt=0.6)              # earpieces dangling
            lay.rect(cx - 14, dy + 7, 2, 3, 'I', 1.6, hgt=0.6)
            lay.px(cx - 18, dy + 7, 'S', 3.4)
            ch = cx - 2                                                     # chair pushed back, empty
            lay.rect(ch - 7, dy - 8, 13, 10, 'D', 3.0, hgt=0.7)
            lay.rect(ch - 7, dy - 8, 13, 1, 'D', 4.6, hgt=0.75)
            lay.rect(ch - 6, dy - 6, 11, 1, 'D', 2.0)
            lay.rect(ch - 8, dy + 4, 15, 2, 'D', 3.6, hgt=0.6)
            lay.rect(ch - 6, dy + 6, 2, 6, 'D', 2.0)
            lay.rect(ch + 3, dy + 6, 2, 6, 'D', 2.0)
        else:
            lay.rect(cx + 9, dy - 3, 9, 2, 'P', 5.6, hgt=0.65)              # papers, cup, headset
            lay.rect(cx + 11, dy - 4, 9, 2, 'P', 6.0, hgt=0.66)
            lay.rect(ix0 + 12, dy - 5, 3, 3, 'P', 5.0, hgt=0.7)
            ch = cx
            lay.rect(ch - 7, dy - 6, 14, 10, 'D', 3.0, hgt=0.7)             # chair pushed in
            lay.rect(ch - 7, dy - 6, 14, 1, 'D', 4.6, hgt=0.75)
            lay.rect(ch - 6, dy - 4, 12, 1, 'D', 2.0)
            if idx == 0:      # a cardigan over the chair back
                lay.rect(ch - 7, dy - 6, 6, 9, 'W', 5.0, hgt=0.75)
                lay.rect(ch - 7, dy - 6, 6, 1, 'W', 6.0)
            if idx == 2:      # a headset laid on the desk
                lay.rect(cx - 16, dy - 4, 6, 2, 'I', 1.4, hgt=0.65)
        # corridor-side glazing: frame, sheen streaks, door with a handle
        lay.rect(x0, gy0 - 2, w, 2, 'D', 3.6, hgt=0.7)
        lay.rect(x0, gy1, w, 2, 'D', 4.0, hgt=0.7)
        lay.rect(x0, gy0, 2, gy1 - gy0, 'D', 3.2, hgt=0.7)
        lay.rect(x1 - 2, gy0, 2, gy1 - gy0, 'D', 2.2, hgt=0.7)
        door = x0 + w * 2 // 3
        lay.rect(door, gy0, 2, gy1 - gy0, 'D', 3.0, hgt=0.7)
        for k in range(0, gy1 - gy0):
            for off in (5, 8):
                xx = x0 + off + k // 3
                yy = gy0 + k
                if (k // 6) % 3 != 2 and xx < x1 - 3 and not (fx0 <= xx < fx1 and wy0 <= yy < wy1):
                    lay.px(xx, yy, 'S', 2.2 if off == 5 else 1.8, gain=0.5)
        lay.rect(door + 3, gy1 + 4, 4, 2, 'B', 4.4, hgt=0.9)                   # handle
        lay.rect(door + 3, gy1 + 4, 1, 3, 'B', 3.6, hgt=0.9)
        # lower panel + kick plate
        bevel(lay, x0 + 2, gy1 + 2, w - 4, L.FLOOR - gy1 - 8, 'D', 2.8, hi=4.0, lo=1.4, hgt=0.4)
        lay.rect(x0, L.FLOOR - 5, w, 5, 'B', 2.6, hgt=0.5)
        lay.rect(x0, L.FLOOR - 5, w, 1, 'B', 4.0, hgt=0.55)

    def fire_cabinet(self, x0, x1):
        lay = self.lay
        top, bot = 222, 264
        lay.rect(x0, top, x1 - x0, bot - top, 'R', 2.4, hgt=0.6)
        lay.rect(x0, top, x1 - x0, 1, 'R', 3.4, hgt=0.65)
        lay.rect(x0 + 2, top + 9, x1 - x0 - 4, bot - top - 12, 'R', 2.0, hgt=0.5)
        lay.text('FEUER', x0 + (x1 - x0 - kit.text_width('FEUER')) // 2, top + 2, 'P', 6.0)
        for a in range(0, 360, 20):                                          # hose reel behind the glass
            r = math.radians(a)
            lay.px(int(round((x0 + x1) / 2 + math.cos(r) * 7)), int(round(top + 22 + math.sin(r) * 7)), 'I', 1.6)
        lay.rect(x1 - 4, top + 16, 2, 8, 'B', 4.0, hgt=0.8)

    def staff_door(self, x0, x1):
        lay = self.lay
        top = 222
        lay.rect(x0 - 4, top - 5, x1 - x0 + 8, L.FLOOR - top + 5, 'W', 5.0, hgt=0.5)
        lay.rect(x0 - 4, top - 5, x1 - x0 + 8, 1, 'W', 6.4, hgt=0.55)
        lay.rect(x0, top, x1 - x0, L.FLOOR - top, 'D', 2.2, hgt=0.3)
        bevel(lay, x0 + 4, top + 5, x1 - x0 - 8, 26, 'D', 2.8, hi=3.8, lo=1.2, hgt=0.4)
        bevel(lay, x0 + 4, top + 36, x1 - x0 - 8, L.FLOOR - top - 42, 'D', 2.8, hi=3.8, lo=1.2, hgt=0.4)
        lay.rect(x1 - 7, top + 32, 3, 2, 'B', 4.4, hgt=0.9)
        pw = kit.text_width('NUR PERSONAL') + 4
        sx = (x0 + x1) // 2 - pw // 2
        lay.rect(sx, top - 16, pw, 9, 'P', 6.0, hgt=0.6)
        lay.text('NUR PERSONAL', sx + 2, top - 14, 'I', 1.0)
        lay.text('UG', x0 + 4, top + 10, 'P', 5.0)                           # down to the cellar
        lay.px(x0 + 13, top + 12, 'P', 5.0); lay.px(x0 + 14, top + 13, 'P', 5.0); lay.px(x0 + 15, top + 12, 'P', 5.0)

    # ------------------------------------------------------------------ floor
    def floor(self):
        lay = self.lay
        W, H = L.WORLD_W, L.WORLD_H
        y0 = L.FLOOR
        rows = [0, 3, 7, 12, 18, 25, 33, 42, 52, 63, 75]
        rowidx = np.searchsorted(np.array(rows) + y0, np.arange(H), side='right') - 1
        ys = np.arange(H, dtype=np.float32)[:, None]
        xs = np.arange(W, dtype=np.float32)[None, :]
        f = np.maximum((ys - L.HORIZON) / (L.FLOOR - L.HORIZON), 1e-3)
        # --- marble chequer (vestibule + foyer): cream and sage-grey marble, per-room perspective.
        # Low contrast on purpose (the Berlin hall uses half a tone step): the polish -- reflections of the
        # walls, the lamps and the daylight -- carries the floor, not a loud black-and-white board.
        mx1 = L.PART2[0]
        vein = noise(W, H, 14, 91, octaves=3)
        vein2 = noise(W, H, 5, 93, octaves=2)
        for (rx0, rx1) in ((0, L.ARCH1[1]), (L.ARCH1[1], mx1)):
            vp = (rx0 + rx1) / 2
            u = vp + (xs - vp) / f
            col = np.floor(u / L.TILE).astype(np.int32)
            joint = np.zeros_like(col, bool)
            joint[:, 1:] = col[:, 1:] != col[:, :-1]
            chk = ((col + rowidx[:, None]) % 2) == 0
            m = np.zeros((H, W), bool)
            m[y0 + 4:, rx0:rx1] = True
            light = m & chk
            dark = m & ~chk
            vn = (np.abs(vein) < 0.028) | (np.abs(vein2) < 0.012)
            tl = 4.05 + vn * 0.55 - (vein > 0.24) * 0.3
            td = 5.0 + vn * 0.6 - (vein < -0.24) * 0.4
            lay.put(light, 0, 0, 'M', tl, hgt=0.0, flat=True)
            lay.put(dark, 0, 0, 'G', td, hgt=0.0, flat=True)
            lay.put(m & joint & chk, 0, 0, 'M', 3.4, hgt=0.0, flat=True)
            lay.put(m & joint & ~chk, 0, 0, 'G', 4.2, hgt=0.0, flat=True)
        for i in range(1, len(rows) - 1):
            ry = y0 + rows[i]
            row = lay.rid[ry, 0:mx1]
            seg = np.where(row == R['M'], 3.5, 4.3).astype(np.float32)
            lay.put(np.ones((1, mx1), bool), 0, ry, None, seg[None, :])
        # verde border band along the wall (with a brass inlay line) + doormat at the revolving door
        lay.rect(0, y0, mx1, 4, 'G', 3.6, hgt=0.0)
        lay.rect(0, y0, mx1, 1, 'G', 2.4, hgt=0.0)
        lay.rect(0, y0 + 4, mx1, 1, 'B', 3.4, hgt=0.0)
        rx0, rx1 = L.REVOLVING
        for yy in range(y0 + 1, y0 + 14):
            k = yy - y0
            a = rx0 - 6 - k // 2
            b = rx1 + 6 + k // 2
            lay.rect(a, yy, b - a, 1, 'D', 3.4 + ((yy + a) % 2) * 0.6, hgt=0.0)
        lay.rect(rx0 - 13, y0 + 14, rx1 - rx0 + 26, 1, 'D', 1.6)
        # melt water tracked in from the snow (revolving door -> cloakroom -> archway), and the freshly mopped,
        # still glossy patch where the cleaner works in the archway (env_veltrava_hall_life.cleaner)
        rngw = np.random.default_rng(1953)
        for k in range(26):
            sx = 96 + k * 12 + int(rngw.integers(-3, 4))
            sy = y0 + 8 + int(rngw.integers(0, 8)) + (k % 2) * 2
            if sx > 392:
                break
            lay.shade_rect(sx, sy, 3, 1, -0.7 + k * 0.012)
            lay.shade_rect(sx + 1, sy - 1, 1, 1, 1.0)
        for yy in range(y0 + 5, y0 + 18):
            half = int(26 * math.sqrt(max(0.0, 1 - ((yy - y0 - 11) / 7.0) ** 2)))
            for xx in range(404 - half, 404 + half):
                if (xx + yy) % 2 == 0:
                    lay.shade_rect(xx, yy, 1, 1, 0.55)
        # --- office: walnut herringbone parquet
        ox0, ox1 = L.PART2[0], L.PART3[1]
        for i in range(len(rows) - 1):
            ra, rb = y0 + rows[i], y0 + rows[i + 1]
            hgt_row = rb - ra
            vp = (ox0 + ox1) / 2
            fr = (ra + 1 - L.HORIZON) / (L.FLOOR - L.HORIZON)
            span = max(3, int(round(14 * fr)))
            for x in range(ox0, ox1):
                ub = int(math.floor((vp + (x - vp) / fr) / 14))
                k = (x - ox0) % (2 * span)
                t = 2.8 + (0.6 if ub % 2 else 0.0)
                lay.rect(x, ra, 1, hgt_row, 'D', t, hgt=0.0)
            for x in range(ox0, ox1):
                ub = int(math.floor((vp + (x - vp) / fr) / 14))
                ub2 = int(math.floor((vp + (x + 1 - vp) / fr) / 14))
                if ub != ub2:
                    for yy in range(ra + 1, rb):
                        lay.px(x + ((yy - ra) * (1 if ub % 2 else -1)) // 3, yy, 'D', 1.8)
            lay.rect(ox0, ra, ox1 - ox0, 1, 'D', 1.6, hgt=0.0)
        # --- interpreters' corridor: wine-dark carpet with a border
        ix0 = L.PART3[1]
        # wine-dark wool: painted on the walnut ramp (same base colour #331F16) so lamp light lifts it to a
        # warm brown pool instead of a saturated red one.  A calm woven pattern in perspective (small
        # lozenges on a grid, every row of the floor one course) instead of loose speckle; the wine accents
        # are the border bands.
        lay.rect(ix0, y0, W - ix0, H - y0, 'D', 2.2, hgt=0.0, gain=0.9)
        vpc = (ix0 + W) / 2
        uc = vpc + (xs - vpc) / f
        cell = np.floor(uc / 12).astype(np.int32)
        fu = (uc / 12) - cell
        fv = np.zeros_like(fu)
        for i in range(len(rows) - 1):
            ra, rb = y0 + rows[i], y0 + rows[i + 1]
            fv[ra:min(rb, H), :] = ((np.arange(ra, min(rb, H)) - ra + 0.5) / max(1, rb - ra))[:, None]
        loz = (np.abs(fu - 0.5) + np.abs(fv - 0.5)) < 0.22
        cm = np.zeros((H, W), bool)
        cm[y0 + 6:, ix0:] = True
        lay.put(cm & loz & (((cell + rowidx[:, None]) % 2) == 0), 0, 0, 'R', 1.75, hgt=0.0)
        lay.put(cm & loz & (((cell + rowidx[:, None]) % 2) == 1), 0, 0, 'D', 2.9, hgt=0.0)
        pile = pg.white_noise(W - ix0, H - y0, 5) > 0.93
        lay.put(pile & cm[y0:, ix0:], ix0, y0, 'D', 2.7, hgt=0.0)
        for (by, rmp, t) in ((y0 + 1, 'R', 2.2), (y0 + 2, 'R', 2.6), (y0 + 3, 'D', 1.4), (y0 + 5, 'R', 2.0),
                             (y0 + 33, 'R', 2.2), (y0 + 34, 'R', 1.8)):
            lay.rect(ix0, by, W - ix0, 1, rmp, t, hgt=0.0)
        for x in range(ix0, W, 6):
            lay.px(x, y0 + 4, 'B', 2.4)
        # thresholds where the floors meet (dark stone sill between two brass strips) so the change of
        # material reads as a doorway, not as a seam; kept darker than both floors so it never glows
        for (tx0, tx1) in (L.PART2, L.PART3):
            vpt = (tx0 + tx1) / 2
            for i in range(len(rows) - 1):
                ra, rb = y0 + rows[i], min(H, y0 + rows[i + 1])
                fr = (ra + 1 - L.HORIZON) / (L.FLOOR - L.HORIZON)
                a = int(round(vpt + (tx0 + 2 - vpt) * fr))
                b = int(round(vpt + (tx1 - 2 - vpt) * fr))
                lay.rect(a, ra, b - a, rb - ra, 'D', 1.7, hgt=0.05)
                lay.rect(a, ra, b - a, 1, 'D', 1.1, hgt=0.05)
                lay.rect(a - 1, ra, 1, rb - ra, 'B', 2.6, hgt=0.12)
                lay.rect(b, ra, 1, rb - ra, 'B', 2.2, hgt=0.12)
        # contact shadow along the wall
        lay.rect(0, y0, W, 1, 'W', 1.2)
        lay.shade_rect(0, y0 + 1, W, 3, -0.6)
        m = np.zeros((H, W), bool)
        m[y0:, :] = lay.rid[y0:, :] >= 0
        lay.paint_normal(m, 0, 0, (0.0, 0.86, 0.5))
        fall = np.zeros((H, W), np.float32)
        fall[:] = (np.clip((np.arange(H, dtype=np.float32) - 318) / 42, 0, 1) * -1.2)[:, None]
        lay.amb_field(fall)

    # ------------------------------------------------------------------ ambient
    def ambient(self):
        lay = self.lay
        W, H = L.WORLD_W, L.WORLD_H
        f = np.zeros((H, W), np.float32)
        xs = np.arange(W, dtype=np.float32)
        reg = np.zeros(W, np.float32)
        reg[L.OFFICE[0]:] = -0.4
        reg[L.INTERP[0]:] = -0.75
        k = np.ones(25, np.float32) / 25
        reg = np.convolve(np.pad(reg, 12, mode='edge'), k, mode='valid')
        f += reg[None, :]
        ys = np.arange(H, dtype=np.float32)[:, None]
        f += -0.9 * np.clip((140 - ys) / 110, 0, 1)
        f += -1.0 * np.clip((40 - xs) / 30, 0, 1)[None, :]
        f += -1.0 * np.clip((xs - (W - 40)) / 30, 0, 1)[None, :]
        f[lay.emis] = 0
        lay.amb_field(f)

    # ------------------------------------------------------------------ build
    def build(self):
        self.base()
        self.vestibule()
        self.open_arch(L.ARCH1[0], L.ARCH1[1], 104)
        self.foyer()
        self.arch_cut(L.PART2[0], L.PART2[1], 196)
        self.office()
        self.arch_cut(L.PART3[0], L.PART3[1], 200)
        self.interp()
        self.floor()
        self.ambient()
        return self.lay


# =========================================================================== shafts
def window_shafts(sources, w=L.WORLD_W, h=L.WORLD_H, ax=0.85, kz=0.32):
    """Volumetric daylight from back-wall glass (3-D rays projected to the side view).
    Returns (air density, floor landing), both ~[0, 1].
    Sources are normalised PER ROOM (vestibule / foyer / office / interpreters): the huge entrance
    glazing must not drown the single foyer window or the office window, and every room keeps a
    readable shaft; the strongest source strength of a room sets that room's peak."""
    air = np.zeros((h, w), np.float32)
    land = np.zeros((h, w), np.float32)
    rooms = (L.VEST[1], L.FOYER[1], L.OFFICE[1], L.WORLD_W)
    groups: dict = {}
    for src in sources:
        gi = next(i for i, lim in enumerate(rooms) if src[1] < lim)
        groups.setdefault(gi, []).append(src)
    for gi, srcs in sorted(groups.items()):
        g_air = np.zeros((h, w), np.float32)
        g_land = np.zeros((h, w), np.float32)
        peak = 0.0
        for (mask, x0, y0, strength) in srcs:
            gy, gx = np.nonzero(mask)
            if len(gx) == 0:
                continue
            peak = max(peak, float(strength))
            sub = max(1, len(gx) // 3000)
            gy, gx = gy[::sub], gx[::sub]
            xg = gx.astype(np.float32) + x0 + 0.5
            yg = gy.astype(np.float32) + y0 + 0.5
            tend = (L.FLOOR - yg) / (1 + kz)
            tmax = int(tend.max()) + 1
            wgt = strength * sub
            for t in range(0, tmax):
                alive = tend > t
                if not alive.any():
                    break
                sx = np.round(xg[alive] + ax * t).astype(np.int32)
                sy = np.round(yg[alive] + t * (1 + kz)).astype(np.int32)
                ok = (sx >= 0) & (sx < w) & (sy >= 0) & (sy < h)
                np.add.at(g_air, (sy[ok], sx[ok]), wgt)
            lx = np.round(xg + ax * tend).astype(np.int32)
            ly = np.round(L.FLOOR + kz * tend * 0.9).astype(np.int32)
            ok = (lx >= 0) & (lx < w) & (ly >= 0) & (ly < h)
            np.add.at(g_land, (ly[ok], lx[ok]), wgt)
        g_air = kit.box_blur(g_air, 2)
        g_land = kit.box_blur(g_land, 2)
        if (g_air > 0).any():
            g_air *= peak / max(1e-6, np.percentile(g_air[g_air > 0], 99.0))
        if (g_land > 0).any():
            g_land *= peak / max(1e-6, np.percentile(g_land[g_land > 0], 96))
        air = np.maximum(air, g_air)
        land = np.maximum(land, g_land)
    return np.clip(air, 0, 1.2), np.clip(land, 0, 1.2)


# =========================================================================== lights
def scene_lights(room: Room):
    """Daylight / glow sources not built by a room element (world coords)."""
    out = [
        {'name': 'entrance_day', 'pos': (62, 170), 'kind': 'cold', 'energy': 1.0, 'radius': 190, 'height': -10},
        {'name': 'foyer_window', 'pos': ((L.WINDOW[0] + L.WINDOW[1]) / 2, 170), 'kind': 'cold', 'energy': 0.9,
         'radius': 150, 'height': -10},
        {'name': 'office_window', 'pos': ((L.OFFICE_WIN[0] + L.OFFICE_WIN[1]) / 2, 160), 'kind': 'cold',
         'energy': 0.6, 'radius': 110, 'height': -10},
    ]
    for i, (a, b) in enumerate(L.LUNETTES):
        out.append({'name': 'lunette_%d' % (i + 1), 'pos': ((a + b) / 2, 46), 'kind': 'cold', 'energy': 0.6,
                    'radius': 120, 'height': -6})
    for i, (fx0, wy0, fx1, wy1) in enumerate(room.saal_windows):
        out.append({'name': 'saal_glow_%d' % (i + 1), 'pos': ((fx0 + fx1) / 2, (wy0 + wy1) / 2), 'kind': 'white',
                    'energy': 0.55, 'radius': 64, 'height': -4})
    return out


def bake(room: Room, extra_lights=None):
    lay = room.lay
    lights = scene_lights(room) + room.lights + (extra_lights or [])
    F = kit.light_fields(lay, lights)
    air, land = window_shafts(room.shaft_windows)
    room.shaft_air, room.shaft_land = air, land
    floor = np.zeros_like(air)
    floor[L.FLOOR:, :] = 1.0
    F['cold'] += (air ** 0.85) * 0.55 + land * floor * 0.9
    # warm lamp pools on the polished floors
    for lt in lights:
        if lt['kind'] == 'warm' and lt.get('pool'):
            x = int(lt['pos'][0])
            for yy in range(L.FLOOR + 1, L.FLOOR + 44):
                k = (1 - (yy - L.FLOOR) / 44) ** 1.5
                hw = 4 + int((yy - L.FLOOR) * 0.4)
                F['warm'][yy, max(0, x - hw):x + hw + 1] += 0.3 * k * lt['energy']
    room.fields = F
    room.all_lights = lights
    lay.resolve(F)
    return room


# =========================================================================== reflections
def reflect_floor(room: Room, props=(), strength=0.34, x_ranges=None):
    """Dithered mirror reflection of the lower walls + props in the polished marble (vestibule, foyer)
    and, weaker, the waxed parquet (office).  Works on the resolved RGBA in place (palette-pure)."""
    lay = room.lay
    W, H = L.WORLD_W, L.WORLD_H
    y0 = L.FLOOR
    src = lay.c.copy()
    # props standing on the floor are part of what the floor mirrors
    for p in props:
        if p.base_y > L.WALK_BAND[1] or getattr(p, 'no_reflect', False):
            continue
        a = p.lay.c[..., 3] > 0
        ys, xs = np.nonzero(a)
        for yy, xx in zip(ys, xs):
            X, Y = p.x + xx, p.y + yy
            if 0 <= X < W and 0 <= Y < y0:
                src[Y, X] = p.lay.c[yy, xx]
    thr = pg.bayer(W, H, 1, 2, 4)
    out = lay.c
    ranges = x_ranges or [((0, L.PART2[0]), strength), ((L.PART2[1], L.PART3[0]), strength * 0.55)]
    # luminance-ordered palette per ramp to darken reflected pixels by one step
    pal = np.array([pg.hx(h)[:3] for h in sorted(kit.palais_hex())], np.int32)
    lumv = pal @ np.array([0.2126, 0.7152, 0.0722])
    for (rx0, rx1), s in ranges:
        for yy in range(y0 + 1, H):
            d = yy - y0
            sy = y0 - d - 1
            if sy < 0:
                break
            fade = s * max(0.0, 1 - d / 64.0) ** 1.2
            if fade <= 0.01:
                continue
            row_src = src[sy, rx0:rx1]
            okm = (row_src[:, 3] > 0) & (out[yy, rx0:rx1, 3] > 0) & (thr[yy, rx0:rx1] < fade)
            if not okm.any():
                continue
            cols = row_src[okm][:, :3].astype(np.int32)
            dst = out[yy, rx0:rx1][okm][:, :3].astype(np.int32)
            # mix toward the reflected colour: choose the palette entry nearest to 55% src + 45% floor
            mixc = cols * 0.55 + dst * 0.45
            dd = ((mixc[:, None, :] - pal[None, :, :]) ** 2).sum(-1)
            pick = pal[np.argmin(dd, axis=1)]
            seg = out[yy, rx0:rx1]
            seg_rgb = seg[..., :3]
            seg_rgb[okm] = pick.astype(np.uint8)
            out[yy, rx0:rx1, :3] = seg_rgb
    lay.c = out
    return room
