"""gen_mg_flap -- art for the Chapter-3 mini-game "Die Fallblatttafel" (Bahnhof Veltrava, Alexei; owner: minigames r7).

    py -3 -P tools/pixelgen/gen_mg_flap.py          (then import under the shared lock)

Writes assets/ui/minigames/flap/ at 1:1 art pixels (the game draws everything x3, nearest):
  flap_board.png     252x110  the split-flap arrivals board ANKUNFT · ПРИБЫТИЕ · ARRIVÉE: iron housing with rivets,
                              header and date plate, column labels, rows 2-3 baked (11:05 KORDON 1 · 14:30 WIEN LINZ 2),
                              empty module windows of row 1 (the game draws its flaps) and the maker's plate
                              "W. HOLUB · VELTRAVA" (fictional)
  flap_faces.png     one row per drum of row 1 (hour, tens, units, from, via, track), one 18 px tall face per flap in
                              drum order; the KARSK flap is new (whiter glyphs, cleaner black) -- the detail Alexei notes
  flap_faces_hc.png  the same faces in pure white on pure black (high-contrast setting)
  flap_hatch.png     252x34   the opened service hatch under row 1: axle, bearing blocks and the four couplings
                              (carry pin units->tens, bent hooks tens->hour, from->via, track->via)
  world_flap_board.png 3 x 84x41  the board as a world prop for L_C3_Station (bolted to canopy column 3): frames 0/1 the
                              jammed top row twitching, frame 2 restored
  flap_closeup.png   240x96   close-up for the find (DiscoveryView, shown x3): the restored line and the new KARSK flap
  flap_layout.json   module rects, drum flap lists, start / target, couplings and hatch rects for
                              scripts/ui/minigames/flap_game.gd (flap_logic.gd mirrors DRUMS / START / TARGET)
Deterministic (seeds = crc32 of names). Colours: data/chapters/c3.json palette "veltrava". No insignia, no brands.
Fonts: the hand-made bitmaps of tools/pixelgen/mg_r7_v_kit.py.
"""
from __future__ import annotations

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import mg_r7_v_kit as K  # noqa: E402

OUT = os.path.join(K.ROOT, 'assets', 'ui', 'minigames', 'flap')
C = K.pal('veltrava')

W, H = 252, 110
X0 = 13                      # first module x
ROW_Y = [33, 55, 77]         # module tops of rows 1-3
FACE_H = 18
SPLIT = 9                    # first row of the lower half
CELL = 9                     # glyph advance of the big font (7 px glyph + 2 px gap)

# drum id, characters, flap list (mirrored in scripts/ui/minigames/flap_logic.gd)
DRUMS = [
    ('hour', 2, [str(h) for h in range(24)]),
    ('tens', 1, [str(d) for d in range(6)]),
    ('units', 1, [str(d) for d in range(10)]),
    ('from', 9, ['', 'BERLIN', 'WIEN', 'PRAG', 'KORDON', 'MINSK', 'MOSKVA', 'ZÜRICH', 'STOCKHOLM', 'HELSINKI']),
    ('via', 8, ['', 'KORDON', 'MINSK', 'KARSK', 'PRAG', 'LINZ', 'SMOLENSK', 'KIEW']),
    ('track', 1, [str(g) for g in range(1, 9)]),
]
START = [17, 2, 7, 3, 0, 1]      # 17:27 PRAG – Gleis 2 (the jam)
TARGET = [8, 4, 1, 6, 3, 4]      # 8:41 MOSKVA über KARSK, Gleis 5
STATIC_ROWS = [[11, 0, 5, 4, 0, 0], [14, 3, 0, 2, 5, 1]]
COUPLINGS = [  # driver -> driven, kind; the hatch shows each where the two drums meet
    ('units', 'tens', 'carry'), ('tens', 'hour', 'drag'), ('from', 'via', 'drag'), ('track', 'via', 'drag')]
NEW_FLAP = ('via', 'KARSK')


def module_x() -> dict:
    xs, x = {}, X0
    for i, (did, n, _f) in enumerate(DRUMS):
        w = CELL * n + 2
        xs[did] = (x, w)
        x += w + (4 if did == 'hour' else 1 if did == 'tens' else 3)
    return xs


MX = module_x()


# ============================================================================ flap faces
def face(text: str, n: int, did: str, idx: int, hc: bool = False, new: bool = False) -> K.Cv:
    w = CELL * n + 2
    cv = K.Cv(w, FACE_H)
    if hc:
        bg_t, bg_b, ink = K.hx('#000000'), K.hx('#000000'), K.hx('#ffffff')
        split, lip = K.hx('#000000'), K.hx('#5e666e')
    else:
        bg_t = C('iron', 1) if new else C('iron', 0)
        bg_b = C('iron', 1) if new else C('night', 1)
        ink = C('snow', 4) if new else C('cream', 5)
        split, lip = C('night', 0), C('iron', 2)
    cv.rect(0, 0, w, SPLIT, bg_t)
    cv.rect(0, SPLIT, w, FACE_H, bg_b)
    if not hc and not new:      # worn flaps: a few scuffs, rounded corners
        r = K.rng('face/%s/%d' % (did, idx))
        for _ in range(max(1, w // 14)):
            x, y = int(r.integers(1, w - 1)), int(r.integers(1, FACE_H - 1))
            cv.px(x, y, C('iron', 2))
    # glyphs: names left, numbers right-aligned in their cells
    if did in ('hour', 'tens', 'units', 'track'):
        s = text.rjust(n)
    else:
        s = text.ljust(n)
    gy = 3
    tx = 1
    for i, ch in enumerate(s):
        if ch == ' ':
            continue
        K.text(cv, tx + i * CELL + 1, gy, ch, ink, 'big')
        if not hc and not new:   # printed ink is a little worn on old flaps: drop the odd pixel to cream 4
            pass
    if not hc and not new:
        # the lower half of old flaps is slightly yellowed: tint glyph pixels below the split
        for y in range(SPLIT, FACE_H):
            for x in range(w):
                c = cv.a[y, x]
                if c[3] > 0 and abs(c[0] - ink[0]) < 1 and abs(c[1] - ink[1]) < 1:
                    if K.BAYER[y % 4, x % 4] < 0.35:
                        cv.a[y, x] = C('cream', 4)
    # split line + lip of the lower flap: on the card only -- printed strokes stay readable, just shaded
    for x in range(w):
        c = cv.a[SPLIT - 1, x]
        is_ink = c[3] > 0 and (c[0] > 120 or hc and c[0] > 100)
        cv.a[SPLIT - 1, x] = (C('cream', 3) if not hc else K.hx('#c8c8c8')) if is_ink else split
        c2 = cv.a[SPLIT, x]
        is_ink2 = c2[3] > 0 and (c2[0] > 120 or hc and c2[0] > 100)
        if not is_ink2:
            cv.a[SPLIT, x] = lip
    # rounded corners (the flap is a card, not a tile)
    for (x, y) in ((0, 0), (w - 1, 0), (0, FACE_H - 1), (w - 1, FACE_H - 1)):
        cv.a[y, x] = [0, 0, 0, 0]
    if new and not hc:
        # a crisp new card: brighter top edge
        cv.rect(1, 0, w - 1, 1, C('iron', 3))
    return cv


def faces_sheet(hc: bool) -> K.Cv:
    maxw = max(CELL * n + 2 for _d, n, f in DRUMS)
    maxn = max(len(f) for _d, n, f in DRUMS)
    sheet = K.Cv(maxw * maxn, FACE_H * len(DRUMS))
    for row, (did, n, flaps) in enumerate(DRUMS):
        w = CELL * n + 2
        for i, t in enumerate(flaps):
            new = (did, t) == NEW_FLAP
            f = face(t, n, did, i, hc, new)
            sheet.paste(f, i * w, row * FACE_H)
    return sheet


# ============================================================================ board
def rivet(cv: K.Cv, x: int, y: int) -> None:
    cv.px(x, y, C('iron', 4))
    cv.px(x + 1, y, C('iron', 3))
    cv.px(x, y + 1, C('iron', 3))
    cv.px(x + 1, y + 1, C('night', 0))


def housing(cv: K.Cv, w: int, h: int) -> None:
    cv.rect(0, 0, w, h, C('night', 1))
    cv.rect(1, 1, w - 1, h - 1, C('iron', 1))
    cv.rect(1, 1, w - 1, 2, C('iron', 3))
    cv.rect(1, 1, 2, h - 1, C('iron', 2))
    cv.rect(1, h - 2, w - 1, h - 1, C('night', 2))
    cv.rect(w - 2, 1, w - 1, h - 1, C('night', 2))
    cv.dither_rect(2, 2, w - 2, h - 2, C('iron', 2), 0.12)
    cv.frame(3, 3, w - 3, h - 3, C('night', 2))
    cv.rect(4, 4, w - 4, h - 4, C('night', 2))


def board() -> K.Cv:
    cv = K.Cv(W, H)
    housing(cv, W, H)
    # header plate
    cv.rect(7, 6, W - 7, 23, C('slate', 1))
    cv.rect(7, 6, W - 7, 7, C('slate', 3))
    cv.rect(7, 22, W - 7, 23, C('night', 1))
    K.text(cv, 12, 11, 'ANKUNFT · ПРИБЫТИЕ · ARRIVÉE', C('cream', 5), 'small')
    date = '12.02.1964'
    dw = K.text_width(date, 'small')
    cv.rect(W - 16 - dw, 8, W - 9, 21, C('night', 2))
    K.text(cv, W - 12 - dw, 11, date, C('lamp', 3), 'small')
    # column labels
    lab = C('cream', 3)
    xs = MX
    K.text(cv, xs['hour'][0] + 1, 24, 'ZEIT', lab, 'small')
    K.text(cv, xs['from'][0] + 1, 24, 'AUS', lab, 'small')
    K.text(cv, xs['via'][0] + 1, 24, 'ÜBER', lab, 'small')
    gl = K.text_width('GLEIS', 'small')
    K.text(cv, xs['track'][0] + xs['track'][1] - gl, 24, 'GLEIS', lab, 'small')
    # module windows of all rows; rows 2-4 carry their flaps
    for r, y in enumerate(ROW_Y):
        for di, (did, n, flaps) in enumerate(DRUMS):
            x, w = xs[did]
            cv.rect(x - 1, y - 1, x + w + 1, y + FACE_H + 1, C('night', 0))
            if r == 0:
                cv.rect(x, y, x + w, y + FACE_H, C('night', 1))
                cv.rect(x, y + SPLIT - 1, x + w, y + SPLIT, C('night', 0))
            else:
                idx = STATIC_ROWS[r - 1][di]
                f = face(flaps[idx], n, did, idx, False, (did, flaps[idx]) == NEW_FLAP)
                cv.paste(f, x, y)
        # the colon between hour and minutes
        cx = xs['hour'][0] + xs['hour'][1] + 1
        cv.rect(cx, y + 5, cx + 2, y + 7, C('cream', 4))
        cv.rect(cx, y + 11, cx + 2, y + 13, C('cream', 4))
        # row lamp (lit by the game when row 1 engages)
        cv.rect(7, y + 7, 10, y + 11, C('night', 0))
        cv.px(8, y + 8, C('iron', 3))
    # maker's plate (fictional)
    plate = 'W. HOLUB · VELTRAVA'
    pw = K.text_width(plate, 'tiny')
    px0 = (W - pw) // 2
    cv.rect(px0 - 4, 98, px0 + pw + 4, 106, C('iron', 3))
    cv.rect(px0 - 3, 99, px0 + pw + 3, 105, C('iron', 2))
    K.text(cv, px0, 99, plate, C('night', 1), 'tiny')
    for (x, y) in ((5, 5), (W - 7, 5), (5, H - 7), (W - 7, H - 7), (W // 2 - 1, 3), (W // 4, 3), (3 * W // 4, 3)):
        rivet(cv, x, y)
    return cv


# ============================================================================ service hatch under row 1
HATCH_H = 34
AXLE_Y = 17


def hatch() -> tuple:
    cv = K.Cv(W, HATCH_H)
    housing(cv, W, HATCH_H)
    cv.rect(4, 4, W - 4, HATCH_H - 4, C('night', 0))
    cv.dither_rect(4, 4, W - 4, HATCH_H - 4, C('night', 1), 0.3)
    # axle through all drums
    cv.rect(6, AXLE_Y, W - 6, AXLE_Y + 1, C('iron', 3))
    cv.rect(6, AXLE_Y + 1, W - 6, AXLE_Y + 2, C('iron', 1))
    rects = {}
    for did, n, _f in DRUMS:
        x, w = MX[did]
        rects[did] = [x, 9, w, 17]
        # brass end caps at both ends (the drums are drawn by the game between them) and a bearing block below
        for bx in (x - 1, x + w):
            cv.rect(bx, 9, bx + 1, 26, C('lamp', 1))
            cv.px(bx, 9, C('lamp', 2))
            cv.px(bx, 17, C('lamp', 3))
        cv.rect(x + w // 2 - 2, 26, x + w // 2 + 3, 29, C('iron', 2))
        cv.rect(x + w // 2 - 2, 26, x + w // 2 + 3, 27, C('iron', 3))
    couplings = []
    for drv, drn, kind in COUPLINGS:
        a, b = MX[drv], MX[drn]
        # the joint sits in the gap between the two neighbouring drums
        left, right = (a, b) if a[0] < b[0] else (b, a)
        gx0 = left[0] + left[1]
        gx1 = right[0]
        if kind == 'carry':
            # carry pin on the units drum reaching into a notch of the tens drum (brass)
            cv.rect(gx0 - 3, 6, gx1 + 3, 9, C('lamp', 2))
            cv.rect(gx0 - 3, 6, gx1 + 3, 7, C('lamp', 3))
            cv.rect(gx1 + 1, 6, gx1 + 3, 12, C('lamp', 1))
            cv.px(gx0 - 3, 9, C('lamp', 1))
            rect = [gx0 - 4, 5, gx1 - gx0 + 8, 8]
        else:
            # bent wire hook below the axle, caught on the cards of both drums
            y0 = 24
            for k in (0, 1):
                cv.line(gx0 - 4, 21 + k, gx0 - 2, y0 + 3 + k, C('snow', 2 - k))
                cv.line(gx0 - 2, y0 + 3 + k, gx1 + 1, y0 + 3 + k, C('snow', 2 - k))
                cv.line(gx1 + 1, y0 + 3 + k, gx1 + 3, 21 + k, C('snow', 2 - k))
            rect = [gx0 - 5, 20, gx1 - gx0 + 10, 10]
        couplings.append({'from': drv, 'to': drn, 'kind': kind, 'rect': rect})
    return cv, rects, couplings


# ============================================================================ world prop (L_C3_Station, column 3)
WW, WH = 84, 41


def world_frames() -> K.Cv:
    sheet = K.Cv(WW * 3, WH)
    cols = [3, 23, 52, 76]     # time, from, via, track (x inside the board face)
    rows = [('11:05', 'KORDON', '', '1'), ('14:30', 'WIEN', 'LINZ', '2')]
    for fi in range(3):
        cv = K.Cv(WW, WH)
        # two brackets to the column behind (top) and the hanging plate
        for bx in (34, 48):
            cv.rect(bx, 0, bx + 2, 6, C('iron', 2))
            cv.px(bx, 0, C('iron', 3))
        cv.rect(30, 4, 54, 6, C('iron', 1))
        bx0, by0 = 0, 5
        bw, bh = WW, WH - 5
        cv.rect(bx0, by0, bx0 + bw, by0 + bh, C('night', 0))
        cv.rect(bx0 + 1, by0 + 1, bx0 + bw - 1, by0 + bh - 1, C('iron', 1))
        cv.rect(bx0 + 1, by0 + 1, bx0 + bw - 1, by0 + 2, C('iron', 3))
        cv.rect(bx0 + 2, by0 + 2, bx0 + bw - 2, by0 + bh - 2, C('night', 1))
        # header
        cv.rect(bx0 + 2, by0 + 2, bx0 + bw - 2, by0 + 9, C('slate', 1))
        K.text(cv, bx0 + 4, by0 + 3, 'ANKUNFT', C('cream', 5), 'tiny')
        K.text(cv, bx0 + 38, by0 + 3, 'ПРИБ.', C('cream', 4), 'tiny')
        K.text(cv, bx0 + 63, by0 + 3, '12.02', C('lamp', 3), 'tiny')
        # rows (row 1 = top)
        for r in range(3):
            ry = by0 + 11 + r * 7
            cv.rect(bx0 + 2, ry - 1, bx0 + bw - 2, ry + 6, C('night', 0))
            for cx0, cx1 in ((2, 20), (22, 49), (51, 73), (75, 81)):
                cv.rect(bx0 + cx0, ry - 1, bx0 + cx1, ry + 6, C('iron', 0))
            if r == 0:
                if fi == 2:
                    vals = ('8:41', 'MOSKVA', 'KARSK', '5')
                    ink = [C('cream', 5), C('cream', 5), C('snow', 4), C('cream', 5)]
                else:
                    vals = None
            else:
                vals = rows[r - 1]
                ink = [C('cream', 4)] * 4
            if vals is not None:
                for k, v in enumerate(vals):
                    if v:
                        K.text(cv, bx0 + cols[k] + (1 if k == 0 and len(v) == 4 else 0), ry, v, ink[k], 'tiny')
                if r == 0 and fi == 2:     # the new KARSK card: brighter background behind the white glyphs
                    for y in range(ry - 1, ry + 6):
                        for x in range(bx0 + 51, bx0 + 73):
                            if cv.a[y, x][3] > 0 and tuple(cv.a[y, x][:3]) == tuple(C('iron', 0)[:3]):
                                cv.a[y, x] = C('iron', 1)
            else:
                # the jam: half-fallen cards, mismatched halves, one card sticking out
                r2 = K.rng('world_jam/%d' % fi)
                for cx0, cx1 in ((2, 20), (22, 49), (51, 73), (75, 81)):
                    for x in range(bx0 + cx0, bx0 + cx1):
                        for y in range(ry, ry + 5):
                            if r2.random() < 0.28:
                                cv.px(x, y, C('cream', 3 if y < ry + 2 else 2))
                    cv.rect(bx0 + cx0, ry + 2, bx0 + cx1, ry + 3, C('night', 0))
                stick_x = 30 if fi == 0 else 58
                cv.rect(bx0 + stick_x, ry - 3, bx0 + stick_x + 9, ry - 1, C('cream', 3))
                cv.rect(bx0 + stick_x, ry - 1, bx0 + stick_x + 9, ry, C('iron', 2))
        for (x, y) in ((2, by0 + bh - 3), (bw - 4, by0 + bh - 3)):
            cv.px(bx0 + x, y, C('iron', 4))
        sheet.paste(cv, fi * WW, 0)
    return sheet


# ============================================================================ close-up for the find
def closeup(faces: dict) -> K.Cv:
    cw, ch = 240, 96
    cv = K.Cv(cw, ch)
    cv.rect(0, 0, cw, ch, C('night', 1))
    cv.dither_rect(0, 0, cw, ch, C('iron', 1), 0.18)
    # header strip
    cv.rect(0, 6, cw, 22, C('slate', 1))
    cv.rect(0, 6, cw, 7, C('slate', 3))
    K.text(cv, 8, 11, 'ANKUNFT · ПРИБЫТИЕ · ARRIVÉE', C('cream', 5), 'small')
    # restored row 1 (shifted so the line sits centred)
    off = -X0 + (cw - (MX['track'][0] + MX['track'][1] - X0)) // 2
    y = 34
    for di, (did, n, flaps) in enumerate(DRUMS):
        x, w = MX[did]
        x += off
        cv.rect(x - 1, y - 1, x + w + 1, y + FACE_H + 1, C('night', 0))
        cv.paste(faces[(did, TARGET[di])], x, y)
    hx_ = MX['hour'][0] + MX['hour'][1] + 1 + off
    cv.rect(hx_, y + 5, hx_ + 2, y + 7, C('cream', 4))
    cv.rect(hx_, y + 11, hx_ + 2, y + 13, C('cream', 4))
    # row 2 below, cut by the frame
    y2 = 58
    for di, (did, n, flaps) in enumerate(DRUMS):
        x, w = MX[did]
        x += off
        cv.rect(x - 1, y2 - 1, x + w + 1, y2 + FACE_H + 1, C('night', 0))
        cv.paste(faces[(did, STATIC_ROWS[0][di])], x, y2)
    cv.rect(hx_, y2 + 5, hx_ + 2, y2 + 7, C('cream', 4))
    cv.rect(hx_, y2 + 11, hx_ + 2, y2 + 13, C('cream', 4))
    # cool platform light from the top, the lamp of row 1 lit
    cv.dither_rect(0, ch - 18, cw, ch, C('night', 0), 0.55)
    lx = MX['hour'][0] + off - 6
    cv.rect(lx, y + 7, lx + 3, y + 11, C('lamp', 3))
    cv.px(lx + 1, y + 8, C('lamp', 4))
    # frame
    cv.frame(0, 0, cw, ch, C('night', 0))
    return cv


def main(argv) -> None:
    os.makedirs(OUT, exist_ok=True)
    written = []
    sheet = faces_sheet(False)
    written.append(sheet.save(os.path.join(OUT, 'flap_faces.png')))
    written.append(faces_sheet(True).save(os.path.join(OUT, 'flap_faces_hc.png')))
    written.append(board().save(os.path.join(OUT, 'flap_board.png')))
    hcv, hrects, couplings = hatch()
    written.append(hcv.save(os.path.join(OUT, 'flap_hatch.png')))
    written.append(world_frames().save(os.path.join(OUT, 'world_flap_board.png')))
    faces = {}
    for did, n, flaps in DRUMS:
        for i, t in enumerate(flaps):
            faces[(did, i)] = face(t, n, did, i, False, (did, t) == NEW_FLAP)
    written.append(closeup(faces).save(os.path.join(OUT, 'flap_closeup.png')))
    layout = {
        'doc': 'tools/pixelgen/gen_mg_flap.py -- art px; the game draws x3. rects [x, y, w, h].',
        'size': [W, H],
        'hatch_size': [W, HATCH_H],
        'face_h': FACE_H,
        'split': SPLIT,
        'row_y': ROW_Y,
        'row_lamp': [7, 7, 3, 4],
        'drums': [{'id': did, 'chars': n, 'x': MX[did][0], 'w': MX[did][1], 'sheet_row': i, 'flaps': flaps}
                  for i, (did, n, flaps) in enumerate(DRUMS)],
        'start': START,
        'target': TARGET,
        'static_rows': STATIC_ROWS,
        'new_flap': list(NEW_FLAP),
        'hatch_drums': hrects,
        'axle_y': AXLE_Y,
        'couplings': couplings,
        'world_frame': [WW, WH],
    }
    written.append(K.write_json(os.path.join(OUT, 'flap_layout.json'), layout))
    for p in written:
        print('wrote', os.path.relpath(p, K.ROOT))


if __name__ == '__main__':
    main(sys.argv[1:])
