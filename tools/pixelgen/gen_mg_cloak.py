"""gen_mg_cloak -- art for the Chapter-3 mini-game "Die Garderobe" (Palais der Kommission, Konrad; owner: minigames r7).

    py -3 -P tools/pixelgen/gen_mg_cloak.py          (then import under the shared lock)

Writes assets/ui/minigames/cloak/ at 1:1 art pixels (the game draws everything x3, nearest):
  cloak_back.png     320x150  the cloakroom behind the counter: green wall, Herr Wenzel's token board (five pegs
                              empty), walnut hat shelf with brass brackets, brass rail with five hooks and their
                              number plates (12, 7, 31, 44, 27 -- the coats hang on the wrong hooks), lamp glow
  cloak_front.png    320x150  the walnut counter (drawn over the coats): brass edge, panels, ledger, the tray of
                              freshly polished spare plates, counter bell, lamp
  cloak_coats.png    5 x 40x78  loden (Bauer), camel (Imhof), the charcoal lady's coat with the wine-red scarf
                              (Elena Weiss, never collected), navy (Duval), dark brown with karakul collar (Orlova);
                              delegation pins (shape + colour), newspapers, a dictionary
  cloak_hats.png     6 x 28x16  grey homburg with a tram ticket, karakul cap, wine-red knitted beret, grey homburg
                              with the square pin, rabbit-fur ushanka, black homburg with a green band
  cloak_guests.png   6 x 4 cells of 64x72  busts of the four guests (Dr. Imhof, Frau Orlova, M. Duval, Herr Bauer);
                              columns: in the suit (neutral, pleased, puzzled), wearing the coat (neutral, pleased,
                              puzzled)
  cloak_wenzel.png   3 x 46x60  Herr Wenzel, garderobier since 1927, behind the counter (polishing, blink, talking)
  cloak_tokens.png   5 x 14x14  the brass coat checks 12, 31, 7, 44, 27
  world_wenzel.png   3 x 20x30  Herr Wenzel at world scale for L_C3_Hall (behind the cloakroom counter)
  cloak_closeup.png  176x120  close-up for the find (DiscoveryView, shown x3): the last coat, the wine-red cap
  cloak_layout.json  hook / shelf / token / guest positions (art px) for scripts/ui/minigames/cloak_game.gd
Deterministic (seeds = crc32 of names). Colours: data/chapters/c3.json palettes "palais" (and "veltrava" patina for
the greens); skin tones are documented mixes of palais amber / marble / wood. Delegation pins are a fictional
conference system (shapes: square Reich delegation, triangle Soviet delegation, diamond observers, circle
commission) -- no state insignia anywhere.
"""
from __future__ import annotations

import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import mg_r7_v_kit as K  # noqa: E402

OUT = os.path.join(K.ROOT, 'assets', 'ui', 'minigames', 'cloak')
P = K.pal('palais')
V = K.pal('veltrava')

W, H = 320, 150
HOOKS_X = [70, 122, 174, 226, 278]
HOOK_NUMBERS = ['12', '7', '31', '44', '27']
COATS = ['loden', 'camel', 'elena', 'navy', 'karakul']          # rack order (left -> right)
SHELF_Y = 30
HATS_X = [64, 106, 148, 190, 232, 274]
HATS = ['ticket', 'karakul', 'beret', 'pin', 'ushanka', 'green']
TOKENS = ['12', '31', '7', '44', '27']
GUESTS = ['imhof', 'orlova', 'duval', 'bauer']
COUNTER_Y = 116
COAT_W, COAT_H = 40, 78
HAT_W, HAT_H = 28, 16
GW, GH = 64, 72

INK = P('ink', 0)
WOOD = [P('wood', i) for i in range(5)]
BRASS = [P('brass', i) for i in range(5)]
WALL = [P('wall', i) for i in range(5)]
MARBLE = [P('marble', i) for i in range(6)]
PAPER = [P('paper', i) for i in range(6)]
AMBER = [P('amber', i) for i in range(5)]
DAY = [P('daylight', i) for i in range(6)]
NIGHT = [P('night', i) for i in range(4)]
RED = [P('ink', 2), P('ink', 3)]
PATINA = [V('patina', i) for i in range(5)]
CAMEL = [K.mix(WOOD[2], MARBLE[1], 0.45), K.mix(WOOD[3], MARBLE[2], 0.5), K.mix(AMBER[2], MARBLE[3], 0.62),
         K.mix(AMBER[3], MARBLE[4], 0.66)]
CHARCOAL = [NIGHT[2], NIGHT[3], K.mix(NIGHT[3], MARBLE[0], 0.5), MARBLE[0]]


def skin(t: float = 0.0):
    """Skin ramp (dark -> light), documented mixes of palais wood / amber / marble; t > 0 a little paler,
    t < 0 a little warmer."""
    return [K.mix(WOOD[3], AMBER[1], 0.5 - 0.2 * t), K.mix(AMBER[2], MARBLE[2], 0.42 + 0.2 * t),
            K.mix(AMBER[3], MARBLE[4], 0.5 + 0.15 * t), K.mix(AMBER[4], MARBLE[5], 0.5 + 0.15 * t)]


# ============================================================================ small shapes
def pin(cv: K.Cv, x: int, y: int, kind: str) -> None:
    """Conference pin (fictional): square = Reich delegation, triangle = Soviet delegation, diamond = observers,
    circle = commission. Told apart by shape first, colour second."""
    if kind == 'square':
        cv.rect(x - 1, y - 1, x + 2, y + 2, MARBLE[3])
        cv.px(x - 1, y - 1, MARBLE[5])
        cv.px(x + 1, y + 1, MARBLE[1])
    elif kind == 'triangle':
        cv.px(x, y - 1, PATINA[4])
        cv.rect(x - 1, y, x + 2, y + 1, PATINA[3])
        cv.rect(x - 2, y + 1, x + 3, y + 2, PATINA[2])
    elif kind == 'diamond':
        cv.px(x, y - 2, PAPER[5])
        cv.rect(x - 1, y - 1, x + 2, y, PAPER[5])
        cv.rect(x - 2, y, x + 3, y + 1, PAPER[4])
        cv.rect(x - 1, y + 1, x + 2, y + 2, PAPER[3])
        cv.px(x, y + 2, PAPER[2])
    elif kind == 'circle':
        cv.rect(x - 1, y - 2, x + 2, y + 3, DAY[2])
        cv.rect(x - 2, y - 1, x + 3, y + 2, DAY[2])
        cv.px(x, y, PAPER[5])
        cv.px(x - 1, y, PAPER[4])
        cv.px(x + 1, y, PAPER[4])


def newspaper(cv: K.Cv, x: int, y: int, kind: str) -> None:
    """Folded paper sticking out of a pocket (12x8): mastheads differ (dark gothic / red / blue)."""
    cv.rect(x, y, x + 9, y + 8, PAPER[4])
    cv.rect(x + 1, y - 1, x + 10, y, PAPER[3])
    cv.rect(x + 9, y, x + 10, y + 8, PAPER[2])
    head = {'berlin': INK, 'moscow': RED[1], 'zurich': DAY[1]}[kind]
    cv.rect(x + 1, y + 1, x + 8, y + 3, head)
    for yy in (y + 4, y + 6):
        cv.rect(x + 1, yy, x + 8, yy + 1, PAPER[2])


def hanger(cv: K.Cv, cx: int) -> None:
    cv.line(cx - 14, 6, cx, 1, WOOD[3])
    cv.line(cx, 1, cx + 14, 6, WOOD[3])
    cv.line(cx - 14, 7, cx + 14, 7, WOOD[2])
    cv.rect(cx, 0, cx + 1, 2, BRASS[3])


# ============================================================================ coats (40x78)
def coat(kind: str) -> K.Cv:
    cv = K.Cv(COAT_W, COAT_H)
    cx = COAT_W // 2
    col = {'loden': [WALL[0], WALL[1], WALL[2], WALL[3]], 'camel': CAMEL, 'elena': CHARCOAL,
           'navy': [DAY[0], K.mix(DAY[0], DAY[1], 0.5), DAY[1], K.mix(DAY[1], DAY[2], 0.5)],
           'karakul': [WOOD[0], WOOD[1], WOOD[2], WOOD[3]]}[kind]
    slim = 2 if kind == 'elena' else 0
    # body: shoulders under the hanger, widening to the hem
    body = [(cx - 15 + slim, 6), (cx + 15 - slim, 6), (cx + 17 - slim, 20), (cx + 18 - slim, 77),
            (cx - 18 + slim, 77), (cx - 17 + slim, 20)]
    cv.poly(body, col[2])
    # shading: light from the lamp on the right, folds
    for y in range(6, 78):
        for x in range(COAT_W):
            if cv.a[y, x][3] > 0:
                rel = (x - (cx - 17)) / 34.0
                if rel < 0.18 or (y > 30 and abs(x - (cx - 6)) <= 1 and K.BAYER[y % 4, x % 4] < 0.5):
                    cv.a[y, x] = col[1]
                elif rel > 0.84 and y > 10:
                    cv.a[y, x] = col[3]
    cv.rect(cx - 18 + slim, 74, cx + 19 - slim, 78, col[0])
    # opening (front edge) and lapels
    cv.line(cx + (1 if kind != 'elena' else -1), 12, cx + (1 if kind != 'elena' else -1), 77, col[0])
    lap_l = [(cx - 10, 7), (cx - 2, 7), (cx, 26), (cx - 6, 18)]
    lap_r = [(cx + 2, 7), (cx + 10, 7), (cx + 6, 18), (cx + 1, 26)]
    cv.poly(lap_l, col[3])
    cv.poly(lap_r, col[1])
    cv.poly([(cx - 2, 7), (cx + 2, 7), (cx, 18)], col[0])
    # buttons (men's coats button right over left, the lady's coat the other way)
    bx = cx - 3 if kind != 'elena' else cx + 3
    for by in (32, 44, 56):
        cv.px(bx, by, col[0])
        cv.px(bx, by - 1, col[3])
    # pockets
    for px_ in (cx - 13, cx + 6):
        cv.rect(px_, 48, px_ + 8, 50, col[0])
        cv.rect(px_, 47, px_ + 8, 48, col[3])
    if kind == 'karakul':
        r = K.rng('karakul_collar')
        for y in range(5, 17):
            for x in range(cx - 13, cx + 14):
                d = ((x - cx) / 13.5) ** 2 + ((y - 4) / 12.5) ** 2
                if d <= 1.0 and not (abs(x - cx) < 3 and y > 9):
                    v = r.random()
                    cv.px(x, y, MARBLE[4] if v < 0.45 else MARBLE[3] if v < 0.8 else MARBLE[1])
    if kind == 'camel':
        # green scarf over the hanger, one end hanging down the left side
        cv.rect(cx - 9, 5, cx + 10, 9, PATINA[3])
        cv.rect(cx - 9, 8, cx + 10, 9, PATINA[2])
        cv.rect(cx - 9, 9, cx - 4, 40, PATINA[2])
        cv.rect(cx - 9, 9, cx - 8, 40, PATINA[1])
        for y in range(37, 41):
            cv.px(cx - 9 + (y % 2) * 2, y + 1, PATINA[1])
            cv.px(cx - 6 + (y % 2), y + 1, PATINA[3])
    if kind == 'elena':
        cv.rect(cx - 9, 5, cx + 10, 9, RED[1])
        cv.rect(cx - 9, 8, cx + 10, 9, RED[0])
        cv.rect(cx + 4, 9, cx + 9, 46, RED[0])
        cv.rect(cx + 8, 9, cx + 9, 46, K.mix(RED[0], NIGHT[2], 0.4))
        cv.rect(cx + 5, 9, cx + 6, 46, RED[1])
        for x in range(cx + 4, cx + 9, 2):
            cv.px(x, 47, RED[0])
    # pins (on the left lapel = viewer's right) and pocket contents
    if kind == 'loden':
        pin(cv, cx + 6, 13, 'square')
        newspaper(cv, cx + 6, 41, 'berlin')
    elif kind == 'camel':
        pin(cv, cx + 6, 13, 'diamond')
        newspaper(cv, cx + 6, 41, 'zurich')
    elif kind == 'elena':
        pin(cv, cx - 5, 13, 'circle')
    elif kind == 'navy':
        pin(cv, cx + 6, 13, 'circle')
        # a small dictionary in the right pocket: red-brown cloth, cream page edge
        cv.rect(cx + 7, 43, cx + 13, 50, RED[0])
        cv.rect(cx + 7, 43, cx + 13, 44, K.mix(RED[1], PAPER[3], 0.3))
        cv.rect(cx + 12, 44, cx + 13, 50, PAPER[3])
    elif kind == 'karakul':
        pin(cv, cx + 7, 19, 'triangle')
        newspaper(cv, cx - 14, 41, 'moscow')
    hanger(cv, cx)
    return cv


# ============================================================================ hats (28x16)
def homburg(cv: K.Cv, base, band) -> None:
    cx = HAT_W // 2
    # brim (curled), crown with the centre dent, ribbon
    cv.ellipse(cx, 13.5, 13, 2.6, base[1])
    cv.ellipse(cx, 12.8, 12, 1.8, base[2])
    cv.rect(cx - 8, 4, cx + 8, 12, base[2])
    cv.ellipse(cx, 4.5, 8, 2.2, base[3])
    cv.rect(cx - 1, 3, cx + 1, 6, base[1])
    cv.rect(cx - 8, 9, cx + 8, 12, band)
    cv.rect(cx + 5, 4, cx + 8, 12, base[1])
    cv.rect(cx + 5, 9, cx + 8, 12, K.mix(band, NIGHT[0], 0.35))


def hat(kind: str) -> K.Cv:
    cv = K.Cv(HAT_W, HAT_H)
    cx = HAT_W // 2
    grey = [MARBLE[0], MARBLE[1], MARBLE[2], MARBLE[3]]
    black = [NIGHT[1], NIGHT[2], NIGHT[3], K.mix(NIGHT[3], MARBLE[0], 0.5)]
    if kind == 'ticket':
        homburg(cv, grey, NIGHT[2])
        cv.rect(cx - 7, 6, cx - 2, 10, PAPER[4])
        cv.rect(cx - 7, 6, cx - 2, 7, PAPER[5])
        cv.rect(cx - 5, 8, cx - 4, 10, RED[1])          # the printed line number, too small to read
    elif kind == 'pin':
        homburg(cv, grey, NIGHT[2])
        pin(cv, cx - 4, 10, 'square')
    elif kind == 'green':
        homburg(cv, black, PATINA[3])
        cv.rect(cx - 8, 10, cx + 5, 11, PATINA[4])
    elif kind == 'karakul':
        r = K.rng('karakul_hat')
        for y in range(3, 15):
            for x in range(cx - 9, cx + 10):
                d = ((x - cx) / 9.5) ** 2 + ((y - 9) / 6.5) ** 2
                if d <= 1.0 or (y >= 9 and abs(x - cx) <= 9):
                    v = r.random()
                    cv.px(x, y, MARBLE[4] if v < 0.42 else MARBLE[3] if v < 0.78 else MARBLE[1])
        cv.rect(cx - 9, 14, cx + 10, 15, MARBLE[1])
    elif kind == 'ushanka':
        fur = [WOOD[2], WOOD[3], WOOD[4], K.mix(WOOD[4], AMBER[2], 0.4)]
        cv.ellipse(cx, 8, 10, 6.5, fur[1])
        cv.ellipse(cx - 1, 7, 8, 4.5, fur[2])
        cv.rect(cx - 10, 9, cx + 11, 15, fur[1])
        cv.rect(cx - 10, 9, cx + 11, 10, fur[3])
        cv.rect(cx - 12, 10, cx - 8, 15, fur[0])
        cv.rect(cx + 9, 10, cx + 13, 15, fur[0])
        cv.rect(cx - 4, 2, cx + 4, 4, fur[3])
    elif kind == 'beret':
        r = K.rng('beret')
        cv.ellipse(cx, 10, 11, 4.6, RED[0])
        cv.ellipse(cx - 1, 9, 9, 3.4, RED[1])
        for y in range(5, 15):
            for x in range(HAT_W):
                if cv.a[y, x][3] > 0 and (x + y) % 3 == 0 and r.random() < 0.7:
                    cv.a[y, x] = K.mix(RED[0], NIGHT[1], 0.35)
        cv.rect(cx, 4, cx + 1, 6, RED[0])
        cv.rect(cx - 9, 13, cx + 10, 14, K.mix(RED[0], NIGHT[1], 0.45))
    return cv


# ============================================================================ guests (64x72 busts)
SPEC = {
    'imhof': {'skin': 0.05, 'hair': [MARBLE[2], MARBLE[4], PAPER[4], PAPER[5]], 'style': 'receding',
              'suit': [K.mix(MARBLE[0], WOOD[1], 0.4), MARBLE[0], MARBLE[1], MARBLE[2]], 'shirt': PAPER[4],
              'tie': PATINA[2], 'pin': 'diamond', 'glasses': True, 'moustache': True, 'coat': 'camel'},
    'orlova': {'skin': 0.25, 'hair': [WOOD[0], WOOD[1], WOOD[2], WOOD[3]], 'style': 'bun',
               'suit': [WOOD[1], WOOD[2], WOOD[3], WOOD[4]], 'shirt': PAPER[5], 'tie': None, 'pin': 'triangle',
               'glasses': False, 'moustache': False, 'coat': 'karakul', 'woman': True},
    'duval': {'skin': -0.1, 'hair': [NIGHT[0], NIGHT[2], WOOD[1], WOOD[2]], 'style': 'curls',
              'suit': [DAY[0], DAY[0], DAY[1], K.mix(DAY[1], DAY[2], 0.5)], 'shirt': DAY[4], 'tie': NIGHT[3],
              'pin': 'circle', 'glasses': False, 'moustache': False, 'coat': None},
    'bauer': {'skin': 0.1, 'hair': [WOOD[2], WOOD[3], K.mix(WOOD[4], AMBER[1], 0.5), AMBER[2]], 'style': 'parted',
              'suit': [MARBLE[0], MARBLE[1], MARBLE[2], MARBLE[3]], 'shirt': PAPER[5], 'tie': MARBLE[0],
              'pin': 'square', 'glasses': False, 'moustache': False, 'coat': 'loden'},
}
COAT_COLS = {'camel': CAMEL, 'karakul': [WOOD[0], WOOD[1], WOOD[2], WOOD[3]], 'loden': [WALL[0], WALL[1], WALL[2], WALL[3]]}


def _face_shade(cv: K.Cv, sk, cx: float, cy: float, rx: float, ry: float, y0: int, y1: int) -> None:
    """Light from the upper left: a crescent of shadow on the right cheek and under the jaw, a highlight on the
    forehead and the left cheek. Only pixels still in the base skin colour are changed (no dither on faces)."""
    for y in range(y0, y1):
        for x in range(int(cx - rx - 1), int(cx + rx + 2)):
            if not (0 <= x < cv.w and 0 <= y < cv.h):
                continue
            c = cv.a[y, x]
            if c[3] == 0 or tuple(c[:3]) != tuple(sk[2][:3]):
                continue
            fx = (x + 0.5 - cx) / rx
            fy = (y + 0.5 - cy) / ry
            edge = fx * fx + fy * fy
            if fx > 0.62 or (fx > 0.35 and edge > 0.72) or fy > 0.86:
                cv.a[y, x] = sk[1]
            elif fx < -0.25 and -0.75 < fy < -0.25:
                cv.a[y, x] = sk[3]
            elif -0.62 < fx < -0.38 and 0.1 < fy < 0.32:
                cv.a[y, x] = sk[3]


def _cap(cv: K.Cv, cx: float, cy: float, rx: float, ry: float, y_top: float, y_line: float, side_low: float,
         side_w: float, colfn) -> None:
    """Hair as a cap over the head ellipse: everything above y_line, and the sides down to side_low."""
    for y in range(int(y_top), int(side_low) + 1):
        for x in range(int(cx - rx - 2), int(cx + rx + 3)):
            d = ((x + 0.5 - cx) / (rx + 1.2)) ** 2 + ((y + 0.5 - cy) / (ry + 1.4)) ** 2
            if d > 1.0:
                continue
            side = abs(x + 0.5 - cx) > rx - side_w
            if y <= y_line or (side and y <= side_low):
                cv.px(x, y, colfn(x, y))


def bust(gid: str, outfit: str, expr: str) -> K.Cv:
    s = SPEC[gid]
    cv = K.Cv(GW, GH)
    sk = skin(s['skin'])
    cx, cy, rx, ry = 32.0, 25.0, 12.0, 14.5
    # ---- body
    if outfit == 'coat' and s['coat']:
        cc = COAT_COLS[s['coat']]
        cv.poly([(1, 72), (2, 59), (11, 51), (24, 47), (40, 47), (53, 51), (62, 59), (63, 72)], cc[2])
        cv.poly([(1, 72), (2, 59), (11, 51), (16, 50), (12, 72)], cc[1])
        cv.poly([(52, 72), (50, 51), (53, 51), (62, 59), (63, 72)], cc[3])
        cv.poly([(25, 49), (39, 49), (37, 72), (27, 72)], s['suit'][1])
        cv.poly([(28, 49), (36, 49), (32, 59)], s['shirt'])
        if s['tie'] is not None:
            cv.poly([(31, 51), (33, 51), (34, 61), (32, 64), (30, 61)], s['tie'])
        cv.poly([(24, 47), (29, 49), (27, 66), (16, 56)], cc[3])
        cv.poly([(40, 47), (35, 49), (37, 66), (48, 56)], cc[1])
        if s['coat'] == 'camel':
            cv.poly([(22, 44), (42, 44), (41, 51), (23, 51)], PATINA[3])
            cv.poly([(23, 49), (41, 49), (40, 51), (24, 51)], PATINA[2])
            cv.poly([(26, 51), (31, 51), (30, 68), (25, 68)], PATINA[2])
            cv.poly([(26, 51), (27, 51), (26, 68), (25, 68)], PATINA[1])
            for x in range(23, 42, 3):
                cv.px(x, 46, PATINA[4])
            pin(cv, 43, 57, 'diamond')
        elif s['coat'] == 'karakul':
            r = K.rng('karakul_bust')
            for y in range(40, 57):
                for x in range(11, 54):
                    d = ((x - cx) / 21.0) ** 2 + ((y - 43) / 11.5) ** 2
                    inner = ((x - cx) / 8.5) ** 2 + ((y - 40) / 9.5) ** 2
                    if d <= 1.0 and inner > 1.0:
                        v = r.random()
                        cv.px(x, y, MARBLE[4] if v < 0.45 else MARBLE[3] if v < 0.8 else MARBLE[1])
            pin(cv, 45, 60, 'triangle')
        elif s['coat'] == 'loden':
            pin(cv, 43, 57, 'square')
    else:
        su = s['suit']
        cv.poly([(3, 72), (5, 60), (13, 52), (25, 48), (39, 48), (51, 52), (59, 60), (61, 72)], su[2])
        cv.poly([(3, 72), (5, 60), (13, 52), (17, 51), (13, 72)], su[1])
        cv.poly([(51, 72), (49, 52), (51, 52), (59, 60), (61, 72)], su[3])
        cv.poly([(27, 48), (37, 48), (32, 61)], s['shirt'])
        if s.get('woman'):
            cv.poly([(25, 48), (32, 52), (27, 57)], s['shirt'])
            cv.poly([(39, 48), (32, 52), (37, 57)], s['shirt'])
            cv.px(32, 55, BRASS[3])        # one small button of the blouse
        if s['tie'] is not None:
            cv.poly([(31, 50), (33, 50), (34, 61), (32, 64), (30, 61)], s['tie'])
            cv.px(31, 50, K.mix(s['tie'], PAPER[5], 0.3))
        cv.poly([(25, 48), (31, 61), (28, 66), (18, 55)], su[3])
        cv.poly([(39, 48), (33, 61), (36, 66), (46, 55)], su[1])
        pin(cv, 41, 57, s['pin'])
    # ---- the bun sits behind the head (drawn first, the head covers most of it)
    if s['style'] == 'bun':
        cv.ellipse(cx + 8.5, 12.5, 4.2, 3.4, s['hair'][1])
        cv.ellipse(cx + 8.0, 11.8, 2.6, 2.0, s['hair'][2])
    # ---- neck and head
    cv.rect(27, 36, 38, 50, sk[1])
    cv.rect(35, 36, 38, 50, sk[0])
    cv.ellipse(cx, cy, rx, ry, sk[2])
    for ex_ in (cx - rx, cx + rx):
        cv.ellipse(ex_, 27, 2.0, 3.6, sk[1] if ex_ < cx else sk[0])
    _face_shade(cv, sk, cx, cy, rx, ry, 9, 41)
    cv.rect(28, 39, 37, 41, sk[0])          # the shadow under the chin
    cv.rect(26, 38, 28, 40, sk[1])
    # ---- hair
    hr = s['hair']
    st = s['style']
    if st == 'receding':
        _cap(cv, cx, cy, rx, ry, 9, 10.5, 29, 3.2, lambda x, y: hr[3] if x < cx - 4 else hr[2] if x < cx + 5 else hr[1])
        cv.rect(int(cx) - 6, 10, int(cx) + 6, 12, sk[3])          # the bald crown catches the light
    elif st == 'bun':
        _cap(cv, cx, cy, rx, ry, 8, 17, 30, 3.0,
             lambda x, y: hr[0] if abs(x + 0.5 - cx) < 1 else hr[2] if x < cx else hr[1])
        cv.px(int(cx) - 7, 18, hr[3])
        cv.px(int(cx) + 6, 12, hr[3])
    elif st == 'curls':
        r = K.rng('curls')
        _cap(cv, cx, cy, rx, ry, 6, 16, 24, 2.6,
             lambda x, y: hr[0] if r.random() < 0.35 else hr[1] if r.random() < 0.6 else hr[2])
        for x in range(int(cx - rx), int(cx + rx), 3):
            cv.px(x, 17, hr[1])
    elif st == 'parted':
        _cap(cv, cx, cy, rx, ry, 9, 15, 24, 2.6, lambda x, y: hr[2] if x < cx - 5 else hr[1] if x < cx + 6 else hr[0])
        cv.line(int(cx) - 5, 9, int(cx) - 6, 15, hr[0])
        cv.line(int(cx) - 4, 10, int(cx) + 4, 11, hr[2])
    # ---- face: brows, eyes, nose, mouth
    browc = hr[0] if st != 'receding' else MARBLE[3]
    lb = 21
    rb = 21 - (1 if expr == 'puzzled' else 0)
    cv.rect(24, lb, 30, lb + 1, browc)
    cv.rect(34, rb, 40, rb + 1, browc)
    if st == 'receding':
        cv.rect(24, lb - 1, 30, lb, PAPER[4])
        cv.rect(34, rb - 1, 40, rb, PAPER[4])
    for ex in (27, 37):
        if expr == 'pleased':
            cv.rect(ex - 2, 25, ex + 2, 26, INK)
            cv.px(ex - 2, 24, sk[1])
            cv.px(ex + 1, 24, sk[1])
        else:
            cv.rect(ex - 2, 24, ex + 2, 25, INK)
            cv.px(ex - 2, 25, PAPER[4])
            cv.rect(ex - 1, 25, ex + 1, 26, INK)
            cv.px(ex + 1, 25, PAPER[3])
            cv.px(ex, 25, DAY[1] if gid in ('duval', 'bauer') else WOOD[1])
    cv.line(33, 25, 33, 30, sk[1])
    cv.px(32, 31, sk[3])
    cv.px(30, 32, sk[0])
    cv.px(34, 32, sk[0])
    cv.px(33, 31, sk[1])
    lip = K.mix(sk[0], RED[1], 0.45 if s.get('woman') else 0.2)
    lip_l = K.mix(sk[2], RED[1], 0.3 if s.get('woman') else 0.1)
    if expr == 'pleased':
        cv.rect(29, 35, 36, 36, lip)
        cv.px(28, 34, lip)
        cv.px(36, 34, lip)
        cv.rect(30, 36, 35, 37, lip_l)
    elif expr == 'puzzled':
        cv.rect(31, 34, 34, 37, K.mix(INK, lip, 0.45))
        cv.px(31, 34, lip)
    else:
        cv.rect(29, 35, 36, 36, lip)
        cv.rect(30, 36, 35, 37, lip_l)
    if s['moustache']:
        cv.rect(28, 32, 37, 34, PAPER[4])
        cv.rect(28, 33, 37, 34, MARBLE[3])
        cv.px(28, 33, sk[2])
    if s['glasses']:
        for ex in (27, 37):
            for a in range(20):
                ang = a / 20.0 * 6.283
                cv.px(ex + 3.6 * math.cos(ang), 25 + 3.0 * math.sin(ang), MARBLE[4])
        cv.rect(31, 24, 33, 25, MARBLE[4])
        cv.line(22, 24, 20, 25, MARBLE[4])
        cv.line(42, 24, 44, 25, MARBLE[4])
    if gid == 'imhof':
        cv.rect(26, 17, 38, 18, sk[1])       # forehead line
        cv.px(24, 29, sk[1])
        cv.px(40, 29, sk[0])
    return cv


# ============================================================================ Herr Wenzel (46x60, behind the counter)
def wenzel(frame: int) -> K.Cv:
    cv = K.Cv(46, 60)
    sk = skin(0.1)
    cx = 23
    # shirt, waistcoat, sleeve garters
    cv.poly([(2, 60), (4, 44), (12, 37), (34, 37), (42, 44), (44, 60)], PAPER[4])
    cv.poly([(2, 60), (4, 44), (8, 40), (8, 60)], PAPER[3])
    cv.poly([(12, 38), (34, 38), (33, 60), (13, 60)], WOOD[2])
    cv.poly([(12, 38), (20, 38), (23, 50), (17, 60), (13, 60)], WOOD[3])
    cv.poly([(26, 38), (34, 38), (33, 60), (29, 60), (23, 50)], WOOD[1])
    cv.poly([(20, 37), (26, 37), (23, 46)], PAPER[5])
    for by in (49, 54):
        cv.px(cx, by, BRASS[3])
    cv.rect(4, 50, 9, 52, RED[0])
    cv.rect(37, 50, 42, 52, RED[0])
    cv.rect(20, 37, 27, 40, INK)            # bow tie
    cv.px(23, 38, RED[0])
    # watch chain
    cv.line(17, 52, 24, 55, BRASS[3])
    # head
    cv.rect(19, 29, 28, 38, sk[1])
    cv.ellipse(cx, 20, 9.5, 11.5, sk[2])
    cv.ellipse(13.5, 21, 1.6, 3, sk[1])
    cv.ellipse(32.5, 21, 1.6, 3, sk[1])
    for y in range(8, 33):
        for x in range(13, 34):
            if cv.a[y, x][3] > 0 and tuple(cv.a[y, x][:3]) == tuple(sk[2][:3]):
                if (x - cx) / 9.5 > 0.55:
                    cv.a[y, x] = sk[1]
                elif (x - cx) < -3 and y < 16 and K.BAYER[y % 4, x % 4] < 0.5:
                    cv.a[y, x] = sk[3]
    # white fringe of hair, bald crown with a shine
    for y in range(12, 25):
        for x in range(12, 35):
            d = ((x - cx) / 10.5) ** 2 + ((y - 19) / 12.5) ** 2
            if 0.78 < d <= 1.0 and y > 14:
                cv.px(x, y, PAPER[4] if x < cx else MARBLE[3])
    cv.px(19, 11, sk[3])
    cv.px(20, 11, sk[3])
    # bushy brows, round glasses, eyes, nose, mouth, little moustache-free smile lines
    cv.rect(17, 16, 22, 18, PAPER[5])
    cv.rect(25, 16, 30, 18, PAPER[4])
    blink = frame == 1
    for ex in (19, 27):
        if blink:
            cv.rect(ex - 1, 20, ex + 2, 21, INK)
        else:
            cv.rect(ex - 1, 19, ex + 2, 20, INK)
            cv.px(ex, 20, INK)
            cv.px(ex - 1, 20, PAPER[4])
        for a in range(14):
            ang = a / 14.0 * 6.283
            cv.px(ex + 0.5 + 3.0 * math.cos(ang), 19.6 + 2.4 * math.sin(ang), BRASS[3])
    cv.rect(22, 19, 25, 20, BRASS[3])
    cv.line(24, 21, 24, 24, sk[1])
    cv.px(22, 25, sk[0])
    if frame == 2:
        cv.rect(20, 27, 27, 29, K.mix(INK, RED[0], 0.4))
    else:
        cv.rect(20, 27, 27, 28, K.mix(sk[0], RED[0], 0.2))
        cv.px(19, 26, sk[1])
        cv.px(27, 26, sk[1])
    # hands: polishing a brass plate with a cloth (frames 0/1) or raising a finger (2)
    if frame == 2:
        cv.rect(38, 30, 42, 37, sk[2])
        cv.rect(39, 26, 40, 31, sk[2])
        cv.rect(36, 37, 43, 44, PAPER[4])
    else:
        cv.rect(14, 50, 32, 56, PAPER[2])
        cv.rect(20, 48, 30, 54, BRASS[3])
        cv.rect(20, 48, 30, 49, BRASS[4])
        cv.rect(12, 51, 18, 57, sk[2])
        cv.rect(30, 50, 36, 56, sk[2])
    return cv


def world_wenzel(frame: int) -> K.Cv:
    """Herr Wenzel at world scale (20x30, front view, cut by the counter at the bottom). Values are kept a step
    darker than the UI bust: the sprite has no normal map and the palace's lamps light it flat."""
    cv = K.Cv(20, 30)
    sk = skin(0.1)
    shirt = [MARBLE[2], MARBLE[3], PAPER[2]]
    cv.poly([(1, 30), (2, 22), (6, 18), (14, 18), (18, 22), (19, 30)], shirt[1])
    cv.poly([(1, 30), (2, 22), (5, 19), (5, 30)], shirt[0])
    cv.poly([(15, 19), (18, 22), (19, 30), (16, 30)], shirt[0])
    cv.poly([(6, 18), (14, 18), (13, 30), (7, 30)], WOOD[1])
    cv.rect(7, 18, 9, 30, WOOD[2])
    cv.px(10, 24, BRASS[2])
    cv.px(10, 27, BRASS[2])
    cv.rect(3, 25, 6, 26, RED[0])
    cv.rect(14, 25, 17, 26, RED[0])
    cv.rect(8, 17, 12, 19, INK)              # bow tie
    cv.px(10, 18, RED[0])
    cv.rect(8, 13, 12, 18, sk[1])            # neck
    cv.rect(11, 13, 12, 18, sk[0])
    cv.ellipse(10, 9, 3.9, 4.7, sk[1])       # head, lit from the lamp on the left
    for y in range(4, 15):
        for x in range(5, 16):
            if cv.a[y, x][3] > 0 and tuple(cv.a[y, x][:3]) == tuple(sk[1][:3]) and x < 10 and y < 11:
                cv.a[y, x] = sk[2]
    cv.px(5, 9, sk[1])                       # ears
    cv.px(15, 9, sk[0])
    for (x, y) in ((6, 7), (6, 8), (6, 10), (14, 7), (14, 8), (14, 10), (7, 6), (13, 6)):
        cv.px(x, y, PAPER[3] if x < 10 else MARBLE[2])   # the white fringe round the bald crown
    cv.px(9, 5, sk[3])                       # shine on the crown
    if frame == 1:
        cv.rect(8, 9, 10, 10, INK)
        cv.rect(11, 9, 13, 10, INK)
    else:
        cv.px(8, 9, INK)
        cv.px(12, 9, INK)
    cv.px(9, 9, BRASS[3])                    # the bridge of his round spectacles
    cv.px(11, 9, BRASS[3])
    cv.px(7, 9, BRASS[2])
    cv.px(13, 9, BRASS[2])
    cv.rect(8, 8, 10, 8 + 1, PAPER[3])       # bushy white brows
    cv.rect(11, 8, 13, 8 + 1, MARBLE[2])
    cv.px(10, 11, sk[0])                     # nose
    cv.rect(9, 12, 12, 13, K.mix(sk[0], RED[0], 0.3))
    # hands with the cloth and a brass plate; frame 2 lifts the plate to the light
    if frame == 2:
        cv.rect(14, 15, 17, 18, BRASS[3])
        cv.px(14, 15, BRASS[4])
        cv.rect(15, 18, 17, 21, sk[1])
        cv.rect(3, 24, 7, 27, sk[1])
    else:
        cv.rect(5, 24, 15, 27, MARBLE[2])
        cv.rect(8, 23, 13, 26, BRASS[2])
        cv.rect(8, 23, 13, 24, BRASS[3])
        cv.rect(3, 24, 6, 27, sk[1])
        cv.rect(14, 24, 17, 27, sk[1])
    return cv


# ============================================================================ tokens (14x14)
def token(num: str) -> K.Cv:
    cv = K.Cv(14, 14)
    cv.ellipse(7, 7, 6.6, 6.6, BRASS[1])
    cv.ellipse(7, 7, 5.8, 5.8, BRASS[3])
    cv.ellipse(6.3, 6.3, 4.2, 4.2, BRASS[4])
    cv.ellipse(7, 7, 4.0, 4.0, BRASS[3])
    cv.rect(6, 1, 8, 3, BRASS[0])         # the hole for the hook
    tw = K.text_width(num, 'tiny')
    K.text(cv, 7 - tw // 2, 6, num, WOOD[0], 'tiny')
    return cv


# ============================================================================ backgrounds
def back() -> K.Cv:
    cv = K.Cv(W, H)
    # wall: green with a faint damask stripe; wainscot top rail behind the counter
    cv.rect(0, 0, W, H, WALL[1])
    for x in range(W):
        for y in range(H):
            if (x % 12 in (0, 1)) and K.BAYER[y % 4, x % 4] < 0.35:
                cv.px(x, y, WALL[2])
    cv.rect(0, 0, W, 5, WOOD[2])
    cv.rect(0, 5, W, 6, WOOD[3])
    cv.rect(0, 6, W, 7, NIGHT[3])
    # lamp glow on the wall (right): two soft steps, no noise
    for y in range(36, 118):
        for x in range(196, W):
            d = ((x - 296) / 74.0) ** 2 + ((y - 104) / 56.0) ** 2
            if d < 0.45:
                cv.a[y, x] = WALL[3] if (x % 12 in (0, 1)) else WALL[2]
            elif d < 1.0 and K.BAYER[y % 4, x % 4] < 0.5 * (1.0 - d) / 0.55:
                cv.a[y, x] = WALL[2]
    # token board on the left wall: two rows of pegs with brass checks, five pegs empty
    cv.rect(6, 12, 42, 44, WOOD[1])
    cv.rect(7, 13, 41, 43, WOOD[2])
    cv.frame(6, 12, 42, 44, WOOD[0])
    empty = {(1, 1), (3, 0), (0, 2), (4, 2), (2, 3)}
    for r in range(4):
        for c in range(5):
            px_, py_ = 10 + c * 7, 16 + r * 7
            cv.px(px_ + 2, py_, BRASS[2])
            if (c, r) not in empty:
                cv.ellipse(px_ + 2.5, py_ + 3, 2.6, 2.6, BRASS[3])
                cv.px(px_ + 2, py_ + 2, BRASS[4])
    K.text(cv, 9, 45, 'MARKEN', WALL[4], 'tiny')
    # hat shelf with brass brackets
    cv.rect(48, SHELF_Y, 316, SHELF_Y + 2, WOOD[4])
    cv.rect(48, SHELF_Y + 2, 316, SHELF_Y + 5, WOOD[2])
    cv.rect(48, SHELF_Y + 5, 316, SHELF_Y + 6, WOOD[0])
    for bx in (56, 186, 308):
        cv.line(bx, SHELF_Y + 6, bx, SHELF_Y + 13, BRASS[2])
        cv.line(bx, SHELF_Y + 13, bx + 5, SHELF_Y + 6, BRASS[2])
    # shadow under the shelf, then the rail, hooks and their number plates
    cv.dither_rect(48, SHELF_Y + 6, 316, SHELF_Y + 9, NIGHT[2], 0.4)
    cv.rect(44, 44, 316, 46, BRASS[2])
    cv.rect(44, 44, 316, 45, BRASS[4])
    for i, hx_ in enumerate(HOOKS_X):
        cv.rect(hx_ - 7, 36, hx_ + 7, 43, BRASS[1])
        cv.rect(hx_ - 6, 37, hx_ + 6, 42, BRASS[3])
        cv.rect(hx_ - 6, 37, hx_ + 6, 38, BRASS[4])
        num = HOOK_NUMBERS[i]
        K.text(cv, hx_ - K.text_width(num, 'tiny') // 2, 37, num, WOOD[0], 'tiny')
        cv.line(hx_, 46, hx_, 50, BRASS[3])
        cv.px(hx_ + 1, 50, BRASS[3])
        cv.px(hx_ + 2, 49, BRASS[2])
    return cv


def front() -> K.Cv:
    cv = K.Cv(W, H)
    y0 = COUNTER_Y
    cv.rect(0, y0, W, y0 + 2, BRASS[3])
    cv.rect(0, y0, W, y0 + 1, BRASS[4])
    cv.rect(0, y0 + 2, W, y0 + 6, WOOD[3])
    cv.rect(0, y0 + 6, W, y0 + 7, WOOD[1])
    cv.rect(0, y0 + 7, W, H, WOOD[2])
    for px0 in range(8, W - 20, 52):
        cv.frame(px0, y0 + 12, px0 + 44, H - 4, WOOD[1])
        cv.frame(px0 + 1, y0 + 13, px0 + 43, H - 5, WOOD[3])
        cv.px(px0 + 22, y0 + 20, BRASS[3])
    # on the counter: ledger, the tray with freshly polished spare plates, bell, lamp
    cv.rect(52, y0 - 4, 84, y0, WOOD[0])
    cv.rect(53, y0 - 5, 83, y0 - 3, PAPER[4])
    cv.rect(67, y0 - 5, 68, y0 - 3, PAPER[2])
    cv.rect(150, y0 - 3, 196, y0, WOOD[1])
    for i in range(6):
        cv.rect(153 + i * 7, y0 - 5, 159 + i * 7, y0 - 2, BRASS[3])
        cv.px(153 + i * 7, y0 - 5, BRASS[4])
    cv.ellipse(262, y0 - 3, 5, 3.2, BRASS[3])
    cv.ellipse(261, y0 - 4, 3, 2, BRASS[4])
    cv.rect(261, y0 - 8, 263, y0 - 6, BRASS[2])
    cv.rect(256, y0 - 1, 269, y0, BRASS[1])
    cv.rect(294, y0 - 26, 296, y0, BRASS[2])
    cv.poly([(285, y0 - 26), (305, y0 - 26), (301, y0 - 34), (289, y0 - 34)], PAPER[4])
    cv.rect(286, y0 - 27, 305, y0 - 26, AMBER[3])
    cv.rect(289, y0 - 2, 302, y0, BRASS[1])
    return cv


def closeup() -> K.Cv:
    cw, ch = 176, 120
    full = back()
    cv = K.Cv(cw, ch)
    ox, oy = 108, 4           # crop of the wall around hook 31
    for y in range(ch):
        for x in range(cw):
            cv.a[y, x] = full.a[min(H - 1, y + oy), min(W - 1, x + ox)]
    c = coat('elena')
    cv.paste(c, 174 - ox - COAT_W // 2, 46 - oy)
    b = hat('beret')
    cv.paste(b, 148 - ox - HAT_W // 2, SHELF_Y - HAT_H - oy)
    fr = front()
    for y in range(ch):
        for x in range(cw):
            v = fr.a[min(H - 1, y + oy), min(W - 1, x + ox)]
            if v[3] > 0:
                cv.a[y, x] = v
    cv.frame(0, 0, cw, ch, NIGHT[1])
    return cv


def main(argv) -> None:
    os.makedirs(OUT, exist_ok=True)
    written = []
    written.append(back().save(os.path.join(OUT, 'cloak_back.png')))
    written.append(front().save(os.path.join(OUT, 'cloak_front.png')))
    sheet = K.Cv(COAT_W * len(COATS), COAT_H)
    for i, k in enumerate(COATS):
        sheet.paste(coat(k), i * COAT_W, 0)
    written.append(sheet.save(os.path.join(OUT, 'cloak_coats.png')))
    hs = K.Cv(HAT_W * len(HATS), HAT_H)
    for i, k in enumerate(HATS):
        hs.paste(hat(k), i * HAT_W, 0)
    written.append(hs.save(os.path.join(OUT, 'cloak_hats.png')))
    gs = K.Cv(GW * 6, GH * len(GUESTS))
    for r, g in enumerate(GUESTS):
        for c, (outfit, expr) in enumerate([('suit', 'neutral'), ('suit', 'pleased'), ('suit', 'puzzled'),
                                            ('coat', 'neutral'), ('coat', 'pleased'), ('coat', 'puzzled')]):
            gs.paste(bust(g, outfit, expr), c * GW, r * GH)
    written.append(gs.save(os.path.join(OUT, 'cloak_guests.png')))
    ws = K.Cv(46 * 3, 60)
    for f in range(3):
        ws.paste(wenzel(f), f * 46, 0)
    written.append(ws.save(os.path.join(OUT, 'cloak_wenzel.png')))
    ts = K.Cv(14 * len(TOKENS), 14)
    for i, n in enumerate(TOKENS):
        ts.paste(token(n), i * 14, 0)
    written.append(ts.save(os.path.join(OUT, 'cloak_tokens.png')))
    ww = K.Cv(20 * 3, 30)
    for f in range(3):
        ww.paste(world_wenzel(f), f * 20, 0)
    written.append(ww.save(os.path.join(OUT, 'world_wenzel.png')))
    written.append(closeup().save(os.path.join(OUT, 'cloak_closeup.png')))
    layout = {
        'doc': 'tools/pixelgen/gen_mg_cloak.py -- art px; the game draws x3.',
        'size': [W, H],
        'counter_y': COUNTER_Y,
        'hooks_x': HOOKS_X,
        'hook_numbers': HOOK_NUMBERS,
        'coats': COATS,
        'coat_cell': [COAT_W, COAT_H],
        'coat_top': 46,
        'shelf_y': SHELF_Y,
        'hats_x': HATS_X,
        'hats': HATS,
        'hat_cell': [HAT_W, HAT_H],
        'tokens': TOKENS,
        'token_cell': [14, 14],
        'token_at': [226, COUNTER_Y - 12],
        'guests': GUESTS,
        'guest_cell': [GW, GH],
        'wenzel_cell': [46, 60],
        'wenzel_at': [2, 58],
        'world_wenzel_cell': [20, 30],
    }
    written.append(K.write_json(os.path.join(OUT, 'cloak_layout.json'), layout))
    for p in written:
        print('wrote', os.path.relpath(p, K.ROOT))


if __name__ == '__main__':
    main(sys.argv[1:])
