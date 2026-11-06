"""gen_ui_c3 -- Chapter 3 puzzle UI art + inspect documents for pz_c3_protocol
("Sitzordnung und Dolmetscherprotokoll", objective c3b_solve_protocol).

Owner: puzzle UI stream (documentation/C3_DESIGN.md §7).  Puzzle facts: C3_DESIGN.md §2.7.
Everything is drawn procedurally at 1:1 (one art pixel = one world pixel) and shown at x3 with
nearest filtering by the UI (scripts/ui/protocol_puzzle.gd, scenes/ui/InspectView.tscn).  No image is
sampled or traced; all randomness uses fixed seeds (deterministic output).

Board art (assets/ui/puzzle/, text-free -- the UI sets every word in HD via Loc keys):
  c3_plan.png              seating plan of the Großer Saal (Berlin drafting style: diazo paper, blue
                           ink, dotted construction grid, hatched table, chairs, microphones)
  c3_log.png               Elena's booth log sheet, Kabine 2 (typed form: letterhead, rules, red
                           margin, punch holes, paper clip, her ink bracket at 10.09)
  c3_card_<id>.png         name plates chair / reich / soviet / secretariat, each with its own shape
                           glyph (circle / square / triangle / diamond -- never colour coded)
  c3_glyph_<shape>.png     the same glyphs, small (plan annotations next to the HD block labels)
  c3_slot.png              empty slot of the order row ("1. Wortmeldung" ... HD)
  c3_seq_arrow.png         arrow between two slots
  c3_protocol_board.json   every HD overlay rect (art px) + seat/mic geometry + solution self-check
Inspect documents (assets/ui/documents/, in-world, pixel lettering because InspectView shows the PNG
as it is):
  veltrava_protocol_seating.png    the identical plan drawing + pixel labels (only mic numbers 1, 2, 12)
  veltrava_protocol_booth_log.png  the log with pixel typewriter rows and Elena's handwritten note
  veltrava_protocol_documents.json InspectView metadata (schema of karsk_documents.json)

Run:  python3 -P tools/pixelgen/gen_ui_c3.py [--preview=DIR]
      --preview writes x3 previews + a contact sheet to DIR (outside the repo or a .gdignore folder).
"""
from __future__ import annotations

import json
import math
import os
import sys

import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pg  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
PUZ = os.path.join(ROOT, 'assets', 'ui', 'puzzle')
DOCS = os.path.join(ROOT, 'assets', 'ui', 'documents')
DATE = '2026-11-04'
GENERATOR = 'tools/pixelgen/gen_ui_c3.py'

hx = pg.hx
CLEAR = np.array([0, 0, 0, 0], np.uint8)

# ----------------------------------------------------------------------------- palette
# UI / archive ramps (gen_ui.py, pg.PALETTES['archive']) + the commission's slate blue
# (data/chapters/c3.json palettes.veltrava.slate).  No new hues.
NIGHT, NIGHT1, NAVY, NAVY_L = '#04090D', '#06151D', '#0B1C24', '#14272B'
WALL = ['#1A2A2E', '#24373A', '#354448', '#4A5A5B', '#62716E']
PAPER = ['#6E6A5C', '#8E8A78', '#B0AA93', '#CEC6AA', '#E6DEC2', '#F5EFDA']   # 0 dark .. 5 light
BLUE = ['#1D2A3A', '#2B3C50', '#3E546B', '#58718A', '#7A93A8', '#A7BCCB']
INK, INK_B = '#1A1C2A', '#2E3248'
RED_D, RED = '#7A2A26', '#A8382E'
SLATE = ['#1E2836', '#2A3646', '#3A4859', '#4F5E70', '#687789', '#8593A3']
COPPER_D, COPPER, COPPER_L = '#7A3E26', '#BA775B', '#DCA16E'


def c(h, a=255):
    return hx(h, a)


def L(w, h):
    return pg.Layer(w, h)


def ring(l, x, y, w, h, col, round_corners=False):
    l.rect(x, y, w, 1, col)
    l.rect(x, y + h - 1, w, 1, col)
    l.rect(x, y, 1, h, col)
    l.rect(x + w - 1, y, 1, h, col)
    if round_corners:
        for px, py in [(x, y), (x + w - 1, y), (x, y + h - 1), (x + w - 1, y + h - 1)]:
            if 0 <= px < l.w and 0 <= py < l.h:
                l.c[py, px] = CLEAR


def dither_fill(l, mask, x0, y0, tone, ramp):
    """tone: float array (mask shape) in ramp-index units -> ordered dither onto ramp."""
    cols = np.stack([c(h) for h in ramp])
    n = len(ramp)
    t = np.clip(tone, 0, n - 1)
    fl = np.floor(t)
    idx = fl + ((t - fl) > pg.bayer(mask.shape[1], mask.shape[0], x0, y0))
    idx = np.clip(idx, 0, n - 1).astype(np.int32)
    l._put(mask, x0, y0, cols[idx])


# ----------------------------------------------------------------------------- pixel lettering
# 3x5 technical capitals (same shapes as the Berlin drafting sheets) + the few glyphs the
# Veltrava documents need (arrows, quotes, section sign, middle dot, exclamation mark).
F35 = {
    'A': ['.#.', '#.#', '###', '#.#', '#.#'], 'B': ['##.', '#.#', '##.', '#.#', '##.'],
    'C': ['.##', '#..', '#..', '#..', '.##'], 'D': ['##.', '#.#', '#.#', '#.#', '##.'],
    'E': ['###', '#..', '##.', '#..', '###'], 'F': ['###', '#..', '##.', '#..', '#..'],
    'G': ['.##', '#..', '#.#', '#.#', '.##'], 'H': ['#.#', '#.#', '###', '#.#', '#.#'],
    'I': ['###', '.#.', '.#.', '.#.', '###'], 'J': ['..#', '..#', '..#', '#.#', '.#.'],
    'K': ['#.#', '#.#', '##.', '#.#', '#.#'], 'L': ['#..', '#..', '#..', '#..', '###'],
    'M': ['#.#', '###', '###', '#.#', '#.#'], 'N': ['##.', '#.#', '#.#', '#.#', '#.#'],
    'O': ['.#.', '#.#', '#.#', '#.#', '.#.'], 'P': ['##.', '#.#', '##.', '#..', '#..'],
    'Q': ['.#.', '#.#', '#.#', '##.', '.##'], 'R': ['##.', '#.#', '##.', '##.', '#.#'],
    'S': ['.##', '#..', '.#.', '..#', '##.'], 'T': ['###', '.#.', '.#.', '.#.', '.#.'],
    'U': ['#.#', '#.#', '#.#', '#.#', '###'], 'V': ['#.#', '#.#', '#.#', '#.#', '.#.'],
    'W': ['#.#', '#.#', '###', '###', '#.#'], 'X': ['#.#', '#.#', '.#.', '#.#', '#.#'],
    'Y': ['#.#', '#.#', '.#.', '.#.', '.#.'], 'Z': ['###', '..#', '.#.', '#..', '###'],
    '0': ['###', '#.#', '#.#', '#.#', '###'], '1': ['.#.', '##.', '.#.', '.#.', '###'],
    '2': ['##.', '..#', '.#.', '#..', '###'], '3': ['##.', '..#', '.#.', '..#', '##.'],
    '4': ['#.#', '#.#', '###', '..#', '..#'], '5': ['###', '#..', '##.', '..#', '##.'],
    '6': ['.##', '#..', '###', '#.#', '###'], '7': ['###', '..#', '.#.', '.#.', '.#.'],
    '8': ['###', '#.#', '###', '#.#', '###'], '9': ['###', '#.#', '###', '..#', '##.'],
    '-': ['...', '...', '###', '...', '...'], '.': ['...', '...', '...', '...', '.#.'],
    ':': ['...', '.#.', '...', '.#.', '...'], '/': ['..#', '..#', '.#.', '#..', '#..'],
    ',': ['...', '...', '...', '.#.', '#..'], '(': ['.#.', '#..', '#..', '#..', '.#.'],
    ')': ['.#.', '..#', '..#', '..#', '.#.'], ' ': ['...', '...', '...', '...', '...'],
    # round 9 (tools/pixelgen/pixfont_umlauts.py): 6 rows -- the dots one row above the line, a blank row, the
    # letter one row shorter, so Ä / Ö / Ü never read as A / O / U at 1x
    'Ä': ['#.#', '...', '.#.', '#.#', '###', '#.#'], 'Ö': ['#.#', '...', '.#.', '#.#', '#.#', '.#.'],
    'Ü': ['#.#', '...', '#.#', '#.#', '#.#', '###'],
    '!': ['.#.', '.#.', '.#.', '...', '.#.'], '·': ['...', '...', '.#.', '...', '...'],
    # section sign: 7 rows (one above, one below the 5-row line) so it never reads as "5"
    '§': ['.##.', '#...', '.##.', '#..#', '.##.', '...#', '.##.'],
    '„': ['...', '...', '...', '#.#', '#.#'],
    '“': ['#.#', '#.#', '...', '...', '...'], '–': ['...', '...', '###', '...', '...'],
    '→': ['.....', '...#.', '#####', '...#.', '.....'],
}
F57 = {
    'A': ['.###.', '#...#', '#...#', '#####', '#...#', '#...#', '#...#'],
    'B': ['####.', '#...#', '#...#', '####.', '#...#', '#...#', '####.'],
    'D': ['####.', '#...#', '#...#', '#...#', '#...#', '#...#', '####.'],
    'E': ['#####', '#....', '#....', '####.', '#....', '#....', '#####'],
    'G': ['.###.', '#...#', '#....', '#.###', '#...#', '#...#', '.####'],
    'I': ['.###.', '..#..', '..#..', '..#..', '..#..', '..#..', '.###.'],
    'K': ['#...#', '#..#.', '#.#..', '##...', '#.#..', '#..#.', '#...#'],
    'L': ['#....', '#....', '#....', '#....', '#....', '#....', '#####'],
    'N': ['#...#', '##..#', '#.#.#', '#..##', '#...#', '#...#', '#...#'],
    'O': ['.###.', '#...#', '#...#', '#...#', '#...#', '#...#', '.###.'],
    'R': ['####.', '#...#', '#...#', '####.', '#.#..', '#..#.', '#...#'],
    'S': ['.####', '#....', '#....', '.###.', '....#', '....#', '####.'],
    'T': ['#####', '..#..', '..#..', '..#..', '..#..', '..#..', '..#..'],
    'U': ['#...#', '#...#', '#...#', '#...#', '#...#', '#...#', '.###.'],
    'Z': ['#####', '....#', '...#.', '..#..', '.#...', '#....', '#####'],
    '2': ['.###.', '#...#', '....#', '...#.', '..#..', '.#...', '#####'],
    ' ': ['.....'] * 7,
}


def text_mask(s: str, big=False, spacing=1) -> np.ndarray:
    """Bool mask of the lettering.  Small glyphs are 5 rows; 7-row glyphs (section sign) reach one
    row above and below, 6-row glyphs (the umlauts) one row above, so the mask of small text is 7 rows high
    with the line at rows 1..5."""
    f = F57 if big else F35
    gh = 7
    off = 0 if big else 1
    glyphs = [f.get(ch, f[' ']) for ch in s.upper()]
    w = sum(len(g[0]) + spacing for g in glyphs) - spacing if glyphs else 0
    m = np.zeros((gh, max(0, w)), bool)
    x = 0
    for g in glyphs:
        top = 0 if len(g) >= 6 else off
        for yy, row in enumerate(g):
            for xx, ch in enumerate(row):
                if ch == '#':
                    m[top + yy, x + xx] = True
        x += len(g[0]) + spacing
    return m


def text_w(s, big=False, spacing=1):
    return text_mask(s, big, spacing).shape[1]


def put_text(l, s, x, y, col, big=False, align='left', italic=False):
    """Draw pixel lettering with its cap line at y; align left/right/center relative to x.
    italic = handwriting: the upper rows are sheared one pixel to the right."""
    m = text_mask(s, big)
    w = m.shape[1]
    y0 = int(y) - (0 if big else 1)
    if align == 'right':
        x -= w
    elif align == 'center':
        x -= w // 2
    if not italic:
        l._put(m, int(x), y0, c(col))
        return int(x), w
    for yy in range(m.shape[0]):
        shift = 1 if yy < 3 else 0
        l._put(m[yy:yy + 1, :], int(x) + shift, y0 + yy, c(col))
    return int(x), w


# ----------------------------------------------------------------------------- shared pieces
def paper(l, seed, base=4.15, age=0.25, edge=12, x0=0, y0=0, w=None, h=None, grain=1.0):
    """Off-white document paper (dark PAPER ramp index 0 .. light 5), yellowing to the edges."""
    w = l.w if w is None else w
    h = l.h if h is None else h
    rng = np.random.default_rng(seed)
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    e = np.minimum(np.minimum(xx, w - 1 - xx), np.minimum(yy, h - 1 - yy))
    t = base - np.clip((edge - e) / edge, 0, 1) * (0.75 + age) \
        + (pg.value_noise(w, h, 36, seed, octaves=2) - 0.5) * (0.42 + age * 0.4) * grain
    dither_fill(l, np.ones((h, w), bool), x0, y0, t, PAPER)
    for _ in range(int((26 + age * 60) * grain)):             # fibre specks
        x, y = int(rng.integers(2, w - 2)), int(rng.integers(2, h - 2))
        l.px(x0 + x, y0 + y, c(PAPER[3] if rng.random() < 0.7 else PAPER[2]))


EMBLEM = [   # fictional arms of the Free City of Veltrava (C3_DESIGN §4.1): white three-arch bridge
    '.###########.',   # (wider middle arch) over a wavy river line, on a slate-blue shield. 13 x 11
    '#############',
    '#############',
    '#WWWWWWWWWWW#',
    '#W##WW.WW##W#',
    '#W..W...W..W#',
    '#W..W...W..W#',
    '#############',
    '#ww.ww.ww.ww#',
    '.#..ww.ww..#.',
    '...#######...',
]


def emblem(l, x, y):
    cols = {'#': c(SLATE[2]), 'W': c(PAPER[5]), 'w': c(BLUE[5]), '.': None}
    for yy, row in enumerate(EMBLEM):
        for xx, ch in enumerate(row):
            col = cols.get(ch)
            if col is not None:
                l.px(x + xx, y + yy, col)
    l.rect(x + 1, y + 1, 11, 1, c(SLATE[3]))                  # top light on the shield


def punch_hole(l, cx, cy, r=2.6):
    l.ellipse(cx + 0.6, cy + 0.6, r + 0.6, r + 0.6, c(PAPER[2]))
    l.ellipse(cx, cy, r, r, c(NIGHT1))
    l.px(int(cx) - 1, int(cy) - 1, c(NAVY_L))


def clip(l, x, y, length=20):
    """Steel paper clip over the top edge (two nested loops)."""
    steel_d, steel, steel_l = c(WALL[2]), c(WALL[4]), c(BLUE[5])
    pts_outer = [(x, y - 2), (x, y + length - 4), (x + 2, y + length - 1), (x + 5, y + length - 1),
                 (x + 7, y + length - 4), (x + 7, y + 1)]
    pts_inner = [(x + 2, y - 2), (x + 2, y + length - 7), (x + 3, y + length - 5), (x + 4, y + length - 5),
                 (x + 5, y + length - 7), (x + 5, y + 3)]
    for pts, col in ((pts_outer, steel), (pts_inner, steel_d)):
        for (ax, ay), (bx, by) in zip(pts[:-1], pts[1:]):
            l.line(ax, ay, bx, by, col)
    l.line(x + 7, y + 1, x + 7, y + length - 5, steel_l)
    # clip shadow on the paper
    for k in range(length - 2):
        if 0 <= y + k < l.h and l.c[y + k, x + 8, 3] > 0:
            l.px(x + 8, y + k, c(PAPER[3]))


# ============================================================================ seating plan
# Geometry in plan pixels.  Mic numbering (C3_DESIGN §2.7): clockwise from the presidium (1);
# right arm going down 2-5 = Sowjetische Delegation; bottom right / bottom left corner 6, 7 =
# observers (Sweden, Switzerland); left arm going up 8-11 = Reichsdelegation; secretariat table
# at the open end in the middle = 12.  The plan prints only 1, 2 and 12.
PW, PH = 232, 160


def plan_geometry():
    cx = 122                      # horseshoe axis (right of centre: the left label is the longest)
    tw = 6                        # table depth
    half = 29                     # half of the inner opening
    top = 40                      # top edge of the presidium table
    arm_end = 101                 # last table row of the arms
    sw = sh = 6                   # chair
    gap = 2                       # chair <-> table
    pitch = 13
    lx0, lx1 = cx - half - tw, cx - half - 1          # left arm columns (inclusive)
    rx0, rx1 = cx + half, cx + half + tw - 1          # right arm columns
    table = {
        'top': [lx0, top, rx1 - lx0 + 1, tw],
        'left': [lx0, top, tw, arm_end - top + 1],
        'right': [rx0, top, tw, arm_end - top + 1],
        'secretariat': [cx - 12, 108, 25, 6],
    }
    arm_y = [top + tw + 2 + k * pitch for k in range(4)]          # 48, 61, 74, 87
    seats = []

    def seat(mic, block, x, y, back):
        seats.append({'mic': mic, 'block': block, 'rect': [x, y, sw, sh], 'back': back})

    seat(1, 'chair', cx - 3, top - gap - sh, 'top')
    for k, y in enumerate(arm_y):                                  # right arm, going down
        seat(2 + k, 'soviet', rx1 + 1 + gap, y, 'right')
    seat(6, 'observer_se', rx0, arm_end + 1 + gap, 'bottom')        # bottom right corner
    seat(7, 'observer_ch', lx0, arm_end + 1 + gap, 'bottom')        # bottom left corner
    for k, y in enumerate(reversed(arm_y)):                        # left arm, going up
        seat(8 + k, 'reich', lx0 - gap - sw, y, 'left')
    st = table['secretariat']
    seat(12, 'secretariat', cx - 3, st[1] + st[3] + 2, 'bottom')
    # microphones: 2x2 ink dot on the table edge facing each chair
    for s in seats:
        x, y, w, h = s['rect']
        mcx, mcy = x + w // 2 - 1, y + h // 2 - 1
        if s['back'] == 'top':
            s['mic_px'] = [mcx, top + 1]
        elif s['back'] == 'right':
            s['mic_px'] = [rx1 - 2, mcy]
        elif s['back'] == 'left':
            s['mic_px'] = [lx0 + 1, mcy]
        elif s['mic'] == 12:
            s['mic_px'] = [mcx, st[1] + st[3] - 3]
        else:
            s['mic_px'] = [mcx, arm_end - 2]
    by = {s['mic']: s for s in seats}
    s1, s2, s12 = by[1]['rect'], by[2]['rect'], by[12]['rect']
    tags = {   # printed number rings (the only numbers on the plan)
        '1': [s1[0] - 11, s1[1] - 2, 9, 9],
        '2': [s2[0] + s2[2] + 2, s2[1] - 2, 9, 9],
        '12': [s12[0] - 13, s12[1] - 2, 11, 9],
    }
    lab_l = 13                                           # left label column (3 px clear of the wall)
    lab_r = PW - 12                                      # right edge of the right label column
    labels = {   # HD label boxes on the board / pixel lettering on the document
        'title': [10, 8, 150, 10],
        'subtitle': [100, 9, 106, 8],
        'chair': [s1[0] + s1[2] + 4, s1[1] - 1, 44, 8],
        'soviet': [tags['2'][0] + tags['2'][2] + 2, arm_y[1] - 3, lab_r - (tags['2'][0] + tags['2'][2] + 2), 20],
        'reich': [lab_l, arm_y[1] + 2, (lx0 - gap - sw - 3) - lab_l, 9],
        'observer_se': [rx1 + 4, arm_end - 1, 42, 15],          # narrow: always two lines
        'observer_ch': [(lx0 - 4) - 42, arm_end - 1, 42, 15],
        'secretariat': [cx - 24, s12[1] + s12[3] + 2, 49, 8],
        'booths': [180, 33, 40, 7],
        'legend': [14, 145, 186, 9],
    }
    return {'cx': cx, 'table': table, 'seats': seats, 'tags': tags, 'labels': labels,
            'arm_y': arm_y, 'top': top, 'arm_end': arm_end, 'hall': [8, 23, PW - 16, 121],
            'door': [cx - 8, 23 + 121 - 2, 17, 2], 'booth_strip': [180, 26, 40, 5],
            'clockwise': [PW - 25, 145, 11, 10]}


def draw_plan(with_text: bool):
    G = plan_geometry()
    l = L(PW, PH)
    paper(l, seed=731, base=4.15, age=0.22)
    # faint printed construction grid (dotted, every 16 px) -- diazo blue, very light
    for gx in range(16, PW - 6, 16):
        for y in range(7, PH - 7, 3):
            l.px(gx, y, c(BLUE[5]))
    for gy in range(16, PH - 6, 16):
        for x in range(7, PW - 7, 3):
            l.px(x, gy, c(BLUE[5]))
    # sheet frame (double rule)
    ring(l, 3, 3, PW - 6, PH - 6, c(BLUE[2]))
    ring(l, 5, 5, PW - 10, PH - 10, c(BLUE[4]))
    # title band + rule
    l.rect(6, 6, PW - 12, 15, c(PAPER[5]))
    l.rect(6, 21, PW - 12, 1, c(BLUE[3]))
    emblem(l, PW - 23, 8)
    # ---- hall walls (2 px poché) with windows (left) and the double door (bottom)
    hx0, hy0, hw, hh = G['hall']
    wall = c(BLUE[1])
    l.rect(hx0, hy0, hw, 2, wall)
    l.rect(hx0, hy0 + hh - 2, hw, 2, wall)
    l.rect(hx0, hy0, 2, hh, wall)
    l.rect(hx0 + hw - 2, hy0, 2, hh, wall)
    for wy in (34, 68, 102):                                   # windows: gap + thin double line
        l.rect(hx0, wy, 2, 18, c(PAPER[5]))
        l.rect(hx0, wy, 1, 18, c(BLUE[3]))
        l.rect(hx0 + 1, wy, 1, 18, c(BLUE[4]))
        l.rect(hx0, wy - 1, 2, 1, wall)
        l.rect(hx0, wy + 18, 2, 1, wall)
    dx, dy, dw, _ = G['door']
    l.rect(dx, hy0 + hh - 2, dw, 2, c(PAPER[4]))
    wy = hy0 + hh - 3                                           # inner face of the bottom wall
    r = dw // 2                                                 # double door: two leaves of r px
    for hinge, sgn in ((dx, 1), (dx + dw - 1, -1)):            # leaves open 90 deg into the hall
        l.rect(hinge, wy - r + 1, 1, r, c(BLUE[2]))
        for i, a in enumerate(np.linspace(0, math.pi / 2, 34)):
            if i % 3 != 2:                                      # dotted swing arc
                l.px(hinge + sgn * round(math.cos(a) * (r - 1)), wy - round(math.sin(a) * (r - 1)), c(BLUE[4]))
    l.rect(dx - 1, wy - 1, 1, 3, wall)                          # door jambs
    l.rect(dx + dw, wy - 1, 1, 3, wall)
    # interpreters' booths: glazed strip in the top wall (gallery), three bays
    bx, byy, bw, bh = G['booth_strip']
    l.rect(bx, byy, bw, bh, c(PAPER[5]))
    ring(l, bx, byy, bw, bh, c(BLUE[2]))
    for k in range(1, 3):
        l.rect(bx + k * bw // 3, byy, 1, bh, c(BLUE[2]))
    for k in range(3):
        for xx in range(bx + 2 + k * bw // 3, bx + (k + 1) * bw // 3 - 1, 2):
            l.px(xx, byy + 2, c(BLUE[4]))
    # ---- tables: outline + light diagonal hatch (furniture)
    def table_box(rect):
        x, y, w, h = rect
        l.rect(x, y, w, h, c(PAPER[5]))
        for yy in range(y + 1, y + h - 1):
            for xx in range(x + 1, x + w - 1):
                if (xx + yy) % 3 == 0:
                    l.px(xx, yy, c(BLUE[5]))
    T = G['table']
    for k in ('top', 'left', 'right', 'secretariat'):
        table_box(T[k])
    # one continuous outline around the U
    tx0, ty0, tw_, th_ = T['top']
    lx, _, lw, lh = T['left']
    rx, _, rw, _ = T['right']
    ink = c(BLUE[1])
    l.rect(tx0, ty0, tw_, 1, ink)                               # outer top
    l.rect(tx0, ty0, 1, lh, ink)                                # outer left
    l.rect(rx + rw - 1, ty0, 1, lh, ink)                        # outer right
    l.rect(lx, ty0 + lh - 1, lw, 1, ink)                        # arm ends
    l.rect(rx, ty0 + lh - 1, rw, 1, ink)
    l.rect(lx + lw - 1, ty0 + th_ - 1, 1, lh - th_ + 1, ink)    # inner left
    l.rect(rx, ty0 + th_ - 1, 1, lh - th_ + 1, ink)             # inner right
    l.rect(lx + lw - 1, ty0 + th_ - 1, rx - (lx + lw - 1) + 1, 1, ink)   # inner top
    sx, sy, sw_, sh_ = T['secretariat']
    ring(l, sx, sy, sw_, sh_, ink)
    # ---- chairs with backs, microphones
    for s in G['seats']:
        x, y, w, h = s['rect']
        l.rect(x, y, w, h, c(PAPER[5]))
        ring(l, x, y, w, h, c(BLUE[2]))
        if s['back'] == 'top':
            l.rect(x, y, w, 2, c(BLUE[1]))
        elif s['back'] == 'bottom':
            l.rect(x, y + h - 2, w, 2, c(BLUE[1]))
        elif s['back'] == 'left':
            l.rect(x, y, 2, h, c(BLUE[1]))
        elif s['back'] == 'right':
            l.rect(x + w - 2, y, 2, h, c(BLUE[1]))
        mx, my = s['mic_px']
        l.rect(mx, my, 2, 2, c(INK))
    # ---- number rings (1, 2, 12): ring outline, the digit goes inside
    for key, (x, y, w, h) in G['tags'].items():
        l.rect(x + 1, y + 1, w - 2, h - 2, c(PAPER[5]))
        ring(l, x, y, w, h, c(INK_B), round_corners=True)
        l.rect(x + 1, y + 1, w - 2, 1, c(PAPER[5]))
    # ---- legend pictogram: clockwise arrow (three quarters of a circle, head pointing down on the right)
    ax, ay, aw, ah = G['clockwise']
    CW = ['...####....',
          '..#....#...',
          '.#......#..',
          '#........#.',
          '#.......###',
          '#........#.',
          '#..........',
          '.#.........',
          '..#....#...',
          '...####....']
    for yy, row in enumerate(CW):
        for xx, ch in enumerate(row):
            if ch == '#':
                l.px(ax + xx, ay + yy, c(BLUE[1]))
    l.rect(ax + 4, ay + 4, 2, 2, c(INK))                        # the microphone dot at the centre
    if with_text:
        draw_plan_text(l, G)
    return l, G


PLAN_DOC_TEXT = {   # in-world lettering of the inspect document (German, capitals)
    'title': 'SITZORDNUNG',
    'subtitle': 'GROSSER SAAL · ERÖFFNUNG',
    'chair': ['VORSITZ'],
    'soviet': ['SOWJETISCHE', 'DELEGATION'],
    'reich': ['REICHSDELEGATION'],
    'observer_se': ['BEOBACHTER', 'SCHWEDEN'],
    'observer_ch': ['BEOBACHTER', 'SCHWEIZ'],
    'secretariat': ['SEKRETARIAT'],
    'booths': ['KABINEN'],
    'legend': 'MIKROFONE IM UHRZEIGERSINN AB VORSITZ (1)',
}


def draw_plan_text(l, G):
    lab = G['labels']
    blue, ink = BLUE[1], INK
    x, y, w, h = lab['title']
    put_text(l, PLAN_DOC_TEXT['title'], x, y + 1, blue, big=True)
    x, y, w, h = lab['subtitle']
    put_text(l, PLAN_DOC_TEXT['subtitle'], x + w - 16, y + 2, BLUE[2], align='right')
    for key, align in (('chair', 'left'), ('soviet', 'left'), ('reich', 'right'), ('observer_se', 'left'),
                       ('observer_ch', 'right'), ('secretariat', 'center'), ('booths', 'center')):
        x, y, w, h = lab[key]
        lines = PLAN_DOC_TEXT[key]
        top = y + (h - (len(lines) * 7 - 2)) // 2
        for i, s in enumerate(lines):
            ax = x if align == 'left' else (x + w if align == 'right' else x + w // 2)
            put_text(l, s, ax, top + i * 7, blue if key != 'booths' else BLUE[3], align=align)
    for key, (x, y, w, h) in G['tags'].items():
        put_text(l, key, x + w // 2 + (1 if len(key) == 1 else 1), y + 2, ink, align='center')
    x, y, w, h = lab['legend']
    put_text(l, PLAN_DOC_TEXT['legend'], x, y + 2, blue)


# ============================================================================ booth log
LW, LH = 168, 160
LOG_ROW0 = 40            # first text row (board); rows are 8 px apart, rule under each row
LOG_PITCH = 8
# board rows: (entry, kind) -- kind a = time/mic/channel line, b = remark, n = Elena's note
LOG_ROWS = [(1, 'a'), (1, 'b'), (2, 'a'), (2, 'b'), (2, 'b'), (3, 'a'), (3, 'b'), (3, 'n'), (4, 'a'), (4, 'b')]
LOG_COLS = {'time': 22, 'mic': 47, 'channel': 61, 'remark': 30, 'note': 30, 'right': 160}
# monospace advance of the typed board text (Courier Prime 20 px = 12 screen px = 4 art px) and the
# position of "§ 4" inside the 10.09 remark ("verliest § 4 ..."), underlined by Elena
TYPE_ADV = 4
PARA_CHARS = (9, 3)
LOG_ENTRIES = [   # canonical facts (C3_DESIGN §2.7) -- the HD board text comes from Loc keys
    {'time': '10.02', 'mic': '1', 'channel': 'FR → DE/RU', 'remark': ['ERÖFFNUNG TOP 4 „ANLAGE C“']},
    {'time': '10.06', 'mic': '9', 'channel': 'DE → RU',
     'remark': ['„KEINE EINWÄNDE GEGEN DIE', 'FASSUNG VOM 12. JANUAR.“']},
    {'time': '10.09', 'mic': '12', 'channel': 'FR → DE/RU', 'remark': ['VERLIEST § 4 (VORBEREITETER TEXT)'],
     'note': ['RU: BEGLEITETE PERSONEN –', 'DE: BEGLEITGUT!']},
    {'time': '10.11', 'mic': '3', 'channel': 'RU → DE', 'remark': ['„WIR SCHLIESSEN UNS AN.“']},
]


def log_base(rows_used: int, row0: int, entry_breaks, seed=811):
    """Typed form: paper, letterhead band, column head, rules every 8 px, red margin, holes, clip."""
    l = L(LW, LH)
    paper(l, seed=seed, base=4.55, age=0.14, edge=10, grain=0.6)
    # letterhead band (pre-printed): slate rule + emblem
    emblem(l, 22, 4)
    l.rect(37, 15, LW - 54, 1, c(SLATE[3]))
    # double rule under the header block
    l.rect(20, row0 - 14, LW - 28, 1, c(BLUE[2]))
    l.rect(20, row0 - 12, LW - 28, 1, c(BLUE[4]))
    # column head band
    l.rect(20, row0 - 11, LW - 28, 8, c(PAPER[4]))
    l.rect(20, row0 - 3, LW - 28, 1, c(BLUE[3]))
    # ruled lines under every row (light blue), a slightly stronger rule between entries
    y = row0
    k = 0
    while y + LOG_PITCH <= LH - 6:
        ry = y + LOG_PITCH - 1
        strong = k in entry_breaks
        for x in range(20, LW - 8):
            if strong or x % 2 == 0 or True:
                l.px(x, ry, c(BLUE[4] if strong else BLUE[5]))
        y += LOG_PITCH
        k += 1
    # red margin rule
    l.rect(18, 4, 1, LH - 8, c(RED))
    l.rect(19, 4, 1, LH - 8, c(PAPER[3]))
    # punch holes + clip
    punch_hole(l, 8, 42)
    punch_hole(l, 8, 118)
    clip(l, LW - 14, 0, 22)
    return l


def draw_log():
    """Board version: the form + Elena's ink marks; the typed rows are HD text placed on LOG_ROWS."""
    entry_breaks_board = [1, 4, 7, 9]           # row index whose rule closes an entry
    rows = LOG_ROWS
    l = log_base(len(rows), LOG_ROW0, entry_breaks_board)
    meta = {'rows': [], 'row0': LOG_ROW0, 'pitch': LOG_PITCH, 'cols': LOG_COLS}
    for i, (entry, kind) in enumerate(rows):
        meta['rows'].append({'entry': entry, 'kind': kind, 'y': LOG_ROW0 + i * LOG_PITCH, 'h': LOG_PITCH})
    note_row = [i for i, r in enumerate(rows) if r[1] == 'n'][0]
    para_row = note_row - 1
    ux = LOG_COLS['remark'] + PARA_CHARS[0] * TYPE_ADV
    _elena_marks(l, LOG_ROW0 + (note_row - 2) * LOG_PITCH, LOG_ROW0 + note_row * LOG_PITCH,
                 (ux, LOG_ROW0 + para_row * LOG_PITCH + 6, PARA_CHARS[1] * TYPE_ADV - 1))
    meta['para_underline'] = [ux, LOG_ROW0 + para_row * LOG_PITCH + 6, PARA_CHARS[1] * TYPE_ADV - 1, 1]
    return l, meta


def _elena_marks(l, y_entry, y_note, underline=None):
    """Elena's fountain-pen marks at 10.09: a bracket over the whole entry in the left margin and a
    stroke under "§ 4" (the note text itself is HD on the board / pixel handwriting on the document)."""
    pen = c(INK_B)
    x = 14
    top, bot = y_entry, y_note + LOG_PITCH - 2
    l.rect(x, top + 1, 1, bot - top - 1, pen)
    l.px(x + 1, top, pen); l.px(x + 2, top, pen)
    l.px(x + 1, bot, pen); l.px(x + 2, bot, pen)
    l.px(x - 1, (top + bot) // 2, pen)
    if underline:
        ux, uy, uw = underline
        for k in range(uw + 2):
            l.px(ux - 1 + k, uy + (1 if k in (0, uw + 1) else 0), pen)


def draw_log_doc():
    """In-world document: same form, pixel typewriter rows + Elena's handwriting."""
    row0 = 56
    rows = []
    for e_i, e in enumerate(LOG_ENTRIES):
        rows.append((e_i, 'a', None))
        for s in e['remark']:
            rows.append((e_i, 'b', s))
        for s in e.get('note', []):
            rows.append((e_i, 'n', s))
    breaks = []
    for i in range(len(rows) - 1):
        if rows[i + 1][0] != rows[i][0]:
            breaks.append(i)
    breaks.append(len(rows) - 1)
    l = log_base(len(rows), row0, breaks, seed=812)
    ink = INK
    put_text(l, 'KABINE 2 · RU-DE · E. WEISS', 38, 7, BLUE[1])
    put_text(l, 'TOP 4 · ANLAGE C –', 22, row0 - 34, ink)
    put_text(l, 'LOGISTIKINTEGRATION', 22, row0 - 26, ink)
    put_text(l, 'ZEIT', LOG_COLS['time'], row0 - 9, BLUE[2])
    put_text(l, 'MIK', LOG_COLS['mic'], row0 - 9, BLUE[2])
    put_text(l, 'KANAL / VERMERK', LOG_COLS['channel'], row0 - 9, BLUE[2])
    note_rows = []
    para = None
    for i, (e_i, kind, s) in enumerate(rows):
        y = row0 + i * LOG_PITCH + 1
        e = LOG_ENTRIES[e_i]
        if kind == 'a':
            put_text(l, e['time'], LOG_COLS['time'], y, ink)
            put_text(l, e['mic'], LOG_COLS['mic'], y, ink)
            put_text(l, e['channel'], LOG_COLS['channel'], y, ink)
        elif kind == 'b':
            put_text(l, s, LOG_COLS['remark'], y, ink)
            if '§' in s:
                k = s.index('§')
                para = (LOG_COLS['remark'] + text_w(s[:k]) + 1, row0 + i * LOG_PITCH + 7, text_w('§ 4'))
        else:
            note_rows.append(i)
            put_text(l, s, LOG_COLS['note'] + 2, y, INK_B, italic=True)
    # underline "BEGLEITGUT!" (her emphasis)
    last = note_rows[-1]
    uy = row0 + last * LOG_PITCH + 7
    ux = LOG_COLS['note'] + 2 + text_w('DE: ')
    uw = text_w('BEGLEITGUT!')
    for k in range(uw + 1):
        l.px(ux + k, uy - (1 if k % 9 == 4 else 0), c(INK_B))
    entry3 = [i for i, r in enumerate(rows) if r[0] == 2]
    _elena_marks(l, row0 + entry3[0] * LOG_PITCH, row0 + note_rows[-1] * LOG_PITCH, para)
    # initials at the foot of the sheet
    put_text(l, 'E.W.', LW - 30, LH - 13, INK_B, italic=True)
    meta = {'rows': [{'entry': r[0] + 1, 'kind': r[1], 'y': row0 + i * LOG_PITCH} for i, r in enumerate(rows)]}
    return l, meta


# ============================================================================ cards, glyphs, slots
CARD_W, CARD_H = 98, 28
CARD_GLYPH = {'chair': 'circle', 'reich': 'square', 'soviet': 'triangle', 'secretariat': 'diamond'}


def glyph_mask(shape: str, s: int) -> np.ndarray:
    """Filled shape in an s x s box (s odd)."""
    yy, xx = np.mgrid[0:s, 0:s].astype(np.float32)
    cc = (s - 1) / 2.0
    if shape == 'circle':
        return (xx - cc) ** 2 + (yy - cc) ** 2 <= (s / 2.0 - 0.2) ** 2
    if shape == 'square':
        m = np.zeros((s, s), bool)
        m[1:s - 1, 1:s - 1] = True
        return m
    if shape == 'diamond':
        return np.abs(xx - cc) + np.abs(yy - cc) <= cc + 0.25
    if shape == 'triangle':
        m = np.zeros((s, s), bool)
        for y in range(1, s):
            half = (y - 0.5) / (s - 1) * (s / 2.0)
            x0, x1 = int(round(cc - half)), int(round(cc + half))
            m[y, max(0, x0):min(s, x1 + 1)] = True
        m[s - 1, :] = m[s - 2, :] if s > 2 else m[s - 1, :]
        return m
    raise ValueError(shape)


def glyph_sprite(shape: str, s: int = 7, col=INK) -> pg.Layer:
    l = L(s, s)
    l._put(glyph_mask(shape, s), 0, 0, c(col))
    return l


def card(card_id: str) -> pg.Layer:
    """Folded conference name plate (Tischkarte): paper face, slate top stripe of the commission,
    fold shadow, glyph box at the left.  The name is HD text set by the UI."""
    w, h = CARD_W, CARD_H
    l = L(w, h)
    rng = np.random.default_rng(sum(map(ord, card_id)))
    edge = c(NIGHT)
    l.rect(1, 0, w - 2, h, edge)
    l.rect(0, 1, w, h - 2, edge)
    l.rect(1, 1, w - 2, h - 2, c(PAPER[4]))
    l.rect(1, 1, w - 2, 1, c(PAPER[5]))
    l.rect(1, 2, w - 2, 2, c(SLATE[3]))                       # commission stripe
    l.rect(1, 4, w - 2, 1, c(SLATE[2]))
    l.rect(1, h - 4, w - 2, 1, c(PAPER[3]))                   # fold / bottom shading
    l.rect(1, h - 3, w - 2, 2, c(PAPER[2]))
    l.rect(w - 2, 5, 1, h - 9, c(PAPER[3]))
    # glyph box
    gx0, gy0, gs = 5, 8, 15
    l.rect(gx0, gy0, gs, gs, c(PAPER[5]))
    ring(l, gx0, gy0, gs, gs, c(PAPER[2]), round_corners=True)
    g = glyph_mask(CARD_GLYPH[card_id], 11)
    l._put(g, gx0 + 2, gy0 + 2, c(INK))
    # divider between glyph and name
    l.rect(gx0 + gs + 3, 8, 1, 15, c(PAPER[3]))
    # paper wear specks
    for _ in range(7):
        x, y = int(rng.integers(26, w - 4)), int(rng.integers(6, h - 5))
        l.px(x, y, c(PAPER[5] if rng.random() < 0.5 else PAPER[3]))
    return l


def slot() -> pg.Layer:
    """Empty place in the order row: recessed dark field with a dashed rule (like card_slot)."""
    w, h = CARD_W, CARD_H
    l = L(w, h)
    l.rect(1, 1, w - 2, h - 2, c(NIGHT1, 210))
    for x in range(1, w - 1, 3):
        l.px(x, 0, c(WALL[3])); l.px(x + 1, 0, c(WALL[3]))
        l.px(x, h - 1, c(WALL[3])); l.px(x + 1, h - 1, c(WALL[3]))
    for y in range(1, h - 1, 3):
        l.px(0, y, c(WALL[3])); l.px(0, y + 1, c(WALL[3]))
        l.px(w - 1, y, c(WALL[3])); l.px(w - 1, y + 1, c(WALL[3]))
    l.rect(2, 2, w - 4, 1, c(NIGHT, 220))                    # inner top shadow (recess)
    return l


def seq_arrow() -> pg.Layer:
    l = L(5, 7)
    for y in range(7):
        d = 3 - abs(3 - y)
        l.rect(0, y, d + 1, 1, c(WALL[4]))
    return l


# ============================================================================ output
def save_png(layer: pg.Layer, path: str):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    Image.fromarray(layer.c, 'RGBA').save(path)


def rel(path: str) -> str:
    return 'res://' + os.path.relpath(path, ROOT).replace(os.sep, '/')


def check_solution(G):
    """The board must encode the canonical solution: chair, reich, secretariat, soviet."""
    by = {s['mic']: s['block'] for s in G['seats']}
    log_order = [by[int(e['mic'])] for e in LOG_ENTRIES]
    assert log_order == ['chair', 'reich', 'secretariat', 'soviet'], log_order
    # clockwise: arm seats on the right go down, on the left go up
    right = sorted([s for s in G['seats'] if s['block'] == 'soviet'], key=lambda s: s['mic'])
    assert [s['rect'][1] for s in right] == sorted(s['rect'][1] for s in right)
    left = sorted([s for s in G['seats'] if s['block'] == 'reich'], key=lambda s: s['mic'])
    assert [s['rect'][1] for s in left] == sorted((s['rect'][1] for s in left), reverse=True)
    assert set(G['tags']) == {'1', '2', '12'}
    return log_order


def main():
    preview = ''
    for a in sys.argv[1:]:
        if a.startswith('--preview='):
            preview = a.split('=', 1)[1]
    written = []
    # ---- board art
    plan, G = draw_plan(with_text=False)
    p = os.path.join(PUZ, 'c3_plan.png'); save_png(plan, p); written.append(p)
    log, LM = draw_log()
    p = os.path.join(PUZ, 'c3_log.png'); save_png(log, p); written.append(p)
    for cid in CARD_GLYPH:
        p = os.path.join(PUZ, 'c3_card_%s.png' % cid); save_png(card(cid), p); written.append(p)
    for shape in ('circle', 'square', 'triangle', 'diamond'):
        p = os.path.join(PUZ, 'c3_glyph_%s.png' % shape); save_png(glyph_sprite(shape, 7, BLUE[1]), p)
        written.append(p)
    p = os.path.join(PUZ, 'c3_slot.png'); save_png(slot(), p); written.append(p)
    p = os.path.join(PUZ, 'c3_seq_arrow.png'); save_png(seq_arrow(), p); written.append(p)
    order = check_solution(G)
    board = {
        'puzzle_id': 'pz_c3_protocol', 'objective': 'c3b_solve_protocol', 'display_scale': 3,
        'coords': 'art pixels from the top-left of each image ([x, y, w, h]); the UI multiplies by 3',
        'generator': GENERATOR, 'date': DATE,
        'plan': {'file': 'c3_plan.png', 'size': [PW, PH], 'labels': G['labels'], 'tags': G['tags'],
                 'seats': G['seats'], 'tables': G['table'], 'hall': G['hall'],
                 'numbering': 'clockwise from the presidium (1): right arm 2-5 going down, corners 6 (right) '
                              'and 7 (left), left arm 8-11 going up, secretariat table 12; printed: 1, 2, 12'},
        'log': {'file': 'c3_log.png', 'size': [LW, LH], 'row0': LM['row0'], 'pitch': LM['pitch'],
                'rows': LM['rows'], 'cols': LM['cols'], 'title': [38, 4, 112, 11], 'agenda': [22, 17, 138, 9],
                'head': [22, 29, 138, 8], 'para_underline': LM['para_underline'], 'type_advance': TYPE_ADV,
                'entries': [{'time': e['time'], 'mic': int(e['mic'])} for e in LOG_ENTRIES]},
        'card': {'size': [CARD_W, CARD_H], 'glyph_box': [5, 8, 15, 15], 'text': [27, 5, CARD_W - 31, 20],
                 'glyphs': CARD_GLYPH, 'files': {k: 'c3_card_%s.png' % k for k in CARD_GLYPH}},
        'slot': {'file': 'c3_slot.png', 'size': [CARD_W, CARD_H]},
        'seq_arrow': {'file': 'c3_seq_arrow.png', 'size': [5, 7]},
        'solution_check': {'log_order': order},
        'world_note': 'Fictional seating plan and interpreters\' booth log of a fictional conference; '
                      'not a real protocol.',
    }
    p = os.path.join(PUZ, 'c3_protocol_board.json')
    with open(p, 'w', encoding='utf-8') as f:
        json.dump(board, f, indent=1, ensure_ascii=False)
    written.append(p)
    # ---- inspect documents (in-world)
    doc_plan, _ = draw_plan(with_text=True)
    p_seat = os.path.join(DOCS, 'veltrava_protocol_seating.png'); save_png(doc_plan, p_seat); written.append(p_seat)
    doc_log, DLM = draw_log_doc()
    p_log = os.path.join(DOCS, 'veltrava_protocol_booth_log.png'); save_png(doc_log, p_log); written.append(p_log)
    docs = {
        'scene': 'L_C3_Hall',
        'palette': 'UI archive paper/blue/ink ramps + veltrava slate (commission)',
        'generator': GENERATOR, 'date': DATE,
        'note': 'Pixel art drawn 1:1, shown at 3x (nearest). In-world lettering in 3x5 / 5x7 pixel capitals; '
                'the plan prints only the microphone numbers 1, 2 and 12. All rects are [x, y, w, h] in '
                'document pixels. The puzzle board (assets/ui/puzzle/c3_*) uses the same drawing without '
                'lettering and sets the words in HD.',
        'documents': [
            {'file': rel(p_seat), 'size': [PW, PH], 'display_scale': 3, 'id': 'veltrava_protocol_seating',
             'alt_key': 'doc.c3.seating.alt', 'item_id': 'ev_c3_seating', 'objective': 'c3b_inspect_seating',
             'hotspot': 'seating', 'title_key': 'item.c3_seating.name',
             'description_key': 'item.c3_seating.description',
             'describes': 'Seating plan of the opening session: horseshoe table in the Großer Saal, presidium on '
                          'top (mic 1), right arm Soviet delegation (first mic printed 2), corner seats observers '
                          'Sweden (right) and Switzerland (left), left arm Reich delegation, secretariat table at '
                          'the open end (mic 12). Legend: microphones clockwise from the chair (1).',
             'marks': {
                 'mic_1': {'rect': G['tags']['1'], 'seat': next(s['rect'] for s in G['seats'] if s['mic'] == 1)},
                 'mic_2': {'rect': G['tags']['2'], 'seat': next(s['rect'] for s in G['seats'] if s['mic'] == 2)},
                 'mic_12': {'rect': G['tags']['12'], 'seat': next(s['rect'] for s in G['seats'] if s['mic'] == 12)},
                 'legend': {'rect': G['labels']['legend'], 'text': PLAN_DOC_TEXT['legend']},
                 'blocks': {k: G['labels'][k] for k in ('chair', 'soviet', 'reich', 'observer_se',
                                                       'observer_ch', 'secretariat')},
                 'seats': [{'mic': s['mic'], 'block': s['block'], 'rect': s['rect']} for s in G['seats']],
             }},
            {'file': rel(p_log), 'size': [LW, LH], 'display_scale': 3, 'id': 'veltrava_protocol_booth_log',
             'alt_key': 'doc.c3.booth_log.alt', 'item_id': 'ev_c3_booth_log', 'objective': 'c3b_inspect_log',
             'hotspot': 'booth_log', 'title_key': 'item.c3_booth_log.name',
             'description_key': 'item.c3_booth_log.description',
             'describes': "Elena Weiss' booth log, Kabine 2 (RU-DE), agenda item 4 'Anlage C': 10.02 mic 1 FR, "
                          "10.06 mic 9 DE, 10.09 mic 12 FR reads out § 4 (prepared text) with her handwritten "
                          "margin note 'RU: begleitete Personen - DE: Begleitgut!', 10.11 mic 3 RU.",
             'marks': {
                 'rows': DLM['rows'],
                 'entries': [{'time': e['time'], 'mic': int(e['mic']), 'channel': e['channel']} for e in LOG_ENTRIES],
                 'margin_note': {'entry': 3, 'text': 'RU: begleitete Personen – DE: Begleitgut!',
                                 'medium': 'fountain pen'},
             }},
        ],
    }
    p = os.path.join(DOCS, 'veltrava_protocol_documents.json')
    with open(p, 'w', encoding='utf-8') as f:
        json.dump(docs, f, indent=1, ensure_ascii=False)
    written.append(p)
    if preview:
        os.makedirs(preview, exist_ok=True)
        for name, layer in (('plan', plan), ('log', log), ('doc_seating', doc_plan), ('doc_log', doc_log),
                            ('card_chair', card('chair')), ('slot', slot())):
            Image.fromarray(layer.c, 'RGBA').resize((layer.w * 3, layer.h * 3), Image.NEAREST).save(
                os.path.join(preview, 'c3_%s_x3.png' % name))
        sheet = Image.new('RGBA', (1300, 1300), tuple(int(v) for v in c(NAVY)))
        x = y = 12
        for name, layer in (('plan', doc_plan), ('log', doc_log)):
            im = Image.fromarray(layer.c, 'RGBA').resize((layer.w * 3, layer.h * 3), Image.NEAREST)
            sheet.alpha_composite(im, (x, y)); x += im.width + 12
        x, y = 12, 500
        for cid in CARD_GLYPH:
            im = Image.fromarray(card(cid).c, 'RGBA').resize((CARD_W * 3, CARD_H * 3), Image.NEAREST)
            sheet.alpha_composite(im, (x, y)); x += im.width + 12
        im = Image.fromarray(slot().c, 'RGBA').resize((CARD_W * 3, CARD_H * 3), Image.NEAREST)
        sheet.alpha_composite(im, (12, 600))
        sheet.save(os.path.join(preview, 'c3_contact_sheet.png'))
    for p in written:
        print('wrote', os.path.relpath(p, ROOT))


if __name__ == '__main__':
    main()
