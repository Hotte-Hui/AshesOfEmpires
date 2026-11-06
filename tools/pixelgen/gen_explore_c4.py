"""gen_explore_c4 -- close-up art of the Chapter-4 exploration (owner: exploration c4, documentation/C4_DESIGN.md §6,
TECHNICAL_ARCHITECTURE §12.1/§12.9).

    py -3 -P tools/pixelgen/gen_explore_c4.py          (then import under the shared lock)

Writes assets/explore/c4/ at 1:1 art pixels (DiscoveryView shows a find's image x3):
  ilse_drawing.png  240x150  the side task „Ilses Puppe“ (berlin.annex.doll_cellar): the drawing Konrad finds on the
                             kitchen wall of the sealed flat -- a page torn from a squared exercise book, wax crayon: house No. 9
                             at night with every window lit, three small figures in one window, the big 9 over the
                             door, snow, tram 74 at the loop, a crescent moon, signed ILSE. An eight-year-old's hand:
                             wobbly outlines, hatching with gaps, colours over the lines.
Deterministic (seeds = crc32 of names). Colours: data/chapters/c4.json palette "annex" (paper, dawn, night, red); the
child's wax crayons outside it are documented here (CRAYON, five values). Font: none -- the signature is drawn
stroke by stroke.
"""
from __future__ import annotations

import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import mg_r7_v_kit as K  # noqa: E402

OUT = os.path.join(K.ROOT, 'assets', 'explore', 'c4')
_C4 = json.load(open(os.path.join(K.ROOT, 'data', 'chapters', 'c4.json'), encoding='utf-8'))
_P = _C4['palettes']['annex']


def A(ramp: str, i: int, a: int = 255):
    return K.hx(_P[ramp][i], a)


CRAYON = {'yellow': K.hx('#E8C04A'), 'blue': K.hx('#34508C'), 'brown': K.hx('#7A5230'), 'black': K.hx('#24262B'),
          'green': K.hx('#4F7A3A')}
W, H = 240, 150


def stroke(cv: K.Cv, pts, c, r, wob: float = 0.8, gap: float = 0.08, width: int = 1) -> None:
    """A wax-crayon stroke through `pts`: wobbly, with small gaps where the crayon skips."""
    for (x0, y0), (x1, y1) in zip(pts[:-1], pts[1:]):
        n = int(max(abs(x1 - x0), abs(y1 - y0))) + 1
        for i in range(n + 1):
            t = i / max(1, n)
            if r.random() < gap:
                continue
            x = x0 + (x1 - x0) * t + math.sin((x0 + y0 + i) * 0.7) * wob * 0.5
            y = y0 + (y1 - y0) * t + math.cos((x1 + i) * 0.5) * wob * 0.5
            cv.px(x, y, c)
            if width > 1:
                cv.px(x + 1, y, c, 0.85)
                cv.px(x, y + 1, c, 0.7)


def hatch(cv: K.Cv, x0, y0, x1, y1, c, r, step: int = 2, slope: float = 0.6, cover: float = 0.8) -> None:
    """Diagonal crayon hatching over a box, going a little over the lines like a child does."""
    h = y1 - y0
    for k in range(int(x0 - h * slope) - 2, int(x1) + 2, step):
        xa, ya = k, y1 + r.integers(-1, 2)
        xb, yb = k + h * slope, y0 + r.integers(-1, 2)
        n = int(max(abs(xb - xa), abs(yb - ya))) + 1
        for i in range(n + 1):
            t = i / max(1, n)
            x, y = xa + (xb - xa) * t, ya + (yb - ya) * t
            if x0 - 1 <= x <= x1 + 1 and y0 - 1 <= y <= y1 + 1 and r.random() < cover:
                cv.px(x, y, c)


def paper(cv: K.Cv) -> None:
    r = K.rng('ilse_paper')
    cv.rect(0, 0, W, H, A('paper', 4))
    for y in range(4, H, 7):                                   # squared exercise-book paper
        for x in range(W):
            cv.px(x, y, A('dawn', 3), 0.45)
    for x in range(3, W, 7):
        for y in range(H):
            cv.px(x, y, A('dawn', 3), 0.45)
    for y in range(H):                                         # torn perforation on the left edge
        cut = 2 + (1 if (y // 3) % 2 == 0 else 0) + (1 if r.random() < 0.2 else 0)
        for x in range(cut):
            cv.a[y, x] = 0
    for _ in range(300):                                       # a page that has hung on a kitchen wall since December
        cv.px(int(r.integers(0, W)), int(r.integers(0, H)), A('paper', 3), 0.5)
    for x in range(W):
        cv.px(x, 74 + (1 if x % 9 == 0 else 0), A('paper', 3), 0.6)


def scene(cv: K.Cv) -> None:
    r = K.rng('ilse_drawing')
    # night sky, scribbled in blue over the top, leaving the paper where the moon is
    for k in range(-40, W, 3):
        pts = [(k, 2 + r.integers(0, 3)), (k + 22, 26 + r.integers(0, 6))]
        (x0, y0), (x1, y1) = pts
        n = int(max(abs(x1 - x0), abs(y1 - y0))) + 1
        for i in range(n + 1):
            t = i / max(1, n)
            x, y = x0 + (x1 - x0) * t, y0 + (y1 - y0) * t
            if (x - 30) ** 2 + (y - 16) ** 2 < 120 or not (4 <= x < W - 3) or y > 30 + (x % 5):
                continue
            if r.random() < 0.82:
                cv.px(x, y, CRAYON['blue'])
    # crescent moon
    for y in range(6, 28):
        for x in range(18, 44):
            d1 = (x - 30) ** 2 + (y - 16) ** 2
            d2 = (x - 35) ** 2 + (y - 13) ** 2
            if d1 < 81 and d2 > 60 and r.random() < 0.9:
                cv.px(x, y, CRAYON['yellow'])
    # house No. 9: four storeys, three windows each, all lit
    hx0, hy0, hx1, hy1 = 70, 34, 152, 128
    hatch(cv, hx0, hy0, hx1, hy1, CRAYON['brown'], r, step=3, cover=0.55)
    stroke(cv, [(hx0, hy1), (hx0 + 1, hy0), (hx1, hy0 + 1), (hx1 - 1, hy1), (hx0, hy1)], CRAYON['black'], r, width=2)
    stroke(cv, [(hx0 - 4, hy0 + 2), (hx0 + 41, hy0 - 14), (hx1 + 4, hy0 + 2)], A('red', 3), r, width=2)   # roof
    hatch(cv, hx0 + 4, hy0 - 12, hx1 - 4, hy0, A('red', 2), r, step=2, slope=0.3, cover=0.6)
    stroke(cv, [(132, 26), (132, 14), (140, 14), (140, 29)], CRAYON['black'], r)                          # chimney
    for i in range(14):                                                                                 # smoke curl
        a = i * 0.9
        cv.px(136 + math.sin(a) * (2 + i * 0.4) + i * 0.6, 12 - i * 0.8, A('dawn', 2))
    wins = []
    for row in range(4):
        for col in range(3):
            wx = hx0 + 9 + col * 25
            wy = hy0 + 8 + row * 19
            wins.append((wx, wy))
            for yy in range(wy, wy + 11):
                for xx in range(wx, wx + 14):
                    if r.random() < 0.88:
                        cv.px(xx, yy, CRAYON['yellow'])
            stroke(cv, [(wx, wy), (wx + 14, wy), (wx + 14, wy + 11), (wx, wy + 11), (wx, wy)], CRAYON['black'], r, wob=0.5)
            stroke(cv, [(wx + 7, wy), (wx + 7, wy + 11)], CRAYON['black'], r, wob=0.3)
            stroke(cv, [(wx, wy + 5), (wx + 14, wy + 5)], CRAYON['black'], r, wob=0.3)
    # three small people in the second-floor middle window: two tall, one small
    fx, fy = wins[4]
    for k, (ox, hh) in enumerate(((2, 9), (6, 9), (11, 6))):
        top = fy + 11 - hh
        cv.px(fx + ox, top, A('red', 1))
        cv.px(fx + ox, top + 1, A('red', 1))
        stroke(cv, [(fx + ox, top + 2), (fx + ox, fy + 10)], A('red', 1), r, wob=0.2, gap=0.0)
    # the door and the big 9
    stroke(cv, [(103, 128), (103, 112), (119, 112), (119, 128)], CRAYON['black'], r, width=2)
    hatch(cv, 104, 113, 118, 127, A('red', 2), r, step=2, cover=0.7)
    for t in range(0, 26):                                      # the big „9“ on the door: a loop and a tail
        a = t / 25.0 * 2 * math.pi
        cv.px(111 + math.cos(a) * 3, 117 + math.sin(a) * 3, CRAYON['yellow'])
        cv.px(111 + math.cos(a) * 3, 118 + math.sin(a) * 3, CRAYON['yellow'])
    stroke(cv, [(114, 117), (113, 124), (108, 125)], CRAYON['yellow'], r, wob=0.2, gap=0.0, width=2)
    # snow ground and the loop's rails
    stroke(cv, [(4, 131), (60, 129), (120, 132), (236, 130)], CRAYON['blue'], r, width=2)
    stroke(cv, [(150, 139), (236, 138)], CRAYON['black'], r)
    stroke(cv, [(150, 143), (236, 142)], CRAYON['black'], r)
    # tram 74
    tx0, ty0, tx1, ty1 = 166, 104, 228, 132
    hatch(cv, tx0, ty0, tx1, ty1, A('red', 3), r, step=2, slope=0.4, cover=0.75)
    stroke(cv, [(tx0, ty1), (tx0, ty0 + 2), (tx1, ty0), (tx1 + 1, ty1), (tx0, ty1)], CRAYON['black'], r, width=2)
    for k in range(3):
        wx = tx0 + 6 + k * 18
        for yy in range(ty0 + 5, ty0 + 14):
            for xx in range(wx, wx + 12):
                if r.random() < 0.85:
                    cv.px(xx, yy, CRAYON['yellow'])
    stroke(cv, [(196, 104), (204, 86)], CRAYON['black'], r)     # trolley pole
    stroke(cv, [(150, 86), (236, 84)], CRAYON['black'], r)       # the wire
    for k, digit in enumerate(('7', '4')):                       # „74“ under the windows
        bx = 190 + k * 8
        if digit == '7':
            stroke(cv, [(bx, 119), (bx + 5, 119), (bx + 2, 127)], CRAYON['yellow'], r, wob=0.2, gap=0.0, width=2)
        else:
            stroke(cv, [(bx + 3, 119), (bx, 124), (bx + 5, 124)], CRAYON['yellow'], r, wob=0.2, gap=0.0, width=2)
            stroke(cv, [(bx + 4, 121), (bx + 4, 127)], CRAYON['yellow'], r, wob=0.2, gap=0.0, width=2)
    for cx in (176, 218):                                        # wheels
        for t in range(16):
            a = t / 16.0 * 2 * math.pi
            cv.px(cx + math.cos(a) * 3, 133 + math.sin(a) * 3, CRAYON['black'])
    # a green tree with snow, left of the house
    stroke(cv, [(40, 130), (40, 104)], CRAYON['brown'], r, width=2)
    for k in range(5):
        y = 100 - k * 7
        stroke(cv, [(40 - 12 + k * 2, y + 6), (40, y - 2), (40 + 12 - k * 2, y + 6)], CRAYON['green'], r, width=2)
    # signature
    sig = [((200, 30), (200, 40)), ((205, 30), (205, 40)), ((205, 40), (210, 40)),
           ((218, 30), (213, 31)), ((213, 31), (213, 35)), ((213, 35), (218, 36)), ((218, 36), (218, 40)), ((218, 40), (213, 40)),
           ((221, 30), (221, 40)), ((221, 30), (226, 30)), ((221, 35), (225, 35)), ((221, 40), (226, 40))]
    for a, b in sig:
        stroke(cv, [a, b], A('red', 3), r, wob=0.3, gap=0.0, width=2)


def main() -> None:
    cv = K.Cv(W, H)
    paper(cv)
    scene(cv)
    p = cv.save(os.path.join(OUT, 'ilse_drawing.png'))
    print('wrote', os.path.relpath(p, K.ROOT).replace('\\', '/'))


if __name__ == '__main__':
    main()
