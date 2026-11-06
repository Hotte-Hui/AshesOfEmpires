"""env_c4p2_karsk_docs -- inspect close-ups of Chapter 4 part 2, Karsk (documentation/C4P2_DESIGN.md 2.5).

Run:  py -3 -P tools/pixelgen/env_c4p2_karsk_docs.py        (deterministic, no network)

Writes assets/ui/documents/karsk_c4p2_*.png + karsk_c4p2_documents.json (InspectView metadata: item -> image, alt
text key, marks) and the German alt texts data/locale/de_env_karsk_c4p2.json.  Drawn 1:1, shown at 3x; only the
story-critical lines are legible, everything else is typed scribble -- the UI shows the item name and description as
HD text.  Palette 'depot' (env_c4p2_karsk_kit.DEPOT).
* the special order: a violet carbon on thin paper on Irina's sill, the depot stamp, her pencil „Кто?“;
* the work list of Kolonne 4 under yellowed cellophane: eleven numbered lines, the names blurred (no real persons,
  no list to read like a monument), the three pencil notes legible -- 11 + 3 = 14;
* the press notice with the depot stamp, the line „Колонна 4 … за брезентом“ underlined in pencil;
* Ekdahl's 1938 Swedish guidebook open at page 212 (original design, no real publisher): the German half of card
  0417 laid in upside down, Konrad's tracing of the Kordon room on onion-skin, its flap folded back on the block
  letters „MOROZOV – 0417 – DI 23.40 – TÜR OST“;
* card 0417, the Russian half (the original from the box): notches on its left edge (the perforation contract of
  part 1: pitch 6, hole 3, first hole 8 px below the top, 15 holes), the right half of the round stamp „C-17“ with
  Cyrillic letters;
* card 0417 whole under the green lamp: teeth in notches, the stamp closed -- German letters left, Cyrillic right.
No real person is named; the names of the list stay illegible.
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
import env_c4p2_karsk_kit as K  # noqa: E402

ROOT = K.ROOT
DOCS = os.path.join(ROOT, 'assets', 'ui', 'documents')
LOCALE = os.path.join(ROOT, 'data', 'locale', 'de_env_karsk_c4p2.json')
LF = chr(10)
PRODUCED: list = []


def C(ramp, i, a=255):
    return K.rgba(ramp, int(round(i)), a)


class Doc:
    def __init__(self, w, h, bg=('N', 1)):
        self.w, self.h = w, h
        self.a = np.zeros((h, w, 4), np.uint8)
        self.a[:] = C(*bg)

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
        ys, xs = np.nonzero(m)
        for yy, xx in zip(ys, xs):
            self.px(x + xx, y + yy, col)

    def text(self, s, x, y, col, font='35', center=False, rot180=False, jitter=None):
        m = K.text_mask(s, font, overhang=font in ('35', '57'))       # Й with its breve, distinct umlauts
        oh = m.shape[0] - (5 if font == '35' else 7)
        if rot180:
            m = m[::-1, ::-1]
        else:
            y -= oh                                           # the marks stand above the cap line
        if center:
            x = int(round(x - m.shape[1] / 2))
        if jitter is not None:                                # handwriting: the baseline wanders a little
            rng = np.random.default_rng(jitter)
            off = 0
            for cx in range(m.shape[1]):
                if cx % 8 == 0:
                    off = (1 if rng.random() < 0.3 else 0) if rng.random() < 0.5 else off
                col_m = m[:, cx]
                for cy in np.nonzero(col_m)[0]:
                    self.px(x + cx, y + cy + off, col)
            return m.shape[1]
        self.mask(m, x, y, col)
        return m.shape[1]

    def scribble(self, x, y, w, rows, col, seed=0, gap=4, rag=0.3):
        rng = np.random.default_rng(seed)
        for r in range(rows):
            xx = x
            end = x + w - int(rng.random() * w * rag)
            while xx < end:
                wl = int(rng.integers(2, 7))
                for k in range(min(wl, end - xx)):
                    if rng.random() < 0.8:
                        self.px(xx + k, y + r * gap + (1 if rng.random() < 0.25 else 0), col)
                xx += wl + 2

    def noise(self, x, y, w, h, ramp, base, amp, seed, cell=3.0):
        n = K.nz(w, h, cell, seed)
        t = base + n * amp * 2
        rgba = K.ramp_rgba(ramp, np.clip(t, 0, K.R.n(ramp) - 1), np.full((h, w), 255, np.uint8), seed=seed, x0=x,
                           y0=y)
        x0, y0, x1, y1 = max(0, x), max(0, y), min(self.w, x + w), min(self.h, y + h)
        self.a[y0:y1, x0:x1] = rgba[y0 - y:y1 - y, x0 - x:x1 - x]

    def light(self, cx, cy, r, k=1.0):
        """Brighten toward a lamp (one palette step per ring, dithered)."""
        ys, xs = np.mgrid[0:self.h, 0:self.w].astype(np.float32)
        f = np.clip(1 - np.hypot(xs - cx, ys - cy) / r, 0, 1) * k
        thr = K.pg.bayer(self.w, self.h, 0, 0, 4)
        step = (f > thr * 0.9 + 0.1)
        rgb = self.a[..., :3].astype(np.int32)
        lifted = np.clip(rgb * 1.18 + 10, 0, 255)
        out = np.where(step[..., None], lifted, rgb)
        self.a[..., :3] = K.snap(out.astype(np.uint8))

    def save(self, name, desc):
        p = os.path.join(DOCS, name + '.png')
        os.makedirs(DOCS, exist_ok=True)
        Image.fromarray(self.a, 'RGBA').save(p)
        PRODUCED.append((os.path.relpath(p, ROOT).replace('\\', '/'), desc))


def wood(d, x, y, w, h, seed, base=3.0, ramp='D'):
    n1 = K.nz(w, h, 2, seed)
    from PIL import Image as _I
    g = K.nz(max(2, w // 8), max(2, h), 2, seed + 1)
    img = _I.fromarray(((g + 0.5) * 255).astype(np.uint8)).resize((w, h), _I.BILINEAR)
    gg = np.asarray(img, np.float32) / 255.0 - 0.5
    t = base + gg * 1.2 + n1 * 0.3
    rgba = K.ramp_rgba(ramp, np.clip(t, 0, K.R.n(ramp) - 1), np.full((h, w), 255, np.uint8), seed=seed)
    d.a[y:y + h, x:x + w] = rgba[:min(h, d.h - y), :min(w, d.w - x)]


def stamp_round(d, cx, cy, r, col, top_text='', bottom_text='', center='', faded=0.25, seed=0):
    rng = np.random.default_rng(seed)
    for k in range(int(2 * math.pi * r * 1.6)):
        ang = k / (r * 1.6)
        for rr in (r, r - 1):
            if rng.random() > faded:
                d.px(int(round(cx + rr * math.cos(ang))), int(round(cy + rr * math.sin(ang))), col)
    if center:
        d.text(center, cx, cy - 2, col, center=True)


def stamp_ring_letters(d, cx, cy, r, letters, a0, a1, col):
    """Upright 3x5 letters set round an arc (angles in radians, screen coords)."""
    n = len(letters)
    for i, ch in enumerate(letters):
        ang = a0 + (a1 - a0) * (i + 0.5) / n
        x = int(round(cx + r * math.cos(ang))) - 1
        y = int(round(cy + r * math.sin(ang))) - 2
        d.text(ch, x, y, col)


# =========================================================================== card 0417 (both halves, compact)
TEETH = dict(pitch=6, hole=3, first=8, n=15)


def card_half_de(d, x, y, w=148, h=104, upside_down=False):
    """The German (left) half: header, red tab, the lines of the Lindner file, teeth on the right edge."""
    paper, ink, red = C('P', 5), C('U', 2), C('R', 3)
    tmp = Doc(w + 4, h, bg=('N', 0))
    tmp.a[:] = 0
    tmp.rect(0, 0, w, h, paper)
    tmp.noise(0, 0, w, h, 'P', 4.6, 0.35, 711, cell=4)
    for k in range(TEETH['n']):                                        # teeth: tabs out on the right edge
        ty = TEETH['first'] + k * TEETH['pitch']
        tmp.rect(w, ty, 3, TEETH['hole'], paper)
    tmp.rect(w - 22, 0, 18, 7, red)                                    # the red C-17 tab
    tmp.text('C-17', w - 13, 1, C('P', 6), center=True)
    tmp.text('NR. 0417', 6, 5, ink)
    tmp.rect(4, 12, w - 10, 1, C('U', 3))
    rows = ['LINDNER, ANNA', 'GEB. KOWALENKO', '* 1926 CHARKOW', 'VERMERK C-17: RÜCKF. OST',
            'ABGABE KORDON-17, TÜR OST', 'DI 18.2., 23.40']
    for i, s in enumerate(rows):
        yy = 17 + i * 10
        tmp.text(s, 6, yy, red if 'VERMERK' in s else ink)
        tmp.rect(4, yy + 7, w - 10, 1, C('P', 3))
    tmp.scribble(6, 80, w - 40, 2, C('U', 3), seed=712, gap=6)
    if upside_down:
        tmp.a = tmp.a[::-1, ::-1].copy()
    m = tmp.a[..., 3] > 0
    ys, xs = np.nonzero(m)
    for yy, xx in zip(ys, xs):
        d.px(x + xx - (4 if upside_down else 0), y + yy, tmp.a[yy, xx])


def card_half_ru(d, x, y, w=148, h=104):
    """The Russian (right) half: notches on the left edge, the registration lines, the stamp „ПРИНЯТЬ“."""
    paper, ink, red = C('P', 4), C('N', 1), C('R', 2)
    d.rect(x, y, w, h, paper)
    d.noise(x, y, w, h, 'P', 4.1, 0.35, 713, cell=4)
    for k in range(TEETH['n']):                                        # notches cut into the left edge
        ty = y + TEETH['first'] + k * TEETH['pitch']
        d.rect(x, ty, 3, TEETH['hole'], C('N', 0))
    d.text('УЧЕТНАЯ КАРТОЧКА', x + 8, y + 5, ink)
    d.text('№ 0417', x + w - 30, y + 5, ink)
    d.rect(x + 6, y + 12, w - 10, 1, ink)
    rows = [('ФАМИЛИЯ', 'КОВАЛЕНКО'), ('ИМЯ, ОТЧ.', 'АННА ПЕТР.'), ('РОД.', '1926, ХАРЬКОВ'), ('ОТМЕТКА', 'ВОЗВРАЩЕНКА'),
            ('ДАЛЕЕ', 'ФИЛЬТР. ПУНКТ КАРСК')]
    for i, (k_, v) in enumerate(rows):
        yy = y + 17 + i * 10
        d.text(k_, x + 8, yy, C('N', 2))
        d.text(v, x + 46, yy, ink)
        d.rect(x + 6, yy + 7, w - 10, 1, C('P', 2))
    d.rect(x + 44, y + 15, 1, 52, C('P', 2))
    d.text('С-17/45', x + 10, y + 86, red)
    d.rect(x + 66, y + 80, 52, 14, red)                                 # the stamp „ПРИНЯТЬ“
    d.rect(x + 67, y + 81, 50, 12, paper)
    d.text('ПРИНЯТЬ', x + 92, y + 85, red, center=True)


def stamp_c17(d, cx, cy, half=None):
    """The round stamp „C-17“ across the cut: German letters on the left arc, Cyrillic on the right.
    half = 'left' | 'right' | None (whole)."""
    col = C('U', 3)
    r = 19
    tmp = Doc(2 * r + 9, 2 * r + 9, bg=('N', 0))
    tmp.a[:] = 0
    c = r + 4
    stamp_round(tmp, c, c, r, col, faded=0.18, seed=721)
    stamp_round(tmp, c, c, r - 8, col, faded=0.3, seed=722)
    stamp_ring_letters(tmp, c, c, r - 4, 'KORDON', math.pi * 0.62, math.pi * 1.38, col)
    stamp_ring_letters(tmp, c, c, r - 4, 'КОРДОН', -math.pi * 0.38, math.pi * 0.38, col)
    tmp.text('C-17', c, c - 2, col, center=True)
    m = tmp.a[..., 3] > 0
    if half == 'left':
        m[:, c:] = False
    elif half == 'right':
        m[:, :c] = False
    ys, xs = np.nonzero(m)
    for yy, xx in zip(ys, xs):
        d.px(cx - c + xx, cy - c + yy, tmp.a[yy, xx])


# =========================================================================== the documents
def doc_order():
    d = Doc(300, 200, bg=('D', 2))
    wood(d, 0, 0, 300, 200, 731, base=2.6)                              # the sill
    d.rect(0, 0, 300, 18, C('L', 3))                                    # the window glass above it, lit
    d.rect(0, 16, 300, 3, C('D', 1))
    px, py, pw, ph = 30, 26, 236, 160
    d.rect(px + 3, py + 4, pw, ph, C('N', 1))                           # shadow
    d.rect(px, py, pw, ph, C('P', 4))
    d.noise(px, py, pw, ph, 'P', 3.9, 0.3, 732, cell=5)
    ink = C('O', 3)                                                     # violet carbon (Soviet copying paper)
    lines = ['ЛОКОМОТИВНОЕ ДЕПО КАРСК', 'НАРЯД № 45/С', '',
             'ДЕПО ВЫДЕЛЯЕТ НА СПЕЦРЕЙС С-17/45', 'ВО ВТОРНИК 18.2. ОДИН ЛОКОМОТИВ', 'И ОДНУ БРИГАДУ.', '',
             'С ПЕРЕСТАН. ПУТИ 19.40 МЕСТН. ВР.,', 'В КОРДОН-17 23.40 КОРИД. ВР.', 'ВАГОН 24 318. СОПРОВОЖД.: ОТД. Т',
             '', 'ПЕРСОНАЛ МОЛЧИТ.']
    y = py + 8
    for s in lines:
        if s:
            d.text(s, px + 10, y, ink)
        y += 9
    # a carbon copy prints unevenly: a share of the strokes comes out paler
    rng = np.random.default_rng(736)
    sub = d.a[py:py + ph, px:px + pw]
    is_ink = np.all(sub == ink, axis=-1)
    sub[is_ink & (rng.random(is_ink.shape) < 0.16)] = C('O', 4)
    d.scribble(px + 10, y + 2, 120, 2, C('O', 2), seed=733, gap=6)
    stamp_round(d, px + 190, py + 128, 17, C('O', 4), seed=734)        # the depot stamp, violet stamp ink
    d.text('ДЕПО', px + 190, py + 120, C('O', 4), center=True)
    d.text('КАРСК', px + 190, py + 128, C('O', 4), center=True)
    d.line(px + 150, py + 130, px + 176, py + 126, C('U', 2))           # a signature over the stamp
    d.line(px + 176, py + 126, px + 168, py + 134, C('U', 2))
    pencil = C('C', 1)
    d.text('КТО?', px + 24, py + 136, pencil, jitter=735)
    d.line(px + 20, py + 145, px + 46, py + 144, pencil)
    d.light(150, 10, 220, 0.5)
    marks = {
        'run': {'rect': [px + 8, py + 33, 210, 25], 'text': 'Sonderlauf C-17/45, Dienstag 18.2.: eine Lok, ein Personal'},
        'times': {'rect': [px + 8, py + 69, 220, 16], 'text': 'Ab Umsetzgleis 19.40 Uhr Ortszeit, an Kordon-17 23.40 Uhr Korridorzeit'},
        'wagon': {'rect': [px + 8, py + 87, 200, 7], 'text': 'Wagen 24 318. Begleitung: Abt. T'},
        'silent': {'rect': [px + 8, py + 105, 90, 7], 'text': 'Das Personal schweigt.'},
        'who': {'rect': [px + 18, py + 133, 32, 14], 'text': 'Irinas Bleistift: „Wer?“'},
    }
    d.save('karsk_c4p2_order', 'the special order C-17/45: a violet carbon on Irina\'s sill, the depot stamp, '
                               'her pencil „Кто?“')
    return marks


def doc_work_list():
    d = Doc(280, 200, bg=('D', 2))
    wood(d, 0, 0, 280, 200, 741, base=2.2)                              # the board on the post
    d.rect(124, 0, 32, 200, C('D', 1))
    px, py, pw, ph = 28, 18, 210, 168
    d.rect(px + 3, py + 3, pw, ph, C('N', 1))
    d.rect(px, py, pw, ph, C('P', 4))
    d.noise(px, py, pw, ph, 'P', 3.8, 0.35, 742, cell=6)
    ink = C('N', 1)
    d.text('КОЛОННА 4', px + 10, py + 8, ink)
    d.text('ПРИБЫТИЕ 22.1.1964', px + 10, py + 17, ink)
    d.text('ДО ОКОНЧАНИЯ ПРОВЕРКИ', px + 10, py + 26, ink)
    d.rect(px + 8, py + 34, 130, 1, ink)
    for i in range(11):
        yy = py + 40 + i * 10
        d.text('%d.' % (i + 1), px + 10, yy, ink)
        # the names: typed, then blurred under the scratched cellophane -- illegible on purpose
        rng = np.random.default_rng(750 + i)
        xx = px + 22
        for wl in (int(rng.integers(5, 9)), int(rng.integers(4, 8)), int(rng.integers(5, 10))):
            for k in range(wl * 4):
                if rng.random() < 0.7:
                    d.px(xx + k, yy + int(rng.integers(0, 5)), C('P', 2))
            xx += wl * 4 + 5
    # pencil notes in the margin (legible)
    pencil = C('C', 2)
    d.text('ЛЕНА, 4, И МИРОН, 6 –', px + 104, py + 46, pencil, jitter=761)
    d.text('ДЕТДОМ № 2', px + 116, py + 56, pencil, jitter=762)
    d.line(px + 100, py + 44, px + 100, py + 64, pencil)
    d.text('ВИЛЬГЕЛЬМ С. –', px + 108, py + 98, pencil, jitter=763)
    d.text('СПЕЦПОСЕЛЕНИЕ СЕВЕР', px + 100, py + 108, pencil, jitter=764)
    d.line(px + 96, py + 96, px + 96, py + 116, pencil)
    # yellowed cellophane over everything: a tint, wrinkles, highlights, a nail at each corner
    ys, xs = np.mgrid[0:d.h, 0:d.w]
    cel = (xs >= px - 6) & (xs < px + pw + 6) & (ys >= py - 6) & (ys < py + ph + 6)
    rgb = d.a[..., :3].astype(np.int32)
    tint = np.clip(rgb * 0.78 + np.array([224, 168, 90]) * 0.22, 0, 255)
    thr = K.pg.bayer(d.w, d.h, 0, 0, 4)
    m = cel & (thr < 0.55)
    rgb[m] = tint[m]
    d.a[..., :3] = K.snap(rgb.astype(np.uint8))
    rng = np.random.default_rng(765)
    for (x0, y0, x1, y1) in ((px + 10, py + 150, px + 120, py + 70), (px + 150, py + 160, px + 200, py + 40),
                             (px - 4, py + 90, px + 40, py + 30)):
        for (x, y) in K.bres(x0, y0, x1, y1):
            if rng.random() < 0.55:
                d.px(x, y, C('P', 6))
    for (nx, ny) in ((px - 3, py - 3), (px + pw + 2, py - 3), (px - 3, py + ph + 2), (px + pw + 2, py + ph + 2)):
        d.rect(nx - 1, ny - 1, 3, 3, C('I', 4))
    marks = {
        'head': {'rect': [px + 8, py + 6, 100, 26], 'text': 'Kolonne 4. Zugang 22.1.1964. Bis zum Abschluss der Prüfung.'},
        'names': {'rect': [px + 8, py + 38, 86, 112], 'text': 'Elf Namen, unter dem Zellophan unleserlich'},
        'children': {'rect': [px + 98, py + 42, 108, 22], 'text': '„Lena, 4, und Miron, 6 – Kinderheim Nr. 2“'},
        'wilhelm': {'rect': [px + 94, py + 94, 112, 22], 'text': '„Wilhelm S. – Sondersiedlung Nord“'},
    }
    d.save('karsk_c4p2_work_list', 'the work list of Kolonne 4 under yellowed cellophane: eleven names blurred, '
                                   'three pencil notes legible')
    return marks


def doc_press_notice():
    d = Doc(320, 210, bg=('D', 2))
    for k in range(0, 320, 16):                                         # the plank door
        wood(d, k, 0, 15, 210, 771 + k, base=2.4)
        d.rect(k + 15, 0, 1, 210, C('D', 0))
    px, py, pw, ph = 18, 20, 284, 170
    d.rect(px + 3, py + 3, pw, ph, C('N', 1))
    d.rect(px, py, pw, ph, C('P', 5))
    d.noise(px, py, pw, ph, 'P', 4.4, 0.3, 772, cell=6)
    ink = C('N', 1)
    d.text('ОБЪЯВЛЕНИЕ', px + pw // 2, py + 8, ink, center=True)
    d.rect(px + 100, py + 15, 84, 1, ink)
    lines = ['ВТОРНИК, 18.2., 17.30: ПОСЕЩЕНИЕ', 'ПРЕДСТАВИТЕЛЯ ШВЕДСКОЙ ПРЕССЫ.', '',
             'ПОКАЗАТЬ: ВОССТАНОВЛЕННЫЙ СИГНАЛ', 'ЛИНИИ (ИНЖ. А. МОРОЗОВ),', 'ОБРАЗЦОВУЮ БРИГАДУ, СТОЛОВУЮ.', '',
             'КОЛОННА 4 В ЭТОТ ДЕНЬ:', 'ЗАДНИЙ ДВОР, ЗА БРЕЗЕНТОМ.']
    y = py + 24
    for s in lines:
        if s:
            d.text(s, px + 14, y, ink)
        y += 10
    pencil = C('C', 2)                                                   # somebody underlined it
    d.line(px + 12, py + 101, px + 112, py + 102, pencil)
    d.line(px + 12, py + 111, px + 128, py + 112, pencil)
    d.line(px + 14, py + 113, px + 124, py + 113, pencil)
    d.text('НАЧАЛЬНИК ДЕПО', px + 14, py + 140, ink)
    d.line(px + 80, py + 146, px + 110, py + 138, C('U', 2))
    stamp_round(d, px + 200, py + 140, 19, C('U', 4), seed=773)
    d.text('ДЕПО', px + 200, py + 131, C('U', 4), center=True)
    d.text('КАРСК', px + 200, py + 139, C('U', 4), center=True)
    d.text('17.2.64', px + 200, py + 147, C('U', 4), center=True)
    for (nx, ny) in ((px + 4, py + 4), (px + pw - 5, py + 4)):           # drawing pins
        d.rect(nx - 1, ny - 1, 3, 3, C('R', 3))
    marks = {
        'visit': {'rect': [px + 12, py + 22, 150, 17], 'text': 'Dienstag, 18.2., 17.30 Uhr: Besuch eines Vertreters der schwedischen Presse'},
        'show': {'rect': [px + 12, py + 52, 150, 27], 'text': 'Vorzuführen: das wiederhergestellte Signal der Strecke (Ing. A. Morozov), die Musterbrigade, die Speisehalle'},
        'kolonne': {'rect': [px + 12, py + 92, 130, 24], 'text': 'Kolonne 4 an diesem Tag: Hinterhof, hinter der Plane (unterstrichen)'},
        'stamp': {'rect': [px + 180, py + 120, 40, 40], 'text': 'Stempel der Depotleitung'},
    }
    d.save('karsk_c4p2_press_notice', 'the press notice on the roundhouse\'s back door, the depot stamp, the '
                                      'Kolonne-4 line underlined')
    return marks


def doc_guidebook():
    d = Doc(320, 210, bg=('P', 6))
    d.noise(0, 0, 320, 210, 'P', 5.6, 0.25, 781, cell=8)                # the white tablecloth
    for k in range(0, 320, 40):
        d.rect(k, 0, 1, 210, C('P', 5))
    bx, by, bw, bh = 24, 18, 272, 176
    d.rect(bx + 4, by + 4, bw, bh, C('C', 3))                            # shadow
    d.rect(bx - 3, by - 3, bw + 6, bh + 6, C('U', 2))                   # the cloth binding
    for i, (x0, pg_) in enumerate(((bx, 212), (bx + bw // 2, 213))):    # two pages
        d.rect(x0, by, bw // 2, bh, C('P', 5))
        d.noise(x0, by, bw // 2, bh, 'P', 4.5, 0.3, 782 + i, cell=5)
        d.text(str(pg_), x0 + (8 if i == 0 else bw // 2 - 20), by + bh - 10, C('N', 2))
    d.rect(bx + bw // 2 - 1, by, 2, bh, C('P', 2))                      # the gutter
    ink = C('N', 2)
    d.text('KARSK – BANGARD', bx + 10, by + 8, ink)
    d.text('OCH DEPA', bx + 10, by + 16, ink)
    d.px(bx + 10 + K.text_width('KARSK – BANG') + 2, by + 6, ink)      # the rings of the two Å
    d.px(bx + 10 + K.text_width('OCH DEP') + 2, by + 14, ink)
    d.rect(bx + 10, by + 24, 60, 1, ink)
    d.scribble(bx + 10, by + 30, bw // 2 - 20, 6, C('N', 3), seed=783, gap=5)
    # an engraving of the station (1938)
    ex, ey = bx + 14, by + 64
    d.rect(ex, ey, 100, 44, C('P', 4))
    for k in range(0, 100, 2):
        d.px(ex + k, ey + 30, ink)
    d.rect(ex + 20, ey + 12, 60, 18, C('P', 3))
    d.rect(ex + 44, ey + 2, 12, 10, C('P', 3))
    d.line(ex + 44, ey + 2, ex + 50, ey - 2, ink)
    d.line(ex + 56, ey + 2, ex + 50, ey - 2, ink)
    for k in range(5):
        d.rect(ex + 24 + k * 11, ey + 16, 5, 8, ink)
    d.text('STATIONEN 1938', ex + 50, ey + 36, ink, center=True)
    d.scribble(bx + 10, by + 116, bw // 2 - 20, 9, C('N', 3), seed=784, gap=5)
    d.scribble(bx + bw // 2 + 8, by + 10, bw // 2 - 20, 30, C('N', 3), seed=785, gap=5)
    # the German half of card 0417, laid in upside down, sticking out of the right page
    card_half_de(d, bx + bw // 2 + 18, by + 40, w=110, h=104, upside_down=True)
    # Konrad's tracing on onion-skin over it: the Kordon room, Tür West / Tür Ost, the counter, the bench for 14
    tx, ty, tw, th = bx + 22, by + 96, 128, 70
    ys, xs = np.mgrid[0:th, 0:tw]
    region = d.a[ty:ty + th, tx:tx + tw, :3].astype(np.int32)
    milky = np.clip(region * 0.55 + np.array([110, 112, 118]) * 0.45, 0, 255)
    d.a[ty:ty + th, tx:tx + tw, :3] = K.snap(milky.astype(np.uint8))
    ln = C('U', 3)
    d.rect(tx + 14, ty + 10, 100, 1, ln)
    d.rect(tx + 14, ty + 46, 100, 1, ln)
    d.rect(tx + 14, ty + 10, 1, 37, ln)
    d.rect(tx + 113, ty + 10, 1, 37, ln)
    d.rect(tx + 14, ty + 24, 1, 8, C('P', 5))                          # Tür West (gap in the wall)
    d.rect(tx + 113, ty + 24, 1, 8, C('P', 5))                         # Tür Ost
    d.text('TÜR WEST', tx + 18, ty + 26, ln)
    d.text('TÜR OST', tx + 82, ty + 26, ln)
    d.rect(tx + 58, ty + 12, 12, 8, ln)                                # the hand-over counter
    d.rect(tx + 59, ty + 13, 10, 6, C('P', 4))
    d.rect(tx + 30, ty + 40, 60, 3, ln)                                # the waiting bench
    d.text('14', tx + 92, ty + 38, ln)
    # its lower edge folded back: the block letters on the back
    fy = ty + th - 12
    d.rect(tx, fy, tw, 12, C('S', 5))
    d.rect(tx, fy, tw, 1, C('S', 3))
    d.text('MOROZOV – 0417 – DI 23.40 – TÜR OST', tx + tw // 2, fy + 4, C('N', 1), center=True)
    marks = {
        'title': {'rect': [bx + 8, by + 6, 70, 16], 'text': 'Seite 212: „Karsk – Bahnhof und Depot“ (schwedisch, 1938)'},
        'card': {'rect': [bx + bw // 2 + 14, by + 40, 116, 56], 'text': 'Die deutsche Hälfte der Karte 0417, verkehrt herum eingelegt'},
        'tracing': {'rect': [tx, ty, tw, th - 12], 'text': 'Konrads Pause: der Raum von Kordon-17, Tür West, Tür Ost, der Durchgabeschalter, die Wartebank für vierzehn'},
        'back': {'rect': [tx, fy, tw, 12], 'text': 'Auf der Rückseite: „MOROZOV – 0417 – DI 23.40 – TÜR OST“'},
    }
    d.save('karsk_c4p2_guidebook', 'Ekdahl\'s Swedish guidebook of 1938 at page 212 with the German half of card '
                                   '0417 and Konrad\'s tracing')
    return marks


def doc_card_ru():
    d = Doc(240, 160, bg=('D', 2))
    wood(d, 0, 0, 240, 160, 791, base=3.0)                              # Lev's bench
    d.light(200, 0, 260, 0.6)
    cx, cy = 52, 26
    d.rect(cx + 3, cy + 3, 148, 104, C('N', 1))
    card_half_ru(d, cx, cy)
    stamp_c17(d, cx, cy + 52, half='right')
    d.text('ДО 19.30 – ОБРАТНО В ЯЩИК', 120, 146, C('P', 5), center=True, jitter=792)
    marks = {
        'name': {'rect': [cx + 6, cy + 15, 140, 30], 'text': '„Kowalenko, Anna Petrowna, 1926, Charkow“'},
        'returnee': {'rect': [cx + 6, cy + 45, 140, 20], 'text': '„Rückkehrerin. Weiter: Filtrationspunkt Karsk.“'},
        'accept': {'rect': [cx + 64, cy + 78, 56, 18], 'text': 'Stempel „Annehmen“'},
        'stamp_half': {'rect': [cx - 2, cy + 30, 24, 46], 'text': 'Links die Perforation, darüber ein halber runder Stempel „C-17“ in kyrillischer Schrift'},
        'slip': {'rect': [40, 140, 160, 12], 'text': 'Levs Zettel: „Bis 19.30 – zurück in den Kasten“'},
    }
    d.save('karsk_c4p2_card_ru', 'card 0417, the Russian half (the original from the box), the right half of the '
                                 'round stamp C-17')
    return marks


def doc_card_whole():
    d = Doc(320, 200, bg=('D', 2))
    wood(d, 0, 0, 320, 200, 801, base=3.2)
    d.light(160, -10, 230, 0.9)                                         # under the green lamp
    x0, y0 = 10, 50
    d.rect(x0 + 3, y0 + 3, 300, 104, C('N', 1))
    card_half_de(d, x0, y0, w=148, h=104)
    card_half_ru(d, x0 + 151, y0)                                       # teeth in the notches
    stamp_c17(d, x0 + 151, y0 + 52, half=None)
    for k in range(10):                                                 # the green shade's rim at the top edge
        hw = 34 + k * 3
        d.rect(x0 + 150 - hw, k, 2 * hw, 1, C('G', 2 + (k // 4)))
    d.rect(x0 + 150 - 64, 10, 128, 1, C('G', 6))
    d.rect(x0 + 140, 11, 20, 2, C('L', 5))
    marks = {
        'de': {'rect': [x0 + 2, y0 + 14, 140, 66], 'text': 'Links, deutsch: „Lindner, Anna, geb. Kowalenko … Vermerk C-17: Rückführung Ost. Abgabe Kordon-17, Tür Ost.“'},
        'ru': {'rect': [x0 + 155, y0 + 14, 145, 60], 'text': 'Rechts, russisch: „Kowalenko, Anna Petrowna … Annehmen … Weiter: Filtrationspunkt Karsk.“'},
        'stamp': {'rect': [x0 + 128, y0 + 28, 46, 48], 'text': 'Der runde Stempel „C-17“ schließt sich über den Schnitt: halb deutsche, halb kyrillische Schrift'},
        'teeth': {'rect': [x0 + 146, y0 + 6, 8, 92], 'text': 'Die Zähne der Perforation greifen ineinander'},
    }
    d.save('karsk_c4p2_card_whole', 'card 0417 whole under the green lamp: the teeth in the notches, the stamp '
                                    'closed')
    return marks


DOCS_META = [
    # (doc id, builder, item, objective, hotspot, scene, describes, alt text de)
    ('karsk_c4p2_order', doc_order, 'ev_c4_special_order', 'c4e_inspect_order', 'dispatch_window', 'L_C4P2_KarskA',
     'A violet carbon copy of the depot order on Irina\'s window sill: special run C-17/45 on Tuesday 18.2., one '
     'engine and one crew, transfer track 19.40 local, Kordon-17 23.40 corridor time, wagon 24 318, escort Dept. T, '
     '„Персонал молчит“; the depot stamp; under it Irina\'s pencil „Кто?“.',
     'Ein violetter Durchschlag auf Irinas Fensterbrett: „Наряд № 45/С“ – Sonderlauf C-17/45 am Dienstag, eine Lok, '
     'ein Personal, ab Umsetzgleis 19.40 Uhr, an Kordon-17 23.40 Uhr, Wagen 24 318, Begleitung Abt. T. „Персонал '
     'молчит“ (Das Personal schweigt). Darunter in Bleistift: „Кто?“ (Wer?).'),
    ('karsk_c4p2_work_list', doc_work_list, 'ev_c4_work_list', 'c4e_inspect_list', 'coal_list', 'L_C4P2_KarskA',
     'A typed list under yellowed cellophane on the coal-stage post: „Колонна 4“, arrival 22.1.1964, until the '
     'check is complete; eleven numbered names, blurred; in the margin two pencil notes: Lena, 4, and Miron, 6 – '
     'children\'s home No. 2; Wilhelm S. – special settlement North.',
     'Unter vergilbtem Zellophan: „Колонна 4. Прибытие 22.1.1964. До окончания проверки.“ Elf Namen, unleserlich. '
     'Am Rand in Bleistift: „Лена, 4, и Мирон, 6 – детдом № 2“ und „Вильгельм С. – спецпоселение Север“. Elf und '
     'drei sind vierzehn.'),
    ('karsk_c4p2_press_notice', doc_press_notice, 'ev_c4_press_notice', 'c4e_inspect_notice', 'press_notice',
     'L_C4P2_KarskA',
     'A typed notice with the depot stamp on the roundhouse\'s back door: Tuesday 18.2., 17.30, visit of a '
     'representative of the Swedish press; to be shown: the restored signal (Eng. A. Morozov), the model brigade, '
     'the canteen; Kolonne 4 that day: back yard, behind the tarpaulin -- underlined in pencil.',
     'Ein Aushang mit dem Stempel der Depotleitung: Dienstag, 18.2., 17.30 Uhr, Besuch eines Vertreters der '
     'schwedischen Presse. Vorzuführen: das Signal (Ing. A. Morozov), die Musterbrigade, die Speisehalle. „Колонна '
     '4 в этот день: задний двор, за брезентом“ – jemand hat die Zeile unterstrichen.'),
    ('karsk_c4p2_guidebook', doc_guidebook, 'ev_c4_guidebook', 'c4g_inspect_book', 'canteen_table', 'L_C4P2_KarskB',
     'A Swedish travel guide of 1938 open on the press table at page 212, „Karsk – bangård och depå“; between the '
     'pages the German half of card 0417 laid in upside down and Konrad\'s tracing of the Kordon room on onion-skin, '
     'its folded edge showing the block letters MOROZOV – 0417 – DI 23.40 – TÜR OST.',
     'Ekdahls Reiseführer von 1938, Seite 212: „Karsk – bangård och depå“. Darin, verkehrt herum, die deutsche '
     'Hälfte der Karte 0417 und eine Pause auf Pauspapier: der Raum von Kordon-17, Tür West, Tür Ost, die Wartebank '
     'für vierzehn. Auf der umgeschlagenen Rückseite: „MOROZOV – 0417 – DI 23.40 – TÜR OST“.'),
    ('karsk_c4p2_card_ru', doc_card_ru, 'ev_c4_card_ru_original', 'c4g_talk_lev', 'lev_sandhouse', 'L_C4P2_KarskB',
     'Card 0417, the Russian half, borrowed for an hour from the box „C-17/45 – принять“: Kovalenko, Anna Petrovna, '
     '1926, Kharkov; returnee; on to the filtration point Karsk; the stamp „Принять“; the notches of the perforation '
     'on its left edge and over them the right half of a round stamp C-17 in Cyrillic letters. Lev\'s slip: back in '
     'the box by 19.30.',
     'Karte 0417, russische Hälfte: „Коваленко Анна Петровна, 1926, Харьков“ – Rückkehrerin, weiter zum '
     'Filtrationspunkt Karsk, Stempel „Принять“ (Annehmen). Links die Kerben der Perforation, darüber ein halber '
     'runder Stempel „C-17“ in kyrillischer Schrift. Levs Zettel: „До 19.30 – обратно в ящик“ (Bis 19.30 zurück in '
     'den Kasten).'),
    ('karsk_c4p2_card_whole', doc_card_whole, 'ev_c4_card_whole', 'c4g_inspect_card', 'sand_lamp', 'L_C4P2_KarskB',
     'Card 0417 whole under the green lamp: the German half (Lindner, Anna, née Kowalenko … note C-17: return East, '
     'hand-over Kordon-17, Tür Ost) and the Russian half (Kovalenko, Anna Petrovna … accept … filtration point '
     'Karsk) laid edge to edge; the teeth of the perforation in the notches; the round stamp C-17 closes across the '
     'cut, half in German, half in Cyrillic letters.',
     'Die ganze Karte 0417 unter der grünen Lampe. Links deutsch: „Lindner, Anna, geb. Kowalenko … Vermerk C-17: '
     'Rückführung Ost, Abgabe Kordon-17, Tür Ost“. Rechts russisch: „Коваленко Анна Петровна … Принять … '
     'Фильтрационный пункт Карск“. Die Zähne greifen ineinander; der runde Stempel „C-17“ schließt sich – halb '
     'deutsch, halb kyrillisch.'),
]


def main():
    entries = []
    strings = {}
    for (did, fn, item, obj, hs, scene, describes, alt) in DOCS_META:
        marks = fn()
        img = Image.open(os.path.join(DOCS, did + '.png'))
        name_key = 'item.%s.name' % item[3:]
        entries.append({'file': 'res://assets/ui/documents/%s.png' % did, 'size': [img.width, img.height],
                        'display_scale': 3, 'id': did, 'alt_key': 'doc.%s.alt' % did, 'item_id': item,
                        'objective': obj, 'hotspot': hs, 'scene': scene, 'title_key': name_key,
                        'description_key': 'item.%s.description' % item[3:], 'describes': describes,
                        'marks': marks})
        strings['doc.%s.alt' % did] = alt
        n, bad = K.palette_report(np.asarray(img.convert('RGBA')))
        if bad:
            print('  WARNING %s: non-palette colours %s' % (did, bad[:4]))
    meta = {'scene': 'L_C4P2_KarskA / L_C4P2_KarskB', 'palette': 'depot',
            'generator': 'tools/pixelgen/env_c4p2_karsk_docs.py', 'date': K.DATE,
            'note': ('Pixel art drawn 1:1, shown at 3x (nearest). Only the story-critical lines are legible; the UI '
                     'shows the item name/description as HD text and the alt text (data/locale/de_env_karsk_c4p2.json) '
                     'as the German caption line. All rects are [x, y, w, h] in document pixels. Card 0417 keeps the '
                     'perforation contract of part 1 (pitch 6, hole 3, first hole 8 px below the top edge, 15 holes); '
                     'the round stamp C-17 is centred on the cut (German letters on the left arc, Cyrillic on the '
                     'right). ev_c4_card_ru_original is granted by c4g_talk_lev (its last line), so its record names '
                     'that objective.'),
            'documents': entries}
    p = os.path.join(DOCS, 'karsk_c4p2_documents.json')
    with open(p, 'w', encoding='utf-8', newline=LF) as f:
        json.dump(meta, f, indent=1, ensure_ascii=False)
        f.write(LF)
    PRODUCED.append((os.path.relpath(p, ROOT).replace('\\', '/'), 'InspectView metadata of the six documents'))
    loc = {'locale': 'de', 'area': 'karsk_c4p2', 'strings': strings}
    with open(LOCALE, 'w', encoding='utf-8', newline=LF) as f:
        json.dump(loc, f, indent=1, ensure_ascii=False)
        f.write(LF)
    PRODUCED.append((os.path.relpath(LOCALE, ROOT).replace('\\', '/'), 'German alt texts of the six documents'))
    print('[env_c4p2_karsk_docs] %d documents' % len(entries))
    return PRODUCED


if __name__ == '__main__':
    main()
