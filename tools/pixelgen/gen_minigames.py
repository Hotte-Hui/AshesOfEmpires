"""gen_minigames -- original pixel art for the three optional mini-games (TECHNICAL_ARCHITECTURE 12.8).

Run:  py -3 -P tools/pixelgen/gen_minigames.py        (Pillow + numpy, deterministic, no downloads)

Writes assets/ui/minigames/ (UI art is drawn at 1:1 and STORED x3, nearest -- like assets/ui/frames):
  shunt_yard.png            Karsk "Rangieren": snowy yard seen from above (headshunt, 3 sidings, 2 points)
  shunt_engine.png, shunt_wagon_{box,coal,flat,tank}.png   top-down vehicles, facing right (36x12 / 34x12)
  shunt_lever_{0,1}.png     hand-throw point lever (0 = straight, 1 = thrown)
  shunt_layout.json         route polylines / lever spots / vehicle pitch in ART px (x1) for the script
  chess_board.png           Karsk "Die Schachpartie": peg-chess board laid on a crate lid (squares 20 px)
  chess_pieces.png          sheet 6x2 (K Q R B N P; row 0 day shift = light birch, row 1 night shift = dark)
  radio.png                 Berlin "Das Radio": 1955 table radio, glass scale, magic-eye bezel, piano keys
  radio_eye.png             8 frames of the magic eye (0 = no signal, 7 = tuned)
  radio_knob.png            8 frames of the tuning knob
  radio_newspaper.png       the porter's newspaper (overlay on his portrait)
  radio_layout.json         scale / eye / knob / key positions in ART px (x1)
No regime insignia anywhere (12.4): the mini-game UI never shows them.
"""
from __future__ import annotations

import json
import math
import os
import zlib

import numpy as np
from PIL import Image

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
OUT = os.path.join(ROOT, 'assets', 'ui', 'minigames')
X = 3
PAL = json.load(open(os.path.join(ROOT, 'data', 'palettes.json'), encoding='utf-8'))
BAYER = np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]) / 16.0


def hx(h: str, a: int = 255):
    h = h.lstrip('#')
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), a)


def P(area: str, ramp: str, i: int):
    return hx(PAL[area][ramp][i])


def rng(name: str):
    return np.random.default_rng(zlib.crc32(name.encode()))


class Canvas:
    def __init__(self, w: int, h: int, bg=(0, 0, 0, 0)):
        self.w, self.h = w, h
        self.a = np.zeros((h, w, 4), np.uint8)
        self.a[:, :] = bg

    def px(self, x, y, c):
        x, y = int(round(x)), int(round(y))
        if 0 <= x < self.w and 0 <= y < self.h:
            self.a[y, x] = c

    def get(self, x, y):
        return tuple(int(v) for v in self.a[y, x])

    def rect(self, x0, y0, x1, y1, c):
        """filled, inclusive-exclusive"""
        x0, y0, x1, y1 = max(0, int(x0)), max(0, int(y0)), min(self.w, int(x1)), min(self.h, int(y1))
        if x1 > x0 and y1 > y0:
            self.a[y0:y1, x0:x1] = c

    def frame(self, x0, y0, x1, y1, c):
        self.rect(x0, y0, x1, y0 + 1, c)
        self.rect(x0, y1 - 1, x1, y1, c)
        self.rect(x0, y0, x0 + 1, y1, c)
        self.rect(x1 - 1, y0, x1, y1, c)

    def line(self, x0, y0, x1, y1, c):
        x0, y0, x1, y1 = int(round(x0)), int(round(y0)), int(round(x1)), int(round(y1))
        dx, dy = abs(x1 - x0), -abs(y1 - y0)
        sx, sy = (1 if x0 < x1 else -1), (1 if y0 < y1 else -1)
        err = dx + dy
        while True:
            self.px(x0, y0, c)
            if x0 == x1 and y0 == y1:
                return
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x0 += sx
            if e2 <= dx:
                err += dx
                y0 += sy

    def disc(self, cx, cy, r, c):
        for y in range(int(cy - r - 1), int(cy + r + 2)):
            for x in range(int(cx - r - 1), int(cx + r + 2)):
                if (x - cx) ** 2 + (y - cy) ** 2 <= r * r:
                    self.px(x, y, c)

    def outline(self, c, src_alpha=1):
        """1 px outer outline around opaque pixels"""
        m = self.a[:, :, 3] >= src_alpha
        o = np.zeros_like(m)
        o[1:, :] |= m[:-1, :]
        o[:-1, :] |= m[1:, :]
        o[:, 1:] |= m[:, :-1]
        o[:, :-1] |= m[:, 1:]
        o &= ~m
        self.a[o] = c

    def paste(self, other: 'Canvas', ox, oy):
        for y in range(other.h):
            for x in range(other.w):
                c = other.a[y, x]
                if c[3] > 0:
                    self.px(ox + x, oy + y, tuple(int(v) for v in c))

    def save(self, name: str):
        os.makedirs(OUT, exist_ok=True)
        im = Image.fromarray(self.a, 'RGBA').resize((self.w * X, self.h * X), Image.NEAREST)
        im.save(os.path.join(OUT, name), optimize=True)


def save_json(name: str, data):
    with open(os.path.join(OUT, name), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(data, f, indent=1)
        f.write('\n')


# ================================================================================ Karsk: shunting yard
YARD_W, YARD_H = 360, 150
Y1, Y2, Y3 = 30, 74, 118
H_START = 14           # left buffer stop of the headshunt (vehicles start here)
W1 = (140, Y1)         # toe of points 1 (straight -> siding 1, thrown -> points 2)
W2 = (200, Y2)         # toe of points 2 (straight -> siding 2, thrown -> siding 3)
BUF = {'1': 296, '2': 306, '3': 346}   # buffer stops (x) of the sidings
PITCH = 40             # vehicle length incl. couplers (art px)

ROUTES = {
    '1': [[H_START, Y1], [BUF['1'], Y1]],
    '2': [[H_START, Y1], [W1[0], Y1], [W1[0] + 44, Y2], [BUF['2'], Y2]],
    '3': [[H_START, Y1], [W1[0], Y1], [W1[0] + 44, Y2], [W2[0], Y2], [W2[0] + 44, Y3], [BUF['3'], Y3]],
}


def walk(poly, step=1.0):
    """yield (x, y, tx, ty) every `step` px along a polyline"""
    for (x0, y0), (x1, y1) in zip(poly, poly[1:]):
        L = math.hypot(x1 - x0, y1 - y0)
        n = max(1, int(L / step))
        tx, ty = (x1 - x0) / L, (y1 - y0) / L
        for i in range(n):
            yield x0 + tx * i * L / n, y0 + ty * i * L / n, tx, ty


def yard():
    c = Canvas(YARD_W, YARD_H)
    r = rng('yard')
    snow = [P('karsk', 'snow', i) for i in range(5)]
    # snow field with soft dithered drifts (lighter towards the top, trodden grey near the tracks)
    for y in range(YARD_H):
        for x in range(YARD_W):
            v = 0.55 + 0.25 * math.sin(x * 0.045 + y * 0.02) * math.sin(y * 0.07 + 1.3) + r.normal(0, 0.06)
            k = 2 if v + BAYER[y % 4, x % 4] * 0.25 > 0.62 else 1
            if v > 0.86:
                k = 3
            c.px(x, y, snow[k])
    # trodden slush paths along the tracks and a walkway at the bottom
    for poly in ROUTES.values():
        for x, y, tx, ty in walk(poly, 1.0):
            for d in range(-9, 10):
                if abs(d) > 6 and r.random() < 0.55:
                    c.px(x - ty * d, y + tx * d, snow[0] if r.random() < 0.3 else snow[1])
    for x in range(YARD_W):
        for y in range(140, 147):
            if (x + y * 3) % 7 and r.random() < 0.7:
                c.px(x, y, snow[0] if r.random() < 0.25 else snow[1])
    # ballast beds
    stone = [P('karsk', 'stone', i) for i in range(6)]
    for poly in ROUTES.values():
        for x, y, tx, ty in walk(poly, 0.5):
            for d in np.arange(-5.5, 6.0, 0.5):
                q = r.random()
                col = stone[3] if q < 0.45 else stone[2] if q < 0.8 else stone[4]
                if q > 0.93:
                    col = snow[2]
                c.px(x - ty * d, y + tx * d, col)
    # sleepers every 4 px
    wood = [P('karsk', 'wood', i) for i in range(5)]
    for poly in ROUTES.values():
        acc = 0.0
        for x, y, tx, ty in walk(poly, 1.0):
            acc += 1
            if acc % 4:
                continue
            for d in range(-5, 6):
                c.px(x - ty * d, y + tx * d, wood[1])
                c.px(x - ty * d + tx, y + tx * d + ty, wood[2] if d % 3 else wood[0])
            if r.random() < 0.35:   # snow left on a sleeper end
                c.px(x - ty * 5, y + tx * 5, snow[3])
    # rails (gauge 6 px): dark web + polished head highlight
    rail_d, rail_l = P('karsk', 'stone', 1), P('karsk', 'snow', 2)
    for poly in ROUTES.values():
        for x, y, tx, ty in walk(poly, 0.25):
            for side in (-3, 3):
                px, py = x - ty * side, y + tx * side
                c.px(px, py, rail_d)
                c.px(px - ty * 0.0, py - 1 if abs(tx) > 0.9 else py, rail_l if abs(tx) > 0.9 else rail_d)
    # buffer stops: wooden beam on a mound, red/white end board
    red, white = P('archive', 'ink', 3), snow[4]

    def buffer_stop(bx, by, facing):
        for dy in range(-6, 7):
            for dx in range(0, 4):
                c.px(bx + dx * facing, by + dy, wood[2] if dx < 2 else wood[1])
        for dy in range(-6, 7):
            c.px(bx - facing, by + dy, red if (dy // 2) % 2 else white)
        c.rect(min(bx + 4 * facing, bx + 7 * facing), by - 7, max(bx + 4 * facing, bx + 7 * facing) + 1, by + 8, stone[2])
    buffer_stop(H_START - 2, Y1, -1)
    buffer_stop(BUF['1'] + 2, Y1, 1)
    buffer_stop(BUF['2'] + 2, Y2, 1)
    buffer_stop(BUF['3'] + 2, Y3, 1)
    # track number boards (digits 3x5) beside the buffer stops
    digits = {'1': ['.#.', '##.', '.#.', '.#.', '###'], '2': ['##.', '..#', '.#.', '#..', '###'],
              '3': ['##.', '..#', '.#.', '..#', '##.']}
    for t, (bx, by) in {'1': (BUF['1'] - 8, Y1 - 19), '2': (BUF['2'] - 8, Y2 - 19), '3': (BUF['3'] - 8, Y3 - 19)}.items():
        c.rect(bx - 1, by - 1, bx + 6, by + 8, P('karsk', 'night', 2))
        c.frame(bx - 1, by - 1, bx + 6, by + 8, wood[0])
        for yy, row in enumerate(digits[t]):
            for xx, ch in enumerate(row):
                if ch == '#':
                    c.px(bx + 1 + xx, by + 1 + yy, snow[4])
        c.rect(bx + 2, by + 8, bx + 3, by + 11, wood[0])   # post
    # a stack of spare sleepers and dry grass tufts poking through the snow
    for i in range(4):
        c.rect(26, 104 + i * 4, 70, 107 + i * 4, wood[2 if i % 2 else 3])
        c.rect(26, 107 + i * 4, 70, 108 + i * 4, wood[0])
        c.rect(26 + 2 * i, 104 + i * 4, 30 + 2 * i, 105 + i * 4, snow[3])
    sage = [P('karsk', 'sage', i) for i in range(6)]
    for i in range(46):
        gx, gy = int(r.integers(4, YARD_W - 4)), int(r.integers(4, YARD_H - 4))
        if any(abs(gy - yy) < 9 for yy in (Y1, Y2, Y3)):
            continue
        for k in range(3):
            c.line(gx + k - 1, gy, gx + k - 1 + int(r.integers(-1, 2)), gy - 2 - int(r.integers(0, 2)), sage[1 + k % 2])
    # footprints of the shunter along the headshunt
    for i in range(14):
        fx, fy = 22 + i * 9, Y1 + 13 + (i % 2) * 3
        c.px(fx, fy, snow[0])
        c.px(fx + 1, fy, snow[0])
    # fence along the top edge
    for x in range(0, YARD_W, 1):
        c.px(x, 6, P('karsk', 'stone', 1) if x % 2 else P('karsk', 'stone', 0))
        c.px(x, 9, P('karsk', 'stone', 1))
        if x % 14 == 3:
            c.rect(x, 3, x + 2, 12, wood[1])
            c.px(x, 3, snow[4])
    c.save('shunt_yard.png')
    save_json('shunt_layout.json', {
        '_doc': 'Karsk shunting mini-game layout in ART px (the PNGs are stored x3). Routes run from the '
                'headshunt buffer (left) to the siding buffer stops; vehicles are placed by arc length.',
        'size': [YARD_W, YARD_H], 'pitch': PITCH, 'routes': ROUTES,
        'levers': {'1': [W1[0] - 6, Y1 - 24], '2': [W2[0] - 6, Y2 - 24]},
        'switch_points': {'1': list(W1), '2': list(W2)},
        'siding_labels': {'1': [BUF['1'] - 8, Y1 - 19], '2': [BUF['2'] - 8, Y2 - 19], '3': [BUF['3'] - 8, Y3 - 19]},
        'buffers': BUF})


def vehicle(kind: str):
    w = 34 if kind == 'engine' else 36
    c = Canvas(w, 12)
    snow = [P('karsk', 'snow', i) for i in range(5)]
    r = rng('veh_' + kind)
    dark = P('karsk', 'night', 0)
    beam = P('archive', 'ink', 3)
    grey = P('karsk', 'stone', 4)
    if kind == 'engine':
        # cab + bunker at the rear (left), boiler with dome and chimney forward (right)
        c.rect(1, 1, w - 1, 11, P('karsk', 'teal', 0))
        c.rect(2, 2, 6, 10, P('karsk', 'night', 1))                 # coal bunker
        for i in range(6):
            c.px(2 + i % 4, 3 + (i * 3) % 7, P('karsk', 'stone', 3))
        c.rect(6, 1, 15, 11, P('karsk', 'stone', 1))                # cab roof
        c.rect(6, 1, 15, 2, P('karsk', 'stone', 3))
        c.rect(7, 2, 14, 3, P('karsk', 'stone', 2))
        c.rect(15, 3, w - 3, 9, P('karsk', 'teal', 1))               # boiler
        c.rect(15, 3, w - 3, 5, P('karsk', 'teal', 3))
        c.rect(15, 5, w - 3, 6, P('karsk', 'teal', 2))
        c.rect(15, 2, w - 3, 3, P('karsk', 'stone', 2))              # running boards
        c.rect(15, 9, w - 3, 10, P('karsk', 'stone', 2))
        c.disc(21, 5.5, 1.6, P('karsk', 'teal', 4))                   # dome
        c.px(21, 5, P('karsk', 'sage', 5))
        c.disc(w - 7, 5.5, 1.8, dark)                                 # chimney
        c.px(w - 7, 5, P('karsk', 'stone', 0))
        c.rect(w - 4, 3, w - 3, 9, P('karsk', 'stone', 3))           # smokebox door ring
        c.rect(0, 1, 1, 11, beam)
        c.rect(w - 1, 1, w, 11, beam)
        for x in (1, 14, 15):
            c.px(x, 0, snow[3])
        c.px(9, 1, snow[4])
        c.px(10, 1, snow[3])
        c.px(13, 2, snow[4])
    else:
        c.rect(1, 1, w - 1, 11, P('karsk', 'night', 2))
        if kind == 'box':
            c.rect(2, 1, w - 2, 11, P('karsk', 'rust', 3))
            for x in range(3, w - 2, 3):
                c.rect(x, 1, x + 1, 11, P('karsk', 'rust', 2))
            c.rect(2, 5, w - 2, 7, P('karsk', 'rust', 4))             # roof ridge
            c.rect(2, 6, w - 2, 7, P('karsk', 'rust', 2))
            for i in range(26):                                        # snow on the roof
                x, y = int(r.integers(2, w - 2)), int(r.integers(1, 11))
                c.px(x, y, snow[3 if y < 6 else 2])
            c.rect(14, 1, 22, 3, snow[4])
            c.rect(16, 3, 21, 4, snow[3])
        elif kind == 'coal':
            c.rect(1, 1, w - 1, 11, P('karsk', 'stone', 2))
            c.rect(2, 2, w - 2, 10, P('karsk', 'night', 1))
            for y in range(2, 10):
                for x in range(2, w - 2):
                    hgt = 1 - abs(y - 5.5) / 5 - abs(x - w / 2) / (w * 0.9)
                    if hgt + r.normal(0, 0.12) > 0.45:
                        c.px(x, y, P('karsk', 'night', 3))
                    if r.random() < 0.08:
                        c.px(x, y, P('karsk', 'stone', 3))
            for i in range(14):
                c.px(int(r.integers(3, w - 3)), int(r.integers(3, 9)), snow[3])
            for x in range(2, w - 2, 6):
                c.rect(x, 1, x + 1, 11, P('karsk', 'stone', 1))
        elif kind == 'flat':
            c.rect(1, 2, w - 1, 10, P('karsk', 'wood', 3))
            for y in range(2, 10, 2):
                c.rect(1, y, w - 1, y + 1, P('karsk', 'wood', 2))
            for i, (x0, x1) in enumerate(((3, 17), (19, 33))):
                c.rect(x0, 2, x1, 10, P('karsk', 'stone', 4))
                c.rect(x0, 2, x1, 3, P('karsk', 'stone', 5))
                c.frame(x0, 2, x1, 10, P('karsk', 'stone', 2))
                c.rect(x0 + 2, 5, x1 - 2, 7, P('karsk', 'stone', 3))       # window opening of the wall panel
                c.rect(x0 + 1, 2, x0 + 4, 3, snow[4])
            for x in (10, 26):
                c.rect(x, 1, x + 1, 11, P('karsk', 'rust', 1))           # straps
        elif kind == 'tank':
            c.rect(1, 1, w - 1, 11, P('karsk', 'night', 1))
            c.rect(3, 2, w - 3, 10, P('karsk', 'stone', 0))
            c.rect(2, 3, 3, 9, P('karsk', 'stone', 0))
            c.rect(w - 3, 3, w - 2, 9, P('karsk', 'stone', 0))
            c.rect(3, 3, w - 3, 5, P('karsk', 'stone', 2))
            c.rect(3, 4, w - 3, 5, P('karsk', 'stone', 3))
            c.disc(w / 2 - 0.5, 5.5, 2.2, P('karsk', 'stone', 1))      # dome
            c.px(w // 2 - 1, 4, P('karsk', 'stone', 4))
            c.rect(3, 6, w - 3, 7, P('karsk', 'wood', 2))               # walkway
            for i in range(10):
                c.px(int(r.integers(4, w - 4)), int(r.integers(2, 5)), snow[3])
        c.rect(0, 1, 1, 11, P('karsk', 'night', 3))
        c.rect(w - 1, 1, w, 11, P('karsk', 'night', 3))
    for y in (2, 9):                                                  # buffers
        c.px(0, y, grey)
        c.px(w - 1, y, grey)
    c.save('shunt_%s.png' % ('engine' if kind == 'engine' else 'wagon_' + kind))


def lever(state: int):
    c = Canvas(14, 22)
    dark = P('karsk', 'night', 1)
    c.rect(3, 15, 11, 21, P('karsk', 'stone', 1))                     # stand
    c.rect(3, 15, 11, 16, P('karsk', 'stone', 3))
    c.rect(4, 19, 10, 21, P('karsk', 'night', 2))
    # indicator lantern on a post: white bar along (straight) or across (thrown) the track
    c.rect(6, 6, 8, 15, P('karsk', 'stone', 0))
    c.rect(3, 1, 11, 7, dark)
    c.rect(4, 2, 10, 6, P('karsk', 'teal', 0))
    lamp = P('karsk', 'copper', 4)
    if state == 0:
        c.rect(6, 2, 8, 6, lamp)
    else:
        c.rect(4, 3, 10, 5, lamp)
    # lever arm with counterweight
    if state == 0:
        c.line(7, 16, 1, 13, P('karsk', 'stone', 4))
        c.disc(1.5, 13.5, 1.6, P('karsk', 'night', 0))
    else:
        c.line(7, 16, 12, 13, P('karsk', 'stone', 4))
        c.disc(12.5, 13.5, 1.6, P('karsk', 'night', 0))
    c.px(3, 15, P('karsk', 'snow', 4))
    c.px(4, 15, P('karsk', 'snow', 3))
    c.px(3, 1, P('karsk', 'snow', 4))
    c.save('shunt_lever_%d.png' % state)


# ================================================================================ Karsk: chess
SQ = 19
BOARD_OFF = 10


def chess_board():
    n = SQ * 8 + BOARD_OFF * 2
    c = Canvas(n, n)
    r = rng('crate')
    wood = [P('karsk', 'wood', i) for i in range(5)]
    snow = [P('karsk', 'snow', i) for i in range(5)]
    # crate lid: horizontal planks with grain and nails
    plank_h = n // 5
    for p in range(5):
        y0 = p * plank_h
        base = 2 + (p % 2)
        for y in range(y0, min(n, y0 + plank_h)):
            for x in range(n):
                g = math.sin(x * 0.11 + p * 2.1 + math.sin(y * 0.6 + p) * 1.4)
                k = base + (1 if g > 0.75 else -1 if g < -0.7 else 0)
                c.px(x, y, wood[max(0, min(4, k))])
        c.rect(0, y0, n, y0 + 1, wood[0])
        for nx in (4, n - 5):
            c.px(nx, y0 + 3, P('karsk', 'stone', 4))
            c.px(nx, y0 + plank_h - 4, P('karsk', 'stone', 4))
    c.frame(0, 0, n, n, wood[0])
    # the board (painted squares, peg holes)
    light, light2 = P('archive', 'paper', 3), P('archive', 'paper', 2)
    darkq, darkq2 = P('archive', 'wood', 2), P('archive', 'wood', 1)
    c.rect(BOARD_OFF - 3, BOARD_OFF - 3, BOARD_OFF + SQ * 8 + 3, BOARD_OFF + SQ * 8 + 3, P('archive', 'wood', 0))
    c.frame(BOARD_OFF - 2, BOARD_OFF - 2, BOARD_OFF + SQ * 8 + 2, BOARD_OFF + SQ * 8 + 2, P('archive', 'wood', 4))
    for fy in range(8):
        for fx in range(8):
            is_light = (fx + fy) % 2 == 0      # fy 0 = rank 8 (top); a8 is light
            x0, y0 = BOARD_OFF + fx * SQ, BOARD_OFF + fy * SQ
            for y in range(SQ):
                for x in range(SQ):
                    worn = r.random() < 0.05
                    if is_light:
                        col = light2 if worn or (x + y * 2) % 11 == 0 else light
                    else:
                        col = darkq2 if worn or (x * 2 + y) % 13 == 0 else darkq
                    c.px(x0 + x, y0 + y, col)
            hx_, hy_ = x0 + SQ // 2 - 1, y0 + SQ // 2 - 1       # peg hole
            hole = P('archive', 'wood', 0)
            c.rect(hx_, hy_, hx_ + 2, hy_ + 2, hole)
            c.px(hx_ + 1, hy_ + 1, light2 if is_light else darkq)
    # snow dust in the lid corners
    for i in range(70):
        x, y = int(r.integers(0, n)), int(r.integers(0, n))
        if BOARD_OFF - 3 <= x < BOARD_OFF + SQ * 8 + 3 and BOARD_OFF - 3 <= y < BOARD_OFF + SQ * 8 + 3:
            continue
        c.px(x, y, snow[3 if i % 3 else 4])
    c.save('chess_board.png')


# 16 x 19 masks: '#' body; shading is derived (light from the upper left)
PIECES = {
    'K': ["................", ".......##.......", "......####......", ".......##.......", ".....######.....",
          "....########....", "....########....", ".....######.....", "......####......", "......####......",
          "......####......", ".....######.....", "......####......", "......####......", ".....######.....",
          "....########....", "...##########...", "...##########...", "................"],
    'Q': ["................", ".......##.......", "...#..####..#...", "...##.####.##...", "....########....",
          "....########....", ".....######.....", "......####......", "......####......", "......####......",
          "......####......", ".....######.....", "......####......", "......####......", ".....######.....",
          "....########....", "...##########...", "...##########...", "................"],
    'R': ["................", "................", "................", "....##.##.##....", "....########....",
          "....########....", ".....######.....", ".....######.....", ".....######.....", ".....######.....",
          ".....######.....", ".....######.....", ".....######.....", ".....######.....", "....########....",
          "....########....", "...##########...", "...##########...", "................"],
    'B': ["................", ".......##.......", "......####......", ".....###.##.....", ".....##.###.....",
          ".....######.....", "......####......", "......####......", ".....######.....", "......####......",
          "......####......", "......####......", "......####......", "......####......", ".....######.....",
          "....########....", "...##########...", "...##########...", "................"],
    'N': ["................", "................", ".......##.......", "......####......", ".....######.....",
          "....########....", "...###.######...", "..##########....", "..#########.....", "...##.#####.....",
          "......######....", ".....#######....", ".....#######....", ".....#######....", ".....#######....",
          "....########....", "...##########...", "...##########...", "................"],
    'P': ["................", "................", "................", "................", "................",
          "................", ".......##.......", "......####......", "......####......", ".......##.......",
          "......####......", ".......##.......", ".......##.......", "......####......", ".....######.....",
          "....########....", "...##########...", "...##########...", "................"],
}
ORDER = ['K', 'Q', 'R', 'B', 'N', 'P']


def chess_pieces():
    cw, ch = 18, 20
    sheet = Canvas(cw * 6, ch * 2)
    ramps = {
        0: [hx('#6E4A37'), hx('#B57B59'), hx('#E6DEC2'), hx('#F5EFDA'), hx('#D79A62')],   # birch, day shift
        1: [hx('#04090D'), hx('#1A1C2A'), hx('#3D2820'), hx('#55372A'), hx('#805C4E')],   # stained, night shift
    }
    for row in (0, 1):
        sh, mid, hi, top, rim = ramps[row]
        for i, k in enumerate(ORDER):
            c = Canvas(cw, ch)
            m = PIECES[k]
            for y, line in enumerate(m):
                for x, chx in enumerate(line):
                    if chx != '#':
                        continue
                    # local shading: left edge + upper rows light, right edge shaded
                    left = x == 0 or line[x - 1] != '#'
                    right = x == len(line) - 1 or line[x + 1] != '#'
                    col = mid
                    if left:
                        col = top if row == 0 else rim
                    elif right:
                        col = sh
                    elif x < 8:
                        col = hi if row == 0 else mid
                    c.px(x + 1, y, col)
            if k == 'N':          # eye of the knight
                c.px(7, 6, sh if row == 0 else rim)
            c.outline(P('archive', 'night', 0))
            c.rect(3, ch - 2, cw - 3, ch - 1, (0, 0, 0, 0))
            sheet.paste(c, i * cw, row * ch)
    sheet.save('chess_pieces.png')


# ================================================================================ Berlin: the radio
RW, RH = 288, 146
SCALE = (22, 82, 266, 104)      # glass dial rect (x0, y0, x1, y1)
REICH_F, FOREIGN_F = 0.24, 0.83  # scale fractions (mirrored in scripts/ui/minigames/radio_logic.gd)
EYE = (236, 28)
KNOB = (258, 126)
KNOB_L = (30, 126)
KEYS_X0, KEY_W, KEY_GAP, KEYS_Y = 92, 18, 3, 114


def radio():
    c = Canvas(RW, RH)
    wood = [P('archive', 'wood', i) for i in range(6)]
    amber = [P('archive', 'amber', i) for i in range(6)]
    paper = [P('archive', 'paper', i) for i in range(6)]
    night = P('archive', 'night', 0)
    r = rng('radio')
    # cabinet with rounded top corners and walnut grain
    for y in range(RH - 6):
        for x in range(RW):
            rad = 14
            if y < rad and (x < rad or x >= RW - rad):
                cx = rad if x < rad else RW - rad - 1
                if (x - cx) ** 2 + (y - rad) ** 2 > rad * rad:
                    continue
            g = math.sin(x * 0.05 + math.sin(y * 0.09) * 2.2) + 0.5 * math.sin(x * 0.17 + y * 0.03)
            k = 3 + (1 if g > 0.9 else -1 if g < -0.6 else 0)
            if y < 4 or x < 3:
                k = 4
            if y > RH - 12 or x > RW - 4:
                k = 1
            c.px(x, y, wood[k])
    c.outline(night)
    # feet
    for fx in (24, RW - 34):
        c.rect(fx, RH - 6, fx + 10, RH - 1, P('archive', 'night', 1))
    # gold trim line
    c.rect(10, 76, RW - 10, 77, amber[3])
    c.rect(10, 77, RW - 10, 78, amber[1])
    # fabric grille (woven, warm) inside a chrome frame
    gx0, gy0, gx1, gy1 = 18, 12, RW - 18, 72
    c.rect(gx0 - 2, gy0 - 2, gx1 + 2, gy1 + 2, amber[2])
    c.frame(gx0 - 2, gy0 - 2, gx1 + 2, gy1 + 2, amber[0])
    for y in range(gy0, gy1):
        for x in range(gx0, gx1):
            weave = ((x // 2) + (y // 2)) % 2
            v = 0.5 + 0.3 * math.sin(x * 0.04) + 0.15 * math.sin(y * 0.2) + r.normal(0, 0.05)
            col = paper[2] if weave else paper[1]
            if v > 0.78:
                col = paper[3]
            if v < 0.28:
                col = paper[0]
            c.px(x, y, col)
    # three vertical wooden ribs over the grille (the classic look; no emblem)
    for rx in (92, 144, 196):
        c.rect(rx, gy0 - 2, rx + 4, gy1 + 2, wood[2])
        c.rect(rx, gy0 - 2, rx + 1, gy1 + 2, wood[4])
    # magic-eye bezel (the eye itself is radio_eye.png, drawn by the UI)
    c.disc(EYE[0], EYE[1], 11, amber[1])
    c.disc(EYE[0], EYE[1], 10, amber[4])
    c.disc(EYE[0] - 1, EYE[1] - 1, 9, amber[2])
    c.disc(EYE[0], EYE[1], 8.2, night)
    # glass dial scale: cream glass, black frame, ticks, the house-rule red line and the pencil dot
    x0, y0, x1, y1 = SCALE
    c.rect(x0 - 3, y0 - 3, x1 + 3, y1 + 3, P('archive', 'night', 2))
    c.rect(x0, y0, x1, y1, paper[4])
    for y in range(y0, y1):
        for x in range(x0, x1):
            if (x - y * 2) % 37 in (0, 1) and r.random() < 0.8:
                c.px(x, y, paper[5])           # glass reflection streaks
    c.rect(x0, y1 - 7, x1, y1 - 6, P('archive', 'ink', 0))
    span = x1 - x0 - 8
    for i in range(0, 61):
        tx = x0 + 4 + round(i * span / 60)
        h = 4 if i % 5 == 0 else 2
        c.rect(tx, y1 - 6, tx + 1, y1 - 6 + h, P('archive', 'ink', 0))
    rx = x0 + 4 + round(REICH_F * span)
    c.rect(rx, y0 + 1, rx + 1, y1 - 7, P('archive', 'ink', 3))
    fx = x0 + 4 + round(FOREIGN_F * span)
    c.rect(fx, y0 + 4, fx + 2, y0 + 6, P('archive', 'ink', 1))
    c.px(fx + 2, y0 + 5, paper[2])
    # piano keys (5); the UI labels them
    for i in range(5):
        kx = KEYS_X0 + i * (KEY_W + KEY_GAP)
        c.rect(kx, KEYS_Y, kx + KEY_W, KEYS_Y + 14, paper[5])
        c.rect(kx, KEYS_Y + 11, kx + KEY_W, KEYS_Y + 14, paper[3])
        c.frame(kx - 1, KEYS_Y - 1, kx + KEY_W + 1, KEYS_Y + 15, P('archive', 'night', 1))
    # volume knob (static); the tuning knob is radio_knob.png
    c.disc(KNOB_L[0], KNOB_L[1], 9, P('archive', 'night', 1))
    c.disc(KNOB_L[0] - 1, KNOB_L[1] - 1, 7, P('archive', 'wood', 1))
    c.rect(KNOB_L[0] - 1, KNOB_L[1] - 8, KNOB_L[0] + 1, KNOB_L[1] - 4, amber[4])
    c.disc(KNOB[0], KNOB[1], 10, P('archive', 'night', 1))
    c.save('radio.png')
    save_json('radio_layout.json', {
        '_doc': 'Berlin radio mini-game layout in ART px (radio.png is stored x3). scale = glass dial rect; the '
                'needle runs between scale_x0 and scale_x1 (fractions 0..1 of the band).',
        'size': [RW, RH], 'scale': list(SCALE), 'scale_x0': x0 + 4, 'scale_x1': x0 + 4 + span,
        'reich': REICH_F, 'foreign': FOREIGN_F, 'eye': list(EYE), 'knob': list(KNOB),
        'keys': [[KEYS_X0 + i * (KEY_W + KEY_GAP), KEYS_Y, KEY_W, 14] for i in range(5)]})


def radio_eye():
    n = 18
    sheet = Canvas(n * 8, n)
    green_d, green, green_l = hx('#1F5A3A'), hx('#3FA86A'), hx('#9CF0B4')
    for f in range(8):
        s = f / 7.0
        shadow = math.radians(14 + (1 - s) * 120)       # dark wedge opening at the top
        for y in range(n):
            for x in range(n):
                dx, dy = x - n / 2 + 0.5, y - n / 2 + 0.5
                d = math.hypot(dx, dy)
                if d > 8.0:
                    continue
                ang = abs(math.atan2(dx, -dy))
                if d < 2.2:
                    col = P('archive', 'night', 1)
                elif ang < shadow / 2:
                    col = hx('#0B2A1C')
                else:
                    col = green_l if d < 4.0 else green if d < 6.6 else green_d
                    if abs(ang - shadow / 2) < 0.18:
                        col = green_l
                sheet.px(f * n + x, y, col)
    sheet.save('radio_eye.png')


def radio_knob():
    n = 24
    sheet = Canvas(n * 8, n)
    for f in range(8):
        a = f / 8.0 * 2 * math.pi
        for y in range(n):
            for x in range(n):
                dx, dy = x - n / 2 + 0.5, y - n / 2 + 0.5
                d = math.hypot(dx, dy)
                if d > 10.5:
                    continue
                col = P('archive', 'wood', 1) if d < 9.5 else P('archive', 'night', 0)
                if d < 9.5 and dx + dy < -4:
                    col = P('archive', 'wood', 2)
                # knurled rim
                if 8.0 < d < 9.5 and int((math.atan2(dy, dx) + math.pi) / (2 * math.pi) * 24 + f * 3) % 2:
                    col = P('archive', 'wood', 0)
                sheet.px(f * n + x, y, col)
        # pointer notch
        for k in range(3, 9):
            px_ = n / 2 - 0.5 + math.sin(a) * k
            py_ = n / 2 - 0.5 - math.cos(a) * k
            sheet.px(f * n + px_, py_, P('archive', 'amber', 4))
    sheet.save('radio_knob.png')


def newspaper():
    w, h = 104, 64
    c = Canvas(w, h)
    r = rng('newspaper')
    paper_l, paper_m, paper_d = hx('#DEE5DC'), hx('#C4CFC8'), hx('#A3B1AD')
    ink = hx('#4F534C')
    c.rect(4, 2, w - 4, h, paper_l)
    c.rect(w // 2, 2, w // 2 + 1, h, paper_d)                       # fold
    c.rect(w // 2 + 1, 2, w // 2 + 3, h, paper_m)
    c.rect(8, 6, w // 2 - 4, 13, hx('#3B3F3B'))                    # masthead block (no text, no symbols)
    c.rect(8, 15, w // 2 - 4, 16, ink)
    for col0, col1, top in ((8, 28, 19), (31, 48, 19), (w // 2 + 5, w - 8, 6)):
        y = top
        while y < h - 3:
            if r.random() < 0.15:
                c.rect(col0, y, col1, y + 2, hx('#666A60'))            # sub-heading
                y += 4
                continue
            ln = int(r.integers(col1 - col0 - 6, col1 - col0 + 1))
            for x in range(col0, col0 + ln):
                if r.random() < 0.82:
                    c.px(x, y, ink if r.random() < 0.6 else hx('#7F8275'))
            y += 3
    c.rect(w // 2 + 6, 30, w - 9, 46, hx('#7F8275'))                 # a photo block
    c.rect(w // 2 + 7, 31, w - 10, 38, hx('#9A9B8B'))
    c.frame(4, 2, w - 4, h, paper_d)
    # fingers holding the paper (porter's hands)
    skin = [P('archive', 'skin', i) for i in range(3)]
    for fx, base in ((0, 22), (w - 6, 22)):
        for i in range(4):
            c.rect(fx, base + i * 5, fx + 6, base + i * 5 + 4, skin[1])
            c.rect(fx, base + i * 5 + 3, fx + 6, base + i * 5 + 4, skin[0])
            c.rect(fx + (0 if fx else 4), base + i * 5, fx + (2 if fx else 6), base + i * 5 + 1, skin[2])
    c.save('radio_newspaper.png')


def main():
    yard()
    for k in ('engine', 'box', 'coal', 'flat', 'tank'):
        vehicle(k)
    lever(0)
    lever(1)
    chess_board()
    chess_pieces()
    radio()
    radio_eye()
    radio_knob()
    newspaper()
    print('gen_minigames: wrote', sorted(os.listdir(OUT)))


if __name__ == '__main__':
    main()
