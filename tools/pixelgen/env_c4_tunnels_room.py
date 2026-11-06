"""env_c4_tunnels_room -- the main layer of L_C4_Tunnels (cellar, door wall, tunnel, siding, floor), one bake per
configuration.

Painted in tone space (env_c4_tunnels_kit.tlayer on the 'tunnels' super-ramps) for a configuration `cfg`
(door_open, wagon_door 'half'|'open', plan_rolled, hist), baked with its lights and resolved palette-pure.  The
glass of the two high cellar windows is left transparent: outside.png shows through it.  The hanging lamps (enamel
shade in the cellar, the bulb over the wagon) are not baked -- they are decals the level script can swing; their
light is baked.  Tunnel and siding painters live in env_c4_tunnels_siding.py.
"""
from __future__ import annotations

import math

import numpy as np

import env_c4_tunnels_kit as K
import env_c4_tunnels_layout as L

W, H = L.WORLD_W, L.WORLD_H
FL = L.FLOOR


class Room:
    def __init__(self, cfg: dict):
        self.cfg = cfg
        self.lay = K.tlayer(W, H, 'room')
        self.glass = np.zeros((H, W), bool)
        self.lights: list[dict] = []
        self.windows: list[tuple] = []        # (x0, y0, x1, y1) glass rects of the cellar windows
        self.hist = bool(cfg.get('hist', False))
        self.rng = np.random.default_rng(1964)

    # ------------------------------------------------------------------ helpers
    def light(self, name, pos, kind, energy, radius, height=24, **kw):
        d = {'name': name, 'pos': (float(pos[0]), float(pos[1])), 'kind': kind, 'energy': energy, 'radius': radius,
             'height': height}
        d.update(kw)
        self.lights.append(d)
        return d

    def cut(self, x, y, w, h):
        self.lay.erase(x, y, w, h)
        self.glass[max(0, y):y + h, max(0, x):x + w] = True

    def planks_v(self, x0, x1, y0, y1, ramp='D', base=2.6, width=6, seed=0, hgt=0.4, var=0.35):
        """Vertical boards with dark joints and grain."""
        lay = self.lay
        rng = np.random.default_rng(seed)
        x = x0
        while x < x1:
            w = min(width + int(rng.integers(-1, 2)), x1 - x)
            if w <= 0:
                break
            K.grain(lay, x, y0, w, y1 - y0, ramp, base + rng.normal(0, var), seed=int(rng.integers(0, 9999)),
                    amp=0.35, hgt=hgt)
            lay.rect(x, y0, 1, y1 - y0, ramp, base - 1.4, hgt=hgt * 0.3)
            x += w

    def planks_h(self, x0, x1, y0, y1, ramp='D', base=2.6, height=5, seed=0, hgt=0.4, var=0.3):
        lay = self.lay
        rng = np.random.default_rng(seed)
        y = y0
        while y < y1:
            h = min(height, y1 - y)
            K.grain(lay, x0, y, x1 - x0, h, ramp, base + rng.normal(0, var), seed=int(rng.integers(0, 9999)),
                    amp=0.3, hgt=hgt, vertical=False)
            lay.rect(x0, y + h - 1, x1 - x0, 1, ramp, base - 1.3, hgt=hgt * 0.3)
            y += h

    def plate(self, x, y, w, h, lines, ramp='P', tone=5.0, ink=('I', 1.0), border=('R', 2.0), wear=0.0, seed=0,
              font='35', gap=2):
        """An enamel / painted sign with centred lines of text."""
        lay = self.lay
        lay.rect(x, y, w, h, border[0], border[1], hgt=0.5)
        lay.rect(x + 1, y + 1, w - 2, h - 2, ramp, tone, hgt=0.55)
        gh = 5 if font == '35' else 7
        tot = len(lines) * gh + (len(lines) - 1) * gap
        ty = y + (h - tot) // 2
        for i, s in enumerate(lines):
            if isinstance(s, tuple):
                s, ink_ = s
            else:
                ink_ = ink
            if wear > 0:
                K.worn_text(lay, s, x + w / 2, ty + i * (gh + gap), ink_[0], ink_[1], font=font, wear=wear,
                            seed=seed + i, center=True, hgt=0.6)
            else:
                K.text(lay, s, x + w / 2, ty + i * (gh + gap), ink_[0], ink_[1], font=font, center=True, hgt=0.6)
        if wear > 0:   # chipped enamel
            rng = np.random.default_rng(seed + 99)
            for _ in range(int(w * h * wear * 0.05) + 1):
                cx, cy = int(rng.integers(x, x + w)), int(rng.integers(y, y + h))
                lay.px(cx, cy, 'I', 1.4)

    # ================================================================== shell: poche + earth
    def poche(self):
        self.lay.rect(0, 0, W, H, 'N', 1.0, hgt=0.0)

    # ================================================================== cellar (A)
    def cellar_wall(self):
        lay = self.lay
        x0, x1 = L.CELLAR[0], L.DOOR_WALL[0]
        w = x1 - x0
        top = L.C_SPRING
        hh = FL - top
        ys = np.arange(hh, dtype=np.float32)[:, None]
        # limewashed brick: thin, patchy wash; warmer low down where the stove and the lamp have yellowed it
        t = K.bricks(lay, x0, top, w, hh, 'W', 0.0, seed=401, course=4, length=10, joint=-0.5, var=0.18)
        nz = K.noise(w, hh, 22, 402) * 0.55 + K.noise(w, hh, 6, 403, octaves=2) * 0.25
        base = 3.6 + 0.3 * np.clip(ys / 120.0, 0, 1)
        lay.put(np.ones((hh, w), bool), x0, top, 'W', base + nz + t, flat=False, hgt=0.12)
        flake = (K.noise(w, hh, 46, 404, octaves=3) > 0.3) & (K.noise(w, hh, 9, 405, octaves=2) > 0.0)
        bt = np.zeros((hh, w), np.float32)
        for row in range(0, hh, 4):
            off = (row // 4) % 2 * 5
            for bx in range(-10, w + 10, 10):
                a_, b_ = max(0, bx + off), min(w, bx + off + 9)
                if b_ > a_:
                    bt[row:row + 3, a_:b_] = 3.0 + ((bx * 7 + row * 13) % 5) * 0.22
            bt[min(hh - 1, row + 3), :] = 1.6
        lay.put(flake, x0, top, 'K', bt, hgt=0.08, flat=False)
        # green oil-paint dado (the Soviet "panel") with a dark lining stripe, tar plinth
        dado = 236
        dz = K.noise(w, FL - dado, 14, 406) * 0.35
        lay.put(np.ones((FL - dado, w), bool), x0, dado, 'G', 2.6 + dz, hgt=0.05, flat=False)
        lay.rect(x0, dado - 1, w, 1, 'G', 1.2, hgt=0.1)
        lay.rect(x0, dado, w, 1, 'G', 3.6, hgt=0.15)
        scuff = K.noise(w, 1, 4, 407)[0]
        for xx in range(w):
            if scuff[xx] > 0.28:
                lay.rect(x0 + xx, dado + 24 + int(scuff[xx] * 8), 1, 2, 'G', 1.6)
        lay.rect(x0, FL - 7, w, 7, 'N', 2.2, hgt=0.1)
        lay.rect(x0, FL - 7, w, 1, 'I', 2.6, hgt=0.15)
        # damp tide line above the plinth
        damp = np.zeros((FL - top, w), bool)
        prof = (dado - 20 - top + 8 * K.noise(w, 1, 30, 408)[0]).astype(int)
        for xx in range(w):
            damp[max(0, prof[xx]):dado - top, xx] = True
        lay.shade_mask(damp, x0, top, -0.4)

    def cellar_vault(self):
        """Four brick barrel vaults running toward the viewer, seen from below: the back wall ends in a lunette arch
        per bay, above it the soffit recedes (course lines converge on the vanishing point, the crown catches the
        lamp light, the near edge drowns in the dark); brick arch ribs between the bays widen toward the viewer."""
        lay = self.lay
        sp = L.C_SPRING
        x0, x1 = L.CELLAR[0], L.DOOR_WALL[0]
        w = x1 - x0
        vp, hz = 350.0, float(L.HORIZON)
        ribs = L.C_RIBS
        rise = 38.0
        yy, xx = np.mgrid[0:sp + 1, x0:x1].astype(np.float32)
        f = 1.0 + 0.6 * (sp - yy) / sp                           # perspective spread above the springing
        u = vp + (xx + 0.5 - vp) / f                              # wall coordinate of the soffit pixel
        depth = (sp - yy) / sp                                    # 0 at the wall ... 1 at the near edge
        bay = np.clip(np.searchsorted(np.array(ribs[1:-1], np.float32), u), 0, len(ribs) - 2)
        b0 = np.array(ribs, np.float32)[bay]
        b1 = np.array(ribs, np.float32)[bay + 1]
        c = (u - (b0 + b1) / 2) / ((b1 - b0) / 2)                 # -1 .. 1 across the bay
        crown = np.sqrt(np.clip(1 - c * c, 0, 1))
        nz = K.noise(w, sp + 1, 14, 411) * 0.35
        tone = 2.7 + 1.0 * crown - 1.3 * np.clip(depth * 1.15, 0, 1) + nz
        course = ((u - b0) / 4.0) % 1.0 < 0.22                    # courses along the barrel (converging lines)
        dk = np.floor(depth * 16 + (bay % 2) * 0.5)
        header = (np.abs((depth * 16) - np.round(depth * 16)) < 0.06 * (1 + depth * 2)) & ((np.floor((u - b0) / 9.0) + dk) % 2 == 0)
        tone = tone - course * 0.55 - header * 0.45
        soot = np.clip(1 - np.hypot((xx - L.STOVE_PIPE_X) / 60.0, (yy - 96) / 46.0), 0, 1) * 1.2
        tone -= soot
        m = np.ones((sp + 1, w), bool)
        lay.put(m, x0, 0, 'W', tone + 0.4, hgt=(0.2 + 0.5 * crown), flat=False)
        bare = (K.noise(w, sp + 1, 30, 412, octaves=3) > 0.26) & (K.noise(w, sp + 1, 7, 414, octaves=2) > -0.1)
        lay.put(bare, x0, 0, 'K', np.clip(tone + 0.3, 1.0, 6.0), hgt=(0.2 + 0.5 * crown), flat=False)
        # lunettes: the wall continues up into the arch of each bay; brick arch ring along the curve
        for i in range(len(ribs) - 1):
            a, b = ribs[i], ribs[i + 1]
            cx_, half = (a + b) / 2.0, (b - a) / 2.0
            for x in range(max(x0, a), min(x1, b)):
                cc = (x + 0.5 - cx_) / half
                top = sp - rise * math.sqrt(max(0.0, 1 - cc * cc))
                ty = int(round(top))
                if ty < sp:
                    k = np.arange(ty, sp + 1, dtype=np.float32)
                    lay.put(np.ones((sp + 1 - ty, 1), bool), x, ty, 'W',
                            (3.4 + 0.25 * K.noise(1, sp + 1 - ty, 3, 413 + x)).reshape(-1, 1) - 0.3, hgt=0.12,
                            flat=False)
                for j in range(4):                                     # voussoir ring
                    yv = ty - 1 - j
                    if 0 <= yv:
                        jt = 2.6 + (0.9 if j == 0 else 0.0) - j * 0.25
                        radial = int(abs(cc) * 9 + 0.5) % 3 == 0 and j > 0
                        lay.px(x, yv, 'K', jt - (0.9 if radial else 0.0), hgt=0.6)
                lay.px(x, ty, 'W', 2.2, hgt=0.1)                           # shadow under the ring
        # ribs between the bays: projecting brick bands receding toward the viewer
        for rx in ribs:
            for y in range(0, sp + 1):
                fy = 1.0 + 0.6 * (sp - y) / sp
                cxr = vp + (rx - vp) * fy
                half = 5.0 * fy
                a_, b_ = int(round(cxr - half)), int(round(cxr + half))
                dep = (sp - y) / sp
                for x in range(max(x0, a_), min(x1, b_ + 1)):
                    k = int((y * 0.5 + (x - a_) * 0.0) / max(1.0, 2.2 * fy)) % 2
                    t_ = 3.4 - 1.9 * min(1.0, dep * 1.2) + (0.5 if x == a_ + 1 else 0.0) - k * 0.35
                    lay.px(x, y, 'K', t_, hgt=0.95)
                side = a_ - 1 if cxr > vp else b_ + 1
                if x0 <= side < x1:
                    lay.px(side, y, 'N', 1.0)
            for (cy, cw, ct) in ((sp + 1, 12, 3.2), (sp + 2, 10, 2.0)):          # corbel stone
                a_ = max(x0, rx - cw // 2)
                b_ = min(x1, rx + cw // 2)
                if b_ > a_:
                    lay.rect(a_, cy, b_ - a_, 1, 'C', ct, hgt=0.8)

    def high_window(self, gx0, gx1, lamp_outside=False):
        lay = self.lay
        y0, y1 = L.WIN_Y
        w = gx1 - gx0
        h = y1 - y0
        # deep splayed reveal in the lunette (arched head)
        rv = K.arch_mask(w + 12, h + 6, 5)
        lay.put(rv, gx0 - 6, y0 - 2, 'W', 2.0, hgt=-0.3)
        for i in range(7):
            lay.rect(gx0 - 6 + i // 2, y1 + 1 + i, w + 12 - i, 1, 'W', 4.4 - i * 0.3, hgt=0.4)
        lay.rect(gx0 - 2, y0, w + 4, h, 'I', 2.0, hgt=0.6)                  # iron frame
        lay.erase(gx0, y0 + 2, w, h - 3)
        self.glass[y0 + 2:y1 - 1, gx0:gx1] = True
        lay.rect(gx0 + w // 2 - 1, y0 + 2, 2, h - 3, 'I', 2.2, hgt=0.7)     # mullion
        lay.rect(gx0, y0 + h // 2, w, 1, 'I', 2.2, hgt=0.7)                 # transom
        for bx in range(gx0 + 4, gx1 - 1, 6):                               # bars outside
            for yy in range(y0 + 2, y1 - 1):
                if self.glass[yy, bx]:
                    lay.px(bx, yy, 'I', 1.2, hgt=0.4)
                    self.glass[yy, bx] = False
        rng = np.random.default_rng(gx0)
        for yy in range(y1 - 7, y1 - 1):                                    # frost on the panes
            for xx in range(gx0, gx1):
                if self.glass[yy, xx] and rng.random() < (yy - (y1 - 8)) * 0.15:
                    lay.px(xx, yy, 'S', 4.0 + rng.random(), hgt=0.05, unlit=True)
                    self.glass[yy, xx] = False
        self.windows.append((gx0, y0 + 2, gx1, y1 - 1))
        cx = (gx0 + gx1) / 2
        self.light('win_%d' % gx0, (cx, y0 + 16), 'cold', 0.55, 120, -10, pool=0.2, pool_dx=10, pool_depth=30,
                   pool_w=10, pool_spread=0.4)
        if lamp_outside:
            self.light('yard_lamp_%d' % gx0, (cx + 6, y0 - 4), 'warm', 0.5, 110, -16)

    def stairs(self):
        """Steep cellar stair from the office door (top left) down to the floor; the door ajar, warm light."""
        lay = self.lay
        top = 230
        dx0, dx1 = 0, 22
        # the landing wall: plank door ajar in a frame, light spilling out
        lay.rect(dx0, top - 58, dx1 + 4, 58, 'D', 1.6, hgt=0.5)            # frame / reveal
        lay.rect(dx0, top - 56, dx1, 56, 'L', 3.6, emis=True)               # lit office beyond the gap
        lay.rect(dx0 + 4, top - 56, dx1 - 8, 56, 'L', 4.4, emis=True)
        self.planks_v(dx0 + 8, dx1 + 2, top - 55, top, 'D', 2.4, width=5, seed=421)   # the leaf, ajar
        lay.rect(dx1 + 2, top - 56, 1, 56, 'D', 4.2, hgt=0.6)
        lay.rect(dx0 + 10, top - 30, 2, 2, 'L', 3.0, hgt=0.7)                # knob
        lay.rect(dx0, top, dx1 + 6, 3, 'D', 3.0, hgt=0.6)                    # landing nosing
        self.light('office_door', (10, top - 26), 'warm', 1.1, 150, 14)
        # stringer + steps (6 steps, run 44 px)
        n = 6
        x_a, x_b = dx1 + 2, L.STAIRS[1]
        rise = (FL - top) / n
        run = (x_b - x_a) / n
        for i in range(n):
            ty = int(round(top + (i + 1) * rise))
            tx = int(round(x_a + i * run))
            lay.rect(tx, ty - 2, int(round(run)) + 2, 2, 'D', 3.4 - i * 0.1, hgt=0.7)    # tread (worn nosing)
            lay.rect(tx, ty, int(round(run)) + 2, int(round(rise)) - 1, 'D', 1.8, hgt=0.4)  # riser
            lay.px(tx + int(run) // 2, ty - 2, 'D', 4.6, hgt=0.75)                         # worn spot
        for (x, y) in K.bres(x_a, top + 2, x_b + 2, FL + 1):                 # stringer
            lay.rect(x, y, 3, 3, 'D', 2.2, hgt=0.6)
        # dark space under the stair: broom, bucket
        for x in range(x_a, x_b):
            yy = int(top + (x - x_a) / (x_b - x_a) * (FL - top)) + 4
            if yy < FL:
                lay.rect(x, yy, 1, FL - yy, 'N', 1.6)
        lay.line(x_b - 30, FL - 2, x_b - 22, FL - 34, 'D', 3.0)              # broom handle
        lay.rect(x_b - 34, FL - 6, 9, 5, 'L', 1.4, hgt=0.4)                  # broom head (straw)
        lay.rect(x_b - 18, FL - 9, 8, 8, 'I', 2.6, hgt=0.6)                  # bucket
        lay.rect(x_b - 18, FL - 9, 8, 1, 'I', 4.0, hgt=0.7)
        # handrail (iron pipe on posts)
        for (x, y) in K.bres(x_a - 2, top - 26, x_b + 4, FL - 30):
            lay.rect(x, y, 1, 2, 'I', 3.2, hgt=0.9)
            lay.px(x, y, 'I', 4.6, hgt=1.0)
        for i in range(0, n + 1, 2):
            px_ = int(round(x_a + i * run))
            py_ = int(round(top + i * rise))
            lay.rect(px_, py_ - 26 + 2, 1, 26, 'I', 2.4, hgt=0.8)

    def shelves(self):
        lay = self.lay
        x0, x1 = L.SHELVES
        top = L.SHELF_TOP
        rng = np.random.default_rng(431)
        bays = [(x0, x0 + 70), (x0 + 70, x0 + 140), (x0 + 140, x1)]
        # back of the shelving (dark boards) + carcass
        self.planks_v(x0, x1, top, FL, 'D', 1.4, width=8, seed=432, hgt=0.1, var=0.15)
        years = ['1963', '1964', 'АРХИВ']
        spine_cols = [('G', 2.6), ('R', 2.0), ('D', 3.2), ('I', 3.0), ('K', 3.0), ('G', 3.2), ('D', 2.4)]
        for bi, (a, b) in enumerate(bays):
            for by in L.SHELF_BOARDS:
                lay.rect(a, by, b - a, 2, 'D', 3.6, hgt=0.7)
                lay.rect(a, by + 2, b - a, 1, 'D', 1.4, hgt=0.3)
                # books standing on the board
                x = a + 3
                gap_board = (bi == 1 and by == L.GAP_BOARD)
                while x < b - 4:
                    if gap_board and L.GAP[0] <= x < L.GAP[1]:
                        x = L.GAP[1]
                        continue
                    bw = int(rng.integers(4, 7))
                    if x + bw > b - 3:
                        break
                    bh = int(rng.integers(14, 18))
                    ramp, tone = spine_cols[int(rng.integers(0, len(spine_cols)))]
                    tone += rng.normal(0, 0.25)
                    lean = gap_board and L.GAP[0] - 6 <= x < L.GAP[0]
                    if lean:      # the last volume before the gap leans into it
                        for i in range(bh):
                            lay.rect(x + i // 5, by - 1 - i, bw, 1, ramp, tone, hgt=0.6)
                    else:
                        lay.rect(x, by - bh, bw, bh, ramp, tone, hgt=0.6)
                        lay.rect(x, by - bh, 1, bh, ramp, tone + 0.8, hgt=0.65)            # spine roundness
                        lay.rect(x + bw - 1, by - bh, 1, bh, ramp, tone - 0.9, hgt=0.5)
                        lay.rect(x + 1, by - bh + 3, bw - 2, 3, 'P', 3.6 + rng.normal(0, 0.3), hgt=0.62)  # label
                        lay.px(x + 1 + int(rng.integers(0, max(1, bw - 2))), by - bh + 4, 'I', 1.0)
                        lay.rect(x + 1, by - 4, bw - 2, 1, ramp, tone - 0.6, hgt=0.6)              # band
                    x += bw + (1 if rng.random() < 0.25 else 0)
                if by == L.SHELF_BOARDS[-1]:
                    pass
            # uprights
            for ux in (a, b - 3):
                lay.rect(ux, top, 3, FL - top, 'D', 3.0, hgt=0.8)
                lay.rect(ux, top, 1, FL - top, 'D', 4.0, hgt=0.85)
            # year plate on the top rail
            lay.rect(a + 3, top + 4, b - a - 6, 6, 'D', 2.8, hgt=0.6)
            K.text(lay, years[bi], (a + b) / 2, top + 5, 'P', 4.6, center=True, hgt=0.7)
        # the January gap: a clean, dust-free board where three volumes stood + Lev's slip of paper
        g0, g1 = L.GAP
        by = L.GAP_BOARD
        lay.rect(g0, by, g1 - g0, 1, 'D', 4.6, hgt=0.75)                       # dust-free outline
        lay.rect(g0, by - 17, g1 - g0, 17, 'N', 1.6, hgt=0.0)                  # shadowed back of the bay
        for (sx, sy) in ((g0 + 4, by - 2), (g0 + 5, by - 2), (g0 + 6, by - 2), (g0 + 7, by - 3), (g0 + 8, by - 3),
                         (g0 + 9, by - 3), (g0 + 10, by - 3), (g0 + 6, by - 3), (g0 + 7, by - 2), (g0 + 8, by - 2),
                         (g0 + 9, by - 2), (g0 + 10, by - 2), (g0 + 11, by - 2)):
            lay.px(sx, sy, 'P', 5.2, hgt=0.8)                                  # the slip, folded once
        lay.hline(g0 + 6, by - 3, 4, 'I', 1.6, hgt=0.8)                        # pencil writing on it
        # header board "ГРУЗОВЫЕ КНИГИ" over the middle bay
        a, b = bays[1]
        self.plate(a + 2, top - 12, b - a - 4, 10, ['ГРУЗОВЫЕ КНИГИ'], ramp='P', tone=4.4, ink=('I', 1.2),
                   border=('D', 1.6))
        lay.rect(x0, top - 2, x1 - x0, 3, 'D', 3.4, hgt=0.8)                   # cornice
        lay.rect(x0, top - 2, x1 - x0, 1, 'D', 4.6, hgt=0.9)
        # stamp rack right of the shelving (exp_stamps): a board with five hooks, stamps hanging, one hook empty
        rx, ry = L.STAMP_RACK
        lay.rect(rx, ry, 12, 28, 'D', 2.8, hgt=0.6)
        lay.rect(rx, ry, 12, 1, 'D', 4.0, hgt=0.7)
        for i in range(5):
            hy = ry + 3 + i * 5
            lay.px(rx + 2, hy, 'I', 4.2, hgt=0.8)
            if i != 2:
                lay.rect(rx + 3, hy, 4, 2, 'D', 3.8, hgt=0.85)               # wooden handle
                lay.rect(rx + 7, hy - 1, 2, 4, 'N', 1.4, hgt=0.7)            # rubber block
                lay.px(rx + 9, hy, 'R', 2.2, hgt=0.6)                         # ink on it
        lay.px(rx + 6, ry - 2, 'I', 3.6, hgt=0.9)                                # nail
        # hidden: a field mouse at a lump of sugar under the lowest shelf board (exp_sugar_mouse)
        mx_, my_ = 110, 284
        lay.rect(mx_, my_, 5, 3, 'C', 3.0, hgt=0.6)                               # body
        lay.px(mx_ + 5, my_ + 1, 'C', 3.4, hgt=0.6)                                # head
        lay.px(mx_ + 6, my_ + 1, 'N', 1.0)                                         # nose
        lay.px(mx_ + 4, my_ - 1, 'Y', 1.0, hgt=0.6)                                # ear
        lay.line(mx_ - 4, my_ + 3, mx_, my_ + 2, 'C', 2.0)                         # tail
        lay.rect(mx_ + 8, my_ + 1, 3, 3, 'P', 5.8, hgt=0.7)                        # sugar lump
        lay.px(mx_ + 8, my_ + 3, 'P', 4.6, hgt=0.6)

    def wall_extras(self):
        """A framed schematic of the Karsk railway junction over the tea table; the conduit with a switch."""
        lay = self.lay
        mx, my, mw, mh = 470, 158, 64, 40
        lay.rect(mx + 1, my + 1, mw + 4, mh + 4, 'N', 1.2)
        lay.rect(mx - 2, my - 2, mw + 4, mh + 4, 'D', 2.4, hgt=0.7)
        lay.rect(mx - 2, my - 2, mw + 4, 1, 'D', 3.8, hgt=0.75)
        lay.rect(mx, my, mw, mh, 'P', 4.2, hgt=0.5)
        rng = np.random.default_rng(481)
        pts = [(mx + 4, my + 30), (mx + 18, my + 24), (mx + 30, my + 21), (mx + 44, my + 14), (mx + 60, my + 6)]
        for (a, b) in zip(pts[:-1], pts[1:]):
            lay.line(a[0], a[1], b[0], b[1], 'I', 1.0)
        for (a, b) in (((mx + 30, my + 21), (mx + 58, my + 32)), ((mx + 18, my + 24), (mx + 8, my + 8)),
                       ((mx + 44, my + 14), (mx + 52, my + 36))):
            lay.line(a[0], a[1], b[0], b[1], 'I', 1.6)
        for p in pts:
            lay.rect(p[0] - 1, p[1] - 1, 3, 3, 'R', 2.4, hgt=0.55)
        K.text(lay, 'КАРСК', mx + 30, my + 26, 'R', 2.2, hgt=0.55)
        K.text(lay, 'СХЕМА', mx + 4, my + 33, 'I', 1.4, hgt=0.55)
        # conduit along the wall with porcelain insulators, a switch by the stair head
        lay.rect(0, 117, L.DOOR_WALL[0], 2, 'I', 2.4, hgt=0.6)
        lay.rect(0, 117, L.DOOR_WALL[0], 1, 'I', 3.4, hgt=0.65)
        for x in range(14, L.DOOR_WALL[0], 58):
            lay.rect(x, 115, 3, 5, 'P', 4.0, hgt=0.8)
        lay.rect(30, 119, 2, 55, 'I', 2.4, hgt=0.6)
        lay.rect(27, 172, 8, 9, 'I', 2.8, hgt=0.8)
        lay.rect(29, 175, 4, 2, 'P', 4.6, hgt=0.9)

    def tea_table(self):
        lay = self.lay
        a, b = L.SIDE_TABLE
        ty = 266
        lay.rect(a, ty, b - a, 3, 'D', 3.6, hgt=0.7)
        lay.rect(a, ty, b - a, 1, 'D', 4.8, hgt=0.8)
        for lx in (a + 2, b - 4):
            lay.rect(lx, ty + 3, 2, FL - ty - 3, 'D', 2.6, hgt=0.6)
        lay.rect(a + 2, ty + 12, b - a - 4, 1, 'D', 2.2, hgt=0.5)
        # samovar: bulbous nickel body, crown, chimney with the teapot on top, tap, tray
        s0, s1 = L.SAMOVAR
        cx = (s0 + s1) / 2
        lay.rect(s0 - 2, ty - 1, s1 - s0 + 4, 1, 'L', 2.6, hgt=0.7)              # tray
        for yy in range(ty - 24, ty - 1):
            k = (yy - (ty - 24)) / 23.0
            half = 4 + 4.2 * math.sin(math.pi * min(1.0, k * 1.05)) if k < 0.85 else 3.5
            lay.rect(int(cx - half), yy, int(2 * half), 1, 'L', 3.0, hgt=0.9)
            lay.px(int(cx - half), yy, 'L', 1.8, hgt=0.6)
            lay.px(int(cx - half) + 2, yy, 'L', 4.6, hgt=1.0)                    # highlight
        lay.rect(int(cx) - 5, ty - 26, 10, 2, 'L', 2.4, hgt=0.9)                 # crown
        lay.rect(int(cx) - 2, ty - 31, 4, 5, 'I', 2.6, hgt=0.9)                  # chimney
        # teapot (white porcelain with a red band) on the crown
        lay.ellipse(int(cx), ty - 34, 4, 3, 'P', 5.0, hgt=0.9)
        lay.rect(int(cx) - 3, ty - 34, 7, 1, 'R', 2.6, hgt=0.9)
        lay.px(int(cx) + 5, ty - 34, 'P', 4.0, hgt=0.8)
        lay.rect(int(cx) + 5, ty - 12, 3, 1, 'L', 3.6, hgt=0.9)                  # tap
        lay.px(int(cx) + 7, ty - 11, 'L', 2.6, hgt=0.8)
        for hx in (int(cx) - 7, int(cx) + 6):                                     # handles
            lay.rect(hx, ty - 20, 1, 3, 'N', 1.6, hgt=0.8)
        # two tea glasses in metal holders (one for a visitor who does not come)
        for gx in (L.GLASSES[0], L.GLASSES[0] + 5):
            lay.rect(gx, ty - 7, 4, 6, 'L', 2.4, hgt=0.7)                         # tea
            lay.rect(gx, ty - 8, 4, 1, 'S', 3.6, hgt=0.8)                         # glass rim
            lay.rect(gx, ty - 4, 4, 3, 'I', 3.4, hgt=0.8)                         # holder
            lay.px(gx + 4, ty - 6, 'I', 3.0, hgt=0.7)                             # holder handle
            lay.px(gx + 1, ty - 7, 'L', 4.4, hgt=0.75)
        # spoon in one glass
        lay.line(L.GLASSES[0] + 2, ty - 8, L.GLASSES[0] + 3, ty - 12, 'I', 4.2)

    def wall_clock(self):
        lay = self.lay
        cx, cy = L.CLOCK
        lay.rect(cx - 7, cy - 8, 14, 30, 'D', 2.4, hgt=0.7)                  # case with pendulum box
        lay.rect(cx - 7, cy - 8, 14, 1, 'D', 3.8, hgt=0.8)
        lay.put(K.disc(11), cx - 5, cy - 6, 'P', 4.8, hgt=0.8)
        lay.px(cx, cy - 1, 'I', 1.0)
        lay.line(cx, cy - 1, cx, cy - 4, 'I', 1.0)                           # minute hand on 8 -> 4.40
        lay.line(cx, cy - 1, cx - 3, cy + 1, 'I', 1.0)
        lay.line(cx, cy - 1, cx + 2, cy + 2, 'I', 1.6)                       # hour hand between 4 and 5
        lay.rect(cx - 4, cy + 7, 8, 13, 'N', 1.8, hgt=0.3)                   # pendulum window (decal swings)
        lay.rect(cx - 4, cy + 7, 8, 1, 'S', 3.0, hgt=0.5)

    def calendar(self, emblem=True):
        lay = self.lay
        x, y = L.CALENDAR
        w, h = 26, 30
        lay.rect(x + 1, y + 1, w, h, 'N', 1.4)                                 # shadow
        lay.rect(x, y, w, h, 'P', 4.6, hgt=0.4)
        lay.rect(x, y, w, 10, 'R', 2.2, hgt=0.45)                              # red header
        import env_karsk_emblems as KE
        kind = KE.kind_for('gw7', self.hist)
        m = KE.mask(kind)
        lay.put(m, x + 2, y + 1, 'L', 4.2, hgt=0.5, flat=True, crisp=True)
        K.text(lay, '1964', x + 10, y + 3, 'P', 5.6, hgt=0.5)
        K.text(lay, 'ФЕВ', x + w / 2, y + 12, 'I', 1.0, center=True, hgt=0.45)
        for r in range(4):                                                     # day grid
            for c in range(7):
                lay.px(x + 2 + c * 2 + c // 3, y + 19 + r * 3, 'I', 2.0 + (c == 6) * 0.6, hgt=0.4)
        lay.rect(x + 2 + 6 * 2 + 2, y + 19 + 2 * 3 - 1, 3, 3, 'R', 2.6)      # Sunday 16 ringed in red
        lay.px(x + w // 2, y - 2, 'I', 3.6, hgt=0.8)                           # nail

    def desk(self):
        lay = self.lay
        a, b = L.DESK
        ty = L.DESK_TOP
        # pedestals + top + modesty panel
        lay.rect(a, ty, b - a, 4, 'D', 3.6, hgt=0.8)
        lay.rect(a, ty, b - a, 1, 'D', 5.0, hgt=0.9)
        lay.rect(a - 1, ty + 3, b - a + 2, 1, 'D', 2.2, hgt=0.6)
        for (p0, p1) in ((a + 2, a + 40), (b - 40, b - 2)):
            K.grain(lay, p0, ty + 4, p1 - p0, FL - ty - 4, 'D', 2.8, seed=p0, amp=0.25, hgt=0.6)
            lay.rect(p0, ty + 4, 1, FL - ty - 4, 'D', 3.8, hgt=0.65)
            lay.rect(p1 - 1, ty + 4, 1, FL - ty - 4, 'D', 1.8, hgt=0.5)
            for dy in (ty + 6, ty + 13):                                        # drawers + brass pulls
                lay.rect(p0 + 2, dy, p1 - p0 - 4, 6, 'D', 3.0, hgt=0.65)
                lay.rect(p0 + 2, dy + 5, p1 - p0 - 4, 1, 'D', 1.8, hgt=0.5)
                lay.rect((p0 + p1) // 2 - 2, dy + 2, 4, 1, 'L', 3.8, hgt=0.8)
        lay.rect(a + 40, ty + 4, b - a - 80, 12, 'D', 2.0, hgt=0.4)            # modesty panel
        lay.rect(a + 40, ty + 16, b - a - 80, FL - ty - 16, 'N', 1.4)          # knee space (dark)
        # felt blotter, the January book open, papers
        lay.rect(a + 10, ty - 1, 64, 1, 'G', 2.4, hgt=0.85)
        b0, b1 = L.BOOK
        bw = b1 - b0
        lay.rect(b0, ty - 3, bw, 2, 'P', 4.6, hgt=0.9)                          # open pages (seen low)
        lay.rect(b0, ty - 4, bw // 2 - 1, 1, 'P', 5.2, hgt=0.95)
        lay.rect(b0 + bw // 2 + 1, ty - 4, bw // 2 - 1, 1, 'P', 5.0, hgt=0.95)
        lay.rect(b0 + bw // 2, ty - 4, 1, 3, 'P', 3.0, hgt=0.8)                # gutter
        lay.rect(b0 - 1, ty - 2, 1, 2, 'R', 2.2, hgt=0.8)                      # cloth binding
        lay.rect(b1, ty - 2, 1, 2, 'R', 2.2, hgt=0.8)
        for i in range(4):                                                      # three cut-outs seen as dark slots
            pass
        # two more January volumes stacked beside the book
        lay.rect(b1 + 3, ty - 6, 14, 3, 'R', 2.0, hgt=0.8)
        lay.rect(b1 + 2, ty - 3, 16, 3, 'G', 2.6, hgt=0.8)
        lay.rect(b1 + 4, ty - 5, 4, 1, 'P', 4.0, hgt=0.85)
        # Lev's own tea glass, the abacus (schoty), a pencil
        gx = 422
        lay.rect(gx, ty - 6, 4, 5, 'L', 2.4, hgt=0.7)
        lay.rect(gx, ty - 7, 4, 1, 'S', 3.4, hgt=0.8)
        lay.rect(gx, ty - 3, 4, 2, 'I', 3.2, hgt=0.8)
        ab0 = 397
        lay.rect(ab0, ty - 9, 22, 8, 'D', 2.2, hgt=0.7)                         # abacus frame
        lay.rect(ab0 + 1, ty - 8, 20, 6, 'N', 1.6, hgt=0.4)
        for r in range(3):
            lay.hline(ab0 + 1, ty - 7 + r * 2, 20, 'I', 2.6, hgt=0.5)
            for k in range(10):
                if (k + r * 3) % 10 < 6:
                    lay.px(ab0 + 2 + k * 2 + (k > 5) * 2 - (r == 1) * 1, ty - 7 + r * 2,
                           'L' if k % 5 else 'P', 3.6 if k % 5 else 4.4, hgt=0.8)
        lay.line(426, ty - 1, 432, ty - 2, 'L', 3.0)
        # the freight office's personnel card cabinet at the desk's left end: small oak, brass label frames
        c0, c1 = L.CARD_INDEX
        ct = 250
        lay.rect(c0, ct, c1 - c0, FL - ct, 'D', 3.0, hgt=0.8)
        lay.rect(c0, ct, c1 - c0, 1, 'D', 4.6, hgt=0.9)
        lay.rect(c0, ct, 1, FL - ct, 'D', 4.0, hgt=0.85)
        for r in range(3):
            for c in range(2):
                dx, dy = c0 + 2 + c * 11, ct + 3 + r * 11
                lay.rect(dx, dy, 10, 10, 'D', 3.4, hgt=0.85)
                lay.rect(dx, dy + 9, 10, 1, 'D', 2.0, hgt=0.7)
                lay.rect(dx + 3, dy + 2, 4, 3, 'L', 3.8, hgt=0.95)                 # brass label frame
                lay.rect(dx + 4, dy + 3, 2, 1, 'P', 5.0, hgt=0.95)
                lay.px(dx + 4, dy + 7, 'L', 4.4, hgt=0.95)                          # pull
        lay.rect(c0 + 2, ct - 3, 10, 3, 'P', 4.2, hgt=0.9)                           # cards waiting on top
        lay.rect(c0 + 3, ct - 4, 8, 1, 'P', 5.0, hgt=0.9)
        if self.cfg.get('plan_rolled', True):
            # the 1941 tunnel plan on linen, rolled and tied, lying across the card index
            p0, p1 = L.PLAN_ROLL
            for i in range(4):
                lay.rect(p0 - 2, ty - 19 + i, p1 - p0 + 2, 1, 'P', 4.6 - abs(i - 1.2) * 0.7, hgt=0.9)
            lay.rect(p0 - 3, ty - 19, 1, 4, 'P', 3.0, hgt=0.8)
            lay.rect(p0 + 8, ty - 19, 1, 4, 'R', 2.2, hgt=0.95)                  # string
        # chair, pushed back
        cx = 424
        lay.rect(cx, 248, 2, FL - 248, 'D', 2.6, hgt=0.6)                       # back post
        lay.rect(cx, 248, 14, 2, 'D', 3.2, hgt=0.7)
        lay.rect(cx, 268, 16, 3, 'D', 3.4, hgt=0.7)                             # seat
        lay.rect(cx + 14, 271, 2, FL - 271, 'D', 2.4, hgt=0.6)
        lay.rect(cx + 2, 254, 10, 1, 'D', 2.6)
        # green-shaded lamp
        lx, ly = L.GREEN_LAMP
        lay.rect(lx - 6, ty - 2, 12, 2, 'L', 3.0, hgt=0.9)                       # brass base
        lay.rect(lx - 1, ly + 2, 2, ty - 2 - ly - 2, 'L', 3.4, hgt=0.9)          # stem
        for yy in range(ly - 8, ly + 1):
            k = (yy - (ly - 8)) / 8.0
            half = int(round(4 + 7 * k))
            lay.rect(lx - half, yy, 2 * half, 1, 'G', 3.6 - 1.2 * k, hgt=1.0)
            lay.px(lx - half + 1, yy, 'G', 5.4, hgt=1.0)                         # glass sheen
        lay.rect(lx - 11, ly + 1, 22, 1, 'L', 5.0, emis=True)                    # bulb glow under the shade
        lay.rect(lx - 2, ly - 10, 4, 2, 'L', 3.4, hgt=1.0)                        # brass cap
        self.light('green_lamp', (lx, ly + 4), 'warm', 2.3, 180, 10, cone=(0.0, 1.0, -0.1), pool=0.55,
                   pool_depth=40, pool_w=26, pool_spread=0.7)
        self.light('green_shade', (lx, ly - 6), 'warm', 0.25, 50, 4)
        # Lev's photo leaning against the lamp foot (exp_lev_photo): a young woman holding a leaflet
        px, py = L.PHOTO
        for i in range(11):
            lay.rect(px + i // 6, py + i, 9, 1, 'D', 1.8, hgt=0.8)                  # frame, leaning back
        lay.rect(px + 2, py + 2, 5, 7, 'P', 3.6, hgt=0.75)
        lay.rect(px + 3, py + 3, 3, 3, 'P', 2.2, hgt=0.75)                         # her face
        lay.rect(px + 3, py + 6, 3, 2, 'P', 5.0, hgt=0.75)                         # the leaflet
        # dust motes / desk light: the paper on the desk catches the lamp
        lay.rect(a + 4, ty - 1, 6, 1, 'P', 4.6, hgt=0.85)

    def lightbox(self):
        lay = self.lay
        a, b = L.LIGHTBOX
        ty = 268
        lay.rect(a - 2, ty, b - a + 4, 3, 'D', 3.4, hgt=0.7)                   # small table
        for lx in (a, b - 2):
            lay.rect(lx, ty + 3, 2, FL - ty - 3, 'D', 2.4, hgt=0.6)
        lay.rect(a + 2, ty + 10, b - a - 4, 1, 'D', 2.0)
        # the box: wood sides, frosted glass on top (glowing), the signal lamp's round lens in front
        lay.rect(a + 2, ty - 14, b - a - 4, 14, 'D', 2.8, hgt=0.75)
        lay.rect(a + 2, ty - 14, 1, 14, 'D', 3.8, hgt=0.8)
        lay.rect(a + 3, ty - 16, b - a - 6, 2, 'P', 5.6, emis=True)             # frosted glass (lit)
        lens = K.disc(9)
        lay.put(lens, (a + b) // 2 - 4, ty - 12, 'I', 2.0, hgt=0.9)
        lay.put(K.disc(7), (a + b) // 2 - 3, ty - 11, 'L', 4.6, emis=True)
        lay.put(K.disc(3), (a + b) // 2 - 1, ty - 9, 'P', 6.0, emis=True)
        # carbon copies on the glass (blue-black sheets, the traces light through)
        for (sx, sw, sy) in ((a + 4, 14, ty - 17), (a + 16, 15, ty - 18), (a + 26, 12, ty - 17)):
            lay.rect(sx, sy, sw, 1, 'I', 2.6, hgt=0.95)
            lay.rect(sx + 2, sy, sw - 5, 1, 'S', 3.0, emis=True)
        lay.line(b - 4, ty - 6, b + 6, FL - 1, 'N', 1.0)                         # cable to the wall
        self.light('lightbox', ((a + b) / 2, ty - 18), 'warm', 1.0, 90, 4)
        self.light('lightbox_lens', ((a + b) / 2, ty - 8), 'warm', 0.6, 60, 6)

    def stove(self):
        lay = self.lay
        a, b = L.STOVE
        top, bot = 246, 282
        # body: riveted iron box on legs, door with vent slits (fire flicker strip on top)
        lay.rect(a + 2, top, b - a - 4, bot - top, 'I', 2.6, hgt=0.9)
        lay.rect(a + 2, top, 2, bot - top, 'I', 3.8, hgt=1.0)
        lay.rect(b - 4, top, 2, bot - top, 'I', 1.6, hgt=0.7)
        lay.rect(a, top - 3, b - a, 3, 'I', 3.4, hgt=1.0)                        # top plate
        lay.rect(a, top - 3, b - a, 1, 'I', 4.6, hgt=1.0)
        K.rivets(lay, a + 4, b - 4, top + 2, 4, 'I', 4.2, 1.2)
        K.rivets(lay, a + 4, b - 4, bot - 3, 4, 'I', 4.2, 1.2)
        dx, dy = a + 8, top + 10
        lay.rect(dx, dy, 18, 14, 'I', 1.8, hgt=0.9)                               # door
        lay.rect(dx, dy, 18, 1, 'I', 3.6, hgt=1.0)
        for k in range(4):                                                         # vent slits (glow)
            lay.rect(dx + 3 + k * 4, dy + 4, 2, 6, 'L', 4.2, emis=True)
            lay.px(dx + 3 + k * 4, dy + 9, 'R', 3.0, emis=True)
        lay.rect(dx + 15, dy + 6, 3, 2, 'I', 4.0, hgt=1.0)                        # handle
        lay.rect(a + 2, bot, b - a - 4, 2, 'R', 2.0, emis=True)                   # glow under the ash pan
        for lx in (a + 3, b - 6):
            lay.rect(lx, bot, 3, FL - bot, 'I', 2.0, hgt=0.7)
        # kettle
        lay.ellipse(a + 26, top - 7, 6, 4, 'I', 3.4, hgt=1.0)
        lay.rect(a + 32, top - 9, 4, 1, 'I', 3.0, hgt=1.0)
        lay.line(a + 21, top - 11, a + 31, top - 11, 'N', 1.6)
        # pipe up through the vault (soot collar where it enters the brick)
        px = L.STOVE_PIPE_X
        K.cyl(lay, px - 3, 96, 6, top - 3 - 96, 'I', 2.4, hgt=1.0, axis='v')
        for jy in range(110, top - 3, 26):
            lay.rect(px - 3, jy, 6, 1, 'I', 3.8, hgt=1.0)
        lay.rect(px - 6, 92, 12, 4, 'I', 3.0, hgt=0.9)                             # tin rosette
        lay.rect(px - 7, 88, 14, 4, 'N', 1.0)                                      # into the vault
        # a pair of felt boots (valenki) drying against the stove, firewood
        for k, bx_ in enumerate((b + 1, b + 8)):
            lay.rect(bx_, FL - 18, 6, 15, 'C', 3.4 - k * 0.4, hgt=0.7)              # shaft
            lay.rect(bx_, FL - 4, 9, 4, 'C', 3.0 - k * 0.4, hgt=0.7)                # foot
            lay.rect(bx_, FL - 18, 6, 1, 'C', 4.4, hgt=0.8)
            lay.rect(bx_, FL - 2, 9, 2, 'N', 1.8, hgt=0.6)                          # galosh
        lay.line(b + 16, FL - 24, b + 13, FL - 2, 'I', 3.0)                         # poker
        for k in range(4):
            lay.rect(a - 14, FL - 4 - k * 3, 12, 3, 'D', 3.0 + (k % 2) * 0.6, hgt=0.6)
            lay.px(a - 14, FL - 3 - k * 3, 'D', 4.6, hgt=0.7)
        self.light('stove', ((a + b) / 2, top + 18), 'warm', 1.1, 120, 6, pool=0.5, pool_depth=26, pool_w=14,
                   pool_spread=0.6)

    def iron_door(self):
        lay = self.lay
        a, b = L.DOOR
        y0, y1 = L.DOOR_Y
        l0, l1 = L.DOOR_LEAF
        # concrete frame (1941 shelter door), the sign above
        lay.rect(a, y0 - 6, b - a, y1 - y0 + 6, 'C', 3.4, hgt=0.6)
        lay.rect(a, y0 - 6, b - a, 1, 'C', 4.6, hgt=0.7)
        lay.rect(a + 2, y0 - 4, b - a - 4, y1 - y0 + 4, 'C', 2.6, hgt=0.4)
        if self.cfg.get('door_open', False):
            # the opening: cold dark, the first metres of the tunnel, polished rails, a far cage lamp
            lay.rect(l0, y0, l1 - l0, y1 - y0, 'N', 0.4, hgt=-0.5)
            for yy in range(y0, y1):
                k = (yy - y0) / (y1 - y0)
                lay.rect(l0 + 2, yy, l1 - l0 - 4, 1, 'C', 0.6 + 0.6 * k, hgt=-0.5)
            vx = (l0 + l1) // 2
            lay.rect(vx - 10, y1 - 10, 20, 10, 'C', 1.4, hgt=-0.4)                  # floor beyond
            lay.line(vx - 9, y1 - 1, vx - 2, y1 - 9, 'S', 3.0)                       # rails converging
            lay.line(vx + 9, y1 - 1, vx + 2, y1 - 9, 'S', 3.0)
            lay.rect(vx - 1, y0 + 14, 3, 3, 'L', 4.4, emis=True)                     # far cage lamp
            lay.px(vx, y0 + 12, 'L', 3.0, emis=True)
            # the leaf swung open toward the viewer (hinged left), seen almost edge-on
            for yy in range(y0 - 2, y1 + 2):
                lay.rect(a - 6, yy, 10, 1, 'G', 2.2, hgt=0.9)
                lay.px(a - 6, yy, 'G', 1.0, hgt=0.6)
                lay.px(a + 3, yy, 'G', 3.4, hgt=1.0)
            for cy in (y0 + 10, y0 + 28, y0 + 46):
                lay.rect(a - 8, cy, 4, 3, 'I', 3.6, hgt=1.0)                         # clamp levers
            # cold air: a little light from the tunnel on the floor
            self.light('door_cold', (vx, y1 - 6), 'cold', 0.6, 70, 6)
        else:
            lw = l1 - l0
            lay.rect(l0, y0, lw, y1 - y0, 'G', 2.4, hgt=0.9)
            lay.rect(l0, y0, lw, 2, 'G', 3.6, hgt=1.0)
            lay.rect(l0, y0, 2, y1 - y0, 'G', 3.2, hgt=1.0)
            lay.rect(l1 - 2, y0, 2, y1 - y0, 'G', 1.4, hgt=0.7)
            lay.rect(l0 + 4, y0 + 4, lw - 8, y1 - y0 - 8, 'G', 2.0, hgt=0.8)      # recessed panel
            K.rivets(lay, l0 + 3, l1 - 2, y0 + 2, 4, 'G', 4.0, 1.0)
            K.rivets(lay, l0 + 3, l1 - 2, y1 - 3, 4, 'G', 4.0, 1.0)
            for cy in (y0 + 10, y0 + 28, y0 + 46):                                # four lever clamps
                lay.rect(l1 - 6, cy, 8, 3, 'I', 3.4, hgt=1.0)
                lay.px(l1 + 1, cy + 1, 'I', 4.8, hgt=1.0)
                lay.rect(l1 - 6, cy + 3, 8, 1, 'N', 1.2)
            lay.rect(l0 + 2, y0 + 26, 4, 6, 'I', 3.0, hgt=1.0)                    # hinges
            rng = np.random.default_rng(611)
            for _ in range(40):                                                    # rust blooms
                rx, ry = int(rng.integers(l0 + 2, l1 - 2)), int(rng.integers(y0 + 2, y1 - 2))
                lay.px(rx, ry, 'K', 2.6 + rng.random(), hgt=0.85)
                if rng.random() < 0.4:
                    lay.px(rx, ry + 1, 'K', 2.2, hgt=0.85)
            # a peephole with a sliding cover, the threshold
            lay.put(K.disc(4), (l0 + l1) // 2 - 2, y0 + 14, 'I', 1.4, hgt=0.9)
        lay.rect(a, y1 - 1, b - a, 2, 'I', 3.8, hgt=0.6)                           # steel threshold
        # sign above: Бомбоубежище - Служебный тоннель №3 (1941, enamel, chipped)
        self.plate(a - 30, L.SIGN_Y + 4, 60, 26, [('БОМБОУБЕЖИЩЕ', ('R', 2.4)), 'СЛУЖЕБНЫЙ', 'ТОННЕЛЬ №3'],
                   ramp='P', tone=4.8, ink=('I', 1.0), border=('R', 2.0), wear=0.08, seed=621)
        # a painted arrow to the shelter on the wall beside the door
        K.worn_text(lay, '→', a - 18, y0 + 10, 'P', 4.6, wear=0.15, seed=622, hgt=0.3)
        lay.rect(a - 24, y0 + 12, 6, 1, 'P', 4.2, hgt=0.3)

    def cellar_floor(self):
        """Worn brick pavers in perspective, the path stairs -> desk -> door, a rag runner, melt water."""
        lay = self.lay
        x0, x1 = L.CELLAR[0], L.DOOR_WALL[0]
        w = x1 - x0
        hh = H - FL
        rows = [0, 3, 6, 10, 15, 21, 28, 36, 45, 55, 66, 72]
        nz = K.noise(w, hh, 12, 451) * 0.4
        lay.put(np.ones((hh, w), bool), x0, FL, 'K', 2.6 + nz, hgt=0.0, flat=False)
        vp = (x0 + x1) / 2
        rng = np.random.default_rng(452)
        for i in range(len(rows) - 1):
            ra, rb = FL + rows[i], min(H, FL + rows[i + 1])
            lay.rect(x0, ra, w, 1, 'K', 1.2)
            fr = (ra + 0.5 - L.HORIZON) / (FL - L.HORIZON)
            off = (i % 2) * 9
            for u in range(int(x0 - 600), int(x1 + 600), 18):
                xx = int(round(vp + (u + off - vp) * fr))
                if x0 <= xx < x1:
                    lay.rect(xx, ra + 1, 1, rb - ra - 1, 'K', 1.4)
            for u in range(int(x0 - 600), int(x1 + 600), 18):              # per-brick tone
                xa = int(round(vp + (u + off - vp) * fr)) + 1
                xb = int(round(vp + (u + off + 18 - vp) * fr))
                if xb > xa and xa < x1 and xb > x0:
                    lay.shade_rect(max(x0, xa), ra + 1, min(x1, xb) - max(x0, xa), rb - ra - 1,
                                   float(rng.normal(0, 0.22)))
        # polished path (stairs -> desk -> door): lighter, smoother
        path = np.zeros((hh, w), np.float32)
        for xx in range(w):
            cy = 12 + 3 * math.sin(xx / 90.0)
            path[:, xx] = np.clip(1 - np.abs(np.arange(hh) - cy) / 9.0, 0, 1)
        lay.amb_field(np.pad(path * 0.45, ((FL, 0), (0, W - w))))
        # rag runner in front of the desk (woven stripes)
        for yy in range(FL + 4, FL + 15):
            k = yy - FL - 4
            a_ = 330 - k // 2
            b_ = 420 + k // 2
            ramp, t_ = (('R', 2.2) if (k // 2) % 3 == 0 else (('G', 2.6) if (k // 2) % 3 == 1 else ('D', 3.0)))
            lay.rect(a_, yy, b_ - a_, 1, ramp, t_, hgt=0.1)
            if k % 2 == 0:
                for fx_ in range(a_, b_, 3):
                    lay.px(fx_, yy, ramp, t_ + 0.6, hgt=0.12)
        for fx_ in range(330, 421, 3):                                         # fringes
            lay.px(fx_, FL + 3, 'P', 3.0)
        # melt water from boots at the stair foot
        for (cx, cy, rx, ry) in ((54, FL + 10, 10, 2), (76, FL + 16, 7, 2), (40, FL + 18, 6, 1)):
            m, mx, my = lay.ellipse_mask(cx, cy, rx, ry)
            lay.put(m, mx, my, 'S', 1.6, hgt=-0.05, flat=False)
            lay.px(cx - rx // 2, cy, 'S', 4.0)

    def door_wall(self):
        """The thick wall between cellar and tunnel, in section (brick ends, dark poche)."""
        lay = self.lay
        a, b = L.DOOR_WALL
        t = K.bricks(lay, a, 0, b - a, FL, 'K', 0.0, seed=461, course=4, length=6, joint=-0.8, var=0.3)
        lay.put(np.ones((FL, b - a), bool), a, 0, 'K', 1.8 + t, flat=False, hgt=0.3)
        lay.rect(a, 0, 1, FL, 'K', 3.4, hgt=0.4)                                  # cut edge (lit side)
        lay.rect(b - 1, 0, 1, FL, 'N', 1.0)
        lay.rect(a, FL, b - a, H - FL, 'C', 2.0, hgt=0.0)                          # threshold slab
        lay.rect(a, FL, b - a, 1, 'C', 3.2)

    # ================================================================== ambient + lights
    def ambient(self):
        lay = self.lay
        f = np.zeros((H, W), np.float32)
        ys = np.arange(H, dtype=np.float32)[:, None]
        xs = np.arange(W, dtype=np.float32)[None, :]
        cell = (xs < L.DOOR_WALL[0]).astype(np.float32)
        f += -0.9 * np.clip((70 - ys) / 70, 0, 1) * cell                          # cellar vault crown darkens
        f += -0.6 * np.clip((40 - xs) / 40, 0, 1) * np.clip((ys - 120) / 80, 0, 1) * 0.0
        tun = ((xs >= L.TUNNEL[0]) & (xs < L.TUNNEL[1])).astype(np.float32)
        f += -0.5 * tun * np.clip((ys - 150) / 140, 0, 1) * 0.0
        sid = (xs >= L.SIDING[0]).astype(np.float32)
        f += -0.8 * sid * np.clip((100 - ys) / 70, 0, 1)
        f += -0.7 * np.clip((ys - 324) / 36, 0, 1)                                 # floor toward the viewer
        f[lay.emis] = 0
        lay.amb_field(f)

    def build(self):
        import env_c4_tunnels_siding as SD
        self.poche()
        # cellar
        self.cellar_wall()
        self.cellar_vault()
        self.high_window(*L.WINDOWS_C[0])
        self.high_window(*L.WINDOWS_C[1], lamp_outside=True)
        self.stairs()
        self.shelves()
        self.wall_extras()
        self.tea_table()
        self.wall_clock()
        self.calendar()
        self.desk()
        self.lightbox()
        self.stove()
        self.iron_door()
        self.cellar_floor()
        self.door_wall()
        # tunnel + siding
        SD.tunnel(self)
        SD.siding(self)
        SD.wagon(self)
        SD.floors(self)
        self.ambient()
        # the hanging lamps are decals; their light is baked here
        self.light('hang_lamp', (L.HANG_LAMP[0], L.HANG_LAMP[1] + 3), 'warm', 0.9, 150, 18, cone=(0.0, 1.0, -0.2),
                   pool=0.35, pool_depth=36, pool_w=18, pool_spread=0.6)
        self.light('bulb_wagon', (L.BULB[0], L.BULB[1] + 3), 'white', 1.6, 210, 26, pool=0.6, pool_depth=46,
                   pool_w=30, pool_spread=0.8)
        return self.lay

    def all_lights(self):
        return self.lights
