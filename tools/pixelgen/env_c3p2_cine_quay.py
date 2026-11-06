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
def h1_bg():
    R = C.ramps(N=NIGHT, S=SNOW, I=ICE, T=STONE, L=LAMP, F=EMBERGLOW, R=IRON)
    p = C.Paint(VW, VH, R, 'h1')
    yy, xx = p.yy, p.xx
    nz = Q.noise(VW, VH, 16, 1101)
    fire = Q.lightfield(VW, VH, [(-60, 150, 420, 1.0, 1.3)])
    # sky over the far bank: night, smoke drifting in from the left, the city glow low
    sky = yy < 86
    p.put(sky, 'N', 1.6 + (yy[sky] - 46) / 40.0 * 1.4 + fire[sky] * 2.0 + nz[sky] * 0.8)
    # the far bank: the Line - an embankment, a double fence, two watchtowers, the dark houses behind it
    bank = (yy >= 86) & (yy < 112)
    p.put(bank, 'T', 1.0 + nz[bank] * 0.6)
    roofs = (yy >= 74) & (yy < 90) & (np.mod(np.floor(xx / 26) * 7.3, 5) > 1.6 - (yy - 74) / 10.0)
    p.put(roofs, 'T', 0.8)
    fence = (yy >= 98) & (yy < 110) & ((np.mod(xx, 9) < 1) | (yy == 99) | (yy == 104))
    p.put(fence, 'R', 2.0)
    for tx, ty in TOWERS:
        tw = poly([(tx - 5, 112), (tx + 5, 112), (tx + 3, ty + 4), (tx - 3, ty + 4)])
        p.put(tw, 'T', 0.6)
        p.put(box(tx - 7, ty - 2, tx + 8, ty + 5), 'T', 1.2)
        p.put(box(tx - 7, ty - 4, tx + 8, ty - 2), 'S', 4.0)
        p.put(box(tx - 1, ty, tx + 2, ty + 3), 'L', 6.0)
    p.put((yy >= 110) & (yy < 113), 'S', 4.0)
    # the frozen river: ice and snow, the fire's glow on it from the left, lantern reflections
    ice = (yy >= 112) & (yy < 206)
    u = (yy - 112) / 94.0
    p.put(ice, 'I', 2.4 + nz[ice] * 1.2 + u[ice] * 1.2 + fire[ice] * 1.4)
    snowp = ice & streaks(VW, VH, 1103, cell=8, stretch=10, thr=0.58)
    p.put(snowp, 'S', 1.8 + u[snowp] * 1.6 + fire[snowp] * 1.0)
    cracks = ice & (np.abs(Q.noise(VW, VH, 9, 1105) - 0.5) < 0.012)
    p.put(cracks, 'I', 0.8)
    refl = ice & (fire * (0.75 + 0.5 * Q.noise(VW, VH, 6, 1107)) > pg.bayer(VW, VH, 1, 0) * 0.9 + 0.32)
    p.put(refl, 'F', 1.2 + fire[refl] * 2.0)
    # the balustrade: plinth, balusters, the snowy handrail
    bal = (yy >= 196) & (yy < 236)
    p.put(bal & (yy >= 226), 'T', 2.4 + fire[bal & (yy >= 226)] * 1.6)
    bx = np.mod(xx - 4, 22)
    baluster = bal & (yy >= 206) & (yy < 226) & (np.abs(bx - 11) < 4.5 - np.abs(yy - 216) * 0.12)
    p.put(baluster, 'T', 2.0 + fire[baluster] * 2.4 + (bx[baluster] < 9) * 0.8)
    rail = bal & (yy < 206)
    p.put(rail, 'T', 3.0 + fire[rail] * 1.6)
    p.put(bal & (yy < 199), 'S', 6.0 + nz[bal & (yy < 199)])
    # the quay pavement under snow, the bench (granite slab on two blocks)
    pave = yy >= 236
    v = (yy - 236) / 78.0
    p.put(pave, 'S', 3.2 + nz[pave] * 1.0 + v[pave] * 1.4 + fire[pave] * 1.6)
    x0, y0, x1, y1 = BENCH
    seat = poly([(x0 + 6, y0), (x1 - 6, y0), (x1, y1), (x0, y1)])
    p.put(seat, 'T', 3.6 + fire[seat] * 1.4)
    p.put(poly([(x0, y1), (x1, y1), (x1, y1 + 8), (x0, y1 + 8)]), 'T', 2.0)
    for lx in (x0 + 24, x1 - 60):
        p.put(box(lx, y1 + 8, lx + 36, 314), 'T', 1.4)
    p.put(seat & ((xx < x0 + 40) | (xx > x1 - 44)) & (Q.noise(VW, VH, 4, 1109) > 0.4), 'S', 6.2)   # snow at the ends
    p.resolve(band=2.0)
    L['bench'] = list(BENCH)
    L['stack_ru'] = list(STACK_RU)
    L['stack_de'] = list(STACK_DE)
    L['towers'] = [list(t) for t in TOWERS]
    return p.L.c


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


def h1_glow():
    return Q.glow_sprite(VW, VH, [(-40, 170, 330, 160, (64, 28, 8), 1.4), (120, 180, 160, 30, (40, 18, 6), 1.5)], 6.0)


# ======================================================================================= h2
PROM_Y = 290                          # feet line of the walkers on the promenade
LANTERNS = (96, 256, 416, 576)


def h2_bg():
    R = C.ramps(N=NIGHT, S=SNOW, I=ICE, T=STONE, L=LAMP, F=EMBERGLOW, R=IRON)
    p = C.Paint(VW, VH, R, 'h2')
    yy, xx = p.yy, p.xx
    nz = Q.noise(VW, VH, 14, 1201)
    fire = Q.lightfield(VW, VH, [(-80, 160, 380, 1.0, 1.3)])
    lamps = Q.lightfield(VW, VH, [(x, 150, 70, 1.0, 1.4) for x in LANTERNS] + [(x, PROM_Y, 60, 0.8, 1.4) for x in LANTERNS])
    sky = yy < 96
    p.put(sky, 'N', 1.4 + (yy[sky] - 46) / 50.0 * 1.4 + fire[sky] * 2.4 + nz[sky] * 0.6)
    farb = (yy >= 96) & (yy < 118)
    p.put(farb, 'T', 0.8 + nz[farb] * 0.5)
    p.put(farb & (yy >= 108) & (np.mod(xx, 11) < 1), 'R', 1.8)
    p.put((yy >= 116) & (yy < 119), 'S', 3.6)
    ice = (yy >= 118) & (yy < 176)
    u = (yy - 118) / 58.0
    p.put(ice, 'I', 2.2 + nz[ice] * 1.2 + u[ice] + fire[ice] * 1.6)
    st = ice & streaks(VW, VH, 1203, cell=8, stretch=12, thr=0.6)
    p.put(st, 'S', 1.8 + u[st] * 1.4)
    # balustrade
    bal = (yy >= 168) & (yy < 214)
    p.put(bal & (yy >= 204), 'T', 2.2 + fire[bal & (yy >= 204)] * 1.4 + lamps[bal & (yy >= 204)] * 1.6)
    bx = np.mod(xx, 18)
    balu = bal & (yy >= 180) & (yy < 204) & (np.abs(bx - 9) < 3.6 - np.abs(yy - 192) * 0.08)
    p.put(balu, 'T', 1.8 + fire[balu] * 2.0 + lamps[balu] * 2.4)
    rail = bal & (yy < 180)
    p.put(rail, 'T', 3.0 + fire[rail] * 1.4 + lamps[rail] * 1.8)
    p.put(bal & (yy < 171), 'S', 6.0)
    # promenade
    pave = yy >= 214
    v = (yy - 214) / 100.0
    p.put(pave, 'S', 3.0 + nz[pave] * 0.9 + v[pave] * 1.2 + fire[pave] * 1.6 + lamps[pave] * 2.2)
    # lanterns: iron posts with glass globes
    for lx in LANTERNS:
        p.put(box(lx - 1, 150, lx + 2, PROM_Y - 4), 'R', 1.2)
        p.put(box(lx - 3, PROM_Y - 8, lx + 4, PROM_Y - 2), 'R', 1.6)
        p.put(ell(lx + 0.5, 146, 5, 6), 'L', 5.8)
        p.put(box(lx - 3, 138, lx + 4, 140), 'R', 2.0)
    # the bench in the middle (their bench), seen from the side
    p.put(box(296, 270, 350, 276), 'T', 3.0)
    p.put(box(300, 276, 306, PROM_Y), 'T', 1.6)
    p.put(box(340, 276, 346, PROM_Y), 'T', 1.6)
    p.put(box(296, 268, 306, 270) | box(340, 268, 350, 270), 'S', 6.0)
    p.resolve(band=2.0)
    L['prom_y'] = PROM_Y
    L['lanterns'] = list(LANTERNS)
    return p.L.c


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


def h2_glow():
    return Q.glow_sprite(VW, VH, [(x, 148, 40, 40, (60, 44, 22), 1.4) for x in LANTERNS] +
                         [(x, PROM_Y, 54, 12, (40, 28, 12), 1.4) for x in LANTERNS] +
                         [(-60, 170, 300, 160, (70, 30, 8), 1.4)], 6.0)


# ======================================================================================= h3
H3_HORIZON = 150


def h3_bg():
    """Wide: the palais with the burning east wing on the near bank (left), the river ice across the frame with
    the fire's mirror image, the far bank with the Line's fence and two towers and the dark roofs behind it, the
    three-arch bridge far right; dawn, searchlights and smoke are runtime layers."""
    R = C.ramps(N=NIGHT, S=SNOW, I=ICE, T=STONE, L=LAMP, F=EMBERGLOW, R=IRON)
    p = C.Paint(VW, VH, R, 'h3')
    yy, xx = p.yy, p.xx
    nz = Q.noise(VW, VH, 18, 1301)
    fire = Q.lightfield(VW, VH, [(190, 150, 300, 1.0, 1.3), (190, 240, 160, 0.7, 1.3)])
    sky = yy < H3_HORIZON
    p.put(sky, 'N', 1.2 + (yy[sky] - 46) / 104.0 * 2.2 + fire[sky] * 3.0 + nz[sky] * 0.6)
    # far bank: dark roofs, the Line's fence on its embankment, two towers, the bridge
    roofs = (yy >= H3_HORIZON - 22) & (yy < H3_HORIZON - 4) & (xx > 300) & \
        (np.mod(np.floor(xx / 18) * 5.3, 7) > (H3_HORIZON - 4 - yy) / 3.0)
    p.put(roofs, 'T', 0.6)
    emb = (yy >= H3_HORIZON - 6) & (yy < H3_HORIZON + 2) & (xx > 290)
    p.put(emb, 'T', 1.0 + nz[emb] * 0.4)
    p.put(emb & (yy < H3_HORIZON - 3) & (np.mod(xx, 6) < 1), 'R', 2.0)
    p.put((yy == H3_HORIZON - 5) & (xx > 290), 'R', 2.0)
    for tx in (360, 486):
        p.put(poly([(tx - 3, H3_HORIZON - 4), (tx + 3, H3_HORIZON - 4), (tx + 2, H3_HORIZON - 36), (tx - 2, H3_HORIZON - 36)]), 'T', 0.6)
        p.put(box(tx - 6, H3_HORIZON - 43, tx + 7, H3_HORIZON - 35), 'T', 1.0)
        p.put(box(tx - 6, H3_HORIZON - 45, tx + 7, H3_HORIZON - 43), 'S', 4.0)
        p.put(box(tx - 1, H3_HORIZON - 41, tx + 2, H3_HORIZON - 38), 'L', 6.0)
    br = (xx >= 548) & (yy >= H3_HORIZON - 22) & (yy < H3_HORIZON + 8)
    arches = br & (yy > H3_HORIZON - 14) & (np.hypot(np.mod(xx - 548, 32) - 16, (yy - (H3_HORIZON + 8)) * 1.2) < 13)
    p.put(br & ~arches, 'T', 1.0)
    p.put(br & (yy < H3_HORIZON - 19), 'S', 4.2)
    # the palais on the near bank: west part and dome dark, the east wing (toward the river) burning
    bx0, bx1, top = 0, 300, 92
    body = (xx < bx1) & (yy >= top) & (yy < 206)
    p.put(body, 'T', 0.9 + fire[body] * 1.6 + nz[body] * 0.3)
    p.put((xx < bx1) & (yy >= top - 3) & (yy < top), 'S', 4.4)
    roof = (xx < bx1) & (yy >= top - 16) & (yy < top - 3) & (np.abs(xx - 150) < 150 - (top - 3 - yy) * 0.8)
    p.put(roof, 'T', 0.6 + fire[roof] * 1.2)
    dome = ell(64, top - 16, 30, 26) & (yy < top - 16)
    p.put(dome, 'T', 1.2 + fire[dome] * 0.8)
    p.put(box(60, top - 54, 68, top - 40), 'T', 1.0)
    for i, wx in enumerate(range(10, bx1 - 6, 19)):
        for j, wy in enumerate((106, 136, 168)):
            w_ = box(wx, wy, wx + 9, wy + 16)
            east = wx > 150
            hot = east and not (j == 0 and i % 3 == 1)
            p.put(w_, 'F' if hot else 'N', (2.6 + nz[w_] * 2.4 - (yy[w_] - wy) / 16.0) if hot else 0.8)
            if hot:
                p.put(box(wx - 1, wy - 6, wx + 10, wy), 'T', 0.4)                 # soot above the window
    # the quay wall of the near bank, the ice, the mirror of the fire
    qw = (yy >= 206) & (yy < 214) & (xx < 330)
    p.put(qw, 'T', 2.0 + fire[qw] * 2.4)
    p.put((yy >= 204) & (yy < 206) & (xx < 330), 'S', 5.0)
    ice = (yy >= H3_HORIZON + 2) & ~((yy < 214) & (xx < 330) & (yy >= 92))
    ice &= ~((xx < bx1) & (yy < 206))
    u = (yy - H3_HORIZON) / (VH - H3_HORIZON)
    p.put(ice, 'I', 1.8 + nz[ice] * 0.9 + u[ice] * 1.8 + fire[ice] * 1.4)
    st = ice & streaks(VW, VH, 1303, cell=7, stretch=14, thr=0.6)
    p.put(st, 'S', 1.6 + u[st] * 1.8 + fire[st] * 0.8)
    mir = ice & (xx > 150) & (xx < 300) & (yy > 214) & \
        ((1 - (yy - 214) / 110.0) * (0.6 + 0.6 * Q.noise(VW, VH, 5, 1305)) > pg.bayer(VW, VH, 2, 1) * 0.8 + 0.25) & \
        (np.mod(xx, 2) == 0)
    p.put(mir, 'F', 1.6 + (1 - (yy[mir] - 214) / 110.0) * 2.6)
    p.resolve(band=2.0)
    L['h3_towers'] = [[360, H3_HORIZON - 40], [486, H3_HORIZON - 40]]
    L['h3_fire'] = [[172, 110], [210, 104], [248, 112], [286, 118], [230, 140]]
    L['h3_horizon'] = H3_HORIZON
    return p.L.c


def h3_dawn():
    """Additive first grey of dawn low over the far bank (east, right); faded in at runtime."""
    a = np.zeros((VH, VW, 3), np.float32)
    Q.add_glow(a, 620, H3_HORIZON - 6, 460, 70, (34, 38, 46), 1.2)
    Q.add_glow(a, 640, H3_HORIZON - 10, 220, 40, (22, 22, 24), 1.3)
    return K.soft_quant(a, 4.0)


def h3_glow():
    return Q.glow_sprite(VW, VH, [(226, 130, 170, 100, (96, 42, 10), 1.3), (226, 250, 100, 80, (60, 26, 6), 1.4)], 6.0)


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


def board_bg():
    """The departures board in the station hall: frame, trilingual header, four rows already standing, the fifth
    row empty (the runtime flips the fresh line in)."""
    R = C.ramps(N=NIGHT, B=BRASS, S=SNOW, L=LAMP, G=['#06070A', '#0C0D11', '#121318', '#1A1B21', '#24252C'],
                U=['#0A1424', '#122038', '#1C2E50', '#2A4070'], T=STONE)
    p = C.Paint(VW, VH, R, 'board')
    yy, xx = p.yy, p.xx
    hall = Q.lightfield(VW, VH, [(320, 40, 420, 1.0, 1.3)])
    p.put(np.ones((VH, VW), bool), 'T', 0.6 + hall * 2.4)
    arch = (yy < 64) & (np.hypot((xx - 320) / 300.0, (yy - 64) / 60.0) > 1.0)
    p.put(arch, 'T', 1.8 + hall[arch] * 1.6)
    x0, y0, x1, y1 = BOARD
    fr = box(x0 - 6, y0 - 6, x1 + 6, y1 + 6)
    p.put(fr, 'B', 2.0 + hall[fr] * 2.0)
    p.put(fr & ((yy == y0 - 6) | (xx == x0 - 6)), 'B', 4.0)
    panel = box(x0, y0, x1, y1)
    p.put(panel, 'G', 0.8)
    head = box(x0, y0, x1, y0 + 30)
    p.put(head, 'U', 1.6)
    tm = K.vtext('ABFAHRT · ОТПРАВЛЕНИЕ · DEPART', 'l', 2)
    sm = K.place(tm, VW, VH, 320 - tm.shape[1] // 2, y0 + 10)
    p.put(sm & head, 'S', 7.0)
    for ry in ROWS_Y:
        p.put(box(x0 + 8, ry + CELL[1] + 6, x1 - 8, ry + CELL[1] + 7), 'G', 2.4)
    p.resolve(band=2.0)
    img = p.L.c.copy()
    atlas_cells = {c: _glyph_cell(c) for c in CHARSET}
    for r, text in enumerate(BOARD_ROWS):
        for i, ch in enumerate(text.upper()):
            cell = atlas_cells.get(ch, atlas_cells[' '])
            Q.blit(img, cell, ROW_X + i * CELL[0], ROWS_Y[r])
    for i in range(len(FRESH)):
        Q.blit(img, atlas_cells[' '], ROW_X + i * CELL[0], ROWS_Y[FRESH_ROW])
    L['rows_y'] = list(ROWS_Y)
    L['row_x'] = ROW_X
    L['fresh_row'] = FRESH_ROW
    L['fresh'] = FRESH
    return img


def board_glow():
    return Q.glow_sprite(VW, VH, [(320, ROWS_Y[FRESH_ROW] + 9, 260, 16, (26, 26, 22), 1.5)], 6.0)


# ======================================================================================= build
def build(w):
    w('halves/h1_bg.png', h1_bg())
    w('halves/h1_glow.png', h1_glow())
    w('halves/stacks.png', stacks())
    w('halves/arms.png', arms())
    w('halves/list_fold.png', list_fold())
    import env_c3p2_cine_figs as F
    w('halves/fig_alexei.png', F.bench_alexei())
    w('halves/fig_konrad.png', F.bench_konrad())
    L['fig_alexei'] = list(F.BENCH_A_AT)
    L['fig_konrad'] = list(F.BENCH_K_AT)
    w('halves/h2_bg.png', h2_bg())
    w('halves/h2_glow.png', h2_glow())
    w('halves/walk_alexei.png', _walk_frames('alexei'))
    w('halves/walk_konrad.png', _walk_frames('konrad'))
    w('halves/h3_bg.png', h3_bg())
    w('halves/h3_dawn.png', h3_dawn())
    w('halves/h3_glow.png', h3_glow())
    w('halves/board_bg.png', board_bg())
    w('halves/glyphs.png', glyph_atlas())
    w('halves/board_glow.png', board_glow())
    w('halves/breath.png', K.puff_sheet(6, 24, 18, ['#4F5E70', '#687789', '#A1AAB7'], 1141, grow=(0.2, 0.42), thin=0.7))
    w('halves/smoke.png', Q.smoke_sheet(8, 64, 48, seed=1151, cols=['#2E2522', '#43352E', '#5C473B', '#78604E', '#957A62']))
    w('halves/flame_s.png', Q.flame_sheet(8, 18, 30, seed=17))
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
