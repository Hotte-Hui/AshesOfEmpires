"""gen_ui_c4 -- puzzle art of Chapter 4 part 1 „Stimmen unter Beton“ (documentation/C4_DESIGN.md §2.7, §10).

Owner: puzzle UI stream.  Two puzzles:

* pz_c4_numbers „Die Nummernkette“ (objective c4c_solve_numbers, scenes/ui/TracePuzzle.tscn): a slate board in
  the siding hut with Service Tunnel 3 drawn in chalk -- freight yard, four switch posts W1-W4 with an iron hook
  each, the siding with its buffer stop.  Four paint layers of ONE wagon are shown as number plates (enamel
  „24 318“, stencil „C-17/42“, brush „47 702“, wet stencil „C-17/45“).  The `_lit` variant of every plate is
  the plate held against the hand lamp (Gegenlicht): the face paint turns to a ghost and the older number
  under it shows dark -- under „24 318“ there is only bare metal.  A small painted wagon token rolls along
  the chalk track and shows the number of the post it stands at (mini plates, 3x5 type).
* pz_c4_routes „Linie 74“ (objective c4b_solve_routes, scenes/ui/RoutePuzzle.tscn): the site plan Süd 8 from
  the eviction notice (north up, three shaft rings S 1-S 3) and Marta's tracing paper with line 74 and the
  three detours of October, December and January (diamond marks), drawn in driving direction -- i.e. turned
  90 degrees against the plan.  Layout file assets/ui/documents/berlin_c4_routes.json (cell size, files,
  landmarks, start pose, board).  The geometry is verified here against data/v3/puzzles.json: exactly one
  rotation and one offset bring every diamond onto its ring, and it is the solution of pz_c4_routes.

Everything is drawn at 1:1 (one art pixel = one world pixel) and shown at x3 with nearest filtering, so every
digit stroke is >= 3 screen px.  Words are set in HD by the UI from Loc keys (ui.c4.numbers.* /
ui.c4.routes.*); the only painted characters are the wagon numbers themselves and Marta's pencil dates
(OKT. / DEZ. / JAN. / 74), in this file's own pixel types.  Nothing is sampled from outside the repository and
nothing is traced; all randomness uses fixed seeds (deterministic output).

Run:  py -3 -P tools/pixelgen/gen_ui_c4.py [--preview=DIR]
      --preview writes an x2 contact sheet to DIR (outside the repo).
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
DATE = '2026-11-06'
GENERATOR = 'tools/pixelgen/gen_ui_c4.py'

# ----------------------------------------------------------------------------- palette (UI / archive ramps)
NIGHT, NIGHT1, NAVY = '#04090D', '#06151D', '#0B1C24'
WALL = ['#1A2A2E', '#24373A', '#354448', '#4A5A5B', '#62716E']
PAPER = ['#6E6A5C', '#8E8A78', '#B0AA93', '#CEC6AA', '#E6DEC2', '#F5EFDA']
INK, INK_B, INK_DIM, BLUE_INK = '#1A1C2A', '#2E3248', '#4D4A42', '#2B3C50'
RED_D, RED = '#7A2A26', '#A8382E'
AMBER, AMBER_L, COPPER_L = '#F0C487', '#FFE2A8', '#DCA16E'
CHALK = ['#8E9690', '#B4B8AE', '#D3D3C6', '#ECEADF']
CHALK_RED = '#D8796A'
WOOD = ['#2A1A10', '#3B2618', '#5A3A22', '#7A5232', '#96693F']
RUST = ['#3E1D16', '#5B2A1E', '#743626', '#8C4430', '#A65A3E', '#BD7350']
ENAMEL = ['#0B1730', '#12224A', '#1A2F5E', '#253F75', '#33528E']
IRON = ['#14161B', '#2A2D33', '#464A51', '#6C7077', '#9196A0']
GRAPHITE, GRAPHITE_L = '#36342F', '#5E5B53'


def C(h, a=255) -> np.ndarray:
    return pg.hx(h, a)


# ============================================================================ canvas with alpha blending
class Canvas:
    def __init__(self, w: int, h: int):
        self.w, self.h = int(w), int(h)
        self.c = np.zeros((self.h, self.w, 4), np.uint8)

    def blend(self, mask, x0: int, y0: int, col, a=1.0):
        """mask: bool/float array (coverage) at (x0, y0); col: RGBA or per-pixel RGBA array of mask's shape."""
        mask = np.asarray(mask)
        mh, mw = mask.shape
        X0, Y0 = max(0, x0), max(0, y0)
        X1, Y1 = min(self.w, x0 + mw), min(self.h, y0 + mh)
        if X1 <= X0 or Y1 <= Y0:
            return
        m = mask[Y0 - y0:Y1 - y0, X0 - x0:X1 - x0].astype(np.float32)
        if not m.any():
            return
        dst = self.c[Y0:Y1, X0:X1].astype(np.float32)
        col = np.asarray(col, np.float32)
        src = col if col.ndim == 1 else col[Y0 - y0:Y1 - y0, X0 - x0:X1 - x0]
        src = np.broadcast_to(src, dst.shape)
        sa = src[..., 3:4] / 255.0 * m[..., None] * float(a)
        da = dst[..., 3:4] / 255.0
        oa = sa + da * (1.0 - sa)
        rgb = (src[..., :3] * sa + dst[..., :3] * da * (1.0 - sa)) / np.maximum(oa, 1e-6)
        rgb = np.where(oa > 0, rgb, dst[..., :3])
        self.c[Y0:Y1, X0:X1] = np.clip(np.round(np.concatenate([rgb, oa * 255.0], -1)), 0, 255).astype(np.uint8)

    def rect(self, x, y, w, h, col, a=1.0):
        if w > 0 and h > 0:
            self.blend(np.ones((int(h), int(w)), bool), int(x), int(y), col, a)

    def px(self, x, y, col, a=1.0):
        self.rect(int(x), int(y), 1, 1, col, a)

    def line(self, x0, y0, x1, y1, col, a=1.0, t=1):
        for (x, y) in bresenham(x0, y0, x1, y1):
            self.rect(x - (t - 1) // 2, y - (t - 1) // 2, t, t, col, a)

    def blit(self, o: 'Canvas', x: int, y: int, a=1.0):
        self.blend(np.ones((o.h, o.w), bool), x, y, o.c, a)

    def save(self, path: str):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        Image.fromarray(self.c, 'RGBA').save(path)

    def image(self) -> Image.Image:
        return Image.fromarray(self.c, 'RGBA')


def bresenham(x0, y0, x1, y1):
    x0, y0, x1, y1 = int(round(x0)), int(round(y0)), int(round(x1)), int(round(y1))
    dx, dy = abs(x1 - x0), -abs(y1 - y0)
    sx, sy = (1 if x0 < x1 else -1), (1 if y0 < y1 else -1)
    err = dx + dy
    out = []
    while True:
        out.append((x0, y0))
        if x0 == x1 and y0 == y1:
            return out
        e2 = 2 * err
        if e2 >= dy:
            err += dy
            x0 += sx
        if e2 <= dx:
            err += dx
            y0 += sy


def dither(w: int, h: int, tone: np.ndarray, ramp, x0=0, y0=0) -> np.ndarray:
    """Per-pixel RGBA array: tone (float, index into ramp) ordered-dithered between neighbouring ramp steps."""
    cols = np.stack([C(c) for c in ramp]).astype(np.float32)
    n = len(ramp)
    t = np.clip(tone, 0, n - 1)
    fl = np.floor(t)
    idx = np.clip(fl + ((t - fl) > pg.bayer(w, h, x0, y0)), 0, n - 1).astype(np.int32)
    return cols[idx]


def noise(w, h, cell, seed, octaves=3):
    return pg.value_noise(w, h, cell, seed, octaves=octaves)


# ============================================================================ pixel types (own designs)
# Plate type: 7 x 11, two-pixel strokes (the wagon numbers).  The centre column 3 is where a stencil bridge
# cuts every bar of five or more pixels.
BIG = {
    '0': ['.#####.', '##...##', '##...##', '##...##', '##...##', '##...##', '##...##', '##...##', '##...##',
          '##...##', '.#####.'],
    '1': ['...##..', '..###..', '.####..', '...##..', '...##..', '...##..', '...##..', '...##..', '...##..',
          '...##..', '...##..'],
    '2': ['.#####.', '##...##', '.....##', '.....##', '....##.', '...##..', '..##...', '.##....', '##.....',
          '##.....', '#######'],
    '3': ['.#####.', '##...##', '.....##', '.....##', '..####.', '.....##', '.....##', '.....##', '.....##',
          '##...##', '.#####.'],
    '4': ['##...##', '##...##', '##...##', '##...##', '##...##', '#######', '.....##', '.....##', '.....##',
          '.....##', '.....##'],
    '5': ['#######', '##.....', '##.....', '######.', '.....##', '.....##', '.....##', '.....##', '.....##',
          '##...##', '.#####.'],
    '7': ['#######', '.....##', '.....##', '....##.', '....##.', '...##..', '...##..', '..##...', '..##...',
          '..##...', '..##...'],
    '8': ['.#####.', '##...##', '##...##', '##...##', '.#####.', '##...##', '##...##', '##...##', '##...##',
          '##...##', '.#####.'],
    'C': ['.#####.', '##...##', '##.....', '##.....', '##.....', '##.....', '##.....', '##.....', '##.....',
          '##...##', '.#####.'],
    '-': ['.....', '.....', '.....', '.....', '#####', '#####', '.....', '.....', '.....', '.....', '.....'],
    '/': ['.....##', '.....##', '....##.', '....##.', '...##..', '...##..', '..##...', '..##...', '.##....',
          '.##....', '##.....'],
}
BIG_SPACE, BIG_GAP = 4, 2
# Mini type 3 x 5 (wagon number window, Marta's pencil): digits, C - / . and the letters of OKT DEZ JAN.
MINI = {
    '0': ['###', '#.#', '#.#', '#.#', '###'], '1': ['.#.', '##.', '.#.', '.#.', '###'],
    '2': ['###', '..#', '###', '#..', '###'], '3': ['###', '..#', '.##', '..#', '###'],
    '4': ['#.#', '#.#', '###', '..#', '..#'], '5': ['###', '#..', '###', '..#', '###'],
    '7': ['###', '..#', '.#.', '.#.', '.#.'], '8': ['###', '#.#', '###', '#.#', '###'],
    'C': ['.##', '#..', '#..', '#..', '.##'], '-': ['...', '...', '###', '...', '...'],
    '/': ['..#', '..#', '.#.', '#..', '#..'], '.': ['.', '.', '.', '.', '#'],
    'O': ['.#.', '#.#', '#.#', '#.#', '.#.'], 'K': ['#.#', '#.#', '##.', '#.#', '#.#'],
    'T': ['###', '.#.', '.#.', '.#.', '.#.'], 'D': ['##.', '#.#', '#.#', '#.#', '##.'],
    'E': ['###', '#..', '##.', '#..', '###'], 'Z': ['###', '..#', '.#.', '#..', '###'],
    'J': ['..#', '..#', '..#', '#.#', '.#.'], 'A': ['.#.', '#.#', '###', '#.#', '#.#'],
    'N': ['#..#', '##.#', '#.##', '#..#', '#..#'],
}
MINI_SPACE, MINI_GAP = 2, 1


def glyph(font: dict, ch: str) -> np.ndarray:
    return np.array([[c == '#' for c in row] for row in font[ch]], bool)


def text_mask(s: str, font: dict, space: int, gap: int, style: str = 'plain', seed: int = 0) -> np.ndarray:
    """One bool mask for the whole string (style: plain | stencil | brush)."""
    parts = []
    for ch in s:
        if ch == ' ':
            parts.append(np.zeros((len(font['0']), space), bool))
            continue
        g = glyph(font, ch).copy()
        if style == 'stencil':
            for r in range(g.shape[0]):
                if g.shape[1] == 7 and g[r, 3]:
                    lo = hi = 3
                    while lo > 0 and g[r, lo - 1]:
                        lo -= 1
                    while hi < 6 and g[r, hi + 1]:
                        hi += 1
                    if hi - lo + 1 >= 5:
                        g[r, 3] = False
        parts.append(g)
    h = parts[0].shape[0]
    w = sum(p.shape[1] for p in parts) + gap * (len(parts) - 1)
    m = np.zeros((h, w), bool)
    x = 0
    for p in parts:
        m[:, x:x + p.shape[1]] = p
        x += p.shape[1] + gap
    if style == 'brush':          # hand-brushed: slight slant, fattened stroke ends, uneven edges
        rng = np.random.default_rng(seed)
        out = np.zeros((h + 2, w + 3), bool)
        for r in range(h):
            sh = (h - 1 - r) // 5
            out[r + 1, 1 + sh:1 + sh + w] |= m[r]
        ys, xs = np.nonzero(out)
        for y, x in zip(ys, xs):
            if rng.random() < 0.12 and 0 < y < out.shape[0] - 1:
                out[y + (1 if rng.random() < 0.6 else -1), x] = True
        for y, x in zip(*np.nonzero(out)):
            if rng.random() < 0.06:
                out[y, x] = False
        return out
    return m


# ============================================================================ number chain (pz_c4_numbers)
SOLUTION_NUMBERS = ['n24318', 'c1742', 'n47702', 'c1745']          # C4_DESIGN §2.7 (self-check below)
PLATES = {
    'n24318': {'face': '24 318', 'style': 'enamel', 'under': '', 'kind': 'enamel'},
    'c1742': {'face': 'C-17/42', 'style': 'stencil_old', 'under': 'n24318', 'kind': 'stencil'},
    'n47702': {'face': '47 702', 'style': 'brush', 'under': 'c1742', 'kind': 'brush'},
    'c1745': {'face': 'C-17/45', 'style': 'stencil_wet', 'under': 'n47702', 'kind': 'stencil_wet'},
}
PLATE_W, PLATE_H = 88, 25
BOARD_W, BOARD_H = 592, 112
POST_X = [125, 235, 345, 455]
PLATE_Y = 12
TRACK_Y = 88                     # chalk line the wagon wheels stand on
SIDING_Y = 100
YARD_X, SIDING_X = 34, 548       # wagon centre x at the yard / in the siding
WAGON_W, WAGON_H = 66, 28
NUM_W, NUM_H = 31, 7             # wagon number window
NUM_AT = [5, 8]                  # window position on the wagon
TICK_W, TICK_H = 13, 11
HALT_S = 19
GLOW_W, GLOW_H = PLATE_W + 14, PLATE_H + 12
WIRE_H = 9


def _plate_face_mask(sym: str) -> np.ndarray:
    p = PLATES[sym]
    st = 'stencil' if p['style'].startswith('stencil') else ('brush' if p['style'] == 'brush' else 'plain')
    return text_mask(p['face'], BIG, BIG_SPACE, BIG_GAP, st, seed=sum(map(ord, sym)))


def plate(sym: str, lit: bool) -> Canvas:
    p = PLATES[sym]
    w, h = PLATE_W, PLATE_H
    cv = Canvas(w, h)
    seed = sum(map(ord, sym)) * 13
    rng = np.random.default_rng(seed)
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    n = noise(w, h, 9, seed)
    style = p['style']
    if style == 'enamel':
        tone = 2.3 - yy / h * 0.9 + (n - 0.5) * 0.5
        base = dither(w, h, tone, ENAMEL)
    else:
        lift = {'stencil_old': -0.35, 'brush': 0.1, 'stencil_wet': 0.75}[style]
        tone = 2.0 + lift - yy / h * 0.6 + (n - 0.5) * (1.2 if style == 'stencil_old' else 0.7)
        base = dither(w, h, tone, RUST)
    body = np.ones((h, w), bool)
    for (cx, cy) in ((0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1)):
        body[cy, cx] = False
    cv.blend(body, 0, 0, base)
    if lit:      # held against the lamp: warm light through the paint (enamel stays almost opaque)
        glow = np.exp(-(((xx - w / 2) / (w * 0.55)) ** 2 + ((yy - h / 2) / (h * 0.75)) ** 2))
        k = 0.30 if style == 'enamel' else 0.62
        cv.blend(body * (0.25 + 0.75 * glow), 0, 0, C(AMBER_L), k)
    # edge: dark outline, light top-left bevel
    edge = np.zeros((h, w), bool)
    edge[0, 1:w - 1] = edge[h - 1, 1:w - 1] = True
    edge[1:h - 1, 0] = edge[1:h - 1, w - 1] = True
    cv.blend(edge, 0, 0, C(IRON[0]))
    cv.rect(1, 1, w - 2, 1, C(AMBER_L if lit else '#FFFFFF'), 0.22)
    cv.rect(1, h - 2, w - 2, 1, C(NIGHT), 0.35)
    if style == 'enamel':
        cv.rect(2, 2, w - 4, 1, C(PAPER[5]), 0.9)
        cv.rect(2, h - 3, w - 4, 1, C(PAPER[5]), 0.9)
        cv.rect(2, 2, 1, h - 4, C(PAPER[5]), 0.9)
        cv.rect(w - 3, 2, 1, h - 4, C(PAPER[5]), 0.9)
        for sx in (5, w - 7):                                     # screws
            cv.rect(sx, h // 2 - 1, 2, 2, C(IRON[1]))
            cv.px(sx, h // 2 - 1, C(IRON[4]))
        for (cx, cy, cw, ch_) in ((1, h - 4, 3, 2), (w - 4, 1, 3, 2), (40, h - 2, 4, 1)):   # enamel chips
            cv.rect(cx, cy, cw, ch_, C(RUST[1]))
    else:   # weathering streaks / gloss
        for _ in range(7 if style == 'stencil_old' else 3):
            x = int(rng.integers(3, w - 3))
            y0 = int(rng.integers(2, h - 8))
            cv.rect(x, y0, 1, int(rng.integers(3, 7)), C(RUST[0] if style != 'stencil_wet' else RUST[5]), 0.35)
        if style == 'stencil_wet':
            for _ in range(14):
                cv.px(int(rng.integers(2, w - 2)), int(rng.integers(2, h - 2)), C('#FFFFFF'), 0.35)
    face = _plate_face_mask(sym)
    fh, fw = face.shape
    fx, fy = (w - fw) // 2, (h - fh) // 2
    ink = {'enamel': PAPER[5], 'stencil_old': PAPER[3], 'brush': '#E3CF95', 'stencil_wet': PAPER[5]}[style]
    if lit:
        under = p['under']
        if under:          # the older number under the paint: dark, in its own type
            um = _plate_face_mask(under)
            uh, uw = um.shape
            cv.blend(um, (w - uw) // 2, (h - uh) // 2, C('#2A140E'), 0.88)
        else:              # bare metal: brushed streaks, nothing underneath
            for r in range(4, h - 4, 3):
                cv.rect(4, r, w - 8, 1, C(IRON[3]), 0.22)
        cv.blend(face, fx, fy, C(ink), 0.22)                     # the face is only a ghost now
    else:
        worn = face.copy()
        if style == 'stencil_old':
            worn &= rng.random(face.shape) > 0.1
        cv.blend(np.roll(face, 1, axis=0) & ~face, fx, fy, C(NIGHT), 0.35)  # paint shadow
        cv.blend(worn, fx, fy, C(ink))
        if style == 'stencil_wet':
            gloss = face & ~np.roll(face, 1, axis=0) & ~np.roll(face, 1, axis=1)
            cv.blend(gloss, fx, fy, C('#FFFFFF'), 0.8)
            cols = [c for c in range(fw) if face[fh - 1, c]]
            for c in cols[::5]:                                   # drips under the wet paint
                cv.rect(fx + c, fy + fh, 1, 2 + (c % 3), C(PAPER[5]), 0.85)
    return cv


def mini_number(sym: str) -> Canvas:
    cv = Canvas(NUM_W, NUM_H)
    m = text_mask(PLATES[sym]['face'], MINI, MINI_SPACE, MINI_GAP)
    mh, mw = m.shape
    x0 = (NUM_W - mw) // 2
    cv.blend(m, x0, 1, C(PAPER[5]))
    return cv


def wagon() -> Canvas:
    """Painted wooden token of the goods wagon (side view, rust-brown, plank body, sliding door, number
    window at NUM_AT -- the UI lays the mini number on it)."""
    w, h = WAGON_W, WAGON_H
    cv = Canvas(w, h)
    rng = np.random.default_rng(4501)
    bx, by, bw, bh = 3, 3, w - 6, 18
    yy, xx = np.mgrid[0:bh, 0:bw].astype(np.float32)
    tone = 2.6 - yy / bh * 0.8 + (noise(bw, bh, 6, 77) - 0.5) * 0.6
    cv.blend(np.ones((bh, bw), bool), bx, by, dither(bw, bh, tone, RUST))
    for x in range(bx + 4, bx + bw - 1, 5):                        # planks
        cv.rect(x, by + 1, 1, bh - 2, C(RUST[1]), 0.7)
    cv.rect(bx - 1, by - 2, bw + 2, 2, C(WALL[2]))                 # roof
    cv.rect(bx, by - 2, bw, 1, C(WALL[4]))
    cv.rect(bx, by, bw, 1, C(RUST[5]), 0.6)
    dx = 41
    cv.rect(dx, by + 1, 15, bh - 2, C(RUST[2]))                    # sliding door
    cv.rect(dx, by + 1, 15, 1, C(RUST[0]))
    cv.rect(dx, by + bh - 2, 15, 1, C(RUST[0]))
    cv.rect(dx, by + 1, 1, bh - 2, C(RUST[0]))
    cv.rect(dx + 14, by + 1, 1, bh - 2, C(RUST[0]))
    cv.line(dx + 1, by + 2, dx + 13, by + bh - 3, C(RUST[1]), 0.8)
    cv.line(dx + 13, by + 2, dx + 1, by + bh - 3, C(RUST[1]), 0.8)
    nx, ny = NUM_AT
    cv.rect(nx - 1, ny - 1, NUM_W + 2, NUM_H + 2, C(RUST[0]))       # number window (painted dark)
    cv.rect(nx, ny, NUM_W, NUM_H, C('#2A140E'))
    cv.rect(bx, by + bh, bw, 2, C(IRON[1]))                        # underframe
    for (ux, uy) in ((0, by + 11), (w - 3, by + 11)):              # buffers
        cv.rect(ux, uy, 3, 3, C(IRON[2]))
        cv.px(ux + (0 if ux == 0 else 2), uy + 1, C(IRON[4]))
    for wx in (15, w - 16):                                        # wheels
        yy2, xx2 = np.mgrid[0:9, 0:9].astype(np.float32)
        r = np.hypot(xx2 - 4, yy2 - 4)
        cv.blend(r <= 4.4, wx - 4, h - 9, C(IRON[1]))
        cv.blend((r <= 4.4) & (r >= 3.2), wx - 4, h - 9, C(IRON[3]))
        cv.rect(wx - 1, h - 6, 2, 2, C(IRON[4]))
    for _ in range(10):                                            # wear
        cv.px(int(rng.integers(bx + 1, bx + bw - 1)), int(rng.integers(by + 1, by + bh - 1)), C(RUST[5]), 0.4)
    return cv


def chalk_path(cv: Canvas, pts, seed: int, t: int = 2, a: float = 0.9, dash=None, col=None):
    """Chalk stroke along a polyline: dusty, slightly broken; dash = (on, off) in pixels."""
    rng = np.random.default_rng(seed)
    col = col or CHALK
    run = 0
    for (x0, y0), (x1, y1) in zip(pts[:-1], pts[1:]):
        for (x, y) in bresenham(x0, y0, x1, y1):
            run += 1
            if dash and (run % (dash[0] + dash[1])) >= dash[0]:
                continue
            for oy in range(t):
                k = rng.random()
                if k < 0.07:
                    continue
                c = col[3] if k > 0.55 else col[2]
                cv.px(x, y + oy - (t - 1) // 2, C(c), a * (0.75 + 0.25 * rng.random()))
            if rng.random() < 0.18:
                cv.px(x + int(rng.integers(-1, 2)), y + int(rng.integers(-2, 3)), C(col[1]), 0.35)


def board() -> Canvas:
    w, h = BOARD_W, BOARD_H
    cv = Canvas(w, h)
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    # wooden frame
    cv.rect(0, 0, w, h, C(WOOD[1]))
    cv.rect(1, 1, w - 2, h - 2, C(WOOD[3]))
    cv.rect(2, 2, w - 4, h - 4, C(WOOD[2]))
    cv.rect(1, 1, w - 2, 1, C(WOOD[4]))
    # slate
    sw, sh = w - 8, h - 8
    n = noise(sw, sh, 22, 9100)
    tone = 1.05 + (n - 0.5) * 0.55
    cv.blend(np.ones((sh, sw), bool), 4, 4, dither(sw, sh, tone, WALL))
    cv.rect(4, 4, sw, 1, C(NIGHT), 0.5)
    smudge = np.clip((noise(sw, sh, 40, 9101, octaves=2) - 0.55) * 2.2, 0, 1)
    cv.blend(smudge, 4, 4, C(CHALK[1]), 0.10)                     # old wiped chalk
    # the tunnel (dashed walls, two portals): „Dienststollen 3“
    for yv in (46, 106):
        chalk_path(cv, [(70, yv), (512, yv)], 11 + yv, 1, 0.42, dash=(4, 3))
    for xv in (70, 512):
        chalk_path(cv, [(xv, 46), (xv, 106)], 13 + xv, 1, 0.42, dash=(3, 3))
    # yard fan, main line, siding with buffer stop
    chalk_path(cv, [(8, 72), (40, 72), (58, TRACK_Y)], 21)
    chalk_path(cv, [(8, TRACK_Y), (58, TRACK_Y)], 22)
    chalk_path(cv, [(8, 104), (40, 104), (58, TRACK_Y)], 23)
    chalk_path(cv, [(58, TRACK_Y), (584, TRACK_Y)], 24)
    chalk_path(cv, [(498, TRACK_Y), (522, SIDING_Y), (574, SIDING_Y)], 25)
    chalk_path(cv, [(577, SIDING_Y - 7), (577, SIDING_Y + 3)], 26)
    chalk_path(cv, [(574, SIDING_Y - 5), (580, SIDING_Y - 5)], 27)
    for i, px_ in enumerate(POST_X):
        chalk_path(cv, [(px_ - 15, TRACK_Y), (px_ + 3, TRACK_Y - 9)], 40 + i)        # the switch's branch
        chalk_path(cv, [(px_, TRACK_Y + 3), (px_, TRACK_Y + 8)], 50 + i, 1, 0.8)    # stop mark
        # iron hook + nail
        cv.rect(px_ - 1, 2, 3, 3, C(IRON[1]))
        cv.px(px_ - 1, 2, C(IRON[4]))
        cv.rect(px_, 5, 1, 4, C(IRON[2]))
        cv.px(px_ + 1, 8, C(IRON[2]))
        cv.px(px_ + 1, 9, C(IRON[3]))
        # where a plate hangs: faint dashed outline
        x0, y0 = px_ - PLATE_W // 2, PLATE_Y
        chalk_path(cv, [(x0, y0), (x0 + PLATE_W - 1, y0), (x0 + PLATE_W - 1, y0 + PLATE_H - 1),
                        (x0, y0 + PLATE_H - 1), (x0, y0)], 60 + i, 1, 0.30, dash=(2, 3))
    return cv


def wire() -> Canvas:
    cv = Canvas(PLATE_W, WIRE_H)
    cx = PLATE_W // 2
    cv.line(cx, 0, 6, WIRE_H - 1, C(IRON[3]))
    cv.line(cx, 0, PLATE_W - 7, WIRE_H - 1, C(IRON[3]))
    return cv


def tick() -> Canvas:
    cv = Canvas(TICK_W, TICK_H)
    chalk_path(cv, [(1, 5), (4, 8), (11, 1)], 71, 2, 1.0)
    return cv


def halt() -> Canvas:
    """Red chalk ring with a cross: where the trial run stopped (shape-coded, not only colour)."""
    s = HALT_S
    cv = Canvas(s, s)
    yy, xx = np.mgrid[0:s, 0:s].astype(np.float32)
    r = np.hypot(xx - (s - 1) / 2, yy - (s - 1) / 2)
    cv.blend((r <= 8.9) & (r >= 7.2), 0, 0, C(NIGHT), 0.55)
    cv.blend((r <= 8.3) & (r >= 6.9), 0, 0, C(CHALK_RED))
    for (a, b) in (((5, 5), (13, 13)), ((13, 5), (5, 13))):
        cv.line(a[0], a[1], b[0], b[1], C(CHALK_RED), 1.0, 2)
    return cv


def glow() -> Canvas:
    cv = Canvas(GLOW_W, GLOW_H)
    yy, xx = np.mgrid[0:GLOW_H, 0:GLOW_W].astype(np.float32)
    d = np.sqrt(((xx - GLOW_W / 2) / (GLOW_W / 2)) ** 2 + ((yy - GLOW_H / 2) / (GLOW_H / 2)) ** 2)
    a = np.clip(1.0 - d, 0, 1) ** 1.2
    q = np.floor(a * 6) / 6 * 0.75                                   # banded (pixel-art light falloff)
    cv.blend(q, 0, 0, C(AMBER))
    return cv


def lamp(on: bool) -> Canvas:
    """Hand lamp with a wire cage (Kontrolllampe), 14 x 20."""
    w, h = 14, 20
    cv = Canvas(w, h)
    if on:
        yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
        d = np.hypot((xx - 6.5) / 7, (yy - 11) / 9)
        cv.blend(np.clip(1 - d, 0, 1) * 0.55, 0, 0, C(AMBER))
    cv.rect(5, 0, 4, 1, C(IRON[2]))                                   # hook
    cv.rect(4, 1, 1, 2, C(IRON[2]))
    cv.rect(9, 1, 1, 2, C(IRON[2]))
    cv.rect(3, 3, 8, 2, C(IRON[1]))                                   # collar
    yy, xx = np.mgrid[0:11, 0:8].astype(np.float32)
    bulb = np.hypot((xx - 3.5) / 4, (yy - 5) / 5.5) <= 1.0
    cv.blend(bulb, 3, 5, C(AMBER_L if on else WALL[1]))
    if on:
        cv.blend(np.hypot((xx - 3.5) / 2, (yy - 5) / 3) <= 1.0, 3, 5, C('#FFFFFF'), 0.9)
    for x in (3, 6, 10):                                              # cage
        cv.rect(x, 5, 1, 11, C(IRON[3] if on else IRON[2]))
    cv.rect(3, 10, 8, 1, C(IRON[3] if on else IRON[2]))
    cv.rect(4, 16, 6, 2, C(IRON[1]))
    cv.rect(5, 18, 4, 2, C(IRON[2]))
    return cv


def numbers_assets():
    out = {}
    out['board'] = board()
    for sym in PLATES:
        out['plate_' + sym] = plate(sym, False)
        out['plate_%s_lit' % sym] = plate(sym, True)
        out['num_' + sym] = mini_number(sym)
    out['wagon'] = wagon()
    out['wire'] = wire()
    out['tick'] = tick()
    out['halt'] = halt()
    out['glow'] = glow()
    out['lamp_on'] = lamp(True)
    out['lamp_off'] = lamp(False)
    return out


def surface(cv: Canvas, rect) -> str:
    x, y, w, h = rect
    reg = cv.c[y:y + h, x:x + w].reshape(-1, 4)
    reg = reg[reg[:, 3] > 0][:, :3]
    m = np.median(reg, axis=0).astype(int)
    return '#%02X%02X%02X' % tuple(m)


def check_numbers():
    pz = json.load(open(os.path.join(ROOT, 'data', 'v3', 'puzzles.json'), encoding='utf-8'))
    p = next(x for x in pz['puzzles'] if x['id'] == 'pz_c4_numbers')
    assert p['solution'] == SOLUTION_NUMBERS, p['solution']
    assert sorted(p['display_symbols']) == sorted(PLATES), p['display_symbols']
    chain = [s for s in SOLUTION_NUMBERS]
    assert PLATES[chain[0]]['under'] == '', 'the first plate lies on bare metal'
    for a, b in zip(chain[:-1], chain[1:]):
        assert PLATES[b]['under'] == a, (a, b)
    return p['display_symbols']


# ============================================================================ route overlay (pz_c4_routes)
CELL = 16
PLAN_CELLS = (14, 10)
TRACE_CELLS = (10, 8)
B_ORIGIN = (-1, 3)                 # trace top-left (cells) relative to the plan at offset (0, 0), unrotated
START = {'rotation_steps': 0, 'offset_x': 0, 'offset_y': 0}
BOARD_CELLS = (18, 14)
PLAN_AT = (2, 2)
V_STREETS = [4, 7, 10]             # plan columns that are streets (7 = the line-74 street)
H_STREETS = [0, 3, 6, 9]
RINGS = [{'id': 's1', 'cell': (9, 1)}, {'id': 's2', 'cell': (5, 5)}, {'id': 's3', 'cell': (8, 8)}]
LOOPS = [   # Marta's detours on the tracing paper (trace cells, continuous), diamond cell, date label position
    {'id': 'okt', 'label': 'OKT.', 'path': [(0.5, 3.5), (0.5, 0.5), (3.5, 0.5), (3.5, 3.5)], 'diamond': (1, 1),
     'text_at': (17, 33), 'pairs_with': 's1'},
    {'id': 'dez', 'label': 'DEZ.', 'path': [(3.5, 3.5), (3.5, 6.5), (6.5, 6.5), (6.5, 3.5)], 'diamond': (5, 5),
     'text_at': (65, 74), 'pairs_with': 's2'},
    {'id': 'jan', 'label': 'JAN.', 'path': [(6.5, 3.5), (6.5, 0.5), (9.5, 0.5), (9.5, 3.5)], 'diamond': (8, 2),
     'text_at': (113, 17), 'pairs_with': 's3'},
]
LINE_ROW = 3.5                     # the autumn route (trace cells, continuous y)
TITLE_BLOCK = [2, 114, 60, 44]     # plan px: lower-left block, outside the trace's footprint when aligned
TITLE_LINES = [[5, 117, 54, 12], [5, 130, 54, 12], [5, 143, 54, 12]]
NORTH = [198, 3, 22, 28]


def rot_point(p, steps: int, w: float, h: float):
    """Trace point (cells, continuous, unrotated local) -> offset from the trace's top-left after `steps`
    clockwise quarter turns around its centre (screen coordinates, y down) -- same maths as the UI."""
    cx, cy = w / 2.0, h / 2.0
    dx, dy = p[0] - cx, p[1] - cy
    for _ in range(steps % 4):
        dx, dy = -dy, dx
    return (cx + dx, cy + dy)


def pose_maps(steps: int, ox: int, oy: int, pt):
    """Trace point -> plan cells for a pose (rotation_steps, offset)."""
    q = rot_point(pt, steps, *TRACE_CELLS)
    return (B_ORIGIN[0] + ox + q[0], B_ORIGIN[1] + oy + q[1])


def aligned(steps: int, ox: int, oy: int) -> int:
    n = 0
    for lp in LOOPS:
        ring = next(r for r in RINGS if r['id'] == lp['pairs_with'])
        p = pose_maps(steps, ox, oy, (lp['diamond'][0] + 0.5, lp['diamond'][1] + 0.5))
        if abs(p[0] - (ring['cell'][0] + 0.5)) < 1e-6 and abs(p[1] - (ring['cell'][1] + 0.5)) < 1e-6:
            n += 1
    return n


def check_routes():
    pz = json.load(open(os.path.join(ROOT, 'data', 'v3', 'puzzles.json'), encoding='utf-8'))
    sol = next(x for x in pz['puzzles'] if x['id'] == 'pz_c4_routes')['solution']
    full = [(r, x, y) for r in range(4) for x in range(-12, 13) for y in range(-12, 13) if aligned(r, x, y) == 3]
    assert full == [(sol['rotation_steps'], sol['offset_x'], sol['offset_y'])], full
    assert aligned(START['rotation_steps'], START['offset_x'], START['offset_y']) == 0
    # the aligned line runs along the plan's street 7 and every detour along streets
    for t in [(u + 0.5, LINE_ROW) for u in range(TRACE_CELLS[0])]:
        p = pose_maps(sol['rotation_steps'], sol['offset_x'], sol['offset_y'], t)
        assert abs(p[0] - 7.5) < 1e-6, p
    for lp in LOOPS:
        for t in lp['path']:
            p = pose_maps(sol['rotation_steps'], sol['offset_x'], sol['offset_y'], t)
            assert (p[0] - 0.5) in V_STREETS or (p[1] - 0.5) in H_STREETS, (lp['id'], p)
    return sol


def plan() -> Canvas:
    """Site plan Süd 8 (Lageplan), north up: streets, hatched blocks with house outlines, tram tracks on street
    7, three ventilation shafts as rings, north arrow, an empty title block (the UI sets the HD lines)."""
    w, h = PLAN_CELLS[0] * CELL, PLAN_CELLS[1] * CELL
    cv = Canvas(w, h)
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    tone = 4.15 + (noise(w, h, 30, 8800) - 0.5) * 0.3
    e = np.minimum(np.minimum(xx, w - 1 - xx), np.minimum(yy, h - 1 - yy))
    tone -= np.clip((4 - e) / 4, 0, 1) * 0.7
    cv.blend(np.ones((h, w), bool), 0, 0, dither(w, h, tone, PAPER))
    street = np.zeros((h, w), bool)
    for c in V_STREETS:
        street[:, c * CELL:(c + 1) * CELL] = True
    for r in H_STREETS:
        street[r * CELL:(r + 1) * CELL, :] = True
    cv.blend(street, 0, 0, C(PAPER[5]), 0.85)
    # blocks: diagonal hatch + house outlines with courtyards
    hatch = (~street) & (((xx + yy).astype(int) % 5) == 0)
    cv.blend(hatch, 0, 0, C(PAPER[2]), 0.9)
    cols = [-1] + V_STREETS + [PLAN_CELLS[0]]
    rows = [-1] + H_STREETS + [PLAN_CELLS[1]]
    for ci in range(len(cols) - 1):
        for ri in range(len(rows) - 1):
            x0, x1 = (cols[ci] + 1) * CELL, cols[ci + 1] * CELL
            y0, y1 = (rows[ri] + 1) * CELL, rows[ri + 1] * CELL
            if x1 - x0 < 8 or y1 - y0 < 8:
                continue
            bx0, by0, bx1, by1 = x0 + 2, y0 + 2, x1 - 3, y1 - 3
            for (a, b) in (((bx0, by0), (bx1, by0)), ((bx1, by0), (bx1, by1)), ((bx1, by1), (bx0, by1)),
                           ((bx0, by1), (bx0, by0))):
                cv.line(a[0], a[1], b[0], b[1], C(INK_B), 0.9)
            if bx1 - bx0 > 14 and by1 - by0 > 12:                  # courtyard
                ix0, iy0, ix1, iy1 = bx0 + 6, by0 + 5, bx1 - 6, by1 - 5
                cv.rect(ix0, iy0, ix1 - ix0 + 1, iy1 - iy0 + 1, C(PAPER[4]))
                for (a, b) in (((ix0, iy0), (ix1, iy0)), ((ix1, iy0), (ix1, iy1)), ((ix1, iy1), (ix0, iy1)),
                               ((ix0, iy1), (ix0, iy0))):
                    cv.line(a[0], a[1], b[0], b[1], C(INK_B), 0.55)
    # street edges
    for c in V_STREETS:
        cv.rect(c * CELL, 0, 1, h, C(INK_B), 0.85)
        cv.rect((c + 1) * CELL - 1, 0, 1, h, C(INK_B), 0.85)
    for r in H_STREETS:
        cv.rect(0, r * CELL, w, 1, C(INK_B), 0.85)
        cv.rect(0, (r + 1) * CELL - 1, w, 1, C(INK_B), 0.85)
    # tram tracks on street 7 (dashed pair)
    for x in (7 * CELL + 5, 7 * CELL + 10):
        for y in range(0, h, 4):
            cv.rect(x, y, 1, 2, C(INK_DIM), 0.9)
    # shafts S 1 - S 3: bold ring + four ticks (ventilation symbol)
    for ring in RINGS:
        cx, cy = (ring['cell'][0] + 0.5) * CELL - 0.5, (ring['cell'][1] + 0.5) * CELL - 0.5
        yy2, xx2 = np.mgrid[0:17, 0:17].astype(np.float32)
        r = np.hypot(xx2 - 8, yy2 - 8)
        x0, y0 = int(round(cx - 8)), int(round(cy - 8))
        cv.blend(r <= 6.3, x0, y0, C(PAPER[5]))
        cv.blend((r <= 6.3) & (r >= 4.4), x0, y0, C(INK))
        cv.rect(x0 + 8, y0 + 8, 1, 1, C(INK))
        for (tx, ty, tw, th) in ((8, 0, 1, 2), (8, 15, 1, 2), (0, 8, 2, 1), (15, 8, 2, 1)):
            cv.rect(x0 + tx, y0 + ty, tw, th, C(INK))
    # north arrow
    nx, ny, nw, nh = NORTH
    cv.rect(nx, ny, nw, nh, C(PAPER[5]), 0.9)
    ax = nx + nw // 2
    cv.line(ax, ny + 9, ax, ny + nh - 3, C(INK))
    for k in range(5):
        cv.rect(ax - k, ny + 9 + k, 2 * k + 1, 1, C(INK))
    nm = glyph(MINI, 'N')
    cv.blend(nm, ax - 1, ny + 2, C(INK))
    # title block (lines only -- the words come from Loc: ui.c4.routes.plan.*)
    tx, ty, tw, th = TITLE_BLOCK
    cv.rect(tx, ty, tw, th, C(PAPER[5]))
    for (a, b) in (((tx, ty), (tx + tw - 1, ty)), ((tx + tw - 1, ty), (tx + tw - 1, ty + th - 1)),
                   ((tx + tw - 1, ty + th - 1), (tx, ty + th - 1)), ((tx, ty + th - 1), (tx, ty))):
        cv.line(a[0], a[1], b[0], b[1], C(INK))
    for ln in TITLE_LINES[1:]:
        cv.rect(tx + 1, ln[1] - 1, tw - 2, 1, C(INK_B), 0.6)
    # sheet edge
    cv.rect(0, 0, w, 1, C(PAPER[1]))
    cv.rect(0, h - 1, w, 1, C(PAPER[0]))
    cv.rect(0, 0, 1, h, C(PAPER[1]))
    cv.rect(w - 1, 0, 1, h, C(PAPER[0]))
    return cv


def pencil(cv: Canvas, pts_px, seed: int, dash=None, a=0.92, t=2, col=GRAPHITE):
    rng = np.random.default_rng(seed)
    run = 0
    for (x0, y0), (x1, y1) in zip(pts_px[:-1], pts_px[1:]):
        for (x, y) in bresenham(x0, y0, x1, y1):
            run += 1
            if dash and (run % (dash[0] + dash[1])) >= dash[0]:
                continue
            for o in range(t):
                if rng.random() < 0.06:
                    continue
                if x0 == x1:
                    cv.px(x + o - (t - 1) // 2, y, C(col), a * (0.8 + 0.2 * rng.random()))
                else:
                    cv.px(x, y + o - (t - 1) // 2, C(col), a * (0.8 + 0.2 * rng.random()))


def rounded(path_cells, r=3):
    """Cell path -> pixel polyline with small rounded (chamfered) corners."""
    pts = [(p[0] * CELL, p[1] * CELL) for p in path_cells]
    out = [pts[0]]
    for i in range(1, len(pts) - 1):
        (ax, ay), (bx, by), (cx, cy) = pts[i - 1], pts[i], pts[i + 1]
        ux, uy = np.sign(bx - ax), np.sign(by - ay)
        vx, vy = np.sign(cx - bx), np.sign(cy - by)
        out.append((bx - ux * r, by - uy * r))
        out.append((bx + vx * r, by + vy * r))
    out.append(pts[-1])
    return [(int(round(x)), int(round(y))) for (x, y) in out]


def trace() -> Canvas:
    """Marta's tracing paper from the depot: line 74 as it ran in autumn (solid) and the detours of October,
    December and January (dashed) with a diamond each and the month in her pencil, drawn in driving
    direction (left -> right); arrow head at the end of the line."""
    w, h = TRACE_CELLS[0] * CELL, TRACE_CELLS[1] * CELL
    cv = Canvas(w, h)
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    fib = noise(w, h, 7, 6200)
    alpha = 0.40 + (fib - 0.5) * 0.10
    e = np.minimum(np.minimum(xx, w - 1 - xx), np.minimum(yy, h - 1 - yy))
    alpha += np.clip((2 - e) / 2, 0, 1) * 0.18
    base = np.zeros((h, w, 4), np.float32)
    base[..., :3] = C('#DCE6EA')[:3]
    base[..., 3] = 255
    cv.blend(alpha, 0, 0, base)
    cv.blend(np.clip((3 - e) / 3, 0, 1) * ((xx + yy) > (w + h - 26)), 0, 0, C('#FFFFFF'), 0.25)   # curled corner
    for (tx, ty) in ((4, -2), (w - 22, -2)):                          # masking tape
        cv.rect(tx, ty + 2, 18, 6, C('#D9C9A0'), 0.8)
        cv.rect(tx, ty + 7, 18, 1, C('#B5A47C'), 0.6)
    ly = int(LINE_ROW * CELL)
    pencil(cv, [(2, ly), (w - 10, ly)], 301, None, 0.95, 2)            # the autumn route
    for k in range(5):                                                # arrow head (driving direction)
        cv.rect(w - 10 + k, ly - 4 + k, 1, 9 - 2 * k, C(GRAPHITE), 0.95)
    for i, lp in enumerate(LOOPS):
        pencil(cv, rounded(lp['path']), 310 + i, (5, 2), 0.9, 2)
        dx, dy = (lp['diamond'][0] + 0.5) * CELL - 0.5, (lp['diamond'][1] + 0.5) * CELL - 0.5
        yy2, xx2 = np.mgrid[0:15, 0:15].astype(np.float32)
        d = np.abs(xx2 - 7) + np.abs(yy2 - 7)
        x0, y0 = int(round(dx - 7)), int(round(dy - 7))
        cv.blend(d <= 6.4, x0, y0, C('#F2F5F2'), 0.7)
        cv.blend((d <= 6.4) & (d >= 4.6), x0, y0, C(GRAPHITE))
        m = text_mask(lp['label'], MINI, MINI_SPACE, MINI_GAP)
        cv.blend(m, lp['text_at'][0], lp['text_at'][1], C(GRAPHITE), 0.95)
    m74 = text_mask('74', MINI, MINI_SPACE, MINI_GAP)
    cv.blend(m74, 3, ly + 4, C(GRAPHITE))                          # line number, under the start
    return cv


def snap_mark() -> Canvas:
    """Corner brackets around a ring that has a diamond on it (shape cue, drawn while aligning)."""
    s = 26
    cv = Canvas(s, s)
    for (x, y, dx, dy) in ((0, 0, 1, 1), (s - 1, 0, -1, 1), (0, s - 1, 1, -1), (s - 1, s - 1, -1, -1)):
        for k in range(6):
            cv.rect(x + dx * k - (1 if dx < 0 else 0), y, 2, 2, C(BLUE_INK))
            cv.rect(x, y + dy * k - (1 if dy < 0 else 0), 2, 2, C(BLUE_INK))
    return cv


def match_mark() -> Canvas:
    """Red pencil loop drawn twice around a ring/diamond pair after the solution."""
    s = 40
    cv = Canvas(s, s)
    for k, (rr, ph) in enumerate(((15.5, 0.2), (17.0, 2.1))):
        n = 90
        prev = None
        for i in range(n + 6):
            t = i / n * math.tau + ph
            r = rr + math.sin(t * 3 + k) * 0.8
            x = s / 2 - 0.5 + math.cos(t) * r
            y = s / 2 - 0.5 + math.sin(t) * r * 0.93
            if prev is not None:
                cv.line(prev[0], prev[1], x, y, C(RED), 0.85 if k == 0 else 0.6, 2 if k == 0 else 1)
            prev = (x, y)
    return cv


def underline() -> Canvas:
    w, h = 50, 6
    cv = Canvas(w, h)
    pencil(cv, [(1, 2), (w - 2, 1)], 820, None, 0.95, 2, RED)
    pencil(cv, [(4, 5), (w - 6, 4)], 821, None, 0.75, 1, RED)
    return cv


def routes_assets():
    return {'plan': plan(), 'trace': trace(), 'snap': snap_mark(), 'match': match_mark(), 'underline': underline()}


# ============================================================================ main
def rel(path: str) -> str:
    return 'res://' + os.path.relpath(path, ROOT).replace(os.sep, '/')


def main():
    preview = ''
    for a in sys.argv[1:]:
        if a.startswith('--preview='):
            preview = a.split('=', 1)[1]
    written = []
    display = check_numbers()
    sol = check_routes()
    na = numbers_assets()
    files = {
        'board': 'c4_numbers_board.png', 'wagon': 'c4_wagon.png', 'wire': 'c4_wire.png', 'tick': 'c4_tick.png',
        'halt': 'c4_halt.png', 'glow': 'c4_glow.png', 'lamp_on': 'c4_lamp_on.png', 'lamp_off': 'c4_lamp_off.png',
    }
    for k, f in files.items():
        p = os.path.join(PUZ, f)
        na[k].save(p)
        written.append(p)
    plates = {}
    for sym, d in PLATES.items():
        for k, f in (('plate_' + sym, 'c4_plate_%s.png' % sym), ('plate_%s_lit' % sym, 'c4_plate_%s_lit.png' % sym),
                     ('num_' + sym, 'c4_num_%s.png' % sym)):
            p = os.path.join(PUZ, f)
            na[k].save(p)
            written.append(p)
        plates[sym] = {'face': d['face'], 'kind': d['kind'], 'under': d['under'], 'file': 'c4_plate_%s.png' % sym,
                       'lit_file': 'c4_plate_%s_lit.png' % sym, 'num_file': 'c4_num_%s.png' % sym,
                       'face_key': 'ui.c4.numbers.face.%s' % sym, 'card_key': 'ui.c4.numbers.card.%s' % sym,
                       'under_key': 'ui.c4.numbers.under.%s' % sym}
    meta = {
        'puzzle_id': 'pz_c4_numbers', 'objective': 'c4c_solve_numbers', 'display_scale': 3,
        'coords': 'art pixels ([x, y] / [x, y, w, h]); the UI multiplies by 3', 'generator': GENERATOR, 'date': DATE,
        'board': {'file': files['board'], 'size': [BOARD_W, BOARD_H], 'posts_x': POST_X, 'plate_y': PLATE_Y,
                  'track_y': TRACK_Y, 'siding_y': SIDING_Y, 'yard_x': YARD_X, 'siding_x': SIDING_X,
                  'labels': {'yard': [8, 51], 'siding': [522, 102], 'tunnel': [150, 92]}},
        'plate': {'size': [PLATE_W, PLATE_H]},
        'plates': plates,
        'wagon': {'file': files['wagon'], 'size': [WAGON_W, WAGON_H], 'number_at': NUM_AT, 'number_size': [NUM_W, NUM_H]},
        'wire': {'file': files['wire'], 'size': [PLATE_W, WIRE_H]},
        'tick': {'file': files['tick'], 'size': [TICK_W, TICK_H]},
        'halt': {'file': files['halt'], 'size': [HALT_S, HALT_S]},
        'glow': {'file': files['glow'], 'size': [GLOW_W, GLOW_H]},
        'lamp': {'on': files['lamp_on'], 'off': files['lamp_off'], 'size': [14, 20]},
        'surfaces': {'slate': surface(na['board'], [200, 50, 60, 30]), 'plate_rust': surface(na['plate_c1742'], [3, 3, 8, 18])},
        'chain_check': {'verified_against': 'data/v3/puzzles.json pz_c4_numbers', 'display_symbols': display},
        'world_note': 'Fictional wagon numbers, paint layers and switch posts; not a real railway numbering scheme.',
    }
    p = os.path.join(PUZ, 'c4_numbers_board.json')
    with open(p, 'w', encoding='utf-8') as f:
        json.dump(meta, f, indent=1, ensure_ascii=False)
    written.append(p)

    ra = routes_assets()
    rfiles = {'plan': ('berlin_c4_routes_plan.png', DOCS), 'trace': ('berlin_c4_routes_trace.png', DOCS),
              'snap': ('c4_route_snap.png', PUZ), 'match': ('c4_route_match.png', PUZ),
              'underline': ('c4_route_underline.png', PUZ)}
    for k, (f, d) in rfiles.items():
        p = os.path.join(d, f)
        ra[k].save(p)
        written.append(p)
    rmeta = {
        'puzzle_id': 'pz_c4_routes', 'objective': 'c4b_solve_routes', 'cell_px': CELL, 'display_scale': 3,
        'coords': 'cells from the top-left of each sheet; +x right, +y down; rotation_steps turn the trace '
                  'clockwise around its centre (screen coordinates); offsets move it in whole cells',
        'generator': GENERATOR, 'date': DATE,
        'plan': {'file': rfiles['plan'][0], 'item': 'ev_c4_notice', 'cells': list(PLAN_CELLS),
                 'rings': [{'id': r['id'], 'cell': list(r['cell']), 'label_key': 'ui.c4.routes.shaft.%s' % r['id'][1]}
                           for r in RINGS],
                 'streets': {'columns': V_STREETS, 'rows': H_STREETS, 'line_74_column': 7},
                 'title_block': TITLE_BLOCK, 'title_lines': TITLE_LINES,
                 'title_keys': ['ui.c4.routes.plan.title', 'ui.c4.routes.plan.sub', 'ui.c4.routes.plan.sign'],
                 'north': NORTH},
        'trace': {'file': rfiles['trace'][0], 'item': 'ev_c4_route_board', 'cells': list(TRACE_CELLS),
                  'line_row': LINE_ROW,
                  'loops': [{'id': lp['id'], 'diamond': list(lp['diamond']), 'pairs_with': lp['pairs_with'],
                             'path': [list(q) for q in lp['path']]} for lp in LOOPS]},
        'landmarks': [{'name': '%s_%s' % (lp['pairs_with'], lp['id']),
                       'a': list(next(r['cell'] for r in RINGS if r['id'] == lp['pairs_with'])),
                       'b': list(lp['diamond']), 'match_key': 'ui.c4.routes.match.%s' % lp['pairs_with'][1]}
                      for lp in LOOPS],
        'b_origin': list(B_ORIGIN), 'start': START, 'board_cells': list(BOARD_CELLS), 'plan_at': list(PLAN_AT),
        'marks': {'snap': rfiles['snap'][0], 'match': rfiles['match'][0], 'underline': rfiles['underline'][0]},
        'surfaces': {'paper': surface(ra['plan'], [TITLE_BLOCK[0] + 2, TITLE_BLOCK[1] + 2, 50, 8])},
        'pose_check': {'verified_against': 'data/v3/puzzles.json pz_c4_routes',
                       'unique': 'exactly one pose (rotation, offset) puts every diamond on its ring',
                       'start_aligned': 0},
        'accessibility': 'shafts are rings with four ticks, detours are hollow diamonds (shape, not colour); the '
                         'dates are pencil text that turns with the sheet',
        'world_note': 'Fictional tram route drawn over a fictional site plan of a fictional Berlin district; not a real plan.',
    }
    p = os.path.join(DOCS, 'berlin_c4_routes.json')
    with open(p, 'w', encoding='utf-8') as f:
        json.dump(rmeta, f, indent=1, ensure_ascii=False)
    written.append(p)
    assert sol['rotation_steps'] == 1

    if preview:
        os.makedirs(preview, exist_ok=True)
        S = 2
        sheet = Image.new('RGBA', (1280, 980), tuple(int(v) for v in C(NAVY)))

        def put(cv, x, y, s=S):
            im = cv.image().resize((cv.w * s, cv.h * s), Image.NEAREST)
            sheet.alpha_composite(im, (x, y))
        put(na['board'], 8, 8)
        for i, sym in enumerate(PLATES):
            put(na['plate_' + sym], 8 + i * 190, 250)
            put(na['plate_%s_lit' % sym], 8 + i * 190, 310)
            put(na['num_' + sym], 8 + i * 190, 370, 3)
        put(na['wagon'], 8, 410, 3)
        for i, k in enumerate(('wire', 'tick', 'halt', 'glow', 'lamp_on', 'lamp_off')):
            put(na[k], 230 + i * 110, 410, 3 if na[k].w < 40 else 1)
        put(ra['plan'], 8, 520)
        put(ra['trace'], 470, 520)
        put(ra['snap'], 820, 520, 3)
        put(ra['match'], 920, 520, 3)
        put(ra['underline'], 820, 660, 3)
        sheet.save(os.path.join(preview, 'c4_contact_sheet.png'))
    for p in written:
        print('wrote', os.path.relpath(p, ROOT))


if __name__ == '__main__':
    main()
