"""env_c4p2_karsk_show -- scene B of L_C4P2_Karsk: the depot's showcase and platform 1, Tuesday 18 February 1964,
17.30-20.10, evening floodlight (documentation/C4P2_DESIGN.md 4.1).

Left -> right: the tarpaulin's painted front („ВОССТАНОВИМ ВМЕСТЕ“; the coal stage and its floodlight mast over it,
coal dust rising -- Kolonne 4 behind it), the restored colour-light signal (green aspect, red bows), the roundhouse
front with the polished engine head-on (red ribbons, a fir wreath on the smokebox door, the emblem -- insignia site,
the brass plate „1939“), the band's plank stage under a string of bulbs, the press canteen cut open (white cloth, tea
glasses, bread with caviar, Ekdahl's Swedish guidebook, the samovar; the band's kasha behind the curtain), the
turntable's cabin, the sand-drying house cut open (sand stove, sieves, the decimal scale, Lev's workbench under the
green-shaded lamp), the gate to the passenger side, platform 1 under its canopy with the westbound Corridor express
(sleeping car, its vestibule door = express_door, the dining car), the station clock.

cfg: book_taken (c4g_inspect_book), halves (c4g_talk_lev .. c4g_solve_halves: the Russian half and the open guidebook
on the bench), joined (c4g_solve_halves: the whole card, the stamp closed), hist (insignia).
"""
from __future__ import annotations

import math

import numpy as np

import env_c4p2_karsk_kit as K
import env_c4p2_karsk_layout as L

W, H = L.WORLD_W, L.WORLD_H
BASE = 292                     # base of the things at the back of the walk band


class Show:
    def __init__(self, cfg: dict):
        self.cfg = dict(cfg)
        self.lay = K.tlayer(W, H, 'show_b')
        self.lights: list = []
        self.rng = np.random.default_rng(5170)
        self.windows: list = []            # express windows (x, y, w, h, lit)
        self.readable: dict = {}           # story text the art must keep readable: name -> [x, y, w, h] (scene.json)

    def L(self, *a, **kw):
        self.lights.append(K.light(*a, **kw))

    def build(self):
        x0, x1 = L.SPAN[L.SB]
        self.ground(x0, x1)
        self.stage_backdrop()
        self.flood_mast_b()
        self.tarpaulin()
        self.roundhouse_front()
        self.signal()
        self.engine()
        self.band_stage()
        self.canteen()
        self.turntable()
        self.sandhouse()
        self.platform()
        self.express()
        self.canopy()
        self.gate()                        # the gate stands in front of the express's end and the canopy
        self.near_rails()
        self.sky_lights()
        self.lay.erase(0, 0, x0, H)
        return self

    # ------------------------------------------------------------------ ground
    def ground(self, x0, x1):
        lay = self.lay
        top = 284
        w, h = x1 - x0, H - top
        yy = np.linspace(0, 1, h, dtype=np.float32)[:, None]
        t = 2.4 + K.nz(w, h, 24, 501, octaves=2) * 0.7 + K.nz(w, h, 6, 502) * 0.3 - yy * 0.2
        lay.put(np.ones((h, w), bool), x0, top, 'S', t, hgt=0.3, flat=False)
        # the swept path (cinders and wet slush, the guest walks here) runs the whole length, on through the gate
        pa = L.PLATFORM[0]
        pn = K.nz(x1 - x0, 26, 6, 503)
        pr = np.abs(np.linspace(-1, 1, 26, dtype=np.float32))[:, None]
        mk = (pn + 0.5) * 1.1 - pr * 0.8 > 0.24
        on_pf = np.arange(x0, x1)[None, :] >= pa
        lay.put(mk & ~on_pf, x0, 289, 'S', 1.6 + pn * 0.8, hgt=0.15, flat=False)
        lay.put(mk & ~on_pf & (pn < -0.15), x0, 289, 'E', 3.0 + pn, hgt=0.1, flat=False)
        # platform 1 lies under the same trodden snow as the yard (no seam at the gate).  The concrete shows only where
        # it is swept: a strip along the whitewashed edge at the back, and -- wet and dark, the slab joints faint in
        # it -- where people stand and walk; the snow is heaped round the column feet.
        pw = x1 - pa
        ramp_in = np.clip((np.arange(pa, x1, dtype=np.float32)[None, :] - pa) / 14.0, 0, 1)
        thr = K.pg.bayer(pw, 26, pa, 289, 4)
        n_x = K.nz(pw, 2, 26, 508, octaves=2)[0][None, :]                  # a slow waviness along the platform
        dist = np.abs(np.arange(289, 315, dtype=np.float32)[:, None] - 300.0) - (6.5 + n_x * 4.0)
        swept = (dist < -1.0) | ((dist < 1.0) & (thr < (1.0 - dist) * 0.5))   # soft, dithered edges
        swept &= (ramp_in > thr * 0.9) | (ramp_in >= 1.0)
        lay.put(swept, pa, 289, 'C', 2.9 + K.nz(pw, 26, 4, 509) * 0.5, hgt=0.12, flat=False)
        jm = np.zeros(swept.shape, bool)
        for (ry, step, off) in ((4, 13, 0), (10, 15, 7), (18, 18, 3)):
            jm[ry, :] = True
            jm[max(0, ry - 5):ry, off::step] = True
        lay.put(swept & jm & (dist < -1.5), pa, 289, 'C', 2.2, hgt=0.0, flat=False)    # the slab joints, faint
        lay.rect(pa + 2, 284, pw - 2, 2, 'C', 2.9, hgt=0.2)                 # the swept edge strip
        for xj in range(pa + 9, x1, 13):
            lay.px(xj, 284, 'C', 1.8)
        for cx_ in L.CANOPY_COLUMNS:                                        # snow heaped round the column feet
            for i in range(-8, 9):
                d = int(round(3.5 * (1 - (i / 9.0) ** 2)))
                lay.rect(cx_ + i, BASE + 2 - d, 1, d, 'S', 3.4 + 0.3 * math.cos(i), hgt=0.4)
        lay.rect(pa, 286, x1 - pa, 2, 'W', 4.6, hgt=0.4)                 # the platform edge, whitewashed
        lay.rect(pa, 288, x1 - pa, 1, 'C', 1.4)
        lay.rect(L.GATE[0] + 4, BASE + 1, L.GATE[1] - L.GATE[0] - 6, 2, 'I', 2.6, hgt=0.5)   # the gate's threshold
        lay.rect(L.GATE[0] + 4, BASE + 1, L.GATE[1] - L.GATE[0] - 6, 1, 'I', 4.0)
        rng = np.random.default_rng(505)
        for (sx, ex, y0, step) in ((900, 1590, 302, 8), (1590, 1910, 304, 7), (1100, 1560, 330, 9)):
            for k, x in enumerate(range(sx, ex, step)):
                lay.rect(x, y0 + (2 if k % 2 else 0) + int(2 * math.sin(x * 0.05)), 2, 1, 'S', 1.8, hgt=0.1)
        # puddles of melt under the floods (they reflect)
        for (px, py, rx) in ((1040, 316, 22), (1120, 330, 14), (1300, 318, 16), (1700, 322, 26)):
            m_, mx, my = lay.ellipse_mask(px, py, rx, 3)
            lay.put(m_, mx, my, 'I', 2.4, hgt=-0.1)
            lay.rect(px - rx // 3, py - 1, rx // 2, 1, 'S', 4.4)

    def near_rails(self):
        """Rails of the stall track run out from under the engine toward the viewer (perspective)."""
        lay = self.lay
        cx = (L.LOCO[0] + L.LOCO[1]) / 2.0
        for y in range(294, H, 6):
            k = (y - 294) / (H - 294.0)
            hw = 26 + k * 22
            lay.rect(int(cx - hw - 4), y, int(2 * hw + 8), 3, 'D', 1.8 + k * 0.4, hgt=0.4)
            lay.rect(int(cx - hw - 4), y, int(2 * hw + 8), 1, 'S', 3.0, hgt=0.5)
        for s in (-1, 1):
            for y in range(292, H):
                k = (y - 294) / (H - 294.0)
                hw = 26 + k * 22
                x = int(round(cx + s * hw))
                lay.rect(x - 1, y, 3, 1, 'I', 3.6, hgt=0.8)
                lay.px(x, y, 'I', 5.6, hgt=0.9)

    # ------------------------------------------------------------------ backdrop: the coal stage over the tarpaulin
    def stage_backdrop(self):
        lay = self.lay
        # the back fence of the showcase yard
        x0 = L.SPAN[L.SB][0]
        K.planks(lay, x0, 250, L.GATE[0] - x0, 34, 'D', 1.8, seed=511, pitch=4)
        for x in range(x0 + 4, L.GATE[0], 52):
            lay.rect(x, 246, 4, 38, 'C', 2.2, hgt=0.6)
            K.snowcap(lay, x, 246, 4, depth=2, seed=x)
        K.snowcap(lay, x0, 250, L.GATE[0] - x0, depth=2, seed=512)
        # the coal stage seen over the tarpaulin: the gondola's edge, the trestle top, the floodlight mast (lit)
        lay.rect(870, 168, 120, 8, 'D', 1.6, hgt=0.6)
        lay.rect(870, 168, 120, 1, 'D', 2.8)
        lay.rect(884, 134, 96, 34, 'K', 1.6, hgt=0.5)
        for xx in range(888, 980, 12):
            lay.rect(xx, 134, 2, 34, 'K', 1.0)
        K.coal_heap(lay, 932, 136, 86, 12, seed=513, glint=0.08)
        mx = 1000
        for yy in range(60, 200):
            k = (yy - 60) / 140.0
            hw = 3 + int(k * 3)
            lay.px(mx - hw, yy, 'I', 2.0)
            lay.px(mx + hw, yy, 'I', 1.8)
            if yy % 8 == 0:
                lay.line(mx - hw, yy, mx + hw, yy + 8, 'I', 1.6)
        for dx in (-6, 0, 6):
            K.lamp_head(lay, mx + dx, 60, 'flood', True)
        self.L('stage_flood', 994, 64, 'warm', 1.2, 300, 60, falloff=1.0, cone=(-0.55, 0.83, 0.70))

    def flood_mast_b(self):
        """A lattice floodlight mast behind the sand-drying house (its foot hidden by the roof): three lamps high in
        the evening sky, their light on the roofs and the platform end -- something lit up in the upper picture."""
        lay = self.lay
        mx = L.FLOOD_MAST_B
        top = 44
        for yy in range(top + 6, 190):
            k = (yy - top) / 146.0
            hw = 2 + int(round(k * 4))
            lay.px(mx - hw, yy, 'I', 2.0)
            lay.px(mx + hw, yy, 'I', 1.7)
            if (yy - top) % 8 == 0:
                lay.line(mx - hw, yy, mx + hw, yy + 8, 'I', 1.5)
                lay.line(mx + hw, yy, mx - hw, yy + 8, 'I', 1.5)
        lay.rect(mx - 10, top + 5, 21, 2, 'I', 2.6, hgt=0.7)              # the lamp platform and its rail
        lay.rect(mx - 10, top + 1, 1, 4, 'I', 2.2)
        lay.rect(mx + 10, top + 1, 1, 4, 'I', 2.2)
        lay.rect(mx - 10, top + 1, 21, 1, 'I', 2.2)
        K.snowcap(lay, mx - 10, top + 5, 21, depth=1, seed=mx)
        for dx in (-6, 0, 6):
            K.lamp_head(lay, mx + dx, top + 2, 'flood', True)
        self.flood_b = (mx, top + 4)
        self.L('flood_b', mx, top + 6, 'warm', 0.7, 240, 60, falloff=1.0, cone=(0.35, 0.94, 0.62))

    def tarpaulin(self):
        lay = self.lay
        a, b = L.TARP_B
        top = 192
        # the near end turns toward the viewer (the blocker): a slanted panel
        lay.poly([(a, top + 30), (a + 22, top), (a + 22, BASE + 2), (a, 312)], 'Q', 1.8, hgt=0.3)
        lay.line(a + 22, top, a + 22, BASE + 2, 'Q', 3.0)
        # the long face along the back of the yard
        face_x0 = a + 22
        n = K.nz(b - face_x0, BASE - top, 5, 521)
        t = 2.4 + n * 0.8
        lay.put(np.ones((BASE - top, b - face_x0), bool), face_x0, top, 'Q', t, hgt=0.3, flat=False)
        for k in range(face_x0 + 6, b, 9):                                 # folds between the lashings
            lay.line(k, top + 2, k + 1, BASE - 2, 'Q', 1.6)
        # the poles with their rope lashings (the painted panel is lashed on in FRONT of them)
        for px in range(face_x0 + 2, b, 34):
            lay.rect(px, top - 8, 3, BASE - top + 8, 'D', 2.2, hgt=0.6)
            lay.rect(px, top - 8, 1, BASE - top + 8, 'D', 3.4)
            K.snowcap(lay, px, top - 8, 3, depth=2, seed=px)
            for yy in range(top + 2, BASE, 14):
                lay.px(px + 3, yy, 'P', 3.0)
        K.snowcap(lay, face_x0, top, b - face_x0, depth=2, seed=522)
        # the painted panel for the guest: cream ground, red border, red letters -- nothing crosses the letters
        px0, px1, py0, py1 = face_x0 + 2, 966, top + 8, top + 34
        lay.rect(px0 + 1, py1, px1 - px0, 1, 'N', 1.4)                     # its shadow on the canvas
        lay.rect(px0, py0, px1 - px0, py1 - py0, 'P', 4.4, hgt=0.3)
        lay.rect(px0, py0, px1 - px0, 2, 'R', 2.6)
        lay.rect(px0, py1 - 2, px1 - px0, 2, 'R', 2.6)
        K.text(lay, 'ВОССТАНОВИМ', (px0 + px1) // 2, py0 + 4, 'R', 3.2, font='57', center=True)
        K.text(lay, 'ВМЕСТЕ', (px0 + px1) // 2, py0 + 14, 'R', 3.2, font='57', center=True)
        for k in range(3):                                                 # paint runs from the border
            xx = px0 + 6 + k * 34
            lay.rect(xx, py1 - 1, 1, 2 + k, 'R', 2.6)
        for (cx_, cy_) in ((px0 + 1, py0 + 2), (px1 - 2, py0 + 2), (px0 + 1, py1 - 3), (px1 - 2, py1 - 3)):
            lay.rect(cx_, cy_, 2, 2, 'D', 3.0)                             # rope through the eyelets
        self.readable['tarpaulin_panel'] = [px0, py0, px1 - px0, py1 - py0]
        # the tear: a shovel's handle behind it (exp_tarpaulin_front)
        tx, ty = 898, 254
        lay.poly([(tx, ty), (tx + 4, ty + 2), (tx + 5, ty + 16), (tx + 1, ty + 14)], 'N', 0.8, hgt=-0.3)
        lay.line(tx + 2, ty + 1, tx + 3, ty + 15, 'D', 3.6)
        lay.line(tx - 1, ty, tx, ty + 15, 'Q', 3.4)
        # snow drifted against the foot
        for i in range(b - a):
            d = int(3 + 3 * math.sin(i / 9.0) + (i % 7 == 0))
            lay.rect(a + i, BASE - d + 2, 1, d, 'S', 3.4, hgt=0.4)

    # ------------------------------------------------------------------ the roundhouse front + the engine
    def roundhouse_front(self):
        lay = self.lay
        a, b = L.RH_FRONT
        top = 112
        K.brick_wall(lay, a, top, b - a, BASE - 6 - top, base=3.4, seed=531, soot=0.7)
        lay.rect(a - 2, top - 5, b - a + 4, 5, 'K', 2.0, hgt=0.7)
        K.snowcap(lay, a - 2, top - 5, b - a + 4, depth=3, seed=532)
        K.icicles(lay, a, b, top, seed=533, density=0.4, maxlen=7)
        # the stall arch, open: warm haze inside, the engine stands in front of it
        sa, sb = L.LOCO[0] - 4, L.LOCO[1] + 4
        arch = K.arch_mask(sb - sa + 10, 18, 16)
        lay.put(arch, sa - 5, 132, 'K', 2.4, hgt=0.6)
        inside = np.full((BASE - 148, sb - sa), 2.0, np.float32) - np.linspace(0, 1.4, BASE - 148)[:, None] * 0.7
        lay.put(np.ones_like(inside, bool), sa, 148, 'L', inside, emis=True, flat=False, hgt=-0.6)
        lay.rect(sa, 148, sb - sa, 3, 'L', 1.4, emis=True)
        # a big banner over the arch for the guest
        K.sign_plate(lay, a + 8, 118, b - a - 16, 11, bg=('R', 2.6), fg=('W', 5.0),
                     lines=('ДОБРО ПОЖАЛОВАТЬ',), border=False)
        # fir garlands along the arch, red flags on short poles (plain red)
        for k in range(0, sb - sa + 10, 3):
            u = k / float(sb - sa + 10)
            yy = 136 + int(10 * (2 * u - 1) ** 2)
            lay.px(sa - 5 + k, yy, 'G', 2.4 + (k % 2) * 0.6, hgt=0.6)
            lay.px(sa - 5 + k, yy + 1, 'G', 1.6)
        for fx_ in (a + 4, b - 6):
            lay.rect(fx_, 132, 1, 26, 'D', 3.0)
            lay.poly([(fx_ + 1, 132), (fx_ + 12, 135), (fx_ + 1, 140)], 'R', 3.0, hgt=0.5)
        # the emblem over the arch (insignia site)
        self.emblem((a + b) // 2, 98)
        # floodlight stands aimed at the engine (white light)
        for (sx, d) in ((a + 2, 1), (b - 2, -1)):
            lay.line(sx, BASE, sx + d * 4, 214, 'I', 2.0)
            lay.line(sx + d * 8, BASE, sx + d * 4, 214, 'I', 1.8)
            lay.poly([(sx + d * 0, 206), (sx + d * 9, 204), (sx + d * 10, 212), (sx + d * 1, 214)], 'I', 2.6,
                     hgt=0.7)
            lay.poly([(sx + d * 9, 205), (sx + d * 11, 205), (sx + d * 11, 211), (sx + d * 9, 212)], 'S', 6.0,
                     emis=True)
            self.L('flood_engine_%d' % d, sx + d * 10, 208, 'white', 1.25, 150, 30,
                   cone=(d * 0.85, 0.5, 0.45))
        self.L('stall_inside', (sa + sb) // 2, 200, 'warm', 0.6, 90, 8)

    def emblem(self, cx, cy):
        lay = self.lay
        hist = self.cfg.get('hist', False)
        lay.ellipse(cx, cy, 10, 10, 'L', 2.6, hgt=0.6)
        lay.ellipse(cx, cy, 8, 8, 'R', 2.2, hgt=0.5)
        if hist:
            pts = []
            for k in range(10):
                r = 7 if k % 2 == 0 else 3.0
                ang = -math.pi / 2 + k * math.pi / 5
                pts.append((cx + r * math.cos(ang), cy + r * math.sin(ang)))
            lay.poly(pts, 'R', 4.0, hgt=0.8)
            lay.line(cx - 3, cy + 2, cx + 2, cy - 3, 'L', 4.8)
            lay.line(cx - 2, cy - 2, cx + 3, cy + 3, 'L', 4.6)
        else:
            for k in range(12):
                ang = k * math.pi / 6
                lay.px(int(round(cx + 6 * math.cos(ang))), int(round(cy + 6 * math.sin(ang))), 'L', 4.2)
            lay.ellipse(cx, cy, 4, 4, 'L', 3.8, hgt=0.8)
            lay.ellipse(cx, cy, 1, 1, 'R', 2.0)
            for s in (-1, 1):
                for k in range(3):
                    lay.px(cx + s * (3 + k // 2), cy + 5 - k * 3, 'L', 4.8)

    def engine(self):
        """The polished engine head-on: cab sides, smoke deflectors, boiler, smokebox door with the wreath and
        the emblem (insignia site), headlamp lit, red buffer beam with the coupler and the brass plate „1939“,
        cylinders, the pony truck, red ribbons from the chimney."""
        lay = self.lay
        a, b = L.LOCO
        cx = (a + b) // 2
        # the cab behind (wider, dark green, the roof curved), its front sheet with the two spectacle windows,
        # the boiler's top running back to it: sand dome, steam dome, the whistle
        lay.rect(a - 4, 152, b - a + 8, 70, 'G', 1.2, hgt=0.5)
        for xx in range(a - 4, b + 4):
            u = (xx - cx) / ((b - a) / 2.0 + 4)
            yy = 150 - int(round(4 * (1 - u * u)))
            lay.rect(xx, yy, 1, 152 - yy + 1, 'V', 1.8, hgt=0.7)
            lay.px(xx, yy, 'S', 3.6)
        K.snowcap(lay, a - 2, 147, b - a + 4, depth=2, seed=541)
        lay.rect(a - 4, 152, 2, 70, 'G', 2.6)
        lay.rect(b + 2, 152, 2, 70, 'G', 0.8)
        for s in (-1, 1):
            wx = cx + s * 27
            lay.ellipse(wx, 166, 4, 4, 'G', 0.6, hgt=0.6)
            lay.ellipse(wx, 166, 3, 3, 'L', 3.2, emis=True)              # spectacle windows, the fire's glow
            lay.px(wx - 1, 165, 'L', 4.4, emis=True)
        lay.rect(cx - 9, 176, 19, 14, 'N', 1.6, hgt=0.7)                 # the boiler's top seen end-on
        lay.rect(cx - 9, 176, 19, 1, 'S', 3.4)
        lay.rect(cx + 7, 158, 6, 9, 'N', 2.2, hgt=0.8)                   # steam dome
        lay.rect(cx + 7, 157, 6, 1, 'L', 4.2)
        lay.rect(cx - 13, 160, 5, 7, 'N', 2.0, hgt=0.8)                  # sand dome
        lay.rect(cx - 13, 159, 5, 1, 'L', 4.0)
        lay.rect(cx + 9, 151, 2, 6, 'L', 4.0)                            # the whistle, brass
        lay.rect(cx + 8, 150, 4, 1, 'L', 4.8)
        for s in (-1, 1):                                                 # handrails round the smokebox, white
            hx_ = cx + s * 25
            lay.line(hx_, 190, hx_ + s * 2, 236, 'S', 5.2)
            lay.px(hx_ + s * 1, 212, 'R', 3.6)                             # ribbons tied to the handrails
            lay.px(hx_ + s * 2, 213, 'R', 3.2)
            lay.px(hx_ + s * 2, 214, 'R', 2.6)
        lay.rect(a + 4, 222, b - a - 8, 40, 'N', 1.0, hgt=0.4)              # the boiler's belly, the frames
        lay.rect(a + 10, 230, b - a - 20, 2, 'I', 1.8)
        # smoke deflectors
        for (dx0, dx1) in ((a, a + 6), (b - 6, b)):
            lay.rect(dx0, 178, dx1 - dx0, 72, 'N', 2.4, hgt=0.6)
            lay.rect(dx0 + (0 if dx0 == a else 5), 178, 1, 72, 'S', 4.6)
            K.snowcap(lay, dx0, 178, dx1 - dx0, depth=1, seed=dx0)
        # boiler / smokebox front
        lay.ellipse(cx, 214, 24, 25, 'N', 2.0, hgt=0.6)
        m, mx, my = lay.ellipse_mask(cx, 214, 21, 22)
        hh = m.shape[0]
        t = 1.8 + np.linspace(1.2, -0.6, hh, dtype=np.float32)[:, None] + np.zeros(m.shape, np.float32)
        xs = (np.arange(m.shape[1]) - m.shape[1] / 2.0)[None, :]
        t = t + np.clip(-xs / 10.0, -0.8, 0.8) * 0.6
        lay.put(m, mx, my, 'I', t, hgt=0.9, flat=False)
        rim = K.edge_of(m)
        lay.put(rim, mx, my, 'L', 4.2, hgt=1.0)                            # polished brass ring
        # the hinges and the dogs of the door
        for yy in (204, 224):
            lay.rect(cx - 21, yy, 7, 2, 'I', 4.4)
        lay.rect(cx + 15, 213, 4, 3, 'I', 5.0)
        # the fir wreath with a red ribbon round the emblem
        for k in range(40):
            ang = k / 40.0 * 2 * math.pi
            r = 11 + (k % 3) * 0.6
            lay.px(int(round(cx + r * math.cos(ang))), int(round(216 + r * math.sin(ang))), 'G',
                   2.2 + (k % 2) * 0.8, hgt=0.8)
            lay.px(int(round(cx + (r - 1) * math.cos(ang))), int(round(216 + (r - 1) * math.sin(ang))), 'G', 1.6)
        lay.rect(cx - 2, 227, 4, 3, 'R', 3.6)
        lay.line(cx - 1, 230, cx - 4, 238, 'R', 3.2)
        lay.line(cx + 1, 230, cx + 4, 238, 'R', 3.2)
        self.engine_emblem(cx, 216)
        # chimney, headlamp (lit), the marker lamps
        lay.rect(cx - 5, 170, 11, 18, 'N', 2.0, hgt=0.7)
        lay.rect(cx - 6, 168, 13, 3, 'N', 3.0, hgt=0.8)
        lay.rect(cx - 5, 170, 1, 18, 'S', 4.0)
        K.snowcap(lay, cx - 6, 168, 13, depth=1, seed=542)
        lay.rect(cx - 5, 186, 11, 7, 'I', 2.6, hgt=0.8)                    # headlamp housing
        lay.ellipse(cx, 189, 3, 3, 'S', 6.0, emis=True)
        self.headlamp = (cx, 189)
        self.L('headlamp', cx, 194, 'white', 0.9, 90, 30, cone=(0.0, 1.0, 0.2))
        for s in (-1, 1):
            lay.rect(cx + s * 30 - 2, 246, 4, 4, 'I', 2.4)
            lay.rect(cx + s * 30 - 1, 247, 2, 2, 'S', 5.6, emis=True)
        # red ribbons from the chimney to the deflectors, bows
        for s in (-1, 1):
            lay.line(cx + s * 5, 172, cx + s * 34, 186, 'R', 3.4)
            lay.line(cx + s * 5, 173, cx + s * 34, 187, 'R', 2.4)
            bx = cx + s * 34
            lay.rect(bx - 2, 184, 5, 3, 'R', 3.8)
            lay.line(bx, 187, bx + s * 2, 196, 'R', 3.0)
        # cylinders and the buffer beam
        for s in (-1, 1):
            x_ = cx + s * 33 - (6 if s < 0 else 0)
            lay.rect(x_, 236, 7, 18, 'N', 2.6, hgt=0.8)
            lay.rect(x_, 236, 7, 1, 'S', 4.0)
            lay.ellipse(x_ + 3, 245, 2, 5, 'I', 4.2)
        lay.rect(a - 2, 252, b - a + 4, 10, 'R', 2.8, hgt=0.9)
        lay.rect(a - 2, 252, b - a + 4, 1, 'R', 4.0)
        lay.rect(a - 2, 261, b - a + 4, 1, 'R', 1.2)
        lay.rect(cx - 4, 254, 8, 7, 'I', 2.2, hgt=0.9)                     # SA-3 coupler
        lay.rect(cx - 2, 256, 4, 3, 'I', 3.8)
        lay.rect(cx + 10, 254, 14, 6, 'L', 3.6, hgt=0.7)                   # the brass plate „1939“
        K.text(lay, '1939', cx + 17, 255, 'N', 1.2, center=True)
        self.readable['engine_plate_1939'] = [cx + 10, 254, 14, 6]
        for s in (-1, 1):                                                  # steps, white-edged
            lay.rect(cx + s * 28 - 3, 262, 7, 2, 'I', 3.0)
            lay.rect(cx + s * 28 - 3, 262, 7, 1, 'S', 5.0)
        # frame and the pony truck under the beam, white-rimmed red wheels
        lay.rect(a + 8, 262, b - a - 16, 22, 'N', 1.4, hgt=0.5)
        for s in (-1, 1):
            wx = cx + s * 14
            lay.ellipse(wx, 280, 6, 9, 'R', 2.0, hgt=0.8)
            lay.ellipse(wx, 280, 4, 7, 'R', 2.8, hgt=0.9)
            for k in range(-8, 9):
                yy = 280 + k
                xx = int(round(wx + 6 * math.sqrt(max(0.0, 1 - (k / 9.0) ** 2)) * (1 if s > 0 else -1)))
                lay.px(xx, yy, 'S', 5.0)
        lay.rect(a + 6, BASE - 2, b - a - 12, 2, 'I', 4.4)

    def engine_emblem(self, cx, cy):
        lay = self.lay
        if self.cfg.get('hist', False):
            pts = []
            for k in range(10):
                r = 7 if k % 2 == 0 else 2.8
                ang = -math.pi / 2 + k * math.pi / 5
                pts.append((cx + r * math.cos(ang), cy + r * math.sin(ang)))
            lay.poly(pts, 'R', 3.8, hgt=1.0)
            lay.line(cx - 2, cy + 2, cx + 2, cy - 2, 'L', 4.8)
            lay.line(cx - 2, cy - 2, cx + 2, cy + 2, 'L', 4.6)
        else:
            lay.ellipse(cx, cy, 6, 6, 'L', 3.0, hgt=1.0)
            for k in range(10):
                ang = k * math.pi / 5
                lay.px(int(round(cx + 6 * math.cos(ang))), int(round(cy + 6 * math.sin(ang))), 'L', 4.6)
            lay.ellipse(cx, cy, 3, 3, 'R', 2.6)
            lay.px(cx, cy, 'L', 4.8)

    # ------------------------------------------------------------------ the signal
    def signal(self):
        lay = self.lay
        x = L.SIGNAL
        top = 106
        lay.rect(x - 2, top, 5, BASE - top, 'I', 2.4, hgt=0.8)           # tubular mast
        lay.rect(x - 2, top, 1, BASE - top, 'S', 4.0)
        lay.rect(x + 2, top, 1, BASE - top, 'N', 1.6)
        for yy in range(top + 50, BASE - 10, 6):                          # ladder
            lay.rect(x + 4, yy, 5, 1, 'I', 3.0)
        lay.rect(x + 4, top + 50, 1, BASE - top - 60, 'I', 2.6)
        lay.rect(x + 8, top + 50, 1, BASE - top - 60, 'I', 2.6)
        # the head: black backing shield with a white border, three lenses under hoods (green lit)
        m = K.soft_box(16, 40, 5)
        lay.put(m, x - 8, top - 2, 'N', 1.0, hgt=0.8)
        lay.put(K.edge_of(m), x - 8, top - 2, 'S', 5.2, hgt=0.9)
        for k, (ramp, tone, lit) in enumerate((('G', 6.0, True), ('L', 1.0, False), ('R', 0.9, False))):
            cy = top + 5 + k * 11
            lay.ellipse(x, cy, 3, 3, ramp if lit else 'N', tone if lit else 0.6, emis=lit, hgt=0.9)
            if lit:
                lay.px(x, cy, 'G', 7.0, emis=True)
                lay.px(x - 1, cy - 1, 'G', 7.0, emis=True)
            else:
                lay.px(x - 1, cy - 1, ramp, tone + 1.0)
                lay.px(x + 1, cy + 1, ramp, tone)
            lay.rect(x - 4, cy - 5, 9, 2, 'N', 1.6, hgt=1.0)               # hood
        self.signal_lens = (x, top + 5)
        self.L('signal_green', x + 4, top + 8, 'cold', 0.5, 60, 10)
        # red bows for the press, the relay box, the number plate, the scratch at child height
        for (yy, s) in ((top + 64, 1), (top + 96, -1)):
            lay.rect(x - 3, yy, 7, 2, 'R', 3.6)
            lay.line(x + s * 3, yy + 2, x + s * 5, yy + 8, 'R', 3.0)
        lay.rect(x - 22, BASE - 22, 14, 22, 'I', 2.2, hgt=0.6)
        lay.rect(x - 22, BASE - 22, 14, 1, 'I', 3.6)
        lay.rect(x - 20, BASE - 18, 10, 1, 'I', 1.4)
        K.snowcap(lay, x - 22, BASE - 22, 14, depth=2, seed=551)
        K.sign_plate(lay, x - 4, top + 44, 9, 7, bg=('W', 5.0), fg=('N', 0.8), lines=('Н2',), border=False)
        lay.rect(x - 2, BASE - 12, 5, 12, 'K', 2.6, hgt=0.7)              # rust below the fresh paint
        lay.rect(x - 2, BASE - 12, 5, 1, 'S', 4.6)
        sx, sy = L.SIGNAL_SCRATCH
        for (dx_, dy_) in ((0, 0), (1, 1), (0, 2), (2, 0), (3, 2)):          # „А. М.“ scratched in
            lay.px(sx + dx_ - 2, sy + dy_, 'K', 4.6)
        # the lineman's box with a coil of galvanised signal wire (side task)
        lay.rect(998, BASE - 12, 14, 12, 'D', 2.6, hgt=0.6)
        lay.rect(998, BASE - 12, 14, 1, 'D', 3.8)
        K.snowcap(lay, 998, BASE - 12, 14, depth=1, seed=553)
        for k in range(3):
            lay.ellipse(1004, BASE - 16 + k, 4, 2, 'I', 4.2 + k * 0.3)
        lay.rect(1001, BASE - 16, 7, 1, 'S', 5.4)
        K.snowcap(lay, x - 8, top - 2, 16, depth=2, seed=552)

    # ------------------------------------------------------------------ the band stage
    def band_stage(self):
        lay = self.lay
        a, b = L.BAND
        top = 281
        K.planks(lay, a, top, b - a, BASE + 2 - top, 'D', 3.0, seed=561, pitch=3, vertical=False)
        lay.rect(a, top, b - a, 1, 'D', 4.4, hgt=0.7)
        for px in (a + 2, (a + b) // 2, b - 4):
            lay.rect(px, top + 3, 2, BASE + 2 - top - 3, 'D', 1.6)
        # bunting along the stage front
        for k in range(a, b - 3, 5):
            lay.poly([(k, top + 2), (k + 4, top + 2), (k + 2, top + 6)], 'R' if (k // 5) % 2 else 'P',
                     3.4 if (k // 5) % 2 else 4.6, hgt=0.6)
        # a string of bulbs over the stage between two poles
        for px in (a - 2, b + 2):
            lay.rect(px, 214, 2, top - 214, 'D', 2.6, hgt=0.6)
            K.snowcap(lay, px, 214, 2, depth=1, seed=px)
        pts = []
        for k in range(b - a + 5):
            u = k / float(b - a + 4)
            pts.append((a - 1 + k, 216 + 10 * 4 * u * (1 - u)))
        for i, (x, y) in enumerate(pts):
            lay.px(int(x), int(y), 'N', 1.4)
            if i % 6 == 3:
                lay.rect(int(x), int(y) + 1, 2, 2, 'L', 5.0, emis=True)
        self.L('bulbs', (a + b) // 2, 230, 'warm', 0.7, 80, 30, pool=0.4, pool_w=20, pool_spread=0.6,
               pool_depth=30)
        # a music stand, a drum case
        lay.rect(b - 10, top - 3, 8, 3, 'I', 2.0)

    # ------------------------------------------------------------------ the press canteen
    def canteen(self):
        lay = self.lay
        a, b = L.CANTEEN_B
        roof = 178
        # back wall: whitewashed plaster, warm, a dado of green oil paint
        K.tex_rect(lay, a + 6, roof + 8, b - a - 12, BASE - roof - 8, 'W', 3.4, seed=571, amp=0.3, cell=8)
        lay.rect(a + 6, 258, b - a - 12, BASE - 258, 'G', 2.6, hgt=0.3)
        lay.rect(a + 6, 258, b - a - 12, 1, 'G', 3.8)
        # roof in section, snow, the eaves
        lay.rect(a - 4, roof - 4, b - a + 8, 12, 'D', 1.6, hgt=0.6)
        lay.rect(a - 4, roof + 6, b - a + 8, 2, 'D', 0.8)
        lay.poly([(a - 6, roof - 4), (b + 6, roof - 4), (b + 2, roof - 12), (a - 2, roof - 12)], 'N', 2.0)
        K.snowcap(lay, a - 6, roof - 12, b - a + 12, depth=5, seed=572)
        K.icicles(lay, a - 4, b + 4, roof + 8, seed=573, density=0.3, maxlen=5)
        # the walls in section (left and right), the plank floor through the walk band
        for (wx, ww) in ((a, 6), (b - 6, 6)):
            K.brick_wall(lay, wx, roof + 8, ww, BASE - roof - 8, base=2.0, seed=wx, soot=0.2)
            lay.rect(wx, roof + 8, ww, 1, 'N', 1.6)
        lay.rect(a + 6, 236, 1, BASE - 236, 'N', 1.4)                     # door frame on the left
        K.planks(lay, a, BASE - 4, b - a, 6, 'D', 2.8, seed=574, pitch=6)
        # a back window: night outside, frost, a curtain
        K.window(lay, a + 30, 200, 20, 22, lit=False, rows=2, cols=2, seed=575, curtain=('R', 2.6, 'l'),
                 sill_snow=False)
        # a framed painting (a locomotive at a station), a wall clock, coat hooks with coats
        lay.rect(a + 60, 204, 18, 12, 'L', 2.6, hgt=0.5)
        lay.rect(a + 61, 205, 16, 10, 'G', 2.4)
        lay.rect(a + 63, 210, 10, 3, 'N', 1.6)
        lay.rect(a + 70, 207, 2, 3, 'N', 1.6)
        lay.ellipse(a + 92, 206, 4, 4, 'P', 5.0, hgt=0.6)
        lay.line(a + 92, 206, a + 92, 203, 'N', 1.0)
        lay.line(a + 92, 206, a + 94, 207, 'N', 1.0)
        for k, (rmp, t) in enumerate((('N', 2.0), ('Q', 2.4), ('M', 2.2))):
            hx_ = a + 12 + k * 6
            lay.px(hx_, 230, 'I', 3.6)
            lay.poly([(hx_ - 2, 231), (hx_ + 2, 231), (hx_ + 3, 252), (hx_ - 3, 252)], rmp, t, hgt=0.5)
        # ceiling lamps (frosted globes), lit
        for lx in (a + 32, a + 86):
            lay.rect(lx, roof + 8, 1, 10, 'N', 1.4)
            lay.ellipse(lx, roof + 21, 3, 3, 'P', 6.0, emis=True)
            self.L('canteen_%d' % lx, lx, roof + 22, 'warm', 1.0, 90, 14, pool=0.6, pool_w=14, pool_spread=0.6,
                   pool_depth=30)
        # the press table: white cloth, tea glasses in holders, bread with caviar, a vase, the guidebook
        ta, tb = L.TABLE
        ty = 266
        lay.rect(ta, ty, tb - ta, 2, 'P', 6.0, hgt=0.6)
        lay.rect(ta, ty + 2, tb - ta, 10, 'P', 5.4, hgt=0.5)
        for k in range(ta + 2, tb, 5):
            lay.line(k, ty + 3, k, ty + 11, 'P', 4.6)
        lay.rect(ta, ty + 12, tb - ta, 1, 'P', 4.0)
        for lx_ in (ta + 3, tb - 4):
            lay.rect(lx_, ty + 13, 2, BASE - 4 - ty - 13, 'D', 2.2)
        for k, gx in enumerate((ta + 4, ta + 22, ta + 30, ta + 40)):
            lay.rect(gx, ty - 5, 3, 5, 'L', 3.2 + (k % 2) * 0.6, hgt=0.8)  # tea in podstakanniki
            lay.rect(gx, ty - 5, 3, 1, 'S', 5.0)
            lay.rect(gx - 1, ty - 2, 5, 1, 'I', 4.4)
            lay.px(gx + 3, ty - 4, 'I', 4.0)
        for k, bx in enumerate((ta + 9, ta + 34)):
            lay.rect(bx - 1, ty - 1, 9, 1, 'P', 6.2)                       # plate
            for j in range(3):
                lay.rect(bx + j * 3, ty - 3, 2, 2, 'L', 3.8)              # bread
                cav = ('N', 0.8) if (j + k) % 2 == 0 else ('R', 2.6)       # black and red caviar
                lay.px(bx + j * 3, ty - 3, cav[0], cav[1])
                lay.px(bx + j * 3 + 1, ty - 3, cav[0], cav[1] + 0.6)
        lay.rect(ta + 26, ty - 8, 3, 7, 'S', 4.0)                          # vase with paper flowers
        for (fx_, fy_, rr) in ((ta + 25, ty - 10, 'R'), (ta + 28, ty - 11, 'L'), (ta + 27, ty - 9, 'P')):
            lay.rect(fx_, fy_, 2, 2, rr, 4.0)
        if not self.cfg.get('book_taken'):
            lay.rect(ta + 12, ty - 3, 10, 3, 'U', 3.0, hgt=0.8)            # the Swedish guidebook, closed
            lay.rect(ta + 12, ty - 3, 10, 1, 'U', 4.2)
            lay.rect(ta + 12, ty - 2, 1, 2, 'P', 5.0)
            lay.rect(ta + 15, ty - 3, 4, 1, 'L', 4.6)                      # gilt title
        for cx_ in (ta - 4, tb + 2):                                       # bentwood chairs
            lay.rect(cx_, ty - 8, 2, BASE - 4 - ty + 8, 'D', 2.0)
            lay.rect(cx_ - 1, ty + 4, 5, 2, 'D', 2.8)
            lay.rect(cx_ + 3, ty + 6, 1, BASE - 4 - ty - 6, 'D', 1.8)
        # the samovar on a side table
        sx_ = 1206
        lay.rect(sx_ - 5, 270, 12, 2, 'D', 3.0)
        lay.rect(sx_ - 4, 272, 2, BASE - 4 - 272, 'D', 2.0)
        lay.rect(sx_ + 4, 272, 2, BASE - 4 - 272, 'D', 2.0)
        for i in range(8):
            c = (i + 0.5) / 8 * 2 - 1
            lay.rect(sx_ - 4 + i, 256, 1, 13, 'L', 3.4 + 1.4 * (0.5 - abs(c + 0.3)), hgt=0.9)
        lay.rect(sx_ - 2, 252, 5, 4, 'L', 3.8)
        lay.rect(sx_ - 1, 249, 3, 3, 'L', 2.8)
        lay.rect(sx_ + 4, 262, 3, 1, 'L', 4.6)
        self.samovar = (sx_, 248)
        # the kitchen corner behind the pulled-back curtain: white tiles, a shelf of tin bowls, the range with the
        # band's kasha -- all inside the canteen's right wall (nothing pokes out toward the turntable)
        cu = L.CURTAIN
        ka, kb = L.KITCHEN_STOVE
        K.tex_rect(lay, cu + 9, roof + 14, ka - cu - 9 + (kb - ka), BASE - 4 - roof - 14, 'W', 3.9, seed=577, amp=0.2,
                   cell=3)
        for yy in range(roof + 16, BASE - 4, 4):
            lay.rect(cu + 9, yy, kb - cu - 9, 1, 'W', 3.0)
        for xx in range(cu + 11, kb, 4):
            lay.rect(xx, roof + 14, 1, BASE - 4 - roof - 14, 'W', 3.2)
        lay.rect(cu + 10, 240, kb - cu - 12, 1, 'D', 3.0, hgt=0.6)        # a shelf: tin bowls, a ladle, a jar
        for k in range(4):
            lay.rect(cu + 12 + k * 4, 236 - (k % 2), 3, 4 + (k % 2), 'S', 3.6 + (k % 2) * 0.4)
        lay.rect(kb - 6, 233, 3, 7, 'P', 3.6)
        lay.line(cu + 11, 230, cu + 13, 239, 'I', 4.2)
        rt = 268                                                           # the range: brick, iron top, fire door
        K.brick_wall(lay, ka, rt, kb - ka, BASE - 4 - rt, base=2.6, seed=578, soot=0.8)
        lay.rect(ka - 1, rt - 2, kb - ka + 2, 2, 'I', 3.0, hgt=0.8)
        lay.rect(ka - 1, rt - 2, kb - ka + 2, 1, 'I', 4.4)
        lay.rect(ka + 4, rt + 7, 8, 7, 'I', 1.4, hgt=0.6)
        lay.rect(ka + 5, rt + 8, 6, 5, 'L', 4.6, emis=True)
        lay.rect(ka + 5, rt + 10, 6, 1, 'L', 3.0, emis=True)
        lay.rect(ka + 2, rt - 11, kb - ka - 4, 9, 'I', 3.2, hgt=0.9)        # the big pot
        lay.rect(ka + 2, rt - 11, kb - ka - 4, 1, 'I', 5.0)
        lay.rect(ka + 1, rt - 9, 1, 2, 'I', 2.4)
        lay.rect(kb - 2, rt - 9, 1, 2, 'I', 2.4)
        lay.rect(ka + 3, rt - 12, kb - ka - 6, 1, 'P', 4.6)                # kasha in it
        lay.rect(kb - 3, rt - 18, 1, 8, 'D', 3.4)                          # the big spoon left in the pot
        self.kasha = ((ka + kb) // 2, rt - 12)
        self.L('kitchen_fire', ka + 8, rt + 10, 'warm', 0.6, 50, 6)
        lay.rect(cu - 2, roof + 12, 36, 1, 'I', 3.4)                       # the curtain, pulled back
        n = K.nz(10, BASE - roof - 16, 3, 576)
        for k in range(9):
            lay.rect(cu + k, roof + 13, 1, BASE - 6 - roof - 13, 'M', 2.6 + math.sin(k * 1.4) * 0.6 + n[5, k],
                     hgt=0.5)
        lay.rect(cu + 8, roof + 13, 1, BASE - 6 - roof - 13, 'M', 1.6)

    # ------------------------------------------------------------------ the turntable
    def turntable(self):
        lay = self.lay
        a, b = L.TURNTABLE
        # the pit rim and the circle rail in the ground
        lay.rect(a - 6, 284, b - a + 12, 6, 'C', 1.8, hgt=0.4)
        lay.rect(a - 6, 284, b - a + 12, 1, 'S', 3.4)
        lay.rect(a - 6, 289, b - a + 12, 1, 'I', 4.4)
        # the bridge girder (seen end-on) and the cabin on it
        lay.rect(a + 4, 270, b - a - 8, 14, 'I', 1.6, hgt=0.7)
        lay.rect(a + 4, 270, b - a - 8, 1, 'I', 3.6)
        for xx in range(a + 6, b - 6, 5):
            lay.line(xx, 271, xx + 4, 283, 'I', 2.6)
        for wx_ in (a + 7, b - 7):                                         # the running wheels on the circle rail
            lay.ellipse(wx_, 286, 3, 3, 'I', 2.2, hgt=0.8)
            lay.px(wx_, 286, 'I', 4.6)
            lay.px(wx_ - 1, 284, 'I', 4.0)
        ca, cb = a + 12, b - 14
        K.planks(lay, ca, 236, cb - ca, 34, 'D', 2.6, seed=581, pitch=4)
        lay.poly([(ca - 3, 236), (cb + 3, 236), (cb + 1, 230), (ca - 1, 230)], 'N', 2.2)
        K.snowcap(lay, ca - 3, 230, cb - ca + 6, depth=3, seed=582)
        K.window(lay, ca + 6, 244, 12, 10, lit=True, rows=1, cols=2, seed=583, frost=0.4)
        lay.rect(ca + 4, 262, 5, 2, 'D', 3.2)                             # his empty stool
        lay.rect(ca + 5, 264, 1, 6, 'D', 2.2)
        lay.rect(cb - 3, 220, 2, 12, 'I', 2.4)                            # stove pipe
        self.cabin_pipe = (cb - 2, 218)
        self.L('cabin', ca + 12, 250, 'warm', 0.7, 50, 6)
        # the drive lever and a red warning lamp on a post
        lay.line(cb + 2, 270, cb + 8, 254, 'I', 3.2)
        lay.rect(cb + 7, 252, 3, 3, 'R', 3.4)
        lay.rect(cb + 5, 249, 6, 2, 'U', 2.6)                              # the operator's cap on the controller
        lay.rect(cb + 6, 248, 4, 1, 'U', 3.2)
        lay.rect(cb + 10, 250, 2, 1, 'N', 1.4)
        lay.rect(b - 4, 238, 2, 46, 'I', 2.2)
        lay.rect(b - 5, 234, 4, 4, 'R', 4.6, emis=True)
        self.L('tt_red', b - 3, 236, 'warm', 0.3, 24, 4)

    # ------------------------------------------------------------------ the sand-drying house (cut open)
    def sandhouse(self):
        lay = self.lay
        a, b = L.SANDHOUSE
        roof = 184
        # back wall: limewashed brick, worn through only in a few broad places -- low down (boots, sacks, damp) and
        # round the stove (heat) -- with flaking edges; a grey-green oil-paint dado; soot climbing over the stove
        wx0, wy0, ww, wh = a + 8, roof + 10, b - a - 16, BASE - roof - 10
        K.brick_wall(lay, wx0, wy0, ww, wh, base=3.0, seed=591, soot=0.5, ramp='K')
        big = K.nz(ww, wh, 15, 592, octaves=2)
        fine = K.nz(ww, wh, 6, 594, octaves=2)
        ys_ = np.linspace(0, 1, wh, dtype=np.float32)[:, None]
        xs_ = np.arange(wx0, wx0 + ww, dtype=np.float32)[None, :]
        stove_c = (L.SAND_STOVE[0] + L.SAND_STOVE[1]) / 2.0
        wear = np.clip((ys_ - 0.7) * 2.5, 0, 1) * 0.22 + np.exp(-((xs_ - stove_c) / 20.0) ** 2) * 0.14
        lime = (big + 0.5) + fine * 0.12 - wear > 0.13
        lime = K.erode(K.dilate(lime, 1), 1)                                # no single-pixel chips
        lay.put(lime, wx0, wy0, 'W', 3.2 + fine * 0.3 - ys_ * 0.4, hgt=0.15, flat=False)
        inner = K.erode(np.ones_like(lime), 1)
        lay.put(K.edge_of(lime) & inner, wx0, wy0, 'W', 2.2, hgt=0.1)        # the flaking rim of the lime
        # soot climbing over the stove and its pipe: a soft smudge, darkest low and in the middle
        sx_c = stove_c + 4
        y_top = wy0
        for yy in range(y_top, 236):
            v = (yy - y_top) / float(236 - y_top)                          # 0 at the eaves, 1 at the stove top
            hw_ = 5.0 + (1 - v) * 9.0
            for xx in range(int(sx_c - hw_), int(sx_c + hw_) + 1):
                u = abs(xx - sx_c) / hw_
                if u < 1.0:
                    lay.tone[yy, xx] -= 0.75 * (1 - u * u) * (0.35 + 0.65 * v)
        lay.rect(wx0, 264, ww, BASE - 4 - 264, 'G', 2.0, hgt=0.2)           # the dado
        lay.rect(wx0, 264, ww, 1, 'G', 1.2)
        dn = K.nz(ww, BASE - 4 - 265, 4, 595)
        lay.put(dn > 0.32, wx0, 265, 'W', 2.6, hgt=0.1)                     # where it is knocked off
        # roof in section, the eaves, snow, a chimney with smoke
        lay.rect(a - 4, roof - 2, b - a + 8, 12, 'D', 1.6, hgt=0.6)
        lay.rect(a - 4, roof + 8, b - a + 8, 2, 'D', 0.8)
        lay.poly([(a - 6, roof - 2), (b + 6, roof - 2), (b + 2, roof - 10), (a - 2, roof - 10)], 'N', 2.2)
        K.snowcap(lay, a - 6, roof - 10, b - a + 12, depth=5, seed=593)
        K.icicles(lay, a - 4, b + 4, roof + 10, seed=594, density=0.35, maxlen=6)
        sa, sb = L.SAND_STOVE
        lay.rect(sa + 20, roof - 34, 7, 26, 'K', 2.6, hgt=0.7)
        lay.rect(sa + 19, roof - 36, 9, 3, 'K', 3.4)
        self.stove_chimney = (sa + 23, roof - 37)
        for (wx, ww) in ((a, 8), (b - 8, 8)):                            # walls in section
            K.brick_wall(lay, wx, roof + 10, ww, BASE - roof - 10, base=2.2, seed=wx, soot=0.3)
        lay.rect(a + 8, 232, 1, BASE - 232, 'N', 1.4)                      # door frame
        lay.rect(a, 228, 14, 4, 'D', 2.4, hgt=0.6)                         # lintel
        K.planks(lay, a, BASE - 4, b - a, 6, 'D', 2.4, seed=595, pitch=7)
        # the sand stove: a brick oven, an iron drying pan on top, the fire door glowing, sand heaps
        K.brick_wall(lay, sa, 238, sb - sa, BASE - 4 - 238, base=3.2, seed=596, soot=0.9)
        lay.rect(sa - 2, 234, sb - sa + 4, 5, 'I', 2.4, hgt=0.8)
        lay.rect(sa - 2, 234, sb - sa + 4, 1, 'I', 4.0)
        K.coal_heap(lay, (sa + sb) // 2, 234, sb - sa - 4, 6, seed=597, ramp='L')
        lay.shade_rect(sa, 228, sb - sa, 6, -1.0)
        lay.rect(sa + 16, 262, 12, 9, 'I', 1.4, hgt=0.6)
        lay.rect(sa + 17, 264, 10, 6, 'L', 4.6, emis=True)
        for k in range(4):
            lay.rect(sa + 17 + k * 3, 263, 1, 8, 'I', 1.8)
        self.stove_fire = (sa + 22, 266)
        self.L('sand_stove', sa + 22, 268, 'warm', 1.1, 90, 8, pool=0.7, pool_w=10, pool_spread=0.7,
               pool_depth=30)
        lay.rect(sa + 24, 194, 4, 40, 'I', 2.2, hgt=0.7)                   # stove pipe to the chimney
        hcx, hby = L.SAND_HEAP                                             # the dry sand heap (the cat's bed)
        K.coal_heap(lay, hcx, hby, 18, 7, seed=hcx, ramp='L')
        lay.shade_rect(hcx - 9, hby - 9, 18, 9, -1.4)
        lay.line(sb + 14, BASE - 4, sb + 20, 252, 'D', 3.0)              # a sieve and a shovel leaning
        lay.ellipse(sb + 20, 258, 5, 5, 'D', 2.6)
        lay.ellipse(sb + 20, 258, 3, 3, 'L', 1.8)
        # round sieves hanging on nails, the fire board (red: conical bucket, axe, hook, shovel), a wall phone, the
        # men's coats on their hooks, the plate „НЕ КУРИТЬ“ by the door (the smoker stands under it, of course)
        for k, (sx_, sy_, r_) in enumerate(((sb + 3, 206, 6), (sb + 13, 211, 5))):
            lay.ellipse(sx_, sy_, r_, r_, 'D', 3.0, hgt=0.7)
            lay.ellipse(sx_, sy_, r_ - 2, r_ - 2, 'I', 1.8, hgt=0.3)
            for j in range(-r_ + 3, r_ - 2, 2):
                lay.rect(sx_ + j, sy_ - r_ + 3, 1, 2 * r_ - 5, 'I', 2.4)
            lay.px(sx_, sy_ - r_ - 1, 'I', 4.0)
        fb_x, fb_y = L.SCALE[0] + 4, 212                                   # the fire board
        lay.rect(fb_x, fb_y, 22, 25, 'R', 2.2, hgt=0.4)
        lay.rect(fb_x, fb_y, 22, 1, 'R', 3.4)
        lay.rect(fb_x, fb_y + 24, 22, 1, 'R', 1.2)
        lay.poly([(fb_x + 2, fb_y + 3), (fb_x + 9, fb_y + 3), (fb_x + 5, fb_y + 11)], 'R', 3.8, hgt=0.8)   # bucket
        lay.rect(fb_x + 2, fb_y + 3, 8, 1, 'R', 4.6)
        lay.line(fb_x + 13, fb_y + 3, fb_x + 13, fb_y + 21, 'D', 3.6)       # the axe
        lay.rect(fb_x + 11, fb_y + 3, 5, 3, 'I', 4.0)
        lay.line(fb_x + 18, fb_y + 2, fb_x + 18, fb_y + 23, 'D', 3.2)       # the hook (bagor)
        lay.line(fb_x + 18, fb_y + 2, fb_x + 20, fb_y + 4, 'I', 3.8)
        lay.rect(fb_x + 2, fb_y + 15, 7, 6, 'I', 3.0)                      # a shovel blade
        lay.line(fb_x + 5, fb_y + 12, fb_x + 5, fb_y + 15, 'D', 3.4)
        K.sign_plate(lay, fb_x - 2, 201, 40, 8, bg=('W', 4.6), fg=('R', 2.2), lines=('НЕ КУРИТЬ',), border=True)
        lay.rect(a + 14, 238, 6, 9, 'N', 2.2, hgt=0.7)                     # the wall phone by the door
        lay.rect(a + 15, 237, 4, 2, 'N', 3.0)
        lay.rect(a + 14, 241, 1, 4, 'N', 1.2)
        lay.px(a + 17, 243, 'L', 3.6)
        lay.line(a + 16, 247, a + 18, 256, 'N', 1.4)
        for k, (rmp, t, ln) in enumerate((('Q', 2.2, 22), ('M', 2.4, 19))):      # the men's coats on their hooks
            hx_ = fb_x + 26 + k * 6
            lay.px(hx_, 230, 'I', 4.2)
            lay.poly([(hx_ - 2, 231), (hx_ + 2, 231), (hx_ + 3, 231 + ln), (hx_ - 3, 231 + ln)], rmp, t, hgt=0.5)
            lay.rect(hx_ - 2, 231, 5, 1, rmp, t + 0.8)
        lay.rect(fb_x + 24, 227, 5, 2, 'U', 2.6)                           # a cap on the first hook
        # the box the sifted sand runs into
        bx_ = L.SAND_SIEVE - 20
        lay.rect(bx_, BASE - 12, 16, 8, 'D', 2.6, hgt=0.6)
        lay.rect(bx_, BASE - 12, 16, 1, 'D', 3.8)
        lay.rect(bx_ + 1, BASE - 13, 14, 1, 'L', 3.4)
        K.coal_heap(lay, bx_ + 8, BASE - 12, 12, 2, seed=bx_, ramp='L')
        # the platform sack scale with its weighing beam, sand sacks stacked beside it (side task)
        ca, cb = L.SCALE
        lay.rect(ca, BASE - 8, cb - ca, 4, 'I', 2.8, hgt=0.7)
        lay.rect(ca, BASE - 8, cb - ca, 1, 'I', 4.4)
        lay.rect(cb - 4, 250, 2, BASE - 8 - 250, 'I', 2.6)
        lay.rect(cb - 16, 250, 14, 2, 'I', 3.6)
        lay.rect(cb - 11, 248, 3, 2, 'I', 4.6)
        for k in range(3):
            lay.rect(ca + 2 + k * 3, BASE - 11 - k, 2, 3 + k, 'I', 3.4)
        for k in range(3):                                                 # sand sacks
            yy = BASE - 7 - k * 6
            K.tex_rect(lay, cb + 1 + (k % 2) * 2, yy, 14, 6, 'P', 3.2, seed=600 + k, amp=0.4, cell=2)
            lay.rect(cb + 1 + (k % 2) * 2, yy, 14, 1, 'P', 4.2)
        # the workbench: vice, tools on the wall, shelves with tins, a calendar, the back window
        ba, bb = L.BENCH
        ty = 264
        lay.rect(ba, ty, bb - ba, 3, 'D', 3.6, hgt=0.7)
        lay.rect(ba, ty, bb - ba, 1, 'D', 4.8)
        lay.rect(ba, ty + 3, bb - ba, 3, 'D', 2.0)
        for lx_ in (ba + 2, bb - 5):
            lay.rect(lx_, ty + 6, 3, BASE - 4 - ty - 6, 'D', 2.2)
        lay.rect(ba + 4, ty + 18, bb - ba - 8, 2, 'D', 2.0)                # shelf under the bench
        for k in range(5):
            lay.rect(ba + 6 + k * 6, ty + 13, 4, 5, 'I', 2.4 + (k % 2) * 0.8)
        lay.rect(bb - 12, ty - 6, 8, 6, 'I', 2.6, hgt=0.8)                # vice
        lay.rect(bb - 14, ty - 4, 2, 2, 'I', 3.6)
        for k, (tx_, tl) in enumerate(((ba + 6, 12), (ba + 12, 9), (ba + 17, 14), (ba + 24, 8))):
            lay.rect(tx_, 236, 1, tl, 'I', 3.2 + (k % 2) * 0.6)            # tools hanging
        lay.rect(ba + 4, 234, 26, 1, 'D', 2.6)
        K.window(lay, ba + 34, 210, 18, 18, lit=False, rows=2, cols=2, seed=598, sill_snow=False, frost=0.8)
        lay.rect(a + 22, 214, 30, 2, 'D', 3.0)                             # shelves with tins
        lay.rect(a + 22, 228, 30, 2, 'D', 3.0)
        for k in range(6):
            lay.rect(a + 24 + k * 5, 208, 3, 6, ('I', 'R', 'G')[k % 3], 3.0)
            lay.rect(a + 24 + k * 5, 222, 3, 6, ('L', 'I', 'P')[k % 3], 3.2)
        lay.rect(b - 30, 214, 10, 14, 'P', 5.0, hgt=0.4)                   # a wall calendar
        lay.rect(b - 30, 214, 10, 4, 'R', 2.8)
        K.pseudo_text(lay, b - 29, 220, 8, 3, 'N', 2.0, seed=599)
        # what lies on the bench (story states)
        if self.cfg.get('joined'):
            # the whole card, perforation teeth closed, the round stamp complete across the cut
            lay.rect(ba + 14, ty - 3, 24, 3, 'P', 5.6, hgt=0.8)
            lay.px(ba + 26, ty - 3, 'P', 4.0)
            lay.rect(ba + 24, ty - 3, 5, 2, 'R', 3.0)
            lay.px(ba + 26, ty - 2, 'P', 5.6)
        elif self.cfg.get('halves'):
            lay.rect(ba + 8, ty - 3, 10, 2, 'U', 3.2, hgt=0.8)             # the guidebook, open
            lay.rect(ba + 9, ty - 4, 8, 1, 'P', 5.4)
            lay.rect(ba + 22, ty - 3, 11, 3, 'P', 5.4, hgt=0.8)            # the Russian half
            lay.rect(ba + 22, ty - 3, 2, 2, 'R', 3.0)
        # the green-shaded lamp over the bench (lit)
        lx_, ly_ = L.GREEN_LAMP
        lay.rect(lx_, roof + 10, 1, ly_ - roof - 14, 'N', 1.4)
        lay.poly([(lx_ - 6, ly_), (lx_ + 7, ly_), (lx_ + 3, ly_ - 5), (lx_ - 2, ly_ - 5)], 'G', 3.4, hgt=0.8)
        lay.rect(lx_ - 6, ly_, 14, 1, 'G', 5.4)
        lay.rect(lx_ - 1, ly_ + 1, 3, 2, 'L', 5.0, emis=True)
        self.L('green_lamp', lx_, ly_ + 3, 'warm', 1.25, 74, 14, cone=(0.0, 1.0, 0.25), pool=0.6, pool_w=10,
               pool_spread=0.5, pool_depth=26)

    def gate(self):
        lay = self.lay
        a, b = L.GATE
        for px in (a + 2, b - 8):
            K.brick_wall(lay, px, 222, 8, BASE - 222, base=3.0, seed=px, soot=0.4)
            lay.rect(px - 1, 218, 10, 4, 'C', 2.8, hgt=0.7)
            K.snowcap(lay, px - 1, 218, 10, depth=3, seed=px + 1)
        for k in range(6):                                                 # the gate leaf, swung open
            lay.rect(a + 11 + k * 2, 234 + k, 1, BASE - 236 - k * 2, 'I', 2.4)
        lay.rect(a + 10, 234, 12, 1, 'I', 3.0)
        lay.rect(a + 10, 262, 12, 1, 'I', 2.6)
        # an iron bracket stands on the two pillars: two posts, a crossbar with scrolled ends and stays; the sign is
        # bolted to the posts' front, the two clocks hang from the crossbar -- the station clock (local time 19.10)
        # and a smaller one with its plate „КОР. ВРЕМЯ“ (Corridor time, 17.10, two hours behind)
        pl, pr = a + 5, b - 4
        top = 168
        for px_ in (pl, pr):
            lay.rect(px_ - 1, top, 2, 218 - top, 'I', 2.4, hgt=0.7)
            lay.rect(px_ - 1, top, 1, 218 - top, 'I', 3.6)
        lay.rect(pl - 6, top - 1, pr - pl + 12, 2, 'I', 2.8, hgt=0.8)
        lay.rect(pl - 6, top - 1, pr - pl + 12, 1, 'I', 4.0)
        for s, px_ in ((-1, pl), (1, pr)):
            lay.px(px_ + s * 6, top + 1, 'I', 2.6)                          # scrolled ends
            lay.px(px_ + s * 5, top + 2, 'I', 2.6)
            lay.line(px_, top + 7, px_ + s * 4, top + 1, 'I', 2.2)           # stays
        K.snowcap(lay, pl - 6, top - 1, pr - pl + 12, depth=2, seed=b)
        c1, c2 = L.CLOCKS
        for (cx_, cy_, r_, hh, mm) in ((c1, 181, 7, 19, 10), (c2, 179, 5, 17, 10)):
            lay.rect(cx_, top + 1, 1, cy_ - r_ - top - 1, 'I', 2.0)        # the hanger
            lay.ellipse(cx_, cy_, r_ + 1, r_ + 1, 'I', 1.6, hgt=0.8)
            lay.ellipse(cx_, cy_, r_, r_, 'P', 6.0, emis=True)
            for k in range(12):                                            # hour marks
                ang = k * math.pi / 6
                lay.px(int(round(cx_ + (r_ - 1) * math.cos(ang))), int(round(cy_ + (r_ - 1) * math.sin(ang))), 'P',
                       4.4, emis=True)
            ah = math.radians((hh % 12) * 30 + mm * 0.5 - 90)
            am = math.radians(mm * 6 - 90)
            lay.line(cx_, cy_, int(round(cx_ + (r_ - 3) * math.cos(ah))), int(round(cy_ + (r_ - 3) * math.sin(ah))),
                     'N', 0.8)
            lay.line(cx_, cy_, int(round(cx_ + (r_ - 1) * math.cos(am))), int(round(cy_ + (r_ - 1) * math.sin(am))),
                     'N', 0.8)
            self.L('clock_%d' % cx_, cx_, cy_, 'cold', 0.35, 26, 6)
        K.sign_plate(lay, c2 - 11, 187, 23, 12, bg=('W', 4.8), fg=('N', 1.0), lines=('КОР.', 'ВРЕМЯ'), border=False)
        sw = 42
        sx0 = (a + b) // 2 - sw // 2
        K.sign_plate(lay, sx0, 202, sw, 14, bg=('U', 2.8), fg=('W', 5.0), lines=('ВЫХОД', 'НА ПЕРРОН'), border=False)
        lay.rect(sx0, 216, sw, 1, 'N', 1.2)
        self.readable['gate_clocks'] = [c1 - 8, 173, c2 + 6 - (c1 - 8), 16]
        self.readable['gate_corridor_plate'] = [c2 - 11, 187, 23, 12]
        self.readable['gate_sign'] = [sx0, 202, sw, 14]

    # ------------------------------------------------------------------ platform 1 and the express
    def platform(self):
        lay = self.lay
        a = L.PLATFORM[0]
        # benches, a luggage pile, a litter bin, a lamp column foot -- leave x 1676-1722 free (side task NPC)
        for (bx, bw) in ((1806, 22),):
            lay.rect(bx, 278, bw, 2, 'D', 3.2, hgt=0.6)
            lay.rect(bx, 270, bw, 2, 'D', 2.8)
            lay.rect(bx + 2, 280, 1, 12, 'I', 2.0)
            lay.rect(bx + bw - 3, 280, 1, 12, 'I', 2.0)
            K.snowcap(lay, bx, 270, bw, depth=1, seed=bx)
        for k, (lx_, lw_, lh_, rmp, t) in enumerate(((1622, 12, 8, 'K', 2.6), (1626, 9, 6, 'P', 3.0),
                                                      (1862, 10, 7, 'M', 2.8))):
            yy = BASE - lh_ - (6 if k == 1 else 0)
            lay.rect(lx_, yy, lw_, lh_, rmp, t, hgt=0.7)
            lay.rect(lx_, yy, lw_, 1, rmp, t + 1.0)
            lay.rect(lx_ + lw_ // 2 - 1, yy - 1, 3, 1, 'N', 1.6)
        lay.rect(1752, 282, 6, 10, 'I', 2.4, hgt=0.6)                      # litter bin
        lay.rect(1752, 282, 6, 1, 'I', 3.8)

    def express(self):
        """The westbound Corridor express behind the platform edge: the sleeping car (its vestibule door =
        express_door), the bellows, the dining car."""
        lay = self.lay
        a, b = L.PLATFORM[0] - 4, W
        floor = 286
        roof = 196
        body_top = 202
        # car body: dark green, a cream band under the windows, the roof
        lay.rect(a, body_top, b - a, floor - body_top, 'G', 2.0, hgt=0.6)
        K.tex_rect(lay, a, body_top, b - a, floor - body_top, 'G', 2.0, seed=601, amp=0.15, cell=10)
        lay.rect(a, 248, b - a, 3, 'P', 3.6, hgt=0.6)
        lay.rect(a, body_top, b - a, 1, 'G', 3.0)
        lay.rect(a, floor - 4, b - a, 4, 'N', 1.6)
        lay.vgrad(a, roof, b - a, body_top - roof, 'V', 2.4, 1.6, hgt=0.7)
        K.snowcap(lay, a, roof, b - a, depth=3, seed=602)
        for xx in range(a, b, 30):                                         # roof vents
            lay.rect(xx + 12, roof - 4, 5, 4, 'V', 2.0)
            K.snowcap(lay, xx + 12, roof - 4, 5, depth=1, seed=xx)
        # the gap between the cars (bellows) at the vestibule door's right
        ga = L.EXPRESS_DOOR[1] + 4
        lay.rect(ga, body_top + 2, 10, floor - body_top - 6, 'N', 1.0, hgt=-0.4)
        for k in range(5):
            lay.rect(ga + 1, body_top + 4 + k * 14, 8, 2, 'N', 2.0)
        # sleeping car: windows (lit, curtains), the vestibule door with its steps and handrails
        da, db = L.EXPRESS_DOOR
        for wx in range(a + 8, da - 14, 22):
            self._car_window(wx, 216, 14, 20, seed=wx)
        lay.rect(da, 210, db - da, floor - 210, 'G', 1.6, hgt=0.5)
        lay.rect(da, 210, db - da, 1, 'G', 3.2)
        lay.rect(da + 4, 216, db - da - 8, 16, 'L', 3.6, emis=True)        # door window, warm
        lay.rect(da + 4, 223, db - da - 8, 1, 'G', 1.6)
        for s in (da - 2, db + 1):
            lay.rect(s, 214, 1, 64, 'S', 5.0)                               # handrails
        for k in range(2):
            lay.rect(da - 1, floor + k * 4, db - da + 2, 2, 'I', 3.0)
        self.L('express_door_win', (da + db) // 2, 224, 'warm', 0.8, 50, 8)
        # the lettering runs on the letterboard ABOVE the windows (y 203-213), over the heads of everybody on the
        # platform: the route board „БЕРЛИН – КАРСК“ on its brackets, „СПАЛЬНЫЙ ВАГОН“, the car number
        ly = L.LETTERBOARD_Y
        for (sa_, sb_) in ((a, da - 3), (ga + 10, b)):                       # the letterboard, a shade lighter
            lay.rect(sa_, ly, sb_ - sa_, 11, 'G', 2.3, hgt=0.5)
            lay.rect(sa_, ly + 11, sb_ - sa_, 1, 'G', 1.2)
        rb_x, rb_w = a + 16, 66
        lay.rect(rb_x - 1, ly + 1, rb_w + 2, 10, 'N', 1.4)                   # the board's shadow / brackets
        K.sign_plate(lay, rb_x, ly, rb_w, 10, bg=('P', 4.2), fg=('G', 1.4), lines=('БЕРЛИН – КАРСК',), border=True)
        for bx in (rb_x + 4, rb_x + rb_w - 5):
            lay.rect(bx, ly - 1, 1, 2, 'I', 4.0)
        sp_x = rb_x + rb_w + 10
        sp_w = K.text(lay, 'СПАЛЬНЫЙ ВАГОН', sp_x, ly + 3, 'P', 4.6)
        no_x = sp_x + sp_w + 6
        no_w = K.text(lay, '07', no_x, ly + 3, 'P', 4.8)
        self.readable['express_route_board'] = [rb_x, ly, rb_w, 10]
        self.readable['express_sleeping_car'] = [sp_x, ly + 2, sp_w, 6]
        self.readable['express_car_number'] = [no_x, ly + 3, no_w, 5]
        # dining car: big windows with table lamps
        for wx in range(ga + 14, b, 26):
            self._car_window(wx, 214, 20, 24, seed=wx, dining=True)
        dc_x = ga + 34
        dc_w = K.text(lay, 'ВАГОН-РЕСТОРАН', dc_x, ly + 3, 'P', 4.6)
        self.readable['express_dining_car'] = [dc_x, ly + 3, dc_w, 5]
        for (nm, (x_, y_, w_, h_)) in list(self.readable.items()):
            if nm.startswith('express_'):
                assert all(not (c - 3 <= x_ + w_ and x_ <= c + 3) for c in L.CANOPY_COLUMNS), \
                    '%s crossed by a canopy column' % nm
        # underframe shadow below the platform edge is hidden; a little steam from the heating
        self.steam_points = [(a + 30, floor - 2), (ga + 6, floor - 4), (b - 60, floor - 2)]

    def _car_window(self, x, y, w, h, seed=0, dining=False):
        lay = self.lay
        rng = np.random.default_rng(abs(seed))
        lay.rect(x - 1, y - 1, w + 2, h + 2, 'G', 1.2, hgt=0.4)
        t = np.full((h, w), 3.8, np.float32) - np.linspace(0, 1.0, h, dtype=np.float32)[:, None]
        lay.put(np.ones((h, w), bool), x, y, 'L', t, emis=True, flat=False, hgt=-0.3)
        lay.rect(x, y, w, 1, 'L', 2.4, emis=True)
        lay.rect(x, y + h // 2, w, 1, 'G', 1.6)                            # the drop-window rail
        if dining:
            for k in range(2):
                lx_ = x + 4 + k * 10
                lay.rect(lx_, y + h - 9, 3, 3, 'L', 5.0, emis=True)        # table lamps
                lay.rect(lx_ + 1, y + h - 6, 1, 3, 'L', 2.0, emis=True)
            if rng.random() < 0.7:
                lay.rect(x + 8, y + 6, 4, 7, 'L', 1.4, emis=True)          # a diner
                lay.rect(x + 9, y + 4, 3, 2, 'L', 1.2, emis=True)
        else:
            lay.rect(x, y, 3, h, 'P', 4.6, emis=True)                      # curtains
            lay.rect(x + w - 3, y, 3, h, 'P', 4.6, emis=True)
            if rng.random() < 0.6:
                hx = x + 4 + int(rng.integers(0, max(1, w - 8)))
                lay.rect(hx, y + 7, 4, h - 7, 'L', 1.6, emis=True)         # a passenger
                lay.rect(hx, y + 4, 3, 3, 'L', 1.4, emis=True)
        self.windows.append((x, y, w, h))
        self.L('car_win_%d' % x, x + w // 2, y + h // 2, 'warm', 0.45, 34, 6)

    def canopy(self):
        lay = self.lay
        a, b = L.PLATFORM[0], W
        top = L.CANOPY_Y - 12
        lay.rect(a - 6, top, b - a + 6, 10, 'I', 1.8, hgt=0.6)
        lay.rect(a - 6, top + 9, b - a + 6, 2, 'I', 1.0)
        lay.rect(a - 6, top, b - a + 6, 1, 'I', 3.2)
        K.snowcap(lay, a - 6, top, b - a + 6, depth=4, seed=611)
        K.icicles(lay, a - 6, b, top + 11, seed=612, density=0.4, maxlen=7)
        for k in range(a + 4, b, 8):                                       # the valance (wooden fretwork)
            lay.poly([(k, top + 10), (k + 6, top + 10), (k + 3, top + 14)], 'D', 2.2)
        for cx in L.CANOPY_COLUMNS:
            lay.rect(cx - 2, top + 11, 5, BASE - top - 11, 'I', 2.0, hgt=0.8)  # cast-iron columns
            lay.rect(cx - 2, top + 11, 1, BASE - top - 11, 'I', 3.6)
            lay.rect(cx - 4, BASE - 6, 9, 6, 'I', 1.6)
            lay.rect(cx - 5, top + 11, 11, 3, 'I', 2.6)
            lay.line(cx + 2, top + 18, cx + 14, top + 11, 'I', 2.2)           # brackets
            lay.line(cx - 2, top + 18, cx - 14, top + 11, 'I', 2.2)
        for lx in (a + 76, a + 196, a + 300):                              # cold lamps under the canopy
            lay.rect(lx, top + 11, 1, 6, 'N', 1.4)
            K.lamp_head(lay, lx, top + 19, 'enamel', True, ramp_glow='S')
            self.L('canopy_%d' % lx, lx, top + 21, 'cold', 1.1, 110, 30, pool=0.9, pool_w=14, pool_spread=0.9,
                   pool_depth=50)

    def sky_lights(self):
        for i, x in enumerate(range(800, 2000, 260)):
            self.lights.append(K.light('sky_%d' % i, x, -260, 'cold', 0.22, 760, 300, falloff=1.0))

    def all_lights(self):
        return list(self.lights)
