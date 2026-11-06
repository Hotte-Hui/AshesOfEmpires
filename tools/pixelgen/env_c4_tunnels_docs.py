"""env_c4_tunnels_docs -- inspect close-ups of Chapter 4 part 1, Karsk (documentation/C4_DESIGN.md 2.5).

Run:  py -3 -P tools/pixelgen/env_c4_tunnels_docs.py        (deterministic, no network)

Writes assets/ui/documents/karsk_tunnels_*.png + karsk_tunnels_documents.json (InspectView metadata: item -> image,
alt text key, marks).  Weighbill style like the Karsk / Veltrava documents: drawn 1:1, shown at 3x; only the
story-critical figures are legible (dates, wagon numbers, the cut-out column, the stamp), everything else is
scribble -- the UI shows the item name and description as HD text, the alt text (data/locale/de_env_karsk_tunnels.json)
is the German caption line.  Palette 'tunnels' (env_c4_tunnels_kit.TUN).  No real names of persons anywhere; the
names scratched into the wagon stay illegible scratches.
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
import env_c4_tunnels_kit as K  # noqa: E402

ROOT = K.ROOT
DOCS = os.path.join(ROOT, 'assets', 'ui', 'documents')
LF = chr(10)


def C(ramp, i, a=255):
    return K.rgba(ramp, i, a)


class Doc:
    def __init__(self, w, h, bg=('N', 1)):
        self.w, self.h = w, h
        self.a = np.zeros((h, w, 4), np.uint8)
        self.a[:] = C(*bg)
        self.rng = np.random.default_rng(w * 7 + h)

    def rect(self, x, y, w, h, col):
        x0, y0, x1, y1 = max(0, x), max(0, y), min(self.w, x + w), min(self.h, y + h)
        if x1 > x0 and y1 > y0:
            self.a[y0:y1, x0:x1] = col

    def px(self, x, y, col):
        if 0 <= x < self.w and 0 <= y < self.h:
            self.a[y, x] = col

    def line(self, x0, y0, x1, y1, col):
        for (x, y) in K.bres(x0, y0, x1, y1):
            self.px(x, y, col)

    def mask(self, m, x, y, col):
        h, w = m.shape
        for yy in range(h):
            for xx in range(w):
                if m[yy, xx]:
                    self.px(x + xx, y + yy, col)

    def text(self, s, x, y, col, font='35', scale=1, center=False, wear=0.0, seed=0):
        m = K.text_mask(s, font)
        if scale > 1:
            m = np.kron(m, np.ones((scale, scale), bool))
        if center:
            x = int(round(x - m.shape[1] / 2))
        if wear > 0:
            m = m & (np.random.default_rng(seed).random(m.shape) >= wear)
        self.mask(m, x, y, col)
        return m.shape[1]

    def paper(self, x, y, w, h, seed=0, base=4.0, ramp='P', aged=True):
        nz = K.noise(w, h, 18, seed) * 0.6 + K.noise(w, h, 3, seed + 1, octaves=1) * 0.3
        t = base + nz
        if aged:
            yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
            edge = np.minimum(np.minimum(xx, w - 1 - xx), np.minimum(yy, h - 1 - yy))
            t -= np.clip(1 - edge / 10.0, 0, 1) * 0.9
        rgba = K.ramp_rgba(ramp, np.clip(t, 0, K.R.n(ramp) - 1), np.full((h, w), 255, np.uint8), seed=seed)
        self.a[y:y + h, x:x + w] = rgba

    def scribble(self, x, y, w, col, seed=0, rows=1, gap=6, rag=0.3):
        rng = np.random.default_rng(seed)
        for r in range(rows):
            xx = x
            end = x + w - int(rng.random() * w * rag)
            while xx < end:
                wl = int(rng.integers(3, 9))
                wl = min(wl, end - xx)
                for k in range(wl):
                    dy = int(rng.integers(-1, 2)) if k % 2 else 0
                    self.px(xx + k, y + r * gap + dy, col)
                    if rng.random() < 0.3:
                        self.px(xx + k, y + r * gap - 1 + dy, col)
                xx += wl + 2

    def stamp(self, s, x, y, col, scale=2, seed=0, frame=True, holes=0.16):
        m = K.text_mask(s)
        m = np.kron(m, np.ones((scale, scale), bool))
        h, w = m.shape
        if frame:
            fm = np.zeros((h + 8, w + 10), bool)
            fm[0, :] = fm[-1, :] = True
            fm[:, 0] = fm[:, -1] = True
            fm[2, 2:-2] = fm[-3, 2:-2] = True
            fm[2:-2, 2] = fm[2:-2, -3] = True
            fm[4:4 + h, 5:5 + w] |= m
            m = fm
        rng = np.random.default_rng(seed)
        m = m & (rng.random(m.shape) >= holes)
        self.mask(m, x, y, col)
        return m.shape

    def save(self, name):
        p = os.path.join(DOCS, name + '.png')
        Image.fromarray(self.a, 'RGBA').save(p)
        return p


INK, INK2, PENCIL, RED, RED2 = C('N', 1), C('I', 3), C('I', 4), C('R', 2), C('R', 3)


def desk_bg(d, seed=0):
    """Dark desk wood under the document (Lev's desk / the counter)."""
    nz = K.noise(d.w, d.h, 6, seed) * 0.5
    g = np.sin(np.arange(d.w, dtype=np.float32)[None, :] / 3.0 + K.noise(d.w, d.h, 20, seed + 1) * 6) * 0.25
    t = 1.6 + nz + g
    d.a[:] = K.ramp_rgba('D', np.clip(t, 0, 7), np.full((d.h, d.w), 255, np.uint8), seed=seed)


# =========================================================================== the January freight book
def freight_book():
    d = Doc(320, 200)
    desk_bg(d, 901)
    x0, y0, w, h = 12, 10, 296, 180
    d.rect(x0 + 3, y0 + 4, w, h, C('N', 0))
    d.paper(x0, y0, w, h, seed=902, base=4.1)
    d.rect(x0 + w // 2 - 1, y0, 2, h, C('P', 1))                               # the gutter
    d.rect(x0, y0, 3, h, C('R', 1))                                               # cloth binding edge
    cols = [x0 + 8, x0 + 40, x0 + 82, x0 + 150, x0 + 212, x0 + 288]               # ДАТА · ВАГОН · НАЗН. · РАЗРЕШИЛ · ПРИМЕЧ.
    heads = ['ДАТА', 'ВАГОН №', 'НАЗНАЧ.', 'РАЗРЕШИЛ', 'ПРИМЕЧАНИЕ']
    for i, hd in enumerate(heads):
        d.text(hd, (cols[i] + cols[i + 1]) // 2, y0 + 7, INK, center=True)
    d.rect(x0 + 6, y0 + 15, w - 12, 1, INK2)
    for c in cols:
        d.rect(c, y0 + 4, 1, h - 10, C('I', 4))
    rows = [('11.01', '53 117', None), ('12.01', '62 409', None), ('14.01', 'C-17/41', 'cut'), ('16.01', '24 871', None),
            ('18.01', '47 115', None), ('21.01', 'C-17/42', 'cut'), ('23.01', '30 298', None), ('25.01', '58 226', None),
            ('28.01', 'C-17/43', 'cut'), ('30.01', '41 760', None)]
    marks = {}
    for r, (date, wagon, cut) in enumerate(rows):
        ry = y0 + 22 + r * 15
        d.rect(x0 + 6, ry + 11, w - 12, 1, C('P', 2))
        d.text(date, cols[0] + 3, ry + 3, INK)
        if cut:
            d.text(wagon, cols[1] + 4, ry + 3, RED)
            d.text('КОРДОН-17', cols[2] + 5, ry + 3, INK)
            # the signature cut out with a blade: a clean rectangular hole, the desk shows through
            cx0, cx1 = cols[3] + 6, cols[4] - 6
            d.rect(cx0, ry, cx1 - cx0, 11, C('D', 1))
            d.rect(cx0, ry, cx1 - cx0, 1, C('N', 0))
            d.rect(cx0, ry, 1, 11, C('N', 0))
            d.rect(cx1 - 1, ry + 1, 1, 10, C('P', 5))                               # the clean cut edge catches light
            d.text('ОТД. Т – УСТНО', (cols[4] + cols[5]) // 2, ry + 3, INK, center=True)
            marks['cut_%s' % date[:2]] = {'rect': [cx0, ry, cx1 - cx0, 11], 'text': '%s – %s – Unterschrift '
                                          'herausgeschnitten' % (date, wagon)}
            marks['note_%s' % date[:2]] = {'rect': [cols[4] + 4, ry + 2, cols[5] - cols[4] - 8, 7],
                                           'text': 'Abt. T – mündlich'}
        else:
            d.text(wagon, cols[1] + 4, ry + 3, INK)
            d.scribble(cols[2] + 4, ry + 6, cols[3] - cols[2] - 10, INK2, seed=910 + r)
            d.scribble(cols[3] + 6, ry + 6, cols[4] - cols[3] - 22, C('I', 1), seed=920 + r, rag=0.5)
            d.scribble(cols[4] + 4, ry + 6, cols[5] - cols[4] - 12, INK2, seed=930 + r, rag=0.6)
    d.text('ЯНВАРЬ 1964 - КН. II', x0 + w // 2 + 20, y0 + h - 9, INK2)
    marks['column'] = {'rect': [cols[3], y0 + 4, cols[4] - cols[3], 12], 'text': 'Spalte „Genehmigt“ (РАЗРЕШИЛ)'}
    d.save('karsk_tunnels_freight_book')
    return {'id': 'karsk_tunnels_freight_book', 'item_id': 'ev_c4_cut_signatures', 'objective': 'c4a_inspect_book',
            'hotspot': 'desk_book', 'size': [d.w, d.h], 'marks': marks,
            'describes': 'Lev\'s January freight book open on the desk: columns date, wagon, destination, approved '
                         'by, remark. In the rows 14.01 (C-17/41), 21.01 (C-17/42) and 28.01 (C-17/43), destination '
                         'Kordon-17, the signature in the column РАЗРЕШИЛ is cut out with a blade; beside each the '
                         'same remark ОТД. Т – УСТНО.'}


# =========================================================================== the carbons against the lamp
def carbon():
    d = Doc(300, 200)
    # the frosted glass of the light box, glowing warm from below
    yy, xx = np.mgrid[0:d.h, 0:d.w].astype(np.float32)
    glow = np.clip(1 - np.hypot((xx - 150) / 190.0, (yy - 110) / 130.0), 0, 1)
    t = 2.0 + 3.4 * glow + K.noise(d.w, d.h, 4, 941, octaves=1) * 0.25
    d.a[:] = K.ramp_rgba('L', np.clip(t, 0, 5), np.full((d.h, d.w), 255, np.uint8), seed=941)
    marks = {}
    # three carbon sheets fanned, the top one fully on the glass
    for k, (sx, sy, rot) in enumerate(((22, 18, 0), (40, 30, 0), (58, 42, 0))):
        w, h = 220, 140
        base = 1.2 + 0.6 * k
        nz = K.noise(w, h, 10, 950 + k) * 0.3
        tt = base + 1.6 * glow[sy:sy + h, sx:sx + w] + nz
        sheet = K.ramp_rgba('I', np.clip(tt, 0, 6), np.full((h, w), 255, np.uint8), seed=950 + k)
        d.a[sy:sy + h, sx:sx + w] = sheet
        d.rect(sx, sy, w, 1, C('S', 0))
        # the typed weighbill under the carbon: faint lighter lines
        for r in range(9):
            if r in (6, 7):
                continue
            d.scribble(sx + 12, sy + 14 + r * 12, w - 40, C('I', 6), seed=960 + k * 10 + r, rag=0.4)
        d.text('НАКЛАДНАЯ', sx + 12, sy + 4, C('S', 1))
        # the pressure trace of the cut-out signature, visible as a light relief
        sig_y = sy + 96
        m = K.text_mask('Ю. АРХИПОВ')
        m = np.kron(m, np.ones((2, 2), bool))
        mh, mw = m.shape
        sxx = sx + 70
        for yy_ in range(mh):
            for xx_ in range(mw):
                if m[yy_, xx_]:
                    d.px(sxx + xx_ + yy_ // 3, sig_y + yy_, C('S', 2 + (k == 2)))
                    d.px(sxx + xx_ + yy_ // 3 + 1, sig_y + yy_ + 1, C('N', 1))
        d.line(sxx - 6, sig_y + mh + 3, sxx + mw + 14, sig_y + mh + 1, C('S', 1))      # the flourish
        d.text('ПОЛКОВНИК - ТРАНСП. ОТД.', sx + 60, sig_y + mh + 7, C('S', 0))
        if k == 2:
            marks['signature'] = {'rect': [sxx - 6, sig_y - 2, mw + 24, mh + 16],
                                  'text': 'Ju. Archipov, Oberst, Transportabteilung (Druckspur)'}
    d.save('karsk_tunnels_carbon')
    return {'id': 'karsk_tunnels_carbon', 'item_id': 'ev_c4_carbon', 'objective': 'c4a_inspect_carbon',
            'hotspot': 'lamp_table', 'size': [d.w, d.h], 'marks': marks,
            'describes': 'Three carbon copies of freight bills fanned on the glowing glass of the light box. Where '
                         'the signature was cut out of the original, the carbon keeps the pressure of the pen: '
                         'light against the lamp, three times the same hand, Ю. АРХИПОВ, полковник, transport '
                         'department.'}


# =========================================================================== the 1941 plan on linen
def tunnel_plan():
    d = Doc(320, 200)
    desk_bg(d, 971)
    x0, y0, w, h = 10, 12, 300, 176
    d.rect(x0 + 3, y0 + 3, w, h, C('N', 0))
    d.paper(x0, y0, w, h, seed=972, base=3.9)
    for yy in range(y0, y0 + h, 2):                                               # linen weave
        for xx in range(x0 + (yy // 2) % 2, x0 + w, 3):
            if d.rng.random() < 0.18:
                d.px(xx, yy, C('P', 3))
    d.text('СЛУЖЕБНЫЙ ТОННЕЛЬ № 3 - МПВО - 1941', x0 + w // 2, y0 + 6, INK, center=True)
    d.rect(x0 + 8, y0 + 14, w - 16, 1, INK2)
    # the freight yard above: many parallel tracks
    for k in range(6):
        ty = y0 + 30 + k * 7
        d.rect(x0 + 18, ty, w - 40, 1, C('I', 3))
        for xx in range(x0 + 18, x0 + w - 22, 6):
            d.px(xx, ty - 1, C('I', 4))
    d.text('ГРУЗОВОЙ ДВОР', x0 + 26, y0 + 22, INK2)
    # the freight office (with the shelter cellar) at the left, the tunnel under the yard, the siding at the end
    d.rect(x0 + 14, y0 + 84, 40, 30, C('I', 3))
    d.rect(x0 + 16, y0 + 86, 36, 26, C('P', 4))
    d.text('КОНТОРА', x0 + 34, y0 + 92, INK, center=True)
    d.text('УБЕЖИЩЕ', x0 + 34, y0 + 102, RED, center=True)
    tun = [(x0 + 54, y0 + 104), (x0 + 120, y0 + 104), (x0 + 160, y0 + 118), (x0 + 236, y0 + 118),
           (x0 + 262, y0 + 132)]
    for (a, b) in zip(tun[:-1], tun[1:]):
        for o in (-3, 3):
            d.line(a[0], a[1] + o, b[0], b[1] + o, INK)
    d.text('Т-3', x0 + 96, y0 + 94, INK)
    # the track without a number at the end
    d.rect(x0 + 252, y0 + 128, 40, 9, C('P', 3))
    d.rect(x0 + 252, y0 + 128, 40, 1, INK)
    d.rect(x0 + 252, y0 + 136, 40, 1, INK)
    d.text('ПУТЬ —', x0 + 256, y0 + 141, INK)
    # the pencil trace along the route + a circle around the end
    rng = np.random.default_rng(973)
    for (a, b) in zip(tun[:-1], tun[1:]):
        for (x, y) in K.bres(a[0], a[1], b[0], b[1]):
            if rng.random() < 0.85:
                d.px(x, y + int(rng.integers(-1, 1)), PENCIL)
    for ang in np.linspace(0, 2 * math.pi, 90):
        d.px(int(round(x0 + 272 + 26 * math.cos(ang))), int(round(y0 + 134 + 14 * math.sin(ang))), PENCIL)
    # north arrow, scale bar, the 1941 stamp
    d.line(x0 + 280, y0 + 40, x0 + 280, y0 + 24, INK)
    d.text('С', x0 + 278, y0 + 18, INK)
    d.rect(x0 + 18, y0 + h - 14, 60, 2, INK)
    d.text('100 М', x0 + 84, y0 + h - 16, INK2)
    d.stamp('МПВО', x0 + 210, y0 + h - 34, C('R', 1), scale=2, seed=974)
    d.save('karsk_tunnels_plan')
    return {'id': 'karsk_tunnels_plan', 'item_id': 'ev_c4_tunnel_plan', 'objective': 'c4a_talk_tunnel',
            'hotspot': 'lev_cellar', 'size': [d.w, d.h],
            'marks': {'route': {'rect': [x0 + 54, y0 + 96, 216, 44], 'text': 'Dienststollen 3, mit Bleistift nachgezogen'},
                      'end': {'rect': [x0 + 246, y0 + 120, 54, 30], 'text': 'Gleis ohne Nummer'}},
            'describes': 'An air-raid plan of 1941 on linen: service tunnel No. 3 runs from the freight office '
                         'cellar (shelter) under the whole freight yard and ends at a track without a number; '
                         'someone has traced the route in pencil and circled the end.'}


# =========================================================================== behind the iron door
def fresh_tracks():
    d = Doc(240, 160)
    nz = K.noise(240, 160, 8, 981) * 0.5
    yy, xx = np.mgrid[0:160, 0:240].astype(np.float32)
    t = 1.8 + nz + (yy / 160.0) * 0.8
    d.a[:] = K.ramp_rgba('C', np.clip(t, 0, 7), np.full((160, 240), 255, np.uint8), seed=981)
    # two rails converging into the dark, the tops polished bright
    for side in (-1, 1):
        for y in range(40, 160):
            k = (y - 40) / 120.0
            x = int(round(120 + side * (12 + 70 * k)))
            wdt = 2 + int(5 * k)
            d.rect(x - wdt // 2, y, wdt, 1, C('I', 2))
            d.rect(x - wdt // 2, y, max(1, wdt // 2), 1, C('S', 4 + (k > 0.5)))
    d.rect(0, 0, 240, 40, C('N', 0))
    for y in range(40, 52):
        d.rect(0, y, 240, 1, C('N', 1 if y < 46 else 2))
    # sleepers, the dust beside the rails trodden (footprints), clean where the boots went
    for k in range(8):
        y = 56 + int(14 * k * (1 + k * 0.12))
        if y >= 160:
            break
        half = int(18 + 70 * (y - 40) / 120.0)
        d.rect(120 - half, y, 2 * half, 2 + k // 3, C('I', 1))
    rng = np.random.default_rng(982)
    for k in range(18):
        fx = int(rng.integers(30, 210))
        fy = int(rng.integers(70, 150))
        s = 1 + (fy - 60) // 40
        d.rect(fx, fy, 4 * s, 2 * s, C('C', 1))
        d.rect(fx + s, fy, 2 * s, 1, C('C', 0))
    # the threshold of the door + a drop of red-brown paint, still soft
    d.rect(0, 148, 240, 12, C('I', 3))
    d.rect(0, 148, 240, 1, C('S', 2))
    for yy in range(150, 156):
        for xx_ in range(146, 156):
            if (xx_ - 150.5) ** 2 / 20.0 + (yy - 153) ** 2 / 6.0 <= 1.0:
                d.px(xx_, yy, C('V', 3))
    d.rect(148, 152, 4, 1, C('V', 5))
    d.px(149, 151, C('R', 3))
    d.px(157, 154, C('V', 3))
    d.save('karsk_tunnels_tracks')
    return {'id': 'karsk_tunnels_tracks', 'item_id': 'ev_c4_fresh_tracks', 'objective': 'c4a_open_door',
            'hotspot': 'tunnel_door', 'size': [d.w, d.h],
            'marks': {'rails': {'rect': [40, 40, 160, 120], 'text': 'blank gefahrene Schienen'},
                      'paint': {'rect': [146, 149, 10, 7], 'text': 'ein Tropfen rotbraune Farbe, noch weich'}},
            'describes': 'Behind the iron door: the rails of the tunnel run into the dark, their tops polished '
                         'bright; the dust beside them is trodden by many boots; on the steel threshold a drop of '
                         'red-brown paint, still soft.'}


# =========================================================================== card No. 0417, Russian half
PERF = {'pitch': 6, 'hole': 3, 'first_y': 8, 'count': 15}       # shared with the German half (mirrored)


def card_ru():
    d = Doc(240, 160)
    desk_bg(d, 991)
    cx0, cy0, cw, ch = 46, 24, 152, 104
    d.rect(cx0 + 3, cy0 + 3, cw, ch, C('N', 0))
    d.paper(cx0, cy0, cw, ch, seed=992, base=4.3)
    # perforated left edge (torn along the holes): half-holes + paper fibres
    for i in range(PERF['count']):
        hy = cy0 + PERF['first_y'] + i * PERF['pitch']
        for yy in range(PERF['hole']):
            d.px(cx0, hy + yy, C('D', 1))
            d.px(cx0 + 1, hy + yy, C('D', 1) if yy == 1 else C('P', 2))
        d.px(cx0, hy - 2, C('P', 5))
    marks = {}
    d.text('№ 0417', cx0 + cw - 40, cy0 + 6, INK)
    marks['number'] = {'rect': [cx0 + cw - 42, cy0 + 4, 36, 9], 'text': 'Nr. 0417'}
    d.text('УЧЁТНАЯ КАРТОЧКА', cx0 + 10, cy0 + 6, INK2)
    d.rect(cx0 + 8, cy0 + 14, cw - 16, 1, INK2)
    lines = [('ФАМИЛИЯ', 'КОВАЛЕНКО'), ('ИМЯ, ОТЧ.', 'АННА ПЕТРОВНА'), ('РОД.', '1926, ХАРЬКОВ'),
             ('1942', 'ВЫВЕЗЕНА В ГЕРМАНИЮ'), ('ОТМЕТКА', 'ВОЗВРАЩЕНКА'), ('ДАЛЕЕ', 'ФИЛЬТР. ПУНКТ КАРСК')]
    for i, (k, v) in enumerate(lines):
        ly = cy0 + 20 + i * 11
        d.text(k, cx0 + 10, ly, INK2)
        d.text(v, cx0 + 50, ly, INK)
        d.rect(cx0 + 48, ly + 7, cw - 58, 1, C('P', 2))
    marks['name'] = {'rect': [cx0 + 48, cy0 + 18, 100, 30], 'text': 'Kowalenko, Anna Petrowna, 1926, Charkow'}
    marks['next'] = {'rect': [cx0 + 48, cy0 + 73, 100, 9], 'text': 'Weiter: Filtrationspunkt Karsk'}
    sh = d.stamp('ПРИНЯТЬ', cx0 + 74, cy0 + 84, C('R', 2), scale=2, seed=993, holes=0.12)
    marks['stamp'] = {'rect': [cx0 + 74, cy0 + 84, int(sh[1]), int(sh[0])], 'text': 'Stempel „ПРИНЯТЬ“'}
    d.text('C-17/45', cx0 + 12, cy0 + 92, RED)
    marks['run'] = {'rect': [cx0 + 10, cy0 + 90, 30, 9], 'text': 'C-17/45'}
    d.save('karsk_tunnels_card_ru')
    return {'id': 'karsk_tunnels_card_ru', 'item_id': 'ev_c4_card_ru', 'objective': 'c4c_inspect_card',
            'hotspot': 'office_desk', 'size': [d.w, d.h], 'marks': marks,
            'card': {'rect': [cx0, cy0, cw, ch], 'perforation': dict(PERF, edge='left')},
            'describes': 'The Russian half of registry card No. 0417, perforated along its left edge: Kovalenko, '
                         'Anna Petrovna, 1926, Kharkov; 1942 taken to Germany; returnee; next: filtration point '
                         'Karsk. Run C-17/45, the stamp ПРИНЯТЬ in red.'}


# =========================================================================== the stencil board
def stencils():
    d = Doc(240, 160)
    nz = K.noise(240, 160, 10, 1001) * 0.4
    d.a[:] = K.ramp_rgba('D', np.clip(2.6 + nz, 0, 7), np.full((160, 240), 255, np.uint8), seed=1001)
    rng = np.random.default_rng(1002)
    for _ in range(260):
        d.px(int(rng.integers(0, 240)), int(rng.integers(0, 160)), C('V', int(rng.integers(2, 5))))
    marks = {}
    for i, num in enumerate(['41', '42', '43', '44', '45']):
        sx, sy = 12, 10 + i * 28
        wet = num == '45'
        d.rect(sx, sy, 132, 22, C('I', 5 if wet else 4))
        d.rect(sx, sy, 132, 1, C('S', 1))
        d.rect(sx, sy + 21, 132, 1, C('I', 2))
        d.px(sx + 66, sy - 2, C('S', 2))
        m = np.kron(K.text_mask('C-17/' + num, '57s'), np.ones((2, 2), bool))
        mh, mw = m.shape
        tx, ty = sx + (132 - mw) // 2, sy + 4
        for yy in range(mh):
            for xx in range(mw):
                if m[yy, xx]:
                    d.px(tx + xx, ty + yy, C('V', 5) if wet else C('D', 1))
        if wet:
            for k in range(0, mw, 5):
                if m[mh - 1, k]:
                    for j in range(2 + k % 4):
                        d.px(tx + k, ty + mh + j, C('V', 4))
            d.rect(sx + 4, sy + 3, 2, 14, C('S', 3))                                     # wet sheen
            marks['wet'] = {'rect': [sx, sy, 132, 22], 'text': 'C-17/45, noch nass'}
        else:
            for _ in range(24):
                d.px(sx + int(rng.integers(0, 132)), sy + int(rng.integers(0, 22)), C('V', 3))
    marks['runs'] = {'rect': [12, 10, 132, 106], 'text': 'C-17/41 bis /44, abgegriffen'}
    # letter stencils in two alphabets
    for r, letters in enumerate(['АБВГД', 'ABCDE']):
        for c, ch in enumerate(letters):
            lx, ly = 156 + c * 15, 12 + r * 24
            d.rect(lx, ly, 13, 19, C('I', 4))
            m = np.kron(K.text_mask(ch)[:, :3], np.ones((3, 3), bool))
            d.mask(m, lx + 2, ly + 2, C('D', 1))
    marks['alphabets'] = {'rect': [156, 12, 75, 43], 'text': 'Schablonen in zwei Alphabeten'}
    # the bucket of red-brown in the corner
    for y in range(110, 160):
        k = (y - 110) / 50.0
        half = int(34 - 4 * k)
        d.rect(190 - half, y, 2 * half, 1, C('I', 3 + (y % 6 == 0)))
    d.rect(158, 110, 64, 6, C('V', 3))
    d.rect(170, 111, 18, 2, C('V', 5))
    d.line(204, 112, 226, 70, C('D', 4))
    marks['bucket'] = {'rect': [156, 108, 68, 52], 'text': 'Rotbraun, die Farbe aller Güterwagen'}
    d.save('karsk_tunnels_stencils')
    return {'id': 'karsk_tunnels_stencils', 'item_id': 'ev_c4_stencils', 'objective': 'c4c_inspect_stencils',
            'hotspot': 'paint_stand', 'size': [d.w, d.h], 'marks': marks,
            'describes': 'Tin stencils on the paint stand, sorted by run: C-17/41 to /44 worn and crusted, '
                         'C-17/45 still wet; letter stencils in two alphabets; a bucket of red-brown.'}


# =========================================================================== inside wagon 24 318
def wagon_inside():
    d = Doc(300, 180)
    # raw planks (horizontal), dim light through the stove hole in the roof
    for y in range(0, 180, 9):
        t = 1.6 + (y // 9 % 3) * 0.3
        nz = K.noise(300, 9, 8, 1010 + y) * 0.4
        d.a[y:y + 9] = K.ramp_rgba('D', np.clip(t + nz, 0, 7), np.full((9, 300), 255, np.uint8), seed=y)
        d.rect(0, y + 8, 300, 1, C('N', 0))
    yy, xx = np.mgrid[0:180, 0:300].astype(np.float32)
    beam = np.clip(1 - np.abs(xx - (151 + (yy * 0.3))) / (12.0 + yy * 0.12), 0, 1) * np.clip(1 - yy / 200.0, 0.1, 1)
    thr = K.pg.bayer(300, 180, 0, 0, 4)
    m = beam * 0.8 > thr
    d.a[m] = K.ramp_rgba('C', np.full((180, 300), 3.0, np.float32), np.full((180, 300), 255, np.uint8))[m]
    d.rect(140, 0, 22, 6, C('S', 3))                                                 # the stove hole, sky
    d.rect(138, 6, 26, 2, C('N', 0))
    # two benches of raw boards, a bucket
    for (by, bx0, bx1) in ((120, 10, 130), (128, 170, 296)):
        d.rect(bx0, by, bx1 - bx0, 6, C('D', 5))
        d.rect(bx0, by + 6, bx1 - bx0, 2, C('D', 2))
        for lx in (bx0 + 6, bx1 - 10):
            d.rect(lx, by + 8, 4, 40, C('D', 3))
    for y in range(140, 170):
        k = (y - 140) / 30.0
        d.rect(140 - int(12 - 3 * k), y, 2 * int(12 - 3 * k), 1, C('I', 3 + (y == 140)))
    # scratches in the planks: names in two scripts (illegible), a date, below "Wir sind vierzehn"
    rng = np.random.default_rng(1011)
    for k in range(14):
        sx = 18 + (k % 5) * 54 + int(rng.integers(-4, 5))
        sy = 26 + (k // 5) * 18 + int(rng.integers(-2, 3))
        wl = int(rng.integers(14, 30))
        for x in range(sx, sx + wl):
            if rng.random() < 0.75:
                d.px(x, sy + int(rng.integers(-1, 2)), C('P', 4))
            if rng.random() < 0.3:
                d.px(x, sy - 2 + int(rng.integers(0, 2)), C('P', 3))
    d.text('21.1.', 236, 84, C('P', 4), scale=2)
    d.text('WIR SIND 14', 62, 92, C('P', 4))
    d.text('НАС 14', 62, 100, C('P', 3))
    d.save('karsk_tunnels_wagon_inside')
    return {'id': 'karsk_tunnels_wagon_inside', 'item_id': 'ev_c4_wagon_inside', 'objective': 'c4c_inspect_wagon',
            'hotspot': 'wagon_door', 'size': [d.w, d.h],
            'marks': {'date': {'rect': [234, 82, 30, 12], 'text': '21.1.'},
                      'fourteen': {'rect': [60, 90, 50, 16], 'text': 'Wir sind vierzehn.'}},
            'describes': 'Inside wagon 24 318: two benches of raw boards, a stove hole in the roof with grey light '
                         'falling in, a bucket. Scratched into the planks: names in two scripts (illegible here), '
                         'a date 21.1., and below, smaller: WIR SIND 14 / НАС 14.'}


# =========================================================================== the gap in the shelf
def book_gap():
    d = Doc(240, 160)
    desk_bg(d, 1021)
    rng = np.random.default_rng(1022)
    cols = [('G', 2), ('R', 1), ('D', 3), ('I', 3), ('K', 3), ('G', 3)]
    for (by, ytop) in ((62, 4), (150, 92)):
        d.rect(0, by, 240, 6, C('D', 4))
        d.rect(0, by + 6, 240, 2, C('D', 1))
        x = 6
        while x < 236:
            if by == 150 and 92 <= x < 152:
                x = 152
                continue
            bw = int(rng.integers(13, 19))
            ramp, i = cols[int(rng.integers(0, len(cols)))]
            d.rect(x, ytop, bw, by - ytop, C(ramp, i))
            d.rect(x, ytop, 2, by - ytop, C(ramp, min(i + 1, 5)))
            d.rect(x + 3, ytop + 10, bw - 6, 14, C('P', 3))
            d.scribble(x + 4, ytop + 15, bw - 8, C('I', 1), seed=int(rng.integers(0, 999)), rows=2, gap=4)
            x += bw + 1
    # the gap: three volumes missing, clean board in the dust, the leaning neighbour, Lev's slip
    d.rect(92, 92, 60, 58, C('N', 1))
    d.rect(92, 148, 60, 2, C('D', 5))
    for k in range(3):
        d.rect(94 + k * 20, 149, 18, 1, C('D', 6))
    for i in range(50):
        d.rect(78 + i // 4, 150 - i, 14, 1, C('G', 2))
    d.rect(102, 134, 44, 14, C('P', 5))
    d.rect(102, 147, 44, 1, C('P', 2))
    d.text('У Л.С. –', 105, 135, C('I', 2))
    d.text('НА ПРОСМ.', 105, 141, C('I', 2))
    d.save('karsk_tunnels_book_gap')
    return {'id': 'karsk_tunnels_book_gap', 'item_id': 'ev_c4_book_gap', 'objective': 'c4a_inspect_shelf',
            'hotspot': 'book_shelf', 'size': [d.w, d.h],
            'marks': {'gap': {'rect': [92, 92, 60, 58], 'text': 'drei Bände fehlen: Januar 1964, I–III'},
                      'slip': {'rect': [102, 134, 44, 14], 'text': 'Bei L. S. – zur Durchsicht.'}},
            'describes': 'The freight book shelf: three volumes missing (January 1964, decades I–III); the board '
                         'is clean where they stood, the neighbour leans into the gap; on the board a slip in '
                         'Lev\'s hand, У Л. С. – на просмотр.'}


ALT = {   # German caption lines (data/locale/de_env_karsk_tunnels.json)
    'karsk_tunnels_book_gap': 'Das Regal der Frachtbücher: drei Bände fehlen – Januar 1964, erste bis dritte Dekade. '
                              'Auf dem leeren Brett ein Zettel in Levs Schrift: „У Л. С. – на просмотр“ (Bei L. S. – '
                              'zur Durchsicht).',
    'karsk_tunnels_freight_book': 'Das Frachtbuch Januar 1964. Am 14., 21. und 28. Januar – C-17/41, /42, /43 nach '
                                  'Kordon-17 – ist in der Spalte „Разрешил“ (Genehmigt) die Unterschrift sauber '
                                  'herausgeschnitten. Daneben jedes Mal: „Отд. Т – устно“ (Abt. T – mündlich).',
    'karsk_tunnels_carbon': 'Drei Durchschläge gegen die Lampe. Wo oben die Unterschrift fehlt, hat der Stift sich '
                            'durchgedrückt: „Ю. Архипов, полковник“ – Ju. Archipov, Oberst, Transportabteilung. '
                            'Dreimal dieselbe Hand.',
    'karsk_tunnels_plan': 'Luftschutzplan von 1941, auf Leinen: Dienststollen 3 führt vom Keller der Güterabfertigung '
                          'unter dem ganzen Güterbahnhof hindurch und endet an einem Gleis ohne Nummer. Jemand hat '
                          'den Weg mit Bleistift nachgezogen.',
    'karsk_tunnels_tracks': 'Hinter der Eisentür: Die Schienen sind blank gefahren, der Staub daneben ist zertreten. '
                            'Auf der Schwelle ein Tropfen rotbraune Farbe, noch weich.',
    'karsk_tunnels_card_ru': 'Karteikarte Nr. 0417, russische Hälfte: „Коваленко Анна Петровна, 1926, Харьков“ – '
                             '1942 nach Deutschland verbracht, Rückkehrerin, weiter: Filtrationspunkt Karsk. Stempel '
                             '„Принять“ (annehmen). Links die Perforation.',
    'karsk_tunnels_stencils': 'Blechschablonen nach Läufen sortiert: C-17/41 bis /44 abgegriffen, C-17/45 noch nass. '
                              'Daneben Buchstaben in zwei Alphabeten und ein Kübel Rotbraun.',
    'karsk_tunnels_wagon_inside': 'Im Wagen 24 318: zwei Bänke aus rohen Brettern, ein Ofenloch im Dach, ein Eimer. In '
                                  'die Bretter geritzt Namen in zwei Schriften, ein Datum – 21.1. Darunter, kleiner: '
                                  '„Wir sind vierzehn.“',
}


def build_all():
    os.makedirs(DOCS, exist_ok=True)
    entries = [book_gap(), freight_book(), carbon(), tunnel_plan(), fresh_tracks(), card_ru(), stencils(),
               wagon_inside()]
    docs = []
    for e in entries:
        doc = {'file': 'res://assets/ui/documents/%s.png' % e['id'], 'size': e['size'], 'display_scale': 3,
               'id': e['id'], 'alt_key': 'doc.%s.alt' % e['id'], 'item_id': e['item_id'],
               'objective': e['objective'], 'hotspot': e['hotspot'],
               'title_key': 'item.%s.name' % e['item_id'][3:], 'description_key': 'item.%s.description' % e['item_id'][3:],
               'describes': e['describes'], 'marks': e['marks']}
        if 'card' in e:
            doc['card'] = e['card']
        docs.append(doc)
        img = np.asarray(Image.open(os.path.join(DOCS, e['id'] + '.png')))
        n, bad = K.palette_report(img)
        if bad:
            print('  WARNING %s: non-palette colours %s' % (e['id'], bad[:4]))
    meta = {'scene': 'L_C4_TunnelsA / L_C4_TunnelsB', 'palette': 'tunnels',
            'generator': 'tools/pixelgen/env_c4_tunnels_docs.py', 'date': K.DATE,
            'note': 'Pixel art drawn 1:1, shown at 3x (nearest). Only the story-critical figures are legible; the UI '
                    'shows the item name/description as HD text and the alt text (data/locale/de_env_karsk_tunnels'
                    '.json) as the German caption line. All rects are [x, y, w, h] in document pixels. The card '
                    'perforation (pitch 6, hole 3, first hole 8 px below the top edge, 15 holes) is the shared '
                    'contract of both halves of card No. 0417 (German half: berlin_annex, mirrored on its right edge).',
            'documents': docs}
    with open(os.path.join(DOCS, 'karsk_tunnels_documents.json'), 'w', encoding='utf-8', newline=LF) as f:
        json.dump(meta, f, indent=1, ensure_ascii=False)
    loc = {'locale': 'de', 'area': 'karsk_tunnels', 'strings': {'doc.%s.alt' % k: v for k, v in ALT.items()}}
    with open(os.path.join(ROOT, 'data', 'locale', 'de_env_karsk_tunnels.json'), 'w', encoding='utf-8',
              newline=LF) as f:
        json.dump(loc, f, indent=1, ensure_ascii=False)
    print('[env_c4_tunnels_docs] %d documents' % len(docs))
    return docs


if __name__ == '__main__':
    build_all()
