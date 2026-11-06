"""env_c3p2_archive_room -- the main layer of L_C3_Registry (yard, souterrain rooms, floor), one per look.

Painted in tone space (env_c3p2_archive_kit.tlayer on the 'registry' super-ramps) for a configuration
(`cfg`, see STATES in env_c3p2_archive.py: green lamp on/off, ramp door open/shut, clock, the objects the
story takes away, fire 0/1/2), baked with that configuration's lights and resolved palette-pure.
Glass of the high windows and the gate opening are left transparent: outside.png shows through them.
"""
from __future__ import annotations

import math

import numpy as np

import env_c3p2_archive_kit as K
import env_c3p2_archive_layout as L

R = K.R
W, H = L.WORLD_W, L.WORLD_H
FL = L.FLOOR


# =========================================================================== small shapes
def _cyl_rect(lay, x, y, w, h, ramp, tone, hgt=0.6, axis='h', amp=1.2):
    """A pipe / pole: tone + relief rounded across its thickness."""
    if axis == 'h':
        for i in range(h):
            c = (i + 0.5) / h * 2 - 1
            lay.rect(x, y + i, w, 1, ramp, tone + amp * (0.5 - abs(c + 0.35)) , hgt=hgt * math.sqrt(max(0, 1 - c * c)))
    else:
        for i in range(w):
            c = (i + 0.5) / w * 2 - 1
            lay.rect(x + i, y, 1, h, ramp, tone + amp * (0.5 - abs(c + 0.35)), hgt=hgt * math.sqrt(max(0, 1 - c * c)))


class Room:
    def __init__(self, cfg: dict):
        self.cfg = cfg
        self.lay = K.tlayer(W, H, 'room')
        self.glass = np.zeros((H, W), bool)
        self.lights: list[dict] = []
        self.windows: list[tuple] = []        # (x0, y0, x1, y1) interior high windows (glass rects)
        self.info: dict = {}
        self.fire = int(cfg.get('fire', 0))
        self.hist = bool(cfg.get('hist', False))

    # ------------------------------------------------------------------ helpers
    def cut(self, x, y, w, h):
        self.lay.erase(x, y, w, h)
        self.glass[max(0, y):y + h, max(0, x):x + w] = True

    def light(self, name, pos, kind, energy, radius, height=24, **kw):
        d = {'name': name, 'pos': (float(pos[0]), float(pos[1])), 'kind': kind, 'energy': energy, 'radius': radius,
             'height': height}
        d.update(kw)
        self.lights.append(d)
        return d

    # ================================================================== interior shell
    def shell(self):
        lay = self.lay
        x0 = L.PIER[0]
        w = W - x0
        ys = np.arange(H, dtype=np.float32)[:, None]
        # limewashed brick: the wash is thin and patchy, cold grey-white in the night
        base = 3.7 + 0.35 * np.clip((ys - 60) / 160, 0, 1) + np.zeros((1, w), np.float32)
        nz = K.noise(w, H, 22, 11) * 0.55 + K.noise(w, H, 6, 12, octaves=2) * 0.25
        t = K.bricks(lay, x0, 0, w, FL, 'W', 0.0, seed=21, course=4, length=10, joint=-0.45, var=0.18)
        lay.put(np.ones((FL, w), bool), x0, 0, 'W', (base[:FL] + nz[:FL] + t), flat=False)
        # flaked wash: bare brick shows through in a few larger, muted islands
        flake = (K.noise(w, FL, 26, 31, octaves=3) > 0.27) & (K.noise(w, FL, 5, 32, octaves=2) > -0.08)
        bt = np.zeros((FL, w), np.float32)
        for row in range(0, FL, 4):
            off = (row // 4) % 2 * 5
            for bx in range(-10, w + 10, 10):
                a_, b_ = max(0, bx + off), min(w, bx + off + 9)
                if b_ > a_:
                    bt[row:row + 3, a_:b_] = 2.2 + ((bx * 7 + row * 13) % 5) * 0.18
            bt[min(FL - 1, row + 3), :] = 1.0
        lay.put(flake, x0, 0, 'K', bt, hgt=0.08, flat=False)
        # Planarchiv: plastered and painted cream; Magazin: bare brick (industrial)
        for (rx0, rx1, kind) in ((L.PART2[1], L.PART3[0], 'plaster'), (L.PART3[1], W, 'brick')):
            ww = rx1 - rx0
            if kind == 'plaster':
                pz = K.noise(ww, FL, 24, 35) * 0.35 + K.noise(ww, FL, 3, 36, octaves=1) * 0.08
                lay.put(np.ones((FL, ww), bool), rx0, 0, 'G', 3.3 + pz, hgt=0.02, flat=False)
                lay.rect(rx0, 100, ww, 1, 'G', 2.0, hgt=0.1)                 # paint line under the ceiling zone
                lay.put(np.ones((100, ww), bool), rx0, 0, 'W', 3.6 + pz[:100], hgt=0.02, flat=False)
                cracks = K.noise(ww, FL, 7, 37, octaves=2)
                lay.put((np.abs(cracks) < 0.005) & (K.noise(ww, FL, 30, 34) > 0.15), rx0, 0, 'G', 2.2)
            else:
                K.bricks(lay, rx0, 0, ww, FL, 'K', 3.2, seed=38, course=4, length=10, joint=-1.0, var=0.3)
                lay.put(np.ones((FL, ww), bool) & (K.noise(ww, FL, 20, 39) > 0.15), rx0, 0, 'K', None)
        # damp tide-line and salt bloom above the plinth
        damp = np.zeros((FL, w), bool)
        prof = (L.DADO_Y - 18 + 8 * K.noise(w, 1, 30, 41)[0]).astype(int)
        for xx in range(w):
            damp[prof[xx]:L.DADO_Y, xx] = True
        lay.shade_mask(damp, x0, 0, -0.45)
        # oil-paint dado (green) with a dark lining stripe, tar plinth
        dz = K.noise(w, FL - L.DADO_Y, 14, 44) * 0.35
        lay.put(np.ones((FL - L.DADO_Y, w), bool), x0, L.DADO_Y, 'G', 1.9 + dz, hgt=0.05, flat=False)
        lay.rect(x0, L.DADO_Y - 2, w, 1, 'G', 1.0, hgt=0.1)
        lay.rect(x0, L.DADO_Y - 1, w, 1, 'G', 2.6, hgt=0.15)
        lay.rect(x0, L.DADO_Y, w, 1, 'G', 1.4, hgt=0.05)
        scuff = K.noise(w, 1, 4, 47)[0]
        for xx in range(w):
            if scuff[xx] > 0.25:
                lay.rect(x0 + xx, L.DADO_Y + 22 + int(scuff[xx] * 6), 1, 2, 'G', 1.2)
        lay.rect(x0, L.PLINTH_Y, w, FL - L.PLINTH_Y, 'I', 1.4, hgt=0.1)
        lay.rect(x0, L.PLINTH_Y, w, 1, 'I', 2.6, hgt=0.15)
        self.vaults()
        self.services()

    def vaults(self):
        """Prussian cap vaults between riveted I-beams (seen from below, per-room perspective)."""
        lay = self.lay
        bays = [(L.PIER[1], L.PART1[0], 4), (L.PART1[1], L.PART2[0], 7), (L.PART2[1], L.PART3[0], 4),
                (L.PART3[1], W, 5)]
        sp = L.VAULT_SPRING
        for (rx0, rx1, n) in bays:
            vp = (rx0 + rx1) / 2.0
            bw = (rx1 - rx0) / n
            beams = [rx0 + i * bw for i in range(n + 1)]
            # soffit (brick, dark) above the springing line
            for yy in range(0, sp + 1):
                f = (L.HORIZON - yy) / (L.HORIZON - sp)
                for xx in range(int(rx0), int(rx1)):
                    u = vp + (xx - vp) / f              # wall coordinate this soffit pixel belongs to
                    k = (u - rx0) / bw
                    fr = k - math.floor(k)
                    depth = 1 - abs(fr - 0.5) * 2       # 1 at the vault crown, 0 at the beams
                    course = int((sp - yy) * f * 0.5 + 0.5) % 3 == 0
                    tone = 3.0 + 1.0 * depth - 0.02 * (sp - yy) + (-0.6 if course else 0.0)
                    lay.px(xx, yy, 'W', tone, hgt=0.2 + depth * 0.5)
            # lunettes: the wall's top follows each vault's segmental arch
            for i in range(n):
                a, b = beams[i], beams[i + 1]
                for xx in range(int(a), int(b)):
                    c = (xx + 0.5 - (a + b) / 2) / ((b - a) / 2)
                    top = int(round(sp - 12 * math.sqrt(max(0.0, 1 - c * c))))
                    lay.rect(xx, top, 1, sp - top, 'W', 3.2 + 0.4 * (1 - abs(c)), hgt=0.0)
                    lay.px(xx, top, 'K', 1.0, hgt=0.3)
                    lay.px(xx, top + 1, 'W', 2.4, hgt=0.1)
            # beams: flange on the wall + the underside receding toward the viewer
            for bx in beams:
                for yy in range(0, sp + 4):
                    f = (L.HORIZON - yy) / (L.HORIZON - sp) if yy <= sp else 1.0
                    xx = int(round(vp + (bx - vp) * f))
                    lay.rect(xx - 2, yy, 5, 1, 'S', 2.0, hgt=0.7)
                    lay.px(xx - 2, yy, 'S', 3.2, hgt=0.75)
                    lay.px(xx + 2, yy, 'S', 1.2, hgt=0.6)
                    if yy % 5 == 2:
                        lay.px(xx, yy, 'S', 3.6, hgt=0.8)            # rivet heads on the flange
                lay.rect(int(bx) - 4, sp, 9, 2, 'S', 2.4, hgt=0.8)  # bearing plate
                lay.rect(int(bx) - 4, sp + 2, 9, 1, 'S', 1.0, hgt=0.2)

    def services(self):
        """Heating pipes, conduit, cable runs on the back wall of the souterrain."""
        lay = self.lay
        x0 = L.PIER[1]
        for (py, th, tone) in ((94, 4, 3.2), (101, 3, 2.8)):
            _cyl_rect(lay, x0, py, W - x0, th, 'S', tone, hgt=0.9)
        for x in range(x0 + 10, W, 34):                     # wall clamps
            lay.rect(x, 92, 2, 13, 'S', 1.6, hgt=1.0)
            lay.px(x, 92, 'S', 3.6, hgt=1.0)
        rng = np.random.default_rng(5)
        for (lx0, lx1) in ((470, 560), (760, 840), (1300, 1420), (1600, 1700)):  # lagging (wrapped sections)
            for x in range(lx0, lx1):
                for y in range(93, 99):
                    lay.px(x, y, 'P', 2.4 + ((x + y * 2) % 4 == 0) * 0.6 - (y == 98) * 0.8 + rng.normal(0, 0.15),
                           hgt=1.0)
            lay.rect(lx0, 92, 1, 8, 'P', 1.4, hgt=1.0); lay.rect(lx1, 92, 1, 8, 'P', 1.4, hgt=1.0)
        for vx in (620, 1120, 1580):                        # valves with red hand wheels
            lay.rect(vx - 1, 88, 3, 6, 'S', 2.4, hgt=1.0)
            lay.rect(vx - 4, 86, 9, 2, 'R', 2.2, hgt=1.1)
            lay.px(vx - 4, 86, 'R', 3.4, hgt=1.1)
        # pressure gauge
        g = K.disc(9)
        lay.put(g, 1004 - 4, 80, 'S', 2.0, hgt=1.0)
        lay.put(K.disc(7), 1004 - 3, 81, 'P', 4.6, hgt=1.1)
        lay.line(1004, 84, 1006, 82, 'I', 0.5)
        lay.rect(1003, 89, 3, 5, 'S', 2.2, hgt=1.0)
        # conduit with porcelain insulators + junction boxes
        lay.rect(x0, 112, W - x0, 2, 'S', 2.2, hgt=0.6)
        lay.rect(x0, 112, W - x0, 1, 'S', 3.4, hgt=0.65)
        for x in range(x0 + 20, W, 52):
            lay.rect(x, 110, 3, 6, 'P', 4.0, hgt=0.8)
            lay.px(x + 2, 111, 'P', 2.4, hgt=0.7)
        for jx in (498, 742, 1010, 1452, 1736):
            K.bevel(lay, jx - 4, 108, 9, 9, 'S', 2.6, hi=3.6, lo=1.2, hgt=0.7)
            lay.px(jx, 112, 'I', 0.6)

    # ------------------------------------------------------------------ high windows (light wells)
    def high_window(self, cx, glow=True):
        lay = self.lay
        w = 30
        x0 = cx - w // 2
        y0, y1 = L.WIN_Y
        h = y1 - y0
        # reveal (deep, splayed sill)
        lay.rect(x0 - 4, y0 - 4, w + 8, h + 12, 'W', 2.6, hgt=-0.2)
        m = K.arch_mask(w + 8, h + 8, 6)
        lay.put(m, x0 - 4, y0 - 4, 'W', 2.2, hgt=-0.3)
        for i in range(6):                                   # sloped sill (lit from the glass)
            lay.rect(x0 - 4 + i // 2, y1 + 1 + i, w + 8 - i, 1, 'W', 4.6 - i * 0.25, hgt=0.4)
        # iron frame + glass (transparent) + bars outside + frost on the panes
        fm = K.arch_mask(w, h, 5)
        lay.put(fm, x0, y0, 'S', 1.6, hgt=0.6)
        inner = K.arch_mask(w - 4, h - 4, 4)
        gx, gy = x0 + 2, y0 + 2
        lay.erase_mask(inner, gx, gy)
        self.glass[gy:gy + inner.shape[0], gx:gx + inner.shape[1]] |= inner
        lay.rect(cx - 1, y0 + 2, 2, h - 3, 'S', 1.8, hgt=0.7)              # mullion
        lay.rect(x0 + 2, y0 + h // 2, w - 4, 1, 'S', 1.8, hgt=0.7)          # transom
        for bx in range(x0 + 6, x0 + w - 3, 6):                              # bars (outside the glass)
            for yy in range(y0 + 3, y1 - 1):
                if self.glass[yy, bx]:
                    lay.px(bx, yy, 'I', 1.0, hgt=0.4)
                    self.glass[yy, bx] = False
        rng = np.random.default_rng(cx)
        for yy in range(y1 - 6, y1 - 1):                                     # frost / condensation
            for xx in range(gx, gx + w - 4):
                if self.glass[yy, xx] and rng.random() < (yy - (y1 - 7)) * 0.16:
                    lay.px(xx, yy, 'C', 6.0 + rng.random(), hgt=0.05, unlit=True)
                    self.glass[yy, xx] = False
        self.windows.append((gx, gy, gx + w - 4, gy + inner.shape[0]))
        if glow:
            k = 0.45 if self.fire == 1 else (0.25 if self.fire == 2 else 1.0)
            self.light('win_%d' % cx, (cx, y0 + 18), 'cold', 0.85 * k, 140, -14,
                       pool=0.35 * k, pool_dx=34, pool_depth=46, pool_w=12, pool_spread=0.5)

    # ================================================================== yard (exterior)
    def yard(self):
        lay = self.lay
        x1 = L.PIER[0]
        # night sky over the roofs: low cloud lit by the town (no stars: it is snowing)
        sky = K.noise(x1, 30, 18, 61) * 0.6
        ys = np.arange(30, dtype=np.float32)[:, None]
        lay.put(np.ones((30, x1), bool), 0, 0, 'C', 1.4 + ys / 30 * 0.9 + sky, hgt=0.0, flat=False, unlit=True)
        # facade: cream render (paper ramp) with rusticated souterrain storey
        fx0 = L.FACADE[0]
        fw = x1 - fx0
        fy0 = L.CORNICE_Y[1]
        rz = K.noise(fw, FL - fy0, 16, 63) * 0.4 + K.noise(fw, FL - fy0, 4, 64, octaves=2) * 0.2
        lay.put(np.ones((FL - fy0, fw), bool), fx0, fy0, 'W', 4.0 + rz, hgt=0.1, flat=False)
        # cornice (stepped profile, snow on top) along the whole yard incl. the posts' wall
        prof = [(1.4, 0.2), (3.2, 0.6), (4.0, 0.8), (2.4, 0.6), (3.6, 0.9), (4.4, 1.0), (3.0, 0.8), (1.8, 0.5),
                (2.8, 0.6), (3.4, 0.6), (2.2, 0.4), (1.2, 0.2), (2.6, 0.3), (2.0, 0.2), (1.0, 0.1), (1.6, 0.1)]
        for i, (t, hh) in enumerate(prof):
            lay.rect(fx0 - 4, L.CORNICE_Y[0] + i, fw + 4, 1, 'P', t, hgt=hh)
        for x in range(fx0, x1, 6):                                   # modillions
            lay.rect(x + 1, L.CORNICE_Y[0] + 9, 3, 3, 'P', 3.6, hgt=1.0)
            lay.px(x + 3, L.CORNICE_Y[0] + 11, 'P', 1.4)
        self._snow_cap(fx0 - 4, L.CORNICE_Y[0] - 3, fw + 4, 4, seed=1)
        # upper-floor windows (one lit, high up)
        for i, wx in enumerate((98, 166, 234, 302)):
            self._facade_window(wx, 52, 24, 44, lit=(i == 3), seed=10 + i)
        # string course
        lay.rect(fx0, 112, fw, 4, 'P', 3.0, hgt=0.8)
        lay.rect(fx0, 112, fw, 1, 'P', 4.2, hgt=0.9)
        lay.rect(fx0, 116, fw, 1, 'P', 0.8, hgt=0.2)
        self._snow_cap(fx0, 109, fw, 3, seed=2)
        # ground-floor windows (tall, dark, shutters closed on one)
        for i, wx in enumerate((98, 166, 234, 302)):
            self._facade_window(wx, 126, 24, 58, lit=False, seed=20 + i, shutter=(i == 1))
        # water table + rusticated souterrain storey
        lay.rect(fx0, 196, fw, 5, 'P', 3.2, hgt=0.9)
        lay.rect(fx0, 196, fw, 1, 'P', 4.4, hgt=1.0)
        lay.rect(fx0, 201, fw, 1, 'P', 0.6, hgt=0.1)
        self._snow_cap(fx0, 193, fw, 3, seed=3)
        for row, yy in enumerate(range(202, FL, 9)):
            lay.rect(fx0, yy + 8, fw, 1, 'P', 0.6, hgt=0.0)
            off = 0 if row % 2 else 14
            for xx in range(fx0 + off, x1, 28):
                lay.rect(xx, yy, 1, 8, 'P', 0.8, hgt=0.0)
            lay.rect(fx0, yy, fw, 1, 'P', 2.6, hgt=0.4)
        for (sx, sw) in ((90, 22), (290, 20)):                         # small barred souterrain windows
            K.recess(lay, sx, 232, sw, 22, 'N', 0.6, shadow=0.2, light=1.6)
            for bx in range(sx + 3, sx + sw - 1, 4):
                lay.rect(bx, 232, 1, 22, 'I', 1.6, hgt=0.5)
            lay.rect(sx - 2, 254, sw + 4, 2, 'P', 3.4, hgt=0.7)
            self._snow_cap(sx - 2, 252, sw + 4, 2, seed=sx)
            if self.fire:
                lay.rect(sx + 1, 236, sw - 2, 16, 'F', 1.6 + (self.fire - 1) * 0.8, emis=True)
                for bx in range(sx + 3, sx + sw - 1, 4):
                    lay.rect(bx, 232, 1, 22, 'I', 1.0, hgt=0.5)
        self.gate()
        self.bracket_lamp()
        self.downpipe(366)
        self.ramp_and_hatch()

    def _snow_cap(self, x, y, w, h, seed=0):
        lay = self.lay
        rng = np.random.default_rng(seed + 400)
        for xx in range(x, x + w):
            hh = h + (1 if rng.random() < 0.35 else 0) - (1 if rng.random() < 0.15 else 0)
            for k in range(hh):
                lay.px(xx, y + h - 1 - k + 1, 'SN', 2.6 + k * 0.7 + rng.random() * 0.4, hgt=0.6 + k * 0.1)
            if rng.random() < 0.06:                                  # icicle
                for k in range(rng.integers(2, 5)):
                    lay.px(xx, y + h + 1 + k, 'C', 6.0 - k * 0.6, hgt=0.4)

    def _facade_window(self, x, y, w, h, lit=False, seed=0, shutter=False):
        lay = self.lay
        K.bevel(lay, x - 3, y - 3, w + 6, h + 6, 'P', 2.8, hi=3.8, lo=1.0, hgt=0.7)     # surround
        lay.rect(x - 4, y - 7, w + 8, 4, 'P', 3.2, hgt=0.9)                               # pediment slab
        lay.rect(x - 4, y - 7, w + 8, 1, 'P', 4.2, hgt=1.0)
        self._snow_cap(x - 4, y - 10, w + 8, 3, seed=seed)
        if lit:
            lay.rect(x, y, w, h, 'P', 5.2, emis=True)
            # net curtain + a lamp shade silhouette
            for yy in range(y, y + h):
                for xx in range(x, x + w):
                    if (xx + yy) % 3 == 0:
                        lay.px(xx, yy, 'B', 4.6, emis=True)
            lay.rect(x + 3, y + 22, 9, 6, 'D', 3.0, emis=True)
            lay.rect(x + 6, y + 28, 2, 14, 'D', 2.0, emis=True)
            self.light('yard_lit_window', (x + w / 2, y + h / 2), 'warm', 0.35, 70, 6)
        elif shutter:
            for yy in range(y, y + h):
                lay.rect(x, yy, w, 1, 'D', 1.6 + (yy % 3 == 0) * 0.8, hgt=0.3)
            lay.rect(x + w // 2, y, 1, h, 'D', 0.8)
        else:
            gz = K.noise(w, h, 8, seed)
            lay.put(np.ones((h, w), bool), x, y, 'C', 1.2 + gz * 0.8 + np.linspace(0, 0.6, h)[:, None], hgt=0.0,
                    flat=False)
            for k in range(3):                                          # reflections of the snow
                lay.line(x + 2 + k * 7, y + h - 2, x + 8 + k * 7, y + h - 14, 'C', 3.4)
        lay.rect(x + w // 2, y, 1, h, 'P', 3.0, hgt=0.5)                  # sash bars
        lay.rect(x, y + h // 3, w, 1, 'P', 3.0, hgt=0.5)
        lay.rect(x - 4, y + h, w + 8, 3, 'P', 3.6, hgt=0.9)                # sill
        self._snow_cap(x - 4, y + h - 3, w + 8, 3, seed=seed + 50)

    def gate(self):
        lay = self.lay
        g0, g1 = L.GATE
        gy0 = L.GATE_Y[0]
        x1 = L.FACADE[0]
        # beyond the yard wall: the lane -- the neighbour's dark facade, a lantern, snow on the cobbles
        nz = K.noise(x1, FL - 30, 12, 71) * 0.5
        lay.put(np.ones((FL - 30, x1), bool), 0, 30, 'C', 1.5 + nz, hgt=0.0, flat=False)
        for (wx, wy) in ((6, 60), (34, 60), (6, 128), (34, 128)):
            K.recess(lay, wx, wy, 14, 30, 'N', 0.8, shadow=0.4, light=1.6)
            lay.rect(wx + 7, wy, 1, 30, 'C', 2.0)
            lay.rect(wx - 2, wy + 30, 18, 2, 'C', 3.0)
            self._snow_cap(wx - 2, wy + 27, 18, 2, seed=wx + wy)
        lay.rect(0, 44, x1, 3, 'C', 2.6, hgt=0.6)
        self._snow_cap(0, 41, x1, 3, seed=70)
        lay.rect(0, 248, x1, FL - 248, 'SN', 2.2, hgt=0.0)                  # the lane (snow, in shadow)
        for x in range(0, x1, 3):
            lay.px(x, 248 + (x * 7) % 5, 'SN', 3.0)
        # lantern on its bracket across the lane
        lx, ly = 30, 196
        lay.line(lx - 12, ly - 12, lx, ly - 12, 'I', 1.6)
        lay.rect(lx - 1, ly - 12, 2, 3, 'I', 1.6)
        lay.rect(lx - 3, ly - 9, 7, 2, 'I', 1.8)
        lay.rect(lx - 2, ly - 7, 5, 6, 'B', 5.4, emis=True)
        lay.rect(lx - 3, ly - 1, 7, 1, 'I', 1.8)
        lay.px(lx, ly - 10, 'SN', 5.0)
        self.light('lane_lamp', (lx, ly - 4), 'warm', 0.7, 80, 10)
        # yard-wall posts (sandstone, ball caps, snow)
        for (p0, p1) in L.GATE_POSTS:
            K.bevel(lay, p0, gy0 - 10, p1 - p0, FL - gy0 + 10, 'P', 2.4, hi=3.4, lo=1.0, hgt=0.9)
            for yy in range(gy0, FL, 12):
                lay.rect(p0, yy, p1 - p0, 1, 'P', 1.0)
            lay.rect(p0 - 1, gy0 - 14, p1 - p0 + 2, 4, 'P', 3.0, hgt=1.0)
            cx = (p0 + p1) // 2
            lay.put(K.disc(7), cx - 3, gy0 - 21, 'P', 3.2, hgt=1.2)
            self._snow_cap(cx - 4, gy0 - 25, 8, 3, seed=p0)
        # the iron gate: bars with spear tips, three rails, scrolls, the lock box (standing open a hand's width)
        rng = np.random.default_rng(7)
        for x in range(g0, g1):
            if (x - g0) % 4 == 1:
                lay.rect(x, gy0 + 2, 1, FL - gy0 - 2, 'I', 1.6, hgt=0.5)
                lay.px(x, gy0, 'I', 2.4, hgt=0.6)
                lay.px(x, gy0 + 1, 'I', 1.8, hgt=0.6)
        for yy in (gy0 + 6, gy0 + 40, FL - 8):
            lay.rect(g0, yy, g1 - g0, 2, 'I', 1.4, hgt=0.6)
        for x in range(g0 + 2, g1 - 2, 8):
            lay.px(x, gy0 + 4, 'I', 2.2); lay.px(x + 1, gy0 + 3, 'I', 2.2); lay.px(x + 2, gy0 + 4, 'I', 2.2)
        lay.rect((g0 + g1) // 2 - 3, gy0 + 44, 6, 8, 'I', 2.0, hgt=0.7)
        lay.px((g0 + g1) // 2, gy0 + 47, 'B', 3.0)
        # the right leaf stands ajar: a dark gap at the lock, the leaf's edge turned toward us
        mx = (g0 + g1) // 2
        lay.rect(mx + 1, gy0 + 2, 2, FL - gy0 - 2, 'N', 0.4, hgt=0.2)
        lay.rect(mx + 3, gy0 + 2, 1, FL - gy0 - 2, 'I', 2.8, hgt=0.7)
        # delivery sign in three languages on the facade beside the gate (exp_gate_sign)
        sx, sy = L.FACADE[0] + 4, 214
        lay.rect(sx + 1, sy + 17, 22, 1, 'W', 1.4)
        lay.rect(sx, sy, 22, 17, 'S', 1.6, hgt=0.6)
        lay.rect(sx + 1, sy + 1, 20, 15, 'P', 5.2, hgt=0.7)
        lay.rect(sx + 1, sy + 1, 20, 3, 'G', 2.4)
        K.text(lay, '7-18', sx + 11, sy + 5, 'I', 0.8, center=True)
        K.pseudo_text(lay, sx + 3, sy + 11, 16, 2, 'I', 1.6, seed=80, gap=2)
        for yy in (gy0 + 5, gy0 + 39, FL - 9):
            for x in range(g0, g1):
                if rng.random() < 0.7:
                    lay.px(x, yy, 'SN', 3.4 + rng.random(), hgt=0.7)

    def bracket_lamp(self):
        lay = self.lay
        cx, cy = L.LAMP_YARD
        # scroll bracket from the facade
        lay.rect(cx + 14, cy - 14, 3, 10, 'I', 1.6, hgt=0.6)
        lay.line(cx + 14, cy - 10, cx, cy - 10, 'I', 1.8)
        lay.line(cx + 14, cy - 9, cx + 4, cy - 9, 'I', 1.0)
        for (a, b) in ((cx + 10, cy - 7), (cx + 7, cy - 6), (cx + 5, cy - 7)):
            lay.px(a, b, 'I', 1.8)
        lay.rect(cx, cy - 10, 1, 4, 'I', 1.8)
        # enamel reflector shade + bulb (glow)
        for i in range(5):
            lay.rect(cx - 2 - i, cy - 6 + i, 5 + 2 * i, 1, 'P', 4.6 - i * 0.3, hgt=0.9)
        lay.rect(cx - 7, cy - 1, 15, 1, 'I', 1.4, hgt=0.6)
        lay.rect(cx - 2, cy, 5, 2, 'B', 5.6, emis=True)
        lay.px(cx, cy + 2, 'B', 6.0, emis=True)
        self._snow_cap(cx - 3, cy - 9, 7, 2, seed=99)
        self.light('yard_lamp', (cx, cy + 4), 'warm', 2.0, 200, 18, falloff=1.25,
                   cone=(0.0, 1.0, -0.15), pool=0.42, pool_depth=60, pool_w=16, pool_spread=1.0)

    def downpipe(self, x):
        lay = self.lay
        _cyl_rect(lay, x, 40, 4, FL - 44, 'S', 2.2, hgt=0.8, axis='v')
        for yy in range(52, FL - 10, 40):
            lay.rect(x - 1, yy, 6, 2, 'S', 1.2, hgt=0.9)
        lay.rect(x - 2, FL - 6, 7, 3, 'S', 2.0, hgt=0.8)        # shoe
        for k in range(4):
            lay.px(x + 1, FL - 3 + k // 2, 'C', 6.2 - k * 0.5)  # ice from the shoe

    def ramp_and_hatch(self):
        lay = self.lay
        # coal-chute hatch: cast iron plate set into the ground against the wall (drawn on the floor strip)
        self.info['hatch'] = L.HATCH

    # ================================================================== pier + ramp door
    def pier_and_door(self):
        lay = self.lay
        p0, p1 = L.PIER
        d0, d1 = L.DOOR
        dy0, dy1 = L.DOOR_Y
        # cut exterior wall: poche core, quoins on the yard face, plaster edge inside
        lay.rect(p0, 0, p1 - p0, FL, 'N', 1.0, hgt=0.0)
        for yy in range(0, FL, 10):
            wq = 8 if (yy // 10) % 2 else 5
            K.bevel(lay, p0, yy, wq, 9, 'P', 2.0, hi=3.0, lo=0.8, hgt=0.8)
        lay.rect(p1 - 3, 0, 3, FL, 'W', 2.6, hgt=0.3)
        lay.rect(p1 - 1, 0, 1, FL, 'W', 1.4, hgt=0.1)
        for yy in range(6, FL, 4):
            lay.rect(p0 + 9, yy, p1 - p0 - 12, 1, 'N', 1.8)
        # steel lintel + opening
        lay.rect(d0 - 3, dy0 - 6, d1 - d0 + 6, 6, 'S', 2.2, hgt=0.8)
        lay.rect(d0 - 3, dy0 - 6, d1 - d0 + 6, 1, 'S', 3.4, hgt=0.9)
        lay.rect(d0 - 3, dy0 - 1, d1 - d0 + 6, 1, 'S', 1.0, hgt=0.3)
        K.rivets(lay, d0 - 1, d1 + 2, dy0 - 4, 5)
        # reveal (jambs) seen into the depth of the wall
        lay.rect(d0, dy0, d1 - d0, dy1 - dy0, 'N', 0.6, hgt=-0.4)
        lay.rect(d0, dy0, 3, dy1 - dy0, 'W', 2.0, hgt=-0.2)
        lay.rect(d1 - 3, dy0, 3, dy1 - dy0, 'W', 1.6, hgt=-0.2)
        lay.rect(d0 - 1, dy1, d1 - d0 + 2, FL - dy1, 'S', 2.6, hgt=0.4)       # steel sill / threshold
        lay.rect(d0 - 1, dy1, d1 - d0 + 2, 1, 'S', 3.8, hgt=0.5)
        if not self.cfg.get('door_closed'):
            # night: the opening shows the snow-lit yard ramp beyond; the leaf stands open on the facade
            for yy in range(dy0 + 2, dy1):
                k = (yy - dy0) / (dy1 - dy0)
                lay.rect(d0 + 3, yy, d1 - d0 - 6, 1, 'C', 1.2 + 2.2 * k, hgt=-0.4)
            self._door_leaf(L.LEAF_OPEN[0], dy0 + 1, L.LEAF_OPEN[1] - L.LEAF_OPEN[0], dy1 - dy0 - 1, opened=True)
            # the bolt hangs open on the facade
            lay.rect(L.LEAF_OPEN[0] - 6, dy0 + 26, 5, 3, 'I', 2.2, hgt=0.8)
        else:
            self._door_leaf(d0, dy0, d1 - d0, dy1 - dy0, opened=False)
            # light of the snow through the gaps
            lay.rect(d0, dy1 - 1, d1 - d0, 1, 'C', 6.6, unlit=True)
            for yy in range(dy0 + 2, dy1, 3):
                lay.px(d0, yy, 'C', 5.4, unlit=True)

    def _door_leaf(self, x, y, w, h, opened):
        lay = self.lay
        tone = 2.0
        lay.rect(x, y, w, h, 'S', tone, hgt=0.6)
        lay.rect(x, y, w, 1, 'S', 3.4, hgt=0.7)
        lay.rect(x, y, 1, h, 'S', 3.0, hgt=0.7)
        lay.rect(x + w - 1, y, 1, h, 'S', 1.0, hgt=0.5)
        lay.rect(x, y + h - 1, w, 1, 'S', 1.0, hgt=0.5)
        for yy in (y + 4, y + h // 2, y + h - 5):                     # straps
            lay.rect(x + 1, yy, w - 2, 2, 'S', 2.8, hgt=0.8)
            K.rivets(lay, x + 2, x + w - 2, yy, 4, tone=4.2)
        lay.line(x + 2, y + h - 6, x + w - 3, y + 6, 'S', 2.6)        # diagonal brace
        lay.line(x + 3, y + h - 6, x + w - 2, y + 6, 'S', 1.4)
        rust = K.noise(w, h, 4, x) > 0.22
        lay.shade_mask(rust, x, y, -0.5)
        for k in range(6):
            lay.vline(x + 3 + k * 4 % (w - 4), y + h // 2 + 2, 6 + k % 3, 'K', 2.4)
        if not opened:
            lay.rect(x + w - 5, y + h // 2 - 4, 2, 8, 'I', 2.4, hgt=1.0)   # handle
            lay.rect(x + 2, y + h // 2 - 6, 2, 12, 'I', 0.6, hgt=0.2)      # keyhole shadow line

    # ================================================================== Annahme
    def annahme(self):
        lay = self.lay
        self.high_window(507)
        self.high_window(645)
        self.notice_board(410, 150)
        self.sign_plate(512, 124, ['ANNAHME', 'ПРИЁМ · RÉCEPTION'])
        self.smoke_sign(422, 208)
        self.chute_door()
        self.wall_clock(*L.CLOCK)
        self.fire_bell()
        self.fire_case()
        self.booth()
        self.desk()

    def notice_board(self, x, y):
        lay = self.lay
        w, h = 22, 40
        K.bevel(lay, x, y, w, h, 'D', 2.4, hi=3.4, lo=1.0, hgt=0.7)
        cz = K.noise(w - 4, h - 4, 3, x)
        lay.put(np.ones((h - 4, w - 4), bool), x + 2, y + 2, 'D', 3.4 + cz * 0.8, hgt=0.5, flat=False)
        rng = np.random.default_rng(x)
        for (px_, py_, pw, ph) in ((x + 3, y + 4, 8, 10), (x + 12, y + 3, 7, 12), (x + 4, y + 17, 9, 11),
                                   (x + 14, y + 18, 6, 8), (x + 5, y + 30, 12, 6)):
            lay.rect(px_, py_, pw, ph, 'P', 4.6 + rng.random() * 0.8, hgt=0.6)
            K.pseudo_text(lay, px_ + 1, py_ + 2, pw - 2, max(1, (ph - 3) // 2), 'I', 1.4, seed=px_ + py_)
            lay.px(px_ + pw // 2, py_, 'R', 3.2, hgt=0.8)
        K.text(lay, 'PLAN', x + w // 2, y + 5, 'I', 0.8, center=True)

    def sign_plate(self, cx, y, lines, ramp='P', tone=5.2, ink=('I', 1.0), border=('S', 1.6)):
        lay = self.lay
        wmax = max(K.text_width(s) for s in lines)
        w = wmax + 8
        h = 4 + len(lines) * 7
        x = cx - w // 2
        lay.rect(x + 1, y + h, w, 1, 'W', 1.6)
        lay.rect(x + w, y + 1, 1, h, 'W', 1.6)
        lay.rect(x, y, w, h, border[0], border[1], hgt=0.6)
        lay.rect(x + 1, y + 1, w - 2, h - 2, ramp, tone, hgt=0.7)
        for i, s in enumerate(lines):
            K.text(lay, s, cx, y + 3 + i * 7, ink[0], ink[1], center=True)
        lay.px(x + 2, y + 2, 'S', 3.0); lay.px(x + w - 3, y + 2, 'S', 3.0)
        return x, w

    def smoke_sign(self, x, y):
        """Enamel 'Rauchen verboten' plate, trilingual, red border."""
        lay = self.lay
        lines = ['RAUCHEN', 'VERBOTEN']
        w, h = 30, 18
        lay.rect(x + 1, y + h, w, 1, 'W', 1.6)
        lay.rect(x, y, w, h, 'R', 2.4, hgt=0.6)
        lay.rect(x + 1, y + 1, w - 2, h - 2, 'P', 5.6, hgt=0.7)
        for i, s in enumerate(lines):
            K.text(lay, s, x + w // 2, y + 3 + i * 6, 'R', 2.6, center=True)
        lay.rect(x + 3, y + 15, w - 6, 1, 'I', 2.2)

    def chute_door(self):
        lay = self.lay
        c0, c1 = L.CHUTE
        cy0 = L.CHUTE_Y[0]
        w, h = c1 - c0, FL - cy0
        lay.rect(c0 - 3, cy0 - 3, w + 6, h + 3, 'I', 1.2, hgt=0.6)                     # angle-iron frame
        lay.rect(c0 - 3, cy0 - 3, w + 6, 1, 'I', 2.6, hgt=0.7)
        lay.rect(c0, cy0, w, h, 'S', 1.8, hgt=0.5)
        K.recess(lay, c0 + 3, cy0 + 3, w - 6, h - 8, 'S', 2.4, shadow=1.0, light=3.2, hgt=0.4)
        lay.line(c0 + 4, cy0 + 4, c1 - 5, FL - 6, 'S', 3.0)
        lay.line(c0 + 4, FL - 6, c1 - 5, cy0 + 4, 'S', 3.0)
        K.rivets(lay, c0 + 2, c1 - 2, cy0 + 1, 4, tone=3.6)
        K.rivets(lay, c0 + 2, c1 - 2, FL - 3, 4, tone=3.6)
        for hy in (cy0 + 6, FL - 10):                                                   # hinges (left)
            lay.rect(c0 - 2, hy, 6, 3, 'I', 2.2, hgt=0.8)
        lay.rect(c1 - 6, cy0 + 14, 3, 10, 'I', 2.0, hgt=0.9)                           # latch lever
        lay.rect(c1 - 9, cy0 + 18, 9, 2, 'I', 2.6, hgt=1.0)
        rust = K.noise(w, h, 3, 909) > 0.2
        lay.shade_mask(rust, c0, cy0, -0.6)
        # cast plate "1909" above the door + faded stencil of the coal cellar
        lay.rect(c0 + 4, cy0 - 11, w - 8, 7, 'I', 1.6, hgt=0.7)
        K.text(lay, '1909', (c0 + c1) // 2, cy0 - 10, 'S', 4.0, center=True, hgt=0.9)
        K.text(lay, 'KOHLE', (c0 + c1) // 2, cy0 - 22, 'W', 2.6, center=True, crisp=False, flat=False)
        self.info['chute'] = (c0, cy0, c1, FL)

    def wall_clock(self, cx, cy):
        lay = self.lay
        hh, mm = self.cfg.get('clock', (0, 40))
        lay.rect(cx - 1, cy - 12, 3, 4, 'S', 2.2, hgt=0.8)
        lay.put(K.disc(17), cx - 8, cy - 8, 'I', 1.4, hgt=0.9)
        lay.put(K.disc(15), cx - 7, cy - 7, 'P', 5.6, hgt=1.0)
        for k in range(12):
            a = k / 12 * 2 * math.pi
            lay.px(cx + round(math.sin(a) * 6), cy - round(math.cos(a) * 6), 'I', 0.6 if k % 3 else 0.2, crisp=True)
        am = mm / 60 * 2 * math.pi
        ah = ((hh % 12) + mm / 60) / 12 * 2 * math.pi
        lay.line(cx, cy, cx + round(math.sin(am) * 5), cy - round(math.cos(am) * 5), 'I', 0.2, crisp=True)
        lay.line(cx, cy, cx + round(math.sin(ah) * 3), cy - round(math.cos(ah) * 3), 'I', 0.2, crisp=True)
        lay.px(cx, cy, 'R', 3.0)

    def fire_bell(self):
        lay = self.lay
        bx, by = L.BELL
        K.bevel(lay, bx - 4, by + 10, 9, 6, 'S', 2.2, hi=3.2, lo=1.0, hgt=0.7)      # mechanism box
        for i in range(9):                                                             # the bell dome
            half = int(round(5.5 * math.sqrt(max(0.0, 1 - ((8 - i) / 9.0) ** 2))))
            lay.rect(bx - half, by + i, 2 * half + 1, 1, 'R', 2.6 + (i < 3) * 0.8, hgt=0.9 + i * 0.02)
            lay.px(bx - half + 1, by + i, 'R', 3.8, hgt=1.0)
        lay.rect(bx - 6, by + 8, 13, 1, 'R', 1.4, hgt=0.8)
        lay.px(bx, by + 4, 'R', 4.4)
        lay.rect(bx + 5, by + 11, 3, 2, 'S', 3.2, hgt=0.9)                            # striker (at rest)
        lay.rect(bx - 12, by + 19, 25, 7, 'R', 2.2, hgt=0.6)                          # label plate
        K.text(lay, 'FEUER', bx, by + 20, 'P', 5.8, center=True)
        lay.rect(bx + 10, by + 13, 1, 40, 'S', 1.6, hgt=0.4)                           # cable down
        self.info['bell'] = (bx, by)

    def fire_case(self):
        lay = self.lay
        c0, c1 = L.FIRE_CASE
        y0, y1 = L.CASE_Y
        w, h = c1 - c0, y1 - y0
        # trilingual instruction plate above (pictogram + pseudo text: the words live in the inspect view)
        lay.rect(c0 - 2, y0 - 13, w + 4, 11, 'P', 5.4, hgt=0.6)
        lay.rect(c0 - 2, y0 - 13, w + 4, 1, 'R', 2.4)
        lay.rect(c0 - 2, y0 - 3, w + 4, 1, 'R', 2.4)
        K.text(lay, 'FEUER', c0 + w // 2, y0 - 11, 'R', 2.8, center=True)
        K.pseudo_text(lay, c0 + 1, y0 - 5, w - 2, 1, 'I', 1.6, seed=7)
        # cabinet
        lay.rect(c0 + 1, y1, w, 1, 'W', 1.6)
        lay.rect(c1, y0 + 1, 1, h, 'W', 1.6)
        K.bevel(lay, c0, y0, w, h, 'R', 2.6, hi=3.6, lo=1.2, hgt=0.9)
        gx0, gy0, gw, gh = c0 + 3, y0 + 3, w - 6, h - 12
        broken = bool(self.cfg.get('case_broken'))
        lay.rect(gx0, gy0, gw, gh, 'N', 1.4, hgt=0.5)                                  # interior
        if not broken:
            # hose coiled on the saddle, brass nozzle, the axe on clips
            for k in range(5):
                lay.rect(gx0 + 2, gy0 + 4 + k * 3, gw - 4, 2, 'P', 3.2 + (k % 2) * 0.5, hgt=0.7)
                lay.px(gx0 + 2, gy0 + 4 + k * 3, 'P', 2.0)
            lay.rect(gx0 + gw // 2 - 2, gy0 + 1, 4, 3, 'S', 2.6, hgt=0.8)
            lay.rect(gx0 + gw - 4, gy0 + 20, 2, 10, 'B', 4.0, hgt=0.8)
            lay.rect(gx0 + 1, gy0 + 22, 2, 9, 'D', 3.6, hgt=0.6)
            lay.rect(gx0, gy0 + 22, 4, 3, 'S', 3.4, hgt=0.7)
            # glass with glints
            for k in range(gh):
                if (k + 2) % 9 < 2:
                    lay.line(gx0 + 1, gy0 + k, gx0 + 5, gy0 + k - 4, 'C', 5.2, unlit=True)
            lay.rect(gx0, gy0, gw, 1, 'C', 3.2)
        else:
            # glass smashed, the hose dragged out and cut (hanging), the axe gone
            rng = np.random.default_rng(560)
            for k in range(4):
                lay.rect(gx0 + 2, gy0 + 4 + k * 3, gw - 6, 2, 'P', 2.8 + (k % 2) * 0.4, hgt=0.7)
            for yy in range(gy0, gy0 + gh):
                for xx in (gx0, gx0 + gw - 1):
                    if rng.random() < 0.5:
                        lay.px(xx, yy, 'C', 5.6, unlit=True)
            for (sx, sy) in ((gx0 + 1, gy0 + 1), (gx0 + gw - 3, gy0 + 2), (gx0 + 1, gy0 + gh - 3)):
                lay.line(sx, sy, sx + 2, sy + 2, 'C', 6.2, unlit=True)
            hx = gx0 + gw // 2
            pts = [(hx, gy0 + 16), (hx + 2, y1 + 2), (hx + 1, y1 + 10), (hx + 4, y1 + 18)]
            for a, b in zip(pts[:-1], pts[1:]):
                lay.line(a[0], a[1], b[0], b[1], 'P', 3.0, hgt=0.9)
                lay.line(a[0] + 1, a[1], b[0] + 1, b[1], 'P', 2.0, hgt=0.8)
            lay.rect(hx + 3, y1 + 18, 3, 2, 'P', 4.6, hgt=0.9)                       # the clean cut
            lay.px(hx + 4, y1 + 18, 'N', 0.6)
            for k in range(6):                                                       # shards on the floor
                lay.px(c0 + rng.integers(0, w), FL + 2 + rng.integers(0, 5), 'C', 6.0, unlit=True)
        lay.rect(c0 + 2, y1 - 8, w - 4, 6, 'R', 2.0, hgt=0.8)                        # base panel
        lay.rect(c0 + w // 2 - 3, y1 - 6, 6, 2, 'P', 5.0)
        # the little hammer on its chain
        lay.rect(c1 + 3, y0 + 8, 1, 10, 'S', 2.6)
        lay.rect(c1 + 2, y0 + 18, 3, 2, 'R', 3.0, hgt=0.8)
        self.info['case'] = (c0, y0, c1, y1)

    def booth(self):
        """The glazed porter's booth (Pforte): key board (one empty hook: Magazin), the framed 1909 Kurhaus plan in
        the middle (Konrad reads it in C), the Bakelite radio with a tobacco tin on the right shelf, an empty coat
        hook; on the counter the thermos with a cup and the relief's note (left) and the open night book."""
        lay = self.lay
        b0, b1 = L.BOOTH
        top = 198
        w = b1 - b0
        # interior back wall (seen through the glass)
        lay.rect(b0 + 2, top + 8, w - 4, 254 - top - 8, 'G', 2.4, hgt=-0.2)
        lay.rect(b0 + 2, top + 8, w - 4, 2, 'G', 1.2, hgt=-0.2)
        # key board: labelled hooks with keys and tags -- the "Magazin" hook is empty
        kx, ky = b0 + 5, top + 13
        K.bevel(lay, kx, ky, 22, 26, 'D', 3.0, hi=4.0, lo=1.6, hgt=0.2)
        rng = np.random.default_rng(612)
        for r in range(4):
            for c in range(4):
                hx_, hy_ = kx + 3 + c * 5, ky + 3 + r * 6
                lay.px(hx_, hy_, 'B', 4.0)
                lay.px(hx_ - 1, hy_ - 1, 'P', 4.4)                                # tiny label above
                if (r, c) != (3, 3):
                    lay.rect(hx_, hy_ + 1, 1, 2, 'S', 4.0)
                    lay.rect(hx_ - 1, hy_ + 3, 3, 1, 'P' if rng.random() < 0.6 else 'R',
                             4.2 if rng.random() < 0.6 else 2.6)
        lay.rect(kx + 17, ky + 21, 4, 1, 'R', 3.0)                                # the empty hook's red label
        # the framed Kurhaus plan, 1909 (yellowed, an elevation + plan), in the middle
        px0, py0 = b0 + 34, top + 12
        K.frame(lay, px0, py0, 28, 20, 'D', 2.0, hi=3.0, lo=0.8, shadow=('G', 1.2))
        lay.rect(px0, py0, 28, 20, 'P', 4.2, hgt=0.3)
        lay.rect(px0 + 3, py0 + 4, 22, 1, 'D', 2.4); lay.rect(px0 + 3, py0 + 4, 1, 10, 'D', 2.4)
        lay.rect(px0 + 24, py0 + 4, 1, 10, 'D', 2.4); lay.rect(px0 + 3, py0 + 13, 22, 1, 'D', 2.4)
        lay.rect(px0 + 10, py0 + 4, 1, 10, 'D', 3.0); lay.rect(px0 + 16, py0 + 8, 9, 1, 'D', 3.0)
        lay.rect(px0 + 5, py0 + 10, 4, 3, 'D', 3.4)                                # the coal cellar, hatched
        lay.line(px0 + 5, py0 + 12, px0 + 8, py0 + 10, 'P', 4.6)
        lay.line(px0 + 7, py0 + 10, px0 + 3, py0 + 6, 'R', 2.6)                    # the chute, inked red
        K.text(lay, '1909', px0 + 14, py0 + 15, 'D', 2.2, center=True)
        # shelf (right) with the Bakelite radio (dial glows) and the tobacco tin
        sy = top + 34
        lay.rect(b0 + 64, sy + 8, 24, 2, 'D', 3.0, hgt=0.4)
        rx, ry = b0 + 66, sy
        lay.put(K.soft_box(14, 8, 2), rx, ry, 'D', 2.2, hgt=0.6)
        lay.rect(rx + 1, ry + 1, 6, 6, 'P', 2.6, hgt=0.5)                          # speaker cloth
        for yy in range(ry + 1, ry + 7, 2):
            lay.rect(rx + 1, yy, 6, 1, 'P', 1.8)
        lay.rect(rx + 8, ry + 2, 5, 3, 'B', 5.0, emis=True)                        # tuning dial
        lay.px(rx + 10, ry + 2, 'R', 3.6, emis=True)
        lay.rect(rx + 9, ry + 6, 2, 1, 'D', 3.6)
        lay.rect(rx + 15, ry + 4, 5, 4, 'R', 2.2, hgt=0.6)                          # tobacco tin
        lay.rect(rx + 15, ry + 4, 5, 1, 'B', 3.4)
        lay.rect(rx + 16, ry + 7, 4, 1, 'P', 4.6)                                   # the folded note under it
        # empty coat hook + the lamp
        lay.rect(b1 - 8, top + 12, 3, 1, 'B', 3.6, hgt=0.6)
        lay.px(b1 - 6, top + 13, 'B', 3.0)
        lay.rect(b0 + 62, top + 8, 1, 4, 'I', 1.4)
        for i in range(4):
            lay.rect(b0 + 59 - i, top + 12 + i, 7 + 2 * i, 1, 'G', 3.0 - i * 0.3, hgt=0.8)
        lay.rect(b0 + 61, top + 16, 3, 1, 'B', 6.0, emis=True)
        # glazed front: frame, mullions, sliding hatch, glass glints (painted ON the glass)
        lay.rect(b0, top, w, 8, 'D', 2.6, hgt=0.8)                        # cornice
        lay.rect(b0 - 1, top, w + 2, 2, 'D', 3.6, hgt=0.9)
        lay.rect(b0, top + 7, w, 1, 'D', 1.2)
        K.text(lay, 'PFORTE', b0 + w // 2, top + 2, 'B', 4.6, center=True)
        for mx in (b0, b0 + 30, b0 + 62, b1 - 3):
            lay.rect(mx, top + 8, 3, 46, 'D', 3.0, hgt=0.8)
            lay.rect(mx, top + 8, 1, 46, 'D', 4.0, hgt=0.85)
        for yy in range(top + 9, 252):
            for xx in range(b0 + 3, b1 - 3):
                if (xx - yy) % 23 in (0, 1) and lay.rid[yy, xx] >= 0 and (xx - b0) % 31 > 4:
                    lay.tone[yy, xx] += 1.2
        lay.rect(b0 + 31, 236, 30, 1, 'D', 3.4, hgt=0.7)                  # hatch rail
        # counter ledge: thermos + cup + note (left), the night book (open), pen on its chain, the telephone
        lay.rect(b0 - 2, 252, w + 4, 4, 'D', 3.6, hgt=0.9)
        lay.rect(b0 - 2, 252, w + 4, 1, 'D', 5.0, hgt=1.0)
        lay.rect(b0 - 2, 255, w + 4, 1, 'D', 1.4)
        tx = b0 - 1
        lay.rect(tx - 1, 251, 5, 1, 'P', 5.0, hgt=1.0)                     # the note under the thermos
        lay.rect(tx, 242, 3, 9, 'S', 3.0, hgt=1.2)                         # thermos (steel, cup-lid)
        lay.rect(tx, 242, 1, 9, 'S', 4.6, hgt=1.25)
        lay.rect(tx - 1, 240, 5, 2, 'R', 2.4, hgt=1.25)
        lay.rect(tx + 4, 248, 3, 3, 'P', 4.4, hgt=1.2)                     # cup
        lay.px(tx + 7, 249, 'P', 3.6)
        nb = b0 + 12
        lay.rect(nb, 249, 22, 3, 'P', 5.4, hgt=1.0)                        # night book pages
        lay.rect(nb + 10, 249, 2, 3, 'P', 3.6, hgt=0.9)                    # gutter
        lay.rect(nb - 1, 251, 24, 1, 'D', 1.6)                             # cover edges
        K.pseudo_text(lay, nb + 1, 249, 8, 2, 'I', 1.6, seed=23, gap=1)
        K.pseudo_text(lay, nb + 13, 249, 8, 2, 'I', 1.6, seed=24, gap=1)
        lay.px(nb + 18, 250, 'R', 3.0)                                     # the other pen's entry
        lay.rect(nb + 24, 250, 6, 1, 'S', 3.0)                             # pen on its chain
        lay.rect(b0 + 46, 246, 9, 6, 'I', 1.2, hgt=0.9)                     # telephone
        lay.rect(b0 + 45, 245, 11, 2, 'I', 1.8, hgt=1.0)
        lay.px(b0 + 50, 248, 'S', 3.6)
        # lower panels + door at the right
        for (px_, pw) in ((b0, 30), (b0 + 30, 32), (b0 + 62, w - 62)):
            K.bevel(lay, px_, 256, pw, FL - 256, 'D', 2.6, hi=3.6, lo=1.0, hgt=0.7)
            K.recess(lay, px_ + 4, 260, pw - 8, FL - 266, 'D', 2.2, shadow=1.2, light=3.2, hgt=0.5)
        lay.rect(b1 - 6, 262, 2, 6, 'B', 4.2, hgt=1.0)                    # door knob
        self.light('booth_lamp', (b0 + 62, top + 20), 'warm', 1.9, 140, 16, falloff=1.15,
                   pool=0.3, pool_dx=-10, pool_depth=44, pool_w=28, pool_spread=0.8)
        self.light('radio_dial', (rx + 10, ry + 3), 'warm', 0.25, 24, 4)
        self.info['booth'] = (b0, top, b1, FL)

    def desk(self):
        lay = self.lay
        d0, d1 = L.DESK
        if self.cfg.get('desk_pushed'):
            d0 += L.DESK_PUSH
            d1 += L.DESK_PUSH
            # scrape marks on the floor where it was dragged
            for k in range(3):
                lay.hline(L.DESK[0] + 2, FL + 3 + k * 3, L.DESK_PUSH + 6, 'P', 2.4 - k * 0.3)
        w = d1 - d0
        top_y = 256
        # body: panelled oak, plinth, slanted writing top (front edge lower)
        K.bevel(lay, d0, top_y + 4, w, FL - top_y - 4, 'D', 2.4, hi=3.4, lo=1.0, hgt=0.8)
        for k, px_ in enumerate(range(d0 + 3, d1 - 10, (w - 6) // 3)):
            K.recess(lay, px_, top_y + 9, (w - 6) // 3 - 3, 16, 'D', 2.0, shadow=1.0, light=3.0, hgt=0.6)
        lay.rect(d0 - 1, FL - 3, w + 2, 3, 'D', 1.4, hgt=0.7)
        for k in range(5):                                                 # slope (seen from above)
            lay.rect(d0 - 2, top_y - k, w + 4, 1, 'D', 3.6 + k * 0.2, hgt=0.9 + k * 0.02)
        lay.rect(d0 - 2, top_y + 1, w + 4, 2, 'D', 1.8, hgt=0.8)
        lay.rect(d0 - 2, top_y - 5, w + 4, 1, 'D', 4.8, hgt=1.0)
        grain_rng = np.random.default_rng(d0)
        for k in range(10):
            lay.hline(d0 + int(grain_rng.integers(0, w - 6)), top_y + 6 + int(grain_rng.integers(0, 20)), 5, 'D', 3.0)
        # the intake book (open, ledger lines) + blotter, stamp rack, inkpad
        bx = d0 + 10
        lay.rect(bx, top_y - 6, 30, 4, 'P', 5.4, hgt=1.0)
        lay.rect(bx + 14, top_y - 6, 2, 4, 'P', 3.6)
        for k in range(3):
            lay.rect(bx + 1, top_y - 5 + k, 12, 1, 'P', 4.4 if k % 2 else 5.0)
            lay.rect(bx + 17, top_y - 5 + k, 12, 1, 'P', 4.4 if k % 2 else 5.0)
        lay.rect(bx + 3, top_y - 5, 1, 3, 'R', 2.6)
        lay.rect(bx + 19, top_y - 5, 1, 3, 'R', 2.6)
        lay.rect(bx - 1, top_y - 2, 32, 1, 'G', 1.6)
        lay.rect(d0 + 2, top_y - 9, 7, 3, 'D', 2.0, hgt=1.0)               # stamp rack
        for k in range(3):
            lay.rect(d0 + 3 + k * 2, top_y - 12, 1, 3, 'I', 1.6, hgt=1.0)
            lay.px(d0 + 3 + k * 2, top_y - 13, 'D', 3.6)
        lay.rect(d0 + 44, top_y - 7, 6, 2, 'S', 1.6, hgt=0.9)               # ink pad
        cx_ = d1 - 6
        lay.rect(cx_, top_y - 9, 8, 6, 'D', 3.2, hgt=1.1)                  # the day's card box
        lay.rect(cx_, top_y - 9, 8, 1, 'D', 4.4, hgt=1.15)
        for k in range(6):
            lay.px(cx_ + 1 + k, top_y - 10, 'P', 4.6 + (k % 2) * 0.6, hgt=1.2)
        # desk lamp (brass, cream shade)
        lx = d1 - 12
        lay.rect(lx - 3, top_y - 7, 7, 2, 'B', 3.0, hgt=1.0)
        lay.line(lx, top_y - 7, lx + 2, top_y - 18, 'B', 3.6)
        lay.line(lx + 2, top_y - 18, lx - 2, top_y - 22, 'B', 3.4)
        for i in range(4):
            lay.rect(lx - 6 - i, top_y - 24 + i, 6 + 2 * i, 1, 'P', 4.2 - i * 0.2, hgt=1.0)
        lay.rect(lx - 6, top_y - 20, 5, 1, 'B', 6.0, emis=True)
        self.light('desk_lamp', (lx - 4, top_y - 17), 'warm', 1.45, 84, 10, falloff=1.25,
                   pool=0.4, pool_depth=30, pool_w=10, pool_spread=0.6)
        self.info['desk'] = (d0, top_y - 24, d1, FL)

    # ================================================================== partitions
    def partition(self, x0, x1, arch_y=64):
        """End of a cross wall: a brick pier on the back plane, stone impost, the transverse brick arch
        (Gurtbogen) running toward the viewer through the vault zone."""
        lay = self.lay
        w = x1 - x0
        K.bricks(lay, x0, 0, w, FL, 'K', 2.6, seed=x0, course=4, length=8, joint=-0.9, var=0.3)
        lay.rect(x0, 0, 1, FL, 'K', 1.0, hgt=0.2)
        lay.rect(x0 + 1, 0, 2, FL, 'K', 3.6, hgt=0.5)                       # lit arris
        lay.rect(x1 - 3, 0, 3, FL, 'K', 1.2, hgt=0.3)                       # shadow side
        for yy in (arch_y - 6, L.DADO_Y - 4):                               # stone imposts
            lay.rect(x0 - 2, yy, w + 4, 4, 'P', 2.8, hgt=0.9)
            lay.rect(x0 - 2, yy, w + 4, 1, 'P', 3.8, hgt=1.0)
            lay.rect(x0 - 2, yy + 3, w + 4, 1, 'P', 1.2, hgt=0.4)
        vp = (x0 + x1) / 2.0
        sp = L.VAULT_SPRING
        for yy in range(0, arch_y - 6):
            f = (L.HORIZON - yy) / (L.HORIZON - sp) if yy < sp else 1.0
            a_ = int(round(vp + (x0 - 2 - vp) * f))
            b_ = int(round(vp + (x1 + 2 - vp) * f))
            lay.rect(a_, yy, b_ - a_, 1, 'K', 2.2 + ((yy // 3) % 2) * 0.5, hgt=0.7)
            lay.px(a_, yy, 'K', 3.4, hgt=0.8)
            lay.px(b_ - 1, yy, 'K', 1.0, hgt=0.5)
        lay.rect(x0, FL, w, 4, 'S', 2.0)

    # ================================================================== Karteisaal
    def karteisaal(self):
        lay = self.lay
        for cx in (740, 900, 1060, 1220):
            self.high_window(cx)
        self.sign_plate(830, 120, ['KARTEI', 'КАРТОТЕКА · FICHIER'])
        self.smoke_sign(986, 206)
        self.buckets()
        for i, (r0, r1) in enumerate(L.ROWS):
            self.aisle(r1, (L.ROWS[i + 1][0] if i + 1 < len(L.ROWS) else L.ROWS[i][1] + 26), lit=(i == 2))
        self.aisle(L.BUCKETS[1] + 4, L.ROWS[0][0], lit=False)
        for i, (r0, r1) in enumerate(L.ROWS):
            self.row_end(r0, r1, ['А-Б', 'В-К', 'Л-Я'][i], ['A-B', 'C-K', 'L-Z'][i])
        self.row_ladder()
        self.bank()
        self.table()
        self.stamp_board(1040, 198)
        self.rohrpost(714)
        self.green_lamp()

    def buckets(self):
        lay = self.lay
        b0 = L.BUCKETS[0]
        b1 = b0 + 18
        lay.rect(b0, 190, b1 - b0, 3, 'R', 2.0, hgt=0.7)
        lay.rect(b0, 190, b1 - b0, 1, 'R', 3.0, hgt=0.8)
        K.text(lay, 'FEUER', (b0 + b1) // 2, 183, 'R', 2.8, center=True)
        for k in range(3):
            bx = b0 + 1 + k * 6
            lay.px(bx + 2, 193, 'S', 3.0)
            for i in range(12):
                hw = 2 + (i * 3) // 12
                lay.rect(bx + 2 - hw // 2 - (i > 6), 195 + i, hw + 1 + (i > 6), 1, 'R', 2.4 + (i < 3) * 0.6, hgt=0.8)
            lay.px(bx + 1, 198, 'R', 3.6)
        # sand box + shovel
        K.bevel(lay, b0, 262, b1 - b0 + 4, FL - 262, 'R', 2.0, hi=3.0, lo=1.0, hgt=0.7)
        K.text(lay, 'SAND', (b0 + b1 + 4) // 2, 266, 'P', 4.6, center=True)
        lay.rect(b0 + 2, 259, b1 - b0, 3, 'P', 3.0, hgt=0.6)
        lay.line(b1 + 1, 260, b1 + 4, 236, 'D', 3.0)
        lay.rect(b1 - 1, 256, 5, 5, 'S', 2.8, hgt=0.8)

    def rohrpost(self, x):
        """Pneumatic-tube station of the registry (exp_tube): two brass tubes down from the vault into a glazed
        receiver; an empty capsule lies in it."""
        lay = self.lay
        for tx in (x + 10, x + 15):
            _cyl_rect(lay, tx, 36, 3, 186, 'B', 2.6, hgt=0.9, axis='v')
            for yy in range(60, 220, 40):
                lay.rect(tx - 1, yy, 5, 2, 'B', 1.8, hgt=1.0)
        K.bevel(lay, x, 222, 22, 26, 'B', 2.4, hi=3.6, lo=1.0, hgt=1.0)
        lay.rect(x + 3, 226, 16, 12, 'C', 2.2, hgt=0.6)                          # glass
        lay.line(x + 4, 236, x + 9, 227, 'C', 4.4, unlit=True)
        lay.rect(x + 5, 232, 12, 4, 'P', 3.6, hgt=0.8)                            # the capsule
        lay.rect(x + 5, 232, 2, 4, 'B', 3.4, hgt=0.85)
        lay.rect(x + 15, 232, 2, 4, 'B', 3.4, hgt=0.85)
        lay.rect(x + 6, 241, 10, 3, 'B', 3.0, hgt=1.0)                             # brass plate
        lay.rect(x + 7, 242, 8, 1, 'I', 1.4)
        self.info['rohrpost'] = (x, 222, x + 22, 248)

    def row_ladder(self):
        """The rolling ladder on its brass rail along the row ends (exp_ladder; the rail is newer than the
        cabinets: conversion 1963)."""
        lay = self.lay
        r0, r1 = L.ROWS[0][0], L.ROWS[-1][1]
        lay.rect(r0 - 2, 150, r1 - r0 + 4, 2, 'B', 3.4, hgt=1.2)
        lay.rect(r0 - 2, 150, r1 - r0 + 4, 1, 'B', 4.8, hgt=1.2)
        for x in range(r0, r1, 30):
            lay.rect(x, 149, 2, 4, 'B', 2.4, hgt=1.2)
        l0 = 816
        for k in range(FL - 152):
            yy = 152 + k
            off = int(k * 0.11)
            for (lx, t) in ((l0 + off, 3.8), (l0 + 15 + off, 3.4)):
                lay.px(lx, yy, 'D', t, hgt=1.4)
                lay.px(lx + 1, yy, 'D', t - 1.2, hgt=1.4)
            if k % 12 == 6:
                lay.rect(l0 + off + 1, yy, 14, 1, 'D', 4.2, hgt=1.4)
                lay.rect(l0 + off + 1, yy + 1, 14, 1, 'D', 1.6, hgt=1.3)
        lay.rect(l0 - 1, 148, 3, 3, 'B', 4.4, hgt=1.4)
        lay.rect(l0 + 14, 148, 3, 3, 'B', 4.4, hgt=1.4)
        for (wx, yy) in ((l0 + 29, FL - 3), (l0 + 15 + 29, FL - 3)):
            lay.rect(wx - 2, yy, 3, 3, 'B', 3.0, hgt=1.3)

    def stamp_board(self, x, y):
        """The registry's stamp board (exp_stamps): rubber stamps on a rack, the counter-seal with the city's
        bridge, seal pliers on numbered hooks -- hook 7 empty."""
        lay = self.lay
        K.bevel(lay, x, y, 26, 38, 'D', 2.6, hi=3.6, lo=1.0, hgt=0.6)
        lay.rect(x + 2, y + 3, 22, 2, 'D', 1.6, hgt=0.7)
        for k in range(5):                                                         # stamps on the rack
            sx = x + 3 + k * 4
            lay.rect(sx, y + 6, 3, 2, 'D', 4.0, hgt=0.9)
            lay.rect(sx + 1, y + 8, 1, 3, 'D', 3.0, hgt=0.9)
            lay.rect(sx, y + 11, 3, 2, 'I', 1.4 if k != 4 else 1.0, hgt=0.9)
        br, wa = K.hk.commission_arms(6, 5)
        lay.put(br, x + 18, y + 6, 'B', 3.4, hgt=1.0)                              # the counter-seal (bridge)
        lay.rect(x + 2, y + 17, 22, 1, 'B', 3.0, hgt=0.8)                          # hook rail
        for k in range(8):
            hx = x + 3 + k * 3
            lay.px(hx, y + 18, 'S', 3.4)
            lay.px(hx, y + 16, 'P', 4.6 if k != 6 else 3.0)                        # numbered tags
            if k != 6:                                                              # hook 7 is empty
                lay.rect(hx, y + 19, 1, 5, 'S', 3.0, hgt=0.9)
                lay.px(hx - 1, y + 24, 'S', 2.4)
                lay.px(hx + 1, y + 24, 'S', 2.4)
        K.pseudo_text(lay, x + 3, y + 30, 20, 2, 'P', 3.4, seed=1040)
    def aisle(self, x0, x1, lit=False):
        """A dark aisle between two rows of cabinets receding into the depth: the drawer fronts of both rows
        converge toward the far end, the boards rise toward it, a sliver of window light at the far wall."""
        lay = self.lay
        w = x1 - x0
        if w < 6:
            return
        top = 146
        fx0, fx1 = x0 + w * 0.34, x1 - w * 0.34
        fy0, fy1 = 200, 258
        for xx in range(x0, x1):
            if xx < fx0:
                d = (xx + 0.5 - x0) / (fx0 - x0)
                side = 'L'
            elif xx >= fx1:
                d = (x1 - xx - 0.5) / (x1 - fx1)
                side = 'R'
            else:
                d = 1.0
                side = 'F'
            yt = top + (fy0 - top) * d
            yb = FL + (fy1 - FL) * d
            for yy in range(top - 6, FL):
                if yy < yt:
                    lay.px(xx, yy, 'N', 0.5, hgt=-0.8)
                elif yy <= yb:
                    if side == 'F':
                        lay.px(xx, yy, 'W', 2.2 - (yy - fy0) * 0.01, hgt=-1.0)
                    else:
                        rel = (yy - yt) / max(1.0, yb - yt)
                        row = int(rel * 12)
                        edge = abs(rel * 12 - row - 0.5) > 0.38
                        tone = 1.5 - d * 0.7 + (0.5 if (side == 'L') else 0.1) - (0.6 if edge else 0.0)
                        lay.px(xx, yy, 'D', tone, hgt=-0.5)
                        k = int(d * 9)
                        if not edge and abs(d * 9 - k - 0.5) < 0.22 and d < 0.92:
                            lay.px(xx, yy, 'B', 2.0 - d * 0.8, hgt=-0.4)
                else:
                    t = 1.6 - (FL - yy) / max(1.0, FL - yb) * 0.6
                    lay.px(xx, yy, 'D', t - (0.7 if (yy - int(yb)) % 3 == 0 else 0.0), hgt=-0.6)
        # a high window's light on the far wall
        mx = int((fx0 + fx1) / 2)
        lay.rect(mx - 2, fy0 + 2, 4, 8, 'C', 3.6, hgt=-1.0)
        lay.rect(mx - 1, fy0 + 10, 2, 30, 'C', 2.6, hgt=-1.0)
        if lit:
            self.info['aisle_lit'] = (x0, top, x1, FL)

    def row_end(self, x0, x1, ru, la):
        lay = self.lay
        w = x1 - x0
        top = 146
        K.grain(lay, x0, top, w, FL - top, 'D', 2.6, seed=x0, amp=0.4)
        lay.rect(x0, top, w, 1, 'D', 4.4, hgt=0.9)
        lay.rect(x0 - 1, top - 4, w + 2, 4, 'D', 3.2, hgt=1.0)            # cornice
        lay.rect(x0 - 1, top - 4, w + 2, 1, 'D', 4.6, hgt=1.0)
        lay.rect(x0, top + 1, 2, FL - top, 'D', 3.6, hgt=0.9)
        lay.rect(x1 - 2, top + 1, 2, FL - top, 'D', 1.6, hgt=0.7)
        K.recess(lay, x0 + 5, top + 10, w - 10, 70, 'D', 2.2, shadow=1.2, light=3.4, hgt=0.6)
        K.recess(lay, x0 + 5, top + 88, w - 10, 44, 'D', 2.2, shadow=1.2, light=3.4, hgt=0.6)
        # brass label holder with the card
        lx = x0 + w // 2 - 9
        lay.rect(lx, top + 18, 18, 14, 'B', 3.0, hgt=1.0)
        lay.rect(lx, top + 18, 18, 1, 'B', 4.6, hgt=1.0)
        lay.rect(lx + 1, top + 19, 16, 12, 'P', 5.4, hgt=1.0)
        K.text(lay, ru, lx + 9, top + 20, 'I', 0.8, center=True)
        K.text(lay, la, lx + 9, top + 26, 'I', 0.8, center=True)
        lay.rect(x0, FL - 6, w, 6, 'D', 1.6, hgt=0.6)                     # kick plate
        # card boxes stacked on top
        rng = np.random.default_rng(x0)
        bx = x0
        while bx < x1 - 4:
            bw = int(rng.integers(7, 12))
            bh = int(rng.integers(5, 9))
            lay.rect(bx, top - 4 - bh, min(bw, x1 - bx), bh, 'P', 2.8 + rng.random(), hgt=0.9)
            lay.rect(bx + 2, top - 2 - bh, 3, 1, 'P', 4.6)
            bx += bw + 1

    def bank(self):
        lay = self.lay
        b0, b1 = L.BANK
        top = 136
        lay.rect(b0 - 2, top - 5, b1 - b0 + 4, 5, 'D', 3.2, hgt=1.0)
        lay.rect(b0 - 2, top - 5, b1 - b0 + 4, 1, 'D', 4.6, hgt=1.0)
        lay.rect(b0, top, b1 - b0, FL - top, 'D', 1.6, hgt=0.6)
        # modules of small card drawers (upper) and the deeper drawers at waist height (lower)
        dw, dh = 13, 7
        for mx in range(b0 + 1, b1 - dw, 42):
            lay.rect(mx - 1, top, 1, FL - top, 'D', 1.0, hgt=0.4)
            for row in range(0, 14):
                yy = top + 3 + row * (dh + 1)
                if yy + dh > 240:
                    break
                for col in range(3):
                    xx = mx + 1 + col * (dw + 1)
                    if xx + dw > b1:
                        continue
                    self._card_drawer(xx, yy, dw, dh, seed=xx * 7 + row)
        # lower drawers (deeper, two rows) -- one of them is C-17
        for row in range(2):
            yy = 242 + row * 14
            for xx in range(b0 + 2, b1 - 26, 28):
                if self.cfg.get('drawer_open', True) and row == 0 and xx <= L.DRAWER[0] < xx + 28:
                    self._open_drawer(xx, yy)
                else:
                    self._big_drawer(xx, yy, 26, 12, label=None)
        lay.rect(b0, FL - 4, b1 - b0, 4, 'D', 1.2, hgt=0.5)
        # brass rail of the bank (no ladder here: it stands at the rows)
        lay.rect(b0, top + 6, b1 - b0, 2, 'B', 3.4, hgt=1.2)
        lay.rect(b0, top + 6, b1 - b0, 1, 'B', 4.8, hgt=1.2)
        self.info['bank'] = (b0, top, b1, FL)

    def _card_drawer(self, x, y, w, h, seed=0):
        lay = self.lay
        lay.rect(x, y, w, h, 'D', 2.3 + (seed % 5) * 0.08, hgt=0.7)
        lay.rect(x, y, w, 1, 'D', 3.2, hgt=0.8)
        lay.rect(x, y + h - 1, w, 1, 'D', 1.2, hgt=0.5)
        lay.rect(x + 3, y + 1, w - 6, 3, 'B', 1.9, hgt=0.9)              # label holder
        lay.rect(x + 4, y + 2, w - 8, 1, 'P', 3.0 + (seed % 3) * 0.3, hgt=0.9)
        lay.rect(x + w // 2 - 1, y + 5, 3, 1, 'B', 2.6, hgt=1.0)          # pull

    def _big_drawer(self, x, y, w, h, label=None):
        lay = self.lay
        lay.rect(x, y, w, h, 'D', 2.4, hgt=0.7)
        lay.rect(x, y, w, 1, 'D', 3.6, hgt=0.8)
        lay.rect(x, y + h - 1, w, 1, 'D', 1.2, hgt=0.5)
        lay.rect(x + w // 2 - 5, y + 2, 10, 4, 'B', 3.0, hgt=0.9)
        lay.rect(x + w // 2 - 4, y + 3, 8, 2, 'P', 4.6, hgt=0.9)
        lay.rect(x + w // 2 - 3, y + 8, 6, 2, 'B', 3.8, hgt=1.0)
        if label:
            K.text(lay, label, x + w // 2, y + 3, 'I', 0.6, center=True)

    def _open_drawer(self, x, y):
        """Drawer C-17, half pulled out toward the viewer: we see the cards inside from above."""
        lay = self.lay
        w = 26
        lay.rect(x, y, w, 12, 'N', 0.5, hgt=-0.4)                          # the dark slot it came out of
        dy = y + 4                                                         # pulled out: lower + nearer
        lay.rect(x - 1, dy, w + 2, 4, 'D', 3.0, hgt=0.9)                   # drawer sides / top edges
        for k in range(w):                                                 # card tops (cream, ragged)
            lay.px(x + k, dy + 1, 'P', 4.6 + ((k * 7) % 3) * 0.35, hgt=1.0)
            if k % 5 == 2:
                lay.px(x + k, dy, 'P', 5.4, hgt=1.1)
        lay.rect(x + 9, dy - 1, 3, 2, 'R', 2.8, hgt=1.1)                   # a red guide card sticks up
        lay.rect(x - 1, dy + 4, w + 2, 10, 'D', 2.8, hgt=0.9)              # front
        lay.rect(x - 1, dy + 4, w + 2, 1, 'D', 4.0, hgt=1.0)
        lay.rect(x - 1, dy + 13, w + 2, 1, 'D', 1.2, hgt=0.6)
        lay.rect(x + w // 2 - 6, dy + 6, 12, 5, 'B', 3.2, hgt=1.0)
        lay.rect(x + w // 2 - 5, dy + 7, 10, 3, 'P', 5.4, hgt=1.0)
        K.text(lay, 'C-17', x + w // 2, dy + 6, 'R', 2.4, center=True)
        self.info['drawer'] = (x - 1, y, x + w + 1, dy + 14)
        # the chair in front with Elena's wine-red scarf over the backrest
        cx = L.DRAWER[0] + 3
        self.chair(cx, facing=1)
        if self.cfg.get('scarf', True):
            for k in range(11):
                lay.rect(cx + 15 + (k > 5), 256 + k, 3, 1, 'R', 2.2 + (k % 3 == 0) * 0.8, hgt=1.2)
            lay.rect(cx + 12, 255, 8, 2, 'R', 2.6, hgt=1.25)
            for k in range(3):
                lay.px(cx + 16 + k, 267, 'R', 1.6)
                lay.px(cx + 16 + k, 268 + (k % 2), 'R', 2.4)

    def chair(self, x, facing=1):
        """Bentwood office chair seen from the side (x = left edge, seat at y 270)."""
        lay = self.lay
        sy = 270
        lay.rect(x + 1, sy, 16, 2, 'D', 3.4, hgt=1.1)
        lay.rect(x + 1, sy, 16, 1, 'D', 4.6, hgt=1.2)
        bx = x + 16 if facing > 0 else x + 1
        lay.rect(bx, 252, 2, sy - 252, 'D', 3.0, hgt=1.1)
        lay.rect(bx - 4 * facing if facing > 0 else bx, 252, 6, 2, 'D', 3.8, hgt=1.15)
        for lx in (x + 2, x + 15):
            lay.rect(lx, sy + 2, 2, FL - sy - 2, 'D', 2.6, hgt=1.0)
        lay.rect(x + 3, sy + 9, 13, 1, 'D', 2.2, hgt=1.0)

    def table(self):
        lay = self.lay
        t0, t1 = L.TABLE
        ty = 266
        lay.rect(t0, ty, t1 - t0, 3, 'D', 4.0, hgt=1.2)                       # top (seen slightly above)
        lay.rect(t0, ty, t1 - t0, 1, 'D', 5.2, hgt=1.25)
        lay.rect(t0, ty + 3, t1 - t0, 5, 'D', 2.2, hgt=1.1)                    # apron
        lay.rect(t0, ty + 8, t1 - t0, 1, 'D', 1.2)
        for lx in (t0 + 3, t0 + 64, t1 - 7):
            for yy in range(ty + 9, FL + 2):
                k = (yy - ty) % 8
                lay.rect(lx + (k in (2, 3)) * 0 - (k == 3), yy, 4 + (k == 3) * 2, 1, 'D', 3.0 - (k > 5) * 0.6, hgt=1.1)
        lay.rect(t0 + 6, FL - 8, t1 - t0 - 12, 2, 'D', 2.0, hgt=1.0)          # stretcher
        # papers, card trays, magnifier (always), the file and the halves (story state)
        rng = np.random.default_rng(1012)
        for k in range(7):
            px_ = t0 + 8 + int(rng.integers(0, t1 - t0 - 22))
            lay.rect(px_, ty - 1, int(rng.integers(6, 12)), 1, 'P', 4.8 + rng.random() * 0.8, hgt=1.3)
        for (bx, bw) in ((t0 + 6, 14), (t1 - 22, 16)):                      # card trays
            lay.rect(bx, ty - 5, bw, 5, 'D', 3.0, hgt=1.35)
            lay.rect(bx, ty - 5, bw, 1, 'D', 4.4, hgt=1.4)
            for k in range(bw - 2):
                lay.px(bx + 1 + k, ty - 6, 'P', 4.8 + (k % 3) * 0.3, hgt=1.45)
        lay.put(K.disc(5), t0 + 48, ty - 4, 'C', 5.0, hgt=1.4)                # magnifier
        lay.line(t0 + 52, ty - 1, t0 + 57, ty - 1, 'D', 2.0)
        if self.cfg.get('file', True):
            fx = 994
            lay.rect(fx, ty - 4, 24, 4, 'G', 2.6, hgt=1.45)                   # grey-green folder, thick
            lay.rect(fx, ty - 4, 24, 1, 'G', 3.6, hgt=1.5)
            for k in range(3):
                lay.rect(fx + 1, ty - 3 + k, 22, 1, 'P', 4.6 - k * 0.4, hgt=1.45)
            lay.rect(fx + 18, ty - 6, 4, 3, 'R', 2.8, hgt=1.55)               # red tab "C-17"
            lay.rect(fx + 2, ty - 5, 12, 1, 'P', 3.0, hgt=1.5)                 # string
        if self.cfg.get('halves'):
            for (hx, ink) in ((958, 'R'), (1028, 'I')):                       # the two halves side by side
                for k in range(3):
                    lay.rect(hx + k, ty - 2 - k, 20, 1, 'P', 5.0 + k * 0.3, hgt=1.4 + k * 0.03)
                lay.rect(hx + 3, ty - 4, 6, 1, ink, 2.4)
                lay.rect(hx + 11, ty - 4, 7, 1, 'I', 1.8)
        # chairs at the table
        self.chair(t0 + 6, facing=-1)
        self.chair(t1 - 26, facing=1)
        self.info['table'] = (t0, ty - 6, t1, FL)

    def green_lamp(self):
        lay = self.lay
        cx, by = L.LAMP_GREEN
        on = bool(self.cfg.get('lamp_green'))
        lay.rect(cx, 0, 1, by - 9, 'I', 1.6, hgt=0.5)                          # cord from the vault
        lay.rect(cx - 2, by - 11, 5, 3, 'B', 3.6, hgt=1.0)                     # brass cap
        for i in range(8):                                                     # green enamel cone
            half = 3 + i
            lay.rect(cx - half, by - 8 + i, 2 * half + 1, 1, 'G', 3.0 - i * 0.12 + (on and i < 2) * 0.6, hgt=1.0)
            lay.px(cx - half, by - 8 + i, 'G', 4.0, hgt=1.05)
        lay.rect(cx - 10, by, 21, 1, 'B', 3.4, hgt=1.0)                        # rim
        if on:
            lay.rect(cx - 9, by + 1, 19, 1, 'P', 6.0, emis=True)                # the bright opening
            lay.rect(cx - 3, by - 1, 7, 1, 'B', 6.0, emis=True)
            self.light('green_lamp', (cx, by + 3), 'warm', 2.8 if not self.fire else 1.4, 180, 8,
                       falloff=1.1, cone=(0.0, 1.0, 0.18), pool=0.32, pool_depth=60, pool_w=34, pool_spread=0.9)
            self.light('green_lamp_shade', (cx, by - 6), 'warm', 0.18, 46, 20)
        elif self.cfg.get('torch'):
            # Konrad's torch: a beam into the aisle beside him (he stands at SP_C3_KonradCards)
            self.light('torch', (897, 266), 'white', 3.0, 150, 6, falloff=0.9, cone=(0.0, -1.0, 0.45),
                       pool=0.5, pool_dx=2, pool_depth=24, pool_w=8, pool_spread=0.4)

    # ================================================================== Planarchiv
    def planarchiv(self):
        lay = self.lay
        for cx in (1383, 1525):
            self.high_window(cx)
        self.sign_plate(1418, 104, ['ANLAGE C', 'ПРИЛОЖЕНИЕ В · ANNEXE C'])
        self.plan_wall()
        self.plan_chests()
        self.drafting_table(1500)

    def plan_wall(self):
        lay = self.lay
        fw, fh = 24, 18
        cols = [1290 + k * 38 for k in range(7)]
        rows = [124, 156, 188]
        sheet_no = 1
        burnt = self.fire >= 1
        for r, yy in enumerate(rows):
            for c, xx in enumerate(cols):
                if (r, c) == (0, 1):
                    continue                                    # Blatt 7 (drawn below)
                n = sheet_no if sheet_no < 7 else sheet_no + 1
                sheet_no += 1
                if burnt and (r, c) in ((1, 2), (0, 5)):
                    # gone (fallen): only the nail and the lighter rectangle remain
                    lay.rect(xx - 1, yy - 1, fw + 2, fh + 2, 'W', 4.6, hgt=0.0)
                    lay.px(xx + fw // 2, yy - 3, 'S', 3.6)
                    continue
                K.frame(lay, xx, yy, fw, fh, 'I', 1.2, hi=2.4, lo=0.4)
                self._sheet(xx, yy, fw, fh, n)
        # Blatt 7: askew, the lighter rectangle where it hung before
        bx = L.BLATT7[0]
        by = rows[0]
        lay.rect(bx - 1, by - 1, fw + 2, fh + 2, 'W', 4.8, hgt=0.0)
        lay.rect(bx - 1, by - 1, fw + 2, 1, 'W', 5.4)
        ox, oy = 2, 3
        for k in range(fw + 4):                                     # frame as a slightly rotated box
            sl = int(k * 2 / (fw + 4))
            lay.px(bx - 2 + ox + k, by - 2 + oy + sl, 'I', 2.2, hgt=0.7)
            lay.px(bx - 2 + ox + k, by + fh + 1 + oy + sl, 'I', 0.6, hgt=0.6)
        for k in range(fh + 4):
            lay.px(bx - 2 + ox, by - 2 + oy + k, 'I', 2.0, hgt=0.7)
            lay.px(bx + fw + 1 + ox, by - 2 + oy + k + 2, 'I', 0.6, hgt=0.6)
        if self.cfg.get('blatt7', True):
            self._sheet(bx + ox, by + oy + 1, fw, fh - 1, 7, kordon=True)
        else:
            lay.rect(bx + ox, by + oy + 1, fw, fh - 1, 'D', 1.8, hgt=0.3)      # the empty backing board
            for k in range(3):
                lay.px(bx + ox + 3 + k * 8, by + oy + 3, 'S', 3.0)
        lay.px(bx + fw // 2 + 1, by - 3, 'S', 3.6)                              # the nail
        lay.line(bx + fw // 2 + 1, by - 3, bx + ox + 3, by + oy - 1, 'S', 2.4)
        lay.line(bx + fw // 2 + 1, by - 3, bx + ox + fw - 3, by + oy, 'S', 2.4)
        self.info['blatt7'] = (bx - 4, by - 4, bx + fw + 6, by + fh + 6)

    def _sheet(self, x, y, w, h, n, kordon=False):
        lay = self.lay
        lay.rect(x, y, w, h, 'P', 4.6 + (n % 3) * 0.2, hgt=0.3)
        rng = np.random.default_rng(n * 31)
        # a little plan drawing: outline, rooms, a dimension line (ink lines)
        lay.rect(x + 2, y + 2, w - 4, 1, 'I', 1.8)
        lay.rect(x + 2, y + h - 5, w - 4, 1, 'I', 1.8)
        lay.rect(x + 2, y + 2, 1, h - 6, 'I', 1.8)
        lay.rect(x + w - 3, y + 2, 1, h - 6, 'I', 1.8)
        for k in range(int(rng.integers(1, 4))):
            xx = x + 4 + int(rng.integers(0, w - 8))
            lay.rect(xx, y + 3, 1, h - 8, 'I', 2.4)
        lay.rect(x + 3, y + 3 + int(rng.integers(2, h - 9)), w - 6, 1, 'I', 2.4)
        if kordon:
            lay.rect(x + 5, y + 6, 12, 2, 'D', 2.6)                         # the bench for 14
            for k in range(7):
                lay.px(x + 5 + k * 2, y + 9, 'I', 1.8)
            lay.rect(x + 15, y + 4, 4, 1, 'R', 2.6)
        lay.rect(x + w - 9, y + h - 4, 7, 3, 'P', 3.6)                       # title block
        K.text(lay, str(n), x + w - 5, y + h - 4, 'I', 0.6, center=True) if n < 10 else None

    def plan_chests(self):
        lay = self.lay
        x0, x1 = 1288, 1488
        top = 246
        for ux in range(x0, x1, 50):
            K.bevel(lay, ux, top, 48, FL - top, 'S', 2.2, hi=3.4, lo=1.0, hgt=0.8)
            for k in range(8):
                yy = top + 3 + k * 5
                if yy > FL - 6:
                    break
                lay.rect(ux + 2, yy, 44, 4, 'S', 2.6, hgt=0.75)
                lay.rect(ux + 2, yy + 3, 44, 1, 'S', 1.2, hgt=0.5)
                lay.rect(ux + 14, yy + 1, 20, 1, 'S', 4.0, hgt=0.9)
                lay.rect(ux + 4, yy + 1, 6, 2, 'P', 4.4 if k % 3 else 3.6, hgt=0.8)
            lay.rect(ux - 1, top - 2, 50, 2, 'S', 3.6, hgt=0.9)
        # the drawer of Annex C (exp_plan_chests): "KORDON-17", trilingual labels
        lay.rect(x0 + 2, top + 13, 40, 4, 'P', 4.8, hgt=0.9)
        K.text(lay, 'KORDON-17', x0 + 22, top + 13, 'I', 0.8, center=True)
        # rolled plans and a tube on top
        rng = np.random.default_rng(1300)
        for k in range(9):
            rx = x0 + 6 + k * 21 + int(rng.integers(0, 5))
            lay.rect(rx, top - 5, int(rng.integers(12, 18)), 3, 'P', 4.4 + rng.random() * 0.6, hgt=1.0)
            lay.rect(rx, top - 5, 1, 3, 'P', 3.0)
        self.info['chests'] = (x0, top, x1, FL)

    def drafting_table(self, x):
        lay = self.lay
        # tilted board on a cast-iron stand, a parallel rule, a stool
        for k in range(34):
            lay.px(x + k, 238 - int(k * 0.35), 'D', 4.0, hgt=1.0)
            lay.rect(x + k, 239 - int(k * 0.35), 1, 3, 'P', 4.8, hgt=0.9)
        lay.line(x + 2, 240, x + 30, 230, 'S', 3.6)
        lay.rect(x + 14, 242, 3, FL - 242, 'I', 1.8, hgt=0.8)
        lay.rect(x + 6, FL - 3, 20, 3, 'I', 1.4, hgt=0.8)
        lay.rect(x - 10, 268, 9, 2, 'D', 3.4, hgt=1.0)
        lay.rect(x - 7, 270, 3, FL - 270, 'I', 1.8, hgt=0.9)

    # ================================================================== Magazin
    def magazin(self):
        lay = self.lay
        for cx in (1610, 1748, 1886):
            self.high_window(cx)
        self.sign_plate(1700, 110, ['MAGAZIN', 'ХРАНИЛИЩЕ · DÉPÔT'])
        self.back_shelves(1752, 1858)
        for (x0, lab) in ((1626, 'A1-40'), (L.C17_SHELF[0], 'C1-24')):
            self.mobile_unit(x0, x0 + 36 if x0 != L.C17_SHELF[0] else L.C17_SHELF[1], lab)
        self.kurhaus_plaque()
        self.cassation_list()
        self.service_door()

    def kurhaus_plaque(self):
        """Enamel plate on the old brick: 'Kurhaus Veltrava 1909 - Kesselhaus - Zutritt nur fuer Heizer'."""
        lay = self.lay
        x0, x1 = L.PLAQUE
        y = 198
        w = x1 - x0
        lay.rect(x0 + 1, y + 16, w, 1, 'K', 1.0)
        lay.rect(x0, y, w, 16, 'S', 1.4, hgt=0.6)
        lay.rect(x0 + 1, y + 1, w - 2, 14, 'C', 2.6, hgt=0.7)                      # blue enamel
        K.text(lay, 'KURHAUS', (x0 + x1) // 2, y + 2, 'P', 5.2, center=True)
        K.text(lay, '1909', (x0 + x1) // 2, y + 8, 'P', 5.2, center=True)
        for (cx, cy) in ((x0 + 2, y + 2), (x1 - 3, y + 2), (x0 + 2, y + 13), (x1 - 3, y + 13)):
            lay.px(cx, cy, 'S', 3.6)
        chip = K.noise(w, 16, 3, 1602) > 0.32
        chip[2:14, 2:w - 2] = False
        lay.put(chip, x0, y, 'I', 1.0)

    def cassation_list(self):
        """The typed cassation list on its clipboard; the last line was added today."""
        lay = self.lay
        x0, x1 = L.CASSATION
        y = 206
        lay.rect(x0 + (x1 - x0) // 2, y - 6, 1, 6, 'S', 2.4)                      # nail + string
        lay.rect(x0, y, x1 - x0, 24, 'D', 2.8, hgt=0.6)                            # board
        lay.rect(x0 + 4, y - 1, x1 - x0 - 8, 3, 'S', 3.4, hgt=0.9)                 # clip
        lay.rect(x0 + 1, y + 2, x1 - x0 - 2, 21, 'P', 4.8, hgt=0.7)
        K.pseudo_text(lay, x0 + 2, y + 4, x1 - x0 - 4, 7, 'I', 1.6, seed=1728, gap=2)
        lay.rect(x0 + 2, y + 19, x1 - x0 - 5, 1, 'R', 2.2)                         # the new line
        self.info['cassation'] = (x0, y, x1, y + 24)

    def mobile_unit(self, x0, x1, label):
        lay = self.lay
        top = 150
        w = x1 - x0
        # the shelves of the unit, seen in the gap before it (boxes)
        rng = np.random.default_rng(x0)
        lay.rect(x0 - 4, top, 4, FL - top, 'N', 0.6, hgt=-0.4)
        for yy in range(top + 6, FL - 10, 22):
            for k in range(2):
                lay.rect(x0 - 3, yy + k * 9, 2, 8, 'P', 1.4 + rng.random() * 0.4, hgt=-0.3)
        # end panel (painted steel), top cap, label frame, hand wheel
        K.bevel(lay, x0, top, w, FL - top - 4, 'S', 2.6, hi=3.6, lo=1.2, hgt=0.8)
        lay.rect(x0 - 1, top - 3, w + 2, 3, 'S', 3.2, hgt=0.9)
        K.recess(lay, x0 + 4, top + 8, w - 8, 60, 'S', 2.2, shadow=1.2, light=3.4, hgt=0.7)
        K.recess(lay, x0 + 4, top + 74, w - 8, 52, 'S', 2.2, shadow=1.2, light=3.4, hgt=0.7)
        lx = x0 + w // 2 - 10
        lay.rect(lx, top + 14, 20, 10, 'S', 1.4, hgt=0.9)
        lay.rect(lx + 1, top + 15, 18, 8, 'P', 5.2, hgt=0.9)
        K.text(lay, label, lx + 10, top + 17, 'I', 0.6, center=True)
        wx, wy = x0 + w // 2, 238
        for a in range(0, 360, 6):
            r = 7
            lay.px(wx + round(math.cos(math.radians(a)) * r), wy + round(math.sin(math.radians(a)) * r), 'S',
                   4.0 if 200 < a < 320 else 2.4, hgt=1.2)
        for a in (90, 210, 330):
            lay.line(wx, wy, wx + round(math.cos(math.radians(a)) * 6), wy + round(math.sin(math.radians(a)) * 6),
                     'S', 3.0, hgt=1.1)
        lay.rect(wx - 1, wy - 1, 3, 3, 'S', 4.2, hgt=1.3)
        lay.rect(wx + 6, wy - 9, 2, 4, 'I', 2.6, hgt=1.3)                      # crank knob
        lay.rect(x0, FL - 4, w, 4, 'S', 1.4, hgt=0.6)
        if label.startswith('C'):
            lay.rect(lx - 2, top + 28, 24, 7, 'R', 2.6, hgt=0.9)                # the red "C-17" tag strip
            K.text(lay, 'C-17', lx + 10, top + 29, 'P', 5.4, center=True)

    def back_shelves(self, x0, x1):
        lay = self.lay
        top = 140
        lay.rect(x0, top, x1 - x0, FL - top, 'N', 1.0, hgt=-0.2)
        for ux in (x0, x0 + (x1 - x0) // 2, x1 - 3):
            lay.rect(ux, top, 3, FL - top, 'S', 2.6, hgt=0.6)
        rng = np.random.default_rng(1752)
        boards = list(range(top + 4, FL - 6, 24))
        for i, yy in enumerate(boards):
            lay.rect(x0, yy + 20, x1 - x0, 2, 'S', 3.0, hgt=0.6)
            xx = x0 + 3
            while xx < x1 - 8:
                bw = int(rng.integers(9, 13))
                bh = int(rng.integers(15, 19))
                if xx + bw > x1 - 3:
                    break
                tone = 2.8 + rng.random() * 0.7
                lay.rect(xx, yy + 20 - bh, bw, bh, 'P', tone, hgt=0.5)
                lay.rect(xx, yy + 20 - bh, 1, bh, 'P', tone + 0.8)
                lay.rect(xx + 2, yy + 20 - bh + 3, bw - 4, 5, 'P', 4.8, hgt=0.55)          # label
                lay.rect(xx + 3, yy + 20 - bh + 4, bw - 6, 1, 'I', 2.0)
                xx += bw + 1
        # delegation labels on the section boards (insignia site: neutral here, *_hist via the patch)
        self._delegation_plate(x0 + 6, top - 12, 'ussr')
        self._delegation_plate(x0 + (x1 - x0) // 2 + 6, top - 12, 'reich')
        self.info['insignia_magazin'] = (x0 + 2, top - 14, x1 - 2, top - 1)

    def _delegation_plate(self, x, y, kind):
        lay = self.lay
        w = 44
        lay.rect(x, y, w, 10, 'P', 5.0, hgt=0.7)
        lay.rect(x, y, w, 1, 'S', 2.0)
        lay.rect(x, y + 9, w, 1, 'S', 1.6)
        K.text(lay, 'СССР' if kind == 'ussr' else 'REICH', x + 12 + 14, y + 3, 'I', 0.8, center=True)
        ex, ey = x + 2, y + 2
        if kind == 'ussr':
            if self.hist:
                pat = ['.#...', '###..', '.#...', '.##.#', '...##', '#.##.']     # star over hammer and sickle
            else:
                pat = ['..#..', '.###.', '##.##', '.###.', '..#..', '#...#']   # gear + wheat (fictional)
            for yy, row in enumerate(pat):
                for xx, ch in enumerate(row):
                    if ch == '#':
                        lay.px(ex + xx, ey + yy, 'R', 2.6, crisp=True)
        else:
            if self.hist:
                # round state stamp with the hooked cross (in-world iconography, historical setting only)
                pat = ['#.###', '#.#..', '#####', '..#.#', '###.#']
            else:
                d, pil = K.hk.reichssiegel_mask(6)
                pat = [''.join('o' if pil[r, c] else ('#' if d[r, c] else '.') for c in range(6)) for r in range(6)]
            for yy, row in enumerate(pat):
                for xx, ch in enumerate(row):
                    if ch == '#':
                        lay.px(ex + xx, ey + yy, 'I', 0.6, crisp=True)
                    elif ch == 'o':
                        lay.px(ex + xx, ey + yy, 'P', 5.6, crisp=True)

    def service_door(self):
        lay = self.lay
        s0, s1 = L.SERVICE_DOOR
        top = 226
        open_ = self.fire >= 1
        lay.rect(s0 - 3, top - 4, s1 - s0 + 6, FL - top + 4, 'S', 1.6, hgt=0.6)
        lay.rect(s0, top, s1 - s0, FL - top, 'N', 0.6, hgt=-0.4)
        if not open_:
            # steel fire door (closed) behind the barred grille
            K.bevel(lay, s0 + 1, top + 1, s1 - s0 - 2, FL - top - 1, 'G', 2.0, hi=2.8, lo=1.0, hgt=0.5)
            lay.rect(s1 - 8, top + 30, 4, 2, 'S', 3.4, hgt=0.8)
            for x in range(s0 + 2, s1 - 1, 4):
                lay.rect(x, top, 1, FL - top, 'I', 2.0, hgt=0.9)
            for yy in (top + 4, top + 32, FL - 6):
                lay.rect(s0, yy, s1 - s0, 2, 'I', 1.8, hgt=0.9)
            lay.rect(s0 + 4, top + 34, 4, 5, 'S', 3.4, hgt=1.0)                      # padlock
        else:
            # the grille swung open against the wall, the fire door ajar (wedged): the stair beyond
            for yy in range(top + 2, FL):
                lay.rect(s0 + 6, yy, s1 - s0 - 8, 1, 'N', 1.2 + (yy - top) * 0.012, hgt=-0.4)
            for k in range(6):                                                         # stair steps beyond
                lay.rect(s0 + 10 + k * 3, FL - 6 - k * 6, s1 - s0 - 14 - k * 3, 1, 'S', 1.6, hgt=-0.3)
            K.bevel(lay, s0 + 1, top + 1, 6, FL - top - 1, 'G', 1.6, hi=2.4, lo=0.8, hgt=0.5)
            lay.rect(s0 + 7, FL - 4, 6, 3, 'D', 3.0, hgt=0.6)                          # the wooden wedge
            for x in range(s1 + 4, s1 + 16, 4):
                lay.rect(x, top, 1, FL - top, 'I', 2.0, hgt=0.9)
            for yy in (top + 4, top + 32, FL - 6):
                lay.rect(s1 + 3, yy, 13, 2, 'I', 1.8, hgt=0.9)
        # lit exit sign + caged bulb lamp
        sx = (s0 + s1) // 2
        lay.rect(sx - 15, top - 20, 30, 12, 'S', 1.2, hgt=0.8)
        lay.rect(sx - 14, top - 19, 28, 10, 'P', 5.6, emis=True)
        K.text(lay, 'AUSGANG', sx, top - 18, 'R', 2.2, center=True, emis=True)
        K.text(lay, 'ВЫХОД', sx, top - 13 + 0, 'R', 2.2, center=True, emis=True)
        lay.rect(sx - 3, top - 30, 7, 6, 'S', 1.6, hgt=1.0)
        lay.rect(sx - 2, top - 29, 5, 4, 'B', 5.6, emis=True)
        for x in (sx - 3, sx, sx + 3):
            lay.px(x, top - 28, 'I', 1.0)
        self.light('exit_lamp', (sx, top - 24), 'warm', 1.3, 110, 14, pool=0.35, pool_depth=30, pool_w=12)
        # the extinguisher on its bracket
        ex = s0 - 20
        lay.rect(ex, 246, 7, 22, 'R', 2.6, hgt=1.0)
        lay.rect(ex, 246, 2, 22, 'R', 3.4, hgt=1.05)
        lay.rect(ex + 1, 242, 5, 4, 'S', 2.6, hgt=1.0)
        lay.rect(ex + 2, 250, 3, 6, 'P', 5.0)
        lay.rect(ex - 2, 254, 11, 2, 'S', 1.6, hgt=0.9)

    # ================================================================== floor
    def floor(self):
        lay = self.lay
        y0 = FL
        rows = [0, 3, 6, 10, 15, 21, 28, 36, 45, 55, 66, 72]
        ys = np.arange(H, dtype=np.float32)
        # --- yard: snow over cobbles with tracks (perspective rows of setts showing in the tracks)
        x1 = L.PIER[0]
        snow_t = np.zeros((H - y0, x1), np.float32)
        sn = K.noise(x1, H - y0, 10, 81) * 0.5 + K.noise(x1, H - y0, 3, 82, octaves=1) * 0.25
        snow_t[:] = 3.1 + sn - np.clip((np.arange(H - y0)[:, None] - 20) / 52.0, 0, 1) * 0.8
        lay.put(np.ones((H - y0, x1), bool), 0, y0, 'SN', snow_t, hgt=0.0, flat=False)
        # tracks: handcart wheels from the gate to the cart, trodden path to the door
        for (ty, tw) in ((y0 + 16, 2), (y0 + 30, 2)):
            for x in range(10, L.CART[0] + 30):
                yy = ty + int(3 * math.sin(x / 60.0))
                lay.rect(x, yy, 1, tw, 'SN', 2.0, hgt=-0.1)
                lay.px(x, yy + tw, 'SN', 3.0)
        for x in range(L.CART[1], L.PIER[0]):                              # trampled to grey slush
            for yy in range(y0 + 2, y0 + 22):
                k = 1.0 - abs((yy - y0 - 12) / 10.0)
                if (x * 13 + yy * 7) % 5 < 3 * k:
                    lay.px(x, yy, 'SN', 1.6 + ((x + yy) % 3) * 0.4)
        rng = np.random.default_rng(83)
        # exp_two_tracks: a fresh line of smooth-soled city shoes; beneath, half snowed-in, two older lines
        # close together -- heavy boots and narrow ladies' shoes. All lead to the ramp; none comes back.
        for k in range(30):
            fx = 40 + k * 11
            if fx > L.RAMP[0] - 4:
                break
            fy = y0 + 18 + int(4 * math.sin(fx / 90.0)) + (k % 2) * 3
            lay.rect(fx, fy, 3, 1, 'SN', 1.4)                                 # fresh: crisp, dark
            lay.px(fx + 1, fy + 1, 'SN', 1.8)
            lay.px(fx + 3, fy, 'SN', 4.6)
        for k in range(36):
            fx = 34 + k * 9
            if fx > L.RAMP[0] - 4:
                break
            fy = y0 + 27 + int(3 * math.sin(fx / 70.0)) + (k % 2) * 3
            lay.rect(fx, fy, 3, 2, 'SN', 2.6)                                 # boots (older, softened)
            fy2 = fy + 7 + (k % 2)
            lay.rect(fx + 2, fy2, 2, 1, 'SN', 2.8)                            # narrow shoes beside them
        # cobbles peeking through the slush near the wall
        for yy in range(y0, y0 + 6):
            for x in range(L.FACADE[0], x1, 5):
                if (x // 5 + yy) % 3 == 0:
                    lay.rect(x, yy, 3, 1, 'S', 2.4, hgt=0.2)
        # the coal hatch: cast-iron plate in the ground, "1909", snow pushed off one corner
        h0, h1 = L.HATCH
        for yy in range(y0, y0 + 9):
            a = h0 - (yy - y0) // 3
            b = h1 + (yy - y0) // 3
            lay.rect(a, yy, b - a, 1, 'I', 1.8 + ((yy - y0) % 3 == 0) * 0.6, hgt=0.1)
        for x in range(h0 + 2, h1 - 2, 3):
            lay.px(x, y0 + 2, 'I', 2.8)
            lay.px(x + 1, y0 + 6, 'I', 2.8)
        K.text(lay, '1909', (h0 + h1) // 2, y0 + 2, 'S', 3.6, center=True)
        for hx_ in (h0 + 3, h1 - 6):                                       # freshly oiled hinges
            lay.rect(hx_, y0, 3, 2, 'B', 3.8, hgt=0.3)
            lay.px(hx_ + 1, y0, 'B', 5.4)
        for x in range(h0 - 3, h0 + 12):
            lay.px(x, y0 + int((x - h0) * 0.3) + 6, 'SN', 4.4)
        # concrete ramp up to the door sill
        r0, r1 = L.RAMP
        for x in range(r0, r1):
            k = (x - r0) / (r1 - r0)
            top = int(round(y0 + 2 - 6 * k))
            lay.rect(x, top, 1, y0 + 14 - top, 'W', 3.0 + k * 0.6, hgt=0.4)
            lay.px(x, top, 'SN', 4.6)
        lay.line(r0, y0 + 2, r1, y0 - 4, 'S', 3.8)
        # --- interior: per-room floors
        self._terrazzo(L.PIER[1], L.PART1[1], rows)
        self._boards(L.PART1[1], L.PART2[0], rows)
        self._lino(L.PART2[1], L.PART3[0], rows)
        self._screed(L.PART3[1], W, rows)
        # thresholds under the partitions + the pier's sill
        for (a, b) in (L.PART2, L.PART3):
            lay.rect(a, y0, b - a, H - y0, 'S', 1.8, hgt=0.05)
            lay.rect(a, y0, 1, H - y0, 'S', 3.0)
        lay.rect(L.PIER[0], y0, L.PIER[1] - L.PIER[0], H - y0, 'S', 2.2, hgt=0.05)
        lay.rect(L.PIER[0], y0, L.PIER[1] - L.PIER[0], 1, 'S', 3.6)
        # coir mat inside the ramp door
        for yy in range(y0 + 3, y0 + 16):
            k = yy - y0
            lay.rect(L.PIER[1] + 2 - k // 3, yy, 40 + k // 2, 1, 'D', 3.0 + ((yy + k) % 2) * 0.5, hgt=0.0)
        # contact shadow along the wall + floor normals + falloff toward the viewer
        lay.rect(L.PIER[0], y0, W - L.PIER[0], 1, 'N', 1.0)
        lay.shade_rect(0, y0 + 1, W, 3, -0.5)
        m = np.zeros((H, W), bool)
        m[y0:, :] = lay.rid[y0:, :] >= 0
        lay.paint_normal(m, 0, 0, (0.0, 0.86, 0.5))
        # floors take less of the baked light (they face the lamps squarely): pools stay pools
        lay.lgain[y0:, :] = 0.75 if not self.fire else 0.3
        fall = np.zeros((H, W), np.float32)
        fall[:] = (np.clip((ys - 318) / 42, 0, 1) * -1.0)[:, None]
        lay.amb_field(fall)

    def _rows(self, rows):
        return [(FL + rows[i], min(H, FL + rows[i + 1])) for i in range(len(rows) - 1)]

    def _terrazzo(self, x0, x1, rows):
        lay = self.lay
        w = x1 - x0
        tz = K.noise(w, H - FL, 12, 91) * 0.35
        speck = K.noise(w, H - FL, 1, 92, octaves=1)
        t = 3.0 + tz + (speck > 0.32) * 0.8 - (speck < -0.34) * 0.7
        lay.put(np.ones((H - FL, w), bool), x0, FL, 'W', t, hgt=0.0, flat=False)
        vp = (x0 + x1) / 2
        for (ra, rb) in self._rows(rows)[::2]:
            lay.rect(x0, ra, w, 1, 'W', 2.2)
        for (ra, rb) in self._rows(rows):
            fr = (ra + 0.5 - L.HORIZON) / (FL - L.HORIZON)
            for u in range(int(x0 - 400), int(x1 + 400), 48):
                xx = int(round(vp + (u - vp) * fr))
                if x0 <= xx < x1:
                    lay.rect(xx, ra, 1, rb - ra, 'W', 2.2)
        lay.rect(x0, FL, w, 3, 'G', 1.6)                                     # skirting border
        lay.rect(x0, FL + 3, w, 1, 'S', 2.6)

    def _boards(self, x0, x1, rows):
        lay = self.lay
        rng = np.random.default_rng(700)
        for (ra, rb) in self._rows(rows):
            hgt = rb - ra
            xx = x0 - int(rng.integers(0, 60))
            while xx < x1:
                ln = int(rng.integers(60, 140))
                a, b = max(x0, xx), min(x1, xx + ln)
                if b > a:
                    base = 2.7 + rng.normal(0, 0.18)
                    g = K.noise(b - a, max(1, hgt), 9, int(rng.integers(0, 9999)), octaves=2) * 0.5
                    lay.put(np.ones((hgt, b - a), bool), a, ra, 'D', base + g, hgt=0.0, flat=False)
                    lay.rect(a, ra, 1, hgt, 'D', 1.2)
                xx += ln
            lay.rect(x0, ra, x1 - x0, 1, 'D', 1.4)
        # the worn path in front of the cabinets + wax sheen strip
        for x in range(x0, x1):
            for yy in range(FL + 8, FL + 20):
                if (x + yy * 3) % 7 == 0:
                    lay.shade_rect(x, yy, 1, 1, 0.5)

    def _lino(self, x0, x1, rows):
        lay = self.lay
        w = x1 - x0
        mz = K.noise(w, H - FL, 6, 95) * 0.6
        lay.put(np.ones((H - FL, w), bool), x0, FL, 'K', 2.0 + mz, hgt=0.0, flat=False)
        for (ra, rb) in self._rows(rows)[1::3]:
            lay.rect(x0, ra, w, 1, 'K', 1.0)

    def _screed(self, x0, x1, rows):
        lay = self.lay
        w = x1 - x0
        cz = K.noise(w, H - FL, 18, 97) * 0.4 + K.noise(w, H - FL, 2, 98, octaves=1) * 0.25
        lay.put(np.ones((H - FL, w), bool), x0, FL, 'S', 2.6 + cz, hgt=0.0, flat=False)
        for ry in (FL + 3, FL + 9):                                         # rails of the mobile shelving
            lay.rect(x0, ry, L.C17_SHELF[1] + 30 - x0, 1, 'S', 4.0)
            lay.rect(x0, ry + 1, L.C17_SHELF[1] + 30 - x0, 1, 'S', 1.4)
        for (ra, rb) in self._rows(rows):                                    # worn ochre aisle line
            if ra > FL + 30:
                lay.rect(x0, ra, w, 1, 'B', 1.4)
                break

    # ================================================================== fire damage + ambient
    def fire_damage(self):
        """Soot, scorch and char of the fire states (flames themselves are FX strips on top)."""
        if not self.fire:
            return
        lay = self.lay
        front = 1236 if self.fire == 1 else 690
        xs = np.arange(W, dtype=np.float32)[None, :]
        ys = np.arange(H, dtype=np.float32)[:, None]
        # soot: ceiling and upper wall darken from the fire side; strongest where things burn
        reach = np.clip((xs - (front - 260)) / 420, 0, 1)
        soot = reach * np.clip((150 - ys) / 150, 0, 1) * 1.6
        soot += np.clip((xs - front) / 200, 0, 1) * np.clip((260 - ys) / 260, 0, 1) * 1.1
        nz = K.noise(W, H, 14, 501) * 0.6
        soot = np.where(ys < FL, soot * (1 + nz), 0)
        soot[:, :L.PIER[1]] = 0
        lay.amb_field(-soot.astype(np.float32))
        # charred objects behind the fire front (darker oak / boxes, glowing cracks)
        rng = np.random.default_rng(777)
        burn = np.zeros((H, W), bool)
        burn[130:FL, front + 20:] = True
        if self.fire == 2:
            burn[140:FL, L.ROWS[0][0]:L.BANK[1]] = True
        cand = burn & lay.ramp_mask('D', 'P', 'K')
        lay.shade_mask(cand, 0, 0, -1.4)
        cy_, cx_ = np.nonzero(cand & (K.noise(W, H, 3, 503, octaves=1) > 0.33))
        for yy, xx in zip(cy_[::3], cx_[::3]):
            lay.px(xx, yy, 'F', 2.6 + rng.random() * 1.6, emis=True)
        # the fallen, burning frame on the Planarchiv floor (glowing char)
        f0, f1 = L.FALLEN_FRAME
        for k in range(f1 - f0):
            yy = FL + 2 + int(k * 0.12)
            lay.rect(f0 + k, yy, 1, 2, 'I', 1.0)
            if k % 3 == 0:
                lay.px(f0 + k, yy - 1, 'F', 4.0, emis=True)
        # collapsed C-17 shelf: boxes slid onto the floor, glowing
        c0, c1 = L.C17_SHELF
        for k in range(14):
            bx = c0 - 10 + int(rng.integers(0, c1 - c0 + 20))
            by = FL - 8 + int(rng.integers(0, 10))
            lay.rect(bx, by, 7, 5, 'I', 1.2, hgt=0.6)
            lay.rect(bx + 1, by, 5, 1, 'F', 3.2, emis=True)
        if self.fire == 2:
            # the green lamp's shade cracked, the cord singed (lamp dark)
            cx, by = L.LAMP_GREEN
            lay.rect(cx - 2, by - 6, 2, 5, 'N', 0.6)

    def ambient(self):
        lay = self.lay
        f = np.zeros((H, W), np.float32)
        ys = np.arange(H, dtype=np.float32)[:, None]
        xs = np.arange(W, dtype=np.float32)
        reg = np.zeros(W, np.float32)
        reg[L.PART2[0]:] = -0.25                                   # Planarchiv + Magazin: no lamp of their own
        reg[L.PART3[0]:] = -0.45
        k = np.ones(31, np.float32) / 31
        reg = np.convolve(np.pad(reg, 15, mode='edge'), k, mode='valid')
        f += reg[None, :]
        inter = np.zeros(W, np.float32)
        inter[L.PIER[1]:] = 1.0
        f += -1.2 * np.clip((140 - ys) / 110, 0, 1) * inter[None, :]
        f += -0.8 * np.clip((60 - ys) / 60, 0, 1) * (1 - inter)[None, :] * 0.4
        f += -0.9 * np.clip((30 - xs) / 30, 0, 1)[None, :]
        f += -0.9 * np.clip((xs - (W - 30)) / 30, 0, 1)[None, :]
        f[lay.emis] = 0
        lay.amb_field(f)

    # ================================================================== lights of the configuration
    def scene_lights(self):
        """Lights not built by an element: snow glow in the yard, the fire."""
        out = [
            {'name': 'yard_sky', 'pos': (190.0, -40.0), 'kind': 'cold', 'energy': 0.6, 'radius': 420, 'height': 60,
             'box': (0, 0, L.PIER[0] + 4, H)},
            {'name': 'yard_snow_bounce', 'pos': (190.0, 330.0), 'kind': 'cold', 'energy': 0.5, 'radius': 260,
             'height': 30, 'box': (0, 0, L.PIER[0] + 6, H)},
        ]
        if self.fire >= 1:
            out += [
                {'name': 'fire_c17', 'pos': (1704.0, 210.0), 'kind': 'warm', 'energy': 2.2, 'radius': 520, 'height': 26},
                {'name': 'fire_magazin_r', 'pos': (1830.0, 250.0), 'kind': 'warm', 'energy': 1.4, 'radius': 320,
                 'height': 20},
                {'name': 'fire_planarchiv', 'pos': (1420.0, 262.0), 'kind': 'warm', 'energy': 1.3, 'radius': 300,
                 'height': 18},
                {'name': 'fire_plan_wall', 'pos': (1400.0, 160.0), 'kind': 'warm', 'energy': 1.0, 'radius': 260,
                 'height': 22},
                {'name': 'fire_front_c', 'pos': (1248.0, 240.0), 'kind': 'warm', 'energy': 2.0, 'radius': 420,
                 'height': 22},
                {'name': 'fire_smoke_glow', 'pos': (1500.0, 20.0), 'kind': 'warm', 'energy': 0.9, 'radius': 900,
                 'height': 60},
            ]
        if self.fire >= 2:
            out += [
                {'name': 'fire_bank', 'pos': (1150.0, 200.0), 'kind': 'warm', 'energy': 1.8, 'radius': 420, 'height': 24},
                {'name': 'fire_rows', 'pos': (810.0, 210.0), 'kind': 'warm', 'energy': 1.6, 'radius': 380, 'height': 24},
                {'name': 'fire_table', 'pos': (1000.0, 262.0), 'kind': 'warm', 'energy': 1.0, 'radius': 220,
                 'height': 14},
                {'name': 'fire_front_d', 'pos': (702.0, 244.0), 'kind': 'warm', 'energy': 2.2, 'radius': 440,
                 'height': 22},
                {'name': 'fire_smoke_glow_d', 'pos': (900.0, 40.0), 'kind': 'warm', 'energy': 0.8, 'radius': 800,
                 'height': 60},
            ]
        return out

    # ================================================================== build
    def build(self):
        self.shell()
        self.yard()
        self.pier_and_door()
        self.annahme()
        self.partition(*L.PART1)
        self.karteisaal()
        self.partition(*L.PART2)
        self.planarchiv()
        self.partition(*L.PART3)
        self.magazin()
        self.floor()
        self.fire_damage()
        self.ambient()
        return self.lay

    def all_lights(self):
        return self.scene_lights() + self.lights
