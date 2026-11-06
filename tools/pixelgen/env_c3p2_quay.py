"""env_c3p2_quay -- generator of L_C3_Quay „Am Kai hinter dem Palais, Veltrava (fiktiv)“ (Chapter 3 part 2,
Alexei, side view, ~2.20 a.m.): the riverside quay behind the palais in the night of the registry fire.
Area env_c3p2_night (documentation/asset_manifest_parts/env_c3p2_night.md).  Contract: C3P2_DESIGN.md §5.2.

Run:  py -3 -P tools/pixelgen/env_c3p2_quay.py [--preview=DIR]     (deterministic, no network, no inputs)

Writes assets/environments/veltrava_quay/: layers (+ _n normal / _e emission maps), props/ (+ *_hist pennant
variants of the two delegation cars), life/ (looping figure and light strips = decals), fx/ (smoke, steam,
chimneys, exhaust = anim_sprite fx), scene.json (TECHNICAL_ARCHITECTURE §3.1; keeps every spawn / hotspot name of
the story shell) and provenance.json.  Never touches explore_hotspots.json (exploration stream).
Modules: _kit (palette ladders, deferred night bake, light fields, glow), _far (sky, smoke pall, the Line, river +
bridge, old town), _near (burning wing, promenade, fg, glow, props), _life (figures, lights, smoke strips).
--preview renders CPU composites (no Godot lighting) at cameras 0/320/640/960/1280 into DIR.
"""
from __future__ import annotations

import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import numpy as np  # noqa: E402
from PIL import Image  # noqa: E402

import env_c3p2_quay_kit as K  # noqa: E402
import env_c3p2_quay_far as F  # noqa: E402
import env_c3p2_quay_near as N  # noqa: E402
import env_c3p2_quay_life as LF  # noqa: E402
from env_c3p2_quay_kit import ENV_DIR, ROOT, hexc, NI, SL, IR, CR, PA, LA, SK, SN, RD  # noqa: E402

LF_ = chr(10)
CANVAS_MODULATE = '#BCC3D2'
PRODUCED: list = []
# story contract (C3P2_DESIGN.md §5.2) -- names and positions are binding
HOTSPOTS = {'bench': [760, 300], 'konrad_quay': [800, 300], 'typist_quay': [330, 300], 'guard_quay': [1050, 300],
            'kessler_quay': [1180, 300], 'voronova_quay': [1330, 300], 'journalist_quay': [1560, 300]}
SPAWNS = {'SP_C3_Quay': [560, 300]}
ZONES = {'burning_wing': [0, 420], 'promenade': [420, 1100], 'cars': [1100, 1520], 'bridge': [1520, 1920]}
# story NPC feet = hotspot + hotspot_offset of scenes/levels/L_C3_Quay.tscn
NPC_FEET = {'konrad': [818, 300], 'typist': [344, 300], 'border_officer': [1050, 300], 'kessler': [1180, 300],
            'voronova': [1344, 300], 'journalist': [1574, 300]}
Z = {'sky': -100, 'pall': -58, 'far_bank': -96, 'river': -94, 'oldtown': -90, 'wing': -60, 'promenade': -50,
     'glow_air': 30, 'fg': 60}
EMISSION_STRENGTH = {'far_bank': 0.5, 'river': 0.5, 'oldtown': 0.55, 'wing': 0.6, 'promenade': 0.6}


def rel(p):
    return os.path.relpath(p, ROOT).replace('\\', '/')


def record(path, gen, desc):
    PRODUCED.append((rel(path), 'tools/pixelgen/' + gen, desc))


def clean_env():
    if not os.path.isdir(ENV_DIR):
        return
    for root, _d, files in os.walk(ENV_DIR):
        if '_preview' in root:
            continue
        for f in files:
            if f.endswith('.png'):
                os.remove(os.path.join(root, f))


def drop_orphan_imports():
    for root, _d, files in os.walk(ENV_DIR):
        for f in files:
            if f.endswith('.png.import') and not os.path.exists(os.path.join(root, f[:-7])):
                os.remove(os.path.join(root, f))


def _save(L, relpath, normal, gen, desc, hist=None):
    base = os.path.join(ENV_DIR, relpath)
    os.makedirs(os.path.dirname(base), exist_ok=True)
    info = L.save(base, normal=normal, emission=None)
    record(base + '.png', gen, desc)
    if normal:
        record(base + '_n.png', gen, desc + ' -- normal map (OpenGL +Y up)')
    if info['emission']:
        record(base + '_e.png', gen, desc + ' -- emission mask (added unshaded)')
    if hist is not None:
        Image.fromarray(hist.c, 'RGBA').save(base + '_hist.png')
        record(base + '_hist.png', gen, desc + ' -- historical insignia variant (Symbols.pick, §12.4)')
    return info


def layer_entry(L, name, p, crop, normal, lit, gen, desc, extra=None):
    px = py = 0
    if crop == 'v':
        L, py = K.crop_v(L)
    elif crop == 'box':
        L, px, py = K.crop_box(L)
    info = _save(L, name, normal, gen, desc)
    e = {'name': name, 'file': name + '.png', 'pos': [int(px), int(py)], 'parallax': [p, 1.0], 'z': Z[name],
         'normal': bool(normal), 'emission': bool(info['emission']), 'lit': bool(lit), 'repeat_x': 0}
    if info['emission'] and name in EMISSION_STRENGTH:
        e['emission_strength'] = EMISSION_STRENGTH[name]
    if extra:
        e.update(extra)
    e['note'] = desc
    return e, (px, py), L


def prop_entry(L, name, base_y, desc, hist=None, gen='env_c3p2_quay_near.py', origin=(0, 0)):
    C, cx0, cy0 = K.crop_box(L)
    H = None
    if hist is not None:
        H = K.sub_layer(hist, cx0, cy0, C.w, C.h)
    info = _save(C, 'props/' + name, True, gen, desc, hist=H)
    e = {'name': name, 'file': 'props/%s.png' % name, 'pos': [int(origin[0] + cx0), int(origin[1] + cy0)],
         'base_y': int(base_y), 'collision': [], 'normal': True, 'emission': bool(info['emission']),
         'size': [C.w, C.h], 'note': desc}
    if H is not None:
        e['hist_variant'] = 'props/%s_hist.png' % name
    return e


def decal_entry(S, name, box, frames, fps, desc, layer='playfield', base_y=None, lit=True, normal=True,
                emission=None, z=0, layer_home=(0, 0), emission_strength=None, alpha=None, figures=None):
    has_em = bool(S.em[..., 3].any())
    em = has_em if emission is None else emission
    _save(S, 'life/' + name, normal, 'env_c3p2_quay_life.py', desc)
    pos = [int(box[0] + layer_home[0]), int(box[1] + layer_home[1])]
    d = {'name': name, 'file': 'life/%s.png' % name, 'pos': pos, 'frames': int(frames), 'fps': fps,
         'layer': layer, 'z': z, 'lit': bool(lit), 'normal': bool(normal), 'emission': bool(em), 'note': desc}
    if base_y is not None:
        d['base_y'] = int(base_y)
    if emission_strength is not None:
        d['emission_strength'] = emission_strength
    if alpha is not None:
        d['alpha'] = alpha
    if figures:
        d['figures'] = [list(f) for f in figures]
    return d


def fx_entry(S, name, box, frames, fps, p, z, desc, alpha=None, layer_home=(0, 0)):
    _save(S, 'fx/' + name, False, 'env_c3p2_quay_life.py', desc)
    d = {'type': 'anim_sprite', 'file': 'fx/%s.png' % name, 'frames': int(frames), 'fps': fps,
         'pos': [int(box[0] + layer_home[0]), int(box[1] + layer_home[1])], 'parallax': [p, 1.0], 'z': z,
         'lit': False, 'frame_size': [S.w // frames, S.h], 'note': desc}
    if alpha is not None:
        d['alpha'] = alpha
    return d


# ===================================================================================================== build
def build():
    t0 = time.time()
    os.makedirs(ENV_DIR, exist_ok=True)
    clean_env()
    lights = N.scene_lights()
    layers, props, decals, fx = [], [], [], []
    homes = {}
    # ---------------------------------------------------------------- far planes (unlit)
    L, _ = F.make_sky()
    e, h, _ = layer_entry(L, 'sky', F.P['sky'], 'v', False, False, 'env_c3p2_quay_far.py',
                          'overcast snow night over the river, faint cold glow of the floodlights on the horizon')
    layers.append(e)
    L, pinfo = F.make_pall()
    e, h, _ = layer_entry(L, 'pall', F.P['pall'], 'box', False, False, 'env_c3p2_quay_far.py',
                          'the smoke pall of the burning east wing: fire-lit belly, drifting right over the river')
    layers.append(e)
    L, fb = F.make_far_bank()
    e, h, _ = layer_entry(L, 'far_bank', F.P['far_bank'], 'v', False, False, 'env_c3p2_quay_far.py',
                          'the far bank: hills, the Line (double fence, floodlight masts, five watchtowers)')
    layers.append(e)
    homes['far_bank'] = h
    L, rv = F.make_river()
    e, h, _ = layer_entry(L, 'river', F.P['river'], 'v', False, False, 'env_c3p2_quay_far.py',
                          'the frozen river: drifts, pressure ridges, the open lead; the three-arch bridge with its '
                          'lamps, the barrier and the guard hut of the Line')
    layers.append(e)
    L, ot = F.make_oldtown()
    e, h, _ = layer_entry(L, 'oldtown', F.P['oldtown'], 'box', False, False, 'env_c3p2_quay_far.py',
                          'the old town of our bank behind the bridge approach: gables, warm windows, church tower '
                          'with a lit clock')
    layers.append(e)
    homes['oldtown'] = h
    # ---------------------------------------------------------------- near planes (lit)
    L, wi = N.make_wing(lights)
    e, h, _ = layer_entry(L, 'wing', 1.0, 'box', True, True, 'env_c3p2_quay_near.py',
                          'the corner of the burning east wing (Kurhaus 1909): fire in the souterrain windows, '
                          'mirrored in the dark upper windows, one lit dormer; yard railing, open gate, the coal '
                          'hatch they came out of, coal dust and two body prints in the snow')
    layers.append(e)
    homes['wing'] = h
    L, pr = N.make_promenade(lights)
    e, h, _ = layer_entry(L, 'promenade', 1.0, 'v', True, True, 'env_c3p2_quay_near.py',
                          'the quay: snow, hoses, tyre tracks, two men\'s footprints from the hatch to the bench, '
                          'the balustrade with six lanterns, snowed-in benches, bridgehead pylon with the city arms, '
                          'ramp wall, tram stop + shelter, catenary')
    layers.append(e)
    L, _ = N.make_glow()
    e, h, _ = layer_entry(L, 'glow_air', 1.0, 'box', False, False, 'env_c3p2_quay_near.py',
                          'soft halos in the snowy air (lanterns, fire, headlight): additive, alpha in dithered steps',
                          extra={'blend': 'add', 'alpha': 0.9})
    layers.append(e)
    L, _ = N.make_fg()
    e, h, _ = layer_entry(L, 'fg', N.P_FG, 'v', False, False, 'env_c3p2_quay_near.py',
                          'low dark snow banks and bollards along the bottom edge (never above y 318)')
    layers.append(e)
    layers.sort(key=lambda d: d['z'])
    # ---------------------------------------------------------------- props
    L, tr = N.make_fire_engine(lights)
    props.append(prop_entry(L, 'fire_engine', N.TRUCK['ground'], 'ladder truck of the Veltrava fire brigade, '
                            'turntable ladder at a first-floor window, the city arms on the cab door, the '
                            'roller-shutter equipment locker behind the cab', origin=tr['origin']))
    for kind in ('reich', 'ussr'):
        L, Lh, ci = N._car(lights, kind)
        props.append(prop_entry(L, 'car_' + kind, 293, 'black delegation car (%s) with its fender pennant (neutral; '
                                '_hist = historical insignia)' % ('Reich' if kind == 'reich' else 'USSR'),
                                hist=Lh, origin=ci['origin']))
    L, bi = N.make_bench_file(lights)
    props.append(prop_entry(L, 'bench_file', 294, 'the bench at x 760: the file burst open on the seat, two fans '
                            'of sheets, the red C-17 tag, sheets in the snow, soot smudges', origin=bi['origin']))
    L, ti = N.make_trestle(lights)
    props.append(prop_entry(L, 'trestle', 293, 'the commission guard\'s striped trestle barrier (onlookers behind it)',
                            origin=ti['origin']))
    # ---------------------------------------------------------------- life decals
    S, box = LF.hose_team(lights)
    decals.append(decal_entry(S, 'hose_team', box, 12, 8, 'two firemen at the yard gate, the jet arcing into the '
                              'first souterrain window', base_y=293, figures=[(128, 293), (150, 293)]))
    S, box = LF.ladder_man(lights)
    decals.append(decal_entry(S, 'ladder_man', box, 8, 5, 'a fireman on the turntable ladder at a first-floor window',
                              base_y=293, figures=[(208, 130)]))
    S, box = LF.pump_man(lights)
    decals.append(decal_entry(S, 'pump_man', box, 16, 5, 'the machinist at the pump panel (looks round, works a '
                              'lever)', base_y=294, figures=[(276, 293)]))
    S, box = LF.onlookers(lights)
    decals.append(decal_entry(S, 'onlookers', box, 24, 5, 'woken neighbours behind the trestle: a woman in a coat over '
                              'her nightdress, an old man who points at the fire, a boy on tiptoe', base_y=291,
                              figures=[(1062, 291), (1076, 291), (1100, 291)]))
    for kind in ('kessler', 'voronova'):
        S, box = LF.aide(lights, kind)
        decals.append(decal_entry(S, 'aide_' + kind, box, 16, 5, '%s\'s aide, waiting apart (%s)' % (
            kind.capitalize(), 'briefcase, looks at his watch' if kind == 'kessler' else 'folder, rubs his hands'),
            base_y=294, figures=[(1150 if kind == 'kessler' else 1376, 294)]))
    S, box = LF.drivers(lights)
    decals.append(decal_entry(S, 'drivers', box, 32, 6, 'the two chauffeurs share one lighter between the cars '
                              '(flame < 3 Hz), then smoke', base_y=292, emission_strength=0.6,
                              figures=[(1252, 293), (1272, 293)]))
    S, box = LF.beacon(tr['beacon'])
    decals.append(decal_entry(S, 'beacon', box, 8, 8, 'blue rotating lamp on the cab roof (one turn per second, '
                              'no flash)', base_y=293, lit=False, normal=False, emission_strength=0.7))
    wing_home = homes['wing']
    for k, c in enumerate(N.BASE_WIN):
        S, box = LF.window_fire(c, lights)
        decals.append(decal_entry(S, 'fire_win_%d' % (k + 1), box, 8, 6, 'flames licking out of souterrain window '
                                  '%d' % (k + 1), layer='wing', lit=False, normal=False, z=2,
                                  emission_strength=0.75))
    for k, c in enumerate(N.BASE_WIN[:3]):
        S, box = LF.embers(c, 960 + k)
        decals.append(decal_entry(S, 'embers_%d' % (k + 1), box, 16, 8, 'sparks rising over window %d (emission '
                                  'only)' % (k + 1), layer='wing', lit=False, normal=False, emission=True, z=3,
                                  emission_strength=0.9))
    for k, (src, seed) in enumerate(zip(fb['searchlights'], (0.0, 2.3))):
        fps = 6 if k == 0 else 5
        S, box = LF.searchlight(src, seed)
        decals.append(decal_entry(S, 'searchlight_%s' % 'ab'[k], box, 80, fps, 'searchlight beam of a watchtower '
                                  'sweeping the ice, %.1f s per sweep (emission only)' % (40 / fps),
                                  layer='far_bank', lit=False, normal=False, emission=True, z=1,
                                  emission_strength=0.8))
    for k, (S, box) in enumerate(LF.town_windows(ot)):
        decals.append(decal_entry(S, 'town_win_%d' % (k + 1), box, 30, 0.5, 'an old-town window lighting up as '
                                  'somebody wakes (60 s loop)', layer='oldtown', lit=False, normal=False, z=1,
                                  emission_strength=0.5))
    # ---------------------------------------------------------------- fx strips
    for k, c in enumerate((N.BASE_WIN[0], N.BASE_WIN[2], N.BASE_WIN[3])):
        S, box = LF.smoke_column(c, 970 + k, drift=(30.0, 40.0, 46.0)[k], r1=(24.0, 28.0, 30.0)[k])
        fx.append(fx_entry(S, 'smoke_%d' % (k + 1), box, 16, 6, 1.0, -55, 'smoke pouring from a souterrain '
                           'window, rolling up the facade and drifting right'))
    S, box = LF.smoke_column(178, 980, n=16, fw=60, fh=110, drift=24.0, r0=4.0, r1=16.0, y_src=150, dens=0.8, fire=0.15)
    fx.append(fx_entry(S, 'smoke_ladder', box, 16, 6, 1.0, -55, 'smoke out of the first-floor window at the ladder'))
    S, box = LF.steam_puffs(N.BASE_WIN[0] + 4, 252, 981)
    fx.append(fx_entry(S, 'steam_jet', box, 12, 8, 1.0, -54, 'steam where the jet hits the fire'))
    oh = homes['oldtown']
    for k, (cx, cy) in enumerate(ot['chimneys'][::2][:5]):
        S, (ax, ay, fw_, fh_) = LF.chimney_smoke(990 + k)
        fx.append(fx_entry(S, 'chimney_%d' % (k + 1), (cx - ax, cy - ay, fw_, fh_), 8, 4, F.P['oldtown'], -89,
                           'old-town chimney smoke'))
    S, (ax, ay, fw_, fh_) = LF.exhaust(995)
    fx.append(fx_entry(S, 'exhaust_ussr', (N.CAR_USSR['x1'] + 2 - ax, 283 - ay, fw_, fh_), 8, 6, 1.0, -5,
                       'the Soviet car idles: exhaust puffs at its tail'))
    fx.append({'type': 'snow', 'density': 0.75, 'wind': 10.0, 'color_far': hexc(SN[0]), 'color_near': hexc(SN[3]),
               'note': 'screen-space snowfall (scripts/levels/fx_snow.gd)'})
    fx.append({'type': 'fog_band', 'y': 214, 'height': 26, 'color': hexc(SL[3]), 'alpha': 0.16, 'parallax': 0.3,
               'z': -93, 'note': 'mist over the open lead'})
    # ---------------------------------------------------------------- dynamic lights (subtler than the bake)
    dyn = []
    for k, lx in enumerate(N.LAMPS):
        dyn.append({'name': 'lamp_%d' % (k + 1), 'pos': [lx, N.LAMP_Y + 6], 'color': hexc(LA[3]), 'energy': 0.5,
                    'radius': 112, 'flicker': 0.0, 'height': 30, 'on_layer': 'playfield'})
    dyn.append({'name': 'pylon_lamp', 'pos': [N.PYLON_LAMP[0], N.PYLON_LAMP[1] + 8], 'color': hexc(LA[3]),
                'energy': 0.55, 'radius': 128, 'flicker': 0.0, 'height': 34, 'on_layer': 'playfield'})
    dyn.append({'name': 'shelter_lamp', 'pos': [N.SHELTER_LAMP[0], N.SHELTER_LAMP[1] + 4], 'color': hexc(LA[3]),
                'energy': 0.45, 'radius': 72, 'flicker': 0.0, 'height': 20, 'on_layer': 'playfield'})
    for k, c in enumerate(N.BASE_WIN):
        dyn.append({'name': 'fire_win_%d' % (k + 1), 'pos': [c, 252], 'color': hexc(LA[2]), 'energy': 0.5,
                    'radius': 150, 'flicker': 0.2, 'height': 18, 'on_layer': 'playfield'})
    dyn.append({'name': 'fire_wide', 'pos': [190, 284], 'color': hexc(LA[1]), 'energy': 0.3, 'radius': 260,
                'flicker': 0.12, 'height': 60, 'on_layer': 'playfield'})
    dyn.append({'name': 'wall_lamp', 'pos': [N.WALL_LAMP[0] + 2, N.WALL_LAMP[1] + 6], 'color': hexc(LA[3]),
                'energy': 0.4, 'radius': 70, 'flicker': 0.0, 'height': 16, 'on_layer': 'playfield'})
    dyn.append({'name': 'headlight', 'pos': list(tr['headlight']), 'color': hexc(LA[4]), 'energy': 0.35,
                'radius': 64, 'flicker': 0.0, 'height': 10, 'on_layer': 'playfield'})
    dyn.append({'name': 'beacon', 'pos': list(tr['beacon']), 'color': hexc(SK[2]), 'energy': 0.3, 'radius': 54,
                'flicker': 0.0, 'height': 16, 'on_layer': 'playfield'})
    dyn.append({'name': 'lighter', 'pos': [1271, 262], 'color': hexc(LA[3]), 'energy': 0.25, 'radius': 26,
                'flicker': 0.2, 'height': 6, 'on_layer': 'playfield'})
    # ---------------------------------------------------------------- manifest
    scene = {
        'id': K.ENV_ID, 'palette': 'veltrava',
        'world_size': [K.WORLD_W, K.WORLD_H],
        'camera': {'bounds': [0, 0, K.WORLD_W, K.WORLD_H]},
        'canvas_modulate': CANVAS_MODULATE,
        'layers': layers,
        'props': props,
        'decals': decals,
        'lights': dyn,
        'fx': fx,
        'walkable': [[K.WALK_X[0], K.WALK_BAND[0]], [K.WALK_X[1], K.WALK_BAND[0]], [K.WALK_X[1], K.WALK_BAND[1]],
                     [K.WALK_X[0], K.WALK_BAND[1]]],
        'spawns': SPAWNS,
        'hotspots': HOTSPOTS,
        'zones': ZONES,
        'hotspot_info': hotspot_info(tr),
        'npcs': {k: {'feet': v, 'facing': 'left'} for k, v in NPC_FEET.items()},
        'explore_sites': explore_sites(tr),
        'notes': [
            'Side view like the palais: feet line y 300, walk band 296-306 (x 18-1902); everything painted stands '
            'behind it (props base_y <= 294, life figures <= 294), the fg layer stays below y 318.',
            'Night bake: env_c3p2_quay_kit.resolve() paints every lit plane with the same light fields (six '
            'lanterns, the pylon and shelter lamps, five burning souterrain windows, the headlight); the Godot '
            'lights above are only accents (fire flicker 0.12-0.22, lanterns steady).',
            'Warm only from the fire (left) and the lanterns; the river, the Line and the sky stay cold blue '
            '(grade "quay").',
            'Insignia: only the two fender pennants (props car_reich / car_ussr) -- neutral files + *_hist variants '
            'resolved by Symbols.pick (TECHNICAL_ARCHITECTURE §12.4). No life strip has a _hist twin.',
            'No story character is painted: Konrad, Frau Brunner, the guard, Kessler, Voronova and Ekdahl are the '
            'level NPCs at their hotspots; firemen, onlookers, aides and drivers are anonymous life strips.',
            'Searchlights sweep at >= 6 s per sweep; fire flicker in the strips <= 3 Hz; the beacon turns once a '
            'second without a flash; nothing flashes the screen.',
            'explore_sites: art features the exploration stream can point its finds at (stand positions on the '
            'walk band, >= 24 px from the story hotspots); they are NOT hotspots of this file.',
        ],
        'meta': {'mode': 'side', 'feet_y': K.FEET_Y, 'generator': 'tools/pixelgen/env_c3p2_quay.py',
                 'date': K.DATE, 'area': 'env_c3p2_night', 'palette_ramps': 'data/chapters/c3.json palettes.veltrava'},
    }
    sj = os.path.join(ENV_DIR, 'scene.json')
    with open(sj, 'w', encoding='utf-8', newline=LF_) as f:
        json.dump(_plain(scene), f, indent=1, ensure_ascii=False)
    record(sj, 'env_c3p2_quay.py', 'art manifest (TECHNICAL_ARCHITECTURE §3.1)')
    write_provenance()
    drop_orphan_imports()
    bad = {}
    for root, _d, files in os.walk(ENV_DIR):
        for fn in files:
            if fn.endswith('.png') and not fn.endswith(('_n.png', '_e.png')) and 'glow_air' not in fn:
                arr = np.asarray(Image.open(os.path.join(root, fn)).convert('RGBA'))
                off = K.palette_off(arr)
                if off:
                    bad[fn] = off[:5]
    print('palette check:', 'OK' if not bad else bad)
    print('scene built in %.1fs (%d files)' % (time.time() - t0, len(PRODUCED)))
    return scene


def hotspot_info(tr):
    return {
        'bench': {'kind': 'story', 'stand': [760, 300], 'focus': [760, 280],
                  'what': 'the bench under the lantern light: the file burst open, two fans of sheets, the red C-17 '
                          'tag, sheets in the snow'},
        'konrad_quay': {'kind': 'story', 'stand': [800, 300], 'focus': [818, 258],
                        'what': 'Konrad (x 818) beside the bench, facing it; sooty coat'},
        'typist_quay': {'kind': 'npc_anchor', 'stand': [330, 300], 'focus': [344, 258],
                        'what': 'Frau Brunner (x 344) in front of the fire engine, coat over her nightdress'},
        'guard_quay': {'kind': 'npc_anchor', 'stand': [1050, 300], 'focus': [1050, 258],
                       'what': 'the commission guard in front of the trestle, the onlookers behind it'},
        'kessler_quay': {'kind': 'npc_anchor', 'stand': [1180, 300], 'focus': [1180, 258],
                         'what': 'Kessler in front of the German car, his aide a step behind (x 1150)'},
        'voronova_quay': {'kind': 'npc_anchor', 'stand': [1330, 300], 'focus': [1344, 258],
                          'what': 'Voronova (x 1344) in front of the Soviet car, her aide at x 1376'},
        'journalist_quay': {'kind': 'npc_anchor', 'stand': [1560, 300], 'focus': [1574, 258],
                            'what': 'Nils Ekdahl (x 1574) with his camera at the bridgehead pylon'},
    }


def explore_sites(tr):
    """Suggested stand positions + focus points for the exploration finds of C3P2_DESIGN §7 (quay)."""
    return {
        'exp_fire_engine': {'stand': [280, 300], 'focus': [276, 252], 'what': 'cab door with the city arms, '
                            'FEUERWEHR lettering, the blue lamp turning, the turntable ladder'},
        'exp_soot_print': {'stand': [168, 300], 'focus': [178, 272], 'hidden': True,
                           'what': 'coal dust on the snow at the open hatch, two body prints where they lay'},
        'exp_ice': {'stand': [640, 300], 'focus': [640, 230], 'what': 'the frozen river over the balustrade: '
                    'pressure ridges, the open black lead'},
        'exp_lantern': {'stand': [470, 300], 'focus': [464, 194], 'what': 'cast-iron lantern on the balustrade, '
                        'snow cap, light in the falling snow'},
        'exp_searchlights': {'stand': [930, 300], 'focus': [930, 140], 'what': 'two searchlights of the Line '
                             'sweeping the ice from their towers'},
        'exp_cars': {'stand': [1116, 300], 'focus': [1120, 254], 'what': 'the two black cars, two pennants; the '
                     'two drivers share one lighter between them (x 1252-1272)'},
        'exp_bridge_arms': {'stand': [1690, 300], 'focus': [1672, 272], 'what': 'the city arms as a relief on the '
                            'ramp wall under a bracket lamp (and small on the pylon): a white three-arch bridge over '
                            'waves, VELTRAVA'},
        'exp_tram_stop': {'stand': [1700, 300], 'focus': [1701, 212], 'what': 'tram stop, lines 7 and 12; the '
                          'shelter with a commission poster'},
        # round 9 fix: the locker of the task text („im Gerätekasten hinter dem Führerhaus“) is the front shutter bay
        # of the body (TRUCK x0 + 79..115, the cab starts at x0 + 116), not the bumper at x 430; >= 24 px from typist_quay
        'blanket_source': {'stand': [360, 300], 'focus': [355, 255], 'what': 'the equipment locker directly behind '
                           'the cab (front shutter bay of the body, x 337-373; side task „Eine Decke für Frau Brunner“)'},
    }


def _plain(o):
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


def write_provenance():
    files = [{'path': p, 'generator': g, 'content': d} for p, g, d in sorted(PRODUCED)]
    out = {'generator': 'tools/pixelgen/env_c3p2_quay.py (+ _kit, _far, _near, _life)', 'date': K.DATE,
           'area': 'env_c3p2_night',
           'licence': 'project-owned original artwork, generated procedurally with fixed seeds; no copied, traced, '
                      'downloaded or AI-generated pixels; fonts from env_veltrava_lib.py',
           'run': 'py -3 -P tools/pixelgen/env_c3p2_quay.py', 'files': files}
    p = os.path.join(ENV_DIR, 'provenance.json')
    with open(p, 'w', encoding='utf-8', newline=LF_) as f:
        json.dump(out, f, indent=1, ensure_ascii=False)


# ===================================================================================================== preview
def preview(out_dir, cams=(0, 320, 640, 960, 1280), frame=0, hist=False):
    """CPU composite of the manifest (no Godot lights / modulate / grade) -> <out_dir>/quay_cam####.png"""
    with open(os.path.join(ENV_DIR, 'scene.json'), encoding='utf-8') as f:
        m = json.load(f)
    os.makedirs(out_dir, exist_ok=True)

    def img(rel_, h=False):
        p = os.path.join(ENV_DIR, rel_)
        if h:
            hp = p[:-4] + '_hist.png'
            if os.path.exists(hp):
                p = hp
        return np.asarray(Image.open(p).convert('RGBA')).astype(np.float32) if os.path.exists(p) else None

    def blit(dst, src, x, y, mode='mix', alpha=1.0):
        h, w = src.shape[:2]
        X0, Y0, X1, Y1 = max(0, x), max(0, y), min(dst.shape[1], x + w), min(dst.shape[0], y + h)
        if X1 <= X0 or Y1 <= Y0:
            return
        s = src[Y0 - y:Y1 - y, X0 - x:X1 - x]
        a = s[..., 3:4] / 255.0 * alpha
        if mode == 'add':
            dst[Y0:Y1, X0:X1] += s[..., :3] * a
        else:
            dst[Y0:Y1, X0:X1] = dst[Y0:Y1, X0:X1] * (1 - a) + s[..., :3] * a

    def frame_of(arr, n, k):
        fw = arr.shape[1] // n
        return arr[:, (k % n) * fw:(k % n + 1) * fw]

    paths = []
    for cam in cams:
        canvas = np.zeros((360, 640, 3), np.float32)
        canvas[:] = NI[0][:3]
        items = []
        lhome = {}
        for L in m['layers']:
            p = L['parallax'][0]
            sx = int(round(L['pos'][0] - cam * p))
            lhome[L['name']] = (sx, L['pos'][1], L['pos'][0])
            items.append((L['z'], 0, 'layer', L, sx))
        for fx_ in m['fx']:
            if fx_.get('type') == 'anim_sprite':
                p = fx_['parallax'][0] if isinstance(fx_['parallax'], list) else fx_['parallax']
                items.append((fx_['z'], 1, 'fx', fx_, int(round(fx_['pos'][0] - cam * p))))
        for P in m['props']:
            items.append((0, P['base_y'], 'prop', P, P['pos'][0] - cam))
        for D in m['decals']:
            if D['layer'] == 'playfield':
                items.append((0, D.get('base_y', 0), 'decal', D, D['pos'][0] - cam))
        items.sort(key=lambda e: (e[0], e[1]))
        for z, sub, kind, E, sx in items:
            if kind == 'layer':
                a = img(E['file'])
                blit(canvas, a, sx, E['pos'][1], 'add' if E.get('blend') == 'add' else 'mix', E.get('alpha', 1.0))
                if E.get('emission'):
                    em = img(E['file'][:-4] + '_e.png')
                    if em is not None:
                        blit(canvas, em, sx, E['pos'][1], 'add', E.get('emission_strength', 0.22))
                for D in m['decals']:
                    if D['layer'] == E['name']:
                        hs, hy, hx = lhome[E['name']]
                        a = img(D['file'])
                        k = (frame + int(K.lum(np.array([len(D['name']) * 40, 0, 0])) * 7)) % D['frames']
                        dx = hs + (D['pos'][0] - hx)
                        blit(canvas, frame_of(a, D['frames'], k), dx, D['pos'][1])
                        if D.get('emission'):
                            em = img(D['file'][:-4] + '_e.png')
                            blit(canvas, frame_of(em, D['frames'], k), dx, D['pos'][1], 'add',
                                 D.get('emission_strength', 0.22))
            elif kind == 'fx':
                a = img(E['file'])
                blit(canvas, frame_of(a, E['frames'], frame), sx, E['pos'][1], 'mix', E.get('alpha', 1.0))
            elif kind == 'prop':
                a = img(E['file'], hist)
                blit(canvas, a, sx, E['pos'][1])
                if E.get('emission'):
                    em = img(E['file'][:-4] + '_e.png')
                    blit(canvas, em, sx, E['pos'][1], 'add', 0.22)
            else:
                a = img(E['file'])
                blit(canvas, frame_of(a, E['frames'], frame), sx, E['pos'][1])
                if E.get('emission'):
                    em = img(E['file'][:-4] + '_e.png')
                    blit(canvas, frame_of(em, E['frames'], frame), sx, E['pos'][1], 'add',
                         E.get('emission_strength', 0.22))
        out = os.path.join(out_dir, 'quay_cam%04d%s.png' % (cam, '_hist' if hist else ''))
        Image.fromarray(np.clip(canvas, 0, 255).astype(np.uint8)).save(out)
        paths.append(out)
    return paths


if __name__ == '__main__':
    build()
    for a in sys.argv[1:]:
        if a.startswith('--preview'):
            d = a.split('=', 1)[1] if '=' in a else os.path.join(ENV_DIR, '_preview')
            print('previews ->', preview(d))
