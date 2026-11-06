"""env_c4p2_berlin_station -- the layers of L_C4P2_BerlinA: Ostbahnhof, Korridorbahnsteig K, Monday 17.2.1964, 20.30.

Painted in tone space (env_c4p2_berlin_kit, world 'A' = palette ostbahnhof + proposed ramps): sodium lamps under a
glass vault turn stone and iron amber, the dining car glows warm, the open end of the hall lets in the blue night
and the snow.  Back to front:
    st_sky     night sky with the city's glow, seen through the open end of the hall        (parallax 0.05)
    st_city    the night city beyond the hall: blocks, lit windows, chimneys, a mast light   (parallax 0.15)
    st_hall    the shell: glass vault, iron ribs, the far brick wall with arched windows      (parallax 0.40)
    st_track2  the next track: the green windowless car with barred hatches, „Di – Kordon“    (parallax 0.92)
    station    the playfield 0..918: track K with the D 303 (locomotive, courier van, the uncoupled gap, dining car,
               sleeping car), platform K with the liaison booth at the barrier, the departure board, the baggage
               counter and its scale, the buffet, the kiosk, the porters' carts, lamps, the clock, the Corridor
               fence at the end                                                              (lit, normals, emission)
    fg_station the near platform edge and the near track bed in near-black                    (parallax 1.25)
Story / insignia states (cfg): 'hist' (historical insignia: the two plates of the liaison booth, the plate on the
locomotive's cab), 'roster' = '3' | '74' (Marta's duty roster on the counter, art gate choice c4d_choose).
"""
from __future__ import annotations

import math

import numpy as np

import env_c4p2_berlin_kit as K
import env_c4p2_berlin_layout as L
import pg

W = L.A_W
H = L.WORLD_H
FEET = L.FEET
PE = L.PLAT_EDGE_Y


# =========================================================================== painters shared by the layers
def wheel(lay, cx, cy, r, ramp_tire='S', ramp_centre='R', spokes=12, crank=None, ctone=2.2, hub=('S', 4.6)):
    """A spoked wheel seen from the side: steel tyre, painted centre with spokes, hub, an optional crank pin /
    counterweight (crank = angle in rad).  Pixels outside the platform's top edge only (the caller hides the rest)."""
    m = K.disc(2 * r + 1)
    x0, y0 = cx - r, cy - r
    inner = K.erode(m, 2)
    tyre = m & ~inner
    lay.put(tyre, x0, y0, ramp_tire, 4.2, hgt=0.6)
    hi = np.zeros_like(m)
    hi[:r, :r] = True
    lay.put(tyre & hi, x0, y0, ramp_tire, 5.4, hgt=0.7)
    lay.put(inner, x0, y0, ramp_centre, ctone, hgt=0.4)
    yy, xx = np.mgrid[0:2 * r + 1, 0:2 * r + 1]
    ang = np.arctan2(yy - r, xx - r)
    rad = np.hypot(yy - r, xx - r)
    sp = (np.abs(((ang * spokes / (2 * math.pi)) % 1.0) - 0.5) > 0.36) & (rad < r - 2) & (rad > 2)
    lay.put(inner & ~sp, x0, y0, 'I', 0.9, hgt=0.1)                 # the dark between the spokes
    lay.put(inner & sp, x0, y0, ramp_centre, ctone + 0.6, hgt=0.5)
    if crank is not None and r >= 7:
        cw = (rad < r - 2) & (np.abs(((ang - crank + math.pi) % (2 * math.pi)) - math.pi) < 0.7) & (rad > r * 0.45)
        lay.put(cw, x0, y0, ramp_centre, ctone - 0.4, hgt=0.6)        # counterweight
    hr, ht = hub
    lay.rect(cx - 1, cy - 1, 3, 3, hr, ht - 1.0, hgt=0.8)
    lay.px(cx, cy, hr, ht, hgt=0.9)
    if crank is not None:
        px_, py_ = cx + int(round(math.cos(crank) * r * 0.55)), cy + int(round(math.sin(crank) * r * 0.55))
        lay.rect(px_ - 1, py_ - 1, 2, 2, 'S', 5.4, hgt=0.9)
        return px_, py_
    return cx, cy


def rivet_row(lay, x0, x1, y, step, ramp, tone):
    for x in range(int(x0), int(x1), step):
        lay.px(x, y, ramp, tone + 1.2, hgt=0.7)
        lay.px(x + 1, y + 1, ramp, tone - 0.8)


def sign(lay, x, y, w, h, s, ramp='B', face=2.0, ink=('P', 6.6), font='35', border=True, center=True, ty=None):
    """An enamel sign: rounded border, face, centred text."""
    lay.rect(x, y, w, h, ramp, face, hgt=0.5)
    if border:
        lay.hline(x + 1, y + 1, w - 2, ink[0], ink[1] - 1.2)
        lay.hline(x + 1, y + h - 2, w - 2, ink[0], ink[1] - 1.2)
        lay.vline(x + 1, y + 1, h - 2, ink[0], ink[1] - 1.2)
        lay.vline(x + w - 2, y + 1, h - 2, ink[0], ink[1] - 1.2)
        for (cx, cy) in ((x, y), (x + w - 1, y), (x, y + h - 1), (x + w - 1, y + h - 1)):
            lay.erase(cx, cy, 1, 1)
    gh = 5 if font == '35' else 7
    tyy = y + (h - gh) // 2 if ty is None else ty
    if center:
        K.text(lay, s, x + w / 2, tyy, ink[0], ink[1], font=font, center=True)
    else:
        K.text(lay, s, x + 3, tyy, ink[0], ink[1], font=font)


CYR = {   # 3x5 Cyrillic glyphs not shared with the Latin font (the liaison booth, the courier van)
    'Л': ['.##', '#.#', '#.#', '#.#', '#.#'], 'Ь': ['#..', '#..', '##.', '#.#', '##.'],
    'Я': ['.##', '#.#', '.##', '#.#', '#.#'], 'З': ['##.', '..#', '.#.', '..#', '##.'],
    'Ь_': ['#..', '##.', '#.#', '##.', '...'], 'С': ['.##', '#..', '#..', '#..', '.##'],
    'В': ['##.', '#.#', '##.', '#.#', '##.'], 'Ж': ['#.#', '#.#', '.#.', '#.#', '#.#'],
    'У': ['#.#', '#.#', '.##', '..#', '##.'], 'Р': ['##.', '#.#', '##.', '#..', '#..'],
    'Н': ['#.#', '#.#', '###', '#.#', '#.#'], 'К': ['#.#', '#.#', '##.', '#.#', '#.#'],
    'О': ['.#.', '#.#', '#.#', '#.#', '.#.'], 'Т': ['###', '.#.', '.#.', '.#.', '.#.'],
    'Б': ['###', '#..', '##.', '#.#', '##.'], 'Е': ['###', '#..', '##.', '#..', '###'],
    'Ш': ['#.#', '#.#', '#.#', '#.#', '###'], 'Ч': ['#.#', '#.#', '.##', '..#', '..#'],
    'А': ['.#.', '#.#', '###', '#.#', '#.#'], 'И': ['#.#', '#.#', '#.#', '##.', '#.#'],
    'П': ['###', '#.#', '#.#', '#.#', '#.#'], 'Д': ['.#.', '##.', '##.', '##.', '###'],
    'М': ['#.#', '###', '#.#', '#.#', '#.#'], '-': ['...', '...', '###', '...', '...'],
    ' ': ['...', '...', '...', '...', '...'], '1': ['.#.', '##.', '.#.', '.#.', '###'],
    '7': ['###', '..#', '.#.', '.#.', '.#.'], '4': ['#.#', '#.#', '###', '..#', '..#'],
    '5': ['###', '#..', '##.', '..#', '##.'], 'Ы': ['#.#', '#.#', '###', '#.#', '###'],
}


def cyr_mask(s: str) -> np.ndarray:
    cols = []
    for i, ch in enumerate(s):
        g = CYR.get(ch, CYR[' '])
        m = np.array([[c == '#' for c in row] for row in g], bool)
        cols.append(m)
        if i < len(s) - 1:
            cols.append(np.zeros((5, 1), bool))
    return np.concatenate(cols, axis=1) if cols else np.zeros((5, 0), bool)


def cyr_text(lay, s, x, y, ramp, tone, center=False, **kw):
    m = cyr_mask(s)
    if center:
        x = int(round(x - m.shape[1] / 2))
    kw.setdefault('flat', True)
    kw.setdefault('crisp', True)
    lay.put(m, x, y, ramp, tone, **kw)
    return m.shape[1]


def steam_blob(lay, cx, cy, rx, ry, seed, ramp='V', tone=3.4, dens=0.75):
    """A soft, dithered puff of steam (opaque pixels only where the noise says so)."""
    nz = pg.value_noise(2 * rx + 2, 2 * ry + 2, 4, seed, octaves=3)
    for yy in range(-ry, ry + 1):
        for xx in range(-rx, rx + 1):
            d = (xx / max(1, rx)) ** 2 + (yy / max(1, ry)) ** 2
            if d > 1:
                continue
            v = nz[yy + ry, xx + rx]
            if v * (1.15 - d) > (1 - dens) * 0.6:
                lay.px(cx + xx, cy + yy, ramp, tone + (0.8 - d) * 1.2 - (yy > 0) * 0.5, hgt=0.2)


# =========================================================================== the playfield
class Station:
    def __init__(self, cfg: dict | None = None):
        self.cfg = cfg or {}
        self.hist = bool(self.cfg.get('hist', False))
        self.lay = K.tlayer(W, H, 'station', 'A')
        self.lights: list[dict] = []

    def light(self, name, pos, kind, energy, radius, height=24, **kw):
        d = {'name': name, 'pos': (float(pos[0]), float(pos[1])), 'kind': kind, 'energy': energy,
             'radius': radius, 'height': height}
        d.update(kw)
        self.lights.append(d)
        return d

    # ------------------------------------------------------------------ track K and the platform
    def track_k(self):
        lay = self.lay
        nz = pg.value_noise(W, 24, 5, 701, octaves=3)
        # ballast bed between the platform walls (seen above the coping where no car stands)
        for y in range(244, PE):
            for x in range(W):
                t = 1.2 + (nz[y - 244, x] - 0.5) * 1.0 + (y - 244) * 0.04
                lay.px(x, y, 'S', t, flat=False, hgt=0.1)
        for x in range(0, W, 7):                                          # sleeper ends
            lay.rect(x, 263, 4, 2, 'D', 1.4, hgt=0.3)
        lay.hline(0, L.RAIL_K, W, 'S', 5.2, hgt=0.8)                      # rail heads catch the lamps
        lay.hline(0, L.RAIL_K + 1, W, 'S', 2.6, hgt=0.5)
        lay.hline(0, L.RAIL_K - 6, W, 'S', 3.4, hgt=0.4)                  # the far rail, half hidden
        # the far platform wall (behind track K) -- a dark stone face, seen only in the open stretches
        lay.rect(0, 238, W, 6, 'P', 1.6, hgt=0.3)
        lay.hline(0, 238, W, 'P', 3.4, hgt=0.6)
        for x in range(0, W, 19):
            lay.vline(x, 239, 5, 'P', 1.0)

    def platform(self):
        lay = self.lay
        nz = pg.value_noise(W, 60, 14, 711, octaves=3)
        fine = pg.value_noise(W, 60, 3, 712, octaves=2)
        y0, y1 = PE, L.PLAT_NEAR_Y
        h0 = y1 - y0
        t = 2.0 + (nz[:h0] - 0.5) * 0.8 + (fine[:h0] - 0.5) * 0.35
        ys = np.arange(h0)[:, None]
        t = t + 0.35 * (ys > 26) - 0.25 * (ys > 40)
        lay.put(np.ones((h0, W), bool), 0, y0, 'P', t.astype(np.float32), flat=False, hgt=0.12)
        # coping stones of the far edge and the white safety line
        lay.rect(0, y0, W, 2, 'P', 4.4, hgt=0.7)
        lay.hline(0, y0 + 2, W, 'P', 1.2)
        for x in range(0, W, 23):
            lay.vline(x, y0, 2, 'P', 2.2)
        for x in range(0, W):
            if (x // 3) % 4 != 3:
                lay.px(x, y0 + 6, 'P', 6.4 - (fine[6, x] < 0.3) * 1.5, hgt=0.1)
        # slab joints, wider toward the viewer
        for jy in (y0 + 13, y0 + 23, y0 + 36, y0 + 50):
            if jy < y1:
                lay.hline(0, jy, W, 'P', 1.0, hgt=0.0)
        for row, (ya, yb, step) in enumerate(((y0 + 3, y0 + 13, 31), (y0 + 13, y0 + 23, 38), (y0 + 23, y0 + 36, 46),
                                               (y0 + 36, y0 + 50, 56))):
            off = (row * 17) % step
            for x in range(off, W, step):
                lay.vline(x, ya + 1, yb - ya - 1, 'P', 1.1, hgt=0.0)
        # the timber deck of the platform's end (where the hidden ticket stub lies between two boards)
        x0 = 828
        for yy in range(y0 + 3, y1):
            lay.hline(x0, yy, W - x0, 'D', 2.2 + (nz[yy - y0, x0] - 0.5) * 0.6 + ((yy - y0) % 5 == 0) * 0.4,
                      hgt=0.15)
        for yy in range(y0 + 3, y1):
            if (yy - y0) % 5 == 0:
                lay.hline(x0, yy, W - x0, 'D', 0.9)
        for x in range(x0, W, 37):
            lay.vline(x, y0 + 3, y1 - y0 - 3, 'D', 0.8)
        lay.rect(x0 - 2, y0 + 3, 2, h0 - 3, 'S', 3.2, hgt=0.5)            # iron angle where the deck begins
        sx, sy = L.TICKET_STUB
        lay.hline(sx - 2, sy - 1, 8, 'D', 0.6)                              # the gap between two boards
        lay.rect(sx, sy - 2, 3, 2, 'P', 5.6, hgt=0.3)                       # the stub, wedged in it
        lay.px(sx + 1, sy - 2, 'R', 3.0)
        # wet patches and blown-in snow near the open end of the hall (left), grit, stubs, a dropped glove
        rng = np.random.default_rng(713)
        for x in range(0, 150):
            depth = int(max(0, (150 - x) / 150 * 7 + (fine[3, x] - 0.5) * 3))
            for k in range(depth):
                lay.px(x, y0 + 3 + k * 2 + int(fine[k, x] * 2), 'V', 3.6 + (k == 0) * 0.8, hgt=0.3)
        for x in range(0, 210):
            for y in range(y0 + 12, y1):
                if fine[y - y0, x] > 0.8 and nz[y - y0, x] > 0.55 and (x + y) % 2 == 0:
                    lay.px(x, y, 'G', 3.0, hgt=-0.1)                      # melt water, mirrors the cold light
        for _ in range(90):
            gx, gy = int(rng.integers(4, W - 4)), int(rng.integers(y0 + 6, y1 - 2))
            lay.px(gx, gy, 'P', 0.6 if rng.random() < 0.6 else 4.8)
        for (bx, by) in ((222, 304), (470, 300), (655, 310), (760, 297)):    # cigarette ends
            lay.rect(bx, by, 2, 1, 'P', 6.0)
            lay.px(bx + 2, by, 'L', 3.4)
        lay.rect(118, 311, 3, 2, 'D', 1.4)                                   # a lost glove
        lay.px(121, 311, 'D', 1.0)
        # the near coping (the foreground starts below it)
        lay.rect(0, y1 - 2, W, 2, 'P', 4.0, hgt=0.6)

    # ------------------------------------------------------------------ the D 303: locomotive
    def loco(self):
        """Engine 01 064, a Pacific with its head to the left (the open end of the hall): buffer beam and lamps, the
        big smoke deflectors, the chimney, the long boiler with handrail, domes and safety valves, the red bar frame,
        cylinder, slide bars and Walschaerts gear, the leading bogie, three red-spoked drivers with coupling and
        connecting rods, the trailing axle, the cab with its lit window, the number plate and the plate above it
        (neutral „DR“ / historical Reichsbahn eagle, 12.4).  The buffet and the kiosk stand in front of it: the
        boiler shows above the buffet's canopy, the drivers through the gap between buffet and kiosk (x 338..380),
        the cab and its plates above the kiosk's roof."""
        lay = self.lay
        x0, x1 = L.LOCO
        cab0 = x1 - 34
        # ---- bar frame (red, lightening holes) and running board
        lay.rect(x0 + 4, 224, cab0 - x0 + 16, 18, 'R', 2.2, hgt=0.3)
        lay.hline(x0 + 4, 224, cab0 - x0 + 16, 'R', 3.2, hgt=0.5)
        for hx in (x0 + 44, x0 + 68, x0 + 92):
            lay.rect(hx - 3, 230, 7, 5, 'I', 0.7)
            lay.hline(hx - 2, 229, 5, 'I', 0.9)
        for ax in (x0 + 56, x0 + 80, x0 + 104):                                 # axle boxes + leaf springs
            lay.rect(ax - 4, 236, 9, 6, 'I', 1.2, hgt=0.6)
            lay.hline(ax - 6, 226, 13, 'S', 3.0, hgt=0.7)
            lay.hline(ax - 5, 227, 11, 'S', 2.2)
        lay.rect(x0 + 2, 220, cab0 - x0 - 2, 3, 'S', 2.2, hgt=0.7)              # running board
        lay.hline(x0 + 2, 220, cab0 - x0 - 2, 'S', 4.4, hgt=0.9)
        # ---- boiler: a lit crown, bands, the handrail on stanchions, pipes
        bx0, bx1, by0, by1 = x0 + 28, cab0 + 2, 176, 220
        for y in range(by0, by1):
            c = (y - by0 + 0.5) / (by1 - by0) * 2 - 1
            t = 1.7 + 2.5 * max(0.0, 0.62 - abs(c + 0.45)) - 0.6 * max(0.0, c - 0.45)
            lay.hline(bx0, y, bx1 - bx0, 'S', t + 0.3, hgt=0.9 * math.sqrt(max(0.0, 1 - c * c)))
        lay.hline(bx0, by0, bx1 - bx0, 'L', 3.4, hgt=0.9)                        # a warm rim along the top
        lay.hline(bx0, by0 + 2, bx1 - bx0, 'S', 5.0, hgt=1.0)                    # the crown catches the lamps
        for xx in range(bx0, bx1):                                                 # the sodium lamps mirrored
            if (xx * 7) % 5 < 3:
                lay.px(xx, by0 + 3, 'L', 3.2, hgt=1.0)
        for bxx in range(bx0 + 12, bx1 - 4, 17):
            lay.vline(bxx, by0 + 1, (by1 - by0) * 2 // 3, 'S', 3.6, hgt=0.8)    # boiler bands, polished
        lay.hline(bx0 + 2, by0 + 13, bx1 - bx0 - 6, 'S', 4.6, hgt=0.9)           # handrail ...
        for sx in range(bx0 + 6, bx1 - 6, 12):
            lay.px(sx, by0 + 14, 'S', 3.2)                                        # ... on its stanchions
        lay.hline(bx0 + 4, by1 - 6, bx1 - bx0 - 8, 'S', 3.6, hgt=0.8)            # feed pipe
        lay.rect(bx0 + 2, by1 - 18, 13, 11, 'I', 1.5, hgt=0.7)                    # feed pump
        lay.hline(bx0 + 2, by1 - 18, 13, 'S', 4.0)
        for k in range(3):
            lay.hline(bx0 + 3, by1 - 15 + k * 3, 11, 'S', 2.6)
        lay.rect(bx1 - 22, by1 - 14, 8, 8, 'L', 2.4, hgt=0.7)                     # brass injector
        lay.px(bx1 - 21, by1 - 14, 'L', 4.0)
        # ---- domes, safety valves, whistle
        for (dx, dw, dh) in ((bx0 + 14, 14, 8), (bx0 + 34, 20, 12)):
            for yy in range(dh + 1):                                               # rounded tops
                ins = 2 if yy == 0 else (1 if yy == 1 else 0)
                lay.hline(dx + ins, by0 - dh + yy, dw - 2 * ins, 'S', 2.6 + (yy < 3) * 0.8, hgt=0.8)
            lay.hline(dx + 2, by0 - dh, dw - 4, 'L', 3.8, hgt=1.0)                  # the lamps on their crowns
            lay.vline(dx, by0 - dh + 2, dh - 1, 'S', 3.4)
            lay.vline(dx + dw - 1, by0 - dh + 2, dh - 1, 'S', 1.6)
        lay.rect(bx1 - 12, by0 - 5, 6, 5, 'S', 3.8, hgt=0.8)                     # safety valves (the steam fx)
        lay.hline(bx1 - 12, by0 - 5, 6, 'S', 5.2)
        lay.rect(bx1 - 4, by0 - 9, 2, 9, 'L', 3.4, hgt=0.8)                      # brass whistle
        lay.px(bx1 - 4, by0 - 10, 'L', 4.6)
        self.safety_valve = (bx1 - 9, by0 - 6)
        # ---- smokebox top and chimney (the deflector covers the smokebox side)
        lay.rect(x0 + 6, by0 - 2, 24, by1 - by0 + 2, 'S', 1.6, hgt=0.8)
        lay.rect(x0 + 13, 158, 11, 18, 'S', 1.8, hgt=0.8)                         # chimney
        lay.rect(x0 + 12, 156, 13, 3, 'S', 3.4, hgt=0.9)                          # its lip
        lay.hline(x0 + 12, 156, 13, 'L', 3.8)
        lay.vline(x0 + 13, 159, 17, 'S', 2.8)
        self.chimney = (x0 + 18, 155)
        # ---- the big smoke deflector (Wagner type): a plate standing proud, its top front corner cut
        dx0, dy0, dw, dh = x0 + 2, 166, 36, 58
        defl = np.zeros((dh, dw), bool)
        for yy in range(dh):
            for xx in range(dw):
                if yy < 8 and xx < 8 - yy:
                    continue
                defl[yy, xx] = True
        dt = np.zeros((dh, dw), np.float32) + np.linspace(2.6, 1.8, dh, dtype=np.float32)[:, None]
        lay.put(defl, dx0, dy0, 'S', dt, hgt=0.5, flat=False)
        edge = K.edge_of(defl)
        top_edge = edge & ~np.roll(edge, 1, axis=0)
        lay.put(top_edge, dx0, dy0, 'L', 3.6, hgt=0.8)                            # lit upper edge
        lay.vline(dx0, dy0 + 8, dh - 8, 'S', 3.6, hgt=0.7)                        # front edge
        lay.rect(dx0 + 7, dy0 + 11, 7, 3, 'I', 0.6)                               # the handhold cut-out
        lay.hline(dx0 + 7, dy0 + 14, 7, 'S', 3.0)
        lay.hline(dx0 + 3, dy0 + 30, dw - 5, 'I', 1.2)                            # its stiffening angle
        lay.hline(dx0 + 3, dy0 + 31, dw - 5, 'S', 2.8)
        # ---- buffer beam, buffers, coupling, the three lamps (lit)
        lay.rect(x0 - 4, 226, 6, 12, 'R', 2.4, hgt=0.7)
        lay.vline(x0 - 4, 226, 12, 'R', 3.4)
        for by in (228, 234):
            lay.rect(x0 - 9, by, 6, 3, 'S', 3.6, hgt=0.8)
            lay.vline(x0 - 9, by, 3, 'S', 5.2)
        lay.rect(x0 - 3, 240, 4, 2, 'I', 1.4)
        for (lx, ly) in ((x0 - 3, 220), (x0 + 8, 160)):
            lay.rect(lx, ly, 4, 5, 'I', 1.4, hgt=0.7)
            lay.rect(lx - 1, ly + 1, 2, 3, 'L', 5.0, emis=True)
        self.light('loco_lamps', (x0 - 4, 224), 'warm', 0.5, 46, height=8)
        # ---- cylinder, slide bars, crosshead, valve gear
        lay.rect(x0 + 10, 227, 30, 17, 'I', 1.6, hgt=0.8)
        lay.hline(x0 + 10, 227, 30, 'S', 3.8, hgt=0.9)
        for cx_ in (x0 + 16, x0 + 33):
            lay.vline(cx_, 228, 15, 'S', 2.8)
        lay.rect(x0 + 6, 231, 4, 9, 'S', 3.2)                                     # front cover
        lay.rect(x0 + 40, 233, 26, 2, 'S', 5.0, hgt=0.9)                          # slide bars
        lay.rect(x0 + 40, 237, 26, 1, 'S', 3.6)
        # ---- wheels: leading bogie, three coupled drivers (red centres), the trailing axle under the cab
        wheel(lay, x0 + 14, 256, 6, spokes=8, ctone=1.6)
        wheel(lay, x0 + 30, 256, 6, spokes=8, ctone=1.6)
        pins = []
        for cx in (x0 + 56, x0 + 80, x0 + 104):
            pins.append(wheel(lay, cx, 251, 11, crank=0.6, ctone=2.6, spokes=14))
        wheel(lay, x1 - 16, 254, 8, spokes=10, ctone=2.0)
        lay.rect(x1 - 26, 241, 20, 4, 'I', 1.1, hgt=0.6)                          # trailing truck frame
        # coupling rod, connecting rod from the crosshead, the Walschaerts eccentric rod and link
        lay.line(pins[0][0], pins[0][1], pins[2][0], pins[2][1], 'S', 5.0, hgt=0.9)
        lay.line(pins[0][0], pins[0][1] + 1, pins[2][0], pins[2][1] + 1, 'S', 2.6, hgt=0.6)
        chx = x0 + 52
        lay.rect(chx - 3, 233, 6, 5, 'S', 3.8, hgt=0.9)                            # crosshead
        lay.line(chx, 236, pins[1][0], pins[1][1], 'S', 4.6, hgt=0.9)
        lay.line(chx, 237, pins[1][0], pins[1][1] + 1, 'S', 2.4)
        rc = (pins[1][0] + 2, pins[1][1] - 4)                                      # return crank -> link
        lay.line(rc[0], rc[1], x0 + 70, 230, 'S', 3.6)
        lay.rect(x0 + 68, 226, 3, 7, 'S', 3.0)
        lay.line(x0 + 69, 228, x0 + 42, 230, 'S', 3.2)                              # radius rod to the valve
        # ---- the cab: roof, side sheet with panel line, the window (the driver is a life strip), steps
        lay.rect(cab0, 168, x1 - cab0, 76, 'S', 2.1, hgt=0.5)
        lay.vline(cab0, 168, 76, 'S', 3.8, hgt=0.6)
        lay.vline(x1 - 1, 168, 76, 'S', 1.4)
        lay.rect(cab0 - 2, 162, x1 - cab0 + 4, 6, 'I', 1.7, hgt=0.8)               # the roof, curved
        lay.hline(cab0 - 1, 162, x1 - cab0 + 2, 'L', 3.4, hgt=0.9)
        lay.hline(cab0 - 2, 167, x1 - cab0 + 4, 'I', 0.8)
        lay.rect(cab0 + 12, 159, 8, 3, 'I', 1.5, hgt=0.9)                          # roof vent
        lay.hline(cab0 + 12, 159, 8, 'S', 3.4)
        lay.hline(cab0 + 1, 228, x1 - cab0 - 2, 'S', 2.6)                          # panel line
        wx0, wy0, ww, wh = cab0 + 5, 177, 19, 16
        lay.rect(wx0 - 1, wy0 - 1, ww + 2, wh + 2, 'S', 3.2, hgt=0.7)              # window frame
        lay.vgrad(wx0, wy0, ww, wh, 'L', 2.0, 1.3, emis=True)                       # the cab lit by the fire
        lay.rect(wx0, wy0 + wh - 4, ww, 4, 'L', 2.6, emis=True)
        lay.hline(wx0 - 1, wy0 + wh, ww + 2, 'S', 4.6, hgt=0.9)                     # sill
        self.cab_window = (wx0, wy0, ww, wh)
        for (hx, t) in ((cab0 + 2, 3.6), (x1 - 3, 3.0)):                           # brass grab handles
            lay.vline(hx, 198, 30, 'L', t, hgt=0.9)
        for k in range(3):                                                           # the steps
            lay.rect(cab0 + 1, 246 + k * 5, 7, 2, 'S', 3.6 - k * 0.4, hgt=0.7)
        lay.vline(cab0 + 1, 246, 14, 'S', 2.6)
        # the plate above the number: neutral „DR“ monogram / historical: the Reichsbahn eagle (12.4)
        pcx, py0 = cab0 + 17, 196
        if self.hist:
            import env_berlin_insignia as BI
            ms = BI.eagle_masks(10, wreath=True, swastika=True)
            hh, ww_ = ms['body'].shape
            ex = pcx - ww_ // 2
            lay.put(ms['body'], ex, py0, 'L', 3.4, hgt=0.7)
            lay.put(ms['lines'] | ms['eye'], ex, py0, 'L', 2.0)
            lay.put(ms['wreath'], ex, py0, 'L', 4.4)
            lay.put(ms['swastika'], ex, py0, 'I', 0.6)
        else:
            lay.rect(pcx - 7, py0 + 3, 14, 10, 'L', 2.2, hgt=0.6)                  # a brass monogram plate
            lay.hline(pcx - 7, py0 + 3, 14, 'L', 3.8)
            lay.vline(pcx - 7, py0 + 4, 9, 'L', 3.2)
            for (cx_, cy_) in ((pcx - 7, py0 + 3), (pcx + 6, py0 + 3), (pcx - 7, py0 + 12), (pcx + 6, py0 + 12)):
                lay.px(cx_, cy_, 'I', 1.4)
            K.text(lay, 'DR', pcx - 3, py0 + 6, 'I', 0.6)
        self.cab_plate = (pcx - 8, py0 - 1, 17, 18)
        # the number plate: black, polished rim and figures
        lay.rect(cab0 + 3, 213, 28, 8, 'S', 5.0, hgt=0.8)
        lay.rect(cab0 + 4, 214, 26, 6, 'I', 0.7, hgt=0.6)
        K.text(lay, '01 064', cab0 + 6, 215, 'P', 6.6)
        self.light('firebox', (wx0 + ww / 2, wy0 + wh - 2), 'warm', 0.7, 54, height=10)
        self.cab = (cab0, 168)

    def tender(self):
        """The 2'2' tender: coal heaped above the rails, the water filler, the lettering „Deutsche Reichsbahn“, red
        frame, two bogies."""
        lay = self.lay
        x0, x1 = L.TENDER
        lay.rect(x0, 182, x1 - x0, 60, 'I', 1.4, hgt=0.6)
        lay.hline(x0, 182, x1 - x0, 'S', 3.8, hgt=0.8)
        lay.vline(x0, 183, 58, 'S', 2.8)
        lay.vline(x1 - 1, 183, 58, 'I', 0.9)
        lay.rect(x0 + 1, 178, x1 - x0 - 2, 4, 'I', 1.1, hgt=0.7)                  # the coal rails
        for xx in range(x0 + 4, x1 - 2, 6):
            lay.vline(xx, 178, 4, 'S', 2.4)
        rng = np.random.default_rng(721)
        for x in range(x0 + 2, x1 - 2):                                           # coal heap
            hh = 4 + int(4 * math.sin((x - x0) / (x1 - x0) * math.pi)) + int(rng.integers(0, 2))
            for k in range(hh):
                lay.px(x, 179 - k, 'I', 0.8 + rng.random() * 0.8 + (k == hh - 1) * 0.7, hgt=0.4)
        for _ in range(14):
            lay.px(x0 + int(rng.integers(4, x1 - x0 - 4)), 174 + int(rng.integers(0, 5)), 'S', 3.6)
        lay.rect(x1 - 14, 175, 8, 4, 'S', 2.4, hgt=0.8)                            # water filler hatch
        lay.hline(x1 - 14, 175, 8, 'S', 4.0)
        K.text(lay, 'DEUTSCHE', (x0 + x1) / 2, 192, 'P', 5.6, center=True)
        K.text(lay, 'REICHSBAHN', (x0 + x1) / 2, 200, 'P', 5.6, center=True)
        rivet_row(lay, x0 + 2, x1 - 2, 186, 5, 'I', 1.4)
        rivet_row(lay, x0 + 2, x1 - 2, 238, 5, 'I', 1.4)
        lay.rect(x0 + 4, 241, x1 - x0 - 8, 6, 'R', 1.6, hgt=0.3)
        for cx in (x0 + 10, x0 + 24, x0 + 38):
            wheel(lay, cx, 256, 6, spokes=8, ctone=1.8)
        lay.rect(x1 - 2, 230, 4, 3, 'S', 3.6, hgt=0.8)                             # buffer toward the van

    # ------------------------------------------------------------------ the courier van and the gap
    def courier(self):
        lay = self.lay
        x0, x1 = L.COURIER
        top, bot = 178, 248
        # body: vertical boards, painted dark grey-olive, iron frame
        for x in range(x0 + 1, x1 - 1):
            t = 2.6 + 0.5 * (((x - x0) % 6) == 0) * -1 + (0.3 if ((x - x0) % 6) == 1 else 0)
            lay.vline(x, top + 4, bot - top - 4, 'S', t, hgt=0.4)
        lay.rect(x0, top + 2, x1 - x0, 3, 'S', 3.8, hgt=0.7)
        lay.rect(x0, bot - 3, x1 - x0, 3, 'I', 1.4, hgt=0.6)
        lay.vline(x0, top + 2, bot - top - 2, 'S', 3.6, hgt=0.6)
        lay.vline(x1 - 1, top + 2, bot - top - 2, 'I', 1.2, hgt=0.6)
        for xx in (x0 + 16, x1 - 18):                                          # diagonal braces
            lay.line(xx - 10, bot - 6, xx + 6, top + 12, 'I', 1.4, hgt=0.6)
        # roof (curved), torpedo vents
        for k, (ins, t) in enumerate(((3, 2.0), (1, 2.6), (0, 3.2))):
            lay.hline(x0 + ins, top - 3 + k, x1 - x0 - 2 * ins, 'S', t, hgt=0.8)
        for vx in (x0 + 18, x0 + 58):
            lay.rect(vx, top - 7, 5, 4, 'S', 2.4, hgt=0.9)
            lay.hline(vx, top - 7, 5, 'S', 4.0)
        # the sliding door with its rail and the two lead seals on the wire at the handle
        d0, d1 = L.COURIER_DOOR
        lay.rect(d0, top + 8, d1 - d0, bot - top - 12, 'S', 3.0, hgt=0.5)
        lay.hline(d0 - 2, top + 7, d1 - d0 + 4, 'I', 1.0, hgt=0.6)              # door rail
        lay.rect(d0, top + 8, 1, bot - top - 12, 'S', 4.4)
        for yy in range(top + 14, bot - 6, 9):
            lay.hline(d0 + 1, yy, d1 - d0 - 2, 'S', 2.2)
        hx = d1 - 5
        lay.rect(hx, 220, 2, 8, 'S', 4.8, hgt=0.9)                              # handle
        lay.line(hx - 4, 224, hx + 1, 230, 'S', 3.6)                            # the sealing wire
        for (sx, sy) in ((hx - 4, 229), (hx - 1, 231)):                          # two lead seals
            lay.rect(sx, sy, 3, 3, 'V', 2.6, hgt=0.8)
            lay.px(sx, sy, 'V', 4.4)
        # plates: „Kurier – Zutritt verboten“ (German / Russian) and the route board
        lay.rect(x0 + 8, top + 13, 30, 14, 'P', 5.4, hgt=0.5)
        lay.hline(x0 + 8, top + 13, 30, 'P', 6.4)
        K.text(lay, 'KURIER', x0 + 11, top + 15, 'R', 2.2)
        cyr_text(lay, 'КУРЬЕР', x0 + 11, top + 21, 'I', 0.8)
        lay.rect(x0 + 6, top + 30, 34, 7, 'B', 2.0, hgt=0.4)
        K.text(lay, 'C-17', x0 + 15, top + 31, 'P', 6.4)
        lay.rect(x1 - 18, top + 14, 14, 9, 'P', 4.6, hgt=0.5)                   # weight / date stencil
        K.pseudo_text(lay, x1 - 16, top + 16, 10, 3, 'I', 1.0, seed=31)
        # underframe, springs, two axles
        lay.rect(x0 + 6, bot, x1 - x0 - 12, 3, 'I', 0.9)
        for cx in (x0 + 18, x1 - 18):
            lay.rect(cx - 9, bot + 1, 18, 2, 'S', 2.8, hgt=0.7)                 # leaf spring
            lay.hline(cx - 7, bot + 3, 14, 'S', 2.0)
            wheel(lay, cx, 257, 8, spokes=10, ramp_centre='S', ctone=2.2)
        for (bx, by) in ((x0 - 4, 234), (x1, 234)):
            lay.rect(bx, by, 4, 3, 'S', 3.6, hgt=0.8)

    def gap(self):
        """Between the van and the dining car: not coupled yet -- buffers, the hanging hose, the dining car's folded
        gangway; through the gap the next track (st_track2) shows the green car."""
        lay = self.lay
        g0, g1 = L.GAP
        lay.rect(g0, 233, 3, 4, 'S', 3.2, hgt=0.8)
        lay.rect(g0, 244, 4, 2, 'I', 1.2)
        lay.line(g0 + 2, 246, g0 + 6, 256, 'I', 1.0)                             # the brake hose hanging down
        lay.rect(g1 - 5, 232, 5, 4, 'S', 3.6, hgt=0.8)                            # the diner's buffer
        lay.rect(g1 - 4, 182, 4, 48, 'I', 1.2, hgt=0.6)                           # folded gangway bellows
        for yy in range(184, 228, 3):
            lay.hline(g1 - 4, yy, 4, 'I', 1.9)
        lay.vline(g1 - 5, 182, 48, 'S', 2.6)
        # a shunter's hand lamp left on the coping (red / white), the coupling chain on the ground
        lay.rect(g0 + 34, PE - 6, 5, 6, 'I', 1.4, hgt=0.6)
        lay.rect(g0 + 35, PE - 5, 3, 3, 'R', 3.6, emis=True)
        lay.hline(g0 + 34, PE - 7, 5, 'S', 3.4)
        self.light('shunter_lamp', (g0 + 36, PE - 4), 'warm', 0.25, 20, height=4)

    # ------------------------------------------------------------------ the dining car and the sleeper
    def car_body(self, x0, x1, ramp, face, top=166, bot=L.CAR_BOT, vents=True):
        lay = self.lay
        for y in range(top + 5, bot):
            c = (y - top) / (bot - top)
            t = face + 0.5 * (c < 0.12) - 0.6 * (c > 0.86)
            lay.hline(x0, y, x1 - x0, ramp, t, hgt=0.4 + 0.2 * math.sin(math.pi * c))
        for k, (ins, t) in enumerate(((5, 1.6), (2, 2.2), (1, 2.8), (0, 3.0), (0, 2.6))):
            lay.hline(x0 + ins, top + k, x1 - x0 - 2 * ins, 'S', t, hgt=0.9)
        if vents:
            for vx in range(x0 + 14, x1 - 10, 30):                               # torpedo vents on the roof
                lay.rect(vx, top - 3, 6, 3, 'S', 2.4, hgt=1.0)
                lay.hline(vx + 1, top - 3, 4, 'S', 3.6)
        lay.hline(x0, top + 5, x1 - x0, 'S', 1.6)                                # gutter
        lay.vline(x0, top + 5, bot - top - 5, ramp, face + 0.8)
        lay.vline(x1 - 1, top + 5, bot - top - 5, ramp, face - 0.9)
        for jx in range(x0 + 44, x1 - 20, 44):                                   # panel joints
            lay.vline(jx, top + 6, bot - top - 7, ramp, face - 0.5)
        lay.rect(x0 + 1, bot - 5, x1 - x0 - 2, 5, ramp, face - 0.7, hgt=0.3)     # the lower skirt, grimy
        lay.hline(x0 + 1, bot - 5, x1 - x0 - 2, ramp, face + 0.3)
        rng = np.random.default_rng(x0)
        for _ in range((x1 - x0) // 3):                                          # road grime splashed up
            lay.px(x0 + int(rng.integers(1, x1 - x0 - 1)), bot - int(rng.integers(1, 9)), ramp, face - 1.0)
        lay.rect(x0 + 4, bot, x1 - x0 - 8, 3, 'I', 0.9)
        lay.rect(x0 + 30, bot + 1, 18, 4, 'I', 1.4)                               # battery box / gas tank
        lay.rect(x1 - 70, bot + 1, 22, 4, 'I', 1.4)
        lay.hline(x1 - 70, bot + 1, 22, 'S', 2.6)

    def bogie(self, cx):
        lay = self.lay
        lay.rect(cx - 15, 252, 30, 5, 'I', 1.2, hgt=0.6)
        lay.hline(cx - 15, 252, 30, 'S', 2.8)
        lay.rect(cx - 6, 254, 12, 3, 'S', 2.4)
        for dx in (-9, 9):
            wheel(lay, cx + dx, 259, 6, spokes=10, ramp_centre='S', ctone=1.8)

    def diner(self):
        lay = self.lay
        x0, x1 = L.DINER
        self.car_body(x0, x1, 'R', 1.9)
        K.text(lay, 'SPEISEWAGEN', x0 + 64, 176, 'P', 5.8)
        # the kitchen at the left end: two small frosted windows, the roof chimney (its steam is a strip)
        for kx in (x0 + 4, x0 + 14):
            lay.rect(kx, 194, 7, 10, 'L', 2.0, emis=True)
            lay.rect(kx, 194, 7, 3, 'P', 4.6, emis=True)
            lay.rect(kx - 1, 193, 9, 1, 'S', 3.4)
        lay.rect(x0 + 10, 158, 5, 8, 'S', 2.0, hgt=0.9)
        lay.hline(x0 + 9, 158, 7, 'S', 3.2)
        self.kitchen_vent = (x0 + 12, 157)
        # the destination plate in its holder, white enamel
        lay.rect(x1 - 82, 229, 50, 7, 'P', 6.4, hgt=0.4)
        lay.hline(x1 - 82, 229, 50, 'S', 3.6)
        K.text(lay, 'BERLIN-KARSK', x1 - 80, 230, 'B', 1.2)
        lay.hline(x0 + 2, 186, x1 - x0 - 4, 'R', 3.0, hgt=0.6)                   # cream-lined belt rail
        lay.hline(x0 + 2, 226, x1 - x0 - 4, 'R', 3.0, hgt=0.6)
        # the windows: tablecloths, lamps with red shades, curtains; the diners are a life strip
        self.diner_windows = []
        wx = x0 + 26
        for i in range(7):
            ww = 20
            if wx + ww > L.DINER_DOOR[0] - 4:
                break
            self.window_lit(wx, 190, ww, 32, seed=40 + i, table=True)
            self.diner_windows.append((wx, 190, ww, 32))
            wx += ww + 5
        # the open door: a lit vestibule, steps, brass handrails; the first table with the guidebook
        d0, d1 = L.DINER_DOOR
        lay.rect(d0, 182, d1 - d0, 70, 'R', 1.2)
        lay.rect(d0 + 2, 184, d1 - d0 - 4, 66, 'L', 2.2, emis=True)
        lay.rect(d0 + 2, 184, d1 - d0 - 4, 3, 'L', 1.4, emis=True)
        lay.rect(d0 + 3, 226, 14, 3, 'P', 6.6, emis=True)                         # the table edge (cloth)
        lay.rect(d0 + 3, 229, 14, 6, 'P', 5.0, emis=True)                          # cloth hanging down
        lay.rect(d0 + 6, 223, 7, 3, 'B', 2.4, emis=True)                           # the guidebook, blue linen
        lay.hline(d0 + 6, 223, 7, 'B', 3.2, emis=True)
        lay.px(d0 + 12, 224, 'P', 6.6, emis=True)                                  # a slip of paper sticks out
        lay.rect(d0 + 15, 219, 2, 7, 'P', 6.0, emis=True)                          # a tea glass
        lay.rect(d0 + 14, 219, 1, 2, 'S', 4.6, emis=True)
        lay.rect(d0 + 4, 210, 5, 4, 'R', 3.6, emis=True)                           # table lamp, red shade
        lay.rect(d0 + 6, 214, 1, 9, 'L', 4.6, emis=True)
        for k in range(4):                                                          # folding steps
            lay.rect(d0 + 2 - k, 252 + k * 4, d1 - d0 - 4 + 2 * k, 2, 'S', 3.6 - k * 0.3, hgt=0.7)
        lay.vline(d0 - 1, 190, 60, 'L', 3.4, hgt=0.9)                              # brass handrails
        lay.vline(d1, 190, 60, 'L', 3.0, hgt=0.9)
        self.light('diner_door', ((d0 + d1) / 2, 214), 'warm', 0.75, 78, height=10, pool=0.6, pool_w=10)
        self.bogie(x0 + 34)
        self.bogie(x1 - 38)
        lay.rect(x0 - 4, 233, 4, 3, 'S', 3.6, hgt=0.8)
        for i, (wx, wy, ww, wh) in enumerate(self.diner_windows):
            self.light('diner_win_%d' % i, (wx + ww / 2, wy + wh / 2), 'warm', 0.42, 64, height=10,
                       pool=0.35, pool_w=8)

    def window_lit(self, x, y, w, h, seed=0, table=False, blind=0.0):
        """A lit coach window: frame, warm interior, curtains, (table: cloth + lamp)."""
        lay = self.lay
        lay.rect(x - 1, y - 1, w + 2, h + 2, 'S', 3.0, hgt=0.7)
        lay.vgrad(x, y, w, h, 'L', 3.6, 2.4, emis=True)
        lay.rect(x, y, 3, h, 'P', 4.8, emis=True)                                 # curtains tied back
        lay.rect(x + w - 3, y, 3, h, 'P', 4.4, emis=True)
        lay.rect(x + 1, y + 2, 1, h - 6, 'P', 5.8, emis=True)
        if blind > 0:
            lay.rect(x + 3, y, w - 6, int(h * blind), 'P', 3.6, emis=True)
        if table:
            ty = y + h - 9
            lay.rect(x + 3, ty, w - 6, 2, 'P', 7.0, emis=True)                    # tablecloth
            lay.rect(x + 4, ty + 2, w - 8, 3, 'P', 5.8, emis=True)
            lay.rect(x + w // 2 - 2, ty - 8, 5, 3, 'R', 3.6, emis=True)            # lamp with a red shade
            lay.px(x + w // 2, ty - 5, 'L', 5.0, emis=True)
            lay.rect(x + w // 2, ty - 5, 1, 5, 'L', 4.4, emis=True)
            lay.rect(x + 5, ty - 3, 2, 3, 'P', 6.4, emis=True)                    # glasses, a bottle
            lay.rect(x + w - 7, ty - 4, 1, 4, 'E', 2.6, emis=True)
        lay.hline(x - 1, y + h + 1, w + 2, 'S', 4.2, hgt=0.8)                      # window sill rail

    def sleeper(self):
        lay = self.lay
        x0, x1 = L.SLEEPER
        x1 = min(x1, W)
        self.car_body(x0, x1 + 4, 'B', 1.9)
        K.text(lay, 'SCHLAFWAGEN', x0 + 30, 176, 'P', 6.0)
        pw = K.tw('KORDON-17') + 4                                                # the plate fits its words
        px0 = x0 + 20                                                             # between door and fence
        lay.rect(px0, 228, pw, 9, 'P', 6.4, hgt=0.4)
        lay.hline(px0, 228, pw, 'S', 3.6)
        lay.hline(px0, 236, pw, 'P', 4.6)
        K.text(lay, 'KORDON-17', px0 + pw / 2, 230, 'B', 1.2, center=True)
        lay.hline(x0 + 2, 186, x1 - x0 - 2, 'B', 2.8)
        # the door at the car's left end (the family waits at it), then compartment windows, blinds half down
        lay.rect(x0 + 2, 184, 16, 66, 'B', 1.4, hgt=0.4)
        lay.rect(x0 + 4, 188, 12, 18, 'L', 2.4, emis=True)                        # door window, lit corridor
        lay.vline(x0 + 1, 188, 62, 'L', 3.2, hgt=0.9)
        for k in range(4):
            lay.rect(x0 + 4 - k, 252 + k * 4, 12 + 2 * k, 2, 'S', 3.4 - k * 0.3, hgt=0.7)
        wx = x0 + 32
        i = 0
        while wx + 18 < x1 + 2:
            lit = i in (0, 2)
            if lit:
                self.window_lit(wx, 192, 18, 26, seed=60 + i, blind=0.45)
            else:
                lay.rect(wx - 1, 191, 20, 28, 'S', 3.0, hgt=0.7)
                lay.vgrad(wx, 192, 18, 26, 'B', 1.2, 0.6)
                lay.rect(wx, 192, 18, 12, 'B', 2.2)                                # blind down
                lay.hline(wx, 204, 18, 'B', 3.0)
            wx += 24
            i += 1
        self.bogie(x0 + 40)
        self.light('sleeper_door', (x0 + 10, 196), 'warm', 0.35, 44, height=8)
        self.light('sleeper_win', (x0 + 41, 205), 'warm', 0.3, 50, height=8)

    # ------------------------------------------------------------------ the barrier and the liaison booth
    def booth(self):
        lay = self.lay
        x0, x1 = L.BOOTH
        top, base = 206, 292
        # steel frame, glazed upper half, panelled lower half
        lay.rect(x0, top, x1 - x0, base - top, 'S', 1.8, hgt=0.5)
        lay.rect(x0 - 2, top - 6, x1 - x0 + 4, 6, 'S', 2.6, hgt=0.8)               # roof
        lay.hline(x0 - 2, top - 6, x1 - x0 + 4, 'S', 4.2, hgt=0.9)
        K.snowcap(lay, x0 - 2, top - 6, x1 - x0 + 4, 1, seed=5, ramp='V', tone=3.8)
        lay.rect(x0 + 2, top + 4, x1 - x0 - 4, 40, 'L', 1.8, emis=True)            # the lit glazing
        for mx in (x0 + 2, x0 + 19, x0 + 36, x1 - 3):
            lay.vline(mx, top + 4, 40, 'S', 3.4, hgt=0.7)                          # mullions
        lay.hline(x0 + 2, top + 4, x1 - x0 - 4, 'S', 3.0)
        # inside: the desk, the lamp, a stamp pad, a ruler, papers, a tea glass in its metal holder
        lay.rect(x0 + 3, top + 34, x1 - x0 - 6, 3, 'D', 3.0, emis=True)
        lay.rect(x0 + 26, top + 22, 6, 3, 'E', 2.6, emis=True)                     # green desk lamp shade
        lay.rect(x0 + 28, top + 25, 1, 9, 'S', 4.0, emis=True)
        lay.rect(x0 + 27, top + 25, 4, 1, 'L', 5.0, emis=True)
        lay.rect(x0 + 8, top + 32, 8, 2, 'P', 6.4, emis=True)                      # papers
        lay.rect(x0 + 36, top + 32, 4, 2, 'B', 2.6, emis=True)                     # stamp pad
        lay.hline(x0 + 18, top + 33, 9, 'D', 4.4, emis=True)                       # ruler
        lay.hline(x0 + 2, top + 44, x1 - x0 - 4, 'S', 4.0, hgt=0.8)                # sill
        for px_ in range(x0 + 4, x1 - 4, 9):                                        # lower panels
            K.recess(lay, px_, top + 48, 7, 30, 'S', 1.6, shadow=1.0, light=2.6)
        # signs over the glazing: German and Russian, the two plates with the emblems (12.4)
        sign(lay, x0 - 1, top - 16, x1 - x0 + 2, 9, 'KONTROLLE', ramp='B', face=1.6)
        lay.rect(x0 + 2, top - 26, x1 - x0 - 4, 9, 'R', 1.4, hgt=0.5)
        cyr_text(lay, 'КОНТРОЛЬ', (x0 + x1) / 2, top - 24, 'P', 6.2, center=True)
        lay.rect(x0 + 1, top + 52, 12, 13, 'P', 4.6, hgt=0.6)
        K.emblem(lay, x0 + 7, top + 53, 11, self.hist, ramp_light='L', ramp_dark='I')
        lay.rect(x1 - 13, top + 52, 12, 13, 'R', 2.0, hgt=0.6)
        K.soviet_emblem(lay, x1 - 11, top + 55, self.hist, 'L', 4.6, kind='gw7')
        self.booth_box = (x0, top, x1, base)
        self.light('booth_lamp', (x0 + 28, top + 28), 'warm', 0.75, 70, height=10, pool=0.4)
        # the barrier: a low railing with an open swing gate, a chained post
        bx0, bx1 = L.BARRIER
        for x in range(x1, bx1 + 1, 5):
            lay.vline(x, 270, 22, 'S', 3.0, hgt=0.6)
        lay.hline(x1, 270, bx1 - x1 + 2, 'S', 4.4, hgt=0.8)
        lay.hline(x1, 281, bx1 - x1 + 2, 'S', 3.4, hgt=0.7)
        lay.rect(bx1, 266, 3, 26, 'S', 3.6, hgt=0.8)
        lay.rect(bx1 - 1, 264, 5, 2, 'S', 4.6, hgt=0.9)

    # ------------------------------------------------------------------ the departure board
    def board(self):
        lay = self.lay
        x0, x1 = L.BOARD
        # two cast-iron posts with a crown and a gooseneck lamp
        for px_ in (x0 + 4, x1 - 7):
            K.cyl(lay, px_, 184, 4, 108, 'S', 2.2, hgt=0.8)
            lay.rect(px_ - 1, 288, 6, 4, 'S', 2.8, hgt=0.7)
            lay.rect(px_ - 1, 182, 6, 3, 'S', 3.6, hgt=0.9)
        lay.rect(x0 + 2, 180, x1 - x0 - 4, 3, 'S', 3.0, hgt=0.9)
        lay.line((x0 + x1) // 2, 180, (x0 + x1) // 2 + 6, 172, 'S', 3.2)
        lay.rect((x0 + x1) // 2 + 4, 170, 7, 3, 'E', 2.6, hgt=0.8)
        lay.px((x0 + x1) // 2 + 7, 173, 'L', 5.0, emis=True)
        self.light('board_lamp', ((x0 + x1) / 2 + 7, 176), 'warm', 0.45, 44, height=8)
        # the enamel board: platform letter, train, route, time
        by0 = 186
        lay.rect(x0, by0, x1 - x0, 44, 'B', 1.6, hgt=0.5)
        lay.rect(x0 + 1, by0 + 1, x1 - x0 - 2, 42, 'B', 2.2, hgt=0.5)
        lay.hline(x0 + 2, by0 + 2, x1 - x0 - 4, 'P', 5.4)
        lay.hline(x0 + 2, by0 + 41, x1 - x0 - 4, 'P', 5.4)
        lay.rect(x0 + 3, by0 + 4, 11, 11, 'P', 6.8, hgt=0.6)                     # the platform letter K
        K.text(lay, 'K', x0 + 6, by0 + 6, 'B', 1.2, font='57')
        K.text(lay, 'KORRIDOR OST', x0 + 18, by0 + 5, 'P', 6.6)
        K.text(lay, 'BAHNSTEIG K', x0 + 18, by0 + 11, 'P', 4.8)
        lay.hline(x0 + 2, by0 + 17, x1 - x0 - 4, 'P', 4.0)
        K.text(lay, 'D 303', x0 + 4, by0 + 20, 'P', 7.0)
        K.text(lay, '21.10', x1 - 24, by0 + 20, 'L', 5.0)
        K.text(lay, 'BERLIN OST', x0 + 26, by0 + 20, 'P', 6.4)
        K.text(lay, 'KORDON-17 · KARSK', x0 + 4, by0 + 28, 'P', 6.6)
        K.text(lay, 'MIT SPEISEWAGEN', x0 + 4, by0 + 34, 'P', 4.6)
        # the freshly painted board for Tuesday, hung below on two hooks
        hy = by0 + 48
        lay.line(x0 + 14, by0 + 44, x0 + 14, hy, 'S', 3.0)
        lay.line(x1 - 14, by0 + 44, x1 - 14, hy, 'S', 3.0)
        lay.rect(x0 + 4, hy, x1 - x0 - 8, 25, 'D', 2.4, hgt=0.4)
        lay.hline(x0 + 4, hy, x1 - x0 - 8, 'D', 3.6)
        lay.hline(x0 + 4, hy + 24, x1 - x0 - 8, 'D', 1.2)
        K.text(lay, 'DIENSTAG: SONDERZUG', x0 + 6, hy + 3, 'P', 6.2)
        K.text(lay, 'KORDON-17  AB 15.30', x0 + 6, hy + 10, 'P', 6.0)
        lay.rect(x0 + 5, hy + 16, K.tw('BAHNSTEIG K GESPERRT') + 3, 7, 'P', 6.2)       # a cream strip ...
        K.text(lay, 'BAHNSTEIG K GESPERRT', x0 + 7, hy + 17, 'R', 3.0)                    # ... red letters on it
        rng = np.random.default_rng(81)
        for _ in range(12):                                                        # brush drips of the paint
            dx = x0 + 6 + int(rng.integers(0, x1 - x0 - 14))
            lay.px(dx, hy + 9 + int(rng.integers(0, 2)) * 7, 'P', 5.0)

    # ------------------------------------------------------------------ baggage counter and the decimal scale
    def baggage(self):
        lay = self.lay
        x0, x1 = L.BAGGAGE
        hx0 = 172
        # the hut: wooden boards, a hatch window with a sill (the clerk is a life strip), a sign
        K.grain(lay, hx0, 214, x1 - hx0, 78, 'D', 2.2, seed=91, amp=0.3)
        lay.rect(hx0 - 2, 208, x1 - hx0 + 4, 6, 'D', 3.0, hgt=0.8)
        lay.hline(hx0 - 2, 208, x1 - hx0 + 4, 'D', 4.2, hgt=0.9)
        K.snowcap(lay, hx0 - 2, 208, x1 - hx0 + 4, 1, seed=9, ramp='V', tone=3.4)
        lay.rect(hx0 + 4, 230, 20, 20, 'L', 1.8, emis=True)
        lay.rect(hx0 + 4, 230, 20, 2, 'L', 1.2, emis=True)
        lay.rect(hx0 + 3, 250, 22, 3, 'D', 3.8, hgt=0.8)                         # counter sill
        lay.rect(hx0 + 6, 247, 8, 3, 'P', 6.4, emis=True)                         # luggage slips
        lay.rect(hx0 + 16, 246, 5, 4, 'D', 3.6, emis=True)                        # the slip book
        sign(lay, hx0, 216, x1 - hx0, 9, 'GEPÄCK', ramp='B', face=1.8, border=False)
        self.light('baggage_hatch', (hx0 + 14, 240), 'warm', 0.45, 46, height=8)
        # the decimal scale: platform, column, beam with two sliding weights, the suitcase
        s0, s1 = L.SCALE
        lay.rect(s0, 284, 22, 6, 'S', 2.6, hgt=0.6)
        lay.hline(s0, 284, 22, 'S', 4.0, hgt=0.7)
        lay.rect(s0 + 1, 290, 20, 2, 'I', 1.0)
        K.cyl(lay, s0 + 22, 256, 4, 34, 'S', 2.4, hgt=0.7)
        lay.rect(s0 + 20, 254, 18, 3, 'S', 3.4, hgt=0.8)                          # the beam at hand height
        lay.hline(s0 + 20, 254, 18, 'S', 5.0)
        lay.rect(s0 + 25, 252, 3, 3, 'L', 3.6, hgt=0.9)                            # the two sliding weights
        lay.rect(s0 + 31, 252, 2, 3, 'L', 3.0, hgt=0.9)
        lay.rect(s0 + 36, 251, 2, 6, 'S', 3.0)                                     # the tongue
        lay.rect(s0 + 3, 270, 16, 14, 'D', 2.8, hgt=0.6)                           # the suitcase on it
        lay.hline(s0 + 3, 270, 16, 'D', 4.0, hgt=0.7)
        lay.rect(s0 + 9, 268, 4, 2, 'D', 1.2)
        lay.vline(s0 + 5, 271, 13, 'L', 2.6)                                       # strap
        lay.vline(s0 + 16, 271, 13, 'L', 2.6)
        lay.rect(s0 + 12, 274, 5, 3, 'P', 6.2)                                     # a luggage label
        # a sack-trolley leaning on the hut
        lay.line(x1 - 2, 290, x1 + 4, 258, 'S', 3.4)
        lay.line(x1 + 2, 290, x1 + 7, 262, 'S', 2.6)
        lay.rect(x1 - 4, 287, 5, 5, 'I', 1.4)

    # ------------------------------------------------------------------ the buffet
    def buffet(self, roster: str | None = None):
        """The platform buffet „Erfrischungen“: an open stand under a green canopy on three slim posts -- the counter
        in front (also the y-sorted prop counter_front), behind the attendant the back counter with stacked cups,
        bottles, the nickel urn and the cash box, the menu board hanging from the canopy.  Open at the back: between
        the posts the engine's red frame and wheels show."""
        lay = self.lay
        x0, x1 = L.BUFFET
        ct = L.COUNTER_TOP
        cy0 = 222                                                                     # canopy fascia top
        # the back counter (waist high, behind the attendant): wood, a zinc top, what stands on it
        bt = 246
        K.grain(lay, x0 + 4, bt, x1 - x0 - 8, ct - bt, 'D', 1.8, seed=113, amp=0.3)
        lay.rect(x0 + 4, bt, x1 - x0 - 8, 2, 'S', 4.0, hgt=0.8)
        lay.hline(x0 + 4, bt, x1 - x0 - 8, 'S', 5.2, hgt=0.9)
        for i, cx in enumerate(range(x0 + 8, x0 + 62, 6)):
            if i % 3 == 2:
                lay.rect(cx, bt - 8, 3, 8, 'E', 2.2 + (i % 2), hgt=0.6)              # bottles
                lay.px(cx + 1, bt - 9, 'E', 3.4)
                lay.px(cx, bt - 6, 'E', 3.8)
            else:
                for k in range(2 + i % 2):                                            # stacked cups
                    lay.rect(cx, bt - 3 - k * 3, 4, 3, 'P', 6.0 - k * 0.3, hgt=0.6)
                    lay.hline(cx - 1, bt - 1 - k * 3, 6, 'P', 5.0)
        ux = x0 + 70
        lay.rect(ux, bt - 13, 14, 13, 'S', 3.8, hgt=0.9)                              # the nickel urn
        for y in range(bt - 13, bt):
            lay.px(ux + 2, y, 'S', 5.8)
            lay.px(ux + 11, y, 'S', 2.6)
        lay.rect(ux + 2, bt - 15, 10, 2, 'S', 4.6, hgt=0.9)
        lay.rect(ux + 5, bt - 16, 4, 1, 'I', 1.4)
        lay.rect(ux - 3, bt - 6, 4, 2, 'L', 3.4)                                      # brass tap
        lay.px(ux - 3, bt - 4, 'L', 2.6)
        self.urn = (ux + 7, bt - 16)
        lay.rect(ux + 20, bt - 5, 12, 5, 'D', 2.6, hgt=0.6)                           # the cash box
        lay.hline(ux + 20, bt - 5, 12, 'D', 3.8)
        lay.px(ux + 25, bt - 3, 'L', 3.6)
        # three slim posts, the canopy with the green fascia and its lettering, two bulbs under it
        for px_ in (x0 + 2, (x0 + x1) // 2, x1 - 4):
            K.cyl(lay, px_, cy0 + 10, 3, ct - cy0 - 10, 'S', 2.6, hgt=0.7)
        lay.rect(x0 - 3, cy0, x1 - x0 + 6, 10, 'E', 2.4, hgt=0.6)
        lay.hline(x0 - 3, cy0, x1 - x0 + 6, 'E', 3.8, hgt=0.8)
        lay.hline(x0 - 3, cy0 + 9, x1 - x0 + 6, 'E', 1.2)
        lay.hline(x0 - 3, cy0 + 10, x1 - x0 + 6, 'I', 1.0)                            # the canopy's shadow line
        K.text(lay, 'ERFRISCHUNGEN', (x0 + x1) / 2, cy0 + 3, 'P', 6.6, center=True)
        for bx in (x0 + 30, x1 - 54):
            lay.rect(bx, cy0 + 10, 1, 3, 'S', 3.4)
            lay.rect(bx - 2, cy0 + 13, 5, 2, 'E', 2.8)
            lay.rect(bx - 1, cy0 + 15, 3, 2, 'L', 5.0, emis=True)
            self.light('buffet_bulb_%d' % bx, (bx, cy0 + 16), 'warm', 0.85, 72, height=12, pool=0.5, pool_w=12)
        # the menu board hanging from the canopy: four lines, a gap row between them
        mx, my, mw, mh = x1 - 44, cy0 + 11, 38, 21
        for hx in (mx + 4, mx + mw - 5):
            lay.vline(hx, cy0 + 10, my - cy0 - 10, 'S', 3.0)
        lay.rect(mx, my, mw, mh, 'D', 2.0, hgt=0.4)
        lay.hline(mx, my, mw, 'D', 3.4)
        lay.rect(mx + 1, my + 1, mw - 2, mh - 2, 'I', 1.1, hgt=0.3)                   # the slate
        for i, (s_, p_) in enumerate((('KAFFEE', '20'), ('BRÜHE', '25'), ('WURST', '60'))):
            K.text(lay, s_, mx + 3, my + 3 + i * 6, 'P', 6.4 - (i % 2) * 0.3)
            K.text(lay, p_, mx + mw - 3 - K.tw(p_), my + 3 + i * 6, 'L', 4.8)
        self.counter()
        if roster:
            self.roster(roster)
        self.counter_box = (x0, ct - 10, x1, 292)

    def counter(self):
        """The buffet counter and what stands on it -- also cut out as the y-sorted prop counter_front (the buffet
        woman stands behind it, the walk band runs in front of it)."""
        lay = self.lay
        x0, x1 = L.BUFFET
        ct = L.COUNTER_TOP
        # zinc top, panelled wooden front (the front is also cut out as a y-sorted prop)
        lay.rect(x0 + 2, ct, x1 - x0 - 4, 3, 'S', 4.4, hgt=0.9)
        lay.hline(x0 + 2, ct, x1 - x0 - 4, 'S', 5.8, hgt=1.0)
        K.grain(lay, x0 + 3, ct + 3, x1 - x0 - 6, 292 - ct - 3, 'D', 2.4, seed=111, amp=0.28)
        for px_ in range(x0 + 6, x1 - 10, 22):
            K.recess(lay, px_, ct + 7, 18, 19, 'D', 2.0, shadow=1.2, light=3.4)
        lay.rect(x0 + 3, 290, x1 - x0 - 6, 2, 'D', 1.2)
        # what stands on the counter: cups and saucers, a plate of rolls, sugar, a newspaper; Marta's roster
        for cx in (x0 + 18, x0 + 30, x1 - 22):
            lay.rect(cx, ct - 4, 4, 4, 'P', 6.2, hgt=0.6)
            lay.hline(cx - 1, ct - 1, 6, 'P', 5.2)
            lay.px(cx + 4, ct - 3, 'P', 5.0)
        lay.rect(x0 + 44, ct - 3, 16, 2, 'P', 6.4, hgt=0.5)
        for k in range(4):
            lay.rect(x0 + 45 + k * 4, ct - 5, 3, 2, 'L', 3.0, hgt=0.6)                   # rolls
        lay.rect(x0 + 64, ct - 4, 5, 4, 'P', 6.6, hgt=0.6)                                # sugar bowl
        lay.rect(x0 + 74, ct - 2, 12, 2, 'P', 5.2, hgt=0.3)                               # folded paper
        K.pseudo_text(lay, x0 + 75, ct - 2, 10, 1, 'I', 1.2, seed=7)

    def roster(self, line: str):
        """Marta's duty roster on the counter (art gate choice c4d_choose): „Linie 3“ (named) / „Linie 74“."""
        lay = self.lay
        rx, ry = 292, L.COUNTER_TOP - 9
        lay.rect(rx, ry, 18, 9, 'P', 6.6, hgt=0.4)
        lay.hline(rx, ry, 18, 'P', 7.0)
        lay.vline(rx + 17, ry + 1, 8, 'P', 4.8)
        K.pseudo_text(lay, rx + 2, ry + 2, 7, 3, 'I', 1.2, seed=3 if line == '3' else 4, gap=2)
        K.text(lay, line, rx + 16 - K.tw(line), ry + 2, 'R', 2.2)
        lay.rect(rx - 4, ry + 5, 3, 4, 'D', 2.0, hgt=0.4)                               # her gloves on it

    # ------------------------------------------------------------------ the kiosk
    def kiosk(self):
        """The newspaper kiosk: green boards, the roof with „Zeitungen“, the day's headline on a board above the
        window („Ein Winter des Friedens“ -- every paper prints it), the kiosk woman in her lit window (a life
        strip), papers clipped at the sides showing the same big W in three inks, the card „vergriffen“ on its hook,
        magazines in the racks below."""
        lay = self.lay
        x0, x1 = L.KIOSK
        top = 230
        K.grain(lay, x0, top, x1 - x0, 292 - top, 'E', 1.8, seed=121, amp=0.25)
        lay.vline(x0, top, 292 - top, 'E', 3.0)
        lay.vline(x1 - 1, top, 292 - top, 'E', 1.0)
        lay.rect(x0 - 3, top - 8, x1 - x0 + 6, 8, 'E', 2.6, hgt=0.8)                       # roof
        lay.hline(x0 - 3, top - 8, x1 - x0 + 6, 'E', 3.8, hgt=0.9)
        lay.hline(x0 - 3, top - 1, x1 - x0 + 6, 'I', 1.0)
        sw = K.tw('ZEITUNGEN') + 4
        lay.rect((x0 + x1) // 2 - sw // 2, top - 7, sw, 6, 'P', 6.4, hgt=0.5)
        K.text(lay, 'ZEITUNGEN', (x0 + x1) / 2, top - 6, 'E', 1.4, center=True)
        # the headline board above the window
        hx0, hw = x0 + 4, x1 - x0 - 8
        lay.rect(hx0, top + 2, hw, 15, 'P', 6.6, hgt=0.4)
        lay.hline(hx0, top + 2, hw, 'P', 7.0)
        lay.hline(hx0, top + 16, hw, 'P', 4.8)
        K.text(lay, 'EIN WINTER', (x0 + x1) / 2, top + 4, 'I', 0.8, center=True)
        K.text(lay, 'DES FRIEDENS', (x0 + x1) / 2, top + 10, 'I', 0.8, center=True)
        # the sales window (lit; the kiosk woman is a life strip), the sill with stacked papers
        wx0, wx1 = x0 + 10, x1 - 10
        wy0, wh = top + 19, 20
        lay.rect(wx0 - 1, wy0 - 1, wx1 - wx0 + 2, wh + 1, 'E', 1.0)
        lay.vgrad(wx0, wy0, wx1 - wx0, wh, 'L', 2.2, 1.6, emis=True)
        lay.rect(wx0, wy0, wx1 - wx0, 2, 'L', 1.2, emis=True)
        lay.rect(wx0 - 2, wy0 + wh, wx1 - wx0 + 4, 3, 'D', 3.6, hgt=0.8)
        lay.hline(wx0 - 2, wy0 + wh, wx1 - wx0 + 4, 'D', 4.4)
        self.kiosk_win = (wx0, wy0, wx1 - wx0, wh)
        for k in range(5):                                                                 # stacked papers
            lay.rect(wx0 + 2 + k * 8, wy0 + wh - 3, 7, 3, 'P', 5.4 + (k % 2) * 0.8, hgt=0.5)
            lay.hline(wx0 + 2 + k * 8, wy0 + wh - 2, 7, 'I', 1.6)
        lay.vline(wx1 - 4, wy0, 7, 'S', 3.4)                                               # the hook ...
        lay.rect(wx1 - 8, wy0 + 7, 8, 5, 'P', 7.0, emis=True)                               # ... and the card
        lay.hline(wx1 - 7, wy0 + 9, 6, 'R', 2.8, emis=True)
        # papers clipped on strings at both sides: the same headline, a big W in three inks
        for (px0, inks) in ((x0 + 1, (('I', 0.8), ('R', 2.4), ('B', 1.6))),
                            (wx1 + 1, (('B', 1.6), ('I', 0.8), ('R', 2.4)))):
            lay.hline(px0, wy0 - 1, 8, 'S', 2.6)
            for i, (ir, it) in enumerate(inks):
                py = wy0 + i * 8
                lay.rect(px0, py, 8, 7, 'P', 6.2 - (i % 2) * 0.6, hgt=0.4)
                lay.hline(px0, py, 8, ir, it)                                               # the masthead
                K.text(lay, 'W', px0 + 1, py + 2, ir, it)
        # magazines in the racks below
        for k in range(3):
            rx0 = x0 + 3 + k * 18
            K.recess(lay, rx0, top + 44, 17, 17, 'E', 1.2, shadow=0.8, light=2.2)
            for j in range(2):
                lay.rect(rx0 + 2, top + 46 + j * 8, 13, 6, ('P', 'R', 'B')[(k + j) % 3],
                         (5.8, 2.8, 2.6)[(k + j) % 3], hgt=0.4)
                lay.hline(rx0 + 2, top + 46 + j * 8, 13, ('P', 'R', 'B')[(k + j) % 3],
                          (6.6, 3.4, 3.0)[(k + j) % 3])
        self.light('kiosk_inside', ((wx0 + wx1) / 2, wy0 + 10), 'warm', 0.6, 60, height=8, pool=0.3)

    # ------------------------------------------------------------------ porters' carts, benches, signs
    def carts(self):
        lay = self.lay
        x0, x1 = L.CARTS
        for (cx, n) in ((x0, 3), (x0 + 30, 2)):
            lay.rect(cx, 278, 22, 4, 'D', 3.0, hgt=0.6)                                    # the platform
            lay.hline(cx, 278, 22, 'D', 4.2, hgt=0.7)
            lay.line(cx + 22, 278, cx + 28, 262, 'S', 3.4)                                 # the shaft
            wheel(lay, cx + 5, 286, 5, spokes=6, ramp_centre='S', ctone=1.8)
            wheel(lay, cx + 17, 286, 5, spokes=6, ramp_centre='S', ctone=1.8)
            yy = 278
            for k in range(n):                                                             # suitcases, a trunk
                hh = (8, 6, 7)[k]
                ww = (18, 14, 16)[k]
                ramp, t = (('D', 2.6), ('B', 2.0), ('R', 1.6))[(k + cx) % 3]
                lay.rect(cx + 2 + k, yy - hh, ww, hh, ramp, t, hgt=0.6)
                lay.hline(cx + 2 + k, yy - hh, ww, ramp, t + 1.0, hgt=0.7)
                lay.rect(cx + 2 + k + ww // 2 - 2, yy - hh - 1, 4, 1, 'I', 1.2)
                lay.rect(cx + 4 + k, yy - hh + 2, 3, 2, 'P', 6.2)                         # labels
                yy -= hh
        # a bench in front of the gap with a forgotten newspaper
        bx = 548
        lay.rect(bx, 280, 30, 2, 'D', 3.4, hgt=0.7)
        lay.rect(bx, 270, 30, 2, 'D', 3.0, hgt=0.6)
        lay.rect(bx, 274, 30, 2, 'D', 2.8, hgt=0.6)
        for lx in (bx + 2, bx + 26):
            lay.rect(lx, 282, 2, 10, 'S', 2.6, hgt=0.6)
            lay.rect(lx, 268, 2, 14, 'S', 2.4, hgt=0.5)
        lay.rect(bx + 6, 277, 10, 3, 'P', 5.8, hgt=0.4)
        K.pseudo_text(lay, bx + 7, 278, 8, 1, 'I', 1.4, seed=17)

    def fence(self):
        """The Corridor fence at the end of platform K (the blocker): iron bars, a locked gate, the sign."""
        lay = self.lay
        x0, x1 = L.FENCE
        for x in range(x0, x1 + 2, 4):
            K.cyl(lay, x, 188, 2, 104, 'S', 2.6, hgt=0.6)
            lay.rect(x, 185, 2, 3, 'S', 3.8)
            lay.px(x, 184, 'S', 4.6)
        for yy in (196, 240, 284):
            lay.rect(x0 - 2, yy, x1 - x0 + 6, 3, 'S', 3.0, hgt=0.8)
            lay.hline(x0 - 2, yy, x1 - x0 + 6, 'S', 4.4)
        lay.rect(x0 + 6, 248, 10, 8, 'I', 1.4, hgt=0.8)                                    # the padlock box
        lay.rect(x0 + 9, 256, 4, 5, 'S', 3.8, hgt=0.9)
        K.snowcap(lay, x0 - 2, 196, x1 - x0 + 6, 1, seed=21, ramp='V', tone=3.0)
        # the enamel sign wired to the bars above head height, readable whole from the platform
        sw = K.tw('DURCHGANG') + 4
        sx0, sy0 = (x0 + x1) // 2 - sw // 2, 214
        for hx in (sx0 + 3, sx0 + sw - 4):                                                   # the wires
            lay.px(hx, sy0 - 1, 'S', 4.0)
        sign(lay, sx0, sy0, sw, 16, '', ramp='P', face=6.2, ink=('R', 2.2))
        K.text(lay, 'KEIN', sx0 + sw / 2, sy0 + 3, 'R', 2.4, center=True)
        K.text(lay, 'DURCHGANG', sx0 + sw / 2, sy0 + 9, 'I', 0.8, center=True)

    def lamps(self):
        """Sodium lamps hanging from the vault on long rods (enamel shades, glowing bulbs)."""
        lay = self.lay
        for i, x in enumerate(L.LAMPS_A):
            y = L.LAMP_Y
            lay.vline(x, 0, y - 4, 'S', 2.2 + (i % 2) * 0.3, hgt=0.4)
            lay.rect(x - 1, y - 6, 3, 3, 'S', 3.0, hgt=0.6)
            for k in range(5):                                                               # the shade
                lay.hline(x - 2 - k, y - 3 + k, 5 + 2 * k, 'E', 2.0 + k * 0.2, hgt=0.7)
            lay.hline(x - 6, y + 2, 13, 'P', 6.0, emis=True)                                # white inside rim
            lay.rect(x - 2, y + 1, 5, 3, 'L', 5.0, emis=True)                                # the bulb
            lay.px(x, y + 2, 'L', 5.6, emis=True)
            self.light('sodium_%d' % i, (x, y + 6), 'warm', 1.05, 150, height=60, pool=0.9, pool_w=18,
                       pool_spread=0.9, pool_depth=52)

    def clock(self):
        """The station clock under the glass roof at 20.31 -- dial baked here, the hands are an actor
        (scripts/levels/c4p2/station_clock.gd); the enamel plate „Ortszeit Karsk + 2“ beside it."""
        lay = self.lay
        cx, cy = L.CLOCK
        lay.vline(cx, 0, cy - 9, 'S', 2.4, hgt=0.5)
        lay.rect(cx - 2, cy - 11, 5, 3, 'S', 3.4, hgt=0.7)
        d = K.disc(19)
        lay.put(d, cx - 9, cy - 9, 'I', 1.0, hgt=0.8)
        lay.put(K.erode(d, 1), cx - 9, cy - 9, 'P', 7.0, hgt=0.6, emis=True)
        for k in range(12):                                                                  # hour marks
            a = k * math.pi / 6
            for rr in ((6.5, 7.5) if k % 3 else (5.5, 6.5, 7.5)):
                lay.px(cx + int(round(math.sin(a) * rr)), cy - int(round(math.cos(a) * rr)), 'I', 0.8, emis=True)
        lay.px(cx, cy, 'I', 0.8, emis=True)
        pw = K.tw('KARSK + 2') + 7
        px0, py0 = cx + 12, cy - 9
        lay.line(px0 + 5, py0, px0 + 5, py0 - 6, 'S', 2.6)                                  # two hangers
        lay.line(px0 + pw - 6, py0, px0 + pw - 6, py0 - 6, 'S', 2.6)
        sign(lay, px0, py0, pw, 16, '', ramp='B', face=2.0)
        K.text(lay, 'ORTSZEIT', px0 + pw / 2, py0 + 3, 'P', 6.4, center=True)
        K.text(lay, 'KARSK + 2', px0 + pw / 2, py0 + 9, 'P', 5.8, center=True)
        self.light('clock_face', (cx, cy), 'white', 0.2, 30, height=6)

    def signs(self):
        lay = self.lay
        # the platform letter, hanging from the vault (both faces)
        for (x, y) in ((266, 150), (606, 150)):
            lay.vline(x + 7, 0, y, 'S', 2.0)
            sign(lay, x, y, 15, 14, 'K', ramp='B', face=2.2, font='57')
        # the Accord's cloth banner hung under the vault over the barrier (C3 station continuity)
        bx0, bx1, by = 66, 150, 140
        for xx in (bx0 + 2, bx1 - 3):
            lay.vline(xx, 0, by, 'S', 1.8)
        lay.rect(bx0, by, bx1 - bx0, 18, 'R', 2.2, hgt=0.3)
        for yy in range(by, by + 18, 3):
            lay.hline(bx0, yy, bx1 - bx0, 'R', 1.9)
        lay.hline(bx0, by, bx1 - bx0, 'R', 3.0)
        K.text(lay, 'DREI KORRIDORE', (bx0 + bx1) / 2, by + 3, 'P', 6.2, center=True)
        K.text(lay, 'EIN FRIEDEN', (bx0 + bx1) / 2, by + 10, 'P', 5.6, center=True)
        for xx in range(bx0, bx1, 4):                                                  # fringe
            lay.px(xx, by + 18, 'L', 2.6)

    # ------------------------------------------------------------------ ambient + build
    def ambient(self):
        lay = self.lay
        f = np.zeros((H, W), np.float32)
        ys = np.arange(H, dtype=np.float32)[:, None]
        xs = np.arange(W, dtype=np.float32)[None, :]
        f += -0.5 * np.clip((150 - ys) / 150, 0, 1)                    # the vault zone stays dark
        f += -0.35 * np.clip((ys - 312) / 20, 0, 1)
        f += -0.3 * np.clip((xs - 860) / 58, 0, 1)                      # toward the fence
        f[150:268, L.LOCO[0] - 10:L.TENDER[1]] -= 0.12                   # the engine stands a little in its shadow
        f[lay.emis] = 0
        lay.amb_field(f)

    def scene_lights(self):
        return [
            {'name': 'hall_end', 'pos': (-60.0, 200.0), 'kind': 'cold', 'energy': 0.75, 'radius': 300, 'height': 60},
            {'name': 'vault_glow', 'pos': (460.0, -120.0), 'kind': 'white', 'energy': 0.22, 'radius': 700,
             'height': 140},
        ]

    def build(self):
        """Paints back to front and keeps an owner map (which painter set each pixel last): the life strips clip to
        the pixels of their own object, so a figure never spills onto what stands in front of it."""
        steps = [('track', self.track_k), ('loco', self.loco), ('tender', self.tender), ('courier', self.courier),
                 ('gap', self.gap), ('diner', self.diner), ('sleeper', self.sleeper), ('platform', self.platform),
                 ('booth', self.booth), ('board', self.board), ('baggage', self.baggage),
                 ('buffet', lambda: self.buffet(self.cfg.get('roster'))), ('kiosk', self.kiosk),
                 ('carts', self.carts), ('fence', self.fence), ('lamps', self.lamps), ('clock', self.clock),
                 ('signs', self.signs)]
        self.owner = np.full((H, W), -1, np.int16)
        self.owner_ids = {}
        for i, (nm, fn) in enumerate(steps):
            rid0, tone0 = self.lay.rid.copy(), self.lay.tone.copy()
            fn()
            changed = (self.lay.rid != rid0) | (self.lay.tone != tone0)
            self.owner[changed] = i
            self.owner_ids[nm] = i
        self.ambient()
        return self.lay

    def owned(self, name: str) -> np.ndarray:
        return self.owner == self.owner_ids[name]

    def all_lights(self):
        return self.scene_lights() + self.lights


def bake_station(cfg: dict | None = None):
    st = Station(cfg)
    st.build()
    lights = st.all_lights()
    F = K.light_fields(st.lay, lights)
    K.add_pools(F, lights, FEET - 30, H, W)
    K.resolve(st.lay, F, exposure=0.93)
    st.F = F
    return st


# =========================================================================== parallax layers
def sky_layer(w=670, h=270):
    """Night over Berlin seen through the open end of the hall: low cloud lit orange-brown by the city."""
    lay = K.tlayer(w, h, 'st_sky', 'A')
    ys = np.arange(h, dtype=np.float32)[:, None] / h
    nz = K.periodic_noise(w, h, 80, 16, 5, octaves=4)
    t = 0.4 + ys * 2.6 + (nz - 0.5) * 0.7
    lay.put(np.ones((h, w), bool), 0, 0, 'G', np.clip(t, 0, 4.2).astype(np.float32), flat=False)
    glow = np.exp(-((ys - 0.78) / 0.12) ** 2) * (nz > 0.45)
    lay.put(glow > 0.55, 0, 0, 'L', 1.2, flat=False)
    lay.put((glow > 0.8) & (nz > 0.6), 0, 0, 'L', 1.8, flat=False)
    K.resolve(lay, None, exposure=1.0)
    return lay


def city_layer(w=690, h=220):
    """The night city outside: blocks with lit windows, chimneys, a mast with a red light, signal lights of the
    tracks leading out of the hall (layer coordinates: y 0 = world y 60)."""
    lay = K.tlayer(w, h, 'st_city', 'A')
    rng = np.random.default_rng(1964)
    ground = h - 20
    x = 0
    while x < w:
        bw = int(rng.integers(40, 110))
        bh = int(rng.integers(50, 120))
        top = ground - bh
        lay.rect(x, top, bw, bh, 'N', 1.6 + rng.random() * 0.6)
        lay.hline(x, top, bw, 'N', 2.8)
        for cx in range(x + 4, x + bw - 4, int(rng.integers(14, 26))):          # chimneys + smoke-less tops
            if rng.random() < 0.5:
                lay.rect(cx, top - 6, 3, 6, 'N', 2.0)
        for wy in range(top + 6, ground - 6, 9):
            for wx in range(x + 4, x + bw - 4, 7):
                r = rng.random()
                if r < 0.16:
                    lay.rect(wx, wy, 3, 4, 'L', 3.0 + rng.random() * 1.2, emis=True)
                elif r < 0.2:
                    lay.rect(wx, wy, 3, 4, 'G', 3.4, emis=True)
        x += bw + int(rng.integers(0, 8))
    for (mx, mh) in ((180, 150), (520, 120)):                                      # radio masts, red lights
        top = ground - mh
        for y in range(top, ground):
            lay.px(mx, y, 'N', 2.4)
            if (y - top) % 6 == 0:
                lay.hline(mx - 1, y, 3, 'N', 2.2)
        lay.px(mx, top - 1, 'R', 4.0, emis=True)
        lay.px(mx, top + mh // 2, 'R', 3.6, emis=True)
    lay.rect(0, ground, w, h - ground, 'N', 1.2)
    for sx in range(10, w, 60):                                                      # track signals far out
        lay.vline(sx, ground - 10, 10, 'N', 2.0)
        lay.px(sx, ground - 11, ('E', 'R', 'L')[sx % 3], (4.0, 4.0, 4.4)[sx % 3], emis=True)
    K.resolve(lay, None, exposure=1.0)
    return lay


def hall_layer(w=770, h=262):
    """The hall's shell (parallax 0.4, unlit, baked).  The glass barrel vault from the smoke lantern on its crown
    (overhead, y 0..13) down to the far side's springing line (y 150): purlins closer together toward the far side,
    glazing bars, panes clear (the night above), snowed over (lit from below), sooted under the lantern or boarded
    since the war, one broken with icicles; the great lattice arches every 118 px -- wide overhead, narrow at the far
    wall, their lower chords catching the sodium light, gusset plates at the purlins, cast-iron consoles at their feet;
    cables sagging between them, pigeons on the purlins, the warm glow of the lamp rows on the lower vault and the
    light bounced up from the platform overhead.  Below: the far brick wall with tall arched windows (open to the city
    layer), the cornice, the lettering band; at the left the end screen of the vault, its lower part open."""
    lay = K.tlayer(w, h, 'st_hall', 'A')
    rng = np.random.default_rng(401)
    spring = L.VAULT_SPRING
    RAMPS = ['G', 'V', 'N', 'D', 'L', 'S', 'I', 'P', 'K']
    lab = np.full((h, w), -1, np.int8)
    ton = np.zeros((h, w), np.float32)

    def paint(mask, ramp, tone):
        lab[mask] = RAMPS.index(ramp)
        ton[mask] = tone if np.isscalar(tone) else np.asarray(tone, np.float32)[mask]

    ys = np.arange(h, dtype=np.float32)[:, None] + np.zeros((1, w), np.float32)
    xs = np.arange(w, dtype=np.float32)[None, :] + np.zeros((h, 1), np.float32)
    depth = np.clip(ys / spring, 0, 1)                         # 0 overhead .. 1 at the far springing line
    rows_of_lamps = 0.5 + 0.5 * np.cos((xs - 64) / 150.0 * 2 * np.pi)
    glow = np.clip((depth - 0.42) / 0.58, 0, 1) ** 1.4 * (0.55 + 0.45 * rows_of_lamps)
    bounce = np.clip(1 - depth / 0.4, 0, 1) * 0.5
    litv = 0.9 * np.exp(-((depth - 0.62) / 0.26) ** 2)               # the part of the barrel facing the lamps
    thr = pg.bayer(w, h, 3, 1, 4)
    snow_n = pg.value_noise(w, h, 26, 405, octaves=3)
    fine = pg.value_noise(w, h, 4, 406, octaves=2)
    # ---- purlin rows (perspective of the barrel): the lantern takes the crown, then wide rows close overhead
    lantern = 13
    purl = []
    y = float(lantern + 1)
    step = 13.0
    while y < spring - 3:
        purl.append(int(y))
        y += step
        step = max(4.0, step * 0.87)
    purl.append(spring - 2)
    bars = list(range(2, w, 8))
    vault = ys < spring
    # ---- the panes
    soot_len = 8 + 44 * pg.value_noise(w, 1, 5, 407, octaves=2)[0]
    for i in range(len(purl) - 1):
        y0_, y1_ = purl[i] + (2 if purl[i] < 60 else 1), purl[i + 1]
        if y1_ <= y0_:
            continue
        for j in range(len(bars) - 1):
            x0_, x1_ = bars[j] + 1, bars[j + 1]
            sl = (slice(y0_, y1_), slice(x0_, x1_))
            m = np.zeros((h, w), bool)
            m[sl] = True
            u = rng.random()
            yc = (y0_ + y1_) // 2
            d = depth[yc, 0]
            sooty = y0_ < lantern + soot_len[min(w - 1, x0_)]
            if u < 0.035 and 20 < y0_ < 120:                                   # boarded up since the war
                t = 1.3 + (fine[sl] - 0.5) * 0.6
                paint(m, 'D', np.pad(t, ((y0_, h - y1_), (x0_, w - x1_))))
                for py in range(y0_ + 1, y1_, 3):
                    lab[py, x0_:x1_] = RAMPS.index('D')
                    ton[py, x0_:x1_] = 0.8
                lab[y0_ + 1, x0_ + 1] = RAMPS.index('S')
                ton[y0_ + 1, x0_ + 1] = 2.8
                continue
            if u < 0.047 and 30 < y0_ < 110:                                   # broken: the night, icicles
                paint(m, 'N', 0.25)
                lab[y0_, x0_:x1_] = RAMPS.index('G')
                ton[y0_, x0_:x1_] = 3.0
                for xx in range(x0_, x1_, 2):
                    ln = int(rng.integers(1, 4))
                    lab[y0_:y0_ + ln, xx] = RAMPS.index('V')
                    ton[y0_:y0_ + ln, xx] = 2.4
                continue
            snowy = snow_n[yc, x0_] > 0.56
            if sooty:
                t = 1.4 + 0.6 * fine[sl] + (0.5 if snowy else 0.0)
                paint(m, 'N', np.pad(t, ((y0_, h - y1_), (x0_, w - x1_))))
            elif snowy:
                t = 2.4 + 0.6 * d + 1.2 * bounce[sl] + 0.9 * litv[sl] + (fine[sl] - 0.5) * 0.5
                tt = np.pad(t, ((y0_, h - y1_), (x0_, w - x1_)))
                paint(m, 'G', tt)
                warm = m & (glow * 0.75 > thr + 0.12)
                paint(warm, 'L', 1.1 + 0.9 * glow)
                lab[y1_ - 1, x0_:x1_] = RAMPS.index('V') if d < 0.6 else RAMPS.index('G')
                ton[y1_ - 1, x0_:x1_] = 0.6 if d < 0.6 else 3.6                  # snow slid to the lower edge
            else:
                t = 1.3 + 0.3 * d + 1.1 * bounce[sl] + 1.0 * litv[sl] + \
                    ((np.arange(y1_ - y0_)[:, None] + x0_) % 9 == 0) * 0.3
                tt = np.pad(t, ((y0_, h - y1_), (x0_, w - x1_)))
                paint(m, 'G', tt)
                refl = m & (glow * 0.55 > thr + 0.3)
                paint(refl, 'L', 1.0 + 0.8 * glow)                              # the lamps mirrored in the glass
    # ---- glazing bars and purlins
    for bx in bars:
        col = vault[:, bx] & (ys[:, 0] >= lantern)
        m = np.zeros((h, w), bool)
        m[col, bx] = True
        paint(m, 'S', 0.9 + 1.2 * glow)
    for k, py in enumerate(purl):
        d = py / spring
        th = 2 if d < 0.45 else 1
        m = np.zeros((h, w), bool)
        m[py:py + th, :] = True
        paint(m, 'S', 1.3 + 0.3 * d)
        lit = np.zeros((h, w), bool)
        lit[py + th - 1, :] = True
        paint(lit & (glow > 0.25) & (k % 2 == 0), 'L', 1.3 + 1.1 * glow)       # undersides catch the lamps
        paint(lit & (glow > 0.25) & (k % 2 == 1), 'S', 2.4 + 1.2 * glow)
        paint(lit & (glow <= 0.25), 'S', 2.2 + 1.6 * bounce)
    # ---- the smoke lantern on the crown: louvres, the night between them, snow on the ledges
    m = np.zeros((h, w), bool)
    m[0:lantern, :] = True
    paint(m, 'N', 0.3)
    for lx_ in range(0, w, 4):
        mm = np.zeros((h, w), bool)
        mm[1:lantern - 1, lx_:lx_ + 2] = True
        paint(mm, 'S', 1.2)
        mm[:] = False
        mm[lantern - 2, lx_:lx_ + 2] = True
        paint(mm, 'S', 2.6)
    for ry in (0, 6, lantern - 1):
        mm = np.zeros((h, w), bool)
        mm[ry, :] = True
        paint(mm, 'S', 2.2)
    for ry in (5, 11):
        for xx in range(0, w):
            if fine[ry, xx] > 0.45:
                lab[ry, xx] = RAMPS.index('V')
                ton[ry, xx] = 0.8 + fine[ry, xx]
    mm = np.zeros((h, w), bool)
    mm[lantern:lantern + 2, :] = True
    paint(mm, 'S', 2.0)
    # ---- the lattice arches: wide overhead, narrow at the far wall; lower chord lit, upper chord dark
    for rx in range(46, w + 60, 118):
        for yy in range(0, spring + 1):
            d = yy / spring
            half = int(round(10 - 7 * d))
            a, b = rx - half, rx + half
            if b < 0 or a >= w:
                continue
            g = float(glow[yy, min(w - 1, max(0, rx))])
            lv = float(litv[yy, 0])
            for xx in range(max(0, a), min(w, b + 1)):
                lab[yy, xx] = RAMPS.index('S')
                ton[yy, xx] = 1.2 + 0.8 * g + 0.8 * lv
            per = max(4, 2 * half)
            ph = (yy % per) / per
            seg = (yy // per) % 2
            dxp = a + 1 + int(round((ph if seg == 0 else 1 - ph) * (2 * half - 2)))
            for xx in (dxp, dxp + (1 if half > 6 else 0)):
                if 0 <= xx < w:
                    lab[yy, xx] = RAMPS.index('S')
                    ton[yy, xx] = 2.8 + 1.2 * g + 0.6 * lv
            warm_chord = g > 0.12 or lv > 0.35
            for xx, (rp, tt) in ((a, ('L' if warm_chord else 'S',
                                      2.6 + 1.8 * g + 0.9 * lv if warm_chord else 3.0 + 1.4 * bounce[yy, 0])),
                                 (a + 1, ('S', 2.2 + 1.0 * g)), (b, ('S', 1.8))):
                if 0 <= xx < w:
                    lab[yy, xx] = RAMPS.index(rp)
                    ton[yy, xx] = tt
        for py in purl:                                                        # gusset plates at the purlins
            d = py / spring
            half = int(round(10 - 7 * d))
            for xx in range(max(0, rx - half - 1), min(w, rx + half + 2)):
                for yy_ in (py - 1, py, py + 1):
                    if 0 <= yy_ < spring:
                        lab[yy_, xx] = RAMPS.index('S')
                        ton[yy_, xx] = 2.8 + 1.4 * float(glow[yy_, min(w - 1, max(0, rx))])
            if 0 <= rx < w:
                lab[py, rx] = RAMPS.index('S')
                ton[py, rx] = 4.4
    # ---- cables sagging between the arches, pigeons on the purlins
    for (cy0, sag, tone) in ((86, 7, 0.7), (101, 5, 0.9)):
        for rx in range(46, w, 118):
            a, b = rx + 4, rx + 114
            for xx in range(a, min(w, b)):
                u = (xx - a) / float(b - a) * 2 - 1
                yy = int(round(cy0 + sag * (1 - u * u)))
                lab[yy, xx] = RAMPS.index('I')
                ton[yy, xx] = tone
                if glow[yy + 1, xx] > 0.2:
                    lab[yy + 1, xx] = RAMPS.index('L')
                    ton[yy + 1, xx] = 1.6 + glow[yy + 1, xx]
    # the lamps over the far platforms: smaller, deeper in the hall, each with its glow on the glass behind
    for (ly, step, off, rod) in ((116, 64, 20, 14), (132, 48, 6, 10)):
        for lx_ in range(off, w, step):
            if (lx_ - 46) % 118 < 12 or (lx_ - 46) % 118 > 106:
                continue
            for yy in range(ly - 7, ly + 6):
                for xx in range(lx_ - 7, lx_ + 8):
                    dd = ((xx - lx_) / 7.0) ** 2 + ((yy - ly - 1) / 6.0) ** 2
                    if 0 <= xx < w and dd < 1 and (xx + yy) % 2 == 0 and lab[yy, xx] != RAMPS.index('S'):
                        lab[yy, xx] = RAMPS.index('L')
                        ton[yy, xx] = 1.4 + (1 - dd) * 1.2
            for yy in range(ly - rod, ly - 1):
                lab[yy, lx_] = RAMPS.index('S')
                ton[yy, lx_] = 1.6
            for xx in range(lx_ - 2, lx_ + 3):
                lab[ly - 1, xx] = RAMPS.index('S')
                ton[ly - 1, xx] = 2.6
            lab[ly, lx_ - 1:lx_ + 2] = RAMPS.index('L')
            ton[ly, lx_ - 1:lx_ + 2] = 4.6
    for _ in range(18):
        py = purl[int(rng.integers(3, len(purl) - 3))]
        px_ = int(rng.integers(8, w - 8))
        if (px_ - 46) % 118 < 14 or (px_ - 46) % 118 > 104:
            continue
        for (dx, dy, rp, tt) in ((0, -2, 'S', 1.0), (1, -2, 'S', 1.2), (2, -2, 'S', 0.9), (-1, -3, 'S', 1.4),
                                 (0, -1, 'V', 0.6), (1, -1, 'S', 1.6), (2, -1, 'I', 0.8)):
            lab[py + dy, px_ + dx] = RAMPS.index(rp)
            ton[py + dy, px_ + dx] = tt
    # ---- the far wall: brick lit warm under the vault, the cornice, arched windows, the lettering band
    wall_top = spring
    for r_, nm in enumerate(RAMPS):
        mm = lab == r_
        if mm.any():
            lay.put(mm, 0, 0, nm, ton, flat=False)
    K.bricks(lay, 0, wall_top, w, h - wall_top, 'K', 1.7, seed=404, course=3, length=7, joint=-0.5, var=0.3)
    wy = np.arange(wall_top, h, dtype=np.float32)[:, None]
    shade = 0.9 * np.clip(1 - (wy - wall_top) / 40.0, 0, 1) * (0.6 + 0.4 * rows_of_lamps[0:1, :]) \
        - 0.4 * np.clip((wy - wall_top - 60) / 50.0, 0, 1)
    sub = lay.tone[wall_top:h, :]
    sub += np.where(lay.rid[wall_top:h, :] >= 0, shade, 0).astype(np.float32)
    lay.rect(0, wall_top, w, 5, 'P', 2.4, hgt=0.6)                              # the cornice
    lay.hline(0, wall_top, w, 'L', 3.0)
    lay.hline(0, wall_top + 5, w, 'K', 0.8)
    for rx in range(46, w + 60, 118):                                           # the arches' cast-iron consoles
        for yy_ in range(spring - 4, spring + 7):
            for xx in range(rx - 7, rx + 8):
                if 0 <= xx < w and abs(xx - rx) <= 7 - max(0, yy_ - spring - 1):
                    lay.px(xx, yy_, 'S', 1.6 if yy_ > spring - 2 else 3.2, hgt=0.8)
        if 0 <= rx < w:
            lay.px(rx, spring - 4, 'L', 3.6)
    win_m = K.arch_mask(22, 60, 11)
    for wx in range(70, w, 104):
        x0 = wx + 30
        if x0 + 22 >= w:
            break
        y0 = wall_top + 18
        lay.rect(x0 - 3, y0 - 3, 28, 66, 'P', 1.9, hgt=0.6)
        lay.hline(x0 - 3, y0 - 3, 28, 'P', 3.0)
        lay.erase_mask(win_m, x0, y0)
        for mx in (x0 + 7, x0 + 14):
            for y in range(y0 + 4, y0 + 60):
                lay.px(mx, y, 'S', 1.4)
        for my in (y0 + 22, y0 + 40):
            lay.hline(x0, my, 22, 'S', 1.4)
    for px_ in range(18, w, 52):
        lay.rect(px_, wall_top + 6, 6, h - wall_top - 6, 'K', 2.3, hgt=0.6)
        lay.vline(px_, wall_top + 6, h - wall_top - 6, 'K', 3.0)
    lay.rect(230, wall_top + 8, 150, 10, 'N', 1.6)
    lay.hline(230, wall_top + 8, 150, 'L', 2.4)
    K.text(lay, 'BERLIN  OSTBAHNHOF', 305, wall_top + 10, 'P', 5.0, center=True)
    # ---- the end screen of the vault at the left: an iron-and-glass gable, its lower part open to the night
    for y in range(0, 140):
        for x in range(0, 46):
            lay.px(x, y, 'G', 1.2 + (y / 140.0) * 0.8 + (fine[y, x] - 0.5) * 0.4)
    for x in range(4, 44, 8):
        lay.vline(x, 0, 140, 'S', 2.2)
    for y in range(10, 140, 16):
        lay.hline(0, y, 46, 'S', 2.2)
        for x in range(0, 46):
            if fine[y, x] > 0.5:
                lay.px(x, y - 1, 'V', 1.2)                                      # snow on the transoms
    lay.erase(0, 140, 44, h - 140)                                              # the open mouth of the hall
    lay.rect(0, 138, 46, 3, 'S', 2.6, hgt=0.8)
    for x in range(1, 44, 3):                                                   # icicles on its lower edge
        ln = 1 + int(fine[141, x] * 5)
        lay.vline(x, 141, ln, 'V', 2.6)
    lay.rect(44, 0, 5, h, 'S', 1.6, hgt=0.7)                                    # the end arch
    lay.vline(44, 0, h, 'S', 3.0)
    K.resolve(lay, None, exposure=1.0)
    return lay


def track2_layer(w=900, h=130):
    """The next track (layer y 0 = world y 136): the green car with barred hatches and the chalk „Di – Kordon“ on
    its door, one hatch frosted from inside; a dwarf signal; the track bed.  Seen through the gap of the D 303
    (x 530..622) and left of the locomotive."""
    lay = K.tlayer(w, h, 'st_track2', 'A')
    oy = 136
    rail = 250 - oy
    nz = pg.value_noise(w, 20, 5, 601, octaves=2)
    for y in range(rail - 6, h):
        for x in range(w):
            lay.px(x, y, 'S', 1.0 + (nz[min(19, y - rail + 6), x] - 0.5) * 0.8 + (y - rail) * 0.02, flat=False)
    lay.hline(0, rail, w, 'S', 4.4)
    lay.hline(0, rail - 4, w, 'S', 3.0)
    # the green car: x 470..760 (its door with the chalk at x ~520)
    x0, x1 = 470, 760
    top, bot = 168 - oy, 244 - oy
    for y in range(top + 4, bot):
        c = (y - top) / (bot - top)
        lay.hline(x0, y, x1 - x0, 'E', 2.2 + 0.4 * (c < 0.1) - 0.5 * (c > 0.85), hgt=0.4)
    for x in range(x0, x1, 5):
        lay.vline(x, top + 4, bot - top - 4, 'E', 1.6)
    for k, (ins, t) in enumerate(((4, 1.6), (2, 2.2), (0, 2.6), (0, 2.0))):
        lay.hline(x0 + ins, top + k, x1 - x0 - 2 * ins, 'S', t)
    lay.rect(x0, bot, x1 - x0, 3, 'I', 1.0)
    # barred hatches high up under the roof (one frosted from inside)
    for i, hx in enumerate(range(x0 + 12, x1 - 12, 34)):
        lay.rect(hx, top + 8, 12, 8, 'I', 0.6)
        if i == 2:
            lay.rect(hx + 1, top + 9, 10, 6, 'V', 3.6)                             # frost from inside
            lay.px(hx + 4, top + 11, 'V', 2.4)
            lay.px(hx + 7, top + 12, 'V', 2.2)
        for bx in range(hx + 1, hx + 12, 3):
            lay.vline(bx, top + 8, 8, 'S', 3.8)
        lay.hline(hx, top + 8, 12, 'S', 3.2)
    # the sliding door and the chalk on it
    dx0 = 546
    lay.rect(dx0, top + 22, 26, bot - top - 24, 'E', 2.6)
    lay.vline(dx0, top + 22, bot - top - 24, 'E', 3.6)
    lay.hline(dx0 - 2, top + 21, 30, 'I', 0.8)
    chalk = ['DI - KORDON']
    K.text(lay, chalk[0], dx0 + 2, top + 36, 'V', 5.0)
    lay.line(dx0 + 3, top + 43, dx0 + 22, top + 42, 'V', 4.0)                       # the chalk underline
    lay.rect(dx0 + 20, top + 50, 2, 8, 'S', 4.2)
    # bogies
    for cx in (x0 + 36, x1 - 36):
        lay.rect(cx - 14, bot + 2, 28, 4, 'I', 1.2)
        for dx in (-8, 8):
            m = K.disc(11)
            lay.put(m, cx + dx - 5, bot + 3, 'S', 2.0)
            lay.put(K.erode(m, 2), cx + dx - 5, bot + 3, 'I', 1.0)
    # a dwarf signal and a track lamp
    lay.rect(300, rail - 12, 6, 12, 'S', 1.6)
    lay.rect(301, rail - 11, 4, 4, 'P', 5.0, emis=True)
    lay.rect(301, rail - 6, 4, 2, 'E', 3.4, emis=True)
    K.resolve(lay, None, exposure=1.0)
    return lay


def fg_layer(w=1000, h=42):
    """The foreground below platform K (parallax 1.25; layer y 0 = world y 318): the coping's front and the stone
    face of the platform wall (cable hooks with two cables, weep holes, icicles near the open end), the signal wires
    on their pulleys at its foot, then the near track -- snow-dusted sleepers, ballast, two rails whose heads mirror
    the sodium lamps, rail joints, meltwater puddles with the lamps in them, coal fallen from tenders, a crumpled
    newspaper, a cigarette packet; a dwarf signal near the end of the platform; at the far left the stair down to the
    underpass with its railing.  Lit by the lamp rows (warm pools under them), darker toward the bottom edge."""
    lay = K.tlayer(w, h, 'fg_station', 'A')
    rng = np.random.default_rng(1250)
    nz = pg.value_noise(w, h, 6, 1251, octaves=3)
    fine = pg.value_noise(w, h, 2, 1252, octaves=2)
    xs = np.arange(w, dtype=np.float32)
    # warm pools under the hanging lamps (x of the lamps + the parallax offset at mid camera)
    pool = np.zeros(w, np.float32)
    for lx_ in L.LAMPS_A:
        c = lx_ + 35
        pool = np.maximum(pool, np.exp(-((xs - c) / 46.0) ** 2))
    vign = lambda yy: 1.0 - 0.45 * max(0.0, (yy - 26) / 16.0)                   # noqa: E731
    # ---- the coping's front and the platform wall
    for x in range(w):
        lay.px(x, 0, 'P', 3.6 + 1.6 * pool[x], hgt=0.7)
        lay.px(x, 1, 'P', 2.0 + 0.8 * pool[x], hgt=0.4)
    for y in range(2, 14):
        off = ((y - 2) // 4) * 9
        for x in range(w):
            joint = ((y - 2) % 4 == 3) or ((x + off) % 17 == 0)
            t = (1.6 - (y - 2) * 0.06 + (nz[y, x] - 0.5) * 0.5 + 0.9 * pool[x]) * (0.7 if joint else 1.0)
            lay.px(x, y, 'P', max(0.3, t), flat=False, hgt=0.2)
    for x in range(0, w, 7):                                                     # soot run down the face
        if fine[3, x] > 0.6:
            for y in range(2, 2 + int(fine[5, x] * 9)):
                lay.px(x, y, 'N', 2.0)
    for x in range(30, w, 64):                                                   # weep holes
        lay.rect(x, 10, 2, 2, 'N', 0.2)
        lay.px(x, 12, 'G', 2.4)
    for (cy, tone) in ((5, 0.9), (7, 1.2)):                                      # two cables on iron hooks
        for x0_ in range(0, w, 48):
            for xx in range(x0_, min(w, x0_ + 48)):
                u = (xx - x0_) / 48.0 * 2 - 1
                yy = cy + int(round(1.5 * (1 - u * u)))
                lay.px(xx, yy, 'I', tone)
                if pool[xx] > 0.35:
                    lay.px(xx, yy - 1, 'S', 2.4 + pool[xx])
            lay.rect(x0_, cy - 1, 1, 3, 'S', 3.0)
    for x in range(0, 300, 3):                                                   # icicles near the open end
        if fine[0, x] > 0.55:
            for k in range(1 + int(fine[1, x] * 4 * (1 - x / 300.0))):
                lay.px(x, 2 + k, 'V', 2.4 - k * 0.3)
    # ---- the wall's foot: drain, signal wires on their pulleys
    for x in range(w):
        lay.px(x, 14, 'N', 0.4)
        lay.px(x, 15, 'S', 1.0)
    for x in range(8, w, 26):
        lay.rect(x, 14, 3, 3, 'S', 2.4 + pool[x], hgt=0.8)
        lay.px(x + 1, 15, 'I', 0.6)
    for wy in (15, 17):
        for x in range(w):
            if (x + wy) % 26 > 2:
                lay.px(x, wy, 'S', 1.8 + 1.2 * pool[x])
    # ---- the near track: ballast, sleepers, rails, joints
    for y in range(18, h):
        for x in range(w):
            t = (1.1 + (nz[y, x] - 0.5) * 1.0 + (fine[y, x] - 0.5) * 0.6 + 0.8 * pool[x]) * vign(y)
            if fine[y, x] > 0.72 and nz[y, x] > 0.45:
                lay.px(x, y, 'G', 2.2 + 0.8 * pool[x], flat=False)              # snow between the stones
            else:
                lay.px(x, y, 'S', max(0.4, t), flat=False, hgt=0.1)
    for sx in range(3, w, 11):                                                    # sleepers
        for y in range(19, 39):
            for x in range(sx, sx + 6):
                if x < w:
                    lay.px(x, y, 'D', (1.0 + (nz[y, x] - 0.5) * 0.5 + 0.6 * pool[x]) * vign(y), hgt=0.3)
        for x in range(sx, min(w, sx + 6)):
            if fine[19, x] > 0.35:
                lay.px(x, 19, 'V', 0.6 + pool[x] * 1.2)                          # snow on the sleepers
            lay.px(x, 38, 'D', 0.6)
    for (ry, head, web) in ((21, 3.6, 1.6), (33, 4.0, 1.8)):                      # far rail, near rail
        for x in range(w):
            lay.px(x, ry, 'S', head + 0.6 * fine[ry, x], hgt=1.0)
            lay.px(x, ry + 1, 'S', web, hgt=0.6)
            lay.px(x, ry + 2, 'I', 1.0)
            if pool[x] > 0.25:
                lay.px(x, ry, 'L', 3.6 + 1.6 * pool[x], hgt=1.0)                  # the lamps in the rail heads
        for sx in range(3, w, 11):
            lay.rect(sx + 1, ry + 1, 4, 2, 'S', 2.6)                             # rail chairs
    for jx in range(90, w, 140):                                                  # rail joints with fishplates
        for ry in (21, 33):
            lay.px(jx, ry, 'I', 0.8)
            lay.rect(jx - 4, ry + 1, 9, 2, 'S', 3.0)
            lay.px(jx - 3, ry + 1, 'S', 4.4)
            lay.px(jx + 3, ry + 1, 'S', 4.4)
    # ---- meltwater with the lamps in it, coal, litter
    for (px0, pw) in ((150, 26), (420, 34), (610, 22), (870, 30)):
        for y in range(25, 31):
            for x in range(px0, px0 + pw):
                if ((x - px0 - pw / 2) / (pw / 2)) ** 2 + ((y - 28) / 3.2) ** 2 < 1:
                    lay.px(x, y, 'G', 1.0 + 0.3 * fine[y, x])
        for k in range(pw // 3):
            lay.px(px0 + pw // 2 - 3 + k % 7, 26 + (k * 3) % 4, 'L', 3.2 + 1.4 * pool[min(w - 1, px0 + pw // 2)])
        lay.px(px0 + 3, 27, 'V', 1.6)
        lay.px(px0 + pw - 5, 29, 'V', 1.4)
    for _ in range(80):
        x, y = int(rng.integers(2, w - 2)), int(rng.integers(20, 40))
        lay.rect(x, y, 2, 1, 'I', 0.6 + rng.random() * 0.8)                      # coal fallen from tenders
        lay.px(x, y - 1, 'S', 2.8)
    lay.rect(300, 27, 8, 4, 'P', 4.6, hgt=0.4)                                    # a crumpled newspaper
    lay.px(301, 28, 'P', 3.0)
    lay.px(304, 29, 'I', 1.6)
    lay.px(306, 27, 'P', 5.6)
    lay.rect(706, 30, 4, 2, 'R', 2.6)                                             # a cigarette packet
    lay.px(709, 30, 'P', 5.6)
    lay.rect(520, 35, 3, 1, 'E', 3.4)                                             # a broken bottle
    lay.px(521, 34, 'V', 3.6)
    # ---- a dwarf signal near the end of the platform, lens lit
    dx = 930
    lay.rect(dx, 8, 7, 10, 'S', 1.6, hgt=0.8)
    lay.hline(dx, 8, 7, 'S', 3.4)
    lay.rect(dx + 1, 10, 2, 2, 'P', 6.4, emis=True)
    lay.rect(dx + 4, 13, 2, 2, 'P', 6.4, emis=True)
    lay.rect(dx + 2, 18, 3, 3, 'S', 2.0)
    # ---- at the far left: the stair down to the underpass, its railing and the lit steps going down
    for y in range(0, h):
        for x in range(0, 62):
            lay.px(x, y, 'N', 0.5 + 0.15 * (y % 4 == 0))
    for k in range(10):
        sy = 2 + k * 4
        lay.hline(0, sy, 62, 'P', 2.6 - k * 0.18, hgt=0.6)                       # the step nosings
        lay.hline(0, sy + 1, 62, 'P', 1.2 - k * 0.08)
    for x in range(0, 60, 9):
        lay.rect(x, 0, 2, h, 'S', 1.6, hgt=0.7)
        lay.px(x, 0, 'S', 3.4)
    lay.rect(0, 0, 63, 2, 'S', 2.6, hgt=0.8)
    lay.hline(0, 0, 63, 'L', 3.0)
    lay.line(62, 0, 80, h - 1, 'S', 2.6)
    lay.line(63, 0, 81, h - 1, 'S', 1.6)
    K.resolve(lay, None, exposure=1.0)
    return lay
