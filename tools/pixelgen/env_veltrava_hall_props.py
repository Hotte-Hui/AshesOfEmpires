"""env_veltrava_hall_props -- y-sorted prop sprites of L_C3_Hall (tone space, baked with the scene lights).

Every prop stands against the back wall (base_y < walk band 296) so actors pass in front of it.
Flags: one prop per flag; USSR and Reich exist as neutral `flag_*.png` plus `flag_*_hist.png`
(TECHNICAL_ARCHITECTURE 12.4, resolved by Symbols.pick in layer_stack.gd):
    flag_reich       fictional Reichssiegel (white pillar in a black disc) on grey-black
    flag_reich_hist  the historical swastika flag (small, limp, in-world only)
    flag_ussr        red with a fictional gear-and-wheat emblem
    flag_ussr_hist   the Soviet red flag with hammer, sickle and star
The seating-plan easel shows exactly the puzzle facts: horseshoe table, presidium at the top,
microphones numbered clockwise from the presidium (1), secretariat table at the open end (12).
"""
from __future__ import annotations

import math

import numpy as np

import env_veltrava_hall_kit as kit
import env_veltrava_hall_layout as L
import pg

R = kit.palais_ramps()


class Prop:
    def __init__(self, name, x, base_y, w, h, note='', hist=False):
        self.name = name
        self.w, self.h = w, h
        self.base_y = base_y
        self.x = int(x)
        self.y = int(base_y - (h - 1))
        self.lay = kit.TLayer(w, h, R, name)
        self.note = note
        self.lights = []
        self.hist = hist             # a *_hist variant layer exists (set by the builder)
        self.hist_lay = None

    @property
    def pos(self):
        return (self.x, self.y)


def bevel(lay, x, y, w, h, ramp, face, hi=None, lo=None, hgt=0.5):
    lay.rect(x, y, w, h, ramp, face, hgt=hgt)
    if hi is not None:
        lay.rect(x, y, w, 1, ramp, hi, hgt=hgt * 0.8)
        lay.rect(x, y, 1, h, ramp, hi, hgt=hgt * 0.8)
    if lo is not None:
        lay.rect(x, y + h - 1, w, 1, ramp, lo, hgt=hgt * 0.6)
        lay.rect(x + w - 1, y, 1, h, ramp, lo, hgt=hgt * 0.6)


# =========================================================================== flags
BW, BH = 12, 24          # banner (vertical flag) size


def _banner_field(kind: str, hist: bool):
    """(ramp, tone) per banner pixel for a vertical banner BW x BH (the national designs rotated for a
    hanging banner: Nordic crosses keep their arm offset toward the hoist = top)."""
    ramp = np.full((BH, BW), 'C', object)
    tone = np.full((BH, BW), 3.0, np.float32)

    def fill(r, t, m):
        ramp[m] = r
        tone[m] = t
    yy, xx = np.mgrid[0:BH, 0:BW]
    allm = np.ones((BH, BW), bool)
    if kind == 'commission':
        fill('C', 2.6, allm)
        br, wa = kit.commission_arms(10, 9)
        m = np.zeros((BH, BW), bool); m[5:14, 1:11] = br
        fill('P', 6.6, m)
        m2 = np.zeros((BH, BW), bool); m2[5:14, 1:11] = wa
        fill('P', 5.4, m2)
        fill('P', 6.2, (yy == 18) & (xx % 3 != 0))
    elif kind == 'sweden':
        fill('C', 2.8, allm)
        fill('B', 4.4, (np.abs(xx - 5.5) < 1.2) | ((yy >= 7) & (yy <= 9)))
    elif kind == 'finland':
        fill('P', 6.4, allm)
        fill('C', 2.6, (np.abs(xx - 5.5) < 1.6) | ((yy >= 7) & (yy <= 10)))
    elif kind == 'switzerland':
        fill('R', 2.8, allm)
        cross = ((np.abs(xx - 5.5) < 1.2) & (np.abs(yy - 11.5) < 4.2)) | \
                ((np.abs(yy - 11.5) < 1.2) & (np.abs(xx - 5.5) < 4.2))
        fill('P', 6.8, cross)
    elif kind == 'ussr':
        fill('R', 2.6, allm)
        if hist:
            # star above a hammer and sickle, in the upper hoist corner (small, flat gold)
            emblem = ['.#...',
                      '###..',
                      '.#...',
                      '.....',
                      '.##.#',
                      '...##',
                      '#.##.',
                      '.##.#']
        else:
            # fictional emblem: a small gear ring framed by two wheat ears (no hammer and sickle)
            emblem = ['..#..',
                      '.###.',
                      '##.##',
                      '.###.',
                      '..#..',
                      '#...#',
                      '.#.#.',
                      '..#..']
        for y, row in enumerate(emblem):
            for x, ch in enumerate(row):
                if ch == '#':
                    fill('B', 4.2, (xx == x + 1) & (yy == y + 1))
    elif kind == 'reich':
        if hist:
            # historical national flag: red field, white disc, black hooked cross (in-world only, small)
            fill('R', 2.6, allm)
            fill('P', 6.4, (xx - 5.5) ** 2 + (yy - 11.5) ** 2 <= 4.6 ** 2)
            cross = ['#.###',
                     '#.#..',
                     '#####',
                     '..#.#',
                     '###.#']
            for y, row in enumerate(cross):
                for x, ch in enumerate(row):
                    if ch == '#':
                        fill('I', 1.0, (xx == x + 3) & (yy == y + 9))
        else:
            # neutral default: the fictional Reichssiegel (white pillar in a black disc) on grey-black
            fill('M', 1.8, allm)
            disc, pillar = kit.reichssiegel_mask(9)
            m = np.zeros((BH, BW), bool); m[7:16, 1:10] = disc
            fill('N', 0.0, m)
            m2 = np.zeros((BH, BW), bool); m2[7:16, 1:10] = pillar
            fill('P', 6.4, m2)
    return ramp, tone


def flag(kind, x, hist=False):
    w, h = 18, 74
    p = Prop('flag_' + kind, x - w // 2, L.FLAG_BASE, w, h, 'flag on a brass pole: ' + kind)
    paint_flag(p.lay, kind, hist)
    return p


def paint_flag(lay, kind, hist):
    cx = 8
    # finial (gilt spear) + pole + cross foot
    lay.px(cx, 0, 'B', 5.0, hgt=0.9); lay.px(cx + 1, 0, 'B', 4.0, hgt=0.9)
    lay.rect(cx - 1, 1, 4, 2, 'B', 4.4, hgt=0.9)
    lay.rect(cx, 3, 2, 3, 'B', 3.6, hgt=0.85)
    lay.rect(cx, 6, 2, 62, 'B', 3.0, hgt=0.7)
    lay.rect(cx, 6, 1, 62, 'B', 4.4, hgt=0.75)
    lay.rect(cx - 4, 68, 10, 2, 'B', 3.4, hgt=0.7)
    lay.rect(cx - 4, 68, 10, 1, 'B', 4.8, hgt=0.75)
    lay.rect(cx - 6, 70, 14, 2, 'D', 2.6, hgt=0.6)
    lay.rect(cx - 7, 72, 16, 2, 'D', 1.8, hgt=0.5)
    # crossbar the banner hangs from
    lay.rect(1, 7, 16, 2, 'B', 3.4, hgt=0.8)
    lay.rect(1, 7, 16, 1, 'B', 4.8, hgt=0.85)
    lay.px(0, 7, 'B', 4.0); lay.px(17, 7, 'B', 4.0)
    ramp, tone = _banner_field(kind, hist)
    bx, by = 3, 9
    for yy in range(BH):
        for xx in range(BW):
            # limp folds: shade by a gentle vertical fold profile
            fold = 0.55 * math.sin(xx / BW * 2 * math.pi * 1.5 + 0.4)
            t = float(tone[yy, xx]) + fold
            lay.px(bx + xx, by + yy, ramp[yy, xx], t, hgt=0.5 + 0.2 * fold, flat=False)
    # hem shadow + gilt fringe
    for xx in range(BW):
        lay.px(bx + xx, by + BH, 'B', 3.6 if xx % 2 else 2.6, hgt=0.5)
        if xx % 2 == 0:
            lay.px(bx + xx, by + BH + 1, 'B', 3.0, hgt=0.45)
    lay.rect(bx, by, BW, 1, 'W', 2.0, hgt=0.4)                             # shadow under the bar
    lay.rect(bx + BW, by + 1, 1, BH, 'W', 2.4, hgt=0.0)
    # tassel cord
    lay.px(bx + BW + 1, by + 2, 'B', 3.6)
    lay.px(bx + BW + 1, by + 3, 'B', 3.0)


def flags():
    out = []
    for kind, x in zip(L.FLAG_ORDER, L.FLAG_X):
        p = flag(kind, x)
        if kind in ('ussr', 'reich'):
            hp = flag(kind, x, hist=True)
            p.hist = True
            p.hist_lay = hp.lay
            p.note += ' (neutral default; *_hist = historical flag)'
        out.append(p)
    return out


# =========================================================================== vestibule
def cloak_counter():
    x0, x1 = L.CLOAK[0] - 4, L.CLOAK[1] + 4
    T = 18                       # counter top (local y)
    p = Prop('cloak_counter', x0, 292, x1 - x0, T + 31, 'cloakroom counter: bell, numbered tokens, lamp')
    lay = p.lay
    w = x1 - x0
    lay.rect(0, T - 3, w, 3, 'D', 4.4, hgt=0.7)                            # top surface
    lay.rect(0, T - 3, w, 1, 'D', 3.0, hgt=0.65)
    top_m = np.ones((3, w), bool)
    lay.paint_normal(top_m, 0, T - 3, (0.0, 0.9, 0.44))
    lay.rect(0, T, w, 1, 'B', 3.6, hgt=0.8)                                # brass edge
    lay.rect(1, T + 1, w - 2, 30, 'D', 2.6, hgt=0.4)
    n = 4
    pw = (w - 10) // n
    for k in range(n):
        xx = 5 + k * pw
        bevel(lay, xx, T + 4, pw - 4, 18, 'D', 2.2, hi=3.6, lo=1.2, hgt=0.3)
        bevel(lay, xx + 2, T + 6, pw - 8, 14, 'D', 3.0, hi=4.0, lo=1.6, hgt=0.45)
        lay.px(xx + pw // 2 - 2, T + 12, 'B', 4.0, hgt=0.6)                # brass rosette
    lay.rect(1, T + 25, w - 2, 5, 'D', 1.4, hgt=0.3)
    lay.rect(1, T + 25, w - 2, 1, 'D', 2.8, hgt=0.35)
    # tray with numbered brass tokens, the bell, a ledger
    lay.rect(10, T - 5, 16, 2, 'D', 3.0, hgt=0.75)
    for k in range(6):
        lay.ellipse(12 + k * 2.4, T - 5.5, 1.1, 0.8, 'B', 4.4 if k % 2 else 3.6, hgt=0.85)
    lay.ellipse(38.5, T - 5, 3.0, 2.0, 'B', 3.6, hgt=0.85)                 # bell
    lay.rect(38, T - 9, 1, 2, 'B', 4.8, hgt=0.9)
    lay.px(37, T - 6, 'B', 5.4)
    lay.poly([(48, T - 4), (60, T - 5), (72, T - 4), (72, T - 2), (48, T - 2)], 'P', 5.6, hgt=0.7)
    lay.line(60, T - 5, 60, T - 2, 'P', 3.4)
    for k in range(2):
        lay.hline(50, T - 4 + k, 8, 'I', 2.6)
    # brass lamp with an amber silk shade at the right end: the warm focal of the vestibule
    lx = w - 12
    lay.rect(lx - 3, T - 5, 8, 2, 'B', 3.0, hgt=0.8)
    lay.rect(lx - 3, T - 5, 8, 1, 'B', 4.6, hgt=0.85)
    lay.rect(lx, T - 15, 2, 10, 'B', 3.4, hgt=0.85)
    lay.px(lx, T - 15, 'B', 5.0)
    shade = [(lx - 6, T - 15), (lx + 7, T - 15), (lx + 5, T - 23), (lx - 4, T - 23)]
    m, mx, my = lay.poly(shade, 'A', 3.6, emis=True)
    lay.put(kit.edge_of(m), mx, my, 'A', 2.6, emis=True)
    lay.rect(lx - 5, T - 15, 12, 1, 'A', 5.0, emis=True)
    lay.rect(lx - 3, T - 22, 8, 1, 'A', 4.6, emis=True)
    p.lights.append({'name': 'cloak_lamp', 'pos': (x0 + lx + 1, p.y + T - 14), 'kind': 'warm', 'energy': 1.35,
                     'radius': 130, 'height': 20, 'pool': True})
    return p


def palm(name, x, base_y=292, seed=0, h=70, note='Kentia palm in a Jugendstil jardiniere'):
    w = 34
    p = Prop(name, x - w // 2, base_y, w, h, note)
    lay = p.lay
    cx = w // 2
    # jardiniere: majolica pot on a little bronze stand
    lay.poly([(cx - 8, h - 22), (cx + 8, h - 22), (cx + 6, h - 6), (cx - 6, h - 6)], 'G', 4.0, hgt=0.7)
    lay.rect(cx - 9, h - 24, 18, 3, 'G', 5.4, hgt=0.8)
    lay.rect(cx - 9, h - 24, 18, 1, 'M', 5.6, hgt=0.85)
    for k in range(cx - 6, cx + 7, 3):
        lay.px(k, h - 16, 'B', 4.0, hgt=0.8)
    lay.rect(cx - 5, h - 6, 10, 2, 'B', 3.0, hgt=0.7)
    lay.rect(cx - 6, h - 4, 2, 4, 'B', 2.6, hgt=0.6)
    lay.rect(cx + 4, h - 4, 2, 4, 'B', 2.6, hgt=0.6)
    # fronds: arching stems with leaflets
    rng = np.random.default_rng(seed)
    base = (cx, h - 24)
    for k in range(9):
        ang = math.radians(-160 + k * 17 + rng.uniform(-5, 5))
        ln = rng.uniform(26, 38) * (0.8 if k in (0, 8) else 1.0)
        pts = []
        for j in range(14):
            t = j / 13
            px_ = base[0] + math.cos(ang) * ln * t
            py_ = base[1] + math.sin(ang) * ln * t + (t ** 2) * ln * 0.55
            pts.append((px_, py_))
        for (a, b) in zip(pts[:-1], pts[1:]):
            lay.line(a[0], a[1], b[0], b[1], 'G', 3.6, hgt=0.6)
        for j in range(3, 14):
            px_, py_ = pts[j]
            for s in (-1, 1):
                ll = 4 + (j % 3)
                ex = px_ + s * 1.5
                ey = py_ + ll
                lay.line(px_, py_, ex, ey, 'G', 4.8 if s < 0 else 3.0, hgt=0.55)
    return p


# =========================================================================== foyer
def buffet():
    x0, x1 = L.BUFFET
    T = 30                     # table top (local y)
    p = Prop('buffet', x0, 293, x1 - x0, T + 33, 'buffet: untouched Sekt and caviar on crushed ice')
    lay = p.lay
    w = x1 - x0
    # floor-length white tablecloth with folds and a lace edge
    lay.rect(0, T, w, 33, 'P', 5.4, hgt=0.4)
    lay.rect(0, T, w, 2, 'P', 6.6, hgt=0.6)
    for k in range(3, w, 6):
        lay.vline(k, T + 3, 30, 'P', 4.6)
        lay.vline(k + 1, T + 3, 30, 'P', 6.0)
    for k in range(0, w, 3):
        lay.px(k, T + 10, 'P', 6.8)
    lay.rect(0, T + 31, w, 2, 'P', 4.0, hgt=0.3)
    top = np.ones((2, w), bool)
    lay.paint_normal(top, 0, T, (0.0, 0.9, 0.44))
    # silver: tiered stand, platters, ice bowls with caviar tins, champagne coolers with bottles
    lay.rect(4, T - 2, 14, 2, 'S', 4.0, hgt=0.8)                         # platter (canapés)
    for k in range(5):
        lay.px(5 + k * 3, T - 3, 'P', 6.0); lay.px(6 + k * 3, T - 3, 'R', 3.0)
    # caviar on crushed ice
    lay.ellipse(28, T - 2, 6.5, 2.2, 'S', 5.0, hgt=0.8)
    lay.ellipse(28, T - 3, 4.0, 1.4, 'S', 6.0, hgt=0.85)
    lay.rect(26, T - 5, 5, 2, 'I', 1.4, hgt=0.9)
    lay.rect(26, T - 5, 5, 1, 'S', 3.0, hgt=0.9)
    # champagne cooler with two bottles (gold foil)
    for (bx, t) in ((40, 3.4), (52, 3.0)):
        lay.rect(bx, T - 7, 7, 7, 'S', t, hgt=0.8)
        lay.rect(bx, T - 7, 7, 1, 'S', 5.4, hgt=0.85)
        lay.rect(bx + 2, T - 15, 3, 8, 'G', 2.0, hgt=0.9)
        lay.rect(bx + 2, T - 15, 1, 8, 'G', 3.4, hgt=0.9)
        lay.rect(bx + 2, T - 18, 3, 3, 'B', 4.4, hgt=0.95)
    # neat rows of filled Sekt flutes (untouched)
    for row, yb in enumerate((T - 1, T - 3)):
        for k in range(6 if row == 0 else 5):
            gx = 6 + k * 2 + row + (34 if k > 2 else 0)
            if gx >= w - 2:
                continue
            lay.rect(gx, yb - 4, 1, 3, 'A', 4.4 if row == 0 else 3.8, hgt=0.9)
            lay.px(gx, yb - 5, 'S', 5.0)
            lay.px(gx, yb - 1, 'S', 4.0)
    # small card
    lay.rect(w - 12, T - 5, 8, 4, 'P', 6.4, hgt=0.85)
    lay.hline(w - 11, T - 3, 6, 'I', 2.0)
    return p


def easel():
    """Seating plan of the opening session on a brass easel (the world prop of ev_c3_seating)."""
    bw, bh = 46, 34
    w, h = 48, 64
    p = Prop('easel_seating', L.EASEL_X - w // 2, 294, w, h, 'seating-plan easel (horseshoe, mics 1/2/12)')
    lay = p.lay
    bx, by = 1, 2
    # tripod legs (behind and in front of the board)
    lay.line(w // 2, 0, 6, h - 1, 'B', 3.0)
    lay.line(w // 2 + 1, 0, w - 6, h - 1, 'B', 2.6)
    lay.line(w // 2, 4, w // 2 + 4, h - 3, 'B', 2.0)
    lay.rect(4, h - 1, 5, 1, 'B', 2.4); lay.rect(w - 8, h - 1, 5, 1, 'B', 2.4)
    # board: walnut frame + cream card
    lay.rect(bx - 1, by - 1, bw + 2, bh + 2, 'D', 3.4, hgt=0.7)
    lay.rect(bx - 1, by - 1, bw + 2, 1, 'D', 5.0, hgt=0.75)
    lay.rect(bx, by, bw, bh, 'P', 6.2, hgt=0.5)
    lay.rect(bx, by, bw, 6, 'C', 2.6, hgt=0.5)                             # slate header band
    lay.text('SITZORDNUNG', bx + (bw - kit.text_width('SITZORDNUNG')) // 2, by + 1, 'P', 7.0)
    # the horseshoe: presidium at the top, arms down, open end at the bottom, secretariat table there
    ux0, ux1 = bx + 9, bx + bw - 10
    uy0, uy1 = by + 10, by + 26
    ink = ('I', 1.4)
    lay.rect(ux0, uy0, ux1 - ux0 + 1, 2, *ink)                              # presidium
    lay.rect(ux0, uy0, 2, uy1 - uy0, *ink)                                   # left arm
    lay.rect(ux1 - 1, uy0, 2, uy1 - uy0, *ink)                               # right arm
    sx = (ux0 + ux1) // 2
    lay.rect(sx - 3, uy1 + 1, 7, 2, *ink)                                     # secretariat table
    # microphones (dots) clockwise from the presidium: 1 top centre, 2-5 right arm, 6/7 bottom
    # corners, 8-11 left arm (going up), 12 secretariat; printed numbers only 1, 2 and 12
    mic = ('R', 3.0)
    lay.px(sx, uy0 - 1, *mic, crisp=True)                                    # 1
    for k in range(4):                                                       # 2..5
        lay.px(ux1 + 2, uy0 + 2 + k * 3, *mic, crisp=True)
    lay.px(ux1 + 1, uy1, *mic, crisp=True)                                   # 6 (bottom right corner)
    lay.px(ux0 - 1, uy1, *mic, crisp=True)                                   # 7 (bottom left corner)
    for k in range(4):                                                       # 8..11 (left arm, upward)
        lay.px(ux0 - 2, uy1 - 3 - k * 3, *mic, crisp=True)
    lay.px(sx, uy1 + 4, *mic, crisp=True)                                    # 12
    lay.text('1', sx + 2, uy0 - 6, 'I', 1.0)
    lay.text('2', ux1 + 4, uy0 + 1, 'I', 1.0)
    lay.text('12', sx + 5, uy1 + 2, 'I', 1.0)
    # legend line ('Mikrofone im Uhrzeigersinn ab Vorsitz (1)') as small print
    for k in range(0, 34, 1):
        if (k % 6) != 5:
            lay.px(bx + 6 + k, by + bh - 2, 'P', 3.0, crisp=True)
    # brass ledge the board rests on
    lay.rect(bx - 2, by + bh + 1, bw + 4, 2, 'B', 3.6, hgt=0.8)
    lay.rect(bx - 2, by + bh + 1, bw + 4, 1, 'B', 5.0, hgt=0.85)
    return p


def saal_rope():
    x0, x1 = L.SAAL_DOOR[0] - 2, L.SAAL_DOOR[1] + 2
    w, h = x1 - x0, 30
    p = Prop('saal_rope', x0, 293, w, h, 'brass stanchions with a velvet rope before the Saal doors')
    lay = p.lay
    for px_ in (1, w - 4):
        lay.rect(px_, 3, 3, h - 6, 'B', 3.2, hgt=0.8)
        lay.rect(px_, 3, 1, h - 6, 'B', 4.8, hgt=0.85)
        lay.ellipse(px_ + 1.5, 2.5, 2.2, 2.2, 'B', 4.4, hgt=0.9)
        lay.rect(px_ - 2, h - 3, 7, 3, 'B', 2.8, hgt=0.7)
        lay.rect(px_ - 2, h - 3, 7, 1, 'B', 4.4, hgt=0.75)
    pts = pg.catenary(3, 5, w - 3, 5, 7)
    for (px_, py_) in pts:
        lay.rect(int(round(px_)), int(round(py_)), 1, 2, 'R', 2.4, hgt=0.7)
        lay.px(int(round(px_)), int(round(py_)), 'R', 3.2)
    return p


# =========================================================================== office
def typist_desk():
    x0, x1 = L.TYPIST_DESK
    T = 34
    p = Prop('typist_desk', x0, 293, x1 - x0, T + 30, 'typist desk: typewriter, carbon box, lamp, telephone')
    lay = p.lay
    w = x1 - x0
    lay.rect(1, T, w - 2, 3, 'D', 5.0, hgt=0.6)
    lay.rect(1, T, w - 2, 1, 'D', 6.2, hgt=0.65)
    lay.rect(2, T + 3, w - 4, 26, 'D', 2.6, hgt=0.4)
    for (a, b) in ((3, 19), (w - 19, w - 3)):
        for k in range(3):
            yy = T + 5 + k * 8
            bevel(lay, a, yy, b - a, 7, 'D', 3.2, hi=4.4, lo=1.4, hgt=0.5)
            lay.rect(a + (b - a) // 2 - 1, yy + 3, 3, 1, 'B', 3.8, hgt=0.7)
    lay.rect(20, T + 4, w - 40, 22, 'D', 1.2, hgt=0.0)
    lay.rect(2, T + 27, w - 4, 2, 'D', 1.4, hgt=0.3)
    # typewriter (dark grey enamel, chrome carriage) with a sheet + carbon
    tx = 18
    lay.poly([(tx, T), (tx + 20, T), (tx + 17, T - 9), (tx + 3, T - 9)], 'I', 1.8, hgt=0.7)
    lay.rect(tx + 1, T - 11, 18, 3, 'I', 2.2, hgt=0.8)
    lay.rect(tx, T - 11, 20, 1, 'S', 5.0, hgt=0.85)
    lay.rect(tx - 2, T - 10, 2, 2, 'S', 4.4, hgt=0.8)
    for k in range(5):
        for j in range(3):
            lay.px(tx + 3 + k * 3 + j % 2, T - 6 + j * 2, 'S', 4.0 if (k + j) % 2 else 3.0)
    lay.rect(tx + 4, T - 21, 12, 10, 'P', 6.4, hgt=0.6)
    lay.rect(tx + 5, T - 20, 12, 9, 'I', 2.0, hgt=0.58)                     # carbon behind the sheet
    lay.rect(tx + 4, T - 21, 12, 10, 'P', 6.4, hgt=0.6)
    for k in range(4):
        lay.hline(tx + 5, T - 19 + k * 2, 7 + (k % 2) * 2, 'I', 2.0)
    # box of carbon paper + stacks
    lay.rect(3, T - 4, 12, 4, 'C', 2.0, hgt=0.65)
    lay.rect(3, T - 4, 12, 1, 'C', 3.4, hgt=0.7)
    for k, t in enumerate((5.6, 4.6, 6.0)):
        lay.rect(4 + k, T - 6 - k * 2, 10, 2, 'P', t, hgt=0.7)
    # telephone
    lay.rect(w - 14, T - 5, 10, 5, 'I', 1.6, hgt=0.7)
    lay.ellipse(w - 9, T - 3, 2.5, 1.6, 'S', 4.0, hgt=0.75)
    lay.rect(w - 15, T - 8, 12, 2, 'I', 2.0, hgt=0.8)
    lay.rect(w - 15, T - 8, 12, 1, 'S', 3.6, hgt=0.85)
    # gooseneck lamp
    lx = w - 22
    lay.rect(lx, T - 2, 5, 2, 'I', 2.0, hgt=0.6)
    lay.polyline([(lx + 2, T - 2), (lx + 1, T - 12), (lx - 2, T - 19), (lx - 6, T - 20)], 'S', 3.0)
    shade = [(lx - 12, T - 23), (lx - 5, T - 22), (lx - 4, T - 17), (lx - 11, T - 17)]
    lay.poly(shade, 'G', 3.0, hgt=0.7)
    lay.line(lx - 11, T - 17, lx - 4, T - 17, 'A', 5.0, emis=True)
    lay.rect(lx - 9, T - 16, 3, 1, 'A', 4.4, emis=True)
    p.lights.append({'name': 'typist_lamp', 'pos': (x0 + lx - 7, p.y + T - 15), 'kind': 'warm', 'energy': 0.8,
                     'radius': 84, 'height': 16, 'cone': (-0.2, 1.0, -0.1)})
    # chair (seen from the front, pushed in)
    lay.rect(22, T + 3, 12, 9, 'D', 3.0, hgt=0.7)
    lay.rect(22, T + 3, 12, 1, 'D', 4.8, hgt=0.75)
    lay.rect(21, T + 14, 14, 2, 'D', 3.6, hgt=0.6)
    lay.rect(23, T + 16, 2, 13, 'D', 2.2, hgt=0.5)
    lay.rect(31, T + 16, 2, 13, 'D', 2.2, hgt=0.5)
    return p


def basket_cabinet():
    x0, x1 = L.BASKET
    T = 26
    p = Prop('carbon_basket', x0, 292, x1 - x0, T + 31, 'wire basket of carbon copies on an oak cabinet (booth_log)')
    lay = p.lay
    w = x1 - x0
    lay.rect(0, T, w, 3, 'D', 4.6, hgt=0.7)
    lay.rect(0, T, w, 1, 'D', 6.0, hgt=0.75)
    lay.rect(1, T + 3, w - 2, 28, 'D', 2.6, hgt=0.45)
    bevel(lay, 3, T + 5, w - 6, 10, 'D', 3.2, hi=4.4, lo=1.4, hgt=0.5)
    bevel(lay, 3, T + 17, w - 6, 12, 'D', 3.2, hi=4.4, lo=1.4, hgt=0.5)
    lay.rect(w // 2 - 2, T + 9, 4, 1, 'B', 4.4, hgt=0.8)
    lay.rect(w // 2 - 2, T + 22, 4, 1, 'B', 4.4, hgt=0.8)
    # the wire basket: stacked flimsy carbon copies (violet-grey edges) behind a wire mesh
    bx0, bx1, by0, by1 = 3, w - 3, T - 12, T
    for k in range(9):
        yy = by1 - 2 - k
        off = (k * 3) % 4 - 1
        lay.rect(bx0 + 1 + off, yy, bx1 - bx0 - 2, 1, 'P', 5.6 if k % 2 else 4.8, hgt=0.6)
        if k % 3 == 1:
            lay.rect(bx0 + 2 + off, yy, bx1 - bx0 - 5, 1, 'C', 2.2, hgt=0.6)    # carbon tissue edge
    lay.rect(bx0 + 4, by0 - 2, 9, 3, 'P', 6.4, hgt=0.7)                        # a sheet sticking up
    lay.rect(bx0 + 5, by0 - 1, 7, 1, 'C', 2.6)
    for xx in range(bx0, bx1 + 1, 3):                                          # mesh verticals
        lay.vline(xx, by0, by1 - by0, 'S', 3.6, hgt=0.8)
    for yy in range(by0, by1, 3):
        lay.hline(bx0, yy, bx1 - bx0 + 1, 'S', 3.0, hgt=0.8)
    lay.rect(bx0 - 1, by0, bx1 - bx0 + 3, 1, 'S', 4.6, hgt=0.85)
    # paper label clipped to the wire: 'KABINE 1 2 3'
    lay.rect(bx0 + 2, by1 - 6, 12, 5, 'P', 6.6, hgt=0.9)
    lay.text('123', bx0 + 3, by1 - 6, 'I', 1.0)
    return p


def protocol_table():
    x0, x1 = L.TABLE
    T = 30
    p = Prop('protocol_table', x0, 294, x1 - x0, T + 32, 'the big table of the Protokollbuero (protocol_table)')
    lay = p.lay
    w = x1 - x0
    # baize top seen slightly from above + walnut frame and turned legs
    lay.rect(2, T - 3, w - 4, 3, 'G', 4.4, hgt=0.6)
    lay.rect(2, T - 3, w - 4, 1, 'G', 3.4, hgt=0.55)
    top = np.ones((3, w - 4), bool)
    lay.paint_normal(top, 2, T - 3, (0.0, 0.9, 0.44))
    lay.rect(0, T, w, 4, 'D', 4.2, hgt=0.7)
    lay.rect(0, T, w, 1, 'D', 5.8, hgt=0.75)
    lay.rect(0, T + 3, w, 1, 'D', 2.0, hgt=0.5)
    lay.rect(2, T + 4, w - 4, 5, 'D', 2.6, hgt=0.5)
    for lx in (3, w // 2 - 2, w - 7):
        lay.rect(lx, T + 9, 4, 22, 'D', 3.2, hgt=0.6)
        lay.rect(lx, T + 9, 1, 22, 'D', 4.6, hgt=0.65)
        for k in (T + 14, T + 22):
            lay.rect(lx - 1, k, 6, 2, 'D', 3.8, hgt=0.65)
        lay.rect(lx - 1, T + 30, 6, 2, 'B', 3.0, hgt=0.6)
    lay.rect(6, T + 26, w - 12, 2, 'D', 2.2, hgt=0.4)                        # stretcher
    # papers: protocol folders, loose sheets, a blotter, inkstand, rubber stamps
    lay.rect(10, T - 4, 22, 2, 'P', 6.0, hgt=0.7)
    lay.rect(12, T - 5, 18, 1, 'P', 6.6, hgt=0.72)
    lay.rect(36, T - 4, 16, 2, 'C', 2.4, hgt=0.7)                            # slate folder
    lay.rect(37, T - 5, 14, 1, 'P', 5.4, hgt=0.72)
    lay.rect(58, T - 4, 26, 2, 'P', 5.2, hgt=0.7)                            # blotter
    lay.rect(58, T - 4, 26, 1, 'G', 3.0)
    lay.rect(88, T - 6, 6, 3, 'B', 3.4, hgt=0.8)                             # inkstand
    lay.rect(89, T - 8, 1, 2, 'I', 1.4)
    lay.rect(92, T - 9, 1, 3, 'P', 6.0)                                       # pen
    for k in range(3):                                                        # stamps
        lay.rect(98 + k * 3, T - 7, 2, 4, 'D', 4.4, hgt=0.8)
        lay.rect(98 + k * 3, T - 3, 2, 1, 'I', 1.4)
    # brass desk lamp with a green glass shade (warm focal of the office)
    lx = w - 16
    lay.rect(lx - 4, T - 5, 10, 2, 'B', 3.0, hgt=0.8)
    lay.rect(lx - 4, T - 5, 10, 1, 'B', 4.6, hgt=0.85)
    lay.rect(lx, T - 14, 2, 9, 'B', 3.4, hgt=0.85)
    sy = T - 20
    lay.poly([(lx - 9, sy + 5), (lx + 10, sy + 5), (lx + 8, sy), (lx - 7, sy)], 'G', 3.4, hgt=0.85)
    lay.rect(lx - 7, sy, 16, 1, 'G', 6.0, hgt=0.9, emis=True)
    lay.rect(lx - 8, sy + 2, 18, 1, 'G', 5.0, hgt=0.88, emis=True)
    lay.rect(lx - 9, sy + 5, 20, 1, 'A', 4.6, emis=True)
    lay.rect(lx - 6, sy + 6, 14, 1, 'A', 5.0, emis=True)
    p.lights.append({'name': 'table_lamp', 'pos': (x0 + lx + 1, p.y + sy + 7), 'kind': 'warm', 'energy': 1.5,
                     'radius': 128, 'height': 8, 'wrap_add': 0.05, 'pool': True})
    # two chairs pulled up at the near side (backs toward us)
    for cxx in (24, 70):
        lay.rect(cxx, T + 2, 14, 10, 'D', 3.0, hgt=0.75)
        lay.rect(cxx, T + 2, 14, 1, 'D', 4.8, hgt=0.8)
        lay.rect(cxx + 2, T + 4, 10, 6, 'R', 1.8, hgt=0.7)                   # leather back
        lay.rect(cxx + 1, T + 12, 2, 19, 'D', 2.4, hgt=0.6)
        lay.rect(cxx + 11, T + 12, 2, 19, 'D', 2.4, hgt=0.6)
    return p


def mimeograph():
    x0, x1 = L.MIMEO
    w, h = x1 - x0, 50
    p = Prop('mimeograph', x0, 293, w, h, 'stencil duplicator (mimeograph) on its stand, fresh copies')
    lay = p.lay
    T = 24
    # iron stand
    for lx in (3, w - 6):
        lay.rect(lx, T + 4, 3, h - T - 4, 'I', 1.8, hgt=0.6)
        lay.rect(lx, T + 4, 1, h - T - 4, 'S', 2.6, hgt=0.65)
    lay.rect(2, h - 12, w - 4, 2, 'I', 1.8, hgt=0.5)
    lay.rect(4, h - 10, w - 8, 3, 'P', 5.4, hgt=0.6)                          # ream on the shelf
    lay.rect(1, T, w - 2, 5, 'I', 2.0, hgt=0.7)
    lay.rect(1, T, w - 2, 1, 'S', 3.6, hgt=0.75)
    # the machine: drum housing, crank, feed tray, output tray with copies, ink tube
    lay.rect(6, T - 14, w - 12, 14, 'S', 2.2, hgt=0.8)
    lay.rect(6, T - 14, w - 12, 1, 'S', 4.0, hgt=0.85)
    lay.ellipse(w / 2, T - 8, 8.0, 5.5, 'I', 1.8, hgt=0.9, flat=False)         # drum end
    lay.ellipse(w / 2 - 1, T - 9, 5.0, 3.5, 'S', 3.0, hgt=0.95, flat=False)
    lay.px(int(w / 2), T - 8, 'B', 4.0)
    lay.line(w / 2, T - 8, w / 2 + 9, T - 16, 'S', 4.4)                        # crank
    lay.rect(int(w / 2) + 8, T - 18, 3, 3, 'D', 3.4, hgt=0.9)
    lay.poly([(0, T - 4), (8, T - 7), (8, T - 5), (0, T - 2)], 'P', 6.0, hgt=0.8)  # feed tray
    lay.rect(w - 9, T - 3, 9, 3, 'P', 5.4, hgt=0.8)                            # output copies
    lay.rect(w - 8, T - 4, 8, 1, 'P', 6.4, hgt=0.82)
    lay.hline(w - 7, T - 2, 5, 'C', 2.6)
    lay.rect(9, T - 18, 3, 4, 'R', 2.4, hgt=0.85)                              # ink tube (red)
    return p


def build_all():
    out = flags()
    out += [cloak_counter(), palm('palm_vest', 394, seed=3), buffet(), easel(), saal_rope(), typist_desk(),
            basket_cabinet(), protocol_table(), mimeograph(), palm('palm_corridor', 1488, seed=5, h=64)]
    return out


def bake_prop(p: Prop, lights, shaft_air=None):
    F = kit.light_fields(p.lay, lights, origin=(p.x, p.y))
    if shaft_air is not None:
        sub = kit.sub_fields({'cold': shaft_air}, p.x, p.y, p.w, p.h)['cold']
        F['cold'] += (sub ** 0.85) * 0.55
    p.lay.resolve(F)
    if p.hist_lay is not None:
        p.hist_lay.resolve(F)
    return p
