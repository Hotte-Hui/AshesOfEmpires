"""gen_ui -- original pixel-art UI kit for ASHES OF EMPIRES: THE LAST WINTER.

Draws every UI texture at 1:1 (one art pixel = one world pixel) and exports
  * assets/ui/src_1x/<name>.png        1:1 sources (not imported by Godot, .gdignore)
  * assets/ui/<group>/<name>.png       x3 nearest-neighbour versions used by theme.tres /
                                       scripts (StyleBoxTexture cannot scale, so 9-patch
                                       frames are stored pre-scaled; 1 art px = 3 screen px)
  * assets/ui/menu/menu_bg.png, assets/ui/portrait_placeholder.png and the plan placeholders
    stay 1:1 because they follow the world/portrait pipeline and are scaled x3 at runtime.
Style law: documentation/ART_DIRECTION.md + UI brief (deep navy translucent panels, thin
copper rules, paper tones, stamps; restrained 1960s Central/Eastern European documents).
All shapes are drawn procedurally here -- no reference image is sampled or traced.

Run:  py -3 -P tools/pixelgen/gen_ui.py          (deterministic, no network)
"""
from __future__ import annotations

import json
import math
import os
import sys

import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pg  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
OUT = os.path.join(ROOT, 'assets', 'ui')
SRC = os.path.join(OUT, 'src_1x')
PREVIEW = os.path.join(OUT, '_preview')

hx = pg.hx
CLEAR = np.array([0, 0, 0, 0], np.uint8)

# ----------------------------------------------------------------------------- UI palette
# (archive / karsk palette entries; the UI never introduces new hues)
NIGHT = '#04090D'
NIGHT1 = '#06151D'
NAVY = '#0B1C24'
NAVY_L = '#14272B'
WALL0, WALL1, WALL2, WALL3, WALL4 = '#1A2A2E', '#24373A', '#354448', '#4A5A5B', '#62716E'
COPPER_D, COPPER, COPPER_L, AMBER, AMBER_L = '#7A3E26', '#BA775B', '#DCA16E', '#F0C487', '#FBE3AE'
PAPER_D2, PAPER_D1, PAPER_D, PAPER_M, PAPER, PAPER_L = '#6E6A5C', '#8E8A78', '#B0AA93', '#CEC6AA', '#E6DEC2', '#F5EFDA'
INK, INK_B, RED_D, RED = '#1A1C2A', '#2E3248', '#7A2A26', '#A8382E'
TEAL = ['#122126', '#1B3033', '#26403F', '#36534D', '#4A675C']
RUST = ['#2E1C1A', '#4A2A22', '#6B3B2C', '#8D5542', '#AF6C47']

MANIFEST: list[dict] = []


def L(w, h):
    return pg.Layer(w, h)


def c(h, a=255):
    return hx(h, a)


def save(layer_or_arr, name, group='frames', scale=3, note=''):
    """Write 1:1 source + scaled runtime texture. Returns runtime res:// path."""
    arr = layer_or_arr.c if isinstance(layer_or_arr, pg.Layer) else layer_or_arr
    img = Image.fromarray(arr, 'RGBA')
    os.makedirs(SRC, exist_ok=True)
    img.save(os.path.join(SRC, name + '.png'))
    d = os.path.join(OUT, group)
    os.makedirs(d, exist_ok=True)
    out = img if scale == 1 else img.resize((img.width * scale, img.height * scale), Image.NEAREST)
    out.save(os.path.join(d, name + '.png'))
    rel = 'assets/ui/%s/%s.png' % (group, name)
    MANIFEST.append({'path': rel, 'size_1x': [img.width, img.height], 'scale': scale, 'note': note})
    return rel


def ring(l: pg.Layer, x, y, w, h, col, round_corners=False):
    l.rect(x, y, w, 1, col)
    l.rect(x, y + h - 1, w, 1, col)
    l.rect(x, y, 1, h, col)
    l.rect(x + w - 1, y, 1, h, col)
    if round_corners:
        for px, py in [(x, y), (x + w - 1, y), (x, y + h - 1), (x + w - 1, y + h - 1)]:
            l.c[py, px] = CLEAR


def chamfer_ring(l: pg.Layer, x, y, w, h, col, k=2):
    """1-px rule ring whose corners are cut by a k-px 45 degree chamfer."""
    l.rect(x + k, y, w - 2 * k, 1, col)
    l.rect(x + k, y + h - 1, w - 2 * k, 1, col)
    l.rect(x, y + k, 1, h - 2 * k, col)
    l.rect(x + w - 1, y + k, 1, h - 2 * k, col)
    for i in range(1, k):
        l.px(x + k - i, y + i, col)
        l.px(x + w - 1 - k + i, y + i, col)
        l.px(x + k - i, y + h - 1 - i, col)
        l.px(x + w - 1 - k + i, y + h - 1 - i, col)


# ============================================================================ frames (9-patch)
def frame_panel(hc=False):
    """Main modal panel: deep navy ~90 %, dark hairline, copper rule with chamfered corners."""
    w = h = 18
    l = L(w, h)
    fill = c(NIGHT1, 255) if hc else c(NAVY, 232)
    edge = c('#000000', 255) if hc else c(NIGHT, 246)
    rule = c(AMBER) if hc else c(COPPER)
    l.rect(0, 0, w, h, fill)
    ring(l, 0, 0, w, h, edge, round_corners=True)
    chamfer_ring(l, 2, 2, w - 4, h - 4, rule, k=3)
    # tiny copper rivet dots outside the chamfers (document corner registration)
    dot = c(COPPER_D) if not hc else c(COPPER_L)
    for px, py in [(2, 2), (w - 3, 2), (2, h - 3), (w - 3, h - 3)]:
        l.px(px, py, dot)
    return save(l, 'panel_hc' if hc else 'panel', note='9-patch margin 6 (18 px at x3)')


def frame_panel_solid():
    """Opaque variant for dialogs stacked over other panels (confirm, settings, save/load)."""
    w = h = 18
    l = L(w, h)
    l.rect(0, 0, w, h, c(NAVY, 252))
    ring(l, 0, 0, w, h, c(NIGHT, 255), round_corners=True)
    chamfer_ring(l, 2, 2, w - 4, h - 4, c(COPPER), k=3)
    for px, py in [(2, 2), (w - 3, 2), (2, h - 3), (w - 3, h - 3)]:
        l.px(px, py, c(COPPER_D))
    return save(l, 'panel_solid', note='9-patch margin 6, opaque')


def frame_band():
    """Chapter-card backing: translucent navy band whose ends and edges dissolve in ordered dither."""
    w, h = 72, 22
    l = L(w, h)
    thr = pg.bayer(w, h)
    for y in range(h):
        for x in range(w):
            ex = min(x, w - 1 - x) / 22.0          # 22 px dithered fade at both ends
            ey = min(y, h - 1 - y) / 5.0           # 5 px fade top/bottom
            t = min(1.0, ex) * min(1.0, ey)
            if t >= 1.0 or thr[y, x] < t:
                l.c[y, x] = c(NIGHT1, 205)
    return save(l, 'band', note='9-patch margins L24 R24 T6 B6 (x3: 72/18)')


def frame_paper_row():
    """Focus/selection row on paper: darker manila band with an ink-red index bar."""
    w, h = 12, 8
    l = L(w, h)
    l.rect(0, 0, w, h, c(PAPER_M))
    l.rect(0, 0, 2, h, c(RED_D))
    l.rect(2, h - 1, w - 2, 1, c(PAPER_D))
    l.rect(2, 0, w - 2, 1, c(PAPER_L))
    return save(l, 'paper_row', note='9-patch margins L4 T1 R1 B1')


def frame_plate():
    """HUD plate (objective tracker / toasts): translucent navy with copper index bar left."""
    w, h = 14, 10
    l = L(w, h)
    l.rect(0, 0, w, h, c(NAVY, 205))
    l.rect(0, 0, w, 1, c(NIGHT, 215))
    l.rect(0, h - 1, w, 1, c(NIGHT, 215))
    l.rect(w - 1, 0, 1, h, c(NIGHT, 215))
    l.c[0, w - 1] = CLEAR
    l.c[h - 1, w - 1] = CLEAR
    l.rect(0, 0, 2, h, c(COPPER))
    l.rect(0, 0, 1, h, c(COPPER_D))
    l.rect(1, 0, 1, 1, c(COPPER_L))
    return save(l, 'plate', note='9-patch margins L5 T3 R3 B3')


def frame_prompt():
    w = h = 10
    l = L(w, h)
    l.rect(0, 0, w, h, c(NAVY, 238))
    ring(l, 0, 0, w, h, c(COPPER), round_corners=True)
    l.rect(1, 1, w - 2, 1, c(NAVY_L, 238))
    return save(l, 'prompt', note='9-patch margin 3')


def prompt_tail():
    l = L(7, 4)
    pts = [(0, 0), (6, 0), (3, 3)]
    for y in range(4):
        x0, x1 = y, 6 - y
        for x in range(x0, x1 + 1):
            edge = x in (x0, x1) or y == 3
            l.px(x, y, c(COPPER) if edge else c(NAVY, 238))
    l.px(0, 0, c(COPPER)); l.px(6, 0, c(COPPER))
    for x in range(1, 6):
        l.px(x, 0, c(NAVY, 238))
    return save(l, 'prompt_tail', group='icons')


def frame_keycap(pressed=False):
    """Mechanical key: face, bevel highlight, front skirt. Margins L4 T4 R4 B5."""
    w, h = 12, 13
    l = L(w, h)
    out = c(NIGHT)
    l.rect(1, 0, w - 2, h, out)
    l.rect(0, 1, w, h - 2, out)
    # skirt (front face) 3 px
    l.rect(1, h - 4, w - 2, 3, c(NAVY))
    l.rect(1, h - 2, w - 2, 1, c(NIGHT1))
    # top face
    l.rect(1, 1, w - 2, h - 5, c(WALL1))
    l.rect(2, 1, w - 4, 1, c(WALL3))          # top bevel highlight
    l.rect(1, 2, 1, h - 7, c(WALL2))          # left bevel
    l.rect(w - 2, 2, 1, h - 7, c(WALL0))      # right bevel shade
    l.rect(2, h - 5, w - 4, 1, c(WALL0))      # face/skirt crease
    return save(l, 'keycap', note='9-patch margins L4 T4 R4 B5')


def frame_paper():
    """Paper sheet with hairline edge, 1 px drop shadow and a folded corner (top right)."""
    w = h = 22
    l = L(w, h)
    sh = c('#000000', 95)
    l.rect(2, 2, w - 2, h - 2, sh)
    pw, ph = w - 1, h - 1
    l.rect(0, 0, pw, ph, c(PAPER))
    ring(l, 0, 0, pw, ph, c(PAPER_D), round_corners=True)
    l.c[0, 0] = CLEAR; l.c[0, pw - 1] = CLEAR; l.c[ph - 1, 0] = CLEAR; l.c[ph - 1, pw - 1] = CLEAR
    # faint inner tone band (aged margin) -- only inside the fixed corner/edge regions
    for i in range(1, pw - 1):
        l.c[1, i] = c(PAPER_L) if i % 5 else c(PAPER)
    # folded corner top-right (4 px)
    k = 4
    for y in range(k):
        for x in range(pw - k + y, pw):
            l.c[y, x] = CLEAR if y < k - 1 or x > pw - 1 else l.c[y, x]
    for i in range(k):
        l.px(pw - k + i, i, c(PAPER_D))
    for y in range(1, k):
        for x in range(pw - k, pw - k + y):
            l.px(x, y, c(PAPER_M))
    l.px(pw - k, 0, c(PAPER_D))
    # corner wear specks (fixed regions only)
    for px, py in [(2, ph - 2), (3, ph - 2), (1, ph - 4), (pw - 2, ph - 3)]:
        l.px(px, py, c(PAPER_M))
    return save(l, 'paper', note='9-patch margin 7, content on PAPER #E6DEC2')


def frame_paper_dark():
    """Inactive paper index tab / list card: aged manila tone."""
    w = h = 12
    l = L(w, h)
    l.rect(0, 0, w, h, c(PAPER_M))
    ring(l, 0, 0, w, h, c(PAPER_D1), round_corners=True)
    l.rect(1, 1, w - 2, 1, c(PAPER))
    return save(l, 'paper_card', note='9-patch margin 3')


def frame_button(state):
    """Bordered action button plates."""
    w = h = 10
    l = L(w, h)
    if state == 'normal':
        l.rect(0, 0, w, h, c(NAVY, 215))
        ring(l, 0, 0, w, h, c(WALL2), round_corners=True)
        l.rect(1, h - 2, w - 2, 1, c(NIGHT1, 230))
    elif state == 'hover':
        l.rect(0, 0, w, h, c(NAVY_L, 240))
        ring(l, 0, 0, w, h, c(COPPER), round_corners=True)
        l.rect(1, 1, w - 2, 1, c(WALL1, 240))
    elif state == 'pressed':
        l.rect(0, 0, w, h, c(NIGHT1, 245))
        ring(l, 0, 0, w, h, c(COPPER_D), round_corners=True)
        l.rect(1, 1, w - 2, 1, c(NIGHT, 245))
    elif state == 'disabled':
        l.rect(0, 0, w, h, c(NAVY, 120))
        ring(l, 0, 0, w, h, c(WALL0, 170), round_corners=True)
    elif state == 'focus':
        ring(l, 0, 0, w, h, c(COPPER_L), round_corners=True)
        for px, py in [(1, 1), (w - 2, 1), (1, h - 2), (w - 2, h - 2)]:
            l.px(px, py, c(COPPER_L))
    return save(l, 'button_' + state, note='9-patch margin 3')


def frame_menu_band(state):
    """Text-list menu entries (main/pause menu, choices): copper index bar + soft band."""
    w, h = 12, 8
    l = L(w, h)
    if state == 'focus':
        l.rect(3, 0, w - 3, h, c(NAVY_L, 175))
        l.rect(0, 0, 2, h, c(COPPER_L))
        l.rect(0, 0, 1, h, c(COPPER))
        l.rect(3, h - 1, w - 3, 1, c(COPPER_D, 220))
    elif state == 'pressed':
        l.rect(3, 0, w - 3, h, c(NIGHT1, 220))
        l.rect(0, 0, 2, h, c(COPPER))
        l.rect(3, h - 1, w - 3, 1, c(COPPER_D, 220))
    return save(l, 'menu_' + state, note='9-patch margins L4 T1 R1 B1')


def frame_tab(state, paper=False):
    """Folder tabs. Navy tabs for settings, paper index tabs for the journal dossier."""
    w, h = 16, 11
    l = L(w, h)
    if paper:
        fill = {'normal': PAPER_M, 'hover': PAPER, 'pressed': PAPER, 'focus': None}[state]
        edge = {'normal': PAPER_D1, 'hover': PAPER_D, 'pressed': PAPER_D, 'focus': COPPER}[state]
    else:
        fill = {'normal': NAVY, 'hover': NAVY_L, 'pressed': NAVY_L, 'focus': None}[state]
        edge = {'normal': WALL1, 'hover': COPPER, 'pressed': COPPER, 'focus': COPPER_L}[state]
    a = 235 if not paper else 255
    # tab silhouette: 3 px chamfer on top corners, open bottom
    for y in range(h):
        inset = max(0, 3 - y)
        for x in range(inset, w - inset):
            if fill is not None:
                l.px(x, y, c(fill, a))
        if state != 'focus' or True:
            l.px(inset, y, c(edge))
            l.px(w - 1 - inset, y, c(edge))
    l.rect(3, 0, w - 6, 1, c(edge))
    if state == 'pressed' and not paper:
        l.rect(3, 1, w - 6, 1, c(COPPER_L))
    if state == 'normal' and fill is not None:
        l.rect(0, h - 1, w, 1, c(edge))          # inactive tabs sit behind a baseline
    if state == 'focus':
        # focus overlay: only the outline, copper light, plus inner tick
        l.c[:] = CLEAR
        for y in range(h):
            inset = max(0, 3 - y)
            l.px(inset, y, c(COPPER_L))
            l.px(w - 1 - inset, y, c(COPPER_L))
        l.rect(3, 0, w - 6, 1, c(COPPER_L))
    name = ('ptab_' if paper else 'tab_') + state
    return save(l, name, note='9-patch margins L4 T4 R4 B2')


def frame_slot():
    """Save-slot / list card (navy, fine rule)."""
    w = h = 12
    l = L(w, h)
    l.rect(0, 0, w, h, c(NAVY, 200))
    ring(l, 0, 0, w, h, c(WALL1), round_corners=True)
    l.rect(1, 1, w - 2, 1, c(NAVY_L, 210))
    return save(l, 'slot', note='9-patch margin 3')


def frame_portrait():
    """Portrait mount: dark passe-partout, copper rule, inner shadow."""
    w = h = 16
    l = L(w, h)
    l.rect(0, 0, w, h, c(NIGHT, 250))
    ring(l, 0, 0, w, h, c(NIGHT, 255), round_corners=True)
    ring(l, 2, 2, w - 4, h - 4, c(COPPER))
    l.rect(4, 4, w - 8, h - 8, CLEAR)
    l.rect(3, 3, w - 6, 1, c(NIGHT1))
    l.rect(3, 3, 1, h - 6, c(NIGHT1))
    for px, py in [(2, 2), (w - 3, 2), (2, h - 3), (w - 3, h - 3)]:
        l.px(px, py, c(COPPER_L))
    return save(l, 'portrait_frame', note='9-patch margin 4; centre transparent')


def frame_scroll():
    l = L(5, 8)
    l.rect(1, 0, 3, 8, c(NIGHT, 200))
    l.rect(2, 0, 1, 8, c(WALL0, 220))
    save(l, 'scroll_track', note='9-patch margin 2')
    g = L(5, 8)
    g.rect(1, 0, 3, 8, c(COPPER_D))
    g.rect(1, 1, 3, 6, c(COPPER))
    g.rect(2, 1, 1, 6, c(COPPER_L))
    save(g, 'scroll_grabber', note='9-patch margin 2')
    gh = L(5, 8)
    gh.rect(1, 0, 3, 8, c(COPPER))
    gh.rect(1, 1, 3, 6, c(COPPER_L))
    gh.rect(2, 1, 1, 6, c(AMBER))
    save(gh, 'scroll_grabber_hl', note='9-patch margin 2')


def slider_parts():
    t = L(8, 5)
    t.rect(0, 0, 8, 5, c(NIGHT))
    t.rect(1, 1, 6, 3, c(NIGHT1))
    t.rect(1, 3, 6, 1, c(NAVY_L))
    t.c[0, 0] = CLEAR; t.c[0, 7] = CLEAR; t.c[4, 0] = CLEAR; t.c[4, 7] = CLEAR
    save(t, 'slider_track', note='9-patch margin 2')
    f = L(8, 5)
    f.rect(0, 0, 8, 5, c(NIGHT))
    f.rect(1, 1, 6, 3, c(COPPER))
    f.rect(1, 1, 6, 1, c(COPPER_L))
    f.rect(1, 3, 6, 1, c(COPPER_D))
    f.c[0, 0] = CLEAR; f.c[0, 7] = CLEAR; f.c[4, 0] = CLEAR; f.c[4, 7] = CLEAR
    save(f, 'slider_fill', note='9-patch margin 2')
    for name, body, hi, rim in [('slider_grabber', PAPER, PAPER_L, NIGHT),
                                ('slider_grabber_hl', AMBER_L, '#FFFFFF', COPPER_D),
                                ('slider_grabber_off', WALL3, WALL4, NIGHT)]:
        g = L(7, 13)
        g.rect(1, 0, 5, 13, c(rim))
        g.rect(0, 1, 7, 11, c(rim))
        g.rect(1, 1, 5, 11, c(body))
        g.rect(1, 1, 5, 1, c(hi))
        g.rect(1, 10, 5, 2, c(PAPER_D) if body == PAPER else c(COPPER_L) if body == AMBER_L else c(WALL2))
        g.rect(3, 3, 1, 6, c(COPPER) if body != WALL3 else c(WALL1))  # notch
        save(g, name, group='icons')


def checkbox_icons():
    def box(checked, disabled=False):
        l = L(11, 11)
        rim = c(WALL1) if disabled else c(WALL4)
        l.rect(0, 0, 11, 11, c(NIGHT))
        l.rect(1, 1, 9, 9, rim)
        l.rect(2, 2, 7, 7, c(NIGHT1))
        l.c[0, 0] = CLEAR; l.c[0, 10] = CLEAR; l.c[10, 0] = CLEAR; l.c[10, 10] = CLEAR
        if checked:
            col = c(WALL3) if disabled else c(AMBER)
            sh = c(COPPER_D) if not disabled else c(WALL1)
            tick = [(3, 5), (4, 6), (5, 7), (6, 6), (7, 5), (8, 4), (9, 3)]
            for (x, y) in tick:
                if x < 9:
                    l.px(x, y, col)
                    l.px(x, y + 1, sh)
            l.px(8, 3, col); l.px(8, 4, col); l.px(3, 4, col)
        return l
    save(box(False), 'check_off', group='icons')
    save(box(True), 'check_on', group='icons')
    save(box(False, True), 'check_off_disabled', group='icons')
    save(box(True, True), 'check_on_disabled', group='icons')


# ============================================================================ small sprites
def ornaments():
    d = L(7, 7)
    for y in range(7):
        r = 3 - abs(3 - y)
        for x in range(3 - r, 4 + r):
            d.px(x, y, c(COPPER))
    d.px(3, 0, c(COPPER_L)); d.px(2, 1, c(COPPER_L)); d.px(1, 2, c(COPPER_L))
    d.px(3, 3, c(NIGHT))
    save(d, 'ornament_diamond', group='icons')
    m = L(5, 9)
    for y in range(9):
        r = 4 - abs(4 - y)
        for x in range(0, r + 1):
            m.px(x, y, c(COPPER_L))
    for y in range(9):
        r = 4 - abs(4 - y)
        m.px(r, y, c(AMBER))
    save(m, 'marker_arrow', group='icons')
    a = L(9, 6)
    for y in range(5):
        for x in range(y, 9 - y):
            a.px(x, y, c(PAPER))
    for y in range(5):
        a.px(y, y, c(COPPER)); a.px(8 - y, y, c(COPPER))
    a.rect(0, 0, 9, 1, c(COPPER_L))
    a.px(4, 5, c(COPPER_D))
    save(a, 'advance_arrow', group='icons')
    for name, flip in [('arrow_right', False), ('arrow_left', True)]:
        r = L(6, 9)
        for y in range(9):
            w_ = 4 - abs(4 - y)
            for x in range(0, w_ + 1):
                r.px(x if not flip else 5 - x, y, c(COPPER_L))
        save(r, name, group='icons')


def _icon_doc(l, ox, oy):
    pw, ph = 9, 11
    l.rect(ox, oy, pw, ph, c(PAPER))
    ring(l, ox, oy, pw, ph, c(PAPER_D1))
    for i in range(3):
        l.px(ox + pw - 1 - i, oy + 2 - i, CLEAR)
    for i in range(3):
        l.px(ox + pw - 3 + i, oy + i, c(PAPER_D1))
    l.px(ox + pw - 3, oy + 1, c(PAPER_M)); l.px(ox + pw - 3, oy + 2, c(PAPER_D1)); l.px(ox + pw - 2, oy + 2, c(PAPER_D1))
    for k, ln in enumerate([5, 6, 4]):
        l.rect(ox + 2, oy + 4 + 2 * k, ln, 1, c(INK_B))


def icons():
    # person (ink, for lists on paper)
    l = L(13, 13)
    l.ellipse(6.5, 4.5, 2.6, 3.0, c(INK_B))
    l.poly([(1, 13), (2, 9), (5, 8), (8, 8), (11, 9), (12, 13)], c(INK))
    l.rect(5, 7, 3, 2, c(INK))
    l.px(6, 9, c(RED)); l.px(6, 10, c(RED))
    save(l, 'icon_person_ink', group='icons')
    # evidence: document with red stamp
    l = L(13, 13)
    _icon_doc(l, 1, 1)
    l.rect(6, 8, 5, 4, c(RED)); l.rect(7, 9, 3, 2, c(PAPER_M)); l.px(8, 9, c(RED))
    save(l, 'icon_evidence', group='icons')
    # journal: notebook with elastic band
    l = L(13, 13)
    l.rect(2, 1, 9, 11, c('#3D2820'))
    ring(l, 2, 1, 9, 11, c('#2A1B16'))
    l.rect(3, 2, 1, 9, c('#55372A'))
    l.rect(10, 2, 1, 9, c(PAPER_M))
    l.rect(7, 1, 1, 11, c(COPPER))
    l.rect(4, 4, 3, 1, c(PAPER_D))
    save(l, 'icon_journal', group='icons')
    # objective: waypoint diamond with centre
    l = L(13, 13)
    for y in range(11):
        r = 5 - abs(5 - y)
        l.px(6 - r, y + 1, c(COPPER_L)); l.px(6 + r, y + 1, c(COPPER_L))
    for y in range(3, 10):
        r = 3 - abs(6 - y)
        if r >= 0:
            for x in range(6 - r, 7 + r):
                l.px(x, y, c(COPPER))
    l.px(6, 6, c(AMBER_L))
    save(l, 'icon_objective', group='icons')
    # person: bust
    l = L(13, 13)
    l.ellipse(6.5, 4.5, 2.6, 3.0, c(PAPER))
    l.poly([(1, 13), (2, 9), (5, 8), (8, 8), (11, 9), (12, 13)], c(PAPER_D))
    l.rect(5, 7, 3, 2, c(PAPER_D))
    l.px(6, 9, c(COPPER)); l.px(6, 10, c(COPPER))
    save(l, 'icon_person', group='icons')
    # decision: forking path
    l = L(13, 13)
    l.rect(6, 7, 1, 6, c(PAPER))
    l.line(6, 7, 2, 3, c(PAPER)); l.line(6, 7, 10, 3, c(PAPER))
    for (x, y) in [(1, 2), (2, 2), (1, 3), (10, 2), (11, 2), (11, 3)]:
        l.px(x, y, c(COPPER_L))
    l.px(2, 1, c(COPPER_L)); l.px(10, 1, c(COPPER_L))
    save(l, 'icon_decision', group='icons')
    # save: archive folder
    l = L(13, 13)
    l.rect(1, 3, 11, 9, c(PAPER_M))
    l.rect(1, 2, 5, 1, c(PAPER_M))
    ring(l, 1, 3, 11, 9, c(PAPER_D1))
    l.rect(2, 5, 9, 1, c(PAPER_D))
    l.rect(4, 8, 5, 2, c(RED))
    save(l, 'icon_save', group='icons')
    # hint: pencil
    l = L(13, 13)
    for i in range(8):
        l.px(3 + i, 9 - i, c(AMBER)); l.px(4 + i, 9 - i, c(COPPER)); l.px(3 + i, 10 - i, c(COPPER_D))
    l.px(2, 11, c(INK)); l.px(3, 10, c(PAPER_D)); l.px(2, 10, c(PAPER_D))
    l.px(11, 2, c(RED)); l.px(12, 1, c(RED)); l.px(11, 1, c(RED_D))
    save(l, 'icon_hint', group='icons')
    # check (completed) and open (pending) small marks for lists on paper
    l = L(9, 9)
    ring(l, 0, 0, 9, 9, c(INK_B))
    for (x, y) in [(2, 4), (3, 5), (4, 6), (5, 5), (6, 4), (7, 3), (8, 2)]:
        l.px(x, y, c(RED)); l.px(x, y - 1, c(RED))
    save(l, 'mark_done', group='icons')
    l = L(9, 9)
    ring(l, 0, 0, 9, 9, c(INK_B))
    save(l, 'mark_open', group='icons')


def stamp(name, w, h, angle_deg, seed=3, col=RED):
    """Rubber stamp frame: double rule, pre-rotated at 1:1, ink gaps."""
    l = L(w, h)
    rng = np.random.default_rng(seed)
    a = math.radians(angle_deg)
    cx, cy = w / 2, h / 2
    bw, bh = w - 8, h - 8
    yy, xx = np.mgrid[0:h, 0:w]
    dx, dy = xx + 0.5 - cx, yy + 0.5 - cy
    u = dx * math.cos(a) + dy * math.sin(a)
    v = -dx * math.sin(a) + dy * math.cos(a)
    au, av = np.abs(u), np.abs(v)
    outer = (au <= bw / 2) & (av <= bh / 2)
    inner1 = (au <= bw / 2 - 1.2) & (av <= bh / 2 - 1.2)
    ring2o = (au <= bw / 2 - 2.6) & (av <= bh / 2 - 2.6)
    ring2i = (au <= bw / 2 - 3.6) & (av <= bh / 2 - 3.6)
    m = (outer & ~inner1) | (ring2o & ~ring2i)
    noise = pg.value_noise(w, h, 3, seed, octaves=2)
    m &= ~(noise < 0.22)
    m &= rng.random((h, w)) > 0.06
    l.c[m] = c(col, 235)
    return save(l, name, group='icons', note='rotated %.1f deg at 1:1' % angle_deg)


# ============================================================================ puzzle art
def symbol_card(shape):
    """Enamel teaching-board plate (fictional, unpowered training box)."""
    w, h = 34, 46
    l = L(w, h)
    l.rect(1, 0, w - 2, h, c(NIGHT))
    l.rect(0, 1, w, h - 2, c(NIGHT))
    l.rect(1, 1, w - 2, h - 2, c(INK_B))
    l.rect(2, 2, w - 4, h - 4, c(PAPER))
    l.rect(2, h - 4, w - 4, 2, c(PAPER_M))
    l.rect(2, 2, w - 4, 1, c(PAPER_L))
    l.rect(w - 3, 3, 1, h - 6, c(PAPER_M))
    # mounting holes
    for hx_ in (6, w - 7):
        l.px(hx_, 5, c(NIGHT)); l.px(hx_ + 1, 5, c(INK_B)); l.px(hx_, 6, c(INK_B))
    # enamel chips
    for (x, y) in [(2, 12), (2, 13), (w - 3, 30), (11, h - 3), (12, h - 3), (25, 2)]:
        l.px(x, y, c(PAPER_D1))
    cx, cy = w / 2, 25
    ink = c(INK)
    if shape == 'square':
        l.rect(int(cx - 8), int(cy - 8), 16, 16, ink)
        l.rect(int(cx - 6), int(cy - 6), 12, 1, c(INK_B))
    elif shape == 'circle':
        l.ellipse(cx, cy, 9.2, 9.2, ink)
        l.px(int(cx - 4), int(cy - 6), c(INK_B)); l.px(int(cx - 5), int(cy - 5), c(INK_B))
    elif shape == 'triangle':
        l.poly([(cx, cy - 10), (cx + 10.5, cy + 8.5), (cx - 10.5, cy + 8.5)], ink)
        l.px(int(cx - 1), int(cy - 6), c(INK_B))
    # stencil index pips (language-neutral)
    return save(l, 'card_' + shape, group='puzzle')


def signal_board():
    """Fictional, disconnected training box: painted steel, three plate recesses, lamp."""
    w, h = 176, 92
    l = L(w, h)
    body = TEAL
    l.rect(0, 0, w, h, c(NIGHT))
    l.rect(1, 1, w - 2, h - 2, c(body[1]))
    # paint tone noise (worn enamel)
    nz = pg.value_noise(w, h, 9, 41, octaves=3)
    m = np.zeros((h, w), bool); m[2:h - 2, 2:w - 2] = True
    t = 0.35 + (nz - 0.5) * 0.5
    l.tone_fill(m[2:h - 2, 2:w - 2], 2, 2, t[2:h - 2, 2:w - 2], [c(body[0]), c(body[1]), c(body[2])])
    l.rect(1, 1, w - 2, 1, c(body[3]))
    l.rect(1, 2, w - 2, 1, c(body[2]))
    l.rect(1, h - 2, w - 2, 1, c(body[0]))
    l.rect(1, 1, 1, h - 2, c(body[3]))
    l.rect(w - 2, 1, 1, h - 2, c(body[0]))
    # header strip with lamp
    l.rect(4, 4, w - 8, 14, c(body[0]))
    l.rect(4, 4, w - 8, 1, c(NIGHT1))
    l.rect(4, 17, w - 8, 1, c(body[3]))
    # three slot recesses (each 38 x 50 incl. lip)
    slots = []
    sw, sh_ = 38, 52
    gap = (w - 3 * sw) // 4
    for i in range(3):
        x = gap + i * (sw + gap)
        y = 24
        slots.append((x, y, sw, sh_))
        l.rect(x - 1, y - 1, sw + 2, sh_ + 2, c(body[3]))
        l.rect(x, y, sw, sh_, c('#0A1219'))
        l.rect(x, y, sw, 2, c(NIGHT))
        l.rect(x, y, 2, sh_, c(NIGHT))
        l.rect(x + 2, y + sh_ - 1, sw - 2, 1, c(body[1]))
        # guide rails
        l.rect(x + 3, y + 3, 1, sh_ - 6, c(body[0]))
        l.rect(x + sw - 4, y + 3, 1, sh_ - 6, c(body[0]))
        # index pips above (1, 2, 3 dots)
        for k in range(i + 1):
            px_ = x + sw // 2 - i * 2 + k * 4
            l.px(px_, 20, c(COPPER_L)); l.px(px_, 21, c(COPPER_D))
    # rivets with rust streaks
    rng = np.random.default_rng(5)
    for (x, y) in [(3, 3), (w - 4, 3), (3, h - 4), (w - 4, h - 4), (w // 2, h - 4), (w // 2, 3)]:
        l.px(x, y, c(body[4])); l.px(x + 1, y + 1, c(NIGHT))
        if y > 10:
            continue
        for k in range(2, 2 + int(rng.integers(2, 6))):
            if y + k < h - 2:
                l.px(x, y + k, c(RUST[2]) if k < 4 else c(RUST[1]))
    # stencilled hazard-free label plate (blank paper label, text is HD)
    l.rect(8, 6, 58, 10, c(PAPER_D))
    l.rect(9, 7, 56, 8, c(PAPER_M))
    l.rect(9, 7, 56, 1, c(PAPER))
    l.px(9, 14, c(PAPER_D1)); l.px(64, 7, c(PAPER_D1))
    # lamp housing (right header)
    lx, ly = w - 22, 11
    l.ellipse(lx, ly, 6.5, 6.5, c(NIGHT))
    l.ellipse(lx, ly, 5.2, 5.2, c(body[3]))
    l.ellipse(lx, ly, 4.0, 4.0, c('#1B1A16'))
    l.px(lx - 2, ly - 2, c('#3A3428'))
    # scratches
    for _ in range(14):
        x = int(rng.integers(6, w - 8)); y = int(rng.integers(20, h - 6))
        if all(not (sx - 1 <= x <= sx + sw and sy - 1 <= y <= sy + sh_) for sx, sy, sw, sh_ in slots):
            l.px(x, y, c(body[3]))
    save(l, 'signal_board', group='puzzle')
    meta = {'size': [w, h], 'slots': [list(s) for s in slots], 'lamp': [lx, ly], 'plate': [9, 7, 56, 8]}
    with open(os.path.join(OUT, 'puzzle', 'signal_board.json'), 'w', encoding='utf-8') as f:
        json.dump(meta, f, indent=1)
    # lamp states (overlay, 15x15)
    off = L(15, 15)
    on = L(15, 15)
    yy, xx = np.mgrid[0:15, 0:15]
    d = np.sqrt((xx - 7) ** 2 + (yy - 7) ** 2)
    thr = pg.bayer(15, 15)
    on.c[(d <= 7.4) & (thr < np.clip((7.4 - d) / 3.0, 0, 1) * 0.55)] = c(AMBER, 150)
    on.ellipse(7.5, 7.5, 4.0, 4.0, c(COPPER_L))
    on.ellipse(7.5, 7.5, 3.0, 3.0, c(AMBER))
    on.ellipse(7.0, 7.0, 1.6, 1.6, c(AMBER_L))
    on.px(6, 6, c('#FFFFFF'))
    off.ellipse(7.5, 7.5, 4.0, 4.0, c('#1B1A16'))
    off.ellipse(7.5, 7.5, 3.0, 3.0, c('#26231C'))
    off.px(6, 6, c('#4A4234'))
    save(off, 'lamp_off', group='puzzle')
    save(on, 'lamp_on', group='puzzle')


def slot_frame():
    """Empty target slot outline used in the HD order row."""
    w, h = 34, 46
    l = L(w, h)
    for x in range(0, w, 3):
        l.px(x, 0, c(WALL3)); l.px(x, h - 1, c(WALL3))
    for y in range(0, h, 3):
        l.px(0, y, c(WALL3)); l.px(w - 1, y, c(WALL3))
    return save(l, 'card_slot', group='puzzle')


def reg_marks():
    """Registration marks for the overlay puzzle: A = solid ring + cross, B = open diamond + cross.
    Distinguishable by shape (accessibility), not colour."""
    a = L(13, 13)
    a.ellipse(6.5, 6.5, 6.0, 6.0, c(INK))
    a.ellipse(6.5, 6.5, 4.2, 4.2, CLEAR)
    a.rect(6, 0, 1, 13, c(INK))
    a.rect(0, 6, 13, 1, c(INK))
    a.px(6, 6, c(RED))
    save(a, 'mark_a', group='puzzle')
    b = L(17, 17)
    for y in range(17):
        r = 8 - abs(8 - y)
        b.px(8 - r, y, c('#2B3C50')); b.px(8 + r, y, c('#2B3C50'))
        if 0 < r:
            b.px(8 - r + 1, y, c('#58718A')); b.px(8 + r - 1, y, c('#58718A'))
    for k in range(17):
        if k % 2 == 0:
            b.px(8, k, c('#2B3C50')); b.px(k, 8, c('#2B3C50'))
    save(b, 'mark_b', group='puzzle')


def plan_placeholders(cell=16):
    """Fallback plans (only used if assets/ui/documents/berlin_plan_*.png are missing).
    Fictional, simplified floor plans; B is an earlier draft with an extra corridor.  The
    shared chimney + stair sit at A-cell (cx, cy) and B-cell (cx - 2, cy + 1) so the canonical
    answer {rotation_steps 0, offset_x 2, offset_y -1} superimposes them."""
    cols, rows = 14, 9
    W, H = cols * cell, rows * cell

    def sheet(tint_lines, paper, alpha=255):
        l = L(W, H)
        l.rect(0, 0, W, H, c(paper, alpha))
        ring(l, 0, 0, W, H, c(tint_lines, alpha))
        ring(l, 2, 2, W - 4, H - 4, c(tint_lines, min(alpha, 200)))
        for gx in range(cell, W, cell):
            for gy in range(4, H - 4, 2):
                l.px(gx, gy, c(PAPER_M if paper == PAPER else '#A7BCCB', alpha))
        for gy in range(cell, H, cell):
            for gx in range(4, W - 4, 2):
                l.px(gx, gy, c(PAPER_M if paper == PAPER else '#A7BCCB', alpha))
        return l

    def wall(l, x0, y0, x1, y1, col, alpha=255):
        if x0 == x1:
            l.rect(x0 * cell - 1, y0 * cell - 1, 3, (y1 - y0) * cell + 3, c(col, alpha))
        else:
            l.rect(x0 * cell - 1, y0 * cell - 1, (x1 - x0) * cell + 3, 3, c(col, alpha))

    def chimney(l, cx, cy, col, alpha=255):
        x, y = cx * cell + 3, cy * cell + 3
        l.rect(x, y, cell - 6, cell - 6, c(col, alpha))
        l.rect(x + 3, y + 3, cell - 12, cell - 12, CLEAR if alpha < 255 else c(PAPER))

    def stair(l, cx, cy, col, alpha=255):
        x, y = cx * cell + 2, cy * cell + 2
        ring(l, x, y, cell * 2 - 4, cell - 4, c(col, alpha))
        for k in range(4, cell * 2 - 6, 4):
            l.rect(x + k, y + 1, 1, cell - 6, c(col, alpha))
        l.line(x + 3, y + cell // 2 - 2, x + cell * 2 - 8, y + cell // 2 - 2, c(col, alpha))

    # Plan A (approved): rooms, chimney at (9,3), stair at (4,5)
    a = sheet(INK_B, PAPER)
    ink = INK_B
    wall(a, 1, 1, 13, 1, ink); wall(a, 1, 8, 13, 8, ink); wall(a, 1, 1, 1, 8, ink); wall(a, 13, 1, 13, 8, ink)
    wall(a, 6, 1, 6, 5, ink); wall(a, 6, 5, 13, 5, ink); wall(a, 9, 5, 9, 8, ink)
    wall(a, 1, 4, 4, 4, ink)
    chimney(a, 9, 3, ink); stair(a, 4, 5, ink)
    # door arcs
    for (dx, dy) in [(6, 3), (9, 6)]:
        a.rect(dx * cell - 1, dy * cell + 2, 3, cell - 4, c(PAPER))
    save(a, 'plan_placeholder_a', group='puzzle', scale=1, note='fallback plan A, cell %d' % cell)
    # Plan B (earlier draft) on tracing paper; features shifted by (-2, +1) cells
    b = L(W, H)
    blue = '#2B3C50'
    ring(b, 0, 0, W, H, c(blue))
    ring(b, 2, 2, W - 4, H - 4, c(blue, 160))
    wall(b, 0, 2, 12, 2, blue); wall(b, 3, 2, 3, 7, blue); wall(b, 7, 2, 7, 6, blue)
    chimney(b, 7, 4, blue, 255); stair(b, 2, 6, blue, 255)
    # the hidden corridor behind the wall (dashed double line)
    for x in range(8 * cell, 12 * cell, 4):
        b.rect(x, 5 * cell - 3, 2, 1, c(RED)); b.rect(x, 6 * cell + 2, 2, 1, c(RED))
    save(b, 'plan_placeholder_b', group='puzzle', scale=1, note='fallback plan B (overlay), cell %d' % cell)
    meta = {'cell': cell, 'grid': [cols, rows], 'landmarks': [
        {'name': 'chimney', 'a': [9, 3], 'b': [7, 4]},
        {'name': 'stair', 'a': [4, 5], 'b': [2, 6]}],
        'note': 'Placeholder geometry only; solution offset (2,-1) rotation 0 aligns b onto a.'}
    with open(os.path.join(OUT, 'puzzle', 'plan_placeholder.json'), 'w', encoding='utf-8') as f:
        json.dump(meta, f, indent=1)


# ============================================================================ pictures (1:1)
def portrait_placeholder():
    """Neutral bust silhouette used when assets/characters/<id>/portrait.png is missing."""
    S = 112
    l = L(S, S)
    l.vgrad(0, 0, S, S, [c('#0B1C24'), c('#0A1219'), c('#06151D'), c('#05090F')])
    yy, xx = np.mgrid[0:S, 0:S]
    d = np.sqrt(((xx - 70) / 60.0) ** 2 + ((yy - 40) / 55.0) ** 2)
    thr = pg.bayer(S, S)
    l.c[(d < 1.0) & (thr < (1 - d) * 0.35)] = c('#13252B')
    sil = c('#03070A')
    l.ellipse(56, 45, 16.5, 20.0, sil)
    l.rect(49, 58, 15, 16, sil)
    l.poly([(6, 112), (10, 92), (24, 82), (44, 74), (68, 74), (88, 82), (102, 92), (106, 112)], sil)
    # coat collar
    l.poly([(44, 74), (56, 92), (49, 96), (38, 78)], c('#0A1219'))
    l.poly([(68, 74), (56, 92), (63, 96), (74, 78)], c('#0A1219'))
    # rim light (key from the right)
    a = np.all(l.c == sil, axis=-1)
    p = np.pad(a, 1)
    edge = a & ~p[1:-1, 2:]
    l.c[edge & (yy < 104)] = c('#36534D')
    edge2 = a & ~p[1:-1, 3:] if False else None
    return save(l, 'portrait_placeholder', group='.', scale=1, note='112x112 placeholder, shown x3')


def menu_background():
    """640x360 title backdrop: dithered night gradient, faint skyline of both empires."""
    W, H = 640, 360
    l = L(W, H)
    pg.sky(l, [c('#04090D'), c('#05090F'), c('#06151D'), c('#0A1219'), c('#0E1A20'), c('#13252B')],
           horizon_glow=(470, 268, 260, 70, [c('#14272B'), c('#1B3033')]))
    rng = np.random.default_rng(1964)
    far = L(W, H)
    farc = c('#0E1A20')
    # monumental dome (fictional Grosse Halle) far right in the haze -- small, distant, no insignia
    dx, base = 516, 262
    far.rect(dx - 46, base - 18, 92, 18, farc)
    far.ellipse(dx, base - 18, 33, 29, farc)
    far.rect(dx - 38, base - 20, 76, 2, farc)
    far.rect(dx - 3, base - 54, 6, 8, farc)
    far.rect(dx - 1, base - 58, 2, 4, farc)
    for k in range(-42, 44, 5):
        far.rect(dx + k, base - 16, 1, 15, c('#10202A'))
    # distant slab blocks along the horizon (very hazy)
    for (bx, bw, bh) in [(236, 26, 20), (266, 18, 26), (300, 34, 16), (402, 22, 22), (436, 30, 14),
                         (574, 28, 24), (606, 34, 18)]:
        far.rect(bx, base - bh, bw, bh + 8, farc)
    pg.atmos(far, c('#13252B'), 0.32)
    # Karsk mid skyline (left -> centre-right): slab blocks, silos, chimneys, crane
    mid = L(W, H)
    midc = c('#0A1219')
    x = -10
    while x < 470:
        kind = rng.choice(['slab', 'slab', 'silo', 'low', 'chimney'])
        if kind == 'slab':
            bw = int(rng.integers(34, 60)); bh = int(rng.integers(40, 78))
            if x < 210:
                bh = int(bh * 0.6)
            mid.rect(x, base + 8 - bh, bw, bh, midc)
            # unlit window grid + a rare warm window
            for wy in range(base + 12 - bh, base + 2, 7):
                for wx in range(x + 3, x + bw - 3, 6):
                    r = rng.random()
                    if r < 0.010 and x > 240:
                        mid.rect(wx, wy, 2, 3, c('#9A5A2F'), em=c('#9A5A2F'))
                    elif r < 0.42:
                        mid.rect(wx, wy, 2, 3, c('#0E1A20'))
            x += bw + int(rng.integers(2, 10))
        elif kind == 'silo':
            n = int(rng.integers(3, 5))
            for i in range(n):
                sx = x + i * 11
                sh = int(rng.integers(52, 70)) if x > 200 else 40
                mid.rect(sx, base + 8 - sh, 10, sh, midc)
                mid.ellipse(sx + 5, base + 8 - sh, 5, 3, midc)
                mid.rect(sx + 2, base + 10 - sh, 1, sh - 4, c('#0E1A20'))
            mid.rect(x - 2, base + 8 - 84 if x > 200 else base - 46, 6, 90 if x > 200 else 54, midc)
            x += n * 11 + int(rng.integers(6, 14))
        elif kind == 'low':
            bw = int(rng.integers(40, 70))
            mid.rect(x, base - 10, bw, 18, midc)
            for k in range(x, x + bw - 8, 8):
                mid.poly([(k, base - 10), (k + 8, base - 10), (k + 8, base - 16)], midc)
            x += bw + 4
        else:
            ch = int(rng.integers(70, 112)) if x > 220 else 60
            mid.rect(x, base + 8 - ch, 4, ch, midc)
            mid.rect(x - 1, base + 8 - ch, 6, 2, midc)
            pg.smoke_ribbon(mid, [(x + 2, base + 4 - ch), (x + 22, base - ch - 12), (x + 64, base - ch - 14),
                                  (x + 118, base - ch - 24)], 2, 8,
                            [c('#0A1219'), c('#0C171D'), c('#0E1A20'), c('#10202A')], seed=int(x) + 7, gaps=0.3)
            x += 14
    # lattice crane
    pg.truss(mid, 300, base - 92, 380, base - 92, 3, midc, step=5)
    mid.rect(318, base - 92, 3, 100, midc)
    pg.wire(mid, 372, base - 89, 372, base - 40, 0, midc)
    pg.atmos(mid, c('#13252B'), 0.08)
    # near ground: snow-covered rail yard, one amber signal lamp = the warm story beat
    near = L(W, H)
    gy = base + 8
    near.rect(0, gy, W, H - gy, c('#05090F'))
    near.vgrad(0, gy, W, 26, [c('#0E1A20'), c('#0A1219'), c('#06151D'), c('#05090F')])
    for k, ry in enumerate([gy + 9, gy + 19, gy + 33, gy + 51]):
        near.rect(0, ry, W, 1, c('#1B3033' if k < 2 else '#13252B'))
        near.rect(0, ry + 1, W, 1, c('#05090F'))
        for tx in range(int(rng.integers(0, 9)), W, 9 + k * 3):
            near.rect(tx, ry + 2, 3 + k, 1, c('#0A1219'))
    # signal mast
    mx = 548
    near.rect(mx, gy - 64, 2, 64 + 12, c('#03070A'))
    near.rect(mx - 6, gy - 66, 14, 10, c('#03070A'))
    near.rect(mx - 4, gy - 64, 3, 3, c('#F0C487'), em=c('#F0C487'))
    near.px(mx - 3, gy - 63, c('#FBE3AE'))
    near.rect(mx + 3, gy - 64, 3, 3, c('#0A1219'))
    # lamp glow in the haze: warm-grey ordered-dither rings (no saturated blob), plus rail reflections
    yy, xx = np.mgrid[0:H, 0:W]
    lx, ly = mx - 3, gy - 63
    d = np.sqrt((xx - lx) ** 2 + ((yy - ly) * 1.15) ** 2)
    thr = pg.bayer(W, H)
    free = near.c[..., 3] == 0
    l2 = L(W, H)
    outer = (d < 20) & (thr < np.clip((20 - d) / 20, 0, 1) * 0.55) & free
    l2.c[outer] = c('#262B29')
    inner = (d < 9) & (thr < np.clip((9 - d) / 9, 0, 1) * 0.9) & free
    l2.c[inner] = c('#4A463A')
    for ry in (gy + 9, gy + 19):
        for k, rx in enumerate(range(lx - 10, lx + 12, 3)):
            if (k * 7) % 3 != 0:
                near.px(rx, ry, c('#6E3F22') if abs(rx - lx) > 4 else c('#9A5A2F'))
    # foreground silhouettes: fence posts and a dead tree at left edge (framing device)
    fg = L(W, H)
    for px_ in range(4, 200, 28):
        fg.rect(px_, gy + 44 - (px_ % 3), 2, 30, c('#020507'))
        fg.px(px_, gy + 43 - (px_ % 3), c('#13252B'))          # snow cap on the post
    fg.rect(0, gy + 50, 200, 1, c('#020507'))
    fg.rect(0, gy + 58, 200, 1, c('#020507'))
    tree = [(18, H), (22, 250), (26, 200), (24, 160)]
    for (x0, y0), (x1, y1) in zip(tree[:-1], tree[1:]):
        for o in range(-2, 3):
            fg.line(x0 + o, y0, x1 + o // 2, y1, c('#020507'))
    for (bx, by, ex, ey) in [(24, 175, 60, 140), (25, 205, 2, 172), (40, 160, 52, 126), (24, 230, 48, 214),
                             (50, 146, 74, 132), (12, 186, 0, 180)]:
        fg.line(bx, by, ex, ey, c('#020507'))
        fg.line(bx, by + 1, ex, ey + 1, c('#020507'))
    pg.snow_caps(mid, [c('#13252B'), c('#1B3033')], depth=1, seed=3, coverage=0.7)
    pg.snow_caps(far, [c('#14272B')], depth=1, seed=4, coverage=0.5)
    out = L(W, H)
    out.c[:] = l.c
    for layer in (far, mid, l2, near, fg):
        out.blit(layer, 0, 0)
    return save(out, 'menu_bg', group='menu', scale=1, note='640x360 backdrop, shown x3')


def mock_world():
    """PREVIEW ONLY (assets/ui/_preview, not shipped): mid-detail stand-in game frame so the
    HUD/dialogue can be judged against busy pixel art. Not a game asset."""
    W, H = 640, 360
    l = L(W, H)
    pg.sky(l, [hx(x) for x in pg.PALETTES['karsk']['sky'][::-1]][:4] + [hx('#AFC1AA')],
           horizon_glow=(420, 180, 300, 90, [hx('#C7D3BA'), hx('#DCE2C8')]))
    pg.clouds(l, 20, 120, [hx(x) for x in pg.PALETTES['karsk']['sky']], seed=4, count=6)
    b = L(W, H)
    rng = np.random.default_rng(7)
    x = 0
    while x < W:
        bw = int(rng.integers(40, 90)); bh = int(rng.integers(70, 150))
        b.rect(x, 250 - bh, bw, bh, hx('#36534D'))
        b.rect(x, 250 - bh, 1, bh, hx('#4A675C'))
        pg.window_grid(b, x + 4, 256 - bh, (bw - 6) // 8, bh // 12, 5, 7, 3, 5, hx('#26403F'), hx('#122126'),
                       hx('#4A675C'), lit=hx('#F0C487'), lit_prob=0.05, seed=int(x))
        x += bw + int(rng.integers(4, 20))
    pg.atmos(b, hx('#98AD9A'), 0.35)
    g = L(W, H)
    g.vgrad(0, 250, W, 110, [hx('#53614F'), hx('#3E4E3D'), hx('#26403F'), hx('#1B3033')])
    for ry in (276, 300, 330):
        g.rect(0, ry, W, 2, hx('#7F8275')); g.rect(0, ry + 2, W, 1, hx('#2A2D2C'))
    out = L(W, H)
    out.c[:] = l.c
    out.blit(b, 0, 0)
    out.blit(g, 0, 0)
    # two figures for scale
    for fx, col in [(300, hx('#26403F')), (352, hx('#4A2A22'))]:
        out.rect(fx, 268, 8, 30, col); out.ellipse(fx + 4, 264, 3, 4, hx('#9A9B8B'))
    os.makedirs(PREVIEW, exist_ok=True)
    out.image().save(os.path.join(PREVIEW, 'mock_world.png'))


def preview_frame(cam_x=300):
    """PREVIEW ONLY: a 640x360 frame composed from the environment team's karsk_railyard layers + two idle
    character frames (plain alpha-over, no lighting) so tests/visual/UIPreview can judge UI legibility against
    real game art. Written to assets/ui/_preview (gdignored); skipped when those assets do not exist."""
    env = os.path.join(ROOT, 'assets', 'environments', 'karsk_railyard')
    path = os.path.join(env, 'scene.json')
    if not os.path.exists(path):
        return
    d = json.load(open(path, encoding='utf-8'))
    out = Image.new('RGBA', (640, 360), (0, 0, 0, 255))

    def paste(img, x, y):
        out.paste(img, (int(x), int(y)), img)

    items = [(l['z'], 'L', l) for l in d['layers'] if l['z'] < 60]
    items += [(p_.get('base_y', 0) / 1000.0, 'P', p_) for p_ in d.get('props', [])]
    for _, kind, it in sorted(items, key=lambda t: t[0]):
        img = Image.open(os.path.join(env, it['file'])).convert('RGBA')
        if kind == 'L':
            paste(img, it['pos'][0] - cam_x * it['parallax'][0], it['pos'][1])
        else:
            paste(img, it['pos'][0] - cam_x, it['pos'][1])
    hx_ = d.get('hotspots', {}).get('irina', [506, 258])[0]
    for cid, wx, base, flip in [('irina', hx_, 300, True), ('alexei', hx_ - 46, 302, False)]:
        sj = os.path.join(ROOT, 'assets', 'characters', cid, 'sheet.json')
        if not os.path.exists(sj):
            continue
        meta = json.load(open(sj, encoding='utf-8'))
        sheet = Image.open(os.path.join(ROOT, 'assets', 'characters', cid, 'sheet.png')).convert('RGBA')
        cw, ch = meta['cell']
        row = meta['anims']['idle_side']['row']
        fr = sheet.crop((0, row * ch, cw, row * ch + ch))
        if flip:
            fr = fr.transpose(Image.FLIP_LEFT_RIGHT)
        paste(fr, wx - cam_x - meta['origin'][0], base - meta['origin'][1])
    for l in d['layers']:
        if l['z'] >= 60:
            img = Image.open(os.path.join(env, l['file'])).convert('RGBA')
            paste(img, l['pos'][0] - cam_x * l['parallax'][0], l['pos'][1])
    os.makedirs(PREVIEW, exist_ok=True)
    out.save(os.path.join(PREVIEW, 'karsk_frame.png'))
    out.resize((1920, 1080), Image.NEAREST).save(os.path.join(PREVIEW, 'karsk_frame_x3.png'))


def contact_sheet():
    """PREVIEW: all x3 sprites on navy + paper swatches so pixel clusters can be judged."""
    files = [m['path'] for m in MANIFEST if m['scale'] == 3]
    ims = [Image.open(os.path.join(ROOT, p)) for p in files]
    pad = 18
    W = 1900
    x = y = pad
    row_h = 0
    pos = []
    for im in ims:
        if x + im.width + pad > W:
            x = pad; y += row_h + pad; row_h = 0
        pos.append((x, y)); x += im.width + pad; row_h = max(row_h, im.height)
    H = y + row_h + pad
    sheet = Image.new('RGBA', (W, H * 2 + pad), (60, 66, 70, 255))
    top = Image.new('RGBA', (W, H), hx('#2A3A40').tolist() and tuple(int(v) for v in hx('#2A3A40')))
    bot = Image.new('RGBA', (W, H), tuple(int(v) for v in hx('#CEC6AA')))
    for im, p in zip(ims, pos):
        top.alpha_composite(im, p); bot.alpha_composite(im, p)
    sheet.paste(top, (0, 0)); sheet.paste(bot, (0, H + pad))
    os.makedirs(PREVIEW, exist_ok=True)
    sheet.save(os.path.join(PREVIEW, 'ui_kit_sheet.png'))


def main():
    os.makedirs(OUT, exist_ok=True)
    for d in (SRC, PREVIEW):
        os.makedirs(d, exist_ok=True)
        open(os.path.join(d, '.gdignore'), 'a').close()
    frame_panel(False); frame_panel(True); frame_panel_solid(); frame_band(); frame_paper_row()
    frame_plate(); frame_prompt(); prompt_tail(); frame_keycap()
    frame_paper(); frame_paper_dark(); frame_slot(); frame_portrait()
    for s in ('normal', 'hover', 'pressed', 'disabled', 'focus'):
        frame_button(s)
    for s in ('focus', 'pressed'):
        frame_menu_band(s)
    for s in ('normal', 'hover', 'pressed', 'focus'):
        frame_tab(s, paper=False); frame_tab(s, paper=True)
    frame_scroll(); slider_parts(); checkbox_icons(); ornaments(); icons()
    stamp('stamp_evidence', 84, 26, -3.0, seed=11)
    stamp('stamp_record', 70, 24, 2.5, seed=12, col=RED)
    for s in ('triangle', 'square', 'circle'):
        symbol_card(s)
    slot_frame(); signal_board(); reg_marks(); plan_placeholders(16)
    portrait_placeholder(); menu_background(); mock_world(); preview_frame()
    contact_sheet()
    with open(os.path.join(SRC, 'manifest.json'), 'w', encoding='utf-8') as f:
        json.dump(MANIFEST, f, indent=1)
    print('wrote %d textures' % len(MANIFEST))


if __name__ == '__main__':
    main()
