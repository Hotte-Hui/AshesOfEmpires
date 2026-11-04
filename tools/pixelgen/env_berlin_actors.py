"""env_berlin_actors -- sprite sheets + scene.json 'actors' entries for the living details of M1 (round 2).

Actors are self-contained scenes in scenes/levels/berlin/ (scripts in scripts/levels/berlin/), instanced by
Level._spawn_actors() into the y-sorted Playfield.  This module draws their sprite sheets (deterministic,
palette-pure) into assets/environments/berlin_archive/actors/ and returns the manifest entries.

  tram.png          motor car + trailer, side view (parallax 0.20, behind the glass); spark.png
  pigeons.png       12 x 10 cells: idle a/b, peck a/b, ruffle, turn, fly 1-4 (outside sill, behind the glass)
  mouse.png         12 x 8 cells: hidden, nose, head, sniff, half out, out, run a/b
  pendulum.png      regulator pendulum, 12 swing frames
  steam.png         radiator valve steam puff, 12 frames
  papers.png        loose sheets lifting in the draught, 8 frames
  tube.png          pneumatic tube station flap + capsule, 6 frames
  radio_glow.png    dial + magic-eye overlay, 3 frames (eye opening)
  smoke_curl.png    cigarette smoke (16 frames, env_berlin_fx)
  win_outer.png     outer stone sills with snow behind every window (a layer, not an actor)
(The insignia overlays decals/decal_*.png are scene.json "decals" built by env_berlin.build_decals.)
"""
from __future__ import annotations

import math
import os

import numpy as np

import env_berlin_kit as kit
import env_berlin_layout as L
import pg

R = kit.archive_ramps()
Bp = kit.B
RB = kit.Ramps({
    'CRM': [Bp['stone'][1], Bp['stone'][2], Bp['stone'][3], Bp['stone'][4], Bp['stone'][5]],
    'OCH': [Bp['night'][2], Bp['ochre'][0], Bp['ochre'][1], Bp['ochre'][2], Bp['ochre'][3]],
    'ROF': [Bp['night'][0], Bp['night'][2], Bp['steel'][0], Bp['steel'][1], Bp['steel'][2], Bp['steel'][3]],
    'GLW': [Bp['ochre'][3], Bp['ochre'][4], Bp['glow'][0], Bp['glow'][1], Bp['glow'][2], Bp['glow'][3],
            Bp['glow'][4]],
    'NGT': [Bp['night'][0], Bp['night'][1], Bp['night'][2], Bp['night'][3]],
    'SNW': [Bp['violet'][2], Bp['snow'][0], Bp['snow'][1], Bp['snow'][2], Bp['snow'][3], Bp['snow'][4]],
    'STN': [Bp['night'][2], Bp['violet'][0], Bp['violet'][1], Bp['violet'][2], Bp['violet'][3], Bp['stone'][1],
            Bp['stone'][2]],
    'PIG': [Bp['night'][2], Bp['violet'][2], Bp['steel'][2], Bp['steel'][3], Bp['steel'][4], Bp['steel'][5],
            Bp['snow'][3]],
    'IRI': [Bp['patina'][1], Bp['patina'][2], Bp['patina'][3], Bp['violet'][3]],
    'BLU': ['#A7BCCB', '#DEE5DC', '#ECE6E0'],
})

ACT_DIR_REL = 'actors'
SCN = 'res://scenes/levels/berlin/'
RES_ENV = 'res://assets/environments/berlin_archive/'


def _lay(w, h, ramps=RB):
    return kit.MLayer(w, h, ramps, 'actor')


def _save(lay, path, normal=False):
    lay.resolve()
    kit.save_rgba(lay.c, path)
    if normal:
        from PIL import Image
        Image.fromarray(lay.normal_map(3.0), 'RGBA').save(path[:-4] + '_n.png')
    return path


# =========================================================================== tram
TRAM_ROOF_Y = L.TRAM_ROOF_Y  # world y of the roof line (the pantograph touches the wire at TRAM_WIRE_Y)
TRAM_TOP = L.TRAM_WIRE_Y - 3 # world y of the sprite's top row


def tram_sheet():
    """Motor car (front = right, with pantograph) + trailer.  Muted cream/ochre BVG livery at dusk, warm lit
    windows with passengers.  Only the upper part is ever seen through the windows."""
    car_w, gap, trl_w = 150, 5, 118
    W = trl_w + gap + car_w
    H = 56
    lay = _lay(W, H)
    roof = TRAM_ROOF_Y - TRAM_TOP

    def car(x0, w, motor, seed):
        rng = np.random.default_rng(seed)
        # body
        lay.rect(x0 + 2, roof + 3, w - 4, H - roof - 3, 'CRM', 2.8, flat=True)
        lay.rect(x0 + 2, roof + 18, w - 4, H - roof - 18, 'OCH', 2.4, flat=True)     # darker lower livery
        lay.rect(x0 + 2, roof + 18, w - 4, 1, 'OCH', 3.6, flat=True)
        # rounded ends
        for (ex, sg) in ((x0 + 2, -1), (x0 + w - 3, 1)):
            for k in range(3):
                lay.rect(ex + sg * k, roof + 4 + k * 2, 1, H - roof - 4 - k * 2, 'CRM', 2.0 - 0.3 * k, flat=True)
        # roof: curved dark top with a lit edge
        lay.rect(x0 + 3, roof, w - 6, 3, 'ROF', 2.6, flat=True)
        lay.rect(x0 + 5, roof - 1, w - 10, 1, 'ROF', 3.6, flat=True)
        lay.rect(x0 + 3, roof + 2, w - 6, 1, 'ROF', 1.4, flat=True)
        lay.rect(x0 + 3, roof + 3, w - 6, 1, 'CRM', 4.0, flat=True)                  # rain strip catching light
        for k in range(x0 + 14, x0 + w - 14, 22):                                    # roof boxes / vents
            lay.rect(k, roof - 2, 8, 2, 'ROF', 2.0, flat=True)
            lay.px(k, roof - 2, 'ROF', 3.6)
        # snow lying on the roof (patches)
        for k in range(x0 + 6, x0 + w - 6):
            if rng.random() < 0.55:
                lay.px(k, roof - 1, 'SNW', 3.0 + rng.random() * 1.5)
        # upper ventilator band + main windows (lit, with passengers)
        lay.rect(x0 + 4, roof + 4, w - 8, 3, 'CRM', 3.4, flat=True)
        for k in range(x0 + 8, x0 + w - 10, 7):
            lay.rect(k, roof + 5, 4, 1, 'GLW', 2.0, flat=True)
        wy0, wy1 = roof + 8, roof + 17
        n = (w - 16) // 13
        ox = x0 + (w - n * 13) // 2 + 1
        for i in range(n):
            wx = ox + i * 13
            lay.rect(wx, wy0, 10, wy1 - wy0, 'GLW', 3.4, flat=True)
            lay.rect(wx, wy0, 10, 2, 'GLW', 2.4, flat=True)                         # lamp glow under the roof
            # passengers: heads + shoulders, a hat, someone standing at the strap
            for j in range(int(rng.integers(0, 3))):
                hx = wx + 1 + int(rng.integers(0, 7))
                tall = rng.random() < 0.4
                hy = wy0 + (2 if tall else 4)
                lay.rect(hx, hy, 2, 2, 'NGT', 1.0, flat=True)
                lay.rect(hx - 1, hy + 2, 4, wy1 - hy - 2, 'NGT', 1.0 + (j % 2) * 0.6, flat=True)
                if rng.random() < 0.35:
                    lay.rect(hx - 1, hy - 1, 4, 1, 'NGT', 0.0, flat=True)            # hat brim
            lay.px(wx + 8, wy0 + 1, 'GLW', 6.0)                                      # reflection glint
        # window pillars (body colour)
        # door (motor car: front third; trailer: middle) -- dark glazed doors
        dx = x0 + (w - 28 if motor else w // 2 - 5)
        lay.rect(dx, wy0 - 1, 10, H - wy0 + 1, 'OCH', 1.6, flat=True)
        lay.rect(dx + 1, wy0, 8, 9, 'GLW', 2.0, flat=True)
        lay.rect(dx + 4, wy0, 1, H - wy0, 'OCH', 0.8, flat=True)
        if motor:
            # destination box above the windscreen (lit) with the route number
            bx = x0 + w - 22
            lay.rect(bx, roof + 4, 16, 4, 'NGT', 1.0, flat=True)
            lay.rect(bx + 1, roof + 5, 14, 2, 'GLW', 4.0, flat=True)
            m = np.array([[c == '#' for c in row] for row in ['.#.', '##.', '.#.']], bool)   # '1'
            lay.put(m, bx + 9, roof + 5, 'NGT', 0.0, flat=True)
            lay.rect(bx + 2, roof + 6, 5, 1, 'NGT', 1.0, flat=True)                  # destination text
            # windscreen
            lay.rect(x0 + w - 8, wy0, 4, 9, 'GLW', 2.6, flat=True)
            # pantograph (scissor) -- top collector bar at world y 216
            px_ = x0 + w // 2
            top = L.TRAM_WIRE_Y - TRAM_TOP
            lay.rect(px_ - 9, top, 19, 1, 'ROF', 3.0, flat=True)
            lay.px(px_ - 10, top + 1, 'ROF', 2.6); lay.px(px_ + 10, top + 1, 'ROF', 2.6)
            for (a, b) in (((px_ - 5, top + 1), (px_ - 1, top + 6)), ((px_ + 5, top + 1), (px_ + 1, top + 6)),
                           ((px_ - 1, top + 6), (px_ - 5, roof - 2)), ((px_ + 1, top + 6), (px_ + 5, roof - 2))):
                lay.line(a[0], a[1], b[0], b[1], 'ROF', 2.2)
            lay.rect(px_ - 7, roof - 2, 15, 2, 'ROF', 1.6, flat=True)                # base frame
            lay.px(px_ - 6, roof - 3, 'SNW', 2.0); lay.px(px_ + 6, roof - 3, 'SNW', 2.0)  # insulators
        lay.rect(x0 + 2, H - 2, w - 4, 2, 'OCH', 1.0, flat=True)
    car(0, trl_w, False, 801)
    car(trl_w + gap, car_w, True, 802)
    lay.rect(trl_w - 1, 46, gap + 2, 2, 'ROF', 1.0, flat=True)                     # coupling
    lay.unlit[:] = True
    return lay, {'w': W, 'h': H, 'pantograph_x': trl_w + gap + car_w // 2, 'top': TRAM_TOP}


def spark_sheet():
    """pantograph spark: 4 frames 9 x 7 (blue-white crackle at the contact point, centre (4, 3))"""
    frames = 4
    lay = _lay(9 * frames, 7)
    pts = [[(4, 3), (3, 2), (5, 4), (2, 3)], [(4, 3), (5, 2), (6, 1), (3, 4), (4, 2)],
           [(4, 3), (2, 4), (1, 5), (5, 3), (6, 4)], [(4, 3), (4, 2)]]
    for f, pp in enumerate(pts):
        for k, (x, y) in enumerate(pp):
            lay.px(f * 9 + x, y, 'BLU', 2.0 if k == 0 else (1.0 if k < 3 else 0.0), flat=True)
    lay.unlit[:] = True
    return lay


# =========================================================================== pigeons
PIG_W, PIG_H = 12, 10


def pigeon_frame(lay, ox, kind):
    """Feral pigeon, side view facing right: grey body, darker wing bars, iridescent neck, pale eye, pink feet.
    Light from the left (the street lamp side) -> a lighter left rim."""
    def P(x, y, ramp, t):
        lay.px(ox + x, y, ramp, t)
    if kind.startswith('fly'):
        ph = int(kind[-1])
        T = {
            1: ['....ww......', '...www......', '..wwww......', '.wwwwbbb.nh.', 'ttbbbbbbbnhk', '..bbbbbb....',
                '............', '............', '............', '............'],
            2: ['............', '............', '............', '.....bbb.nh.', 'ttwwwwwwwnhk', '..dbbbbb....',
                '............', '............', '............', '............'],
            3: ['............', '............', '............', '.....bbb.nh.', 'ttbbbbbbbnhk', '..bbwwww....',
                '...wwww.....', '....ww......', '............', '............'],
        }[1 if ph == 1 else (3 if ph == 3 else 2)]
        tone = {'w': ('PIG', 4.4), 'b': ('PIG', 3.4), 'd': ('PIG', 2.2), 'n': ('IRI', 2.0), 'h': ('PIG', 3.8),
                'k': ('OCH', 2.0), 't': ('PIG', 2.6)}
        for yy, row in enumerate(T):
            for xx, ch in enumerate(row):
                if ch in tone:
                    rm, tt = tone[ch]
                    P(xx, yy, rm, tt)
        return
    body_y = 4
    peck = kind.startswith('peck')
    # tail + body
    for x in range(1, 4):
        P(x, body_y + 2 + (1 if x == 1 else 0), 'PIG', 2.4)
    for y in range(body_y, body_y + 4):
        for x in range(3, 9):
            if (y == body_y and x in (3, 8)) or (y == body_y + 3 and x in (3, 4)):
                continue
            P(x, y, 'PIG', 3.4 if y < body_y + 2 else 3.0)
    for x in range(4, 8):
        P(x, body_y + 1, 'PIG', 2.4 if x in (5, 7) else 3.8)                       # wing bars
    P(3, body_y + 1, 'PIG', 4.6)                                                    # rim light (left)
    if kind == 'ruffle':
        for x in range(3, 9):
            P(x, body_y - 1, 'PIG', 3.6)
        P(2, body_y + 1, 'PIG', 3.2)
    # neck + head
    if peck:
        hx, hy = (9, body_y + 3) if kind == 'peck_b' else (9, body_y + 2)
        P(8, body_y, 'IRI', 2.0); P(9, body_y + 1, 'IRI', 1.0)
        P(hx, hy, 'PIG', 3.6); P(hx + 1, hy, 'PIG', 3.2); P(hx + 1, hy + 1, 'OCH', 2.0)
    else:
        facing_back = kind == 'turn'
        P(8, body_y - 1, 'IRI', 2.0); P(9, body_y, 'IRI', 1.0)
        P(8, body_y - 2, 'PIG', 3.6); P(9, body_y - 2, 'PIG', 3.4); P(9, body_y - 3, 'PIG', 3.6)
        P(8, body_y - 3, 'PIG', 3.8)
        if facing_back:
            P(7, body_y - 2, 'OCH', 2.0)
        else:
            P(10, body_y - 2, 'OCH', 2.0)                                          # beak
            P(9, body_y - 3, 'SNW', 4.0)                                            # pale eye
        if kind == 'idle_b':
            P(10, body_y - 3, 'PIG', 3.4)
    # feet
    P(5, body_y + 4, 'OCH', 3.0); P(7, body_y + 4, 'OCH', 3.0)


def pigeons_sheet():
    kinds = ['idle_a', 'idle_b', 'peck_a', 'peck_b', 'ruffle', 'turn', 'fly1', 'fly2', 'fly3', 'fly4']
    lay = _lay(PIG_W * len(kinds), PIG_H)
    for i, k in enumerate(kinds):
        pigeon_frame(lay, i * PIG_W, k)
    # selective dark outline below and behind (the side away from the street lamp) for separation
    body = lay.rid >= 0
    below = np.zeros_like(body)
    below[1:, :] = body[:-1, :] & ~body[1:, :]
    right = np.zeros_like(body)
    right[:, :-1] = body[:, 1:] & ~body[:, :-1]
    for i in range(len(kinds)):
        below[:, i * PIG_W] = False
    lay.put(below | right, 0, 0, 'PIG', 0.0, flat=True)
    lay.unlit[:] = True
    return lay, kinds


# =========================================================================== mouse
MOUSE_W, MOUSE_H = 12, 8


def mouse_sheet():
    kinds = ['hidden', 'nose', 'head', 'sniff', 'half', 'out', 'run_a', 'run_b']
    lay = _lay(MOUSE_W * len(kinds), MOUSE_H, R)
    base = MOUSE_H - 1                         # floor row (the hole's sill)
    for i, k in enumerate(kinds):
        ox = i * MOUSE_W

        def P(x, y, ramp, t):
            lay.px(ox + x, y, ramp, t, flat=True)
        if k == 'hidden':
            continue
        # the hole is at local x 0..4; the mouse comes out to the right
        if k in ('nose', 'head', 'sniff'):
            ext = {'nose': 1, 'head': 3, 'sniff': 3}[k]
            for x in range(ext):
                P(3 + x, base - 1, 'W', 4.0 if x < ext - 1 else 4.6)
                if x >= 1:
                    P(3 + x, base - 2, 'W', 3.6)
            P(3 + ext, base - 1, 'R', 3.0)                                          # pink nose tip
            if ext >= 3:
                P(4, base - 3, 'W', 4.6)                                            # ear
                P(5, base - 2, 'I', 0.0)                                            # eye
            if k == 'sniff':
                P(6 + 1, base - 2, 'P', 3.0); P(6 + 1, base, 'P', 3.0)              # whiskers
        else:
            off = {'half': 2, 'out': 5, 'run_a': 6, 'run_b': 7}[k]
            for x in range(5):
                P(off + x, base - 1, 'W', 3.6)
                if 0 < x < 4:
                    P(off + x, base - 2, 'W', 4.0)
            P(off + 1, base - 3, 'W', 4.4) if k != 'half' else None
            P(off + 5, base - 1, 'W', 4.0); P(off + 6, base - 1, 'R', 3.0)
            P(off + 4, base - 3, 'W', 4.6); P(off + 5, base - 2, 'I', 0.0)
            # tail curling back into / along the floor
            for x in range(1, off + 1):
                P(off - x, base - (1 if x < 2 else 0), 'W', 2.6)
            if k.startswith('run'):
                P(off + 1, base, 'W', 2.0 if k == 'run_a' else 3.0); P(off + 3, base, 'W', 3.0 if k == 'run_a' else 2.0)
    return lay, kinds


# =========================================================================== regulator pendulum
def pendulum_sheet(length, frames=12, amp_deg=5.5):
    w = int(2 * math.ceil(length * math.sin(math.radians(amp_deg))) + 9)
    h = length + 5
    lay = _lay(w * frames, h, R)
    cx = w // 2
    for f in range(frames):
        ang = math.radians(amp_deg) * math.sin(2 * math.pi * f / frames)
        ox = f * w
        bx = cx + length * math.sin(ang)
        by = 1 + length * math.cos(ang)
        lay.line(ox + cx, 0, ox + bx, by - 3, 'A', 2.6)
        lay.line(ox + cx + 1, 0, ox + bx + 1, by - 3, 'A', 1.6)
        m, mx, my = lay.ellipse_mask(ox + bx + 0.5, by, 2.6, 2.6)
        lay.put(m, mx, my, 'A', 3.4, flat=True)
        lay.px(int(ox + bx - 0.5), int(by - 1), 'A', 5.6)
        lay.px(int(ox + bx + 1.5), int(by + 1), 'A', 2.0)
    return lay, (w, h)


# =========================================================================== steam
def steam_sheet(frames=12, w=12, h=20):
    lay = _lay(w * frames, h, R)
    rng = np.random.default_rng(91)
    puffs = [(rng.uniform(-1, 1), rng.uniform(0, 0.4), rng.uniform(1.2, 2.2)) for _ in range(9)]
    for f in range(frames):
        u = f / (frames - 1)
        for (dx, d0, r0) in puffs:
            t = u - d0
            if t <= 0 or t > 0.7:
                continue
            t2 = t / 0.7
            x = w / 2 + dx * 2 + math.sin(t2 * 5 + dx * 3) * 1.4 * t2
            y = h - 2 - t2 * (h - 4)
            r = r0 + t2 * 1.8
            m, mx, my = lay.ellipse_mask(f * w + x, y, r, r * 0.8)
            tone = 9.0 - t2 * 2.8
            ok = m & (pg.bayer(m.shape[1], m.shape[0], mx, my) < (1.0 - t2 * 0.85))
            lay.put(ok, mx, my, 'W', tone, flat=True)
    return lay


# =========================================================================== papers
def papers_sheet(frames=8, w=18, h=9):
    """three loose sheets on the table; the top one's corner lifts and drops (draught)"""
    lay = _lay(w * frames, h, R)
    for f in range(frames):
        ox = f * w
        lift = [0, 1, 2, 3, 3, 2, 1, 0][f]
        lay.rect(ox + 1, h - 2, 12, 1, 'P', 4.0, flat=True)                         # bottom sheets (flat)
        lay.rect(ox + 3, h - 3, 12, 1, 'P', 5.0, flat=True)
        lay.rect(ox + 1, h - 1, 13, 1, 'P', 2.6, flat=True)                         # shadow edge
        # top sheet: left part flat, right corner rising with the draught
        for x in range(13):
            yy = h - 4
            if x > 7:
                yy -= int(round(lift * (x - 7) / 5.0))
            lay.px(ox + 4 + x, yy, 'P', 5.6 if x < 11 else 6.2, flat=True)
            if x > 7 and lift:
                lay.px(ox + 4 + x, yy + 1, 'P', 3.6, flat=True)                     # underside in shadow
        for k in range(2):
            lay.hline(ox + 5, h - 4 - 0, 1, 'I', 2.6, flat=True)
        lay.px(ox + 6, h - 4, 'I', 2.6, flat=True); lay.px(ox + 8, h - 4, 'I', 2.6, flat=True)
    return lay


# =========================================================================== tube station flap
def tube_sheet(frames=6, w=14, h=26):
    """0 closed, 1 flap kicked open, 2 capsule out, 3 capsule falling, 4 capsule in the basket, 5 flap settles"""
    lay = _lay(w * frames, h, R)
    for f in range(frames):
        ox = f * w
        # flap over the tube mouth (local 3..9, 3..9 of the station at x+1)
        if f in (0, 4):
            lay.rect(ox + 4, 3, 6, 6, 'A', 3.2, flat=True)
            lay.rect(ox + 4, 3, 6, 1, 'A', 4.6, flat=True)
            lay.px(ox + 9, 6, 'A', 2.0, flat=True)
        elif f in (1, 2, 3):
            lay.rect(ox + 4, 1, 6, 2, 'A', 4.0, flat=True)                          # flap swung up
            lay.rect(ox + 4, 0, 6, 1, 'A', 5.2, flat=True)
        else:
            lay.rect(ox + 4, 2, 6, 5, 'A', 3.6, flat=True)
        cap = {2: (5, 8), 3: (5, 13), 4: (4, 17), 5: (4, 17)}.get(f)
        if cap:
            cx, cy = cap
            if f >= 4:                                                             # lying in the basket
                lay.rect(ox + cx, cy, 7, 3, 'K', 3.6, flat=True)
                lay.rect(ox + cx, cy, 7, 1, 'K', 5.4, flat=True)
                lay.rect(ox + cx + 2, cy, 1, 3, 'A', 3.4, flat=True)
            else:
                lay.rect(ox + cx, cy, 4, 6, 'K', 3.6, flat=True)
                lay.rect(ox + cx, cy, 1, 6, 'K', 5.4, flat=True)
                lay.rect(ox + cx, cy + 2, 4, 1, 'A', 3.4, flat=True)
    return lay


# =========================================================================== radio glow
def radio_glow_sheet(frames=3, w=22, h=12):
    """overlay for the lodge radio: brighter dial + the magic eye's green wedge (closing as it tunes)"""
    lay = _lay(w * frames, h, R)
    for f in range(frames):
        ox = f * w
        lay.rect(ox + 2, 9, w - 4, 2, 'A', 5.6, flat=True)
        for k in range(3, w - 3, 3):
            lay.px(ox + k, 9, 'A', 4.4)
        lay.px(ox + 11, 10, 'R', 3.0)
        # magic eye: green fan with a dark wedge that narrows
        lay.rect(ox + 16, 3, 3, 3, 'G', 6.6, flat=True)
        wedge = [(17, 3), (17, 4)] if f == 0 else ([(17, 3)] if f == 1 else [])
        for (x, y) in wedge:
            lay.px(ox + x, y, 'G', 2.4)
    return lay


# =========================================================================== outer sills (layer)
def win_outer_layer():
    """Stone sills outside every window (seen through the lower panes) with snow on them -- the pigeons sit
    here.  Parallax 1, drawn between the snow fx and the room layer."""
    lay = kit.MLayer(L.WORLD_W, L.WORLD_H, RB, 'win_outer')
    rng = np.random.default_rng(611)
    for (x0, x1) in L.ALL_WINDOWS:
        wy0, wy1 = L.win_y(x0)
        # the hall window's sill sits higher in the glass (the pigeons stand there and must read); the
        # others are low so the passing tram stays visible
        top = wy1 - (10 if (x0, x1) in L.HALL_WINDOWS else 6)
        lay.rect(x0 - 2, top + 2, x1 - x0 + 4, wy1 - top - 2, 'STN', 2.6, flat=True)        # stone front
        lay.rect(x0 - 2, top + 6, x1 - x0 + 4, max(0, wy1 - top - 6), 'STN', 1.6, flat=True)  # drip shadow
        lay.rect(x0 - 2, top + 2, x1 - x0 + 4, 1, 'STN', 4.6, flat=True)
        lay.rect(x0 - 2, top + 5, x1 - x0 + 4, 1, 'STN', 1.6, flat=True)
        for x in range(x0 - 2, x1 + 2):                                                    # snow cushion
            hh = 1 + int(rng.random() < 0.6) + int(rng.random() < 0.25)
            lay.rect(x, top + 2 - hh, 1, hh, 'SNW', 3.4 + rng.random() * 1.2, flat=True)
            lay.px(x, top + 2 - hh, 'SNW', 4.6)
        # bird droppings + a few footprints in the snow (the pigeons come here every day)
        for k in range(4):
            lay.px(x0 + 4 + int(rng.integers(0, x1 - x0 - 8)), top + 3, 'SNW', 5.0)
    lay.unlit[:] = True
    lay.resolve()
    return lay


# =========================================================================== actors
def build_all(env_dir, room):
    """Write the actor sheets; return (files, actor entries for scene.json).  (The insignia overlays are
    scene.json "decals" handled by layer_stack.gd, see env_berlin.build_decals.)"""
    adir = os.path.join(env_dir, ACT_DIR_REL)
    os.makedirs(adir, exist_ok=True)
    files = []

    def res(name):
        return RES_ENV + ACT_DIR_REL + '/' + name

    tram, tinfo = tram_sheet()
    files.append((_save(tram, os.path.join(adir, 'tram.png')), 'tram motor car + trailer, side view (actor)'))
    files.append((_save(spark_sheet(), os.path.join(adir, 'spark.png')), 'pantograph spark, 4 frames (actor)'))
    pig, kinds = pigeons_sheet()
    files.append((_save(pig, os.path.join(adir, 'pigeons.png')), 'feral pigeon, 10 frames: idle, peck, ruffle, turn, fly'))
    mouse, mkinds = mouse_sheet()
    files.append((_save(mouse, os.path.join(adir, 'mouse.png')), 'archive mouse, 8 frames: peek, sniff, out, run'))
    pcx, pty, plen = room.regulator_pendulum
    pend, (pw, ph) = pendulum_sheet(plen)
    files.append((_save(pend, os.path.join(adir, 'pendulum.png')), 'regulator clock pendulum, 12 swing frames'))
    files.append((_save(steam_sheet(), os.path.join(adir, 'steam.png')), 'radiator valve steam puff, 12 frames'))
    files.append((_save(papers_sheet(), os.path.join(adir, 'papers.png')), 'loose sheets lifting in the draught, 8 frames'))
    files.append((_save(tube_sheet(), os.path.join(adir, 'tube.png')), 'pneumatic tube flap + capsule, 6 frames'))
    files.append((_save(radio_glow_sheet(), os.path.join(adir, 'radio_glow.png')), 'radio dial + magic eye glow overlay, 3 frames'))
    import env_berlin_fx as EFX
    files.append((EFX.build_smoke(adir), 'cigarette smoke curl over the porter\'s ashtray, 16 frames'))

    acts = []
    # ---- tram (every ~45 s, alternating direction), seen through the windows only
    glass = [[a, L.win_y(a)[0], b - a, L.win_y(a)[1] - L.win_y(a)[0]] for (a, b) in L.ALL_WINDOWS]
    acts.append({'scene': SCN + 'BerlinTram.tscn', 'pos': [0, 260],
                 'props': {'sheet_path': res('tram.png'), 'spark_path': res('spark.png'),
                           'sound_path': 'res://assets/audio/sfx/berlin_tram_rumble.wav',
                           'parallax': L.TRAM_P, 'top_y': float(tinfo['top']), 'pantograph_x': float(tinfo['pantograph_x']),
                           'wire_y': float(L.TRAM_WIRE_Y),
                           'period': 45.0, 'first_delay': 9.0, 'speed': 46.0,
                           'layer_width': float(L.layer_width(L.TRAM_P)), 'glass_rects': glass},
                 'note': 'tram on the street below; z -89 (behind the glass), warm light sweep through the windows'})
    # ---- pigeons on the outside sill of the hall window
    hx0, hx1 = L.HALL_WINDOWS[0]
    sill = L.win_y(hx0)[1] - 10 + 1
    acts.append({'scene': SCN + 'BerlinPigeons.tscn', 'pos': [hx0 + 6, sill],
                 'props': {'sheet_path': res('pigeons.png'), 'count': 3, 'span': float(hx1 - hx0 - 14),
                           'coo_path': 'res://assets/audio/sfx/berlin_pigeon_coo.wav',
                           'flutter_path': 'res://assets/audio/sfx/berlin_pigeon_flutter.wav'},
                 'note': 'exp_pigeons: they flutter off when Konrad comes close and return later'})
    # ---- mouse in the archive plinth
    mx, my = L.MOUSE_HOLE
    acts.append({'scene': SCN + 'BerlinMouse.tscn', 'pos': [mx, L.FLOOR],
                 'props': {'sheet_path': res('mouse.png'), 'squeak_path': 'res://assets/audio/sfx/berlin_mouse_squeak.wav'},
                 'note': 'exp_mouse: peeks out of the hole, sniffs, retreats when the player approaches'})
    # ---- clocks (hands drawn at runtime; same time on both)
    cx, cy, r = L.REG_FACE
    acts.append({'scene': SCN + 'BerlinClock.tscn', 'pos': [cx, cy],
                 'props': {'radius': float(r), 'second_hand': True, 'pendulum_path': res('pendulum.png'),
                           'pendulum_frames': 12, 'pendulum_offset': [pcx - cx - pw // 2, pty - cy],
                           'tick_path': 'res://assets/audio/sfx/berlin_clock_tick.wav',
                           'tock_path': 'res://assets/audio/sfx/berlin_clock_tock.wav',
                           'chime_path': 'res://assets/audio/sfx/berlin_clock_chime.wav'},
                 'note': 'exp_clock: working regulator (hands, pendulum, tick-tock, quarter chime)'})
    ox, oy = L.CLOCK
    acts.append({'scene': SCN + 'BerlinClock.tscn', 'pos': [ox, oy],
                 'props': {'radius': 5.0, 'second_hand': False, 'pendulum_path': '', 'tick_path': '',
                           'tock_path': '', 'chime_path': ''},
                 'note': 'office wall clock, same time as the regulator'})
    # ---- radiator steam + knocking (first library window)
    wx0, wx1 = L.LIB_WINDOWS[0]
    ny0 = L.LIB_WIN_Y[1] + 13
    vx, vy = wx0 - 3 + 3 - 5, ny0 + 6 + 3
    acts.append({'scene': SCN + 'BerlinRadiator.tscn', 'pos': [vx + 3, L.FLOOR - 1],
                 'props': {'steam_path': res('steam.png'), 'valve_offset': [0, vy - (L.FLOOR - 1)],
                           'knock_path': 'res://assets/audio/sfx/berlin_radiator_knock.wav',
                           'hiss_path': 'res://assets/audio/sfx/berlin_radiator_hiss.wav'},
                 'note': 'exp_heater: steam puffs at the valve, knocking in the pipes'})
    # ---- radio glow in the porter's lodge
    rx, ry = room.radio_pos
    acts.append({'scene': SCN + 'BerlinRadio.tscn', 'pos': [rx, 262],
                 'props': {'glow_path': res('radio_glow.png'), 'glow_offset': [0, ry - 262],
                           'loop_path': 'res://assets/audio/sfx/berlin_radio_loop.wav'},
                 'note': 'exp_radio: glowing dial, breathing magic eye, faint music'})
    # ---- papers stirring on the reading table (under the tilted fanlight)
    tx0 = L.LIB_READ_TABLE[0]
    acts.append({'scene': SCN + 'BerlinPapers.tscn', 'pos': [tx0 + 2, 295],
                 'props': {'sheet_path': res('papers.png'), 'sheet_offset': [0, 239 + 26 - 9 + 1 - 295],
                           'rustle_path': 'res://assets/audio/sfx/berlin_paper_flutter.wav'},
                 'note': 'papers lifting in the draught from the open fanlight'})
    # ---- pneumatic tube station (archive)
    sx, sy = room.tube_station
    acts.append({'scene': SCN + 'BerlinTube.tscn', 'pos': [sx, L.FLOOR - 1],
                 'props': {'sheet_path': res('tube.png'), 'sheet_offset': [-1, sy - (L.FLOOR - 1)],
                           'sound_path': 'res://assets/audio/sfx/berlin_tube_capsule.wav'},
                 'note': 'exp_pneumatic_tube: a capsule arrives now and then'})
    # ---- cigarette smoke over the porter's ashtray (y-sorted just in front of the lodge)
    acts.append({'scene': SCN + 'BerlinAnim.tscn', 'pos': [L.LODGE[0] + 90, 293.5],
                 'props': {'sheet_path': res('smoke_curl.png'), 'frames': 16, 'fps': 6.0,
                           'sheet_offset': [-6, int(L.LODGE_GLASS[1] - 3 - 36 - 293.5)]},
                 'note': 'smoke curling up from the porter\'s ashtray on the lodge sill'})
    return files, acts
