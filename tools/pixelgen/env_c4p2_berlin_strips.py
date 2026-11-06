"""env_c4p2_berlin_strips -- the people of L_C4P2_Berlin as life strips, placed with intent (C4P2_DESIGN §4):

Ostbahnhof (scene A): the two officials of the liaison booth at one desk (a German railway policeman stamping, a
Soviet liaison officer with his tea glass in its metal holder), the baggage clerk writing slips, a boy asleep on
the family's suitcase, the kiosk woman folding papers, the engine driver leaning out of the cab, the diners and the
waiter in the dining car (and Ekdahl's empty table), a passenger lifting his case into the rack of the sleeper.
Kolonnenstraße 14 (scene B): the households of the house puzzle in their windows -- the Schulz mother walking the
baby, Lenz at his desk with the radio dial, the Mertens family at supper, Frau Pohl's curtain, Ilse drawing at
Hanna's kitchen table (until the house is solved) / Hanna at her window (after), Frau Kuhnert knitting by the
radio in the lodge, the Kühns' card game; after the puzzle: the sweep's men in the passage, the car's lights, the
candle in the cobbler's souterrain.  Plus the steam, snow, smoke and lamp loops.
"""
from __future__ import annotations

import math

import numpy as np

import env_c4p2_berlin_kit as K
import env_c4p2_berlin_layout as L
import env_c4p2_berlin_life as LF


def _clip_rects(w, h, rects, x0, y0):
    m = np.zeros((h, w), bool)
    for (rx, ry, rw, rh) in rects:
        a, b = max(0, rx - x0), min(w, rx - x0 + rw)
        c, d = max(0, ry - y0), min(h, ry - y0 + rh)
        if b > a and d > c:
            m[c:d, a:b] = True
    return m


def _own(st, name, box):
    """The strip's clip: the pixels its object owns in the baked layer (Station.owned)."""
    x0, y0, w, h = box
    return st.owned(name)[y0:y0 + h, x0:x0 + w].copy()


# =========================================================================== A: the station
def booth_officials(st):
    x0, x1 = L.BOOTH
    top = 206
    box = (x0 + 2, top + 4, x1 - x0 - 4, 30)                     # the glazing down to the desk (y 210..240)
    bx, by = box[0], box[1]

    def draw(lay, k):
        # the German railway policeman (left), stamping, then ruling a line, then looking across
        arm = 'write' if k < 8 else ('table' if k < 16 else None)
        face = 1 if k < 20 else -1
        LF.person(lay, 15 - bx + x0 - 2, 236 - by, k=k, s=0.9, coat=('B', 2.2), skin=('Y', 1.4),
                  hair=('I', 1.2), hat=('B', 1.6, 'cap'), face=face, arm=arm, rim=('L', 3.0), collar=('B', 1.4))
        if arm == 'write':                                                     # the stamp going up and down
            lay.rect(15 - bx + x0 + 4, 236 - by - 4 - (k % 2) * 2, 2, 2, 'D', 3.0)
        # the Soviet liaison officer (right), the tea glass in its holder: drinks at frames 10..14
        up = 10 <= k <= 14
        LF.person(lay, 47 - bx + x0 - 2, 236 - by, k=k, s=0.9, coat=('E', 2.4), skin=('Y', 1.2),
                  hair=('I', 1.6), hat=('E', 1.8, 'field'), face=-1, arm='up' if up else 'table', rim=('L', 3.2))
        lay.px(47 - bx + x0 - 6, 236 - by - 12, 'L', 3.8)                       # shoulder board
        gx, gy = (47 - bx + x0 - 9, 236 - by - 14) if up else (47 - bx + x0 - 10, 236 - by - 4)
        lay.rect(gx, gy, 2, 3, 'P', 6.0)                                       # the glass
        lay.rect(gx - 1, gy + 1, 1, 2, 'S', 4.4)                                # the metal holder's handle
        lay.hline(gx, gy + 2, 2, 'S', 4.0)
        # the mullions stay in front of them
        for mx in (x0 + 2, x0 + 19, x0 + 36, x1 - 3):
            lay.vline(mx - bx, 0, 30, 'S', 3.4)
    c, e = LF.life_strip(st.lay.c, st.lay.em, box, 24, draw, 'A', clip=_own(st, 'booth', box))
    return c, e, box, 24, 6


def baggage_clerk(st):
    box = (176, 230, 20, 20)

    def draw(lay, k):
        arm = 'write' if k < 8 else ('out' if k < 11 else 'table')
        LF.person(lay, 10, 20, k=k, s=0.85, coat=('S', 3.0), skin=('Y', 1.4), hair=('I', 1.6), face=-1, arm=arm,
                  rim=('L', 3.0), collar=('P', 5.0), bend=1 if k < 8 else 0)
        if arm == 'out':
            lay.rect(2, 13, 4, 3, 'P', 6.4)                                     # the slip handed out
    c, e = LF.life_strip(st.lay.c, st.lay.em, box, 16, draw, 'A', clip=_own(st, 'baggage', box))
    return c, e, box, 16, 5


def sleeping_boy(st):
    """exp_corridor_permit: a boy asleep on the family's suitcase in front of the buffet (a transparent strip in
    the playfield, y-sorted in front of the counter): the case lying flat with straps, corner caps and a label; the
    boy on his side on top -- his cheek on his folded arm, the knitted cap slipped back with its bobble, the scarf,
    the navy coat rising with his breath, knees drawn up, white socks, one shoe over the edge, a little wooden
    engine held to his chest.  The buffet's bulbs light his top edges.  Now and then his foot twitches."""
    box = (228, 266, 36, 28)

    def draw(lay, k):
        # the suitcase: lid seen a little from above, the front face, corner caps, straps with buckles, the label
        lay.rect(3, 17, 30, 2, 'D', 3.4, hgt=0.7)
        lay.rect(3, 19, 30, 8, 'D', 2.4, hgt=0.5)
        lay.hline(3, 26, 30, 'D', 1.2)
        lay.hline(4, 19, 28, 'D', 1.8)                                            # the lid's seam
        for (cx_, cy_) in ((3, 17), (31, 17), (3, 25), (31, 25)):
            lay.rect(cx_, cy_, 2, 2, 'S', 3.2)
        for sx in (9, 26):
            lay.rect(sx, 17, 2, 10, 'L', 2.0)
            lay.rect(sx, 21, 2, 2, 'S', 4.2)
        lay.rect(16, 21, 5, 3, 'P', 6.0)
        lay.hline(17, 22, 3, 'R', 2.4)
        lay.hline(16, 20, 4, 'D', 1.0)                                            # the handle
        b = 1 if 4 <= k % 12 <= 7 else 0                                          # he breathes
        twitch = 1 if k % 12 == 9 else 0
        # the arm under his head (sleeve), the red mitten on its string
        lay.rect(3, 14, 9, 3, 'B', 2.2, hgt=0.5)
        lay.hline(3, 14, 9, 'B', 2.9)
        lay.rect(1, 15, 2, 2, 'R', 2.0)
        # the coat: a rounded mound, lit on top, a fold, darker below; collar and scarf at the neck
        rows = {10 - b: (13, 21), 11 - b: (11, 23)}
        for yy in range(12 - b, 17):
            rows[yy] = (10, 25)
        for yy, (xa, xb) in rows.items():
            t = 2.9 if yy <= 11 - b else (2.2 if yy < 15 else 1.5)
            lay.hline(xa, yy, xb - xa, 'B', t, hgt=0.6)
        lay.line(14, 13, 19, 16, 'B', 1.4)                                         # a fold
        lay.rect(10, 12, 3, 3, 'E', 2.4)                                           # the scarf
        lay.px(12, 15, 'E', 1.8)
        # knees drawn up, the shins on the lid, white socks, the shoes (one over the edge)
        lay.hline(24, 11 - b, 3, 'S', 2.8)
        lay.rect(23, 12 - b, 5, 3 + b, 'S', 2.2, hgt=0.5)
        lay.rect(26, 15, 5, 2, 'S', 2.0)
        lay.rect(30, 15, 2, 2, 'P', 5.6)
        lay.rect(31, 15 + twitch, 4, 2, 'I', 1.0)
        lay.px(34, 15 + twitch, 'I', 2.2)                                          # the toe catches the light
        # the wooden engine held to his chest: red body, black chimney and wheels
        lay.rect(16, 14, 5, 2, 'R', 2.6)
        lay.px(17, 13, 'I', 1.0)
        lay.px(17, 16, 'I', 0.8)
        lay.px(20, 16, 'I', 0.8)
        # the head: round, cheek on the arm, the closed eye, nose and mouth, hair at the back, the cap slipped back
        for yy, (xa, xb) in {9: (7, 10), 10: (6, 11), 11: (5, 11), 12: (5, 11), 13: (5, 11), 14: (6, 10)}.items():
            lay.hline(xa, yy, xb - xa, 'Y', 1.5, hgt=0.6)
        lay.px(8, 13, 'Y', 2.0)                                                    # the cheek
        lay.px(9, 13, 'Y', 1.9)
        lay.hline(8, 12, 2, 'I', 0.9)                                              # the closed eye
        lay.px(11, 12, 'Y', 1.3)                                                   # the nose
        lay.px(10, 14, 'Y', 0.9)                                                   # the mouth, a little open
        lay.vline(5, 11, 3, 'D', 1.3)                                              # hair at the back
        lay.px(6, 10, 'D', 1.5)
        lay.rect(5, 8, 5, 2, 'R', 2.4, hgt=0.6)                                    # the knitted cap ...
        lay.hline(6, 10, 4, 'R', 1.6)                                              # ... its ribbed band
        lay.px(4, 9, 'R', 2.0)
        lay.rect(2, 8, 2, 2, 'R', 3.0)                                             # ... the bobble
        # the bulbs above light his top edges
        m = lay.rid >= 0
        top = m & ~np.roll(m, 1, axis=0)
        top[17:, :] = False
        for (yy, xx) in zip(*np.nonzero(top)):
            lay.tone[yy, xx] += 0.6
    c, e = LF.life_strip(st.lay.c, st.lay.em, box, 12, draw, 'A', fields=st.F, transparent=True)
    return c, e, box, 12, 3


def kiosk_woman(st):
    wx, wy, ww, wh = st.kiosk_win
    box = (wx, wy, ww, wh)

    def draw(lay, k):
        look = 12 <= k <= 15
        arm = 'out' if (k // 4) % 2 == 0 and not look else 'table'
        LF.person(lay, 17 + (1 if (k // 4) % 2 else 0), wh - 2, k=k, s=0.95, coat=('R', 1.6), skin=('Y', 1.6),
                  hair=('P', 4.4), hat=('E', 2.2, 'scarf'), face=1 if look else -1, arm=arm, rim=('L', 3.4),
                  collar=('P', 3.0))
        if arm == 'out':
            lay.rect(5 + (k % 2), wh - 10, 6, 3, 'P', 6.2)                         # a paper being folded
    c, e = LF.life_strip(st.lay.c, st.lay.em, box, 16, draw, 'A', clip=_own(st, 'kiosk', box))
    return c, e, box, 16, 4


def loco_crew(st):
    """The engine driver in the cab window: he leans on the sill and looks back along the platform, glances at the
    clock, then turns to the fire; behind him the firebox glow flickers.  Clipped to the window opening (the plates
    under it and the kiosk in front stay untouched)."""
    wx, wy, ww, wh = st.cab_window
    box = (wx, wy, ww, wh)

    def draw(lay, k):
        f = (0.0, 0.3, -0.2, 0.4, 0.1, -0.3, 0.2, 0.0)[k % 8]
        lay.vgrad(0, 0, ww, wh, 'L', 2.0 + f, 1.3 + f * 0.5, emis=True)        # the cab lit by the fire
        lay.rect(0, wh - 4, ww, 4, 'L', 2.6 + f, emis=True)
        lay.rect(ww - 5, 3, 3, wh - 7, 'L', 3.4 + f, emis=True)                   # the open firedoor's glare
        lay.rect(ww - 8, 6, 2, 4, 'S', 2.4, emis=True)                            # gauge glasses
        if k < 12:                                                                 # leaning on the sill
            face = -1 if (k < 6 or k >= 9) else 1
            LF.person(lay, 7, wh + 1, k=k, s=0.85, coat=('B', 1.6), skin=('Y', 1.6), hair=('I', 1.0),
                      hat=('I', 1.4, 'cap'), face=face, arm='table', rim=('L', 4.2), collar=('P', 4.6))
        else:                                                                      # turned to the fire
            LF.person(lay, 11, wh + 2, k=k, s=0.85, coat=('B', 1.4), skin=('Y', 1.2), hair=('I', 1.0),
                      hat=('I', 1.2, 'cap'), face=1, arm='out', rim=('L', 4.6))
    c, e = LF.life_strip(st.lay.c, st.lay.em, box, 16, draw, 'A', emissive_fig=True, clip=_own(st, 'loco', box))
    return c, e, box, 16, 4


def diners(st):
    wins = st.diner_windows                                          # [(x, y, w, h)]
    x0 = wins[0][0] - 2
    x1 = wins[-1][0] + wins[-1][2] + 2
    y0, y1 = wins[0][1] - 2, wins[0][1] + wins[0][3] + 2
    box = (x0, y0, x1 - x0, y1 - y0)
    inner = [(wx + 3, wy, ww - 6, wh - 9) for (wx, wy, ww, wh) in wins]           # between the curtains, above the cloth
    clip = _clip_rects(box[2], box[3], inner, x0, y0)
    N = 48

    def draw(lay, k):
        oy = wins[0][1] - y0
        ty = oy + wins[0][3] - 9                                                   # table top (cloth) in box coords
        def wxc(i, frac):
            wx, wy, ww, wh = wins[i]
            return int(wx - x0 + ww * frac)
        # W0: a couple; he lifts his wine glass (k 20..27)
        LF.person(lay, wxc(0, 0.3), ty, k=k, s=0.8, coat=('S', 2.2), skin=('Y', 1.6), hair=('I', 1.4), face=1,
                  arm='up' if 20 <= k <= 27 else 'table', rim=('L', 4.2), collar=('P', 6.0))
        LF.person(lay, wxc(0, 0.72), ty, k=k, s=0.78, coat=('R', 2.6), skin=('Y', 1.8), hair=('D', 2.0),
                  hat=('D', 2.0, 'bun'), face=-1, arm='table', rim=('L', 4.4))
        # W1: a man behind his newspaper, turning a page (k 30..33)
        LF.person(lay, wxc(1, 0.4), ty, k=k, s=0.8, coat=('D', 2.0), skin=('Y', 1.4), hair=('V', 2.4), face=1,
                  arm='table', rim=('L', 4.0))
        px_ = wxc(1, 0.55)
        lay.rect(px_, ty - 10, 6, 7, 'P', 6.4 if not 30 <= k <= 33 else 5.4)
        K.pseudo_text(lay, px_ + 1, ty - 9, 4, 3, 'I', 2.0, seed=k // 8, gap=2)
        # W2: Ekdahl's table -- he is out on the platform: his hat, a cup, the scarf over the chair
        lay.rect(wxc(2, 0.3) - 3, ty - 3, 7, 2, 'I', 1.4)
        lay.rect(wxc(2, 0.3) - 2, ty - 5, 5, 2, 'I', 1.8)
        lay.rect(wxc(2, 0.62), ty - 3, 2, 3, 'P', 6.4)
        lay.rect(wxc(2, 0.75), ty - 12, 2, 12, 'R', 2.4)
        # W3: two women talking, one gesturing
        LF.person(lay, wxc(3, 0.32), ty, k=k, s=0.78, coat=('E', 2.6), skin=('Y', 1.8), hair=('I', 1.6),
                  hat=('E', 2.0, 'hat'), face=1, arm='out' if (k // 6) % 2 else 'table', rim=('L', 4.2))
        LF.person(lay, wxc(3, 0.72), ty, k=k, s=0.78, coat=('B', 2.4), skin=('Y', 1.6), hair=('D', 1.4),
                  face=-1, arm='table', rim=('L', 4.2))
        # W4: an old man spooning soup
        LF.person(lay, wxc(4, 0.5), ty, k=k, s=0.82, coat=('S', 3.0), skin=('Y', 1.4), hair=('V', 4.0), face=-1,
                  arm='up' if (k // 3) % 3 == 1 else 'table', rim=('L', 4.0), bend=1)
        # the waiter in his white jacket walks the aisle right to left with a tray (k 0..47)
        wxp = int((x1 - x0) + 10 - (k / N) * (x1 - x0 + 20))
        LF.person(lay, wxp, ty + 4, k=k, s=0.86, coat=('P', 6.4), skin=('Y', 1.6), hair=('I', 1.0), face=-1,
                  arm='out', rim=('L', 4.6), collar=('I', 1.0))
        lay.hline(wxp - 9, ty - 7, 7, 'S', 4.6)                                    # the tray
        lay.rect(wxp - 7, ty - 10, 2, 3, 'P', 6.4)
    c, e = LF.life_strip(st.lay.c, st.lay.em, box, N, draw, 'A', clip=clip & _own(st, 'diner', box))
    return c, e, box, N, 6


def sleeper_passenger(st):
    x0 = L.SLEEPER[0] + 32
    box = (x0, 192 + 12, 18, 14)

    def draw(lay, k):
        lift = (k // 4) % 4
        arm = 'raise' if lift in (1, 2) else None
        LF.person(lay, 9, 14, k=k, s=0.8, coat=('P', 5.6), skin=('Y', 1.6), hair=('I', 1.8), face=1, arm=arm,
                  rim=('L', 4.4))
        if arm == 'raise':
            lay.rect(9, 0, 7, 3, 'D', 2.6)                                             # the case going up
    c, e = LF.life_strip(st.lay.c, st.lay.em, box, 16, draw, 'A', clip=_own(st, 'sleeper', box))
    return c, e, box, 16, 3


# =========================================================================== B: the courtyard
def _wins(yd, names):
    return [yd.windows[n] for n in names if n in yd.windows]


def _box_of(rects, pad=1):
    x0 = min(r[0] for r in rects) - pad
    y0 = min(r[1] for r in rects) - pad
    x1 = max(r[0] + r[2] for r in rects) + pad
    y1 = max(r[1] + r[3] for r in rects) + pad
    return (x0, y0, x1 - x0, y1 - y0)


def _inner(rects):
    """window interiors minus the frame bars (so the bars stay in front of the people)."""
    out = []
    for (x, y, w, h) in rects:
        out.append((x, y, w // 2, h // 3))
        out.append((x + w // 2 + 1, y, w - w // 2 - 1, h // 3))
        out.append((x, y + h // 3 + 1, w // 2, h - h // 3 - 1))
        out.append((x + w // 2 + 1, y + h // 3 + 1, w - w // 2 - 1, h - h // 3 - 1))
    return out


def window_strip(yd, names, frames, draw, fps):
    rects = _wins(yd, names)
    box = _box_of(rects)
    clip = _clip_rects(box[2], box[3], _inner(rects), box[0], box[1])
    c, e = LF.life_strip(yd.lay.c, yd.lay.em, box, frames, lambda lay, k: draw(lay, k, box, rects), 'B', clip=clip)
    return c, e, box, frames, fps


def schulz(yd):
    """v1: the Schulz mother walks the baby between her two windows."""
    def draw(lay, k, box, rects):
        a = rects[0][0] + rects[0][2] // 2 - box[0]
        b = rects[-1][0] + rects[-1][2] // 2 - box[0]
        t = (k % 32) / 32.0
        pos = a + (b - a) * (0.5 - 0.5 * math.cos(2 * math.pi * t))
        bob = 1 if (k // 2) % 2 else 0
        face = 1 if t < 0.5 else -1
        wy = rects[0][1] - box[1] + rects[0][3] + 2
        LF.person(lay, int(pos), wy + bob, k=k, s=1.0, coat=('R', 2.2), skin=('Y', 1.6), hair=('D', 2.2),
                  hat=('D', 2.2, 'bun'), face=face, rim=('L', 4.6))
        bx = int(pos) + (2 if face > 0 else -6)
        lay.rect(bx, wy - 15 + bob, 5, 6, 'Q', 2.6)                                   # the baby on her shoulder
        lay.rect(bx + 1, wy - 17 + bob, 3, 3, 'Y', 2.0)
    return window_strip(yd, ['v1_1024', 'v1_1078'], 32, draw, 4)


def lenz(yd):
    """v3: Lenz at his desk under the lamp, turning a page; the radio dial glows in the other window."""
    def draw(lay, k, box, rects):
        x, y, w, h = rects[0]
        ox, oy = x - box[0], y - box[1]
        lay.rect(ox + 1, oy + h - 7, w - 2, 2, 'D', 2.8)                              # the desk
        lay.rect(ox + 2, oy + h - 13, 4, 2, 'E', 2.2)                                 # green lamp shade
        lay.rect(ox + 3, oy + h - 11, 1, 4, 'L', 5.0, emis=True)
        rub = 18 <= k <= 20
        LF.person(lay, ox + w - 6, oy + h - 6, k=k, s=0.9, coat=('U', 2.6), skin=('Y', 1.8), hair=('D', 1.8),
                  face=-1, arm='up' if rub else 'table', rim=('L', 4.6), bend=0 if rub else 2)
        page = (k % 12) < 2
        lay.rect(ox + 6, oy + h - 9, 5, 2, 'P', 6.0 if not page else 5.0)             # the open book
        if page:
            lay.px(ox + 8, oy + h - 11, 'P', 6.0)
        if len(rects) > 1:                                                             # the radio dial
            x2, y2, w2, h2 = rects[1]
            ox2, oy2 = x2 - box[0], y2 - box[1]
            lay.rect(ox2 + 3, oy2 + h2 - 8, 8, 5, 'D', 2.0)
            g = 4.2 + (0.6 if (k // 3) % 3 == 0 else 0.0)
            lay.rect(ox2 + 4, oy2 + h2 - 7, 5, 2, 'L', g, emis=True)
            lay.px(ox2 + 9, oy2 + h2 - 7, 'E', 3.2 if (k // 2) % 2 else 2.4, emis=True)   # the magic eye
    rects = _wins(yd, ['v3_1078', 'v3_1132'])
    box = _box_of(rects)
    clip = _clip_rects(box[2], box[3], _inner(rects), box[0], box[1])
    c, e = LF.life_strip(yd.lay.c, yd.lay.em, box, 24, lambda lay, k: draw(lay, k, box, rects), 'B', clip=clip,
                         emissive_fig=True)
    return c, e, box, 24, 4


def mertens(yd):
    """s1: the tram conductor's family at supper; the mother serves, the child presses its nose to the glass."""
    def draw(lay, k, box, rects):
        cx = [r[0] + r[2] // 2 - box[0] for r in rects]
        wy = rects[0][1] - box[1] + rects[0][3] - 6
        # the father in shirt-sleeves (braces), seated at the middle window
        LF.person(lay, cx[1] + 2, wy, k=k, s=0.95, coat=('Q', 2.4), skin=('Y', 1.6), hair=('I', 1.4), face=-1,
                  arm='up' if (k // 4) % 3 == 1 else 'table', rim=('L', 4.6))
        lay.vline(cx[1] - 1, wy - 11, 11, 'R', 2.0)                                     # braces
        # the mother between the stove (left window) and the table
        t = (k % 32) / 32.0
        mx = int(cx[0] + (cx[1] - 6 - cx[0]) * (0.5 - 0.5 * math.cos(2 * math.pi * t)))
        LF.person(lay, mx, wy + 3, k=k, s=1.0, coat=('E', 2.4), skin=('Y', 1.8), hair=('D', 2.6), face=1 if t < 0.5 else -1,
                  arm='out', rim=('L', 4.6), apron=('Q', 2.8))
        # the child in the right window: on a chair, nose against the glass at k 20..27
        near = 20 <= k <= 27
        LF.person(lay, cx[2] - (0 if near else 3), wy - (4 if near else 0), k=k, s=0.7, coat=('R', 2.6),
                  skin=('Y', 2.0), hair=('P', 4.2), face=1 if near else -1, arm='table', rim=('L', 4.6))
        # the conductor's cap on its hook beside the window
        lay.rect(cx[2] + 3, wy - 16, 5, 2, 'B' if 'B' in lay.R.idx else 'U', 1.6)
        lay.px(cx[2] + 5, wy - 16, 'L', 4.0)
    return window_strip(yd, ['s1_1444', 's1_1496', 's1_1548'], 32, draw, 4)


def pohl(yd):
    """s2: Frau Pohl's curtain moves; a face, then the curtain again."""
    def draw(lay, k, box, rects):
        x, y, w, h = rects[0]
        ox, oy = x - box[0], y - box[1]
        if 20 <= k <= 23 or 32 <= k <= 35:                                             # the curtain edge moves
            lay.rect(ox + 1, oy + 2, 3, h - 4, 'L', 3.8)
        if 24 <= k <= 31:
            LF.person(lay, ox + 4, oy + h - 2, k=k, s=0.85, coat=('U', 1.6), skin=('Y', 1.4), hair=('Q', 2.8),
                      hat=('Q', 2.8, 'bun'), face=1, arm=None, rim=('L', 3.4))
            lay.rect(ox + 6, oy + 2, 3, h - 4, 'L', 3.4)                                # the lifted curtain
    return window_strip(yd, ['s2_1340'], 40, draw, 4)


def ilse(yd):
    """s3 (until c4h_solve_house): Ilse at Hanna's kitchen table, drawing houses with lit windows."""
    def draw(lay, k, box, rects):
        x, y, w, h = rects[0]
        ox, oy = x - box[0], y - box[1]
        lay.rect(ox + 1, oy + h - 7, w - 2, 2, 'D', 3.0)                               # the table
        lay.rect(ox + 3, oy + h - 9, 5, 2, 'P', 6.0)                                   # the paper
        lay.px(ox + 4, oy + h - 10, 'L', 2.6)
        bob = 1 if (k // 3) % 2 else 0
        LF.person(lay, ox + w - 6, oy + h - 6, k=k, s=0.72, coat=('R', 2.8), skin=('Y', 2.0), hair=('L', 2.2),
                  face=-1, arm='write', rim=('L', 4.6), bend=2 + bob)
        lay.rect(ox + w - 3, oy + h - 11, 3, 4, 'D', 2.2)                              # her satchel on the chair
        lay.px(ox + w - 2, oy + h - 12, 'D', 3.0)
    return window_strip(yd, ['s3_1340'], 16, draw, 4)


def hanna_window(yd):
    """s3 (after c4h_solve_house): Hanna back at her kitchen window with her light on, seen from the front behind
    the left lower pane -- the grey cardigan, the rust scarf, her hair in a bun lit from the lamp behind her; she
    holds the curtain aside and looks down into the courtyard, now and then up at the windows across."""
    def draw(lay, k, box, rects):
        x, y, w, h = rects[0]
        ox, oy = x - box[0], y - box[1]
        lay.rect(ox, oy + h - 3, w, 3, 'D', 3.0)                                   # the table's edge behind her
        down = (k // 6) % 3 != 2
        LF.person_front(lay, ox + 3, oy + h - 1, k=k, coat=('U', 2.0), skin=('Y', 1.1), hair=('D', 1.3),
                        scarf=('R', 1.8), rim=('L', 4.6), look_down=down, hand='curtain')
        lay.rect(ox, oy + h // 3 + 1, 1, h - h // 3 - 2, 'P', 4.2)                 # the curtain she holds
    return window_strip(yd, ['s3_1340'], 18, draw, 3)


def kuhnert_lodge(yd):
    """se: Frau Kuhnert knitting by the radio, now and then looking out at the courtyard."""
    x, y, w, h = yd.windows['se_lodge']
    box = (x, y, w, h)
    clip = _clip_rects(w, h, [(x + 3, y + 1, w - 6, h - 2)], x, y)

    def draw(lay, k):
        look = 16 <= k <= 19
        LF.person(lay, 16, h - 2, k=k, s=1.05, coat=('R', 1.8), skin=('Y', 1.6), hair=('Q', 2.6),
                  hat=('Q', 2.4, 'bun'), face=-1 if look else 1, arm='table', rim=('L', 4.6))
        if not look:
            lay.px(23 + (k % 2), h - 6, 'P', 5.4)                                       # needles
            lay.px(25 - (k % 2), h - 7, 'P', 5.4)
            lay.rect(22, h - 5, 4, 3, 'R', 2.6)                                         # the knitting
    c, e = LF.life_strip(yd.lay.c, yd.lay.em, box, 24, draw, 'B', clip=clip)
    return c, e, box, 24, 4


def kuehn(yd):
    """h1: the Kühns' card game."""
    def draw(lay, k, box, rects):
        cx = [r[0] + r[2] // 2 - box[0] for r in rects]
        wy = rects[0][1] - box[1] + rects[0][3] - 6
        slap = 6 <= k <= 8
        LF.person(lay, cx[0] - 1, wy, k=k, s=0.95, coat=('D', 2.6), skin=('Y', 1.6), hair=('Y', 1.8), face=1,
                  arm='out' if slap else 'table', rim=('L', 4.6))
        think = 14 <= k <= 19
        LF.person(lay, cx[1] + 1, wy, k=k, s=0.92, coat=('E', 2.2), skin=('Y', 1.8), hair=('Q', 2.6),
                  hat=('Q', 2.4, 'bun'), face=-1, arm='up' if think else ('out' if 20 <= k <= 22 else 'table'),
                  rim=('L', 4.6))
        for i in range(3):                                                              # her hand of cards
            lay.px(cx[1] - 5 - i, wy - 7 + (i % 2), 'P', 6.0)
        if slap:
            lay.rect(cx[0] + 6, wy - 4, 3, 2, 'P', 6.4)
    return window_strip(yd, ['h1_1764', 'h1_1816'], 24, draw, 4)


def _rim_left(lay, ramp, tone, x0, x1):
    """The light from the left (the car's headlights in the doorway): each figure row's first pixel lights up."""
    for yy in range(lay.h):
        row = np.nonzero(lay.rid[yy, x0:x1] >= 0)[0]
        if row.size:
            lay.px(x0 + int(row[0]), yy, ramp, tone)


def sweep_men(yd):
    """After the puzzle: two of the sweep's men in the doorway, against the car's headlights -- one leans on the wall
    and smokes, one looks up at the windows; both rim-lit from the street (a transparent strip on the passage,
    above the headlights patch; their long shadows are painted on the setts)."""
    a = K.Fig(coat=('I', 1.6), skin=('Y', 1.2), hair=('I', 1.0), hat=('I', 1.8, 'hat'), legs=('I', 1.2), h=46, face=1)
    b = K.Fig(coat=('W', 2.0), skin=('Y', 1.4), hair=('I', 1.2), hat=('W', 2.2, 'hat'), legs=('I', 1.4), h=47,
              face=1, collar=('I', 1.4))
    x0 = 26
    box = (x0, 244, 44, 54)

    def draw(lay, k):
        a.stand(lay, 9, 52, pose=0, arm='up' if (k // 4) % 4 == 1 else None)
        _rim_left(lay, 'SN', 4.0, 0, 20)
        if (k // 4) % 4 == 1:
            lay.px(15, 52 - 46 + 8, 'L', 5.0, emis=True)                                 # the cigarette's glow
        else:
            lay.px(14, 52 - 46 + 18, 'L', 3.6, emis=True)
        b.stand(lay, 30, 53, pose=0)
        b.head(lay, 30, 53 - 47, look=-1 if (k // 8) % 2 else 1)
        _rim_left(lay, 'SN', 3.6, 21, 44)
    c, e = LF.life_strip(yd.lay.c, yd.lay.em, box, 16, draw, 'B', fields=yd.F, transparent=True, emissive_fig=True)
    return c, e, box, 16, 4


def _puff(lay, x, y, k0, k, drift=-1):
    """A breath puff in the cold: two frames, a light pixel pair that rises and thins."""
    if k == k0:
        lay.px(x, y, 'SN', 4.2)
        lay.px(x + drift, y, 'SN', 3.6)
    elif k == k0 + 1:
        lay.px(x + drift, y - 1, 'SN', 3.6)
        lay.px(x + 2 * drift, y - 2, 'SN', 3.0)


def _scuttle(lay, cx, top, carried):
    """A tapered zinc coal scuttle, heaped with briquettes, its top rim at `top`; `carried` adds the bail."""
    for i, yy in enumerate(range(top, top + 9)):
        w = 8 - i // 4
        x0 = cx - w // 2
        for j in range(w):
            t = 2.4 - 0.9 * (j + 0.5) / w + (0.5 if i == 0 else 0.0)
            lay.px(x0 + j, yy, 'I', t, hgt=0.6)
    lay.hline(cx - 4, top, 8, 'W', 2.6)                                                  # the rolled zinc rim
    lay.px(cx - 3, top + 3, 'W', 2.2)                                                    # a dull highlight
    for j, t in enumerate((1.2, 1.8, 1.0, 1.6, 1.3, 1.9)):                               # briquettes heaped
        lay.px(cx - 3 + j, top - 1, 'D', t)
    lay.px(cx - 1, top - 2, 'D', 1.5)
    lay.px(cx, top - 2, 'D', 1.1)
    lay.px(cx - 2, top - 1, 'U', 3.0)                                                    # a glint of the lamp
    if carried:
        lay.line(cx - 4, top - 1, cx, top - 4, 'I', 2.8)                                 # the wire bail
        lay.line(cx, top - 4, cx + 3, top - 1, 'I', 2.8)


def coal_neighbour(yd):
    """An old neighbour up from the cellar with a full coal scuttle for the night's stove, between the open hatch and
    the lodge: he sets the scuttle down by the hatch, blows into his cold hand, glances across at the lodge window
    (the Blockleiter's evening) and takes it up again.  A transparent strip on the courtyard floor, until the house
    is solved (at 23.30 everyone is inside)."""
    man = K.Fig(coat=('D', 1.5), skin=('Y', 1.2), hair=('W', 4.2), hat=('I', 1.6, 'cap'), legs=('I', 1.4),
                scarf=('W', 2.4), h=45, face=-1)
    hx = 16
    box = (L.COAL_MAN - L.SEAM_B - hx, 244, 28, 54)                                   # layer coords

    def draw(lay, k):
        down = 6 <= k <= 11
        man.stand(lay, hx, 52, pose=0, arm='up' if 6 <= k <= 8 else None)
        head_y = 52 - man.h
        if 9 <= k <= 11:
            man.head(lay, hx, head_y, look=1)                                             # a glance at the lodge
        ax = hx - 9 // 2                                                                  # the near hand (face left)
        if down:
            _scuttle(lay, hx - 10, 44, False)                                             # set down by the hatch
        else:
            _scuttle(lay, ax, 39, True)                                                   # hanging from his hand
        _puff(lay, hx - 5, head_y + 5, 7, k)
        _puff(lay, hx - 5, head_y + 5, 13, k)

    c, e = LF.life_strip(yd.lay.c, yd.lay.em, box, 16, draw, 'B', fields=yd.F, transparent=True)
    return c, e, box, 16, 4


def wash_basket(yd):
    """Tuesday is washing day (the house cards: „Dachboden: Waschtag Di: offen“): a woman out of the wash-house with
    the last basket of wet washing for the side wing's attic, her coat over the apron; she hitches the basket up,
    looks back over her shoulder at the lodge and goes on standing in the cold.  Transparent, until the house is
    solved."""
    woman = K.Fig(coat=('U', 2.3), skin=('Y', 1.4), hair=('D', 2.2), hat=('R', 1.9, 'scarf'), legs=('I', 1.5),
                  apron=('Q', 0.9), h=43, face=-1)
    hx = 18
    box = (L.WASH_WOMAN - L.SEAM_B - hx, 246, 26, 52)                                 # layer coords

    def draw(lay, k):
        woman.stand(lay, hx, 50, pose=0, arm='out')
        head_y = 50 - woman.h
        if 8 <= k <= 11:
            woman.head(lay, hx, head_y, look=1)                                           # back at the lodge
        lift = 1 if k in (6, 7) else 0                                                    # hitches it up
        bx, by = hx - 16, head_y + 16 - lift                                              # the wicker basket
        for j in range(11):
            for i in range(5):
                t = 2.2 + (0.5 if (i + j) % 2 else 0.0) - 0.6 * j / 10.0
                lay.px(bx + j, by + i, 'D', t, hgt=0.6)
        lay.hline(bx, by, 11, 'D', 3.2)                                                   # the rim
        lay.hline(bx + 1, by + 5, 9, 'D', 1.4)                                            # the foot
        for j, dy in enumerate((1, 2, 2, 3, 2, 2, 3, 2, 1)):                              # wet washing, heaped
            for i in range(dy):
                lay.px(bx + 1 + j, by - 1 - i, 'Q', 2.8 - 0.3 * i + (0.3 if j % 3 == 0 else 0.0))
        lay.vline(bx - 1, by + 1, 4, 'Q', 2.2)                                            # a sleeve over the edge
        lay.px(bx - 1, by + 5, 'Q', 1.8)
        _puff(lay, hx - 5, head_y + 5, 13, k)

    c, e = LF.life_strip(yd.lay.c, yd.lay.em, box, 16, draw, 'B', fields=yd.F, transparent=True)
    return c, e, box, 16, 4


def candle(yd_after):
    """The candle in the cobbler's souterrain after the puzzle: the flame flickers, its glow breathes on the shoes,
    and Ilse sits by it at the bench -- her face lit from the flame, her hair gold at the edge; she looks into the
    flame, then up at the window.  The window's middle bar stays in front."""
    x, y, w, h = yd_after.windows['ws_1']
    box = (x, y, w, h)
    fx, fy = yd_after.candle_xy[0] - x, yd_after.candle_xy[1] - y
    clip = np.ones((h, w), bool)
    clip[:, w // 2] = False

    def draw(lay, k):
        fl = (0.0, 0.5, -0.3, 0.2, 0.6, -0.1, 0.3, -0.4)[k % 8]
        for (dx, dy, t) in ((-2, 0, 3.0), (2, 0, 3.0), (0, -2, 3.2), (-1, -1, 3.6), (1, -1, 3.6), (-1, 1, 3.4),
                            (1, 1, 3.4), (-3, 1, 2.6), (3, 1, 2.6)):
            lay.px(fx + dx, fy + dy, 'L', t + fl * 0.6, emis=True)                    # the glow around the flame
        lay.px(fx, fy - 1 - (k % 2), 'L', 5.4 + fl * 0.2, emis=True)                  # the flame
        lay.px(fx, fy, 'L', 4.8 + fl, emis=True)
        lay.rect(fx, fy + 1, 1, 3, 'P', 5.0, emis=True)                               # the candle
        up = (k // 4) % 2 == 1
        LF.person(lay, w // 2 - 6, h - 3, k=k, s=0.85, coat=('R', 2.4), skin=('Y', 1.8 + fl * 0.3),
                  hair=('L', 3.2), face=1, arm='table', rim=('L', 4.8), bend=0 if up else 2)
    c, e = LF.life_strip(yd_after.lay.c, yd_after.lay.em, box, 8, draw, 'B', emissive_fig=True, clip=clip)
    return c, e, box, 8, 6
