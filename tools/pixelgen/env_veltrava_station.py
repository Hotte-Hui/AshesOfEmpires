"""env_veltrava_station -- generator for L_C3_Station 'Bahnhof Veltrava – Freie Stadt (fiktiv)' (Chapter 3,
Alexei, oblique 2.5D like Karsk, cold dawn, February 1964).  Reproduce everything with:

    python3 -P tools/pixelgen/env_veltrava_station.py                  (art + scene.json + documents + locale)
    python3 -P tools/pixelgen/env_veltrava_station.py --preview=DIR     (+ composited previews into DIR)

Outputs (area env_veltrava_station):
    assets/environments/veltrava_station/*.png (+ _n normal maps, _e emission masks, _hist insignia variants),
        props/, fx/, scene.json (TECHNICAL_ARCHITECTURE 3.1)
    assets/ui/documents/veltrava_station_*.png + veltrava_station_documents.json (inspect documents, 1:1 px)
    data/locale/de_env_veltrava_station.json (document alt texts)
Deterministic: fixed seeds, no network, original procedural art (references are never sampled).
Shared folder (round 10, env_keep.py): thaw/ (env_veltrava_station_thaw.py), walkers/ (walkers_r8.py), the
hand-added "actors" entries (AmbientWalkers, StationThaw) and anything else this generator did not write stay; a run
removes only the PNGs its previous run recorded in provenance.json (written since round 10) and merges scene.json.
Palette: 'veltrava' (registered into pg.PALETTES by env_veltrava_lib, ramps = data/chapters/c3.json).
"""
from __future__ import annotations

import json
import os
import shutil
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import numpy as np  # noqa: E402
from PIL import Image  # noqa: E402

from env_veltrava_lib import (ENV_DIR, ROOT, Layer, NI, SL, IR, CR, PA, LA, SK, SN, RD, crop_v, crop_box,  # noqa: E402
                              palette_report, hexc, layer_w, WORLD_W, WORLD_H)
import env_veltrava_station_bg as BG  # noqa: E402
import env_keep as KEEP  # noqa: E402  (round 10: the folder is shared)
import env_veltrava_station_tracks as TR  # noqa: E402
import env_veltrava_station_props as PR  # noqa: E402
import env_veltrava_station_fx as FX  # noqa: E402
import env_veltrava_station_life as LIFE  # noqa: E402

WORLD = (WORLD_W, WORLD_H)
CANVAS_MODULATE = '#D5D3D6'
# story NPC feet = scene.json hotspot + hotspot_offset of the node in scenes/levels/L_C3_Station.tscn, and the
# side they face; used only to place their breath puffs (mouth ~41 px above the feet on the 32x56 sheets)
NPC_FEET = {'conductor': ((616, 290), -1), 'border_officer': ((1208, 286), -1), 'voronova': ((346, 300), -1),
            'konrad_queue': ((1300, 280), -1)}
EMISSION_STRENGTH = {'skyline': 0.35, 'city': 0.4, 'station': 0.5, 'far_track': 0.5, 'island': 0.6,
                     'square': 0.5, 'ground': 0.3, 'train_near': 0.5, 'concourse': 0.55, 'canopy': 0.7}


def save_layer(L: Layer, name, parallax, z, lit=True, normal=True, crop='v', strength=3.0, hist=None):
    """crop 'v' = vertical only (full-width parallax layers), 'box' = both axes (local layers)."""
    px = py = 0
    if crop == 'v':
        L, py = crop_v(L)
    elif crop == 'box':
        L, px, py = crop_box(L)
    base = os.path.join(ENV_DIR, name)
    info = L.save(base, normal=normal, strength=strength)
    if hist is not None:
        H = hist
        if crop == 'v':
            H = TR_sub(H, 0, py, L.w, L.h)
        elif crop == 'box':
            H = TR_sub(H, px, py, L.w, L.h)
        Image.fromarray(H.c, 'RGBA').save(base + '_hist.png')
    entry = {'name': name, 'file': name + '.png', 'pos': [int(px), int(py)],
             'parallax': [parallax, 0.0 if parallax < 1.0 else 1.0], 'z': z, 'normal': bool(normal),
             'emission': bool(info['emission']), 'lit': bool(lit), 'size': [L.w, L.h]}
    if entry['emission'] and name in EMISSION_STRENGTH:
        entry['emission_strength'] = EMISSION_STRENGTH[name]
    if hist is not None:
        entry['hist_variant'] = name + '_hist.png'
    if crop == 'v' and parallax < 1.0:
        need = 640 + parallax * (WORLD[0] - 640)
        assert L.w >= need - 0.5, (name, L.w, need)
    return entry, L, (px, py)


def TR_sub(L, x0, y0, w, h):
    from env_veltrava_lib import sub_layer
    return sub_layer(L, x0, y0, w, h)


def save_prop(P: Layer, name, foot_local, foot_world, base_y, collision, normal=True, hist=None, extra=None):
    """Crop the prop and place it so foot_local (x, y in the uncropped sprite) lands on foot_world."""
    C, cx0, cy0 = crop_box(P, pad=0)
    fx, fy = foot_local
    pos = [int(foot_world[0] - (fx - cx0)), int(foot_world[1] - (fy - cy0))]
    os.makedirs(os.path.join(ENV_DIR, 'props'), exist_ok=True)
    info = C.save(os.path.join(ENV_DIR, 'props', name), normal=normal, strength=3.0)
    if hist is not None:
        from env_veltrava_lib import sub_layer
        Hc = sub_layer(hist, cx0, cy0, C.w, C.h)
        Image.fromarray(Hc.c, 'RGBA').save(os.path.join(ENV_DIR, 'props', name + '_hist.png'))
    e = {'name': name, 'file': 'props/' + name + '.png', 'pos': pos, 'base_y': int(base_y),
         'collision': [[int(a), int(b)] for a, b in collision] if collision else [], 'normal': bool(normal),
         'emission': bool(info['emission']), 'size': [C.w, C.h]}
    if hist is not None:
        e['hist_variant'] = 'props/' + name + '_hist.png'
    if extra:
        e.update(extra)
    return e, pos, (cx0, cy0)


def rect_poly(x0, y0, x1, y1):
    return [[x0, y0], [x1, y0], [x1, y1], [x0, y1]]


def save_strip(S: Layer, name):
    os.makedirs(os.path.join(ENV_DIR, 'fx'), exist_ok=True)
    S.save(os.path.join(ENV_DIR, 'fx', name), normal=False, emission=bool(S.em[..., 3].any()))
    return 'fx/' + name + '.png'


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


# provenance rows of this generator (env_keep): what its run writes, the record its next run removes first
FAMILY = ('tools/pixelgen/env_veltrava_station.py', 'tools/pixelgen/env_veltrava_station_life.py')


def clean_env():
    """Remove the PNGs this generator wrote last time (its provenance.json rows; their Godot .import sidecars stay so
    UIDs remain stable) -- nothing else of the shared folder: thaw/, walkers/ and hand-made files stay."""
    if not os.path.isdir(ENV_DIR):
        return
    KEEP.remove_own_pngs(ENV_DIR, ROOT, FAMILY)


def _content(r: str) -> str:
    """Provenance line of a written file from its place and name."""
    name = r.rsplit('/', 1)[-1][:-4]
    kind = ('ambient actor sprite' if '/actors/' in r else 'prop' if '/props/' in r else 'fx strip' if '/fx/' in r
            else 'layer')
    for suf, what in (('_n', 'normal map (OpenGL +Y up)'), ('_e', 'emission mask'),
                      ('_hist', 'variant with the historical insignia (Symbols.pick)')):
        if name.endswith(suf):
            return '%s %s -- %s' % (kind, name[:-len(suf)], what)
    return '%s %s' % (kind, name)


def write_provenance(written: list):
    """provenance.json (round 10): every file this run wrote -- the record env_keep reads on the next run -- plus the
    rows other generators or hands added for files that still exist."""
    rows = []
    for path in written + [os.path.join(ENV_DIR, 'scene.json')]:
        r = KEEP.rel(path, ROOT)
        life = '/actors/' in r
        rows.append({'path': r, 'generator': FAMILY[1] if life else FAMILY[0],
                     'content': 'art manifest (TECHNICAL_ARCHITECTURE 3.1)' if r.endswith('.json') else _content(r)})
    p = os.path.join(ENV_DIR, 'provenance.json')
    files = KEEP.merge_rows(sorted(rows, key=lambda e: e['path']), KEEP.read_json(p), FAMILY, ROOT)
    out = {'generator': 'tools/pixelgen/env_veltrava_station.py (+ _bg, _tracks, _props, _fx, _life, env_veltrava_lib)',
           'date': '2026-11-04', 'area': 'env_veltrava_station',
           'licence': 'project-owned original artwork, generated procedurally with fixed seeds; no copied, traced, '
                      'downloaded or AI-generated pixels',
           'run': 'python3 -P tools/pixelgen/env_veltrava_station.py', 'files': files}
    with open(p, 'w', encoding='utf-8', newline='\n') as f:
        json.dump(out, f, indent=1, ensure_ascii=False)


def drop_orphan_imports():
    for root, dirs, files in os.walk(ENV_DIR):
        for fn in files:
            if fn.endswith('.png.import') and not os.path.exists(os.path.join(root, fn[:-7])):
                os.remove(os.path.join(root, fn))


def build():
    t0 = time.time()
    os.makedirs(ENV_DIR, exist_ok=True)
    clean_env()
    stamps = KEEP.png_stamps(ENV_DIR)      # what the run writes changes its stamp (the provenance record)
    layers, props, fx, lights = [], [], [], []
    A = {}
    # ------------------------------------------------------------------ far planes
    e, _, _ = save_layer(BG.make_sky(), 'sky', 0.0, -100, lit=False, normal=False)
    layers.append(e)
    e, _, _ = save_layer(BG.make_clouds(), 'clouds', 0.03, -96, lit=False)
    layers.append(e)
    e, _, _ = save_layer(BG.make_skyline(), 'skyline', 0.10, -90)
    layers.append(e)
    city, chimneys = BG.make_city()
    e, _, _ = save_layer(city, 'city', 0.30, -80)
    layers.append(e)
    station, ES = BG.make_station()
    e, _, _ = save_layer(station, 'station', 0.55, -70)
    layers.append(e)
    # ------------------------------------------------------------------ tracks, trains, island
    far, EF = TR.make_far()
    e, _, _ = save_layer(far, 'far_track', TR.P_FAR, -50)
    layers.append(e)
    pen = TR.make_pennants(EF, hist=False)
    pen_h = TR.make_pennants(EF, hist=True)
    e, _, _ = save_layer(pen, 'pennants_reich', TR.P_FAR, -49, hist=pen_h)
    layers.append(e)
    isl, EI = TR.make_island()
    e, _, _ = save_layer(isl, 'island', TR.P_ISL, -40)
    layers.append(e)
    tr, ET = TR.make_train_near()
    e, _, trpos = save_layer(tr, 'train_near', 1.0, -16, crop='box')
    layers.append(e)
    # compartments of wagon 2 whose lamp is on but where nobody is baked in: somebody moves behind the glass
    A['life_windows'] = [(w[0], w[1]) for w in ET['cars'][1].get('lit', []) if not w[4]][:3]
    EC = {}
    canopy = PR.make_canopy(EC)
    e, _, _ = save_layer(canopy, 'canopy', 1.0, -12, crop='box')
    layers.append(e)
    EQ = {}
    conc = PR.make_concourse(EQ)
    e, _, _ = save_layer(conc, 'concourse', 1.0, -13, crop='box')
    layers.append(e)
    e, _, _ = save_layer(PR.make_square(), 'square', 0.85, -18, crop='box')
    layers.append(e)
    # ------------------------------------------------------------------ props (y-sorted)
    col_kind = {30: 'track', 290: None, 545: 'track', 900: 'departures', 1095: 'poster', 1352: None}
    for i, cx in enumerate(PR.COLUMN_XS):
        P, foot, info = PR.column_prop(col_kind[cx])
        ent, pos, (cx0, cy0) = save_prop(P, 'column_%d' % (i + 1), foot, (cx, 266), 266,
                                         rect_poly(cx - 7, 261, cx + 8, 267))
        props.append(ent)
        if 'board' in info:
            A['departures_board'] = (pos[0] + info['board'][0] - cx0, pos[1] + info['board'][1] - cy0)
        if 'poster' in info:
            A['poster'] = (pos[0] + info['poster'][0] - cx0, pos[1] + info['poster'][1] - cy0)
    P, foot = PR.luggage_cart()
    ent, _, _ = save_prop(P, 'luggage_cart', foot, (424, 290), 290, rect_poly(398, 283, 452, 291))
    props.append(ent)
    P, foot = PR.bench(seated=True)
    ent, bpos_a, (ba0, bb0) = save_prop(P, 'bench_a', foot, (206, 282), 282, rect_poly(181, 276, 233, 283))
    props.append(ent)
    A['bench_heads'] = [(bpos_a[0] + hx - ba0, bpos_a[1] + hy - bb0) for (hx, hy) in PR.BENCH_HEADS]
    P, foot = PR.bench(mitten=True)
    ent, _, _ = save_prop(P, 'bench_mitten', foot, (802, 298), 298, rect_poly(777, 292, 829, 299))
    props.append(ent)
    P, foot = PR.litter_basket()
    ent, _, _ = save_prop(P, 'litter_basket', foot, (516, 272), 272, rect_poly(511, 268, 522, 273))
    props.append(ent)
    P, foot = PR.kiosk()
    ent, _, _ = save_prop(P, 'kiosk', foot, (1016, 274), 274, rect_poly(986, 266, 1046, 275))
    props.append(ent)
    P, foot = PR.barrier()
    ent, _, _ = save_prop(P, 'barrier', foot, (1150, 284), 284, rect_poly(1121, 279, 1179, 285))
    props.append(ent)
    P, foot, binfo = PR.booth()
    ent, bpos, (bx0, by0) = save_prop(P, 'control_booth', foot, (1257, 277), 277, rect_poly(1182, 266, 1334, 278))
    props.append(ent)
    A['booth_lamp'] = (bpos[0] + binfo['lamp'][0] - bx0, bpos[1] + binfo['lamp'][1] - by0)
    A['counter2'] = (bpos[0] + binfo['counter2'][0] - bx0, bpos[1] + binfo['counter2'][1] - by0)
    A['counter1'] = (bpos[0] + binfo['counter1'][0] - bx0, bpos[1] + binfo['counter1'][1] - by0)
    P, foot = PR.flag('commission')
    ent, _, _ = save_prop(P, 'flag_commission', foot, (1176, 279), 279, rect_poly(1173, 276, 1180, 280))
    props.append(ent)
    for kind, fxw in (('ussr', A['counter2'][0] - 30), ('reich', A['counter1'][0] + 26)):
        # small delegation flags on wall staffs at the roof lip of the booth (above the counter signs)
        P, foot = PR.flag(kind, hist=False)
        H, _ = PR.flag(kind, hist=True)
        ent, _, _ = save_prop(P, 'flag_' + kind, foot, (fxw, bpos[1] + 15), 278, [], hist=H)
        props.append(ent)
    P, foot = PR.queue_reich()
    ent, qpos, (qx0, qy0) = save_prop(P, 'queue_reich', foot, (1342, 280), 280, rect_poly(1320, 274, 1364, 281))
    props.append(ent)
    A['queue_heads'] = [(qpos[0] + hx - qx0, qpos[1] + hy - qy0) for (hx, hy) in PR.QUEUE_HEADS]
    P, foot = PR.menu_stand()
    ent, _, _ = save_prop(P, 'menu_stand', foot, (1604, 290), 290, rect_poly(1596, 286, 1612, 291))
    props.append(ent)
    # ------------------------------------------------------------------ ground (needs the light sources)
    cold = [(lx, 270, (SN[1], SL[3]), 0.55, 2) for lx in PR.LAMP_XS if lx < 1560 or lx > 1800]
    warm = [(1594, 270, (LA[2], LA[1]), 0.95, 3), (1650, 268, (LA[3], LA[2]), 1.0, 3),
            (1704, 270, (LA[2], LA[1]), 0.95, 3), (A['booth_lamp'][0], 282, (LA[2], LA[1]), 0.6, 1),
            (ET['saloon'][0], 268, (LA[1], LA[0]), 0.5, 1)]
    # polish pass: the lit compartments mirror faintly in the wet slabs along the platform edge (warm accents)
    warm += [(w[0] + 8, 267, (LA[1], LA[0]), 0.32, 1) for car in ET['cars'] for w in car.get('lit', [])
             if 0 <= w[0] < 1920]
    EG = {}
    door_xs = [dx + dw // 2 for car in ET['cars'] for (dx, dw) in car['doors'] if 0 <= dx < 1920]
    ground = TR.make_ground(EG, cold, warm, door_xs=door_xs)
    e, _, _ = save_layer(ground, 'ground', 1.0, -20, crop='box')
    layers.append(e)
    e, _, _ = save_layer(PR.make_fg(), 'fg_frame', 1.3, 60, lit=False, normal=False)
    layers.append(e)
    # ------------------------------------------------------------------ ambient life (actors + viaduct plane)
    A['breath'] = [{'pos': [fx_, fy_], 'points': [[fx_ + face * 3, fy_ - 41]], 'interval': 4.2 + (fx_ % 7) * 0.2}
                   for (fx_, fy_), face in NPC_FEET.values()]
    A['breath'].append({'pos': [1342, 280], 'points': [list(h) for h in A['queue_heads']], 'interval': 5.0})
    A['breath'].append({'pos': [206, 282], 'points': [list(h) for h in A['bench_heads']], 'interval': 5.6})
    actors, extra = LIFE.build(A)
    for (XL, nm, par, z) in extra:
        e, _, _ = save_layer(XL, nm, par, z)
        layers.append(e)
    layers.sort(key=lambda d: d['z'])
    # ------------------------------------------------------------------ fx strips
    strips = {}

    def strip(key, S, org, frames):
        strips[key] = (save_strip(S, key), org, S.w // frames, S.h, frames)

    S = FX.snow_tile(frames=24, fw=160, fh=80, n=16, size=1, seed=1)
    strip('snow_far', S, (0, 0), 24)
    S = FX.snow_tile(frames=16, fw=160, fh=112, n=7, size=2, seed=2, wobble=4.0)
    strip('snow_near', S, (0, 0), 16)
    S = FX.snow_tile(frames=16, fw=80, fh=104, n=9, size=2, seed=3, wobble=3.0)
    strip('snow_arch', S, (0, 0), 16)
    S, org = FX.steam_plume(seed=4)
    strip('loco_steam', S, org, 8)
    S, org = FX.steam_puffs(seed=5)
    strip('heater_steam', S, org, 6)
    S, org = FX.smoke_ribbon(seed=6)
    strip('chimney_smoke', S, org, 8)
    S, org = FX.smoke_ribbon(seed=7, fw=30, fh=54, drift=16.0, w0=1.5, w1=6.0, cols=[SK[0], SK[1], SK[2], SK[3]])
    strip('chimney_smoke_far', S, org, 8)

    def anim(key, src, parallax, z, fps, emission=False, alpha=1.0, note=None):
        f, org, fw, fh, n = strips[key]
        d = {'type': 'anim_sprite', 'file': f, 'frames': n, 'fps': fps,
             'pos': [int(src[0] - org[0]), int(src[1] - org[1])], 'parallax': parallax, 'z': z,
             'emission': emission, 'frame_size': [fw, fh], 'lit': False}
        if alpha != 1.0:
            d['alpha'] = alpha
        if note:
            d['note'] = note
        fx.append(d)

    # snow only OUTSIDE our canopy: tiles behind the near train / platform, in front of the far planes
    for row, y in enumerate((26, 106)):
        for k in range(10):
            anim('snow_far', (k * 160 - row * 80, y), 0.7, -60, 4 + (k + row) % 2,
                 note='far flakes between canopy edge and station' if k == 0 and row == 0 else None)
    for row, y in enumerate((28, 140)):
        for k in range(13):
            anim('snow_near', (k * 160 - row * 70, y), 0.96, -35, 5 + (k % 2),
                 note='near flakes beyond the canopy edge, hidden by trains and platform' if k == 0 and row == 0 else None)
    ax, ay, aw, ah = EQ['arch']
    anim('snow_arch', (ax - 2, ay), 1.0, -14, 5,
         note='snow on the square, seen only through the exit arch (in front of the tram actor at z -17)')
    # steam: Soviet loco (left, off-screen) and the steam-heating couplings between the carriages
    anim('loco_steam', (-30, 178), 1.0, -15, 5)
    anim('heater_steam', (-6, 258), 1.0, -15, 6, alpha=0.9)
    decals = []
    for (gx, gy) in ET['gangways']:
        if gx == 326:
            # the leaking heating coupling between wagons 2 and 3 (side task 'Wagen drei ist kalt'): a named
            # decal, so the task code can stop the hiss once the stop cock is thawed:
            #   level.backdrop.decals_by_name["heater_leak_23"].visible = false
            f_, org_, fw_, fh_, n_ = strips['heater_steam']
            decals.append({'name': 'heater_leak_23', 'file': f_, 'pos': [int(gx - 2 - org_[0]), int(gy + 20 - org_[1])],
                           'z': -15, 'parallax': [1.0, 1.0], 'lit': False, 'normal': False, 'frames': n_,
                           'fps': 7, 'alpha': 0.9,
                           'note': 'steam leak of the frozen stop cock between wagons 2 and 3 (exp_task_coupling)'})
            continue
        anim('heater_steam', (gx - 2, gy + 20), 1.0, -15, 5 + gx % 2, alpha=0.85)
    # chimney smoke: city (0.3) and the station building (0.55)
    # polish pass: fewer ribbons -- ten thin plumes at cam 0 read as scratches across the old town
    for (cx, cy) in [c for c in chimneys if c[1] < 150][::5][:4]:
        anim('chimney_smoke_far', (cx, cy), 0.30, -79, 4)
    for (cx, cy) in ES['chimneys'][1:3]:
        anim('chimney_smoke', (cx, cy), 0.55, -69, 4 + cx % 2)
    # fog bands: 'y' = band centre, parallax between the planes they separate
    fx += [
        {'type': 'fog_band', 'y': 142, 'height': 26, 'color': hexc(SK[4]), 'alpha': 0.30, 'parallax': 0.18, 'z': -86},
        {'type': 'fog_band', 'y': 170, 'height': 34, 'color': hexc(SK[3]), 'alpha': 0.30, 'parallax': 0.4, 'z': -76},
        {'type': 'fog_band', 'y': 204, 'height': 30, 'color': hexc(SK[2]), 'alpha': 0.26, 'parallax': 0.7, 'z': -62},
        {'type': 'fog_band', 'y': 236, 'height': 20, 'color': hexc(SL[4]), 'alpha': 0.12, 'parallax': 0.95, 'z': -38},
    ]
    # ------------------------------------------------------------------ lights
    for i, (lx, ly) in enumerate(EC['lamps']):
        lights.append({'id': 'canopy_lamp_%d' % (i + 1), 'pos': [lx, 292], 'color': hexc(SN[3]), 'energy': 0.55,
                       'radius': 104, 'flicker': 0.04 if i == 3 else 0.0, 'height': 60, 'on_layer': 'playfield'})
    lights += [
        {'id': 'cafe_korridor', 'pos': [1650, 284], 'color': hexc(LA[3]), 'energy': 1.3, 'radius': 140,
         'flicker': 0.02, 'height': 30, 'on_layer': 'playfield'},
        {'id': 'cafe_facade', 'pos': [1650, 226], 'color': hexc(LA[2]), 'energy': 0.6, 'radius': 96, 'flicker': 0.0,
         'height': 20, 'on_layer': 'playfield'},
        {'id': 'control_booth_lamp', 'pos': [A['booth_lamp'][0] + 4, A['booth_lamp'][1] + 18], 'color': hexc(LA[3]),
         'energy': 0.85, 'radius': 82, 'flicker': 0.03, 'height': 24, 'on_layer': 'playfield'},
        {'id': 'saloon_window', 'pos': [ET['saloon'][0], ET['saloon'][1] + 52], 'color': hexc(LA[2]),
         'energy': 0.6, 'radius': 70, 'flicker': 0.0, 'height': 30, 'on_layer': 'playfield'},
        {'id': 'station_hall_window', 'pos': [ES['hall_window'][0] + ES['hall_window'][2] // 2,
                                              ES['hall_window'][1] + ES['hall_window'][3] - 10],
         'color': hexc(LA[2]), 'energy': 0.5, 'radius': 64, 'flicker': 0.0, 'height': 20, 'on_layer': 'station'},
        {'id': 'waiting_room_stove', 'pos': [EQ['stove'][0], EQ['stove'][1] + 30], 'color': hexc(LA[2]),
         'energy': 0.35, 'radius': 40, 'flicker': 0.12, 'height': 16, 'on_layer': 'playfield'},
        {'id': 'exit_arch_daylight', 'pos': [ax + aw // 2, 268], 'color': hexc(SN[3]), 'energy': 0.5,
         'radius': 92, 'flicker': 0.0, 'height': 40, 'on_layer': 'playfield'},
        {'id': 'buffer_stop_lamp', 'pos': list(ET['buffer_lamp']), 'color': hexc(RD[3]), 'energy': 0.35,
         'radius': 18, 'flicker': 0.0, 'height': 8, 'on_layer': 'playfield'},
    ]
    # ------------------------------------------------------------------ gameplay data (C3_DESIGN 4.1)
    w4 = ET['wagon4']
    hotspots = {
        'conductor': [600, 292], 'weighbill': [690, 290], 'departures': [900, 286], 'control': [1190, 292],
        'elena_cafe': [1640, 300], 'elena_control': [1222, 288], 'konrad_queue': [1300, 280], 'voronova': [330, 300],
        'exp_four_rails': [240, 270], 'exp_luggage': [420, 300], 'exp_pigeons': [480, 296], 'exp_bogie': [730, 272],
        'exp_mitten': [800, 304], 'exp_clock': [960, 292], 'exp_kiosk': [1010, 300], 'exp_poster': [1080, 290],
        'exp_return_notice': [1440, 292], 'exp_stove': [1520, 296], 'exp_exchange': [1770, 296],
        'exp_tram': [1880, 300], 'exp_footprints': [160, 268],
    }
    bog = w4['bogies'][1]
    hotspot_info = {
        'conductor': {'kind': 'dialogue', 'npc': 'conductor', 'mark': [616, 244], 'radius': 34, 'facing': 'left',
                      'desc': 'Schaffner at the left end of courier wagon 4 (gangway to car 3).'},
        'weighbill': {'kind': 'inspect', 'mark': list(w4['frame']), 'radius': 30,
                      'document': 'res://assets/ui/documents/veltrava_station_weighbill.png',
                      'desc': 'Brass frame with the weighing ticket between the two sealed doors of wagon 4.'},
        'departures': {'kind': 'inspect', 'mark': list(A['departures_board']), 'radius': 30,
                       'document': 'res://assets/ui/documents/veltrava_station_departures.png',
                       'desc': 'Departures board bolted to the canopy column; last row 23.40 KORDON-17, Gleis 5.'},
        'control': {'kind': 'dialogue', 'npc': 'border_officer', 'mark': [A['counter2'][0], A['counter2'][1] - 10],
                    'radius': 36, 'document': 'res://assets/ui/documents/veltrava_station_travel_order.png',
                    'desc': 'Counter 2 (Sowjetische Delegation) of the commission booth; travel order granted here.'},
        'elena_cafe': {'kind': 'dialogue', 'npc': 'elena', 'mark': [1650, 240], 'radius': 34, 'facing': 'left',
                       'desc': 'In front of Café „Korridor“, the warm focal light of the concourse.'},
        'elena_control': {'kind': 'npc_anchor', 'npc': 'elena', 'mark': [1222, 244],
                          'desc': 'Elena interprets at counter 2 (hidden after c3a_pass_control).'},
        'konrad_queue': {'kind': 'npc_anchor', 'npc': 'konrad', 'mark': [1300, 236],
                         'desc': 'Konrad first in the German queue at counter 1, seen from behind.'},
        'voronova': {'kind': 'npc_anchor', 'npc': 'voronova', 'mark': [346, 256],
                     'desc': 'Deputy minister Voronova below the warm saloon window of car 3.'},
        'exp_four_rails': {'kind': 'discover', 'mark': [240, 252], 'radius': 26,
                           'desc': 'Four-rail dual-gauge track (1520 + 1435) visible between the bogies of car 2.'},
        'exp_luggage': {'kind': 'discover', 'mark': [424, 270], 'radius': 26,
                        'desc': 'Porter cart: the delegation case No. 14, tied with cord, a wooden toy horse '
                                'strapped on top with a trouser belt; trunk with travel labels, hat box.'},
        'exp_pigeons': {'kind': 'discover', 'mark': [484, 268], 'radius': 26,
                        'desc': 'Pigeon corner at the platform edge (StationPigeons actor): two tug at a '
                                'sandwich, a third waits; more roost on the canopy girder.'},
        'exp_bogie': {'kind': 'discover', 'mark': [bog[0] + bog[2] // 2, bog[1] + 4], 'radius': 26,
                      'desc': 'Convertible bogie of wagon 4 with the empty second wheel-set notch and gauge plate.'},
        'exp_mitten': {'kind': 'discover', 'mark': [805, 277], 'radius': 24,
                       'desc': 'A red child\'s mitten left on the bench.'},
        'exp_clock': {'kind': 'discover', 'mark': list(EC['clock']), 'radius': 30,
                      'desc': 'Triple clock: BERLIN 7:55 / VELTRAVA 8:55 / MOSKAU 9:55.'},
        'exp_kiosk': {'kind': 'discover', 'mark': [1016, 236], 'radius': 26,
                      'desc': 'Newspaper kiosk ZEITUNGEN · ГАЗЕТЫ · JOURNAUX; the same photo on three front '
                              'pages (Moscow, Berlin, the city paper).'},
        'exp_poster': {'kind': 'discover', 'mark': list(A['poster']), 'radius': 26,
                       'desc': 'Commission poster „DREI KORRIDORE – EIN FRIEDEN“ on the column, peeling: '
                               'one drawing pin left (top left), three corners hanging.'},
        'exp_return_notice': {'kind': 'discover', 'mark': list(EQ['notice']), 'radius': 26,
                              'desc': 'Notice case with the trilingual notice „Büro für Rückführung“ (Zimmer 4) '
                                      'and a 23.40 slip.'},
        'exp_stove': {'kind': 'discover', 'mark': list(EQ['stove']), 'radius': 26,
                      'desc': 'Waiting-room door; the green tiled stove glows behind the glass, two porters '
                              'warm their hands, coal scuttle at its foot.'},
        'exp_exchange': {'kind': 'discover', 'mark': list(EQ['exchange']), 'radius': 26,
                         'desc': 'Exchange office WECHSELSTUBE · ОБМЕН ВАЛЮТЫ · CHANGE; chalk rate board RM / '
                                 'RBL / VKR, every rate corrected.'},
        'exp_tram': {'kind': 'discover', 'mark': [ax + aw // 2, ay + 60], 'radius': 30,
                     'desc': 'Exit arch: the snowy station square, tram line 7 waiting (StationTram actor) '
                             'with its hand-written trilingual line board.'},
        'exp_footprints': {'kind': 'discover', 'hidden': True, 'mark': [162, 266], 'radius': 18,
                           'desc': 'Several pairs of footprints cross the drift at the platform edge, step over '
                                   'the coping and go on in the snow of the track bed under wagon 2.'},
    }
    manifest = {
        'id': 'veltrava_station', 'palette': 'veltrava', 'world_size': list(WORLD),
        'camera': {'bounds': [0, 0, WORLD[0], WORLD[1]]},
        # polish pass: a touch brighter and warmer than the cloud pass's #C9CED8 (cold blue cast read as night
        # on the PC's Forward+ path); the canopy lamps keep the cold accent, the café the warm one
        'canvas_modulate': CANVAS_MODULATE,
        'layers': [{k: v for k, v in l.items() if k != 'size'} for l in layers],
        'props': [{k: v for k, v in p.items() if k != 'size'} for p in props],
        'walkable': [[0, 262], [1920, 262], [1920, 350], [0, 350]],
        'spawns': {'SP_C3_Platform': [120, 300]},
        'hotspots': hotspots,
        'hotspot_info': hotspot_info,
        'lights': lights,
        'fx': fx,
        'decals': decals,
        'actors': actors,
        'notes': {
            'generator': 'tools/pixelgen/env_veltrava_station.py (python3 -P tools/pixelgen/env_veltrava_station.py)',
            'date': '2026-11-04',
            'depth_bands': {'far_edge': [197, 210], 'track_4_rails': list(TR.FAR_RAILS), 'island': [226, 244],
                            'track_5_rails': list(TR.NEAR_RAILS), 'platform_edge': TR.PLATFORM_EDGE,
                            'walkable': [262, 350]},
            'tracks': 'Four-rail dual gauge on both tracks: outer pair 1520 mm, inner pair 1435 mm.',
            'snow': 'No screen-wide snow: under our canopy it does not snow. Snow tiles (fx/snow_*.png) fall only in '
                    'the open band behind the canopy edge (z between far planes and the near train) and in the '
                    'exit arch.',
            'insignia': 'Only pennants_reich (layer) and props flag_ussr / flag_reich carry insignia; neutral file + '
                        '_hist variant, resolved by Symbols.pick in layer_stack.gd (TECHNICAL_ARCHITECTURE 12.4).',
            'npc_anchors': 'conductor, elena_control, konrad_queue, voronova, elena_cafe, control are NOT painted; '
                           'the German queue (2 figures) and island figures are baked away from the anchors.',
            'light_on_layer': 'pos of a light with on_layer != playfield is given like a layer pos (where it appears '
                              'at camera x 0); it scrolls with that layer.',
            'warm_focal': 'cam 0: saloon window of car 3 (Voronova); cam 640: booth lamp at counter 2; cam 1280: '
                          'Café Korridor.',
            'polish_2026_11_06': 'Forward+ polish on the PC: dawn sky one ramp step lighter with a rose-cream band, '
                                 'canvas modulate #D5D3D6, sandstone station building and concourse (value groups '
                                 'like Karsk), glazed canopy roof lights, occupied compartments (car 3 frosted, no '
                                 'heating), platform lit from the open side, fluted fg columns + low fg silhouettes, '
                                 'fewer smoke ribbons; props match their find texts (poster, kiosk, exchange, '
                                 'notice, luggage, stove, footprints); ambient actors (pigeons, island walkers, '
                                 'tram, viaduct train, window life, breath) and the decal hook heater_leak_23.',
            'actors': 'scenes/levels/veltrava_station/*.tscn (station_pigeons / station_walkers / station_tram, '
                      'all extend scripts/levels/karsk/karsk_actor.gd) + the generic Karsk actors KarskTrain, '
                      'KarskWindowLife, KarskBreath configured by props; sprites in actors/ '
                      '(tools/pixelgen/env_veltrava_station_life.py).',
        },
    }
    sj = os.path.join(ENV_DIR, 'scene.json')
    # keeps the hand-added actors (AmbientWalkers, StationThaw: scenes this generator never writes) and later keys
    manifest = KEEP.merge_scene(_plain(manifest), KEEP.read_json(sj))
    KEEP.write_json(sj, manifest)   # same content as before: the file stays byte for byte
    write_provenance(KEEP.written_since(ENV_DIR, stamps))
    bad = {}
    for root, _, files in os.walk(ENV_DIR):
        for fn in files:
            if fn.endswith('.png') and not fn.endswith('_n.png') and not fn.endswith('_e.png'):
                arr = np.asarray(Image.open(os.path.join(root, fn)).convert('RGBA'))
                off = palette_report(arr)
                if off:
                    bad[fn] = off[:6]
    drop_orphan_imports()
    print('palette check:', 'OK' if not bad else bad)
    print('scene built in %.1fs' % (time.time() - t0))
    return manifest


if __name__ == '__main__':
    man = build()
    try:
        import env_veltrava_station_docs as DOCS
        DOCS.build_all()
    except ImportError:
        print('documents module missing (skipped)')
    for a in sys.argv[1:]:
        if a.startswith('--preview'):
            import env_veltrava_station_preview as PV
            out = a.split('=', 1)[1] if '=' in a else None
            print('previews ->', PV.run(out))
