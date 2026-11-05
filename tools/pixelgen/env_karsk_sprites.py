"""env_karsk_sprites -- frame strips for the interactive ambient actors of scene A1 (TECHNICAL_ARCHITECTURE
§12.2 "actors"): hooded crows on the PA wire, the ginger cat by the fire barrel, the distant goods train
(parallax 0.25), laundry on the barrack line (parallax 0.72), signalman silhouettes for the amber window,
the hidden-cache glint / cloth flutter, the lost mitten, the flickering lamp bulb and smoke puffs.

All sprites are hand-placed ASCII pixel maps (1 char = 1 game pixel) coloured from the karsk palette.
Strips are horizontal: frame k occupies x = k*cw .. (k+1)*cw.  Deterministic, no randomness without seed.
"""
from __future__ import annotations

import os as _os
import sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))

import math

import numpy as np

from env_karsk_lib import Layer, NI, TE, SA, SK, ST, RU, CO, SN, WO, RED, bayer, value_noise

CLEAR = np.zeros(4, np.uint8)


def _grid(s: str):
    rows = s.strip('\n').split('\n')
    w = max(len(r) for r in rows)
    return [r.ljust(w, '.') for r in rows]


def stamp(L: Layer, x0: int, y0: int, art: str, legend: dict, hgt=0.5, em_keys=(), flip=False):
    """Paint ASCII art at (x0, y0). legend: char -> colour; '.' = transparent.
    em_keys: chars that are also written to the emission mask."""
    rows = _grid(art)
    w = len(rows[0])
    for y, r in enumerate(rows):
        for x, ch in enumerate(r):
            if ch == '.' or ch == ' ':
                continue
            col = legend.get(ch)
            if col is None:
                continue
            xx = x0 + (w - 1 - x if flip else x)
            L.px(xx, y0 + y, col, hgt, col if ch in em_keys else None)
    return w, len(rows)


def strip(frames, cw, ch, legend, name, em_keys=(), dx=0, dy=0):
    S = Layer(cw * len(frames), ch, name)
    for i, art in enumerate(frames):
        if art is None:
            continue
        stamp(S, i * cw + dx, dy, art, legend, em_keys=em_keys)
    return S


# =========================================================================== hooded crows (playfield scale)
# Hooded crow (Corvus cornix, the crow of Russian towns): black head, bib, wings and tail; ash-grey mantle
# and belly.  Facing right; feet on the bottom row (= the wire).  Rim light from the low sun (right).
CROW_LEG = {'K': NI[0], 'k': NI[1], 'b': NI[2], 'g': ST[2], 'G': ST[3], 'h': ST[4], 'r': TE[3], 'e': ST[1]}
CW, CH = 14, 12
_crow_idle_a = """
..............
..............
..............
..............
........KKr...
.......KKKKbb.
.....ggKKKK...
...gggGGKK....
..KKKKgGG.....
.KKKKKKgh.....
KKK..k.k......
K....k.k......"""
_crow_idle_b = """
..............
..............
..............
..............
..............
........KKr...
.....ggKKKKbb.
...gggGGKKK...
..KKKKgGGh....
.KKKKKKgh.....
KKK..k.k......
K....k.k......"""
_crow_look = """
..............
..............
..............
..............
........rKK...
......bbKKKK..
.....ggKKKK...
...gggGGKK....
..KKKKgGG.....
.KKKKKKgh.....
KKK..k.k......
K....k.k......"""
_crow_caw = """
..............
..............
..............
.........KKb..
........KKK.b.
.......KKKK...
.....ggKKK....
...gggGGKK....
..KKKKgGG.....
.KKKKKKgh.....
KKK..k.k......
K....k.k......"""
_crow_preen = """
..............
..............
..............
..............
..............
..............
.....ggKKKr...
...gggKKKKbb..
..KKKKKGGh....
.KKKKKKgh.....
KKK..k.k......
K....k.k......"""
_crow_hop = """
..............
..............
........KKr...
.......KKKKbb.
.....ggKKKK...
...gggGGKK....
..KKKKgGG.....
.KKKKKKgh.....
KKK..k.k......
K....k..k.....
..............
.............."""
_crow_takeoff = """
..............
...KK.........
....KKK.......
.....KKK.KKr..
......KKKKKKbb
....ggKKKK....
..gggGGKK.....
.KKKKgGG......
KKKKKKgh......
KK...kk.......
..............
.............."""
# flight (wing cycle), body level, ~15 px span
_fly_up = """
..............
....KK........
.....KKK......
......KKK.....
......KKKK....
.......KKKKr..
..gggKKKKKKKbb
KKKKKKKKKK....
.KK...........
..............
..............
.............."""
_fly_mid = """
..............
..............
..............
..............
..............
.......KKKKr..
.KKggKKKKKKKbb
KKKKKKKKKKK...
...KKKKKK.....
.....KKK......
..............
.............."""
_fly_down = """
..............
..............
..............
..............
..............
.........KKr..
..ggKKKKKKKKbb
KKKKKKKKKKK...
....KKKKK.....
.....KKKK.....
......KKK.....
.......KK....."""
_fly_glide = """
..............
..............
..............
..............
..............
.KK.......KKr.
..KKggKKKKKKbb
KKKKKKKKKKKK..
....KK........
..............
..............
.............."""
CROW_FRAMES = ['idle_a', 'idle_b', 'look', 'caw', 'preen', 'hop', 'takeoff', 'fly_up', 'fly_mid', 'fly_down',
               'glide']


def crows():
    arts = [_crow_idle_a, _crow_idle_b, _crow_look, _crow_caw, _crow_preen, _crow_hop, _crow_takeoff,
            _fly_up, _fly_mid, _fly_down, _fly_glide]
    S = strip(arts, CW, CH, CROW_LEG, 'crows')
    return S, {'cell': [CW, CH], 'origin': [6, CH - 1], 'frames': CROW_FRAMES}


# =========================================================================== ginger cat (curled by the barrel)
# A round, curled ginger tabby facing LEFT (toward the barrel): body oval, head resting on the front,
# tail wrapped along the front.  Fire side (left) = warm rim, back = cold sky rim, tabby stripes on the back.
KW, KH = 18, 11
CAT_FRAMES = ['sleep_a', 'sleep_b', 'head_mid', 'head_up', 'blink', 'ear', 'tail']


def _cat_frame(L: Layer, ox: int, lift=0, eyes='closed', breath=0, ear=False, tail_up=False):
    """Draw one cat frame into L at x offset ox. Ground row = KH-1."""
    base = KH - 2
    bcx, bcy, brx, bry = 10.2, base - 2.6 - breath * 0.5, 5.9, 3.1 + breath * 0.5
    yy, xx = np.mgrid[0:KH, 0:KW].astype(np.float32)
    body = ((xx + 0.5 - bcx) / brx) ** 2 + ((yy + 0.5 - bcy) / bry) ** 2 <= 1.0
    hcx, hcy, hr = 4.6 - lift * 0.3, base - 2.0 - lift, 2.55
    head = ((xx + 0.5 - hcx) ** 2 + (yy + 0.5 - hcy) ** 2) <= hr * hr
    neck = np.zeros_like(body)
    if lift >= 2:
        neck = (xx >= hcx - 0.5) & (xx <= hcx + 2.5) & (yy >= hcy) & (yy <= base - 2)
    M = body | head | neck
    cols = np.zeros((KH, KW, 4), np.uint8)
    cols[M] = RU[3]
    for y in range(KH):
        for x in range(KW):
            if not M[y, x]:
                continue
            up = y == 0 or not M[y - 1, x]
            down = y == KH - 1 or not M[y + 1, x]
            left = x == 0 or not M[y, x - 1]
            right = x == KW - 1 or not M[y, x + 1]
            in_body = body[y, x] and not head[y, x]
            if down:
                cols[y, x] = RU[1]
            elif in_body and y >= base - 1:
                cols[y, x] = RU[2]
            elif in_body and x in (8, 11, 14) and y < base - 1:
                cols[y, x] = RU[2]          # tabby stripes (short vertical bands)
            if up and x > 6:
                cols[y, x] = TE[3] if in_body else RU[4]
            elif up:
                cols[y, x] = RU[4]
            if left and not down:
                cols[y, x] = RU[5]
            if right and in_body and not up:
                cols[y, x] = RU[2]
    if tail_up:
        for (x, y) in ((16, base - 3), (16, base - 4), (17, base - 5), (17, base - 6)):
            cols[y, x] = RU[3]
        cols[base - 6, 17] = RU[4]
    else:
        for x in range(4, 15):
            y = base
            if not M[y, x] or x < 6:
                cols[y, x] = RU[2] if x % 3 else RU[3]
        cols[base, 3] = RU[3]
        cols[base - 1, 3] = RU[2]
    cols[base, 5] = SN[2]
    if lift >= 2:
        cols[base - 1, 4] = SN[2]
    ty = int(round(hcy - hr))
    for ex in (int(hcx - 1.6), int(hcx + 0.8)):
        cols[ty, ex] = RU[1]
        if ear and ex > hcx:
            cols[ty - 1, ex] = RU[1]
        if ty + 1 < KH and cols[ty + 1, ex][3]:
            cols[ty + 1, ex] = RU[2]
    ey = int(round(hcy)) - (1 if lift >= 2 else 0)
    exl = int(round(hcx - 1.4))
    em_px = []
    if eyes == 'closed':
        cols[ey, exl] = NI[2]
        cols[ey, exl + 1] = NI[2]
    else:
        cols[ey, exl] = CO[3]
        em_px.append((exl, ey))
        if lift >= 2:
            cols[ey, exl + 2] = CO[3]
            em_px.append((exl + 2, ey))
    nx_, ny_ = int(round(hcx - hr + 0.2)), int(round(hcy)) + 1
    if 0 <= nx_ < KW:
        cols[ny_, nx_] = RU[4]
    for x in range(3, 17):
        cols[KH - 1, x] = NI[3]
    for y in range(KH):
        for x in range(KW):
            c = cols[y, x]
            if c[3]:
                L.px(ox + x, y, c, 0.5, c if (x, y) in em_px else None)


def cat():
    specs = [dict(), dict(breath=1), dict(lift=1), dict(lift=3, eyes='open'), dict(lift=3, eyes='closed'),
             dict(lift=3, eyes='open', ear=True), dict(lift=3, eyes='open', tail_up=True)]
    S = Layer(KW * len(specs), KH, 'cat')
    for i, sp in enumerate(specs):
        _cat_frame(S, i * KW, **sp)
    return S, {'cell': [KW, KH], 'origin': [10, KH - 1], 'frames': CAT_FRAMES}


# =========================================================================== goods train on the far embankment
# Mid-distance plane (parallax 0.45, ~3 px per metre): hazed silhouettes in the mid layer's tones, snow on the
# roofs, rim light on the right edges.  Facing LEFT (the actor mirrors for the other direction); the bottom row
# is the rail.  'L' = the loco's headlamp (one warm pixel, emissive).
TR_LEG = {'K': NI[3], 'D': TE[1], 'd': TE[2], 'B': TE[3], 'b': TE[2], 'l': SA[1], 'r': SA[2], 's': SA[4],
          'S': SN[1], 'w': TE[4], 'L': CO[3], 'c': ST[1]}
_loco = """
.....KK...........................
.....KK.......sss.................
....KKKK.....DDDDD.....SSSSSSSS...
.....KK......DDDDD....DdddddddDD..
.....KK..KK..DDDDD....DdKKdKKddDr.
..DDDDDDDDDDDDDDDDDDDDDdKKdKKddDr.
.DBBBBBBBBBBBBBBBBBBBBDddddddddDr.
LDBBBlBBBBBlBBBBBBlBBBDDDDDDDDDDr.
.DBBBBBBBBBBBBBBBBBBBBDBBBBBBBBDr.
.DDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDD.
.cKDDKKDDKKDDKKDDKKDDDDKKDDDKKDDc.
..wKKw.KwwK.KwwK.KwwK..wKKw.wKKw..
...ww...ww...ww...ww....ww...ww..."""
_tender = """
.SSSSSSSSSSSSSSS.
DddddddddddddddDr
DbbbbbbbbbbbbbbDr
DBBBBBBBBBBBBBBDr
DBBBBBBBBBBBBBBDr
DDDDDDDDDDDDDDDDD
cKDDKKDDDDKKDDKKc
.wKKw......wKKw..
..ww........ww..."""
_wag_box = """
.SSSSSSSSSSSSSSSSSSSSSSSS.
DddddddddddddddddddddddddD
DBdBBBBBdBBBBBBBBdBBBBBdBr
DBdBBBBBdBlllllBBdBBBBBdBr
DBdBBBBBdBlBBBlBBdBBBBBdBr
DBdBBBBBdBlBBBlBBdBBBBBdBr
DBdBBBBBdBlllllBBdBBBBBdBr
DBdBBBBBdBBBBBBBBdBBBBBdBr
DDDDDDDDDDDDDDDDDDDDDDDDDD
cKDDKKDDDDDDDDDDDDDDKKDDKc
.wKKw..............wKKw...
..ww................ww...."""
_wag_tank = """
..........DD..............
.....SSSSSDDSSSSSSSS......
...DDdddddddddddddddDD....
..DdBBBBBBBBBBBBBBBBBdD...
.DdBBBBBBBBBBBBBBBBBBBdDr.
.DBlllllllllllllllllllBDr.
.DdBBBBBBBBBBBBBBBBBBBdDr.
..DdBBBBBBBBBBBBBBBBBdDr..
DDDDDDDDDDDDDDDDDDDDDDDDDD
cKDDKKDDDDDDDDDDDDDDKKDDKc
.wKKw..............wKKw...
..ww................ww...."""
_wag_flat = """
..........................
..........................
..SSSSSSS.....SSSSSSSSS...
..rllllllr....rlllllllr...
..DBBBBBBD....DBBBBBBBD...
..DBBBBBBD....DBBBBBBBD...
..DBBBBBBD....DBBBBBBBD...
.D.DDDDDD..D..DDDDDDDDD.D.
DDDDDDDDDDDDDDDDDDDDDDDDDD
cKDDKKDDDDDDDDDDDDDDKKDDKc
.wKKw..............wKKw...
..ww................ww...."""
_wag_gond = """
..........................
..........................
..........................
.SSSSSSSSSSSSSSSSSSSSSSSS.
DDDDDDDDDDDDDDDDDDDDDDDDDD
DBBBBBBdBBBBBBBBdBBBBBBBBr
DBBlBBBdBBBBlBBBdBBBBlBBBr
DBBBBBBdBBBBBBBBdBBBBBBBBr
DDDDDDDDDDDDDDDDDDDDDDDDDD
cKDDKKDDDDDDDDDDDDDDKKDDKc
.wKKw..............wKKw...
..ww................ww...."""


def train():
    """Returns {'loco': Layer (loco + tender), 'wagons': [Layer...]}; bottom row of every part = the rail."""
    parts = {}

    def mk(arts, name, em=()):
        rows_list = [_grid(a) for a in arts]
        h = max(len(r) for r in rows_list)
        w = sum(len(r[0]) for r in rows_list) - (len(arts) - 1)
        L = Layer(w, h, name)
        x = 0
        for a, rows in zip(arts, rows_list):
            stamp(L, x, h - len(rows), a, TR_LEG, em_keys=em)
            x += len(rows[0]) - 1
        return L
    parts['loco'] = mk([_loco, _tender], 'train_loco', em=('L',))
    parts['wagons'] = [mk([_wag_box], 'wag_box'), mk([_wag_tank], 'wag_tank'), mk([_wag_flat], 'wag_flat'),
                       mk([_wag_gond], 'wag_gond')]
    return parts


def smoke_puff_strip(frames=8, size=14, seed=3, cols=None):
    """One puff growing and dissolving over `frames` frames (train plume).  Dissolve = ordered dither with a
    rising threshold (clean pixel clusters, no noise speckle)."""
    cols = cols or [SK[1], SK[2], SK[3], SK[4]]
    S = Layer(size * frames, size, 'puff')
    rng = np.random.default_rng(seed)
    lobes = [(rng.uniform(-0.3, 0.3), rng.uniform(-0.25, 0.15), rng.uniform(0.6, 0.85)) for _ in range(3)]
    yy, xx = np.mgrid[0:size, 0:size].astype(np.float32)
    c = size / 2.0
    for f in range(frames):
        t = f / (frames - 1)
        r = 1.5 + t * (size * 0.44 - 1.5)
        M = ((xx + 0.5 - c) ** 2 + (yy + 0.5 - c) ** 2) <= (r * 0.75) ** 2
        for (ox, oy, k) in lobes:
            M |= ((xx + 0.5 - c - ox * r) ** 2 + (yy + 0.5 - c - oy * r) ** 2) <= (r * k) ** 2
        lit = ((xx + 0.5 - c) * 0.55 - (yy + 0.5 - c) * 0.85) / max(1.0, r)
        tone = np.clip(0.42 + 0.5 * lit - 0.25 * t, 0, 0.999) * len(cols)
        idx = np.clip(tone.astype(int), 0, len(cols) - 1)
        thr = bayer(size, size, 0, 0, 4)
        fade = max(0.0, (t - 0.35) / 0.65) ** 1.2
        d = np.sqrt((xx + 0.5 - c) ** 2 + (yy + 0.5 - c) ** 2) / max(1.0, r)
        keep = M & (thr > fade * (0.55 + 0.6 * d))
        sub = S.c[:, f * size:(f + 1) * size]
        sub[keep] = np.stack(cols)[idx[keep]]
    return S


# =========================================================================== laundry (parallax 0.72)
LAUNDRY_ITEMS = [
    # (name, w, h, colours dark->light)
    ('sheet', 8, 8, [SN[1], SN[2], SN[3]]),
    ('shirt', 7, 6, [TE[2], TE[3], TE[4]]),
    ('towel', 5, 7, [RU[1], RU[2], RU[3]]),
    ('johns', 5, 8, [SN[0], SN[1], SN[2]]),
    ('apron', 6, 6, [SA[1], SA[2], SA[3]]),
    ('cloth', 6, 7, [SN[1], SN[2], SN[3]]),
]
LAUNDRY_FRAMES = 4


def laundry():
    """Per item a strip of 4 sway frames (0 = hanging still, 1/2 = blown right, 3 = flutter back).
    Cell = (w+4) x (h+2); the peg row is y=0, item hangs from x=1."""
    out = []
    for name, w, h, cols in LAUNDRY_ITEMS:
        cw, chh = w + 4, h + 2
        S = Layer(cw * LAUNDRY_FRAMES, chh, 'laundry_' + name)
        for f in range(LAUNDRY_FRAMES):
            shear = [0.0, 1.2, 2.4, -0.8][f]
            lift = [0, 0, 1, 0][f]
            for yy in range(h - lift):
                t = yy / max(1, h - 1)
                off = int(round(shear * t * t))
                for xx in range(w):
                    # shirt: sleeves at the top, narrower body
                    if name == 'shirt' and yy > 1 and (xx == 0 or xx == w - 1):
                        continue
                    if name == 'johns' and yy > 3 and xx == w // 2:
                        continue
                    if name == 'apron' and yy < 2 and (xx < 1 or xx > w - 2):
                        continue
                    c = cols[1]
                    if xx == 0:
                        c = cols[0]
                    elif xx == w - 1 or (yy == 0 and xx > w // 2):
                        c = cols[2]
                    if name == 'towel' and yy in (1, h - 2):
                        c = SN[2]
                    if yy == h - lift - 1 and f in (2, 3):
                        c = cols[0]
                    S.px(f * cw + 1 + xx + off, 1 + yy, c, 0.5)
            # pegs
            S.px(f * cw + 1, 0, WO[3])
            S.px(f * cw + w, 0, WO[3])
        out.append((name, S, [cw, chh]))
    return out


# =========================================================================== amber window silhouettes
def window_silhouettes(w=24, h=24):
    """Frames over the cabin's amber window (window-local pixels): the signalman as a dark warm silhouette.
    0 empty, 1 standing left pane, 2 crossing the mullion, 3 bent over the desk (right), 4 seated head,
    5 seated + cup raised, 6 seated head turned.  Transparent where the window shows through."""
    D, d = RU[0], WO[0]
    frames = []

    def person(S, ox, x, top, shoulders=True, bend=0, cup=False, turn=False):
        # head (5x5 rounded) + neck + shoulders block down to the sill
        hx = x
        for yy in range(5):
            for xx in range(5):
                if (yy in (0, 4)) and (xx in (0, 4)):
                    continue
                S.px(ox + hx + xx + (1 if bend and yy < 2 else 0), top + yy + bend, D)
        if turn:
            S.px(ox + hx + 5, top + 2, D)           # nose profile
        S.rect(ox + hx + 1, top + 5 + bend, 3, 1, D)
        if shoulders:
            S.rect(ox + hx - 3, top + 6 + bend, 11, h - top - 6 - bend, d)
            S.rect(ox + hx - 2, top + 6 + bend, 9, h - top - 6 - bend, D)
        if cup:
            S.rect(ox + hx + 5, top + 3, 2, 3, d)
            S.px(ox + hx + 7, top + 4, d)
            S.rect(ox + hx + 3, top + 6, 3, 3, D)   # raised forearm
    S = Layer(w * 7, h, 'win_sil')
    person(S, w * 1, 3, 4)
    person(S, w * 2, 9, 4)
    person(S, w * 3, 14, 7, bend=2)
    person(S, w * 4, 8, 12)
    person(S, w * 5, 8, 12, cup=True)
    person(S, w * 6, 8, 12, turn=True)
    # keep the window frame/mullion in front of the person (mullion x = w//2, transom y = h//3)
    for f in range(1, 7):
        S.c[:, f * w + w // 2] = CLEAR
        S.c[h // 3, f * w:(f + 1) * w] = CLEAR
    # sill: never draw on the bottom row
    S.c[h - 1, :] = CLEAR
    return S


def small_window_silhouettes(w, h, mull_x, transom_y):
    """Distant lit windows (near background): 0 empty, 1 somebody in the left pane, 2 in the right pane,
    3 a curtain drawn half across.  Mullion / transom pixels stay transparent (the window frame shows)."""
    D, d = RU[0], WO[0]
    S = Layer(w * 4, h, 'win_small')

    def person(ox, px_):
        S.rect(ox + px_, h - 9, 2, 2, D)                 # head
        S.rect(ox + px_ - 1, h - 6, 4, 6, D)             # shoulders / body
        S.px(ox + px_ + 2, h - 6, d)
    person(w * 1, 1)
    person(w * 2, w - 3)
    for yy in range(h):                                  # curtain drawn across the left half, one fold
        for xx in range(w // 2 + 1):
            S.px(w * 3 + xx, yy, d if xx != 1 else RU[0])
    for f in range(4):
        S.c[:, f * w + mull_x] = CLEAR
        if transom_y >= 0:
            S.c[transom_y, f * w:(f + 1) * w] = CLEAR
    return S


# =========================================================================== small FX sprites
def glint_strip():
    """Subtle glint for hidden finds: 5 frames 5x5 (off, dot, small plus, plus, dot)."""
    S = Layer(5 * 5, 5, 'glint')
    hi, mid = SN[4], SK[4]
    f1 = [(2, 2, mid)]
    f2 = [(2, 2, hi), (1, 2, mid), (3, 2, mid), (2, 1, mid), (2, 3, mid)]
    f3 = [(2, 2, hi), (1, 2, hi), (3, 2, hi), (2, 1, hi), (2, 3, hi), (0, 2, mid), (4, 2, mid), (2, 0, mid),
          (2, 4, mid)]
    for f, pts in enumerate([[], f1, f2, f3, f1]):
        for (x, y, c) in pts:
            S.px(f * 5 + x, y, c, em=c)
    return S


def cloth_flutter_strip():
    """Red cloth corner of the cache bundle under the stairs: 4 frames 7x5 (still, lift, flap, lift)."""
    S = Layer(7 * 4, 5, 'cloth')
    shapes = [
        ["......", "......", "......", "##....", "###..."],
        ["......", "......", "..#...", "###...", "##...."],
        ["......", "...##.", "..##..", "###...", "##...."],
        ["......", "......", "..##..", "###...", "##...."],
    ]
    for f, rows in enumerate(shapes):
        for y, r in enumerate(rows):
            for x, ch in enumerate(r):
                if ch == '#':
                    c = RED[1] if (x + y) % 3 else RED[2]
                    if y == 4 or x == 0:
                        c = RED[0]
                    S.px(f * 7 + x, y, c)
    return S


def mitten_strip():
    """Child's red knitted mitten pushed onto a fence post (fingers up, thumb left, white cuff around the
    post top): 4 frames 9x10 (still, gust lean, flap, settle).  Anchor = cuff bottom centre (4, 9)."""
    arts = [
        """
...rRR...
..rRRRq..
..rRpRq..
r.rRRRq..
rrRpRRq..
.rRRRRq..
.rRRpRq..
.rRRRRq..
.wwwwww..
.pwwwwp..""",
        """
....rRR..
...rRRRq.
..rRpRRq.
r.rRRRRq.
rrRpRRq..
.rRRRRq..
.rRRpRq..
.rRRRRq..
.wwwwww..
.pwwwwp..""",
        """
.....rR..
....rRRRq
...rRpRRq
r.rRRRRq.
rrRpRRq..
.rRRRRq..
.rRRpRq..
.rRRRRq..
.wwwwww..
.pwwwwp..""",
        """
...rRR...
..rRRRRq.
..rRpRq..
r.rRRRq..
rrRpRRq..
.rRRRRq..
.rRRpRq..
.rRRRRq..
.wwwwww..
.pwwwwp..""",
    ]
    leg = {'R': RED[2], 'r': RED[1], 'q': RED[3], 'w': SN[3], 'p': SN[1]}
    S = Layer(9 * 4, 10, 'mitten')
    for f, a in enumerate(arts):
        stamp(S, f * 9, 0, a, leg)
    return S


def bulb_glow():
    """Lamp-post 2 bulb (emissive) and its dark state, 2 frames 5x3: 0 lit, 1 dark."""
    S = Layer(10, 3, 'bulb')
    for x in range(3):
        S.px(1 + x, 0, SN[4], em=SN[4])
        S.px(1 + x, 1, SN[4], em=SN[4])
    S.px(2, 2, SK[5], em=SK[5])
    for x in range(3):
        S.px(5 + 1 + x, 0, ST[2])
        S.px(5 + 1 + x, 1, ST[3])
    S.px(5 + 2, 2, ST[2])
    return S


# =========================================================================== review sheet
def review_sheet(path, scale=8):
    from PIL import Image
    tiles = []
    for S in [crows()[0], cat()[0], window_silhouettes(), glint_strip(), cloth_flutter_strip(), mitten_strip(),
              bulb_glow(), smoke_puff_strip()] + [s for _, s, _ in laundry()] + \
             [train()['loco']] + train()['wagons']:
        a = S.c.copy()
        bg = np.zeros_like(a)
        bg[..., :3] = (38, 52, 50)
        bg[..., 3] = 255
        m = a[..., 3] > 0
        bg[m] = a[m]
        tiles.append(np.kron(bg, np.ones((scale, scale, 1), np.uint8)))
    W = max(t.shape[1] for t in tiles)
    H = sum(t.shape[0] + 6 for t in tiles)
    out = np.full((H, W, 4), 16, np.uint8)
    out[..., 3] = 255
    y = 0
    for t in tiles:
        out[y:y + t.shape[0], :t.shape[1]] = t
        y += t.shape[0] + 6
    Image.fromarray(out).save(path)


if __name__ == '__main__':
    review_sheet(_sys.argv[1] if len(_sys.argv) > 1 else 'sprites_review.png')
