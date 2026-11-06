"""env_berlin_hall -- the arrival hall of the Bauarchiv floor (round 2): stairwell door with the state plaque,
the porter's lodge (interior seen through its glazing), a regulator wall clock, a window with pigeons on the
outside sill, the 'Chronik' photo display and the way into the reading room.

Painted into the shared room MLayer (tone space, env_berlin_kit) by paint_hall(room); props (lodge front,
bench) live in props_hall().  Insignia sites take `hist` (see env_berlin_insignia).
"""
from __future__ import annotations

import math

import numpy as np

import env_berlin_insignia as INS
import env_berlin_kit as kit
import env_berlin_layout as L
import pg

R = kit.archive_ramps()


def _pseudo(lay, x, y, w, rows, ramp, tone, seed, gap=2):
    rng = np.random.default_rng(seed)
    for r in range(rows):
        xx = x
        end = x + w - int(rng.integers(0, max(1, w // 3)))
        while xx < end:
            wl = int(rng.integers(2, 6))
            lay.hline(xx, y + r * gap, min(wl, end - xx), ramp, tone, flat=True)
            xx += wl + 1


# =========================================================================== insignia site: the plaque
def plaque(lay, hist: bool):
    """Bronze plaque beside the stairwell door: state emblem above 'BAUAMT / ARCHIV'.
    neutral: plain eagle on a perch bar; hist: Reichsadler with the wreathed swastika."""
    x, y, w, h = L.PLAQUE
    # plate: dark bronze with a bevelled rim, slightly raised from the wall
    lay.rect(x, y, w, h, 'A', 1.0, hgt=0.55, flat=True)
    lay.rect(x, y, w, 1, 'A', 3.0, hgt=0.6, flat=True)
    lay.rect(x, y, 1, h, 'A', 2.4, hgt=0.6, flat=True)
    lay.rect(x + w - 1, y, 1, h, 'D', 1.4, hgt=0.5, flat=True)
    lay.rect(x, y + h - 1, w, 1, 'D', 1.2, hgt=0.5, flat=True)
    lay.rect(x + 2, y + 2, w - 4, h - 4, 'D', 1.6, hgt=0.45, flat=True)       # sunken field (patinated)
    lay.rect(x + 2, y + 2, w - 4, 1, 'D', 0.8, hgt=0.42, flat=True)
    # emblem in relief
    e = INS.eagle_masks(w - 6, wreath=hist, swastika=hist)
    eh, ew = e['size']
    ex, ey = x + 3, y + 3
    if hist:
        inner = np.zeros((eh, ew), bool)
        ys, xs = np.nonzero(e['wreath'])
        if len(ys):
            cy, cx = (ys.min() + ys.max()) / 2.0, (xs.min() + xs.max()) / 2.0
            rr = (xs.max() - xs.min()) / 2.0 - 0.8
            yy, xx = np.mgrid[0:eh, 0:ew]
            inner = ((yy - cy) ** 2 + (xx - cx) ** 2 <= rr * rr) & ~e['wreath'] & ~e['body']
        lay.put(inner, ex, ey, 'D', 0.6, hgt=0.4, flat=True)
    lay.put(e['body'], ex, ey, 'A', 3.4, hgt=0.85, flat=True)
    lay.put(e['lines'], ex, ey, 'A', 2.0, hgt=0.7, flat=True)
    lay.put(e['eye'], ex, ey, 'D', 0.8, hgt=0.7, flat=True)
    if hist:
        lay.put(e['wreath'], ex, ey, 'A', 3.0, hgt=0.8, flat=True)
        lay.put(e['swastika'], ex, ey, 'A', 4.2, hgt=0.85, flat=True)
    # polished highlights on the upper-left edges of the relief (people touch it in passing)
    allm = e['all']
    hi = allm & ~np.vstack([np.zeros((1, ew), bool), allm[:-1]])
    lay.put(hi & e['body'], ex, ey, 'A', 4.6, hgt=0.88, flat=True)
    # engraved lettering
    for k, txt in enumerate(('BAUAMT', 'ARCHIV')):
        m = kit.text_mask(txt, '35')
        lay.put(m, x + (w - m.shape[1]) // 2, y + h - 14 + k * 6, 'A', 3.8, hgt=0.5, flat=True)
    for (sx, sy) in ((x + 1, y + 1), (x + w - 2, y + 1), (x + 1, y + h - 2), (x + w - 2, y + h - 2)):
        lay.px(sx, sy, 'A', 4.4, hgt=0.7)
    lay.rect(x + w, y + 1, 1, h, 'W', 2.2, flat=True)                          # cast shadow
    lay.rect(x + 1, y + h, w, 1, 'W', 2.4, flat=True)


# =========================================================================== hall
def paint_hall(room):
    lay = room.lay
    x0, x1 = L.HALL
    room.dado(x0 + 10, x1, top=248)
    # end wall (poche) at the far left of the building
    lay.rect(0, 0, 10, L.FLOOR, 'W', 1.2, hgt=0.9, flat=True)
    lay.rect(9, 0, 1, L.FLOOR, 'W', 3.0, hgt=0.8, flat=True)
    for (px0, px1) in ((14, 26), (296, 308), (372, 384), (500, 512)):
        room.pilaster(px0, px1, room.frieze_bottom + 8)
    # ---- the stairwell door: glazed double door, warm stairwell light behind the frosted glass
    d0, d1 = L.STAIR_DOOR
    room.double_door(d0, d1, L.STAIR_DOOR_TOP, glass_text='BAUARCHIV', lit=True, seed=61)
    # fanlight above the door (semicircular, frosted, lit from the stairwell)
    cx = (d0 + d1) / 2.0
    top = L.STAIR_DOOR_TOP - 17
    m, mx, my = lay.ellipse_mask(cx, top + 15.5, 22.0, 15.0)
    m[int(top + 15.5 - my):, :] = False
    lay.put(m, mx, my, 'D', 2.0, hgt=0.4, flat=True)
    inner, ix, iy = lay.ellipse_mask(cx, top + 15.5, 19.5, 12.5)
    inner[int(top + 15.5 - iy):, :] = False
    lay.put(inner, ix, iy, 'A', 2.8, emis=True, flat=True)
    for a in range(20, 170, 30):                                               # radiating glazing bars
        r = math.radians(a)
        lay.line(cx, top + 15, cx + math.cos(r) * 19, top + 15 - math.sin(r) * 12, 'D', 1.6)
    lay.rect(int(cx) - 2, top + 13, 5, 3, 'D', 2.6, hgt=0.5, flat=True)
    # sign above
    msg = kit.text_mask('TREPPENHAUS', '35')
    tw = msg.shape[1]
    sy = top - 12
    lay.rect(int(cx) - tw // 2 - 3, sy, tw + 6, 9, 'W', 1.4, hgt=0.5, flat=True)
    lay.rect(int(cx) - tw // 2 - 3, sy, tw + 6, 1, 'W', 3.6, hgt=0.55, flat=True)
    lay.put(msg, int(cx) - tw // 2, sy + 2, 'P', 4.6, flat=True)
    room.lights.append({'name': 'stair_glass', 'pos': (cx, 214), 'kind': 'warm', 'energy': 0.4, 'radius': 70,
                        'height': 8})
    # ---- the plaque (insignia site)
    plaque(lay, hist=room.hist)
    room.decal_sites['plaque'] = (L.PLAQUE[0] - 1, L.PLAQUE[1] - 1, L.PLAQUE[2] + 3, L.PLAQUE[3] + 3, plaque)
    # door bell push + house rules beside the door
    lay.rect(d0 - 14, 224, 5, 7, 'A', 2.6, hgt=0.6, flat=True)
    lay.px(d0 - 12, 227, 'P', 6.0, hgt=0.7)
    room.framed_notice(L.PLAQUE[0] + 2, 222, 22, 20, seed=611, emblem=False)
    # ---- building directory above the lodge: white enamel letters slotted into a black felt board
    directory_board(room, 148, 150, 52, 50)
    # ---- porter's lodge interior (seen through the glazing of the lodge prop)
    lodge_interior(room)
    # ---- regulator clock (hands and pendulum are animated by an actor)
    regulator(room)
    # ---- window with radiator; pigeons sit on the outside sill (actor)
    for i, (wx0, wx1) in enumerate(L.HALL_WINDOWS):
        room.window(wx0, wx1, 10 + i, blind=0, sill_item=None)
    # ---- 'Chronik' photo display (exp_photo)
    photos(room)
    # ---- reading-room sign with a pointing hand
    sx, sy = 446, 230
    lay.rect(sx, sy, 48, 9, 'P', 5.2, hgt=0.5, flat=True)                         # white enamel sign
    lay.rect(sx, sy, 48, 1, 'P', 6.0, hgt=0.55, flat=True)
    lay.rect(sx + 1, sy + 8, 47, 1, 'P', 3.4, hgt=0.45, flat=True)
    m = kit.text_mask('LESESAAL', '35')
    lay.put(m, sx + 3, sy + 2, 'I', 1.0, flat=True)
    hand = ['.##.....', '########', '.####...', '.###....']                    # fist left, index finger right
    for yy, row in enumerate(hand):
        for xx, ch in enumerate(row):
            if ch == '#':
                lay.px(sx + 37 + xx, sy + 2 + yy, 'I', 1.0)
    lay.rect(sx + 48, sy + 1, 1, 9, 'W', 2.4, flat=True)
    # ---- 'Rauchen verboten' enamel sign + fire bucket hooks by the partition
    lay.rect(476, 196, 20, 11, 'P', 5.6, hgt=0.5, flat=True)
    lay.rect(476, 196, 20, 1, 'P', 6.6, hgt=0.55, flat=True)
    lay.rect(477, 197, 18, 9, 'P', 5.0, hgt=0.5, flat=True)
    _pseudo(lay, 479, 199, 14, 3, 'I', 1.0, seed=612, gap=2)
    lay.rect(496, 197, 1, 11, 'W', 2.4, flat=True)
    # ---- hall pendant: opal glass globe on a chain (warm)
    pendant_globe(room, L.HALL_LAMP, room.frieze_bottom - 4, 52, name='hall_pendant', energy=0.85)
    # ---- conduit + wall telephone of the building (between the door and the lodge)
    lay.rect(134, 120, 1, 94, 'W', 3.6, hgt=0.3, flat=True)
    lay.rect(131, 214, 5, 4, 'W', 2.6, hgt=0.5, flat=True)


def directory_board(room, x, y, w, h):
    lay = room.lay
    lay.rect(x - 2, y - 2, w + 4, h + 4, 'D', 2.6, hgt=0.6, flat=True)
    lay.rect(x - 2, y - 2, w + 4, 1, 'D', 4.2, hgt=0.65, flat=True)
    lay.rect(x - 2, y + h + 1, w + 4, 1, 'D', 1.2, hgt=0.5, flat=True)
    lay.rect(x, y, w, h, 'N', 0.6, hgt=0.3, flat=True)
    for k in range(y + 1, y + h, 2):                                              # felt grooves
        lay.rect(x, k, w, 1, 'N', 0.2, hgt=0.28, flat=True)
    m = kit.text_mask('HAUS 2', '35')
    lay.put(m, x + (w - m.shape[1]) // 2, y + 3, 'P', 5.4, flat=True)
    lay.rect(x + 3, y + 10, w - 6, 1, 'P', 3.0, flat=True)
    rng = np.random.default_rng(641)
    for r in range(6):
        yy = y + 13 + r * 6
        nx = x + 3
        lay.rect(nx, yy, 7, 3, 'P', 4.4, flat=True)                                # room number
        _pseudo(lay, nx + 10, yy + 1, w - 16 - int(rng.integers(0, 10)), 1, 'P', 4.6, seed=642 + r)
    lay.rect(x + w + 2, y - 1, 1, h + 4, 'W', 2.2, flat=True)


def lodge_interior(room):
    lay = room.lay
    x0, x1 = L.LODGE[0] + 3, L.LODGE[1] - 3
    y0, y1 = L.LODGE_TOP + 2, 262
    # panelled interior back wall (dark varnished wood)
    lay.rect(x0, y0, x1 - x0, y1 - y0, 'D', 1.6, hgt=-0.2, flat=True)
    for k in range(x0 + 2, x1, 12):
        lay.rect(k, y0, 1, y1 - y0, 'D', 1.0, hgt=-0.25, flat=True)
        lay.rect(k + 1, y0, 1, y1 - y0, 'D', 2.2, hgt=-0.2, flat=True)
    lay.rect(x0, y0, x1 - x0, 2, 'D', 0.8, hgt=-0.25, flat=True)               # shadow under the lodge roof
    # key board: three rows of hooks with brass tags (two keys missing)
    kx, ky = x0 + 6, y0 + 6
    lay.rect(kx - 2, ky - 2, 31, 22, 'D', 3.0, hgt=0.3, flat=True)
    lay.rect(kx - 2, ky - 2, 31, 1, 'D', 4.4, hgt=0.35, flat=True)
    rng = np.random.default_rng(633)
    for r in range(3):
        for c in range(7):
            hx, hy = kx + c * 4, ky + r * 6
            lay.px(hx + 1, hy, 'A', 3.6, hgt=0.6)
            if (r, c) in ((1, 2), (2, 5)):
                continue
            lay.rect(hx + 1, hy + 1, 1, 2, 'K', 4.0, hgt=0.5, flat=True)          # key
            lay.rect(hx, hy + 3, 3, 2, 'A', 2.6 + float(rng.choice([0.0, 0.8])), hgt=0.5, flat=True)
    # calendar (one sheet per day; today's date circled -- not readable at this scale)
    lay.rect(x0 + 40, y0 + 5, 10, 13, 'P', 5.4, hgt=0.2, flat=True)
    lay.rect(x0 + 40, y0 + 5, 10, 3, 'R', 1.0, hgt=0.2, flat=True)
    _pseudo(lay, x0 + 41, y0 + 10, 8, 4, 'I', 2.0, seed=634, gap=2)
    # shelf with the radio (glowing dial) and a tea glass in a holder
    sy = y0 + 22
    lay.rect(x0 + 54, sy, x1 - x0 - 56, 2, 'D', 3.6, hgt=0.5, flat=True)
    lay.rect(x0 + 54, sy + 2, x1 - x0 - 56, 1, 'D', 0.8, hgt=0.2, flat=True)
    rx, ry = x0 + 70, sy - 12
    radio(lay, rx, ry)
    room.radio_pos = (rx, ry)
    lay.rect(x0 + 60, sy - 6, 4, 6, 'P', 4.0, hgt=0.5, flat=True)                # glass of tea
    lay.rect(x0 + 60, sy - 3, 4, 3, 'A', 1.6, hgt=0.5, flat=True)
    lay.rect(x0 + 59, sy - 5, 1, 4, 'K', 3.0, hgt=0.5, flat=True)
    # duty roster pinned under the shelf + a lamp hanging from the lodge ceiling (warm, the focal light)
    lay.rect(x0 + 58, sy + 5, 14, 9, 'P', 4.6, hgt=0.2, flat=True)
    _pseudo(lay, x0 + 59, sy + 7, 12, 3, 'I', 2.0, seed=635, gap=2)
    lx = x0 + 48
    lay.rect(lx, y0, 1, 4, 'K', 2.0, flat=True)
    lay.rect(lx - 3, y0 + 4, 7, 2, 'G', 2.6, hgt=0.5, flat=True)
    lay.rect(lx - 2, y0 + 6, 5, 1, 'A', 6.0, emis=True, flat=True)
    room.lights.append({'name': 'lodge_lamp', 'pos': (lx, y0 + 8), 'kind': 'warm', 'energy': 1.0, 'radius': 88,
                        'height': 14, 'cone': (0.0, 1.0, -0.2)})


def radio(lay, x, y):
    """Tube radio of the 1950s: walnut cabinet, cloth grille, long glass dial (emission), magic eye."""
    w, h = 22, 12
    lay.rect(x, y, w, h, 'D', 3.4, hgt=0.6, flat=True)
    lay.rect(x, y, w, 1, 'D', 5.0, hgt=0.65, flat=True)
    lay.rect(x, y, 1, h, 'D', 4.4, hgt=0.62, flat=True)
    lay.rect(x + w - 1, y, 1, h, 'D', 1.6, hgt=0.55, flat=True)
    # speaker cloth (left two thirds) with a vertical rib pattern
    lay.rect(x + 2, y + 2, 12, 6, 'P', 2.0, hgt=0.45, flat=True)
    for k in range(x + 3, x + 14, 2):
        lay.rect(k, y + 2, 1, 6, 'P', 1.2, hgt=0.4, flat=True)
    # long horizontal dial glass (glowing) across the bottom with station marks
    lay.rect(x + 2, y + 9, w - 4, 2, 'A', 4.6, emis=True, flat=True)
    for k in range(x + 3, x + w - 3, 3):
        lay.px(k, y + 9, 'A', 3.0, emis=True)
    lay.px(x + 11, y + 10, 'R', 2.0, emis=True)                                # the pointer
    # magic eye (green) + two knobs
    lay.rect(x + 16, y + 3, 3, 3, 'G', 5.0, emis=True, flat=True)
    lay.px(x + 17, y + 4, 'G', 3.0, emis=True)
    lay.px(x + 16, y + 7, 'A', 4.0, hgt=0.7)
    lay.px(x + 19, y + 7, 'A', 4.0, hgt=0.7)


def regulator(room):
    lay = room.lay
    x0, x1 = L.REGULATOR
    w = x1 - x0
    cx, cy, r = L.REG_FACE
    top = cy - r - 12
    bot = 234
    # crown with a small pediment and finials
    lay.poly([(x0 - 1, top + 6), (x1 + 1, top + 6), (cx + 0.5, top - 2)], 'D', 3.2, hgt=0.7)
    lay.line(x0 - 1, top + 6, cx, top - 2, 'D', 5.0)
    lay.rect(x0 - 2, top + 6, w + 4, 3, 'D', 4.0, hgt=0.75, flat=True)
    lay.rect(x0 - 2, top + 6, w + 4, 1, 'D', 5.6, hgt=0.8, flat=True)
    lay.px(x0 - 1, top + 4, 'A', 4.0); lay.px(x1, top + 4, 'A', 4.0); lay.px(cx, top - 3, 'A', 4.6)
    # case body
    lay.rect(x0, top + 9, w, bot - top - 9, 'D', 2.8, hgt=0.6, flat=True)
    lay.rect(x0, top + 9, 1, bot - top - 9, 'D', 4.4, hgt=0.62, flat=True)
    lay.rect(x1 - 1, top + 9, 1, bot - top - 9, 'D', 1.4, hgt=0.55, flat=True)
    # dial: brass bezel ring + enamel face with hour marks (hands drawn at runtime)
    lay.ellipse(cx + 0.5, cy + 0.5, r + 2.0, r + 2.0, 'A', 2.8, hgt=0.75, flat=True)
    lay.ellipse(cx + 0.5, cy + 0.5, r + 1.0, r + 1.0, 'A', 4.4, hgt=0.8, flat=True)
    lay.ellipse(cx + 0.5, cy + 0.5, r - 0.2, r - 0.2, 'P', 5.4, hgt=0.7, flat=True)
    for a in range(0, 360, 30):
        rr = math.radians(a)
        rad = r - 1.4
        lay.px(cx + round(math.cos(rr) * rad), cy + round(math.sin(rr) * rad), 'I', 1.0 if a % 90 else 0.0)
    lay.ellipse(cx - 1.5, cy - 1.5, 2.6, 2.6, 'P', 6.2, hgt=0.7, flat=True)      # enamel sheen
    # glass door over the pendulum (dark interior, brass rail, two weights on chains)
    gy0, gy1 = cy + r + 5, bot - 8
    lay.rect(x0 + 3, gy0, w - 6, gy1 - gy0, 'D', 0.8, hgt=0.4, flat=True)
    lay.rect(x0 + 3, gy0, w - 6, 1, 'D', 0.4, hgt=0.4, flat=True)
    for wx in (x0 + 6, x1 - 7):
        lay.rect(wx, gy0 + 1, 1, 14, 'A', 2.2, hgt=0.5, flat=True)
        lay.rect(wx - 1, gy0 + 15, 3, 9, 'A', 3.4, hgt=0.6, flat=True)
        lay.rect(wx - 1, gy0 + 15, 1, 9, 'A', 4.6, hgt=0.62, flat=True)
    lay.line(x0 + 4, gy0 + 4, x0 + 10, gy0 + 22, 'W', 6.4)                    # glass glint
    lay.rect(x0 + 2, gy0 - 1, w - 4, 1, 'D', 4.0, hgt=0.6, flat=True)
    lay.rect(x0 + 2, gy1, w - 4, 1, 'D', 4.0, hgt=0.6, flat=True)
    # base + finial
    lay.rect(x0 - 1, bot - 8, w + 2, 6, 'D', 3.6, hgt=0.7, flat=True)
    lay.rect(x0 - 1, bot - 8, w + 2, 1, 'D', 5.0, hgt=0.72, flat=True)
    lay.poly([(x0 + 4, bot - 2), (x1 - 4, bot - 2), (cx + 0.5, bot + 5)], 'D', 2.6, hgt=0.6)
    lay.rect(x1 + 1, top + 8, 1, bot - top - 4, 'W', 2.2, flat=True)            # shadow on the wall
    room.regulator_pendulum = (cx, gy0 + 1, gy1 - gy0 - 2)


def photos(room):
    """'Chronik der Dienststelle': three framed photographs (demolition of a street, the model of the
    hall, the foundation-stone ceremony) above a brass caption."""
    lay = room.lay
    x, y, w, h = L.PHOTOS
    rng = np.random.default_rng(651)
    frames = [(x, y + 4, 24, 30), (x + 29, y, 26, 36), (x + 60, y + 4, 24, 30)]
    for i, (fx, fy, fw, fh) in enumerate(frames):
        lay.rect(fx - 1, fy - 1, fw + 2, fh + 2, 'D', 1.4, hgt=0.6, flat=True)
        lay.rect(fx - 1, fy - 1, fw + 2, 1, 'D', 3.2, hgt=0.65, flat=True)
        lay.rect(fx, fy, fw, fh, 'P', 5.6, hgt=0.3, flat=True)                     # passe-partout
        ix, iy, iw, ih = fx + 3, fy + 3, fw - 6, fh - 9
        lay.vgrad(ix, iy, iw, ih, 'P', 3.6, 2.4, hgt=0.3)                          # sepia print
        if i == 0:
            # a tenement street being cleared: facades, a crane jib, a furniture cart
            for k in range(3):
                bx = ix + k * 6
                lay.rect(bx, iy + 4 + (k % 2) * 2, 5, ih - 4 - (k % 2) * 2, 'P', 1.6, flat=True)
                for wy in range(iy + 7, iy + ih - 2, 4):
                    lay.px(bx + 1, wy, 'P', 3.0); lay.px(bx + 3, wy, 'P', 3.0)
            lay.rect(ix + 12, iy + 5, 1, ih - 5, 'P', 0.8, flat=True)                # crane tower
            lay.line(ix + 12, iy + 5, ix + iw - 1, iy + 3, 'P', 0.8)
            lay.rect(ix + 1, iy + ih - 3, 6, 2, 'P', 1.0, flat=True)                  # cart with furniture
            lay.px(ix + 2, iy + ih - 1, 'P', 0.6); lay.px(ix + 5, iy + ih - 1, 'P', 0.6)
            lay.rect(ix + 2, iy + ih - 6, 3, 3, 'P', 1.4, flat=True)
        elif i == 1:
            # the model of the hall on a table, men in dark suits around it
            m, mx, my = lay.ellipse_mask(ix + iw / 2, iy + 12, 6, 5)
            m[max(0, iy + 12 - my):, :] = False                                     # dome = upper half
            lay.put(m, mx, my, 'P', 4.6, flat=True)
            lay.rect(ix + iw // 2 - 8, iy + 12, 16, 4, 'P', 4.2, flat=True)
            lay.rect(ix + 2, iy + 16, iw - 4, 2, 'P', 1.6, flat=True)
            for k in range(5):
                hx = ix + 2 + k * 4
                lay.rect(hx, iy + 18, 2, ih - 18, 'P', 0.6, flat=True)
                lay.px(hx, iy + 17, 'P', 4.0); lay.px(hx + 1, iy + 17, 'P', 3.4)
        else:
            # foundation-stone ceremony: a crowd of heads, a tribune with long banners
            lay.rect(ix + 3, iy + 2, iw - 6, 7, 'P', 1.4, flat=True)                  # tribune
            for k in range(3):
                lay.rect(ix + 4 + k * 4, iy + 2, 2, 10, 'P', 0.8, flat=True)          # banners
            for k in range(26):
                hx = ix + int(rng.integers(0, iw))
                hy = iy + 13 + int(rng.integers(0, ih - 14))
                lay.px(hx, hy, 'P', 0.8 if k % 3 else 1.6)
        lay.rect(fx + 3, fy + fh - 5, fw - 6, 1, 'P', 4.2, flat=True)              # handwritten caption line
        lay.rect(fx + fw + 1, fy, 1, fh + 2, 'W', 2.2, flat=True)                   # shadow
        lay.px(fx + fw // 2, fy - 4, 'I', 1.0, hgt=0.5)                              # nail + string
        lay.line(fx + fw // 2, fy - 4, fx + 3, fy - 1, 'W', 3.4)
        lay.line(fx + fw // 2, fy - 4, fx + fw - 4, fy - 1, 'W', 3.4)
    # brass caption plate
    m = kit.text_mask('CHRONIK 1938-1961', '35')
    px_ = x + (w - m.shape[1]) // 2 - 2
    lay.rect(px_ - 2, y + 40, m.shape[1] + 4, 8, 'A', 2.6, hgt=0.6, flat=True)
    lay.rect(px_ - 2, y + 40, m.shape[1] + 4, 1, 'A', 4.4, hgt=0.65, flat=True)
    lay.put(m, px_, y + 41, 'D', 0.8, flat=True)
    lay.rect(px_ + m.shape[1] + 2, y + 41, 1, 8, 'W', 2.4, flat=True)


def pendant_globe(room, cx, top, length, name, energy=0.8):
    """Opal glass globe on a chain: warm, soft.  Registers a baked light."""
    lay = room.lay
    for yy in range(top, top + length, 2):
        lay.px(cx, yy, 'K', 2.6 if (yy // 2) % 2 else 3.6)
    lay.rect(cx - 3, top, 7, 2, 'K', 3.0, hgt=0.6, flat=True)
    gy = top + length
    lay.rect(cx - 2, gy, 5, 2, 'A', 3.0, hgt=0.7, flat=True)                      # brass gallery
    m, mx, my = lay.ellipse_mask(cx + 0.5, gy + 8, 6.5, 6.5)
    lay.put(m, mx, my, 'A', 5.0, emis=True, flat=True)
    m2, mx2, my2 = lay.ellipse_mask(cx - 0.5, gy + 7, 3.6, 3.6)
    lay.put(m2, mx2, my2, 'A', 6.0, emis=True, flat=True)
    lay.rect(cx - 5, gy + 12, 11, 1, 'A', 4.0, emis=True, flat=True)
    room.lights.append({'name': name, 'pos': (cx, gy + 9), 'kind': 'warm', 'energy': energy, 'radius': 120,
                        'height': 40})


# =========================================================================== props
def props_hall(Prop):
    return [porter_lodge(Prop), hall_bench(Prop), umbrella_stand(Prop)]


def porter_lodge(Prop):
    """The porter's lodge front: panelled lower half, glazing with an open sliding hatch, 'PFÖRTNER' fascia.
    The glazing is transparent (the porter NPC and the interior are seen through it)."""
    x0, x1 = L.LODGE
    top = L.LODGE_TOP
    base = 293
    p = Prop('porter_lodge', x0, base, x1 - x0, base - top + 1,
             "porter's lodge: panelled front, glazing with an open hatch, visitors' book")
    lay = p.lay
    w = x1 - x0
    gy0, gy1 = L.LODGE_GLASS[0] - p.y, L.LODGE_GLASS[1] - p.y
    # roof fascia with the sign
    lay.rect(0, 0, w, 7, 'D', 2.6, hgt=0.7, flat=True)
    lay.rect(0, 0, w, 1, 'D', 4.6, hgt=0.75, flat=True)
    lay.rect(0, 6, w, 1, 'D', 1.0, hgt=0.6, flat=True)
    # distinct Ö (pixfont_umlauts, round 9): the dots take the row above the cap line, so the plate reaches the
    # fascia's top edge there; the letters keep their rows 1-5
    m = kit.text_mask('PFÖRTNER', '35', overhang=True)
    up = m.shape[0] - 5
    lay.rect((w - m.shape[1]) // 2 - 3, 1 - up, m.shape[1] + 6, 5 + up, 'D', 1.2, hgt=0.72, flat=True)
    lay.put(m, (w - m.shape[1]) // 2, 1 - up, 'A', 4.4, flat=True)
    # glazing frame: posts + transom; the panes themselves stay transparent
    lay.rect(0, 7, 3, gy1 - 7, 'D', 3.0, hgt=0.6, flat=True)
    lay.rect(0, 7, 1, gy1 - 7, 'D', 4.6, hgt=0.62, flat=True)
    lay.rect(w - 3, 7, 3, gy1 - 7, 'D', 2.0, hgt=0.6, flat=True)
    lay.rect(3, 7, w - 6, 2, 'D', 2.4, hgt=0.6, flat=True)
    posts = [34, 70]
    for px_ in posts:
        lay.rect(px_, 7, 2, gy1 - 7, 'D', 2.8, hgt=0.6, flat=True)
        lay.px(px_, 8, 'D', 4.4)
    # the sliding hatch (middle bay) pushed open to the left: its sash now overlaps the left bay
    lay.rect(32, gy0 + 3, 2, gy1 - gy0 - 3, 'D', 3.6, hgt=0.6, flat=True)        # sash stile (open)
    lay.rect(3, gy0 + 3, 31, 1, 'D', 2.4, hgt=0.55, flat=True)                   # sash top rail
    lay.rect(3, gy1 - 2, 31, 1, 'D', 2.4, hgt=0.55, flat=True)
    # glass glints (diagonal reflections) on the two closed bays
    for gx0 in (6, 76):
        for k in range(9):
            lay.px(gx0 + k, gy0 + 16 - k, 'W', 7.0, hgt=0.3)
            lay.px(gx0 + 4 + k, gy0 + 22 - k, 'W', 6.0, hgt=0.3)
    # counter sill (deep ledge) + the visitors' book and a pen on a chain
    sy = gy1
    lay.rect(-0, sy, w, 3, 'D', 4.6, hgt=0.8, flat=True)
    lay.rect(0, sy, w, 1, 'D', 6.0, hgt=0.85, flat=True)
    lay.rect(0, sy + 3, w, 1, 'D', 1.2, hgt=0.4, flat=True)
    lay.poly([(40, sy), (50, sy - 1), (60, sy), (60, sy + 1), (40, sy + 1)], 'P', 5.6, hgt=0.9)
    lay.line(50, sy - 1, 50, sy + 1, 'P', 3.4)
    for k in range(3):
        lay.hline(42 + (k % 2), sy, 6, 'I', 2.6, flat=True)
    lay.line(61, sy, 64, sy - 1, 'I', 1.4)
    lay.line(64, sy - 1, 66, sy + 2, 'K', 3.0)
    # bell push on the sill (right of the hatch)
    lay.rect(73, sy - 2, 4, 2, 'A', 3.4, hgt=0.9, flat=True)
    lay.px(74, sy - 3, 'P', 6.0)
    # the porter's ashtray (a smoke curl actor rises from it) on the sill in front of the right bay
    lay.rect(86, sy - 2, 8, 2, 'K', 3.0, hgt=0.9, flat=True)
    lay.rect(86, sy - 2, 8, 1, 'K', 4.6, hgt=0.92, flat=True)
    lay.rect(89, sy - 3, 4, 1, 'P', 5.4, hgt=0.95, flat=True)                     # the cigarette
    lay.px(93, sy - 3, 'A', 6.0, emis=True)                                         # glowing tip
    # panelled lower front
    lay.rect(1, sy + 4, w - 2, base - p.y - sy - 4, 'D', 2.4, hgt=0.4, flat=True)
    for k in range(3):
        bx = 4 + k * 33
        bw = 29
        lay.rect(bx, sy + 7, bw, base - p.y - sy - 13, 'D', 2.0, hgt=0.3, flat=True)
        lay.rect(bx + 2, sy + 9, bw - 4, base - p.y - sy - 17, 'D', 3.0, hgt=0.45, flat=True)
        lay.rect(bx + 2, sy + 9, bw - 4, 1, 'D', 4.0, hgt=0.5, flat=True)
        lay.rect(bx + 2, base - p.y - 9, bw - 4, 1, 'D', 1.4, hgt=0.35, flat=True)
    lay.rect(1, base - p.y - 4, w - 2, 4, 'D', 1.2, hgt=0.3, flat=True)         # kick plate
    lay.rect(1, base - p.y - 4, w - 2, 1, 'D', 2.6, hgt=0.35, flat=True)
    # a notice taped to the glass: 'BITTE KLINGELN' (pseudo text)
    lay.rect(86, gy1 - 12, 11, 9, 'P', 5.6, hgt=0.35, flat=True)
    lay.rect(86, gy1 - 12, 11, 1, 'P', 4.6, hgt=0.35, flat=True)
    _pseudo(lay, 87, gy1 - 9, 9, 3, 'I', 2.0, seed=671, gap=2)
    return p


def hall_bench(Prop):
    p = Prop('hall_bench', 396, 291, 46, 24, 'waiting bench under the chronicle photos: briefcase, gloves')
    lay = p.lay
    for k in range(3):
        lay.rect(2, 1 + k * 3, 42, 2, 'D', 3.2, hgt=0.5, flat=True)
        lay.rect(2, 1 + k * 3, 42, 1, 'D', 4.4, hgt=0.55, flat=True)
    lay.rect(2, 11, 42, 3, 'D', 3.8, hgt=0.6, flat=True)
    lay.rect(2, 11, 42, 1, 'D', 5.2, hgt=0.65, flat=True)
    lay.rect(2, 14, 42, 1, 'D', 1.4, hgt=0.3, flat=True)
    for x in (4, 40):
        lay.rect(x, 0, 2, 24, 'W', 2.2, hgt=0.6, flat=True)
        lay.rect(x, 0, 1, 24, 'W', 4.0, hgt=0.65, flat=True)
        lay.rect(x - 1, 22, 4, 2, 'W', 2.0, hgt=0.5, flat=True)
    # a visitor's briefcase (leather) and a pair of gloves left on the seat
    lay.rect(9, 4, 12, 8, 'D', 2.6, hgt=0.7, flat=True)
    lay.rect(9, 4, 12, 1, 'D', 4.0, hgt=0.75, flat=True)
    lay.rect(13, 2, 4, 2, 'D', 1.6, hgt=0.75, flat=True)
    lay.px(14, 7, 'A', 4.6)
    lay.rect(28, 9, 6, 2, 'I', 2.0, hgt=0.7, flat=True)
    lay.rect(29, 8, 4, 1, 'I', 1.6, hgt=0.72, flat=True)
    return p


def umbrella_stand(Prop):
    p = Prop('umbrella_stand', 96, 292, 10, 26, 'umbrella stand by the door, two umbrellas, a puddle of melt water')
    lay = p.lay
    lay.rect(1, 12, 8, 13, 'K', 2.6, hgt=0.6, flat=True)
    lay.rect(1, 12, 1, 13, 'K', 4.4, hgt=0.62, flat=True)
    lay.rect(1, 12, 8, 1, 'K', 5.0, hgt=0.65, flat=True)
    lay.rect(1, 18, 8, 1, 'K', 1.6, hgt=0.5, flat=True)
    for (x, top, t) in ((3, 0, 1.6), (6, 3, 2.4)):
        lay.rect(x, top + 2, 2, 12 - top, 'I', t, hgt=0.6, flat=True)
        lay.polyline([(x, top + 2), (x, top), (x + 2, top)], 'D', 3.0)
    lay.rect(0, 25, 10, 1, 'W', 6.0, hgt=0.1, flat=True)                          # melt water
    return p
