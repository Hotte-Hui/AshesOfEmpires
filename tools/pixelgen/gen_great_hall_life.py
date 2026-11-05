"""gen_great_hall_life -- street life for the Great Hall reveal (L_M1_HallReveal, shot S011).

Owner: hall (great_hall_3d).  Original, deterministic pixel art (berlin palette), rendered at native size:
the engine shows every sprite at exactly 1 texel = 1 screen pixel ("texel lock"), so each distance band has
its own level of detail instead of scaled sprites.

Outputs (assets/architecture/great_hall/life/):
  walk_<H>.png (+_n)  walk cycles, one row per citizen variant, 8 frames (H = 36, 24) / 4 frames (14, 8);
                      side view facing right, feet on the cell's origin pixel.  life.json lists cells/origins/
                      ground speed (px/s at the nominal fps) so the engine keeps the feet planted.
  stand_<H>.png (+_n) idle loops (breathing / shifting weight) for queues and onlookers.
  march_<H>.png (+_n) a guard patrol marching (greatcoat, helmet, rifle; no insignia).
  sweeper.png (+_n)   municipal street sweeper with a birch broom, 6-frame sweep (46 px class, as the family).
  handcart.png (+_n)  his two-wheeled cart.
  birds.png           pigeons (ground: stand/peck), flying birds (3 wing frames), crows on wires (sit/flap).
  smoke.png           chimney smoke loop (8 frames), steam.png manhole steam loop (8 frames).
  window_people.png   silhouettes seen through lit windows (head-and-shoulders, standing, woman at a curtain).
  kiosk_front.png     newspaper kiosk display (unreadable mastheads), kiosk_sign.png
  tram_stop.png       the round stop sign (green disc, yellow "H")
Run:  py -3 -P tools/pixelgen/gen_great_hall_life.py
"""
from __future__ import annotations

import json
import math
import os
import sys
import zlib

import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pg  # noqa: E402
import gen_great_hall as ggh  # noqa: E402  (own module: Fig rasteriser + material table)

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..',
                                     'assets', 'architecture', 'great_hall', 'life'))
PREV = os.path.normpath(os.path.join(ROOT, '..', '_preview'))
H = pg.hx

NIGHT = ['#120C14', '#1B1520', '#211623', '#2A2130']
VIOLET = ['#25202B', '#342F37', '#443B43', '#57494D']
STONE = ['#4A3A35', '#5F4A40', '#7A5E4E', '#94735C', '#AE8A6C', '#C9A585']
OCHRE = ['#5F4530', '#735145', '#8D5542', '#AF6C47', '#D07744', '#E5945A']
GLOW = ['#E5945A', '#F0AE6E', '#F4BA81', '#F8D2A0', '#FCE9C8']
STEEL = ['#1E2329', '#2F363F', '#454E58', '#5F6973', '#7C8690', '#A3ACB4']
PATINA = ['#1E2E2C', '#2C4440', '#3E5D55', '#56776A', '#73927F']
SNOW = ['#6E6A73', '#8F8A92', '#B2ACB0', '#D2CCCB', '#ECE6E0']

# extra materials for the citizens (3-tone ramps, dark -> light), merged into the shared table of the Fig
# rasteriser (gen_great_hall.MATS, same owner)
EXTRA_MATS = {
    'c_grey': [STEEL[0], STEEL[1], STEEL[2]],
    'c_greyl': [STEEL[1], STEEL[2], STEEL[3]],
    'c_brown': [STONE[0], STONE[1], STONE[2]],
    'c_violet': [VIOLET[0], VIOLET[1], VIOLET[2]],
    'c_ochre': [OCHRE[0], OCHRE[1], OCHRE[2]],
    'c_night': [NIGHT[1], NIGHT[2], NIGHT[3]],
    'c_patina': [PATINA[0], PATINA[1], PATINA[2]],
    'c_snow': [SNOW[1], SNOW[2], SNOW[3]],
    'c_field': [STEEL[0], STEEL[1], STEEL[2]],
    'c_birch': [STONE[1], STONE[2], STONE[3]],
    'c_wood': [NIGHT[3], STONE[0], STONE[1]],
    'c_tin': [STEEL[2], STEEL[3], STEEL[4]],
}
ggh.MATS.update(EXTRA_MATS)

OUTLINE = NIGHT[0]


def out(*parts):
    p = os.path.join(ROOT, *parts)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    return p


def save_rgba(arr, path):
    Image.fromarray(np.asarray(arr, np.uint8), 'RGBA').save(path)


def seed_of(name: str) -> int:
    return zlib.crc32(name.encode('utf-8')) & 0x7FFFFFFF


# ============================================================================ citizens
# kind, coat material, hat, hat material, legs material, accessory, coat length (fraction of H), scale
VARIANTS = [
    {'id': 'man_fedora', 'coat': 'c_grey', 'hat': 'fedora', 'hatm': 'c_night', 'legs': 'trou', 'acc': 'case',
     'hem': 0.74, 'width': 1.0},
    {'id': 'woman_scarf', 'coat': 'c_violet', 'hat': 'scarf', 'hatm': 'c_patina', 'legs': 'stock', 'acc': 'bag',
     'hem': 0.80, 'width': 1.05, 'woman': True},
    {'id': 'man_cap', 'coat': 'c_brown', 'hat': 'cap', 'hatm': 'c_night', 'legs': 'trou', 'acc': '',
     'hem': 0.62, 'width': 1.0},
    {'id': 'woman_hat', 'coat': 'c_ochre', 'hat': 'cloche', 'hatm': 'c_night', 'legs': 'stock', 'acc': 'bag',
     'hem': 0.78, 'width': 1.0, 'woman': True},
    {'id': 'man_coat_dark', 'coat': 'c_night', 'hat': 'fedora', 'hatm': 'c_grey', 'legs': 'trou', 'acc': 'paper',
     'hem': 0.76, 'width': 1.05},
    {'id': 'old_man', 'coat': 'c_greyl', 'hat': 'cap', 'hatm': 'c_brown', 'legs': 'trou', 'acc': 'cane',
     'hem': 0.74, 'width': 1.0, 'stoop': 1},
]


def _leg(f, hip, knee, foot, th, mat, z):
    """Leg as thigh + shin quads (th = half thickness)."""
    for a, b in ((hip, knee), (knee, foot)):
        dx, dy = b[0] - a[0], b[1] - a[1]
        L = max(1e-3, math.hypot(dx, dy))
        nx, ny = -dy / L * th, dx / L * th
        f.poly([(a[0] + nx, a[1] + ny), (a[0] - nx, a[1] - ny), (b[0] - nx, b[1] - ny),
                (b[0] + nx, b[1] + ny)], mat, 0.6, z)


def citizen(Hh: int, v: dict, phase: float, mode: str = 'walk', frame: int = 0):
    """One frame of a citizen (side view facing right) on a (Wc x Hc) cell; returns (Fig, origin)."""
    s = Hh / 36.0
    Wc = int(math.ceil(Hh * 0.62)) + 4
    Hc = Hh + 2
    f = ggh.Fig(Wc, Hc)
    cx = Wc * 0.5 - 0.5
    foot_y = Hc - 1.0
    bob = 0.0
    stoop = v.get('stoop', 0) * s
    if mode == 'walk':
        A = 0.17 * Hh
        if v.get('march'):
            A = 0.19 * Hh
        fa = A * math.cos(phase)
        fb = A * math.cos(phase + math.pi)
        la = max(0.0, -math.sin(phase)) * 0.07 * Hh
        lb = max(0.0, -math.sin(phase + math.pi)) * 0.07 * Hh
        k = int(round(phase / (2 * math.pi) * 8)) % 8
        bob = -1.0 if k in (3, 7) else 0.0
        arm = -0.12 * Hh * math.cos(phase) * (0.45 if v.get('march') else 1.0)
    else:   # stand / idle: weight shift + breathing
        fa, fb, la, lb = 0.06 * Hh, -0.05 * Hh, 0.0, 0.0
        bob = -1.0 if frame in (1, 2) and Hh >= 20 else 0.0
        arm = 0.0
    hip_y = foot_y - 0.47 * Hh + bob
    hip_x = cx
    th = max(0.55, 0.045 * Hh)
    knee_y = foot_y - 0.24 * Hh + bob * 0.5
    legs = v.get('legs', 'trou')
    # back leg (b) first, darker by drawing it lower in the height field
    for (fo, lo, mat, z) in ((fb, lb, legs, 0.0), (fa, la, legs, 0.3)):
        foot = (hip_x + fo, foot_y - lo)
        swing = lo > 0.01
        knee = (hip_x + fo * 0.45 + (0.05 * Hh if swing else 0.0), knee_y - lo * 0.4)
        _leg(f, (hip_x, hip_y), knee, foot, th, mat, z)
        # shoe: a small wedge pointing forward
        fx, fy = foot
        sl = max(1.2, 0.07 * Hh)
        f.poly([(fx - th - 0.3, fy - 1.2 * s - 0.4), (fx + sl, fy - 0.8 * s - 0.3), (fx + sl + 0.4, fy + 0.5),
                (fx - th - 0.3, fy + 0.5)], 'shoe', 0.4, z + 0.1)
    # body / coat: shoulders to hem, the hem follows the legs (flare)
    sh_y = foot_y - 0.81 * Hh + bob
    hw = 0.115 * Hh * v.get('width', 1.0)
    hem_y = foot_y - (1.0 - v.get('hem', 0.74)) * Hh * 0.98 + bob * 0.5
    if v.get('woman'):
        hem_spread = 0.16 * Hh
    else:
        hem_spread = 0.13 * Hh
    front = max(fa, fb) * 0.35
    back = min(fa, fb) * 0.35
    lean = stoop
    coat = v['coat']
    f.poly([(cx - hw + lean, sh_y + 0.5), (cx + hw * 0.8 + lean, sh_y), (cx + hw + lean * 0.5, sh_y + 0.18 * Hh),
            (cx + hem_spread + front, hem_y), (cx - hem_spread + back, hem_y), (cx - hw - 0.3, sh_y + 0.2 * Hh)],
           coat, 1.6, 0.6)
    # collar
    f.poly([(cx - hw * 0.7 + lean, sh_y - 0.3), (cx + hw * 0.6 + lean, sh_y - 0.5), (cx + hw * 0.7 + lean,
            sh_y + 0.07 * Hh), (cx - hw * 0.7 + lean, sh_y + 0.07 * Hh)], coat, 0.8, 1.0)
    # head
    hr = max(1.0, 0.075 * Hh)
    hx = cx + 0.25 * hr + lean * 1.4
    hy = sh_y - hr * 1.15
    f.ell(hx, hy, hr * 0.95, hr * 1.05, 'skin', 1.0, 1.2)
    if Hh >= 20:
        f.px(int(hx + hr * 0.95), int(hy), '#94735C')            # nose
    # hat
    hat = v.get('hat', '')
    hm = v.get('hatm', 'c_night')
    if hat == 'fedora':
        f.poly([(hx - hr * 1.0, hy - hr * 0.55), (hx - hr * 0.7, hy - hr * 1.45), (hx + hr * 0.75, hy - hr * 1.5),
                (hx + hr * 1.0, hy - hr * 0.55)], hm, 0.8, 1.6)
        f.poly([(hx - hr * 1.55, hy - hr * 0.35), (hx + hr * 1.6, hy - hr * 0.45), (hx + hr * 1.55, hy - hr * 0.1),
                (hx - hr * 1.55, hy - hr * 0.05)], hm, 0.4, 1.7)
    elif hat == 'cap':
        f.poly([(hx - hr * 1.0, hy - hr * 0.35), (hx - hr * 0.6, hy - hr * 1.25), (hx + hr * 0.9, hy - hr * 1.2),
                (hx + hr * 1.9, hy - hr * 0.45), (hx + hr * 1.0, hy - hr * 0.3)], hm, 0.7, 1.6)
    elif hat == 'scarf':
        f.poly([(hx - hr * 1.15, hy + hr * 0.3), (hx - hr * 0.9, hy - hr * 1.15), (hx + hr * 0.6, hy - hr * 1.25),
                (hx + hr * 1.1, hy - hr * 0.3), (hx + hr * 0.4, hy - hr * 0.2), (hx - hr * 0.2, hy + hr * 1.0),
                (hx - hr * 0.9, hy + hr * 1.1)], hm, 0.9, 1.6)
    elif hat == 'cloche':
        f.poly([(hx - hr * 1.2, hy - hr * 0.1), (hx - hr * 0.9, hy - hr * 1.3), (hx + hr * 0.8, hy - hr * 1.3),
                (hx + hr * 1.2, hy - hr * 0.2)], hm, 0.8, 1.6)
    elif hat == 'helmet':
        f.poly([(hx - hr * 1.35, hy + hr * 0.25), (hx - hr * 1.1, hy - hr * 1.1), (hx - hr * 0.2, hy - hr * 1.45),
                (hx + hr * 0.9, hy - hr * 1.2), (hx + hr * 1.3, hy - hr * 0.15), (hx + hr * 0.5, hy - hr * 0.3),
                (hx - hr * 0.6, hy + hr * 0.55)], hm, 0.9, 1.6)
    # arm (near) with hand, swinging
    sx0 = cx + lean + 0.1 * hw
    hand = (cx + arm + lean * 0.5 + 0.03 * Hh, foot_y - 0.47 * Hh + bob)
    if v.get('march'):
        hand = (cx + arm + 0.02 * Hh, foot_y - 0.46 * Hh + bob)
    at = max(0.6, 0.055 * Hh)
    _leg(f, (sx0, sh_y + 0.04 * Hh), ((sx0 + hand[0]) * 0.5, (sh_y + hand[1]) * 0.5 + 0.3), hand, at, coat, 1.2)
    f.ell(hand[0], hand[1] + 0.3, max(0.7, 0.04 * Hh), max(0.7, 0.04 * Hh), 'skin', 0.5, 1.3)
    acc = v.get('acc', '')
    if acc == 'case' and Hh >= 14:
        bw, bh = 0.2 * Hh, 0.13 * Hh
        f.rect(hand[0] - bw * 0.5, hand[1] + 0.6, hand[0] + bw * 0.5, hand[1] + 0.6 + bh, 'leath', 0.4, 1.4)
    elif acc == 'bag' and Hh >= 14:
        bw, bh = 0.13 * Hh, 0.12 * Hh
        f.rect(hand[0] - bw * 0.5, hand[1] + 0.4, hand[0] + bw * 0.5, hand[1] + 0.4 + bh, 'bag', 0.5, 1.4)
    elif acc == 'paper' and Hh >= 20:
        f.rect(hand[0] - 0.5, hand[1] - 0.06 * Hh, hand[0] + 0.12 * Hh, hand[1] + 0.12 * Hh, 'paper', 0.2, 1.5)
    elif acc == 'cane' and Hh >= 14:
        cx2 = hand[0] + 0.03 * Hh
        f.rect(cx2, hand[1], cx2 + max(0.8, 0.025 * Hh), foot_y + 0.5, 'leath', 0.2, 1.5)
    elif acc == 'rifle':
        # slung rifle: barrel above the back shoulder
        rx = cx - hw * 0.7
        f.rect(rx, sh_y - 0.12 * Hh, rx + max(0.8, 0.03 * Hh), sh_y + 0.42 * Hh, 'rifle', 0.3, 1.8)
    origin = (int(round(cx)), int(foot_y))
    return f, origin


def render_fig(f: 'ggh.Fig', small: bool):
    img, nimg = f.render(light=(-0.35, -0.7, 0.62))
    if small:
        # tiny figures: keep the outline only where it touches the background below/behind; flatter shading
        pass
    return img, nimg


def sheet(name: str, Hh: int, variants, frames: int, mode: str, fps: float):
    cells = []
    origin = None
    for vi, v in enumerate(variants):
        row = []
        for fi in range(frames):
            ph = 2 * math.pi * fi / frames
            fg, origin = citizen(Hh, v, ph, mode, fi)
            img, nimg = render_fig(fg, Hh < 20)
            row.append((img, nimg))
        cells.append(row)
    cw = cells[0][0][0].shape[1]
    ch = cells[0][0][0].shape[0]
    big = np.zeros((ch * len(variants), cw * frames, 4), np.uint8)
    bign = np.zeros_like(big)
    for r, row in enumerate(cells):
        for c, (img, nimg) in enumerate(row):
            big[r * ch:(r + 1) * ch, c * cw:(c + 1) * cw] = img
            bign[r * ch:(r + 1) * ch, c * cw:(c + 1) * cw] = nimg
    save_rgba(big, out(name + '.png'))
    save_rgba(bign, out(name + '_n.png'))
    A = 0.19 * Hh if mode == 'walk' and variants and variants[0].get('march') else 0.17 * Hh
    gs = 4.0 * A * fps / frames if mode == 'walk' else 0.0
    return {'file': name + '.png', 'cell': [cw, ch], 'origin': list(origin), 'frames': frames, 'fps': fps,
            'rows': [v['id'] for v in variants], 'ground_speed': round(gs, 2), 'height': Hh}


# ---------------------------------------------------------------------------- tiny figures (hand templates)
# 8 px tall walkers, 4 frames.  'h' head/hat, 'c' coat, 'l' legs, 's' skin.  Columns: 5.
_TINY = [
    ["..h..", ".hs..", ".cc..", ".ccc.", ".cc..", ".cc..", ".l.l.", "l...l"],
    ["..h..", ".hs..", ".cc..", ".ccc.", ".cc..", ".cc..", "..ll.", "..l.l"],
    ["..h..", ".hs..", ".cc..", ".ccc.", ".cc..", ".cc..", "..l..", "..l.."],
    ["..h..", ".hs..", ".cc..", ".ccc.", ".cc..", ".cc..", ".ll..", ".l.l."],
]


def tiny_sheet(name: str, palettes):
    """8 px citizens (d ~ 200-400 m): silhouette + 1 px head + 2-tone coat, 4-frame stride."""
    fr = len(_TINY)
    cw, ch = 5, 8
    img = np.zeros((ch * len(palettes), cw * fr, 4), np.uint8)
    for r, (pid, hc, cc, cc2, lc) in enumerate(palettes):
        for k, rows in enumerate(_TINY):
            for y, row in enumerate(rows):
                for x, chh in enumerate(row):
                    col = {'h': hc, 'c': cc if x < 2 else cc2, 'l': lc, 's': '#7A5E4E'}.get(chh)
                    if col:
                        img[r * ch + y, k * cw + x] = H(col)
    save_rgba(img, out(name + '.png'))
    nimg = np.zeros_like(img)
    nimg[..., 0] = 128
    nimg[..., 1] = 128
    nimg[..., 2] = 255
    nimg[..., 3] = img[..., 3]
    save_rgba(nimg, out(name + '_n.png'))
    return {'file': name + '.png', 'cell': [cw, ch], 'origin': [2, ch - 1], 'frames': fr, 'fps': 6.0,
            'rows': [p[0] for p in palettes], 'ground_speed': 6.0, 'height': 8}


# ============================================================================ sweeper + cart
def sweeper():
    """Street sweeper with a birch broom (46 px class, as the family).  6 frames: the broom swings across the
    ground in front of him, the body twists a little with it."""
    frames = []
    for k in range(6):
        ph = 2 * math.pi * k / 6
        Hh = 45
        Wc, Hc = 40, 48
        f = ggh.Fig(Wc, Hc)
        cx = 16.0
        foot_y = Hc - 1.0
        # legs apart, knees slightly bent
        for (fo, z) in ((-3.0, 0.0), (3.5, 0.3)):
            _leg(f, (cx, foot_y - 21), (cx + fo * 0.6, foot_y - 11), (cx + fo, foot_y), 1.6, 'trou', z)
            f.poly([(cx + fo - 2, foot_y - 1.6), (cx + fo + 3.2, foot_y - 1.4), (cx + fo + 3.4, foot_y + 0.5),
                    (cx + fo - 2, foot_y + 0.5)], 'shoe', 0.4, z + 0.1)
        # broom handle from the hands down to the head near the ground; swing +-
        sw = math.sin(ph)
        hx, hy = cx + 7.0 + sw * 1.2, foot_y - 26
        bx, by = cx + 14.0 + sw * 6.5, foot_y - 1.5
        # back arm on the handle
        _leg(f, (cx - 1.0, foot_y - 35), (cx + 2.0, foot_y - 28), (hx - 2.0, hy + 1.0), 1.2, 'c_patina', 0.9)
        # coat (work coat, apron-like), slight forward lean
        f.poly([(cx - 3.4, foot_y - 37), (cx + 3.4, foot_y - 37.6), (cx + 4.6, foot_y - 28), (cx + 5.2, foot_y - 15),
                (cx - 5.0, foot_y - 15), (cx - 4.6, foot_y - 28)], 'c_patina', 1.6, 0.6)
        f.rect(cx - 4.8, foot_y - 24, cx + 5.0, foot_y - 22.8, 'leath', 0.3, 1.0)
        # handle (wood) and the birch bundle
        L = math.hypot(bx - hx, by - hy)
        nx, ny = -(by - hy) / L * 0.7, (bx - hx) / L * 0.7
        f.poly([(hx + nx, hy + ny), (hx - nx, hy - ny), (bx - nx, by - ny), (bx + nx, by + ny)], 'c_wood', 0.3, 1.5)
        f.poly([(bx - 3.0, by - 3.5), (bx + 3.5, by - 4.0), (bx + 6.5, by + 1.5), (bx - 4.5, by + 1.5)], 'c_birch',
               0.6, 1.4)
        # near arm
        _leg(f, (cx + 2.0, foot_y - 35), (cx + 5.0, foot_y - 29), (hx + 1.5, hy + 4.0), 1.3, 'c_patina', 1.3)
        f.ell(hx + 1.5, hy + 4.4, 1.3, 1.2, 'skin', 0.5, 1.4)
        # head with peaked cap (municipal), bent towards the work
        f.ell(cx + 1.6, foot_y - 40.5, 2.9, 3.1, 'skin', 1.0, 1.2)
        f.px(int(cx + 4.4), int(foot_y - 40.5), '#94735C')
        f.poly([(cx - 1.6, foot_y - 42.2), (cx - 0.8, foot_y - 45.4), (cx + 3.6, foot_y - 45.6), (cx + 4.6, foot_y - 42.6),
                (cx + 6.6, foot_y - 42.0), (cx + 4.4, foot_y - 41.2), (cx - 1.4, foot_y - 41.0)], 'c_night', 0.8, 1.6)
        # snow puffs kicked up by the broom (frames 1,2)
        img, nimg = f.render(light=(-0.35, -0.7, 0.62))
        if k in (1, 2, 4):
            for (dx, dy) in ((5, -2), (7, -3), (8, -1), (6, -5)):
                x, y = int(bx + dx * (1 if k != 4 else -0.6)), int(by + dy)
                if 0 <= x < Wc and 0 <= y < Hc and img[y, x, 3] == 0:
                    img[y, x] = H(SNOW[3] if (x + y) % 2 else SNOW[4])
        frames.append((img, nimg))
    cw, ch = frames[0][0].shape[1], frames[0][0].shape[0]
    big = np.zeros((ch, cw * len(frames), 4), np.uint8)
    bign = np.zeros_like(big)
    for i, (a, b) in enumerate(frames):
        big[:, i * cw:(i + 1) * cw] = a
        bign[:, i * cw:(i + 1) * cw] = b
    save_rgba(big, out('sweeper.png'))
    save_rgba(bign, out('sweeper_n.png'))
    return {'file': 'sweeper.png', 'cell': [cw, ch], 'origin': [16, ch - 1], 'frames': 6, 'fps': 5.0,
            'rows': ['sweep'], 'ground_speed': 0.0, 'height': 45}


def handcart():
    f = ggh.Fig(30, 22)
    # box on two wheels, shafts to the left
    f.poly([(6, 6), (27, 6), (26, 15), (7, 15)], 'c_tin', 1.2)
    f.rect(6, 5, 27, 7, 'c_greyl', 0.4, 0.8)
    f.ell(19, 16.5, 4.6, 4.6, 'c_night', 0.8, 1.2)
    f.ell(19, 16.5, 1.4, 1.4, 'c_tin', 0.3, 1.6)
    f.poly([(0, 11), (8, 10), (8, 11.6), (0, 12.6)], 'c_wood', 0.3, 0.4)
    # snow heaped in the box
    f.poly([(8, 6), (12, 3.5), (18, 2.5), (24, 3.6), (26, 6)], 'c_snow', 0.9, 1.0)
    img, nimg = f.render(light=(-0.35, -0.7, 0.62))
    save_rgba(img, out('handcart.png'))
    save_rgba(nimg, out('handcart_n.png'))
    return {'file': 'handcart.png', 'cell': [30, 22], 'origin': [19, 21], 'frames': 1}


# ============================================================================ birds
def birds():
    """Row 0: ground pigeon 5x4 (stand, peck, stand-look, step).  Row 1: flying bird 7x4 (up, mid, down, mid).
    Row 2: crow on a wire 4x4 (sit, sit-turn, flap, sit).  Cells 7x5, feet/perch on the bottom row."""
    cw, ch = 7, 5
    img = np.zeros((ch * 3, cw * 4, 4), np.uint8)
    D, M, L = H(NIGHT[1]), H(SNOW[0]), H(SNOW[2])
    # ground pigeons: grey-blue body (reads on the trampled slush), light wing bar, dark head and feet
    pig = [
        [".....", "..DD.", ".LMMM", "DMMM.", ".D.D."],
        [".....", ".....", ".LMMM", "DMMMD", ".D.DD"],
        [".....", ".DD..", ".LMMM", "DMMM.", ".D.D."],
        [".....", "..DD.", ".LMMM", "DMMM.", "..DD."],
    ]
    fly = [
        ["D.....D", ".D...D.", "..DMD..", "...D...", "......."],
        [".......", "DD...DD", "..DMD..", "...D...", "......."],
        [".......", ".......", "DDDMDDD", ".D.D.D.", "......."],
        [".......", "DD...DD", "..DMD..", "...D...", "......."],
    ]
    crow = [
        [".....", "..DD.", ".DDD.", "DDDD.", "..D.."],
        [".....", ".DD..", ".DDD.", "DDDD.", "..D.."],
        ["D...D", ".DDD.", ".DDD.", ".DDD.", "..D.."],
        [".....", "..DD.", ".DDD.", "DDDD.", "..D.."],
    ]
    cmap = {'D': D, 'M': M, 'L': L}
    for r, frames in enumerate((pig, fly, crow)):
        for k, rows in enumerate(frames):
            for y, row in enumerate(rows):
                for x, chh in enumerate(row):
                    if chh in cmap:
                        img[r * ch + y, k * cw + x] = cmap[chh]
    save_rgba(img, out('birds.png'))
    return {'file': 'birds.png', 'cell': [cw, ch], 'origin': [3, ch - 1], 'frames': 4,
            'rows': ['pigeon', 'fly', 'crow']}


# ============================================================================ smoke & steam loops
def plume(name, w, h, frames, cols, n_puffs, r0, r1, drift, rise_curve, seed, dens0=0.95, dens1=0.15,
          base_w=2.0):
    """Looping plume: puffs are born at the bottom centre, rise, grow, drift sideways and thin out (ordered
    dither).  Seamless: every puff's age wraps after one loop."""
    rng = np.random.default_rng(seed)
    offs = (np.arange(n_puffs) + rng.uniform(0.0, 0.35, n_puffs)) / n_puffs
    jit = rng.uniform(-1.0, 1.0, n_puffs)
    img = np.zeros((h, w * frames, 4), np.uint8)
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    thr = pg.bayer(w, h)
    carr = np.stack([H(c) for c in cols])
    for k in range(frames):
        dens = np.zeros((h, w), np.float32)
        tone = np.zeros((h, w), np.float32)
        for i in range(n_puffs):
            age = (k / frames + offs[i]) % 1.0
            y = (h - 2) - rise_curve(age) * (h - 4)
            x = w * 0.28 + drift * age * age * w + jit[i] * base_w * (0.4 + age)
            r = r0 + (r1 - r0) * age
            d = np.sqrt((xx - x) ** 2 + ((yy - y) * 1.15) ** 2) / max(r, 0.5)
            e = np.clip((d - 0.62) / 0.38, 0, 1)
            fade = 1.0 if age < 0.55 else 1.0 - (age - 0.55) / 0.45
            a = (1.0 - e * e * (3 - 2 * e)) * (dens1 + (dens0 - dens1) * fade)
            dens = np.maximum(dens, a)
            # lit from the upper left: tone higher on the upper-left side of each puff
            lt = np.clip(0.5 - ((xx - x) + (yy - y)) / max(r, 0.5) * 0.35, 0, 1)
            tone = np.where(a >= dens - 1e-6, lt * (1.0 - 0.5 * age) + 0.25 * (1 - age), tone)
        on = dens > thr
        idx = np.clip((tone * (len(cols) - 0.01)).astype(int), 0, len(cols) - 1)
        sub = img[:, k * w:(k + 1) * w]
        sub[on] = carr[idx[on]]
    # clean single orphan pixels (keeps the dither edges crisp)
    a = img[..., 3] > 0
    p = np.pad(a, 1).astype(int)
    nb = (p[:-2, 1:-1] + p[2:, 1:-1] + p[1:-1, :-2] + p[1:-1, 2:] + p[:-2, :-2] + p[:-2, 2:] + p[2:, :-2] +
          p[2:, 2:])
    img[a & (nb == 0)] = 0
    save_rgba(img, out(name + '.png'))
    return {'file': name + '.png', 'cell': [w, h], 'origin': [int(w * 0.28), h - 2], 'frames': frames,
            'fps': 7.0}


# ============================================================================ windows, kiosk, stop sign
def window_people():
    """Silhouettes behind lit curtains (dark shapes, a few px of rim from the room light), 14x24 cells:
    0 head and shoulders, 1 standing figure in profile, 2 woman with a bun holding the curtain, 3 two heads."""
    cw, ch = 14, 24
    img = np.zeros((ch, cw * 4, 4), np.uint8)
    D, E = H(NIGHT[2]), H(OCHRE[1])
    L = pg.Layer(cw * 4, ch)
    # 0: head + shoulders from below the sill
    L.ellipse(7, 12, 2.6, 3.0, D)
    L.poly([(1, 24), (2, 18), (5, 15.5), (9, 15.5), (12, 18), (13, 24)], D)
    # 1: standing profile
    o = cw
    L.ellipse(o + 7, 5, 2.2, 2.6, D)
    L.poly([(o + 4, 24), (o + 4.5, 10), (o + 6, 8), (o + 9, 8.5), (o + 10, 12), (o + 9.5, 24)], D)
    L.px(o + 9, 5, D)
    # 2: woman with hair bun, arm raised to the curtain
    o = 2 * cw
    L.ellipse(o + 6, 7, 2.3, 2.7, D)
    L.ellipse(o + 4, 5, 1.3, 1.3, D)
    L.poly([(o + 2, 24), (o + 3, 12), (o + 5, 10.5), (o + 8, 10.5), (o + 10, 13), (o + 10.5, 24)], D)
    L.poly([(o + 9, 12), (o + 12.5, 4), (o + 13.5, 4.5), (o + 10.2, 13.5)], D)
    # 3: two heads at a table
    o = 3 * cw
    L.ellipse(o + 4, 13, 2.2, 2.5, D)
    L.ellipse(o + 10, 14, 2.0, 2.3, D)
    L.poly([(o + 0, 24), (o + 1, 18), (o + 7, 17), (o + 13, 18.5), (o + 14, 24)], D)
    img = L.c.copy()
    # warm rim on the side facing the lamp (left)
    a = img[..., 3] > 0
    p = np.pad(a, 1)
    rim = a & ~p[1:-1, :-2]
    img[rim] = E
    save_rgba(img, out('window_people.png'))
    return {'file': 'window_people.png', 'cell': [cw, ch], 'frames': 4}


def kiosk():
    """Front display of a newspaper kiosk (40x18) and its sign board (40x6), unreadable mastheads only."""
    w, h = 40, 18
    L = pg.Layer(w, h)
    L.rect(0, 0, w, h, H(NIGHT[2]))
    rng = np.random.default_rng(seed_of('kiosk'))
    cols = [SNOW[3], SNOW[4], SNOW[2], OCHRE[3], STONE[4], STEEL[3]]
    x = 1
    while x < w - 4:
        pw = int(rng.integers(4, 7))
        for row in range(2):
            y0 = 1 + row * 8
            c = cols[int(rng.integers(0, len(cols)))]
            L.rect(x, y0, pw, 7, H(c))
            L.hline(x, y0 + 1, pw, H(NIGHT[1]))           # masthead line
            for yy in range(y0 + 3, y0 + 7, 2):
                L.hline(x + 1, yy, pw - 2, H(SNOW[0]))
        x += pw + 1
    save_rgba(L.c, out('kiosk_front.png'))
    S = pg.Layer(40, 6)
    S.rect(0, 0, 40, 6, H(NIGHT[1]))
    for i, xx in enumerate(range(3, 37, 4)):
        S.rect(xx, 2, 2 + (i % 2), 2, H(GLOW[3]))
    save_rgba(S.c, out('kiosk_sign.png'))


def tram_stop():
    """Round stop sign 9x9: green disc, yellow H (Berlin style, original drawing)."""
    L = pg.Layer(9, 9)
    L.ellipse(4.5, 4.5, 4.5, 4.5, H(PATINA[2]))
    L.ellipse(4.5, 4.5, 3.5, 3.5, H(PATINA[3]))
    for y in range(2, 7):
        L.px(3, y, H(GLOW[2]))
        L.px(5, y, H(GLOW[2]))
    L.px(4, 4, H(GLOW[2]))
    save_rgba(L.c, out('tram_stop.png'))


# ============================================================================ the family's belongings
def belongings():
    """Household things carried out of the sealed flat (d ~ 33 m, 1 texel = 1 px): a bentwood chair with a
    coat over its back, a crate with pots, a bedding roll tied with a strap, a birdcage with a canary."""
    meta = {}
    # chair (side view, back to the left), coat over the back
    f = ggh.Fig(16, 25)
    f.rect(2, 0.5, 4.2, 24, 'c_wood', 0.4)                 # back post + rear leg
    f.poly([(3.2, 13), (13.5, 12.6), (13.5, 14.4), (3.2, 14.8)], 'c_wood', 0.6, 0.3)   # seat
    f.rect(12.0, 14, 13.6, 24, 'c_wood', 0.4, 0.2)          # front leg
    f.poly([(5.0, 15), (6.4, 15), (10.0, 24), (8.6, 24)], 'c_wood', 0.3, 0.1)          # stretcher hint
    f.poly([(0.8, 1.6), (5.2, 1.0), (6.6, 9.0), (6.2, 17.4), (1.0, 18.0)], 'c_grey', 1.3, 0.8)  # coat
    f.rect(1.2, 3.2, 5.6, 4.2, 'c_night', 0.3, 1.2)          # coat collar shadow
    img, nimg = f.render(light=(-0.35, -0.7, 0.62))
    ggh.save_rgba(img, out('belong_chair.png'))
    ggh.save_rgba(nimg, out('belong_chair_n.png'))
    meta['chair'] = {'file': 'belong_chair.png', 'cell': [16, 25], 'origin': [8, 24], 'frames': 1}
    # crate with pots (front view), handles sticking out
    f = ggh.Fig(17, 14)
    f.rect(1, 4, 16, 14, 'c_wood', 1.0)
    f.rect(1, 8.4, 16, 9.4, 'c_night', 0.2, 0.6)
    f.ell(5.5, 4.2, 3.2, 2.4, 'c_tin', 1.0, 0.8)            # pot
    f.ell(11.5, 3.8, 2.6, 2.6, 'c_grey', 0.9, 0.7)          # second pot / kettle
    f.rect(14.0, 2.4, 16.8, 3.2, 'c_tin', 0.2, 1.0)         # handle
    img, nimg = f.render(light=(-0.35, -0.7, 0.62))
    ggh.save_rgba(img, out('belong_crate.png'))
    ggh.save_rgba(nimg, out('belong_crate_n.png'))
    meta['crate'] = {'file': 'belong_crate.png', 'cell': [17, 14], 'origin': [8, 13], 'frames': 1}
    # bedding roll with a strap
    f = ggh.Fig(22, 11)
    f.poly([(1.5, 2.5), (20.0, 2.0), (21.2, 5.5), (20.0, 10.5), (1.5, 10.5), (0.6, 6.5)], 'c_snow', 1.4)
    f.ell(1.8, 6.5, 1.5, 3.8, 'c_brown', 0.6, 0.6)           # rolled end
    f.rect(8.0, 1.6, 9.4, 10.8, 'leath', 0.3, 1.4)
    f.rect(14.6, 1.6, 16.0, 10.8, 'leath', 0.3, 1.4)
    img, nimg = f.render(light=(-0.35, -0.7, 0.62))
    ggh.save_rgba(img, out('belong_bedding.png'))
    ggh.save_rgba(nimg, out('belong_bedding_n.png'))
    meta['bedding'] = {'file': 'belong_bedding.png', 'cell': [22, 11], 'origin': [11, 10], 'frames': 1}
    # birdcage with a canary (2 frames: the bird hops)
    cw, ch = 11, 14
    img = np.zeros((ch, cw * 2, 4), np.uint8)
    for k in range(2):
        L = pg.Layer(cw, ch)
        wire = H(STEEL[3])
        L.px(5, 0, H(STEEL[2]))
        L.ellipse(5.0, 4.5, 4.5, 3.6, wire)
        L.ellipse(5.0, 4.8, 3.6, 2.7, (0, 0, 0, 0))
        L.c[3:12][L.c[3:12, :, 3] == 0] = 0
        for x in (1, 3, 5, 7, 9):
            L.vline(x, 4, 8, wire)
        L.hline(0, 12, 11, H(NIGHT[2]))
        L.hline(1, 13, 9, H(NIGHT[1]))
        by = 8 if k == 0 else 7
        L.px(4, by, H(GLOW[2]))                              # the canary
        L.px(5, by, H(GLOW[1]))
        L.px(4, by - 1, H(GLOW[3]))
        L.px(3, by - 1, H(OCHRE[3]))
        img[:, k * cw:(k + 1) * cw] = L.c
    ggh.save_rgba(img, out('belong_cage.png'))
    meta['cage'] = {'file': 'belong_cage.png', 'cell': [cw, ch], 'origin': [5, ch - 1], 'frames': 2, 'fps': 0.7}
    return meta


def paper_sheet():
    """A newspaper page tumbling over the snow in the wind: 4 frames, 9x7."""
    cw, ch = 9, 7
    frames = [
        [".........", ".........", ".........", "..LLLLL..", ".LMMMMML.", ".........", "........."],
        [".........", "....LL...", "...LMML..", "..LMMML..", "..LMML...", "...LL....", "........."],
        [".........", ".L.......", ".LMLL....", "..LMMLL..", "....LMML.", "......L..", "........."],
        [".........", ".........", "...LLLL..", "..LMMMML.", ".LMMMML..", ".........", "........."],
    ]
    img = np.zeros((ch, cw * 4, 4), np.uint8)
    cmap = {'L': H(SNOW[4]), 'M': H(SNOW[2])}
    for k, rows in enumerate(frames):
        for y, r in enumerate(rows):
            for x, chh in enumerate(r):
                if chh in cmap:
                    img[y, k * cw + x] = cmap[chh]
        # a couple of printed lines on the page
        img[4, k * cw + 3] = H(SNOW[0]) if img[4, k * cw + 3, 3] else img[4, k * cw + 3]
    ggh.save_rgba(img, out('paper.png'))
    return {'file': 'paper.png', 'cell': [cw, ch], 'origin': [4, ch - 1], 'frames': 4, 'fps': 9.0}


# ============================================================================ preview
def preview(names, scale=4):
    ims = [Image.open(out(n)).convert('RGBA') for n in names]
    pad = 4
    W = max(i.width for i in ims) + 2 * pad
    Hh = sum(i.height + pad for i in ims) + pad
    sheet_img = Image.new('RGBA', (W, Hh), (110, 106, 115, 255))
    y = pad
    for im in ims:
        sheet_img.paste(im, (pad, y), im)
        y += im.height + pad
    os.makedirs(PREV, exist_ok=True)
    open(os.path.join(PREV, '.gdignore'), 'a').close()
    pg.upscale(sheet_img, scale).save(os.path.join(PREV, 'life_x%d.png' % scale))


def main():
    os.makedirs(ROOT, exist_ok=True)
    meta = {}
    meta['walk_36'] = sheet('walk_36', 36, VARIANTS, 8, 'walk', 10.0)
    meta['walk_24'] = sheet('walk_24', 24, VARIANTS, 8, 'walk', 10.0)
    meta['walk_14'] = sheet('walk_14', 14, VARIANTS[:4], 4, 'walk', 6.0)
    meta['stand_36'] = sheet('stand_36', 36, VARIANTS, 4, 'stand', 2.0)
    meta['stand_24'] = sheet('stand_24', 24, VARIANTS, 4, 'stand', 2.0)
    soldier = [{'id': 'soldier', 'coat': 'c_field', 'hat': 'helmet', 'hatm': 'c_grey', 'legs': 'leath',
                'acc': 'rifle', 'hem': 0.82, 'width': 1.05, 'march': True}]
    meta['march_14'] = sheet('march_14', 14, soldier, 4, 'walk', 6.0)
    meta['march_24'] = sheet('march_24', 24, soldier, 8, 'walk', 10.0)
    meta['walk_8'] = tiny_sheet('walk_8', [
        ('dark', NIGHT[1], NIGHT[2], VIOLET[1], NIGHT[1]),
        ('grey', NIGHT[1], STEEL[1], STEEL[2], NIGHT[1]),
        ('brown', NIGHT[2], STONE[0], STONE[1], NIGHT[1]),
        ('violet', PATINA[1], VIOLET[1], VIOLET[2], NIGHT[1]),
    ])
    meta['sweeper'] = sweeper()
    meta['handcart'] = handcart()
    meta['birds'] = birds()
    meta['smoke'] = plume('smoke', 24, 56, 8, [NIGHT[2], VIOLET[0], VIOLET[1], VIOLET[2]], 13, 2.0, 7.5, 0.5,
                          lambda a: a ** 0.85, seed_of('smoke'), dens0=1.0, dens1=0.25, base_w=1.0)
    meta['steam'] = plume('steam', 30, 32, 8, [SNOW[0], SNOW[1], SNOW[2], SNOW[3]], 12, 2.6, 7.0, 0.32,
                          lambda a: a ** 0.9, seed_of('steam'), dens0=0.9, dens1=0.0, base_w=1.6)
    meta['window_people'] = window_people()
    for k, v in belongings().items():
        meta['belong_' + k] = v
    meta['paper'] = paper_sheet()
    kiosk()
    tram_stop()
    with open(out('life.json'), 'w', encoding='utf-8') as fh:
        json.dump(meta, fh, indent=1)
    preview(['walk_36.png', 'walk_24.png', 'walk_14.png', 'stand_36.png', 'march_24.png', 'march_14.png',
             'walk_8.png', 'sweeper.png', 'handcart.png', 'birds.png', 'smoke.png', 'steam.png',
             'window_people.png', 'kiosk_front.png', 'tram_stop.png', 'belong_chair.png', 'belong_crate.png',
             'belong_bedding.png', 'belong_cage.png', 'paper.png'])
    print('life sprites written to', ROOT)


if __name__ == '__main__':
    main()
