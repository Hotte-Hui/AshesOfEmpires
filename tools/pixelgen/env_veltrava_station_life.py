"""env_veltrava_station_life -- ambient-life sprite strips for L_C3_Station (polish pass, 2026-11-06).

Frame strips (horizontal, palette 'veltrava', binary alpha) for the station's actors (scene.json "actors",
TECHNICAL_ARCHITECTURE §12.2): the pigeon flock that tugs at a sandwich (exp_pigeons), travellers and a porter
walking on the island platform, a tram that waits in the station square (seen through the exit arch), a small
train crossing the river viaduct far behind the station, passengers moving behind lit compartment windows and
breath puffs.  Everything is original procedural pixel art with fixed seeds (no reference is ever sampled);
env_veltrava_station.py calls build(...) and merges the returned actor entries into scene.json.
"""
from __future__ import annotations

import math
import os

import numpy as np

from env_veltrava_lib import (ENV_DIR, Layer, NI, SL, IR, CR, PA, LA, SK, SN, RD, text, text_width, value_noise,
                              layer_w)

ACTOR_DIR = os.path.join(ENV_DIR, 'actors')
RES = 'res://assets/environments/veltrava_station/actors/'
SCN = 'res://scenes/levels/veltrava_station/'
KARSK_SCN = 'res://scenes/levels/karsk/'


def _save(L: Layer, name: str, normal: bool = False) -> str:
    os.makedirs(ACTOR_DIR, exist_ok=True)
    L.save(os.path.join(ACTOR_DIR, name), normal=normal, emission=bool(L.em[..., 3].any()))
    return RES + name + '.png'


def _ascii(L: Layer, ox: int, oy: int, rows, cmap, em=None):
    for y, row in enumerate(rows):
        for x, ch in enumerate(row):
            if ch in cmap:
                L.px(ox + x, oy + y, cmap[ch], 0.6, em.get(ch) if em else None)


# =========================================================================== pigeons (exp_pigeons)
PIGEON_CELL = (12, 10)
PIGEON_FRAMES = ['idle_a', 'idle_b', 'peck_a', 'peck_b', 'tug', 'walk', 'takeoff', 'fly_up', 'fly_mid',
                 'fly_down', 'glide']
_PC = {'b': SN[0], 'w': SN[1], 's': SL[4], 'h': SL[3], 'n': PA[3], 'k': NI[2], 'f': RD[3], 'e': LA[3],
       'i': SL[1], 'd': SL[2], 'g': LA[1]}
# facing right, feet on row 9 (origin (5, 9)); rock doves: pale grey body, darker head, green neck sheen,
# two black wing bars, dark tail band, pink feet
_PIGEON = {
    # polish: wing bars as a diagonal pair at the rear of the folded wing (two dots mid-body read as eyes)
    'idle_a': ["............", "........hh..", ".......hhhe.", ".......nnhi.", "...wwwwbnn..", "..wwwkwbbbs.",
               "kkwwkwbbbbs.", "...ssbbbbs..", "....g..g....", "....f..f...."],
    'idle_b': ["........hh..", ".......hhhe.", ".......nnhi.", "........nn..", "...wwwwbnn..", "..wwwkwbbbs.",
               "kkwwkwbbbbs.", "...ssbbbbs..", "....g..g....", "....f..f...."],
    'peck_a': ["............", "............", "............", "............", "...wwwwbnhh.", "..wwwkwbbnhe",
               "kkwwkwbbbbsi", "...ssbbbbs..", "....g..g....", "....f..f...."],
    'peck_b': ["............", "............", "............", "............", "...wwwwbb...", "..wwwkwbbnn.",
               "kkwwkwbbbbnh", "...ssbbbbshh", "....g..g...i", "....f..f...."],
    'tug':    ["............", "............", "............", "..wwwwb.....", ".wwwkwbbn...", "kwwkwbbbbnn.",
               "k..ssbbbbshh", ".........hhe", "...g..g...ii", "...f..f....."],
    'walk':   ["............", "........hh..", ".......hhhe.", ".......nnhi.", "...wwwwbnn..", "..wwwkwbbbs.",
               "kkwwkwbbbbs.", "...ssbbbbs..", "...g....g...", "..f......f.."],
    'takeoff': ["..w.........", "..ww....hh..", "..www..hhhe.", "...www.nnhi.", "...wwwwbnn..", "..wwwkwbbbs.",
                "kkwwkwbbbbs.", "...ssbbbbs..", "....f..f....", "............"],
    'fly_up': [".w.......w..", ".ww.....ww..", "..ww...ww...", "...wwwww.hh.", "kkwwkwwbnhhe", ".kssbbbbbsi.",
               "...ssssss...", "............", "............", "............"],
    'fly_mid': ["............", "............", "............", ".........hh.", "kkwwkwwbnhhe", "wwwwkwkbbwwi",
                "...ssssss...", "............", "............", "............"],
    'fly_down': ["............", "............", "............", ".........hh.", "kkkbbbbbnhhe", ".kssbbbbbsi.",
                 "..wwwwww....", "..ww...ww...", ".ww.....ww..", "............"],
    'glide':  ["............", "............", ".ww......ww.", "..wwwwwww.hh", "kkwwkwkbbnhe", ".kssbbbbbs.i",
               "...ssssss...", "............", "............", "............"],
}


def pigeon_sheet() -> Layer:
    cw, ch = PIGEON_CELL
    S = Layer(cw * len(PIGEON_FRAMES), ch, 'pigeons_sheet')
    for i, name in enumerate(PIGEON_FRAMES):
        _ascii(S, i * cw, 0, _PIGEON[name], _PC)
    return S


def bread_sprite() -> Layer:
    """A buttered slice of bread from the delegation's provisions (exp_pigeons), 6x3, origin bottom-left."""
    S = Layer(6, 3, 'bread')
    S.rect(0, 1, 6, 2, CR[4])
    S.hline(0, 0, 6, CR[2])
    S.px(2, 1, LA[4]); S.px(3, 1, LA[4])
    S.px(5, 2, CR[3])
    return S


# =========================================================================== side-view walkers (island)
WALK_FRAMES = 8


def _side_person(S: Layer, ox: int, oy_base: int, H: int, phase: float, spec: dict, facing: int, stand=False):
    """One side-view figure, feet on oy_base, centred on ox.  phase 0..1 = stride cycle (two steps)."""
    coat = spec['coat']
    k = H / 36.0
    head_h = max(4, int(round(5 * k)))
    head_w = max(3, int(round(4 * k)))
    top = oy_base - H + 1
    sh_y = top + head_h + 1
    hip_y = oy_base - int(round(H * 0.46))
    hem_y = oy_base - int(round(H * spec.get('hem', 0.3)))
    body_w = max(5, int(round(7.2 * k * spec.get('width', 1.0))))
    a = 0.0 if stand else math.sin(2 * math.pi * phase)
    leg_len = oy_base - hip_y
    stride = 0.0 if stand else 4.2 * k
    lift = 0 if stand else (1 if abs(math.cos(2 * math.pi * phase)) > 0.8 else 0)
    trousers = spec.get('trousers', NI[2])
    boots = spec.get('boots', NI[0])
    skin = spec.get('skin', CR[3])
    f = facing
    # legs (far leg darker), drawn as 2-px lines from the hip to the foot
    for leg, col in ((-1, NI[1]), (1, trousers)):
        fx = ox + f * leg * a * stride
        for y in range(hip_y, oy_base + 1):
            t = (y - hip_y) / max(1, leg_len)
            x = ox + (fx - ox) * t
            S.px(int(round(x)), y - (lift if leg > 0 and t > 0.8 else 0), col)
            S.px(int(round(x)) - f, y - (lift if leg > 0 and t > 0.8 else 0), col)
        S.px(int(round(fx)) + f, oy_base, boots)
        S.px(int(round(fx)), oy_base, boots)
        S.px(int(round(fx)) - f, oy_base, boots)
    # coat: trapezoid shoulders -> hem, swinging a pixel with the stride
    sway = int(round(a * 1.2 * k)) if not stand else 0
    for y in range(sh_y, hem_y + 1):
        t = (y - sh_y) / max(1, hem_y - sh_y)
        w = body_w + int(round(t * 2 * k * spec.get('flare', 1.0)))
        x0 = ox - w // 2 + (int(round(sway * t)) if t > 0.6 else 0)
        for x in range(x0, x0 + w):
            rel = (x - x0) / max(1, w - 1)
            c = coat[1]
            if (rel < 0.3 and f > 0) or (rel > 0.7 and f < 0):
                c = coat[0]                                  # back side in shade
            S.px(x, y, c)
        S.px(x0 + w - 1, y, coat[2] if len(coat) > 2 else coat[1])   # dawn rim (key light from the right)
    S.hline(ox - body_w // 2, hip_y - 1, body_w, coat[0])          # belt line
    # arm: swings opposite to the near leg, or holds the luggage down at the side
    carry = spec.get('carry')
    sx = ox + f * 1
    if carry:
        for y in range(sh_y + 1, sh_y + int(round(H * 0.32))):
            S.px(sx, y, coat[0])
        hy = sh_y + int(round(H * 0.32))
        bw, bh, bc = carry
        bx = sx - bw // 2 + f
        S.rect(bx, hy, bw, bh, bc[1])
        S.hline(bx, hy, bw, bc[2])
        S.px(bx + bw // 2, hy - 1, bc[0])
        S.vline(bx + (0 if f > 0 else bw - 1), hy, bh, bc[0])
    else:
        swing = 0.0 if stand else -a * 2.6 * k
        for i in range(int(round(H * 0.3))):
            t = i / max(1, H * 0.3)
            S.px(int(round(sx + f * swing * t)), sh_y + 1 + i, coat[0])
        S.px(int(round(sx + f * swing)), sh_y + int(round(H * 0.3)) + 1, skin)
    # head + hat
    hx0 = ox - head_w // 2 + (1 if f > 0 else 0)
    S.rect(hx0, top + 1, head_w, head_h, skin)
    S.vline(hx0 + (0 if f > 0 else head_w - 1), top + 1, head_h, spec.get('hair', NI[2]))   # hair / back
    S.px(hx0 + (head_w - 1 if f > 0 else 0), top + 1 + head_h // 2, CR[2])               # nose / shade
    S.hline(hx0, top + head_h, head_w, spec.get('collar', coat[0]))
    hat = spec.get('hat')
    hc = spec.get('hat_col', NI[1])
    if hat in ('fedora', 'homburg'):
        S.rect(hx0 - 1, top + 1, head_w + 2, 1, hc)
        S.rect(hx0, top - 1, head_w, 2, hc)
    elif hat == 'cap':
        S.rect(hx0, top, head_w, 2, hc)
        S.px(hx0 + (head_w if f > 0 else -1), top + 1, hc)
    elif hat == 'scarf':
        S.rect(hx0 - 1, top, head_w + 2, 2, hc)
        S.vline(hx0 - (1 if f > 0 else -head_w), top + 1, head_h, hc)
    elif hat == 'shapka':
        S.rect(hx0 - 1, top - 1, head_w + 2, 3, hc)
    if spec.get('lamp'):                                   # railwayman's hand lamp (warm, emissive)
        lx, ly = int(round(sx + f * 1)), sh_y + int(round(H * 0.3)) + 2
        S.rect(lx - 1, ly, 3, 3, IR[2])
        S.px(lx, ly + 1, LA[3], em=LA[3])


# coats one value step lighter than the delegation's black: the island people stand in front of the dark German
# special train and must read as silhouettes against it (the rim colour is the dawn key light from the right)
WALKERS = {
    'official': dict(coat=[IR[1], IR[2], SL[4]], hat='homburg', hat_col=NI[1], hem=0.26,
                     carry=(5, 4, [NI[1], LA[0], LA[1]])),
    'woman_scarf': dict(coat=[CR[1], CR[2], CR[4]], hat='scarf', hat_col=RD[2], hem=0.3, width=0.95, flare=1.6,
                        trousers=NI[3], skin=CR[4]),
    'traveller': dict(coat=[SL[1], SL[2], SL[4]], hat='fedora', hat_col=SL[0], hem=0.3,
                      carry=(6, 5, [CR[0], CR[2], CR[3]])),
    'railwayman': dict(coat=[SL[0], SL[1], SL[3]], hat='cap', hat_col=NI[1], hem=0.36, lamp=True),
    'woman_fur': dict(coat=[SL[1], SL[2], SL[4]], hat='shapka', hat_col=CR[2], hem=0.28, width=0.95, flare=1.4,
                      carry=(4, 4, [LA[0], RD[1], RD[2]]), skin=CR[4]),
    'soviet_staff': dict(coat=[PA[1], PA[2], PA[3]], hat='shapka', hat_col=NI[2], hem=0.3,
                         carry=(5, 4, [NI[1], IR[1], IR[2]])),
}


def walker_sheet(kind: str, H: int = 34):
    """Frames 0-7 walking right, 8-15 walking left, 16 standing right, 17 standing left (rim always right)."""
    spec = WALKERS[kind]
    cw, ch = int(round(H * 0.5)) + 6, H + 3
    n = WALK_FRAMES * 2 + 2
    S = Layer(cw * n, ch, 'walker_' + kind)
    for i in range(n):
        facing = 1 if (i < WALK_FRAMES or i == 16) else -1
        stand = i >= 16
        ph = (i % WALK_FRAMES) / WALK_FRAMES
        _side_person(S, i * cw + cw // 2, ch - 1, H, ph, spec, facing, stand=stand)
    return S, (cw, ch)


def porter_sheet(H: int = 33):
    """Porter in a blue smock and peaked cap pushing a two-wheeled luggage barrow (8 frames right, 8 left)."""
    spec = dict(coat=[SL[1], SL[2], SL[4]], hat='cap', hat_col=NI[2], hem=0.38, trousers=NI[3])
    cw, ch = 40, H + 3
    S = Layer(cw * 16, ch, 'porter_barrow')
    for i in range(16):
        f = 1 if i < 8 else -1
        ph = (i % 8) / 8.0
        ox = i * cw + (14 if f > 0 else cw - 14)
        _side_person(S, ox, ch - 1, H, ph, spec, f)
        # barrow in front of him: two wheels, a deck with trunks, handles to his hands
        bx = ox + f * 6
        deck_y = ch - 9
        for kx in range(0, 18):
            S.px(bx + f * kx, deck_y, CR[1])
            S.px(bx + f * kx, deck_y + 1, CR[0])
        wx = bx + f * 13
        S.rect(wx - 2, ch - 5, 5, 5, NI[2])
        S.px(wx, ch - 3, IR[3])
        for (o, w, h, c) in ((2, 7, 6, (LA[0], LA[1])), (9, 7, 4, (IR[1], IR[2])), (4, 5, 3, (PA[0], PA[1]))):
            y0 = deck_y - h - (6 if o == 4 else 0)
            x0 = bx + f * o if f > 0 else bx + f * o - w + 1
            S.rect(x0, y0, w, h, c[0])
            S.hline(x0, y0, w, c[1])
        hy = deck_y - 1 - int(round(2 * math.sin(2 * math.pi * ph) ** 2))
        S.px(ox + f * 2, hy - 6, SL[1]); S.px(ox + f * 3, hy - 5, SL[1])
        S.px(ox + f * 4, hy - 3, IR[1]); S.px(ox + f * 5, hy - 2, IR[1])
    return S, (cw, ch)


# =========================================================================== tram (station square)
def tram_sprite():
    """Veltrava tram 7, cream and red, lit windows, a hand-written trilingual line board in the front window
    (find text: Bahnhof – Palais – Altstadt).  Facing right (the board is at the right end).  72x36."""
    S = Layer(72, 36, 'tram')
    S.rect(2, 12, 68, 18, CR[4])
    S.rect(2, 24, 68, 6, RD[2])
    S.hline(2, 24, 68, RD[3])
    S.hline(2, 29, 68, RD[1])
    S.rect(4, 8, 64, 4, CR[3])                     # clerestory roof
    S.hline(4, 7, 64, SN[4])
    S.hline(2, 12, 68, CR[5])
    for k in range(7):                             # lit passenger windows (emissive)
        wx = 5 + k * 9
        S.rect(wx, 14, 7, 8, LA[3], em=LA[3])
        S.hline(wx, 14, 7, LA[2], )
        if k % 3 == 1:
            S.rect(wx + 2, 16, 3, 6, LA[0], em=LA[0])          # passenger
            S.rect(wx + 2, 15, 3, 1, LA[0], em=LA[0])
    S.rect(66, 13, 4, 10, LA[4], em=LA[4])         # driver's window
    S.rect(57, 9, 12, 5, SN[4])                    # line board, chalk on white enamel, three languages
    for r_, w_ in ((10, 9), (12, 7)):
        S.hline(58, r_, w_, SL[1])
    text(S, 3, 25, '7', SN[4])
    S.rect(6, 30, 8, 3, NI[2])                     # bogies
    S.rect(56, 30, 8, 3, NI[2])
    S.px(8, 32, IR[3]); S.px(60, 32, IR[3])
    S.vline(36, 1, 7, IR[2])                       # pole + shoe to the wire
    S.hline(33, 0, 7, IR[3])
    S.vline(2, 12, 18, CR[2]); S.vline(69, 12, 18, CR[5])
    return S


# =========================================================================== viaduct train (far, parallax 0.2)
VIADUCT_P = 0.2
VIADUCT_RAIL = 108          # screen y of the viaduct rail (well above the station roofs, in front of the castle hill)


def viaduct_layer():
    """River viaduct far behind the station: a long deck on tall stone arches crossing the valley in front of
    the castle hill.  Separate parallax plane (0.2) between the old town (0.1) and the city (0.3).  Kept deep in
    the haze (values of the old town behind it, wide 34 px spans): only the deck line reads clearly, so the
    small dark train crossing it is what the eye catches, not the masonry."""
    W = layer_w(VIADUCT_P, 16)
    L = Layer(W, 360, 'viaduct')
    deck = VIADUCT_RAIL + 1
    span = 34
    spring, r = deck + 15, 13.5
    for xx in range(W):                             # piers and round arches
        u = (xx + 9) % span - span / 2 + 0.5
        for y in range(deck + 4, deck + 48):
            opening = abs(u) < r and (y >= spring or u * u + (y + 0.5 - spring) ** 2 <= r * r)
            if not opening:
                edge = abs(u) < r + 1.0 and (y >= spring or u * u + (y + 0.5 - spring) ** 2 <= (r + 1.0) ** 2)
                L.px(xx, y, SK[2] if edge else SK[3], 0.3)
    L.rect(0, deck, W, 4, SK[1], hgt=0.5)            # deck + parapet: the one darker line in the haze
    L.hline(0, deck, W, SK[3])
    L.hline(0, deck + 3, W, SK[2])
    for x in range(0, W, 6):
        L.px(x, deck - 1, SK[1])                     # parapet posts
    L.hline(0, deck - 2, W, SK[2])
    return L


def viaduct_train():
    """Tiny goods train for the viaduct (KarskTrain actor: loco art faces left).  Returns sprites + puff."""
    loco = Layer(20, 10, 'viaduct_loco')
    loco.rect(2, 3, 12, 5, NI[3])                   # boiler
    loco.rect(13, 1, 6, 7, NI[2])                   # cab
    loco.px(15, 3, LA[3], em=LA[3])                 # firebox glow in the cab window
    loco.rect(3, 1, 2, 2, NI[2])                    # chimney
    loco.hline(1, 8, 18, NI[1])
    for wx in (4, 8, 12, 16):
        loco.px(wx, 9, NI[1])
    loco.hline(2, 3, 11, SL[1])                     # boiler top catches the sky
    wag_box = Layer(14, 9, 'viaduct_wag_box')
    wag_box.rect(0, 1, 14, 6, CR[0])
    wag_box.hline(0, 1, 14, CR[1])
    wag_box.hline(0, 0, 14, SN[1])                  # snow on the roof
    wag_box.px(2, 8, NI[1]); wag_box.px(11, 8, NI[1])
    wag_box.hline(0, 7, 14, NI[2])
    wag_tank = Layer(13, 9, 'viaduct_wag_tank')
    wag_tank.rect(1, 2, 11, 4, IR[2])
    wag_tank.hline(1, 2, 11, IR[3])
    wag_tank.hline(0, 6, 13, NI[2])
    wag_tank.px(2, 8, NI[1]); wag_tank.px(10, 8, NI[1])
    wag_tank.hline(0, 7, 13, NI[1])
    wag_flat = Layer(14, 9, 'viaduct_wag_flat')
    wag_flat.rect(1, 3, 12, 3, SL[1])               # tarpaulin load
    wag_flat.hline(1, 3, 12, SN[1])
    wag_flat.hline(0, 6, 14, NI[2])
    wag_flat.px(2, 8, NI[1]); wag_flat.px(11, 8, NI[1])
    wag_flat.hline(0, 7, 14, NI[1])
    puff = Layer(8 * 10, 10, 'viaduct_puff')
    for f in range(8):
        r = 1.2 + f * 0.55
        cx, cy = f * 10 + 5, 6 - f * 0.4
        for y in range(10):
            for x in range(10):
                if (x + 0.5 - 5) ** 2 + (y + 0.5 - cy) ** 2 <= r * r and (f < 5 or (x + y + f) % 2 == 0):
                    puff.px(f * 10 + x, y, SN[2] if y < cy else SN[1])
    return loco, [wag_box, wag_tank, wag_flat], puff


# =========================================================================== compartment silhouettes
def window_life_sheet():
    """KarskWindowLife 'small' strip for a lit compartment window (16x17): 0 empty, 1 passenger seated by the
    window, 2 somebody standing in the compartment, 3 a hand wiping a peephole in the misted glass."""
    S = Layer(16 * 4, 17, 'window_life')
    sil = LA[0]
    o = 16
    S.rect(o + 3, 10, 6, 7, sil); S.rect(o + 4, 6, 4, 4, sil); S.hline(o + 4, 5, 4, NI[2])
    o = 32
    S.rect(o + 6, 6, 5, 11, sil); S.rect(o + 7, 2, 3, 4, sil); S.px(o + 11, 9, sil)
    o = 48
    S.rect(o + 2, 9, 7, 8, sil); S.rect(o + 3, 5, 5, 4, sil)
    S.rect(o + 10, 6, 3, 4, CR[3]); S.px(o + 11, 5, CR[3]); S.px(o + 12, 10, sil)
    return S


def breath_puff():
    """Breath cloud strip (6 frames, 7x7): a pale puff that swells and thins out."""
    S = Layer(42, 7, 'breath_puff')
    for f in range(6):
        r = 1.0 + f * 0.6
        for y in range(7):
            for x in range(7):
                d = (x + 0.5 - 3.5) ** 2 + (y + 0.5 - 3.5) ** 2
                if d <= r * r and (f < 3 or (x * 3 + y + f) % (2 if f < 5 else 3) == 0):
                    S.px(f * 7 + x, y, SN[3] if f < 2 else (SN[2] if f < 4 else SN[1]))
    return S


# =========================================================================== build
def build(A: dict) -> tuple[list, list]:
    """A = anchors from the orchestrator.  Returns (actor entries, extra layers [(Layer, name, parallax, z)])."""
    actors = []
    # ---- pigeon flock with the sandwich (exp_pigeons): spots on the snowy rear edge of the platform
    psheet = _save(pigeon_sheet(), 'pigeons_sheet')
    bread = _save(bread_sprite(), 'bread')
    actors.append({'scene': SCN + 'StationPigeons.tscn', 'pos': [478, 279], 'props': {
        'sprite': psheet, 'bread': bread, 'bread_pos': [476, 279],
        'spots': [[472, 279], [481, 280], [492, 277], [462, 281], [503, 279]],
        'tuggers': 2, 'scare_radius': 13.0, 'run_radius': 52.0, 'roost_y': 26.0},
        'note': 'exp_pigeons: two tug at a sandwich, a third waits at the edge; they tolerate a walking '
                'observer and only fly up when somebody runs past or steps right into them'})
    # ---- walkers and a porter on the island platform (parallax 0.93, feet on the island surface)
    sheets = []
    for i, kind in enumerate(('official', 'woman_scarf', 'traveller', 'railwayman', 'woman_fur', 'soviet_staff')):
        S, cell = walker_sheet(kind, 34 if i % 2 == 0 else 33)
        sheets.append({'file': _save(S, 'walker_' + kind), 'cell': list(cell), 'frames': 18,
                       'speed': [17.0, 23.0] if kind != 'railwayman' else [13.0, 16.0]})
    S, cell = porter_sheet()
    sheets.append({'file': _save(S, 'porter_barrow'), 'cell': list(cell), 'frames': 16, 'speed': [9.0, 11.0],
                   'barrow': True})
    actors.append({'scene': SCN + 'StationWalkers.tscn', 'pos': [0, 232], 'props': {
        'parallax': 0.93, 'z': -39.0, 'span': [560.0, 1440.0], 'count': 6, 'sheets': sheets, 'rng_seed': 931,
        'pause_spots': [[990.0, 2.5, 5.0], [1180.0, 3.0, 6.0]]},
        'note': 'island platform between tracks 4 and 5; seen between wagon 4 and the concourse (cam 480-1280)'})
    # ---- the tram that waits in the station square (seen only through the exit arch)
    tram = _save(tram_sprite(), 'tram')
    actors.append({'scene': SCN + 'StationTram.tscn', 'pos': [1668, 238], 'props': {
        'sprite': tram, 'parallax': 0.85, 'z': -17.0, 'stop_x': 1668.0, 'leave_x': 1800.0, 'enter_x': 1540.0,
        'wait': [34.0, 46.0], 'away': [7.0, 11.0], 'speed': 22.0},
        'note': 'exp_tram: „Vor dem Ausgang wartet die Straßenbahn“ -- it waits most of the time, leaves, the '
                'next one rolls in'})
    # ---- far goods train on the river viaduct (reuses the Karsk train actor)
    loco, wagons, puff = viaduct_train()
    lpath = _save(loco, 'viaduct_loco')
    wpaths = [_save(w, w.name) for w in wagons]
    ppath = _save(puff, 'viaduct_puff')
    actors.append({'scene': KARSK_SCN + 'KarskTrain.tscn', 'pos': [0, VIADUCT_RAIL + 1], 'props': {
        'loco': lpath, 'wagons': wpaths, 'puff': ppath, 'parallax': VIADUCT_P, 'z': -85.0,
        'span': [-60.0, float(layer_w(VIADUCT_P, 16) + 40)], 'speed': 13.0, 'interval': [55.0, 75.0],
        'first_delay': 6.0, 'chimney': [4.0, -10.0], 'wagons_min': 6.0, 'wagons_max': 10.0},
        'note': 'reuses scenes/levels/karsk/KarskTrain.tscn (generic: sprites + timing are props)'})
    # ---- passengers moving behind lit compartment windows (reuses KarskWindowLife, mode small)
    wl = _save(window_life_sheet(), 'window_life')
    for (wx, wy) in A.get('life_windows', []):
        actors.append({'scene': KARSK_SCN + 'KarskWindowLife.tscn', 'pos': [int(wx), int(wy)], 'props': {
            'sprite': wl, 'cell': [16, 17], 'mode': 'small', 'z': -15.0}})
    # ---- breath of the people standing in the cold (reuses KarskBreath)
    bp = _save(breath_puff(), 'breath_puff')
    for grp in A.get('breath', []):
        e = {'scene': KARSK_SCN + 'KarskBreath.tscn', 'pos': [int(grp['pos'][0]), int(grp['pos'][1])], 'props': {
            'points': [[int(p[0]), int(p[1])] for p in grp['points']], 'sprite': bp,
            'interval': float(grp.get('interval', 4.8))}}
        if 'parallax' in grp:
            e['props']['parallax'] = float(grp['parallax'])
        if 'z' in grp:
            e['props']['z'] = float(grp['z'])
        actors.append(e)
    return actors, [(viaduct_layer(), 'viaduct', VIADUCT_P, -86)]
