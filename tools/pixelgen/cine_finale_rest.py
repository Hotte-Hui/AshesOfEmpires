"""cine_finale_rest -- wide shots, window inserts, snow veil and the border map of the X1 finale (trans-finale).

b_wide    Konrad's drafting room at night (side view): east window with the floodlit dome, drafting table
          with the architect's lamp, a pendulum clock; Konrad = runtime sprite (assets/characters/konrad)
k_wide    the Karsk signal box (side view, mirrored): west window over the yard, lever frame, block
          instruments, desk with the green lamp, stove; Alexei = runtime sprite facing west
b_window / k_window   inserts: snow against the glass, the city / the yard beyond (same exterior paintings)
veil      the snow thickens into a dithered pale veil that carries the cut from Berlin to Karsk
map       one schematic border map under both desk lamps; the red C-17 route draws itself from Karsk west to
          Berlin; the lamps go out one after the other; the red line is the last light
"""
from __future__ import annotations

import math
import os

import numpy as np

import cine_finale_kit as kit
import cine_finale_berlin as b
import cine_finale_karsk as k
import cine_finale_karsk_anim as ka
import cine_finale_wide as wide
import pg

WIDE_EXTRA = {}

BR, KR, MR = kit.BR, kit.KR, kit.MR
W, H = b.W, b.H
V = b.V


def save(arr, rel_name, out):
    kit.save_rgba(arr, os.path.join(out, rel_name))
    return rel_name


# ------------------------------------------------------------------------------------------- window inserts
def window_insert(ext, off, ramp_frame, frost_cols, refl_col, warm_dot, seed, mull=(330, 150)):
    """Full-frame window: heavy casing + cross mullion; frost creeping from the corners; flakes stuck to
    the glass; a warm reflection of the desk lamp.  Returns (frame_rgba, glass_rgba, ext_layer)."""
    cv = kit.Canvas(W, H)
    xx, yy = cv.grid()
    bay = kit.bayer_full(W, H)
    x0, y0, x1, y1 = V(60, 20)[0], V(0, 20)[1], V(600, 0)[0], V(0, 330)[1]
    outer = np.ones((H, W), bool)
    panes = (xx >= x0) & (xx < x1) & (yy >= y0) & (yy < y1)
    mx, my = V(*mull)
    panes &= ~((xx >= mx - 4) & (xx < mx + 4))
    panes &= ~((yy >= my - 4) & (yy < my + 4))
    casing = outer & ~panes
    # casing lit faintly from inside (lamp behind the camera, warm on the lower edges)
    tone = 0.10 + 0.18 * np.clip((yy - y0) / (y1 - y0), 0, 1) + 0.12 * (kit.outline_of(~panes) & casing)
    cv.paint(casing, np.clip(tone, 0, 1), ramp_frame)
    # bevels on the mullions
    edge = kit.dilate(panes, 1) & casing
    cv.paint(edge & ((xx < mx) | (yy < my)), np.full((H, W), 0.42, np.float32), ramp_frame)
    cv.c[panes] = 0
    glass = np.zeros((H, W, 4), np.uint8)
    d = np.minimum.reduce([xx - x0, x1 - xx, yy - y0, y1 - yy, np.abs(xx - mx) - 4, np.abs(yy - my) - 4])
    nz = pg.value_noise(W, H, 9, kit.seed_of(seed + 'frost'), octaves=3)
    fr = panes & (d < 10) & (bay < np.clip(1.0 - d / 10.0 + (nz - 0.5) * 0.5, 0, 1) * 0.42)
    glass[fr] = frost_cols[0]
    glass[fr & (d < 5) & (nz > 0.5)] = frost_cols[1]
    rng = np.random.default_rng(kit.seed_of(seed + 'flakes'))
    for _ in range(70):
        px_ = int(rng.uniform(x0 + 4, x1 - 4))
        py_ = int(rng.uniform(y0 + 4, y1 - 4))
        if panes[py_, px_]:
            glass[py_, px_] = frost_cols[1]
            if rng.random() < 0.3 and panes[py_, px_ + 1]:
                glass[py_, px_ + 1] = frost_cols[0]
    # melt drop tracks on the lower panes
    for _ in range(6):
        px_ = int(rng.uniform(x0 + 10, x1 - 10))
        py0 = int(rng.uniform(my + 20, y1 - 60))
        for yk in range(py0, py0 + int(rng.uniform(14, 40))):
            if panes[yk, px_]:
                glass[yk, px_] = refl_col
    lx, ly = warm_dot
    lr = panes & ((((xx - lx) ** 2) / 30 + ((yy - ly) ** 2) / 9) < 1)
    glass[lr] = pg.hx('#F4BA81')
    glass[lr & ((((xx - lx) ** 2) / 8 + ((yy - ly) ** 2) / 2) < 1)] = pg.hx('#FCE9C8')
    glass[..., 3] = np.where(glass[..., :3].any(-1), 255, 0)
    return cv.c, glass, b.ext_layer(ext, off)


def build_windows(ext_b, ext_k, T, out):
    sets = {}
    frame_b, glass_b, extl_b = window_insert(ext_b, (V(320, 0)[0] - 360, V(0, 190)[1] - 240), BR['desk'],
                                             [pg.hx('#57494D'), pg.hx('#8F8A92')], pg.hx('#443B43'), V(520, 250), 'bw')
    frame_k, glass_k, extl_k = window_insert(ext_k, (V(330, 0)[0] - 360, V(0, 190)[1] - 192), KR['wall'],
                                             [pg.hx('#4A675C'), pg.hx('#A3B1AD')], pg.hx('#26403F'), V(120, 250), 'kw',
                                             mull=(310, 150))
    for sid, fr, gl, ex, cols, wind, seed in (('b_window', frame_b, glass_b, extl_b, ['#8F8A92', '#ECE6E0'], -6, 'bw_snow'),
                                              ('k_window', frame_k, glass_k, extl_k, ['#7E8E8C', '#F1F4EC'], 6, 'kw_snow')):
        nodes = [
            {'id': 'ext', 'type': 'sprite', 'file': save(ex, sid + '/ext.png', out), 'z': 0, 'parallax': 0.5},
            {'id': 'snow_far', 'type': 'snow', 'rect': [-20, -20, W + 40, H + 40], 'count': 260, 'seed': kit.seed_of(seed + 'f'),
             'speed': [8, 14], 'sway': 2, 'wind': wind * 0.6, 'near': 0.0, 'colors': [cols[0], cols[0]], 'z': 1, 'parallax': 0.6},
            {'id': 'snow_near', 'type': 'snow', 'rect': [-20, -20, W + 40, H + 40], 'count': 110, 'seed': kit.seed_of(seed + 'n'),
             'speed': [22, 34], 'sway': 4, 'wind': wind, 'near': 1.0, 'colors': [cols[1], cols[1]], 'z': 2, 'parallax': 0.9},
            {'id': 'frame', 'type': 'sprite', 'file': save(fr, sid + '/frame.png', out), 'z': 3},
            {'id': 'glass', 'type': 'sprite', 'file': save(gl, sid + '/glass.png', out), 'z': 4},
        ]
        nodes[1:1] = window_life(sid, out, T)
        sets[sid] = {'nodes': nodes, 'flicker': {}}
    # veil: dense snow + pale dithered fill (its shot fades in and out)
    veil_nodes = [
        {'id': 'fill', 'type': 'rect', 'rect': [-40, -40, W + 80, H + 80], 'color': '#9AA6A5', 'z': 0},
        {'id': 'snow', 'type': 'snow', 'rect': [-20, -20, W + 40, H + 40], 'count': 520, 'seed': kit.seed_of('veil'),
         'speed': [26, 40], 'sway': 5, 'wind': 0, 'near': 0.6, 'colors': ['#C4CFC8', '#F1F4EC'], 'z': 1},
    ]
    sets['veil'] = {'nodes': veil_nodes, 'flicker': {}}
    return sets


# ------------------------------------------------------------------------------------------- wide shots
def floor_band(cv, y0, ramp, lamp, seed, plank=7):
    xx, yy = cv.grid()
    m = yy >= y0
    nz = pg.value_noise(W, H, 16, kit.seed_of(seed), octaves=2)
    rel = yy - y0
    seam = (np.floor(rel) % plank) == 0
    tone = 0.08 + 0.7 * lamp.pool(xx, yy) + (nz - 0.5) * 0.05 - 0.06 * seam
    cv.paint(m, np.clip(tone, 0, 1), ramp)


def b_wide(ext_b):
    """Konrad's drafting room at night, side view at the 46 px human scale.
    Returns (base, glass, ext_layer, lamp_rgba, lamp_head, feet)."""
    cv = kit.Canvas(W, H, 'b_wide')
    xx, yy = cv.grid()
    bay = kit.bayer_full(W, H)
    floor_y = V(0, 292)[1]
    feet = (V(330, 0)[0], floor_y + 1)
    lamp_head = V(236, 228)                  # architect's lamp at the left end of his desk (as in the close-up)
    L = kit.Lamp(lamp_head[0] + 14, floor_y, 64, 70, depth=0.35, power=1.0)
    halo = np.clip(1.0 - np.sqrt((xx - lamp_head[0]) ** 2 + ((yy - lamp_head[1]) * 1.15) ** 2) / 150.0, 0, 1) ** 1.6
    nz = pg.value_noise(W, H, 40, kit.seed_of('bw_wall'), octaves=3)
    wall_t = 0.24 + 0.46 * halo + (nz - 0.5) * 0.05 - 0.04 * ((np.floor(xx) % 9) == 0)
    cv.paint(yy < floor_y, np.clip(wall_t, 0, 1), BR['wall'])
    # wainscot panels on the lower wall + picture rail
    wy = V(0, 240)[1]
    wain = (yy >= wy) & (yy < floor_y)
    cv.paint(wain, np.clip(wall_t - 0.04, 0, 1), BR['desk'][:7])
    for px_ in range(V(10, 0)[0], W, 38):
        cv.rect(px_, wy + 6, 30, 1, BR['desk'][1])
        cv.rect(px_, wy + 6, 1, floor_y - wy - 14, BR['desk'][1])
        cv.rect(px_ + 1, wy + 7, 29, 1, BR['desk'][4])
    cv.rect(0, wy, W, 2, BR['desk'][4])
    cv.rect(0, V(0, 92)[1], W, 2, BR['wall'][1])
    # floor: planks, warm pool under the lamp
    floor_band(cv, floor_y, BR['desk'], L, 'bw_floor', plank=6)
    # big east window (right): Great Hall beyond
    wx0, wx1, wy0, wy1 = V(436, 0)[0], V(604, 0)[0], V(0, 70)[1], V(0, 236)[1]
    win = (xx >= wx0) & (xx < wx1) & (yy >= wy0) & (yy < wy1)
    panes = (xx >= wx0 + 6) & (xx < wx1 - 6) & (yy >= wy0 + 6) & (yy < wy1 - 6)
    mid = (wx0 + wx1) // 2
    panes &= ~((xx >= mid - 2) & (xx < mid + 2))
    for ty in (wy0 + 58, wy0 + 112):
        panes &= ~((yy >= ty - 2) & (yy < ty + 2))
    cas = win & ~panes
    cv.paint(cas, np.clip(0.20 + 0.35 * halo + 0.1 * (xx < wx0 + 4), 0, 1), BR['desk'])
    cv.c[panes] = 0
    sill = (xx >= wx0 - 8) & (xx < wx1 + 8) & (yy >= wy1) & (yy < wy1 + 5)
    cv.paint(sill, np.clip(0.30 + 0.3 * halo, 0, 1), BR['desk'])
    cv.rect(wx0 - 8, wy1, wx1 - wx0 + 16, 1, BR['desk'][7])
    rad = (xx >= wx0 + 10) & (xx < wx1 - 10) & (yy >= wy1 + 16) & (yy < floor_y - 6)
    cv.paint(rad, np.clip(0.16 + 0.2 * halo + 0.08 * ((np.floor(xx) % 4) == 0), 0, 1), BR['metal'])
    # curtain bunched at the left of the window (heavy, dark red-brown)
    cur = kit.poly_mask_full(W, H, [(wx0 - 18, wy0 - 10), (wx0 + 2, wy0 - 10), (wx0 + 6, wy1 + 30), (wx0 - 24, wy1 + 30)])
    ct = 0.12 + 0.30 * halo + 0.10 * (np.sin(xx * 0.9) > 0.5)
    cv.paint(cur, np.clip(ct, 0, 1), BR['lining'])
    cv.rect(wx0 - 30, wy0 - 12, wx1 - wx0 + 50, 2, BR['brass'][2])
    # cold window light on the floor and on the radiator wall
    b.cold_patch(cv, [(wx0 + 6, floor_y), (wx1 - 6, floor_y), (wx1 - 60, H), (wx0 - 110, H)], gain=1.3, lift=0.03)
    # left: tall plan cabinet with rolled plans, wall clock, framed rendering of the hall
    cab = (xx >= V(36, 0)[0]) & (xx < V(116, 0)[0]) & (yy >= V(0, 150)[1]) & (yy < floor_y)
    cv.paint(cab, np.clip(0.14 + 0.2 * halo + 0.06 * ((np.floor(yy) % 14) == 0), 0, 1), BR['desk'])
    for kk in range(9):
        tx = V(40 + kk * 8, 0)[0]
        ty = V(0, 134)[1] + (kk * 7) % 5
        cv.rect(tx, ty, 6, V(0, 150)[1] - ty, BR['paper'][2 + (kk % 3)])
        cv.px(tx + 2, ty, BR['paper'][6])
    for dy_ in range(0, 130, 14):
        cv.rect(V(44, 0)[0], V(0, 160)[1] + dy_, 64, 1, BR['desk'][1])
        cv.rect(V(70, 0)[0], V(0, 164)[1] + dy_, 12, 2, BR['brass'][3])
    cx, cy = V(170, 128)
    case = (np.abs(xx - cx) < 11) & (yy >= cy - 14) & (yy < cy + 44)
    cv.paint(case, np.clip(0.16 + 0.25 * halo + 0.1 * (np.abs(xx - cx) < 9), 0, 1), BR['desk'])
    face = kit.ellipse_full(W, H, cx, cy - 2, 8, 8)
    cv.paint(face, np.clip(0.45 + 0.3 * halo, 0, 1), BR['paper'])
    for kk in range(12):
        a = kk / 12 * 2 * math.pi
        cv.px(cx + math.sin(a) * 6, cy - 2 - math.cos(a) * 6, BR['ink'][0])
    cv.line(cx, cy - 2, cx, cy - 7, BR['ink'][0])
    am = 47 / 60 * 2 * math.pi
    cv.line(cx, cy - 2, cx + math.sin(am) * 6, cy - 2 - math.cos(am) * 6, BR['ink'][0])
    pend = (np.abs(xx - cx) < 7) & (yy >= cy + 12) & (yy < cy + 40)
    cv.paint(pend, np.full((H, W), 0.08, np.float32), BR['desk'])
    cv.line(cx, cy + 12, cx, cy + 34, BR['brass'][4])
    cv.ellipse(cx, cy + 35, 3, 3, BR['brass'][5])
    fr = (xx >= V(222, 0)[0]) & (xx < V(290, 0)[0]) & (yy >= V(0, 120)[1]) & (yy < V(0, 170)[1])
    cv.paint(fr, np.clip(0.14 + 0.3 * halo, 0, 1), BR['desk'])
    inner = (xx >= V(226, 0)[0]) & (xx < V(286, 0)[0]) & (yy >= V(0, 124)[1]) & (yy < V(0, 166)[1])
    cv.paint(inner, np.clip(0.25 + 0.45 * halo, 0, 1), BR['paper'])
    pcx, pby = V(256, 160)
    for kk in range(0, 30):
        a = math.pi * kk / 29.0
        cv.px(pcx + math.cos(a) * 16, pby - 10 - math.sin(a) * 14, BR['ink'][1])
    cv.line(pcx - 22, pby - 9, pcx + 22, pby - 9, BR['ink'][1])
    for kk in range(-20, 22, 4):
        cv.line(pcx + kk, pby - 8, pcx + kk, pby - 2, BR['ink'][1])
    # hanging ceiling lamp (off), dark silhouette
    cv.rect(V(300, 0)[0], 0, 1, V(0, 66)[1], BR['black'][2])
    shade = kit.poly_mask_full(W, H, [V(290, 66), V(312, 66), V(318, 78), V(284, 78)])
    cv.paint(shade, np.full((H, W), 0.25, np.float32), BR['black'])
    # his desk against the wall under the rendering (the close-up looks over his shoulder at it)
    wide.b_wide_desk(cv, L, halo, floor_y)
    # foreground frame: dark door jamb at the left edge
    jamb = (xx < V(14, 0)[0]) | ((xx < V(22, 0)[0]) & (yy < V(0, 40)[1]))
    cv.paint(jamb, np.full((H, W), 0.04, np.float32), BR['void'])
    wide.clock_case_cover(cv, cx, cy)
    tip = wide.b_wide_enrich(cv, L, halo, floor_y)
    WIDE_EXTRA['b'] = {'pendulum': (cx, cy + 12), 'tip': tip, 'win': (wx0, wy0, wx1, wy1),
                       'ext_off': (V(520, 0)[0] - 360, V(0, 196)[1] - 240)}
    glass = np.zeros((H, W, 4), np.uint8)
    dd = np.minimum.reduce([xx - wx0, wx1 - xx, yy - wy0, wy1 - yy])
    frm = panes & (dd < 12) & (bay < np.clip(1.0 - dd / 12.0, 0, 1) * 0.5)
    glass[frm] = pg.hx('#57494D')
    lr = panes & ((((xx - lamp_head[0] - 262) ** 2) / 9 + ((yy - lamp_head[1] + 22) ** 2) / 4) < 1)
    glass[lr] = pg.hx('#F4BA81')
    glass[..., 3] = np.where(glass[..., :3].any(-1), 255, 0)
    extl = b.ext_layer(ext_b, (V(520, 0)[0] - 360, V(0, 196)[1] - 240))
    lamp_rgba = small_lamp_b(lamp_head)
    return cv.c, glass, extl, lamp_rgba, lamp_head, feet


def small_lamp_b(head):
    """Architect's lamp standing at the left end of Konrad's desk: weighted foot, two-part arm, the shade
    aimed down-right at the typewriter, a faint cone of dust in the light."""
    cv = kit.Canvas(W, H)
    hx, hy = head
    top = V(0, 292)[1] - 20
    foot = (hx - 4, top - 2)
    cv.rect(foot[0] - 4, top - 3, 9, 2, BR['black'][3])
    cv.px(foot[0] - 3, top - 3, BR['black'][6])
    elbow = (hx - 12, hy + 16)
    cv.line(foot[0], top - 3, elbow[0], elbow[1], BR['black'][4])
    cv.line(elbow[0], elbow[1], hx - 3, hy - 3, BR['black'][4])
    cv.line(elbow[0] + 1, elbow[1], hx - 2, hy - 3, BR['black'][2])
    cv.px(elbow[0], elbow[1], BR['metal'][6])
    sh = kit.poly_mask_full(W, H, [(hx - 4, hy - 6), (hx + 3, hy - 5), (hx + 8, hy + 4), (hx - 3, hy + 3)])
    cv.paint(sh, np.full((H, W), 0.55, np.float32), BR['black'])
    for dx_ in (3, 4, 5):
        cv.px(hx + dx_, hy + 3, pg.hx('#FFE3AA') if dx_ < 5 else pg.hx('#F2C27E'))
    xx, yy = cv.grid()
    bay = kit.bayer_full(W, H)
    cone = kit.poly_mask_full(W, H, [(hx - 2, hy + 4), (hx + 8, hy + 4), (hx + 52, top - 2), (hx + 8, top - 2)])
    ct = np.clip(1.0 - np.sqrt((xx - hx) ** 2 + (yy - hy) ** 2) / 56.0, 0, 1)
    cv.c[cone & (bay < ct * 0.16)] = pg.hx('#9A5A2F')
    return cv.c


def k_wide(ext_k):
    """Karsk signal box at night, mirrored: west window + lever frame left, Alexei at the desk facing west."""
    cv = kit.Canvas(W, H, 'k_wide')
    xx, yy = cv.grid()
    bay = kit.bayer_full(W, H)
    floor_y = V(0, 292)[1]
    feet = (V(312, 0)[0], floor_y + 1)
    lamp_head = V(262, 232)
    L = kit.Lamp(lamp_head[0] + 4, floor_y, 64, 70, depth=0.35, power=1.0)
    halo = np.clip(1.0 - np.sqrt((xx - lamp_head[0]) ** 2 + ((yy - lamp_head[1]) * 1.15) ** 2) / 150.0, 0, 1) ** 1.6
    nz = pg.value_noise(W, H, 40, kit.seed_of('kw_wall'), octaves=3)
    wall_t = 0.24 + 0.46 * halo + (nz - 0.5) * 0.05
    cv.paint(yy < floor_y, np.clip(wall_t, 0, 1), KR['wall'])
    dado = (yy >= V(0, 212)[1]) & (yy < floor_y)
    cv.paint(dado, np.clip(wall_t - 0.06, 0, 1), KR['green'])
    cv.rect(0, V(0, 212)[1], W, 1, KR['green'][5])
    floor_band(cv, floor_y, KR['desk'], L, 'kw_floor', plank=6)
    # panorama window (left), lever frame + block shelf below it
    wx0, wx1, wy0, wy1 = V(30, 0)[0], V(230, 0)[0], V(0, 62)[1], V(0, 176)[1]
    win = (xx >= wx0) & (xx < wx1) & (yy >= wy0) & (yy < wy1)
    panes = (xx >= wx0 + 5) & (xx < wx1 - 5) & (yy >= wy0 + 5) & (yy < wy1 - 5)
    for mx_ in (wx0 + 66, wx0 + 133):
        panes &= ~((xx >= mx_ - 2) & (xx < mx_ + 2))
    panes &= ~((yy >= wy0 + 52) & (yy < wy0 + 56))
    cas = win & ~panes
    cv.paint(cas, np.clip(0.22 + 0.3 * halo, 0, 1), KR['green'])
    cv.c[panes] = 0
    cv.rect(wx0 - 6, wy1, wx1 - wx0 + 12, 5, KR['desk'][4])
    cv.rect(wx0 - 6, wy1, wx1 - wx0 + 12, 1, KR['desk'][6])
    for kk in range(4):
        bx = wx0 + 6 + kk * 50
        by = wy1 + 9
        box = (xx >= bx) & (xx < bx + 30) & (yy >= by) & (yy < by + 20)
        cv.paint(box, np.clip(0.22 + 0.35 * halo, 0, 1), KR['desk'])
        cv.c[kit.outline_of(box)] = KR['desk'][1]
        dial = kit.ellipse_full(W, H, bx + 10, by + 8, 5, 5)
        cv.paint(dial, np.full((H, W), 0.6, np.float32), KR['paper'])
        cv.px(bx + 10, by + 8, KR['red'][3] if kk % 2 else KR['metal'][2])
        cv.line(bx + 10, by + 8, bx + 12, by + 5, KR['metal'][1])
        bell = kit.ellipse_full(W, H, bx + 23, by + 6, 4, 3)
        cv.paint(bell, np.full((H, W), 0.65, np.float32), KR['brass'])
    frame_y = V(0, 258)[1]
    cv.rect(wx0, frame_y, wx1 - wx0, 5, KR['metal'][2])
    cv.rect(wx0, frame_y, wx1 - wx0, 1, KR['metal'][6])
    cols = [KR['red'][3], pg.hx('#36534D'), KR['metal'][1], KR['copper'][2], KR['red'][3], KR['metal'][1],
            pg.hx('#36534D'), KR['red'][3], KR['copper'][2], KR['metal'][1]]
    for kk, c in enumerate(cols):
        lx = wx0 + 10 + kk * 19
        lean = 4 if kk in (2, 6) else 0
        cv.line(lx, frame_y, lx + lean, frame_y - 30, KR['metal'][6])
        cv.line(lx + 1, frame_y, lx + 1 + lean, frame_y - 30, KR['metal'][3])
        cv.rect(lx - 1 + lean, frame_y - 35, 4, 6, c)
        cv.px(lx + lean, frame_y - 35, KR['metal'][8])
        cv.rect(lx - 2, frame_y + 5, 6, floor_y - frame_y - 5, KR['metal'][1])
    # Alexei's desk (left of him, he faces west): top at ~30 px, drawers, green lamp, ledger, tea
    dx0, dx1 = V(238, 0)[0], V(298, 0)[0]
    dy = V(0, 262)[1]
    top = (xx >= dx0) & (xx < dx1) & (yy >= dy) & (yy < dy + 4)
    cv.paint(top, np.clip(0.35 + 0.7 * L.pool(xx, yy + 20), 0, 1), KR['desk'])
    body = (xx >= dx0 + 3) & (xx < dx1 - 3) & (yy >= dy + 4) & (yy < floor_y)
    cv.paint(body, np.clip(0.16 + 0.35 * halo, 0, 1), KR['desk'])
    for dd_ in (dy + 8, dy + 18):
        cv.rect(dx0 + 6, dd_, 22, 8, KR['desk'][2])
        cv.rect(dx0 + 15, dd_ + 3, 4, 2, KR['brass'][4])
    cv.rect(dx0 + 4, dy - 3, 30, 3, KR['ledger'][5])
    cv.rect(dx0 + 4, dy - 1, 30, 1, KR['cover'][3])
    cv.rect(dx0 + 40, dy - 7, 5, 7, KR['tea'][3])
    cv.rect(dx0 + 39, dy - 4, 7, 4, KR['metal'][6])
    # right: stove with glowing door, kettle, pipe; bench; clock; telephone; plaque spot
    sx = V(520, 0)[0]
    stove = (xx >= sx) & (xx < sx + 32) & (yy >= V(0, 250)[1]) & (yy < floor_y)
    cv.paint(stove, np.full((H, W), 0.2, np.float32), KR['metal'])
    door = (xx >= sx + 9) & (xx < sx + 23) & (yy >= V(0, 264)[1]) & (yy < V(0, 276)[1])
    cv.paint(door, np.clip(0.5 + 0.5 * ((np.floor(yy) % 3) == 0), 0, 1), KR['fire'])
    cv.rect(sx + 13, V(0, 70)[1], 5, V(0, 250)[1] - V(0, 70)[1], KR['metal'][2])
    cv.rect(sx + 13, V(0, 70)[1], 1, V(0, 250)[1] - V(0, 70)[1], KR['metal'][4])
    cv.rect(sx + 5, V(0, 241)[1], 20, 9, KR['metal'][5])
    cv.rect(sx + 24, V(0, 243)[1], 5, 2, KR['metal'][5])
    fg = kit.ellipse_full(W, H, sx + 16, floor_y + 16, 46, 12)
    fgd = np.sqrt(((xx - sx - 16) / 46.0) ** 2 + ((yy - floor_y - 16) / 12.0) ** 2)
    cv.c[fg & (bay < 0.4 * (1 - fgd)) & (yy >= floor_y)] = KR['rust'][3]
    cv.c[fg & (bay < 0.15 * (1 - fgd)) & (yy >= floor_y)] = KR['rust'][5]
    bench = (xx >= V(420, 0)[0]) & (xx < V(500, 0)[0]) & (yy >= V(0, 272)[1]) & (yy < V(0, 276)[1])
    cv.paint(bench, np.full((H, W), 0.35, np.float32), KR['desk'])
    for lx_ in (V(426, 0)[0], V(492, 0)[0]):
        cv.rect(lx_, V(0, 276)[1], 2, floor_y - V(0, 276)[1], KR['desk'][2])
    ccx, ccy = V(400, 112)
    face = kit.ellipse_full(W, H, ccx, ccy, 10, 10)
    cv.paint(face, np.full((H, W), 0.7, np.float32), KR['paper'])
    cv.c[kit.outline_of(face)] = KR['metal'][1]
    for kk in range(12):
        a = kk / 12 * 2 * math.pi
        cv.px(ccx + math.sin(a) * 8, ccy - math.cos(a) * 8, KR['metal'][1])
    am = 47 / 60 * 2 * math.pi
    cv.line(ccx, ccy, ccx + math.sin(am) * 8, ccy - math.cos(am) * 8, KR['metal'][0])
    ah = (1 + 47 / 60) / 12 * 2 * math.pi
    cv.line(ccx, ccy, ccx + math.sin(ah) * 5, ccy - math.cos(ah) * 5, KR['metal'][0])
    cv.rect(V(456, 0)[0], V(0, 160)[1], 12, 20, KR['metal'][3])
    cv.rect(V(453, 0)[0], V(0, 157)[1], 18, 4, KR['metal'][2])
    tt = (xx >= V(330, 0)[0]) & (xx < V(372, 0)[0]) & (yy >= V(0, 100)[1]) & (yy < V(0, 150)[1])
    cv.paint(tt, np.clip(0.2 + 0.5 * halo, 0, 1), KR['paper'])
    for r in range(104, 148, 4):
        cv.rect(V(334, 0)[0], V(0, r)[1], 34, 1, KR['paper'][2])
    # foreground: the stove pipe's shadow column at the right edge (frame device)
    jamb = (xx >= V(626, 0)[0])
    cv.paint(jamb, np.full((H, W), 0.04, np.float32), KR['void'])
    info = wide.k_wide_enrich(cv, L, halo, floor_y)
    WIDE_EXTRA['k'] = info
    k.cold_patch_k(cv, [(wx0 + 5, floor_y), (wx1 - 5, floor_y), (wx1 + 70, H), (wx0 + 30, H)])
    glass = np.zeros((H, W, 4), np.uint8)
    dd = np.minimum.reduce([xx - wx0, wx1 - xx, yy - wy0, wy1 - yy])
    frm = panes & (dd < 12) & (bay < np.clip(1.0 - dd / 12.0, 0, 1) * 0.5)
    glass[frm] = pg.hx('#4A675C')
    glass[..., 3] = np.where(glass[..., :3].any(-1), 255, 0)
    extl = b.ext_layer(ext_k, (V(130, 0)[0] - 360, V(0, 168)[1] - 192))
    lamp_rgba = small_lamp_k(lamp_head)
    return cv.c, glass, extl, lamp_rgba, lamp_head, feet, (wx0, wy0, wx1, wy1)


def small_lamp_k(head):
    """Green enamel lamp on the desk, shade aimed at the ledger (and at Alexei's hands)."""
    cv = kit.Canvas(W, H)
    hx, hy = head
    base_y = V(0, 262)[1]
    cv.rect(hx - 4, base_y - 2, 9, 2, KR['metal'][3])
    cv.line(hx, base_y - 2, hx + 2, hy + 4, KR['metal'][4])
    sh = kit.poly_mask_full(W, H, [(hx - 7, hy + 5), (hx - 3, hy - 3), (hx + 4, hy - 3), (hx + 8, hy + 5)])
    cv.paint(sh, np.full((H, W), 0.55, np.float32), KR['enamel'])
    cv.rect(hx - 6, hy + 5, 13, 1, KR['copper'][3])
    xx, yy = cv.grid()
    bay = kit.bayer_full(W, H)
    cone = kit.poly_mask_full(W, H, [(hx - 6, hy + 6), (hx + 7, hy + 6), (hx + 22, hy + 30), (hx - 20, hy + 30)])
    ct = np.clip(1.0 - (yy - hy) / 34.0, 0, 1)
    cv.c[cone & (bay < ct * 0.16)] = KR['copper'][0]
    return cv.c


def konrad_seated_node(out):
    """Konrad at his desk in the wide shot (back to us): breathes, turns his head to the window and the dome
    (2.0-3.4 s), turns back and leans in towards the typewriter as the shot cuts to the close-up."""
    at = kit.Atlas('bw_konrad')
    fr = wide.konrad_seated_frames(at, V(0, 292)[1], V(236, 228))
    keys = [[0.0, fr[0]], [0.9, fr[1]], [1.6, fr[0]], [2.0, fr[2]], [2.7, fr[3]], [3.3, fr[2]], [3.5, fr[0]],
            [4.0, fr[1]], [4.3, fr[4]]]
    return {'id': 'konrad', 'type': 'anim', 'atlas': 'b_wide/konrad.png', 'frames': at.save(os.path.join(out, 'b_wide/konrad.png')),
            'keys': keys, 'z': 10}


def build_wides(ext_b, ext_k, out, T):
    sets = {}
    base, glass, extl, lamp_rgba, lamp_head, feet = b_wide(ext_b)
    wx = (V(470, 0)[0], V(0, 70)[1], V(610, 0)[0], V(0, 236)[1])
    sets['b_wide'] = {'nodes': [
        {'id': 'ext', 'type': 'sprite', 'file': save(extl, 'b_wide/ext.png', out), 'z': 0, 'parallax': 0.4},
        {'id': 'snow', 'type': 'snow', 'rect': [wx[0] - 30, wx[1] - 10, wx[2] - wx[0] + 60, wx[3] - wx[1] + 20], 'count': 90,
         'seed': kit.seed_of('bw_snow'), 'speed': [9, 18], 'sway': 2, 'wind': -3, 'near': 0.25,
         'colors': ['#8F8A92', '#D2CCCB'], 'z': 1, 'parallax': 0.6},
        {'id': 'base', 'type': 'sprite', 'file': save(base, 'b_wide/base.png', out), 'z': 2},
        {'id': 'glass', 'type': 'sprite', 'file': save(glass, 'b_wide/glass.png', out), 'z': 3},
        konrad_seated_node(out),
        {'id': 'lamp', 'type': 'sprite', 'file': save(lamp_rgba, 'b_wide/lamp.png', out), 'z': 12},
    ] + b_wide_anims(out, T), 'flicker': {'amp': 0.015, 'dips': [[1.9, 0.08, 0.16]]}}
    base, glass, extl, lamp_rgba, lamp_head, feet, wk = k_wide(ext_k)
    sets['k_wide'] = {'nodes': [
        {'id': 'ext', 'type': 'sprite', 'file': save(extl, 'k_wide/ext.png', out), 'z': 0, 'parallax': 0.4},
        {'id': 'snow', 'type': 'snow', 'rect': [wk[0] - 30, wk[1] - 10, wk[2] - wk[0] + 60, wk[3] - wk[1] + 20], 'count': 110,
         'seed': kit.seed_of('kw_snow'), 'speed': [9, 18], 'sway': 2, 'wind': 3, 'near': 0.25,
         'colors': ['#7E8E8C', '#DEE5DC'], 'z': 1, 'parallax': 0.6},
        {'id': 'base', 'type': 'sprite', 'file': save(base, 'k_wide/base.png', out), 'z': 2},
        {'id': 'glass', 'type': 'sprite', 'file': save(glass, 'k_wide/glass.png', out), 'z': 3},
        {'id': 'alexei', 'type': 'actor', 'char': 'alexei', 'anim': 'idle_side', 'flip': True, 'pos': list(feet),
         'modulate': '#7b8a86', 'z': 10,
         'light': {'pos': [lamp_head[0] - feet[0] - 4, lamp_head[1] - feet[1] + 8], 'color': '#F0C487', 'energy': 1.6,
                   'scale': 0.45, 'height': 20}},
        {'id': 'lamp', 'type': 'sprite', 'file': save(lamp_rgba, 'k_wide/lamp.png', out), 'z': 12},
    ] + k_wide_anims(out, T), 'flicker': {'amp': 0.015, 'dips': []}}
    return sets


def window_life(sid, out, T):
    """Motion behind the window inserts: Berlin -- the searchlights sweeping behind the dome; Karsk -- a
    signalman's lantern walking along the far track and a shunting engine's headlamp crawling past."""
    nodes = []
    if sid == 'b_window':
        at = kit.Atlas('bwin_beams')
        fr = wide.searchlight_frames(at, (V(320, 0)[0] - 360, V(0, 190)[1] - 240), n=24)
        nodes.append({'id': 'beams', 'type': 'anim', 'atlas': 'b_window/beams.png',
                      'frames': at.save(os.path.join(out, 'b_window/beams.png')), 'z': 0, 'parallax': 0.5,
                      'loop': {'fps': 3.0, 'seq': fr, 't0': 0.0}})
        return nodes
    t0, t1 = T['k_window']
    lant = np.zeros((H, W, 4), np.uint8)
    cv = kit.Canvas(W, H)
    bay = kit.bayer_full(W, H)
    xx, yy = cv.grid()
    cx, cy = 40, 232
    g = np.clip(1.0 - np.sqrt(((xx - cx) / 22.0) ** 2 + ((yy - cy - 6) / 10.0) ** 2), 0, 1)
    m = (g > 0.04) & (bay < g * 0.5)
    cv.c[m] = pg.hx('#6B3B2C')
    cv.c[m & (bay < g * 0.2)] = pg.hx('#AF6C47')
    cv.rect(cx - 1, cy - 2, 3, 3, pg.hx('#FBE3AE'))
    cv.rect(cx - 3, cy - 14, 2, 10, pg.hx('#0A1219'))
    cv.rect(cx - 4, cy - 18, 4, 4, pg.hx('#13252B'))
    cv.rect(cx - 4, cy - 4, 2, 9, pg.hx('#0A1219'))
    save(cv.c, 'k_window/lantern.png', out)
    nodes.append({'id': 'lantern', 'type': 'sprite', 'file': 'k_window/lantern.png', 'z': 0, 'parallax': 0.5,
                  'pos_keys': [[t0, 0, 0], [t1 + 0.5, 70, -4]], 'pos_lin': True})
    hl = kit.Canvas(W, H)
    g = np.clip(1.0 - np.sqrt(((xx - 300) / 60.0) ** 2 + ((yy - 196) / 8.0) ** 2), 0, 1)
    m = (g > 0.03) & (bay < g * 0.6)
    hl.c[m] = pg.hx('#7E8E8C')
    hl.c[m & (bay < g * 0.25)] = pg.hx('#DEE5DC')
    hl.rect(296, 194, 6, 4, pg.hx('#F1F4EC'))
    hl.rect(302, 186, 34, 12, pg.hx('#0A1219'))
    hl.rect(310, 180, 14, 6, pg.hx('#0A1219'))
    save(hl.c, 'k_window/shunter.png', out)
    nodes.append({'id': 'shunter', 'type': 'sprite', 'file': 'k_window/shunter.png', 'z': 0, 'parallax': 0.5,
                  'pos_keys': [[t0, 120, 0], [t1 + 0.5, -40, 0]], 'pos_lin': True})
    return nodes


def b_wide_anims(out, T):
    """Pendulum (1 Hz swing in step with the tick/tock), searchlight sweep behind the dome, tram flash at the
    tram bell, smoke from the cigarette on the sill."""
    ex = WIDE_EXTRA['b']
    nodes = []
    at = kit.Atlas('bw_pend')
    fr = wide.pendulum_frames(at, ex['pendulum'], 22, n=16)
    nodes.append({'id': 'pendulum', 'type': 'anim', 'atlas': 'b_wide/pendulum.png',
                  'frames': at.save(os.path.join(out, 'b_wide/pendulum.png')),
                  'z': 5, 'loop': {'fps': 8.0, 'seq': fr, 't0': 0.0}})        # extremes on the ticks (0.5, 1.5, ...)
    at = kit.Atlas('bw_beams')
    fr = wide.searchlight_frames(at, ex['ext_off'], n=24)
    nodes.append({'id': 'beams', 'type': 'anim', 'atlas': 'b_wide/beams.png', 'frames': at.save(os.path.join(out, 'b_wide/beams.png')),
                  'z': 0, 'parallax': 0.4, 'loop': {'fps': 3.0, 'seq': fr, 't0': 0.0}})
    at = kit.Atlas('bw_flash')
    f1, f2 = wide.tram_flash(at, ex['win'])
    nodes.append({'id': 'tram_flash', 'type': 'anim', 'atlas': 'b_wide/flash.png', 'frames': at.save(os.path.join(out, 'b_wide/flash.png')),
                  'z': 6, 'keys': [[0.0, -1], [2.32, f1], [2.40, f2], [2.47, -1], [2.58, f2], [2.63, -1]]})
    at = kit.Atlas('bw_sillsmoke')
    fr = ka.wisp_frames(at, ex['tip'], 10, kit.BR['smoke'], kit.Lamp(404, 240, 64, 70), 'bw_sill', height=46, spread=3.0,
                        draft=-5.0, count=6, rmax=2.6, density=0.7, ribbon=True)
    nodes.append({'id': 'sill_smoke', 'type': 'anim', 'atlas': 'b_wide/sill_smoke.png',
                  'frames': at.save(os.path.join(out, 'b_wide/sill_smoke.png')), 'z': 7, 'loop': {'fps': 7.0, 'seq': fr, 't0': 0.0}})
    return nodes


def k_wide_anims(out, T):
    """Freight train passing in the yard (behind the window, with the far horn), blinking track lamps on the
    diagram, the stove's firelight, the kettle's steam."""
    ex = WIDE_EXTRA['k']
    nodes = []
    t0, t1 = T['k_wide']
    train = wide.train_sprite(360)
    save(train, 'k_wide/train.png', out)
    y_tr = 136
    nodes.append({'id': 'train', 'type': 'sprite', 'file': 'k_wide/train.png', 'pos': [0, y_tr], 'z': 1, 'parallax': 0.4,
                  'pos_keys': [[0.0, 396, 0], [t0 - 0.2, 396, 0], [t1 + 0.2, -312, 0]], 'pos_lin': True})
    at = kit.Atlas('kw_plume')
    fr = [at.add_cropped(img, 0, 0) for img in wide.steam_plume_frames(at, n=6)]
    nodes.append({'id': 'plume', 'type': 'anim', 'atlas': 'k_wide/plume.png', 'frames': at.save(os.path.join(out, 'k_wide/plume.png')),
                  'pos': [8, y_tr - 22], 'z': 1, 'parallax': 0.4, 'loop': {'fps': 6.0, 'seq': fr, 't0': 0.0},
                  'pos_keys': [[0.0, 396, 0], [t0 - 0.2, 396, 0], [t1 + 0.2, -312, 0]], 'pos_lin': True})
    at = kit.Atlas('kw_lamps')
    fr = wide.track_lamp_frames(at, ex['lamps'], n=8)
    nodes.append({'id': 'track_lamps', 'type': 'anim', 'atlas': 'k_wide/track_lamps.png',
                  'frames': at.save(os.path.join(out, 'k_wide/track_lamps.png')), 'z': 5, 'loop': {'fps': 2.0, 'seq': fr, 't0': 0.0}})
    at = kit.Atlas('kw_glow')
    fr = wide.stove_glow_frames(at, (556, 280), n=8)
    nodes.append({'id': 'stove_glow', 'type': 'anim', 'atlas': 'k_wide/stove_glow.png',
                  'frames': at.save(os.path.join(out, 'k_wide/stove_glow.png')), 'z': 6,
                  'loop': {'fps': 9.0, 'seq': [fr[i] for i in (0, 3, 1, 5, 2, 7, 4, 6, 1, 3)], 't0': 0.0}})
    at = kit.Atlas('kw_kettle')
    fr = ka.wisp_frames(at, (570, 250), 10, kit.KR['steam'], kit.Lamp(282, 302, 64, 70), 'kw_kettle', height=40, spread=3.0,
                        draft=-6.0, count=7, rmax=3.5, density=0.8)
    nodes.append({'id': 'kettle_steam', 'type': 'anim', 'atlas': 'k_wide/kettle_steam.png',
                  'frames': at.save(os.path.join(out, 'k_wide/kettle_steam.png')), 'z': 7, 'loop': {'fps': 7.0, 'seq': fr, 't0': 0.0}})
    return nodes


# ------------------------------------------------------------------------------------------- map
B_CITY = V(118, 228)
K_CITY = V(526, 238)
VELTRAVA = V(320, 214)


def map_paper(state: str) -> np.ndarray:
    """state: 'both' (two lamp pools), 'berlin' (Karsk lamp off), 'dark' (both off: faint cold light)."""
    cv = kit.Canvas(W, H, 'map_' + state)
    xx, yy = cv.grid()
    tone = MR['tone']
    nz = pg.value_noise(W, H, 26, kit.seed_of('map_paper'), octaves=4)
    lb = kit.Lamp(V(150, 168)[0], V(0, 168)[1], 118, 150, depth=0.62, power=1.0, aim=(-20, 52))
    lk = kit.Lamp(V(490, 168)[0], V(0, 168)[1], 118, 150, depth=0.62, power=1.0, aim=(20, 52))
    light = np.zeros((H, W), np.float32)
    if state in ('both', 'berlin'):
        light += lb.pool(xx, yy)
    if state == 'both':
        light += lk.pool(xx, yy)
    base_t = 0.05 + (nz - 0.5) * 0.05
    if state == 'dark':
        base_t = base_t + 0.04
    t = np.clip(base_t + 0.55 * light, 0, 1)
    cv.paint(np.ones((H, W), bool), t, tone)
    # the lamp pools are warm: amber paper under Konrad's lamp (left), copper under Alexei's (right)
    warm_b = [pg.hx(c) for c in ('#2A2829', '#343232', '#494545', '#5E5A54', '#7A7364', '#969185', '#B0AA93',
                                 '#CEC6AA', '#E6DEC2')]
    warm_k = [pg.hx(c) for c in ('#2A2829', '#343232', '#4A2A22', '#6B3B2C', '#8D5542', '#AF6C47', '#C98A5C',
                                 '#DCA16E', '#F0C487')]
    if state in ('both', 'berlin'):
        pb = lb.pool(xx, yy)
        mb = pb > 0.10
        cv.paint(mb & (xx < V(320, 0)[0]), np.clip(base_t + 0.66 * pb, 0, 1), warm_b)
    if state == 'both':
        pk = lk.pool(xx, yy)
        mk = pk > 0.10
        cv.paint(mk & (xx >= V(320, 0)[0]), np.clip(base_t + 0.66 * pk, 0, 1), warm_k)
    # fold lines (a map that has been folded many times)
    for fx in (V(214, 0)[0], V(428, 0)[0]):
        m = (np.abs(xx - fx) < 0.6)
        cv.paint(m, np.clip(t - 0.10, 0, 1), tone)
    fy = V(0, 196)[1]
    cv.paint(np.abs(yy - fy) < 0.6, np.clip(t - 0.10, 0, 1), tone)

    def ink(tt):
        return kit.tone_to_ramp(np.clip(tt, 0, 1), tone, dither=False)
    ink_t = np.clip(t * 0.45, 0, 1)
    ink_col = ink(ink_t)
    # grid ticks along the border + frame
    fr = ((xx >= V(14, 0)[0]) & (xx < V(626, 0)[0]) & ((np.abs(yy - V(0, 52)[1]) < 0.6) | (np.abs(yy - V(0, 306)[1]) < 0.6))) | \
         ((yy >= V(0, 52)[1]) & (yy < V(0, 306)[1]) & ((np.abs(xx - V(14, 0)[0]) < 0.6) | (np.abs(xx - V(626, 0)[0]) < 0.6)))
    cv.c[fr] = ink_col[fr]
    for gx in range(V(14, 0)[0], V(626, 0)[0], 60):
        cv.rect(gx, V(0, 52)[1], 1, 4, ink_col[V(0, 52)[1], gx])
        cv.rect(gx, V(0, 302)[1], 1, 4, ink_col[V(0, 302)[1], gx])
    # rivers (soft double lines), terrain hatching blobs
    for pts in ([V(60, 60), V(90, 140), V(70, 220), V(110, 305)], [V(250, 60), V(270, 150), V(240, 230), V(280, 306)],
                [V(440, 52), V(470, 120), V(430, 200), V(470, 306)]):
        for (px_, py_) in pg.bezier(pts, n=160):
            ix, iy = int(px_), int(py_)
            if 0 <= iy < H and 0 <= ix < W:
                cv.c[iy, ix] = ink(np.array([[t[iy, ix] * 0.7]]))[0, 0]
                cv.c[iy, ix + 2] = ink(np.array([[t[iy, ix] * 0.7]]))[0, 0]
    rng = np.random.default_rng(kit.seed_of('map_hatch'))
    for (hx, hy, r) in ((V(180, 120), 22), (V(390, 270), 18), (V(560, 120), 20), (V(70, 270), 16)) if False else \
            [(*V(180, 120), 22), (*V(390, 272), 18), (*V(568, 118), 20), (*V(66, 276), 16)]:
        for kk in range(40):
            a = kk / 40 * 2 * math.pi
            x0_, y0_ = hx + math.cos(a) * r, hy + math.sin(a) * r * 0.6
            x1_, y1_ = hx + math.cos(a) * (r + 5), hy + math.sin(a) * (r + 5) * 0.6
            cv.line(x0_, y0_, x1_, y1_, ink(np.array([[t[int(hy), int(hx)] * 0.6]]))[0, 0])
    # the armistice line ("die Linie"): dash-dot, north-south through Veltrava
    lx = V(320, 0)[0]
    for y in range(V(0, 54)[1], V(0, 304)[1]):
        ph = (y - V(0, 54)[1]) % 12
        if ph < 6 or ph in (8, 9):
            wob = int(round(math.sin(y / 23.0) * 2))
            cv.c[y, lx + wob] = ink(np.array([[t[y, lx] * 0.35]]))[0, 0]
            cv.c[y, lx + wob + 1] = ink(np.array([[t[y, lx] * 0.35]]))[0, 0]
    # corridor band (hatched) and the rail line under the route
    route = route_points()
    for (px_, py_) in route:
        for off in (-7, 7):
            ix, iy = int(px_), int(py_ + off)
            if (ix + iy) % 3 == 0 and 0 <= iy < H:
                cv.c[iy, ix] = ink(np.array([[t[iy, ix] * 0.6]]))[0, 0]
        ix, iy = int(px_), int(py_ + 3)
        if (ix // 3) % 2 == 0:
            cv.c[iy, ix] = ink(np.array([[t[iy, ix] * 0.3]]))[0, 0]
    # cities + labels
    for (cx, cy), name in ((B_CITY, 'BERLIN'), (VELTRAVA, 'VELTRAVA'), (K_CITY, 'KARSK')):
        ring = kit.ellipse_full(W, H, cx, cy, 4.5, 4.5) & ~kit.ellipse_full(W, H, cx, cy, 2.5, 2.5)
        cv.c[ring] = ink(np.clip(t * 0.3, 0, 1))[ring]
        tm = kit.text_mask(name, kit.FONT3)
        kit.blit_mask(cv.c, tm, int(cx - tm.shape[1] / 2), int(cy + 8), ink(np.array([[t[int(cy), int(cx)] * 0.35]]))[0, 0])
    tm = kit.text_mask('LINIE 1953', kit.FONT3)
    kit.blit_mask(cv.c, tm, lx + 6, V(0, 66)[1], ink(np.array([[t[V(0, 66)[1], lx] * 0.4]]))[0, 0])
    tm = kit.text_mask('KORRIDOR C', kit.FONT3)
    kit.blit_mask(cv.c, tm, V(380, 0)[0], V(0, 178)[1], ink(np.array([[t[V(0, 178)[1], V(380, 0)[0]] * 0.45]]))[0, 0])
    # compass + title block
    tm = kit.text_mask('SCHEMA - NICHT MASSSTAEBLICH', kit.FONT3)
    kit.blit_mask(cv.c, tm, V(30, 0)[0], V(0, 292)[1], ink(np.array([[t[V(0, 292)[1], V(30, 0)[0]] * 0.45]]))[0, 0])
    import cine_finale_mapdetail as md
    md.enrich(cv, t, tone, state, {'BERLIN': B_CITY, 'VELTRAVA': VELTRAVA, 'KARSK': K_CITY}, lx, route_points())
    if state == 'dark':
        md.window_light(cv, tone)
    cv.c[..., 3] = 255
    return cv.c


def route_points():
    """The C-17 route from Karsk west to Berlin along the corridor (screen points, ordered)."""
    ctrl = [K_CITY, V(470, 226), V(420, 230), V(372, 214), VELTRAVA, V(272, 216), V(220, 236), V(170, 230), B_CITY]
    pts = []
    for a, b_, c in zip(ctrl[:-2:2], ctrl[1:-1:2], ctrl[2::2]):
        pts += pg.bezier([a, b_, c], n=120)[:-1]
    pts.append(ctrl[-1])
    return pts


def route_layers():
    """Route sprite (2 px red line with dark-red edge glow) + order texture (arc length in R + G/255)."""
    pts = route_points()
    total = sum(math.dist(a, c) for a, c in zip(pts[:-1], pts[1:]))
    img = np.zeros((H, W, 4), np.uint8)
    order = np.zeros((H, W, 4), np.uint8)
    acc = 0.0
    red = MR['red']
    halo = np.zeros((H, W), bool)
    for i, (a, c) in enumerate(zip(pts[:-1], pts[1:])):
        seg = math.dist(a, c)
        steps = max(1, int(seg * 2))
        for s_ in range(steps):
            f = s_ / steps
            x = a[0] + (c[0] - a[0]) * f
            y = a[1] + (c[1] - a[1]) * f
            o = (acc + seg * f) / total
            for (dx, dy) in ((0, 0), (0, 1)):
                ix, iy = int(x) + dx, int(y) + dy
                if 0 <= ix < W and 0 <= iy < H and order[iy, ix, 3] == 0:
                    img[iy, ix] = (*red[2][:3], 255) if dy == 0 else (*red[1][:3], 255)
                    v = int(o * 65535)
                    order[iy, ix] = (v >> 8, v & 255, 0, 255)
        acc += seg
    # dark-red glow (1 px) around the line, same order as the nearest line pixel
    core = order[..., 3] > 0
    ring = kit.dilate(core, 1) & ~core
    ys, xs = np.nonzero(ring)
    for y, x in zip(ys, xs):
        best = None
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                yy_, xx_ = y + dy, x + dx
                if 0 <= yy_ < H and 0 <= xx_ < W and core[yy_, xx_]:
                    best = order[yy_, xx_]
                    break
            if best is not None:
                break
        if best is not None and (x + y) % 2 == 0:
            img[y, x] = (*red[0][:3], 255)
            order[y, x] = best
    return img, order


def map_lamps(out):
    """Lamp heads at the same screen positions as in the close-ups (on/off frames)."""
    at_b = kit.Atlas('map_lamp_b')
    on, _ = b.lamp_architect(W, H, V(112, 70), True)
    off, _ = b.lamp_architect(W, H, V(112, 70), False)
    fb = [at_b.add(on), at_b.add(off)]
    rb = at_b.save(os.path.join(out, 'map/lamp_b.png'))
    at_k = kit.Atlas('map_lamp_k')
    on, _ = k.lamp_enamel(W, H, V(528, 70), True)
    off, _ = k.lamp_enamel(W, H, V(528, 70), False)
    fk = [at_k.add(on), at_k.add(off)]
    rk = at_k.save(os.path.join(out, 'map/lamp_k.png'))
    return (rb, fb), (rk, fk)


def build_map(out, T, DUR):
    t0, t1 = T['map']
    r_start, r_end = t0 + 1.4, t0 + 7.0
    k_off, b_off = r_end + 0.8, r_end + 1.6
    nodes = [
        {'id': 'paper', 'type': 'sprite', 'file': save(map_paper('both'), 'map/paper.png', out), 'z': 0},
        {'id': 'paper_b', 'type': 'sprite', 'file': save(map_paper('berlin'), 'map/paper_berlin.png', out), 'z': 1,
         'reveal': [[0.0, 0.0], [k_off, 0.0], [k_off + 0.25, 1.0]]},
        {'id': 'paper_d', 'type': 'sprite', 'file': save(map_paper('dark'), 'map/paper_dark.png', out), 'z': 2,
         'reveal': [[0.0, 0.0], [b_off, 0.0], [b_off + 0.25, 1.0]]},
    ]
    img, order = route_layers()
    nodes.append({'id': 'route', 'type': 'route', 'file': save(img, 'map/route.png', out), 'order': save(order, 'map/route_order.png', out),
                  'z': 5, 'progress': [[0.0, 0.0], [r_start, 0.0], [r_end, 1.0]],
                  'reveal': [[0.0, 1.0], [DUR - 2.6, 1.0], [DUR - 0.6, 0.0]]})
    (rb, fb), (rk, fk) = map_lamps(out)
    nodes.append({'id': 'lamp_b', 'type': 'anim', 'atlas': 'map/lamp_b.png', 'frames': rb, 'z': 30,
                  'keys': [[0.0, fb[0]], [b_off, fb[1]]]})
    nodes.append({'id': 'lamp_k', 'type': 'anim', 'atlas': 'map/lamp_k.png', 'frames': rk, 'z': 30,
                  'keys': [[0.0, fk[0]], [k_off, fk[1]]]})
    return {'map': {'nodes': nodes, 'flicker': {'amp': 0.01, 'dips': [[k_off - 0.25, 0.06, 0.1], [b_off - 0.3, 0.05, 0.1]]}}}, \
        (r_start, r_end, k_off, b_off)


# ------------------------------------------------------------------------------------------- shots / events
def build(ext_b, ext_k, T, DUR, out, HOME):
    sets = {}
    sets.update(build_windows(ext_b, ext_k, T, out))
    sets.update(build_wides(ext_b, ext_k, out, T))
    msets, (r_start, r_end, k_off, b_off) = build_map(out, T, DUR)
    sets.update(msets)
    shots = []

    def cam(t0, t1, a, c):
        return [[t0, a[0], a[1]], [t1, c[0], c[1]]]
    t0, t1 = T['b_wide']
    shots.append({'set': 'b_wide', 't0': t0, 't1': t1, 'home': HOME, 'cam': cam(t0, t1, (4, 12), (30, 8))})
    t0, t1 = T['b_window']
    shots.append({'set': 'b_window', 't0': t0, 't1': t1, 'home': HOME, 'cam': cam(t0, t1, (20, 12), (24, 6))})
    t0, t1 = T['veil']
    shots.append({'set': 'veil', 't0': t0, 't1': t1, 'home': HOME, 'fade_in': 0.55, 'fade_out': 0.55,
                  'cam': cam(t0, t1, (20, 10), (20, 10))})
    t0, t1 = T['k_window']
    shots.append({'set': 'k_window', 't0': t0, 't1': t1, 'home': HOME, 'fade_in': 0.7, 'cam': cam(t0, t1, (20, 6), (16, 12))})
    t0, t1 = T['k_wide']
    shots.append({'set': 'k_wide', 't0': t0, 't1': t1, 'home': HOME, 'fade_in': 0.35, 'cam': cam(t0, t1, (36, 8), (10, 12))})
    t0, t1 = T['r3_b']
    shots.append({'set': 'b_window', 't0': t0, 't1': t1, 'home': HOME, 'cam': cam(t0, t1, (22, 9), (23, 9))})
    t0, t1 = T['r4_k']
    shots.append({'set': 'k_window', 't0': t0, 't1': t1, 'home': HOME, 'cam': cam(t0, t1, (18, 9), (17, 9))})
    t0, t1 = T['map']
    shots.append({'set': 'map', 't0': t0, 't1': t1, 'home': HOME, 'fade_in': 0.8,
                  'cam': [[t0, 20, 10], [r_start, 24, 10], [r_end, 10, 8], [t1, 14, 8]],
                  'tint': [[0.0, 0.0], [DUR - 1.2, 0.0], [DUR - 0.1, 1.0]], 'tint_color': '#000000'})
    ev = events(T, DUR, r_start, r_end, k_off, b_off)
    return sets, shots, ev


def events(T, DUR, r_start, r_end, k_off, b_off):
    E = []

    def sfx(t, sid, db=0.0, when=None):
        e = {'t': round(t, 3), 'type': 'sfx', 'id': sid, 'db': db}
        if when:
            e['when'] = when
        E.append(e)
    E.append({'t': 0.0, 'type': 'music', 'id': 'cine_finale_score', 'db': -2.0})
    E.append({'t': 0.0, 'type': 'loop', 'id': 'cine_finale_room_berlin', 'key': 'room', 'db': -14.0, 'fade': 1.2, 'bus': 'Ambience'})
    E.append({'t': 13.6, 'type': 'loop_stop', 'key': 'room', 'fade': 1.6})
    E.append({'t': 14.2, 'type': 'loop', 'id': 'cine_finale_room_karsk', 'key': 'room_k', 'db': -14.0, 'fade': 1.4, 'bus': 'Ambience'})
    E.append({'t': 33.0, 'type': 'loop_stop', 'key': 'room_k', 'fade': 2.0})
    E.append({'t': 0.5, 'type': 'subtitle', 'key': 'cine.finale.caption_berlin', 'dur': 3.4})
    E.append({'t': 15.0, 'type': 'subtitle', 'key': 'cine.finale.caption_karsk', 'dur': 3.6})
    E.append({'t': r_end + 0.15, 'type': 'subtitle', 'key': 'cine.finale.line1', 'dur': 2.5})
    E.append({'t': b_off + 0.3, 'type': 'subtitle', 'key': 'cine.finale.final', 'dur': DUR - (b_off + 0.3) - 0.1})
    # Berlin: pendulum clock, tick-tock each second (quieter in the close-up, gone in the window insert)
    t = 0.5
    i = 0
    while t < 13.6:
        db = -15.0 if t < T['b_close'][0] else (-19.0 if t < T['b_window'][0] else -24.0)
        sfx(t, 'cine_finale_tick' if i % 2 == 0 else 'cine_finale_tock', db)
        t += 1.0
        i += 1
    sfx(2.3, 'tram_bell', -26.0)
    sfx(T['b_window'][0] + 0.2, 'cine_finale_snowgust', -8.0)
    # Karsk: telegraph / block instrument clicks (irregular groups) from the window onward
    tk = T['k_window'][0] + 0.6
    pattern = [0.0, 0.14, 0.28, 0.62, 0.76, 1.30, 1.44, 1.58, 1.72]
    while tk < T['k_close'][1]:
        for p in pattern:
            if tk + p < T['k_close'][1]:
                db = -16.0 if tk + p < T['k_close'][0] else -21.0
                sfx(tk + p, 'cine_finale_telegraph', db)
        tk += 3.6
    sfx(T['k_wide'][0] + 1.4, 'train_horn_far', -22.0)
    # branch foley -- Berlin
    b0 = T['b_close'][0]
    req = {'m1_choose': 'request_explanation'}
    evd = {'m1_choose': 'preserve_evidence'}
    import cine_finale_berlin_anim as ba
    for (ta, tb), n in ((ba.T_LINE0, len(ba.LINES[0])), (ba.T_LINE1, len(ba.LINES[1]))):
        line = ba.LINES[0 if n == len(ba.LINES[0]) else 1]
        for c in range(0, n, 2):                      # every second key: readable rhythm, no voice stealing
            if line[c] == ' ':
                continue
            sfx(b0 + ta + (tb - ta) * c / n, 'cine_finale_type', -9.0, req)
    sfx(b0 + ba.T_CR1[0] + 0.22, 'cine_finale_bell', -14.0, req)
    sfx(b0 + ba.T_CR1[0] + 0.3, 'cine_finale_carriage', -10.0, req)
    sfx(b0 + ba.T_PULL[0], 'cine_finale_pull', -8.0, req)
    sfx(b0 + ba.T_CARRY[1] - 0.05, 'paper_rustle', -12.0, req)
    sfx(b0 + 0.5, 'paper_rustle', -13.0, evd)
    sfx(b0 + 1.2, 'cine_finale_fold', -10.0, evd)
    sfx(b0 + 2.1, 'cine_finale_fold', -11.0, evd)
    sfx(b0 + 2.8, 'cine_finale_cloth', -10.0, evd)          # the coat panel pulled up over the desk edge
    sfx(b0 + 3.5, 'cine_finale_cloth', -16.0, evd)          # the lining smoothed
    sfx(b0 + 4.3, 'paper_rustle', -15.0, evd)               # the packet slides into the slit
    sfx(b0 + 5.05, 'cine_finale_cloth', -17.0, evd)         # patted flat
    sfx(b0 + 5.35, 'cine_finale_cloth', -12.0, evd)         # the panel falls back
    # branch foley -- Karsk
    k0 = T['k_close'][0]
    sh = {'a1_choose': 'share_with_irina'}
    kp = {'a1_choose': 'keep_private'}
    for tt in (0.62, 0.9, 1.16):
        sfx(k0 + tt, 'cine_finale_knock', -6.0, sh)
    sfx(k0 + 1.45, 'door_open', -10.0, sh)
    sfx(k0 + 1.55, 'wind_gust', -14.0, sh)
    sfx(k0 + 2.95, 'paper_rustle', -13.0, sh)
    sfx(k0 + 4.0, 'cine_finale_pencil', -12.0, sh)
    sfx(k0 + 5.2, 'cine_finale_door_shut', -11.0, sh)
    sfx(k0 + 1.25, 'cine_finale_pencil', -12.0, kp)
    sfx(k0 + 1.9, 'cine_finale_book', -8.0, kp)             # the ledger shuts
    sfx(k0 + 2.55, 'drawer_slide', -10.0, kp)               # the drawer pulled wide open
    sfx(k0 + 3.4, 'paper_rustle', -17.0, kp)                # the book slides across the blotter
    sfx(k0 + 4.15, 'cine_finale_book', -9.0, kp)            # over the edge, into the drawer
    sfx(k0 + 4.65, 'drawer_slide', -10.0, kp)               # pushed shut
    sfx(k0 + 5.3, 'cine_finale_key', -8.0, kp)              # the key turns
    # rhyme: tick / telegraph answering, then together
    sfx(T['r1_b'][0] + 0.45, 'cine_finale_tick', -14.0)
    sfx(T['r2_k'][0] + 0.45, 'cine_finale_telegraph', -13.0)
    sfx(T['r3_b'][0] + 0.3, 'cine_finale_tock', -15.0)
    sfx(T['r4_k'][0] + 0.3, 'cine_finale_telegraph', -14.0)
    sfx(T['split'][0] + 0.5, 'cine_finale_tick', -14.0)
    sfx(T['split'][0] + 0.5, 'cine_finale_telegraph', -15.0)
    sfx(T['split'][0] + 1.5, 'cine_finale_tock', -16.0)
    sfx(T['split'][0] + 1.5, 'cine_finale_telegraph', -17.0)
    # the map: the line is drawn (soft pen on paper), then two switches
    sfx(r_start, 'cine_finale_pen', -12.0)
    sfx(k_off, 'cine_finale_switch_k', -6.0)
    sfx(b_off, 'cine_finale_switch_b', -6.0)
    E.sort(key=lambda e: e['t'])
    return E
