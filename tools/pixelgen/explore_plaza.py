"""explore_plaza -- close-ups for the plaza exploration finds during the parade (owner: plaza-explore).

Writes assets/explore/plaza/<name>.png (240 x 150 px, pixel art 1:1, shown x3 by the discovery view,
TECHNICAL_ARCHITECTURE 12.1).  Close-ups whose subject is regime iconography also get <name>_hist.png with the
real historical insignia (12.4: the neutral file always exists; loaders resolve via Symbols.pick):
  poster   the parade poster: state emblem above the dome (neutral: fictional Reichssiegel)
  banner   the facade banners (neutral: Reichssiegel on the white disc)
Painting toolkit (tone-space Canvas, masks, 3x5/5x7 fonts, emblems) is imported read-only from
explore_berlin.py, so both chapters share one look and one palette (pg.py scene ramps, Bayer dithering).
Light = the parade evening of hall_plaza: snow clouds, searchlight shafts, warm accents where people keep warm.
Nothing is traced or sampled; all text is in-world fiction.  Deterministic: seeds are crc32 of the names.

Run:  py -3 -P tools/pixelgen/explore_plaza.py [--preview DIR] [names...]
"""
from __future__ import annotations

import math
import os
import sys

import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import explore_berlin as eb  # noqa: E402  (read-only shared close-up toolkit)
from explore_berlin import (Canvas, edge, dilate, ellipse_mask, paper_sheet, typed_line, tack,  # noqa: E402
                            reichssiegel, hakenkreuz, eagle_mask, scribble)

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
OUT = os.path.join(ROOT, 'assets', 'explore', 'plaza')
W, H = eb.W, eb.H
YY, XX = eb.YY, eb.XX


# =========================================================================== shared pieces
def snowfall(cv: Canvas, n=70, seed=0, y0=0, y1=H):
    rng = np.random.default_rng(cv.seed + seed)
    for _ in range(n):
        x, y = int(rng.integers(0, W)), int(rng.integers(y0, y1))
        cv.px(x, y, 'snow', 4 if rng.random() < 0.6 else 3)


def overcast(cv: Canvas, y1=H, t0=1.4, t1=3.0):
    """Evening sky of the parade (env hall_plaza is lit for the Lichtdom): snow cloud cover over the city glow,
    with the pale shafts of the searchlights rising behind the scene."""
    cv.grad(0, 0, W, y1, 'violet', 1.0, 4.4)
    sky = cv.full((np.ones((y1, W), bool), 0, 0))
    cv.noise(26, 0.45, sky, seed_add=3)
    for k, xb in enumerate((30 + cv.seed % 50, 120 + cv.seed % 40, 200 + cv.seed % 30)):
        lean = (k - 1) * 18 + (cv.seed % 7) - 3
        beam = cv.full(cv.poly([(xb - 2, y1), (xb + 2, y1), (xb + lean + 6, 0), (xb + lean - 6, 0)], 'snow', 0.3))
        cv.adjust(np.clip(YY / max(1.0, y1), 0, 1) * 0.6, beam)


def stone_wall(cv: Canvas, tone=7.0, course=14, seed=1, x0=0, y0=0, w=W, h=H, ramp='sepia'):
    m = cv.full(cv.rect(x0, y0, w, h, ramp, tone))
    cv.noise(10, 0.45, m, seed_add=seed)
    cv.grain(0.25, m, seed_add=seed)
    for k, y in enumerate(range(y0 + course - 1, y0 + h, course)):
        cv.line(x0, y, x0 + w - 1, y, ramp, tone - 2.2, flat=False)
        off = (k % 2) * 17
        for x in range(x0 + off, x0 + w, 34):
            cv.line(x, y - course + 1, x, y - 1, ramp, tone - 1.6, flat=False)
    return m


def snow_cap(cv: Canvas, x, y, w, seed=0, depth=3):
    rng = np.random.default_rng(cv.seed + 11 + seed)
    for i in range(w):
        d = max(1, int(depth - abs(i - w / 2) / (w / 2) * depth * 0.6 + rng.integers(-1, 2)))
        cv.rect(x + i, y - d, 1, d, 'snow', 3.6 + rng.random() * 0.4)


def crowd(cv: Canvas, y_feet, y_head, seed=0, tone=2.2, ramp='violet', step=11):
    """A dense row of winter coats and hats seen from the side/front, shaded as a mass."""
    rng = np.random.default_rng(cv.seed + 31 + seed)
    x = -4
    while x < W + 4:
        hh = int(y_head + rng.integers(-4, 5))
        w_ = int(rng.integers(9, 14))
        cv.poly([(x, y_feet), (x + 1, hh + 9), (x + w_ / 2, hh + 6), (x + w_, hh + 9), (x + w_ + 1, y_feet)],
                ramp, tone + rng.random() * 0.8)
        cv.ellipse(x + w_ / 2, hh + 3, 3.2, 3.6, 'stone', 2.6 + rng.random())
        if rng.random() < 0.7:   # hat or headscarf
            cv.rect(x + w_ / 2 - 4, hh - 1, 9, 3, ramp, tone - 0.6)
        x += step + int(rng.integers(-2, 3))


def finish(cv: Canvas, light=(0.5, -0.5), vig=1.2):
    cv.adjust(-0.8)   # evening: the plaza is lit by lamps and floodlights, not by day (matches hall_plaza)
    cv.linear(*light)
    cv.vignette(vig)


# =========================================================================== scenes
def s_tram_stop(cv: Canvas, hist=False):
    overcast(cv, 100)
    stone_wall(cv, 4.6, 12, 2, 0, 18, W, 82)
    for x in range(8, W, 26):
        cv.rect(x, 30, 10, 16, 'room', 2.6); cv.rect(x, 62, 10, 16, 'room', 2.4)
    cv.grad(0, 100, W, 50, 'snow', 2.6, 3.8)
    cv.noise(8, 0.3, cv.full((np.ones((50, W), bool), 0, 100)), seed_add=5)
    # pole with the stop disc and the closed route plate
    cv.bevel(cv.full(cv.rect(40, 26, 5, 124, 'steel', 3.0)), 1.0, 1.0)
    cv.ellipse(42, 24, 15, 15, 'green', 2.4)
    cv.ellipse(42, 24, 13, 13, 'amber', 4.4)
    for (x, y, w, h) in ((36, 17, 3, 15), (46, 17, 3, 15), (36, 23, 13, 3)):
        cv.rect(x, y, w, h, 'green', 2.0, flat=True)
    cv.rect(30, 42, 25, 12, 'paper', 6.4)
    cv.text(42, 45, '74', 'ink', 0, font='57', align='center')
    cv.rect(24, 55, 37, 8, 'red', 3.6)
    cv.text(43, 57, 'GESPERRT', 'paper', 7, align='center')
    snow_cap(cv, 28, 9, 29, 1)
    # timetable case: the old yellowed plan, a fresh notice pasted over it
    case = cv.full(cv.rect(84, 12, 122, 116, 'steel', 2.2))
    cv.bevel(case, 1.2, 1.0)
    cv.rect(88, 16, 114, 108, 'blue', 1.0)
    paper_sheet(cv, 91, 19, 108, 40, tone=4.6, seed=4, age=0.7)
    for i, y in enumerate(range(24, 56, 4)):
        typed_line(cv, 95, y, 100, 'ink', 1, cv.seed + i)
    note = paper_sheet(cv, 96, 46, 98, 76, tone=6.5, seed=6, age=0.25)
    cv.shadow(note, 1, 2, 1.0)
    rows = [('SONDERFAHRTEN', 50, 'red', 2), ('FÜR UMSIEDLER', 57, 'red', 2), ('PLANQUADRAT SÜD 7-12', 67, 'ink', 0),
            ('AB GÜTERBAHNHOF WEST', 74, 'ink', 0), ('VERLADERAMPE 3', 81, 'ink', 0),
            ('GEPÄCK HÖCHSTENS', 91, 'ink', 0), ('2 ZENTNER JE FAMILIE', 98, 'ink', 0)]
    for s, y, r, t in rows:
        cv.text(145, y, s, r, t, align='center')
    for i, y in enumerate((106, 110)):
        typed_line(cv, 102, y, 60, 'ink', 1, cv.seed + 20 + i, h=1)
    ring = cv.full(ellipse_mask(178, 110, 7, 7)) & ~cv.full(ellipse_mask(178, 110, 5.2, 5.2))
    cv.put(ring, 0, 0, 'red', 3, flat=True)
    cv.text(178, 108, 'G', 'red', 3, align='center')
    for (x, y) in ((97, 47), (191, 47)):
        tack(cv, x, y, 'brass')
    snow_cap(cv, 82, 12, 126, 2, 4)
    cv.spot(60, -20, 200, 0.8)
    finish(cv)
    snowfall(cv, 80)


def s_poster(cv: Canvas, hist=False):
    # the poster is pasted on the Litfass column (env prop 'litfass'): curved surface, older posters around it
    col = cv.full(cv.rect(0, 0, W, H, 'paper', 4.4))
    cv.noise(8, 0.5, col, seed_add=2)
    for (x0, w_, r, t, y0) in ((0, 50, 'blue', 2.8, 4), (8, 40, 'paper', 5.6, 96), (190, 50, 'sepia', 6.0, 0),
                               (196, 44, 'red', 2.2, 88)):
        old = cv.full(cv.rect(x0, y0, w_, 60, r, t))
        cv.grain(0.3, old, seed_add=x0)
        cv.put(edge(old), 0, 0, r, t - 1.2, flat=False)
    for i, y in enumerate(range(104, 140, 5)):
        typed_line(cv, 12, y, 32, 'ink', 1, cv.seed + 60 + i)
    cv.adjust(-np.abs((XX - 120) / 120.0) ** 2 * 3.2)
    px0, py0, pw, ph = 58, 6, 124, 140
    poster = paper_sheet(cv, px0, py0, pw, ph, tone=6.2, seed=2, age=0.3)
    cv.shadow(poster, 3, 3, 1.6)
    field = cv.full(cv.rect(px0 + 5, py0 + 5, pw - 10, 86, 'red', 2.4))
    cv.adjust(np.clip((YY - py0) * 0.02, 0, 1.4), field)
    cv.noise(9, 0.25, field, seed_add=4)
    cx, base = 120, py0 + 80
    cv.poly([(cx + math.cos(a) * 34, base - 6 - math.sin(a) * 28) for a in np.linspace(0, math.pi, 40)]
            + [(cx - 34, base - 6)], 'room', 1.2, flat=True)
    cv.rect(cx - 38, base - 6, 77, 10, 'room', 1.0, flat=True)
    for x in range(cx - 36, cx + 37, 5):
        cv.line(x, base - 5, x, base + 3, 'red', 2.0)
    cv.rect(cx - 3, base - 42, 7, 8, 'room', 1.2, flat=True)
    cv.rect(px0 + 5, base + 4, pw - 10, 2, 'room', 1.0, flat=True)
    ey = py0 + 13
    if hist:
        eg = eagle_mask(25, claws=True)
        cv.put(eg, cx - eg.shape[1] // 2, ey - 6, 'paper', 6.6, flat=True)
        wo = cv.full(ellipse_mask(cx, ey + 14.5, 5.6, 5.6))
        wi = cv.full(ellipse_mask(cx, ey + 14.5, 4.5, 4.5))
        cv.put(wo & ~wi, 0, 0, 'paper', 6.6, flat=True)
        cv.put(wi, 0, 0, 'paper', 7.4, flat=True)
        cv.put(hakenkreuz(7), cx - 3, ey + 11, 'ink', 0, flat=True)
    else:
        d_, p_ = reichssiegel(19)
        cv.put(d_, cx - 9, ey - 4, 'ink', 0, flat=True)
        cv.put(p_, cx - 9, ey - 4, 'paper', 6.6, flat=True)
        cv.put(edge(d_), cx - 9, ey - 4, 'paper', 5.0, flat=True)
    cv.text(cx, py0 + 96, 'EIN VOLK · EINE ORDNUNG', 'red', 2, align='center')
    cv.text(cx, py0 + 104, 'EIN PLATZ', 'red', 2, font='57', align='center')
    cv.line(px0 + 16, py0 + 114, px0 + pw - 16, py0 + 114, 'ink', 1)
    for i, s in enumerate(('10 UHR AUFSTELLUNG', '11 UHR VORBEIMARSCH', '17 UHR LICHTDOM')):
        cv.text(cx, py0 + 117 + i * 7, s, 'ink', 0, align='center')
    # the pencilled, rubbed-out house number in the corner
    cv.ellipse(px0 + pw - 13, py0 + ph - 12, 7, 6, 'paper', 5.5)
    rub = np.random.default_rng(cv.seed + 5).random((7, 5)) < 0.55
    cv.put(eb.text_mask('9', '57') & rub, px0 + pw - 16, py0 + ph - 16, 'graphite', 2.2, flat=True)
    for (tx, ty) in ((px0 + 2, py0 + 2), (px0 + pw - 4, py0 + 2), (px0 + 2, py0 + ph - 4)):
        tack(cv, tx, ty, 'brass')
    cv.poly([(px0 + pw - 12, py0 + ph), (px0 + pw, py0 + ph - 12), (px0 + pw, py0 + ph)], 'paper', 4.0)
    cv.adjust(-np.abs((XX - 120) / 120.0) ** 2 * 1.6, poster)
    finish(cv, (0.7, -0.6), 1.1)
    snowfall(cv, 40, 1)


def s_vendor(cv: Canvas, hist=False):
    overcast(cv, 70, 1.6, 2.8)
    crowd(cv, 96, 30, 0, 2.0)
    cv.grad(0, 90, W, 60, 'snow', 2.4, 3.6)
    # chalkboard
    cv.bevel(cv.full(cv.rect(128, 8, 104, 90, 'wood', 3.6)), 1.0, 1.0)
    board = cv.full(cv.rect(132, 12, 96, 82, 'room', 2.4))
    cv.noise(7, 0.4, board, seed_add=6)
    ch = ('paper', 6.6)
    cv.text(180, 17, 'MARONEN', *ch, font='57', align='center')
    cv.text(180, 27, '30 PF', *ch, font='57', align='center')
    cv.line(146, 37, 214, 37, 'paper', 5.2, dash=(3, 2))
    cv.text(180, 43, 'KINDER MIT', *ch, align='center')
    cv.text(180, 50, 'ROTER NASE', *ch, align='center')
    cv.text(180, 59, '20 PF', *ch, font='57', align='center')
    face = cv.full(ellipse_mask(180, 80, 8, 8))
    cv.put(edge(face), 0, 0, 'paper', 6.0, flat=True)
    cv.ellipse(180, 81, 1.8, 1.8, 'red', 4.6, flat=True)
    cv.px(177, 77, 'paper', 6.0); cv.px(183, 77, 'paper', 6.0)
    cv.line(177, 84, 183, 84, 'paper', 6.0)
    # roasting drum over the brazier
    cv.bevel(cv.full(cv.rect(18, 104, 82, 40, 'steel', 1.6)), 0.6, 0.8)
    for x in range(24, 96, 8):
        cv.rect(x, 110, 4, 6, 'glow', 2.2 + (x % 3) * 0.6, flat=True)
    drum = cv.full(cv.rect(22, 70, 74, 32, 'steel', 3.2))
    cv.adjust(-np.clip(np.abs(YY - 86) / 16.0, 0, 1) * 1.6, drum)
    for x in range(26, 96, 9):
        cv.line(x, 72, x, 100, 'steel', 1.6, flat=False)
    cv.ellipse(22, 86, 5, 16, 'steel', 2.0)
    cv.line(96, 86, 112, 86, 'steel', 4.0, flat=False); cv.rect(110, 80, 3, 12, 'wood', 4)
    cv.spot(58, 120, 70, 1.6)
    # paper cone from an old city map, full of chestnuts
    cone = cv.full(cv.poly([(112, 104), (152, 98), (136, 148)], 'paper', 5.8))
    for k, (p0, p1, r, t) in enumerate([((112 + k * 7, 96), (128 + k * 3, 150), 'blue', 3.0) for k in range(6)]
                                       + [((110, 116), (152, 108), 'graphite', 2), ((114, 128), (148, 122), 'red', 3)]):
        for (x, y) in eb.bres(*p0, *p1):   # old city map printed on the cone: streets clipped to the paper
            if 0 <= x < W and 0 <= y < H and cone[y, x]:
                cv.px(x, y, r, t)
    cv.bevel(cone, 0.6, 1.0)
    rng = np.random.default_rng(cv.seed + 9)
    for i in range(9):
        x, y = 118 + rng.integers(0, 30), 94 + rng.integers(-4, 8)
        nut = cv.full(cv.ellipse(x, y, 4.2, 3.4, 'wood', 3.2))
        cv.bevel(nut, 1.2, 0.8)
        cv.px(x - 1, y - 2, 'brass', 5)
    for i in range(14):   # steam
        cv.px(126 + rng.integers(0, 18), 70 + rng.integers(0, 22), 'snow', 3 + rng.random(), flat=False)
    finish(cv, (0.4, -0.3), 1.2)
    snowfall(cv, 50, 2)


def s_loudspeaker(cv: Canvas, hist=False):
    overcast(cv, H, 2.8, 1.2)
    stone_wall(cv, 3.0, 12, 4, 196, 0, 44, H)
    cv.rect(190, 0, 6, H, 'sepia', 1.6)
    cv.grad(206, 0, 22, H, 'steel', 3.4, 2.2)
    for x in (210, 216, 222):
        cv.line(x, 0, x, H - 1, 'steel', 1.8, flat=False)
    cv.bevel(cv.full(cv.rect(106, 50, 7, 100, 'steel', 2.0)), 0.8, 0.8)
    cv.bevel(cv.full(cv.rect(60, 46, 100, 5, 'steel', 2.2)), 0.8, 0.8)
    for side in (-1, 1):   # two horns in profile, pointing outwards
        x0 = 109 + side * 6
        mouth = 109 + side * 48
        horn = cv.full(cv.poly([(x0, 36), (mouth, 22), (mouth, 58), (x0, 44)], 'steel', 3.4))
        cv.adjust(-np.clip((YY - 30) / 26.0, 0, 1) * 1.6, horn)
        cv.bevel(horn, 1.0, 0.6)
        cv.ellipse(mouth, 40, 4, 18, 'steel', 4.6)
        cv.ellipse(mouth + side, 40, 2.4, 15, 'room', 1.4)
        snow_cap(cv, min(x0, mouth) + 4, 30 if side < 0 else 30, 40, 5 + side, 3)
    face = cv.full(ellipse_mask(109, 82, 22, 22))
    cv.put(face, 0, 0, 'steel', 3.8)
    cv.bevel(face, 1.2, 1.0)
    for r, t in ((18, 2.6), (13, 1.8), (8, 1.0), (4, 0.4)):
        cv.ellipse(109, 82, r, r, 'steel', t)
    snow_cap(cv, 92, 61, 34, 7, 4)
    for k in range(3):   # cables sagging away to the next mast
        cv.polyline([(160, 48 + k * 2)] + [(160 + i * 8, 48 + k * 2 + math.sin(i / 10 * math.pi) * 12) for i in range(1, 11)],
                    'ink', 1)
    for (x, y) in ((40, 20), (52, 14), (70, 26)):   # crows
        cv.line(x - 3, y - 1, x, y + 1, 'ink', 0); cv.line(x, y + 1, x + 3, y - 1, 'ink', 0)
    finish(cv, (0.3, -0.5), 1.0)
    snowfall(cv, 90, 3)


def s_barrier(cv: Canvas, hist=False):
    overcast(cv, 50, 1.6, 2.6)
    stone_wall(cv, 4.0, 12, 5, 0, 0, W, 34)
    crowd(cv, 112, 36, 1, 2.0, step=12)
    crowd(cv, 118, 52, 2, 3.0, 'violet', 14)
    cv.grad(0, 112, W, 38, 'snow', 2.8, 3.8)
    for lx in (34, 206):   # trestle legs
        cv.poly([(lx - 14, 150), (lx - 10, 150), (lx + 2, 86), (lx - 2, 86)], 'wood', 2.6)
        cv.poly([(lx + 10, 150), (lx + 14, 150), (lx + 2, 86), (lx - 2, 86)], 'wood', 3.4)
    for i, x in enumerate(range(10, 232, 16)):
        cv.bevel(cv.full(cv.rect(x, 80, 16, 10, 'red' if i % 2 == 0 else 'paper', 3.4 if i % 2 == 0 else 6.4)), 0.8, 0.8)
    snow_cap(cv, 10, 80, 222, 3, 3)
    for i in range(10):   # chain to the next trestle
        cv.ellipse(232 + i * 3, 92 + math.sin(i / 9 * math.pi) * 6, 1.6, 1.2, 'steel', 4)
    cv.line(118, 90, 118, 96, 'steel', 3); cv.line(162, 90, 162, 96, 'steel', 3)
    sign = paper_sheet(cv, 84, 96, 112, 30, tone=6.4, seed=3, age=0.3)
    cv.shadow(sign, 1, 2, 1.0)
    cv.text(140, 100, 'NEUORDNUNGSBEZIRK', 'red', 2, align='center')
    cv.text(140, 108, 'AUFSTELLUNG NACH', 'ink', 0, align='center')
    cv.text(140, 115, 'HAUSNUMMERN', 'ink', 0, align='center')
    finish(cv, (0.4, -0.4), 1.2)
    snowfall(cv, 70, 4)


def s_tank(cv: Canvas, hist=False):
    overcast(cv, 40, 1.4, 2.2)
    stone_wall(cv, 7.0, 14, 6, 0, 0, W, 22)
    hull = cv.full(cv.poly([(0, 18), (W, 14), (W, 74), (0, 78)], 'patina', 2.6))
    cv.noise(16, 0.25, hull, seed_add=8)
    cv.bevel(hull, 1.0, 0.6)
    cv.line(0, 40, W, 37, 'patina', 1.4, flat=False)
    for x in range(14, W, 46):
        cv.ellipse(x, 30, 2, 2, 'patina', 3.8)
    cv.text(150, 46, '214', 'paper', 6.6, font='57', scale=2, align='center')
    snow_cap(cv, 0, 18, 120, 4, 4); snow_cap(cv, 120, 16, 120, 5, 4)
    track = cv.full(cv.rect(0, 70, W, 50, 'steel', 1.4))
    for x in range(-2, W, 6):
        cv.line(x, 70, x + 2, 120, 'steel', 2.6, flat=False)
    for x in range(-2, W, 12):
        cv.rect(x, 66, 4, 4, 'steel', 3.0)
    for cx in range(22, W, 46):
        cv.ellipse(cx, 96, 17, 17, 'ink', 1)
        rim = cv.full(ellipse_mask(cx, 96, 15, 15))
        cv.put(rim, 0, 0, 'steel', 3.2); cv.bevel(rim, 1.2, 1.0)
        cv.ellipse(cx, 96, 7, 7, 'steel', 4.2); cv.ellipse(cx, 96, 3, 3, 'steel', 2.0)
    cv.adjust(-0.8, track)
    cv.grad(0, 120, W, 30, 'sepia', 6.0, 7.6)
    for x in range(0, W, 13):
        cv.line(x + (x // 13 % 2) * 6, 120, x + (x // 13 % 2) * 6, H - 1, 'sepia', 4.2, flat=False)
    cv.line(0, 134, W - 1, 134, 'sepia', 4.2, flat=False)
    rng = np.random.default_rng(cv.seed + 4)
    for i in range(160):   # snow torn up by the tracks
        x, y = int(rng.integers(0, W)), int(120 + rng.integers(0, 30) * rng.random())
        cv.rect(x, y, int(rng.integers(1, 4)), 1, 'snow', 2.6 + rng.random() * 1.4)
    for i in range(40):
        x, y = int(rng.integers(0, W)), int(rng.integers(60, 120))
        cv.line(x, y, x + int(rng.integers(3, 9)), y, 'snow', 3.4, flat=False)
    for (x0, y0, x1, y1) in ((40, 150, 42, 98), (92, 150, 89, 100), (41, 100, 66, 104), (66, 104, 90, 99)):
        cv.line(x0, y0, x1, y1, 'steel', 4.6)   # the bent carpet-beating bar of the former courtyard
    barrel = cv.full(cv.rect(206, 104, 26, 46, 'steel', 2.0))
    cv.bevel(barrel, 0.8, 0.8)
    cv.line(206, 116, 231, 116, 'steel', 1.0); cv.line(206, 132, 231, 132, 'steel', 1.0)
    cv.ellipse(219, 104, 13, 3, 'glow', 2.6)
    cv.spot(219, 100, 70, 1.6)
    finish(cv, (0.4, -0.4), 1.1)
    snowfall(cv, 50, 5)


def s_tribune(cv: Canvas, hist=False):
    overcast(cv, 90, 1.6, 3.0)
    cv.poly([(150 + math.cos(a) * 80, 70 - math.sin(a) * 62) for a in np.linspace(0, math.pi, 50)], 'violet', 6.2)
    cv.rect(66, 66, 168, 10, 'violet', 5.6)
    cv.rect(176, 0, 6, 10, 'violet', 5.8)
    steps = cv.full(cv.poly([(20, 112), (40, 52), (200, 52), (220, 112)], 'sepia', 9.0))
    for k, y in enumerate(range(58, 112, 5)):
        cv.line(40 - k * 2, y, 200 + k * 2, y, 'sepia', 6.8, flat=False)
    cv.bevel(steps, 1.0, 1.0)
    for x in range(46, 196, 20):   # red drapes with gold fringe
        cv.grad(x, 54, 14, 38, 'steel', 3.8, 2.4)
        cv.line(x, 92, x + 13, 92, 'brass', 4, dash=(1, 1))
    rng = np.random.default_rng(cv.seed + 2)
    for i, x in enumerate(range(52, 192, 12)):   # the guests: coats, fur collars, caps
        hy = 30 + int(rng.integers(-2, 3))
        cv.poly([(x - 5, 52), (x - 4, hy + 8), (x + 4, hy + 8), (x + 5, 52)], 'room', 1.2 + rng.random() * 0.6)
        cv.rect(x - 4, hy + 6, 9, 3, 'wood', 2.4)
        cv.ellipse(x, hy + 3, 2.6, 3.0, 'stone', 3.0)
        cv.rect(x - 3, hy - 1, 7, 2, 'room', 0.6)
    cv.grad(0, 112, W, 38, 'snow', 2.6, 3.4)
    for i in range(18):   # the chain of the barrier and the heads in front of it
        cv.ellipse(6 + i * 13, 126 + (i % 2), 1.6, 1.2, 'steel', 3)
    crowd(cv, 160, 126, 3, 1.2, 'violet', 16)
    finish(cv, (0.2, -0.3), 1.2)
    snowfall(cv, 60, 6)


def s_banner(cv: Canvas, hist=False):
    stone_wall(cv, 8.4, 18, 7)
    cv.adjust(-np.clip(YY / 150.0, 0, 1) * 1.8)
    for (x, y) in ((96, 22), (96, 90), (204, 22), (204, 90)):
        fr = cv.full(cv.rect(x, y, 26, 40, 'sepia', 4.0))
        cv.rect(x + 3, y + 3, 20, 34, 'room', 1.4)
        cv.line(x + 13, y + 3, x + 13, y + 36, 'sepia', 4.0)
    cv.poly([(99, 25), (110, 25), (106, 50), (103, 62), (99, 62)], 'paper', 5.4)   # gathered curtain
    cv.line(104, 26, 102, 60, 'paper', 4.2)
    for bx in (30, 140):
        cv.rect(bx + 2, 2, 3, 4, 'brass', 4); cv.rect(bx + 37, 2, 3, 4, 'brass', 4)
        # neutral world: slate state banners (as env prop banner_near); _hist: the real red flag
        ban = cv.full(cv.rect(bx, 5, 42, H - 5, 'red' if hist else 'steel', 3.6 if hist else 3.4))
        cv.adjust(np.sin((XX - bx) / 42 * math.pi * 3) * 0.7, ban)
        cv.adjust(np.clip((YY - 5) / 150.0, 0, 1) * -0.8, ban)
        cv.ellipse(bx + 21, 46, 14, 14, 'paper', 6.6)
        if hist:
            cv.put(hakenkreuz(17), bx + 13, 38, 'ink', 0, flat=True)
        else:
            d_, p_ = reichssiegel(19)
            cv.put(d_, bx + 12, 37, 'ink', 0, flat=True)
            cv.put(p_, bx + 12, 37, 'paper', 6.6, flat=True)
    finish(cv, (0.6, -0.4), 1.1)
    snowfall(cv, 60, 7)


def s_window(cv: Canvas, hist=False):
    stone_wall(cv, 5.0, 14, 8)
    cv.adjust(-0.8)
    frame = cv.full(cv.rect(64, 10, 112, 112, 'sepia', 8.4))
    cv.bevel(frame, 1.0, 1.4)
    glass = cv.full(cv.rect(72, 16, 96, 100, 'glow', 2.2))
    cv.adjust(cv.field_radial(120, 52, 70, 1.8), glass)
    cv.poly([(100, 116), (104, 62), (112, 50), (128, 50), (136, 62), (140, 116)], 'dusk', 6.2)   # the woman
    cv.ellipse(120, 40, 7, 8.5, 'dusk', 6.6)
    cv.rect(116, 47, 8, 4, 'dusk', 6.4)
    cv.poly([(72, 16), (102, 16), (96, 70), (98, 116), (72, 116)], 'paper', 5.6)   # drawn curtain
    cv.poly([(124, 16), (168, 16), (168, 116), (128, 116), (132, 70)], 'paper', 5.0)   # being drawn
    for x in (78, 86, 94, 136, 146, 156):
        cv.line(x, 18, x - 2, 114, 'paper', 4.0, flat=False)
    cv.rect(72, 14, 96, 3, 'brass', 3)
    cv.line(120, 16, 120, 116, 'sepia', 7.0, flat=False)
    sill = cv.full(cv.rect(56, 120, 128, 9, 'sepia', 7.4))
    cv.bevel(sill, 1.2, 1.4)
    snow_cap(cv, 56, 120, 30, 2, 3); snow_cap(cv, 150, 120, 34, 3, 3)
    cv.ellipse(120, 119, 15, 2.4, 'paper', 5.0)   # plate under a cloth
    cloth = cv.full(cv.poly([(108, 119), (110, 109), (120, 105), (130, 109), (132, 119)], 'paper', 6.4))
    cv.bevel(cloth, 0.8, 1.0)
    cv.line(112, 116, 128, 116, 'blue', 3.4, dash=(2, 1))
    cv.grad(0, 129, W, 21, 'sepia', 3.0, 2.0)
    finish(cv, (0.2, -0.2), 1.6)
    snowfall(cv, 70, 8)


def s_rubble(cv: Canvas, hist=False):
    overcast(cv, 40, 1.8, 2.8)
    rng = np.random.default_rng(cv.seed + 1)
    fw = cv.full(cv.rect(0, 6, W, 70, 'sepia', 6.4))   # the remaining fire wall: ghost of floors, stairs, rooms
    cv.noise(9, 0.4, fw, seed_add=12)
    for (x, y, w, h, r, t) in ((8, 10, 60, 22, 'blue', 3.4), (76, 10, 70, 22, 'paper', 5.0), (158, 10, 74, 22, 'green', 3.6),
                               (8, 38, 70, 24, 'stone', 4.2), (150, 38, 82, 24, 'blue', 2.8)):
        room = cv.full(cv.rect(x, y, w, h, r, t))
        cv.grain(0.4, room, seed_add=x)
    for y in (34, 64):
        cv.rect(0, y, W, 3, 'sepia', 3.6)
    cv.polyline([(84 + i * 6 + (k % 2) * 6, 64 - i * 5 - (k % 2) * 0) for i in range(7) for k in range(2)], 'sepia', 3.2, width=2)
    cv.poly([(0, 150), (0, 76), (60, 60), (130, 68), (200, 56), (240, 72), (240, 150)], 'stone', 1.6)
    for i in range(260):   # bricks and stones
        x, y = int(rng.integers(-6, W)), int(rng.integers(58, H))
        r = 'red' if rng.random() < 0.6 else 'stone'
        b = cv.full(cv.rect(x, y, int(rng.integers(6, 12)), int(rng.integers(3, 6)), r, 1.6 + rng.random() * 2.2))
        cv.bevel(b, 0.8, 0.8)
    paper = cv.full(cv.poly([(14, 70), (78, 58), (90, 104), (60, 116), (22, 108)], 'paper', 5.4))
    cv.grain(0.3, paper, seed_add=3)
    for k in range(14):   # blue roses on the wallpaper
        x, y = 22 + (k % 5) * 14 + (k // 5) * 5, 70 + (k // 5) * 14
        if paper[min(H - 1, y), min(W - 1, x)]:
            cv.ellipse(x, y, 2.6, 2.2, 'blue', 3.0); cv.px(x, y, 'blue', 5); cv.px(x + 3, y + 2, 'green', 3)
    cv.put(edge(paper), 0, 0, 'paper', 3.6, flat=False)
    tile = cv.full(cv.rect(160, 52, 32, 28, 'green', 3.2))
    cv.bevel(tile, 1.6, 1.2)
    cv.rect(166, 58, 20, 16, 'green', 4.0)
    cv.bevel(cv.full(cv.rect(200, 92, 22, 30, 'brass', 3.0)), 1.2, 1.0)   # doorbell plate, no name
    cv.ellipse(211, 101, 3, 3, 'brass', 5); cv.rect(204, 110, 14, 6, 'paper', 5.2)
    badge = cv.full(cv.rect(104, 98, 42, 26, 'blue', 2.6))
    cv.shadow(badge, 2, 2, 1.2)
    cv.put(edge(cv.full((np.ones((22, 38), bool), 106, 100))), 0, 0, 'paper', 6.8, flat=True)
    cv.text(125, 107, 'OST', 'paper', 6.8, font='57', align='center')
    for (x, y) in ((104, 97), (146, 110), (120, 124)):   # frayed threads
        cv.px(x, y, 'blue', 3); cv.px(x + 1, y - 1, 'blue', 4)
    for i in range(180):   # snow dusting on upper faces
        x, y = int(rng.integers(0, W)), int(rng.integers(58, H))
        cv.rect(x, y, int(rng.integers(1, 5)), 1, 'snow', 3.0 + rng.random())
    finish(cv, (0.5, -0.4), 1.2)
    snowfall(cv, 50, 9)


def s_family_door(cv: Canvas, hist=False):
    stone_wall(cv, 5.6, 14, 9)
    cv.poly([(62, 150), (62, 30), (105, 8), (148, 30), (148, 150)], 'sepia', 3.0)
    eb.wood_planks(cv, 68, 30, 74, 120, tone=3.6, plank=9, seed=4, vertical=True)
    cv.poly([(68, 30), (105, 12), (142, 30)], 'wood', 2.4)
    for y in (60, 104):
        cv.bevel(cv.full(cv.rect(74, y, 62, 30, 'wood', 3.8)), 1.0, 1.0)
    cv.rect(128, 92, 6, 14, 'brass', 3.4); cv.ellipse(131, 96, 2, 2, 'brass', 5)
    for (a, b) in (((70, 44), (140, 128)), ((140, 44), (70, 128))):   # two laths nailed across the door
        lath = cv.polyline([a, b], 'wood', 5.0, flat=False, width=3)
        cv.bevel(lath, 1.0, 1.2)
        for q in (a, b):
            cv.px(q[0] + (2 if q[0] < 100 else -2), q[1] + 2, 'steel', 5)
    strip = cv.full(cv.rect(110, 86, 36, 8, 'paper', 6.6))
    cv.shadow(strip, 1, 1, 1.0)
    ring = cv.full(ellipse_mask(128, 90, 6, 6)) & ~cv.full(ellipse_mask(128, 90, 4.4, 4.4))
    cv.put(ring, 0, 0, 'red', 3, flat=True)
    cv.px(128, 90, 'red', 3); cv.line(126, 89, 130, 89, 'red', 3)
    cv.bevel(cv.full(cv.rect(150, 18, 22, 22, 'blue', 2.6)), 1.0, 1.0)
    cv.text(161, 22, '9', 'paper', 7, font='57', scale=2, align='center')
    note = paper_sheet(cv, 158, 48, 70, 88, tone=6.4, seed=5, age=0.35)
    cv.shadow(note, 2, 2, 1.2)
    cv.text(193, 53, 'RÄUMUNGS-', 'ink', 0, align='center')
    cv.text(193, 60, 'VERFÜGUNG', 'ink', 0, align='center')
    cv.text(193, 70, 'AUSZUG BIS 14.', 'ink', 0, align='center')
    for i, y in enumerate(range(80, 116, 4)):
        typed_line(cv, 163, y, 58, 'ink', 1, cv.seed + 40 + i, h=1)
    scribble(cv, 166, 124, 28, 'ink', 1, cv.seed + 3)
    ring2 = cv.full(ellipse_mask(212, 124, 7, 7)) & ~cv.full(ellipse_mask(212, 124, 5.2, 5.2))
    cv.put(ring2, 0, 0, 'blue', 2, flat=True)
    if hist:   # the office stamp: eagle (historical) / fictional Reichssiegel pillar (neutral)
        eg = eagle_mask(9)
        cv.put(eg, 212 - eg.shape[1] // 2, 124 - eg.shape[0] // 2, 'blue', 2, flat=True)
    else:
        cv.put(reichssiegel(9)[1], 208, 120, 'blue', 2, flat=True)
    for (x, y) in ((159, 49), (226, 49)):
        tack(cv, x, y, 'brass')
    cv.grad(0, 140, W, 10, 'snow', 2.6, 3.6)
    finish(cv, (0.6, -0.4), 1.3)
    snowfall(cv, 60, 10)


SCENES = {
    'tram_stop': (s_tram_stop, False),
    'poster': (s_poster, True),
    'vendor': (s_vendor, False),
    'loudspeaker': (s_loudspeaker, False),
    'barrier': (s_barrier, False),
    'tank': (s_tank, False),
    'tribune': (s_tribune, False),
    'banner': (s_banner, True),
    'rubble': (s_rubble, False),
    'family_door': (s_family_door, True),
    'window': (s_window, False),
}


def render(name: str, hist: bool = False) -> np.ndarray:
    cv = Canvas('plaza.' + name)
    SCENES[name][0](cv, hist)
    return cv.render()


def main(argv: list[str]) -> int:
    preview, only, i = None, [], 0
    while i < len(argv):
        if argv[i] == '--preview' and i + 1 < len(argv):
            preview = argv[i + 1]; i += 2; continue
        only.append(argv[i]); i += 1
    os.makedirs(OUT, exist_ok=True)
    shots = []
    for name, (fn, has_hist) in SCENES.items():
        if only and name not in only:
            continue
        for hist, fname in [(False, name)] + ([(True, name + '_hist')] if has_hist else []):
            arr = render(name, hist)
            bad = eb.palette_problems(arr)
            if bad:
                print('PALETTE', fname, bad[:6])
            Image.fromarray(arr, 'RGBA').save(os.path.join(OUT, fname + '.png'))
            shots.append((fname, arr))
            print('wrote', fname, arr.shape[1], 'x', arr.shape[0])
    if preview:
        os.makedirs(preview, exist_ok=True)
        cols = 3
        rows = (len(shots) + cols - 1) // cols
        sheet = Image.new('RGBA', (cols * (W + 6), rows * (H + 6)), (10, 10, 12, 255))
        for k, (fname, arr) in enumerate(shots):
            sheet.paste(Image.fromarray(arr, 'RGBA'), ((k % cols) * (W + 6), (k // cols) * (H + 6)))
        sheet.save(os.path.join(preview, 'contact_sheet.png'))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
