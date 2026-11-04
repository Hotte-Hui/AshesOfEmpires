"""env_karsk_docs -- inspect-UI document art for scene A1 (drawn 1:1, shown at 3x in InspectView).

Text is kept as pixel scribbles (the UI overlays readable HD text), but the story-critical marks are
legible in pixels: the 'C-17' under the abraded double stamp on the lead seal, the square / circle /
triangle marks, the red C-17 ledger stamp, the blacked-out recipient, the three empty card slots.
Writes assets/ui/documents/karsk_*.png and karsk_documents.json (pixel rects of the key marks).
"""
from __future__ import annotations

import os as _os
import sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))

import json
import math
import os

import numpy as np

from env_karsk_lib import (DOC_DIR, Layer, NI, TE, SA, SK, ST, RU, CO, SN, WO, RED, FONT_S, FONT_L, text,
                           text_width, bayer, value_noise, palette_report)

PAPER = [SK[3], SK[4], SK[5], SN[3], SN[4]]
INK = NI[1]


# --------------------------------------------------------------------------- scribbles
_PSEUDO_CACHE = {}


def _pseudo_glyphs(seed=0, n=28):
    """Print-like pseudo glyphs (3-4 px wide, 5 rows) built from strokes; deliberately not real letters
    so filler text never reads as words under the HD text overlay."""
    if seed in _PSEUDO_CACHE:
        return _PSEUDO_CACHE[seed]
    rng = np.random.default_rng(1000 + seed)
    out = []
    real = set(tuple(g) for g in FONT_S.values())
    while len(out) < n:
        w = int(rng.integers(3, 5))
        g = np.zeros((5, w), bool)
        strokes = rng.choice(6, size=int(rng.integers(2, 4)), replace=False)
        for st in strokes:
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
        if rng.random() < 0.5:                    # notch / serif to break letter likeness
            g[int(rng.integers(0, 5)), int(rng.integers(0, w))] ^= True
        rows = tuple(''.join('#' if v else '.' for v in row) for row in g)
        if g.sum() >= 5 and rows not in real:
            out.append(list(rows))
    _PSEUDO_CACHE[seed] = out
    return out


def scribble_print(L, x, y, w, col, rng, wear=0.08, max_x=None):
    """Printed / stencilled pseudo text (illegible stroke glyphs with word gaps and wear)."""
    glyphs = _pseudo_glyphs(int(rng.integers(0, 4)))
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
        cx += 3
    return cx


def scribble_digits(L, x, y, s, col, rng, wear=0.05):
    cx = x
    for ch in s:
        g = FONT_S.get(ch)
        if g is None:
            cx += 2
            continue
        for r, row in enumerate(g):
            for c, v in enumerate(row):
                if v == '#' and rng.random() > wear:
                    L.px(cx + c, y + r, col)
        cx += len(g[0]) + 1
    return cx


def scribble_hand(L, x, y, w, col, rng, xh=3, asc=3, slant=0, max_words=99):
    """Cursive handwriting scribble: connected humps on a baseline, random ascenders/descenders."""
    base = y + asc + xh
    cx = x
    words = 0
    while cx < x + w - 4 and words < max_words:
        n = int(rng.integers(2, 7))
        pts = [(cx, base)]
        for i in range(n):
            kind = rng.random()
            wdt = int(rng.integers(2, 4))
            if kind < 0.18:          # ascender
                pts += [(cx + 1 + slant, base - xh - asc), (cx + 1, base), (cx + wdt, base - xh + 1)]
            elif kind < 0.3:         # descender
                pts += [(cx + 1, base - xh), (cx + 1, base + 2), (cx + wdt, base)]
            elif kind < 0.65:        # hump
                pts += [(cx + 1, base - xh), (cx + wdt, base)]
            else:                    # loop-ish
                pts += [(cx + wdt, base - xh), (cx + 1, base - xh + 1), (cx + wdt, base)]
            cx += wdt + 1
            if cx > x + w - 2:
                break
        for a, b in zip(pts[:-1], pts[1:]):
            L.line(a[0], a[1], b[0], b[1], col)
        if rng.random() < 0.25:      # crossbar / diacritic
            L.hline(int(pts[1][0]) - 1, base - xh - 1, 3, col)
        cx += int(rng.integers(3, 6))
        words += 1
    return cx


def paper_fill(L, x, y, w, h, seed=0, base=2, aged=True):
    """Aged paper: flat base with soft mottling (ordered dither, few levels), darker edges."""
    nz = value_noise(w, h, 9, seed=seed, octaves=3)
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    edge = np.minimum(np.minimum(xx, w - 1 - xx), np.minimum(yy, h - 1 - yy))
    t = base + (nz - 0.5) * 1.1 - np.clip(1 - edge / 10.0, 0, 1) * (1.2 if aged else 0.4)
    t = np.clip(t, 0, len(PAPER) - 1)
    idx = np.floor(t).astype(int)
    fr = np.clip((t - idx - 0.5) * 2.2 + 0.5, 0, 1)
    idx = np.clip(idx + (fr > bayer(w, h, x, y)), 0, len(PAPER) - 1)
    L.c[y:y + h, x:x + w] = np.stack(PAPER)[idx]


def stamp_text(L, x, y, s, col, rng, bold=True, holes=0.12, font='l'):
    """Rubber-stamp lettering: bold strokes with ink starvation holes."""
    f = FONT_L if font == 'l' else FONT_S
    cx = x
    rects = []
    for ch in s:
        if ch == ' ':
            cx += 4
            continue
        g = f[ch]
        for r, row in enumerate(g):
            for c, v in enumerate(row):
                if v == '#':
                    for dx in ((0, 1) if bold else (0,)):
                        if rng.random() > holes:
                            L.px(cx + c + dx, y + r, col)
        cx += len(g[0]) + (2 if bold else 1)
    return cx - x


def save_doc(L, name, marks, meta):
    os.makedirs(DOC_DIR, exist_ok=True)
    path = os.path.join(DOC_DIR, name)
    from PIL import Image
    Image.fromarray(L.c, 'RGBA').save(path)
    off = palette_report(L.c)
    if off:
        print('WARN off-palette colours in', name, off[:5])
    d = {'file': 'res://assets/ui/documents/' + name, 'size': [L.w, L.h], 'display_scale': 3}
    d.update(meta)
    d['marks'] = marks
    return d


# =========================================================================== SEAL
def make_seal():
    W, H = 200, 140
    L = Layer(W, H, 'karsk_seal')
    rng = np.random.default_rng(101)
    # wagon door planks (rust-brown paint, worn to wood), vertical boards 10 px
    for x in range(W):
        board = x // 10
        col = RU[1] if (x % 10) not in (0, 9) else RU[0]
        L.rect(x, 0, 1, H, col)
        if x % 10 == 1:
            L.vline(x, 0, H, RU[2])
    nzs = value_noise(W // 3 + 2, H // 14 + 2, 2, seed=3, octaves=2)
    nz = np.repeat(np.repeat(nzs, 3, axis=1), 14, axis=0)[:H, :W]
    nz = nz * 0.75 + value_noise(W, H, 5, seed=4, octaves=2) * 0.25
    worn = nz > 0.6
    L.c[worn] = WO[2]
    L.c[(nz > 0.68)] = WO[3]
    edge = worn & ~np.roll(worn, 1, axis=0)
    L.c[edge] = RU[0]
    for _ in range(90):                                 # wood grain flecks
        x = int(rng.integers(0, W))
        y = int(rng.integers(0, H - 6))
        L.vline(x, y, int(rng.integers(2, 6)), RU[0])
    for x in range(0, W, 10):                           # nails
        for y in (14, 124):
            L.px(x + 5, y, ST[3])
            L.px(x + 5, y + 1, RU[0])
    # steel hasp (latch) across the upper part + staple ring
    L.rect(14, 30, 110, 14, ST[2])
    L.hline(14, 30, 110, ST[4])
    L.hline(14, 31, 110, ST[3])
    L.hline(14, 43, 110, ST[0])
    for x in (20, 60, 100):
        L.rect(x, 34, 4, 4, ST[1])
        L.px(x + 1, 34, ST[4])
    L.vline(123, 30, 14, ST[1])
    for k in range(H - 46):                             # rust bleed below the hasp
        if rng.random() < 0.5:
            x = 16 + int(rng.integers(0, 106))
            L.vline(x, 44, int(rng.integers(3, 14)), RU[2] if rng.random() < 0.5 else RU[3])
    # staple ring at the hasp end
    m, mx, my = L.ellipse(132, 37, 9, 9, ST[1])
    L.ellipse(132, 37, 5, 5, RU[1])
    for a in range(-90, 20, 15):
        L.px(132 + int(round(math.cos(math.radians(a)) * 8)), 37 + int(round(math.sin(math.radians(a)) * 8)), ST[4])
    # twisted seal wire from the ring down to the seal
    for k in range(0, 34):
        x = 130 - k // 3
        y = 46 + k
        L.px(x, y, ST[4] if k % 3 else ST[2])
        L.px(x + 1, y, ST[2] if k % 3 else ST[4])
    # lead seal disc (dented), lit from upper right
    cx, cy, rx, ry = 104, 92, 36, 29
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    dx = (xx + 0.5 - cx) / rx
    dy = (yy + 0.5 - cy) / ry
    r2 = dx * dx + dy * dy
    disc = r2 <= 1.0
    dent = ((xx - 82) ** 2 / 90 + (yy - 104) ** 2 / 40) < 1
    shade = 0.55 + 0.35 * (dx * 0.6 - dy * 0.8) - 0.4 * np.clip(r2 - 0.75, 0, 1) - 0.25 * dent
    lad = [ST[1], ST[2], ST[3], ST[4], ST[5], SN[1]]
    T = np.clip(shade, 0, 0.999) * len(lad)
    idx = np.floor(T).astype(int)
    idx = np.clip(idx + ((T - idx) > bayer(W, H)), 0, len(lad) - 1)
    L.c[disc] = np.stack(lad)[idx][disc]
    rim = disc & (r2 > 0.86)
    L.c[rim & (dx + dy < 0)] = ST[2]
    L.c[rim & (dx - dy > 0.6)] = SN[2]
    outer = (r2 > 1.0) & (r2 < 1.12)
    L.c[outer & (dy > -0.2)] = NI[3]                    # cast shadow lower left
    # crimp jaw texture on the left/right lugs
    for k in range(6):
        L.hline(cx - rx - 1, cy - 8 + k * 3, 4, ST[1])
        L.hline(cx + rx - 2, cy - 8 + k * 3, 4, ST[3])
    marks = {}
    # doubled stamp: station code + number stamped twice, offset (embossed relief)
    def emboss(x, y, s, hi, lo, body, font='s'):
        f = FONT_S if font == 's' else FONT_L
        cx_ = x
        for ch in s:
            if ch == ' ':
                cx_ += 3
                continue
            g = f[ch]
            for r, row in enumerate(g):
                for c, v in enumerate(row):
                    if v == '#':
                        L.px(cx_ + c + 1, y + r + 1, lo)
            for r, row in enumerate(g):
                for c, v in enumerate(row):
                    if v == '#':
                        L.px(cx_ + c, y + r, body)
                        if r == 0 or row[c - 1:c] == '.':
                            L.px(cx_ + c, y + r, hi)
            cx_ += len(g[0]) + 1
        return cx_ - x

    def strike(x, y, s, body, lo, keep=1.0, seed=0):
        r_ = np.random.default_rng(seed)
        cx_ = x
        for ch in s:
            if ch == ' ':
                cx_ += 3
                continue
            g = FONT_S[ch]
            for r, row in enumerate(g):
                for c, v in enumerate(row):
                    if v == '#' and r_.random() < keep:
                        L.px(cx_ + c, y + r, body)
                        if lo is not None:
                            L.px(cx_ + c + 1, y + r + 1, lo)
            cx_ += len(g[0]) + 1
        return cx_ - x

    w1 = strike(82, 71, 'КРС 0412', ST[3], None, keep=0.8, seed=2)      # second strike, offset ghost
    strike(80, 69, 'КРС 0412', ST[1], SN[2], keep=1.0, seed=1)           # first strike, crisp engraved
    marks['double_stamp'] = {'rect': [78, 68, w1 + 8, 12],
                             'note': 'station code + number struck twice (offset strike)'}
    # abrasion: scraped band across the lower half, fresh bright lead, scratches
    band = disc & (yy > 82) & (yy < 112) & ((xx - cx) * 0.35 + (yy - 97) < 10) & ((xx - cx) * 0.35 + (yy - 97) > -12)
    lad2 = [ST[4], ST[5], SN[1], SN[2]]
    nz2 = value_noise(W, H, 3, seed=9, octaves=2)
    idx2 = np.clip((nz2 * 3.99).astype(int), 0, 3)
    L.c[band] = np.stack(lad2)[idx2][band]
    for k in range(14):                                 # scratch strokes
        x0 = 72 + int(rng.integers(0, 60))
        y0 = 84 + int(rng.integers(0, 24))
        ln = int(rng.integers(5, 14))
        for j in range(ln):
            x, y = x0 + j, y0 - j // 3
            if 0 <= y < H and disc[y, x]:
                L.px(x, y, ST[3] if (j % 2) else SN[3])
    # C-17 underneath, revealed by the abrasion (engraved: dark letters, light lower edge)
    cxs = 86
    for ch in 'C-17':
        g = FONT_L[ch]
        for r, row in enumerate(g):
            for c, v in enumerate(row):
                if v == '#':
                    L.px(cxs + c * 2, 89 + r * 2, ST[1])
                    L.px(cxs + c * 2 + 1, 89 + r * 2, ST[1])
                    L.px(cxs + c * 2, 89 + r * 2 + 1, ST[0])
                    L.px(cxs + c * 2 + 1, 89 + r * 2 + 1, ST[1])
                    L.px(cxs + c * 2 + 1, 89 + r * 2 + 2, SN[2]) if r == 6 or g[min(6, r + 1)][c] == '.' else None
        cxs += len(g[0]) * 2 + 2
    marks['c17'] = {'rect': [84, 87, cxs - 84, 18], 'note': "'C-17' visible under the abrasion"}
    # three shapes scratched into the paint beside the seal: square, circle, triangle (in this order)
    sx0, sy0 = 146, 104
    scratch = SN[0]
    groove = RU[0]
    # square 8x8
    for k in range(8):
        for (x, y) in ((sx0 + k, sy0), (sx0 + k, sy0 + 7), (sx0, sy0 + k), (sx0 + 7, sy0 + k)):
            L.px(x, y, scratch)
            L.px(x + 1, y + 1, groove) if (x, y) != (sx0 + 7, sy0 + 7) else None
    # circle r 4.5
    ccx, ccy = sx0 + 18, sy0 + 4
    for a in range(0, 360, 12):
        x = int(round(ccx + math.cos(math.radians(a)) * 4.4))
        y = int(round(ccy + math.sin(math.radians(a)) * 4.4))
        L.px(x, y, scratch)
    for a in range(30, 160, 20):
        L.px(int(round(ccx + math.cos(math.radians(a)) * 5.3)), int(round(ccy + math.sin(math.radians(a)) * 5.3)), groove)
    # triangle 9 wide, 8 tall
    tx, ty = sx0 + 26, sy0
    L.line(tx + 4, ty, tx, ty + 7, scratch)
    L.line(tx + 4, ty, tx + 8, ty + 7, scratch)
    L.hline(tx, ty + 7, 9, scratch)
    L.hline(tx + 1, ty + 8, 9, groove)
    marks['shapes'] = {'rect': [sx0 - 1, sy0 - 1, 37, 11], 'order': ['square', 'circle', 'triangle'],
                       'note': 'scratched beside the seal, left to right'}
    marks['shape_square'] = {'rect': [sx0, sy0, 8, 8]}
    marks['shape_circle'] = {'rect': [ccx - 5, ccy - 5, 11, 11]}
    marks['shape_triangle'] = {'rect': [tx, ty, 9, 8]}
    marks['seal'] = {'rect': [cx - rx, cy - ry, 2 * rx, 2 * ry], 'note': 'lead seal disc, dented'}
    # thin snow line on the hasp top
    for x in range(14, 124):
        L.px(x, 29, SN[3] if x % 5 else SN[2])
    L.outline(NI[1], outer=False)
    return save_doc(L, 'karsk_seal.png', marks, {
        'id': 'karsk_seal', 'alt_key': 'doc.karsk.seal.alt', 'item_id': 'ev_damaged_seal', 'objective': 'a1_inspect_seal', 'hotspot': 'seal',
        'title_key': 'item.seal.name', 'description_key': 'item.seal.description',
        'describes': 'Close-up of the dented lead seal on the C-17 wagon door: a station stamp struck twice, '
                     'an abraded band revealing C-17, three small shapes scratched beside it (square, circle, '
                     'triangle).'})


# =========================================================================== TIMETABLE
def make_timetable():
    W, H = 300, 200
    L = Layer(W, H, 'karsk_timetable')
    rng = np.random.default_rng(202)
    # wooden frame
    L.rect(0, 0, W, H, WO[2])
    for y in range(0, H, 3):
        L.hline(0, y, W, WO[1]) if (y // 3) % 4 == 0 else None
    L.rect(0, 0, W, 2, WO[3])
    L.rect(W - 2, 0, 2, H, WO[3])
    L.rect(0, H - 2, W, 2, WO[0])
    L.rect(0, 0, 2, H, WO[1])
    for (x, y) in ((5, 5), (W - 7, 5), (5, H - 7), (W - 7, H - 7)):
        L.rect(x, y, 3, 3, ST[2])
        L.px(x + 2, y, ST[4])
        L.vline(x + 1, y + 3, 7, RU[2])
    # snow on the top edge
    for x in range(W):
        d = 1 + int(2 * (0.5 + 0.5 * math.sin(x / 13.0)) + (x % 7 == 0))
        for k in range(d):
            L.px(x, k, SN[3] if k == 0 else SN[2])
    # enamel board face
    bx, by, bw, bh = 10, 10, W - 20, H - 20
    L.rect(bx, by, bw, bh, TE[1])
    nz = value_noise(bw, bh, 8, seed=4, octaves=3)
    m = nz > 0.66
    L.c[by:by + bh, bx:bx + bw][m] = TE[0]
    chips = nz > 0.78
    L.c[by:by + bh, bx:bx + bw][chips] = RU[1]
    for _ in range(30):                                  # enamel chips with rust rings
        x = bx + int(rng.integers(2, bw - 4))
        y = by + int(rng.integers(2, bh - 4))
        L.rect(x, y, 2, 2, RU[1])
        L.px(x + 2, y + 1, RU[2])
    # header band: emblem + painted title (scribble) + date line
    L.rect(bx + 4, by + 4, bw - 8, 18, TE[2])
    L.hline(bx + 4, by + 21, bw - 8, SN[1])
    L.ellipse(bx + 16, by + 13, 6, 6, SN[2])
    L.ellipse(bx + 16, by + 13, 3, 3, TE[2])
    for a in range(0, 360, 45):
        L.px(int(bx + 16 + math.cos(math.radians(a)) * 5), int(by + 13 + math.sin(math.radians(a)) * 5), TE[2])
    scribble_print(L, bx + 28, by + 7, 150, SN[3], rng, wear=0.05)
    scribble_print(L, bx + 28, by + 14, 90, SN[1], rng, wear=0.1)
    scribble_digits(L, bx + bw - 60, by + 10, '1964', SN[2], rng)
    # column headers + grid
    cols = [bx + 4, bx + 36, bx + 120, bx + 210, bx + bw - 4]
    hy = by + 26
    for i in range(4):
        scribble_print(L, cols[i] + 3, hy, cols[i + 1] - cols[i] - 6, SN[1], rng, wear=0.15)
    L.hline(bx + 4, hy + 7, bw - 8, SN[1])
    for x in cols[1:-1]:
        L.vline(x, hy - 2, bh - 32, SN[0])
    rows_y = list(range(hy + 11, by + bh - 8, 12))
    rebooked = {3: 'square', 5: 'circle', 7: 'triangle'}
    marks = {}
    for i, ry in enumerate(rows_y):
        L.hline(bx + 4, ry + 9, bw - 8, TE[0])
        if i in rebooked:
            continue
        scribble_digits(L, cols[0] + 4, ry + 2, '%d%02d' % (int(rng.integers(1, 9)), int(rng.integers(0, 99))), SN[2], rng)
        scribble_digits(L, cols[1] + 4, ry + 2, '%02d-%03d' % (int(rng.integers(10, 99)), int(rng.integers(0, 999))),
                        SN[2], rng)
        scribble_print(L, cols[2] + 4, ry + 2, 80, SN[2], rng, wear=0.12)
        scribble_digits(L, cols[3] + 6, ry + 2, '%02d:%02d' % (int(rng.integers(0, 24)), int(rng.integers(0, 60))),
                        SN[2], rng)
    # the three re-booked wagon lines: pasted paper strips, new wagon numbers in pencil,
    # destination field left EMPTY, symbol in the left margin: square, circle, triangle (top->bottom)
    for order, (i, sym) in enumerate(sorted(rebooked.items())):
        ry = rows_y[i]
        sx0, sx1 = cols[0] + 1, cols[3] - 2
        paper_fill(L, sx0, ry, sx1 - sx0, 10, seed=50 + i, base=2.2)
        L.hline(sx0, ry + 10, sx1 - sx0, TE[0])
        scribble_digits(L, cols[0] + 16, ry + 3, '%d%02d' % (int(rng.integers(1, 9)), int(rng.integers(0, 99))), INK, rng)
        scribble_hand(L, cols[1] + 4, ry + 1, 70, TE[0], rng, xh=3, asc=2, max_words=3)
        # destination: deliberately empty -- a long dash only
        L.hline(cols[2] + 30, ry + 5, 24, ST[2])
        # (time column on the strip left blank too)
        # symbol in the margin, chalk white, legible at 1:1
        mx, my = cols[0] + 3, ry + 1
        if sym == 'square':
            for k in range(8):
                L.px(mx + k, my, NI[1]); L.px(mx + k, my + 7, NI[1]); L.px(mx, my + k, NI[1]); L.px(mx + 7, my + k, NI[1])
            rect = [mx, my, 8, 8]
        elif sym == 'circle':
            ccx, ccy = mx + 4, my + 4
            for a in range(0, 360, 10):
                L.px(int(round(ccx + math.cos(math.radians(a)) * 3.6)), int(round(ccy + math.sin(math.radians(a)) * 3.6)), NI[1])
            rect = [mx, my, 9, 9]
        else:
            L.line(mx + 4, my, mx, my + 7, NI[1])
            L.line(mx + 4, my, mx + 8, my + 7, NI[1])
            L.hline(mx, my + 7, 9, NI[1])
            rect = [mx, my, 9, 8]
        marks['line_%d_%s' % (order + 1, sym)] = {'rect': [sx0, ry, sx1 - sx0, 10], 'symbol': sym,
                                                 'symbol_rect': rect, 'order': order + 1,
                                                 'destination_rect': [cols[2] + 2, ry, cols[3] - cols[2] - 4, 10]}
    marks['symbols_order'] = ['square', 'circle', 'triangle']
    # handwritten note pinned at the bottom right corner (scribble) + rust streaks
    paper_fill(L, bx + bw - 70, by + bh - 24, 60, 20, seed=77)
    for k in range(3):
        scribble_hand(L, bx + bw - 66, by + bh - 23 + k * 6, 52, INK, rng, xh=2, asc=1, max_words=3)
    L.rect(bx + bw - 42, by + bh - 26, 3, 3, ST[3])
    for _ in range(12):
        x = bx + int(rng.integers(0, bw))
        L.vline(x, by + bh - int(rng.integers(4, 18)), int(rng.integers(3, 12)), RU[1])
    L.outline(NI[1], outer=False)
    return save_doc(L, 'karsk_timetable.png', marks, {
        'id': 'karsk_timetable', 'alt_key': 'doc.karsk.timetable.alt', 'item_id': 'ev_timetable', 'objective': 'a1_inspect_timetable',
        'hotspot': 'timetable', 'title_key': 'item.timetable.name', 'description_key': 'item.timetable.description',
        'describes': 'Worn enamel timetable board. Three re-booked wagon lines are pasted over with paper strips; '
                     'their destination fields are empty. In the margin they are marked, top to bottom, with a '
                     'square, a circle and a triangle (puzzle order).'})


# =========================================================================== LEDGER
def make_ledger():
    W, H = 320, 200
    L = Layer(W, H, 'karsk_ledger')
    rng = np.random.default_rng(303)
    # desk (dark wood) + book binding + page
    L.rect(0, 0, W, H, WO[1])
    for y in range(0, H, 4):
        L.hline(0, y, W, WO[0]) if rng.random() < 0.5 else None
    L.rect(8, 6, W - 14, H - 10, NI[2])                  # cover edge
    L.rect(14, 8, W - 22, H - 14, SK[3])                 # page block edge
    paper_fill(L, 18, 8, W - 26, H - 16, seed=12, base=2.4)
    for y in range(8, H - 8):                            # gutter shadow
        L.px(18, y, SK[2]); L.px(19, y, SK[3])
        if y % 2:
            L.px(20, y, SK[3])
    # printed ruling
    left, right = 26, W - 14
    hy = 16
    cols = [left, left + 30, left + 72, left + 130, left + 196, left + 248, right]
    L.rect(left, hy, right - left, 10, SK[4])
    for i in range(len(cols) - 1):
        scribble_print(L, cols[i] + 2, hy + 2, cols[i + 1] - cols[i] - 4, TE[3], rng, wear=0.1)
    L.hline(left, hy + 10, right - left, TE[3])
    L.hline(left, hy + 11, right - left, TE[3])
    for x in cols[1:-1]:
        L.vline(x, hy, H - 34, SK[1])
    rows = list(range(hy + 14, H - 22, 11))
    for ry in rows:
        L.hline(left, ry + 9, right - left, SK[2])
    marks = {}
    # older entries in faded ink (handwriting scribbles), dates as digits
    new_row = len(rows) - 1
    for i, ry in enumerate(rows):
        if i == new_row:
            continue
        ink = TE[1] if i % 3 else TE[2]
        scribble_digits(L, cols[0] + 2, ry + 2, '%02d.01' % (2 + i), ink, rng, wear=0.1)
        scribble_digits(L, cols[1] + 3, ry + 2, '%02d-%03d' % (int(rng.integers(10, 99)), int(rng.integers(0, 999))), ink, rng)
        scribble_hand(L, cols[2] + 3, ry, 52, ink, rng, xh=3, asc=2, max_words=2)
        scribble_hand(L, cols[3] + 3, ry, 60, ink, rng, xh=3, asc=2, max_words=3)
        scribble_hand(L, cols[4] + 3, ry, 46, ink, rng, xh=3, asc=2, max_words=2)
        scribble_hand(L, cols[5] + 4, ry, 30, ink, rng, xh=2, asc=3, max_words=1)
        if rng.random() < 0.3:                           # tick marks
            L.line(cols[5] + 38, ry + 4, cols[5] + 40, ry + 6, ink)
            L.line(cols[5] + 40, ry + 6, cols[5] + 44, ry + 1, ink)
    # the NEW line: fresher dark ink, recipient blacked out, red C-17 stamp
    ry = rows[new_row]
    L.rect(left + 1, ry, right - left - 2, 9, SN[3])     # slightly erased / rewritten (paper scuffed)
    scribble_digits(L, cols[0] + 2, ry + 2, '14.01', INK, rng, wear=0.0)
    scribble_digits(L, cols[1] + 3, ry + 2, '24-311', INK, rng, wear=0.0)
    scribble_hand(L, cols[2] + 3, ry, 50, INK, rng, xh=3, asc=2, max_words=2)
    scribble_hand(L, cols[3] + 3, ry, 56, INK, rng, xh=3, asc=2, max_words=2)
    # recipient: heavy black marker bar with ragged ends
    bx0, bx1 = cols[4] + 2, cols[5] - 3
    L.rect(bx0, ry, bx1 - bx0, 9, NI[0])
    for x in (bx0 - 1, bx1):
        for y in range(ry + 1, ry + 8):
            if rng.random() < 0.6:
                L.px(x, y, NI[0])
    for _ in range(6):
        L.px(bx0 + int(rng.integers(0, bx1 - bx0)), ry + int(rng.integers(0, 9)), NI[2])
    marks['recipient_blacked_out'] = {'rect': [bx0 - 1, ry, bx1 - bx0 + 2, 9]}
    scribble_hand(L, cols[5] + 4, ry, 30, INK, rng, xh=2, asc=3, max_words=1)
    marks['new_line'] = {'rect': [left, ry, right - left, 10], 'wagon': '24-311'}
    # red C-17 stamp: double frame, letters at 2x, slight ink starvation; overlaps the line like a
    # real stamp but the letters stay fully legible at 1:1
    sx, sy, sw, sh = cols[2] + 4, ry - 10, 64, 24
    srng = np.random.default_rng(31)
    L.rect(sx + 3, sy + 3, sw - 6, sh - 6, SN[3])           # stamp pressed over the scuffed paper
    for k in range(sw):
        for (y, c) in ((sy, RED[2]), (sy + sh - 1, RED[2]), (sy + 2, RED[1]), (sy + sh - 3, RED[1])):
            if srng.random() > 0.07:
                L.px(sx + k, y, c)
    for k in range(sh):
        for (x, c) in ((sx, RED[2]), (sx + sw - 1, RED[2])):
            if srng.random() > 0.07:
                L.px(x, sy + k, c)
        if 2 <= k < sh - 2:
            for x in (sx + 2, sx + sw - 3):
                if srng.random() > 0.1:
                    L.px(x, sy + k, RED[1])
    tx = sx + 7
    ty = sy + 5
    for ch in 'C-17':
        g = FONT_L[ch]
        for r, row in enumerate(g):
            for c, v in enumerate(row):
                if v == '#':
                    for (ddx, ddy) in ((0, 0), (1, 0), (0, 1), (1, 1)):
                        if srng.random() > 0.05:
                            L.px(tx + c * 2 + ddx, ty + r * 2 + ddy, RED[3] if ddy == 0 else RED[2])
        tx += len(g[0]) * 2 + 3
    tw = tx - (sx + 7) - 3
    marks['c17_stamp'] = {'rect': [sx, sy, sw, sh], 'text_rect': [sx + 7, sy + 5, tw, 14], 'color': 'red'}
    # small details: tea ring stain, thumb smudge, page number
    for a in range(0, 360, 6):
        r = 13 + (a % 30 == 0)
        L.px(int(250 + math.cos(math.radians(a)) * r), int(150 + math.sin(math.radians(a)) * r * 0.8), CO[3])
    for k in range(10):
        L.px(int(rng.integers(40, 60)), int(rng.integers(160, 172)), SK[2])
    scribble_digits(L, W - 34, H - 16, '47', TE[2], rng)
    # page corner curl at the bottom right
    for k in range(10):
        L.hline(W - 16 - k, H - 9 - (9 - k), k + 1, SK[2] if k < 9 else SK[1])
    L.outline(NI[1], outer=False)
    return save_doc(L, 'karsk_ledger.png', marks, {
        'id': 'karsk_ledger', 'alt_key': 'doc.karsk.ledger.alt', 'item_id': 'ev_ledger', 'objective': 'a1_inspect_ledger', 'hotspot': 'ledger',
        'title_key': 'item.ledger.name', 'description_key': 'item.ledger.description',
        'describes': 'Freight ledger page, Cyrillic handwriting. One new line (wagon 24-311) carries a red C-17 '
                     'stamp; the recipient field is blacked out.'})


# =========================================================================== TEACHING BOARD
def make_signal_board():
    W, H = 260, 180
    L = Layer(W, H, 'karsk_signal_board')
    rng = np.random.default_rng(404)
    # cabinet shell (teal steel), open door edge on the left, inner pale panel
    L.rect(0, 0, W, H, TE[1])
    L.rect(0, 0, W, 3, TE[3])
    L.rect(W - 3, 0, 3, H, TE[4])
    L.rect(0, 0, 14, H, TE[2])                          # open door edge (seen from the side)
    L.vline(13, 0, H, TE[0])
    for y in (30, 140):
        L.rect(3, y, 8, 10, ST[3])                       # hinges
        L.hline(3, y, 8, ST[4])
    px0, py0, pw, ph = 22, 10, W - 32, H - 20
    L.rect(px0, py0, pw, ph, ST[4])
    nz = value_noise(pw, ph, 18, seed=6, octaves=2)
    L.c[py0:py0 + ph, px0:px0 + pw][nz > 0.7] = ST[3]
    L.rect(px0, py0, pw, 1, ST[5])
    L.rect(px0, py0 + ph - 1, pw, 1, ST[2])
    for (x, y) in ((px0 + 3, py0 + 3), (px0 + pw - 5, py0 + 3), (px0 + 3, py0 + ph - 5), (px0 + pw - 5, py0 + ph - 5)):
        L.rect(x, y, 2, 2, ST[1])
    marks = {}
    # title plate (pixel scribble) + readable small plate 'УЧЕБНЫЙ' (= training) in the corner
    L.rect(px0 + 8, py0 + 6, pw - 16, 13, TE[0])
    scribble_print(L, px0 + 14, py0 + 10, pw - 70, SN[2], rng, wear=0.05)
    L.rect(px0 + pw - 54, py0 + 8, 44, 9, CO[4])
    text(L, px0 + pw - 52, py0 + 10, 'УЧЕБНЫЙ', RED[1], font='s')
    marks['training_plate'] = {'rect': [px0 + pw - 54, py0 + 8, 44, 9], 'text': 'УЧЕБНЫЙ (training)'}
    # demonstration diagram (fictional): 3 numbered slots -> dashed line -> lamp, example with OTHER shapes
    dx, dy = px0 + 10, py0 + 26
    L.rect(dx, dy, 96, 40, SN[3])
    L.hline(dx, dy, 96, ST[2]); L.hline(dx, dy + 39, 96, ST[2]); L.vline(dx, dy, 40, ST[2]); L.vline(dx + 95, dy, 40, ST[2])
    for k in range(3):
        bx = dx + 8 + k * 22
        L.rect(bx, dy + 12, 14, 16, ST[3])
        L.rect(bx + 1, dy + 13, 12, 14, SN[2])
        text(L, bx + 5, dy + 5, str(k + 1), NI[2], font='s')
        cx, cy = bx + 7, dy + 20
        if k == 0:     # cross
            L.line(cx - 3, cy - 3, cx + 3, cy + 3, NI[2]); L.line(cx - 3, cy + 3, cx + 3, cy - 3, NI[2])
        elif k == 1:   # diamond
            for (a, b) in (((cx, cy - 4), (cx + 4, cy)), ((cx + 4, cy), (cx, cy + 4)), ((cx, cy + 4), (cx - 4, cy)),
                           ((cx - 4, cy), (cx, cy - 4))):
                L.line(a[0], a[1], b[0], b[1], NI[2])
        else:          # star-ish asterisk
            L.vline(cx, cy - 4, 9, NI[2]); L.hline(cx - 4, cy, 9, NI[2])
            L.px(cx - 2, cy - 2, NI[2]); L.px(cx + 2, cy + 2, NI[2]); L.px(cx + 2, cy - 2, NI[2]); L.px(cx - 2, cy + 2, NI[2])
        if k < 2:
            for x in range(bx + 15, bx + 21, 2):
                L.px(x, cy, NI[2])
    for x in range(dx + 74, dx + 82, 2):
        L.px(x, dy + 20, NI[2])
    L.ellipse(dx + 87, dy + 20, 4, 4, ST[2])           # example lamp
    L.ellipse(dx + 87, dy + 20, 2.5, 2.5, CO[4])
    L.px(dx + 87, dy + 19, SN[4])
    marks['demo_diagram'] = {'rect': [dx, dy, 96, 40],
                             'note': 'fictional example: order of three cards -> lamp; uses cross/diamond/'
                                     'asterisk so it never shows the solution'}
    scribble_print(L, dx + 102, dy + 4, pw - 124, ST[1], rng, wear=0.1)
    scribble_print(L, dx + 102, dy + 12, pw - 130, ST[1], rng, wear=0.1)
    scribble_print(L, dx + 102, dy + 20, pw - 140, ST[1], rng, wear=0.1)
    # dead indicator lamp (unpowered) + cut cable
    lx, ly = px0 + pw - 24, py0 + 50
    L.ellipse(lx, ly, 8, 8, ST[1])
    L.ellipse(lx, ly, 6, 6, TE[2])
    L.ellipse(lx, ly, 3, 3, TE[3])
    L.px(lx + 2, ly - 3, SN[2])
    marks['dead_lamp'] = {'rect': [lx - 8, ly - 8, 17, 17], 'note': 'unlit indicator: board has no power'}
    # three EMPTY card slots
    sy = py0 + 76
    for k in range(3):
        sx = px0 + 22 + k * 64
        L.rect(sx - 3, sy - 3, 46, 62, ST[2])
        L.rect(sx - 3, sy - 3, 46, 1, ST[1])
        L.rect(sx, sy, 40, 56, NI[2])
        L.rect(sx, sy, 40, 2, NI[0])
        L.rect(sx + 38, sy, 2, 56, NI[3])
        L.rect(sx + 4, sy + 52, 32, 4, ST[3])            # card rail
        L.hline(sx + 4, sy + 52, 32, ST[5])
        L.rect(sx + 14, sy - 2, 12, 3, ST[1])            # slot clip
        text(L, sx + 18, sy - 12 if sy - 12 > py0 + 66 else sy - 10, str(k + 1), NI[2], font='s')
        L.px(sx + 6, sy + 6, NI[3])                      # faint ghost of an old card corner
        L.hline(sx + 6, sy + 6, 6, NI[3])
        L.vline(sx + 6, sy + 6, 6, NI[3])
        marks['slot_%d' % (k + 1)] = {'rect': [sx, sy, 40, 56]}
    # cut cable hanging at the bottom (not connected)
    for k in range(18):
        L.px(px0 + pw - 30 + (k // 6), py0 + ph - 2 + k // 9 - 18 + k, NI[1])
    L.rect(px0 + pw - 28, py0 + ph - 4, 3, 2, RU[3])
    L.px(px0 + pw - 26, py0 + ph - 3, ST[5])
    marks['cut_cable'] = {'rect': [px0 + pw - 31, py0 + ph - 20, 8, 20]}
    # scuffs and rust
    for _ in range(40):
        x = px0 + int(rng.integers(0, pw - 2))
        y = py0 + int(rng.integers(0, ph - 2))
        if not (py0 + 70 < y < py0 + 136):
            L.px(x, y, ST[2])
    L.outline(NI[1], outer=False)
    return save_doc(L, 'karsk_signal_board.png', marks, {
        'id': 'karsk_signal_board', 'alt_key': 'doc.karsk.signal_board.alt', 'puzzle_id': 'pz_signal', 'objective': 'a1_solve_signal',
        'hotspot': 'signal_board', 'title_key': 'doc.karsk.signal_board.title',
        'describes': "Inside of the disconnected, unpowered TEACHING board ('Übungskasten', plate УЧЕБНЫЙ): "
                     'three empty card slots, a dead indicator lamp, a cut cable and a small fictional '
                     'demonstration diagram (example uses cross/diamond/asterisk, never the solution).'})


def build_all():
    docs = [make_seal(), make_timetable(), make_ledger(), make_signal_board()]
    out = {'scene': 'L_A1_Railyard', 'palette': 'karsk (+ shared C-17 red accent)', 'generator':
           'tools/pixelgen/env_karsk_docs.py (via env_karsk.py)', 'date': '2026-11-04',
           'note': 'Pixel art drawn 1:1, shown at 3x (nearest). Text is scribble; the UI overlays HD text. '
                   'All rects are [x, y, w, h] in document pixels.',
           'documents': docs}
    with open(os.path.join(DOC_DIR, 'karsk_documents.json'), 'w', encoding='utf-8') as f:
        json.dump(out, f, indent=1, ensure_ascii=False)
    print('documents:', ', '.join(d['id'] for d in docs))
    return out


if __name__ == '__main__':
    build_all()
