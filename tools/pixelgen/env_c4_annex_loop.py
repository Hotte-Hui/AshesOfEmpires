"""env_c4_annex_loop -- the street layers of L_C4_AnnexA 'Wendeschleife Sued 8' (Berlin, 16 Feb 1964, ~5.10).

Painted in tone space (env_c4_annex_kit, hue world 'loop'): blue dawn on stucco and snow, sodium light under the
span wire turns snow and stone yellow-cream, the tram and Marta's window glow warm.
    sky        night -> dawn gradient, low stratus, the last stars                 (parallax 0.03, unlit)
    dome       the Great Hall far away in the haze (+ _hist banners, 12.4)          (parallax 0.08, unlit)
    far        the axis under construction: building shells, tower cranes          (parallax 0.2, unlit)
    mid        cleared blocks: the last tenements, site huts, an excavator          (parallax 0.5, unlit)
    loop       the playfield street 0..846: house No. 11 (lived in), No. 9 gutted with three storeys of wallpaper
               on the exposed wall, the shelter with the lit timetable case, tram 74 in the loop, the advertising
               column S 2, the freight hatch with the crates C-17/45, the lorry, the site hoarding  (lit)
    fg_loop    snow banks, a bollard, the stop post in near-black silhouette          (parallax 1.25)
Story states (cfg): 'routes' (Konrad's tracing sheets on the timetable case), 'bared' (poster of S 2 peeled back,
the steel door), 'hist' (historical insignia at the official sites).
"""
from __future__ import annotations

import math

import numpy as np

import env_c4_annex_kit as K
import env_c4_annex_layout as L
import pg

W = L.SEAM
H = L.WORLD_H
B = L.BASE_Y


def snowcap(lay, x, y, w, depth=2, seed=0, drip=0.25, tone=6.2):
    """Snow on an upward edge at y (the cap sits on y-depth .. y-1), soft irregular top, a few drips below."""
    rng = np.random.default_rng(seed)
    for i in range(int(w)):
        d = depth + (1 if rng.random() < 0.3 else 0) - (1 if rng.random() < 0.15 else 0)
        if i == 0 or i == w - 1:
            d = max(1, d - 1)
        for k in range(max(1, d)):
            lay.px(x + i, y - 1 - k, 'SN', tone - 0.9 * (k == 0 and d > 1) + 0.6 * (k == d - 1), hgt=0.5)
        if rng.random() < drip * 0.25:
            lay.px(x + i, y, 'SN', tone - 2.0, hgt=0.2)


class Street:
    def __init__(self, cfg: dict | None = None):
        self.cfg = cfg or {}
        self.lay = K.tlayer(W, H, 'loop', 'loop')
        self.lights: list[dict] = []
        self.hist = bool(self.cfg.get('hist', False))

    def light(self, name, pos, kind, energy, radius, height=24, **kw):
        d = {'name': name, 'pos': (float(pos[0]), float(pos[1])), 'kind': kind, 'energy': energy,
             'radius': radius, 'height': height}
        d.update(kw)
        self.lights.append(d)
        return d

    # ================================================================== the cleared lot behind the loop
    def lot(self):
        lay = self.lay
        x0 = L.HOUSE9[1] - 4
        nz = pg.value_noise(W, 60, 18, 41, octaves=3)
        top = np.zeros(W, np.float32)
        for x in range(x0, W):
            top[x] = 243 + 5 * math.sin(x * 0.021) + 3 * math.sin(x * 0.067 + 1.3) + (nz[10, x] - 0.5) * 6
        for x in range(x0, W):
            ty = int(top[x])
            for y in range(ty, B + 2):
                d = (y - ty) / max(1.0, B - ty)
                t = 4.9 - 0.9 * d + (nz[min(59, y - 228), x] - 0.5) * 1.3
                lay.px(x, y, 'SN', t, flat=False, hgt=0.15 + 0.2 * (1 - d))
            lay.px(x, ty, 'SN', 5.8, hgt=0.4)
        rng = np.random.default_rng(7)
        # rubble mounds, foundation stubs and a heap of salvaged bricks
        for cx, w_, h_ in ((236, 30, 12), (330, 44, 8), (612, 36, 10), (700, 28, 7)):
            for i in range(w_):
                hh = int(h_ * math.sin(math.pi * (i + 0.5) / w_) ** 0.8)
                for k in range(hh):
                    lay.px(cx - w_ // 2 + i, B - 4 - k, 'SN', 4.2 + k / max(1, hh) * 1.8 - (i > w_ * 0.6) * 0.8,
                           flat=False, hgt=0.6)
        for fx0, fw, fy in ((262, 70, 262), (430, 120, 256), (560, 60, 268)):
            lay.rect(fx0, fy, fw, 3, 'K', 2.4, hgt=0.5)
            lay.rect(fx0, fy + 3, fw, 1, 'K', 1.2)
            snowcap(lay, fx0, fy, fw, 2, seed=fx0)
        for i in range(26):
            bx, by = 664 + int(rng.integers(0, 22)), B - 3 - int(rng.integers(0, 8))
            lay.rect(bx, by, 3, 1, 'K', 2.5 + rng.random(), hgt=0.4)
        # tyre tracks of the lorry towards the hatch
        for k in range(2):
            for x in range(560, 712):
                y = int(B - 6 - (x - 560) * 0.07) + k * 4
                lay.px(x, y, 'SN', 3.2, hgt=0.05)

    # ================================================================== the lone street tree
    def tree(self, x0=586, base=L.BASE_Y - 2, top=78):
        lay = self.lay
        rng = np.random.default_rng(1964)
        lay.rect(x0 - 2, top + 70, 5, base - top - 70, 'I', 1.6, hgt=0.7)
        lay.vline(x0 - 2, top + 70, base - top - 70, 'I', 2.4, hgt=0.6)

        def branch(x, y, ang, ln, wd, depth):
            x1 = x + math.cos(ang) * ln
            y1 = y - math.sin(ang) * ln
            n = max(1, int(ln))
            for i in range(n + 1):
                t = i / n
                px, py = x + (x1 - x) * t, y + (y1 - y) * t
                ww = max(1, int(round(wd * (1 - 0.5 * t))))
                lay.rect(int(px) - ww // 2, int(py), ww, 1, 'I', 1.4 + 0.3 * (ww > 1), hgt=0.5)
                if ww >= 1 and math.sin(ang) > 0.2 and rng.random() < 0.35:
                    lay.px(int(px), int(py) - 1, 'SN', 5.6, hgt=0.6)
            if depth > 0:
                for d_ang in (-0.42 - rng.random() * 0.2, 0.36 + rng.random() * 0.25):
                    branch(x1, y1, ang + d_ang, ln * (0.62 + rng.random() * 0.12), wd * 0.6, depth - 1)
        branch(x0, top + 74, math.pi / 2 + 0.05, 34, 4, 5)
        branch(x0, top + 98, math.pi / 2 + 0.7, 26, 3, 4)
        branch(x0, top + 92, math.pi / 2 - 0.6, 28, 3, 4)

    # ================================================================== house No. 11 (lived in)
    def house11(self):
        lay = self.lay
        x0, x1 = L.HOUSE11
        w = x1 - x0
        nz = pg.value_noise(w, H, 7, 11, octaves=3)
        streak = pg.value_noise(w, 8, 3, 12, octaves=2)
        for y in range(L.CORNICE_11[0], B):
            row = 4.2 + (nz[y, :] - 0.5) * 0.7 - (streak[(y // 45) % 8, :] - 0.5) * 0.8 - 0.4 * (y < 120)
            for x in range(w):
                lay.px(x0 + x, y, 'W', row[x], flat=False, hgt=0.2)
        # rusticated ground floor
        for y in range(L.STOREYS_11[0][0], B, 6):
            lay.hline(x0, y, w, 'W', 2.6, hgt=0.0)
            lay.hline(x0, y + 1, w, 'W', 5.4, hgt=0.35)
        # storey cornices
        for (ya, yb) in L.STOREYS_11[1:] + [L.STOREYS_11[0]]:
            lay.rect(x0, yb - 3, w, 2, 'W', 6.2, hgt=0.8)
            lay.rect(x0, yb - 1, w, 1, 'W', 2.2, hgt=0.3)
            snowcap(lay, x0, yb - 3, w, 2, seed=yb)
        # main cornice with dentils and the mansard roof
        cy0, cy1 = L.CORNICE_11
        lay.rect(x0, cy0, w + 2, cy1 - cy0, 'W', 5.8, hgt=1.0)
        for x in range(x0, x1, 4):
            lay.rect(x, cy1 - 4, 2, 2, 'W', 3.0, hgt=0.6)
        lay.rect(x0, cy1 - 1, w + 2, 1, 'W', 2.0)
        snowcap(lay, x0, cy0, w + 2, 3, seed=3)
        for y in range(30, cy0 - 2):
            inset = int((cy0 - y) * 0.35)
            for x in range(x0, x1 - inset):
                lay.px(x, y, 'S', 2.6 + ((x + y // 3) % 5 == 0) * 0.8 - (y < 36) * 0.4, hgt=0.4)
        for x in range(x0, x1 - 6):
            lay.px(x, 29, 'SN', 5.5, hgt=0.6)
            lay.px(x, 28 + (x % 7 == 0), 'SN', 6.2, hgt=0.6)
        # dormer and chimney
        lay.rect(30, 34, 14, 16, 'W', 4.6, hgt=0.7)
        lay.rect(33, 38, 8, 10, 'D', 1.4)
        lay.rect(36, 38, 1, 10, 'S', 2.2)
        snowcap(lay, 29, 34, 16, 2, seed=5)
        lay.rect(12, 12, 9, 20, 'K', 2.6, hgt=0.8)
        lay.rect(11, 10, 11, 3, 'K', 3.6, hgt=0.9)
        snowcap(lay, 11, 10, 11, 2, seed=6)
        # windows
        for si, (ya, yb) in enumerate(L.STOREYS_11[1:]):
            for wx in (12, 52):
                lit = None
                if si == 0 and wx == 52:
                    lit = 'marta'
                elif si == 1 and wx == 12:
                    lit = 'dim'
                self.altbau_window(wx, ya + 8, 16, 26 if si < 3 else 22, lit=lit, seed=si * 7 + wx,
                                   pediment=si == 0)
        # ground floor: shuttered shop + the house door of No. 11
        lay.rect(6, 248, 36, 36, 'S', 2.4, hgt=0.3)
        for y in range(250, 284, 2):
            lay.hline(7, y, 34, 'S', 3.4 if y % 4 == 0 else 1.8, hgt=0.2)
        lay.rect(6, 246, 36, 2, 'W', 6.0, hgt=0.6)
        K.text(lay, 'KOHLEN', 9, 240, 'P', 1.2)
        lay.rect(54, 242, 24, 46, 'W', 2.8, hgt=0.4)
        lay.rect(56, 246, 20, 42, 'P', 1.6, hgt=0.3)
        for dx in (56, 66):
            K.recess(lay, dx + 1, 250, 8, 14, 'P', 1.2, shadow=0.6, light=2.4)
            K.recess(lay, dx + 1, 268, 8, 16, 'P', 1.2, shadow=0.6, light=2.4)
        lay.rect(65, 246, 1, 42, 'I', 1.0)
        lay.rect(58, 236, 16, 5, 'L', 2.2, emis=True)          # transom: the stairwell light
        lay.rect(58, 238, 16, 1, 'S', 1.6)
        lay.rect(46, 250, 6, 5, 'D', 3.6, crisp=True)           # house number plate
        K.text(lay, '11', 46, 250, 'P', 5.2, font='35', spacing=0)
        self.light('stair_11', (66, 236), 'warm', 0.25, 26, height=6)
        # the party wall's raw edge where No. 9 was torn away
        for y in range(70, 240):
            lay.px(x1 - 2, y, 'K', 1.8 + ((y // 3) % 2) * 0.6, hgt=0.3)
            lay.px(x1 - 1, y, 'K', 1.2, hgt=0.2)

    def altbau_window(self, x, y, w, h, lit=None, seed=0, pediment=False):
        lay = self.lay
        lay.rect(x - 2, y - 2, w + 4, h + 4, 'W', 6.0, hgt=0.6)               # stucco surround
        lay.rect(x - 1, y - 1, w + 2, h + 2, 'W', 3.0, hgt=0.4)
        if pediment:
            lay.rect(x - 4, y - 6, w + 8, 3, 'W', 6.4, hgt=0.9)
            lay.rect(x - 4, y - 3, w + 8, 1, 'W', 2.4)
            snowcap(lay, x - 4, y - 6, w + 8, 2, seed=seed + 1)
        if lit == 'marta':
            # Marta's room: a lamp left on behind the lace -- nobody is home, the child is in the tram
            lay.vgrad(x, y, w, h, 'L', 4.6, 3.2, emis=True)
            for yy in range(y, y + h):
                for xx in range(x, x + w):
                    if (xx * 3 + yy * 5) % 7 == 0 and yy < y + h - 4:
                        lay.px(xx, yy, 'L', 5.0, emis=True)
            lay.rect(x + 9, y + h - 12, 5, 4, 'L', 2.0, emis=True)      # lamp shade
            lay.rect(x + 11, y + h - 8, 1, 5, 'L', 1.2, emis=True)
            lay.rect(x + 2, y + h - 6, 4, 6, 'L', 2.0, emis=True)      # a plant pot
            lay.rect(x + 3, y + h - 9, 2, 3, 'G', 2.0, emis=True)
            self.light('marta_window', (x + w / 2, y + h / 2), 'warm', 0.65, 60, height=10)
        elif lit == 'dim':
            lay.vgrad(x, y, w, h, 'L', 2.6, 1.6, emis=True)
            lay.rect(x, y, w, 7, 'L', 1.2, emis=True)
            self.light('window_11_dim', (x + w / 2, y + h / 2), 'warm', 0.25, 34, height=8)
        else:
            lay.vgrad(x, y, w, h, 'D', 1.0, 2.2)
            lay.line(x + 2, y + h - 3, x + w - 4, y + 3, 'D', 3.4)
            lay.rect(x, y, w, 3, 'N', 1.5)
        mid = x + w // 2
        lay.vline(mid, y, h, 'W', 5.0, hgt=0.3)
        lay.hline(x, y + h // 3, w, 'W', 5.0, hgt=0.3)
        lay.rect(x - 3, y + h + 2, w + 6, 2, 'W', 6.3, hgt=0.8)                 # sill
        lay.rect(x - 3, y + h + 4, w + 6, 1, 'W', 2.0)
        snowcap(lay, x - 3, y + h + 2, w + 6, 2, seed=seed + 2)

    # ================================================================== house No. 9 (gutted)
    def house9(self):
        lay = self.lay
        x0, x1 = L.HOUSE9
        rng = np.random.default_rng(909)
        nz = pg.value_noise(x1 - x0, H, 5, 99, octaves=3)
        # the torn top of the wall: stepped brick courses, lower towards the stair side
        top = np.zeros(x1 - x0, np.int32)
        i = 0
        while i < x1 - x0:
            seg = int(rng.integers(5, 13))
            lvl = int(rng.integers(92, 106)) + max(0, i - 92) * 2
            top[i:i + seg] = lvl
            i += seg
        # the exposed wall: plaster with brick showing at the torn edge
        for i in range(x1 - x0):
            for y in range(top[i], 236):
                lay.px(x0 + i, y, 'W', 4.2 + (nz[y, i] - 0.5) * 0.7, flat=False, hgt=0.1)
            for k in range(4):
                if k < 2 or rng.random() < 0.5:
                    lay.px(x0 + i, top[i] + k, 'K', 1.6 + ((i // 4 + k) % 2) * 0.8, hgt=0.5)
            lay.px(x0 + i, top[i] - 1, 'SN', 5.8, hgt=0.6)
            if rng.random() < 0.4:
                lay.px(x0 + i, top[i] - 2, 'SN', 6.4, hgt=0.6)
        # three storeys, two rooms each: the paper of the flats that were here
        rooms = {'rose': (('Y', 1.5, 'dots'), ('P', 3.0, 'stripes')),
                 'green': (('G', 2.8, 'stripes'), ('D', 3.6, 'plain')),
                 'blue': (('D', 3.8, 'diamonds'), ('Y', 2.0, 'plain'))}
        split = x0 + 66
        for (ya, yb, kind) in L.PAPER_STOREYS:
            (r1, t1, p1), (r2, t2, p2) = rooms[kind]
            self.paper(x0 + 3, ya + 3, split - x0 - 5, yb - ya - 5, r1, t1, p1, top, x0, seed=ya)
            self.paper(split + 3, ya + 3, (x1 - 24) - split - 5, yb - ya - 5, r2, t2, p2, top, x0, seed=ya + 1)
            lay.vline(split, ya + 2, yb - ya - 3, 'W', 5.4, hgt=0.3)                  # the partition's trace
            lay.vline(split + 1, ya + 2, yb - ya - 3, 'W', 3.2, hgt=0.2)
        self.ghosts(x0, split)
        for yj in (L.PAPER_STOREYS[0][0], L.PAPER_STOREYS[1][0], L.PAPER_STOREYS[2][0]):
            lay.rect(x0, yj - 1, x1 - x0 - 4, 3, 'W', 2.6, hgt=-0.2)
            for x in range(x0 + 4, x1 - 8, 8):
                lay.rect(x, yj - 1, 2, 2, 'N', 1.0)
            snowcap(lay, x0 + 1, yj - 1, x1 - x0 - 6, 1, seed=yj, tone=5.6, drip=0.0)
        # the stair's trace: a darker band zig-zagging through the three storeys on the right
        for y in range(104, 240):
            ph = (y - 104) % 46
            sx = x1 - 22 + (ph // 3 if ((y - 104) // 46) % 2 == 0 else 15 - ph // 3)
            if y >= top[min(x1 - x0 - 1, sx - x0)] + 3:
                lay.rect(sx - 4, y, 6, 1, 'W', 2.4, hgt=-0.1)
        # tiled stove on the second floor, still clinging to the wall
        sx0 = x0 + 62
        lay.rect(sx0, 160, 18, 34, 'P', 3.4, hgt=0.7)
        for yy in range(160, 194, 5):
            lay.hline(sx0, yy, 18, 'P', 2.0, hgt=0.3)
        for xx in range(sx0, sx0 + 18, 6):
            lay.vline(xx, 160, 34, 'P', 2.2, hgt=0.3)
        lay.rect(sx0 - 1, 158, 20, 3, 'P', 4.6, hgt=0.9)
        lay.rect(sx0 + 6, 182, 6, 5, 'I', 1.0)
        lay.rect(sx0 + 7, 148, 4, 4, 'N', 0.8)                          # stovepipe hole above
        snowcap(lay, sx0 - 1, 158, 20, 2, seed=11)
        # ground-floor front with the sealed door
        gy = 228
        for i in range(x1 - x0):
            ty = gy + int(4 * math.sin(i * 0.4) + rng.integers(0, 3))
            for y in range(ty, B):
                lay.px(x0 + i, y, 'W', 4.0 + (nz[y, i] - 0.5) * 0.9 - 0.6 * ((y - 240) % 6 == 0), flat=False,
                       hgt=0.25)
            lay.px(x0 + i, ty, 'K', 2.6, hgt=0.5)
            lay.px(x0 + i, ty - 1, 'SN', 5.8, hgt=0.6)
        d0, d1 = L.DOOR9
        dy0, dy1 = L.DOOR9_Y
        lay.rect(d0 - 4, dy0 - 6, d1 - d0 + 8, dy1 - dy0 + 6, 'W', 6.0, hgt=0.7)
        lay.rect(d0 + (d1 - d0) // 2 - 3, dy0 - 8, 6, 6, 'W', 6.6, hgt=0.9)     # keystone
        lay.rect(d0, dy0, d1 - d0, dy1 - dy0, 'P', 1.5, hgt=0.2)
        for dx in (d0, d0 + (d1 - d0) // 2):
            for py in (dy0 + 4, dy0 + 26):
                K.recess(lay, dx + 3, py, (d1 - d0) // 2 - 6, 18, 'P', 1.1, shadow=0.5, light=2.2)
        lay.vline(d0 + (d1 - d0) // 2, dy0, dy1 - dy0, 'I', 0.8)
        # planks nailed across, the red seal strip, the notice (decal site), the number
        for (py, slant) in ((dy0 + 10, 4), (dy0 + 30, -3), (dy0 + 44, 2)):
            for i in range(d1 - d0 + 6):
                yy = py + int(slant * i / (d1 - d0))
                lay.rect(d0 - 3 + i, yy, 1, 4, 'P', 3.2 + ((i * 7) % 5) * 0.15, hgt=0.7)
                lay.px(d0 - 3 + i, yy + 4, 'N', 1.2)
            lay.px(d0, py + 1, 'S', 4.6)
            lay.px(d1 - 1, py + 1 + slant, 'S', 4.6)
        for i in range(d1 - d0 - 4):
            lay.px(d0 + 2 + i, dy0 + 21 + i // 9, 'R', 3.4, hgt=0.4)
            lay.px(d0 + 2 + i, dy0 + 22 + i // 9, 'R', 2.4, hgt=0.3)
        lay.rect(d0 + (d1 - d0) // 2 - 2, dy0 - 15, 6, 6, 'D', 3.6, crisp=True)
        K.text(lay, '9', d0 + (d1 - d0) // 2 - 1, dy0 - 15, 'P', 5.2)
        # bricked-up ground-floor windows
        for wx in (148, 178):
            lay.rect(wx - 2, 244, 24, 34, 'W', 5.8, hgt=0.6)
            K.bricks(lay, wx, 246, 20, 30, 'K', 2.6, seed=wx, course=3, length=6)
            snowcap(lay, wx - 3, 278, 26, 2, seed=wx)
        # a child's sled leaned against the wall beside the sealed door
        lay.line(140, 286, 146, 266, 'P', 3.0, hgt=0.6)
        lay.line(143, 287, 149, 267, 'P', 3.0, hgt=0.6)
        for k in range(4):
            lay.line(141 + k, 280 - k * 4, 145 + k, 280 - k * 4, 'P', 4.0, hgt=0.7)
        lay.line(146, 266, 150, 263, 'R', 2.6)
        # rubble heap at the open side of the gap
        for i in range(44):
            hh = int(14 * math.sin(math.pi * (i + 0.5) / 44) ** 0.7)
            for k in range(hh):
                lay.px(x1 - 10 + i, B - 1 - k, 'SN' if k > hh - 3 else 'K', 5.4 if k > hh - 3 else 2.0 + rng.random(),
                       hgt=0.6)
        if self.cfg.get('notice9'):
            self.notice9(d0 + 4, dy0 + 16)

    def notice9(self, x, y):
        """The eviction notice pasted over the planks of the left leaf (decal notice_9, env_c4_annex): a typed
        sheet 12x15 with the red round stamp of the Bezirksamt and the site plan stapled under it -- no
        insignia.  The seal strip stays visible across the door join, the '9' plate above."""
        lay = self.lay
        lay.rect(x + 1, y + 1, 12, 15, 'N', 1.0)                                   # its shadow on the boards
        lay.rect(x, y, 12, 15, 'P', 4.7, hgt=0.3, crisp=True)
        lay.hline(x, y, 12, 'P', 5.3, hgt=0.4, crisp=True)
        lay.rect(x + 2, y + 2, 8, 1, 'I', 1.4, crisp=True)                        # the heading
        for k, w_ in enumerate((9, 7, 9, 8)):                                      # the typed lines
            lay.rect(x + 1, y + 4 + k * 2, w_, 1, 'I', 2.6, crisp=True)
        for (sx, sy) in ((1, 0), (2, 0), (0, 1), (3, 1), (0, 2), (3, 2), (1, 3), (2, 3)):   # the round stamp, red
            lay.px(x + 1 + sx, y + 11 + sy, 'R', 3.0, crisp=True)
        # the site plan stapled to its lower right corner, over the second plank
        px_, py_ = x + 6, y + 10
        lay.rect(px_ + 1, py_ + 1, 8, 7, 'N', 1.0)
        lay.rect(px_, py_, 8, 7, 'D', 5.4, hgt=0.3, crisp=True)
        lay.hline(px_ + 1, py_ + 3, 6, 'D', 2.6, crisp=True)                      # streets of the plan
        lay.vline(px_ + 4, py_ + 1, 5, 'D', 2.6, crisp=True)
        lay.px(px_ + 2, py_ + 1, 'D', 2.2, crisp=True)
        lay.px(px_ + 6, py_ + 5, 'D', 2.2, crisp=True)
        lay.rect(px_ + 3, py_, 2, 1, 'S', 1.6, crisp=True)                        # the staple
        lay.px(x + 11, y, 'P', 5.6, crisp=True)                                    # a corner lifting in the frost

    def paper(self, x, y, w, h, ramp, base, pat, top, hx0, seed=0):
        """Wallpaper of one room of the demolished flat: its pattern, a plaster rim at the ceiling and the floor,
        a few torn places."""
        lay = self.lay
        rng = np.random.default_rng(seed)
        for yy in range(y, y + h):
            for xx in range(x, x + w):
                if yy < top[min(len(top) - 1, xx - hx0)] + 4:
                    continue
                t = base
                if pat == 'dots':
                    t += 0.8 if ((xx // 3 + yy // 4) % 3 == 0 and yy % 4 == 1) else 0.0
                elif pat == 'stripes':
                    t += 0.6 if xx % 6 in (0, 1) else 0.0
                elif pat == 'diamonds':
                    t += 0.6 if (abs((xx % 8) - 4) + abs((yy % 8) - 4)) == 3 else 0.0
                t += (rng.random() - 0.5) * 0.25 - 0.4 * (yy < y + 3)
                lay.px(xx, yy, ramp, t, hgt=0.12)
        for _ in range(int(w * h * 0.006)):
            tx, ty = x + int(rng.integers(0, max(1, w - 4))), y + int(rng.integers(4, max(5, h)))
            if ty < top[min(len(top) - 1, tx - hx0)] + 5:
                continue
            lay.rect(tx, ty, int(rng.integers(2, 4)), 1, 'W', 4.0, hgt=0.0)

    def ghosts(self, x0, split):
        """Where the furniture stood the paper kept its colour: the wardrobe and a picture on the first floor,
        the dresser's shelf in the kitchen, the mirror upstairs, the child's height marks at a door frame."""
        lay = self.lay
        (y1a, y1b, _k1), (y2a, y2b, _k2), (y3a, y3b, _k3) = L.PAPER_STOREYS
        lay.shade_rect(x0 + 8, y1a + 8, 20, y1b - y1a - 10, 0.55)
        lay.shade_rect(x0 + 38, y1a + 10, 12, 9, 0.6)
        lay.px(x0 + 44, y1a + 7, 'I', 1.4)
        lay.line(x0 + 41, y1a + 9, x0 + 44, y1a + 7, 'I', 2.0)
        lay.line(x0 + 47, y1a + 9, x0 + 44, y1a + 7, 'I', 2.0)
        lay.shade_rect(split + 6, y1a + 6, 24, 16, 0.5)
        m = np.zeros((14, 10), bool)
        yy, xx = np.mgrid[0:14, 0:10]
        m[((xx - 4.5) / 5) ** 2 + ((yy - 6.5) / 7) ** 2 <= 1] = True
        lay.shade_mask(m, x0 + 24, y3a + 12, 0.6)
        lay.vline(split + 12, y2a + 6, y2b - y2a - 8, 'W', 5.0, hgt=0.3)
        lay.vline(split + 26, y2a + 6, y2b - y2a - 8, 'W', 5.0, hgt=0.3)
        lay.hline(split + 12, y2a + 6, 15, 'W', 5.0, hgt=0.3)
        for k, yy_ in enumerate((y2b - 12, y2b - 16, y2b - 19, y2b - 22)):
            lay.hline(split + 9, yy_, 3, 'I', 1.2)

    # ================================================================== poles, wires, the sodium lamp
    def pole(self, x):
        lay = self.lay
        K.cyl(lay, x - 2, 116, 5, B - 116, 'S', 3.0, hgt=0.7, amp=1.4)
        lay.rect(x - 4, B - 22, 9, 22, 'S', 2.6, hgt=0.8)
        lay.rect(x - 5, B - 4, 11, 4, 'S', 2.0, hgt=0.6)
        for yy in (B - 22, B - 14):
            lay.hline(x - 4, yy, 9, 'S', 4.8, hgt=0.9)
        lay.rect(x - 1, 108, 3, 8, 'S', 4.0, hgt=0.8)
        lay.px(x, 106, 'S', 5.0, hgt=0.9)
        # bracket arm to the contact wire with its insulator
        lay.hline(x - 1, L.WIRE_Y - 8, 12 if x < 400 else -12, 'S', 3.6)
        arm = (x, x + 14) if x < 400 else (x - 14, x)
        lay.hline(arm[0], L.WIRE_Y - 8, arm[1] - arm[0], 'S', 3.6, hgt=0.5)
        lay.line(x, L.WIRE_Y - 16, arm[1] if x < 400 else arm[0], L.WIRE_Y - 8, 'S', 2.8)
        snowcap(lay, x - 4, B - 22, 9, 1, seed=x)

    def wires(self):
        lay = self.lay
        # contact wire above the loop track, hangers every 40 px
        lay.hline(206, L.WIRE_Y, W - 206, 'I', 1.6)
        for x in range(232, W, 40):
            lay.vline(x, L.WIRE_Y - 3, 3, 'I', 1.2)
        # span wire pole to pole, sagging under the lamp
        x0, x1 = L.POLES
        lx, ly = L.LAMP_LOOP
        for x in range(x0, x1 + 1):
            if x <= lx:
                y = 116 + (ly - 14 - 116) * ((x - x0) / (lx - x0)) ** 1.2
            else:
                y = ly - 14 + (116 - ly + 14) * ((x - lx) / (x1 - lx)) ** 0.8
            lay.px(x, int(y), 'I', 1.4)
        # the sodium lamp: a shallow dish, the glowing bowl underneath
        lay.rect(lx - 9, ly - 10, 19, 3, 'S', 2.4, hgt=0.8)
        lay.rect(lx - 7, ly - 7, 15, 3, 'S', 3.2, hgt=0.7)
        lay.rect(lx - 6, ly - 4, 13, 3, 'L', 4.6, emis=True)
        lay.rect(lx - 4, ly - 1, 9, 1, 'L', 5.2, emis=True)
        lay.vline(lx, ly - 14, 4, 'I', 1.2)
        snowcap(lay, lx - 9, ly - 10, 19, 1, seed=2)
        self.light('sodium_loop', (lx, ly + 2), 'warm', 1.6, 190, height=46, pool=0.55, pool_w=34, pool_depth=40,
                   pool_spread=1.3)

    # ================================================================== shelter, timetable case, stop sign
    def shelter(self):
        lay = self.lay
        s0, s1 = L.SHELTER
        r0, r1 = L.SHELTER_ROOF_Y
        # back glazing (dark glass, cold reflection streaks), frames, posts
        lay.rect(s0 + 4, r1, s1 - s0 - 8, B - 4 - r1, 'D', 1.6, hgt=-0.1)
        for x in range(s0 + 4, s1 - 4):
            for y in range(r1, B - 4):
                if (x - y * 0.6) % 31 < 3:
                    lay.px(x, y, 'D', 3.2)
        for fx in (s0 + 4, s0 + 30, s0 + 56, s1 - 5):
            lay.rect(fx, r1, 2, B - 4 - r1, 'S', 2.6, hgt=0.5)
        lay.rect(s0 + 4, B - 6, s1 - s0 - 8, 2, 'S', 2.4, hgt=0.4)
        for px_ in (s0 + 2, s1 - 4):
            K.cyl(lay, px_, r1, 3, B - r1, 'S', 3.0, hgt=0.7)
        self.shelter_poster(s1 - 18, 237)
        # roof slab with the name fascia, snow and icicles
        lay.rect(s0 - 3, r0, s1 - s0 + 6, r1 - r0, 'C', 3.6, hgt=0.9)
        lay.rect(s0 - 3, r0 + 2, s1 - s0 + 6, 7, 'S', 1.4, hgt=0.6)
        nm = 'WENDESCHLEIFE SÜD 8'
        K.text(lay, nm, (s0 + s1) // 2, r0 + 3, 'P', 5.0, center=True)
        lay.rect(s0 - 3, r1 - 1, s1 - s0 + 6, 1, 'C', 1.6)
        snowcap(lay, s0 - 4, r0, s1 - s0 + 8, 3, seed=33)
        rng = np.random.default_rng(34)
        for x in range(s0 - 2, s1 + 3, 3):
            if rng.random() < 0.5:
                lay.vline(x, r1, int(rng.integers(1, 4)), 'SN', 5.0)
        # bench
        lay.rect(s0 + 8, 266, 26, 3, 'P', 2.8, hgt=0.6)
        lay.rect(s0 + 8, 272, 26, 2, 'P', 2.4, hgt=0.5)
        for bx in (s0 + 10, s0 + 30):
            lay.rect(bx, 269, 2, B - 4 - 269, 'I', 1.4)
        # the lit timetable case: Konrad's light table
        c0, c1 = L.CASE
        cy0, cy1 = L.CASE_Y
        lay.rect(c0 - 2, cy0 - 2, c1 - c0 + 4, cy1 - cy0 + 4, 'S', 2.0, hgt=0.8)
        lay.rect(c0 - 2, cy0 - 2, c1 - c0 + 4, 1, 'S', 4.2, hgt=0.9)
        lay.rect(c0, cy0, c1 - c0, cy1 - cy0, 'SN', 7.0, emis=True)
        lay.rect(c0, cy0, c1 - c0, 4, 'SN', 5.0, emis=True)
        K.text(lay, '74', c0 + 1, cy0, 'I', 0.6, emis=True)
        for col in range(3):
            for row in range(5):
                lay.rect(c0 + 2 + col * 7, cy0 + 7 + row * 3, 5, 1, 'I', 2.6 - (row % 2) * 0.4, emis=True)
        lay.hline(c0 + 2, cy0 + 24, c1 - c0 - 4, 'R', 3.2, emis=True)              # the line on the map
        for k in range(5):
            lay.px(c0 + 3 + k * 4, cy0 + 24, 'I', 1.0, emis=True)
        lay.vline(c0 + 18, cy0 + 21, 6, 'R', 3.2, emis=True)
        lay.rect((c0 + c1) // 2 - 1, cy1 + 2, 3, B - cy1 - 2, 'S', 2.2, hgt=0.6)
        if self.cfg.get('routes'):
            # Konrad's tracing sheets taped over the glass: Marta's line in red, three detours, the site plan
            lay.rect(c0 - 1, cy0 + 1, c1 - c0 + 2, cy1 - cy0 - 3, 'SN', 7.0, emis=True)
            for x in range(c0, c1):
                for y in range(cy0 + 2, cy1 - 3):
                    if (x * 7 + y * 3) % 9 == 0:
                        lay.px(x, y, 'SN', 6.0, emis=True)
            pts = [(c0 + 1, cy0 + 22), (c0 + 6, cy0 + 22), (c0 + 6, cy0 + 12), (c0 + 12, cy0 + 12),
                   (c0 + 12, cy0 + 20), (c0 + 18, cy0 + 20), (c0 + 18, cy0 + 8), (c1 - 2, cy0 + 8)]
            lay.polyline(pts, 'R', 3.4, emis=True)
            for (bx, by) in ((c0 + 4, cy0 + 4), (c0 + 10, cy0 + 4), (c0 + 16, cy0 + 4)):
                lay.rect(bx, by, 4, 3, 'D', 2.2, emis=True)
            for (sx, sy) in ((c0 + 6, cy0 + 16), (c0 + 12, cy0 + 16), (c0 + 18, cy0 + 14)):
                lay.px(sx, sy, 'I', 1.0, emis=True)
            for (tx, ty) in ((c0 - 1, cy0 + 1), (c1 - 1, cy0 + 1), (c0 - 1, cy1 - 4), (c1 - 1, cy1 - 4)):
                lay.rect(tx, ty, 2, 2, 'P', 4.0, emis=True)
        self.light('timetable_case', ((c0 + c1) / 2, (cy0 + cy1) / 2), 'cold', 0.9, 54, height=8, pool=0.4,
                   pool_w=8, pool_depth=24)
        # the stop sign: H (green on yellow) and the line plate 74
        sx = L.STOP_SIGN
        K.cyl(lay, sx - 1, 196, 3, B - 196, 'S', 3.2, hgt=0.6)
        m = K.disc(13)
        lay.put(m, sx - 6, 186, 'L', 3.8, hgt=0.8)
        lay.put(K.edge_of(m), sx - 6, 186, 'S', 1.6)
        K.text(lay, 'H', sx - 1, 190, 'G', 1.4)
        lay.rect(sx - 5, 200, 11, 7, 'P', 5.0, hgt=0.5)
        K.text(lay, '74', sx - 3, 201, 'I', 0.8)
        snowcap(lay, sx - 4, 186, 9, 1, seed=8)

    def shelter_poster(self, x, y):
        """The poster „Berlin baut“ on the right side wall of the shelter (find exp_shelter_poster, focus 322 / 246),
        12 x 18: the red title band, a crane over the dome, the sun, three workers in open white shirts, the
        lower right corner torn off, and on the paper margin under the picture a pencil line („und wo wohnen
        wir?“).  No insignia."""
        lay = self.lay

        def torn(u, v):
            return u + v >= 26

        def put(u, v, ramp, tone, hgt=0.3):
            if 0 <= u < 12 and 0 <= v < 18 and not torn(u, v):
                lay.px(x + u, y + v, ramp, tone, hgt=hgt, crisp=True)
        for v in range(18):
            for u in range(12):
                if v <= 2:
                    put(u, v, 'R', 2.9)                                             # title band
                elif v <= 9:
                    put(u, v, 'D', 5.2 - (v - 3) * 0.12)                            # sky
                elif v <= 14:
                    put(u, v, 'D', 4.4)
                else:
                    put(u, v, 'P', 5.0)                                             # paper margin
        for u in (1, 2, 4, 5, 6, 8, 9, 10):                                         # BERLIN BAUT
            put(u, 1, 'P', 5.4)
        for (u, v) in ((9, 4), (10, 4), (9, 5), (10, 5)):                           # the sun
            put(u, v, 'L', 4.4)
        for v in range(6, 10):                                                     # the dome, too near
            for u in range(3, 10):
                if (u - 6.0) ** 2 + ((v - 9.5) * 1.15) ** 2 <= 12.5:
                    put(u, v, 'W', 6.0 if u < 6 else 5.2)
        put(6, 5, 'W', 5.6)
        put(6, 4, 'W', 4.6)
        for v in range(4, 10):                                                     # the crane: mast, jib, hook
            put(1, v, 'R', 1.6)
        for u in range(0, 6):
            put(u, 4, 'R', 1.6)
        put(5, 5, 'I', 1.6)
        put(5, 6, 'I', 1.6)
        for u0 in (2, 5, 8):                                                       # three workers
            put(u0, 9, 'Y', 2.0)
            put(u0 + 1, 9, 'Y', 1.6)
            for v in (10, 11):
                put(u0, v, 'P', 5.4)
                put(u0 + 1, v, 'P', 5.0 if v == 10 else 4.6)
            put(u0 + 1, 10, 'Y', 1.8)                                              # the open collar
            for v in (12, 13):
                put(u0, v, 'D', 2.2)
                put(u0 + 1, v, 'D', 2.6)
        for u in range(12):
            put(u, 14, 'K', 2.6)                                                   # the ground line
        for (u, v) in ((1, 16), (2, 15), (3, 16), (4, 16), (5, 15), (6, 16), (7, 16), (8, 15)):
            put(u, v, 'S', 2.6)                                                    # the pencil line
        for u in range(12):                                                        # the curling edge of the tear
            v = 25 - u
            if 12 <= v < 18:
                put(u, v, 'P', 5.8, hgt=0.6)

    # ================================================================== tram 74
    def tram(self):
        lay = self.lay
        t0, t1 = L.TRAM
        ty0, ty1 = L.TRAM_Y
        body_top, belt, skirt = ty0 + 6, 258, 284
        # roof (lantern roof) and the bow collector up to the wire
        lay.rect(t0 + 6, ty0 + 2, t1 - t0 - 12, 4, 'S', 2.4, hgt=0.7)
        lay.rect(t0 + 30, ty0 - 2, t1 - t0 - 60, 4, 'S', 2.0, hgt=0.6)
        for x in range(t0 + 34, t1 - 34, 8):
            lay.rect(x, ty0 - 1, 4, 2, 'L', 3.6, emis=True)
        snowcap(lay, t0 + 6, ty0 + 2, t1 - t0 - 12, 2, seed=74)
        snowcap(lay, t0 + 30, ty0 - 2, t1 - t0 - 60, 2, seed=75)
        bx = (t0 + t1) // 2 - 6
        lay.rect(bx - 6, ty0 - 4, 12, 2, 'S', 2.0)
        lay.line(bx - 4, ty0 - 4, bx - 1, L.WIRE_Y + 2, 'S', 3.2)
        lay.line(bx + 4, ty0 - 4, bx + 1, L.WIRE_Y + 2, 'S', 3.2)
        lay.hline(bx - 3, L.WIRE_Y + 1, 7, 'S', 4.0)
        # body: cream upper and lower panels, dark belt rail; front rounded
        for x in range(t0, t1):
            edge = min(x - t0, t1 - 1 - x)
            r = 0 if edge >= 6 else int((6 - edge) ** 1.3 / 2)
            for y in range(body_top + r, skirt):
                tone = 4.2 - (y - body_top) / (skirt - body_top) * 1.1
                if belt <= y < belt + 4:
                    lay.px(x, y, 'S', 2.0 + (y == belt) * 1.6, hgt=0.6)
                else:
                    lay.px(x, y, 'P', tone - (edge < 3) * 0.7, flat=False, hgt=0.5 - 0.1 * (edge < 3))
        lay.hline(t0 + 3, body_top, t1 - t0 - 6, 'P', 5.0, hgt=0.7)
        lay.hline(t0 + 2, skirt - 6, t1 - t0 - 4, 'R', 2.4, hgt=0.5)
        K.text(lay, '3518', t0 + 154, belt + 6, 'S', 1.6)
        # underframe, axles, rail
        lay.rect(t0 + 8, skirt, t1 - t0 - 16, 5, 'I', 1.2)
        for ax in (t0 + 60, t1 - 58):
            m = K.disc(11)
            lay.put(m, ax - 5, skirt - 3, 'I', 1.8, hgt=0.5)
            lay.rect(ax - 1, skirt + 1, 3, 3, 'S', 3.4)
        # windows (warm interior), the destination board, the headlamp
        wy0, wy1 = 232, 256
        for (a, b) in L.TRAM_WINDOWS:
            self.tram_window(a, wy0, b - a, wy1 - wy0, fogged=(a, b) == L.ILSE_WIN)
        for a in (t0 + 3, t0 + 11):
            lay.rect(a, wy0 + 2, 7, wy1 - wy0 - 4, 'D', 1.6)
            lay.line(a + 1, wy1 - 4, a + 5, wy0 + 4, 'D', 3.4)
        lay.rect(t0 + 6, ty0 + 7, 30, 7, 'I', 1.0, hgt=0.4)
        K.text(lay, '74', t0 + 8, ty0 + 8, 'L', 5.0, emis=True)
        lay.rect(t0 + 18, ty0 + 8, 16, 5, 'P', 5.0, emis=True)                    # handwritten route board
        for k in range(4):
            lay.line(t0 + 19 + k * 4, ty0 + 12, t0 + 21 + k * 4, ty0 + 9, 'I', 1.4, emis=True)
        lay.rect(t0 + 2, 266, 4, 4, 'L', 5.0, emis=True)
        lay.rect(t0 + 1, 265, 6, 1, 'S', 3.6)
        self.light('tram_headlamp', (t0 + 2, 268), 'warm', 0.6, 48, height=6)
        # the open front door: the platform inside, the controller, a grab pole
        d0, d1 = L.TRAM_DOOR
        lay.rect(d0, wy0 - 4, d1 - d0, skirt - wy0 + 4, 'L', 1.6, emis=True)
        lay.rect(d0, wy0 - 4, d1 - d0, 6, 'L', 3.0, emis=True)
        lay.rect(d0 + 4, 262, 6, 18, 'I', 1.2)
        lay.rect(d0 + 3, 260, 8, 3, 'S', 3.0)
        lay.vline(d1 - 4, wy0 - 2, skirt - wy0, 'L', 4.4, emis=True)
        for dd in (d0 - 3, d1):
            lay.rect(dd, wy0 - 4, 3, skirt - wy0 + 4, 'P', 3.4, hgt=0.6)
            lay.vline(dd + 1, wy0, 22, 'D', 2.0)
        lay.rect(d0 - 2, skirt, d1 - d0 + 4, 3, 'S', 3.4, hgt=0.6)                  # step
        # rear platform door (closed) and the tail lamp
        lay.rect(t1 - 32, wy0 - 2, 14, skirt - wy0, 'P', 3.0, hgt=0.4)
        lay.rect(t1 - 30, wy0, 10, 20, 'L', 2.4, emis=True)
        lay.rect(t1 - 4, 264, 3, 3, 'R', 4.0, emis=True)
        self.light('tram_inside', ((t0 + t1) / 2, 246), 'warm', 0.8, 120, height=12, pool=0.5, pool_w=60,
                   pool_depth=26, pool_spread=0.3)

    def tram_window(self, x, y, w, h, fogged=False):
        lay = self.lay
        lay.rect(x - 1, y - 1, w + 2, h + 2, 'P', 2.0, hgt=0.3)
        lay.vgrad(x, y, w, h, 'L', 3.8, 2.6, emis=True)
        lay.rect(x, y + h - 8, w, 8, 'L', 1.6, emis=True)                         # backrests
        for sx in range(x + 2, x + w - 2, 9):
            lay.rect(sx, y + h - 11, 6, 4, 'L', 1.2, emis=True)
        lay.hline(x, y + 3, w, 'L', 4.8, emis=True)                                # the ceiling lamps
        for sx in range(x + 3, x + w, 7):
            lay.vline(sx, y, 5, 'L', 2.0, emis=True)                              # straps
        if fogged:
            for yy in range(y + 6, y + h):
                for xx in range(x, x + w):
                    if (xx + 2 * yy) % 3 != 0:
                        lay.px(xx, yy, 'L', 4.2 - (yy - y) * 0.04, emis=True)
        lay.rect(x, y, w, 1, 'P', 1.4)

    # ================================================================== the advertising column S 2
    def column(self, bared=False):
        lay = self.lay
        c0, c1 = L.COLUMN
        y0, y1 = L.COLUMN_Y
        w = c1 - c0
        # posters around the drum (shaded like a cylinder)
        posters = [(y0 + 8, 30, 'P', 4.6, 'KONZERT'), (y0 + 38, 24, 'R', 2.8, 'KINO'), (y0 + 62, 24, 'P', 4.2, None)]
        for x in range(w):
            c = (x + 0.5) / w * 2 - 1
            shade = -1.3 * abs(c + 0.25) ** 1.6 + 0.4
            for y in range(y0, y1):
                lay.px(c0 + x, y, 'C', 3.6 + shade, hgt=0.6 * math.sqrt(max(0, 1 - c * c)), flat=False)
            for (py, ph, ramp, tone, _t) in posters:
                for y in range(py, min(y1 - 4, py + ph)):
                    lay.px(c0 + x, y, ramp, tone + shade + ((y - py) % 7 == 0) * 0.3, hgt=0.55 *
                           math.sqrt(max(0, 1 - c * c)), flat=False)
        for (py, ph, ramp, tone, txt) in posters:
            if txt:
                K.text(lay, txt, c0 + w // 2, py + 3, 'I' if ramp == 'P' else 'P', 1.0 if ramp == 'P' else 5.0,
                       center=True)
            K.pseudo_text(lay, c0 + 5, py + 11, w - 10, 3, 'I' if ramp != 'R' else 'P', 1.6, seed=py, gap=3)
            lay.hline(c0 + 1, py, w - 2, 'C', 1.4)
        # the official notice (insignia site, 12.4): the emblem above the small print
        K.emblem(lay, c0 + w // 2 - 3, y0 + 63, 12, self.hist)
        # a poster corner curling in the frost
        lay.poly([(c1 - 7, y0 + 38), (c1 - 1, y0 + 38), (c1 - 1, y0 + 44)], 'P', 5.2, hgt=0.9)
        # crown, cap, finial
        lay.rect(c0 - 4, y0 - 12, w + 8, 4, 'C', 4.6, hgt=1.0)
        lay.rect(c0 - 3, y0 - 8, w + 6, 8, 'C', 3.0, hgt=0.8)
        for x in range(c0 - 3, c1 + 3, 3):
            lay.vline(x, y0 - 8, 8, 'C', 2.0)
        for i in range(w + 4):
            hh = int(10 * math.sin(math.pi * (i + 0.5) / (w + 4)) ** 0.6)
            lay.vline(c0 - 2 + i, y0 - 12 - hh, hh, 'C', 3.4 + (i < w // 2) * 0.8, hgt=0.7)
        lay.rect(c0 + w // 2 - 1, y0 - 28, 3, 7, 'S', 4.0, hgt=0.9)
        snowcap(lay, c0 - 4, y0 - 12, w + 8, 2, seed=62)
        for i in range(w + 2):
            hh = int(10 * math.sin(math.pi * (i + 0.5) / (w + 4)) ** 0.6)
            lay.px(c0 - 1 + i, y0 - 13 - hh, 'SN', 6.0, hgt=0.8)
        # plinth ring with the warm-air grate at its foot; the snow has melted around it
        lay.rect(c0 - 3, y1, w + 6, B - y1, 'C', 3.2, hgt=0.7)
        lay.hline(c0 - 3, y1, w + 6, 'C', 5.0, hgt=0.9)
        g0 = c0 + 6
        for x in range(g0, c1 - 6):
            lay.vline(x, y1 + 2, B - y1 - 3, 'L' if x % 2 else 'I', 2.4 if x % 2 else 1.0, emis=bool(x % 2))
        self.light('column_grate', ((c0 + c1) / 2, B - 2), 'warm', 0.35, 30, height=4)
        if bared:
            # the poster torn back: a steel door with the stencil of the ventilation structure
            dx0, dx1 = c0 + 8, c1 - 8
            lay.rect(dx0 - 1, y0 + 30, dx1 - dx0 + 2, y1 - y0 - 32, 'S', 2.0, hgt=0.6)
            lay.rect(dx0, y0 + 32, dx1 - dx0, y1 - y0 - 36, 'S', 3.2, hgt=0.5)
            K.text(lay, 'S 2', (dx0 + dx1) // 2, y0 + 40, 'P', 4.8, center=True)
            lay.rect(dx1 - 4, y0 + 58, 2, 6, 'S', 5.0)
            lay.poly([(dx0 - 1, y0 + 30), (dx0 - 7, y0 + 34), (dx0 - 5, y0 + 56), (dx0 - 1, y0 + 60)], 'D', 4.4,
                     hgt=0.9)

    # ================================================================== freight hatch, crates, lorry
    def lorry(self):
        lay = self.lay
        l0, l1 = L.LORRY
        top, tail = 204, 262
        nz = pg.value_noise(l1 - l0, 60, 4, 77, octaves=2)
        for x in range(l0, l1):
            for y in range(top + abs(x - (l0 + l1) // 2) // 10, 250):
                lay.px(x, y, 'G', 1.6 + (nz[y - top, x - l0] - 0.5) * 0.7 + (y < top + 6) * 0.5, flat=False,
                       hgt=0.4)
        lay.rect(l0 + 6, 214, l1 - l0 - 12, 36, 'N', 0.6)                     # the open back: darkness, crates
        for (cx, cy, cw, ch) in ((l0 + 10, 232, 18, 18), (l0 + 30, 236, 16, 14), (l0 + 48, 228, 14, 22)):
            lay.rect(cx, cy, cw, ch, 'P', 1.2, hgt=0.3)
            lay.hline(cx, cy, cw, 'P', 2.0)
        lay.rect(l0 + 4, 212, l1 - l0 - 8, 3, 'G', 2.6, hgt=0.6)                  # rolled-up flap
        for rx in range(l0 + 8, l1 - 6, 10):
            lay.vline(rx, 214, 6, 'P', 3.0)
        snowcap(lay, l0 + 2, top + 2, l1 - l0 - 4, 2, seed=44)
        lay.rect(l0, 250, l1 - l0, 5, 'S', 2.4, hgt=0.6)                          # tailgate
        lay.rect(l0 + 2, 255, l1 - l0 - 4, 9, 'I', 1.2)
        for (wx, flip) in ((l0 + 6, 0), (l1 - 20, 1)):
            m = K.disc(14)
            lay.put(m, wx, 260, 'I', 1.6, hgt=0.6)
            lay.rect(wx + 5, 265, 4, 4, 'S', 2.6)
        for tx in (l0 + 2, l1 - 6):
            lay.rect(tx, tail, 4, 3, 'R', 4.0, emis=True)
            lay.px(tx + 1, tail + 1, 'L', 5.0, emis=True)
        lay.rect((l0 + l1) // 2 - 8, tail, 16, 5, 'P', 4.6, hgt=0.5)
        K.pseudo_text(lay, (l0 + l1) // 2 - 6, tail + 2, 12, 1, 'I', 1.0, seed=3, gap=2)
        self.light('lorry_tail_l', (l0 + 4, tail + 1), 'warm', 0.3, 22, height=4)
        self.light('lorry_tail_r', (l1 - 4, tail + 1), 'warm', 0.3, 22, height=4)

    def hatch(self):
        lay = self.lay
        h0, h1 = L.HATCH
        # hoist frame: two A-legs and the top beam, trolley, chain and hook
        for lx in (h0 + 2, h1 - 4):
            K.cyl(lay, lx, 198, 3, B - 198, 'S', 3.4, hgt=0.6)
        lay.rect(h0, 196, h1 - h0, 4, 'S', 3.8, hgt=0.8)
        lay.hline(h0, 196, h1 - h0, 'S', 5.4, hgt=0.9)
        snowcap(lay, h0, 196, h1 - h0, 2, seed=96)
        hx = (h0 + h1) // 2 + 4
        lay.rect(hx - 4, 200, 9, 6, 'S', 2.4, hgt=0.7)
        for y in range(206, 268, 2):
            lay.px(hx, y, 'I', 2.6)
            lay.px(hx, y + 1, 'S', 3.6)
        lay.rect(hx - 2, 268, 5, 2, 'S', 3.8)
        lay.line(hx + 2, 270, hx + 3, 274, 'S', 3.8)
        lay.text('ACHTUNG LAST', h0 + 6, 202, 'L', 3.6)
        # the curb frame and the open hatch leaves (tread plate)
        lay.rect(h0, B - 8, h1 - h0, 8, 'C', 3.6, hgt=0.8)
        lay.hline(h0, B - 8, h1 - h0, 'C', 5.4, hgt=0.9)
        lay.rect(h0 + 8, B - 5, h1 - h0 - 16, 4, 'N', 0.4)
        for (lx, w_) in ((h0 + 3, 6), (h1 - 9, 6)):
            lay.rect(lx, 246, w_, B - 8 - 246, 'S', 3.0, hgt=0.7)
            for y in range(248, B - 8, 3):
                for x in range(lx + (y // 3) % 2, lx + w_, 2):
                    lay.px(x, y, 'S', 4.4, hgt=0.8)
        snowcap(lay, h0, B - 8, 8, 2, seed=97)
        snowcap(lay, h1 - 8, B - 8, 8, 2, seed=98)

    def crates(self):
        lay = self.lay
        c0, _c1 = L.CRATES
        stack = [(c0, 270, 32, 18), (c0 + 1, 253, 31, 17), (c0 + 2, 238, 30, 15)]
        for i, (x, y, w, h) in enumerate(stack):
            lay.rect(x, y, w, h, 'P', 3.0, hgt=0.6)
            for yy in range(y + 3, y + h, 4):
                lay.hline(x, yy, w, 'P', 2.2, hgt=0.3)
            lay.rect(x, y, w, 1, 'P', 4.4, hgt=0.8)
            for cx in (x, x + w - 2):
                lay.rect(cx, y, 2, h, 'S', 2.6, hgt=0.7)
            K.text(lay, 'C-17/45', x + w // 2 + 1, y + (h - 5) // 2, 'I', 1.0, center=True)
            if i == len(stack) - 1:
                snowcap(lay, x, y, w, 2, seed=i + 40)
        # the split crate: boards splayed, cards fanned into the snow
        s0, s1 = L.SPLIT_CRATE
        lay.poly([(s0, 288), (s0 + 4, 272), (s1 - 6, 270), (s1, 286)], 'P', 2.4, hgt=0.5)
        lay.poly([(s0 + 2, 274), (s0 + 14, 266), (s0 + 16, 269), (s0 + 4, 277)], 'P', 3.6, hgt=0.7)
        lay.line(s1 - 4, 271, s1 + 4, 266, 'P', 3.4, hgt=0.6)
        K.text(lay, 'C-17', s0 + 4, 279, 'I', 1.2)
        rng = np.random.default_rng(417)
        for _ in range(26):
            cx, cy = s0 + int(rng.integers(-4, 26)), 283 + int(rng.integers(0, 10))
            lay.rect(cx, cy, 3, 2, 'P', 4.6 + rng.random() * 0.6, hgt=0.4)
            lay.px(cx, cy + 1, 'P', 3.0)
        cx, cy = L.CARD_0417
        lay.rect(cx - 3, cy - 1, 6, 3, 'P', 5.2, hgt=0.4, crisp=True)
        lay.hline(cx - 2, cy, 3, 'I', 1.4)
        lay.vline(cx + 3, cy - 1, 3, 'P', 3.2)                                       # perforated edge

    # ================================================================== the site hoarding of the axis
    def fence(self):
        lay = self.lay
        f0, f1 = L.FENCE
        rng = np.random.default_rng(800)
        for x in range(f0, f1 + 2, 6):
            t = 2.6 + rng.random() * 0.8
            top = 212 + int(rng.integers(-2, 3))
            lay.rect(x, top, 6, B - top, 'P', t, hgt=0.5)
            lay.vline(x, top, B - top, 'P', 1.4)
            lay.vline(x + 1, top, B - top, 'P', t + 0.9, hgt=0.6)
            snowcap(lay, x, top, 6, 2, seed=x)
        for yy in (226, 270):
            lay.rect(f0, yy, f1 - f0 + 2, 3, 'P', 2.0, hgt=0.6)
        lay.rect(f0 + 4, 236, 40, 24, 'P', 5.0, hgt=0.4)
        lay.rect(f0 + 4, 236, 40, 1, 'P', 3.4)
        K.text(lay, 'BAUSTELLE', f0 + 24, 239, 'R', 3.2, center=True)
        K.text(lay, 'BETRETEN', f0 + 24, 246, 'I', 1.0, center=True)
        K.text(lay, 'VERBOTEN', f0 + 24, 252, 'I', 1.0, center=True)
        lay.rect(f1 - 8, 196, 3, B - 196, 'S', 2.6, hgt=0.6)
        lay.rect(f1 - 10, 192, 7, 5, 'R', 2.6, hgt=0.8)
        lay.rect(f1 - 9, 193, 5, 3, 'R', 3.8, emis=True)
        self.light('fence_blinker', (f1 - 7, 194), 'warm', 0.25, 26, height=6)
        snowcap(lay, f0, 212, f1 - f0, 1, seed=81)

    # ================================================================== ground: track bed, walk band, street
    def ground(self):
        lay = self.lay
        nz = pg.value_noise(W, H, 18, 301, octaves=3)
        fine = pg.value_noise(W, H, 3, 302, octaves=2)
        streak = np.repeat(pg.value_noise(W // 8 + 2, H, 3, 303, octaves=2), 8, axis=1)[:, :W]
        rng = np.random.default_rng(306)
        # far track bed + pavement island under snow; the walk band trodden grey, a sett peeking here and there
        h0 = 312 - B
        band = np.zeros((h0, W), bool)
        band[296 - B:307 - B, :] = True
        t = np.where(band, 3.9, 4.9) + (nz[B:312] - 0.5) * 0.9 + (fine[B:312] - 0.5) * 0.35
        lay.put(np.ones((h0, W), bool), 0, B, 'SN', t.astype(np.float32), flat=False, hgt=0.15)
        setts = band & (fine[B:312] > 0.78) & (nz[B:312] < 0.5)
        lay.put(setts, 0, B, 'C', 2.6, hgt=0.3)
        # rails of the far track (the tram stands on them) curving forward round the column
        for x in range(0, W):
            for ry, tone in ((L.FAR_RAIL_Y[0], 4.4), (L.FAR_RAIL_Y[1], 5.0)):
                y = ry
                if x > 640:
                    k = min(1.0, (x - 640) / 90.0)
                    y = int(round(ry + (L.NEAR_RAIL_Y[0] + (ry - L.FAR_RAIL_Y[0]) * 1.8 - ry) * (k ** 1.6)))
                    if x > 730:
                        continue
                lay.px(x, y, 'S', tone, hgt=0.6)
                lay.px(x, y + 1, 'N', 1.0)
        # kerb of the island and the near street with the near side of the loop
        lay.rect(0, 310, W, 2, 'C', 4.6, hgt=0.7)
        lay.rect(0, 312, W, 1, 'C', 1.6)
        # the street: dark wet setts, ploughed slush in long streaks, the lamps mirrored in the wet
        hs = H - 313
        base = 1.9 + (nz[313:] - 0.5) * 0.7 + (fine[313:] - 0.5) * 0.25
        lay.put(np.ones((hs, W), bool), 0, 313, 'C', base.astype(np.float32), flat=False, hgt=0.05)
        slush = (streak[313:] > 0.6) & (fine[313:] > 0.25)
        lay.put(slush, 0, 313, 'SN', (3.2 + (streak[313:] - 0.6) * 4).astype(np.float32), flat=False, hgt=0.1)
        for (rx, half, ramp, top) in ((L.LAMP_LOOP[0], 22, 'L', 3.6), ((L.TRAM[0] + L.TRAM[1]) // 2, 90, 'L', 2.6),
                                      ((L.CASE[0] + L.CASE[1]) // 2, 8, 'SN', 5.4)):
            for y in range(316, 352):
                k = 1 - (y - 316) / 36.0
                for x in range(rx - half, rx + half + 1):
                    f = (1 - abs(x - rx) / (half + 1)) * k
                    if fine[y, x] < f * 0.9 and (y + x // 2) % 2 == 0 and streak[y, x] < 0.62:
                        lay.px(x, y, ramp, top - (1 - f) * 1.4, hgt=0.0)
        for x in range(0, 740):
            for ry, tone in ((L.NEAR_RAIL_Y[0], 4.0), (L.NEAR_RAIL_Y[1], 4.8)):
                y = ry
                if x > 640:
                    k = min(1.0, (x - 640) / 90.0)
                    y = int(round(ry - (ry - L.FAR_RAIL_Y[0] - (ry - L.NEAR_RAIL_Y[0]) * 0.5) * (k ** 0.7)))
                if y < 312:
                    continue
                lay.px(x, y, 'S', tone, hgt=0.5)
                lay.px(x, y - 1, 'N', 0.8)
                lay.px(x, y + 1, 'N', 1.4)
        # snow banks along the island kerb, ploughed slush, footprints in the walk band
        for x in range(W):
            hh = int(3 + 2 * math.sin(x * 0.09) + rng.random() * 1.5)
            for k in range(hh):
                lay.px(x, 312 + k, 'SN', 5.0 - k * 0.5, hgt=0.4)
        for i in range(140):
            fx_, fy = int(rng.integers(10, W - 10)), int(rng.integers(297, 306))
            lay.rect(fx_, fy, 2, 1, 'SN', 3.0, hgt=-0.1)
        # manhole cover in the street
        m = K.disc(13)
        lay.put(m[3:9, :], 420, 344, 'S', 2.2, hgt=0.3)

    # ================================================================== ambient + build
    def ambient(self):
        lay = self.lay
        f = np.zeros((H, W), np.float32)
        ys = np.arange(H, dtype=np.float32)[:, None]
        xs = np.arange(W, dtype=np.float32)[None, :]
        f += -0.6 * np.clip((120 - ys) / 120, 0, 1)                    # upper facades lose the street glow
        f += -0.5 * np.clip((40 - xs) / 40, 0, 1)
        f += -0.4 * np.clip((ys - 330) / 30, 0, 1)
        f[lay.emis] = 0
        lay.amb_field(f)

    def scene_lights(self):
        return [
            {'name': 'dawn_sky', 'pos': (420.0, -80.0), 'kind': 'white', 'energy': 0.55, 'radius': 760, 'height': 120},
            {'name': 'snow_bounce', 'pos': (420.0, 360.0), 'kind': 'white', 'energy': 0.35, 'radius': 420,
             'height': 40},
        ]

    def build(self):
        self.lot()
        self.tree()
        self.house11()
        self.house9()
        for x in L.POLES:
            self.pole(x)
        self.lorry()
        self.shelter()
        self.tram()
        self.column(bared=bool(self.cfg.get('bared')))
        self.hatch()
        self.crates()
        self.fence()
        self.wires()
        self.ground()
        self.ambient()
        return self.lay

    def all_lights(self):
        return self.scene_lights() + self.lights


def bake_street(cfg: dict | None = None):
    st = Street(cfg)
    st.build()
    lights = st.all_lights()
    F = K.light_fields(st.lay, lights)
    K.add_pools(F, lights, L.BASE_Y + 6, H, W)
    K.resolve(st.lay, F, exposure=0.92)
    return st


# =========================================================================== distant layers (unlit, hazed)
def sky_layer(w=700, h=260):
    lay = K.tlayer(w, h, 'sky', 'loop')
    ys = np.arange(h, dtype=np.float32)[:, None] / h
    nz = K.periodic_noise(w, h, 90, 14, 5, octaves=4)
    t = 0.6 + ys[:, 0][:, None] * 4.6 + (nz - 0.5) * 0.6
    band = np.exp(-((ys - 0.62) / 0.08) ** 2) * (nz > 0.48) * 1.2              # low stratus, lit from below
    t = t - band * 0.8 + np.exp(-((ys - 0.66) / 0.03) ** 2) * (nz > 0.55) * 0.9
    lay.put(np.ones((h, w), bool), 0, 0, 'D', np.clip(t, 0, 6.2), flat=False)
    rng = np.random.default_rng(16)
    for _ in range(46):
        x, y = int(rng.integers(0, w)), int(rng.integers(2, int(h * 0.38)))
        lay.px(x, y, 'SN', 4.0 + rng.random() * 2.5)
    K.resolve(lay, None, exposure=1.0)
    return lay


def dome_layer(hist=False, w=210, h=150):
    """The Great Hall far away in the dawn haze: dome, lantern, the cubic base with its pilasters, banners."""
    lay = K.tlayer(w, h, 'dome', 'loop')
    cx, base_y, r = w // 2, 112, 84
    for x in range(w):
        dx = (x - cx) / r
        if abs(dx) > 1:
            continue
        hh = int(r * 0.62 * math.sqrt(1 - dx * dx))
        for y in range(base_y - 12 - hh, base_y - 12):
            rib = (int((x - cx) / 7) != int((x - cx - 1) / 7))
            lay.px(x, y, 'D', 3.0 + (1 - dx) * 0.6 - (y - (base_y - 12 - hh)) * 0.012 + rib * 0.4, flat=False)
        lay.px(x, base_y - 12 - hh, 'D', 4.8)
    lay.rect(cx - 7, base_y - 12 - int(r * 0.62) - 14, 14, 15, 'D', 3.4)
    lay.rect(cx - 2, base_y - 12 - int(r * 0.62) - 22, 4, 8, 'D', 3.0)
    lay.rect(cx - 5, base_y - 12 - int(r * 0.62) - 25, 10, 3, 'D', 2.6)            # the eagle on the globe, tiny
    lay.rect(10, base_y - 14, w - 20, h - base_y + 14, 'D', 3.4)
    lay.rect(4, base_y - 18, w - 8, 5, 'D', 3.9)
    for x in range(14, w - 12, 8):
        lay.rect(x, base_y - 10, 3, h - base_y + 10, 'D', 4.1)
    for bx in (34, 58, w - 64, w - 40):                                             # banners on the front
        if hist:
            lay.rect(bx, base_y - 8, 6, 30, 'R', 2.6)
            lay.rect(bx + 2, base_y + 2, 2, 2, 'SN', 5.4)
            lay.px(bx + 2, base_y + 3, 'I', 1.0)
        else:
            lay.rect(bx, base_y - 8, 6, 30, 'D', 1.6)
            lay.rect(bx + 2, base_y + 1, 2, 4, 'SN', 5.0)
    for x in range(w):                                                               # first light on the rim
        for y in range(h):
            if lay.rid[y, x] >= 0 and (x == 0 or lay.rid[y, x - 1] < 0) and x < cx:
                lay.px(x, y, 'D', 5.4)
    K.resolve(lay, None, exposure=1.0)
    return lay


def far_layer(w=720, h=190):
    """The north-south axis under construction: monumental shells in scaffolding, tower cranes."""
    lay = K.tlayer(w, h, 'far', 'loop')
    rng = np.random.default_rng(1961)
    ground = h - 14
    x = 0
    while x < w:
        bw = int(rng.integers(60, 130))
        bh = int(rng.integers(40, 90))
        if x + bw > 440 and x < 680:              # keep the front of the Great Hall (banners) in view
            bh = int(rng.integers(14, 26))
        top = ground - bh
        lay.rect(x, top, bw, bh, 'D', 2.4 + rng.random() * 0.4)
        for px_ in range(x + 3, x + bw - 2, 6):
            lay.vline(px_, top + 4, bh - 4, 'D', 2.9)
        if rng.random() < 0.6:
            for sy in range(top - 12, top, 4):
                lay.hline(x + 4, sy, bw - 8, 'D', 2.2)
            for sx in range(x + 4, x + bw - 4, 10):
                lay.vline(sx, top - 12, 12, 'D', 2.2)
        lay.hline(x, top, bw, 'D', 3.6)
        for _ in range(int(bw * bh / 900)):
            if rng.random() < 0.35:
                wx, wy = x + int(rng.integers(4, bw - 4)), top + int(rng.integers(6, bh - 6))
                lay.rect(wx, wy, 2, 2, 'L', 3.6, emis=True)
        x += bw + int(rng.integers(6, 24))
    lay.rect(0, ground, w, h - ground, 'D', 3.2)
    for cx, ch, jib in ((120, 150, 70), (380, 168, 90), (610, 140, 60)):
        top = ground - ch
        for y in range(top, ground):
            lay.px(cx, y, 'D', 1.4)
            lay.px(cx + 3, y, 'D', 1.4)
            if (y - top) % 4 == 0:
                lay.hline(cx, y, 4, 'D', 1.2)
            if (y - top) % 8 < 4:
                lay.px(cx + 1 + ((y - top) % 4 > 1), y, 'D', 1.2)
        lay.rect(cx - jib // 3, top - 4, jib + jib // 3, 2, 'D', 1.2)
        lay.line(cx + 1, top - 12, cx + jib, top - 3, 'D', 1.6)
        lay.line(cx + 1, top - 12, cx - jib // 3, top - 3, 'D', 1.6)
        lay.rect(cx - jib // 3, top - 2, 6, 6, 'D', 1.0)
        lay.vline(cx + jib - 10, top - 2, 30, 'D', 1.4)
        lay.rect(cx - 2, top + 6, 8, 6, 'L', 2.6, emis=True)
    lay.amb_field(np.full((h, w), 0.0, np.float32))
    K.resolve(lay, None, exposure=1.0)
    return lay


CRANE_TOPS = ((120, 150), (380, 168), (610, 140))   # (x, height) in far-layer coordinates (fx: aviation lights)


def mid_layer(w=780, h=118):
    """Cleared blocks between the loop and the axis: the last tenements, site huts, an excavator."""
    lay = K.tlayer(w, h, 'mid', 'loop')
    rng = np.random.default_rng(1964)
    ground = h - 18
    for (x0, bw, bh, broken) in ((20, 90, 70, 0), (150, 70, 52, 1), (300, 110, 80, 0), (520, 80, 60, 1),
                                 (660, 100, 74, 0)):
        top = ground - bh
        for x in range(x0, x0 + bw):
            tt = top + (int(rng.integers(0, 4)) * 4 + int(6 * abs(math.sin(x * 0.05))) if broken else 0)
            lay.vline(x, tt, ground - tt, 'D', 1.6 + ((x - x0) % 11 == 0) * 0.4)
            lay.px(x, tt, 'SN', 3.8)
        for wy in range(top + 8, ground - 8, 14):
            for wx in range(x0 + 6, x0 + bw - 6, 12):
                if rng.random() < 0.12:
                    lay.rect(wx, wy, 4, 6, 'L', 3.4, emis=True)
                else:
                    lay.rect(wx, wy, 4, 6, 'N', 2.6)
    for hx in (240, 470):                                                           # site huts
        lay.rect(hx, ground - 16, 34, 16, 'P', 1.6)
        lay.rect(hx - 2, ground - 18, 38, 3, 'SN', 4.4)
        lay.rect(hx + 6, ground - 12, 6, 5, 'L', 3.8, emis=True)
    ex = 590                                                                        # excavator, still
    lay.rect(ex, ground - 14, 26, 10, 'D', 1.2)
    lay.rect(ex + 4, ground - 22, 12, 9, 'D', 1.4)
    lay.line(ex + 16, ground - 20, ex + 40, ground - 34, 'D', 1.2)
    lay.line(ex + 40, ground - 34, ex + 48, ground - 12, 'D', 1.2)
    lay.rect(ex + 44, ground - 12, 7, 5, 'D', 1.2)
    for x in range(w):                                                              # snow field
        for y in range(ground, h):
            lay.px(x, y, 'SN', 3.0 + (y - ground) * 0.06 + ((x * 7 + y * 3) % 11 == 0) * 0.5)
    for lx in range(30, w, 70):
        lay.vline(lx, ground - 26, 26, 'D', 1.2)
        lay.px(lx, ground - 27, 'L', 4.6, emis=True)
    K.resolve(lay, None, exposure=1.0)
    return lay


def fg_layer(w=900, h=42):
    """Near-black snow banks, a bollard and the stop post at the bottom edge (parallax 1.25)."""
    lay = K.tlayer(w, h, 'fg_loop', 'loop')
    rng = np.random.default_rng(1250)
    for (cx, bw, bh) in ((40, 120, 22), (330, 70, 14), (520, 140, 18), (820, 110, 24)):
        for i in range(bw):
            hh = int(bh * math.sin(math.pi * (i + 0.5) / bw) ** 0.6 + rng.random() * 2)
            for k in range(hh):
                lay.px(cx - bw // 2 + i, h - 1 - k, 'N', 1.4 + (k == hh - 1) * 1.2)
    for bx in (210, 640):
        lay.rect(bx, h - 30, 5, 30, 'N', 0.8)
        lay.rect(bx - 1, h - 31, 7, 2, 'N', 2.0)
    K.resolve(lay, None, exposure=1.0)
    return lay
