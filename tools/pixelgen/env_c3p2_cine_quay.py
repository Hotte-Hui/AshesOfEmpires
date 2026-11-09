"""env_c3p2_cine_quay -- art of LS_C3_Halves (owner: cinematics stream, round 8; C3P2_DESIGN §2.9, §5.2).

Before dawn on the riverside quay behind the palais: the burning east wing upstream (left, west), the frozen
river, the Line on the far bank with its watchtowers and searchlights, the lanterns of the promenade.

h1  the bench from behind and above: Alexei (left) and Konrad (right) through the portrait pipeline, the two
    halves of the broken file between them (Russian pages with the list of names on top, German pages); the
    runtime moves the stacks and the reaching arms per ctx.choices.c3g_choose
h2  the promenade from the side: they walk apart, Alexei east (right) toward the station, Konrad west (left)
h3  wide: the burning wing mirrored in the ice, the searchlights on the far bank, the first grey of dawn
h4  the departures board of the station; the runtime flips a fresh row in from a glyph atlas
Runtime: scenes/cinematics/ch3_halves/ch3_halves.gd (anchors in layout.json "halves").
"""
from __future__ import annotations

import math

import numpy as np

import env_c3p2_cine_kit as Q
from env_c3p2_cine_kit import (C, K, VW, VH, NIGHT, SNOW, LAMP, IRON, OAK, PAPER, FIRE, RED, BRASS, K_COAT,
                               A_COAT, A_FUR, K_HAT, grid, poly, ell, box, hexrgb)
import pg

L = Q.LAYOUT.setdefault('halves', {})
EMBERGLOW = ['#1A0805', '#3A0F08', '#6E1E0C', '#A8381A', '#D8662A', '#F2A044', '#FCE0A0']
STONE = ['#06080C', '#0C1017', '#131922', '#1B232E', '#252F3C', '#313D4C', '#41505F', '#56677A']
ICE = ['#0A0F16', '#101823', '#18222F', '#202C3B', '#2A3848', '#36475A', '#4A5C70', '#62768C']
VIOLET = ['#1A1424', '#2E2440', '#4A3A66', '#6A5690']

def streaks(w, h, seed, cell=10, stretch=8, thr=0.6):
    """Bool mask of wind-blown snow streaks on ice: value noise stretched horizontally."""
    n = pg.value_noise(max(2, w // stretch + 2), h, cell / 2.0, seed, octaves=3)
    n = np.repeat(n, stretch, axis=1)[:, :w]
    return n > thr


FAR_BANK = 128                        # y of the far bank's waterline (h1 / h3 share the idea, not the pixels)
BENCH = (150, 258, 490, 276)          # seat slab x0, y0 (top surface), x1, y1 (front edge)
STACK_RU = (276, 262)                 # bottom-centre of the Russian pages on the seat (h1)
STACK_DE = (364, 262)
TOWERS = ((168, 94), (486, 90))       # far-bank watchtower lamps (h1)


# ======================================================================================= h1


def stacks():
    """3 sprites in one sheet (each 40 x 16, bottom-anchored): Russian pages (cool white, violet stamps, typed
    Cyrillic lines), German pages (cream, black lines, a red stamp), the list (one sheet, a red pencil line)."""
    fw, fh = 40, 16
    R = C.ramps(P=PAPER, S=SNOW, V=VIOLET, N=NIGHT, R=RED, F=EMBERGLOW)
    out = []
    for kind in ('ru', 'de', 'list'):
        p = C.Paint(fw, fh, R, 'stack_' + kind)
        yy, xx = p.yy, p.xx
        if kind == 'list':
            top = poly([(5, 8), (35, 7), (37, 14), (3, 15)], fw, fh)
            p.put(top, 'S', 7.0)
            p.put(top & (yy == 10) & (xx > 8) & (xx < 30) & (np.mod(xx, 3) < 2), 'N', 3.0)
            p.put(top & (yy == 12) & (xx > 8) & (xx < 26) & (np.mod(xx, 3) < 2), 'N', 3.0)
            p.put(top & (yy == 11) & (xx > 12) & (xx < 24), 'R', 3.6)                    # the red pencil line
        else:
            ramp = 'S' if kind == 'ru' else 'P'
            base = 6.0 if kind == 'ru' else 4.4
            for k in range(4):
                lay = poly([(4 + k, 9 - k), (36 - k * 0.5, 8 - k), (38 - k * 0.5, 15 - k), (2 + k, 16 - k)], fw, fh)
                p.put(lay, ramp, base - 1.6 + k * 0.5)
            top = poly([(7, 6), (35, 5), (37, 12), (5, 13)], fw, fh)
            p.put(top, ramp, base)
            for ly in (7, 9, 11):
                ln = top & (yy == ly) & (xx > 9) & (xx < 32) & (np.mod(xx * 5 + ly, 7) < 4)
                p.put(ln, 'V' if kind == 'ru' else 'N', 2.0 if kind == 'ru' else 3.0)
            st = top & ell(29, 10, 3, 2, fw, fh)
            p.put(st, 'V' if kind == 'ru' else 'R', 3.0)
        p.resolve(band=2.0)
        out.append(p.L.c)
    return Q.sheet(out)


def arms():
    """Reaching arms (seen from behind and above): rows = Alexei (green quilted sleeve) / Konrad (dark blue
    sleeve, shirt cuff); columns = reach to the near stack, reach across to the far stack, the hand drawn back
    holding pages against the body.  Each frame 220 x 110 at layout halves.arms_at.  Round 9: sculpted and lit like
    the bench figures (env_c3p2_cine_hands.arm_frame), leaving the bodies at their shoulders."""
    import env_c3p2_cine_hands as H
    if hasattr(H, 'arms_sheet'):
        # round 11 (figures stream): reach in three steps, the pull with the pages, the hold, Konrad's list --
        # the cell layout and the anchors go to layout.json (arms_at, arm_cols, list_fold_at)
        sheet, extra = H.arms_sheet()
        L.update(extra)
        return sheet
    rows = [np.concatenate([H.arm_frame(who, mode) for mode in ('near', 'far', 'hold')], axis=1)
            for who in ('a', 'k')]
    L['arms_at'] = list(H.ARMS_ORIGIN)
    return np.concatenate(rows, axis=0)


def list_fold():
    """Konrad folds the list (hide_for_elena): 4 frames of the sheet in his hand (flat, half, folded, gone into the
    coat), each 40 x 24, drawn at the hand position by the runtime."""
    fw, fh = 40, 24
    R = C.ramps(S=SNOW, N=NIGHT, R=RED)
    frames = []
    for i in range(4):
        p = C.Paint(fw, fh, R, 'fold')
        if i == 0:
            m = poly([(4, 10), (36, 8), (38, 18), (2, 20)], fw, fh)
        elif i == 1:
            m = poly([(10, 4), (30, 6), (36, 18), (6, 20)], fw, fh)
        elif i == 2:
            m = poly([(14, 8), (26, 7), (28, 18), (12, 19)], fw, fh)
        else:
            m = np.zeros((fh, fw), bool)
        p.put(m, 'S', 6.4)
        p.put(m & C.rim(m, 1, 0), 'S', 4.0)
        if i < 2:
            p.put(m & (p.yy == 13) & (np.mod(p.xx, 3) < 2), 'N', 3.0)
            p.put(m & (p.yy == 14) & (p.xx > 12) & (p.xx < 24), 'R', 3.6)
        p.resolve(band=2.0)
        frames.append(p.L.c)
    return Q.sheet(frames)


# ======================================================================================= h2
PROM_Y = 290                          # feet line of the walkers on the promenade
LANTERNS = (96, 256, 416, 576)


def _walk_frames(kind, n=6):
    """Side-view walk cycle (facing right; the runtime flips Konrad), ~64 px tall, n frames."""
    fw, fh = 44, 72
    R = C.ramps(K=K_COAT, A=['#020504', '#071009', '#0E1A14', '#16261D', '#20342A', '#2E4636'], U=A_FUR, H=K_HAT,
                Z=['#2A1A18', '#46302A', '#6A4A3C', '#8A644E'], F=EMBERGLOW, L=LAMP, P=PAPER, T=['#0A0604', '#24160C'])
    frames = []
    for i in range(n):
        p = C.Paint(fw, fh, R, 'walk_' + kind)
        ph = i / n * 2 * math.pi
        sw = math.sin(ph)
        bob = int(round(abs(math.cos(ph)) * -1.5))
        cx = fw / 2
        top = 6 + bob
        coat = 'K' if kind == 'konrad' else 'A'
        hip = top + 38
        # legs (scissor), boots
        for k_, sgn in ((sw, 1), (-sw, -1)):
            fx = cx + k_ * 9
            knee = (cx + k_ * 4 + 2, hip + 12)
            leg = p.line([(cx, hip), knee, (fx, fh - 4)], r=2.8)
            p.put(leg, coat, 0.6 if sgn < 0 else 1.0)
            p.put(p.box(fx - 3, fh - 5, fx + 5, fh - 2), coat, 0.3)
        # coat body (long for Konrad, to the knee for Alexei)
        hem = top + (50 if kind == 'konrad' else 44)
        body = p.poly([(cx - 7, top + 13), (cx + 7, top + 13), (cx + 9 + sw * 1.5, hem), (cx - 9 + sw * 1.5, hem)])
        p.put(body, coat, 1.4)
        # arms swing (Konrad: hands in the pockets; Alexei: the near arm swings)
        if kind == 'alexei':
            arm = p.line([(cx + 1, top + 16), (cx - sw * 7, top + 30), (cx - sw * 9, top + 38)], r=2.6)
            p.put(arm, coat, 2.0)
            strap = p.line([(cx - 6, top + 14), (cx + 7, top + 36)], r=1.0)
            p.put(strap & body, 'T', 1.0)
        else:
            arm = p.line([(cx + 1, top + 16), (cx + 3, top + 30), (cx + 5, top + 34)], r=2.6)
            p.put(arm, coat, 2.0)
        # head, collar, hat
        p.put(p.ell(cx + 1, top + 12, 6, 3), coat, 2.0)
        head = p.ell(cx + 1.5, top + 7, 4.2, 4.8)
        p.put(head, 'Z', 1.4)
        p.put(p.box(cx + 4, top + 6, cx + 7, top + 9), 'Z', 2.6)                  # nose / cheek in profile
        if kind == 'konrad':
            hat = p.ell(cx + 1.5, top + 3.5, 7.5, 1.8) | p.rr(cx - 3, top - 3, cx + 6, top + 3.5, 2)
            p.put(hat, 'H', 1.2)
            sc = p.ell(cx + 2, top + 13, 5, 2.4)
            p.put(sc, 'P', 2.0)
        else:
            hat = p.ell(cx + 1, top + 3, 6.5, 5) | p.rr(cx - 5, top + 3, cx - 1, top + 11, 2)
            p.put(hat, 'U', 1.6)
        sil = p.L.rid >= 0
        # light: lantern/cold from above, the fire from behind (left for Alexei walking right)
        p.put(sil & C.rim(sil, 0, -1), 'L', 2.6)
        p.put(sil & C.rim(sil, -1, 0), 'F', 3.0)
        p.resolve(band=2.0)
        frames.append(p.L.c)
    return Q.sheet(frames)


# ======================================================================================= h3
H3_HORIZON = 150


# ======================================================================================= h4
BOARD = (40, 70, 600, 290)
CELL = (12, 18)
ROW_X = 64
ROWS_Y = (122, 156, 190, 224, 258)
FRESH_ROW = 4
BOARD_ROWS = ['0.55 · NORDHAFEN · GLEIS 2', '1.20 · KARSK · GLEIS 4', '5.10 · BERLIN · GLEIS 3',
              '6.45 · TRIEST · GLEIS 1']
FRESH = 'DIENSTAG · 23.40 · KORDON-17 · GLEIS 5'
CHARSET = ' ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789.·-:ÄÖÜ'


def _glyph_cell(ch, flap=False):
    """One split-flap cell (12 x 18): dark card, the split line, the glyph at 2x (white)."""
    w, h = CELL
    a = np.zeros((h, w, 3), np.float32)
    a[:] = np.array([20, 20, 24], np.float32)
    a[:h // 2] = np.array([26, 26, 30], np.float32)
    a[h // 2] = np.array([6, 6, 8], np.float32)
    if ch != ' ':
        import pixfont_umlauts as UML
        if ch in UML.UML_57:
            # round 9: Ä / Ö / Ü keep their dots on the flap (dots, a blank row, the letter one row shorter)
            m = np.array([[c == '#' for c in row] for row in UML.UML_57[ch]], bool)
        else:
            m = K.vtext(ch, 'l', 1)
            m = m[2:9, 1:-1] if m.shape[0] >= 9 else m
        m = np.repeat(np.repeat(m, 2, 0), 2, 1)
        gy, gx = (h - m.shape[0]) // 2, (w - m.shape[1]) // 2
        sub = a[gy:gy + m.shape[0], gx:gx + m.shape[1]]
        sub[m[:sub.shape[0], :sub.shape[1]]] = np.array([232, 228, 214], np.float32)
        a[h // 2] = np.array([6, 6, 8], np.float32)
    if flap:                                    # a falling flap: the top half darkened and squashed
        a[:h // 2] *= 0.45
        a[h // 2 - 2:h // 2] = np.array([60, 60, 64], np.float32)
    out = np.zeros((h, w, 4), np.uint8)
    out[..., :3] = np.clip(a, 0, 255).astype(np.uint8)
    out[..., 3] = 255
    return out


def glyph_atlas():
    """All board glyphs in one row (CHARSET order) + the same glyphs mid-flap in a second row."""
    cells = [_glyph_cell(c) for c in CHARSET]
    flaps = [_glyph_cell(c, True) for c in CHARSET]
    L['charset'] = CHARSET
    L['cell'] = list(CELL)
    return np.concatenate([np.concatenate(cells, axis=1), np.concatenate(flaps, axis=1)], axis=0)


def board_glow():
    return Q.glow_sprite(VW, VH, [(320, ROWS_Y[FRESH_ROW] + 9, 260, 16, (26, 26, 22), 1.5)], 6.0)


# ======================================================================================= build
def build(w):
    import env_c3p2_cine_river as RV
    import env_c3p2_cine_life as LF
    w('halves/h1_bg.png', RV.h1_bg())
    w('halves/h1_glow.png', RV.h1_glow())
    w('halves/stacks.png', stacks())
    w('halves/arms.png', arms())
    w('halves/list_fold.png', list_fold())
    import env_c3p2_cine_figs as F
    w('halves/fig_alexei.png', F.bench_alexei())
    w('halves/fig_konrad.png', F.bench_konrad())
    L['fig_alexei'] = list(F.BENCH_A_AT)
    L['fig_konrad'] = list(F.BENCH_K_AT)
    w('halves/h2_bg.png', RV.h2_bg())
    w('halves/h2_near.png', RV.h2_near())
    w('halves/h2_glow.png', RV.h2_glow())
    qw = getattr(F, 'quay_walk', None)                   # the figures stream's rigged walk cycles (fallback: round 8)
    w('halves/walk_alexei.png', qw('alexei') if qw else _walk_frames('alexei'))
    w('halves/walk_konrad.png', qw('konrad') if qw else _walk_frames('konrad'))
    build_places(w)
    w('halves/crow.png', LF.crow_sheet())
    # travellers in the station hall in front of the board, looking up at it (the figures stream's townspeople)
    ps = getattr(F, 'person_sheet', None)
    if ps:
        w('halves/traveller_l.png', ps('guest', 2, 'look_up', 96, 170.0, 'dawn', 'night', 2, eyes=False))
        w('halves/traveller_r.png', ps('woman', 1, 'look_up', 90, 195.0, 'dawn', 'night', 2, eyes=False))
        L['travellers'] = [['halves/traveller_l.png', 24, 352], ['halves/traveller_r.png', 606, 354]]
    else:
        L['travellers'] = []
    w('halves/pigeon.png', LF.pigeon_sheet())
    w('halves/glyphs.png', glyph_atlas())
    w('halves/board_glow.png', board_glow())
    L['preview'] = [
        {'id': 'h1', 'layers': [['halves/h1_bg.png', [0, 0]], ['halves/h1_glow.png', [0, 0], 'add'],
                                ['halves/stacks.png', [STACK_RU[0] - 20, STACK_RU[1] - 16], 'over', 3, 0],
                                ['halves/stacks.png', [STACK_DE[0] - 20, STACK_DE[1] - 16], 'over', 3, 1],
                                ['halves/fig_alexei.png', L['fig_alexei'], 'over', 2, 0],
                                ['halves/fig_konrad.png', L['fig_konrad'], 'over', 2, 0]]},
        {'id': 'h2', 'layers': [['halves/h2_bg.png', [0, 0]], ['halves/h2_glow.png', [0, 0], 'add'],
                                ['halves/walk_alexei.png', [420, PROM_Y - 72], 'over', 6, 1],
                                ['halves/walk_konrad.png', [190, PROM_Y - 72], 'over', 6, 4]]},
        {'id': 'h3', 'layers': [['halves/h3_bg.png', [0, 0]], ['halves/h3_glow.png', [0, 0], 'add'],
                                ['halves/h3_dawn.png', [0, 0], 'add']]},
        {'id': 'h4', 'layers': [['halves/board_bg.png', [0, 0]], ['halves/board_glow.png', [0, 0], 'add']]},
    ]


def build_places(w):
    """The halves' places and soft effects that need no figure renders (round 11): the burning wing over the ice
    and a dawn that can be seen, the board hall, soft steam / breath (the wing's fire and smoke: pixel fire kit,
    played by the film)."""
    import env_c3p2_cine_river as RV
    import env_c3p2_cine_life as LF
    w('halves/h3_bg.png', RV.h3_bg())
    w('halves/h3_dawn.png', RV.h3_dawn())
    w('halves/h3_glow.png', RV.h3_glow())
    w('halves/board_bg.png', RV.board_bg())
    w('halves/steam.png', LF.soft_puff_sheet(6, 120, 80, LF.STEAM_COLD, 1161, grow=(0.3, 0.5), light=(0.2, -0.9),
                                             thin=0.55, drift=0.06, alpha=0.7, wisp=0.6))
    w('halves/breath.png', LF.soft_puff_sheet(6, 24, 18, ['#3A4859', '#4F5E70', '#687789', '#A1AAB7', '#C2C9D2'],
                                              1141, grow=(0.2, 0.42), light=(0.3, -0.8), thin=0.7, alpha=0.8, lobes=6))
    # round 13: the wing's flames, smoke and smoke column are the pixel fire kit's sheets, played by the film
    # (halves/flame_s, halves/smoke and halves/h3_plume are gone)
