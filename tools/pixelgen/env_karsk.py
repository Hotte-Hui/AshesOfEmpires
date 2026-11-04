"""env_karsk -- generator for scene A1 'Verladebahnhof Karsk' (fictional Soviet railway town, winter
dawn, 1964).  Reproduce everything with:

    py -3 -P tools/pixelgen/env_karsk.py               (art + scene.json + locale + previews)
    py -3 -P tools/pixelgen/env_karsk.py --no-preview  (skip the python review composites)
    py -3 -P tools/pixelgen/env_karsk.py --docs        (also rebuild the inspect-UI documents)

Outputs (area env_karsk):
    assets/environments/karsk_railyard/*.png (+ _n normal maps, _e emission masks), props/, fx/, actors/,
        and the *_hist twins of every file that shows a state emblem (TECHNICAL_ARCHITECTURE §12.4)
    assets/environments/karsk_railyard/scene.json         (§3.1 + §12.2 hotspots/actors)
    data/locale/de_env_karsk.json                          (optional observation strings)
    assets/environments/karsk_railyard/_preview/*.png      (composited checks, .gdignore'd)
Deterministic: fixed seeds, no network, original procedural art (references are never sampled).
"""
from __future__ import annotations

import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import numpy as np  # noqa: E402
from PIL import Image  # noqa: E402

import pg  # noqa: E402
from env_karsk_lib import (ENV_DIR, ROOT, Layer, crop_v, crop_box, palette_report, NI, TE, SA, SK, ST, RU,  # noqa: E402
                           CO, SN, WO, RED)
import env_karsk_bg as BG  # noqa: E402
import env_karsk_yard as YD  # noqa: E402
import env_karsk_fx as FX  # noqa: E402
import env_karsk_life as LF  # noqa: E402
import env_karsk_sprites as SPR  # noqa: E402

WORLD = (1920, 360)
ACTOR_DIR = 'res://scenes/levels/karsk/'


def hexc(c):
    return '#%02X%02X%02X' % (int(c[0]), int(c[1]), int(c[2]))


EMISSION_STRENGTH = {'far_city': 0.35, 'far_industry': 0.35, 'mid': 0.45, 'near_bg': 0.3, 'poles': 0.7,
                     'yard_back': 0.16, 'ground': 0.25}


def _crop_rows(L: Layer, y0: int, y1: int) -> Layer:
    N = Layer(L.w, y1 - y0, L.name)
    N.c, N.hgt, N.nrm, N.em = L.c[y0:y1].copy(), L.hgt[y0:y1].copy(), L.nrm[y0:y1].copy(), L.em[y0:y1].copy()
    return N


def _crop_box_at(L: Layer, x0, y0, x1, y1) -> Layer:
    N = Layer(x1 - x0, y1 - y0, L.name)
    N.c, N.hgt = L.c[y0:y1, x0:x1].copy(), L.hgt[y0:y1, x0:x1].copy()
    N.nrm, N.em = L.nrm[y0:y1, x0:x1].copy(), L.em[y0:y1, x0:x1].copy()
    return N


def save_layer(L: Layer, name, pos_x, pos_y, parallax, z, lit=True, normal=True, crop=True, strength=3.0,
               repeat_x=0, hist: Layer | None = None):
    """Crop + save a parallax layer.  hist: same-size layer with the historical emblems -> <name>_hist.png
    (+ _hist_n / _hist_e), cropped identically.  Returns (manifest entry, saved Layer, hist Layer or None)."""
    dy = 0
    if crop:
        rows = np.nonzero(L.c[..., 3].any(1))[0]
        if len(rows):
            dy, y1 = int(rows[0]), int(rows[-1]) + 1
            L = _crop_rows(L, dy, y1)
            if hist is not None:
                hist = _crop_rows(hist, dy, y1)
        pos_y += dy
    base = os.path.join(ENV_DIR, name)
    info = L.save(base, normal=normal, strength=strength)
    if hist is not None:
        hist.save(base + '_hist', normal=normal, emission=info['emission'], strength=strength)
    entry = {'name': name, 'file': name + '.png', 'pos': [int(pos_x), int(pos_y)],
             'parallax': [parallax, 0.0 if parallax < 1.0 else 1.0], 'z': z,
             'normal': bool(normal), 'emission': bool(info['emission']), 'lit': bool(lit),
             'size': [L.w, L.h]}
    if repeat_x:
        entry['repeat_x'] = repeat_x
    if entry['emission'] and name in EMISSION_STRENGTH:
        entry['emission_strength'] = EMISSION_STRENGTH[name]
    need = 640 + parallax * (WORLD[0] - 640)
    assert L.w >= need - 0.5 or parallax == 0.0 and L.w >= 640, (name, L.w, need)
    return entry, L, hist


def save_prop(P: Layer, name, foot_local, foot_world, base_y, collision, z=0, normal=True, extra=None,
              hist: Layer | None = None):
    """Crop the prop to content and place it so foot_local (x, y in the uncropped sprite) lands on
    foot_world.  hist: same-size variant with historical emblems, saved as <name>_hist.png with the same crop.
    Returns (manifest entry, pos, (crop x0, y0), saved Layer, hist Layer or None)."""
    C, cx0, cy0 = crop_box(P, pad=0)
    fx, fy = foot_local
    pos = [int(foot_world[0] - (fx - cx0)), int(foot_world[1] - (fy - cy0))]
    os.makedirs(os.path.join(ENV_DIR, 'props'), exist_ok=True)
    info = C.save(os.path.join(ENV_DIR, 'props', name), normal=normal, strength=3.0)
    H = None
    if hist is not None:
        H = _crop_box_at(hist, cx0, cy0, cx0 + C.w, cy0 + C.h)
        H.save(os.path.join(ENV_DIR, 'props', name + '_hist'), normal=normal, emission=info['emission'],
               strength=3.0)
    e = {'name': name, 'file': 'props/' + name + '.png', 'pos': pos, 'base_y': int(base_y),
         'collision': [[int(a), int(b)] for a, b in collision], 'normal': bool(normal),
         'emission': bool(info['emission']), 'size': [C.w, C.h]}
    if z:
        e['z'] = z
    if extra:
        e.update(extra)
    return e, pos, (cx0, cy0), C, H


def _plain(o):
    """Convert numpy scalars / tuples recursively into plain JSON types."""
    if isinstance(o, dict):
        return {str(k): _plain(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [_plain(v) for v in o]
    if isinstance(o, np.integer):
        return int(o)
    if isinstance(o, np.floating):
        return round(float(o), 4)
    if isinstance(o, float):
        return round(o, 4)
    return o


def rect_poly(x0, y0, x1, y1):
    return [[x0, y0], [x1, y0], [x1, y1], [x0, y1]]


def save_strip(S: Layer, name):
    os.makedirs(os.path.join(ENV_DIR, 'fx'), exist_ok=True)
    S.save(os.path.join(ENV_DIR, 'fx', name), normal=False, emission=bool(S.em[..., 3].any()))
    return 'fx/' + name + '.png'


def save_actor_png(S: Layer, name, normal=False):
    os.makedirs(os.path.join(ENV_DIR, 'actors'), exist_ok=True)
    S.save(os.path.join(ENV_DIR, 'actors', name), normal=normal, emission=bool(S.em[..., 3].any()))
    return 'res://assets/environments/karsk_railyard/actors/' + name + '.png'


def actor(scene, pos, **props):
    return {'scene': ACTOR_DIR + scene, 'pos': [int(round(pos[0])), int(round(pos[1]))], 'props': props}


def wire_y(pts, x):
    best = min(pts, key=lambda p: abs(p[0] - x))
    return best[1]


def build(preview=True):
    t0 = time.time()
    os.makedirs(ENV_DIR, exist_ok=True)
    os.makedirs(os.path.join(ENV_DIR, '_preview'), exist_ok=True)
    open(os.path.join(ENV_DIR, '_preview', '.gdignore'), 'w').close()
    layers = []
    E = {}
    # ------------------------------------------------------------------ background planes
    sky, y = BG.make_sky()
    e, _, _ = save_layer(sky, 'sky', 0, y, 0.0, -100, lit=False, normal=False, crop=False)
    layers.append(e)
    clouds, y = BG.make_clouds()
    e, _, _ = save_layer(clouds, 'clouds', 0, y, 0.03, -96, lit=False, normal=True)
    layers.append(e)
    fc, y = BG.make_far_city()
    e, fcL, _ = save_layer(fc, 'far_city', 0, y, 0.12, -90, lit=True)
    layers.append(e)
    fi, y = BG.make_far_industry()
    e, fiL, _ = save_layer(fi, 'far_industry', 0, y, 0.25, -84, lit=True)
    layers.append(e)
    mid, y = BG.make_mid()
    e, midL, _ = save_layer(mid, 'mid', 0, y, 0.45, -74, lit=True)
    layers.append(e)
    nb, y = BG.make_near_bg()
    e, nbL, _ = save_layer(nb, 'near_bg', 0, y, 0.72, -60, lit=True)
    layers.append(e)
    po, y = BG.make_poles()
    poles_top = y
    e, poL, _ = save_layer(po, 'poles', 0, y, 0.86, -50, lit=True)
    layers.append(e)
    # ------------------------------------------------------------------ playfield back-line (+ hist variant)
    Eh = {}
    yard = YD.make_yard_back(E, hist=False)
    yard_h = YD.make_yard_back(Eh, hist=True)
    e, ydL, ydH = save_layer(yard, 'yard_back', 0, 0, 1.0, -14, lit=True, hist=yard_h)
    layers.append(e)

    # ------------------------------------------------------------------ props
    props = []
    lamp_heads = []
    for i, (lx, ly) in enumerate(((205, 304), (700, 303), (1185, 304))):
        P, foot, head = YD.lamp_post(variant=1 if i == 1 else 0, emissive=(i != 1))
        ent, pos, (cx0, cy0), _, _ = save_prop(P, 'lamp_post_%d' % (i + 1), foot, (lx, ly), ly,
                                               rect_poly(lx - 4, ly - 3, lx + 5, ly + 1))
        props.append(ent)
        lamp_heads.append((pos[0] + head[0] - cx0, pos[1] + head[1] - cy0))
    P, seal_local, rail_row, winfo = YD.wagon_c17(hist=False)
    Ph, _, _, _ = YD.wagon_c17(hist=True)
    # wheels stand on the near rail of track 1 (y 294); body centred at x ~830
    ent, wpos, (cx0, cy0), WC, WH = save_prop(P, 'wagon_c17', (100, rail_row), (830, 294), 297,
                                              rect_poly(744, 283, 918, 297), hist=Ph)
    props.append(ent)
    seal_world = (wpos[0] + seal_local[0] - cx0, wpos[1] + seal_local[1] - cy0)
    chalk_world = (wpos[0] + winfo['chalk'][0] - cx0, wpos[1] + winfo['chalk'][1] - cy0)
    P, rail_row = YD.flatcar_panels()
    ent, fpos, _, _, _ = save_prop(P, 'flatcar_panels', (98, rail_row), (1802, 272), 276,
                                   rect_poly(1716, 261, 1890, 276))
    props.append(ent)
    P, flame_local, by = YD.fire_barrel_workers()
    ent, bpos, (cx0, cy0), _, _ = save_prop(P, 'fire_barrel', (32, by), (975, 304), 304,
                                            rect_poly(955, 298, 997, 305))
    props.append(ent)
    flame_world = (bpos[0] + flame_local[0] - cx0, bpos[1] + flame_local[1] - cy0)
    barrel_origin = (bpos[0] - cx0, bpos[1] - cy0)          # world position of the prop's local (0, 0)
    P, by = YD.timetable_board()
    ent, tpos, _, _, _ = save_prop(P, 'timetable_board', (22, by), (1068, 306), 306,
                                   rect_poly(1050, 302, 1087, 307))
    props.append(ent)
    P, by = YD.teaching_board()
    ent, sbpos, _, _, _ = save_prop(P, 'teaching_board', (21, by), (1290, 305), 305,
                                    rect_poly(1283, 300, 1299, 306))
    props.append(ent)
    P, by = YD.family_bundles()
    ent, fampos, (cx0, cy0), _, _ = save_prop(P, 'family_bundles', (36, by), (276, 322), 322,
                                              rect_poly(242, 314, 312, 323))
    props.append(ent)
    family_origin = (fampos[0] - cx0, fampos[1] - cy0)
    P, foot, glint_local = LF.crates_with_gap(seed=1)
    ent, cpos, (cx0, cy0), _, _ = save_prop(P, 'crates_a', foot, (1432, 306), 306,
                                            rect_poly(1414, 299, 1452, 307))
    props.append(ent)
    glint_world = (cpos[0] + glint_local[0] - cx0, cpos[1] + glint_local[1] - cy0)
    P, by = YD.crates_stack(seed=2)
    ent, _, _, _, _ = save_prop(P, 'crates_b', (20, by), (640, 302), 302, rect_poly(622, 296, 658, 303))
    props.append(ent)
    P, foot, emb_local = LF.bench_newspaper(hist=False)
    Ph, _, _ = LF.bench_newspaper(hist=True)
    ent, bnpos, (cx0, cy0), BC, BH = save_prop(P, 'bench', foot, (566, 320), 320,
                                               rect_poly(549, 315, 584, 321), hist=Ph)
    props.append(ent)
    # round-2 props: PA pole, snowman, sled, dwarf signal
    P, foot, anchor = LF.loudspeaker_pole()
    pf = YD.PA_POLE_FOOT
    ent, ppos, _, _, _ = save_prop(P, 'loudspeaker_pole', foot, pf, pf[1],
                                   rect_poly(pf[0] - 4, pf[1] - 3, pf[0] + 5, pf[1] + 1))
    props.append(ent)
    P, foot = LF.snowman()
    ent, snpos, _, _, _ = save_prop(P, 'snowman', foot, (350, 339), 339, rect_poly(343, 336, 358, 340))
    props.append(ent)
    P, foot = LF.sled()
    ent, _, _, _, _ = save_prop(P, 'sled', foot, (318, 334), 334, rect_poly(310, 331, 327, 335))
    props.append(ent)
    P, foot = LF.dwarf_signal()
    ent, dpos, _, _, _ = save_prop(P, 'dwarf_signal', foot, (1100, 262), 262, rect_poly(1097, 259, 1104, 263))
    props.append(ent)

    # warm/cold sources whose reflections are baked into the wet ground (x, start row, colours, strength)
    aw = E['amber_window']
    ol = E['office_lamp']
    # baked reflections only where a puddle sits in front of the source (the dynamic lights do the rest)
    warm_sources = [(aw[0] + aw[2] // 2, 254, (CO[3], CO[2]), 0.95),
                    (ol[0], 254, (CO[3], CO[2]), 0.85),
                    (flame_world[0] - 15, 326, (CO[2], CO[1]), 0.8)]
    for (hx, hy) in lamp_heads:
        warm_sources.append((hx - 10, 322, (SK[1], TE[3]), 0.6))
    ground = YD.make_ground(E, [h[0] for h in lamp_heads], warm_sources)
    LF.ground_life(ground, E)
    e, gL, _ = save_layer(ground, 'ground', 0, 0, 1.0, -16, lit=True)
    layers.append(e)
    fg = YD.make_fg()
    e, fgL, _ = save_layer(fg, 'fg_frame', 0, 0, 1.3, 60, lit=False, normal=False)
    layers.append(e)
    layers.sort(key=lambda d: d['z'])

    # ------------------------------------------------------------------ animated fx strips
    fx = []
    strips = {}
    S, org = FX.smoke_ribbon(seed=1)
    strips['smoke_ribbon_a'] = (save_strip(S, 'smoke_ribbon_a'), org, S.w // 8, S.h, 8)
    S, org = FX.smoke_ribbon(seed=2, drift=52.0, w1=18.0)
    strips['smoke_ribbon_b'] = (save_strip(S, 'smoke_ribbon_b'), org, S.w // 8, S.h, 8)
    S, org = FX.smoke_ribbon(seed=3, fw=56, fh=96, cols=[SK[0], SK[1], SK[2], SK[3]], drift=30.0, w1=11.0)
    strips['smoke_ribbon_far'] = (save_strip(S, 'smoke_ribbon_far'), org, S.w // 8, S.h, 8)
    S, org = FX.tower_plume(seed=4)
    strips['tower_plume'] = (save_strip(S, 'tower_plume'), org, S.w // 8, S.h, 8)
    S, org = FX.steam_puffs(seed=5)
    strips['steam_puffs'] = (save_strip(S, 'steam_puffs'), org, S.w // 6, S.h, 6)
    S, org = FX.chimney_wisp(seed=6)
    strips['chimney_wisp'] = (save_strip(S, 'chimney_wisp'), org, S.w // 8, S.h, 8)
    S, org = FX.barrel_flames(seed=7)
    strips['barrel_flames'] = (save_strip(S, 'barrel_flames'), org, S.w // 8, S.h, 8)
    S, org = FX.steam_puffs(seed=8, fw=14, fh=26, spawn=3, grow=3.5, r0=1.0, drift=4.0)
    strips['samovar_steam'] = (save_strip(S, 'samovar_steam'), org, S.w // 6, S.h, 6)

    def anim(key, src_world, parallax, z, fps, layer=None, emission=False, base_y=None, alpha=1.0):
        f, org, fw, fh, n = strips[key]
        pos = [int(src_world[0] - org[0]), int(src_world[1] - org[1])]
        d = {'type': 'anim_sprite', 'file': f, 'frames': n, 'fps': fps, 'pos': pos, 'parallax': parallax,
             'z': z, 'emission': emission, 'frame_size': [fw, fh]}
        if layer:
            d['layer'] = layer
        if base_y is not None:
            d['base_y'] = base_y
        if alpha != 1.0:
            d['alpha'] = alpha
        fx.append(d)

    stacks_fi = [(112, 217 - 118), (130, 217 - 98), (458, 217 - 56 - 78), (432, 217 - 56 - 66), (846, 217 - 26 - 92)]
    for i, (sx, sy) in enumerate(stacks_fi):
        anim('smoke_ribbon_a' if i % 2 == 0 else 'smoke_ribbon_b', (sx, sy), 0.25, -83, 4 + (i % 2),
             layer='far_industry')
    for (sx, sy) in ((688, 207 - 84), (60, 207 - 0)):
        if sy < 200:
            anim('smoke_ribbon_far', (sx, sy), 0.12, -89, 4, layer='far_city')
    anim('tower_plume', (546, 207 - 58), 0.12, -89, 5, layer='far_city')
    anim('tower_plume', (590, 207 - 50), 0.12, -89, 4, layer='far_city')
    anim('smoke_ribbon_far', (884, 231 - 126), 0.45, -73, 4, layer='mid')
    anim('smoke_ribbon_far', (58, 231 - 50 - 64), 0.45, -73, 5, layer='mid')
    anim('chimney_wisp', (4 + 32 + 9, 249 - 66 + 12 - 17), 0.72, -59, 6, layer='near_bg')
    anim('chimney_wisp', (4 + 116 + 9, 249 - 66 + 44 - 17), 0.72, -59, 5, layer='near_bg')
    anim('chimney_wisp', (420, 249 - 46), 0.72, -59, 5, layer='near_bg')
    anim('steam_puffs', (690 + 150, 249 - 78 - 22), 0.72, -59, 5, layer='near_bg')
    anim('chimney_wisp', E['stovepipe_top'], 1.0, -13, 6, layer='yard_back')
    anim('chimney_wisp', E['stall_pipe'], 1.0, -13, 5, layer='yard_back')
    anim('chimney_wisp', E['office_chimney'], 1.0, -13, 5, layer='yard_back')
    anim('samovar_steam', E['samovar'], 1.0, -13, 6, layer='yard_back')        # tea stall samovar in the hatch
    # (barrel flames, sparks and breath are the KarskBarrel actor: y-sorted with the barrel)
    fx = [{'type': 'snow', 'density': 0.55, 'wind': 5.0, 'color_far': hexc(SN[1]), 'color_near': hexc(SN[3])}] + fx
    fx += [
        {'type': 'fog_band', 'y': 204, 'height': 26, 'color': hexc(SK[4]), 'alpha': 0.32, 'parallax': 0.18, 'z': -87},
        {'type': 'fog_band', 'y': 216, 'height': 30, 'color': hexc(SK[3]), 'alpha': 0.30, 'parallax': 0.35, 'z': -80},
        {'type': 'fog_band', 'y': 234, 'height': 28, 'color': hexc(SK[2]), 'alpha': 0.26, 'parallax': 0.6, 'z': -65},
        {'type': 'fog_band', 'y': 276, 'height': 44, 'color': hexc(SK[3]), 'alpha': 0.14, 'parallax': 1.0, 'z': -12},
    ]

    # ------------------------------------------------------------------ lights (lamp 2 belongs to KarskLamp)
    lights = [
        {'id': 'cabin_amber_window', 'pos': [aw[0] + aw[2] // 2, aw[1] + aw[3] + 34], 'color': hexc(CO[3]),
         'energy': 1.0, 'radius': 118, 'flicker': 0.03, 'height': 34, 'on_layer': 'playfield'},
        {'id': 'fire_barrel', 'pos': [flame_world[0], flame_world[1] + 2], 'color': hexc(CO[2]), 'energy': 1.35,
         'radius': 104, 'flicker': 0.22, 'height': 22, 'on_layer': 'playfield'},
        {'id': 'office_lamp', 'pos': [ol[0], ol[1] + 4], 'color': hexc(CO[3]), 'energy': 1.25, 'radius': 104,
         'flicker': 0.02, 'height': 22, 'on_layer': 'playfield'},
    ]
    for i, (hx, hy) in enumerate(lamp_heads):
        if i == 1:
            continue
        lights.append({'id': 'platform_lamp_%d' % (i + 1), 'pos': [hx, hy + 2], 'color': hexc(SN[3]),
                       'energy': 0.45, 'radius': 84, 'flicker': 0.0, 'height': 40, 'on_layer': 'playfield'})
    lights.append({'id': 'distant_red_signal', 'pos': [1662 + 1, poles_top + (252 - 82) - 114 + 1],
                   'color': hexc(RED[3]), 'energy': 0.55, 'radius': 22, 'flicker': 0.0, 'height': 10,
                   'on_layer': 'poles'})

    # ------------------------------------------------------------------ actor sprites
    S, crow_meta = SPR.crows()
    crow_png = save_actor_png(S, 'crows', normal=True)
    S, cat_meta = SPR.cat()
    cat_png = save_actor_png(S, 'cat', normal=True)
    tr = SPR.train()
    loco_png = save_actor_png(tr['loco'], 'train_loco')
    wag_pngs = [save_actor_png(w, 'train_' + w.name) for w in tr['wagons']]
    puff_png = save_actor_png(SPR.smoke_puff_strip(frames=8, size=18, seed=3,
                                                    cols=[TE[3], TE[4], SK[0], SK[1]]), 'train_puff')
    breath_S = SPR.smoke_puff_strip(frames=6, size=6, seed=9, cols=[SN[1], SN[2], SN[3], SN[4]])
    breath_png = save_actor_png(breath_S, 'breath_puff')
    laundry = []
    for (nm, S, cell) in SPR.laundry():
        laundry.append({'file': save_actor_png(S, 'laundry_' + nm, normal=True), 'cell': cell})
    win_png = save_actor_png(SPR.window_silhouettes(), 'window_signalman')
    small_win = []
    for k, (wx, wy, ww, wh, mx, ty) in enumerate(BG.NEAR_LIT_WINDOWS):
        f = save_actor_png(SPR.small_window_silhouettes(ww, wh, mx, ty), 'window_near_%d' % k)
        small_win.append(((wx, wy), f, [ww, wh]))
    glint_png = save_actor_png(SPR.glint_strip(), 'glint')
    cloth_png = save_actor_png(SPR.cloth_flutter_strip(), 'cache_cloth')
    mitten_png = save_actor_png(SPR.mitten_strip(), 'mitten', normal=True)
    bulb_png = save_actor_png(SPR.bulb_glow(), 'lamp_bulb')

    # ------------------------------------------------------------------ actors (§12.2: self-contained scenes)
    pa = E['pa_wire']
    perches = [[x, wire_y(pa, x)] for x in (636, 651, 667, 684)]
    barrel_mouths = [[barrel_origin[0] + 16, barrel_origin[1] + 12], [barrel_origin[0] + 47, barrel_origin[1] + 13]]
    fam_mouths = [[family_origin[0] + 41, family_origin[1] + 11], [family_origin[0] + 15, family_origin[1] + 23]]
    roofs = [[466, 596, 134], [252, 330, 200], [738, 1100, 203], [1100, 1462, 204], [1478, 1688, 171],
             [-2, 252, 214], [1690, 1920, 212]]
    actors = [
        actor('KarskWind.tscn', (0, 0), roofs=roofs),
        actor('KarskCrows.tscn', (660, 258), perches=perches, sprite=crow_png, scare_radius=34.0,
              nervous_radius=80.0),
        actor('KarskCat.tscn', (1007, 307), sprite=cat_png, wake_radius=46.0),
        actor('KarskBarrel.tscn', (975, 304), flames='res://assets/environments/karsk_railyard/fx/barrel_flames.png',
              flame_pos=[flame_world[0], flame_world[1]], flame_frames=8.0, mouths=barrel_mouths, breath=breath_png),
        actor('KarskBreath.tscn', (276, 322), points=fam_mouths, sprite=breath_png, interval=4.6),
        actor('KarskBreath.tscn', (296, 249), points=[[E['samovar'][0] + 18, E['samovar'][1] + 3]],
              sprite=breath_png, interval=5.2, z=-13.0),
        actor('KarskLamp.tscn', (700, 303), sprite=bulb_png,
              bulb_pos=[lamp_heads[1][0] - 2, lamp_heads[1][1] - 1], light_pos=[lamp_heads[1][0], lamp_heads[1][1] + 2],
              light_color=hexc(SN[3]), energy=0.45, radius=84.0, height=40.0),
        actor('KarskTrain.tscn', (0, BG.RAIL_Y_MID), loco=loco_png, wagons=wag_pngs, puff=puff_png, parallax=0.45,
              z=-73.0, span=[-40.0, 1250.0], speed=44.0, interval=[38.0, 50.0], first_delay=4.0,
              chimney=[5.0, -14.0], wagons_min=6.0, wagons_max=9.0),
        actor('KarskLaundry.tscn', (0, 0), items=laundry, pegs=list(BG.LAUNDRY_PEGS), parallax=0.72, z=-59.0),
        actor('KarskWindowLife.tscn', (aw[0], aw[1]), sprite=win_png, cell=[aw[2], aw[3]], z=-13.0),
    ] + [
        actor('KarskWindowLife.tscn', pos, sprite=f, cell=cell, z=-59.0, parallax=0.72, mode='small')
        for (pos, f, cell) in small_win
    ] + [
        actor('KarskGlint.tscn', (glint_world[0], 306), sprite=glint_png, frames=5,
              offset=[-2, glint_world[1] - 306 - 2], period=[4.0, 7.5], mode='glint'),
        actor('KarskGlint.tscn', (E['cache_cloth'][0], E['cache_cloth'][1]), sprite=cloth_png, frames=4,
              offset=[0, 0], period=[0.0, 0.0], mode='gust', z=-13.0),
        actor('KarskGlint.tscn', (1464, 219), sprite=mitten_png, frames=4, offset=[-4, -9], period=[0.0, 0.0],
              mode='gust', z=-13.0, lit=True),
    ]

    # ------------------------------------------------------------------ gameplay data
    hotspots = {
        'irina': [506, 258],
        'seal': [int(seal_world[0]) - 4, 304],
        'timetable': [1068, 314],
        'signal_board': [1290, 314],
        'ledger': [E['counter'][0] + E['counter'][2] // 2, 258],
        'obs_family': [282, 332],
        'obs_stove': [975, 314],
        'obs_poster': [E['poster'][0] + 19, 257],
        # §12.2 exploration hotspots (position = where the player stands to look)
        'exp_barrack': [100, 258],
        'exp_mitten': [1466, 258],
        'exp_grain': [196, 318],
        'exp_stall': [292, 258],
        'exp_snowman': [372, 340],
        'exp_stairs_under': [404, 256],
        'exp_newspaper': [596, 322],
        'exp_crows': [652, 318],
        'exp_loudspeaker': [732, 256],
        'exp_wagon_chalk': [906, 304],
        'exp_workers': [944, 316],
        'exp_cat': [1026, 312],
        'exp_banner': [1220, 258],
        'exp_stash': [1458, 312],
        'exp_kontora_shelf': [1624, 258],
        'exp_cooling_towers': [1120, 330],
        'exp_distant_train': [470, 330],
    }
    hotspot_info = {
        'irina': {'kind': 'dialogue', 'mark': [506, 212], 'radius': 34, 'npc': 'irina', 'facing': 'left'},
        'seal': {'kind': 'inspect', 'mark': [int(seal_world[0]), int(seal_world[1])], 'radius': 30,
                 'document': 'res://assets/ui/documents/karsk_seal.png'},
        'timetable': {'kind': 'inspect', 'mark': [1068, 266], 'radius': 30,
                      'document': 'res://assets/ui/documents/karsk_timetable.png'},
        'signal_board': {'kind': 'puzzle', 'mark': [1291, 258], 'radius': 30,
                         'document': 'res://assets/ui/documents/karsk_signal_board.png'},
        'ledger': {'kind': 'inspect', 'mark': [E['counter'][0] + 16, E['counter'][1] + E['counter'][3] - 2],
                   'radius': 30, 'document': 'res://assets/ui/documents/karsk_ledger.png'},
        'obs_family': {'kind': 'observe', 'mark': [276, 282], 'radius': 34,
                       'prompt_key': 'obs.karsk.family.prompt', 'observe_text_key': 'obs.karsk.family.text'},
        'obs_stove': {'kind': 'observe', 'mark': [975, 266], 'radius': 34,
                      'prompt_key': 'obs.karsk.stove.prompt', 'observe_text_key': 'obs.karsk.stove.text'},
        'obs_poster': {'kind': 'observe', 'mark': [E['poster'][0] + 10, E['poster'][1] + 12], 'radius': 30,
                       'prompt_key': 'obs.karsk.poster.prompt', 'observe_text_key': 'obs.karsk.poster.text'},
        # exploration objects: 'mark' = the object on screen (world px, parallax 1 unless 'layer'),
        # 'radius' = suggested interaction radius, 'hidden' = secret (subtle glint / animated detail only)
        'exp_barrack': {'mark': [82, 186], 'layer': 'near_bg', 'radius': 30,
                        'what': 'two-storey residential barrack: stovepipes through the windows, laundry line (KarskLaundry)'},
        'exp_mitten': {'mark': [1464, 212], 'radius': 26,
                       'what': 'a child\'s red mitten pushed onto the fence post between hoarding and office '
                               '(KarskGlint mode gust)'},
        'exp_grain': {'mark': [190, 120], 'layer': 'mid', 'radius': 30,
                      'what': 'grain elevator: five silos, shell hole and repair patch'},
        'exp_stall': {'mark': [290, 226], 'radius': 30, 'what': 'tea stall ЧАЙ: vendor, steaming samovar'},
        'exp_snowman': {'mark': [350, 318], 'radius': 26,
                        'what': 'snowman with a tin-can ushanka, child footprints around it, sled beside'},
        'exp_stairs_under': {'mark': list(E['cache_mark']), 'radius': 22, 'hidden': True,
                             'what': 'cache under the stairs: loose bricks, oilcloth bundle, red cloth corner that flutters in gusts'},
        'exp_newspaper': {'mark': [570, 304], 'radius': 26,
                          'what': 'newspaper left on the bench, masthead emblem, official stamp'},
        'exp_crows': {'mark': [660, 152], 'radius': 34,
                      'what': 'hooded crows on the PA cable (KarskCrows: nervous at 80 px, fly off at 34 px or when running)'},
        'exp_loudspeaker': {'mark': [722, 160], 'radius': 28, 'what': 'PA pole with two horn loudspeakers'},
        'exp_wagon_chalk': {'mark': [int(chalk_world[0]), int(chalk_world[1])], 'radius': 28,
                            'what': 'chalk tallies, an arrow and a crossed-out mark at the far end of wagon 24-311'},
        'exp_workers': {'mark': [960, 258], 'radius': 28, 'what': 'the two workers at the fire barrel (baked in fire_barrel)'},
        'exp_cat': {'mark': [1007, 300], 'radius': 26, 'what': 'ginger cat curled by the barrel (KarskCat lifts its head)'},
        'exp_banner': {'mark': [1220, 220], 'radius': 34, 'what': 'banner ВОССТАНОВИМ ВМЕСТЕ with the state emblem at both ends'},
        'exp_stash': {'mark': [int(glint_world[0]), int(glint_world[1])], 'radius': 22, 'hidden': True,
                      'what': 'tin box in the gap between the crate stacks (occasional glint)'},
        'exp_kontora_shelf': {'mark': [1624, 214], 'radius': 26, 'what': 'bookshelf behind the freight-office window'},
        'exp_cooling_towers': {'mark': [1250, 175], 'layer': 'far_city', 'radius': 30,
                               'what': 'two cooling towers of the power plant on the horizon, steaming (seen between the depot and the house under repair from here, camera ~800-840)'},
        'exp_distant_train': {'mark': [400, 200], 'layer': 'mid', 'radius': 30,
                              'what': 'goods train on the far embankment (KarskTrain, every ~40-50 s, alternating direction)'},
    }
    manifest = {
        'id': 'karsk_railyard', 'palette': 'karsk', 'world_size': list(WORLD),
        'camera': {'bounds': [0, 0, WORLD[0], WORLD[1]]},
        'canvas_modulate': '#CBD5D3',
        'layers': [{k: v for k, v in l.items() if k != 'size'} for l in layers],
        'props': [{k: v for k, v in p.items() if k != 'size'} for p in props],
        'walkable': [[0, 252], [1920, 252], [1920, 352], [0, 352]],
        'spawns': {'SP_A1_Platform': [120, 312], 'NPC_irina': [506, 256]},
        'hotspots': hotspots,
        'hotspot_info': hotspot_info,
        'lights': lights,
        'fx': fx,
        'actors': actors,
        'notes': {
            'generator': 'tools/pixelgen/env_karsk.py (py -3 -P tools/pixelgen/env_karsk.py)',
            'ground_rows': {'back_strip': [250, 262], 'track_2_rails': [264, 272], 'track_1_rails': [286, 294],
                            'platform_edge': 297, 'platform': [300, 352]},
            'light_on_layer': 'pos of a light with on_layer != playfield is given like a layer pos: where it '
                              'appears when the camera top-left is (0,0); it scrolls with that layer\'s parallax.',
            'anim_sprite': 'horizontal frame strips (frame_size); entries with base_y belong to the y-sorted '
                           'Playfield, the others sit at z between layers and scroll with "parallax".',
            'z_order': 'yard_back (-14) is drawn over ground (-16) so building bases overlap the back strip.',
            'insignia': 'TECHNICAL_ARCHITECTURE 12.4: yard_back.png, props/wagon_c17.png and props/bench.png show '
                        'the fictional gear-and-wheat emblem; their *_hist.png twins (+ _hist_n / _hist_e; identical '
                        'except the emblem pixels) show the hammer & sickle and are picked by LayerStack through '
                        'Symbols.pick (applied at scene load).',
            'actors': 'scenes/levels/karsk/*.tscn (scripts/levels/karsk/*.gd): self-contained ambient life, '
                      'never touches Story/Explore state.',
        },
    }
    manifest = _plain(manifest)
    manifest = apply_skyline(manifest)
    with open(os.path.join(ENV_DIR, 'scene.json'), 'w', encoding='utf-8') as f:
        json.dump(manifest, f, indent=1, ensure_ascii=False)
    # palette discipline report (colour PNGs only)
    bad = {}
    for root, _, files in os.walk(ENV_DIR):
        if '_preview' in root:
            continue
        for fn in files:
            if fn.endswith('.png') and not fn.endswith('_n.png') and not fn.endswith('_e.png'):
                arr = np.asarray(Image.open(os.path.join(root, fn)).convert('RGBA'))
                off = palette_report(arr)
                if off:
                    bad[fn] = off[:6]
    print('palette check:', 'OK' if not bad else bad)
    print('scene built in %.1fs' % (time.time() - t0))
    return manifest


def previews(manifest):
    import env_karsk_preview as PV
    out = os.path.join(ENV_DIR, '_preview')
    for cam in (0, 640, 1280):
        img = PV.compose(ENV_DIR, cam, lit=False)
        PV.save(img, os.path.join(out, 'world_cam%04d.png' % cam))
    pano = np.zeros((360, 1920, 3), np.uint8)
    for cam in range(0, 1281, 64):
        img = PV.compose(ENV_DIR, cam, lit=False)
        pano[:, cam:cam + 640] = img
    PV.save(pano, os.path.join(out, 'world_panorama_scrollstitch.png'))


LOCALE = {
    # optional observations (Alexei: short, precise, dry)
    'obs.karsk.stove.prompt': 'Feuertonne ansehen',
    'obs.karsk.stove.text': 'Alte Schwellen in einer Teertonne. Brennt schlecht, wärmt trotzdem – die Männer '
                            'reden über die Nachtschicht, nicht über die Wagen.',
    'obs.karsk.poster.prompt': 'Aushänge lesen',
    'obs.karsk.poster.text': 'Neue Wohnblocks bis zum Herbst, verspricht das Plakat. Die Warteliste daneben ist '
                             'mit Bleistift verlängert worden.',
    'obs.karsk.family.prompt': 'Wartende Familie ansehen',
    'obs.karsk.family.text': 'Drei Generationen, vier Bündel, eine Holzkiste. Sie warten, wie man hier wartet: '
                             'ohne zu fragen.',
    # inspect-UI document titles / reading-mode descriptions (karsk_documents.json)
    'doc.karsk.signal_board.title': 'Übungskasten – stromloses Lehrmodell',
    'doc.karsk.seal.alt': 'Bleiplombe an der Wagentür: Stationsstempel doppelt eingeschlagen, darunter '
                          'abgeschabt „C-17“. Daneben eingeritzt: Quadrat, Kreis, Dreieck.',
    'doc.karsk.timetable.alt': 'Dienstfahrplan: drei umgebuchte Wagenzeilen ohne Zielbahnhof, am Rand markiert '
                               'mit Quadrat, Kreis und Dreieck – von oben nach unten.',
    'doc.karsk.ledger.alt': 'Frachtbuch: eine neue Zeile für Wagen 24-311 mit rotem Stempel „C-17“. Der '
                            'Empfänger ist geschwärzt.',
    'doc.karsk.signal_board.alt': 'Stromloser Übungskasten mit drei leeren Kartenschächten, toter Kontrolllampe '
                                  'und Beispielschema. Kein Teil einer echten Signalanlage.',
}


def write_locale():
    path = os.path.join(ROOT, 'data', 'locale', 'de_env_karsk.json')
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump({'locale': 'de-DE', 'area': 'env_karsk', 'strings': LOCALE}, f, indent=1, ensure_ascii=False)
    print('locale:', path, len(LOCALE), 'strings')



def apply_skyline(manifest):
    """Round-2 skyline (tools/pixelgen/env_karsk_skyline.py -> assets/environments/karsk_skyline/): if present,
    its four background planes, their smoke/steam and the laundry pegs replace this generator's own versions,
    so re-running env_karsk.py keeps the realistic Soviet skyline (user feedback 2026-11-04)."""
    sk_path = os.path.join(os.path.dirname(ENV_DIR), 'karsk_skyline', 'skyline.json')
    if not os.path.exists(sk_path):
        return manifest
    with open(sk_path, encoding='utf-8') as f:
        sk = json.load(f)
    planes = {'far_city', 'far_industry', 'mid', 'near_bg'}
    new_layers = {l['name']: l for l in sk.get('layers', [])}
    manifest['layers'] = [new_layers.get(l['name'], l) if l['name'] in planes else l for l in manifest['layers']]
    manifest['fx'] = [x for x in manifest.get('fx', []) if x.get('layer') not in planes] + sk.get('fx', [])
    for a in manifest.get('actors', []):
        if str(a.get('scene', '')).endswith('KarskLaundry.tscn') and sk.get('laundry_pegs'):
            a.setdefault('props', {})['pegs'] = sk['laundry_pegs']
    info = manifest.get('hotspot_info', {})
    for k, v in sk.get('hotspot_marks', {}).items():
        if isinstance(info.get(k), dict):
            info[k]['mark'] = v
    return manifest

if __name__ == '__main__':
    man = build()
    write_locale()
    if '--docs' in sys.argv:
        import env_karsk_docs as DOCS
        DOCS.build_all()
    if '--no-preview' not in sys.argv:
        previews(man)
        print('previews written to', os.path.join(ENV_DIR, '_preview'))
