"""env_c4p2_berlin_yard -- the layers of L_C4P2_BerlinB: Kolonnenstraße 14, gate passage and courtyard, Tuesday
18.2.1964, 22.10-23.40.

Painted in tone space (env_c4p2_berlin_kit, world 'B' = palette courtyard + proposed ramps): night blue plaster and
snow, warm windows, one sodium lamp in the gate passage.  The courtyard is unrolled into one elevation, the way the
house puzzle cuts the house open: Vorderhaus (front wing, with the gate passage) | Seitenflügel (side wing) |
Hinterhaus (back wing) from left to right.  Every lit window is a household of the house puzzle (C4P2_DESIGN §2.7).
    yd_sky    night sky, low cloud lit by the city                                    (parallax 0.03)
    yd_dome   the Great Hall far above the roofs, floodlit in the haze (+ _hist banners) (parallax 0.08)
    yd_roofs  the roofscape beyond the courtyard: chimneys, firewalls, antennas         (parallax 0.30)
    yard      the playfield 918..1920: the passage with the notice, the three façades, the courtyard with the coal,
              the cellar hatch, the lodge window, the bins, the pump, the carpet rack, the frozen laundry, the
              cobbler's souterrain                                                     (lit, normals, emission)
    fg_yard   near-black snow banks, a bicycle wheel, a bucket                          (parallax 1.25)
Story / insignia states (cfg): 'hist' (the party emblem on the Blockleitung's notice, the dome's banners),
'after' (c4h_solve_house done: the stairwells lit -- the sweep went up --, Hanna back at her window, the candle in
the cobbler's souterrain; patches only).
"""
from __future__ import annotations

import math

import numpy as np

import env_c4p2_berlin_kit as K
import env_c4p2_berlin_layout as L
import pg

X0 = L.SEAM_B
W = L.B_W
H = L.WORLD_H
FEET = L.FEET
F = L.FLOORS


def lx(x):
    """world x -> layer x"""
    return int(x) - X0


# =========================================================================== the playfield
class Yard:
    def __init__(self, cfg: dict | None = None):
        self.cfg = cfg or {}
        self.hist = bool(self.cfg.get('hist', False))
        self.after = bool(self.cfg.get('after', False))
        self.lay = K.tlayer(W, H, 'yard', 'B')
        self.lights: list[dict] = []
        self.windows: dict = {}          # name -> (x, y, w, h) layer coords (life strips crop from here)

    def light(self, name, pos, kind, energy, radius, height=24, **kw):
        d = {'name': name, 'pos': (float(pos[0]) - X0, float(pos[1])), 'kind': kind, 'energy': energy,
             'radius': radius, 'height': height}
        d.update(kw)
        self.lights.append(d)
        return d

    # ------------------------------------------------------------------ the façades
    def facades(self):
        lay = self.lay
        nz = pg.value_noise(W, H, 9, 811, octaves=4)
        damp = pg.value_noise(W, H, 30, 812, octaves=2)
        streak = np.repeat(pg.value_noise(W // 3 + 2, H, 2, 813, octaves=2), 3, axis=1)[:, :W]
        top = L.EAVES
        for (wx0, wx1, base, ramp, bricky) in ((L.WING_V[0], L.WING_V[1], 3.3, 'U', 70), (L.WING_S[0], L.WING_S[1], 2.7, 'U', 52),
                                                (L.WING_H[0], L.WING_H[1], 2.4, 'U', 26)):
            a, b = lx(wx0), lx(wx1)
            sl = (slice(top, FEET), slice(a, b))
            t = base + (nz[sl] - 0.5) * 0.5 - (damp[sl] > 0.66) * 0.3 - (streak[sl] - 0.5) * 0.35
            yy = np.arange(top, FEET)[:, None]
            t = t - 0.4 * (yy > 270) + 0.25 * (yy < 130)
            lay.put(np.ones((FEET - top, b - a), bool), a, top, ramp, t.astype(np.float32), flat=False, hgt=0.15)
            # render repairs in grey on the blue wings, rain streaks under the sills
            rng = np.random.default_rng(814 + a)
            if ramp == 'U':
                for _ in range(int((b - a) / 70)):
                    px_, py_ = a + int(rng.integers(4, b - a - 30)), int(rng.integers(top + 10, FEET - 40))
                    rw_, rh_ = int(rng.integers(10, 28)), int(rng.integers(6, 16))
                    for yy3 in range(py_, py_ + rh_):
                        for xx3 in range(px_, px_ + rw_):
                            if (xx3 + yy3) % 2 == 0:
                                lay.px(xx3, yy3, 'U', base - 0.35, hgt=0.2)
            # plaster fallen off: brick shows (more on the back wing)
            for _ in range(int((b - a) / bricky)):
                px_, py_ = a + int(rng.integers(4, b - a - 20)), int(rng.integers(top + 6, FEET - 30))
                pw, ph = int(rng.integers(8, 22)), int(rng.integers(5, 13))
                m = np.zeros((ph, pw), bool)
                for yy2 in range(ph):
                    for xx2 in range(pw):
                        if ((xx2 - pw / 2) / (pw / 2)) ** 2 + ((yy2 - ph / 2) / (ph / 2)) ** 2 < 1 - rng.random() * 0.3:
                            m[yy2, xx2] = True
                K.bricks(lay, px_, py_, pw, ph, 'K', 1.6, seed=int(px_), course=3, length=6, mask=m)
                lay.put(K.edge_of(m) & (np.roll(m, 1, axis=0) == False), px_, py_, ramp, base + 1.0)  # noqa: E712
        # the front wing is the better house: rusticated ground floor, window surrounds come with its windows
        va, vb = lx(L.WING_V[0]), lx(L.WING_V[1])
        for y in range(F['E'][0] + 4, FEET - 8, 6):
            lay.hline(va, y, vb - va, 'W', 1.8, hgt=0.0)
            lay.hline(va, y + 1, vb - va, 'W', 3.8, hgt=0.3)
        # the side wing's stair tower: a shallow projection with lighter render
        sa, sb = lx(L.S_STAIR) - 17, lx(L.S_STAIR) + 17
        for x in range(sa, sb):
            for y in range(top + 2, F['E'][0] - 3):
                lay.px(x, y, 'U', 3.2 + (nz[y, x] - 0.5) * 0.4 + (x == sa) * 0.8 - (x == sb - 1) * 0.9, hgt=0.35)
        # floor bands (cornices) with snow, the main cornice under the eaves
        for name, (ya, yb) in F.items():
            if name in ('E', 'D'):
                continue
            lay.rect(0, yb - 2, W, 2, 'W', 4.4, hgt=0.7)
            lay.hline(0, yb, W, 'W', 1.6)
            K.snowcap(lay, 0, yb - 2, W, 1, seed=yb, drip=0.15)
        lay.rect(0, F['E'][0] - 3, W, 3, 'W', 4.6, hgt=0.8)                    # the ground-floor cornice
        lay.hline(0, F['E'][0], W, 'W', 1.4)
        K.snowcap(lay, 0, F['E'][0] - 3, W, 2, seed=231, drip=0.3)
        lay.rect(0, top - 3, W, 4, 'W', 5.0, hgt=0.9)                           # main cornice
        lay.hline(0, top + 1, W, 'W', 1.6)
        lay.hline(0, top + 2, W, 'W', 2.2)
        # the inner corners: the receding wall in shadow, a downpipe with snow on its brackets
        for cx in (lx(L.WING_V[1]), lx(L.WING_H[0])):
            for k in range(5):
                lay.vline(cx - 2 + k, top + 4, FEET - top - 4, 'U', 0.8 + k * 0.3, hgt=0.1)
            K.cyl(lay, cx + 5, top + 2, 3, FEET - top - 4, 'I', 1.8, hgt=0.6)
            for by in range(top + 20, FEET - 10, 38):
                lay.rect(cx + 4, by, 5, 1, 'I', 2.6)
                lay.px(cx + 6, by - 1, 'SN', 5.0)
            lay.rect(cx + 3, FEET - 6, 7, 3, 'I', 2.0, hgt=0.6)                  # its shoe
        # a downpipe at the far right corner too, and the eaves gutter with icicles everywhere
        lay.rect(0, top - 5, W, 2, 'I', 1.8, hgt=0.8)
        lay.hline(0, top - 5, W, 'SN', 4.6)
        K.icicles(lay, 0, top - 3, W, seed=815, n=W // 6, maxlen=7)
        # the base: a dark plinth with splashes of slush
        lay.rect(0, FEET - 8, W, 8, 'W', 1.6, hgt=0.3)
        lay.hline(0, FEET - 8, W, 'W', 3.0)

    def roofs(self):
        """Roof slopes from the eaves up (snow on dark tiles), dormers, chimneys, antennas, the firewall."""
        lay = self.lay
        top = L.RIDGE
        nz = pg.value_noise(W, 40, 6, 821, octaves=3)
        fine = pg.value_noise(W, 40, 2, 825, octaves=2)
        for y in range(top, L.EAVES - 4):
            k = (y - top) / (L.EAVES - 4 - top)
            row = (y - top) % 5 == 4
            for x in range(W):
                v = nz[y - top, x]
                bare = (fine[y - top, x] > 0.9 - 0.12 * k) and row
                if bare:
                    lay.px(x, y, 'U', 1.4 + k * 0.4, flat=False, hgt=0.2)
                else:
                    lay.px(x, y, 'SN', 3.3 - k * 0.6 + (v - 0.5) * 0.35 - row * 0.35, flat=False, hgt=0.3)
        lay.hline(0, top, W, 'SN', 5.6, hgt=0.5)
        # roof hatches / small dormers of the drying lofts
        for x in (lx(1050), lx(1340), lx(1520), lx(1816)):
            lay.rect(x - 6, top + 8, 13, 12, 'W', 2.2, hgt=0.6)
            lay.rect(x - 4, top + 11, 9, 8, 'N', 1.4)
            K.snowcap(lay, x - 7, top + 8, 15, 2, seed=x)
        # chimney stacks with several flues
        rng = np.random.default_rng(822)
        self.chimneys = []
        for x in (lx(990), lx(1110), lx(1250), lx(1420), lx(1560), lx(1660), lx(1760), lx(1850)):
            cw = int(rng.integers(8, 14))
            ch = int(rng.integers(18, 30))
            ytop = top - ch
            K.bricks(lay, x, ytop, cw, ch + 6, 'K', 1.8, seed=x, course=3, length=5)
            lay.rect(x - 1, ytop, cw + 2, 2, 'W', 3.0, hgt=0.8)
            K.snowcap(lay, x - 1, ytop, cw + 2, 2, seed=x + 1)
            for fx in range(x + 1, x + cw - 1, 4):
                lay.rect(fx, ytop - 3, 2, 3, 'I', 1.4, hgt=0.6)
            self.chimneys.append((x + cw // 2, ytop - 3))
        # television aerials and a wire (1964)
        for (ax, ah) in ((lx(1180), 26), (lx(1480), 30), (lx(1700), 22)):
            lay.vline(ax, top - ah, ah, 'I', 1.8)
            for k in range(4):
                lay.hline(ax - 4 + k, top - ah + 3 + k * 4, 9 - 2 * k, 'I', 1.6)
        # the neighbour's firewall rising at the right end, a faded painted advertisement
        fx0 = lx(1872)
        K.bricks(lay, fx0, 18, W - fx0, L.EAVES - 18, 'K', 1.6, seed=823, course=3, length=7)
        lay.rect(fx0, 18, W - fx0, 2, 'W', 2.0)
        K.snowcap(lay, fx0, 18, W - fx0, 2, seed=824)
        K.text(lay, 'WASCH', fx0 + 6, 34, 'P', 3.0)
        K.text(lay, 'ANSTALT', fx0 + 4, 41, 'P', 2.6)
        K.text(lay, 'PLÄTTEREI', fx0 + 2, 50, 'P', 2.2)

    # ------------------------------------------------------------------ windows
    def window(self, cx, floor, kind='dark', w=None, h=None, seed=0, name=None, curtain=True, jars=False):
        """A Berlin box window at axis cx (world x) in `floor`; kind: dark | lit | dim | sealed.  Each window gets
        its own small life: frame paint, curtains, a cushion, a cat, a flower box, jars between the panes."""
        lay = self.lay
        ya, yb = F[floor]
        if w is None:
            w = 18 if floor == 'E' else 15
        if h is None:
            h = 30 if floor == 'E' else (14 if floor == 'D' else 24)
        x = lx(cx) - w // 2
        y = ya + (12 if floor == 'E' else (5 if floor == 'D' else 7))
        rng = np.random.default_rng(seed * 131 + cx * 7 + ord(floor[0]))
        front = cx < L.WING_V[1]
        back = cx >= L.WING_H[0]
        fr, ft = ('W', 4.4) if rng.random() < 0.55 else ('D', 2.6)            # white-painted or brown frames
        if back:
            fr, ft = ('D', 2.0) if rng.random() < 0.6 else ('W', 3.4)
        # reveal (lintel shadow), the front wing's surrounds and cornice hoods
        if front and floor in ('1', '2', '3'):
            lay.rect(x - 4, y - 4, w + 8, h + 7, 'W', 4.0, hgt=0.5)
            lay.rect(x - 6, y - 7, w + 12, 3, 'W', 4.8, hgt=0.8)
            lay.hline(x - 6, y - 4, w + 12, 'W', 2.0)
            K.snowcap(lay, x - 6, y - 7, w + 12, 2, seed=seed + cx + 9)
        lay.rect(x - 2, y - 2, w + 4, h + 4, 'U', 1.2, hgt=-0.2)
        lay.hline(x - 2, y - 2, w + 4, 'U', 0.8)
        lay.vline(x - 2, y - 1, h + 2, 'U', 1.0)
        if kind in ('lit', 'dim'):
            top, bot = (4.6, 3.2) if kind == 'lit' else (2.8, 1.8)
            lay.vgrad(x, y, w, h, 'L', top, bot, emis=True)
            if curtain:                                                        # net curtain pattern
                for yy in range(y, y + h):
                    for xx in range(x, x + w):
                        if (xx * 3 + yy * 5) % 7 == 0 and yy < y + h - 3:
                            lay.px(xx, yy, 'L', min(5.0, top + 0.4), emis=True)
                lay.rect(x, y, 2, h, 'P', 4.2 if kind == 'lit' else 3.0, emis=True)          # drapes
                lay.rect(x + w - 2, y, 2, h, 'P', 4.0 if kind == 'lit' else 2.8, emis=True)
            self.light('win_%s_%d' % (floor, cx), (cx, y + h / 2), 'warm', 0.6 if kind == 'lit' else 0.3,
                       52 if kind == 'lit' else 32, height=6)
        elif kind == 'sealed':
            lay.vgrad(x, y, w, h, 'U', 0.8, 0.4)
            lay.rect(x + 1, y + 1, w - 2, h - 2, 'P', 0.9)                     # newspaper stuck behind the glass
            K.pseudo_text(lay, x + 2, y + 3, w - 4, (h - 6) // 2, 'N', 2.4, seed=seed, gap=2)
            for k in range(-1, 2):                                             # paper seal strips with stamps
                yy0 = y + h // 2 + k * 7
                lay.hline(x - 2, yy0, w + 4, 'P', 4.4, crisp=True)
                lay.px(x + w // 2 + k * 3, yy0, 'R', 2.4)
        else:                                                                  # dark: the night sky on the glass
            style = rng.integers(0, 4)
            for yy in range(y, y + h):
                for xx in range(x, x + w):
                    sheen = ((xx - x) - (yy - y) * 0.6 + cx) % 11
                    lay.px(xx, yy, 'U', 0.7 + (1.0 if sheen < 1.5 else 0) + (yy - y) / h * 0.4)
            if curtain and style == 0:                                         # drapes
                lay.rect(x + 1, y, 3, h, 'U', 1.7)
                lay.rect(x + w - 4, y, 3, h, 'U', 1.6)
            elif curtain and style == 1:                                       # net curtain, faint
                for yy in range(y, y + h - 2):
                    for xx in range(x, x + w):
                        if (xx * 3 + yy * 5) % 9 == 0:
                            lay.px(xx, yy, 'U', 2.2)
            elif curtain and style == 2:                                       # roller blind half down
                lay.rect(x, y, w, h // 2, 'U', 1.9)
                lay.hline(x, y + h // 2, w, 'U', 2.8)
            if jars:                                                           # food kept between the panes
                for k in range(2):
                    lay.rect(x + 3 + k * 6, y + h - 5, 3, 4, 'Q', 1.4)
                    lay.px(x + 3 + k * 6, y + h - 6, 'R', 2.0)
        # frames: outer frame, the middle mullion, the transom
        lay.rect(x - 1, y - 1, w + 2, 1, fr, ft, hgt=0.6)
        lay.rect(x - 1, y + h, w + 2, 1, fr, ft - 0.4, hgt=0.6)
        lay.vline(x - 1, y, h, fr, ft, hgt=0.6)
        lay.vline(x + w, y, h, fr, ft - 0.6, hgt=0.6)
        inner = (fr, ft - 0.2) if kind != 'lit' else ('D', 1.6)
        lay.vline(x + w // 2, y, h, inner[0], inner[1], hgt=0.5)
        ty = y + h // 3
        lay.hline(x, ty, w, inner[0], inner[1], hgt=0.5)
        # sill with snow; things on some sills
        lay.rect(x - 3, y + h + 1, w + 6, 2, 'W', 4.6, hgt=0.8)
        lay.hline(x - 3, y + h + 3, w + 6, 'U', 0.8)
        K.snowcap(lay, x - 3, y + h + 1, w + 6, 2, seed=seed + cx, drip=0.3)
        r = rng.random()
        if floor in ('1', '2', '3') and kind != 'sealed':
            if r < 0.14:
                lay.rect(x - 1, y + h - 3, w + 2, 4, 'D', 1.8, hgt=0.6)        # a flower box under snow
                K.snowcap(lay, x - 1, y + h - 3, w + 2, 2, seed=seed + cx + 3)
            elif r < 0.22 and kind == 'lit':
                lay.rect(x + 1, y + h - 3, w - 2, 3, 'R', 1.8, emis=True)       # the window cushion
                lay.hline(x + 1, y + h - 3, w - 2, 'R', 2.6, emis=True)
            elif r < 0.27 and kind == 'dark':
                cxk = x + w - 6                                                 # a cat sits in a dark window
                lay.rect(cxk, y + h - 6, 4, 5, 'N', 0.6)
                lay.px(cxk, y + h - 7, 'N', 0.6)
                lay.px(cxk + 3, y + h - 7, 'N', 0.6)
                lay.px(cxk + 1, y + h - 5, 'L', 4.0, emis=True)
                lay.px(cxk + 3, y + h - 5, 'L', 4.0, emis=True)
                lay.line(cxk + 4, y + h - 1, cxk + 6, y + h - 3, 'N', 0.6)
            elif r < 0.31:
                lay.rect(x + w + 2, y + h - 8, 4, 4, 'D', 2.6, hgt=0.6)         # a bird feeder on a bracket
                lay.hline(x + w + 1, y + h - 9, 6, 'D', 3.4)
                lay.px(x + w + 3, y + h - 10, 'SN', 5.0)
        if name:
            self.windows[name] = (x, y, w, h)
        return x, y, w, h

    def stair_windows(self, cx, name, floors=('1', '2', '3'), lit=False):
        """The stairwell's half-landing windows (between the floors), dark -- or lit after the sweep."""
        lay = self.lay
        for fl in floors:
            ya, yb = F[fl]
            y = yb + 6
            w, h = 11, 16
            x = lx(cx) - w // 2
            lay.rect(x - 2, y - 2, w + 4, h + 4, 'W', 1.8, hgt=-0.2)
            if lit:
                lay.vgrad(x, y, w, h, 'L', 3.8, 2.6, emis=True)
                lay.hline(x, y + 4, w, 'L', 2.2, emis=True)                    # the banister's shadow
                lay.line(x, y + h - 1, x + w - 1, y + 6, 'L', 1.8, emis=True)
            else:
                lay.vgrad(x, y, w, h, 'U', 1.2, 0.8)
                lay.line(x, y + h - 1, x + w - 1, y + 6, 'U', 2.0)
            lay.rect(x - 1, y - 1, w + 2, 1, 'D', 2.4)
            lay.rect(x - 1, y + h, w + 2, 1, 'D', 2.0)
            lay.vline(x - 1, y, h, 'D', 2.4)
            lay.vline(x + w, y, h, 'D', 2.0)
            lay.vline(x + w // 2, y, h, 'D', 2.2)
            lay.rect(x - 2, y + h + 1, w + 4, 2, 'W', 4.6, hgt=0.7)
            K.snowcap(lay, x - 2, y + h + 1, w + 4, 2, seed=cx + int(fl))
            if lit:
                self.light('stair_%s_%s' % (name, fl), (cx, y + h / 2), 'warm', 0.35, 34, height=6, dynamic=True)

    def all_windows(self):
        """Every window of the three wings; the households of the house puzzle are lit as §2.7 tells."""
        hh = L.HOUSEHOLDS
        lit_axes = {}
        for hid, (wing, fl, kind, axes, _what) in hh.items():
            for a in axes:
                lit_axes[(fl, a)] = (kind, hid)
        # front wing (above the passage + right of it)
        for fl in ('1', '2', '3'):
            for a in L.V_AXES:
                kind, hid = lit_axes.get((fl, a), ('dark', None))
                self.window(a, fl, kind if kind in ('lit', 'dim', 'sealed') else 'dark', seed=11,
                            name=('%s_%d' % (hid, a)) if hid else None, jars=(fl == '2' and a == 1024))
        self.window(L.V_KITCHEN, '2', 'dark', w=11, seed=12, name='v2_kitchen', curtain=False, jars=True)
        self.window(L.V_KITCHEN, '1', 'dark', w=11, seed=13)
        self.window(L.V_KITCHEN, '3', 'dark', w=11, seed=14)
        self.window(1132, 'E', 'dark', seed=15)
        for a in (1024, 1132):
            self.window(a, 'D', 'dark', w=11, seed=16)
        # side wing
        for fl in ('1', '2', '3'):
            for a in L.S_AXES:
                if a == L.S_STAIR:
                    continue
                kind, hid = lit_axes.get((fl, a), ('dark', None))
                self.window(a, fl, kind if kind in ('lit', 'dim', 'sealed') else 'dark', seed=21,
                            name=('%s_%d' % (hid, a)) if hid else None, jars=(fl == '3' and a == 1600))
        for a in (1236, 1340, 1496, 1652):
            self.window(a, 'E', 'dark', seed=22)
        for a in (1340, 1444, 1548):
            self.window(a, 'D', 'dark', w=11, seed=23, name='sd_%d' % a)
        self.stair_windows(L.S_STAIR, 's', lit=self.after)
        self.stair_windows(970, 'v', lit=self.after)
        # back wing
        for fl in ('1', '2', '3'):
            for a in L.H_AXES[1:]:
                kind, hid = lit_axes.get((fl, a), ('dark', None))
                self.window(a, fl, kind if kind in ('lit', 'dim', 'sealed') else 'dark', seed=31,
                            name=('%s_%d' % (hid, a)) if hid else None)
        for a in L.H_AXES[1:]:
            self.window(a, 'E', 'dark', w=15, h=22, seed=32)
        self.window(1816, 'D', 'dark', w=11, seed=33, name='hd_1816')
        self.stair_windows(L.H_AXES[0], 'h', lit=self.after)

    def lodge(self):
        """The lodge window (Loge Kuhnert): lit, a radio, Frau Kuhnert (life strip), the box of cards on the sill."""
        lay = self.lay
        x0, x1 = L.LODGE
        x, y, w, h = lx(x0), F['E'][0] + 14, x1 - x0, 30
        lay.rect(x - 3, y - 3, w + 6, h + 6, 'W', 1.8, hgt=-0.2)
        lay.vgrad(x, y, w, h, 'L', 4.2, 2.8, emis=True)
        lay.rect(x, y, w, 3, 'L', 2.4, emis=True)
        lay.rect(x + w - 12, y + h - 12, 10, 8, 'D', 2.6, emis=True)            # the radio on a shelf
        lay.rect(x + w - 11, y + h - 11, 6, 3, 'L', 5.0, emis=True)             # its dial
        lay.rect(x + w - 4, y + h - 11, 1, 6, 'D', 1.4, emis=True)
        lay.rect(x + 2, y + 4, 8, 6, 'P', 3.6, emis=True)                       # a framed picture
        lay.rect(x, y, 3, h, 'P', 4.0, emis=True)                               # curtains
        lay.rect(x + w - 3, y, 3, h, 'P', 3.8, emis=True)
        for fx_ in (x - 1, x + w):
            lay.vline(fx_, y, h, 'D', 2.6, hgt=0.6)
        lay.hline(x - 1, y - 1, w + 2, 'D', 2.6)
        lay.vline(x + w // 2, y, h, 'D', 1.6)
        lay.hline(x, y + h // 3, w, 'D', 1.6)
        # the sill and the wooden box of household cards on it
        lay.rect(x - 4, y + h, w + 8, 3, 'W', 4.8, hgt=0.8)
        K.snowcap(lay, x - 4, y + h, 5, 2, seed=41)
        bx, by = x + w // 2 - 7, y + h - 7
        lay.rect(bx, by, 14, 7, 'D', 3.0, hgt=0.7)
        lay.hline(bx, by, 14, 'D', 4.2, hgt=0.8)
        for k in range(6):                                                       # card tops sticking up
            lay.rect(bx + 1 + k * 2, by - 2 - (k % 2), 1, 2 + (k % 2), 'P', 5.0 - (k == 3) * 1.8)
        lay.px(bx + 7, by - 3, 'R', 3.0)                                         # one red tab
        self.windows['se_lodge'] = (x, y, w, h)
        self.light('lodge', ((x0 + x1) / 2, y + h / 2), 'warm', 0.75, 70, height=8, pool=0.6, pool_w=14)

    # ------------------------------------------------------------------ the gate passage
    def passage(self):
        lay = self.lay
        a, b = lx(L.PASSAGE[0]), lx(L.PASSAGE[1])
        top = L.PASSAGE_TOP
        # the back wall: plaster above a dado of glazed tiles, the vault overhead
        nz = pg.value_noise(b - a, FEET - top, 6, 831, octaves=3)
        t = 2.2 + (nz - 0.5) * 0.5
        lay.put(np.ones((FEET - top, b - a), bool), a, top, 'W', t.astype(np.float32), flat=False, hgt=0.1)
        for yy in range(262, FEET - 4):                                          # tiles
            for xx in range(a, b):
                c = ((xx - a) // 6 + (yy - 262) // 5) % 2
                lay.px(xx, yy, 'E', 2.0 + c * 0.5 + (nz[yy - top, xx - a] - 0.5) * 0.3, hgt=0.15)
        for xx in range(a, b, 6):
            lay.vline(xx, 262, FEET - 266, 'E', 1.2)
        for yy in range(262, FEET - 4, 5):
            lay.hline(a, yy, b - a, 'E', 1.2)
        lay.rect(a, 259, b - a, 3, 'E', 3.0, hgt=0.6)                            # tile cap
        # the vault: a band of ribs in perspective
        for k in range(14):
            yy = top + k
            lay.hline(a, yy, b - a, 'W', 1.2 + k * 0.08 + (k % 4 == 0) * 0.4, hgt=0.4)
        for xx in range(a + 10, b, 26):
            lay.line(xx, top, xx - 4, top + 13, 'W', 2.2)
        lay.rect(a - 2, top - 4, b - a + 4, 5, 'W', 4.0, hgt=0.9)                # the arch rim, courtyard side
        lay.hline(a - 2, top - 4, b - a + 4, 'W', 5.2)
        K.snowcap(lay, a - 2, top - 4, b - a + 4, 2, seed=832)
        # keystone with the house number
        lay.rect((a + b) // 2 - 6, top - 9, 13, 9, 'W', 4.6, hgt=1.0)
        K.text(lay, '14', (a + b) / 2, top - 7, 'D', 1.4, center=True)
        # the courtyard-side corner of the passage: a guard stone against wheels
        gx = b - 2
        lay.rect(gx, top, 8, FEET - top, 'W', 3.4, hgt=0.6)
        lay.vline(gx, top, FEET - top, 'W', 4.6)
        lay.rect(gx - 2, FEET - 14, 8, 12, 'W', 4.0, hgt=0.9)
        lay.hline(gx - 2, FEET - 14, 8, 'W', 5.4)
        K.snowcap(lay, gx - 2, FEET - 14, 8, 2, seed=833)
        # the floor of the passage: cobbles, a drain
        for yy in range(FEET - 4, 318):
            for xx in range(a, b):
                c = ((xx // 5) + (yy // 3)) % 2
                lay.px(xx, yy, 'W', 1.8 + c * 0.5 + ((xx * 7 + yy) % 13 == 0) * 0.6, hgt=0.2)
        lay.rect(a + 60, 306, 14, 3, 'I', 1.0)
        for k in range(4):
            lay.vline(a + 62 + k * 3, 306, 3, 'W', 3.0)
        # the notice board: the Blockleitung's notice (its title on two lines; the party eagle above it only in the
        # _hist variant) and the pinned site plan with the hatched houses, No. 14 ringed in red (gate_notice)
        nx0, nx1 = lx(L.NOTICE[0]), lx(L.NOTICE[1])
        lay.rect(nx0 - 2, 237, nx1 - nx0 + 4, 35, 'D', 2.0, hgt=0.6)              # cork board in a frame
        lay.hline(nx0 - 2, 237, nx1 - nx0 + 4, 'D', 3.4)
        lay.hline(nx0 - 2, 271, nx1 - nx0 + 4, 'D', 1.2)
        nw = 33
        lay.rect(nx0, 239, nw, 31, 'P', 5.0, hgt=0.3)                             # the typed notice
        lay.hline(nx0, 239, nw, 'P', 4.2)
        lay.vline(nx0 + nw - 1, 240, 30, 'P', 3.8)
        ty = 241
        if self.hist:
            ty += self.notice_emblem(nx0 + nw // 2, 241) + 1
        K.text(lay, 'BEKANNT-', nx0 + nw / 2, ty + 1, 'I', 0.8, center=True)
        K.text(lay, 'MACHUNG', nx0 + nw / 2, ty + 7, 'I', 0.8, center=True)
        if ty + 14 < 267:
            K.pseudo_text(lay, nx0 + 3, ty + 14, nw - 8, max(1, (268 - ty - 14) // 3), 'I', 1.6, seed=5, gap=2)
        lay.px(nx0 + nw // 2, 239, 'R', 3.0)                                       # the drawing pin
        # the site plan, pinned over the notice's right edge
        px0 = nx0 + nw - 1
        pw = nx1 - px0
        lay.rect(px0, 243, pw, 25, 'P', 4.6, hgt=0.3)
        lay.hline(px0, 243, pw, 'P', 5.4)
        lay.hline(px0 + 1, 257, pw - 2, 'P', 2.6)                                  # the street
        for k in range(4):                                                          # four hatched houses
            hx = px0 + 2 + k * 6
            lay.rect(hx, 247, 5, 9, 'P', 2.6)
            for hy in range(248, 256, 2):
                lay.hline(hx + 1, hy, 3, 'P', 4.0)
        lay.rect(px0 + 1 + 2 * 6, 246, 7, 11, 'R', 2.6)                            # No. 14 ringed in red ...
        lay.rect(px0 + 2 + 2 * 6, 247, 5, 9, 'P', 2.6)                             # ... still hatched
        for hy in range(248, 256, 2):
            lay.hline(px0 + 3 + 2 * 6, hy, 3, 'P', 4.0)
        lay.rect(px0 + pw - 10, 260, 8, 5, 'P', 3.2)                               # title block „gez. K. A.“
        lay.hline(px0 + pw - 9, 262, 6, 'I', 1.4)
        lay.px(px0 + 3, 244, 'R', 3.0)                                             # the drawing pins
        lay.px(px0 + pw - 3, 244, 'R', 3.0)
        lay.rect(nx0 + 2, 272, 10, 3, 'P', 4.0, hgt=0.2)                           # an older notice, curled below
        # letterboxes, the residents' board, the front wing's stair door, the light switch
        for k in range(6):
            bx = lx(1056) + (k % 3) * 9
            by = 250 + (k // 3) * 9
            lay.rect(bx, by, 8, 8, 'D', 2.2 + (k % 2) * 0.4, hgt=0.6)
            lay.hline(bx + 1, by + 2, 6, 'I', 0.8)
            lay.px(bx + 6, by + 5, 'P', 4.4)
        lay.rect(lx(1084), 244, 12, 22, 'D', 1.8, hgt=0.5)
        lay.rect(lx(1085), 245, 10, 20, 'P', 3.0)
        for k in range(8):
            lay.hline(lx(1086), 247 + k * 2, 7 - (k % 3), 'I', 1.4)
        d0, d1 = lx(L.STAIR_DOOR_V[0]), lx(L.STAIR_DOOR_V[1])
        lay.rect(d0 - 2, 244, d1 - d0 + 4, FEET - 248, 'W', 1.8, hgt=-0.2)
        lay.rect(d0, 246, d1 - d0, FEET - 250, 'D', 2.2, hgt=0.4)
        lay.rect(d0 + 2, 250, d1 - d0 - 4, 14, 'L', 1.4, emis=True)               # frosted glass, the stairs dark
        lay.vline(d0 + (d1 - d0) // 2, 250, 14, 'D', 2.0)
        K.recess(lay, d0 + 2, 268, d1 - d0 - 4, 24, 'D', 1.8, shadow=1.2, light=2.8)
        lay.px(d1 - 3, 268, 'L', 4.0)
        lay.rect(lx(1028), 262, 3, 4, 'P', 3.4)                                    # light switch (timer)
        # the caged sodium lamp under the vault
        px_, py_ = lx(L.PASSAGE_LAMP[0]), L.PASSAGE_LAMP[1]
        lay.vline(px_, top + 2, py_ - top - 6, 'I', 1.4)
        lay.rect(px_ - 3, py_ - 4, 7, 7, 'L', 4.6, emis=True)
        lay.rect(px_ - 1, py_ - 2, 3, 3, 'L', 5.4, emis=True)
        for k in (-3, 0, 3):
            lay.vline(px_ + k, py_ - 4, 7, 'I', 1.4)
        lay.hline(px_ - 3, py_ - 5, 7, 'I', 1.8)
        self.light('passage_lamp', (L.PASSAGE_LAMP[0], py_ + 2), 'warm', 1.15, 130, height=16, pool=0.9,
                   pool_w=16, pool_spread=0.8)

    def notice_emblem(self, cx, y):
        """The Blockleitung's notice: no emblem (neutral) / the party eagle (historical, 12.4) -- a tiny one above the
        title.  Returns the rows it takes (0 when neutral)."""
        if not self.hist:
            return 0
        import env_berlin_insignia as BI
        ms = BI.eagle_masks(7, wreath=True, swastika=True)
        hh, ww = ms['body'].shape
        m = ms['all'][:, ::-1]                                                      # the party eagle looks right
        self.lay.put(m, cx - ww // 2, y, 'I', 1.0, hgt=0.4)
        return hh

    def street_door(self):
        """The far end of the passage: the open street door, the street at night beyond (snow, the house
        opposite, a street lamp, the red warning lamp on the barrier of No. 12).  After the house is solved (23.30)
        the sweep's car stands in the street, nose to the door: a dark saloon seen head-on through the doorway,
        its two headlamps glaring into the passage; their light lies on the setts and the tiles, and the two men in
        the doorway throw long shadows toward the courtyard."""
        lay = self.lay
        a, b = lx(L.STREET_DOOR[0]), lx(L.STREET_DOOR[1])
        top = 222
        # the street outside
        for yy in range(top, FEET + 2):
            for xx in range(a, b):
                lay.px(xx, yy, 'U', 1.0 + (yy - top) * 0.008, hgt=0.0)
        lay.rect(a, 268, b - a, 26, 'U', 1.8)                                      # the house opposite
        for xx in range(a + 3, b - 2, 8):
            lay.rect(xx, 272, 4, 6, 'L', 2.6 if xx % 16 else 1.6, emis=True)
        lay.rect(a, 294, b - a, 8, 'SN', 3.4, hgt=0.2)                              # the snowy pavement
        lay.hline(a, 294, b - a, 'SN', 5.2)
        lay.vline(a + 6, 236, 58, 'I', 1.4)                                         # the barrier's post ...
        lay.hline(a, 266, b - a, 'R', 2.4)                                           # ... its red-white boards
        for xx in range(a, b, 6):
            lay.rect(xx, 266, 3, 2, 'P', 5.0)
        lay.rect(a + 5, 258, 3, 3, 'R', 4.0, emis=True)                              # the warning lamp
        self.warning_lamp = (a + 5, 258)
        if self.after:
            self.car(a, b)
        # the open door leaves folded against the passage's sides, the threshold
        for (dx, t) in ((b - 2, 2.6), (a, 2.0)):
            lay.rect(dx, top, 3, FEET - top, 'D', t, hgt=0.6)
        lay.rect(a, top - 4, b - a + 2, 4, 'W', 2.6, hgt=0.8)
        lay.rect(a, FEET - 2, b - a + 4, 2, 'W', 4.2, hgt=0.6)
        self.light('street_lamp', (L.STREET_DOOR[0] + 8, 230), 'warm', 0.5, 56, height=20)
        if self.after:
            self.beam(b)

    def car(self, a, b):
        """The sweep's car head-on in the doorway: roof with snow, the windscreen with the street lamp in it, the
        bonnet, wings, chrome grille, bumper and plate, the two headlamps with their glare."""
        lay = self.lay
        cx = (a + b) // 2
        lay.rect(cx - 8, 266, 17, 3, 'I', 1.3, hgt=0.6)                                # roof
        lay.hline(cx - 7, 265, 15, 'SN', 3.6)                                         # snow on it
        lay.rect(cx - 10, 269, 21, 8, 'N', 0.7, hgt=0.4)                              # windscreen
        lay.line(cx - 7, 275, cx - 2, 270, 'U', 3.0)                                  # the street lamp in the glass
        lay.px(cx + 5, 271, 'U', 2.6)
        lay.vline(cx - 10, 269, 8, 'I', 1.8)                                          # A-pillars
        lay.vline(cx + 10, 269, 8, 'I', 1.8)
        lay.rect(cx - 12, 277, 25, 5, 'I', 1.5, hgt=0.7)                              # bonnet ...
        lay.hline(cx - 6, 277, 13, 'W', 2.6)                                          # ... its crown catches light
        lay.px(cx, 278, 'W', 3.4)                                                     # the bonnet mascot
        lay.rect(cx - 14, 282, 29, 10, 'I', 1.0, hgt=0.6)                             # the front: wings, grille
        lay.hline(cx - 14, 282, 29, 'I', 2.0)
        for gx in range(cx - 4, cx + 5, 2):
            lay.vline(gx, 283, 6, 'W', 3.8)                                           # chrome grille bars
        lay.hline(cx - 5, 283, 11, 'W', 4.6)
        lay.hline(cx - 5, 289, 11, 'W', 2.8)
        lay.rect(cx - 14, 292, 29, 2, 'W', 3.8, hgt=0.8)                              # the bumper
        lay.hline(cx - 14, 292, 29, 'W', 5.2)
        lay.rect(cx - 4, 290, 9, 3, 'P', 4.8)                                         # the number plate
        lay.hline(cx - 3, 291, 7, 'I', 1.2)
        lay.rect(cx - 13, 294, 27, 3, 'N', 0.4)                                       # shadow under the car
        for hx in (cx - 9, cx + 9):                                                   # the two headlamps
            for (dx, dy, t) in ((-3, 0, 3.0), (3, 0, 3.0), (0, -3, 3.0), (0, 3, 2.6),
                                (-2, -2, 2.4), (2, -2, 2.4), (-2, 2, 2.2), (2, 2, 2.2)):
                lay.px(hx + dx, 285 + dy, 'SN', t, emis=True)                         # the glare around it
            lay.rect(hx - 1, 284, 3, 3, 'L', 5.0, emis=True)
            lay.px(hx, 285, 'SN', 6.0, emis=True)
        self.light('headlights', (L.STREET_DOOR[0] + 12, 284), 'cold', 1.0, 150, height=8, dynamic=True)

    def beam(self, door_x):
        """The headlights' light on the passage floor and the first tiles: soft, falling off with distance (the
        setts' tops catch it, the joints stay dark), the two men's long shadows toward the courtyard."""
        lay = self.lay
        thr = pg.bayer(W, 30, 0, 0, 4)
        men = ((lx(953), 297), (lx(974), 298))                                     # the sweep's men (life strip)
        for yy in range(FEET - 6, 318):
            for xx in range(door_x, door_x + 150):
                if lay.rid[yy, xx] < 0:
                    continue
                d = (xx - door_x) / 150.0
                k = math.exp(-3.2 * d) * max(0.0, 1 - abs(yy - 307) / 13.0) ** 0.7
                shadow = any(xx > mx + 1 and abs(yy - (my + (xx - mx) * 0.06)) < 1.3 and xx < mx + 70
                             for (mx, my) in men)
                if shadow:
                    k *= 0.15
                if k < 0.06 or k * 1.3 < thr[yy - (FEET - 6), xx % W]:
                    continue
                top_ = ((xx // 5) + (yy // 3)) % 2 == 0 and (xx % 5) != 0 and (yy % 3) != 0
                if top_:
                    lay.px(xx, yy, 'SN', 2.4 + 2.6 * k, flat=False)
                else:
                    lay.px(xx, yy, 'W', 2.0 + 1.6 * k, flat=False)

    # ------------------------------------------------------------------ doors
    def doors(self):
        lay = self.lay
        # the side wing's stair door: green double door, frosted glass with Ilse's drawing in the frost
        d0, d1 = lx(L.S_DOOR[0]), lx(L.S_DOOR[1])
        ytop = 244
        lay.rect(d0 - 3, ytop - 6, d1 - d0 + 6, FEET - ytop + 6, 'W', 1.6, hgt=-0.2)
        lay.rect(d0 - 2, ytop - 5, d1 - d0 + 4, 4, 'W', 4.2, hgt=0.8)               # door head
        lay.rect(d0, ytop, d1 - d0, FEET - ytop - 3, 'E', 2.2, hgt=0.5)
        mid = d0 + (d1 - d0) // 2
        lay.vline(mid, ytop, FEET - ytop - 3, 'E', 1.0)
        for (gx0, gx1) in ((d0 + 2, mid - 1), (mid + 2, d1 - 2)):
            lay.rect(gx0, ytop + 3, gx1 - gx0, 18, 'SN', 2.6)                        # frosted panes
            lay.hline(gx0, ytop + 3, gx1 - gx0, 'SN', 3.6)
            K.recess(lay, gx0, ytop + 25, gx1 - gx0, 22, 'E', 1.6, shadow=1.0, light=2.8)
        # the finger drawing in the frost: a house with all its windows lit (hidden find exp_ilse_drawing)
        hx, hy = mid + 3, ytop + 8
        lay.rect(hx, hy + 3, 5, 5, 'SN', 4.8)
        lay.line(hx - 1, hy + 3, hx + 2, hy, 'SN', 4.8)
        lay.line(hx + 2, hy, hx + 5, hy + 3, 'SN', 4.8)
        lay.px(hx + 1, hy + 4, 'L', 4.0)
        lay.px(hx + 3, hy + 4, 'L', 4.0)
        lay.px(hx + 1, hy + 6, 'L', 4.0)
        lay.px(hx + 3, hy + 6, 'L', 4.0)
        lay.px(d1 - 4, ytop + 28, 'P', 4.4)                                          # handle
        lay.px(mid - 3, ytop + 28, 'P', 4.4)
        lay.rect(d0 - 4, FEET - 3, d1 - d0 + 8, 3, 'W', 4.4, hgt=0.6)               # the stone step
        K.snowcap(lay, d0 - 4, FEET - 3, d1 - d0 + 8, 1, seed=51)
        sign_y = ytop - 13
        lay.rect(mid - 9, sign_y, 19, 7, 'P', 4.6, hgt=0.4)
        K.text(lay, 'AUFG.B', mid - 8, sign_y + 1, 'I', 1.0)
        lay.rect(mid - 1, ytop - 8, 3, 2, 'I', 1.2)                                  # the dark door lamp
        # the back wing's hall door, four steps up (high ground floor), a railing
        h0, h1 = lx(L.H_DOOR[0]), lx(L.H_DOOR[1])
        ytop2 = 236
        lay.rect(h0 - 3, ytop2 - 5, h1 - h0 + 6, FEET - 12 - ytop2 + 5, 'W', 1.6, hgt=-0.2)
        lay.rect(h0, ytop2, h1 - h0, FEET - 14 - ytop2, 'D', 2.0, hgt=0.5)
        lay.rect(h0 + 2, ytop2 + 3, h1 - h0 - 4, 12, 'L', 2.4, emis=True)               # the hallway is lit (he)
        lay.rect(h0 + 2, ytop2 + 3, h1 - h0 - 4, 2, 'L', 1.6, emis=True)
        lay.rect(h0 + 1, ytop2 - 4, h1 - h0 - 2, 3, 'L', 2.0, emis=True)                 # the transom
        self.light('hall_he', ((L.H_DOOR[0] + L.H_DOOR[1]) / 2, ytop2 + 8), 'warm', 0.4, 40, height=6, pool=0.3)
        lay.vline((h0 + h1) // 2, ytop2, FEET - 14 - ytop2, 'D', 1.0)
        for k in range(4):                                                           # steps
            sy = FEET - 14 + k * 3
            lay.rect(h0 - 4 - k * 2, sy, h1 - h0 + 8 + k * 4, 3, 'W', 4.0 - k * 0.3, hgt=0.6)
            K.snowcap(lay, h0 - 4 - k * 2, sy, h1 - h0 + 8 + k * 4, 1, seed=60 + k)
        for xx in (h0 - 12, h1 + 10):
            lay.line(xx, FEET - 2, xx + (4 if xx < h0 else -4), FEET - 22, 'I', 1.8)
        lay.line(h0 - 8, FEET - 22, h0, FEET - 26, 'I', 2.2)
        lay.line(h1 + 6, FEET - 22, h1, FEET - 26, 'I', 2.2)
        # the wash-house door
        w0, w1 = lx(L.WASH_DOOR[0]), lx(L.WASH_DOOR[1])
        lay.rect(w0, 254, w1 - w0, FEET - 254, 'D', 1.8, hgt=0.4)
        for xx in range(w0, w1, 4):
            lay.vline(xx, 254, FEET - 254, 'D', 1.2)
        lay.rect(w0 - 2, 251, w1 - w0 + 4, 3, 'W', 4.2)
        pw = K.tw('WASCH') + 4
        lay.rect((w0 + w1) // 2 - pw // 2, 257, pw, 8, 'P', 4.8, hgt=0.3)
        lay.hline((w0 + w1) // 2 - pw // 2, 257, pw, 'P', 5.4)
        K.text(lay, 'WASCH', (w0 + w1) / 2, 259, 'I', 1.0, center=True)
        lay.px(w1 - 5, 276, 'P', 4.4)                                                 # the latch

    # ------------------------------------------------------------------ the courtyard floor and its things
    def ground(self):
        lay = self.lay
        nz = pg.value_noise(W, 40, 12, 841, octaves=3)
        fine = pg.value_noise(W, 40, 3, 842, octaves=2)
        y0, y1 = FEET - 6, 318
        a = lx(L.PASSAGE[1]) + 6
        for yy in range(y0, y1):
            for xx in range(a, W):
                t = 2.9 + (nz[yy - y0 + 4, xx] - 0.5) * 1.0 + (fine[yy - y0 + 4, xx] - 0.5) * 0.5 + (yy > 310) * 0.4
                lay.px(xx, yy, 'SN', t, flat=False, hgt=0.15)
        # the trodden paths: from the passage to the side door, the lodge, the bins, the pump, the back door
        rng = np.random.default_rng(843)
        for yy in range(296, 307):
            for xx in range(a, W):
                if fine[yy - y0 + 4, xx] > 0.45:
                    lay.px(xx, yy, 'SN', 2.6 + (nz[yy - y0 + 4, xx] - 0.5) * 0.8, flat=False, hgt=0.05)
        for _ in range(180):
            fx_, fy = int(rng.integers(a, W - 2)), int(rng.integers(297, 306))
            lay.rect(fx_, fy, 2, 1, 'SN', 2.2, hgt=-0.1)
        for (cx0, cx1) in ((a, a + 40), (lx(1300), lx(1380)), (lx(1520), lx(1600))):   # cobbles peeking out
            for _ in range(30):
                xx, yy = int(rng.integers(cx0, cx1)), int(rng.integers(298, 312))
                lay.rect(xx, yy, 3, 2, 'W', 2.2 + rng.random() * 0.6, hgt=0.3)
        # snow piled along the walls
        for xx in range(a, W):
            hh = int(3 + 2 * math.sin(xx * 0.07) + fine[0, xx] * 3)
            for k in range(hh):
                lay.px(xx, FEET - 6 - k, 'SN', 4.6 - k * 0.3, hgt=0.4)
        # the frozen puddle at the pump, a drain grate, cat paw prints, the hopscotch half under snow
        px0 = lx(L.PUMP[0]) - 6
        for yy in range(300, 308):
            for xx in range(px0, px0 + 30):
                if ((xx - px0 - 15) / 15) ** 2 + ((yy - 304) / 4) ** 2 < 1:
                    lay.px(xx, yy, 'U', 3.6 + ((xx + yy) % 5 == 0) * 1.4, hgt=0.0)
        lay.rect(lx(1508), 302, 10, 4, 'I', 1.2)
        for k in range(4):
            lay.vline(lx(1509) + k * 3, 302, 4, 'W', 2.8)
        for k in range(9):
            lay.px(lx(1560) + k * 4, 300 + (k % 2), 'SN', 2.0)
        r0 = lx(1620)
        for yy in range(297, 305):                                                     # the swept patch
            for xx in range(r0 - 2, r0 + 70):
                if fine[yy - y0 + 4, xx] < 0.62 - (xx - r0) / 140.0:
                    c = ((xx // 5) + (yy // 3)) % 2
                    lay.px(xx, yy, 'W', 1.3 + c * 0.3, flat=False, hgt=0.2)
        for i in range(7):
            cx0 = r0 + i * 10
            if i < 6:
                for xx in range(cx0, cx0 + 10):
                    for yy in (296, 304):
                        if fine[1, xx] > 0.12 + i * 0.07:
                            lay.px(xx, yy, 'Q', 3.0)
                lay.vline(cx0, 296, 9, 'Q', 2.8)
                if i < 5:
                    K.text(lay, str(i + 1), cx0 + 4, 298, 'Q', 3.0, crisp=True)
        K.text(lay, 'HIM', r0 + 61, 298, 'Q', 2.6)                                     # HIMMEL, under the snow
        for xx in range(r0 + 50, r0 + 78):
            for yy in range(296, 306):
                if fine[yy - y0 + 4, xx] > 0.72 - (xx - r0 - 50) / 60.0:
                    lay.px(xx, yy, 'SN', 3.6 + fine[0, xx] * 0.6, flat=False)

    def coal_and_hatch(self):
        lay = self.lay
        c0, c1 = lx(L.COAL[0]), lx(L.COAL[1])
        rng = np.random.default_rng(851)
        for k in range(150):                                                         # briquettes in a heap
            u = rng.random()
            xx = c0 + int(u * (c1 - c0))
            hmax = int(14 * math.sin(math.pi * u) ** 0.8) + 2
            yy = FEET - 2 - int(rng.integers(0, hmax))
            lay.rect(xx, yy, 3, 2, 'I', 0.8 + rng.random() * 1.4, hgt=0.5)
            lay.px(xx, yy, 'I', 2.6)
        for k in range(14):
            lay.rect(c0 - 8 + int(rng.integers(0, 60)), FEET + int(rng.integers(0, 8)), 3, 2, 'I', 1.4)
        K.snowcap(lay, c0 + 10, FEET - 13, 14, 1, seed=852)
        # the open iron cellar hatch: two leaves standing up, the dark chute, a glowing arrow inside
        h0, h1 = lx(L.HATCH[0]), lx(L.HATCH[1])
        lay.rect(h0, FEET - 4, h1 - h0, 8, 'N', 0.6)
        lay.rect(h0 + 3, FEET - 2, 6, 3, 'E', 3.0, emis=True)                         # luminous paint arrow
        lay.px(h0 + 9, FEET - 1, 'E', 3.0, emis=True)
        for (lx0, t) in ((h0 - 2, 2.2), (h1 - 1, 1.8)):
            lay.rect(lx0, FEET - 26, 3, 24, 'I', t, hgt=0.6)
            for yy in range(FEET - 24, FEET - 2, 4):
                lay.hline(lx0, yy, 3, 'I', t + 1.2)
        lay.rect(h0 - 3, FEET - 4, h1 - h0 + 6, 2, 'I', 2.6, hgt=0.7)
        # the shovel leaning against the hatch leaf
        lay.line(h0 - 3, FEET - 2, h0 - 12, FEET - 30, 'D', 2.6)
        lay.rect(h0 - 5, FEET - 7, 5, 6, 'I', 2.2, hgt=0.6)
        # the wartime arrow on the wall above (white paint, half gone): LSR -> cellar
        ax, ay = lx(L.HATCH[0]) - 4, 262
        lay.hline(ax, ay, 18, 'Q', 2.8)
        lay.line(ax + 18, ay, ax + 14, ay - 3, 'Q', 2.8)
        lay.line(ax + 18, ay, ax + 14, ay + 3, 'Q', 2.8)
        K.text(lay, 'LSR', ax + 1, ay - 7, 'Q', 2.4)

    def bins(self):
        lay = self.lay
        b0 = lx(L.BINS[0])
        labels = ['VH', 'SF', 'HH', 'HH 3']
        for k in range(4):
            x = b0 + k * 13
            K.cyl(lay, x, 270, 11, 26, 'I', 2.0, hgt=0.7)
            for ry in (274, 284):
                lay.hline(x, ry, 11, 'I', 3.0, hgt=0.8)
            lay.rect(x - 1, 267, 13, 3, 'I', 2.6, hgt=0.9)                               # lid
            K.snowcap(lay, x - 1, 267, 13, 3, seed=861 + k)
            K.text(lay, labels[k][:2], x + 2, 277, 'Q', 2.6)
            if labels[k] == 'HH 3':
                K.text(lay, '3', x + 4, 287, 'Q', 2.6)
                lay.rect(x + 1, 266, 9, 1, 'P', 4.0)                                    # newspaper lining
        lay.line(b0 + 4, 266, b0 + 1, 256, 'E', 2.0)                                    # fir twigs
        lay.line(b0 + 6, 266, b0 + 8, 255, 'E', 1.6)
        lay.px(b0 + 2, 258, 'E', 2.4)
        lay.line(b0 + 18, 266, b0 + 24, 250, 'D', 2.6)                                   # a chair leg
        lay.rect(b0 + 23, 249, 2, 2, 'D', 3.0)

    def pump(self):
        lay = self.lay
        x0, x1 = lx(L.PUMP[0]), lx(L.PUMP[1])
        cx = (x0 + x1) // 2
        lay.rect(cx - 5, 290, 11, 6, 'E', 1.8, hgt=0.7)                                  # base plinth
        K.cyl(lay, cx - 3, 250, 7, 40, 'E', 1.8, hgt=0.8)                                # the cast-iron column
        for ry in (258, 272, 284):
            lay.rect(cx - 4, ry, 9, 2, 'E', 2.6, hgt=0.9)
        lay.rect(cx - 4, 244, 9, 6, 'E', 2.2, hgt=0.9)                                   # the cap ...
        lay.rect(cx - 2, 240, 5, 4, 'E', 2.6, hgt=1.0)                                   # ... and its knob
        lay.px(cx, 239, 'SN', 5.4)
        lay.line(cx + 3, 252, cx + 18, 244, 'I', 2.4)                                    # the lever
        lay.rect(cx + 17, 242, 3, 3, 'I', 2.8)
        lay.rect(cx - 9, 266, 7, 3, 'E', 2.4, hgt=0.8)                                   # the spout ...
        K.icicles(lay, cx - 9, 269, 6, seed=871, n=4, maxlen=8)                          # ... frozen
        lay.rect(cx - 12, 292, 12, 3, 'U', 3.4)                                          # ice at its foot

    def rack(self):
        lay = self.lay
        x0, x1 = lx(L.RACK[0]), lx(L.RACK[1])
        for px_ in (x0, x1 - 3):
            K.cyl(lay, px_, 244, 3, 52, 'I', 1.8, hgt=0.7)
            lay.px(px_ + 1, 243, 'SN', 5.0)
        lay.rect(x0, 246, x1 - x0, 3, 'I', 2.4, hgt=0.8)                                 # the bar
        K.snowcap(lay, x0, 246, x1 - x0, 2, seed=881)
        lay.rect(x0 + 3, 270, x1 - x0 - 6, 2, 'I', 2.0, hgt=0.6)                          # the lower bar
        lay.line(x0 + 30, 249, x0 + 28, 262, 'D', 2.6)                                    # a carpet beater
        for k in range(3):
            lay.px(x0 + 26 + k * 2, 263 + (k % 2), 'D', 2.6)
        lay.rect(x0 + 6, 252, 16, 11, 'P', 5.2, hgt=0.4)                                  # the house rules plate
        lay.hline(x0 + 6, 252, 16, 'B' if 'B' in lay.R.idx else 'U', 2.6)
        K.text(lay, 'HAUS', x0 + 7, 253, 'I', 0.8)
        K.pseudo_text(lay, x0 + 7, 259, 14, 2, 'I', 1.4, seed=9)

    def laundry(self):
        """Frozen laundry high across the corner of front and side wing (exp_frozen_laundry, focus 1204, 128):
        two lines from window hooks, stiff shirts, a sheet, children's stockings in three sizes."""
        lay = self.lay
        a, b = lx(L.LAUNDRY[0]), lx(L.LAUNDRY[1])
        for (ly0, sag, items) in ((124, 4, ('shirt', 'sheet', 'sock3', 'sock2', 'sock1', 'shirt')),
                                  (162, 3, ('towel', 'longjohns', 'shirt'))):
            pts = pg.catenary(a, ly0, b, ly0, sag)
            for (xx, yy) in pts:
                lay.px(int(xx), int(yy), 'I', 2.2)
            lay.rect(a - 2, ly0 - 1, 3, 3, 'I', 2.6)
            lay.rect(b - 1, ly0 - 1, 3, 3, 'I', 2.6)
            n = len(items)
            for i, it in enumerate(items):
                ix = a + 6 + int((b - a - 14) * i / max(1, n - 1))
                iy = int(ly0 + sag * math.sin(math.pi * (ix - a) / (b - a)))
                if it == 'shirt':
                    lay.rect(ix - 4, iy + 1, 9, 9, 'Q', 2.4, hgt=0.5)
                    lay.rect(ix - 6, iy + 1, 2, 5, 'Q', 2.0)
                    lay.rect(ix + 5, iy + 1, 2, 5, 'Q', 2.0)
                    lay.hline(ix - 4, iy + 1, 9, 'Q', 3.0)
                    lay.px(ix, iy + 3, 'Q', 1.2)
                elif it == 'sheet':
                    lay.rect(ix - 7, iy + 1, 15, 16, 'Q', 2.6, hgt=0.3)
                    for yy in range(iy + 3, iy + 16, 4):
                        lay.hline(ix - 7, yy, 15, 'Q', 2.2)
                    K.icicles(lay, ix - 7, iy + 17, 15, seed=ix, n=4, maxlen=3)
                elif it.startswith('sock'):
                    s = int(it[-1])
                    lay.rect(ix, iy + 1, 2, 3 + s * 2, 'R' if s == 2 else 'Q', 2.4 if s == 2 else 1.8)
                    lay.rect(ix, iy + 3 + s * 2, 3, 2, 'R' if s == 2 else 'Q', 2.4 if s == 2 else 1.8)
                elif it == 'towel':
                    lay.rect(ix - 3, iy + 1, 7, 10, 'Q', 2.0, hgt=0.3)
                    lay.hline(ix - 3, iy + 8, 7, 'R', 2.2)
                elif it == 'longjohns':
                    lay.rect(ix - 3, iy + 1, 7, 5, 'Q', 1.8)
                    lay.rect(ix - 3, iy + 6, 3, 9, 'Q', 1.6)
                    lay.rect(ix + 1, iy + 6, 3, 9, 'Q', 1.6)
                lay.px(ix, iy, 'D', 3.0)                                                # the peg

    def basket(self):
        """Frau Grabowski's basket on a washing line from her dark kitchen window (2nd floor) down to head height."""
        lay = self.lay
        wx, wy, ww, wh = self.windows.get('v2_kitchen', (lx(L.V_KITCHEN) - 5, F['2'][0] + 7, 11, 24))
        bx, by = lx(L.BASKET[0]), L.BASKET[1]
        lay.vline(bx, wy + wh + 2, by - (wy + wh + 2) - 4, 'Q', 2.0)
        lay.line(bx - 4, by - 4, bx, by - 8, 'Q', 2.0)
        lay.line(bx + 4, by - 4, bx, by - 8, 'Q', 2.0)
        lay.rect(bx - 5, by - 4, 11, 7, 'D', 3.0, hgt=0.6)                              # the wicker basket
        for k in range(0, 11, 2):
            lay.vline(bx - 5 + k, by - 4, 7, 'D', 3.8)
        lay.hline(bx - 5, by - 4, 11, 'D', 4.2)
        lay.rect(wx + 2, wy + wh - 3, ww - 4, 3, 'P', 1.6)                                # a hand at the sill? a cloth

    def workshop(self):
        """Schuhmacherei Pietsch: half-sunk souterrain windows with shelves of shoes, name tags, lasts; the
        painted sign and a hanging boot (the candle after the puzzle is a patch)."""
        lay = self.lay
        a, b = lx(L.WORKSHOP[0]), lx(L.WORKSHOP[1])
        y0 = 276
        lay.rect(a - 3, y0 - 3, b - a + 6, FEET - y0 + 3, 'W', 1.6, hgt=-0.3)
        n = 5
        ww = (b - a - (n - 1) * 6) // n
        for i in range(n):
            x = a + i * (ww + 6)
            candle = self.after and i == 1
            if candle:
                lay.vgrad(x, y0, ww, FEET - y0 - 2, 'L', 3.4, 1.8, emis=True)
            else:
                lay.vgrad(x, y0, ww, FEET - y0 - 2, 'U', 2.2, 1.0)
                for yy in range(y0, FEET - 2):                                   # the snow mirrored in the glass
                    lay.px(x + (yy - y0) % ww, yy, 'U', 3.0)
            # shelves with pairs of shoes and their little white tags
            for sy in (y0 + 6, y0 + 13):
                lay.hline(x, sy, ww, 'D', 2.0 if not candle else 3.4, emis=candle)
                for k in range(0, ww - 3, 5):
                    lay.rect(x + k + 1, sy - 3, 3, 3, 'D' if (k // 5) % 2 else 'I', 1.4 if not candle else 2.6,
                             emis=candle)
                    lay.px(x + k + 2, sy - 4, 'P', 3.4 if not candle else 5.0, emis=candle)
            if candle:
                cx_ = x + (3 * ww) // 4
                lay.rect(cx_, y0 + 15, 1, 3, 'P', 5.0, emis=True)
                lay.px(cx_, y0 + 14, 'L', 5.4, emis=True)
                lay.rect(cx_ - 2, y0 + 18, 5, 1, 'D', 3.4, emis=True)                 # the saucer
                self.candle_xy = (cx_, y0 + 14)
            lay.rect(x - 1, y0 - 1, ww + 2, 1, 'D', 2.4)
            lay.vline(x - 1, y0, FEET - y0 - 2, 'D', 2.4)
            lay.vline(x + ww, y0, FEET - y0 - 2, 'D', 2.0)
            lay.vline(x + ww // 2, y0, FEET - y0 - 2, 'D', 2.0)
            self.windows['ws_%d' % i] = (x, y0, ww, FEET - y0 - 2)
        # the light well's grating at the pavement
        lay.rect(a - 4, FEET - 2, b - a + 8, 2, 'I', 1.6, hgt=0.6)
        for xx in range(a - 4, b + 4, 3):
            lay.px(xx, FEET - 2, 'I', 3.0)
        K.snowcap(lay, a - 4, FEET - 2, b - a + 8, 1, seed=891)
        # painted sign, the boot on its bracket
        lay.rect(a + 6, 262, 86, 9, 'W', 2.0, hgt=0.3)
        K.text(lay, 'SCHUHMACHEREI', a + 8, 264, 'P', 4.4)
        K.text(lay, 'PIETSCH', a + 62, 264, 'P', 3.6)
        bx = b - 8
        lay.hline(bx - 6, 258, 10, 'I', 2.0)
        lay.vline(bx, 258, 3, 'I', 2.0)
        lay.rect(bx - 2, 261, 4, 8, 'D', 2.8, hgt=0.7)                                   # the boot
        lay.rect(bx - 2, 268, 7, 3, 'D', 2.8, hgt=0.7)
        if self.after:
            self.light('candle', (self.candle_xy[0] + X0, self.candle_xy[1]), 'warm', 0.45, 40, height=4,
                       dynamic=True)

    def extras(self):
        """The side wing's bicycle, a sled, a lilac bush in the corner, a bench under snow."""
        lay = self.lay
        bx = lx(1458)
        for (cx, cy) in ((bx, 288), (bx + 18, 288)):                                     # the bicycle
            m = K.disc(13)
            lay.put(K.edge_of(m), cx - 6, cy - 6, 'I', 2.2, hgt=0.6)
            lay.px(cx, cy, 'I', 3.0)
        lay.line(bx, 288, bx + 8, 278, 'I', 2.6)
        lay.line(bx + 8, 278, bx + 18, 288, 'I', 2.6)
        lay.line(bx + 8, 278, bx + 16, 278, 'I', 2.4)
        lay.line(bx + 16, 278, bx + 18, 288, 'I', 2.4)
        lay.line(bx + 7, 276, bx + 9, 280, 'I', 2.0)
        lay.rect(bx + 5, 275, 5, 2, 'D', 2.2)                                            # saddle
        lay.line(bx + 15, 274, bx + 17, 278, 'I', 2.6)
        lay.hline(bx + 13, 274, 5, 'I', 2.4)
        K.snowcap(lay, bx + 5, 275, 5, 1, seed=901)
        sx = lx(1302)                                                                     # a child's sled
        lay.line(sx, 296, sx + 2, 270, 'D', 3.0)
        lay.line(sx + 8, 296, sx + 10, 270, 'D', 2.6)
        for yy in range(274, 294, 5):
            lay.hline(sx + 1, yy, 8, 'D', 3.2)
        # the lilac in the corner between front and side wing: bare twigs, snow on them
        rng = np.random.default_rng(902)
        base_x = lx(1206)

        def twig(x, y, ang, ln, depth):
            x1 = x + math.cos(ang) * ln
            y1 = y - math.sin(ang) * ln
            n = max(1, int(ln))
            for i in range(n + 1):
                t = i / n
                lay.px(int(x + (x1 - x) * t), int(y + (y1 - y) * t), 'I', 1.6, hgt=0.4)
            if math.sin(ang) > 0.3 and rng.random() < 0.6:
                lay.px(int(x1), int(y1) - 1, 'SN', 5.4)
            if depth > 0:
                for da in (-0.5 - rng.random() * 0.2, 0.4 + rng.random() * 0.3):
                    twig(x1, y1, ang + da, ln * 0.68, depth - 1)
        for k in range(5):
            twig(base_x + k * 3 - 6, 296, math.pi / 2 + (k - 2) * 0.22, 14 + rng.random() * 6, 3)

    # ------------------------------------------------------------------ ambient + build
    def ambient(self):
        lay = self.lay
        f = np.zeros((H, W), np.float32)
        ys = np.arange(H, dtype=np.float32)[:, None]
        xs = np.arange(W, dtype=np.float32)[None, :]
        f += -0.45 * np.clip((ys - 120) / 160, 0, 1)                    # the lower façades in the well's shadow
        f += -0.3 * np.clip((xs - (W - 40)) / 40, 0, 1)
        f[lay.emis] = 0
        lay.amb_field(f)

    def scene_lights(self):
        return [
            {'name': 'night_sky', 'pos': (480.0, -160.0), 'kind': 'cold', 'energy': 0.48, 'radius': 820,
             'height': 220},
            {'name': 'snow_bounce', 'pos': (500.0, 380.0), 'kind': 'cold', 'energy': 0.25, 'radius': 360,
             'height': 30},
        ]

    def build(self):
        self.facades()
        self.roofs()
        self.all_windows()
        self.lodge()
        self.passage()
        self.street_door()
        self.doors()
        self.ground()
        self.coal_and_hatch()
        self.bins()
        self.pump()
        self.rack()
        self.workshop()
        self.extras()
        self.laundry()
        self.basket()
        self.ambient()
        return self.lay

    def all_lights(self):
        return self.scene_lights() + self.lights


def bake_yard(cfg: dict | None = None):
    """Builds and bakes the courtyard.  Lights marked dynamic (the car's headlights, the candle, the stairwells
    after the sweep) are left to the engine's lights: the after-state's patches then differ from the base only where
    something is painted differently -- no baked glow spills past a patch's edge."""
    yd = Yard(cfg)
    yd.build()
    lights = [li for li in yd.all_lights() if not li.get('dynamic')]
    F_ = K.light_fields(yd.lay, lights)
    K.add_pools(F_, lights, FEET - 6, H, W)
    K.resolve(yd.lay, F_, exposure=0.84)
    yd.F = F_
    return yd


# =========================================================================== parallax layers
def sky_layer(w=670, h=200):
    lay = K.tlayer(w, h, 'yd_sky', 'B')
    ys = np.arange(h, dtype=np.float32)[:, None] / h
    nz = K.periodic_noise(w, h, 90, 18, 7, octaves=4)
    t = 0.3 + ys * 2.2 + (nz - 0.5) * 0.8
    lay.put(np.ones((h, w), bool), 0, 0, 'U', np.clip(t, 0, 3.4).astype(np.float32), flat=False)
    cloud = (nz > 0.56) & (ys > 0.35)
    lay.put(cloud, 0, 0, 'U', 2.6, flat=False)
    lay.put(cloud & (nz > 0.66), 0, 0, 'W', 2.2, flat=False)
    rng = np.random.default_rng(17)
    for _ in range(24):
        x, y = int(rng.integers(0, w)), int(rng.integers(2, int(h * 0.3)))
        lay.px(x, y, 'SN', 3.0 + rng.random() * 2.5)
    K.resolve(lay, None, exposure=1.0)
    return lay


def dome_layer(hist=False, w=150, h=82):
    """The Great Hall far away above the roofs (parallax 0.08; layer y 0 = world y 0): the floodlit dome with its
    ribs, the lantern with the eagle on the globe, the arcaded drum, the cornice, and four long banners hanging on
    the drum -- neutral: dark grey cloth with the fictional Reichssiegel (black disc, white pillar) / historical:
    red cloth, white disc, black swastika (Symbols.pick, 12.4); searchlight beams standing in the haze behind it.
    The courtyard's roofs hide the base; the far roofscape is kept low here (roofs_layer), so drum and banners show."""
    import env_berlin_insignia as INS
    import env_berlin_kit as BK
    lay = K.tlayer(w, h, 'yd_dome', 'B')
    cx = w // 2
    base_y, rx, hh = 48, 54, 34                                    # dome springing row, half width, height
    # searchlight beams first (the dome stands in front of them)
    for (x0, x1, t) in ((cx - 66, cx - 92, 2.2), (cx - 30, cx - 40, 2.0), (cx + 34, cx + 50, 2.0),
                        (cx + 64, cx + 98, 2.2)):
        for y in range(0, h - 20):
            u = 1 - y / float(h - 20)
            xx = int(round(x1 + (x0 - x1) * (y / float(h - 20))))
            for dx in (0, 1):
                if (y + dx) % 2 == 0 or u > 0.35:
                    lay.px(xx + dx, y, 'U', t + 0.6 * (1 - u))
    # the haze around the floodlit dome
    for y in range(h):
        for x in range(w):
            if ((x - cx) / (rx + 16.0)) ** 2 + ((y - base_y + 6) / 44.0) ** 2 < 1 and (x + y) % 3 == 0:
                lay.px(x, y, 'U', 2.0)
    # the dome: floodlit from below, ribs, a snow line on the upper shell
    for x in range(cx - rx, cx + rx + 1):
        dx = (x - cx) / float(rx)
        top = base_y - int(round(hh * math.sqrt(max(0.0, 1 - dx * dx))))
        rib = (x - cx) % 8 == 0
        for y in range(top, base_y):
            k = (base_y - y) / float(hh)                            # 0 at the springing .. 1 at the crown
            if k < 0.5:
                lay.px(x, y, 'W', 4.2 - k * 2.4 + rib * 0.7 - abs(dx) * 0.9, flat=False)     # floodlit
            else:
                lay.px(x, y, 'U', 4.0 - (k - 0.5) * 1.8 + rib * 0.6 - abs(dx) * 0.6, flat=False)
        lay.px(x, top, 'SN', 4.2 - abs(dx) * 1.2)
    # the lantern, the globe, the eagle on it (a dark silhouette at this distance)
    ly0 = base_y - hh - 8
    lay.rect(cx - 4, ly0, 9, 9, 'W', 3.0)
    for x in range(cx - 4, cx + 5, 2):
        lay.vline(x, ly0 + 2, 6, 'U', 1.4)
    lay.rect(cx - 5, ly0 - 1, 11, 2, 'W', 4.0)
    lay.rect(cx - 1, ly0 - 4, 3, 3, 'U', 3.2)                       # the globe
    lay.hline(cx - 3, ly0 - 6, 7, 'N', 1.6)                          # the eagle's spread wings
    lay.rect(cx - 1, ly0 - 7, 3, 3, 'N', 1.6)
    # the drum: an arcade of floodlit piers
    dw = rx + 6
    lay.rect(cx - dw, base_y, 2 * dw + 1, 13, 'U', 1.4)
    for x in range(cx - dw, cx + dw + 1, 4):
        lay.rect(x, base_y + 1, 2, 12, 'W', 3.6 - abs(x - cx) / dw * 0.8)
    lay.rect(cx - dw - 2, base_y - 1, 2 * dw + 5, 2, 'W', 4.4)
    lay.rect(cx - dw - 6, base_y + 13, 2 * dw + 13, 3, 'W', 4.0)     # the cornice
    lay.rect(cx - dw - 8, base_y + 16, 2 * dw + 17, h - base_y - 16, 'W', 2.6)
    # four long banners on the drum
    d = 5
    sw = INS.swastika_mask(d)
    disc, pillar = BK.reichssiegel_mask(d)
    for bx in (cx - 46, cx - 18, cx + 12, cx + 40):
        top = base_y - 1
        for xx in range(7):
            fold = 0.4 * math.sin(xx / 7.0 * math.pi * 2 + bx)
            lay.rect(bx + xx, top, 1, 19 - (xx % 2), 'R' if hist else 'W', (2.6 if hist else 1.5) + fold)
        lay.hline(bx - 1, top - 1, 9, 'N', 1.2)                       # the rod
        dx0, dy0 = bx + 1, top + 3
        if hist:
            lay.put(disc, dx0, dy0, 'SN', 5.4)
            lay.put(sw, dx0, dy0, 'N', 0.2)
        else:
            lay.put(disc, dx0, dy0, 'N', 0.3)
            lay.put(pillar, dx0, dy0, 'SN', 5.0)
    K.resolve(lay, None, exposure=1.0)
    return lay


def roofs_layer(w=770, h=110):
    """The roofscape beyond the courtyard (layer y 0 = world y -10, parallax 0.3): roofs, chimneys, firewalls, a
    lit attic window, a church spire.  Behind the dome (layer x ~320..600 at both camera stops) the roofs stay low,
    so the Great Hall's drum and banners stand clear above the courtyard."""
    lay = K.tlayer(w, h, 'yd_roofs', 'B')
    rng = np.random.default_rng(931)
    base = h
    x = 0
    while x < w:
        bw = int(rng.integers(50, 120))
        top = int(rng.integers(40, 76))
        low = x < 610 and x + bw > 310
        if low:
            top = max(top, 76)
        for xx in range(x, min(w, x + bw)):
            for yy in range(top, base):
                lay.px(xx, yy, 'U', 1.0 + (yy == top) * 1.8 + ((xx - x) % 17 == 0) * 0.3)
        for cx in range(x + 6, x + bw - 6, int(rng.integers(16, 30))):
            ch = int(rng.integers(6, 14)) if not low else int(rng.integers(3, 6))
            lay.rect(cx, top - ch, 5, ch, 'U', 1.6)
            lay.hline(cx, top - ch, 5, 'SN', 3.4)
        if rng.random() < 0.4:
            lay.rect(x + 10, top + 6, 4, 5, 'L', 2.4, emis=True)
        x += bw
    sx = 690                                                                             # a church spire
    for y in range(4, 60):
        half = int((y - 4) * 0.12) + 1
        lay.hline(sx - half, y, 2 * half + 1, 'U', 1.4)
    lay.px(sx, 3, 'U', 2.4)
    K.resolve(lay, None, exposure=1.0)
    return lay


def fg_layer(w=1100, h=42):
    """The courtyard's near edge (parallax 1.25; layer y 0 = world y 318): trodden snow over the setts with
    footprints and a sledge track, the lit windows of the ground floor laid on the snow as warm panes, a gully
    grate, a frozen puddle with a window in it; things left out: a handcart with a sack of briquettes, a crate of
    milk bottles, a broom, a bucket, a child's lost mitten; the low railing of a light well; cat tracks."""
    lay = K.tlayer(w, h, 'fg_yard', 'B')
    rng = np.random.default_rng(941)
    nz = pg.value_noise(w, h, 7, 942, octaves=3)
    fine = pg.value_noise(w, h, 2, 943, octaves=2)
    xs = np.arange(w)
    # warm panes of window light on the snow (lodge, the lit ground floor, the hall door) -- placed for the
    # parallax at the middle camera stop
    panes = [(300, 26), (560, 30), (790, 20), (980, 24)]
    warm = np.zeros((h, w), np.float32)
    for (px0, pw) in panes:
        for y in range(2, 30):
            sk = int((y - 2) * 0.5)                                    # the light falls slanting toward us
            for x in range(px0 + sk, px0 + pw + sk):
                if 0 <= x < w:
                    edge = min(x - px0 - sk, px0 + pw + sk - 1 - x, y - 2, 29 - y)
                    warm[y, x] = max(warm[y, x], min(1.0, 0.35 + edge * 0.25) * (1 - y / 40.0))
            for x in range(px0 + pw // 2 - 1 + sk, px0 + pw // 2 + 1 + sk):  # the window cross as a shadow
                if 0 <= x < w:
                    warm[y, x] *= 0.3
    thr = pg.bayer(w, h, 1, 0, 4)
    for y in range(h):
        for x in range(w):
            dark = y / float(h)
            t = 2.5 + (nz[y, x] - 0.5) * 0.9 + (fine[y, x] - 0.5) * 0.4 - dark * 1.3
            if fine[y, x] > 0.8 and nz[y, x] < 0.4:
                lay.px(x, y, 'W', 1.4 + 0.4 * (x % 5 == 0), flat=False)               # a sett showing through
            else:
                lay.px(x, y, 'SN', max(0.4, t), flat=False)
    # footprints from the passage toward the doors, a sledge track
    for k in range(70):
        fx = 20 + k * 15 + int(rng.integers(-2, 3))
        fy = 6 + (k % 2) * 4 + int(rng.integers(0, 2))
        if fx < w - 4:
            lay.rect(fx, fy, 3, 2, 'U', 2.6)
            lay.px(fx + 1, fy + 2, 'U', 2.2)
    for x in range(140, 720):
        y = 19 + int(2 * math.sin(x / 70.0))
        lay.px(x, y, 'U', 2.4)
        lay.px(x, y + 4, 'U', 2.4)
    # a gully grate, a frozen puddle with a lit window in it
    lay.rect(470, 12, 12, 5, 'I', 1.0)
    for k in range(5):
        lay.vline(471 + k * 2 + (k > 2), 12, 5, 'W', 2.6)
    for y in range(26, 34):
        for x in range(860, 900):
            if ((x - 880) / 20.0) ** 2 + ((y - 30) / 4.0) ** 2 < 1:
                lay.px(x, y, 'U', 3.2 + ((x + y) % 6 == 0) * 1.2)
    lay.rect(874, 28, 5, 3, 'L', 3.6)
    lay.px(876, 29, 'L', 4.6)
    # the handcart with a sack of briquettes (left), its shaft lying in the snow
    hx = 96
    lay.rect(hx, 14, 34, 9, 'D', 1.6, hgt=0.6)
    lay.hline(hx, 14, 34, 'D', 2.8)
    for k in range(0, 34, 6):
        lay.vline(hx + k, 15, 8, 'D', 1.0)
    lay.rect(hx + 4, 4, 24, 10, 'Q', 1.2, hgt=0.5)                     # the sack
    lay.hline(hx + 6, 4, 20, 'Q', 2.0)
    lay.rect(hx + 13, 2, 4, 3, 'Q', 1.0)
    K.snowcap(lay, hx + 4, 3, 24, 2, seed=944)
    for (wx_, wy_) in ((hx + 6, 26), (hx + 28, 26)):                    # wheels
        m = K.disc(11)
        lay.put(K.edge_of(m), wx_ - 5, wy_ - 5, 'I', 1.6)
        lay.px(wx_, wy_, 'I', 2.6)
    lay.line(hx + 34, 18, hx + 70, 30, 'D', 2.0)                        # the shaft
    lay.line(hx + 34, 19, hx + 70, 31, 'D', 1.2)
    # a crate of empty milk bottles by the lodge, frost in them
    cx0 = 640
    lay.rect(cx0, 8, 22, 12, 'D', 2.0, hgt=0.6)
    lay.hline(cx0, 8, 22, 'D', 3.2)
    for k in range(5):
        bx = cx0 + 1 + k * 4
        lay.rect(bx, 1, 3, 8, 'SN', 3.0)
        lay.px(bx + 1, 0, 'SN', 4.4)
        lay.px(bx, 3, 'SN', 5.2)
    lay.hline(cx0, 13, 22, 'D', 1.0)
    # a broom and a bucket against the cart
    lay.line(70, 0, 84, 30, 'D', 2.2)
    for k in range(6):
        lay.line(82 + k, 28, 80 + k * 2, 36, 'D', 1.6)
    bx = 150
    lay.rect(bx, 20, 10, 10, 'W', 2.4, hgt=0.6)
    lay.hline(bx, 20, 10, 'W', 3.8)
    lay.hline(bx + 1, 21, 8, 'SN', 4.2)                                  # frozen water in it
    lay.line(bx, 20, bx + 5, 15, 'I', 1.8)
    lay.line(bx + 9, 20, bx + 5, 15, 'I', 1.8)
    # the low railing of a light well, snow on its top bar, the well's dark mouth
    rx0 = 900
    lay.rect(rx0, 16, 90, 10, 'N', 0.6)
    for x in range(rx0, rx0 + 90, 6):
        lay.vline(x, 4, 13, 'I', 1.8)
    lay.hline(rx0, 4, 90, 'I', 2.6)
    K.snowcap(lay, rx0, 3, 90, 2, seed=945)
    # a child's red mitten, cat tracks
    lay.rect(420, 20, 3, 2, 'R', 2.4)
    lay.px(423, 20, 'R', 2.0)
    for k in range(16):
        lay.px(700 + k * 5, 33 - (k % 2), 'U', 2.0)
    # darker toward the bottom edge (the camera stands in the shadow of the front wing)
    K.resolve(lay, None, exposure=1.0)
    return lay
