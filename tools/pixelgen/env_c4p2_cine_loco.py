"""env_c4p2_cine_loco -- steam locomotives of the Chapter-4-part-2 films, painted as pixel art (owner: cine stream).

One painter for the engines of LS_C4P2_Steam (the Karsk special at the coal stage, the Berlin express under the
glass roof), LS_C4P2_Book b4 (the polished show engine) and LS_C4P2_Depot p2 (the engine in the roundhouse, from
the front).  Everything is drawn with flat tones from short ramps (env_c4p2_cine_flat.Flat): the boiler, smokebox
and domes are cylinders in stepped bands (a lit crown, a highlight line, the body, the shadowed belly), riveted
seams, boiler bands, handrails on stanchions, pipes, the air pump, sand domes, pop valves and the whistle, the
cylinders with their covers, crosshead and slide bars, Walschaerts valve gear, coupling and connecting rods, spoked
wheels with balance weights and tyres, brake gear, the cab with its lit windows and the fire's glow, the tender
with its riveted tank, coal heap, bogies, springs and ladder; snow lies on every upper edge.  Dimensions are in
metres (u from the front buffer face back along the engine, v up from the rail top) scaled by `m` px per metre,
so a figure of the game's rig (44 px ~ 1.7 m) stands at the right size beside it (m ~ 26).  Deterministic.
"""
from __future__ import annotations

import math

import numpy as np

import env_c4p2_cine_flat as FL
import env_c4p2_cine_kit as K

# ------------------------------------------------------------------------------------------------- ramps (0 dark .. 5)
BLACK = ['#07080a', '#101215', '#1a1d22', '#262a31', '#383d46', '#565c66']
BLACK_LIT = ['#2a2018', '#5a4026', '#9a7044', '#d0a868']      # sodium on black steel: sheen, edge, hot edge
RED = ['#24070a', '#420c0c', '#661410', '#8e1e16', '#b42e20', '#d64a30']
GREEN = ['#06100a', '#0c1c12', '#14301c', '#1e4428', '#2c5c36', '#467a4c']
BRASS = ['#3a2408', '#6a4612', '#9a6e22', '#c8983a', '#e8c46a', '#fff0b8']
STEEL = ['#14181c', '#262c32', '#3c444c', '#5a646e', '#848e98', '#b8c2ca']
COPPER = ['#2a0e06', '#5a2410', '#8a4020', '#b86434', '#e09058', '#ffc890']
SNOW = ['#8a96a8', '#b4bfcc', '#dfe6ee', '#f6f8fa']


def _band(F, m, cy, r, ramp, lit=None, belly=True, seam=True, xform=None):
    """A horizontal cylinder in stepped bands: rows by v = (y - cy) / r."""
    v = (F.yy - cy) / max(r, 1e-3)
    chk = ((F.xx.astype(np.int32) + F.yy.astype(np.int32)) & 1) == 0
    j = 0.06 if seam else 0.0
    vv = v + np.where(chk, j, -j)
    idx = np.full(v.shape, 3, np.int32)
    idx = np.where(vv < 0.38, 3, idx)
    idx = np.where(vv >= 0.38, 2, idx)
    idx = np.where(vv >= 0.74, 1, idx)
    idx = np.where(vv < -0.12, 4, idx)
    idx = np.where(vv < -0.56, 5, idx)
    idx = np.where(vv < -0.84, 3, idx)
    if not belly:
        idx = np.maximum(idx, 2)
    cols = np.stack([FL.hx(c) for c in ramp])
    col = cols[np.clip(idx, 0, 5)]
    F.rgb[m] = col[m]
    F.a |= m
    if lit is not None:
        hl = m & (vv < -0.56) & (vv >= -0.84)
        F.rgb[hl] = F.rgb[hl] * 0.4 + FL.hx(lit) * 0.6
    return m


def _vband(F, m, cx, r, ramp, side=1):
    """A vertical cylinder (domes, chimney, pump) in stepped columns; side = +1 lit from the right."""
    u = (F.xx - cx) / max(r, 1e-3) * side
    chk = ((F.xx.astype(np.int32) + F.yy.astype(np.int32)) & 1) == 0
    uu = u + np.where(chk, 0.06, -0.06)
    idx = np.full(u.shape, 3, np.int32)
    idx = np.where(uu > 0.25, 4, idx)
    idx = np.where(uu > 0.6, 5, idx)
    idx = np.where(uu > 0.86, 3, idx)
    idx = np.where(uu < -0.3, 2, idx)
    idx = np.where(uu < -0.72, 1, idx)
    cols = np.stack([FL.hx(c) for c in ramp])
    col = cols[idx]
    F.rgb[m] = col[m]
    F.a |= m
    return m


def _rivets(F, pts, col_hi, col_lo):
    for (x, y) in pts:
        F.fill(F.box(x, y, x + 1, y + 1), col_hi)
        F.fill(F.box(x + 1, y + 1, x + 2, y + 2), col_lo)


def wheel(F, cx, cy, r, ramp=RED, tyre=STEEL, spokes=12, ang=0.0, weight=True, lit=1, snow=False):
    """A spoked driving wheel: steel tyre with its flange, a red centre with spokes, the balance weight, the hub,
    the crank pin; one lit arc on the tyre."""
    disc = F.ell(cx, cy, r, r)
    F.fill(disc, tyre[1])
    top = disc & (F.yy < cy - r * 0.55)
    F.fill(top, tyre[2])
    arc = disc & ~F.ell(cx, cy, r - 1, r - 1) & (F.yy < cy) & ((F.xx - cx) * lit > -r * 0.2)
    F.fill(arc, tyre[4])
    ri = max(1.0, r - max(1.5, r * 0.16))
    inner = F.ell(cx, cy, ri, ri)
    F.fill(inner, '#0a0a0c')
    rim = inner & ~F.ell(cx, cy, ri - max(1.0, r * 0.08), ri - max(1.0, r * 0.08))
    F.fill(rim, ramp[3])
    F.fill(rim & (F.yy < cy), ramp[4])
    sp = np.zeros_like(disc)
    for k in range(spokes):
        a = ang + 2 * math.pi * k / spokes
        sp |= F.line([(cx + math.cos(a) * r * 0.22, cy + math.sin(a) * r * 0.22),
                      (cx + math.cos(a) * (ri - 1), cy + math.sin(a) * (ri - 1))], max(0.5, r * 0.055))
    F.fill(sp & inner, ramp[3])
    F.fill(sp & inner & ((F.xx - cx > 0) == (lit > 0)), ramp[2])
    if weight:
        wa = ang + math.pi
        wx, wy = cx + math.cos(wa) * r * 0.5, cy + math.sin(wa) * r * 0.5
        wm = F.ell(wx, wy, r * 0.42, r * 0.42) & inner & ~F.ell(cx, cy, r * 0.28, r * 0.28)
        F.fill(wm, ramp[3])
        F.fill(wm & FL.edge(wm, 't'), ramp[5])
    hub = F.ell(cx, cy, max(1.5, r * 0.24), max(1.5, r * 0.24))
    F.fill(hub, ramp[3])
    F.fill(hub & (F.yy < cy), ramp[4])
    F.fill(F.ell(cx, cy, max(1.0, r * 0.1), max(1.0, r * 0.1)), STEEL[3])
    px, py = cx + math.cos(ang) * r * 0.5, cy + math.sin(ang) * r * 0.5
    F.fill(F.ell(px, py, max(1.0, r * 0.12), max(1.0, r * 0.12)), STEEL[4])
    F.outline(disc, col='#050506')
    if snow:
        F.fill(disc & FL.edge(disc, 't') & (F.yy < cy - r * 0.8), SNOW[2])
    return (px, py)


class SideLoco:
    """A side-view steam engine.  kind: 'soviet' (2-10-0 freight, a feed-water heater drum), 'show' (the same
    engine polished green with red wheels, brass bands, red ribbons and a fir garland), 'german' (4-6-2 express,
    big drivers, smoke deflectors, green tender stripe).  facing -1: the smokebox at the left (runs left)."""

    def __init__(self, F, x0, rail_y, m=26.0, facing=-1, kind='soviet', number='Л-2238', crank=0.0, snow=True,
                 lit=1, cab_glow=True):
        self.F, self.x0, self.ry, self.m, self.f = F, float(x0), float(rail_y), float(m), facing
        self.kind, self.number, self.crank, self.snow, self.lit, self.cab_glow = kind, number, crank, snow, lit, \
            cab_glow
        self.body = GREEN if kind == 'show' else BLACK
        self.wheel_ramp = RED
        self.band = BRASS if kind in ('show', 'german') else BLACK
        self.anchors = {}
        self.snowm = np.zeros((F.h, F.w), bool)

    # -------------------------------------------------------------- coordinates
    def X(self, u):
        return self.x0 - self.f * u * self.m if self.f < 0 else self.x0 + u * self.m * 0 + self.f * u * self.m

    def x(self, u):
        return self.x0 + (u * self.m if self.f < 0 else -u * self.m)

    def y(self, v):
        return self.ry - v * self.m

    def box(self, u0, u1, v0, v1):
        a, b = sorted((self.x(u0), self.x(u1)))
        return self.F.box(a, self.y(v1), b, self.y(v0))

    def poly(self, pts):
        return self.F.poly([(self.x(u), self.y(v)) for (u, v) in pts])

    def ell(self, u, v, ru, rv):
        return self.F.ell(self.x(u), self.y(v), ru * self.m, rv * self.m)

    def line(self, pts, r=0.5):
        return self.F.line([(self.x(u), self.y(v)) for (u, v) in pts], r)

    def cap(self, m, k=1):
        """Snow on the upper edge of mask m (k rows)."""
        if self.snow:
            e = FL.edge(m, 't', k)
            self.snowm |= e

    # -------------------------------------------------------------- the engine
    def paint(self):
        F = self.F
        big = self.kind == 'german'
        B = self.body
        R_ = self.wheel_ramp
        Lb = 10.8 if not big else 12.6                        # cab back
        bc = 3.05 if not big else 3.15                        # boiler centre height
        br = 0.86 if not big else 0.92
        # frames between the wheels (dark), brake hangers
        F.fill(self.box(0.3, Lb - 0.1, 0.5, 1.3), B[0])
        # running board and its valance
        rb = self.box(0.2, Lb, 1.25, 1.36)
        F.fill(rb, B[3])
        F.fill(self.box(0.2, Lb, 1.05, 1.25), B[1])
        F.fill(rb & FL.edge(rb, 't'), B[5])
        self.cap(rb, 1)
        # buffer beam, buffers, coupling hook
        F.fill(self.box(0.0, 0.28, 0.72, 1.3), R_[3])
        F.fill(self.box(0.0, 0.28, 1.2, 1.3), R_[5])
        for v in (0.95,):
            F.fill(self.box(-0.42, 0.0, v - 0.08, v + 0.08), STEEL[2])
            bh = self.box(-0.5, -0.36, v - 0.2, v + 0.2)
            F.fill(bh, STEEL[3])
            F.fill(bh & FL.edge(bh, 'l' if self.f < 0 else 'r'), STEEL[5])
            F.outline(bh, col='#050506')
        F.fill(self.box(-0.3, 0.0, 0.66, 0.74), STEEL[1])
        # cylinder block, valve chest, slide bars, crosshead
        cyl = self.box(0.55, 2.05, 0.78, 1.95)
        _band(F, cyl, self.y(1.36), 0.6 * self.m, B, lit=BLACK_LIT[2] if self.kind != 'show' else None)
        for u in (0.62, 1.95):
            F.fill(self.box(u, u + 0.1, 0.76, 1.97), self.band[4] if self.kind != 'soviet' else B[4])
        vc = self.box(0.7, 1.95, 1.95, 2.45)
        _band(F, vc, self.y(2.2), 0.26 * self.m, B)
        F.outline(cyl | vc, col='#050506')
        F.fill(self.box(2.05, 3.6, 1.18, 1.24) | self.box(2.05, 3.6, 0.98, 1.04), STEEL[4])
        xh = 2.4 + 0.5 * (1 + math.cos(self.crank)) * 0.55
        ch = self.box(xh, xh + 0.34, 0.94, 1.28)
        F.fill(ch, STEEL[3])
        F.outline(ch, col='#050506')
        # boiler, smokebox, chimney, domes, valves, whistle
        sm = self.box(0.38, 1.95, bc - br - 0.08, bc + br + 0.08)
        _band(F, sm, self.y(bc), (br + 0.08) * self.m, B, lit=BLACK_LIT[3] if self.kind != 'show' else None)
        F.fill(self.box(0.36, 0.44, bc - br - 0.02, bc + br + 0.02), B[1])
        bo = self.box(1.95, Lb - 2.6, bc - br, bc + br)
        _band(F, bo, self.y(bc), br * self.m, B, lit=BLACK_LIT[3] if self.kind != 'show' else '#8ac08a')
        fb = self.box(Lb - 2.6, Lb - 2.35, bc - br - 0.25, bc + br)
        F.fill(fb, B[2])
        for u in np.arange(2.9, Lb - 2.7, 1.45):
            bnd = self.box(u, u + 0.09, bc - br, bc + br)
            _band(F, bnd, self.y(bc), br * self.m, self.band if self.kind != 'soviet' else B[1:] + [B[5]])
        rivy = [self.y(bc + br * 0.92)]
        _rivets(F, [(self.x(u), self.y(bc + 0.18)) for u in np.arange(0.5, 1.9, 0.18)], B[5], B[0])
        self.cap(sm | bo, 2)
        # chimney (stovepipe with a lip) and the headlamp
        cu = 1.05
        chm = self.box(cu - 0.22, cu + 0.22, bc + br, bc + br + 0.62)
        _vband(F, chm, self.x(cu), 0.22 * self.m, B, side=self.lit * -self.f)
        lip = self.box(cu - 0.3, cu + 0.3, bc + br + 0.56, bc + br + 0.72)
        F.fill(lip, B[2])
        F.fill(lip & FL.edge(lip, 't'), B[5])
        F.outline(chm | lip, col='#050506')
        self.cap(lip, 2)
        self.anchors['chimney'] = (self.x(cu), self.y(bc + br + 0.72))
        hl = self.box(0.18, 0.5, bc + br - 0.05, bc + br + 0.3)
        F.fill(hl, B[3])
        F.fill(self.box(0.12, 0.2, bc + br + 0.02, bc + br + 0.24), '#fff2c0')
        F.outline(hl, col='#050506')
        self.anchors['headlamp'] = (self.x(0.12), self.y(bc + br + 0.13))
        for (du, w, h) in ((4.2 if not big else 4.8, 0.52, 0.42), (2.8 if not big else 3.2, 0.36, 0.3)):
            dm = self.ell(du, bc + br, w, h) & (F.yy <= self.y(bc + br) + 1)
            _vband(F, dm, self.x(du), w * self.m, B if self.kind != 'show' else GREEN, side=self.lit * -self.f)
            F.fill(dm & FL.edge(dm, 't'), B[5])
            F.outline(dm, col='#050506', sides='lr')
            self.cap(dm, 2)
        vu = Lb - 3.25
        for k in range(2):
            vm = self.box(vu + k * 0.28 - 0.08, vu + k * 0.28 + 0.08, bc + br - 0.02, bc + br + 0.3)
            F.fill(vm, BRASS[3])
            F.fill(vm & FL.edge(vm, 'l' if self.lit < 0 else 'r'), BRASS[5])
            F.fill(self.box(vu + k * 0.28 - 0.12, vu + k * 0.28 + 0.12, bc + br + 0.26, bc + br + 0.34), BRASS[4])
            F.outline(vm, col='#1a1004')
        self.anchors['valve'] = (self.x(vu + 0.14), self.y(bc + br + 0.34))
        wu = Lb - 2.75
        wm_ = self.box(wu - 0.04, wu + 0.04, bc + br, bc + br + 0.5)
        F.fill(wm_, BRASS[3])
        bell = self.box(wu - 0.09, wu + 0.09, bc + br + 0.32, bc + br + 0.58)
        F.fill(bell, BRASS[4])
        F.outline(bell, col='#1a1004')
        self.anchors['whistle'] = (self.x(wu), self.y(bc + br + 0.6))
        # feed-water heater drum across the smokebox top (soviet), smoke deflectors (german)
        if self.kind in ('soviet', 'show'):
            fw = self.box(1.2, 2.6, bc + br - 0.05, bc + br + 0.28)
            _band(F, fw, self.y(bc + br + 0.12), 0.18 * self.m, B)
            F.outline(fw, col='#050506')
            self.cap(fw, 1)
        if big:
            dfl = self.poly([(0.6, 1.4), (2.1, 1.4), (2.1, bc + br + 0.1), (0.9, bc + br + 0.1), (0.6, bc + 0.5)])
            F.fill(dfl, B[2])
            F.fill(dfl & FL.edge(dfl, 't'), B[5])
            F.outline(dfl, col='#050506')
            for u in (0.9, 1.4, 1.9):
                F.fill(self.box(u, u + 0.06, 1.7, bc + 0.6), B[1])
            self.cap(dfl, 1)
        # handrail, pipes, sand pipes, air pump
        hr = self.line([(0.6, bc + 0.36), (Lb - 2.7, bc + 0.36)], 0.5)
        F.fill(hr, STEEL[4])
        for u in np.arange(0.8, Lb - 2.8, 1.1):
            F.fill(self.line([(u, bc + 0.36), (u, bc + 0.2)], 0.5), STEEL[2])
        pp = self.line([(Lb - 2.65, bc - br * 0.55), (2.1, bc - br * 0.55), (1.7, bc - br * 0.2)], 0.6)
        F.fill(pp, COPPER[2] if self.kind == 'soviet' else COPPER[3])
        F.fill(pp & FL.edge(pp, 't'), COPPER[4])
        lp = self.line([(Lb - 2.65, 1.62), (3.3, 1.62), (2.9, 1.95)], 0.5)
        F.fill(lp, B[4])
        if not big:
            pm = self.box(2.5, 2.85, 1.6, 2.6)
            _vband(F, pm, self.x(2.675), 0.175 * self.m, B, side=self.lit * -self.f)
            F.fill(self.box(2.45, 2.9, 2.0, 2.06) | self.box(2.45, 2.9, 2.3, 2.36), STEEL[3])
            F.outline(pm, col='#050506')
        for u in ((2.4, 3.8, 5.2, 6.6) if not big else (3.0, 5.1)):
            F.fill(self.line([(u - 0.5, 1.3), (u - 0.62, 0.55)], 0.5), STEEL[1])
        # cab: sides, roof overhang, windows lit by the fire, the number plate, the door opening
        cab = self.box(Lb - 2.4, Lb, 1.25, 4.15 if not big else 4.25)
        F.fill(cab, B[3])
        F.fill(cab & FL.edge(cab, 'l' if self.f > 0 else 'r', 2), B[4])
        roof = self.box(Lb - 2.55, Lb + 0.25, 4.1 if not big else 4.2, 4.32 if not big else 4.42)
        F.fill(roof, B[2])
        F.fill(roof & FL.edge(roof, 't'), B[5])
        self.cap(roof, 2)
        for k, (w0, w1) in enumerate(((Lb - 2.2, Lb - 1.5), (Lb - 1.3, Lb - 0.6))):
            wn = self.box(w0, w1, 2.9, 3.7)
            F.fill(wn, '#0c0806')
            if self.cab_glow:
                F.fill(wn & self.box(w0, w1, 2.9, 3.25), '#c86424' if k == 0 else '#a04c1c')
                F.fill(wn & self.box(w0, w1, 2.9, 3.02), '#f0a050')
            F.outline(wn, col=B[5], sides='b')
            F.outline(wn, col=B[0], sides='t')
        door = self.box(Lb - 0.42, Lb - 0.08, 1.4, 3.3)
        F.fill(door, '#0c0806')
        if self.cab_glow:
            F.fill(door & self.box(Lb - 0.42, Lb - 0.08, 1.4, 2.1), '#7a3412')
        np_ = self.box(Lb - 2.15, Lb - 0.65, 2.1, 2.5)
        F.fill(np_, BRASS[3] if self.kind != 'soviet' else '#c8b070')
        tw = K.VK.vtext(self.number, 's').shape[1]
        cx_ = (self.x(Lb - 2.15) + self.x(Lb - 0.65)) / 2
        F.fill(F.text(self.number, int(cx_ - tw / 2), int(self.y(2.45)), 's') & np_, '#1a1008')
        F.outline(np_, col='#1a1008')
        F.outline(cab | roof, col='#050506')
        self.anchors['cab_door'] = (self.x(Lb - 0.25), self.y(1.3))
        self.anchors['cab_win'] = (self.x(Lb - 1.85), self.y(3.3))
        # wheels: pony / bogie and drivers, coupling rod, connecting rod, valve gear
        if big:
            drivers = [(4.0 + 2.05 * k, 1.0) for k in range(3)]
            small = [(0.9, 0.45), (2.2, 0.45), (Lb - 0.8, 0.55)]
        else:
            drivers = [(2.45 + 1.4 * k, 0.66) for k in range(5)]
            small = [(1.0, 0.42)]
        for (u, r) in small:
            wheel(F, self.x(u), self.y(r), r * self.m, R_, spokes=8, ang=self.crank, weight=False,
                  lit=self.lit * -self.f)
        pins = []
        for i, (u, r) in enumerate(drivers):
            pins.append(wheel(F, self.x(u), self.y(r), r * self.m, R_, spokes=14 if big else 12,
                              ang=self.crank + (0.0 if True else 0), lit=self.lit * -self.f))
        rod = F.line(pins, max(1.0, 0.07 * self.m))
        F.fill(rod, STEEL[4])
        F.fill(rod & FL.edge(rod, 't'), STEEL[5])
        F.outline(rod, col='#050506', sides='b')
        main = pins[2 if not big else 1]
        crx, cry = self.x(xh + 0.17), self.y(1.11)
        cr = F.line([(crx, cry), main], max(1.0, 0.09 * self.m))
        F.fill(cr, STEEL[4])
        F.fill(cr & FL.edge(cr, 't'), STEEL[5])
        F.outline(cr, col='#050506', sides='b')
        ex = (main[0] + (6 if self.f < 0 else -6) * self.m / 26.0, main[1] - 4)
        link = (self.x(3.9 if not big else 4.6), self.y(1.75))
        F.fill(F.line([ex, link], 0.6) | F.line([link, (self.x(2.2), self.y(2.0))], 0.6), STEEL[3])
        F.fill(F.line([(crx, cry), (self.x(xh + 0.17), self.y(1.9))], 0.5), STEEL[3])
        self.anchors['drivers'] = [(self.x(u), self.y(r), r * self.m) for (u, r) in drivers]
        self.Lb = Lb
        return self

    def tender(self, coal=True, number=None, lamp=True):
        F = self.F
        big = self.kind == 'german'
        B = self.body
        u0 = self.Lb + 0.3
        u1 = u0 + (7.6 if not big else 8.8)
        top = 3.35 if not big else 3.6
        tk = self.box(u0, u1, 1.15, top)
        F.fill(tk, B[3])
        F.fill(tk & self.box(u0, u1, 1.15, 1.5), B[2])
        F.fill(tk & FL.edge(tk, 't', 2), B[5])
        for u in np.arange(u0 + 1.2, u1 - 0.4, 1.25):
            F.fill(self.box(u, u + 0.05, 1.5, top - 0.1), B[1])
            F.fill(self.box(u + 0.05, u + 0.09, 1.5, top - 0.1), B[4])
        _rivets(F, [(self.x(u), self.y(top - 0.22)) for u in np.arange(u0 + 0.2, u1 - 0.1, 0.22)], B[5], B[0])
        _rivets(F, [(self.x(u), self.y(1.62)) for u in np.arange(u0 + 0.2, u1 - 0.1, 0.22)], B[5], B[0])
        if self.kind == 'german':
            F.fill(self.box(u0 + 0.2, u1 - 0.2, 2.3, 2.38), BRASS[3])
        if number:
            tw = K.VK.vtext(number, 's').shape[1]
            cx_ = (self.x(u0) + self.x(u1)) / 2
            F.fill(F.text(number, int(cx_ - tw / 2), int(self.y(2.75)), 's') & tk, '#c8b070')
        F.outline(tk, col='#050506')
        self.cap(tk, 1)
        if coal:
            pts = [(u0 + 0.2, top)]
            n = 18
            for k in range(n + 1):
                u = u0 + 0.2 + (u1 - u0 - 0.4) * k / n
                h = 0.25 + 0.45 * math.sin(math.pi * k / n) + 0.12 * K.hash2(k, 3, 7)
                pts.append((u, top + h))
            pts.append((u1 - 0.2, top))
            cm = self.poly(pts)
            F.fill(cm, '#0c0c0e')
            xx, yy = F.xx.astype(np.int64), F.yy.astype(np.int64)
            lump = cm & (K.hash2(np.floor_divide(xx, 3), np.floor_divide(yy, 2), 51) > 0.55)
            F.fill(lump, '#1c1c22')
            F.fill(lump & (K.hash2(xx, yy, 52) > 0.7), '#3a3a46')
            F.fill(cm & (K.hash2(xx, yy, 53) > 0.985), BLACK_LIT[3])
            F.outline(cm, col='#050506', sides='t')
            self.cap(cm, 1)
            self.anchors['coal_top'] = (self.x((u0 + u1) / 2), self.y(top + 0.7))
        # frames, bogies, springs, axle boxes
        F.fill(self.box(u0, u1, 0.75, 1.15), B[1])
        for bu in ((u0 + 1.6, u0 + 3.0), (u1 - 3.0, u1 - 1.6)):
            for u in bu:
                wheel(F, self.x(u), self.y(0.46), 0.46 * self.m, BLACK if self.kind != 'show' else RED, spokes=10,
                      ang=self.crank * 1.4, weight=False, lit=self.lit * -self.f)
                ab = self.box(u - 0.18, u + 0.18, 0.5, 0.85)
                F.fill(ab, B[2])
                F.outline(ab, col='#050506')
            sp = self.box(bu[0] - 0.1, bu[1] + 0.1, 0.86, 0.98)
            F.fill(sp, STEEL[2])
            for k in range(3):
                F.fill(self.box(bu[0] + 0.1, bu[1] - 0.1, 0.98 + k * 0.05, 1.01 + k * 0.05), STEEL[3 - k % 2])
        lad = self.box(u1 - 0.35, u1 - 0.25, 0.9, top)
        F.fill(lad, STEEL[2])
        for v in np.arange(1.0, top, 0.32):
            F.fill(self.box(u1 - 0.45, u1 - 0.15, v, v + 0.05), STEEL[3])
        if lamp:
            lm = self.box(u1 - 0.1, u1 + 0.12, top - 0.6, top - 0.25)
            F.fill(lm, B[2])
            F.fill(self.box(u1 + 0.06, u1 + 0.14, top - 0.55, top - 0.3), '#e83a2a')
            self.anchors['tail_lamp'] = (self.x(u1 + 0.1), self.y(top - 0.42))
        self.anchors['tender'] = (min(self.x(u0), self.x(u1)), max(self.x(u0), self.x(u1)), self.y(top))
        self.u_end = u1
        return self

    def finish(self):
        """Lay the gathered snow edges (a bright row with a shadowed row under it)."""
        if self.snow:
            F = self.F
            F.fill(self.snowm, SNOW[2])
            under = FL.shift(self.snowm, 0, 1) & ~self.snowm & F.a
            F.rgb[under] = F.rgb[under] * 0.6 + FL.hx(SNOW[0]) * 0.4
            spark = self.snowm & (K.hash2(F.xx.astype(np.int64), F.yy.astype(np.int64), 61) > 0.85)
            F.fill(spark, SNOW[3])
        return self


def ribbons(F, loco: SideLoco, us=(0.3, 3.0, 6.0)):
    """The show engine's red ribbons (bows on the buffer beam, the smokebox and the cab) and a fir garland along
    the running board."""
    for k, u in enumerate(us):
        v = 1.0 if k == 0 else (3.2 if k == 1 else 1.6)
        x, y = loco.x(u), loco.y(v)
        bow = F.poly([(x - 6, y - 4), (x, y), (x - 6, y + 4)]) | F.poly([(x + 6, y - 4), (x, y), (x + 6, y + 4)])
        F.fill(bow, RED[4])
        F.fill(bow & FL.edge(bow, 't'), RED[5])
        F.fill(F.line([(x, y), (x - 3, y + 12)], 0.8) | F.line([(x, y), (x + 4, y + 11)], 0.8), RED[3])
        F.outline(bow, col=RED[0])
    for k in range(0, int((loco.Lb - 0.6) * 5)):
        u = 0.5 + k * 0.2
        x, y = loco.x(u), loco.y(1.18) + 2.5 * math.sin(u * 2.1) + 2
        g = F.ell(x, y, 3.2, 2.4)
        F.fill(g, '#14301a' if k % 2 else '#1e4426')
        F.fill(g & FL.edge(g, 't'), '#3a6a3a')
        if k % 5 == 2:
            F.fill(F.box(x, y - 1, x + 2, y + 1), RED[5])


class FrontLoco:
    """The engine head-on (Depot p2, under the roundhouse arch): the smokebox door with its dart and hinge
    straps, the number plate and the star, the chimney, the headlamps, the buffer beam with buffers and the
    coupling, the cylinders at the sides, the running boards, the wheels' edges.  cx = centre line, base = rail
    top, m px per metre."""

    def __init__(self, F, cx, base, m=40.0, number='2238', star=True, lamps=True):
        self.F, self.cx, self.base, self.m, self.number, self.star, self.lamps = F, cx, base, m, number, star, lamps
        self.anchors = {}

    def X(self, s):
        return self.cx + s * self.m

    def Y(self, v):
        return self.base - v * self.m

    def paint(self):
        F = self.F
        m = self.m
        B = BLACK
        # frames and wheels' edges (seen front: narrow dark slabs), the pony truck
        for s in (-0.78, 0.78):
            wl = F.box(self.X(s - 0.07), self.Y(1.3), self.X(s + 0.07), self.Y(0.0))
            F.fill(wl, '#0a0a0c')
            F.fill(wl & FL.edge(wl, 'l' if s < 0 else 'r'), RED[3])
        F.fill(F.box(self.X(-0.6), self.Y(0.9), self.X(0.6), self.Y(0.1)), B[0])
        # running boards and cylinders at both sides
        for s in (-1, 1):
            cy_ = F.ell(self.X(s * 1.12), self.Y(1.4), 0.36 * m, 0.52 * m)
            _vband(F, cy_, self.X(s * 1.12), 0.36 * m, B, side=-s)
            F.outline(cy_, col='#050506')
            rbm = F.box(min(self.X(s * 0.55), self.X(s * 1.5)), self.Y(2.0), max(self.X(s * 0.55), self.X(s * 1.5)),
                        self.Y(1.9))
            F.fill(rbm, B[3])
            F.fill(rbm & FL.edge(rbm, 't'), B[5])
        # buffer beam with buffers and coupling hook
        bb = F.box(self.X(-1.45), self.Y(1.3), self.X(1.45), self.Y(0.72))
        F.fill(bb, RED[3])
        F.fill(bb & FL.edge(bb, 't', 2), RED[5])
        F.fill(bb & FL.edge(bb, 'b', 2), RED[1])
        F.outline(bb, col=RED[0])
        for s in (-0.88, 0.88):
            bh = F.ell(self.X(s), self.Y(1.0), 0.24 * m, 0.24 * m)
            F.fill(bh, STEEL[2])
            F.fill(bh & ~F.ell(self.X(s) + 1, self.Y(1.0) + 1, 0.24 * m, 0.24 * m), STEEL[4])
            F.fill(F.ell(self.X(s), self.Y(1.0), 0.08 * m, 0.08 * m), STEEL[1])
            F.outline(bh, col='#050506')
        hook = F.box(self.X(-0.08), self.Y(1.05), self.X(0.08), self.Y(0.62))
        F.fill(hook, STEEL[2])
        F.fill(F.ell(self.X(0), self.Y(0.62), 0.12 * m, 0.08 * m), STEEL[3])
        # the smokebox front: a ring, the door with its dart, hinge straps, the number plate and the star
        cy = 3.05
        ring = F.ell(self.X(0), self.Y(cy), 0.98 * m, 0.98 * m)
        F.fill(ring, B[2])
        F.fill(ring & ~F.ell(self.X(0) + 2, self.Y(cy) + 2, 0.98 * m, 0.98 * m), B[4])
        F.outline(ring, col='#050506')
        door = F.ell(self.X(0), self.Y(cy), 0.8 * m, 0.8 * m)
        F.fill(door, B[3])
        F.fill(door & ~F.ell(self.X(0) + 2, self.Y(cy) + 2, 0.8 * m, 0.8 * m), B[5])
        F.fill(door & ~F.ell(self.X(0) - 2, self.Y(cy) - 2, 0.8 * m, 0.8 * m), B[1])
        _rivets(F, [(self.X(0) + math.cos(a) * 0.9 * m, self.Y(cy) + math.sin(a) * 0.9 * m)
                    for a in np.linspace(0, 2 * math.pi, 28, endpoint=False)], B[5], B[0])
        for dy in (-0.45, 0.45):
            st = F.box(self.X(-0.1), self.Y(cy + dy) - 2, self.X(0.86), self.Y(cy + dy) + 2)
            F.fill(st & door, B[4])
            F.fill(F.ell(self.X(0.84), self.Y(cy + dy), 0.07 * m, 0.09 * m), B[5])
        dart = F.line([(self.X(-0.22), self.Y(cy - 0.2)), (self.X(0.22), self.Y(cy + 0.2))], 1.2)
        F.fill(F.ell(self.X(0), self.Y(cy), 0.1 * m, 0.1 * m), STEEL[3])
        F.fill(dart, STEEL[4])
        plate = F.box(self.X(-0.42), self.Y(cy - 0.42), self.X(0.42), self.Y(cy - 0.62))
        F.fill(plate, '#c8b070')
        tw = K.VK.vtext(self.number, 's').shape[1]
        F.fill(F.text(self.number, int(self.X(0) - tw / 2), int(self.Y(cy - 0.45)), 's') & plate, '#1a1008')
        F.outline(plate, col='#1a1008')
        if self.star:
            sx, sy, r = self.X(0), self.Y(cy + 0.48), 0.2 * m
            pts = []
            for k in range(10):
                a = -math.pi / 2 + k * math.pi / 5
                rr = r if k % 2 == 0 else r * 0.42
                pts.append((sx + math.cos(a) * rr, sy + math.sin(a) * rr))
            stm = F.poly(pts)
            F.fill(stm, RED[4])
            F.fill(stm & (F.xx < sx), RED[5])
            F.outline(stm, col=RED[0])
        # chimney, headlamps, handrails, steps
        ch = F.box(self.X(-0.24), self.Y(cy + 1.62), self.X(0.24), self.Y(cy + 0.9))
        _vband(F, ch, self.X(0), 0.24 * m, B, side=1)
        lip = F.box(self.X(-0.32), self.Y(cy + 1.7), self.X(0.32), self.Y(cy + 1.56))
        F.fill(lip, B[4])
        F.outline(ch | lip, col='#050506')
        self.anchors['chimney'] = (self.X(0), self.Y(cy + 1.7))
        if self.lamps:
            for (s, v) in ((-0.8, 1.6), (0.8, 1.6), (0.0, cy + 1.05)):
                lm = F.box(self.X(s - 0.16), self.Y(v + 0.32), self.X(s + 0.16), self.Y(v))
                F.fill(lm, B[2])
                F.fill(F.ell(self.X(s), self.Y(v + 0.16), 0.11 * m, 0.11 * m), '#fff2c0')
                F.outline(lm, col='#050506')
            self.anchors['lamps'] = [(self.X(s), self.Y(v + 0.16)) for (s, v) in ((-0.8, 1.6), (0.8, 1.6),
                                                                                    (0.0, cy + 1.05))]
        for s in (-1, 1):
            F.fill(F.line([(self.X(s * 0.98), self.Y(cy + 0.2)), (self.X(s * 0.98), self.Y(cy - 0.6))], 0.6), STEEL[4])
            F.fill(F.box(self.X(s * 1.25) - 4, self.Y(0.55), self.X(s * 1.25) + 4, self.Y(0.5)), STEEL[3])
        self.anchors['smokebox'] = (self.X(0), self.Y(cy), 0.98 * m)
        return self
