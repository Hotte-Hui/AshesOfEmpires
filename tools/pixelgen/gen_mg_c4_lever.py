"""gen_mg_c4_lever -- art for the Chapter-4 mini-game "Der Hebelrahmen" (Service Tunnel 3 under the Karsk freight
yard, Alexei; owner: exploration c4, TECHNICAL_ARCHITECTURE §12.8, documentation/C4_DESIGN.md §6).

    py -3 -P tools/pixelgen/gen_mg_c4_lever.py          (then import under the shared lock)

Writes assets/ui/minigames/lever/ at 1:1 art pixels (the game draws everything x3, or x2 for larger text):
  lever_back.png       400x148  the tunnel niche at W2: formwork concrete in cage-lamp light; the enamel track diagram
                                („Gleisbild“) on the wall -- tunnel 3, points 1-3, track 1 with wagon 24 318, track 2,
                                the main line and a fourth track whose label is taped over; the dark route indicator
                                box and the two signal lamp sockets; below it the cast-iron lever frame of 1941: the
                                slot bank, brass number plates 1-8 with lock pip sockets, a dark strip for the German
                                labels, the night shift's route book on a nail, the painted locking table on the wall
  lever_indicator.png  3 x 64x9 the lit texts of the route indicator: „ПУТЬ 1“ (route a), „ГЛАВН.“ (route b),
                                „КОРДОН 17“ (route c, the reveal)
  lever_closeup.png    200x120  close-up for the find (DiscoveryView, x3): the indicator lit „КОРДОН 17“ above the lit
                                track 0, the tape peeled back from „ПУТЬ 0“, the bright-worn handle of lever 6
  lever_layout.json    canvas size and every coordinate the game draws over the art (lever x, slot, handle travel,
                       plates, lock pips, label strip, track polylines, routes, points branches, signals, indicator);
                       the rule itself lives in scripts/ui/minigames/lever_logic.gd (tests/test_c4_explore.gd checks
                       both agree)
Deterministic (seeds = crc32 of names). Colours: data/chapters/c4.json palette "tunnels"; outside it only the enamel
green of the diagram board (BOARD, four documented values) -- the signal green and the moon-white route light are
drawn by the game (scripts/ui/minigames/lever_game.gd, documented there). Fonts: the hand-made bitmap fonts of
mg_r7_v_kit (SMALL 5x7 with the Cyrillic letters used here, TINY 3x5 digits) -- no font file is read.
"""
from __future__ import annotations

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import mg_r7_v_kit as K  # noqa: E402

OUT = os.path.join(K.ROOT, 'assets', 'ui', 'minigames', 'lever')
_C4 = json.load(open(os.path.join(K.ROOT, 'data', 'chapters', 'c4.json'), encoding='utf-8'))
_P = _C4['palettes']['tunnels']


def T(ramp: str, i: int, a: int = 255):
    return K.hx(_P[ramp][i], a)


BOARD = [K.hx(h) for h in ('#0E1914', '#15241C', '#1E3226', '#2A4434')]   # enamel green of the track diagram

W, H = 400, 148
LEVERS = ['w1', 'w2', 'w3', 'a', 'b', 'c', 's1', 's2']
LEVER_X = [60 + 40 * i for i in range(8)]
SLOT_Y = 100
HANDLE_Y = [64, 84]          # handle top: normal (upright, away from the operator) / reversed (pulled over)
PLATE_Y = (107, 118)
LABEL_RECT = [44, 121, 312, 14]
PIP = (5, 109)               # lock pip: offset from the lever x, top y (2x2)
BOARD_RECT = [8, 4, 384, 56]
IND_CELL = (64, 9)
IND_AT = (16, 9)
SIGNALS = {'s1': [91, 24], 's2': [243, 24]}
WAGON = [150, 28, 28, 4]
TRACKS = {
    'tunnel': [[16, 32], [100, 32]],
    't1': [[100, 32], [268, 32]],
    't2': [[100, 32], [114, 46], [254, 46], [268, 32]],
    'exit': [[268, 32], [300, 32]],
    'main': [[300, 32], [384, 32]],
    'zero': [[300, 32], [316, 16], [384, 16]],
}
ROUTES = {
    'a': [[16, 32], [100, 32], [236, 32]],
    'b': [[180, 32], [268, 32], [300, 32], [384, 32]],
    'c': [[180, 32], [268, 32], [300, 32], [316, 16], [384, 16]],
}
BRANCHES = {   # points lever -> [normal branch, reversed branch]
    'w1': [[[100, 32], [114, 32]], [[100, 32], [114, 46]]],
    'w2': [[[254, 32], [268, 32]], [[254, 46], [268, 32]]],
    'w3': [[[300, 32], [314, 32]], [[300, 32], [314, 18]]],
}
INDICATOR_TEXT = {'a': 'ПУТЬ 1', 'b': 'ГЛАВН.', 'c': 'КОРДОН 17'}


def seg_pixels(pts):
    out = []
    for (x0, y0), (x1, y1) in zip(pts[:-1], pts[1:]):
        n = max(abs(x1 - x0), abs(y1 - y0))
        for i in range(n + 1):
            t = i / max(1, n)
            p = (int(round(x0 + (x1 - x0) * t)), int(round(y0 + (y1 - y0) * t)))
            if not out or out[-1] != p:
                out.append(p)
    return out


def wall(cv: K.Cv) -> None:
    r = K.rng('lever_wall')
    cv.vgrad(0, 0, W, H, T('night', 3), T('iron', 1))
    for y in range(9, H, 11):                                   # formwork board marks
        for x in range(W):
            if r.random() < 0.82:
                cv.px(x, y, T('iron', 2), 0.35)
    for x0 in (52, 118, 196, 262, 338):                         # formwork seams
        for y in range(H):
            if r.random() < 0.7:
                cv.px(x0, y, T('night', 2), 0.5)
    for _ in range(26):                                         # water stains running down
        x = int(r.integers(4, W - 4))
        y = int(r.integers(0, 60))
        for k in range(int(r.integers(6, 30))):
            cv.px(x + (1 if r.random() < 0.15 else 0), y + k, T('night', 1), 0.45)
    for y in range(0, 100):                                     # the cage lamp's pool of light on the concrete
        for x in range(0, 230):
            d = ((x - 24) / 210.0) ** 2 + ((y + 4) / 96.0) ** 2
            if d < 1.0 and K.BAYER[y % 4, x % 4] < (1.0 - d) * 0.75:
                cv.px(x, y, T('iron', 2))
            if d < 0.35 and K.BAYER[(y + 2) % 4, (x + 1) % 4] < (0.35 - d) * 1.4:
                cv.px(x, y, T('iron', 3))
    cv.rect(2, 0, 10, 3, T('iron', 3))                          # the cage lamp itself, top left
    cv.rect(3, 3, 9, 7, T('lamp', 3))
    cv.rect(4, 4, 8, 6, T('lamp', 4))
    for xx in (3, 5, 7, 9):
        cv.rect(xx, 3, xx + 1, 8, T('iron', 1))


def board(cv: K.Cv) -> None:
    x, y, w, h = BOARD_RECT
    cv.rect(x, y, x + w, y + h, T('wagon', 1))                  # wooden frame
    cv.rect(x + 1, y + 1, x + w - 1, y + 2, T('wagon', 3))
    cv.rect(x + 2, y + 2, x + w - 2, y + h - 2, BOARD[1])
    r = K.rng('lever_board')
    for yy in range(y + 2, y + h - 2):                          # enamel, slightly clouded
        for xx in range(x + 2, x + w - 2):
            v = r.random()
            if v < 0.05:
                cv.px(xx, yy, BOARD[0])
            elif v > 0.97:
                cv.px(xx, yy, BOARD[2])
    cv.rect(x + 2, y + 2, x + w - 2, y + 3, BOARD[3])
    for sx, sy in ((x + 3, y + 3), (x + w - 4, y + 3), (x + 3, y + h - 4), (x + w - 4, y + h - 4)):
        cv.px(sx, sy, T('iron', 4))
    # tracks, painted dim (the game lights what is set)
    for name, pts in TRACKS.items():
        for p in seg_pixels(pts):
            cv.px(p[0], p[1], T('paper', 1))
    for p in (100, 268, 300):                                   # points blades
        cv.px(p, 33, T('paper', 2))
    K.text(cv, 96, 36, '1', T('paper', 2), 'tiny')
    K.text(cv, 265, 36, '2', T('paper', 2), 'tiny')
    K.text(cv, 297, 36, '3', T('paper', 2), 'tiny')
    # wagon 24 318 standing on track 1
    wx, wy, ww, wh = WAGON
    cv.rect(wx, wy, wx + ww, wy + wh, T('wagon', 2))
    cv.rect(wx, wy, wx + ww, wy + 1, T('wagon', 4))
    cv.rect(wx, wy + wh - 1, wx + ww, wy + wh, T('wagon', 0))
    cv.px(wx + 4, wy + wh, T('iron', 4))
    cv.px(wx + ww - 5, wy + wh, T('iron', 4))
    # labels in white paint
    K.text(cv, 16, 36, 'ТОННЕЛЬ 3', T('paper', 3), 'small')
    K.text(cv, 186, 22, 'ПУТЬ 1', T('paper', 3), 'small')
    K.text(cv, 160, 49, 'ПУТЬ 2', T('paper', 3), 'small')
    K.text(cv, 340, 36, 'ГЛАВН.', T('paper', 3), 'small')
    K.text(cv, 330, 7, 'ПУТЬ 0', T('paper', 3), 'small')
    tape = (326, 5, 372, 15)                                    # grey tape over track 0's label
    cv.rect(tape[0], tape[1], tape[2], tape[3], T('paper', 1))
    cv.dither_rect(tape[0], tape[1], tape[2], tape[3], T('paper', 2), 0.3)
    cv.rect(tape[0], tape[3] - 1, tape[2], tape[3], T('paper', 0))
    for k in range(4):                                          # a torn corner, the paint shows through a little
        cv.px(tape[2] - 1 - k, tape[1] + k, BOARD[1])
    # route indicator box (dark until a route is set) and the signal lamp sockets
    ix, iy = IND_AT
    cv.rect(ix - 2, iy - 2, ix + IND_CELL[0] + 2, iy + IND_CELL[1] + 2, T('iron', 3))
    cv.rect(ix - 1, iy - 1, ix + IND_CELL[0] + 1, iy + IND_CELL[1] + 1, T('night', 0))
    for s, (sx, sy) in SIGNALS.items():
        cv.rect(sx + 1, sy + 3, sx + 2, 32, T('iron', 3))      # mast
        cv.rect(sx - 1, sy - 1, sx + 4, sy + 4, T('iron', 3))
        cv.rect(sx, sy, sx + 3, sy + 3, T('night', 0))


def frame(cv: K.Cv) -> None:
    r = K.rng('lever_frame')
    # the painted locking table on the wall (decorative; the readable one is in the side panel)
    cv.rect(10, 66, 36, 94, T('paper', 2))
    cv.frame(10, 66, 36, 94, T('paper', 1))
    for yy in (72, 79, 86):
        cv.rect(11, yy, 35, yy + 1, T('paper', 1))
    for xx in (17, 23, 29):
        cv.rect(xx, 67, xx + 1, 93, T('paper', 1))
    cv.dither_rect(10, 84, 36, 94, T('night', 2), 0.25)
    # the night shift's route book on a nail
    cv.px(376, 66, T('iron', 4))
    cv.line(376, 66, 370, 72, T('paper', 1))
    cv.line(376, 66, 382, 72, T('paper', 1))
    cv.rect(366, 72, 388, 100, T('paper', 1))
    cv.rect(367, 73, 387, 99, T('paper', 2))
    for yy in range(77, 97, 3):
        cv.rect(369, yy, 385, yy + 1, T('paper', 1))
    cv.line(384, 74, 372, 98, T('red', 1))                      # the pencil on its string
    # cast-iron frame: legs, slot bank, front plate
    cv.rect(40, 96, 360, 148, T('iron', 2))
    for yy in range(118, 148):
        for xx in range(40, 360):
            if K.BAYER[yy % 4, xx % 4] < (yy - 118) / 40.0:
                cv.px(xx, yy, T('iron', 1))
    cv.rect(40, 96, 360, 104, T('iron', 3))
    cv.rect(40, 96, 360, 97, T('iron', 4))
    cv.rect(40, 103, 360, 104, T('iron', 1))
    for xx in (40, 354):
        cv.rect(xx, 96, xx + 6, 148, T('iron', 3))
        cv.rect(xx, 96, xx + 1, 148, T('iron', 4))
        cv.rect(xx + 5, 96, xx + 6, 148, T('iron', 1))
    for xx in range(52, 352, 16):                               # rivets
        cv.px(xx, 105, T('iron', 4))
        cv.px(xx, 146, T('iron', 4))
    for x in LEVER_X:
        cv.rect(x - 2, 97, x + 3, 103, T('night', 0))           # slot
        py0, py1 = PLATE_Y
        cv.rect(x - 7, py0, x + 8, py1, T('lamp', 2))
        cv.rect(x - 7, py0, x + 8, py0 + 1, T('lamp', 3))
        cv.rect(x - 7, py1 - 1, x + 8, py1, T('lamp', 1))
        cv.px(x - 6, py0 + 2, T('iron', 1))
        cv.px(x - 6, py1 - 3, T('iron', 1))
        n = str(LEVER_X.index(x) + 1)
        K.text(cv, x - 2, py0 + 3, n, T('iron', 0), 'tiny')
        px, pyy = PIP
        cv.rect(x + px - 1, pyy - 1, x + px + 3, pyy + 3, T('lamp', 1))
        cv.rect(x + px, pyy, x + px + 2, pyy + 2, T('night', 0))
    lx, ly, lw, lh = LABEL_RECT
    cv.rect(lx, ly, lx + lw, ly + lh, T('night', 2))
    cv.rect(lx, ly, lx + lw, ly + 1, T('night', 1))
    K.text(cv, 48, 139, '1941', T('paper', 2), 'tiny')
    for _ in range(40):                                         # grease and wear on the bank
        xx = int(r.integers(44, 356))
        cv.px(xx, int(r.integers(97, 103)), T('night', 1), 0.6)


def indicator() -> K.Cv:
    cw, ch = IND_CELL
    cv = K.Cv(cw * 3, ch)
    for i, rid in enumerate(('a', 'b', 'c')):
        s = INDICATOR_TEXT[rid]
        tw = K.text_width(s, 'small')
        x0 = i * cw + (cw - tw) // 2
        glow = K.Cv(cw, ch)
        K.text(glow, (cw - tw) // 2, 1, s, T('lamp', 2), 'small')
        for yy in range(ch):                                     # one-pixel glow around the lit letters
            for xx in range(cw):
                if glow.a[yy, xx, 3] > 0:
                    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        cv.px(i * cw + xx + dx, yy + dy, T('lamp', 1))
        K.text(cv, x0, 1, s, T('lamp', 4), 'small')
    return cv


def closeup() -> K.Cv:
    cw, chh = 200, 120
    cv = K.Cv(cw, chh)
    cv.rect(0, 0, cw, chh, BOARD[1])
    r = K.rng('lever_closeup')
    for yy in range(chh):
        for xx in range(cw):
            v = r.random()
            if v < 0.05:
                cv.px(xx, yy, BOARD[0])
            elif v > 0.975:
                cv.px(xx, yy, BOARD[2])
    # indicator box, letters doubled
    bx, by, bw, bh = 20, 10, 160, 30
    cv.rect(bx - 3, by - 3, bx + bw + 3, by + bh + 3, T('iron', 3))
    cv.rect(bx - 2, by - 2, bx + bw + 2, by + bh + 2, T('night', 0))
    s = INDICATOR_TEXT['c']
    small = K.Cv(K.text_width(s, 'small') + 2, 9)
    K.text(small, 1, 1, s, T('lamp', 4), 'small')
    ox = bx + (bw - small.w * 2) // 2
    oy = by + (bh - small.h * 2) // 2
    for yy in range(small.h):
        for xx in range(small.w):
            if small.a[yy, xx, 3] > 0:
                for dx in (-1, 0, 1, 2):
                    for dy in (-1, 0, 1, 2):
                        cv.px(ox + xx * 2 + dx, oy + yy * 2 + dy, T('lamp', 1), 0.7)
    for yy in range(small.h):
        for xx in range(small.w):
            if small.a[yy, xx, 3] > 0:
                cv.rect(ox + xx * 2, oy + yy * 2, ox + xx * 2 + 2, oy + yy * 2 + 2, T('lamp', 4))
    # lit track 0 rising to the right, the main line dim
    for p in seg_pixels([[0, 78], [96, 78], [120, 56], [200, 56]]):
        cv.rect(p[0], p[1], p[0] + 1, p[1] + 2, T('snow', 4))
        cv.px(p[0], p[1] + 2, T('snow', 1), 0.6)
    for p in seg_pixels([[96, 78], [200, 78]]):
        cv.px(p[0], p[1], T('paper', 1))
    # the tape, peeled back from „ПУТЬ 0“
    K.text(cv, 126, 44, 'ПУТЬ 0', T('paper', 3), 'small')
    cv.poly([(168, 42), (192, 42), (192, 52), (178, 52)], T('paper', 1))
    cv.poly([(168, 42), (178, 52), (170, 55), (164, 47)], T('paper', 2))
    # the frame edge and the bright-worn handle of lever 6 (its plate holder empty)
    cv.rect(0, 92, cw, chh, T('iron', 2))
    cv.rect(0, 92, cw, 93, T('iron', 4))
    hx0 = 100
    cv.rect(hx0 - 2, 70, hx0 + 3, 120, T('iron', 3))
    cv.rect(hx0 - 2, 70, hx0 - 1, 120, T('iron', 4))
    cv.rect(hx0 - 9, 62, hx0 + 10, 70, T('lamp', 3))
    cv.rect(hx0 - 9, 62, hx0 + 10, 63, T('lamp', 4))
    cv.rect(hx0 - 5, 64, hx0 + 4, 66, T('lamp', 4))            # worn bright where the hand grips
    cv.rect(hx0 - 9, 69, hx0 + 10, 70, T('lamp', 1))
    cv.rect(hx0 - 12, 100, hx0 + 13, 114, T('lamp', 1))        # plate holder, empty
    cv.rect(hx0 - 11, 101, hx0 + 12, 113, T('iron', 1))
    cv.px(hx0 - 9, 103, T('lamp', 3))
    cv.px(hx0 + 10, 111, T('lamp', 3))
    K.text(cv, 20, 104, '6', T('lamp', 3), 'small')
    return cv


def layout() -> dict:
    return {
        'size': [W, H], 'levers': LEVERS, 'lever_x': LEVER_X, 'slot_y': SLOT_Y, 'handle_y': HANDLE_Y,
        'plate_y': list(PLATE_Y), 'pip': list(PIP), 'label_rect': LABEL_RECT, 'board': BOARD_RECT,
        'indicator': {'at': list(IND_AT), 'cell': list(IND_CELL), 'order': ['a', 'b', 'c']},
        'signals': SIGNALS, 'wagon': WAGON, 'tracks': TRACKS, 'routes': ROUTES, 'branches': BRANCHES,
    }


def main() -> None:
    back = K.Cv(W, H)
    wall(back)
    board(back)
    frame(back)
    out = [back.save(os.path.join(OUT, 'lever_back.png')),
           indicator().save(os.path.join(OUT, 'lever_indicator.png')),
           closeup().save(os.path.join(OUT, 'lever_closeup.png')),
           K.write_json(os.path.join(OUT, 'lever_layout.json'), layout())]
    for p in out:
        print('wrote', os.path.relpath(p, K.ROOT).replace('\\', '/'))


if __name__ == '__main__':
    main()
