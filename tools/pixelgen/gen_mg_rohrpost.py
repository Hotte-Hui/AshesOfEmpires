"""gen_mg_rohrpost -- original pixel art for the Berlin mini-game "Rohrpost" (TECHNICAL_ARCHITECTURE 12.8).

Run:  py -3 -P tools/pixelgen/gen_mg_rohrpost.py        (Pillow + numpy, deterministic, no downloads)

Writes assets/ui/minigames/rohrpost/ (UI art drawn 1:1 and STORED x3 nearest, like assets/ui/minigames/):
  rohrpost_board_{1,2,3}.png  the switch board ("Weichentafel") of the archive's house tube system, one per capsule:
                              enamel panel in a wooden frame, brass tubes with flanges, diverter housings (the UI
                              draws the knob state), a crossing, station mouths, board 2: a frozen line with its tag
  rohrpost_knob.png           6 frames 18x18: diverter knob with the engraved channel W-E, N-S, N-E, E-S, S-W, W-N
  rohrpost_capsule.png        2 frames 12x12: the capsule (leather, brass caps) horizontal / vertical
  rohrpost_lamp.png           2 frames 8x8: station pilot lamp off / on
  rohrpost_layout.json        the three boards (grid, tiles, diverters, stations, frozen cells) + geometry in ART px;
                              read by scripts/ui/minigames/rohrpost_logic.gd (single source of the puzzle data)
  find_capsules.png           1:1 close-up for the find (<= 320x200): the opened capsule and the three things it brought
The boards are verified here (solve()): every board has exactly one way to the reading room with the fewest changes,
and the start setting sends the capsule somewhere else.  Colours: data/palettes.json "archive" / "berlin".
No regime insignia anywhere (12.4).
"""
from __future__ import annotations

import itertools
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mg_r7_kb_lib import (F35, F57, ROOT, Canvas, P, bayer, draw_text, draw_text_centered, hx, mix, rng,  # noqa: E402
                          save_1x, save_json, save_x3, text_width)

OUT = os.path.join(ROOT, 'assets', 'ui', 'minigames', 'rohrpost')
CS = 22                       # grid cell (art px)
COLS, ROWS = 8, 5
ML, MT, MR, MB = 52, 16, 58, 16
MOUTH_H, MOUTH_V = 10, 6      # how far a station mouth stands out of the grid (W/E, N/S)
BW, BH = ML + COLS * CS + MR, MT + ROWS * CS + MB
TUBE_R = 3.2                  # tube radius
OPEN = {'h': 'WE', 'v': 'NS', 'NE': 'NE', 'NW': 'NW', 'SE': 'SE', 'SW': 'SW'}
OPP = {'N': 'S', 'S': 'N', 'E': 'W', 'W': 'E'}
STEP = {'N': (0, -1), 'S': (0, 1), 'E': (1, 0), 'W': (-1, 0)}
PAIRS = ['WE', 'NS', 'NE', 'ES', 'SW', 'WN']   # knob frames (rohrpost_knob.png)


def A(ramp, i, a=255):
    return P('archive', ramp, i, a)


def B(ramp, i, a=255):
    return P('berlin', ramp, i, a)


def grid(rows):
    t = {}
    for r, line in enumerate(rows):
        for c, tok in enumerate(line.split()):
            if tok != '.':
                t['%d,%d' % (c, r)] = tok
    return t


# ================================================================================ the three boards
# Mirrored nowhere else: rohrpost_layout.json is the single source for scripts/ui/minigames/rohrpost_logic.gd.
BOARDS = [
    {'id': 1, 'note': 'mg.tube.board.1', 'content': 'mg.tube.content.1',
     'source': {'cell': [0, 3], 'side': 'W'}, 'target': 'lesesaal',
     'stations': [{'id': 'lesesaal', 'cell': [7, 1], 'side': 'E'}, {'id': 'abt3', 'cell': [7, 2], 'side': 'E'},
                  {'id': 'registratur', 'cell': [7, 3], 'side': 'E'}],
     'tiles': grid([". . . . . . . .",
                    ". . SE h h D h h",
                    ". . v . . NE h h",
                    "h h D h h h h h",
                    ". . . . . . . ."]),
     'diverters': [{'cell': [2, 3], 'states': ['WE', 'WN', 'NE'], 'start': 0},
                   {'cell': [5, 1], 'states': ['WE', 'SW', 'ES'], 'start': 1}],
     'frozen': []},
    {'id': 2, 'note': 'mg.tube.board.2', 'content': 'mg.tube.content.2',
     'source': {'cell': [0, 2], 'side': 'W'}, 'target': 'lesesaal',
     'stations': [{'id': 'lesesaal', 'cell': [7, 2], 'side': 'E'}, {'id': 'direktion', 'cell': [3, 0], 'side': 'N'},
                  {'id': 'kantine', 'cell': [2, 4], 'side': 'S'}],
     'tiles': grid([". SE h D h h SW .",
                    ". v . . . . v .",
                    "h D h h h h D h",
                    ". v . . . . . .",
                    ". NE SW . . . . ."]),
     'diverters': [{'cell': [1, 2], 'states': ['WE', 'WN', 'SW'], 'start': 0},
                   {'cell': [3, 0], 'states': ['WE', 'WN', 'NE'], 'start': 1},
                   {'cell': [6, 2], 'states': ['WE', 'NE', 'WN'], 'start': 2}],
     'frozen': [[4, 2]]},
    {'id': 3, 'note': 'mg.tube.board.3', 'content': 'mg.tube.content.3',
     'source': {'cell': [0, 3], 'side': 'W'}, 'target': 'lesesaal',
     'stations': [{'id': 'lesesaal', 'cell': [7, 0], 'side': 'E'}, {'id': 'registratur', 'cell': [7, 2], 'side': 'E'},
                  {'id': 'planarchiv', 'cell': [5, 4], 'side': 'S'}, {'id': 'loge', 'cell': [0, 1], 'side': 'W'},
                  {'id': 'direktion', 'cell': [2, 0], 'side': 'N'}, {'id': 'kantine', 'cell': [1, 4], 'side': 'S'}],
     'tiles': grid([". SE D h D h h h",
                    "h NW . . v . . .",
                    ". . SE h x h D h",
                    "h D NW . v . v .",
                    ". v . . NE D NW ."]),
     'diverters': [{'cell': [1, 3], 'states': ['WE', 'SW', 'ES'], 'start': 1},
                   {'cell': [6, 2], 'states': ['WE', 'SW', 'ES'], 'start': 0},
                   {'cell': [5, 4], 'states': ['WE', 'ES', 'SW'], 'start': 1},
                   {'cell': [4, 0], 'states': ['WE', 'SW', 'ES'], 'start': 1},
                   {'cell': [2, 0], 'states': ['WE', 'WN', 'NE'], 'start': 0}],
     'frozen': []},
]


def simulate(b, states):
    """same rules as rohrpost_logic.gd: ('arrive', station) / ('jam'|'frozen'|'dead'|'open'|'loop', cell)"""
    divs = {tuple(d['cell']): i for i, d in enumerate(b['diverters'])}
    st = {(tuple(s['cell']), s['side']): s['id'] for s in b['stations']}
    cell, enter = tuple(b['source']['cell']), b['source']['side']
    seen = set()
    while True:
        if (cell, enter) in seen:
            return ('loop', cell)
        seen.add((cell, enter))
        if list(cell) in b['frozen']:
            return ('frozen', cell)
        if cell in divs:
            pair = b['diverters'][divs[cell]]['states'][states[divs[cell]]]
            if enter not in pair:
                return ('jam', cell)
            out = pair[1] if pair[0] == enter else pair[0]
        else:
            t = b['tiles'].get('%d,%d' % cell)
            if t is None:
                return ('open', cell)
            if t == 'x':
                out = OPP[enter]
            else:
                o = OPEN[t]
                if enter not in o:
                    return ('dead', cell)
                out = o[1] if o[0] == enter else o[0]
        if (cell, out) in st:
            return ('arrive', st[(cell, out)])
        cell = (cell[0] + STEP[out][0], cell[1] + STEP[out][1])
        if not (0 <= cell[0] < COLS and 0 <= cell[1] < ROWS):
            return ('open', cell)
        enter = OPP[out]


def solve(b):
    start = [d['start'] for d in b['diverters']]
    best = []
    for combo in itertools.product(*[range(len(d['states'])) for d in b['diverters']]):
        if simulate(b, list(combo)) == ('arrive', b['target']):
            best.append((sum(1 for i, v in enumerate(combo) if v != start[i]), combo))
    best.sort()
    return best


def verify():
    for i, b in enumerate(BOARDS):
        for d in b['diverters']:
            assert '%d,%d' % tuple(d['cell']) in b['tiles'] and b['tiles']['%d,%d' % tuple(d['cell'])] == 'D'
            assert all(p in PAIRS for p in d['states'])
        sols = solve(b)
        assert sols, 'board %d unsolvable' % b['id']
        assert simulate(b, [d['start'] for d in b['diverters']]) != ('arrive', b['target']), 'board %d starts solved' % b['id']
        assert len([s for s in sols if s[0] == sols[0][0]]) == 1, 'board %d: minimal solution not unique' % b['id']
        assert sols[0][0] == i + 2, 'board %d needs %d changes' % (b['id'], sols[0][0])
    return [solve(b)[0][1] for b in BOARDS]


# ================================================================================ drawing helpers
def cell_xy(c, r):
    return ML + c * CS, MT + r * CS


def side_mid(c, r, side):
    x, y = cell_xy(c, r)
    h = CS / 2.0
    return {'N': (x + h, y), 'S': (x + h, y + CS), 'W': (x, y + h), 'E': (x + CS, y + h)}[side]


# polished brass of the tubes and knobs (archive amber in the shadows, warmer gold in the lights)
BRASS = [hx('#3D2616'), A('amber', 0), hx('#9A6A33'), hx('#C29245'), hx('#E4BC6A'), hx('#F7E0A0')]


def brass(k):
    return BRASS[max(0, min(5, k))]


def tube_px(cv: Canvas, x, y, d, nx, ny, frozen=False, r=None, radius=TUBE_R):
    """shade one tube pixel at distance d from the centre line with outward normal (nx, ny); light from the upper left"""
    if d > radius + 0.5:
        return
    if d > radius - 0.4:
        cv.px(x, y, A('night', 0))
        return
    nd = d / radius
    lit = nx * -0.6 + ny * -0.8                         # > 0 on the side facing the light
    v = 0.55 + 0.5 * lit * nd + 0.22 * (1.0 - nd * nd)
    if lit > 0.2 and 0.25 < nd < 0.6:
        v += 0.25                                        # specular streak
    f = max(0.0, min(5.0, v * 5.0))
    k = int(f)
    if bayer(x, y) < (f - k) * 0.8:
        k += 1
    col = brass(k)
    if frozen:
        ice = [P('berlin', 'snow', i) for i in range(5)]
        col = ice[max(0, min(4, k - 1))]
    cv.px(x, y, col)


def stroke_line(cv, x0, y0, x1, y1, **kw):
    """straight tube segment (axis aligned)"""
    if abs(y1 - y0) < 0.01:      # horizontal
        for x in range(int(min(x0, x1)), int(max(x0, x1)) + 1):
            for y in range(int(y0 - TUBE_R - 1), int(y0 + TUBE_R + 2)):
                d = abs(y + 0.5 - y0)
                tube_px(cv, x, y, d, 0.0, 1.0 if y + 0.5 > y0 else -1.0, **kw)
    else:
        for y in range(int(min(y0, y1)), int(max(y0, y1)) + 1):
            for x in range(int(x0 - TUBE_R - 1), int(x0 + TUBE_R + 2)):
                d = abs(x + 0.5 - x0)
                tube_px(cv, x, y, d, 1.0 if x + 0.5 > x0 else -1.0, 0.0, **kw)


def stroke_arc(cv, c, r, a, b, **kw):
    """quarter arc between the midpoints of sides a and b of cell (c, r), centred on their shared corner"""
    x, y = cell_xy(c, r)
    corner = {frozenset('NE'): (x + CS, y), frozenset('NW'): (x, y), frozenset('SE'): (x + CS, y + CS),
              frozenset('SW'): (x, y + CS)}[frozenset(a + b)]
    R = CS / 2.0
    for py in range(y - 1, y + CS + 1):
        for px_ in range(x - 1, x + CS + 1):
            dx, dy = px_ + 0.5 - corner[0], py + 0.5 - corner[1]
            dist = math.hypot(dx, dy)
            if dist < 0.01:
                continue
            if not (x <= px_ < x + CS and y <= py < y + CS):
                continue
            d = abs(dist - R)
            sgn = 1.0 if dist > R else -1.0
            tube_px(cv, px_, py, d, dx / dist * sgn, dy / dist * sgn, **kw)


def flange(cv, x, y, horizontal):
    """a flange ring where a tube crosses a cell border; (x, y) = point on the border"""
    if horizontal:                       # tube runs horizontally: band is vertical
        for yy in range(int(y - TUBE_R - 1), int(y + TUBE_R + 2)):
            cv.px(x - 1, yy, brass(1))
            cv.px(x, yy, brass(3) if yy < y else brass(2))
        cv.px(x - 1, int(y - TUBE_R - 2), A('night', 0))
        cv.px(x, int(y - TUBE_R - 2), A('night', 0))
        cv.px(x - 1, int(y + TUBE_R + 2), A('night', 0))
        cv.px(x, int(y + TUBE_R + 2), A('night', 0))
    else:
        for xx in range(int(x - TUBE_R - 1), int(x + TUBE_R + 2)):
            cv.px(xx, y - 1, brass(1))
            cv.px(xx, y, brass(3) if xx < x else brass(2))
        cv.px(int(x - TUBE_R - 2), y - 1, A('night', 0))
        cv.px(int(x - TUBE_R - 2), y, A('night', 0))
        cv.px(int(x + TUBE_R + 2), y - 1, A('night', 0))
        cv.px(int(x + TUBE_R + 2), y, A('night', 0))


def stub(cv, c, r, side, length, **kw):
    """tube from the cell centre (minus `length` from the side) to the side midpoint"""
    x, y = cell_xy(c, r)
    h = CS / 2.0
    cx, cy = x + h, y + h
    mx, my = side_mid(c, r, side)
    if side in 'WE':
        sx = mx + (length if side == 'W' else -length)
        stroke_line(cv, min(sx, mx), cy, max(sx, mx), cy, **kw)
    else:
        sy = my + (length if side == 'N' else -length)
        stroke_line(cv, cx, min(sy, my), cx, max(sy, my), **kw)


def panel(cv: Canvas, r):
    """enamel panel in a wooden frame with screws and the engraved title plate"""
    en = [B('patina', i) for i in range(5)]
    for y in range(BH):
        for x in range(BW):
            v = 1.25 - y / BH * 0.6 + 0.18 * math.sin(x * 0.05) + r.normal(0, 0.05)
            k = int(v)
            if bayer(x, y) < v - k:
                k += 1
            cv.px(x, y, en[max(0, min(2, k))])
    # faint plan grid engraved in the enamel (the panel is a technical drawing too)
    for c in range(COLS + 1):
        for y in range(MT - 4, MT + ROWS * CS + 4):
            if (y // 2) % 2 == 0:
                cv.px(ML + c * CS, y, en[0])
    for rr in range(ROWS + 1):
        for x in range(ML - 4, ML + COLS * CS + 4):
            if (x // 2) % 2 == 0:
                cv.px(x, MT + rr * CS, en[0])
    # frame
    wood = [A('wood', i) for i in range(6)]
    for y in range(BH):
        for x in range(BW):
            e = min(x, y, BW - 1 - x, BH - 1 - y)
            if e < 5:
                g = math.sin((x + y) * 0.3 + math.sin(x * 0.05) * 2)
                k = (4 if e == 0 else 3 if e < 2 else 2) + (1 if g > 0.8 else 0)
                if x > BW - 6 or y > BH - 6:
                    k -= 2
                cv.px(x, y, wood[max(0, min(5, k))])
            elif e == 5:
                cv.px(x, y, A('night', 0))
    for sx, sy in ((9, 9), (BW - 10, 9), (9, BH - 10), (BW - 10, BH - 10)):
        cv.disc(sx, sy, 2.2, brass(2))
        cv.px(sx - 1, sy - 1, brass(5))
        cv.line(sx - 1, sy + 1, sx + 1, sy - 1, brass(0))
    # engraved brass plate (top right, clear of every station plate the UI draws)
    label = 'HAUSROHRPOST  1938'
    w = text_width(label, F35) + 10
    px0, py0 = BW - 14 - w, 3
    cv.rect(px0, py0, px0 + w, py0 + 11, brass(3))
    cv.frame(px0, py0, px0 + w, py0 + 11, brass(1))
    cv.hline(px0 + 1, px0 + w - 1, py0 + 1, brass(5))
    draw_text(cv, px0 + 5, py0 + 3, label, brass(0), F35)


def mouth(cv, c, r, side, kind):
    """tube from the grid edge into the margin, ending in a brass mouth (station)"""
    mx, my = side_mid(c, r, side)
    ln = MOUTH_H if side in 'WE' else MOUTH_V
    if side == 'W':
        stroke_line(cv, mx - ln, my, mx, my)
        ex, ey = mx - ln, my
    elif side == 'E':
        stroke_line(cv, mx, my, mx + ln, my)
        ex, ey = mx + ln, my
    elif side == 'N':
        stroke_line(cv, mx, my - ln, mx, my)
        ex, ey = mx, my - ln
    else:
        stroke_line(cv, mx, my, mx, my + ln)
        ex, ey = mx, my + ln
    # funnel ring
    if side in 'WE':
        for yy in range(int(ey - 5), int(ey + 6)):
            for k in range(3):
                xx = ex + (-k if side == 'W' else k)
                col = brass(4 - k) if yy < ey else brass(2 - (k > 1))
                if abs(yy - ey) >= 5:
                    col = A('night', 0)
                cv.px(xx, yy, col)
        cv.rect(ex - (2 if side == 'W' else 0), ey - 2, ex + (1 if side == 'W' else 3), ey + 3, A('night', 0))
    else:
        for xx in range(int(ex - 5), int(ex + 6)):
            for k in range(3):
                yy = ey + (-k if side == 'N' else k)
                col = brass(4 - k) if xx < ex else brass(2 - (k > 1))
                if abs(xx - ex) >= 5:
                    col = A('night', 0)
                cv.px(xx, yy, col)
        cv.rect(ex - 2, ey - (2 if side == 'N' else 0), ex + 3, ey + (1 if side == 'N' else 3), A('night', 0))


def housing(cv, c, r):
    x, y = cell_xy(c, r)
    cx, cy = x + CS / 2.0 - 0.5, y + CS / 2.0 - 0.5
    cv.disc(cx + 1, cy + 1, 11.0, A('night', 0))
    for yy in range(int(cy - 12), int(cy + 13)):
        for xx in range(int(cx - 12), int(cx + 13)):
            d = math.hypot(xx - cx, yy - cy)
            if d > 10.6:
                continue
            if d > 9.0:
                lit = ((xx - cx) * -0.6 + (yy - cy) * -0.8) / d
                cv.px(xx, yy, brass(4 if lit > 0.3 else (2 if lit > -0.3 else 1)))
            else:
                cv.px(xx, yy, A('night', 1))
    for a in (45, 135, 225, 315):
        cv.px(cx + math.cos(math.radians(a)) * 9.8, cy + math.sin(math.radians(a)) * 9.8, brass(0))


def board_art(b) -> Canvas:
    r = rng('rohrpost_board_%d' % b['id'])
    cv = Canvas(BW, BH)
    panel(cv, r)
    frozen = {tuple(f) for f in b['frozen']}
    # stations (mouths) first so the grid tubes overlap their joints
    for s in b['stations']:
        mouth(cv, s['cell'][0], s['cell'][1], s['side'], 'out')
    mouth(cv, b['source']['cell'][0], b['source']['cell'][1], b['source']['side'], 'in')
    # tubes
    tiles = b['tiles']
    cross = []
    for key, t in sorted(tiles.items()):
        c, rr = (int(v) for v in key.split(','))
        fz = (c, rr) in frozen
        x, y = cell_xy(c, rr)
        h = CS / 2.0
        if t == 'h':
            stroke_line(cv, x, y + h, x + CS - 1, y + h, frozen=fz)
        elif t == 'v':
            stroke_line(cv, x + h, y, x + h, y + CS - 1, frozen=fz)
        elif t == 'x':
            cross.append((c, rr))
            stroke_line(cv, x, y + h, x + CS - 1, y + h)
        elif t == 'D':
            d = next(d for d in b['diverters'] if d['cell'] == [c, rr])
            sides = set(''.join(d['states']))
            for sd in sides:
                stub(cv, c, rr, sd, 9)
        else:
            stroke_arc(cv, c, rr, t[0], t[1], frozen=fz)
    # crossings: the vertical tube passes over the horizontal one (shadow + clamps)
    for c, rr in cross:
        x, y = cell_xy(c, rr)
        h = CS / 2.0
        for yy in range(int(y + h - TUBE_R - 1), int(y + h + TUBE_R + 2)):
            cv.px(x + h + TUBE_R + 1.5, yy, brass(0))
            cv.px(x + h + TUBE_R + 2.5, yy, brass(1))
        stroke_line(cv, x + h, y, x + h, y + CS - 1)
        for yy in (y + h - 6, y + h + 6):
            cv.hline(int(x + h - 5), int(x + h + 6), int(yy), A('night', 1))
            cv.hline(int(x + h - 4), int(x + h + 5), int(yy) - 1, A('night', 2))
    # flanges on cell borders
    for key, t in sorted(tiles.items()):
        c, rr = (int(v) for v in key.split(','))
        x, y = cell_xy(c, rr)
        h = CS / 2.0
        opens = set()
        if t in OPEN:
            opens = set(OPEN[t])
        elif t == 'x':
            opens = set('NSWE')
        elif t == 'D':
            d = next(d for d in b['diverters'] if d['cell'] == [c, rr])
            opens = set(''.join(d['states']))
        for sd in opens:
            if sd == 'E':
                flange(cv, x + CS, int(y + h), True)
            elif sd == 'S':
                flange(cv, int(x + h), y + CS, False)
            elif sd == 'W' and c == 0:
                flange(cv, x + 1, int(y + h), True)
            elif sd == 'N' and rr == 0:
                flange(cv, int(x + h), y + 1, False)
    # diverter housings (the knob is drawn by the UI)
    for d in b['diverters']:
        housing(cv, d['cell'][0], d['cell'][1])
    # frozen line: frost, icicles and a red tag "GESPERRT"
    for c, rr in frozen:
        x, y = cell_xy(c, rr)
        h = CS / 2.0
        for i in range(110):
            xx = x - 2 + int(r.integers(0, CS + 4))
            yy = int(round(y + h + r.normal(0, 4.0)))
            cv.px(xx, yy, P('berlin', 'snow', 4) if r.random() < 0.55 else P('berlin', 'snow', 2))
        for ix in range(x + 2, x + CS - 2, 4):
            ln = int(r.integers(2, 6))
            for k in range(ln):
                cv.px(ix, int(y + h + TUBE_R + 1 + k), P('berlin', 'snow', 4 - min(3, k)))
        # tag on a string
        tx, ty = int(x + h) - 18, int(y + h + 9)
        cv.line(int(x + h), int(y + h + 3), tx + 18, ty, A('paper', 1))
        cv.rect(tx, ty, tx + 37, ty + 10, A('ink', 3))
        cv.frame(tx, ty, tx + 37, ty + 10, A('ink', 2))
        draw_text_centered(cv, tx + 19, ty + 3, 'GESPERRT', A('paper', 5), F35)
    return cv


# ================================================================================ sprites
def knob():
    n = 18
    sheet = Canvas(n * len(PAIRS), n)
    for f, pair in enumerate(PAIRS):
        c = Canvas(n, n)
        cx = cy = n / 2.0 - 0.5
        for y in range(n):
            for x in range(n):
                d = math.hypot(x - cx, y - cy)
                if d > 8.6:
                    continue
                if d > 7.0:                                  # turned brass rim with knurls
                    lit = ((x - cx) * -0.6 + (y - cy) * -0.8) / d
                    k = 3 + (1 if lit > 0.3 else 0) - (1 if lit < -0.3 else 0)
                    if int((math.atan2(y - cy, x - cx) + math.pi) / (2 * math.pi) * 20) % 2:
                        k -= 1
                    c.px(x, y, brass(k))
                else:
                    c.px(x, y, A('night', 1) if d > 5.8 else A('night', 2))
        # the channel: a brass tube piece inside the well, joining the two connected sides
        a, b2 = pair[0], pair[1]
        rad = 2.6
        for y in range(n):
            for x in range(n):
                if math.hypot(x - cx, y - cy) > 7.6:
                    continue
                px_, py_ = x + 0.5, y + 0.5
                if OPP[a] == b2:
                    if a in 'WE':
                        d = abs(py_ - n / 2.0)
                        nx, ny = 0.0, (1.0 if py_ > n / 2.0 else -1.0)
                    else:
                        d = abs(px_ - n / 2.0)
                        nx, ny = (1.0 if px_ > n / 2.0 else -1.0), 0.0
                else:
                    corner = {frozenset('NE'): (n, 0.0), frozenset('NW'): (0.0, 0.0), frozenset('SE'): (n, n),
                              frozenset('SW'): (0.0, n)}[frozenset(pair)]
                    dx, dy = px_ - corner[0], py_ - corner[1]
                    dist = math.hypot(dx, dy)
                    d = abs(dist - n / 2.0)
                    sg = 1.0 if dist > n / 2.0 else -1.0
                    nx, ny = dx / max(0.01, dist) * sg, dy / max(0.01, dist) * sg
                if d <= rad + 0.5:
                    tube_px(c, x, y, d, nx, ny, radius=rad)
        c.disc(cx, cy, 1.0, brass(1))
        c.outline(A('night', 0))
        sheet.paste(c, f * n, 0)
    save_x3(sheet, os.path.join(OUT, 'rohrpost_knob.png'))


def capsule():
    """the capsule as seen through the tube wall: dark leather body, bright brass caps, a light rim so it reads
    against the brass of the tubes"""
    n = 12
    sheet = Canvas(n * 2, n)
    leather = [A('night', 1), A('wood', 1), A('wood', 2)]
    for f in (0, 1):
        c = Canvas(n, n)
        for i in range(10):
            for j in range(6):
                cap = i < 2 or i > 7
                if cap:
                    col = brass(5 if j < 2 else (4 if j < 4 else 2))
                else:
                    col = leather[2 if j < 2 else (1 if j < 4 else 0)]
                    if j == 1 and 3 <= i <= 6:
                        col = A('amber', 2)          # sheen on the leather
                    if i == 5:
                        col = A('night', 0)          # the seam of the lid
                x, y = (1 + i, 3 + j) if f == 0 else (3 + j, 1 + i)
                c.px(x, y, col)
        c.outline(A('paper', 5))
        sheet.paste(c, f * n, 0)
    save_x3(sheet, os.path.join(OUT, 'rohrpost_capsule.png'))


def lamp():
    n = 8
    sheet = Canvas(n * 2, n)
    for f in (0, 1):
        c = Canvas(n, n)
        c.disc(3.5, 3.5, 3.4, brass(1))
        glass = [A('ink', 2), A('amber', 1)] if f == 0 else [A('amber', 4), A('amber', 5)]
        c.disc(3.5, 3.5, 2.3, glass[0])
        c.px(3, 3, glass[1])
        c.px(2, 2, glass[1] if f else A('amber', 2))
        c.outline(A('night', 0))
        sheet.paste(c, f * n, 0)
    save_x3(sheet, os.path.join(OUT, 'rohrpost_lamp.png'))


# ================================================================================ close-up for the find (1:1)
def slip(cv, x0, y0, w, h, lines, paper, ink, r, font=F35, title_ink=None):
    cv.rect(x0 + 2, y0 + 2, x0 + w + 2, y0 + h + 2, A('night', 1))
    for y in range(y0, y0 + h):
        for x in range(x0, x0 + w):
            v = 0.5 + 0.3 * math.sin(x * 0.09 + y * 0.05) + r.normal(0, 0.1)
            cv.px(x, y, paper[1] if v > 0.45 else paper[0])
    cv.frame(x0, y0, x0 + w, y0 + h, paper[2])
    y = y0 + 4
    for i, ln in enumerate(lines):
        col = title_ink if (i == 0 and title_ink is not None) else ink
        draw_text(cv, x0 + 4, y, ln, col, font)
        y += 8 if i == 0 else 7


def find_capsules():
    W, H = 300, 180
    cv = Canvas(W, H, A('wood', 2))
    r = rng('find_capsules')
    # reading-room desk: dark wood with a green baize writing pad and the lamp's warm light
    for y in range(H):
        for x in range(W):
            g = math.sin(x * 0.06 + math.sin(y * 0.11) * 1.8)
            k = 2 + (1 if g > 0.7 else 0)
            cv.px(x, y, A('wood', k))
    baize = [B('patina', 1), B('patina', 2), B('patina', 3)]
    for y in range(14, 170):
        for x in range(20, 282):
            v = 1.0 + 0.6 * max(0.0, 1.0 - math.hypot(x - 120, y - 60) / 200.0) + r.normal(0, 0.12)
            cv.px(x, y, baize[int(max(0, min(2, round(v))))])
    cv.frame(20, 14, 282, 170, A('night', 0))
    cv.frame(21, 15, 281, 169, B('patina', 4))
    paper = [A('paper', 4), A('paper', 5), A('paper', 2)]
    ink = A('ink', 0)
    # 1: the porter's loan slip
    slip(cv, 30, 22, 96, 50, ['LEIHSCHEIN', 'BREHMS TIERLEBEN', 'BAND: VÖGEL', 'GRUND: RING AM BEIN', 'PFORTE'],
         paper, A('ink', 1), r, title_ink=A('ink', 3))
    # 2: the house management circular (typed, with a stamp)
    slip(cv, 136, 26, 104, 56, ['RUNDSCHREIBEN', 'WER HAT IM LESESAAL', 'DIE HEIZUNG AUF-', 'GEDREHT? UM MELDUNG', 'WIRD GEBETEN.', 'HAUSVERWALTUNG'],
         paper, ink, r, title_ink=ink)
    vio = hx('#4B3A6B')
    cv.frame(206, 66, 236, 78, vio)
    draw_text_centered(cv, 221, 70, 'EINGANG', vio, F35)
    # 3: the sandwich in parchment, tied with string, pencil on the paper
    sx0, sy0 = 140, 98
    parch = [A('paper', 3), A('paper', 4)]
    for y in range(sy0, sy0 + 50):
        for x in range(sx0, sx0 + 92):
            fold = (x - sx0 + (y - sy0) // 2) % 23 == 0
            cv.px(x, y, A('paper', 2) if fold else parch[1 if bayer(x, y) < 0.6 else 0])
    cv.frame(sx0, sy0, sx0 + 92, sy0 + 50, A('paper', 1))
    cv.rect(sx0 + 3, sy0 + 50, sx0 + 95, sy0 + 53, A('night', 1))
    cv.vline(sx0 + 30, sy0, sy0 + 50, A('amber', 2))
    cv.hline(sx0, sx0 + 92, sy0 + 34, A('amber', 2))
    cv.disc(sx0 + 30, sy0 + 34, 1.6, A('amber', 3))
    draw_text(cv, sx0 + 36, sy0 + 6, 'FÜR DEN', A('wall', 1), F35)
    draw_text(cv, sx0 + 36, sy0 + 13, 'LESESAAL.', A('wall', 1), F35)
    draw_text(cv, sx0 + 36, sy0 + 22, 'SIE VERGESSEN', A('wall', 1), F35)
    draw_text(cv, sx0 + 36, sy0 + 38, 'IMMER DAS ESSEN.', A('wall', 1), F35)
    # the opened capsule (leather body, brass caps), its lid beside it
    cx0, cy0 = 34, 104
    for i in range(80):
        for j in range(22):
            cap = i < 9 or i > 70
            if cap:
                col = brass(5 if j < 4 else (4 if j < 9 else (3 if j < 15 else 1)))
            else:
                col = (A('amber', 2), A('wood', 4), A('wood', 3), A('wood', 2))[min(3, j // 6)]
                if (i - 9) % 15 == 0:
                    col = A('wood', 1)
            cv.px(cx0 + i, cy0 + j, col)
    cv.rect(cx0 + 79, cy0 + 3, cx0 + 84, cy0 + 19, A('night', 0))          # open end
    cv.disc(cx0 + 64, cy0 + 47, 9.0, A('night', 1))                         # the lid, set down beside it
    cv.disc(cx0 + 63, cy0 + 45, 9.0, brass(2))
    cv.disc(cx0 + 62, cy0 + 44, 6.5, brass(4))
    cv.disc(cx0 + 63, cy0 + 45, 2.0, brass(1))
    cv.rect(cx0 + 2, cy0 + 22, cx0 + 82, cy0 + 25, A('night', 1))
    # address ring on the capsule
    draw_text(cv, cx0 + 24, cy0 + 8, 'LESESAAL', A('paper', 5), F35)
    save_1x(cv, os.path.join(OUT, 'find_capsules.png'))


def layout(solutions):
    boards = []
    for b, sol in zip(BOARDS, solutions):
        bb = dict(b)
        bb['solution'] = list(sol)
        boards.append(bb)
    save_json(os.path.join(OUT, 'rohrpost_layout.json'), {
        '_doc': 'Rohrpost mini-game: the three boards of the archive house tube system. Geometry in ART px '
                '(rohrpost_board_N.png is stored x3): grid origin [ML, MT], cell size, grid size. tiles: "c,r" -> '
                'h | v | NE | NW | SE | SW (curve between the two sides) | x (crossing, no junction) | D (diverter). '
                'diverters: cell, states = side pairs the knob connects (cycled by turning; frames of rohrpost_knob.png '
                'follow knob_frames), start = index of the setting when the board opens. stations: where a side of a cell '
                'leads out of the grid. source: where the capsule from the porter\'s lodge enters. frozen: cells a capsule '
                'cannot pass. solution: the unique fewest-change setting (written by gen_mg_rohrpost.py after verify()).',
        'cell': CS, 'grid': [COLS, ROWS], 'origin': [ML, MT], 'board_size': [BW, BH], 'knob_frames': PAIRS,
        'mouth': [MOUTH_H, MOUTH_V],
        'knob_size': 18, 'capsule_size': 12, 'lamp_size': 8, 'boards': boards})


def main():
    sols = verify()
    for b in BOARDS:
        save_x3(board_art(b), os.path.join(OUT, 'rohrpost_board_%d.png' % b['id']))
    knob()
    capsule()
    lamp()
    find_capsules()
    layout(sols)
    print('gen_mg_rohrpost: boards verified, solutions', sols)
    print('gen_mg_rohrpost: wrote', sorted(os.listdir(OUT)))


if __name__ == '__main__':
    main()
