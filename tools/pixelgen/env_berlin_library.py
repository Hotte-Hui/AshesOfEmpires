"""env_berlin_library -- the reading room & library of the Bauarchiv floor (round 2).

Five tall oak bookcases with brass section labels (I VERWALTUNG .. V ARBEITSEINSATZ -- each section holds the
in-world literature next to which the real-history cards are found), two tall windows (the first with the
knocking radiator, the second with a tilted fanlight above the reading table), a framed wall map over the
librarian's desk, a pneumatic tube dropping to the desk, signs, pendant lamps and a brass rail for the rolling
ladder.  The hidden compartment is the right cupboard door of section V: not flush, its knob polished by use,
and a clean quarter-arc swept into the dust of the floor in front of it.

paint_library(room) paints into the room MLayer; props_library(Prop) returns the free-standing furniture.
"""
from __future__ import annotations

import math
import zlib

import numpy as np

import env_berlin_kit as kit
import env_berlin_layout as L

R = kit.archive_ramps()


def _rng(name):
    return np.random.default_rng(zlib.crc32(name.encode()) % 100000)


# =========================================================================== books
BINDINGS = {
    # style -> list of (ramp, tone) bindings, weighted by repetition
    'gazette': [('B', 2.0), ('B', 2.4), ('W', 3.4), ('B', 2.0), ('W', 3.0), ('B', 1.6)],
    'rail': [('D', 2.6), ('D', 3.0), ('R', 1.0), ('D', 2.2), ('D', 3.4), ('I', 1.4)],
    'atlas': [('G', 2.4), ('D', 3.0), ('P', 2.4), ('G', 3.0), ('W', 3.0), ('D', 2.2)],
    'journal': [('P', 2.6), ('P', 3.2), ('W', 4.0), ('B', 3.0), ('P', 2.0), ('G', 2.0)],
    'binder': [('W', 4.4), ('W', 3.6), ('B', 2.6), ('D', 2.4), ('W', 4.0), ('K', 2.6)],
    'mixed': [('D', 2.6), ('B', 2.2), ('W', 3.4), ('D', 3.4), ('G', 2.4), ('R', 1.0), ('P', 2.6), ('D', 2.0)],
}


def books_row(lay, x0, x1, base, hmax, rng, style, gilt=True, gaps=0.05):
    """Fill one shelf (x0..x1, books standing on y=base) with spines up to hmax tall."""
    pal = BINDINGS[style]
    x = x0
    run_left = 0
    cur = None
    while x < x1 - 1:
        r = rng.random()
        if r < gaps and x < x1 - 8:                                    # a gap (book on loan)
            x += int(rng.integers(2, 6))
            continue
        if r < gaps + 0.05 and x < x1 - 10:                            # a small stack lying flat
            sw = int(rng.integers(7, 11))
            yy = base
            for k in range(int(rng.integers(2, 4))):
                rm, t = pal[int(rng.integers(0, len(pal)))]
                th = int(rng.integers(2, 4))
                lay.rect(x, yy - th, sw - (k % 2), th, rm, t, hgt=0.5, flat=True)
                lay.rect(x, yy - th, sw - (k % 2), 1, rm, t + 0.8, hgt=0.55, flat=True)
                yy -= th
            x += sw + 1
            continue
        if run_left <= 0:                                              # series: same binding for a run
            cur = pal[int(rng.integers(0, len(pal)))]
            run_left = int(rng.integers(1, 6)) if style in ('gazette', 'rail', 'binder') else int(rng.integers(1, 3))
        run_left -= 1
        rm, t = cur
        if style == 'binder':
            sw = 4
            sh = hmax - int(rng.integers(0, 2))
        else:
            sw = int(rng.choice([2, 2, 3, 3, 3, 4]))
            sh = hmax - int(rng.integers(0, 7))
        sw = min(sw, x1 - x)
        if sw < 2:
            break
        lean = rng.random() < 0.04 and x > x0 + 6
        if lean:
            for k in range(sh - 1):
                lay.rect(x + k // 4, base - 1 - k, sw, 1, rm, t, hgt=0.4, flat=True)
            x += sw + 3
            continue
        lay.rect(x, base - sh, sw, sh, rm, t, hgt=0.5, flat=True)
        lay.rect(x, base - sh, 1, sh, rm, t + 0.9, hgt=0.55, flat=True)            # lit left edge
        if sw >= 3:
            lay.rect(x + sw - 1, base - sh, 1, sh, rm, t - 0.8, hgt=0.45, flat=True)
        if style == 'binder':
            lay.rect(x + 1, base - sh + 3, 2, 4, 'P', 5.4, hgt=0.6, flat=True)        # label
            lay.px(x + 1, base - 6, 'I', 1.0)                                        # finger hole
            lay.px(x + 2, base - 6, 'I', 1.0)
        elif gilt and rm in ('D', 'R', 'G', 'B') and sw >= 2:
            lay.rect(x, base - sh + 2, sw, 1, 'A', 2.6, hgt=0.55, flat=True)       # gilt bands
            if sh > 12:
                lay.rect(x, base - 4, sw, 1, 'A', 2.2, hgt=0.55, flat=True)
            if rng.random() < 0.35:
                lay.px(x + sw // 2, base - sh + 5, 'P', 5.0)                       # spine label
        elif style == 'gazette':
            lay.rect(x, base - sh + 3, sw, 2, 'P', 4.6, hgt=0.55, flat=True)       # year label
        elif style == 'journal' and rng.random() < 0.5:
            lay.rect(x, base - sh + 2, sw, 1, 'I', 2.0, hgt=0.5, flat=True)
        x += sw


def bookcase(room, x0, x1, label, style, seed_name, hidden_door=False):
    lay = room.lay
    rng = _rng(seed_name)
    top = L.LIB_SHELF_TOP
    lab_y = L.LIB_LABEL_Y
    w = x1 - x0
    # carcass + crown cornice
    lay.rect(x0, top, w, L.FLOOR - top, 'D', 1.4, hgt=0.3, flat=True)
    lay.rect(x0 - 2, top - 6, w + 4, 6, 'D', 3.0, hgt=0.75, flat=True)
    lay.rect(x0 - 2, top - 6, w + 4, 1, 'D', 4.8, hgt=0.8, flat=True)
    lay.rect(x0 - 1, top - 2, w + 2, 1, 'D', 1.6, hgt=0.6, flat=True)
    for k in range(x0, x1, 4):
        lay.rect(k, top - 4, 2, 1, 'D', 4.2, hgt=0.78, flat=True)                 # dentils
    # upper tier: 3 shelves
    tiers = [(top + 2, lab_y - 2, 3), (lab_y + 11, 262, 4)]
    for (ty0, ty1, n) in tiers:
        sh = (ty1 - ty0) // n
        for r in range(n):
            yb = ty0 + (r + 1) * sh - 2
            lay.rect(x0 + 3, ty0 + r * sh, w - 6, sh - 2, 'D', 0.7, hgt=-0.4, flat=True)   # shelf void (dark)
            lay.rect(x0 + 3, ty0 + r * sh, w - 6, 1, 'D', 0.3, hgt=-0.45, flat=True)
            books_row(lay, x0 + 4, x1 - 4, yb, sh - 4, rng, style)
            lay.rect(x0 + 2, yb, w - 4, 2, 'D', 3.4, hgt=0.5, flat=True)            # shelf board
            lay.rect(x0 + 2, yb, w - 4, 1, 'D', 4.6, hgt=0.55, flat=True)
    # label band with the brass plate
    lay.rect(x0, lab_y - 2, w, 13, 'D', 2.6, hgt=0.6, flat=True)
    lay.rect(x0, lab_y - 2, w, 1, 'D', 4.2, hgt=0.65, flat=True)
    lay.rect(x0, lab_y + 10, w, 1, 'D', 1.2, hgt=0.5, flat=True)
    m = kit.text_mask(label, '35')
    pw = m.shape[1] + 6
    px_ = x0 + (w - pw) // 2
    lay.rect(px_, lab_y, pw, 9, 'A', 3.4, hgt=0.75, flat=True)
    lay.rect(px_, lab_y, pw, 1, 'A', 5.0, hgt=0.8, flat=True)
    lay.rect(px_, lab_y + 8, pw, 1, 'A', 2.0, hgt=0.7, flat=True)
    lay.put(m, px_ + 3, lab_y + 2, 'D', 0.6, flat=True)
    lay.px(px_ + 1, lab_y + 4, 'A', 5.4); lay.px(px_ + pw - 2, lab_y + 4, 'A', 5.4)  # screws
    # base cupboard with two doors
    cy0, cy1 = 262, L.FLOOR - 5
    lay.rect(x0 + 2, cy0, w - 4, cy1 - cy0, 'D', 2.4, hgt=0.45, flat=True)
    half = (w - 4) // 2
    for k in range(2):
        dx = x0 + 3 + k * half
        dw = half - 2
        lay.rect(dx, cy0 + 2, dw, cy1 - cy0 - 4, 'D', 2.8, hgt=0.5, flat=True)
        lay.rect(dx + 2, cy0 + 4, dw - 4, cy1 - cy0 - 8, 'D', 2.2, hgt=0.42, flat=True)
        lay.rect(dx + 2, cy0 + 4, dw - 4, 1, 'D', 1.4, hgt=0.4, flat=True)
        lay.rect(dx + 2, cy1 - 5, dw - 4, 1, 'D', 3.4, hgt=0.45, flat=True)
        kx = dx + (dw - 2 if k == 0 else 1)
        lay.px(kx, (cy0 + cy1) // 2, 'A', 3.6, hgt=0.7)
        if hidden_door and k == 1:
            # the door is not flush: a dark sliver along its hinge-free edge and a lit door edge,
            # and its knob is polished bright by use
            lay.rect(dx - 1, cy0 + 2, 1, cy1 - cy0 - 4, 'N', 0.0, hgt=0.2, flat=True)
            lay.rect(dx, cy0 + 2, 1, cy1 - cy0 - 4, 'D', 4.4, hgt=0.6, flat=True)
            lay.px(kx, (cy0 + cy1) // 2, 'A', 6.0, hgt=0.75)
            lay.px(kx, (cy0 + cy1) // 2 - 1, 'A', 5.0, hgt=0.72)
            room.hidden_floor_arc = (dx + dw, L.FLOOR, dw - 2)
    lay.rect(x0, L.FLOOR - 5, w, 5, 'D', 1.2, hgt=0.3, flat=True)                  # plinth
    lay.rect(x0, L.FLOOR - 5, w, 1, 'D', 2.8, hgt=0.35, flat=True)
    # side stiles
    lay.rect(x0, top, 3, L.FLOOR - top, 'D', 2.6, hgt=0.55, flat=True)
    lay.rect(x0, top, 1, L.FLOOR - top, 'D', 3.8, hgt=0.58, flat=True)
    lay.rect(x1 - 3, top, 3, L.FLOOR - top, 'D', 1.6, hgt=0.55, flat=True)
    lay.rect(x1, top - 4, 1, L.FLOOR - top + 4, 'W', 1.6, hgt=0.0, flat=True)       # cast shadow on the wall
    # brass ladder rail across the upper tier
    lay.rect(x0 - 1, L.LIB_RAIL_Y, w + 2, 1, 'A', 3.6, hgt=0.85, flat=True)
    lay.rect(x0 - 1, L.LIB_RAIL_Y + 1, w + 2, 1, 'A', 1.6, hgt=0.7, flat=True)
    for k in (x0 + 4, x1 - 5):
        lay.rect(k, L.LIB_RAIL_Y - 1, 2, 3, 'A', 2.6, hgt=0.8, flat=True)            # rail brackets


SHELF_STYLES = ['gazette', 'rail', 'atlas', 'journal', 'binder']


def paint_library(room):
    lay = room.lay
    x0, x1 = L.LIBRARY
    room.dado(x0 + 4, x1 - 4, top=246)
    # pilasters framing the window bays and the desk wall
    for (px0, px1) in ((708, 716), (780, 788), (842, 850), (972, 980), (1060, 1066), (1132, 1139)):
        room.pilaster(px0, px1, room.frieze_bottom + 8, cap=True, face=4.6)
    # bookcases with section labels
    for i, ((bx0, bx1), label) in enumerate(zip(L.LIB_SHELVES, L.LIB_LABELS)):
        bookcase(room, bx0, bx1, label, SHELF_STYLES[i], 'libshelf%d' % i, hidden_door=(i == 4))
    # windows (taller than the office ones); the second one has its fanlight tilted open
    for i, (wx0, wx1) in enumerate(L.LIB_WINDOWS):
        room.window(wx0, wx1, 20 + i, blind=0, sill_item=None, wy=L.LIB_WIN_Y, fanlight_open=(i == 1))
    # wall map over the librarian's desk
    wall_map(room)
    # 'AUSKUNFT' sign hanging from the gallery of the desk wall + the pneumatic tube down to the desk
    sx = (L.LIB_DESK[0] + L.LIB_DESK[1]) // 2
    m = kit.text_mask('AUSKUNFT', '35')
    sw = m.shape[1] + 8
    lay.rect(sx - sw // 2 + 3, 148, 1, 14, 'K', 2.4, flat=True)
    lay.rect(sx + sw // 2 - 4, 148, 1, 14, 'K', 2.4, flat=True)
    lay.rect(sx - sw // 2, 162, sw, 10, 'W', 1.4, hgt=0.55, flat=True)
    lay.rect(sx - sw // 2, 162, sw, 1, 'W', 3.6, hgt=0.6, flat=True)
    lay.put(m, sx - sw // 2 + 4, 164, 'P', 5.0, flat=True)
    tube_x = L.LIB_DESK[1] - 7
    lay.rect(tube_x, room.frieze_bottom, 3, 262 - room.frieze_bottom, 'A', 2.6, hgt=0.7, flat=True)
    lay.rect(tube_x, room.frieze_bottom, 1, 262 - room.frieze_bottom, 'A', 4.2, hgt=0.72, flat=True)
    lay.rect(tube_x + 2, room.frieze_bottom, 1, 262 - room.frieze_bottom, 'A', 1.4, hgt=0.6, flat=True)
    for yy in range(room.frieze_bottom + 10, 262, 26):
        lay.rect(tube_x - 1, yy, 5, 2, 'A', 3.4, hgt=0.75, flat=True)                # clamps
    # (the horizontal run along the frieze is painted by Room.tube_network after all rooms)
    # reading-room rules + 'RUHE' enamel sign near the globe
    lay.rect(950, 168, 18, 10, 'P', 5.6, hgt=0.5, flat=True)
    lay.rect(950, 168, 18, 1, 'P', 6.4, hgt=0.55, flat=True)
    mr = kit.text_mask('RUHE', '35')
    lay.put(mr, 951 + (16 - mr.shape[1]) // 2, 171, 'I', 1.0, flat=True)
    lay.rect(968, 169, 1, 10, 'W', 2.2, flat=True)
    room.framed_notice(952, 186, 14, 20, seed=711, emblem=False)
    # wall sconce between the bookcases and the window (warm)
    room.sconce(846, 214)
    room.lights[-1]['name'] = 'lib_sconce'
    # pendant lamps (opal globes) over the reading area
    import env_berlin_hall as EH
    for i, lx in enumerate(L.LIB_LAMPS):
        EH.pendant_globe(room, lx, room.frieze_bottom - 4, 44 + (i % 2) * 8, name='lib_pendant_%d' % (i + 1),
                         energy=0.75)
    # framed engraving above the card catalogue (the old library building)
    ex, ey = 796, 176
    lay.rect(ex - 2, ey - 2, 40, 30, 'D', 2.2, hgt=0.55, flat=True)
    lay.rect(ex - 2, ey - 2, 40, 1, 'D', 3.8, hgt=0.6, flat=True)
    lay.rect(ex, ey, 36, 26, 'P', 4.8, hgt=0.25, flat=True)
    for k in range(4):                                                           # facade with columns
        lay.rect(ex + 6 + k * 7, ey + 9, 2, 12, 'P', 2.6, flat=True)
    lay.poly([(ex + 4, ey + 9), (ex + 32, ey + 9), (ex + 18, ey + 3)], 'P', 3.2)
    lay.rect(ex + 4, ey + 21, 28, 2, 'P', 3.0, flat=True)
    lay.rect(ex + 2, ey + 23, 32, 1, 'P', 3.6, flat=True)
    lay.rect(ex + 38, ey - 1, 1, 30, 'W', 2.2, flat=True)


def wall_map(room):
    """Framed wall map 'Grossdeutsches Reich 1964' (fictional world): land, sea, rivers, the armistice line."""
    lay = room.lay
    x, y, w, h = L.LIB_MAP
    lay.rect(x - 3, y - 3, w + 6, h + 6, 'D', 2.0, hgt=0.6, flat=True)
    lay.rect(x - 3, y - 3, w + 6, 1, 'D', 3.8, hgt=0.65, flat=True)
    lay.rect(x - 1, y - 1, w + 2, h + 2, 'A', 2.6, hgt=0.55, flat=True)            # gilt inner frame
    # sea (top-left: North Sea / Baltic) and land
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    coast = 14 + 7 * np.sin(xx / 9.0) + 4 * np.sin(xx / 3.7 + 1.3)
    sea = yy < coast - (xx / w) * 6
    sea |= (xx > w * 0.55) & (yy < 9 + 3 * np.sin(xx / 4.0))
    land_t = 4.2 + (kit.pg.value_noise(w, h, 9, 77, octaves=2) - 0.5) * 0.8
    lay.put(~sea, x, y, 'P', land_t, hgt=0.2)
    lay.put(sea, x, y, 'B', 3.4, hgt=0.2, flat=True)
    # coast line
    edge = kit.edge_of(~sea)
    lay.put(edge, x, y, 'B', 2.4, flat=True)
    # rivers (blue lines running north)
    for (rx, seed) in ((14, 1), (33, 2), (52, 3)):
        rng = np.random.default_rng(700 + seed)
        px_ = x + rx
        for yy2 in range(y + h - 1, y + 10, -1):
            if not sea[yy2 - y, min(w - 1, max(0, px_ - x))]:
                lay.px(px_, yy2, 'B', 3.0)
            if rng.random() < 0.3:
                px_ += int(rng.choice([-1, 1]))
    # state borders (dotted ink) and the armistice line far east (bold, dashed)
    for yy2 in range(y + 12, y + h, 2):
        lay.px(x + 24 + int(3 * math.sin(yy2 * 0.4)), yy2, 'I', 2.0)
    for yy2 in range(y + 6, y + h):
        if (yy2 // 3) % 2 == 0:
            xx2 = x + w - 14 + int(2 * math.sin(yy2 * 0.3))
            lay.rect(xx2, yy2, 2, 1, 'R', 1.0, flat=True)
    # Berlin: a dot with a ring; a few cities
    lay.rect(x + 38, y + 22, 2, 2, 'I', 1.0, flat=True)
    lay.px(x + 37, y + 21, 'R', 1.0); lay.px(x + 40, y + 24, 'R', 1.0)
    for (cx, cy) in ((x + 12, y + 30), (x + 22, y + 40), (x + 50, y + 34), (x + 30, y + 18), (x + 58, y + 26)):
        lay.px(cx, cy, 'I', 2.0)
    # title cartouche
    lay.rect(x + 3, y + h - 8, 30, 6, 'P', 5.6, flat=True)
    lay.hline(x + 5, y + h - 6, 24, 'I', 2.0, flat=True)
    lay.hline(x + 5, y + h - 4, 16, 'I', 2.0, flat=True)
    lay.rect(x + w + 4, y - 2, 1, h + 7, 'W', 2.0, flat=True)


# =========================================================================== props
def props_library(Prop):
    return [card_catalogue_lib(Prop), librarian_desk(Prop), globe(Prop), reading_table(Prop),
            library_ladder(Prop), book_trolley(Prop)]


def card_catalogue_lib(Prop):
    x0, x1 = L.CATALOGUE
    w = x1 - x0
    p = Prop('lib_catalogue', x0, 292, w, 82, 'reading-room card catalogue: 9 x 4 drawers, one pulled out (exp_card_catalogue)')
    lay = p.lay
    top = 10
    rows, cols = 9, 4
    dw, dh = (w - 6) // cols, 6
    bh = rows * dh + 3
    # sign 'KATALOG' on the top
    m = kit.text_mask('KATALOG', '35')
    lay.rect((w - m.shape[1]) // 2 - 2, 0, m.shape[1] + 4, 7, 'D', 1.4, hgt=0.6, flat=True)
    lay.put(m, (w - m.shape[1]) // 2, 1, 'A', 4.2, flat=True)
    lay.rect(1, top - 3, w - 2, 3, 'D', 4.0, hgt=0.65, flat=True)
    lay.rect(1, top - 3, w - 2, 1, 'D', 5.4, hgt=0.7, flat=True)
    lay.rect(2, top, w - 4, bh, 'D', 1.8, hgt=0.4, flat=True)
    rng = _rng('libcat')
    for r in range(rows):
        for c in range(cols):
            x = 3 + c * dw
            y = top + 1 + r * dh
            lay.rect(x, y, dw - 1, dh - 1, 'D', 3.2, hgt=0.5, flat=True)
            lay.rect(x, y, dw - 1, 1, 'D', 4.2, hgt=0.55, flat=True)
            lay.rect(x + dw // 2 - 2, y + 1, 4, 2, 'P', 3.0 + float(rng.choice([0, 0.6])), hgt=0.6, flat=True)
            lay.px(x + dw // 2 - 1, y + 3, 'A', 4.0, hgt=0.7)
    # pulled-out drawer (row 4, col 1) with index cards and a brass rod
    x = 3 + 1 * dw
    y = top + 1 + 4 * dh
    lay.rect(x - 1, y - 4, dw + 1, 4, 'P', 5.6, hgt=0.75, flat=True)
    for k in range(0, dw, 2):
        lay.px(x - 1 + k, y - 4, 'P', 4.2)
    lay.px(x + 3, y - 5, 'P', 6.2)                                                  # a card standing up
    lay.rect(x - 1, y, dw + 1, dh, 'D', 3.8, hgt=0.8, flat=True)
    lay.rect(x - 1, y, dw + 1, 1, 'D', 5.0, hgt=0.85, flat=True)
    lay.rect(x + dw // 2 - 2, y + 1, 4, 2, 'P', 5.4, hgt=0.85, flat=True)
    # stand + legs
    sy = top + bh
    lay.rect(1, sy, w - 2, 3, 'D', 3.0, hgt=0.5, flat=True)
    lay.rect(1, sy, w - 2, 1, 'D', 4.4, hgt=0.55, flat=True)
    for lx in (3, w - 6):
        lay.rect(lx, sy + 3, 3, p.h - sy - 3, 'D', 2.6, hgt=0.5, flat=True)
        lay.rect(lx, sy + 3, 1, p.h - sy - 3, 'D', 3.8, hgt=0.55, flat=True)
    lay.rect(6, p.h - 8, w - 12, 1, 'D', 2.0, hgt=0.4, flat=True)
    # loose cards on the top + a pencil
    lay.rect(6, top - 5, 8, 2, 'P', 5.8, hgt=0.75, flat=True)
    lay.rect(16, top - 4, 6, 1, 'P', 5.0, hgt=0.75, flat=True)
    lay.line(26, top - 4, 33, top - 5, 'R', 1.0)
    return p


def librarian_desk(Prop):
    x0, x1 = L.LIB_DESK
    w = x1 - x0
    ct = 30                     # desk top front edge (local y)
    H = ct + 30
    p = Prop('lib_desk', x0, 293, w, H, "librarian's desk: green lamp, date stamp, card trays, returned books, tube terminal")
    lay = p.lay
    lay.rect(0, ct - 4, w, 4, 'D', 4.2, hgt=0.6, flat=True)
    lay.rect(0, ct - 4, w, 1, 'D', 3.0, hgt=0.55, flat=True)
    top_m = np.ones((4, w), bool)
    lay.paint_normal(top_m, 0, ct - 4, (0.0, 0.9, 0.44))
    lay.rect(0, ct, w, 1, 'A', 3.2, hgt=0.75, flat=True)
    lay.rect(1, ct + 1, w - 2, H - ct - 1, 'D', 2.6, hgt=0.4, flat=True)
    for k in range(3):
        bx = 4 + k * ((w - 8) // 3)
        bw = (w - 8) // 3 - 4
        lay.rect(bx, ct + 4, bw, H - ct - 12, 'D', 2.0, hgt=0.3, flat=True)
        lay.rect(bx + 2, ct + 6, bw - 4, H - ct - 16, 'D', 3.0, hgt=0.45, flat=True)
        lay.rect(bx + 2, ct + 6, bw - 4, 1, 'D', 4.0, hgt=0.5, flat=True)
    lay.rect(1, H - 5, w - 2, 5, 'D', 1.2, hgt=0.3, flat=True)
    lay.rect(1, H - 5, w - 2, 1, 'D', 2.6, hgt=0.35, flat=True)
    # returned books in a stack (left), a card tray, the date stamp and its pad
    for k, (rm, t, bw) in enumerate((('D', 3.0, 16), ('B', 2.4, 15), ('G', 2.6, 17), ('D', 2.2, 14))):
        lay.rect(4 + (k % 2), ct - 7 - k * 3, bw, 3, rm, t, hgt=0.7, flat=True)
        lay.rect(4 + (k % 2), ct - 7 - k * 3, bw, 1, rm, t + 1.0, hgt=0.75, flat=True)
        lay.rect(4 + (k % 2) + bw - 1, ct - 7 - k * 3, 1, 3, 'P', 5.0, hgt=0.7, flat=True)   # page edges
    lay.rect(26, ct - 8, 14, 4, 'D', 3.4, hgt=0.7, flat=True)
    for k in range(13):
        lay.px(27 + k, ct - 9 - (k % 3 == 0), 'P', 5.0 if k % 2 else 4.2)
    lay.rect(44, ct - 9, 3, 5, 'D', 4.0, hgt=0.75, flat=True)                     # date stamp handle
    lay.rect(43, ct - 5, 5, 2, 'I', 1.4, hgt=0.7, flat=True)
    lay.rect(50, ct - 6, 7, 2, 'I', 1.6, hgt=0.7, flat=True)                       # pad
    lay.rect(51, ct - 6, 5, 1, 'B', 2.0, hgt=0.72, flat=True)
    # green banker's lamp (the librarian's)
    bx = 64
    lay.rect(bx - 4, ct - 5, 10, 2, 'A', 2.8, hgt=0.8, flat=True)
    lay.rect(bx - 4, ct - 5, 10, 1, 'A', 4.4, hgt=0.85, flat=True)
    lay.rect(bx, ct - 12, 2, 7, 'A', 3.2, hgt=0.85, flat=True)
    sy = ct - 17
    lay.poly([(bx - 8, sy + 4), (bx + 9, sy + 4), (bx + 7, sy), (bx - 6, sy)], 'G', 3.0, hgt=0.85)
    lay.rect(bx - 6, sy, 14, 1, 'G', 6.0, emis=True, flat=True)
    lay.rect(bx - 7, sy + 2, 16, 1, 'G', 4.4, emis=True, flat=True)
    lay.rect(bx - 8, sy + 4, 18, 1, 'G', 5.0, emis=True, flat=True)
    lay.rect(bx - 5, sy + 5, 12, 1, 'A', 6.0, emis=True, flat=True)
    p.lights.append({'name': 'lamp_librarian', 'pos': (x0 + bx + 1, p.y + sy + 6), 'kind': 'green', 'energy': 1.4,
                     'radius': 84, 'height': -2, 'wrap_add': 0.06})
    # pneumatic tube terminal (brass cylinder with a lid) at the right end, where the wall tube ends
    tx = w - 9
    lay.rect(tx, ct - 14, 5, 10, 'A', 3.0, hgt=0.8, flat=True)
    lay.rect(tx, ct - 14, 1, 10, 'A', 4.6, hgt=0.82, flat=True)
    lay.rect(tx - 1, ct - 15, 7, 2, 'A', 4.0, hgt=0.85, flat=True)
    lay.rect(tx - 5, ct - 7, 4, 4, 'K', 3.6, hgt=0.75, flat=True)                  # wire basket
    lay.rect(tx - 5, ct - 5, 4, 1, 'P', 5.6, hgt=0.76, flat=True)
    return p


# coarse world map for the globe: 36 x 18 cells (10 degrees each), '#' = land
WORLD = [
    '....................................',
    '..##....##..........###########.....',
    '.######.####.....#################..',
    '..######.###...##################...',
    '...#######.....###################..',
    '....######.....############.######..',
    '.....####......#####...#####..####..',
    '......###.....#######..#######.#....',
    '.......##.....########...####.......',
    '........####...#######.....#..#.....',
    '.........#####..#####.........##....',
    '.........######.####..........###...',
    '..........####...###.........#####..',
    '..........###....##..........#####..',
    '..........##.....#.................#',
    '..........#.........................',
    '....................................',
    '...............#############........',
]


def globe(Prop):
    cxw = L.GLOBE_X
    p = Prop('globe', cxw - 12, 295, 25, 52, 'floor globe on a tripod stand (exp_globe)')
    lay = p.lay
    cx, cy, r = 12.0, 14.0, 10.0
    land = np.array([[c == '#' for c in row] for row in WORLD], bool)
    lon0, lat0 = math.radians(18.0), math.radians(25.0)
    for yy in range(int(cy - r) - 1, int(cy + r) + 2):
        for xx in range(int(cx - r) - 1, int(cx + r) + 2):
            u = (xx + 0.5 - cx) / r
            v = (yy + 0.5 - cy) / r
            d = u * u + v * v
            if d > 1.0:
                continue
            z = math.sqrt(1 - d)
            # orthographic -> lat/lon (tilted by lat0)
            lat = math.asin(-v * math.cos(lat0) + z * math.sin(lat0))
            lon = lon0 + math.atan2(u, z * math.cos(lat0) + v * math.sin(lat0))
            gx = int(((math.degrees(lon) + 180) % 360) / 10) % 36
            gy = min(17, max(0, int((90 - math.degrees(lat)) / 10)))
            shade = 0.9 * (u * -0.55 + v * -0.45 + z * 0.7)                          # light from the window
            if land[gy, gx]:
                lay.px(xx, yy, 'P', 3.6 + shade * 1.6, hgt=0.7)
            else:
                lay.px(xx, yy, 'B', 3.0 + shade * 1.6, hgt=0.7)
    lay.dome_height(cx, cy, r, r, base=0.4, amp=0.6)
    # meridian ring (brass) + axis pins
    for a in np.linspace(-1.2, 4.3, 120):
        x = cx + math.cos(a) * (r + 1.6)
        y = cy + math.sin(a) * (r + 1.6) * 1.0
        lay.px(int(round(x - 0.5)), int(round(y - 0.5)), 'A', 3.4 if math.sin(a) < 0 else 2.4, hgt=0.8)
    lay.px(int(cx) + 3, int(cy - r - 2), 'A', 5.0)
    lay.px(int(cx) - 3, int(cy + r + 1), 'A', 3.0)
    # horizon ring (flat ellipse at the equator line of the stand)
    for a in np.linspace(0, math.pi, 30):
        lay.px(int(round(cx + math.cos(a) * (r + 2))), int(round(cy + 2 + math.sin(a) * 2.5)), 'D', 4.4, hgt=0.75)
    # turned column + tripod legs
    lay.rect(int(cx) - 1, int(cy + r + 2), 3, 14, 'D', 3.2, hgt=0.6, flat=True)
    lay.rect(int(cx) - 1, int(cy + r + 2), 1, 14, 'D', 4.6, hgt=0.65, flat=True)
    lay.ellipse(cx + 0.5, cy + r + 9, 2.6, 1.6, 'D', 3.6, hgt=0.6, flat=True)
    bx = int(cy + r + 16)
    for (a, b) in (((int(cx), bx), (1, p.h - 1)), ((int(cx) + 1, bx), (p.w - 2, p.h - 1)),
                   ((int(cx), bx), (int(cx), p.h - 1))):
        lay.line(a[0], a[1], b[0], b[1], 'D', 2.8)
    lay.px(1, p.h - 1, 'A', 3.0); lay.px(p.w - 2, p.h - 1, 'A', 3.0)
    return p


def reading_table(Prop):
    x0, x1 = L.LIB_READ_TABLE
    w = x1 - x0
    T = 30                      # table top (local y of the front edge)
    H = T + 26
    p = Prop('reading_table', x0, 294, w, H, 'reading table under the tilted window: two green lamps, open books, chairs')
    lay = p.lay
    # table top (seen slightly from above) + apron
    lay.rect(0, T - 4, w, 4, 'D', 4.4, hgt=0.55, flat=True)
    lay.rect(0, T - 4, w, 1, 'D', 3.2, hgt=0.5, flat=True)
    lay.paint_normal(np.ones((4, w), bool), 0, T - 4, (0.0, 0.9, 0.44))
    lay.rect(0, T, w, 2, 'D', 3.0, hgt=0.6, flat=True)
    lay.rect(0, T, w, 1, 'D', 5.0, hgt=0.65, flat=True)
    lay.rect(2, T + 2, w - 4, 3, 'D', 1.8, hgt=0.4, flat=True)
    for lx in (3, w - 7):                                                         # turned legs
        lay.rect(lx, T + 5, 4, H - T - 5, 'D', 2.8, hgt=0.5, flat=True)
        lay.rect(lx, T + 5, 1, H - T - 5, 'D', 4.2, hgt=0.55, flat=True)
        lay.rect(lx - 1, T + 8, 6, 2, 'D', 3.4, hgt=0.55, flat=True)
        lay.rect(lx - 1, H - 3, 6, 2, 'D', 2.2, hgt=0.5, flat=True)
    lay.rect(7, H - 9, w - 14, 2, 'D', 2.0, hgt=0.4, flat=True)                  # stretcher
    # two green banker's lamps
    for (bx, nm) in ((16, 'read_lamp_1'), (w - 18, 'read_lamp_2')):
        lay.rect(bx - 4, T - 6, 10, 2, 'A', 2.8, hgt=0.8, flat=True)
        lay.rect(bx - 4, T - 6, 10, 1, 'A', 4.4, hgt=0.85, flat=True)
        lay.rect(bx, T - 13, 2, 7, 'A', 3.2, hgt=0.85, flat=True)
        sy = T - 18
        lay.poly([(bx - 8, sy + 4), (bx + 9, sy + 4), (bx + 7, sy), (bx - 6, sy)], 'G', 3.0, hgt=0.85)
        lay.rect(bx - 6, sy, 14, 1, 'G', 6.0, emis=True, flat=True)
        lay.rect(bx - 7, sy + 2, 16, 1, 'G', 4.4, emis=True, flat=True)
        lay.rect(bx - 8, sy + 4, 18, 1, 'G', 5.0, emis=True, flat=True)
        lay.rect(bx - 5, sy + 5, 12, 1, 'A', 6.0, emis=True, flat=True)
        p.lights.append({'name': nm, 'pos': (x0 + bx + 1, p.y + sy + 6), 'kind': 'green', 'energy': 1.3,
                         'radius': 80, 'height': -2, 'wrap_add': 0.06})
    # an open book (pages fanning), a closed volume, a notebook with a pencil, a magnifier
    ox = 30
    lay.poly([(ox, T - 4), (ox + 9, T - 6), (ox + 18, T - 4), (ox + 18, T - 2), (ox, T - 2)], 'P', 5.8, hgt=0.75)
    lay.line(ox + 9, T - 6, ox + 9, T - 2, 'P', 3.4)
    for k in range(3):
        lay.hline(ox + 2, T - 4 + k, 5, 'I', 2.8, flat=True)
        lay.hline(ox + 11, T - 4 + k, 5, 'I', 2.8, flat=True)
    lay.rect(ox + 22, T - 7, 12, 3, 'R', 1.0, hgt=0.75, flat=True)
    lay.rect(ox + 22, T - 7, 12, 1, 'R', 2.0, hgt=0.78, flat=True)
    lay.rect(ox + 33, T - 7, 1, 3, 'P', 5.0, hgt=0.75, flat=True)
    lay.ellipse(ox + 40, T - 3, 2.5, 1.2, 'A', 3.0, hgt=0.8, flat=True)
    lay.px(ox + 40, T - 3, 'B', 5.4)
    lay.line(ox + 42, T - 3, ox + 45, T - 2, 'D', 2.0)
    # two chairs pushed in under the table (backs seen from the room)
    for cx in (20, w - 26):
        lay.rect(cx, T - 3, 12, 2, 'D', 3.6, hgt=0.75, flat=True)
        lay.rect(cx, T - 3, 12, 1, 'D', 5.0, hgt=0.8, flat=True)
        lay.rect(cx + 1, T - 1, 2, H - T + 1, 'D', 2.4, hgt=0.7, flat=True)
        lay.rect(cx + 9, T - 1, 2, H - T + 1, 'D', 2.4, hgt=0.7, flat=True)
        for k in range(3):
            lay.rect(cx + 4 + k * 2, T - 1, 1, 9, 'D', 3.0, hgt=0.7, flat=True)
        lay.rect(cx, T + 10, 12, 2, 'D', 3.2, hgt=0.72, flat=True)
    return p


def library_ladder(Prop):
    x = 616
    top = L.LIB_RAIL_Y - 1
    p = Prop('lib_ladder', x, 291, 28, 291 - top + 1, 'rolling library ladder hooked on the brass rail (sections I/II)')
    lay = p.lay
    h = p.h
    for k in range(h):
        f = k / (h - 1)
        xl = int(round(5 - 3 * f))
        xr = int(round(21 + 3 * f))
        lay.rect(xl, k, 2, 1, 'D', 3.6, hgt=0.6, flat=True)
        lay.px(xl, k, 'D', 5.0, hgt=0.65)
        lay.rect(xr, k, 2, 1, 'D', 3.2, hgt=0.6, flat=True)
        lay.px(xr + 1, k, 'D', 1.8, hgt=0.55)
    for y in range(10, h - 6, 11):
        f = y / (h - 1)
        xl = int(round(5 - 3 * f)) + 2
        xr = int(round(21 + 3 * f))
        lay.rect(xl, y, xr - xl, 2, 'D', 3.4, hgt=0.55, flat=True)
        lay.rect(xl, y, xr - xl, 1, 'D', 5.2, hgt=0.6, flat=True)
        lay.rect(xl, y + 2, xr - xl, 1, 'D', 1.0, hgt=0.2, flat=True)
    for x_ in (4, 21):
        lay.rect(x_, 0, 3, 2, 'A', 3.6, hgt=0.8, flat=True)
        lay.px(x_ + (2 if x_ < 10 else 0), 2, 'A', 2.4)
    for x_ in (1, 23):
        lay.ellipse(x_ + 1.5, h - 2.5, 2.0, 2.0, 'I', 1.4, hgt=0.6, flat=True)
        lay.px(x_ + 1, h - 3, 'W', 5.0)
    return p


def book_trolley(Prop):
    p = Prop('book_trolley', 1158, 293, 30, 30, 'book trolley with volumes waiting to be shelved')
    lay = p.lay
    rng = _rng('trolley')
    for (ty, n) in ((6, 1), (17, 1)):
        lay.rect(1, ty + 8, 28, 2, 'D', 3.4, hgt=0.6, flat=True)
        lay.rect(1, ty + 8, 28, 1, 'D', 4.6, hgt=0.65, flat=True)
        books_row(lay, 2, 28, ty + 8, 9, rng, 'mixed', gaps=0.0)
    lay.rect(1, 0, 2, 27, 'D', 2.6, hgt=0.55, flat=True)
    lay.rect(27, 4, 2, 23, 'D', 2.2, hgt=0.55, flat=True)
    lay.rect(0, 0, 4, 2, 'D', 4.0, hgt=0.6, flat=True)                            # handle
    for x_ in (2, 25):
        lay.ellipse(x_ + 1.5, 27.5, 2.0, 2.0, 'I', 1.4, hgt=0.6, flat=True)
        lay.px(x_ + 1, 27, 'W', 5.0)
    return p
