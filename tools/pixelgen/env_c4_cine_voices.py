"""env_c4_cine_voices -- art of LS_C4_Voices, the closing of Chapter 4 part 1 (owner: cine stream).

  v1  Berlin morning: Konrad climbs out of the service door of the advertising column S 2 -- the loop of the
      level re-baked for the morning with the poster torn back (env_c4_cine_levelplates.loop_layers('morning')),
      the steel door standing open over it (v1_door), the Lindner file under his coat or empty-handed
  v2  Marta's tram (the level's car 3518, env_c4_cine_levelplates.tram_sheets) leaves the loop, Ilse at the last
      window; Konrad from behind in the foreground (portrait pipeline, env_c4_cine_figs) -- one bell, or two bells
      and he raises his hand (and Ilse her red mitten on the glass)
  v3  Karsk: Alexei and Lev climb out of the cellar stair into the yard under the green signal (the layered yard,
      env_c4_cine_yard) -> insert: Alexei's squared notebook page with the four numbers of the one wagon
  v4  the siding of L_C4_TunnelsB: wagon C-17/45 alone under its work lamp; the lamp goes out (lit / dark plates)
  v5  black; the caption
Runtime: scenes/cinematics/ch4_voices/ch4_voices.gd (anchors in layout.json "voices").
"""
from __future__ import annotations

import numpy as np

import env_c4_cine_kit as Q
import pg
from env_c4_cine_kit import (C, VW, VH, KNIGHT, AMBER, IRONK, box, ell, poly)

L = Q.LAYOUT.setdefault('voices', {})

V1_OFF = -206                          # plate offset of v1: the column S 2 right of centre (level camera 206)
V2_OFF = -150                          # plate offset of v2 at its start (the camera then follows the tram)
NUMBERS = ['24 318', 'C-17/42', '47 702', 'C-17/45']   # the puzzle's order (C4_DESIGN §2.7): one wagon


def _door():
    import env_c4_cine_places as P
    return P._loop_anchors()['loop_door'], P._loop_anchors()['loop_w']


def v1_door():
    """The column's steel door standing open: the dark inside with the top rung of the shaft ladder and the warm
    air from the grate below, the leaf swung out to the right on its hinges (plate coordinates)."""
    (d0, dy0, d1, dy1), w = _door()
    R = Q.ramps(K=IRONK, A=AMBER, T=['#1A1C20', '#2C3036', '#40464E', '#5A626A', '#7A828A', '#A2AAB0'])
    p = C.Paint(w, VH, R, 'v1door')
    yy, xx = p.yy, p.xx
    inside = box(d0, dy0, d1, dy1, w)
    p.put(inside, 'K', 0.4 + (yy[inside] - dy0) / (dy1 - dy0) * 0.6)
    p.put(box(d0 + 1, dy1 - 8, d1 - 1, dy1, w), 'A', 1.4)
    for ry in (dy0 + 30, dy0 + 42):                                             # the ladder's top rungs
        p.put(box(d0 + 3, ry, d1 - 3, ry + 1, w), 'T', 1.6)
    p.put(box(d0 + 3, dy0 + 24, d0 + 4, dy1, w) | box(d1 - 4, dy0 + 24, d1 - 3, dy1, w), 'T', 1.4)
    leaf = poly([(d1, dy0), (d1 + 7, dy0 + 2), (d1 + 7, dy1 + 1), (d1, dy1)], w)
    p.put(leaf, 'T', 2.4 + (xx[leaf] - d1) * 0.18)
    p.put(leaf & C.rim(leaf, 1, 0), 'T', 4.4)
    for hy in (dy0 + 8, dy1 - 10):
        p.put(box(d1 - 1, hy, d1 + 2, hy + 4, w), 'T', 3.4)                     # hinges
    p.resolve(band=2.0)
    return p.L.c


def v1_file():
    """The Lindner file under Konrad's coat: only the corner of the buff folder shows between the lapels (5 x 5)."""
    m = np.zeros((5, 5), bool)
    m[1:5, 0:4] = True
    m[1, 3] = False
    img = Q.flat(m, '#9E8656')
    Q.flat(np.pad(np.ones((1, 3), bool), ((1, 3), (0, 2))), '#C8B07A', img)
    return img


def v3_note():
    """Insert: Alexei's notebook under the green signal (the round-9 single plate, kept as the composite of the
    round-10 layers for old references)."""
    bg, book = v3_note_layers()
    out = bg.astype(np.float32) / 255.0
    import env_c4_cine_levelart as LA
    LA.over(out, book.astype(np.float32) / 255.0, 0, 0)
    return LA.to8(out)


V3_COVER = ((96, 66), (560, 42), (576, 330), (92, 344))
V3_PAGE = ((120, 60), (548, 48), (560, 318), (108, 330))


def v3_note_layers():
    """Insert v3, in layers: (bg, book).  bg -- the yard at night out of focus behind the notebook: the snow field
    dark blue below, the warm smear of the office window at the left, the green of the signal high at the right.
    book -- Alexei's squared exercise book (the Soviet 'v kletku'), transparent outside its cover: the cardboard
    cover with its worn corner, the edges of the pages beneath, the stapled spine where the page curves down into
    the fold, the 5 mm squares and the margin line, the four numbers of the one wagon in pencil (graphite catching
    the light), the last one underlined twice, an arrow down the column, a dog-eared corner.  The hand (figures
    stream, v3_thumb) holds it at the lower left; snow lands on the page at runtime."""
    R = Q.ramps(P=['#0C1A12', '#14281C', '#1E3A28', '#2C5038', '#406A4C', '#5E8C66', '#86B48A', '#B4DCB2'],
                G=['#06100A', '#0C1A12', '#14281C', '#1E3226', '#2C4434'], K=KNIGHT,
                Q=['#070B09', '#0A0F0C', '#14201A', '#203428', '#2E4A38', '#3E5E48'],
                S=['#3A4038', '#5A6656', '#7E8C78'],
                N=['#05070C', '#0A0E16', '#101722', '#18222E', '#22303E'],
                A=['#0C0806', '#1E140A', '#3A2610', '#5A3C18'],
                V=['#06100A', '#0C2214', '#14361E', '#1E4A2A'])
    # ---- the background (opaque): night, out of focus
    b = C.Paint(VW, VH, R, 'v3bg')
    yy, xx = b.yy, b.xx
    nz = Q.noise(VW, VH, 40, 9121, octaves=2)
    warm = Q.lightfield(VW, VH, [(30, 120, 160, 1.0, 1.3)])
    green = Q.lightfield(VW, VH, [(640, 30, 180, 1.0, 1.3)])
    b.put(yy >= 0, 'N', 0.8 + nz * 0.8 + np.clip((yy - 200) / 160.0, 0, 1) * 1.6)
    th = pg.bayer(VW, VH, 2, 1)
    wm = warm > 0.22 + th * 0.35                                               # dithered edges: smears, no discs
    b.put(wm, 'A', 0.5 + warm[wm] * 2.0 + nz[wm] * 0.4)
    gm = green > 0.22 + th * 0.35
    b.put(gm, 'V', 0.5 + green[gm] * 2.0 + nz[gm] * 0.4)
    b.resolve(band=2.0)
    bg = b.L.c.copy()
    bg[..., 3] = 255
    # ---- the notebook
    p = C.Paint(VW, VH, R, 'v3book')
    yy, xx = p.yy, p.xx
    nz = Q.noise(VW, VH, 12, 9111)
    fine = Q.noise(VW, VH, 2, 9113)
    sig = Q.lightfield(VW, VH, [(560, -60, 620, 1.0, 1.1)])
    cover = poly(list(V3_COVER))
    p.put(cover, 'Q', 1.6 + sig[cover] * 1.4 + nz[cover] * 0.5)
    p.put(cover & C.rim(cover, 0, 0, 1), 'Q', 3.6 + sig[cover & C.rim(cover, 0, 0, 1)])     # the board's cut edge
    worn = cover & (np.hypot(xx - 574, yy - 330) < 16) & (fine > 0.4)
    p.put(worn, 'S', 0.8)                                                        # the worn corner
    # the pages beneath, their edges between the page and the cover (right and bottom)
    under = poly([(124, 56), (554, 46), (568, 326), (104, 338)])
    p.put(under & cover, 'P', 2.6 + sig[under & cover] * 1.8)
    stack = under & cover & (np.mod(xx * 0.2 + yy * 1.0, 2.0) < 0.7)
    p.put(stack, 'P', 1.6 + sig[stack] * 1.2)
    page = poly(list(V3_PAGE))
    # the page: lit green by the signal from the upper right, curving down into the fold at the spine (left)
    fold = np.clip(1.0 - (xx - 108) / 46.0, 0, 1) ** 1.6
    p.put(page, 'P', 3.2 + sig[page] * 2.6 + fine[page] * 0.35 - fold[page] * 1.8)
    # the squares (5 mm grid), a little skewed with the page; the margin line
    gu = (xx - 108) + (yy - 48) * 0.03
    gv = (yy - 48) - (xx - 108) * 0.027
    grid_ = page & ((np.mod(gu, 13) < 0.9) | (np.mod(gv, 13) < 0.9))
    p.put(grid_, 'P', 2.5 + sig[grid_] * 2.0 - fold[grid_] * 1.6)
    p.put(page & (np.abs(gu - 380) < 0.9), 'S', 1.4)
    p.put(page & C.rim(page, 0, -1, 2), 'P', 6.0)
    for sy in (120, 250):                                                       # the staples at the spine
        p.put(box(112, sy, 118, sy + 2), 'S', 2.4)
        p.put(box(112, sy, 118, sy + 1), 'S', 2.9)
        p.put(box(111, sy + 2, 119, sy + 3), 'G', 0.6)
    # the dog-eared corner at the lower right
    ear = poly([(560, 318), (530, 320), (557, 292)])
    p.put(ear & page, 'P', 4.6 + sig[ear & page] * 1.4)
    p.put(ear & page & C.rim(ear, 0, 0, 1), 'P', 2.4)
    p.put(poly([(560, 318), (557, 292), (562, 300)]) & cover, 'Q', 0.8)
    # the pencil: graphite strokes, dark, a sheen on their upper edges
    for i, s_ in enumerate(NUMBERS):
        t = Q.place(Q.hand_text_k(s_, 3, 0.18, 9105 + i), VW, VH, 170 + i * 6, 76 + i * 56)
        p.put(t & page, 'G', 0.8 + fine[t & page] * 0.6)
        sheen = t & page & ~C.shift(t, 0, 1)
        p.put(sheen, 'G', 2.6 + sig[sheen] * 1.4)
    for k in range(2):
        ul = p.line([(176, 76 + 3 * 56 + 30 + k * 5), (420, 70 + 3 * 56 + 32 + k * 5)], r=0.9)
        p.put(ul & page, 'G', 0.8)
    arrow = p.line([(470, 98), (480, 260)], r=0.9) | p.line([(470, 248), (480, 262), (492, 250)], r=0.9)
    p.put(arrow & page, 'G', 1.0)
    smudge = page & (np.hypot((xx - 300) / 60.0, (yy - 268) / 10.0) < 1.0) & (fine > 0.55)
    p.put(smudge, 'P', 3.0 + sig[smudge] * 2.0)                                  # graphite rubbed by the hand
    p.resolve(band=2.0)
    book = p.L.c.copy()
    book[..., 3] = np.where(cover, 255, 0).astype(np.uint8)
    return bg, book


def _components(alpha):
    """4-connected components of a boolean mask -> label image (0 = background)."""
    h, w = alpha.shape
    lab = np.zeros((h, w), np.int32)
    n = 0
    for y0, x0 in zip(*np.nonzero(alpha)):
        if lab[y0, x0]:
            continue
        n += 1
        stack = [(y0, x0)]
        lab[y0, x0] = n
        while stack:
            y, x = stack.pop()
            for yy_, xx_ in ((y - 1, x), (y + 1, x), (y, x - 1), (y, x + 1)):
                if 0 <= yy_ < h and 0 <= xx_ < w and alpha[yy_, xx_] and not lab[yy_, xx_]:
                    lab[yy_, xx_] = n
                    stack.append((yy_, xx_))
    return lab


def seat_thumb(img, at, cover_left=94):
    """v3_thumb (figures stream) arrives as two pieces: the sleeve and wrist cut at the notebook's left edge, and
    the thumb alone some 30 px further in on the page -- a thumb floating free of its hand.  Place the thumb piece
    so that its base sits on the cover's edge where the wrist goes behind the notebook (the hand wraps the spine:
    palm and fingers behind the cover, the thumb in front), touching the cut of the sleeve.  Only the figures'
    own pixels are moved; nothing is painted."""
    a = img[..., 3] > 0
    lab = _components(a)
    sizes = np.bincount(lab.ravel())
    sizes[0] = 0
    if (sizes > 30).sum() < 2:
        return img
    order = np.argsort(-sizes)
    sleeve, thumb = order[0], order[1]
    ty, tx = np.nonzero(lab == thumb)
    sy, sx = np.nonzero(lab == sleeve)
    if tx.mean() < sx.mean():                       # the thumb is the piece further right (on the page)
        sleeve, thumb = thumb, sleeve
        ty, tx = np.nonzero(lab == thumb)
        sy, sx = np.nonzero(lab == sleeve)
    base = int(np.argmin(tx))                       # its base: the leftmost pixel (the tip is down-right)
    by = ty[base]
    near = np.abs(sy - by) <= 3
    edge = int(sx[near].max()) if near.any() else cover_left - at[0]
    dx = edge - int(tx[base]) - 1
    out = img.copy()
    out[ty, tx, 3] = 0
    nx = tx + dx
    ok = (nx >= 0) & (nx < img.shape[1])
    out[ty[ok], nx[ok]] = img[ty[ok], tx[ok]]
    return out


def build(w):
    w('voices/v1_door.png', v1_door())
    w('voices/v1_file.png', v1_file())
    look = Q.LIGHT_MORNING_B
    sk, ik = Q.fig_sheet('konrad', [('walk_side', None, True), ('idle_side', None, True)], look)
    w('voices/v1_konrad.png', sk)
    L['v1_konrad'] = ik
    L['v1_off'] = V1_OFF
    (d0, dy0, d1, dy1), _w = _door()
    L['v1_walk'] = [d0 + 8, d0 + 8 - 150]
    L['v1_sill'] = dy1
    import env_c4_cine_figs as G
    from env_c4_cine_places import figs_disk as FD
    w('voices/v2_konrad.png', FD('voices/v2_konrad.png', lambda: Q.sheet([G.v2_konrad(0), G.v2_konrad(1),
                                                                           G.v2_konrad(2)])))
    L['v2_konrad_at'] = list(G.V2_AT)
    L['v2_off'] = V2_OFF
    sa, ia = Q.fig_sheet('alexei', [('walk_side', None, True), ('idle_side', None, True)], Q.LIGHT_SIGNAL)
    w('voices/v3_alexei.png', sa)
    L['v3_alexei'] = ia
    sl, il = Q.fig_sheet('lev', [('walk_side', None, True), ('idle_side', None, True)], Q.LIGHT_SIGNAL,
                         standin='worker_b')
    w('voices/v3_lev.png', sl)
    L['v3_lev'] = il
    bg, book = v3_note_layers()
    w('voices/v3_note_bg.png', bg)
    w('voices/v3_book.png', book)
    w('voices/v3_note.png', v3_note())
    w('voices/v3_thumb.png', seat_thumb(FD('voices/v3_thumb_raw.png', G.v3_thumb), G.V3T_AT))
    w('voices/v3_thumb_raw.png', FD('voices/v3_thumb_raw.png', G.v3_thumb))    # the render as delivered
    L['v3t_at'] = list(G.V3T_AT)
    w('voices/lantern.png', Q.glow_sprite(64, 64, [(32, 32, 26, 26, (110, 70, 24), 1.4),
                                                   (32, 32, 4, 5, (160, 120, 60), 1.6)], 6.0))
    L['numbers'] = NUMBERS
