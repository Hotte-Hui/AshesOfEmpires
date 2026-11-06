"""gen_mg_c3p2_kartei -- art for the Chapter-3 part-2 mini-game "Die Suchkartei" (registry card hall, Konrad;
owner: exploration c3p2, TECHNICAL_ARCHITECTURE §12.8, documentation/C3P2_DESIGN.md §7).

    py -3 -P tools/pixelgen/gen_mg_c3p2_kartei.py          (then import under the shared lock)

Writes assets/ui/minigames/kartei/ at 1:1 art pixels (the game draws everything x3, or x2 for larger text):
  kartei_back.png     400x136  the card-hall floor at night (oak parquet, the green-shaded lamp's pool, cold window
                               light at the edges) with the fallen drawer of the commission's tracing index: back
                               wall, dark inner bottom, side walls, its shadow on the boards
  kartei_front.png    400x136  the drawer's front panel (drawn over the filed cards): oak, brass label holder
                               „SUCHKARTEI“, cup handle, the nut of the card rod
  kartei_tabs.png     15 x 22x36  the upper part of every card as it stands in the drawer: three guide cards
                               (pressboard, coloured tabs „B·Б“, „K·К“, „V·В“) and twelve index cards (origin
                               letter, year/number, two handwritten lines). German cards: cream stock, red printed
                               rule, blue-black ink. Russian cards: grey-blue stock, slate rule, violet ink.
  kartei_faces.png    9 x 46x30  the nine cards lying on the floor, full face: code as written, origin line in the
                               card's own script (BERLIN / БЕРЛИН …), two handwritten lines, the result stamp
                               (red: no information, blue: forwarded, grey: pending, green: address transmitted)
  kartei_closeup.png  200x120  close-up for the find (DiscoveryView, shown x3): the drawer in order, the card of
                               Teodor Wanek („Anschrift übermittelt“) lying on top
  world_drawer.png    2 x 34x12  world cue for L_C3_Registry (in front of the cabinets beside drawer C-17): frame 0
                               the fallen drawer and scattered cards, frame 1 empty (the drawer is back in place)
  kartei_layout.json  canvas size, drawer slots, cell sizes, atlas order and floor positions for
                      scripts/ui/minigames/kartei_game.gd; the card list itself is the game rule and lives in
                      scripts/ui/minigames/kartei_logic.gd (tests/test_c3p2_explore.gd checks both agree)
Deterministic (seeds = crc32 of names). Colours: data/chapters/c3.json palette "registry"; the one colour outside
it is the violet office ink of the Russian cards (VIOLET, three documented values). Fonts: the hand-made bitmap
fonts of mg_r7_v_kit (SMALL 5x7) and env_veltrava_lib (FONT_S 3x5 with Cyrillic) -- no font file is read.
"""
from __future__ import annotations

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import mg_r7_v_kit as K  # noqa: E402
import env_veltrava_lib as VL  # noqa: E402

OUT = os.path.join(K.ROOT, 'assets', 'ui', 'minigames', 'kartei')
R = K.pal('registry')

W, H = 400, 136
SLOT_W = 22
X0 = 22
TAB_Y = 6
TAB_W, TAB_H = 22, 36
FACE_W, FACE_H = 46, 30
FRONT_Y = 42
LIFT = 8

# --------------------------------------------------------------------------- the cards (mirror of kartei_logic.gd)
# id: (code as written, origin, lang, result)
CARDS = {
    'kranz': ('B 61/22', 'B', 'de', 'none'), 'ryschkowa': ('K 62/05', 'K', 'de', 'none'),
    'petrauskas': ('V 63/11', 'V', 'de', 'forwarded'),
    'kulikowa': ('K 63/09', 'K', 'de', 'none'), 'lacis': ('В 62/08', 'V', 'ru', 'none'),
    'hrubes': ('B 64/02', 'B', 'de', 'pending'), 'wiebe': ('Б 63/04', 'B', 'ru', 'forwarded'),
    'sorokin': ('К 61/17', 'K', 'ru', 'none'), 'wanek': ('V 64/03', 'V', 'de', 'address'),
    'sell': ('B 62/30', 'B', 'de', 'none'), 'hartl': ('В 63/15', 'V', 'ru', 'none'),
    'kowalenko': ('К 63/21', 'K', 'ru', 'none'),
}
GUIDES = {'guide_B': ('B', 'Б'), 'guide_K': ('K', 'К'), 'guide_V': ('V', 'В')}
FLOOR = ['kulikowa', 'lacis', 'hrubes', 'wiebe', 'sorokin', 'wanek', 'sell', 'hartl', 'kowalenko']
SOLVED = ['guide_B', 'kranz', 'sell', 'wiebe', 'hrubes', 'guide_K', 'sorokin', 'ryschkowa', 'kulikowa', 'kowalenko',
          'guide_V', 'lacis', 'petrauskas', 'hartl', 'wanek']
TABS = ['guide_B', 'guide_K', 'guide_V', 'kranz', 'ryschkowa', 'petrauskas'] + FLOOR
CITY = {('B', 'de'): 'BERLIN', ('K', 'de'): 'KARSK', ('V', 'de'): 'VELTRAVA',
        ('B', 'ru'): 'БЕРЛИН', ('K', 'ru'): 'КАРСК', ('V', 'ru'): 'ВЕЛЬТРАВА'}
# floor spots (top-left of each face), two loose rows
FLOOR_XY = {'kulikowa': (14, 68), 'lacis': (92, 71), 'hrubes': (170, 67), 'wiebe': (248, 70), 'sorokin': (326, 69),
            'wanek': (52, 104), 'sell': (130, 102), 'hartl': (208, 106), 'kowalenko': (286, 102)}

# --------------------------------------------------------------------------- colours
NIGHT = [R('night', i) for i in range(4)]
SLATE = [R('slate', i) for i in range(5)]
OAK = [R('oak', i) for i in range(5)]
LAMP = [R('lamp_green', i) for i in range(5)]
PAPER = [R('paper', i) for i in range(5)]
BRASS = [R('brass', i) for i in range(5)]
SNOW = [R('snow', i) for i in range(5)]
RED = [R('red', i) for i in range(4)]
VIOLET = [K.hx('3E2C5E'), K.hx('5C4488'), K.hx('8068B0')]          # Soviet office ink (fiolet), original pick
INK_DE = K.mix(NIGHT[2], SLATE[1], 0.5)
STOCK = {'de': [PAPER[2], PAPER[3], PAPER[4]],
         'ru': [K.mix(SNOW[0], PAPER[2], 0.45), K.mix(SNOW[1], PAPER[3], 0.4), K.mix(SNOW[2], PAPER[4], 0.35)]}
RULE = {'de': RED[2], 'ru': SLATE[3]}
INK = {'de': INK_DE, 'ru': VIOLET[1]}
GUIDE_TAB = {'B': [SLATE[2], SLATE[3], SLATE[4]], 'K': [BRASS[1], BRASS[2], BRASS[3]], 'V': [LAMP[2], LAMP[3], LAMP[4]]}
PRESS = [K.mix(LAMP[1], SLATE[1], 0.5), K.mix(LAMP[2], SLATE[2], 0.5), K.mix(LAMP[3], SLATE[3], 0.55)]
STAMP = {'none': RED[2], 'forwarded': SLATE[4], 'pending': PAPER[1], 'address': LAMP[3]}


def tiny(cv: K.Cv, x: int, y: int, s: str, c, alpha: float = 1.0) -> int:
    """env_veltrava_lib FONT_S (3x5, Latin + Cyrillic) onto a K.Cv; returns the end x."""
    cx = x
    for ch in s:
        if ch == ' ':
            cx += 2
            continue
        g, _acc = VL._glyph(ch, 's')
        if g is None:
            cx += 4
            continue
        for yy, row in enumerate(g):
            for xx, v in enumerate(row):
                if v == '#':
                    cv.px(cx + xx, y + yy, c, alpha)
        cx += len(g[0]) + 1
    return cx - 1


def tiny_w(s: str) -> int:
    return VL.text_width(s, 's')


def scribble(cv: K.Cv, x0: int, x1: int, y: int, c, seed: str, alpha: float = 0.75) -> None:
    """One handwritten line: short strokes with ascenders, never letters (names are read in the side panel)."""
    r = K.rng(seed)
    x = x0
    while x < x1:
        n = int(r.integers(2, 6))
        for i in range(n):
            if x + i >= x1:
                break
            dy = int(r.integers(0, 2))
            cv.px(x + i, y + dy, c, alpha)
            if r.random() < 0.18:
                cv.px(x + i, y - 1, c, alpha * 0.8)
        x += n + int(r.integers(1, 3))


# --------------------------------------------------------------------------- floor + drawer
def floor(cv: K.Cv) -> None:
    r = K.rng('kartei_floor')
    for y in range(H):
        row = y // 9
        off = (row * 23) % 61
        for x in range(W):
            seam = (y % 9 == 0) or ((x + off) % 61 == 0)
            n = r.random()
            c = OAK[1] if seam else (OAK[2] if n < 0.82 else OAK[3])
            if not seam and K.BAYER[y % 4, x % 4] < 0.12 and (x * 7 + row * 13) % 17 < 3:
                c = OAK[1]
            cv.px(x, y, c)
    # the green lamp's pool (warm paper light through the shade), dithered
    for y in range(H):
        for x in range(W):
            d = ((x - 232) / 175.0) ** 2 + ((y - 96) / 66.0) ** 2
            if d < 1.0:
                t = (1.0 - d) * 0.55
                if K.BAYER[y % 4, x % 4] < t:
                    cv.px(x, y, K.mix(OAK[3], LAMP[3], 0.35), 0.55)
                if d < 0.25 and K.BAYER[y % 4, x % 4] < (0.25 - d) * 1.6:
                    cv.px(x, y, K.mix(OAK[4], PAPER[3], 0.4), 0.45)
    # cold window light / night at the edges (vignette)
    for y in range(H):
        for x in range(W):
            e = max(0.0, max(abs(x - W / 2) / (W / 2), abs(y - H / 2) / (H / 2)) - 0.62) / 0.38
            if e > 0 and K.BAYER[y % 4, x % 4] < e * 0.85:
                cv.px(x, y, NIGHT[1] if (x + y) % 3 else SLATE[0], 0.6)
    # a pencil and a paper clip that fell with the drawer
    cv.line(358, 128, 380, 124, PAPER[1])
    cv.line(358, 129, 380, 125, BRASS[2])
    cv.px(381, 124, NIGHT[0])
    cv.frame(30, 126, 36, 129, SNOW[1])


def drawer_back(cv: K.Cv) -> None:
    cv.rect(10, 8, 394, 70, NIGHT[0], 0.55)                     # shadow on the boards
    cv.rect(8, 2, 392, 10, OAK[3])                               # back wall (top edge seen from above)
    cv.rect(8, 2, 392, 3, OAK[4])
    cv.rect(8, 9, 392, 10, OAK[1])
    cv.vgrad(14, 10, 386, 44, NIGHT[1], OAK[0])                  # inner bottom, dark
    for x in range(14, 386, 7):                                  # grain of the bottom board
        cv.px(x, 30 + (x * 3) % 9, OAK[1])
    cv.rect(8, 2, 14, 66, OAK[3])                                # side walls
    cv.rect(386, 2, 392, 66, OAK[3])
    cv.rect(13, 10, 14, 44, OAK[1])
    cv.rect(386, 10, 387, 44, OAK[1])
    cv.rect(8, 2, 9, 66, OAK[4])
    cv.rect(391, 2, 392, 66, OAK[2])


def drawer_front(cv: K.Cv) -> None:
    cv.rect(8, FRONT_Y, 392, 66, OAK[3])
    cv.rect(8, FRONT_Y, 392, FRONT_Y + 1, OAK[4])
    cv.rect(8, 65, 392, 66, OAK[1])
    cv.frame(14, 46, 386, 62, OAK[2])
    cv.rect(15, 47, 385, 48, OAK[4], 0.5)
    for x in range(16, 384, 11):                                 # grain
        cv.px(x, 52 + (x * 5) % 7, OAK[2])
    # brass label holder with the trilingual-in-spirit label (the drawer says only what it is)
    cv.rect(172, 47, 228, 58, BRASS[2])
    cv.frame(172, 47, 228, 58, BRASS[1])
    cv.rect(173, 47, 227, 48, BRASS[4])
    cv.rect(175, 49, 225, 56, PAPER[4])
    lab = 'SUCHKARTEI'
    tiny(cv, 200 - tiny_w(lab) // 2, 50, lab, INK_DE)
    # cup handle
    cv.rect(186, 58, 214, 64, BRASS[2])
    cv.rect(188, 58, 212, 61, BRASS[0])
    cv.rect(186, 63, 214, 64, BRASS[1])
    cv.rect(186, 58, 214, 59, BRASS[4])
    # the nut of the card rod
    cv.ellipse(30, 54, 2.6, 2.6, BRASS[1])
    cv.ellipse(30, 53.5, 1.6, 1.6, BRASS[3])
    cv.px(29, 53, BRASS[4])


# --------------------------------------------------------------------------- cards
def tab(cid: str) -> K.Cv:
    cv = K.Cv(TAB_W, TAB_H)
    if cid in GUIDES:
        o, cy = GUIDES[cid]
        col = GUIDE_TAB[o]
        cv.rect(1, 8, 21, TAB_H, PRESS[1])
        cv.rect(1, 8, 21, 9, PRESS[2])
        cv.rect(1, 8, 2, TAB_H, PRESS[2])
        cv.rect(20, 8, 21, TAB_H, PRESS[0])
        cv.rect(2, 0, 20, 10, col[1])                           # the tab sticking up
        cv.rect(2, 0, 20, 1, col[2])
        cv.rect(2, 9, 20, 10, col[0])
        s = o + '·' + cy
        x = 11 - K.text_width(s, 'small') // 2
        K.text(cv, x, 2, s, PAPER[4])
        for i in range(3):                                      # pressboard texture
            cv.px(4 + i * 6, 16 + (i * 5) % 9, PRESS[0])
            cv.px(6 + i * 5, 27 + (i * 3) % 5, PRESS[2])
        return cv
    code, origin, lang, _res = CARDS[cid]
    st = STOCK[lang]
    ink = INK[lang]
    cv.rect(1, 6, 21, TAB_H, st[2])
    cv.rect(1, 6, 21, 7, st[2])
    cv.rect(1, 6, 2, TAB_H, st[1])
    cv.rect(20, 6, 21, TAB_H, st[0])
    cv.rect(2, 8, 20, 9, RULE[lang])                            # printed rule of the form
    letter, rest = code.split(' ', 1)
    K.text(cv, 3, 10, letter, ink)
    tiny(cv, 11 - tiny_w(rest) // 2, 19, rest, ink)
    scribble(cv, 3, 18, 27, ink, 'tab_' + cid + '_1', 0.55)
    scribble(cv, 3, 14, 31, ink, 'tab_' + cid + '_2', 0.45)
    return cv


def face(cid: str) -> K.Cv:
    code, origin, lang, res = CARDS[cid]
    st = STOCK[lang]
    ink = INK[lang]
    cv = K.Cv(FACE_W, FACE_H)
    cv.rect(0, 0, FACE_W, FACE_H, st[2])
    cv.frame(0, 0, FACE_W, FACE_H, st[0])
    cv.rect(1, 1, FACE_W - 1, 2, st[2])
    cv.rect(2, 2, FACE_W - 2, 3, RULE[lang])
    K.text(cv, 3, 5, code, ink)
    tiny(cv, 3, 14, CITY[(origin, lang)], ink, 0.9)
    scribble(cv, 3, 27, 22, ink, 'face_' + cid + '_1', 0.7)
    scribble(cv, 3, 22, 26, ink, 'face_' + cid + '_2', 0.6)
    # result stamp (a rubber stamp's frame with a hatched field)
    sc = STAMP[res]
    cv.frame(30, 20, 43, 27, sc, 0.9)
    for y in range(21, 26):
        for x in range(31, 42):
            if (x + y) % 3 == 0:
                cv.px(x, y, sc, 0.55)
    # wear: a dog-ear or a crease, deterministic per card
    r = K.rng('face_wear_' + cid)
    if r.random() < 0.5:
        for i in range(4):
            for j in range(4 - i):
                cv.px(FACE_W - 1 - j, i, OAK[2])
        cv.line(FACE_W - 5, 0, FACE_W - 1, 4, st[0])
    else:
        x = int(r.integers(12, 32))
        cv.line(x, 1, x + 2, FACE_H - 2, st[1], 0.6)
    return cv


# --------------------------------------------------------------------------- outputs
def strip(cells) -> K.Cv:
    w, h = cells[0].w, cells[0].h
    out = K.Cv(w * len(cells), h)
    for i, c in enumerate(cells):
        out.paste(c, i * w, 0)
    return out


def closeup() -> K.Cv:
    full = K.Cv(W, H)
    floor(full)
    drawer_back(full)
    tabs = {cid: tab(cid) for cid in SOLVED}
    for i, cid in enumerate(SOLVED):
        dy = -6 if cid == 'wanek' else 0
        full.paste(tabs[cid], X0 + i * SLOT_W, TAB_Y + dy)
    drawer_front(full)
    cv = K.Cv(200, 120)
    x0 = 190
    cv.a[:, :, :] = full.a[0:120, x0:x0 + 200, :]
    f = face('wanek')
    cv.rect(119, 78, 167, 110, NIGHT[0], 0.6)                    # its shadow
    cv.paste(f, 118, 76)
    return cv


def world_drawer() -> K.Cv:
    cv = K.Cv(68, 12)
    # frame 0: the fallen drawer (18 x 6) with its brass label, a spill of cards on the boards
    d = K.Cv(34, 12)
    d.rect(8, 5, 26, 11, OAK[3])
    d.rect(8, 5, 26, 6, OAK[4])
    d.rect(9, 6, 25, 8, OAK[0])
    d.rect(15, 8, 19, 10, BRASS[3])
    d.rect(8, 10, 26, 11, OAK[1])
    for (x, y, w, h, c) in ((2, 8, 3, 2, PAPER[4]), (4, 10, 3, 1, STOCK['ru'][2]), (27, 9, 3, 2, PAPER[4]),
                            (30, 7, 2, 2, PAPER[3]), (11, 3, 3, 2, PAPER[4]), (21, 2, 3, 2, STOCK['ru'][2])):
        d.rect(x, y, x + w, y + h, c)
    d.px(12, 3, VIOLET[1])
    d.px(22, 2, VIOLET[1])
    d.outline(NIGHT[0])
    cv.paste(d, 0, 0)
    return cv                                                   # frame 1 stays empty


def layout() -> dict:
    return {
        'doc': 'Generated by tools/pixelgen/gen_mg_c3p2_kartei.py -- read by scripts/ui/minigames/kartei_game.gd. '
               'Art px; the card rule (codes, origins, order) is scripts/ui/minigames/kartei_logic.gd.',
        'size': [W, H], 'slot_w': SLOT_W, 'x0': X0, 'tab_y': TAB_Y, 'tab_cell': [TAB_W, TAB_H],
        'face_cell': [FACE_W, FACE_H], 'front_y': FRONT_Y, 'lift': LIFT, 'caret': [2, 44],
        'tabs': TABS, 'faces': FLOOR,
        'floor': {cid: list(FLOOR_XY[cid]) for cid in FLOOR},
        'codes': {cid: CARDS[cid][0] for cid in CARDS},
        'solved': SOLVED,
        'world_cell': [34, 12],
    }


def main(argv) -> None:
    os.makedirs(OUT, exist_ok=True)
    for cid in CARDS:
        assert K.text_width(CARDS[cid][0], 'small') <= FACE_W - 6, cid
        assert tiny_w(CITY[(CARDS[cid][1], CARDS[cid][2])]) <= FACE_W - 6, cid
    back = K.Cv(W, H)
    floor(back)
    drawer_back(back)
    front = K.Cv(W, H)
    drawer_front(front)
    written = [
        back.save(os.path.join(OUT, 'kartei_back.png')),
        front.save(os.path.join(OUT, 'kartei_front.png')),
        strip([tab(c) for c in TABS]).save(os.path.join(OUT, 'kartei_tabs.png')),
        strip([face(c) for c in FLOOR]).save(os.path.join(OUT, 'kartei_faces.png')),
        closeup().save(os.path.join(OUT, 'kartei_closeup.png')),
        world_drawer().save(os.path.join(OUT, 'world_drawer.png')),
        K.write_json(os.path.join(OUT, 'kartei_layout.json'), layout()),
    ]
    for p in written:
        print('wrote', os.path.relpath(p, K.ROOT).replace('\\', '/'))


if __name__ == '__main__':
    main(sys.argv[1:])
