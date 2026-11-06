"""gen_mg_morse -- original pixel art for the Karsk mini-game "Der Morsetaster" (TECHNICAL_ARCHITECTURE 12.8).

Run:  py -3 -P tools/pixelgen/gen_mg_morse.py        (Pillow + numpy, deterministic, no downloads)

Writes assets/ui/minigames/morse/ (UI art drawn 1:1 and STORED x3 nearest, like assets/ui/minigames/):
  morse_desk.png      the telegraph desk in the Karsk signal box: window onto the yard at dusk (wagon 24-311 under
                      snow), two-tone oil-paint wall, duty log, tea glass, Morse register (paper reel, clockwork,
                      inking wheel, tape table, tape hanging off the desk) -- the UI draws the ink marks on the tape
  morse_sounder.png   2 frames 40x30: sounder (Klopfer) armature up / down
  morse_key.png       2 frames 54x24: the Morse key (Taste) lever up / down
  morse_lamp.png      2 frames 20x20: call lamp with amber glass, off / on (the UI adds the glow)
  morse_table.png     the wall chart "АЗБУКА МОРЗЕ": pinned paper card with a 6 x 7 grid (letters drawn by the UI)
  morse_tape.png      48x6 tileable strip of Morse tape (fibres) for the strips glued onto the telegram form
  morse_layout.json   tape / lamp / sounder / key / table grid positions in ART px (x1) for the script
  find_telegram.png   1:1 close-up for the find (DiscoveryView, <= 320x200): the telegram form with the glued strips
Colours: data/palettes.json "karsk" (+ "archive" paper and ink). No regime insignia anywhere (12.4).
"""
from __future__ import annotations

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mg_r7_kb_lib import (F35, F57, ROOT, Canvas, P, bayer, draw_text, draw_text_centered, hx, mix, rng,  # noqa: E402
                          save_1x, save_json, save_x3, text_width)

OUT = os.path.join(ROOT, 'assets', 'ui', 'minigames', 'morse')


def K(ramp, i, a=255):
    return P('karsk', ramp, i, a)


def A(ramp, i, a=255):
    return P('archive', ramp, i, a)


# Russian Morse (mirrored in scripts/ui/minigames/morse_logic.gd TABLE; display order of the wall chart)
MORSE = [
    ('А', '.-'), ('Б', '-...'), ('В', '.--'), ('Г', '--.'), ('Д', '-..'), ('Е', '.'),
    ('Ж', '...-'), ('З', '--..'), ('И', '..'), ('Й', '.---'), ('К', '-.-'), ('Л', '.-..'),
    ('М', '--'), ('Н', '-.'), ('О', '---'), ('П', '.--.'), ('Р', '.-.'), ('С', '...'),
    ('Т', '-'), ('У', '..-'), ('Ф', '..-.'), ('Х', '....'), ('Ц', '-.-.'), ('Ч', '---.'),
    ('Ш', '----'), ('Щ', '--.-'), ('Ъ', '--.--'), ('Ы', '-.--'), ('Ь', '-..-'), ('Э', '..-..'),
    ('Ю', '..--'), ('Я', '.-.-'), ('1', '.----'), ('2', '..---'), ('3', '...--'), ('4', '....-'),
    ('5', '.....'), ('6', '-....'), ('7', '--...'), ('8', '---..'), ('9', '----.'), ('0', '-----'),
]
CODE = dict(MORSE)

DESK_W, DESK_H = 300, 144
WALL_H = 57                        # back edge of the desk
TAPE_Y0, TAPE_Y1 = 52, 55          # tape strip on the register (UI draws the marks here)
TAPE_HEAD = 129                    # print point (inking wheel); marks run to the right
TAPE_END = 179
SOUNDER_AT = (190, 36)
KEY_AT = (238, 94)
LAMP_AT = (262, 5)
FORM_RECT = (8, 80, 232, 142)      # where the telegram form lies on the desk (drawn by the UI)
TABLE_W, TABLE_H = 222, 144
TABLE_GRID = (6, 13, 30, 20)       # x0, y0, cell w, cell h (7 x 6 cells)


# ================================================================================ desk
def window(c: Canvas, r):
    wx0, wy0, wx1, wy1 = 7, 4, 63, 42
    sky = [K('night', 3), K('teal', 1), K('teal', 2), K('sage', 1)]
    c.vgrad(wx0, wy0, wx1, wy0 + 22, sky)
    # far city silhouettes, a few lit windows, the grain elevator
    for bx, bw, bh in ((8, 9, 6), (17, 6, 9), (24, 12, 4), (38, 7, 12), (46, 10, 7), (57, 6, 9)):
        c.rect(bx, wy0 + 22 - bh, bx + bw, wy0 + 23, K('night', 2))
    for wx in (19, 40, 42, 49):
        c.px(wx, wy0 + 17, K('copper', 3))
    # snowy ground, rails converging
    c.rect(wx0, wy0 + 23, wx1, wy1, K('snow', 0))
    for y in range(wy0 + 23, wy1):
        for x in range(wx0, wx1):
            if bayer(x, y) < 0.18:
                c.px(x, y, K('snow', 1))
    for k in range(3):
        y = wy0 + 27 + k * 4
        c.hline(wx0, wx1, y, K('stone', 1))
        c.hline(wx0, wx1, y + 1, K('stone', 3) if k else K('stone', 2))
    # wagon 24-311 on the siding, snow on its roof
    c.rect(27, wy0 + 18, 52, wy0 + 28, K('rust', 1))
    c.rect(27, wy0 + 17, 52, wy0 + 18, K('snow', 3))
    c.vline(39, wy0 + 19, wy0 + 28, K('rust', 0))
    c.rect(29, wy0 + 28, 32, wy0 + 30, K('night', 0))
    c.rect(47, wy0 + 28, 50, wy0 + 30, K('night', 0))
    for x in (33, 34, 36):
        c.px(x, wy0 + 22, K('snow', 2))
    # lamp post with a warm pool of light
    c.vline(14, wy0 + 6, wy0 + 31, K('night', 1))
    c.hline(12, 17, wy0 + 6, K('night', 1))
    c.px(15, wy0 + 7, K('copper', 4))
    c.glow(15, wy0 + 9, 12, K('copper', 3), 0.55)
    for i in range(34):
        x = int(r.integers(wx0, wx1))
        y = int(r.integers(wy0, wy1))
        c.px(x, y, K('snow', 4 if r.random() < 0.4 else 3))
    # frame, mullion, transom, frost in the corners, inner sill
    frame = [K('sky', 1), K('sky', 3), K('sky', 4)]
    c.frame(wx0 - 3, wy0 - 3, wx1 + 3, wy1 + 3, K('night', 2))
    c.rect(wx0 - 2, wy0 - 2, wx1 + 2, wy0, frame[1])
    c.rect(wx0 - 2, wy0, wx0, wy1, frame[1])
    c.rect(wx1, wy0, wx1 + 2, wy1, frame[0])
    c.rect((wx0 + wx1) // 2 - 1, wy0, (wx0 + wx1) // 2 + 1, wy1, frame[1])
    c.rect(wx0, wy0 + 14, wx1, wy0 + 16, frame[1])
    for cx, cy in ((wx0, wy0), (wx1 - 1, wy0), (wx0, wy1 - 1), (wx1 - 1, wy1 - 1), (35, wy0 + 16), (33, wy0 + 16)):
        for i in range(24):
            dx = int(r.integers(0, 7))
            dy = int(r.integers(0, 6))
            sx = 1 if cx < 35 else -1
            sy = 1 if cy < 24 else -1
            if dx + dy < 7:
                c.px(cx + sx * dx, cy + sy * dy, K('snow', 4) if r.random() < 0.5 else K('snow', 3))
    c.rect(wx0 - 4, wy1 + 2, wx1 + 4, wy1 + 5, frame[2])
    c.hline(wx0 - 4, wx1 + 4, wy1 + 5, K('teal', 0))


def desk():
    c = Canvas(DESK_W, DESK_H, K('night', 1))
    r = rng('morse_desk')
    # ---- wall: whitewash above, oil-painted teal panel below (the usual two-tone of a Soviet service room)
    wash = [K('sage', 1), K('sage', 2), K('sage', 3)]
    for y in range(0, 33):
        for x in range(0, DESK_W):
            v = 0.35 + 0.25 * math.sin(x * 0.07 + y * 0.05) + r.normal(0, 0.08)
            light = max(0.0, 1.0 - math.hypot(x - 158, (y + 6) * 1.4) / 150.0)   # warm bulb above the desk
            k = 0 if v + light * 0.9 < 0.55 else (1 if v + light * 0.9 < 1.05 else 2)
            c.px(x, y, wash[k])
    c.hline(0, DESK_W, 33, K('teal', 4))
    c.hline(0, DESK_W, 34, K('night', 3))
    panel = [K('teal', 1), K('teal', 2), K('teal', 3)]
    for y in range(35, WALL_H):
        for x in range(0, DESK_W):
            light = max(0.0, 1.0 - math.hypot(x - 158, y - 20) / 140.0)
            t = 0.25 + light * 0.75 + 0.06 * math.sin(x * 0.9 + y * 0.3)
            k = 0 if t < 0.45 else (1 if t < 0.85 else 2)
            if bayer(x, y) < (t * 1.5) % 1.0 * 0.3:
                k = min(2, k + 1)
            c.px(x, y, panel[k])
    for i in range(14):
        x = int(r.integers(70, 298))
        y = int(r.integers(36, WALL_H - 2))
        c.px(x, y, K('teal', 0))
        if r.random() < 0.5:
            c.px(x, y + 1, K('teal', 0))
    window(c, r)
    # ---- wall details: wiring to a junction box, the call-lamp plate, a calendar
    c.rect(228, 14, 240, 24, K('stone', 2))
    c.frame(228, 14, 240, 24, K('night', 1))
    c.px(231, 17, K('stone', 4))
    c.px(237, 21, K('stone', 4))
    c.vline(233, 0, 14, K('night', 0))
    c.vline(235, 0, 14, K('night', 1))
    for i in range(48):
        x = 228 - i
        y = 22 + int(round(3 * math.sin(i / 47 * math.pi)))
        c.px(x, y, K('night', 0))
    c.vline(181, 22, 37, K('night', 0))
    c.vline(208, 24, 38, K('night', 0))
    c.rect(254, 26, 292, 35, A('paper', 3))
    c.frame(254, 26, 292, 35, K('stone', 1))
    draw_text_centered(c, 273, 27, 'ВЫЗОВ', A('ink', 0), F57, spacing=2)
    c.rect(200, 4, 222, 22, A('paper', 4))
    c.frame(200, 4, 222, 22, A('paper', 1))
    c.rect(200, 4, 222, 8, A('ink', 3))
    draw_text_centered(c, 211, 11, '17', A('ink', 0), F57)
    c.px(211, 3, K('stone', 1))
    # ---- desk: wooden back rim, then patterned oilcloth seen from the chair
    c.rect(0, WALL_H, DESK_W, WALL_H + 2, K('wood', 3))
    c.hline(0, DESK_W, WALL_H, K('wood', 4))
    cloth = [K('teal', 0), K('teal', 1), K('teal', 2), K('teal', 3)]
    for y in range(WALL_H + 2, DESK_H):
        for x in range(0, DESK_W):
            light = max(0.0, 1.0 - math.hypot(x - 150, (y - 70) * 1.3) / 190.0)
            depth = (y - WALL_H) / (DESK_H - WALL_H)          # nearer = a little lighter
            t = 0.15 + light * 0.95 + depth * 0.25
            dia = ((x + y) // 6 + (x - y) // 6) % 2 == 0      # faint diamond print of the oilcloth
            if dia:
                t += 0.07
            f = t * 2.2
            k = int(f)
            if bayer(x, y) < (f - k):
                k += 1
            c.px(x, y, cloth[max(0, min(3, k))])
    c.hline(0, DESK_W, WALL_H + 2, K('night', 2))
    # ---- duty log (open book) at the back left, tea glass beside it
    bx0, by0 = 8, 61
    c.rect(bx0 - 1, by0 + 1, bx0 + 50, by0 + 17, K('night', 1))
    c.rect(bx0, by0, bx0 + 48, by0 + 15, A('paper', 3))
    c.rect(bx0 + 24, by0, bx0 + 25, by0 + 15, A('paper', 1))
    for i in range(5):
        y = by0 + 2 + i * 3
        c.hline(bx0 + 2, bx0 + 22, y, A('blue', 4))
        c.hline(bx0 + 27, bx0 + 46, y, A('blue', 4))
    for i in range(4):
        y = by0 + 1 + i * 3
        for x in range(bx0 + 3, bx0 + 3 + int(r.integers(10, 19))):
            if r.random() < 0.7:
                c.px(x, y, K('stone', 2))
    for i in range(2):
        y = by0 + 1 + i * 3
        for x in range(bx0 + 28, bx0 + 28 + int(r.integers(8, 16))):
            if r.random() < 0.7:
                c.px(x, y, K('stone', 2))
    gx = 62
    c.rect(gx, 46, gx + 10, 48, K('snow', 3))
    for y in range(48, 66):
        for x in range(gx, gx + 10):
            col = K('rust', 3) if y > 50 else K('snow', 2)
            if x == gx or x == gx + 9:
                col = K('snow', 3)
            if y >= 57:
                col = K('stone', 3) if (x - gx) % 3 else K('stone', 4)       # plain metal holder
                if x == gx:
                    col = K('stone', 5)
            c.px(x, y, col)
    c.rect(gx + 10, 54, gx + 13, 56, K('stone', 3))
    c.rect(gx + 12, 54, gx + 13, 63, K('stone', 3))
    c.rect(gx + 10, 62, gx + 13, 64, K('stone', 3))
    c.rect(gx - 1, 66, gx + 11, 67, K('night', 1))
    c.px(gx + 2, 51, K('rust', 5))
    c.px(gx + 3, 52, K('rust', 4))
    c.line(gx + 7, 42, gx + 7, 51, K('stone', 4))
    # ---- Morse register (inker), cable from the key to the sounder, pencil
    reg(c)
    for i in range(40):
        x = 246 - int(i * 0.9)
        y = 112 - int(i * 1.2)
        if y > 64:
            c.px(x, y, K('night', 0))
    c.line(246, 130, 276, 126, K('copper', 2))
    c.line(246, 131, 276, 127, K('copper', 1))
    c.px(245, 131, K('night', 0))
    c.px(277, 126, K('rust', 3))
    # warm light falling on everything from the bulb above
    c.glow(158, 60, 78, K('copper', 3), 0.2)
    return c


def reg(c: Canvas):
    dy = -4
    # wooden base board + iron plate
    c.rect(80, 64 + dy, 184, 71 + dy, K('wood', 2))
    c.hline(80, 184, 64 + dy, K('wood', 4))
    c.hline(80, 184, 70 + dy, K('wood', 0))
    c.rect(80, 71 + dy, 184, 72 + dy, K('night', 0))
    c.rect(84, 60 + dy, 180, 65 + dy, K('stone', 1))
    c.hline(84, 180, 60 + dy, K('stone', 4))
    c.hline(84, 180, 64 + dy, K('night', 1))
    for sx in (87, 177):
        c.px(sx, 62 + dy, K('stone', 5))
    # reel bracket and paper reel
    c.rect(94, 46 + dy, 98, 60 + dy, K('stone', 2))
    c.vline(94, 46 + dy, 60 + dy, K('stone', 4))
    cx, cy = 96, 40 + dy
    for y in range(cy - 13, cy + 14):
        for x in range(cx - 13, cx + 14):
            d = math.hypot(x - cx, y - cy)
            if d > 12.5:
                continue
            if d > 11.5:
                col = K('snow', 0)
            elif d > 4.5:
                ring = int(d * 1.6) % 3
                col = (K('snow', 3), K('snow', 2), K('snow', 3))[ring]
                if x - cx + y - cy < -6:
                    col = K('snow', 4)
            elif d > 3.0:
                col = K('stone', 2)
            else:
                col = K('stone', 4) if d < 1.5 else K('stone', 1)
            c.px(x, y, col)
    for ang in (0.3, 2.4, 4.5):
        for k in range(2, 5):
            c.px(cx + math.cos(ang) * k, cy + math.sin(ang) * k, K('night', 1))
    c.rect(96, 52 + dy, 110, 55 + dy, K('snow', 3))
    c.line(96, 52 + dy, 108, 55 + dy, K('snow', 2))
    # clockwork housing (black-green enamel, brass trim)
    hx0, hy0, hx1, hy1 = 106, 32 + dy, 152, 56 + dy
    c.rect(hx0, hy0, hx1, hy1, K('night', 2))
    c.rect(hx0, hy0, hx1, hy0 + 2, K('copper', 2))
    c.hline(hx0, hx1, hy0, K('copper', 3))
    c.rect(hx0, hy1 - 2, hx1, hy1, K('copper', 1))
    c.vline(hx0, hy0, hy1, K('teal', 2))
    c.vline(hx1 - 1, hy0, hy1, K('night', 0))
    for y in range(hy0 + 3, hy1 - 2):
        for x in range(hx0 + 1, hx1 - 1):
            if bayer(x, y) < 0.12 and x < hx0 + 18:
                c.px(x, y, K('teal', 1))
    c.rect(114, 38 + dy, 144, 44 + dy, K('copper', 2))
    c.frame(114, 38 + dy, 144, 44 + dy, K('copper', 0))
    c.hline(116, 142, 40 + dy, K('copper', 4))
    c.hline(117, 141, 42 + dy, K('copper', 1))
    for sx in (109, 149):
        c.px(sx, hy0 + 4, K('copper', 3))
        c.px(sx, hy1 - 4, K('copper', 3))
    c.rect(152, 42 + dy, 156, 45 + dy, K('copper', 2))
    c.rect(155, 40 + dy, 157, 50 + dy, K('copper', 3))
    c.rect(155, 49 + dy, 160, 51 + dy, K('night', 1))
    # rollers and the inking wheel with its ink disc
    for rx in (112, 160):
        c.disc(rx, 54 + dy, 2.2, K('stone', 3))
        c.px(rx - 1, 53 + dy, K('stone', 5))
    c.disc(126, 52 + dy, 3.2, K('night', 1))
    c.disc(126, 52 + dy, 2.0, A('blue', 1))
    c.px(125, 51 + dy, A('blue', 3))
    # electromagnet (two coils) and the armature lever to the wheel
    for coil_x in (160, 168):
        c.rect(coil_x, 40 + dy, coil_x + 6, 52 + dy, K('rust', 4))
        for y in range(40 + dy, 52 + dy, 2):
            c.hline(coil_x, coil_x + 6, y, K('rust', 3))
        c.vline(coil_x, 40 + dy, 52 + dy, K('rust', 5))
        c.rect(coil_x - 1, 38 + dy, coil_x + 7, 40 + dy, K('stone', 2))
    c.line(128, 49 + dy, 160, 37 + dy, K('stone', 3))
    c.line(128, 50 + dy, 160, 38 + dy, K('stone', 1))
    c.rect(158, 35 + dy, 176, 38 + dy, K('stone', 2))
    c.hline(158, 176, 35 + dy, K('stone', 4))
    # tape table: the strip the UI prints on
    c.rect(108, TAPE_Y0 - 1, TAPE_END + 1, TAPE_Y1 + 1, K('stone', 2))
    for x in range(108, TAPE_END + 1):
        c.rect(x, TAPE_Y0, x + 1, TAPE_Y1, K('snow', 4) if bayer(x, 0) < 0.8 else K('snow', 3))
    c.hline(108, TAPE_END + 1, TAPE_Y1, K('snow', 1))
    # the printed tape spills over the edge of the register onto the desk in loose loops
    for i in range(70):
        u = i / 69.0
        x = TAPE_END + 2 + 10 * u + 5 * math.sin(u * 7.0)
        y = TAPE_Y0 + 4 + 22 * u + 3 * math.cos(u * 7.0)
        c.rect(int(x), int(y), int(x) + 3, int(y) + 1, K('snow', 3) if i % 9 else K('snow', 2))
        c.px(int(x) + 3, int(y), K('snow', 1))
        if i % 6 == 0:
            c.px(int(x) + 1, int(y), A('blue', 2))


# ================================================================================ sounder / key / lamp
def sounder():
    w, h = 40, 30
    sheet = Canvas(w * 2, h)
    for f in (0, 1):
        c = Canvas(w, h)
        c.rect(2, 22, 38, 29, K('wood', 2))
        c.hline(2, 38, 22, K('wood', 4))
        c.hline(2, 38, 28, K('wood', 0))
        # two coils on a yoke
        for x0 in (12, 21):
            c.rect(x0, 12, x0 + 7, 22, K('rust', 4))
            for y in range(12, 22, 2):
                c.hline(x0, x0 + 7, y, K('rust', 3))
            c.vline(x0, 12, 22, K('rust', 5))
        c.rect(10, 20, 30, 22, K('stone', 2))
        # pillar and stop screws
        c.rect(32, 6, 35, 22, K('copper', 2))
        c.vline(32, 6, 22, K('copper', 3))
        c.rect(31, 4, 36, 6, K('copper', 1))
        c.rect(31, 17, 36, 18, K('stone', 4))
        # pivot at the back, armature bar to the front
        c.disc(6, 9, 2.3, K('copper', 1))
        c.px(6, 9, K('copper', 4))
        y_front = 6 if f == 0 else 9
        c.line(6, 8, 34, y_front, K('copper', 3))
        c.line(6, 9, 34, y_front + 1, K('copper', 2))
        c.line(6, 10, 34, y_front + 2, K('copper', 0))
        c.rect(14, 10 if f == 0 else 11, 30, 12, K('stone', 3))     # iron armature plate
        c.outline(K('night', 0))
        sheet.paste(c, f * w, 0)
    save_x3(sheet, os.path.join(OUT, 'morse_sounder.png'))


def key():
    w, h = 54, 24
    sheet = Canvas(w * 2, h)
    for f in (0, 1):
        c = Canvas(w, h)
        c.rect(2, 16, 52, 23, K('wood', 3))
        c.hline(2, 52, 16, K('wood', 4))
        c.hline(2, 52, 22, K('wood', 0))
        c.rect(6, 14, 50, 17, K('copper', 1))
        c.hline(6, 50, 14, K('copper', 3))
        # pivot block, spring, contact
        c.rect(8, 9, 14, 15, K('copper', 2))
        c.vline(8, 9, 15, K('copper', 3))
        c.disc(11, 9, 2.0, K('copper', 4))
        for y in range(10, 15):
            c.px(28 + (y % 2), y, K('stone', 4))
        c.rect(38, 12, 42, 14, K('stone', 5))
        # lever + bakelite knob
        y1 = 5 if f == 0 else 8
        c.line(11, 8, 44, y1 + 2, K('copper', 3))
        c.line(11, 9, 44, y1 + 3, K('copper', 1))
        kx = 44
        c.rect(kx - 3, y1 - 3, kx + 5, y1 + 3, K('night', 1))
        c.rect(kx - 4, y1 - 2, kx + 6, y1 + 2, K('night', 1))
        c.hline(kx - 2, kx + 4, y1 - 3, K('stone', 2))
        c.px(kx - 2, y1 - 2, K('stone', 4))
        c.outline(K('night', 0))
        sheet.paste(c, f * w, 0)
    save_x3(sheet, os.path.join(OUT, 'morse_key.png'))


def lamp():
    n = 20
    sheet = Canvas(n * 2, n)
    for f in (0, 1):
        c = Canvas(n, n)
        c.disc(9.5, 9.5, 8.6, K('stone', 1))
        c.disc(9.5, 9.5, 7.6, K('stone', 3))
        c.disc(9.0, 9.0, 6.0, K('night', 1))
        glass = [K('rust', 1), K('rust', 2), K('copper', 0)] if f == 0 else [K('copper', 2), K('copper', 3), K('copper', 4)]
        for y in range(n):
            for x in range(n):
                d = math.hypot(x - 9.5, y - 9.5)
                if d <= 5.2:
                    k = 2 if d < 2.0 else (1 if d < 3.8 else 0)
                    c.px(x, y, glass[k])
        c.px(7, 7, K('snow', 4) if f else K('rust', 4))
        c.px(8, 7, K('snow', 3) if f else K('rust', 3))
        for a in range(0, 360, 45):
            c.px(9.5 + math.cos(math.radians(a)) * 7.0, 9.5 + math.sin(math.radians(a)) * 7.0, K('stone', 5))
        c.outline(K('night', 0))
        sheet.paste(c, f * n, 0)
    save_x3(sheet, os.path.join(OUT, 'morse_lamp.png'))


# ================================================================================ wall chart
def table():
    c = Canvas(TABLE_W, TABLE_H)
    r = rng('morse_table')
    paper = [A('paper', i) for i in range(6)]
    for y in range(TABLE_H):
        for x in range(TABLE_W):
            v = 4.25 + 0.45 * math.sin(x * 0.045 + y * 0.03) + 0.2 * math.sin(y * 0.21 - x * 0.02) + r.normal(0, 0.07)
            edge = min(x, y, TABLE_W - 1 - x, TABLE_H - 1 - y)
            if edge < 3:
                v -= 1.2 - edge * 0.3
            k = int(max(2, min(5, round(v))))
            c.px(x, y, paper[k])
    # fold crease and a tea ring in the bottom margin
    for y in range(TABLE_H):
        if bayer(111, y) < 0.7:
            c.px(111, y, paper[3])
        c.px(112, y, paper[5])
    for a in range(0, 360, 4):
        rr = 8 + (a % 12 == 0)
        c.px(204 + math.cos(math.radians(a)) * rr, 141 + math.sin(math.radians(a)) * rr * 0.8, A('amber', 1, 160))
    # header
    ink = A('ink', 0)
    draw_text_centered(c, TABLE_W // 2, 2, 'АЗБУКА МОРЗЕ', ink, F57, spacing=2, bold=True)
    c.hline(36, TABLE_W - 36, 10, A('ink', 2))
    # grid (letters and patterns are drawn by the UI)
    x0, y0, cw, ch = TABLE_GRID
    for i in range(6):
        for j in range(7):
            x, y = x0 + j * cw, y0 + i * ch
            c.frame(x, y, x + cw + 1, y + ch + 1, A('paper', 1))
    c.frame(x0 - 1, y0 - 1, x0 + 7 * cw + 2, y0 + 6 * ch + 2, A('ink', 1))
    # drawing pins
    for px_, py_ in ((7, 5), (TABLE_W - 8, 5)):
        c.disc(px_, py_, 3.1, A('ink', 3))
        c.disc(px_ - 0.5, py_ - 0.5, 1.5, A('ink', 2))
        c.px(px_ - 1, py_ - 1, A('paper', 5))
    # a pencil note in the margin (who checked the chart)
    draw_text(c, 8, TABLE_H - 8, 'ПРОВ. 1963', A('paper', 1), F57)
    save_x3(c, os.path.join(OUT, 'morse_table.png'))


def tape():
    c = Canvas(48, 6)
    r = rng('morse_tape')
    for y in range(6):
        for x in range(48):
            k = 4 if r.random() < 0.75 else 3
            if y == 0 or y == 5:
                k = 2
            c.px(x, y, K('snow', k))
    for i in range(10):
        x = int(r.integers(0, 47))
        y = int(r.integers(1, 5))
        c.px(x, y, K('snow', 1))
        c.px(x + 1, y, K('snow', 2))
    save_x3(c, os.path.join(OUT, 'morse_tape.png'))


# ================================================================================ close-up for the find (1:1)
def marks(c: Canvas, x: int, y: int, word: str, ink, u: int = 1) -> int:
    """draws the Morse marks of `word` on a tape at (x, y); returns the end x"""
    for li, ch in enumerate(word):
        code = CODE[ch]
        for ei, e in enumerate(code):
            ln = u if e == '.' else 3 * u
            c.rect(x, y, x + ln, y + 2, ink)
            x += ln + u
        x += 2 * u
    return x


def find_telegram():
    W, H = 300, 190
    c = Canvas(W, H, K('teal', 0))
    r = rng('find_telegram')
    # oilcloth desk with lamp light
    for y in range(H):
        for x in range(W):
            light = max(0.0, 1.0 - math.hypot(x - 150, y - 80) / 190.0)
            t = light + 0.06 * math.sin(x * 0.4) * math.sin(y * 0.5)
            k = 0 if t < 0.35 else (1 if t < 0.7 else 2)
            c.px(x, y, (K('teal', 0), K('teal', 1), K('teal', 2))[k])
    # the telegram form
    fx0, fy0, fx1, fy1 = 22, 10, 252, 182
    c.rect(fx0 + 3, fy0 + 3, fx1 + 3, fy1 + 3, K('night', 1))
    paper = [A('paper', i) for i in range(6)]
    for y in range(fy0, fy1):
        for x in range(fx0, fx1):
            v = 4.3 + 0.4 * math.sin(x * 0.07 + y * 0.04) + r.normal(0, 0.15)
            c.px(x, y, paper[int(max(3, min(5, round(v))))])
    red = A('ink', 2)
    # printed head (red-brown print): ТЕЛЕГРАММА, form fields
    draw_text_centered(c, (fx0 + fx1) // 2, fy0 + 5, 'ТЕЛЕГРАММА', red, F57, spacing=2, bold=True)
    c.hline(fx0 + 8, fx1 - 8, fy0 + 15, red)
    draw_text(c, fx0 + 8, fy0 + 19, '№ 118', red, F57)
    draw_text(c, fx0 + 60, fy0 + 19, 'ОТ ДНЦ', red, F57)
    draw_text(c, fx0 + 120, fy0 + 19, 'КОМУ ДСП КАРСК', red, F57)
    c.hline(fx0 + 8, fx1 - 8, fy0 + 29, A('paper', 2))
    pencil = K('stone', 1)
    # line 1 in pencil (taken down by the duty officer before he went for tea)
    draw_text(c, fx0 + 10, fy0 + 36, 'П 2417 ОПОЗД 40 МИН', pencil, F57, spacing=2)
    # glued strip: ВАГ 24311 (routine, written underneath by Alexei)
    tape_col = K('snow', 4)
    ink = A('blue', 1)
    y = fy0 + 54
    c.rect(fx0 + 8, y - 3, fx0 + 214, y + 5, tape_col)
    c.hline(fx0 + 8, fx0 + 214, y + 5, K('snow', 1))
    xe = marks(c, fx0 + 12, y, 'ВАГ', ink)
    marks(c, xe + 6, y, '24311', ink)
    draw_text(c, fx0 + 12, y + 9, 'ВАГ 24311', pencil, F57, spacing=2)
    # glued strip: НЕ ВЗВЕШИВАТЬ -- the words he had to read letter by letter
    y = fy0 + 86
    c.rect(fx0 + 8, y - 3, fx0 + 222, y + 5, tape_col)
    c.hline(fx0 + 8, fx0 + 222, y + 5, K('snow', 1))
    xe = marks(c, fx0 + 12, y, 'НЕ', ink)
    marks(c, xe + 6, y, 'ВЗВЕШИВАТЬ', ink)
    xe = draw_text(c, fx0 + 12, y + 9, 'НЕ ВЗВЕШИВАТЬ', K('night', 1), F57, spacing=2)
    c.hline(fx0 + 11, xe + 1, y + 18, pencil)
    c.hline(fx0 + 13, xe - 2, y + 20, pencil)
    # received by: ПР and a pencil signature
    draw_text(c, fx0 + 10, fy1 - 30, 'ПРИНЯЛ:', red, F57)
    draw_text(c, fx0 + 58, fy1 - 30, 'ПР', K('night', 1), F57, spacing=2)
    sx, sy = fx0 + 90, fy1 - 26
    for i in range(46):
        c.px(sx + i, sy + int(round(2.2 * math.sin(i * 0.9) + (i % 7 == 0) * -2)), pencil)
    c.hline(fx0 + 8, fx1 - 8, fy1 - 16, A('paper', 2))
    draw_text(c, fx0 + 10, fy1 - 12, '17.01.64  16.42', red, F57)
    # receiving stamp of the station (violet, slightly faded): a plain frame with the station and the date
    vio = hx('#4B3A6B')
    sx0, sy0 = fx0 + 150, fy0 + 118
    c.frame(sx0, sy0, sx0 + 66, sy0 + 26, vio)
    c.frame(sx0 + 2, sy0 + 2, sx0 + 64, sy0 + 24, vio)
    draw_text_centered(c, sx0 + 33, sy0 + 5, 'СТ. КАРСК', vio, F57)
    draw_text_centered(c, sx0 + 33, sy0 + 15, '17 01 64', vio, F57)
    for i in range(70):
        x = sx0 + int(r.integers(0, 67))
        y2 = sy0 + int(r.integers(0, 27))
        if c.get(x, y2)[:3] == vio[:3]:
            c.px(x, y2, A('paper', 4))
    # glass of tea in a plain metal holder (podstakannik), at the right edge
    gx, gy = 266, 70
    for yy in range(gy, gy + 52):
        for xx in range(gx, gx + 18):
            if yy < gy + 3:
                col = K('snow', 4) if xx in (gx, gx + 17) or yy == gy else K('snow', 3)
            elif yy < gy + 8:
                col = K('snow', 2) if xx not in (gx, gx + 17) else K('snow', 4)
            else:
                col = (K('rust', 2), K('rust', 3))[1 if xx < gx + 7 else 0]
                if xx in (gx, gx + 17):
                    col = K('rust', 4)
            c.px(xx, yy, col)
    c.rect(gx + 3, gy + 10, gx + 5, gy + 30, K('rust', 5))
    hy0 = gy + 30
    for yy in range(hy0, gy + 54):
        for xx in range(gx - 1, gx + 19):
            lattice = (xx - gx) % 4 == 1 or (yy - hy0) in (0, 1, 21, 22)
            col = K('stone', 4) if lattice else K('stone', 2)
            if xx == gx - 1:
                col = K('stone', 5)
            c.px(xx, yy, col)
    c.rect(gx - 2, gy + 52, gx + 20, gy + 55, K('stone', 3))
    c.rect(gx + 19, hy0 + 2, gx + 24, hy0 + 4, K('stone', 4))
    c.rect(gx + 22, hy0 + 2, gx + 24, hy0 + 18, K('stone', 4))
    c.rect(gx + 19, hy0 + 16, gx + 24, hy0 + 18, K('stone', 4))
    c.line(gx + 12, gy - 10, gx + 9, gy + 22, K('stone', 5))      # spoon
    c.glow(gx + 8, gy + 12, 12, K('rust', 5), 0.35)
    c.line(150, 170, 236, 146, K('copper', 2))
    c.line(150, 171, 236, 147, K('copper', 1))
    c.line(150, 172, 236, 148, K('copper', 0))
    c.px(149, 172, K('night', 0))
    c.rect(236, 145, 240, 149, K('rust', 3))
    save_1x(c, os.path.join(OUT, 'find_telegram.png'))


def layout():
    save_json(os.path.join(OUT, 'morse_layout.json'), {
        '_doc': 'Morse mini-game layout in ART px (morse_*.png are stored x3). tape = strip on the register where '
                'the UI prints the marks (they appear at tape_head and run right to tape_end); sounder / key / lamp = '
                'top-left of their 2-frame sprites on morse_desk.png; form = where the telegram form lies on the desk; '
                'table_grid = x0, y0, cell w, cell h of the 7 x 6 chart cells on morse_table.png (display order = '
                'morse_logic.gd TABLE).',
        'desk_size': [DESK_W, DESK_H], 'tape': [TAPE_HEAD, TAPE_Y0, TAPE_END, TAPE_Y1], 'tape_head': TAPE_HEAD,
        'sounder': list(SOUNDER_AT), 'sounder_frame': [40, 30], 'key': list(KEY_AT), 'key_frame': [54, 24],
        'lamp': list(LAMP_AT), 'lamp_frame': [20, 20], 'form': list(FORM_RECT), 'table_size': [TABLE_W, TABLE_H],
        'table_grid': list(TABLE_GRID), 'table': [[ch, code] for ch, code in MORSE]})


def main():
    c = desk()
    save_x3(c, os.path.join(OUT, 'morse_desk.png'))
    sounder()
    key()
    lamp()
    table()
    tape()
    find_telegram()
    layout()
    print('gen_mg_morse: wrote', sorted(os.listdir(OUT)))


if __name__ == '__main__':
    main()
