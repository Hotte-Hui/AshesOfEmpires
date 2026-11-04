"""env_karsk -- generator for scene A1 'Verladebahnhof Karsk' (fictional Soviet railway town, winter
dawn, 1964).  Reproduce everything with:

    py -3 -P tools/pixelgen/env_karsk.py            (art + scene.json + documents + locale + previews)
    py -3 -P tools/pixelgen/env_karsk.py --no-preview

Outputs (area env_karsk):
    assets/environments/karsk_railyard/*.png (+ _n normal maps, _e emission masks), props/, fx/
    assets/environments/karsk_railyard/scene.json         (TECHNICAL_ARCHITECTURE 3.1)
    assets/ui/documents/karsk_*.png + karsk_documents.json (inspect-UI document art, 1:1 pixels)
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

import pg  # noqa: E402
from env_karsk_lib import (ENV_DIR, ROOT, Layer, crop_v, crop_box, palette_report, NI, TE, SA, SK, ST, RU,  # noqa: E402
                           CO, SN, WO, RED)
import env_karsk_bg as BG  # noqa: E402
import env_karsk_yard as YD  # noqa: E402
import env_karsk_fx as FX  # noqa: E402

WORLD = (1920, 360)


def hexc(c):
    return '#%02X%02X%02X' % (int(c[0]), int(c[1]), int(c[2]))


EMISSION_STRENGTH = {'far_city': 0.35, 'far_industry': 0.35, 'mid': 0.45, 'near_bg': 0.45, 'poles': 0.7,
                     'yard_back': 0.16, 'ground': 0.25}


def save_layer(L: Layer, name, pos_x, pos_y, parallax, z, lit=True, normal=True, crop=True, strength=3.0,
               repeat_x=0):
    if crop:
        L, dy = crop_v(L)
        pos_y += dy
    base = os.path.join(ENV_DIR, name)
    info = L.save(base, normal=normal, strength=strength)
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
    return entry, L


def save_prop(P: Layer, name, foot_local, foot_world, base_y, collision, z=0, normal=True, extra=None):
    """Crop the prop to content and place it so foot_local (x, y in the uncropped sprite) lands on
    foot_world.  Returns the manifest entry."""
    C, cx0, cy0 = crop_box(P, pad=0)
    fx, fy = foot_local
    pos = [int(foot_world[0] - (fx - cx0)), int(foot_world[1] - (fy - cy0))]
    os.makedirs(os.path.join(ENV_DIR, 'props'), exist_ok=True)
    info = C.save(os.path.join(ENV_DIR, 'props', name), normal=normal, strength=3.0)
    e = {'name': name, 'file': 'props/' + name + '.png', 'pos': pos, 'base_y': int(base_y),
         'collision': [[int(a), int(b)] for a, b in collision], 'normal': bool(normal),
         'emission': bool(info['emission']), 'size': [C.w, C.h]}
    if extra:
        e.update(extra)
    return e, pos, (cx0, cy0)


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


def build(preview=True):
    t0 = time.time()
    os.makedirs(ENV_DIR, exist_ok=True)
    os.makedirs(os.path.join(ENV_DIR, '_preview'), exist_ok=True)
    open(os.path.join(ENV_DIR, '_preview', '.gdignore'), 'w').close()
    layers = []
    E = {}
    # ------------------------------------------------------------------ background planes
    sky, y = BG.make_sky()
    e, _ = save_layer(sky, 'sky', 0, y, 0.0, -100, lit=False, normal=False, crop=False)
    layers.append(e)
    clouds, y = BG.make_clouds()
    e, _ = save_layer(clouds, 'clouds', 0, y, 0.03, -96, lit=False, normal=True)
    layers.append(e)
    fc, y = BG.make_far_city()
    e, fcL = save_layer(fc, 'far_city', 0, y, 0.12, -90, lit=True)
    layers.append(e)
    fi, y = BG.make_far_industry()
    e, fiL = save_layer(fi, 'far_industry', 0, y, 0.25, -84, lit=True)
    layers.append(e)
    mid, y = BG.make_mid()
    e, midL = save_layer(mid, 'mid', 0, y, 0.45, -74, lit=True)
    layers.append(e)
    nb, y = BG.make_near_bg()
    e, nbL = save_layer(nb, 'near_bg', 0, y, 0.72, -60, lit=True)
    layers.append(e)
    po, y = BG.make_poles()
    poles_top = y
    e, poL = save_layer(po, 'poles', 0, y, 0.86, -50, lit=True)
    layers.append(e)
    poles_entry = e
    # ------------------------------------------------------------------ playfield back-line + ground
    yard = YD.make_yard_back(E)
    e, ydL = save_layer(yard, 'yard_back', 0, 0, 1.0, -14, lit=True)
    layers.append(e)

    # props first (we need lamp heads for the ground reflections)
    props = []
    lamp_heads = []
    for i, (lx, ly) in enumerate(((205, 304), (700, 303), (1185, 304))):
        P, foot, head = YD.lamp_post(variant=1 if i == 1 else 0)
        ent, pos, (cx0, cy0) = save_prop(P, 'lamp_post_%d' % (i + 1), foot, (lx, ly), ly,
                                         rect_poly(lx - 4, ly - 3, lx + 5, ly + 1))
        props.append(ent)
        lamp_heads.append((pos[0] + head[0] - cx0, pos[1] + head[1] - cy0))
    P, seal_local, rail_row = YD.wagon_c17()
    # wheels stand on the near rail of track 1 (y 294); body centred at x ~830
    ent, wpos, (cx0, cy0) = save_prop(P, 'wagon_c17', (100, rail_row), (830, 294), 297,
                                      rect_poly(744, 283, 918, 297))
    props.append(ent)
    seal_world = (wpos[0] + seal_local[0] - cx0, wpos[1] + seal_local[1] - cy0)
    P, rail_row = YD.flatcar_panels()
    ent, fpos, _ = save_prop(P, 'flatcar_panels', (98, rail_row), (1802, 272), 276,
                             rect_poly(1716, 261, 1890, 276))
    props.append(ent)
    P, flame_local, by = YD.fire_barrel_workers()
    ent, bpos, (cx0, cy0) = save_prop(P, 'fire_barrel', (32, by), (975, 304), 304,
                                      rect_poly(955, 298, 997, 305))
    props.append(ent)
    flame_world = (bpos[0] + flame_local[0] - cx0, bpos[1] + flame_local[1] - cy0)
    P, by = YD.timetable_board()
    ent, tpos, _ = save_prop(P, 'timetable_board', (22, by), (1068, 306), 306,
                             rect_poly(1050, 302, 1087, 307))
    props.append(ent)
    P, by = YD.teaching_board()
    ent, sbpos, _ = save_prop(P, 'teaching_board', (21, by), (1290, 305), 305,
                              rect_poly(1283, 300, 1299, 306))
    props.append(ent)
    P, by = YD.family_bundles()
    ent, fampos, _ = save_prop(P, 'family_bundles', (36, by), (276, 322), 322,
                               rect_poly(242, 314, 312, 323))
    props.append(ent)
    P, by = YD.crates_stack(seed=1)
    ent, _, _ = save_prop(P, 'crates_a', (20, by), (1432, 306), 306, rect_poly(1414, 299, 1450, 307))
    props.append(ent)
    P, by = YD.crates_stack(seed=2)
    ent, _, _ = save_prop(P, 'crates_b', (20, by), (640, 302), 302, rect_poly(622, 296, 658, 303))
    props.append(ent)
    P, by = YD.bench()
    ent, _, _ = save_prop(P, 'bench', (18, by), (566, 320), 320, rect_poly(549, 315, 584, 321))
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
    gL, gdy = crop_v(ground)
    e, gL = save_layer(ground, 'ground', 0, 0, 1.0, -16, lit=True)
    layers.append(e)
    fg = YD.make_fg()
    e, fgL = save_layer(fg, 'fg_frame', 0, 0, 1.3, 60, lit=False, normal=False)
    layers.append(e)
    # order layers by z for readability
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
    strips['barrel_flames'] = (save_strip(S, 'barrel_flames'), org, S.w // 6, S.h, 6)

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

    # far industry stacks (layer coords == pos at cam 0); mouths read from BG layout constants
    fi_top = [l for l in layers if l['name'] == 'far_industry'][0]['pos'][1]
    mid_top = [l for l in layers if l['name'] == 'mid'][0]['pos'][1]
    fc_top = [l for l in layers if l['name'] == 'far_city'][0]['pos'][1]
    nb_top = [l for l in layers if l['name'] == 'near_bg'][0]['pos'][1]
    stacks_fi = [(112, 217 - 118), (130, 217 - 98), (458, 217 - 56 - 78), (432, 217 - 56 - 66), (846, 217 - 26 - 92)]
    for i, (sx, sy) in enumerate(stacks_fi):
        anim('smoke_ribbon_a' if i % 2 == 0 else 'smoke_ribbon_b', (sx, sy), 0.25, -83, 4 + (i % 2),
             layer='far_industry')
    for (sx, sy) in ((688, 207 - 84), (60, 207 - 0)):
        if sy < 200:
            anim('smoke_ribbon_far', (sx, sy), 0.12, -89, 4, layer='far_city')
    anim('tower_plume', (546, 207 - 58), 0.12, -89, 5, layer='far_city')
    anim('tower_plume', (662, 207 - 50), 0.12, -89, 4, layer='far_city')
    anim('smoke_ribbon_far', (884, 231 - 126), 0.45, -73, 4, layer='mid')
    anim('smoke_ribbon_far', (58, 231 - 50 - 64), 0.45, -73, 5, layer='mid')
    # near: barrack stovepipes, shed pipe (near_bg), depot lantern steam
    anim('chimney_wisp', (4 + 32 + 9, 249 - 66 + 12 - 17), 0.72, -59, 6, layer='near_bg')
    anim('chimney_wisp', (4 + 116 + 9, 249 - 66 + 44 - 17), 0.72, -59, 5, layer='near_bg')
    anim('chimney_wisp', (420, 249 - 46), 0.72, -59, 5, layer='near_bg')
    anim('steam_puffs', (690 + 150, 249 - 78 - 22), 0.72, -59, 5, layer='near_bg')
    # playfield: signal box stovepipe, tea stall pipe + samovar, office chimney, barrel flames
    anim('chimney_wisp', E['stovepipe_top'], 1.0, -13, 6, layer='yard_back')
    anim('chimney_wisp', E['stall_pipe'], 1.0, -13, 5, layer='yard_back')
    anim('chimney_wisp', E['office_chimney'], 1.0, -13, 5, layer='yard_back')
    anim('barrel_flames', flame_world, 1.0, 0, 10, layer='playfield', emission=True, base_y=304)
    anim('steam_puffs', (flame_world[0] + 2, flame_world[1] - 12), 1.0, 0, 6, layer='playfield', base_y=304,
         alpha=0.85)
    fx = [{'type': 'snow', 'density': 0.55, 'wind': 5.0, 'color_far': hexc(SN[1]), 'color_near': hexc(SN[3])}] + fx
    # fog bands: 'y' is the band centre (layer_stack._build_fog), parallax between the planes they separate
    fx += [
        {'type': 'fog_band', 'y': 204, 'height': 26, 'color': hexc(SK[4]), 'alpha': 0.32, 'parallax': 0.18, 'z': -87},
        {'type': 'fog_band', 'y': 216, 'height': 30, 'color': hexc(SK[3]), 'alpha': 0.30, 'parallax': 0.35, 'z': -80},
        {'type': 'fog_band', 'y': 234, 'height': 28, 'color': hexc(SK[2]), 'alpha': 0.26, 'parallax': 0.6, 'z': -65},
        {'type': 'fog_band', 'y': 276, 'height': 44, 'color': hexc(SK[3]), 'alpha': 0.14, 'parallax': 1.0, 'z': -12},
    ]

    # ------------------------------------------------------------------ lights
    lights = [
        # placed below the window: lights the wall, the door, Irina and the wet back strip, not the glass
        {'id': 'cabin_amber_window', 'pos': [aw[0] + aw[2] // 2, aw[1] + aw[3] + 34], 'color': hexc(CO[3]),
         'energy': 1.0, 'radius': 118, 'flicker': 0.03, 'height': 34, 'on_layer': 'playfield'},
        {'id': 'fire_barrel', 'pos': [flame_world[0], flame_world[1] + 2], 'color': hexc(CO[2]), 'energy': 1.35,
         'radius': 104, 'flicker': 0.22, 'height': 22, 'on_layer': 'playfield'},
            {'id': 'office_lamp', 'pos': [ol[0], ol[1] + 4], 'color': hexc(CO[3]), 'energy': 1.25, 'radius': 104,
         'flicker': 0.02, 'height': 22, 'on_layer': 'playfield'},
    ]
    for i, (hx, hy) in enumerate(lamp_heads):
        lights.append({'id': 'platform_lamp_%d' % (i + 1), 'pos': [hx, hy + 2], 'color': hexc(SN[3]),
                       'energy': 0.45, 'radius': 84, 'flicker': 0.0 if i != 1 else 0.04, 'height': 40,
                       'on_layer': 'playfield'})
    lights.append({'id': 'distant_red_signal', 'pos': [1662 + 1, poles_top + (252 - 82) - 114 + 1],
                   'color': hexc(RED[3]), 'energy': 0.55, 'radius': 22, 'flicker': 0.0, 'height': 10,
                   'on_layer': 'poles'})

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
        'notes': {
            'generator': 'tools/pixelgen/env_karsk.py (py -3 -P tools/pixelgen/env_karsk.py)',
            'ground_rows': {'back_strip': [250, 262], 'track_2_rails': [264, 272], 'track_1_rails': [286, 294],
                            'platform_edge': 297, 'platform': [300, 352]},
            'light_on_layer': 'pos of a light with on_layer != playfield is given like a layer pos: where it '
                              'appears when the camera top-left is (0,0); it scrolls with that layer\'s parallax.',
            'anim_sprite': 'horizontal frame strips (frame_size); entries with base_y belong to the y-sorted '
                           'Playfield, the others sit at z between layers and scroll with "parallax".',
            'z_order': 'yard_back (-14) is drawn over ground (-16) so building bases overlap the back strip.',
        },
    }
    manifest = _plain(manifest)
    with open(os.path.join(ENV_DIR, 'scene.json'), 'w', encoding='utf-8') as f:
        json.dump(manifest, f, indent=1, ensure_ascii=False)
    # palette discipline report
    bad = {}
    for root, _, files in os.walk(ENV_DIR):
        if '_preview' in root:
            continue
        for fn in files:
            if fn.endswith('.png') and not fn.endswith('_n.png') and not fn.endswith('_e.png'):
                from PIL import Image
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
        PV.save(img, os.path.join(out, 'world_cam%04d_x2.png' % cam), 2)
        lit = PV.compose(ENV_DIR, cam, lit=True)
        PV.save(lit, os.path.join(out, 'world_cam%04d_lit.png' % cam))
    # 3x crops of the key areas
    crops = {
        'crop_cabin_irina': (0, (400, 110, 640, 300)),
        'crop_stall_family': (0, (180, 180, 380, 350)),
        'crop_wagon_seal': (640, (80, 170, 330, 330)),
        'crop_barrel_timetable': (640, (290, 220, 500, 340)),
        'crop_board_poster': (1280, (0, 190, 200, 330)),
        'crop_office_ledger': (1280, (190, 150, 420, 300)),
        'crop_sky_sun': (0, (430, 40, 640, 220)),
        'crop_fg_truck': (0, (0, 230, 200, 360)),
        'crop_fg_tree': (1280, (440, 100, 640, 360)),
    }
    for name, (cam, box) in crops.items():
        img = PV.compose(ENV_DIR, cam, lit=False)
        PV.crop3(img, box, os.path.join(out, name + '_x3.png'))
    # full panorama at world scale (cam positions stitched with the parallax formula per column band)
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


if __name__ == '__main__':
    man = build()
    write_locale()
    try:
        import env_karsk_docs as DOCS
        DOCS.build_all()
    except ImportError:
        print('documents module missing (skipped)')
    if '--no-preview' not in sys.argv:
        previews(man)
        print('previews written to', os.path.join(ENV_DIR, '_preview'))
