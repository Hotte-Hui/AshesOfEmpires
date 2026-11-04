"""gen_ui_explore -- original pixel-art UI kit for the exploration layer of ASHES OF EMPIRES (round 2).

Owner: explore-system. Draws every texture at 1:1 (one art pixel = one world pixel) and writes
  * assets/ui/explore/src_1x/<name>.png        1:1 sources (folder has .gdignore, never imported)
  * assets/ui/explore/frames/<name>.png        x3 nearest 9-patch frames (StyleBoxTexture cannot scale)
  * assets/ui/explore/icons/<name>.png         x3 icons and markers
  * assets/ui/explore/manifest.json            what was written (size at 1:1, scale, 9-patch margins)
  * tests/visual/explore_ui_mock_closeup.png   1:1 demo close-up for the UI harness (mock data, not shipped
                                               content; real close-ups come from the content owners)
Style law: documentation/ART_DIRECTION.md and the round-1 UI kit (tools/pixelgen/gen_ui.py, read only):
warm paper + ink for the protagonists' notebooks (in-world fiction), a cool, sober archive card (karsk snow
ramp, slate band, no emblem of any kind) for the real-history pages, so the two can never be confused.
All colours come from pg.PALETTES / the UI palette. Shapes are procedural; nothing is traced or sampled.
Deterministic: seeds are crc32 of the asset names; no wall clock, no hash().

Run:  py -3 -P tools/pixelgen/gen_ui_explore.py
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
OUT = os.path.join(ROOT, 'assets', 'ui', 'explore')
SRC = os.path.join(OUT, 'src_1x')
MOCK = os.path.join(ROOT, 'tests', 'visual', 'explore_ui_mock_closeup.png')

hx = pg.hx
CLEAR = np.array([0, 0, 0, 0], np.uint8)

# ----------------------------------------------------------------------------- palette (UI kit + pg ramps)
NIGHT, NIGHT1, NAVY, NAVY_L = '#04090D', '#06151D', '#0B1C24', '#14272B'
WALL0, WALL1, WALL2, WALL3, WALL4 = '#1A2A2E', '#24373A', '#354448', '#4A5A5B', '#62716E'
COPPER_D, COPPER, COPPER_L, AMBER, AMBER_L = '#7A3E26', '#BA775B', '#DCA16E', '#F0C487', '#FBE3AE'
PAPER_D2, PAPER_D1, PAPER_D, PAPER_M, PAPER, PAPER_L = '#6E6A5C', '#8E8A78', '#B0AA93', '#CEC6AA', '#E6DEC2', '#F5EFDA'
INK, INK_B, RED_D, RED = '#1A1C2A', '#2E3248', '#7A2A26', '#A8382E'
TEXT_DIM = '#A3ACA2'
COVER = ['#2A1B16', '#3D2820', '#55372A', '#6E4A37']          # archive wood ramp (notebook cover)
SNOW = ['#7E8E8C', '#A3B1AD', '#C4CFC8', '#DEE5DC', '#F1F4EC']  # karsk snow ramp (cool archive paper)
BLUE = ['#1D2A3A', '#2B3C50', '#3E546B', '#58718A', '#7A93A8', '#A7BCCB']  # archive blue ramp (ink)

MANIFEST: list[dict] = []


def c(h, a=255):
    return hx(h, a)


def seed_of(name: str) -> int:
    return zlib.crc32(name.encode('utf-8')) & 0x7FFFFFFF


def L(w, h):
    return pg.Layer(w, h)


def save(layer_or_arr, name, group='frames', scale=3, note='', margins=None):
    """Writes the 1:1 source and the x3 runtime texture. margins = 9-patch margins at 1:1 (l, t, r, b)."""
    arr = layer_or_arr.c if isinstance(layer_or_arr, pg.Layer) else layer_or_arr
    img = Image.fromarray(arr, 'RGBA')
    os.makedirs(SRC, exist_ok=True)
    img.save(os.path.join(SRC, name + '.png'))
    d = os.path.join(OUT, group)
    os.makedirs(d, exist_ok=True)
    out = img if scale == 1 else img.resize((img.width * scale, img.height * scale), Image.NEAREST)
    out.save(os.path.join(d, name + '.png'))
    rel = 'assets/ui/explore/%s/%s.png' % (group, name)
    e = {'path': rel, 'size_1x': [img.width, img.height], 'scale': scale, 'note': note}
    if margins:
        e['margins_1x'] = list(margins)
    MANIFEST.append(e)
    return rel


def orphan_check(arr: np.ndarray, name: str) -> int:
    """Counts opaque pixels whose 4 neighbours are all transparent (stray pixels). Must be 0 for frames."""
    a = arr[..., 3] > 0
    p = np.pad(a, 1)
    nb = p[:-2, 1:-1] | p[2:, 1:-1] | p[1:-1, :-2] | p[1:-1, 2:]
    n = int((a & ~nb).sum())
    if n:
        print('  note: %s has %d isolated pixel(s)' % (name, n))
    return n


# ============================================================================ frames (9-patch)
def frame_notebook():
    """Notebook page of the protagonists: warm paper, sewn gutter at the left (thread every 6 px, tiles),
    cover board peeking out behind the page, dog-eared bottom-right corner, 1 px drop shadow that follows
    the page silhouette. Margins L10 T6 R7 B8; the middle (14 x 12) is plain paper; TILE vertically."""
    w, h = 31, 26
    l = L(w, h)
    px0, pw, ph = 2, w - 3, h - 2                        # page: x [2, 29], y [0, 23]
    cx, cy = px0 + pw - 1, ph - 1                        # bottom-right page pixel
    k = 5                                                # dog-ear size (stays inside the 7x8 corner region)
    page = np.zeros((h, w), bool)
    page[0:ph, px0:px0 + pw] = True
    page[0, cx] = False                                  # rounded top-right
    yy, xx = np.mgrid[0:h, 0:w]
    s = (cx - xx) + (cy - yy)
    page &= ~((s < k) & (xx <= cx) & (yy <= cy))          # corner folded away
    cover = np.zeros((h, w), bool)
    cover[0:ph + 1, 0:2] = True                          # board behind the page, 1 px longer
    cover[0, 0] = False
    solid = page | cover
    sh = np.zeros_like(solid)
    sh[1:, 1:] = solid[:-1, :-1]
    l.c[sh & ~solid] = c('#000000', 90)
    l.c[cover & (xx == 0)] = c(COVER[0])
    l.c[cover & (xx == 1)] = c(COVER[1])
    l.px(1, 0, c(COVER[0])); l.px(1, ph, c(COVER[0]))
    l.c[page] = c(PAPER)
    top = page & (yy == 0)
    l.c[top] = c(PAPER_D)
    l.c[page & (yy == 1) & (xx > px0) & (xx < cx)] = c(PAPER_L)   # catch light under the edge
    l.c[page & (xx == cx)] = c(PAPER_D)
    l.c[page & (yy == cy)] = c(PAPER_D1)
    # gutter: fold line, shadow band, dithered falloff (columns only -> tiles vertically)
    l.c[page & (xx == px0)] = c(PAPER_D1)
    l.c[page & (xx == px0 + 1) & (yy > 0) & (yy < cy)] = c(PAPER_M)
    thr = pg.bayer(w, h)
    l.c[page & (xx == px0 + 2) & (yy > 0) & (yy < cy) & (thr < 0.5)] = c(PAPER_M)
    l.c[page & (xx == px0 + 3) & (yy > 0) & (yy < cy) & (thr < 0.25)] = c(PAPER_M)
    # thread stitches in the fold (period 6: rows 2,3 / 8,9 / 14,15 / 20,21)
    for y in range(1, cy):
        if y % 6 in (2, 3):
            l.px(px0 + 1, y, c(PAPER_D2))
        elif y % 6 == 4:
            l.px(px0 + 1, y, c(PAPER_D))
    # dog-ear flap: the folded corner lies on the page as a triangle (back of the sheet, a shade darker)
    flap = (xx >= cx - k) & (yy >= cy - k) & (s >= k) & (s <= 2 * k) & (xx <= cx) & (yy <= cy)
    flap &= (xx - (cx - k)) + (yy - (cy - k)) <= k
    l.c[flap] = c(PAPER_M)
    l.c[flap & ((xx == cx - k) | (yy == cy - k))] = c(PAPER_D)    # flap edges
    l.c[flap & (s == k)] = c(PAPER_D1)                            # crease
    # (no cast shadow outside the flap: it would leak into the tiled/stretched edge regions of the 9-patch)
    assert not (flap & ((xx < w - 7) | (yy < h - 8))).any(), 'dog-ear must stay inside the corner region'
    # a little edge wear (fixed corner regions only)
    for (x, y) in [(cx - 2, 0), (cx - 3, 0), (px0 + 5, cy)]:
        l.px(x, y, c(PAPER_M))
    orphan_check(l.c, 'notebook')
    return save(l, 'notebook', note='9-patch L10 T6 R7 B8 (x3: 30/18/21/24); vertical axis TILE (period 6)',
                margins=(10, 6, 7, 8))


def frame_archive_card():
    """Real-history card: cool archive paper (karsk snow ramp), slate title band, hairline frame, shadow.
    Deliberately plain: no emblem, no stamp, no seal. Margins L8 T16 R8 B8 (band = rows 1..12)."""
    w, h = 24, 32
    l = L(w, h)
    l.rect(1, 1, w - 1, h - 1, c('#000000', 100))      # shadow
    cw, ch = w - 1, h - 1
    l.rect(0, 0, cw, ch, c(SNOW[3]))
    # band
    l.rect(1, 1, cw - 2, 12, c(WALL1))
    l.rect(1, 13, cw - 2, 1, c(WALL3))
    l.rect(1, 14, cw - 2, 1, c(SNOW[4]))
    # left highlight / right shade inside the frame (columns only -> stretches cleanly)
    l.rect(1, 15, 1, ch - 17, c(SNOW[4]))
    l.rect(cw - 2, 15, 1, ch - 17, c(SNOW[2]))
    l.rect(2, ch - 2, cw - 4, 1, c(SNOW[2]))
    # hairline frame
    for x in range(cw):
        l.px(x, 0, c(SNOW[0])); l.px(x, ch - 1, c(SNOW[0]))
    for y in range(ch):
        l.px(0, y, c(SNOW[0])); l.px(cw - 1, y, c(SNOW[0]))
    for (x, y) in [(0, 0), (cw - 1, 0), (0, ch - 1), (cw - 1, ch - 1)]:
        l.c[y, x] = CLEAR
    orphan_check(l.c, 'archive_card')
    return save(l, 'archive_card', note='9-patch L8 T16 R8 B8 (x3: 24/48/24/24); band rows 1..12 (x3: y 3..39)',
                margins=(8, 16, 8, 8))


def frame_archive_card_hc():
    """High-contrast variant: white paper, black frame and band edge."""
    w, h = 24, 32
    l = L(w, h)
    l.rect(1, 1, w - 1, h - 1, c('#000000', 160))
    cw, ch = w - 1, h - 1
    l.rect(0, 0, cw, ch, c(SNOW[4]))
    l.rect(1, 1, cw - 2, 12, c(NIGHT1))
    l.rect(1, 13, cw - 2, 1, c('#000000'))
    for x in range(cw):
        l.px(x, 0, c('#000000')); l.px(x, ch - 1, c('#000000'))
    for y in range(ch):
        l.px(0, y, c('#000000')); l.px(cw - 1, y, c('#000000'))
    for (x, y) in [(0, 0), (cw - 1, 0), (0, ch - 1), (cw - 1, ch - 1)]:
        l.c[y, x] = CLEAR
    return save(l, 'archive_card_hc', note='high-contrast variant of archive_card', margins=(8, 16, 8, 8))


def frame_photo_mount():
    """Deckle-edged photo print (typical European prints of the 1950s/60s): white border with a scalloped
    edge (period 4 px; edge regions TILE seamlessly), hairline around the picture, soft 1 px shadow.
    Margins L7 T7 R7 B8 (the picture fills the content rect exactly)."""
    w, h = 22, 23
    l = L(w, h)
    pw, ph = w - 1, h - 1                                # print area (shadow at +1/+1)
    m = np.zeros((h, w), bool)
    m[0:ph, 0:pw] = True
    for x in range(pw):
        if x % 4 == 3:
            m[0, x] = False
        if x % 4 == 1:
            m[ph - 1, x] = False
    for y in range(ph):
        if y % 4 == 3:
            m[y, 0] = False
        if y % 4 == 1:
            m[y, pw - 1] = False
    for (x, y) in [(0, 0), (pw - 1, 0), (0, ph - 1), (pw - 1, ph - 1)]:
        m[y, x] = False
    sh = np.zeros_like(m)
    sh[1:, 1:] = m[:-1, :-1]
    l.c[sh & ~m] = c('#000000', 110)
    l.c[m] = c(PAPER_L)
    # aged rim: one px inside the deckle in the darker paper tone, dithered
    thr = pg.bayer(w, h)
    p = np.pad(m, 1)
    edge = m & ~(p[:-2, 1:-1] & p[2:, 1:-1] & p[1:-1, :-2] & p[1:-1, 2:])
    rim = np.zeros_like(m)
    rim[1:-1, 1:-1] = m[1:-1, 1:-1] & ~edge[1:-1, 1:-1] & (
        edge[:-2, 1:-1] | edge[2:, 1:-1] | edge[1:-1, :-2] | edge[1:-1, 2:])
    l.c[edge] = c(PAPER)
    l.c[rim & (thr < 0.5)] = c(PAPER)
    # hairline around the picture (content rect = [7, 15) x [7, 15) at 1:1)
    for x in range(6, 16):
        l.px(x, 6, c(PAPER_D)); l.px(x, 15, c(PAPER_D))
    for y in range(6, 16):
        l.px(6, y, c(PAPER_D)); l.px(15, y, c(PAPER_D))
    l.rect(7, 7, 8, 8, c(WALL1))                         # centre (hidden behind the picture)
    orphan_check(l.c, 'photo_mount')
    return save(l, 'photo_mount', note='9-patch L7 T7 R7 B8 (x3: 21/21/21/24); both axes TILE (period 4 px)',
                margins=(7, 7, 7, 8))


def tape(name: str, angle_deg: float):
    """Translucent paper tape strip, pre-rotated at 1:1 with torn ends (holds the photo in the notebook)."""
    w, h = 22, 12
    l = L(w, h)
    a = math.radians(angle_deg)
    cx, cy = w / 2, h / 2
    yy, xx = np.mgrid[0:h, 0:w]
    dx, dy = xx + 0.5 - cx, yy + 0.5 - cy
    u = dx * math.cos(a) + dy * math.sin(a)
    v = -dx * math.sin(a) + dy * math.cos(a)
    rng = np.random.default_rng(seed_of(name))
    tear = rng.integers(0, 2, size=16)                   # torn ends: +-1 px jitter per row band
    vi = np.clip(np.floor(v + 8).astype(int), 0, 15)
    half_len = 8.6 + tear[vi] * 0.9
    body = (np.abs(u) <= half_len) & (np.abs(v) <= 2.6)
    top = body & (v < -1.6)
    bot = body & (v > 1.6)
    l.c[body] = c(PAPER_M, 178)
    l.c[top] = c(PAPER_L, 200)
    l.c[bot] = c(PAPER_D, 185)
    # remove single stray pixels at the torn ends
    l.clean_orphans(1)
    a_ = l.c[..., 3] > 0
    p = np.pad(a_, 1)
    lonely = a_ & ~(p[:-2, 1:-1] | p[2:, 1:-1] | p[1:-1, :-2] | p[1:-1, 2:])
    l.c[lonely] = CLEAR
    return save(l, name, group='icons', note='tape strip, %.0f deg, translucent' % angle_deg)


def bar(name: str, fill, top, edge):
    """Progress bar parts on paper (9-patch margin 2)."""
    w, h = 7, 5
    l = L(w, h)
    l.rect(0, 0, w, h, c(fill))
    l.rect(1, 1, w - 2, 1, c(top))
    for x in range(w):
        l.px(x, 0, c(edge)); l.px(x, h - 1, c(edge))
    for y in range(h):
        l.px(0, y, c(edge)); l.px(w - 1, y, c(edge))
    for (x, y) in [(0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1)]:
        l.c[y, x] = CLEAR
    return save(l, name, note='9-patch margin 2', margins=(2, 2, 2, 2))


# ============================================================================ icons (13 x 13 at 1:1)
def _magnifier(l, ring_col, glass_col, glint_col, handle_cols, ferrule_col):
    for y in range(13):
        for x in range(13):
            d = math.hypot(x + 0.5 - 5.5, y + 0.5 - 5.5)
            if 2.55 <= d <= 3.75:
                l.px(x, y, c(ring_col))
            elif d < 2.55 and glass_col is not None:
                l.px(x, y, c(glass_col))
    if glint_col is not None:
        l.px(4, 4, c(glint_col)); l.px(4, 5, c(glint_col)); l.px(5, 4, c(glint_col))
    hd, hl = handle_cols
    for i in range(4):
        l.px(8 + i, 9 + i, c(hd)); l.px(9 + i, 8 + i, c(hl)); l.px(9 + i, 9 + i, c(hd))
    l.px(8, 8, c(ferrule_col))


def icons():
    # discovery (HUD toast on the navy plate): magnifying glass over the plate, copper rim, teal glass
    l = L(13, 13)
    _magnifier(l, COPPER_L, '#26403F', AMBER_L, (PAPER_D1, PAPER_M), COPPER)
    save(l, 'icon_discovery', group='icons')
    # history (HUD toast / journal tab): neutral stack of archive index cards, greys only
    l = L(13, 13)
    l.rect(4, 1, 8, 7, c(SNOW[1]))
    for x in range(4, 12):
        l.px(x, 1, c(SNOW[0]))
    for y in range(1, 8):
        l.px(4, y, c(SNOW[0])); l.px(11, y, c(SNOW[0]))
    l.rect(1, 4, 10, 8, c(SNOW[3]))
    for x in range(1, 11):
        l.px(x, 4, c(SNOW[0])); l.px(x, 11, c(SNOW[0]))
    for y in range(4, 12):
        l.px(1, y, c(SNOW[0])); l.px(10, y, c(SNOW[0]))
    l.rect(2, 3, 3, 1, c(SNOW[0]))
    for k, ln in enumerate([6, 5, 4]):
        l.rect(3, 6 + 2 * k, ln, 1, c(WALL3))
    save(l, 'icon_history', group='icons')

    # ---- ink icons for lists on paper (journal) and the notebook kicker
    l = L(13, 13)
    _magnifier(l, INK_B, None, None, (INK, INK_B), RED)
    l.px(5, 5, c(RED))
    save(l, 'kind_detail', group='icons')
    # secret: brick wall with one brick pulled out (dark gap)
    l = L(13, 13)
    for y in (1, 5, 9):
        l.rect(1, y, 11, 1, c(INK_B))
    l.rect(1, 12, 11, 1, c(INK_B))
    for (x, y0) in [(6, 2), (3, 6), (9, 6), (6, 10)]:
        l.rect(x, y0, 1, 3, c(INK_B))
    l.rect(1, 1, 1, 12, c(INK_B)); l.rect(11, 1, 1, 12, c(INK_B))
    l.rect(4, 6, 5, 3, c(INK))                           # the gap
    l.px(5, 7, c(RED))                                   # something hidden inside
    save(l, 'kind_secret', group='icons')
    # curiosity / easter egg: six-point asterisk star
    l = L(13, 13)
    for i in range(-5, 6):
        l.px(6 + i, 6, c(INK_B)) if abs(i) > 1 else None
        l.px(6, 6 + i, c(INK_B)) if abs(i) > 1 else None
    for i in range(-4, 5):
        if abs(i) > 1:
            l.px(6 + i, 6 + i, c(INK_B)); l.px(6 + i, 6 - i, c(INK_B))
    l.rect(5, 5, 3, 3, c(RED))
    l.px(6, 6, c(RED_D))
    save(l, 'kind_easter_egg', group='icons')
    # chat: speech bubble with three dots
    l = L(13, 13)
    for x in range(2, 11):
        l.px(x, 1, c(INK_B)); l.px(x, 8, c(INK_B))
    for y in range(2, 8):
        l.px(1, y, c(INK_B)); l.px(11, y, c(INK_B))
    l.px(3, 9, c(INK_B)); l.px(3, 10, c(INK_B)); l.px(2, 11, c(INK_B)); l.px(4, 9, c(INK_B))
    for x in (4, 6, 8):
        l.px(x, 4, c(RED_D)); l.px(x, 5, c(RED_D))
    save(l, 'kind_chat', group='icons')
    # history (ink, on paper): index card with lines, neutral (no red)
    l = L(13, 13)
    for x in range(1, 12):
        l.px(x, 2, c(INK_B)); l.px(x, 10, c(INK_B))
    for y in range(2, 11):
        l.px(1, y, c(INK_B)); l.px(11, y, c(INK_B))
    l.rect(1, 4, 11, 1, c(INK_B))
    for k, ln in enumerate([7, 5]):
        l.rect(3, 6 + 2 * k, ln, 1, c(PAPER_D2))
    l.rect(2, 3, 2, 1, c(INK_B))
    save(l, 'kind_history', group='icons')

    # ---- prompt markers (on the navy prompt plate)
    # not yet discovered: a small four-point twinkle (diamond core, long thin tips) -- never a "+"
    l = L(9, 9)
    star = ['....a....',
            '....a....',
            '...aLa...',
            '..aLLLa..',
            'aaLLWLLaa',
            '..aLLLa..',
            '...aLa...',
            '....a....',
            '....a....']
    pal_ = {'a': COPPER_L, 'L': AMBER, 'W': AMBER_L}
    for y, row in enumerate(star):
        for x, ch in enumerate(row):
            if ch in pal_:
                l.px(x, y, c(pal_[ch]))
    save(l, 'mark_new', group='icons', note='prompt marker: not yet discovered (9x9 twinkle)')
    l = L(7, 7)
    for (x, y) in [(0, 3), (1, 4), (2, 5), (3, 4), (4, 3), (5, 2), (6, 1)]:
        l.px(x, y, c(TEXT_DIM))
    for (x, y) in [(1, 3), (2, 4), (3, 3), (4, 2), (5, 1)]:
        l.px(x, y, c(WALL4))
    save(l, 'mark_seen', group='icons', note='prompt marker: already discovered')
    # ---- page indicator (5 x 5) on the dark backdrop
    for name, on in [('page_on', True), ('page_off', False)]:
        l = L(5, 5)
        for y in range(5):
            r = 2 - abs(2 - y)
            for x in range(2 - r, 3 + r):
                edge = x in (2 - r, 2 + r)
                if on:
                    l.px(x, y, c(COPPER_L) if edge else c(AMBER))
                elif edge:
                    l.px(x, y, c(WALL4))
        save(l, name, group='icons')
    # neutral page indicator for the history pages (greys only)
    l = L(5, 5)
    for y in range(5):
        r = 2 - abs(2 - y)
        for x in range(2 - r, 3 + r):
            l.px(x, y, c(SNOW[3]) if x in (2 - r, 2 + r) else c(SNOW[4]))
    save(l, 'page_on_neutral', group='icons')
    # "more text below" chevron for scrolling pages (ink grey, on paper)
    l = L(7, 4)
    for i in range(4):
        l.px(i, i, c(WALL3)); l.px(6 - i, i, c(WALL3))
        if i < 3:
            l.px(i + 1, i, c(WALL4)); l.px(5 - i, i, c(WALL4))
    save(l, 'more_down', group='icons')


# ============================================================================ demo close-up (harness only)
def mock_closeup():
    """240 x 150 demo close-up for tests/visual (tea glass in a metal holder on a newspaper by a frosted
    window, warm lamp from the right). Mock content to judge the DiscoveryView layout -- not game content."""
    P = pg.PALETTES['karsk']
    A = pg.PALETTES['archive']
    w, h = 240, 150
    l = L(w, h)
    rng = np.random.default_rng(seed_of('mock_closeup'))
    # wall: dark teal with a warm falloff toward the lamp (right)
    l.vgrad(0, 0, w, 96, [c(P['night'][2]), c(P['teal'][0]), c(P['teal'][1])])
    for y in range(96):          # lamp glow on the wall (off-frame lamp, top right), ordered dither
        for x in range(110, w):
            d = math.hypot((x - 246) / 120.0, (y - 4) / 80.0)
            if d < 1:
                t = (1 - d) * 0.75
                if pg.BAYER4[y % 4, x % 4] < t:
                    l.px(x, y, c(A['wood'][1] if t < 0.45 else A['amber'][0]))
    # window (left): frame + frosted panes, night outside
    fx0, fy0, fw, fh = 14, 8, 92, 80
    l.rect(fx0, fy0, fw, fh, c(A['wood'][1]))
    l.rect(fx0 + 1, fy0 + 1, fw - 2, 1, c(A['wood'][3]))
    panes = [(fx0 + 5, fy0 + 5, 39, 32), (fx0 + 48, fy0 + 5, 39, 32), (fx0 + 5, fy0 + 41, 39, 34), (fx0 + 48, fy0 + 41, 39, 34)]
    frost = pg.value_noise(w, h, 7, seed_of('frost'), octaves=3)
    for (x0, y0, pw_, ph_) in panes:
        l.vgrad(x0, y0, pw_, ph_, [c(P['night'][1]), c(P['night'][3]), c(P['teal'][1])])
        for y in range(y0, y0 + ph_):
            for x in range(x0, x0 + pw_):
                # frost creeps in from the pane edges (ferns)
                e = min(x - x0, x0 + pw_ - 1 - x, y - y0, y0 + ph_ - 1 - y)
                f = frost[y, x] - e / 14.0
                if f > 0.42:
                    l.px(x, y, c(P['snow'][2] if f > 0.6 else P['snow'][0]))
                elif f > 0.36 and pg.BAYER4[y % 4, x % 4] < 0.5:
                    l.px(x, y, c(P['snow'][0]))
        l.rect(x0, y0, pw_, 1, c(A['wood'][0]))
        l.rect(x0, y0, 1, ph_, c(A['wood'][0]))
    l.rect(fx0, fy0 + fh - 3, fw + 4, 3, c(A['wood'][2]))     # sill
    l.rect(fx0, fy0 + fh - 3, fw + 4, 1, c(A['wood'][4]))
    # table
    l.vgrad(0, 92, w, 58, [c(A['wood'][2]), c(A['wood'][1]), c(A['wood'][0])])
    l.rect(0, 92, w, 1, c(A['wood'][4]))
    for y in (104, 119, 137):
        l.rect(0, y, w, 1, c(A['wood'][0]))
    grain = pg.value_noise(w, 58, 5, seed_of('grain'), octaves=2)
    for y in range(93, h):
        for x in range(w):
            if grain[y - 92, x] > 0.68 and (x + y) % 3 == 0:
                l.px(x, y, c(A['wood'][3]))
    # newspaper (left front), slightly skewed sheet with headline blocks and text rows
    sheet = [(22, 104), (128, 99), (136, 147), (16, 150)]
    l.poly(sheet, c(A['paper'][3]))
    m, mx0, my0 = l.poly_mask(sheet)
    shade = np.zeros((h + 8, w + 8), bool)
    shade[my0:my0 + m.shape[0], mx0:mx0 + m.shape[1]] = m
    shade = shade[:h, :w]
    for y in range(h):
        for x in range(w):
            if shade[y, x] and (x - 20) * 0.05 + (y - 100) * 0.02 > 3.2 and pg.BAYER4[y % 4, x % 4] < 0.5:
                l.px(x, y, c(A['paper'][2]))
    for k in range(4):
        y = 108 + k * 9
        x0 = 28 + int(k * 0.45)
        l.rect(x0, y, 40 + (k % 2) * 18, 3 if k == 0 else 1, c(A['ink'][0] if k == 0 else A['paper'][1]))
        if k:
            l.rect(x0 + 62, y + 1, 30, 1, c(A['paper'][1]))
    for y in range(124, 146, 3):
        l.rect(30, y, 44, 1, c(A['paper'][2])); l.rect(80, y - 1, 44, 1, c(A['paper'][2]))
    l.rect(30, 107, 18, 1, c(A['ink'][2]))                  # red rule under the masthead
    # glass holder (podstakannik) + tea glass, centre x 160
    gx, gy, gw, gh = 148, 50, 26, 52
    # glass (tea inside)
    for y in range(gy, gy + 26):
        for x in range(gx + 2, gx + gw - 2):
            t = (x - gx) / gw
            col = A['amber'][1] if t < 0.25 else (A['amber'][2] if t < 0.7 else A['amber'][3])
            l.px(x, y, c(col))
    l.rect(gx + 2, gy, gw - 4, 2, c(P['snow'][3]))         # meniscus / rim
    l.rect(gx + gw - 6, gy + 3, 2, 18, c(A['amber'][5]))    # lamp glint on the glass
    l.rect(gx + 4, gy + 3, 1, 14, c(P['snow'][1]))          # window rim light
    # metal holder: steel greys, filigree windows, copper highlights from the lamp
    hy = gy + 14
    for y in range(hy, gy + gh):
        widen = 0 if y < gy + gh - 6 else (y - (gy + gh - 6))
        for x in range(gx - widen, gx + gw + widen):
            t = (x - gx + widen) / (gw + 2 * widen)
            col = P['stone'][1] if t < 0.2 else (P['stone'][3] if t < 0.6 else (P['stone'][4] if t < 0.85 else A['amber'][3]))
            l.px(x, y, c(col))
    for y in range(hy + 5, gy + gh - 9, 6):
        for x in range(gx + 4, gx + gw - 4, 5):
            l.rect(x, y, 2, 3, c(A['amber'][1]))            # tea seen through the filigree
            l.px(x, y, c(P['stone'][0]))
    l.rect(gx - 1, hy, gw + 2, 2, c(P['stone'][5]))         # rim of the holder
    l.rect(gx - 4, gy + gh - 1, gw + 8, 2, c(P['stone'][1]))
    # handle (right)
    for y in range(hy + 3, hy + 26):
        dx = int(round(5 * math.sin((y - hy - 3) / 23 * math.pi)))
        l.px(gx + gw + 1 + dx, y, c(P['stone'][4])); l.px(gx + gw + 2 + dx, y, c(A['amber'][3]))
    # spoon
    l.line(gx + 18, gy - 12, gx + 14, gy + 10, c(P['snow'][1]))
    l.line(gx + 19, gy - 12, gx + 15, gy + 10, c(P['stone'][4]))
    # saucer shadow on the table
    l.rect(gx - 8, gy + gh + 1, gw + 18, 2, c(A['wood'][0]))
    # sugar cubes
    for (sx, sy) in [(196, 106), (206, 109)]:
        l.rect(sx, sy, 7, 6, c(P['snow'][3])); l.rect(sx, sy, 7, 1, c(P['snow'][4]))
        l.rect(sx + 6, sy, 1, 6, c(P['snow'][1])); l.rect(sx, sy + 6, 8, 1, c(A['wood'][0]))
    # steam wisps above the glass (dithered)
    for i, x0 in enumerate([gx + 8, gx + 15]):
        for y in range(gy - 30, gy - 2):
            k = (gy - 2 - y) / 28
            x = int(round(x0 + 3 * math.sin(y / 5.0 + i * 2.1) * k))
            if pg.BAYER4[y % 4, x % 4] < 0.85 - k * 0.6:
                l.px(x, y, c(P['snow'][2] if k < 0.5 else P['snow'][1]))
    # lamp light pool on the table (warm dither, right)
    for y in range(94, h):
        for x in range(150, w):
            d = math.hypot((x - 205) / 60.0, (y - 112) / 22.0)
            if d < 1 and pg.BAYER4[y % 4, x % 4] < (1 - d) * 0.55:
                cur = tuple(l.c[y, x][:3])
                if cur == tuple(c(A['wood'][1])[:3]) or cur == tuple(c(A['wood'][2])[:3]):
                    l.px(x, y, c(A['wood'][3]))
    Image.fromarray(l.c, 'RGBA').save(MOCK)
    MANIFEST.append({'path': 'tests/visual/explore_ui_mock_closeup.png', 'size_1x': [w, h], 'scale': 1,
                     'note': 'harness mock close-up (shown x3 by the DiscoveryView preview)'})


def contact_sheet():
    """x3 overview of every runtime texture (scratch preview, written next to the sources)."""
    files = [e for e in MANIFEST if e['path'].startswith('assets/ui/explore/')]
    ims = [Image.open(os.path.join(ROOT, e['path'])) for e in files]
    W = 1200
    x = y = 12
    rowh = 0
    pos = []
    for im in ims:
        if x + im.width > W - 12:
            x, y = 12, y + rowh + 12
            rowh = 0
        pos.append((x, y))
        x += im.width + 12
        rowh = max(rowh, im.height)
    sheet = Image.new('RGBA', (W, y + rowh + 12), (12, 20, 26, 255))
    for im, p in zip(ims, pos):
        sheet.alpha_composite(im.convert('RGBA'), p)
    sheet.save(os.path.join(SRC, '_contact_sheet.png'))


def main():
    os.makedirs(SRC, exist_ok=True)
    open(os.path.join(SRC, '.gdignore'), 'a').close()
    frame_notebook()
    frame_archive_card()
    frame_archive_card_hc()
    frame_photo_mount()
    bar('bar_track', PAPER_M, PAPER_D, PAPER_D1)
    bar('bar_fill', BLUE[1], BLUE[2], BLUE[0])
    bar('bar_fill_neutral', WALL3, WALL4, WALL1)
    tape('tape_l', -16.0)
    tape('tape_r', 14.0)
    icons()
    mock_closeup()
    contact_sheet()
    with open(os.path.join(OUT, 'manifest.json'), 'w', encoding='utf-8') as f:
        json.dump(MANIFEST, f, indent=1)
    print('gen_ui_explore: wrote %d textures' % len(MANIFEST))


if __name__ == '__main__':
    main()
