"""env_c4_cine_stamp -- art of LS_C4_Stamp (owner: cine stream, round 9; C4_DESIGN §2.9).

The third match cut, on the rubber-stamp gesture:
  s1  the siding office desk from above: Alexei copies the card into his notebook (the pencil line grows),
      Lev's hand slides the Russian half back into the box „C-17/45 – ПРИНЯТЬ“
  s2  overhead insert: Lev's stamp comes down on the slip beside the box -- ПРИНЯТЬ (violet)
  s3  match cut: the registrar's stamp comes down at the same place -- ABGANG (red), same frame (s3a) -> the
      counter „Auskunft · Abgleich“ of the annex: Fengler's hands, the perforating machine splitting a card,
      the cabinets, the typists behind glass (s3b)
  s4  the foot of the shaft ladder between the card cabinets: Konrad, the German half in his coat
Runtime: scenes/cinematics/ch4_stamp/ch4_stamp.gd (anchors in layout.json "stamp").
"""
from __future__ import annotations

import numpy as np

import env_c4_cine_kit as Q
from env_c4_cine_kit import (C, VW, VH, KNIGHT, AMBER, OAKK, IRONK, CREAM, VIOLET, FLUO, STEEL, PAPERB, INKRED,
                             DAWN, NAVYB, box, ell, poly, grid)
import pg

L = Q.LAYOUT.setdefault('stamp', {})

STAMP_C = (320, 188)                   # centre of both impressions (s2 / s3a): the match point
BOX = (300, 50, 448, 156)              # the card box on the desk (s1): x0, y0 (back top), x1, y1 (front bottom)
BOX_SLOT = (370, 86)                   # where the card goes in (the gap between the cards)
NOTE_LINES = [(70, 206, 'КОВАЛЕНКО А. П.'), (70, 226, '1926, ХАРЬКОВ'), (70, 246, '→ ФИЛЬТР. КАРСК'),
              (70, 266, 'C-17/45  ВТ 23.40')]


# ======================================================================================= s1
def s1_desk():
    R = Q.ramps(W=OAKK, A=AMBER, P=CREAM, K=KNIGHT, I=IRONK, G=['#1A1E22', '#2A3036', '#3E464E', '#56606A'],
                V=VIOLET)
    p = C.Paint(VW, VH, R, 's1')
    yy, xx = p.yy, p.xx
    nz = Q.noise(VW, VH, 10, 7101)
    lamp = Q.lightfield(VW, VH, [(120, -40, 560, 1.0, 1.15)])
    p.put(yy >= 0, 'W', 2.6 + nz * 0.8 + lamp * 3.2 + Q.noise(VW, VH, 3, 7103) * 0.4)
    p.put(np.mod(yy + np.floor(xx / 200) * 5, 24) < 1, 'W', 1.6 + lamp[np.mod(yy + np.floor(xx / 200) * 5, 24) < 1])
    # the open notebook: two pages, ruled, the spine; the pencil writing is revealed at runtime
    nb = box(40, 180, 340, 300)
    p.put(nb, 'P', 4.4 + nz[nb] * 0.4 + lamp[nb] * 1.4)
    p.put(nb & (np.mod(yy - 180, 20) == 19), 'G', 3.0)
    p.put(box(188, 180, 192, 300), 'P', 2.6)
    p.put(box(40, 298, 340, 302), 'W', 1.2)
    old = [(210, 206, '24 318'), (210, 226, 'C-17/42'), (210, 246, '47 702')]
    for (x, y, s) in old:
        p.put(Q.place(Q.hand_text_k(s, 1, 0.2, 7105), VW, VH, x, y), 'G', 1.2)
    # the card box: open top with the cards standing in it, the front with the label
    x0, y0, x1, y1 = BOX
    top = box(x0, y0, x1, y0 + 40)
    p.put(top, 'W', 1.2 + lamp[top] * 1.4)
    for i in range(10):
        cy_ = y0 + 4 + i * 3
        p.put(box(x0 + 6, cy_, x1 - 6, cy_ + 2), 'P', 3.0 + (i % 3) * 0.4 + lamp[cy_, x0 + 40] * 1.0)
    p.put(box(x0 + 6, y0 + 34, x1 - 6, y0 + 38), 'K', 0.8)                      # the gap where 0417 goes
    p.put(box(x0, y0 + 40, x1, y1), 'W', 3.4 + lamp[y0 + 40:y1, x0:x1].mean() * 2.0)
    p.put(box(x0, y0 + 40, x1, y0 + 42), 'W', 5.0)
    lab = box(x0 + 22, y0 + 54, x1 - 22, y0 + 76)
    p.put(lab, 'P', 5.0)
    p.put(Q.text_at('C-17/45 – ПРИНЯТЬ', VW, VH, x0 + 26, y0 + 61, 's'), 'K', 0.8)
    # the stamp lying beside the box, the violet ink pad
    p.put(box(470, 96, 500, 124), 'W', 2.2)
    p.put(ell(485, 92, 9, 9), 'W', 4.0)
    p.put(box(510, 92, 580, 132), 'I', 2.0)
    p.put(box(514, 96, 576, 128), 'V', 2.6 + nz[96:128, 514:576].mean())
    p.resolve(band=2.0)
    L['box'] = list(BOX)
    L['box_slot'] = list(BOX_SLOT)
    L['note_lines'] = [[x, y] for (x, y, _) in NOTE_LINES]
    return p.L.c


def s1_boxfront():
    """The box's front wall + label, drawn over the card that slides into the box."""
    R = Q.ramps(W=OAKK, P=CREAM, K=KNIGHT)
    p = C.Paint(VW, VH, R, 's1front')
    x0, y0, x1, y1 = BOX
    lamp = Q.lightfield(VW, VH, [(120, -40, 560, 1.0, 1.15)])
    p.put(box(x0, y0 + 40, x1, y1), 'W', 3.4 + lamp[y0 + 40:y1, x0:x1].mean() * 2.0)
    p.put(box(x0, y0 + 40, x1, y0 + 42), 'W', 5.0)
    p.put(box(x0 + 22, y0 + 54, x1 - 22, y0 + 76), 'P', 5.0)
    p.put(Q.text_at('C-17/45 – ПРИНЯТЬ', VW, VH, x0 + 26, y0 + 61, 's'), 'K', 0.8)
    p.resolve(band=2.0)
    return p.L.c


def notes():
    """Alexei's pencil lines (runtime reveals them left to right as the pencil moves)."""
    R = Q.ramps(G=['#1A1E22', '#2A3036', '#3E464E', '#56606A'])
    p = C.Paint(VW, VH, R, 'notes')
    for (x, y, s) in NOTE_LINES:
        p.put(Q.place(Q.hand_text_k(s, 1, 0.2, 7107 + y), VW, VH, x, y), 'G', 0.8)
    p.resolve(band=2.0)
    return p.L.c


def card_small():
    """The Russian half in Lev's fingers (s1), 66 x 40, perforation on the left."""
    w, h = 66, 40
    R = Q.ramps(P=['#2A241A', '#463C2C', '#665840', '#887654', '#A89470', '#C8B48E', '#E2D0AA', '#F2E4C4'],
                I=['#1A1612', '#2C241E', '#3E342A'], V=VIOLET)
    p = C.Paint(w, h, R, 'card_s')
    paper = Q.torn_edge_mask(h, w, 1.0, Q.perforation(12, 4.0, 1.0, 417), 'right', y0=0.0, scale=1.0)
    p.put(paper, 'P', 4.4 + Q.noise(w, h, 3, 7111)[paper])
    for i in range(4):
        p.put(box(6, 6 + i * 7, 6 + (40 if i else 24), 7 + i * 7, w, h) & paper, 'I', 1.6)
    p.put(Q.place(Q.stamp_mask('ПРИНЯТЬ', k=1, frame=(30, 12), angle=-4, seed=7113)[2:-2, 2:-2], w, h, 30, 22) &
          paper, 'V', 3.4)
    p.resolve(band=2.0)
    return p.L.c


# ======================================================================================= s2 / s3a (overhead inserts)
def s2_slip():
    """The paper slip on the box's side, overhead, kerosene light: ruled form, Cyrillic headings."""
    R = Q.ramps(P=['#2A241A', '#463C2C', '#665840', '#887654', '#A89470', '#C8B48E', '#E2D0AA', '#F2E4C4'],
                I=['#1A1612', '#2C241E', '#3E342A'], W=OAKK)
    p = C.Paint(VW, VH, R, 's2')
    yy, xx = p.yy, p.xx
    lamp = Q.lightfield(VW, VH, [(-60, -40, 760, 1.4, 1.1)])
    p.put(yy >= 0, 'W', 2.0 + Q.noise(VW, VH, 20, 7201) + lamp * 2.4)
    slip = box(60, 56, 600, 316)
    p.put(slip, 'P', 4.2 + Q.noise(VW, VH, 2, 7203)[slip] * 0.6 + lamp[slip] * 1.4)
    p.put(slip & (np.mod(yy - 56, 30) == 29), 'I', 2.6)
    p.put(Q.place(Q.smooth_up(Q.text('ГРУЗ: СЛУЖЕБНЫЙ  ВАГОН C-17/45', 's', 1), 2), VW, VH, 80, 66), 'I', 1.2)
    p.put(Q.place(Q.smooth_up(Q.text('ОТПРАВИТЕЛЬ:', 's', 1), 2), VW, VH, 80, 280), 'I', 1.2)
    p.resolve(band=2.0)
    return p.L.c


def s3_card():
    """The annex's index card, overhead, flat fluorescent light: printed fields in German."""
    R = Q.ramps(P=PAPERB, I=['#16181A', '#24282A', '#363C3C'], F=FLUO, R=INKRED)
    p = C.Paint(VW, VH, R, 's3a')
    yy, xx = p.yy, p.xx
    light = Q.lightfield(VW, VH, [(320, -200, 800, 1.0, 1.0)])
    p.put(yy >= 0, 'F', 3.0 + Q.noise(VW, VH, 30, 7301) * 0.8 + light * 1.4)
    card = box(56, 52, 600, 318)
    p.put(card, 'P', 5.0 + Q.noise(VW, VH, 2, 7303)[card] * 0.5 + light[card] * 1.2)
    p.put(card & (np.mod(yy - 52, 30) == 29), 'F', 5.0)
    p.put(box(56, 52, 120, 84), 'R', 3.4)
    p.put(Q.place(Q.smooth_up(Q.text('C-17', 's', 1), 2), VW, VH, 68, 62), 'P', 7.6)
    p.put(Q.place(Q.smooth_up(Q.text('ZENTRALE ERFASSUNGSSTELLE · NEBENSTELLE SÜD', 's', 1), 2), VW, VH, 132, 62),
          'I', 1.2)
    p.put(Q.place(Q.smooth_up(Q.text('VORGANG:', 's', 1), 2), VW, VH, 76, 280), 'I', 1.2)
    p.resolve(band=2.0)
    return p.L.c


def impression(word, ink, seed, angle):
    m = Q.stamp_mask(word, k=4, seed=seed, angle=angle)
    pal = {'violet': '#5E4486', 'red': '#A8301E'}[ink]
    dark = {'violet': '#48326C', 'red': '#7A2216'}[ink]
    out = Q.flat(m, pal)
    heavy = m & (Q.noise(m.shape[1], m.shape[0], 3, seed + 5) > 0.62)
    Q.flat(heavy, dark, out)
    return out


def stamp_top(city):
    """The stamp seen from above as it comes down: the block (wood in Karsk, black bakelite in Berlin) and the
    knob; the hand on the knob is composited at runtime (figs)."""
    fw, fh = Q.STAMP_FRAME
    w, h = fw + 24, fh + 24
    R = Q.ramps(W=OAKK if city == 'karsk' else ['#08090A', '#101214', '#1A1D20', '#262A2E', '#343A3E', '#464C50',
                                                 '#5C6266'],
                M=['#20180E', '#3A2C18', '#5A4426', '#7E6038', '#A07C4A'] if city == 'karsk' else
                ['#14181A', '#262C30', '#3C4448', '#566066', '#7A848A', '#A8B0B4'])
    p = C.Paint(w, h, R, 'stamp_' + city)
    yy, xx = p.yy, p.xx
    blk = Q.C.rrect_mask(w, h, 2, 2, w - 2, h - 2, 5)
    p.put(blk, 'W', 2.6 + Q.noise(w, h, 6, 7401)[blk] * 1.0 - (yy[blk] / h) * 0.8)
    p.put(blk & C.rim(blk, -1, -1, 2), 'W', 5.0)
    p.put(blk & C.rim(blk, 1, 1, 2), 'W', 1.0)
    p.put(ell(w / 2, h / 2, 26, 22, w, h), 'M', 2.2)
    p.put(ell(w / 2 - 6, h / 2 - 6, 10, 8, w, h), 'M', 4.0)
    p.resolve(band=2.0)
    return p.L.c


# ======================================================================================= s3b (the counter)
S3_PERF = (96, 120)                    # the perforating machine (lever pivot)
S3_SPLIT = (78, 214)                   # the card it splits (top-left)


def s3b_counter():
    R = Q.ramps(F=FLUO, T=STEEL, P=PAPERB, I=['#16181A', '#24282A', '#363C3C'], K=['#08090A', '#121416', '#1E2124',
                                                                                 '#2C3034', '#3E4448'],
                C=['#141618', '#202426', '#2E3436', '#3E4446', '#50585A', '#646C6E'],
                N=['#1E2620', '#2C382E', '#3C4A3E', '#4E5E50', '#627464'], R=INKRED)
    p = C.Paint(VW, VH, R, 's3b')
    yy, xx = p.yy, p.xx
    nz = Q.noise(VW, VH, 12, 7501)
    tube = Q.lightfield(VW, VH, [(320, -40, 520, 1.0, 1.0)])
    # the card hall behind: steel cabinets to the ceiling, drawers with brass-less label holders
    back = yy < 150
    p.put(back, 'T', 2.0 + nz[back] * 0.5 + tube[back] * 2.6)
    p.put(back & (np.mod(yy, 18) == 0), 'T', 1.0)
    p.put(back & (np.mod(xx, 46) == 0), 'T', 1.0)
    p.put(back & (np.mod(yy, 18) == 8) & (np.mod(xx, 46) > 18) & (np.mod(xx, 46) < 28), 'P', 4.6)
    # the typists' glass partition at the right: blurred figures behind it (life)
    gl = box(400, 46, 640, 150)
    p.put(gl, 'F', 4.4 + nz[gl] * 0.6 + tube[gl] * 1.4)
    for gx in (436, 520, 596):
        fig = (ell(gx, 140, 24, 18) & (yy < 150)) | ell(gx, 108, 8, 10)
        p.put(fig & gl, 'F', 3.0)
        p.put(fig & gl & C.rim(fig, 0, -1, 2), 'F', 3.8)
    p.put(box(400, 46, 404, 150) | box(400, 96, 640, 98), 'T', 3.4)
    # Fengler himself, leaning over the counter: the grey dust coat over his chest between the upper arms of
    # s3b_hands (they run up into the letterbox to his shoulders, G.S3M_SHOULDERS), the V of shirt and tie, the
    # lapel badge without insignia, pencils in the breast pocket; his head is above the frame
    import env_c4_cine_figs as G
    (lsx, _ly), (rsx, _ry) = G.S3M_SHOULDERS
    chest = poly([(lsx - 22, 30), (rsx + 22, 30), (rsx + 8, 100), (rsx - 4, 150), (lsx + 4, 150), (lsx - 10, 100)])
    cx_ = (lsx + rsx) / 2.0
    p.put(chest, 'C', 2.8 + nz[chest] * 0.3 + tube[chest] * 1.2 - np.abs(xx[chest] - cx_) / 90.0 * 0.9
          - (yy[chest] - 30) / 120.0 * 0.5)
    vee = poly([(cx_ - 16, 30), (cx_ + 16, 30), (cx_, 92)])
    p.put(vee, 'P', 6.2 - (yy[vee] - 30) / 62.0 * 1.0)
    p.put(poly([(cx_ - 3, 34), (cx_ + 3, 34), (cx_ + 4, 80), (cx_, 88), (cx_ - 4, 80)]), 'K', 1.2)
    p.put(p.line([(cx_ - 24, 30), (cx_, 98)], r=0.7) | p.line([(cx_ + 24, 30), (cx_, 98)], r=0.7), 'C', 1.2)
    for by_ in (106, 126, 146):
        p.put(box(int(cx_) - 1, by_, int(cx_) + 1, by_ + 2), 'C', 0.8)
    p.put(ell(cx_ + 22, 52, 2.6, 2.6) & ~ell(cx_ + 22, 52, 1.2, 1.2), 'P', 4.0)
    p.put(box(int(cx_) + 30, 78, int(cx_) + 54, 80), 'C', 1.4)
    p.put(box(int(cx_) + 36, 68, int(cx_) + 38, 78), 'P', 5.0)
    p.put(box(int(cx_) + 42, 70, int(cx_) + 44, 78), 'R', 2.6)
    # the counter top: green-grey linoleum, a brass-less edge strip, the front panel
    top = (yy >= 150) & (yy < 300)
    p.put(top, 'N', 2.6 + nz[top] * 0.6 + tube[top] * 2.0 - (yy[top] - 150) / 150.0 * 0.6)
    p.put(top & (yy < 158) & (xx > lsx - 6) & (xx < rsx + 6), 'N', 1.6)            # his shadow at the far edge
    p.put(box(0, 298, VW, 304), 'T', 4.0)
    p.put(box(0, 304, VW, VH), 'K', 1.6)
    # the card stacks, forms, a pen tray
    for (cx, cy, n) in ((470, 168, 9), (536, 176, 6)):
        for i in range(n):
            p.put(box(cx, cy - i * 2, cx + 56, cy + 34 - i * 2), 'P', 4.4 + (i % 2) * 0.6)
    p.put(box(250, 250, 330, 270), 'K', 2.4)
    p.put(box(256, 254, 300, 258), 'R', 3.0)
    # the stamp under Fengler's right hand (block + knob), a fresh ABGANG beside it
    p.put(box(232, 206, 276, 226), 'K', 1.6)
    p.put(box(232, 206, 276, 208), 'K', 3.4)
    p.put(ell(254, 204, 7, 5), 'K', 2.8)
    imp = Q.place(Q.stamp_mask('ABGANG', k=1, frame=(40, 14), angle=2, seed=7505)[3:-3, 3:-3], VW, VH, 286, 214)
    p.put(box(282, 206, 346, 240), 'P', 5.0)
    p.put(imp, 'R', 3.4)
    # the perforating machine: cast-iron frame, the bed with the guide line
    px_, py_ = S3_PERF
    frame = poly([(40, 250), (150, 250), (150, 236), (118, 236), (110, py_ + 10), (82, py_ + 10), (76, 236),
                  (40, 236)])
    p.put(frame, 'K', 2.4 + nz[frame] * 0.6 + tube[frame] * 1.4)
    p.put(frame & C.rim(frame, 0, -1), 'K', 4.2)
    p.put(box(44, 210, 146, 236), 'K', 3.0)
    p.put(box(44, 222, 146, 223), 'R', 3.6)
    p.put(Q.text_at('SÜD 8', VW, VH, 54, 240, 's'), 'T', 6.0)
    p.resolve(band=2.0)
    L['s3_perf'] = list(S3_PERF)
    L['s3_split'] = list(S3_SPLIT)
    return p.L.c


def lever_sheet():
    """The perforator's lever, 3 frames (up, half, down), pivot at (12, 12) of a 120 x 100 cell."""
    out = []
    for ang in (-34.0, -14.0, 6.0):
        m = np.zeros((100, 120), bool)
        import math
        a = math.radians(ang)
        tip = (12 + 96 * math.cos(a), 12 + 96 * math.sin(a))
        m |= Q.thick([(12, 12), tip], 6.0, 120, 100)
        m |= Q.C.ellipse_mask(120, 100, tip[0], tip[1], 7, 7)
        m |= Q.C.ellipse_mask(120, 100, 12, 12, 8, 8)
        img = Q.flat(m, '#2C3034')
        Q.flat(m & C.rim(m, 0, -1), '#5A6266', img)
        Q.flat(Q.C.ellipse_mask(120, 100, tip[0], tip[1], 5, 5), '#1A1D20', img)
        out.append(img)
    return Q.sheet(out)


def split_card():
    """The card under the perforator, as two halves (left, right) 34 x 22 each."""
    w, h = 34, 22
    halves = []
    for side in ('left', 'right'):
        R = Q.ramps(P=PAPERB, R=INKRED, I=['#16181A', '#24282A'])
        p = C.Paint(w, h, R, 'split_' + side)
        paper = Q.torn_edge_mask(h, w, w - 1.0 if side == 'left' else 1.0, Q.perforation(6, 4.0, 1.0, 417), side,
                                 y0=0.0, scale=1.0)
        p.put(paper, 'P', 5.2)
        if side == 'left':
            p.put(box(0, 0, 8, 5, w, h), 'R', 3.6)
        for i in range(3):
            p.put(box(4, 7 + i * 4, 26, 8 + i * 4, w, h) & paper, 'I', 1.4)
        p.resolve(band=2.0)
        halves.append(p.L.c)
    return Q.sheet(halves)


# ======================================================================================= s4 (the ladder)
S4_LADDER = (150, 196)                 # x range of the ladder in the shaft
S4_KONRAD_X = 214


def s4_ladder():
    R = Q.ramps(F=FLUO, T=STEEL, K=['#08090A', '#121416', '#1E2124', '#2C3034', '#3E4448', '#545C60'],
                D=['#2A3446', '#3E4C62', '#56677E', '#7486A0', '#98A8BE', '#C2CEDC', '#E8EEF4'], P=PAPERB,
                C=['#121412', '#1C201C', '#282C28', '#363A36', '#464A44', '#5A5E56'])
    p = C.Paint(VW, VH, R, 's4')
    yy, xx = p.yy, p.xx
    nz = Q.noise(VW, VH, 12, 7601)
    tube = Q.lightfield(VW, VH, [(420, -20, 460, 1.0, 1.0)])
    day = Q.lightfield(VW, VH, [(172, 30, 220, 1.0, 1.1)])
    # the shaft at the left: concrete, the daylight falling in from the column's door far above
    shaft = xx < 236
    p.put(shaft, 'C', 1.4 + nz[shaft] * 0.8 + day[shaft] * 3.4 + tube[shaft] * 0.8)
    p.put(shaft & (np.mod(yy, 30) == 0), 'C', 0.8 + day[shaft & (np.mod(yy, 30) == 0)] * 2.0)
    open_ = box(136, 40, 212, 64)
    p.put(open_, 'D', 6.6)
    x0, x1 = S4_LADDER
    for lx in (x0, x1):
        rail = box(lx, 52, lx + 4, 300)
        p.put(rail, 'K', 2.4 + day[rail] * 2.4)
        p.put(box(lx, 52, lx + 1, 300), 'K', 4.6)
    for ry in range(64, 300, 14):
        rung = box(x0 + 4, ry, x1, ry + 3)
        p.put(rung, 'K', 3.0 + day[rung] * 2.4)
    # the card hall at the right: cabinets to the ceiling, a sliding ladder, the fluorescent tube
    hall = xx >= 236
    p.put(hall, 'T', 2.2 + nz[hall] * 0.5 + tube[hall] * 2.4)
    p.put(hall & (np.mod(yy, 20) == 0), 'T', 1.2)
    p.put(hall & (np.mod(xx - 236, 52) == 0), 'T', 1.0)
    lbl = hall & (np.mod(yy, 20) == 9) & (np.mod(xx - 236, 52) > 20) & (np.mod(xx - 236, 52) < 32)
    p.put(lbl, 'P', 4.8)
    p.put(Q.text_at('SÜD 1', VW, VH, 262, 216, 's') | Q.text_at('SÜD 2', VW, VH, 314, 216, 's'), 'K', 1.0)
    for lx in (452, 500):
        p.put(p.line([(lx, 300), (lx + 16, 60)], r=1.2), 'K', 3.0 + tube[150, lx] * 1.4)
    for ry in range(80, 300, 22):
        p.put(p.line([(452 + (300 - ry) * 16 / 240, ry), (500 + (300 - ry) * 16 / 240, ry)], r=0.6), 'K', 3.4)
    p.put(box(300, 46, 560, 52), 'F', 9.4)
    p.put(box(296, 44, 564, 46), 'T', 3.0)
    # the floor: linoleum
    fl = yy >= 300
    p.put(fl, 'C', 2.4 + nz[fl] * 0.4 + tube[fl] * 1.6 + day[fl] * 1.6)
    p.resolve(band=2.0)
    L['s4_ladder'] = list(S4_LADDER)
    L['s4_konrad_x'] = S4_KONRAD_X
    return p.L.c


# ======================================================================================= polish pass
def s1_desk2():
    """The siding-office desk from above in the kerosene light: worn oak with its grain and old ink rings, the
    open notebook (lines 1-2 written; 3-4 appear at runtime), the card box C-17/45 - ПРИНЯТЬ with the cards
    standing in it, the wooden stamp and the violet ink pad, a glass of tea in its holder seen from above, an
    ashtray with Lev's cigarette (its smoke at runtime), a ruler, a pencil stub and shavings, a stack of forms,
    the base of the lamp in the corner."""
    R = Q.ramps(W=OAKK, A=AMBER, P=CREAM, K=KNIGHT, I=IRONK, G=['#1A1E22', '#2A3036', '#3E464E', '#56606A'],
                V=VIOLET, B=['#2A1D0B', '#4A3415', '#73531F', '#9C7630', '#C49A48', '#E8C779'],
                T=['#1A1C20', '#2C2F34', '#40444A', '#585C62', '#74787C'],
                F=['#2A241A', '#463C2C', '#665840', '#887654', '#A89470', '#C8B48E', '#E2D0AA'],
                E=['#1A0A08', '#3A140E', '#6A2418', '#9A3A22', '#C8603A'])
    p = C.Paint(VW, VH, R, 's1b')
    yy, xx = p.yy, p.xx
    nz = Q.noise(VW, VH, 10, 7121)
    grain = np.sin(yy * 0.6 + Q.noise(VW, VH, 8, 7123) * 7.0) * 0.5 + 0.5
    lamp = Q.lightfield(VW, VH, [(120, -40, 560, 1.0, 1.15)])
    p.put(yy >= 0, 'W', 2.2 + nz * 0.7 + grain * 0.7 + lamp * 3.2)
    p.put(np.mod(yy + np.floor(xx / 200) * 5, 24) < 1, 'W', 1.4 + lamp[np.mod(yy + np.floor(xx / 200) * 5, 24) < 1])
    for (rx, ry, rr) in ((470, 250, 16), (560, 210, 12), (150, 120, 14)):          # old glass rings
        ring = ell(rx, ry, rr, rr * 0.8) & ~ell(rx, ry, rr - 2, rr * 0.8 - 2)
        p.put(ring, 'W', 1.6 + lamp[ring] * 2.0)
    # the stack of forms at the top left, slightly fanned
    for k in range(4):
        fm = Q.place(Q.rotate_mask(np.ones((60, 90), bool), -6 + k * 4, (74, 100)), VW, VH, 30 + k * 3, 20 + k * 2)
        p.put(fm, 'F', 4.2 + k * 0.4 + lamp[fm] * 1.2)
        p.put(fm & C.rim(fm, 0, -1), 'F', 6.0)
        p.put(fm & (np.mod(yy, 6) == 2) & (np.mod(xx, 11) < 8) & ~C.rim(fm, 0, 0, 2), 'G', 2.6)
    # the open notebook: two pages, ruled, the spine; the pencil writing is revealed at runtime
    nb = box(40, 180, 340, 300)
    p.put(nb, 'P', 4.4 + nz[nb] * 0.4 + lamp[nb] * 1.4)
    p.put(nb & (np.mod(yy - 180, 20) == 19), 'G', 3.0)
    p.put(box(188, 180, 192, 300), 'P', 2.6)
    p.put(box(40, 298, 340, 302), 'W', 1.2)
    p.put(box(36, 178, 344, 180), 'W', 1.4)
    p.put(nb & C.rim(nb, 0, -1), 'P', 6.0)
    old = [(210, 206, '24 318'), (210, 226, 'C-17/42'), (210, 246, '47 702')]
    for (x, y, s) in old:
        p.put(Q.place(Q.hand_text_k(s, 1, 0.2, 7105), VW, VH, x, y), 'G', 1.2)
    # the ruler, a pencil stub with shavings
    rul = box(352, 210, 362, 330)
    p.put(rul, 'B', 3.4 + lamp[rul] * 1.0)
    p.put(rul & (np.mod(yy, 5) == 0) & (xx < 356), 'W', 1.0)
    p.put(p.line([(380, 300), (408, 288)], r=1.6), 'E', 2.6)
    p.put(p.line([(406, 289), (412, 287)], r=1.0), 'W', 4.0)
    for k in range(5):
        p.put(ell(392 + k * 7, 312 + (k % 2) * 4, 3, 2), 'B', 2.4 + (k % 3) * 0.6)
    # the card box: open top with the cards standing in it, the front with the label
    x0, y0, x1, y1 = BOX
    top = box(x0, y0, x1, y0 + 40)
    p.put(top, 'W', 1.2 + lamp[top] * 1.4)
    for i in range(10):
        cy_ = y0 + 4 + i * 3
        p.put(box(x0 + 6, cy_, x1 - 6, cy_ + 2), 'P', 3.0 + (i % 3) * 0.4 + lamp[cy_, x0 + 40] * 1.0)
        if i % 4 == 1:
            p.put(box(x0 + 10 + i * 9, cy_ - 2, x0 + 22 + i * 9, cy_), 'E', 3.2)          # index tabs
    p.put(box(x0 + 6, y0 + 34, x1 - 6, y0 + 38), 'K', 0.8)
    p.put(box(x0, y0 + 40, x1, y1), 'W', 3.4 + lamp[y0 + 40:y1, x0:x1].mean() * 2.0)
    p.put(box(x0, y0 + 40, x1, y0 + 42), 'W', 5.0)
    lab = box(x0 + 22, y0 + 54, x1 - 22, y0 + 76)
    p.put(lab, 'P', 5.0)
    p.put(Q.text_at('C-17/45 – ПРИНЯТЬ', VW, VH, x0 + 26, y0 + 61, 's'), 'K', 0.8)
    # the wooden stamp lying by the box, the violet ink pad in its tin
    p.put(box(470, 96, 500, 124), 'W', 2.2)
    p.put(ell(485, 92, 9, 9), 'W', 4.0)
    p.put(ell(485, 92, 9, 9) & C.rim(ell(485, 92, 9, 9), -1, -1), 'W', 5.4)
    p.put(box(510, 92, 580, 132), 'I', 2.0)
    p.put(box(510, 92, 580, 93), 'I', 4.0)
    p.put(box(514, 96, 576, 128), 'V', 2.6 + nz[96:128, 514:576].mean())
    # the tea glass in its holder from above: brass rim, the dark tea, the spoon
    tx, ty = 470, 250
    p.put(ell(tx, ty, 18, 16), 'B', 3.2 + lamp[ty, tx] * 1.0)
    p.put(ell(tx, ty, 18, 16) & C.rim(ell(tx, ty, 18, 16), -1, -1, 2), 'B', 5.2)
    p.put(ell(tx, ty, 14, 12), 'A', 1.4)
    p.put(ell(tx - 4, ty - 4, 4, 3), 'A', 3.8)                                    # the lamp in the tea
    p.put(p.line([(tx + 4, ty + 2), (tx + 22, ty - 10)], r=1.0), 'T', 4.2)
    p.put(box(tx + 18, ty - 4, tx + 26, ty + 2), 'B', 3.0)                        # handle
    # the ashtray with the cigarette resting on its rim
    ax, ay = 586, 300
    p.put(ell(ax, ay, 22, 18), 'T', 2.4)
    p.put(ell(ax, ay, 16, 12), 'T', 1.2)
    for (ex, ey) in ((580, 298), (590, 304), (584, 306)):
        p.put(ell(ex, ey, 3, 2), 'T', 3.4)                                        # ash and a stub
    p.put(p.line([(566, 290), (548, 282)], r=1.2), 'P', 5.4)
    p.put(ell(566, 290, 1.6, 1.4), 'E', 4.6)                                      # the ember
    # the lamp's base in the top-right corner, its shadow
    p.put(ell(610, 30, 40, 32), 'B', 2.8 + lamp[30, 610] * 1.0)
    p.put(ell(610, 30, 26, 20), 'B', 4.0)
    p.resolve(band=2.0)
    L['box'] = list(BOX)
    L['box_slot'] = list(BOX_SLOT)
    L['note_lines'] = [[x, y] for (x, y, _) in NOTE_LINES]
    L['s1_ember'] = [566, 289]
    L['s1_tea'] = [tx - 4, ty - 6]
    return p.L.c


S3_TYPISTS = [(452, 92, 'a'), (548, 96, 'b')]   # top-left of the level's typist strips behind the glass


def s3b_back():
    """Behind the counter: the card hall of the annex as the level paints it (cabinets 'Haushaltskartei Süd',
    the sliding ladder, the tubes), re-lit and pushed back into the fluorescent haze."""
    import env_c4_cine_levelart as LA
    import env_c4_cine_levelplates as LP
    Ld = LA.layer('berlin_annex', 'annex', (150, 40, 790, 400 - 40))
    fl = LA.hexf('#E8F0E4')
    lights = [{'pos': (LP.ANNEX_X + x, 78), 'height': 30, 'rgb': fl, 'energy': 0.55, 'radius': 170}
              for x in (154, 274, 394, 514, 634)]
    a = LA.relight(Ld, (0.46, 0.50, 0.48), lights, origin=(LP.ANNEX_X + 150, 40), emis_k=1.0)
    a = LA.grade(a, mul=(0.86, 0.92, 0.88), add=(0.05, 0.07, 0.06), sat=0.8)        # the haze of depth
    out = np.zeros((VH, VW, 4), np.float32)
    out[..., 3] = 1.0
    out[..., :3] = np.asarray([0.10, 0.12, 0.11])
    LA.over(out, a, 0, -10)
    return LA.to8(LA.dither_quant(out, 36, seed=9))


def s3b_front():
    """The counter close-up drawn over the hall: the glazed partition of the typists' room (frosted, dithered so
    the hall and the typists show through), Fengler's chest between the arms of s3b_hands, the counter top, the
    stamp, the forms, the perforating machine."""
    full = s3b_counter()
    out = full.copy()
    # the old painted hall and the blob typists go: the band above the counter shows the level's hall
    out[:150, :, 3] = 0
    # keep Fengler's chest (painted in s3b_counter between his shoulders)
    import env_c4_cine_figs as G
    (lsx, _ly), (rsx, _ry) = G.S3M_SHOULDERS
    yy, xx = np.mgrid[0:VH, 0:VW]
    chest = poly([(lsx - 22, 30), (rsx + 22, 30), (rsx + 8, 100), (rsx - 4, 150), (lsx + 4, 150), (lsx - 10, 100)])
    keep = chest & (yy < 150)
    out[keep] = full[keep]
    # the frosted glass partition at the right: a dithered veil, mullions, the transom bar
    gl = box(400, 46, 640, 150)
    th = pg.bayer(VW, VH, 2, 1)
    veil = gl & (th > 0.62) & ~keep
    out[veil, :3] = np.array([150, 170, 156], np.uint8)
    out[veil, 3] = 255
    frame = (box(400, 46, 405, 150) | box(400, 96, 640, 99) | box(520, 46, 523, 150)) & ~keep
    out[frame, :3] = np.array([60, 70, 66], np.uint8)
    out[frame, 3] = 255
    L['s3_typists'] = [[x, y, k] for (x, y, k) in S3_TYPISTS]
    return out


def life_strip(name):
    from PIL import Image
    import env_c4_cine_levelart as LA
    import os
    p = os.path.join(LA.ENV, 'berlin_annex', 'life', name + '.png')
    return np.asarray(Image.open(p).convert('RGBA')).copy()


def s4_ladder2():
    """The foot of the shaft ladder in the card hall: the level's annex (shaft niche, ladder, the fans behind
    their grille, the card cabinets with the sliding ladders, the plan and the clock) re-lit by its tubes and the
    daylight falling down the shaft; a strip of the near-black cut pier at the left."""
    import env_c4_cine_levelart as LA
    import env_c4_cine_levelplates as LP
    off = 32                                   # (round 10: the cut pier only a narrow edge, not an 80 px band)
    room = LP.annex_ladder().astype(np.float32) / 255.0
    out = np.zeros((VH, VW, 4), np.float32)
    out[..., 3] = 1.0
    nz = Q.noise(VW, VH, 8, 7611)
    pier = np.clip(0.07 + nz[..., None] * 0.05, 0, 1) * np.asarray([1.0, 1.05, 1.1])
    out[:, :off + 26, :3] = pier[:, :off + 26]
    LA.over(out, room[:, :VW - off], off, 0)
    out[:, :off, :3] *= np.clip((np.arange(off)[None, :, None] / off) * 0.5 + 0.5, 0, 1)
    L['s4_ladder'] = [off + 38, off + 58]
    L['s4_konrad_x'] = off + 56
    L['s4_shaft_light'] = [off + 48, 46]
    return LA.to8(LA.dither_quant(out, 40, seed=11))


# ======================================================================================= s4 medium (round 10)
S4M_W = 660                            # both layers are a little wider than the frame: the camera drifts
S4M_AT = (186, 44)                     # top-left of Konrad's medium figure (figures stream, S4M_SIZE 230 x 300)
S4M_LADDER = (64, 152)                 # the ladder's stiles (outer x of the left one, inner x of the right one)


def s4_medium():
    """The medium shot of s4 (round 10; before the game-scale ending): the foot of the shaft ladder, close.
    hall  (far, opaque)  the card hall out of focus -- the cabinets' drawer fronts and handles softened, the tubes'
          long bright smears under the ceiling, a pale cold wash where the daylight from the shaft spills out
    niche (near, alpha)  the shaft niche at the left: the concrete back wall brightening toward the daylight above,
          the steel ladder in focus -- stiles, round rungs lit from above with snow on the top ones, the wall
          brackets -- a conduit, „SCHACHT 2“ stencilled and faded, the pier's edge catching the tubes' green
    Konrad (s4_konrad_medium) stands between them at S4M_AT, turned to the ladder, looking up."""
    W = S4M_W
    R = Q.ramps(H=['#080C0A', '#0E1612', '#16201A', '#1E2C24', '#283A30', '#344A3E', '#425C4E', '#546E60',
                   '#6C8678', '#8AA294', '#B0C4B8'],
                Y=['#5A6A5E', '#8A9C8E', '#BACCBC', '#E4F2E4', '#F8FFF6'],
                C=['#07090B', '#0C0F12', '#12161A', '#191E23', '#21272D', '#2B323A', '#38404A', '#48525C',
                   '#5C6670', '#768088', '#96A0A8'],
                T=STEEL, D=['#2A3648', '#3E4C62', '#56667E', '#74849A', '#98A8BA', '#C0CCD8', '#E4ECF2'],
                S=['#7E8B96', '#A4AEB6', '#CED6DC', '#EEF2F4'], K=KNIGHT, X=CREAM)
    # ---- the hall, out of focus
    h = C.Paint(W, VH, R, 's4m_hall')
    yy, xx = h.yy, h.xx
    nz = Q.noise(W, VH, 30, 7801, octaves=2)
    tubes = Q.lightfield(W, VH, [(x, 70, 150, 1.0, 1.25) for x in (300, 470, 640)])
    sharp = np.zeros((VH, W), np.float32)
    cab = (yy > 96) & (yy < 330)
    dx_ = np.mod(xx - 230, 24)
    dy_ = np.mod(yy - 100, 14)
    sharp += cab * (1.0 - ((dx_ < 2) | (dy_ < 2)) * 0.9)                       # drawer fronts and their gaps
    sharp += cab * ((np.abs(dx_ - 12) < 3) & (np.abs(dy_ - 7) < 1.5)) * 0.9    # the handles
    sharp += ((yy > 86) & (yy < 96)) * 1.3                                     # the cornice over the cabinets
    sharp -= (np.mod(xx - 230, 168) < 6) * cab * 0.8                           # the sliding ladders' rails
    soft = C.blur(C.blur(sharp, 3), 2)
    base = 2.0 + nz * 0.6 + tubes * 3.4 + soft * (1.0 + tubes * 1.4) + np.clip((yy - 260) / 100.0, 0, 1) * -0.8
    h.put(yy >= 0, 'H', base)
    for x0 in (230, 400, 570):                                                 # the tubes, smeared
        tube = (np.abs(yy - 66) < 2.5) & (xx > x0) & (xx < x0 + 120)
        h.put(tube, 'Y', 2.6 + (np.abs(yy - 66) < 1.2)[tube] * 1.4)
        halo = (np.abs(yy - 66) < 6) & (xx > x0 - 6) & (xx < x0 + 126) & ~tube
        h.put(halo, 'H', 8.0 + nz[halo] * 0.6)
    day = np.clip(1.0 - np.hypot((xx - 210) / 120.0, (yy - 60) / 160.0), 0, 1)
    dm = day > 0.2
    h.put(dm, 'H', base[dm] + day[dm] * 1.6)
    h.resolve(band=2.0)
    hall = h.L.c.copy()
    hall[..., 3] = 255
    # ---- the niche and the ladder (in focus)
    p = C.Paint(W, VH, R, 's4m_niche')
    yy, xx = p.yy, p.xx
    nz = Q.noise(W, VH, 9, 7803)
    fine = Q.noise(W, VH, 2, 7805)
    sky = np.clip(1.0 - (yy - 40) / 250.0, 0, 1) ** 1.6                       # daylight falling down the shaft
    beam = np.clip(1.0 - np.abs(xx - 108) / 120.0, 0, 1) * sky                 # brightest down its middle
    niche = xx < 232
    p.put(niche, 'C', 2.0 + nz[niche] * 0.8 + fine[niche] * 0.3 + sky[niche] * 3.6 + beam[niche] * 3.2)
    p.put(niche & (np.mod(yy + 7, 58) < 1), 'C', 1.4 + sky[niche & (np.mod(yy + 7, 58) < 1)] * 3.0)   # shuttering
    stain = niche & (Q.noise(W, VH, 5, 7807) > 0.68) & (yy > 120)
    p.put(stain, 'C', 1.6 + sky[stain] * 3.0)                                  # damp streaks
    side = xx < 26                                                             # the niche's own side wall
    p.put(side, 'C', 1.2 + nz[side] * 0.5 + sky[side] * 2.4)
    pier = (xx >= 206) & (xx < 232)
    p.put(pier, 'C', 2.0 + nz[pier] * 0.5 + sky[pier] * 2.0)
    p.put(pier & (xx >= 228), 'H', 6.6)                                        # its edge catches the tubes
    p.put(box(198, 40, 204, VH, W), 'T', 2.6 + sky[40:VH, 198:204].mean() * 2.0)  # the conduit
    p.put(box(198, 40, 199, VH, W), 'T', 4.4)
    for cy in range(60, VH, 64):
        p.put(box(196, cy, 206, cy + 3, W), 'T', 3.6)
    sign = box(155, 214, 195, 228, W)                                          # an enamel sign beside the ladder
    p.put(sign, 'X', 3.6 + sky[sign] * 1.4)
    p.put(sign & C.rim(sign, 0, 0, 1), 'K', 2.0)
    p.put(Q.text_at('SCHACHT 2', W, VH, 158, 217, 's') & sign, 'K', 0.6)
    p.put(box(157, 228, 194, 231, W) & (fine > 0.4), 'C', 1.0)                 # a rust run under it
    lx0, lx1 = S4M_LADDER
    for (a, b) in ((lx0, lx0 + 7), (lx1 - 7, lx1)):                         # the stiles
        stile = box(a, 40, b, VH, W)
        p.put(stile, 'T', 2.4 + sky[stile] * 3.6 + nz[stile] * 0.3)
        p.put(box(a, 40, a + 1, VH, W), 'D', 1.0 + sky * 5.0)
        p.put(box(b - 1, 40, b, VH, W), 'T', 1.2)
    for k, ry in enumerate(range(52, VH, 24)):                                 # the rungs
        rung = box(lx0 + 7, ry, lx1 - 7, ry + 4, W)
        p.put(rung, 'T', 2.2 + sky[ry, 100] * 3.4)
        p.put(box(lx0 + 7, ry, lx1 - 7, ry + 1, W), 'D', 1.4 + sky[ry, 100] * 5.0)
        p.put(box(lx0 + 7, ry + 3, lx1 - 7, ry + 4, W), 'T', 0.8)
        p.put(box(lx0 + 7, ry + 4, lx1 - 7, ry + 6, W) & (fine > 0.2), 'C', 1.0)   # its shadow on the wall
        if ry < 150:
            snow = box(lx0 + 7, ry - 1, lx1 - 7, ry, W) & (fine > 0.35 + k * 0.08)
            p.put(snow, 'S', 2.6 - k * 0.3)
    for by in range(88, VH, 72):                                               # wall brackets
        for (bx0, bx1) in ((lx0 - 10, lx0), (lx1, lx1 + 10)):
            p.put(box(bx0, by, bx1, by + 4, W), 'T', 1.8 + sky[by, 100] * 2.6)
    p.resolve(band=2.0)
    near = p.L.c.copy()
    near[..., 3] = np.where(xx < 232, 255, 0).astype(np.uint8)
    L['s4m_at'] = list(S4M_AT)
    L['s4m_w'] = W
    L['s4m_shaft'] = [(S4M_LADDER[0] + S4M_LADDER[1]) // 2, 46]
    return hall, near


def build(w):
    import env_c4_cine_figs as G
    w('stamp/s1_desk.png', s1_desk2())
    w('stamp/s1_boxfront.png', s1_boxfront())
    nimg = notes()
    w('stamp/s1_notes.png', nimg)
    spans = []
    for (x, y, _s) in NOTE_LINES:
        band = nimg[y - 2:y + 18, :, 3] > 0
        xs = np.nonzero(band.any(0))[0]
        spans.append([int(xs.min()), y - 2, int(xs.max()) + 1, y + 18])
    L['note_spans'] = spans
    w('stamp/s1_card.png', card_small())
    from env_c4_cine_places import figs_disk as FD
    w('stamp/s1_pencil.png', FD('stamp/s1_pencil.png', lambda: Q.sheet([G.s1_pencil(0), G.s1_pencil(1)])))
    lev = FD('stamp/s1_lev.png', G.s1_lev)
    w('stamp/s1_lev.png', lev)
    ys, xs = np.nonzero(lev[..., 3] > 0)
    k = int(np.argmax(ys))
    L['lev_tip'] = [int(xs[k]), int(ys[k])]
    L['pencil_tip'] = [60, 62]
    w('stamp/s2_slip.png', s2_slip())
    w('stamp/s3a_card.png', s3_card())
    w('stamp/imp_ru.png', impression('ПРИНЯТЬ', 'violet', 7701, -2.5))
    w('stamp/imp_de.png', impression('ABGANG', 'red', 7703, 1.5))
    w('stamp/stamp_ru.png', stamp_top('karsk'))
    w('stamp/stamp_de.png', stamp_top('berlin'))
    w('stamp/hand_ru.png', FD('stamp/hand_ru.png', lambda: G.stamp_hand('karsk')))
    w('stamp/hand_de.png', FD('stamp/hand_de.png', lambda: G.stamp_hand('berlin')))
    w('stamp/s3b_back.png', s3b_back())
    w('stamp/s3b_counter.png', s3b_front())
    w('stamp/s3b_hands.png', FD('stamp/s3b_hands.png', G.s3_hands_med))
    for k in ('a', 'b'):
        w('stamp/typist_%s.png' % k, life_strip('typist_' + k))
    w('stamp/lever.png', lever_sheet())
    w('stamp/split.png', split_card())
    w('stamp/s4_ladder.png', s4_ladder2())
    fw, fh = Q.STAMP_FRAME
    L['stamp_c'] = list(STAMP_C)
    L['stamp_frame'] = [fw, fh]
    L['imp_size'] = [fw + 20, fh + 20]
    L['stamp_size'] = [fw + 24, fh + 24]
    L['hand_knob'] = [100, 150]
    L['lever_pivot'] = [12, 12]
    L['s3b_hands_at'] = list(G.S3M_AT)
    look = Q.LIGHT_FLUO
    sheet, idx = Q.fig_sheet('konrad', [('idle_side', None, False), ('inspect_side', None, False),
                                        ('look_side', None, False)], look)
    w('stamp/s4_konrad.png', sheet)
    L['s4_konrad'] = idx
    # the medium shot of s4 (round 10): the niche and the hall in two depths, Konrad waist-up between them
    hall, near = s4_medium()
    w('stamp/s4m_hall.png', hall)
    w('stamp/s4m_niche.png', near)
    w('stamp/s4_konrad_med.png', FD('stamp/s4_konrad_med.png',
                                     lambda: Q.sheet([G.s4_konrad_medium(0), G.s4_konrad_medium(1)])))
