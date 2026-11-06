"""env_c4p2_berlin -- generator for L_C4P2_Berlin (Chapter 4 part 2, round 10; C4P2_DESIGN.md §4.2, owner env-berlin).

Run:  py -3 -P tools/pixelgen/env_c4p2_berlin.py [--preview=DIR] [--no-docs]     (deterministic, no network)

Produces assets/environments/berlin_c4p2/ (one level file, two Story scenes, two walk areas):
* scene A 'Ostbahnhof, Korridorbahnsteig K' (L_C4P2_BerlinA, Monday 20.30): st_sky, st_city, st_hall, st_track2
  (parallax, unlit), station.png (+ _n / _e; the playfield 0..918), fg_station.png; props/counter_front (the
  buffet counter, y-sorted: the buffet woman behind it); patches: Marta's duty roster „Linie 3“ / „Linie 74“
  (art gate choice c4d_choose), the insignia sites (the liaison booth's two plates, the plate on the engine's cab:
  neutral + *_hist, TECHNICAL_ARCHITECTURE §12.4);
* scene B 'Kolonnenstraße 14' (L_C4P2_BerlinB, Tuesday 22.10): yd_sky, yd_dome (+ _hist banners), yd_roofs,
  yard.png (+ _n / _e; placed at x 918), fg_yard.png; patches: after c4h_solve_house the three stairwells lit (the
  sweep went up), the car's headlights in the passage, the candle in the cobbler's souterrain; the Blockleitung's
  notice (neutral: no emblem / _hist: the party eagle);
* life/ and fx/ strips (env_c4p2_berlin_strips / _life): the people behind glass, the households in the windows,
  steam, snow, smoke, the blinking lamp; crowd/ walker rigs + walkers_a.json (env_c4p2_berlin_crowd);
* scene.json (layers / props / decals / fx / lights / actors with the gate keys after / until / choice and the
  per-scene key "scene", every spawn / hotspot / NPC anchor / blocker / camera zone of the story stream's
  placeholder), merged over the previous file by tools/pixelgen/env_keep.py (keys and actors of other writers
  stay), provenance.json (own rows + other generators' rows), the inspect documents (env_c4p2_berlin_docs).
scripts/levels/c4p2/berlin_c4p2_level.gd (on top of annex_level.gd) applies the gates, the scene filter, the camera
zones and the footsteps of the place.
"""
from __future__ import annotations

import json
import os
import sys
import time

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import env_keep as KEEP                  # noqa: E402
import env_c4p2_berlin_kit as K          # noqa: E402
import env_c4p2_berlin_layout as L       # noqa: E402
import env_c4p2_berlin_station as ST     # noqa: E402
import env_c4p2_berlin_yard as YD        # noqa: E402
import env_c4p2_berlin_strips as SP      # noqa: E402
import env_c4p2_berlin_life as LF        # noqa: E402
import env_c4p2_berlin_crowd as CR       # noqa: E402

ROOT = K.ROOT
ENV_DIR = os.path.join(ROOT, 'assets', 'environments', 'berlin_c4p2')
ENV_REL = 'assets/environments/berlin_c4p2'
GEN = 'tools/pixelgen/env_c4p2_berlin.py'
FAMILY = 'tools/pixelgen/env_c4p2_berlin'
PRODUCED: list[tuple[str, str, str]] = []
A, B = L.SCENE_A, L.SCENE_B
XB = L.SEAM_B
PAL_OF = {}                               # relpath -> palette dict (palette check)

COL = {'sodium': '#E2AC4A', 'warm': '#F0C487', 'lamp': '#F8DB96', 'cold': '#C6CACE', 'blue': '#94A0B2',
       'window': '#E8B65A', 'red': '#C8503C', 'white': '#E8EAEC'}


# =========================================================================== io
def rel(p: str) -> str:
    return os.path.relpath(p, ROOT).replace('\\', '/')


def save(arr, relpath, gen, desc, pal=None):
    path = os.path.join(ENV_DIR, relpath)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    Image.fromarray(np.asarray(arr).astype(np.uint8), 'RGBA').save(path)
    PRODUCED.append((rel(path), gen, desc))
    if pal is not None:
        PAL_OF[rel(path)] = pal
    return relpath


def maps(lay):
    return lay.c.copy(), lay.normal_map(3.0), lay.em.copy()


def write_layer(name, m, gen, desc, pal):
    c, n, e = m
    save(c, name + '.png', gen, desc, pal)
    save(n, name + '_n.png', gen, desc + ' -- normal map (OpenGL +Y up)')
    has_e = bool(e[..., 3].any())
    if has_e:
        save(e, name + '_e.png', gen, desc + ' -- emission mask (unshaded glow)', pal)
    return has_e


def diff_mask(a, b):
    d = np.zeros(a[0].shape[:2], bool)
    for x, y in zip(a, b):
        d |= np.any(x != y, axis=-1)
    return d


def box_of(mask, pad=1, xr=None, yr=None):
    m = mask.copy()
    if xr is not None:
        m[:, :max(0, xr[0])] = False
        m[:, max(0, xr[1]):] = False
    if yr is not None:
        m[:max(0, yr[0]), :] = False
        m[max(0, yr[1]):, :] = False
    if not m.any():
        return None
    ys, xs = np.nonzero(m)
    h, w = mask.shape
    return (max(0, xs.min() - pad), max(0, ys.min() - pad), min(w, xs.max() + pad + 1), min(h, ys.max() + pad + 1))


def write_patch(name, m, box, gen, desc, pal, hist_m=None):
    """An exact crop of a baked layer with one state applied (+ its normal map, emission, and the _hist trio)."""
    x0, y0, x1, y1 = box
    c, n, e = m
    sl = (slice(y0, y1), slice(x0, x1))
    save(c[sl], 'patches/%s.png' % name, gen, desc, pal)
    save(n[sl], 'patches/%s_n.png' % name, gen, desc + ' -- normal map')
    has_e = bool(e[sl][..., 3].any())
    if hist_m is not None:
        hc, hn, he = hist_m
        save(hc[sl], 'patches/%s_hist.png' % name, gen,
             desc + ' -- historical insignia variant (Symbols.pick, TECHNICAL_ARCHITECTURE 12.4)', pal)
        save(hn[sl], 'patches/%s_hist_n.png' % name, gen, desc + ' -- historical, normal map')
        has_e = has_e or bool(he[sl][..., 3].any())
        if has_e:
            save(he[sl], 'patches/%s_hist_e.png' % name, gen, desc + ' -- historical, emission', pal)
    if has_e:
        save(e[sl], 'patches/%s_e.png' % name, gen, desc + ' -- emission mask', pal)
    return has_e


# =========================================================================== A: the Ostbahnhof
def build_station(scene: dict):
    gen = 'tools/pixelgen/env_c4p2_berlin_station.py'
    base = ST.bake_station({})
    mb = maps(base.lay)
    write_layer('station', mb, gen, 'Ostbahnhof, Korridorbahnsteig K: track K with the D 303 (engine 01 064, courier van '
                                   'with two seals, the uncoupled gap, dining car, sleeping car) and platform K (liaison '
                                   'booth at the barrier, departure board, baggage counter and scale, buffet, kiosk, '
                                   'porters\' carts, lamps, clock, the Corridor fence), x 0..918', K.OST)
    scene['layers'].append({'name': 'station', 'file': 'station.png', 'pos': [0, 0], 'parallax': [1, 1], 'z': -50,
                            'normal': True, 'emission': True, 'emission_strength': 0.6, 'lit': True, 'scene': A})
    # Marta's duty roster on the counter (art gate c4d_choose)
    roster_boxes = []
    for line, cond, nm in (('3', {'c4d_choose': 'name_marta'}, 'roster_l3'),
                           ('74', {'c4d_choose': '!name_marta'}, 'roster_l74')):
        st = ST.bake_station({'roster': line})
        m = maps(st.lay)
        box = box_of(diff_mask(mb, m), xr=(L.BUFFET[0], L.BUFFET[1]))
        roster_boxes.append(box)
        has_e = write_patch(nm, m, box, gen, 'Marta\'s duty roster on the buffet counter: „Linie %s“ (her gloves on it)'
                            % line, K.OST)
        scene['decals'].append({'name': nm, 'file': 'patches/%s.png' % nm, 'pos': [int(box[0]), int(box[1])],
                                'z': -46, 'lit': True, 'normal': True, 'emission': has_e, 'scene': A,
                                'choice': cond, 'fade': 0.0,
                                'note': 'C4P2_DESIGN §2.6: Linie 3 on the named route, Linie 74 otherwise'})
    # insignia sites: the liaison booth's two plates, the plate on the engine's cab
    sth = ST.bake_station({'hist': True})
    mh = maps(sth.lay)
    dm = diff_mask(mb, mh)
    for nm, xr, desc in (('plates_booth', (L.BOOTH[0] - 2, L.BOOTH[1] + 2),
                          'the liaison booth\'s two plates: the Reich (neutral Reichssiegel / historical state eagle) and '
                          'the Soviet Union (neutral gear-and-wheat / historical hammer and sickle)'),
                         ('plate_cab', (base.cab_plate[0] - 1, base.cab_plate[0] + base.cab_plate[2] + 1),
                          'the plate on the engine\'s cab: neutral „DR“ monogram / historical Reichsbahn eagle')):
        box = box_of(dm, xr=xr)
        has_e = write_patch(nm, mb, box, gen, desc, K.OST, hist_m=mh)
        scene['decals'].append({'name': nm, 'file': 'patches/%s.png' % nm, 'pos': [int(box[0]), int(box[1])],
                                'z': -48, 'lit': True, 'normal': True, 'emission': has_e, 'scene': A,
                                'hist_variant': 'patches/%s_hist.png' % nm,
                                'note': 'insignia site (12.4)'})
    build_counter_prop(scene, base, mb, roster_boxes)
    # Godot lights for the actors (the art has them baked)
    for li in base.lights:
        if li['name'].startswith('diner_win_') and li['name'] not in ('diner_win_0', 'diner_win_2', 'diner_win_4'):
            continue
        e = {'name': li['name'], 'pos': [round(li['pos'][0], 1), round(li['pos'][1], 1)],
             'color': COL['sodium'] if li['name'].startswith('sodium') else COL['warm'],
             'energy': round(min(1.0, li['energy'] * 0.8), 2), 'radius': int(li['radius']), 'flicker': 0.0,
             'height': int(li.get('height', 24)), 'on_layer': 'playfield', 'scene': A}
        if li['name'] == 'firebox':
            e['flicker'] = 0.12
        scene['lights'].append(e)
    scene['lights'].append({'name': 'hall_end', 'pos': [-30, 220], 'color': COL['cold'], 'energy': 0.45,
                            'radius': 220, 'flicker': 0.0, 'height': 50, 'on_layer': 'playfield', 'scene': A})
    return base


def counter_mask():
    """Pixels the station's counter() paints (counter body and what stands on it), read from the paint arrays before
    and after the call -- independent of the light fields."""
    st = ST.Station({})
    orig = st.counter
    snap = {}

    def counter():
        rid0, tone0 = st.lay.rid.copy(), st.lay.tone.copy()
        orig()
        snap['mask'] = (st.lay.rid != rid0) | (st.lay.tone != tone0)
    st.counter = counter
    st.build()
    return snap['mask']


def build_counter_prop(scene, base, mb, roster_boxes):
    gen = 'tools/pixelgen/env_c4p2_berlin_station.py'
    mask = counter_mask()
    for (x0, y0, x1, y1) in roster_boxes:
        mask[y0:y1, x0:x1] = False
    bx0, by0, bx1, by1 = box_of(mask, pad=0)
    sl = (slice(by0, by1), slice(bx0, bx1))
    a = mask[sl]
    c, n, e = mb
    desc = 'the buffet counter and what stands on it, cut from station.png (y-sorted prop: the buffet woman behind ' \
           'it, Marta and the walk band in front of it)'
    out = []
    for arr in (c, n):
        p = arr[sl].copy()
        p[..., 3] = np.where(a, 255, 0)
        p[~a] = 0
        out.append(p)
    save(out[0], 'props/counter_front.png', gen, desc, K.OST)
    save(out[1], 'props/counter_front_n.png', gen, desc + ' -- normal map')
    ee = e[sl].copy()
    ee[~a] = 0
    has_e = bool(ee[..., 3].any())
    if has_e:
        save(ee, 'props/counter_front_e.png', gen, desc + ' -- emission mask', K.OST)
    scene['props'].append({'name': 'counter_front', 'file': 'props/counter_front.png', 'pos': [int(bx0), int(by0)],
                           'base_y': 292, 'size': [int(bx1 - bx0), int(by1 - by0)], 'normal': True,
                           'emission': has_e, 'scene': A,
                           'note': 'the buffet woman (walker, feet y 281) stands behind it; Marta (318, 300) in front'})


def build_station_distant(scene: dict):
    gen = 'tools/pixelgen/env_c4p2_berlin_station.py'
    sky = ST.sky_layer()
    save(sky.c, 'st_sky.png', gen, 'night over Berlin through the open end of the hall: low cloud lit by the city', K.OST)
    city = ST.city_layer()
    save(city.c, 'st_city.png', gen, 'the night city beyond the hall: blocks with lit windows, masts, track signals',
         K.OST)
    if city.em[..., 3].any():
        save(city.em, 'st_city_e.png', gen, 'city layer -- emission (lit windows, signal lights)', K.OST)
    hall = ST.hall_layer()
    save(hall.c, 'st_hall.png', gen, 'the hall\'s shell: the glass barrel vault under its smoke lantern -- lattice arches '
                                    'with lit lower chords, purlins, panes clear / snowed / sooted / boarded, cables, '
                                    'pigeons, the glow of the lamp rows -- the far brick wall with arched windows, the '
                                    'end screen of the vault', K.OST)
    tr2 = ST.track2_layer()
    save(tr2.c, 'st_track2.png', gen, 'the next track: the green windowless car with barred hatches and the chalk '
                                     '„Di – Kordon“, one hatch frosted from inside; a dwarf signal', K.OST)
    if tr2.em[..., 3].any():
        save(tr2.em, 'st_track2_e.png', gen, 'next track -- emission (the dwarf signal)', K.OST)
    fg = ST.fg_layer()
    save(fg.c, 'fg_station.png', gen, 'the platform wall with cables and weep holes, signal wires, the near track with '
                                      'the lamps in its rails, meltwater, coal, litter, a dwarf signal, the stair down to '
                                      'the underpass (foreground)', K.OST)
    scene['layers'][0:0] = [
        {'name': 'st_sky', 'file': 'st_sky.png', 'pos': [0, 0], 'parallax': [0.05, 1.0], 'z': -100, 'normal': False,
         'emission': False, 'lit': False, 'scene': A},
        {'name': 'st_city', 'file': 'st_city.png', 'pos': [0, 60], 'parallax': [0.15, 1.0], 'z': -96, 'normal': False,
         'emission': bool(city.em[..., 3].any()), 'emission_strength': 0.5, 'lit': False, 'scene': A},
        {'name': 'st_hall', 'file': 'st_hall.png', 'pos': [0, 0], 'parallax': [0.4, 1.0], 'z': -90, 'normal': False,
         'emission': False, 'lit': False, 'scene': A},
        {'name': 'st_track2', 'file': 'st_track2.png', 'pos': [0, 136], 'parallax': [0.92, 1.0], 'z': -60,
         'normal': False, 'emission': bool(tr2.em[..., 3].any()), 'emission_strength': 0.4, 'lit': False, 'scene': A,
         'note': 'seen through the uncoupled gap of the D 303 (x 530..622): the green car (exp_green_car)'},
    ]
    scene['layers'].append({'name': 'fg_station', 'file': 'fg_station.png', 'pos': [0, 318], 'parallax': [1.25, 1.0],
                            'z': 60, 'normal': False, 'emission': False, 'lit': False, 'scene': A})


# =========================================================================== B: Kolonnenstraße 14
def build_yard(scene: dict):
    gen = 'tools/pixelgen/env_c4p2_berlin_yard.py'
    base = YD.bake_yard({})
    mb = maps(base.lay)
    write_layer('yard', mb, gen, 'Kolonnenstraße 14, Tuesday night: the gate passage with the Blockleitung\'s notice, '
                                'the courtyard façades of front wing, side wing and back wing (every lit window a '
                                'household of the house puzzle), the coal, the cellar hatch, the lodge window with the '
                                'card box, the bins, the pump, the carpet rack, the frozen laundry, the cobbler\'s '
                                'souterrain (x 918..1920)', K.YARD)
    scene['layers'].append({'name': 'yard', 'file': 'yard.png', 'pos': [XB, 0], 'parallax': [1, 1], 'z': -50,
                            'normal': True, 'emission': True, 'emission_strength': 0.6, 'lit': True, 'scene': B})
    # after c4h_solve_house: the stairwells lit, the headlights, the candle
    aft = YD.bake_yard({'after': True})
    ma = maps(aft.lay)
    dm = diff_mask(mb, ma)
    for nm, xr, yr, desc in (
            ('stairs_v', (950 - XB, 992 - XB), (80, 240), 'the front wing\'s stairwell lit: the sweep went up'),
            ('stairs_s', (1268 - XB, 1306 - XB), (80, 240), 'the side wing\'s stairwell lit: the sweep went up'),
            ('stairs_h', (1694 - XB, 1730 - XB), (80, 240), 'the back wing\'s stairwell lit: the sweep went up'),
            ('candle_ws', (1730 - XB, 1890 - XB), (268, 300), 'a candle in the cobbler\'s souterrain: Ilse is there'),
            ('car', (0, L.STREET_DOOR[1] - XB + 1), (256, 302), 'the sweep\'s car in the street, head-on in the '
                                                              'doorway, its headlamps glaring'),
            ('headlights', (L.STREET_DOOR[1] - XB + 1, 1110 - XB), (288, 318), 'the headlights\' light on the '
                                                                              'passage\'s setts, the men\'s long '
                                                                              'shadows')):
        box = box_of(dm, xr=xr, yr=yr)
        if box is None:
            print('  no after-change in', nm)
            continue
        has_e = write_patch(nm, ma, box, gen, desc, K.YARD)
        scene['decals'].append({'name': nm, 'file': 'patches/%s.png' % nm, 'pos': [int(box[0]) + XB, int(box[1])],
                                'z': -48, 'lit': True, 'normal': True, 'emission': has_e, 'scene': B,
                                'after': ['c4h_solve_house'], 'fade': 0.8,
                                'note': 'under the life strips (z -47): the sweep\'s men and the candle play on it'})
    # the Blockleitung's notice: no emblem (neutral) / the party eagle (historical)
    yh = YD.bake_yard({'hist': True})
    mh = maps(yh.lay)
    box = box_of(diff_mask(mb, mh), xr=(L.NOTICE[0] - XB - 4, L.NOTICE[1] - XB + 4))
    if box is not None:
        has_e = write_patch('notice_k14', mb, box, gen, 'the Blockleitung\'s notice in the passage: neutral (no party '
                            'emblem) / historical (the party eagle)', K.YARD, hist_m=mh)
        scene['decals'].append({'name': 'notice_k14', 'file': 'patches/notice_k14.png',
                                'pos': [int(box[0]) + XB, int(box[1])], 'z': -48, 'lit': True, 'normal': True,
                                'emission': has_e, 'scene': B, 'hist_variant': 'patches/notice_k14_hist.png',
                                'note': 'insignia site (12.4): the gate_notice\'s typed notice'})
    for li in base.lights:
        nm = li['name']
        if not (nm in ('passage_lamp', 'lodge', 'street_lamp') or nm.startswith('win_E') or nm in
                ('win_1_1444', 'win_1_1496', 'win_3_1340', 'win_1_1764')):
            continue
        scene['lights'].append({'name': nm, 'pos': [round(li['pos'][0] + XB, 1), round(li['pos'][1], 1)],
                                'color': COL['sodium'] if nm == 'passage_lamp' else COL['window'],
                                'energy': round(min(1.0, li['energy'] * (0.9 if nm == 'passage_lamp' else 0.6)), 2),
                                'radius': int(li['radius']), 'flicker': 0.03 if nm == 'passage_lamp' else 0.0,
                                'height': int(li.get('height', 24)), 'on_layer': 'playfield', 'scene': B})
    for li in aft.lights:
        if li['name'] in ('headlights', 'candle'):
            scene['lights'].append({'name': li['name'], 'pos': [round(li['pos'][0] + XB, 1), round(li['pos'][1], 1)],
                                    'color': COL['white'] if li['name'] == 'headlights' else COL['lamp'],
                                    'energy': 0.8 if li['name'] == 'headlights' else 0.35,
                                    'radius': int(li['radius']), 'flicker': 0.0 if li['name'] == 'headlights' else 0.15,
                                    'height': int(li.get('height', 12)), 'on_layer': 'playfield', 'scene': B,
                                    'after': ['c4h_solve_house'], 'fade': 0.8})
    scene['lights'].append({'name': 'night_sky', 'pos': [1420, 40], 'color': COL['blue'], 'energy': 0.3,
                            'radius': 520, 'flicker': 0.0, 'height': 120, 'on_layer': 'playfield', 'scene': B})
    return base, aft


def build_yard_distant(scene: dict):
    gen = 'tools/pixelgen/env_c4p2_berlin_yard.py'
    sky = YD.sky_layer()
    save(sky.c, 'yd_sky.png', gen, 'night sky over the courtyard, low cloud lit by the city', K.YARD)
    dn, dh = YD.dome_layer(False), YD.dome_layer(True)
    save(dn.c, 'yd_dome.png', gen, 'the Great Hall far above the roofs, floodlit in the haze, searchlights behind it; '
                                   'neutral banners (grey cloth, the fictional Reichssiegel)', K.YARD)
    save(dh.c, 'yd_dome_hist.png', gen, 'the Great Hall far above the roofs, historical banners (red, white disc, '
                                        'swastika; Symbols.pick, 12.4)', K.YARD)
    roofs = YD.roofs_layer()
    save(roofs.c, 'yd_roofs.png', gen, 'the roofscape beyond the courtyard: chimneys, firewalls, a church spire', K.YARD)
    if roofs.em[..., 3].any():
        save(roofs.em, 'yd_roofs_e.png', gen, 'roofs -- emission (a lit attic window)', K.YARD)
    fg = YD.fg_layer()
    save(fg.c, 'fg_yard.png', gen, 'the courtyard\'s near edge: trodden snow, window light lying on it, footprints, a '
                                   'sledge track, a handcart with briquettes, milk bottles, a broom, a bucket, a light '
                                   'well\'s railing, a lost mitten (foreground)', K.YARD)
    scene['layers'][0:0] = [
        {'name': 'yd_sky', 'file': 'yd_sky.png', 'pos': [28, 0], 'parallax': [0.03, 1.0], 'z': -100, 'normal': False,
         'emission': False, 'lit': False, 'scene': B},
        {'name': 'yd_dome', 'file': 'yd_dome.png', 'pos': [420, 0], 'parallax': [0.08, 1.0], 'z': -96,
         'normal': False, 'emission': False, 'lit': False, 'scene': B, 'hist_variant': 'yd_dome_hist.png',
         'note': 'the Great Hall; banners on its front: neutral / historical (12.4)'},
        {'name': 'yd_roofs', 'file': 'yd_roofs.png', 'pos': [275, -10], 'parallax': [0.3, 1.0], 'z': -92,
         'normal': False, 'emission': bool(roofs.em[..., 3].any()), 'emission_strength': 0.4, 'lit': False,
         'scene': B},
    ]
    scene['layers'].append({'name': 'fg_yard', 'file': 'fg_yard.png', 'pos': [1147, 318], 'parallax': [1.25, 1.0],
                            'z': 60, 'normal': False, 'emission': False, 'lit': False, 'scene': B,
                            'note': 'pos x = 918 * 1.25: its left edge meets the screen edge at the courtyard\'s camera stop'})


# =========================================================================== strips + fx
def build_strips(scene: dict, st, yd, yd_after):
    gen = 'tools/pixelgen/env_c4p2_berlin_strips.py'

    def decal(nm, res, scene_id, desc, xoff=0, pal=None, folder='life', **kw):
        c, e, box, frames, fps = res
        save(c, '%s/%s.png' % (folder, nm), gen, desc, pal)
        if e is not None:
            save(e, '%s/%s_e.png' % (folder, nm), gen, desc + ' -- emission', pal)
        d = {'name': nm, 'file': '%s/%s.png' % (folder, nm), 'pos': [int(box[0]) + xoff, int(box[1])], 'z': -47,
             'frames': frames, 'fps': fps, 'lit': True, 'normal': False, 'emission': e is not None, 'scene': scene_id}
        d.update(kw)
        scene['decals'].append(d)

    # ---- the station
    decal('booth_officials', SP.booth_officials(st), A, 'the liaison booth at the barrier: a German railway policeman '
          'stamping, a Soviet liaison officer with his tea glass in its metal holder, one desk, one lamp', pal=K.OST)
    decal('baggage_clerk', SP.baggage_clerk(st), A, 'the baggage clerk behind his hatch writing slips', pal=K.OST)
    res = SP.sleeping_boy(st)
    decal('sleeping_boy', res, A, 'exp_corridor_permit: a boy asleep on the family\'s suitcase in front of the buffet',
          pal=K.OST, layer='playfield', base_y=294, z=0)
    decal('kiosk_woman', SP.kiosk_woman(st), A, 'the kiosk woman folding papers, looking up now and then', pal=K.OST)
    decal('loco_crew', SP.loco_crew(st), A, 'the engine driver leaning out of the cab, the firebox glow', pal=K.OST)
    decal('diners', SP.diners(st), A, 'the dining car: a couple with wine, a man behind his paper, Ekdahl\'s empty table '
          '(hat, cup, scarf), two women talking, an old man with soup, the waiter walking the aisle', pal=K.OST)
    decal('sleeper_passenger', SP.sleeper_passenger(st), A, 'a passenger lifting his case into the rack of the sleeper',
          pal=K.OST)
    # ---- the courtyard (layer coords -> world: + XB)
    decal('v1_schulz', SP.schulz(yd), B, 'v1 Schulz: the mother walks the baby between her two windows', xoff=XB,
          pal=K.YARD)
    decal('v3_lenz', SP.lenz(yd), B, 'v3 Lenz: the student under his desk lamp, the radio dial', xoff=XB, pal=K.YARD)
    decal('s1_mertens', SP.mertens(yd), B, 's1 Mertens: the tram conductor\'s family at supper', xoff=XB, pal=K.YARD)
    decal('s2_pohl', SP.pohl(yd), B, 's2 Pohl: the curtain moves, a face, the curtain again', xoff=XB, pal=K.YARD)
    decal('s3_ilse', SP.ilse(yd), B, 's3 Hanna\'s kitchen: Ilse draws houses with lit windows (until the house is solved)',
          xoff=XB, pal=K.YARD, until=['c4h_solve_house'], fade=0.6)
    decal('s3_hanna', SP.hanna_window(yd), B, 's3 after the house is solved: Hanna back at her window, her light on',
          xoff=XB, pal=K.YARD, after=['c4h_solve_house'], fade=0.8)
    decal('se_kuhnert', SP.kuhnert_lodge(yd), B, 'se the lodge: Frau Kuhnert knitting by the radio', xoff=XB, pal=K.YARD)
    decal('h1_kuehn', SP.kuehn(yd), B, 'h1 Kühn: the old couple\'s card game', xoff=XB, pal=K.YARD)
    # the courtyard floor: two neighbours out in the cold (until the house is solved -- by 23.30 everyone is in)
    decal('yard_coal', SP.coal_neighbour(yd), B, 'an old neighbour up from the cellar with a full coal scuttle for '
          'the night (sets it down by the hatch, blows into his hand, glances at the lodge)', xoff=XB, pal=K.YARD,
          until=['c4h_solve_house'], fade=0.6)
    decal('yard_wash', SP.wash_basket(yd), B, 'Tuesday is washing day: a woman out of the wash-house with the last '
          'basket for the attic, looking back at the lodge', xoff=XB, pal=K.YARD, until=['c4h_solve_house'],
          fade=0.6)
    decal('sweep_men', SP.sweep_men(yd_after), B, 'after the house is solved: two of the sweep\'s men by the street '
          'door, one smoking', xoff=XB, pal=K.YARD, after=['c4h_solve_house'], fade=0.8)
    decal('candle_flame', SP.candle(yd_after), B, 'the candle in the cobbler\'s souterrain (after the house is solved)',
          xoff=XB, pal=K.YARD, after=['c4h_solve_house'], fade=0.8)
    # the red warning lamp on the site barrier of No. 12, at the end of the passage (1 Hz)
    wx, wy = yd.warning_lamp
    on = yd.lay.c[wy - 1:wy + 4, wx - 1:wx + 4].copy()
    eon = yd.lay.em[wy - 1:wy + 4, wx - 1:wx + 4].copy()
    off = on.copy()
    lit = eon[..., 3] > 0
    off[lit] = K.rgba(K.RB, 'R', 1.6)
    save(LF.blink_strip(on, off), 'life/warning_lamp.png', gen, 'the red warning lamp on the barrier of No. 12 (1 Hz)',
         K.YARD)
    save(LF.blink_strip(eon, np.zeros_like(eon)), 'life/warning_lamp_e.png', gen, 'the warning lamp -- emission',
         K.YARD)
    scene['decals'].append({'name': 'warning_lamp', 'file': 'life/warning_lamp.png', 'pos': [wx - 1 + XB, wy - 1],
                            'z': -47, 'frames': 4, 'fps': 2, 'lit': False, 'normal': False, 'emission': True,
                            'scene': B})


def build_fx(scene: dict, st, yd):
    gen = 'tools/pixelgen/env_c4p2_berlin_life.py'
    RA, RB = K.RA, K.RB

    def fx(nm, arr, pos, frames, fps, z, scene_id, desc, pal, parallax=(1.0, 1.0), **kw):
        save(arr, 'fx/%s.png' % nm, gen, desc, pal)
        e = {'type': 'anim_sprite', 'name': nm, 'file': 'fx/%s.png' % nm, 'frames': frames, 'fps': fps,
             'pos': [int(pos[0]), int(pos[1])], 'parallax': [parallax[0], parallax[1]], 'z': z, 'lit': False,
             'scene': scene_id}
        e.update(kw)
        scene['fx'].append(e)

    # ---- the station: steam everywhere, snow blown in at the open end
    vx, vy = st.safety_valve
    fx('steam_valve', LF.plume_strip(RA, 46, 120, 16, seed=3, ramp='V', base=4.0, dens=1.0, drift=0.35, spread=0.6,
                                     warm_root=('P', 5.0)), (vx - 23, vy - 116), 16, 8, -44, A,
       'the engine\'s safety valve blowing off: a white plume up into the vault', K.OST)
    cx_, cy_ = st.chimney
    fx('smoke_chimney', LF.plume_strip(RA, 30, 70, 16, seed=4, ramp='V', base=2.6, dens=0.7, drift=-0.4, spread=0.7),
       (cx_ - 15, cy_ - 68), 16, 6, -44, A, 'a lazy wisp of smoke from the standing engine\'s chimney', K.OST)
    fx('steam_cocks', LF.plume_strip(RA, 44, 26, 16, seed=6, ramp='V', base=4.2, dens=0.8, drift=0.6, spread=1.0,
                                     root=0.5), (L.LOCO[0] + 92, 236), 16, 8, -45, A,
       'steam curling from the drain cocks between the drivers (seen in the gap between buffet and kiosk)', K.OST)
    kx, ky = st.kitchen_vent
    fx('steam_kitchen', LF.plume_strip(RA, 26, 64, 16, seed=5, ramp='V', base=3.6, dens=0.8, drift=0.5),
       (kx - 13, ky - 62), 16, 6, -44, A, 'the dining car\'s kitchen chimney: cooking steam', K.OST)
    fx('steam_heat_a', LF.plume_strip(RA, 70, 44, 16, seed=7, ramp='V', base=4.2, dens=0.7, drift=0.2, spread=0.9,
                                      root=0.4), (L.GAP[0] + 8, 222), 16, 8, -45, A,
       'steam heating leaking at the uncoupled ends (winter)', K.OST)
    fx('steam_heat_b', LF.plume_strip(RA, 30, 40, 16, seed=9, ramp='V', base=4.0, dens=0.6, drift=0.3),
       (L.DINER[1] - 14, 220), 16, 8, -45, A, 'steam heating leaking between dining car and sleeper', K.OST)
    ux, uy = st.urn
    fx('steam_urn', LF.plume_strip(RA, 16, 30, 12, seed=11, ramp='V', base=4.4, dens=0.6, drift=0.4),
       (ux - 8, uy - 28), 12, 6, -44, A, 'the buffet urn steaming', K.OST)
    fx('haze_vault', LF.haze_strip(RA, 420, 90, 24, seed=13, ramp='V', base=2.8, dens=0.55, drift=2),
       (190, 50), 24, 3, -40, A, 'steam collected under the glass vault, drifting', K.OST)
    fx('drift_end', LF.drift_strip(RA, 240, 190, 24, 8, n=70, seed=15, ramp='V', tones=(5, 4)), (0, 110), 24, 8, 30,
       A, 'snow blown in through the open end of the hall', K.OST)
    # ---- the courtyard: snow over everything, chimney smoke, the car's exhaust after the puzzle
    half = (L.WORLD_W - XB) // 2
    for k, x0 in enumerate((XB, XB + half)):
        fx('snow_%s' % 'ab'[k], LF.snow_strip(RB, half + 1, 320, 24, 8, n=130, seed=21 + k, ramp='SN',
                                              tones=(6, 5, 4), wind=(-2, 2)), (x0, 0), 24, 8, 30, B,
           'snow falling into the courtyard, two depths (%s half)' % ('left', 'right')[k], K.YARD)
    for i, (cx, cy) in enumerate(yd.chimneys[1::2]):
        fx('smoke_%d' % i, LF.plume_strip(RB, 22, 46, 16, seed=31 + i, ramp='U', base=2.8, dens=0.8, drift=0.7),
           (cx - 11 + XB, cy - 44), 16, 5, -48, B, 'smoke from a chimney of No. 14 (stoves lit for the night)', K.YARD)
    fx('exhaust', LF.plume_strip(RB, 24, 22, 12, seed=41, ramp='SN', base=4.0, dens=0.8, drift=0.8),
       (L.STREET_DOOR[0] + 2, 272), 12, 8, -45, B, 'the sweep\'s car: exhaust in the frost', K.YARD,
       after=['c4h_solve_house'], fade=0.8)


# =========================================================================== actors
def actors(scene: dict, yd):
    pig = 'res://assets/environments/veltrava_station/actors/'
    breath = 'res://assets/environments/karsk_railyard/actors/breath_puff.png'
    scene['actors'] = [
        {'scene': 'res://scenes/actors/AmbientWalkers.tscn', 'pos': [0, 0],
         'props': {'data': 'res://assets/environments/berlin_c4p2/walkers_a.json'}, 'gen': 'env_c4p2_berlin',
         'scene_id': A, 'note': 'the people of the Corridor platform (crowd/ rigs, walkers_a.json)'},
        {'scene': 'res://scenes/levels/c4p2/C4P2StationClock.tscn', 'pos': list(L.CLOCK),
         'props': {'radius': 7.0, 'start': '20:31:12'}, 'gen': 'env_c4p2_berlin', 'scene_id': A,
         'note': 'exp_station_clock: the hands of the platform clock (dial baked), 20.31 when the level opens'},
        {'scene': 'res://scenes/levels/veltrava_station/StationPigeons.tscn', 'pos': [368, 292],
         'props': {'sprite': pig + 'pigeons_sheet.png', 'bread': pig + 'bread.png', 'bread_pos': [366, 292],
                   'spots': [[362, 292], [371, 293], [378, 291], [356, 294]], 'tuggers': 2, 'scare_radius': 13.0,
                   'run_radius': 52.0, 'roost_y': 118.0},
         'gen': 'env_c4p2_berlin', 'scene_id': A,
         'note': 'pigeons between the buffet and the kiosk tug at a roll from the buffet; they flutter up under the vault'},
        {'scene': 'res://scenes/levels/karsk/KarskBreath.tscn', 'pos': [318, 300],
         'props': {'points': [[313, 262]], 'sprite': breath, 'interval': 4.8}, 'gen': 'env_c4p2_berlin', 'scene_id': A,
         'note': 'Marta\'s breath in the cold hall'},
        {'scene': 'res://scenes/levels/karsk/KarskBreath.tscn', 'pos': [698, 300],
         'props': {'points': [[693, 262]], 'sprite': breath, 'interval': 5.4}, 'gen': 'env_c4p2_berlin', 'scene_id': A,
         'note': 'Ekdahl\'s breath'},
        {'scene': 'res://scenes/levels/karsk/KarskBreath.tscn', 'pos': [1060, 300],
         'props': {'points': [[1055, 262]], 'sprite': breath, 'interval': 4.4}, 'gen': 'env_c4p2_berlin', 'scene_id': B,
         'note': 'Kuhnert\'s breath in the passage'},
        {'scene': 'res://scenes/levels/karsk/KarskCat.tscn', 'pos': [1404, 276],
         'props': {'sprite': 'res://assets/environments/karsk_railyard/actors/cat.png', 'wake_radius': 42.0},
         'gen': 'env_c4p2_berlin', 'scene_id': B,
         'note': 'a cat asleep on the lodge\'s warm window sill; it lifts its head when Konrad comes to the card box'},
        {'scene': 'res://scenes/levels/karsk/KarskWind.tscn', 'pos': [0, 0],
         'props': {'roofs': [[918, 1872, 82], [918, 1872, 58], [1872, 1920, 16]], 'min_gap': 11.0, 'max_gap': 22.0},
         'gen': 'env_c4p2_berlin', 'scene_id': B, 'note': 'gusts blow snow off the eaves and the ridge into the courtyard'},
        {'scene': 'res://scenes/levels/berlin/BerlinRadio.tscn', 'pos': [L.LODGE[1] - 8, 272],
         'props': {'glow_path': 'res://assets/environments/berlin_c4p2/actors/radio_glow.png', 'glow_offset': [-6, -14],
                   'loop_path': 'res://assets/audio/sfx/berlin_radio_loop.wav'},
         'gen': 'env_c4p2_berlin', 'scene_id': B,
         'note': '„seine Frau hört Radio“: dance music, faint, from the lodge (positional)'},
    ]


def radio_glow():
    """3-frame glow for the lodge radio actor (BerlinRadio adds it): a soft amber dot that breathes."""
    gen = 'tools/pixelgen/env_c4p2_berlin.py'
    fr = []
    for k in range(3):
        a = np.zeros((6, 8, 4), np.uint8)
        col = K.rgba(K.RB, 'L', 4 - (k == 1))
        for (x, y) in ((3, 2), (4, 2), (3, 3), (4, 3)) + (((2, 2), (5, 3)) if k != 2 else ()):
            a[y, x] = col
        fr.append(a)
    save(K.strip(fr), 'actors/radio_glow.png', gen, 'the lodge radio\'s dial glow for BerlinRadio (3 frames)', K.YARD)


# =========================================================================== scene.json
def hotspot_info():
    what = {
        'departure_board': 'the enamel departure board of platform K on two cast-iron posts: „D 303 BERLIN OST – '
                           'KORDON-17 · KARSK 21.10“; below it the freshly painted board for Tuesday',
        'marta_buffet': 'the buffet „Erfrischungen“: Marta Vogel (318) at the counter, her duty roster on it (decal by '
                        'c4d_choose: „Linie 3“ / „Linie 74“); the buffet woman behind it; through the open stand the '
                        'engine 01 064 (its drivers in the gap toward the kiosk)',
        'shadow_kiosk': 'the newspaper kiosk, the headline board „Ein Winter des Friedens“; the man in the leather coat '
                        '(stapo_civil) reads the same page in front of it',
        'courier_car': 'behind the engine and its tender the two-axle courier van without windows, two lead seals on the '
                       'wire of its sliding door (x ~500); through the uncoupled gap beside it the green car on the next '
                       'track',
        'ekdahl_window': 'the dining car (wine red, „SPEISEWAGEN“, lit windows, white cloths); Nils Ekdahl (698) on the '
                         'platform before his own empty table (hat, cup, scarf)',
        'dining_table': 'the dining car\'s open door: the lit vestibule, the first table with a cloth, a tea glass, the '
                        'blue linen guidebook with a slip of paper sticking out',
        'gate_notice': 'the cork board in the gate passage: the typed notice of the Blockleitung (emblem only in the '
                       '_hist patch) and the pinned site plan with the hatched houses',
        'kuhnert_gate': 'Kuhnert (blockwart, 1060) waits in the passage by the letterboxes and the front wing\'s stair door',
        'wendt_yard': 'just outside the passage in the courtyard; Wendt (1128) after the house is solved, the car\'s '
                      'lights behind him',
        'hanna_yard': 'Hanna (1268) beside the side wing\'s green stair door „Aufg. B“ (Ilse\'s frost drawing on its glass)',
        'lodge_window': 'the lodge window (Loge Kuhnert, lit): Frau Kuhnert knitting by the radio; the wooden box of '
                        'household cards on the sill, one red tab; a cat asleep on the warm sill',
        'yard_pump': 'the cast-iron courtyard pump with its frozen spout and the ice at its foot; Konrad looks up at the '
                     'house from here (the house puzzle)',
    }
    obj = {'departure_board': (62, 148), 'marta_buffet': L.BUFFET, 'shadow_kiosk': L.KIOSK,
           'courier_car': (448, 530), 'ekdahl_window': (624, 816), 'dining_table': (794, 814),
           'gate_notice': L.NOTICE, 'kuhnert_gate': (1036, 1100), 'wendt_yard': (1100, 1140),
           'hanna_yard': (1236, 1300), 'lodge_window': L.LODGE, 'yard_pump': L.PUMP}
    out = {}
    for k, (x, y) in L.HOTSPOTS.items():
        kind = 'npc_anchor' if k in ('shadow_kiosk', 'kuhnert_gate') else 'story'
        out[k] = {'kind': kind, 'stand': [x, y], 'focus': [x, 250], 'what': what[k], 'object_x': list(obj[k])}
    return out


def build_scene():
    scene = {'id': 'berlin_c4p2', 'palette': 'ostbahnhof', 'world_size': [L.WORLD_W, L.WORLD_H],
             'camera': {'bounds': [0, 0, L.WORLD_W, L.WORLD_H]}, 'camera_zones': L.CAMERA_ZONES,
             'canvas_modulate': '#DED7C9', 'layers': [], 'props': [], 'decals': [], 'lights': [], 'fx': [],
             'actors': []}
    st = build_station(scene)
    build_station_distant(scene)
    yd, yd_after = build_yard(scene)
    build_yard_distant(scene)
    build_strips(scene, st, yd, yd_after)
    build_fx(scene, st, yd)
    actors(scene, yd)
    radio_glow()
    scene.update({
        'walkable': [[L.WALK_X[0], L.WALK_BAND[0]], [L.WALK_X[1], L.WALK_BAND[0]], [L.WALK_X[1], L.WALK_BAND[1]],
                     [L.WALK_X[0], L.WALK_BAND[1]]],
        'blockers': [dict(L.BLOCKER)],
        'spawns': {k: [v[0], v[1]] for k, v in L.SPAWNS.items()},
        'hotspots': {k: [v[0], v[1]] for k, v in L.HOTSPOTS.items()},
        'zones': L.ZONES,
        'looks': [
            {'name': 'station', 'scene': A, 'canvas_modulate': '#DED7C9', 'grade': 'ostbahnhof'},
            {'name': 'courtyard', 'scene': B, 'canvas_modulate': '#C6CEDF', 'grade': 'courtyard_night'},
        ],
        'hotspot_info': hotspot_info(),
        'npcs': {k: dict(v) for k, v in L.NPCS.items()},
        'households': {k: {'wing': v[0], 'floor': v[1], 'light': v[2], 'axes': list(v[3]), 'what': v[4]}
                       for k, v in L.HOUSEHOLDS.items()},
        'gates_doc': 'Entries with "after" (objectives that must be complete), "until" (hidden once one of them is '
                     'complete) or "choice" (objective: id | "!id") are built by registry_level.gd (base of '
                     'scripts/levels/c4/annex_level.gd -> scripts/levels/c4p2/berlin_c4p2_level.gd) and shown while the '
                     'condition holds; "fade" = seconds of the live cross-fade. "scene" (one id; actors use "scene_id") '
                     '= only built when the level plays that Story scene (decided at load: every part-2 scene starts '
                     'with a level load).',
        'notes': [
            'Two walk areas in one file: L_C4P2_BerlinA (Ostbahnhof, x 18..898) left of the permanent blocker '
            'platform_end, L_C4P2_BerlinB (Kolonnenstraße 14, x 938..1902) right of it; the station layers cover '
            'x 0..918, the courtyard layers x 918..1920 (camera zones [0, 0, 918, 360] / [918, 0, 1002, 360]).',
            'Every spawn, hotspot, blocker, camera zone and NPC anchor of the story stream\'s placeholder is kept '
            'name for name and position for position; the exploration stream\'s finds (explore_hotspots.json) stand '
            'at the art their "info" asks for.',
            'The courtyard is unrolled into one elevation like the house puzzle\'s cutaway: Vorderhaus | Seitenflügel '
            '| Hinterhaus; every lit window is a household of §2.7 ("households").',
            'Palettes: data/chapters/c4p2.json ostbahnhof / courtyard + the proposed ramps (wood, brick, enamel, cream '
            '/ dusk, wood, green) -- see asset_manifest_parts/env_c4p2_berlin.md.',
        ],
        'meta': {'mode': 'side', 'feet_y': L.FEET, 'generator': GEN, 'date': K.DATE,
                 'palette_ostbahnhof': {k: v for k, v in K.OST.items()},
                 'palette_courtyard': {k: v for k, v in K.YARD.items()}},
    })
    return scene, st, yd


def write_walkers():
    rows, data = CR.build(ENV_DIR, 'tools/pixelgen/env_c4p2_berlin_crowd.py')
    PRODUCED.extend(rows)
    p = os.path.join(ENV_DIR, 'walkers_a.json')
    KEEP.write_json(p, data)
    PRODUCED.append((rel(p), 'tools/pixelgen/env_c4p2_berlin_crowd.py', 'ambient walkers of the Corridor platform'))


def write_scene(scene: dict):
    old = KEEP.read_json(os.path.join(ENV_DIR, 'scene.json'))
    if isinstance(old, dict):
        old = {k: v for k, v in old.items() if k != 'placeholder'}
    merged = KEEP.merge_scene(scene, old)
    KEEP.write_json(os.path.join(ENV_DIR, 'scene.json'), merged)
    PRODUCED.append((ENV_REL + '/scene.json', GEN, 'art manifest of L_C4P2_Berlin (both scenes)'))
    return merged


def write_provenance():
    rows = [{'path': p, 'generator': g, 'description': d} for (p, g, d) in PRODUCED]
    old = KEEP.read_json(os.path.join(ENV_DIR, 'provenance.json'))
    files = KEEP.merge_rows(rows, old, FAMILY, ROOT)
    data = {'environment': 'berlin_c4p2', 'level': 'scenes/levels/L_C4P2_Berlin.tscn', 'generator': GEN,
            'date': K.DATE, 'license': 'original work, generated deterministically by the project tools (no third-party '
                                      'images, no traced references)', 'files': files}
    KEEP.write_json(os.path.join(ENV_DIR, 'provenance.json'), data)


# =========================================================================== preview (dev aid)
def preview(scene, out_dir, hist=False, after=False, cams=None):
    """Composite the layers + static decals + strips' first frames per scene at a few camera stops (python only)."""
    os.makedirs(out_dir, exist_ok=True)

    def load(rp):
        if hist:
            hp = rp[:-4] + '_hist.png'
            if os.path.isfile(os.path.join(ENV_DIR, hp)):
                rp = hp
        return Image.open(os.path.join(ENV_DIR, rp)).convert('RGBA')
    shots = []
    for sid, cs in (cams or ((A, (0, 139, 278)), (B, (918, 1099, 1280)))):
        for cam in cs:
            img = Image.new('RGBA', (640, 360), (0, 0, 0, 255))
            ents = [e for e in scene['layers'] if e.get('scene', sid) == sid]
            for e in scene['decals'] + scene['fx'] + scene['props']:
                if e.get('scene', sid) != sid:
                    continue
                if e.get('after') and not after:
                    continue
                if e.get('until') and after:
                    continue
                ch = e.get('choice')
                if ch and list(ch.values())[0].startswith('!') is False:
                    continue
                ents.append(dict(e, parallax=e.get('parallax', [1, 1]), z=e.get('z', -40) if 'base_y' not in e else -41))
            ents.sort(key=lambda e: e.get('z', 0))
            for e in ents:
                im = load(e['file'])
                fr = int(e.get('frames', 1))
                if fr > 1:
                    im = im.crop((0, 0, im.size[0] // fr, im.size[1]))
                px = e.get('parallax', [1, 1])
                px = px if isinstance(px, list) else [px, 1]
                x = int(round(e['pos'][0] - cam * float(px[0])))
                tmp = Image.new('RGBA', (640, 360), (0, 0, 0, 0))
                tmp.paste(im, (x, int(e['pos'][1])))
                img.alpha_composite(tmp)
            p = os.path.join(out_dir, 'prev_%s_%04d%s%s.png' % (sid[-1], cam, '_hist' if hist else '',
                                                                 '_after' if after else ''))
            img.convert('RGB').save(p)
            shots.append(p)
    return shots


def main(argv):
    pv = None
    docs = True
    for a in argv:
        if a.startswith('--preview='):
            pv = a.split('=', 1)[1]
        elif a == '--no-docs':
            docs = False
    t0 = time.time()
    os.makedirs(ENV_DIR, exist_ok=True)
    gone = KEEP.remove_own_pngs(ENV_DIR, ROOT, FAMILY)
    scene, st, yd = build_scene()
    write_walkers()
    if docs:
        import env_c4p2_berlin_docs as DOCS
        PRODUCED.extend(DOCS.build())
    merged = write_scene(scene)
    write_provenance()
    if pv:
        preview(merged, pv)
        preview(merged, pv, hist=True, after=True, cams=((B, (918, 1280)), (A, (0,))))
    bad = []
    for (p, _g, _d) in PRODUCED:
        pal = PAL_OF.get(p)
        if pal is None:
            continue
        arr = np.asarray(Image.open(os.path.join(ROOT, p)).convert('RGBA'))
        _n, off = K.palette_report(arr, pal)
        if off:
            bad.append((p, off[:4]))
    print('env_c4p2_berlin: %d files, %d layers, %d props, %d decals, %d fx, %d lights, %d actors in %.1f s '
          '(removed %d stale own PNGs first)' % (len(PRODUCED), len(scene['layers']), len(scene['props']),
                                                 len(scene['decals']), len(scene['fx']), len(scene['lights']),
                                                 len(merged.get('actors', [])), time.time() - t0, len(gone)))
    print('  palettes: ostbahnhof %d colours, courtyard %d colours' % (K.palette_count(K.OST), K.palette_count(K.YARD)))
    for n_ in K.check_c4p2_palettes():
        print('  palette note:', n_)
    for b in bad:
        print('  OFF PALETTE', b)
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
