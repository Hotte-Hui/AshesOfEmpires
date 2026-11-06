"""env_c4_cine_card -- art of LS_C4_Card (owner: cine stream, round 9; C4_DESIGN §2.9, §2.5).

The second match cut, on the torn registry card No. 0417 (Anna Lindner, née Kowalenko):
  c1  Berlin, the loading hatch at dawn: Konrad lifts the German half out of the snow beside the split crate;
      his right thumb runs down the perforated edge
  c2  macro: the perforation of the German half (paper left of the edge), the thumb's shadow along it
  c3  match cut, mirrored: the SAME perforation (same holes, same tufts) of the Russian half (paper right of the
      edge), Alexei's finger's shadow (c3a) -> the desk in the siding office: the Russian half, Alexei's hand,
      the kerosene lamp, the stencils on the wall (c3b)
  c4  over Alexei's shoulder: he looks up from the card to the wagon beyond the booth window
Runtime: scenes/cinematics/ch4_card/ch4_card.gd (anchors in layout.json "card").
"""
from __future__ import annotations

import math
import os

import numpy as np

import env_c4_cine_kit as Q
from env_c4_cine_kit import (C, VW, VH, KNIGHT, AMBER, RUST, CREAM, OAKK, IRONK, DAWN, SNOWB, SODIUM, PINE,
                             PAPERB, INKRED, VIOLET, STEEL, box, ell, poly, grid)
import pg

L = Q.LAYOUT.setdefault('card', {})

CARD_W, CARD_H = 176, 118              # the German half in c1 (sprite)
CARD_AT = (230, 104)                   # its top-left when held (c1)
EDGE_X = 330                           # the perforation in the macros (c2 / c3a)
MACRO_K = 4                            # macro scale of the perforation
PERF = Q.perforation(40, Q.PERF_PITCH, 1.6, seed=417)
MACRO_Y0 = -6.0                        # hole phase of the macro (same in c2 and c3a)
RU_AT = (300, 150)                     # the Russian half on the desk (c3b), top-left
RU_W, RU_H = 170, 96


def _paper(p, mask, ramp, base, seed, yy, xx, light):
    fib = Q.noise(p.w, p.h, 2, seed) * 0.6 + Q.noise(p.w, p.h, 9, seed + 1) * 0.6
    p.put(mask, ramp, base + fib[mask] + light[mask])


# ======================================================================================= c1
def card_de():
    """The German half (left part of the bilingual form), perforated right edge, red C-17 tab, typed."""
    w, h = CARD_W, CARD_H
    R = Q.ramps(P=PAPERB, I=['#1A1A1E', '#2A2A30', '#3C3C44'], R=INKRED, S=SNOWB)
    p = C.Paint(w, h, R, 'card_de')
    yy, xx = p.yy, p.xx
    light = Q.lightfield(w, h, [(-20, -30, 260, 1.4, 1.0)])
    paper = Q.torn_edge_mask(h, w, w - 1, PERF, 'left', y0=2.0, scale=1.0)
    _paper(p, paper, 'P', 4.6, 6101, yy, xx, light)
    p.put(paper & (xx == 0), 'P', 3.6)
    p.put(paper & (yy == 0), 'P', 7.0)
    p.put(paper & (yy == h - 1), 'P', 3.4)
    # the red C-17 tab at the top left
    p.put(box(0, 0, 30, 12, w, h), 'R', 3.6)
    p.put(Q.text_at('C-17', w, h, 4, 3, 's') & box(0, 0, 30, 12, w, h), 'P', 7.6)
    ink = lambda m: p.put(m & paper, 'I', 1.0)  # noqa: E731
    ink(Q.text_at('NR. 0417', w, h, w - 42, 3, 's'))
    p.put(box(34, 14, w - 8, 15, w, h), 'I', 2.0)
    ink(Q.text_at('LINDNER, ANNA', w, h, 6, 19, 'l'))
    lines = ['GEB. KOWALENKO, 1926 CHARKOW', 'VERMERK C-17: RÜCKFÜHRUNG OST', 'ABGABE KORDON-17, TÜR OST',
             'KURIERWAGEN C-17/45', 'DI 18.2., 23.40', 'KIND ILSE, 8 - VERBLEIB', 'UNGEKLÄRT']
    for i, s in enumerate(lines):
        ink(Q.text_at(s, w, h, 6, 33 + i * 10, 's'))
    p.put(box(6, 33 + 3 * 10 + 7, 82, 33 + 3 * 10 + 8, w, h) & paper, 'R', 3.0)   # underlined in red
    p.resolve(band=2.0)
    L['card_size'] = [w, h]
    return p.L.c


def c1_bg():
    """The snow beside the split crate, seen from above at dawn: spilled cards, foot prints, the sodium lamp's
    warm edge at the right."""
    R = Q.ramps(S=SNOWB, P=PINE, X=PAPERB, B=['#06080C', '#0C1018', '#141A24', '#1E2632'], N=SODIUM, D=DAWN)
    p = C.Paint(VW, VH, R, 'c1')
    yy, xx = p.yy, p.xx
    nz = Q.noise(VW, VH, 18, 6201)
    sod = Q.lightfield(VW, VH, [(700, 120, 380, 1.0, 1.2)])
    crys = (Q.noise(VW, VH, 1.5, 6203) > 0.8) & (pg.bayer(VW, VH, 0, 0) > 0.5)
    p.put(yy >= 0, 'S', 4.8 + nz * 1.6 + sod * 1.8 - (xx / VW) * 0.4)
    p.put(crys, 'S', 8.0)
    # foot prints (a trodden track across)
    for i in range(7):
        fx, fy = 40 + i * 92, 300 - i * 10 + (i % 2) * 18
        fp = ell(fx, fy, 12, 6)
        p.put(fp, 'S', 3.0 + nz[fp])
        p.put(fp & C.rim(fp, 0, 1), 'S', 6.4)
    # the split crate at the upper right: broken boards, cards spilling into the snow
    crate = poly([(430, 40), (640, 30), (640, 170), (470, 186), (420, 120)])
    p.put(crate, 'P', 3.4 + nz[crate] * 1.4 + sod[crate] * 1.6)
    p.put(crate & (np.mod(yy - xx * 0.05, 14) < 1.2), 'B', 1.6)
    split = poly([(446, 64), (474, 70), (496, 108), (484, 150), (522, 182), (506, 184), (470, 152), (480, 112),
                  (460, 80)])
    p.put(split, 'B', 0.6)
    p.put(split & C.rim(split, 1, 0), 'P', 5.4)
    inside = poly([(452, 84), (470, 92), (478, 120), (466, 150), (448, 130)])
    p.put(inside & (np.mod(yy, 3) == 0), 'X', 5.0)                                    # cards standing inside
    p.put(Q.stencil_mask('C-17/45', 16, VW, VH, 520, 60, width=1.9) & crate, 'B', 1.0)
    rng = np.random.default_rng(6205)
    for k in range(9):
        cx, cy = 300 + rng.integers(0, 200), 150 + rng.integers(0, 140)
        ang = rng.uniform(-30, 30)
        c = Q.rotate_mask(np.ones((22, 34), bool), ang, (40, 44))
        m = Q.place(c, VW, VH, cx, cy)
        p.put(m, 'X', 5.4 + sod[m] * 1.0)
        p.put(m & C.rim(m, 0, -1), 'X', 7.0)
        p.put(m & (np.mod(yy, 4) == 1) & (np.mod(xx + k, 9) < 6) & ~C.rim(m, 0, -1), 'X', 3.6)   # typed lines
        drift = m & (yy > cy + 14 + (k % 3) * 2)
        p.put(drift, 'S', 7.0)                                                       # snow drifted over
    p.resolve(band=2.0)
    return p.L.c


# ======================================================================================= c2 / c3a (macros)
def _macro_paper(side, ramp_bg):
    """Shared macro of the perforation: paper on `side` of EDGE_X, holes at the same y in both halves."""
    return Q.torn_edge_mask(VH, VW, EDGE_X, PERF, side, y0=MACRO_Y0, scale=MACRO_K)


def c2_macro():
    R = Q.ramps(P=PAPERB, I=['#16161A', '#24242A', '#34343C'], S=SNOWB, D=DAWN, R=INKRED)
    p = C.Paint(VW, VH, R, 'c2')
    yy, xx = p.yy, p.xx
    light = Q.lightfield(VW, VH, [(-100, -80, 700, 1.4, 1.0)])
    # out-of-focus snow beyond the edge: soft blue, the split crate a dark blur low at the right, the dawn sky a
    # paler band at the top (the bokeh discs are runtime sprites now: they drift with the hand)
    blur = Q.noise(VW, VH, 60, 6301, octaves=2)
    crate = np.clip(1.0 - np.hypot((xx - 560) / 150.0, (yy - 330) / 90.0), 0, 1) ** 0.8
    p.put(yy >= 0, 'S', 3.6 + (yy / VH) * 1.6 + blur * 1.2 + np.clip((60 - yy) / 60.0, 0, 1) * 1.4 - crate * 2.2)
    paper = _macro_paper('left', 'S')
    _paper(p, paper, 'P', 4.4, 6305, yy, xx, light * 1.6)
    # paper fibres along the torn edge
    fe = paper & ~C.shift(paper, -1, 0)
    p.put(fe, 'P', 7.0)
    p.put(paper & C.rim(paper, 1, 0, 3) & ~fe, 'P', 3.4)
    # the typed number, huge: „NR. 0417“ just left of the edge, a few cut lines below
    t = Q.smooth_up(Q.text('NR. 0417', 'l', 1), 4)
    m = Q.place(t, VW, VH, EDGE_X - t.shape[1] - 18, 70)
    inkn = Q.noise(VW, VH, 2, 6307) > 0.22
    p.put(m & paper & inkn, 'I', 1.0)
    p.put(m & paper & ~inkn, 'I', 2.4)
    for i, s in enumerate(('C-17/45', 'TÜR OST', '23.40')):
        tm = Q.place(Q.smooth_up(Q.text(s, 's', 1), 4), VW, VH, EDGE_X - 230 + i * 18, 140 + i * 48)
        p.put(tm & paper & inkn, 'I', 1.4)
    p.put(box(0, 128, EDGE_X - 30, 130) & paper, 'I', 2.6)
    p.resolve(band=2.0)
    L['edge_x'] = EDGE_X
    L['macro_k'] = MACRO_K
    L['macro_y0'] = MACRO_Y0
    L['macro_holes'] = [round(MACRO_Y0 + y * MACRO_K, 2) for y in PERF['ys'] if MACRO_Y0 + y * MACRO_K < VH + 20]
    return p.L.c


def c3a_macro():
    R = Q.ramps(P=['#2A241A', '#463C2C', '#665840', '#887654', '#A89470', '#C8B48E', '#E2D0AA', '#F2E4C4'],
                I=['#1A1612', '#2C241E', '#3E342A'], W=OAKK, A=AMBER, V=VIOLET)
    p = C.Paint(VW, VH, R, 'c3a')
    yy, xx = p.yy, p.xx
    light = Q.lightfield(VW, VH, [(760, -60, 700, 1.6, 1.0)])
    # out-of-focus desk wood beyond the edge (warm)
    p.put(yy >= 0, 'W', 2.6 + Q.noise(VW, VH, 50, 6401, octaves=2) * 1.6 + light * 1.4 + (xx / VW) * 0.8 -
          np.clip((yy - 250) / 110.0, 0, 1) * 0.8)
    paper = _macro_paper('right', 'W')
    _paper(p, paper, 'P', 3.8, 6405, yy, xx, light * 1.6)
    fe = paper & ~C.shift(paper, 1, 0)
    p.put(fe, 'P', 6.4)
    p.put(paper & C.rim(paper, -1, 0, 3) & ~fe, 'P', 2.6)
    t = Q.smooth_up(Q.text('№ 0417', 'l', 1), 4)
    m = Q.place(t, VW, VH, EDGE_X + 22, 70)
    inkn = Q.noise(VW, VH, 2, 6407) > 0.22
    p.put(m & paper & inkn, 'I', 1.0)
    p.put(m & paper & ~inkn, 'I', 2.2)
    for i, s in enumerate(('КОВАЛЕНКО', 'ХАРЬКОВ', 'КАРСК')):
        tm = Q.place(Q.smooth_up(Q.text(s, 's', 1), 4), VW, VH, EDGE_X + 24 + i * 14, 140 + i * 48)
        p.put(tm & paper & inkn, 'I', 1.4)
    st = Q.stamp_mask('ПРИНЯТЬ', k=4, seed=6409)
    sm = Q.place(st, VW, VH, EDGE_X + 150, 230)
    p.put(sm & paper, 'V', 3.0)
    p.resolve(band=2.0)
    return p.L.c


def paper_layer(img, side):
    """The paper of a macro plate alone (alpha = the torn paper mask): drawn over the fingers that hold the card
    from behind, so the perforated edge itself cuts them."""
    out = img.copy()
    out[..., 3] = np.where(_macro_paper(side, 'S'), 255, 0).astype(np.uint8)
    return out


THUMB_FRONT = (28, 104)                # c2_thumb canvas: the thumb lies right of x / below y (the fingers above it)


def split_thumb(img):
    """c2_thumb -> (behind, front).  Konrad's right hand grips the German half at its torn edge: the thumb is
    pressed on the face of the card, the other fingers are behind it.  `behind` (drawn under the paper layer) is
    the glove without the thumb, `front` (over it) the thumb and the glove beyond the edge; the cast shadow stays
    only where it falls on the paper (left of the edge), never on the snow far behind."""
    h, w = img.shape[:2]
    yy, xx = grid(h, w)
    a = img[..., 3]
    shadow = (a > 0) & (a < 255)
    tx, ty = THUMB_FRONT
    thumb = (a == 255) & (yy >= ty) & (xx >= tx)
    import env_c4_cine_figs as G
    on_paper = xx < (G.MACRO_OFF['de'][0] - 2)
    behind = img.copy()
    behind[..., 3] = np.where((a == 255) & ~thumb, 255, 0).astype(np.uint8)
    front = img.copy()
    front[..., 3] = np.where(thumb, 255, np.where(shadow & on_paper & (yy >= ty), a, 0)).astype(np.uint8)
    return behind, front


def bokeh_sheet():
    """Out-of-focus light discs (3 sizes) for the macros: a soft disc with the brighter rim of a lens' bokeh,
    white, drawn additively and tinted at runtime (dawn snow blue in c2, lamp amber in c3a)."""
    out = []
    for r in (9, 15, 23):
        s = 2 * r + 4
        yy, xx = grid(s, s)
        d = np.hypot(xx + 0.5 - s / 2, yy + 0.5 - s / 2) / r
        v = np.where(d < 1.0, 0.42 + 0.30 * np.clip((d - 0.55) / 0.4, 0, 1), 0.0)
        v *= np.clip((1.0 - d) / 0.12, 0, 1)
        q = np.floor(v * 6.0 + pg.bayer(s, s, 1, 2) * 0.9) / 6.0
        a = np.zeros((56, 56, 4), np.uint8)
        o = (56 - s) // 2
        a[o:o + s, o:o + s, :3] = np.clip(q * 255, 0, 255).astype(np.uint8)[..., None]
        a[o:o + s, o:o + s, 3] = np.where(q > 0, 255, 0).astype(np.uint8)
        out.append(a)
    return Q.sheet(out)


def thumb_shadow(w=120, h=150):
    """The soft shadow of a thumb / fingertip pressed on the paper near the edge (multiplied by alpha)."""
    yy, xx = grid(h, w)
    d = np.hypot((xx - w / 2) / (w / 2), (yy - h / 2) / (h / 2))
    a = np.clip(1.0 - d, 0, 1) ** 0.8 * 0.7
    out = np.zeros((h, w, 4), np.uint8)
    out[..., :3] = (8, 10, 18)
    return Q.dither_alpha(np.concatenate([out[..., :3], np.full((h, w, 1), 255, np.uint8)], -1), a, seed=3)


# ======================================================================================= c3b (the desk)
def card_ru_desk():
    """The Russian half lying on the desk (perforation at its LEFT edge), seen from above at an angle."""
    w, h = RU_W, RU_H
    R = Q.ramps(P=['#2A241A', '#463C2C', '#665840', '#887654', '#A89470', '#C8B48E', '#E2D0AA', '#F2E4C4'],
                I=['#1A1612', '#2C241E', '#3E342A'], V=VIOLET)
    p = C.Paint(w, h, R, 'card_ru')
    yy, xx = p.yy, p.xx
    light = Q.lightfield(w, h, [(w + 60, -40, 260, 1.2, 1.0)])
    paper = Q.torn_edge_mask(h, w, 1.0, PERF, 'right', y0=1.0, scale=0.8)
    _paper(p, paper, 'P', 4.0, 6501, yy, xx, light)
    ink = lambda m: p.put(m & paper, 'I', 1.0)  # noqa: E731
    ink(Q.text_at('№ 0417', w, h, 8, 4, 's'))
    ink(Q.text_at('КОВАЛЕНКО АННА ПЕТРОВНА', w, h, 8, 16, 's'))
    for i, s in enumerate(('1926, ХАРЬКОВ', '1942 В ГЕРМАНИЮ', 'ВОЗВРАЩЕНКА', 'ДАЛЕЕ: ФИЛЬТР. ПУНКТ', 'КАРСК')):
        ink(Q.text_at(s, w, h, 8, 28 + i * 9, 's'))
    sm = Q.place(Q.stamp_mask('ПРИНЯТЬ', k=1, frame=(52, 18), angle=-4, seed=6503), w, h, 96, 60)
    p.put(sm & paper, 'V', 3.4)
    p.resolve(band=2.0)
    return p.L.c


C3_LAMP = (548, 92)                     # kerosene lamp flame (c3b)


def c3b_desk():
    R = Q.ramps(W=OAKK, A=AMBER, I=IRONK, K=KNIGHT, B=['#2A1D0B', '#4A3415', '#73531F', '#9C7630', '#C49A48',
                                                      '#E8C779'],
                T=['#1A1C20', '#2C2F34', '#40444A', '#585C62', '#74787C'], R=RUST, X=CREAM)
    p = C.Paint(VW, VH, R, 'c3b')
    yy, xx = p.yy, p.xx
    nz = Q.noise(VW, VH, 10, 6601)
    lamp = Q.lightfield(VW, VH, [(C3_LAMP[0], C3_LAMP[1] + 40, 520, 1.0, 1.15)])
    # the booth wall: vertical boards, the stencils on nails (C-17/41 .. /44, the nail of /45 empty)
    wall = yy < 132
    p.put(wall, 'W', 1.6 + nz[wall] * 0.6 + lamp[wall] * 2.8 - (np.mod(xx, 26) < 1)[wall] * 1.0)
    for i, sx in enumerate((40, 128, 216, 304)):
        sh = box(sx, 54, sx + 72, 104)
        p.put(sh, 'T', 2.6 + nz[sh] * 0.8 + lamp[sh] * 1.8)
        p.put(sh & (yy == 54), 'T', 4.6)
        st = Q.stencil_mask('C-17/4%d' % (1 + i), 9, VW, VH, sx + 6, 72, width=1.9)
        p.put(st, 'K', 0.6)
        p.put(st & C.shift(st, 1, 1) & ~st | (C.shift(st, 0, 1) & ~st & sh), 'R', 2.4)    # old paint at the edges
        p.put(ell(sx + 36, 48, 2, 2), 'I', 4.0)
    p.put(ell(428, 48, 2, 2), 'I', 4.4)                                     # the empty nail of /45
    p.put(box(396, 56, 464, 104) & (Q.noise(VW, VH, 3, 6603) > 0.55), 'W', 3.6)   # paler wood where it hung
    # the desk: oak, worn, the edge toward us
    desk = yy >= 132
    p.put(desk, 'W', 2.8 + nz[desk] * 0.9 + lamp[desk] * 3.0 + Q.noise(VW, VH, 3, 6605)[desk] * 0.4)
    p.put(desk & (np.mod(yy + np.floor(xx / 160) * 3, 22) < 1), 'W', 1.8)
    p.put(box(0, 132, VW, 134), 'W', 4.6)
    # the kerosene lamp: brass foot, glass chimney (the flame is a runtime sprite)
    lx, ly = C3_LAMP
    foot = ell(lx, 150, 26, 8) | box(lx - 10, 118, lx + 10, 150)
    p.put(foot, 'B', 2.6 + (lx + 10 - xx[foot]) / 20.0 * 1.6)
    p.put(ell(lx, 124, 18, 10), 'B', 3.4)
    chim = ell(lx, 100, 12, 18) | box(lx - 6, 70, lx + 7, 100)
    p.put(chim, 'A', 4.6 + lamp[chim] * 1.4)
    p.put(chim & (np.abs(xx - lx + 6) < 1.5), 'X', 6.0)
    # the card box at the right edge, its label
    bx = box(588, 150, 640, 240)
    p.put(bx, 'W', 3.6 + lamp[bx] * 1.6)
    p.put(box(596, 186, 640, 206), 'X', 4.6)
    p.put(Q.text_at('C-17/45', VW, VH, 600, 190, 's'), 'K', 0.8)
    p.resolve(band=2.0)
    L['c3_lamp'] = list(C3_LAMP)
    L['ru_at'] = list(RU_AT)
    return p.L.c


FLAME_W, FLAME_H = 12, 24              # flame cells (the wick at the bottom centre: FLAME_W // 2, FLAME_H - 2)


def lamp_flame():
    """4 frames of the kerosene flame inside the chimney (normal blending, alpha): a flat wick flame -- a blue
    foot on the wick, the white-yellow core, the yellow body, an orange skin and a thin tip that sways and
    stretches as it breathes.  Bottom-anchored on the wick (FLAME_W x FLAME_H cells)."""
    out = []
    w, h = FLAME_W, FLAME_H
    yy, xx = grid(h, w)
    for i, (hgt, sway, wid) in enumerate(((17.0, 0.0, 3.0), (18.5, 0.7, 2.8), (16.0, -0.5, 3.2), (17.8, -0.9, 2.9))):
        base = h - 2.0
        t = np.clip((base - (yy + 0.5)) / hgt, 0.0, 1.2)                # 0 at the wick, 1 at the tip
        cx = w / 2.0 + sway * t ** 2
        half = wid * np.sin(np.pi * np.clip(t, 0, 1) ** 0.62) * (1.0 - 0.25 * t)
        d = np.abs(xx + 0.5 - cx) / np.maximum(half, 1e-3)
        body = (t > 0.0) & (t < 1.0) & (d < 1.0)
        img = np.zeros((h, w, 4), np.uint8)

        def put(m, hexcol, alpha=255):
            img[m, :3] = Q.hexrgb(hexcol).astype(np.uint8)
            img[m, 3] = alpha
        put(body, '#F08A2A')                                            # orange skin
        put(body & (d < 0.78) & (t > 0.06), '#FFC860')                  # yellow body
        put(body & (d < 0.5) & (t > 0.12) & (t < 0.72), '#FFF0C0')      # white-yellow core
        put(body & (t < 0.12) & (d < 0.9), '#6A78D8')                   # blue foot on the wick
        put((t >= 0.98) & (t < 1.12) & (np.abs(xx + 0.5 - cx) < 0.6), '#F0A040', 200)   # the thin tip
        img[h - 2:h, w // 2 - 1:w // 2 + 1, :3] = Q.hexrgb('#2A1A10').astype(np.uint8)   # the wick
        img[h - 2:h, w // 2 - 1:w // 2 + 1, 3] = 255
        out.append(img)
    return Q.sheet(out)


# ======================================================================================= c4 (over the shoulder)
C4_WIN = (250, 70, 600, 254)


def c4_bg():
    R = Q.ramps(W=OAKK, A=AMBER, K=KNIGHT, I=IRONK, R=RUST, X=CREAM,
                Y=['#0E1014', '#1A1E24', '#2A3038', '#3E4650', '#566270', '#76828E', '#A2AAB2', '#D2D6D8'])
    p = C.Paint(VW, VH, R, 'c4')
    yy, xx = p.yy, p.xx
    nz = Q.noise(VW, VH, 12, 6701)
    lamp = Q.lightfield(VW, VH, [(-40, 220, 420, 1.0, 1.2)])
    p.put(yy >= 0, 'W', 1.2 + nz * 0.6 + lamp * 3.0 - (np.mod(xx, 30) < 1) * 0.8)
    x0, y0, x1, y1 = C4_WIN
    win = box(x0, y0, x1, y1)
    # the view through the dirty glass: the siding hall, wagon 24 318 under the cold work lamp
    wl = Q.lightfield(VW, VH, [(430, 70, 200, 1.0, 1.2)])
    p.put(win, 'Y', 0.8 + wl[win] * 4.0 + nz[win] * 0.4)
    wag = box(300, 132, 560, 222) & win
    p.put(wag, 'R', 1.6 + wl[wag] * 4.4 - (np.mod(yy[wag] - 132, 10) < 1) * 1.0)
    p.put(box(300, 124, 560, 132) & win, 'I', 2.0 + wl[124:132, 300:560].mean() * 2.0)
    st = Q.stencil_mask('C-17/45', 11, VW, VH, 320, 160, width=1.9)
    p.put(st & win, 'X', 4.6)
    p.put(box(418, 146, 456, 218) & win, 'K', 0.6)                          # the half-open door
    p.put(box(428, y0, 429, 84), 'I', 2.0)
    p.put(ell(428.5, 88, 6, 3), 'Y', 7.6)
    smudge = win & (Q.noise(VW, VH, 20, 6703) > 0.78) & (pg.bayer(VW, VH, 1, 1) > 0.55)
    p.put(smudge, 'Y', 3.0 + wl[smudge] * 1.6)
    # window frame and muntins
    fr = box(x0 - 10, y0 - 10, x1 + 10, y1 + 10) & ~win
    p.put(fr, 'W', 2.6 + lamp[fr] * 2.0)
    mun = win & ((np.abs(xx - (x0 + x1) / 2) < 3) | (np.abs(yy - (y0 + y1) / 2) < 3))
    p.put(mun, 'W', 2.2 + lamp[mun] * 1.6)
    p.put(box(x0 - 14, y1 + 8, x1 + 14, y1 + 16), 'W', 3.6 + lamp[y1 + 8:y1 + 16, x0:x1].mean() * 2.0)
    # the desk edge at the bottom, the card on it (Alexei's hands rest there)
    desk = yy >= 284
    p.put(desk, 'W', 3.0 + nz[desk] + lamp[desk] * 2.6)
    p.resolve(band=2.0)
    L['c4_win'] = list(C4_WIN)
    return p.L.c


# ======================================================================================= polish pass
def c1_bg2():
    """The snow beside the split crate at dawn (from above, as Konrad bends down): wind-rippled snow with blue
    hollows, the tyre track of the lorry, boot prints with their shadowed rims, the split crate (boards with grain,
    nails, the splintered break, the stencil C-17/45), cards fanned out of it and half-buried, a dropped chain, the
    warm edge of the sodium lamp at the right."""
    R = Q.ramps(S=SNOWB, P=PINE, X=PAPERB, B=['#06080C', '#0C1018', '#141A24', '#1E2632', '#2A3440'], N=SODIUM,
                D=DAWN, T=STEEL, I=['#1A1A1E', '#2A2A30', '#3C3C44'])
    p = C.Paint(VW, VH, R, 'c1b')
    yy, xx = p.yy, p.xx
    nz = Q.noise(VW, VH, 18, 6211)
    fine = Q.noise(VW, VH, 2.5, 6213)
    sod = Q.lightfield(VW, VH, [(700, 120, 380, 1.0, 1.2)])
    ripple = np.sin(xx * 0.05 + yy * 0.11 + nz * 4.0)
    p.put(yy >= 0, 'S', 4.6 + nz * 1.4 + ripple * 0.35 + sod * 1.6 - (xx / VW) * 0.4)
    p.put((fine > 0.86) & (pg.bayer(VW, VH, 0, 0) > 0.6), 'S', 8.4)          # glitter of the crust
    # the tyre track across the lower left: tread blocks pressed into the snow
    tr = (np.abs(yy - (342 - xx * 0.2)) < 12) & (fine > 0.18)
    p.put(tr, 'S', 4.2 + nz[tr] * 0.8 + sod[tr] * 1.4)
    p.put(tr & (np.mod(xx + yy * 0.5, 9) < 2) & (fine > 0.4), 'S', 3.4 + sod[tr & (np.mod(xx + yy * 0.5, 9) < 2) &
                                                                               (fine > 0.4)])
    p.put(tr & C.rim(tr, 0, -1, 1), 'S', 6.4)
    # boot prints with heel and sole, rims lit from the upper left
    for i in range(6):
        fx, fy = 70 + i * 86, 262 - i * 12 + (i % 2) * 20
        sole = ell(fx, fy, 11, 5)
        heel = ell(fx + 16, fy + 1, 5, 4)
        fp = sole | heel
        p.put(fp, 'S', 3.0 + nz[fp] * 0.5)
        p.put(fp & (np.mod(xx, 3) == 0), 'S', 2.4)
        p.put(fp & C.rim(fp, 0, 1), 'S', 6.8)
        p.put(C.rim(fp, 0, -1) & ~fp, 'S', 3.4)
    # the split crate at the upper right: boards with grain, the break, nails, the stencil
    crate = poly([(430, 40), (640, 30), (640, 170), (470, 186), (420, 120)])
    grain = Q.noise(VW, VH, 2, 6215)
    p.put(crate, 'P', 3.2 + nz[crate] * 1.0 + grain[crate] * 0.8 + sod[crate] * 1.6)
    p.put(crate & (np.mod(yy - xx * 0.05, 14) < 1.2), 'B', 1.6)
    for (nx_, ny_) in ((452, 52), (470, 166), (612, 40), (624, 156)):
        p.put(ell(nx_, ny_, 2, 2), 'T', 4.6)
    split = poly([(446, 64), (474, 70), (496, 108), (484, 150), (522, 182), (506, 184), (470, 152), (480, 112),
                  (460, 80)])
    p.put(split, 'B', 0.6)
    p.put(split & C.rim(split, 1, 0), 'P', 5.6)
    sp_ = p.line([(476, 92), (500, 84)], r=1.0) | p.line([(486, 128), (510, 134)], r=1.0)    # splinters
    p.put(sp_, 'P', 6.0)
    inside = poly([(452, 84), (470, 92), (478, 120), (466, 150), (448, 130)])
    p.put(inside & (np.mod(yy, 3) == 0), 'X', 5.0)
    p.put(Q.stencil_mask('C-17/45', 16, VW, VH, 520, 60, width=1.9) & crate, 'B', 1.0)
    # cards fanned out of the crate into the snow, some half-buried
    rng = np.random.default_rng(6217)
    for k in range(13):
        cx, cy = 300 + int(rng.integers(0, 210)), 140 + int(rng.integers(0, 150))
        ang = float(rng.uniform(-40, 40))
        c = Q.rotate_mask(np.ones((22, 34), bool), ang, (44, 46))
        m = Q.place(c, VW, VH, cx, cy)
        p.put(m, 'X', 5.2 + sod[m] * 1.0 + fine[m] * 0.4)
        p.put(m & C.rim(m, 0, -1), 'X', 7.0)
        p.put(m & (np.mod(yy, 4) == 1) & (np.mod(xx + k, 9) < 6) & ~C.rim(m, 0, -1), 'I', 2.2)   # typed lines
        if k % 3 == 0:
            p.put(m & (np.mod(yy, 9) < 3) & (np.mod(xx, 7) < 2), 'X', 3.0)                       # a red tab
        drift = m & (yy > cy + 12 + (k % 3) * 3)
        p.put(drift, 'S', 6.8 + nz[drift] * 0.6)
    # a dropped lifting chain in the snow near the crate
    for i in range(10):
        cx_, cy_ = 380 + i * 7, 230 + int(6 * math.sin(i * 0.9))
        ring = ell(cx_, cy_, 3.2, 2.2) & ~ell(cx_, cy_, 1.6, 0.8)
        p.put(ring, 'T', 3.4 + (i % 2) * 1.0)
    p.resolve(band=2.0)
    return p.L.c


def c3b_desk2():
    """The desk in the siding booth by the kerosene lamp: the board wall with the stencils C-17/41-44 on their nails
    (the nail of /45 empty, the paler wood where it hung), a calendar for February 1964 (plain, no emblem), a
    pinned timetable; on the oak desk a green blotter, an abacus, a glass of tea in its holder, a pencil in a jar,
    the violet stamp pad, the open freight ledger, the card box C-17/45 at the edge."""
    R = Q.ramps(W=OAKK, A=AMBER, I=IRONK, K=KNIGHT, B=['#2A1D0B', '#4A3415', '#73531F', '#9C7630', '#C49A48',
                                                      '#E8C779'],
                T=['#1A1C20', '#2C2F34', '#40444A', '#585C62', '#74787C'], R=RUST, X=CREAM, V=VIOLET,
                G=['#0C140E', '#14221A', '#1E3226', '#2A4432', '#385840'],
                P=['#2A241A', '#463C2C', '#665840', '#887654', '#A89470', '#C8B48E', '#E2D0AA', '#F2E4C4'],
                E=['#1A0A08', '#3A140E', '#6A2418', '#9A3A22'], H=['#D8CCB0', '#EEE4CC', '#FAF4E4'])
    p = C.Paint(VW, VH, R, 'c3b2')
    yy, xx = p.yy, p.xx
    nz = Q.noise(VW, VH, 10, 6611)
    grain = Q.noise(VW, VH, 3, 6613)
    lamp = Q.lightfield(VW, VH, [(C3_LAMP[0], C3_LAMP[1] + 40, 520, 1.0, 1.15)])
    # the board wall
    wall = yy < 132
    p.put(wall, 'W', 1.4 + nz[wall] * 0.5 + grain[wall] * 0.4 + lamp[wall] * 2.8 - (np.mod(xx, 26) < 1)[wall] * 1.0)
    p.put(wall & (np.mod(xx, 26) == 1), 'W', 2.4 + lamp[wall & (np.mod(xx, 26) == 1)] * 2.6)
    for i, sx in enumerate((40, 128, 216, 304)):
        sh = box(sx, 54, sx + 72, 104)
        p.put(sh, 'T', 2.6 + nz[sh] * 0.8 + lamp[sh] * 1.8)
        p.put(sh & (yy == 54), 'T', 4.6)
        p.put(sh & C.rim(sh, 1, 1, 2) & ~C.rim(sh, 0, -1), 'T', 1.4)
        st = Q.stencil_mask('C-17/4%d' % (1 + i), 9, VW, VH, sx + 6, 72, width=1.9)
        p.put(st, 'K', 0.6)
        p.put(st & C.shift(st, 1, 1) & ~st | (C.shift(st, 0, 1) & ~st & sh), 'R', 2.4)
        p.put(ell(sx + 36, 48, 2, 2), 'I', 4.0)
        p.put(p.line([(sx + 36, 48), (sx + 10, 54)], r=0.4) | p.line([(sx + 36, 48), (sx + 62, 54)], r=0.4), 'I', 3.0)
    p.put(ell(428, 48, 2, 2), 'I', 4.6)
    p.put(box(396, 56, 464, 104) & (Q.noise(VW, VH, 3, 6603) > 0.55), 'W', 3.6)
    # the calendar (February 1964) between the empty nail and the lamp
    cal = box(470, 40, 512, 96)
    p.put(cal, 'H', 1.0 + lamp[cal] * 1.2)
    p.put(box(470, 40, 512, 50), 'E', 2.6)
    p.put(Q.text_at('1964', VW, VH, 480, 42, 's'), 'H', 2.0)
    for r_ in range(5):
        for c_ in range(7):
            p.put(box(474 + c_ * 5, 54 + r_ * 7, 477 + c_ * 5, 57 + r_ * 7), 'T', 2.0 + (c_ == 6) * 0.0)
    p.put(box(494, 75, 497, 78), 'E', 3.4)                                      # the 16th circled
    # the desk: oak, worn, the edge toward us, a green blotter under the card
    desk = yy >= 132
    p.put(desk, 'W', 2.6 + nz[desk] * 0.8 + lamp[desk] * 3.0 + grain[desk] * 0.5)
    p.put(desk & (np.mod(yy + np.floor(xx / 160) * 3, 22) < 1), 'W', 1.8)
    p.put(box(0, 132, VW, 134), 'W', 4.6)
    blot = box(250, 140, 500, 262)
    p.put(blot, 'G', 1.8 + nz[blot] * 0.6 + lamp[blot] * 2.0)
    p.put(blot & C.rim(blot, 0, 0, 2), 'W', 1.4)
    ink = blot & (Q.noise(VW, VH, 6, 6617) > 0.78)
    p.put(ink, 'G', 0.8)
    # the abacus at the left: frame, rods, beads (brown and two white)
    ab = box(26, 150, 176, 236)
    p.put(ab, 'W', 3.2 + lamp[ab] * 1.4)
    p.put(box(32, 156, 170, 230), 'W', 0.8)
    for r_ in range(8):
        ry = 162 + r_ * 8
        p.put(box(32, ry, 170, ry + 1), 'T', 3.6)
        for b_ in range(10):
            bx_ = 40 + b_ * 9 + (14 if b_ >= 6 - (r_ % 3) else 0)
            col_ = 'H' if b_ in (4, 5) else 'E'
            p.put(ell(bx_, ry + 0.5, 3.6, 3.0), col_, 1.4 + lamp[ry, min(VW - 1, bx_)] * 1.6)
    # the tea glass in its holder, the pencil jar, the stamp pad
    gx, gy = 512, 196
    p.put(box(gx, gy, gx + 18, gy + 26), 'B', 3.0 + lamp[gy:gy + 26, gx:gx + 18].mean() * 1.6)
    p.put(box(gx + 2, gy + 2, gx + 16, gy + 24) & (np.mod(xx - gx, 3) == 0), 'B', 1.6)
    p.put(box(gx + 18, gy + 4, gx + 23, gy + 16) & ~box(gx + 18, gy + 7, gx + 20, gy + 13), 'B', 2.8)
    p.put(box(gx + 1, gy - 8, gx + 17, gy), 'A', 3.4)
    p.put(box(gx + 1, gy - 9, gx + 17, gy - 8), 'H', 1.4)
    p.put(box(gx + 12, gy - 22, gx + 13, gy - 6), 'H', 1.0)
    jar = box(200, 120, 220, 146)
    p.put(jar, 'T', 2.6 + lamp[jar] * 1.2)
    for k, px_ in enumerate((202, 207, 213)):
        p.put(p.line([(px_ + 2, 120), (px_ + k * 2, 96 + k * 4)], r=0.8), 'B' if k != 1 else 'E', 3.0)
    pad = box(520, 236, 584, 262)
    p.put(pad, 'T', 2.2)
    p.put(box(524, 240, 580, 258), 'V', 2.4 + nz[pad].mean())
    # the open freight ledger at the bottom left (ruled columns, handwriting)
    led = poly([(20, 262), (230, 254), (236, 330), (14, 338)])
    p.put(led, 'P', 4.2 + lamp[led] * 1.6 + nz[led] * 0.3)
    p.put(led & (np.mod(yy - 0.04 * xx, 9) < 1), 'P', 2.8)
    p.put(led & (np.abs(xx - 124) < 1), 'P', 2.2)
    for k in range(6):
        hw = Q.place(Q.hand_text_k(('24 318', '47 702', 'C-17/42', '19 044', '31 507', 'C-17/40')[k], 1, 0.2,
                                   6621 + k), VW, VH, 30 + (k % 2) * 104, 268 + (k // 2) * 18)
        p.put(hw & led, 'T', 1.4)
    # the card box at the right edge, its label
    bx = box(588, 150, 640, 240)
    p.put(bx, 'W', 3.6 + lamp[bx] * 1.6)
    p.put(box(588, 150, 640, 154), 'W', 5.0)
    p.put(box(596, 186, 640, 206), 'X', 4.6)
    p.put(Q.text_at('C-17/45', VW, VH, 600, 190, 's'), 'K', 0.8)
    _kerosene_lamp(p, xx, yy)
    p.resolve(band=2.0)
    L['c3_lamp'] = list(C3_LAMP)
    L['ru_at'] = list(RU_AT)
    L['c3_tea'] = [gx + 9, gy - 10]
    return p.L.c


C3_WICK = (C3_LAMP[0], 112)             # the flame stands on the wick here (c3b)


def _kerosene_lamp(p, xx, yy):
    """The kerosene lamp of the siding booth: brass foot and font, the burner collar with its wick knob, the glass
    chimney (bulb and neck) lit from inside -- bright where the flame shines through, the glass walls darker and
    amber, a cold window highlight down the left, soot at the neck's top.  The flame is a runtime sprite."""
    lx, _ = C3_LAMP
    wx, wy = C3_WICK
    foot = ell(lx, 150, 26, 8) | box(lx - 10, 126, lx + 10, 150)
    p.put(foot, 'B', 2.6 + (lx + 10 - xx[foot]) / 20.0 * 1.6)
    p.put(ell(lx, 150, 26, 8) & (yy < 147), 'B', 4.6)
    font = ell(lx, 126, 18, 10)
    p.put(font, 'B', 2.8 + np.clip((lx + 6 - xx[font]) / 24.0, 0, 1) * 1.6 + np.clip((126 - yy[font]) / 10.0, 0, 1))
    p.put(font & C.rim(font, -1, -1), 'B', 5.0)
    p.put(font & (np.abs(yy - 127) < 1), 'B', 1.6)                                # the seam of the font
    collar = box(lx - 9, wy, lx + 10, wy + 7)
    p.put(collar, 'B', 2.2 + np.clip((lx + 8 - xx[collar]) / 18.0, 0, 1) * 2.2)
    p.put(box(lx - 9, wy, lx + 10, wy + 1), 'B', 5.2)
    p.put(collar & (np.mod(xx, 3) == 0) & (yy > wy + 2), 'B', 1.4)                # the vents of the burner
    p.put(ell(lx + 13, wy + 4, 3, 3), 'B', 3.2)                                    # wick knob
    p.put(ell(lx + 13, wy + 4, 1, 1), 'B', 5.2)
    # the chimney: bulb + neck; the glass glows where the flame is behind it
    bulb = ell(lx, wy - 14, 12, 15)
    neck = box(lx - 5, 60, lx + 6, wy - 24)
    flare = ell(lx, 60, 7, 2)
    chim = (bulb | neck | flare) & (yy < wy)
    half = np.where(neck & ~bulb, 5.5, 12.0)
    r = np.clip(np.abs(xx + 0.5 - lx) / half, 0, 1)
    glow_ = np.clip(1.0 - np.hypot((xx - wx) / 11.0, (yy - (wy - 9)) / 15.0), 0, 1)
    p.put(chim, 'A', 4.0 + glow_[chim] * 3.6 - r[chim] ** 2 * 1.8 + (yy[chim] > wy - 4) * 0.6)
    p.put(chim & C.rim(chim, 0, 0, 1), 'A', 3.0)                                   # the glass walls' edge
    p.put(chim & (np.abs(xx + 0.5 - (lx - 7)) < 1.0) & (yy > 70) & (yy < wy - 6), 'X', 6.0)   # window highlight
    p.put(neck & (np.abs(xx + 0.5 - (lx - 3)) < 0.6) & (yy < 80), 'X', 5.0)
    p.put(box(lx - 6, 58, lx + 7, 62) & ~flare | (flare & (yy < 60)), 'K', 1.2)  # soot on the rim
    L['c3_wick'] = [wx, wy]
    L['c3_flame_at'] = [wx - FLAME_W // 2, wy - (FLAME_H - 2)]


def c4_bg2():
    """Over Alexei's shoulder: the booth's board wall in the kerosene light, the window onto the siding hall --
    the level's own hall re-lit by its work lamp, wagon 24 318 / C-17/45 under it -- seen through dirty glass with
    frost in the corners and a warm reflection of the lamp; the desk edge below."""
    import env_c4_cine_levelart as LA
    import env_c4_cine_levelplates as LP
    R = Q.ramps(W=OAKK, A=AMBER, K=KNIGHT, I=IRONK, R=RUST, X=CREAM,
                Y=['#0E1014', '#1A1E24', '#2A3038', '#3E4650', '#566270', '#76828E', '#A2AAB2', '#D2D6D8'])
    p = C.Paint(VW, VH, R, 'c4b')
    yy, xx = p.yy, p.xx
    nz = Q.noise(VW, VH, 12, 6711)
    grain = Q.noise(VW, VH, 3, 6713)
    lamp = Q.lightfield(VW, VH, [(-40, 220, 420, 1.0, 1.2)])
    p.put(yy >= 0, 'W', 1.2 + nz * 0.5 + grain * 0.4 + lamp * 3.0 - (np.mod(xx, 30) < 1) * 0.8)
    p.put(np.mod(xx, 30) == 1, 'W', 2.0 + lamp[np.mod(xx, 30) == 1] * 2.6)
    x0, y0, x1, y1 = C4_WIN
    fr = box(x0 - 10, y0 - 10, x1 + 10, y1 + 10) & ~box(x0, y0, x1, y1)
    p.put(fr, 'W', 2.6 + lamp[fr] * 2.0)
    p.put(box(x0 - 10, y0 - 10, x1 + 10, y0 - 8), 'W', 4.0)
    p.put(box(x0 - 14, y1 + 8, x1 + 14, y1 + 16), 'W', 3.6 + lamp[y1 + 8:y1 + 16, x0:x1].mean() * 2.0)
    p.put(box(x0 - 14, y1 + 8, x1 + 14, y1 + 9), 'W', 5.0)
    desk = yy >= 284
    p.put(desk, 'W', 3.0 + nz[desk] + lamp[desk] * 2.6)
    p.resolve(band=2.0)
    room = p.L.c.copy()
    # the view: the level's hall through the glass
    view = LP.booth_view().astype(np.float32) / 255.0
    vh, vw = view.shape[:2]
    out = room.astype(np.float32) / 255.0
    win = np.zeros((VH, VW), bool)
    win[y0:y1, x0:x1] = True
    canvas = np.zeros_like(out)
    LA.over(canvas, view, x0 - (vw - (x1 - x0)) // 2, y0 - (vh - (y1 - y0)) // 2)
    # dirty glass: a cool veil, smudges, frost creeping in from the corners, the lamp's warm reflection
    veil = Q.noise(VW, VH, 22, 6715)
    g = canvas[..., :3] * (0.78 + veil[..., None] * 0.14) + np.asarray([0.035, 0.04, 0.05], np.float32)
    cx_, cy_ = (x0 + x1) / 2, (y0 + y1) / 2
    dxn = np.abs(xx - cx_) / ((x1 - x0) / 2)
    dyn = np.abs(yy - cy_) / ((y1 - y0) / 2)
    fn = Q.noise(VW, VH, 3, 6717)
    hw_, hh_ = (x1 - x0) / 2.0, (y1 - y0) / 2.0
    rc = np.hypot((1.0 - dxn) * hw_, (1.0 - dyn) * hh_)            # px from the nearest window corner
    reach = 18.0 + Q.noise(VW, VH, 7, 6719) * 22.0
    frost = (rc < reach) & win
    sparse = frost & (pg.bayer(VW, VH, 1, 2) > 0.35 + rc / np.maximum(reach, 1.0) * 0.5)
    g = np.where(sparse[..., None], g * 0.55 + np.asarray([0.66, 0.70, 0.74]) * 0.45, g)
    edge_f = frost & ~sparse & (fn > 0.5)
    g = np.where(edge_f[..., None], g * 0.8 + np.asarray([0.5, 0.54, 0.6]) * 0.2, g)
    refl = Q.lightfield(VW, VH, [(x0 + 40, y1 - 30, 60, 1.0, 1.5)])
    g = g + refl[..., None] * np.asarray([0.20, 0.12, 0.04])
    out[win, :3] = np.clip(g[win], 0, 1)
    out[win, 3] = 1.0
    # the muntins over the glass
    mun = win & ((np.abs(xx - (x0 + x1) / 2) < 3) | (np.abs(yy - (y0 + y1) / 2) < 3))
    mc = Q.hexrgb(OAKK[3]) / 255.0
    out[mun, :3] = mc * (0.8 + lamp[mun][:, None] * 0.6)
    out[mun & (np.abs(xx - (x0 + x1) / 2) < 1), :3] = Q.hexrgb(OAKK[5]) / 255.0
    L['c4_win'] = list(C4_WIN)
    L['c4_snow_clip'] = [x0, y0, x1 - x0, y1 - y0]
    return LA.to8(out)


def build(w):
    import env_c4_cine_figs as G
    w('card/card_de.png', card_de())
    w('card/c1_bg.png', c1_bg2())
    from env_c4_cine_places import figs_disk as FD
    if os.environ.get('ASHES_C4_FIGS_FROM_DISK') == '1' and os.path.exists(os.path.join(Q.OUT, 'card/c1_lthumb.png')):
        behind, thumb = FD('card/c1_lhand.png', None), FD('card/c1_lthumb.png', None)
    else:
        behind, thumb = G.c1_lhand()
    w('card/c1_lhand.png', behind)
    w('card/c1_lthumb.png', thumb)
    rh = FD('card/c1_rhand.png', G.c1_rhand)
    w('card/c1_rhand.png', rh)
    # place the left hand so the pinch lands on the card's upper-left corner, the right thumb on the edge
    ys, xs = np.nonzero(thumb[..., 3] > 0)
    if len(xs):
        k = np.argmax(xs + ys)
        tip = (int(xs[k]), int(ys[k]))
    else:
        tip = (110, 100)
    L['c1_lhand_at'] = [CARD_AT[0] + 14 - tip[0], CARD_AT[1] + 16 - tip[1]]
    ys, xs = np.nonzero(rh[..., 3] > 0)
    k = np.argmin(xs - (ys < rh.shape[0] * 0.7) * 0)
    L['c1_rhand_tip'] = [int(xs[k]), int(ys[k])]
    L['card_at'] = list(CARD_AT)
    c2 = c2_macro()
    w('card/c2_macro.png', c2)
    w('card/c2_paper.png', paper_layer(c2, 'left'))
    w('card/c3a_macro.png', c3a_macro())
    w('card/shadow.png', thumb_shadow())                # round 9 (kept for old references; no runtime uses it)
    # the macro digits (figures stream): Konrad's gloved thumb on the German half (the fingers behind the paper),
    # Alexei's bare index finger along the Russian half; canvas top-left = (macro_digit[side]) + (0, shadow_y)
    def _c2_raw():
        return G.c2_thumb()
    if os.environ.get('ASHES_C4_FIGS_FROM_DISK') == '1' and os.path.exists(os.path.join(Q.OUT, 'card/c2_thumb.png')):
        b_, f_ = FD('card/c2_thumb_back.png', None), FD('card/c2_thumb.png', None)
        raw = np.where((b_[..., 3] > 0)[..., None], b_, f_)               # the union is the render again
    else:
        raw = _c2_raw()
    behind, front = split_thumb(raw)
    w('card/c2_thumb_back.png', behind)
    w('card/c2_thumb.png', front)
    w('card/c3_finger.png', FD('card/c3_finger.png', G.c3_finger))
    # (+6: at the shot's first frame the sleeve's cut end stays under the letterbox)
    L['macro_digit'] = {s: [EDGE_X - G.MACRO_OFF[s][0], 60 - G.MACRO_OFF[s][1] + 6] for s in ('de', 'ru')}
    w('card/bokeh.png', bokeh_sheet())
    w('card/card_ru.png', card_ru_desk())
    w('card/c3b_desk.png', c3b_desk2())
    w('card/flame.png', lamp_flame())
    w('card/lamp_glow.png', Q.glow_sprite(VW, VH, [(C3_LAMP[0], C3_LAMP[1], 230, 190, (70, 44, 14), 1.3),
                                                   (C3_LAMP[0], C3_LAMP[1], 26, 30, (90, 60, 20), 1.5)], 6.0))
    hand = FD('card/c3_hand.png', G.c3_hand)
    w('card/c3_hand.png', hand)
    L['c3_hand_at'] = [RU_AT[0] - 172, RU_AT[1] - 50]
    w('card/c4_bg.png', c4_bg2())
    w('card/c4_alexei.png', FD('card/c4_alexei.png', lambda: Q.sheet([G.c4_back(0), G.c4_back(1)])))
    L['c4_alexei_at'] = list(G.C4_AT)
    w('card/c4_lampglow.png', Q.glow_sprite(VW, VH, [(-20, 240, 300, 220, (60, 38, 12), 1.3)], 6.0))
