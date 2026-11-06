"""gen_ui_c4p2 -- puzzle art of Chapter 4 part 2 „Stimmen unter Beton“ (documentation/C4P2_DESIGN.md §2.7, §10).

Owner: puzzle UI stream (round 10).  Two puzzles:

* pz_c4_halves „Die Hälften“ (objective c4g_solve_halves, scenes/ui/JoinPuzzle.tscn).  Card No. 0417 is painted
  WHOLE once -- one bilingual two-part form, German left, Russian right, the ruled lines running through, five
  irregular teeth on the cut and a round violet stamp „C-17“ printed across it (ring text ABGABE | ПРИЁМ, the
  centre C- | 17 split by the cut) -- and then cut along the toothed edge into the two halves.  So the halves fit
  by construction: tooth into notch, line into line, and the stamp closes into a circle only in the one pose.
  The German half is stored the way Konrad laid it into Ekdahl's guidebook: upside down.  The board is the table
  of the sand house in the Karsk depot under a hanging lamp: the open guidebook (pages 212/213, the German half
  lies on it at the start), Konrad's tracing of the Kordon room with the bench for fourteen, Lev's card box
  „С-17/45 ПРИНЯТЬ“ with the empty slot, a pocket watch at 19.05, Ekdahl's camera, a tin mug, a sieve and sand.
  Layout: assets/ui/documents/karsk_c4p2_halves.json -- verified here against data/v3/puzzles.json: only one
  rotation lets the marks face each other, exactly one pose joins every tooth and the stamp, it is the
  solution, and no other pose joins even a single tooth (the UI's count is never misleading).
* pz_c4_house „Haus 14“ (objective c4h_solve_house, scenes/ui/HousePuzzle.tscn).  Kolonnenstraße 14 seen from
  the courtyard on Tuesday night, in the plasters of the courtyard level: Vorderhaus, Seitenflügel and
  Hinterhaus as three columns, six storeys from the cellar to the drying lofts, the stairwells cut open (a
  dog-leg stair per storey, the steep cellar stairs), the cobbler's souterrain right of the back cellar under
  the Hinterhaus, which goes on right of its stairs (its board SCHUHMACHEREI / PIETSCH over the souterrain
  windows, as in the courtyard).  Every flat shows its windows -- who is awake: Lenz at his desk lamp with the
  radio, Herr Schulz walking the baby, Frau Grabowski in her coat at the cold stove, Ilse drawing at Hanna's
  table, Pohl's curtain, the Mertens family and the conductor's jacket, the lodge with Frau Kuhnert at her lamp
  and radio (the card box on the sill), Kuhnert in his hat under the passage lamp, the sealed No. 3, the
  Brettschneider bed empty (night shift), the Kühns' card game and their cat.  Two renderings: the overview
  (every room readable) and the 22.40 lights (L), plus window animation frames for the lights, the walking
  figures (five frames each: Ilse with her satchel, Konrad in his fedora), the shape-coded watcher marks (eye /
  lamp / cap), the stop mark and the success overlays (the candle in Pietsch's workshop, the red pencil ring).
  Layout: assets/ui/puzzle/c4p2_house.json -- verified here: the only simple path from s3 to ws that avoids
  the unsafe rooms is the solution of pz_c4_house, every room has at most one passage per arrow direction, the
  input driver's keys (↓ from s3 = Frau Pohl; R; ↑ → ↓×5 → = the solution) follow the layout's arrows, every
  room has a place on its floor with room for Konrad, and every passage a way along the floor or the flights.

Everything is drawn 1:1 and shown at x3 with nearest filtering.  Words the player must read are set in HD by
the UI from Loc keys (ui.c4p2.*); the painted characters are document type (the card, the book page, the box
label, the shop sign), in the 3x5 / 5x7 bitmap types of tools/pixelgen/env_veltrava_hall_kit.py (imported
read-only) with the distinct umlauts of tools/pixelgen/pixfont_umlauts.py, plus the few glyphs added below.  Nothing is sampled from outside the repository and nothing is
traced; all randomness uses fixed seeds (deterministic output).  World note: a fictional two-part registry
card, a fictional depot and a fictional Berlin tenement and its fictional households; no real persons.

Run:  py -3 -P tools/pixelgen/gen_ui_c4p2.py [--preview=DIR]
      --preview writes x2 contact sheets (≤ 1280 px wide) to DIR (outside the repo).
"""
from __future__ import annotations

import json
import math
import os
import sys

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import pg  # noqa: E402
import gen_ui_c4 as c4  # noqa: E402  (Canvas, dither, noise, bresenham -- read-only use)
import env_veltrava_hall_kit as hk  # noqa: E402  (bitmap types F35 / F57 -- read-only use)

ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))
PUZ = os.path.join(ROOT, 'assets', 'ui', 'puzzle')
DOCS = os.path.join(ROOT, 'assets', 'ui', 'documents')
DATE = '2026-11-06'
GENERATOR = 'tools/pixelgen/gen_ui_c4p2.py'

Canvas = c4.Canvas
C = c4.C
dither = c4.dither
noise = c4.noise
bresenham = c4.bresenham

# ----------------------------------------------------------------------------- palette
NIGHT, NAVY = '#04090D', '#0B1C24'
PAPER = ['#6E6A5C', '#8E8A78', '#B0AA93', '#CEC6AA', '#E6DEC2', '#F5EFDA']
INK, INK_B, BLUE_INK = '#1A1C2A', '#2E3248', '#2B3C50'
RED_D, RED, RED_L = '#7A2A26', '#A8382E', '#C8503C'
VIOLET = ['#2A2258', '#3C3280', '#5446A0', '#7060BC']
AMBER, AMBER_L = '#F0C487', '#FFE2A8'
WOOD = ['#21140C', '#2E1D12', '#3E2818', '#523520', '#68452A', '#7E5634']
WOOD_L = ['#3B2618', '#5A3A22', '#7A5232', '#96693F', '#B08550']
SAND = ['#6E5A36', '#9A8250', '#C2A86E', '#DCC48A']
BRASS = ['#3A2A10', '#6A4E1E', '#9A7A34', '#C8A65A', '#EED89A']
STEEL = ['#14161B', '#2A2D33', '#464A51', '#6C7077', '#9196A0', '#C4C8CE']
CLOTH = ['#10201F', '#18302E', '#244440', '#305A54']
ONION = ['#B9C6C8', '#D2DCDD', '#E6EEEE']
GRAPHITE = '#36342F'
PENCIL_BLUE = '#3C5A86'

# ----------------------------------------------------------------------------- bitmap types
import pixfont_umlauts as UML  # noqa: E402  (round 9: distinct Ä / Ö / Ü -- read-only use)

F35 = dict(hk.F35)
F35.update({
    'Щ': ['#.#.#.', '#.#.#.', '#.#.#.', '######', '.....#'],
    '№': ['#..#.##', '##.#.##', '#.##...', '#..#.##', '#..#...'],
    '*': ['...', '#.#', '.#.', '#.#', '...'],
    '–': ['...', '...', '###', '...', '...'],
    '·': ['.', '.', '#', '.', '.'],
    '?': ['##.', '..#', '.#.', '...', '.#.'],
    'Ø': ['###', '#.#', '#.#', '#.#', '###'],
    # round 10 review: letters that read as others at 1x.  A rounded 8 (the square one read as B), Д with a flat
    # roof and feet under the bar (the pointed one read as А), Л with its left leg kicked out (it read as П).
    '8': ['.#.', '#.#', '.#.', '#.#', '.#.'],
    'Д': ['.###.', '.#.#.', '.#.#.', '#####', '#...#'],
    'Л': ['.###', '.#.#', '.#.#', '.#.#', '#..#'],
})
# Distinct diacritics in the round-9 manner (tools/pixelgen/pixfont_umlauts.py): the dots / the ring take one row
# ABOVE the cap line, a blank row, then the letter one row shorter -- the dots never touch the letter.  tmask() and
# text() keep the cap line where the caller puts it and let these glyphs reach one row higher.
UML.install(F35, 5)
F35.update({
    'Å': ['.#.', '...', '.#.', '#.#', '###', '#.#'],
    'Ё': ['#.#', '...', '###', '##.', '#..', '###'],
})
F57 = dict(hk.F57)
F57.update({
    '0': ['.###.', '#...#', '#..##', '#.#.#', '##..#', '#...#', '.###.'],
    '4': ['...#.', '..##.', '.#.#.', '#..#.', '#####', '...#.', '...#.'],
    '7': ['#####', '....#', '...#.', '..#..', '..#..', '.#...', '.#...'],
    ' ': ['..', '..', '..', '..', '..', '..', '..'],
})


def overhang(s: str, font: dict | None = None) -> int:
    """Rows a string reaches ABOVE its cap line (the distinct diacritics); 0 for plain capitals."""
    font = F35 if font is None else font
    gh = len(font['A'])
    return max([0] + [len(font[ch]) - gh for ch in s.upper() if ch in font])


def tmask(s: str, font: dict | None = None, spacing: int = 1) -> np.ndarray:
    """One bool mask for a string in a bitmap type (variable glyph widths).  A string with a distinct diacritic
    (Ä Ö Ü Å Ё) gets `overhang` extra rows at the TOP; the cap line is then row `overhang`."""
    font = F35 if font is None else font
    gh = len(font['A'])
    glyphs = []
    for ch in s.upper():
        assert ch in font, 'missing glyph %r' % ch
        glyphs.append(font[ch])
    extra = overhang(s, font)
    if not glyphs:
        return np.zeros((gh, 0), bool)
    widths = [max(len(r) for r in g) for g in glyphs]
    w = sum(widths) + spacing * (len(glyphs) - 1)
    m = np.zeros((gh + extra, w), bool)
    x = 0
    for g, gw in zip(glyphs, widths):
        top = extra - (len(g) - gh)
        for yy, row in enumerate(g):
            for xx, c in enumerate(row):
                if c == '#':
                    m[top + yy, x + xx] = True
        x += gw + spacing
    return m


def text(cv: Canvas, s: str, x: int, y: int, col, font=None, a=1.0, spacing=1, align='left') -> int:
    """Paints a string with its CAP LINE at y (a distinct diacritic reaches the row above)."""
    m = tmask(s, font, spacing)
    if align == 'center':
        x = int(round(x - m.shape[1] / 2))
    elif align == 'right':
        x = x - m.shape[1]
    cv.blend(m, int(x), int(y) - overhang(s, font), C(col) if isinstance(col, str) else col, a)
    return m.shape[1]


def text_w(s: str, font=None, spacing=1) -> int:
    return int(tmask(s, font, spacing).shape[1])


def disc(r: float, cx: float | None = None, cy: float | None = None, size: int | None = None) -> np.ndarray:
    n = size if size is not None else int(math.ceil(r * 2 + 1))
    cx = (n - 1) / 2 if cx is None else cx
    cy = (n - 1) / 2 if cy is None else cy
    yy, xx = np.mgrid[0:n, 0:n].astype(np.float32)
    return np.hypot(xx - cx, yy - cy) <= r


def ring(r0: float, r1: float, n: int) -> np.ndarray:
    yy, xx = np.mgrid[0:n, 0:n].astype(np.float32)
    d = np.hypot(xx - (n - 1) / 2, yy - (n - 1) / 2)
    return (d >= r0) & (d <= r1)


def rim(alpha: np.ndarray) -> np.ndarray:
    """Pixels of an opaque region that touch a transparent neighbour (4-connected)."""
    a = alpha > 0
    p = np.pad(a, 1, constant_values=False)
    inner = p[1:-1, :-2] & p[1:-1, 2:] & p[:-2, 1:-1] & p[2:, 1:-1]
    return a & ~inner


def outline(cv: Canvas, col=INK, a=1.0):
    """1-px outline around the opaque pixels of a sprite (drawn outside the sprite)."""
    al = cv.c[..., 3] > 0
    p = np.pad(al, 1, constant_values=False)
    grown = p[1:-1, :-2] | p[1:-1, 2:] | p[:-2, 1:-1] | p[2:, 1:-1]
    m = grown & ~al
    cv.blend(m, 0, 0, C(col), a)


def light_bands(light: np.ndarray, steps: int = 7) -> np.ndarray:
    """Banded + ordered-dithered light field (pixel-art lighting instead of smooth gradients)."""
    h, w = light.shape
    return np.floor(light * steps + pg.bayer(w, h)) / steps


def multiply(cv: Canvas, f: np.ndarray, tint=(1.0, 1.0, 1.0)):
    rgb = cv.c[..., :3].astype(np.float32)
    rgb *= f[..., None] * np.array(tint, np.float32)[None, None, :]
    cv.c[..., :3] = np.clip(np.round(rgb), 0, 255).astype(np.uint8)


def sprite(rows: list, legend: dict) -> Canvas:
    h, w = len(rows), max(len(r) for r in rows)
    cv = Canvas(w, h)
    for y, row in enumerate(rows):
        for x, ch in enumerate(row):
            if ch in legend:
                cv.px(x, y, C(legend[ch]))
    return cv


# ============================================================================= THE HALVES (pz_c4_halves)
CELL = 16
HALF_CELLS = (7, 5)
CARD_W, CARD_H = 224, 80          # the whole card No. 0417 (art px); the cut runs at x = 112
CUT = 112
PAD = 6                           # px around the German half (teeth + the red C-17 tab)
# (centre row, half base) -> base 2h + 1 px.  No tooth comes near the stamp's centre (rows 37-43, „C-“ | „17“):
# the corner brackets (13 px) and the click marks of a joined tooth must never cover the „1“ on the seam.
TEETH = [(7, 3), (18, 4), (30, 3), (52, 4), (69, 3)]
STAMP_TEXT_ROWS = (37, 44)        # the centre „C-17“ (F57) on the card
TOOTH_D = 5
LINES_Y = [22, 34, 46, 58, 70]
STAMP_C = (112, 40)
STAMP_R = 24
TAB = (84, 105)                   # the red C-17 tab on the German half's top edge (card x)
BOARD_CELLS = (20, 14)
RU_AT = (12, 5)                   # Russian half (base sheet), board cells
GE_AT = (1, 4)                    # German half body top-left at offset (0, 0), board cells, unrotated
START = {'rotation_steps': 0, 'offset_x': 0, 'offset_y': 0}
EDGE_MARGIN = 8                   # art px between the German half's paper and the table's edge (pad 6 + frame 2)
LAMP = (214, 116)                 # the hanging lamp's light pool (board art px)
BOOK = (6, 46, 146, 124)          # open guidebook on the table (x, y, w, h)


def tooth_mask() -> np.ndarray:
    """Card-sized mask of the five teeth (German paper reaching into the Russian half)."""
    m = np.zeros((CARD_H, CARD_W), bool)
    for (cy, hb) in TEETH:
        for k in range(TOOTH_D):
            r = int(round(hb * (1.0 - k / TOOTH_D)))
            m[max(0, cy - r):cy + r + 1, CUT + k] = True
    return m


def perforation_mask(teeth: np.ndarray) -> np.ndarray:
    m = np.zeros((CARD_H, CARD_W), bool)
    for y in range(1, CARD_H - 1, 3):
        if not teeth[max(0, y - 1):y + 2, CUT].any():
            m[y, CUT - 1] = True
            m[y, CUT] = True
    return m


def stamp_mask() -> tuple[np.ndarray, np.ndarray]:
    """Card-sized masks of the round violet stamp „C-17“ (ink) and its ink density."""
    ink = np.zeros((CARD_H, CARD_W), bool)
    cx, cy = STAMP_C[0] - 0.5, STAMP_C[1] - 0.5
    yy, xx = np.mgrid[0:CARD_H, 0:CARD_W].astype(np.float32)
    d = np.hypot(xx - cx, yy - cy)
    ink |= (d >= STAMP_R - 1.6) & (d <= STAMP_R + 0.4)
    ink |= (d >= 13.6) & (d <= 14.5)
    # ring text: German on the left semicircle (bottom -> top), Russian on the right (top -> bottom)
    for word, a0, a1 in (('ABGABE', 140.0, 222.0), ('ПРИЁМ', -34.0, 34.0)):
        n = len(word)
        for i, ch in enumerate(word):                                  # clockwise: up the left, down the right
            ang = math.radians(a0 + (a1 - a0) * (i / max(1, n - 1)))
            gx = cx + math.cos(ang) * 19.0
            gy = cy + math.sin(ang) * 19.0
            g = tmask(ch)
            x0 = int(round(gx - g.shape[1] / 2 + 0.5))
            y0 = int(round(gy - g.shape[0] / 2 + 0.5))
            ink[y0:y0 + g.shape[0], x0:x0 + g.shape[1]] |= g
    # separators on the cut (half a dot on each half)
    for sy in (int(cy - 19), int(cy + 19)):
        ink[sy:sy + 2, CUT - 1:CUT + 1] = True
    # centre: „C-“ left of the cut, „17“ right of it -- the same letters in both scripts
    left = tmask('C-', F57)
    right = tmask('17', F57)
    r0, r1 = STAMP_TEXT_ROWS
    ink[r0:r1, CUT - 2 - left.shape[1]:CUT - 2] |= left
    ink[r0:r1, CUT + 1:CUT + 1 + right.shape[1]] |= right
    for (cy, hb) in TEETH:                                            # brackets (±6 rows) stay clear of it
        assert cy + 6 < r0 or cy - 6 >= r1, ('tooth too close to the stamp centre', cy)
    dens = 0.78 + (noise(CARD_W, CARD_H, 4, 7177, octaves=2) - 0.5) * 0.5
    dens -= np.clip((d - 18) / 8, 0, 1) * 0.12                       # pressed harder in the middle
    return ink, np.clip(dens, 0.35, 0.95)


def whole_card() -> tuple[Canvas, np.ndarray, np.ndarray, np.ndarray]:
    """The joined card No. 0417 on a padded canvas; returns (canvas, teeth, holes, stamp ink)."""
    W, H = CARD_W + 2 * PAD, CARD_H + 2 * PAD
    cv = Canvas(W, H)
    yy, xx = np.mgrid[0:CARD_H, 0:CARD_W].astype(np.float32)
    tone = 4.05 + (noise(CARD_W, CARD_H, 24, 4170) - 0.5) * 0.45 + (noise(CARD_W, CARD_H, 3, 4171, 2) - 0.5) * 0.25
    e = np.minimum(np.minimum(xx, CARD_W - 1 - xx), np.minimum(yy, CARD_H - 1 - yy))
    tone -= np.clip((5 - e) / 5, 0, 1) * 0.55
    gx = np.abs(xx - CUT + 0.5)
    tone -= np.clip((3 - gx) / 3, 0, 1) * 0.35                       # handled along the perforation
    # the German half lay in the snow in a split crate: a tide mark low on the left
    td = np.hypot((xx - 34) / 1.6, yy - 62)
    tone -= ((td > 15) & (td < 17.5)).astype(np.float32) * 0.55
    tone -= np.clip(1 - td / 16, 0, 1) * 0.25 * (xx < CUT)
    card = dither(CARD_W, CARD_H, tone, PAPER)
    cv.blend(np.ones((CARD_H, CARD_W), bool), PAD, PAD, card)
    rng = np.random.default_rng(4172)
    for _ in range(26):                                               # foxing
        fx, fy = int(rng.integers(3, CARD_W - 3)), int(rng.integers(3, CARD_H - 3))
        cv.rect(PAD + fx, PAD + fy, 1 + int(rng.integers(0, 2)), 1, C(PAPER[2]), 0.7)
    # the form: header rules, ruled lines with ticks at the cut, a margin line on the German side
    cv.rect(PAD + 3, PAD + 13, CARD_W - 6, 1, C(BLUE_INK), 0.55)
    cv.rect(PAD + 3, PAD + 15, CARD_W - 6, 1, C(BLUE_INK), 0.35)
    for ly in LINES_Y:
        cv.rect(PAD + 3, PAD + ly, CARD_W - 6, 1, C(BLUE_INK), 0.42)
        cv.rect(PAD + CUT - 3, PAD + ly - 1, 1, 3, C(BLUE_INK), 0.8)   # line-end ticks either side of the cut
        cv.rect(PAD + CUT + 2, PAD + ly - 1, 1, 3, C(BLUE_INK), 0.8)
    cv.rect(PAD + 3, PAD + 16, 1, CARD_H - 19, C(RED), 0.35)
    # German half (left): No., name, the red Vermerk, Kordon-17, Ilse
    text(cv, 'NR. 0417', PAD + 6, PAD + 4, INK, F57)
    text(cv, 'KARTEIKARTE', PAD + 54, PAD + 6, INK_B, a=0.75)
    rows_de = [('LINDNER, ANNA', INK), ('GEB. KOWALENKO 1926', INK), ('C-17: RÜCKF. OST', RED),
               ('KORDON-17, TÜR OST', INK), ('ILSE, 8 – UNGEKLÄRT', INK)]
    for (s, col), ly in zip(rows_de, LINES_Y):
        assert text_w(s) <= CUT - STAMP_R - 2, s
        text(cv, s, PAD + 6, PAD + ly - 7, col, a=0.92)
    # Russian half (right): the header clear of the first notch, the rows clear of the round stamp
    hx = PAD + CUT + 7
    head_ru = 'УЧЁТНАЯ КАРТОЧКА'
    text(cv, head_ru, hx, PAD + 6, INK_B, a=0.8)
    rows_ru = ['КОВАЛЕНКО', 'АННА ПЕТРОВНА', '1926, ХАРЬКОВ', 'ВОЗВРАЩЕНКА', 'ДАЛЕЕ: КАРСК']
    rx = CUT + STAMP_R + 4
    for s, ly in zip(rows_ru, LINES_Y):
        assert rx + text_w(s) <= CARD_W - 6, s
        text(cv, s, PAD + rx, PAD + ly - 7, INK, a=0.92)
    text(cv, 'С-17/45', hx, PAD + 73, INK_B, a=0.8)
    text(cv, '№0417', PAD + CARD_W - 5, PAD + 73, INK, align='right')
    # rectangular red stamp „ПРИНЯТЬ“ (Annehmen), top right: a 1-px frame with two clear pixels between it and the
    # letters on every side, clear of the header and of the first row (the review found the old one touching
    # „КАРСК“ and its П merging into the frame); the ink is worn like a rubber stamp, not printed.
    word = 'ПРИНЯТЬ'
    ww = text_w(word)
    sw, sh = ww + 6, 11
    sx, sy = PAD + CARD_W - 5 - sw, PAD + 2
    stamp = np.zeros((sh, sw), bool)
    stamp[0, :] = stamp[sh - 1, :] = True
    stamp[:, 0] = stamp[:, sw - 1] = True
    stamp[3:8, 3:3 + ww] |= tmask(word)
    wear = 0.8 + (noise(sw, sh, 3, 4173) - 0.5) * 0.34
    col = np.zeros((sh, sw, 4), np.float32)
    col[..., :3] = C(RED)[:3]
    col[..., 3] = 255
    cv.blend(stamp.astype(np.float32) * np.clip(wear, 0.6, 0.95), sx, sy, col)
    assert hx + text_w(head_ru) + 2 <= sx, 'ПРИНЯТЬ touches the header'
    assert PAD + rx + text_w(rows_ru[0]) + 4 <= sx, 'ПРИНЯТЬ touches the first row'
    assert sy + sh + 1 <= PAD + LINES_Y[0] - 7, 'ПРИНЯТЬ reaches the first row'
    # pin hole of the box on the Russian half
    cv.rect(PAD + CUT + 58, PAD + 2, 1, 1, C(INK), 0.9)
    cv.rect(PAD + CUT + 57, PAD + 2, 3, 1, C('#7A5A3A'), 0.35)
    # the red C-17 tab (German half only), sticking out above the top edge
    tx0, tx1 = TAB
    cv.rect(PAD + tx0, PAD - 5, tx1 - tx0, 9, C(RED))
    cv.rect(PAD + tx0, PAD - 5, tx1 - tx0, 1, C(RED_L))
    cv.rect(PAD + tx0, PAD + 3, tx1 - tx0, 1, C(RED_D))
    text(cv, 'C-17', PAD + (tx0 + tx1) // 2, PAD - 4, PAPER[5], align='center')
    # the round stamp across the cut
    ink, dens = stamp_mask()
    teeth = tooth_mask()
    holes = perforation_mask(teeth)
    col = np.zeros((CARD_H, CARD_W, 4), np.float32)
    col[..., :3] = C(VIOLET[1])[:3]
    col[..., 3] = 255
    cv.blend(ink.astype(np.float32) * dens, PAD, PAD, col)
    return cv, teeth, holes, ink


def card_halves() -> dict:
    """Cuts the whole card into the German half (stored upside down, padded) and the Russian half."""
    cv, teeth, holes, ink = whole_card()
    W, H = CARD_W + 2 * PAD, CARD_H + 2 * PAD
    ge = np.zeros((H, W), bool)
    ge[PAD:PAD + CARD_H, PAD:PAD + CUT] = True
    ge[PAD:PAD + CARD_H, PAD:PAD + CARD_W] |= teeth
    ge[PAD - 5:PAD + 1, PAD + TAB[0]:PAD + TAB[1]] = True
    ru = np.zeros((H, W), bool)
    ru[PAD:PAD + CARD_H, PAD + CUT:PAD + CARD_W] = True
    ru[PAD:PAD + CARD_H, PAD:PAD + CARD_W] &= ~teeth
    hole_full = np.zeros((H, W), bool)
    hole_full[PAD:PAD + CARD_H, PAD:PAD + CARD_W] = holes
    ge &= ~hole_full
    ru &= ~hole_full
    out = {}
    for name, m, x0, x1, y0, y1 in (('de', ge, 0, PAD + CUT + PAD, 0, H), ('ru', ru, PAD + CUT, PAD + CARD_W, PAD, PAD + CARD_H)):
        arr = cv.c[y0:y1, x0:x1].copy()
        arr[..., 3] = np.where(m[y0:y1, x0:x1], arr[..., 3], 0)
        half = Canvas(x1 - x0, y1 - y0)
        half.c = arr
        r = rim(half.c[..., 3])
        half.blend(r, 0, 0, C(PAPER[1]), 0.55)
        out[name] = half
    de = out['de']
    de.c = np.ascontiguousarray(np.rot90(de.c, 2))                    # laid in upside down
    out['whole'] = cv
    return out


def halves_marks() -> dict:
    """Mark positions (continuous art px of each sheet BODY) and inward directions.  base = Russian half (as on
    the table); overlay = German half AS STORED (upside down).  Upright German point (x, y) -> stored
    (112 - x, 80 - y)."""
    bw, bh = HALF_CELLS[0] * CELL, HALF_CELLS[1] * CELL

    def st(p):
        return [bw - p[0], bh - p[1]]

    base = {'notch': [], 'stamp_half': [], 'line_end': []}
    over = {'tooth': [], 'stamp_half': [], 'line_end': []}
    for i, (cy, hb) in enumerate(TEETH):
        tid = 't%d' % (i + 1)
        base['notch'].append({'id': tid, 'at': [float(TOOTH_D), cy + 0.5], 'dir': [1, 0], 'half_base': hb})
        over['tooth'].append({'id': tid, 'at': st((CUT + TOOTH_D, cy + 0.5)), 'dir': [1, 0], 'half_base': hb})
    base['stamp_half'].append({'id': 'stamp', 'at': [0.0, float(STAMP_C[1])], 'dir': [1, 0], 'r': STAMP_R})
    over['stamp_half'].append({'id': 'stamp', 'at': st((CUT, STAMP_C[1])), 'dir': [1, 0], 'r': STAMP_R})
    for i, ly in enumerate(LINES_Y):
        lid = 'l%d' % (i + 1)
        base['line_end'].append({'id': lid, 'at': [0.0, ly + 0.5], 'dir': [1, 0]})
        over['line_end'].append({'id': lid, 'at': st((CUT, ly + 0.5)), 'dir': [1, 0]})
    return {'base': base, 'overlay': over}


def rot(v, steps: int):
    dx, dy = v
    for _ in range(steps % 4):
        dx, dy = -dy, dx               # clockwise quarter turn on screen (y down) -- Vector2.rotated(PI / 2)
    return (dx, dy)


def over_to_board(p, steps: int, ox: int, oy: int):
    bw, bh = HALF_CELLS[0] * CELL, HALF_CELLS[1] * CELL
    cx = (GE_AT[0] + ox) * CELL + bw / 2
    cy = (GE_AT[1] + oy) * CELL + bh / 2
    d = rot((p[0] - bw / 2, p[1] - bh / 2), steps)
    return (cx + d[0], cy + d[1])


def base_to_board(p):
    return (RU_AT[0] * CELL + p[0], RU_AT[1] * CELL + p[1])


PAIRS = (('tooth', 'notch'), ('stamp_half', 'stamp_half'), ('line_end', 'line_end'))


def joined(marks: dict, steps: int, ox: int, oy: int) -> dict:
    out = {}
    for ko, kb in PAIRS:
        n = 0
        for mo in marks['overlay'][ko]:
            mb = next(m for m in marks['base'][kb] if m['id'] == mo['id'])
            p = over_to_board(mo['at'], steps, ox, oy)
            q = base_to_board(mb['at'])
            d = rot(mo['dir'], steps)
            if abs(p[0] - q[0]) < 0.5 and abs(p[1] - q[1]) < 0.5 and d == (-mb['dir'][0], -mb['dir'][1]):
                n += 1
        out[ko] = n
    return out


def faces(marks: dict, steps: int) -> bool:
    """Geometry only: can SOME offset put every tooth on its notch in this orientation?"""
    first = None
    for mo in marks['overlay']['tooth']:
        mb = next(m for m in marks['base']['notch'] if m['id'] == mo['id'])
        if rot(mo['dir'], steps) != (-mb['dir'][0], -mb['dir'][1]):
            return False
        p = over_to_board(mo['at'], steps, 0, 0)
        q = base_to_board(mb['at'])
        delta = (q[0] - p[0], q[1] - p[1])
        if first is None:
            first = delta
        elif abs(first[0] - delta[0]) > 0.5 or abs(first[1] - delta[1]) > 0.5:
            return False
    return True


def offset_range(steps: int):
    """Offsets that keep the WHOLE German half (turned by `steps`) on the table with EDGE_MARGIN art px to spare --
    the board frame never cuts its paper or its writing (round 10 review: at the old limits it did)."""
    bw, bh = HALF_CELLS
    hx, hy = (bw / 2.0, bh / 2.0) if steps % 2 == 0 else (bh / 2.0, bw / 2.0)
    m = EDGE_MARGIN / CELL
    c0 = (GE_AT[0] + bw / 2.0, GE_AT[1] + bh / 2.0)
    lo = (math.ceil(hx + m - c0[0] - 1e-6), math.ceil(hy + m - c0[1] - 1e-6))
    hi = (math.floor(BOARD_CELLS[0] - hx - m - c0[0] + 1e-6), math.floor(BOARD_CELLS[1] - hy - m - c0[1] + 1e-6))
    return lo, hi


def check_halves(marks: dict) -> dict:
    pz = json.load(open(os.path.join(ROOT, 'data', 'v3', 'puzzles.json'), encoding='utf-8'))
    sol = next(x for x in pz['puzzles'] if x['id'] == 'pz_c4_halves')['solution']
    full, partial = [], []
    for r in range(4):
        lo, hi = offset_range(r)
        for x in range(lo[0], hi[0] + 1):
            for y in range(lo[1], hi[1] + 1):
                j = joined(marks, r, x, y)
                if j['tooth'] == 5 and j['stamp_half'] == 1:
                    full.append((r, x, y))
                elif j['tooth'] > 0 or j['stamp_half'] > 0:
                    partial.append((r, x, y, j))
    assert full == [(sol['rotation_steps'], sol['offset_x'], sol['offset_y'])], full
    assert partial == [], partial[:5]
    j = joined(marks, sol['rotation_steps'], sol['offset_x'], sol['offset_y'])
    assert j['line_end'] == len(LINES_Y), j
    assert [faces(marks, r) for r in range(4)] == [r == sol['rotation_steps'] for r in range(4)]
    s0 = joined(marks, START['rotation_steps'], START['offset_x'], START['offset_y'])
    assert s0 == {'tooth': 0, 'stamp_half': 0, 'line_end': 0}, s0
    # the solution pose puts the German body flush against the Russian half
    assert (GE_AT[0] + sol['offset_x'] + HALF_CELLS[0], GE_AT[1] + sol['offset_y']) == RU_AT
    # the start, the solution and every pose of the input driver (R, R, →×4, ↓) lie inside the clamped ranges
    for (r, x, y) in ((0, 0, 0), (1, 0, 0), (2, 0, 0), (2, 4, 0), (2, 4, 1)):
        lo, hi = offset_range(r)
        assert lo[0] <= x <= hi[0] and lo[1] <= y <= hi[1], ('pose outside the table', r, x, y)
    return sol


# ----------------------------------------------------------------------------- the sand house table
def wood_planks(w: int, h: int, seed: int, ramp=None, plank: int = CELL) -> tuple[np.ndarray, list]:
    """Tone field of horizontal planks (one cell high), grain, end seams; returns (tone, nail positions)."""
    ramp = ramp or WOOD
    rng = np.random.default_rng(seed)
    tone = np.zeros((h, w), np.float32)
    nails = []
    xx = np.arange(w, dtype=np.float32)[None, :]
    for r in range(int(math.ceil(h / plank))):
        y0, y1 = r * plank, min(h, (r + 1) * plank)
        ph = y1 - y0
        small = noise(w // 7 + 3, ph, 2.5, seed * 7 + r, octaves=2)
        g = np.repeat(small, 7, axis=1)[:, :w]
        knot = noise(w, ph, 9, seed * 11 + r, octaves=2)
        base = 2.6 + rng.uniform(-0.45, 0.45)
        t = base + (g - 0.5) * 1.1 + 0.28 * np.sin(xx / (6.0 + r % 3) + r * 1.7 + g * 4.0)
        t -= np.clip((knot - 0.78) * 6, 0, 1) * 1.2
        tone[y0:y1] = t
        tone[y0, :] = 0.35                                            # the joint between two planks
        if y0 + 1 < h:
            tone[y0 + 1, :] += 0.35
        x = int(rng.integers(8, 70))
        while x < w - 4:
            tone[y0:y1, x] = 0.6
            tone[y0:y1, x + 1] += 0.3
            for ny in (y0 + 4, y1 - 5):
                nails.append((x - 3, ny))
                nails.append((x + 4, ny))
            x += int(rng.integers(80, 170))
    return np.clip(tone, 0, len(ramp) - 1), nails


def table() -> Canvas:
    w, h = BOARD_CELLS[0] * CELL, BOARD_CELLS[1] * CELL
    cv = Canvas(w, h)
    tone, nails = wood_planks(w, h, 61)
    rng = np.random.default_rng(6101)
    for _ in range(40):                                              # scratches and knife marks
        x0, y0 = int(rng.integers(0, w)), int(rng.integers(0, h))
        ln = int(rng.integers(4, 16))
        dy = int(rng.integers(-2, 3))
        for k in range(ln):
            yy = y0 + (dy * k) // max(1, ln)
            if 0 <= yy < h and 0 <= x0 + k < w:
                tone[yy, x0 + k] += 0.55
    cv.blend(np.ones((h, w), bool), 0, 0, dither(w, h, tone, WOOD))
    for (nx, ny) in nails:
        if 0 <= nx < w - 2 and 0 <= ny < h - 2:
            cv.rect(nx, ny, 2, 2, C(STEEL[1]))
            cv.px(nx, ny, C(STEEL[3]))
    # a sieve in the corner (top left) and the drying sand
    sv = Canvas(64, 64)
    m_out = disc(30, 31.5, 31.5, 64)
    m_in = disc(26, 31.5, 31.5, 64)
    sv.blend(m_out & ~m_in, 0, 0, C(WOOD_L[2]))
    sv.blend(ring(28.5, 30.0, 64), 0, 0, C(WOOD_L[3]))
    yy, xx = np.mgrid[0:64, 0:64]
    mesh = m_in & (((xx + yy) % 3 == 0) | ((xx - yy) % 3 == 0))
    sv.blend(m_in, 0, 0, C(SAND[1]), 0.85)
    sv.blend(mesh, 0, 0, C(STEEL[2]), 0.9)
    cv.blit(sv, -26, -28)
    sand_rng = np.random.default_rng(6102)
    for _ in range(900):
        if sand_rng.random() < 0.55:
            x = int(abs(sand_rng.normal(0, 26)))
            y = int(abs(sand_rng.normal(0, 22)))
        else:
            x = int(sand_rng.normal(118, 16))
            y = int(abs(sand_rng.normal(10, 7)))
        if 0 <= x < w and 0 <= y < h:
            cv.px(x, y, C(SAND[int(sand_rng.integers(1, 4))]), 0.9)
    for _ in range(260):                                             # grains everywhere (sand house)
        x, y = int(sand_rng.integers(0, w)), int(sand_rng.integers(0, h))
        cv.px(x, y, C(SAND[int(sand_rng.integers(0, 3))]), 0.6)
    heap = np.zeros((14, 34), np.float32)
    hy, hx = np.mgrid[0:14, 0:34].astype(np.float32)
    heap = np.clip(1 - np.hypot((hx - 17) / 16, (hy - 9) / 6), 0, 1)
    cv.blend(heap > 0.05, 101, 2, dither(34, 14, 1.0 + heap * 2.3, SAND))

    tracing(cv)
    book(cv)
    card_box(cv)
    watch(cv, 286, 196)
    camera(cv, 156, 190)
    mug(cv, 170, 22)
    # the hanging lamp: banded light pool, dark corners
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    d = np.hypot((xx - LAMP[0]) / 1.3, (yy - LAMP[1]) * 1.05)
    light = np.clip(1.0 - d / 190.0, 0, 1) ** 1.25
    f = 0.42 + 0.78 * light_bands(light, 8)
    multiply(cv, f, (1.0, 0.97, 0.9))
    return cv


def book(cv: Canvas):
    """Ekdahl's Swedish guidebook (1938, original design), open at pages 212/213."""
    x, y, w, h = BOOK
    cv.rect(x - 3, y - 2, w + 6, h + 5, C(CLOTH[1]))                   # cover
    cv.rect(x - 3, y + h + 2, w + 6, 1, C(CLOTH[0]))
    cv.rect(x - 2, y - 1, w + 4, h + 2, C(CLOTH[2]))
    gut = x + w // 2
    for side in (0, 1):
        px0 = x if side == 0 else gut + 1
        pw = w // 2 - 1
        pg_ = Canvas(pw, h)
        yy, xx = np.mgrid[0:h, 0:pw].astype(np.float32)
        dg = (pw - 1 - xx) if side == 0 else xx                       # distance to the gutter
        tone = 4.2 + (noise(pw, h, 18, 3800 + side) - 0.5) * 0.35 - np.clip((7 - dg) / 7, 0, 1) * 1.3
        tone -= np.clip((3 - (xx if side == 0 else pw - 1 - xx)) / 3, 0, 1) * 0.6
        pg_.blend(np.ones((h, pw), bool), 0, 0, dither(pw, h, tone, PAPER))
        cv.blit(pg_, px0, y)
        for k in range(3):                                            # page stack at the outer edge
            ex = px0 - 1 - k if side == 0 else px0 + pw + k
            cv.rect(ex, y + 1 + k, 1, h - 2 - 2 * k, C(PAPER[3 - k]))
    cv.rect(gut - 1, y, 3, h, C(PAPER[0]), 0.85)
    # left page 212: chapter heading, text, a small engraving of the depot turntable
    lx = x + 6
    text(cv, 'KARSK', lx, y + 6, INK, F57)
    text(cv, 'BANGÅRD OCH DEPÅ', lx, y + 16, INK_B, a=0.85)
    rng = np.random.default_rng(3801)
    for r in range(8):
        yy0 = y + 26 + r * 5
        xx0 = lx
        while xx0 < gut - 10:
            ln = int(rng.integers(3, 12))
            cv.rect(xx0, yy0, min(ln, gut - 8 - xx0), 1, C(INK_B), 0.55)
            xx0 += ln + 2
    ex, ey = lx + 10, y + 70                                          # engraving: turntable and stalls
    for k in range(9):
        a = math.radians(200 + k * 17)
        cv.line(ex + 22, ey + 34, ex + 22 + math.cos(a) * 26, ey + 34 + math.sin(a) * 26, C(INK_B), 0.75)
    for rr in (8, 9):
        m = ring(rr - 0.5, rr + 0.5, 2 * rr + 3)
        cv.blend(m, ex + 22 - rr - 1, ey + 34 - rr - 1, C(INK_B), 0.8)
    for k in range(5):
        cv.rect(ex + k * 9, ey + 4, 6, 6, C(INK_B), 0.35)
    text(cv, '212', lx, y + h - 8, INK_B, a=0.9)
    # right page 213: text and a small station map
    rx = gut + 6
    for r in range(13):
        yy0 = y + 8 + r * 5
        xx0 = rx
        while xx0 < x + w - 8:
            ln = int(rng.integers(3, 12))
            cv.rect(xx0, yy0, min(ln, x + w - 6 - xx0), 1, C(INK_B), 0.55)
            xx0 += ln + 2
    for k in range(4):
        cv.line(rx + 2, y + 80 + k * 6, rx + 60, y + 76 + k * 5, C(INK_B), 0.6)
    text(cv, '213', x + w - 6, y + h - 8, INK_B, a=0.9, align='right')


def tracing(cv: Canvas):
    """Konrad's tracing of Blatt 7 (onion skin), half under the book and a little askew: the Kordon room with
    Tür West and Tür Ost, the counter, the bench for fourteen; his block letters at the edge."""
    w, h = 112, 58
    tr = Canvas(w, h)
    a = 0.58 + (noise(w, h, 6, 5200) - 0.5) * 0.16
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    a += np.clip((3 - np.minimum(np.minimum(xx, w - 1 - xx), np.minimum(yy, h - 1 - yy))) / 3, 0, 1) * 0.18
    curl = (xx - (w - 16)) + (yy - (h - 14)) > 0
    base = np.zeros((h, w, 4), np.float32)
    base[..., :3] = C(ONION[2])[:3]
    base[..., 3] = 255
    tr.blend(a * ~curl, 0, 0, base)
    tr.blend(curl & ((xx - (w - 16)) + (yy - (h - 14)) < 9), 0, 0, C(ONION[0]), 0.75)    # curled corner
    for k in range(0, min(w, h) * 2, 1):                                               # a soft fold
        fx, fy = 20 + k, 2 + k // 3
        if fx < w and fy < h:
            tr.px(fx, fy, C(ONION[0]), 0.35)
    rx0, ry0, rx1, ry1 = 14, 34, 88, 54
    for (p, q) in (((rx0, ry0), (rx1, ry0)), ((rx1, ry0), (rx1, ry1)), ((rx0, ry1), (rx1, ry1)), ((rx0, ry0), (rx0, ry1))):
        tr.line(p[0], p[1], q[0], q[1], C(PENCIL_BLUE), 0.95)
    tr.rect(rx0, 40, 1, 7, C(ONION[2]))                                # Tür West
    tr.rect(rx1, 40, 1, 7, C(ONION[2]))                                # Tür Ost
    tr.rect(rx0 + 30, ry0 + 1, 12, 3, C(PENCIL_BLUE), 0.55)            # the handover counter
    tr.rect(rx0 + 6, ry1 - 4, 52, 1, C(PENCIL_BLUE), 0.9)              # the bench ...
    for k in range(14):                                                # ... for fourteen
        tr.rect(rx0 + 7 + k * 3 + (k // 7), ry1 - 6, 1, 2, C(PENCIL_BLUE), 0.95)
    text(tr, 'TÜR OST', rx1 - 30, 46, PENCIL_BLUE, a=0.9)
    text(tr, 'DI 23.40', rx0, 27, PENCIL_BLUE, a=0.85)
    out = Canvas(w + 8, h)                                             # laid a little askew
    for y in range(h):
        sh = int(y * 0.12)
        out.c[y, sh:sh + w] = tr.c[y]
    cv.blit(out, 22, 144)


def card_box(cv: Canvas):
    """Lev's index box from the siding hut, „С-17/45 ПРИНЯТЬ“ -- one slot empty (card 0417 is on the table)."""
    x, y, w, h = 236, 6, 78, 46
    cv.rect(x + 3, y + 4, w, h, C(NIGHT), 0.45)                        # shadow
    cv.rect(x, y, w, h, C(WOOD_L[1]))
    cv.rect(x + 1, y + 1, w - 2, h - 14, C(WOOD_L[0]))                # the inside, seen from above
    for k in range(17):                                               # standing cards (top edges)
        cy = y + 3 + k * 2
        if cy > y + h - 16:
            break
        if k == 7:
            cv.rect(x + 4, cy, w - 8, 1, C(NIGHT), 0.8)                # the gap of card 0417
            continue
        cv.rect(x + 4, cy, w - 8, 1, C(PAPER[3 + (k % 2)]))
    cv.rect(x + 9, y + 2, 12, 2, C(RED), 0.9)                          # a red tab further back
    cv.rect(x, y + h - 13, w, 13, C(WOOD_L[2]))                        # front panel
    cv.rect(x, y + h - 13, w, 1, C(WOOD_L[3]))
    cv.rect(x + 8, y + h - 11, w - 16, 9, C(PAPER[4]))                 # label
    text(cv, 'С-17/45 ПРИНЯТЬ', x + w // 2, y + h - 9, INK, align='center')
    cv.rect(x + w // 2 - 4, y + h - 2, 8, 1, C(BRASS[2]))             # pull


def watch(cv: Canvas, cx: int, cy: int):
    """Lev's pocket watch, 19.05 -- the card has to be back in the box at half past seven."""
    r = 13
    n = 2 * r + 3
    cv.blend(disc(r + 1.2, size=n), cx - n // 2 + 2, cy - n // 2 + 2, C(NIGHT), 0.5)
    cv.blend(disc(r + 1.2, size=n), cx - n // 2, cy - n // 2, C(STEEL[2]))
    cv.blend(ring(r - 0.4, r + 1.2, n), cx - n // 2, cy - n // 2, C(STEEL[4]))
    cv.blend(disc(r - 1.4, size=n), cx - n // 2, cy - n // 2, C(PAPER[5]))
    for k in range(12):
        a = math.radians(k * 30 - 90)
        cv.px(cx + round(math.cos(a) * (r - 3)), cy + round(math.sin(a) * (r - 3)), C(INK), 0.9)
    ah = math.radians((7 + 5 / 60) * 30 - 90)
    am = math.radians(5 * 6 - 90)
    cv.line(cx, cy, cx + math.cos(ah) * 6, cy + math.sin(ah) * 6, C(INK))
    cv.line(cx, cy, cx + math.cos(am) * 9, cy + math.sin(am) * 9, C(INK))
    cv.px(cx, cy, C(RED))
    cv.rect(cx - 2, cy - r - 4, 5, 3, C(STEEL[3]))                     # crown
    cv.rect(cx - 1, cy - r - 6, 3, 2, C(STEEL[4]))
    for k in range(1, 12):                                            # chain
        if k % 2:
            cv.px(cx + 4 + k * 2, cy - r - 6 - int(4 * math.sin(k / 3.0)), C(STEEL[4]))


def camera(cv: Canvas, x: int, y: int):
    """Ekdahl's camera (generic 1950s rangefinder, no maker's name)."""
    w, h = 50, 26
    cv.rect(x + 3, y + 4, w, h, C(NIGHT), 0.45)
    cv.rect(x, y + 6, w, h - 6, C(STEEL[0]))                           # leatherette body
    for k in range(0, w, 2):
        cv.rect(x + k, y + 8, 1, h - 9, C(STEEL[1]), 0.6)
    cv.rect(x, y, w, 7, C(STEEL[4]))                                   # chrome top plate
    cv.rect(x, y + 6, w, 1, C(STEEL[3]))
    cv.rect(x + 4, y + 2, 7, 3, C(STEEL[1]))                           # finder windows
    cv.rect(x + 36, y + 2, 5, 3, C(STEEL[1]))
    cv.rect(x + 19, y - 2, 6, 3, C(STEEL[3]))                          # shutter dial
    n = 17
    cv.blend(disc(8, size=n), x + 25 - 8, y + 9, C(STEEL[2]))           # lens
    cv.blend(disc(5.5, size=n), x + 25 - 8, y + 9, C('#101820'))
    cv.blend(disc(2, 6, 6, n), x + 25 - 8, y + 9, C('#6A86A0'), 0.8)
    for k in range(20):                                               # strap
        cv.px(x + w + 1 + k, y + 10 + int(5 * math.sin(k / 4.0)), C(STEEL[1]))
        cv.px(x + w + 1 + k, y + 11 + int(5 * math.sin(k / 4.0)), C(STEEL[0]))


def mug(cv: Canvas, cx: int, cy: int):
    n = 21
    cv.blend(disc(9.5, size=n), cx - 10 + 2, cy - 10 + 2, C(NIGHT), 0.45)
    cv.blend(disc(9.5, size=n), cx - 10, cy - 10, C(STEEL[3]))
    cv.blend(disc(7.6, size=n), cx - 10, cy - 10, C('#5A3418'))
    cv.blend(disc(5.0, 8.5, 8.5, n), cx - 10, cy - 10, C('#7A4A22'), 0.6)
    cv.blend(ring(8.6, 9.5, n), cx - 10, cy - 10, C(STEEL[5]), 0.8)
    cv.rect(cx + 9, cy - 3, 4, 2, C(STEEL[3]))
    cv.rect(cx + 12, cy - 3, 2, 7, C(STEEL[3]))
    cv.rect(cx + 9, cy + 3, 4, 2, C(STEEL[3]))


def halves_snap() -> Canvas:
    """Amber corner brackets around a tooth that sits in its notch (shape cue while joining)."""
    s = 13
    cv = Canvas(s, s)
    for (x, y, dx, dy) in ((0, 0, 1, 1), (s - 1, 0, -1, 1), (0, s - 1, 1, -1), (s - 1, s - 1, -1, -1)):
        for k in range(4):
            cv.px(x + dx * k, y, C(AMBER))
            cv.px(x, y + dy * k, C(AMBER))
    outline(cv, NIGHT, 0.9)
    return cv


def halves_ring() -> Canvas:
    """The closed stamp: a pale violet ring that blooms over the joined circle (success beat)."""
    n = 2 * STAMP_R + 9
    cv = Canvas(n, n)
    cv.blend(ring(STAMP_R + 1.0, STAMP_R + 3.2, n), 0, 0, C('#C9BEF2'), 0.9)
    cv.blend(ring(STAMP_R + 3.2, STAMP_R + 4.2, n), 0, 0, C('#8E80D0'), 0.6)
    return cv


def halves_click() -> Canvas:
    """A small spark where a tooth clicks into its notch."""
    rows = ['...#...', '...#...', '.#.#.#.', '###.###', '.#.#.#.', '...#...', '...#...']
    cv = sprite(rows, {'#': AMBER_L})
    return cv


def legend_icons() -> dict:
    """Clean legend drawings (shape, not colour): a tooth meeting its notch, a stamp half, a ruled line with its
    tick at the cut."""
    out = {}
    cv = Canvas(26, 18)                                                # tooth -> notch
    cv.rect(0, 1, 11, 16, C(PAPER[4]))
    for k in range(5):
        r = 4 - k
        cv.rect(11 + k, 9 - r, 1, 2 * r + 1, C(PAPER[4]))
    cv.rect(15, 1, 11, 16, C(PAPER[3]))
    for k in range(5):
        r = 4 - k
        cv.rect(15 + k, 9 - r, 1, 2 * r + 1, C(NAVY))
    cv.rect(0, 5, 11, 1, C(BLUE_INK), 0.6)
    cv.rect(0, 13, 11, 1, C(BLUE_INK), 0.6)
    cv.rect(20, 5, 6, 1, C(BLUE_INK), 0.6)
    cv.rect(20, 13, 6, 1, C(BLUE_INK), 0.6)
    out['tooth'] = cv
    cv = Canvas(18, 22)                                                # stamp half
    cv.rect(0, 0, 18, 22, C(PAPER[4]))
    n = 41
    m = ring(STAMP_R - 1.6 - 6, STAMP_R + 0.4 - 6, n)
    cv.blend(m[n // 2 - 11:n // 2 + 11, n // 2 - 18:n // 2], 0, 0, C(VIOLET[1]))
    cv.blend(tmask('C-', F57), 4, 8, C(VIOLET[1]))
    cv.rect(17, 0, 1, 22, C(PAPER[1]))
    out['stamp'] = cv
    cv = Canvas(26, 14)                                                # line ends with ticks
    cv.rect(0, 0, 12, 14, C(PAPER[4]))
    cv.rect(14, 0, 12, 14, C(PAPER[4]))
    for y in (4, 10):
        cv.rect(0, y, 12, 1, C(BLUE_INK), 0.7)
        cv.rect(14, y, 12, 1, C(BLUE_INK), 0.7)
        cv.rect(10, y - 1, 1, 3, C(BLUE_INK))
        cv.rect(15, y - 1, 1, 3, C(BLUE_INK))
    out['lines'] = cv
    return out


def surface(cv: Canvas, rect) -> str:
    x, y, w, h = rect
    a = cv.c[y:y + h, x:x + w, :3].reshape(-1, 3).astype(np.float32)
    m = np.median(a, axis=0)
    return '#%02X%02X%02X' % tuple(int(v) for v in m)


# ============================================================================= HAUS 14 (pz_c4_house)
HW, HH = 316, 246
WING_W = 78
WING_X = {'v': 10, 's': 92, 'h': 174}
SEAMS = [88, 170, 252]            # 4-px inner corners / fire walls between the wings; 252 is the cut wall right of the
                                  # back stairs -- the Hinterhaus goes on over Pietsch's souterrain (as in the courtyard)
WS = (256, 190, 56, 50)           # Pietsch's workshop in the souterrain (x, y, w, h)
EXT = (256, HW)                   # the Hinterhaus right of its stairwell, over the workshop (x0, x1)
FLAT_W = 54                       # facade part of a storey; the stairwell is cut open to the right of it
NODE_DX = 68                      # route node and Ilse's place inside a wing: the stair landing, clear of the flights
ROWS = {'d': (18, 34), '3': (52, 38), '2': (90, 38), '1': (128, 38), 'e': (166, 40), 'k': (206, 34)}
ROW_INDEX = {'k': 0, 'e': 1, '1': 2, '2': 3, '3': 4, 'd': 5}
COL_INDEX = {'v': 0, 's': 1, 'h': 2}
ORDER = ['k', 'e', '1', '2', '3', 'd']
GROUND = 206
KNEE = 30                         # attic knee walls rise from the loft floor to y 30, the ridge at y 20
RIDGE = 20
FLOOR_ATTIC = 50                  # feet stand on the drying lofts' floorboards at y 50
FLOOR_CELLAR = 238                # ... and on the cellar / workshop floor at y 238
HOUSE_ROOMS = ['vk', 've', 'v1', 'v2', 'v3', 'vd', 'sk', 'se', 's1', 's2', 's3', 'sd', 'hk', 'he', 'h1', 'h2', 'h3', 'hd', 'ws']
UNSAFE = ['s2', 'se', 've']
WATCH = {'s2': 'eye', 'se': 'lamp', 've': 'hat'}
HOUSEHOLDS = ['v3', 'v2', 'v1', 's3', 's2', 's1', 'se', 'h3', 'h2', 'h1']
LIT = ['v3', 'v1', 's3', 's1', 'se', 'h1', 'he']    # awake at 22.40
DIM = ['s2']                      # Pohl: a weak light behind the curtain (the courtyard shows it dim as well)
KIND = {'vd': 'attic', 'sd': 'attic', 'hd': 'attic', 'vk': 'cellar', 'sk': 'cellar', 'hk': 'cellar',
        've': 'passage', 'se': 'lodge', 'he': 'hall', 'ws': 'workshop'}
# the walking markers (tools: marker_konrad / marker_ilse): frame w, h, the feet pixel (x, y), the figure's height
K_FIG = {'frame': (15, 23), 'feet': (8, 21), 'height': 21}
I_FIG = {'frame': (12, 17), 'feet': (6, 15), 'height': 15}
FIG_FRAMES = 5                    # standing + four walking frames
TRAIL = 14                        # Konrad walks this many px of the way behind Ilse (one or two steps)
MATE_DX = -10                     # ... and stands this far beside her where no way leads in (the start)


def house_edges() -> list:
    e = []
    for w in 'vsh':
        chain = [w + f for f in ('k', 'e', '1', '2', '3', 'd')]
        e += [[a, b] for a, b in zip(chain[:-1], chain[1:])]
    e += [['vd', 'sd'], ['sd', 'hd'], ['vk', 'sk'], ['sk', 'hk'], ['hk', 'ws']]
    return e


def room_cell(rid: str) -> tuple[int, int]:
    if rid == 'ws':
        return (3, 0)
    return (COL_INDEX[rid[0]], ROW_INDEX[rid[1]])


def room_rect(rid: str) -> list:
    if rid == 'ws':
        return list(WS)
    y, h = ROWS[rid[1]]
    return [WING_X[rid[0]], y, WING_W, h]


def room_extra(rid: str) -> list:
    """Hit areas beyond the room's own rect: the back wing's flats and its loft go on right of its stairwell."""
    if rid in ('h1', 'h2', 'h3', 'hd'):
        y, h = ROWS[rid[1]]
        return [[EXT[0], y, EXT[1] - EXT[0], h]]
    return []


def floor_y(rid: str) -> int:
    """Where feet stand in a room: the top of its floor (art px)."""
    if rid == 'ws' or rid[1] == 'k':
        return FLOOR_CELLAR
    if rid[1] == 'd':
        return FLOOR_ATTIC
    y, h = ROWS[rid[1]]
    return y + h - 2


def room_stand(rid: str) -> list:
    """Ilse's place in a room (feet x, floor y): the landing in the stairwell, the loft and the cellar under the route
    line, in the workshop between the bench and the stove."""
    if rid == 'ws':
        return [WS[0] + 36, FLOOR_CELLAR]
    return [WING_X[rid[0]] + NODE_DX, floor_y(rid)]


def room_node(rid: str) -> list:
    """The route line's vertex: just above the floor where Ilse stands."""
    x, y = room_stand(rid)
    return [x, y - 2]


def room_label_at(rid: str) -> list:
    if rid == 'ws':
        return [WS[0] + 2, WS[1] + 15]
    wx = WING_X[rid[0]]
    f = rid[1]
    if f == 'd':
        return [wx + 18, 27]
    if f == 'k':
        return [wx + 3, 212]
    y, _ = ROWS[f]
    return [wx + 2, y + 1]


def stair_points(w: str, f: str) -> tuple:
    """The two flights of storey f in wing w as feet points: the foot of the near flight on the landing (right of the
    flat door), the half landing, the head of the far flight on the landing above."""
    sx = WING_X[w] + FLAT_W
    fy, fh = ROWS[f]
    bot = fy + fh
    half = bot - fh // 2
    return (sx + 6, bot - 2), (sx + 18, half - 1), (sx + 4, fy - 2)


def cellar_stair(w: str) -> tuple:
    """The steep cellar stair under the ground landing: its foot on the cellar floor, its head on the landing."""
    sx = WING_X[w] + FLAT_W
    return (sx + 2, FLOOR_CELLAR), (sx + 22, GROUND - 2)


def edge_path(a: str, b: str) -> list:
    """Feet waypoints from room a's stand to room b's: along the loft / the cellar corridor, or by the stairs."""
    pa, pb = room_stand(a), room_stand(b)
    if a == 'ws' or b == 'ws' or a[0] != b[0]:
        assert pa[1] == pb[1], (a, b)
        return [pa, pb]
    ia, ib = ORDER.index(a[1]), ORDER.index(b[1])
    if ia > ib:
        return list(reversed(edge_path(b, a)))
    if a[1] == 'k':
        foot, head = cellar_stair(a[0])
        return [pa, list(foot), list(head), pb]
    foot, turn, top = stair_points(a[0], a[1])
    return [pa, list(foot), list(turn), list(top), pb]


def roof_span(w: str) -> tuple:
    return (WING_X[w], WING_X[w] + WING_W) if w != 'h' else (WING_X['h'], HW)


def attic_top(x: float, w: str) -> float:
    """The underside of the roof (the loft's ceiling) at x."""
    x0, x1 = roof_span(w)
    mid, half = (x0 + x1) / 2.0, (x1 - x0) / 2.0
    return RIDGE + 3 + (abs(x - mid) / half) * (KNEE - RIDGE - 3)


def headroom(rid: str, x: float) -> float:
    """Free height above the floor at x in a room (the loft under its roof, the cellar under its vault)."""
    if rid == 'ws':
        return FLOOR_CELLAR - WS[1]
    if rid[1] == 'd':
        return FLOOR_ATTIC - attic_top(x, rid[0])
    if rid[1] == 'k':
        return FLOOR_CELLAR - (GROUND + 5)
    y, h = ROWS[rid[1]]
    return h - 2


def dir_of(a: str, b: str) -> str:
    ca, cb = room_cell(a), room_cell(b)
    d = (cb[0] - ca[0], cb[1] - ca[1])
    return {(0, 1): 'up', (0, -1): 'down', (1, 0): 'right', (-1, 0): 'left'}[d]


def check_house() -> list:
    pz = json.load(open(os.path.join(ROOT, 'data', 'v3', 'puzzles.json'), encoding='utf-8'))
    sol = next(x for x in pz['puzzles'] if x['id'] == 'pz_c4_house')['solution']
    adj = {r: [] for r in HOUSE_ROOMS}
    for a, b in house_edges():
        adj[a].append(b)
        adj[b].append(a)
    out, stack = [], [['s3']]
    while stack:
        path = stack.pop()
        if path[-1] == 'ws':
            out.append(path)
            continue
        for n in adj[path[-1]]:
            if n not in path and n not in UNSAFE:
                stack.append(path + [n])
    assert out == [sol], out
    for r in HOUSE_ROOMS:                                             # one passage per arrow at most
        ds = [dir_of(r, n) for n in adj[r]]
        assert len(ds) == len(set(ds)), (r, ds)
    step = {r: {dir_of(r, n): n for n in adj[r]} for r in HOUSE_ROOMS}
    assert step['s3']['down'] == 's2'                                  # inputplay: ↓ + Enter = past Frau Pohl
    route = ['s3']
    for k in ['up', 'right', 'down', 'down', 'down', 'down', 'down', 'right']:
        route.append(step[route[-1]][k])
    assert route == sol, route
    # the markers: every room's place is inside it, on its floor, with room above Konrad's hat; every way between
    # two rooms starts and ends at their places and runs level (a floor) or along a flight (never through a slab)
    for r in HOUSE_ROOMS:
        x, y = room_stand(r)
        rx, ry, rw, rh = room_rect(r)
        assert rx <= x < rx + rw and ry < y <= ry + rh, (r, x, y)
        assert headroom(r, x) >= K_FIG['height'] and headroom(r, x + MATE_DX) >= K_FIG['height'], (r, headroom(r, x))
    for a, b in house_edges():
        p = edge_path(a, b)
        assert p[0] == room_stand(a) and p[-1] == room_stand(b), (a, b)
        for (x0, y0), (x1, y1) in zip(p[:-1], p[1:]):
            assert 0 <= min(x0, x1) and max(x0, x1) < HW and 0 < min(y0, y1) and max(y0, y1) <= HH
            if y0 != y1:                                              # a flight: as steep as a stair, not a ladder
                assert abs(x1 - x0) >= 8 and abs(y1 - y0) / abs(x1 - x0) <= 1.8, (a, b, (x0, y0), (x1, y1))
    return sol


# ----------------------------------------------------------------------------- palettes (house)
SKY = ['#060B14', '#0A1220', '#0F1A2C', '#16233A', '#1F2E48']
SNOW = ['#7C889E', '#A3AFC2', '#C6CFDC', '#E4EAF1']
PL_V = ['#4A4640', '#5C564D', '#706859', '#857B69', '#9A8F7A']        # Vorderhaus courtyard plaster (ochre-grey)
PL_S = ['#3A3D3B', '#484B48', '#585B56', '#6A6C66', '#7E7F78']        # Seitenflügel plaster (grey, sooty)
BRICK = ['#36211D', '#472B24', '#5A372D', '#6D4437', '#835444']       # brick where the plaster has fallen
PL_H = ['#3E4246', '#4C5156', '#5C6268', '#6E747A', '#82888E']        # Hinterhaus plaster (cool grey, as in the yard)
ROOF = ['#12161C', '#1A1F27', '#232A33', '#2E3640']
STONE = ['#17140F', '#211D18', '#2C2720', '#38322A', '#463F35']
STAIR_WALL = ['#2E3A30', '#3A483C', '#6E6E64', '#86867A']            # oil-paint dado (green) / whitewash
LAMPW = ['#5A3216', '#8C5426', '#BA7A3A', '#E0A85A', '#F8D898']
SODIUM = ['#4A2A0C', '#7A4614', '#B86E22', '#E09A3C', '#FFC870']
DARKWIN = ['#06090E', '#0C1119', '#141B26', '#1F2836']
FRAME_N = {'neutral': '#2C2620', 'lit': '#1E140C', 'dark': '#151A22', 'dim': '#18140F'}

ROLE_COLORS = {
    'neutral': {'wall': '#6A5E4C', 'wall2': '#55493A', 'floor': '#4A3626', 'furn': '#3E2A1C', 'furn2': '#5E4430',
                'metal': '#4A4F56', 'paper': '#D6CEB6', 'fig': '#34384A', 'fig2': '#5A4238', 'skin': '#C29274',
                'hair': '#34261C', 'light': '#F2C878', 'glow': '#B08A54', 'curtain': '#6E5E48', 'lace': '#A89E88',
                'plant': '#3A5236', 'red': '#9A3A2E', 'cloth': '#7A6A52', 'cloth2': '#2A3448', 'face': '#C29274',
                'ember': '#7A3A1A', 'glass': '#3A4656'},
    'lit': {'wall': '#C88E48', 'wall2': '#A87036', 'floor': '#7A4A22', 'furn': '#3A2412', 'furn2': '#5A3418',
            'metal': '#2E2014', 'paper': '#FBE6B0', 'fig': '#1C130C', 'fig2': '#24180F', 'skin': '#2E1E12',
            'hair': '#140E09', 'light': '#FFF4CE', 'glow': '#F2C878', 'curtain': '#DCA45C', 'lace': '#F0C887',
            'plant': '#2A2412', 'red': '#3A1A10', 'cloth': '#4A2E16', 'cloth2': '#20160E', 'face': '#4A3220',
            'ember': '#E0782A', 'glass': '#E8B870'},
    'dark': {'wall': '#10151E', 'wall2': '#0B0F16', 'floor': '#090C12', 'furn': '#0A0D13', 'furn2': '#121822',
             'metal': '#121822', 'paper': '#262E3C', 'fig': '#1A212D', 'fig2': '#1A212D', 'skin': '#232B38',
             'hair': '#0E131B', 'light': '#2A3444', 'glow': '#161D28', 'curtain': '#1A2230', 'lace': '#2A3444',
             'plant': '#10161E', 'red': '#1A1E28', 'cloth': '#161C26', 'cloth2': '#10151E', 'face': '#5E6676',
             'ember': '#3A1E10', 'glass': '#1A2230'},
}


class Vig:
    """A small interior painted once with ROLES and rendered in three lights: neutral (overview), lit (awake at
    22.40, figures as silhouettes against the lamp), dark (an unlit room seen through cold glass)."""

    def __init__(self, w: int, h: int):
        self.w, self.h = w, h
        self.role = np.full((h, w), '', dtype=object)

    def rect(self, x, y, w, h, role):
        x0, y0 = max(0, int(x)), max(0, int(y))
        x1, y1 = min(self.w, int(x + w)), min(self.h, int(y + h))
        if x1 > x0 and y1 > y0:
            self.role[y0:y1, x0:x1] = role

    def px(self, x, y, role):
        if 0 <= x < self.w and 0 <= y < self.h:
            self.role[int(y), int(x)] = role

    def spr(self, rows, x, y, legend, flip=False):
        for yy, row in enumerate(rows):
            r = row[::-1] if flip else row
            for xx, ch in enumerate(r):
                if ch in legend:
                    self.px(x + xx, y + yy, legend[ch])

    def render(self, mode: str, seed: int = 0, cols: dict | None = None) -> np.ndarray:
        cols = cols or ROLE_COLORS[mode]
        out = np.zeros((self.h, self.w, 4), np.uint8)
        b = pg.bayer(self.w, self.h, seed % 4, (seed // 4) % 4)
        for role in set(self.role.flatten()):
            if role == '':
                continue
            m = self.role == role
            c = C(cols[role]).astype(np.float32)
            if role in ('wall', 'curtain', 'floor'):                   # a little texture on large areas
                shade = np.where(b > 0.72, 0.9, 1.0)[..., None]
                cc = np.clip(c[None, None, :3] * shade, 0, 255)
                out[m, :3] = cc[m].astype(np.uint8)
            else:
                out[m, :3] = c[:3].astype(np.uint8)
            out[m, 3] = 255
        return out


# legend letters for the figures: h hair, s skin, f clothes, g second clothes, k cap, r red, w paper, b cloth,
# c dark cloth, m metal (glasses, buttons), l light, e face (a pale face that shows even in a dark room), q glass glint
FIG = {'h': 'hair', 's': 'skin', 'f': 'fig', 'g': 'fig2', 'k': 'fig2', 'r': 'red', 'w': 'paper', 'b': 'cloth',
       'c': 'cloth2', 'm': 'metal', 'l': 'light', 'e': 'face', 'q': 'glass'}
# busts seen through a window, 7 px wide (facing right; flip for left) -- the silhouette must read in the light
BUST_MAN = ['..hhh..', '.hhhhh.', '.hhsss.', '.hssss.', '..ssss.', '...ss..', '.fffff.', 'fffffff', 'fffffff',
            'fffffff', 'fffffff']
BUST_READER = ['..hhh..', '.hhhhh.', '.hhsss.', '.hsqsss', '..sss..', '..fss..', '.fffff.', 'ffffff.', 'fffffff',
               'fffffff']
BUST_WOMAN = ['hh.....', 'hhhhh..', 'hhhhhh.', '.hhsss.', '.hssss.', '..sss..', '...s...', '.ggggg.', 'ggggggg',
              'ggggggg', 'ggggggg']
BUST_SHAWL = ['.bbbb..', 'bbbbbb.', 'bbssss.', 'bbssss.', 'b.sss..', '.bbbbb.', 'bbbbbbb', 'bgggggb', 'ggggggg',
              'ggggggg', 'ggggggg']
BUST_CHILD = ['.kkkk.', 'kkkkkk', '.sssss', '.ssss.', '..ss..', '.ffff.', 'ffffff', 'ffffff', 'ffffff']
BUST_OLD = ['.sss...', 'sssss..', 'ssmmss.', 'ssssss.', '.ssss..', '..ss...', '.ffff..', 'ffffff.', 'fffffff',
            'fffffff']
BUST_GRAN = ['.hh....', 'hhhh...', 'hhhhh..', 'hssmm..', '.ssss..', '..ss...', '.gggg..', 'gggggg.', 'ggggggg',
             'ggggggg']
BUST_GRAN_FRONT = ['..hhh..', '.hhhhh.', 'hhssshh', '.smsms.', '.sssss.', '..sss..', '.ggggg.', 'ggggggg',
                   'ggggggg', 'ggggggg']
BUST_KID = ['.hhh.', 'hhsss', '.sss.', '..s..', '.fff.', 'fffff', 'fffff']
WIN_W, WIN_H = 15, 21             # a window incl. its frame; the interior is 13 x 19
IN_W, IN_H = WIN_W - 2, WIN_H - 2
MULL_X, TRANS_Y = 7, 7            # the window cross (Kastenfenster): mullion column, transom row


def vig_window(name: str, frame: int = 0) -> Vig:
    """Interiors seen through a window (13 x 19 inner px).  The cross of the frame is drawn on top later
    (column MULL_X, row TRANS_Y), so people sit behind it the way they do in a real window."""
    v = Vig(IN_W, IN_H)
    v.rect(0, 0, IN_W, IN_H, 'wall')
    if name == 'v3a':                                                 # Lenz at his desk lamp, reading
        v.rect(0, 13, 13, 2, 'furn')
        v.rect(0, 15, 13, 4, 'wall2')
        v.rect(1, 6, 4, 1, 'metal')                                    # desk lamp: shade, arm, foot
        v.rect(0, 7, 5, 1, 'metal')
        v.rect(4, 8, 1, 4, 'metal')
        v.rect(3, 12, 3, 1, 'metal')
        v.rect(0, 9, 4, 4, 'glow')                                     # its pool on the desk
        v.px(2, 8, 'light')
        v.rect(10, 9, 3, 4, 'paper')                                   # a stack of books
        v.rect(10, 10, 3, 1, 'furn2')
        v.rect(10, 12, 3, 1, 'red')
        v.spr(BUST_READER, 5, 3 + (1 if frame else 0), FIG)
        v.rect(6, 12, 4, 1, 'paper')                                   # the open book
    elif name == 'v3b':                                               # the shelf of books and the radio
        v.rect(0, 6, 13, 1, 'furn')
        for k in range(12):
            top = 1 + (k % 3 == 1) + (k % 5 == 0)
            v.rect(k + 1, top, 1, 6 - top, ('paper', 'furn2', 'red', 'cloth')[k % 4])
        v.rect(2, 10, 9, 7, 'furn2')                                   # radio cabinet
        v.rect(3, 11, 7, 3, 'cloth')
        for k in range(3, 10, 2):
            v.px(k, 12, 'furn2')
        v.rect(3, 15, 5, 1, 'light')                                   # the dial
        v.px(9, 15, 'metal')
        v.rect(0, 17, 13, 2, 'furn')
    elif name == 'v2a':                                               # Frau Grabowski in her coat at the cold stove
        v.rect(0, 16, 13, 3, 'floor')
        v.rect(8, 7, 5, 11, 'metal')                                   # stove
        v.rect(9, 0, 2, 7, 'metal')                                    # pipe
        v.rect(9, 11, 3, 2, 'wall2')                                   # the cold fire door
        v.rect(8, 7, 5, 1, 'furn2')
        v.spr(BUST_SHAWL, 1, 7, FIG)
        v.rect(5, 15, 3, 1, 'cloth')                                   # her hands in her lap
    elif name == 'v2b':                                               # curtains drawn tight
        v.rect(0, 0, 13, 19, 'curtain')
        for k in range(1, 13, 3):
            v.rect(k, 1, 1, 18, 'lace')
        v.rect(0, 0, 13, 1, 'furn')
        v.rect(6, 1, 1, 18, 'wall2')
    elif name == 'v1a':                                               # Herr Schulz walks the baby up and down
        v.rect(0, 16, 13, 3, 'floor')
        v.rect(11, 1, 2, 14, 'curtain')
        dx = 1 if frame else 0
        v.spr(BUST_MAN, 1 + dx, 4, FIG)
        v.rect(5 + dx, 10, 4, 3, 'cloth')                              # the bundle on his shoulder
        v.rect(6 + dx, 9, 2, 1, 'skin')                                # a tiny head
        v.rect(3 + dx, 12, 3, 1, 'skin')                               # his hand on its back
    elif name == 'v1b':                                               # the crib and the nightlight
        v.rect(0, 16, 13, 3, 'floor')
        v.rect(1, 10, 11, 1, 'furn')
        for k in range(1, 12, 2):
            v.rect(k, 11, 1, 5, 'furn')
        v.rect(2, 12, 7, 3, 'cloth')
        v.rect(3, 12, 2, 1, 'skin')
        v.rect(8, 4, 4, 4, 'glow')
        v.rect(9, 5, 2, 2, 'light')
        v.rect(8, 8, 4, 1, 'furn')                                     # the shelf it stands on
    elif name == 's3a':                                               # Ilse at Hanna's kitchen table, drawing
        v.rect(6, 0, 1, 3, 'metal')                                    # lamp cord, shade, light
        v.rect(4, 3, 5, 1, 'metal')
        v.rect(5, 4, 3, 1, 'light')
        v.rect(3, 5, 7, 2, 'glow')
        v.rect(0, 14, 13, 2, 'furn')
        v.rect(0, 16, 13, 3, 'wall2')
        v.spr(BUST_CHILD, 0, 7, FIG)
        v.rect(6, 13, 6, 1, 'paper')                                   # her drawing: a house with lit windows
        v.rect(7, 10, 4, 3, 'paper')
        v.px(9, 9, 'paper')
        v.px(8, 11, 'light')
        v.px(10, 11, 'light')
        v.rect(12, 12, 1, 2, 'red')                                    # a crayon
        v.rect(5, 12, 1, 2, 'skin')                                    # her hand
    elif name == 's3b':                                               # the teacher's shelf: exercise books, a globe
        v.rect(0, 7, 13, 1, 'furn')
        for k in range(7):
            v.rect(1 + k, 3 + (k % 2), 1, 4 - (k % 2), 'paper' if k % 3 else 'cloth2')
        v.rect(9, 2, 3, 3, 'cloth2')                                   # the globe
        v.px(10, 3, 'plant')
        v.rect(10, 5, 1, 2, 'metal')
        v.rect(2, 10, 1, 1, 'metal')                                   # the empty coat hook
        v.rect(2, 11, 2, 1, 'metal')
        v.rect(7, 14, 4, 4, 'red')                                     # a pot ...
        v.rect(6, 10, 6, 4, 'plant')                                   # ... with a geranium
        v.px(7, 10, 'red')
        v.px(10, 11, 'red')
    elif name == 's2a':                                               # Pohl: the curtain that moves
        v.rect(0, 0, 13, 19, 'curtain')
        for k in range(0, 13, 3):
            v.rect(k, 0, 1, 19, 'wall2')
        if frame:
            v.rect(7, 0, 5, 19, 'wall2')
            v.rect(8, 4, 3, 4, 'face')                                 # a face behind the gap
            v.px(9, 5, 'fig')
            v.rect(7, 8, 4, 6, 'fig')
            v.rect(11, 0, 2, 19, 'curtain')
        else:
            v.rect(8, 0, 1, 19, 'wall2')
    elif name == 's2b':                                               # lace and an aspidistra
        v.rect(0, 0, 13, 19, 'lace')
        yy, xx = np.mgrid[0:19, 0:13]
        v.role[((xx + yy) % 3 == 0) & (yy < 13)] = 'wall2'
        v.rect(3, 9, 7, 6, 'plant')
        v.px(2, 10, 'plant')
        v.px(10, 9, 'plant')
        v.rect(4, 15, 5, 4, 'furn2')
    elif name == 's1a':                                               # the Mertens family at supper
        v.rect(6, 0, 1, 2, 'metal')
        v.rect(4, 2, 5, 1, 'metal')
        v.rect(5, 3, 3, 1, 'light')
        v.rect(0, 14, 13, 2, 'furn')
        v.rect(0, 16, 13, 3, 'wall2')
        v.spr(BUST_MAN, -1, 4, FIG)
        v.spr(BUST_WOMAN, 7, 4, FIG, flip=True)
        v.spr(BUST_KID, 4, 8, FIG)
        v.rect(2, 13, 2, 1, 'paper')                                   # plates, the pot
        v.rect(9, 13, 2, 1, 'paper')
        v.rect(5, 12, 3, 2, 'metal')
    elif name == 's1b':                                               # the conductor's jacket and cap; a child asleep
        v.rect(3, 0, 1, 2, 'metal')
        v.rect(1, 2, 6, 1, 'cloth2')                                   # cap with its visor
        v.rect(2, 1, 4, 1, 'cloth2')
        v.rect(6, 3, 2, 1, 'metal')
        v.rect(1, 4, 6, 9, 'cloth2')                                   # jacket on its hanger
        v.rect(3, 4, 2, 2, 'wall')
        for yb in (6, 8, 10):
            v.px(4, yb, 'light')
        v.rect(0, 15, 13, 4, 'furn')                                   # bed
        v.rect(1, 13, 11, 2, 'cloth')
        v.rect(9, 12, 2, 2, 'hair')
    elif name == 'sea':                                               # the lodge: Frau Kuhnert at her lamp, watching
        v.rect(0, 15, 13, 4, 'furn')
        v.rect(0, 5, 3, 3, 'curtain')
        v.rect(0, 8, 2, 7, 'curtain')
        v.rect(9, 8, 4, 4, 'glow')                                     # table lamp with a red shade
        v.rect(9, 7, 4, 1, 'red')
        v.rect(10, 6, 2, 1, 'red')
        v.px(10, 9, 'light')
        v.rect(10, 12, 1, 3, 'metal')
        v.spr(BUST_GRAN if frame else BUST_GRAN_FRONT, 3, 5, FIG)
    elif name == 'seb':                                               # her radio, a picture, the knitting
        v.rect(2, 2, 6, 5, 'furn2')
        v.rect(3, 3, 4, 3, 'paper')
        v.rect(0, 12, 13, 1, 'furn')
        v.rect(1, 7, 9, 5, 'furn2')                                    # radio on the shelf
        v.rect(2, 8, 5, 2, 'cloth')
        v.rect(2, 10, 4, 1, 'light')
        v.rect(0, 13, 13, 6, 'wall2')
        v.rect(9, 14, 3, 2, 'red')                                     # wool
        v.px(10, 13, 'metal')
    elif name in ('h3a', 'h3b'):                                      # sealed, empty since October
        v.rect(0, 0, 13, 19, 'wall2')
        v.rect(2, 3, 6, 7, 'wall')                                     # where a picture hung
        if name == 'h3a':
            v.rect(7, 12, 5, 1, 'furn')                                # a chair left behind
            v.rect(7, 13, 1, 5, 'furn')
            v.rect(11, 13, 1, 5, 'furn')
            v.rect(11, 8, 1, 4, 'furn')
        else:
            v.rect(0, 0, 13, 12, 'paper')                              # newspaper pasted on the glass
            for k in range(1, 11, 2):
                v.rect(1, k, 11, 1, 'wall2')
            v.rect(1, 1, 5, 3, 'wall2')
    elif name == 'h2a':                                               # Brettschneider's bed, empty: night shift
        v.rect(0, 14, 13, 2, 'furn')
        v.rect(0, 11, 10, 3, 'cloth')
        v.rect(0, 10, 3, 3, 'paper')
        v.rect(9, 16, 4, 3, 'furn')
        v.rect(9, 15, 4, 1, 'metal')                                   # the lunch tin he left
        v.rect(0, 16, 9, 3, 'floor')
    elif name == 'h2b':                                               # work jacket and cap on the hook
        v.rect(6, 1, 1, 2, 'metal')
        v.rect(3, 3, 7, 10, 'cloth')
        v.rect(3, 2, 7, 1, 'fig')
        v.rect(5, 3, 3, 2, 'wall')
        v.rect(0, 16, 13, 3, 'floor')
        v.rect(9, 14, 3, 2, 'furn2')                                   # boots
    elif name == 'h1a':                                               # the Kühns' card game
        v.rect(6, 0, 1, 2, 'metal')
        v.rect(4, 2, 5, 1, 'metal')
        v.rect(5, 3, 3, 1, 'light')
        v.rect(0, 14, 13, 2, 'furn')
        v.rect(0, 16, 13, 3, 'wall2')
        v.spr(BUST_OLD, -1, 4, FIG)
        v.spr(BUST_GRAN, 6, 4, FIG, flip=True)
        v.rect(5, 13, 3, 1, 'paper')                                   # the cards on the table
        v.px(4, 12, 'paper')
        if frame:
            v.rect(4, 9, 1, 3, 'skin')                                 # he slaps a card down
            v.rect(4, 8, 2, 1, 'paper')
    elif name == 'h1b':                                               # sofa, wall clock, the cat on the sill
        v.rect(5, 2, 3, 3, 'metal')
        v.px(6, 3, 'paper')
        v.rect(6, 5, 1, 3, 'metal')
        v.rect(0, 13, 13, 6, 'cloth2')
        v.rect(0, 12, 13, 1, 'cloth')
        v.rect(7, 13, 5, 5, 'fig')                                     # the cat
        v.px(7, 12, 'fig')
        v.px(10, 12, 'fig')
        v.rect(8, 12, 2, 1, 'fig')
        v.px(12, 17, 'fig')
        v.px(8, 14, 'light')
    elif name in ('h3c', 'h3d'):                                      # No. 3 goes on: sealed, the glass pasted over
        v.rect(0, 0, 13, 19, 'wall2')
        if name == 'h3c':
            v.rect(0, 0, 13, 13, 'paper')                              # newspaper on the glass, a strip of tape
            for k in range(1, 12, 2):
                v.rect(1, k, 11, 1, 'wall2')
            v.rect(7, 2, 5, 4, 'wall2')
            v.rect(0, 6, 13, 1, 'furn2')
        else:
            v.rect(3, 2, 5, 6, 'wall')                                 # where the mirror hung
            v.px(5, 1, 'metal')
            v.rect(6, 0, 1, 9, 'metal')                                # the bulb's empty wire
            v.rect(1, 15, 11, 1, 'paper')                              # a paper strip on the floor
    elif name == 'h2c':                                               # Brettschneider's kitchen: the coffee pot gone cold
        v.rect(0, 13, 13, 2, 'furn')
        v.rect(0, 15, 13, 4, 'wall2')
        v.rect(8, 9, 3, 4, 'metal')
        v.px(11, 10, 'metal')
        v.rect(8, 8, 3, 1, 'metal')
        v.rect(2, 2, 4, 5, 'paper')                                    # the calendar (the gasworks' shifts)
        v.rect(2, 2, 4, 1, 'red')
        v.rect(2, 11, 4, 2, 'furn2')                                   # the bread board
    elif name == 'h2d':                                               # his other window: the curtain half drawn, a geranium
        v.rect(0, 0, 5, 19, 'curtain')
        for k in (1, 3):
            v.rect(k, 0, 1, 19, 'lace')
        v.rect(6, 15, 6, 4, 'red')
        v.rect(7, 10, 5, 5, 'plant')
        v.px(8, 10, 'red')
        v.px(11, 11, 'red')
    elif name == 'h1c':                                               # the Kühns' kitchen: the kettle, the canary
        v.rect(6, 0, 1, 2, 'metal')
        v.rect(4, 2, 5, 1, 'metal')
        v.rect(5, 3, 3, 1, 'light')
        v.rect(0, 13, 13, 2, 'furn')
        v.rect(0, 15, 13, 4, 'wall2')
        v.rect(1, 10, 4, 3, 'metal')                                   # the kettle
        v.px(5, 10, 'metal')
        v.rect(2, 9, 2, 1, 'metal')
        v.rect(7, 4, 5, 7, 'metal')                                    # the cage, its bars, the bird
        for k in range(8, 12, 2):
            v.rect(k, 5, 1, 5, 'wall')
        v.rect(9, 7, 2, 2, 'light')
        v.rect(8, 11, 3, 2, 'furn2')
    elif name == 'h1d':                                               # their parlour: sideboard, radio, the photograph
        v.rect(1, 1, 3, 3, 'glow')
        v.rect(0, 11, 13, 1, 'furn')
        v.rect(0, 12, 13, 7, 'furn2')
        v.rect(2, 14, 4, 3, 'furn')
        v.rect(7, 14, 4, 3, 'furn')
        v.rect(3, 7, 6, 4, 'furn2')
        v.rect(4, 8, 3, 2, 'cloth')
        v.px(8, 9, 'light')
        v.rect(9, 2, 3, 4, 'paper')
        v.rect(10, 3, 1, 2, 'fig')
    elif name == 'hea':                                               # the back hall: a bare bulb over the stairs
        v.rect(6, 0, 1, 3, 'metal')
        v.rect(4, 3, 5, 4, 'glow')
        v.rect(6, 4, 1, 2, 'light')
        v.rect(0, 13, 13, 1, 'furn')
        for k in range(2, 12, 3):
            v.rect(k, 14, 1, 5, 'furn')
        v.rect(0, 17, 13, 2, 'wall2')
    return v


# windows of the facade: (room, name, x, y) -- WIN_W x WIN_H incl. the frame
WINDOWS = []
for _w, _rows in (('v', ('3', '2', '1')), ('s', ('3', '2', '1')), ('h', ('3', '2', '1'))):
    for _f in _rows:
        _y, _h = ROWS[_f]
        for _k, _dx in (('a', 6), ('b', 30)):
            WINDOWS.append((_w + _f, _w + _f + _k, WING_X[_w] + _dx, _y + 10))
for _f in ('3', '2', '1'):                                            # the back house right of its stairs
    _y, _h = ROWS[_f]
    for _k, _dx in (('c', 8), ('d', 36)):
        WINDOWS.append(('h' + _f, 'h' + _f + _k, EXT[0] + _dx, _y + 10))
WINDOWS.append(('se', 'sea', WING_X['s'] + 6, ROWS['e'][0] + 10))
WINDOWS.append(('se', 'seb', WING_X['s'] + 30, ROWS['e'][0] + 10))
WINDOWS.append(('he', 'hea', WING_X['h'] + 6, ROWS['e'][0] + 10))
ANIMS = ['v3a', 'v1a', 's2a', 'sea', 'h1a']


def window_mode(room: str, view: str) -> str:
    if view == 'overview':
        return 'neutral'
    return 'lit' if room in LIT else ('dim' if room in DIM else 'dark')


def paint_window(cv: Canvas, name: str, x: int, y: int, mode: str, frame: int = 0):
    v = vig_window(name, frame)
    if mode == 'dim':                                                 # a weak light far behind the curtain
        a = v.render('lit', seed=x + y).astype(np.float32)
        b = v.render('dark', seed=x + y).astype(np.float32)
        arr = np.clip(a * 0.34 + b * 0.66, 0, 255).astype(np.uint8)
        arr[..., 3] = 255
    else:
        arr = v.render(mode, seed=x + y)
    cv.blend(np.ones((IN_H, IN_W), bool), x + 1, y + 1, arr)
    if mode == 'dark':                                                # cold glass: a pale diagonal of the sky
        for k in range(IN_H):
            xx = IN_W - 2 - k // 2
            if 0 <= xx < IN_W:
                cv.px(x + 1 + xx, y + 1 + k, C('#3A4A62'), 0.45)
    fc = C(FRAME_N[mode])
    cv.rect(x, y, WIN_W, 1, fc)
    cv.rect(x, y + WIN_H - 1, WIN_W, 1, fc)
    cv.rect(x, y, 1, WIN_H, fc)
    cv.rect(x + WIN_W - 1, y, 1, WIN_H, fc)
    cv.rect(x + MULL_X, y + 1, 1, WIN_H - 2, fc)                       # mullion
    cv.rect(x + 1, y + TRANS_Y, WIN_W - 2, 1, fc)                       # transom


def plaster(w: int, h: int, ramp, seed: int, base: float = 2.2) -> np.ndarray:
    tone = base + (noise(w, h, 14, seed) - 0.5) * 0.9 + (noise(w, h, 3, seed + 1, 2) - 0.5) * 0.45
    return dither(w, h, tone, ramp)


def bricks(w: int, h: int, ramp, seed: int) -> np.ndarray:
    yy, xx = np.mgrid[0:h, 0:w]
    rng = np.random.default_rng(seed)
    tone = 2.1 + (noise(w, h, 10, seed) - 0.5) * 0.7
    row = yy // 3
    off = (row % 2) * 4
    brick_id = row * 1000 + (xx + off) // 8
    jitter = rng.uniform(-0.5, 0.5, int(brick_id.max()) + 1)
    tone = tone + jitter[brick_id]
    mortar = (yy % 3 == 2) | ((xx + off) % 8 == 7)
    tone = np.where(mortar, 0.6, tone)
    return dither(w, h, tone, ramp)


def facade(cv: Canvas, x0: int, x1: int, ramp, seed: int, snow: np.ndarray):
    """Courtyard plaster from the top floor down to the ground for x0..x1, a cornice band (snow on it) per storey."""
    y0, y1 = ROWS['3'][0], GROUND
    w = x1 - x0
    cv.blend(np.ones((y1 - y0, w), bool), x0, y0, plaster(w, y1 - y0, ramp, seed))
    for f in ('3', '2', '1', 'e'):
        fy, _ = ROWS[f]
        cv.rect(x0, fy, w, 1, C(ramp[3]), 0.8)
        cv.rect(x0, fy + 1, w, 1, C(ramp[0]), 0.6)
        cv.rect(x0, fy - 1, w, 1, C(SNOW[2]))
        snow[fy - 1, x0:x1] = True


BRICK_UNDER = ['#2E2624', '#3A302C', '#463A34', '#52443C', '#5E4E44']   # old brick under the plaster, sooted


def spall(cv: Canvas, x: int, y: int, w: int, h: int, seed: int, ramp):
    """A patch where the plaster has fallen and the sooted bricks show: a ragged outline (never an oval blob), the
    broken plaster edge a little lighter, a few loose crumbs below."""
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    d = np.hypot((xx - w / 2.0) / (w / 2.0), (yy - h / 2.0) / (h / 2.0))
    d = d + (noise(w, h, 2.5, seed) - 0.5) * 0.9 + (noise(w, h, 1.2, seed + 3) - 0.5) * 0.35
    hole = d < 0.8
    cv.blend(hole, x, y, bricks(w, h, BRICK_UNDER, seed), 0.9)
    cv.blend((d >= 0.8) & (d < 0.95), x, y, C(ramp[4]), 0.55)
    rng = np.random.default_rng(seed)
    for _ in range(3):
        cv.px(x + int(rng.integers(1, w - 1)), y + h + int(rng.integers(0, 3)), C(ramp[3]), 0.6)


def house_base() -> tuple[Canvas, np.ndarray]:
    """Everything that does not change with the light (later graded for 22.40); returns (canvas, snow mask)."""
    cv = Canvas(HW, HH)
    snow = np.zeros((HH, HW), bool)
    yy, xx = np.mgrid[0:HH, 0:HW].astype(np.float32)
    # sky with stars and haze; the dome of the Great Hall far away, between the front and the side wing's gables
    tone = 0.6 + (yy / 60.0) * 2.4 + (noise(HW, HH, 40, 9100) - 0.5) * 0.5
    cv.blend(np.ones((HH, HW), bool), 0, 0, dither(HW, HH, tone, SKY))
    dc = (90, 21)
    dome = (np.hypot((xx - dc[0]) / 21.0, (yy - dc[1]) / 13.0) <= 1.0) & (yy <= dc[1])
    dome |= (np.abs(xx - dc[0]) <= 24) & (yy > dc[1]) & (yy < dc[1] + 4)
    lantern = (np.abs(xx - dc[0]) <= 2) & (yy > dc[1] - 18) & (yy <= dc[1] - 12)
    cv.blend(dome | lantern, 0, 0, C(SKY[3]), 0.8)
    cv.blend(dome & (((xx - dc[0]) % 6) == 0) & (yy > dc[1] - 12), 0, 0, C(SKY[4]), 0.45)        # ribs in the haze
    cv.blend((np.abs(xx - dc[0]) <= 1) & (yy > dc[1] - 22) & (yy <= dc[1] - 18), 0, 0, C(SKY[4]), 0.5)
    rng = np.random.default_rng(9101)
    for _ in range(40):
        sx, sy = int(rng.integers(0, HW)), int(rng.integers(0, 30))
        cv.px(sx, sy, C('#9AA6C0'), 0.5 + 0.4 * rng.random())
    # the three wings; the Hinterhaus goes on right of its stairwell over Pietsch's souterrain -- plaster all of it,
    # as the courtyard shows it (round 10 review: no brick back house, no painted fire wall)
    facade(cv, WING_X['v'], WING_X['v'] + WING_W, PL_V, 9110 + ord('v'), snow)
    facade(cv, WING_X['s'], WING_X['s'] + WING_W, PL_S, 9110 + ord('s'), snow)
    facade(cv, WING_X['h'], HW, PL_H, 9110 + ord('h'), snow)
    for gy in range(ROWS['e'][0] + 4, GROUND, 5):                      # the front wing's rusticated ground floor
        cv.rect(WING_X['v'], gy, FLAT_W, 1, C(PL_V[1]), 0.8)
    spall(cv, WING_X['s'] + 32, 137, 18, 11, 9120, PL_S)               # fallen plaster in the side wing
    spall(cv, EXT[0] + 23, 101, 14, 10, 9121, PL_H)                    # ... and on the back house
    spall(cv, WING_X['h'] + 2, 60, 9, 12, 9122, PL_H)
    for (x0, ramp) in ((WING_X['v'], PL_V), (WING_X['s'], PL_S), (WING_X['h'], PL_H), (HW - 5, PL_H)):
        cv.rect(x0 + 1, ROWS['3'][0], 2, GROUND - ROWS['3'][0], C(STEEL[1]))      # drainpipes
        for k in range(ROWS['3'][0], GROUND, 9):
            cv.rect(x0, k, 4, 1, C(STEEL[2]))
    # soot streaks under some windows
    for (rx, ry) in ((WING_X['v'] + 12, 82), (WING_X['s'] + 35, 120), (WING_X['h'] + 12, 158), (EXT[0] + 34, 82)):
        for k in range(8):
            cv.px(rx + (k % 2), ry + k, C(NIGHT), 0.25)
    # window sills with snow, lintels
    for (room, name, x, y) in WINDOWS:
        ramp = PL_V if room[0] == 'v' else PL_S if room[0] == 's' else PL_H
        cv.rect(x - 1, y - 2, WIN_W + 2, 2, C(ramp[3]), 0.9)
        cv.rect(x - 1, y + WIN_H, WIN_W + 2, 2, C(STONE[3]))
        cv.rect(x - 1, y + WIN_H, WIN_W + 2, 1, C(SNOW[3]))
        snow[y + WIN_H, x - 1:x + WIN_W + 1] = True
        if room[0] == 'v':
            cv.rect(x + MULL_X - 1, y - 3, 3, 2, C(PL_V[4]))            # keystone
    # the card box of the lodge on the sill under the radio window
    bx, by = WING_X['s'] + 30, ROWS['e'][0] + 10 + WIN_H - 4
    cv.rect(bx + 2, by, 11, 4, C(WOOD_L[2]))
    cv.rect(bx + 3, by - 1, 9, 1, C(PAPER[4]))
    cv.rect(bx + 2, by, 11, 1, C(WOOD_L[3]))
    # seams between the wings: inner corners with a downpipe, fire walls above the roofs; right of the back stairs
    # the cut wall of the stairwell (the house goes on)
    for sx in SEAMS[:2]:
        cv.rect(sx, RIDGE - 2, 4, GROUND - RIDGE + 2, C(STONE[1]))
        cv.rect(sx + 1, RIDGE + 10, 1, GROUND - RIDGE - 10, C(STEEL[1]))
        cv.rect(sx, RIDGE - 3, 4, 1, C(SNOW[2]))
        snow[RIDGE - 3, sx:sx + 4] = True
    cv.rect(SEAMS[2], ROWS['3'][0], 4, GROUND - ROWS['3'][0], C(STONE[1]))
    cv.rect(SEAMS[2] + 3, ROWS['3'][0], 1, GROUND - ROWS['3'][0], C(PL_H[2]), 0.6)
    # the souterrain's shop sign over its windows (the courtyard has the same board): SCHUHMACHEREI / PIETSCH
    fx0, fx1 = EXT[0] + 1, EXT[1] - 1
    cv.rect(fx0, 175, fx1 - fx0, 14, C('#1C2024'))
    cv.rect(fx0, 175, fx1 - fx0, 1, C(PL_H[4]), 0.8)
    cv.rect(fx0, 188, fx1 - fx0, 1, C(NIGHT), 0.7)
    for k in (fx0 + 6, fx1 - 7):                                       # its two iron brackets
        cv.rect(k, 172, 1, 3, C(STEEL[2]))
    text(cv, 'SCHUHMACHEREI', (fx0 + fx1) // 2, 177, '#D8CDA8', align='center', a=0.95)
    text(cv, 'PIETSCH', (fx0 + fx1) // 2, 183, '#D8CDA8', align='center', a=0.95)
    cv.rect(EXT[0] + 44, 167, 5, 2, C(STEEL[2]))                       # a wall lamp over the sign (off)
    cv.rect(EXT[0] + 45, 169, 3, 2, C('#C8B890'), 0.8)
    for w in 'vsh':
        stairwell(cv, WING_X[w], w)
        attic(cv, w, snow)
    ground_floor(cv, snow)
    cellars(cv)
    workshop(cv, 'neutral')
    # snow band where the courtyard meets the facades; snowflakes
    cv.rect(0, GROUND - 2, HW, 2, C(SNOW[2]))
    cv.rect(0, GROUND - 3, HW, 1, C(SNOW[3]), 0.6)
    snow[GROUND - 3:GROUND, :] = True
    flakes = np.random.default_rng(9199)
    for _ in range(140):
        fx, fy = int(flakes.integers(0, HW)), int(flakes.integers(0, GROUND))
        cv.px(fx, fy, C(SNOW[3]), 0.35 + 0.35 * flakes.random())
    return cv, snow


def flight(cv: Canvas, lo, hi, near: bool):
    """A flight between two feet points (lo the lower end, hi the upper): stepped treads on the line the figures
    walk, the riser band and the stringer under them; the near flight (in front) carries a handrail with
    balusters, the far one (behind) is darker."""
    (x0, y0), (x1, y1) = lo, hi
    rise = y0 - y1
    run = abs(x1 - x0)
    n = max(3, int(round(rise / 2.0)))
    sgn = 1 if x1 > x0 else -1
    tread, body, string = (WOOD[4], WOOD[2], WOOD[0]) if near else (WOOD[3], WOOD[1], NIGHT)
    for c in range(run + 1):
        x = x0 + sgn * c
        k = min(n - 1, int(c * n / max(1, run)))
        ty = int(round(y0 - (k + 0.5) * rise / n))
        cv.rect(x, ty, 1, 1, C(tread))
        cv.rect(x, ty + 1, 1, 3, C(body))
        cv.rect(x, ty + 4, 1, 1, C(string), 0.9)
    if near:
        for c in range(run + 1):
            x = x0 + sgn * c
            ny = y0 - rise * c / max(1, run)
            cv.px(x, int(round(ny - 9)), C(WOOD[0]))
            if c % 3 == 1:
                cv.rect(x, int(round(ny - 8)), 1, 7, C(WOOD[1]), 0.8)


def stairwell(cv: Canvas, wx: int, w: str):
    """The stairwell cut open, storeys e .. 3: whitewash over an oil-paint dado, per storey the far flight (behind),
    the half landing, the flat door, the near flight (in front) and the landing; on the ground floor the opening of
    the steep cellar stair.  The geometry is stair_points(): the markers walk exactly these flights."""
    sx = wx + FLAT_W
    sw = WING_W - FLAT_W
    for f in ('e', '1', '2', '3'):
        fy, fh = ROWS[f]
        bot = fy + fh
        cv.rect(sx, fy, sw, fh, C(STAIR_WALL[2]))
        cv.rect(sx, bot - 14, sw, 14, C(STAIR_WALL[1]))
        cv.rect(sx, bot - 15, sw, 1, C(STAIR_WALL[0]))
        cv.rect(sx + sw - 2, fy + 4, 1, 3, C(STEEL[1]))               # a bulb on its wire over the half landing
        cv.px(sx + sw - 2, fy + 7, C('#B8B098'))
        foot, turn, top = stair_points(w, f)
        flight(cv, turn, top, near=False)
        cv.rect(turn[0] - 1, turn[1], sx + sw - turn[0] + 1, 2, C(WOOD[3]))           # half landing
        cv.rect(turn[0] - 1, turn[1] + 2, sx + sw - turn[0] + 1, 1, C(WOOD[1]))
        if f != 'e':                                                  # the flat door on the landing
            room = w + f
            leaf = PL_S[1] if w == 's' else WOOD[2]
            dy0 = bot - 24
            cv.rect(sx + 1, dy0, 6, 22, C(WOOD[0]))
            cv.rect(sx + 2, dy0 + 1, 4, 21, C(leaf))
            cv.rect(sx + 2, dy0 + 3, 4, 6, C(WOOD[1]), 0.5)           # panels
            cv.rect(sx + 2, dy0 + 12, 4, 7, C(WOOD[1]), 0.5)
            cv.px(sx + 5, dy0 + 11, C(BRASS[3]))                       # knob
            cv.rect(sx + 3, dy0 + 10, 2, 1, C(BRASS[3]))               # nameplate
            if room == 's2':
                cv.px(sx + 3, dy0 + 6, C(BRASS[4]))                    # the spy hole
                cv.px(sx + 4, dy0 + 6, C(NIGHT))
            if room == 'h3':
                cv.line(sx + 1, dy0 + 2, sx + 6, dy0 + 14, C(PAPER[4]))   # the seal across the door
                cv.px(sx + 4, dy0 + 8, C(RED))
        flight(cv, foot, turn, near=True)
        cv.rect(sx, fy, 1, fh, C(NIGHT), 0.55)                        # the cut wall
        if f == 'e':                                                  # the ground landing and the cellar stair's well
            cv.rect(sx, bot - 2, 13, 2, C(STONE[3]))
            cv.rect(sx + 13, bot - 2, sw - 13, 2, C(NIGHT), 0.9)
            cv.rect(sx + 13, bot - 10, 1, 8, C(STEEL[2]))
            cv.rect(sx + 13, bot - 10, sw - 14, 1, C(STEEL[2]))
        else:
            cv.rect(sx, bot - 2, sw, 2, C(STONE[3]))


def attic(cv: Canvas, w: str, snow: np.ndarray):
    """Roof with the drying loft cut open: knee walls, rafters, the floor with the stair's well, laundry (s, h --
    Tuesday is washing day) or junk (v); chimneys, aerials, the hatch; snow on the roof.  The Hinterhaus has one
    long roof over its stairs and the part above the souterrain."""
    x0, x1 = roof_span(w)
    y1 = ROWS['d'][0] + ROWS['d'][1]
    mid, half = (x0 + x1) / 2.0, (x1 - x0) / 2.0
    yy, xx = np.mgrid[0:HH, 0:HW].astype(np.float32)
    roof_top = RIDGE + (np.abs(xx - mid) / half) * (KNEE - RIDGE)
    roof = (xx >= x0) & (xx < x1) & (yy >= roof_top) & (yy < y1)
    cv.blend(roof, 0, 0, C(ROOF[2]))
    inner_top = RIDGE + 3 + (np.abs(xx - mid) / half) * (KNEE - RIDGE - 3)
    inner = (xx >= x0 + 2) & (xx < x1 - 2) & (yy >= inner_top) & (yy < FLOOR_ATTIC)
    room = Canvas(HW, HH)
    tone = 1.4 + (noise(HW, HH, 9, 9200 + x0) - 0.5) * 0.6
    room.blend(inner, 0, 0, dither(HW, HH, tone, WOOD))
    for k in range(int(x0) + 6, int(x1) - 4, 8):                      # rafters
        top = RIDGE + 3 + (abs(k - mid) / half) * (KNEE - RIDGE - 3)
        room.rect(k, int(top), 1, int(FLOOR_ATTIC - top), C(WOOD[1]))
    room.rect(int(mid - half * 0.4), 26, int(half * 0.8), 1, C(WOOD[3]))     # collar beam under the ridge
    room.rect(x0 + 2, FLOOR_ATTIC, x1 - x0 - 4, 1, C(WOOD[4]))                # floorboards
    room.rect(x0 + 2, FLOOR_ATTIC + 1, x1 - x0 - 4, 1, C(WOOD[1]))
    cv.blit(room, 0, 0)
    if w in ('s', 'h'):                                               # the stair comes up through the floor
        _, _, top = stair_points(w, '3')
        cv.rect(top[0], FLOOR_ATTIC, 14, 2, C(NIGHT), 0.85)
        cv.rect(top[0] + 14, FLOOR_ATTIC - 8, 1, 8, C(WOOD[0]))
        cv.rect(top[0] + 4, FLOOR_ATTIC - 8, 11, 1, C(WOOD[0]))
    else:
        _, _, top = stair_points(w, '3')
        cv.rect(top[0], FLOOR_ATTIC, 14, 2, C(NIGHT), 0.85)
        cv.rect(top[0] + 14, FLOOR_ATTIC - 8, 1, 8, C(WOOD[0]))
    edge = (xx >= x0 - 1) & (xx < x1 + 1) & (yy >= roof_top - 2) & (yy < roof_top)
    cv.blend(edge, 0, 0, C(SNOW[2]))
    snow |= edge
    if w in ('s', 'h'):                                               # Tuesday is washing day: the lofts are open
        k = 0
        for lx in range(int(x0) + 8, int(x1) - 12, 11):
            if w == 'h' and abs(lx + 3 - (WING_X['h'] + NODE_DX)) < 9:
                continue                                              # the way from the stairs stays free
            cv.rect(lx - 2, 35, 12, 1, C(STEEL[3]))
            hh = 6 + (k * 3) % 5
            cv.rect(lx, 36, 7, hh, C(PAPER[4] if k % 2 else '#C8CED6'))
            cv.rect(lx + 6, 36, 1, hh, C(PAPER[2]))
            cv.rect(lx, 36 + hh - 1, 7, 1, C(PAPER[2]))
            if k % 3 == 2:                                            # stockings and a shirt among the sheets
                cv.rect(lx + 2, 36 + hh, 1, 3, C('#7A6A5A'))
            k += 1
        bx = int(x0) + 50 if w == 's' else int(x0) + 20
        cv.rect(bx, FLOOR_ATTIC - 4, 7, 4, C(WOOD_L[2]))              # a laundry basket
        cv.rect(bx + 1, FLOOR_ATTIC - 5, 5, 1, C(PAPER[3]))
        if w == 'h':
            cv.rect(int(mid) + 22, RIDGE + 6, 7, 2, C(SKY[3]))        # roof hatch
            cv.rect(int(mid) + 22, RIDGE + 5, 7, 1, C(SNOW[2]))
            cv.rect(EXT[0] + 30, FLOOR_ATTIC - 6, 9, 6, C('#5A4E3A'))  # an old trunk
            cv.rect(EXT[0] + 30, FLOOR_ATTIC - 6, 9, 1, C(BRASS[2]))
    else:                                                              # the front loft: junk
        cv.rect(x0 + 8, FLOOR_ATTIC - 7, 8, 7, C(WOOD_L[1]))
        cv.rect(x0 + 9, FLOOR_ATTIC - 11, 7, 4, C(WOOD_L[2]))
        cv.rect(x0 + 22, FLOOR_ATTIC - 8, 9, 5, C('#2A3236'))          # a pram without wheels
        cv.rect(x0 + 22, FLOOR_ATTIC - 11, 4, 3, C('#2A3236'))
        cv.rect(x0 + 36, FLOOR_ATTIC - 6, 5, 1, C(WOOD[3]))            # broken chair
        cv.rect(x0 + 36, FLOOR_ATTIC - 5, 1, 5, C(WOOD[3]))
        cv.rect(x0 + 40, FLOOR_ATTIC - 10, 1, 10, C(WOOD[3]))
    # chimneys (the back house has three), television aerials (1964)
    chims = [(x0 + 16, w != 's'), (x0 + 58, True)] if w != 'h' else [(x0 + 16, True), (x0 + 66, False), (x0 + 118, True)]
    for (cx, smoke) in chims:
        top = int(RIDGE + (abs(cx + 2 - mid) / half) * (KNEE - RIDGE)) - 12
        cv.rect(cx, top, 5, 14, C(BRICK[2]))
        cv.rect(cx - 1, top, 7, 2, C(BRICK[3]))
        cv.rect(cx - 1, top - 1, 7, 1, C(SNOW[2]))
        snow[top - 1, cx - 1:cx + 6] = True
        if smoke:
            for k in range(8):
                cv.px(cx + 2 + int(2 * math.sin(k / 1.6)), top - 2 - k, C('#5A6474'), 0.45 - k * 0.04)
    for ax in ((int(mid) + 6,) if w == 'v' else (int(mid) - 9,) if w == 's' else (int(mid) - 30, int(mid) + 40)):
        top = int(RIDGE + (abs(ax - mid) / half) * (KNEE - RIDGE))
        cv.rect(ax, top - 13, 1, 13, C(STEEL[2]))
        for (ww, dy) in ((9, 12), (7, 9), (5, 6)):
            cv.rect(ax - ww // 2, top - dy, ww, 1, C(STEEL[2]))
    for sx in SEAMS[:2]:                                               # doors between the lofts (in the fire walls)
        cv.rect(sx, 31, 4, FLOOR_ATTIC - 31, C(NIGHT), 0.85)
        cv.rect(sx, 30, 4, 1, C(WOOD[3]))


def ground_floor(cv: Canvas, snow: np.ndarray):
    """ve: the gate passage (vault painted per light in passage()); se: the lodge (windows per light); he: the back
    house's door; against the walls the bins and a bicycle."""
    fy, fh = ROWS['e']
    vx = WING_X['v']
    cv.rect(vx + 3, fy + 3, 48, 2, C(PL_V[4]))
    dx = WING_X['h'] + 24                                              # the back house's door to the courtyard
    cv.rect(dx - 1, GROUND - 23, 14, 23, C(STONE[2]))
    cv.rect(dx, GROUND - 22, 12, 22, C(WOOD[2]))
    cv.rect(dx + 1, GROUND - 21, 4, 8, C(DARKWIN[2]))
    cv.rect(dx + 7, GROUND - 21, 4, 8, C(DARKWIN[2]))
    cv.rect(dx + 6, GROUND - 22, 1, 22, C(WOOD[0]))
    cv.rect(dx - 1, GROUND - 24, 14, 1, C(SNOW[2]))
    snow[GROUND - 24, dx - 1:dx + 13] = True
    for bx in (WING_X['h'] + 38, WING_X['h'] + 46):                    # zinc bins by the back door
        cv.rect(bx, GROUND - 9, 7, 9, C(STEEL[2]))
        cv.rect(bx - 1, GROUND - 10, 9, 1, C(STEEL[3]))
        cv.rect(bx - 1, GROUND - 11, 9, 1, C(SNOW[3]))
        snow[GROUND - 11, bx - 1:bx + 8] = True
        for k in range(bx + 1, bx + 7, 2):
            cv.rect(k, GROUND - 8, 1, 7, C(STEEL[1]))
    bkx = WING_X['s'] + 2                                              # a bicycle under the lodge window
    for cxx in (bkx + 3, bkx + 13):
        cv.blend(ring(2.6, 3.4, 9), cxx - 4, GROUND - 9, C(STEEL[0]))
    cv.line(bkx + 3, GROUND - 5, bkx + 8, GROUND - 8, C(STEEL[1]))
    cv.line(bkx + 8, GROUND - 8, bkx + 13, GROUND - 5, C(STEEL[1]))
    cv.line(bkx + 8, GROUND - 8, bkx + 6, GROUND - 11, C(STEEL[1]))
    cv.rect(bkx + 5, GROUND - 12, 3, 1, C(STEEL[0]))
    cv.rect(bkx + 11, GROUND - 10, 3, 1, C(STEEL[1]))


def passage(cv: Canvas, mode: str):
    """The gate passage (Durchfahrt): vault, the street beyond, the notice, Kuhnert in his hat under the lamp."""
    x0, y0 = WING_X['v'] + 4, ROWS['e'][0] + 6
    w, h = 46, GROUND - (ROWS['e'][0] + 6)
    p = Canvas(w, h)
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    arch = (yy >= 6 - 6 * np.sqrt(np.clip(1 - ((xx - w / 2) / (w / 2)) ** 2, 0, 1)))
    lit = mode == 'lit'
    vault = SODIUM if lit else ['#1A1A1E', '#24242A', '#303038', '#3E3E48', '#4E4E58']
    d = np.hypot(xx - w / 2, (yy - 6) * 1.2)
    tone = (3.6 - d / 9.0) if lit else (2.2 - d / 30.0)
    p.blend(arch, 0, 0, dither(w, h, np.clip(tone, 0, 4), vault))
    # the far end: the street, cold light
    p.rect(w // 2 - 7, 9, 14, h - 9, C('#3A4A62' if not lit else '#2A3446'))
    p.rect(w // 2 - 7, h - 6, 14, 6, C(SNOW[1]))
    p.rect(w // 2 + 4, 12, 1, h - 18, C(STEEL[1]))                       # street lamp post beyond
    p.rect(w // 2 + 3, 11, 3, 2, C('#D8E4F0'))
    # converging side walls
    for k in range(h):
        p.px(int(k * 0.3), k, C(STONE[1]))
        p.px(w - 1 - int(k * 0.3), k, C(STONE[1]))
    # the notice with the pinned site plan on the left wall
    p.rect(5, 18, 6, 8, C(PAPER[4] if not lit else LAMPW[4]))
    p.rect(6, 20, 4, 1, C(INK))
    p.rect(6, 22, 3, 2, C(INK_B))
    p.px(8, 18, C(RED))
    # cobbles
    for k in range(0, w, 3):
        p.px(k, h - 1 - (k % 2), C(STONE[3]))
    # the lamp in the vault
    p.rect(w // 2, 0, 1, 4, C(STEEL[1]))
    p.rect(w // 2 - 2, 4, 5, 1, C(STEEL[2]))
    p.px(w // 2, 5, C(SODIUM[4] if lit else '#C8B890'))
    # Kuhnert, Blockleiter: hat, brown work coat, the card box under his arm
    kun = ['.kkkk...', 'kkkkkkk.', '.hsss...', '.hsgs...', '..sss...', '...s....', '.ccccc..', 'cccccc..',
           'cccccbb.', 'cccccbb.', '.cccccc.', '.cccc...', '.ccyc...', '.cccc...', '.cc.cc..', '.cc.cc..', '.dd.dd..']
    if lit:
        leg = {'k': '#2A1A0C', 'h': '#E8D0A0', 's': '#E0A060', 'g': '#FFE2A8', 'c': '#5A3414', 'b': '#7A4A1A',
               'y': '#C89040', 'd': '#140C06'}
    else:
        leg = {'k': '#3A3424', 'h': '#C8C8C0', 's': '#B08870', 'g': '#D8E0E8', 'c': '#5A4632', 'b': '#7A5232',
               'y': '#8A7A50', 'd': '#1A1610'}
    kk = sprite(kun, leg)
    p.blit(kk, w // 2 + 5, h - kk.h)
    cv.blend(np.ones((h, w), bool), x0, y0, p.c)
    # the arch frame
    for k in range(w):
        ay = int(6 - 6 * math.sqrt(max(0.0, 1 - ((k - w / 2) / (w / 2)) ** 2)))
        cv.rect(x0 + k, y0 + ay - 2, 1, 2, C(PL_V[4]))


def cellars(cv: Canvas):
    """Below the courtyard: the soil, brick vaults, the slatted coal cellars with their numbers and padlocks, the
    corridor through all wings (doors in the walls), a bicycle (front), the sled and the potato sacks (side), the
    shelf of preserving jars and the old pram (back), the steep cellar stairs, the door to Pietsch's workshop."""
    _, h = ROWS['k']
    cv.rect(0, GROUND, HW, HH - GROUND, C(STONE[1]))
    soil = dither(HW, HH - GROUND, 1.4 + (noise(HW, HH - GROUND, 5, 9300) - 0.5) * 1.2, STONE)
    cv.blend(np.ones((HH - GROUND, HW), bool), 0, GROUND, soil)
    for w in 'vsh':
        wx = WING_X[w]
        rx0, ry0, rw, rh = wx + 2, GROUND + 3, WING_W - 4, h - 3
        room = Canvas(rw, rh)
        room.blend(np.ones((rh, rw), bool), 0, 0, bricks(rw, rh, ['#1E1814', '#28201A', '#322820', '#3C3026'], 9310 + wx))
        yy, xx = np.mgrid[0:rh, 0:rw].astype(np.float32)
        vault = yy < 5 - 5 * np.sqrt(np.clip(1 - ((xx - rw / 2) / (rw / 2)) ** 2, 0, 1))
        room.blend(vault, 0, 0, C(STONE[1]))
        room.rect(0, rh - 2, rw, 2, C(STONE[3]))
        for k in range(3, 37, 3):                                      # slatted coal cellars
            room.rect(k, 8, 1, rh - 10, C(WOOD[3]))
        room.rect(3, 8, 34, 1, C(WOOD[3]))
        room.rect(3, 15, 34, 1, C(WOOD[2]))
        room.rect(4, rh - 9, 32, 7, C('#0E0E10'))                       # coal
        for k in range(6, 35, 4):
            room.px(k, rh - 10, C('#2A2A30'))
        for i, dx in enumerate((9, 21, 33)):                           # numbers (paper) and padlocks (brass)
            room.rect(dx - 1, 10, 3, 2, C(PAPER[3]))
            room.px(dx, 10, C(INK))
            room.px(dx, 17, C(BRASS[3]))
        if w == 'v':                                                   # a bicycle
            for cxx in (40, 49):
                room.blend(ring(2.6, 3.4, 9), cxx - 4, rh - 11, C(STEEL[3]))
            room.line(40, rh - 7, 45, rh - 10, C(STEEL[3]))
            room.line(45, rh - 10, 49, rh - 7, C(STEEL[3]))
            room.rect(44, rh - 12, 3, 1, C(STEEL[2]))
        if w == 's':                                                   # the sled, potato sacks
            room.line(38, rh - 4, 43, rh - 16, C(WOOD_L[3]))
            room.line(41, rh - 4, 46, rh - 16, C(WOOD_L[3]))
            room.rect(44, rh - 7, 5, 5, C('#6A5A3A'))
            room.rect(48, rh - 6, 4, 4, C('#5E5034'))
        if w == 'h':                                                   # preserving jars on a shelf, an old pram
            room.rect(38, 12, 12, 1, C(WOOD[3]))
            room.rect(38, 18, 12, 1, C(WOOD[3]))
            for k in range(39, 49, 3):
                room.rect(k, 9, 2, 3, C('#5A6E58'))
                room.rect(k, 15, 2, 3, C('#7A3A2A'))
            room.rect(38, rh - 8, 9, 4, C('#2A3236'))
            room.rect(38, rh - 11, 4, 3, C('#2A3236'))
            room.blend(ring(1.2, 2.0, 5), 38, rh - 5, C(STEEL[2]))
            room.blend(ring(1.2, 2.0, 5), 43, rh - 5, C(STEEL[2]))
        room.rect(28, 3, 1, 3, C(STEEL[1]))                             # bulb (off)
        room.px(28, 6, C('#5A5A50'))
        cv.blit(room, rx0, ry0)
        for kx in (wx + 10, wx + 30):                                  # cellar windows in their light wells
            cv.rect(kx, GROUND + 1, 9, 4, C(DARKWIN[1]))
            for b in range(kx + 1, kx + 9, 2):
                cv.rect(b, GROUND + 1, 1, 4, C(STEEL[2]))
        foot, head = cellar_stair(w)                                   # the steep cellar stair to the ground landing
        flight(cv, foot, head, near=True)
    for sx in SEAMS:                                                   # the corridor doors through the wing walls
        cv.rect(sx - 1, FLOOR_CELLAR - 20, 6, 20, C('#0A0A0C'))
        cv.rect(sx - 1, FLOOR_CELLAR - 21, 6, 1, C(WOOD[3]))
    cv.rect(SEAMS[2] - 1, FLOOR_CELLAR - 20, 1, 20, C(WOOD[2]))          # Pietsch's door stands ajar
    cv.rect(SEAMS[2] - 2, FLOOR_CELLAR - 19, 1, 18, C(WOOD[3]))


def workshop_vig() -> Vig:
    """Pietsch's workshop painted once with roles (so every light shows the same things -- nothing pops in when the
    candle is lit): whitewash, the two windows half above the courtyard, the shelves of lasts and of shoes waiting with
    their tags, the tool rack and the hanging lamp, the bench with a boot on the last, nails and glue, the candle stub,
    the arm sewing machine, his stool, the apron on its nail, the stove, a crate of shoes.  Pietsch himself is not
    shown (C4P2 §5)."""
    x0, y0, w, h = WS
    v = Vig(w, h)
    v.rect(0, 0, w, h, 'wall')
    v.rect(0, 34, w, 12, 'wall2')                                      # the lower wall, darker
    v.rect(0, 0, w, 2, 'furn')                                         # ceiling beam
    for wx_ in (4, 30):                                                # windows half above the courtyard
        v.rect(wx_, 2, 14, 11, 'furn')
        v.rect(wx_ + 1, 3, 12, 8, 'glass')
        v.rect(wx_ + 7, 3, 1, 8, 'furn')
        v.rect(wx_ - 1, 13, 16, 1, 'furn2')                             # sill
    v.rect(1, 19, 12, 1, 'furn')                                       # shelves on the left wall
    v.rect(1, 26, 12, 1, 'furn')
    v.rect(1, 33, 12, 1, 'furn')
    for k in range(1, 13, 3):                                          # lasts (wooden feet) on the top shelf
        v.rect(k, 16, 2, 3, 'furn2')
        v.px(k + 2, 18, 'furn2')
    for k, role in ((1, 'fig'), (5, 'fig2'), (9, 'fig')):              # pairs of shoes waiting, with their tags
        v.rect(k, 23, 3, 3, role)
        v.px(k + 3, 25, role)
        v.px(k + 1, 22, 'paper')
    for k, role in ((1, 'fig2'), (6, 'fig')):
        v.rect(k, 30, 4, 3, role)
        v.px(k + 2, 29, 'paper')
    v.rect(10, 29, 2, 4, 'red')                                        # a red child's boot
    v.rect(16, 15, 13, 1, 'furn')                                      # the tool rack: hammer, pincers, awl, knife
    v.rect(17, 16, 1, 4, 'metal')
    v.rect(16, 16, 3, 1, 'metal')
    v.rect(20, 16, 1, 4, 'metal')
    v.rect(21, 16, 1, 3, 'metal')
    v.rect(24, 16, 1, 3, 'metal')
    v.px(24, 19, 'furn2')
    v.rect(27, 16, 1, 3, 'metal')
    v.rect(22, 2, 1, 8, 'metal')                                       # the lamp over the bench
    v.rect(20, 10, 5, 1, 'metal')
    v.rect(19, 11, 7, 1, 'metal')
    v.px(22, 12, 'light')
    v.rect(14, 31, 17, 2, 'furn')                                      # the bench
    v.rect(15, 33, 2, 12, 'furn')
    v.rect(28, 33, 2, 12, 'furn')
    v.rect(15, 40, 15, 1, 'furn')
    v.rect(23, 25, 4, 6, 'fig')                                        # a boot on the last
    v.rect(26, 29, 2, 2, 'fig')
    v.rect(22, 30, 7, 1, 'furn2')
    v.rect(18, 29, 3, 2, 'metal')                                      # a box of nails, the glue pot
    v.rect(19, 28, 1, 1, 'metal')
    v.rect(14, 30, 3, 1, 'metal')                                      # the candle's saucer and stub
    v.rect(15, 27, 1, 3, 'paper')
    v.rect(26, 38, 6, 1, 'furn')                                       # his stool
    v.rect(27, 39, 1, 6, 'furn')
    v.rect(30, 39, 1, 6, 'furn')
    v.rect(33, 22, 7, 2, 'metal')                                      # the arm sewing machine on its stand
    v.rect(38, 24, 2, 7, 'metal')
    v.rect(33, 24, 1, 3, 'metal')
    v.rect(32, 31, 9, 1, 'furn')
    v.rect(33, 32, 1, 12, 'metal')
    v.rect(39, 32, 1, 12, 'metal')
    v.rect(33, 43, 7, 1, 'metal')
    v.rect(41, 14, 1, 1, 'metal')                                      # his apron on a nail
    v.rect(40, 15, 4, 9, 'cloth')
    v.rect(41, 15, 2, 1, 'fig')
    v.rect(45, 29, 9, 16, 'metal')                                     # the stove and its pipe
    v.rect(46, 30, 7, 1, 'furn2')
    v.rect(47, 36, 5, 3, 'ember')
    v.rect(48, 4, 3, 25, 'metal')
    v.rect(48, 4, 7, 2, 'metal')
    v.rect(2, 39, 10, 6, 'furn2')                                      # a crate of shoes for collection
    v.rect(3, 37, 3, 2, 'fig')
    v.rect(7, 37, 3, 2, 'fig2')
    v.rect(2, 41, 10, 1, 'furn')
    v.rect(0, 45, w, 5, 'floor')
    return v


# the workshop's own light: grey whitewash by day; the candle's warm room; the dark room with the stove's ember
WS_COLORS = {
    'neutral': {'wall': '#8E887A', 'wall2': '#6E6A5E', 'floor': '#4A443A', 'furn': '#3E2A1C', 'furn2': '#8A6A44',
                'metal': '#2E3036', 'paper': '#E6DEC2', 'light': '#C8C0A0', 'glass': '#3A4A5E', 'cloth': '#6A5A44',
                'fig': '#1E1A18', 'fig2': '#5A3A22', 'red': '#8A3226', 'ember': '#7A3A1A'},
    'lit': {'wall': '#D49A54', 'wall2': '#B07A3C', 'floor': '#7A4A22', 'furn': '#2E1C0E', 'furn2': '#A0703A',
            'metal': '#24180E', 'paper': '#FFE8B8', 'light': '#3A2A1A', 'glass': '#1A2232', 'cloth': '#5A3818',
            'fig': '#140C06', 'fig2': '#3A2010', 'red': '#6A2414', 'ember': '#F08A3A'},
    'dark': {'wall': '#1A1C22', 'wall2': '#14161C', 'floor': '#0E1014', 'furn': '#0C0E12', 'furn2': '#1E1E22',
             'metal': '#0A0C10', 'paper': '#3A3C44', 'light': '#20242C', 'glass': '#141C2A', 'cloth': '#16181E',
             'fig': '#08090C', 'fig2': '#14100E', 'red': '#2A1612', 'ember': '#C0501E'},
}


def workshop(cv: Canvas, mode: str, candle: bool = False):
    """Pietsch's workshop in one light: 'neutral' (overview), 'dark' (22.40, only the stove's ember), 'lit' (the
    candle is lit -- the success).  Same drawing in all three (workshop_vig)."""
    x0, y0, w, h = WS
    v = workshop_vig()
    arr = v.render(mode, seed=7, cols=WS_COLORS[mode]).astype(np.float32)
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    if mode == 'lit':
        d = np.hypot(xx - 15.5, (yy - 26) * 1.1)
        f = np.clip(1.0 - d / 40.0, 0, 1) ** 1.2
        k = light_bands(0.42 + 0.78 * f, 6)
    elif mode == 'dark':
        d = np.hypot(xx - 49, yy - 37)
        k = light_bands(0.9 + 0.9 * np.clip(1.0 - d / 16.0, 0, 1), 5)
    else:
        k = 1.0 + (noise(w, h, 6, 9400) - 0.5) * 0.12
    arr[..., :3] *= np.asarray(k, np.float32)[..., None] if np.ndim(k) else k
    arr = np.clip(arr, 0, 255).astype(np.uint8)
    arr[..., 3] = 255
    for wx_ in (4, 30):                                                # snow in the light wells (any light)
        arr[9:11, wx_ + 1:wx_ + 13, :3] = C(SNOW[1] if mode != 'dark' else '#4A5568')[:3]
    if candle:
        arr[24, 15, :3] = C('#FFF4CE')[:3]
        arr[25, 15, :3] = C('#FFE2A8')[:3]
        arr[26, 15, :3] = C('#F2B860')[:3]
    cv.blend(np.ones((h, w), bool), x0, y0, arr)
    cv.rect(x0, y0, 1, h, C(NIGHT), 0.6)


def glow(cv: Canvas, cx: float, cy: float, r: float, col, a: float = 0.35):
    n = int(2 * r + 3)
    yy, xx = np.mgrid[0:n, 0:n].astype(np.float32)
    d = np.hypot(xx - n / 2, yy - n / 2) / r
    f = np.clip(1 - d, 0, 1) ** 1.5
    m = (f * 4 + pg.bayer(n, n)) // 1 / 4.0
    cv.blend(m * a, int(cx - n / 2), int(cy - n / 2), C(col))


def grade_night(cv: Canvas, snow: np.ndarray):
    rgb = cv.c[..., :3].astype(np.float32)
    k = np.where(snow[..., None], np.array([0.62, 0.68, 0.86]), np.array([0.46, 0.52, 0.76]))
    rgb = rgb * k + np.array([3, 5, 12])
    cv.c[..., :3] = np.clip(np.round(rgb), 0, 255).astype(np.uint8)


def house_views() -> dict:
    base, snow = house_base()
    views = {}
    for view in ('overview', 'night'):
        cv = Canvas(HW, HH)
        cv.c = base.c.copy()
        if view == 'night':
            grade_night(cv, snow)
        for (room, name, x, y) in WINDOWS:
            mode = window_mode(room, view)
            if view == 'night' and mode == 'lit':
                glow(cv, x + WIN_W / 2.0, y + WIN_H / 2.0, 13, LAMPW[3], 0.28)
                cv.rect(x - 1, y + WIN_H, WIN_W + 2, 1, C('#E8C890'))   # light on the snow of the sill
            elif view == 'night' and mode == 'dim':
                glow(cv, x + WIN_W / 2.0, y + WIN_H / 2.0, 10, LAMPW[2], 0.12)
            paint_window(cv, name, x, y, mode)
        passage(cv, 'lit' if view == 'night' else 'neutral')
        if view == 'night':
            glow(cv, WING_X['v'] + 27, ROWS['e'][0] + 14, 16, SODIUM[3], 0.32)
            workshop(cv, 'dark')
            glow(cv, WS[0] + 49, WS[1] + 37, 7, '#E0782A', 0.25)
        views[view] = cv
    return views


def anim_frames() -> Canvas:
    """The lights at 22.40 move a little: Lenz turns a page, Schulz rocks the baby, Pohl's curtain opens, Frau
    Kuhnert turns her head, Kühn slaps a card down.  Two frames each (WIN_W x WIN_H incl. the frame)."""
    atlas = Canvas(WIN_W * 2 * len(ANIMS), WIN_H)
    for i, name in enumerate(ANIMS):
        room = next(r for (r, n, x, y) in WINDOWS if n == name)
        mode = window_mode(room, 'night')
        for f in range(2):
            cv = Canvas(WIN_W, WIN_H)
            paint_window(cv, name, 0, 0, mode, f)
            atlas.blit(cv, (2 * i + f) * WIN_W, 0)
    return atlas


# ----------------------------------------------------------------------------- the walking markers
# Hand-placed rows (facing right; the UI flips them for a walk to the left).  Konrad (C4P2 §5, cast sheet
# `konrad`): grey fedora with its brim snapped down in front, the face under it (ear, eye, nose), dark-blue civilian
# overcoat, ochre wool scarf, the drafting tube on his back, dark trousers and shoes.  Ilse (`berlin_child`): the
# dark-blue knitted cap with a short peak, a light-brown plait, the pale grey wool coat, the brown satchel she never
# lets go of, grey wool stockings.  Three tones per material, lit from the upper left, a dark outline for the board.
K_PAL = {
    'a': '#A8A8AE', 'b': '#7E7E86', 'c': '#5A5A62', 'd': '#2A2A32',
    's': '#D2A07E', 't': '#EABE9A', 'u': '#A87458', 'U': '#8A5A44', 'e': '#1C120E', 'h': '#3E2C20',
    'y': '#A88444', 'Y': '#C8A25A',
    'k': '#46598A', 'm': '#2E3F66', 'n': '#1E2A48', 'o': '#141C34',
    'q': '#6A5E50', 'p': '#4A4038', 'r': '#9A9AA2',
    'v': '#40424E', 'w': '#2A2C36', 'x': '#121216', 'X': '#4A4A54', 'g': '#E0B494',
}
I_PAL = {
    'k': '#2E3C66', 'K': '#4A5C92', 'j': '#1A2342', 'h': '#7A5232', 'H': '#A07448',
    's': '#E2B494', 't': '#F2CCAC', 'u': '#B88464', 'e': '#1C120E', 'R': '#DA8E7C',
    'c': '#8E8A7C', 'C': '#B2AC98', 'D': '#6A665A', 'E': '#D2CCB4',
    'b': '#5E3A20', 'B': '#86562C', 'g': '#D0A850', 'l': '#6E7078', 'L': '#8E9098', 'x': '#141418', 'X': '#4A4A54',
}
K_HEAD = ['.....bbc.....', '....abbbbc...', '....dddddd...', '..cbbbbbbbbbc', '....hhuuuu..c', '....hUsses...',
          '....hsssst...', '.....ussu....', '...r.yYYyy...']
K_BODY = [
    ['...qkkmmmYm..', '...qkkmmmyn..', '...pkkmmnmm..', '...pkkmmnmm..', '...pkkmmnmm..', '....kkmmngm..',
     '....kkmmmmm..', '....kkmmmnm..', '....okmmmnno.'],                                   # standing
    ['...qkkmmmYm..', '...qkkmmmyn..', '...pkkmmmmmn.', '...pkkmmmmmg.', '...pkkmmnmm..', '....kkmmnmm..',
     '....kkmmmmm..', '...okkmmmnmm.', '...okkmmmnnmo'],                                   # contact, arm forward
    ['...qkkmmmYm..', '...qkkmmmyn..', '...pkkmmnmm..', '...pkkmmnmm..', '...pkkmmnmm..', '....kkmmngm..',
     '....kkmmmmm..', '....kkmmmnm..', '....okmmmnno.'],                                   # passing
    ['...qkkmmmYm..', '...qkkmmmyn..', '...pkkmmnmm..', '..gpkkmmnmm..', '...pkkmmnmm..', '....kkmmnmm..',
     '....kkmmmmm..', '...okkmmmnmm.', '...okkmmmnnmo'],                                   # contact, arm back
    ['...qkkmmmYm..', '...qkkmmmyn..', '...pkkmmnmm..', '...pkkmmnmm..', '...pkkmmnmm..', '....kkmmngm..',
     '....kkmmmmm..', '....kkmmmnm..', '....okmmmnno.'],                                   # passing
]
K_LEGS = [
    ['.....wvvv....', '.....wv.v....', '....xxx.xxX..'],
    ['....wv...vv..', '...wv.....vv.', '..xxx.....xxX'],
    ['.....wvvv....', '.....wvv.....', '.....xxxXx...'],
    ['....vv...wv..', '...vv.....wv.', '..xxx.....xxX'],
    ['.....vvwv....', '.....vvw.....', '.....xxxXx...'],
]
I_HEAD = ['...kkK....', '..kkkKK...', '..hkkkkjj.', '..hHsset..', '..hhsRs...', '..h..us...']
I_BODY = [
    ['...cEC....', '..DcCCC...', '..DcCbbbb.', '..DcCbgBb.', '..DccbBBb.', '..DcccCC..'],
    ['...cEC....', '..DcCCC...', '..DcCbbbb.', '..DcCbgBbs', '..DccbBBb.', '..DDcccCC.'],
    ['...cEC....', '..DcCCC...', '..DcCbbbb.', '..DcCbgBb.', '..DccbBBb.', '..DcccCC..'],
    ['...cEC....', '..DcCCC...', '..DcCbbbb.', '.sDcCbgBb.', '..DccbBBb.', '..DDcccCC.'],
    ['...cEC....', '..DcCCC...', '..DcCbbbb.', '..DcCbgBb.', '..DccbBBb.', '..DcccCC..'],
]
I_LEGS = [
    ['....lL....', '....lL....', '...xxxxX..'],
    ['...l..L...', '..l....L..', '.xx....xxX'],
    ['....lL....', '....l.L...', '...xxXxx..'],
    ['...L..l...', '..L....l..', '.xx....xxX'],
    ['....Ll....', '....L.l...', '...xxXxx..'],
]


def _marker(rows: list, pal: dict, frame_wh) -> Canvas:
    cv = Canvas(*frame_wh)
    cv.blit(sprite(rows, pal), 1, 1)
    outline(cv, NIGHT)
    return cv


def marker_konrad(frame: int) -> Canvas:
    return _marker(K_HEAD + K_BODY[frame] + K_LEGS[frame], K_PAL, K_FIG['frame'])


def marker_ilse(frame: int) -> Canvas:
    return _marker(I_HEAD + I_BODY[frame] + I_LEGS[frame], I_PAL, I_FIG['frame'])


def mark_icon(kind: str) -> Canvas:
    """Shape-coded watcher marks (never colour alone): a spy-hole eye, a table lamp, the Blockleiter's peaked cap
    (a flat wide crown over a band, the peak sticking out -- round 10: the old one read as a blob); the stop sign is
    a light bar on a red disc."""
    n = 15
    cv = Canvas(n, n)
    plate = '#F0E6CC' if kind != 'stop' else RED
    cv.blend(disc(6.6, size=n), 0, 0, C(plate))
    cv.blend(ring(6.0, 7.2, n), 0, 0, C(INK))
    ink = C(INK)
    if kind == 'eye':
        for (x, y, w) in ((5, 5, 5), (4, 6, 7), (3, 7, 9), (4, 8, 7), (5, 9, 5)):
            cv.rect(x, y, w, 1, ink)
        cv.rect(6, 6, 3, 3, C('#2B3C50'))
        cv.px(7, 7, C('#F5EFDA'))
        cv.rect(4, 7, 1, 1, C(PAPER[5]))
        cv.rect(10, 7, 1, 1, C(PAPER[5]))
    elif kind == 'lamp':                                              # a table lamp: shade, light, stem, foot
        for (x, y, w) in ((6, 3, 3), (5, 4, 5), (4, 5, 7), (3, 6, 9)):
            cv.rect(x, y, w, 1, ink)
        cv.rect(5, 7, 5, 1, C('#E0A85A'))
        cv.rect(6, 8, 3, 1, C('#F0C487'))
        cv.rect(7, 7, 1, 4, ink)
        cv.rect(5, 11, 5, 1, ink)
    elif kind == 'hat':                                               # the peaked cap, side view, peak to the right:
        for (x, y, w) in ((4, 3, 7), (3, 4, 9), (3, 5, 9)):           # the wide flat crown (clear of the ring),
            cv.rect(x, y, w, 1, ink)
        cv.rect(4, 6, 7, 1, C('#8A7A5A'))                             # the piping,
        cv.rect(5, 7, 5, 1, ink)                                      # the narrow band,
        cv.rect(5, 8, 7, 1, ink)                                      # the peak jutting out in front
        cv.rect(8, 9, 4, 1, ink)
    elif kind == 'stop':
        cv.rect(3, 6, 9, 3, C('#F5EFDA'))
    return cv


CIRCLE = (WS[0] + WS[2] // 2, WS[1] + WS[3] // 2, 29, 24)            # Konrad's ring: centre x, y, radii -- on the board, under the sign


def red_circle() -> Canvas:
    """Konrad's red pencil ring around the workshop after the right way: drawn twice by hand, inside the board
    (round 10 review: the old one ran past the right edge)."""
    cx, cy, rx, ry = CIRCLE
    w, h = 2 * rx + 5, 2 * ry + 5
    cv = Canvas(w, h)
    for k, (ax, ay, ph) in enumerate(((rx - 0.5, ry - 0.5, 0.3), (rx, ry - 1.2, 2.0))):
        prev = None
        for i in range(160):
            t = i / 150 * math.tau + ph
            x = w / 2 - 0.5 + math.cos(t) * (ax + math.sin(t * 3) * 0.6)
            y = h / 2 - 0.5 + math.sin(t) * (ay + math.cos(t * 2) * 0.6)
            if prev is not None:
                cv.line(prev[0], prev[1], x, y, C(RED), 0.95 if k == 0 else 0.6, 2 if k == 0 else 1)
            prev = (x, y)
    return cv


def ws_lit() -> Canvas:
    cv = Canvas(HW, HH)
    workshop(cv, 'lit', candle=True)
    x0, y0, w, h = WS
    out = Canvas(w, h)
    out.c = cv.c[y0:y0 + h, x0:x0 + w].copy()
    return out


# ============================================================================= main
def rel(path: str) -> str:
    return 'res://' + os.path.relpath(path, ROOT).replace(os.sep, '/')


def main():
    preview = ''
    for a in sys.argv[1:]:
        if a.startswith('--preview='):
            preview = a.split('=', 1)[1]
    written = []

    def save(cv: Canvas, d: str, f: str):
        p = os.path.join(d, f)
        cv.save(p)
        written.append(p)

    # ---------------------------------------------------------------- the halves
    marks = halves_marks()
    sol = check_halves(marks)
    halves = card_halves()
    tab = table()
    snap, ringc, click = halves_snap(), halves_ring(), halves_click()
    save(halves['de'], DOCS, 'karsk_c4p2_halves_de.png')
    save(halves['ru'], DOCS, 'karsk_c4p2_halves_ru.png')
    save(tab, PUZ, 'c4p2_halves_table.png')
    save(snap, PUZ, 'c4p2_halves_snap.png')
    save(ringc, PUZ, 'c4p2_halves_ring.png')
    save(click, PUZ, 'c4p2_halves_click.png')
    leg = legend_icons()
    save(leg['tooth'], PUZ, 'c4p2_halves_legend_teeth.png')
    save(leg['stamp'], PUZ, 'c4p2_halves_legend_stamp.png')
    save(leg['lines'], PUZ, 'c4p2_halves_legend_lines.png')
    jmeta = {
        'puzzle_id': 'pz_c4_halves', 'objective': 'c4g_solve_halves', 'cell_px': CELL, 'display_scale': 3,
        'coords': 'board in cells (+x right, +y down); marks in continuous art px of each sheet BODY (+x right, +y '
                  'down); rotation_steps turn the German half clockwise around its body centre (screen '
                  'coordinates); offsets move it in whole cells; a mark pair is joined when the positions meet and '
                  'the inward directions are opposite',
        'generator': GENERATOR, 'date': DATE,
        'board': {'file': 'c4p2_halves_table.png', 'cells': list(BOARD_CELLS), 'lamp': list(LAMP),
                  'edge_margin_px': EDGE_MARGIN, 'book': list(BOOK)},
        'base': {'file': 'karsk_c4p2_halves_ru.png', 'item': 'ev_c4_card_ru_original', 'cells': list(HALF_CELLS),
                 'at': list(RU_AT), 'pad': 0, 'marks': marks['base']},
        'overlay': {'file': 'karsk_c4p2_halves_de.png', 'item': 'ev_c4_guidebook', 'cells': list(HALF_CELLS),
                    'at': list(GE_AT), 'pad': PAD, 'stored': 'upside down, as Konrad laid it into the guidebook',
                    'marks': marks['overlay']},
        'pairs': [list(p) for p in PAIRS],
        'start': START,
        'offsets': [{'rotation_steps': r, 'min': list(offset_range(r)[0]), 'max': list(offset_range(r)[1])}
                    for r in range(4)],
        'marks': {'snap': 'c4p2_halves_snap.png', 'ring': 'c4p2_halves_ring.png', 'click': 'c4p2_halves_click.png'},
        'legend': {'tooth': 'c4p2_halves_legend_teeth.png', 'stamp': 'c4p2_halves_legend_stamp.png',
                   'lines': 'c4p2_halves_legend_lines.png'},
        'surfaces': {'paper': surface(halves['ru'], [60, 20, 20, 6]), 'table': surface(tab, [200, 90, 20, 10])},
        'pose_check': {'verified_against': 'data/v3/puzzles.json pz_c4_halves',
                       'unique': 'exactly one pose (rotation, offset) joins all five teeth and the stamp; no other '
                                 'pose joins even one tooth; only one rotation lets the marks face each other',
                       'start_joined': 0, 'rotation_fits': [r == sol['rotation_steps'] for r in range(4)]},
        'accessibility': 'teeth are triangles, notches are cut-outs, the stamp halves are semicircles, the line ends '
                         'are ticks -- shapes, not colours; the card text turns with the paper',
        'world_note': 'Fictional two-part registry card laid against its other half; not a real form.',
    }
    p = os.path.join(DOCS, 'karsk_c4p2_halves.json')
    with open(p, 'w', encoding='utf-8') as f:
        json.dump(jmeta, f, indent=1, ensure_ascii=False)
    written.append(p)

    # ---------------------------------------------------------------- the house
    hsol = check_house()
    views = house_views()
    save(views['overview'], PUZ, 'c4p2_house_board.png')
    save(views['night'], PUZ, 'c4p2_house_night.png')
    atlas = anim_frames()
    save(atlas, PUZ, 'c4p2_house_anim.png')
    kw, kh = K_FIG['frame']
    ks = Canvas(kw * FIG_FRAMES, kh)
    for f in range(FIG_FRAMES):
        ks.blit(marker_konrad(f), f * kw, 0)
    save(ks, PUZ, 'c4p2_house_konrad.png')
    iw, ih = I_FIG['frame']
    il = Canvas(iw * FIG_FRAMES, ih)
    for f in range(FIG_FRAMES):
        il.blit(marker_ilse(f), f * iw, 0)
    save(il, PUZ, 'c4p2_house_ilse.png')
    for k in ('eye', 'lamp', 'hat', 'stop'):
        save(mark_icon(k), PUZ, 'c4p2_house_%s.png' % k)
    circ = red_circle()
    save(circ, PUZ, 'c4p2_house_circle.png')
    wl = ws_lit()
    save(wl, PUZ, 'c4p2_house_ws_lit.png')
    rooms = {}
    for rid in HOUSE_ROOMS:
        stand = room_stand(rid)
        r = {'wing': 'w' if rid == 'ws' else rid[0], 'floor': 'k' if rid == 'ws' else rid[1],
             'col': room_cell(rid)[0], 'row': room_cell(rid)[1], 'rect': room_rect(rid), 'extra': room_extra(rid),
             'node': room_node(rid), 'stand': stand, 'mate': [stand[0] + MATE_DX, stand[1]],
             'label_at': room_label_at(rid), 'kind': KIND.get(rid, 'flat'),
             'windows': [[x, y, WIN_W, WIN_H] for (rm, n, x, y) in WINDOWS if rm == rid]}
        rooms[rid] = r
    watch_at = {'s2': [WING_X['s'] + FLAT_W - 6, ROWS['2'][0] + ROWS['2'][1] - 12],
                'se': [WING_X['s'] + 13, ROWS['e'][0] + 24],
                've': [WING_X['v'] + 4 + 46 // 2 + 9, GROUND - 16]}
    edges = house_edges()
    hmeta = {
        'puzzle_id': 'pz_c4_house', 'objective': 'c4h_solve_house', 'display_scale': 3,
        'coords': 'art pixels ([x, y] / [x, y, w, h]) of the board; the UI multiplies by 3.  col: Vorderhaus 0, '
                  'Seitenflügel 1, Hinterhaus 2, workshop 3; row: cellar 0 … drying loft 5.  An arrow moves to '
                  'the neighbour whose (col, row) differs by one in that direction when a passage joins them.  '
                  'stand / mate / paths are FEET points: x = the pixel column, y = the top of the floor.',
        'generator': GENERATOR, 'date': DATE,
        'board': {'file': 'c4p2_house_board.png', 'night_file': 'c4p2_house_night.png', 'size': [HW, HH],
                  'gutter': [0, 10], 'ground_y': GROUND},
        'rows': {k: list(v) for k, v in ROWS.items()},
        'wings': {w: {'x': roof_span(w)[0], 'w': roof_span(w)[1] - roof_span(w)[0],
                      'label_at': [(roof_span(w)[0] + roof_span(w)[1]) // 2, 2]} for w in 'vsh'},
        'rooms': rooms,
        'edges': edges,
        'paths': [edge_path(a, b) for a, b in edges],
        'unsafe': UNSAFE,
        'watch': {r: {'mark': WATCH[r], 'at': watch_at[r]} for r in UNSAFE},
        'start': 's3', 'goal': 'ws',
        'households': HOUSEHOLDS,
        'lit': LIT,
        'dim': DIM,
        'anims': [{'room': next(r for (r, n, x, y) in WINDOWS if n == name), 'window': name,
                   'rect': [next([x, y, WIN_W, WIN_H] for (r, n, x, y) in WINDOWS if n == name)][0],
                   'frames': [2 * i, 2 * i + 1], 'period': [1.3, 0.9, 1.7, 1.5, 1.1][i]}
                  for i, name in enumerate(ANIMS)],
        'figures': {'konrad': {'file': 'c4p2_house_konrad.png', 'frame': list(K_FIG['frame']),
                               'feet': list(K_FIG['feet']), 'height': K_FIG['height'], 'frames': FIG_FRAMES},
                    'ilse': {'file': 'c4p2_house_ilse.png', 'frame': list(I_FIG['frame']),
                             'feet': list(I_FIG['feet']), 'height': I_FIG['height'], 'frames': FIG_FRAMES},
                    'frames': 'standing, then four walking frames (contact, passing, contact, passing); facing right',
                    'trail_px': TRAIL},
        'marks': {'eye': 'c4p2_house_eye.png', 'lamp': 'c4p2_house_lamp.png', 'hat': 'c4p2_house_hat.png',
                  'stop': 'c4p2_house_stop.png', 'circle': 'c4p2_house_circle.png', 'circle_at': list(CIRCLE[:2]),
                  'ws_lit': 'c4p2_house_ws_lit.png', 'anim': 'c4p2_house_anim.png', 'anim_frame': [WIN_W, WIN_H]},
        'surfaces': {'facade_v': surface(views['overview'], [WING_X['v'] + 44, 60, 8, 8]),
                     'night_facade_s': surface(views['night'], [WING_X['s'] + 44, 100, 8, 8]),
                     'sky': surface(views['overview'], [140, 2, 20, 6])},
        'graph_check': {'verified_against': 'data/v3/puzzles.json pz_c4_house', 'safe_paths': 1,
                        'inputplay': '↓ from s3 = s2; ↑ → ↓×5 → from s3 = the solution',
                        'markers': 'every place is on its floor with room for Konrad; every way runs level or '
                                   'along a flight'},
        'accessibility': 'watchers are shape-coded (eye = spy hole, lamp = lodge window, cap = Blockleiter); the route '
                         'is drawn by the UI as a line with an outline; every room name and card note is HD text',
        'world_note': 'A fictional Berlin tenement, its fictional households and a fictional card file; no real persons.',
    }
    p = os.path.join(PUZ, 'c4p2_house.json')
    with open(p, 'w', encoding='utf-8') as f:
        json.dump(hmeta, f, indent=1, ensure_ascii=False)
    written.append(p)
    assert hsol[0] == 's3' and hsol[-1] == 'ws'

    if preview:
        os.makedirs(preview, exist_ok=True)
        S = 2
        sheet = Image.new('RGBA', (1280, 980), tuple(int(v) for v in C(NAVY)))

        def put(cv, x, y, s=S):
            im = cv.image().resize((cv.w * s, cv.h * s), Image.NEAREST)
            sheet.alpha_composite(im, (x, y))
        put(tab, 4, 4)
        put(halves['ru'], 660, 4)
        put(halves['de'], 660, 180)
        put(halves['whole'], 660, 380, 2)
        put(snap, 1150, 4, 3)
        put(ringc, 1100, 60, 2)
        put(click, 1150, 200, 3)
        sheet.save(os.path.join(preview, 'c4p2_halves_sheet.png'))
        sheet2 = Image.new('RGBA', (1280, 520), tuple(int(v) for v in C(NAVY)))
        for i, k in enumerate(('overview', 'night')):
            im = views[k].image().resize((HW * 2, HH * 2), Image.NEAREST)
            sheet2.alpha_composite(im, (i * 640, 4))
        sheet2.save(os.path.join(preview, 'c4p2_house_sheet.png'))
        sheet3 = Image.new('RGBA', (900, 200), tuple(int(v) for v in C(NAVY)))

        def put3(cv, x, y, s):
            im = cv.image().resize((cv.w * s, cv.h * s), Image.NEAREST)
            sheet3.alpha_composite(im, (x, y))
        put3(atlas, 4, 4, 3)
        put3(ks, 4, 70, 2)
        put3(il, 4, 120, 2)
        for i, k in enumerate(('eye', 'lamp', 'hat', 'stop')):
            put3(mark_icon(k), 170 + i * 52, 70, 3)
        put3(circ, 390, 70, 1)
        put3(wl, 470, 70, 2)
        sheet3.save(os.path.join(preview, 'c4p2_marks_sheet.png'))
    for p in written:
        print('wrote', os.path.relpath(p, ROOT))


if __name__ == '__main__':
    main()
