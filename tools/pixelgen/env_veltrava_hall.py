"""env_veltrava_hall -- generator for L_C3_Hall 'Palais der Kommission, Veltrava' (Chapter 3, Konrad).

Run:  python3 -P tools/pixelgen/env_veltrava_hall.py            (deterministic, no network)

Produces
* assets/environments/veltrava_hall/   layers, props (+ *_hist flag variants), FX strips, scene.json,
                                       provenance.json
* assets/ui/documents/veltrava_hall_carbon.png + veltrava_hall_documents.json   (ev_c3_carbon)
* data/locale/de_env_veltrava_hall.json  alt texts of the hall documents
Previews: tools/pixelgen/env_veltrava_hall_preview.py (cameras 0 / 640 / 1280, written outside the repo
or into the git-ignored _preview/ folder).
Flags: --scene-only, --docs-only, --preview[=DIR]
"""
from __future__ import annotations

import json
import os
import sys
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import env_veltrava_hall_kit as kit        # noqa: E402  (registers pg.PALETTES['palais'])
import env_veltrava_hall_layout as L       # noqa: E402
import pg                                  # noqa: E402

ROOT = kit.ROOT
ENV_DIR = os.path.join(ROOT, 'assets', 'environments', 'veltrava_hall')
DOC_DIR = os.path.join(ROOT, 'assets', 'ui', 'documents')
LOCALE = os.path.join(ROOT, 'data', 'locale', 'de_env_veltrava_hall.json')

PRODUCED: list[tuple[str, str, str]] = []

LIGHT_COLORS = {'warm': '#E9B46E', 'cold': '#A9C0D0', 'white': '#D3DEE6', 'red': '#A8382E'}
# dynamic Godot lights (energy, radius, height, flicker) -- subtler than the bake, the art carries it
DYN = {
    'entrance_day': (0.45, 170, 40, 0.0, 'cold'), 'foyer_window': (0.45, 150, 40, 0.0, 'cold'),
    'office_window': (0.32, 110, 30, 0.0, 'cold'), 'lunette_2': (0.25, 130, 60, 0.0, 'cold'),
    'vest_lantern': (0.4, 100, 30, 0.04, 'warm'), 'cloak_lamp': (0.95, 120, 20, 0.02, 'warm'),
    'chandelier': (1.05, 200, 44, 0.0, 'warm'), 'sconce_buffet_l': (0.28, 60, 14, 0.03, 'warm'),
    'sconce_buffet_r': (0.28, 60, 14, 0.03, 'warm'), 'saal_doors': (0.6, 92, 8, 0.0, 'warm'),
    'typist_lamp': (0.5, 80, 16, 0.03, 'warm'), 'table_lamp': (0.95, 120, 10, 0.02, 'warm'),
    'globe_1470': (0.28, 90, 30, 0.0, 'warm'), 'globe_1830': (0.28, 90, 30, 0.0, 'warm'),
    'booth_1_lamp': (0.28, 46, 8, 0.0, 'warm'), 'booth_2_lamp': (1.0, 110, 10, 0.02, 'warm'),
    'booth_3_lamp': (0.28, 46, 8, 0.0, 'warm'), 'saal_glow_1': (0.32, 64, 4, 0.0, 'white'),
    'saal_glow_2': (0.32, 64, 4, 0.0, 'white'), 'saal_glow_3': (0.32, 64, 4, 0.0, 'white'),
    'sign_ruhe': (0.18, 36, 6, 0.0, 'red'), 'sconce_interp': (0.25, 60, 14, 0.03, 'warm'),
}
CANVAS_MODULATE = '#C9CDCC'
Z = {'ext_sky': -100, 'ext_town': -97, 'ext_river': -95, 'ext_square': -90, 'saal_far': -84, 'saal_near': -82,
     'room': -50, 'shafts': 10, 'fg_frame': 60}
EXT_DESC = {
    'ext_sky': 'overcast winter morning sky (seen through every window)',
    'ext_town': 'far river bank with the Line: double fence, watchtowers, floodlight masts (hazy)',
    'ext_river': 'frozen river, the three-arched bridge with a barrier, old-town roofs, dome and spire',
    'ext_square': 'the snowy square in front of the palais: stucco houses, tram stop, lamp post, car',
    'saal_far': 'Grosser Saal head wall: windows, panelling, dais with six small flags, chandeliers',
    'saal_far_hist': 'same as saal_far with the historical USSR / Reich flags (Symbols.pick variant)',
    'saal_near': 'the horseshoe table seen from the booths: presidium, delegates, secretariat table',
}


def rel(p: str) -> str:
    return os.path.relpath(p, ROOT).replace('\\', '/')


def record(path: str, gen: str, desc: str):
    PRODUCED.append((rel(path), gen, desc))


def save_layer(lay, base: str, normal=True, gen='env_veltrava_hall_room.py', desc=''):
    os.makedirs(os.path.dirname(base), exist_ok=True)
    info = lay.save(base, normal=normal)
    record(base + '.png', gen, desc)
    if normal:
        record(base + '_n.png', gen, desc + ' -- normal map (OpenGL +Y up)')
    if info['emission']:
        record(base + '_e.png', gen, desc + ' -- emission mask (unshaded glow)')
    return info


def clean_env_dir():
    """Remove previously generated PNGs so renamed / dropped files never linger (imports stay)."""
    if not os.path.isdir(ENV_DIR):
        return
    for root, _dirs, files in os.walk(ENV_DIR):
        if '_preview' in root:
            continue
        for f in files:
            if f.endswith('.png'):
                os.remove(os.path.join(root, f))


# =========================================================================== scene
def build_scene():
    import env_veltrava_hall_room as ER
    import env_veltrava_hall_props as EP
    import env_veltrava_hall_ext as EX
    import env_veltrava_hall_fg as EF
    import env_veltrava_hall_fx as EFX
    t0 = time.time()
    room = ER.Room()
    room.build()
    props = EP.build_all()
    prop_lights = [lt for p in props for lt in p.lights]
    ER.bake(room, extra_lights=prop_lights)
    for p in props:
        EP.bake_prop(p, room.all_lights, shaft_air=room.shaft_air)
    ER.reflect_floor(room, props)
    ext = EX.build_all()
    fg = EF.build()
    shafts = build_shaft_overlay(room)
    clean_env_dir()
    fx_files, fx_entries = EFX.build_all(ENV_DIR, room)
    for (fp, desc) in fx_files:
        record(fp, 'env_veltrava_hall_fx.py', desc)
    print('  scene built in %.1fs' % (time.time() - t0))

    os.makedirs(ENV_DIR, exist_ok=True)
    layers = []
    for name in ('ext_sky', 'ext_town', 'ext_river', 'ext_square', 'saal_far', 'saal_near'):
        lay, px_ = ext[name]
        info = save_layer(lay, os.path.join(ENV_DIR, name), normal=False, gen='env_veltrava_hall_ext.py',
                          desc=EXT_DESC[name])
        y = EX.SAAL_Y if name.startswith('saal') else 0
        entry = {'name': name, 'file': name + '.png', 'pos': [px_, y],
                 'parallax': [L.PARALLAX[name], 1.0], 'z': Z[name], 'normal': False,
                 'emission': info['emission'], 'lit': False, 'repeat_x': 0}
        if name == 'saal_far':
            hl, _ = ext['saal_far_hist']
            hinfo = save_layer(hl, os.path.join(ENV_DIR, 'saal_far_hist'), normal=False,
                               gen='env_veltrava_hall_ext.py', desc=EXT_DESC['saal_far_hist'])
            entry['hist_variant'] = 'saal_far_hist.png'
            if hinfo['emission'] != info['emission']:
                print('  WARNING saal_far emission mismatch')
        layers.append(entry)
    info = save_layer(room.lay, os.path.join(ENV_DIR, 'room'),
                      desc='palais interior: vestibule, foyer + staircase, Protokollbuero, interpreters\' corridor')
    layers.append({'name': 'room', 'file': 'room.png', 'pos': [0, 0], 'parallax': [1, 1], 'z': Z['room'],
                   'normal': True, 'emission': info['emission'], 'lit': True})
    save_layer(shafts, os.path.join(ENV_DIR, 'shafts'), normal=False, gen='env_veltrava_hall.py',
               desc='volumetric daylight-shaft veil (soft alpha, plain alpha blending)')
    layers.append({'name': 'shafts', 'file': 'shafts.png', 'pos': [0, 0], 'parallax': [1, 1], 'z': Z['shafts'],
                   'normal': False, 'emission': False, 'lit': False,
                   'note': 'soft alpha veil (max ~16 %); reads as dithered light in front of actors'})
    save_layer(fg, os.path.join(ENV_DIR, 'fg_frame'), normal=False, gen='env_veltrava_hall_fg.py',
               desc='foreground framing silhouettes (columns, velvet drapes, palm, chair)')
    layers.append({'name': 'fg_frame', 'file': 'fg_frame.png', 'pos': [0, 0], 'parallax': [L.PARALLAX['fg_frame'], 1.0],
                   'z': Z['fg_frame'], 'normal': False, 'emission': False, 'lit': False})
    prop_entries = []
    for p in props:
        info = save_layer(p.lay, os.path.join(ENV_DIR, 'props', p.name), gen='env_veltrava_hall_props.py',
                          desc=p.note)
        e = {'name': p.name, 'file': 'props/%s.png' % p.name, 'pos': [p.x, p.y], 'base_y': p.base_y,
             'size': [p.w, p.h], 'normal': True, 'emission': info['emission']}
        if p.hist_lay is not None:
            hb = os.path.join(ENV_DIR, 'props', p.name + '_hist')
            p.hist_lay.save(hb, normal=False)
            record(hb + '.png', 'env_veltrava_hall_props.py', p.note.split(' (')[0] + ' -- historical insignia '
                   'variant (Symbols.pick, TECHNICAL_ARCHITECTURE 12.4)')
            e['hist_variant'] = 'props/%s_hist.png' % p.name
        prop_entries.append(e)

    lights = []
    for lt in room.all_lights:
        name = lt.get('name', '')
        if name not in DYN:
            continue
        e_, r_, h_, fl_, kind = DYN[name]
        lights.append({'name': name, 'pos': [int(round(lt['pos'][0])), int(round(lt['pos'][1]))],
                       'color': LIGHT_COLORS[kind], 'energy': e_, 'radius': r_, 'flicker': fl_, 'height': h_,
                       'on_layer': 'playfield'})
    hotspot_info = build_hotspot_info()
    scene = {
        'id': 'veltrava_hall', 'palette': 'palais', 'palette_exterior': 'veltrava',
        'world_size': [L.WORLD_W, L.WORLD_H],
        'camera': {'bounds': [0, 0, L.WORLD_W, L.WORLD_H]},
        'canvas_modulate': CANVAS_MODULATE,
        'layers': layers,
        'props': prop_entries,
        'walkable': [[L.WALK_X[0], L.WALK_BAND[0]], [L.WALK_X[1], L.WALK_BAND[0]],
                     [L.WALK_X[1], L.WALK_BAND[1]], [L.WALK_X[0], L.WALK_BAND[1]]],
        'spawns': {k: list(v) for k, v in L.SPAWNS.items()},
        'hotspots': {k: list(v) for k, v in L.HOTSPOTS.items()},
        'lights': lights,
        'fx': fx_entries,
        # ---- extension data (not required by the level contract; safe to ignore)
        'hotspot_info': hotspot_info,
        'npcs': {k: {'feet': list(v), 'facing': 'left' if k != 'voronova' else 'right'} for k, v in L.NPC_FEET.items()},
        'windows': {'glass_note': 'room.png is transparent at the glazing; ext_* / saal_* layers show through',
                    'saal_windows': [[a, b, c - a, d - b] for (a, b, c, d) in room.saal_windows]},
        'notes': [
            'Side view like L_M1_Archive: feet line y 300, walk band 296-306 (flat 8x2 collider), x 18-1902.',
            'Warm focal lights: cloakroom lamp (vestibule, Kessler), chandelier (foyer), Saal-door glass '
            '(seating easel), table lamp (Protokollbuero), booth 2 lamp (interpreters\' corridor).',
            'Flags: props/flag_ussr.png and props/flag_reich.png are the neutral defaults; *_hist.png variants '
            '(and saal_far_hist.png) carry the historical insignia; layer_stack resolves them via Symbols.pick.',
            'Elena\'s charcoal coat with the wine-red scarf hangs on the sixth cloakroom hook (x ~264).',
            'The seating easel matches the puzzle: horseshoe, presidium on top, mics clockwise from 1, '
            'secretariat (12) at the open end; only 1, 2 and 12 are printed.',
            'Booth 2 (x 1622-1682): empty chair, headset dangling on its cable, pencil, blotter pad, lamp on.',
            'The evacuation plan shows a dashed staff corridor down to a cellar room (foreshadowing).',
            'No story character is painted into the art; NPC sprites stand at the npc anchors.',
        ],
        'meta': {'mode': 'side', 'feet_y': L.WALK_Y, 'generator': 'tools/pixelgen/env_veltrava_hall.py',
                 'date': kit.DATE, 'palette_ramps': kit.PALAIS,
                 'palette_note': "'palais' = c3.json palettes.palais + daylight #D3DEE6 (cold near-white)"},
    }
    sj = os.path.join(ENV_DIR, 'scene.json')
    with open(sj, 'w', encoding='utf-8') as f:
        json.dump(scene, f, indent=1, ensure_ascii=False)
    record(sj, 'env_veltrava_hall.py', 'art manifest (TECHNICAL_ARCHITECTURE 3.1)')

    # ---- checks
    issues = EF.check_clearance(fg)
    if issues:
        print('  WARNING fg covers hotspots:', issues)
    allowed = kit.palais_hex()
    for nm, lay in [('room', room.lay), ('fg', fg)] + [(p.name, p.lay) for p in props] + \
            [('saal_far', ext['saal_far'][0]), ('saal_near', ext['saal_near'][0])]:
        n, bad = kit.palette_report(lay.c, allowed)
        if bad:
            print('  WARNING %s uses non-palette colours: %s' % (nm, bad[:6]))
    allowed_v = kit.velt_hex()
    for nm in ('ext_sky', 'ext_town', 'ext_river', 'ext_square'):
        n, bad = kit.palette_report(ext[nm][0].c, allowed_v)
        if bad:
            print('  WARNING %s uses non-palette colours: %s' % (nm, bad[:6]))
    for note in kit.check_c3_palettes():
        print('  NOTE', note)
    return scene, room


def build_shaft_overlay(room):
    """Soft daylight veil above the playfield (plain alpha; the post palette snap dithers it)."""
    air = room.shaft_air
    H, W = air.shape
    lay = pg.Layer(W, H, 'shafts')
    y = np.arange(H, dtype=np.float32)[:, None]
    fade = np.clip((L.FLOOR + 26 - y) / 50, 0, 1) * np.clip((y - 20) / 40, 0, 1)
    a = (np.clip(air, 0, 1) ** 1.3) * fade
    a[room.glass] = 0
    from env_veltrava_hall_kit import dilate
    near_glass = dilate(room.glass, 3)
    a[near_glass] *= 0.25
    alpha = np.clip(np.round(a * 42), 0, 255).astype(np.uint8)
    col = pg.hx(kit.PALAIS['daylight'][4])
    lay.c[..., 0], lay.c[..., 1], lay.c[..., 2] = col[0], col[1], col[2]
    lay.c[..., 3] = alpha
    lay.c[alpha == 0] = 0
    return lay


def build_hotspot_info():
    kinds = {'kessler': 'story', 'seating': 'story', 'booth_log': 'story', 'protocol_table': 'story',
             'booth_2': 'story', 'alexei_meet': 'story'}
    for k in ('elena_arrival', 'voronova_bg', 'typist', 'journalist'):
        kinds[k] = 'npc_anchor'
    what = {
        'kessler': 'Kessler stands at x 316 (hotspot_offset +16) by the lit cloakroom counter',
        'elena_arrival': 'Elena at x 353, in front of the directory board',
        'seating': 'brass easel with the seating plan in front of the doors to the Grosser Saal',
        'booth_log': 'wire basket of carbon copies on the oak cabinet under the office window',
        'protocol_table': 'the big baize table with the brass desk lamp',
        'booth_2': 'booth 2 (RU <-> DE): empty chair, dangling headset, pencil, blotter pad, lamp on',
        'alexei_meet': 'in front of booth 3; Alexei appears at x 1718',
        'voronova_bg': 'below the staircase landing (background NPC)',
        'typist': 'typist at x 1134 in front of her desk (typewriter, carbon box)',
        'journalist': 'journalist at x 574 at the foot of the grand staircase',
        'exp_flags': 'six flags: commission, USSR, Reich, Sweden, Switzerland, Finland',
        'exp_cloakroom': "numbered hooks; Elena's charcoal coat with the wine-red scarf",
        'exp_photos': 'photo wall: the 1953 armistice signing',
        'exp_chandelier': 'the crystal chandelier above',
        'exp_buffet': 'untouched Sekt and caviar on crushed ice',
        'exp_window': 'old town, the frozen river, the bridge and the watchtowers of the Line',
        'exp_evac_plan': 'evacuation plan: a dashed staff corridor leads down to a cellar room',
        'exp_treaty_shelf': 'bookcase of bound treaty volumes 1953 / 1963',
        'exp_mimeograph': 'stencil duplicator with fresh copies',
        'exp_headsets': 'glazed cabinet with numbered headsets (two hooks empty)',
    }
    out = {}
    for k, v in L.HOTSPOTS.items():
        out[k] = {'kind': kinds.get(k, 'exploration'), 'stand': list(v), 'focus': list(L.FOCUS.get(k, v)),
                  'facing': L.APPROACH_FACING.get(k, 'back'), 'what': what.get(k, '')}
    return out


# =========================================================================== provenance
def write_provenance():
    out = {'generator': 'tools/pixelgen/env_veltrava_hall.py (+ _kit, _layout, _room, _props, _ext, _fx, _fg, '
                        '_docs, _preview)',
           'date': kit.DATE,
           'licence': 'project-owned original artwork, generated procedurally; no copied, traced, downloaded or '
                      'AI-generated pixels; bitmap fonts hand-defined in env_veltrava_hall_kit.py',
           'run': 'python3 -P tools/pixelgen/env_veltrava_hall.py',
           'files': [{'path': p, 'generator': 'tools/pixelgen/' + g, 'content': d} for p, g, d in sorted(PRODUCED)]}
    p = os.path.join(ENV_DIR, 'provenance.json')
    with open(p, 'w', encoding='utf-8') as f:
        json.dump(out, f, indent=1, ensure_ascii=False)


# =========================================================================== main
def main(argv):
    t0 = time.time()
    scene = None
    if '--docs-only' not in argv:
        print('[env_veltrava_hall] scene ...')
        scene, _room = build_scene()
    if '--scene-only' not in argv:
        import env_veltrava_hall_docs as ED
        print('[env_veltrava_hall] documents ...')
        for path, desc in ED.build_all(DOC_DIR, LOCALE):
            record(path, 'env_veltrava_hall_docs.py', desc)
    if scene is not None and '--docs-only' not in argv and '--scene-only' not in argv:
        write_provenance()
    for a in argv:
        if a.startswith('--preview'):
            import env_veltrava_hall_preview as EV
            out = a.split('=', 1)[1] if '=' in a else os.path.join(ENV_DIR, '_preview')
            EV.render_all(out)
    print('[env_veltrava_hall] done in %.1fs, %d files' % (time.time() - t0, len(PRODUCED)))


if __name__ == '__main__':
    main(sys.argv[1:])
