"""env_c4_cine_voices -- art of LS_C4_Voices, the closing of Chapter 4 part 1 (owner: cine stream, round 9).

  v1  Berlin morning: Konrad climbs out of the service door of the advertising column S 2 (plate: the loop in
      morning light, env_c4_cine_places.berlin_loop('morning')) -- the Lindner file under his coat or empty-handed
  v2  Marta's tram leaves the loop, Ilse at the last window; Konrad from behind in the foreground (portrait
      pipeline) -- one bell, or two bells and he raises his hand (and Ilse hers on the glass)
  v3  Karsk: Alexei and Lev climb out of the cellar stair into the dark yard under the green signal (plate shared
      with LS_C4_Homeward w3) -> insert: Alexei's notebook with the four numbers of the one wagon
  v4  the siding: wagon C-17/45 alone under its work lamp; the lamp goes out (lit / dark plates)
  v5  black; the caption
Runtime: scenes/cinematics/ch4_voices/ch4_voices.gd (anchors in layout.json "voices").
"""
from __future__ import annotations

import numpy as np

import env_c4_cine_kit as Q
from env_c4_cine_kit import (C, VW, VH, KNIGHT, AMBER, CREAM, SIGNAL, SNOWK, IRONK, PAPERB, OAKK, box, ell, poly,
                             grid)
import env_c4_cine_places as P

L = Q.LAYOUT.setdefault('voices', {})

V1_OFF = -330                          # plate offset of v1 (the column at the centre)
V2_OFF = -150                          # plate offset of v2
NUMBERS = ['24 318', 'C-17/42', '47 702', 'C-17/45']   # the puzzle's order (C4_DESIGN §2.7): one wagon


def v1_door():
    """The column's service door standing open (leaf swung out to the right), the dark inside breathing warm
    air; drawn in plate coordinates over the morning plate."""
    w = P.LOOP_W
    R = Q.ramps(K=IRONK, A=AMBER)
    p = C.Paint(w, VH, R, 'v1door')
    d0, dy0, d1, dy1 = P.LOOP_DOOR
    p.put(box(d0, dy0, d1, dy1, w), 'K', 0.4)
    p.put(box(d0 + 2, dy1 - 10, d1 - 2, dy1, w), 'A', 1.6)
    leaf = poly([(d1, dy0), (d1 + 9, dy0 + 3), (d1 + 9, dy1 + 1), (d1, dy1)], w)
    p.put(leaf, 'K', 2.6)
    p.put(leaf & C.rim(leaf, 1, 0), 'K', 4.6)
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
    """Insert: the notebook page under the green signal: the four numbers of the one wagon in pencil, the last
    one underlined twice; snow lands on the page (runtime)."""
    R = Q.ramps(P=['#0C1A12', '#14281C', '#1E3A28', '#2C5038', '#406A4C', '#5E8C66', '#86B48A', '#B4DCB2'],
                G=['#06100A', '#0C1A12', '#14281C'], K=KNIGHT, Q=['#0A0F0C', '#14201A', '#203428', '#2E4A38'])
    p = C.Paint(VW, VH, R, 'v3note')
    yy, xx = p.yy, p.xx
    nz = Q.noise(VW, VH, 12, 9101)
    sig = Q.lightfield(VW, VH, [(560, -60, 600, 1.0, 1.1)])
    p.put(yy >= 0, 'K', 0.6 + nz * 0.6)
    page = poly([(120, 60), (548, 48), (560, 318), (108, 330)])
    p.put(page, 'P', 3.0 + sig[page] * 2.6 + Q.noise(VW, VH, 2, 9103)[page] * 0.5)
    p.put(page & (np.mod(yy - 48 + (xx - 108) * 0.03, 24) < 1), 'P', 2.4 + sig[page & (np.mod(
        yy - 48 + (xx - 108) * 0.03, 24) < 1)] * 1.2)
    p.put(page & C.rim(page, 0, -1, 2), 'P', 6.0)
    for i, s in enumerate(NUMBERS):
        t = Q.place(Q.hand_text_k(s, 3, 0.18, 9105 + i), VW, VH, 170 + i * 6, 76 + i * 56)
        p.put(t & page, 'G', 0.6)
    for k in range(2):
        ul = p.line([(176, 76 + 3 * 56 + 30 + k * 5), (420, 70 + 3 * 56 + 32 + k * 5)], r=0.9)
        p.put(ul & page, 'G', 0.8)
    arrow = p.line([(470, 98), (480, 260)], r=0.9) | p.line([(470, 248), (480, 262), (492, 250)], r=0.9)
    p.put(arrow & page, 'G', 1.0)
    thumb = ell(140, 300, 40, 26) & ~page | (ell(140, 300, 40, 26) & (yy > 286))
    p.put(thumb, 'Q', 1.6 + sig[thumb] * 1.6)
    p.resolve(band=2.0)
    return p.L.c


def build(w):
    w('voices/v1_door.png', v1_door())
    w('voices/v1_file.png', v1_file())
    look = Q.LIGHT_MORNING_B
    sk, ik = Q.fig_sheet('konrad', [('walk_side', None, True), ('idle_side', None, True)], look)
    w('voices/v1_konrad.png', sk)
    L['v1_konrad'] = ik
    L['v1_off'] = V1_OFF
    L['v1_walk'] = [P.LOOP_DOOR[0] + 12, P.LOOP_DOOR[0] - 150]
    import env_c4_cine_figs as G
    w('voices/v2_konrad.png', Q.sheet([G.v2_konrad(0), G.v2_konrad(1), G.v2_konrad(2)]))
    L['v2_konrad_at'] = list(G.V2_AT)
    L['v2_off'] = V2_OFF
    sa, ia = Q.fig_sheet('alexei', [('walk_side', None, True), ('idle_side', None, True)], Q.LIGHT_SIGNAL)
    w('voices/v3_alexei.png', sa)
    L['v3_alexei'] = ia
    sl, il = Q.fig_sheet('lev', [('walk_side', None, True), ('idle_side', None, True)], Q.LIGHT_SIGNAL,
                         standin='worker_b')
    w('voices/v3_lev.png', sl)
    L['v3_lev'] = il
    w('voices/v3_note.png', v3_note())
    w('voices/lantern.png', Q.glow_sprite(64, 64, [(32, 32, 26, 26, (110, 70, 24), 1.4),
                                                   (32, 32, 4, 5, (160, 120, 60), 1.6)], 6.0))
    L['numbers'] = NUMBERS
