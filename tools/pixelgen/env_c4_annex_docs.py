"""env_c4_annex_docs -- inspect-UI document art of L_C4_Annex (drawn 1:1, shown at 3x by InspectView).

Six evidence items of C4_DESIGN 2.5 (scenes L_C4_AnnexA / L_C4_AnnexB):
    berlin_annex_notice.png     ev_c4_notice     Raeumungsbescheid Nr. 9, the fresh addendum, the attached
                                                 Lageplan Sued 8 with the three shafts (same grid as the route
                                                 puzzle's plan, berlin_c4_routes.json), title block 'gez. K. A.'
    berlin_annex_shaft.png      ev_c4_shaft      the steel door behind the posters of S 2 and its enamel plate
    berlin_annex_card_de.png    ev_c4_card_de    card No. 0417, the German half, perforated edge, red C-17 tab
    berlin_annex_drawer.png     ev_c4_drawer_s8  drawer Sued 8 seen from above: 212 cards, 37 red tabs
    berlin_annex_plan.png       ev_c4_annex_plan Lueftungsplan Nebenstelle Sued, 1961, Blatt 3, gez. K. Adler
    berlin_annex_tube_slip.png  ev_c4_tube_slip  the pneumatic-tube slip of the Staatspolizeistelle
    berlin_annex_route_board.png ev_c4_route_board Marta's route board: line 74 and the detours Okt./Dez./Jan. on
                                                 tracing paper, drawn in driving direction (round-9 fix compl-04)
The story-critical words are legible pixel capitals (3x5 font); the rest is print / handwriting scribble under the
UI's HD caption (item name + description).  Writes berlin_annex_documents.json (schema of the other
*_documents.json: id, file, size, display_scale, item_id, objective, hotspot, marks, alt_key -- the German caption
line under the document, written by hand in data/locale/de_env_berlin_annex.json).  Deterministic, palette
'annex' (+ lamp) only, no insignia (the documents carry no emblem, so no _hist pair is needed).
"""
from __future__ import annotations

import json
import math
import os
import sys

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import env_c4_annex_kit as K  # noqa: E402
import pg  # noqa: E402

ROOT = K.ROOT
DOC_DIR = os.path.join(ROOT, 'assets', 'ui', 'documents')
GEN = 'tools/pixelgen/env_c4_annex_docs.py'
A = K.ANNEX
C = {
    'cream': [A['paper'][2], A['paper'][3], A['paper'][4]],
    'white': [A['snow'][1], A['snow'][2], A['snow'][3], A['snow'][4]],
    'ink': A['night'][2], 'ink2': A['steel'][1], 'grey': A['steel'][3], 'blue': A['dawn'][1], 'blue2': A['dawn'][0],
    'red': A['red'][2], 'red2': A['red'][3], 'shadow': A['paper'][1], 'edge': A['paper'][0], 'steel': A['steel'],
    'lamp': A['lamp'], 'pencil': A['concrete'][2],
}


def hx(h):
    return np.array(pg.hx(h), np.uint8)


class Doc:
    def __init__(self, w, h):
        self.w, self.h = w, h
        self.a = np.zeros((h, w, 4), np.uint8)
        self.marks: dict = {}

    def px(self, x, y, col):
        if 0 <= x < self.w and 0 <= y < self.h:
            self.a[y, x] = hx(col)

    def rect(self, x, y, w, h, col):
        for yy in range(max(0, y), min(self.h, y + h)):
            for xx in range(max(0, x), min(self.w, x + w)):
                self.a[yy, xx] = hx(col)

    def line(self, x0, y0, x1, y1, col):
        for (x, y) in K.bres(int(x0), int(y0), int(x1), int(y1)):
            self.px(x, y, col)

    def paper(self, x, y, w, h, ramp, seed=0, age=0.5, corner=True):
        """A sheet: ordered-dither stains, a darker rim, a dog-eared corner."""
        nz = pg.value_noise(w, h, 9, seed, octaves=3)
        thr = pg.bayer(w, h, seed, 0, 4)
        n = len(ramp)
        for yy in range(h):
            for xx in range(w):
                rim = min(xx, yy, w - 1 - xx, h - 1 - yy)
                t = (n - 1) - (nz[yy, xx] - 0.35) * age * 3 - (1.2 if rim < 2 else 0) * age
                idx = int(np.clip(math.floor(t) + (t - math.floor(t) > thr[yy, xx]), 0, n - 1))
                self.px(x + xx, y + yy, ramp[idx])
        if corner:
            for k in range(7):
                for j in range(7 - k):
                    self.px(x + w - 1 - j, y + k, C['shadow'] if j < 2 else ramp[max(0, n - 2)])
        for xx in range(w):
            self.px(x + xx + 2, y + h, C['edge'])
        for yy in range(h):
            self.px(x + w, y + yy + 2, C['edge'])

    def text(self, s, x, y, col, scale=1, mark=None, wear=0.0, seed=0, center=False):
        m = K.text_mask(s, '35', 1)
        if center:
            x = int(round(x - m.shape[1] * scale / 2))
        rng = np.random.default_rng(seed)
        for yy in range(m.shape[0]):
            for xx in range(m.shape[1]):
                if m[yy, xx] and rng.random() >= wear:
                    for dy in range(scale):
                        for dx in range(scale):
                            self.px(x + xx * scale + dx, y + yy * scale + dy, col)
        if mark:
            self.marks[mark] = {'rect': [int(x), int(y), int(m.shape[1] * scale), int(m.shape[0] * scale)], 'text': s}
        return x + m.shape[1] * scale

    def print_lines(self, x, y, w, rows, col, seed=0, gap=6, rag=0.3):
        """Typed / printed pseudo text: word blocks of 3-5 px high scribble glyphs (never real words)."""
        rng = np.random.default_rng(seed)
        for r in range(rows):
            xx = x
            end = x + w - int(rng.random() * w * rag)
            while xx < end - 3:
                wl = int(rng.integers(3, 9)) * 4
                for k in range(0, min(wl, end - xx), 4):
                    g = int(rng.integers(0, 6))
                    for dy in range(5):
                        if (g + dy) % 3 != 0 or dy in (0, 4):
                            if rng.random() < 0.7:
                                self.px(xx + k + (dy + g) % 3, y + r * gap + dy, col)
                xx += wl + 4
        return y + rows * gap

    def hand(self, x, y, w, col, seed=0, xh=3, slant=1):
        """Cursive handwriting scribble on a baseline."""
        rng = np.random.default_rng(seed)
        base = y + 6
        cx = x
        while cx < x + w - 4:
            n = int(rng.integers(2, 6))
            pts = [(cx, base)]
            for _ in range(n):
                wd = int(rng.integers(2, 4))
                if rng.random() < 0.2:
                    pts += [(cx + 1 + slant, base - xh - 3), (cx + 1, base), (cx + wd, base - xh + 1)]
                else:
                    pts += [(cx + 1 + slant, base - xh), (cx + wd, base)]
                cx += wd + 1
            for a, b in zip(pts[:-1], pts[1:]):
                self.line(a[0], a[1], b[0], b[1], col)
            cx += int(rng.integers(3, 6))

    def stamp(self, cx, cy, r, col, words=('NEBENSTELLE', 'SÜD')):
        for a in range(0, 360, 3):
            t = math.radians(a)
            for rr in (r, r - 1):
                if (a // 3) % 7 != 0:
                    self.px(int(round(cx + rr * math.cos(t))), int(round(cy + rr * math.sin(t))), col)
        self.text(words[0], cx, cy - 6, col, center=True, wear=0.25, seed=r)
        if len(words) > 1:
            self.text(words[1], cx, cy + 1, col, center=True, wear=0.25, seed=r + 1)

    def save(self, name):
        path = os.path.join(DOC_DIR, name + '.png')
        Image.fromarray(self.a, 'RGBA').save(path)
        return path


# =========================================================================== the documents
def lageplan(d: Doc, x, y, cell=7, title=True):
    """Lageplan Sued 8 on the grid of the route puzzle (14 x 10 cells, streets at columns 4/7/10 and rows
    0/3/6/9, line 74 along column 7, shafts S1 (9,1), S2 (5,5), S3 (8,8))."""
    w, h = 14 * cell, 10 * cell
    d.rect(x, y, w, h, C['white'][3])
    for c in (4, 7, 10):
        d.rect(x + c * cell, y, cell, h, C['white'][2])
    for r in (0, 3, 6, 9):
        d.rect(x, y + r * cell, w, cell, C['white'][2])
    for bx0, bx1 in ((0, 4), (5, 7), (8, 10), (11, 14)):
        for by0, by1 in ((1, 3), (4, 6), (7, 9)):
            X0, Y0, X1, Y1 = x + bx0 * cell + 1, y + by0 * cell + 1, x + bx1 * cell - 1, y + by1 * cell - 1
            for xx in range(X0, X1):
                d.px(xx, Y0, C['blue'])
                d.px(xx, Y1 - 1, C['blue'])
            for yy in range(Y0, Y1):
                d.px(X0, yy, C['blue'])
                d.px(X1 - 1, yy, C['blue'])
            for k in range(X0 + 1, X1 - 1):
                for yy in range(Y0 + 1, Y1 - 1):
                    if (k + yy) % 4 == 0:
                        d.px(k, yy, C['white'][1])
    for yy in range(y, y + h, 3):
        d.px(x + 7 * cell + cell // 2, yy, C['blue2'])
    for i, (cxc, cyc) in enumerate(((9, 1), (5, 5), (8, 8))):
        cx, cy = x + cxc * cell + cell // 2, y + cyc * cell + cell // 2
        for a in range(0, 360, 20):
            t = math.radians(a)
            d.px(int(round(cx + 3 * math.cos(t))), int(round(cy + 3 * math.sin(t))), C['ink'])
        d.px(cx, cy, C['ink'])
        d.text('S%d' % (i + 1), cx + 5, cy - 2, C['ink'], mark='shaft_%d' % (i + 1))
    for k in range(w):
        d.px(x + k, y, C['ink2'])
        d.px(x + k, y + h - 1, C['ink2'])
    for k in range(h):
        d.px(x, y + k, C['ink2'])
        d.px(x + w - 1, y + k, C['ink2'])
    if title:
        d.text('LAGEPLAN SÜD 8', x + 2, y + h + 3, C['ink'], mark='lageplan')
        d.text('GEZ. K. A.', x + w - 38, y + h + 3, C['ink'], mark='sign_ka')


def notice():
    d = Doc(320, 210)
    d.paper(8, 6, 178, 196, C['white'], seed=91, age=0.7)
    d.text('BESCHEID', 97, 14, C['ink'], scale=2, center=True, mark='title')
    d.text('RÄUMUNG HAUS NR. 9', 97, 30, C['ink'], center=True, mark='house')
    d.print_lines(18, 42, 160, 6, C['ink2'], seed=1)
    d.text('BAUMASSNAHMEN ACHSE SÜD', 18, 82, C['ink'], mark='reason')
    d.print_lines(18, 92, 160, 4, C['ink2'], seed=2)
    d.stamp(128, 132, 17, C['red'], words=('BEZIRKS', 'AMT'))
    # the fresh addendum by another hand, legible in its key words
    d.hand(18, 152, 90, C['blue2'], seed=7)
    d.text('HAUSHALT AUFGELÖST.', 18, 166, C['blue2'], mark='addendum_1')
    d.text('VORGANG AN NEBENSTELLE SÜD', 18, 175, C['blue2'], mark='addendum_2')
    d.line(18, 184, 130, 184, C['blue2'])
    # the attached site plan, pinned over the corner
    d.paper(170, 48, 112, 100, C['white'][1:], seed=93, age=0.4, corner=False)
    lageplan(d, 177, 54, cell=7)
    for (px_, py_) in ((172, 50), (278, 50)):
        d.rect(px_, py_, 3, 3, C['grey'])
        d.px(px_ + 1, py_ + 1, C['white'][3])
    return d


def shaft():
    d = Doc(260, 170)
    # the drum of the column: torn posters around a steel door with its enamel plate
    for yy in range(170):
        for xx in range(260):
            c = (xx + 0.5) / 260 * 2 - 1
            t = 3.6 - 2.2 * abs(c + 0.2) ** 1.5
            d.px(xx, yy, C['steel'][int(np.clip(round(t), 0, 4))])
    rng = np.random.default_rng(22)
    for (x0, y0, w, h, col) in ((0, 0, 70, 90, A['red'][2]), (190, 10, 70, 80, A['paper'][3]), (0, 100, 60, 70, A['dawn'][2]),
                                (200, 100, 60, 70, A['paper'][4])):
        for yy in range(y0, y0 + h):
            for xx in range(x0, x0 + w):
                edge = (xx in (x0 + w - 1,) or yy in (y0 + h - 1,)) and rng.random() < 0.5
                if not edge:
                    d.px(xx, yy, col)
    d.rect(64, 14, 132, 150, A['steel'][2])
    d.rect(68, 18, 124, 142, A['steel'][3])
    for yy in range(22, 156, 10):
        d.px(72, yy, A['steel'][4])
        d.px(187, yy, A['steel'][4])
    d.rect(80, 34, 100, 46, C['white'][3])
    d.rect(80, 34, 100, 2, C['blue'])
    d.rect(80, 78, 100, 2, C['blue'])
    d.text('LÜFTUNGSBAUWERK', 130, 40, C['blue2'], center=True, mark='plate_1')
    d.text('S 2', 130, 49, C['blue2'], scale=2, center=True, mark='plate_s2')
    d.text('ZUTRITT NUR FÜR', 130, 63, C['ink'], center=True, mark='plate_2')
    d.text('BEDIENSTETE', 130, 70, C['ink'], center=True, mark='plate_3')
    d.rect(168, 104, 10, 4, A['steel'][4])
    d.rect(126, 120, 8, 8, A['steel'][1])
    # warm air through the grate at the bottom
    for xx in range(70, 190, 4):
        d.rect(xx, 162, 2, 8, A['night'][1])
        d.rect(xx + 2, 162, 2, 8, A['lamp'][2])
    return d


def card_de():
    d = Doc(220, 150)
    d.paper(6, 8, 196, 132, C['cream'], seed=417, age=0.5, corner=False)
    # perforated right edge: the other half is missing
    for yy in range(8, 140):
        d.px(202, yy, C['edge'] if yy % 4 else C['shadow'])
        if yy % 4 == 0:
            d.rect(199, yy, 3, 2, C['shadow'])
    d.rect(170, 2, 14, 12, C['red'])
    d.text('C-17', 177, 5, C['white'][3], center=True, mark='tab')
    d.text('NR. 0417', 14, 14, C['ink'], scale=2, mark='number')
    d.line(14, 28, 190, 28, C['blue'])
    rows = (('LINDNER, ANNA', 'name'), ('GEB. KOWALENKO', 'born'), ('  1926 CHARKOW', 'birth'),
            ('VERMERK C-17: RÜCKFÜHRUNG OST', 'note'), ('ABGABE KORDON-17, TÜR OST', 'handover'),
            ('KURIERWAGEN C-17/45', 'wagon'), ('DI 18.2., 23.40', 'time'))
    y = 34
    for txt, mk in rows:
        # no wear on the typed rows: every one is a key line, and a dropped pixel in the 3x5 font turns
        # letters into others (the U-umlaut of RUECKFUEHRUNG read as a J with wear 0.03)
        d.text(txt, 14, y, C['ink'] if mk != 'note' else C['red'], mark=mk, wear=0.0, seed=y)
        if mk == 'birth':                                   # the asterisk of 'born' (not in the 3x5 font)
            for (ax, ay) in ((15, y + 1), (17, y + 1), (16, y + 2), (15, y + 3), (17, y + 3), (16, y + 1), (16, y + 3)):
                d.px(ax, ay, C['ink'])
        d.line(14, y + 7, 196, y + 7, C['cream'][0])
        y += 11
    d.hand(14, y + 2, 60, C['blue2'], seed=8)
    d.text('KIND ILSE, 8 - VERBLEIB UNGEKLÄRT', 14, y + 12, C['blue2'], mark='child')
    return d


def drawer():
    d = Doc(320, 170)
    d.rect(0, 0, 320, 170, A['steel'][1])
    d.rect(6, 6, 308, 158, A['steel'][2])
    d.rect(12, 18, 296, 140, A['steel'][0])
    rng = np.random.default_rng(212)
    tabs = set(int(v) for v in rng.choice(212, size=37, replace=False))
    # 212 cards on edge, seen from above: 4 rows of 53, a red tab on 37 of them
    k = 0
    for r in range(4):
        y0 = 22 + r * 34
        for c in range(53):
            x = 16 + c * 5 + (r % 2)
            d.rect(x, y0, 3, 30, C['cream'][1 + (c % 2)])
            d.px(x + 2, y0, C['cream'][0])
            if k in tabs:
                d.rect(x, y0 - 4, 3, 5, C['red'])
            k += 1
    d.rect(118, 0, 84, 14, C['white'][3])
    d.text('SÜD 8', 160, 2, C['ink'], scale=2, center=True, mark='label')
    d.text('212', 26, 160, C['white'][3], mark='count')
    d.text('37 X C-17', 260, 160, C['red2'], center=True, mark='tabs')
    return d


def plan():
    d = Doc(320, 220)
    d.rect(0, 0, 320, 220, A['steel'][0])
    d.rect(3, 3, 314, 214, A['steel'][2])
    d.paper(10, 10, 300, 200, C['white'], seed=1961, age=0.35, corner=False)
    d.text('LÜFTUNGSPLAN NEBENSTELLE SÜD', 18, 16, C['blue2'], mark='title')
    d.text('1961   BLATT 3', 18, 24, C['blue2'], mark='sheet')
    # three blocks above, hatched in red pencil: 'freizumachen'
    for i, bx in enumerate((40, 130, 220)):
        d.rect(bx, 44, 60, 36, C['white'][3])
        for k in range(60):
            d.px(bx + k, 44, C['blue'])
            d.px(bx + k, 79, C['blue'])
        for k in range(36):
            d.px(bx, 44 + k, C['blue'])
            d.px(bx + 59, 44 + k, C['blue'])
        for k in range(-36, 60, 5):
            for t in range(36):
                if 0 <= k + t < 60:
                    d.px(bx + k + t, 44 + t, C['red'])
        d.text('S%d' % (i + 1), bx + 30, 118, C['blue2'], center=True, mark='shaft_%d' % (i + 1))
        for yy in range(80, 150):
            d.px(bx + 28, yy, C['blue'])
            d.px(bx + 32, yy, C['blue'])
    d.text('FREIZUMACHEN', 160, 86, C['red'], center=True, mark='clear')
    # the annex: a long box under the street, the machine room, the card hall, the counter
    d.rect(30, 150, 262, 30, C['white'][2])
    for k in range(262):
        d.px(30 + k, 150, C['blue2'])
        d.px(30 + k, 179, C['blue2'])
    for k in range(30):
        d.px(30, 150 + k, C['blue2'])
        d.px(291, 150 + k, C['blue2'])
    for xx in (80, 210, 250):
        for k in range(30):
            d.px(xx, 150 + k, C['blue'])
    d.text('KARTEI', 145, 162, C['blue2'], center=True)
    # title block, signed by the man who drew it
    d.rect(214, 186, 92, 20, C['white'][3])
    for k in range(92):
        d.px(214 + k, 186, C['ink2'])
        d.px(214 + k, 205, C['ink2'])
    d.text('GEZ. K. ADLER', 220, 192, C['ink'], mark='signed')
    d.hand(224, 197, 60, C['ink2'], seed=4)
    return d


def tube_slip():
    d = Doc(250, 130)
    d.rect(6, 6, 238, 118, C['white'][2])
    d.paper(4, 4, 236, 114, C['white'], seed=45, age=0.3, corner=False)
    for k in range(0, 236, 6):
        d.px(4 + k, 4, C['red'])
    d.text('STAATSPOLIZEISTELLE', 12, 12, C['ink'], mark='sender')
    d.text('KOMMISSAR WENDT', 12, 20, C['ink'], mark='wendt')
    d.line(12, 28, 228, 28, C['grey'])
    lines = ('BIS MONTAG: ALLE C-17-HAUSHALTE', 'SÜD 8, VERBLEIB DER KINDER.', 'AUSKUNFTSPERSONEN NAMENTLICH.')
    for i, t in enumerate(lines):
        d.text(t, 12, 36 + i * 10, C['ink'], mark='order_%d' % (i + 1), wear=0.04, seed=i)
    d.print_lines(12, 72, 200, 3, C['ink2'], seed=9)
    d.text('EILT', 210, 100, C['red'], scale=2, center=True, mark='urgent')
    return d


def _dash_rect(d: Doc, x0, y0, x1, y1, col, dash=4, gap=3):
    """A pencilled dashed rectangle (the detour loops of the route board)."""
    for x in range(x0, x1 + 1):
        if (x - x0) % (dash + gap) < dash:
            d.px(x, y0, col)
            d.px(x, y1, col)
    for y in range(y0, y1 + 1):
        if (y - y0) % (dash + gap) < dash:
            d.px(x0, y, col)
            d.px(x1, y, col)


def _diamond(d: Doc, cx, cy, r, col):
    for k in range(-r, r + 1):
        w = r - abs(k)
        d.px(cx - w, cy + k, col)
        d.px(cx + w, cy + k, col)


def route_board():
    """Marta's route board (ev_c4_route_board, C4_DESIGN 2.5): tracing paper from the depot clipped to the cab's
    board, line 74 in her pencil and three detour loops dated Okt. / Dez. / Jan. (hollow diamonds at their centres,
    the geometry of the route puzzle's trace), drawn in driving direction -- not north up: the little north arrow
    points left, which is why the sheet must be turned once on the plan."""
    d = Doc(320, 210)
    d.rect(0, 0, 320, 210, A['steel'][1])
    d.rect(4, 4, 312, 202, A['steel'][2])
    for yy in range(8, 204, 6):                                  # hardboard grain
        for xx in range(6, 314):
            if (xx * 7 + yy * 3) % 23 == 0:
                d.px(xx, yy, A['steel'][1])
    d.paper(14, 14, 292, 184, C['white'], seed=74, age=0.25)
    for yy in range(20, 196, 9):                                 # the board's grain shows through the tracing paper
        for xx in range(18, 300, 2):
            if (xx + yy * 5) % 37 == 0:
                d.px(xx, yy, C['white'][1])
    d.rect(128, 2, 64, 14, A['steel'][3])                        # the clip
    d.rect(128, 2, 64, 1, A['steel'][4])
    d.rect(152, 14, 16, 4, A['steel'][3])
    for (px_, py_) in ((18, 18), (300, 18), (18, 192), (300, 192)):
        d.rect(px_, py_, 2, 2, C['grey'])
    d.text('LINIE 74', 22, 20, C['ink'], scale=2, mark='title')
    d.text('UMLEITUNGEN', 22, 34, C['ink2'], mark='detours')
    # north arrow: the sheet is drawn in driving direction, north lies to the left
    d.line(272, 30, 296, 30, C['ink2'])
    for k in range(1, 4):
        d.px(272 + k, 30 - k, C['ink2'])
        d.px(272 + k, 30 + k, C['ink2'])
    d.text('N', 264, 28, C['ink2'], mark='north')
    # the three detours of the winter, dashed in pencil around the blocks being cleared
    _dash_rect(d, 36, 52, 116, 118, C['pencil'])
    _dash_rect(d, 116, 118, 196, 182, C['pencil'])
    _dash_rect(d, 196, 52, 276, 118, C['pencil'])
    for (cx, cy) in ((64, 74), (176, 160), (252, 96)):
        _diamond(d, cx, cy, 5, C['ink'])
    d.text('OKT.', 46, 92, C['ink2'], mark='okt')
    d.text('DEZ.', 128, 128, C['ink2'], mark='dez')
    d.text('JAN.', 206, 60, C['ink2'], mark='jan')
    # line 74 itself: a heavy pencil line, the stops as ticks, the loop at the end
    for t in range(3):
        d.line(22, 117 + t, 280, 117 + t, C['ink2'])
    for sx in (28, 76, 156, 236):
        d.line(sx, 112, sx, 124, C['ink'])
    d.hand(24, 124, 26, C['pencil'], seed=741)
    d.hand(70, 124, 30, C['pencil'], seed=742)
    for a in range(0, 360, 12):                                  # the turning loop
        t = math.radians(a)
        d.px(int(round(290 + 8 * math.cos(t))), int(round(118 + 8 * math.sin(t))), C['ink2'])
    for k in range(4):                                           # driving direction on the line
        d.line(256 + k, 114 + k, 256 + k, 122 - k, C['ink'])
    d.text('FAHRTRICHTUNG', 206, 128, C['ink2'], mark='direction')
    d.text('WENDESCHLEIFE SÜD 8', 222, 150, C['ink'], mark='loop')
    d.stamp(62, 158, 16, C['red'], words=('DEPOT', 'SÜD'))
    d.hand(206, 168, 80, C['pencil'], seed=743)
    d.hand(22, 186, 120, C['pencil'], seed=744)
    return d


DOCS = [
    ('berlin_annex_notice', notice, 'ev_c4_notice', 'c4b_inspect_notice', 'door_9',
     'the eviction notice of house No. 9: typed notice, the fresh addendum "Haushalt aufgelöst. Vorgang an Nebenstelle Süd.", '
     'the attached Lageplan Süd 8 with the shafts S1-S3 and "gez. K. A."'),
    ('berlin_annex_shaft', shaft, 'ev_c4_shaft', 'c4b_inspect_column', 'column_s2',
     'the steel door behind the posters of S 2: "Lüftungsbauwerk S 2 - Zutritt nur für Bedienstete", warm air at the grate'),
    ('berlin_annex_card_de', card_de, 'ev_c4_card_de', 'c4b_inspect_crates', 'loading_hatch',
     'card No. 0417, the German half: Lindner, Anna, geb. Kowalenko, Rückführung Ost, C-17/45, Di 18.2., 23.40; '
     '"Kind Ilse, 8 - Verbleib ungeklärt"; perforated right edge'),
    ('berlin_annex_drawer', drawer, 'ev_c4_drawer_s8', 'c4d_inspect_drawer', 'drawer_s8',
     'drawer Süd 8 from above: 212 cards, 37 with a red C-17 tab'),
    ('berlin_annex_plan', plan, 'ev_c4_annex_plan', 'c4d_inspect_plan', 'plan_wall',
     'Lüftungsplan Nebenstelle Süd, 1961, Blatt 3: three shafts under three blocks hatched "freizumachen", gez. K. Adler'),
    ('berlin_annex_tube_slip', tube_slip, 'ev_c4_tube_slip', 'c4d_inspect_tube', 'tube_station',
     'the tube slip of the Staatspolizeistelle, Kommissar Wendt: all C-17 households Süd 8, where the children are, '
     'informants by name'),
    ('berlin_annex_route_board', route_board, 'ev_c4_route_board', 'c4b_talk_marta', 'marta_tram',
     "Marta's route board: tracing paper from the depot, line 74 in pencil with its stops and the turning loop "
     'Süd 8, three dashed detours dated Okt. / Dez. / Jan. with hollow diamonds, drawn in driving direction (the north '
     'arrow points left)'),
]
# every document carries the key of its German caption line (InspectView: UIKit.doc_alt_text); the texts are
# written by hand in data/locale/de_env_berlin_annex.json (round-9 fixes compl-04 / compl-10)
ALT_KEY = 'doc.%s.alt'


def build() -> list:
    out = []
    entries = []
    for row in DOCS:
        name, fn, item, obj, hot, desc = row[:6]
        extra = row[6] if len(row) > 6 else {}
        d = fn()
        path = d.save(name)
        _n, off = K.palette_report(d.a)
        if off:
            raise SystemExit('%s off palette: %s' % (name, off[:4]))
        out.append((os.path.relpath(path, ROOT).replace('\\', '/'), GEN, desc))
        key = item.replace('ev_', 'item.')
        entry = {'file': 'res://assets/ui/documents/%s.png' % name, 'size': [d.w, d.h], 'display_scale': 3,
                 'id': name, 'item_id': item, 'objective': obj, 'hotspot': hot,
                 'title_key': key + '.name', 'description_key': key + '.description', 'describes': desc,
                 'marks': d.marks, 'alt_key': ALT_KEY % name}
        entry.update(extra)
        entries.append(entry)
    data = {'scene': 'L_C4_AnnexA / L_C4_AnnexB', 'palette': 'annex', 'generator': GEN, 'date': K.DATE,
            'note': 'Pixel art drawn 1:1, shown at 3x (nearest). Story-critical words are legible 3x5 capitals; the '
                    'rest is print / handwriting scribble under the UI caption. Rects are [x, y, w, h] in document '
                    'pixels. The route board close-up (ev_c4_route_board, InspectView / evidence board) is drawn here '
                    '(round-9 fix compl-04); the route puzzle keeps its own overlay berlin_c4_routes_trace.png '
                    '(puzzle stream, berlin_c4_routes.json).',
            'documents': entries}
    p = os.path.join(DOC_DIR, 'berlin_annex_documents.json')
    with open(p, 'w', encoding='utf-8', newline='\n') as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
        f.write('\n')
    out.append((os.path.relpath(p, ROOT).replace('\\', '/'), GEN, 'document metadata (item -> image, key marks)'))
    return out


if __name__ == '__main__':
    for p, _g, _d in build():
        print(p)
