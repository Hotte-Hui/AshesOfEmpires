"""env_c4_annex_hall -- the main layer of L_C4_AnnexB 'Nebenstelle Sued der Zentralen Erfassungsstelle'.

Underground, ~6.00, no daylight: flat fluorescent green-white over concrete, steel and oil paint (hue world
'hall' of env_c4_annex_kit), one warm lamp at the counter.  The layer spans world x 846..1920 (placed at
pos [846, 0]); left -> right: the cut wall of the shaft and the ladder niche (Konrad's way down from S 2), the
machine room behind a mesh grille with the two fans the column breathes through, the card hall (steel cabinets
to the ceiling, sliding ladders, the drawer bank Sued 1..12 -- Sued 3 always a finger's width open with Brandt's card
standing up, the hidden find exp_brandt_card), the framed ventilation plan (Blatt 3, gez. K. Adler),
the pneumatic-tube station, the waiting bench, the counter 'Auskunft . Abgleich' with the typists' room behind
glass, the steel door to the Staatspolizei corridor.
Story states (cfg): 'drawer' (Sued 8 pulled out, red C-17 tabs), 'tube' (capsule opened, the slip taken),
'form' (the form laid out on the counter), 'hist' (historical insignia at the two official plates).
"""
from __future__ import annotations

import math

import numpy as np

import env_c4_annex_kit as K
import env_c4_annex_layout as L
import pg

X0 = L.SEAM
W = L.WORLD_W - L.SEAM
H = L.WORLD_H
FL = L.FLOOR


def lx(x):
    """world x -> layer x"""
    return int(x) - X0


class Hall:
    def __init__(self, cfg: dict | None = None):
        self.cfg = cfg or {}
        self.lay = K.tlayer(W, H, 'annex', 'hall')
        self.lights: list[dict] = []
        self.hist = bool(self.cfg.get('hist', False))

    def light(self, name, pos, kind, energy, radius, height=24, **kw):
        """pos in WORLD coordinates (the bake converts)."""
        d = {'name': name, 'pos': (float(pos[0]), float(pos[1])), 'kind': kind, 'energy': energy,
             'radius': radius, 'height': height}
        d.update(kw)
        self.lights.append(d)
        return d

    # ================================================================== shell: wall, ceiling, services
    def shell(self):
        lay = self.lay
        nz = pg.value_noise(W, H, 9, 501, octaves=3)
        stain = np.repeat(pg.value_noise(W, 6, 2, 502, octaves=2), 1, axis=0)
        # upper wall: pale oil-green paint over board-formed concrete, panel joints, water streaks
        t = 3.1 + (nz[:FL] - 0.5) * 0.45
        ys = np.arange(FL)[:, None]
        streaks = (stain[2][None, :] > 0.62) & (ys > 60) & (ys < L.DADO_Y)
        t = t - streaks * (0.5 * np.clip((ys - 60) / 120.0, 0, 1))
        lay.put(np.ones((FL, W), bool), 0, 0, 'G', t.astype(np.float32), flat=False, hgt=0.1)
        for x in range(0, W, 64):
            lay.vline(x, 40, L.DADO_Y - 40, 'G', 2.4, hgt=-0.2)
        for y in (120,):
            lay.hline(0, y, W, 'G', 2.6, hgt=-0.2)
        # dado (darker oil paint), its line, the skirting
        dt = 1.9 + (nz[L.DADO_Y:FL] - 0.5) * 0.35
        lay.put(np.ones((FL - L.DADO_Y, W), bool), 0, L.DADO_Y, 'G', dt.astype(np.float32), flat=False, hgt=0.12)
        lay.hline(0, L.DADO_Y, W, 'G', 0.9, hgt=0.3)
        lay.hline(0, L.DADO_Y + 1, W, 'G', 3.4, hgt=0.3)
        lay.rect(0, FL - 4, W, 4, 'I', 1.6, hgt=0.4)
        lay.hline(0, FL - 4, W, 'I', 2.8, hgt=0.5)
        # ceiling slab (board marks), downstand beams
        for y in range(0, L.CEIL_Y):
            for x in range(W):
                lay.px(x, y, 'C', 2.1 + (y % 4 == 0) * -0.4 + (nz[y, x] - 0.5) * 0.4 + y * 0.02, hgt=0.1)
        lay.hline(0, L.CEIL_Y, W, 'C', 1.2)
        for bx in L.BEAMS:
            b = lx(bx) - 8
            lay.rect(b, 0, 16, 42, 'C', 2.8, hgt=0.8)
            lay.vline(b, 0, 42, 'C', 4.0, hgt=0.9)
            lay.vline(b + 15, 0, 42, 'C', 1.6, hgt=0.5)
            lay.hline(b, 41, 16, 'C', 1.4)

    def services(self):
        lay = self.lay
        # main air duct from the machine room along the hall
        d0, d1 = lx(1056), lx(1664)
        y0, y1 = L.DUCT_Y
        lay.rect(d0, y0, d1 - d0, y1 - y0, 'S', 3.6, hgt=0.7)
        lay.hline(d0, y0, d1 - d0, 'S', 5.2, hgt=0.9)
        lay.hline(d0, y1 - 1, d1 - d0, 'S', 1.8, hgt=0.4)
        for x in range(d0, d1, 40):
            lay.rect(x, y0 - 1, 2, y1 - y0 + 2, 'S', 2.4, hgt=0.9)
            for yy in range(y0 + 2, y1 - 1, 4):
                lay.px(x + 1, yy, 'S', 5.0)
        for x in range(d0 + 70, d1 - 20, 120):
            lay.rect(x, y1 - 7, 18, 6, 'S', 1.6)
            for k in range(0, 18, 2):
                lay.vline(x + k, y1 - 7, 6, 'S', 3.0)
        # the two pneumatic tubes from the Staatspolizei corridor to the station, a glass inspection length
        t0, t1 = L.TUBES_Y
        sx = lx((L.TUBE_ST[0] + L.TUBE_ST[1]) // 2)
        for k, ty in enumerate((t0, t0 + 4)):
            xs = sx - 8 + k * 16
            lay.rect(xs, ty, W - xs, 3, 'S', 4.0, hgt=0.6)
            lay.hline(xs, ty, W - xs, 'S', 5.6, hgt=0.8)
            lay.hline(xs, ty + 2, W - xs, 'S', 2.2)
            # the bend down into the station
            for y in range(ty, L.TUBE_ST_Y[0]):
                lay.rect(xs, y, 3, 1, 'S', 4.0, hgt=0.6)
                lay.px(xs, y, 'S', 5.6)
            for x in range(xs + 24, W, 70):
                lay.rect(x, ty - 1, 2, 5, 'S', 2.6, hgt=0.8)
        g0, g1 = lx(1700), lx(1760)
        lay.rect(g0, t0 - 1, g1 - g0, 10, 'S', 2.0)
        lay.rect(g0 + 2, t0, g1 - g0 - 4, 8, 'G', 3.8, hgt=0.3)
        lay.hline(g0 + 2, t0, g1 - g0 - 4, 'G', 5.0)
        lay.rect(g0 - 2, t0 - 2, 3, 12, 'S', 4.2, hgt=0.9)
        lay.rect(g1 - 1, t0 - 2, 3, 12, 'S', 4.2, hgt=0.9)
        # cable tray
        y = L.TRAY_Y[0]
        lay.rect(0, y, W, 3, 'I', 2.0)
        lay.hline(0, y, W, 'S', 3.2)
        for x in range(0, W, 9):
            lay.px(x, y + 1, 'S', 2.6)

    def fixtures(self):
        lay = self.lay
        fy = L.FIXTURE_Y
        for i, fx in enumerate(L.FIXTURES):
            x = lx(fx) - 20
            for rx in (x + 6, x + 33):
                lay.vline(rx, L.TRAY_Y[1], fy - L.TRAY_Y[1], 'I', 1.8)
            lay.rect(x, fy, 40, 3, 'S', 3.2, hgt=0.7)
            lay.hline(x, fy, 40, 'S', 4.8, hgt=0.8)
            lay.rect(x + 1, fy + 3, 38, 2, 'G', 5.0, emis=True)
            lay.hline(x + 2, fy + 5, 36, 'G', 4.0, emis=True)
            self.light('tube_%d' % i, (fx, fy + 6), 'cold', 0.9, 230, height=34, pool=0.45, pool_w=26,
                       pool_depth=50, pool_spread=0.8)

    # ================================================================== the shaft: cut wall, ladder niche
    def shaft(self):
        lay = self.lay
        p0, p1 = lx(L.PIER[0]), lx(L.PIER[1])
        # the cut wall in section: poche with the draughtsman's 45-degree hatch
        lay.rect(p0, 0, p1 - p0, H, 'N', 1.1, hgt=0.6)
        for y in range(0, H):
            for x in range(p0, p1):
                if (x + y) % 6 == 0:
                    lay.px(x, y, 'N', 2.0, hgt=0.6)
        lay.vline(p1 - 1, 0, FL, 'C', 3.2, hgt=0.9)
        lay.vline(p1 - 2, 0, FL, 'C', 2.0, hgt=0.7)
        # the niche: recessed, darker concrete; the shaft opens through the slab
        s0, s1 = lx(L.SHAFT[0]), lx(L.SHAFT[1])
        nz = pg.value_noise(s1 - s0, FL, 6, 77, octaves=2)
        for y in range(0, FL):
            for x in range(s0, s1):
                lay.px(x, y, 'C', 1.9 + (nz[y, x - s0] - 0.5) * 0.6 + (y % 24 == 0) * -0.5, hgt=-0.3)
        lay.vline(s0, 0, FL, 'C', 1.2, hgt=-0.4)
        lay.vline(s1 - 1, 0, FL, 'C', 3.4, hgt=0.4)
        for y in range(0, L.CEIL_Y + 16):
            k = y / (L.CEIL_Y + 16)
            lay.rect(s0 + 1, y, s1 - s0 - 2, 1, 'D', 2.6 - k * 1.8 if y < 10 else 0.6 + (1 - k) * 0.8, hgt=-0.5)
        lay.rect(s0 - 3, L.CEIL_Y + 14, s1 - s0 + 6, 3, 'C', 3.6, hgt=0.8)        # collar of the shaft
        # iron ladder: two rails, rungs every 8 px, wall brackets
        a0, a1 = lx(L.LADDER[0]), lx(L.LADDER[1])
        for rx in (a0, a1 - 2):
            lay.rect(rx, 0, 2, FL, 'S', 3.4, hgt=0.8)
            lay.vline(rx, 0, FL, 'S', 4.8, hgt=0.9)
        for y in range(6, FL - 2, 8):
            lay.rect(a0 + 2, y, a1 - a0 - 4, 1, 'S', 4.4, hgt=0.7)
            lay.rect(a0 + 2, y + 1, a1 - a0 - 4, 1, 'S', 1.6, hgt=0.3)
        for y in (60, 150, 240):
            lay.rect(a0 - 3, y, 3, 2, 'S', 2.6)
            lay.rect(a1, y, 3, 2, 'S', 2.6)
        # caged bulkhead lamp (warm, old) and the stencils
        bx, by = s1 - 7, 118
        lay.rect(bx - 3, by - 4, 7, 9, 'S', 2.0, hgt=0.6)
        lay.rect(bx - 2, by - 3, 5, 7, 'L', 4.6, emis=True)
        for k in range(-3, 4, 2):
            lay.vline(bx + k, by - 4, 9, 'I', 1.4)
        self.light('shaft_bulkhead', (L.SHAFT[1] - 7, by), 'warm', 0.7, 90, height=10, pool=0.3, pool_w=10,
                   pool_depth=24)
        K.text(lay, 'S 2', s0 + 26, 160, 'R', 3.2)
        lay.line(s0 + 30, 152, s0 + 30, 140, 'R', 3.2)
        lay.line(s0 + 28, 142, s0 + 30, 140, 'R', 3.2)
        lay.line(s0 + 32, 142, s0 + 30, 140, 'R', 3.2)
        # floor grate at the foot of the ladder
        lay.rect(a0 - 4, FL - 3, a1 - a0 + 8, 3, 'S', 2.2, hgt=0.4)

    # ================================================================== machine room behind the grille
    def machine_room(self):
        lay = self.lay
        m0, m1 = lx(L.MACHINE[0]), lx(L.MACHINE[1])
        top = L.CEIL_Y + 16
        # the room behind: dark concrete, the fan housings in the back wall, the riser duct to the shaft
        nz = pg.value_noise(m1 - m0, FL, 7, 88, octaves=2)
        for y in range(top, FL):
            for x in range(m0, m1):
                lay.px(x, y, 'C', 1.7 + (nz[y, x - m0] - 0.5) * 0.4, hgt=-0.4)
        lay.rect(m0 + 40, L.CEIL_Y, 40, top - L.CEIL_Y, 'S', 2.8, hgt=0.6)
        ph = float(self.cfg.get('fan_phase', 0.0))
        for i, (cx, cy, r) in enumerate(L.FANS):
            self.fan(lx(cx), cy, r, ph + i * 0.37)
        lay.rect(m0 + 10, 210, m1 - m0 - 20, 30, 'S', 2.0, hgt=0.5)            # motor block and belt guard
        for (cx, cy, r) in L.FANS:
            lay.rect(lx(cx) - 6, 196, 12, 14, 'S', 2.8, hgt=0.7)
        lay.rect(m0 + 10, 240, m1 - m0 - 20, FL - 240, 'C', 2.2, hgt=0.3)
        # the grille in front: steel frame and expanded-metal mesh
        for y in range(top, FL - 4):
            for x in range(m0, m1):
                d = (x + y) % 5 == 0 or (x - y) % 5 == 0
                if d:
                    lay.px(x, y, 'S', 3.6, hgt=0.6)
        for fx_ in (m0, m0 + 64, m1 - 3):
            lay.rect(fx_, top, 3, FL - top, 'S', 2.6, hgt=0.8)
            lay.vline(fx_, top, FL - top, 'S', 4.2, hgt=0.9)
        lay.rect(m0, top, m1 - m0, 3, 'S', 2.6, hgt=0.8)
        lay.rect(m0, 200, m1 - m0, 2, 'S', 2.8, hgt=0.7)
        # mesh door with padlock, the plates
        lay.rect(m1 - 26, 220, 2, 10, 'S', 4.6)
        lay.rect(m1 - 25, 228, 4, 4, 'L', 2.6)
        lay.rect(m0 + 74, 150, 32, 9, 'P', 4.8, hgt=0.4, crisp=True)
        K.text(lay, 'LÜFTUNG', m0 + 90, 152, 'I', 0.8, center=True)
        lay.rect(m0 + 78, 162, 24, 16, 'L', 3.8, hgt=0.4)
        lay.poly([(m0 + 90, 164), (m0 + 84, 176), (m0 + 96, 176)], 'I', 1.0)
        lay.rect(m0 + 89, 168, 2, 4, 'L', 3.8)
        self.light('machine_lamp', ((L.MACHINE[0] + L.MACHINE[1]) / 2, 96), 'cold', 0.55, 120, height=20,
                   box=(L.MACHINE[0], 0, L.MACHINE[1], FL))

    def fan(self, cx, cy, r, phase, lay=None):
        """Axial fan: steel ring housing, four blades at angle `phase` (radians), the hub."""
        lay = lay or self.lay
        yy, xx = np.mgrid[-r - 3:r + 4, -r - 3:r + 4]
        d = np.sqrt(xx ** 2 + yy ** 2)
        ring = (d <= r + 3) & (d > r)
        hole = d <= r
        x0, y0 = cx - r - 3, cy - r - 3
        lay.put(hole, x0, y0, 'N', 0.8, hgt=-0.6)
        ang = np.arctan2(yy, xx)
        blade = np.zeros_like(hole)
        for k in range(4):
            a = phase + k * math.pi / 2
            da = np.angle(np.exp(1j * (ang - a)))
            blade |= hole & (d > 4) & (np.abs(da) < 0.42 * (1 - d / (r * 1.8)))
        lay.put(blade, x0, y0, 'S', 2.6, hgt=0.4)
        edge = blade & ~K.erode(blade, 1)
        lay.put(edge, x0, y0, 'S', 3.8, hgt=0.5)
        lay.put(d <= 4, x0, y0, 'S', 4.2, hgt=0.8)
        lay.put(ring, x0, y0, 'S', 3.4, hgt=0.9)
        lay.put(ring & (yy < 0) & (xx < 0), x0, y0, 'S', 4.8, hgt=0.9)

    # ================================================================== the card hall
    def card_hall(self):
        lay = self.lay
        for (a, b) in L.CABINETS:
            self.cabinets(lx(a), lx(b))
        # rail and sliding ladders
        lay.hline(lx(1062), 72, lx(1500) - lx(1062), 'S', 4.4, hgt=0.8)
        for x in L.LADDERS:
            self.sliding_ladder(lx(x))
        self.drawer_bank(open_s8=bool(self.cfg.get('drawer')))
        # the wall section with the plan, the clock, a notice
        self.plan()
        self.clock(lx(L.CLOCK[0]), L.CLOCK[1])
        # filing trolley
        t0 = lx(1452)
        lay.rect(t0, 250, 40, 26, 'S', 2.6, hgt=0.6)
        lay.hline(t0, 250, 40, 'S', 4.6, hgt=0.8)
        for k in range(7):
            lay.rect(t0 + 3 + k * 5, 240, 4, 10, 'P', 3.6 + (k % 2) * 0.6, hgt=0.5)
        for wx in (t0 + 4, t0 + 33):
            lay.rect(wx, 278, 4, 4, 'I', 1.4)
            lay.vline(wx + 1, 276, 2, 'S', 2.0)

    def cabinets(self, a, b):
        lay = self.lay
        top, bottom = 74, 236
        lay.rect(a, top - 4, b - a, bottom - top + 4, 'S', 2.2, hgt=0.6)
        lay.rect(a, top - 4, b - a, 3, 'S', 4.2, hgt=0.9)
        rng = np.random.default_rng(a)
        for mx in range(a, b - 1, 32):
            mw = min(32, b - mx)
            lay.vline(mx, top, bottom - top, 'S', 1.4, hgt=0.3)
            for row, y in enumerate(range(top + 2, bottom - 6, 9)):
                for k in range(2):
                    dx = mx + 2 + k * (mw // 2)
                    dw = mw // 2 - 3
                    if dw < 4:
                        continue
                    lay.rect(dx, y, dw, 7, 'S', 3.0 + rng.random() * 0.25, hgt=0.5)
                    lay.hline(dx, y, dw, 'S', 4.0, hgt=0.6)
                    lay.rect(dx + dw // 2 - 2, y + 2, 4, 2, 'P', 4.4, hgt=0.5, crisp=True)
                    lay.px(dx + dw // 2, y + 5, 'S', 5.2, hgt=0.7)
        lay.rect(a, bottom - 2, b - a, 2, 'S', 1.6)

    def sliding_ladder(self, x):
        lay = self.lay
        for k in (0, 7):
            lay.line(x + k, 72, x + k + 12, FL - 2, 'P', 2.8, hgt=0.7)
        for y in range(80, FL - 4, 10):
            off = int((y - 72) / (FL - 74) * 12)
            lay.hline(x + off + 1, y, 6, 'P', 3.6, hgt=0.6)
        lay.rect(x - 1, 70, 10, 4, 'S', 3.6, hgt=0.8)

    def drawer_bank(self, open_s8=False):
        lay = self.lay
        b0, b1 = lx(L.BANK[0]), lx(L.BANK[1])
        y0, y1 = L.BANK_Y
        lay.rect(b0 - 4, y0 - 4, b1 - b0 + 8, 4, 'G', 1.2, hgt=0.9)           # linoleum top
        lay.hline(b0 - 4, y0 - 4, b1 - b0 + 8, 'G', 2.6, hgt=1.0)
        lay.rect(b0 - 3, y0, b1 - b0 + 6, y1 - y0 + 4, 'S', 2.0, hgt=0.6)
        for i in range(12):
            dx = b0 + i * L.DRAWER_W
            if dx == lx(L.DRAWER_S3[0]):
                self.ajar_drawer(dx, i + 1)
                continue
            lay.rect(dx + 1, y0 + 2, L.DRAWER_W - 2, y1 - y0 - 2, 'S', 3.2, hgt=0.6)
            lay.hline(dx + 1, y0 + 2, L.DRAWER_W - 2, 'S', 4.6, hgt=0.8)
            lay.rect(dx + 2, y0 + 5, L.DRAWER_W - 4, 7, 'P', 4.8, hgt=0.4, crisp=True)
            K.text(lay, str(i + 1), dx + L.DRAWER_W // 2 + 1, y0 + 6, 'I', 0.6, center=True, spacing=1)
            lay.rect(dx + 4, y0 + 20, L.DRAWER_W - 8, 3, 'L', 2.4, hgt=0.8)      # brass pull
            lay.hline(dx + 4, y0 + 20, L.DRAWER_W - 8, 'L', 3.8, hgt=0.9)
        # a few cards on the top, a sign above
        for k, cx in enumerate((b0 + 20, b0 + 70, b0 + 130)):
            lay.rect(cx, y0 - 6, 6, 2, 'P', 5.0, hgt=0.5)
        lay.rect(b0 + 30, 214, 108, 10, 'P', 4.8, hgt=0.4, crisp=True)
        lay.rect(b0 + 30, 214, 108, 1, 'P', 3.0)
        K.text(lay, 'HAUSHALTSKARTEI SÜD', b0 + 84, 216, 'I', 0.6, center=True)
        s8 = lx(L.DRAWER_S8[0])
        if open_s8:
            # Sued 8 pulled out: the drawer's long box toward the viewer, 212 cards, 37 red C-17 tabs
            lay.rect(s8 - 1, y0 + 2, L.DRAWER_W + 2, y1 - y0 + 6, 'S', 2.6, hgt=0.7)
            lay.rect(s8, y0 - 8, L.DRAWER_W, 10, 'S', 1.8, hgt=0.5)
            for k in range(L.DRAWER_W - 2):
                lay.vline(s8 + 1 + k, y0 - 9 + (k % 3 == 1), 9, 'P', 4.6 + (k % 2) * 0.5, hgt=0.6)
            for k in (1, 4, 6, 9, 11):
                lay.rect(s8 + k, y0 - 13, 2, 4, 'R', 3.4, hgt=0.8)
            lay.rect(s8 + 1, y0 + 9, L.DRAWER_W - 2, 7, 'P', 5.0, hgt=0.5, crisp=True)
            K.text(lay, '8', s8 + L.DRAWER_W // 2, y0 + 10, 'I', 0.6, center=True)
            lay.rect(s8 + 3, y0 + 26, L.DRAWER_W - 6, 3, 'L', 3.0, hgt=0.9)
            lay.rect(s8 - 1, y1 + 4, L.DRAWER_W + 2, 2, 'N', 1.0)
        else:
            lay.rect(s8 + 9, y0 + 1, 3, 3, 'R', 3.4, hgt=0.7)                   # one red tab peeking out

    def ajar_drawer(self, dx, num):
        """Sued 3 stands a finger's width open (the find exp_brandt_card, round-9 fix art-11), in every state: a dark
        slit above the front with the card tops in it, the front 2 px nearer (drawn lower, a brighter top edge, its
        shadow on the frame and under it), and one card -- Brandt's -- pulled up out of the slit, leaning a little,
        standing over the linoleum top."""
        lay = self.lay
        y0, y1 = L.BANK_Y
        w = L.DRAWER_W
        lay.rect(dx + 1, y0 + 2, w - 2, 2, 'N', 0.4, hgt=-0.4)                   # the slit into the drawer
        for k in range(1, w - 3, 2):
            lay.px(dx + 1 + k, y0 + 3, 'P', 1.4, hgt=-0.2)                       # card tops in the dark
        lay.rect(dx + 1, y0 + 4, w - 2, y1 - y0 - 2, 'S', 3.4, hgt=0.7)          # the front, pulled forward
        lay.hline(dx + 1, y0 + 4, w - 2, 'S', 5.0, hgt=0.9)
        lay.vline(dx + 1, y0 + 5, y1 - y0 - 3, 'S', 4.0, hgt=0.8)
        lay.vline(dx + w - 1, y0 + 4, y1 - y0 - 1, 'N', 0.8)                     # its shadow on the frame ...
        lay.hline(dx + 1, y1 + 2, w - 1, 'N', 0.8)                               # ... and under it
        lay.rect(dx + 2, y0 + 7, w - 4, 7, 'P', 4.8, hgt=0.4, crisp=True)
        K.text(lay, str(num), dx + w // 2 + 1, y0 + 8, 'I', 0.6, center=True, spacing=1)
        lay.rect(dx + 4, y0 + 22, w - 8, 3, 'L', 2.4, hgt=0.8)                   # brass pull
        lay.hline(dx + 4, y0 + 22, w - 8, 'L', 3.8, hgt=0.9)
        # Brandt's card: the front card of the drawer, pulled up through the slit -- its face (the drawer's width
        # less the walls) stands over the frame and the linoleum top, two typed lines, the shaded right edge
        cx, cw = dx + 3, w - 6
        lay.rect(cx, y0 - 6, cw, 10, 'P', 4.7, hgt=0.6)
        lay.hline(cx, y0 - 6, cw, 'P', 5.0, hgt=0.7)
        lay.vline(cx + cw - 1, y0 - 5, 9, 'P', 3.4, hgt=0.5)
        lay.hline(cx + 1, y0 - 4, cw - 3, 'P', 2.4, hgt=0.6)                     # name line
        lay.hline(cx + 1, y0 - 2, cw - 5, 'P', 2.4, hgt=0.6)                     # the note under it

    def plan(self):
        lay = self.lay
        p0, p1 = lx(L.PLAN[0]), lx(L.PLAN[1])
        y0, y1 = L.PLAN_Y
        K.frame(lay, p0, y0, p1 - p0, y1 - y0, ramp='S', face=1.6, hi=3.6, lo=0.8, shadow=('G', 1.4))
        lay.rect(p0, y0, p1 - p0, y1 - y0, 'P', 4.7, hgt=0.2)
        # diazo blue lines: the annex (long box), the three shafts up to three blocks hatched in red pencil
        ink = ('D', 1.6)
        K.text(lay, 'BLATT 3', p0 + 3, y0 + 3, *ink)
        base = y1 - 14
        lay.rect(p0 + 6, base, p1 - p0 - 12, 6, 'D', 3.4)
        lay.hline(p0 + 6, base, p1 - p0 - 12, *ink)
        lay.hline(p0 + 6, base + 6, p1 - p0 - 12, *ink)
        lay.vline(p0 + 6, base, 7, *ink)
        lay.vline(p1 - 7, base, 7, *ink)
        for k, sx in enumerate((p0 + 16, p0 + 36, p0 + 56)):
            lay.vline(sx, y0 + 22, base - y0 - 22, *ink)
            lay.vline(sx + 2, y0 + 22, base - y0 - 22, *ink)
            K.text(lay, 'S%d' % (k + 1), sx - 2, base + 1, 'D', 1.2)
            bx0 = sx - 6
            lay.rect(bx0, y0 + 12, 14, 9, 'P', 4.7)
            for i in range(14):
                for j in range(9):
                    if i in (0, 13) or j in (0, 8):
                        lay.px(bx0 + i, y0 + 12 + j, *ink)
                    elif (i + j) % 3 == 0:
                        lay.px(bx0 + i, y0 + 12 + j, 'R', 2.8)
        lay.rect(p1 - 31, y1 - 7, 29, 6, 'P', 5.0, crisp=True)
        K.text(lay, 'K.ADLER', p1 - 30, y1 - 7, 'D', 1.0)
        # glass reflection
        for i in range(10):
            lay.px(p0 + 3 + i, y0 + 30 - i, 'P', 5.2)

    def clock(self, cx, cy, r=7):
        lay = self.lay
        m = K.disc(2 * r + 1)
        lay.put(m, cx - r, cy - r, 'P', 4.8, hgt=0.6)
        lay.put(K.edge_of(m), cx - r, cy - r, 'I', 1.2, hgt=0.8)
        for a in range(12):
            ang = a * math.pi / 6
            lay.px(cx + int(round(math.sin(ang) * (r - 2))), cy - int(round(math.cos(ang) * (r - 2))), 'I', 1.4)
        lay.vline(cx, cy - r + 2, r - 1, 'I', 0.6)              # 6.00: minute hand up ...
        lay.vline(cx, cy, r - 3, 'I', 0.6)                      # ... hour hand down
        lay.rect(cx - 1, cy - r - 3, 3, 3, 'S', 2.6)

    # ================================================================== tube station, bench
    def tube_station(self, opened=False):
        lay = self.lay
        t0, t1 = lx(L.TUBE_ST[0]), lx(L.TUBE_ST[1])
        y0, y1 = L.TUBE_ST_Y
        cx = (t0 + t1) // 2
        lay.rect(t0, y0 - 12, t1 - t0, 10, 'P', 4.8, hgt=0.4, crisp=True)
        K.text(lay, 'ROHRPOST', cx + 1, y0 - 10, 'I', 0.6, center=True)
        lay.rect(t0 + 2, y0, t1 - t0 - 4, y1 - y0, 'S', 2.8, hgt=0.6)
        lay.vline(t0 + 2, y0, y1 - y0, 'S', 4.2, hgt=0.8)
        lay.vline(t1 - 3, y0, y1 - y0, 'S', 1.6, hgt=0.4)
        # receivers (brass flaps) where the tubes come in
        for k, rx in enumerate((cx - 9, cx + 7)):
            lay.rect(rx - 4, y0 + 2, 10, 20, 'L', 2.2, hgt=0.7)
            lay.rect(rx - 3, y0 + 4, 8, 14, 'L', 3.2, hgt=0.6)
            lay.hline(rx - 3, y0 + 4, 8, 'L', 4.4, hgt=0.8)
            lay.rect(rx, y0 + 22, 2, 18, 'S', 3.8, hgt=0.6)
        # control panel: lamps, selector dial
        lay.rect(t0 + 6, y0 + 46, t1 - t0 - 12, 30, 'S', 1.8, hgt=0.5)
        for k, (ramp, tone) in enumerate((('G', 5.0), ('R', 4.0), ('L', 4.6))):
            lay.rect(t0 + 10 + k * 8, y0 + 50, 3, 3, ramp, tone, emis=True)
        m = K.disc(11)
        lay.put(m, cx - 5, y0 + 58, 'P', 4.4, hgt=0.7)
        lay.put(K.edge_of(m), cx - 5, y0 + 58, 'I', 1.2)
        for a in range(10):
            ang = a * math.pi / 5
            lay.px(cx + int(round(math.sin(ang) * 3)), y0 + 63 - int(round(math.cos(ang) * 3)), 'I', 1.6)
        # the delivery tray (wire basket) with the capsule from the Staatspolizei
        ty = y0 + 88
        lay.rect(t0 - 2, ty, t1 - t0 + 4, 3, 'S', 4.0, hgt=0.8)
        for x in range(t0 - 2, t1 + 2, 3):
            lay.vline(x, ty + 3, 8, 'S', 3.0)
        lay.hline(t0 - 2, ty + 10, t1 - t0 + 4, 'S', 3.4)
        if opened:
            lay.rect(cx - 11, ty - 5, 13, 5, 'S', 3.8, hgt=0.7)
            lay.hline(cx - 11, ty - 5, 13, 'S', 5.4, hgt=0.8)
            lay.rect(cx + 2, ty - 5, 2, 5, 'N', 0.8)
            lay.rect(cx + 6, ty - 4, 5, 4, 'R', 3.0, hgt=0.7)
        else:
            lay.rect(cx - 10, ty - 5, 20, 5, 'S', 3.8, hgt=0.7)
            lay.hline(cx - 10, ty - 5, 20, 'S', 5.6, hgt=0.8)
            lay.hline(cx - 10, ty - 1, 20, 'S', 2.0)
            lay.rect(cx - 2, ty - 5, 4, 5, 'R', 3.4, hgt=0.7)
            lay.rect(cx + 7, ty - 5, 3, 5, 'S', 2.6, hgt=0.6)
        lay.rect(t0 + 4, y1, 4, FL - y1, 'S', 2.2)
        lay.rect(t1 - 8, y1, 4, FL - y1, 'S', 2.2)
        self.light('tube_station_lamps', ((L.TUBE_ST[0] + L.TUBE_ST[1]) / 2, y0 + 52), 'cold', 0.25, 30, height=6)

    def bench(self):
        lay = self.lay
        b0, b1 = lx(L.BENCH[0]), lx(L.BENCH[1])
        lay.rect(b0, 266, b1 - b0, 3, 'P', 2.8, hgt=0.7)
        lay.rect(b0, 256, b1 - b0, 2, 'P', 2.6, hgt=0.6)
        lay.rect(b0, 260, b1 - b0, 2, 'P', 2.4, hgt=0.6)
        for x in (b0 + 3, b1 - 6):
            lay.rect(x, 256, 3, FL - 256, 'I', 1.6)
        lay.rect(b0 + 2, 186, b1 - b0 - 4, 20, 'P', 4.9, hgt=0.4, crisp=True)
        K.text(lay, 'WARTEN BIS', (b0 + b1) // 2, 189, 'I', 0.6, center=True)
        K.text(lay, 'ZUM AUFRUF', (b0 + b1) // 2, 197, 'I', 0.6, center=True)
        lay.rect((b0 + b1) // 2 - 6, 207, 12, 9, 'S', 1.4)                    # the call-number box
        K.text(lay, '17', (b0 + b1) // 2 + 1, 209, 'R', 3.8, center=True, emis=True)

    # ================================================================== counter, typists' room, the corridor door
    def typists_room(self):
        lay = self.lay
        g0, g1 = lx(L.GLASS[0]), lx(L.GLASS[1])
        y0, y1 = L.GLASS_Y
        # the room behind the glass: brighter, its own tubes; shelves of files, desks, the two typists' places
        lay.rect(g0, y0, g1 - g0, y1 - y0, 'G', 3.6, hgt=-0.5)
        lay.rect(g0, y0, g1 - g0, 8, 'G', 4.4, emis=True)
        for x in range(g0 + 4, g1 - 4, 14):
            for yy in range(y0 + 14, y0 + 60, 12):
                lay.rect(x, yy, 12, 10, 'P', 2.6, hgt=-0.4)
                for k in range(0, 12, 3):
                    lay.vline(x + k, yy + 1, 9, 'P', 3.6 + (k % 2) * 0.4, hgt=-0.4)
                lay.hline(x - 1, yy + 10, 14, 'S', 2.0)
        for (tx, _v) in L.TYPISTS:
            dx = lx(tx)
            lay.rect(dx - 16, y1 - 22, 34, 4, 'P', 2.4, hgt=-0.3)              # desk
            lay.rect(dx - 6, y1 - 30, 12, 8, 'S', 1.4, hgt=-0.3)               # typewriter
            lay.hline(dx - 6, y1 - 30, 12, 'S', 3.0)
            lay.rect(dx - 3, y1 - 36, 6, 6, 'P', 5.0, hgt=-0.3)                # paper in the platen
            lay.rect(dx - 14, y1 - 18, 2, 18, 'S', 1.6)
            lay.rect(dx + 14, y1 - 18, 2, 18, 'S', 1.6)

    def glass_front(self):
        lay = self.lay
        g0, g1 = lx(L.GLASS[0]), lx(L.GLASS[1])
        y0, y1 = L.GLASS_Y
        self.glass_mask = np.zeros((H, W), bool)
        for x in range(g0, g1):
            for y in range(y0, y1):
                if (x - y * 0.5) % 47 < 2:
                    lay.px(x, y, 'G', 5.0)
                    self.glass_mask[y, x] = True
        for fx_ in range(g0, g1 + 1, 46):
            lay.rect(min(fx_, g1 - 3), y0, 3, y1 - y0, 'S', 2.6, hgt=0.8)
            lay.vline(min(fx_, g1 - 3), y0, y1 - y0, 'S', 4.0, hgt=0.9)
            self.glass_mask[y0:y1, min(fx_, g1 - 3):min(fx_, g1 - 3) + 3] = True
        lay.rect(g0, y0 - 3, g1 - g0, 3, 'S', 2.6, hgt=0.8)
        lay.rect(g0, y1 - 2, g1 - g0, 2, 'S', 2.2, hgt=0.6)
        # speaking grille and the pass-through slot in front of the registrar's place
        sg = lx(1712)
        for k in range(-4, 5, 2):
            for j in range(-4, 5, 2):
                if k * k + j * j <= 16:
                    lay.px(sg + k, 212 + j, 'S', 2.0)
        lay.rect(sg - 10, y1 - 6, 20, 4, 'N', 1.4)

    def counter(self, form=False):
        lay = self.lay
        c0, c1 = lx(L.COUNTER[0]), lx(L.COUNTER[1])
        y0, y1 = L.COUNTER_Y
        lay.rect(c0, y0 - 2, c1 - c0, 4, 'G', 1.3, hgt=0.9)                    # linoleum top
        lay.hline(c0, y0 - 2, c1 - c0, 'G', 3.0, hgt=1.0)
        lay.rect(c0 + 1, y0 + 2, c1 - c0 - 2, y1 - y0 - 2, 'P', 2.2, hgt=0.6)
        for x in range(c0 + 4, c1 - 4, 20):
            K.recess(lay, x, y0 + 6, 16, y1 - y0 - 12, 'P', 1.8, shadow=1.2, light=3.0)
        lay.rect(c0 + 1, y1 - 3, c1 - c0 - 2, 3, 'I', 1.4)
        # the sign and the official plate above (insignia decal site)
        cx = lx(1711)
        lay.rect(cx - 44, 136, 88, 10, 'P', 4.9, hgt=0.4, crisp=True)
        lay.rect(cx - 44, 136, 88, 1, 'P', 3.0)
        w1 = K.text_width('AUSKUNFT')
        K.text(lay, 'AUSKUNFT', cx - 3 - w1, 138, 'I', 0.6)
        lay.px(cx, 140, 'I', 0.6)
        K.text(lay, 'ABGLEICH', cx + 3, 138, 'I', 0.6)
        self.plate(cx, 100, 'NEBENSTELLE SÜD')
        # on the counter: stamp carousel, stamp pad, forms, the goose-neck lamp, the perforator
        sx = c0 + 6
        lay.rect(sx + 4, y0 - 20, 2, 18, 'I', 1.4)
        lay.rect(sx, y0 - 22, 10, 2, 'I', 1.8)
        for k in range(4):
            lay.rect(sx + k * 3, y0 - 20, 2, 5, 'P', 2.8, hgt=0.6)
            lay.rect(sx + k * 3, y0 - 15, 2, 2, 'I', 1.0)
        lay.rect(sx + 12, y0 - 5, 9, 3, 'S', 1.6, hgt=0.5)
        lay.rect(sx + 13, y0 - 5, 7, 1, 'R', 2.0)
        for k in range(5):
            lay.rect(sx + 24, y0 - 4 - k, 14, 1, 'P', 4.4 + (k % 2) * 0.5, hgt=0.4)
        if form:
            fx_ = lx(1696)
            lay.rect(fx_, y0 - 4, 14, 2, 'P', 5.2, hgt=0.4)
            lay.hline(fx_ + 2, y0 - 4, 8, 'I', 1.6)
            lay.line(fx_ + 12, y0 - 7, fx_ + 17, y0 - 4, 'I', 1.2)
        lx_ = lx(1748)
        lay.rect(lx_ - 4, y0 - 4, 9, 3, 'S', 2.0, hgt=0.6)
        lay.line(lx_, y0 - 4, lx_ + 2, y0 - 22, 'S', 3.2)
        lay.line(lx_ + 2, y0 - 22, lx_ - 4, y0 - 28, 'S', 3.2)
        lay.rect(lx_ - 9, y0 - 30, 9, 4, 'S', 2.4, hgt=0.7)
        lay.rect(lx_ - 8, y0 - 26, 7, 1, 'L', 5.0, emis=True)
        self.light('counter_lamp', (1743, y0 - 24), 'warm', 1.2, 120, height=14, pool=0.4, pool_w=14,
                   pool_depth=30)
        px_ = lx(1758)
        lay.rect(px_, y0 - 12, 12, 10, 'I', 2.0, hgt=0.8)
        lay.hline(px_, y0 - 12, 12, 'I', 3.0, hgt=0.9)
        lay.line(px_ + 10, y0 - 12, px_ + 14, y0 - 22, 'S', 3.6)
        lay.rect(px_ + 13, y0 - 24, 3, 3, 'R', 2.4, hgt=0.8)
        lay.rect(px_ + 2, y0 - 15, 6, 3, 'P', 5.0, hgt=0.5)

    def plate(self, cx, y, txt):
        """Official plate: the emblem above the text (neutral Reichssiegel / historical eagle, 12.4)."""
        lay = self.lay
        w = max(40, K.text_width(txt) + 8)
        lay.rect(cx - w // 2, y, w, 31, 'S', 1.6, hgt=0.6)
        lay.rect(cx - w // 2 + 1, y + 1, w - 2, 29, 'S', 2.4, hgt=0.5)
        K.text(lay, txt, cx, y + 24, 'P', 4.4, center=True)
        self.emblem(cx, y + 2)

    def emblem(self, cx, y, size=20):
        K.emblem(self.lay, cx, y, size, self.hist)

    def stapo_door(self):
        lay = self.lay
        d0, d1 = lx(L.STAPO_DOOR[0]), lx(L.STAPO_DOOR[1])
        y0, y1 = L.STAPO_DOOR_Y
        lay.rect(d0 - 3, y0 - 3, d1 - d0 + 6, y1 - y0 + 3, 'S', 1.6, hgt=0.8)
        lay.rect(d0, y0, d1 - d0, y1 - y0, 'S', 2.6, hgt=0.5)
        for y in range(y0 + 3, y1, 8):
            for x in (d0 + 2, d1 - 3):
                lay.px(x, y, 'S', 4.6, hgt=0.8)
        lay.rect(d0 + 10, y0 + 8, d1 - d0 - 20, 14, 'N', 1.6)
        for x in range(d0 + 10, d1 - 10, 3):
            lay.vline(x, y0 + 8, 14, 'S', 2.2)
        for y in range(y0 + 8, y0 + 22, 3):
            lay.hline(d0 + 10, y, d1 - d0 - 20, 'S', 2.2)
        lay.rect(d1 - 9, y0 + 28, 5, 2, 'S', 4.8, hgt=0.8)
        cx = (d0 + d1) // 2
        lay.rect(cx - 28, y0 - 14, 56, 9, 'P', 4.8, hgt=0.4, crisp=True)
        K.text(lay, 'STAATSPOLIZEI', cx + 1, y0 - 12, 'I', 0.6, center=True)
        self.emblem(cx, y0 - 34)
        lay.rect(d1 + 6, y0 + 2, 5, 5, 'R', 4.0, emis=True)
        lay.rect(d1 + 5, y0 + 1, 7, 1, 'S', 3.0)
        self.light('stapo_lamp', (L.STAPO_DOOR[1] + 8, y0 + 4), 'warm', 0.3, 28, height=6)
        # fire extinguisher on the end pier
        ex = lx(1902)
        lay.rect(ex, 252, 6, 16, 'R', 3.0, hgt=0.8)
        lay.vline(ex, 252, 16, 'R', 4.0, hgt=0.9)
        lay.rect(ex + 1, 248, 3, 4, 'I', 1.4)

    def end_pier(self):
        lay = self.lay
        e0 = lx(1896)
        lay.rect(e0 - 4, 0, 4, FL, 'C', 3.6, hgt=0.8)
        lay.rect(lx(1832), L.CEIL_Y, 16, FL - L.CEIL_Y, 'C', 2.6, hgt=0.7)
        lay.vline(lx(1832), L.CEIL_Y, FL - L.CEIL_Y, 'C', 3.8, hgt=0.9)

    # ================================================================== floor
    def floor(self):
        lay = self.lay
        nz = pg.value_noise(W, H, 14, 601, octaves=3)
        fine = pg.value_noise(W, H, 2, 602, octaves=2)
        hf = H - FL
        ys = np.arange(hf, dtype=np.float32)[:, None]
        t = 2.35 + (nz[FL:] - 0.5) * 0.5 + (fine[FL:] - 0.5) * 0.12 + ys * 0.004
        lay.put(np.ones((hf, W), bool), 0, FL, 'S', t.astype(np.float32), flat=False, hgt=0.05)
        for y in (FL + 6, FL + 15, FL + 27, FL + 42, FL + 60):
            if y < H:
                lay.hline(0, y, W, 'S', 1.6, hgt=-0.1)
        # reflections of the tubes in the polished linoleum: soft vertical sheen, ordered dither, every other row
        thr = pg.bayer(W, H, 0, 0, 4)
        for fx in L.FIXTURES:
            x = lx(fx)
            for y in range(FL + 2, min(H, FL + 46), 2):
                k = 1 - (y - FL - 2) / 44.0
                half = 6 + (y - FL) * 0.12
                for xx in range(int(x - half), int(x + half) + 1):
                    f = (1 - abs(xx - x) / (half + 1)) ** 1.3 * k
                    if f > thr[y, xx] * 0.9:
                        lay.px(xx, y, 'G', 2.2 + f * 1.8, hgt=0.0)
        # rubber runners in front of the counter and the drawer bank
        for (a, b) in ((lx(1640), lx(1780)), (lx(1120), lx(1300))):
            lay.rect(a, FL + 9, b - a, 5, 'I', 1.6, hgt=0.1)
            lay.hline(a, FL + 9, b - a, 'I', 2.4)

    def ambient(self):
        lay = self.lay
        f = np.zeros((H, W), np.float32)
        ys = np.arange(H, dtype=np.float32)[:, None]
        f += -0.7 * np.clip((60 - ys) / 60, 0, 1)
        f += -0.3 * np.clip((ys - 330) / 30, 0, 1)
        f[lay.emis] = 0
        lay.amb_field(f)

    def build(self):
        self.shell()
        self.services()
        self.machine_room()
        self.card_hall()
        self.tube_station(opened=bool(self.cfg.get('tube')))
        self.bench()
        self.typists_room()
        self.glass_front()
        self.counter(form=bool(self.cfg.get('form')))
        self.end_pier()
        self.stapo_door()
        self.shaft()
        self.fixtures()
        self.floor()
        self.ambient()
        return self.lay

    def all_lights(self):
        return list(self.lights)


def bake_hall(cfg: dict | None = None):
    h = Hall(cfg)
    h.build()
    lights = h.all_lights()
    F = K.light_fields(h.lay, lights, origin=(X0, 0))
    local = [dict(lt, pos=(lt['pos'][0] - X0, lt['pos'][1])) for lt in lights]
    K.add_pools(F, local, FL, H, W)
    K.resolve(h.lay, F, exposure=0.9)
    return h


def fg_layer(w=1190, h=42):
    """Near-black foreground of the annex (parallax 1.25): a filing trolley's edge, a chair back, cable reels."""
    lay = K.tlayer(w, h, 'fg_annex', 'hall')
    for (cx, kind) in ((90, 'chair'), (420, 'reel'), (760, 'cart'), (1100, 'chair')):
        if kind == 'chair':
            lay.rect(cx, h - 28, 3, 28, 'N', 1.0)
            lay.rect(cx - 10, h - 30, 16, 4, 'N', 1.6)
            lay.rect(cx - 12, h - 12, 20, 3, 'N', 1.2)
        elif kind == 'reel':
            m = K.disc(24)
            lay.put(m[:20, :], cx, h - 20, 'N', 1.2)
            lay.put(K.disc(8), cx + 8, h - 14, 'N', 2.2)
        else:
            lay.rect(cx, h - 22, 60, 4, 'N', 1.6)
            lay.rect(cx + 4, h - 18, 3, 18, 'N', 1.0)
            lay.rect(cx + 52, h - 18, 3, 18, 'N', 1.0)
    K.resolve(lay, None, exposure=1.0)
    return lay
