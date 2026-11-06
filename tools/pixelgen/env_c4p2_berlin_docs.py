"""env_c4p2_berlin_docs -- inspect-UI document art of L_C4P2_Berlin (drawn 1:1, shown at 3x by InspectView).

Five evidence items of C4P2_DESIGN §2.5 (scenes L_C4P2_BerlinA / L_C4P2_BerlinB), §2.5's document notes:
    berlin_c4p2_departures.png   ev_c4_departures_east  the enamel board of platform K (D 303 Berlin Ost – Kordon-17 –
                                                        Karsk 21.10) and the freshly painted board for Tuesday
    berlin_c4p2_seals.png (+_hist) ev_c4_courier_seals   two lead seals on the courier van's wire, both stamped „C-17“
                                                        (German: plain disc „DR“ / _hist eagle; Soviet: a wheel / _hist
                                                        star); beside it the green car's barred hatch, chalk „Di – Kordon“
    berlin_c4p2_tracing.png      ev_c4_konrad_tracing   Ekdahl's 1938 guidebook open at page 212 „Karsk – bangård och
                                                        depå“ (original design, no real publisher): the German half of
                                                        card 0417 laid in upside down, Konrad's tracing on onion skin
                                                        (Tür West, Tür Ost, the counter, the bench for 14), its corner
                                                        folded back: „MOROZOV – 0417 – DI 23.40 – TÜR OST“
    berlin_c4p2_house_notice.png (+_hist) ev_c4_house_notice  the Blockleitung's typed notice (no emblem / _hist the
                                                        party eagle), the pinned site plan „Bauabschnitt Süd 9 –
                                                        Kolonnenstraße 12 bis 18 – Lageplan“, houses hatched, „gez. K. A.“
    berlin_c4p2_house_cards.png  ev_c4_house_cards      Kuhnert's wooden box, the cards fanned out, the notes legible
Story-critical words are legible pixel capitals (3x5 font, distinct umlauts); the rest is print / handwriting
scribble under the UI's HD caption.  Writes berlin_c4p2_documents.json (schema of the other *_documents.json: id,
file, size, display_scale, item_id, objective, hotspot, marks, alt_key -- the German caption line, written by hand
in data/locale/de_env_berlin_c4p2.json).  Deterministic; palettes ostbahnhof (A) / courtyard (B) of
env_c4p2_berlin_kit.
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
import env_c4p2_berlin_kit as K  # noqa: E402
import pg  # noqa: E402

ROOT = K.ROOT
DOC_DIR = os.path.join(ROOT, 'assets', 'ui', 'documents')
GEN = 'tools/pixelgen/env_c4p2_berlin_docs.py'
ALT_KEY = 'doc.%s.alt'
O, Y = K.OST, K.YARD


def hx(h):
    return np.array(pg.hx(h), np.uint8)


class Doc:
    def __init__(self, w, h, pal):
        self.w, self.h, self.pal = w, h, pal
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

    def disc(self, cx, cy, r, col):
        for yy in range(-r, r + 1):
            for xx in range(-r, r + 1):
                if xx * xx + yy * yy <= r * r + r * 0.6:
                    self.px(cx + xx, cy + yy, col)

    def paper(self, x, y, w, h, ramp, seed=0, age=0.5, corner=True, edge=None, shadow=None):
        """A sheet: ordered-dither stains, a darker rim, a dog-eared corner, a drop shadow."""
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
                    self.px(x + w - 1 - j, y + k, shadow if (j < 2 and shadow) else ramp[max(0, n - 2)])
        if edge:
            for xx in range(w):
                self.px(x + xx + 2, y + h, edge)
            for yy in range(h):
                self.px(x + w, y + yy + 2, edge)

    def text(self, s, x, y, col, scale=1, mark=None, wear=0.0, seed=0, center=False, jitter=0):
        """3x5 capitals with distinct umlauts; y = the cap line (umlaut dots one row above)."""
        m = K.text_mask(s, '35', 1, overhang=True)
        oh = m.shape[0] - 5
        if center:
            x = int(round(x - m.shape[1] * scale / 2))
        rng = np.random.default_rng(seed)
        for yy in range(m.shape[0]):
            for xx in range(m.shape[1]):
                if m[yy, xx] and rng.random() >= wear:
                    jy = int(rng.integers(-jitter, jitter + 1)) if jitter and xx % 4 == 0 else 0
                    for dy in range(scale):
                        for dx in range(scale):
                            self.px(x + xx * scale + dx, y + (yy - oh) * scale + dy + jy, col)
        if mark:
            self.marks[mark] = {'rect': [int(x), int(y - oh * scale), int(m.shape[1] * scale),
                                         int(m.shape[0] * scale)], 'text': s}
        return x + m.shape[1] * scale

    def print_lines(self, x, y, w, rows, col, seed=0, gap=6, rag=0.3):
        """Typed / printed pseudo text: word blocks of scribble glyphs (never real words)."""
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

    def ring_stamp(self, cx, cy, r, col, words):
        for a in range(0, 360, 3):
            t = math.radians(a)
            for rr in (r, r - 1):
                if (a // 3) % 7 != 0:
                    self.px(int(round(cx + rr * math.cos(t))), int(round(cy + rr * math.sin(t))), col)
        self.text(words[0], cx, cy - 6, col, center=True, wear=0.2, seed=r)
        if len(words) > 1:
            self.text(words[1], cx, cy + 1, col, center=True, wear=0.2, seed=r + 1)

    def pin(self, x, y, col, hi):
        self.rect(x, y, 3, 3, col)
        self.px(x + 1, y + 1, hi)

    def save(self, name):
        path = os.path.join(DOC_DIR, name + '.png')
        Image.fromarray(self.a, 'RGBA').save(path)
        return path


# =========================================================================== A: the Ostbahnhof
def departures():
    d = Doc(300, 190, O)
    en, cr, so = O['enamel'], O['cream'], O['sodium']
    # the enamel board: dark blue, a cream rim, a white square with the platform letter
    d.rect(4, 4, 292, 104, O['night'][1])
    d.rect(6, 6, 288, 100, en[1])
    for k in range(288):
        d.px(6 + k, 8, cr[0])
        d.px(6 + k, 103, cr[0])
    for k in range(96):
        d.px(8, 8 + k, cr[0])
        d.px(291, 8 + k, cr[0])
    d.rect(14, 14, 26, 26, cr[1])
    d.text('K', 27, 18, en[0], scale=3, center=True, mark='platform')
    d.text('KORRIDOR OST', 48, 16, cr[1], scale=2, mark='corridor')
    d.text('BAHNSTEIG K', 48, 31, cr[0])
    for k in range(276):
        d.px(12 + k, 44, cr[0] if k % 2 else en[2])
    d.text('D 303', 16, 52, cr[1], scale=2, mark='train')
    d.text('BERLIN OST – KORDON-17 – KARSK', 16, 72, cr[1], mark='route')
    d.text('MIT SPEISEWAGEN · KURSWAGEN NACH KARSK', 16, 84, cr[0])
    d.text('SCHLAFWAGEN NUR MIT KORRIDORSCHEIN', 16, 93, O['steam'][3])
    tx = 288 - K.tw('21.10') * 2                                              # the time, right-aligned
    d.text('21.10', tx, 52, so[3], scale=2, mark='time')
    # the iron hooks and the hand-painted board for Tuesday below
    for hxp in (60, 240):
        d.line(hxp, 106, hxp, 116, O['steel'][2])
        d.rect(hxp - 1, 115, 3, 2, O['steel'][3])
    wd = O['wood']
    thr = pg.bayer(272, 66, 3, 1, 4)
    rngp = np.random.default_rng(7)
    plank_off = [rngp.uniform(-0.3, 0.3) for _ in range(8)]
    for yy in range(66):
        pl = yy // 11
        for xx in range(272):
            t = 1.45 + plank_off[pl] + 0.3 * math.sin(xx * 0.06 + pl * 1.7 + yy * 0.8) - (0.9 if yy % 11 == 0 else 0)
            idx = int(np.clip(math.floor(t) + ((t - math.floor(t)) > thr[yy, xx]), 0, 3))
            d.px(14 + xx, 118 + yy, wd[idx])
    for k in range(272):
        d.px(14 + k, 118, wd[3])
        d.px(14 + k, 183, O['night'][2])
    paint = O['cream'][0]
    d.text('DIENSTAG:', 22, 125, paint, mark='tuesday_1', seed=1)
    d.text('SONDERZUG NACH KORDON-17 MIT SONDERWAGEN,', 22, 137, paint, mark='tuesday_2', seed=2)
    d.text('AB 15.30 UHR.', 22, 149, paint, mark='tuesday_3', seed=3)
    d.text('BAHNSTEIG K AB 15 UHR GESPERRT.', 22, 163, O['red'][3], mark='closed', seed=4)
    return d


def _lead_seal(d, cx, cy, r, kind, hist, txt_col):
    """A lead seal pressed onto the wire: dull grey disc with a raised rim, the emblem and „C-17“."""
    st = O['steam']
    for yy in range(-r, r + 1):
        for xx in range(-r, r + 1):
            dd = math.hypot(xx, yy)
            if dd > r + 0.3:
                continue
            t = 1.6 + (-(xx + yy) / (2 * r)) * 1.4
            if dd > r - 2:
                t += 0.9 if (xx + yy) < 0 else -0.6
            d.px(cx + xx, cy + yy, st[int(np.clip(round(t), 0, 4))])
    em = O['steel'][1]
    hi = st[3]
    if kind == 'de':
        if hist:
            import env_berlin_insignia as BI
            ms = BI.eagle_masks(15, wreath=True, swastika=True)
            m = ms['all']
            hh, ww = m.shape
            for yy in range(hh):
                for xx in range(ww):
                    if m[yy, xx]:
                        d.px(cx - ww // 2 + xx, cy - 12 + yy, em if not ms['swastika'][yy, xx] else st[0])
        else:
            for a in range(0, 360, 10):                                       # a plain disc „DR“
                t = math.radians(a)
                d.px(int(round(cx + 7 * math.cos(t))), int(round(cy - 5 + 7 * math.sin(t))), em)
            d.text('DR', cx, cy - 7, em, center=True)
    else:
        if hist:                                                               # a five-pointed star
            pts = []
            for k in range(10):
                rr = 8 if k % 2 == 0 else 3.4
                t = math.radians(-90 + k * 36)
                pts.append((cx + rr * math.cos(t), cy - 5 + rr * math.sin(t)))
            for yy in range(-9, 9):
                for xx in range(-9, 9):
                    if _in_poly(cx + xx + 0.5, cy - 5 + yy + 0.5, pts):
                        d.px(cx + xx, cy - 5 + yy, em)
        else:                                                                  # a wheel
            for a in range(0, 360, 8):
                t = math.radians(a)
                d.px(int(round(cx + 7 * math.cos(t))), int(round(cy - 5 + 7 * math.sin(t))), em)
            for a in range(0, 360, 45):
                t = math.radians(a)
                d.line(cx, cy - 5, cx + 6 * math.cos(t), cy - 5 + 6 * math.sin(t), em)
            d.disc(cx, cy - 5, 1, hi)
    d.text('C-17', cx, cy + 6, txt_col, center=True)


def _in_poly(x, y, pts):
    inside = False
    n = len(pts)
    for i in range(n):
        x1, y1 = pts[i]
        x2, y2 = pts[(i + 1) % n]
        if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1 + 1e-9) + x1:
            inside = not inside
    return inside


def seals(hist=False):
    d = Doc(300, 180, O)
    st = O['steel']
    # the courier van's door: vertical boards, dark grey-olive, the rail, the handle
    for xx in range(0, 196):
        for yy in range(0, 180):
            t = 2 + (0.6 if xx % 14 == 1 else 0) - (0.8 if xx % 14 == 0 else 0) + (yy / 180) * -0.6
            d.px(xx, yy, st[int(np.clip(round(t), 0, 4))])
    d.rect(0, 14, 196, 5, O['night'][2])
    d.rect(150, 40, 10, 70, st[4])
    d.rect(152, 42, 6, 66, st[3])
    # the wire through the handle, the two seals side by side
    pts = [(155, 70), (130, 96), (102, 110), (60, 112), (30, 100)]
    for a, b in zip(pts[:-1], pts[1:]):
        d.line(a[0], a[1], b[0], b[1], O['steam'][1])
        d.line(a[0], a[1] + 1, b[0], b[1] + 1, O['night'][3])
    _lead_seal(d, 100, 118, 17, 'de', hist, O['night'][1])
    _lead_seal(d, 52, 120, 17, 'su', hist, O['night'][1])
    d.marks['seal_de'] = {'rect': [83, 101, 35, 35], 'text': 'C-17 (DR)'}
    d.marks['seal_su'] = {'rect': [35, 103, 35, 35], 'text': 'C-17'}
    d.text('KURIER', 20, 30, O['red'][2])
    # the green car on the next track: a barred hatch high up, the chalk on its door
    gr = O['green']
    for xx in range(200, 300):
        for yy in range(0, 180):
            t = 1.6 + (0.5 if xx % 9 == 0 else 0) - (yy / 180) * 0.6
            d.px(xx, yy, gr[int(np.clip(round(t), 0, 3))])
    d.rect(196, 0, 4, 180, O['night'][0])
    d.rect(216, 18, 60, 30, O['night'][1])
    for bx in range(220, 276, 7):
        d.rect(bx, 18, 2, 30, st[4])
    for k in range(30):
        d.px(240 + (k % 12), 22 + k // 3, O['steam'][4] if (k * 7) % 5 else O['steam'][3])   # frost from inside
    d.text('DI – KORDON', 250, 92, O['steam'][4], center=True, mark='chalk', seed=5)
    d.line(212, 100, 288, 98, O['steam'][3])
    return d


def tracing():
    d = Doc(300, 200, O)
    pa, cr = O['paper'], O['cream']
    # the guidebook open at page 212/213: blue linen cover edges, two cream pages, the gutter
    d.rect(4, 10, 292, 184, O['enamel'][1])
    d.paper(10, 14, 138, 174, [pa[2], pa[3], pa[4], cr[0]], seed=212, age=0.35, corner=False)
    d.paper(152, 14, 138, 174, [pa[2], pa[3], pa[4], cr[0]], seed=213, age=0.35, corner=False)
    for yy in range(14, 188):
        d.px(148, yy, pa[0])
        d.px(149, yy, pa[1])
        d.px(150, yy, pa[1])
        d.px(151, yy, pa[0])
    ink = O['night'][1]
    d.text('KARSK – BANGÅRD OCH DEPÅ', 79, 22, ink, center=True, mark='chapter')
    d.print_lines(18, 34, 122, 9, pa[0], seed=21, gap=6)
    d.text('212', 18, 180, ink, mark='page')
    d.text('213', 271, 180, ink)
    d.print_lines(160, 22, 122, 3, pa[0], seed=22, gap=6)
    # a little engraving of the station on the left page
    for xx in range(24, 128):
        d.px(xx, 132, ink)
    for (x0, x1, top) in ((30, 60, 112), (64, 100, 104), (104, 124, 116)):
        for xx in range(x0, x1):
            d.px(xx, top, ink)
        for yy in range(top, 132):
            d.px(x0, yy, ink)
            d.px(x1 - 1, yy, ink)
        for wx in range(x0 + 4, x1 - 4, 6):
            d.rect(wx, top + 6, 2, 4, pa[1])
    # the German half of card 0417, laid in upside down: only its red tab and the number read the right way
    d.paper(22, 140, 112, 38, [cr[0], cr[1]], seed=417, age=0.3, corner=False)
    for xx in range(22, 134):
        d.px(xx, 140, pa[1] if xx % 4 else pa[0])                            # the perforation now at the top
    d.rect(30, 172, 14, 8, O['red'][2])
    d.print_lines(30, 150, 96, 3, O['enamel'][1], seed=23, gap=6)
    d.marks['card_de'] = {'rect': [22, 140, 112, 38], 'text': 'Karte 0417, deutsche Hälfte (verkehrt herum)'}
    # Konrad's tracing on onion skin over the right page: the room of Kordon-17
    on = [cr[0], cr[1]]
    d.paper(160, 46, 124, 110, on, seed=740, age=0.15, corner=False)
    gl = O['steam'][1]
    for xx in range(170, 274):
        d.px(xx, 58, gl)
        d.px(xx, 132, gl)
    for yy in range(58, 133):
        d.px(170, yy, gl)
        d.px(273, yy, gl)
    for yy in range(80, 96):                                                   # the two doors
        d.px(170, yy, cr[1])
        d.px(273, yy, cr[1])
    d.rect(212, 62, 20, 6, gl)                                                 # the counter in the middle
    d.text('SCHALTER', 222, 71, ink, center=True, mark='counter')
    d.text('TÜR WEST', 174, 86, ink, mark='door_west')                        # beside the door openings (80..96)
    d.text('TÜR OST', 270 - K.tw('TÜR OST'), 86, ink, mark='door_east')
    for (ax, dx) in ((172, 1), (271, -1)):                                     # small arrows to the doors
        d.px(ax, 88, ink)
        d.px(ax + dx, 87, ink)
        d.px(ax + dx, 89, ink)
    for k in range(14):                                                        # the bench for 14
        d.rect(184 + k * 6, 116, 4, 3, gl)
    d.text('BANK FÜR 14', 222, 122, ink, center=True, mark='bench')
    # the lower right corner folded back: the back of the sheet with the block letters
    for yy in range(0, 40):
        for xx in range(0, 40 - yy):
            d.px(284 - xx, 156 - yy, cr[1] if (xx + yy) % 5 else cr[0])
    for k in range(40):
        d.px(244 + k, 156 - k, gl)
    d.paper(196, 158, 96, 34, on, seed=741, age=0.2, corner=False)
    d.text('MOROZOV – 0417', 244, 164, O['night'][0], center=True, mark='back_1')
    d.text('DI 23.40 – TÜR OST', 244, 176, O['night'][0], center=True, mark='back_2')
    return d


# =========================================================================== B: Kolonnenstraße 14
def _party_eagle(d, cx, y, col):
    import env_berlin_insignia as BI
    ms = BI.eagle_masks(22, wreath=True, swastika=True)
    m = ms['all'][:, ::-1]                                                    # the party eagle looks right
    sw = ms['swastika'][:, ::-1]
    hh, ww = m.shape
    for yy in range(hh):
        for xx in range(ww):
            if m[yy, xx]:
                d.px(cx - ww // 2 + xx, y + yy, col if not sw[yy, xx] else Y['night'][0])
    return hh


def house_notice(hist=False):
    d = Doc(320, 210, Y)
    pa = Y['paper']
    ink, ink2 = Y['night'][1], Y['plaster'][1]
    d.rect(0, 0, 320, 210, Y['wood'][1])                                       # the cork board behind
    nz = pg.value_noise(320, 210, 3, 9, octaves=2)
    for yy in range(210):
        for xx in range(320):
            if nz[yy, xx] > 0.6:
                d.px(xx, yy, Y['wood'][2])
    d.paper(10, 8, 168, 194, [pa[2], pa[3], pa[4]], seed=141, age=0.6, edge=Y['night'][2])
    y0 = 16
    if hist:
        y0 += _party_eagle(d, 94, 14, ink) + 2
    d.text('BEKANNTMACHUNG', 94, y0 + 2, ink, scale=2, center=True, mark='title')
    d.text('DER BLOCKLEITUNG', 94, y0 + 18, ink, center=True, mark='blockleitung')
    d.print_lines(20, y0 + 30, 148, 2, ink2, seed=1)
    yk = y0 + 46
    for i, s in enumerate(('ALLE HAUSHALTE HALTEN SICH AM', 'DIENSTAG AB 22 UHR ZUR', 'ÜBERPRÜFUNG DER HAUSHALTS-',
                           'KARTEI BEREIT.')):
        d.text(s, 20, yk + i * 9, ink, mark='line_%d' % (i + 1))
    d.text('KINDER SIND VORZUZEIGEN.', 20, yk + 42, ink, mark='children')
    for xx in range(20, 118):
        d.px(xx, yk + 49, Y['red'][2])                                         # underlined by somebody
    d.print_lines(20, yk + 58, 148, 4, ink2, seed=2)
    d.ring_stamp(140, 182, 15, Y['red'][2], ('BLOCK', 'LEITUNG'))
    d.hand(24, 176, 70, Y['dusk'][1], seed=5)
    # the site plan, pinned over the notice's corner
    d.paper(150, 70, 160, 132, [Y['snow'][3], Y['snow'][4]], seed=142, age=0.3, corner=False,
            edge=Y['night'][2])
    bl = Y['dusk'][2]
    px0, py0 = 160, 82
    d.rect(px0, py0 + 50, 140, 8, Y['snow'][2])                                # the street
    d.text('KOLONNENSTRASSE', px0 + 70, py0 + 52, bl, center=True)
    for i, nr in enumerate((12, 13, 14, 15, 16, 17, 18)):
        x = px0 + i * 20
        for (bx, by, bw, bh) in ((x + 1, py0 + 26, 18, 22), (x + 1, py0 + 4, 6, 22), (x + 1, py0, 18, 5)):
            for yy in range(by, by + bh):
                for xx in range(bx, bx + bw):
                    edge_ = yy in (by, by + bh - 1) or xx in (bx, bx + bw - 1)
                    if edge_:
                        d.px(xx, yy, bl)
                    elif (xx + yy) % 3 == 0:
                        d.px(xx, yy, bl)                                        # hatched: all of them
        d.rect(x + 3, py0 + 31, 14, 9, Y['snow'][4])                          # a clear label for the number
        for xx in range(x + 3, x + 17):
            d.px(xx, py0 + 31, bl)
            d.px(xx, py0 + 39, bl)
        d.text(str(nr), x + 10, py0 + 33, Y['night'][1], center=True, mark='house_14' if nr == 14 else None)
        if nr == 14:                                                          # ringed in red pencil
            for a in range(0, 360, 6):
                t = math.radians(a)
                d.px(int(round(x + 10 + 10 * math.cos(t))), int(round(py0 + 35 + 7 * math.sin(t))), Y['red'][2])
    d.rect(px0, py0 + 62, 140, 1, bl)
    d.text('BAUABSCHNITT SÜD 9', px0 + 4, py0 + 70, Y['night'][1], mark='plan_title')
    d.text('KOLONNENSTR. 12 BIS 18', px0 + 4, py0 + 80, Y['night'][1], mark='plan_street')
    d.text('LAGEPLAN', px0 + 4, py0 + 90, bl, mark='plan')
    d.rect(px0 + 95, py0 + 86, 44, 22, Y['snow'][3])
    for k in range(44):
        d.px(px0 + 95 + k, py0 + 86, bl)
    d.text('GEZ. K. A.', px0 + 98, py0 + 92, Y['night'][1], mark='sign_ka')
    d.pin(152, 72, Y['red'][2], Y['red'][3])
    d.pin(302, 72, Y['red'][2], Y['red'][3])
    return d


def house_cards():
    d = Doc(320, 220, Y)
    wd = Y['wood']
    d.rect(0, 0, 320, 220, Y['plaster'][1])                                     # the sill
    for yy in range(0, 220, 9):
        for xx in range(320):
            if (xx + yy) % 7 == 0:
                d.px(xx, yy, Y['plaster'][2])
    # the wooden box at the bottom, open, cards standing in it
    d.rect(18, 176, 284, 40, wd[1])
    d.rect(20, 178, 280, 36, wd[2])
    for xx in range(20, 300, 23):
        d.rect(xx, 178, 1, 36, wd[1])
    d.rect(24, 168, 272, 10, Y['paper'][4])
    for xx in range(24, 296, 3):
        d.px(xx, 168, Y['paper'][2])
    d.rect(150, 194, 22, 8, Y['window'][2])                                     # a brass label holder
    d.text('NR. 14', 161, 196, wd[0], center=True)
    # seven cards fanned out on the sill, each note legible, in Kuhnert's ink
    ink = Y['night'][1]
    notes = (('SF 3: ADLER, HANNA – LEHRERIN, 1 PERS.', 'adler'),
             ('SF 2: POHL, GERTRUD – WITWE – MELDET ZUVERLÄSSIG', 'pohl'),
             ('LOGE: KUHNERT, ERWIN U. FRIEDA – FENSTER ZUM HOF', 'loge'),
             ('HH 3: LEER, UMGESETZT 10/63', 'leer'),
             ('DURCHFAHRT: AB 22 UHR BLOCKLEITER', 'durchfahrt'),
             ('DACHBODEN: WASCHTAG DI: OFFEN', 'dachboden'))
    for i, (s, mk) in enumerate(notes):
        x, y = 12 + (i % 2) * 6, 8 + i * 22
        d.paper(x, y, 220 + (i % 3) * 8, 20, [Y['paper'][3], Y['paper'][4]], seed=50 + i, age=0.3, corner=False,
                edge=Y['plaster'][0])
        for xx in range(x, x + 220):
            d.px(xx, y + 6, Y['laundry'][0] if xx % 2 else Y['paper'][3])
        if mk == 'adler':
            d.rect(x + 2, y + 1, 10, 4, Y['red'][2])                           # Hanna's card has no tab ...
            d.rect(x + 2, y + 1, 10, 4, Y['paper'][4])
        d.text(s, x + 4, y + 10, ink, mark=mk)
    # the slip without a household card: the cobbler's workshop
    d.paper(236, 40, 78, 62, [Y['snow'][3], Y['snow'][4]], seed=58, age=0.2, corner=False, edge=Y['plaster'][0])
    d.text('SCHUHMACHEREI', 275, 48, ink, center=True, mark='pietsch_1')
    d.text('PIETSCH,', 275, 57, ink, center=True, mark='pietsch_2')
    d.text('SOUTERRAIN', 275, 66, ink, center=True, mark='pietsch_3')
    d.text('– GEWERBE –', 275, 78, Y['red'][2], center=True, mark='pietsch_4')
    d.text('KEINE HH-KARTE', 275, 90, Y['dusk'][2], center=True)
    return d


DOCS = [
    ('berlin_c4p2_departures', departures, 'ev_c4_departures_east', 'c4f_inspect_board', 'departure_board',
     'the enamel departure board of platform K: D 303 Berlin Ost – Kordon-17 – Karsk 21.10; the hand-painted board for '
     'Tuesday: special train to Kordon-17 with a special car from 15.30, platform K closed from 15.00', O, False),
    ('berlin_c4p2_seals', seals, 'ev_c4_courier_seals', 'c4f_inspect_courier', 'courier_car',
     'two lead seals on the courier van\'s wire, both stamped C-17 (German: a plain disc DR / _hist eagle; Soviet: a '
     'wheel / _hist star); beside it the green car on the next track, a barred hatch frosted from inside, the chalk '
     '„Di – Kordon“', O, True),
    ('berlin_c4p2_tracing', tracing, 'ev_c4_konrad_tracing', 'c4f_inspect_book', 'dining_table',
     'Ekdahl\'s guidebook open at page 212 „Karsk – bangård och depå“, the German half of card 0417 laid in upside down, '
     'Konrad\'s tracing of the room of Kordon-17 (Tür West, Tür Ost, the counter, the bench for 14), its corner folded '
     'back: MOROZOV – 0417 – DI 23.40 – TÜR OST', O, False),
    ('berlin_c4p2_house_notice', house_notice, 'ev_c4_house_notice', 'c4h_inspect_gate', 'gate_notice',
     'the Blockleitung\'s notice (Tuesday from 22.00, children to be shown; neutral: no emblem / _hist: the party '
     'eagle), the pinned site plan Bauabschnitt Süd 9 – Kolonnenstraße 12 bis 18, all houses hatched, gez. K. A.',
     Y, True),
    ('berlin_c4p2_house_cards', house_cards, 'ev_c4_house_cards', 'c4h_inspect_cards', 'lodge_window',
     'Kuhnert\'s wooden box of household cards, six cards fanned out (Adler, Pohl, the lodge, the empty Hinterhaus 3, '
     'the passage, the drying loft) and the slip of the cobbler Pietsch (no household card)', Y, False),
]


def build() -> list:
    out = []
    entries = []
    for (name, fn, item, obj, hot, desc, pal, has_hist) in DOCS:
        d = fn()
        path = d.save(name)
        _n, off = K.palette_report(d.a, pal)
        if off:
            raise SystemExit('%s off palette: %s' % (name, off[:4]))
        out.append((os.path.relpath(path, ROOT).replace('\\', '/'), GEN, desc))
        if has_hist:
            dh = fn(hist=True)
            ph = dh.save(name + '_hist')
            _n, off = K.palette_report(dh.a, pal)
            if off:
                raise SystemExit('%s_hist off palette: %s' % (name, off[:4]))
            out.append((os.path.relpath(ph, ROOT).replace('\\', '/'), GEN,
                        desc + ' -- historical insignia variant (Symbols.pick, 12.4)'))
        key = item.replace('ev_', 'item.')
        entries.append({'file': 'res://assets/ui/documents/%s.png' % name, 'size': [d.w, d.h], 'display_scale': 3,
                        'id': name, 'item_id': item, 'objective': obj, 'hotspot': hot,
                        'title_key': key + '.name', 'description_key': key + '.description', 'describes': desc,
                        'marks': d.marks, 'alt_key': ALT_KEY % name})
    data = {'scene': 'L_C4P2_BerlinA / L_C4P2_BerlinB', 'palette': 'ostbahnhof (A) / courtyard (B)', 'generator': GEN,
            'date': K.DATE,
            'note': 'Pixel art drawn 1:1, shown at 3x (nearest). Story-critical words are legible 3x5 capitals; the '
                    'rest is print / handwriting scribble under the UI caption. Rects are [x, y, w, h] in document '
                    'pixels. Two documents carry insignia (seals, house notice) and have a _hist twin that '
                    'Symbols.pick() chooses.',
            'documents': entries}
    p = os.path.join(DOC_DIR, 'berlin_c4p2_documents.json')
    with open(p, 'w', encoding='utf-8', newline='\n') as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
        f.write('\n')
    out.append((os.path.relpath(p, ROOT).replace('\\', '/'), GEN, 'document metadata (item -> image, key marks)'))
    return out


if __name__ == '__main__':
    for p, _g, _d in build():
        print(p)
