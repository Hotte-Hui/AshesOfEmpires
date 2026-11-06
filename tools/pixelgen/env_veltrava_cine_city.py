"""env_veltrava_cine_city -- t4 of LS_C3_Trains (round 10 rework): dawn over Veltrava, crane-up reveal.

Owner: cinematics stream (LS_C3_Trains places/motion).  The shot keeps the original idea -- dawn, the three-arch
stone bridge, Konrad's train from the west on the far track and Alexei's (sealed wagon 4 at its tail) from the east
on the near track meeting over the middle arch, their plumes running together, crows lifting off the ice at the
whistle, a woman pulling a sled along the bank -- but it is staged as a crane shot: it opens low on the river (ice,
floes, the arches, the near bank) with the bridge high in frame, and after the meeting the camera rises until the
Free City stands over the bridge: castle hill, cathedral, the palais of the Commission with its patinated dome
catching the first sun, the onion church, the town hall clock, the glass hall of the station, the old town with
its lit windows and chimney smoke, the quay with its lamps and a tram.

Planes (each a full-width image; END-view rows = image rows, the START view shows rows travel..travel+360):
  d4_sky (travel 40), d4_city (105), d4_bridge + d4_parapet + d4_lamp_glow (140), d4_bank (225).
The runtime (scenes/cinematics/ch3_trains) places a plane at y = -travel * (1 - crane(t)); because the far
planes travel less, the sun climbs out of the station roof and the city rises over the bridge while it cranes.
"""
from __future__ import annotations

import math

import numpy as np

import env_veltrava_cine as C
import env_veltrava_cine_kit as K
import pg

VW = C.VW
kit = C.kit
shift = C.shift
rim = C.rim
LAYOUT = C.LAYOUT.setdefault('trains', {})

PLANES = {'sky': 40, 'city': 105, 'bridge': 140, 'bank': 225}
H = {k: 360 + v for k, v in PLANES.items()}

# bridge plane rows (END view): the bridge of the original dawn shot, 100 px lower
DROP = 100
TRAIN_H = 30
DE_RAIL, SU_RAIL = 181 + DROP, 191 + DROP
PARAPET_Y = 185 + DROP
ARCHES = [(44, 220), (236, 404), (420, 596)]
ARCH_CY, ARCH_RY = 238 + DROP, 34
WATER_Y = 244 + DROP
QUAY_Y = 252                                    # city plane: top of the quay wall
PARAPET_LAMPS = [36, 128, 220, 312, 404, 496, 588]
BANK_TOP = 505                                  # bank plane: crest of the near bank
SUN = (604, 176)                                # sky plane: the low sun (behind the station hall at the start)
WALKER_Y = 498                                  # bank plane: top of the walker sprite (feet on the path)

SKY = ['#070A12', '#0C111C', '#121A26', '#1A2431', '#1E2836', '#2A3646', '#3A4859', '#4F5E70', '#5C6B82',
       '#687789', '#7684A0', '#8593A3', '#95A0B8', '#A1AAB7', '#B6B9C9']
DAWN = ['#5C6B82', '#7684A0', '#95A0B8', '#B6B9C9', '#D3CDD3', '#E8DCD6', '#F2E4D2', '#FCE2B0']
SIL = ['#070A12', '#0C111C', '#121A26', '#1A2431', '#1E2836', '#2A3646', '#3A4859', '#4F5E70', '#5C6B82',
       '#687789', '#7684A0', '#8593A3', '#95A0B8']
STONE = ['#0C111C', '#15171C', '#22262D', '#323840', '#464D55', '#5E666E', '#687789', '#8593A3', '#A1AAB7']
SNOW = ['#2A3646', '#3A4859', '#4F5E70', '#687789', '#7D8796', '#A1AAB7', '#C2C9D2', '#DEE2E7', '#F2F3F5']
WATER = ['#070A12', '#0C111C', '#121A26', '#1A2431', '#1E2836', '#2A3646', '#3A4859', '#4F5E70', '#687789',
         '#8593A3', '#A1AAB7']
CREAM = ['#1A2431', '#2E2C2C', '#4A4236', '#645A49', '#80745E', '#9E9076', '#BBAD8F', '#D6CBAE', '#E8DCD6']
BRICK = ['#140E10', '#2E1C1A', '#4A2A22', '#6A3C2C', '#8A5238', '#A86C4C', '#C48A62']
ROOF = ['#0C111C', '#15171C', '#1E2228', '#2A2E36', '#3A3E48', '#4E5260', '#687080']
PATINA = ['#0C1A1A', '#1E302E', '#2B4541', '#3D5E57', '#56796E', '#739585', '#97B5A2', '#C2D6C6']
LAMP = ['#4A2D1F', '#6E3F22', '#A8643A', '#D08F55', '#EDB777', '#FCE2B0', '#FFF4DA']
GOLD = ['#4A3415', '#73531F', '#9C7630', '#C49A48', '#E8C779', '#FCE2B0']
GREEN = ['#0C111C', '#121A1A', '#1E302E', '#2B4541', '#3D5E57', '#4A4236']


def ramps():
    return C.ramps(S=SKY, D=DAWN, N=SIL, I=STONE, W=SNOW, Q=WATER, C=CREAM, K=BRICK, F=ROOF, P=PATINA, L=LAMP,
                   G=GOLD, R=C.V['red'], T=GREEN)


def _east(xx):
    return np.clip((xx - 140) / 500.0, 0, 1)


def _bayer(w, h, ox=0, oy=0):
    return pg.bayer(w, h, ox, oy)


# =========================================================================== sky
def d4_sky():
    """Winter dawn: slate overhead, a cold band, rose-cream low in the east; stratus banks with lit undersides,
    the low sun over the station (the runtime raises it with the crane)."""
    h = H['sky']
    p = C.Paint(VW, h, ramps(), 'd4_sky')
    yy, xx = p.yy, p.xx
    east = _east(xx)
    u = np.clip((yy - 10) / 240.0, 0, 1)
    st = 3.0 + u ** 1.25 * (6.4 + 4.4 * east) + (pg.value_noise(VW, h, 70, 1401, 3) - 0.5) * 0.6
    p.put(np.ones((h, VW), bool), 'S', st)
    warm = np.clip((yy - 96) / 150.0, 0, 1) ** 1.05 * east ** 0.6
    wz = (warm * 1.6 > _bayer(VW, h, 1, 2)) & (yy < 330)
    p.put(wz, 'D', 0.6 + warm * 5.6 + (pg.value_noise(VW, h, 34, 1402, 2) - 0.5) * 0.5)
    sd = np.hypot(xx + 0.5 - SUN[0], (yy + 0.5 - SUN[1]) * 1.08)
    halo = (np.clip(1 - sd / 60.0, 0, 1) ** 1.3 * 1.6 > _bayer(VW, h, 3, 1)) & (sd >= 7.5)
    p.put(halo, 'D', 4.6 + np.clip(1 - sd / 60.0, 0, 1) * 2.4)
    p.put(sd < 8.0, 'D', 6.8)
    p.put(sd < 5.5, 'D', 7.0)
    rng = np.random.default_rng(1403)
    for _ in range(14):
        by = rng.uniform(16, 230)
        x0 = rng.uniform(-200, 560)
        ln = rng.uniform(170, 420)
        th = rng.uniform(2.5, 8.0) * (0.6 + by / 220)
        slope = rng.uniform(-0.01, 0.016)
        prof = np.clip(1 - np.abs(yy - by - slope * (xx - x0)) / th, 0, 1)
        taper = np.clip(np.minimum(xx - x0, x0 + ln - xx) / 70.0, 0, 1)
        dens = prof ** 0.7 * taper * (0.7 + 0.6 * pg.value_noise(VW, h, 20, int(rng.integers(1 << 20)), 2))
        band = dens > _bayer(VW, h, 2, 3) * 0.9 + 0.1
        uu = np.clip((by - 10) / 240.0, 0, 1)
        p.put(band, 'S', 3.2 + uu * 4.2 + east * 1.0 - dens * 1.0)
        under = band & ~shift(band, 0, 1) & (yy > by)
        hot = east > 0.4
        p.put(under & hot, 'D', 1.4 + east * 3.6 + uu * 1.2)
        p.put(under & ~hot, 'S', 6.0 + uu * 2.2)
        p.add(band & ~shift(band, 0, -1), -0.6)
    p.resolve(band=2.6)
    return p.L


# =========================================================================== city helpers
class City:
    """Paint helper for the city plane: houses, towers, roofs with snow and lit windows."""

    def __init__(self, p, rng):
        self.p = p
        self.rng = rng
        self.lit_windows = []           # runtime: [x, y, w, h, off_time] windows that go dark at dawn
        self.chimneys = []

    def windows(self, x0, x1, y0, y1, nx, ny, haze, lit_p=0.35, ww=2, wh=3, base=None):
        p, rng = self.p, self.rng
        if nx <= 0 or ny <= 0:
            return
        sx = (x1 - x0) / nx
        sy = (y1 - y0) / ny
        for j in range(ny):
            for i in range(nx):
                wx = int(round(x0 + sx * (i + 0.5) - ww / 2))
                wy = int(round(y0 + sy * (j + 0.5) - wh / 2))
                m = p.box(wx, wy, wx + ww, wy + wh)
                if rng.random() < lit_p:
                    lv = float(rng.choice([2.2, 3.0, 3.6, 4.2]))
                    p.put(m, 'L', lv, emis=True)
                    if wh >= 3 and rng.random() < 0.5:
                        p.put(p.box(wx, wy + wh - 1, wx + ww, wy + wh), 'L', lv - 1.0, emis=True)
                    if rng.random() < 0.3 and len(self.lit_windows) < 110:
                        self.lit_windows.append([wx, wy, ww, wh, round(float(rng.uniform(1.5, 11.5)), 2)])
                else:
                    tone = (base if base is not None else 0.8) + haze * 2.2
                    p.put(m, 'N', tone)
                    p.put(p.box(wx, wy, wx + ww, wy + 1), 'N', tone + 1.6)          # cold sky in the upper pane
                p.put(p.box(wx, wy - 1, wx + ww, wy), 'W', 3.0 + haze * 3.0)          # snow on the lintel

    def snow_cap(self, m, tone=5.5, depth=1):
        p = self.p
        cap = m & ~shift(m, 0, -1)
        for k in range(1, depth):
            cap |= m & ~shift(m, 0, -(k + 1)) & shift(m, 0, -1)
        p.put(cap, 'W', tone)
        return cap

    def roof(self, x, top, w, kind, haze, seed=0):
        """Roof polygon above the wall top `top`; snow-covered slate with the east slope lit."""
        p = self.p
        yy, xx = p.yy, p.xx
        east = _east(xx)
        rh = int(max(5, min(w * (0.62 if kind == 'gable' else 0.42), 22)))
        if kind == 'gable':
            pts = [(x - 1, top + 1), (x + w / 2, top - rh), (x + w + 1, top + 1)]
        elif kind == 'mansard':
            pts = [(x - 1, top + 1), (x + 2, top - rh * 0.75), (x + 5, top - rh), (x + w - 5, top - rh),
                   (x + w - 2, top - rh * 0.75), (x + w + 1, top + 1)]
        elif kind == 'hip':
            pts = [(x - 1, top + 1), (x + w * 0.28, top - rh * 0.85), (x + w * 0.72, top - rh * 0.85),
                   (x + w + 1, top + 1)]
        elif kind == 'step':
            n = 3
            sw = w / (2 * n + 1)
            pts = [(x, top + 1)]
            for k in range(n):
                y0_ = top - k * rh / n
                y1_ = top - (k + 1) * rh / n
                pts += [(x + k * sw, y1_), (x + (k + 1) * sw, y1_)]
            pts += [(x + w - n * sw, top - rh)]
            for k in reversed(range(n)):
                y1_ = top - (k + 1) * rh / n
                pts += [(x + w - (k + 1) * sw, y1_), (x + w - k * sw, y1_)]
            pts += [(x + w, top + 1)]
        else:
            pts = [(x - 1, top - 3), (x + w + 1, top - 3), (x + w + 1, top + 1), (x - 1, top + 1)]
        m = p.poly(pts)
        slate = 'F' if haze < 0.6 else 'N'
        p.put(m, slate, 1.2 + haze * 4.0)
        nz = pg.value_noise(VW, p.h, 3, 1600 + seed, 2)
        eave = m & ~shift(m, 0, -2)
        snow = m & ~eave & (nz > 0.3)
        p.put(snow, 'W', 3.2 + haze * 2.6 + east * 0.7)
        if kind != 'flat':
            p.put(snow & (xx > x + w / 2), 'W', 4.2 + haze * 2.4 + east * 1.0)
        self.snow_cap(m, 6.0 + haze * 1.4 + east * 0.5)
        p.put(m & ~shift(m, 0, 1), slate, 0.6 + haze * 2.0)                   # eaves shadow line
        return m, rh

    def house(self, x, base, w, h, kind, haze, lit_p=0.35, ramp='N', wall=None, seed=0, chimney=True,
              windows=True, door=False):
        """One town house: facade + roof + snow + windows + chimneys. haze 0 (near, dark) .. 1 (far, light)."""
        p, rng = self.p, self.rng
        xx = p.xx
        east = _east(xx)
        wall_t = (wall if wall is not None else 2.0) + haze * 3.4
        body = p.box(x, base - h, x + w, base)
        p.put(body, ramp, wall_t + east * 0.4)
        p.put(body & ~shift(body, 1, 0), ramp, wall_t + 1.2 + east * 0.8)            # dawn on the east edge
        p.put(body & ~shift(body, -1, 0), ramp, wall_t - 0.6)
        floors = max(1, int(h // 9))
        for f in range(1, floors):
            yv = base - int(h * f / floors)
            p.put(p.box(x, yv, x + w, yv + 1), ramp, wall_t + 0.7)
        top = base - h
        p.put(p.box(x - 1, top, x + w + 1, top + 1), ramp, wall_t + 1.0)              # cornice
        rm, rh = self.roof(x, top, w, kind, haze, seed)
        if kind == 'mansard' and w > 14:
            for dx in range(x + 5, x + w - 6, 7):                                       # dormers
                p.put(p.box(dx, top - rh + 4, dx + 3, top - 1), ramp, wall_t)
                p.put(p.box(dx - 1, top - rh + 3, dx + 4, top - rh + 4), 'W', 6.2)
                if rng.random() < lit_p:
                    p.put(p.box(dx + 1, top - rh + 5, dx + 2, top - 2), 'L', 3.0, emis=True)
        if chimney:
            for _ in range(int(rng.integers(1, 3))):
                cx = int(rng.uniform(x + 2, x + w - 4))
                ytop = top - rh - int(rng.integers(0, 4)) if kind != 'flat' else top - 7
                ch = p.box(cx, ytop, cx + 3, top) & ~kit.erode(rm, 2)
                p.put(ch, 'K' if haze < 0.5 else ramp, 2.4 + haze * 2.4)
                p.put(p.box(cx, ytop, cx + 3, ytop + 1) & ch, 'W', 6.2)
                self.chimneys.append([cx + 1, ytop])
        if windows:
            nx = max(1, int(w // 6))
            self.windows(x + 2, x + w - 2, top + 3, base - (5 if door else 1), nx, floors, haze, lit_p=lit_p)
        if door:
            dx = x + w // 2 - 2
            on = rng.random() < 0.45
            p.put(p.box(dx, base - 5, dx + 4, base), 'L' if on else 'N', 2.4 if on else 0.6, emis=on)

    def tower(self, x, base, w, h, top, haze, ramp='N', clock=False, lit=True):
        """Square tower with a spire / onion / pyramid / copper top and an optional lit clock."""
        p = self.p
        xx = p.xx
        t0 = 2.0 + haze * 3.6
        body = p.box(x, base - h, x + w, base)
        p.put(body, ramp, t0)
        p.put(body & ~shift(body, 1, 0), ramp, t0 + 1.6)
        p.put(body & ~shift(body, -1, 0), ramp, t0 - 0.6)
        for yv in range(base - h + 6, base, 10):
            p.put(p.box(x, yv, x + w, yv + 1), ramp, t0 + 0.9)
            p.put(p.box(x, yv - 1, x + w, yv), 'W', 4.0 + haze * 2.0)
        ytop = base - h
        cx = x + w / 2
        if top == 'spire':
            sp = p.poly([(x - 1, ytop + 1), (cx, ytop - w * 2.6), (x + w + 1, ytop + 1)])
            p.put(sp, 'F' if haze < 0.5 else ramp, 1.6 + haze * 3.6)
            p.put(sp & (xx > cx), 'F' if haze < 0.5 else ramp, 2.6 + haze * 3.6)
            p.put(p.line([(cx, ytop - w * 2.6), (cx, ytop - w * 2.6 - 5)], 0.4), 'G', 2.6)
            for k in (0, 1):
                px_ = x + (0 if k == 0 else w - 2)
                p.put(p.poly([(px_, ytop + 1), (px_ + 1, ytop - 6), (px_ + 2, ytop + 1)]), ramp, t0 + 0.6)
        elif top == 'onion':
            r = w * 0.75
            on = p.ell(cx, ytop - r * 0.8, r, r * 0.95) | p.poly([(cx - r * 0.7, ytop - r * 1.2),
                                                                  (cx, ytop - r * 2.6), (cx + r * 0.7, ytop - r * 1.2)])
            p.put(on, 'P', 1.6 + np.clip((xx - cx + r) / (2 * r), 0, 1) * 2.6 + haze * 1.0)
            p.put(on & ~shift(on, 1, 0), 'D', 3.0)
            self.snow_cap(on, 6.0)
            p.put(p.line([(cx, ytop - r * 2.6), (cx, ytop - r * 2.6 - 6)], 0.4), 'G', 3.0)
            p.put(p.box(cx - 2, ytop - r * 2.6 - 4, cx + 3, ytop - r * 2.6 - 3), 'G', 3.0)
        elif top == 'pyramid':
            sp = p.poly([(x - 1, ytop + 1), (cx, ytop - w * 0.9), (x + w + 1, ytop + 1)])
            p.put(sp, 'F', 1.8 + haze * 3.4)
            self.snow_cap(sp, 6.0)
        elif top == 'copper':
            sp = p.poly([(x - 1, ytop + 1), (x + 2, ytop - 6), (cx, ytop - w * 2.2), (x + w - 2, ytop - 6),
                         (x + w + 1, ytop + 1)])
            p.put(sp, 'P', 1.8 + np.clip((xx - x) / w, 0, 1) * 2.4 + haze)
            p.put(p.line([(cx, ytop - w * 2.2), (cx, ytop - w * 2.2 - 6)], 0.4), 'G', 3.0)
            self.snow_cap(sp, 6.4)
        if clock:
            cy = ytop + 8
            p.put(p.ell(cx, cy, w * 0.36, w * 0.36), 'C', 7.0, emis=True)
            p.put(p.ell(cx, cy, w * 0.36 - 1, w * 0.36 - 1), 'C', 8.0, emis=True)
            p.put(p.line([(cx, cy), (cx, cy - w * 0.25)], 0.4), 'N', 1.0)
            p.put(p.line([(cx, cy), (cx + w * 0.2, cy + 1)], 0.4), 'N', 1.0)
        if lit:
            for yv in range(base - h + (20 if clock else 14), base - 4, 12):
                p.put(p.box(cx - 1, yv, cx + 1, yv + 3), 'L', 2.4, emis=True)


def _stone(p, m, base, lit_from=None, seed=0):
    """Masonry in the dawn: cool stone (SIL ramp) with courses and a few odd blocks, the shaded west edge, the
    east-facing part warmed by the low sun (DAWN ramp) and its east edge lit."""
    yy, xx = p.yy, p.xx
    nz = pg.value_noise(VW, p.h, 2, 1430 + seed, 1)
    course = (yy.astype(int) % 3) == 0
    p.put(m, 'N', base + (nz - 0.5) * 0.5)
    p.put(m & course, 'N', base - 0.7)
    p.put(m & (nz > 0.82) & ~course, 'N', base + 0.6)
    p.put(m & ~shift(m, -1, 0), 'N', base - 0.9)
    if lit_from is not None:
        warm = m & (xx >= lit_from)
        p.put(warm & ~course, 'D', 0.9 + (nz - 0.5) * 0.5)
        p.put(warm & course, 'N', base + 0.2)
    p.put(m & ~shift(m, 1, 0), 'D', 2.6)


def _crenels(p, x0, x1, y, tone=6.8, step=4):
    """Merlons along a wall top at row y (2 px high, snow on each)."""
    for bx in range(int(x0), int(x1) - 1, step):
        p.put(p.box(bx, y - 2, bx + 2, y), 'N', tone)
        p.put(p.box(bx, y - 3, bx + 2, y - 2), 'W', 7.4)


def _cone(p, cty, cx, y_eave, r, h, haze=0.0):
    """A round tower's conical roof: slate, the east half in the dawn, snow streaks, a finial."""
    yy, xx = p.yy, p.xx
    m = p.poly([(cx - r - 1, y_eave + 1), (cx, y_eave - h), (cx + r + 1, y_eave + 1)])
    p.put(m, 'F', 3.0 + haze)
    p.put(m & (xx > cx), 'F', 4.4 + haze)
    p.put(m & (xx > cx + r * 0.45), 'D', 1.4)
    streak = m & ((xx.astype(int) * 3 + yy.astype(int)) % 5 == 0) & (yy > y_eave - h + 3)
    p.put(streak, 'W', 5.6 + haze)
    cty.snow_cap(m, 7.4)
    p.put(p.box(cx, y_eave - h - 4, cx + 1, y_eave - h), 'I', 4.0)
    return m


def _round_tower(p, cty, cx, top, base, r, roof_h, slits=()):
    """Cylinder shading lit from the east, string courses, arrow slits, a conical roof."""
    yy, xx = p.yy, p.xx
    body = p.box(cx - r, top, cx + r + 1, base)
    u = np.clip((xx + 0.5 - cx) / (r + 0.5), -1, 1)
    p.put(body, 'N', 5.4 + (u + 1) * 0.9 + (pg.value_noise(VW, p.h, 2, 1440 + int(cx), 1) - 0.5) * 0.4)
    p.put(body & (u > 0.35), 'D', 0.9 + (u - 0.35) * 2.8)
    p.put(body & ((yy.astype(int) % 3) == 0) & (u <= 0.35), 'N', 5.2 + (u + 1) * 0.7)
    p.put(body & (np.abs(yy - (top + 2)) < 1), 'N', 7.6)                      # the corbel course under the eave
    for sy in slits:
        p.put(p.box(cx - 1, sy, cx, sy + 3), 'N', 1.6)
    _cone(p, cty, cx, top, r, roof_h)


def _fir_tiers(p, x, base, h, tone=4.4, lit=6.6):
    """A snow-laden spruce on the hill: dark tiers, the east tips catching the dawn."""
    yy, xx = p.yy, p.xx
    w = max(1.6, h * 0.36)
    m = p.poly([(x - w, base), (x, base - h), (x + w, base)])
    p.put(m, 'N', tone)
    tiers = m & (((yy.astype(int) - int(base)) % 3) == 0)
    p.put(tiers & (xx >= x), 'W', lit)
    p.put(tiers & (xx < x), 'W', lit - 1.4)
    p.put(m & ~shift(m, 1, 0) & (xx > x), 'D', 1.8)
    return m


def _hill(p, cty):
    """The castle hill in the west (AD round 2: drawn with the care of the palais beside it).  A crag with a rock
    face under the walls, spruce forest on the flanks, the road zig-zagging up between retaining walls and lamps to
    the gatehouse; on top the castle: curtain wall with merlons and arrow slits, two round towers with conical roofs,
    the square keep with its corbelled gallery and steep roof (a plain pennant), the palas with dormers, chimneys and
    lit windows, a chapel with its ridge turret, the stair tower's copper cap.  Dawn comes from the east (right)."""
    yy, xx = p.yy, p.xx
    # ---- the hill: wooded flanks, snow on the clearings
    hill = p.poly([(-6, 236), (-6, 166), (10, 156), (26, 147), (40, 139), (52, 134), (70, 131), (96, 129),
                   (124, 130), (146, 134), (162, 142), (180, 157), (202, 180), (220, 204), (234, 236)])
    gn = pg.value_noise(VW, p.h, 14, 1420, 3)
    p.put(hill, 'N', 7.4 + np.clip((yy - 130) / 110, 0, 1) * 0.6 + (gn - 0.5) * 0.5)
    p.put(hill & ~shift(hill, 0, -1), 'W', 6.4)
    # the east flank of the hill takes the first light, the west flank stays cold
    p.put(hill & (xx > 150) & (yy < 200) & ((gn * 1.4 + (xx - 150) / 90.0) > 1.0), 'D', 1.6 + (gn - 0.5) * 0.6)
    # the rock face under the castle: buttresses of rock, their east faces in the dawn, dark clefts between them,
    # snow on every ledge and on the tops
    crag = p.poly([(40, 140), (46, 134), (156, 134), (166, 144), (160, 154), (146, 152), (132, 160), (112, 156),
                   (92, 162), (74, 156), (58, 158), (48, 150)])
    rng = np.random.default_rng(1422)
    p.put(crag, 'N', 5.0)
    bx = 40.0
    while bx < 166:
        bw = rng.uniform(5, 14)
        bot = 148 + rng.uniform(0, 14)
        top_ = 134 + (rng.uniform(0, 7) if rng.random() < 0.45 else 0.0)        # some heads broken lower
        lean = rng.uniform(-0.25, 0.25)                                          # the joints are not plumb
        x_l = bx + (yy - 134) * lean
        but = crag & (xx >= x_l) & (xx < x_l + bw) & (yy < bot) & (yy >= top_)
        p.put(but, 'N', 6.0 + rng.uniform(-0.4, 0.4))
        lf = rng.uniform(0.4, 0.72)
        p.put(but & (xx >= x_l + bw * lf), 'D', 1.0 + rng.uniform(0, 0.8))      # the east face in the dawn
        p.put(but & (xx < x_l + rng.uniform(0.8, 1.8)), 'N', 3.4)               # the cleft on its west side
        p.put(but & ~shift(but, 0, -1) & (yy > 135), 'W', 6.8)                   # snow on a broken head
        for ly in np.arange(137 + rng.uniform(0, 4), bot - 1, rng.uniform(4.5, 7.0)):
            lx0 = bx + rng.uniform(0, bw * 0.4)
            p.put(but & (np.abs(yy - ly) < 0.6) & (xx >= lx0) & (xx < lx0 + bw * rng.uniform(0.4, 0.8)), 'W', 7.0)
        bx += bw
    p.put(crag & ~shift(crag, 0, -1), 'W', 7.2)
    p.put(crag & ~shift(crag, 0, 1) & ~hill, 'N', 4.6)
    # spruce forest in stands on the flanks, back rows first (not over the road band or the crag); bare birches
    rng = np.random.default_rng(1423)
    road_pts = [(10, 236), (66, 216), (34, 200), (92, 184), (62, 170), (112, 158), (124, 140)]
    road = p.line(road_pts, 1.2)
    stands = [(14, 172, 16), (36, 160, 14), (60, 192, 18), (100, 172, 14), (150, 170, 16), (176, 186, 18),
              (198, 206, 16), (120, 206, 20), (20, 214, 16), (84, 222, 18), (160, 222, 18)]
    trees = []
    for (sx_, sy_, sr) in stands:
        for _ in range(int(sr * 1.3)):
            ang = rng.uniform(0, 2 * math.pi)
            rad = sr * math.sqrt(rng.uniform(0, 1))
            trees.append((sy_ + math.sin(ang) * rad * 0.45, sx_ + math.cos(ang) * rad))
    for _ in range(40):
        trees.append((rng.uniform(150, 236), rng.uniform(-4, 230)))
    trees.sort()
    for fy, fx in trees:
        ix, iy = int(np.clip(fx, 0, VW - 1)), int(np.clip(fy, 0, p.h - 1))
        if not hill[iy, ix] or crag[iy, ix] or road[iy, ix] or road[max(0, iy - 3), ix]:
            continue
        if rng.random() < 0.12:                                                    # a bare birch
            bh = rng.uniform(6, 10)
            p.put(p.box(fx, fy - bh, fx + 1, fy + 1), 'W', 6.0)
            for _b in range(4):
                a_ = rng.uniform(-2.5, -0.6)
                sy0 = fy - bh + rng.uniform(0, bh * 0.5)
                p.put(p.line([(fx, sy0), (fx + math.cos(a_) * 3.5, sy0 + math.sin(a_) * 3.5)], 0.3), 'N', 4.2)
            continue
        h = rng.uniform(6, 11) * (0.85 + (fy - 150) / 260)
        _fir_tiers(p, fx, fy, h, tone=3.6 + rng.uniform(-0.4, 0.5), lit=6.2)
    # the road: a snowy band with its retaining wall below, lamps along it (a few still lit at dawn)
    p.put(road & hill & ~crag, 'W', 6.2)
    wallr = shift(road, 0, -2) & ~road & hill & ~crag
    p.put(wallr, 'N', 5.0)
    p.put(wallr & ((xx.astype(int) % 3) == 0), 'N', 5.8)
    for i, (lx, ly) in enumerate(((22, 230), (50, 211), (74, 194), (52, 176), (96, 163), (118, 150))):
        p.put(p.box(lx, ly - 4, lx + 1, ly), 'I', 2.2)
        p.put(p.box(lx - 1, ly - 5, lx + 2, ly - 4), 'L' if i % 2 == 0 else 'N', 4.4 if i % 2 == 0 else 5.0,
              emis=i % 2 == 0)
    # ---- the castle
    # curtain wall along the top of the crag, merlons, arrow slits; the gatehouse where the road arrives
    wall = p.box(44, 118, 158, 136)
    _stone(p, wall, 6.2, 150)
    _crenels(p, 44, 158, 118)
    for sx in range(52, 152, 9):
        p.put(p.box(sx, 124, sx + 1, 128), 'N', 2.6)
    gate = p.box(116, 106, 132, 136)
    _stone(p, gate, 6.6, 128, seed=3)
    _crenels(p, 116, 132, 106)
    arch = p.box(121, 126, 127, 136) | p.ell(124, 126, 3, 3)
    p.put(arch, 'N', 1.4)
    p.put(p.box(122, 128, 126, 136), 'L', 1.8, emis=True)                    # the gate passage, a lamp inside
    p.put(p.box(118, 120, 119, 123), 'L', 4.0, emis=True)                    # lantern by the gate
    p.put(p.box(121, 112, 123, 116) | p.box(125, 112, 127, 116), 'N', 2.4)
    # the chapel (west), its ridge turret with a little spire
    chap = p.box(56, 100, 76, 118)
    _stone(p, chap, 6.8, 72, seed=4)
    croof = p.poly([(54, 101), (66, 92), (78, 101)])
    p.put(croof, 'F', 3.2)
    p.put(croof & (xx > 66), 'F', 4.6)
    cty.snow_cap(croof, 7.4, depth=2)
    for wx in (60, 66, 72):
        p.put(p.box(wx, 104, wx + 2, 111) | p.ell(wx + 1, 104, 1, 1), 'L', 2.2, emis=True)
    p.put(p.box(65, 84, 68, 93), 'N', 6.4)
    spm = p.poly([(64, 85), (66.5, 77), (69, 85)])
    p.put(spm, 'F', 3.6)
    cty.snow_cap(spm, 7.4)
    # the palas (east): a long hall with a steep roof, dormers, chimneys, two rows of windows
    pal = p.box(96, 88, 148, 118)
    _stone(p, pal, 6.6, 142, seed=5)
    p.put(p.box(96, 102, 148, 103), 'N', 7.6)                                # string course
    proof = p.poly([(94, 89), (100, 74), (144, 74), (150, 89)])
    p.put(proof, 'F', 3.0)
    p.put(proof & (xx > 122), 'F', 4.2)
    p.put(proof & (xx > 144), 'D', 1.6)
    cty.snow_cap(proof, 7.6, depth=2)
    p.put(proof & ((xx.astype(int) % 4) == 0) & (yy > 78), 'W', 5.2)         # snow lying in the seams
    for dx in (104, 116, 130):                                               # dormers
        dm = p.box(dx, 79, dx + 5, 85)
        p.put(dm, 'N', 6.6)
        p.put(p.poly([(dx - 1, 80), (dx + 2.5, 76), (dx + 6, 80)]), 'W', 7.2)
        p.put(p.box(dx + 1, 81, dx + 4, 84), 'L' if dx != 116 else 'N', 3.0 if dx != 116 else 3.0,
              emis=dx != 116)
    for cx_ in (100, 140):                                                   # chimneys, smoke via LAYOUT d4_chimneys
        p.put(p.box(cx_, 68, cx_ + 3, 76), 'K', 3.0)
        p.put(p.box(cx_, 67, cx_ + 3, 68), 'W', 7.0)
        cty.chimneys.append([cx_ + 1, 67])
    lit_rows = ((92, 0.55), (106, 0.4))
    rng2 = np.random.default_rng(1424)
    for (wy, pl) in lit_rows:
        for wx in range(99, 146, 6):
            if 116 <= wx <= 121:
                continue
            m = p.box(wx, wy, wx + 2, wy + 4)
            if rng2.random() < pl:
                lv = float(rng2.choice([2.4, 3.0, 3.6]))
                p.put(m, 'L', lv, emis=True)
                if len(cty.lit_windows) < 110 and rng2.random() < 0.5:
                    cty.lit_windows.append([wx, wy, 2, 4, round(float(rng2.uniform(3.0, 10.0)), 2)])
            else:
                p.put(m, 'N', 2.8)
                p.put(p.box(wx, wy, wx + 2, wy + 1), 'N', 4.6)
            p.put(p.box(wx, wy + 4, wx + 2, wy + 5), 'W', 7.2)                   # snow on the sill
    # the stair tower in front of the palas with its copper cap
    st = p.box(117, 80, 124, 118)
    _stone(p, st, 7.0, 122, seed=6)
    for sy in (86, 96, 108):
        p.put(p.box(119, sy, 121, sy + 3), 'L', 2.6, emis=True)
    cap = p.ell(120.5, 79, 4.5, 3.5) & (yy < 80) | p.poly([(117, 77), (120.5, 70), (124, 77)])
    p.put(cap, 'P', 3.0)
    p.put(cap & (xx > 120), 'P', 5.0)
    cty.snow_cap(cap, 7.4)
    p.put(p.box(120, 66, 121, 70), 'G', 3.4)
    # the keep: square, tall, a corbelled timber gallery at the top, a steep pyramid roof, the pennant
    keep = p.box(78, 64, 94, 118)
    _stone(p, keep, 6.4, 91, seed=7)
    for sy in (78, 92, 104):
        p.put(p.box(85, sy, 87, sy + 4), 'N', 1.8)
    p.put(p.box(85, 92, 87, 96), 'L', 3.2, emis=True)
    gal = p.box(76, 56, 96, 64)
    p.put(gal, 'K', 1.6)
    p.put(gal & (xx > 90), 'K', 2.6)
    for gx in range(77, 96, 3):
        p.put(p.box(gx, 58, gx + 1, 62), 'K', 0.8)
    for kx in range(76, 96, 4):
        p.put(p.box(kx, 64, kx + 2, 66), 'N', 5.0)                           # the corbels
    p.put(p.box(79, 58, 81, 61), 'L', 3.0, emis=True)
    kroof = p.poly([(74, 57), (86, 38), (98, 57)])
    p.put(kroof, 'F', 3.0)
    p.put(kroof & (xx > 86), 'F', 4.4)
    p.put(kroof & (xx > 92), 'D', 1.6)
    cty.snow_cap(kroof, 7.6, depth=2)
    p.put(kroof & ((xx.astype(int) * 2 + yy.astype(int)) % 6 == 0) & (yy > 44), 'W', 5.8)
    p.put(p.box(86, 28, 87, 38), 'I', 4.0)                                    # plain pennant on the keep
    p.put(p.poly([(87, 28), (96, 30), (87, 33)]), 'C', 7.0)
    # the round towers at both ends of the curtain wall
    _round_tower(p, cty, 44, 100, 138, 6, 15, slits=(108, 120))
    _round_tower(p, cty, 157, 104, 140, 6, 14, slits=(112, 124))


def _cathedral(p, cty):
    yy, xx = p.yy, p.xx
    nave = p.poly([(152, 214), (152, 170), (164, 160), (216, 160), (228, 170), (228, 214)])
    p.put(nave, 'N', 6.2 + np.clip((xx - 152) / 76, 0, 1) * 0.6)
    cty.snow_cap(nave, 7.2)
    for k in range(5):                                                                # buttresses + tall windows
        bx = 168 + k * 10
        p.put(p.box(bx, 172, bx + 2, 214), 'N', 7.0)
        p.put(p.box(bx + 4, 176, bx + 6, 196), 'L', 1.8, emis=True)
    for (sx, h_, w_) in ((154, 70, 14), (206, 60, 12)):
        cty.tower(sx, 214, w_, h_, 'spire', 0.72)
    for k in range(6):
        p.put(p.poly([(166 + k * 8, 160), (168 + k * 8, 152), (170 + k * 8, 160)]), 'N', 6.0)
    p.put(p.ell(190, 178, 5, 5), 'L', 2.2, emis=True)
    p.put(p.ell(190, 178, 2, 2), 'L', 3.4, emis=True)


def _palais(p, cty):
    """The palais of the Commission: classical front, portico, drum and the patinated dome (first sun)."""
    yy, xx = p.yy, p.xx
    east = _east(xx)
    front = p.box(236, 166, 424, 222)
    p.put(front, 'C', 4.4 + east * 0.6 - np.clip((yy - 166) / 56, 0, 1) * 0.8)
    p.put(p.box(232, 162, 428, 166), 'C', 6.0)
    p.put(p.box(232, 161, 428, 162), 'W', 7.0)
    p.put(p.box(232, 166, 428, 167), 'C', 2.6)
    for k in range(16):                                                     # pilasters
        px_ = 240 + k * 12
        p.put(p.box(px_, 168, px_ + 2, 220), 'C', 5.4 + (0.6 if k % 2 else 0))
        p.put(p.box(px_ + 2, 168, px_ + 3, 220), 'C', 3.4)
    for row, (y0, y1) in enumerate(((172, 181), (187, 196), (202, 211))):
        for k in range(15):
            wx = 245 + k * 12
            if 300 <= wx <= 356:
                continue
            lit = (k * 7 + row * 3) % 5 in (0, 2)
            m = p.box(wx, y0, wx + 4, y1)
            if lit:
                p.put(m, 'L', 2.6 + (k % 3) * 0.5, emis=True)
                p.put(p.box(wx, y0, wx + 4, y0 + 1), 'L', 4.4, emis=True)
                if (k + row) % 3 == 0:
                    cty.lit_windows.append([wx, y0, 4, y1 - y0, round(3.0 + ((k * 5 + row * 7) % 9) * 0.9, 2)])
            else:
                p.put(m, 'N', 3.0)
                p.put(p.box(wx, y0, wx + 4, y0 + 1), 'N', 5.2)
            p.put(p.box(wx - 1, y0 - 1, wx + 5, y0), 'W', 6.4)
            p.put(p.box(wx - 1, y1, wx + 5, y1 + 1), 'C', 6.0)
    ped = p.poly([(294, 183), (330, 166), (366, 183)])
    p.put(p.box(298, 182, 362, 222), 'C', 3.6)
    p.put(ped, 'C', 5.8)
    p.put(ped & ~shift(ped, 0, -1), 'W', 7.2)
    p.put(p.poly([(304, 181), (330, 170), (356, 181)]), 'C', 4.4)
    for k in range(6):
        cx_ = 303 + k * 10
        col = p.box(cx_, 185, cx_ + 4, 222)
        p.put(col, 'C', 6.4)
        p.put(col & (xx == cx_), 'C', 5.0)
        p.put(col & (xx == cx_ + 3), 'C', 7.4)
        p.put(p.box(cx_ - 1, 184, cx_ + 5, 186), 'C', 7.0)
    p.put(p.box(310, 200, 350, 222), 'L', 2.4, emis=True)                  # the lit door hall behind the columns
    for k in range(6):
        p.put(p.box(303 + k * 10, 200, 307 + k * 10, 222), 'C', 6.0)
    drum = p.box(284, 130, 376, 162)
    p.put(drum, 'C', 4.2 + np.clip((xx - 284) / 92, 0, 1) * 1.6)
    for k in range(12):
        p.put(p.box(287 + k * 8, 134, 289 + k * 8, 160), 'C', 6.0)
        if k % 2 == 0 and k < 11:
            p.put(p.box(290 + k * 8, 140, 293 + k * 8, 154), 'L', 2.2, emis=True)
    p.put(p.box(280, 126, 380, 130), 'C', 6.4)
    p.put(p.box(280, 125, 380, 126), 'W', 7.4)
    dome = p.ell(330, 128, 47, 46) & (yy < 126)
    dl = np.clip((xx - 296) / 74, 0, 1)
    p.put(dome, 'P', 1.6 + dl * 3.4 + np.clip((yy - 84) / 40, 0, 1) * 0.5)
    for k in range(-4, 5):
        rx = 330 + k * 9.5
        p.put(p.line([(rx, 126), (330 + k * 5.0, 86)], 0.45) & dome, 'P', 1.0 + dl[110, int(rx) % VW] * 1.8)
    p.put(dome & rim(dome, 1, -1, 2) & (xx > 334), 'P', 7.0)                       # first sun on the copper
    p.put(dome & rim(dome, 0, -1, 1), 'W', 6.0)
    lantern = p.box(323, 72, 337, 86) | p.poly([(321, 72), (330, 60), (339, 72)])
    p.put(lantern, 'C', 4.6)
    p.put(lantern & ~shift(lantern, 1, 0), 'C', 7.0)
    p.put(p.box(326, 75, 334, 82), 'L', 3.6, emis=True)
    p.put(p.line([(330, 60), (330, 52)], 0.4), 'G', 4.0)
    for fx_ in (248, 270, 390, 412):                                        # flagpoles with plain pennants
        p.put(p.box(fx_, 138, fx_ + 1, 162), 'I', 4.0)
        p.put(p.poly([(fx_ + 1, 139), (fx_ + 10, 141), (fx_ + 1, 144)]), 'C', 7.4)
    LAYOUT['d4_dome'] = [330, 104]


def _station(p, cty):
    """The station: the arched glass end wall of the hall (backlit by the rising sun) and its tower."""
    yy, xx = p.yy, p.xx
    hall = p.poly([(530, 238), (530, 178), (542, 162), (560, 152), (584, 148), (608, 152), (628, 162), (640, 172),
                   (640, 238)])
    p.put(hall, 'C', 3.4 + np.clip((xx - 530) / 110, 0, 1) * 1.0)
    glass = p.poly([(538, 232), (538, 182), (548, 168), (563, 159), (584, 155), (605, 159), (621, 168), (632, 180),
                    (632, 232)])
    p.put(glass, 'S', 8.6 + np.clip((xx - 538) / 94, 0, 1) * 2.8 - np.clip((yy - 155) / 77, 0, 1) * 2.4)
    mull = glass & (((xx.astype(int) - 538) % 8 == 0) | ((yy.astype(int) - 155) % 10 == 0))
    p.put(mull, 'I', 3.0 + np.clip((yy - 155) / 77, 0, 1) * 1.2)
    for k in range(6):                                                    # the lamps of the hall shining through
        p.put(p.box(548 + k * 15, 214, 550 + k * 15, 216), 'L', 4.0, emis=True)
    cty.snow_cap(hall, 7.0, depth=2)
    p.put(p.box(530, 232, 640, 238), 'C', 4.4)
    for k in range(5):
        p.put(p.box(536 + k * 22, 226, 548 + k * 22, 238), 'N', 1.4)       # the openings where the tracks run in
    ct = p.box(508, 118, 524, 238)
    p.put(ct, 'C', 4.0)
    p.put(ct & ~shift(ct, 1, 0), 'C', 6.6)
    p.put(ct & ~shift(ct, -1, 0), 'C', 2.8)
    for yv in range(128, 232, 14):
        p.put(p.box(514, yv, 518, yv + 6), 'L', 2.8, emis=True)
    cap = p.poly([(506, 119), (516, 100), (526, 119)])
    p.put(cap, 'P', 2.4 + np.clip((xx - 506) / 20, 0, 1) * 2.0)
    cty.snow_cap(cap, 7.0)
    p.put(p.box(515, 92, 516, 100), 'I', 4.0)
    p.put(p.poly([(516, 92), (523, 94), (516, 96)]), 'C', 7.4)


# =========================================================================== city
def d4_city():
    """Veltrava from the river at dawn: far rank (castle hill, cathedral, palais dome, onion church, town hall,
    station hall), the old town, the quay rank with lamps, the quay wall and the water beyond the bridge."""
    h = H['city']
    R = ramps()
    p = C.Paint(VW, h, R, 'd4_city')
    yy, xx = p.yy, p.xx
    rng = np.random.default_rng(1410)
    cty = City(p, rng)
    east = _east(xx)
    _hill(p, cty)
    _cathedral(p, cty)
    _palais(p, cty)
    # the onion church and the town hall tower with its lit clock
    cty.house(434, 214, 30, 30, 'hip', 0.66, lit_p=0.2, chimney=False, ramp='N')
    cty.tower(442, 188, 14, 24, 'onion', 0.6)
    cty.tower(476, 220, 18, 104, 'copper', 0.6, clock=True)
    _station(p, cty)
    # ---------------------------------------------------------------- the old town (middle rank, lighter)
    x = -4
    i = 0
    walls = ['N', 'C', 'N', 'K', 'C', 'N']
    while x < VW + 4:
        w = int(rng.uniform(14, 30))
        if 236 <= x <= 420:
            hh = int(rng.uniform(10, 18))          # low in front of the palais so its front reads
        elif 506 <= x <= 640:
            hh = int(rng.uniform(10, 16))
        else:
            hh = int(rng.uniform(18, 34))
        kind = ['gable', 'mansard', 'hip', 'gable', 'step', 'mansard', 'flat'][int(rng.integers(0, 7))]
        ramp = walls[i % len(walls)]
        wall = {'N': 2.6, 'C': 2.4, 'K': 1.6}[ramp]
        cty.house(x, 230 + int(rng.integers(-2, 3)), w, hh, kind, 0.36, lit_p=0.42, seed=i, ramp=ramp, wall=wall)
        x += w + int(rng.integers(0, 3))
        i += 1
    # ---------------------------------------------------------------- the quay rank (near, dark, many lit windows)
    x = -6
    while x < VW + 6:
        w = int(rng.uniform(18, 32))
        hh = int(rng.uniform(16, 28))
        kind = ['mansard', 'gable', 'hip', 'flat', 'mansard', 'step'][int(rng.integers(0, 6))]
        ramp = ['N', 'K', 'N', 'C'][int(rng.integers(0, 4))]
        wall = {'N': 1.4, 'C': 1.2, 'K': 1.0}[ramp]
        cty.house(x, QUAY_Y - 10, w, hh, kind, 0.08, lit_p=0.5, seed=60 + i, ramp=ramp, wall=wall, door=True)
        x += w + int(rng.integers(0, 2))
        i += 1
    # arcade / shopfronts along the quay street (lit, awnings with snow)
    p.put(p.box(0, QUAY_Y - 10, VW, QUAY_Y - 6), 'N', 1.4)
    for k in range(0, VW, 13):
        on = (k // 13) % 3 != 1
        p.put(p.box(k + 3, QUAY_Y - 10, k + 9, QUAY_Y - 6), 'L' if on else 'N', 2.6 if on else 1.0, emis=on)
        p.put(p.box(k + 2, QUAY_Y - 11, k + 10, QUAY_Y - 10), 'W', 5.6)
    # quay street with tram rails, lamps, railing; quay wall into the water
    street = p.box(0, QUAY_Y - 6, VW, QUAY_Y)
    p.put(street, 'W', 3.4 + (pg.value_noise(VW, h, 7, 1412, 2) - 0.5) * 0.6)
    p.put(p.box(0, QUAY_Y - 4, VW, QUAY_Y - 3), 'I', 3.0)                  # tram rails
    p.put(p.box(0, QUAY_Y - 6, VW, QUAY_Y - 5), 'W', 4.8)
    for k in range(0, VW, 3):
        p.put(p.box(k, QUAY_Y - 2, k + 1, QUAY_Y), 'I', 1.8)
    p.put(p.box(0, QUAY_Y - 2, VW, QUAY_Y - 1), 'I', 2.6)
    for k in range(0, VW, 23):                                              # tram wire poles
        p.put(p.box(k, QUAY_Y - 26, k + 1, QUAY_Y - 5), 'I', 1.2)
    p.put(p.box(0, QUAY_Y - 24, VW, QUAY_Y - 23), 'I', 1.0)                 # the overhead wire
    quay_lamps = list(range(18, VW, 46))
    for lx in quay_lamps:
        p.put(p.box(lx, QUAY_Y - 18, lx + 1, QUAY_Y - 2), 'I', 1.4)
        p.put(p.box(lx - 1, QUAY_Y - 21, lx + 2, QUAY_Y - 18), 'L', 4.4, emis=True)
        p.put(p.box(lx, QUAY_Y - 22, lx + 1, QUAY_Y - 21), 'W', 6.0)
    wallq = p.box(0, QUAY_Y, VW, QUAY_Y + 10)
    p.put(wallq, 'I', 2.6 + (pg.value_noise(VW, h, 5, 1413, 2) - 0.5) * 0.8 + east * 0.6)
    p.put(wallq & ((yy.astype(int) - QUAY_Y) % 4 == 0), 'I', 2.0)
    p.put(p.box(0, QUAY_Y, VW, QUAY_Y + 1), 'W', 5.6)
    for k in range(9, VW, 37):                                              # steps down to the water
        p.put(p.box(k, QUAY_Y + 2, k + 6, QUAY_Y + 10) & ((yy.astype(int) % 2) == 0), 'W', 4.4)
    # the river beyond the bridge: dark water, the quay lamps and the dawn mirrored in streaks; floating ice
    water = p.box(0, QUAY_Y + 10, VW, h)
    wn = pg.value_noise(VW, h, 18, 1414, 2)
    p.put(water, 'Q', 2.6 + east * 3.0 + (wn - 0.5) * 0.8 - np.clip((yy - 262) / 200, 0, 1) * 0.6)
    rip = water & (np.sin(yy * 2.1 + wn * 8 + xx * 0.03) > 0.75)
    p.add(rip, 0.9)
    for lx in quay_lamps:
        stk = water & (np.abs(xx - lx) < 1.0) & ((yy.astype(int) + lx) % 3 != 0) & (yy < QUAY_Y + 34)
        p.put(stk, 'L', 1.8)
    p.put(water & (yy < QUAY_Y + 12), 'Q', 1.4)
    rng2 = np.random.default_rng(1415)
    for _ in range(24):
        fx = rng2.uniform(0, VW)
        fy = rng2.uniform(268, h - 4)
        fw = rng2.uniform(6, 22) * (0.6 + (fy - 262) / 300)
        fh = max(1.0, fw * 0.18)
        floe = p.ell(fx, fy, fw / 2, fh)
        p.put(floe & water, 'W', 3.6 + east[0, int(fx) % VW] * 1.4)
        p.put(floe & water & ~shift(floe, 0, -1), 'W', 5.6)
    p.resolve(band=2.6)
    LAYOUT['d4_lit_windows'] = cty.lit_windows
    chims = [c for c in cty.chimneys if c[1] > 120]
    chims.sort(key=lambda c: (c[0] * 7919) % 641)
    LAYOUT['d4_chimneys'] = chims[:24]
    LAYOUT['d4_quay_lamps'] = quay_lamps
    LAYOUT['d4_quay_y'] = QUAY_Y
    return p.L


# =========================================================================== bridge + river
def d4_bridge():
    """The bridge behind the trains (far railing, deck, far track), its spandrel wall and three arches (open:
    the far quay shows through them), the piers with cutwaters, and the river in front: the open channel
    mirroring the dawn, ice sheets from both banks, floes, cracks and wind-blown snow."""
    h = H['bridge']
    R = ramps()
    p = C.Paint(VW, h, R, 'd4_bridge')
    yy, xx = p.yy, p.xx
    east = _east(xx)
    # far railing: top bar, balusters, bottom bar; lamp posts on the far side
    p.put(p.box(0, 272, VW, 273), 'I', 4.8 + east * 1.2)
    p.put(p.box(0, 271, VW, 272), 'W', 6.4)
    rail = p.box(0, 273, VW, 279) & ((xx.astype(int) % 6) == 2)
    p.put(rail, 'I', 1.6)
    p.put(p.box(0, 277, VW, 278), 'I', 2.2)
    deck = p.box(0, 279, VW, PARAPET_Y + 9)
    p.put(deck, 'W', 3.2 + (pg.value_noise(VW, h, 9, 1430, 2) - 0.5) * 0.9)
    p.put(p.box(0, DE_RAIL - 1, VW, DE_RAIL), 'I', 5.6)
    p.put(p.box(0, DE_RAIL, VW, DE_RAIL + 1), 'I', 1.4)
    for k in range(0, VW, 5):                                                # sleepers of the far track
        p.put(p.box(k, DE_RAIL + 1, k + 3, DE_RAIL + 2), 'I', 2.0)
    for k in range(10, VW, 92):                                              # catenary-free: signal posts
        p.put(p.box(k, 252, k + 1, 279), 'I', 1.6)
        p.put(p.box(k - 1, 250, k + 2, 253), 'I', 2.2)
        p.put(p.box(k, 251, k + 1, 252), 'T', 4.0)
    # spandrel wall and arches (openings transparent)
    p.put(p.box(0, 294, VW, 297), 'I', 4.4 + east * 1.0)
    p.put(p.box(0, 296, VW, 297), 'I', 2.0)
    wall = p.box(0, 297, VW, WATER_Y + 6)
    stone = pg.value_noise(VW, h, 7, 1431, 2)
    p.put(wall, 'I', 2.6 + (stone - 0.5) * 0.9 - np.clip((yy - 297) / 50, 0, 1) * 0.6 + east * 0.7)
    p.add(wall & ((yy.astype(int) % 6) == 0), -0.5)
    p.add(wall & (((xx.astype(int) + (yy.astype(int) // 6) * 7) % 14) == 0), -0.4)
    holes = np.zeros((h, VW), bool)
    for (a, b) in ARCHES:
        cx = (a + b) / 2
        op = p.ell(cx, ARCH_CY, (b - a) / 2, ARCH_RY) & (yy < WATER_Y)
        holes |= op
        ring = kit.dilate(op, 2) & ~op & (yy < ARCH_CY + 10)
        p.put(ring, 'I', 1.2)
        p.put(ring & (xx > cx) & (yy < ARCH_CY - 16), 'I', 4.4 + east * 0.8)
        for k in range(-6, 7):                                                     # voussoir joints
            ang = math.pi / 2 + k * 0.22
            x1 = cx + math.cos(ang) * ((b - a) / 2 + 2)
            y1 = ARCH_CY - math.sin(ang) * (ARCH_RY + 2)
            x0_ = cx + math.cos(ang) * ((b - a) / 2 - 1)
            y0_ = ARCH_CY - math.sin(ang) * (ARCH_RY - 1)
            p.put(p.line([(x0_, y0_), (x1, y1)], 0.4) & ring, 'I', 0.6)
        key = p.box(cx - 3, 301, cx + 3, 307) & ~op
        p.put(key, 'I', 5.0)
        # the soffit: the underside of the vault seen inside the opening's top
        soffit = op & ~shift(op, 0, -3) & (yy < ARCH_CY - 10)
        p.put(soffit, 'I', 1.0)
        # icicles hanging from the arch ring
        for ix in range(int(a) + 8, int(b) - 8, 7):
            top_y = int(ARCH_CY - ARCH_RY * math.sqrt(max(0.0, 1 - ((ix - cx) / ((b - a) / 2)) ** 2)))
            ln = 2 + (ix * 7) % 5
            p.put(p.box(ix, top_y, ix + 1, top_y + ln) & op, 'W', 6.6)
    for (a, b) in ((220, 236), (404, 420)):
        pier = p.box(a, 304, b, WATER_Y + 10)
        p.put(pier, 'I', 2.0 + np.clip((xx - a) / (b - a), 0, 1) * 1.8)
        cw = p.poly([(a - 5, WATER_Y + 10), (a - 5, 328), ((a + b) / 2, 314), (b + 5, 328), (b + 5, WATER_Y + 10)])
        p.put(cw, 'I', 1.8 + np.clip((xx - a + 5) / (b - a + 10), 0, 1) * 1.8)
        p.put(p.box(a - 6, WATER_Y - 2, b + 6, WATER_Y + 1), 'W', 3.8)
        p.put(cw & ~shift(cw, 0, -1), 'W', 6.0)
    # ---- the river in front of the bridge: dark open water, the bridge's shadow, short dawn streaks
    water = p.box(0, WATER_Y, VW, h)
    wn = pg.value_noise(VW, h, 22, 1432, 3)
    chan = np.clip(1 - np.abs(xx - 430) / 260, 0, 1)
    wt = 2.2 + chan * 1.6 + east * 1.4 + (wn - 0.5) * 0.6 - np.clip((yy - WATER_Y) / 110, 0, 1) * 0.9
    wt -= np.clip(1 - (yy - WATER_Y) / 18, 0, 1) * 1.2                                 # under the bridge
    p.put(water, 'Q', wt)
    rngs = np.random.default_rng(1441)
    for _ in range(420):
        u = rngs.random() ** 1.6
        sy = int(WATER_Y + 4 + u * 110)
        sx = rngs.uniform(0, VW)
        ln = int(2 + rngs.random() * 12 * (1 - u * 0.7))
        e = float(np.clip((sx - 140) / 500.0, 0, 1))
        c = float(np.clip(1 - abs(sx - 430) / 260, 0, 1))
        if rngs.random() > 0.35 + c * 0.5:
            continue
        seg = p.box(sx, sy, sx + ln, sy + 1)
        if e > 0.45 and rngs.random() < 0.7:
            p.put(seg & water, 'D', 0.8 + e * 2.6 * (1 - u * 0.6))
        else:
            p.put(seg & water, 'Q', 4.2 + c * 1.6 - u * 1.4)
    for (a, b) in ARCHES:
        cx = (a + b) / 2
        mir = p.ell(cx, 2 * WATER_Y - ARCH_CY + 6, (b - a) / 2, ARCH_RY) & water & (yy < WATER_Y + 24)
        p.add(mir & ((yy.astype(int) + xx.astype(int) // 5) % 3 != 0), -0.9)
    for lx in PARAPET_LAMPS:
        stk = water & (np.abs(xx - lx) < 1.0) & ((yy.astype(int) * 2 + lx) % 5 < 2) & (yy < WATER_Y + 30)
        p.put(stk, 'L', 0.8 + np.clip(1 - (yy - WATER_Y) / 30, 0, 1) * 1.6)
    rngi = np.random.default_rng(1435)
    edge_l = 92 + np.cumsum(rngi.normal(0, 2.2, h)).astype(np.float32) * 0.5
    edge_r = 566 + np.cumsum(rngi.normal(0, 2.0, h)).astype(np.float32) * 0.5
    sheet_l = water & (xx < edge_l[:, None] + np.clip((yy - WATER_Y) * 0.25, 0, 60))
    sheet_r = water & (xx > edge_r[:, None] - np.clip((yy - WATER_Y) * 0.2, 0, 50))
    near_band = water & (yy > 468 + (pg.value_noise(VW, 4, 40, 1436, 2)[0] * 14)[None, :].astype(int))
    ice = sheet_l | sheet_r | near_band
    for _ in range(12):
        fx = rngi.uniform(140, 560)
        fy = rngi.uniform(WATER_Y + 8, 420)
        fw = rngi.uniform(8, 30) * (0.7 + (fy - WATER_Y) / 160)
        fh = fw * rngi.uniform(0.16, 0.3)
        pts = [(fx - fw / 2 + rngi.uniform(-2, 2), fy + rngi.uniform(-1, 1)),
               (fx + rngi.uniform(-3, 3), fy - fh), (fx + fw / 2 + rngi.uniform(-2, 2), fy + rngi.uniform(-1, 1)),
               (fx + rngi.uniform(-3, 3), fy + fh)]
        ice |= p.poly(pts) & water
    it = 3.0 + np.clip((yy - WATER_Y) / 120, 0, 1) * 0.9 + east * 1.4 + (wn - 0.5) * 0.9
    p.put(ice, 'W', it)
    patches = ice & (pg.value_noise(VW, h, 7, 1442, 3) > 0.56)                            # wind-packed snow
    p.add(patches, 0.8)
    wet = ice & kit.dilate(water & ~ice, 2)                                             # dark wet rim at open water
    p.add(wet, -1.2)
    p.put(ice & ~shift(ice, 0, -1), 'W', it + 1.4)
    p.put(ice & ~shift(ice, 0, 1) & water, 'Q', 1.0)
    for _ in range(10):                                                                # pressure ridges
        rx0 = rngi.uniform(0, VW)
        ry0 = rngi.uniform(WATER_Y + 20, h - 20)
        pts = [(rx0, ry0)]
        for _k in range(4):
            pts.append((pts[-1][0] + rngi.uniform(8, 16) * (1 if rx0 < 320 else -1), pts[-1][1] + rngi.uniform(-2, 2)))
        rd = p.line(pts, 0.6) & ice
        p.put(rd, 'W', 6.2)
        p.put(shift(rd, 0, -1) & ice & ~rd, 'W', 2.6)
    for _ in range(26):
        cx0 = rngi.uniform(0, VW)
        cy0 = rngi.uniform(WATER_Y + 4, h - 10)
        pts = [(cx0, cy0)]
        for _k in range(5):
            pts.append((pts[-1][0] + rngi.uniform(-12, 12), pts[-1][1] + rngi.uniform(-3, 3)))
        cr = p.line(pts, 0.4) & ice & kit.erode(ice, 1)
        p.add(cr, -1.6)
    # a fishing hole with its little wind screen on the western sheet, a sled track across the eastern one
    p.put(p.ell(70, 392, 4, 1.4), 'Q', 1.0)
    p.put(p.box(76, 384, 78, 392), 'I', 2.2)
    p.put(p.box(78, 385, 86, 392), 'T', 3.6)
    p.put(p.line([(600, 360), (590, 380), (606, 404), (598, 430)], 0.4) & ice, 'W', 2.4)
    p.put(p.line([(604, 360), (594, 380), (610, 404), (602, 430)], 0.4) & ice, 'W', 2.4)
    p.L.rid[holes] = -1
    p.resolve(band=2.6)
    glints = []
    rngg = np.random.default_rng(1438)
    for _ in range(60):
        gx = int(rngg.uniform(200, 620))
        gy = int(rngg.uniform(WATER_Y + 3, WATER_Y + 70))
        if not ice[gy, gx]:
            glints.append([gx, gy, int(rngg.integers(1, 4))])
    LAYOUT['d4_glints'] = glints
    return p.L


def d4_parapet():
    """The near parapet in front of the trains: stone, snow on the coping, seven lanterns (lit)."""
    h = H['bridge']
    R = ramps()
    p = C.Paint(VW, h, R, 'd4_parapet')
    yy, xx = p.yy, p.xx
    east = _east(xx)
    par = p.box(0, PARAPET_Y, VW, 294)
    st = pg.value_noise(VW, h, 6, 1440, 2)
    p.put(par, 'I', 2.8 + (st - 0.5) * 0.8 + east * 0.9)
    p.put(par & ((xx.astype(int) % 12) == 0), 'I', 1.4)
    p.put(p.box(0, PARAPET_Y, VW, PARAPET_Y + 1), 'W', 6.2 + east * 1.0)
    p.put(p.box(0, PARAPET_Y + 1, VW, PARAPET_Y + 2), 'I', 5.2)
    p.put(p.box(0, 293, VW, 294), 'I', 1.4)
    for lx in PARAPET_LAMPS:
        p.put(p.box(lx - 2, PARAPET_Y - 2, lx + 3, PARAPET_Y + 1), 'I', 1.6)
        p.put(p.box(lx, PARAPET_Y - 22, lx + 1, PARAPET_Y - 1), 'I', 1.4)
        p.put(p.box(lx - 1, PARAPET_Y - 24, lx + 2, PARAPET_Y - 22), 'I', 2.0)
        p.put(p.box(lx - 2, PARAPET_Y - 30, lx + 3, PARAPET_Y - 24), 'L', 3.4, emis=True)
        p.put(p.box(lx - 1, PARAPET_Y - 28, lx + 2, PARAPET_Y - 25), 'L', 4.8, emis=True)
        p.put(p.box(lx - 2, PARAPET_Y - 31, lx + 3, PARAPET_Y - 30), 'I', 3.2)
        p.put(p.box(lx - 1, PARAPET_Y - 32, lx + 2, PARAPET_Y - 31), 'W', 6.0)
        p.put(p.box(lx - 3, PARAPET_Y - 30, lx - 2, PARAPET_Y - 24), 'I', 2.6)
        p.put(p.box(lx + 3, PARAPET_Y - 30, lx + 4, PARAPET_Y - 24), 'I', 2.6)
    p.resolve(band=2.6)
    return p.L


def d4_lamp_glow():
    """Additive halos of the parapet lanterns and the quay lamps' warmth on the deck (bridge plane)."""
    h = H['bridge']
    yy, xx = np.mgrid[0:h, 0:VW].astype(np.float32)
    a = np.zeros((h, VW, 3), np.float32)
    for lx in PARAPET_LAMPS:
        d = np.hypot((xx + 0.5 - lx - 0.5) / 15.0, (yy + 0.5 - (PARAPET_Y - 27)) / 11.0)
        g = np.clip(1 - d, 0, 1) ** 1.5
        for c, v in enumerate((64, 40, 18)):
            a[..., c] += g * v
    return K.soft_quant(a, 6.0)


def d4_sun_glow():
    """Additive warmth of the low sun and the dawn band (sky plane); the runtime fades it in with the crane."""
    h = H['sky']
    yy, xx = np.mgrid[0:h, 0:VW].astype(np.float32)
    a = np.zeros((h, VW, 3), np.float32)
    d = np.hypot((xx - SUN[0]) / 120.0, (yy - SUN[1]) / 70.0)
    g = np.clip(1 - d, 0, 1) ** 1.6
    band = np.clip(1 - np.abs(yy - (SUN[1] + 8)) / 70, 0, 1) ** 1.8 * np.clip((xx - 200) / 440, 0, 1)
    for c, v in enumerate((90, 56, 30)):
        a[..., c] += g * v + band * v * 0.45
    return K.soft_quant(a, 6.0)


def d4_dome_glow():
    """Additive first sun on the palais dome and the station roof (city plane)."""
    h = H['city']
    yy, xx = np.mgrid[0:h, 0:VW].astype(np.float32)
    a = np.zeros((h, VW, 3), np.float32)
    d = np.hypot((xx - 352) / 34.0, (yy - 100) / 30.0)
    g = np.clip(1 - d, 0, 1) ** 1.4 * (xx > 330)
    d2 = np.hypot((xx - 600) / 60.0, (yy - 160) / 26.0)
    g2 = np.clip(1 - d2, 0, 1) ** 1.6
    for c, v in enumerate((70, 46, 22)):
        a[..., c] += g * v + g2 * v * 0.8
    return K.soft_quant(a, 6.0)


# =========================================================================== near bank
def d4_bank():
    """The near bank (foreground of the low start): snow slope with its blue shadow, the promenade path, the
    iron fence along the crest, a bench, a dark lamp, reeds, a rowing boat frozen in at the left, a mooring
    bollard, footprints and sled tracks, and the bare willow at the right reaching over the river."""
    h = H['bank']
    R = ramps()
    p = C.Paint(VW, h, R, 'd4_bank')
    yy, xx = p.yy, p.xx
    east = _east(xx)
    bank_top = BANK_TOP + (C.wrap_noise(VW, 1, 70, 1450)[0] * 7).astype(int)
    bank = yy >= bank_top[None, :]
    sn = pg.value_noise(VW, h, 14, 1451, 2)
    p.put(bank, 'W', 3.6 + (sn - 0.5) * 0.8 - np.clip((yy - BANK_TOP - 6) / 40, 0, 1) * 1.6 + east * 0.5)
    p.put(bank & ~shift(bank, 0, 1), 'W', 6.6 + east * 1.0)
    p.put(bank & shift(bank, 0, 1) & ~shift(bank, 0, 2), 'W', 5.6)
    path_y = BANK_TOP + 12
    path = bank & (yy > path_y) & (yy < path_y + 6)
    p.put(path, 'W', 2.8 + (sn - 0.5) * 0.6)
    trod = path & (((xx.astype(int) * 7 + yy.astype(int) * 3) % 11) < 2)
    p.add(trod, -0.8)
    p.put(bank & (yy >= path_y + 6) & (yy < path_y + 7), 'W', 4.8)
    # the lower slope: drifts and a long blue shadow, footprints across it
    drift = bank & (yy > path_y + 7) & (np.sin(xx * 0.05 + sn * 6 + yy * 0.2) > 0.75)
    p.add(drift, 0.8)
    for k in range(24):
        fx = 120 + k * 17 + (k % 2) * 4
        fy = path_y + 12 + (k * 13) % 30
        p.put(p.box(fx, fy, fx + 2, fy + 1), 'W', 2.4)
    p.put(bank & (yy > path_y + 50), 'W', 2.6 + (sn - 0.5) * 0.6)
    rng = np.random.default_rng(1452)
    for _ in range(22):                                                        # reeds at the waterline
        rx = int(rng.uniform(10, 600))
        base = int(bank_top[rx])
        for k in range(int(rng.integers(3, 8))):
            hh = int(rng.uniform(5, 14))
            dx = rng.uniform(-3, 3)
            p.put(p.line([(rx + dx, base + 2), (rx + dx + rng.uniform(-2, 2), base - hh)], 0.4), 'T',
                  float(rng.uniform(1.0, 5.0)))
    # promenade fence along the crest
    for fx in range(6, 586, 14):
        top_y = int(bank_top[min(VW - 1, fx)]) + 1
        p.put(p.box(fx, top_y - 8, fx + 1, top_y + 1), 'N', 1.4)
        p.put(p.box(fx, top_y - 9, fx + 1, top_y - 8), 'W', 6.0)
    for fx in range(6, 586):
        ty_ = int(bank_top[fx]) - 7 + int(round(0.8 * math.sin(math.pi * ((fx - 6) % 14) / 14)))
        p.put(p.box(fx, ty_, fx + 1, ty_ + 1), 'N', 2.0)
        if fx % 3 == 0:
            p.put(p.box(fx, ty_ - 1, fx + 1, ty_), 'W', 5.4)
    bx0 = 214
    by0 = int(bank_top[bx0]) + 1
    p.put(p.box(bx0, by0 - 7, bx0 + 18, by0 - 6), 'T', 4.4)                          # bench back
    p.put(p.box(bx0, by0 - 3, bx0 + 18, by0 - 2), 'T', 3.6)                          # seat
    p.put(p.box(bx0, by0 - 4, bx0 + 18, by0 - 3), 'W', 6.6)                          # snow on the seat
    p.put(p.box(bx0, by0 - 8, bx0 + 18, by0 - 7), 'W', 6.6)
    for lg in (bx0 + 1, bx0 + 16):
        p.put(p.box(lg, by0 - 2, lg + 1, by0 + 2), 'N', 1.2)
    lp = 472
    lpy = int(bank_top[lp]) + 1
    p.put(p.box(lp, lpy - 34, lp + 1, lpy + 1), 'N', 1.2)
    p.put(p.box(lp - 2, lpy - 39, lp + 3, lpy - 34), 'N', 1.8)
    p.put(p.box(lp - 1, lpy - 38, lp + 2, lpy - 35), 'L', 1.2)
    p.put(p.box(lp - 2, lpy - 40, lp + 3, lpy - 39), 'W', 6.0)
    # the rowing boat frozen in at the left (in the ice below the crest), with a snow load
    boat = p.poly([(18, BANK_TOP - 6), (66, BANK_TOP - 6), (60, BANK_TOP + 1), (24, BANK_TOP + 1)])
    p.put(boat, 'T', 2.0 + np.clip((xx - 18) / 48, 0, 1) * 1.2)
    p.put(p.box(20, BANK_TOP - 7, 64, BANK_TOP - 5), 'W', 6.4)
    p.put(boat & ~shift(boat, 0, 1), 'N', 1.0)
    p.put(p.line([(66, BANK_TOP - 6), (80, BANK_TOP - 2)], 0.4), 'N', 2.4)              # the mooring rope
    p.put(p.box(80, BANK_TOP - 6, 83, BANK_TOP + 2), 'I', 2.2)                          # bollard
    p.put(p.box(80, BANK_TOP - 7, 83, BANK_TOP - 6), 'W', 6.4)
    # the willow: a leaning trunk at the right edge, its crown over the river, long hanging twigs
    trunk = p.poly([(588, h), (596, 560), (598, 528), (592, 500), (586, 478), (594, 476), (604, 500), (610, 530),
                    (612, 560), (618, h)])
    p.put(trunk, 'N', 1.2 + np.clip((xx - 588) / 30, 0, 1) * 1.4)
    p.put(trunk & ~shift(trunk, 1, 0), 'D', 1.8)
    p.put(trunk & ((yy.astype(int) * 3 + xx.astype(int)) % 9 == 0), 'N', 0.6)          # bark furrows
    limbs = (((590, 480), (570, 452), (548, 436), (520, 430)), ((592, 478), (596, 448), (590, 420)),
             ((596, 482), (622, 458), (646, 446)), ((570, 452), (560, 432)), ((596, 448), (608, 428)),
             ((548, 436), (536, 426)), ((520, 430), (502, 436)))
    tips = []
    for pts in limbs:
        br = p.line(list(pts), 0.9 if pts[0][1] > 470 else 0.6)
        p.put(br, 'N', 1.0)
        p.put(br & ~shift(br, 0, 1), 'W', 4.6)
        tips += [pts[-1], ((pts[0][0] + pts[-1][0]) / 2, (pts[0][1] + pts[-1][1]) / 2)]
    rngw = np.random.default_rng(1453)
    for (tx, ty) in tips:
        for k in range(5):
            ox = tx + rngw.uniform(-10, 10)
            oy = ty + rngw.uniform(-4, 4)
            ln = rngw.uniform(14, 34)
            sway = rngw.uniform(-3, 3)
            tw = p.line([(ox, oy), (ox + sway * 0.4, oy + ln * 0.5), (ox + sway, oy + ln)], 0.3)
            p.put(tw, 'T', float(rngw.uniform(1.0, 2.6)))
    # snow-laden bushes along the crest
    for (bx, bw) in ((120, 10), (164, 7), (300, 12), (356, 8), (418, 11), (520, 9)):
        by = int(bank_top[bx]) + 2
        bm = p.ell(bx, by - bw * 0.35, bw * 0.6, bw * 0.4)
        p.put(bm, 'T', 1.8)
        p.put(bm & ~shift(bm, 0, -2), 'W', 6.0)
    p.resolve(band=2.6)
    LAYOUT['d4_walker_y'] = WALKER_Y
    return p.L


# =========================================================================== small sprites
def d4_tram():
    """A two-axle tram (cream and red, lit windows) running along the quay street; 2 frames (trolley spark)."""
    fw, fh = 34, 18
    sheet = np.zeros((fh, fw * 2, 4), np.uint8)
    R = ramps()
    for fr in range(2):
        p = C.Paint(fw, fh, R, 'd4_tram')
        yy, xx = p.yy, p.xx
        body = p.rr(2, 6, 32, 16, 1)
        p.put(body, 'C', 5.6)
        p.put(p.box(2, 12, 32, 16) & body, 'R', 2.0)
        p.put(p.box(2, 6, 32, 7), 'C', 7.0)
        p.put(p.box(3, 5, 31, 6), 'W', 6.6)
        for k in range(5):
            p.put(p.box(5 + k * 5, 8, 8 + k * 5, 11), 'L', 4.0 + (k % 2) * 0.6, emis=True)
        p.put(p.box(2, 8, 3, 11) | p.box(31, 8, 32, 11), 'L', 5.4, emis=True)        # end windows
        p.put(p.box(6, 16, 9, 18) | p.box(25, 16, 28, 18), 'N', 1.0)
        p.put(p.line([(16, 5), (24, 0)], 0.4), 'I', 3.0)
        if fr == 1:
            p.put(p.box(24, 0, 25, 1), 'L', 6.0, emis=True)
        p.put(p.box(1, 13, 2, 14), 'L', 5.6, emis=True)                                  # head lamp
        p.resolve(band=2.0)
        sheet[:, fr * fw:(fr + 1) * fw] = p.L.c
    LAYOUT['d4_tram'] = {'w': fw, 'h': fh, 'frames': 2, 'y': QUAY_Y - 6 - fh + 2}
    return sheet


def d4_gull():
    """A gull / crow in four wing frames (7 x 5) for the flocks over the city."""
    fw, fh = 7, 5
    sheet = np.zeros((fh, fw * 4, 4), np.uint8)
    dark = pg.hx('#121A26')
    for fr, wing in enumerate([-2, -1, 0, 1]):
        o = fr * fw
        sheet[2, o + 2:o + 5] = dark
        for s in (-1, 1):
            for k in (1, 2, 3):
                y = 2 + (wing * k) // 2 if wing < 0 else 2 + (wing * k + 1) // 3
                x = o + 3 + s * k
                if 0 <= y < fh:
                    sheet[y, x] = dark
    return sheet


def preview(cam=1.0):
    """Composite the planes at crane position cam (0 = start, 1 = end) -> PNG in %TEMP%."""
    import os
    from PIL import Image
    sky = d4_sky().c
    city = d4_city().c
    br = d4_bridge().c
    par = d4_parapet().c
    bank = d4_bank().c
    img = np.zeros((360, VW, 3), np.float32)

    def over(layer, travel):
        y0 = int(round(-travel * (1 - cam)))
        part = np.zeros((360, VW, 4), np.uint8)
        src0 = -y0
        part[:] = layer[src0:src0 + 360]
        a = part[..., 3:4] / 255.0
        img[:] = part[..., :3] * a + img * (1 - a)
    over(sky, PLANES['sky'])
    over(city, PLANES['city'])
    over(br, PLANES['bridge'])
    over(par, PLANES['bridge'])
    over(bank, PLANES['bank'])
    out = os.path.join(os.environ.get('TEMP', '.'), 'd4_preview_%d.png' % int(cam * 100))
    Image.fromarray(img.astype(np.uint8)).save(out)
    print(out)


# =========================================================================== steam
def _puff_frames(n, fw, fh, r0, r1, cols, seed, light=(0.6, -0.8), thin_from=0.55):
    """Clean pixel-art steam puffs: round lobes in 4-5 flat tones lit from `light`, dithered only on the tone
    borders and (late frames) on the thinning outer edge."""
    sheet = np.zeros((fh, fw * n, 4), np.uint8)
    yy, xx = np.mgrid[0:fh, 0:fw].astype(np.float32)
    rgb = [pg.hx(c) for c in cols]
    lx, ly = light
    for i in range(n):
        u = i / max(1, n - 1)
        r = r0 + (r1 - r0) * u ** 0.8
        cx, cy = fw / 2, fh / 2 + (1 - u) * 2
        rng = np.random.default_rng(seed + i * 31)
        field = np.zeros((fh, fw), np.float32)
        shade = np.zeros((fh, fw), np.float32)
        lobes = [(0.0, 0.05, 0.7)]
        for k in range(7):
            ang = k / 7 * 2 * math.pi + rng.uniform(-0.3, 0.3)
            dist = rng.uniform(0.38, 0.6)
            lobes.append((math.cos(ang) * dist, math.sin(ang) * dist * 0.8 - 0.05, rng.uniform(0.38, 0.58)))
        for (ox, oy, rr) in lobes:
            lr = r * rr
            dx = (xx + 0.5 - cx - ox * r) / lr
            dy = (yy + 0.5 - cy - oy * r) / lr
            d2 = dx * dx + dy * dy
            inside = d2 < 1.0
            nz = np.sqrt(np.clip(1 - d2, 0, 1))
            lam = np.clip(dx * lx + dy * ly + nz * 0.55, -1, 1)
            upd = inside & (np.clip(1 - d2, 0, 1) >= field)
            shade = np.where(upd, lam, shade)
            field = np.maximum(field, np.where(inside, np.clip(1 - d2, 0, 1), 0))
        bay = pg.bayer(fw, fh, i * 2, i * 3)
        thin = max(0.0, (u - thin_from) / (1 - thin_from))
        keep = (field > 0) & ((field > thin * 0.9) | (field * 2.2 > bay + thin))
        if thin > 0:
            keep &= (field > bay * thin * 1.1)
        level = (shade * 0.5 + 0.5) * (len(rgb) - 1) * 1.05 - 0.5 - (1 - np.sqrt(field)) * 1.2 + (bay - 0.5) * 0.7
        idx = np.clip(np.round(level), 0, len(rgb) - 1).astype(int)
        frame = np.zeros((fh, fw, 4), np.uint8)
        for k, c in enumerate(rgb):
            sel = keep & (idx == k)
            frame[sel, :3] = c[:3]
            frame[sel, 3] = 255
        sheet[:, i * fw:(i + 1) * fw] = frame
    return sheet


def d4_steam():
    """Eight frames of locomotive steam (40 x 34): a dense young puff that grows, cools and thins; the dawn lights
    it from the east (upper right)."""
    n, fw, fh = 8, 40, 34
    sheet = _puff_frames(n, fw, fh, 6.0, 15.5, ['#4F5E70', '#687789', '#8593A3', '#A1AAB7', '#C2C9D2', '#E8DCD6'],
                         1460, light=(0.62, -0.78))
    LAYOUT['smoke'] = {'frames': n}
    return sheet


def d4_chimney_smoke():
    """Six frames of thin chimney smoke over the old town (14 x 12)."""
    n, fw, fh = 6, 14, 12
    sheet = _puff_frames(n, fw, fh, 2.0, 5.5, ['#4F5E70', '#687789', '#8593A3', '#A1AAB7'], 1470,
                         light=(0.6, -0.8), thin_from=0.35)
    LAYOUT['chimney_smoke'] = {'frames': n}
    return sheet


def _drift_frames(n, fw, fh, cols, seed, light=(0.3, -0.85), aspect=1.7, lobes=12, grow=(0.6, 1.0), thin=0.5):
    """AD round 2: soft drifting steam whose frames are one cloud at successive ages -- the same lobes in every
    frame, drifting apart and swelling a little, the rim thinning -- so the runtime can step (and cross-fade)
    through them without a puff jumping in shape or size (_cloud_frames draws unrelated clouds per frame)."""
    sheet = np.zeros((fh, fw * n, 4), np.uint8)
    yy, xx = np.mgrid[0:fh, 0:fw].astype(np.float32)
    rgb = [pg.hx(c) for c in cols]
    rng = np.random.default_rng(seed)
    L = []
    for k in range(lobes):
        L.append((rng.uniform(-0.32, 0.32), rng.uniform(-0.22, 0.18), rng.uniform(0.12, 0.22),
                  rng.uniform(0.8, 1.3), rng.uniform(-0.05, 0.05), rng.uniform(-0.04, 0.02)))
    for i in range(n):
        u = i / max(1, n - 1)
        sc = grow[0] + (grow[1] - grow[0]) * u
        dens = np.zeros((fh, fw), np.float32)
        lit = np.zeros((fh, fw), np.float32)
        for (ox, oy, rr, asp, dx, dy) in L:
            cx = fw * (0.5 + (ox + dx * u) * sc)
            cy = fh * (0.55 + (oy + dy * u) * sc)
            ry = fh * rr * sc
            rx = ry * aspect * asp
            g = np.exp(-(((xx - cx) / rx) ** 2 + ((yy - cy) / ry) ** 2))
            dens += g
            lit += g * np.clip(0.5 - (yy - cy) / (2.2 * ry) * light[1] * -1 + (xx - cx) / (3.0 * rx) * light[0], 0, 1)
        dens = np.clip(dens, 0, 1.6)
        shade = lit / np.maximum(dens, 1e-3)
        th = pg.bayer(fw, fh, 0, 0)                     # the same dither cells in every frame (no crawling)
        fade = 1.0 - thin * u
        keep = dens * fade > th * 0.55 + 0.12
        level = np.clip(shade, 0, 1) * (len(rgb) - 1) + (th - 0.5) * 0.6 - (1 - np.clip(dens, 0, 1)) * 0.8
        idx = np.clip(np.round(level), 0, len(rgb) - 1).astype(int)
        for k_, c in enumerate(rgb):
            sel = keep & (idx == k_)
            sheet[:, i * fw:(i + 1) * fw][sel, :3] = c[:3]
            sheet[:, i * fw:(i + 1) * fw][sel, 3] = 255
    return sheet


def _cloud_frames(n, fw, fh, cols, seed, light=(0.3, -0.85), aspect=1.7, lobes=12, grow=(0.55, 0.95), thin=0.5):
    """Soft drifting steam (platform steam, night steam): a cluster of elongated gaussian lobes whose density is
    ordered-dithered at the rim (solid core, airy edge), shaded light on top / dark below."""
    sheet = np.zeros((fh, fw * n, 4), np.uint8)
    yy, xx = np.mgrid[0:fh, 0:fw].astype(np.float32)
    rgb = [pg.hx(c) for c in cols]
    for i in range(n):
        u = i / max(1, n - 1)
        rng = np.random.default_rng(seed + i * 13)
        sc = grow[0] + (grow[1] - grow[0]) * u
        dens = np.zeros((fh, fw), np.float32)
        lit = np.zeros((fh, fw), np.float32)
        for k in range(lobes):
            cx = fw * (0.5 + rng.uniform(-0.32, 0.32) * sc)
            cy = fh * (0.55 + rng.uniform(-0.22, 0.18) * sc)
            ry = fh * rng.uniform(0.12, 0.22) * sc
            rx = ry * aspect * rng.uniform(0.8, 1.3)
            g = np.exp(-(((xx - cx) / rx) ** 2 + ((yy - cy) / ry) ** 2))
            dens += g
            lit += g * np.clip(0.5 - (yy - cy) / (2.2 * ry) * light[1] * -1 + (xx - cx) / (3.0 * rx) * light[0], 0, 1)
        dens = np.clip(dens, 0, 1.6)
        shade = lit / np.maximum(dens, 1e-3)
        th = pg.bayer(fw, fh, i * 2, i * 3)
        fade = 1.0 - thin * u
        keep = dens * fade > th * 0.55 + 0.12
        level = np.clip(shade, 0, 1) * (len(rgb) - 1) + (th - 0.5) * 0.6 - (1 - np.clip(dens, 0, 1)) * 0.8
        idx = np.clip(np.round(level), 0, len(rgb) - 1).astype(int)
        for k_, c in enumerate(rgb):
            sel = keep & (idx == k_)
            sheet[:, i * fw:(i + 1) * fw][sel, :3] = c[:3]
            sheet[:, i * fw:(i + 1) * fw][sel, 3] = 255
    return sheet
