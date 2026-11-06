"""env_c4p2_karsk_yard -- scene A of L_C4P2_Karsk: the back yard of the Karsk locomotive depot, Monday 17 February
1964, 6.10 (documentation/C4P2_DESIGN.md 4.1).

Left -> right: the yard lamp and a stack of sleepers, the red fire board, Irina's dispatch office (brick lean-to,
lit window with the typed order on the sill, the duty blackboard, the padded door), the canteen's back (serving
hatch with the kasha pot and the radio, a lit window upstairs), the water crane with its brazier, the coal stage
(timber trestle, the deck with a gondola being emptied, three chutes, the special run's tender under them, the stair,
the list post with Lena's mitten), the floodlight mast, the ash pit, the guard's fire barrel, the roundhouse's back
(two stall doors -- one ajar with steam and the warm stall -- the back door with the press notice, the old banner
„ВОССТАНОВИМ ВМЕСТЕ“ patched with sacking, the emblem on the gable), the back of the tarpaulin.

Painted into a full-width TLayer (world coordinates), cropped to SPAN[A] by the assembly.  The figures of Kolonne 4
are life strips (env_c4p2_karsk_people.py); the speaking people (Irina, Maria, the guard) stand at the npcs anchors.
"""
from __future__ import annotations

import math

import numpy as np

import env_c4p2_karsk_kit as K
import env_c4p2_karsk_layout as L

W, H = L.WORLD_W, L.WORLD_H


class Yard:
    """cfg: order_taken (c4e_inspect_order done), hist (historical insignia)."""

    def __init__(self, cfg: dict):
        self.cfg = dict(cfg)
        self.lay = K.tlayer(W, H, 'yard_a')
        self.lights: list = []
        self.rng = np.random.default_rng(4170)
        self.readable: dict = {}           # story text the art must keep readable: name -> [x, y, w, h] (scene.json)

    # ------------------------------------------------------------------ helpers
    def L(self, *a, **kw):
        self.lights.append(K.light(*a, **kw))

    # ------------------------------------------------------------------ build
    def build(self):
        lay = self.lay
        x0, x1 = L.SPAN[L.SA]
        self.back_fence(x0, x1)
        self.ground(x0, x1)
        self.roundhouse()
        self.flood_mast()
        self.tender()
        self.coal_stage()
        self.canteen()
        self.dispatch()
        self.water_crane()
        self.yard_left()
        self.ash_pit()
        self.barrel()
        self.tarp_back()
        self.near_track(x0, x1)
        self.clutter()
        self.sky_lights()
        # nothing of the other place
        lay.erase(x1, 0, W - x1, H)
        return self

    # ------------------------------------------------------------------ back of the yard
    def back_fence(self, x0, x1):
        """Concrete-post plank fence along the back of the yard (y 252-284), the far world shows above it."""
        lay = self.lay
        y0, y1 = 254, L.A_BACK
        K.planks(lay, x0, y0, x1 - x0, y1 - y0, 'D', 2.2, seed=11, pitch=4, vertical=True, var=0.4)
        lay.shade_rect(x0, y0, x1 - x0, 4, -0.6)
        for x in range(x0 + 6, x1, 46):
            lay.rect(x, y0 - 4, 4, y1 - y0 + 4, 'C', 2.6, hgt=0.6)
            lay.rect(x, y0 - 4, 1, y1 - y0 + 4, 'C', 3.4)
            K.snowcap(lay, x, y0 - 4, 4, depth=2, seed=x)
        K.snowcap(lay, x0, y0, x1 - x0, depth=2, seed=12, drift=0.6)
        # a ripped poster and a stencilled number on the fence
        lay.rect(250, 262, 12, 9, 'P', 2.4, hgt=0.3)
        K.pseudo_text(lay, 251, 264, 10, 3, 'N', 1.6, seed=3)
        lay.rect(250, 268, 5, 3, 'D', 2.0)
        K.worn_text(lay, '17', 660, 262, 'W', 3.6, wear=0.3, seed=5)

    def ground(self, x0, x1):
        """Compacted snow over cinders: broad soft variation, a trodden path of cinders and slush along the walk
        band, coal dust greying the snow round the stage, sparse lumps, footprint trails."""
        lay = self.lay
        top = L.A_BACK
        w, h = x1 - x0, H - top
        yy = np.linspace(0, 1, h, dtype=np.float32)[:, None]
        n_big = K.nz(w, h, 26, 21, octaves=2)
        n_mid = K.nz(w, h, 7, 22, octaves=2)
        t = 2.3 + n_big * 0.8 + n_mid * 0.3 - yy * 0.2
        lay.put(np.ones((h, w), bool), x0, top, 'S', t, hgt=0.3, flat=False)
        # the trodden path (y 292-312): cinders and grey slush, edges ragged
        pn = K.nz(w, 24, 5, 23, octaves=3)
        pr = np.abs(np.linspace(-1, 1, 24, dtype=np.float32))[:, None]
        mk = (pn + 0.5) * 1.1 - pr * 0.75 > 0.22
        lay.put(mk, x0, 290, 'S', 1.6 + pn * 0.8, hgt=0.15, flat=False)
        lay.put(mk & (pn < -0.12), x0, 290, 'E', 3.4 + pn, hgt=0.1, flat=False)
        # coal dust greying the snow round the stage and the ash pit
        for (a, b, k) in ((416, 626, 1.0), (606, 700, 0.6), (372, 420, 0.45)):
            nn = K.nz(b - a, h, 9, a, octaves=2)
            u = np.abs(np.linspace(-1, 1, b - a, dtype=np.float32))[None, :]
            f = np.clip((1 - u * u) * k * (1.1 - yy) + nn * 0.5, 0, 1)
            sub = lay.tone[top:top + h, a:b]
            rid = lay.rid[top:top + h, a:b]
            ms = rid == K.R['S']
            sub[ms] -= f[ms] * 1.8
        rng = np.random.default_rng(24)
        for _ in range(140):                                               # lumps of coal, sparse
            x = int(rng.integers(400, 700))
            y = int(rng.integers(top + 2, H - 4))
            if rng.random() < 0.7:
                lay.rect(x, y, 1 + int(rng.random() < 0.3), 1, 'X', 2.0 + rng.random(), hgt=0.6)
        for (sx, ex, y0, step) in ((20, 380, 300, 7), (60, 860, 316, 9), (400, 700, 296, 6), (180, 520, 340, 8)):
            k = 0
            for x in range(sx, ex, step):                                  # footprint trails (pairs)
                yy_ = y0 + int(2 * math.sin(x * 0.07)) + (2 if k % 2 else 0)
                lay.rect(x, yy_, 2, 1, 'S', 2.2, hgt=0.1)
                k += 1
        # frozen puddles (ice, a cold sheen)
        for (px, py, rx) in ((160, 318, 16), (330, 332, 12), (720, 324, 20), (520, 346, 14)):
            m_, mx, my = lay.ellipse_mask(px, py, rx, 3)
            lay.put(m_, mx, my, 'S', 2.0, hgt=-0.1)
            lay.rect(px - rx // 2, py - 1, rx // 2, 1, 'S', 4.6)
        # the coaling track at the back (rail heads side-on at y 288, sleeper ends under it)
        for x in range(L.STAGE[0] - 20, L.ROUNDHOUSE[0] - 4, 9):
            lay.rect(x, 290, 6, 2, 'D', 1.6, hgt=0.3)
        lay.rect(L.STAGE[0] - 20, 288, L.ROUNDHOUSE[0] - L.STAGE[0] + 16, 2, 'I', 4.0, hgt=0.7)
        lay.rect(L.STAGE[0] - 20, 288, L.ROUNDHOUSE[0] - L.STAGE[0] + 16, 1, 'I', 5.6, hgt=0.8)

    def near_track(self, x0, x1):
        """A siding in front of the walk path (rails y 324 / 338), half under trodden snow."""
        lay = self.lay
        for x in range(x0 - 4, x1, 11):
            k = self.rng.random()
            lay.poly([(x, 322), (x + 6, 322), (x + 8, 342), (x + 1, 342)], 'D', 2.2 + k * 0.6, hgt=0.4)
            if k < 0.75:
                lay.poly([(x, 322), (x + 6, 322), (x + 7, 330), (x + 1, 330)], 'S', 3.4 + k, hgt=0.5)
        for (yr, t) in ((323, 4.4), (337, 4.8)):
            lay.rect(x0, yr, x1 - x0, 3, 'I', t - 1.4, hgt=0.8)
            lay.rect(x0, yr, x1 - x0, 1, 'I', t + 1.0, hgt=0.9)
        # snow drifted over the rails in places
        for (a, b) in ((100, 170), (430, 470), (690, 760)):
            nn = K.nz(b - a, 4, 5, a)[0]
            for i in range(b - a):
                d = int(2 + 3 * math.sin(math.pi * i / (b - a)) + nn[i] * 2)
                lay.rect(a + i, 336 - d, 1, d + 3, 'S', 3.8 + nn[i], hgt=0.5)

    # ------------------------------------------------------------------ the left edge
    def yard_left(self):
        lay = self.lay
        lx, ly = L.LAMP_A
        # lamp post: wooden pole with a bracket, enamel shade
        lay.rect(lx - 1, ly - 4, 3, L.A_MID - ly + 4, 'D', 2.2, hgt=0.6)
        lay.rect(lx - 1, ly - 4, 1, L.A_MID - ly + 4, 'D', 3.2)
        lay.rect(lx, ly - 6, 10, 1, 'I', 2.0)
        lay.line(lx, ly + 4, lx + 6, ly - 5, 'I', 1.8)
        K.lamp_head(lay, lx + 9, ly, 'enamel', True)
        K.wire(lay, lx, ly - 6, L.DISPATCH[0] + 10, 206, 6)
        self.L('lamp_yard', lx + 9, ly + 2, 'warm', 1.1, 110, 22, pool=0.9, pool_w=8, pool_spread=0.6, pool_depth=48)
        # stack of sleepers (old, tarred)
        a, b = L.SLEEPERS
        for k in range(5):
            y = L.A_MID - 5 * (k + 1)
            off = (k % 2) * 3
            lay.rect(a + off, y, b - a - 3, 5, 'D', 1.6 + (k % 2) * 0.5, hgt=0.6)
            lay.rect(a + off, y, b - a - 3, 1, 'D', 2.6)
            for e in (a + off, b - 4 + off):
                lay.rect(e, y + 1, 1, 3, 'D', 0.8)
        K.snowcap(lay, a + 3, L.A_MID - 25, b - a - 3, depth=3, seed=31)
        # the fire board (пожарный щит): red board on posts, hooks, buckets, an axe, a sand box
        fa, fb = L.FIRE_SHIELD
        lay.rect(fa, 226, fb - fa, 3, 'D', 2.0, hgt=0.5)
        for px in (fa + 2, fb - 4):
            lay.rect(px, 226, 2, L.A_MID - 226, 'D', 1.8, hgt=0.5)
        lay.rect(fa + 1, 230, fb - fa - 2, 30, 'R', 2.2, hgt=0.4)
        lay.rect(fa + 1, 230, fb - fa - 2, 1, 'R', 3.2)
        lay.rect(fa + 1, 259, fb - fa - 2, 1, 'R', 1.2)
        for (bx, by) in ((fa + 4, 236), (fa + 13, 236)):                 # two conical red buckets
            lay.poly([(bx, by), (bx + 6, by), (bx + 3, by + 7)], 'R', 3.6, hgt=0.6)
            lay.rect(bx, by, 7, 1, 'R', 4.6)
        lay.rect(fa + 4, 248, 16, 1, 'I', 3.0)                            # hook pole
        lay.line(fa + 20, 248, fa + 22, 246, 'I', 3.0)
        lay.rect(fa + 5, 252, 8, 2, 'D', 3.4)                             # axe
        lay.rect(fa + 12, 251, 3, 4, 'I', 4.4)
        lay.rect(fa, 270, fb - fa, 22, 'R', 1.8, hgt=0.5)                 # sand box
        lay.rect(fa, 270, fb - fa, 1, 'R', 2.8)
        K.text(lay, 'ПЕСОК', (fa + fb) // 2, 278, 'W', 4.4, center=True)
        K.snowcap(lay, fa, 226, fb - fa, depth=2, seed=33)
        K.snowcap(lay, fa, 270, fb - fa, depth=2, seed=34)

    # ------------------------------------------------------------------ Irina's dispatch office
    def dispatch(self):
        lay = self.lay
        a, b = L.DISPATCH
        top = 214
        K.brick_wall(lay, a, top, b - a, L.A_MID - top, base=3.4, seed=41, soot=0.5)
        # plinth, corner pilasters, eaves
        lay.rect(a, L.A_MID - 8, b - a, 8, 'C', 2.4, hgt=0.5)
        lay.rect(a, L.A_MID - 8, b - a, 1, 'C', 3.4)
        for px in (a, b - 4):
            lay.rect(px, top, 4, L.A_MID - 8 - top, 'K', 3.0, hgt=0.6)
            lay.rect(px, top, 1, L.A_MID - 8 - top, 'K', 4.2)
        lay.rect(a - 4, top - 6, b - a + 8, 6, 'D', 1.6, hgt=0.6)         # eaves board
        lay.rect(a - 4, top - 6, b - a + 8, 1, 'D', 2.8)
        lay.poly([(a - 6, top - 6), (b + 6, top - 6), (b + 2, top - 13), (a - 2, top - 11)], 'N', 2.4, hgt=0.4)
        K.snowcap(lay, a - 6, top - 11, b - a + 12, depth=4, seed=42, drift=-1.0)
        K.icicles(lay, a - 4, b + 4, top, seed=43, density=0.35, maxlen=6)
        # stove pipe
        lay.rect(b - 18, top - 34, 4, 24, 'I', 2.6, hgt=0.7)
        lay.rect(b - 18, top - 34, 1, 24, 'I', 3.8)
        lay.rect(b - 20, top - 36, 8, 3, 'I', 2.0)
        self.stovepipe_top = (b - 16, top - 37)
        # the window: warm, the samovar and the telephone against the glow
        wx, wy, ww, wh = L.DISPATCH_WIN
        K.window(lay, wx, wy, ww, wh, lit=True, rows=2, cols=3, frame=('D', 2.6), glass=('L', 4.2), seed=44,
                 curtain=('L', 3.0, 'r'), frost=0.6)
        # interior silhouettes against the lit glass (emissive darker shapes)
        lay.rect(wx + 25, wy + 13, 6, 9, 'L', 1.4, emis=True)             # samovar body
        lay.rect(wx + 26, wy + 10, 4, 3, 'L', 1.8, emis=True)
        lay.rect(wx + 27, wy + 8, 2, 2, 'L', 1.2, emis=True)
        lay.rect(wx + 4, wy + 18, 8, 4, 'L', 1.2, emis=True)              # telephone
        lay.rect(wx + 5, wy + 16, 6, 2, 'L', 0.8, emis=True)
        lay.rect(wx + 14, wy + 4, 10, 6, 'L', 2.2, emis=True)             # duty roster on the back wall
        lay.rect(wx + 1, wy + 1, ww - 2, 1, 'L', 4.8, emis=True)
        if not self.cfg.get('order_taken'):                               # the carbon on the inside sill
            lay.rect(wx + 14, wy + wh - 4, 13, 3, 'P', 5.0, emis=True)
            lay.rect(wx + 15, wy + wh - 3, 10, 1, 'U', 3.4, emis=True)
            lay.px(wx + 22, wy + wh - 4, 'P', 3.2, emis=True)
        self.L('win_dispatch', wx + ww // 2, wy + wh // 2 + 6, 'warm', 0.95, 70, 6, pool=0.7, pool_w=10,
               pool_spread=0.7, pool_depth=40)
        # Irina's duty roster on its board: a heading, seven name strips, one with a fresh red pencil line, a
        # pencil on a string (exp_duty_board)
        bx, by, bw, bh = L.DUTY_BOARD
        lay.rect(bx - 1, by - 1, bw + 2, bh + 2, 'D', 2.2, hgt=0.5)
        lay.rect(bx, by, bw, bh, 'D', 3.4, hgt=0.4)
        lay.rect(bx + 1, by + 1, bw - 2, 3, 'U', 2.4)
        lay.rect(bx + 3, by + 2, bw - 6, 1, 'W', 4.6)
        rng = np.random.default_rng(45)
        for i in range(7):
            yy = by + 6 + i * 2
            lay.rect(bx + 1, yy, bw - 2, 1, 'P', 5.0, crisp=True)
            ln = int(rng.integers(5, bw - 6))
            lay.rect(bx + 2, yy, ln, 1, 'N', 2.0, crisp=True)
            if i == 4:
                lay.rect(bx + 1, yy, bw - 2, 1, 'R', 3.6, crisp=True)
        lay.line(bx + bw, by + 4, bx + bw + 2, by + 14, 'N', 1.6)        # the string
        lay.rect(bx + bw + 2, by + 14, 1, 5, 'L', 3.6)                     # the pencil
        # the padded door (oilcloth over felt, studs), a step, a bell box
        dx, dy, dw, dh = L.DISPATCH_DOOR
        lay.rect(dx - 2, dy - 2, dw + 4, dh + 2, 'D', 1.8, hgt=0.6)
        lay.rect(dx, dy, dw, dh, 'M', 1.6, hgt=0.4)
        for yy in range(dy + 3, dy + dh - 2, 6):                           # studded quilting
            for xx in range(dx + 2, dx + dw - 1, 4):
                lay.px(xx + ((yy // 6) % 2) * 2, yy, 'L', 3.0)
        lay.rect(dx + dw - 4, dy + dh // 2, 2, 3, 'L', 3.6)                # handle
        lay.rect(dx - 4, L.A_MID - 3, dw + 8, 3, 'C', 2.6, hgt=0.5)       # step
        K.snowcap(lay, dx - 4, L.A_MID - 3, dw + 8, depth=1, seed=46)
        lay.rect(dx + dw + 4, dy + 2, 5, 6, 'R', 1.6, hgt=0.6)            # bell box
        lay.rect(dx + dw + 5, dy + 3, 3, 3, 'I', 3.0)
        # wall details: thermometer, a loudspeaker horn, a wire, a nameplate
        lay.rect(a + 8, 240, 2, 12, 'P', 4.4, hgt=0.5)
        lay.px(a + 8, 250, 'R', 3.6)
        K.sign_plate(lay, 100, 222, 32, 9, bg=('U', 2.4), fg=('W', 4.6), lines=('ДИСПЕТЧЕР',), border=False)
        lay.poly([(b - 34, 222), (b - 24, 220), (b - 24, 228), (b - 34, 226)], 'I', 3.2, hgt=0.7)  # horn
        lay.rect(b - 36, 222, 3, 5, 'I', 2.0)
        K.wire(lay, b - 36, 224, b + 30, 196, 4)

    # ------------------------------------------------------------------ the canteen's back
    def canteen(self):
        lay = self.lay
        a, b = L.CANTEEN
        top = 156
        # plastered brick, two storeys, peeling to the brick in places
        K.tex_rect(lay, a, top, b - a, L.A_BACK - top, 'W', 2.4, seed=51, amp=0.35, cell=6)
        pe = K.nz(b - a, L.A_BACK - top, 7, 52)
        peel = (pe > 0.22)
        lay.put(peel, a, top, 'K', 3.0, hgt=0.1)
        K.brick_wall(lay, a, top, b - a, L.A_BACK - top, base=3.0, seed=53, soot=0.4, mask=peel)
        lay.rect(a, L.A_BACK - 10, b - a, 10, 'C', 2.2, hgt=0.5)
        lay.rect(a, top + 52, b - a, 2, 'W', 3.4, hgt=0.6)                # cornice between the storeys
        lay.rect(a - 3, top - 6, b - a + 6, 6, 'N', 2.6, hgt=0.6)         # roof edge
        K.snowcap(lay, a - 3, top - 6, b - a + 6, depth=5, seed=54)
        K.icicles(lay, a - 2, b + 2, top, seed=55, density=0.4, maxlen=8)
        # upstairs: one lit window (the kitchen staff's room), one dark, a ventilation duct with steam
        K.window(lay, a + 14, top + 16, 20, 26, lit=True, rows=2, cols=2, seed=56, curtain=('P', 3.6, 'both'))
        K.window(lay, a + 62, top + 16, 20, 26, lit=False, rows=2, cols=2, seed=57)
        self.L('win_canteen_up', a + 24, top + 30, 'warm', 0.6, 46, 6)
        lay.rect(b - 18, top + 6, 10, 8, 'I', 2.4, hgt=0.6)               # vent grille
        for k in range(4):
            lay.rect(b - 17, top + 7 + 2 * k, 8, 1, 'I', 1.0)
        self.vent = (b - 13, top + 4)
        # drainpipe with an ice beard
        lay.rect(a + 4, top, 3, L.A_BACK - top - 4, 'I', 2.6, hgt=0.7)
        lay.rect(a + 4, top, 1, L.A_BACK - top - 4, 'I', 3.8)
        lay.ellipse(a + 5, L.A_BACK - 6, 5, 4, 'S', 4.6, hgt=0.6)
        # the serving hatch
        hx, hy, hw, hh = L.HATCH
        lay.rect(hx - 3, hy - 4, hw + 6, hh + 8, 'D', 2.0, hgt=0.6)
        lay.rect(hx - 3, hy - 4, hw + 6, 1, 'D', 3.2)
        t = np.full((hh, hw), 3.6, np.float32) - np.linspace(0, 1.2, hh)[:, None]
        lay.put(np.ones((hh, hw), bool), hx, hy, 'L', t, emis=True, flat=False, hgt=-0.4)
        # inside: shelves with tins, the radio with its lit dial, the kasha pot on the counter
        lay.rect(hx + 2, hy + 4, hw - 4, 1, 'L', 1.6, emis=True)
        for k in range(6):
            lay.rect(hx + 3 + k * 5, hy + 1, 3, 3, 'L', 2.2 + (k % 3) * 0.4, emis=True)
        lay.rect(hx + 28, hy + 6, 9, 6, 'L', 1.2, emis=True)              # radio cabinet
        lay.rect(hx + 29, hy + 7, 4, 3, 'L', 5.0, emis=True)              # its dial
        lay.rect(hx + 34, hy + 7, 2, 4, 'L', 0.8, emis=True)              # speaker cloth
        lay.rect(hx - 4, hy + hh, hw + 8, 4, 'D', 3.0, hgt=0.7)           # counter board
        lay.rect(hx - 4, hy + hh, hw + 8, 1, 'D', 4.4)
        lay.rect(hx + 6, hy + hh - 7, 12, 7, 'I', 3.4, hgt=0.8)           # kasha pot
        lay.rect(hx + 6, hy + hh - 7, 12, 1, 'I', 5.0)
        lay.rect(hx + 4, hy + hh - 6, 2, 2, 'I', 2.4)
        lay.rect(hx + 18, hy + hh - 6, 2, 2, 'I', 2.4)
        lay.rect(hx + 22, hy + hh - 3, 5, 3, 'P', 4.6)                    # a stack of tin bowls
        lay.rect(hx + 22, hy + hh - 3, 5, 1, 'S', 5.0)
        self.pot = (hx + 12, hy + hh - 8)
        self.L('hatch', hx + hw // 2, hy + hh // 2, 'warm', 1.15, 80, 8, pool=0.9, pool_w=14, pool_spread=0.8,
               pool_depth=46)
        # a sign over the hatch, a bin with empty bottles, a cat-flap, crates
        K.sign_plate(lay, hx + 2, hy - 13, hw - 4, 8, bg=('W', 4.4), fg=('R', 2.0), lines=('РАЗДАЧА',), border=False)
        self.readable['hatch_sign'] = [hx + 2, hy - 13, hw - 4, 8]
        for k in range(3):
            K.crate(lay, b - 26 + k * 2, L.A_BACK - 10 - k * 8, 18, 8, seed=59 + k, snow=(k == 2))
            for j in range(4):
                lay.rect(b - 23 + k * 2 + j * 4, L.A_BACK - 13 - k * 8, 2, 4, 'G', 3.4)
        K.barrel(lay, a + 10, L.A_BACK - 18, 12, 18, 'I', 2.6, seed=60, snow=True)

    # ------------------------------------------------------------------ the water crane
    def water_crane(self):
        lay = self.lay
        x = L.WATER_CRANE
        base = L.A_BACK
        lay.rect(x - 7, base - 8, 15, 8, 'C', 2.4, hgt=0.6)              # plinth
        lay.rect(x - 7, base - 8, 15, 1, 'C', 3.6)
        for i in range(7):                                                # cast-iron column
            c = (i + 0.5) / 7 * 2 - 1
            lay.rect(x - 3 + i, 168, 1, base - 8 - 168, 'I', 3.0 + 1.4 * (0.45 - abs(c + 0.3)),
                     hgt=0.8 * math.sqrt(1 - c * c))
        for yy in (200, 236, base - 14):
            lay.rect(x - 4, yy, 9, 2, 'I', 4.4, hgt=0.9)
        lay.rect(x - 5, 162, 11, 6, 'I', 3.2, hgt=0.8)                    # head
        lay.rect(x - 2, 158, 5, 4, 'I', 2.6)
        # the swinging arm (turned along the track), a leather hose with an ice beard
        lay.rect(x + 3, 164, 34, 4, 'I', 3.0, hgt=0.7)
        lay.rect(x + 3, 164, 34, 1, 'I', 4.6)
        lay.line(x + 4, 170, x + 22, 165, 'I', 2.6)
        lay.rect(x + 35, 166, 5, 24, 'D', 1.6, hgt=0.6)
        lay.rect(x + 35, 166, 1, 24, 'D', 2.8)
        for k in range(5):
            lay.px(x + 36 + (k % 2), 190 + k, 'S', 4.8 - k * 0.3)
        lay.rect(x - 8, 174, 4, 2, 'R', 3.0)                               # the red handwheel
        lay.rect(x - 7, 172, 2, 6, 'R', 2.4)
        K.tex_rect(lay, x - 4, 198, 9, 54, 'L', 2.2, seed=64, amp=0.6, cell=1.5)     # straw lagging
        for yy in range(198, 252, 4):
            lay.rect(x - 4, yy, 9, 1, 'D', 2.4)
        K.tex_rect(lay, x - 4, 214, 9, 14, 'P', 1.8, seed=65, amp=0.4, cell=2)    # a sack tied round it
        lay.rect(x - 4, 214, 9, 1, 'D', 1.6)
        lay.rect(x - 4, 227, 9, 1, 'D', 1.6)
        lay.rect(x + 2, 163, 4, 6, 'P', 2.6)                              # rags + wire at the swivel joint
        lay.px(x + 3, 162, 'I', 4.6)
        lay.px(x + 5, 168, 'I', 4.6)
        K.snowcap(lay, x - 5, 158, 11, depth=3, seed=61)
        K.snowcap(lay, x + 3, 164, 34, depth=2, seed=62)
        K.icicles(lay, x + 3, x + 37, 168, seed=63, density=0.5, maxlen=6)
        # ice frozen around the foot, the brazier that keeps it from freezing
        mk, mx, my = lay.ellipse_mask(x, base, 16, 4)
        lay.put(mk, mx, my, 'S', 4.2, hgt=0.4)
        bx = x + 12
        lay.poly([(bx - 6, base - 12), (bx + 6, base - 12), (bx + 4, base - 4), (bx - 4, base - 4)], 'I', 1.6,
                 hgt=0.7)
        for k in range(4):
            lay.px(bx - 4 + k * 3, base - 9, 'L', 5.0, emis=True)
        lay.rect(bx - 5, base - 13, 11, 2, 'L', 4.0, emis=True)
        for lx in (bx - 4, bx + 3):
            lay.rect(lx, base - 4, 1, 4, 'I', 2.0)
        self.brazier = (bx, base - 13)
        self.L('brazier', bx, base - 14, 'warm', 0.7, 44, 6, pool=0.5, pool_w=6, pool_spread=0.4, pool_depth=24)

    # ------------------------------------------------------------------ the coal stage
    def coal_stage(self):
        lay = self.lay
        a, b = L.STAGE
        dy = L.DECK_Y
        posts = list(range(a + 4, b, 40))
        # the gondola being emptied on the deck track
        ga, gb = a + 66, b - 10
        gt = dy - 34
        lay.rect(ga, gt, gb - ga, 30, 'V', 1.4, hgt=0.6)                   # steel sides (dark red-brown)
        K.tex_rect(lay, ga, gt, gb - ga, 30, 'K', 2.2, seed=71, amp=0.35, cell=5)
        for xx in range(ga + 4, gb, 12):                                  # stakes
            lay.rect(xx, gt, 2, 30, 'K', 1.4, hgt=0.7)
            lay.rect(xx, gt, 1, 30, 'K', 3.2)
        lay.rect(ga, gt, gb - ga, 2, 'K', 3.6, hgt=0.8)
        lay.rect(ga, gt + 28, gb - ga, 2, 'K', 1.2)
        K.worn_text(lay, '64 172', ga + 8, gt + 10, 'W', 4.0, wear=0.2, seed=72)
        K.worn_text(lay, 'УГОЛЬ', ga + 8, gt + 18, 'W', 3.6, wear=0.3, seed=73)
        for k in range(2):                                                # bogies on the deck rail
            bx = ga + 10 + k * (gb - ga - 34)
            lay.rect(bx, dy - 4, 24, 3, 'I', 1.6, hgt=0.6)
            for w_ in (bx + 4, bx + 16):
                lay.ellipse(w_ + 2, dy - 2, 3, 3, 'I', 2.2, hgt=0.8)
        K.coal_heap(lay, (ga + gb) // 2 + 6, gt + 2, gb - ga - 14, 14, seed=74, glint=0.06, snow=0.2)
        # the deck: heavy beam band + plank edge + hand rail
        lay.rect(a - 2, dy, b - a + 4, 8, 'D', 2.0, hgt=0.7)
        lay.rect(a - 2, dy, b - a + 4, 1, 'D', 3.6)
        for xx in range(a, b, 6):
            lay.rect(xx, dy + 1, 1, 6, 'D', 1.2)
        lay.rect(a - 2, dy + 8, b - a + 4, 3, 'D', 1.2, hgt=0.5)
        lay.rect(a - 2, dy - 2, b - a + 4, 2, 'I', 3.6, hgt=0.8)          # deck rail
        for xx in range(a, ga - 4, 12):                                   # hand rail on the open part
            lay.rect(xx, dy - 12, 2, 12, 'D', 2.2, hgt=0.6)
        lay.rect(a, dy - 12, ga - a - 4, 2, 'D', 2.8, hgt=0.6)
        K.snowcap(lay, a, dy - 12, ga - a - 4, depth=2, seed=75)
        K.coal_heap(lay, a + 40, dy - 1, 44, 9, seed=76, glint=0.06)     # coal on the deck by the stair
        # posts and bracing
        for i, px in enumerate(posts):
            K.grain(lay, px, dy + 11, 6, L.A_MID - dy - 11, 'D', 2.6, seed=80 + i, amp=0.3)
            lay.rect(px, dy + 11, 1, L.A_MID - dy - 11, 'D', 3.6)
            lay.rect(px + 5, dy + 11, 1, L.A_MID - dy - 11, 'D', 1.4)
            lay.rect(px - 2, L.A_MID - 6, 10, 6, 'C', 2.2, hgt=0.5)       # footing
            K.snowcap(lay, px - 2, L.A_MID - 6, 10, depth=2, seed=90 + i)
        for i in range(len(posts) - 1):
            p, q = posts[i] + 5, posts[i + 1]
            for (ya, yb) in ((dy + 14, dy + 58), (dy + 58, dy + 14)):
                for t_ in range(3):
                    lay.line(p, ya + t_, q, yb + t_, 'D', 2.0 + 0.4 * t_)
            lay.rect(p, dy + 58, q - p, 3, 'D', 2.2, hgt=0.6)
            for (bx, by_) in ((p + 1, dy + 15), (q - 2, dy + 15), (p + 1, dy + 57)):
                lay.px(bx, by_, 'I', 4.4)
        K.icicles(lay, a, b, dy + 11, seed=99, density=0.25, maxlen=5)
        # the chutes (sheet steel, raised on chains)
        for cx in L.CHUTES:
            lay.poly([(cx - 9, dy + 10), (cx + 9, dy + 10), (cx + 13, dy + 42), (cx + 1, dy + 46)], 'I', 2.4,
                     hgt=0.7)
            lay.line(cx - 9, dy + 10, cx + 1, dy + 46, 'I', 3.8)
            lay.line(cx + 9, dy + 10, cx + 13, dy + 42, 'I', 1.4)
            lay.line(cx + 12, dy + 40, cx + 14, dy + 12, 'I', 1.0)
            for k in range(6):
                lay.px(cx + 14, dy + 12 + k * 5, 'I', 3.0)
            K.rust_streak(lay, cx + 2, dy + 22, 14, seed=cx, ramp='K', tone=3.0)
            lay.rect(cx - 2, dy + 40, 6, 3, 'X', 2.6)                     # coal caught in the lip
        # bulb under the deck
        lx = (L.CHUTES[0] + L.CHUTES[1]) // 2
        lay.rect(lx, dy + 11, 1, 6, 'N', 1.4)
        K.lamp_head(lay, lx, dy + 20, 'enamel', True)
        self.L('deck_bulb', lx, dy + 22, 'warm', 0.9, 70, 10, pool=0.0)
        # the stair to the deck
        sa, sb = L.STAIR
        for k in range(14):
            y = L.A_MID - 8 - k * 8
            xx = sa + 2 + (k * (sb - sa - 6)) // 14
            if y < dy:
                break
            lay.rect(xx, y, 10, 2, 'D', 3.0, hgt=0.6)
            lay.rect(xx, y, 10, 1, 'D', 4.0)
            K.snowcap(lay, xx + 1, y, 8, depth=1, seed=100 + k)
        lay.line(sa, L.A_MID, sa + (sb - sa - 6) + 2, dy + 2, 'D', 2.2)
        lay.line(sa + 1, L.A_MID, sa + (sb - sa - 6) + 3, dy + 2, 'D', 1.6)
        lay.line(sa + 12, L.A_MID - 10, sb + 6, dy - 10, 'D', 3.0)        # hand rail
        # the list post: a squared post at the foot of the stair, the board, the cellophane, a pencil on string
        px = L.LIST_POST
        lay.rect(px - 2, 238, 4, L.A_MID - 238, 'D', 2.4, hgt=0.6)
        lay.rect(px - 2, 238, 1, L.A_MID - 238, 'D', 3.6)
        lay.rect(px - 8, 244, 16, 18, 'D', 1.6, hgt=0.5)
        lay.rect(px - 7, 245, 14, 16, 'P', 4.0, hgt=0.4)
        K.pseudo_text(lay, px - 6, 247, 12, 6, 'N', 1.8, seed=101, gap=2)
        lay.rect(px - 7, 245, 14, 1, 'S', 5.6, crisp=True)                # cellophane sheen
        lay.line(px - 7, 252, px - 3, 248, 'S', 5.0)
        lay.line(px + 7, 258, px + 9, 270, 'N', 1.2)                       # string
        lay.rect(px + 8, 270, 1, 5, 'L', 3.6)                              # pencil
        K.snowcap(lay, px - 8, 244, 16, depth=2, seed=102)
        # an extra strut under the deck; Lena's mitten nailed to it at knee height (hidden find)
        sx_ = L.STRUT
        K.grain(lay, sx_ - 2, dy + 11, 5, L.A_MID - dy - 11, 'D', 2.2, seed=103, amp=0.3)
        lay.rect(sx_ - 2, dy + 11, 1, L.A_MID - dy - 11, 'D', 3.4)
        lay.rect(sx_ - 4, L.A_MID - 5, 9, 5, 'C', 2.0, hgt=0.5)
        mx, my = L.MITTEN
        mk = np.array([[0, 1, 1, 1, 0], [1, 1, 1, 1, 0], [1, 1, 1, 1, 1], [1, 1, 1, 1, 1], [1, 1, 1, 1, 0],
                       [0, 1, 1, 0, 0]], bool)
        lay.put(mk, mx - 2, my - 3, 'C', 3.4, hgt=0.6)
        lay.rect(mx - 1, my + 3, 3, 1, 'W', 5.0)                           # cuff with the name tape
        lay.px(mx, my - 3, 'I', 4.8)                                       # the nail
        lay.px(mx + 2, my - 1, 'C', 4.6)

    def tender(self):
        """The special run's tender under the chutes (black, a red frame, number plate, coal heaped)."""
        lay = self.lay
        a, b = L.TENDER
        top = 226
        rail = 288
        hh = rail - 18 - top
        t = 2.0 + K.nz(b - a, hh, 8, 111) * 0.6 + np.linspace(0.8, -0.4, hh, dtype=np.float32)[:, None]
        lay.put(np.ones((hh, b - a), bool), a, top, 'I', t, hgt=0.6, flat=False)          # tank, lit from above
        lay.rect(a, top, 2, hh, 'I', 3.4, hgt=0.8)
        lay.rect(b - 2, top, 2, hh, 'I', 1.2)
        lay.rect(a, top, b - a, 2, 'I', 4.2, hgt=0.9)
        lay.rect(a, top + 2, b - a, 1, 'I', 3.0)
        for xx in range(a + 6, b, 18):                                     # rivet lines
            for yy in range(top + 6, rail - 22, 6):
                lay.px(xx, yy, 'I', 3.4)
        lay.rect(a, rail - 18, b - a, 5, 'R', 1.8, hgt=0.7)                # frame, red
        lay.rect(a, rail - 18, b - a, 1, 'R', 3.0)
        lay.rect(a + 40, top + 22, 22, 9, 'L', 2.4, hgt=0.6)              # number plate (brass)
        K.text(lay, 'ЭУ-708', a + 51, top + 24, 'N', 1.0, center=True)
        K.worn_text(lay, 'ВТ', a + 100, top + 26, 'W', 4.8, wear=0.1, seed=112)   # fresh chalk: Tuesday
        lay.rect(a + 99, top + 32, 12, 1, 'W', 4.4)
        for k in range(3):                                                 # wheels + springs
            wx = a + 22 + k * 44
            lay.ellipse(wx, rail - 7, 8, 7, 'I', 1.6, hgt=0.8)
            lay.ellipse(wx, rail - 7, 5, 4, 'I', 2.6, hgt=0.9)
            lay.rect(wx - 1, rail - 8, 2, 2, 'I', 4.0)
            lay.rect(wx - 9, rail - 13, 18, 2, 'I', 3.4)
        K.coal_heap(lay, (a + b) // 2, top + 1, b - a - 16, 16, seed=113, glint=0.05, snow=0.15)
        K.snowcap(lay, a, top, 8, depth=2, seed=114)
        K.snowcap(lay, b - 10, top, 10, depth=2, seed=115)

    def flood_mast(self):
        lay = self.lay
        x = L.FLOOD_MAST
        top = 62
        for yy in range(top, L.A_MID, 1):
            k = (yy - top) / (L.A_MID - top)
            hw = 3 + int(k * 4)
            lay.px(x - hw, yy, 'I', 2.6, hgt=0.6)
            lay.px(x + hw, yy, 'I', 2.2, hgt=0.6)
        y = top + 4
        while y < L.A_MID - 8:                                             # lattice
            k = (y - top) / (L.A_MID - top)
            hw = 3 + int(k * 4)
            lay.line(x - hw, y, x + hw, y + 8, 'I', 1.8)
            lay.line(x + hw, y, x - hw, y + 8, 'I', 1.6)
            lay.rect(x - hw, y, 2 * hw + 1, 1, 'I', 2.4)
            y += 8
        lay.rect(x - 9, top - 2, 19, 3, 'I', 2.8, hgt=0.7)                 # platform with railing
        lay.rect(x - 9, top - 8, 1, 6, 'I', 2.0)
        lay.rect(x + 9, top - 8, 1, 6, 'I', 2.0)
        lay.rect(x - 9, top - 8, 19, 1, 'I', 2.4)
        K.snowcap(lay, x - 9, top - 2, 19, depth=2, seed=121)
        for i, dx in enumerate((-6, 0, 6)):
            K.lamp_head(lay, x + dx, top + 2, 'flood', True)
        lay.rect(x - 2, L.A_MID - 14, 5, 8, 'I', 2.0, hgt=0.6)            # switch box
        K.wire(lay, x, top + 6, L.ROUNDHOUSE[0] + 4, 150, 10)
        for i, (dx, cx, cy) in enumerate(((-6, 470, 250), (0, 530, 260), (6, 640, 280))):
            vx, vy = cx - (x + dx), cy - (top + 4)
            n = math.hypot(vx, vy)
            self.L('flood_%d' % i, x + dx, top + 5, 'warm', 1.6, 430, 60, falloff=1.0, cone=(vx / n, vy / n, 0.72),
                   pool=0.0)
        # pools of the floods on the ground (wide, under the stage and at the ash pit)
        for (px, k) in ((470, 0.8), (540, 0.9), (630, 0.7)):
            self.lights.append(K.light('flood_pool_%d' % px, px, 286, 'warm', k, 10, 1, pool=1.0, pool_w=34,
                                       pool_spread=1.2, pool_depth=70))

    # ------------------------------------------------------------------ ash pit, barrel
    def ash_pit(self):
        lay = self.lay
        a, b = L.ASH_PIT
        y = L.A_MID - 4
        lay.rect(a, y, b - a, 4, 'K', 2.4, hgt=0.5)                       # brick rim
        for xx in range(a, b, 6):
            lay.rect(xx, y, 1, 4, 'K', 1.2)
        lay.rect(a, y, b - a, 1, 'K', 3.6)
        lay.rect(a + 4, y - 3, b - a - 8, 3, 'X', 2.0, hgt=0.3)           # ash and clinker in the pit
        for k in range(10):
            xx = a + 6 + int(self.rng.integers(0, b - a - 12))
            lay.px(xx, y - 2, 'L', 3.6 + self.rng.random(), emis=True)
        self.L('ash_glow', (a + b) // 2, y - 2, 'warm', 0.55, 46, 4, pool=0.0)
        # the ash rake leaning on the pit's rim (the fire barrel stands beyond it)
        lay.line(a - 4, L.A_MID, a + 8, y - 28, 'D', 2.8)
        lay.rect(a + 6, y - 30, 7, 2, 'I', 3.0)

    def barrel(self):
        """The guard's fire barrel: a full 200-litre drum, sooted black above, punched with two rows of glowing
        holes, a broken rim with the embers' glow on it; the snow melted back round it into wet black cinders that
        catch the fire; split sleepers for firewood beside it.  It stands clear of the guard (690) and of every
        snow heap."""
        lay = self.lay
        cx = L.BARREL
        bw, bh = 16, 24
        x0, y0 = cx - bw // 2, L.A_MID - bh
        m_, mx_, my_ = lay.ellipse_mask(cx, L.A_MID + 1, 17, 4)                # the melt ring: wet cinders
        lay.put(m_, mx_, my_, 'E', 1.6, hgt=0.05)
        for k in range(9):
            lay.px(cx - 13 + k * 3 + (k % 2), L.A_MID + 1 + (k % 3) - 1, 'L', 2.6)   # the fire mirrored in the wet
        K.barrel(lay, x0, y0, bw, bh, 'I', 2.2, seed=131, hoops=2)
        lay.shade_rect(x0, y0, bw, 10, -1.2)                                   # soot above
        lay.rect(x0 - 1, y0, bw + 2, 2, 'I', 3.4, hgt=0.9)                     # the rolled rim, bent in one place
        lay.rect(x0 + 10, y0, 4, 1, 'I', 1.4)
        lay.px(x0 + 3, y0 + 6, 'I', 1.0)                                        # a dent
        lay.px(x0 + 4, y0 + 7, 'I', 3.8)
        for row, (yy, n) in enumerate(((y0 + 9, 5), (y0 + 15, 4))):            # punched air holes, glowing
            for k in range(n):
                hx = x0 + 3 + k * 3 + (row % 2) * 1
                lay.rect(hx, yy, 2, 2, 'L', 4.6 - row * 0.4, emis=True)
                lay.px(hx, yy - 1, 'K', 2.0)                                   # scorch over each hole
        for k in range(6):                                                     # embers glowing at the broken rim
            lay.px(x0 + 1 + k * 3 - (k % 2), y0 + 2 + (k % 2), 'L', 4.8 - (k % 3) * 0.5, emis=True)
        # a pair of women's gloves drying on the rim (Maria's)
        lay.rect(x0 + bw - 3, y0 - 3, 4, 3, 'G', 2.4, hgt=0.6)
        lay.rect(x0 + bw - 2, y0, 2, 4, 'G', 1.8)
        self.barrel_top = (cx, y0)
        self.L('barrel', cx, y0 - 6, 'warm', 1.3, 80, 10, pool=0.9, pool_w=12, pool_spread=0.8, pool_depth=40)
        # firewood: split sleepers stacked by the barrel, a block with the axe in it
        for k in range(3):
            lay.rect(cx - 30 + k, L.A_MID - 4 - k * 3, 14, 3, 'D', 1.8 + k * 0.4, hgt=0.6)
            lay.rect(cx - 30 + k, L.A_MID - 4 - k * 3, 14, 1, 'D', 2.8 + k * 0.4)
        lay.rect(cx - 14, L.A_MID - 7, 5, 7, 'D', 2.6, hgt=0.7)
        lay.rect(cx - 14, L.A_MID - 7, 5, 1, 'D', 4.0)
        lay.line(cx - 12, L.A_MID - 8, cx - 15, L.A_MID - 15, 'D', 3.4)
        lay.rect(cx - 13, L.A_MID - 9, 3, 2, 'I', 4.2)

    # ------------------------------------------------------------------ the roundhouse's back
    def roundhouse(self):
        lay = self.lay
        a, b = L.ROUNDHOUSE
        top = 120
        K.brick_wall(lay, a, top, b - a, L.A_BACK - top, base=3.6, seed=141, soot=0.9)
        lay.rect(a, L.A_BACK - 10, b - a, 10, 'C', 2.2, hgt=0.5)
        # pilasters and the sawtooth gable line with smoke hoods
        for px in range(a, b, 46):
            lay.rect(px, top, 6, L.A_BACK - 10 - top, 'K', 3.2, hgt=0.6)
            lay.rect(px, top, 1, L.A_BACK - 10 - top, 'K', 4.6)
        lay.rect(a - 2, top - 4, b - a + 4, 4, 'K', 2.2, hgt=0.7)
        for k, hx in enumerate(range(a + 20, b, 58)):
            lay.poly([(hx - 10, top - 4), (hx + 10, top - 4), (hx + 6, top - 18), (hx - 6, top - 18)], 'I', 2.0,
                     hgt=0.6)
            lay.rect(hx - 8, top - 22, 16, 4, 'I', 2.8, hgt=0.7)
            K.snowcap(lay, hx - 8, top - 22, 16, depth=2, seed=150 + k)
        K.snowcap(lay, a - 2, top - 4, b - a + 4, depth=3, seed=142)
        self.smoke_hoods = [(hx, top - 24) for hx in range(a + 20, b, 58)]
        # high windows: dirty, warm glow from the stalls
        for wx in range(a + 12, b - 12, 46):
            K.window(lay, wx + 6, top + 18, 28, 34, lit=True, rows=3, cols=4, frame=('I', 2.0), glass=('L', 3.0),
                     seed=wx, frost=0.2, sill_snow=True)
            lay.shade_rect(wx + 6, top + 18, 28, 34, -0.6)
            arch = K.arch_mask(32, 6, 5)
            lay.put(arch, wx + 4, top + 12, 'K', 2.6, hgt=0.5)
        # the old banner across the wall, patched with sacking
        by = 186
        lay.rect(a + 10, by, 170, 12, 'R', 2.0, hgt=0.3)
        lay.rect(a + 10, by, 170, 1, 'R', 3.0)
        n = K.nz(170, 12, 4, 143)
        lay.put(n > 0.18, a + 10, by, 'R', 1.4, hgt=0.3)
        # sacking patches where it tore -- at the ends and in the word gap, never over a letter
        tw = K.text_width('ВОССТАНОВИМ ВМЕСТЕ', '57')
        tx0 = a + 95 - tw // 2
        gap_x = tx0 + K.text_width('ВОССТАНОВИМ', '57') + 2
        for (px, pw) in ((a + 12, 14), (gap_x, 3), (tx0 + tw + 4, 12)):
            K.tex_rect(lay, px, by + 1, pw, 10, 'P', 2.0, seed=px, amp=0.4, cell=2)
            for k in range(0, pw, 3):
                lay.px(px + k, by + 1, 'P', 3.2)
        # weathered, not worn away: the tired spots of the paint go dull, the letters keep their shapes
        K.worn_text(lay, 'ВОССТАНОВИМ ВМЕСТЕ', a + 95, by + 3, 'W', 4.4, font='57', wear=0.16, seed=144, center=True,
                    ghost=('W', 3.3))
        self.readable['roundhouse_banner'] = [tx0, by + 3, tw, 7]
        for (px, py) in ((a + 10, by), (a + 179, by)):
            lay.rect(px, py - 2, 1, 16, 'I', 2.0)
        # the emblem on the parapet between two smoke hoods (insignia site): neutral = gear and wheat / hist = star
        # with hammer and sickle -- clear of the window bays below
        self.emblem(*L.GABLE_EMBLEM)
        # stall doors
        for i, (da, db) in enumerate(L.STALL_DOORS):
            self.stall_door(da, db, ajar=(i == 0))
        # the personnel door with the press notice and a lamp over it
        pa, pb = L.PERSONNEL_DOOR
        dt = 246
        lay.rect(pa - 2, dt - 3, pb - pa + 4, L.A_BACK - dt + 3, 'K', 1.8, hgt=0.6)
        K.planks(lay, pa, dt, pb - pa, L.A_BACK - dt, 'D', 2.2, seed=145, pitch=4)
        lay.rect(pb - 5, dt + 22, 2, 3, 'I', 4.2)
        nx, ny, nw, nh = L.NOTICE
        lay.rect(nx, ny, nw, nh, 'P', 5.0, hgt=0.3)
        K.pseudo_text(lay, nx + 1, ny + 2, nw - 2, 5, 'N', 2.0, seed=146, gap=2)
        lay.rect(nx + 1, ny + nh - 4, 9, 1, 'R', 2.6)                     # the underlined line
        lay.ellipse(nx + nw - 4, ny + nh - 3, 2, 2, 'U', 2.8)              # depot stamp
        for (cx, cy) in ((nx, ny), (nx + nw - 1, ny)):
            lay.px(cx, cy, 'I', 4.4)
        lay.rect(pa + 2, dt - 12, pb - pa - 4, 2, 'I', 2.4)
        K.lamp_head(lay, (pa + pb) // 2, dt - 6, 'enamel', True)
        self.L('door_lamp', (pa + pb) // 2, dt - 4, 'warm', 0.95, 54, 12, pool=0.6, pool_w=8, pool_spread=0.6,
               pool_depth=36)
        lay.rect(pa - 6, L.A_BACK - 2, pb - pa + 12, 2, 'C', 2.6)
        # drainpipes, a ladder hook, rust
        for px in (a + 2, b - 40):
            lay.rect(px, top, 3, L.A_BACK - top - 4, 'I', 2.4, hgt=0.7)
            lay.rect(px, top, 1, L.A_BACK - top - 4, 'I', 3.6)
        K.icicles(lay, a - 2, b, top, seed=147, density=0.3, maxlen=7)

    def stall_door(self, a, b, ajar=False):
        lay = self.lay
        top = 206
        w = b - a
        arch = K.arch_mask(w + 8, 14, 12)
        lay.put(arch, a - 4, top - 12, 'K', 2.6, hgt=0.6)
        lay.rect(a - 4, top, 4, L.A_BACK - top, 'K', 2.8, hgt=0.6)
        lay.rect(b, top, 4, L.A_BACK - top, 'K', 2.8, hgt=0.6)
        if ajar:
            # left leaf open (swung toward us: a narrow edge), the stall inside: warm haze, a tender's back, a pit
            gap = 20
            inside = np.full((L.A_BACK - top, gap), 3.4, np.float32)
            inside -= np.linspace(0, 1.8, L.A_BACK - top)[:, None] * 0.6
            lay.put(np.ones_like(inside, bool), a + 4, top, 'L', inside, emis=True, flat=False, hgt=-0.5)
            lay.rect(a + 8, top + 20, 12, L.A_BACK - top - 30, 'L', 1.0, emis=True)   # a tender's dark back
            lay.rect(a + 9, top + 22, 4, 4, 'L', 2.2, emis=True)
            lay.rect(a + 4, L.A_BACK - 8, gap, 8, 'L', 2.4, emis=True)
            K.planks(lay, a + 4 + gap, top, w - gap - 4, L.A_BACK - top, 'D', 2.0, seed=a, pitch=5)
            lay.rect(a, top, 5, L.A_BACK - top, 'D', 3.0, hgt=0.8)                     # open leaf edge
            lay.rect(a, top, 1, L.A_BACK - top, 'D', 4.2)
            self.stall_glow = (a + 4 + gap // 2, top + 30)
            self.L('stall', a + 14, top + 34, 'warm', 1.05, 110, 12, pool=0.8, pool_w=12, pool_spread=1.0,
                   pool_depth=52)
        else:
            K.planks(lay, a, top, w, L.A_BACK - top, 'D', 2.0, seed=a, pitch=5)
            lay.rect(a + w // 2, top, 1, L.A_BACK - top, 'D', 0.8)
            for yy in (top + 14, L.A_BACK - 22):                           # strap hinges
                lay.rect(a + 2, yy, w - 4, 2, 'I', 2.6, hgt=0.7)
            lay.rect(a + w // 2 - 3, top + 40, 6, 3, 'I', 3.4)
            K.worn_text(lay, '7', a + 8, top + 24, 'W', 3.6, wear=0.2, seed=a)
        K.snowcap(lay, a - 4, L.A_BACK - 1, w + 8, depth=3, seed=a + 1, drift=0.8)

    def emblem(self, cx, cy):
        lay = self.lay
        hist = self.cfg.get('hist', False)
        for dx in (-6, 6):                                                 # its iron stand on the cornice
            lay.rect(cx + dx, cy + 8, 2, 120 - 4 - cy - 8 + 1, 'I', 2.2, hgt=0.7)
        lay.ellipse(cx, cy, 11, 11, 'K', 2.0, hgt=0.6)
        lay.ellipse(cx, cy, 9, 9, 'R', 1.8, hgt=0.5)
        for dx in range(-7, 8):                                            # snow on its top
            yy = cy - int(round(math.sqrt(max(0.0, 121 - dx * dx))))
            lay.px(cx + dx, yy, 'S', 4.6, hgt=0.7)
            if abs(dx) < 5:
                lay.px(cx + dx, yy - 1, 'S', 4.2, hgt=0.7)
        if hist:      # five-pointed star with a hammer and sickle (real insignia: only the _hist variant)
            pts = []
            for k in range(10):
                r = 8 if k % 2 == 0 else 3.4
                ang = -math.pi / 2 + k * math.pi / 5
                pts.append((cx + r * math.cos(ang), cy + r * math.sin(ang)))
            lay.poly(pts, 'R', 3.8, hgt=0.8)
            lay.line(cx - 3, cy + 2, cx + 2, cy - 3, 'L', 4.6)
            lay.line(cx - 2, cy - 2, cx + 3, cy + 3, 'L', 4.4)
            lay.px(cx + 3, cy - 3, 'L', 4.6)
        else:         # fictional gear-and-wheat emblem (neutral)
            for k in range(12):
                ang = k * math.pi / 6
                lay.rect(int(round(cx + 7 * math.cos(ang))), int(round(cy + 7 * math.sin(ang))), 1, 1, 'L', 4.0)
            lay.ellipse(cx, cy, 5, 5, 'L', 3.6, hgt=0.8)
            lay.ellipse(cx, cy, 2, 2, 'R', 2.0)
            for s in (-1, 1):
                for k in range(4):
                    lay.px(cx + s * (3 + k // 2), cy + 6 - k * 3, 'L', 4.6)

    # ------------------------------------------------------------------ the tarpaulin from behind
    def tarp_back(self):
        lay = self.lay
        a, b = L.TARP_A
        poles = (a + 2, a + 30, a + 58)
        top = 214
        # the canvas runs from the back (left, higher) toward the viewer (right, lower): a slanted plane
        pts = [(a + 2, top), (b, top + 18), (b, L.A_MID + 6), (a + 2, L.A_BACK - 2)]
        m, mx, my = lay.poly(pts, 'Q', 2.4, hgt=0.3)
        n = K.nz(m.shape[1], m.shape[0], 5, 161)
        lay.put(m, mx, my, 'Q', 2.0 + n * 1.0, hgt=0.3, flat=False)
        for k in range(6):                                                 # sagging folds
            xx = a + 6 + k * 10
            lay.line(xx, top + 4 + k * 3, xx + 3, L.A_BACK - 4, 'Q', 1.2)
        for (px, py, pw, ph) in ((a + 12, 236, 9, 8), (a + 36, 250, 11, 9), (a + 50, 228, 7, 6)):   # patches
            K.tex_rect(lay, px, py, pw, ph, 'P', 1.8, seed=px, amp=0.4, cell=2)
            lay.rect(px, py, pw, 1, 'P', 2.8)
            for k in range(0, pw, 2):
                lay.px(px + k, py + ph - 1, 'N', 2.0)
        ghost = K.text_mask('ВМЕСТЕ', '57')[:, ::-1]                    # the front's letters, mirrored
        gm = ghost & (np.random.default_rng(166).random(ghost.shape) < 0.55)
        lay.put(gm, a + 6, 228, 'R', 1.2, hgt=0.3)
        K.tex_rect(lay, a + 40, 262, 12, 14, 'P', 2.6, seed=167, amp=0.4, cell=2)      # a potato sack, stamped
        lay.rect(a + 40, 262, 12, 1, 'P', 3.6)
        lay.ellipse(a + 46, 269, 2, 2, 'U', 2.4)
        # the gap: light from the floodlit showcase leaks through
        lay.poly([(a + 24, 252), (a + 28, 251), (a + 29, 282), (a + 25, 284)], 'L', 4.4, emis=True)
        # a child's chalk drawing of a train (loco + two wagons, smoke curls)
        cx_, cy_ = a + 8, 262
        for (dx, dy, w_, h_) in ((0, 0, 8, 5), (9, 1, 7, 4), (17, 1, 7, 4)):
            lay.rect(cx_ + dx, cy_ + dy, w_, 1, 'W', 4.4)
            lay.rect(cx_ + dx, cy_ + dy + h_, w_, 1, 'W', 4.4)
            lay.rect(cx_ + dx, cy_ + dy, 1, h_, 'W', 4.4)
            lay.rect(cx_ + dx + w_ - 1, cy_ + dy, 1, h_, 'W', 4.4)
            lay.px(cx_ + dx + 2, cy_ + dy + h_ + 1, 'W', 4.0)
            lay.px(cx_ + dx + w_ - 3, cy_ + dy + h_ + 1, 'W', 4.0)
        lay.rect(cx_ + 1, cy_ - 3, 2, 3, 'W', 4.4)
        for k in range(4):
            lay.px(cx_ - k, cy_ - 4 - k, 'W', 4.2)
        for px in poles:
            lay.rect(px, top - 10, 3, L.A_MID - top + 10, 'D', 2.6, hgt=0.6)
            lay.rect(px, top - 10, 1, L.A_MID - top + 10, 'D', 3.6)
            K.snowcap(lay, px, top - 10, 3, depth=2, seed=px)
        lay.line(a + 2, top - 8, b, top + 4, 'N', 1.6)                    # guy rope
        # snow piled against its foot
        for i in range(b - a):
            d = int(3 + 3 * math.sin(i / 7.0))
            lay.rect(a + i, L.A_MID - d + 2, 1, d, 'S', 3.8, hgt=0.4)

    # ------------------------------------------------------------------ small clutter
    def clutter(self):
        lay = self.lay
        # snow shovels and a broom leaning on the dispatch office
        for (x, t) in ((96, 3.0), (100, 2.6)):
            lay.line(x, L.A_MID - 2, x + 4, 250, 'D', t)
        lay.rect(94, L.A_MID - 6, 6, 5, 'I', 3.0, hgt=0.6)
        # buckets, a sack of salt, coal baskets by the stage
        K.barrel(lay, 244, L.A_MID - 10, 8, 10, 'I', 2.8, seed=171, hoops=1, snow=True)
        lay.rect(L.STAGE[0] + 30, L.A_MID - 9, 10, 9, 'D', 3.2, hgt=0.6)   # wicker basket
        for k in range(0, 10, 2):
            lay.rect(L.STAGE[0] + 30 + k, L.A_MID - 9, 1, 9, 'D', 2.2)
        K.coal_heap(lay, L.STAGE[0] + 35, L.A_MID - 9, 10, 3, seed=172)
        # the heap of spilled coal under the stage (the gang shovels it)
        K.coal_heap(lay, 520, L.A_MID, 88, 16, seed=173, glint=0.07, snow=0.1)
        K.coal_heap(lay, 588, L.A_MID, 30, 8, seed=174, glint=0.06)
        # a neat row of worn Western shoes beside issued felt boots stuffed with straw (exp_kolonne_shoes)
        for k, (sx, rmp, t, w_) in enumerate(((470, 'M', 2.6, 4), (475, 'K', 2.8, 4), (480, 'N', 2.4, 4),
                                               (485, 'K', 2.2, 4))):
            lay.rect(sx, L.A_MID - 3, w_, 3, rmp, t, hgt=0.7)
            lay.rect(sx, L.A_MID - 3, w_, 1, rmp, t + 1.2)
            lay.px(sx + (1 if k % 2 else 2), L.A_MID - 2, 'N', 1.0)
        for (sx, t) in ((490, 1.8), (494, 2.0)):
            lay.rect(sx, L.A_MID - 9, 3, 9, 'C', t, hgt=0.7)
            lay.rect(sx, L.A_MID - 10, 3, 2, 'L', 3.0)                    # straw sticking out
        # a wheelbarrow (the shoveller fills it), a pick
        lay.poly([(448, L.A_MID - 14), (466, L.A_MID - 14), (462, L.A_MID - 6), (452, L.A_MID - 6)], 'I', 2.4,
                 hgt=0.7)
        K.coal_heap(lay, 457, L.A_MID - 14, 16, 4, seed=175)
        lay.ellipse(462, L.A_MID - 4, 3, 3, 'I', 1.8)
        lay.line(468, L.A_MID - 14, 476, L.A_MID - 8, 'D', 2.6)
        lay.line(560, L.A_MID - 2, 566, L.A_MID - 16, 'D', 2.8)            # pick
        lay.rect(563, L.A_MID - 18, 7, 2, 'I', 3.2)
        # snow heaps shovelled against the canteen and the fence (the fire barrel's place melted clear)
        for (a, b) in ((236, 260), (300, 344), (692, 712)):
            for i in range(b - a):
                d = int(2 + 5 * math.sin(math.pi * i / (b - a)))
                lay.rect(a + i, L.A_BACK - d + 1, 1, d, 'S', 3.6 + 0.4 * math.sin(i), hgt=0.5)
        # the rest corner by the canteen's bottle crates (L.REST = the old man of Kolonne 4 who sits on it): a
        # sleeper with a thermos and bread wrapped in newspaper, painted after the snow heap it stands against
        lay.rect(L.REST - 8, L.A_MID - 6, 22, 5, 'D', 1.8, hgt=0.6)
        lay.rect(L.REST + 10, L.A_MID - 10, 3, 4, 'G', 3.0)
        lay.rect(L.REST + 6, L.A_MID - 8, 3, 2, 'P', 3.8)

    # ------------------------------------------------------------------ sky light
    def sky_lights(self):
        """The cold dawn from above: broad, weak, from the upper left (the snow on every top edge catches it)."""
        for i, x in enumerate(range(-200, 1100, 240)):
            self.lights.append(K.light('sky_%d' % i, x, -260, 'cold', 0.36, 760, 300, falloff=1.0))

    def all_lights(self):
        return list(self.lights)
