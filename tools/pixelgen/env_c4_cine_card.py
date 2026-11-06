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

import numpy as np

import env_c4_cine_kit as Q
from env_c4_cine_kit import (C, VW, VH, KNIGHT, AMBER, RUST, CREAM, OAKK, IRONK, DAWN, SNOWB, SODIUM, PINE,
                             PAPERB, INKRED, VIOLET, box, ell, poly, grid)
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
    # out-of-focus snow beyond the edge: soft blue with a few bokeh discs
    p.put(yy >= 0, 'S', 3.6 + (yy / VH) * 1.6 + Q.noise(VW, VH, 60, 6301, octaves=2) * 1.2)
    for (bx, by, br) in ((420, 90, 22), (560, 160, 30), (480, 270, 18), (610, 60, 14), (380, 200, 12)):
        d = ell(bx, by, br, br)
        p.put(d, 'S', 6.4 + Q.noise(VW, VH, 30, 6303)[d] * 0.6)
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
    p.put(yy >= 0, 'W', 2.6 + Q.noise(VW, VH, 50, 6401, octaves=2) * 1.6 + light * 1.4 + (xx / VW) * 0.8)
    for (bx, by, br) in ((120, 100, 26), (220, 240, 18), (60, 280, 30)):
        d = ell(bx, by, br, br)
        p.put(d, 'A', 3.6 + Q.noise(VW, VH, 30, 6403)[d] * 0.6)
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


def lamp_flame():
    """4 frames of a small kerosene flame behind the chimney glass (bottom-anchored, 10 x 16)."""
    out = []
    for i in range(4):
        a = np.zeros((16, 10, 3), np.float32)
        sway = (i - 1.5) * 0.4
        Q.add_glow(a, 5 + sway, 9, 3.4, 7.0 + (i % 2) * 0.6, (255, 190, 90), 1.2)
        Q.add_glow(a, 5 + sway * 0.5, 11, 1.6, 3.0, (255, 240, 200), 1.4)
        out.append(Q.K.soft_quant(a, 12.0))
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


def build(w):
    import env_c4_cine_figs as G
    w('card/card_de.png', card_de())
    w('card/c1_bg.png', c1_bg())
    behind, thumb = G.c1_lhand()
    w('card/c1_lhand.png', behind)
    w('card/c1_lthumb.png', thumb)
    rh = G.c1_rhand()
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
    w('card/c2_macro.png', c2_macro())
    w('card/c3a_macro.png', c3a_macro())
    w('card/shadow.png', thumb_shadow())
    w('card/card_ru.png', card_ru_desk())
    w('card/c3b_desk.png', c3b_desk())
    w('card/flame.png', lamp_flame())
    w('card/lamp_glow.png', Q.glow_sprite(VW, VH, [(C3_LAMP[0], C3_LAMP[1], 230, 190, (70, 44, 14), 1.3),
                                                   (C3_LAMP[0], C3_LAMP[1], 26, 30, (90, 60, 20), 1.5)], 6.0))
    hand = G.c3_hand()
    w('card/c3_hand.png', hand)
    L['c3_hand_at'] = [RU_AT[0] - 172, RU_AT[1] - 50]
    w('card/c4_bg.png', c4_bg())
    w('card/c4_alexei.png', Q.sheet([G.c4_back(0), G.c4_back(1)]))
    L['c4_alexei_at'] = list(G.C4_AT)
