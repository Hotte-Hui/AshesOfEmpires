"""env_veltrava_cine_dawn -- the two trains of LS_C3_Trains t4 (Konrad's and Alexei's, side view, 2 frames).

Owner: cinematics stream.  Round 10: the dawn over Veltrava itself (sky, city, bridge, river, bank, steam,
glows) moved to env_veltrava_cine_city.py (the crane shot); this module keeps the train sprite sheets:
Konrad's train (grey-blue saloon cars, the salon car, pennants, engine running east) and Alexei's (green
carriages, the sealed courier wagon 4 at its tail, engine running west).  The runtime places them on the
bridge plane (layout trains.d4.de_rail / su_rail).
"""
from __future__ import annotations

import math

import numpy as np

import env_veltrava_cine as C
import env_veltrava_cine_kit as K
import pg

VW, VH = C.VW, C.VH
V = C.V
LAYOUT = C.LAYOUT.setdefault('trains', {})
kit = C.kit
shift = C.shift
rim = C.rim

TRAIN_H = 30
TRAIN_W = 376
DE_RAIL, SU_RAIL = 181, 191                    # rail rows of the far / near track
TRAIN_DE_Y, TRAIN_SU_Y = DE_RAIL - TRAIN_H + 2, SU_RAIL - TRAIN_H + 2
PARAPET_Y = 185                                # top of the near parapet (bridge_fg) -> hides the near wheels
ARCHES = [(44, 220), (236, 404), (420, 596)]
ARCH_CY, ARCH_RY = 238, 34
WATER_Y = 244
QUAY_LAMPS = [34, 118, 206, 294, 378, 466, 550, 626]
PARAPET_LAMPS = [36, 128, 220, 312, 404, 496, 588]
CHIMNEYS = [[58, 140], [139, 131], [231, 138], [287, 140], [437, 139], [519, 132], [604, 141]]

SKY = ['#070A12', '#0C111C', '#121A26', '#1A2431', '#1E2836', '#2A3646', '#3A4859', '#4F5E70', '#5C6B82',
       '#687789', '#7684A0', '#8593A3', '#95A0B8', '#A1AAB7', '#B6B9C9']
DAWN = ['#5C6B82', '#7684A0', '#95A0B8', '#B6B9C9', '#D3CDD3', '#E8DCD6', '#F2E4D2']
SIL = ['#070A12', '#0C111C', '#121A26', '#1A2431', '#1E2836', '#2A3646', '#3A4859', '#4F5E70', '#5C6B82',
       '#687789', '#7684A0']
STONE = ['#0C111C', '#15171C', '#22262D', '#323840', '#464D55', '#5E666E', '#687789', '#8593A3']
SNOW = ['#2A3646', '#3A4859', '#4F5E70', '#687789', '#7D8796', '#A1AAB7', '#C2C9D2', '#DEE2E7', '#F2F3F5']
WATER = ['#070A12', '#0C111C', '#121A26', '#1A2431', '#1E2836', '#2A3646', '#3A4859', '#4F5E70', '#687789',
         '#8593A3', '#A1AAB7']


def ramps_dawn():
    return C.ramps(S=SKY, D=DAWN, N=SIL, I=STONE, W=SNOW, Q=WATER, L=V['lamp'], P=V['patina'], C=V['cream'],
                   R=V['red'], G=['#0C111C', '#1E302E', '#2B4541', '#3D5E57', '#4A4236'],
                   B=['#0C111C', '#121A26', '#1E2836', '#2A3646', '#3A4859', '#4F5E70'],
                   T=['#070A12', '#0B1512', '#12201a', '#1E302E', '#2B4541', '#3D5E57', '#56796E'])


def _east(xx):
    return np.clip((xx - 120) / 520.0, 0, 1)


# =========================================================================== trains
def _coach(p, x0, w, body_ramp, body_tone, lit, frame, stripe=None, pennant=False, boxcar=False, salon=False):
    """One coach on the TRAIN_H-row sprite, rail at row TRAIN_H - 2 (wheels hidden by the parapet later)."""
    yy, xx = p.yy, p.xx
    east = np.clip((xx - x0) / max(1, w), 0, 1)
    body = p.rr(x0 + 1, 9, x0 + w - 1, 26, 2)
    p.put(body, body_ramp, body_tone + east * 0.4)
    p.put(body & (yy >= 24), body_ramp, body_tone - 0.6)
    roof = p.rr(x0 + 1, 5, x0 + w - 1, 10, 3)
    p.put(roof, 'I', 2.6)
    p.put(roof & (yy < 7), 'W', 3.6)                                                  # snow on the roof
    p.put(p.box(x0 + 3, 9, x0 + w - 3, 10), 'I', 1.2)
    if stripe is not None:
        p.put(p.box(x0 + 2, 20, x0 + w - 2, 21) & body, stripe[0], stripe[1])
    if boxcar:
        door = p.box(x0 + w // 2 - 8, 11, x0 + w // 2 + 8, 25)
        p.put(door & ~kit.erode(door, 1), body_ramp, body_tone - 0.8)
        p.put(p.box(x0 + w // 2 - 8, 17, x0 + w // 2 + 8, 18), body_ramp, body_tone - 0.7)
        tm = C.text('4', '35')
        p.put(K.place(tm, p.w, p.h, x0 + 6, 13), 'W', 4.0)
        p.put(p.box(x0 + w // 2 + 10, 18, x0 + w // 2 + 13, 20), 'L', 1.8)        # lead seal plate
        p.put(p.box(x0 + w // 2 + 10, 18, x0 + w // 2 + 11, 19), 'C', 4.0)
    else:
        k = 0
        step = 9 if salon else 7
        ww = 6 if salon else 4
        for wx in range(x0 + 7, x0 + w - 8, step):
            win = p.box(wx, 12, wx + ww, 18)
            on = lit[k % len(lit)]
            p.put(win, 'L' if on else 'B', 2.2 + (k % 3) * 0.4 if on else 1.0, emis=on)
            if on:
                p.put(p.box(wx, 12, wx + ww, 13), 'L', 3.6, emis=True)
                # round 10 (figures stream): passengers at the lit windows; Konrad and Alexei at theirs
                import env_veltrava_cine_people as PP
                PP.paint_window_passengers(p, wx, 12, ww, 6, seed=k * 5 + x0)
            k += 1
        for dx in (x0 + 2, x0 + w - 5):
            p.put(p.box(dx, 11, dx + 3, 25), body_ramp, body_tone - 0.7)
            p.put(p.box(dx + 1, 13, dx + 2, 16), 'B', 1.4)
    p.put(p.box(x0 + 1, 26, x0 + w - 1, 27), 'N', 1.0)
    for bx in (x0 + 9, x0 + w - 13):
        p.put(p.box(bx - 2, 26, bx + 6, 28), 'N', 0.6)
    p.put(p.box(x0 - 1, 21, x0 + 1, 23), 'I', 1.4)
    if pennant:
        p.put(p.box(x0 + w - 3, 0, x0 + w - 2, 6), 'I', 3.0)
        fl = [(x0 + w - 2, 0), (x0 + w + 3 + frame, 1 + frame * 0.5), (x0 + w - 2, 3)]
        p.put(p.poly(fl), 'C', 3.6 if frame == 0 else 3.0)


def _loco(p, x0, side, frame):
    """Steam locomotive (64 px) with tender (26 px); 'de' runs right (front at the right), 'su' runs left."""
    yy, xx = p.yy, p.xx
    f = (lambda dx: x0 + dx) if side == 'de' else (lambda dx: x0 + 90 - dx)       # dx from the tender end
    lo = lambda a, b: (min(a, b), max(a, b))                                         # noqa: E731
    body_r = 'B'
    a, b = lo(f(0), f(26))
    p.put(p.box(a + 1, 11, b - 1, 26), body_r, 2.0)
    p.put(p.box(a + 2, 9, b - 2, 12), 'N', 0.6)
    p.put(p.box(a + 2, 9, b - 2, 10), 'W', 3.0)                                       # snow on the coal
    p.put(p.box(a + 1, 11, b - 1, 12), 'I', 3.0)
    a, b = lo(f(26), f(41))
    p.put(p.box(a, 7, b, 26), body_r, 2.2)
    p.put(p.box(a - 1, 6, b + 1, 8), 'I', 3.0)
    p.put(p.box(a + 1, 5, b - 1, 7), 'W', 3.6)
    cw = a + 4 if side == 'de' else b - 8
    p.put(p.box(cw, 10, cw + 4, 16), 'L', 3.2, emis=True)                            # firelit cab window
    a, b = lo(f(41), f(86))
    boil = p.rr(a, 10, b, 22, 3)
    p.put(boil, body_r, 2.4 + np.clip((yy - 10) / 12, 0, 1) * -1.2)
    p.put(boil & (yy < 12), 'I', 4.2)
    p.put(boil & (yy < 11), 'W', 4.0)
    p.put(p.box(a, 22, b, 26), 'N', 0.8)
    dome_x = f(60)
    p.put(p.ell(dome_x, 10, 3.5, 2.5) & (yy < 10), 'I', 3.0)
    chim = f(78)
    p.put(p.box(chim - 2, 3, chim + 2, 10), 'I', 1.8)
    p.put(p.box(chim - 3, 3, chim + 3, 4), 'I', 3.2)
    front = f(90)
    fa, fb = lo(f(86), front)
    p.put(p.box(fa, 9, fb, 22), 'I', 1.6)
    hl = f(88)
    p.put(p.box(hl - 1, 11, hl + 1, 13), 'C', 5.0, emis=True)
    p.put(p.box(hl - 1, 18, hl + 1, 20), 'C', 4.4, emis=True)
    da, db = lo(f(82), f(83))
    p.put(p.box(da, 6, db + 1, 21), 'I', 3.4)                                         # smoke deflector
    if side == 'su':
        p.put(p.box(lo(f(70), f(84))[0], 18, lo(f(70), f(84))[1], 19), 'R', 2.0)      # red running board line
    LAYOUT['train_' + side]['chimney'] = [int(chim), 3]
    LAYOUT['train_' + side]['headlamp'] = [int(hl), 12]


def train_sheet(side):
    W = TRAIN_W
    sheet = np.zeros((TRAIN_H * 2, W, 4), np.uint8)
    LAYOUT['train_' + side] = {'front': W if side == 'de' else 0, 'y': TRAIN_DE_Y if side == 'de' else TRAIN_SU_Y,
                               'w': W, 'h': TRAIN_H}
    for fr in range(2):
        p = C.Paint(W, TRAIN_H, ramps_dawn(), 'train_' + side)
        if side == 'de':
            for i in range(4):
                _coach(p, i * 71, 71, 'B', 2.4, [1, 1, 0, 1, 0, 1, 1, 0] if i != 2 else [1, 1, 1, 1, 1, 1],
                       fr, stripe=('C', 2.4), pennant=True, salon=(i == 2))
            _loco(p, 286, 'de', fr)
        else:
            _loco(p, 0, 'su', fr)
            for i in range(3):
                _coach(p, 90 + i * 71, 71, 'T', 3.2, [0, 1, 1, 0, 1, 0, 0, 1], fr, stripe=('C', 2.0))
            _coach(p, 303, 71, 'T', 2.6, [], fr, boxcar=True)
        p.resolve(band=2.6)
        sheet[fr * TRAIN_H:(fr + 1) * TRAIN_H] = p.L.c
    return sheet


def train_de():
    return train_sheet('de')


def train_su():
    return train_sheet('su')
