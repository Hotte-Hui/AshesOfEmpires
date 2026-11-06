"""gen_ui_board -- original pixel-art kit for the evidence board „Die Akte C-17“ (round 9, owner: board).

Draws every texture at 1:1 (one art pixel = three screen pixels) and writes
  * assets/ui/board/src_1x/<name>.png      1:1 sources (folder has .gdignore, never imported)
  * assets/ui/board/<name>.png             x3 nearest runtime textures (frames are 9-patches)
  * assets/ui/board/thumbs/<item>.png      x3 card pictures, 54x24 at 1:1 (162x72 on screen)
  * assets/ui/board/manifest.json          what was written (size at 1:1, scale, 9-patch margins, source)
Card pictures of items that have an inspect close-up (assets/ui/documents/*) are 1:1 detail crops of that
close-up (the telling spot: the stamp, the number, the margin note) -- the same pixels the InspectView shows,
never resampled. Items without a close-up get an original drawing here. The vertical journal tab „Akte“ is the
round-1 paper tab (assets/ui/frames/ptab_*.png) turned by 90 degrees (exact, no resampling).
Style law: documentation/ART_DIRECTION.md + the UI kit palette (gen_ui.py / gen_ui_explore.py): warm paper and
ink, archive wood, one red ramp for C-17 and the threads. No emblem or insignia of any kind. Shapes are
procedural; nothing is traced or sampled from references. Deterministic: seeds are crc32 of asset names.

Run:  py -3 -P tools/pixelgen/gen_ui_board.py
"""
from __future__ import annotations

import json
import math
import os
import sys
import zlib

import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pg  # noqa: E402  (read-only shared helpers)

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
OUT = os.path.join(ROOT, 'assets', 'ui', 'board')
SRC = os.path.join(OUT, 'src_1x')
DOCS = os.path.join(ROOT, 'assets', 'ui', 'documents')
FRAMES = os.path.join(ROOT, 'assets', 'ui', 'frames')
SCALE = 3
THUMB = (54, 24)
DRAW = (54, 30)          # original drawings are made at 54x30 and cut to the card window (CUT_Y)

hx = pg.hx

# ----------------------------------------------------------------------------- palette (UI kit + pg ramps)
NIGHT, NIGHT1, NAVY, NAVY_L = '#04090D', '#06151D', '#0B1C24', '#14272B'
WALL0, WALL1, WALL2, WALL3, WALL4 = '#1A2A2E', '#24373A', '#354448', '#4A5A5B', '#62716E'
COPPER_D, COPPER, COPPER_L, AMBER, AMBER_L = '#7A3E26', '#BA775B', '#DCA16E', '#F0C487', '#FBE3AE'
PAPER_D2, PAPER_D1, PAPER_D, PAPER_M, PAPER, PAPER_L = '#6E6A5C', '#8E8A78', '#B0AA93', '#CEC6AA', '#E6DEC2', '#F5EFDA'
INK, INK_B, INK_DIM = '#1A1C2A', '#2E3248', '#4D4A42'
RED_D2, RED_D, RED, RED_L = '#4A1A18', '#7A2A26', '#A8382E', '#CF5B4A'
COVER = ['#2A1B16', '#3D2820', '#55372A', '#6E4A37', '#8A6247']          # archive wood ramp
CORK = ['#3C2A1E', '#483224', '#543B2A', '#604430', '#6C4E37', '#7A5940', '#8A674B']
CORK_HC = ['#2A1D14', '#33241A', '#3B2A1E', '#433022', '#4B3626']
STEEL = ['#1D2A3A', '#2B3C50', '#3E546B', '#58718A', '#7A93A8', '#A7BCCB']
BRASS = ['#4A3018', '#7A5228', '#A87A3A', '#D2A75A', '#F0D48E']
LEAD = ['#2E3436', '#4A5254', '#687274', '#8E9896', '#B8C0BC']
WINE = ['#3A1418', '#5A1E26', '#7A2A34', '#9A3A44', '#BA5A5E']
SNOW = ['#7E8E8C', '#A3B1AD', '#C4CFC8', '#DEE5DC', '#F1F4EC']
BLUE_INK = '#2B3C50'
PENCIL = '#6E6A6E'
HOSE = ['#5A5040', '#7E7258', '#A49878', '#C8BE9C']
FIRE_RED = ['#4A1210', '#7A1E18', '#A82A20', '#C8483A']

MANIFEST: list[dict] = []
CLEAR = np.array([0, 0, 0, 0], np.uint8)


def c(h, a=255):
    return hx(h, a)


def seed_of(name: str) -> int:
    return zlib.crc32(name.encode('utf-8')) & 0x7FFFFFFF


def L(w, h):
    return pg.Layer(w, h)


def rel(path: str) -> str:
    return os.path.relpath(path, ROOT).replace('\\', '/')


def save(layer_or_arr, name, group='', scale=SCALE, note='', margins=None, source=''):
    """Writes the 1:1 source and the x3 runtime texture. margins = 9-patch margins at 1:1 (l, t, r, b)."""
    arr = layer_or_arr.c if isinstance(layer_or_arr, pg.Layer) else layer_or_arr
    img = arr if isinstance(arr, Image.Image) else Image.fromarray(arr, 'RGBA')
    sub = os.path.join(SRC, group) if group else SRC
    os.makedirs(sub, exist_ok=True)
    img.save(os.path.join(sub, name + '.png'))
    d = os.path.join(OUT, group) if group else OUT
    os.makedirs(d, exist_ok=True)
    out = img if scale == 1 else img.resize((img.width * scale, img.height * scale), Image.NEAREST)
    path = os.path.join(d, name + '.png')
    out.save(path)
    e = {'path': rel(path), 'size_1x': [img.width, img.height], 'scale': scale, 'note': note}
    if margins:
        e['margins_1x'] = list(margins)
    if source:
        e['source'] = source
    MANIFEST.append(e)
    return out


# ----------------------------------------------------------------------------- tiny pixel font (3x5)
FONT = {
    'C': ['111', '100', '100', '100', '111'], '-': ['000', '000', '111', '000', '000'],
    '1': ['010', '110', '010', '010', '111'], '7': ['111', '001', '010', '010', '010'],
    '4': ['101', '101', '111', '001', '001'], '/': ['001', '001', '010', '100', '100'],
    '?': ['111', '001', '011', '000', '010'], 'A': ['010', '101', '111', '101', '101'],
    'K': ['101', '110', '100', '110', '101'], 'T': ['111', '010', '010', '010', '010'],
    'E': ['111', '100', '110', '100', '111'], '2': ['110', '001', '010', '100', '111'],
    '3': ['110', '001', '010', '001', '110'], '0': ['111', '101', '101', '101', '111'],
    '.': ['000', '000', '000', '000', '010'], ' ': ['000', '000', '000', '000', '000'],
    '5': ['111', '100', '111', '001', '111'], '8': ['111', '101', '111', '101', '111'],
}


def text(layer, x, y, s, col, gap=1):
    cx = x
    for ch in s:
        g = FONT.get(ch.upper(), FONT[' '])
        for j, row in enumerate(g):
            for i, b in enumerate(row):
                if b == '1':
                    layer.px(cx + i, y + j, col)
        cx += 3 + gap


def scribble(layer, x, y, w, col, seed, density=0.7, height=2):
    """A line of handwriting/typing at 1:1: short strokes with gaps, deterministic."""
    rng = np.random.default_rng(seed)
    cx = x
    while cx < x + w:
        word = int(rng.integers(2, 6))
        for k in range(word):
            if cx >= x + w:
                break
            if rng.random() < density:
                hgt = int(rng.integers(1, height + 1))
                layer.vline(cx, y + (height - hgt), hgt, col)
            if rng.random() < 0.35:
                layer.px(cx, y + height - 1, col)
            cx += 1
        cx += int(rng.integers(1, 3))


def paper_fill(layer, x, y, w, h, cols, seed, grain=0.10):
    """Paper with a soft value-noise grain from a ramp (light first)."""
    n = pg.value_noise(w, h, 6.0, seed=seed, octaves=3)
    t = np.clip((n - 0.5) * 2.0 * grain + 0.5, 0, 1)
    ramp = [np.asarray(c(k), np.float32) for k in cols]
    idx = np.clip((t * (len(ramp) - 1) + pg.bayer(w, h) * 0.5 - 0.25).round().astype(int), 0, len(ramp) - 1)
    for yy in range(h):
        for xx in range(w):
            layer.c[y + yy, x + xx] = ramp[idx[yy, xx]].astype(np.uint8)


def vgrad(layer, x, y, w, h, cols):
    layer.vgrad(x, y, w, h, [c(k) for k in cols])


# ----------------------------------------------------------------------------- board materials
def periodic_noise(w, h, seed, terms=14, fmax=6):
    rng = np.random.default_rng(seed)
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    out = np.zeros((h, w), np.float32)
    for _ in range(terms):
        fx, fy = int(rng.integers(-fmax, fmax + 1)), int(rng.integers(-fmax, fmax + 1))
        if fx == 0 and fy == 0:
            continue
        ph = rng.random() * math.tau
        amp = 1.0 / math.sqrt(fx * fx + fy * fy)
        out += amp * np.cos(math.tau * (fx * xx / w + fy * yy / h) + ph)
    out -= out.min()
    return out / max(1e-6, out.max())


def cork_tile(name, ramp, seed_name, granules=True):
    w = h = 64
    lay = L(w, h)
    n = periodic_noise(w, h, seed_of(seed_name), terms=18, fmax=7)
    wn = pg.white_noise(w, h, seed_of(seed_name + 'w'))
    t = np.clip(n * 0.75 + wn * 0.32 - 0.04, 0, 1)
    idx = np.clip((t * (len(ramp) - 1)).round().astype(int), 0, len(ramp) - 1)
    pal = np.stack([c(k) for k in ramp])
    lay.c[:] = pal[idx]
    if granules:
        rng = np.random.default_rng(seed_of(seed_name + 'g'))
        for _ in range(150):
            x, y = int(rng.integers(0, w)), int(rng.integers(0, h))
            dark = rng.random() < 0.55
            col = c(ramp[0]) if dark else c(ramp[-1])
            lay.px(x % w, y % h, col)
            if rng.random() < 0.4:
                lay.px((x + 1) % w, y % h, c(ramp[1] if dark else ramp[-2]))
    save(lay, name, note='tileable cork (TextureRect STRETCH_TILE)')


def frame_9patch():
    """Archive-wood board frame. Centre transparent (the cork tiles behind it)."""
    s, m = 30, 10
    lay = L(s, s)
    wood = COVER
    for i in range(m):
        col = c(wood[min(len(wood) - 1, 1 + (i * 4) // m)])
        if i == 0:
            col = c(wood[0])
        if i == m - 1:
            col = c(wood[1])
        lay.rect(i, i, s - 2 * i, 1, col)
        lay.rect(i, s - 1 - i, s - 2 * i, 1, col)
        lay.rect(i, i, 1, s - 2 * i, col)
        lay.rect(s - 1 - i, i, 1, s - 2 * i, col)
    # bevel light on top/left, grain flecks
    lay.rect(2, 2, s - 4, 1, c(wood[4]))
    lay.rect(2, 2, 1, s - 4, c(wood[4]))
    rng = np.random.default_rng(seed_of('frame'))
    for _ in range(40):
        x, y = int(rng.integers(1, s - 1)), int(rng.integers(1, s - 1))
        if m - 1 > x > 1 or m - 1 > y > 1 or x > s - m or y > s - m:
            lay.px(x, y, c(wood[2] if rng.random() < 0.5 else wood[3]))
    # mitre joints
    for k in range(1, m - 1):
        lay.px(k, k, c(wood[0]))
        lay.px(s - 1 - k, k, c(wood[0]))
        lay.px(k, s - 1 - k, c(wood[0]))
        lay.px(s - 1 - k, s - 1 - k, c(wood[0]))
    lay.c[m:s - m, m:s - m] = 0
    # soft shadow of the frame on the cork (inside, last rows of the margin: half transparent)
    sh = c(NIGHT, 110)
    lay.c[m - 1, m - 1:s - m + 1] = sh
    lay.c[m - 1:s - m + 1, m - 1] = sh
    save(lay, 'frame', note='board frame 9-patch, centre transparent', margins=(m, m, m, m))


def pin(name, ramp):
    """Push pin seen from the front-top: round head, short needle, shadow to the lower right. 1:1 9x10."""
    lay = L(9, 10)
    sh = c(NIGHT, 120)
    lay.ellipse(5.5, 4.5, 2.6, 2.2, sh)
    lay.px(5, 7, sh)
    lay.px(6, 8, sh)
    lay.ellipse(3.5, 3.0, 2.8, 2.4, c(ramp[1]))
    lay.ellipse(3.3, 2.6, 2.0, 1.6, c(ramp[2]))
    lay.ellipse(3.0, 2.2, 1.1, 0.9, c(ramp[3]))
    lay.px(2, 1, c(ramp[-1]))
    lay.px(3, 6, c(ramp[0]))
    lay.px(4, 6, c(ramp[0]))
    lay.px(3, 7, c(LEAD[3]))
    lay.px(3, 8, c(LEAD[2]))
    save(lay, name, note='push pin; the thread knot sits at (3.5, 3) x3 from the top-left')


def card_9patch(name, face, edge, shade, light, note, burned=False):
    s, m = 15, 5
    lay = L(s, s)
    lay.rect(0, 0, s, s, c(face[0]))
    paper_fill(lay, 1, 1, s - 2, s - 2, face, seed_of(name), grain=0.25)
    lay.rect(0, 0, s, 1, c(light))
    lay.rect(0, 0, 1, s, c(light))
    lay.rect(0, s - 1, s, 1, c(edge))
    lay.rect(s - 1, 0, 1, s, c(edge))
    lay.rect(1, s - 2, s - 2, 1, c(shade))
    lay.rect(s - 2, 1, 1, s - 2, c(shade))
    if burned:
        rng = np.random.default_rng(seed_of(name + 'b'))
        char = [c('#120C0A'), c('#2A1810'), c('#4A2A18'), c('#7A4A26')]
        for y in range(s):
            for x in range(s):
                d = min(x, y, s - 1 - x, s - 1 - y)
                r = rng.random()
                if d == 0 and r < 0.55:
                    lay.c[y, x] = 0
                elif d <= 1 and r < 0.7:
                    lay.c[y, x] = char[int(rng.integers(0, 2))]
                elif d <= 2 and r < 0.45:
                    lay.c[y, x] = char[int(rng.integers(2, 4))]
    save(lay, name, note=note, margins=(m, m, m, m))


def simple_9patch(name, s, m, draw, note):
    lay = L(s, s)
    draw(lay, s)
    save(lay, name, note=note, margins=(m, m, m, m))


def tag_draw(lay, s):
    """Masking-tape label for thread captions: pale tape, ragged ends, faint edge."""
    rng = np.random.default_rng(seed_of('tag'))
    lay.rect(0, 0, s, s, c('#D8CDA2'))
    paper_fill(lay, 0, 0, s, s, ['#E2D8B0', '#D8CDA2', '#CBBF92'], seed_of('tagp'), grain=0.3)
    lay.rect(0, 0, s, 1, c('#EDE4C0'))
    lay.rect(0, s - 1, s, 1, c('#B8AC80'))
    for y in range(s):
        if rng.random() < 0.5:
            lay.c[y, 0] = 0
        if rng.random() < 0.5:
            lay.c[y, s - 1] = 0


def note_draw(lay, s):
    """Typed summary sheet: off-white, red margin rule on the left, slight edge shade."""
    lay.rect(0, 0, s, s, c(PAPER_L))
    paper_fill(lay, 1, 1, s - 2, s - 2, [PAPER_L, PAPER, PAPER_M], seed_of('note'), grain=0.18)
    lay.rect(0, s - 1, s, 1, c(PAPER_D))
    lay.rect(s - 1, 0, 1, s, c(PAPER_D))
    lay.rect(0, 0, s, 1, c('#FBF7E8'))
    lay.rect(5, 0, 1, s, c(RED_L, 200))


def ghost_draw(lay, s):
    """A reserved place on the cork: a lighter rectangle where a card will hang, four old pin holes."""
    lay.c[:] = c('#E8C89A', 30)
    lay.c[0, :] = c('#E8C89A', 70)
    lay.c[s - 1, :] = c('#E8C89A', 70)
    lay.c[:, 0] = c('#E8C89A', 70)
    lay.c[:, s - 1] = c('#E8C89A', 70)
    for x, y in ((2, 2), (s - 3, 2)):
        lay.px(x, y, c(NIGHT, 160))


def focus_draw(lay, s, outer=AMBER_L, inner=COPPER_D):
    """Focus ring: a dark line on the card edge, two pixels of light inside it (9-patch, centre clear)."""
    lay.c[:] = 0
    for i in range(s):
        for (x, y) in ((i, 0), (i, s - 1), (0, i), (s - 1, i)):
            lay.c[y, x] = c(inner)
        for d in (1, 2):
            for (x, y) in ((i, d), (i, s - 1 - d), (d, i), (s - 1 - d, i)):
                if d <= x <= s - 1 - d and d <= y <= s - 1 - d:
                    lay.c[y, x] = c(outer)


def unknown_marker():
    """Empty pin with a small blank tag and a „?“ -- an item that is not in the file yet (no spoiler)."""
    lay = L(18, 22)
    tag = L(14, 13)
    tag.rect(0, 0, 14, 13, c(PAPER_M))
    tag.rect(0, 0, 14, 1, c(PAPER))
    tag.rect(0, 12, 14, 1, c(PAPER_D))
    tag.rect(13, 0, 1, 13, c(PAPER_D))
    tag.px(0, 0, c(NIGHT, 0))
    tag.px(13, 0, c(NIGHT, 0))
    text(tag, 6, 4, '?', c(INK_DIM))
    sh = L(14, 13)
    sh.c[:] = c(NIGHT, 90)
    over(lay, sh, 3, 8)
    lay.blit(tag, 2, 6)
    # string from the pin to the tag
    lay.px(8, 4, c(PAPER_D1))
    lay.px(8, 5, c(PAPER_D1))
    p = L(9, 10)
    p.ellipse(3.5, 3.0, 2.8, 2.4, c(WALL2))
    p.ellipse(3.3, 2.6, 2.0, 1.6, c(WALL3))
    p.px(2, 1, c(WALL4))
    lay.blit(p, 5, 0)
    save(lay, 'unknown', note='empty pin + „?“ tag for items not yet in the file')


def folder():
    """Closed manila file folder for the journal cover page, red C-17 stamp, paper corners peeking out."""
    w, h = 124, 86
    lay = L(w, h)
    # papers behind (peeking at the top right)
    lay.rect(70, 4, 46, 12, c(PAPER_L))
    lay.rect(70, 4, 46, 1, c('#FBF7E8'))
    lay.rect(115, 4, 1, 12, c(PAPER_D))
    lay.rect(58, 7, 40, 10, c(SNOW[3]))
    lay.rect(97, 7, 1, 10, c(SNOW[0]))
    # back flap with the tab
    manila = ['#8A6A3A', '#A8844A', '#C4A060', '#D8B878', '#E8CC92']
    lay.rect(2, 12, w - 6, h - 16, c(manila[1]))
    lay.rect(6, 6, 40, 8, c(manila[2]))
    lay.rect(6, 6, 40, 1, c(manila[3]))
    lay.px(6, 6, CLEAR)
    lay.px(45, 6, CLEAR)
    # front cover
    paper_fill(lay, 2, 16, w - 6, h - 20, [manila[3], manila[2], manila[2], manila[1]], seed_of('folder'), grain=0.35)
    lay.rect(2, 16, w - 6, 1, c(manila[4]))
    lay.rect(2, h - 5, w - 6, 1, c(manila[0]))
    lay.rect(w - 5, 16, 1, h - 20, c(manila[0]))
    lay.rect(2, 16, 1, h - 20, c(manila[4]))
    # shadow
    lay.rect(4, h - 4, w - 6, 2, c(NIGHT, 120))
    lay.rect(w - 4, 18, 2, h - 20, c(NIGHT, 120))
    # label field (blank: the journal writes the file title and the places on it in HD type)
    lay.rect(10, 24, 74, 22, c(PAPER_L))
    lay.rect(10, 24, 74, 1, c('#FBF7E8'))
    lay.rect(10, 45, 74, 1, c(PAPER_D))
    lay.rect(83, 24, 1, 22, c(PAPER_D))
    lay.rect(10, 34, 74, 1, c('#DCD4B8'))
    # red stamp „C-17“ (rectangle frame + glyphs, slightly worn)
    sx, sy = 70, 46
    st = L(40, 22)
    st.rect(0, 0, 40, 1, c(RED))
    st.rect(0, 21, 40, 1, c(RED))
    st.rect(0, 0, 1, 22, c(RED))
    st.rect(39, 0, 1, 22, c(RED))
    st.rect(2, 2, 36, 1, c(RED))
    st.rect(2, 19, 36, 1, c(RED))
    big = L(16, 5)
    text(big, 0, 0, 'C-17', c(RED))
    bi = big.image().resize((32, 10), Image.NEAREST)
    st.blit(pg_from_image(bi), 4, 6)
    rng = np.random.default_rng(seed_of('stamp'))
    m = st.alpha()
    holes = (rng.random(m.shape) < 0.16) & m
    st.c[holes] = 0
    lay.blit(st, sx, sy)
    # string tie
    lay.rect(2, 60, w - 6, 1, c(manila[0]))
    lay.ellipse(18, 60.5, 2.2, 2.2, c(PAPER_D1))
    lay.px(17, 59, c(PAPER_M))
    save(lay, 'folder', note='journal cover: closed file folder with the C-17 stamp')


def over(dst: pg.Layer, src: pg.Layer, x: int, y: int) -> None:
    """Real alpha-over (pg.Layer.blit is binary): for soft shadows."""
    a = Image.fromarray(dst.c, 'RGBA')
    a.alpha_composite(Image.fromarray(src.c, 'RGBA'), (x, y))
    dst.c[:] = np.asarray(a, np.uint8)


def pg_from_image(img: Image.Image) -> pg.Layer:
    a = np.asarray(img.convert('RGBA'), np.uint8)
    lay = L(a.shape[1], a.shape[0])
    lay.c[:] = a
    return lay


def vertical_tabs():
    """The round-1 paper tab (frames/ptab_*.png, x3) turned 90 degrees clockwise: it sticks out to the right of
    the journal sheet. 9-patch margins at x3 turn with it (l,t,r,b 12,12,12,6 -> 6,12,12,12)."""
    for st in ('normal', 'hover', 'pressed', 'focus'):
        src = os.path.join(FRAMES, 'ptab_%s.png' % st)
        if not os.path.exists(src):
            continue
        im = Image.open(src).convert('RGBA').transpose(Image.ROTATE_270)
        path = os.path.join(OUT, 'vtab_%s.png' % st)
        im.save(path)
        MANIFEST.append({'path': rel(path), 'size_1x': [im.width // 3, im.height // 3], 'scale': 3,
            'note': 'vertical journal tab „Akte“ (turned copy of %s)' % rel(src), 'margins_x3': [6, 12, 12, 12],
            'source': rel(src)})


# ----------------------------------------------------------------------------- card pictures
## item -> (document close-up, crop x, crop y): 54x24 at 1:1 around the telling detail.
DOC_CROPS = {
    'ev_damaged_seal': ('karsk_seal', 77, 83),
    'ev_timetable': ('karsk_timetable', 10, 84),
    'ev_ledger': ('karsk_ledger', 101, 161),
    'ev_plan_a': ('berlin_plan_a', 196, 61),
    'ev_plan_b': ('berlin_plan_b', 216, 105),
    'ev_emil_note': ('berlin_emil_note', 52, 41),
    'ev_c3_weighbill': ('veltrava_station_weighbill', 136, 97),
    'ev_c3_departures': ('veltrava_station_departures', 55, 109),
    'ev_c3_travel_order': ('veltrava_station_travel_order', 22, 113),
    'ev_c3_seating': ('veltrava_protocol_seating', 90, 101),
    'ev_c3_booth_log': ('veltrava_protocol_booth_log', 26, 107),
    'ev_c3_carbon': ('veltrava_hall_carbon', 108, 49),
}


def doc_thumbs():
    for item, (doc, x, y) in DOC_CROPS.items():
        src = os.path.join(DOCS, doc + '.png')
        if not os.path.exists(src):
            print('missing close-up', src)
            continue
        im = Image.open(src).convert('RGBA')
        x = max(0, min(im.width - THUMB[0], x))
        y = max(0, min(im.height - THUMB[1], y))
        crop = im.crop((x, y, x + THUMB[0], y + THUMB[1]))
        save(crop, item, group='thumbs', note='detail crop of the inspect close-up', source='%s @ %d,%d' % (rel(src), x, y))
        hist = os.path.join(DOCS, doc + '_hist.png')
        if os.path.exists(hist):
            hc = Image.open(hist).convert('RGBA').crop((x, y, x + THUMB[0], y + THUMB[1]))
            if np.asarray(hc).tobytes() != np.asarray(crop).tobytes():
                save(hc, item + '_hist', group='thumbs', note='detail crop of the _hist close-up', source=rel(hist))


def T():
    return L(*DRAW)


def photo_bg(lay, top, bottom, seed):
    w, h = DRAW
    vgrad(lay, 0, 0, w, h, [top, bottom])
    n = pg.white_noise(w, h, seed)
    lay.c[..., :3] = np.clip(lay.c[..., :3].astype(np.int16) + ((n - 0.5) * 10).astype(np.int16)[..., None], 0, 255).astype(np.uint8)


def draw_cut_seal():
    lay = T()
    photo_bg(lay, WALL2, WALL0, seed_of('seal_bg'))
    # crate front: planks, a nail row, the hole the wire ran through
    for k in range(3):
        lay.rect(0, k * 6, 54, 5, c(COVER[2 + (k % 2)]))
        lay.rect(0, k * 6 + 5, 54, 1, c(COVER[0]))
        lay.rect(0, k * 6, 54, 1, c(COVER[4]))
    for x in (5, 48):
        for k in range(3):
            lay.px(x, 2 + k * 6, c(LEAD[3]))
    lay.rect(19, 9, 3, 3, c(NIGHT))
    # the wire: out of the crate, down to the seal, then cut -- the far end springs away
    lay.line(20, 11, 20, 15, c(LEAD[3]))
    lay.line(21, 15, 22, 16, c(LEAD[3]))
    lay.line(33, 16, 36, 13, c(LEAD[3]))
    lay.line(36, 13, 40, 12, c(LEAD[3]))
    lay.px(40, 12, c(SNOW[4]))
    lay.px(33, 16, c(SNOW[4]))
    # the lead seal (flattened disk with C-17 pressed in)
    lay.ellipse(28, 21, 8.2, 6.4, c(LEAD[0]))
    lay.ellipse(27.6, 20.6, 7.4, 5.6, c(LEAD[2]))
    lay.ellipse(26.8, 19.6, 5.0, 3.4, c(LEAD[3]))
    lay.px(23, 17, c(LEAD[4]))
    lay.px(24, 16, c(LEAD[4]))
    text(lay, 22, 19, 'C-17', c(LEAD[0]), gap=0)
    lay.px(21, 15, c(LEAD[3]))
    # shadow under the seal
    lay.rect(22, 28, 14, 1, c(NIGHT, 150))
    return lay


def draw_night_book():
    lay = T()
    lay.rect(0, 0, 54, 30, c(COVER[1]))
    # open book: two pages
    paper_fill(lay, 2, 2, 24, 26, [PAPER_L, PAPER, PAPER], seed_of('nb_l'), grain=0.15)
    paper_fill(lay, 28, 2, 24, 26, [PAPER_L, PAPER, PAPER], seed_of('nb_r'), grain=0.15)
    lay.rect(26, 2, 2, 26, c(PAPER_D1))
    lay.rect(27, 2, 1, 26, c(COVER[0]))
    for y in range(6, 28, 4):
        lay.rect(3, y, 22, 1, c('#C6CCC4'))
        lay.rect(29, y, 22, 1, c('#C6CCC4'))
    for k, y in enumerate((4, 8, 12, 16)):
        scribble(lay, 4, y, 18 - (k % 2) * 4, c(INK_B), seed_of('nbl%d' % k))
    # right page: 23.10 Weiss (blue ink, round hand) / 23.25 ab (another hand: black, heavier)
    text(lay, 30, 3, '23.10', c(BLUE_INK), gap=0)
    scribble(lay, 44, 4, 7, c(BLUE_INK), seed_of('nbw'))
    scribble(lay, 30, 10, 18, c(BLUE_INK), seed_of('nbw2'))
    text(lay, 30, 15, '23.2', c(INK), gap=0)
    lay.rect(30, 21, 1, 1, c(INK))
    for k in range(5):
        lay.rect(43 + k * 2, 17 - (k % 2), 2, 2, c(INK))
    lay.rect(30, 23, 12, 1, c(RED, 160))   # someone's pencil underline
    return lay


def draw_intake_book():
    lay = T()
    paper_fill(lay, 0, 0, 54, 30, [PAPER_L, PAPER, PAPER_M], seed_of('ib'), grain=0.2)
    lay.rect(0, 0, 54, 5, c(INK_B))
    for x in (17, 35):
        lay.rect(x, 0, 1, 30, c(PAPER_D))
    for k, x in enumerate((3, 21, 39)):
        lay.rect(x, 2, 10, 1, c(PAPER_L))
    for r in range(6):
        y = 7 + r * 4
        lay.rect(0, y + 3, 54, 1, c('#C9CBBF'))
        hot = r in (3, 4)
        col = c(RED) if hot else c(INK_B)
        scribble(lay, 2, y, 13, col, seed_of('ibr%d' % r))
        scribble(lay, 19, y, 14, c(INK_B), seed_of('ibm%d' % r))
        scribble(lay, 37, y, 14, c(INK_B), seed_of('ibn%d' % r))
    text(lay, 2, 19, 'C-17', c(RED), gap=0)
    lay.rect(0, 18, 1, 9, c(RED))
    return lay


def draw_scarf():
    lay = T()
    photo_bg(lay, WALL1, NIGHT1, seed_of('scarf_bg'))
    # card cabinet behind: a row of drawer fronts, one pulled open (dark)
    for k in range(4):
        x = 1 + k * 13
        lay.rect(x, 1, 12, 8, c(WALL3))
        lay.rect(x, 1, 12, 1, c(WALL4))
        lay.rect(x + 4, 4, 4, 2, c(PAPER_M))
    lay.rect(40, 1, 12, 8, c(NIGHT))
    lay.rect(41, 6, 10, 3, c(PAPER_D1))
    # chair back seen from behind: two posts and a top rail
    lay.rect(12, 11, 26, 3, c(COVER[3]))
    lay.rect(12, 11, 26, 1, c(COVER[4]))
    lay.rect(13, 14, 3, 16, c(COVER[2]))
    lay.rect(34, 14, 3, 16, c(COVER[2]))
    lay.rect(16, 20, 18, 2, c(COVER[1]))
    # the scarf over the rail: a soft fold on top, two long ends hanging down (one longer), fringes
    lay.rect(15, 9, 21, 4, c(WINE[2]))
    lay.rect(15, 9, 21, 1, c(WINE[4]))
    lay.rect(17, 12, 6, 1, c(WINE[1]))
    lay.rect(15, 13, 7, 12, c(WINE[2]))
    lay.rect(15, 13, 1, 12, c(WINE[3]))
    lay.rect(21, 13, 1, 12, c(WINE[1]))
    lay.line(16, 16, 20, 20, c(WINE[3]))
    lay.rect(28, 13, 7, 16, c(WINE[2]))
    lay.rect(34, 13, 1, 16, c(WINE[1]))
    lay.rect(28, 13, 1, 16, c(WINE[3]))
    lay.line(29, 18, 33, 22, c(WINE[3]))
    for x in range(15, 22, 2):
        lay.px(x, 25, c(WINE[4]))
        lay.px(x, 26, c(WINE[3]))
    for x in range(28, 35, 2):
        lay.px(x, 29, c(WINE[4]))
    return lay


def draw_halves():
    lay = T()
    photo_bg(lay, COVER[2], COVER[1], seed_of('halves_bg'))
    # lamp glow in the middle
    g = pg.value_noise(54, 30, 9.0, seed=seed_of('glow'), octaves=2)
    yy, xx = np.mgrid[0:30, 0:54]
    d = np.sqrt(((xx - 27) / 30.0) ** 2 + ((yy - 12) / 18.0) ** 2)
    glow = np.clip(1.0 - d, 0, 1) * 34
    lay.c[..., :3] = np.clip(lay.c[..., :3].astype(np.int16) + glow[..., None].astype(np.int16), 0, 255).astype(np.uint8)
    # Alexei's chain (left): weighbill with copper frame, dark departures card, travel order (cool paper)
    lay.rect(3, 4, 13, 9, c(COPPER))
    lay.rect(4, 5, 11, 7, c(PAPER))
    lay.rect(9, 9, 5, 2, c(RED))
    lay.rect(6, 14, 14, 8, c(NAVY_L))
    lay.rect(7, 18, 12, 1, c(PAPER_M))
    lay.rect(3, 22, 11, 7, c(SNOW[3]))
    scribble(lay, 4, 24, 8, c(INK_B), seed_of('hv1'))
    # gap: the line between the halves
    lay.rect(26, 2, 1, 27, c(COVER[0], 180))
    # Konrad's half (right): seating plan, booth log, carbon
    lay.rect(31, 3, 13, 10, c(PAPER_L))
    lay.rect(34, 5, 7, 6, c(BLUE_INK))
    lay.rect(35, 6, 5, 4, c(PAPER_L))
    lay.rect(41, 14, 10, 9, c(PAPER))
    for y in (16, 18, 20):
        scribble(lay, 42, y, 8, c(INK_B), seed_of('hv%d' % y))
    lay.rect(30, 21, 12, 8, c('#5A5658'))
    lay.rect(31, 22, 10, 6, c(PAPER_M))
    scribble(lay, 32, 24, 8, c(PENCIL), seed_of('hv9'))
    return lay


def draw_kordon_plan(burned=False):
    lay = T()
    paper_fill(lay, 0, 0, 54, 30, ['#E8E8DA', '#DCDED0', '#CED2C4'], seed_of('kp'), grain=0.2)
    ink = c(BLUE_INK)
    # the room
    lay.rect(6, 5, 42, 1, ink)
    lay.rect(6, 22, 42, 1, ink)
    lay.rect(6, 5, 1, 18, ink)
    lay.rect(47, 5, 1, 18, ink)
    # doors left and right (gaps + swing)
    lay.rect(6, 11, 1, 5, c('#DCDED0'))
    lay.rect(47, 11, 1, 5, c('#DCDED0'))
    lay.line(7, 11, 10, 14, ink)
    lay.line(46, 11, 43, 14, ink)
    # the Line through the room: red dashes
    for y in range(1, 29, 3):
        lay.rect(27, y, 1, 2, c(RED))
    # counter in the middle
    lay.rect(24, 12, 7, 3, ink)
    lay.rect(25, 13, 5, 1, c('#DCDED0'))
    # two benches in a different (sepia) ink, revision c
    sep = c('#7A4A2E')
    lay.rect(10, 19, 12, 2, sep)
    lay.rect(33, 19, 12, 2, sep)
    lay.rect(10, 19, 12, 1, c('#9A6A44'))
    # title block bottom right
    lay.rect(36, 25, 17, 4, ink)
    lay.rect(37, 26, 15, 2, c('#E8E8DA'))
    scribble(lay, 38, 26, 12, ink, seed_of('kptb'), height=1)
    if burned:
        rng = np.random.default_rng(seed_of('kpburn'))
        n = pg.value_noise(54, 30, 7.0, seed=seed_of('kpb'), octaves=3)
        yy, xx = np.mgrid[0:30, 0:54]
        edge = np.minimum(np.minimum(xx, 53 - xx), np.minimum(yy, 29 - yy)).astype(np.float32)
        heat = n * 1.4 - edge / 9.0 + (xx / 54.0) * 0.35
        lay.c[heat > 0.62] = c('#120C0A')
        mask = (heat > 0.48) & (heat <= 0.62)
        lay.c[mask] = c('#3A2214')
        mask2 = (heat > 0.38) & (heat <= 0.48)
        lay.c[mask2] = c('#8A5A30')
        holes = heat > 0.82
        lay.c[holes] = 0
        _ = rng
    return lay


def draw_file():
    lay = T()
    photo_bg(lay, WALL1, NIGHT, seed_of('file_bg'))
    manila = ['#7A5A2E', '#A8844A', '#C4A060', '#D8B878']
    # papers sticking out
    lay.rect(9, 5, 36, 4, c(PAPER_L))
    lay.rect(12, 3, 30, 3, c(SNOW[3]))
    # folder body
    lay.rect(6, 8, 42, 19, c(manila[2]))
    lay.rect(6, 8, 42, 1, c(manila[3]))
    lay.rect(6, 26, 42, 1, c(manila[0]))
    lay.rect(47, 8, 1, 19, c(manila[0]))
    # label with C-17
    lay.rect(10, 12, 20, 8, c(PAPER_L))
    text(lay, 12, 14, 'C-17', c(RED), gap=1)
    # soot and heat on the right edge („Der Einband ist warm“)
    n = pg.value_noise(54, 30, 5.0, seed=seed_of('soot'), octaves=3)
    yy, xx = np.mgrid[0:30, 0:54]
    soot = (n + (xx - 30) / 26.0) > 1.0
    soot &= lay.c[..., 3] > 0
    soot &= (xx > 30) & (yy > 6) & (yy < 28)
    lay.c[soot] = c('#3A2A20')
    glow = soot & (n > 0.62)
    lay.c[glow] = c(COPPER)
    return lay


def draw_bolt():
    lay = T()
    # steel door filling the frame, lit from the gap below
    lay.rect(0, 0, 54, 30, c(STEEL[1]))
    for x in range(0, 54, 9):
        lay.rect(x, 0, 1, 25, c(STEEL[0]))
    for k in range(4):
        lay.px(4 + k * 13, 3, c(STEEL[3]))
        lay.px(4 + k * 13, 20, c(STEEL[3]))
    # the bolt on the outside, seen through the crack: bar + housing
    lay.rect(16, 10, 24, 3, c(LEAD[3]))
    lay.rect(16, 10, 24, 1, c(LEAD[4]))
    lay.rect(38, 8, 6, 7, c(LEAD[1]))
    lay.rect(18, 13, 3, 4, c(LEAD[2]))
    # gap at the floor: snow light, fresh tracks to the gate
    lay.rect(0, 25, 54, 5, c(SNOW[2]))
    lay.rect(0, 25, 54, 1, c(SNOW[4]))
    for k in range(6):
        x = 6 + k * 8
        lay.rect(x, 27 - (k % 2), 3, 2, c(SNOW[0]))
    lay.rect(0, 24, 54, 1, c(NIGHT))
    return lay


def draw_cut_hose():
    lay = T()
    photo_bg(lay, WALL1, WALL0, seed_of('hose_bg'))
    # red fire case, door open
    lay.rect(4, 2, 26, 26, c(FIRE_RED[2]))
    lay.rect(4, 2, 26, 1, c(FIRE_RED[3]))
    lay.rect(6, 4, 22, 22, c(FIRE_RED[0]))
    lay.rect(30, 3, 10, 24, c(FIRE_RED[1]))   # open door
    lay.rect(31, 5, 8, 20, c('#7E9AA6'))      # glass pane
    lay.rect(32, 6, 2, 8, c('#B8CCD2'))
    # hose coil
    for r, col in ((8.5, HOSE[1]), (6.5, HOSE[2]), (4.5, HOSE[1]), (2.5, HOSE[0])):
        lay.ellipse(17, 15, r, r * 0.9, c(col))
    lay.ellipse(17, 15, 1.5, 1.4, c(FIRE_RED[0]))
    # the cut end hanging out: smooth cut face (bright oval)
    lay.rect(22, 21, 4, 7, c(HOSE[2]))
    lay.rect(24, 25, 9, 3, c(HOSE[2]))
    lay.rect(33, 25, 2, 3, c(HOSE[3]))
    lay.px(34, 26, c(HOSE[0]))
    lay.rect(41, 26, 9, 2, c(HOSE[1]))     # the other piece on the floor
    lay.rect(40, 26, 1, 2, c(HOSE[3]))
    return lay


def draw_escort_list():
    lay = T()
    paper_fill(lay, 0, 0, 54, 30, [PAPER_L, PAPER, PAPER_M], seed_of('el'), grain=0.2)
    # burnt binding edge on the left
    rng = np.random.default_rng(seed_of('elb'))
    for y in range(30):
        w = int(rng.integers(1, 4))
        lay.rect(0, y, w, 1, c('#2A1810'))
        lay.px(w, y, c('#8A5A30'))
    # two column heads (West / Ost) as stamped blocks
    lay.rect(6, 2, 20, 4, c(INK_B))
    lay.rect(30, 2, 20, 4, c(INK_B))
    lay.rect(8, 3, 16, 1, c(PAPER_L))
    lay.rect(32, 3, 16, 1, c(PAPER_L))
    for r in range(5):
        y = 9 + r * 4
        scribble(lay, 7, y, 17, c(INK_B), seed_of('elw%d' % r))
        scribble(lay, 31, y, 17, c(INK_B), seed_of('elo%d' % r))
    # Tür Ost, third row: a pencil ring around the name
    y = 9 + 2 * 4
    lay.rect(29, y - 2, 21, 1, c(RED_L))
    lay.rect(29, y + 3, 21, 1, c(RED_L))
    lay.rect(28, y - 1, 1, 4, c(RED_L))
    lay.rect(50, y - 1, 1, 4, c(RED_L))
    return lay


def draw_generic(kind):
    lay = T()
    if kind == 'physical_clue':
        photo_bg(lay, WALL2, WALL0, seed_of('gen_pc'))
        lay.rect(20, 8, 16, 14, c(PAPER_M))
        lay.rect(20, 8, 16, 1, c(PAPER_L))
        lay.ellipse(23, 11, 1.2, 1.2, c(WALL0))
        lay.line(23, 11, 15, 4, c(PAPER_D1))
        scribble(lay, 22, 15, 11, c(INK_B), seed_of('gpc'))
        scribble(lay, 22, 18, 8, c(INK_B), seed_of('gpc2'))
    else:
        paper_fill(lay, 0, 0, 54, 30, [PAPER_L, PAPER, PAPER_M], seed_of('gen_doc'), grain=0.2)
        for k in range(6):
            scribble(lay, 4, 3 + k * 4, 44 - (k % 3) * 7, c(INK_B), seed_of('gd%d' % k))
    return lay


ORIGINAL = {
    'ev_c3_cut_seal': draw_cut_seal,
    'ev_c3_night_book': draw_night_book,
    'ev_c3_intake_book': draw_intake_book,
    'ev_c3_scarf': draw_scarf,
    'ev_c3_halves': draw_halves,
    'ev_c3_kordon_plan': draw_kordon_plan,
    'ev_c3_file': draw_file,
    'ev_c3_bolt': draw_bolt,
    'ev_c3_cut_hose': draw_cut_hose,
    'ev_c3_escort_list': draw_escort_list,
}


## rows cut from the 54x30 drawing for the 54x24 card window (default 3 = centre)
CUT_Y = {'ev_c3_intake_book': 0, 'ev_c3_night_book': 2, 'ev_c3_escort_list': 1, 'ev_c3_cut_seal': 4, 'ev_c3_bolt': 6,
         'ev_c3_scarf': 4, 'ev_c3_halves': 3, 'ev_c3_file': 3}


def cut(lay: pg.Layer, oy: int) -> pg.Layer:
    out = L(*THUMB)
    out.c[:] = lay.c[oy:oy + THUMB[1], :THUMB[0]]
    return out


def original_thumbs():
    for item, fn in ORIGINAL.items():
        save(cut(fn(), CUT_Y.get(item, 3)), item, group='thumbs', note='original drawing (no inspect close-up exists)')
    save(cut(draw_kordon_plan(burned=True), 3), 'ev_c3_kordon_plan_burned', group='thumbs',
         note='Blatt 7 after the fire (choice c3d_choose = admit_plan: the sheet stayed on the wall)')
    save(cut(draw_generic('document'), 3), '_document', group='thumbs', note='fallback picture for a document')
    save(cut(draw_generic('physical_clue'), 3), '_physical_clue', group='thumbs', note='fallback picture for a physical clue')


# ----------------------------------------------------------------------------- Chapter 4 (C4_DESIGN.md §2.5)
RUST = ['#3A1E14', '#5A2E1C', '#7A4026', '#9A5634']     # red-brown wagon paint
GREEN_SPINE = ['#1E2A22', '#2A3A2E', '#3A4E3E']


def draw_c4_book_gap():
    lay = T()
    photo_bg(lay, WALL1, NIGHT1, seed_of('c4gap_bg'))
    lay.rect(0, 22, 54, 3, c(COVER[3]))
    lay.rect(0, 22, 54, 1, c(COVER[4]))
    rng = np.random.default_rng(seed_of('c4gap'))
    x = 1
    while x < 53:
        if 20 <= x < 33:
            x = 33
            continue
        w = int(rng.integers(3, 5))
        col = [GREEN_SPINE[1], COVER[2], WALL2, GREEN_SPINE[2], COVER[1]][int(rng.integers(0, 5))]
        h = int(rng.integers(13, 18))
        lay.rect(x, 22 - h, w, h, c(col))
        lay.rect(x, 22 - h + 3, w, 1, c(PAPER_D1))
        lay.rect(x, 22 - h + 9, w, 1, c(PAPER_D1))
        lay.vline(x, 22 - h, h, c(NIGHT))
        x += w + 1
    # the slip on the empty board (Lev took the three January books „zur Durchsicht“)
    lay.rect(22, 18, 9, 4, c(PAPER_L))
    scribble(lay, 23, 19, 7, c(INK_B), seed_of('c4gapn'), height=1)
    lay.rect(22, 22, 9, 1, c(NIGHT, 160))
    return lay


def draw_c4_cut_signatures():
    lay = T()
    paper_fill(lay, 0, 0, 54, 30, [PAPER_L, PAPER, PAPER_M], seed_of('c4sig'), grain=0.2)
    for x in (12, 30):
        lay.rect(x, 0, 1, 30, c(PAPER_D))
    for r in range(7):
        y = 2 + r * 4
        lay.rect(0, y + 3, 54, 1, c('#C9CBBF'))
        scribble(lay, 1, y, 10, c(INK_B), seed_of('c4s%d' % r))
        scribble(lay, 14, y, 14, c(INK_B), seed_of('c4t%d' % r))
    for r in (1, 3, 5):   # three clean cut-outs in the column "Genehmigt", a note beside each
        y = 2 + r * 4
        lay.rect(33, y - 1, 12, 4, c('#3A3630'))
        lay.rect(33, y - 1, 12, 1, c(PAPER_D2))
        scribble(lay, 46, y, 7, c(BLUE_INK), seed_of('c4m%d' % r), height=1)
    return lay


def draw_c4_carbon():
    lay = T()
    photo_bg(lay, COPPER_D, COVER[1], seed_of('c4carb_bg'))
    yy, xx = np.mgrid[0:30, 0:54]
    d = np.sqrt(((xx - 27) / 24.0) ** 2 + ((yy - 13) / 14.0) ** 2)
    glow = np.clip(1.0 - d, 0, 1)
    sheet = ['#3E4A5C', '#56637A', '#7A88A0', '#A8B4C8']
    for y in range(3, 28):
        for x in range(6, 48):
            lay.c[y, x] = c(sheet[min(3, int(glow[y, x] * 3.6))])
    for r in range(4):
        scribble(lay, 9, 6 + r * 4, 30 - r * 3, c('#2A3242'), seed_of('c4cr%d' % r), height=1)
    # the pressure trace of the cut-out signature, light against the lamp
    scribble(lay, 18, 21, 20, c('#E8EEF8'), seed_of('c4arch'), density=0.9, height=2)
    lay.rect(16, 24, 24, 1, c('#C8D2E2'))
    return lay


def draw_c4_tunnel_plan():
    lay = T()
    paper_fill(lay, 0, 0, 54, 30, ['#E2DCC6', '#D6CFB6', '#C8C0A4'], seed_of('c4tp'), grain=0.35)
    for x in range(0, 54, 3):
        lay.px(x, 0, c(PAPER_D))
        lay.px(x, 29, c(PAPER_D))
    ink = c(BLUE_INK)
    pts = [(2, 8), (14, 8), (22, 14), (38, 14), (46, 20), (52, 20)]
    for (a, b) in zip(pts, pts[1:]):
        lay.line(a[0], a[1], b[0], b[1], ink)
        lay.line(a[0], a[1] + 3, b[0], b[1] + 3, ink)
    for (a, b) in zip(pts, pts[1:]):   # someone's pencil trace along the tunnel
        lay.line(a[0], a[1] + 1, b[0], b[1] + 1, c(PENCIL))
    lay.rect(47, 24, 6, 1, ink)       # the track without a number
    lay.rect(4, 22, 14, 5, c('#D6CFB6'))
    lay.rect(4, 22, 14, 1, ink)
    scribble(lay, 5, 24, 11, ink, seed_of('c4tpt'), height=1)
    return lay


def draw_c4_fresh_tracks():
    lay = T()
    photo_bg(lay, WALL0, NIGHT, seed_of('c4ft_bg'))
    for (x0, x1) in ((6, 22), (48, 32)):   # blank rails running into the dark
        lay.line(x0, 29, x1, 6, c(LEAD[4]))
        lay.line(x0 + (1 if x0 < 27 else -1), 29, x1, 6, c(LEAD[2]))
    rng = np.random.default_rng(seed_of('c4dust'))
    for _ in range(40):
        x, y = int(rng.integers(0, 54)), int(rng.integers(14, 30))
        lay.px(x, y, c(WALL3 if rng.random() < 0.6 else WALL2))
    for k in range(5):   # trampled dust
        lay.rect(10 + k * 7, 25 - k * 2, 3, 2, c(WALL1))
    lay.rect(0, 12, 54, 2, c(STEEL[1]))   # the iron threshold, a drop of red-brown paint, still soft
    lay.rect(0, 12, 54, 1, c(STEEL[3]))
    lay.ellipse(30, 13, 1.6, 1.2, c(RUST[2]))
    lay.px(30, 12, c(RUST[3]))
    return lay


def draw_c4_notice():
    lay = T()
    lay.rect(0, 0, 54, 30, c(WALL2))
    paper_fill(lay, 2, 1, 50, 28, [PAPER_L, PAPER, PAPER_M], seed_of('c4no'), grain=0.2)
    lay.rect(4, 3, 20, 2, c(INK_B))
    for r in range(3):
        scribble(lay, 4, 7 + r * 3, 20, c(INK_B), seed_of('c4nl%d' % r), height=1)
    scribble(lay, 4, 16, 18, c(BLUE_INK), seed_of('c4nadd'), height=2)   # the fresh addition
    lay.rect(27, 4, 23, 22, c(SNOW[3]))   # the site plan Sued 8: three rings over three blocks
    lay.rect(27, 4, 23, 1, c(SNOW[4]))
    for k in range(3):
        lay.rect(29 + k * 7, 9, 5, 10, c(SNOW[1]))
        lay.ellipse(31 + k * 7, 13, 2.2, 2.2, c(RED))
        lay.ellipse(31 + k * 7, 13, 1.2, 1.2, c(SNOW[3]))
    lay.rect(40, 21, 9, 4, c(BLUE_INK))
    lay.rect(41, 22, 7, 2, c(SNOW[3]))
    lay.px(38, 3, c(LEAD[3]))
    return lay


def draw_c4_route_board():
    lay = T()
    for y in range(30):
        for x in range(54):
            lay.c[y, x] = c('#DCE2E2' if (x + y) % 7 else '#D2D8DA')
    route = [(2, 22), (12, 22), (18, 16), (30, 16), (36, 10), (52, 10)]   # line 74 in Marta's pencil
    for (a, b) in zip(route, route[1:]):
        lay.line(a[0], a[1], b[0], b[1], c(INK_B))
        lay.line(a[0], a[1] + 1, b[0], b[1] + 1, c(INK_B))
    for (x, y) in ((16, 22), (26, 22), (40, 16)):   # three dated detours
        for i in range(0, 10, 2):
            lay.px(x + i, y + 4 + (i // 4), c(RED_L))
        lay.rect(x + 2, y + 7, 4, 1, c(PENCIL))
    lay.line(47, 4, 50, 7, c(INK_B))   # driving direction
    lay.line(50, 7, 47, 7, c(INK_B))
    return lay


def draw_c4_shaft():
    lay = T()
    photo_bg(lay, NAVY_L, NIGHT, seed_of('c4sh_bg'))
    lay.rect(0, 25, 54, 5, c(SNOW[2]))
    lay.rect(0, 25, 54, 1, c(SNOW[4]))
    lay.rect(18, 2, 18, 23, c(PAPER_M))   # the advertising column with posters
    lay.rect(17, 1, 20, 2, c(STEEL[2]))
    lay.rect(19, 4, 7, 9, c(RED_D))
    lay.rect(27, 4, 8, 6, c(AMBER))
    lay.rect(27, 11, 8, 6, c(STEEL[3]))
    lay.rect(19, 14, 7, 6, c(PAPER_L))
    lay.rect(18, 2, 1, 23, c(PAPER_D1))
    lay.rect(35, 2, 1, 23, c(PAPER_D))
    lay.rect(22, 21, 10, 3, c(LEAD[0]))   # the grille at its foot, warm air rising into the frost
    for x in range(22, 32, 2):
        lay.vline(x, 21, 3, c(LEAD[2]))
    for k, x in enumerate((24, 28, 31)):
        for y in range(10, 20, 2):
            lay.px(x + ((y // 2 + k) % 2), y, c(SNOW[4]))
    lay.rect(29, 15, 5, 7, c(STEEL[1]))   # the steel door behind a torn poster
    lay.px(30, 18, c(LEAD[4]))
    return lay


def card_half(lay, left: bool):
    paper_fill(lay, 0, 0, 54, 30, [PAPER_L, PAPER, PAPER], seed_of('c4card%d' % left), grain=0.15)
    lay.rect(0, 0, 54, 1, c('#FBF7E8'))
    edge = 51 if left else 2
    for y in range(1, 30, 2):   # the perforation where the card was torn in two
        lay.px(edge, y, c(WALL2))


def draw_c4_card_de():
    lay = T()
    card_half(lay, True)
    lay.rect(3, 2, 14, 6, c(RED))   # the red C-17 tab
    text(lay, 4, 3, 'C-17', c(PAPER_L), gap=0)
    text(lay, 32, 3, '0417', c(INK_B), gap=0)
    for r in range(5):
        scribble(lay, 3, 10 + r * 4, 42 - (r % 2) * 9, c(INK_B), seed_of('c4de%d' % r), height=2)
    lay.rect(3, 27, 30, 1, c(RED_L))
    return lay


def draw_c4_card_ru():
    lay = T()
    card_half(lay, False)
    text(lay, 7, 3, '0417', c(INK_B), gap=0)
    for r in range(4):
        scribble(lay, 6, 10 + r * 4, 40 - (r % 2) * 8, c(INK_B), seed_of('c4ru%d' % r), height=2)
    st = c('#5A3C78')   # the violet acceptance stamp
    lay.rect(32, 21, 18, 7, st)
    lay.rect(33, 22, 16, 5, c(PAPER))
    scribble(lay, 34, 23, 14, st, seed_of('c4stamp'), density=0.9, height=2)
    return lay


def draw_c4_stencils():
    lay = T()
    photo_bg(lay, WALL1, WALL0, seed_of('c4st_bg'))
    lay.rect(0, 2, 54, 1, c(COVER[2]))
    for k in range(4):   # worn tin stencils .../41 ... /44
        x = 2 + k * 10
        lay.rect(x, 4, 9, 9, c(LEAD[2]))
        lay.rect(x, 4, 9, 1, c(LEAD[4]))
        text(lay, x + 1, 6, '4' + str(1 + k), c(NIGHT), gap=1)
    lay.rect(42, 4, 10, 9, c(RUST[2]))   # .../45, still wet with red-brown
    lay.rect(42, 4, 10, 1, c(RUST[3]))
    text(lay, 43, 6, '45', c(NIGHT), gap=1)
    lay.px(46, 13, c(RUST[2]))
    lay.px(46, 14, c(RUST[1]))
    lay.rect(18, 18, 14, 10, c(LEAD[1]))   # the paint bucket
    lay.rect(18, 18, 14, 2, c(RUST[2]))
    lay.rect(18, 18, 14, 1, c(RUST[3]))
    lay.rect(17, 17, 16, 1, c(LEAD[3]))
    return lay


def draw_c4_wagon_inside():
    lay = T()
    for x in range(0, 54, 6):   # plank walls
        lay.rect(x, 0, 6, 30, c(COVER[1] if (x // 6) % 2 else COVER[2]))
        lay.vline(x, 0, 30, c(COVER[0]))
    lay.rect(24, 0, 6, 3, c(NIGHT))   # the stove hole in the roof
    lay.rect(25, 1, 4, 1, c(SNOW[1]))
    for y, x0 in ((19, 2), (25, 28)):   # two raw benches
        lay.rect(x0, y, 24, 2, c(COVER[4]))
        lay.rect(x0, y + 2, 24, 1, c(COVER[0]))
    lay.rect(4, 24, 5, 5, c(LEAD[1]))   # a bucket
    lay.rect(4, 24, 5, 1, c(LEAD[3]))
    for r in range(3):   # names scratched into the wall in two scripts
        scribble(lay, 8 + r * 3, 5 + r * 3, 16, c(PAPER_M), seed_of('c4wn%d' % r), density=0.6, height=1)
        scribble(lay, 30, 5 + r * 3, 18 - r * 3, c(PAPER_D), seed_of('c4wr%d' % r), density=0.6, height=1)
    scribble(lay, 30, 15, 14, c(PAPER_L), seed_of('c4w14'), density=0.8, height=1)
    return lay


def draw_c4_drawer_s8():
    lay = T()
    lay.rect(0, 0, 54, 30, c(COVER[1]))
    lay.rect(2, 2, 50, 26, c(COVER[0]))
    for k in range(24):   # card tops from above; the red C-17 flags, and those cards only half as tall
        x = 3 + k * 2
        flagged = k % 4 == 1 or k % 7 == 3
        h = 10 if flagged else 22
        lay.rect(x, 4 + (22 - h), 1, h, c(PAPER if k % 2 else PAPER_M))
        if flagged:
            lay.rect(x, 4 + (22 - h) - 2, 2, 2, c(RED))
    lay.rect(20, 27, 14, 2, c(LEAD[3]))
    return lay


def draw_c4_annex_plan():
    lay = T()
    lay.rect(0, 0, 54, 30, c('#1A1410'))
    lay.rect(2, 2, 50, 26, c(SNOW[3]))
    ink = c(BLUE_INK)
    for k in range(3):   # three blocks hatched in pencil, a shaft under each
        x = 6 + k * 15
        lay.rect(x, 5, 11, 8, c(SNOW[2]))
        for i in range(0, 11, 2):
            lay.line(x + i, 12, x + min(10, i + 4), 5 + max(0, 4 - i // 2), c(PENCIL))
        lay.ellipse(x + 5, 19, 2.6, 2.6, ink)
        lay.ellipse(x + 5, 19, 1.4, 1.4, c(SNOW[3]))
        lay.vline(x + 5, 13, 4, ink)
    lay.rect(36, 23, 14, 4, ink)
    lay.rect(37, 24, 12, 2, c(SNOW[3]))
    for i in range(0, 20):   # a reflection on the glass
        lay.px(8 + i, 26 - i, c(SNOW[4]))
    return lay


def draw_c4_tube_slip():
    lay = T()
    photo_bg(lay, WALL2, WALL1, seed_of('c4tu_bg'))
    lay.rect(3, 9, 22, 12, c(BRASS[2]))   # the brass capsule, felt rings at both ends
    lay.rect(3, 9, 22, 2, c(BRASS[3]))
    lay.rect(3, 19, 22, 2, c(BRASS[1]))
    lay.rect(3, 8, 3, 14, c('#3A3A44'))
    lay.rect(22, 8, 3, 14, c('#3A3A44'))
    lay.rect(24, 6, 28, 18, c(PAPER_L))   # the typed slip coming out of it
    lay.rect(24, 6, 28, 1, c('#FBF7E8'))
    lay.rect(26, 8, 14, 2, c(INK))
    for r in range(3):
        scribble(lay, 26, 12 + r * 3, 22 - r * 4, c(INK_B), seed_of('c4tl%d' % r), height=1)
    return lay


ORIGINAL.update({
    'ev_c4_book_gap': draw_c4_book_gap, 'ev_c4_cut_signatures': draw_c4_cut_signatures,
    'ev_c4_carbon': draw_c4_carbon, 'ev_c4_tunnel_plan': draw_c4_tunnel_plan,
    'ev_c4_fresh_tracks': draw_c4_fresh_tracks, 'ev_c4_notice': draw_c4_notice,
    'ev_c4_route_board': draw_c4_route_board, 'ev_c4_shaft': draw_c4_shaft,
    'ev_c4_card_de': draw_c4_card_de, 'ev_c4_card_ru': draw_c4_card_ru,
    'ev_c4_stencils': draw_c4_stencils, 'ev_c4_wagon_inside': draw_c4_wagon_inside,
    'ev_c4_drawer_s8': draw_c4_drawer_s8, 'ev_c4_annex_plan': draw_c4_annex_plan,
    'ev_c4_tube_slip': draw_c4_tube_slip,
})
CUT_Y.update({'ev_c4_book_gap': 2, 'ev_c4_cut_signatures': 1, 'ev_c4_stencils': 2, 'ev_c4_wagon_inside': 3,
              'ev_c4_notice': 3, 'ev_c4_shaft': 2, 'ev_c4_card_de': 1, 'ev_c4_card_ru': 2, 'ev_c4_tube_slip': 3})


# ----------------------------------------------------------------------------- main
def main():
    os.makedirs(SRC, exist_ok=True)
    with open(os.path.join(SRC, '.gdignore'), 'w', encoding='utf-8') as f:
        f.write('')
    cork_tile('cork', CORK, 'cork')
    cork_tile('cork_hc', CORK_HC, 'cork_hc', granules=False)
    frame_9patch()
    pin('pin_alexei', STEEL[1:])
    pin('pin_konrad', BRASS)
    pin('pin_red', [RED_D2, RED_D, RED, RED_L, '#F0A090'])
    card_9patch('card_paper', [PAPER_L, PAPER, PAPER], PAPER_D1, PAPER_M, '#FBF7E8', 'index card (documents), 9-patch')
    card_9patch('card_photo', ['#F2F0E8', '#E8E6DE', '#E8E6DE'], '#8E8C84', '#CFCDC4', '#FFFFFF', 'photo print (physical clues), 9-patch')
    card_9patch('card_burned', [PAPER, PAPER_M, PAPER_M], PAPER_D2, PAPER_D, PAPER_L, 'scorched card, 9-patch', burned=True)
    simple_9patch('tag', 9, 3, tag_draw, 'masking-tape label for thread captions, 9-patch')
    simple_9patch('note', 24, 8, note_draw, 'typed summary sheet, 9-patch')
    simple_9patch('ghost', 12, 4, ghost_draw, 'reserved place of an item not yet found, 9-patch')
    simple_9patch('focus', 8, 3, focus_draw, 'focus ring around a card, 9-patch')
    simple_9patch('focus_hc', 8, 3, lambda l, s: focus_draw(l, s, outer='#FFF27A', inner='#000000'), 'focus ring, high contrast')
    unknown_marker()
    folder()
    vertical_tabs()
    doc_thumbs()
    original_thumbs()
    pg.write_manifest(os.path.join(OUT, 'manifest.json'), {
        'generator': 'tools/pixelgen/gen_ui_board.py', 'scale': SCALE, 'thumb_1x': list(THUMB),
        'files': MANIFEST})
    print('wrote', len(MANIFEST), 'textures to', rel(OUT))


if __name__ == '__main__':
    main()
