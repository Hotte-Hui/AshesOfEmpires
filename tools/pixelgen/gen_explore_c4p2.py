"""gen_explore_c4p2 -- close-up art of the Chapter-4 part-2 exploration (owner: exploration c4p2,
documentation/C4P2_DESIGN.md §6, TECHNICAL_ARCHITECTURE §12.1).

    py -3 -P tools/pixelgen/gen_explore_c4p2.py          (then import under the shared lock)

Writes assets/explore/c4p2/ at 1:1 art pixels (DiscoveryView shows a find's image x3), 240x150 each:
  lena_mitten.png     karsk.depot.lena_mitten (secret): the foot of a coal-stage trestle post at dawn -- timber black
                      with coal dust, a rusty horseshoe nail through the cuff of a small grey knitted mitten, darned once,
                      frost on the wool, „Lena“ cross-stitched in red on the cuff; cold dawn from the left, the coal
                      stage's sodium lamp warming the post's right edge, snow drifting.
  ilse_frost_house.png  berlin.k14.ilse_drawing (secret): the glass of the side wing's stair door at night, grown over
                      with frost ferns from the frame; drawn into the frost with a child's finger, a house of five
                      storeys and every window lit -- the cellar windows too --, smoke curling from the chimney, the door
                      open; the stairwell lamp shines through the wiped lines, melt water runs from their ends; in one
                      corner the frost already clouds under Konrad's breath.
  signal_scratch.png  karsk.depot.signal_scratch (secret): the foot of Alexei's restored signal mast in the evening
                      floodlight -- fresh grey paint down to a hand's width above the ballast, drips over the edge;
                      below it the old rust, and scratched into it to the bare metal „А. М.“ and „1949“; the base
                      plate's bolts, ballast and snow.
Deterministic (seeds = crc32 of names). Colours: data/chapters/c4p2.json palettes "depot" (mitten, signal) and
"courtyard" (stair door), plus documented extras: the stair door's old green paint (DOOR #2E4A3C / #3D5E4C / #233A2F)
and the wool of the mitten (WOOL #6F7176 / #8C8E92 / #A9AAAD, darned with #7C7466). Letters are drawn stroke by stroke
(no font file).
"""
from __future__ import annotations

import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import mg_r7_v_kit as K  # noqa: E402

OUT = os.path.join(K.ROOT, 'assets', 'explore', 'c4p2')
_C = json.load(open(os.path.join(K.ROOT, 'data', 'chapters', 'c4p2.json'), encoding='utf-8'))['palettes']
W, H = 240, 150
DOOR = [K.hx('#233A2F'), K.hx('#2E4A3C'), K.hx('#3D5E4C')]
WOOL = [K.hx('#6F7176'), K.hx('#8C8E92'), K.hx('#A9AAAD')]
DARN = K.hx('#7C7466')


def P(pal: str, ramp: str, i: int, a: int = 255):
    return K.hx(_C[pal][ramp][i], a)


def snowflakes(cv: K.Cv, r, n: int, c, region=(0, 0, W, H)) -> None:
    x0, y0, x1, y1 = region
    for _ in range(n):
        x, y = int(r.integers(x0, x1)), int(r.integers(y0, y1))
        cv.px(x, y, c, 0.9)
        if r.random() < 0.3:
            cv.px(x + 1, y, c, 0.5)


# =========================================================================== Lena's mitten
LETTERS = {  # 5 rows high, cross-stitch cells
    'L': ['X..', 'X..', 'X..', 'X..', 'XXX'],
    'e': ['...', '.X.', 'XXX', 'X..', '.XX'],
    'n': ['...', 'XX.', 'X.X', 'X.X', 'X.X'],
    'a': ['...', 'XX.', '..X', 'XXX', 'XXX'],
}


def band_fill(cv: K.Cv, x0, y0, x1, y1, stops, soft: int = 3) -> None:
    """Horizontal bands top to bottom (stops = [(y_end, colour), ...]); dithered only `soft` px around each edge."""
    for y in range(int(y0), int(y1)):
        for x in range(int(x0), int(x1)):
            col = stops[-1][1]
            for i, (ye, c) in enumerate(stops):
                if y < ye:
                    col = c
                    if i + 1 < len(stops) and ye - y <= soft and K.BAYER[y % 4, x % 4] < (soft - (ye - y) + 1) / (2.0 * soft + 1):
                        col = stops[i + 1][1]
                    break
            cv.px(x, y, col)


def mitten(cv: K.Cv) -> None:
    r = K.rng('lena_mitten')
    D = lambda ramp, i, a=255: P('depot', ramp, i, a)  # noqa: E731
    # dawn behind the post: night blue going grey over the snow; the coal stage's dark on the right, its lamp
    band_fill(cv, 0, 0, 70, H, [(34, D('night', 2)), (64, D('night', 3)), (92, D('snow', 0)), (H, D('snow', 1))])
    for _ in range(40):
        cv.px(r.integers(0, 66), r.integers(96, H), D('snow', 2))
    for k in range(5):
        cv.ellipse(18 + k * 9, 130 + (k % 2) * 6, 2, 1, D('snow', 0))
    band_fill(cv, 172, 0, W, H, [(40, D('coal', 1)), (H, D('coal', 0))])
    cv.ellipse(214, 22, 9, 9, D('lamp', 1))
    cv.ellipse(214, 22, 5, 5, D('lamp', 3))
    for y in range(0, H):
        for x in range(172, W):
            d = math.hypot(x - 214, y - 22)
            if 10 < d < 34 and K.BAYER[y % 4, x % 4] < 0.22 * (1.0 - (d - 10) / 24.0):
                cv.px(x, y, D('lamp', 1))
    # the post: timber blackened by coal, irregular grain, two knots, a bolt; the lamp warms its right edge
    x0, x1 = 70, 172
    cv.rect(x0, 0, x1, H, D('coal', 2))
    for x in range(x0, x1):
        wav = 3.0 * math.sin(x * 0.21) + 2.0 * math.sin(x * 0.07 + 1.0)
        for y in range(H):
            g = (y * 0.11 + wav + x * 0.9) % 7.0
            if g < 0.9:
                cv.px(x, y, D('coal', 1))
            elif g > 6.4 and (x + y) % 3 == 0:
                cv.px(x, y, D('coal', 3), 0.7)
    for (kx, ky) in ((90, 18), (156, 128)):
        cv.ellipse(kx, ky, 6, 8, D('coal', 0))
        cv.ellipse(kx, ky, 3, 5, D('brick', 0))
        cv.ellipse(kx, ky, 1, 2, D('coal', 1))
    for y in range(H):
        cv.px(x1 - 1, y, D('lamp', 2), 0.8)
        cv.px(x1 - 2, y, D('lamp', 1), 0.5)
        cv.px(x0, y, D('snow', 1), 0.4)
    cv.ellipse(158, 12, 4, 4, D('iron', 1))
    cv.ellipse(158, 12, 2, 2, D('iron', 3))
    cv.px(157, 11, D('snow', 3))
    # the mitten: ribbed cuff, the hand, the thumb to the left; knitted stitches, a darned patch, frost on the edges
    hand = [(92, 62), (146, 62), (150, 76), (150, 108), (142, 122), (120, 127), (100, 122), (92, 110)]
    thumb = [(92, 78), (80, 80), (75, 92), (80, 102), (92, 102)]
    for y in range(58, 130):
        for x in range(72, 152):
            if not (K.inside(x + 0.5, y + 0.5, hand) or K.inside(x + 0.5, y + 0.5, thumb)):
                continue
            row, colm = y // 3, x // 2
            v = (colm + row) % 2
            col = WOOL[2] if (v == 0 and y % 3 == 0) else WOOL[1]
            if v == 1 and y % 3 == 2:
                col = WOOL[0]
            cv.px(x, y, col)
    for (x, y) in hand + thumb:
        pass
    # shading on the right of the hand (away from the dawn), the darn in brown wool
    for y in range(62, 128):
        for x in range(138, 152):
            if K.inside(x + 0.5, y + 0.5, hand) and K.BAYER[y % 4, x % 4] < (x - 138) / 18.0:
                cv.px(x, y, WOOL[0])
    cv.rect(108, 92, 128, 108, DARN)
    for y in range(93, 108, 2):
        cv.line(108, y, 127, y, K.hx('#665F53'), 0.8)
    for x in range(109, 128, 3):
        cv.line(x, 92, x, 107, K.hx('#948A78'), 0.6)
    edge = [(92, 62), (150, 76), (150, 108), (142, 122), (120, 127), (100, 122), (80, 102), (75, 92), (80, 80)]
    for (x, y) in edge:
        for k in range(10):
            cv.px(x + int(r.integers(-3, 4)), y + int(r.integers(-3, 4)), D('snow', 3), 0.85)
    for _ in range(30):
        cv.px(int(r.integers(96, 146)), int(r.integers(68, 122)), D('coal', 1), 0.5)
    # the cuff: ribbed knit, Lena cross-stitched in red thread
    cv.rect(90, 28, 148, 64, WOOL[1])
    for x in range(90, 148):
        if x % 3 == 0:
            cv.line(x, 28, x, 63, WOOL[0])
        elif x % 3 == 1:
            cv.line(x, 28, x, 63, WOOL[2], 0.65)
    cv.rect(90, 62, 148, 65, WOOL[0])
    cv.rect(90, 28, 148, 29, WOOL[2])
    cx = 96
    for ch in 'Lena':
        rows = LETTERS[ch]
        for j, row in enumerate(rows):
            for i, cell in enumerate(row):
                if cell != 'X':
                    continue
                px, py = cx + i * 4, 34 + j * 4
                for (a, b, c) in ((0, 0, 3), (1, 1, 3), (2, 2, 3), (2, 0, 2), (0, 2, 2), (1, 0, 1), (0, 1, 1)):
                    cv.px(px + a, py + b, D('red', c))
        cx += 13
    # the horseshoe nail through the cuff and the rust it bled into the wool
    cv.rect(116, 22, 124, 30, D('iron', 1))
    cv.rect(117, 23, 123, 29, D('iron', 2))
    cv.rect(118, 24, 120, 26, D('iron', 3))
    for y in range(30, 44):
        cv.px(120 + (y % 2), y, D('red', 0), 0.55)
    snowflakes(cv, r, 46, D('snow', 3))


# =========================================================================== Ilse's house in the frost
def frost_house(cv: K.Cv) -> None:
    r = K.rng('ilse_frost_house')
    C = lambda ramp, i, a=255: P('courtyard', ramp, i, a)  # noqa: E731
    # the door: old green paint, the frame of the pane, a brass handle edge at the bottom right
    cv.rect(0, 0, W, H, DOOR[1])
    for y in range(H):
        for x in range(W):
            if (x * 3 + y * 7) % 29 == 0:
                cv.px(x, y, DOOR[2], 0.7)
            elif (x + y * 5) % 37 == 0:
                cv.px(x, y, DOOR[0])
    gx0, gy0, gx1, gy1 = 22, 10, 218, 140
    cv.rect(gx0 - 4, gy0 - 4, gx1 + 4, gy1 + 4, DOOR[0])
    cv.rect(gx0 - 2, gy0 - 2, gx1 + 2, gy1 + 2, DOOR[2])
    # behind the glass: the stairwell lamp (warm, brightest at the top), the banister's shadow
    for y in range(gy0, gy1):
        for x in range(gx0, gx1):
            d = math.hypot((x - 120) / 120.0, (y - 30) / 110.0)
            t = max(0.0, 1.0 - d)
            i = 3 if t > 0.75 else 2 if t > 0.45 else 1 if t > 0.2 else 0
            cv.px(x, y, C('window', i))
    for k in range(6):
        cv.line(40 + k * 30, gy1, 70 + k * 30, gy0 + 40, C('window', 0), 0.35)
    # the frost: a milky film over everything, ferns growing in from the frame
    frost = [[0.55 for _ in range(W)] for _ in range(H)]
    for _ in range(46):
        side = int(r.integers(0, 4))
        if side == 0:
            x, y, ang = float(r.integers(gx0, gx1)), float(gy0), math.pi / 2
        elif side == 1:
            x, y, ang = float(r.integers(gx0, gx1)), float(gy1 - 1), -math.pi / 2
        elif side == 2:
            x, y, ang = float(gx0), float(r.integers(gy0, gy1)), 0.0
        else:
            x, y, ang = float(gx1 - 1), float(r.integers(gy0, gy1)), math.pi
        ang += float(r.uniform(-0.6, 0.6))
        length = int(r.integers(18, 54))
        for s in range(length):
            x += math.cos(ang)
            y += math.sin(ang)
            ang += float(r.uniform(-0.18, 0.18))
            xi, yi = int(x), int(y)
            if not (gx0 <= xi < gx1 and gy0 <= yi < gy1):
                break
            frost[yi][xi] = 1.0
            if s % 3 == 0:
                for side_a in (ang + 0.9, ang - 0.9):
                    bx, by = x, y
                    for k in range(int(r.integers(2, 7))):
                        bx += math.cos(side_a)
                        by += math.sin(side_a)
                        bi, bj = int(bx), int(by)
                        if gx0 <= bi < gx1 and gy0 <= bj < gy1:
                            frost[bj][bi] = max(frost[bj][bi], 0.85)
    # the finger drawing wipes the frost: house, roof, chimney, smoke, windows (cellar too), an open door
    wipe = [[False for _ in range(W)] for _ in range(H)]

    def finger(pts, w=2.0, wob=0.6):
        for (x0, y0), (x1, y1) in zip(pts[:-1], pts[1:]):
            n = int(max(abs(x1 - x0), abs(y1 - y0))) + 1
            for i in range(n + 1):
                t = i / max(1, n)
                x = x0 + (x1 - x0) * t + math.sin((x0 + y0 + i) * 0.5) * wob
                y = y0 + (y1 - y0) * t + math.cos((x1 + i) * 0.4) * wob
                for dy in range(-int(w), int(w) + 1):
                    for dx in range(-int(w), int(w) + 1):
                        if dx * dx + dy * dy <= w * w:
                            xi, yi = int(x + dx), int(y + dy)
                            if gx0 <= xi < gx1 and gy0 <= yi < gy1:
                                wipe[yi][xi] = True

    hx0, hx1, hy0, hy1 = 78, 162, 44, 128
    finger([(hx0, hy1), (hx0, hy0), (hx1, hy0), (hx1, hy1), (hx0, hy1)])
    finger([(hx0 - 6, hy0 + 2), (120, 20), (hx1 + 6, hy0 + 2)])
    finger([(146, 34), (146, 22), (152, 22), (152, 38)], 1.5)
    finger([(149, 18), (154, 12), (150, 7), (157, 3)], 1.2)
    for row in range(5):
        for col in range(3):
            wx = hx0 + 10 + col * 26
            wy = hy0 + 7 + row * 14
            for yy in range(wy, wy + 7):
                for xx in range(wx, wx + 9):
                    wipe[yy][xx] = True
    for col in range(3):
        wx = hx0 + 12 + col * 26
        for yy in range(hy1 - 6, hy1 - 3):
            for xx in range(wx, wx + 6):
                wipe[yy][xx] = True
    finger([(112, hy1), (112, hy1 - 16), (122, hy1 - 18), (122, hy1 - 2)], 1.4)
    # Konrad's breath clouds the lower right corner
    for y in range(gy0, gy1):
        for x in range(gx0, gx1):
            b = math.hypot((x - 176) / 40.0, (y - 118) / 26.0)
            if b < 1.0:
                frost[y][x] = max(frost[y][x], 0.75 + 0.25 * (1.0 - b))
                if wipe[y][x] and b < 0.7 and K.BAYER[y % 4, x % 4] < 0.6 * (1.0 - b):
                    wipe[y][x] = False
    for y in range(gy0, gy1):
        for x in range(gx0, gx1):
            if wipe[y][x]:
                continue
            f = frost[y][x]
            col = C('snow', 3) if f >= 0.95 else C('snow', 2) if f >= 0.8 else C('snow', 1)
            cv.px(x, y, col, 0.9 if f >= 0.8 else 0.72)
    # melt water: drops running down from the bottom ends of the strokes
    for (dx, dy, n) in ((hx0, hy1, 6), (hx1, hy1, 9), (112, hy1, 5), (122, hy1, 7), (hx0 + 36, hy0 + 7 + 4 * 14 + 7, 4)):
        for k in range(n):
            cv.px(dx + (k // 4), dy + 2 + k, C('window', 3), 0.8)
            cv.px(dx + 1 + (k // 4), dy + 2 + k, C('snow', 3), 0.5)
    # the frame's inner shadow and the handle at the bottom right
    cv.frame(gx0 - 1, gy0 - 1, gx1 + 1, gy1 + 1, DOOR[0])
    cv.rect(gx1 + 6, 118, gx1 + 14, 146, P('courtyard', 'window', 0))
    cv.rect(gx1 + 7, 119, gx1 + 13, 124, P('courtyard', 'window', 2))


# =========================================================================== „А. М. 1949“ on the signal mast
STROKES = {  # scratched letters: polylines in a 8x12 cell
    'А': [[(0, 12), (4, 0), (8, 12)], [(2, 7), (6, 7)]],
    'М': [[(0, 12), (0, 0), (4, 7), (8, 0), (8, 12)]],
    '.': [[(1, 11), (2, 12)]],
    '1': [[(2, 3), (5, 0), (5, 12)]],
    '9': [[(7, 4), (4, 0), (1, 3), (3, 6), (7, 4), (6, 12)]],
    '4': [[(6, 12), (6, 0), (0, 8), (8, 8)]],
}


def scratched(cv: K.Cv, s: str, x: int, y: int, r) -> None:
    D = lambda ramp, i, a=255: P('depot', ramp, i, a)  # noqa: E731
    for ch in s:
        if ch == ' ':
            x += 6
            continue
        for poly in STROKES.get(ch, []):
            for (x0, y0), (x1, y1) in zip(poly[:-1], poly[1:]):
                n = int(max(abs(x1 - x0), abs(y1 - y0))) * 2 + 1
                for i in range(n + 1):
                    t = i / max(1, n)
                    px = x + x0 + (x1 - x0) * t + float(r.uniform(-0.35, 0.35))
                    py = y + y0 + (y1 - y0) * t + float(r.uniform(-0.35, 0.35))
                    cv.px(px, py + 1, D('red', 0))
                    cv.px(px, py, D('steam', 2))
                    if r.random() < 0.25:
                        cv.px(px + 1, py, D('steam', 3), 0.7)
        x += 12 if ch not in '.1' else 7


def signal(cv: K.Cv) -> None:
    r = K.rng('signal_scratch')
    D = lambda ramp, i, a=255: P('depot', ramp, i, a)  # noqa: E731
    # night around the floodlight, the light falling in from the top right
    bands = ((0.58, D('lamp', 0)), (0.34, D('night', 3)), (-1.0, D('night', 2)))
    for y in range(H):
        for x in range(W):
            t = 1.0 - math.hypot((x - 300) / 250.0, (y + 70) / 210.0)
            t += 0.035 * (K.BAYER[y % 4, x % 4] - 0.5)
            for lim, c in bands:
                if t >= lim:
                    cv.px(x, y, c)
                    break
    # ballast with snow at the bottom
    for y in range(126, H):
        for x in range(W):
            cv.px(x, y, D('iron', 1 + ((x * 5 + y * 3) % 7 == 0)))
    for _ in range(140):
        x, y = int(r.integers(0, W)), int(r.integers(126, H))
        cv.ellipse(x, y, float(r.uniform(1.5, 3.5)), float(r.uniform(1.0, 2.2)), D('iron', int(r.integers(1, 4))))
    for _ in range(90):
        x, y = int(r.integers(0, W)), int(r.integers(124, H))
        cv.px(x, y, D('snow', 3))
        cv.px(x + 1, y, D('snow', 2))
    # the mast: an H-section, flanges and web; the base plate with its bolts
    mx0, mx1 = 84, 156
    paint_edge = 88
    for y in range(0, 128):
        edge = paint_edge
        for x in range(mx0, mx1):
            flange = x < mx0 + 12 or x >= mx1 - 12
            if y < edge + (1 if (x * 7) % 11 == 0 else 0):
                col = D('steam', 3) if flange and x % 12 in (2, 3) else D('steam', 2) if flange else D('steam', 1)
                if x in (mx0 + 12, mx1 - 13):
                    col = D('steam', 0)
            else:
                rust = (x * 13 + y * 7) % 9
                col = D('red', 1) if rust < 4 else D('brick', 2) if rust < 7 else D('red', 0)
                if flange and x % 12 in (2, 3):
                    col = D('red', 2)
                if (x * 31 + y * 17) % 23 == 0:
                    col = D('coal', 1)
            cv.px(x, y, col)
    # drips of the fresh paint over the edge
    for (dx, n) in ((92, 6), (101, 3), (118, 9), (137, 4), (149, 7)):
        for k in range(n):
            cv.px(dx, paint_edge + k, D('steam', 2))
        cv.px(dx, paint_edge + n, D('steam', 3))
    cv.rect(mx0 - 8, 120, mx1 + 8, 128, D('iron', 2))
    cv.rect(mx0 - 8, 120, mx1 + 8, 121, D('iron', 3))
    for bx in (mx0 - 4, mx0 + 6, mx1 - 7, mx1 + 3):
        cv.rect(bx, 121, bx + 3, 125, D('iron', 1))
        cv.px(bx + 1, 121, D('iron', 3))
    # what a fourteen-year-old scratched at the foot of the mast in autumn 1949
    scratched(cv, 'А. М.', 98, 92, r)
    scratched(cv, '1949', 100, 107, r)
    snowflakes(cv, r, 60, D('snow', 3), (0, 0, W, 120))


def main() -> None:
    for name, fn in (('lena_mitten', mitten), ('ilse_frost_house', frost_house), ('signal_scratch', signal)):
        cv = K.Cv(W, H)
        fn(cv)
        p = cv.save(os.path.join(OUT, name + '.png'))
        print('wrote', os.path.relpath(p, K.ROOT).replace('\\', '/'))


if __name__ == '__main__':
    main()
