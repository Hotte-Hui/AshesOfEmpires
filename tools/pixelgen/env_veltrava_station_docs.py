"""env_veltrava_station_docs -- inspect-UI document art for L_C3_Station (drawn 1:1, shown at 3x).

Three evidence documents of C3_DESIGN 2.5 (items ev_c3_weighbill / ev_c3_departures / ev_c3_travel_order):
    veltrava_station_weighbill.png     the weighing ticket in the brass frame of courier wagon 4
    veltrava_station_departures.png    the departures board with the inserted 23.40 line
    veltrava_station_travel_order.png  Alexei's travel order with the typed addendum (RU / DE)
Text is scribble (the UI overlays HD text) EXCEPT the story-critical figures, which are legible pixel glyphs:
„2410 kg" and „C-17/44" (weighbill), „23.40 · KORDON-17 · GLEIS 5 · LEERFAHRT" (departures) and the addendum
„Begleitperson Kurierwagen 4" in Russian and German (travel order; RU says freight, DE says files).
Writes assets/ui/documents/veltrava_station_*.png + veltrava_station_documents.json (schema of
karsk_documents.json: entries keyed by item_id, pixel rects of the key marks) and the alt texts
data/locale/de_env_veltrava_station.json.  Deterministic (fixed seeds), palette 'veltrava' only.
"""
from __future__ import annotations

import json
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import numpy as np  # noqa: E402
from PIL import Image  # noqa: E402

from env_veltrava_lib import (ROOT, DOC_DIR, Layer, NI, SL, IR, CR, PA, LA, SK, SN, RD, FONT_S, FONT_L,  # noqa: E402
                              text, text_width, text_center, bayer, value_noise, palette_report, ladder_paint, dmask)

PAPER = [CR[2], CR[3], CR[4], CR[5], SN[3]]          # aged card stock -> fresh paper
WHITE = [CR[4], CR[5], SN[3], SN[4]]                  # office paper
LOC_PATH = os.path.join(ROOT, 'data', 'locale', 'de_env_veltrava_station.json')


# --------------------------------------------------------------------------- scribbles (illegible by design)
_PSEUDO = {}


def pseudo_glyphs(seed=0, n=30):
    """Print-like stroke glyphs 3-4 px wide, 5 rows, never identical to a real FONT_S letter, so filler text
    under the HD overlay reads as 'print' but never as words."""
    if seed in _PSEUDO:
        return _PSEUDO[seed]
    rng = np.random.default_rng(2000 + seed)
    real = set(tuple(g) for g in FONT_S.values())
    out = []
    while len(out) < n:
        w = int(rng.integers(3, 5))
        g = np.zeros((5, w), bool)
        for st in rng.choice(6, size=int(rng.integers(2, 4)), replace=False):
            if st == 0:
                g[:, 0] = True
            elif st == 1:
                g[:, w - 1] = True
            elif st == 2:
                g[0, :] = True
            elif st == 3:
                g[2, :] = True
            elif st == 4:
                g[4, :] = True
            else:
                for k in range(5):
                    g[k, min(w - 1, int(k * (w - 1) / 4 + 0.5))] = True
        if rng.random() < 0.5:
            g[int(rng.integers(0, 5)), int(rng.integers(0, w))] ^= True
        rows = tuple(''.join('#' if v else '.' for v in row) for row in g)
        if g.sum() >= 5 and rows not in real:
            out.append(list(rows))
    _PSEUDO[seed] = out
    return out


def scribble_print(L, x, y, w, col, rng, wear=0.08, gap=3):
    """Printed / typed pseudo text with word gaps and ink wear; returns the end x."""
    glyphs = pseudo_glyphs(int(rng.integers(0, 4)))
    cx = x
    end = x + w
    while cx < end - 3:
        for _ in range(int(rng.integers(2, 7))):
            g = glyphs[int(rng.integers(0, len(glyphs)))]
            gw = len(g[0])
            if cx + gw > end:
                break
            for r, row in enumerate(g):
                for c, v in enumerate(row):
                    if v == '#' and rng.random() > wear:
                        L.px(cx + c, y + r, col)
            cx += gw + 1
        cx += gap
    return cx


def scribble_hand(L, x, y, w, col, rng, xh=3, asc=3, slant=0, max_words=99):
    """Cursive handwriting scribble: connected humps on a baseline with random ascenders / descenders."""
    base = y + asc + xh
    cx = x
    words = 0
    while cx < x + w - 4 and words < max_words:
        n = int(rng.integers(2, 7))
        pts = [(cx, base)]
        for _ in range(n):
            kind = rng.random()
            wdt = int(rng.integers(2, 4))
            if kind < 0.18:
                pts += [(cx + 1 + slant, base - xh - asc), (cx + 1, base), (cx + wdt, base - xh + 1)]
            elif kind < 0.3:
                pts += [(cx + 1, base - xh), (cx + 1, base + 2), (cx + wdt, base)]
            elif kind < 0.65:
                pts += [(cx + 1, base - xh), (cx + wdt, base)]
            else:
                pts += [(cx + wdt, base - xh), (cx + 1, base - xh + 1), (cx + wdt, base)]
            cx += wdt + 1
            if cx > x + w - 2:
                break
        for a, b in zip(pts[:-1], pts[1:]):
            L.line(a[0], a[1], b[0], b[1], col)
        if rng.random() < 0.25:
            L.hline(int(pts[1][0]) - 1, base - xh - 1, 3, col)
        cx += int(rng.integers(3, 6))
        words += 1
    return cx


def typed(L, x, y, s, col, rng, wear=0.06, font='s', scale=1, spacing=1):
    """Typewriter / print lettering with ink starvation (legible)."""
    return text(L, x, y, s, col, font=font, scale=scale, spacing=spacing, rng=rng, wear=wear)


FONT_L_PLAIN0 = dict(FONT_L)                           # weighing-machine stamp: plain (unslashed) zero
FONT_L_PLAIN0['0'] = [".###.", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."]


def stamp_text(L, x, y, s, col, rng, holes=0.12, font='l', scale=1, glyphs=None):
    """Rubber-stamp lettering: bold (doubled) strokes with ink starvation holes."""
    f = glyphs if glyphs is not None else (FONT_L if font == 'l' else FONT_S)
    cx = x
    for ch in s:
        if ch == ' ':
            cx += 4 * scale
            continue
        g = f[ch]
        for r, row in enumerate(g):
            for c, v in enumerate(row):
                if v == '#':
                    for dx in range(scale + 1):
                        for dy in range(scale):
                            if rng.random() > holes:
                                L.px(cx + c * scale + dx, y + r * scale + dy, col)
        cx += (len(g[0]) + 1) * scale + 1
    return cx - x


def paper_fill(L, x, y, w, h, ladder, seed=0, base=2.0, edge_dark=1.0, cell=9):
    """Paper: flat base with soft mottling (ordered dither, few levels) and darker, worn edges."""
    nz = value_noise(w, h, cell, seed=seed, octaves=3)
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    edge = np.minimum(np.minimum(xx, w - 1 - xx), np.minimum(yy, h - 1 - yy))
    T = base + (nz - 0.5) * 1.1 - np.clip(1 - edge / 10.0, 0, 1) * edge_dark
    ladder_paint(L, np.ones((h, w), bool), x, y, T, ladder, steep=2.2)


def round_stamp(L, cx, cy, r, col, rng, arms=True, holes=0.18):
    """Round ink stamp: double ring, dotted legend, the Veltrava bridge arms in the centre (commission)."""
    for a in range(0, 360, 2):
        for rr in (r, r - 3):
            if rng.random() > holes:
                L.px(int(round(cx + math.cos(math.radians(a)) * rr)), int(round(cy + math.sin(math.radians(a)) * rr)), col)
    for a in range(0, 360, 9):                                 # legend dots (illegible)
        if rng.random() > 0.2:
            L.px(int(round(cx + math.cos(math.radians(a)) * (r - 6))), int(round(cy + math.sin(math.radians(a)) * (r - 6))), col)
    if arms:
        L.hline(cx - 6, cy - 3, 13, col)
        for k in (-4, 0, 4):
            L.px(cx + k - 1, cy - 2, col); L.px(cx + k + 1, cy - 2, col)
            L.px(cx + k - 2, cy - 1, col); L.px(cx + k + 2, cy - 1, col)
        for k in range(-6, 7, 2):
            L.px(cx + k, cy + 2 + (k // 2) % 2, col)


def save_doc(L, name, marks, meta):
    os.makedirs(DOC_DIR, exist_ok=True)
    Image.fromarray(L.c, 'RGBA').save(os.path.join(DOC_DIR, name))
    off = palette_report(L.c)
    if off:
        print('WARN off-palette colours in', name, off[:5])
    d = {'file': 'res://assets/ui/documents/' + name, 'size': [L.w, L.h], 'display_scale': 3}
    d.update(meta)
    d['marks'] = marks
    return d


# =========================================================================== WEIGHBILL (Wiegekarte)
def make_weighbill():
    """The weighing ticket behind glass in the brass frame of courier wagon 4 (close-up of the frame)."""
    W, H = 240, 160
    L = Layer(W, H, 'veltrava_station_weighbill')
    rng = np.random.default_rng(301)
    # wagon side: riveted dark-green panels behind the frame
    L.rect(0, 0, W, H, PA[0])
    for y in range(0, H, 10):
        L.hline(0, y, W, NI[3])
        for x in range(2, W, 4):
            L.px(x, y + 1, IR[3])
    for x in range(0, W, 30):
        L.vline(x, 0, H, NI[3])
    # brass frame (bevelled), screws, glass
    fx, fy, fw, fh = 18, 12, 204, 136
    L.rect(fx - 6, fy - 6, fw + 12, fh + 12, LA[0])
    L.rect(fx - 5, fy - 5, fw + 10, fh + 10, LA[1])
    L.hline(fx - 5, fy - 5, fw + 10, LA[3]); L.vline(fx - 5, fy - 5, fh + 10, LA[2])
    L.hline(fx - 5, fy + fh + 4, fw + 10, LA[0]); L.vline(fx + fw + 4, fy - 5, fh + 10, LA[2])
    L.rect(fx - 2, fy - 2, fw + 4, fh + 4, LA[0])
    L.hline(fx - 2, fy - 2, fw + 4, LA[2])
    for (sx, sy) in ((fx - 4, fy - 4), (fx + fw + 2, fy - 4), (fx - 4, fy + fh + 2), (fx + fw + 2, fy + fh + 2)):
        L.rect(sx, sy, 3, 3, LA[2]); L.px(sx + 1, sy + 1, LA[0]); L.px(sx, sy, LA[4])
    # the ticket (cream card stock), slightly askew corner and a thumb smudge
    paper_fill(L, fx, fy, fw, fh, PAPER, seed=5, base=2.4, edge_dark=1.3)
    marks = {}
    # printed form head: station logotype (bridge arms), title lines (scribble), form number
    L.rect(fx + 6, fy + 6, fw - 12, 1, SL[2])
    L.rect(fx + 6, fy + 30, fw - 12, 1, SL[2])
    L.hline(fx + 10, fy + 12, 15, SL[2])
    for k in (3, 7, 11):
        L.px(fx + 10 + k - 1, fy + 13, SL[2]); L.px(fx + 10 + k + 1, fy + 13, SL[2])
        L.vline(fx + 10 + k - 2, fy + 13, 3, SL[2]); L.vline(fx + 10 + k + 2, fy + 13, 3, SL[2])
    for k in range(10, 25, 2):
        L.px(fx + k, fy + 18 + (k // 2) % 2, SL[2])
    scribble_print(L, fx + 32, fy + 10, 120, SL[1], rng, wear=0.05)       # 'Wiegekarte' / station name
    scribble_print(L, fx + 32, fy + 18, 90, SL[2], rng, wear=0.1)
    typed(L, fx + fw - 48, fy + 10, 'Nr. 0417', SL[1], rng, wear=0.1)
    typed(L, fx + fw - 48, fy + 18, '12.02.64', SL[1], rng, wear=0.1)
    marks['header'] = {'rect': [fx + 6, fy + 6, fw - 12, 25]}
    # field rows: printed labels (scribble, light) + typed values (scribble, dark)
    rows = [fy + 36, fy + 48, fy + 60, fy + 72]
    for i, ry in enumerate(rows):
        scribble_print(L, fx + 8, ry, 44, SL[3], rng, wear=0.12)
        L.hline(fx + 8, ry + 7, fw - 16, SL[3])
        if i == 0:                                                             # Wagen: 4 (typed digit legible)
            typed(L, fx + 58, ry - 1, 'KURIERWAGEN 4', SL[0], rng, wear=0.08)
            marks['wagon'] = {'rect': [fx + 58, ry - 1, 60, 7]}
        elif i == 1:                                                           # Ladung: Akten, Anlage C (scribble)
            scribble_print(L, fx + 58, ry, 110, SL[0], rng, wear=0.05)
            marks['cargo'] = {'rect': [fx + 58, ry, 110, 7], 'note': 'Ladung „Akten, Anlage C“ (scribble)'}
        elif i == 2:                                                           # Empfänger: Sekretariat (scribble)
            scribble_print(L, fx + 58, ry, 126, SL[0], rng, wear=0.05)
            marks['recipient'] = {'rect': [fx + 58, ry, 126, 7], 'note': 'Empfänger: Sekretariat der Kommission'}
        else:                                                                  # Abgang / Bestimmung
            scribble_print(L, fx + 58, ry, 70, SL[0], rng, wear=0.05)
            scribble_print(L, fx + 134, ry, 50, SL[0], rng, wear=0.05)
    # the MASS: boxed weighing field, big stamped digits (legible): 2410 kg
    bx, by, bw, bh = fx + 8, fy + 84, 104, 30
    L.rect(bx, by, bw, bh, CR[5]); L.rect(bx, by, bw, 1, SL[2]); L.rect(bx, by + bh - 1, bw, 1, SL[2])
    L.rect(bx, by, 1, bh, SL[2]); L.rect(bx + bw - 1, by, 1, bh, SL[2])
    scribble_print(L, bx + 3, by + 3, 60, SL[3], rng, wear=0.15)            # 'Bruttogewicht' label
    mw = stamp_text(L, bx + 6, by + 11, '2410', NI[1], rng, holes=0.08, scale=2, glyphs=FONT_L_PLAIN0)
    kw = text(L, bx + 6 + mw + 4, by + 18, 'kg', NI[1], font='l', rng=rng, wear=0.05)
    marks['mass'] = {'rect': [bx + 6, by + 11, mw + 6 + kw, 16], 'text': '2410 kg'}
    # seal number: PLOMBE C-17/44 — red stamp (the story's C-17 red), legible
    sx, sy = fx + 120, fy + 82
    scribble_print(L, sx, sy, 40, SL[3], rng, wear=0.15)                      # 'Plombe Nr.' label
    L.rect(sx - 2, sy + 8, 80, 16, CR[5])
    srng = np.random.default_rng(31)
    for k in range(80):
        for (yy, c) in ((sy + 8, RD[2]), (sy + 23, RD[2])):
            if srng.random() > 0.08:
                L.px(sx - 2 + k, yy, c)
    for k in range(16):
        for (xx, c) in ((sx - 2, RD[2]), (sx + 77, RD[2])):
            if srng.random() > 0.08:
                L.px(xx, sy + 8 + k, c)
    tw = stamp_text(L, sx + 4, sy + 12, 'C-17/44', RD[3], srng, holes=0.07)
    marks['seal_no'] = {'rect': [sx - 2, sy + 8, 80, 16], 'text_rect': [sx + 4, sy + 12, tw, 7], 'text': 'C-17/44',
                        'color': 'red'}
    # commission counter-seal: round slate-blue stamp with the bridge arms, struck over the signature line
    L.hline(fx + 120, fy + 124, 76, SL[3])
    scribble_hand(L, fx + 124, fy + 112, 56, SL[0], rng, xh=3, asc=3, max_words=2)
    round_stamp(L, fx + 180, fy + 128, 15, SL[3], rng)
    marks['counter_seal'] = {'rect': [fx + 164, fy + 112, 33, 33], 'note': 'Gegensiegel der Kommission (bridge arms)'}
    scribble_print(L, fx + 8, fy + 120, 90, SL[3], rng, wear=0.2)            # footer small print
    scribble_print(L, fx + 8, fy + 127, 70, SL[3], rng, wear=0.2)
    # tally pencil line and a thumb smudge
    L.hline(fx + 12, fy + 118, 12, CR[2])
    for _ in range(14):
        L.px(fx + 20 + int(rng.integers(0, 16)), fy + 128 + int(rng.integers(0, 6)), CR[2])
    # glass: diagonal cold glints at the upper right, a few dust specks (clean clusters, no blur)
    for k in range(26):
        xx, yy = fx + fw - 40 + k, fy + 4 + k
        if yy < fy + fh and xx < fx + fw:
            L.px(xx, yy, SN[4] if k % 2 else SN[3])
            L.px(xx + 3, yy, SN[3]) if k % 3 == 0 else None
    for k in range(8):
        xx, yy = fx + fw - 22 + k, fy + 2 + k
        L.px(xx, yy, SN[4])
    marks['frame'] = {'rect': [fx - 6, fy - 6, fw + 12, fh + 12], 'note': 'brass frame with glass'}
    marks['ticket'] = {'rect': [fx, fy, fw, fh]}
    L.outline(NI[1], outer=False)
    return save_doc(L, 'veltrava_station_weighbill.png', marks, {
        'id': 'veltrava_station_weighbill', 'alt_key': 'doc.veltrava.weighbill.alt', 'item_id': 'ev_c3_weighbill',
        'objective': 'c3a_inspect_weighbill', 'hotspot': 'weighbill', 'title_key': 'item.c3_weighbill.name',
        'description_key': 'item.c3_weighbill.description',
        'describes': 'Weighing ticket in the brass frame of courier wagon 4: cargo „Akten, Anlage C“ (scribble), '
                     'the stamped mass 2410 kg (legible), the red seal number C-17/44 (legible) and the round '
                     'slate-blue counter-seal of the commission (bridge arms) over the signature.'})


# =========================================================================== DEPARTURES (Abfahrtstafel)
def make_departures():
    """Close-up of the mechanical split-flap departures board: four day trains (scribble flaps) and the freshly
    inserted night line 23.40 · KORDON-17 · GLEIS 5 · LEERFAHRT (legible)."""
    W, H = 300, 190
    L = Layer(W, H, 'veltrava_station_departures')
    rng = np.random.default_rng(302)
    # cast-iron case with rivets, black enamel face
    L.rect(0, 0, W, H, IR[1])
    L.rect(0, 0, W, 2, IR[3]); L.rect(0, 0, 2, H, IR[2]); L.rect(W - 2, 0, 2, H, NI[2]); L.rect(0, H - 2, W, 2, NI[2])
    for x in range(8, W, 24):
        L.rect(x, 4, 2, 2, IR[3]); L.rect(x, H - 6, 2, 2, IR[3])
    bx, by, bw, bh = 10, 10, W - 20, H - 20
    L.rect(bx, by, bw, bh, NI[0])
    nz = value_noise(bw, bh, 12, seed=4, octaves=2)
    L.c[by:by + bh, bx:bx + bw][nz > 0.72] = NI[1]
    # header band: ABFAHRT (legible, station lettering) + the RU / FR words as pseudo print + date
    L.rect(bx + 2, by + 2, bw - 4, 16, IR[2])
    L.hline(bx + 2, by + 17, bw - 4, IR[4])
    typed(L, bx + 8, by + 6, 'ABFAHRT', SN[4], rng, wear=0.0, font='l')
    scribble_print(L, bx + 70, by + 7, 60, SN[2], rng, wear=0.1)
    scribble_print(L, bx + 140, by + 7, 60, SN[2], rng, wear=0.1)
    typed(L, bx + bw - 54, by + 7, '12.02.1964', SN[3], rng, wear=0.05)
    marks = {'header': {'rect': [bx + 2, by + 2, bw - 4, 16]}}
    # column headers (pseudo print) over the flap columns
    cols = [bx + 6, bx + 48, bx + 128, bx + 180, bx + bw - 6]
    hy = by + 24
    for i in range(4):
        scribble_print(L, cols[i] + 2, hy, cols[i + 1] - cols[i] - 8, SN[1], rng, wear=0.15)
    L.hline(bx + 4, hy + 8, bw - 8, IR[2])

    def flap_row(ry, h=11):
        """One row of split-flap tiles: tile background with the horizontal split line."""
        L.rect(bx + 4, ry, bw - 8, h, NI[2])
        L.hline(bx + 4, ry + h // 2, bw - 8, NI[0])
        for x in cols[1:-1]:
            L.vline(x - 3, ry, h, NI[0])
        for x in range(bx + 4, bx + bw - 4, 7):
            L.vline(x, ry, h, NI[1])

    rows_y = [hy + 14 + i * 16 for i in range(5)]
    for i, ry in enumerate(rows_y[:4]):
        flap_row(ry)
        col = SN[2] if i % 2 else SN[1]
        scribble_print(L, cols[0] + 3, ry + 3, 30, col, rng, wear=0.15, gap=2)
        scribble_print(L, cols[1] + 3, ry + 3, 70, col, rng, wear=0.15, gap=2)
        scribble_print(L, cols[2] + 3, ry + 3, 20, col, rng, wear=0.15, gap=2)
        scribble_print(L, cols[3] + 3, ry + 3, 84, col, rng, wear=0.15, gap=2)
        marks['row_%d' % (i + 1)] = {'rect': [bx + 4, ry, bw - 8, 11], 'note': 'day train (scribble)'}
    # the inserted night line: fresh flaps (lighter tiles, un-dusted), legible big glyphs
    ry = rows_y[4]
    flap_row(ry, h=13)
    L.rect(bx + 4, ry, bw - 8, 13, IR[1]); L.hline(bx + 4, ry + 6, bw - 8, NI[0])
    for x in cols[1:-1]:
        L.vline(x - 3, ry, 13, NI[0])
    for x in range(bx + 4, bx + bw - 4, 7):
        L.vline(x, ry, 13, IR[2])
    L.hline(bx + 4, ry - 1, bw - 8, SN[1])                                   # bright edge of the fresh slip
    parts = [('23.40', cols[0] + 3), ('KORDON-17', cols[1] + 3), ('GLEIS 5', cols[2] + 3), ('LEERFAHRT', cols[3] + 3)]
    for (s, x) in parts:
        w = text(L, x, ry + 3, s, SN[4], font='l', rng=rng, wear=0.0)
        key = {'23.40': 'time', 'KORDON-17': 'destination', 'GLEIS 5': 'track', 'LEERFAHRT': 'category'}[s]
        marks[key] = {'rect': [x, ry + 3, w, 7], 'text': s}
    marks['night_line'] = {'rect': [bx + 4, ry - 1, bw - 8, 15], 'text': '23.40 · KORDON-17 · GLEIS 5 · LEERFAHRT',
                           'note': 'freshly inserted; Zuggattung reads only Leerfahrt'}
    for i in range(2):                                                        # empty flap rows below (dashes)
        ey = ry + 18 + i * 16
        flap_row(ey)
        for x in cols[:-1]:
            for k in range(x + 4, min(x + 60, cols[cols.index(x) + 1] - 6), 7):
                L.hline(k + 1, ey + 5, 3, NI[3])
    # paper slip with a pencilled note pinned at the bottom right (scribble), key lock, dust streaks
    paper_fill(L, bx + bw - 70, by + bh - 26, 62, 20, WHITE, seed=7, base=2.0, edge_dark=0.6)
    for k in range(3):
        scribble_hand(L, bx + bw - 66, by + bh - 25 + k * 6, 54, SL[0], rng, xh=2, asc=1, max_words=3)
    L.rect(bx + bw - 40, by + bh - 28, 3, 3, IR[3])
    L.rect(bx + 10, by + bh - 14, 6, 6, IR[2]); L.px(bx + 12, by + bh - 12, NI[0]); L.px(bx + 13, by + bh - 11, NI[0])
    for _ in range(40):
        x = bx + int(rng.integers(0, bw)); y = by + int(rng.integers(0, bh))
        if (L.c[y, x, :3] == NI[0][:3]).all():
            L.px(x, y, NI[1])
    # cold reflection of a canopy lamp in the glass (upper left), clean diagonal
    for k in range(18):
        L.px(bx + 14 + k, by + 20 + k, SL[3] if k % 2 else SL[2])
    L.outline(NI[1], outer=False)
    return save_doc(L, 'veltrava_station_departures.png', marks, {
        'id': 'veltrava_station_departures', 'alt_key': 'doc.veltrava.departures.alt', 'item_id': 'ev_c3_departures',
        'objective': 'c3a_inspect_departures', 'hotspot': 'departures', 'title_key': 'item.c3_departures.name',
        'description_key': 'item.c3_departures.description',
        'describes': 'Split-flap departures board: four day trains as scribble flaps; the freshly inserted last '
                     'line reads 23.40 · KORDON-17 · GLEIS 5 · LEERFAHRT (legible).'})


# =========================================================================== TRAVEL ORDER (Dienstreiseauftrag)
def make_travel_order():
    """Alexei's typed Soviet travel order (grey office paper, faded ribbon, round stamp, signature) with the
    addendum typed later on another machine: „Begleitperson Kurierwagen 4“ in Russian (… freight) and German
    (… files) — both legible."""
    W, H = 260, 200
    L = Layer(W, H, 'veltrava_station_travel_order')
    rng = np.random.default_rng(303)
    # the officer's counter: dark wood, the paper slightly turned, a corner folded
    L.rect(0, 0, W, H, CR[0])
    for y in range(0, H, 3):
        if rng.random() < 0.5:
            L.hline(0, y, W, CR[1])
    px0, py0, pw, ph = 14, 8, W - 28, H - 16
    paper_fill(L, px0, py0, pw, ph, WHITE, seed=9, base=2.3, edge_dark=1.2)
    for k in range(9):                                                        # folded corner, bottom right
        L.hline(px0 + pw - 9 + k, py0 + ph - 9 + k, 9 - k, CR[4])
        L.px(px0 + pw - 9 + k, py0 + ph - 1 - (8 - k), CR[3])
    marks = {}
    # ministry letterhead: two centred lines of pseudo print, a rule, the form number; NO state emblem
    scribble_print(L, px0 + 52, py0 + 8, 120, SL[1], rng, wear=0.08)
    scribble_print(L, px0 + 70, py0 + 15, 84, SL[2], rng, wear=0.12)
    L.hline(px0 + 10, py0 + 24, pw - 20, SL[2])
    typed(L, px0 + 10, py0 + 28, 'ФОРМА Т-10', SL[2], rng, wear=0.15)
    typed(L, px0 + pw - 50, py0 + 28, '№ 2 17/64', SL[1], rng, wear=0.12)
    marks['letterhead'] = {'rect': [px0 + 10, py0 + 6, pw - 20, 20]}
    # title line (pseudo print, larger spacing), then the typed body in faded ribbon
    L.hline(px0 + 60, py0 + 44, 100, SL[3])
    scribble_print(L, px0 + 62, py0 + 37, 96, SL[0], rng, wear=0.05, gap=4)
    body = [py0 + 52, py0 + 60, py0 + 68, py0 + 76, py0 + 84, py0 + 92]
    for i, ry in enumerate(body):
        label_w = [34, 26, 40, 30, 36, 28][i]
        scribble_print(L, px0 + 10, ry, label_w, SL[2], rng, wear=0.1)
        L.hline(px0 + 12 + label_w, ry + 6, pw - 24 - label_w, SL[3])
        if i == 0:
            typed(L, px0 + 14 + label_w, ry, 'МОРОЗОВ А. И.', SL[0], rng, wear=0.08)      # name (legible)
            marks['name'] = {'rect': [px0 + 14 + label_w, ry, 56, 6], 'text': 'МОРОЗОВ А. И.'}
        elif i == 2:
            typed(L, px0 + 14 + label_w, ry, 'ВЕЛТРАВА', SL[0], rng, wear=0.08)           # destination
        elif i == 4:
            typed(L, px0 + 14 + label_w, ry, '12.02.1964 - 19.02.1964', SL[0], rng, wear=0.1)
        else:
            scribble_print(L, px0 + 14 + label_w, ry, pw - 40 - label_w, SL[0], rng, wear=0.08)
    marks['body'] = {'rect': [px0 + 10, py0 + 50, pw - 20, 50], 'note': 'typed form fields (scribble)'}
    # the ADDENDUM: typed later on another machine (darker ribbon, baseline 1 px off, no label), two lines
    ay = py0 + 108
    L.hline(px0 + 10, ay - 4, pw - 20, SL[3])
    scribble_print(L, px0 + 10, ay - 12, 48, SL[2], rng, wear=0.1)                       # 'Zusatz / Примечание'
    ru = 'СОПРОВОЖДАЮЩИЙ: КУРЬЕРСКИЙ ВАГОН 4 (ГРУЗ)'
    de = 'BEGLEITPERSON: KURIERWAGEN 4 (AKTEN)'
    wru = typed(L, px0 + 12, ay, ru, NI[1], rng, wear=0.03)
    wde = typed(L, px0 + 12, ay + 9, de, NI[1], rng, wear=0.03)
    marks['addendum_ru'] = {'rect': [px0 + 12, ay - 2, wru, 7], 'text': ru,
                            'note': 'Russian: he accompanies freight (груз)'}
    marks['addendum_de'] = {'rect': [px0 + 12, ay + 7, wde, 7], 'text': de,
                            'note': 'German: he accompanies files (Akten)'}
    marks['addendum'] = {'rect': [px0 + 8, ay - 3, max(wru, wde) + 8, 18], 'text': 'Begleitperson Kurierwagen 4',
                         'note': 'typed later on another machine: darker ribbon, baseline off by 1 px'}
    for k in range(ay - 3, ay + 16, 2):                                                   # pencil bracket in the margin
        L.px(px0 + 6, k, CR[2])
    L.px(px0 + 7, ay - 3, CR[2]); L.px(px0 + 7, ay + 15, CR[2])
    # signatures, date, the round ministry stamp (slate ink) and a second small stamp of the commission
    L.hline(px0 + 14, py0 + ph - 30, 70, SL[3])
    scribble_hand(L, px0 + 18, py0 + ph - 44, 60, NI[1], rng, xh=3, asc=4, slant=1, max_words=2)
    scribble_print(L, px0 + 14, py0 + ph - 27, 50, SL[3], rng, wear=0.15)
    L.hline(px0 + pw - 90, py0 + ph - 30, 70, SL[3])
    scribble_hand(L, px0 + pw - 84, py0 + ph - 43, 54, SL[0], rng, xh=3, asc=3, max_words=2)
    scribble_print(L, px0 + pw - 90, py0 + ph - 27, 46, SL[3], rng, wear=0.15)
    round_stamp(L, px0 + 60, py0 + ph - 44, 20, SL[2], rng, arms=False, holes=0.22)
    marks['stamp'] = {'rect': [px0 + 40, py0 + ph - 64, 41, 41], 'note': 'round ministry stamp, slate ink'}
    round_stamp(L, px0 + pw - 36, py0 + 116, 12, SL[3], rng, arms=True, holes=0.25)
    marks['commission_stamp'] = {'rect': [px0 + pw - 48, py0 + 104, 25, 25], 'note': 'commission control stamp'}
    marks['signature'] = {'rect': [px0 + 14, py0 + ph - 46, 70, 18]}
    # paper clip, a coffee ring, a crease
    for k in range(10):
        L.px(px0 + pw - 60 + k, py0 - 2, IR[3]); L.px(px0 + pw - 60 + k, py0 + 8, IR[3])
    L.vline(px0 + pw - 60, py0 - 2, 11, IR[3]); L.vline(px0 + pw - 51, py0 - 2, 11, IR[4])
    for a in range(0, 360, 5):
        r = 14 + (a % 40 == 0)
        xx = int(px0 + 190 + math.cos(math.radians(a)) * r); yy = int(py0 + 70 + math.sin(math.radians(a)) * r * 0.75)
        if (L.c[yy, xx, :3] != NI[1][:3]).any():
            L.px(xx, yy, CR[4])
    for y in range(py0, py0 + ph):
        if (L.c[y, px0 + 128, :3] != NI[1][:3]).any() and y % 3:
            L.px(px0 + 128, y, CR[5])
    L.outline(NI[1], outer=False)
    return save_doc(L, 'veltrava_station_travel_order.png', marks, {
        'id': 'veltrava_station_travel_order', 'alt_key': 'doc.veltrava.travel_order.alt',
        'item_id': 'ev_c3_travel_order', 'objective': 'c3a_pass_control', 'hotspot': 'control',
        'title_key': 'item.c3_travel_order.name', 'description_key': 'item.c3_travel_order.description',
        'describes': 'Typed Soviet travel order (grey office paper, faded ribbon, round stamps, signatures). The '
                     'addendum typed later on another machine is legible in Russian and German: '
                     'СОПРОВОЖДАЮЩИЙ: КУРЬЕРСКИЙ ВАГОН 4 (ГРУЗ) / BEGLEITPERSON: KURIERWAGEN 4 (AKTEN).'})


# =========================================================================== build
ALT_TEXTS = {
    'doc.veltrava.weighbill.alt': 'Wiegekarte im Messingrahmen von Kurierwagen 4: Ladung „Akten, Anlage C“, '
                                  'Gewicht 2410 kg, Plombe C-17/44 mit dem runden Gegensiegel der Kommission. '
                                  'Empfänger: Sekretariat der Kommission.',
    'doc.veltrava.departures.alt': 'Abfahrtstafel mit Fallblättern: vier Tageszüge, darunter eine frisch eingeschobene '
                                   'Zeile – 23.40, Kordon-17, Gleis 5, Zuggattung: Leerfahrt.',
    'doc.veltrava.travel_order.alt': 'Dienstreiseauftrag auf grauem Dienstpapier, Stempel und Unterschriften. Ein '
                                     'nachträglich eingetippter Zusatz lautet „Begleitperson Kurierwagen 4“ – auf '
                                     'Russisch mit dem Vermerk Fracht, auf Deutsch mit dem Vermerk Akten.',
}


def build_all():
    docs = [make_weighbill(), make_departures(), make_travel_order()]
    out = {'scene': 'L_C3_Station', 'palette': 'veltrava (incl. the shared C-17 red accent)',
           'generator': 'tools/pixelgen/env_veltrava_station_docs.py (via env_veltrava_station.py)',
           'date': '2026-11-05',
           'note': 'Pixel art drawn 1:1, shown at 3x (nearest). Text is scribble except the story-critical figures '
                   '(legible pixel glyphs). All rects are [x, y, w, h] in document pixels.',
           'documents': docs}
    with open(os.path.join(DOC_DIR, 'veltrava_station_documents.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(out, f, indent=1, ensure_ascii=False)
    os.makedirs(os.path.dirname(LOC_PATH), exist_ok=True)
    with open(LOC_PATH, 'w', encoding='utf-8', newline='\n') as f:
        json.dump({'locale': 'de', 'area': 'env_veltrava_station', 'strings': ALT_TEXTS}, f, indent=1,
                  ensure_ascii=False)
        f.write('\n')
    print('documents:', ', '.join(d['id'] for d in docs))
    return out


if __name__ == '__main__':
    build_all()
