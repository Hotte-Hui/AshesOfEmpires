"""env_berlin_room -- the main interior layer (walls, windows, archive shelving, floor) of M1.

Painted in tone space (env_berlin_kit.MLayer, 'archive' super-ramps), then baked with the scene
lights + volumetric window shafts and resolved to palette-pure RGBA.
"""
from __future__ import annotations

import math
import zlib

import numpy as np

import env_berlin_insignia as INS
import env_berlin_kit as kit
import env_berlin_layout as L
import pg

X = L.X

R = kit.archive_ramps()


# =========================================================================== helpers
def plaster_noise(w, h, seed):
    n = pg.value_noise(w, h, 22, seed, octaves=3)
    return (n - 0.5)


def molding(lay, x, y, w, profile, ramp='W', hbase=0.4):
    """Horizontal molding: profile = list of (tone, height) rows from top to bottom."""
    for i, (t, hh) in enumerate(profile):
        lay.rect(x, y + i, w, 1, ramp, t, hgt=hbase * hh, flat=True)


def bevel_box(lay, x, y, w, h, ramp, face, hi=None, lo=None, hgt=0.5, edge=1, flat=True):
    """Raised box: face tone, lighter top/left edge, darker bottom/right edge (+height)."""
    lay.rect(x, y, w, h, ramp, face, hgt=hgt, flat=flat)
    if hi is not None:
        lay.rect(x, y, w, edge, ramp, hi, hgt=hgt * 0.8, flat=True)
        lay.rect(x, y, edge, h, ramp, hi, hgt=hgt * 0.8, flat=True)
    if lo is not None:
        lay.rect(x, y + h - edge, w, edge, ramp, lo, hgt=hgt * 0.6, flat=True)
        lay.rect(x + w - edge, y, edge, h, ramp, lo, hgt=hgt * 0.6, flat=True)


def recess(lay, x, y, w, h, ramp, face, hgt=-0.4, shadow=None, light=None):
    """Sunken panel: dark top/left inner edge (shadow), light bottom/right inner edge."""
    lay.rect(x, y, w, h, ramp, face, hgt=hgt, flat=True)
    if shadow is not None:
        lay.rect(x, y, w, 1, ramp, shadow, hgt=hgt, flat=True)
        lay.rect(x, y, 1, h, ramp, shadow, hgt=hgt, flat=True)
    if light is not None:
        lay.rect(x, y + h - 1, w, 1, ramp, light, hgt=hgt, flat=True)
        lay.rect(x + w - 1, y + 1, 1, h - 1, ramp, light, hgt=hgt, flat=True)


def pseudo_text(lay, x, y, w, rows, ramp, tone, seed=0, gap=3, indent=True, rag=0.35):
    rng = np.random.default_rng(seed)
    for r in range(rows):
        xx = x + (2 if indent and r == 0 else 0)
        end = x + w - int(rng.random() * w * rag)
        while xx < end:
            wl = int(rng.integers(2, 7))
            lay.hline(xx, y + r * gap, min(wl, end - xx), ramp, tone, flat=True)
            xx += wl + 1


def poster_field(lay, hist: bool):
    """'AUFBAU 1964' poster, upper field: grey-black ground, pale technical rendering of the hall dome and the
    state emblem in front of it.  neutral: the fictional Reichssiegel disc; hist: the Reichsadler holding the
    wreathed swastika (pale print on the dark field)."""
    x, y, w, h = L.POSTER
    lay.rect(x + 1, y + 1, w - 2, 36, 'W', 2.0, hgt=0.12, flat=True)
    lay.vgrad(x + 1, y + 1, w - 2, 36, 'W', 2.4, 1.2, hgt=0.12)
    cx = x + w // 2
    for a in range(0, 181, 4):
        r = math.radians(a)
        lay.px(cx + int(round(math.cos(r) * 13)), y + 30 - int(round(math.sin(r) * 11)), 'P', 2.6)
    lay.hline(cx - 15, y + 30, 31, 'P', 2.6, flat=True)
    lay.hline(cx - 15, y + 34, 31, 'P', 2.2, flat=True)
    for k in range(-14, 15, 3):
        lay.vline(cx + k, y + 31, 3, 'P', 2.2, flat=True)
    lay.vline(cx, y + 15, 4, 'P', 2.6, flat=True)
    if hist:
        e = INS.eagle_masks(w - 4)
        eh, ew = e['size']
        ex, ey = x + 2, y + 2
        inner = np.zeros((eh, ew), bool)
        ys, xs = np.nonzero(e['wreath'] | e['swastika'])
        if len(ys):
            cyy, cxx = (ys.min() + ys.max()) / 2.0, (xs.min() + xs.max()) / 2.0
            rr = (xs.max() - xs.min()) / 2.0
            yy, xx = np.mgrid[0:eh, 0:ew]
            inner = ((yy - cyy) ** 2 + (xx - cxx) ** 2 <= rr * rr)
        lay.put(inner, ex, ey, 'P', 5.6, flat=True)                     # white disc inside the wreath
        lay.put(e['body'], ex, ey, 'P', 5.2, flat=True)
        lay.put(e['lines'], ex, ey, 'P', 3.4, flat=True)
        lay.put(e['eye'], ex, ey, 'I', 1.0, flat=True)
        lay.put(e['wreath'], ex, ey, 'P', 4.0, flat=True)
        lay.put(e['swastika'], ex, ey, 'I', 0.0, flat=True)
    else:
        disc, pillar = kit.reichssiegel_mask(15)
        lay.put(disc, cx - 7, y + 6, 'N', 0.0, flat=True)
        lay.put(pillar, cx - 7, y + 6, 'P', 6.0, flat=True)
    # torn top-right corner + pins (part of the site so both variants match)
    lay.rect(x + w - 4, y, 4, 2, 'W', 4.4, hgt=0.0, flat=True)
    lay.rect(x + w - 2, y + 2, 2, 1, 'W', 4.4, hgt=0.0, flat=True)
    for (px_, py_) in ((x + 1, y + 1), (x + w - 5, y + 2)):
        lay.px(px_, py_, 'A', 4.0, hgt=0.4)


# =========================================================================== room layer
class Room:
    def __init__(self, hist: bool = False):
        self.hist = hist           # paint the historical insignia variant (used to cut the _hist decals)
        self.lay = kit.MLayer(L.WORLD_W, L.WORLD_H, R, 'room')
        self.windows = []          # dicts with glass rect + glass mask
        self.lights = []           # baked lights (world coords)
        self.extra_floor = []
        self.decal_sites = {}      # insignia sites: name -> (x, y, w, h, painter(lay, hist))
        self.radio_pos = None
        self.regulator_pendulum = None
        self.hidden_floor_arc = None
        self.fanlight = None
        self.tube_station = None

    # ------------------------------------------------------------------ base
    def base(self):
        lay = self.lay
        W, H = L.WORLD_W, L.WORLD_H
        # wall field (plaster): dark under the ceiling, mid in the lower half, faint mottling
        y = np.arange(H, dtype=np.float32)[:, None]
        t = 3.1 + 1.75 * np.clip((y - 44) / 150, 0, 1) ** 0.9 - 0.4 * np.clip((y - 210) / 70, 0, 1)
        t = t + np.zeros((1, W), np.float32)
        t = t + plaster_noise(W, H, 3) * 0.3
        lay.put(np.ones((H, W), bool), 0, 0, 'W', t, hgt=0.0)
        # ceiling underside (seen from below): dark band with converging beams per room
        lay.vgrad(0, 0, W, L.CEIL, 'W', 1.6, 2.6, hgt=0.0)
        for (rx0, rx1) in (L.HALL, L.LIBRARY, L.OFFICE, L.ARCHIVE, L.LIGHTROOM, L.EMIL):
            vp = (rx0 + rx1) / 2
            step = 40
            for bx in range(rx0 + 20, rx1, step):
                for yy in range(0, L.CEIL):
                    f = (L.HORIZON - yy) / (L.HORIZON - L.CEIL)
                    xx = int(round(vp + (bx - vp) * f))
                    lay.rect(xx - 3, yy, 7, 1, 'W', 3.0, hgt=0.2, flat=True)
                    lay.rect(xx + 4, yy, 1, 1, 'W', 1.0, hgt=0.0, flat=True)
                    lay.rect(xx - 4, yy, 1, 1, 'W', 4.0, hgt=0.1, flat=True)
        # cornice + frieze along the whole building
        prof = [(1.0, 0.0), (2.0, 0.2), (6.0, 1.0), (5.0, 0.9), (5.0, 0.8), (4.0, 0.6), (6.4, 0.8),
                (6.0, 0.7), (4.0, 0.5), (3.0, 0.4), (5.0, 0.6), (5.0, 0.6), (4.6, 0.5), (4.0, 0.4),
                (2.0, 0.1), (3.0, 0.2)]
        molding(self.lay, 0, L.CEIL, W, prof, hbase=0.7)
        # dentils in the cornice band
        for x in range(0, W, 4):
            lay.rect(x, L.CEIL + 9, 2, 2, 'W', 5.4, hgt=0.5, flat=True)
            lay.rect(x + 2, L.CEIL + 9, 2, 2, 'W', 2.6, hgt=0.15, flat=True)
        # frieze band
        fy = L.CEIL + len(prof)
        lay.rect(0, fy, W, 7, 'W', 4.0, hgt=0.15, flat=True)
        lay.rect(0, fy + 7, W, 1, 'W', 5.0, hgt=0.3, flat=True)
        lay.rect(0, fy + 8, W, 1, 'W', 2.8, hgt=0.0, flat=True)
        self.frieze_bottom = fy + 9

    # ------------------------------------------------------------------ dado (wainscot)
    def dado(self, x0, x1, top=248):
        lay = self.lay
        h = L.FLOOR - top
        lay.rect(x0, top, x1 - x0, h, 'D', 2.0, hgt=0.15, flat=True)
        # chair rail
        lay.rect(x0, top, x1 - x0, 1, 'D', 5.0, hgt=0.6, flat=True)
        lay.rect(x0, top + 1, x1 - x0, 2, 'D', 3.6, hgt=0.5, flat=True)
        lay.rect(x0, top + 3, x1 - x0, 1, 'D', 1.0, hgt=0.1, flat=True)
        # panels
        pw = 22
        n = max(1, int((x1 - x0 - 4) // (pw + 4)))
        pw = (x1 - x0 - 4 - (n - 1) * 4) // n
        px_ = x0 + 2 + ((x1 - x0 - 4) - (n * pw + (n - 1) * 4)) // 2
        for i in range(n):
            xx = px_ + i * (pw + 4)
            recess(lay, xx, top + 7, pw, h - 17, 'D', 1.6, hgt=-0.2, shadow=1.0, light=3.0)
            lay.rect(xx + 2, top + 9, pw - 4, h - 21, 'D', 2.0, hgt=0.05, flat=True)
        # skirting
        lay.rect(x0, L.FLOOR - 6, x1 - x0, 6, 'D', 1.4, hgt=0.3, flat=True)
        lay.rect(x0, L.FLOOR - 6, x1 - x0, 1, 'D', 3.0, hgt=0.4, flat=True)

    # ------------------------------------------------------------------ pilaster
    def pilaster(self, x0, x1, top, bot=L.FLOOR, cap=True, ramp='W', face=5.0):
        lay = self.lay
        w = x1 - x0
        lay.rect(x0, top, w, bot - top, ramp, face, hgt=0.6, flat=True)
        lay.rect(x0, top, 1, bot - top, ramp, face + 1.6, hgt=0.45, flat=True)
        lay.rect(x0 + 1, top, 1, bot - top, ramp, face + 0.6, hgt=0.55, flat=True)
        lay.rect(x1 - 1, top, 1, bot - top, ramp, face - 1.6, hgt=0.45, flat=True)
        lay.rect(x1, top, 1, bot - top, ramp, 2.4, hgt=0.0, flat=True)     # cast shadow on wall
        # subtle vertical recessed strip (stripped classicism)
        lay.rect(x0 + 4, top + 12, w - 8, bot - top - 30, ramp, face - 0.5, hgt=0.5, flat=True)
        lay.rect(x0 + 4, top + 12, w - 8, 1, ramp, face - 1.5, hgt=0.45, flat=True)
        lay.rect(x0 + 4, top + 12, 1, bot - top - 30, ramp, face - 1.2, hgt=0.45, flat=True)
        if cap:
            # capital: abacus + echinus
            lay.rect(x0 - 3, top - 6, w + 6, 3, ramp, face + 1.0, hgt=0.8, flat=True)
            lay.rect(x0 - 3, top - 6, w + 6, 1, ramp, face + 2.2, hgt=0.85, flat=True)
            lay.rect(x0 - 2, top - 3, w + 4, 2, ramp, face - 0.2, hgt=0.7, flat=True)
            lay.rect(x0 - 1, top - 1, w + 2, 1, ramp, face - 1.6, hgt=0.6, flat=True)
            lay.rect(x0 - 3, top - 3, w + 6, 1, ramp, 2.4, hgt=0.6, flat=True)
        # base / plinth
        lay.rect(x0 - 2, bot - 10, w + 4, 10, ramp, face - 0.4, hgt=0.7, flat=True)
        lay.rect(x0 - 2, bot - 10, w + 4, 1, ramp, face + 1.4, hgt=0.75, flat=True)
        lay.rect(x0 - 1, bot - 13, w + 2, 3, ramp, face + 0.4, hgt=0.65, flat=True)
        lay.rect(x0 - 1, bot - 13, w + 2, 1, ramp, face + 1.6, hgt=0.7, flat=True)
        lay.rect(x1 + 2, bot - 10, 1, 10, ramp, 2.2, hgt=0.0, flat=True)

    # ------------------------------------------------------------------ window
    def window(self, x0, x1, idx, blind=0, sill_item=None, wy=None, fanlight_open=False):
        lay = self.lay
        y0, y1 = wy if wy is not None else L.WIN_Y
        w = x1 - x0
        # architrave (raised stone surround)
        ax0, ax1, ay0, ay1 = x0 - 9, x1 + 9, y0 - 12, y1 + 6
        lay.rect(ax0, ay0, ax1 - ax0, ay1 - ay0, 'W', 5.6, hgt=0.5, flat=True)
        lay.rect(ax0, ay0, 1, ay1 - ay0, 'W', 7.0, hgt=0.4, flat=True)
        lay.rect(ax1 - 1, ay0, 1, ay1 - ay0, 'W', 3.6, hgt=0.4, flat=True)
        lay.rect(ax0 + 3, ay0 + 3, ax1 - ax0 - 6, 1, 'W', 4.4, hgt=0.45, flat=True)     # inner fillet
        lay.rect(ax0 + 3, ay0 + 3, 1, ay1 - ay0 - 6, 'W', 4.4, hgt=0.45, flat=True)
        lay.rect(ax1 - 4, ay0 + 3, 1, ay1 - ay0 - 6, 'W', 6.6, hgt=0.45, flat=True)
        lay.rect(ax1, ay0 + 2, 1, ay1 - ay0 - 2, 'W', 2.6, hgt=0.0, flat=True)          # shadow on wall
        # ears (crossettes) at the top corners
        lay.rect(ax0 - 2, ay0, 2, 7, 'W', 5.4, hgt=0.5, flat=True)
        lay.rect(ax1, ay0, 2, 7, 'W', 4.6, hgt=0.5, flat=True)
        # hood cornice
        hx0, hx1, hy = x0 - 14, x1 + 14, ay0 - 10
        lay.rect(hx0, hy, hx1 - hx0, 10, 'W', 5.0, hgt=0.8, flat=True)
        lay.rect(hx0 - 1, hy, hx1 - hx0 + 2, 2, 'W', 6.8, hgt=0.95, flat=True)
        lay.rect(hx0, hy + 2, hx1 - hx0, 1, 'W', 4.0, hgt=0.85, flat=True)
        lay.rect(hx0 + 1, hy + 6, hx1 - hx0 - 2, 1, 'W', 6.0, hgt=0.7, flat=True)
        lay.rect(hx0 + 1, hy + 8, hx1 - hx0 - 2, 2, 'W', 3.4, hgt=0.6, flat=True)
        lay.rect(hx0 + 2, hy + 10, hx1 - hx0 - 4, 2, 'W', 2.8, hgt=0.3, flat=True)     # shadow under hood
        for k in range(hx0 + 3, hx1 - 3, 5):                                            # small modillions
            lay.rect(k, hy + 3, 2, 3, 'W', 5.8, hgt=0.9, flat=True)
            lay.rect(k + 2, hy + 3, 1, 3, 'W', 3.2, hgt=0.8, flat=True)
        # reveal (deep wall opening)
        rx0, rx1, ry0, ry1 = x0 - 5, x1 + 5, y0 - 7, y1 + 3
        lay.rect(rx0, ry0, rx1 - rx0, ry1 - ry0, 'W', 3.0, hgt=-0.5, flat=True)
        lay.rect(rx0, ry0, rx1 - rx0, 3, 'W', 2.0, hgt=-0.45, flat=True)               # soffit (dark)
        lay.rect(rx0, ry0 + 3, 3, ry1 - ry0 - 3, 'W', 4.6, hgt=-0.45, flat=True)       # left jamb
        lay.rect(rx1 - 3, ry0 + 3, 3, ry1 - ry0 - 3, 'W', 3.6, hgt=-0.45, flat=True)   # right jamb
        # outer casing + sashes
        cx0, cx1, cy0, cy1 = x0 - 2, x1 + 2, y0 - 3, y1 + 2
        lay.rect(cx0, cy0, cx1 - cx0, cy1 - cy0, 'W', 3.4, hgt=-0.2, flat=True)
        glass = np.zeros((y1 - y0, w), bool)
        glass[:] = True
        mid = w // 2
        tr = 38                                   # transom height from glass top (fanlight)
        bars = np.zeros_like(glass)
        bars[:, mid - 1:mid + 1] = True            # meeting stiles
        bars[tr:tr + 3, :] = True                  # transom
        bars[:, :1] = True; bars[:, -1:] = True
        bars[:1, :] = True; bars[-1:, :] = True
        ph3 = (y1 - y0 - tr - 3) / 3.0
        for gy in (int(round(tr + 3 + ph3)), int(round(tr + 3 + 2 * ph3))):  # glazing bars in lower sashes
            bars[gy:gy + 1, :] = True
        bars[0:tr, mid - 1:mid + 1] = True
        # sash frames thicker around each sash
        bars[tr + 3:, mid - 3:mid + 3] = True
        bars[tr + 3:, 1:3] = True
        bars[tr + 3:, -3:-1] = True
        glass &= ~bars
        sub = np.zeros((y1 - y0, w), np.float32)
        lay.put(bars, x0, y0, 'W', 3.0, hgt=0.1, flat=True)
        # bar highlights (cold light catching the inner edges)
        bh = bars & ~np.vstack([bars[1:], np.zeros((1, w), bool)])
        lay.put(bh & bars, x0, y0, 'W', 4.4, flat=True)
        lay.erase_mask(glass, x0, y0)
        # frost: feathery fans in the lower corners of the lower panes + a thin rime line
        rng = np.random.default_rng(100 + idx)
        frost = np.zeros_like(glass)
        core = np.zeros_like(glass)
        panes = self._panes(w, y1 - y0, mid, tr)
        if fanlight_open:
            # the fanlight sash is tilted into the room for air: its frame leans toward the viewer (a
            # trapezoid); the gap at the top is open air -- the papers below stir in the draught
            ox = 3
            pane = np.zeros((tr, w), bool)
            for yy in range(4, tr):
                f = (yy - 4) / max(1, tr - 5)
                a = int(round(ox * (1 - f))) + 1
                pane[yy, a:w - a] = True
            lay.put(pane, x0, y0, 'W', 3.4, hgt=0.4, flat=True)
            inner = kit.erode(pane, 2)
            glass[0:tr, :] = False
            glass[0:tr, :] |= inner
            lay.erase_mask(inner, x0, y0)
            lay.erase(x0 + 2, y0 + 1, w - 4, 3)                                     # the open gap at the top
            glass[1:4, 2:w - 2] = True
            lay.rect(x0 + w // 2, y0 + tr, 1, 22, 'K', 3.6, flat=True)                 # tilt rod
            lay.rect(x0 + w // 2 - 1, y0 + tr + 22, 3, 2, 'A', 3.6, hgt=0.6, flat=True)
            self.fanlight = (x0, y0, w, tr)
        for pi, (fx, fy0, fx1, fy1) in enumerate(panes):
            lowest = fy1 >= (y1 - y0) - 2
            if not lowest:             # frost only creeps up the lowest panes (cold sill)
                continue
            for corner_x, sgn in ((fx, 1), (fx1 - 1, -1)):
                rad = (7.5 if lowest else 4.5) + rng.uniform(-1, 1.5)
                for yy in range(max(fy0, int(fy1 - rad - 2)), fy1):
                    for xx in range(fx, fx1):
                        dx = (xx - corner_x) * sgn
                        dy = fy1 - 1 - yy
                        if dx < 0:
                            continue
                        d = math.hypot(dx * 1.1, dy)
                        edge = rad + 1.3 * math.sin(math.atan2(dy, dx + 0.01) * 5 + pi) + rng.normal(0, 0.45)
                        if d < edge:
                            frost[yy, xx] = True
                            if d < edge - 2.2:
                                core[yy, xx] = True
                # a few crystal needles
                for k in range(2):
                    ang = rng.uniform(0.25, 1.25)
                    ln = rad + rng.uniform(1, 4)
                    for s in range(int(ln)):
                        xx = int(round(corner_x + sgn * math.cos(ang) * s))
                        yy = int(round(fy1 - 1 - math.sin(ang) * s))
                        if fx <= xx < fx1 and fy0 <= yy < fy1:
                            frost[yy, xx] = True
            # rime along the bottom edge
            for xx in range(fx, fx1):
                if rng.random() < (0.85 if lowest else 0.55):
                    frost[fy1 - 1, xx] = True
        frost &= glass
        core &= glass
        lay.put(frost, x0, y0, 'W', 8.0, hgt=0.05, flat=True)
        lay.put(core, x0, y0, 'W', 9.0, flat=True)
        # roller blind partly lowered
        if blind:
            lay.rect(x0, y0, w, blind, 'P', 3.0, hgt=0.15, flat=True)
            for k in range(0, blind, 4):
                lay.rect(x0, y0 + k, w, 1, 'P', 2.4, hgt=0.12, flat=True)
            lay.rect(x0, y0 + blind - 2, w, 2, 'D', 3.0, hgt=0.3, flat=True)
            lay.rect(x0 + mid - 1, y0 + blind, 2, 4, 'W', 6.0, hgt=0.2, flat=True)
            lay.rect(x0 - 1, y0 - 2, w + 2, 2, 'D', 2.0, hgt=0.4, flat=True)
        # sill (seen from above) + apron
        sx0, sx1 = x0 - 11, x1 + 11
        lay.rect(sx0, y1 + 4, sx1 - sx0, 2, 'W', 7.0, hgt=0.7, flat=True)
        lay.rect(sx0, y1 + 6, sx1 - sx0, 3, 'W', 4.6, hgt=0.6, flat=True)
        lay.rect(sx0, y1 + 9, sx1 - sx0, 1, 'W', 2.4, hgt=0.2, flat=True)
        # radiator niche
        nx0, nx1, ny0, ny1 = x0 - 3, x1 + 3, y1 + 13, L.FLOOR - 4
        lay.rect(nx0, ny0, nx1 - nx0, ny1 - ny0, 'W', 2.6, hgt=-0.4, flat=True)
        lay.rect(nx0, ny0, nx1 - nx0, 2, 'W', 1.6, hgt=-0.4, flat=True)
        self.radiator(nx0 + 3, ny0 + 6, nx1 - nx0 - 6, ny1 - ny0 - 7)
        # sill items
        if sill_item == 'plant':
            self.sill_plant(x0 + 4, y1 + 4)
        elif sill_item == 'rolls':
            self.sill_rolls(x1, y1 + 4)
        self.windows.append({'glass': glass, 'x0': x0, 'y0': y0, 'x1': x1, 'y1': y1, 'tr': tr})

    def _panes(self, w, h, mid, tr):
        out = []
        ph3 = (h - tr - 3) / 3.0
        ys = [tr + 3, int(round(tr + 3 + ph3)), int(round(tr + 3 + 2 * ph3)), h]
        for i in range(3):
            out.append((3, ys[i] + 1, mid - 3, ys[i + 1] - 1))
            out.append((mid + 3, ys[i] + 1, w - 3, ys[i + 1] - 1))
        return out

    def radiator(self, x, y, w, h):
        lay = self.lay
        # feed pipe + valve
        lay.rect(x - 3, y + 2, 2, h + 2, 'W', 4.0, hgt=0.4, flat=True)
        lay.rect(x - 3, y + 2, 1, h + 2, 'W', 5.6, hgt=0.4, flat=True)
        lay.rect(x - 5, y + 3, 6, 3, 'A', 2.0, hgt=0.6, flat=True)
        lay.rect(x - 5, y + 3, 6, 1, 'A', 3.6, hgt=0.7, flat=True)
        lay.rect(x, y, w, 2, 'W', 5.0, hgt=0.5, flat=True)
        lay.rect(x, y, w, 1, 'W', 6.4, hgt=0.55, flat=True)
        cols = w // 3
        for c in range(cols):
            cx = x + c * 3
            lay.rect(cx, y + 2, 2, h - 4, 'W', 4.6, hgt=0.6, flat=True)
            lay.rect(cx, y + 2, 1, h - 4, 'W', 5.8, hgt=0.65, flat=True)
            lay.rect(cx + 2, y + 2, 1, h - 4, 'W', 1.6, hgt=0.1, flat=True)
            lay.rect(cx, y + 3, 2, 1, 'W', 6.2, hgt=0.65, flat=True)
        lay.rect(x, y + h - 2, w, 2, 'W', 3.6, hgt=0.5, flat=True)
        lay.rect(x + 1, y + h, 2, 2, 'W', 2.0, hgt=0.3, flat=True)
        lay.rect(x + w - 3, y + h, 2, 2, 'W', 2.0, hgt=0.3, flat=True)

    def sill_plant(self, x, y):
        lay = self.lay
        # clay pot + a few fleshy leaves (a stubborn office plant)
        lay.rect(x, y - 6, 8, 6, 'D', 4.0, hgt=0.6, flat=True)
        lay.rect(x, y - 6, 8, 1, 'D', 6.0, hgt=0.7, flat=True)
        lay.rect(x + 6, y - 5, 2, 5, 'D', 2.6, hgt=0.5, flat=True)
        leaves = [(x + 1, y - 12, 2, 6), (x + 3, y - 15, 2, 9), (x + 5, y - 11, 2, 5), (x - 1, y - 9, 2, 3),
                  (x + 7, y - 9, 2, 3)]
        for (lx, ly, lw, lh) in leaves:
            lay.rect(lx, ly, lw, lh, 'G', 3.0, hgt=0.5, flat=True)
            lay.rect(lx, ly, 1, lh, 'G', 4.4, hgt=0.55, flat=True)

    def sill_rolls(self, x1, sill_y):
        """Rolled drawings lying on the window board, seen from the side (horizontal cylinders).  Round 10:
        they used to float 2 px above the board and stick out over the right-hand window frame (a visible
        glitch); now a small pyramid inside the glass span, the lowest roll resting on the board's back
        row (the front row stays visible below it), each roll showing its cut end with the spiral core."""
        lay = self.lay
        for i, (r_end, ln, t) in enumerate([(x1 - 5, 26, 4.6), (x1 - 7, 21, 5.2), (x1 - 10, 15, 4.2)]):
            y = sill_y - 2 - i * 3
            xs = r_end - ln + 1
            lay.rect(xs, y, ln, 3, 'P', t, hgt=0.5, flat=True)
            lay.rect(xs, y, ln, 1, 'P', t + 1.2, hgt=0.6, flat=True)
            lay.rect(xs, y + 2, ln, 1, 'P', t - 0.8, hgt=0.45, flat=True)
            lay.rect(r_end, y, 1, 3, 'P', t - 1.4, hgt=0.4, flat=True)
            lay.px(r_end, y + 1, 'I', 2.0)
        lay.rect(x1 - 30, sill_y + 1, 26, 1, 'W', 5.4, hgt=0.6, flat=True)      # contact shadow on the board

    # ------------------------------------------------------------------ door
    def double_door(self, x0, x1, top, glass_text=None, lit=True, seed=0):
        lay = self.lay
        bot = L.FLOOR
        # stone architrave
        lay.rect(x0 - 6, top - 8, x1 - x0 + 12, bot - top + 8, 'W', 5.4, hgt=0.5, flat=True)
        lay.rect(x0 - 6, top - 8, 1, bot - top + 8, 'W', 6.8, hgt=0.45, flat=True)
        lay.rect(x1 + 5, top - 8, 1, bot - top + 8, 'W', 3.4, hgt=0.45, flat=True)
        lay.rect(x0 - 3, top - 5, x1 - x0 + 6, 1, 'W', 4.0, hgt=0.45, flat=True)
        lay.rect(x1 + 6, top - 6, 1, bot - top + 6, 'W', 2.4, hgt=0.0, flat=True)
        # overdoor cornice
        lay.rect(x0 - 10, top - 16, x1 - x0 + 20, 8, 'W', 5.0, hgt=0.8, flat=True)
        lay.rect(x0 - 11, top - 16, x1 - x0 + 22, 2, 'W', 6.8, hgt=0.9, flat=True)
        lay.rect(x0 - 9, top - 10, x1 - x0 + 18, 2, 'W', 3.0, hgt=0.6, flat=True)
        # leaves
        w = x1 - x0
        half = w // 2
        lay.rect(x0, top, w, bot - top, 'D', 2.4, hgt=0.3, flat=True)
        for k in range(2):
            lx = x0 + k * half
            lay.rect(lx, top, 1, bot - top, 'D', 1.0, hgt=0.1, flat=True)
            # upper frosted glass panel
            gx, gy, gw, gh = lx + 4, top + 6, half - 8, 44
            if lit:
                lay.rect(gx, gy, gw, gh, 'A', 3.2, hgt=-0.2, emis=True)
                tt = pg.value_noise(gw, gh, 9, seed + k, octaves=2)
                lay.put(np.ones((gh, gw), bool), gx, gy, 'A', 2.6 + tt * 1.6, emis=True)
                lay.rect(gx, gy, gw, 1, 'A', 2.0, emis=True)
            else:
                lay.rect(gx, gy, gw, gh, 'W', 4.0, hgt=-0.2, flat=True)
            # glazing frame
            lay.rect(gx - 1, gy - 1, gw + 2, 1, 'D', 3.6, hgt=0.4, flat=True)
            lay.rect(gx - 1, gy + gh, gw + 2, 1, 'D', 1.0, hgt=0.4, flat=True)
            lay.rect(gx - 1, gy - 1, 1, gh + 2, 'D', 3.6, hgt=0.4, flat=True)
            lay.rect(gx + gw, gy - 1, 1, gh + 2, 'D', 1.2, hgt=0.4, flat=True)
            # lower raised panels
            for (py, ph) in ((top + 56, 18), (top + 78, bot - top - 86)):
                bevel_box(lay, lx + 4, py, half - 8, ph, 'D', 2.8, hi=4.0, lo=1.2, hgt=0.35)
        # mirrored lettering on the frosted glass (seen from inside the office)
        if glass_text and lit:
            m = kit.text_mask(glass_text, '35', overhang=True)[:, ::-1]     # distinct umlauts (pixfont_umlauts)
            tw = m.shape[1]
            lay.put(m, x0 + (w - tw) // 2, top + 14 - (m.shape[0] - 5), 'A', 1.0, emis=True, flat=True)
        # brass handles
        lay.rect(x0 + half - 4, top + 52, 2, 6, 'A', 4.0, hgt=0.8, flat=True)
        lay.rect(x0 + half + 2, top + 52, 2, 6, 'A', 4.0, hgt=0.8, flat=True)
        lay.rect(x0 + half - 4, top + 52, 1, 6, 'A', 5.4, hgt=0.9, flat=True)
        lay.rect(x0 + half + 2, top + 52, 1, 6, 'A', 5.4, hgt=0.9, flat=True)
        # threshold
        lay.rect(x0 - 2, bot - 2, w + 4, 2, 'W', 6.0, hgt=0.3, flat=True)

    # ------------------------------------------------------------------ office wall details
    def poster(self):
        lay = self.lay
        x, y, w, h = L.POSTER
        lay.rect(x, y, w, h, 'P', 2.0, hgt=0.12, flat=True)
        poster_field(lay, hist=self.hist)
        self.decal_sites['poster'] = (x - 1, y - 1, w + 2, 40, poster_field)
        # bottom: paper band with lettering
        lay.rect(x + 1, y + 37, w - 2, h - 38, 'P', 4.0, hgt=0.12, flat=True)
        m = kit.text_mask('AUFBAU', '35')
        lay.put(m, x + (w - m.shape[1]) // 2, y + 40, 'I', 1.0, flat=True)
        m2 = kit.text_mask('1964', '35')
        lay.put(m2, x + w - m2.shape[1] - 3, y + 47, 'I', 2.0, flat=True)
        lay.px(x + w - 2, y + h - 2, 'A', 4.0, hgt=0.4)
        # drop shadow right/bottom
        lay.rect(x + w, y + 2, 1, h - 1, 'W', 2.6, flat=True)
        lay.rect(x + 1, y + h, w, 1, 'W', 2.6, flat=True)
        # a typed notice pinned on the bare wall right of the framed notice, level with it.  Round 10b: it used
        # to be pasted over the poster's lower-left corner, covering the 'A' of AUFBAU, and the poster's drop
        # shadow (drawn after it) ran across it like a stray text line -- it now overlaps nothing.
        nx, ny = X(538), 190
        lay.rect(nx + 15, ny + 2, 1, 17, 'W', 2.6, flat=True)
        lay.rect(nx + 1, ny + 18, 15, 1, 'W', 2.6, flat=True)
        lay.rect(nx, ny, 15, 18, 'P', 6.0, hgt=0.16, flat=True)
        lay.rect(nx + 14, ny + 1, 1, 17, 'P', 4.0, hgt=0.16, flat=True)
        lay.rect(nx, ny + 17, 14, 1, 'P', 4.4, hgt=0.16, flat=True)
        pseudo_text(lay, nx + 2, ny + 3, 11, 5, 'I', 2.0, seed=31)
        lay.px(nx + 1, ny + 1, 'A', 4.0, hgt=0.4)

    def framed_notice(self, x, y, w, h, seed, emblem=True):
        lay = self.lay
        lay.rect(x - 1, y - 1, w + 2, h + 2, 'D', 2.0, hgt=0.4, flat=True)
        lay.rect(x - 1, y - 1, w + 2, 1, 'D', 3.6, hgt=0.45, flat=True)
        lay.rect(x, y, w, h, 'P', 4.2, hgt=0.15, flat=True)
        lay.rect(x, y, w, 1, 'P', 3.4, flat=True)
        if emblem:
            disc, pillar = kit.reichssiegel_mask(5)
            lay.put(disc, x + w // 2 - 2, y + 2, 'N', 0.6, flat=True)
            lay.put(pillar, x + w // 2 - 2, y + 2, 'P', 5.0, flat=True)
        pseudo_text(lay, x + 2, y + 9, w - 4, max(1, (h - 11) // 2), 'I', 2.0, seed=seed, gap=2)
        lay.rect(x + w + 1, y, 1, h + 2, 'W', 2.6, flat=True)

    def clock(self):
        lay = self.lay
        cx, cy = L.CLOCK
        lay.ellipse(cx + 0.5, cy + 0.5, 8.0, 8.0, 'D', 2.0, hgt=0.6, flat=True)
        lay.ellipse(cx + 0.5, cy + 0.5, 6.5, 6.5, 'P', 5.0, hgt=0.5, flat=True)
        lay.ellipse(cx - 1.0, cy - 1.0, 3.0, 3.0, 'P', 6.0, hgt=0.5, flat=True)
        for a in range(0, 360, 30):
            r = math.radians(a)
            lay.px(cx + round(math.cos(r) * 5), cy + round(math.sin(r) * 5), 'I', 2.0)
        # (the hands are drawn at runtime by the BerlinClock actor: the clock runs)
        # rim highlight/shadow + hanger
        for a in range(200, 300, 8):
            r = math.radians(a)
            lay.px(cx + 0.5 + math.cos(r) * 7.5, cy + 0.5 + math.sin(r) * 7.5, 'D', 4.0)
        lay.rect(cx, cy - 11, 1, 3, 'W', 3.0, flat=True)

    def filing_cabinets(self, x0, x1):
        lay = self.lay
        top = 238
        n = 3
        cw = (x1 - x0) // n
        for i in range(n):
            x = x0 + i * cw
            lay.rect(x, top, cw - 1, L.FLOOR - top, 'W', 5.0, hgt=0.5, flat=True)
            lay.rect(x, top, cw - 1, 1, 'W', 7.0, hgt=0.55, flat=True)
            lay.rect(x, top, 1, L.FLOOR - top, 'W', 6.2, hgt=0.5, flat=True)
            lay.rect(x + cw - 2, top, 1, L.FLOOR - top, 'W', 3.0, hgt=0.4, flat=True)
            lay.rect(x + cw - 1, top, 1, L.FLOOR - top, 'W', 1.4, hgt=0.0, flat=True)
            dh = (L.FLOOR - top - 4) // 4
            for d in range(4):
                yy = top + 2 + d * dh
                lay.rect(x + 2, yy, cw - 5, dh - 1, 'W', 4.6, hgt=0.45, flat=True)
                lay.rect(x + 2, yy + dh - 1, cw - 5, 1, 'W', 2.0, hgt=0.2, flat=True)
                # label holder + handle
                lay.rect(x + cw // 2 - 4, yy + 2, 6, 3, 'P', 4.6, hgt=0.5, flat=True)
                lay.rect(x + cw // 2 - 4, yy + 2, 6, 1, 'W', 6.8, hgt=0.55, flat=True)
                lay.rect(x + cw // 2 - 3, yy + 6, 4, 1, 'W', 7.4, hgt=0.7, flat=True)
                lay.rect(x + cw // 2 - 3, yy + 7, 4, 1, 'W', 2.6, hgt=0.6, flat=True)
            # one drawer slightly open (third cabinet)
            if i == 2:
                yy = top + 2 + 1 * dh
                lay.rect(x + 1, yy - 1, cw - 3, 2, 'P', 4.0, hgt=0.6, flat=True)
        # binders + boxes on top
        bx = x0 + 2
        cols = [('B', 2.6), ('D', 3.0), ('W', 5.4), ('B', 3.4), ('D', 2.4), ('P', 3.0), ('W', 4.6)]
        rng = np.random.default_rng(5)
        for (rm, t) in cols:
            bw = int(rng.integers(3, 5)); bh = int(rng.integers(11, 15))
            lay.rect(bx, top - bh, bw, bh, rm, t, hgt=0.5, flat=True)
            lay.rect(bx, top - bh, 1, bh, rm, t + 1.0, hgt=0.55, flat=True)
            lay.rect(bx + 1, top - bh + 3, bw - 2 if bw > 2 else 1, 2, 'P', 5.0, hgt=0.55, flat=True)
            bx += bw
        # a leaning binder
        lay.line(bx + 1, top - 1, bx + 6, top - 12, 'B', 3.0)
        lay.line(bx + 2, top - 1, bx + 7, top - 12, 'B', 2.4)
        # archive box with lid
        lay.rect(x1 - 26, top - 10, 22, 10, 'P', 2.4, hgt=0.5, flat=True)
        lay.rect(x1 - 27, top - 12, 24, 3, 'P', 3.4, hgt=0.6, flat=True)
        lay.rect(x1 - 27, top - 12, 24, 1, 'P', 4.4, hgt=0.6, flat=True)
        lay.rect(x1 - 19, top - 7, 8, 4, 'P', 5.0, hgt=0.55, flat=True)

    # ------------------------------------------------------------------ partition (poche + arch)
    def partition(self, x0, x1, lintel):
        lay = self.lay
        w = x1 - x0
        # the cut wall (poche): near-black stone with faint coursing
        lay.rect(x0, 0, w, lintel, 'W', 1.4, hgt=0.9, flat=True)
        for yy in range(6, lintel, 9):
            lay.rect(x0 + 1, yy, w - 2, 1, 'W', 0.6, hgt=0.85, flat=True)
        for yy in range(6, lintel, 18):
            lay.rect(x0 + w // 2, yy - 8, 1, 8, 'W', 0.6, hgt=0.85, flat=True)
        lay.rect(x0, 0, 1, lintel, 'W', 3.0, hgt=0.8, flat=True)
        lay.rect(x1 - 1, 0, 1, lintel, 'W', 2.4, hgt=0.8, flat=True)
        # arch soffit (underside seen from below) + keystone
        for i in range(w):
            u = (i + 0.5) / w
            dy = int(round(4 * math.sin(math.pi * u)))
            lay.rect(x0 + i, lintel - dy, 1, dy + 4, 'W', 3.4, hgt=0.5, flat=True)
            lay.rect(x0 + i, lintel + 4, 1, 1, 'W', 2.0, hgt=0.3, flat=True)
        lay.rect(x0 + w // 2 - 3, lintel - 9, 6, 9, 'W', 4.6, hgt=1.0, flat=True)
        lay.rect(x0 + w // 2 - 3, lintel - 9, 6, 1, 'W', 6.0, hgt=1.0, flat=True)
        # passage behind (darker plaster, lower dado)
        lay.rect(x0, lintel + 5, w, L.FLOOR - lintel - 5, 'W', 3.0, hgt=-0.2, flat=True)
        lay.vgrad(x0, lintel + 5, w, 30, 'W', 2.0, 3.0, hgt=-0.2)
        lay.rect(x0, L.FLOOR - 20, w, 20, 'D', 1.4, hgt=-0.1, flat=True)
        lay.rect(x0, L.FLOOR - 20, w, 1, 'D', 3.0, hgt=-0.05, flat=True)
        # jamb casings on both room sides
        for (jx, hi) in ((x0 - 4, True), (x1, False)):
            lay.rect(jx, lintel - 12, 4, L.FLOOR - lintel + 12, 'W', 5.2 if hi else 4.6, hgt=0.6, flat=True)
            lay.rect(jx + (0 if hi else 3), lintel - 12, 1, L.FLOOR - lintel + 12, 'W', 6.6 if hi else 3.0,
                     hgt=0.6, flat=True)

    # ------------------------------------------------------------------ archive hall
    def archive(self):
        lay = self.lay
        ax0, ax1 = L.ARCHIVE
        gy0, gy1 = L.GALLERY_Y
        # upper level: dark wall + upper shelving behind the balustrade
        lay.vgrad(ax0, self.frieze_bottom, ax1 - ax0, gy0 - self.frieze_bottom, 'W', 2.6, 3.4, hgt=0.0)
        for i in range(len(L.PIERS) - 1):
            bx0 = L.PIERS[i] + L.PIER_W
            bx1 = L.PIERS[i + 1]
            self.upper_shelf(bx0 + 2, self.frieze_bottom + 8, bx1 - bx0 - 4, gy0 - self.frieze_bottom - 8,
                             seed=40 + i)
        # last partial bay up to the partition
        self.upper_shelf(L.PIERS[-1] + L.PIER_W + 2, self.frieze_bottom + 8,
                         L.PART2[0] - L.PIERS[-1] - L.PIER_W - 4, gy0 - self.frieze_bottom - 8, seed=49)
        # balustrade
        rt = L.RAIL_Y
        for x in range(ax0, ax1, 5):
            lay.rect(x + 2, rt + 3, 1, gy0 - rt - 4, 'W', 4.2, hgt=0.5, flat=True)
            lay.rect(x + 3, rt + 3, 1, gy0 - rt - 4, 'W', 1.6, hgt=0.1, flat=True)
        lay.rect(ax0, rt, ax1 - ax0, 3, 'D', 3.0, hgt=0.7, flat=True)
        lay.rect(ax0, rt, ax1 - ax0, 1, 'D', 5.0, hgt=0.75, flat=True)
        lay.rect(ax0, rt + 3, ax1 - ax0, 1, 'W', 1.4, hgt=0.2, flat=True)
        lay.rect(ax0, gy0 - 3, ax1 - ax0, 2, 'W', 4.4, hgt=0.5, flat=True)
        # gallery slab
        lay.rect(ax0, gy0, ax1 - ax0, gy1 - gy0, 'W', 5.0, hgt=0.7, flat=True)
        lay.rect(ax0, gy0, ax1 - ax0, 1, 'W', 7.0, hgt=0.75, flat=True)
        lay.rect(ax0, gy0 + 2, ax1 - ax0, 1, 'W', 3.6, hgt=0.7, flat=True)
        lay.rect(ax0, gy1 - 2, ax1 - ax0, 1, 'W', 6.0, hgt=0.7, flat=True)
        lay.rect(ax0, gy1, ax1 - ax0, 3, 'W', 1.6, hgt=0.2, flat=True)
        for x in range(ax0 + 6, ax1, 24):                                      # bolt heads
            lay.px(x, gy0 + 5, 'W', 7.0, hgt=0.9)
        # lower level bays
        lower_top = gy1 + 3
        bays = []
        for i in range(len(L.PIERS) - 1):
            bays.append((L.PIERS[i] + L.PIER_W, L.PIERS[i + 1]))
        bays.append((L.PIERS[-1] + L.PIER_W, L.PART2[0]))
        kinds = ['rolls', 'rolls', 'boxes', 'ledgers', 'rolls_small']
        for (bx0, bx1), kind in zip(bays, kinds):
            self.lower_shelf(bx0, lower_top, bx1, kind)
        # brass rail for the rolling library ladder
        for (bx0, bx1) in bays:
            lay.rect(bx0, 151, bx1 - bx0, 1, 'A', 2.6, hgt=0.7, flat=True)
            lay.rect(bx0, 152, bx1 - bx0, 1, 'D', 1.0, hgt=0.2, flat=True)
        # piers (full height, in front of the slab)
        for p in L.PIERS:
            self.pier(p, p + L.PIER_W)
        # pendant lamp over the flat files (hangs from the gallery soffit)
        self.pendant(L.HOTSPOTS['plan_b'][0], gy1 + 3, 40)
        # wall sconce on pier 4
        sx = L.PIERS[3] + L.PIER_W // 2
        self.sconce(sx, 204)
        # small enamel sign on the first pier: room number (round 10: the old 3-digit number was 11 px on a
        # 10-px plate and lost its first column -- it read as a clipped '314'; two digits sit with a margin)
        m = kit.text_mask('14', '35')
        px0 = L.PIERS[1] + 2
        lay.rect(px0, 160, m.shape[1] + 2, 7, 'P', 5.4, hgt=0.6, flat=True)
        lay.rect(px0, 166, m.shape[1] + 2, 1, 'P', 3.6, hgt=0.6, flat=True)
        lay.put(m, px0 + 1, 161, 'I', 1.0, flat=True)

    def pier(self, x0, x1):
        lay = self.lay
        top = self.frieze_bottom
        w = x1 - x0
        lay.rect(x0, top, w, L.FLOOR - top, 'W', 4.8, hgt=0.8, flat=True)
        lay.rect(x0, top, 1, L.FLOOR - top, 'W', 6.4, hgt=0.7, flat=True)
        lay.rect(x0 + 1, top, 1, L.FLOOR - top, 'W', 5.6, hgt=0.75, flat=True)
        lay.rect(x1 - 1, top, 1, L.FLOOR - top, 'W', 3.0, hgt=0.7, flat=True)
        lay.rect(x1, top, 1, L.FLOOR - top, 'W', 1.4, hgt=0.0, flat=True)
        # corbel under the gallery slab
        gy0, gy1 = L.GALLERY_Y
        lay.rect(x0 - 2, gy1, w + 4, 4, 'W', 5.4, hgt=0.9, flat=True)
        lay.rect(x0 - 1, gy1 + 4, w + 2, 2, 'W', 4.6, hgt=0.85, flat=True)
        lay.rect(x0 - 2, gy1 + 3, w + 4, 1, 'W', 3.0, hgt=0.8, flat=True)
        # stone joints
        for yy in range(top + 14, L.FLOOR - 12, 16):
            lay.rect(x0 + 1, yy, w - 2, 1, 'W', 3.8, hgt=0.75, flat=True)
        # base
        lay.rect(x0 - 2, L.FLOOR - 9, w + 4, 9, 'W', 4.4, hgt=0.9, flat=True)
        lay.rect(x0 - 2, L.FLOOR - 9, w + 4, 1, 'W', 6.2, hgt=0.9, flat=True)

    def upper_shelf(self, x, y, w, h, seed):
        """Upper-gallery shelving in deep shadow: only shelf lips and a few spines catch light."""
        lay = self.lay
        rng = np.random.default_rng(seed)
        lay.rect(x, y, w, h, 'W', 1.2, hgt=-0.3, flat=True)
        rows = 4
        rh = h // rows
        for r in range(rows):
            yy = y + r * rh
            xx = x + 1
            while xx < x + w - 2:
                kind = rng.random()
                if kind < 0.6:
                    sw = int(rng.integers(2, 4)); sh = int(rng.integers(rh - 9, rh - 3))
                    rm = rng.choice(['D', 'W', 'D'])
                    tone = float(rng.choice([0.8, 1.2, 1.6])) + (1.0 if rm == 'W' else 0)
                    lay.rect(xx, yy + rh - 2 - sh, sw, sh, rm, tone, hgt=0.2, flat=True)
                    lay.rect(xx, yy + rh - 2 - sh, 1, sh, rm, tone + 0.6, hgt=0.2, flat=True)
                    xx += sw
                elif kind < 0.78:
                    for k in range(int(rng.integers(2, 4))):
                        cy = yy + rh - 5 - k * 3
                        lay.rect(xx, cy, 3, 3, 'P', 0.6, hgt=0.2, flat=True)
                        lay.px(xx, cy, 'P', 1.2)
                    xx += 4
                else:
                    xx += int(rng.integers(2, 6))
            lay.rect(x, yy + rh - 2, w, 2, 'D', 1.4, hgt=0.3, flat=True)
            lay.rect(x, yy + rh - 2, w, 1, 'D', 2.6, hgt=0.35, flat=True)

    def roll_end(self, x, y, r, tone, ramp='P', hole=True):
        """End of a rolled drawing: flat disc, darker rim bottom-right, one highlight px top-left."""
        lay = self.lay
        m, mx, my = lay.ellipse_mask(x, y, r, r)
        hh, ww = m.shape
        yy, xx = np.mgrid[0:hh, 0:ww]
        dx = (xx + mx + 0.5 - x)
        dy = (yy + my + 0.5 - y)
        rim = (dx * dx + dy * dy) > (r - 0.9) ** 2
        tt = np.where(rim & ((dx + dy) > 0), tone - 1.2, tone)
        tt = np.where(rim & ((dx + dy) <= -0.5), tone + 0.8, tt)
        lay.put(m, mx, my, ramp, tt, hgt=0.3, flat=True)
        lay.dome_height(x, y, r, r, base=0.1, amp=0.3)
        if hole and r >= 2.4:
            lay.px(int(math.floor(x)), int(math.floor(y)), 'D', 1.0, hgt=0.0)

    # hand-drawn roll-end stamps: 3 = lit rim, 2 = face, 1 = shadow rim, 4 = core hole
    ROLL5 = ['.332.', '32221', '32421', '22211', '.111.']
    ROLL7 = ['..333..', '.32221.', '3222221', '3224221', '3222211', '.22211.', '..111..']

    def roll_stamp(self, x, y, stamp, tone, ramp='P'):
        lay = self.lay
        for yy, row in enumerate(stamp):
            for xx, ch in enumerate(row):
                if ch == '.':
                    continue
                t = {'3': tone + 1.0, '2': tone, '1': tone - 1.3, '4': None}[ch]
                if t is None:
                    lay.px(x + xx, y + yy, 'D', 0.5, hgt=0.0, flat=True)
                else:
                    lay.px(x + xx, y + yy, ramp, t, hgt=0.3 + (0.15 if ch == '3' else 0), flat=True)

    def roll_stack(self, cx, cy, cell, rng):
        """Rolls stored end-on in a cubby, packed tight (2x2 thin, or fat + thin)."""
        inner = cell - 1
        k = rng.random()
        if k < 0.07:
            return

        def pick():
            blue = rng.random() < 0.15
            return (2.9 if blue else float(rng.choice([2.3, 2.7, 3.1, 3.5]))), ('B' if blue else 'P')
        gap = 1 if inner >= 11 else 0
        if k < 0.22 and inner >= 11:
            t, r = pick(); self.roll_stamp(cx, cy + inner - 7, self.ROLL7, t, r)
            t, r = pick(); self.roll_stamp(cx + 7, cy + inner - 5, self.ROLL5, t, r)
            if rng.random() < 0.5:
                t, r = pick(); self.roll_stamp(cx + 7, cy + inner - 10, self.ROLL5, t, r)
            return
        slots = [(0, inner - 5), (5 + gap, inner - 5), (0, inner - 10 - gap), (5 + gap, inner - 10 - gap)]
        n = 4 if rng.random() < 0.7 else int(rng.integers(2, 4))
        for (dx, dy) in slots[:n]:
            t, r = pick()
            self.roll_stamp(cx + dx, cy + dy, self.ROLL5, t, r)

    def lower_shelf(self, x0, top, x1, kind):
        lay = self.lay
        rng = np.random.default_rng(zlib.crc32(kind.encode()) % 1000 + x0)   # stable across runs
        w = x1 - x0
        # carcass (oak) with cubbies
        lay.rect(x0, top, w, L.FLOOR - top, 'D', 1.6, hgt=0.3, flat=True)
        lay.rect(x0, top, w, 2, 'D', 3.4, hgt=0.5, flat=True)
        if kind in ('rolls', 'rolls_small'):
            cell = 13 if kind == 'rolls' else 11
            cols = max(1, (w - 3) // cell)
            ox = x0 + (w - cols * cell) // 2 + 1
            rows = (L.FLOOR - 6 - top - 3) // cell
            for r in range(rows):
                for c in range(cols):
                    cx, cy = ox + c * cell, top + 3 + r * cell
                    recess(lay, cx, cy, cell - 1, cell - 1, 'D', 0.8, hgt=-0.5, shadow=0.2, light=1.4)
                    # dividers
                    lay.rect(cx + cell - 1, cy, 1, cell, 'D', 2.6, hgt=0.4, flat=True)
                    lay.rect(cx, cy + cell - 1, cell, 1, 'D', 3.2, hgt=0.45, flat=True)
                    self.roll_stack(cx, cy, cell, rng)
                    if rng.random() < 0.25:            # label tab hanging on the board edge
                        lay.rect(cx + 3, cy + cell - 1, 5, 2, 'P', 5.6, hgt=0.5, flat=True)
                        lay.px(cx + 4, cy + cell, 'I', 2.0)
        elif kind == 'boxes':
            rows = 5
            rh = (L.FLOOR - 6 - top - 3) // rows
            for r in range(rows):
                yy = top + 3 + r * rh
                lay.rect(x0 + 1, yy + rh - 2, w - 2, 2, 'D', 3.0, hgt=0.4, flat=True)
                lay.rect(x0 + 1, yy + rh - 2, w - 2, 1, 'D', 4.0, hgt=0.45, flat=True)
                xx = x0 + 2
                while xx < x1 - 12:
                    bw = int(rng.integers(13, 18))
                    bh = rh - int(rng.integers(4, 7))
                    if xx + bw > x1 - 2:
                        break
                    t = float(rng.choice([2.2, 2.6, 3.0]))
                    lay.rect(xx, yy + rh - 2 - bh, bw - 1, bh, 'P', t, hgt=0.5, flat=True)
                    lay.rect(xx, yy + rh - 2 - bh, bw - 1, 1, 'P', t + 1.2, hgt=0.55, flat=True)
                    lay.rect(xx + bw - 2, yy + rh - 2 - bh, 1, bh, 'P', t - 1.2, hgt=0.45, flat=True)
                    # label holder + finger hole
                    lay.rect(xx + 3, yy + rh - bh + 2, bw - 8, 4, 'P', 5.4, hgt=0.6, flat=True)
                    lay.hline(xx + 4, yy + rh - bh + 4, max(1, bw - 11), 'I', 2.0, flat=True)
                    lay.rect(xx + bw // 2 - 2, yy + rh - 6, 3, 2, 'D', 0.6, hgt=0.2, flat=True)
                    xx += bw
        elif kind == 'ledgers':
            rows = 5
            rh = (L.FLOOR - 6 - top - 3) // rows
            for r in range(rows):
                yy = top + 3 + r * rh
                lay.rect(x0 + 1, yy + rh - 2, w - 2, 2, 'D', 3.0, hgt=0.4, flat=True)
                lay.rect(x0 + 1, yy + rh - 2, w - 2, 1, 'D', 4.0, hgt=0.45, flat=True)
                xx = x0 + 2
                while xx < x1 - 3:
                    sw = int(rng.integers(3, 6))
                    sh = rh - int(rng.integers(3, 8))
                    rm, t = [('D', 2.6), ('D', 3.2), ('B', 2.4), ('W', 4.0), ('D', 2.2), ('B', 1.8)][int(rng.integers(0, 6))]
                    if rng.random() < 0.06:
                        # a leaning volume
                        for k in range(sh - 2):
                            lay.rect(xx + k // 4, yy + rh - 3 - k, sw, 1, rm, t, hgt=0.4, flat=True)
                        xx += sw + 4
                        continue
                    lay.rect(xx, yy + rh - 2 - sh, sw, sh, rm, t, hgt=0.5, flat=True)
                    lay.rect(xx, yy + rh - 2 - sh, 1, sh, rm, t + 1.0, hgt=0.55, flat=True)
                    lay.rect(xx, yy + rh - sh + 1, sw, 1, 'A', 2.4, hgt=0.55, flat=True)   # gilt band
                    lay.rect(xx, yy + rh - 6, sw, 1, 'A', 2.0, hgt=0.55, flat=True)
                    xx += sw
                if rng.random() < 0.5:
                    pass
        # plinth
        lay.rect(x0, L.FLOOR - 6, w, 6, 'D', 1.2, hgt=0.3, flat=True)
        lay.rect(x0, L.FLOOR - 6, w, 1, 'D', 2.6, hgt=0.35, flat=True)
        # side posts
        lay.rect(x0, top, 2, L.FLOOR - top, 'D', 2.4, hgt=0.5, flat=True)
        lay.rect(x1 - 2, top, 2, L.FLOOR - top, 'D', 1.2, hgt=0.5, flat=True)

    def pendant(self, cx, top, length):
        lay = self.lay
        lay.rect(cx, top, 1, length, 'W', 3.0, hgt=0.5, flat=True)
        lay.rect(cx - 2, top, 5, 2, 'W', 4.0, hgt=0.6, flat=True)
        y = top + length
        # enamel shade: dark green outside, white inside, bulb glowing
        for i in range(8):
            hw = 2 + i
            lay.rect(cx - hw, y + i, 2 * hw + 1, 1, 'G', 2.6 + (0.6 if i < 2 else 0), hgt=0.6 + 0.04 * i, flat=True)
            lay.px(cx - hw, y + i, 'G', 4.2, hgt=0.5)
        lay.rect(cx - 9, y + 8, 19, 1, 'A', 6.0, emis=True, flat=True)
        lay.rect(cx - 7, y + 9, 15, 1, 'A', 5.0, emis=True, flat=True)
        lay.rect(cx - 2, y + 9, 5, 2, 'A', 6.0, emis=True, flat=True)
        self.lights.append({'pos': (cx, y + 10), 'kind': 'warm', 'energy': 1.15, 'radius': 120,
                            'height': 26, 'cone': (0.0, 1.0, 0.15), 'name': 'archive_pendant'})

    def sconce(self, cx, y):
        lay = self.lay
        lay.rect(cx - 2, y, 5, 6, 'A', 2.0, hgt=0.7, flat=True)               # back plate
        lay.rect(cx - 2, y, 5, 1, 'A', 3.4, hgt=0.7, flat=True)
        lay.rect(cx, y - 7, 1, 7, 'A', 2.4, hgt=0.8, flat=True)               # arm
        lay.rect(cx - 3, y - 13, 7, 6, 'A', 5.0, emis=True, flat=True)        # frosted tulip shade
        lay.rect(cx - 2, y - 14, 5, 1, 'A', 4.0, emis=True, flat=True)
        lay.rect(cx - 2, y - 12, 2, 3, 'A', 6.0, emis=True, flat=True)
        self.lights.append({'pos': (cx, y - 10), 'kind': 'warm', 'energy': 0.7, 'radius': 84,
                            'height': 16, 'name': 'archive_sconce'})

    # ------------------------------------------------------------------ light room
    def lightroom(self):
        lay = self.lay
        x0, x1 = L.LIGHTROOM
        self.dado(x0, x1, top=252)
        # exhaust hood + duct over the diazo machine (ammonia process)
        dx0, dx1 = L.DIAZO
        hx0, hx1 = dx0 - 4, dx1 + 2
        duct_x = (hx0 + hx1) // 2 - 7
        lay.rect(duct_x, self.frieze_bottom - 10, 14, 196 - self.frieze_bottom + 10, 'W', 4.6, hgt=0.7, flat=True)
        lay.rect(duct_x, self.frieze_bottom - 10, 1, 196 - self.frieze_bottom + 10, 'W', 6.2, hgt=0.65, flat=True)
        lay.rect(duct_x + 13, self.frieze_bottom - 10, 1, 196 - self.frieze_bottom + 10, 'W', 2.8, hgt=0.65, flat=True)
        for yy in range(self.frieze_bottom, 196, 22):
            lay.rect(duct_x - 1, yy, 16, 2, 'W', 5.6, hgt=0.8, flat=True)
            lay.rect(duct_x - 1, yy + 2, 16, 1, 'W', 3.0, hgt=0.7, flat=True)
            for k in range(duct_x + 1, duct_x + 14, 4):
                lay.px(k, yy, 'W', 7.4, hgt=0.9)
        lay.poly([(hx0, 214), (hx1, 214), (hx1 - 8, 196), (hx0 + 8, 196)], 'W', 4.4, hgt=0.6)
        lay.line(hx0, 214, hx0 + 8, 196, 'W', 6.6)
        lay.rect(hx0, 214, hx1 - hx0, 2, 'W', 2.6, hgt=0.6, flat=True)
        lay.rect(hx0 + 2, 216, hx1 - hx0 - 4, 2, 'W', 1.6, hgt=0.2, flat=True)
        # diazo machine (baked: it stands against the wall)
        my = 240
        lay.rect(dx0, my, dx1 - dx0, L.FLOOR - my, 'W', 4.4, hgt=0.6, flat=True)
        lay.rect(dx0, my, dx1 - dx0, 2, 'W', 6.4, hgt=0.65, flat=True)
        lay.rect(dx0, my, 1, L.FLOOR - my, 'W', 5.8, hgt=0.6, flat=True)
        lay.rect(dx1 - 1, my, 1, L.FLOOR - my, 'W', 2.4, hgt=0.6, flat=True)
        # feed table + rollers
        lay.rect(dx0 - 6, my + 3, dx1 - dx0 + 4, 3, 'W', 5.6, hgt=0.75, flat=True)
        lay.rect(dx0 - 6, my + 3, dx1 - dx0 + 4, 1, 'W', 7.2, hgt=0.8, flat=True)
        lay.rect(dx0 + 4, my + 7, dx1 - dx0 - 8, 3, 'I', 1.0, hgt=0.3, flat=True)          # slot
        lay.rect(dx0 + 4, my + 7, dx1 - dx0 - 8, 1, 'W', 2.2, hgt=0.35, flat=True)
        # a print half fed into the slot
        lay.rect(dx0 + 10, my - 1, 20, 4, 'P', 5.4, hgt=0.8, flat=True)
        lay.rect(dx0 + 12, my, 14, 1, 'B', 4.0, hgt=0.8, flat=True)
        # control panel with amber indicator + dials
        lay.rect(dx1 - 16, my + 13, 12, 10, 'W', 3.0, hgt=0.65, flat=True)
        lay.rect(dx1 - 16, my + 13, 12, 1, 'W', 5.0, hgt=0.7, flat=True)
        lay.rect(dx1 - 14, my + 15, 2, 2, 'A', 6.0, emis=True)
        lay.ellipse(dx1 - 8.5, my + 18.5, 2.0, 2.0, 'W', 6.0, hgt=0.8, flat=True)
        lay.px(dx1 - 9, my + 18, 'I', 1.0)
        # vents
        for yy in range(my + 28, L.FLOOR - 6, 3):
            lay.rect(dx0 + 5, yy, 18, 1, 'W', 2.6, hgt=0.4, flat=True)
        lay.rect(dx0, L.FLOOR - 4, dx1 - dx0, 4, 'W', 2.0, hgt=0.3, flat=True)
        # drying line with hanging prints
        ly = 150
        lay.rect(x0 + 4, ly - 2, 2, 5, 'W', 5.4, hgt=0.6, flat=True)
        lay.rect(dx0 - 18, ly - 2, 2, 5, 'W', 5.4, hgt=0.6, flat=True)
        pts = pg.catenary(x0 + 5, ly, dx0 - 17, ly, 5)
        for (px_, py_) in pts:
            lay.px(int(round(px_)), int(round(py_)), 'W', 5.6, hgt=0.3)
        for i, (sx, sw, sh) in enumerate([(x0 + 14, 22, 34), (x0 + 42, 18, 30), (x0 + 66, 24, 38)]):
            t = (sx - (x0 + 5)) / max(1, (dx0 - 17 - x0 - 5))
            sy = int(round(ly + 5 * 4 * t * (1 - t))) + 1
            lay.rect(sx, sy, sw, sh, 'P', 5.4, hgt=0.25, flat=True)
            lay.rect(sx, sy, sw, 1, 'P', 4.4, hgt=0.25, flat=True)
            lay.rect(sx + sw - 1, sy, 1, sh, 'P', 4.0, hgt=0.22, flat=True)
            # sag/curl at the bottom
            lay.rect(sx + 1, sy + sh, sw - 2, 1, 'P', 3.8, hgt=0.2, flat=True)
            # diazo blue lines (a plan section)
            rng = np.random.default_rng(70 + i)
            for k in range(4):
                yy = sy + 4 + k * int(sh / 5)
                lay.hline(sx + 2, yy, sw - 4 - int(rng.integers(0, 6)), 'B', 4.0, flat=True)
            lay.vline(sx + 3 + int(rng.integers(0, 6)), sy + 3, sh - 6, 'B', 4.4, flat=True)
            lay.vline(sx + sw - 6, sy + 6, sh - 12, 'B', 4.4, flat=True)
            # clips
            lay.rect(sx + 2, sy - 2, 2, 3, 'W', 6.6, hgt=0.6, flat=True)
            lay.rect(sx + sw - 4, sy - 2, 2, 3, 'W', 6.6, hgt=0.6, flat=True)
        # big paper roll dispenser above the light table
        rx0, rx1, ry = x0 + 18, x0 + 92, 206
        lay.rect(rx0 - 3, ry - 6, 3, 14, 'W', 4.0, hgt=0.6, flat=True)
        lay.rect(rx1, ry - 6, 3, 14, 'W', 4.0, hgt=0.6, flat=True)
        lay.rect(rx0, ry - 5, rx1 - rx0, 10, 'P', 4.6, hgt=0.6)
        lay.vgrad(rx0, ry - 5, rx1 - rx0, 10, 'P', 5.6, 3.0, hgt=0.6)
        lay.rect(rx0, ry + 5, rx1 - rx0, 1, 'W', 2.0, hgt=0.2, flat=True)
        lay.rect(rx0 + 8, ry + 5, rx1 - rx0 - 16, 3, 'P', 4.4, hgt=0.4, flat=True)      # paper tongue
        # wall-mounted drawing board rack
        # (left in shadow on purpose -- the light table is the focal light here)

    # ------------------------------------------------------------------ Emil's counter area
    def emil_area(self):
        lay = self.lay
        x0, x1 = L.EMIL
        self.dado(x0 + 12, x1 - 12, top=250)
        # entry pier
        self.pier(x0, x0 + 12)
        # pigeonhole wall behind the counter
        px_, py_, pw, ph = L.PIGEON
        lay.rect(px_ - 3, py_ - 3, pw + 6, ph + 6, 'D', 2.2, hgt=0.6, flat=True)
        lay.rect(px_ - 3, py_ - 3, pw + 6, 1, 'D', 4.0, hgt=0.65, flat=True)
        lay.rect(px_ - 4, py_ - 6, pw + 8, 3, 'D', 3.0, hgt=0.75, flat=True)
        lay.rect(px_ - 4, py_ - 6, pw + 8, 1, 'D', 4.6, hgt=0.8, flat=True)
        rng = np.random.default_rng(88)
        cell = 16
        for r in range(ph // cell):
            for c in range(pw // cell):
                cx, cy = px_ + c * cell, py_ + r * cell
                recess(lay, cx + 1, cy + 1, cell - 2, cell - 2, 'D', 0.8, hgt=-0.5, shadow=0.2, light=1.4)
                lay.rect(cx, cy, cell, 1, 'D', 3.0, hgt=0.5, flat=True)
                lay.rect(cx, cy, 1, cell, 'D', 2.6, hgt=0.5, flat=True)
                k = rng.random()
                if k < 0.35:      # stacked folders
                    for q in range(int(rng.integers(2, 5))):
                        yy = cy + cell - 3 - q * 2
                        tt = float(rng.choice([3.0, 3.6, 4.2, 4.8]))
                        lay.rect(cx + 2, yy, cell - 4, 2, 'P', tt, hgt=0.3, flat=True)
                        lay.px(cx + 2, yy, 'P', tt + 1.2)
                elif k < 0.6:     # index cards upright
                    for q in range(cell - 5):
                        if rng.random() < 0.75:
                            hh = int(rng.integers(5, 9))
                            lay.rect(cx + 2 + q, cy + cell - 2 - hh, 1, hh, 'P', float(rng.choice([4.0, 4.8, 5.4])),
                                     hgt=0.3, flat=True)
                elif k < 0.75:    # rolled documents
                    self.roll_stamp(cx + 7, cy + 7, self.ROLL7, 3.6)
                    self.roll_stamp(cx + 2, cy + 9, self.ROLL5, 3.0)
                # number plate on some cells
                if rng.random() < 0.3:
                    lay.rect(cx + 5, cy + 1, 6, 2, 'P', 5.4, hgt=0.55, flat=True)
        lay.rect(px_ + pw + 3, py_ - 3, 1, ph + 6, 'W', 1.4, flat=True)
        # sign above: AUSGABE on an enamel plate
        m = kit.text_mask('AUSGABE', '57')
        sw = m.shape[1] + 8
        sx = px_ + (pw - sw) // 2
        sy = py_ - 22
        lay.rect(sx, sy, sw, 12, 'W', 2.0, hgt=0.5, flat=True)
        lay.rect(sx, sy, sw, 1, 'W', 4.6, hgt=0.55, flat=True)
        lay.rect(sx + 1, sy + 1, sw - 2, 10, 'W', 1.2, hgt=0.5, flat=True)
        lay.put(m, sx + 4, sy + 3, 'P', 5.0, flat=True)
        lay.rect(sx + 3, sy - 6, 1, 6, 'W', 3.0, flat=True)
        lay.rect(sx + sw - 4, sy - 6, 1, 6, 'W', 3.0, flat=True)
        # notice board (cork) with pinned sheets -- the typed list is the big one
        nx, ny, nw, nh = L.NOTICE
        lay.rect(nx - 2, ny - 2, nw + 4, nh + 4, 'D', 2.0, hgt=0.5, flat=True)
        lay.rect(nx - 2, ny - 2, nw + 4, 1, 'D', 3.6, hgt=0.55, flat=True)
        cork = pg.white_noise(nw, nh, 12)
        lay.put(np.ones((nh, nw), bool), nx, ny, 'D', 3.4 + (cork > 0.6) * 0.8 - (cork < 0.2) * 0.6, hgt=0.2)
        # typed list (obs_notice)
        lx, ly = nx + 3, ny + 3
        lay.rect(lx, ly, 17, 24, 'P', 6.0, hgt=0.3, flat=True)
        lay.rect(lx + 17, ly + 1, 1, 24, 'D', 1.6, flat=True)
        lay.rect(lx, ly, 17, 1, 'P', 5.0, flat=True)
        disc, pillar = kit.reichssiegel_mask(4)
        lay.put(disc, lx + 1, ly + 2, 'N', 0.6, flat=True)
        for k in range(8):
            yy = ly + 7 + k * 2
            lay.hline(lx + 2, yy, 6 + (k * 3) % 4, 'I', 2.0, flat=True)
            lay.hline(lx + 10, yy, 5, 'I', 2.0, flat=True)
        lay.px(lx + 8, ly, 'R', 2.0)
        # smaller sheets
        lay.rect(nx + 23, ny + 4, 10, 13, 'P', 4.6, hgt=0.3, flat=True)
        pseudo_text(lay, nx + 24, ny + 7, 8, 4, 'I', 2.0, seed=91, gap=2)
        lay.px(nx + 27, ny + 4, 'A', 4.0)
        lay.rect(nx + 22, ny + 22, 12, 9, 'P', 5.2, hgt=0.3, flat=True)
        pseudo_text(lay, nx + 23, ny + 24, 10, 3, 'I', 2.0, seed=92, gap=2)
        lay.px(nx + 27, ny + 22, 'A', 4.0)
        lay.rect(nx + 4, ny + 30, 14, 9, 'P', 4.0, hgt=0.3, flat=True)
        pseudo_text(lay, nx + 5, ny + 32, 12, 3, 'I', 2.0, seed=93, gap=2)
        lay.rect(nx + nw + 2, ny - 1, 1, nh + 4, 'W', 1.6, flat=True)
        # framed perspective rendering of the Great Hall (image of power over the waiting bench)
        fx, fy, fw, fh = X(1490), 176, 30, 22
        lay.rect(fx - 2, fy - 2, fw + 4, fh + 4, 'D', 3.0, hgt=0.5, flat=True)
        lay.rect(fx - 2, fy - 2, fw + 4, 1, 'D', 4.6, hgt=0.55, flat=True)
        lay.rect(fx, fy, fw, fh, 'P', 3.6, hgt=0.2, flat=True)
        lay.vgrad(fx, fy, fw, fh - 6, 'P', 4.6, 3.6, hgt=0.2)
        dm, _, _ = lay.ellipse_mask(fx + fw / 2, fy + fh - 6, 9, 8)
        lay.put(dm, int(math.floor(fx + fw / 2 - 9)), int(math.floor(fy + fh - 6 - 8)), 'W', 3.6, flat=True)
        lay.rect(fx + 3, fy + fh - 7, fw - 6, 4, 'W', 3.0, flat=True)
        lay.rect(fx, fy + fh - 3, fw, 3, 'W', 4.4, flat=True)
        lay.rect(fx + fw // 2, fy + fh - 17, 1, 3, 'W', 3.0, flat=True)
        lay.rect(fx + fw + 2, fy - 1, 1, fh + 4, 'W', 1.6, flat=True)
        self.master_plan(X(1362), 50, 104, 66)
        self.loudspeaker(X(1522), 104)
        # door to the stacks behind the issue counter (the stairwell is now at the far left of the floor)
        self.double_door(L.EXIT_DOOR[0], L.EXIT_DOOR[1], 186, lit=False)
        m = kit.text_mask('MAGAZIN', '35')
        tw = m.shape[1]
        cx = (L.EXIT_DOOR[0] + L.EXIT_DOOR[1]) // 2
        lay.rect(cx - tw // 2 - 2, 158, tw + 4, 8, 'W', 1.6, hgt=0.5, flat=True)
        lay.put(m, cx - tw // 2, 159, 'P', 4.4, flat=True)
        m2 = kit.text_mask('KEIN ZUTRITT', '35')
        lay.rect(cx - m2.shape[1] // 2 - 2, 228, m2.shape[1] + 4, 8, 'P', 5.4, hgt=0.5, flat=True)
        lay.put(m2, cx - m2.shape[1] // 2, 229, 'R', 1.0, flat=True)
        # end wall (poche)
        lay.rect(x1 - 10, 0, 10, L.FLOOR, 'W', 1.2, hgt=0.9, flat=True)
        lay.rect(x1 - 10, 0, 1, L.FLOOR, 'W', 3.0, hgt=0.8, flat=True)

    def master_plan(self, x, y, w, h):
        """Framed general development plan of the capital: the axis and the hall dominate the archive."""
        lay = self.lay
        lay.rect(x - 3, y - 3, w + 6, h + 6, 'D', 2.2, hgt=0.6, flat=True)
        lay.rect(x - 3, y - 3, w + 6, 1, 'D', 3.8, hgt=0.65, flat=True)
        lay.rect(x - 1, y - 1, w + 2, h + 2, 'D', 1.2, hgt=0.4, flat=True)
        lay.rect(x, y, w, h, 'P', 3.4, hgt=0.2, flat=True)
        rng = np.random.default_rng(64)
        # street blocks
        for k in range(26):
            bx = x + 3 + int(rng.integers(0, w - 12))
            by = y + 3 + int(rng.integers(0, h - 10))
            lay.rect(bx, by, int(rng.integers(4, 10)), int(rng.integers(3, 7)), 'P', 2.4, flat=True)
        # river
        pts = [(x, y + 40), (x + 20, y + 36), (x + 38, y + 44), (x + 60, y + 41), (x + 80, y + 50), (x + w, y + 47)]
        for a, b in zip(pts[:-1], pts[1:]):
            for (px_, py_) in kit.bres(a[0], a[1], b[0], b[1]):
                lay.rect(px_, py_, 1, 2, 'B', 3.0, flat=True)
        # the monumental north-south axis and the hall (circle) at its end
        cx = x + w // 2 + 6
        lay.rect(cx - 1, y + 2, 3, h - 4, 'P', 5.4, flat=True)
        lay.rect(cx - 1, y + 2, 1, h - 4, 'R', 1.0, flat=True)
        m, mx, my = lay.ellipse_mask(cx + 0.5, y + 14.5, 7.0, 7.0)
        lay.put(m, mx, my, 'P', 5.6, flat=True)
        lay.put(kit.edge_of(m), mx, my, 'R', 1.0, flat=True)
        lay.rect(x + 6, y + h - 9, 30, 5, 'P', 5.0, flat=True)                 # cartouche
        lay.hline(x + 8, y + h - 7, 24, 'I', 2.0, flat=True)
        disc, pillar = kit.reichssiegel_mask(5)
        lay.put(disc, x + w - 9, y + h - 9, 'N', 0.6, flat=True)
        lay.put(pillar, x + w - 9, y + h - 9, 'P', 5.0, flat=True)
        lay.rect(x + w + 3, y - 2, 1, h + 6, 'W', 1.4, flat=True)

    def loudspeaker(self, x, y):
        """Wall-mounted public-address horn: the hall's announcements reach even the archive."""
        lay = self.lay
        lay.rect(x + 4, self.frieze_bottom, 1, y - self.frieze_bottom, 'W', 3.4, hgt=0.3, flat=True)   # conduit
        lay.rect(x + 2, y, 6, 4, 'W', 3.0, hgt=0.6, flat=True)                                         # bracket
        lay.rect(x + 2, y, 6, 1, 'W', 5.0, hgt=0.65, flat=True)
        horn = [(x + 4, y + 4), (x + 8, y + 5), (x + 16, y + 15), (x + 6, y + 19), (x + 3, y + 8)]
        lay.poly(horn, 'W', 3.6, hgt=0.7)
        lay.line(x + 4, y + 4, x + 3, y + 8, 'W', 5.4)
        lay.line(x + 8, y + 5, x + 16, y + 15, 'W', 2.0)
        lay.line(x + 16, y + 15, x + 6, y + 19, 'W', 1.2)
        lay.line(x + 15, y + 15, x + 7, y + 18, 'I', 1.0)                                              # mouth

    # ------------------------------------------------------------------ office
    def office(self):
        lay = self.lay
        x0, x1 = L.OFFICE
        self.dado(x0 + 8, x1, top=248)
        for (px0, px1) in L.PILASTERS:
            self.pilaster(px0, px1, self.frieze_bottom + 8)
        items = ['plant', None, 'rolls']
        blinds = [0, 0, 24]
        for i, (wx0, wx1) in enumerate(L.WINDOWS):
            self.window(wx0, wx1, i, blind=blinds[i], sill_item=items[i])
        self.double_door(L.DOOR0[0], L.DOOR0[1], L.DOOR0_TOP, glass_text='ZEICHENBÜRO', lit=True, seed=4)
        self.poster()
        self.framed_notice(X(512), 192, 14, 18, seed=7)
        self.framed_notice(X(494), 222, 10, 12, seed=8, emblem=False)    # clear of the binders (round 10)
        self.clock()
        self.filing_cabinets(*L.CABINETS)
        # light switch + cable conduit by the door
        lay.rect(L.DOOR0[1] + 10, 230, 4, 6, 'P', 3.6, hgt=0.5, flat=True)
        lay.rect(L.DOOR0[1] + 11, 232, 2, 2, 'D', 3.0, hgt=0.6, flat=True)
        lay.rect(L.DOOR0[1] + 11, 120, 1, 110, 'W', 3.4, hgt=0.3, flat=True)
        # lit corridor behind the door: dim warm light
        self.lights.append({'pos': ((L.DOOR0[0] + L.DOOR0[1]) / 2, 214), 'kind': 'warm', 'energy': 0.35,
                            'radius': 60, 'height': 6, 'name': 'corridor_glass'})
        # ghost of a removed portrait: a cleaner rectangle of plaster with a dust edge and its nail
        gx, gy, gw, gh = X(462), 96, 28, 36
        lay.shade_rect(gx, gy, gw, gh, 0.75)
        lay.rect(gx, gy, gw, 1, 'W', 3.2, flat=True)
        lay.rect(gx - 1, gy, 1, gh, 'W', 3.4, flat=True)
        lay.shade_rect(gx + 2, gy + 2, gw - 4, gh - 4, 0.25)
        lay.px(gx + gw // 2, gy - 5, 'I', 1.0, hgt=0.5)
        lay.line(gx + gw // 2, gy - 5, gx + 3, gy, 'W', 3.6)
        lay.line(gx + gw // 2, gy - 5, gx + gw - 4, gy, 'W', 3.6)
        # damp stains below the window sills and a hairline crack from the cornice
        rng = np.random.default_rng(23)
        for (a, b) in L.WINDOWS:
            for k in range(3):
                sx = int(rng.integers(a - 6, b + 6))
                ln = int(rng.integers(6, 14))
                for yy in range(L.WIN_Y[1] + 10, L.WIN_Y[1] + 10 + ln):
                    lay.shade_rect(sx + int(rng.integers(-1, 2)), yy, 2, 1, -0.6)
        crack = [(X(300), self.frieze_bottom), (X(302), 58), (X(299), 66), (X(303), 79), (X(301), 92),
                 (X(305), 101)]
        for a, b in zip(crack[:-1], crack[1:]):
            for (x, y) in kit.bres(a[0], a[1], b[0], b[1]):
                lay.shade_rect(x, y, 1, 1, -1.4)

    # ------------------------------------------------------------------ floor
    def floor(self):
        lay = self.lay
        W, H = L.WORLD_W, L.WORLD_H
        y0 = L.FLOOR
        rows = [0, 3, 7, 12, 18, 25, 33, 42, 52, 63, 75]
        rng = np.random.default_rng(17)
        nrm = (0.0, 0.86, 0.5)
        ys = np.arange(H, dtype=np.float32)[:, None]
        xs = np.arange(W, dtype=np.float32)[None, :]
        f = np.maximum((ys - L.HORIZON) / (L.FLOOR - L.HORIZON), 1e-3)
        rowidx = np.searchsorted(np.array(rows) + y0, np.arange(H), side='right') - 1
        # --- office parquet (warm wood), from the library partition to the archive partition
        ox0, ox1 = L.PARTL[0], L.PART1[1]
        vp = L.X(284)
        for i in range(len(rows) - 1):
            ra, rb = y0 + rows[i], y0 + rows[i + 1]
            t = 2.6 + (0.5 if i % 2 else 0.0)
            lay.rect(ox0, ra, ox1 - ox0, rb - ra, 'D', t, hgt=0.0, flat=True)
            lay.rect(ox0, ra, ox1 - ox0, 1, 'D', 1.2, hgt=0.0, flat=True)
            span = int(46 * (1 + i * 0.35))
            off = int(rng.integers(0, span))
            ff = (ra + 1 - L.HORIZON) / (L.FLOOR - L.HORIZON)
            for bx in range(ox0 - span + off - 400, ox1 + span + 400, span):
                xx = int(round(vp + (bx - vp) * ff))
                if ox0 <= xx < ox1:
                    lay.rect(xx, ra + 1, 1, rb - ra - 1, 'D', 1.4, flat=True)
                    lay.rect(xx + 1, ra + 1, 1, rb - ra - 1, 'D', t + 0.6, flat=True)
        # --- library: herringbone oak parquet in perspective (courses alternate their slant)
        lx0, lx1 = L.PART0[0], L.PARTL[0]
        vpl = (L.LIBRARY[0] + L.LIBRARY[1]) / 2
        u = vpl + (xs - vpl) / f
        rr = np.array(rows, np.float32) + y0
        cidx = np.clip(rowidx, 0, len(rows) - 2)
        top = rr[cidx][:, None]
        hgt_c = (rr[np.clip(cidx + 1, 0, len(rows) - 1)] - rr[cidx])[:, None]
        tloc = np.clip((ys - top) / np.maximum(hgt_c, 1), 0, 1)
        Pl = 14.0
        sgn = np.where((cidx % 2)[:, None] == 0, 1.0, -1.0)
        uu = u + sgn * tloc * Pl * 0.9
        k = np.floor(uu / Pl).astype(np.int64)
        joint = np.zeros(k.shape, bool)
        joint[:, 1:] = k[:, 1:] != k[:, :-1]
        hsh = ((k * 73856093) ^ (cidx[:, None].astype(np.int64) * 19349663)) % 5
        tone = 2.7 + hsh.astype(np.float32) * 0.18
        tone = np.where(joint, 1.3, tone)
        m = np.zeros((H, W), bool)
        m[y0:, lx0:lx1] = True
        lay.put(m, 0, 0, 'D', tone, hgt=0.0, flat=True)
        for i in range(len(rows) - 1):
            lay.rect(lx0, y0 + rows[i], lx1 - lx0, 1, 'D', 1.4, hgt=0.0, flat=True)
        # the hidden cupboard door of section V has swept a clean quarter arc into the dust
        if self.hidden_floor_arc:
            hx, hy, rad = self.hidden_floor_arc
            for a in np.linspace(0.0, math.pi / 2, 60):
                px_ = hx - rad * math.cos(a)
                dz = rad * math.sin(a) / 24.0                                       # floor rows are ~24 px deep
                py_ = y0 + float(np.interp(dz, np.arange(len(rows)), rows)) + 1
                lay.shade_rect(int(round(px_)), int(round(py_)), 2, 1, 0.9)
            for k2 in range(3):                                                     # fine scratches
                lay.shade_rect(hx - rad + 4 + k2 * 7, y0 + 2 + (k2 % 2), 5, 1, -0.7)
        # --- hall: stone floor, large slabs with a dark border band along the wall
        hx0, hx1 = 0, L.PART0[0]
        vph = (L.HALL[0] + L.HALL[1]) / 2
        uh = vph + (xs - vph) / f
        colh = np.floor(uh / 32).astype(np.int32)
        jh = np.zeros_like(colh, bool)
        jh[:, 1:] = colh[:, 1:] != colh[:, :-1]
        chk = ((colh + (rowidx[:, None] // 2)) % 2).astype(np.float32)
        th = 4.2 + 0.5 * chk
        th = np.where(jh, 2.6, th)
        band = (rowidx[:, None] <= 0) + np.zeros_like(th, bool)
        th = np.where(band, 3.0, th)
        m = np.zeros((H, W), bool)
        m[y0:, hx0:hx1] = True
        lay.put(m, 0, 0, 'W', th, hgt=0.0, flat=True)
        for i in range(0, len(rows) - 1, 2):
            lay.rect(hx0, y0 + rows[i], hx1 - hx0, 1, 'W', 2.6, hgt=0.0, flat=True)
        # a wet trail of melt water from the stairwell door (Konrad came in from the snow)
        for k2 in range(14):
            sx = L.STAIR_DOOR[0] + 18 + k2 * 9 + int(rng.integers(-2, 3))
            sy = y0 + 6 + int(rng.integers(0, 6))
            lay.shade_rect(sx, sy, 3, 1, -0.9)
            lay.shade_rect(sx + 1, sy - 1, 1, 1, 1.2)
        # --- archive / light room / emil: polished stone tiles (cold), per-room perspective
        sx0 = ox1
        for (rx0, rx1) in (L.ARCHIVE, L.LIGHTROOM, L.EMIL):
            vp2 = (rx0 + rx1) / 2
            u2 = vp2 + (xs - vp2) / f
            col = np.floor(u2 / 24).astype(np.int32)
            joint2 = np.zeros_like(col, bool)
            joint2[:, 1:] = col[:, 1:] != col[:, :-1]
            chk2 = ((col + rowidx[:, None]) % 2).astype(np.float32)
            tone2 = 4.4 + 0.45 * chk2
            tone2 = np.where(joint2, 2.8, tone2)
            m = np.zeros((H, W), bool)
            m[y0:, max(rx0, sx0):rx1] = True
            lay.put(m, 0, 0, 'W', tone2, hgt=0.0, flat=True)
        for i in range(len(rows) - 1):
            ra = y0 + rows[i]
            lay.rect(sx0, ra, W - sx0, 1, 'W', 2.6, hgt=0.0, flat=True)
        # skirting shadow line + contact shadow along the wall
        lay.rect(0, y0, W, 1, 'W', 1.0, flat=True)
        lay.shade_rect(0, y0 + 1, W, 3, -0.6)
        # normals: horizontal floor faces up (+Y), slightly toward the viewer
        m = np.zeros((H, W), bool)
        m[y0:, :] = lay.rid[y0:, :] >= 0
        lay.paint_normal(m, 0, 0, nrm)
        # depth falloff toward the bottom edge
        fall = np.zeros((H, W), np.float32)
        yy = np.arange(H, dtype=np.float32)
        fz = np.clip((yy - 318) / 42, 0, 1) * -1.3
        fall[:] = fz[:, None]
        lay.amb_field(fall)

    # ------------------------------------------------------------------ ambient darkness
    def ambient(self):
        """Art-directed ambient: rooms without windows sink into shadow, the ceiling zone is dark,
        corners get occlusion.  Lamps (baked later) carve the light back out."""
        lay = self.lay
        W, H = L.WORLD_W, L.WORLD_H
        f = np.zeros((H, W), np.float32)
        xs = np.arange(W, dtype=np.float32)
        reg = np.zeros(W, np.float32)
        reg[:L.PART0[1]] = -0.45             # arrival hall: one window, lodge lamp, pendant
        reg[L.PART0[1]:L.PARTL[0]] = -0.35   # reading room: lamps + two windows
        reg[L.PART1[0]:] = -1.0
        reg[L.LIGHTROOM[0]:] = -0.8
        reg[L.EMIL[0]:] = -0.9
        # soften region transitions over 24 px
        k = np.ones(25, np.float32) / 25
        reg = np.convolve(np.pad(reg, 12, mode='edge'), k, mode='valid')
        f += reg[None, :]
        ys = np.arange(H, dtype=np.float32)[:, None]
        f += -0.9 * np.clip((150 - ys) / 110, 0, 1)            # high wall zone falls into darkness
        # end-wall occlusion
        f += -1.0 * np.clip((40 - xs) / 30, 0, 1)[None, :]
        f += -1.0 * np.clip((xs - (W - 40)) / 30, 0, 1)[None, :]
        f[lay.emis] = 0
        lay.amb_field(f)

    # ------------------------------------------------------------------ mouse hole (exp_mouse)
    def mouse_hole(self):
        """A gnawed hole in the oak plinth of the box shelving; the mouse actor lives here."""
        lay = self.lay
        hx, hy = L.MOUSE_HOLE
        x0 = hx - 2
        lay.rect(x0, L.FLOOR - 4, 5, 4, 'D', 3.0, hgt=0.3, flat=True)            # gnawed, lighter rim
        lay.rect(x0 + 1, L.FLOOR - 3, 3, 3, 'N', 0.0, hgt=-0.4, flat=True)        # the dark hole
        lay.px(x0 + 2, L.FLOOR - 4, 'N', 0.3, hgt=-0.4)
        lay.px(x0, L.FLOOR - 4, 'D', 1.2)
        lay.px(x0 + 4, L.FLOOR - 4, 'D', 1.2)
        for k in (-4, 7, 9):                                                    # crumbs / droppings
            lay.px(x0 + k, L.FLOOR, 'D', 1.0)

    # ------------------------------------------------------------------ pneumatic tube network
    def tube_network(self):
        """Brass Rohrpost tube along the frieze from the librarian's desk to the archive station and Emil's
        counter (skipping the cut partition walls), with the receiving station on the last archive pier."""
        lay = self.lay
        y = self.frieze_bottom + 1
        x0, x1 = L.LIB_DESK[1] - 7, L.EMIL[0] + 64
        cuts = [L.PARTL, L.PART1, L.PART2]
        x = x0
        for (c0, c1) in cuts + [(x1, x1)]:
            if c0 - 4 > x:
                lay.rect(x, y, c0 - x - 4, 2, 'A', 2.2, hgt=0.6, flat=True)
                lay.rect(x, y, c0 - x - 4, 1, 'A', 3.4, hgt=0.62, flat=True)
                for k in range(x + 30, c0 - 6, 40):
                    lay.rect(k, y - 1, 2, 4, 'A', 3.0, hgt=0.7, flat=True)               # clamps
            x = c1 + 4
        # drop to the archive receiving station on the last pier
        sx, sy = L.TUBE_STATION
        tx = sx + 4
        lay.rect(tx, y, 3, sy - y, 'A', 2.6, hgt=0.75, flat=True)
        lay.rect(tx, y, 1, sy - y, 'A', 4.2, hgt=0.78, flat=True)
        for yy in range(y + 16, sy - 4, 24):
            lay.rect(tx - 1, yy, 5, 2, 'A', 3.4, hgt=0.8, flat=True)
        # station: brass body with a hinged flap (the flap is animated by an actor) and a wire basket
        lay.rect(sx + 1, sy, 10, 14, 'A', 2.8, hgt=0.85, flat=True)
        lay.rect(sx + 1, sy, 10, 1, 'A', 4.4, hgt=0.88, flat=True)
        lay.rect(sx + 1, sy, 1, 14, 'A', 4.0, hgt=0.86, flat=True)
        lay.rect(sx + 10, sy, 1, 14, 'A', 1.6, hgt=0.8, flat=True)
        lay.rect(sx + 3, sy + 3, 6, 6, 'N', 0.6, hgt=0.5, flat=True)                   # the tube mouth
        lay.rect(sx, sy + 16, 12, 6, 'K', 2.0, hgt=0.6, flat=True)                      # basket
        for k in range(sx + 1, sx + 12, 2):
            lay.rect(k, sy + 16, 1, 6, 'K', 4.0, hgt=0.65, flat=True)
        lay.rect(sx, sy + 21, 12, 1, 'K', 4.6, hgt=0.65, flat=True)
        m = kit.text_mask('ROHRPOST', '35')
        lay.rect(sx - 10, sy - 9, m.shape[1] + 4, 7, 'P', 5.2, hgt=0.6, flat=True)
        lay.put(m, sx - 8, sy - 8, 'I', 1.0, flat=True)
        self.tube_station = (sx, sy)
        # drop to Emil's counter (beside the pigeonhole wall)
        ex = L.PIGEON[0] - 10
        lay.rect(ex, y, 3, 238 - y, 'A', 2.4, hgt=0.7, flat=True)
        lay.rect(ex, y, 1, 238 - y, 'A', 4.0, hgt=0.72, flat=True)

    # ------------------------------------------------------------------ build
    def build(self):
        import env_berlin_hall as EH
        import env_berlin_library as ELB
        self.base()
        EH.paint_hall(self)
        self.partition(L.PART0[0], L.PART0[1], 176)
        ELB.paint_library(self)
        self.partition(L.PARTL[0], L.PARTL[1], 176)
        self.office()
        self.partition(L.PART1[0], L.PART1[1], 176)
        self.archive()
        self.mouse_hole()
        self.partition(L.PART2[0], L.PART2[1], 180)
        self.lightroom()
        self.emil_area()
        self.tube_network()
        self.floor()
        self.ambient()
        return self.lay


# =========================================================================== shafts
def window_shafts(windows, w=L.WORLD_W, h=L.WORLD_H, ax=0.9, az=1.0, kz=0.35):
    """Volumetric light from back-wall windows (3-D rays projected to the side view).
    Returns (air density field, floor landing field), both normalised to ~[0,1]."""
    air = np.zeros((h, w), np.float32)
    land = np.zeros((h, w), np.float32)
    for win in windows:
        g = win['glass']
        gy, gx = np.nonzero(g)
        xg = gx.astype(np.float32) + win['x0'] + 0.5
        yg = gy.astype(np.float32) + win['y0'] + 0.5
        tend = (L.FLOOR - yg)
        tmax = int(tend.max()) + 1
        for t in range(0, tmax, 1):
            alive = tend > t
            if not alive.any():
                break
            sx = np.round(xg[alive] + ax * t).astype(np.int32)
            sy = np.round(yg[alive] + t * (1 + kz * az)).astype(np.int32)
            ok = (sx >= 0) & (sx < w) & (sy >= 0) & (sy < h)
            np.add.at(air, (sy[ok], sx[ok]), 1.0)
        lx = np.round(xg + ax * tend).astype(np.int32)
        ly = np.round(L.FLOOR + kz * az * tend).astype(np.int32)
        ok = (lx >= 0) & (lx < w) & (ly >= 0) & (ly < h)
        np.add.at(land, (ly[ok], lx[ok]), 1.0)
    # soften a little (box blur) so the integration noise does not alias
    air = box_blur(air, 2)
    land = box_blur(land, 1)
    air /= max(1e-6, np.percentile(air[air > 0], 99.5)) if (air > 0).any() else 1
    land /= max(1e-6, np.percentile(land[land > 0], 97)) if (land > 0).any() else 1
    return np.clip(air, 0, 1.2), np.clip(land, 0, 1.2)


def box_blur(a, r):
    if r <= 0:
        return a
    k = 2 * r + 1
    p = np.pad(a, r, mode='edge')
    c = np.cumsum(np.cumsum(p, 0), 1)
    c = np.pad(c, ((1, 0), (1, 0)))
    out = (c[k:, k:] - c[:-k, k:] - c[k:, :-k] + c[:-k, :-k]) / (k * k)
    return out.astype(np.float32)


# =========================================================================== lights
def scene_lights():
    """Baked + dynamic light list (world coords) for the whole scene (excluding room-built ones)."""
    return [
        {'name': 'window_%d' % (i + 1), 'pos': ((a + b) / 2, 200), 'kind': 'cold', 'energy': 0.9, 'radius': 110,
         'height': -14} for i, (a, b) in enumerate(L.WINDOWS)
    ] + [
        {'name': 'window_h%d' % (i + 1), 'pos': ((a + b) / 2, 200), 'kind': 'cold', 'energy': 0.8, 'radius': 104,
         'height': -14} for i, (a, b) in enumerate(L.HALL_WINDOWS)
    ] + [
        {'name': 'window_l%d' % (i + 1), 'pos': ((a + b) / 2, 206), 'kind': 'cold', 'energy': 0.85, 'radius': 110,
         'height': -14} for i, (a, b) in enumerate(L.LIB_WINDOWS)
    ]


def compute_fields(room: Room, lay, lights):
    """Light fields for a room-sized MLayer: normal-mapped lamps + window shafts + floor reflections."""
    F = kit.light_fields(lay, lights)
    air, land = room.shaft_air, room.shaft_land
    floor = np.zeros_like(air)
    floor[L.FLOOR:, :] = 1.0
    F['cold'] += (air ** 0.85) * 0.55 + land * floor * 0.75
    # reflections of the bright windows in the polished floors (vertical, dithered streaks)
    refl = np.zeros_like(air)
    for (a, b) in L.ALL_WINDOWS:
        for yy in range(L.FLOOR + 1, L.FLOOR + 30):
            k = (1 - (yy - L.FLOOR) / 30) ** 1.4
            refl[yy, a + 2:b - 2] += 0.55 * k
    # warm lamp reflections on the stone floors (hall, archive, light room, Emil)
    for lt in lights:
        x = lt['pos'][0]
        if lt['kind'] in ('warm', 'white') and (x > L.PART1[1] or x < L.PART0[0]):
            xi = int(x)
            for yy in range(L.FLOOR + 1, L.FLOOR + 40):
                k = (1 - (yy - L.FLOOR) / 40) ** 1.6
                F[lt['kind']][yy, max(0, xi - 3):xi + 4] += 0.35 * k * lt['energy']
    F['cold'] += refl
    return F


def bake(room: Room, extra_lights=None):
    lay = room.lay
    lights = scene_lights() + room.lights + (extra_lights or [])
    air, land = window_shafts(room.windows)
    room.shaft_air, room.shaft_land = air, land
    F = compute_fields(room, lay, lights)
    room.fields = F
    room.all_lights = lights
    lay.resolve(F)
    return room
